"""Contract tests for P8b (ledger #diff): ``loremaster.diff`` — the diff engine
over P5 snapshots.

Versioning is first-class in v1.0: a ``snapshot`` row is a full-project index
GENERATION marker whose ``snapshot_entry`` children carry the per-file
sha512 + per-chunk identity/digest ledger (written by
:class:`~loremaster.index.snapshots.SnapshotStamper`, pinned in
``test_snapshots.py``). THIS file pins the READER layer ABOVE that ledger — the
engine that answers "what changed between snapshot X and snapshot Y (or the live
'now' state)?" at BOTH file granularity (added / removed / modified by sha512)
and function granularity (per-file chunk identity → hash add / remove / change).

THE PINNED PUBLIC API SURFACE (named here, blind to any implementation)
-----------------------------------------------------------------------
``loremaster.diff``::

    class DiffEngine:
        def __init__(
            self, *, url: str, namespace: str, database: str, user: str,
            password: str, store: SurrealStore, manifest: SurrealManifest,
        ) -> None: ...

        async def ensure_ready(self) -> None: ...
        async def close(self) -> None: ...

        async def list_snapshots(self, limit: int = 20) -> list[SnapshotSummary]:
            # Newest-first by created_at (then id, deterministic). `limit` is a
            # REQUIRED bound clamped to [1, _MAX_LIST_LIMIT]. Empty store ⇒ [].

        async def diff(self, since: str, until: str | None = None) -> DiffResult:
            # `since`/`until` are snapshot id strings exactly as
            # SnapshotStamper.stamp / list_snapshots return them
            # ("snapshot:sn<hex>"). until=None ⇒ the CURRENT live state
            # (manifest indexed rows for file-level; store.scroll of CHANGED
            # files only for function-level). Unknown/malformed id ⇒
            # SnapshotNotFoundError. Store down ⇒ SurrealConnectionError.

Lifecycle convention: like its sibling ports (``SurrealStore`` /
``SurrealManifest`` / ``SurrealCodeGraph`` / ``SnapshotStamper``),
``DiffEngine`` owns its OWN connection (same
``url``/``namespace``/``database``/``user``/``password`` construction), exposed
at ``self._connection`` for the same mid-life-drop self-heal contract those
already have.

RED STRATEGY
------------
``loremaster.diff`` does not exist yet, so the import below is guarded (mirrors
``test_snapshots.py``'s pattern for a brand-new top-level API): the file
COLLECTS, and every test that actually exercises the missing API fails on ITS
OWN behaviour (calling ``None(...)`` raises ``TypeError``) rather than one
collection error hiding the whole contract. Every non-pure test runs against the
REAL 3.1.5 dev server (``_surreal_harness`` per-test DB isolation), building real
snapshots via :class:`SnapshotStamper` and asserting the diff.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    TIER_A,
    SurrealEnv,
    call_until_recovered,
    chunk_record,
    connect_admin,
    run,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
    unit_vector,
)
from loremaster.index.records import sha512_hex
from loremaster.index.snapshots import SnapshotStamper
from loremaster.index.surreal_manifest import STATE_DIRTY, STATE_INDEXED, SurrealManifest
from loremaster.store.surreal import (
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    SurrealStore,
    SurrealStoreError,
    _SurrealConnection,
)
from surrealdb.errors import ErrorKind, ServerError

try:
    from loremaster.diff import (
        DiffEngine,
        DiffResult,
        FileRef,
        FunctionDelta,
        SnapshotNotFoundError,
        SnapshotSummary,
    )

    _DIFF_API_AVAILABLE = True
except ImportError:  # pragma: no cover - pre-P8b RED: the module does not exist
    _DIFF_API_AVAILABLE = False
    DiffEngine = None  # type: ignore[assignment,misc]
    DiffResult = None  # type: ignore[assignment,misc]
    FileRef = None  # type: ignore[assignment,misc]
    FunctionDelta = None  # type: ignore[assignment,misc]
    SnapshotNotFoundError = None  # type: ignore[assignment,misc]
    SnapshotSummary = None  # type: ignore[assignment,misc]


_DIM = PRODUCTION_DIM
_TIER = TIER_A

# The self-heal error vocabulary a healthy, self-healing port may surface across
# a mid-life socket drop — mirrors ``test_snapshots.py``'s identical set.
_HEALABLE_ERRORS: tuple[type[BaseException], ...] = (SurrealStoreError, *_CONNECTION_ERRORS)

# A port with nothing listening — the "server is down" adversary (the SAME dead
# port ``test_snapshots.py`` / ``test_surreal_store.py`` use for this).
_DEAD_URL = "ws://127.0.0.1:19555/rpc"

# A synthetic ASSERT rejection carrying a value that must NEVER reach the raised
# message (mirrors ``test_snapshots.py``'s ``_SNAPSHOT_SENSITIVE_*``).
_DIFF_SENSITIVE_MARKER = "TOP-SECRET-DIFF-BOUND-VALUE-9f3e2a"
_DIFF_SENSITIVE_ENGINE_TEXT = (
    f"Found '{_DIFF_SENSITIVE_MARKER}' for field `sha512`, with record "
    f"`snapshot_entry:abc123`, but field must conform to: $value != NONE"
)
# The transport-``kind`` rejection the SDK raises when a mid-life socket drop left
# the reconnected session unauthenticated (``NotAllowed``) — a transport fault.
_DIFF_TRANSPORT_ENGINE_TEXT = "Anonymous access to the diff query is not allowed"


# ===========================================================================
# File / chunk source fixtures — distinct source texts so each chunk's
# content_hash is genuinely distinguishable (a real per-chunk fidelity check).
# ===========================================================================

_ORDER_PATH = "src/order_service.py"
_PRICING_PATH = "src/pricing.py"
_INVENTORY_PATH = "src/inventory.py"

_MARGIN_V1 = "def compute_margin(cost, price):\n    return price - cost\n"
_MARGIN_V2 = "def compute_margin(cost, price):\n    return round(price - cost, 2)\n"
_DISCOUNT = "def compute_discount(price, rate):\n    return price * (1 - rate)\n"
_CONFIRM = 'def confirm(self, order):\n    order.state = "purchase"\n    return order\n'
_CANCEL = 'def cancel(self, order):\n    order.state = "cancel"\n    return order\n'
_REORDER = "def reorder(product, qty):\n    return qty * 2\n"

# One chunk.
_PRICING_A: dict[str, str] = {"compute_margin": _MARGIN_V1}
# compute_margin body CHANGED + a NEW compute_discount chunk.
_PRICING_B: dict[str, str] = {"compute_margin": _MARGIN_V2, "compute_discount": _DISCOUNT}

_ORDER_CHUNKS: dict[str, str] = {"confirm": _CONFIRM, "cancel": _CANCEL}
_INVENTORY_CHUNKS: dict[str, str] = {"reorder": _REORDER}


def _source_of(chunk_sources: Mapping[str, str]) -> str:
    """The concatenated file text for a chunk-source map (drives its sha512)."""
    return "".join(chunk_sources.values())


# ===========================================================================
# Test helpers — mirror ``test_snapshots.py``'s live-harness write idiom.
# ===========================================================================


async def _write_chunk_rows(
    store: SurrealStore,
    *,
    tier: str,
    file_path: str,
    chunk_sources: Mapping[str, str],
    dim: int,
) -> None:
    """Write one REAL chunk row per ``(identity, source_text)`` pair for
    ``(tier, file_path)`` — replaces any prior rows under it (the store's own
    replace-fragment semantics), mirroring ``test_snapshots.py``.
    """
    records_with_vectors = [
        (
            chunk_record(
                tier=tier,
                file_path=file_path,
                identity=identity,
                ident_text=identity,
                source_text=source_text,
            ),
            unit_vector(axis=index % dim, dim=dim),
        )
        for index, (identity, source_text) in enumerate(chunk_sources.items())
    ]
    fragment = store.replace_file_fragment(tier, file_path, records_with_vectors)
    await store.apply([fragment])


async def _upsert_manifest_row(
    manifest: SurrealManifest,
    *,
    tier: str,
    file_path: str,
    source: str,
    n_chunks: int,
) -> str:
    """Upsert an ``indexed`` manifest row for ``(tier, file_path)``; returns its sha512."""
    sha512 = sha512_hex(source)
    await manifest.upsert(
        tier=tier,
        file_path=file_path,
        sha512=sha512,
        mtime_ns=1_751_000_000_000_000_000,
        size=len(source.encode("utf-8")),
        n_chunks=n_chunks,
        chunk_ids=[f"chunk_{i}" for i in range(n_chunks)],
        state=STATE_INDEXED,
    )
    return sha512


async def _index_file(
    bench: _DiffBench,
    *,
    file_path: str,
    chunk_sources: Mapping[str, str],
    source_override: str | None = None,
) -> str:
    """Write chunks + upsert a manifest row for one file; returns its sha512.

    ``source_override`` decouples the manifest sha512 from the chunk sources — a
    deliberate synthetic that lets a test build the belt-and-braces case
    (identical sha512, different chunk_hashes) the deterministic chunker could
    never produce on its own.
    """
    await _write_chunk_rows(
        bench.store, tier=_TIER, file_path=file_path, chunk_sources=chunk_sources, dim=_DIM
    )
    source = source_override if source_override is not None else _source_of(chunk_sources)
    return await _upsert_manifest_row(
        bench.manifest,
        tier=_TIER,
        file_path=file_path,
        source=source,
        n_chunks=len(chunk_sources),
    )


async def _remove_manifest_file(bench: _DiffBench, *, file_path: str) -> None:
    """Delete a manifest row so a later ``until=now`` state no longer sees it."""
    await bench.manifest.delete(tier=_TIER, file_path=file_path)


def _refs(file_refs: list[Any]) -> set[tuple[str, str]]:
    """Normalise a list of FileRef value objects to a comparable ``{(tier, path)}`` set."""
    return {(ref.tier, ref.file_path) for ref in file_refs}


def _delta_for(result: Any, file_path: str) -> Any:
    """The single FunctionDelta for ``file_path`` in a result (asserts exactly one)."""
    matches = [delta for delta in result.function_deltas if delta.file_path == file_path]
    assert len(matches) == 1, f"expected exactly one function delta for {file_path}"
    return matches[0]


# ===========================================================================
# The bench: a real store + manifest + stamper (to CREATE snapshots) + the
# DiffEngine under test, all on one shared database.
# ===========================================================================


@dataclass
class _DiffBench:
    store: SurrealStore
    manifest: SurrealManifest
    stamper: Any
    engine: Any
    env: SurrealEnv
    project_root: Path


@pytest_asyncio.fixture()
async def diff_bench(
    surreal_env: SurrealEnv,  # noqa: F811 - imported fixture
    tmp_path: Path,
) -> AsyncIterator[_DiffBench]:
    project_root = tmp_path / "project"
    project_root.mkdir()

    store = SurrealStore(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        dim=_DIM,
        user=surreal_env.user,
        password=surreal_env.password,
    )
    manifest = SurrealManifest(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        user=surreal_env.user,
        password=surreal_env.password,
    )
    await store.ensure_ready()
    await manifest.ensure_ready()

    stamper = SnapshotStamper(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        user=surreal_env.user,
        password=surreal_env.password,
        store=store,
        manifest=manifest,
        project_root=project_root,
    )
    engine = DiffEngine(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        user=surreal_env.user,
        password=surreal_env.password,
        store=store,
        manifest=manifest,
    )
    await stamper.ensure_ready()
    await engine.ensure_ready()
    try:
        yield _DiffBench(
            store=store,
            manifest=manifest,
            stamper=stamper,
            engine=engine,
            env=surreal_env,
            project_root=project_root,
        )
    finally:
        await engine.close()
        await stamper.close()
        await store.close()
        await manifest.close()


# ===========================================================================
# list_snapshots
# ===========================================================================


class TestListSnapshots:
    """``list_snapshots`` returns newest-first, bounded, well-typed summaries —
    and an empty store is an empty list, never an error."""

    async def test_empty_store_returns_empty_list(self, diff_bench: _DiffBench) -> None:
        assert await diff_bench.engine.list_snapshots() == []

    async def test_returns_newest_first_with_correct_fields(
        self, diff_bench: _DiffBench
    ) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        first = await diff_bench.stamper.stamp()
        # A second stamp with an extra file — a DIFFERENT files_total to assert on.
        await _index_file(diff_bench, file_path=_ORDER_PATH, chunk_sources=_ORDER_CHUNKS)
        second = await diff_bench.stamper.stamp()

        summaries = await diff_bench.engine.list_snapshots()
        assert [s.id for s in summaries] == [second, first]  # newest first
        assert all(isinstance(s, SnapshotSummary) for s in summaries)

        newest = summaries[0]
        assert newest.id == second
        assert newest.files_total == 2
        assert newest.chunks_total == len(_PRICING_A) + len(_ORDER_CHUNKS)
        # Non-git project_root ⇒ git identity absent, never fabricated.
        assert newest.git_ref is None
        assert newest.git_branch is None
        assert newest.created_at  # a real, non-empty timestamp

    async def test_limit_bounds_the_result_and_clamps_out_of_range(
        self, diff_bench: _DiffBench
    ) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        ids = [await diff_bench.stamper.stamp() for _ in range(3)]

        # An explicit small limit bounds the result to the newest N.
        limited = await diff_bench.engine.list_snapshots(limit=2)
        assert [s.id for s in limited] == [ids[2], ids[1]]

        # A zero/negative limit clamps to the floor (>= 1), never returns empty
        # by accident nor raises.
        clamped = await diff_bench.engine.list_snapshots(limit=0)
        assert len(clamped) == 1
        assert clamped[0].id == ids[2]


class TestCountSnapshots:
    """``count_snapshots`` — the cheap total the P8d Wave 4a listing pagination
    trailer needs (finding #8: the default 20-row listing must say "showing
    N of M", never silently cap without a total to compare against)."""

    async def test_empty_store_is_zero(self, diff_bench: _DiffBench) -> None:
        assert await diff_bench.engine.count_snapshots() == 0

    async def test_counts_every_snapshot_regardless_of_list_limit(
        self, diff_bench: _DiffBench
    ) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        for _ in range(3):
            await diff_bench.stamper.stamp()

        assert await diff_bench.engine.count_snapshots() == 3
        # The count is independent of any list_snapshots limit.
        limited = await diff_bench.engine.list_snapshots(limit=1)
        assert len(limited) == 1
        assert await diff_bench.engine.count_snapshots() == 3


# ===========================================================================
# diff — file level
# ===========================================================================


class TestDiffFileLevel:
    """``diff`` reports added / removed / modified files between two snapshots."""

    async def test_empty_to_populated_marks_every_file_added(
        self, diff_bench: _DiffBench
    ) -> None:
        empty = await diff_bench.stamper.stamp()  # zero indexed files
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        await _index_file(diff_bench, file_path=_ORDER_PATH, chunk_sources=_ORDER_CHUNKS)
        populated = await diff_bench.stamper.stamp()

        result = await diff_bench.engine.diff(empty, populated)
        assert isinstance(result, DiffResult)
        assert _refs(result.added) == {(_TIER, _PRICING_PATH), (_TIER, _ORDER_PATH)}
        assert result.removed == []
        assert result.modified == []

    async def test_modify_one_file_is_reported_modified(
        self, diff_bench: _DiffBench
    ) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        await _index_file(diff_bench, file_path=_ORDER_PATH, chunk_sources=_ORDER_CHUNKS)
        before = await diff_bench.stamper.stamp()

        # Only pricing changes; order_service is byte-identical.
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_B)
        after = await diff_bench.stamper.stamp()

        result = await diff_bench.engine.diff(before, after)
        assert _refs(result.modified) == {(_TIER, _PRICING_PATH)}
        assert result.added == []
        assert result.removed == []

    async def test_deleted_file_is_reported_removed(self, diff_bench: _DiffBench) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        await _index_file(diff_bench, file_path=_ORDER_PATH, chunk_sources=_ORDER_CHUNKS)
        before = await diff_bench.stamper.stamp()

        await _remove_manifest_file(diff_bench, file_path=_ORDER_PATH)
        after = await diff_bench.stamper.stamp()

        result = await diff_bench.engine.diff(before, after)
        assert _refs(result.removed) == {(_TIER, _ORDER_PATH)}
        assert result.added == []
        assert result.modified == []


