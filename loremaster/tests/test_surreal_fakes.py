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

import inspect
import math
from collections.abc import Callable
from typing import Any

import pytest
from _surreal_fakes import FakeSurrealStore, fake_surreal_trio
from _surreal_harness import PRODUCTION_DIM, TIER_A, TIER_B, chunk_record, unit_vector
from loremaster.index.records import Record
from loremaster.store.candidate import Candidate
from loremaster.store.surreal import (
    SurrealConnectionError,
    SurrealStore,
    SurrealStoreError,
    _RRF_K as _PRODUCTION_RRF_K,
)
from loremaster.store.surreal_schema import CHUNK_FILTER_KEYS
from loremaster.symbols import _SCROLL_LIMIT  # the real scroll caller's read cap

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
