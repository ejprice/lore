"""Contract tests for ``loremaster.index.surreal_manifest.SurrealManifest``, the
P3 port of ``loremaster.index.manifest.Manifest`` onto the P2 SurrealDB ``file``
table, against the REAL SurrealDB server (see ``_surreal_harness``).

WHAT THIS PINS (mirrors ``tests/test_manifest.py`` — the SQLite Manifest's
existing behavioural contract — modulo the SQLite-specific mechanism tests,
which have no SurrealDB analog and are replaced by the equivalent BEHAVIOURAL
guarantee via the engine's native transaction isolation; see ``TestConcurrent
ReaderSnapshot`` below):

* CRUD round-trips keyed by ``(tier, file_path)``, including ``chunk_ids``.
* C1 — the SAME path under two tiers keeps BOTH rows (composite identity).
* The mtime+size fast-path (``needs_reindex``), tier-scoped.
* ``set_state`` / ``delete`` are tier-scoped, no-op on a missing row.
* ``replace`` is atomic: a mid-op failure leaves the PRIOR row intact — no
  orphan, no gap, and (this is the load-bearing bit — see the module note
  below) the failure must be VISIBLE to the caller, never a silent success.
* A concurrent reader (a second, independent ``SurrealManifest`` on the same
  database) never observes a half-applied ``replace`` — the D10/WAL intent,
  reimplemented on the engine's real transaction isolation instead of a
  SQLite ``PRAGMA``.
* ``meta_get`` / ``meta_set`` round-trip (the schema-fingerprint / rebuild-
  status stamps ``schema.py`` and ``server.py`` read/write today).
* The reconcile surface NOT covered by ``test_manifest.py`` itself but present
  in ``manifest.py``'s public API and used directly by ``server.py``:
  ``expected_chunks``, ``indexed_file_count``, ``reset_tier`` (see the
  ``Extra scope`` note below).
* Resilience: a down/unreachable server RAISES (never a silently-empty
  manifest); a mid-life WS-socket drop self-heals within a bounded number of
  calls (mirrors ``test_surreal_store.py::TestMidLifeConnectionRecovery``).

GROUNDING FINDINGS (from live-server probes run while writing this contract —
see the operator report for the full detail; summarised here since they shape
the test bodies below):

1. **The P2 ``meta`` table has ZERO ``DEFINE FIELD`` statements today**
   (``surreal_schema._STRUCTURAL_TABLES`` — a bare ``SCHEMAFULL`` placeholder).
   Verified live: ``CREATE meta:x SET k='a', v='b'`` raises
   ``InternalError: Found field 'k', but no such field exists for table
   'meta'``. ``TestMeta`` below pins the *behavioural* contract regardless —
   GREEN will require extending the DDL with ``k``/``v`` fields (or an
   equivalent), which is flagged to the operator as necessary P3 scope, not
   assumed away here.
2. **A multi-statement ``BEGIN…COMMIT`` whose LATER statement violates a field
   ``ASSERT`` does not raise a Python exception from ``connection.query()`` —
   it silently returns ``None``**, even though the engine correctly rolled the
   transaction back server-side (confirmed via the lower-level
   ``query_raw()``, whose per-statement result carries ``status: "ERR"``).
   ``TestReplace::test_replace_rolls_back_on_failure_and_the_caller_sees_it``
   is written to force a correct implementation to surface this (it will FAIL
   RED against a naive ``await connection.query(...)`` implementation that
   trusts the absence of a raised exception).
3. **The ``file`` table has NO ``tier``/``file_path`` fields in the DDL** — the
   only place those two values can live is the record id itself, confirmed
   live to work as a composite ``file:[tier, file_path]`` id (UPSERT-idempotent,
   coexisting per tier). This is the origin of the "composite record id"
   design directive in the P3 task and is exercised, not merely assumed.
4. **``chunk_ids`` is typed ``array<string>`` in the landed P2 DDL** — NOT
   ``array<record<chunk>>``. Confirmed both by reading ``surreal_schema.py``
   directly and by the ALREADY-LANDED, ALREADY-PASSING
   ``test_surreal_schema.py::test_file_manifest_probe_round_trips``, which
   asserts ``row["chunk_ids"] == ["c1", "c2", "c3"]`` (bare strings). This
   means there is no record-vs-string *storage* translation to pin; the only
   translation this port must guarantee is that the MANIFEST's public
   ``chunk_ids: list[str]`` field continues to carry exactly the bare uuid5
   ids callers already depend on — ``TestChunkIdsSeam`` pins that at the wire
   level, independent of the DDL's exact field type.

DESIGN DECISIONS THIS FILE MAKES (proposals, not mandates — see the operator
report for the trade-offs):

* ``SurrealManifest`` methods are **all async** (``async def get(...)``, etc.),
  matching ``SurrealStore``'s own fully-async surface and the fact that EVERY
  current production caller (``indexer.py``, ``watcher.py``, ``reconcile.py``,
  ``server.py``) already invokes the manifest from inside an ``async def``.
  This means callers gain an ``await``, not "compiles unchanged" byte-for-byte
  — flagged explicitly, not assumed.
* ``SurrealManifest`` owns its OWN connection (constructed the same way as
  ``SurrealStore``: ``url``/``namespace``/``database``/``user``/``password``),
  rather than being handed the indexer's live ``SurrealStore`` — flagged as a
  trade-off, not decided unilaterally.
* ``SurrealManifest.get()`` (and friends) return the EXISTING
  ``loremaster.index.manifest.FileRow`` pydantic model, not a new duplicate
  value object — same row shape, only the backing store changes.
* Connection/query failures raise the EXISTING ``loremaster.store.surreal``
  exception types (``SurrealConnectionError`` / ``SurrealStoreError``) rather
  than a parallel hierarchy.

Expected until P3 lands: collection ERROR in THIS FILE — ``ModuleNotFoundError:
loremaster.index.surreal_manifest``.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, cast

import pytest
import pytest_asyncio
from _surreal_harness import (
    SLUG,
    TIER_A,
    TIER_B,
    SurrealEnv,
    call_until_recovered,
    connect_admin,
    run,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
)
from loremaster.index.manifest import FileRow
from loremaster.index.records import point_id, sha512_hex
from loremaster.index.surreal_manifest import (
    STATE_DIRTY,
    STATE_EMBEDDING,
    STATE_FAILED,
    STATE_INDEXED,
    SurrealManifest,
)
from loremaster.store.surreal import (
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    SurrealStoreError,
    _SurrealConnection,
)
from loremaster.store.surreal_schema import FILE_STATES, FILE_TABLE, generate_manifest_ddl
from surrealdb import AsyncSurreal as _RealAsyncSurreal
from surrealdb.errors import ErrorKind, ServerError

# A port with nothing listening — the "server is down" adversary (same dead
# port ``test_surreal_store.py`` uses, so a shared firewall/port-reservation
# rule never collides).
_DEAD_URL = "ws://127.0.0.1:19555/rpc"

# Realistic Odoo-style paths (the actual shape of what lore indexes), not
# ``foo.py``/``bar.py``.
_PROBE_PATH = "models/purchase_order.py"
_OTHER_PATH = "models/sale_order.py"
_MD_PATH = "docs/purchase_workflow.md"
_GHOST_PATH = "models/never_indexed.py"

# A real function body — the SAME shape ``_surreal_harness.chunk_record`` uses —
# so the sha512/size fixtures below are computed from real content, not
# hand-typed placeholders.
_SOURCE_BODY = (
    "def action_confirm(self):\n"
    "    for order in self:\n"
    "        order.write({'state': 'purchase'})\n"
    "    return True\n"
)
# A REAL sha512 digest over real content (clause 1) — not a repeated-letter
# stand-in. sha512_hex is the SAME production hashing function staleness
# detection uses (clause 5).
_SHA512 = sha512_hex(_SOURCE_BODY)
_OTHER_SHA512 = sha512_hex(_SOURCE_BODY + "\n# variant\n")
# The real byte size of that body, not an arbitrary round number.
_SIZE = len(_SOURCE_BODY.encode("utf-8"))
# A realistic recent nanosecond-precision mtime (matches the ns precision
# ``records.chunk_to_record``/``chunk_record`` actually stamp).
_MTIME_NS = 1_751_000_000_000_000_000

# An out-of-domain state — NOT one of the four the DDL's ASSERT allows — used
# to trigger a genuine engine-level constraint violation (the realistic
# "poison value" for this schema, in place of the SQLite contract's
# non-JSON-serializable ``object()``, which has no SurrealDB analogue).
_INVALID_STATE = "corrupted"
assert _INVALID_STATE not in FILE_STATES  # guards the poison value's premise


def _chunk_ids(tier: str, file_path: str, count: int) -> list[str]:
    """Real uuid5 point ids from the SAME production scheme (``records.point_id``).

    Matches what the indexer would actually mint for this (tier, file_path) —
    not hand-typed placeholder UUIDs — so the manifest's ``chunk_ids``
    round-trip is pinned against byte-identical, production-shaped ids
    (clause 5: the shared source of truth, not a hand-copied literal).
    """
    return [
        point_id(SLUG, tier, file_path, "python_symbol", f"Symbol{i}.method", i)
        for i in range(count)
    ]


async def _upsert_indexed(manifest: SurrealManifest, **overrides: object) -> None:
    """Upsert a representative, realistic file row in the ``indexed`` state."""
    params: dict[str, object] = {
        "tier": TIER_A,
        "file_path": _PROBE_PATH,
        "sha512": _SHA512,
        "mtime_ns": _MTIME_NS,
        "size": _SIZE,
        "n_chunks": 2,
        "chunk_ids": _chunk_ids(TIER_A, _PROBE_PATH, 2),
        "state": STATE_INDEXED,
    }
    params.update(overrides)
    await manifest.upsert(**params)  # type: ignore[arg-type]


ManifestFactory = Callable[[], Awaitable[SurrealManifest]]


@pytest_asyncio.fixture()
async def manifest(surreal_env: SurrealEnv) -> AsyncIterator[SurrealManifest]:  # noqa: F811
    """A ready ``SurrealManifest`` on a fresh unique database (its OWN connection)."""
    live_manifest = SurrealManifest(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        user=surreal_env.user,
        password=surreal_env.password,
    )
    await live_manifest.ensure_ready()
    try:
        yield live_manifest
    finally:
        await live_manifest.close()


@pytest_asyncio.fixture()
async def two_manifests(surreal_env: SurrealEnv) -> AsyncIterator[ManifestFactory]:  # noqa: F811
    """A factory yielding independent, ready ``SurrealManifest``s on ONE database.

    The concurrent-reader and concurrent-replace tests need a writer and a
    reader (or two writers) on SEPARATE connections observing the same
    database at once.
    """
    created: list[SurrealManifest] = []

    async def make() -> SurrealManifest:
        live_manifest = SurrealManifest(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user,
            password=surreal_env.password,
        )
        await live_manifest.ensure_ready()
        created.append(live_manifest)
        return live_manifest

    try:
        yield make
    finally:
        for live_manifest in created:
            await live_manifest.close()


class TestStateConstants:
    """A drift guard: the manifest's state constants must AGREE with the DDL's
    closed domain (``surreal_schema.FILE_STATES``) — an independent module, so
    this is a real cross-module consistency check, not a tautology."""

    def test_constants_match_the_ddl_asserted_domain(self) -> None:
        assert {STATE_INDEXED, STATE_DIRTY, STATE_EMBEDDING, STATE_FAILED} == set(FILE_STATES)

    def test_constants_are_the_documented_lowercase_strings(self) -> None:
        # The exact spellings production code/DDL already commit to.
        assert STATE_INDEXED == "indexed"
        assert STATE_DIRTY == "dirty"
        assert STATE_EMBEDDING == "embedding"
        assert STATE_FAILED == "failed"


class TestCrud:
    """Basic create/read/delete behaviour, keyed by (tier, file_path)."""

    async def test_get_missing_returns_none(self, manifest: SurrealManifest) -> None:
        assert await manifest.get(TIER_A, "does/not/exist.py") is None

    async def test_upsert_then_get_roundtrips(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest)
        row = await manifest.get(TIER_A, _PROBE_PATH)
        assert row is not None
        assert isinstance(row, FileRow)
        assert row.tier == TIER_A
        assert row.file_path == _PROBE_PATH
        assert row.sha512 == _SHA512
        assert row.mtime_ns == _MTIME_NS
        assert row.size == _SIZE
        assert row.n_chunks == 2
        assert row.chunk_ids == _chunk_ids(TIER_A, _PROBE_PATH, 2)
        assert row.state == STATE_INDEXED
        assert row.updated_at  # truthy — the exact serialization is not pinned

    async def test_upsert_is_idempotent_on_composite_key(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest)
        new_ids = _chunk_ids(TIER_A, _PROBE_PATH, 1)
        await _upsert_indexed(manifest, sha512=_OTHER_SHA512, n_chunks=1, chunk_ids=new_ids)
        row = await manifest.get(TIER_A, _PROBE_PATH)
        assert row is not None
        assert row.sha512 == _OTHER_SHA512
        assert row.n_chunks == 1
        assert row.chunk_ids == new_ids
        # No duplicate row was created for this (tier, path).
        all_rows = await manifest.all_files()
        assert [(item.tier, item.file_path) for item in all_rows] == [(TIER_A, _PROBE_PATH)]

    async def test_delete_removes_only_the_tier_row(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest, tier=TIER_A)
        await _upsert_indexed(manifest, tier=TIER_B)
        await manifest.delete(TIER_A, _PROBE_PATH)
        assert await manifest.get(TIER_A, _PROBE_PATH) is None
        # The other tier's row for the same path survives.
        assert await manifest.get(TIER_B, _PROBE_PATH) is not None

    async def test_delete_missing_is_a_noop(self, manifest: SurrealManifest) -> None:
        await manifest.delete(TIER_A, _GHOST_PATH)  # must not raise

    async def test_all_files_lists_every_row(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest, file_path=_PROBE_PATH)
        await _upsert_indexed(manifest, file_path=_OTHER_PATH, chunk_ids=_chunk_ids(TIER_A, _OTHER_PATH, 2))
        paths = sorted(item.file_path for item in await manifest.all_files())
        assert paths == sorted([_PROBE_PATH, _OTHER_PATH])

    async def test_all_files_empty_initially(self, manifest: SurrealManifest) -> None:
        assert await manifest.all_files() == []


class TestChunkIdsSeam:
    """The producer/consumer seam: callers see the SAME bare uuid5 strings the
    indexer minted, verified at the storage wire level (not just via the
    manifest's own round-trip, which could hide a lossy translation)."""

    async def test_chunk_ids_are_stored_as_a_plain_string_array(
        self, manifest: SurrealManifest, surreal_env: SurrealEnv  # noqa: F811
    ) -> None:
        ids = _chunk_ids(TIER_A, _PROBE_PATH, 3)
        await _upsert_indexed(manifest, n_chunks=3, chunk_ids=ids)

        # A RAW connection on the SAME database, independent of whatever
        # internal representation SurrealManifest uses — pins the wire shape.
        raw = await connect_admin(surreal_env)
        try:
            result = await run(
                raw,
                "SELECT chunk_ids FROM type::record('file', [$tier, $path])",
                {"tier": TIER_A, "path": _PROBE_PATH},
            )
        finally:
            await raw.close()
        assert isinstance(result, list) and len(result) == 1
        stored = result[0]["chunk_ids"]
        assert isinstance(stored, list)
        assert all(isinstance(item, str) for item in stored)
        # Byte-identical to the ids the indexer minted — no record-ref wrapper,
        # no JSON-encoded single string, no re-ordering.
        assert stored == ids

    async def test_zero_chunk_file_round_trips_an_empty_array(
        self, manifest: SurrealManifest
    ) -> None:
        # A real, legitimate case: an empty ``__init__.py`` indexes successfully
        # with zero chunks — not an error state.
        await _upsert_indexed(
            manifest, file_path="models/__init__.py", n_chunks=0, chunk_ids=[], state=STATE_INDEXED
        )
        row = await manifest.get(TIER_A, "models/__init__.py")
        assert row is not None
        assert row.n_chunks == 0
        assert row.chunk_ids == []


class TestTierCoexistence:
    """C1: two tiers' rows for ONE path must coexist (composite identity)."""

    async def test_same_path_two_tiers_keeps_both_rows(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest, tier=TIER_A, sha512=_SHA512)
        await _upsert_indexed(manifest, tier=TIER_B, sha512=_OTHER_SHA512)

        row_custom = await manifest.get(TIER_A, _PROBE_PATH)
        row_community = await manifest.get(TIER_B, _PROBE_PATH)
        assert row_custom is not None and row_community is not None
        # Distinct rows with their own content hashes — neither overwrote the
        # other despite sharing a file_path.
        assert row_custom.sha512 == _SHA512
        assert row_community.sha512 == _OTHER_SHA512
        # Exactly two physical rows exist for this path.
        all_rows = await manifest.all_files()
        assert sum(1 for row in all_rows if row.file_path == _PROBE_PATH) == 2

    async def test_files_for_tier_filters_by_tier(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest, tier=TIER_A, file_path=_PROBE_PATH)
        await _upsert_indexed(
            manifest, tier=TIER_A, file_path=_OTHER_PATH, chunk_ids=_chunk_ids(TIER_A, _OTHER_PATH, 2)
        )
        await _upsert_indexed(manifest, tier=TIER_B, file_path=_PROBE_PATH)
        custom_paths = sorted(item.file_path for item in await manifest.files_for_tier(TIER_A))
        community_paths = sorted(item.file_path for item in await manifest.files_for_tier(TIER_B))
        assert custom_paths == sorted([_PROBE_PATH, _OTHER_PATH])
        assert community_paths == [_PROBE_PATH]


class TestSetState:
    """The tier-scoped state-transition helper."""

    async def test_set_state_updates_only_state(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest)
        await manifest.set_state(TIER_A, _PROBE_PATH, STATE_DIRTY)
        row = await manifest.get(TIER_A, _PROBE_PATH)
        assert row is not None
        assert row.state == STATE_DIRTY
        assert row.sha512 == _SHA512
        assert row.n_chunks == 2

    @pytest.mark.parametrize("state", list(FILE_STATES))
    async def test_all_documented_states_are_accepted(
        self, manifest: SurrealManifest, state: str
    ) -> None:
        await _upsert_indexed(manifest)
        await manifest.set_state(TIER_A, _PROBE_PATH, state)
        row = await manifest.get(TIER_A, _PROBE_PATH)
        assert row is not None
        assert row.state == state

    async def test_out_of_domain_state_is_rejected_loudly(self, manifest: SurrealManifest) -> None:
        # NEW, stronger than the SQLite contract (which had no domain check at
        # the app layer): the DDL's ASSERT gives this for free, and a silent
        # acceptance here would corrupt the lifecycle invariant every reconcile
        # decision depends on.
        #
        # F2 (error-type unification, task #19): this is a SINGLE-statement
        # write (``set_state`` -> one ``UPDATE`` through the bare ``_query``
        # seam). Verified live: today it raises ``SurrealConnectionError``
        # (not ``SurrealStoreError``) and NULLS the healthy connection —
        # ``_query``'s except-branch treats the engine's ASSERT-rejection
        # ``SurrealError`` exactly like a genuine transport failure. The
        # broad ``pytest.raises(Exception)`` this test used before is
        # precisely what let that drift go unnoticed (an audit finding), so
        # the type is now pinned EXACTLY, and the connection's health is
        # checked too. LOAD-BEARING: this must FAIL RED against current code.
        await _upsert_indexed(manifest)
        connection_before = manifest._connection
        with pytest.raises(SurrealStoreError) as exc_info:
            await manifest.set_state(TIER_A, _PROBE_PATH, _INVALID_STATE)
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        # A healthy connection must never be nulled for a rejection that has
        # nothing to do with the transport.
        assert manifest._connection is connection_before
        row = await manifest.get(TIER_A, _PROBE_PATH)
        assert row is not None
        assert row.state == STATE_INDEXED  # unchanged — the bad write never landed

    async def test_set_state_only_touches_the_named_tier(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest, tier=TIER_A)
        await _upsert_indexed(manifest, tier=TIER_B)
        await manifest.set_state(TIER_A, _PROBE_PATH, STATE_FAILED)
        touched = await manifest.get(TIER_A, _PROBE_PATH)
        untouched = await manifest.get(TIER_B, _PROBE_PATH)
        assert touched is not None and touched.state == STATE_FAILED
        assert untouched is not None and untouched.state == STATE_INDEXED

    async def test_set_state_on_missing_row_is_a_noop(self, manifest: SurrealManifest) -> None:
        await manifest.set_state(TIER_A, _GHOST_PATH, STATE_FAILED)  # must not raise
        assert await manifest.get(TIER_A, _GHOST_PATH) is None


class TestNeedsReindex:
    """The tier-scoped mtime+size fast-path."""

    async def test_unchanged_indexed_file_does_not_need_reindex(
        self, manifest: SurrealManifest
    ) -> None:
        await _upsert_indexed(manifest)
        assert await manifest.needs_reindex(TIER_A, _PROBE_PATH, _MTIME_NS, _SIZE) is False

    async def test_absent_file_needs_reindex(self, manifest: SurrealManifest) -> None:
        assert await manifest.needs_reindex(TIER_A, _GHOST_PATH, _MTIME_NS, _SIZE) is True

    async def test_same_path_other_tier_still_needs_reindex(self, manifest: SurrealManifest) -> None:
        # An indexed row under TIER_A must NOT make TIER_B's copy of the same
        # path look already-indexed — the fast-path is tier-scoped.
        await _upsert_indexed(manifest, tier=TIER_A)
        assert await manifest.needs_reindex(TIER_B, _PROBE_PATH, _MTIME_NS, _SIZE) is True

    async def test_changed_mtime_needs_reindex(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest)
        assert await manifest.needs_reindex(TIER_A, _PROBE_PATH, _MTIME_NS + 1, _SIZE) is True

    async def test_changed_size_needs_reindex(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest)
        assert await manifest.needs_reindex(TIER_A, _PROBE_PATH, _MTIME_NS, _SIZE + 1) is True

    @pytest.mark.parametrize("state", [STATE_DIRTY, STATE_EMBEDDING, STATE_FAILED])
    async def test_non_indexed_state_needs_reindex_even_when_unchanged(
        self, manifest: SurrealManifest, state: str
    ) -> None:
        await _upsert_indexed(manifest, state=state)
        assert await manifest.needs_reindex(TIER_A, _PROBE_PATH, _MTIME_NS, _SIZE) is True


class TestReplace:
    """The atomic, tier-scoped row-swap that leaves no orphan rows."""

    async def test_replace_swaps_the_row_atomically(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest)
        new_ids = _chunk_ids(TIER_A, _PROBE_PATH, 1)
        await manifest.replace(
            tier=TIER_A,
            file_path=_PROBE_PATH,
            sha512=_OTHER_SHA512,
            mtime_ns=_MTIME_NS + 10,
            size=_SIZE + 10,
            n_chunks=1,
            chunk_ids=new_ids,
            state=STATE_INDEXED,
        )
        row = await manifest.get(TIER_A, _PROBE_PATH)
        assert row is not None
        assert row.sha512 == _OTHER_SHA512
        assert row.mtime_ns == _MTIME_NS + 10
        assert row.chunk_ids == new_ids
        all_rows = await manifest.all_files()
        assert sum(
            1 for r in all_rows if r.tier == TIER_A and r.file_path == _PROBE_PATH
        ) == 1

    async def test_replace_inserts_when_absent(self, manifest: SurrealManifest) -> None:
        ids = _chunk_ids(TIER_A, "models/fresh.py", 2)
        await manifest.replace(
            tier=TIER_A,
            file_path="models/fresh.py",
            sha512=_SHA512,
            mtime_ns=_MTIME_NS,
            size=_SIZE,
            n_chunks=2,
            chunk_ids=ids,
            state=STATE_INDEXED,
        )
        row = await manifest.get(TIER_A, "models/fresh.py")
        assert row is not None
        assert row.chunk_ids == ids

    async def test_replace_does_not_touch_other_tier_same_path(
        self, manifest: SurrealManifest
    ) -> None:
        # Replacing TIER_A's row for a path must leave TIER_B's row for the
        # SAME path intact (composite-identity scoping).
        kept_ids = _chunk_ids(TIER_B, _PROBE_PATH, 1)
        await _upsert_indexed(manifest, tier=TIER_B, chunk_ids=kept_ids, n_chunks=1)
        await manifest.replace(
            tier=TIER_A,
            file_path=_PROBE_PATH,
            sha512=_SHA512,
            mtime_ns=_MTIME_NS,
            size=_SIZE,
            n_chunks=1,
            chunk_ids=_chunk_ids(TIER_A, _PROBE_PATH, 1),
            state=STATE_INDEXED,
        )
        kept = await manifest.get(TIER_B, _PROBE_PATH)
        assert kept is not None
        assert kept.chunk_ids == kept_ids

    async def test_replace_rolls_back_on_failure_and_the_caller_sees_it(
        self, manifest: SurrealManifest
    ) -> None:
        # LOAD-BEARING (see grounding finding #2 in the module docstring): a
        # naive implementation that trusts "no Python exception" as success
        # would pass this call silently even though the engine rejected the
        # write and rolled back — this assertion is what forces the
        # implementation to actually surface the per-statement failure.
        #
        # F2 (error-type unification, task #19): this is the MULTI-statement
        # path (``replace`` -> ``_exec_txn``), which already raises the exact
        # ``SurrealStoreError`` and leaves the connection untouched (verified
        # live) — this hardens the assertion from a broad
        # ``pytest.raises(Exception)`` to the PRECISE type, so this test
        # cannot silently regress to the single-statement path's
        # miscategorization bug.
        await _upsert_indexed(manifest)
        connection_before = manifest._connection
        with pytest.raises(SurrealStoreError) as exc_info:
            await manifest.replace(
                tier=TIER_A,
                file_path=_PROBE_PATH,
                sha512=_OTHER_SHA512,
                mtime_ns=_MTIME_NS + 1,
                size=_SIZE + 1,
                n_chunks=1,
                chunk_ids=["poison"],
                state=_INVALID_STATE,  # out-of-domain — the poison
            )
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert manifest._connection is connection_before
        # The PRIOR row survives completely intact — no orphan, no gap.
        row = await manifest.get(TIER_A, _PROBE_PATH)
        assert row is not None
        assert row.sha512 == _SHA512
        assert row.mtime_ns == _MTIME_NS
        assert row.chunk_ids == _chunk_ids(TIER_A, _PROBE_PATH, 2)
        assert row.state == STATE_INDEXED

    async def test_concurrent_replace_yields_one_complete_writer_never_a_hybrid(
        self, two_manifests: ManifestFactory
    ) -> None:
        # Two independent connections replace the SAME (tier, path)
        # concurrently with two internally-consistent payloads; the final row
        # must be entirely ONE writer's content, never a field-level mix.
        first, second = await two_manifests(), await two_manifests()
        await _upsert_indexed(first)

        ids_a = _chunk_ids(TIER_A, _PROBE_PATH, 4)
        ids_b = _chunk_ids(TIER_A, _PROBE_PATH, 7)

        async def replace_a() -> None:
            await first.replace(
                tier=TIER_A,
                file_path=_PROBE_PATH,
                sha512=_SHA512,
                mtime_ns=_MTIME_NS + 100,
                size=100,
                n_chunks=4,
                chunk_ids=ids_a,
                state=STATE_INDEXED,
            )

        async def replace_b() -> None:
            await second.replace(
                tier=TIER_A,
                file_path=_PROBE_PATH,
                sha512=_OTHER_SHA512,
                mtime_ns=_MTIME_NS + 200,
                size=200,
                n_chunks=7,
                chunk_ids=ids_b,
                state=STATE_INDEXED,
            )

        await asyncio.gather(replace_a(), replace_b())

        row = await first.get(TIER_A, _PROBE_PATH)
        assert row is not None
        # Either writer entirely won — a hybrid (e.g. writer A's sha512 with
        # writer B's chunk_ids) would mean the "replace" was not atomic.
        is_a = (row.sha512, row.n_chunks, row.chunk_ids) == (_SHA512, 4, ids_a)
        is_b = (row.sha512, row.n_chunks, row.chunk_ids) == (_OTHER_SHA512, 7, ids_b)
        assert is_a or is_b, f"hybrid/partial state observed: {row!r}"


class TestConcurrentReaderSnapshot:
    """The D10/WAL INTENT, reimplemented on real transaction isolation: a
    concurrent reader never observes a half-applied ``replace``.

    ``test_manifest.py::TestWalMode`` pinned this via a SQLite ``PRAGMA`` +
    hand-timed ``BEGIN IMMEDIATE`` probe — mechanisms with no SurrealDB
    analogue. The BEHAVIOURAL guarantee (readers never see a torn write) is
    preserved here using the engine's own snapshot isolation, mirroring
    ``test_surreal_store.py::TestSnapshotIsolation`` for the chunk table.
    """

    async def test_reader_never_sees_a_partial_replace(
        self, two_manifests: ManifestFactory
    ) -> None:
        writer, reader = await two_manifests(), await two_manifests()
        old_ids = _chunk_ids(TIER_A, _PROBE_PATH, 5)
        await _upsert_indexed(writer, n_chunks=5, chunk_ids=old_ids, sha512=_SHA512)
        new_ids = _chunk_ids(TIER_A, _PROBE_PATH, 9)

        observed: list[tuple[str, int]] = []

        async def read_loop() -> None:
            for _ in range(80):
                row = await reader.get(TIER_A, _PROBE_PATH)
                if row is not None:
                    observed.append((row.sha512, row.n_chunks))
                await asyncio.sleep(0)

        async def write_once() -> None:
            await asyncio.sleep(0.002)
            await writer.replace(
                tier=TIER_A,
                file_path=_PROBE_PATH,
                sha512=_OTHER_SHA512,
                mtime_ns=_MTIME_NS + 1,
                size=_SIZE + 1,
                n_chunks=9,
                chunk_ids=new_ids,
                state=STATE_INDEXED,
            )

        await asyncio.gather(read_loop(), write_once())

        old_state = (_SHA512, 5)
        new_state = (_OTHER_SHA512, 9)
        for snapshot in observed:
            assert snapshot in (old_state, new_state), f"partial file state observed: {snapshot}"
        final = await reader.get(TIER_A, _PROBE_PATH)
        assert final is not None
        assert (final.sha512, final.n_chunks) == new_state


class TestMeta:
    """The auxiliary key/value meta store (schema-fingerprint + rebuild-status
    stamps). See grounding finding #1: GREEN requires extending the DDL's
    ``meta`` table with fields before these can pass against the live engine.
    """

    async def test_meta_get_missing_returns_none(self, manifest: SurrealManifest) -> None:
        assert await manifest.meta_get("tier_version:community") is None

    async def test_meta_set_then_get(self, manifest: SurrealManifest) -> None:
        await manifest.meta_set("tier_version:community", "15.0.20260420")
        assert await manifest.meta_get("tier_version:community") == "15.0.20260420"

    async def test_meta_set_overwrites(self, manifest: SurrealManifest) -> None:
        await manifest.meta_set("tier_version:community", "15.0.20260420")
        await manifest.meta_set("tier_version:community", "15.0.20260501")
        assert await manifest.meta_get("tier_version:community") == "15.0.20260501"

    async def test_meta_keys_are_independent(self, manifest: SurrealManifest) -> None:
        # A realistic pair of real callers' keys (schema.py / server.py use
        # exactly this "namespaced" key shape) must not collide.
        await manifest.meta_set("schema_fingerprint", "sha256:abc123")
        await manifest.meta_set("schema_rebuild_status", "idle")
        assert await manifest.meta_get("schema_fingerprint") == "sha256:abc123"
        assert await manifest.meta_get("schema_rebuild_status") == "idle"


class TestPersistence:
    """Data written by one ``SurrealManifest`` connection is durably visible to
    a FRESH instance against the same (namespace, database) — the networked
    analogue of "survives reopen" (SurrealDB has no local file to reopen; the
    durability boundary is the server, not the client connection)."""

    async def test_data_is_durable_across_manifest_instances(
        self, two_manifests: ManifestFactory
    ) -> None:
        first = await two_manifests()
        await _upsert_indexed(first)
        await first.close()

        second = await two_manifests()
        row = await second.get(TIER_A, _PROBE_PATH)
        assert row is not None
        assert row.chunk_ids == _chunk_ids(TIER_A, _PROBE_PATH, 2)


# ---------------------------------------------------------------------------
# Extra scope: the reconcile surface manifest.py exposes and server.py calls
# directly (``expected_chunks`` / ``indexed_file_count`` / ``reset_tier``) but
# that ``test_manifest.py`` itself does not unit-test (it is only exercised,
# indirectly, inside the large ``test_startup_divergence_reconcile.py``
# integration suite). Flagged to the operator: included here because these are
# part of the manifest's PUBLIC API used by real callers today, and the task
# frames the port as preserving that whole surface — not merely what
# ``test_manifest.py`` happens to cover directly. Grounded in the SPEC the
# ``manifest.py`` docstrings state (the intended invariant), not reverse-
# engineered from behaviour.
# ---------------------------------------------------------------------------


class TestExpectedChunks:
    """The SUM of ``n_chunks`` over ``indexed`` rows only — what a live chunk
    count is compared against to detect a wiped/short or orphan-over-count
    store (FP-02/FP-03)."""

    async def test_sums_n_chunks_over_indexed_rows_only(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(
            manifest, file_path=_PROBE_PATH, n_chunks=3, chunk_ids=_chunk_ids(TIER_A, _PROBE_PATH, 3)
        )
        await _upsert_indexed(
            manifest, file_path=_OTHER_PATH, n_chunks=5, chunk_ids=_chunk_ids(TIER_A, _OTHER_PATH, 5)
        )
        # A dirty row's n_chunks must NOT count — no live points to expect.
        await _upsert_indexed(
            manifest,
            file_path=_MD_PATH,
            n_chunks=10,
            chunk_ids=_chunk_ids(TIER_A, _MD_PATH, 10),
            state=STATE_DIRTY,
        )
        assert await manifest.expected_chunks() == 8  # 3 + 5, NOT +10

    async def test_scopes_to_tier(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(
            manifest, tier=TIER_A, n_chunks=3, chunk_ids=_chunk_ids(TIER_A, _PROBE_PATH, 3)
        )
        await _upsert_indexed(
            manifest, tier=TIER_B, n_chunks=6, chunk_ids=_chunk_ids(TIER_B, _PROBE_PATH, 6)
        )
        assert await manifest.expected_chunks(TIER_A) == 3
        assert await manifest.expected_chunks(TIER_B) == 6
        assert await manifest.expected_chunks() == 9

    async def test_empty_manifest_returns_zero(self, manifest: SurrealManifest) -> None:
        assert await manifest.expected_chunks() == 0
        assert await manifest.expected_chunks(TIER_A) == 0

    async def test_tier_with_only_non_indexed_rows_returns_zero(
        self, manifest: SurrealManifest
    ) -> None:
        # Rows EXIST for the tier, but none are ``indexed`` — a degenerate
        # driver-table case the SUM must not silently miscount.
        await _upsert_indexed(manifest, state=STATE_EMBEDDING, n_chunks=4)
        assert await manifest.expected_chunks(TIER_A) == 0


class TestIndexedFileCount:
    """The COUNT of ``indexed`` rows, optionally tier- and suffix-scoped — the
    manifest's view of "how many files are live" the FP-04 graph check reads."""

    async def test_counts_indexed_rows_only(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest, file_path=_PROBE_PATH)
        await _upsert_indexed(
            manifest, file_path=_OTHER_PATH, chunk_ids=_chunk_ids(TIER_A, _OTHER_PATH, 2)
        )
        await _upsert_indexed(
            manifest,
            file_path=_MD_PATH,
            state=STATE_FAILED,
            chunk_ids=_chunk_ids(TIER_A, _MD_PATH, 2),
        )
        assert await manifest.indexed_file_count() == 2

    async def test_scopes_to_tier(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest, tier=TIER_A)
        await _upsert_indexed(manifest, tier=TIER_B)
        assert await manifest.indexed_file_count(tier=TIER_A) == 1
        assert await manifest.indexed_file_count(tier=TIER_B) == 1
        assert await manifest.indexed_file_count() == 2

    async def test_scopes_to_suffix(self, manifest: SurrealManifest) -> None:
        # A docs-only corpus has a legitimately-empty graph while its Markdown
        # rows are indexed — the suffix filter is what keeps FP-04 honest.
        await _upsert_indexed(manifest, file_path=_PROBE_PATH)
        await _upsert_indexed(
            manifest, file_path=_MD_PATH, chunk_ids=_chunk_ids(TIER_A, _MD_PATH, 2)
        )
        assert await manifest.indexed_file_count(suffix=".py") == 1
        assert await manifest.indexed_file_count(suffix=".md") == 1

    async def test_tier_and_suffix_combine(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest, tier=TIER_A, file_path=_PROBE_PATH)
        await _upsert_indexed(
            manifest, tier=TIER_A, file_path=_MD_PATH, chunk_ids=_chunk_ids(TIER_A, _MD_PATH, 2)
        )
        await _upsert_indexed(manifest, tier=TIER_B, file_path=_PROBE_PATH)
        assert await manifest.indexed_file_count(tier=TIER_A, suffix=".py") == 1

    async def test_no_match_returns_zero(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest, file_path=_PROBE_PATH)
        assert await manifest.indexed_file_count(suffix=".rst") == 0
        assert await manifest.indexed_file_count(tier="nonexistent_tier") == 0


class TestResetTier:
    """The count-driven heal primitive: mark every row for a tier as needing
    re-index WITHOUT discarding its content (the row survives for the re-embed
    to overwrite)."""

    async def test_flips_indexed_rows_to_dirty(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest)
        await manifest.reset_tier(TIER_A)
        row = await manifest.get(TIER_A, _PROBE_PATH)
        assert row is not None
        assert row.state == STATE_DIRTY

    async def test_preserves_chunk_ids_sha512_size(self, manifest: SurrealManifest) -> None:
        ids = _chunk_ids(TIER_A, _PROBE_PATH, 2)
        await _upsert_indexed(manifest, chunk_ids=ids, sha512=_SHA512, size=_SIZE)
        await manifest.reset_tier(TIER_A)
        row = await manifest.get(TIER_A, _PROBE_PATH)
        assert row is not None
        # Only the lifecycle state flips — the content the next sweep would
        # need to compare/overwrite is NOT erased.
        assert row.chunk_ids == ids
        assert row.sha512 == _SHA512
        assert row.size == _SIZE

    async def test_only_touches_named_tier(self, manifest: SurrealManifest) -> None:
        await _upsert_indexed(manifest, tier=TIER_A)
        await _upsert_indexed(manifest, tier=TIER_B)
        await manifest.reset_tier(TIER_A)
        touched = await manifest.get(TIER_A, _PROBE_PATH)
        untouched = await manifest.get(TIER_B, _PROBE_PATH)
        assert touched is not None and touched.state == STATE_DIRTY
        assert untouched is not None and untouched.state == STATE_INDEXED

    async def test_reset_row_needs_reindex_even_with_unchanged_mtime_size(
        self, manifest: SurrealManifest
    ) -> None:
        # The FP-02 fast-path-trap fix: a wiped collection over files whose
        # mtime+size are unchanged would otherwise be fast-path-skipped.
        await _upsert_indexed(manifest, mtime_ns=_MTIME_NS, size=_SIZE)
        assert await manifest.needs_reindex(TIER_A, _PROBE_PATH, _MTIME_NS, _SIZE) is False
        await manifest.reset_tier(TIER_A)
        # SAME mtime/size passed again — must now report True purely because
        # of the state flip, not a file change.
        assert await manifest.needs_reindex(TIER_A, _PROBE_PATH, _MTIME_NS, _SIZE) is True


class TestResilience:
    """Connection failure RAISES a typed error — never a silently-empty manifest
    (the honest-failure discipline every other lore store enforces)."""

    async def test_unreachable_server_raises_on_ensure_ready(
        self, surreal_env: SurrealEnv  # noqa: F811
    ) -> None:
        down_manifest = SurrealManifest(
            url=_DEAD_URL,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user,
            password=surreal_env.password,
        )
        with pytest.raises(SurrealConnectionError):
            await down_manifest.ensure_ready()

    async def test_unreachable_server_raises_on_get_never_returns_none(
        self, surreal_env: SurrealEnv  # noqa: F811
    ) -> None:
        # A ``None`` here would be indistinguishable from "file genuinely not
        # indexed yet" — a down server must be loud, not silently empty.
        down_manifest = SurrealManifest(
            url=_DEAD_URL,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user,
            password=surreal_env.password,
        )
        with pytest.raises(SurrealConnectionError):
            await down_manifest.get(TIER_A, _PROBE_PATH)

    async def test_unreachable_server_raises_on_all_files_never_returns_empty(
        self, surreal_env: SurrealEnv  # noqa: F811
    ) -> None:
        # An empty list here would look identical to "a genuinely fresh,
        # empty manifest" — the same honesty requirement as get().
        down_manifest = SurrealManifest(
            url=_DEAD_URL,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user,
            password=surreal_env.password,
        )
        with pytest.raises(SurrealConnectionError):
            await down_manifest.all_files()

    async def test_bad_auth_raises(self, surreal_env: SurrealEnv) -> None:  # noqa: F811
        bad_manifest = SurrealManifest(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user,
            password="DELIBERATELY-WRONG-PASSWORD",
        )
        with pytest.raises(SurrealConnectionError):
            await bad_manifest.ensure_ready()


# Connection-drop exception classes a mid-life failure may surface as before
# the manifest heals — mirrors ``test_surreal_store.py``'s tolerant probe: the
# manifest's OWN typed wrapper plus the raw transport/SDK errors, so the test
# accepts either a transparent single-call retry OR one surfaced transient
# then a clean reconnect.
_HEALABLE_ERRORS: tuple[type[BaseException], ...] = (SurrealStoreError, *_CONNECTION_ERRORS)


class TestMidLifeConnectionRecovery:
    """A mid-life connection drop must self-heal — degradation → recovery
    (CLAUDE.md). Reuses/mirrors the exact self-heal seam ``SurrealStore``
    already has (see the module docstring's connection-sharing note): whether
    ``SurrealManifest`` implements this via its OWN ``_query`` seam or by
    delegating to a composed ``SurrealStore``-shaped helper, the OBSERVABLE
    contract is identical — the socket dies, the NEXT call transparently
    reconnects rather than wedging forever.
    """

    async def test_get_recovers_from_a_mid_life_socket_drop(
        self, manifest: SurrealManifest
    ) -> None:
        await _upsert_indexed(manifest)
        baseline = await manifest.get(TIER_A, _PROBE_PATH)
        assert baseline is not None  # healthy baseline — connection established

        # Degradation: kill the manifest's underlying WS socket, leaving its
        # cached handle dead (mirrors ``test_surreal_store.py::_kill_socket``).
        connection = manifest._connection
        assert connection is not None, "expected an established connection to kill"
        await connection.close()

        # Recovery: heal within a bounded number of calls (never wedge).
        recovered = await call_until_recovered(
            lambda: manifest.get(TIER_A, _PROBE_PATH), _HEALABLE_ERRORS, label="manifest"
        )
        assert recovered is not None
        assert recovered.sha512 == _SHA512
        # And it STAYS healed — a further call also works.
        again = await manifest.get(TIER_A, _PROBE_PATH)
        assert again is not None

    async def test_replace_recovers_from_a_mid_life_socket_drop(
        self, manifest: SurrealManifest
    ) -> None:
        await _upsert_indexed(manifest)
        connection = manifest._connection
        assert connection is not None
        await connection.close()

        new_ids = _chunk_ids(TIER_A, _PROBE_PATH, 3)

        async def _replace() -> FileRow | None:
            await manifest.replace(
                tier=TIER_A,
                file_path=_PROBE_PATH,
                sha512=_OTHER_SHA512,
                mtime_ns=_MTIME_NS + 5,
                size=_SIZE + 5,
                n_chunks=3,
                chunk_ids=new_ids,
                state=STATE_INDEXED,
            )
            return await manifest.get(TIER_A, _PROBE_PATH)

        recovered = await call_until_recovered(_replace, _HEALABLE_ERRORS, label="manifest")
        assert recovered is not None
        assert recovered.chunk_ids == new_ids


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
    applies ``generate_manifest_ddl()`` via a bare ``connection.query(ddl)``
    call, which inspects only the first statement and swallows a later
    ``ERR`` completely.
    """

    async def test_ensure_ready_raises_on_a_semantically_invalid_late_ddl_statement(
        self, surreal_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch  # noqa: F811
    ) -> None:
        # Arrange: the REAL manifest DDL, poisoned mid-way through.
        real_ddl = generate_manifest_ddl()
        poisoned_ddl = _ddl_with_late_invalid_statement(real_ddl, FILE_TABLE)

        def _poisoned_generate_manifest_ddl() -> str:
            return poisoned_ddl

        monkeypatch.setattr(
            "loremaster.index.surreal_manifest.generate_manifest_ddl",
            _poisoned_generate_manifest_ddl,
        )
        broken_manifest = SurrealManifest(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user,
            password=surreal_env.password,
        )

        try:
            # Act / Assert: a domain/schema rejection — the transport is
            # healthy — must surface as a STORE error, never a silent success.
            with pytest.raises(SurrealStoreError) as exc_info:
                await broken_manifest.ensure_ready()
            assert type(exc_info.value) is SurrealStoreError
            assert not isinstance(exc_info.value, SurrealConnectionError)
            assert broken_manifest._connection is not None
        finally:
            await broken_manifest.close()


# ---------------------------------------------------------------------------
# P5-C1c, hardening #2: ``_drop_connection`` must be a compare-and-swap, not
# an unconditional null — mirrors ``test_surreal_store.py``'s identical
# concern for ``SurrealManifest``'s own connection-lifecycle seam.
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
        monkeypatch.setattr("loremaster.index.surreal_manifest.AsyncSurreal", factory)
        fresh_manifest = SurrealManifest(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user,
            password=surreal_env.password,
        )
        try:
            # connection A, then simulate an EARLIER self-heal that already
            # replaced it with connection B (bypassing ``_drop_connection``
            # directly, so the STALE reference to A survives independently).
            stale_connection = await fresh_manifest._ensure_connection()
            assert get_call_count() == 1
            # cast: keep mypy at the declared union (bare None narrows the
            # attribute for the rest of the block -> false 'unreachable').
            fresh_manifest._connection = cast("_SurrealConnection | None", None)
            live_connection = await fresh_manifest._ensure_connection()
            assert get_call_count() == 2
            assert live_connection is not stale_connection

            # Act: a LATE caller drops the STALE connection A — AFTER B is
            # already the live, cached handle.
            await fresh_manifest._drop_connection(stale_connection)

            # Assert: B survives untouched.
            assert fresh_manifest._connection is live_connection

            # And the manifest keeps working by REUSING B — no third
            # connection opened.
            await fresh_manifest.ensure_ready()
            assert get_call_count() == 2
            assert fresh_manifest._connection is live_connection
        finally:
            await fresh_manifest.close()


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
        monkeypatch.setattr("loremaster.index.surreal_manifest.AsyncSurreal", factory)
        live_manifest = SurrealManifest(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user,
            password=surreal_env.password,
        )
        try:
            await live_manifest.ensure_ready()
            assert get_call_count() == 1
            broken_connection = live_manifest._connection
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
                await live_manifest.all_files()
            assert live_manifest._connection is None

            # Recovery: the NEXT call reconnects — exactly one NEW connection.
            assert await live_manifest.all_files() == []
            assert get_call_count() == 2
        finally:
            await live_manifest.close()


# ===========================================================================
# P8a-5b: the SINGLE-statement ``_query`` seam's classified-error posture
# (follow-up to P8a #7 — ledger #31's launder-the-domain-message posture,
# applied here to close the SECOND of three leak sites hygiene-7 flagged but
# was not authorized to touch: ``store/surreal.py``, ``memory/local.py``, and
# ``tasks.py`` already adopted this exact posture — see ``git show b262ab4``).
#
# ``SurrealManifest._query`` already splits a caught error into transport
# (self-heal + ``SurrealConnectionError``) vs domain (keep the connection +
# ``SurrealStoreError``) — see ``TestResilience`` /
# ``TestQuerySeamSdkKeyErrorClassification`` above. What it did NOT do was
# launder the DOMAIN branch's message: it interpolated the raw ``{error}``
# straight into the raised ``SurrealStoreError``. A domain ``ASSERT``/coercion
# rejection's engine text can echo a bound VALUE back verbatim, and that text
# flows to MCP clients in P8 — this pins the SAME classified posture at this
# seam: the full detail is logged server-side and the raised error carries
# only a CLASSIFIED, generic label + a "see the server log" hint, never the
# raw engine text.
#
# Deterministic and live-server-free: a fake connection raises a scripted
# ``ServerError`` — the identical fault-injection shape
# ``test_surreal_store.py``'s ``TestQueryMessageHygiene`` /
# ``test_memory_backend.py``'s ``TestQueryClassifiedErrorPosture`` use.
# ===========================================================================

# A synthetic ASSERT rejection carrying a value that must NEVER reach the
# raised message (mirrors ``test_surreal_store.py``'s ``_SENSITIVE_ENGINE_TEXT``).
_MANIFEST_SENSITIVE_MARKER = "TOP-SECRET-MANIFEST-BOUND-VALUE-2e6a4f"
_MANIFEST_SENSITIVE_ENGINE_TEXT = (
    f"Found '{_MANIFEST_SENSITIVE_MARKER}' for field `state`, with record "
    f"`file:[community, models/purchase_order.py]`, but field must conform to: "
    f"$value INSIDE ['indexed', 'dirty', 'embedding', 'failed']"
)
# The transport-``kind`` rejection the SDK raises when a mid-life socket drop
# left the reconnected session unauthenticated (``NotAllowed``) — a transport
# fault, never a rejection of the write we sent.
_MANIFEST_TRANSPORT_ENGINE_TEXT = "Anonymous access to the manifest query is not allowed"


@dataclass
class _RejectingConnection:
    """A fake SDK connection whose ``query`` raises a scripted error — the seam
    fault-injector for ``_query``'s classified-error posture. ``close`` is a
    tolerant no-op so a manifest holding this handle still tears down cleanly.
    """

    error: BaseException

    async def query(self, statement: str, params: dict[str, Any]) -> Any:
        raise self.error

    async def close(self) -> None:
        return None


class TestQueryClassifiedErrorPosture:
    """The single-statement ``_query`` seam classifies like ``execute_transaction``
    (ledger #31): a DOMAIN rejection keeps the healthy connection and raises a
    ``SurrealStoreError`` naming a generic engine CLASS + a server-log hint, NEVER
    the raw engine text; a TRANSPORT fault self-heals (drops the handle) and
    raises ``SurrealConnectionError``. Real-only seam test — built inline with an
    injected fake connection (the real engine can't be made to echo a KNOWN
    poison value on demand), mirroring ``test_memory_backend.py``'s
    ``TestQueryClassifiedErrorPosture``.
    """

    @staticmethod
    def _manifest_rejecting_with(error: BaseException) -> SurrealManifest:
        manifest = SurrealManifest(
            url=_DEAD_URL,
            namespace="ns",
            database="db",
            user="root",
            password="root",
        )
        manifest._connection = cast("_SurrealConnection", _RejectingConnection(error=error))
        return manifest

    async def test_domain_rejection_message_never_echoes_the_raw_engine_text(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        manifest = self._manifest_rejecting_with(
            ServerError(ErrorKind.INTERNAL, _MANIFEST_SENSITIVE_ENGINE_TEXT)
        )
        connection_before = manifest._connection
        with caplog.at_level(logging.ERROR, logger="loremaster.index.surreal_manifest"):
            with pytest.raises(SurrealStoreError) as exc_info:
                await manifest._query(
                    f"UPDATE type::record('{FILE_TABLE}', $id) SET state = $state",
                    {"id": [TIER_A, _PROBE_PATH], "state": "poison"},
                )

        message = str(exc_info.value)
        # A domain rejection is a STORE error, not a connection error, and the
        # healthy connection is never thrown away.
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert manifest._connection is connection_before
        # The raw engine text / the value it carries NEVER reaches the message.
        assert _MANIFEST_SENSITIVE_ENGINE_TEXT not in message
        assert _MANIFEST_SENSITIVE_MARKER not in message
        # It DOES carry a classified label + the server-log correlation hint.
        assert "assert violation" in message.lower()
        assert "server log" in message.lower()
        # The FULL engine detail is recoverable server-side (logged before raising).
        error_records = [record for record in caplog.records if record.levelno == logging.ERROR]
        assert error_records, "the full engine detail must be logged server-side"
        logged = " ".join(
            str(value)
            for value in (error_records[0].getMessage(), getattr(error_records[0], "engine_error", ""))
        )
        assert _MANIFEST_SENSITIVE_MARKER in logged

    async def test_transport_failure_drops_the_handle_and_raises_connection_error(self) -> None:
        # The transport branch self-heals: a ``NotAllowed`` (mid-life socket drop
        # reconnected unauthenticated) drops the cached handle so the NEXT call
        # reconnects, and surfaces the connection type — never a raw SDK exception.
        manifest = self._manifest_rejecting_with(
            ServerError(ErrorKind.NOT_ALLOWED, _MANIFEST_TRANSPORT_ENGINE_TEXT)
        )
        with pytest.raises(SurrealConnectionError):
            await manifest._query(f"SELECT * FROM {FILE_TABLE}")
        assert manifest._connection is None  # the dead handle was dropped (self-heal)
