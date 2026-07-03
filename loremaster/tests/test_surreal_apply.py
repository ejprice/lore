"""Contract tests for P5-C2 (ledger #23): the ONE atomic per-file
``BEGIN … COMMIT`` that spans a file's chunks + ``file_text`` body + code-graph
nodes/edges + manifest row, applied on a single SurrealDB connection so a
concurrent reader never observes a half-applied file.

WHAT THIS FILE PINS
-------------------
The four ported writers (``SurrealStore`` chunks, the NEW ``file_text`` body
writer, ``SurrealManifest`` row, ``SurrealCodeGraph`` nodes/edges) each learn to
BUILD a composable transaction *fragment* (an ordered list of SurrealQL
statements + a producer-namespaced params dict, carrying NO ``BEGIN``/``COMMIT``
of its own). A new composition primitive merges any set of fragments into one
executable transaction, and ``SurrealStore.apply`` runs that ONE transaction on
the store's own connection. Because a SurrealDB transaction is connection-scoped,
running all four producers' fragments through the store's single connection is
exactly what makes the per-file update atomic across all four tables.

THE PINNED PUBLIC API SURFACE (named here, blind to any implementation)
-----------------------------------------------------------------------
``loremaster.store._txn``:

    @dataclass(frozen=True)
    class TxnFragment:
        statements: Sequence[str]   # ordered SurrealQL, NO BEGIN/COMMIT
        params: Mapping[str, Any]   # bound params, producer-namespaced

    class TxnParamCollisionError(SurrealStoreError): ...

    def compose(*fragments: TxnFragment) -> tuple[str, dict[str, Any]]:
        # merge into ONE ``BEGIN … COMMIT`` (statement_text, merged_params);
        # raise TxnParamCollisionError on ANY param-name collision across
        # fragments; raise ValueError when handed no fragments.

    TXN_STATEMENT_WARN_THRESHOLD: int   # apply() WARNs above this body-stmt count

``loremaster.store.surreal`` (on ``SurrealStore``):

    CHUNK_FRAGMENT_PARAM_PREFIX = "st_"
    FILE_TEXT_FRAGMENT_PARAM_PREFIX = "ft_"
    def replace_file_fragment(tier, file_path, records_with_vectors) -> TxnFragment
    def delete_file_fragment(tier, file_path) -> TxnFragment
    def file_text_fragment(tier, file_path, text, sha512) -> TxnFragment
    def file_text_delete_fragment(tier, file_path) -> TxnFragment
    async def apply(fragments: Sequence[TxnFragment]) -> None

``loremaster.index.surreal_manifest`` (on ``SurrealManifest``):

    MANIFEST_FRAGMENT_PARAM_PREFIX = "mf_"
    def replace_fragment(*, tier, file_path, sha512, mtime_ns, size, n_chunks,
                         chunk_ids, state) -> TxnFragment
    def delete_fragment(tier, file_path) -> TxnFragment

``loremaster.graph_surreal`` (on ``SurrealCodeGraph``):

    GRAPH_FRAGMENT_PARAM_PREFIX = "gr_"
    def build_file_graph_fragment(tier, file_path, chunks, *, module_name=None) -> TxnFragment
    def purge_file_fragment(tier, file_path) -> TxnFragment

The fragment builders are PURE (no I/O): dimension validation, the C1a
metadata reshaping, and the astroid graph derivation (sync CPU, reads on-disk
source) all happen at BUILD time; only ``apply`` touches the socket.

RED STRATEGY (why the file COLLECTS but every test FAILS)
---------------------------------------------------------
The brand-new *top-level* names (``TxnFragment`` / ``compose`` /
``TxnParamCollisionError`` / ``TXN_STATEMENT_WARN_THRESHOLD`` / the four param
prefixes) are imported under a guard so a pre-P5-C2 collection does NOT explode
into one ``ImportError`` that hides the whole contract — the file collects and
each test reports its OWN behavioural failure. The new *methods* hang off
classes that already import cleanly (``SurrealStore`` / ``SurrealManifest`` /
``SurrealCodeGraph``), so calling a not-yet-existing builder raises
``AttributeError`` at the point under test — a behavioural RED, not a collection
error. (Contrast ``test_graph_surreal.py``'s pre-P4 whole-file collection error,
used only because every new name there was a fresh top-level import.)

Runs against the REAL 3.1.5 server (``_surreal_harness`` per-test DB isolation) —
cross-connection visibility and snapshot isolation are server-side properties
with no in-memory shortcut.
"""

from __future__ import annotations

import asyncio
import logging
import textwrap
import time
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SLUG,
    TIER_A,
    TIER_B,
    SurrealEnv,
    connect_admin,
    run,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
    unit_vector,
)
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.records import chunk_to_record, sha512_hex
from loremaster.index.surreal_manifest import STATE_INDEXED, SurrealManifest
from loremaster.store.surreal import (
    SurrealConnectionError,
    SurrealStore,
    SurrealStoreError,
    VectorDimensionError,
)
from loremaster.store.surreal_schema import CHUNK_TABLE, FILE_STATES, FILE_TABLE, FILE_TEXT_TABLE
from lorescribe.astroid_parse import clear_resolution_cache, reset_search_path_memo
from lorescribe.models import Chunk, ChunkContext
from lorescribe.python_ast import PythonAstChunker

# --- The brand-new composition API (RED-guarded so collection never explodes) --
#
# These four modules ALL exist today; only the NEW names below are missing until
# the P5-C2 STUB lands. Guarding just these keeps the file collectable so every
# test fails on its OWN behaviour (a missing builder method / a None callable)
# rather than one collection error hiding the whole contract.
try:
    from loremaster.graph_surreal import GRAPH_FRAGMENT_PARAM_PREFIX  # noqa: E402
    from loremaster.index.surreal_manifest import (  # noqa: E402
        MANIFEST_FRAGMENT_PARAM_PREFIX,
    )
    from loremaster.store._txn import (  # noqa: E402
        TXN_STATEMENT_WARN_THRESHOLD,
        TxnFragment,
        TxnParamCollisionError,
        compose,
    )
    from loremaster.store.surreal import (  # noqa: E402
        CHUNK_FRAGMENT_PARAM_PREFIX,
        FILE_TEXT_FRAGMENT_PARAM_PREFIX,
    )

    _APPLY_API_AVAILABLE = True
except ImportError:  # pragma: no cover - pre-P5-C2 RED: the compose/apply API is absent
    _APPLY_API_AVAILABLE = False

    class _MissingComposeApiError(Exception):
        """Placeholder so ``pytest.raises(TxnParamCollisionError)`` is a valid
        type expression before the real error class exists — the test still REDs
        because ``compose`` / ``TxnFragment`` below are ``None``."""

    TxnFragment = None  # type: ignore[assignment,misc]
    compose = None  # type: ignore[assignment]
    TxnParamCollisionError = _MissingComposeApiError  # type: ignore[misc,assignment]
    # Documented placeholder values: every test that reads these ALSO calls a
    # not-yet-existing builder method first, so the RED comes from the real
    # API-under-test, never from these fallbacks.
    TXN_STATEMENT_WARN_THRESHOLD = 800
    CHUNK_FRAGMENT_PARAM_PREFIX = "st_"
    FILE_TEXT_FRAGMENT_PARAM_PREFIX = "ft_"
    MANIFEST_FRAGMENT_PARAM_PREFIX = "mf_"
    GRAPH_FRAGMENT_PARAM_PREFIX = "gr_"


# --- P5-C3a: composed-transaction hardening (hard cap / envelope integrity /
# file_text size bound) — RED-guarded SEPARATELY from the P5-C2 block above so
# an import failure here can NEVER regress an already-GREEN P5-C2 test; only
# the tests below that actually exercise these three new names go RED.
try:
    from loremaster.store._txn import (  # noqa: E402
        TXN_STATEMENT_HARD_CAP,
        TxnEnvelopeViolationError,
    )
    from loremaster.store.surreal import FILE_TEXT_MAX_BYTES  # noqa: E402

    _HARDENING_API_AVAILABLE = True
except ImportError:  # pragma: no cover - pre-P5-C3a RED: the hardening API is absent
    _HARDENING_API_AVAILABLE = False

    class _MissingHardeningApiError(Exception):
        """Placeholder so ``pytest.raises(TxnEnvelopeViolationError)`` is a
        valid type expression before the real error class exists — the test
        still REDs because this placeholder is NOT a ``SurrealStoreError``
        subclass and/or ``compose``/``file_text_fragment`` never actually
        raise it."""

    TxnEnvelopeViolationError = _MissingHardeningApiError  # type: ignore[misc,assignment]
    # Documented placeholders: every test that reads these ALSO calls the real
    # API under test, so the RED comes from the real behaviour, never from
    # these fallback numbers.
    TXN_STATEMENT_HARD_CAP = 5000
    FILE_TEXT_MAX_BYTES = 10 * 1024 * 1024