# ===========================================================================
# diff — function level
# ===========================================================================


class TestDiffFunctionLevel:
    """For each modified file, ``diff`` compares chunk identity → hash maps:
    identities added / removed / changed."""

    async def test_added_changed_and_removed_identities_within_one_file(
        self, diff_bench: _DiffBench
    ) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        before = await diff_bench.stamper.stamp()

        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_B)
        after = await diff_bench.stamper.stamp()

        result = await diff_bench.engine.diff(before, after)
        delta = _delta_for(result, _PRICING_PATH)
        # compute_discount is brand new; compute_margin kept its identity but its
        # body (hash) changed; nothing was removed.
        assert delta.added == ["compute_discount"]
        assert delta.changed == ["compute_margin"]
        assert delta.removed == []

    async def test_removed_identity_within_one_file(self, diff_bench: _DiffBench) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_B)
        before = await diff_bench.stamper.stamp()

        # Drop compute_discount, restore compute_margin's v1 body (a change too).
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        after = await diff_bench.stamper.stamp()

        result = await diff_bench.engine.diff(before, after)
        delta = _delta_for(result, _PRICING_PATH)
        assert delta.removed == ["compute_discount"]
        assert delta.changed == ["compute_margin"]
        assert delta.added == []


# ===========================================================================
# diff — until=now (live state)
# ===========================================================================


