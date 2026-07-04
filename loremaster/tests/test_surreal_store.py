"""Contract tests for ``loremaster.store.surreal.SurrealStore`` + the neutral
``loremaster.store.candidate.Candidate`` value object, against the REAL server.

``SurrealStore`` is the P2 replacement for ``QdrantStore``: one unified store over
a per-project SurrealDB database, exposing an async surface the loremaster callers
already depend on (upsert / search / scroll / count / the three deletes) plus the
hybrid retrieval and atomic per-file replace the unification adds. These tests
run against a live engine (see ``_surreal_harness``) — originally verified on
3.0.5, re-verified with no dialect deltas on 3.1.5, which is the documented
floor going forward (matching Spectron's runtime floor) — because every
behaviour that matters — HNSW filtered recall, BM25 rescue, ``search::rrf``
fusion, cross-connection snapshot isolation — is a server-side property.

The pinned contract (signatures the store must expose):

    Candidate(BaseModel):  # loremaster.store.candidate — NO qdrant types anywhere
        key: str                       # the chunk's bare uuid5 point-id
        score: float                   # the derived relevance/fusion score
        payload: dict[str, Any]        # the stored chunk fields
        origin: Literal["vector", "fulltext", "fused"]

    SurrealStore(*, url, namespace, database, dim, user, password, ...)
        async ensure_ready() -> None
        async close() -> None
        async upsert(records_with_vectors: Sequence[tuple[Record, list[float]]]) -> None
        async hybrid_search(*, query_vector, query_text, k, filters=None) -> list[Candidate]
        async scroll(filters: dict[str, str]) -> list[dict[str, Any]]
        async count(tier: str | None = None) -> int
        async replace_file(tier, file_path, records_with_vectors) -> None
        async delete_by_file(tier, file_path) -> None
        async delete_by_tier(tier) -> None
        async delete_points(ids: Sequence[str]) -> None

    Exceptions: SurrealStoreError(RuntimeError); SurrealConnectionError;
                VectorDimensionError.

Expected until P2 lands: collection ERROR in THIS FILE — ``ModuleNotFoundError:
loremaster.store.surreal`` / ``loremaster.store.candidate``.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest
import pytest_asyncio
from _surreal_fakes import FakeSurrealStore, fake_surreal_trio
from _surreal_harness import (
    PRODUCTION_DIM,
    SLUG,
    TIER_A,
    TIER_B,
    SurrealEnv,
    call_until_recovered,
    chunk_record,
    connect_admin,
    drop_database,
    make_env,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
    unique_database,
    unit_vector,
)
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.records import Record, chunk_to_record, sha512_hex
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.store._txn import (
    _MAX_TXN_CONFLICT_ATTEMPTS,
    _RETRYABLE_CONFLICT_MARKER,
    execute_transaction,
)
from loremaster.store.candidate import Candidate
from loremaster.store.surreal import (
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    SurrealStore,
    SurrealStoreError,
    VectorDimensionError,
    _SurrealConnection,
)
from loremaster.store.surreal_schema import CHUNK_TABLE, TRACE_TABLE, generate_ddl
from loremaster.symbols import _SCROLL_LIMIT  # the real scroll caller's read cap
from lorescribe.models import Chunk
from pydantic import ValidationError
from surrealdb import AsyncSurreal as _RealAsyncSurreal
from surrealdb.errors import ErrorKind, ServerError

# A factory (yielded by the ``two_stores`` fixture) that builds one more ready
# store on the SAME database — a second live connection for the isolation test.
StoreFactory = Callable[[], Awaitable[SurrealStore]]

# A port with nothing listening — the "server is down" adversary. Connecting here
# must RAISE fast, never hang and never silently return an empty result set.
_DEAD_URL = "ws://127.0.0.1:19555/rpc"

# A generous per-read cap for the small test corpora — big enough never to
# truncate an intended result, while still exercising the now-REQUIRED bound.
_READ_ALL = 1000


def _distractor(index: int, *, tier: str = TIER_A) -> Record:
    """A chunk with NO lexical overlap with the domain queries under test.

    Deliberately avoids the tokens (purchase/order/account/reconcile/action/
    confirm) the identifier queries match on, so a distractor can only surface via
    the vector arm — never by accidentally matching BM25.
    """
    return chunk_record(
        tier=tier,
        file_path=f"models/widget_{index}.py",
        identity=f"WidgetFactory.build_{index}",
        ident_text=f"WidgetFactory build_gizmo_{index}",
        source_text=f"def build_gizmo_{index}(self):\n    return {index}\n",
    )


def _near_query_vector(index: int, dim: int) -> list[float]:
    """A vector very close to the axis-0 query but DISTINCT per ``index``.

    Cosine to the axis-0 query is ~1.0 for every index (a tiny off-axis
    perturbation), so all such chunks are near-equally good vector matches — the
    interleaving that makes a naive (non-overfetched) filtered KNN under-return.
    """
    vector = [0.0] * dim
    vector[0] = 1.0
    vector[1 + (index % (dim - 1))] = 0.01
    return vector


@pytest_asyncio.fixture()
async def store(surreal_env: SurrealEnv) -> AsyncIterator[SurrealStore]:  # noqa: F811
    """A ready :class:`SurrealStore` on a fresh unique database at the production dim."""
    live_store = SurrealStore(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        dim=surreal_env.dim,
        user=surreal_env.user,
        password=surreal_env.password,
    )
    await live_store.ensure_ready()
    try:
        yield live_store
    finally:
        await live_store.close()


@pytest_asyncio.fixture()
async def two_stores(surreal_env: SurrealEnv) -> AsyncIterator[StoreFactory]:  # noqa: F811
    """A factory yielding independent ready stores on the SAME database (two conns).

    The snapshot-isolation test needs a writer and a reader on separate
    connections observing the same database concurrently.
    """
    created: list[SurrealStore] = []

    async def make() -> SurrealStore:
        live_store = SurrealStore(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            dim=surreal_env.dim,
            user=surreal_env.user,
            password=surreal_env.password,
        )
        await live_store.ensure_ready()
        created.append(live_store)
        return live_store

    try:
        yield make
    finally:
        for live_store in created:
            await live_store.close()


class TestCandidateModel:
    """The neutral candidate value object — the store's only search return type."""

    def test_holds_the_four_neutral_fields(self) -> None:
        candidate = Candidate(
            key="550e8400-e29b-41d4-a716-446655440000",
            score=0.0164,
            payload={"file_path": "models/purchase_order.py", "tier": TIER_A},
            origin="fused",
        )
        assert candidate.key == "550e8400-e29b-41d4-a716-446655440000"
        assert candidate.origin == "fused"
        assert candidate.payload["file_path"] == "models/purchase_order.py"

    def test_origin_is_restricted_to_the_three_arms(self) -> None:
        # A stray origin (e.g. a leaked qdrant-ism) must fail loudly, not coerce.
        with pytest.raises(ValidationError):
            Candidate(key="k", score=0.1, payload={}, origin="qdrant_hit")  # type: ignore[arg-type]

    def test_forbids_extra_fields_no_qdrant_leak(self) -> None:
        # extra="forbid" guarantees no qdrant ScoredPoint attribute can ride along.
        with pytest.raises(ValidationError):
            Candidate(key="k", score=0.1, payload={}, origin="vector", version=7)  # type: ignore[call-arg]


class TestEnsureReady:
    """Connect + apply schema; idempotent; a probe write round-trips afterward."""

    async def test_ensure_ready_makes_the_store_writable(self, store: SurrealStore) -> None:
        record = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py", identity="PurchaseOrder.action_confirm"
        )
        await store.upsert([(record, unit_vector(0, PRODUCTION_DIM))])
        assert await store.count() == 1

    async def test_ensure_ready_is_idempotent(self, store: SurrealStore) -> None:
        # The fixture already called it once; a second call must be a safe no-op
        # that neither raises nor wipes the store.
        record = chunk_record(tier=TIER_A, file_path="a.py", identity="A")
        await store.upsert([(record, unit_vector(0, PRODUCTION_DIM))])
        await store.ensure_ready()
        assert await store.count() == 1


class TestUpsertAndScroll:
    """Persistence + filter-only exact retrieval (the get_symbol path)."""

    async def test_scroll_returns_payload_rows_by_filter(self, store: SurrealStore) -> None:
        record = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py", identity="PurchaseOrder.action_confirm"
        )
        await store.upsert([(record, unit_vector(0, PRODUCTION_DIM))])
        rows = await store.scroll({"tier": TIER_A, "file_path": "models/purchase_order.py"}, limit=_READ_ALL)
        assert len(rows) == 1
        assert rows[0]["identity"] == "PurchaseOrder.action_confirm"
        # The verbatim body must survive the round-trip (a citation renders it).
        assert rows[0]["source_text"] == record.payload["source_text"]

    async def test_reupsert_same_records_is_idempotent(self, store: SurrealStore) -> None:
        pairs = [(_distractor(i), unit_vector(0, PRODUCTION_DIM)) for i in range(5)]
        await store.upsert(pairs)
        await store.upsert(pairs)  # deterministic ids overwrite in place, not append
        assert await store.count() == 5

    async def test_duplicate_id_within_one_batch_collapses(self, store: SurrealStore) -> None:
        record = chunk_record(tier=TIER_A, file_path="models/dup.py", identity="Dup.same")
        await store.upsert(
            [(record, unit_vector(0, PRODUCTION_DIM)), (record, unit_vector(1, PRODUCTION_DIM))]
        )
        assert await store.count() == 1

    async def test_scroll_no_match_is_honest_empty(self, store: SurrealStore) -> None:
        await store.upsert([(_distractor(0), unit_vector(0, PRODUCTION_DIM))])
        assert await store.scroll({"file_path": "does/not/exist.py"}, limit=_READ_ALL) == []