# A generous per-read cap for the small test corpora — big enough never to
# truncate an intended result, while exercising ``scroll``'s required bound.
_READ_ALL = 1000

# The embedder's injected token-count contract (~4 chars/token) + hard cap,
# mirrored from ``test_graph_surreal`` so the REAL chunker runs exactly as prod.
VOYAGE4_MAX_INPUT_TOKENS = 8192

# A file.state value deliberately OUTSIDE the schema's closed domain — the
# poison the mid-transaction-failure cases splice in. Independent of any
# implementation: its rejection is guaranteed by the ``file.state`` field ASSERT
# (``surreal_schema._file_statements`` → ``ASSERT $value IN [...]``), verified
# below to genuinely not be a member of the shared ``FILE_STATES`` domain.
_INVALID_FILE_STATE = "__definitely_not_a_valid_state__"


# ===========================================================================
# Authored on-disk fixture sources. Each is an INDEPENDENT ORACLE: the true FQNs
# / importer sets / reference profiles are read straight off the source text
# below, never re-derived from the engine. astroid resolution needs the file ON
# DISK under the project roots, so these are materialised to ``tmp_path``.
# ===========================================================================

ERRORS_SOURCE = textwrap.dedent(
    '''\
    """The demo project's error types."""


    class LoadError(Exception):
        """Raised when a config file cannot be loaded."""
    '''
)

APP_SOURCE = textwrap.dedent(
    '''\
    """A small but realistic service module."""
    from __future__ import annotations

    import json
    from pathlib import Path

    from demo.errors import LoadError


    def load_config(path):
        """Module-level helper: read and parse a config file."""
        return json.loads(Path(path).read_text())


    class BaseService:
        """Common service plumbing."""

        def start(self):
            """Start the service."""
            return True


    class IndexService(BaseService):
        """Indexes documents; inherits plumbing from BaseService."""

        def boot(self, path):
            """Boot the service from a config file."""
            config = load_config(path)
            return self.start()
    '''
)

# The REVISED body for the replace-semantics cases: the ``from demo.errors
# import LoadError`` import is GONE (so ``what_imports(LoadError)`` must drop
# ``demo.service`` — the stale-edge oracle), ``load_config`` is REMOVED and
# ``save_config`` is ADDED (so the chunk-identity set both loses and gains a
# member — a partial delete-then-insert can equal NEITHER the old nor the new
# set, which is what makes the snapshot-isolation loop meaningful).
APP_SOURCE_V2 = textwrap.dedent(
    '''\
    """A small but realistic service module (revised)."""
    from __future__ import annotations

    import json
    from pathlib import Path


    def save_config(path, data):
        """Module-level helper: serialise a config file."""
        return Path(path).write_text(json.dumps(data))


    class BaseService:
        """Common service plumbing."""

        def start(self):
            """Start the service."""
            return True


    class IndexService(BaseService):
        """Indexes documents; inherits plumbing from BaseService."""

        def boot(self):
            """Boot the service."""
            return self.start()
    '''
)

TEST_SOURCE = textwrap.dedent(
    '''\
    """Tests for the index service."""
    from __future__ import annotations

    from demo.service import IndexService


    def test_boot():
        """A test that boots the service."""
        service = IndexService()
        return service.boot("/tmp/config.json")
    '''
)

ERRORS_PATH = "demo/errors.py"
APP_PATH = "demo/service.py"
TEST_PATH = "tests/test_service.py"

ERRORS_MODULE = "demo.errors"
APP_MODULE = "demo.service"
TEST_MODULE = "tests.test_service"

# Independent oracles — the TRUE FQNs, read straight off the sources above.
FQN_LOAD_ERROR = "demo.errors.LoadError"
FQN_BASE = "demo.service.BaseService"
FQN_INDEX = "demo.service.IndexService"


def _write_source(root: Path, path: str, source: str) -> None:
    """Materialise ``source`` at ``root/path`` (astroid resolves from disk)."""
    absolute = root / path
    absolute.parent.mkdir(parents=True, exist_ok=True)
    absolute.write_text(source, encoding="utf-8")


def _write_demo_package(root: Path) -> None:
    """Materialise ``demo/`` (errors + service) and ``tests/`` on disk for astroid.

    The WHOLE package is written even when a test builds only one file's
    fragments, because astroid must resolve ``from demo.errors import LoadError``
    against ``errors.py`` on disk for the ``imports`` edge to carry the resolved
    ``demo.errors.LoadError`` dst.
    """
    (root / "demo").mkdir(parents=True, exist_ok=True)
    (root / "demo" / "__init__.py").write_text("", encoding="utf-8")
    _write_source(root, ERRORS_PATH, ERRORS_SOURCE)
    _write_source(root, APP_PATH, APP_SOURCE)
    _write_source(root, TEST_PATH, TEST_SOURCE)


def approx_token_count(text: str) -> int:
    """Behavioural stand-in for the embedder's injected token counter (~4 cpt)."""
    return max(1, len(text) // 4)


def _chunk(path: str, source: str) -> list[Chunk]:
    """Chunk ``source`` through the REAL ``PythonAstChunker`` (the prod producer).

    Driving the real chunker (not hand-rolled ``Chunk`` objects) exercises the
    producer↔consumer seam both the store and the graph consume, so a chunker
    shape drift cannot slip past.
    """
    context = ChunkContext(
        slug=SLUG,
        file_path=path,
        count_tokens=approx_token_count,
        max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
    )
    return PythonAstChunker().chunk(source, context)


@dataclass(frozen=True)
class _Bench:
    """The shared per-test topology: three components on ONE database.

    ``store`` is the connection ``apply`` runs its single transaction on;
    ``manifest`` and ``graph`` are INDEPENDENT instances (their own separate
    connections, same ns/db) used both as fragment PRODUCERS and, crucially, as
    the READERS that prove cross-connection visibility of what the store wrote.
    """

    store: SurrealStore
    manifest: SurrealManifest
    graph: SurrealCodeGraph
    env: SurrealEnv
    project_root: Path


@dataclass(frozen=True)
class _FileFragments:
    """One file's four built fragments plus the oracles derived alongside them."""

    fragments: list[Any]  # list[TxnFragment] once the API exists
    records: list[Any]  # list[Record]
    chunks: list[Chunk]
    file_sha: str

    @property
    def identities(self) -> frozenset[str]:
        """The chunk identities the producer emitted (the store must round-trip)."""
        return frozenset(record.payload["identity"] for record in self.records)

    @property
    def point_ids(self) -> frozenset[str]:
        """The deterministic uuid5 point ids (the manifest must carry these)."""
        return frozenset(record.point_id for record in self.records)


def _fragments_for_file(
    bench: _Bench, *, tier: str, path: str, source: str, module: str
) -> _FileFragments:
    """Build the FOUR per-file fragments through the four real producers.

    Every value is grounded in the SAME source of truth production uses: the
    chunk ``Record``s come from the production translator
    ``records.chunk_to_record`` (metadata spread top-level, no wrapper key); the
    ``file_text`` body is the verbatim source; the manifest's ``chunk_ids`` are
    exactly those records' point ids; the file's SHA-512 is one
    ``records.sha512_hex`` digest shared by the ``file_text`` row AND the
    manifest row (clause 5 — never a hand-copied twin). The source is written to
    disk first because the graph builder's astroid derivation reads it there.
    """
    _write_source(bench.project_root, path, source)
    chunks = _chunk(path, source)
    file_sha = sha512_hex(source)
    mtime_ns = time.time_ns()
    records = [
        chunk_to_record(
            chunk,
            slug=SLUG,
            tier=tier,
            file_path=path,
            content_hash=file_sha,
            mtime_ns=mtime_ns,
        )
        for chunk in chunks
    ]
    pairs = [(record, unit_vector(index, bench.env.dim)) for index, record in enumerate(records)]
    fragments = [
        bench.store.replace_file_fragment(tier, path, pairs),
        bench.store.file_text_fragment(tier, path, source, file_sha),
        bench.manifest.replace_fragment(
            tier=tier,
            file_path=path,
            sha512=file_sha,
            mtime_ns=mtime_ns,
            size=len(source.encode("utf-8")),
            n_chunks=len(records),
            chunk_ids=[record.point_id for record in records],
            state=STATE_INDEXED,
        ),
        bench.graph.build_file_graph_fragment(tier, path, chunks, module_name=module),
    ]
    return _FileFragments(
        fragments=fragments, records=records, chunks=chunks, file_sha=file_sha
    )


# --- production-shaped chunk records (the C1a reshaping seam) -----------------

_METADATA_TEST_SOURCE = (
    "def action_confirm(self):\n"
    "    for order in self:\n"
    "        order.write({'state': 'purchase'})\n"
    "    return True\n"
)


def _production_metadata(*, ident_text: str) -> dict[str, Any]:
    """A representative chunker metadata payload — the actual multi-typed shape a
    real chunker attaches (nested dict, list, str, int, bool), NOT a convenience
    synthetic. ``ident_text`` is the only channel that populates the REQUIRED
    ``ident_text`` chunk column via ``chunk_to_record``'s top-level spread.
    """
    return {
        "ident_text": ident_text,
        "docstring": "Confirm the purchase order and post the linked account move.",
        "decorators": ["api.model", "api.depends('state')"],
        "complexity": 7,
        "is_property": False,
        "signature": {"args": ["self"], "returns": "bool"},
    }


def _production_record(
    *,
    tier: str,
    file_path: str,
    identity: str,
    metadata: dict[str, Any],
    source_text: str = _METADATA_TEST_SOURCE,
) -> Any:
    """Build a chunk ``Record`` via the REAL ``records.chunk_to_record``.

    The resulting payload is byte-identical in shape to what an indexing run
    would upsert — the exact producer→consumer seam the C1a reshaping pins.
    """
    chunk = Chunk(
        chunk_type="python_symbol",
        source_text=source_text,
        identity=identity,
        line_start=1,
        line_end=source_text.count("\n") + 1,
        metadata=metadata,
    )
    return chunk_to_record(
        chunk,
        slug=SLUG,
        tier=tier,
        file_path=file_path,
        content_hash=sha512_hex(source_text),
        mtime_ns=time.time_ns(),
    )


# --- hand-built fragments (poison + synthetic telemetry) ---------------------


def _invalid_state_fragment(tier: str, poison_path: str) -> Any:
    """A fragment whose single statement violates the ``file.state`` ASSERT.

    A CREATE on a DISTINCT ``file`` record id (its own ``poison_path``, so the
    failure can never be an id clash with the manifest fragment's row) that sets
    ``state`` to an out-of-domain value. The engine rejects it at execution,
    rolling the WHOLE composed transaction back. Uses a ``px_`` param prefix,
    disjoint from every producer prefix, so composing it never collides.
    """
    return TxnFragment(
        statements=[
            f"CREATE type::record('{FILE_TABLE}', $px_id) SET "
            "sha512 = $px_sha, mtime_ns = $px_mtime, size = $px_size, "
            "n_chunks = $px_n, chunk_ids = $px_ids, state = $px_state, "
            "updated_at = $px_when"
        ],
        params={
            "px_id": [tier, poison_path],
            "px_sha": "0" * 128,
            "px_mtime": 0,
            "px_size": 0,
            "px_n": 0,
            "px_ids": [],
            "px_state": _INVALID_FILE_STATE,
            "px_when": datetime.now(UTC),
        },
    )


def _synthetic_fragment(statement_count: int) -> Any:
    """A fragment of ``statement_count`` trivial statements + as many params.

    Used ONLY by the telemetry cases (with ``execute_transaction`` monkeypatched
    to a no-op), so these statements are never actually sent to the server — the
    fragment exists purely to drive ``apply``'s statement/param COUNTING.
    """
    statements = [f"UPDATE marker:{index} SET n = $sy_p{index}" for index in range(statement_count)]
    params = {f"sy_p{index}": index for index in range(statement_count)}
    return TxnFragment(statements=statements, params=params)


# ===========================================================================
# Fixtures.
# ===========================================================================


@pytest.fixture(autouse=True)
def _reset_astroid_resolution_state() -> Iterator[None]:
    """Reset astroid's process-global resolution state around EVERY graph test,
    so one test's throwaway package cannot leak its warm cache / search-path
    entries into the next (same guard ``test_graph_surreal`` uses)."""
    clear_resolution_cache()
    reset_search_path_memo()
    yield
    clear_resolution_cache()
    reset_search_path_memo()


async def _new_store(env: SurrealEnv) -> SurrealStore:
    """A ready ``SurrealStore`` on ``env``'s database (applies the full DDL)."""
    store = SurrealStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        dim=env.dim,
        user=env.user,
        password=env.password,
    )
    await store.ensure_ready()
    return store


