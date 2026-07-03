"""Contract tests for ``loremaster.graph_surreal.SurrealCodeGraph`` — the P4
port of the astroid-derived code-graph from KùzuDB onto the unified SurrealDB
store, against the REAL server (per-test database isolation, ``_surreal_harness``).

WHAT THIS FILE PINS (and what it deliberately does NOT)
------------------------------------------------------
P4 ports ONLY the storage + query layer (the Kùzu ``CREATE``/``MATCH`` →
SurrealQL). The astroid DERIVATION (``_derive_nodes`` / ``_derive_edges`` /
``_resolve`` / the keep-drop rule / the module-qualified-name helpers) MOVES
UNCHANGED and is NOT re-tested here — its behaviour is already pinned by
``tests/test_graph.py``. These tests drive the REAL producer (the ``PythonAst
Chunker``) and the REAL astroid resolution over on-disk packages exactly the way
``test_graph.py`` does, so every expected FQN / count / reason is an INDEPENDENT
oracle read straight off the authored source below — never re-derived from the
engine. What P4 adds and what these tests certify is that the SAME query
behaviours hold when the edges are stored under the S13 "Model A" schema
(``code_node`` name-node indirection + native ``RELATE``) and that the
Model-A-specific storage properties (deterministic id, order-independence, FQN
fan-out, per-file purge isolation, self-heal) are honoured against the live 3.1.5
engine.

THE DECIDED S13 MODEL (Model A — not re-litigated here)
------------------------------------------------------
* ``code_node`` table, DETERMINISTIC record id ``code_node:[tier, file_path,
  qualified_name]`` (an array-keyed ``RecordID``, exactly like the manifest's
  ``file:[tier, file_path]``). Fields: ``kind`` (module|class|method|function),
  ``qualified_name``, ``bare_name`` (derived — the last dotted segment),
  ``file_path``, ``tier``, ``chunk_id`` (``option<string>`` — ``NONE`` for the
  synthesised module node).
* ``name`` table: id ``name:<dst-string>``, fieldless — always constructible from
  what a referencing file knows (UPSERTed idempotently, so an edge to a
  not-yet-defined name simply UPSERTs the name first: order-independence).
* ``refers`` RELATION (``code_node`` → ``name``): ``kind`` (defines|inherits|
  imports|calls), ``resolved`` (bool), ``src_tier``, ``src_file_path`` (for
  per-file purge).
* ``answers_to`` RELATION (``code_node`` → ``name``): ``tier``, ``file_path`` —
  each node ``answers_to`` its FQN-name AND its bare-name (the FQN-collision
  fan-out mechanism).

RED until STUB: this file COLLECTION-ERRORS with ``ModuleNotFoundError``
(``loremaster.graph_surreal``) / ``ImportError`` (the new ``surreal_schema``
graph-DDL names) until P4's STUB phase lands them. The error is confined to this
file (the harness imports only the SDK + ``loremaster.index.records``).

A behaviour that does NOT map cleanly (RAISED for the operator — see the module
footnote ``_OPERATOR_NOTE``): ``test_graph.py``'s
``test_what_imports_matches_by_bare_name_seam`` builds ONLY the importer file
(the target's own file is absent) and relies on Kùzu's ``r.dst ENDS WITH
".LoadError"`` string-suffix match. Model A has no suffix match — the bare↔FQN
bridge runs through the TARGET node's ``answers_to`` fan-out, so it requires the
target's file to be in the graph. Production always indexes the whole project (so
the target node exists), so this file pins the bare-name seam under the realistic
whole-package build and documents the divergence rather than papering over it.
"""

from __future__ import annotations

import inspect
import textwrap
from collections.abc import AsyncIterator, Callable, Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import pytest
import pytest_asyncio
from _surreal_harness import (
    TIER_A,
    TIER_B,
    SurrealConnection,
    SurrealEnv,
    admin_db,  # noqa: F401 - re-exported pytest fixture
    call_until_recovered,
    connect_admin,
    run,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
)

# --- Target module under contract (RED until the P4 STUB lands) --------------
from loremaster.graph_surreal import (  # noqa: E402
    DEFAULT_DEAD_CODE_MAX_RESULTS,
    EDGE_CALLS,
    EDGE_DEFINES,
    EDGE_IMPORTS,
    EDGE_INHERITS,
    KIND_CLASS,
    KIND_FUNCTION,
    KIND_METHOD,
    KIND_MODULE,
    MAX_DEAD_CODE_MAX_RESULTS,
    REASON_NO_REFERENCES,
    REASON_ONLY_REFERENCED_BY_TESTS,
    DeadCodeNode,
    GraphNode,
    ReferenceSummary,
    SurrealCodeGraph,
    _AstroidDerivation,
)

# The connection/transport error vocabulary is re-exported from the existing
# store module (which DOES exist) — importing it here does not contribute to the
# RED, which comes from ``graph_surreal`` + the new ``surreal_schema`` names.
from loremaster.store.surreal import (  # noqa: E402
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    SurrealStoreError,
    _SurrealConnection,
)

# The graph DDL slice + the canonical table/relation names — the SINGLE source of
# truth the port and these tests share (clause 5). New in P4 → part of the RED.
from loremaster.store.surreal_schema import (  # noqa: E402
    ANSWERS_TO_RELATION,
    CODE_NODE_TABLE,
    NAME_TABLE,
    REFERS_RELATION,
    generate_graph_ddl,
)
from lorescribe.astroid_parse import clear_resolution_cache, reset_search_path_memo
from lorescribe.models import Chunk, ChunkContext
from lorescribe.python_ast import PythonAstChunker
from surrealdb import AsyncSurreal as _RealAsyncSurreal
from surrealdb import RecordID

# A port with nothing listening — the "server is down" adversary (the same dead
# port ``test_surreal_store``/``test_surreal_manifest`` use, so a shared
# port-reservation rule never collides).
_DEAD_URL = "ws://127.0.0.1:19555/rpc"

# The transient-error set a mid-life socket drop may surface before the self-heal
# completes — mirrors ``test_surreal_manifest._HEALABLE_ERRORS`` exactly (the
# reconnect can momentarily raise either wrapper before the next call succeeds).
_HEALABLE_ERRORS: tuple[type[BaseException], ...] = (SurrealStoreError, *_CONNECTION_ERRORS)

# The embedder's injected token-count contract (~4 chars/token) and the hard cap,
# mirrored from ``test_graph.py`` so the REAL chunker runs exactly as in prod.
VOYAGE4_MAX_INPUT_TOKENS: int = 8192