class TestHybridSearch:
    """One-query hybrid retrieval: HNSW ⊕ BM25 fused by native ``search::rrf``."""

    async def test_exact_identifier_query_rescues_a_mediocre_vector(
        self, store: SurrealStore
    ) -> None:
        # The load-bearing hybrid contract. The target's vector is ORTHOGONAL to the
        # query (worst possible), while 10 distractors sit exactly ON the query
        # (best possible). Vector-only would rank the target dead last and exclude
        # it from the top-5. Its presence proves BM25 (the exact identifier match)
        # rescued it through rrf fusion.
        dim = PRODUCTION_DIM
        target = chunk_record(
            tier=TIER_A,
            file_path="models/purchase_order.py",
            identity="PurchaseOrder.action_confirm",
            ident_text="PurchaseOrder action_confirm",
        )
        pairs = [(target, unit_vector(3, dim))]
        pairs += [(_distractor(i), unit_vector(0, dim)) for i in range(10)]
        await store.upsert(pairs)

        results = await store.hybrid_search(
            query_vector=unit_vector(0, dim),
            query_text="PurchaseOrder.action_confirm",
            k=5,
        )
        assert target.point_id in {candidate.key for candidate in results}

    async def test_semantic_query_retrieves_by_vector_without_lexical_overlap(
        self, store: SurrealStore
    ) -> None:
        # The mirror image: the query text shares NO token with any chunk, so BM25
        # contributes nothing; the target surfaces purely because its vector equals
        # the query vector — proving the vector arm still works when lexis fails.
        dim = PRODUCTION_DIM
        target = chunk_record(
            tier=TIER_A,
            file_path="models/account_move.py",
            identity="AccountMove.reconcile",
            ident_text="AccountMove reconcile",
            source_text="def reconcile(self):\n    return self.env['account.move.line']\n",
        )
        pairs = [(target, unit_vector(7, dim))]
        pairs += [(_distractor(i), unit_vector(0, dim)) for i in range(6)]
        await store.upsert(pairs)

        results = await store.hybrid_search(
            query_vector=unit_vector(7, dim),
            query_text="zzqx nonexistent lexeme",
            k=5,
        )
        assert target.point_id in {candidate.key for candidate in results}

    async def test_filter_scopes_with_full_k_recall(self, store: SurrealStore) -> None:
        # 20 tier-A and 20 tier-B chunks share the SAME near-query vectors, so a
        # naive filtered KNN (take k pre-filter, then drop the wrong tier) would
        # under-return ~half. A correct overfetch yields the full k, all tier A.
        dim = PRODUCTION_DIM
        pairs = [(_distractor(i, tier=TIER_A), _near_query_vector(i, dim)) for i in range(20)]
        pairs += [(_distractor(100 + i, tier=TIER_B), _near_query_vector(i, dim)) for i in range(20)]
        await store.upsert(pairs)

        results = await store.hybrid_search(
            query_vector=unit_vector(0, dim),
            query_text="build_gizmo",
            k=10,
            filters={"tier": TIER_A},
        )
        assert len(results) == 10  # full-k recall, not under-returned
        assert all(candidate.payload["tier"] == TIER_A for candidate in results)

    async def test_k_limits_result_count(self, store: SurrealStore) -> None:
        dim = PRODUCTION_DIM
        await store.upsert([(_distractor(i), unit_vector(0, dim)) for i in range(8)])
        results = await store.hybrid_search(
            query_vector=unit_vector(0, dim), query_text="build_gizmo", k=3
        )
        assert len(results) <= 3

    async def test_empty_corpus_returns_empty_list(self, store: SurrealStore) -> None:
        # A HEALTHY store with no data returns [] — the honest empty (distinct from
        # a connection failure, which must RAISE; see TestResilience).
        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM), query_text="anything", k=5
        )
        assert results == []

    async def test_filter_matching_nothing_is_honest_empty(self, store: SurrealStore) -> None:
        await store.upsert([(_distractor(0, tier=TIER_A), unit_vector(0, PRODUCTION_DIM))])
        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM),
            query_text="build_gizmo",
            k=5,
            filters={"tier": "nonexistent_tier"},
        )
        assert results == []

    async def test_rrf_ordering_is_deterministic(self, store: SurrealStore) -> None:
        # Same inputs, same order — a stable tie-break so results don't shuffle
        # between identical calls (which would make pagination/caching incoherent).
        dim = PRODUCTION_DIM
        await store.upsert([(_distractor(i), _near_query_vector(i, dim)) for i in range(6)])
        first = [c.key for c in await store.hybrid_search(
            query_vector=unit_vector(0, dim), query_text="build_gizmo", k=6)]
        second = [c.key for c in await store.hybrid_search(
            query_vector=unit_vector(0, dim), query_text="build_gizmo", k=6)]
        assert first == second

    async def test_returns_neutral_candidates_keyed_by_bare_point_id(
        self, store: SurrealStore
    ) -> None:
        dim = PRODUCTION_DIM
        target = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py", identity="PurchaseOrder.action_confirm"
        )
        await store.upsert([(target, unit_vector(0, dim))])
        results = await store.hybrid_search(
            query_vector=unit_vector(0, dim), query_text="PurchaseOrder", k=5
        )
        assert results, "the target chunk should surface"
        hit = next(candidate for candidate in results if candidate.key == target.point_id)
        assert isinstance(hit, Candidate)
        # The key is the BARE uuid5 point-id — no ``chunk:`` record-table prefix —
        # so it matches the existing memory-ref / chunk_key convention unchanged.
        assert hit.key == target.point_id
        assert "chunk:" not in hit.key
        assert hit.payload["file_path"] == "models/purchase_order.py"
        assert hit.origin in ("vector", "fulltext", "fused")
        # Sanity bound on the derived fusion score: finite and non-negative.
        assert hit.score >= 0.0
        assert hit.score == hit.score  # not NaN

    async def test_unicode_and_emoji_source_text_round_trips(self, store: SurrealStore) -> None:
        dim = PRODUCTION_DIM
        body = "def greet():\n    return 'café ☕ — naïve Ünïcode 🎉 日本語'\n"
        record = chunk_record(
            tier=TIER_A,
            file_path="models/greet.py",
            identity="greet",
            ident_text="greet cafe",
            source_text=body,
        )
        await store.upsert([(record, unit_vector(0, dim))])
        results = await store.hybrid_search(
            query_vector=unit_vector(0, dim), query_text="greet", k=5
        )
        hit = next(candidate for candidate in results if candidate.key == record.point_id)
        assert hit.payload["source_text"] == body

    async def test_large_metadata_payload_round_trips(self, store: SurrealStore) -> None:
        # A production long-tail row: a big metadata blob must survive intact
        # through the store's serialization. The INPUT still uses the
        # harness's legacy nested-``metadata``-key producer shape
        # (``chunk_record()`` migrates in a later REFACTOR, not here), but
        # the reconciled READ-BACK contract is canonical regardless of
        # producer shape: every attribute key comes back TOP-LEVEL, and the
        # returned row carries NO ``"metadata"`` wrapper key at all — the
        # same canonical shape ``TestMetadataShapeReconciliation`` pins for
        # the modern ``chunk_to_record``-flattened producer shape.
        dim = PRODUCTION_DIM
        big_metadata = {
            f"attr_{i}": {"nested": list(range(20)), "text": "x" * 500} for i in range(50)
        }
        record = chunk_record(
            tier=TIER_A, file_path="models/big.py", identity="Big.thing", metadata=big_metadata
        )
        await store.upsert([(record, unit_vector(0, dim))])
        rows = await store.scroll({"file_path": "models/big.py"}, limit=_READ_ALL)
        assert len(rows) == 1
        # Canonical API-boundary shape: no "metadata" wrapper key survives —
        # every attribute is promoted to a top-level key on read-back.
        assert "metadata" not in rows[0]
        assert rows[0]["attr_0"]["nested"] == list(range(20))
        assert rows[0]["attr_49"]["text"] == "x" * 500


class TestCount:
    """The live server-side count — total and tier-scoped, never the manifest."""

    async def test_count_total_and_by_tier(self, store: SurrealStore) -> None:
        dim = PRODUCTION_DIM
        await store.upsert(
            [
                (chunk_record(tier=TIER_A, file_path="a.py", identity="A"), unit_vector(0, dim)),
                (chunk_record(tier=TIER_A, file_path="b.py", identity="B"), unit_vector(1, dim)),
                (chunk_record(tier=TIER_B, file_path="a.py", identity="A"), unit_vector(2, dim)),
            ]
        )
        assert await store.count() == 3
        assert await store.count(tier=TIER_A) == 2
        assert await store.count(tier=TIER_B) == 1
        # An absent tier counts zero (non-negative), never raises.
        assert await store.count(tier="nonexistent") == 0


class TestTierCollisionC1:
    """One path under two tiers — both copies coexist (tier folded into the key)."""

    async def test_same_path_two_tiers_both_survive(self, store: SurrealStore) -> None:
        dim = PRODUCTION_DIM
        path = "models/account.py"
        record_a = chunk_record(tier=TIER_A, file_path=path, identity="Account")
        record_b = chunk_record(tier=TIER_B, file_path=path, identity="Account")
        # Distinct ids from the shared tiered point-id scheme — what lets both live.
        assert record_a.point_id != record_b.point_id
        await store.upsert([(record_a, unit_vector(0, dim)), (record_b, unit_vector(1, dim))])

        assert await store.count() == 2
        tiers = sorted(row["tier"] for row in await store.scroll({"file_path": path}, limit=_READ_ALL))
        assert tiers == [TIER_B, TIER_A]  # sorted: community, custom


class TestDeletes:
    """The per-file / per-tier / per-id purge primitives."""

    async def test_delete_by_file_purges_only_that_tier_and_path(
        self, store: SurrealStore
    ) -> None:
        dim = PRODUCTION_DIM
        path = "shared.py"
        await store.upsert(
            [
                (chunk_record(tier=TIER_A, file_path=path, identity="x"), unit_vector(0, dim)),
                (chunk_record(tier=TIER_B, file_path=path, identity="x"), unit_vector(1, dim)),
                (chunk_record(tier=TIER_A, file_path="other.py", identity="y"), unit_vector(2, dim)),
            ]
        )
        await store.delete_by_file(TIER_B, path)

        assert await store.count() == 2
        assert await store.count(tier=TIER_B) == 0
        survivors = sorted(
            (row["tier"], row["file_path"]) for row in await store.scroll({"tier": TIER_A}, limit=_READ_ALL)
        )
        assert survivors == [(TIER_A, "other.py"), (TIER_A, "shared.py")]

    async def test_delete_by_tier_purges_only_that_tier(self, store: SurrealStore) -> None:
        dim = PRODUCTION_DIM
        await store.upsert(
            [
                (chunk_record(tier=TIER_A, file_path="a.py", identity="x"), unit_vector(0, dim)),
                (chunk_record(tier=TIER_A, file_path="b.py", identity="y"), unit_vector(1, dim)),
                (chunk_record(tier=TIER_B, file_path="a.py", identity="x"), unit_vector(2, dim)),
            ]
        )
        await store.delete_by_tier(TIER_A)
        assert await store.count(tier=TIER_A) == 0
        assert await store.count(tier=TIER_B) == 1

    async def test_delete_missing_tier_is_a_noop(self, store: SurrealStore) -> None:
        await store.upsert(
            [(chunk_record(tier=TIER_A, file_path="a.py", identity="x"), unit_vector(0, PRODUCTION_DIM))]
        )
        await store.delete_by_tier("nonexistent")  # must not raise
        assert await store.count() == 1

    async def test_delete_points_removes_only_named_ids(self, store: SurrealStore) -> None:
        # The upsert-new-before-purge-stale enabler: purge only the stale id, the
        # fresh chunk of the same (tier, file) survives.
        dim = PRODUCTION_DIM
        stale = chunk_record(tier=TIER_A, file_path="m.py", identity="old")
        fresh = chunk_record(tier=TIER_A, file_path="m.py", identity="new")
        await store.upsert([(stale, unit_vector(0, dim)), (fresh, unit_vector(1, dim))])
        await store.delete_points([stale.point_id])
        idents = {row["identity"] for row in await store.scroll({"file_path": "m.py"}, limit=_READ_ALL)}
        assert idents == {"new"}

    async def test_delete_points_empty_is_a_noop(self, store: SurrealStore) -> None:
        await store.upsert(
            [(chunk_record(tier=TIER_A, file_path="a.py", identity="x"), unit_vector(0, PRODUCTION_DIM))]
        )
        await store.delete_points([])  # must not raise, must delete nothing
        assert await store.count() == 1


class TestSnapshotIsolation:
    """A concurrent reader never observes a partial per-file replace (two conns)."""

    async def test_reader_never_sees_a_partial_file_replace(
        self, two_stores: StoreFactory
    ) -> None:
        make = two_stores
        writer = await make()
        reader = await make()
        dim = PRODUCTION_DIM
        tier = TIER_A
        path = "models/purchase_order.py"

        old = [
            chunk_record(tier=tier, file_path=path, identity=f"old_{i}", ident_text=f"Old member{i}")
            for i in range(8)
        ]
        await writer.upsert([(record, unit_vector(i, dim)) for i, record in enumerate(old)])
        new = [
            chunk_record(tier=tier, file_path=path, identity=f"new_{i}", ident_text=f"New member{i}")
            for i in range(8)
        ]
        new_pairs = [(record, unit_vector(100 + i, dim)) for i, record in enumerate(new)]

        old_set = frozenset(f"old_{i}" for i in range(8))
        new_set = frozenset(f"new_{i}" for i in range(8))
        observed: list[frozenset[str]] = []

        async def read_loop() -> None:
            for _ in range(120):
                rows = await reader.scroll({"tier": tier, "file_path": path}, limit=_READ_ALL)
                observed.append(frozenset(row["identity"] for row in rows))
                await asyncio.sleep(0)

        async def write_once() -> None:
            await asyncio.sleep(0.002)  # let the reader loop get going
            await writer.replace_file(tier, path, new_pairs)

        await asyncio.gather(read_loop(), write_once())

        # Every snapshot is a COMPLETE pre- or post-commit state; a non-atomic
        # delete-then-insert would leak an empty/partial window that lands here.
        for snapshot in observed:
            assert snapshot in (old_set, new_set), f"partial file state observed: {sorted(snapshot)}"
        # Post-condition: the replace committed the new content.
        final = frozenset(
            row["identity"] for row in await reader.scroll({"tier": tier, "file_path": path}, limit=_READ_ALL)
        )
        assert final == new_set