class TestDiffUntilNow:
    """``until=None`` diffs a snapshot against the CURRENT live state, reading
    chunk identities ONLY for files whose sha512 changed (read-efficiency)."""

    async def test_diff_against_live_now_reflects_manifest_and_store_changes(
        self, diff_bench: _DiffBench
    ) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        await _index_file(diff_bench, file_path=_ORDER_PATH, chunk_sources=_ORDER_CHUNKS)
        baseline = await diff_bench.stamper.stamp()

        # Live mutations, NO new snapshot: modify pricing, add inventory, drop order.
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_B)
        await _index_file(diff_bench, file_path=_INVENTORY_PATH, chunk_sources=_INVENTORY_CHUNKS)
        await _remove_manifest_file(diff_bench, file_path=_ORDER_PATH)

        result = await diff_bench.engine.diff(baseline, None)
        assert result.until is None
        assert _refs(result.added) == {(_TIER, _INVENTORY_PATH)}
        assert _refs(result.removed) == {(_TIER, _ORDER_PATH)}
        assert _refs(result.modified) == {(_TIER, _PRICING_PATH)}
        delta = _delta_for(result, _PRICING_PATH)
        assert delta.added == ["compute_discount"]
        assert delta.changed == ["compute_margin"]

    async def test_only_changed_files_are_scrolled_from_the_store(
        self, diff_bench: _DiffBench, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Three indexed files in the baseline snapshot.
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        await _index_file(diff_bench, file_path=_ORDER_PATH, chunk_sources=_ORDER_CHUNKS)
        await _index_file(diff_bench, file_path=_INVENTORY_PATH, chunk_sources=_INVENTORY_CHUNKS)
        baseline = await diff_bench.stamper.stamp()

        # Change exactly ONE file; the other two are byte-identical.
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_B)

        # Spy on the store's scroll: it must fire ONCE (the single changed file),
        # never once-per-indexed-file (that would be a wasteful near-full scan).
        original_scroll = diff_bench.store.scroll
        calls: list[dict[str, str]] = []

        async def _counting_scroll(filters: dict[str, str], limit: int) -> Any:
            calls.append(filters)
            return await original_scroll(filters, limit)

        monkeypatch.setattr(diff_bench.store, "scroll", _counting_scroll)

        result = await diff_bench.engine.diff(baseline, None)
        assert _refs(result.modified) == {(_TIER, _PRICING_PATH)}
        assert len(calls) == 1
        assert calls[0]["file_path"] == _PRICING_PATH


