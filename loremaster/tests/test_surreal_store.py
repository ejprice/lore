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

import ast
import asyncio
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
import pytest_asyncio
from _surreal_fakes import FakeSurrealStore, fake_surreal_trio
from _surreal_harness import (
    PRODUCTION_DIM,
    SLUG,
    TIER_A,
    TIER_B,
    SurrealConnection,
    SurrealEnv,
    call_until_recovered,
    chunk_record,
    connect_admin,
    drop_database,
    make_env,
    run,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
    unique_database,
    unit_vector,
)
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.records import Record, chunk_to_record, sha512_hex
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.store._txn import (
    _ERROR_CLASS_ASSERT_VIOLATION,
    _ERROR_CLASS_FIELD_COERCION,
    _ERROR_CLASS_QUERY_TOO_COMPLEX,
    _ERROR_CLASS_RETRYABLE_CONFLICT,
    _ERROR_CLASS_UNSPECIFIED,
    _MAX_TXN_CONFLICT_ATTEMPTS,
    _RETRYABLE_CONFLICT_MARKER,
    _classify_engine_error,
    execute_transaction,
)
from loremaster.store.candidate import Candidate
from loremaster.store.surreal import (
    _CONNECTION_ERRORS,
    _MAX_LEXICAL_QUERY_CHARS,
    _MAX_QUERY_TOKENS,
    SurrealConnectionError,
    SurrealStore,
    SurrealStoreError,
    VectorDimensionError,
    _SurrealConnection,
)
from loremaster.store.surreal_schema import (
    _BRIEFED_VIA_PUBLISH,
    AGENT_TABLE,
    BRIEF_TABLE,
    BRIEFED_RELATION,
    CHUNK_TABLE,
    FILE_TABLE,
    FINDING_TABLE,
    MEMORY_TABLE,
    TASK_TABLE,
    TRACE_TABLE,
    _define_field,
    _define_table,
    generate_agent_ddl,
    generate_brief_ddl,
    generate_ddl,
    generate_graph_ddl,
)
from loremaster.symbols import _SCROLL_LIMIT  # the real scroll caller's read cap
from lorescribe.models import Chunk
from pydantic import ValidationError
from surrealdb import AsyncSurreal as _RealAsyncSurreal
from surrealdb.errors import ErrorKind, ServerError, SurrealError

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

    def test_vector_cosine_defaults_to_none(self) -> None:
        # A caller that never projects the cosine substrate (a test double, an
        # older store) must not be forced to supply it.
        candidate = Candidate(key="k", score=0.1, payload={}, origin="fused")
        assert candidate.vector_cosine is None

    def test_vector_cosine_can_be_set(self) -> None:
        candidate = Candidate(key="k", score=0.1, payload={}, origin="fused", vector_cosine=0.87)
        assert candidate.vector_cosine == pytest.approx(0.87)


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

    async def test_hybrid_search_projects_vector_cosine_per_hit(
        self, store: SurrealStore
    ) -> None:
        # S4b Phase A (docs/design/2026-07-06-weak-match-discrimination.md §6):
        # the store projects each fused hit's RAW pre-fusion query<->chunk
        # cosine alongside the fused rrf score — the preferred form (an outer
        # ``vector::similarity::cosine(embedding, $qv)`` projection over the
        # fused ``search::rrf`` rows) confirmed live against spike-surreal
        # (scratchpad/probe_cosine_projection_s4b.py): ``search::rrf`` passes
        # ``embedding`` through from its ``SELECT *`` arm subqueries, so the
        # outer projection computes correctly for every fused row regardless
        # of which arm surfaced it.
        dim = PRODUCTION_DIM
        near = chunk_record(
            tier=TIER_A, file_path="pkg/near.py", identity="near_fn",
            ident_text="alpha beta", source_text="def near_fn():\n    pass\n",
        )
        far = chunk_record(
            tier=TIER_A, file_path="pkg/far.py", identity="far_fn",
            ident_text="gamma delta", source_text="def far_fn():\n    pass\n",
        )
        await store.upsert([(near, unit_vector(0, dim)), (far, unit_vector(1, dim))])

        results = await store.hybrid_search(
            query_vector=unit_vector(0, dim), query_text="alpha beta", k=5
        )

        near_hit = next(c for c in results if c.key == near.point_id)
        far_hit = next(c for c in results if c.key == far.point_id)
        assert near_hit.vector_cosine == pytest.approx(1.0, abs=1e-6)
        assert far_hit.vector_cosine == pytest.approx(0.0, abs=1e-6)

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
# Finding #66: hybrid_search's lexical (BM25) arm hard-rejected a realistically
# long query. Root cause (live-measured against spike-surreal 3.1.5, NOT the
# informal 245/340-char bisection — see scratchpad/probe_long_query_66*.py):
# the SurrealQL parser's own "expression recursion depth limit" on
# ``_build_fulltext_predicate``'s flat OR-chain, tripped at 40 analyzed tokens
# (120 OR clauses at 3 fulltext fields/token) — NOT the old, too-permissive
# 4096-char/64-token caps, which never actually protected against this. The
# fix: word-boundary text truncation + a measured-with-margin token clamp
# (:data:`_MAX_LEXICAL_QUERY_CHARS` / :data:`_MAX_QUERY_TOKENS`), and an
# honest classifier extension for the (now vanishingly rare) residual case.
# ---------------------------------------------------------------------------

# Distinct, single-token synthetic lexemes (all-lowercase ASCII letters only —
# no digits, no case changes — so the ``code_ident`` analyzer's blank/class/
# camel tokenizers never split one into two): 60 of them, far beyond both the
# new :data:`_MAX_QUERY_TOKENS` clamp and the OLD 40-token live rejection
# boundary, so a query built from all of them exercises the worst realistic
# case deterministically (no dependence on natural-English tokenization).
_SYNTHETIC_LEXEMES = tuple(
    f"lexeme{chr(97 + index // 26)}{chr(97 + index % 26)}" for index in range(60)
)

# The EXACT failure shape finding #66 was discovered from (REPORT-
# slate-builder-search.md §New Finding): a multi-sentence, plain-English
# LLM-style question. That report's live bisection found ~245 chars OK and
# ~340 chars REJECTED for a query of this shape; this one is deliberately
# >=340 chars so it reproduces the reported failure, not just the informal
# midpoint.
_REPORTED_SHAPE_LONG_QUERY = (
    "What was the operator ruling on the P8d closure and how does the slate "
    "cycle get sequenced before the detection layer lands, and which commits "
    "carry the surface flip receipts we should cite when asked about it later, "
    "and can you also summarize how the client-needs consult informed the "
    "accuracy-versus-efficiency tradeoff the lead ultimately ruled on."
)

# A punctuation-heavy, non-ASCII (French + Japanese) long query — proves the
# fix's word-boundary truncation and token clamp are content-agnostic, not
# tuned to plain ASCII English.
_NON_ASCII_LONG_QUERY = (
    "Quelle était la décision de l'opérateur sur la clôture de P8d, et comment "
    "le cycle « slate » est-il séquencé avant la couche de détection ? "
    "日本語のテスト文字列もここに含まれています、質問はとても長くなりますが大丈夫です。 "
    "Encore quelques mots supplémentaires pour dépasser confortablement le seuil mesuré, "
    "et voici même davantage de texte non-ASCII pour être certain de dépasser trois cent "
    "quarante caractères — なぜなら、この境界値を確実に超える必要があるからです。"
)


class TestTruncateAtWordBoundary:
    """``SurrealStore._truncate_at_word_boundary`` — the lexical arm's
    word-boundary text pre-truncation (finding #66). Pure/static: no live
    store or server round-trip needed.
    """

    def test_text_at_or_under_the_cap_is_returned_unchanged(self) -> None:
        assert SurrealStore._truncate_at_word_boundary("short query", 300) == "short query"
        exactly_at_cap = "x" * 10
        assert SurrealStore._truncate_at_word_boundary(exactly_at_cap, 10) == exactly_at_cap

    def test_over_cap_backs_off_to_the_last_word_boundary_never_splitting_a_word(self) -> None:
        text = "one two three four five"
        # The cutoff (17) lands mid-"four" (which spans indices 14-17); the
        # result must back off to the LAST full word before it, "three".
        assert SurrealStore._truncate_at_word_boundary(text, 17) == "one two three"

    def test_hostile_newline_and_tab_are_valid_word_boundaries(self) -> None:
        # A tab and a newline are both valid boundaries, not just a literal
        # space — a hostile multi-line query must not still be able to split a
        # word at the cutoff.
        text = "alpha\tbeta\ncharlie delta epsilon zeta eta theta iota kappa"
        assert SurrealStore._truncate_at_word_boundary(text, 20) == "alpha\tbeta\ncharlie"

    def test_single_giant_token_with_no_whitespace_falls_back_to_the_raw_slice(self) -> None:
        # No whitespace anywhere in the window — there is no better boundary to
        # back off to, so the raw slice is the best truncation available.
        text = "x" * 500
        assert SurrealStore._truncate_at_word_boundary(text, 300) == "x" * 300

    def test_punctuation_and_non_ascii_text_truncates_as_a_clean_prefix(self) -> None:
        text = _NON_ASCII_LONG_QUERY * 3
        truncated = SurrealStore._truncate_at_word_boundary(text, 50)
        assert len(truncated) <= 50
        assert truncated == text[: len(truncated)]  # a genuine prefix, never mangled/reordered


class TestLexicalArmLongQueryNeverRejects:
    """A realistically long (or synthetically token-heavy) query must NEVER
    hard-fail ``hybrid_search`` — measured live (scratchpad/
    probe_long_query_66*.py), the OLD 64-token/4096-char caps let a query with
    >=40 analyzed tokens straight through to the engine's hard "query
    rejected" (the SurrealQL expression-recursion-depth limit on the BM25
    OR-predicate).
    """

    async def test_query_at_the_new_token_clamp_boundary_succeeds(
        self, store: SurrealStore
    ) -> None:
        dim = PRODUCTION_DIM
        target = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py", identity="PurchaseOrder.action_confirm"
        )
        await store.upsert([(target, unit_vector(0, dim))])
        query_text = " ".join(_SYNTHETIC_LEXEMES[:_MAX_QUERY_TOKENS])  # exactly at the clamp
        results = await store.hybrid_search(query_vector=unit_vector(0, dim), query_text=query_text, k=5)
        assert any(candidate.key == target.point_id for candidate in results)

    async def test_query_far_beyond_the_old_broken_cap_is_bounded_not_rejected(
        self, store: SurrealStore
    ) -> None:
        dim = PRODUCTION_DIM
        target = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py", identity="PurchaseOrder.action_confirm"
        )
        await store.upsert([(target, unit_vector(0, dim))])
        # 60 distinct real tokens: under the OLD (broken) 64-token/4096-char
        # caps this sailed through to a live SurrealQL "expression recursion
        # depth limit" rejection (measured: fails at 40 tokens). Must now
        # succeed — the token clamp silently bounds the predicate to the first
        # _MAX_QUERY_TOKENS tokens, and the vector arm still finds the target.
        query_text = " ".join(_SYNTHETIC_LEXEMES)
        results = await store.hybrid_search(query_vector=unit_vector(0, dim), query_text=query_text, k=5)
        assert any(candidate.key == target.point_id for candidate in results)

    async def test_a_340_char_plain_english_question_succeeds_end_to_end(
        self, store: SurrealStore
    ) -> None:
        # The EXACT reported failure shape (REPORT-slate-builder-search.md
        # §New Finding) — a multi-sentence LLM-style question, live-reproduced
        # as a hard rejection before this fix.
        assert len(_REPORTED_SHAPE_LONG_QUERY) >= 340
        dim = PRODUCTION_DIM
        target = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py", identity="PurchaseOrder.action_confirm"
        )
        await store.upsert([(target, unit_vector(0, dim))])
        results = await store.hybrid_search(
            query_vector=unit_vector(0, dim), query_text=_REPORTED_SHAPE_LONG_QUERY, k=5
        )
        assert any(candidate.key == target.point_id for candidate in results)

    async def test_non_ascii_punctuation_heavy_long_query_does_not_raise(
        self, store: SurrealStore
    ) -> None:
        assert len(_NON_ASCII_LONG_QUERY) > 340
        # No corpus needed — the ONLY assertion that matters is "does not
        # raise" for content that is neither plain ASCII nor English.
        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM), query_text=_NON_ASCII_LONG_QUERY, k=5
        )
        assert results == []

    async def test_short_query_below_the_char_bound_is_untouched_by_truncation(
        self, store: SurrealStore
    ) -> None:
        # A short, realistic query sits well under _MAX_LEXICAL_QUERY_CHARS —
        # truncation must be a complete no-op (byte-identical text reaches the
        # analyzer), and the token clamp must never even engage — exactly the
        # pre-fix behaviour for any query this short.
        query_text = "PurchaseOrder action_confirm reconcile"
        assert len(query_text) < _MAX_LEXICAL_QUERY_CHARS
        assert (
            SurrealStore._truncate_at_word_boundary(query_text, _MAX_LEXICAL_QUERY_CHARS)
            == query_text
        )
        direct_tokens = await store._analyze_query(query_text)
        assert len(direct_tokens) <= _MAX_QUERY_TOKENS  # the clamp never even triggers