class TestReplaceFile:
    """The atomic per-file transaction (task #19): swap a file's chunks in ONE
    ``BEGIN … COMMIT`` round trip, and — the hardening this task pins — never
    report a silent false success when the engine rolls that transaction back.

    Grounding (live 3.1.5 probes, since the ``chunk`` table carries no
    field-level ``ASSERT`` the way ``file.state`` does): a bare ``query()``
    call only inspects the FIRST statement's status (the ``BEGIN``, which
    never itself fails) before deciding whether to raise — confirmed live
    that a LATER statement's rejection rolls the WHOLE transaction back
    server-side while ``query()`` returns ``None`` with **no exception at
    all**. The deterministic in-transaction failure used below is a genuine
    SCHEMAFULL TYPE-coercion rejection: ``sub_ordinal`` is declared ``int``
    (``surreal_schema._CHUNK_FIELD_SPECS``), and handing it a string is
    rejected server-side ("Couldn't coerce value for field `sub_ordinal`") —
    verified live to roll back the DELETE too, not just the bad UPSERT.
    """

    async def test_replace_file_swaps_old_chunks_for_new_ones(self, store: SurrealStore) -> None:
        # Regression: the plain happy path must keep working unchanged.
        dim = PRODUCTION_DIM
        path = "models/purchase_order.py"
        old = [
            chunk_record(tier=TIER_A, file_path=path, identity=f"Old.method_{i}")
            for i in range(3)
        ]
        await store.upsert([(record, unit_vector(i, dim)) for i, record in enumerate(old)])

        new = [
            chunk_record(tier=TIER_A, file_path=path, identity=f"New.method_{i}")
            for i in range(2)
        ]
        await store.replace_file(
            TIER_A, path, [(record, unit_vector(10 + i, dim)) for i, record in enumerate(new)]
        )

        rows = await store.scroll({"tier": TIER_A, "file_path": path}, limit=_READ_ALL)
        assert {row["identity"] for row in rows} == {"New.method_0", "New.method_1"}
        assert await store.count() == 2  # the old rows are gone, not additive

    async def test_replace_file_does_not_touch_other_files_or_tiers(
        self, store: SurrealStore
    ) -> None:
        dim = PRODUCTION_DIM
        path = "models/purchase_order.py"
        kept_other_file = chunk_record(
            tier=TIER_A, file_path="models/sale_order.py", identity="Kept"
        )
        kept_other_tier = chunk_record(tier=TIER_B, file_path=path, identity="Kept")
        await store.upsert(
            [(kept_other_file, unit_vector(0, dim)), (kept_other_tier, unit_vector(1, dim))]
        )
        new = chunk_record(tier=TIER_A, file_path=path, identity="New.method")
        await store.replace_file(TIER_A, path, [(new, unit_vector(2, dim))])

        assert await store.count() == 3  # kept_other_file + kept_other_tier + new
        survivors = {row["identity"] for row in await store.scroll({}, limit=_READ_ALL)}
        assert survivors == {"Kept", "New.method"}

    async def test_replace_file_surfaces_a_rolled_back_transaction(
        self, store: SurrealStore
    ) -> None:
        # LOAD-BEARING (task #19): must FAIL RED against the current bare-
        # ``_query`` ``replace_file`` — it currently returns ``None`` with no
        # exception at all here (verified live), even though the engine
        # rejected the write and rolled the WHOLE transaction back.
        dim = PRODUCTION_DIM
        path = "models/purchase_order.py"
        prior = [
            chunk_record(tier=TIER_A, file_path=path, identity=f"Prior.method_{i}")
            for i in range(2)
        ]
        await store.upsert([(record, unit_vector(i, dim)) for i, record in enumerate(prior)])

        good = chunk_record(tier=TIER_A, file_path=path, identity="New.good")
        poison = chunk_record(tier=TIER_A, file_path=path, identity="New.poison")
        # Poison: wrong TYPE (not wrong VALUE) — the chunk table has no field
        # ASSERT, but ``sub_ordinal`` is SCHEMAFULL ``int``; a string there is
        # a genuine, deterministic, engine-level rejection (see class docstring).
        poison.payload["sub_ordinal"] = "not-an-int"

        connection_before = store._connection
        with pytest.raises(SurrealStoreError) as exc_info:
            await store.replace_file(
                TIER_A, path, [(good, unit_vector(10, dim)), (poison, unit_vector(11, dim))]
            )
        # F2 (error-type unification): a domain/schema rejection is a STORE
        # error, never miscategorized as a connection failure — the broad
        # ``pytest.raises(Exception)`` pattern is exactly what let this drift
        # elsewhere, so the type is pinned EXACTLY, not just "a subclass of".
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        # A healthy connection must never be nulled for a rejection that has
        # nothing to do with the transport.
        assert store._connection is connection_before

        # The prior rows survive completely intact — the DELETE was rolled
        # back too, not just the poisoned UPSERT (rollback verified by a
        # follow-up read, not just "no exception on the surface").
        rows = await store.scroll({"tier": TIER_A, "file_path": path}, limit=_READ_ALL)
        assert {row["identity"] for row in rows} == {"Prior.method_0", "Prior.method_1"}
        assert await store.count() == 2


class TestResilience:
    """Connection failure RAISES a typed error — never a silent empty result."""

    async def test_unreachable_server_raises_on_ensure_ready(
        self, surreal_env: SurrealEnv  # noqa: F811 - imported fixture as param
    ) -> None:
        down_store = SurrealStore(
            url=_DEAD_URL,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            dim=surreal_env.dim,
            user=surreal_env.user,
            password=surreal_env.password,
        )
        with pytest.raises(SurrealConnectionError):
            await down_store.ensure_ready()

    async def test_connection_failure_raises_never_silent_empty(
        self, surreal_env: SurrealEnv  # noqa: F811 - imported fixture as param
    ) -> None:
        # SchemaRebuildingError-style honesty: a search against a down server must
        # RAISE, never return [] (which a caller would read as "no results").
        down_store = SurrealStore(
            url=_DEAD_URL,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            dim=surreal_env.dim,
            user=surreal_env.user,
            password=surreal_env.password,
        )
        with pytest.raises(SurrealConnectionError):
            await down_store.hybrid_search(
                query_vector=[0.0] * surreal_env.dim, query_text="anything", k=5
            )

    async def test_bad_auth_raises(
        self, surreal_env: SurrealEnv  # noqa: F811 - imported fixture as param
    ) -> None:
        bad_store = SurrealStore(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            dim=surreal_env.dim,
            user=surreal_env.user,
            password="DELIBERATELY-WRONG-PASSWORD",
        )
        with pytest.raises(SurrealConnectionError):
            await bad_store.ensure_ready()

    async def test_wrong_dim_vector_rejected_loudly_at_upsert(self, store: SurrealStore) -> None:
        # A vector at the wrong width is rejected LOUDLY (typed) at the write
        # boundary and must not partially persist — the probe-gate discipline.
        record = chunk_record(tier=TIER_A, file_path="models/x.py", identity="X")
        wrong_width = [0.1] * (PRODUCTION_DIM // 4)  # 512 against a 2048 store
        with pytest.raises(VectorDimensionError):
            await store.upsert([(record, wrong_width)])
        assert await store.count() == 0


class TestDomainRejectionErrorType:
    """F2 (error-type unification, task #19): a domain/schema rejection is a
    STORE error, never a connection error.

    ``upsert`` runs a SINGLE statement per record through the bare
    ``_query`` seam (see :meth:`SurrealStore._query`). Verified live: a
    SCHEMAFULL type-coercion rejection there raises a
    ``surrealdb.errors.SurrealError`` subclass, which today is caught by the
    SAME except-branch as a genuine transport failure
    (:data:`_CONNECTION_ERRORS`) and re-wrapped as
    :class:`SurrealConnectionError` — nulling an otherwise HEALTHY
    connection. The caller cannot tell "the server is down" apart from "the
    write I sent was rejected", and a perfectly good connection is thrown
    away for no reason. This class pins the INTENDED unified behaviour:
    exactly :class:`SurrealStoreError`, connection left untouched.
    """

    async def test_single_statement_domain_rejection_raises_store_error(
        self, store: SurrealStore
    ) -> None:
        # LOAD-BEARING: must FAIL RED against current code, which raises
        # SurrealConnectionError here (verified live) instead of
        # SurrealStoreError, and nulls the healthy connection in the process.
        dim = PRODUCTION_DIM
        poison = chunk_record(tier=TIER_A, file_path="models/x.py", identity="X")
        poison.payload["sub_ordinal"] = "not-an-int"  # wrong TYPE, not wrong VALUE

        connection_before = store._connection
        with pytest.raises(SurrealStoreError) as exc_info:
            await store.upsert([(poison, unit_vector(0, dim))])
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert store._connection is connection_before
        assert await store.count() == 0  # nothing partially persisted


# The closed allow-list of real chunk columns that are legitimate exact-match
# filter dimensions (records.py structural fields + the security requirement).
# The store validates every filter KEY against this set AT THE TRUST BOUNDARY,
# so an agent-supplied key can never be interpolated into a query.
_ALLOWED_FILTER_KEYS = ("tier", "file_path", "chunk_type", "identity", "content_hash")

# A harmless, well-formed value per allowed column so an "is it accepted?" probe
# builds a valid query.
_ALLOWED_KEY_VALUES = {
    "tier": TIER_A,
    "file_path": "models/purchase_order.py",
    "chunk_type": "python_symbol",
    "identity": "PurchaseOrder.action_confirm",
    "content_hash": "0" * 128,
}

# Hostile filter keys an agent-facing search tool could pass through. NONE may
# reach a query: the KEY was string-interpolated (only values were bound), so a
# key is a full SurrealQL statement-injection vector once the store is wired
# behind ``search_code``. A closed allow-list (exact membership) rejects every
# one of these, including the clean-looking non-columns a mere character
# blocklist would wave through.
_HOSTILE_FILTER_KEYS = (
    "a; DELETE chunk; --",             # multi-statement injection
    "true OR true",                    # boolean tautology — bypass the filter
    "tier = 'x' OR '1'='1'",           # classic tautology with quotes
    'file_path"; REMOVE TABLE chunk',  # embedded double-quote break-out
    "tｉer",                            # unicode homoglyph (U+FF49) — NOT "tier"
    "",                                # empty key
    "nonexistent_field",               # clean, but not a column — proves ALLOW-list
    "embedding",                       # a real column, but not a filter dimension
)


class TestFilterKeyInjection:
    """Filter KEYS are validated at the store trust boundary — no SurrealQL injection.

    Values were always bound as params; the KEY was interpolated verbatim into
    the WHERE fragment. Once ``SurrealStore`` sits behind ``search_code`` (P6), an
    agent-supplied filter key becomes a statement-injection vector — scroll and
    hybrid search run multi-statement SurrealQL that reaches the memory /
    file_text tables. The store must reject any key NOT in the closed column
    allow-list BEFORE building a query, while binding hostile CONTENT as data.
    """

    async def test_legitimate_filter_keys_are_accepted(self, store: SurrealStore) -> None:
        # Guard against over-restriction: every real filter column a caller uses
        # (symbols.py scrolls identity+chunk_type; hybrid filters tier/file_path)
        # must pass the boundary and simply return a list, never raise.
        await store.upsert(
            [
                (
                    chunk_record(
                        tier=TIER_A,
                        file_path="models/purchase_order.py",
                        identity="PurchaseOrder.action_confirm",
                    ),
                    unit_vector(0, PRODUCTION_DIM),
                )
            ]
        )
        for key in _ALLOWED_FILTER_KEYS:
            rows = await store.scroll({key: _ALLOWED_KEY_VALUES[key]}, limit=_READ_ALL)
            assert isinstance(rows, list)  # accepted at the boundary, no raise

    @pytest.mark.parametrize("hostile_key", _HOSTILE_FILTER_KEYS)
    async def test_hostile_filter_key_is_rejected_at_scroll(
        self, store: SurrealStore, hostile_key: str
    ) -> None:
        # Seed a known corpus, attempt a hostile-key scroll: the store must RAISE
        # at the boundary AND the corpus must be intact afterward — proving the
        # injected DELETE/REMOVE never executed (the non-execution guarantee).
        await store.upsert(
            [
                (chunk_record(tier=TIER_A, file_path=f"models/m{i}.py", identity=f"X{i}"),
                 unit_vector(0, PRODUCTION_DIM))
                for i in range(5)
            ]
        )
        with pytest.raises(SurrealStoreError):
            await store.scroll({hostile_key: "x"}, limit=_READ_ALL)
        assert await store.count() == 5  # the injected statement never ran

    @pytest.mark.parametrize("hostile_key", _HOSTILE_FILTER_KEYS)
    async def test_hostile_filter_key_is_rejected_at_hybrid_search(
        self, store: SurrealStore, hostile_key: str
    ) -> None:
        await store.upsert(
            [
                (chunk_record(tier=TIER_A, file_path=f"models/m{i}.py", identity=f"X{i}"),
                 unit_vector(0, PRODUCTION_DIM))
                for i in range(5)
            ]
        )
        with pytest.raises(SurrealStoreError):
            await store.hybrid_search(
                query_vector=unit_vector(0, PRODUCTION_DIM),
                query_text="build",
                k=5,
                filters={hostile_key: "x"},
            )
        assert await store.count() == 5  # the injected statement never ran

    async def test_hostile_source_text_round_trips_as_data_never_executes(
        self, store: SurrealStore
    ) -> None:
        # Belt-and-suspenders: chunk CONTENT is bound (safe). A body full of
        # SurrealQL + quotes must persist verbatim and NOT delete the sibling row.
        dim = PRODUCTION_DIM
        malicious_body = "'; DELETE chunk WHERE true; -- \" OR \"1\"=\"1"
        victim = chunk_record(tier=TIER_A, file_path="models/victim.py", identity="Victim")
        attacker = chunk_record(
            tier=TIER_A,
            file_path="models/attacker.py",
            identity="Attacker",
            source_text=malicious_body,
        )
        await store.upsert([(victim, unit_vector(0, dim)), (attacker, unit_vector(1, dim))])
        # Both rows survive — the body was stored as data, never run as a statement.
        assert await store.count() == 2
        rows = await store.scroll({"file_path": "models/attacker.py"}, limit=_READ_ALL)
        assert len(rows) == 1
        assert rows[0]["source_text"] == malicious_body  # verbatim, unescaped


class TestScrollLimit:
    """scroll() takes a REQUIRED bound and honors it — no unbounded reads."""

    async def test_scroll_honors_its_limit(self, store: SurrealStore) -> None:
        # Seed more rows than the cap under one filter; the read returns EXACTLY
        # the cap. An unbounded scroll (the regression) would return all of them.
        dim = PRODUCTION_DIM
        await store.upsert(
            [
                (chunk_record(tier=TIER_A, file_path=f"models/f{i}.py", identity="Shared.symbol"),
                 unit_vector(0, dim))
                for i in range(12)
            ]
        )
        rows = await store.scroll({"identity": "Shared.symbol"}, limit=5)
        assert len(rows) == 5

    async def test_scroll_signature_matches_symbols_caller(self, store: SurrealStore) -> None:
        # The live caller (symbols.py) calls scroll(filters=…, limit=_SCROLL_LIMIT).
        # That exact form must work and be capped — else it TypeErrors when
        # SurrealStore is wired in (P6). Seed > _SCROLL_LIMIT collision siblings.
        dim = PRODUCTION_DIM
        await store.upsert(
            [
                (
                    chunk_record(
                        tier=TIER_A,
                        file_path=f"models/g{i}.py",
                        identity="Collide.name",
                        chunk_type="python_symbol",
                    ),
                    unit_vector(0, dim),
                )
                for i in range(_SCROLL_LIMIT + 4)
            ]
        )
        rows = await store.scroll(
            filters={"identity": "Collide.name", "chunk_type": "python_symbol"},
            limit=_SCROLL_LIMIT,
        )
        assert len(rows) == _SCROLL_LIMIT

    async def test_scroll_order_is_deterministic_ascending_record_id(
        self, store: SurrealStore
    ) -> None:
        # Cycle-1 audit addendum: scroll order must be CONTRACTUAL (ORDER BY
        # id), not an engine accident — symbols.py's collision handling and
        # every future scroll consumer must never inherit a heisen-order.
        # Seed in DESCENDING point-id order (the known-permutation trick) so
        # an insertion-order echo cannot masquerade as the contract. Honest
        # note: pre-ORDER-BY the engine may ALREADY iterate ascending (RocksDB
        # key order), so this pin's red phase is best-effort; the guarantee —
        # not the accident — is what it locks in.
        dim = PRODUCTION_DIM
        pairs = [
            (
                chunk_record(
                    tier=TIER_A,
                    file_path=f"models/order{i}.py",
                    identity="Ordered.scan",
                ),
                unit_vector(0, dim),
            )
            for i in range(9)
        ]
        pairs.sort(key=lambda pair: pair[0].point_id, reverse=True)
        await store.upsert(pairs)
        # Expected: ascending bare point-id order (record ids share the table
        # prefix, so bare-key order == record-id order, ASCII collation both
        # sides).
        expected_paths = [
            record.payload["file_path"]
            for record, _vector in sorted(pairs, key=lambda pair: pair[0].point_id)
        ]

        first = await store.scroll({"identity": "Ordered.scan"}, limit=9)
        second = await store.scroll({"identity": "Ordered.scan"}, limit=9)

        assert [row["file_path"] for row in first] == expected_paths
        assert [row["file_path"] for row in second] == expected_paths


# Connection-drop exception classes a mid-life failure may surface as before the
# store heals — the store's OWN _CONNECTION_ERRORS (shared source of truth) plus
# its typed SurrealStoreError wrapper, so the probe tolerates either GREEN surface
# (transparent single-call retry, OR one surfaced typed transient then reconnect).
_HEALABLE_ERRORS: tuple[type[BaseException], ...] = (SurrealStoreError, *_CONNECTION_ERRORS)


async def _kill_socket(store: SurrealStore) -> None:
    """Kill the store's underlying WS socket, leaving its CACHED handle dead.

    The degradation half of the lifecycle test: the socket dies out from under
    the store (a real transient WS drop), but the store still holds the (now
    dead) connection object — exactly the mid-life failure the module docstring
    claims to survive.
    """
    connection = store._connection
    assert connection is not None, "expected an established connection to kill"
    await connection.close()


class TestMidLifeConnectionRecovery:
    """A mid-life connection drop must self-heal — degradation → recovery (CLAUDE.md).

    The store caches ONE stateful WS connection. When that socket dies mid-life,
    the store must drop the cached handle on the connection-class failure so the
    next call transparently reconnects — it must NOT wedge, raising on every
    subsequent call until an (uncalled) ``close()``. This is the degradation→
    recovery lifecycle test whose absence let the bug ship green: the module
    docstring asserts this recovery already exists, but operation-time failures
    never nulled the cached handle (only connect-TIME failures did).
    """

    async def test_count_recovers_from_a_mid_life_socket_drop(self, store: SurrealStore) -> None:
        dim = PRODUCTION_DIM
        await store.upsert(
            [
                (chunk_record(tier=TIER_A, file_path=f"models/m{i}.py", identity=f"X{i}"),
                 unit_vector(0, dim))
                for i in range(5)
            ]
        )
        assert await store.count() == 5  # healthy baseline — connection established

        await _kill_socket(store)  # degradation: the socket dies, handle goes stale

        # Recovery: heal within a bounded number of calls (never wedge) and return
        # the correct live count.
        assert await call_until_recovered(store.count, _HEALABLE_ERRORS, label="store") == 5
        # And it STAYS healed — a further call also works (the handle was actually
        # replaced, not a one-off fluke).
        assert await store.count() == 5

    async def test_hybrid_search_recovers_from_a_mid_life_socket_drop(
        self, store: SurrealStore
    ) -> None:
        # The same lifecycle guarantee on the search path, not just count.
        dim = PRODUCTION_DIM
        target = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py", identity="PurchaseOrder.action_confirm"
        )
        await store.upsert([(target, unit_vector(0, dim))])
        first = await store.hybrid_search(
            query_vector=unit_vector(0, dim), query_text="PurchaseOrder", k=5
        )
        assert any(candidate.key == target.point_id for candidate in first)

        await _kill_socket(store)

        async def _search() -> list[Candidate]:
            return await store.hybrid_search(
                query_vector=unit_vector(0, dim), query_text="PurchaseOrder", k=5
            )

        recovered = await call_until_recovered(_search, _HEALABLE_ERRORS, label="store")
        assert any(candidate.key == target.point_id for candidate in recovered)