# ===========================================================================
# diff — degenerate / edge cases
# ===========================================================================


class TestDiffEdgeCases:
    """Degenerate inputs produce well-formed, documented results — never a crash
    nor a silently-wrong answer."""

    async def test_since_equals_until_is_a_well_formed_empty_diff(
        self, diff_bench: _DiffBench
    ) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        only = await diff_bench.stamper.stamp()

        result = await diff_bench.engine.diff(only, only)
        assert result.added == []
        assert result.removed == []
        assert result.modified == []
        assert result.function_deltas == []

    async def test_reversed_order_computes_literally_from_since_to_until(
        self, diff_bench: _DiffBench
    ) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        older = await diff_bench.stamper.stamp()
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_B)
        newer = await diff_bench.stamper.stamp()

        # since=newer, until=older — direction is literal, NOT reordered: what was
        # added going forward reads as removed going back.
        result = await diff_bench.engine.diff(newer, older)
        assert _refs(result.modified) == {(_TIER, _PRICING_PATH)}
        delta = _delta_for(result, _PRICING_PATH)
        assert delta.removed == ["compute_discount"]  # present in `since`, gone in `until`
        assert delta.changed == ["compute_margin"]
        assert delta.added == []

    async def test_same_sha512_but_different_chunks_is_surfaced_as_function_modified(
        self, diff_bench: _DiffBench
    ) -> None:
        # Belt-and-braces (contract item 3): DECOUPLE the manifest sha512 from the
        # store chunks so both snapshots record an IDENTICAL sha512 for the file
        # while their chunk_hashes genuinely differ — a state a deterministic
        # chunker never produces, but one a chunker-version change between
        # generations could. The CHOSEN behaviour: surface it at function level
        # even though sha512 is unchanged (never silently hide a chunk drift).
        frozen_source = "# a fixed file body whose sha512 must not move\n"
        await _index_file(
            diff_bench,
            file_path=_PRICING_PATH,
            chunk_sources=_PRICING_A,
            source_override=frozen_source,
        )
        before = await diff_bench.stamper.stamp()
        await _index_file(
            diff_bench,
            file_path=_PRICING_PATH,
            chunk_sources=_PRICING_B,
            source_override=frozen_source,
        )
        after = await diff_bench.engine.diff(before, await diff_bench.stamper.stamp())

        # sha512 is identical ⇒ NOT file-level modified …
        assert after.modified == []
        # … but the chunk drift IS surfaced at function level.
        delta = _delta_for(after, _PRICING_PATH)
        assert delta.added == ["compute_discount"]
        assert delta.changed == ["compute_margin"]


# ===========================================================================
# diff — not-found / malformed ids
# ===========================================================================