@pytest_asyncio.fixture()
async def apply_bench(
    surreal_env: SurrealEnv,  # noqa: F811
    tmp_path: Path,
) -> AsyncIterator[_Bench]:
    """Three components on ONE fresh database, each having applied its own schema
    slice, with the demo package on disk for astroid resolution.

    Store, manifest and graph each open their OWN connection: readiness applies
    the union of the DDL slices into the shared database (schema is DB-scoped),
    so the store's connection can write graph/manifest rows that the SEPARATE
    manifest/graph connections then read back — the cross-connection visibility
    the atomic ``apply`` depends on.
    """
    project_root = tmp_path / "project"
    _write_demo_package(project_root)

    store = await _new_store(surreal_env)
    manifest = SurrealManifest(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        user=surreal_env.user,
        password=surreal_env.password,
    )
    graph = SurrealCodeGraph(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        user=surreal_env.user,
        password=surreal_env.password,
        tier_roots={TIER_A: project_root, TIER_B: project_root},
        project_roots=[project_root],
    )
    await manifest.ensure_ready()
    await graph.ensure_ready()
    try:
        yield _Bench(
            store=store,
            manifest=manifest,
            graph=graph,
            env=surreal_env,
            project_root=project_root,
        )
    finally:
        await store.close()
        await manifest.close()
        await graph.close()


# ===========================================================================
# Raw-read helpers (fresh admin connection — independent of the store's own).
# ===========================================================================