class TestQueryTextEdgeCases:
    """Degenerate query_text (the _NO_MATCH fulltext arm) and the k=1 boundary."""

    @pytest.mark.parametrize("query_text", ["", "   ", "!!! ??? ...", "()[]{}.,;"])
    async def test_tokenless_query_text_still_retrieves_by_vector(
        self, store: SurrealStore, query_text: str
    ) -> None:
        # An empty / all-punctuation query yields NO analyzer tokens, so the BM25
        # arm degenerates to the _NO_MATCH ("false") predicate; the vector arm must
        # still surface the near chunk (rrf over one live arm) — never error.
        dim = PRODUCTION_DIM
        target = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py", identity="PurchaseOrder.action_confirm"
        )
        await store.upsert([(target, unit_vector(0, dim))])
        results = await store.hybrid_search(
            query_vector=unit_vector(0, dim), query_text=query_text, k=5
        )
        assert any(candidate.key == target.point_id for candidate in results)

    async def test_k_of_one_returns_a_single_best_hit(self, store: SurrealStore) -> None:
        dim = PRODUCTION_DIM
        target = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py", identity="PurchaseOrder.action_confirm"
        )
        pairs = [(target, unit_vector(0, dim))]
        pairs += [(_distractor(i), unit_vector(0, dim)) for i in range(4)]
        await store.upsert(pairs)
        results = await store.hybrid_search(
            query_vector=unit_vector(0, dim), query_text="PurchaseOrder", k=1
        )
        assert len(results) == 1  # exactly the boundary k
        assert results[0].key == target.point_id  # the BM25+vector best


# ---------------------------------------------------------------------------
# P5-C1a, concern 1 (P2-audit S5): the connect-lock race.
#
# ``_ensure_connection`` on ALL THREE lazily-connecting classes
# (``SurrealStore``, ``SurrealManifest``, ``SurrealCodeGraph``) is a bare
# check-then-set: ``if self._connection is not None: return ...`` followed by
# an ``await``-laden connect+signin sequence before ``self._connection =
# connection`` is ever assigned. N concurrent FIRST callers on a freshly
# constructed instance therefore all pass the check before any of them
# finishes connecting, each opening its OWN underlying SDK connection — a
# resource leak (N-1 sockets abandoned) that also wastes N signin round trips
# at process/request startup, when exactly one connection is needed.
# ---------------------------------------------------------------------------

# The number of concurrent first-callers racing a fresh instance — enough to
# make a check-then-set race land reliably (matches this suite's other
# "prove concurrency correctness" probes, e.g. the snapshot-isolation loop).
_RACE_CONCURRENT_CALLERS = 8

# A small artificial delay inserted into the wrapped connection's ``signin``
# so ALL ``_RACE_CONCURRENT_CALLERS`` coroutines are guaranteed to pass the
# ``self._connection is not None`` check before any of them completes and
# assigns — forcing the interleave deterministically rather than depending on
# incidental localhost network timing (which could vary by host/load and make
# the RED demonstration flaky).
_RACE_SIGNIN_DELAY_SECONDS = 0.02


def _counting_connection_factory() -> tuple[Callable[[str], Any], Callable[[], int]]:
    """A drop-in replacement for the SDK's ``AsyncSurreal`` constructor that
    COUNTS every real connection it opens.

    Wraps the REAL ``AsyncSurreal(url)`` (preserving behaviour — the returned
    object is a genuine, working connection against the live server) and
    delays its ``signin`` by :data:`_RACE_SIGNIN_DELAY_SECONDS` so a batch of
    concurrently-scheduled callers all reach their own ``AsyncSurreal(url)``
    construction (and thus increment the counter) before ANY of them
    completes signin and could assign ``self._connection`` — the
    deterministic check-then-set race window the class docstrings below pin.

    Returns:
        ``(factory, get_call_count)`` — the callable to monkeypatch in for
        ``AsyncSurreal``, and a zero-arg accessor for the running count of
        distinct connections it has constructed.
    """
    call_count = 0

    def factory(url: str) -> Any:
        nonlocal call_count
        call_count += 1
        connection = _RealAsyncSurreal(url)
        original_signin = connection.signin

        async def delayed_signin(credentials: dict[str, Any]) -> Any:
            await asyncio.sleep(_RACE_SIGNIN_DELAY_SECONDS)
            return await original_signin(credentials)

        connection.signin = delayed_signin  # type: ignore[assignment, method-assign]
        return connection

    return factory, lambda: call_count


class TestConnectionRaceSingleConnect:
    """P2-audit S5: a fresh instance's lazy connect must open exactly ONE
    underlying SDK connection under N concurrent first-callers — for EACH of
    the three lazily-connecting classes (``SurrealStore``, ``SurrealManifest``,
    ``SurrealCodeGraph``), which all share the identical check-then-set
    ``_ensure_connection`` idiom (verified by reading each class's source).

    LOAD-BEARING: every case here must FAIL RED against current code — the
    bare ``if self._connection is not None`` check has no lock, so N
    concurrently-scheduled first callers all pass it before any of them
    finishes connecting and assigns, each opening its own connection.
    """

    async def test_surreal_store_opens_exactly_one_connection_under_concurrent_first_use(
        self, surreal_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch  # noqa: F811
    ) -> None:
        # Arrange: a FRESH store (never connected) with the connection
        # factory it will call wrapped to count + deterministically widen
        # the race window.
        factory, get_call_count = _counting_connection_factory()
        monkeypatch.setattr("loremaster.store.surreal.AsyncSurreal", factory)
        fresh_store = SurrealStore(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            dim=surreal_env.dim,
            user=surreal_env.user,
            password=surreal_env.password,
        )

        # Act: N concurrent first-callers racing the SAME fresh instance.
        try:
            results = await asyncio.gather(
                *(fresh_store._ensure_connection() for _ in range(_RACE_CONCURRENT_CALLERS))
            )
        finally:
            await fresh_store.close()

        # Assert: every racing caller still gets a usable, signed-in
        # connection back — the race is about HOW MANY connections get
        # opened, not the correctness of any individual caller's result.
        assert len(results) == _RACE_CONCURRENT_CALLERS
        assert get_call_count() == 1, (
            f"expected exactly one underlying connection, got {get_call_count()} — "
            "the check-then-set race let concurrent first-callers each open their own"
        )

    async def test_surreal_manifest_opens_exactly_one_connection_under_concurrent_first_use(
        self, surreal_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch  # noqa: F811
    ) -> None:
        factory, get_call_count = _counting_connection_factory()
        monkeypatch.setattr("loremaster.index.surreal_manifest.AsyncSurreal", factory)
        fresh_manifest = SurrealManifest(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            user=surreal_env.user,
            password=surreal_env.password,
        )

        try:
            results = await asyncio.gather(
                *(fresh_manifest._ensure_connection() for _ in range(_RACE_CONCURRENT_CALLERS))
            )
        finally:
            await fresh_manifest.close()

        assert len(results) == _RACE_CONCURRENT_CALLERS
        assert get_call_count() == 1, (
            f"expected exactly one underlying connection, got {get_call_count()} — "
            "the check-then-set race let concurrent first-callers each open their own"
        )

    async def test_surreal_code_graph_opens_exactly_one_connection_under_concurrent_first_use(
        self, surreal_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch  # noqa: F811
    ) -> None:
        factory, get_call_count = _counting_connection_factory()
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
            results = await asyncio.gather(
                *(fresh_graph._ensure_connection() for _ in range(_RACE_CONCURRENT_CALLERS))
            )
        finally:
            await fresh_graph.close()

        assert len(results) == _RACE_CONCURRENT_CALLERS
        assert get_call_count() == 1, (
            f"expected exactly one underlying connection, got {get_call_count()} — "
            "the check-then-set race let concurrent first-callers each open their own"
        )