class TestResidualRejectionStillLaunders:
    """If both of the lexical arm's own clamps were ever bypassed (e.g. a
    future regression widens :data:`_MAX_QUERY_TOKENS` back up), the
    SurrealQL parser's rejection must STILL never leak raw engine text — it
    flows through the existing classify/log/launder seam (:meth:`SurrealStore.
    _query`), now honestly extended with a "query too complex" label (finding
    #66) instead of falling into the generic "unspecified rejection".
    """

    def test_classifier_recognises_the_live_recursion_depth_rejection_text(self) -> None:
        # The EXACT raw engine text captured live against spike-surreal
        # (scratchpad/probe_long_query_66b.py) — a pure, fast unit test of the
        # classifier extension, no live server needed.
        raw_engine_text = (
            "Parse error: Exceeded expression recursion depth limit\n"
            " --> [1:3139]\n"
            "  |\n"
            "1 | ...rce_text @@ $__ft39 OR llm_summary @@ $__ft39))], 5, 60)\n"
            "  |              ^ this expression nests or chains operators too deeply\n"
        )
        assert _classify_engine_error(raw_engine_text) == _ERROR_CLASS_QUERY_TOO_COMPLEX

    async def test_bypassing_both_clamps_still_raises_a_classified_store_error(
        self, store: SurrealStore, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Force BOTH lexical-arm clamps back up past the measured-safe
        # ceiling — simulating the exact pre-fix (broken) configuration — and
        # confirm the genuine engine rejection still comes back laundered, not
        # raw, and the connection stays healthy (a domain rejection, not a
        # transport fault, per TestDomainRejectionErrorType's contract).
        monkeypatch.setattr("loremaster.store.surreal._MAX_QUERY_TOKENS", 200)
        monkeypatch.setattr("loremaster.store.surreal._MAX_LEXICAL_QUERY_CHARS", 4096)
        connection_before = store._connection
        query_text = " ".join(_SYNTHETIC_LEXEMES)  # 60 real tokens, now fully unclamped
        with pytest.raises(SurrealStoreError) as exc_info:
            await store.hybrid_search(
                query_vector=unit_vector(0, PRODUCTION_DIM), query_text=query_text, k=5
            )
        message = str(exc_info.value)
        assert "query too complex" in message
        assert "recursion depth" not in message  # the raw engine text never echoes
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert store._connection is connection_before  # healthy connection, never dropped


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

# ---------------------------------------------------------------------------
# LIVE-CAPTURED ENGINE TEXTS — every one of these is copied out of a real
# SurrealDB 3.1.5 response, not typed from memory.
#
# PROVENANCE: captured off spike-surreal (ws://127.0.0.1:18000), SurrealDB
# 3.1.5, 2026-07-13, by ``scratchpad/contract-v5/capture_engine.py`` — which
# DEFINEs a real ASSERT/typed field and then violates it. Re-run that probe to
# re-derive these; the [real]-tier ``TestLiveEngineClassification`` suite below
# is the standing guard that they still match the engine.
#
# WHY THIS BLOCK EXISTS AT ALL. Three separate defects in this file family —
# #102, and the audit's B2 and B3 — have ONE root cause: **a fixture typed from
# a BELIEVED engine instead of a MEASURED one.** The previous version of this
# block said a rejected ASSERT reads "…expected the value to fulfil the
# following assertion:…". The engine has never once said that. It says "…but
# field must conform to:…" — so the classifier's ``"assert"`` marker has NEVER
# matched real output, and every ASSERT violation in this repo's entire
# production life was served as "unspecified rejection". The pins were green
# because the fixture and the code shared one imagination.
#
# STANDING RULE (design addendum, Ruling 2): a classifier marker ships only with
# a live-engine pin that PROVOKES its class. **A marker without a provocation
# pin is presumed fiction.**
# ---------------------------------------------------------------------------

# The value the engine echoes back verbatim in an ASSERT rejection — the whole
# reason the raised message must never carry engine text (ledger #31). Note the
# live text ACTUALLY interpolates the offending value, so this is not a
# hypothetical leak: it is the engine's real behaviour.
_SENSITIVE_MARKER = "TOP-SECRET-BOUND-VALUE-9f3a1c"

# LIVE ASSERT-violation text. Captured shape, with the offending value replaced
# by the sensitive marker above (the engine interpolates whatever was written).
# Contains NO "assert" substring — that is finding B2, in one line.
_SENSITIVE_ENGINE_TEXT = (
    f"Found '{_SENSITIVE_MARKER}' for field `state`, with record `thing:bad`, "
    f"but field must conform to: $value INSIDE ['open', 'done']"
)

# LIVE field-coercion text. A distinct engine SHAPE from an ASSERT violation, so
# the classifier's branches are independently pinned. (Its "coerce" marker does
# match reality — the coercion branch was never broken.)
_COERCION_ENGINE_TEXT = (
    "Couldn't coerce value for field `ordinal` of `thing:c`: "
    "Expected `int` but found `'not-an-int'`"
)

# LIVE retryable-conflict text (the COMMIT entry of a write-write race).
_CONFLICT_ENGINE_TEXT = (
    f"Cannot COMMIT: Transaction conflict: Resource busy. This transaction "
    f"{_RETRYABLE_CONFLICT_MARKER}"
)

# LIVE COMMIT-abort notice: what the COMMIT entry says once any earlier
# statement failed.
_COMMIT_ABORTED_ENGINE_TEXT = "Cannot COMMIT: the transaction was aborted due to a prior error"

# LIVE cascade notices. THE FIXTURE VALUE THAT CHANGES EVERYTHING (audit B3):
# the engine stamps statements BEFORE the offender as ``ERR`` — "not executed due
# to a failed transaction" — NOT as ``OK``. So the FIRST failed entry is a
# CASCADE, not the root cause. Every fixture in this file used to model those
# statements as OK, which is precisely why a ``[0]``-picking selector looked
# correct for the repo's entire life.
_CASCADE_ENGINE_TEXT = "The query was not executed due to a failed transaction"
_CASCADE_CANCELLED_ENGINE_TEXT = "The query was not executed due to a cancelled transaction"

_OK_STATEMENT: dict[str, Any] = {"status": "OK", "result": None}


def _rolled_back_response(*results: str | None) -> dict[str, Any]:
    """Build a ``query_raw``-shaped response with one entry per argument:
    ``None`` → an OK statement, a string → an ERR statement carrying that
    text — the exact shape :func:`~loremaster.store._txn._failed_statements`
    inspects. Unlike :func:`_err_response` it expresses ANY failure shape —
    in particular the real rollback cascade (root ERR, then later cascade
    ERRs, then the COMMIT-aborted ERR) that a single-ERR-only builder could
    never model, which is exactly how finding #93 stayed green.
    """
    entries: list[dict[str, Any]] = [
        dict(_OK_STATEMENT) if result_text is None else {"status": "ERR", "result": result_text}
        for result_text in results
    ]
    return {"result": entries}


def _err_response(*, result_text: str, leading_ok: int = 0, trailing_ok: int = 0) -> dict[str, Any]:
    """Build a ``query_raw``-shaped response: ``leading_ok`` OK statements,
    then one ERR statement carrying ``result_text``, then ``trailing_ok`` more
    OK statements — a single-ERR convenience wrapper over
    :func:`_rolled_back_response`. Leading/trailing OK counts let a test pin
    the failed statement's INDEX distinctly from the total statement COUNT.
    """
    return _rolled_back_response(*([None] * leading_ok), result_text, *([None] * trailing_ok))


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
    fake: _TxnRollbackFakeConnection,
    *,
    drop: Callable[[Any], Awaitable[None]] | None = None,
    deadline_seconds: float | None = None,
) -> None:
    """Drive ``execute_transaction`` against ``fake`` with a fixed poison
    statement/params — the shape is irrelevant to these tests since the fake
    ignores it entirely and only replays scripted responses.

    ``deadline_seconds=None`` uses the seam's own default (what every one of the 16
    production call sites does today).
    """

    async def _acquire() -> _SurrealConnection:
        return cast("_SurrealConnection", fake)

    await execute_transaction(
        "BEGIN;\nUPDATE chunk SET name = $name;\nCOMMIT;\n",
        {"name": "poison"},
        acquire=_acquire,
        drop=drop or _never_drop(),
        url="ws://127.0.0.1:19555/rpc",  # unreachable — never actually dialed
        deadline_seconds=deadline_seconds,
    )


# ---------------------------------------------------------------------------
# Finding #102 — the LIVE rolled-back-conflict shape, and the fixtures that
# can actually SEE it.
#
# THE fixture defect this finding is made of: every conflict fixture above
# puts the engine's ``can be retried`` marker on entry ``[0]`` — a shape the
# LIVE engine never produces. When two transactions race a row, the engine
# rolls back and the failed-statement list looks like this (captured live):
#
#     idx1: "The query was not executed due to a failed transaction"
#     idx2: "The query was not executed due to a failed transaction"
#     idx3: "Cannot COMMIT: Transaction conflict: Resource busy. This
#            transaction can be retried"
#
# The marker rides the LAST (COMMIT) entry ONLY; every earlier entry is
# marker-less cascade noise. A raise site that classifies ``[0]`` therefore
# labels a sustained conflict "unspecified rejection" — while
# ``_is_retryable_conflict``'s ``any()`` scan (which sees every entry) happily
# retries it. Retry and label read DIFFERENT witnesses, so they disagree.
#
# The two shapes below are kept as a PAIR, forever: the conflict evidence can
# sit at either end of the list, and a classifier that is right about one
# position and wrong about the other must go RED. If the code can branch on
# position, the pins must cover both positions.
# ---------------------------------------------------------------------------


def _live_conflict_rollback_response() -> dict[str, Any]:
    """The LIVE conflict-rollback shape: marker-less cascade entries, then the
    conflict-marked COMMIT — the marker on the LAST entry ONLY.

    This is what the engine actually emits under a write-write race (lead's
    captured log, finding #102). The conflict-bearing entry is at 0-based
    index 2 of 3.
    """
    return _rolled_back_response(
        _CASCADE_ENGINE_TEXT, _CASCADE_ENGINE_TEXT, _CONFLICT_ENGINE_TEXT
    )


def _marker_first_conflict_rollback_response() -> dict[str, Any]:
    """The conflict marker on entry ``[0]`` — the shape every pre-#102 conflict
    fixture used. NOT a live shape, but retained deliberately: it is the OTHER
    position the classifier could branch on, and a semantic (marker-seeking)
    selector must handle both.
    """
    return _err_response(result_text=_CONFLICT_ENGINE_TEXT)


# The 0-based index of the conflict-bearing entry in each shape above — the
# entry the seam must name as the root cause of an exhausted conflict, because
# it is the entry that MADE the retry decision.
_LIVE_CONFLICT_MARKER_INDEX = 2
_MARKER_FIRST_CONFLICT_MARKER_INDEX = 0

# The conflict shapes, as (id, response-builder, marker-index, statement-count)
# — every conflict pin is parametrized over BOTH so neither position can be
# silently regressed.
_CONFLICT_SHAPES = [
    pytest.param(
        _live_conflict_rollback_response, _LIVE_CONFLICT_MARKER_INDEX, 3, id="marker-last-LIVE"
    ),
    pytest.param(
        _marker_first_conflict_rollback_response,
        _MARKER_FIRST_CONFLICT_MARKER_INDEX,
        1,
        id="marker-first",
    ),
]

# A hard stop on the fake's call count: NOT a tuned constant and NOT the seam's
# budget — an absurdity ceiling that turns "the retry loop is unbounded" from a
# HANG (which a test runner reports as a timeout, minutes later, with no useful
# receipt) into an immediate, legible failure. Any real budget sits far below it.
_ABSURD_ATTEMPT_CEILING = 5_000


# ---------------------------------------------------------------------------
# THE FIXTURE THAT DID NOT EXIST — a transaction that TAKES TIME (audit B1).
#
# Every fake in this file returns from ``query_raw`` INSTANTLY. So the entire
# deadline pin family — `test_the_deadline_is_honoured`,
# `test_a_longer_deadline_buys_more_attempts`, the default-budget pin — was blind
# to a build in which **the deadline vetoes the first retry**, because that build
# only misbehaves when ONE ATTEMPT outlasts THE DEADLINE. No fixture had ever
# produced such an attempt.
#
# It shipped through four contract revisions, three cold adversaries and a builder,
# and it took a full-suite run against `test_surreal_apply.py` to find it: a bulk
# apply measured at 9.56s for a SINGLE attempt against a 2.0s deadline gets a retry
# budget of ZERO — the first conflict raises with `attempts=1`. Pre-#102, every
# caller got five attempts regardless of wall time. That is a regression, and all
# 16 call sites run on the default.
#
# "What WRONG build would this fixture still pass?" — the answer, for every
# instant-returning fake, is: *that* one.
# ---------------------------------------------------------------------------


