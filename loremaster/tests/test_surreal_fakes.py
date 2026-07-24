"""Contract tests for the P6 READ-PATH extension to
``loremaster.tests._surreal_fakes.FakeSurrealStore``: ``hybrid_search`` and
``scroll``.

P5 project-memory lesson (the reason this file exists as its OWN adversarial
pass, not just "whatever makes the pipeline tests pass"): a too-faithful fake
once shipped a silent-corruption bug GREEN because it consumed keyed results
POSITIONALLY, trusting an assumed order that production never actually
promises. A fake that is merely "faithful to the happy path" — same method
names, same signatures, plausible-looking data — is not enough; it must also
be willing to LIE the way production genuinely can: a down connection raises
(never a silent empty), ties do not resolve by insertion order, and a
filter/`k`/emptiness edge case behaves exactly as the real engine's own
contract (pinned in ``test_surreal_store.py``) says it must.

This file pins TWELVE invariants (see the class docstrings for which is
which):

 1. ``hybrid_search`` signature parity with the real ``SurrealStore``.
 2. Return type is the REAL ``Candidate`` (not a lookalike), keyed by the bare
    point id, ``origin="fused"``, scores on the RRF scale (not cosine scale).
 3. Honest emptiness: a healthy-but-empty/no-match store returns ``[]``, never
    raises.
 4. The vector arm alone ranks a genuinely nearest chunk first.
 5. The BM25 arm alone rescues a chunk whose vector is a poor match.
 6. Filters scope BOTH arms with FULL-``k`` recall inside the scope.
 7. A hostile filter KEY raises ``SurrealStoreError`` — the same allow-list
    defense the real store enforces.
 8. ``k`` binds the result count, including when it exceeds corpus size.
 9. Equal-relevance ties are resolved in a PROVABLY non-insertion order.
10. A failure-injection seam lets a test arm the fake to raise
    ``SurrealConnectionError`` on demand, then recover.
11. ``scroll`` signature/behavioural parity (limit, honest emptiness, hostile
    keys, non-insertion-order ties — the exact hazard ``symbols.py`` documents
    at ``_find_by_identity``).
12. Neither a ``Candidate.payload`` nor a scroll row ever leaks the raw stored
    vector or the fake's own internal ``"__point_id"`` bookkeeping key.

Expected RED against the current ``_surreal_fakes.py``: ``FakeSurrealStore``
has no ``hybrid_search``/``scroll``/``arm_connection_failure`` yet, so almost
every test here fails with an ``AttributeError`` at CALL time (not at
collection — nothing here references those methods at import time), which is
the informative, per-test RED this contract wants.
"""

from __future__ import annotations

import ast
import inspect
import math
from collections.abc import Callable
from datetime import datetime
from typing import Any

import pytest
from _surreal_fakes import FakeSurrealCodeGraph, FakeSurrealStore, fake_surreal_trio
from _surreal_harness import PRODUCTION_DIM, TIER_A, TIER_B, chunk_record, unit_vector
from loremaster.graph import KIND_CLASS, KIND_FUNCTION, KIND_METHOD, KIND_MODULE, GraphNode
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.records import Record, sha512_hex
from loremaster.store.candidate import Candidate
from loremaster.store.surreal import (
    _RRF_K as _PRODUCTION_RRF_K,
)
from loremaster.store.surreal import (
    SurrealConnectionError,
    SurrealStore,
    SurrealStoreError,
)
from loremaster.store.surreal_schema import CHUNK_FILTER_KEYS
from loremaster.symbols import _SCROLL_LIMIT  # the real scroll caller's read cap
from lorescribe.models import ChunkContext
from lorescribe.python_ast import PythonAstChunker

# Hostile filter KEYS an agent-facing search tool could pass through P6's
# ``search_code``/``get_symbol`` tools. None may be silently accepted: the real
# store treats an unknown filter key as a SurrealQL-injection vector (the KEY,
# not just the value, would otherwise be interpolated). The fake must enforce
# the SAME allow-list class of defense so a test written against the fake
# never certifies a permissiveness the real store would reject.
_HOSTILE_FILTER_KEYS = (
    "a; DELETE chunk; --",       # multi-statement injection shape
    "tier = 'x' OR '1'='1'",     # boolean-tautology injection shape
    "tｉer",                      # unicode homoglyph (U+FF49) — NOT "tier"
    "",                          # empty key
    "nonexistent_field",         # clean-looking, but not a real chunk column
    "embedding",                 # a REAL chunk column, but not a filter dimension
)

# A harmless, well-formed value per ALLOWED filter column — imported from the
# schema's own single source of truth (never a hand-copied twin), so this test
# can never silently drift from the real allow-list.
_ALLOWED_KEY_VALUES: dict[str, str] = {
    "tier": TIER_A,
    "file_path": "models/purchase_order.py",
    "chunk_type": "python_symbol",
    "identity": "PurchaseOrder.action_confirm",
    "content_hash": "0" * 128,
}

# The RRF score ceiling every fused hit must respect. Grounded in production's
# OWN RRF constant (imported, not re-guessed): a rank-1 hit on BOTH arms tops
# out at 2/(_RRF_K + 1); with production's _RRF_K == 60 that ceiling is
# ~0.033. The fake is free to choose its OWN internal RRF constant, so this
# test asserts the LOOSE-but-load-bearing ``< 1.0`` bound rather than the
# tight production value — loose enough to accommodate any reasonable
# implementer choice, while still catching the adversarial failure mode this
# guards against: a COSINE-scale fake (scores clustering near 1.0 for a
# near-identical vector) goes red here.
assert 2 / (_PRODUCTION_RRF_K + 1) < 1.0  # documents WHY 1.0 is a safe ceiling
_RRF_SCORE_CEILING = 1.0


def _params_excluding_self(func: Callable[..., Any]) -> dict[str, inspect.Parameter]:
    """The callable's parameters, dropping ``self`` — for cross-class signature diffs."""
    return {
        name: parameter
        for name, parameter in inspect.signature(func).parameters.items()
        if name != "self"
    }


def _distractor(index: int, *, tier: str = TIER_A, axis: int) -> tuple[Record, list[float]]:
    """A widget-factory chunk with NO lexical overlap with the domain queries
    under test (realistic Odoo-style code text — deliberately not
    ``foo``/``bar``), paired with a vector on the given ``axis``.
    """
    record = chunk_record(
        tier=tier,
        file_path=f"models/widget_{index}.py",
        identity=f"WidgetFactory.build_{index}",
        ident_text=f"WidgetFactory build_gizmo_{index}",
        source_text=f"def build_gizmo_{index}(self):\n    return {index}\n",
    )
    return record, unit_vector(axis, PRODUCTION_DIM)


def _duplicate_hit(suffix: str, *, tier: str = TIER_A, axis: int) -> tuple[Record, list[float]]:
    """A chunk deliberately IDENTICAL to its siblings in every SCORED dimension.

    Only ``identity``/``file_path`` (and thus the derived point id) differ
    across ``suffix`` values; ``ident_text``/``source_text`` and the paired
    vector are byte-identical. Under any sane hybrid-fusion formula every
    sibling is therefore an EQUAL-relevance hit — the real-world analogue is a
    boilerplate override (the same ``def action_confirm(self):`` body)
    repeated verbatim across several modules, not a contrived tie.
    """
    record = chunk_record(
        tier=tier,
        file_path=f"models/purchase_order_{suffix}.py",
        identity=f"PurchaseOrder.action_confirm_{suffix}",
        ident_text="PurchaseOrder action_confirm",
    )
    return record, unit_vector(axis, PRODUCTION_DIM)


@pytest.fixture()
def store() -> FakeSurrealStore:
    """A fresh, empty fake store at the PRODUCTION embedding width, per test."""
    return fake_surreal_trio(dim=PRODUCTION_DIM).store


class TestSignatureParity:
    """The fake's read-path methods must be structurally IDENTICAL callables to
    the real store's — same parameter names/kinds/defaults, both ``async def``
    — the SAME faithfulness invariant this module's write-path methods already
    keep (see ``_surreal_fakes.py``'s own docstring). Pins contract item 1 (and
    the signature half of item 11).
    """

    def test_hybrid_search_signature_matches_real_store(self) -> None:
        real_params = _params_excluding_self(SurrealStore.hybrid_search)
        fake_params = _params_excluding_self(FakeSurrealStore.hybrid_search)
        assert list(fake_params) == list(real_params) == [
            "query_vector",
            "query_text",
            "k",
            "filters",
        ]
        for name, real_param in real_params.items():
            fake_param = fake_params[name]
            # KEYWORD_ONLY on both sides — a caller may never pass these
            # positionally, on the fake any more than on the real store.
            assert fake_param.kind == real_param.kind == inspect.Parameter.KEYWORD_ONLY, name
            assert fake_param.default == real_param.default, name
        assert inspect.iscoroutinefunction(FakeSurrealStore.hybrid_search)

    def test_scroll_signature_matches_real_store(self) -> None:
        real_params = _params_excluding_self(SurrealStore.scroll)
        fake_params = _params_excluding_self(FakeSurrealStore.scroll)
        assert list(fake_params) == list(real_params) == ["filters", "limit"]
        for name, real_param in real_params.items():
            fake_param = fake_params[name]
            assert fake_param.kind == real_param.kind, name
            assert fake_param.default == real_param.default, name
        assert inspect.iscoroutinefunction(FakeSurrealStore.scroll)