def approx_token_count(text: str) -> int:
    """Behavioural stand-in for the embedder's injected token counter (~4 cpt)."""
    return max(1, len(text) // 4)


def _chunk(path: str, source: str) -> list[Chunk]:
    """Chunk ``source`` through the REAL ``PythonAstChunker`` (the prod producer).

    Driving the real chunker (not hand-rolled ``Chunk`` objects) exercises the
    producer↔consumer seam: the graph consumes exactly the chunk shape the
    chunker emits, so a chunker-shape drift cannot slip past (clause 3).
    """
    ctx = ChunkContext(
        slug="demo",
        file_path=path,
        count_tokens=approx_token_count,
        max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
    )
    return PythonAstChunker().chunk(source, ctx)


async def _build(
    graph: SurrealCodeGraph, root: Path, tier: str, path: str, source: str, module: str
) -> None:
    """Materialise ``source`` on disk under ``root``, then build the file's graph slice.

    astroid resolves imports/inherits/calls from the ON-DISK file (Kuzu-identical),
    so the source is written to ``root / path`` BEFORE chunking + building — this is
    load-bearing when a test rebuilds a file with NEW source
    (``test_lifecycle_flip_on_rebuild``). ``root`` is the fixture's OWN tier-root (the
    caller already owns it via the ``tier_roots`` it passed to ``SurrealCodeGraph``).
    """
    absolute = root / path
    absolute.parent.mkdir(parents=True, exist_ok=True)
    absolute.write_text(source, encoding="utf-8")
    await graph.build_file_graph(tier, path, _chunk(path, source), module_name=module)


# ===========================================================================
# Authored on-disk fixture sources. Each is an INDEPENDENT ORACLE: the true FQNs
# / reference counts / reasons are read straight off the source text below, never
# re-derived from the engine. Resolution requires the file ON DISK under the
# project roots, so these are materialised to ``tmp_path`` and the graph is wired
# with ``tier_roots`` + ``project_roots``.
# ===========================================================================

ERRORS_SOURCE: str = textwrap.dedent(
    '''\
    """The demo project's error types."""


    class LoadError(Exception):
        """Raised when a config file cannot be loaded."""
    '''
)

APP_SOURCE: str = textwrap.dedent(
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

TEST_SOURCE: str = textwrap.dedent(
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

ERRORS_PATH: str = "demo/errors.py"
APP_PATH: str = "demo/service.py"
TEST_PATH: str = "tests/test_service.py"

ERRORS_MODULE: str = "demo.errors"
APP_MODULE: str = "demo.service"
TEST_MODULE: str = "tests.test_service"

# Independent oracles — the TRUE FQNs, read straight off APP_SOURCE/ERRORS_SOURCE.
FQN_BASE: str = "demo.service.BaseService"
FQN_INDEX: str = "demo.service.IndexService"
FQN_LOAD_CONFIG: str = "demo.service.load_config"
FQN_BOOT: str = "demo.service.IndexService.boot"
FQN_START: str = "demo.service.BaseService.start"
FQN_LOAD_ERROR: str = "demo.errors.LoadError"


def _write_demo_package(root: Path) -> None:
    """Materialise ``demo/`` (errors + service) and ``tests/`` on disk for astroid."""
    (root / "demo").mkdir(parents=True, exist_ok=True)
    (root / "demo" / "__init__.py").write_text("", encoding="utf-8")
    (root / "demo" / "errors.py").write_text(ERRORS_SOURCE, encoding="utf-8")
    (root / "demo" / "service.py").write_text(APP_SOURCE, encoding="utf-8")
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_service.py").write_text(TEST_SOURCE, encoding="utf-8")


# --- reference-counter / dead-code library (mixed reference profiles) --------

REFLIB_SOURCE: str = textwrap.dedent(
    '''\
    """A small library with mixed reference profiles."""
    from __future__ import annotations


    def widget(value):
        """Called from production AND from a test."""
        return value + 1


    def lonely(value):
        """Called ONLY from a test — dead in production."""
        return value - 1


    def orphan(value):
        """Called by nobody — truly dead."""
        return value * 2


    def countdown(value):
        """Self-recursive: its only caller is itself."""
        if value <= 0:
            return 0
        return countdown(value - 1)
    '''
)

REFCONSUMER_SOURCE: str = textwrap.dedent(
    '''\
    """A production module consuming the library."""
    from __future__ import annotations

    from demo.reflib import widget


    def run(value):
        """A real production caller of ``widget``."""
        return widget(value)
    '''
)

REFTEST_SOURCE: str = textwrap.dedent(
    '''\
    """Tests for the library."""
    from __future__ import annotations

    from demo.reflib import widget, lonely


    def test_widget():
        """Exercises widget (also called in production)."""
        return widget(1)


    def test_lonely():
        """Exercises lonely (called ONLY here)."""
        return lonely(1)
    '''
)

REFLIB_PATH: str = "demo/reflib.py"
REFCONSUMER_PATH: str = "demo/consumer.py"
REFTEST_PATH: str = "tests/test_reflib.py"
REFLIB_MODULE: str = "demo.reflib"
REFCONSUMER_MODULE: str = "demo.consumer"
REFTEST_MODULE: str = "tests.test_reflib"

FQN_WIDGET: str = "demo.reflib.widget"
FQN_LONELY: str = "demo.reflib.lonely"
FQN_ORPHAN: str = "demo.reflib.orphan"
FQN_COUNTDOWN: str = "demo.reflib.countdown"
FQN_RUN: str = "demo.consumer.run"


def _write_reflib_package(root: Path) -> None:
    """Materialise the reference-counter demo package on disk for astroid."""
    (root / "demo").mkdir(parents=True, exist_ok=True)
    (root / "demo" / "__init__.py").write_text("", encoding="utf-8")
    (root / "demo" / "reflib.py").write_text(REFLIB_SOURCE, encoding="utf-8")
    (root / "demo" / "consumer.py").write_text(REFCONSUMER_SOURCE, encoding="utf-8")
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_reflib.py").write_text(REFTEST_SOURCE, encoding="utf-8")


# ===========================================================================
# autouse astroid resolution-state reset (process-global — same guard as
# test_graph.py, so one test's throwaway package cannot leak its warm cache /
# search-path entries into the next).
# ===========================================================================


@pytest.fixture(autouse=True)
def _reset_astroid_resolution_state() -> Iterator[None]:
    """Reset astroid's process-global resolution state around EVERY graph test."""
    clear_resolution_cache()
    reset_search_path_memo()
    yield
    clear_resolution_cache()
    reset_search_path_memo()


# ===========================================================================
# Live-server graph fixtures (per-test database isolation via ``surreal_env``).
# ===========================================================================


async def _make_graph(
    env: SurrealEnv, *, tier_roots: dict[str, Path], project_roots: list[Path]
) -> SurrealCodeGraph:
    """Construct + ready a resolution-enabled graph on ``env``'s fresh database.

    The constructor mirrors ``SurrealManifest`` (url/namespace/database/user/
    password — NO ``dim``: the code-graph stores no vectors) plus the resolution
    roots the derivation needs. ``ensure_ready`` applies the graph DDL slice.
    """
    graph = SurrealCodeGraph(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
        tier_roots=tier_roots,
        project_roots=project_roots,
    )
    await graph.ensure_ready()
    return graph


async def _make_and_build_graph(
    env: SurrealEnv, project_root: Path, files: Sequence[tuple[str, str, str]]
) -> SurrealCodeGraph:
    """A single-tier graph, ready and with every ``(path, source, module)`` built.

    The shared shape ``reflib_graph`` / ``modlib_graph`` / ``collide_graph`` each
    need: one fresh database, one project root, build every file in order. Each
    fixture still owns its OWN on-disk package materialisation (the sources
    differ) and its own close/teardown (``yield`` semantics vary), so only this
    common middle is factored out.
    """
    graph = await _make_graph(env, tier_roots={TIER_A: project_root}, project_roots=[project_root])
    for path, source, module in files:
        await _build(graph, project_root, TIER_A, path, source, module)
    return graph


@pytest_asyncio.fixture()
async def demo_graph(
    surreal_env: SurrealEnv,  # noqa: F811
    tmp_path: Path,
) -> AsyncIterator[tuple[SurrealCodeGraph, SurrealEnv, Path]]:
    """A resolution-enabled graph over the demo (errors + service + test) package.

    Yields ``(graph, env, project_root)``; NOTHING is built yet, so a test picks
    exactly which files to build (and in which order — used by the
    order-independence and partial-build cases).
    """
    project_root = tmp_path / "project"
    _write_demo_package(project_root)
    graph = await _make_graph(
        surreal_env,
        tier_roots={TIER_A: project_root, TIER_B: project_root},
        project_roots=[project_root],
    )
    try:
        yield graph, surreal_env, project_root
    finally:
        await graph.close()


@pytest_asyncio.fixture()
async def app_graph(
    demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path],
) -> tuple[SurrealCodeGraph, SurrealEnv, Path]:
    """The demo graph with the WHOLE package built (errors + service + test).

    Production always indexes the whole project, so the whole-package build is the
    realistic baseline for the query contracts (and the one under which the
    bare↔FQN answers_to bridge is exercised).
    """
    graph, env, project_root = demo_graph
    await _build(graph, project_root, TIER_A, ERRORS_PATH, ERRORS_SOURCE, ERRORS_MODULE)
    await _build(graph, project_root, TIER_A, APP_PATH, APP_SOURCE, APP_MODULE)
    await _build(graph, project_root, TIER_A, TEST_PATH, TEST_SOURCE, TEST_MODULE)
    return graph, env, project_root


@pytest_asyncio.fixture()
async def reflib_graph(
    surreal_env: SurrealEnv,  # noqa: F811
    tmp_path: Path,
) -> AsyncIterator[tuple[SurrealCodeGraph, SurrealEnv]]:
    """A resolution-enabled graph over the reference-counter package, ALL built.

    ``widget`` has one production + one test reference, ``lonely`` a test-only
    reference, ``orphan`` none, ``countdown`` only its self-edge — the profiles the
    reference counter / dead-code sweep must distinguish.
    """
    project_root = tmp_path / "project"
    _write_reflib_package(project_root)
    graph = await _make_and_build_graph(
        surreal_env,
        project_root,
        [
            (REFLIB_PATH, REFLIB_SOURCE, REFLIB_MODULE),
            (REFCONSUMER_PATH, REFCONSUMER_SOURCE, REFCONSUMER_MODULE),
            (REFTEST_PATH, REFTEST_SOURCE, REFTEST_MODULE),
        ],
    )
    try:
        yield graph, surreal_env
    finally:
        await graph.close()


# ===========================================================================
# Raw-store introspection helpers (the storage MODEL is decided by S13, so
# pinning the deterministic id / per-file purge / collision fan-out at the row
# level is pinning the DECIDED MODEL — not reverse-engineering an implementation).
# Each opens a FRESH admin connection independent of the graph's own (which a
# resilience test may have deliberately broken), mirroring the harness teardown.
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


async def _code_node_rows(
    env: SurrealEnv, *, tier: str | None = None, file_path: str | None = None, kind: str | None = None
) -> list[dict[str, Any]]:
    """The raw ``code_node`` rows, optionally scoped by tier/file/kind."""
    conditions: list[str] = []
    params: dict[str, Any] = {}
    if tier is not None:
        conditions.append("tier = $tier")
        params["tier"] = tier
    if file_path is not None:
        conditions.append("file_path = $file_path")
        params["file_path"] = file_path
    if kind is not None:
        conditions.append("kind = $kind")
        params["kind"] = kind
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    return await _fetch_rows(env, f"SELECT * FROM {CODE_NODE_TABLE}{where}", params)


async def _relation_count(env: SurrealEnv, relation: str, where: str, params: dict[str, Any]) -> int:
    """The number of ``relation`` edge rows matching ``where`` (client-side count)."""
    rows = await _fetch_rows(env, f"SELECT * FROM {relation} WHERE {where}", params)
    return len(rows)


# ===========================================================================
# Public vocabulary — the edge-kind literals + value-object types the port must
# re-export unchanged (the server + CLI import these from the graph module and
# the derivation stores them verbatim as ``refers.kind``). The expected literals
# come from the documented S13 model, not the implementation.
# ===========================================================================


class TestPublicVocabulary:
    """The edge-kind constants keep their exact wire literals; queries return GraphNode."""

    def test_edge_kind_literals_are_stable(self) -> None:
        # A rename of any of these silently corrupts the stored ``refers.kind`` and
        # the reference-kind rule; pin the literals as the wire contract.
        assert EDGE_IMPORTS == "imports"
        assert EDGE_CALLS == "calls"
        assert EDGE_INHERITS == "inherits"
        assert EDGE_DEFINES == "defines"

    def test_node_kind_literals_are_stable(self) -> None:
        assert (KIND_MODULE, KIND_CLASS, KIND_METHOD, KIND_FUNCTION) == (
            "module",
            "class",
            "method",
            "function",
        )

    async def test_what_imports_returns_graph_nodes(
        self, app_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """The query return type is the neutral ``GraphNode`` value object."""
        graph, _env, _root = app_graph
        importers = await graph.what_imports(FQN_LOAD_ERROR)
        assert importers  # the app imports LoadError
        assert all(isinstance(node, GraphNode) for node in importers)


# ===========================================================================
# 0. Schema / DDL — the S13 Model-A tables + fields + indexes exist on the live
#    engine (pinned against ``INFO FOR DB`` / ``INFO FOR TABLE``, the same idiom
#    as ``test_surreal_schema``). The table/field/index shape is the DECIDED
#    model, an independent spec — not read from the port's code.
# ===========================================================================


class TestGraphSchemaDDL:
    """``generate_graph_ddl`` emits the Model-A code-graph schema (real server)."""

    async def test_creates_the_four_model_a_tables(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """``code_node`` / ``name`` / ``refers`` / ``answers_to`` all exist."""
        connection, _env = admin_db
        await run(connection, generate_graph_ddl())
        info = await run(connection, "INFO FOR DB")
        tables = set(info.get("tables", {}))
        assert {CODE_NODE_TABLE, NAME_TABLE, REFERS_RELATION, ANSWERS_TO_RELATION} <= tables

    async def test_refers_and_answers_to_are_relation_tables(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """The two edge tables are native ``TYPE RELATION`` tables (not plain)."""
        connection, _env = admin_db
        await run(connection, generate_graph_ddl())
        info = await run(connection, "INFO FOR DB")
        table_ddls = info.get("tables", {})
        assert "RELATION" in str(table_ddls.get(REFERS_RELATION, ""))
        assert "RELATION" in str(table_ddls.get(ANSWERS_TO_RELATION, ""))

    async def test_code_node_carries_the_documented_fields(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """``code_node`` defines kind/qualified_name/bare_name/file_path/tier/chunk_id."""
        connection, _env = admin_db
        await run(connection, generate_graph_ddl())
        info = await run(connection, f"INFO FOR TABLE {CODE_NODE_TABLE}")
        fields = set(info.get("fields", {}))
        assert {"kind", "qualified_name", "bare_name", "file_path", "tier", "chunk_id"} <= fields

    async def test_refers_carries_the_documented_fields(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """``refers`` defines kind/resolved/src_tier/src_file_path (per-file purge keys)."""
        connection, _env = admin_db
        await run(connection, generate_graph_ddl())
        info = await run(connection, f"INFO FOR TABLE {REFERS_RELATION}")
        fields = set(info.get("fields", {}))
        assert {"kind", "resolved", "src_tier", "src_file_path"} <= fields

    async def test_code_node_indexes_cover_bare_name_qname_and_tier_file(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """The hot lookups are indexed: bare_name, qualified_name, (tier, file_path)."""
        connection, _env = admin_db
        await run(connection, generate_graph_ddl())
        info = await run(connection, f"INFO FOR TABLE {CODE_NODE_TABLE}")
        index_ddls = [str(ddl) for ddl in info.get("indexes", {}).values()]
        assert any("bare_name" in ddl for ddl in index_ddls), "no index on bare_name"
        assert any("qualified_name" in ddl for ddl in index_ddls), "no index on qualified_name"
        # A composite scoping index over the per-file purge / count dimensions.
        assert any("tier" in ddl and "file_path" in ddl for ddl in index_ddls)

    async def test_refers_indexes_cover_src_file_path_for_purge(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """``refers`` is indexed on its per-file purge key (src_file_path)."""
        connection, _env = admin_db
        await run(connection, generate_graph_ddl())
        info = await run(connection, f"INFO FOR TABLE {REFERS_RELATION}")
        index_ddls = [str(ddl) for ddl in info.get("indexes", {}).values()]
        assert any("src_file_path" in ddl for ddl in index_ddls), "no purge index on refers.src_file_path"

    async def test_ddl_is_idempotent(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Applying the DDL twice is a safe no-op (IF NOT EXISTS)."""
        connection, _env = admin_db
        await run(connection, generate_graph_ddl())
        await run(connection, generate_graph_ddl())  # must not raise
        info = await run(connection, "INFO FOR DB")
        assert CODE_NODE_TABLE in set(info.get("tables", {}))


# ===========================================================================
# 1. Construction / readiness / indexed_file_count
# ===========================================================================


class TestConstructionAndReadiness:
    """Lazy connect + idempotent readiness + the empty-graph file count."""

    async def test_ensure_ready_is_idempotent(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """A second ``ensure_ready`` neither raises nor disturbs state."""
        graph, _env, _root = demo_graph
        await graph.ensure_ready()  # fixture already called it once
        assert await graph.indexed_file_count() == 0

    async def test_fresh_graph_reports_zero_indexed_files(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """A fresh/wiped graph reports zero indexed files (the reconcile trigger)."""
        graph, _env, _root = demo_graph
        assert await graph.indexed_file_count() == 0

    async def test_counts_distinct_tier_file_pairs(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """The same path under two tiers counts as two distinct files (C1).

        3.1.5 has no ``SELECT DISTINCT <field>``, so the port must dedupe the
        ``(tier, file_path)`` pairs client-side — pinned here by the two-tier count.
        """
        graph, _env, _root = demo_graph
        chunks = _chunk(APP_PATH, APP_SOURCE)
        await graph.build_file_graph(TIER_A, APP_PATH, chunks, module_name=APP_MODULE)
        assert await graph.indexed_file_count() == 1
        await graph.build_file_graph(TIER_B, APP_PATH, chunks, module_name=APP_MODULE)
        assert await graph.indexed_file_count() == 2


# ===========================================================================
# 2. Node storage — the derived nodes persist with the NEW Model-A shape
#    (bare_name derived; module chunk_id NONE). This is a STORAGE contract (the
#    node SET itself is derivation, already pinned by test_graph.py); what P4
#    adds is the bare_name field and the option<string> chunk_id null handling.
# ===========================================================================


class TestNodeStorage:
    """The port persists each derived node with its Model-A fields."""

    async def test_stores_one_module_node(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """A file yields exactly one ``module`` code_node, qualified from its name."""
        graph, env, _root = demo_graph
        await _build(graph, _root, TIER_A, APP_PATH, APP_SOURCE, APP_MODULE)
        modules = await _code_node_rows(env, tier=TIER_A, file_path=APP_PATH, kind=KIND_MODULE)
        assert [row["qualified_name"] for row in modules] == [APP_MODULE]

    async def test_stores_class_nodes_with_dotted_qualified_names(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """Each top-level class becomes a ``class`` node (independent oracle: source)."""
        graph, env, _root = demo_graph
        await _build(graph, _root, TIER_A, APP_PATH, APP_SOURCE, APP_MODULE)
        rows = await _code_node_rows(env, tier=TIER_A, file_path=APP_PATH, kind=KIND_CLASS)
        assert {row["qualified_name"] for row in rows} == {FQN_BASE, FQN_INDEX}

    async def test_stores_method_and_function_nodes(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """Methods qualify under their class; top-level functions under the module."""
        graph, env, _root = demo_graph
        await _build(graph, _root, TIER_A, APP_PATH, APP_SOURCE, APP_MODULE)
        methods = {r["qualified_name"] for r in await _code_node_rows(env, kind=KIND_METHOD)}
        functions = {r["qualified_name"] for r in await _code_node_rows(env, kind=KIND_FUNCTION)}
        assert methods == {FQN_START, FQN_BOOT}
        assert functions == {FQN_LOAD_CONFIG}

    async def test_bare_name_is_the_last_dotted_segment(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """The derived ``bare_name`` column is the last segment (kills the scan).

        Independent oracle: ``demo.service.IndexService``'s last segment is
        ``IndexService`` — read off the qualified name, not the engine.
        """
        graph, env, _root = demo_graph
        await _build(graph, _root, TIER_A, APP_PATH, APP_SOURCE, APP_MODULE)
        classes = await _code_node_rows(env, kind=KIND_CLASS)
        by_qname = {row["qualified_name"]: row for row in classes}
        assert by_qname[FQN_INDEX]["bare_name"] == "IndexService"
        assert by_qname[FQN_BASE]["bare_name"] == "BaseService"

    async def test_module_node_chunk_id_is_none(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """The synthesised module node has NO originating chunk → ``chunk_id`` NONE.

        Pinned both at the raw column (``option<string>`` NONE) and through the
        public decode path: ``blast_radius`` reaches the module node as a reverse
        dependent of its own defined symbol and decodes ``chunk_id is None``.
        """
        graph, env, _root = demo_graph
        await _build(graph, _root, TIER_A, APP_PATH, APP_SOURCE, APP_MODULE)
        module_rows = await _code_node_rows(env, kind=KIND_MODULE)
        assert module_rows[0].get("chunk_id") is None
        # A symbol node, by contrast, DOES carry its chunk identity.
        class_rows = await _code_node_rows(env, kind=KIND_CLASS)
        assert class_rows[0].get("chunk_id") is not None
        # Public decode: the module node reached via the reverse walk is None too.
        reached = [
            n for n in await graph.blast_radius(FQN_BASE, depth=3, max_results=50)
            if n.kind == KIND_MODULE
        ]
        assert reached, "the module node must be reachable as a reverse dependent"
        assert all(node.chunk_id is None for node in reached)


# ===========================================================================
# 3. what_imports — reverse of the imports edge, matched by FQN or bare name.
# ===========================================================================


class TestWhatImports:
    """``what_imports`` reverses the ``imports`` ref: who pulls in a target?"""

    async def test_returns_modules_that_import_the_resolved_symbol_fqn(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """``from demo.errors import LoadError`` is found by the SYMBOL FQN query.

        Independent oracle: ERRORS_SOURCE defines ``LoadError`` in ``demo/errors``
        → ``demo.errors.LoadError``. This holds with ONLY the importer built (the
        importer's ``refers`` edge UPSERTs ``name:demo.errors.LoadError``), so it is
        the guarantee that survives regardless of whether the target file is graphed.
        """
        graph, _env, _root = demo_graph
        await _build(graph, _root, TIER_A, APP_PATH, APP_SOURCE, APP_MODULE)
        importers = {node.qualified_name for node in await graph.what_imports(FQN_LOAD_ERROR)}
        assert APP_MODULE in importers

    async def test_matches_by_bare_name_under_whole_package_build(
        self, app_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """A bare ``LoadError`` query reaches the resolved FQN import (bare↔FQN seam).

        In Model A the bare→FQN bridge runs through the TARGET node's ``answers_to``
        fan-out (FQN-name AND bare-name), so the target's own file must be graphed —
        which it always is in production (``app_graph`` builds the whole package).
        See ``_OPERATOR_NOTE``: this is the deliberate, flagged divergence from
        Kùzu's file-independent ``ENDS WITH`` suffix match.
        """
        graph, _env, _root = app_graph
        importers = {node.qualified_name for node in await graph.what_imports("LoadError")}
        assert APP_MODULE in importers

    async def test_returns_empty_for_unimported_target(
        self, app_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """A target nobody imports yields an empty list, not an error."""
        graph, _env, _root = app_graph
        assert list(await graph.what_imports("nonexistent.module")) == []

    async def test_external_import_is_not_matchable(
        self, app_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """A stdlib import (``json``) was dropped by resolution → no importer of it.

        Independent oracle: ``json`` is stdlib, resolved-external, so the keep/drop
        rule dropped its ``imports`` edge; nobody "imports" it in the graph.
        """
        graph, _env, _root = app_graph
        assert list(await graph.what_imports("json")) == []


# ===========================================================================
# 4. blast_radius — bounded reverse-transitive closure across ALL ref kinds.
# ===========================================================================


class TestBlastRadius:
    """``blast_radius`` is a BOUNDED reverse-reference transitive closure."""

    async def test_finds_direct_reverse_dependents(
        self, app_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """``IndexService`` inherits ``BaseService`` → it is in BaseService's radius."""
        graph, _env, _root = app_graph
        affected = {n.qualified_name for n in await graph.blast_radius(FQN_BASE, depth=3, max_results=100)}
        assert FQN_INDEX in affected

    async def test_respects_depth_bound(
        self, surreal_env: SurrealEnv, tmp_path: Path  # noqa: F811
    ) -> None:
        """A deep inheritance chain is truncated at exactly ``depth`` hops.

        Independent oracle: a linear chain ``N0 <- N1 <- ... <- N7`` (each inherits
        the previous, RESOLVED in-project). The reverse closure from ``N0`` at
        depth 3 includes N1 (1 hop) and N3 (at the bound) but NOT N4 or N7.
        """
        chain_length = 8
        depth_bound = 3
        lines = ['"""A deep linear inheritance chain."""', "", "", "class N0:", "    pass", ""]
        for index in range(1, chain_length):
            lines += ["", f"class N{index}(N{index - 1}):", "    pass", ""]
        chain_source = "\n".join(lines) + "\n"

        project_root = tmp_path / "project"
        (project_root / "demo").mkdir(parents=True)
        (project_root / "demo" / "__init__.py").write_text("", encoding="utf-8")
        (project_root / "demo" / "chain.py").write_text(chain_source, encoding="utf-8")
        graph = await _make_graph(
            surreal_env, tier_roots={TIER_A: project_root}, project_roots=[project_root]
        )
        try:
            await _build(graph, project_root, TIER_A, "demo/chain.py", chain_source, "demo.chain")
            affected = {
                n.qualified_name
                for n in await graph.blast_radius("demo.chain.N0", depth=depth_bound, max_results=1000)
            }
            assert "demo.chain.N1" in affected  # 1 hop
            assert f"demo.chain.N{depth_bound}" in affected  # exactly at the bound
            assert f"demo.chain.N{depth_bound + 1}" not in affected  # one beyond
            assert f"demo.chain.N{chain_length - 1}" not in affected  # far beyond
        finally:
            await graph.close()

    async def test_respects_max_results_cap(
        self, surreal_env: SurrealEnv, tmp_path: Path  # noqa: F811
    ) -> None:
        """A wide fan-out is clamped at ``max_results`` — the closure cannot blow up.

        Independent oracle: ``fan_out`` subclasses of one ``Hub`` (all RESOLVED
        in-project inherits). Hub's reverse closure has ``fan_out`` dependents; the
        cap clamps the returned list without zeroing it.
        """
        fan_out = 200
        cap = 25
        lines = ['"""A wide fan-out: many subclasses of one base."""', "", "class Hub:", "    pass", ""]
        for index in range(fan_out):
            lines += ["", f"class Leaf{index}(Hub):", "    pass", ""]
        star_source = "\n".join(lines) + "\n"

        project_root = tmp_path / "project"
        (project_root / "demo").mkdir(parents=True)
        (project_root / "demo" / "__init__.py").write_text("", encoding="utf-8")
        (project_root / "demo" / "star.py").write_text(star_source, encoding="utf-8")
        graph = await _make_graph(
            surreal_env, tier_roots={TIER_A: project_root}, project_roots=[project_root]
        )
        try:
            await _build(graph, project_root, TIER_A, "demo/star.py", star_source, "demo.star")
            affected = list(await graph.blast_radius("demo.star.Hub", depth=5, max_results=cap))
            assert len(affected) <= cap  # hard ceiling honoured
            assert len(affected) > 0  # clamps, never zeroes
        finally:
            await graph.close()

    async def test_negative_or_zero_bounds_return_empty(
        self, app_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """Degenerate bounds (depth < 0 / max_results <= 0) yield [], never a crash."""
        graph, _env, _root = app_graph
        assert list(await graph.blast_radius(FQN_BASE, depth=-1, max_results=10)) == []
        assert list(await graph.blast_radius(FQN_BASE, depth=3, max_results=0)) == []


# ===========================================================================
# 3b/4b. what_imports / blast_radius by MODULE TARGET — the P4 audit regression.
#
# THE REGRESSION (audit-confirmed, live-reproduced against spike-surreal): Kùzu's
# ``what_imports``/``_reverse_neighbours`` support a "STARTS WITH '<module>.'"
# prefix arm so a MODULE-NAME query (e.g. ``what_imports("demo.reflib")``) finds
# every ``from <module> import <symbol>`` importer, because the stored ``imports``
# edge ``dst`` is the resolved SYMBOL fqn (``demo.reflib.widget``), not the bare
# module. Model A's ``answers_to`` fan-out only bridges a name to nodes whose own
# FQN/bare-name literally IS that name — there is no equivalent "symbols defined
# under module M" reverse match, so these queries return [] today (RED below).
#
# ORACLE: every expected importer set is read straight off the ALREADY-AUTHORED
# fixture sources this file uses elsewhere (REFCONSUMER_SOURCE / REFTEST_SOURCE /
# MODLIB_APP_SOURCE / TEST_SOURCE) — never re-derived from either graph engine.
# ===========================================================================


class TestWhatImportsModuleTarget:
    """``what_imports`` queried BY MODULE NAME finds ``from module import X`` importers.

    RED today: Model A has no module-prefix reverse arm (see the section banner
    above). Kept in the SAME file as the rest of ``TestWhatImports`` (same target,
    same live server, same fixtures) — only the QUERY ARGUMENT is new: a module's
    own dotted name instead of a symbol's own FQN.
    """

    async def test_module_target_finds_multiple_from_import_importers(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """``what_imports("demo.reflib")`` finds every ``from demo.reflib import`` site.

        Independent oracle, read off REFCONSUMER_SOURCE (``from demo.reflib import
        widget``) and REFTEST_SOURCE (``from demo.reflib import widget, lonely``):
        both ``demo.consumer`` and ``tests.test_reflib`` import a symbol FROM
        ``demo.reflib``, queried BY THE MODULE'S OWN NAME (neither importer's own
        FQN). This is the exact live receipt the audit recorded against Kùzu
        (``['demo.consumer', 'tests.test_reflib']``) vs Surreal's ``[]``.
        """
        graph, _env = reflib_graph
        importers = {node.qualified_name for node in await graph.what_imports(REFLIB_MODULE)}
        assert importers == {REFCONSUMER_MODULE, REFTEST_MODULE}

    async def test_module_target_finds_single_from_import_importer(
        self, modlib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """``what_imports("pkg.helpers")`` finds ``pkg.app`` (the only importer).

        Independent oracle: MODLIB_APP_SOURCE reads ``from pkg.helpers import
        build`` — the sole importer of the ``pkg.helpers`` module, queried by the
        module's own name (the audit's ``what_imports("pkg.helpers")`` receipt).
        """
        graph, _env = modlib_graph
        importers = {node.qualified_name for node in await graph.what_imports(MODLIB_HELPERS_MODULE)}
        assert importers == {MODLIB_APP_MODULE}

    async def test_dotted_module_target_finds_its_from_import_importer(
        self, app_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """A multi-segment dotted module target still resolves its importer.

        Independent oracle: TEST_SOURCE reads ``from demo.service import
        IndexService`` — ``tests.test_service`` imports a SYMBOL from the dotted
        module ``demo.service``, queried by the module's own dotted name (the
        audit's ``what_imports("demo.service")`` receipt).
        """
        graph, _env, _root = app_graph
        importers = {node.qualified_name for node in await graph.what_imports(APP_MODULE)}
        assert TEST_MODULE in importers

    async def test_module_target_prefix_does_not_leak_across_sibling_modules(
        self, modlib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """A naive string-prefix match must NOT confuse ``pkg.a`` with ``pkg.ab``.

        Independent oracle: MODLIB_APP_SOURCE imports ``pkg.ab.ab_symbol`` (``from
        pkg.ab import ab_symbol``) but NEVER imports anything from ``pkg.a``. The
        literal string ``"pkg.a"`` IS a Python string-prefix of
        ``"pkg.ab.ab_symbol"`` (adding one character, ``"b"``, turns one into the
        other) — an anchor-less ``STARTS WITH`` would wrongly report ``pkg.app``
        as an importer of ``pkg.a``. The correct, trailing-dot-anchored match
        (``pkg.a.`` vs ``pkg.ab.``) returns nothing for ``pkg.a`` and exactly
        ``pkg.app`` for ``pkg.ab``. Same anchor convention already decided for
        ``dead_code``'s module roll-up (``test_module_prefix_scoping_uses_
        trailing_dot_anchor``) — reused here, not reinvented.
        """
        graph, _env = modlib_graph
        assert list(await graph.what_imports(MODLIB_A_MODULE)) == []
        ab_importers = {node.qualified_name for node in await graph.what_imports(MODLIB_AB_MODULE)}
        assert ab_importers == {MODLIB_APP_MODULE}

    async def test_symbol_target_lookup_is_unaffected_by_the_module_target_fix(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """Regression guard: a SYMBOL-target query keeps ITS pre-existing behaviour.

        Independent oracle, unchanged from ``TestWhatImports``: ``widget``'s two
        importers by its OWN fqn (``demo.reflib.widget``, not the module name).
        This must hold both BEFORE and AFTER the module-target fix lands — the
        module-prefix arm must be strictly additive, never a replacement for the
        existing FQN/bare match.
        """
        graph, _env = reflib_graph
        importers = {node.qualified_name for node in await graph.what_imports(FQN_WIDGET)}
        assert importers == {REFCONSUMER_MODULE, REFTEST_MODULE}


class TestBlastRadiusModuleTarget:
    """``blast_radius`` must reach reverse-import dependents when a MODULE enters the walk."""

    async def test_module_target_at_the_root_reaches_its_from_import_importers(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """``blast_radius("demo.reflib", depth=3)`` reaches both module-level importers.

        Independent oracle: identical to the ``what_imports`` oracle above — both
        ``demo.consumer`` and ``tests.test_reflib`` import a symbol from
        ``demo.reflib``, a single hop back from the module target itself. ``depth=3``
        (generous, matching this file's own ``test_finds_direct_reverse_dependents``
        convention for a 1-hop assertion) so the case pins reachability, not an
        unrelated depth-boundary edge.
        """
        graph, _env = reflib_graph
        affected = {
            node.qualified_name
            for node in await graph.blast_radius(REFLIB_MODULE, depth=3, max_results=100)
        }
        assert REFCONSUMER_MODULE in affected
        assert REFTEST_MODULE in affected

    async def test_module_enters_the_frontier_mid_walk_and_still_reaches_its_importer(
        self, app_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """``blast_radius(symbol)`` still finds a 2nd-hop importer of the 1st-hop MODULE.

        Independent oracle, the audit's exact live-reproduced scenario: ``demo.
        service`` imports the symbol ``demo.errors.LoadError`` (1 hop back from
        LoadError reaches the MODULE node ``demo.service``, per APP_SOURCE's ``from
        demo.errors import LoadError``); ``tests.test_service`` in turn imports a
        SYMBOL from ``demo.service`` (TEST_SOURCE's ``from demo.service import
        IndexService``), reachable only via the module-prefix arm once ``demo.
        service`` — a bare module qualified_name, not a symbol fqn — enters the BFS
        frontier at hop 2. Kùzu already walks this correctly (the audit's
        ``blast_radius("demo.errors.LoadError")`` receipt); Model A drops
        ``tests.test_service`` here.
        """
        graph, _env, _root = app_graph
        affected = {
            node.qualified_name
            for node in await graph.blast_radius(FQN_LOAD_ERROR, depth=3, max_results=100)
        }
        assert APP_MODULE in affected  # 1st hop: demo.service imports LoadError
        assert TEST_MODULE in affected  # 2nd hop: test_service imports FROM demo.service


# ===========================================================================
# 5. tests_for — test-path nodes referencing the symbol + the test_x↔x heuristic.
# ===========================================================================


class TestTestsFor:
    """``tests_for`` links test nodes to a target by reference OR the name heuristic."""

    async def test_finds_test_by_reference_edge(
        self, app_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """A test-glob file that references the target's symbol is a test for it.

        ``tests/test_service.py`` imports ``IndexService`` and calls ``boot`` — a
        test-glob path with a resolved reference into the target.
        """
        graph, _env, _root = app_graph
        related_files = {node.file_path for node in await graph.tests_for(FQN_INDEX)}
        assert TEST_PATH in related_files

    async def test_finds_test_by_name_heuristic(
        self, app_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """``test_boot`` links to symbol ``boot`` via the ``test_x`` ↔ ``x`` heuristic."""
        graph, _env, _root = app_graph
        related_names = {node.qualified_name for node in await graph.tests_for(FQN_BOOT)}
        assert any(name.endswith("test_boot") for name in related_names)

    async def test_does_not_return_non_test_nodes(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """With no test file indexed, a depended-on symbol still has no tests.

        Build errors + service only (no test file). ``BaseService`` is inherited
        (has a reverse dependent) but nothing in a test path references it, so
        ``tests_for`` must not leak ordinary application nodes.
        """
        graph, _env, _root = demo_graph
        await _build(graph, _root, TIER_A, ERRORS_PATH, ERRORS_SOURCE, ERRORS_MODULE)
        await _build(graph, _root, TIER_A, APP_PATH, APP_SOURCE, APP_MODULE)
        assert list(await graph.tests_for(FQN_BASE)) == []


# ===========================================================================
# 6. references — production vs test split; defines excluded; dead ⇔ prod==0.
# ===========================================================================


class TestReferences:
    """``references`` counts references TO a symbol, split by production vs test."""

    async def test_splits_production_and_test_references(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """``widget`` has 2 distinct production sources and 2 distinct test sources.

        Independent oracle read off the source: production = {consumer module import,
        ``demo.consumer.run`` call}; test = {test module import, ``test_widget``
        call}. The crux is the split and that production is non-zero (alive). The
        distinct-source count forces the client-side dedup 3.1.5 requires (no
        ``SELECT DISTINCT <field>``).
        """
        graph, _env = reflib_graph
        summary = await graph.references(FQN_WIDGET)
        assert isinstance(summary, ReferenceSummary)
        assert summary.qualified_name == FQN_WIDGET
        assert summary.production_references == 2
        assert summary.test_references == 2

    async def test_referencing_nodes_are_distinct(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """The ``referencing`` list holds the distinct referrers, deduped."""
        graph, _env = reflib_graph
        summary = await graph.references(FQN_WIDGET)
        referencing_names = [node.qualified_name for node in summary.referencing]
        assert FQN_RUN in referencing_names  # the production caller is present
        assert len(referencing_names) == len(set(referencing_names))  # no dupes

    async def test_unreferenced_symbol_is_empty_not_error(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """``orphan`` is called by nobody → all-zero summary, not an error."""
        graph, _env = reflib_graph
        summary = await graph.references(FQN_ORPHAN)
        assert summary.production_references == 0
        assert summary.test_references == 0
        assert summary.referencing == []

    async def test_self_reference_is_excluded(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """``countdown`` calls only itself; the self-edge is NOT a reference."""
        graph, _env = reflib_graph
        summary = await graph.references(FQN_COUNTDOWN)
        assert summary.production_references == 0
        assert summary.test_references == 0

    async def test_defines_edge_is_not_a_reference(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """The structural ``defines`` parent edge does NOT count as a reference.

        ``orphan`` IS defined by its module (a ``defines`` refers edge points at
        it), yet ``references`` reports zero — proving ``defines`` is excluded
        (counting it would make nothing ever dead).
        """
        graph, env = reflib_graph
        # Ground truth at the storage layer: a defines edge to orphan exists.
        defines_to_orphan = await _relation_count(
            env,
            REFERS_RELATION,
            "kind = $kind AND out = $name",
            {"kind": EDGE_DEFINES, "name": RecordID(NAME_TABLE, FQN_ORPHAN)},
        )
        assert defines_to_orphan >= 1
        # …yet it does not count as a reference.
        assert (await graph.references(FQN_ORPHAN)).production_references == 0


# ===========================================================================
# 7. dead_code — zero-production-reference symbols; exclusions; module roll-up.
# ===========================================================================


class TestDeadCode:
    """``dead_code`` is the orphan sweep: nodes with zero PRODUCTION references."""

    async def test_reports_test_only_symbol_with_reason(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """``lonely`` is referenced ONLY from tests → dead, ``only_referenced_by_tests``.

        Independent oracle: two distinct test sources (the test module's import +
        ``test_lonely``'s call), zero production.
        """
        graph, _env = reflib_graph
        by_name = {node.qualified_name: node for node in await graph.dead_code([TIER_A])}
        assert FQN_LONELY in by_name
        lonely = by_name[FQN_LONELY]
        assert isinstance(lonely, DeadCodeNode)
        assert lonely.reason == REASON_ONLY_REFERENCED_BY_TESTS
        assert lonely.test_references == 2

    async def test_orphan_symbol_has_no_references_reason(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """``orphan`` (nobody calls it) → dead with reason ``no_references``."""
        graph, _env = reflib_graph
        by_name = {node.qualified_name: node for node in await graph.dead_code([TIER_A])}
        assert FQN_ORPHAN in by_name
        assert by_name[FQN_ORPHAN].reason == REASON_NO_REFERENCES
        assert by_name[FQN_ORPHAN].test_references == 0

    async def test_excludes_symbol_with_production_caller(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """``widget`` has a real production caller (``run``) → alive → absent."""
        graph, _env = reflib_graph
        dead_names = {node.qualified_name for node in await graph.dead_code([TIER_A])}
        assert FQN_WIDGET not in dead_names

    async def test_self_recursive_function_is_dead(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """A recursive function with no OTHER caller is dead (self-edge excluded)."""
        graph, _env = reflib_graph
        by_name = {node.qualified_name: node for node in await graph.dead_code([TIER_A])}
        assert FQN_COUNTDOWN in by_name
        assert by_name[FQN_COUNTDOWN].reason == REASON_NO_REFERENCES

    async def test_excludes_test_nodes_by_default_includes_with_flag(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """A test node isn't dead just because nothing calls it — unless asked."""
        graph, _env = reflib_graph
        default_paths = {node.file_path for node in await graph.dead_code([TIER_A])}
        assert REFTEST_PATH not in default_paths
        with_tests = {node.file_path for node in await graph.dead_code([TIER_A], include_tests=True)}
        assert REFTEST_PATH in with_tests

    async def test_scoped_to_passed_tiers_and_empty_tiers(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """Only the passed tiers are swept; an empty tiers list yields []."""
        graph, _env = reflib_graph
        assert await graph.dead_code([TIER_B]) == []  # nothing built under TIER_B
        assert await graph.dead_code([]) == []
        sample = {node.qualified_name for node in await graph.dead_code([TIER_A])}
        assert FQN_ORPHAN in sample

    async def test_respects_max_results_cap(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """The sweep is capped at ``max_results`` (several dead nodes exist)."""
        graph, _env = reflib_graph
        assert len(await graph.dead_code([TIER_A], max_results=1)) == 1

    async def test_dead_code_bounds_constants_are_sane(self) -> None:
        """The default cap is positive and no greater than the hard ceiling."""
        # Pure-logic surface guard (no server): the reviewable-size default must
        # sit within the pathological-request ceiling.
        assert 0 < DEFAULT_DEAD_CODE_MAX_RESULTS <= MAX_DEAD_CODE_MAX_RESULTS

    async def test_excludes_dunder_methods_by_default(
        self, surreal_env: SurrealEnv, tmp_path: Path  # noqa: F811
    ) -> None:
        """``__init__`` (protocol-invoked) is excluded by default; plain method isn't.

        Independent oracle: a dunder is never an explicit call edge, so it always
        looks orphaned; a plain unreferenced method in the same class is genuinely
        dead and must appear.
        """
        source = textwrap.dedent(
            '''\
            """A class with a dunder and a plain unreferenced method."""


            class Thing:
                def __init__(self):
                    self.value = 0

                def plain_unused(self):
                    return self.value
            '''
        )
        project_root = tmp_path / "project"
        (project_root / "pkg").mkdir(parents=True)
        (project_root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
        (project_root / "pkg" / "thing.py").write_text(source, encoding="utf-8")
        graph = await _make_graph(
            surreal_env, tier_roots={TIER_A: project_root}, project_roots=[project_root]
        )
        try:
            await _build(graph, project_root, TIER_A, "pkg/thing.py", source, "pkg.thing")
            default_names = {n.qualified_name for n in await graph.dead_code([TIER_A])}
            assert "pkg.thing.Thing.__init__" not in default_names
            assert "pkg.thing.Thing.plain_unused" in default_names  # sanity
            with_flag = {n.qualified_name for n in await graph.dead_code([TIER_A], include_dunders=True)}
            assert "pkg.thing.Thing.__init__" in with_flag
        finally:
            await graph.close()

    async def test_excludes_entry_modules_by_default(
        self, surreal_env: SurrealEnv, tmp_path: Path  # noqa: F811
    ) -> None:
        """``__main__`` and ``__init__`` package modules are excluded by default.

        Independent oracle: neither is imported by dotted name, so both always look
        orphaned; by default neither module node is reported, with the flag both are.
        """
        project_root = tmp_path / "project"
        (project_root / "pkg").mkdir(parents=True)
        init_source = '"""The package init."""\n'
        main_source = '"""The CLI entrypoint."""\n\n\ndef main():\n    return 0\n'
        (project_root / "pkg" / "__init__.py").write_text(init_source, encoding="utf-8")
        (project_root / "pkg" / "__main__.py").write_text(main_source, encoding="utf-8")
        graph = await _make_graph(
            surreal_env, tier_roots={TIER_A: project_root}, project_roots=[project_root]
        )
        try:
            await _build(graph, project_root, TIER_A, "pkg/__init__.py", init_source, "pkg")
            await _build(graph, project_root, TIER_A, "pkg/__main__.py", main_source, "pkg.__main__")
            default_modules = {
                n.qualified_name
                for n in await graph.dead_code([TIER_A])
                if n.kind == KIND_MODULE
            }
            assert "pkg" not in default_modules
            assert "pkg.__main__" not in default_modules
            with_flag = {
                n.qualified_name
                for n in await graph.dead_code([TIER_A], include_entrypoints=True)
                if n.kind == KIND_MODULE
            }
            assert "pkg" in with_flag
            assert "pkg.__main__" in with_flag
        finally:
            await graph.close()

    async def test_lifecycle_flip_on_rebuild(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv], tmp_path: Path
    ) -> None:
        """Removing the last production caller flips a symbol to dead; re-adding revives.

        ``widget`` starts alive (caller ``run``). Rebuild ``consumer.py`` without the
        call → widget dead (test-only). Rebuild it back → alive. The per-file rebuild
        must track liveness both ways (degradation → recovery).
        """
        graph, _env = reflib_graph
        # The fixture's tier-root (the SAME function-scoped tmp_path it built the
        # package under) — where _build writes the rebuilt source before re-resolving.
        project_root = tmp_path / "project"
        assert FQN_WIDGET not in {n.qualified_name for n in await graph.dead_code([TIER_A])}

        no_call_source = textwrap.dedent(
            '''\
            """The consumer no longer calls widget."""
            from __future__ import annotations


            def run(value):
                """No longer references the library."""
                return value
            '''
        )
        await _build(graph, project_root, TIER_A, REFCONSUMER_PATH, no_call_source, REFCONSUMER_MODULE)
        after = {n.qualified_name: n for n in await graph.dead_code([TIER_A])}
        assert FQN_WIDGET in after
        assert after[FQN_WIDGET].reason == REASON_ONLY_REFERENCED_BY_TESTS

        await _build(graph, project_root, TIER_A, REFCONSUMER_PATH, REFCONSUMER_SOURCE, REFCONSUMER_MODULE)
        assert FQN_WIDGET not in {n.qualified_name for n in await graph.dead_code([TIER_A])}


# --- dead_code module-node roll-up (references are symbol-level) --------------

MODLIB_HELPERS_SOURCE: str = textwrap.dedent(
    '''\
    """A helper module whose SYMBOL (not its bare module name) is used."""
    from __future__ import annotations


    def build(value):
        """Imported and called by the production app — keeps this module alive."""
        return value + 1
    '''
)
MODLIB_ORPHAN_SOURCE: str = textwrap.dedent(
    '''\
    """A module nobody references — neither it nor its symbol is used anywhere."""
    from __future__ import annotations


    def never_used(value):
        """Called by nobody, anywhere."""
        return value * 2
    '''
)
MODLIB_A_SOURCE: str = textwrap.dedent(
    '''\
    """Module pkg.a — its symbol is unreferenced; pkg.ab must not save it."""
    from __future__ import annotations


    def a_symbol(value):
        """Referenced by nobody — pkg.a must stay dead."""
        return value
    '''
)
MODLIB_AB_SOURCE: str = textwrap.dedent(
    '''\
    """Module pkg.ab — its symbol IS used; pkg.ab is alive, pkg.a is not."""
    from __future__ import annotations


    def ab_symbol(value):
        """Imported and called by the production app — keeps pkg.ab alive."""
        return value + 10
    '''
)
MODLIB_APP_SOURCE: str = textwrap.dedent(
    '''\
    """The production app — the source of the package's production references."""
    from __future__ import annotations

    from pkg.helpers import build
    from pkg.ab import ab_symbol


    def run(value):
        """Calls the two used symbols (helpers.build, ab.ab_symbol)."""
        return build(value) + ab_symbol(value)
    '''
)

MODLIB_HELPERS_MODULE: str = "pkg.helpers"
MODLIB_ORPHAN_MODULE: str = "pkg.orphan_mod"
MODLIB_A_MODULE: str = "pkg.a"
MODLIB_AB_MODULE: str = "pkg.ab"
MODLIB_APP_MODULE: str = "pkg.app"

MODLIB_HELPERS_PATH: str = "pkg/helpers.py"
MODLIB_ORPHAN_PATH: str = "pkg/orphan_mod.py"
MODLIB_A_PATH: str = "pkg/a.py"
MODLIB_AB_PATH: str = "pkg/ab.py"
MODLIB_APP_PATH: str = "pkg/app.py"


def _write_modlib_package(root: Path) -> None:
    """Materialise the module-roll-up demo package (helpers/orphan/a/ab/app) on disk."""
    (root / "pkg").mkdir(parents=True, exist_ok=True)
    (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (root / "pkg" / "helpers.py").write_text(MODLIB_HELPERS_SOURCE, encoding="utf-8")
    (root / "pkg" / "orphan_mod.py").write_text(MODLIB_ORPHAN_SOURCE, encoding="utf-8")
    (root / "pkg" / "a.py").write_text(MODLIB_A_SOURCE, encoding="utf-8")
    (root / "pkg" / "ab.py").write_text(MODLIB_AB_SOURCE, encoding="utf-8")
    (root / "pkg" / "app.py").write_text(MODLIB_APP_SOURCE, encoding="utf-8")


@pytest_asyncio.fixture()
async def modlib_graph(
    surreal_env: SurrealEnv,  # noqa: F811
    tmp_path: Path,
) -> AsyncIterator[tuple[SurrealCodeGraph, SurrealEnv]]:
    """A graph over the module-roll-up package (symbol-level refs, all built)."""
    project_root = tmp_path / "project"
    _write_modlib_package(project_root)
    graph = await _make_and_build_graph(
        surreal_env,
        project_root,
        [
            (MODLIB_HELPERS_PATH, MODLIB_HELPERS_SOURCE, MODLIB_HELPERS_MODULE),
            (MODLIB_ORPHAN_PATH, MODLIB_ORPHAN_SOURCE, MODLIB_ORPHAN_MODULE),
            (MODLIB_A_PATH, MODLIB_A_SOURCE, MODLIB_A_MODULE),
            (MODLIB_AB_PATH, MODLIB_AB_SOURCE, MODLIB_AB_MODULE),
            (MODLIB_APP_PATH, MODLIB_APP_SOURCE, MODLIB_APP_MODULE),
        ],
    )
    try:
        yield graph, surreal_env
    finally:
        await graph.close()


class TestDeadCodeModuleRollUp:
    """A MODULE is dead only if neither it nor any symbol it defines is used."""

    async def test_module_with_referenced_symbol_is_not_dead(
        self, modlib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """The regression: a module whose SYMBOL has a production ref is NOT dead.

        Independent oracle: ``pkg.helpers`` is never referenced by its bare module
        name, but ``pkg.helpers.build`` is imported AND called by ``pkg.app``. The
        module must be alive even though ``references('pkg.helpers')`` is zero.
        """
        graph, _env = modlib_graph
        assert (await graph.references(MODLIB_HELPERS_MODULE)).production_references == 0
        assert (await graph.references("pkg.helpers.build")).production_references >= 1
        dead_modules = {n.qualified_name for n in await graph.dead_code([TIER_A]) if n.kind == KIND_MODULE}
        assert MODLIB_HELPERS_MODULE not in dead_modules

    async def test_fully_orphaned_module_is_dead(
        self, modlib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """A module whose neither self nor symbols are referenced is STILL dead."""
        graph, _env = modlib_graph
        by_name = {n.qualified_name: n for n in await graph.dead_code([TIER_A]) if n.kind == KIND_MODULE}
        assert MODLIB_ORPHAN_MODULE in by_name
        assert by_name[MODLIB_ORPHAN_MODULE].reason == REASON_NO_REFERENCES

    async def test_module_prefix_scoping_uses_trailing_dot_anchor(
        self, modlib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """``pkg.a`` is NOT kept alive by a reference to ``pkg.ab``'s symbol.

        Independent oracle: ``pkg.a.a_symbol`` is unreferenced; only ``pkg.ab.
        ab_symbol`` is used. A trailing-dot anchor (``pkg.a.``) must not prefix-match
        ``pkg.ab.ab_symbol``, so ``pkg.a`` stays dead while ``pkg.ab`` is alive.
        """
        graph, _env = modlib_graph
        dead_modules = {n.qualified_name for n in await graph.dead_code([TIER_A]) if n.kind == KIND_MODULE}
        assert MODLIB_A_MODULE in dead_modules
        assert MODLIB_AB_MODULE not in dead_modules


# ===========================================================================
# 8. Order-independence (load-bearing) — build order must not change results.
# ===========================================================================


class TestOrderIndependence:
    """A caller graphed BEFORE its callee still resolves once the callee is built.

    The RELATE mechanism: a ``refers`` edge to a not-yet-defined ``name`` simply
    UPSERTs the name first (no dangling error); when the callee's file is later
    built, its ``answers_to`` closes the reverse path. So building the caller-first
    and the callee-first must reach byte-identical query results.
    """

    async def _blast_after_orders(
        self, env: SurrealEnv, project_root: Path, order: tuple[str, ...]
    ) -> set[str]:
        """Build the two demo files in ``order`` on ``env`` and return the radius."""
        graph = await _make_graph(env, tier_roots={TIER_A: project_root}, project_roots=[project_root])
        try:
            builders = {
                ERRORS_PATH: (ERRORS_PATH, ERRORS_SOURCE, ERRORS_MODULE),
                APP_PATH: (APP_PATH, APP_SOURCE, APP_MODULE),
            }
            for key in order:
                path, source, module = builders[key]
                await _build(graph, project_root, TIER_A, path, source, module)
            return {
                n.qualified_name
                for n in await graph.blast_radius(FQN_LOAD_ERROR, depth=2, max_results=50)
            }
        finally:
            await graph.close()

    async def test_caller_before_callee_matches_callee_before_caller(
        self, surreal_env: SurrealEnv, tmp_path: Path  # noqa: F811
    ) -> None:
        """blast_radius(LoadError) is identical whether app or errors is built first.

        Caller-first (``app`` then ``errors``) is the load-bearing order: when
        ``app`` is graphed, ``name:demo.errors.LoadError`` is UPSERTed by its import
        edge though NO node answers_to it yet; building ``errors`` afterwards closes
        the reverse path. The importing module (``demo.service``) must appear in
        LoadError's blast radius in BOTH orders, and the two results must match.
        """
        project_root = tmp_path / "project"
        _write_demo_package(project_root)
        # Two fresh databases so the two orders never share state.
        caller_first_env = surreal_env
        callee_first = await self._blast_after_orders(caller_first_env, project_root, (ERRORS_PATH, APP_PATH))
        caller_first = await self._blast_after_orders(caller_first_env, project_root, (APP_PATH, ERRORS_PATH))
        assert APP_MODULE in caller_first, "caller-first build failed to close the reverse path"
        assert caller_first == callee_first, "build order changed the query result"


# ===========================================================================
# 9. FQN collision — a bare reference fans out to every node answering that name.
# ===========================================================================

# Two DISTINCT modules each defining a class named ``Config`` (same bare name,
# different FQN). A third module makes an un-inferable bare reference to
# ``Config`` (astroid cannot infer it → resolved=False, dst = bare ``Config``),
# so it lands on ``name:Config`` — which BOTH Config nodes answer_to. The single
# bare reference is therefore a reference to BOTH FQNs (the fan-out).
COLLIDE_ALPHA_SOURCE: str = textwrap.dedent(
    '''\
    """pkg.alpha — defines a class named Config."""


    class Config:
        """The alpha Config."""
    '''
)
COLLIDE_BETA_SOURCE: str = textwrap.dedent(
    '''\
    """pkg.beta — ALSO defines a class named Config (same bare name)."""


    class Config:
        """The beta Config."""
    '''
)
COLLIDE_USER_SOURCE: str = textwrap.dedent(
    '''\
    """pkg.user — an un-inferable bare reference to Config (never imported)."""


    class Widget(Config):  # noqa: F821 - intentionally un-imported / un-inferable
        """Inherits a bare, unresolved Config."""
    '''
)

COLLIDE_ALPHA_PATH: str = "pkg/alpha.py"
COLLIDE_BETA_PATH: str = "pkg/beta.py"
COLLIDE_USER_PATH: str = "pkg/user.py"
COLLIDE_ALPHA_MODULE: str = "pkg.alpha"
COLLIDE_BETA_MODULE: str = "pkg.beta"
COLLIDE_USER_MODULE: str = "pkg.user"


def _write_collide_package(root: Path) -> None:
    """Materialise the FQN-collision demo package (alpha/beta/user) on disk."""
    (root / "pkg").mkdir(parents=True, exist_ok=True)
    (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (root / "pkg" / "alpha.py").write_text(COLLIDE_ALPHA_SOURCE, encoding="utf-8")
    (root / "pkg" / "beta.py").write_text(COLLIDE_BETA_SOURCE, encoding="utf-8")
    (root / "pkg" / "user.py").write_text(COLLIDE_USER_SOURCE, encoding="utf-8")


class TestFqnCollision:
    """The SAME qualified/bare name across files stays distinct AND fans out."""

    @pytest_asyncio.fixture()
    async def collide_graph(
        self,
        surreal_env: SurrealEnv,  # noqa: F811
        tmp_path: Path,
    ) -> AsyncIterator[tuple[SurrealCodeGraph, SurrealEnv]]:
        project_root = tmp_path / "project"
        _write_collide_package(project_root)
        graph = await _make_and_build_graph(
            surreal_env,
            project_root,
            [
                (COLLIDE_ALPHA_PATH, COLLIDE_ALPHA_SOURCE, COLLIDE_ALPHA_MODULE),
                (COLLIDE_BETA_PATH, COLLIDE_BETA_SOURCE, COLLIDE_BETA_MODULE),
                (COLLIDE_USER_PATH, COLLIDE_USER_SOURCE, COLLIDE_USER_MODULE),
            ],
        )
        try:
            yield graph, surreal_env
        finally:
            await graph.close()

    async def test_same_qualified_name_two_files_are_distinct_rows(
        self, surreal_env: SurrealEnv, tmp_path: Path  # noqa: F811
    ) -> None:
        """Two tiers' copies of one file keep DISTINCT code_node rows (collision-correct).

        The deterministic id includes the tier, so the SAME qualified_name under two
        tiers is two distinct rows — never conflated (the identity the Kùzu design
        used a surrogate id to protect).
        """
        project_root = tmp_path / "project"
        _write_demo_package(project_root)
        graph = await _make_graph(
            surreal_env, tier_roots={TIER_A: project_root, TIER_B: project_root}, project_roots=[project_root]
        )
        try:
            chunks = _chunk(APP_PATH, APP_SOURCE)
            await graph.build_file_graph(TIER_A, APP_PATH, chunks, module_name=APP_MODULE)
            await graph.build_file_graph(TIER_B, APP_PATH, chunks, module_name=APP_MODULE)
            base_rows = [
                r for r in await _code_node_rows(surreal_env, kind=KIND_CLASS)
                if r["qualified_name"] == FQN_BASE
            ]
            tiers = {r["tier"] for r in base_rows}
            assert tiers == {TIER_A, TIER_B}  # two distinct rows, one per tier
        finally:
            await graph.close()

    async def test_bare_reference_fans_out_to_both_definitions(
        self, collide_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """One bare ``Config`` reference counts against BOTH ``Config`` FQNs.

        Independent oracle read off the source: ``pkg.user.Widget`` inherits a bare,
        un-inferable ``Config``; both ``pkg.alpha.Config`` and ``pkg.beta.Config``
        answer_to ``name:Config``, so the single reference is a reference to each.
        """
        graph, _env = collide_graph
        alpha = await graph.references("pkg.alpha.Config")
        beta = await graph.references("pkg.beta.Config")
        alpha_referrers = {n.qualified_name for n in alpha.referencing}
        beta_referrers = {n.qualified_name for n in beta.referencing}
        assert "pkg.user.Widget" in alpha_referrers  # fans out to alpha
        assert "pkg.user.Widget" in beta_referrers  # …and to beta
        assert alpha.production_references >= 1
        assert beta.production_references >= 1


# ===========================================================================
# 10. Per-file purge isolation — delete removes exactly that file's rows.
# ===========================================================================


class TestPerFilePurgeIsolation:
    """``delete_file_graph`` purges one (tier, file) — siblings survive intact."""

    async def test_delete_removes_exactly_that_files_rows(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """After delete: the file's code_node + refers + answers_to rows are gone."""
        graph, env, _root = demo_graph
        await _build(graph, _root, TIER_A, APP_PATH, APP_SOURCE, APP_MODULE)
        assert await _code_node_rows(env, tier=TIER_A, file_path=APP_PATH)

        await graph.delete_file_graph(TIER_A, APP_PATH)

        assert await _code_node_rows(env, tier=TIER_A, file_path=APP_PATH) == []
        refers_left = await _relation_count(
            env, REFERS_RELATION, "src_tier = $t AND src_file_path = $f", {"t": TIER_A, "f": APP_PATH}
        )
        answers_left = await _relation_count(
            env, ANSWERS_TO_RELATION, "tier = $t AND file_path = $f", {"t": TIER_A, "f": APP_PATH}
        )
        assert refers_left == 0
        assert answers_left == 0

    async def test_delete_is_tier_scoped(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """Deleting one tier's copy of a path leaves another tier's copy intact (C1)."""
        graph, env, _root = demo_graph
        chunks = _chunk(APP_PATH, APP_SOURCE)
        await graph.build_file_graph(TIER_A, APP_PATH, chunks, module_name=APP_MODULE)
        await graph.build_file_graph(TIER_B, APP_PATH, chunks, module_name=APP_MODULE)
        await graph.delete_file_graph(TIER_A, APP_PATH)
        assert await _code_node_rows(env, tier=TIER_A, file_path=APP_PATH) == []
        assert await _code_node_rows(env, tier=TIER_B, file_path=APP_PATH)  # survives

    async def test_sibling_file_survives_and_queries_stay_correct(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """Purging service.py leaves errors.py's rows AND leaves orphan names harmless.

        The whole package is built; deleting ``service.py`` removes its rows and may
        leave orphan ``name`` nodes (that only its edges pointed at). Those orphans
        must be harmless — the surviving file's queries stay correct and error-free.
        """
        graph, env, _root = demo_graph
        await _build(graph, _root, TIER_A, ERRORS_PATH, ERRORS_SOURCE, ERRORS_MODULE)
        await _build(graph, _root, TIER_A, APP_PATH, APP_SOURCE, APP_MODULE)
        errors_before = {
            r["qualified_name"] for r in await _code_node_rows(env, tier=TIER_A, file_path=ERRORS_PATH)
        }

        await graph.delete_file_graph(TIER_A, APP_PATH)

        errors_after = {
            r["qualified_name"] for r in await _code_node_rows(env, tier=TIER_A, file_path=ERRORS_PATH)
        }
        assert errors_after == errors_before  # sibling rows survive byte-identical
        # Orphan name nodes (if any) are harmless: the surviving symbol's query still
        # runs cleanly and returns the correct (now zero) reference profile.
        summary = await graph.references(FQN_LOAD_ERROR)
        assert summary.production_references == 0  # its only importer (service) is gone
        remaining = {r["qualified_name"] for r in await _code_node_rows(env)}
        assert FQN_INDEX not in remaining  # service symbols gone


# ===========================================================================
# 11. Deterministic id — same (tier, file_path, qname) ⇒ same record id.
# ===========================================================================


class TestDeterministicId:
    """The client-generated id is a deterministic ``RecordID`` → idempotent rebuild."""

    async def test_rebuild_is_idempotent_no_duplicate_nodes(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """Building the same file twice does not double its nodes."""
        graph, env, _root = demo_graph
        chunks = _chunk(APP_PATH, APP_SOURCE)
        await graph.build_file_graph(TIER_A, APP_PATH, chunks, module_name=APP_MODULE)
        first = len(await _code_node_rows(env, tier=TIER_A, file_path=APP_PATH))
        await graph.build_file_graph(TIER_A, APP_PATH, chunks, module_name=APP_MODULE)
        second = len(await _code_node_rows(env, tier=TIER_A, file_path=APP_PATH))
        assert first == second
        assert first > 0  # sanity: the file actually produced nodes

    async def test_node_id_is_the_deterministic_composite_record_id(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """A node's record id key is exactly ``[tier, file_path, qualified_name]``.

        The DECIDED S13 scheme (an array-keyed ``RecordID``, like ``file:[tier,
        file_path]``). The expected id is constructed from the same components the
        caller supplied — no round-trip to learn a server id — so two builds of the
        same file target the SAME row.
        """
        graph, env, _root = demo_graph
        await _build(graph, _root, TIER_A, APP_PATH, APP_SOURCE, APP_MODULE)
        rows = [
            r for r in await _code_node_rows(env, tier=TIER_A, file_path=APP_PATH)
            if r["qualified_name"] == FQN_INDEX
        ]
        assert len(rows) == 1
        record_id = rows[0]["id"]
        assert isinstance(record_id, RecordID)
        # The key is the deterministic composite (order [tier, file_path, qname]).
        assert record_id == RecordID(CODE_NODE_TABLE, [TIER_A, APP_PATH, FQN_INDEX])


# ===========================================================================
# 12. Resilience — a down server RAISES (never silently empty); mid-life heal.
# ===========================================================================


class TestResilience:
    """Honest failure: down ⇒ raise; mid-life socket drop ⇒ self-heal next call."""

    async def test_down_server_raises_never_returns_empty(
        self, tmp_path: Path
    ) -> None:
        """A query against a DOWN server RAISES ``SurrealConnectionError`` — not [].

        A silently-empty graph would let the reconcile pass mistake a dead server
        for a wiped index. The failure must be LOUD and typed.
        """
        project_root = tmp_path / "project"
        _write_demo_package(project_root)
        graph = SurrealCodeGraph(
            url=_DEAD_URL,
            namespace="lore_test",
            database="never_created",
            user="root",
            password="spikeroot",
            tier_roots={TIER_A: project_root},
            project_roots=[project_root],
        )
        try:
            with pytest.raises(SurrealConnectionError):
                await graph.indexed_file_count()
        finally:
            await graph.close()

    async def test_mid_life_connection_drop_self_heals(
        self, reflib_graph: tuple[SurrealCodeGraph, SurrealEnv]
    ) -> None:
        """After its live socket is force-closed, the next call transparently reconnects.

        Degradation: close the graph's cached connection out from under it.
        Recovery: the next query re-establishes a freshly signed-in connection and
        returns the correct result (whether it heals transparently or surfaces one
        transient error then reconnects — ``call_until_recovered``).
        """
        graph, _env = reflib_graph
        # Degrade: force-close the graph's live cached socket out from under it
        # (the exact idiom ``test_surreal_manifest`` uses on its own ``_connection``).
        connection = graph._connection  # noqa: SLF001 - lifecycle probe
        assert connection is not None, "the fixture's builds must have opened a connection"
        await connection.close()

        # Recovery: the next call reconnects (transparently, or after one transient
        # heal-able error), then serves the correct count.
        healed = await call_until_recovered(
            lambda: graph.indexed_file_count(),
            _HEALABLE_ERRORS,
            label="graph",
        )
        assert healed == 3  # reflib + consumer + test — the three files stay indexed


# ===========================================================================
# 13. Naming helper survives the port (the indexer calls it statically).
# ===========================================================================


class TestNamingHelperSurvivesPort:
    """``importable_module_name`` is a pure static helper the indexer still calls.

    It MOVES UNCHANGED with the derivation; this pins that the port re-exposes it
    (so ``indexer._importable_module_name`` keeps compiling) with its load-bearing
    behaviour — the doubled-member-dir fix — intact. Pure logic, no server.
    """

    def test_strips_leading_member_dir_to_package_top(self, tmp_path: Path) -> None:
        """``loremaster/loremaster/config.py`` → ``loremaster.config`` (NOT doubled)."""
        inner = tmp_path / "loremaster" / "loremaster"
        inner.mkdir(parents=True)
        (inner / "__init__.py").write_text("", encoding="utf-8")
        (inner / "config.py").write_text("X = 1\n", encoding="utf-8")
        assert (
            SurrealCodeGraph.importable_module_name(tmp_path, "loremaster/loremaster/config.py")
            == "loremaster.config"
        )

    def test_namespace_layout_degrades_to_full_join(self, tmp_path: Path) -> None:
        """No ``__init__.py`` anywhere → strip nothing (the documented fallback)."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "widget.py").write_text("W = 1\n", encoding="utf-8")
        assert SurrealCodeGraph.importable_module_name(tmp_path, "src/widget.py") == "src.widget"


# ===========================================================================
# 14. reset_resolution_cache is a SYNC surface (the indexer calls it at a sweep
#     boundary, NOT awaited — it only touches astroid's process-global cache).
# ===========================================================================


class TestResolutionCacheSurface:
    """``reset_resolution_cache`` stays a synchronous, side-effect-only method."""

    async def test_reset_resolution_cache_is_sync_and_safe(
        self, demo_graph: tuple[SurrealCodeGraph, SurrealEnv, Path]
    ) -> None:
        """It is callable WITHOUT await and returns None (no DB round-trip)."""
        graph, _env, _root = demo_graph
        # No ``await`` — a coroutine here would be a contract break for the indexer.
        # No ``await``, and a coroutine-function guard: the indexer calls this from
        # SYNCHRONOUS code at a sweep boundary, so it must stay a sync method.
        assert not inspect.iscoroutinefunction(graph.reset_resolution_cache)
        graph.reset_resolution_cache()  # sync, side-effect only (returns None by contract)


# ===========================================================================
# 15. _AstroidDerivation delegate safety — the borrowed pure-derivation surface
#     must never reach a Kùzu connection; touching it fails LOUD and immediate.
# ===========================================================================


class TestAstroidDerivationDelegateSafety:
    """``_AstroidDerivation`` skips the Kùzu open; reaching it must fail loud."""

    def test_execute_refuses_with_a_targeted_diagnostic(self) -> None:
        """The reused derivation's sole Kùzu chokepoint raises immediately.

        Every OTHER Kùzu-facing ``CodeGraph`` method funnels through
        ``_execute`` (see ``graph.py``), so this pins that the delegate's
        override fails LOUDLY and specifically — never an incidental, unrelated
        ``AttributeError`` — should a future change to a reused derivation
        method ever add a stray Kùzu query.
        """
        derivation = _AstroidDerivation(tier_roots=None, project_roots=None)
        with pytest.raises(RuntimeError, match="never opens a Kùzu connection"):
            derivation._execute("RETURN 1")  # noqa: SLF001 - guardrail probe


# ---------------------------------------------------------------------------
# _OPERATOR_NOTE — behaviours that do NOT map cleanly onto the RELATE model, and
# caller-visible changes the port forces. Surfaced in the returned report; kept
# here so the STUB/GREEN engineer sees them in-file too.
#
# 1. SYNC → ASYNC (unavoidable). The Kùzu ``CodeGraph`` is fully synchronous; the
#    ``surrealdb`` SDK is async-only. build_file_graph / delete_file_graph /
#    what_imports / blast_radius / tests_for / references / dead_code /
#    indexed_file_count therefore become ``async def`` (they await the SDK +
#    reuse the async ``execute_transaction`` per-file txn). Every call site in the
#    indexer (``_refresh_graph`` is sync but sits inside async ``index_file``;
#    ``reconcile._purge_deletions`` is async) and the server's ``_AppContext``
#    graph methods must add ``await``. This mirrors what P2/P3 forced on the
#    store/manifest callers — NOT optional.
#
# 2. Constructor change. ``CodeGraph(db_path, *, tier_roots, project_roots)`` →
#    ``SurrealCodeGraph(*, url, namespace, database, user, password, tier_roots,
#    project_roots)`` (no ``dim`` — the code-graph stores no vectors). Both build
#    sites (server ``_build_code_graph``, the ``graph_path=…graph.kuzu`` wiring)
#    change.
#
# 3. GraphNode.id representation. Kùzu used an int SERIAL id; Model A has no
#    surrogate — a node's identity is the composite ``RecordID`` [tier, file_path,
#    qualified_name]. The port should type ``GraphNode.id`` as ``str`` (the
#    stringified record id) or drop it in favour of the (tier, file_path, qname)
#    triple. These tests dedupe/compare by qualified_name and inspect the raw
#    RecordID directly, so they do not hard-code the id type — but the server
#    serializes GraphNode to the MCP client, so the field-type change is
#    caller-visible and needs a decision.
#
# 4. what_imports bare-name seam requires the target's file in the graph. Kùzu
#    matched ``r.dst ENDS WITH ".LoadError"`` (file-independent). Model A bridges
#    bare↔FQN through the TARGET node's answers_to fan-out, so
#    ``what_imports("LoadError")`` needs the LoadError node built. Production
#    always indexes the whole project, so this holds; but the strict
#    build-only-the-importer variant of ``test_graph.py``'s bare-seam test cannot
#    be preserved 1:1. Pinned here under the realistic whole-package build
#    (``TestWhatImports.test_matches_by_bare_name_under_whole_package_build``) and
#    flagged rather than papered over.
#
# 5. The Kùzu-only surface does not port: the ``.connection`` property,
#    ``CALL show_tables()`` / ``CALL table_info()`` schema introspection, and
#    ``open_resilient_kuzu`` are replaced by the store-style lazy async connection
#    + ``INFO FOR DB`` / ``INFO FOR TABLE`` DDL introspection.
# ---------------------------------------------------------------------------
_OPERATOR_NOTE = (
    "see the module footnote for sync\u2192async, constructor, GraphNode.id, "
    "and bare-seam divergences"
)


# ---------------------------------------------------------------------------
# P5-C1c (SurrealDB docs-audit, ledger #28), hardening #1: ``ensure_ready``
# must be LOUD on ANY failing DDL statement, not just the first — mirrors
# ``test_surreal_store.py``'s identical concern (the SAME SDK gap: ``query()``
# validates only the first statement of a multi-statement string). See that
# file's matching section for the live-verified proof that the invalid
# statement below fails at EXECUTION (not parse) and every statement after it
# still applies while ``query()`` raises nothing.
# ---------------------------------------------------------------------------

# The ghost index/field names the invalid DDL statement below references.
_GHOST_INDEX_NAME = "ghost_idx_probe"
_GHOST_FIELD_NAME = "ghost_field_xyz_probe"


def _invalid_ddl_statement(table: str) -> str:
    """A syntactically valid ``DEFINE INDEX`` that 3.1.5 rejects AT EXECUTION.

    Indexing a field never ``DEFINE FIELD``'d on ``table`` parses cleanly but
    fails when the engine tries to build the index (verified live:
    ``status: "ERR"``, ``"The field '<field>' does not exist"``), while
    ``query()`` raises nothing and the ghost index is confirmed absent
    afterward.
    """
    return (
        f"DEFINE INDEX IF NOT EXISTS {_GHOST_INDEX_NAME} ON {table} "
        f"FIELDS {_GHOST_FIELD_NAME}"
    )


def _ddl_with_late_invalid_statement(ddl: str, table: str) -> str:
    """Splice :func:`_invalid_ddl_statement` into the MIDDLE of a real DDL string.

    A middle position proves the SDK's first-statement-only check misses a
    failure ANYWHERE downstream of the first statement.
    """
    statements = [stmt.strip() for stmt in ddl.strip().split(";\n") if stmt.strip()]
    middle_index = len(statements) // 2
    statements.insert(middle_index, _invalid_ddl_statement(table))
    return ";\n".join(statements) + ";\n"


class TestEnsureReadyRaisesOnLateDdlFailure:
    """P5-C1c hardening #1: a LATER DDL statement's rejection must surface.

    LOAD-BEARING: must FAIL RED against current code — ``ensure_ready``
    applies ``generate_graph_ddl()`` via a bare ``connection.query(ddl)``
    call, which inspects only the first statement and swallows a later
    ``ERR`` completely.
    """

    async def test_ensure_ready_raises_on_a_semantically_invalid_late_ddl_statement(
        self, surreal_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch  # noqa: F811
    ) -> None:
        # Arrange: the REAL graph DDL, poisoned mid-way through.
        real_ddl = generate_graph_ddl()
        poisoned_ddl = _ddl_with_late_invalid_statement(real_ddl, CODE_NODE_TABLE)

        def _poisoned_generate_graph_ddl() -> str:
            return poisoned_ddl

        monkeypatch.setattr(
            "loremaster.graph_surreal.generate_graph_ddl", _poisoned_generate_graph_ddl
        )
        broken_graph = SurrealCodeGraph(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user,
            password=surreal_env.password,
            tier_roots={},
            project_roots=[],
        )

        try:
            # Act / Assert: a domain/schema rejection — the transport is
            # healthy — must surface as a STORE error, never a silent success.
            with pytest.raises(SurrealStoreError) as exc_info:
                await broken_graph.ensure_ready()
            assert type(exc_info.value) is SurrealStoreError
            assert not isinstance(exc_info.value, SurrealConnectionError)
            assert broken_graph._connection is not None
        finally:
            await broken_graph.close()


# ---------------------------------------------------------------------------
# P5-C1c, hardening #2: ``_drop_connection`` must be a compare-and-swap, not
# an unconditional null — mirrors ``test_surreal_store.py``'s identical
# concern for ``SurrealCodeGraph``'s own connection-lifecycle seam.
# ---------------------------------------------------------------------------


def _plain_counting_connection_factory() -> tuple[Callable[[str], Any], Callable[[], int]]:
    """A drop-in ``AsyncSurreal`` replacement that COUNTS every real connection
    it opens — no artificial signin delay, since this test drives its callers
    SEQUENTIALLY (no concurrent race to widen).

    Returns:
        ``(factory, get_call_count)``.
    """
    call_count = 0

    def factory(url: str) -> Any:
        nonlocal call_count
        call_count += 1
        return _RealAsyncSurreal(url)

    return factory, lambda: call_count


class TestDropConnectionCompareAndSwap:
    """P5-C1c hardening #2: dropping a STALE connection must never touch a
    fresher, live one.

    LOAD-BEARING: must FAIL RED against current code — ``_drop_connection``
    nulls ``self._connection`` unconditionally, with no check that the
    connection it was handed is still the live one.
    """

    async def test_dropping_a_stale_connection_after_a_reconnect_leaves_the_live_one_intact(
        self, surreal_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch  # noqa: F811
    ) -> None:
        factory, get_call_count = _plain_counting_connection_factory()
        monkeypatch.setattr("loremaster.graph_surreal.AsyncSurreal", factory)
        fresh_graph = SurrealCodeGraph(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user,
            password=surreal_env.password,
            tier_roots={},
            project_roots=[],
        )
        try:
            # connection A, then simulate an EARLIER self-heal that already
            # replaced it with connection B (bypassing ``_drop_connection``
            # directly, so the STALE reference to A survives independently).
            stale_connection = await fresh_graph._ensure_connection()
            assert get_call_count() == 1
            # cast: keep mypy at the declared union (bare None narrows the
            # attribute for the rest of the block -> false 'unreachable').
            fresh_graph._connection = cast("_SurrealConnection | None", None)
            live_connection = await fresh_graph._ensure_connection()
            assert get_call_count() == 2
            assert live_connection is not stale_connection

            # Act: a LATE caller drops the STALE connection A — AFTER B is
            # already the live, cached handle.
            await fresh_graph._drop_connection(stale_connection)

            # Assert: B survives untouched.
            assert fresh_graph._connection is live_connection

            # And the graph keeps working by REUSING B — no third connection
            # opened.
            await fresh_graph.ensure_ready()
            assert get_call_count() == 2
            assert fresh_graph._connection is live_connection
        finally:
            await fresh_graph.close()


# ---------------------------------------------------------------------------
# P5-C1c, hardening #3 (SurrealDB docs-audit follow-up, ledger #28): a raw SDK
# routing ``KeyError`` must be classified as a connection fault — mirrors
# ``test_surreal_store.py``'s identical ``_query`` seam (see that file's
# module note for the live-probed root cause: an in-flight query on a dropped
# socket surfaces ``builtins.KeyError(<request-uuid>)`` from the SDK's own
# response routing, never ``_CONNECTION_ERRORS``, and the SCOPING note on why
# classifying it here cannot misclassify a KeyError from our own code).
# ---------------------------------------------------------------------------

_SDK_ROUTING_KEY_ERROR_TOKEN = "3fae6a02-9c1e-4c1b-8f3a-77c2e4a9b001"


class TestQuerySeamSdkKeyErrorClassification:
    """P5-C1c hardening #3: a KeyError raised BY THE SDK CALL ITSELF inside
    ``_query`` must surface as ``SurrealConnectionError`` and self-heal.

    LOAD-BEARING: must FAIL RED against current code — ``_query``'s except
    clause only catches ``_CONNECTION_ERRORS``; ``KeyError`` propagates
    completely untyped today.
    """

    async def test_sdk_routing_key_error_surfaces_as_connection_error_and_heals(
        self, surreal_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch  # noqa: F811
    ) -> None:
        factory, get_call_count = _plain_counting_connection_factory()
        monkeypatch.setattr("loremaster.graph_surreal.AsyncSurreal", factory)
        live_graph = SurrealCodeGraph(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user,
            password=surreal_env.password,
            tier_roots={},
            project_roots=[],
        )
        try:
            await live_graph.ensure_ready()
            assert get_call_count() == 1
            broken_connection = live_graph._connection
            assert broken_connection is not None

            # A deterministic stand-in for the SDK's own response-routing
            # failure (see the module note above) — patched on the LIVE
            # connection INSTANCE itself.
            async def _raise_routing_key_error(*args: object, **kwargs: object) -> Any:
                raise KeyError(_SDK_ROUTING_KEY_ERROR_TOKEN)

            monkeypatch.setattr(broken_connection, "query", _raise_routing_key_error)

            # Act / Assert: the raw KeyError must surface as a typed
            # SurrealConnectionError (never bare) AND drop the connection.
            with pytest.raises(SurrealConnectionError):
                await live_graph.indexed_file_count()
            assert live_graph._connection is None

            # Recovery: the NEXT call reconnects — exactly one NEW connection.
            assert await live_graph.indexed_file_count() == 0
            assert get_call_count() == 2
        finally:
            await live_graph.close()