class TestDiffUnknownAndMalformedIds:
    """An id that resolves to no snapshot — whether well-formed-but-unknown or
    outright malformed — is a clean, typed :class:`SnapshotNotFoundError` naming
    the id and teaching the next step; a raw SDK ``InvalidRecordIdError`` must
    never escape."""

    async def test_unknown_since_id_raises_named_not_found(
        self, diff_bench: _DiffBench
    ) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        real = await diff_bench.stamper.stamp()
        bogus = "snapshot:definitely_never_created"

        with pytest.raises(SnapshotNotFoundError) as exc_info:
            await diff_bench.engine.diff(bogus, real)
        message = str(exc_info.value)
        assert bogus in message
        assert "list_snapshots" in message

    async def test_unknown_until_id_raises_named_not_found(
        self, diff_bench: _DiffBench
    ) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        real = await diff_bench.stamper.stamp()
        bogus = "snapshot:also_never_created"

        with pytest.raises(SnapshotNotFoundError) as exc_info:
            await diff_bench.engine.diff(real, bogus)
        assert bogus in str(exc_info.value)

    async def test_malformed_id_raises_not_found_not_a_raw_sdk_error(
        self, diff_bench: _DiffBench
    ) -> None:
        malformed = "this is not a valid record id!!!"
        # The SAME clean error family — a raw ``InvalidRecordIdError`` must not leak.
        with pytest.raises(SnapshotNotFoundError):
            await diff_bench.engine.diff(malformed)


# ===========================================================================
# Lifecycle — degradation → recovery (CLAUDE.md) + connection-down loudness.
# ===========================================================================


class TestDiffConnectionLifecycle:
    """The DiffEngine owns its OWN connection with the SAME mid-life-drop
    self-heal + loud-when-down contract as every sibling port."""

    async def test_list_snapshots_recovers_from_a_mid_life_socket_drop(
        self, diff_bench: _DiffBench
    ) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        await diff_bench.stamper.stamp()

        first = await diff_bench.engine.list_snapshots()
        assert first  # baseline: healthy

        # Degradation: kill the engine's OWN underlying socket.
        connection = diff_bench.engine._connection
        assert connection is not None, "expected an established connection to kill"
        await connection.close()

        # Recovery: heal within a bounded number of calls (never wedge).
        recovered = await call_until_recovered(
            diff_bench.engine.list_snapshots, _HEALABLE_ERRORS, label="diff_engine"
        )
        assert [s.id for s in recovered] == [s.id for s in first]

    async def test_diff_against_a_dead_server_raises_connection_error(self) -> None:
        store = SurrealStore(
            url=_DEAD_URL, namespace="ns", database="db", dim=PRODUCTION_DIM,
            user="root", password="root",
        )
        manifest = SurrealManifest(
            url=_DEAD_URL, namespace="ns", database="db", user="root", password="root",
        )
        engine = DiffEngine(
            url=_DEAD_URL, namespace="ns", database="db",
            user="root", password="root", store=store, manifest=manifest,
        )
        with pytest.raises(SurrealConnectionError):
            await engine.list_snapshots()


# ===========================================================================
# The single-statement ``_query`` seam's classified-error posture (ledger #31 /
# b262ab4) — mirrors ``test_snapshots.py``'s ``TestQueryClassifiedErrorPosture``.
# ===========================================================================


@dataclass
class _RejectingConnection:
    """A fake SDK connection whose ``query`` raises a scripted error — the seam
    fault-injector for ``_query``'s classified-error posture. ``close`` is a
    tolerant no-op so an engine holding this handle still tears down cleanly.
    """

    error: BaseException

    async def query(self, statement: str, params: dict[str, Any]) -> Any:
        raise self.error

    async def close(self) -> None:
        return None