class TestCandidateContract:
    """Every ``hybrid_search`` hit is the REAL, neutral ``Candidate`` value
    object (never a lookalike/dict), keyed by the BARE point id, always
    ``origin="fused"``, with a score on the RRF scale. Pins contract item 2.
    """

    async def test_hybrid_search_returns_real_candidate_instances(
        self, store: FakeSurrealStore
    ) -> None:
        record = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py",
            identity="PurchaseOrder.action_confirm",
        )
        await store.upsert([(record, unit_vector(0, PRODUCTION_DIM))])

        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM), query_text="PurchaseOrder", k=5
        )

        assert isinstance(results, list)
        assert results, "the seeded chunk must surface"
        # isinstance (not duck-typing) — a lookalike object could never satisfy
        # this, and Candidate's own extra="forbid" guarantees nothing else rode
        # along on it either.
        assert all(isinstance(candidate, Candidate) for candidate in results)

    async def test_candidates_are_keyed_by_bare_point_id_without_table_prefix(
        self, store: FakeSurrealStore
    ) -> None:
        record = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py",
            identity="PurchaseOrder.action_confirm",
        )
        await store.upsert([(record, unit_vector(0, PRODUCTION_DIM))])

        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM), query_text="PurchaseOrder", k=5
        )

        hit = next(candidate for candidate in results if candidate.key == record.point_id)
        assert hit.key == record.point_id
        assert "chunk:" not in hit.key  # no record-table prefix leaked onto the key

    async def test_candidates_origin_is_always_fused(self, store: FakeSurrealStore) -> None:
        record = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py",
            identity="PurchaseOrder.action_confirm",
        )
        await store.upsert([(record, unit_vector(0, PRODUCTION_DIM))])

        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM), query_text="PurchaseOrder", k=5
        )

        assert results
        assert all(candidate.origin == "fused" for candidate in results)

    async def test_candidates_carry_the_vector_cosine_substrate(
        self, store: FakeSurrealStore
    ) -> None:
        # S4b (docs/design/2026-07-06-weak-match-discrimination.md): the fake
        # must faithfully mirror the real store's new pre-fusion cosine
        # projection, not just the fused rrf score — it already computes
        # cosine internally for vector-arm ranking (``_cosine_similarity``),
        # so this is exposing an existing computation, not a new one.
        near = chunk_record(
            tier=TIER_A, file_path="pkg/near.py", identity="near_fn",
            ident_text="alpha beta",
        )
        far = chunk_record(
            tier=TIER_A, file_path="pkg/far.py", identity="far_fn",
            ident_text="gamma delta",
        )
        await store.upsert([
            (near, unit_vector(0, PRODUCTION_DIM)), (far, unit_vector(1, PRODUCTION_DIM)),
        ])

        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM), query_text="alpha beta", k=5
        )

        near_hit = next(c for c in results if c.key == near.point_id)
        far_hit = next(c for c in results if c.key == far.point_id)
        assert near_hit.vector_cosine == pytest.approx(1.0, abs=1e-9)
        assert far_hit.vector_cosine == pytest.approx(0.0, abs=1e-9)

    async def test_candidate_scores_are_finite_non_negative_and_rrf_scale(
        self, store: FakeSurrealStore
    ) -> None:
        target = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py",
            identity="PurchaseOrder.action_confirm",
            ident_text="PurchaseOrder action_confirm",
        )
        pairs = [(target, unit_vector(0, PRODUCTION_DIM))]
        pairs += [_distractor(i, axis=i + 1) for i in range(2)]
        await store.upsert(pairs)

        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM),
            query_text="PurchaseOrder action_confirm",
            k=5,
        )

        assert results
        for candidate in results:
            assert math.isfinite(candidate.score)  # never NaN/inf
            assert candidate.score >= 0.0
            # See the module-level derivation: a cosine-scale fake (~1.0 for a
            # near-identical vector) is caught here, not just a NaN/negative one.
            assert candidate.score < _RRF_SCORE_CEILING


class TestHonestEmptiness:
    """A HEALTHY store with nothing to return answers ``[]`` — never an
    exception. Distinct from ``TestFailureInjection`` (a DOWN connection,
    which must raise). Pins contract item 3.
    """

    async def test_empty_corpus_returns_empty_list(self, store: FakeSurrealStore) -> None:
        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM), query_text="anything", k=5
        )
        assert results == []

    async def test_filter_matching_nothing_is_honest_empty(
        self, store: FakeSurrealStore
    ) -> None:
        await store.upsert(
            [
                (
                    chunk_record(tier=TIER_A, file_path="a.py", identity="A"),
                    unit_vector(0, PRODUCTION_DIM),
                )
            ]
        )

        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM),
            query_text="A",
            k=5,
            filters={"tier": "nonexistent_tier"},
        )
        assert results == []


class TestVectorArm:
    """The vector arm alone must rank a genuinely nearest chunk first — proven
    with a query text sharing NO token with any stored chunk, so BM25
    contributes nothing. Pins contract item 4.
    """

    async def test_nearest_vector_ranks_first(self, store: FakeSurrealStore) -> None:
        target_axis = 5
        target = chunk_record(
            tier=TIER_A, file_path="models/account_move.py",
            identity="AccountMove.reconcile", ident_text="AccountMove reconcile",
            source_text="def reconcile(self):\n    return self.env['account.move.line']\n",
        )
        pairs = [(target, unit_vector(target_axis, PRODUCTION_DIM))]
        # 5 distractors on axes 0..4 — every one ORTHOGONAL (cosine 0) to the
        # target's axis-5 query, so only the target is a genuine vector match.
        pairs += [_distractor(i, axis=i) for i in range(5)]
        await store.upsert(pairs)

        results = await store.hybrid_search(
            query_vector=unit_vector(target_axis, PRODUCTION_DIM),
            query_text="zzqx nonexistent lexeme",  # shares no token with any chunk
            k=6,
        )

        assert results, "the nearest chunk must surface"
        assert results[0].key == target.point_id


class TestFulltextRescue:
    """The BM25 arm must rescue a chunk whose VECTOR is the worst possible
    match, when its indexed text matches the query — the load-bearing hybrid
    behaviour (mirrors the real store's own
    ``test_exact_identifier_query_rescues_a_mediocre_vector``, applied to the
    fake). Pins contract item 5.
    """

    async def test_identifier_query_rescues_a_mediocre_vector(
        self, store: FakeSurrealStore
    ) -> None:
        query_axis = 0
        target = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py",
            identity="PurchaseOrder.action_confirm",
            ident_text="PurchaseOrder action_confirm",
        )
        # Target's vector is ORTHOGONAL to the query (worst possible); every
        # distractor sits EXACTLY on the query vector (best possible). Only a
        # working BM25 rescue can surface the target here.
        pairs = [(target, unit_vector(9, PRODUCTION_DIM))]
        pairs += [_distractor(i, axis=query_axis) for i in range(8)]
        await store.upsert(pairs)

        results = await store.hybrid_search(
            query_vector=unit_vector(query_axis, PRODUCTION_DIM),
            query_text="PurchaseOrder action_confirm",
            k=5,
        )

        assert target.point_id in {candidate.key for candidate in results}


class TestFilterScoping:
    """Filters scope BOTH arms with FULL-``k`` recall inside the scope — never
    "take the global top-k, then filter" (which would under-return here, since
    tier A and tier B chunks are interleaved 50/50 by insertion). Pins
    contract item 6.
    """

    async def test_filter_scopes_both_arms_with_full_k_recall(
        self, store: FakeSurrealStore
    ) -> None:
        axis = 2
        pairs: list[tuple[Record, list[float]]] = []
        for i in range(6):
            pairs.append(
                (
                    chunk_record(
                        tier=TIER_A, file_path=f"models/scope_a_{i}.py",
                        identity=f"ScopeFactory.build_a_{i}",
                        ident_text="ScopeFactory build_widget",
                    ),
                    unit_vector(axis, PRODUCTION_DIM),
                )
            )
            pairs.append(
                (
                    chunk_record(
                        tier=TIER_B, file_path=f"models/scope_b_{i}.py",
                        identity=f"ScopeFactory.build_b_{i}",
                        ident_text="ScopeFactory build_widget",
                    ),
                    unit_vector(axis, PRODUCTION_DIM),
                )
            )
        await store.upsert(pairs)  # interleaved A,B,A,B,... insertion order

        results = await store.hybrid_search(
            query_vector=unit_vector(axis, PRODUCTION_DIM),
            query_text="ScopeFactory build_widget",
            k=6,
            filters={"tier": TIER_A},
        )

        assert len(results) == 6  # full-k recall, not under-returned by ~half
        assert all(candidate.payload["tier"] == TIER_A for candidate in results)


class TestFilterKeyInjectionOnFake:
    """Filter KEYS are validated at the fake's own trust boundary, the SAME
    allow-list class of defense the real store enforces at
    ``TestFilterKeyInjection`` — so a test written against the fake never
    certifies a permissiveness ``search_code``/``get_symbol`` (P6) would
    reject for real. Pins contract item 7.
    """

    async def test_legitimate_filter_keys_are_accepted_at_both_seams(
        self, store: FakeSurrealStore
    ) -> None:
        await store.upsert(
            [
                (
                    chunk_record(
                        tier=TIER_A, file_path="models/purchase_order.py",
                        identity="PurchaseOrder.action_confirm",
                    ),
                    unit_vector(0, PRODUCTION_DIM),
                )
            ]
        )
        for key in CHUNK_FILTER_KEYS:
            value = _ALLOWED_KEY_VALUES[key]
            rows = await store.scroll(filters={key: value}, limit=10)
            assert isinstance(rows, list)  # accepted at the boundary, never raises
            results = await store.hybrid_search(
                query_vector=unit_vector(0, PRODUCTION_DIM),
                query_text="PurchaseOrder",
                k=5,
                filters={key: value},
            )
            assert isinstance(results, list)

    @pytest.mark.parametrize("hostile_key", _HOSTILE_FILTER_KEYS)
    async def test_hostile_filter_key_raises_at_scroll(
        self, store: FakeSurrealStore, hostile_key: str
    ) -> None:
        await store.upsert(
            [(chunk_record(tier=TIER_A, file_path="a.py", identity="A"), unit_vector(0, PRODUCTION_DIM))]
        )
        with pytest.raises(SurrealStoreError):
            await store.scroll(filters={hostile_key: "x"}, limit=10)
        assert await store.count() == 1  # the illegal probe never mutated the corpus

    @pytest.mark.parametrize("hostile_key", _HOSTILE_FILTER_KEYS)
    async def test_hostile_filter_key_raises_at_hybrid_search(
        self, store: FakeSurrealStore, hostile_key: str
    ) -> None:
        await store.upsert(
            [(chunk_record(tier=TIER_A, file_path="a.py", identity="A"), unit_vector(0, PRODUCTION_DIM))]
        )
        with pytest.raises(SurrealStoreError):
            await store.hybrid_search(
                query_vector=unit_vector(0, PRODUCTION_DIM),
                query_text="A",
                k=5,
                filters={hostile_key: "x"},
            )
        assert await store.count() == 1