# ---------------------------------------------------------------------------
# P5-C1a, concern 2: metadata-shape reconciliation.
#
# ``records.chunk_to_record`` — the REAL, production translator every indexed
# chunk goes through — spreads a chunk's ``metadata`` dict TOP-LEVEL into the
# record payload (``**dict(chunk.metadata)``); it never nests it under a
# ``"metadata"`` key (see ``records.py``). The store's public API boundary
# must speak that SAME top-level shape in both directions: what goes in via
# ``upsert``/``replace_file`` must come back byte-equal (per key) from
# ``scroll`` and ``hybrid_search`` — regardless of whatever internal row
# shape the store chooses to persist it as.
# ---------------------------------------------------------------------------

# A representative source body for the metadata-shape tests — real Odoo-style
# domain code, not a placeholder.
_METADATA_TEST_SOURCE = (
    "def action_confirm(self):\n"
    "    for order in self:\n"
    "        order._check_stock_level()\n"
    "        order.write({'state': 'purchase'})\n"
    "    return True\n"
)


def _production_metadata(*, ident_text: str) -> dict[str, Any]:
    """A representative chunker metadata payload: nested dict, list, string,
    int and bool values — the actual shape a real chunker attaches, not a
    convenience synthetic chosen because the arithmetic comes out clean.

    ``ident_text`` is included because the ``chunk`` schema declares it a
    REQUIRED (non-``option``) top-level column
    (``surreal_schema._CHUNK_FIELD_SPECS``) that ``records.chunk_to_record``
    itself never populates — a real producer stamps it into
    ``Chunk.metadata`` before translation, which ``chunk_to_record``'s
    documented top-level spread then promotes to a first-class field. Using
    it here is not a test workaround; it is the only channel that exists
    today for that column, exercised exactly as production would use it.
    """
    return {
        "ident_text": ident_text,
        "docstring": "Confirm the purchase order and post the linked account move.",
        "decorators": ["api.model", "api.depends('state')"],
        "complexity": 7,
        "is_property": False,
        "signature": {"args": ["self"], "returns": "bool"},
        "call_sites": ["sale_order.py:88", "stock_picking.py:142"],
    }


def _production_record(
    *,
    tier: str,
    file_path: str,
    identity: str,
    metadata: dict[str, Any],
    chunk_type: str = "python_symbol",
    source_text: str = _METADATA_TEST_SOURCE,
    slug: str = SLUG,
) -> Record:
    """Build a chunk :class:`Record` via the REAL ``records.chunk_to_record``.

    Unlike the harness's ``chunk_record()`` (which stamps the PLACEHOLDER
    nested-``metadata`` shape), this goes through the SAME production
    translator ``indexer.py`` calls, so the resulting :class:`Record` payload
    is byte-identical in shape to what a real indexing run would upsert —
    the exact producer to consumer seam this contract pins.
    """
    chunk = Chunk(
        chunk_type=chunk_type,
        source_text=source_text,
        identity=identity,
        line_start=1,
        line_end=source_text.count("\n") + 1,
        metadata=metadata,
    )
    return chunk_to_record(
        chunk,
        slug=slug,
        tier=tier,
        file_path=file_path,
        content_hash=sha512_hex(source_text),
        mtime_ns=time.time_ns(),
    )


class TestMetadataShapeReconciliation:
    """P5-C1a, concern 2: the store's public API boundary speaks the SAME
    production payload shape ``records.chunk_to_record`` produces — chunker
    metadata keys spread top-level, no ``"metadata"`` wrapper key — in BOTH
    directions (write via ``upsert``/``replace_file``, read via
    ``scroll``/``hybrid_search``).

    LOAD-BEARING: every case here must FAIL RED against current code. The
    ``chunk`` table's SCHEMAFULL ``metadata`` column is a REQUIRED (non-
    ``option``) ``object FLEXIBLE`` field (``surreal_schema._CHUNK_FIELD_
    SPECS``) that a real ``chunk_to_record`` payload never populates (it has
    no ``"metadata"`` key at all — see the module note above); today's
    ``SurrealStore._chunk_content`` passes ``record.payload`` straight
    through as ``CONTENT``, so the engine rejects the write outright
    (verified live: ``Couldn't coerce value for field 'metadata' ...
    Expected object but found NONE``) — the store cannot persist a real
    production-shaped chunk at all today, not merely lose a few of its keys.
    """

    async def test_upsert_scroll_round_trips_production_shaped_metadata_top_level(
        self, store: SurrealStore
    ) -> None:
        # Arrange: a real chunk_to_record()-built record with representative,
        # multi-typed chunker metadata (nested dict, list, str, int, bool).
        dim = PRODUCTION_DIM
        file_path = "models/purchase_order.py"
        metadata = _production_metadata(ident_text="PurchaseOrder action_confirm")
        record = _production_record(
            tier=TIER_A,
            file_path=file_path,
            identity="PurchaseOrder.action_confirm",
            metadata=metadata,
        )

        # Act
        await store.upsert([(record, unit_vector(0, dim))])
        rows = await store.scroll({"file_path": file_path}, limit=_READ_ALL)

        # Assert: every key the production translator emitted — including
        # every metadata-origin key — round-trips PER-KEY EQUAL, not merely
        # "some subset survived".
        assert len(rows) == 1
        row = rows[0]
        for key, expected_value in record.payload.items():
            assert row.get(key) == expected_value, (
                f"payload key {key!r} did not round-trip: "
                f"expected {expected_value!r}, got {row.get(key)!r}"
            )
        # Duplication guard: no internal "metadata" wrapper rides along
        # alongside the flattened top-level copies (which would still pass the
        # per-key subset check above while silently doubling the data). The
        # pin is deliberately subset-shaped, not exact-key-set: read-back may
        # legitimately carry the store-DERIVED ident_text column a production
        # payload never supplies.
        assert "metadata" not in row

    async def test_replace_file_hybrid_search_round_trips_production_shaped_metadata(
        self, store: SurrealStore
    ) -> None:
        dim = PRODUCTION_DIM
        file_path = "models/account_move.py"
        metadata = _production_metadata(ident_text="AccountMove reconcile")
        record = _production_record(
            tier=TIER_A,
            file_path=file_path,
            identity="AccountMove.reconcile",
            metadata=metadata,
        )

        await store.replace_file(TIER_A, file_path, [(record, unit_vector(0, dim))])
        results = await store.hybrid_search(
            query_vector=unit_vector(0, dim), query_text="AccountMove reconcile", k=5
        )

        hit = next((candidate for candidate in results if candidate.key == record.point_id), None)
        assert hit is not None, "the production-shaped chunk should surface"
        for key, expected_value in record.payload.items():
            assert hit.payload.get(key) == expected_value, (
                f"Candidate payload key {key!r} did not round-trip: "
                f"expected {expected_value!r}, got {hit.payload.get(key)!r}"
            )
        # Duplication guard (same as the scroll seam): no internal "metadata"
        # wrapper riding along the fused Candidate payload.
        assert "metadata" not in hit.payload

    async def test_metadata_key_matching_declared_column_does_not_corrupt_round_trip(
        self, store: SurrealStore
    ) -> None:
        # A chunker-attached metadata key that happens to SHARE A NAME with a
        # declared chunk column (``chunk_type``) is a realistic accident (a
        # chunker that also stamps its own classification label). Python's
        # dict-merge order in ``chunk_to_record`` (metadata spread LAST)
        # resolves the collision to ONE value before the record ever reaches
        # the store — that resolved value is the ground truth this test
        # documents (independent of the store) and then requires the store to
        # persist FAITHFULLY as the DECLARED column, usable for filtering,
        # never silently redirected into an internal metadata blob and lost
        # from column-based scroll/delete.
        dim = PRODUCTION_DIM
        file_path = "models/stock_picking.py"
        shadowing_value = "stale_chunker_classification"
        metadata = _production_metadata(ident_text="StockPicking action_done")
        metadata["chunk_type"] = shadowing_value
        record = _production_record(
            tier=TIER_A,
            file_path=file_path,
            identity="StockPicking.action_done",
            metadata=metadata,
            chunk_type="python_symbol",
        )
        # Ground truth, independent of the store: chunk_to_record's own
        # dict-merge already resolved the collision to the metadata's value
        # (metadata is spread LAST in records.chunk_to_record's payload dict
        # literal, so it wins) — this is records.py's pinned, existing
        # behaviour, not something this test invents.
        assert record.payload["chunk_type"] == shadowing_value

        await store.upsert([(record, unit_vector(0, dim))])

        # The resolved value must be usable as the DECLARED filter column —
        # not silently dropped or hidden inside an opaque metadata blob.
        matches = await store.scroll({"chunk_type": shadowing_value}, limit=_READ_ALL)
        assert len(matches) == 1
        assert matches[0]["identity"] == "StockPicking.action_done"
        # Duplication guard (same as the other two seams): no internal
        # "metadata" wrapper riding along the returned row.
        assert "metadata" not in matches[0]
        # The pre-collision value never independently survives anywhere,
        # confirming the collision resolved to ONE value, not a silent
        # duplicate under a second key.
        stale = await store.scroll({"chunk_type": "python_symbol"}, limit=_READ_ALL)
        assert stale == []

    async def test_non_dict_metadata_payload_key_is_rejected_loudly(
        self, store: SurrealStore
    ) -> None:
        # C1-audit finding #1: a chunker metadata key literally named
        # ``metadata`` with a NON-dict value cannot be represented faithfully
        # (a dict value is the documented legacy nested-producer shape; a
        # scalar is neither shape). Silently dropping it — the pre-fix
        # behaviour — is data loss; the store must refuse the write LOUDLY
        # and persist nothing.
        dim = PRODUCTION_DIM
        file_path = "models/res_partner.py"
        metadata = _production_metadata(ident_text="ResPartner name_get")
        metadata["metadata"] = "a-string-label"  # non-dict reserved-name value
        record = _production_record(
            tier=TIER_A,
            file_path=file_path,
            identity="ResPartner.name_get",
            metadata=metadata,
        )

        with pytest.raises(SurrealStoreError):
            await store.upsert([(record, unit_vector(0, dim))])

        assert await store.scroll({"file_path": file_path}, limit=_READ_ALL) == []

    async def test_metadata_key_named_embedding_is_rejected_loudly(
        self, store: SurrealStore
    ) -> None:
        # C1-audit finding #1 (mirror case): a chunker metadata key named
        # ``embedding`` would nest into the metadata bucket on write and then
        # reappear TOP-LEVEL on read-merge — a spurious vector-column leak the
        # ``SELECT * OMIT embedding`` projection cannot catch. Reserved name:
        # the store must refuse the write LOUDLY and persist nothing. Exercised
        # through replace_file to cover the second write entrance.
        dim = PRODUCTION_DIM
        file_path = "models/res_users.py"
        metadata = _production_metadata(ident_text="ResUsers has_group")
        metadata["embedding"] = "chunker-emitted-lookalike"
        record = _production_record(
            tier=TIER_A,
            file_path=file_path,
            identity="ResUsers.has_group",
            metadata=metadata,
        )

        with pytest.raises(SurrealStoreError):
            await store.replace_file(TIER_A, file_path, [(record, unit_vector(0, dim))])

        assert await store.scroll({"file_path": file_path}, limit=_READ_ALL) == []


# ---------------------------------------------------------------------------
# P5-C1c (SurrealDB docs-audit, ledger #28), hardening #1: ``ensure_ready``
# must be LOUD on ANY failing DDL statement, not just the first.
#
# The installed SDK (``surrealdb`` 2.0.0) ``query()`` validates ONLY the FIRST
# statement of a multi-statement string (it inspects ``response["result"][0]``
# and returns ``result[0]["result"]``); a LATER statement's semantic rejection
# comes back with per-statement ``status == "ERR"`` while ``query()`` itself
# raises NOTHING. Verified live against the dev server (3.1.5): splicing a
# syntactically valid but semantically invalid ``DEFINE INDEX`` into the
# MIDDLE of the real ``generate_ddl()`` output leaves every statement AFTER it
# still applied (the rest of the schema is built normally) while ``query()``
# returns ``None`` and the poisoned index itself is confirmed absent
# afterward (``INFO FOR TABLE`` never lists it) — a genuine execution-time
# semantic rejection, not a parse error that would abort the whole batch
# before any statement ran. ``ensure_ready`` applies its DDL through a bare
# ``connection.query(ddl)`` call, so today it reports success on a schema
# that was only PARTIALLY applied.
# ---------------------------------------------------------------------------

# The ghost index/field names the invalid DDL statement below references —
# named constants (never re-typed inline) so the "why did this fail" story
# stays in one place.
_GHOST_INDEX_NAME = "ghost_idx_probe"
_GHOST_FIELD_NAME = "ghost_field_xyz_probe"