async def _fetch_rows(
    env: SurrealEnv, statement: str, params: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Run a read on a fresh admin connection and return its dict rows."""
    connection = await connect_admin(env)
    try:
        result = await run(connection, statement, params or {})
    finally:
        await connection.close()
    return [row for row in result if isinstance(row, dict)] if isinstance(result, list) else []


async def _file_text_rows(env: SurrealEnv) -> list[dict[str, Any]]:
    """Every ``file_text`` row (id + body + digest), read raw off the engine."""
    return await _fetch_rows(env, f"SELECT id, text, sha512 FROM {FILE_TEXT_TABLE}")


# ===========================================================================
# 1. TxnFragment / compose — the composition primitive (PURE, no server).
# ===========================================================================


class TestTxnFragmentCompose:
    """``compose`` merges producer fragments into ONE ``BEGIN … COMMIT`` and
    refuses a param-name collision loudly — the seam where four modules' bound
    parameters land in one dict, exactly where a namespacing bug would corrupt a
    value silently."""

    def test_compose_wraps_fragments_in_exactly_one_begin_commit(self) -> None:
        # Arrange: two fragments with distinctive, collision-free statements.
        first = TxnFragment(statements=["UPDATE alpha:1 SET n = $a_n"], params={"a_n": 1})
        second = TxnFragment(statements=["UPDATE beta:2 SET n = $b_n"], params={"b_n": 2})

        # Act
        statement_text, _merged = compose(first, second)

        # Assert: exactly one transaction envelope wraps both bodies.
        assert statement_text.count("BEGIN") == 1
        assert statement_text.count("COMMIT") == 1
        assert statement_text.strip().startswith("BEGIN")
        assert statement_text.strip().endswith("COMMIT;")

    def test_compose_merges_all_fragment_params_without_loss(self) -> None:
        first = TxnFragment(statements=["UPDATE alpha:1 SET n = $a_n"], params={"a_n": 1})
        second = TxnFragment(
            statements=["UPDATE beta:2 SET n = $b_n"], params={"b_n": 2, "b_m": 3}
        )

        _text, merged = compose(first, second)

        # Every producer's params survive; the merged dict is exactly their union.
        assert merged == {"a_n": 1, "b_n": 2, "b_m": 3}
        assert len(merged) == len(first.params) + len(second.params)

    def test_compose_preserves_statement_order_across_fragments(self) -> None:
        # Order is load-bearing: a producer's DELETE-then-UPSERT must stay ordered,
        # and fragment order must stay stable (graph purge before store upsert, etc.).
        first = TxnFragment(statements=["UPDATE alpha:1 SET n = $a_n"], params={"a_n": 1})
        second = TxnFragment(
            statements=["UPDATE beta:2 SET n = $b_n", "UPDATE beta:3 SET n = $b_m"],
            params={"b_n": 2, "b_m": 3},
        )

        statement_text, _merged = compose(first, second)

        positions = [
            statement_text.index("alpha:1"),
            statement_text.index("beta:2"),
            statement_text.index("beta:3"),
        ]
        assert positions == sorted(positions)  # authored order preserved

    def test_compose_raises_typed_error_on_param_name_collision(self) -> None:
        # LOAD-BEARING: two producers that both bound the SAME param name would
        # silently overwrite one value in a naive merge. compose must REFUSE,
        # loudly and typed — this is the guard the whole namespacing scheme leans
        # on. Hand-built collision so the assertion is independent of any builder.
        left = TxnFragment(statements=["UPDATE alpha:1 SET n = $shared_id"], params={"shared_id": 1})
        right = TxnFragment(statements=["UPDATE beta:2 SET n = $shared_id"], params={"shared_id": 2})

        with pytest.raises(TxnParamCollisionError):
            compose(left, right)

    def test_compose_of_no_fragments_raises_value_error(self) -> None:
        # Composing nothing is a caller bug (an empty apply names no work) — loud,
        # never a silently-empty ``BEGIN … COMMIT`` that commits nothing.
        with pytest.raises(ValueError):
            compose()

    def test_a_built_fragment_carries_no_begin_or_commit_of_its_own(self) -> None:
        # A fragment is COMPOSABLE precisely because it owns no transaction
        # envelope — the envelope is added once, by compose. A builder that
        # embedded its own BEGIN/COMMIT would nest transactions on composition.
        fragment = TxnFragment(
            statements=["UPDATE alpha:1 SET n = $a_n", "DELETE alpha:2"], params={"a_n": 1}
        )
        for statement in fragment.statements:
            assert "BEGIN" not in statement
            assert "COMMIT" not in statement


# ===========================================================================
# 2. Param namespacing — each producer prefixes its params; the four real
#    builders compose without collision. The prefixes come from the SAME source
#    of truth production uses (imported constants), never hand-copied literals.
# ===========================================================================


class TestFragmentParamNamespacing:
    """Every producer stamps its bound params with a distinct prefix so four
    fragments merge into one param dict without clobbering each other."""

    async def test_chunk_replace_fragment_params_are_store_namespaced(
        self, apply_bench: _Bench
    ) -> None:
        record = _production_record(
            tier=TIER_A,
            file_path="models/purchase_order.py",
            identity="PurchaseOrder.action_confirm",
            metadata=_production_metadata(ident_text="PurchaseOrder action_confirm"),
        )
        fragment = apply_bench.store.replace_file_fragment(
            TIER_A, "models/purchase_order.py", [(record, unit_vector(0, apply_bench.env.dim))]
        )
        assert fragment.params, "the fragment must bind at least one param"
        assert all(key.startswith(CHUNK_FRAGMENT_PARAM_PREFIX) for key in fragment.params)

    async def test_file_text_fragment_params_are_file_text_namespaced(
        self, apply_bench: _Bench
    ) -> None:
        fragment = apply_bench.store.file_text_fragment(
            TIER_A, APP_PATH, APP_SOURCE, sha512_hex(APP_SOURCE)
        )
        assert fragment.params
        assert all(key.startswith(FILE_TEXT_FRAGMENT_PARAM_PREFIX) for key in fragment.params)

    async def test_manifest_replace_fragment_params_are_manifest_namespaced(
        self, apply_bench: _Bench
    ) -> None:
        fragment = apply_bench.manifest.replace_fragment(
            tier=TIER_A,
            file_path=APP_PATH,
            sha512=sha512_hex(APP_SOURCE),
            mtime_ns=time.time_ns(),
            size=len(APP_SOURCE.encode("utf-8")),
            n_chunks=0,
            chunk_ids=[],
            state=STATE_INDEXED,
        )
        assert fragment.params
        assert all(key.startswith(MANIFEST_FRAGMENT_PARAM_PREFIX) for key in fragment.params)

    async def test_graph_build_fragment_params_are_graph_namespaced(
        self, apply_bench: _Bench
    ) -> None:
        _write_source(apply_bench.project_root, APP_PATH, APP_SOURCE)
        fragment = apply_bench.graph.build_file_graph_fragment(
            TIER_A, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE
        )
        assert fragment.params
        assert all(key.startswith(GRAPH_FRAGMENT_PARAM_PREFIX) for key in fragment.params)

    async def test_the_four_real_builders_compose_without_param_collision(
        self, apply_bench: _Bench
    ) -> None:
        # The whole point of the namespacing scheme: the four REAL producers'
        # fragments for one file merge into a single transaction with NO collision
        # and NO lost param — the merged dict has exactly the sum of the parts.
        built = _fragments_for_file(
            apply_bench, tier=TIER_A, path=APP_PATH, source=APP_SOURCE, module=APP_MODULE
        )
        _statement_text, merged = compose(*built.fragments)
        expected_param_count = sum(len(fragment.params) for fragment in built.fragments)
        assert len(merged) == expected_param_count, "a collision silently dropped a param"


# ===========================================================================
# 3. Chunk fragment reshaping — the C1a seam BOTH write paths must keep. The
#    fragment builder validates dims + reshapes production-shaped metadata at
#    BUILD time (pure), and refuses reserved keys loudly, exactly like the
#    inline ``replace_file`` path does.
# ===========================================================================


class TestChunkFragmentReshaping:
    """The chunk fragment builder is a WRITE path, so it inherits the C1a
    contract: production metadata spreads top-level, reserved keys are refused,
    wrong-width vectors are rejected — all at build, before any statement runs."""

    async def test_replace_file_fragment_rejects_metadata_key_named_embedding_at_build(
        self, apply_bench: _Bench
    ) -> None:
        # A chunker metadata key literally named ``embedding`` would nest on write
        # and spuriously reappear top-level on read-merge — reserved, refused
        # LOUDLY at BUILD time (no I/O), so nothing is ever composed or applied.
        metadata = _production_metadata(ident_text="ResUsers has_group")
        metadata["embedding"] = "chunker-emitted-lookalike"
        record = _production_record(
            tier=TIER_A,
            file_path="models/res_users.py",
            identity="ResUsers.has_group",
            metadata=metadata,
        )
        with pytest.raises(SurrealStoreError):
            apply_bench.store.replace_file_fragment(
                TIER_A, "models/res_users.py", [(record, unit_vector(0, apply_bench.env.dim))]
            )

    async def test_replace_file_fragment_rejects_nondict_metadata_key_at_build(
        self, apply_bench: _Bench
    ) -> None:
        # A ``metadata`` key with a NON-dict value is neither the production nor
        # the legacy nested shape — refused rather than silently dropped.
        metadata = _production_metadata(ident_text="ResPartner name_get")
        metadata["metadata"] = "a-string-label"
        record = _production_record(
            tier=TIER_A,
            file_path="models/res_partner.py",
            identity="ResPartner.name_get",
            metadata=metadata,
        )
        with pytest.raises(SurrealStoreError):
            apply_bench.store.replace_file_fragment(
                TIER_A, "models/res_partner.py", [(record, unit_vector(0, apply_bench.env.dim))]
            )

    async def test_replace_file_fragment_rejects_wrong_dim_vector_at_build(
        self, apply_bench: _Bench
    ) -> None:
        # A wrong-width vector is a probe-gate failure: rejected LOUDLY at build,
        # so a malformed batch never even reaches ``compose``/``apply``.
        record = _production_record(
            tier=TIER_A,
            file_path="models/x.py",
            identity="X.method",
            metadata=_production_metadata(ident_text="X method"),
        )
        wrong_width = [0.1] * (PRODUCTION_DIM // 4)  # 512 against a 2048 store
        with pytest.raises(VectorDimensionError):
            apply_bench.store.replace_file_fragment(
                TIER_A, "models/x.py", [(record, wrong_width)]
            )

    async def test_apply_round_trips_production_shaped_metadata_top_level(
        self, apply_bench: _Bench
    ) -> None:
        # End-to-end through apply: a real ``chunk_to_record`` payload (metadata
        # spread top-level, no wrapper key) survives the composed transaction and
        # comes back PER-KEY EQUAL from scroll, with no internal "metadata"
        # wrapper riding along — the canonical API-boundary shape.
        file_path = "models/purchase_order.py"
        metadata = _production_metadata(ident_text="PurchaseOrder action_confirm")
        record = _production_record(
            tier=TIER_A,
            file_path=file_path,
            identity="PurchaseOrder.action_confirm",
            metadata=metadata,
        )
        fragment = apply_bench.store.replace_file_fragment(
            TIER_A, file_path, [(record, unit_vector(0, apply_bench.env.dim))]
        )
        await apply_bench.store.apply([fragment])

        rows = await apply_bench.store.scroll({"file_path": file_path}, limit=_READ_ALL)
        assert len(rows) == 1
        row = rows[0]
        for key, expected_value in record.payload.items():
            assert row.get(key) == expected_value, (
                f"payload key {key!r} did not round-trip: "
                f"expected {expected_value!r}, got {row.get(key)!r}"
            )
        assert "metadata" not in row  # no wrapper key duplicating the flattened data


# ===========================================================================
# 4. Atomic success — one apply persists chunks + file_text + manifest + graph,
#    each readable through the SEPARATE reader connections (cross-connection
#    visibility). Oracles are read off the authored sources, never the engine.
# ===========================================================================


class TestApplyAtomicSuccess:
    """A single ``apply`` of all four producers' fragments for one file lands
    every surface, visible across the independent connections."""

    async def test_apply_persists_chunks_file_text_manifest_and_graph(
        self, apply_bench: _Bench
    ) -> None:
        built = _fragments_for_file(
            apply_bench, tier=TIER_A, path=APP_PATH, source=APP_SOURCE, module=APP_MODULE
        )
        await apply_bench.store.apply(built.fragments)

        # 1) chunks — scrollable via the store; identities match the producer's.
        rows = await apply_bench.store.scroll(
            {"tier": TIER_A, "file_path": APP_PATH}, limit=_READ_ALL
        )
        assert frozenset(row["identity"] for row in rows) == built.identities
        assert await apply_bench.store.count() == len(built.records)

        # 2) file_text — the verbatim body + shared digest (raw read).
        file_text_rows = await _file_text_rows(apply_bench.env)
        assert len(file_text_rows) == 1
        assert file_text_rows[0]["text"] == APP_SOURCE
        assert file_text_rows[0]["sha512"] == built.file_sha

        # 3) manifest — visible via a SEPARATE SurrealManifest connection.
        file_row = await apply_bench.manifest.get(TIER_A, APP_PATH)
        assert file_row is not None
        assert file_row.state == STATE_INDEXED
        assert file_row.n_chunks == len(built.records)
        assert frozenset(file_row.chunk_ids) == built.point_ids
        assert file_row.sha512 == built.file_sha

        # 4) graph — queryable via a SEPARATE SurrealCodeGraph connection.
        # Independent oracle (APP_SOURCE): ``demo.service`` imports LoadError, and
        # IndexService inherits BaseService.
        importers = {node.qualified_name for node in await apply_bench.graph.what_imports(FQN_LOAD_ERROR)}
        assert APP_MODULE in importers
        dependents = {
            node.qualified_name
            for node in await apply_bench.graph.blast_radius(FQN_BASE, depth=3, max_results=100)
        }
        assert FQN_INDEX in dependents
        # Sanity bound on a derived count: BaseService is inherited in production
        # (alive), and no test file was built, so test refs are zero.
        summary = await apply_bench.graph.references(FQN_BASE)
        assert summary.production_references >= 1
        assert summary.test_references == 0

    async def test_apply_writes_file_text_with_full_body_and_sha512(
        self, apply_bench: _Bench
    ) -> None:
        # Focused on the NEW writer: the WHOLE body round-trips byte-equal (not a
        # truncated/normalised copy) and the digest is the independent
        # ``records.sha512_hex`` of that same body (128 hex chars) — verified
        # against an oracle recomputed here, not echoed from the row.
        source = APP_SOURCE
        expected_sha = sha512_hex(source)
        fragment = apply_bench.store.file_text_fragment(TIER_A, APP_PATH, source, expected_sha)
        await apply_bench.store.apply([fragment])

        rows = await _file_text_rows(apply_bench.env)
        assert len(rows) == 1
        assert rows[0]["text"] == source
        assert rows[0]["sha512"] == expected_sha
        assert len(rows[0]["sha512"]) == 128  # a full SHA-512 hex digest, not a stub

    async def test_file_text_composite_id_keeps_two_tiers_distinct(
        self, apply_bench: _Bench
    ) -> None:
        # C1 discipline mirrored onto file_text: the record id must fold in
        # ``tier`` (the ``[tier, file_path]`` composite the ``file`` table uses),
        # so a custom override and the community original of one path COEXIST
        # rather than the second overwriting the first.
        sha = sha512_hex(APP_SOURCE)
        await apply_bench.store.apply(
            [apply_bench.store.file_text_fragment(TIER_A, APP_PATH, APP_SOURCE, sha)]
        )
        await apply_bench.store.apply(
            [apply_bench.store.file_text_fragment(TIER_B, APP_PATH, APP_SOURCE, sha)]
        )

        rows = await _file_text_rows(apply_bench.env)
        composite_ids = {tuple(row["id"].id) for row in rows}
        assert composite_ids == {(TIER_A, APP_PATH), (TIER_B, APP_PATH)}

    async def test_apply_file_with_no_chunks_still_writes_file_text_and_manifest(
        self, apply_bench: _Bench
    ) -> None:
        # A degenerate but real case: a data/module file that yields ZERO chunks.
        # The store fragment upserts nothing (and deletes any stale), yet the
        # file_text body and the manifest row (n_chunks=0, chunk_ids=[]) must
        # still land — a bug that skipped these on an empty chunk set would leave
        # the body unsearchable and the manifest blind to the file.
        path = "data/empty_module.py"
        source = '"""A data module with no indexable symbols."""\n'
        file_sha = sha512_hex(source)
        fragments = [
            apply_bench.store.replace_file_fragment(TIER_A, path, []),
            apply_bench.store.file_text_fragment(TIER_A, path, source, file_sha),
            apply_bench.manifest.replace_fragment(
                tier=TIER_A,
                file_path=path,
                sha512=file_sha,
                mtime_ns=time.time_ns(),
                size=len(source.encode("utf-8")),
                n_chunks=0,
                chunk_ids=[],
                state=STATE_INDEXED,
            ),
        ]
        await apply_bench.store.apply(fragments)

        assert await apply_bench.store.scroll({"file_path": path}, limit=_READ_ALL) == []
        file_row = await apply_bench.manifest.get(TIER_A, path)
        assert file_row is not None
        assert file_row.n_chunks == 0
        assert file_row.chunk_ids == []
        assert file_row.state == STATE_INDEXED
        assert any(row["text"] == source for row in await _file_text_rows(apply_bench.env))


# ===========================================================================
# 5. Mid-transaction failure → NOTHING applied. Compose the four good fragments
#    PLUS a deliberately-failing one (an out-of-domain file.state) and confirm
#    apply raises a typed store error while EVERY surface reads back empty —
#    in both fragment orders.
# ===========================================================================


class TestApplyMidTxnFailureRollsBackEverything:
    """One rejected statement rolls the WHOLE composed transaction back: no
    chunks, no file_text, no manifest row, no graph nodes — and the error is a
    domain rejection (store error), never a connection fault."""

    def test_poison_state_is_genuinely_out_of_domain(self) -> None:
        # Guard the poison itself: its rejection is guaranteed by the schema's
        # closed ``file.state`` domain, not by luck — pinned against the SHARED
        # ``FILE_STATES`` source of truth, so a future domain change surfaces here.
        assert _INVALID_FILE_STATE not in FILE_STATES

    async def _assert_nothing_applied(self, bench: _Bench, poison_path: str) -> None:
        """Every surface reads back its prior/empty state after a rollback."""
        assert await bench.store.count() == 0
        assert await bench.store.scroll({"tier": TIER_A, "file_path": APP_PATH}, limit=_READ_ALL) == []
        assert await _file_text_rows(bench.env) == []
        assert await bench.manifest.get(TIER_A, APP_PATH) is None
        assert await bench.manifest.get(TIER_A, poison_path) is None  # the poison row too
        assert await bench.graph.indexed_file_count() == 0
        assert await bench.graph.what_imports(FQN_LOAD_ERROR) == []

    async def test_failing_fragment_last_rolls_back_all_surfaces(
        self, apply_bench: _Bench
    ) -> None:
        poison_path = "demo/__poison_last__.py"
        built = _fragments_for_file(
            apply_bench, tier=TIER_A, path=APP_PATH, source=APP_SOURCE, module=APP_MODULE
        )
        fragments = [*built.fragments, _invalid_state_fragment(TIER_A, poison_path)]

        connection_before = apply_bench.store._connection
        with pytest.raises(SurrealStoreError) as exc_info:
            await apply_bench.store.apply(fragments)
        # A domain/schema rejection is a STORE error, never a connection fault,
        # and must never throw away a healthy connection.
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert apply_bench.store._connection is connection_before

        await self._assert_nothing_applied(apply_bench, poison_path)

    async def test_failing_fragment_first_rolls_back_all_surfaces(
        self, apply_bench: _Bench
    ) -> None:
        # Reverse order: the failure at the FRONT must still roll back the good
        # fragments that follow it — the envelope, not position, provides atomicity.
        poison_path = "demo/__poison_first__.py"
        built = _fragments_for_file(
            apply_bench, tier=TIER_A, path=APP_PATH, source=APP_SOURCE, module=APP_MODULE
        )
        fragments = [_invalid_state_fragment(TIER_A, poison_path), *built.fragments]

        with pytest.raises(SurrealStoreError):
            await apply_bench.store.apply(fragments)

        await self._assert_nothing_applied(apply_bench, poison_path)


# ===========================================================================
# 6. Replace semantics — a second apply over an already-populated file removes
#    stale chunks/edges and updates the manifest, all atomically. A concurrent
#    reader mid-apply sees ONLY the old or ONLY the new state.
# ===========================================================================


class TestApplyReplaceSemantics:
    """Re-applying a changed file fully re-derives it: stale chunks gone, stale
    graph edges gone, manifest updated — with snapshot isolation for readers."""

    async def test_reapply_removes_stale_chunks_and_graph_edges_and_updates_manifest(
        self, apply_bench: _Bench
    ) -> None:
        first = _fragments_for_file(
            apply_bench, tier=TIER_A, path=APP_PATH, source=APP_SOURCE, module=APP_MODULE
        )
        await apply_bench.store.apply(first.fragments)
        # Pre-state oracle (APP_SOURCE): the LoadError import edge exists.
        assert APP_MODULE in {
            node.qualified_name for node in await apply_bench.graph.what_imports(FQN_LOAD_ERROR)
        }

        second = _fragments_for_file(
            apply_bench, tier=TIER_A, path=APP_PATH, source=APP_SOURCE_V2, module=APP_MODULE
        )
        await apply_bench.store.apply(second.fragments)

        # Stale chunk removal: the surviving identities are EXACTLY v2's — the v1
        # ``load_config`` chunk is gone, v2's ``save_config`` present.
        surviving = frozenset(
            row["identity"]
            for row in await apply_bench.store.scroll(
                {"tier": TIER_A, "file_path": APP_PATH}, limit=_READ_ALL
            )
        )
        assert surviving == second.identities
        assert surviving != first.identities  # the set genuinely changed
        assert await apply_bench.store.count() == len(second.records)

        # Stale EDGE removal: v2 dropped the LoadError import, so no importer
        # remains — proving the old edge was purged, not merely shadowed.
        assert await apply_bench.graph.what_imports(FQN_LOAD_ERROR) == []

        # Manifest updated to v2's chunk set + digest.
        file_row = await apply_bench.manifest.get(TIER_A, APP_PATH)
        assert file_row is not None
        assert frozenset(file_row.chunk_ids) == second.point_ids
        assert file_row.n_chunks == len(second.records)
        assert file_row.sha512 == second.file_sha

    async def test_concurrent_reader_never_observes_a_partial_apply(
        self, apply_bench: _Bench
    ) -> None:
        # A reader on a SEPARATE store connection scrolls the file's chunk
        # identities in a tight loop while a replace apply commits on the writer's
        # connection. Every snapshot must be a COMPLETE pre- or post-commit state:
        # v2 both removes (load_config) and adds (save_config) a chunk, so a
        # non-atomic delete-then-insert would leak a set equal to NEITHER v1 nor
        # v2 and be caught here.
        first = _fragments_for_file(
            apply_bench, tier=TIER_A, path=APP_PATH, source=APP_SOURCE, module=APP_MODULE
        )
        await apply_bench.store.apply(first.fragments)
        second = _fragments_for_file(
            apply_bench, tier=TIER_A, path=APP_PATH, source=APP_SOURCE_V2, module=APP_MODULE
        )

        reader = await _new_store(apply_bench.env)
        observed: list[frozenset[str]] = []
        try:

            async def read_loop() -> None:
                for _ in range(150):
                    rows = await reader.scroll(
                        {"tier": TIER_A, "file_path": APP_PATH}, limit=_READ_ALL
                    )
                    observed.append(frozenset(row["identity"] for row in rows))
                    await asyncio.sleep(0)

            async def write_once() -> None:
                await asyncio.sleep(0.002)  # let the reader loop get going
                await apply_bench.store.apply(second.fragments)

            await asyncio.gather(read_loop(), write_once())

            for snapshot in observed:
                assert snapshot in (first.identities, second.identities), (
                    f"partial file state observed mid-apply: {sorted(snapshot)}"
                )
            # Post-condition: the replace committed the new content.
            final = frozenset(
                row["identity"]
                for row in await reader.scroll(
                    {"tier": TIER_A, "file_path": APP_PATH}, limit=_READ_ALL
                )
            )
            assert final == second.identities
        finally:
            await reader.close()


# ===========================================================================
# 7. Purge composition — one apply of the four DELETE fragments removes
#    everything for a file, atomically.
# ===========================================================================


class TestApplyPurgeComposition:
    """A file's full removal is itself a composed apply: store-delete +
    file_text-delete + manifest-delete + graph-purge in one transaction."""

    async def test_purge_apply_removes_chunks_file_text_manifest_and_graph(
        self, apply_bench: _Bench
    ) -> None:
        built = _fragments_for_file(
            apply_bench, tier=TIER_A, path=APP_PATH, source=APP_SOURCE, module=APP_MODULE
        )
        await apply_bench.store.apply(built.fragments)
        # Sanity: it really was populated before the purge.
        assert await apply_bench.store.count() == len(built.records)

        purge_fragments = [
            apply_bench.store.delete_file_fragment(TIER_A, APP_PATH),
            apply_bench.store.file_text_delete_fragment(TIER_A, APP_PATH),
            apply_bench.manifest.delete_fragment(TIER_A, APP_PATH),
            apply_bench.graph.purge_file_fragment(TIER_A, APP_PATH),
        ]
        await apply_bench.store.apply(purge_fragments)

        assert await apply_bench.store.count() == 0
        assert await apply_bench.store.scroll({"file_path": APP_PATH}, limit=_READ_ALL) == []
        assert await _file_text_rows(apply_bench.env) == []
        assert await apply_bench.manifest.get(TIER_A, APP_PATH) is None
        assert await apply_bench.graph.indexed_file_count() == 0
        assert await apply_bench.graph.what_imports(FQN_LOAD_ERROR) == []


# ===========================================================================
# 8. Idempotence under rerun — a successful apply leaves state a second
#    identical apply reproduces exactly (the cheap proxy for the engine's
#    whole-block conflict retry re-running the composed transaction safely).
# ===========================================================================


class TestApplyIdempotenceUnderRerun:
    """execute_transaction re-runs the ENTIRE composed block on a retryable
    conflict, so applying the same fragments twice must converge on identical
    state — deterministic ids/composite keys make the second run overwrite in
    place, never duplicate."""

    async def _stable_state(self, bench: _Bench, tier: str, path: str) -> tuple[Any, ...]:
        """The rerun-invariant projection (excludes the manifest's ``updated_at``,
        which is a wall-clock stamp, not a data value)."""
        chunk_identities = frozenset(
            row["identity"]
            for row in await bench.store.scroll({"tier": tier, "file_path": path}, limit=_READ_ALL)
        )
        file_text = {(row["text"], row["sha512"]) for row in await _file_text_rows(bench.env)}
        file_row = await bench.manifest.get(tier, path)
        manifest_projection = (
            None
            if file_row is None
            else (file_row.sha512, tuple(sorted(file_row.chunk_ids)), file_row.n_chunks, file_row.state)
        )
        importers = frozenset(
            node.qualified_name for node in await bench.graph.what_imports(FQN_LOAD_ERROR)
        )
        return (chunk_identities, file_text, manifest_projection, importers)

    async def test_second_identical_apply_reproduces_state(
        self, apply_bench: _Bench
    ) -> None:
        built = _fragments_for_file(
            apply_bench, tier=TIER_A, path=APP_PATH, source=APP_SOURCE, module=APP_MODULE
        )
        await apply_bench.store.apply(built.fragments)
        state_after_first = await self._stable_state(apply_bench, TIER_A, APP_PATH)

        # Re-run the SAME composed fragments (the whole-block-retry proxy).
        await apply_bench.store.apply(built.fragments)
        state_after_second = await self._stable_state(apply_bench, TIER_A, APP_PATH)

        assert state_after_second == state_after_first
        # And the store did not duplicate the chunks on the rerun.
        assert await apply_bench.store.count() == len(built.records)


# ===========================================================================
# 9. Transaction-size telemetry — apply logs the statement + param counts and
#    WARNs above the documented threshold. execute_transaction is monkeypatched
#    to a no-op so a large SYNTHETIC fragment never hits the shared server.
# ===========================================================================

_TELEMETRY_SMALL_STATEMENTS = 5


class TestApplyTxnSizeTelemetry:
    """apply reports how big a transaction it is about to run and warns when it
    grows past the documented ceiling — the guard against an accidental
    thousands-of-statements batch. No real statements are sent here."""

    def _offline_store(
        self, env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> tuple[SurrealStore, dict[str, Any]]:
        """A store whose ``execute_transaction`` is replaced by a capturing no-op,
        so ``apply`` composes + logs without opening a socket."""
        captured: dict[str, Any] = {}

        async def _fake_execute_transaction(
            statement: str, params: dict[str, Any], **_kwargs: Any
        ) -> None:
            captured["statement"] = statement
            captured["params"] = params

        monkeypatch.setattr(
            "loremaster.store.surreal.execute_transaction", _fake_execute_transaction
        )
        store = SurrealStore(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            dim=env.dim,
            user=env.user,
            password=env.password,
        )
        return store, captured

    async def test_apply_logs_statement_and_param_counts(
        self,
        surreal_env: SurrealEnv,  # noqa: F811
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        store, _captured = self._offline_store(surreal_env, monkeypatch)
        fragment = _synthetic_fragment(_TELEMETRY_SMALL_STATEMENTS)

        with caplog.at_level(logging.DEBUG, logger="loremaster.store.surreal"):
            await store.apply([fragment])

        count_records = [
            record for record in caplog.records if getattr(record, "statement_count", None) is not None
        ]
        assert count_records, "apply must log the transaction's statement/param counts"
        record = count_records[0]
        assert getattr(record, "statement_count") == _TELEMETRY_SMALL_STATEMENTS  # noqa: B009 - logging extra, unknown to mypy
        assert getattr(record, "param_count") == _TELEMETRY_SMALL_STATEMENTS  # noqa: B009 - logging extra, unknown to mypy

    async def test_apply_warns_above_statement_threshold(
        self,
        surreal_env: SurrealEnv,  # noqa: F811
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        store, _captured = self._offline_store(surreal_env, monkeypatch)
        # One past the documented ceiling (read from the shared constant, never a
        # hand-copied number) — enough to trip the WARNING.
        oversized = _synthetic_fragment(TXN_STATEMENT_WARN_THRESHOLD + 1)

        with caplog.at_level(logging.DEBUG, logger="loremaster.store.surreal"):
            await store.apply([oversized])

        warnings = [
            record
            for record in caplog.records
            if record.levelno == logging.WARNING and getattr(record, "statement_count", None) is not None
        ]
        assert warnings, "apply must WARN when the transaction exceeds the threshold"
        assert getattr(warnings[0], "statement_count") > TXN_STATEMENT_WARN_THRESHOLD  # noqa: B009 - logging extra, unknown to mypy

    async def test_apply_stays_quiet_below_statement_threshold(
        self,
        surreal_env: SurrealEnv,  # noqa: F811
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        # The negative: a normal-sized transaction must NOT warn (else the warning
        # is noise and gets ignored when it matters).
        store, _captured = self._offline_store(surreal_env, monkeypatch)

        with caplog.at_level(logging.DEBUG, logger="loremaster.store.surreal"):
            await store.apply([_synthetic_fragment(_TELEMETRY_SMALL_STATEMENTS)])

        store_warnings = [
            record
            for record in caplog.records
            if record.name.startswith("loremaster.store") and record.levelno >= logging.WARNING
        ]
        assert store_warnings == []


# ===========================================================================
# 10. Composed-transaction hardening (P5-C3a, ledger security-audit items):
#     (a) a HARD ceiling on the composed body-statement count — the write-path
#         analogue of the read path's ``k`` clamp, guarding the SHARED server
#         against a pathological file (e.g. 100k tiny generated functions)
#         producing one multi-hundred-thousand-statement transaction
#         (cross-tenant DoS);
#     (b) an envelope-integrity assert in ``compose()`` against a fragment
#         statement that smuggles its own bare ``BEGIN``/``COMMIT``/internal
#         statement separator, which would close the atomic envelope early or
#         split one declared statement into several UNTRACKED ones;
#     (c) a byte-size bound on ``file_text_fragment``'s body, so one pathological
#         file can never inflate a single row (and the composed transaction it
#         rides in) without limit.
# All three raise BEFORE anything is composed or sent to the server. Every
# case here uses ONLY synthetic fragments / offline (monkeypatched) stores —
# never a giant real transaction against the shared server.
# ===========================================================================

# The sharpest boundary probe: exactly one statement past the hard cap, so the
# over-cap tests exercise the ceiling itself rather than some arbitrarily
# larger number that could pass even a badly off-by-N implementation.
_HARD_CAP_OVERAGE = 1


class TestComposeStatementHardCap:
    """``compose()`` (and therefore ``apply()``, which calls it first) refuses
    to build a transaction whose body-statement count exceeds
    :data:`TXN_STATEMENT_HARD_CAP` — a ceiling well above the existing
    :data:`TXN_STATEMENT_WARN_THRESHOLD` WARN, so a batch that only warns today
    keeps composing, while a genuinely pathological one is refused outright.
    """

    def test_compose_raises_surreal_store_error_over_the_hard_cap(self) -> None:
        # Arrange: the pathological-file shape — one fragment whose statement
        # count alone exceeds the ceiling (mirrors a 100k-tiny-function file
        # whose chunk-replace fragment would otherwise emit one UPSERT per
        # function in a single composed transaction).
        over_cap_count = TXN_STATEMENT_HARD_CAP + _HARD_CAP_OVERAGE
        oversized = _synthetic_fragment(over_cap_count)

        # Act & Assert
        with pytest.raises(SurrealStoreError) as exc_info:
            compose(oversized)
        message = str(exc_info.value)
        # The message names BOTH the actual count and the configured cap, so
        # an operator can see the real number without re-deriving it from logs.
        assert str(over_cap_count) in message, "error message must name the actual statement count"
        assert str(TXN_STATEMENT_HARD_CAP) in message, "error message must name the configured cap"

    def test_compose_accepts_exactly_at_the_hard_cap(self) -> None:
        # The boundary itself must compose fine — a ceiling, not an off-by-one
        # trap that rejects a legitimately-sized batch sitting exactly on it.
        at_cap = _synthetic_fragment(TXN_STATEMENT_HARD_CAP)

        statement_text, merged_params = compose(at_cap)

        assert len(merged_params) == TXN_STATEMENT_HARD_CAP
        assert statement_text.count("BEGIN") == 1
        assert statement_text.count("COMMIT") == 1

    def test_compose_still_succeeds_above_warn_threshold_but_below_hard_cap(self) -> None:
        # The hard cap is a DISTINCT, HIGHER ceiling than the existing WARN
        # threshold, not a tightening of it: a batch that trips the WARN (see
        # ``TestApplyTxnSizeTelemetry``) must still compose successfully so
        # long as it stays under the hard cap.
        between_count = TXN_STATEMENT_WARN_THRESHOLD + 1
        assert between_count < TXN_STATEMENT_HARD_CAP, (
            "fixture assumption: the warn threshold must sit strictly below the hard cap"
        )
        between = _synthetic_fragment(between_count)

        _statement_text, merged_params = compose(between)

        assert len(merged_params) == between_count


class TestApplyStatementHardCapNeverReachesTheServer:
    """``apply()`` surfaces the same hard-cap rejection — and, critically,
    never calls ``execute_transaction`` when it does: the whole point of a
    BUILD-time cap is that a pathological batch never even reaches the socket,
    let alone strains the shared server."""

    def _offline_store(
        self, env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> tuple[SurrealStore, dict[str, Any]]:
        """Mirrors ``TestApplyTxnSizeTelemetry._offline_store``: a store whose
        ``execute_transaction`` is replaced by a capturing no-op, so a
        hard-cap violation can be proven to reach zero network I/O.
        """
        captured: dict[str, Any] = {}

        async def _fake_execute_transaction(
            statement: str, params: dict[str, Any], **_kwargs: Any
        ) -> None:
            captured["statement"] = statement
            captured["params"] = params

        monkeypatch.setattr(
            "loremaster.store.surreal.execute_transaction", _fake_execute_transaction
        )
        store = SurrealStore(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            dim=env.dim,
            user=env.user,
            password=env.password,
        )
        return store, captured

    async def test_apply_raises_and_never_calls_execute_transaction_over_hard_cap(
        self,
        surreal_env: SurrealEnv,  # noqa: F811
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        store, captured = self._offline_store(surreal_env, monkeypatch)
        oversized = _synthetic_fragment(TXN_STATEMENT_HARD_CAP + _HARD_CAP_OVERAGE)

        with pytest.raises(SurrealStoreError):
            await store.apply([oversized])

        # LOAD-BEARING: nothing was ever handed to the transport layer.
        assert captured == {}, "execute_transaction must never run for an over-cap transaction"


class TestComposeEnvelopeIntegrity:
    """``compose()`` refuses a fragment statement that could close or split the
    single atomic envelope early — the probe-confirmed exploit shape where a
    bare ``BEGIN``/``COMMIT`` (or an internal statement separator) rides
    inside one fragment's statement text, so everything composed after it
    would run OUTSIDE the intended atomic block. Must be word-boundary-aware:
    a column/identifier that merely CONTAINS the substring ``commit``/``begin``
    (e.g. a future git-provenance ``commit_hash`` audit column) is ordinary,
    legitimate SurrealQL and must NOT be flagged.
    """

    def test_txn_envelope_violation_error_is_a_surreal_store_error(self) -> None:
        # Type-hierarchy pin: callers that already catch ``SurrealStoreError``
        # (e.g. every existing ``apply()`` caller) catch this too, with no
        # code change required.
        assert issubclass(TxnEnvelopeViolationError, SurrealStoreError)

    def test_raises_on_statement_containing_bare_uppercase_commit_keyword(self) -> None:
        # The probe-confirmed exploit shape verbatim: an embedded COMMIT closes
        # the envelope early, so the DELETE after it would run OUTSIDE the
        # atomic block once composed.
        poisoned = TxnFragment(
            statements=["UPDATE alpha:1 SET n = $a_n; COMMIT; DELETE alpha:2"],
            params={"a_n": 1},
        )
        with pytest.raises(TxnEnvelopeViolationError):
            compose(poisoned)

    def test_raises_on_statement_containing_bare_uppercase_begin_keyword(self) -> None:
        # The mirror-image poison: a smuggled BEGIN would open a SECOND,
        # nested envelope inside the one ``compose()`` adds.
        poisoned = TxnFragment(
            statements=["UPDATE alpha:1 SET n = $a_n; BEGIN; DELETE alpha:2"],
            params={"a_n": 1},
        )
        with pytest.raises(TxnEnvelopeViolationError):
            compose(poisoned)

    def test_raises_on_lowercase_bare_commit_keyword(self) -> None:
        # SurrealQL keywords are case-insensitive to the engine even though
        # every builder in this codebase emits uppercase — the guard must not
        # be foolable by casing alone.
        poisoned = TxnFragment(
            statements=["UPDATE alpha:1 SET n = $a_n; commit; DELETE alpha:2"],
            params={"a_n": 1},
        )
        with pytest.raises(TxnEnvelopeViolationError):
            compose(poisoned)

    def test_raises_on_statement_with_internal_separator_and_no_keyword(self) -> None:
        # No BEGIN/COMMIT keyword at all — just two statements smuggled into
        # ONE fragment "statement" string via an embedded ``;``. Still a
        # violation: the fragment's declared statement count (what
        # ``TestComposeStatementHardCap`` counts against the hard cap) would
        # silently UNDERCOUNT the true number of statements actually executed.
        poisoned = TxnFragment(
            statements=["UPDATE alpha:1 SET n = $a_n; DELETE alpha:2"],
            params={"a_n": 1},
        )
        with pytest.raises(TxnEnvelopeViolationError):
            compose(poisoned)

    def test_does_not_raise_on_column_identifier_containing_commit_substring(self) -> None:
        # NOT a false positive: ``commit_hash`` contains ``commit`` but is not
        # the bare keyword (no word boundary immediately follows — ``_`` is a
        # word character) — a plausible real audit column (the git commit a
        # chunk was indexed from), on the REAL chunk table.
        fragment = TxnFragment(
            statements=[f"UPDATE {CHUNK_TABLE} SET commit_hash = $st_x"],
            params={"st_x": "a3f9c21e7b0d4c6f9a1b2c3d4e5f60718293a4b5"},
        )
        _statement_text, _merged = compose(fragment)  # must not raise

    def test_does_not_raise_on_column_identifier_containing_begin_substring(self) -> None:
        # Same word-boundary safety for ``begin``: a plausible byte-offset
        # audit column, not the bare keyword.
        fragment = TxnFragment(
            statements=[f"UPDATE {CHUNK_TABLE} SET begin_offset = $st_x"],
            params={"st_x": 4096},
        )
        _statement_text, _merged = compose(fragment)  # must not raise

    def test_does_not_raise_on_identifier_where_commit_is_a_non_prefix_substring(self) -> None:
        # ``recommit_flag`` — ``commit`` is preceded by ``e`` (also a word
        # character), so there is no boundary on EITHER side; must not be
        # mistaken for the bare keyword.
        fragment = TxnFragment(
            statements=[f"UPDATE {CHUNK_TABLE} SET recommit_flag = $st_x"],
            params={"st_x": True},
        )
        _statement_text, _merged = compose(fragment)  # must not raise

    def test_does_not_raise_when_commit_appears_only_in_a_bound_param_value(self) -> None:
        # The word "COMMIT" inside DATA (a bound param value — e.g. genuine
        # prose in an indexed docstring or commit-message chunk) is not
        # statement TEXT at all; only the SurrealQL text is scanned, never the
        # param values a producer binds.
        fragment = TxnFragment(
            statements=["UPDATE alpha:1 SET note = $a_note"],
            params={"a_note": "Please COMMIT this change before the release."},
        )
        _statement_text, _merged = compose(fragment)  # must not raise

    def test_does_not_raise_on_statement_with_a_single_ordinary_trailing_semicolon(self) -> None:
        # The ordinary shape a real builder may emit (see
        # ``_normalise_statement``'s trailing-terminator handling) — a single
        # trailing ``;`` must never be mistaken for an "internal" separator.
        fragment = TxnFragment(statements=["UPDATE alpha:1 SET n = $a_n;"], params={"a_n": 1})
        _statement_text, _merged = compose(fragment)  # must not raise


class TestFileTextFragmentSizeBound:
    """``file_text_fragment`` refuses an oversized body at BUILD time —
    nothing is composed or sent for a file whose whole verbatim text would
    blow past a sane per-row ceiling (:data:`FILE_TEXT_MAX_BYTES`)."""

    @staticmethod
    def _bare_store(env: SurrealEnv) -> SurrealStore:
        """A ``SurrealStore`` that never opens a connection.

        ``file_text_fragment`` is a pure builder (no I/O, like
        ``replace_file_fragment``) — these tests never call ``ensure_ready()``
        or ``apply()``, so no live server round trip happens for any case
        here, including the exactly-at-cap acceptance case.
        """
        return SurrealStore(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            dim=env.dim,
            user=env.user,
            password=env.password,
        )

    async def test_raises_surreal_store_error_for_body_one_byte_over_the_cap(
        self, surreal_env: SurrealEnv  # noqa: F811
    ) -> None:
        store = self._bare_store(surreal_env)
        # ASCII text: 1 byte/char, so the char count IS the UTF-8 byte count —
        # the sharpest boundary probe (exactly one byte over the cap).
        oversized_text = "x" * (FILE_TEXT_MAX_BYTES + 1)

        with pytest.raises(SurrealStoreError) as exc_info:
            store.file_text_fragment(TIER_A, APP_PATH, oversized_text, sha512_hex(oversized_text))
        message = str(exc_info.value)
        assert str(len(oversized_text.encode("utf-8"))) in message, (
            "error message must name the actual body size"
        )
        assert str(FILE_TEXT_MAX_BYTES) in message, "error message must name the configured cap"

    async def test_accepts_body_exactly_at_the_byte_cap(
        self, surreal_env: SurrealEnv  # noqa: F811
    ) -> None:
        # The boundary itself must build fine — never applied/sent to the
        # server, only proven to compose without raising.
        store = self._bare_store(surreal_env)
        at_cap_text = "x" * FILE_TEXT_MAX_BYTES

        fragment = store.file_text_fragment(TIER_A, APP_PATH, at_cap_text, sha512_hex(at_cap_text))

        assert fragment.statements
        assert len(at_cap_text.encode("utf-8")) == FILE_TEXT_MAX_BYTES  # guard the fixture itself

    async def test_accepts_a_realistic_multi_megabyte_file_body(
        self, surreal_env: SurrealEnv  # noqa: F811
    ) -> None:
        # A few-MB generated/vendored source file is REAL production data
        # (large ORM-generated modules, vendored bundles) and comfortably
        # under the cap — must build without raising, so the cap never
        # rejects a legitimately large real file.
        realistic_large_text = APP_SOURCE * 4000  # ~2.5 MiB of real Python text
        size_mib = len(realistic_large_text.encode("utf-8")) / (1024 * 1024)
        assert 1 < size_mib < 5, "fixture assumption: a realistic few-MB body"
        store = self._bare_store(surreal_env)

        fragment = store.file_text_fragment(
            TIER_A, APP_PATH, realistic_large_text, sha512_hex(realistic_large_text)
        )

        assert fragment.statements

    async def test_byte_cap_is_measured_in_utf8_bytes_not_code_points(
        self, surreal_env: SurrealEnv  # noqa: F811
    ) -> None:
        # WRONG-UNIT guard: a CJK-heavy body where each character is 3 UTF-8
        # bytes. A CODE-POINT-count cap would wildly under-reject relative to
        # the real on-disk byte size a ``file_text`` row actually stores
        # (production source carries non-ASCII docstrings/comments/string
        # literals). Chosen so the code-point count sits comfortably UNDER the
        # cap while the UTF-8 byte count sits OVER it — this only fails
        # (raises) if the bound is genuinely byte-based, the unit
        # ``FILE_TEXT_MAX_BYTES`` promises.
        multibyte_char = "文"  # U+6587 CJK ideograph, 3 bytes in UTF-8
        char_count = (FILE_TEXT_MAX_BYTES // 3) + 1
        oversized_text = multibyte_char * char_count
        assert char_count < FILE_TEXT_MAX_BYTES, "fewer code points than the byte cap"
        assert len(oversized_text.encode("utf-8")) > FILE_TEXT_MAX_BYTES, "but over cap in UTF-8 bytes"
        store = self._bare_store(surreal_env)

        with pytest.raises(SurrealStoreError):
            store.file_text_fragment(TIER_A, APP_PATH, oversized_text, sha512_hex(oversized_text))