class TestKLimits:
    """``k`` binds the fused result count, including when it exceeds corpus
    size. Pins contract item 8.
    """

    async def test_k_limits_result_count(self, store: FakeSurrealStore) -> None:
        pairs = [_distractor(i, axis=0) for i in range(8)]
        await store.upsert(pairs)

        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM), query_text="build_gizmo", k=3
        )
        # 8 equally-matching candidates, k=3: must bind EXACTLY, not just "<=".
        assert len(results) == 3

    async def test_k_larger_than_corpus_returns_all_without_error(
        self, store: FakeSurrealStore
    ) -> None:
        pairs = [_distractor(i, axis=0) for i in range(4)]
        await store.upsert(pairs)

        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM), query_text="build_gizmo", k=100
        )
        assert len(results) == 4


class TestAdversarialOrderingHybridSearch:
    """The P5 project-memory lesson, applied here: a fake that just walks its
    backing dict in INSERTION order would hide a caller bug that assumes
    ordering trustworthy fusion never promised. This class proves the fake's
    tie-break for EQUAL-relevance candidates is NOT insertion order, while
    still being deterministic call-to-call (mirrors the real store's own
    documented ``test_rrf_ordering_is_deterministic`` contract). Pins contract
    item 9.
    """

    async def test_equal_relevance_candidates_are_not_returned_in_insertion_order(
        self, store: FakeSurrealStore
    ) -> None:
        axis = 3
        pairs = [_duplicate_hit(str(i), axis=axis) for i in range(5)]
        # Insert in DESCENDING point-id order — a deliberate, KNOWN permutation
        # distinct from the construction order — so "result order != insertion
        # order" is a real, non-coincidental check regardless of whether the
        # fake's own tie-break sorts ascending, descending, or by some other
        # deterministic key (the implementer's choice; only insertion order
        # itself is disallowed).
        pairs.sort(key=lambda pair: pair[0].point_id, reverse=True)
        await store.upsert(pairs)
        insertion_order = [record.point_id for record, _vector in pairs]

        first = await store.hybrid_search(
            query_vector=unit_vector(axis, PRODUCTION_DIM),
            query_text="PurchaseOrder action_confirm",
            k=5,
        )
        second = await store.hybrid_search(
            query_vector=unit_vector(axis, PRODUCTION_DIM),
            query_text="PurchaseOrder action_confirm",
            k=5,
        )
        first_order = [candidate.key for candidate in first]
        second_order = [candidate.key for candidate in second]

        assert len(first_order) == 5
        assert first_order == second_order  # deterministic call-to-call
        assert first_order != insertion_order  # NOT a naive dict.values() walk


class TestFailureInjection:
    """The seam future pipeline tests need to pin "a down connection RAISES,
    never a silent empty result" (the real store's ``TestResilience``
    contract). The fake has no real socket to kill, so this class DEFINES a
    fresh control surface for it:

    ``FakeSurrealStore.arm_connection_failure(times=1)`` makes the NEXT
    ``times`` calls to EITHER ``hybrid_search`` or ``scroll`` — a single
    SHARED trip counter, mirroring a genuinely down connection where it does
    not matter which read method asks — raise ``SurrealConnectionError``. The
    counter then auto-disarms and subsequent calls behave normally again
    (degradation -> recovery, never permanently wedged). Pins contract item
    10.
    """

    async def test_armed_fake_raises_on_hybrid_search_then_recovers(
        self, store: FakeSurrealStore
    ) -> None:
        store.arm_connection_failure()

        with pytest.raises(SurrealConnectionError):
            await store.hybrid_search(
                query_vector=unit_vector(0, PRODUCTION_DIM), query_text="anything", k=5
            )

        # Recovery: the very next call is healthy again (honest empty corpus).
        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM), query_text="anything", k=5
        )
        assert results == []

    async def test_armed_fake_raises_on_scroll_then_recovers(
        self, store: FakeSurrealStore
    ) -> None:
        store.arm_connection_failure()

        with pytest.raises(SurrealConnectionError):
            await store.scroll(filters={}, limit=10)

        rows = await store.scroll(filters={}, limit=10)
        assert rows == []

    async def test_arm_counter_is_shared_across_both_methods_and_disarms_after_count(
        self, store: FakeSurrealStore
    ) -> None:
        store.arm_connection_failure(times=2)

        with pytest.raises(SurrealConnectionError):
            await store.scroll(filters={}, limit=10)  # trip 1
        with pytest.raises(SurrealConnectionError):
            await store.hybrid_search(
                query_vector=unit_vector(0, PRODUCTION_DIM), query_text="x", k=5
            )  # trip 2, across the OTHER method — proves the shared counter

        # Exhausted: the third call, on either method, is healthy again.
        assert await store.scroll(filters={}, limit=10) == []


class TestScrollContract:
    """``scroll`` behavioural parity: honours its required ``limit``, is
    honest-empty on no match, returns ``list[dict]`` payload rows, accepts the
    EXACT call shape ``symbols.py`` uses, and — the ``symbols.py``:193
    documented hazard — resolves same-filter ties in a non-insertion order, so
    a caller that (bug-prone) reads ``points[0]`` is exercised realistically.
    Pins contract item 11.
    """

    async def test_scroll_returns_list_of_dict_payload_rows(
        self, store: FakeSurrealStore
    ) -> None:
        record = chunk_record(
            tier=TIER_A, file_path="models/purchase_order.py",
            identity="PurchaseOrder.action_confirm",
        )
        await store.upsert([(record, unit_vector(0, PRODUCTION_DIM))])

        rows = await store.scroll(
            filters={"tier": TIER_A, "file_path": "models/purchase_order.py"}, limit=10
        )

        assert isinstance(rows, list)
        assert len(rows) == 1
        assert isinstance(rows[0], dict)
        assert rows[0]["identity"] == "PurchaseOrder.action_confirm"
        # The verbatim body must survive the round-trip (a citation renders it).
        assert rows[0]["source_text"] == record.payload["source_text"]

    async def test_scroll_honors_its_limit(self, store: FakeSurrealStore) -> None:
        pairs = [
            (
                chunk_record(tier=TIER_A, file_path=f"models/f{i}.py", identity="Shared.symbol"),
                unit_vector(0, PRODUCTION_DIM),
            )
            for i in range(12)
        ]
        await store.upsert(pairs)

        rows = await store.scroll(filters={"identity": "Shared.symbol"}, limit=5)
        assert len(rows) == 5  # capped, not the full 12

    async def test_scroll_no_match_is_honest_empty(self, store: FakeSurrealStore) -> None:
        await store.upsert(
            [(chunk_record(tier=TIER_A, file_path="a.py", identity="A"), unit_vector(0, PRODUCTION_DIM))]
        )
        rows = await store.scroll(filters={"file_path": "does/not/exist.py"}, limit=10)
        assert rows == []

    async def test_scroll_signature_matches_symbols_caller(
        self, store: FakeSurrealStore
    ) -> None:
        # The live caller (symbols.py::_find_by_identity) calls
        # scroll(filters=…, limit=_SCROLL_LIMIT). That EXACT call shape must
        # work and be capped, or the FakeSurrealTrio wiring TypeErrors the
        # moment symbols.py is rewired onto it (P6). Seed more than
        # _SCROLL_LIMIT collision siblings.
        pairs = [
            (
                chunk_record(
                    tier=TIER_A, file_path=f"models/g{i}.py", identity="Collide.name",
                    chunk_type="python_symbol",
                ),
                unit_vector(0, PRODUCTION_DIM),
            )
            for i in range(_SCROLL_LIMIT + 4)
        ]
        await store.upsert(pairs)

        rows = await store.scroll(
            filters={"identity": "Collide.name", "chunk_type": "python_symbol"},
            limit=_SCROLL_LIMIT,
        )
        assert len(rows) == _SCROLL_LIMIT

    async def test_scroll_equal_matches_are_not_returned_in_insertion_order(
        self, store: FakeSurrealStore
    ) -> None:
        # symbols.py:193 documents the real hazard this guards against:
        # `_find_by_identity` takes `points[0]` on a same-identity collision
        # (e.g. `EmbeddingConfig` defined in two packages), so "which sibling
        # wins" is scroll-order-dependent. A fake with a hidden insertion-order
        # bias would make that documented hazard invisible to any test built
        # on top of it.
        pairs = [
            (
                chunk_record(
                    tier=TIER_A, file_path=f"models/collide_{i}.py",
                    identity="EmbeddingConfig", chunk_type="python_symbol",
                ),
                unit_vector(0, PRODUCTION_DIM),
            )
            for i in range(5)
        ]
        pairs.sort(key=lambda pair: pair[0].point_id, reverse=True)
        await store.upsert(pairs)
        insertion_file_paths = [record.payload["file_path"] for record, _vector in pairs]

        first = await store.scroll(
            filters={"identity": "EmbeddingConfig", "chunk_type": "python_symbol"}, limit=10
        )
        second = await store.scroll(
            filters={"identity": "EmbeddingConfig", "chunk_type": "python_symbol"}, limit=10
        )
        # Rows carry no point-id field of their own; file_path (unique per
        # sibling here) stands in as the row's identity for order comparison.
        first_order = [row["file_path"] for row in first]
        second_order = [row["file_path"] for row in second]

        assert len(first_order) == 5
        assert first_order == second_order  # deterministic call-to-call
        assert first_order != insertion_file_paths  # NOT a naive insertion walk