def _invalid_ddl_statement(table: str) -> str:
    """A syntactically valid ``DEFINE INDEX`` that 3.1.5 rejects AT EXECUTION.

    Indexing a field that was never ``DEFINE FIELD``'d on ``table`` PARSES
    cleanly (valid SurrealQL grammar) but fails when the engine actually
    tries to build the index. Verified live via ``query_raw`` against the dev
    server: the statement's per-statement result comes back
    ``status: "ERR"``, ``result: "The field '<field>' does not exist"`` —
    while the SAME string run through the SDK's ``query()`` raises nothing at
    all, and the ghost index is confirmed absent afterward.
    """
    return (
        f"DEFINE INDEX IF NOT EXISTS {_GHOST_INDEX_NAME} ON {table} "
        f"FIELDS {_GHOST_FIELD_NAME}"
    )


def _ddl_with_late_invalid_statement(ddl: str, table: str) -> str:
    """Splice :func:`_invalid_ddl_statement` into the MIDDLE of a real DDL string.

    A middle (neither first nor last) position proves the SDK's
    first-statement-only check misses a failure ANYWHERE downstream of the
    first statement — not merely a special-cased "last statement" gap.
    """
    statements = [stmt.strip() for stmt in ddl.strip().split(";\n") if stmt.strip()]
    middle_index = len(statements) // 2
    statements.insert(middle_index, _invalid_ddl_statement(table))
    return ";\n".join(statements) + ";\n"


class TestEnsureReadyRaisesOnLateDdlFailure:
    """P5-C1c hardening #1: a LATER DDL statement's rejection must surface.

    LOAD-BEARING: must FAIL RED against current code — ``ensure_ready``
    applies its DDL via a bare ``connection.query(ddl)`` call, which (per the
    module docstring above) inspects only the first statement and swallows a
    later ``ERR`` completely; ``ensure_ready`` returns normally today even
    though a real statement in its own schema was rejected by the engine.
    """

    async def test_ensure_ready_raises_on_a_semantically_invalid_late_ddl_statement(
        self, surreal_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch  # noqa: F811
    ) -> None:
        # Arrange: the REAL DDL (same generator, same kwargs ``ensure_ready``
        # calls today), poisoned with one invalid statement mid-way through.
        real_ddl = generate_ddl(dim=surreal_env.dim)
        poisoned_ddl = _ddl_with_late_invalid_statement(real_ddl, CHUNK_TABLE)

        def _poisoned_generate_ddl(*, dim: int, analyzer_name: str) -> str:
            return poisoned_ddl

        monkeypatch.setattr("loremaster.store.surreal.generate_ddl", _poisoned_generate_ddl)
        broken_store = SurrealStore(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            dim=surreal_env.dim,
            user=surreal_env.user,
            password=surreal_env.password,
        )

        try:
            # Act / Assert: the failing statement must surface as a STORE
            # error (a domain/schema rejection — the transport is perfectly
            # healthy) rather than a silent success.
            with pytest.raises(SurrealStoreError) as exc_info:
                await broken_store.ensure_ready()
            assert type(exc_info.value) is SurrealStoreError
            assert not isinstance(exc_info.value, SurrealConnectionError)
            # A domain rejection must never throw away a healthy connection.
            assert broken_store._connection is not None
        finally:
            await broken_store.close()


# ---------------------------------------------------------------------------
# P5-C1c, hardening #2: ``_drop_connection`` must be a compare-and-swap, not
# an unconditional null.
#
# A LATE caller can hold a STALE connection reference captured BEFORE an
# earlier self-heal already replaced ``self._connection`` with a fresh one.
# Today's ``_drop_connection`` nulls ``self._connection`` unconditionally —
# regardless of whether the connection object it was HANDED is still the live
# one — so that late caller wipes out a perfectly healthy, freshly-reconnected
# handle out from under every other in-flight caller.
# ---------------------------------------------------------------------------


def _plain_counting_connection_factory() -> tuple[Callable[[str], Any], Callable[[], int]]:
    """A drop-in ``AsyncSurreal`` replacement that COUNTS every real connection
    it opens — a lighter sibling of :func:`_counting_connection_factory` with
    NO artificial signin delay, because this test drives its callers
    SEQUENTIALLY (there is no concurrent race to widen here).

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
    is ``self._connection = None; await self._safe_close(connection)``
    unconditionally, with no check that ``connection`` is still
    ``self._connection`` before nulling it.
    """

    async def test_dropping_a_stale_connection_after_a_reconnect_leaves_the_live_one_intact(
        self, surreal_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch  # noqa: F811
    ) -> None:
        # Arrange: a fresh store; count every real connection opened.
        factory, get_call_count = _plain_counting_connection_factory()
        monkeypatch.setattr("loremaster.store.surreal.AsyncSurreal", factory)
        fresh_store = SurrealStore(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            dim=surreal_env.dim,
            user=surreal_env.user,
            password=surreal_env.password,
        )
        try:
            # connection A, then simulate an EARLIER self-heal that already
            # replaced it with connection B (bypassing ``_drop_connection``
            # directly, so the STALE reference to A survives independently —
            # exactly as a slow concurrent caller would still be holding it).
            stale_connection = await fresh_store._ensure_connection()
            assert get_call_count() == 1
            # cast: keep mypy at the declared union — a bare None assignment
            # narrows the attribute to None across the rest of the block
            # (method calls never re-widen it), making later asserts
            # 'unreachable' under warn_unreachable.
            fresh_store._connection = cast("_SurrealConnection | None", None)
            live_connection = await fresh_store._ensure_connection()
            assert get_call_count() == 2
            assert live_connection is not stale_connection

            # Act: a LATE caller drops the STALE connection A — AFTER B is
            # already the live, cached handle.
            await fresh_store._drop_connection(stale_connection)

            # Assert: B survives untouched — a compare-and-swap, not an
            # unconditional null.
            assert fresh_store._connection is live_connection

            # And the store keeps working by REUSING B — no third connection
            # is opened just because a stale handle was dropped.
            await fresh_store.ensure_ready()
            assert get_call_count() == 2
            assert fresh_store._connection is live_connection
        finally:
            await fresh_store.close()


# ---------------------------------------------------------------------------
# P5-C1c, hardening #3 (SurrealDB docs-audit follow-up, ledger #28): a raw
# ``KeyError`` from the SDK's OWN response-routing must be classified as a
# connection fault, not propagate untyped.
#
# Probe-confirmed live (throwaway 3.1.5 container): when the socket drops
# with queries IN FLIGHT on one shared connection, the installed SDK (2.0.0)
# raises a raw ``builtins.KeyError(<request-uuid>)`` from its response
# routing on EVERY in-flight future (6/6 in the probe) — NOT
# ``asyncio.CancelledError`` (never reproduced), and NOT anything in
# ``_CONNECTION_ERRORS`` (``OSError`` / ``SurrealError`` /
# ``WebSocketException``). Only the NEXT call on the dead connection heals via
# ``ConnectionClosedError``. Today's ``_query`` except clause only catches
# ``_CONNECTION_ERRORS``, so this ``KeyError`` propagates completely
# untyped — never wrapped, never triggering the self-heal.
#
# SCOPING NOTE for the GREEN implementer: both try blocks this classification
# must widen to catch ``KeyError`` in — ``_query``'s
# ``return await connection.query(statement, params or {})`` and
# ``_txn_query_raw``'s ``await connection.query_raw(...)`` /
# ``connection.check_response_for_error(...)`` — contain ONLY the SDK call
# itself (verified by reading both try bodies), so classifying ANY KeyError
# raised inside these specific try blocks as a connection fault cannot
# misclassify a KeyError from our own code — there is no own-code path inside
# either try block today. Keep the except scoped this tight; do not widen the
# try block to also cover post-processing logic that might raise its own
# KeyError.
# ---------------------------------------------------------------------------

# A realistic SDK request-correlation id — the SDK routes in-flight requests
# by a UUID4 key, so the raw KeyError this bug raises always carries one.
_SDK_ROUTING_KEY_ERROR_TOKEN = "3fae6a02-9c1e-4c1b-8f3a-77c2e4a9b001"


class TestQuerySeamSdkKeyErrorClassification:
    """P5-C1c hardening #3: a KeyError raised BY THE SDK CALL ITSELF inside
    ``_query`` must surface as ``SurrealConnectionError`` and self-heal —
    mirrors the identical seam on ``SurrealManifest``/``SurrealCodeGraph``
    (see their own test files' matching section).

    LOAD-BEARING: must FAIL RED against current code — ``_query``'s except
    clause is ``except _CONNECTION_ERRORS``; ``KeyError`` is none of those, so
    it propagates completely untyped today.
    """

    async def test_sdk_routing_key_error_surfaces_as_connection_error_and_heals(
        self, surreal_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch  # noqa: F811
    ) -> None:
        # Arrange: a fresh, ready store on a REAL connection (counted, so the
        # eventual reconnect can be pinned to exactly one NEW connection).
        factory, get_call_count = _plain_counting_connection_factory()
        monkeypatch.setattr("loremaster.store.surreal.AsyncSurreal", factory)
        live_store = SurrealStore(
            url=surreal_env.url,
            namespace=surreal_env.namespace,
            database=surreal_env.database,
            dim=surreal_env.dim,
            user=surreal_env.user,
            password=surreal_env.password,
        )
        try:
            await live_store.ensure_ready()
            assert get_call_count() == 1
            broken_connection = live_store._connection
            assert broken_connection is not None

            # A deterministic stand-in for the SDK's own response-routing
            # failure (see the module note above) — patched on the LIVE
            # connection INSTANCE itself, exactly the technique
            # ``_counting_connection_factory`` already uses for ``signin``.
            async def _raise_routing_key_error(*args: object, **kwargs: object) -> Any:
                raise KeyError(_SDK_ROUTING_KEY_ERROR_TOKEN)

            monkeypatch.setattr(broken_connection, "query", _raise_routing_key_error)

            # Act / Assert: the raw KeyError must surface as a typed
            # SurrealConnectionError (never bare) AND drop the connection.
            with pytest.raises(SurrealConnectionError):
                await live_store.count()
            assert live_store._connection is None

            # Recovery: the NEXT call reconnects — exactly one NEW
            # connection, never a wedge and never a silent reconnect storm.
            assert await live_store.count() == 0
            assert get_call_count() == 2
        finally:
            await live_store.close()


class _FakeSdkRoutingKeyErrorConnection:
    """A minimal stand-in for a live SDK connection whose ``query_raw`` raises
    the SDK's own raw response-routing ``KeyError`` (see the module note
    above) — deterministic, no live server or socket kill needed, since
    :func:`~loremaster.store._txn.execute_transaction` is fully
    dependency-injected (``acquire``/``drop``), unlike the single-statement
    ``_query`` seam above which needs a real connected instance.
    """

    async def query_raw(self, statement: str, params: dict[str, Any]) -> dict[str, Any]:
        raise KeyError(_SDK_ROUTING_KEY_ERROR_TOKEN)

    def check_response_for_error(self, response: Any, method: str) -> None:  # pragma: no cover
        raise AssertionError("query_raw must raise before this is ever reached")


class TestTxnSdkKeyErrorClassification:
    """P5-C1c hardening #3, shared seam: :func:`~loremaster.store._txn.
    execute_transaction`'s ``query_raw`` call must classify the SAME SDK
    routing ``KeyError`` the single-statement ``_query`` seams do — the
    identical gap lives in the SHARED ``_txn_query_raw`` (used by
    ``replace_file`` / ``replace`` / ``build_file_graph`` /
    ``delete_file_graph`` across all three ported classes), so this pins it
    ONCE against the shared function directly rather than duplicating the
    probe through all three callers (the classification logic is not
    per-class code, unlike the compare-and-swap hardening above).

    LOAD-BEARING: must FAIL RED against current code — ``_txn_query_raw``'s
    except clause is ``except _CONNECTION_ERRORS`` (same tuple as
    ``_query``); a raw ``KeyError`` from ``query_raw`` propagates completely
    untyped, and ``drop`` is never invoked.
    """

    async def test_sdk_routing_key_error_surfaces_as_connection_error_and_drops(self) -> None:
        # Arrange: a fake connection whose query_raw call IS the failure —
        # no live server needed, execute_transaction is fully DI'd.
        fake_connection = _FakeSdkRoutingKeyErrorConnection()
        dropped: list[Any] = []

        async def _acquire() -> _SurrealConnection:
            return cast("_SurrealConnection", fake_connection)

        async def _drop(connection: Any) -> None:
            dropped.append(connection)

        # Act / Assert: the raw KeyError must surface as SurrealConnectionError
        # and the transaction's connection must be dropped exactly once.
        with pytest.raises(SurrealConnectionError):
            await execute_transaction(
                "BEGIN;\nDELETE chunk;\nCOMMIT;\n",
                {},
                acquire=_acquire,
                drop=_drop,
                url="ws://127.0.0.1:19555/rpc",  # unreachable — never actually dialed
            )
        assert dropped == [fake_connection]