@dataclass
class _SlowConflictFakeConnection:
    """A fake whose ``query_raw`` genuinely BLOCKS for ``attempt_seconds`` before
    answering — the slow-transaction regime (a bulk apply, an indexing write on a
    loaded box), which is exactly the regime most likely to hit a write-write
    conflict and the one no previous fixture could express.

    Sleeps via the real ``asyncio.sleep`` captured at import, so it is immune to the
    monkeypatching the backoff pins do — a fake that only *pretends* to be slow
    cannot see this defect either.
    """

    response: dict[str, Any]
    attempt_seconds: float
    # Answer with a conflict until this many calls have been made, then succeed.
    # ``None`` = conflict forever.
    succeed_after_calls: int | None = None
    calls: int = field(default=0, init=False)

    async def query_raw(self, statement: str, params: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        if self.calls > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError("unbounded retry")
        await _REAL_ASYNCIO_SLEEP(self.attempt_seconds)  # the attempt's OWN duration
        if self.succeed_after_calls is not None and self.calls >= self.succeed_after_calls:
            return {"result": [dict(_OK_STATEMENT)]}
        return self.response

    def check_response_for_error(self, response: Any, method: str) -> None:
        return None


@dataclass
class _SustainedConflictFakeConnection:
    """A fake SDK connection that returns the SAME rolled-back response to
    EVERY ``query_raw`` — sustained, unresolvable contention.

    Deliberately constant-free (unlike a scripted response LIST, which must be
    sized to the seam's attempt budget and therefore silently pins it): the
    seam may retry as many times as its own budget allows and this fake keeps
    feeding it conflicts. That is what lets the conflict pins assert
    BOUNDEDNESS — "it stopped, and it stopped without being told how many
    attempts to make" — instead of asserting a magic number that the repair is
    explicitly allowed to re-measure and change.
    """

    response: dict[str, Any]
    calls: int = field(default=0, init=False)

    async def query_raw(self, statement: str, params: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        if self.calls > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError(
                f"execute_transaction made more than {_ABSURD_ATTEMPT_CEILING} attempts "
                f"against sustained contention — the retry budget is effectively unbounded"
            )
        return self.response

    def check_response_for_error(self, response: Any, method: str) -> None:
        return None


@dataclass
class _SleepRecorder:
    """Records every duration handed to ``asyncio.sleep`` and yields control
    without actually waiting.

    The instrument for the backoff pins. The seam's backoff is only observable
    through the durations it asks to sleep for, so the tests patch
    ``asyncio.sleep`` and read them back. Sleeping for REAL zero (rather than
    not awaiting at all) keeps the event loop's scheduling semantics intact
    while making a full exhaustion run instant.

    Contract note: this pins ``asyncio.sleep`` as the seam's backoff mechanism.
    A repair that waits by some other means (``loop.call_later``, a third-party
    sleep) is not covered by these pins and must not be shipped without
    replacing them.
    """

    durations: list[float] = field(default_factory=list)

    async def sleep(self, duration: float) -> None:
        self.durations.append(duration)
        await _REAL_ASYNCIO_SLEEP(0)


# Captured BEFORE any monkeypatching, so a recorder can still yield to the loop.
_REAL_ASYNCIO_SLEEP = asyncio.sleep


@dataclass
class _PerRacerSleepRecorder:
    """Records backoffs **keyed by the racer that asked for them**.

    The instrument MISSING PIN 3 needs, and the reason the sequential sampler
    could not be extended to do this job: with one global list of durations, a
    build in which every concurrent racer sleeps the IDENTICAL amount is
    indistinguishable from one in which they all sleep differently — the bag of
    numbers looks the same. Attribution is the whole measurement, so the recorder
    keys on ``asyncio.current_task()``: under ``asyncio.gather`` each racer IS a
    distinct task, so its draws are its own.
    """

    per_racer: dict[object, list[float]] = field(default_factory=dict)

    async def sleep(self, duration: float) -> None:
        racer = asyncio.current_task()
        self.per_racer.setdefault(racer, []).append(duration)
        await _REAL_ASYNCIO_SLEEP(0)

    def first_draws(self) -> list[float]:
        """Each racer's FIRST backoff — the draw that decides whether two racers
        that just collided will wake together and collide again.
        """
        return [durations[0] for durations in self.per_racer.values() if durations]

    def within_racer_ratios(self) -> list[float]:
        """Each racer's 2nd backoff over its 1st. A racer that draws entropy ONCE
        and scales it by the attempt index reports the same ratio as every other
        racer — however random that one draw was.
        """
        return [
            round(durations[1] / durations[0], 9)
            for durations in self.per_racer.values()
            if len(durations) >= 2 and durations[0] > 0
        ]


async def _exhaust_conflict_concurrently(
    racer_count: int, *, monkeypatch: pytest.MonkeyPatch
) -> _PerRacerSleepRecorder:
    """Drive ``racer_count`` GENUINELY CONCURRENT transactions into the same
    sustained conflict, recording each racer's own backoff sequence.

    This is the shape the finding is actually about — N writers colliding on ONE
    row — and it is the shape no sequential sampler can reproduce, no matter how
    many times it is run.
    """
    recorder = _PerRacerSleepRecorder()
    monkeypatch.setattr(asyncio, "sleep", recorder.sleep)

    async def _one_racer() -> None:
        fake = _SustainedConflictFakeConnection(response=_live_conflict_rollback_response())
        with pytest.raises(SurrealStoreError):
            await _run_execute_transaction(cast("_TxnRollbackFakeConnection", fake))

    await asyncio.gather(*(_one_racer() for _ in range(racer_count)))
    assert len(recorder.per_racer) == racer_count, (
        f"expected {racer_count} distinct racers to back off, saw "
        f"{len(recorder.per_racer)} — the concurrency of this pin is not real"
    )
    return recorder


async def _exhaust_conflict(
    response: dict[str, Any], *, monkeypatch: pytest.MonkeyPatch
) -> tuple[_SustainedConflictFakeConnection, _SleepRecorder, BaseException]:
    """Drive ``execute_transaction`` into sustained contention with a patched
    (recording, non-waiting) ``asyncio.sleep``, and return the fake, the sleep
    recorder, and the exception that finally surfaced.

    Fails the test outright if the seam does NOT raise — "it silently gave up
    and returned" is a wrong build this helper must never hide.
    """
    fake = _SustainedConflictFakeConnection(response=response)
    recorder = _SleepRecorder()
    monkeypatch.setattr(asyncio, "sleep", recorder.sleep)
    try:
        await _run_execute_transaction(cast("_TxnRollbackFakeConnection", fake))
    except SurrealStoreError as error:
        return fake, recorder, error
    raise AssertionError(
        "execute_transaction returned normally under sustained contention — an "
        "exhausted conflict must always surface to the caller, never be swallowed"
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


class TestTxnRootCauseSelection:
    """Finding #93's INTENT, on the engine that actually exists (audit B3).

    #93 was right about the goal — *a domain rollback must name the statement that
    really failed, not the COMMIT* — and wrong about the engine. Its premise, written
    into the code as the justification for picking ``failed_statements[0]``, was:

        "statements execute in order, so everything before the first ERR succeeded"

    **That is false.** SurrealDB 3.1.5 retroactively stamps the statements BEFORE the
    offender as ``ERR`` too, with the notice *"The query was not executed due to a
    failed transaction"*. Live capture (``scratchpad/contract-v5/capture_engine.py``,
    a real ``DEFINE FIELD … ASSERT`` then violated mid-transaction):

        idx 0  OK
        idx 1  ERR  "The query was not executed due to a failed transaction"   <- CASCADE
        idx 2  ERR  "Found 'BOGUS' … but field must conform to: …"             <- THE REAL CAUSE
        idx 3  ERR  "The query was not executed due to a cancelled transaction"
        idx 4  ERR  "Cannot COMMIT: the transaction was aborted due to a prior error"

    So ``failed_statements[0]`` is a **cascade notice**, and `[-1]` is the COMMIT
    abort. **Neither end is the root cause.** Both #93's pick and its predecessor were
    wrong, and every domain rollback in this repo's production life has misnamed which
    statement failed *and* classified a cascade message (which lands in "unspecified
    rejection").

    The old pins passed because their fixture modelled the pre-offender statements as
    ``OK`` — a shape the engine never emits. The fixture and the code shared one
    imagination. **These fixtures are derived from the capture above; not one is typed
    from memory.**

    The rule (design addendum, Ruling 3): the root cause is the FIRST failed entry
    whose text is non-empty and carries NO cascade marker; degrade to the LAST entry
    when every entry is a cascade. Semantic, never positional — at both ends.
    """

    @staticmethod
    def _live_domain_rollback_response() -> dict[str, Any]:
        """THE DISCRIMINATING SHAPE — the offender MID-transaction, exactly as
        captured. A ``[0]``-picker names index 1 (a cascade); a ``[-1]``-picker names
        index 4 (the COMMIT abort). Only a semantic selector names index 2.
        """
        return _rolled_back_response(
            None,                            # idx 0: OK
            _CASCADE_ENGINE_TEXT,            # idx 1: ERR — cascade (before the offender)
            _SENSITIVE_ENGINE_TEXT,          # idx 2: ERR — THE ROOT CAUSE
            _CASCADE_CANCELLED_ENGINE_TEXT,  # idx 3: ERR — cascade (after)
            _COMMIT_ABORTED_ENGINE_TEXT,     # idx 4: ERR — the COMMIT abort
        )

    @staticmethod
    def _live_offender_first_response() -> dict[str, Any]:
        """The BOUNDARY shape: the offender is the first body statement, so there is
        no preceding cascade and the root cause genuinely IS the first failed entry.
        Captured live (``assert_alone``). Keeps the selector honest at the edge — a
        build that blindly skips the first failed entry would pass the shape above and
        fail this one.
        """
        return _rolled_back_response(
            None,                          # idx 0: OK
            _SENSITIVE_ENGINE_TEXT,        # idx 1: ERR — THE ROOT CAUSE (no cascade before it)
            _COMMIT_ABORTED_ENGINE_TEXT,   # idx 2: ERR — the COMMIT abort
        )

    async def test_the_root_cause_is_the_first_SUBSTANTIVE_entry_not_the_first_failed_one(
        self,
    ) -> None:
        """RED against today's code: it names statement 2 of 5 (a cascade notice that
        says only "the query was not executed") and labels it "unspecified rejection".

        The ordinal is part of the served surface, so it is part of the pin.
        """
        fake = _TxnRollbackFakeConnection(responses=[self._live_domain_rollback_response()])
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(fake)

        message = str(exc_info.value)
        assert "statement 3 of 5" in message  # idx 2 -> 1-based 3. NOT the cascade at idx 1.
        assert _ERROR_CLASS_ASSERT_VIOLATION in message.lower()
        assert _ERROR_CLASS_UNSPECIFIED not in message.lower()
        assert _SENSITIVE_MARKER not in message  # ledger #31 hygiene, preserved
        assert fake.calls == 1  # a domain rejection is never retried

    async def test_the_boundary_shape_still_names_the_first_entry_when_it_IS_the_cause(
        self,
    ) -> None:
        """The offender is the first body statement — no preceding cascade. The
        semantic selector must land on it, not skip past it.
        """
        fake = _TxnRollbackFakeConnection(responses=[self._live_offender_first_response()])
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(fake)

        message = str(exc_info.value)
        assert "statement 2 of 3" in message
        assert _ERROR_CLASS_ASSERT_VIOLATION in message.lower()
        assert _ERROR_CLASS_UNSPECIFIED not in message.lower()

    async def test_server_log_reports_the_root_cause_and_carries_every_failed_statement(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The receipt names the SUBSTANTIVE entry, and still carries every failed
        statement (the cascades are diagnostically useful, just not the cause).
        """
        fake = _TxnRollbackFakeConnection(responses=[self._live_domain_rollback_response()])
        with caplog.at_level(logging.ERROR, logger="loremaster.store._txn"):
            with pytest.raises(SurrealStoreError):
                await _run_execute_transaction(fake)

        error_records = [record for record in caplog.records if record.levelno == logging.ERROR]
        assert error_records, "the full engine detail must be logged server-side"
        record = error_records[0]
        assert getattr(record, "statement_index", None) == 2  # the ROOT cause, not the cascade
        assert getattr(record, "statement_count", None) == 5
        assert getattr(record, "status", None) == "ERR"
        assert _SENSITIVE_ENGINE_TEXT in str(getattr(record, "engine_result", ""))
        failed = getattr(record, "failed_statements", None)
        assert failed is not None, "the receipt must carry every failed statement"
        assert [entry["index"] for entry in failed] == [1, 2, 3, 4]
        assert any(_COMMIT_ABORTED_ENGINE_TEXT in str(entry["engine_result"]) for entry in failed)

    @pytest.mark.parametrize(
        ("root_text", "expected_label"),
        [
            pytest.param(_SENSITIVE_ENGINE_TEXT, _ERROR_CLASS_ASSERT_VIOLATION, id="assert-violation"),
            pytest.param(_COERCION_ENGINE_TEXT, _ERROR_CLASS_FIELD_COERCION, id="field-coercion"),
        ],
    )
    async def test_neither_cascade_nor_commit_abort_ever_drives_the_classification(
        self, root_text: str, expected_label: str
    ) -> None:
        """The structural pin of the defect CLASS, at BOTH ends: with a substantive
        entry present, neither the leading cascade nor the trailing COMMIT abort may
        be the entry that gets classified.
        """
        fake = _TxnRollbackFakeConnection(
            responses=[
                _rolled_back_response(
                    _CASCADE_ENGINE_TEXT, root_text, _COMMIT_ABORTED_ENGINE_TEXT
                )
            ]
        )
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(fake)

        message = str(exc_info.value)
        assert expected_label in message.lower()
        assert _ERROR_CLASS_UNSPECIFIED not in message.lower()
        assert "statement 2 of 3" in message  # the middle entry — neither end
        assert fake.calls == 1

    async def test_an_all_cascade_rollback_degrades_to_the_last_entry(self) -> None:
        """The DEGENERATE case: no substantive text anywhere. There is no root cause to
        name, so the honest report is the engine's own final word — the last entry —
        and the generic label. (Observables preserved from the pin this replaces.)
        """
        fake = _TxnRollbackFakeConnection(
            responses=[_rolled_back_response(None, None, _COMMIT_ABORTED_ENGINE_TEXT)]
        )
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(fake)

        message = str(exc_info.value)
        assert "statement 3 of 3" in message
        assert _ERROR_CLASS_UNSPECIFIED in message.lower()
        assert fake.calls == 1

    async def test_a_cascade_only_prefix_with_no_substantive_entry_still_degrades(
        self,
    ) -> None:
        """Every failed entry is a cascade notice (the engine's non-execution notices
        plus the abort). Nothing substantive exists — degrade to the LAST entry rather
        than blaming the first "query was not executed" notice, which explains nothing.
        """
        fake = _TxnRollbackFakeConnection(
            responses=[
                _rolled_back_response(
                    None,
                    _CASCADE_ENGINE_TEXT,
                    _CASCADE_CANCELLED_ENGINE_TEXT,
                    _COMMIT_ABORTED_ENGINE_TEXT,
                )
            ]
        )
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(fake)

        message = str(exc_info.value)
        assert "statement 4 of 4" in message  # the LAST entry, not the first cascade
        assert _ERROR_CLASS_UNSPECIFIED in message.lower()


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

    @pytest.mark.parametrize(("build_response", "marker_index", "statement_count"), _CONFLICT_SHAPES)
    async def test_sustained_conflict_still_raises_after_bounded_attempts(
        self,
        build_response: Callable[[], dict[str, Any]],
        marker_index: int,
        statement_count: int,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Sustained contention surfaces, BOUNDED, and is labelled a CONFLICT.

        Constant-free by construction (see ``_SustainedConflictFakeConnection``):
        it asserts the seam retried at least once and then STOPPED, never that
        it stopped after some particular number of attempts — the budget is the
        repair's to re-measure.

        The ``marker-last-LIVE`` parametrization is the finding: today's raise
        site classifies ``failed_statements[0]`` — a marker-less cascade entry —
        so it labels a genuine exhausted conflict "unspecified rejection".
        """
        fake, _, error = await _exhaust_conflict(build_response(), monkeypatch=monkeypatch)

        assert fake.calls >= 2, "a retryable conflict must be RETRIED, not raised on first sight"
        assert fake.calls < _ABSURD_ATTEMPT_CEILING  # bounded, not unbounded
        assert _CONFLICT_ENGINE_TEXT not in str(error)  # hygiene: no raw engine text
        assert _ERROR_CLASS_RETRYABLE_CONFLICT in str(error).lower()
        assert _ERROR_CLASS_UNSPECIFIED not in str(error).lower()

    async def test_non_retryable_rejection_is_never_retried(self) -> None:
        fake = _TxnRollbackFakeConnection(
            responses=[_err_response(result_text=_SENSITIVE_ENGINE_TEXT)]
        )

        with pytest.raises(SurrealStoreError):
            await _run_execute_transaction(fake)

        assert fake.calls == 1

    async def test_retry_marker_on_a_later_failed_statement_still_triggers_a_retry(self) -> None:
        """``_is_retryable_conflict`` scans ALL failed statements (``any()``),
        so a conflict marker on a LATER entry must still trigger a retry even
        though the raise site reads the FIRST entry — pins the scan against a
        future "align the retry decision to the root cause" regression. The
        two-ERR shape is adversarial-synthetic: a marker-free cascade entry
        ahead of the conflict-marked COMMIT.
        """
        fake = _TxnRollbackFakeConnection(
            responses=[
                _rolled_back_response(_CASCADE_ENGINE_TEXT, _CONFLICT_ENGINE_TEXT),
                {"result": [dict(_OK_STATEMENT)]},
            ]
        )

        await _run_execute_transaction(fake)  # must NOT raise

        assert fake.calls == 2  # one conflict, one successful retry — invisible to the caller


class TestSlowTransactionsKeepTheirRetryBudget:
    """Audit B1 (BLOCKER) — **the deadline may bound retries; it may never veto the
    first one.**

    A wall-clock budget smaller than a single attempt is incoherent AS A RETRY BUDGET.
    A clean 9.56s bulk apply takes 9.56s with no retry policy involved at all — the
    caller's own execution time is not the retry policy's to ration. When the built
    loop counted the attempt's own duration against the deadline and then checked the
    deadline before deciding to retry, every transaction slower than 2.0s got a retry
    budget of **zero**: first conflict, `attempts=1`, raise. Pre-#102 those callers got
    five attempts regardless of wall time. That is a straight regression, and it is
    what broke `test_surreal_apply.py`.

    The ruling (design addendum, R1 — candidate (a), **zero new constants**)::

        give_up = (
            attempt >= _TXN_CONFLICT_ATTEMPT_CEILING
            or (elapsed >= deadline and attempt >= _MAX_TXN_CONFLICT_ATTEMPTS)
        )

    The FLOOR is the EXISTING ``_MAX_TXN_CONFLICT_ATTEMPTS`` (5) — not a tuned number
    but **the pre-#102 behavioural contract itself**, so the non-regression guarantee
    is restored BY CONSTRUCTION rather than by picking a value. Two regimes, two honest
    guarantees: fast attempts are governed by the wall clock (the #102 case); slow
    attempts are governed by an attempt count (the pre-#102 case).
    """

    # An attempt that outlasts the deadline — the whole point. Scaled down from the
    # audit's live numbers (a 9.56s apply against a 2.0s deadline) so the pins are
    # fast; only the RATIO matters: attempt_seconds > deadline_seconds.
    _SLOW_ATTEMPT_SECONDS = 0.10
    _DEADLINE_BELOW_ONE_ATTEMPT = 0.02

    async def test_a_slow_conflicting_transaction_still_gets_the_attempt_floor(
        self,
    ) -> None:
        """RED against today's build: it gives up after **1** attempt.

        The attempt itself outlasts the deadline, so a loop that charges the attempt's
        own duration to the retry budget has already overspent before it has retried
        even once.
        """
        fake = _SlowConflictFakeConnection(
            response=_live_conflict_rollback_response(),
            attempt_seconds=self._SLOW_ATTEMPT_SECONDS,
        )
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(
                cast("_TxnRollbackFakeConnection", fake),
                deadline_seconds=self._DEADLINE_BELOW_ONE_ATTEMPT,
            )

        assert fake.calls >= _MAX_TXN_CONFLICT_ATTEMPTS, (
            f"a slow transaction got only {fake.calls} attempt(s) before the seam gave "
            f"up. The deadline ({self._DEADLINE_BELOW_ONE_ATTEMPT}s) is shorter than ONE "
            f"attempt ({self._SLOW_ATTEMPT_SECONDS}s), so it vetoed the retry budget "
            f"entirely — pre-#102 this caller was guaranteed "
            f"{_MAX_TXN_CONFLICT_ATTEMPTS} attempts regardless of wall time."
        )
        assert getattr(exc_info.value, "attempts", 0) >= _MAX_TXN_CONFLICT_ATTEMPTS

    async def test_the_regression_shape_a_slow_transaction_that_would_have_succeeded(
        self,
    ) -> None:
        """THE EXACT SHAPE THAT BROKE THE SUITE: a slow transaction conflicts once and
        would succeed on its second attempt. It must SUCCEED.

        Today it raises, because the deadline vetoed the retry that would have worked.
        This is `test_surreal_apply.py`'s failure, reduced to a unit pin.
        """
        fake = _SlowConflictFakeConnection(
            response=_live_conflict_rollback_response(),
            attempt_seconds=self._SLOW_ATTEMPT_SECONDS,
            succeed_after_calls=2,  # the SECOND attempt lands
        )

        # Must NOT raise.
        await _run_execute_transaction(
            cast("_TxnRollbackFakeConnection", fake),
            deadline_seconds=self._DEADLINE_BELOW_ONE_ATTEMPT,
        )

        assert fake.calls == 2, (
            f"expected the retry to run and succeed; the seam made {fake.calls} attempt(s)"
        )

    async def test_a_FAST_conflicting_transaction_is_still_governed_by_the_deadline(
        self,
    ) -> None:
        """**POSITIVE CONTROL — mandatory.** The fix must restore the floor WITHOUT
        disabling the deadline.

        In the fast regime (the #102 case: millisecond attempts, many cheap retries)
        the wall clock is still the budget, and it must still cut the loop well ABOVE
        the floor. A build that "fixed" B1 by deleting the deadline would sail through
        the two pins above and fail this one.
        """
        fake = _SustainedConflictFakeConnection(response=_live_conflict_rollback_response())
        started = time.monotonic()
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(
                cast("_TxnRollbackFakeConnection", fake), deadline_seconds=0.25
            )
        elapsed = time.monotonic() - started

        attempts = getattr(exc_info.value, "attempts", 0)
        assert attempts > _MAX_TXN_CONFLICT_ATTEMPTS, (
            f"a FAST transaction stopped at {attempts} attempts — the deadline is no "
            f"longer buying retries in the regime it exists for. Did the fix delete it?"
        )
        assert elapsed < 2.0, (
            f"the deadline no longer bounds the fast regime ({elapsed:.2f}s for a 0.25s "
            f"budget) — the floor must not become an unbounded licence to retry"
        )

    @pytest.mark.parametrize(
        ("attempt_seconds", "deadline_seconds"),
        [
            pytest.param(0.10, 0.02, id="attempt-outlasts-deadline"),
            pytest.param(0.0, 0.25, id="instant-attempts"),
            pytest.param(0.0, 0.0, id="zero-deadline"),
        ],
    )
    async def test_the_typed_error_can_never_carry_fewer_attempts_than_the_floor(
        self, attempt_seconds: float, deadline_seconds: float
    ) -> None:
        """THE INVARIANT, across every regime including a pathological zero deadline:
        exhaustion is never reported below the floor. If this can be violated, some
        caller somewhere has silently lost its retry budget.
        """
        fake = _SlowConflictFakeConnection(
            response=_live_conflict_rollback_response(), attempt_seconds=attempt_seconds
        )
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(
                cast("_TxnRollbackFakeConnection", fake),
                deadline_seconds=deadline_seconds,
            )

        attempts = getattr(exc_info.value, "attempts", 0)
        assert attempts >= _MAX_TXN_CONFLICT_ATTEMPTS, (
            f"exhaustion reported {attempts} attempts, below the guaranteed floor of "
            f"{_MAX_TXN_CONFLICT_ATTEMPTS}"
        )
        assert fake.calls == attempts, "the reported attempt count must be the real one"


class TestTxnConflictRootCauseIsTheMarkerBearingEntry:
    """Finding #102 — ONE witness for the retry decision AND the report.

    The rule the seam must obey: **the entry you classify is the entry that
    made you decide.** ``_is_retryable_conflict`` decides to retry by scanning
    every failed statement for the engine's marker; when that retry budget
    finally drains, the entry reported as the root cause must be the SAME entry
    that drove the decision — the marker-bearing one — not whatever happens to
    sit at position ``[0]``.

    Selecting by POSITION cannot work for both cases and must not be attempted:
    the engine writes DOMAIN root causes FIRST (cascade after), but writes
    CONFLICT evidence LAST (non-execution noise before). ``[0]`` is right for
    one and wrong for the other; ``[-1]`` is right for the other and wrong for
    the first (that was finding #93). Only a SEMANTIC selector — seek the
    marker — is right for both, which is why these pins and
    ``TestTxnRootCauseSelection``'s (#93) must both stay green forever.
    """

    @pytest.mark.parametrize(("build_response", "marker_index", "statement_count"), _CONFLICT_SHAPES)
    async def test_server_log_names_the_marker_bearing_entry_as_the_root_cause(
        self,
        build_response: Callable[[], dict[str, Any]],
        marker_index: int,
        statement_count: int,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The exhausted-conflict receipt names the entry that carried the
        marker — the honest root cause — and its ordinal is therefore honest too.

        RED against a ``[0]``-classifying build on the LIVE shape: it reports
        statement_index 0 (a cascade entry whose text says only "the query was
        not executed due to a failed transaction" — a statement that never even
        RAN) as the cause of the rollback.
        """
        with caplog.at_level(logging.ERROR, logger="loremaster.store._txn"):
            _, _, error = await _exhaust_conflict(build_response(), monkeypatch=monkeypatch)

        error_records = [record for record in caplog.records if record.levelno == logging.ERROR]
        assert error_records, "an exhausted conflict must leave a server-side receipt"
        record = error_records[-1]
        assert getattr(record, "statement_index", None) == marker_index
        assert getattr(record, "statement_count", None) == statement_count
        # The receipt still carries EVERY failed statement — the cascade entries
        # are diagnostically useful even though they are not the root cause.
        failed = getattr(record, "failed_statements", None)
        assert failed is not None
        assert [entry["index"] for entry in failed] == list(range(statement_count))
        # The marker-bearing entry's raw text reached the log (never the raise).
        assert _CONFLICT_ENGINE_TEXT in str(failed[marker_index]["engine_result"])
        assert _CONFLICT_ENGINE_TEXT not in str(error)

    async def test_a_domain_rejection_is_never_labelled_a_conflict(self) -> None:
        """The counterweight — and the pin that stops an OVERCORRECTION.

        A build that "fixes" #102 by labelling every rollback a conflict (or by
        seeking the marker and falling back to the marker's label when there is
        none) would pass every conflict pin above. This is the case that kills
        it: a rollback with NO marker anywhere is a domain rejection, is never
        retried, and keeps finding #93's ``[0]`` root cause and its own specific
        label.
        """
        fake = _TxnRollbackFakeConnection(
            responses=[
                _rolled_back_response(
                    _SENSITIVE_ENGINE_TEXT, _CASCADE_ENGINE_TEXT, _COMMIT_ABORTED_ENGINE_TEXT
                )
            ]
        )
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(fake)

        message = str(exc_info.value).lower()
        assert _ERROR_CLASS_ASSERT_VIOLATION in message  # #93's root cause, preserved
        assert _ERROR_CLASS_RETRYABLE_CONFLICT not in message
        assert "statement 1 of 3" in message  # the FIRST entry — the real cause
        assert fake.calls == 1  # never retried


class TestTxnConflictBackoffIsJittered:
    """Finding #102 — the backoff must DESYNCHRONISE racers, and today it
    cannot.

    Today's seam sleeps ``BACKOFF * (attempt + 1)``: a pure function of the
    attempt index, identical for every racer. N transactions that collide on
    one row therefore sleep the IDENTICAL duration and re-collide in lockstep,
    attempt after attempt, until the budget drains. The only thing that has ever
    broken the lockstep is natural scheduling variance — which loses roughly
    half the time at 8-way (measured: 6 failures in 10 runs of the live mint).

    The repair draws a FRESH random duration on EVERY attempt. These pins read
    the durations back through a patched ``asyncio.sleep``, and are written to
    fail a build that:
      * sleeps a deterministic duration (today's build);
      * draws its jitter ONCE per call and reuses it (findings' dead backstop
        did exactly this — a slot derived from the finding id, redrawn never);
      * draws from a small DISCRETE set of slots (findings' dead backstop used 16,
        briefs' deleted mint loop used 4 — at N racers over S slots the pigeonhole
        guarantees collisions, and two racers that share a slot stay collided for
        every attempt);
      * grows the window without a CAP (an unbounded exponential);
      * jitters around a floor instead of down to zero (equal jitter rather than
        the full jitter the design ruled).
    """

    # Enough independent exhaustion runs that a CONTINUOUS random draw is
    # overwhelmingly likely to produce a distinct value every time, while a
    # DISCRETE slot scheme (16 slots, 4 slots, or a deterministic 1) cannot.
    # Not a tuned constant — a sample size, chosen so the discrimination below
    # is decisive rather than marginal.
    _SAMPLE_RUNS = 30
    # A continuous draw yields 30 distinct floats with probability ~1; the
    # richest discrete scheme in this repo's history (16 slots) can never exceed
    # 16 no matter how many runs are taken. Anything at or above this threshold
    # is continuous; anything below is not.
    _MIN_DISTINCT = 25
    # An absolute sanity ceiling on a single backoff, NOT a tuned cap: it sits
    # far above any plausible CAP (the design's starting value is 0.1s) and far
    # below where an UNCAPPED exponential lands within a normal budget
    # (5ms · 2^20 ≈ 87 minutes). A build that forgot to cap the growth blows
    # through it long before its attempts run out.
    _SANITY_SLEEP_CEILING_SECONDS = 5.0

    async def _sample_first_two_sleeps(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> tuple[list[float], list[float], list[float]]:
        """Exhaust the conflict ``_SAMPLE_RUNS`` times; return the first-attempt
        backoffs, the second-attempt backoffs, and every backoff observed.
        """
        first: list[float] = []
        second: list[float] = []
        every: list[float] = []
        for _ in range(self._SAMPLE_RUNS):
            _, recorder, _ = await _exhaust_conflict(
                _live_conflict_rollback_response(), monkeypatch=monkeypatch
            )
            assert len(recorder.durations) >= 2, (
                "a sustained conflict must back off between attempts; fewer than two "
                "sleeps means the seam is spinning without pause"
            )
            first.append(recorder.durations[0])
            second.append(recorder.durations[1])
            every.extend(recorder.durations)
        return first, second, every

    async def test_backoff_is_redrawn_at_random_on_every_attempt(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """THE lockstep pin. The first backoff of a run must differ from run to
        run — a fresh draw from a continuous distribution, not a constant and
        not a slot.

        RED against today's build: every run sleeps exactly
        the SAME fixed base delay first, so all 30 runs report ONE distinct value.
        """
        first, second, _ = await self._sample_first_two_sleeps(monkeypatch)

        assert len(set(first)) >= self._MIN_DISTINCT, (
            f"the first backoff took only {len(set(first))} distinct values across "
            f"{self._SAMPLE_RUNS} runs — a deterministic or slot-quantised backoff "
            f"leaves colliding racers in lockstep"
        )
        assert len(set(second)) >= self._MIN_DISTINCT, (
            "the SECOND backoff is quantised or deterministic — jitter must be "
            "redrawn on EVERY attempt, not once per call"
        )
        # Drawn independently per attempt: the two attempts' draws must not be a
        # fixed function of one another (a once-per-call slot reused across
        # attempts makes second == first * k for a per-run constant k).
        ratios = {round(b / a, 6) for a, b in zip(first, second, strict=True) if a > 0}
        assert len(ratios) >= self._MIN_DISTINCT, (
            "every run's second backoff is the same multiple of its first — the "
            "jitter was drawn ONCE and scaled, not redrawn per attempt"
        )

    async def test_backoff_window_grows_and_reaches_down_to_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The window is exponential (it GROWS between attempts) and it is FULL
        jitter (it reaches down toward zero, rather than jittering above a
        floor).

        Constant-free: it compares attempt 1's observed spread against attempt
        0's rather than asserting either bound's value, so the repair's survey
        is free to set BASE and CAP to whatever it measures.
        """
        first, second, _ = await self._sample_first_two_sleeps(monkeypatch)

        assert max(second) > max(first), (
            "the backoff window did not grow between the first and second attempt — "
            "sustained contention needs an EXPONENTIAL window, not a flat one"
        )
        # Full jitter: uniform(0, window) reaches into the bottom half of its own
        # window. Equal jitter (window/2 + uniform(0, window/2)) never does.
        assert min(first) < max(first) / 2, (
            "no first-attempt backoff landed in the lower half of its window — this "
            "is jitter around a FLOOR, not the full jitter that lets one racer go "
            "almost immediately while another waits"
        )

    async def test_no_backoff_exceeds_the_sanity_ceiling(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The exponential window is CAPPED — the pin against a growth term with
        no ceiling, which would park a caller for minutes on a busy row.
        """
        _, _, every = await self._sample_first_two_sleeps(monkeypatch)

        assert every, "no backoff was observed at all"
        assert max(every) < self._SANITY_SLEEP_CEILING_SECONDS, (
            f"a single backoff reached {max(every)}s — the exponential window is "
            f"uncapped"
        )


class TestConcurrentRacersDrawDistinctBackoffs:
    """**THE lockstep pin** — and the only one in this file that measures the
    property finding #102 is actually about.

    Why the sequential jitter pins above are not enough, proven rather than
    argued. The cold adversary built ``wb6-budget-only``: a **totally
    deterministic, zero-jitter, lockstepped** backoff with the attempt ceiling
    merely raised to 64. **It passes the live mint at 8-, 16- AND 32-way.** So the
    live-mint pins DISCRIMINATE (they prove the mint works) but cannot ATTRIBUTE
    (they cannot tell you *why*), and the entire defence against lockstep rests
    here.

    And the sequential sampler cannot carry that weight, because it measures the
    wrong axis. It draws 30 runs of ONE racer, so it sees per-attempt and per-call
    entropy — never **per-racer decorrelation**. A build with fresh entropy every
    attempt that is nonetheless IDENTICAL across concurrent racers produces plenty
    of distinct values globally and sails straight through. That build is the C1
    defect verbatim: ``BriefLedger.publish`` seeded its jitter from the CONTENDED
    ROW's id — a value every racer shares by definition — so all N racers slept
    the same duration, woke together, and re-collided forever.

    Sequential sampling holds against that today only by luck: an entropy source
    shared *between* racers (a row id, a coarse clock, a slot table) also happens
    to be constant *within* a call or *across* runs, so the sequential sampler
    trips over it. That is contingent, not structural. This pin makes it
    structural: N racers, colliding on one row, at the same time — exactly the
    scenario — each recording its own draws.
    """

    # Genuinely concurrent racers, at the house floor for a concurrency pin
    # (never 2-way). Enough that a shared entropy source collides visibly.
    _RACERS = 16
    # Repeat rounds so the full-jitter check has a large sample: 16 x 3 = 48
    # first-draws. A floor-jittered build cannot put ANY of them in the bottom
    # half of the window, so a single round would be a coin-flip and 48 is a
    # certainty.
    _ROUNDS = 3
    _MIN_DISTINCT_RATIOS = 12

    # How many of the 16 racers must draw a first backoff nobody else drew.
    #
    # NOT a guess, and NOT exact-distinctness. Exact distinctness (all 16) is a
    # COIN-FLIP against a legitimate build: a continuous draw rounded to a fine
    # grid decorrelates racers perfectly well, yet collides by birthday paradox
    # often enough to fail an ==16 assertion ~36% of the time. A pin that a good
    # build fails one run in three is the exact condition under which a builder
    # says "flaky" and ships — which this repo's law forbids, and which is how the
    # C1 mint defect reached production.
    #
    # So the threshold is MEASURED, from the distinct-count distribution of every
    # jitter build available (25 trials each, scratchpad/contract-v2/measure_distinct.py):
    #
    #     lockstep (production today, ceiling-only)   1 .. 1
    #     2-slot / 4-slot jitter                      2 .. 4
    #     16-slot jitter (THIS repo's own idiom)      8 .. 13     <- must die
    #     ------------------------------------------------------ the gap
    #     quantised continuous (fine grid)           15 .. 16     <- must live
    #     full continuous jitter (the design)        16 .. 16     <- must live
    #
    # WHAT THIS THRESHOLD DOES AND DOES NOT GUARANTEE — corrected, because my earlier
    # claim was wrong and a cold adversary measured it:
    #
    #   IT DOES: never false-fail the repair. A continuous draw yields distinct=16
    #     every time — 300/300 idle and 200/200 under loadavg 32 (adversary-measured;
    #     load-invariant BY CONSTRUCTION, since random.uniform reads no clock). And it
    #     deterministically condemns the defect this pin exists for: total lockstep
    #     (1 distinct), correlated entropy (row-seeded, clock-shared), and the coarse
    #     slot tables that are this repo's own history — 8-slot 0/300, 16-slot 1/300.
    #
    #   IT DOES NOT: adjudicate slot GRANULARITY. I previously claimed a "one-wide gap
    #     at 13->15" from 7 builds x 25 trials. That was FALSE — distinct-count is a
    #     SMOOTH function of slot size, so no threshold on it can separate the
    #     continuum. Re-measured over 300 trials: a 30-slot table passes 26% of the
    #     time, 45-slot 52%, 55-slot 70%. A coin-flip is not a guard.
    #
    # The granularity axis is adjudicated instead by
    # ``test_the_backoff_draw_is_continuous_not_a_slot_table`` below, which pools draws
    # across rounds and wins on a HARD COMBINATORIAL BOUND rather than a probability.
    # This pin keeps the job it can actually do: per-racer decorrelation.
    _MIN_DISTINCT_FIRST_DRAWS = 14

    async def test_concurrent_racers_draw_distinct_backoffs(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two racers that just collided must not sleep the SAME duration.

        RED before 8f24e11: every racer slept a fixed base delay x (attempt + 1) — a pure
        function of the attempt index, identical for all of them. All 16 woke together
        and re-collided. That was the lockstep, and it is what made the live 8-way mint
        fail 6 runs in 10.

        **Catches (each proven by the adversary as a build the old pins could not
        stop, or could stop only by luck):** any jitter derived from the contended
        row's identity (`wb5-row-seeded` — the literal C1 bug); any clock-derived
        jitter coarse enough that concurrent racers land in the same quantum
        (`wb16`, `wb17`); any deterministic backoff (`wb3`, `wb6-budget-only`).
        """
        recorder = await _exhaust_conflict_concurrently(self._RACERS, monkeypatch=monkeypatch)
        first_draws = recorder.first_draws()
        distinct = len(set(first_draws))

        assert distinct >= self._MIN_DISTINCT_FIRST_DRAWS, (
            f"only {distinct} of {len(first_draws)} concurrent racers drew a first "
            f"backoff nobody else drew — the rest wake together and re-collide on the "
            f"same row. This is the lockstep finding #102 IS. An entropy source shared "
            f"between racers (the contended row's id, a coarse clock, a slot table) is "
            f"not jitter. A discrete slot table is this repo's OWN historical idiom — "
            f"findings' dead backstop used 16 slots and briefs' deleted mint loop used "
            f"4 — and it is exactly what must not be copied here."
        )

    async def test_each_racer_redraws_its_own_entropy_every_attempt(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Per-racer decorrelation is not enough on its own: a build that draws ONE
        random value per call and scales it by the attempt index gives every racer a
        different first backoff (so the pin above passes) while every racer's
        *sequence* stays a fixed multiple of its own first draw.

        Catches `wb4-per-call-jitter`: every racer reports the identical
        second/first ratio, however random its single draw was.
        """
        recorder = await _exhaust_conflict_concurrently(self._RACERS, monkeypatch=monkeypatch)
        ratios = recorder.within_racer_ratios()

        assert len(ratios) >= 2, "not enough attempts per racer to compare draws"
        assert len(set(ratios)) >= self._MIN_DISTINCT_RATIOS, (
            f"the {len(ratios)} racers produced only {len(set(ratios))} distinct "
            f"second/first backoff ratios — each racer drew its entropy ONCE and "
            f"scaled it, rather than redrawing every attempt. Two racers that share a "
            f"window stay collided for the whole ladder."
        )

    async def test_concurrent_racers_draw_full_jitter_down_to_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Under real contention the window must reach down toward ZERO, so one
        racer can go almost immediately while another waits — that asymmetry is what
        breaks a tie.

        Catches `wb13-equal-jitter` (a floor plus half a window): its draws can
        never enter the bottom half of their own window, so N racers stay bunched
        even though each draw is random. Sampled across all rounds, so the verdict
        is a certainty rather than a coin-flip.
        """
        draws: list[float] = []
        for _ in range(self._ROUNDS):
            recorder = await _exhaust_conflict_concurrently(self._RACERS, monkeypatch=monkeypatch)
            draws.extend(recorder.first_draws())

        assert draws, "no backoff was observed at all"
        assert min(draws) < max(draws) / 2, (
            f"across {len(draws)} concurrent first-backoffs, none landed in the lower "
            f"half of the window (min={min(draws)}, max={max(draws)}) — this is jitter "
            f"around a FLOOR, not the full jitter the design ruled. Racers stay bunched."
        )

    # Pool first-draws across rounds: 4 x 16 = 64 samples, of which at least 50 must
    # be distinct.
    #
    # THIS is the statistic that adjudicates SLOT GRANULARITY, and it does so by a
    # HARD COMBINATORIAL BOUND rather than a probability: **a table of S slots can
    # never emit more than S distinct values, across any number of draws.** So every
    # S < 50 is not merely unlikely to pass — it is IMPOSSIBLE. Continuous jitter, by
    # contrast, emits a fresh float essentially every draw (64 of 64).
    #
    # It exists because the per-round distinct-count above CANNOT adjudicate
    # granularity: distinct-count is a smooth function of slot size, so any threshold
    # on it is straddled by some table. A cold adversary measured exactly that — my
    # earlier ">=14, one-wide gap" claim was derived from too few builds and is
    # EMPIRICALLY FALSE: a 30-slot table passed it 26% of the time, 45-slot 52%,
    # 55-slot 70%. A pin a wrong build survives one run in four is a coin-flip, and
    # this repo's law forbids shipping one.
    #
    # Measured (40 trials each, scratchpad/contract-v2/measure_pooled.py):
    #
    #     full continuous jitter (the design)     64 .. 64   ->  40/40 PASS
    #     fine quantisation (~500 slots)          56 .. 63   ->  40/40 PASS
    #     -------------------------------------------------------------- 50
    #     70-slot table                           37 .. 47   ->   0/40 RED
    #     55-slot table                           32 .. 43   ->   0/40 RED   (straddled before)
    #     45-slot table                           30 .. 39   ->   0/40 RED   (straddled before)
    #     30-slot table                           24 .. 29   ->   0/40 RED   (straddled before)
    #     16-slot table (findings' own idiom)     14 .. 16   ->   0/40 RED
    #     8-slot / coarse clock                    4 ..  8   ->   0/40 RED
    #
    # HONEST BOUND ON THE CLAIM: a table of ~100+ slots is NOT adjudicated by this pin
    # (measured 10/40). That is deliberate and it is where the boundary belongs: at 16
    # slots, 16 racers collide in ~8 pairs per round — the defect. At 100+ slots it is
    # ~1 pair, and at 500 (which passes) it is ~0.26. Beyond ~70 slots a quantised draw
    # is no longer the lockstep #102 is made of, and this contract does not condemn it.
    _ROUNDS_POOLED = 4
    _MIN_DISTINCT_POOLED = 50

    async def test_the_backoff_draw_is_continuous_not_a_slot_table(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The draw must come from a CONTINUOUS distribution, not a slot table.

        Catches the whole slot-table class — including the 30/45/55-slot tables that
        straddled the per-round threshold — by a bound no wrong build can argue with:
        it cannot produce more distinct values than it has slots.
        """
        draws: list[float] = []
        for _ in range(self._ROUNDS_POOLED):
            recorder = await _exhaust_conflict_concurrently(self._RACERS, monkeypatch=monkeypatch)
            draws.extend(recorder.first_draws())

        distinct = len(set(draws))
        assert distinct >= self._MIN_DISTINCT_POOLED, (
            f"only {distinct} distinct values across {len(draws)} pooled first-backoffs — "
            f"the backoff is drawn from a SLOT TABLE of at most {distinct} slots, not from "
            f"a continuous distribution. A slot table pigeonholes concurrent racers into "
            f"shared windows: they wake together and re-collide. This repo's own history "
            f"is the warning — findings' dead backstop used 16 slots and briefs' deleted "
            f"mint loop used 4. The design ruled uniform(0, window); draw from it."
        )


# ===========================================================================
# Finding #102 — the REPO INVARIANT the #93 → #102 kill chain lacked.
#
# The mechanism of the finding, stated once: findings' hand-rolled mint backstop
# (now deleted) gated its retry on the LABEL TEXT of a classified exception —
# ``if _ERROR_CLASS_RETRYABLE_CONFLICT not in str(error): raise``. When #93
# legitimately changed which statement gets classified, that label silently
# changed too, the substring stopped matching, and a 12-attempt backstop became
# dead code — with ZERO test signal, because no gate anywhere checks that a
# classification label still means what a distant ``except`` body assumes.
#
# A classification label is a HUMAN-FACING summary. It is not an API. Control
# flow that depends on one is a coupling no type checker, linter or test can
# see. The repair replaces the coupling with a TYPE (an exception class), and
# this scan is the instrument that keeps it replaced: a fix without an
# invariant is half a fix, and this defect CLASS has now cost two findings.
#
# THERE ARE NO EXEMPTIONS. ``briefs.py`` was the single, named, expiring one: it
# gated its LIVE single-statement mint retry on the label, because the
# single-statement path had no typed contention error to catch (finding #108).
# The DRY retry seam gives it one — the mint now calls ``_txn.retry_on_conflict``
# and hears about exhaustion as a TYPE — so the hand-rolled loop, the label import
# and the exemption are all DELETED together. The coupling class is now
# structurally impossible rather than merely discouraged, which was always the
# point: a self-cleaning exemption is a promise, and this repo's own law says a
# rule people must remember is not a guard, it is a hope.
#
# (The widened, prose-inclusive version of this ban — no production module may so
# much as MENTION a label or the engine's raw marker, docstrings included — lives in
# test_retry_seam.py::TestNoCallerEverReadsAnEngineMessage. An AST scan cannot see a
# docstring, and a future agent reads the docstring, not the AST.)
# ===========================================================================

# Every classification label a production ``except`` body might be tempted to
# match on — by CONSTANT name or by the bare literal text.
_CLASSIFICATION_LABEL_NAMES = frozenset(
    {
        "_ERROR_CLASS_RETRYABLE_CONFLICT",
        "_ERROR_CLASS_ASSERT_VIOLATION",
        "_ERROR_CLASS_FIELD_COERCION",
        "_ERROR_CLASS_QUERY_TOO_COMPLEX",
        "_ERROR_CLASS_UNSPECIFIED",
    }
)
_CLASSIFICATION_LABEL_VALUES = frozenset(
    {
        _ERROR_CLASS_RETRYABLE_CONFLICT,
        _ERROR_CLASS_ASSERT_VIOLATION,
        _ERROR_CLASS_FIELD_COERCION,
        _ERROR_CLASS_QUERY_TOO_COMPLEX,
        _ERROR_CLASS_UNSPECIFIED,
    }
)

# EMPTY, and it stays empty. Finding #108 migrated briefs' mint to the typed error,
# so the last exemption expired exactly as it was designed to. The set is kept (rather
# than deleted along with its member) because it is the thing a future violation will
# reach for first: an empty frozenset here is a standing refusal, and adding a name to
# it is a diff a reviewer can see.
#
# Any entry that ever returns must be matched on the module's PATH, never its BASENAME:
# a basename match would hand the exemption to ANY future file of that name anywhere in
# the package — a brand-new ``store/briefs.py`` would inherit an exemption nobody
# granted. Contrived as an attack; entirely plausible as an accident.
_LABEL_MATCH_EXEMPT_PATHS: frozenset[str] = frozenset()

# ``_txn.py`` DEFINES the labels and is the one module allowed to compare against
# marker text — that is the classifier's entire job. It is not an exemption from
# the invariant; it is the invariant's subject. (Path-matched, same reasoning.)
_LABEL_HOME_PATH = "store/_txn.py"

_PRODUCTION_ROOT = Path(__file__).resolve().parents[1] / "loremaster"


def _module_key(path: Path) -> str:
    """The module's path relative to the production root, POSIX-style — the key
    every exemption below is matched on. Never ``path.name``.
    """
    return path.relative_to(_PRODUCTION_ROOT).as_posix()


def _folded_string(node: ast.expr) -> str | None:
    """Constant-fold a string expression built from literals, so a label spelled
    as ``"retryable" + " conflict"`` is seen for what it is.

    (Adjacent literals — ``"retryable" " conflict"`` — are already folded by the
    PARSER into one ``Constant``, so they need no help here.)
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _folded_string(node.left)
        right = _folded_string(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _classification_label_holders(source: str) -> list[int]:
    """Return the line numbers where a module HOLDS a classification label at all —
    by importing its name, reaching it through a module attribute, referencing the
    name, or spelling its literal value.

    **This is the load-bearing invariant, and it replaces an arms race.** The v1
    contract scanned for ``in``/``not in`` comparisons inside ``except`` bodies.
    The cold adversary defeated that scan with **six of seven** evasions — the
    first being a one-line, entirely natural refactor::

        except SurrealStoreError as error:
            conflict_label = _ERROR_CLASS_RETRYABLE_CONFLICT   # now it is a local
            if conflict_label in str(error):                   # ...and invisible
                raise

    It then built a wrong implementation on exactly that shape (`wb-string-gate`)
    which reintroduced the #102 coupling into ``tasks.py`` and scored **545 passed,
    ruff clean, mypy exit 0 — byte-identical to a correct build.**

    Hardening the comparison matcher would invite the next evasion (``str.find``,
    a helper function, an f-string, a tuple loop…). So do not match the
    COMPARISON — deny the INGREDIENT. Every one of those seven shapes needs the
    label NAME in scope or its LITERAL in the source. A module that holds neither
    cannot branch on one, however it is written.

    A classification label is a human-facing summary, not an API. Control flow that
    depends on one is a coupling no type checker, linter or test can see — which is
    precisely how finding #93's legitimate change silently killed a retry loop and
    became finding #102.
    """
    offenders: list[int] = []
    for node in ast.walk(ast.parse(source)):
        # 1. `from loremaster.store._txn import _ERROR_CLASS_RETRYABLE_CONFLICT`
        if isinstance(node, ast.ImportFrom):
            if any(alias.name in _CLASSIFICATION_LABEL_NAMES for alias in node.names):
                offenders.append(node.lineno)
        # 2. `_txn._ERROR_CLASS_RETRYABLE_CONFLICT` — the module-attribute back door.
        elif isinstance(node, ast.Attribute):
            if node.attr in _CLASSIFICATION_LABEL_NAMES:
                offenders.append(node.lineno)
        # 3. ANY reference to the bare name (a local rebinding, a tuple, a helper's
        #    argument — the whole evasion family collapses into this one check).
        elif isinstance(node, ast.Name):
            if node.id in _CLASSIFICATION_LABEL_NAMES:
                offenders.append(node.lineno)
        # 4. The literal value, spelled out — including inside an f-string, and
        #    including a `+`-concatenation of literals.
        elif isinstance(node, ast.expr):
            folded = _folded_string(node)
            if folded is not None and folded in _CLASSIFICATION_LABEL_VALUES:
                offenders.append(node.lineno)
    return sorted(set(offenders))


# The seven ways a builder can branch on a classification label while the v1
# except-body scan sees nothing. SIX of these were built by the cold adversary
# and passed the v1 invariant; EVASION 1 is the one it used to construct
# `wb-string-gate`, the wrong build that scored 545 passed / ruff clean / mypy 0
# — byte-identical to a correct build. Every one of them is a positive control
# for the import ban below: they all need the NAME in scope or the LITERAL in
# the source, and the ban denies both.
_LABEL_EVASIONS: list[tuple[str, str]] = [
    (
        "bind-the-label-to-a-local",  # <-- built wb-string-gate; a ONE-LINE refactor
        """
def transition(self):
    try:
        write()
    except SurrealStoreError as error:
        conflict_label = _ERROR_CLASS_RETRYABLE_CONFLICT
        if conflict_label in str(error):
            raise
""",
    ),
    (
        "a-module-level-helper-does-the-match",
        """
def _is_conflict(error):
    return _ERROR_CLASS_RETRYABLE_CONFLICT in str(error)

def transition(self):
    try:
        write()
    except SurrealStoreError as error:
        if _is_conflict(error):
            raise
""",
    ),
    (
        "str-find-instead-of-in",
        """
def transition(self):
    try:
        write()
    except SurrealStoreError as error:
        if str(error).find(_ERROR_CLASS_RETRYABLE_CONFLICT) >= 0:
            raise
""",
    ),
    (
        "endswith-startswith",
        """
def transition(self):
    try:
        write()
    except SurrealStoreError as error:
        if str(error).endswith(_ERROR_CLASS_RETRYABLE_CONFLICT):
            raise
""",
    ),
    (
        "the-label-respelled-as-an-f-string",
        """
def transition(self):
    try:
        write()
    except SurrealStoreError as error:
        if f"retryable conflict" in str(error):
            raise
""",
    ),
    (
        "the-literal-split-across-a-concatenation",
        """
def transition(self):
    try:
        write()
    except SurrealStoreError as error:
        if "retryable" + " conflict" in str(error):
            raise
""",
    ),
    (
        "a-for-loop-over-a-tuple-of-labels",
        """
def transition(self):
    try:
        write()
    except SurrealStoreError as error:
        for label in (_ERROR_CLASS_RETRYABLE_CONFLICT,):
            if label in str(error):
                raise
""",
    ),
    (
        "the-module-attribute-back-door",
        """
from loremaster.store import _txn

def transition(self):
    try:
        write()
    except SurrealStoreError as error:
        if _txn._ERROR_CLASS_RETRYABLE_CONFLICT in str(error):
            raise
""",
    ),
]

# Code that legitimately holds NO label and must never be flagged — the negative
# half of the control. A scanner that cannot spare these is a scanner nobody can
# ship behind.
_LABEL_INNOCENTS: list[tuple[str, str]] = [
    (
        "the-repair-itself-branches-on-a-TYPE",
        """
def transition(self):
    try:
        write()
    except TxnContentionExhaustedError:
        raise
    except SurrealStoreError as error:
        fresh = self._select_row()
        raise IllegalTransitionError(str(fresh)) from error
""",
    ),
    (
        "prose-mentioning-the-label-in-a-docstring",
        """
def transition(self):
    '''Rolls back on a retryable conflict; see _ERROR_CLASS_RETRYABLE_CONFLICT.'''
    write()
""",
    ),
    (
        "matching-the-engines-RAW-marker-is-not-a-label",
        """
def _is_retryable_conflict(failed):
    return any(_RETRYABLE_CONFLICT_MARKER in str(f.raw_result) for f in failed)
""",
    ),
]


class TestNoProductionModuleHoldsAClassificationLabel:
    """A cheap, narrow TRIPWIRE — explicitly **not** the guard.

    THE guard against #102 is behavioural and lives in ``test_txn_contention.py``:
    ``TestContentionIsNeverReportedAsALostRace`` runs every pass-through pin against
    a REWORDED label, so a build that depends on the message's prose fails on a
    spelling it was not handed — however that dependence is written, and wherever it
    is routed. It needs no AST and no refactor evades it.

    Three revisions of this contract tried to forbid the coupling SYNTACTICALLY —
    ban the comparison, ban the label, ban the message reaching a condition — and a
    cold adversary defeated each with a one-line refactor; the last, most elaborate
    scanner waved through 13 of 15 evasions AND carried three false positives. **A
    syntactic scan over one ``except`` body cannot see prose that leaves the body**
    (a helper in another module, a ``match``, a bare ``except``, a classifier
    object). The evasion space is unbounded; it cannot be enumerated. That scanner
    is deleted.

    What survives is only this: **no production module may HOLD a classification
    label.** It is kept because it is honest about what it is — a lint. It is narrow
    (an import / a name / a literal), it had **zero** false positives against the
    live tree, and it fails FAST with a file and a line when someone reaches for the
    label. It catches the lazy path, not the determined one. The behavioural pin
    catches the determined one.

    Exempt: NOTHING. ``store/_txn.py`` is skipped because it DEFINES the labels and
    classifies engine text — the invariant's subject, not an exception to it. The one
    real exemption (``briefs.py``, whose single-statement mint had no typed contention
    error to catch) died with finding #108: the mint calls the shared driver now, and
    the label import went with the loop.
    """

    @pytest.mark.parametrize(("evasion", "source"), _LABEL_EVASIONS)
    def test_every_known_evasion_is_flagged(self, evasion: str, source: str) -> None:
        """POSITIVE CONTROLS — a lint that has not been shown FIRING is not even a
        lint. These are the shapes that reach for the label by name or literal.
        """
        assert _classification_label_holders(source), (
            f"evasion {evasion!r} is NOT flagged by the label tripwire"
        )

    @pytest.mark.parametrize(("innocent", "source"), _LABEL_INNOCENTS)
    def test_innocent_code_is_spared(self, innocent: str, source: str) -> None:
        """NEGATIVE CONTROLS. A lint that cries wolf gets disabled — which is how
        the deleted scanner would have died (it flagged the ubiquitous "stash the
        error text for telemetry, then branch on a retry counter" pattern).
        """
        assert not _classification_label_holders(source), (
            f"innocent shape {innocent!r} was flagged — the tripwire would refuse "
            f"correct code"
        )

    def test_no_production_module_holds_a_classification_label(self) -> None:
        """Zero false positives against the live tree — the reason this one is kept
        when its more ambitious siblings were deleted.
        """
        offenders: dict[str, list[int]] = {}
        for path in sorted(_PRODUCTION_ROOT.rglob("*.py")):
            key = _module_key(path)
            if key in _LABEL_MATCH_EXEMPT_PATHS or key == _LABEL_HOME_PATH:
                continue
            lines = _classification_label_holders(path.read_text(encoding="utf-8"))
            if lines:
                offenders[key] = lines

        assert not offenders, (
            f"production code HOLDS a classification label: {offenders}. A label is a "
            f"human-facing summary, not an API — finding #93 reworded one and silently "
            f"killed the retry loop that depended on it (that is finding #102). Branch "
            f"on the exception TYPE: catch TxnContentionExhaustedError."
        )


# ===========================================================================
# DELETED HERE (finding #108, the DRY retry seam):
#
#   * ``test_the_briefs_exemption_is_still_needed`` — the self-cleaning assertion that
#     forced this deletion. It fired exactly as designed: briefs no longer holds a
#     label, so the exemption had to go, and the assertion with it.
#
#   * ``TestBriefsInheritedConflictBudgetIsNotSilentlyRepointed`` — it pinned briefs'
#     PRIVATE 20-attempt mint budget (the seam's floor, multiplied by briefs' own
#     4-attempt app-level ladder) and the loop it drove, hand-rolled because the
#     substrate offered nothing to call. Every one of those things is now gone — the
#     retired names live in test_retired_symbols.py's registry, and naming them here
#     would be the very dangling reference that gate exists to forbid. **A test written
#     before a semantic change certifies the OLD world** (CLAUDE.md), and this one
#     certified the exact structure the change deletes — a suite can be green BECAUSE it
#     still asserts the corpse.
#
# Its LIVE half — the seam's floor must not be silently re-tuned or repointed — is not
# lost: it is re-pinned for the new world in
# test_retry_seam.py::TestTheAttemptFloorOutlivesItsBriefsConsumer, which asserts the
# floor is still 5 AND that it now has exactly ONE consumer (the driver that owns the
# policy) — the opposite invariant, for the opposite reason.
# ===========================================================================


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
_TRACE_TOOL = "lore_search"
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


@pytest_asyncio.fixture(params=["real", "fake"])
async def existence_store(request: pytest.FixtureRequest) -> AsyncIterator[SurrealStore]:
    """A ready store for the ``existing_point_ids`` parity pins — parametrized over
    BOTH the real SurrealDB-backed :class:`SurrealStore` and the adversarial
    in-memory :class:`FakeSurrealStore`.

    Mirrors ``trace_store``: the ``"real"`` branch calls the harness helpers
    (``make_env`` / ``connect_admin`` / ``drop_database``) directly rather than
    depending on the ``surreal_env`` fixture (resolving an async fixture from
    inside another async fixture's body re-enters pytest-asyncio 1.4's shared
    ``Runner``), and reaps its throwaway database on exit; the ``"fake"`` branch
    never touches the SurrealDB harness at all.
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
        # FakeSurrealStore satisfies the existing_point_ids contract behaviourally
        # (that IS this parity pin); the cast tells mypy what the suite proves.
        yield cast(SurrealStore, fake_store)


# ===========================================================================
# P8a #9 (notes-9b): the public BATCH existence read ``existing_point_ids``.
#
# The memory backend's drift oracle resolves N recalled refs in ONE query (not N
# point-fetches). ``existing_point_ids(ids) -> set[str]`` returns exactly the
# subset of ``ids`` that currently exist as chunk points; the keys NOT returned
# have drifted. Empty input short-circuits to the empty set with NO query; a down
# server RAISES (loud on failure, never a silent empty set the drift oracle would
# misread as "every ref was deleted"). Pinned fake+real; the single-query claim is
# proven against the fake's query counter.
# ===========================================================================


class TestExistingPointIds:
    """``existing_point_ids(ids)`` — the public batch existence read the memory
    backend's drift oracle rides (P8a #9 item 1). Parity: every case runs against
    BOTH the real store and the adversarial in-memory fake.
    """

    async def test_empty_input_returns_empty_set(
        self, existence_store: SurrealStore
    ) -> None:
        # No ids to resolve → the empty set (and, for the real store, no query
        # is issued — mirrors ``delete_points([])``'s early return).
        assert await existence_store.existing_point_ids([]) == set()

    async def test_returns_only_the_existing_subset(
        self, existence_store: SurrealStore
    ) -> None:
        present = chunk_record(tier=TIER_A, file_path="models/a.py", identity="Present")
        also_present = chunk_record(tier=TIER_B, file_path="models/b.py", identity="Also")
        await existence_store.upsert(
            [
                (present, unit_vector(0, PRODUCTION_DIM)),
                (also_present, unit_vector(1, PRODUCTION_DIM)),
            ]
        )
        absent = chunk_record(tier=TIER_A, file_path="models/gone.py", identity="Gone").point_id

        result = await existence_store.existing_point_ids(
            [present.point_id, absent, also_present.point_id]
        )
        # Exactly the stored subset — the absent id (the drift case) is omitted.
        assert result == {present.point_id, also_present.point_id}

    async def test_all_present_returns_every_id(
        self, existence_store: SurrealStore
    ) -> None:
        records = [
            chunk_record(tier=TIER_A, file_path=f"models/m{index}.py", identity=f"M{index}")
            for index in range(3)
        ]
        await existence_store.upsert(
            [(record, unit_vector(index, PRODUCTION_DIM)) for index, record in enumerate(records)]
        )
        ids = [record.point_id for record in records]
        assert await existence_store.existing_point_ids(ids) == set(ids)

    async def test_none_present_returns_empty_set(
        self, existence_store: SurrealStore
    ) -> None:
        # Every id asked for was never stored (or a refactor purged the file) → the
        # whole batch has drifted, so the existing subset is empty.
        absent_ids = [
            chunk_record(tier=TIER_A, file_path=f"deleted/{index}.py", identity=f"D{index}").point_id
            for index in range(4)
        ]
        assert await existence_store.existing_point_ids(absent_ids) == set()

    async def test_deduplicates_repeated_ids(
        self, existence_store: SurrealStore
    ) -> None:
        # A ref key can appear on several recalled memories; the same id passed
        # twice resolves to one membership result (a set is inherently deduped).
        record = chunk_record(tier=TIER_A, file_path="models/dup.py", identity="Dup")
        await existence_store.upsert([(record, unit_vector(0, PRODUCTION_DIM))])
        result = await existence_store.existing_point_ids(
            [record.point_id, record.point_id, record.point_id]
        )
        assert result == {record.point_id}

    async def test_is_point_scoped_not_a_table_probe(
        self, existence_store: SurrealStore
    ) -> None:
        # A stored chunk must not make a DIFFERENT id report existing — the batch
        # read is membership BY ID, never a "the table is non-empty" probe.
        present = chunk_record(tier=TIER_A, file_path="a.py", identity="Present")
        await existence_store.upsert([(present, unit_vector(2, PRODUCTION_DIM))])
        other = chunk_record(tier=TIER_B, file_path="b.py", identity="Other").point_id
        assert await existence_store.existing_point_ids([other]) == set()


class TestExistingPointIdsIsOneQuery:
    """``existing_point_ids`` resolves ALL ids in a SINGLE query — the whole point
    of the batch read (N point-fetches collapse to one). Proven against the fake's
    query counter (the real store's one ``WHERE id IN $ids`` statement is the same
    guarantee, unobservable from outside without a socket spy).
    """

    async def test_many_ids_resolve_in_exactly_one_query(self) -> None:
        fake_store = fake_surreal_trio(dim=PRODUCTION_DIM).store
        await fake_store.ensure_ready()
        records = [
            chunk_record(tier=TIER_A, file_path=f"models/n{index}.py", identity=f"N{index}")
            for index in range(20)
        ]
        await fake_store.upsert(
            [(record, unit_vector(index, PRODUCTION_DIM)) for index, record in enumerate(records)]
        )
        stored_ids = [record.point_id for record in records]
        absent_ids = [
            chunk_record(tier=TIER_A, file_path=f"gone/{index}.py", identity=f"G{index}").point_id
            for index in range(20)
        ]

        result = await fake_store.existing_point_ids(stored_ids + absent_ids)

        assert result == set(stored_ids)
        # ONE query resolved all 40 ids — not one point-fetch per id.
        assert fake_store.existing_point_ids_queries == 1

    async def test_empty_input_issues_no_query(self) -> None:
        fake_store = fake_surreal_trio(dim=PRODUCTION_DIM).store
        await fake_store.ensure_ready()
        assert await fake_store.existing_point_ids([]) == set()
        # The empty batch short-circuits — no query is issued at all.
        assert fake_store.existing_point_ids_queries == 0


class TestExistingPointIdsResilience:
    """``existing_point_ids`` is LOUD on failure — a down server RAISES a typed
    connection error, never a silent empty set (which the drift oracle would
    misread as "every ref was deleted"). Real-only: the fake has no socket to kill.
    """

    async def test_down_server_raises_never_silent_empty(
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
            await down_store.existing_point_ids(["loremaster:loremaster/x.py:symbol:X:0"])


# ===========================================================================
# THE INSTRUMENT — a live-engine classification suite (audit B2, design R2).
#
# ``_ERROR_CLASS_ASSERT_VIOLATION`` has NEVER ONCE FIRED IN PRODUCTION. Its marker
# is ``"assert"``; the engine's real ASSERT rejection says "…but field must conform
# to:…" and contains no such substring. So for this repo's entire life every ASSERT
# violation was served to callers as "unspecified rejection" — and every unit pin was
# green, because the fixtures were TYPED BY HAND with the word "assert" in them. The
# fixture and the code shared one imagination, and reality was never consulted.
#
# The marker fix is one line. **The marker fix is not the deliverable.** The
# deliverable is this: a [real]-tier suite that PROVOKES each class against the live
# engine and asserts the label the classifier ACTUALLY returns.
#
#     ** STANDING RULE: a classifier marker ships only with a live-engine pin that
#        provokes its class. A MARKER WITHOUT A PROVOCATION PIN IS PRESUMED FICTION. **
#
# Version-coupling is the POINT, not a cost: an engine upgrade that rewords its
# rejection text must fail HERE, loudly, at the gate — not silently degrade every
# label to "unspecified rejection" for another six months.
# ===========================================================================


@pytest_asyncio.fixture()
async def classification_probe() -> AsyncIterator[tuple[SurrealEnv, Any]]:
    """A live spike-surreal database carrying a REAL ``ASSERT`` and a REAL typed
    field, so each error class can be provoked for real rather than imagined.
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    connection = await connect_admin(env)
    await connection.query("DEFINE TABLE classify_probe SCHEMAFULL;")
    await connection.query(
        "DEFINE FIELD state ON classify_probe TYPE string "
        "ASSERT $value INSIDE ['open', 'done'];"
    )
    await connection.query("DEFINE FIELD ordinal ON classify_probe TYPE int;")
    try:
        yield env, connection
    finally:
        await connection.close()
        await drop_database(env)


async def _provoke_rejection(env: SurrealEnv, connection: Any, statement: str) -> str:
    """Run ``statement`` through the REAL ``execute_transaction`` against the REAL
    engine and return the classified message the caller would actually see.
    """

    async def _acquire() -> _SurrealConnection:
        return cast("_SurrealConnection", connection)

    async def _drop(_: Any) -> None:
        raise AssertionError("a domain rejection must never drop a healthy connection")

    with pytest.raises(SurrealStoreError) as exc_info:
        await execute_transaction(
            statement, {}, acquire=_acquire, drop=_drop, url=env.url
        )
    return str(exc_info.value).lower()


# Every class the classifier can return, so each provocation can be cross-controlled
# against ALL the others — a marker that matched everything would otherwise pass.
_ALL_ERROR_CLASSES = (
    _ERROR_CLASS_ASSERT_VIOLATION,
    _ERROR_CLASS_FIELD_COERCION,
    _ERROR_CLASS_RETRYABLE_CONFLICT,
    _ERROR_CLASS_QUERY_TOO_COMPLEX,
)


class TestLiveEngineClassification:
    """[real] tier — provoke each error class against SurrealDB and assert the label."""

    async def test_a_real_assert_violation_is_classified_as_an_assert_violation(
        self, classification_probe: tuple[SurrealEnv, Any]
    ) -> None:
        """RED before 8f24e11: the engine says "must conform to", the marker said "assert", and
        the caller was told "unspecified rejection". THE defect, provoked for real.
        """
        env, connection = classification_probe
        message = await _provoke_rejection(
            env,
            connection,
            "BEGIN;\nCREATE classify_probe:a SET state = 'BOGUS', ordinal = 1;\nCOMMIT;",
        )

        assert _ERROR_CLASS_ASSERT_VIOLATION in message, (
            f"a REAL ASSERT violation was classified as {message!r}. The marker does not "
            f"match what the engine actually emits — so this class has never fired."
        )
        # CROSS-CONTROL: its own class, and no sibling's.
        for other in _ALL_ERROR_CLASSES:
            if other != _ERROR_CLASS_ASSERT_VIOLATION:
                assert other not in message, f"also matched the sibling class {other!r}"

    async def test_a_real_coercion_failure_is_classified_as_field_coercion(
        self, classification_probe: tuple[SurrealEnv, Any]
    ) -> None:
        """The control that proves the suite can see a marker that DOES work: the
        coercion marker ("coerce") genuinely occurs in the engine's text. If this pin
        did not exist, the assert pin's RED could be blamed on the harness.
        """
        env, connection = classification_probe
        message = await _provoke_rejection(
            env,
            connection,
            "BEGIN;\nCREATE classify_probe:c SET state = 'open', ordinal = 'not-an-int';\nCOMMIT;",
        )

        assert _ERROR_CLASS_FIELD_COERCION in message
        for other in _ALL_ERROR_CLASSES:
            if other != _ERROR_CLASS_FIELD_COERCION:
                assert other not in message, f"also matched the sibling class {other!r}"

    async def test_the_two_domain_classes_do_not_collide(
        self, classification_probe: tuple[SurrealEnv, Any]
    ) -> None:
        """THE COLLISION CONTROL. A marker broad enough to match a sibling's text would
        silently merge two classes, and every single-class pin above would still pass.
        Provoke both, assert each yields exactly one class and they are DIFFERENT.
        """
        env, connection = classification_probe
        assert_message = await _provoke_rejection(
            env,
            connection,
            "BEGIN;\nCREATE classify_probe:x SET state = 'BOGUS', ordinal = 1;\nCOMMIT;",
        )
        coercion_message = await _provoke_rejection(
            env,
            connection,
            "BEGIN;\nCREATE classify_probe:y SET state = 'open', ordinal = 'nope';\nCOMMIT;",
        )

        assert _ERROR_CLASS_ASSERT_VIOLATION in assert_message
        assert _ERROR_CLASS_FIELD_COERCION in coercion_message
        assert _ERROR_CLASS_ASSERT_VIOLATION not in coercion_message
        assert _ERROR_CLASS_FIELD_COERCION not in assert_message

    async def test_the_unit_fixtures_still_match_the_live_engine(
        self, classification_probe: tuple[SurrealEnv, Any]
    ) -> None:
        """THE ANTI-DRIFT PIN — the one that would have caught B2 years ago.

        Every scripted-fake engine text in this file claims to be what the engine
        emits. This asserts it, against the engine. When SurrealDB rewords a rejection,
        this fails LOUDLY here instead of silently rotting every unit fixture into
        fiction.
        """
        env, connection = classification_probe
        raw = await connection.query_raw(
            "BEGIN;\n"
            "CREATE classify_probe:ok SET state = 'open', ordinal = 1;\n"
            "CREATE classify_probe:bad SET state = 'BOGUS', ordinal = 2;\n"
            "CREATE classify_probe:after SET state = 'done', ordinal = 3;\n"
            "COMMIT;"
        )
        entries = [str(entry.get("result")) for entry in (raw.get("result") or [])]
        blob = "\n".join(entries)

        # The SUBSTANTIVE rejection text our _SENSITIVE_ENGINE_TEXT fixture models.
        assert "must conform to" in blob, (
            "the engine no longer says 'must conform to' in an ASSERT rejection — every "
            "unit fixture and the classifier's marker are now fiction. Re-capture with "
            "scratchpad/contract-v5/capture_engine.py."
        )
        # The CASCADE notices our fixtures model — B3's whole point: statements BEFORE
        # the offender are stamped ERR, not OK.
        assert _CASCADE_ENGINE_TEXT in blob, (
            "the engine no longer emits the pre-offender cascade notice — the rollback "
            "SHAPE every fixture models has changed"
        )
        assert _COMMIT_ABORTED_ENGINE_TEXT in blob
        statuses = [entry.get("status") for entry in (raw.get("result") or [])]
        assert statuses.count("ERR") >= 3, (
            f"expected the engine to stamp the pre-offender statement ERR too; got "
            f"{statuses}. If this changed, TestTxnRootCauseSelection's shapes are stale."
        )


# ---------------------------------------------------------------------------
# Schema MIGRATION against an EXISTING store (ledger #107)
#
# Every other suite in this repo runs against a VIRGIN database
# (``_surreal_harness.unique_database()`` mints ``test_<pid>_<uuid4>`` per test)
# — and ``DEFINE FIELD IF NOT EXISTS`` cheerfully creates the NEW definition on a
# virgin store. So no test here has EVER applied a schema CHANGE to a store that
# already carried the OLD one, which is the only condition under which the defect
# appears. That blind spot let finding #98's widened ``briefed.via`` ASSERT ship
# past 1040 green comms tests, a cold code audit and a contract adversary, and
# take ``brief_publish`` down 100% in production. These pins mint a fresh database
# and then DIRTY IT DELIBERATELY: old definition -> a row that is legal under it
# -> the new definition -> did the change LAND, and did the data SURVIVE?
# ---------------------------------------------------------------------------

# A tiny embedding width for the migration databases: these pins exercise the DDL
# layer, never recall quality, and the blast-radius pin applies the WHOLE schema
# (both HNSW indexes) — at ``PRODUCTION_DIM`` that is needless work per test.
_MIGRATION_DIM = 8

# The probe table the field-level pins evolve. A dedicated table (not a real one)
# keeps the pins about ``_define_field`` — the SHARED emitter every table's DDL
# goes through — rather than about any single ledger's field list, which is free
# to change without weakening this invariant.
_MIGRATION_TABLE = "migration_probe"

# The probe's evolving column, and the unrelated column an UPDATE touches when a
# pin needs to prove that a row is (or is not) still WRITABLE after a migration.
_MIGRATION_FIELD = "via"
_MIGRATION_SIDE_FIELD = "tag"

# The narrow (OLD) and widened (NEW) closed sets — deliberately the exact shape of
# the change that broke production: two values, then three.
_OLD_CLOSED_SET = ("register", "explicit")
_NEW_CLOSED_SET = ("register", "explicit", "publish")

# A value in NEITHER set: the POSITIVE CONTROL. A migration that "works" by
# quietly DROPPING the ASSERT would accept the new value too — this value is how a
# pin tells a widened constraint apart from an absent one.
_OUT_OF_DOMAIN_VALUE = "bogus"


def _closed_set_assert(values: tuple[str, ...]) -> str:
    """The ``ASSERT`` clause pinning ``$value`` to ``values`` — the schema's own idiom.

    Mirrors how :mod:`loremaster.store.surreal_schema` builds every closed-domain
    constraint it emits (``file.state`` / ``task.status`` / ``briefed.via`` …).
    """
    allowed = ", ".join(f"'{value}'" for value in values)
    return f"ASSERT $value IN [{allowed}]"


def _probe_ddl(field_specs: tuple[tuple[str, str, str], ...]) -> str:
    """DDL for the probe table, emitted through the PRODUCTION helpers.

    Deliberately built from :func:`~loremaster.store.surreal_schema._define_table`
    and :func:`~loremaster.store.surreal_schema._define_field` rather than
    hand-written SurrealQL: the defect lives in the EMITTER, so a pin that wrote
    its own ``DEFINE FIELD`` string would test a copy of the code and pass while
    production stayed broken.
    """
    statements = [_define_table(_MIGRATION_TABLE)]
    statements += [
        _define_field(_MIGRATION_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in field_specs
    ]
    return ";\n".join(statements) + ";\n"


def _closed_set_specs(values: tuple[str, ...]) -> tuple[tuple[str, str, str], ...]:
    """The probe table's fields with its closed set pinned to ``values``."""
    return (
        (_MIGRATION_FIELD, "string", _closed_set_assert(values)),
        (_MIGRATION_SIDE_FIELD, "option<string>", ""),
    )


# The probe table typed for the TYPE-change pin: the same column as a ``string``,
# then as an ``int``. A TYPE change is the one migration shape that could plausibly
# fail LOUDLY or corrupt data, so it is measured, not assumed.
_STRING_TYPED_SPECS: tuple[tuple[str, str, str], ...] = (
    (_MIGRATION_FIELD, "string", ""),
    (_MIGRATION_SIDE_FIELD, "option<string>", ""),
)
_INT_TYPED_SPECS: tuple[tuple[str, str, str], ...] = (
    (_MIGRATION_FIELD, "int", ""),
    (_MIGRATION_SIDE_FIELD, "option<string>", ""),
)


async def _apply_ddl(connection: SurrealConnection, ddl: str, *, url: str) -> None:
    """Apply ``ddl`` EXACTLY as production does — one ``BEGIN … COMMIT`` through
    :func:`~loremaster.store._txn.execute_transaction`.

    Not a bare ``connection.query(ddl)``: the SDK inspects only the FIRST
    statement's status, so a later DDL statement's rejection would roll the whole
    schema back server-side while ``query()`` raised nothing at all (see
    :meth:`SurrealStore.ensure_ready`). A migration pin that applied its DDL the
    lax way could report a green migration over a schema the engine had just
    silently discarded.
    """

    async def _acquire() -> _SurrealConnection:
        # No cast: the harness's ``SurrealConnection`` IS the store's
        # ``_SurrealConnection`` union — a raw admin connection is exactly what the
        # transaction seam expects.
        return connection

    async def _never_drop(_connection: _SurrealConnection) -> None:
        raise AssertionError("a DDL rejection must never drop the connection")

    await execute_transaction(
        f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=_acquire, drop=_never_drop, url=url
    )


def _brief_ddl_before_the_via_widening() -> str:
    """The brief slice's DDL as it stood BEFORE finding #98 widened ``briefed.via``.

    DERIVED from the current generator (never hand-copied): the widened value is
    removed from whatever ASSERT the code emits today. The derivation CHECKS
    ITSELF — if removing the value stops changing the DDL (because the vocabulary
    moved on), this raises rather than handing back an "old" DDL identical to the
    new one, which would leave the pin passing while testing nothing at all.
    """
    current = generate_brief_ddl()
    old = current.replace(f", '{_BRIEFED_VIA_PUBLISH}'", "", 1)
    if old == current:
        raise AssertionError(
            f"the old-world derivation no longer changes anything: '{_BRIEFED_VIA_PUBLISH}' "
            "is not in the briefed.via ASSERT this code emits, so this fixture would "
            "'migrate' a schema to itself and pin nothing"
        )
    return old


@pytest_asyncio.fixture()
async def migration_db() -> AsyncIterator[tuple[SurrealConnection, SurrealEnv]]:
    """A raw admin connection on a fresh unique database, reaped on exit.

    The migration pins own their schema themselves — they apply an OLD definition,
    dirty the store, then apply the CURRENT one — so they need a bare connection,
    NOT a :class:`SurrealStore` that has already applied today's schema at
    ``ensure_ready``.
    """
    env = make_env(database=unique_database(), dim=_MIGRATION_DIM)
    connection = await connect_admin(env)
    try:
        yield connection, env
    finally:
        await connection.close()
        await drop_database(env)


class TestSchemaMigrationAgainstAnExistingStore:
    """The DDL layer must be able to EVOLVE (ledger #107).

    ``DEFINE FIELD IF NOT EXISTS`` is a NO-OP on a field that already exists, so
    ANY change to an existing field's definition — a widened ASSERT, a changed
    TYPE, a new DEFAULT — is silently discarded against a store that already
    carries the old one. Every long-lived deployment is such a store; no test in
    this repo was. These pins apply a schema CHANGE to a DIRTY database and demand
    that the change actually lands and the data survives.
    """

    async def test_a_widened_assert_lands_on_an_existing_field(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        connection, env = migration_db
        # The OLD world: the narrow closed set.
        await _apply_ddl(connection, _probe_ddl(_closed_set_specs(_OLD_CLOSED_SET)), url=env.url)
        # DIRTY THE STORE — a row that is legal under the OLD definition. This is
        # the whole condition the defect needs: the field must ALREADY EXIST.
        await run(
            connection,
            f"CREATE {_MIGRATION_TABLE}:legacy CONTENT {{ {_MIGRATION_FIELD}: $value }}",
            {"value": _OLD_CLOSED_SET[0]},
        )

        # The NEW world: the widened closed set, through the same emitter.
        await _apply_ddl(connection, _probe_ddl(_closed_set_specs(_NEW_CLOSED_SET)), url=env.url)

        # The change must have LANDED: a value legal ONLY under the new definition
        # is now accepted. Today the engine rejects it — the store still carries
        # the OLD ASSERT, exactly as it did when `brief_publish` went down.
        widened_value = _NEW_CLOSED_SET[-1]
        await run(
            connection,
            f"CREATE {_MIGRATION_TABLE}:widened CONTENT {{ {_MIGRATION_FIELD}: $value }}",
            {"value": widened_value},
        )
        rows = await run(
            connection, f"SELECT {_MIGRATION_FIELD} FROM {_MIGRATION_TABLE}:widened"
        )
        assert rows[0][_MIGRATION_FIELD] == widened_value

    async def test_the_migrated_field_still_rejects_an_out_of_domain_value(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        # THE POSITIVE CONTROL for the pin above. "The new value was accepted" is
        # worthless on its own: a migration that landed by DROPPING the ASSERT
        # entirely would accept it too — and would accept every typo'd garbage
        # value forever after. The constraint must be WIDER, not GONE.
        connection, env = migration_db
        await _apply_ddl(connection, _probe_ddl(_closed_set_specs(_OLD_CLOSED_SET)), url=env.url)
        await run(
            connection,
            f"CREATE {_MIGRATION_TABLE}:legacy CONTENT {{ {_MIGRATION_FIELD}: $value }}",
            {"value": _OLD_CLOSED_SET[0]},
        )

        await _apply_ddl(connection, _probe_ddl(_closed_set_specs(_NEW_CLOSED_SET)), url=env.url)

        with pytest.raises(SurrealError) as rejection:
            await run(
                connection,
                f"CREATE {_MIGRATION_TABLE}:garbage CONTENT {{ {_MIGRATION_FIELD}: $value }}",
                {"value": _OUT_OF_DOMAIN_VALUE},
            )
        # ...and rejected BY THE ASSERT (naming the offending value), never by a
        # parse error or a missing table — a probe that passes for the wrong
        # reason is the failure mode this whole class exists to end.
        assert _OUT_OF_DOMAIN_VALUE in str(rejection.value)
        assert _MIGRATION_FIELD in str(rejection.value)

    async def test_the_pre_existing_row_survives_the_migration(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        # A migration that "converges" the schema by destroying the rows that live
        # under it has not migrated anything. The dirty row must come through the
        # DDL change untouched.
        connection, env = migration_db
        await _apply_ddl(connection, _probe_ddl(_closed_set_specs(_OLD_CLOSED_SET)), url=env.url)
        await run(
            connection,
            f"CREATE {_MIGRATION_TABLE}:legacy CONTENT "
            f"{{ {_MIGRATION_FIELD}: $value, {_MIGRATION_SIDE_FIELD}: $tag }}",
            {"value": _OLD_CLOSED_SET[0], "tag": "keep-me"},
        )

        await _apply_ddl(connection, _probe_ddl(_closed_set_specs(_NEW_CLOSED_SET)), url=env.url)

        rows = await run(connection, f"SELECT * FROM {_MIGRATION_TABLE}:legacy")
        assert len(rows) == 1
        assert rows[0][_MIGRATION_FIELD] == _OLD_CLOSED_SET[0]
        assert rows[0][_MIGRATION_SIDE_FIELD] == "keep-me"
        # ...and it is still WRITABLE: a widening leaves every existing row legal,
        # so an update of an unrelated column must not trip the new ASSERT.
        await run(
            connection,
            f"UPDATE {_MIGRATION_TABLE}:legacy SET {_MIGRATION_SIDE_FIELD} = $tag",
            {"tag": "touched"},
        )
        rows = await run(connection, f"SELECT * FROM {_MIGRATION_TABLE}:legacy")
        assert rows[0][_MIGRATION_SIDE_FIELD] == "touched"

    async def test_reapplying_an_unchanged_definition_is_still_an_idempotent_no_op(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        # The guarantee ``IF NOT EXISTS`` buys today, and the one a fix must NOT
        # spend: ``ensure_ready`` runs the DDL unconditionally on every boot, so
        # re-applying an UNCHANGED definition must neither raise nor wipe data nor
        # loosen a constraint.
        connection, env = migration_db
        specs = _closed_set_specs(_NEW_CLOSED_SET)
        await _apply_ddl(connection, _probe_ddl(specs), url=env.url)
        await run(
            connection,
            f"CREATE {_MIGRATION_TABLE}:legacy CONTENT {{ {_MIGRATION_FIELD}: $value }}",
            {"value": _OLD_CLOSED_SET[0]},
        )

        await _apply_ddl(connection, _probe_ddl(specs), url=env.url)
        await _apply_ddl(connection, _probe_ddl(specs), url=env.url)

        rows = await run(connection, f"SELECT * FROM {_MIGRATION_TABLE}")
        assert len(rows) == 1
        assert rows[0][_MIGRATION_FIELD] == _OLD_CLOSED_SET[0]
        # The constraint is still THERE after the re-applications (the control: a
        # no-op that quietly stripped the ASSERT would still pass the count check).
        with pytest.raises(SurrealError):
            await run(
                connection,
                f"CREATE {_MIGRATION_TABLE}:garbage CONTENT {{ {_MIGRATION_FIELD}: $value }}",
                {"value": _OUT_OF_DOMAIN_VALUE},
            )

    async def test_a_narrowing_change_is_loud_never_a_silent_data_rewrite(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        """A migration that makes a constraint STRICTER while a row already
        violates the new rule: measured live against 3.1.5 (spike-surreal), not
        assumed.

        The measured behaviour, pinned here so an engine upgrade that starts
        silently mangling data goes RED: the DDL itself APPLIES cleanly; the
        now-illegal row is NEITHER deleted NOR rewritten (it reads back with its
        original value — the engine does not retro-validate rows at DDL time); new
        writes of the now-illegal value are REJECTED; and any UPDATE of the
        offending row — even of a completely unrelated column — FAILS LOUDLY,
        because the whole record is re-validated on write. The row is effectively
        read-only until it is fixed. Loud is the acceptable outcome; a silent
        coercion would not be.
        """
        connection, env = migration_db
        await _apply_ddl(connection, _probe_ddl(_closed_set_specs(_NEW_CLOSED_SET)), url=env.url)
        now_illegal_value = _NEW_CLOSED_SET[-1]
        await run(
            connection,
            f"CREATE {_MIGRATION_TABLE}:legacy CONTENT {{ {_MIGRATION_FIELD}: $value }}",
            {"value": now_illegal_value},
        )

        # NARROW the domain out from under that row.
        await _apply_ddl(connection, _probe_ddl(_closed_set_specs(_OLD_CLOSED_SET)), url=env.url)

        # 1. The narrowing LANDED: the value is no longer writable.
        with pytest.raises(SurrealError):
            await run(
                connection,
                f"CREATE {_MIGRATION_TABLE}:fresh CONTENT {{ {_MIGRATION_FIELD}: $value }}",
                {"value": now_illegal_value},
            )
        # 2. The existing row was NOT destroyed and NOT silently rewritten.
        rows = await run(connection, f"SELECT * FROM {_MIGRATION_TABLE}:legacy")
        assert len(rows) == 1
        assert rows[0][_MIGRATION_FIELD] == now_illegal_value
        # 3. Touching it fails LOUDLY, naming the field and the offending value —
        #    the row is write-poisoned until a migration fixes its data. Silence
        #    here (a swallowed write, a coerced value) would be the real defect.
        with pytest.raises(SurrealError) as rejection:
            await run(
                connection,
                f"UPDATE {_MIGRATION_TABLE}:legacy SET {_MIGRATION_SIDE_FIELD} = $tag",
                {"tag": "touched"},
            )
        assert _MIGRATION_FIELD in str(rejection.value)
        assert now_illegal_value in str(rejection.value)
        # 4. And the failed UPDATE left the row exactly as it was (no partial write).
        rows = await run(connection, f"SELECT * FROM {_MIGRATION_TABLE}:legacy")
        assert rows[0][_MIGRATION_FIELD] == now_illegal_value
        assert rows[0].get(_MIGRATION_SIDE_FIELD) is None
        # 5. CONTROL — the narrowed domain still ACCEPTS its own legal values, so
        #    the rejections above are the ASSERT working, not the table broken.
        await run(
            connection,
            f"CREATE {_MIGRATION_TABLE}:ok CONTENT {{ {_MIGRATION_FIELD}: $value }}",
            {"value": _OLD_CLOSED_SET[1]},
        )

    async def test_a_type_change_on_a_populated_table_is_loud_never_silent(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        """A field's TYPE (not merely its ASSERT) changing on a table that ALREADY
        HAS ROWS — the one migration shape that could plausibly fail badly.
        Measured live against 3.1.5, then pinned.

        The measured behaviour: the DDL APPLIES (it does not raise, and it does not
        touch existing rows); the old-typed rows still READ BACK with their old
        values — including one that LOOKS coercible (``'7'``), which is NOT
        silently turned into ``7``; new writes are held to the NEW type; and any
        UPDATE of an old-typed row FAILS LOUDLY with a coercion error. So a TYPE
        change converges the SCHEMA but never the DATA: the rows must be migrated
        separately or they are write-poisoned. That is the fact a builder flipping
        this DDL layer needs, and this pin is where it is written down.
        """
        connection, env = migration_db
        await _apply_ddl(connection, _probe_ddl(_STRING_TYPED_SPECS), url=env.url)
        await run(
            connection,
            f"CREATE {_MIGRATION_TABLE}:coercible CONTENT {{ {_MIGRATION_FIELD}: $value }}",
            {"value": "7"},
        )
        await run(
            connection,
            f"CREATE {_MIGRATION_TABLE}:garbage CONTENT {{ {_MIGRATION_FIELD}: $value }}",
            {"value": "abc"},
        )

        # string -> int, on a table with rows of both kinds.
        await _apply_ddl(connection, _probe_ddl(_INT_TYPED_SPECS), url=env.url)

        # 1. The TYPE change LANDED: new writes are held to the new type...
        await run(
            connection,
            f"CREATE {_MIGRATION_TABLE}:fresh CONTENT {{ {_MIGRATION_FIELD}: $value }}",
            {"value": 5},
        )
        # ...and a string is no longer accepted (the control: this is what proves
        # the DDL converged rather than the ``int`` write merely being tolerated by
        # a still-``string`` column).
        with pytest.raises(SurrealError):
            await run(
                connection,
                f"CREATE {_MIGRATION_TABLE}:rejected CONTENT {{ {_MIGRATION_FIELD}: $value }}",
                {"value": "abc"},
            )
        # 2. The old rows survived, UNCOERCED — no silent data mangling.
        rows = await run(connection, f"SELECT * FROM {_MIGRATION_TABLE}:coercible")
        assert rows[0][_MIGRATION_FIELD] == "7"
        rows = await run(connection, f"SELECT * FROM {_MIGRATION_TABLE}:garbage")
        assert rows[0][_MIGRATION_FIELD] == "abc"
        # 3. But they are WRITE-POISONED, loudly: the engine refuses to coerce the
        #    old value to the new type, and says so. (Even the "coercible" one.)
        for record_id in ("coercible", "garbage"):
            with pytest.raises(SurrealError) as rejection:
                await run(
                    connection,
                    f"UPDATE {_MIGRATION_TABLE}:{record_id} SET {_MIGRATION_SIDE_FIELD} = $tag",
                    {"tag": "touched"},
                )
            assert _MIGRATION_FIELD in str(rejection.value)

    async def test_the_briefed_via_widening_that_broke_production(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        """The exact regression: finding #98's widened ``briefed.via`` applied to a
        store that already carries the OLD two-value ASSERT — i.e. production.

        Distinct from the ``_define_field`` pins above, and NOT redundant with
        them: this one drives the REAL generators
        (:func:`~loremaster.store.surreal_schema.generate_agent_ddl` /
        :func:`~loremaster.store.surreal_schema.generate_brief_ddl`) that
        :meth:`~loremaster.briefs.BriefLedger.ensure_ready` actually applies, so a
        fix that teaches ``_define_field`` a new opt-in ``overwrite=True`` flag —
        and then forgets to pass it from the generators — dies HERE while passing
        every pin above.
        """
        connection, env = migration_db
        # The store as it was BEFORE #98: agent + brief slices, two-value via.
        await _apply_ddl(connection, generate_agent_ddl(), url=env.url)
        await _apply_ddl(connection, _brief_ddl_before_the_via_widening(), url=env.url)
        stamp = datetime.now(UTC)
        await run(
            connection,
            f"CREATE {AGENT_TABLE}:publisher CONTENT $content",
            {
                "content": {
                    "name": "c1f-publisher",
                    "session": "migration-probe",
                    "role": "the brief's own author",
                    "status": "active",
                    "registered_at": stamp,
                    "heartbeat_at": stamp,
                }
            },
        )
        for version in (1, 2):
            await run(
                connection,
                f"CREATE {BRIEF_TABLE}:v{version} CONTENT $content",
                {
                    "content": {
                        "name": "project",
                        "version": version,
                        "body": f"the standing brief, version {version}",
                        "created_by": "c1f-publisher",
                    }
                },
            )
        # A row under the OLD definition: the store is now genuinely dirty.
        await run(
            connection,
            f"RELATE {AGENT_TABLE}:publisher->{BRIEFED_RELATION}->{BRIEF_TABLE}:v1 "
            "CONTENT { via: 'register' }",
        )

        # Deploy today's code against that store — exactly what BriefLedger does.
        await _apply_ddl(connection, generate_agent_ddl(), url=env.url)
        await _apply_ddl(connection, generate_brief_ddl(), url=env.url)

        # The publish-time self-ack. In production this RELATE was rejected by the
        # stale two-value ASSERT and rolled back the whole publish transaction —
        # every `brief_publish` failed, 100%.
        await run(
            connection,
            f"RELATE {AGENT_TABLE}:publisher->{BRIEFED_RELATION}->{BRIEF_TABLE}:v2 "
            "CONTENT { via: $via }",
            {"via": _BRIEFED_VIA_PUBLISH},
        )
        edges = await run(connection, f"SELECT via FROM {BRIEFED_RELATION}")
        assert sorted(edge["via"] for edge in edges) == sorted(["register", _BRIEFED_VIA_PUBLISH])

        # CONTROL: the widened domain is WIDER, not ABSENT — a junk ``via`` is
        # still rejected, so the pin above cannot pass by the ASSERT vanishing.
        with pytest.raises(SurrealError) as rejection:
            await run(
                connection,
                f"RELATE {AGENT_TABLE}:publisher->{BRIEFED_RELATION}->{BRIEF_TABLE}:v1 "
                "CONTENT { via: $via }",
                {"via": _OUT_OF_DOMAIN_VALUE},
            )
        assert _OUT_OF_DOMAIN_VALUE in str(rejection.value)

    async def test_the_whole_schema_migrates_an_existing_populated_store(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        """The blast radius is EVERY ledger: ``_define_field`` emits the DDL for
        chunk / file / memory / trace / task / finding / agent / brief / the graph.

        So: populate one row in each of those tables, re-apply the ENTIRE schema
        (every slice ``ensure_ready`` applies, in the same one-transaction way),
        and demand that every row survives byte-identically AND that the
        constraints still bite. A fix that converges the schema by dropping and
        re-creating a table would pass every widening pin above and destroy the
        production store; this is the pin that catches it.
        """
        connection, env = migration_db
        ddl_slices = (
            generate_ddl(dim=_MIGRATION_DIM),
            generate_graph_ddl(),
            generate_agent_ddl(),
            generate_brief_ddl(),
        )
        for ddl in ddl_slices:
            await _apply_ddl(connection, ddl, url=env.url)

        stamp = datetime.now(UTC)
        record = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py", identity="PurchaseOrder.action_confirm"
        )
        seeds: tuple[tuple[str, str, dict[str, Any]], ...] = (
            (
                CHUNK_TABLE,
                # ``type::record`` (NOT ``type::thing`` — that is a parse error on
                # 3.1.5): the chunk's record id is the PRODUCTION uuid5 point id.
                "type::record($table, $key)",
                {**record.payload, "embedding": unit_vector(0, _MIGRATION_DIM)},
            ),
            (
                FILE_TABLE,
                f"{FILE_TABLE}:probe",
                {
                    "sha512": sha512_hex("body"),
                    "mtime_ns": time.time_ns(),
                    "size": 4,
                    "n_chunks": 1,
                    "chunk_ids": [record.point_id],
                    "state": "indexed",
                    "updated_at": stamp,
                },
            ),
            (
                MEMORY_TABLE,
                f"{MEMORY_TABLE}:probe",
                {
                    "note_text": "the store survives its own migration",
                    "kind": "fact",
                    "source": {"kind": "agent", "ref": "c1f", "trust": "high"},
                    "created_at": stamp,
                    "embedding": unit_vector(1, _MIGRATION_DIM),
                },
            ),
            (
                TRACE_TABLE,
                f"{TRACE_TABLE}:probe",
                {
                    "tool": "lore_search",
                    "params_hash": sha512_hex("params"),
                    "hit_count": 3,
                    "latency_ms": 12.5,
                    "session": "migration-probe",
                },
            ),
            (
                TASK_TABLE,
                f"{TASK_TABLE}:probe",
                {
                    "subject": "survive the migration",
                    "description": "a task row written under the OLD schema",
                    "status": "open",
                    "provenance": {"created_by": "c1f"},
                    "created_at": stamp,
                },
            ),
            (
                FINDING_TABLE,
                f"{FINDING_TABLE}:probe",
                {
                    "number": 107,
                    "kind": "bug",
                    "subject": "the schema cannot evolve",
                    "body": "a finding row written under the OLD schema",
                    "area": "loremaster.store.surreal_schema",
                    "category": "bug",
                    "created_by": "c1f",
                    "provenance": {"created_by": "c1f"},
                },
            ),
            (
                AGENT_TABLE,
                f"{AGENT_TABLE}:probe",
                {
                    "name": "c1f-probe",
                    "session": "migration-probe",
                    "role": "a registered agent from before the deploy",
                    "status": "active",
                    "registered_at": stamp,
                    "heartbeat_at": stamp,
                },
            ),
            (
                BRIEF_TABLE,
                f"{BRIEF_TABLE}:probe",
                {
                    "name": "project",
                    "version": 1,
                    "body": "a brief published under the OLD schema",
                    "created_by": "c1f",
                },
            ),
        )
        for table, target, content in seeds:
            await run(
                connection,
                f"CREATE {target} CONTENT $content",
                {"table": table, "key": record.point_id, "content": content},
            )
        await run(
            connection,
            f"RELATE {AGENT_TABLE}:probe->{BRIEFED_RELATION}->{BRIEF_TABLE}:probe "
            "CONTENT { via: 'register' }",
        )

        # THE DEPLOY: re-apply every slice to the now-populated store.
        for ddl in ddl_slices:
            await _apply_ddl(connection, ddl, url=env.url)

        # 1. Every seeded row survived — same count, same content.
        for table, _target, content in seeds:
            rows = await run(connection, f"SELECT * FROM {table}")
            assert len(rows) == 1, f"{table} lost (or duplicated) its row across the migration"
            for key, value in content.items():
                if key in {"embedding", "created_at", "updated_at", "registered_at", "heartbeat_at"}:
                    continue  # floats / engine datetimes: presence is pinned by the row surviving
                assert rows[0][key] == value, f"{table}.{key} changed across the migration"
        edges = await run(connection, f"SELECT via FROM {BRIEFED_RELATION}")
        assert [edge["via"] for edge in edges] == ["register"]

        # 2. The constraints still BITE after the re-application (the control: a
        #    migration that converged by loosening every table would pass step 1).
        with pytest.raises(SurrealError):
            await run(
                connection,
                f"CREATE {FILE_TABLE}:bogus CONTENT $content",
                {
                    "content": {
                        "sha512": sha512_hex("x"),
                        "mtime_ns": 1,
                        "size": 1,
                        "n_chunks": 0,
                        "chunk_ids": [],
                        "state": _OUT_OF_DOMAIN_VALUE,
                        "updated_at": stamp,
                    }
                },
            )
        with pytest.raises(SurrealError):
            await run(
                connection,
                f"CREATE {TASK_TABLE}:bogus CONTENT $content",
                {
                    "content": {
                        "subject": "s",
                        "description": "d",
                        "status": _OUT_OF_DOMAIN_VALUE,
                        "provenance": {},
                        "created_at": stamp,
                    }
                },
            )
        # 3. ...and the store is still WRITABLE for legal rows.
        await run(
            connection,
            f"CREATE {TASK_TABLE}:after CONTENT $content",
            {
                "content": {
                    "subject": "written after the migration",
                    "description": "d",
                    "status": "open",
                    "provenance": {},
                    "created_at": stamp,
                }
            },
        )