class TestNoVectorLeakage:
    """Neither a ``hybrid_search`` ``Candidate.payload`` nor a ``scroll`` row
    may carry the raw stored vector, or the fake's own internal
    ``"__point_id"`` bookkeeping key — both would be a leaked
    backend/implementation detail riding along on a caller-facing result
    (exactly the class of leak ``Candidate``'s ``extra="forbid"`` polices for
    its OWN top-level fields; ``payload``/a scroll row is an untyped dict, so
    the leak must be checked explicitly). Pins contract item 12.
    """

    async def test_hybrid_search_candidate_never_carries_the_vector_or_bookkeeping_key(
        self, store: FakeSurrealStore
    ) -> None:
        stored_vector = unit_vector(4, PRODUCTION_DIM)
        record = chunk_record(tier=TIER_A, file_path="models/leak.py", identity="Leak.probe")
        await store.upsert([(record, stored_vector)])

        results = await store.hybrid_search(
            query_vector=stored_vector, query_text="Leak probe", k=5
        )
        hit = next(candidate for candidate in results if candidate.key == record.point_id)

        assert "embedding" not in hit.payload
        assert "vector" not in hit.payload
        assert "__point_id" not in hit.payload
        assert stored_vector not in hit.payload.values()

    async def test_scroll_row_never_carries_the_vector_or_bookkeeping_key(
        self, store: FakeSurrealStore
    ) -> None:
        stored_vector = unit_vector(4, PRODUCTION_DIM)
        record = chunk_record(tier=TIER_A, file_path="models/leak.py", identity="Leak.probe")
        await store.upsert([(record, stored_vector)])

        rows = await store.scroll(filters={"file_path": "models/leak.py"}, limit=10)
        assert len(rows) == 1
        row = rows[0]

        assert "embedding" not in row
        assert "vector" not in row
        assert "__point_id" not in row
        assert stored_vector not in row.values()


class TestCanonicalPayloadShape:
    """Invariant 13 (cycle-1 audit addendum): the fake serves the CANONICAL
    flattened payload shape the real store's read path produces.

    The real ``SurrealStore`` runs ``_normalize_row`` on every scroll row and
    every hybrid-search payload: the ``metadata`` column's contents are
    promoted TOP-LEVEL and the ``"metadata"`` wrapper key itself never
    survives to a caller (pinned canonically by test_surreal_store.py's
    ``TestMetadataShapeReconciliation`` — ``assert "metadata" not in
    rows[0]``); on an (adversarial-only) name collision the declared column's
    own value wins. A fake serving the NESTED shape instead would let a P6
    pipeline read ``payload["metadata"][...]`` and ship green while
    production KeyErrors — the exact faithful-to-the-happy-path failure mode
    this contract exists to prevent.
    """

    async def test_hybrid_search_payload_flattens_metadata_top_level(
        self, store: FakeSurrealStore
    ) -> None:
        record = chunk_record(
            tier=TIER_A,
            file_path="models/meta_shape.py",
            identity="MetaShape.symbol",
            ident_text="MetaShape symbol",
            metadata={"language": "python", "signature": "def confirm(self, order)"},
        )
        await store.upsert([(record, unit_vector(0, PRODUCTION_DIM))])

        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM),
            query_text="MetaShape symbol",
            k=5,
        )

        assert results
        payload = results[0].payload
        assert "metadata" not in payload, (
            "the metadata WRAPPER must never survive to a caller — the real "
            "store's _normalize_row drops it (TestMetadataShapeReconciliation)"
        )
        # The wrapper's CONTENTS are promoted top-level…
        assert payload["language"] == "python"
        assert payload["signature"] == "def confirm(self, order)"
        # …and the declared columns are still intact alongside them.
        assert payload["tier"] == TIER_A
        assert payload["file_path"] == "models/meta_shape.py"

    async def test_scroll_row_flattens_metadata_top_level(
        self, store: FakeSurrealStore
    ) -> None:
        populated = chunk_record(
            tier=TIER_A,
            file_path="models/meta_scroll.py",
            identity="MetaScroll.symbol",
            metadata={"language": "python"},
        )
        # ``chunk_record`` injects ``"metadata": {}`` BY DEFAULT — so the
        # empty-wrapper case rides every corpus; pin that it too is dropped.
        empty_default = chunk_record(
            tier=TIER_A,
            file_path="models/meta_scroll_empty.py",
            identity="MetaScrollEmpty.symbol",
        )
        await store.upsert(
            [
                (populated, unit_vector(0, PRODUCTION_DIM)),
                (empty_default, unit_vector(1, PRODUCTION_DIM)),
            ]
        )

        rows = await store.scroll(filters={"tier": TIER_A}, limit=10)

        assert len(rows) == 2
        by_path = {row["file_path"]: row for row in rows}
        populated_row = by_path["models/meta_scroll.py"]
        empty_row = by_path["models/meta_scroll_empty.py"]
        assert "metadata" not in populated_row
        assert populated_row["language"] == "python"
        assert "metadata" not in empty_row, (
            "an EMPTY metadata wrapper is dropped too — the real "
            "_normalize_row never lets the key survive"
        )

    async def test_metadata_collision_declared_column_wins(
        self, store: FakeSurrealStore
    ) -> None:
        # Adversarial-only input: a metadata key shadowing a declared column.
        # The real _normalize_row applies the declared columns LAST, so the
        # column's genuine value wins over the same-named metadata key.
        record = chunk_record(
            tier=TIER_A,
            file_path="models/meta_clash.py",
            identity="MetaClash.symbol",
            ident_text="MetaClash symbol",
            metadata={"tier": "EVIL-SHADOW-TIER", "extra_key": "kept"},
        )
        await store.upsert([(record, unit_vector(0, PRODUCTION_DIM))])

        results = await store.hybrid_search(
            query_vector=unit_vector(0, PRODUCTION_DIM),
            query_text="MetaClash symbol",
            k=5,
        )

        assert results
        payload = results[0].payload
        assert payload["tier"] == TIER_A, (
            "on a name collision the DECLARED column's value wins — a fake "
            "letting metadata shadow a column would corrupt tier/path scoping"
        )
        assert payload["extra_key"] == "kept"
        assert "metadata" not in payload