# ===========================================================================
# Ledger #31 (c2-security, low): error-message hygiene. A rolled-back
# transaction's raw engine detail can echo bound VALUES back through the
# ASSERT/coercion rejection text (e.g. "Found 'the-actual-value' for field
# ..."), and that raw text used to ride straight into ``SurrealStoreError``'s
# message — which will flow to MCP clients in P8. The contract pinned here:
#
#   1. The FULL engine detail is logged server-side (``logger.error``,
#      structured: statement index, status, the raw engine result text)
#      BEFORE raising.
#   2. The RAISED ``SurrealStoreError`` carries a CLASSIFIED, generic
#      message: which statement failed (index/count), a short engine ERROR
#      CLASS if extractable (e.g. "assert violation", "field coercion"), and
#      a "see the server log" correlation hint — but NEVER the raw engine
#      text or any value it could carry.
#   3. The retryable-conflict detection (:data:`_RETRYABLE_CONFLICT_MARKER`)
#      still reads the RAW text internally — only the RAISED message changed.
#
# Every case here is fully DI'd against a scripted fake connection (the same
# pattern as ``TestTxnSdkKeyErrorClassification`` above) — no live server, no
# genuine write-write race, fully deterministic.
# ===========================================================================

# A synthetic engine rejection carrying a value that must NEVER reach the
# raised message — stands in for a real ASSERT/coercion rejection that echoes
# the offending bound value back verbatim (the finding's exact shape).
_SENSITIVE_MARKER = "TOP-SECRET-BOUND-VALUE-9f3a1c"
_SENSITIVE_ENGINE_TEXT = (
    f"Found '{_SENSITIVE_MARKER}' for field `name`, with record "
    f"`chunk:abc123`, but expected the value to fulfil the following "
    f"assertion: $value != NONE"
)

# A field-coercion rejection — a distinct engine failure SHAPE from an ASSERT
# violation, so the classifier's two branches are each independently pinned.
_COERCION_ENGINE_TEXT = "Couldn't coerce value for field `sub_ordinal`: Expected int"

# The exact live retryable-conflict text (see ``_txn._RETRYABLE_CONFLICT_MARKER``).
_CONFLICT_ENGINE_TEXT = (
    f"Cannot COMMIT: Transaction conflict: Resource busy. This transaction "
    f"{_RETRYABLE_CONFLICT_MARKER}"
)

_OK_STATEMENT: dict[str, Any] = {"status": "OK", "result": None}


def _err_response(*, result_text: str, leading_ok: int = 0, trailing_ok: int = 0) -> dict[str, Any]:
    """Build a ``query_raw``-shaped response: ``leading_ok`` OK statements,
    then one ERR statement carrying ``result_text``, then ``trailing_ok`` more
    OK statements — the exact shape :func:`~loremaster.store._txn.
    _failed_statements` inspects. Leading/trailing OK counts let a test pin
    the failed statement's INDEX distinctly from the total statement COUNT.
    """
    entries = [dict(_OK_STATEMENT) for _ in range(leading_ok)]
    entries.append({"status": "ERR", "result": result_text})
    entries.extend(dict(_OK_STATEMENT) for _ in range(trailing_ok))
    return {"result": entries}