class TestQueryClassifiedErrorPosture:
    """A DOMAIN rejection keeps the healthy connection and raises a
    ``SurrealStoreError`` naming a generic engine CLASS + a server-log hint,
    NEVER the raw engine text; a TRANSPORT fault self-heals (drops the handle)
    and raises ``SurrealConnectionError``."""

    @staticmethod
    def _engine_rejecting_with(error: BaseException) -> DiffEngine:
        store = SurrealStore(
            url=_DEAD_URL, namespace="ns", database="db", dim=PRODUCTION_DIM,
            user="root", password="root",
        )
        manifest = SurrealManifest(
            url=_DEAD_URL, namespace="ns", database="db", user="root", password="root",
        )
        engine = DiffEngine(
            url=_DEAD_URL, namespace="ns", database="db",
            user="root", password="root", store=store, manifest=manifest,
        )
        engine._connection = cast("_SurrealConnection", _RejectingConnection(error=error))
        return engine

    async def test_domain_rejection_message_never_echoes_the_raw_engine_text(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        engine = self._engine_rejecting_with(
            ServerError(ErrorKind.INTERNAL, _DIFF_SENSITIVE_ENGINE_TEXT)
        )
        connection_before = engine._connection
        with caplog.at_level(logging.ERROR, logger="loremaster.diff"):
            with pytest.raises(SurrealStoreError) as exc_info:
                await engine._query("SELECT * FROM snapshot")

        message = str(exc_info.value)
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert engine._connection is connection_before  # healthy connection kept
        assert _DIFF_SENSITIVE_ENGINE_TEXT not in message
        assert _DIFF_SENSITIVE_MARKER not in message
        assert "assert violation" in message.lower()
        assert "server log" in message.lower()
        error_records = [record for record in caplog.records if record.levelno == logging.ERROR]
        assert error_records, "the full engine detail must be logged server-side"
        logged = " ".join(
            str(value)
            for value in (
                error_records[0].getMessage(),
                getattr(error_records[0], "engine_error", ""),
            )
        )
        assert _DIFF_SENSITIVE_MARKER in logged

    async def test_transport_failure_drops_the_handle_and_raises_connection_error(
        self,
    ) -> None:
        engine = self._engine_rejecting_with(
            ServerError(ErrorKind.NOT_ALLOWED, _DIFF_TRANSPORT_ENGINE_TEXT)
        )
        with pytest.raises(SurrealConnectionError):
            await engine._query("SELECT * FROM snapshot")
        assert engine._connection is None  # the dead handle was dropped (self-heal)


# ===========================================================================
# Rendering — counts first, capped per-section lists, explicit elision.
# ===========================================================================


class TestDiffRender:
    """``DiffResult.render()`` gives a summarised human view: counts first, then
    capped per-section lists with an EXPLICIT ``+K more`` elision marker (never a
    silent truncation), function-level grouped under its file."""

    @staticmethod
    def _result(
        *,
        added: list[tuple[str, str]] = [],
        removed: list[tuple[str, str]] = [],
        modified: list[tuple[str, str]] = [],
        function_deltas: list[Any] = [],
    ) -> DiffResult:
        return DiffResult(
            since="snapshot:snAAAA",
            until="snapshot:snBBBB",
            added=[FileRef(tier=t, file_path=p) for t, p in added],
            removed=[FileRef(tier=t, file_path=p) for t, p in removed],
            modified=[FileRef(tier=t, file_path=p) for t, p in modified],
            function_deltas=function_deltas,
        )

    def test_render_leads_with_counts(self) -> None:
        result = self._result(
            added=[("custom", "a.py"), ("custom", "b.py")],
            removed=[("custom", "c.py")],
            modified=[("custom", "d.py")],
        )
        rendered = result.render()
        first_lines = rendered.splitlines()
        assert "snapshot:snAAAA" in first_lines[0]
        assert "snapshot:snBBBB" in first_lines[0]
        # Counts appear before any per-file enumeration.
        counts_line = next(line for line in first_lines if line.startswith("files:"))
        assert "+2" in counts_line and "-1" in counts_line and "~1" in counts_line

    def test_render_elides_explicitly_with_a_plus_k_more_marker(self) -> None:
        many = [("custom", f"file_{i:02d}.py") for i in range(10)]
        result = self._result(added=many)
        rendered = result.render(max_per_section=3)
        # Only 3 of 10 added files are enumerated, and the elision is NAMED.
        assert rendered.count("file_") == 3
        assert "+7 more" in rendered
        assert "max_per_section=3" in rendered

    def test_render_groups_function_changes_under_their_file(self) -> None:
        delta = FunctionDelta(
            tier="custom",
            file_path="src/pricing.py",
            added=["compute_discount"],
            removed=[],
            changed=["compute_margin"],
        )
        result = self._result(
            modified=[("custom", "src/pricing.py")], function_deltas=[delta]
        )
        rendered = result.render()
        assert "src/pricing.py" in rendered
        assert "compute_discount" in rendered
        assert "compute_margin" in rendered


# ===========================================================================
# F1 — same-identity WINDOW siblings must not silently collapse.
# ===========================================================================

_BIG_DOC_PATH = "docs/big_section.md"


async def _write_windows(
    bench: _DiffBench, *, file_path: str, identity: str, window_bodies: list[str]
) -> str:
    """Write ONE identity split into N window siblings (sub_ordinal 0..N-1), each
    with its own body, + an indexed manifest row. Returns the whole-file source.

    This is the shape ``identity`` alone cannot key: markdown/python windowing of
    a large block emits several chunks that SHARE one identity and are told apart
    only by ``sub_ordinal`` (the ``(identity, sub_ordinal)`` natural key).
    """
    records_with_vectors = [
        (
            chunk_record(
                tier=_TIER,
                file_path=file_path,
                identity=identity,
                chunk_type="md_section",
                sub_ordinal=index,
                ident_text=identity,
                source_text=body,
            ),
            unit_vector(axis=index % _DIM, dim=_DIM),
        )
        for index, body in enumerate(window_bodies)
    ]
    fragment = bench.store.replace_file_fragment(_TIER, file_path, records_with_vectors)
    await bench.store.apply([fragment])
    whole = "".join(window_bodies)
    await _upsert_manifest_row(
        bench.manifest, tier=_TIER, file_path=file_path, source=whole, n_chunks=len(window_bodies)
    )
    return whole


class TestDiffSameIdentityWindowSiblings:
    """The headline function-level contract on the ONE input shape the audit's F1
    proved broken: a long function / markdown section split into windows that
    share one ``identity``. A change confined to ONE window must surface at
    function level, NOT collapse last-write-wins into 'no change'."""

    async def test_a_change_in_one_window_of_a_shared_identity_is_not_masked(
        self, diff_bench: _DiffBench
    ) -> None:
        await _write_windows(
            diff_bench,
            file_path=_BIG_DOC_PATH,
            identity="big",
            window_bodies=["WINDOW-0-STABLE", "WINDOW-1-ORIGINAL"],
        )
        before = await diff_bench.stamper.stamp()

        # Change ONLY window 1's body; window 0 is byte-identical.
        await _write_windows(
            diff_bench,
            file_path=_BIG_DOC_PATH,
            identity="big",
            window_bodies=["WINDOW-0-STABLE", "WINDOW-1-REWRITTEN"],
        )
        after = await diff_bench.stamper.stamp()

        result = await diff_bench.engine.diff(before, after)
        # File-level modified fires (whole-file sha512 moved) …
        assert _refs(result.modified) == {(_TIER, _BIG_DOC_PATH)}
        # … AND the window-1 change surfaces at function level (never masked). The
        # window marker names WHICH window changed so the two siblings stay
        # distinguishable in the human view.
        delta = _delta_for(result, _BIG_DOC_PATH)
        assert delta.changed == ["big [window 1]"]
        assert delta.added == []
        assert delta.removed == []

    async def test_single_window_identity_still_renders_as_a_plain_identity(
        self, diff_bench: _DiffBench
    ) -> None:
        # A file whose identities each have a SOLE window (sub_ordinal 0) must NOT
        # grow a window marker — the common case stays legible.
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        before = await diff_bench.stamper.stamp()
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_B)
        after = await diff_bench.stamper.stamp()

        result = await diff_bench.engine.diff(before, after)
        delta = _delta_for(result, _PRICING_PATH)
        assert delta.added == ["compute_discount"]
        assert delta.changed == ["compute_margin"]