class TestRecordTraceFake:
    """The fake's P8a ``record_trace`` observability write path — signature parity
    with the real store, the injected down-connection append-failure (via the
    SHARED ``arm_connection_failure`` trip counter — the real store's transport can
    fail ANY write), and the adversarial NON-insertion read-back order (the P5
    positional-consumption lesson applied to traces: the real engine returns rows
    unordered without an ``ORDER BY``, so a consumer assuming insertion order is a
    latent bug the fake must expose, not hide).
    """

    def test_record_trace_signature_matches_real_store(self) -> None:
        # AMENDED for packet 03b's all-tools trace telemetry — authorized fork
        # FK-3 (03b-design-rulings-r2.md T8 + DIFF-adjudication-03b.md AC-16;
        # operator grant in 03b-comms-message-surface.md §OPERATOR GRANT (second),
        # commit 1e3a249). STRENGTHEN-ONLY: the committed seven names are still
        # asserted, in the same order and still keyword-only with matching
        # defaults; four telemetry parameters are APPENDED.
        #
        # ``agent`` / ``action`` / ``transport_session`` / ``ok`` are the seam's
        # declared-identity, verb, transport-correlator and outcome columns. They
        # go at the END so the committed prefix stays readable as one unit; every
        # parameter is keyword-only, so position carries no caller meaning.
        #
        # ``ordinal`` is deliberately ABSENT: the ordinal is minted SERVER-SIDE
        # inside the trace write from the ``trace_seq`` native sequence (T3), so a
        # build that accepts it as a parameter — i.e. mints it client-side, which
        # races under concurrency — goes RED right here.
        #
        # MUTATION-PROOF OBLIGATION (adversary): add an ``ordinal`` parameter to
        # the real ``record_trace`` and watch this pin go RED; drop any one of the
        # four new names from the FAKE and watch it go RED on the parity leg.
        #
        # ⚠ THIS PIN ASSERTS PARAMETER ORDER, and that IS deliberate (adversary
        # residual R2, which correctly calls it over-specification on the
        # semantics: every parameter is keyword-only, so order carries no meaning
        # for any caller, and a natural "required-before-defaulted" signature is
        # RED here for a cosmetic reason). It stays because the pin's subject is
        # EXACT-SHAPE PARITY between two implementations of one signature: a
        # `list(fake) == list(real)` comparison is what makes a divergence
        # impossible to miss, and comparing sets would let the two drift into
        # different orders and then into different NAMES via a rename on one side.
        # A builder who hits this: reorder to match, or raise it — do not weaken it
        # to a set comparison.
        real_params = _params_excluding_self(SurrealStore.record_trace)
        fake_params = _params_excluding_self(FakeSurrealStore.record_trace)
        assert list(fake_params) == list(real_params) == [
            "tool",
            "params_hash",
            "hit_count",
            "latency_ms",
            "session",
            "token_cost",
            "model",
            "agent",
            "action",
            "transport_session",
            "ok",
        ]
        for name, real_param in real_params.items():
            fake_param = fake_params[name]
            # KEYWORD_ONLY on both sides — a caller may never pass these
            # positionally, on the fake any more than on the real store.
            assert fake_param.kind == real_param.kind == inspect.Parameter.KEYWORD_ONLY, name
            assert fake_param.default == real_param.default, name
        assert inspect.iscoroutinefunction(FakeSurrealStore.record_trace)

    async def test_record_trace_persists_and_reads_back_core_fields(
        self, store: FakeSurrealStore
    ) -> None:
        await store.record_trace(
            tool="lore_impact", params_hash="digest-a", hit_count=3,
            latency_ms=1.5, session="orchestrator-session-7f3a",
        )
        rows = store.recorded_traces()
        assert len(rows) == 1
        row = rows[0]
        assert row["tool"] == "lore_impact"
        assert row["params_hash"] == "digest-a"
        assert row["hit_count"] == 3
        assert row["latency_ms"] == 1.5  # fractional preserved (mirrors ``number``)
        assert row["session"] == "orchestrator-session-7f3a"
        # ts is stamped (the fake's analogue of the schema's server-side default).
        assert isinstance(row["ts"], datetime)
        assert row["ts"].tzinfo is not None

    # ----------------------------------------------------------------------- #
    # The telemetry enrichment columns — packet 03b (MP-F, adversary-directed;
    # the ORACLE change itself is the ESC-5 grant, T7.8/T8).
    #
    # WHY THESE EXIST: the signature-parity pin above proves the fake ACCEPTS the
    # four new parameters, and nothing proved it STORES them. Measured by the
    # adversary: dropping all four from the fake's row AND freezing its ordinal at
    # 0 left `test_surreal_fakes.py` + `test_mcp_server.py` +
    # `test_trace_telemetry.py` at 783 passed — the oracle could silently stop
    # mirroring the real row shape, and every fake-backed consumer would be
    # grading against a row the real store does not write. An oracle whose new
    # behaviour cannot FAIL is not an oracle.
    # ----------------------------------------------------------------------- #

    async def test_record_trace_stores_the_four_enrichment_columns_when_given(
        self, store: FakeSurrealStore
    ) -> None:
        await store.record_trace(
            tool="lore_comms", params_hash="digest-enriched", latency_ms=2.5,
            agent="auditor-q", action="drain",
            transport_session="3f9c1d7a55b04e0f9d2c8e6b71a04c15", ok=True,
        )
        row = store.recorded_traces()[0]
        assert row["agent"] == "auditor-q"
        assert row["action"] == "drain", (
            "without `action`, a drain row is indistinguishable from a heartbeat inside "
            "lore_comms's tool count — the numerator collapses into the denominator"
        )
        assert row["transport_session"] == "3f9c1d7a55b04e0f9d2c8e6b71a04c15"
        assert row["ok"] is True

    async def test_record_trace_omits_the_enrichment_columns_when_not_given(
        self, store: FakeSurrealStore
    ) -> None:
        # The real columns are ``option<>``: an unset one reads NONE, never a
        # fabricated "" / 0 / False. A fake that stored defaults would teach every
        # consumer that absence is representable as a value.
        await store.record_trace(tool="lore_search", params_hash="digest-bare", latency_ms=1.0)
        row = store.recorded_traces()[0]
        for column in ("agent", "action", "transport_session", "ok", "hit_count", "session"):
            assert row.get(column) is None, (
                f"the fake fabricated {column}={row.get(column)!r} for a call that declared "
                f"nothing; the real column stores NONE and an omitted key reads None"
            )

    async def test_record_trace_mints_distinct_increasing_zero_based_ordinals(
        self, store: FakeSurrealStore
    ) -> None:
        # Mirrors the real store's server-side mint from ``trace_seq``, which is
        # 0-BASED (``sequence::nextval`` under the default ``START 0``, probed on
        # 3.2.1) — a fake minting from 1, or freezing at a constant, would teach a
        # consumer numbering the engine never produces.
        for index in range(3):
            await store.record_trace(
                tool="lore_search", params_hash=f"digest-{index}", latency_ms=1.0
            )
        ordinals = sorted(int(row["ordinal"]) for row in store.recorded_traces())
        assert ordinals == [0, 1, 2], (
            f"the fake minted {ordinals!r}; the mint must be distinct, increasing and 0-based to "
            f"mirror the engine's sequence. A frozen ordinal makes every ordering consumer green "
            f"against a row the real store would never write."
        )

    async def test_record_trace_omitted_optionals_read_back_none(
        self, store: FakeSurrealStore
    ) -> None:
        await store.record_trace(
            tool="lore_map", params_hash="digest-b", hit_count=0,
            latency_ms=0.0, session="s",
        )
        row = store.recorded_traces()[0]
        # Mirrors the real ``option`` column: an omitted accounting column is
        # absent, so ``.get(...)`` is ``None`` — never a leaked placeholder.
        assert row.get("token_cost") is None
        assert row.get("model") is None
        assert store.recorded_traces()[0]  # sanity: a row exists to read

    async def test_record_trace_stores_optional_columns_when_given(
        self, store: FakeSurrealStore
    ) -> None:
        await store.record_trace(
            tool="lore_search", params_hash="digest-c", hit_count=5,
            latency_ms=9.0, session="s", token_cost=1536, model="voyage-4-large",
        )
        row = store.recorded_traces()[0]
        assert row["token_cost"] == 1536
        assert row["model"] == "voyage-4-large"

    async def test_armed_fake_raises_on_record_trace_then_recovers(
        self, store: FakeSurrealStore
    ) -> None:
        store.arm_connection_failure()

        with pytest.raises(SurrealConnectionError):
            await store.record_trace(
                tool="t", params_hash="h", hit_count=1, latency_ms=1.0, session="s"
            )
        # The armed trip persisted NOTHING (it raised before the append) — a down
        # connection is never a silent success.
        assert store.recorded_traces() == []

        # Recovery: the very next call is healthy again and lands its row.
        await store.record_trace(
            tool="t", params_hash="h", hit_count=1, latency_ms=1.0, session="s"
        )
        assert len(store.recorded_traces()) == 1

    async def test_record_trace_shares_the_arm_counter_with_the_read_methods(
        self, store: FakeSurrealStore
    ) -> None:
        # The SAME shared trip counter the read methods consume — a genuinely down
        # connection does not care which operation asks next.
        store.arm_connection_failure(times=2)
        with pytest.raises(SurrealConnectionError):
            await store.scroll(filters={}, limit=10)  # trip 1 (a read)
        with pytest.raises(SurrealConnectionError):
            await store.record_trace(
                tool="t", params_hash="h", hit_count=1, latency_ms=1.0, session="s"
            )  # trip 2 (the write) — proves the shared counter
        # Exhausted: the third call, a write, is healthy again.
        await store.record_trace(
            tool="t", params_hash="h", hit_count=1, latency_ms=1.0, session="s"
        )
        assert len(store.recorded_traces()) == 1

    async def test_recorded_traces_are_not_returned_in_insertion_order(
        self, store: FakeSurrealStore
    ) -> None:
        # Adversarial ordering: distinguish each row by a per-insert params_hash,
        # then prove the read-back is deterministic but NOT insertion order — a
        # fake that walked its backing list in insertion order would hide a
        # consumer bug the real (unordered) engine would eventually expose.
        insertion_hashes = [f"digest-{index}" for index in range(4)]
        for params_hash in insertion_hashes:
            await store.record_trace(
                tool="t", params_hash=params_hash, hit_count=1, latency_ms=1.0, session="s"
            )
        first = [row["params_hash"] for row in store.recorded_traces()]
        second = [row["params_hash"] for row in store.recorded_traces()]

        assert first == second  # deterministic call-to-call
        assert set(first) == set(insertion_hashes)  # no row lost or duplicated
        assert first != insertion_hashes  # NOT a naive insertion-order walk


class TestFileTextReadFake:
    """The fake's P8b ``file_text`` keyed-read surface — signature parity with the
    real store, keyed read-back of the stored body+digest, honest ``None`` on a
    missing pair, a COPY (never a live reference a caller could scribble on to
    corrupt the fake's stored state — the adversarial-double doctrine), and the
    injected down-connection failure via the SHARED ``arm_connection_failure``
    trip counter (the real store's transport can fail ANY read, so the fake can
    never be more forgiving on a downed connection than the real store).
    """

    _TIER = TIER_A
    _PATH = "models/purchase_order.py"
    _SOURCE = "def action_confirm(self):\n    return True\n"

    async def _seed(self, store: FakeSurrealStore) -> str:
        """Write the body through the SHARED write API and return its digest."""
        sha = sha512_hex(self._SOURCE)
        await store.apply(
            [store.file_text_fragment(self._TIER, self._PATH, self._SOURCE, sha)]
        )
        return sha

    def test_file_text_signature_matches_real_store(self) -> None:
        real_params = _params_excluding_self(SurrealStore.file_text)
        fake_params = _params_excluding_self(FakeSurrealStore.file_text)
        assert list(fake_params) == list(real_params) == ["tier", "file_path"]
        for name, real_param in real_params.items():
            fake_param = fake_params[name]
            assert fake_param.kind == real_param.kind, name
            assert fake_param.default == real_param.default, name
        assert inspect.iscoroutinefunction(FakeSurrealStore.file_text)

    async def test_reads_back_stored_body_and_digest(self, store: FakeSurrealStore) -> None:
        sha = await self._seed(store)
        row = await store.file_text(self._TIER, self._PATH)
        assert row is not None
        assert row["text"] == self._SOURCE
        assert row["sha512"] == sha

    async def test_absent_pair_returns_none(self, store: FakeSurrealStore) -> None:
        assert await store.file_text(self._TIER, "models/missing.py") is None

    async def test_returned_row_is_a_copy_not_a_live_reference(
        self, store: FakeSurrealStore
    ) -> None:
        await self._seed(store)
        row = await store.file_text(self._TIER, self._PATH)
        assert row is not None
        row["text"] = "MUTATED-BY-CALLER"  # a caller scribbling on the result
        again = await store.file_text(self._TIER, self._PATH)
        assert again is not None
        assert again["text"] == self._SOURCE  # the fake's stored state is untouched

    async def test_armed_fake_raises_on_file_text_then_recovers(
        self, store: FakeSurrealStore
    ) -> None:
        await self._seed(store)
        store.arm_connection_failure()
        with pytest.raises(SurrealConnectionError):
            await store.file_text(self._TIER, self._PATH)
        # Recovery: the very next call is healthy again (a down read is never a
        # silent empty — it raised BEFORE the lookup).
        row = await store.file_text(self._TIER, self._PATH)
        assert row is not None
        assert row["text"] == self._SOURCE

    async def test_file_text_shares_the_arm_counter_with_the_read_methods(
        self, store: FakeSurrealStore
    ) -> None:
        # The SAME shared trip counter the other read methods consume — a
        # genuinely down connection does not care which read asks next.
        store.arm_connection_failure(times=2)
        with pytest.raises(SurrealConnectionError):
            await store.scroll(filters={}, limit=10)  # trip 1 (a read)
        with pytest.raises(SurrealConnectionError):
            await store.file_text(self._TIER, self._PATH)  # trip 2 — proves shared counter
        # Exhausted: the third call is healthy again (honest None on a missing pair).
        assert await store.file_text(self._TIER, self._PATH) is None


