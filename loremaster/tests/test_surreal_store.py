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
from collections.abc import AsyncIterator, Awaitable, Callable

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    TIER_A,
    TIER_B,
    SurrealEnv,
    chunk_record,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
    unit_vector,
)
from loremaster.index.records import Record
from loremaster.store.candidate import Candidate
from loremaster.store.surreal import (
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    SurrealStore,
    SurrealStoreError,
    VectorDimensionError,
)
from loremaster.symbols import _SCROLL_LIMIT  # the real scroll caller's read cap
from pydantic import ValidationError

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
        # A production long-tail row: a big nested FLEXIBLE metadata blob must
        # survive intact through the store's serialization.
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
        assert rows[0]["metadata"]["attr_0"]["nested"] == list(range(20))
        assert rows[0]["metadata"]["attr_49"]["text"] == "x" * 500


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


async def _call_until_recovered[T](op: Callable[[], Awaitable[T]], attempts: int = 4) -> T:
    """Call ``op`` until it succeeds, swallowing the transient drop errors.

    Proves the store is NOT permanently wedged: a healthy store heals within a few
    calls (whether GREEN retries transparently or surfaces one transient then
    reconnects). A wedged store (the current bug) raises on EVERY attempt and this
    exhausts — the RED that the missing lifecycle test would have caught.
    """
    last: BaseException | None = None
    for _ in range(attempts):
        try:
            return await op()
        except _HEALABLE_ERRORS as error:
            last = error
    raise AssertionError(f"store never recovered within {attempts} calls: {last!r}")


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
        assert await _call_until_recovered(store.count) == 5
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

        recovered = await _call_until_recovered(_search)
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