# ===========================================================================
# F1 legacy tolerance — a pre-``sub_ordinal`` snapshot_entry (written under the
# old schema) must degrade HONESTLY, never crash, never pretend precision.
# ===========================================================================

# The snapshot / snapshot_entry schema slice AS IT WAS before F1 — no
# ``chunk_hashes[*].sub_ordinal`` field. A row written here lacks the
# disambiguator; the later full DDL adds the field IF NOT EXISTS WITHOUT
# retro-validating this row (live-verified), reproducing a real upgraded DB.
_PRE_SUB_ORDINAL_SNAPSHOT_DDL = """
DEFINE TABLE IF NOT EXISTS snapshot SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS created_at ON snapshot TYPE datetime DEFAULT time::now();
DEFINE FIELD IF NOT EXISTS git_ref ON snapshot TYPE option<string>;
DEFINE FIELD IF NOT EXISTS git_branch ON snapshot TYPE option<string>;
DEFINE FIELD IF NOT EXISTS files_total ON snapshot TYPE int;
DEFINE FIELD IF NOT EXISTS chunks_total ON snapshot TYPE int;
DEFINE TABLE IF NOT EXISTS snapshot_entry SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS snapshot ON snapshot_entry TYPE record<snapshot>;
DEFINE FIELD IF NOT EXISTS tier ON snapshot_entry TYPE string;
DEFINE FIELD IF NOT EXISTS file_path ON snapshot_entry TYPE string;
DEFINE FIELD IF NOT EXISTS sha512 ON snapshot_entry TYPE string;
DEFINE FIELD IF NOT EXISTS chunk_hashes ON snapshot_entry TYPE array<object> FLEXIBLE;
DEFINE FIELD IF NOT EXISTS chunk_hashes[*].identity ON snapshot_entry TYPE string;
DEFINE FIELD IF NOT EXISTS chunk_hashes[*].hash ON snapshot_entry TYPE string;
"""


class TestDiffLegacyEntryTolerance:
    """A snapshot stamped BEFORE F1 has ``chunk_hashes`` without ``sub_ordinal``
    — its window siblings were ALREADY collapsed at write time (unrecoverable).
    A diff touching such an entry must (a) not crash, (b) degrade to per-identity
    comparison for that side, and (c) FLAG the degradation explicitly in the
    result and the render (serve-and-say-so), never silently pretend precision."""

    async def test_legacy_entry_degrades_to_per_identity_and_is_flagged(
        self,
        surreal_env: SurrealEnv,  # noqa: F811 - imported fixture
        tmp_path: Path,
    ) -> None:
        # 1. Under the OLD schema, hand-build a LEGACY snapshot + entry (no
        #    sub_ordinal) — a genuine pre-F1 row.
        admin = await connect_admin(surreal_env)
        legacy_hash = sha512_hex("legacy-body")
        try:
            await run(admin, _PRE_SUB_ORDINAL_SNAPSHOT_DDL)
            await run(
                admin,
                "CREATE type::record('snapshot', $id) SET files_total = 1, chunks_total = 1",
                {"id": "legacy_gen"},
            )
            await run(
                admin,
                "CREATE type::record('snapshot_entry', $id) SET "
                "snapshot = type::record('snapshot', $sid), tier = $tier, "
                "file_path = $path, sha512 = $sha, chunk_hashes = $ch",
                {
                    "id": "legacy_entry",
                    "sid": "legacy_gen",
                    "tier": _TIER,
                    "path": _PRICING_PATH,
                    "sha": legacy_hash,
                    "ch": [{"identity": "compute_margin", "hash": legacy_hash}],
                },
            )
        finally:
            await admin.close()

        # 2. Bring up the real ports; store.ensure_ready applies the FULL DDL,
        #    which ADDS chunk_hashes[*].sub_ordinal IF NOT EXISTS — the legacy row
        #    above survives (no retro-validation) but every NEW write must carry it.
        store = SurrealStore(
            url=surreal_env.url, namespace=surreal_env.namespace,
            database=surreal_env.database, dim=_DIM,
            user=surreal_env.user, password=surreal_env.password,
        )
        manifest = SurrealManifest(
            url=surreal_env.url, namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user, password=surreal_env.password,
        )
        await store.ensure_ready()
        await manifest.ensure_ready()
        stamper = SnapshotStamper(
            url=surreal_env.url, namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user, password=surreal_env.password,
            store=store, manifest=manifest, project_root=tmp_path,
        )
        engine = DiffEngine(
            url=surreal_env.url, namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user, password=surreal_env.password,
            store=store, manifest=manifest,
        )
        await stamper.ensure_ready()
        await engine.ensure_ready()
        bench = _DiffBench(
            store=store, manifest=manifest, stamper=stamper, engine=engine,
            env=surreal_env, project_root=tmp_path,
        )
        try:
            # 3. A MODERN snapshot for the SAME file, compute_margin body changed.
            await _index_file(
                bench, file_path=_PRICING_PATH, chunk_sources={"compute_margin": _MARGIN_V2}
            )
            modern = await stamper.stamp()

            # 4. Diff LEGACY -> MODERN. It must not raise, must flag the file as
            #    legacy-degraded, and must degrade to per-identity precision (the
            #    changed identity carries NO window marker — precision was lost).
            result = await engine.diff("snapshot:legacy_gen", modern)
            assert (_TIER, _PRICING_PATH) in _refs(result.legacy_files)
            delta = _delta_for(result, _PRICING_PATH)
            assert delta.changed == ["compute_margin"]  # per-identity, no "[window N]"

            rendered = result.render()
            assert "legacy" in rendered.lower()  # serve-and-say-so
        finally:
            await engine.close()
            await stamper.close()
            await store.close()
            await manifest.close()