# --------------------------------------------------------------------------- #
# lore_map's whole-graph read surface: ``all_nodes()`` — signature/shape
# parity between the real graph and the fake, plus the fake's OWN dedupe
# guarantee on a re-upserted file (the deferred all_nodes parity pin:
# ``MapEngine._extract_module_graph`` already depends on this method, but
# until now it was only exercised INDIRECTLY through test_map.py's PageRank
# assertions — never pinned at the signature/shape/dedupe level directly).
# --------------------------------------------------------------------------- #
_ALL_NODES_TIER = TIER_A
_ALL_NODES_FILE_PATH = "models/purchase_order_router.py"
_ALL_NODES_SOURCE = """\
def route_purchase_order(order_id):
    \"\"\"Route a purchase order to its approval chain.\"\"\"
    return order_id
"""


def _approx_token_count(text: str) -> int:
    """Behavioural stand-in for the embedder's injected token counter (~4 cpt)."""
    return max(1, len(text) // 4)


def _all_nodes_chunk(path: str, source: str) -> list[Any]:
    """Chunk ``source`` through the REAL ``PythonAstChunker`` (the prod producer).

    Mirrors ``test_graph_surreal.py``'s own ``_chunk`` helper: driving the real
    chunker (not hand-rolled ``Chunk`` objects) exercises the producer/consumer
    seam ``all_nodes`` sits behind (clause 3), so a chunker-shape drift cannot
    slip past this parity pin either.
    """
    ctx = ChunkContext(
        slug="all_nodes_parity",
        file_path=path,
        count_tokens=_approx_token_count,
        max_input_tokens=8192,
    )
    return PythonAstChunker().chunk(source, ctx)


class TestAllNodesParity:
    """``all_nodes()`` signature parity + decode shape + dedupe-on-reupsert.

    Only the FAKE's own guarantees are exercised directly here (this file's
    charter, per its own module docstring) — the REAL graph's identical
    idempotent-rebuild guarantee is already pinned in
    ``test_graph_surreal.py::TestDeterministicId::
    test_rebuild_is_idempotent_no_duplicate_nodes``. This class is the FAKE's
    OWN formal pin of the same invariant, plus the cross-fake/real signature
    check ``TestSignatureParity`` above already established for the store's
    read-path methods.
    """

    def test_all_nodes_signature_matches_real_graph(self) -> None:
        real_params = _params_excluding_self(SurrealCodeGraph.all_nodes)
        fake_params = _params_excluding_self(FakeSurrealCodeGraph.all_nodes)
        assert list(fake_params) == list(real_params) == []
        assert inspect.iscoroutinefunction(SurrealCodeGraph.all_nodes)
        assert inspect.iscoroutinefunction(FakeSurrealCodeGraph.all_nodes)

    async def test_all_nodes_returns_real_graph_node_instances_with_full_shape(
        self,
    ) -> None:
        trio = fake_surreal_trio(dim=PRODUCTION_DIM)
        chunks = _all_nodes_chunk(_ALL_NODES_FILE_PATH, _ALL_NODES_SOURCE)
        await trio.graph.build_file_graph(_ALL_NODES_TIER, _ALL_NODES_FILE_PATH, chunks)

        nodes = await trio.graph.all_nodes()

        assert nodes, "the seeded file must contribute at least one node"
        assert all(isinstance(node, GraphNode) for node in nodes)
        # Every real decode column the production consumer (MapEngine) reads
        # off a node must be present and correctly typed.
        for node in nodes:
            assert node.id
            assert node.kind in {KIND_MODULE, KIND_CLASS, KIND_FUNCTION, KIND_METHOD}
            assert node.qualified_name
            assert node.file_path == _ALL_NODES_FILE_PATH
            assert node.tier == _ALL_NODES_TIER

    async def test_all_nodes_empty_on_a_wiped_graph(self) -> None:
        trio = fake_surreal_trio(dim=PRODUCTION_DIM)
        assert await trio.graph.all_nodes() == []

    async def test_upserting_the_same_file_twice_never_duplicates_nodes(self) -> None:
        trio = fake_surreal_trio(dim=PRODUCTION_DIM)
        chunks = _all_nodes_chunk(_ALL_NODES_FILE_PATH, _ALL_NODES_SOURCE)

        await trio.graph.build_file_graph(_ALL_NODES_TIER, _ALL_NODES_FILE_PATH, chunks)
        first_ids = sorted(node.id for node in await trio.graph.all_nodes())

        await trio.graph.build_file_graph(_ALL_NODES_TIER, _ALL_NODES_FILE_PATH, chunks)
        second_ids = sorted(node.id for node in await trio.graph.all_nodes())

        assert first_ids, "sanity: the file must have actually produced nodes"
        assert first_ids == second_ids, (
            "re-upserting the SAME file must not change the node id set"
        )
        assert len(second_ids) == len(set(second_ids)), (
            "no duplicate node ids may appear after a re-upsert"
        )


# --------------------------------------------------------------------------- #
# Bare-name bridge cycle — FakeSurrealCodeGraph matching-semantics parity
# (deferred pins 2b/2c of the bridge-cycle contract). Item 2a (``all_nodes``
# signature/shape/dedupe parity) is ALREADY pinned above by
# ``TestAllNodesParity`` — not duplicated here.
#
# WHY a SECOND corpus builder (not the ``TestAllNodesParity`` one above): 2b/2c
# need a genuinely RESOLVED cross-file reference (an import + a call astroid
# can actually resolve to a full FQN dst), which requires real on-disk files
# under ``tier_roots``/``project_roots`` — the single-file, no-resolution
# fixture above has no dst to bridge to.
# --------------------------------------------------------------------------- #

import textwrap  # noqa: E402
from collections.abc import Iterator  # noqa: E402 - see module note above
from pathlib import Path  # noqa: E402

from loremaster.graph import ReferenceSummary  # noqa: E402
from lorescribe.astroid_parse import (  # noqa: E402
    clear_resolution_cache,
    reset_search_path_memo,
)

_BRIDGE_TIER = TIER_A

# The SAME champion_routing/reflib/consumer naming already established across
# this repo's P6-tail contracts (``test_impact.py``, ``test_search.py``) and
# reused verbatim in ``test_graph_surreal.py``'s own bare-name-bridge section
# — clause 5: one shared convention, never a hand-invented twin.
_BRIDGE_REFLIB_SOURCE = textwrap.dedent(
    '''\
    """demo.reflib -- defines champion_routing."""


    def champion_routing(week):
        """Route the champion warehouse."""
        return week * 2
    '''
)
_BRIDGE_CONSUMER_SOURCE = textwrap.dedent(
    '''\
    """A production caller of champion_routing."""
    from demo.reflib import champion_routing


    def dispatch(week):
        """A production caller."""
        return champion_routing(week)
    '''
)
_BRIDGE_REFLIB_PATH = "demo/reflib.py"
_BRIDGE_CONSUMER_PATH = "demo/consumer.py"
_BRIDGE_REFLIB_MODULE = "demo.reflib"
_BRIDGE_CONSUMER_MODULE = "demo.consumer"
_FQN_BRIDGE_CHAMPION_ROUTING = "demo.reflib.champion_routing"
_FQN_BRIDGE_DISPATCH = "demo.consumer.dispatch"


@pytest.fixture(autouse=True)
def _reset_astroid_resolution_state_for_bridge_tests() -> Iterator[None]:
    """Reset astroid's process-global resolution state around EVERY test in
    this file.

    Mirrors ``test_graph_surreal.py``'s/``test_impact.py``'s identical guard
    (clause 5 — the SAME convention, not reinvented): the bridge tests below
    build resolution-enabled packages reusing the SAME dotted module names
    (``demo.reflib`` / ``demo.consumer``) under a FRESH ``tmp_path`` per test;
    without the reset, an earlier test's residual astroid cache/search-path
    memo degrades a later test's cross-module resolution to a bare, unresolved
    reference regardless of test order. Harmless for this file's OTHER
    (non-resolution) fake-store tests — it only touches astroid's own global
    state.
    """
    clear_resolution_cache()
    reset_search_path_memo()
    yield
    clear_resolution_cache()
    reset_search_path_memo()


def _bridge_chunk(path: str, source: str) -> list[Any]:
    """Chunk ``source`` through the REAL ``PythonAstChunker`` (mirrors
    ``test_graph_surreal.py``'s own ``_chunk`` helper — the SAME production
    producer, so the fake's derivation input is byte-identical to the real
    build path's).
    """
    ctx = ChunkContext(
        slug="bridge",
        file_path=path,
        count_tokens=lambda text: max(1, len(text) // 4),
        max_input_tokens=8192,
    )
    return PythonAstChunker().chunk(source, ctx)


async def _build_bridge_reflib_graph(tmp_path: Path) -> FakeSurrealCodeGraph:
    """Materialise the reflib/consumer corpus on disk; build a fresh,
    resolution-enabled :class:`FakeSurrealCodeGraph` over BOTH files.
    """
    root = tmp_path / "project"
    (root / "demo").mkdir(parents=True)
    (root / "demo" / "__init__.py").write_text("", encoding="utf-8")
    (root / "demo" / "reflib.py").write_text(_BRIDGE_REFLIB_SOURCE, encoding="utf-8")
    (root / "demo" / "consumer.py").write_text(_BRIDGE_CONSUMER_SOURCE, encoding="utf-8")
    trio = fake_surreal_trio(
        dim=PRODUCTION_DIM, tier_roots={_BRIDGE_TIER: root}, project_roots=[root]
    )
    await trio.graph.build_file_graph(
        _BRIDGE_TIER,
        _BRIDGE_REFLIB_PATH,
        _bridge_chunk(_BRIDGE_REFLIB_PATH, _BRIDGE_REFLIB_SOURCE),
        module_name=_BRIDGE_REFLIB_MODULE,
    )
    await trio.graph.build_file_graph(
        _BRIDGE_TIER,
        _BRIDGE_CONSUMER_PATH,
        _bridge_chunk(_BRIDGE_CONSUMER_PATH, _BRIDGE_CONSUMER_SOURCE),
        module_name=_BRIDGE_CONSUMER_MODULE,
    )
    return trio.graph


class TestFakeMatchingDoesNotOverMatchOnWrongFqn:
    """``FakeSurrealCodeGraph._matches`` must not over-match relative to the
    REAL graph's LITERAL name-id equality (bridge-cycle contract item 2b).

    Live-verified against the REAL ``SurrealCodeGraph`` on the equivalent
    corpus (see ``test_graph_surreal.py``'s bare-name-bridge section):
    ``references("lib.champion_routing")`` — a WRONG FQN sharing ONLY
    champion_routing's bare LAST segment (a plausible typo/wrong-module-guess,
    not a contrived string) — returns an all-zero summary on the real graph,
    because real name-id equality never matches on a shared last segment
    alone. The fake's ``_matches`` instead computes ``bare_name(dst) ==
    bare_name(target)``, oblivious to the (wrong) leading module segment, so
    it WRONGLY reports 2 production references today — RED.
    """

    async def test_wrong_fqn_sharing_only_the_bare_segment_is_rejected_by_references(
        self, tmp_path: Path
    ) -> None:
        graph = await _build_bridge_reflib_graph(tmp_path)
        summary = await graph.references("lib.champion_routing")
        assert isinstance(summary, ReferenceSummary)
        assert summary.production_references == 0
        assert summary.referencing == []

    async def test_wrong_fqn_sharing_only_the_bare_segment_is_rejected_by_blast_radius(
        self, tmp_path: Path
    ) -> None:
        graph = await _build_bridge_reflib_graph(tmp_path)
        radius = await graph.blast_radius(
            "lib.champion_routing", depth=1, max_results=10
        )
        assert radius == []

    async def test_an_unrelated_bare_string_is_honestly_rejected(
        self, tmp_path: Path
    ) -> None:
        """Two ordinary non-matching bare strings — a REGRESSION GUARD (already
        green today): neither ``"outing"`` nor ``"n_routing"`` equals
        ``champion_routing``'s own bare last segment on EITHER the fake's rule
        or the real's, so both must stay honestly empty.
        """
        graph = await _build_bridge_reflib_graph(tmp_path)
        assert (await graph.references("outing")).production_references == 0
        assert (await graph.references("n_routing")).production_references == 0


class TestFakeBareAndFqnBridgeAlignment:
    """Valid bare + FQN queries both work on the fake TODAY (via its own
    over-permissive ``_matches``), and must KEEP working once the fake's
    matching is tightened to the real answers_to-bridge rule (bridge-cycle
    contract item 2c) — pinned so the eventual alignment cannot regress the
    happy path.
    """

    async def test_bare_query_finds_the_resolved_reference(
        self, tmp_path: Path
    ) -> None:
        graph = await _build_bridge_reflib_graph(tmp_path)
        summary = await graph.references("champion_routing")
        assert summary.production_references == 2
        assert _FQN_BRIDGE_DISPATCH in {n.qualified_name for n in summary.referencing}

    async def test_fqn_query_finds_the_resolved_reference(
        self, tmp_path: Path
    ) -> None:
        graph = await _build_bridge_reflib_graph(tmp_path)
        summary = await graph.references(_FQN_BRIDGE_CHAMPION_ROUTING)
        assert summary.production_references == 2
        assert _FQN_BRIDGE_DISPATCH in {n.qualified_name for n in summary.referencing}


# --------------------------------------------------------------------------- #
# Finding #65/#43 channel honesty -- FakeSurrealCodeGraph.references() fidelity
# gap (REPORT-slate-builder-impactres.md decisions-needed #2): the fake used
# to construct EVERY ReferenceSummary with bare_fallback_used/
# bare_fallback_candidates left at their pydantic defaults (False/[]), so any
# test riding this shared fixture to assert channel honesty would silently get
# the default rather than a real signal. Two independently re-materialised
# corpora below (SAME naming convention as ``test_graph_surreal.py``'s
# ``TestReferencesBareFallbackChannelHonesty`` / ``TestReferencesBareNameFqn
# CollisionFanOut`` -- clause 5, never a cross-file import of their locals)
# reproduce BOTH risk shapes against the FAKE: a DOTTED/FQN query riding the
# risky bare-trailing-segment term (an astroid-unresolvable caller elsewhere
# sharing the bare tail), and a genuinely BARE query colliding across two
# independently-resolved FQNs.
# --------------------------------------------------------------------------- #

_CHANNEL_ALPHA_SOURCE = textwrap.dedent(
    '''\
    """channel_pkg.alpha -- defines ClassAlpha.resolve, called via a receiver
    astroid CAN infer (a local instantiation) -- a RESOLVED call, so its dst
    is the exact FQN, never the bare fallback."""


    class ClassAlpha:
        """Alpha's own resolve -- collides on the bare name with beta's."""

        def resolve(self, name):
            """Alpha's resolve."""
            return name
    '''
)
_CHANNEL_ALPHA_CONSUMER_SOURCE = textwrap.dedent(
    '''\
    """A production caller whose receiver type astroid CAN infer."""
    from channel_pkg.alpha import ClassAlpha


    def use_alpha(name):
        """Instantiates ClassAlpha directly -- a RESOLVED call."""
        alpha = ClassAlpha()
        return alpha.resolve(name)
    '''
)
_CHANNEL_BETA_SOURCE = textwrap.dedent(
    '''\
    """channel_pkg.beta -- a SEPARATE, unrelated module ALSO defining a
    ``resolve`` method (same bare name, different FQN, no relation to
    channel_pkg.alpha)."""


    class ClassBeta:
        """Beta's own resolve -- unrelated to alpha's."""

        def resolve(self, name):
            """Beta's resolve."""
            return name
    '''
)
_CHANNEL_BETA_CONSUMER_SOURCE = textwrap.dedent(
    '''\
    """A production caller whose receiver type astroid CANNOT infer -- the
    call's dst falls back to the bare written name "resolve", never
    channel_pkg.beta.ClassBeta.resolve."""


    def use_beta(unknown_receiver, name):
        """Calls .resolve on an untyped, un-inferable parameter."""
        return unknown_receiver.resolve(name)
    '''
)

_CHANNEL_ALPHA_PATH = "channel_pkg/alpha.py"
_CHANNEL_ALPHA_CONSUMER_PATH = "channel_pkg/alpha_consumer.py"
_CHANNEL_BETA_PATH = "channel_pkg/beta.py"
_CHANNEL_BETA_CONSUMER_PATH = "channel_pkg/beta_consumer.py"

_CHANNEL_ALPHA_MODULE = "channel_pkg.alpha"
_CHANNEL_ALPHA_CONSUMER_MODULE = "channel_pkg.alpha_consumer"
_CHANNEL_BETA_MODULE = "channel_pkg.beta"
_CHANNEL_BETA_CONSUMER_MODULE = "channel_pkg.beta_consumer"

_FQN_CHANNEL_ALPHA_RESOLVE = "channel_pkg.alpha.ClassAlpha.resolve"
_FQN_CHANNEL_BETA_RESOLVE = "channel_pkg.beta.ClassBeta.resolve"
_FQN_CHANNEL_USE_ALPHA = "channel_pkg.alpha_consumer.use_alpha"
_FQN_CHANNEL_USE_BETA = "channel_pkg.beta_consumer.use_beta"


async def _build_channel_risk_graph(tmp_path: Path) -> FakeSurrealCodeGraph:
    """Materialise the alpha(resolved)/beta(unresolved) bare-collision
    package; build a fresh, resolution-enabled :class:`FakeSurrealCodeGraph`
    over all four files -- finding #65's live shape: an exact-FQN query for
    alpha's ``resolve`` is joined by beta's astroid-unresolvable caller,
    which can ONLY be reached via the bare-trailing-segment OR-term.
    """
    root = tmp_path / "project"
    (root / "channel_pkg").mkdir(parents=True)
    (root / "channel_pkg" / "__init__.py").write_text("", encoding="utf-8")
    (root / "channel_pkg" / "alpha.py").write_text(_CHANNEL_ALPHA_SOURCE, encoding="utf-8")
    (root / "channel_pkg" / "alpha_consumer.py").write_text(
        _CHANNEL_ALPHA_CONSUMER_SOURCE, encoding="utf-8"
    )
    (root / "channel_pkg" / "beta.py").write_text(_CHANNEL_BETA_SOURCE, encoding="utf-8")
    (root / "channel_pkg" / "beta_consumer.py").write_text(
        _CHANNEL_BETA_CONSUMER_SOURCE, encoding="utf-8"
    )
    trio = fake_surreal_trio(
        dim=PRODUCTION_DIM, tier_roots={_BRIDGE_TIER: root}, project_roots=[root]
    )
    for path, source, module in (
        (_CHANNEL_ALPHA_PATH, _CHANNEL_ALPHA_SOURCE, _CHANNEL_ALPHA_MODULE),
        (
            _CHANNEL_ALPHA_CONSUMER_PATH,
            _CHANNEL_ALPHA_CONSUMER_SOURCE,
            _CHANNEL_ALPHA_CONSUMER_MODULE,
        ),
        (_CHANNEL_BETA_PATH, _CHANNEL_BETA_SOURCE, _CHANNEL_BETA_MODULE),
        (
            _CHANNEL_BETA_CONSUMER_PATH,
            _CHANNEL_BETA_CONSUMER_SOURCE,
            _CHANNEL_BETA_CONSUMER_MODULE,
        ),
    ):
        await trio.graph.build_file_graph(
            _BRIDGE_TIER, path, _bridge_chunk(path, source), module_name=module
        )
    return trio.graph


_COLLIDE_ALPHA_LIB_SOURCE = textwrap.dedent(
    '''\
    """collide_routing.alpha_lib -- defines its OWN champion_routing."""


    def champion_routing(week):
        """Route the alpha warehouse."""
        return week * 2
    '''
)
_COLLIDE_ALPHA_CONSUMER_SOURCE = textwrap.dedent(
    '''\
    """A production caller of alpha's champion_routing."""
    from collide_routing.alpha_lib import champion_routing


    def alpha_dispatch(week):
        """The alpha production caller."""
        return champion_routing(week)
    '''
)
_COLLIDE_BETA_LIB_SOURCE = textwrap.dedent(
    '''\
    """collide_routing.beta_lib -- a SEPARATE module, ALSO defining
    champion_routing (same bare name, different FQN, no relation to
    collide_routing.alpha_lib)."""


    def champion_routing(week):
        """Route the beta warehouse."""
        return week * 3
    '''
)
_COLLIDE_BETA_CONSUMER_SOURCE = textwrap.dedent(
    '''\
    """A production caller of beta's champion_routing."""
    from collide_routing.beta_lib import champion_routing


    def beta_dispatch(week):
        """The beta production caller."""
        return champion_routing(week)
    '''
)

_COLLIDE_ALPHA_LIB_PATH = "collide_routing/alpha_lib.py"
_COLLIDE_ALPHA_CONSUMER_PATH = "collide_routing/alpha_consumer.py"
_COLLIDE_BETA_LIB_PATH = "collide_routing/beta_lib.py"
_COLLIDE_BETA_CONSUMER_PATH = "collide_routing/beta_consumer.py"

_COLLIDE_ALPHA_LIB_MODULE = "collide_routing.alpha_lib"
_COLLIDE_ALPHA_CONSUMER_MODULE = "collide_routing.alpha_consumer"
_COLLIDE_BETA_LIB_MODULE = "collide_routing.beta_lib"
_COLLIDE_BETA_CONSUMER_MODULE = "collide_routing.beta_consumer"

_FQN_COLLIDE_ALPHA_ROUTING = "collide_routing.alpha_lib.champion_routing"
_FQN_COLLIDE_BETA_ROUTING = "collide_routing.beta_lib.champion_routing"


async def _build_routing_collide_graph(tmp_path: Path) -> FakeSurrealCodeGraph:
    """Materialise the two-module RESOLVED bare-name-collision package; build
    a fresh, resolution-enabled :class:`FakeSurrealCodeGraph` over all four
    files -- a genuine bare-name fan-out where BOTH collidees are
    independently resolved from their own caller (no unresolved call needed
    for this shape, unlike :func:`_build_channel_risk_graph`)."""
    root = tmp_path / "project"
    (root / "collide_routing").mkdir(parents=True)
    (root / "collide_routing" / "__init__.py").write_text("", encoding="utf-8")
    (root / "collide_routing" / "alpha_lib.py").write_text(
        _COLLIDE_ALPHA_LIB_SOURCE, encoding="utf-8"
    )
    (root / "collide_routing" / "alpha_consumer.py").write_text(
        _COLLIDE_ALPHA_CONSUMER_SOURCE, encoding="utf-8"
    )
    (root / "collide_routing" / "beta_lib.py").write_text(
        _COLLIDE_BETA_LIB_SOURCE, encoding="utf-8"
    )
    (root / "collide_routing" / "beta_consumer.py").write_text(
        _COLLIDE_BETA_CONSUMER_SOURCE, encoding="utf-8"
    )
    trio = fake_surreal_trio(
        dim=PRODUCTION_DIM, tier_roots={_BRIDGE_TIER: root}, project_roots=[root]
    )
    for path, source, module in (
        (_COLLIDE_ALPHA_LIB_PATH, _COLLIDE_ALPHA_LIB_SOURCE, _COLLIDE_ALPHA_LIB_MODULE),
        (
            _COLLIDE_ALPHA_CONSUMER_PATH,
            _COLLIDE_ALPHA_CONSUMER_SOURCE,
            _COLLIDE_ALPHA_CONSUMER_MODULE,
        ),
        (_COLLIDE_BETA_LIB_PATH, _COLLIDE_BETA_LIB_SOURCE, _COLLIDE_BETA_LIB_MODULE),
        (
            _COLLIDE_BETA_CONSUMER_PATH,
            _COLLIDE_BETA_CONSUMER_SOURCE,
            _COLLIDE_BETA_CONSUMER_MODULE,
        ),
    ):
        await trio.graph.build_file_graph(
            _BRIDGE_TIER, path, _bridge_chunk(path, source), module_name=module
        )
    return trio.graph


class TestFakeReferencesBareFallbackChannelHonesty:
    """Finding #65/#43 fidelity: the FAKE must disclose the bare-fallback
    channel too -- the gap REPORT-slate-builder-impactres.md's decisions-
    needed #2 flagged (the fake always defaulted both fields to False/[], so
    a future test riding the fixture would silently get a clean-looking
    summary even over a genuinely colliding corpus).

    Mirrors ``test_graph_surreal.py``'s ``TestReferencesBareFallbackChannel
    Honesty`` (same corpus SHAPE, independently re-materialised per this
    file's own convention) plus ``TestReferencesBareNameFqnCollisionFanOut``'s
    bare-collision case, against the FAKE instead of the real
    ``SurrealCodeGraph``.
    """

    async def test_exact_query_names_the_colliding_candidate_when_the_bare_channel_serves(
        self, tmp_path: Path
    ) -> None:
        """``references(FQN_CHANNEL_ALPHA_RESOLVE)`` must ALSO surface beta's
        unresolved caller, HONESTLY: flagged, with beta's FQN named, never
        silently presented as alpha's own clean profile."""
        graph = await _build_channel_risk_graph(tmp_path)
        summary = await graph.references(_FQN_CHANNEL_ALPHA_RESOLVE)
        referrers = {n.qualified_name for n in summary.referencing}

        assert _FQN_CHANNEL_USE_ALPHA in referrers
        assert _FQN_CHANNEL_USE_BETA in referrers
        assert summary.production_references == 2

        assert summary.bare_fallback_used is True
        assert _FQN_CHANNEL_BETA_RESOLVE in summary.bare_fallback_candidates
        assert _FQN_CHANNEL_ALPHA_RESOLVE not in summary.bare_fallback_candidates

    async def test_exact_query_with_no_real_collision_never_flags_the_channel(
        self, tmp_path: Path
    ) -> None:
        """A clean, non-colliding exact-FQN query must never flag the
        channel -- the honesty fix must not manufacture risk where none
        exists."""
        graph = await _build_bridge_reflib_graph(tmp_path)
        summary = await graph.references(_FQN_BRIDGE_CHAMPION_ROUTING)

        assert summary.bare_fallback_used is False
        assert summary.bare_fallback_candidates == []

    async def test_bare_query_with_a_unique_symbol_never_flags_the_channel(
        self, tmp_path: Path
    ) -> None:
        """A bare query is only "risky" when it genuinely collides across
        more than one distinct symbol -- reaching a resolved FQN via the
        bridge is how every bare query works, never itself the risk."""
        graph = await _build_bridge_reflib_graph(tmp_path)
        summary = await graph.references("champion_routing")

        assert summary.bare_fallback_used is False
        assert summary.bare_fallback_candidates == []

    async def test_bare_query_with_a_genuine_collision_flags_and_names_both_candidates(
        self, tmp_path: Path
    ) -> None:
        """A bare query genuinely colliding across two distinct FQNs must
        flag the channel and name BOTH real candidates (finding #43's ask),
        not a generic "may collide" hedge."""
        graph = await _build_routing_collide_graph(tmp_path)
        summary = await graph.references("champion_routing")

        assert summary.bare_fallback_used is True
        assert set(summary.bare_fallback_candidates) == {
            _FQN_COLLIDE_ALPHA_ROUTING,
            _FQN_COLLIDE_BETA_ROUTING,
        }


class TestFakeReferenceSummaryFieldParity:
    """FIDELITY PIN (the point of this wave -- the steering fix above closes
    TODAY's gap, this pin stops the NEXT one): the fake's
    ``ReferenceSummary(...)`` construction call inside ``references()`` must
    explicitly pass EVERY field the real pydantic model declares. An AST scan
    of the method's own source (never a live call, so a branch a given test
    corpus does not exercise cannot hide a missing keyword) -- the SAME
    "AST scan over string literals" idiom ``test_text_hygiene.py`` already
    established for a different defect class in this repo, applied here to a
    constructor-call SHAPE instead of a string literal.

    bare_fallback_used/bare_fallback_candidates were the SECOND time this
    fake silently defaulted a new ``ReferenceSummary`` field (production_
    references/test_references/referencing were never at risk -- they are
    the model's original fields); this pin makes a THIRD time impossible to
    ship unnoticed: it fails the moment ``ReferenceSummary`` grows a field
    this fake's construction call does not name, regardless of whether any
    OTHER test happens to exercise it yet.
    """

    @staticmethod
    def _reference_summary_construction_kwargs() -> set[str]:
        """The keyword-argument names ``FakeSurrealCodeGraph.references``
        passes when constructing its ``ReferenceSummary`` return value."""
        source = textwrap.dedent(inspect.getsource(FakeSurrealCodeGraph.references))
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "ReferenceSummary"
            ):
                return {kw.arg for kw in node.keywords if kw.arg is not None}
        raise AssertionError(
            "no ReferenceSummary(...) construction found in "
            "FakeSurrealCodeGraph.references() -- has it been refactored away?"
        )

    def test_fake_construction_sets_every_field_the_real_model_declares(self) -> None:
        real_fields = set(ReferenceSummary.model_fields)
        fake_kwargs = self._reference_summary_construction_kwargs()
        assert fake_kwargs == real_fields, (
            f"FakeSurrealCodeGraph.references() must explicitly pass every "
            f"ReferenceSummary field so a new field can never silently take "
            f"its pydantic default in the fake; missing="
            f"{real_fields - fake_kwargs!r} extra={fake_kwargs - real_fields!r}"
        )