@dataclass
class _TxnRollbackFakeConnection:
    """Stand-in SDK connection for the ledger #31 hygiene + retry pins:
    scripts a SEQUENCE of ``query_raw`` responses (one consumed per attempt),
    in the SDK's raw multi-statement shape — so the classified-message /
    server-log / retry-preserved contract is pinned deterministically,
    without a live server or a genuine write-write race.
    """

    responses: list[dict[str, Any]]
    calls: int = field(default=0, init=False)

    async def query_raw(self, statement: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self.responses[self.calls]
        self.calls += 1
        return response

    def check_response_for_error(self, response: Any, method: str) -> None:
        """No RPC-level error in these canned per-statement responses."""
        return None


def _never_drop() -> Callable[[Any], Awaitable[None]]:
    """A ``drop`` callback that fails the test if invoked — a domain
    rejection (or a retryable conflict) must never tear down a healthy
    connection, only a genuine transport failure may.
    """

    async def _drop(connection: Any) -> None:
        raise AssertionError("a domain rejection must never drop the connection")

    return _drop


async def _run_execute_transaction(
    fake: _TxnRollbackFakeConnection, *, drop: Callable[[Any], Awaitable[None]] | None = None
) -> None:
    """Drive ``execute_transaction`` against ``fake`` with a fixed poison
    statement/params — the shape is irrelevant to these tests since the fake
    ignores it entirely and only replays scripted responses.
    """

    async def _acquire() -> _SurrealConnection:
        return cast("_SurrealConnection", fake)

    await execute_transaction(
        "BEGIN;\nUPDATE chunk SET name = $name;\nCOMMIT;\n",
        {"name": "poison"},
        acquire=_acquire,
        drop=drop or _never_drop(),
        url="ws://127.0.0.1:19555/rpc",  # unreachable — never actually dialed
    )


class TestTxnRollbackMessageHygiene:
    """The RAISED message is classified/generic; the engine's raw
    per-statement detail is logged server-side, never echoed to the caller."""

    async def test_raised_message_never_echoes_the_raw_engine_text(self) -> None:
        fake = _TxnRollbackFakeConnection(
            responses=[_err_response(result_text=_SENSITIVE_ENGINE_TEXT, leading_ok=2, trailing_ok=2)]
        )
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(fake)

        message = str(exc_info.value)
        assert _SENSITIVE_ENGINE_TEXT not in message
        assert _SENSITIVE_MARKER not in message
        assert fake.calls == 1  # non-retryable: never retried

    async def test_raised_message_names_the_failed_statement_position_and_class(self) -> None:
        fake = _TxnRollbackFakeConnection(
            responses=[_err_response(result_text=_SENSITIVE_ENGINE_TEXT, leading_ok=2, trailing_ok=2)]
        )
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(fake)

        message = str(exc_info.value)
        # 2 leading OK + the ERR (index 2, 1-based ordinal 3) + 2 trailing OK
        # = 5 statements total: the ERR is neither first nor last, so the
        # ordinal and the count are DISTINCT numbers in the message.
        assert "statement 3 of 5" in message
        assert "assert violation" in message.lower()
        assert "server log" in message.lower()

    async def test_field_coercion_rejection_is_classified_distinctly(self) -> None:
        fake = _TxnRollbackFakeConnection(
            responses=[_err_response(result_text=_COERCION_ENGINE_TEXT, leading_ok=1)]
        )
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(fake)

        message = str(exc_info.value)
        assert _COERCION_ENGINE_TEXT not in message
        assert "field coercion" in message.lower()

    async def test_server_log_carries_the_full_engine_detail_before_raising(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        fake = _TxnRollbackFakeConnection(
            responses=[_err_response(result_text=_SENSITIVE_ENGINE_TEXT, leading_ok=2, trailing_ok=2)]
        )
        with caplog.at_level(logging.ERROR, logger="loremaster.store._txn"):
            with pytest.raises(SurrealStoreError):
                await _run_execute_transaction(fake)

        error_records = [record for record in caplog.records if record.levelno == logging.ERROR]
        assert error_records, "the full engine detail must be logged server-side"
        record = error_records[0]
        logged = " ".join(
            str(value) for value in (record.getMessage(), getattr(record, "engine_result", ""))
        )
        assert _SENSITIVE_ENGINE_TEXT in logged
        assert getattr(record, "statement_index", None) == 2  # 0-based: the 3rd entry
        assert getattr(record, "statement_count", None) == 5
        assert getattr(record, "status", None) == "ERR"


class TestTxnMalformedResponseHygiene:
    """``_failed_statements``' malformed-response guard (a shape the engine
    should never return) must ALSO never echo the raw response into the
    raised message — only into the server-side log.
    """

    async def test_malformed_response_message_never_echoes_the_raw_response(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        malformed = {"result": _SENSITIVE_MARKER}  # not a list — the poison shape
        fake = _TxnRollbackFakeConnection(responses=[malformed])

        with caplog.at_level(logging.ERROR, logger="loremaster.store._txn"):
            with pytest.raises(SurrealStoreError) as exc_info:
                await _run_execute_transaction(fake)

        assert _SENSITIVE_MARKER not in str(exc_info.value)
        error_records = [record for record in caplog.records if record.levelno == logging.ERROR]
        assert error_records
        logged = " ".join(
            str(value)
            for value in (error_records[0].getMessage(), getattr(error_records[0], "response", ""))
        )
        assert _SENSITIVE_MARKER in logged


class TestTxnRetryBehaviourUnchanged:
    """The conflict-retry decision (``_should_retry`` / ``_is_retryable_conflict``)
    still reads the RAW engine text internally — only the RAISED message
    changed; the retry/no-retry behaviour itself must be unchanged.
    """

    async def test_retryable_conflict_is_retried_and_succeeds_silently(self) -> None:
        fake = _TxnRollbackFakeConnection(
            responses=[
                _err_response(result_text=_CONFLICT_ENGINE_TEXT),
                {"result": [dict(_OK_STATEMENT)]},
            ]
        )

        await _run_execute_transaction(fake)  # must NOT raise

        assert fake.calls == 2  # one conflict, one successful retry — invisible to the caller

    async def test_sustained_conflict_still_raises_after_bounded_attempts(self) -> None:
        fake = _TxnRollbackFakeConnection(
            responses=[
                _err_response(result_text=_CONFLICT_ENGINE_TEXT) for _ in range(_MAX_TXN_CONFLICT_ATTEMPTS)
            ]
        )

        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(fake)

        assert fake.calls == _MAX_TXN_CONFLICT_ATTEMPTS  # bounded, not unbounded
        assert _CONFLICT_ENGINE_TEXT not in str(exc_info.value)
        assert "retryable conflict" in str(exc_info.value).lower()

    async def test_non_retryable_rejection_is_never_retried(self) -> None:
        fake = _TxnRollbackFakeConnection(
            responses=[_err_response(result_text=_SENSITIVE_ENGINE_TEXT)]
        )

        with pytest.raises(SurrealStoreError):
            await _run_execute_transaction(fake)

        assert fake.calls == 1


# ===========================================================================
# P8a: the ``trace`` observability write path — ``record_trace``.
#
# ``trace`` is lore's per-tool-invocation OBSERVABILITY row, written async by the
# mcp role (the async fire-and-forget EMISSION that schedules these writes, and
# the aggregates over them, are a later serving-layer phase — P8d). P8a delivers
# only the awaitable STORE-side write: ``record_trace`` persists one row — the six
# core fields plus the two optional accounting columns — with ``ts`` stamped
# server-side by the schema's ``DEFAULT time::now()`` so the writer never computes
# it. These pins run against BOTH the real store and the adversarial in-memory
# fake via the parametrized ``trace_store`` fixture — the fake-vs-real PARITY PIN
# (mirrors ``test_task_ledger.py``'s ``task_ledger_factory``): a behaviour the
# fake gets wrong, or too friendly, shows up as a real-vs-fake divergence rather
# than a fake-only green.
#
# ``session`` is a SurrealDB PROTECTED variable, so the write MUST bind a single
# CONTENT object (``session`` as an object KEY) rather than ``SET session =
# $session`` (rejected: "'session' is a protected variable and cannot be set").
# ===========================================================================

# Realistic lore-domain trace fixtures (a real tool name, a real SHA-512 params
# digest, a real fleet session id) — never convenience placeholders.
_TRACE_TOOL = "lore_search_code"
_TRACE_PARAMS_HASH = sha512_hex("query=PurchaseOrder.action_confirm&k=8&tier=custom")
_TRACE_HIT_COUNT = 8
# Fractional: the schema types ``latency_ms`` as ``number``; an ``int`` column
# would silently truncate a sub-millisecond latency.
_TRACE_LATENCY_MS = 42.5
_TRACE_SESSION = "orchestrator-session-7f3a"
_TRACE_TOKEN_COST = 1536
_TRACE_MODEL = "voyage-4-large"

# The recent-``ts`` sanity window — mirrors ``test_task_ledger``'s
# ``_TIMESTAMP_TOLERANCE`` / ``test_surreal_schema``'s ``_CLOCK_SKEW_ALLOWANCE``:
# loose enough for container/CI clock jitter, tight enough to catch a
# wrong-epoch / stale-clock / no-default stamp.
_TRACE_TS_TOLERANCE = timedelta(seconds=30)


@pytest_asyncio.fixture(params=["real", "fake"])
async def trace_store(request: pytest.FixtureRequest) -> AsyncIterator[SurrealStore]:
    """A ready store for the ``record_trace`` parity pins — parametrized over BOTH
    the real SurrealDB-backed :class:`SurrealStore` and the adversarial in-memory
    :class:`FakeSurrealStore`.

    Mirrors ``test_task_ledger.py``'s ``task_ledger_factory``: the ``"real"``
    branch deliberately does NOT depend on the ``surreal_env`` fixture (resolving
    one async fixture from inside another async fixture's own body re-enters
    pytest-asyncio 1.4's shared function-scoped ``Runner`` — a documented live
    ``RuntimeError``), so it calls the SAME underlying harness helpers
    ``surreal_env`` itself calls (``make_env`` / ``connect_admin`` /
    ``drop_database``) directly, keeping the identical isolated-throwaway-database
    guarantee without touching pytest's fixture graph. The ``"fake"`` branch never
    touches the SurrealDB harness at all.
    """
    if request.param == "real":
        env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()
        live_store = SurrealStore(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            dim=env.dim,
            user=env.user,
            password=env.password,
        )
        await live_store.ensure_ready()
        try:
            yield live_store
        finally:
            await live_store.close()
            await drop_database(env)
    else:
        fake_store = fake_surreal_trio(dim=PRODUCTION_DIM).store
        await fake_store.ensure_ready()
        # FakeSurrealStore satisfies the record_trace contract behaviourally (that
        # IS this parity pin); it shares no base class with SurrealStore, so the
        # cast tells mypy what the suite proves.
        yield cast(SurrealStore, fake_store)


async def _recorded_traces(trace_store: Any) -> list[dict[str, Any]]:
    """Read back every persisted trace row, uniformly across real + fake.

    The real store has NO public trace-read API — P8a is write-path only;
    aggregates are P8d — so the REAL rows are read through the store's own private
    ``_query`` seam (a TEST introspection, not a store API), while the FAKE exposes
    a ``recorded_traces`` oracle. NEITHER backend promises insertion order (the
    real engine returns rows unordered without an ``ORDER BY``; the fake
    deliberately reorders), so every caller compares as an UNORDERED collection.
    """
    if isinstance(trace_store, FakeSurrealStore):
        return trace_store.recorded_traces()
    raw = await trace_store._query(f"SELECT * FROM {TRACE_TABLE}")
    return [row for row in raw if isinstance(row, dict)] if isinstance(raw, list) else []


class TestRecordTrace:
    """``record_trace`` persists one observability row — the six core fields,
    server-stamped ``ts``, and the two optional accounting columns. Parity: every
    case runs against BOTH the real store and the adversarial fake.
    """

    async def test_record_trace_persists_all_six_core_fields(
        self, trace_store: SurrealStore
    ) -> None:
        await trace_store.record_trace(
            tool=_TRACE_TOOL,
            params_hash=_TRACE_PARAMS_HASH,
            hit_count=_TRACE_HIT_COUNT,
            latency_ms=_TRACE_LATENCY_MS,
            session=_TRACE_SESSION,
        )
        rows = await _recorded_traces(trace_store)
        assert len(rows) == 1
        row = rows[0]
        assert row["tool"] == _TRACE_TOOL
        assert row["params_hash"] == _TRACE_PARAMS_HASH
        assert row["hit_count"] == _TRACE_HIT_COUNT
        assert row["latency_ms"] == _TRACE_LATENCY_MS  # fractional survives (number)
        assert row["session"] == _TRACE_SESSION

    async def test_record_trace_generates_ts_server_side(
        self, trace_store: SurrealStore
    ) -> None:
        # ``record_trace`` takes NO ts argument — the ts is generated server-side
        # (the schema's ``DEFAULT time::now()``), so the async writer never has to
        # compute the ingestion instant itself. It must come back tz-aware and
        # inside this call's wall-clock window.
        before = datetime.now(UTC)
        await trace_store.record_trace(
            tool=_TRACE_TOOL,
            params_hash=_TRACE_PARAMS_HASH,
            hit_count=_TRACE_HIT_COUNT,
            latency_ms=_TRACE_LATENCY_MS,
            session=_TRACE_SESSION,
        )
        after = datetime.now(UTC)
        rows = await _recorded_traces(trace_store)
        assert len(rows) == 1
        ts = rows[0]["ts"]
        assert isinstance(ts, datetime)
        assert ts.tzinfo is not None, "ts must be timezone-aware (fleet-comparable), not naive"
        assert before - _TRACE_TS_TOLERANCE <= ts <= after + _TRACE_TS_TOLERANCE

    async def test_record_trace_stores_optional_accounting_columns_when_given(
        self, trace_store: SurrealStore
    ) -> None:
        await trace_store.record_trace(
            tool=_TRACE_TOOL,
            params_hash=_TRACE_PARAMS_HASH,
            hit_count=_TRACE_HIT_COUNT,
            latency_ms=_TRACE_LATENCY_MS,
            session=_TRACE_SESSION,
            token_cost=_TRACE_TOKEN_COST,
            model=_TRACE_MODEL,
        )
        rows = await _recorded_traces(trace_store)
        assert len(rows) == 1
        assert rows[0]["token_cost"] == _TRACE_TOKEN_COST
        assert rows[0]["model"] == _TRACE_MODEL

    async def test_record_trace_stores_none_cleanly_when_optionals_omitted(
        self, trace_store: SurrealStore
    ) -> None:
        # The two ``option`` columns store NONE cleanly when omitted (absent/None
        # on read-back) — a writer that skips accounting never poisons the row.
        await trace_store.record_trace(
            tool=_TRACE_TOOL,
            params_hash=_TRACE_PARAMS_HASH,
            hit_count=_TRACE_HIT_COUNT,
            latency_ms=_TRACE_LATENCY_MS,
            session=_TRACE_SESSION,
        )
        rows = await _recorded_traces(trace_store)
        assert len(rows) == 1
        assert rows[0].get("token_cost") is None
        assert rows[0].get("model") is None

    async def test_record_trace_appends_distinct_rows_never_dedups(
        self, trace_store: SurrealStore
    ) -> None:
        # A trace is an append-only observability EVENT, never keyed/deduped: two
        # identical-content ``record_trace`` calls persist TWO distinct rows (the
        # anti-dedup seam, mirroring the task ledger's distinct-duplicate-subjects
        # pin). Compared as an unordered count — neither backend promises order.
        for _ in range(2):
            await trace_store.record_trace(
                tool=_TRACE_TOOL,
                params_hash=_TRACE_PARAMS_HASH,
                hit_count=_TRACE_HIT_COUNT,
                latency_ms=_TRACE_LATENCY_MS,
                session=_TRACE_SESSION,
            )
        rows = await _recorded_traces(trace_store)
        assert len(rows) == 2

    async def test_record_trace_fractional_latency_round_trips(
        self, trace_store: SurrealStore
    ) -> None:
        # Explicit pin on the ``number`` typing: a sub-millisecond latency must not
        # be truncated to an int on the way in or out.
        fractional_latency_ms = 0.375
        await trace_store.record_trace(
            tool=_TRACE_TOOL,
            params_hash=_TRACE_PARAMS_HASH,
            hit_count=1,
            latency_ms=fractional_latency_ms,
            session=_TRACE_SESSION,
        )
        rows = await _recorded_traces(trace_store)
        assert len(rows) == 1
        assert rows[0]["latency_ms"] == fractional_latency_ms


class TestRecordTraceErrorPosture:
    """``record_trace`` never leaks a raw engine error: a domain/schema rejection
    surfaces as :class:`SurrealStoreError` (healthy connection kept), a transport
    failure self-heals — the classified posture the store's ``_query`` seam
    establishes. Real-only: the fake has no engine to reject and no socket to kill
    (its own resilience contract lives in ``test_surreal_fakes.py``).
    """

    async def test_domain_rejection_raises_store_error_and_keeps_connection(
        self, store: SurrealStore
    ) -> None:
        # A wrong-TYPE ``hit_count`` is a genuine SCHEMAFULL coercion rejection
        # (``hit_count`` is ``int``), surfacing as a STORE error — never
        # miscategorized as a connection failure, and the healthy connection is
        # never thrown away (mirrors ``TestDomainRejectionErrorType``).
        connection_before = store._connection
        with pytest.raises(SurrealStoreError) as exc_info:
            await store.record_trace(
                tool=_TRACE_TOOL,
                params_hash=_TRACE_PARAMS_HASH,
                hit_count="not-an-int",  # type: ignore[arg-type]  # deliberate poison
                latency_ms=_TRACE_LATENCY_MS,
                session=_TRACE_SESSION,
            )
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert store._connection is connection_before
        # Nothing partially persisted.
        assert await _recorded_traces(store) == []

    async def test_record_trace_recovers_from_a_mid_life_socket_drop(
        self, store: SurrealStore
    ) -> None:
        # CLAUDE.md lifecycle pin: ``record_trace`` holds a reference to the store's
        # shared connection; when that socket dies mid-life the next call must
        # self-heal (reconnect) within a bounded number of calls, never wedge.
        async def _record() -> None:
            await store.record_trace(
                tool=_TRACE_TOOL,
                params_hash=_TRACE_PARAMS_HASH,
                hit_count=_TRACE_HIT_COUNT,
                latency_ms=_TRACE_LATENCY_MS,
                session=_TRACE_SESSION,
            )

        await _record()  # healthy baseline — connection established
        await _kill_socket(store)  # degradation: the socket dies, handle goes stale

        await call_until_recovered(_record, _HEALABLE_ERRORS, label="store")
        # And it STAYS healed — a further write also lands (handle really replaced).
        await _record()
        assert len(await _recorded_traces(store)) >= 1


# ===========================================================================
# P8a #7: the SINGLE-statement ``_query`` seam's message hygiene.
#
# ``SurrealStore._query`` already SPLITS a caught error into transport (self-heal
# + ``SurrealConnectionError``) vs domain (keep the connection +
# ``SurrealStoreError``) — see ``TestDomainRejectionErrorType`` /
# ``TestMidLifeConnectionRecovery``. What it did NOT do was launder the DOMAIN
# branch's message: it interpolated the raw ``{error}`` straight into the raised
# ``SurrealStoreError``. A domain ``ASSERT``/coercion rejection's engine text can
# echo a bound VALUE back verbatim (the exact ledger #31 leak the MULTI-statement
# ``execute_transaction`` path already closes — see ``TestTxnRollbackMessageHygiene``),
# and that text flows to MCP clients in P8. This pins the SAME classified posture
# at the single-statement seam: raw text logged server-side, a CLASSIFIED, generic
# label + a "see the server log" hint raised, never the raw engine text.
#
# Deterministic and live-server-free: a fake connection raises a DOMAIN-kind
# ``ServerError`` carrying the poison text — mirroring ``TestTxnRollbackMessageHygiene``'s
# scripted-fake approach rather than depending on a real engine rejection.
# ===========================================================================


@dataclass
class _RejectingConnection:
    """A fake SDK connection whose ``query`` raises a scripted error — the seam
    fault-injector for ``_query``'s classified-error posture.

    A DOMAIN-kind ``ServerError`` (a ``kind`` outside ``_CONNECTION_ERROR_KINDS``)
    drives the message-hygiene branch under test; ``close`` is a tolerant no-op so
    a store holding this handle still tears down cleanly.
    """

    error: BaseException

    async def query(self, statement: str, params: dict[str, Any]) -> Any:
        raise self.error

    async def close(self) -> None:
        return None


class TestQueryMessageHygiene:
    """The single-statement ``_query`` domain branch classifies like
    ``execute_transaction`` (ledger #31): the RAISED ``SurrealStoreError`` names a
    generic engine CLASS + a server-log hint, NEVER the raw engine text (which can
    echo a bound value); the full detail is logged server-side. Real-only seam
    test — built inline with an injected fake connection (the ``store`` fixture's
    real engine can't be made to echo a KNOWN poison value on demand), mirroring
    ``TestTxnRollbackMessageHygiene``.
    """

    @staticmethod
    def _store_rejecting_with(error: BaseException) -> SurrealStore:
        store = SurrealStore(
            url=_DEAD_URL,
            namespace="ns",
            database="db",
            dim=PRODUCTION_DIM,
            user="root",
            password="root",
        )
        store._connection = cast("_SurrealConnection", _RejectingConnection(error=error))
        return store

    async def test_domain_rejection_message_never_echoes_the_raw_engine_text(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        store = self._store_rejecting_with(ServerError(ErrorKind.INTERNAL, _SENSITIVE_ENGINE_TEXT))
        connection_before = store._connection
        with caplog.at_level(logging.ERROR, logger="loremaster.store.surreal"):
            with pytest.raises(SurrealStoreError) as exc_info:
                await store._query("UPDATE chunk SET name = $name", {"name": "poison"})

        message = str(exc_info.value)
        # A domain rejection is a STORE error, not a connection error, and never
        # tears down the healthy connection (mirrors TestDomainRejectionErrorType).
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert store._connection is connection_before
        # The raw engine text / the value it carries NEVER reaches the message.
        assert _SENSITIVE_ENGINE_TEXT not in message
        assert _SENSITIVE_MARKER not in message
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
        assert _SENSITIVE_MARKER in logged

    async def test_field_coercion_rejection_is_classified_distinctly(self) -> None:
        store = self._store_rejecting_with(ServerError(ErrorKind.INTERNAL, _COERCION_ENGINE_TEXT))
        with pytest.raises(SurrealStoreError) as exc_info:
            await store._query("UPDATE chunk SET sub_ordinal = $v", {"v": "not-an-int"})

        message = str(exc_info.value)
        assert _COERCION_ENGINE_TEXT not in message
        assert "field coercion" in message.lower()