# ===========================================================================
# F2 — a file mid-reindex (dirty/embedding/failed) must NOT read as REMOVED.
# ===========================================================================


class TestDiffInFlightFilesAreExcludedNotRemoved:
    """``until=None`` filters the live view to ``indexed`` rows. A file that is
    merely mid-reindex (``dirty``/``embedding``/``failed``) is NOT a deletion —
    it must be EXCLUDED from the comparison and surfaced explicitly under
    ``in_flight``, never mis-reported as ``removed``."""

    async def test_a_dirty_file_is_reported_in_flight_not_removed(
        self, diff_bench: _DiffBench
    ) -> None:
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        await _index_file(diff_bench, file_path=_ORDER_PATH, chunk_sources=_ORDER_CHUNKS)
        baseline = await diff_bench.stamper.stamp()

        # order_service goes DIRTY (mid-reindex) — NOT deleted, NOT re-indexed.
        await diff_bench.manifest.set_state(
            tier=_TIER, file_path=_ORDER_PATH, state=STATE_DIRTY
        )

        result = await diff_bench.engine.diff(baseline, None)
        # It is NOT a deletion …
        assert not any(ref.file_path == _ORDER_PATH for ref in result.removed)
        # … it is surfaced as in-flight, carrying its transient state.
        in_flight_paths = {(ref.tier, ref.file_path) for ref in result.in_flight}
        assert (_TIER, _ORDER_PATH) in in_flight_paths
        dirty_ref = next(ref for ref in result.in_flight if ref.file_path == _ORDER_PATH)
        assert dirty_ref.state == STATE_DIRTY
        # The render says so, so an operator never mistakes it for a deletion.
        rendered = result.render()
        assert "in-flight" in rendered.lower()

    async def test_a_genuinely_deleted_file_is_still_reported_removed(
        self, diff_bench: _DiffBench
    ) -> None:
        # The guard must not swallow REAL deletions: a manifest row that is GONE
        # (not merely transient) is still a removal.
        await _index_file(diff_bench, file_path=_PRICING_PATH, chunk_sources=_PRICING_A)
        await _index_file(diff_bench, file_path=_ORDER_PATH, chunk_sources=_ORDER_CHUNKS)
        baseline = await diff_bench.stamper.stamp()

        await _remove_manifest_file(diff_bench, file_path=_ORDER_PATH)

        result = await diff_bench.engine.diff(baseline, None)
        assert _refs(result.removed) == {(_TIER, _ORDER_PATH)}
        assert result.in_flight == []


# ===========================================================================
# F3 — the until=None same-sha chunk-drift SKIP must be documented as a
# same-chunker caveat, not asserted as a guarantee.
# ===========================================================================


class TestDiffUntilNowDocumentsTheSameShaSkipCaveat:
    """The ``until=None`` path skips chunk-comparing an unchanged-``sha512`` file
    for efficiency. That is only sound WHILE the chunker is unchanged; a
    lorescribe chunker-version upgrade breaks the premise. The docstrings must
    state that caveat honestly (snapshot↔snapshot stays the fidelity path),
    rather than asserting the skip 'loses no real drift'."""

    def test_live_state_docstring_flags_the_chunker_upgrade_caveat(self) -> None:
        doc = (DiffEngine._live_state.__doc__ or "").lower()
        assert "chunker" in doc
        assert "upgrade" in doc

    def test_module_docstring_points_to_snapshot_comparison_as_the_fidelity_path(
        self,
    ) -> None:
        import loremaster.diff as diff_module

        doc = (diff_module.__doc__ or "").lower()
        assert "chunker" in doc and "upgrade" in doc


# ===========================================================================
# F4 — hostile store-derived strings (identity / path) must be sanitised at the
# render boundary; a newline must not forge a fake section.
# ===========================================================================


class TestDiffRenderSanitisesHostileStrings:
    """Chunk identities and file paths flow from the store straight into the
    multi-line render. An identity bearing a newline could forge a whole fake
    section; a zero-width character could smuggle a hidden payload. Every
    store-derived string is run through the shared render sanitiser so it stays
    one visually-honest line."""

    def test_a_newline_bearing_identity_cannot_forge_a_section(self) -> None:
        evil = "innocent\n  removed:\n    custom:FORGED_FILE.py"
        delta = FunctionDelta(
            tier="custom", file_path="src/x.py", added=[evil], removed=[], changed=[]
        )
        result = DiffResult(
            since="snapshot:snA", until="snapshot:snB",
            added=[], removed=[], modified=[FileRef(tier="custom", file_path="src/x.py")],
            function_deltas=[delta],
        )
        out = result.render()
        # The forged 'removed:' block never materialises as its own line.
        assert "\n  removed:\n" not in out
        # The whole hostile identity collapses onto a SINGLE added-identity line.
        forged_lines = [line for line in out.splitlines() if "FORGED_FILE.py" in line]
        assert len(forged_lines) == 1
        assert forged_lines[0].lstrip().startswith("+")

    def test_a_zero_width_character_in_an_identity_is_collapsed(self) -> None:
        zwsp_identity = "compute\u200bmargin"
        delta = FunctionDelta(
            tier="custom", file_path="s.py", added=[], removed=[], changed=[zwsp_identity]
        )
        result = DiffResult(
            since="a", until="b", added=[], removed=[], modified=[], function_deltas=[delta]
        )
        assert "\u200b" not in result.render()

    def test_a_hostile_file_path_cannot_forge_a_section(self) -> None:
        evil_ref = FileRef(tier="custom", file_path="ok.py\nadded:\n  custom:FAKE.py")
        result = DiffResult(
            since="a", until="b", added=[evil_ref], removed=[], modified=[], function_deltas=[]
        )
        out = result.render()
        assert "\nadded:\n  custom:FAKE.py" not in out
