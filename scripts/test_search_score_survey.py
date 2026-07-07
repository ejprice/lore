"""Unit tests for the deterministic core of ``scripts/search_score_survey.py``.

These cover the pure, network-free concerns the S4b weak-match-discrimination
measurement protocol (docs/design/2026-07-06-weak-match-discrimination.md §6)
depends on:

* **Eval-question mining** — extracting the 35-pair eval set's ``<question>``
  text (real, authentic code-intent queries) from ``loremaster/evaluation.xml``.
* **Deterministic corpus sampling** — ``every_nth`` (the identifier group's
  "sorted qualified names, every Nth" rule).
* **The verbatim-identifier-anchor channel** — D3's exact-lookup carve-out.
* **Per-hit aggregation** — top-hit cosine, max-cosine-of-response, the fused
  top1-top2 margin, within-query spread, source concentration.
* **Distribution summary** — percentile statistics over a group's captures
  (reusing :func:`token_survey.percentile`, not re-implementing percentile math).
* **The D1 substrate gate and D2 floor-selection rules** — pure, pre-registered
  decision functions; this task implements the machinery, it does NOT run
  Phase C selection (see the survey script's module docstring).

The live client (the direct store + embedder connection) is intentionally
*out of scope* here — it is exercised by the real survey run, not by unit
tests (mirrors ``token_survey.py``'s network/pure split).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest
from loremaster.store.candidate import Candidate

# The survey module lives beside this test file in ``scripts/`` (not an
# installed package), so make that directory importable before importing it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import search_score_survey as sss  # noqa: E402  (path insert must precede the import)

# --------------------------------------------------------------------------- #
# parse_eval_questions
# --------------------------------------------------------------------------- #
_SAMPLE_EVAL_XML = """<?xml version="1.0" encoding="UTF-8"?>
<evaluation>
   <qa_pair>
      <question>What is the exact name of the probe-gate exception class?</question>
      <answer>ProbeGateError</answer>
   </qa_pair>
   <qa_pair>
      <question>  Which module defines the once-per-process lifespan guard?  </question>
      <answer>_ProcessLifespanGuard</answer>
   </qa_pair>
</evaluation>
"""


class TestParseEvalQuestions:
    def test_extracts_question_text_in_document_order(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "evaluation.xml"
        xml_path.write_text(_SAMPLE_EVAL_XML, encoding="utf-8")

        questions = sss.parse_eval_questions(xml_path)

        assert questions == [
            "What is the exact name of the probe-gate exception class?",
            "Which module defines the once-per-process lifespan guard?",
        ]

    def test_strips_surrounding_whitespace(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "evaluation.xml"
        xml_path.write_text(_SAMPLE_EVAL_XML, encoding="utf-8")

        questions = sss.parse_eval_questions(xml_path)

        assert all(q == q.strip() for q in questions)

    def test_real_repo_eval_file_yields_35_questions(self) -> None:
        """Grounding receipt: the committed 35-pair set really has 35 questions."""
        real_path = (
            Path(__file__).resolve().parents[1] / "loremaster" / "evaluation.xml"
        )
        questions = sss.parse_eval_questions(real_path)
        assert len(questions) == 35
        assert all(isinstance(q, str) and q for q in questions)


# --------------------------------------------------------------------------- #
# NONSENSE_QUERIES — the adversarial contrast set
# --------------------------------------------------------------------------- #
class TestNonsenseQueries:
    def test_is_a_nonempty_deterministic_tuple_of_distinct_strings(self) -> None:
        assert isinstance(sss.NONSENSE_QUERIES, tuple)
        assert len(sss.NONSENSE_QUERIES) >= 10
        assert len(set(sss.NONSENSE_QUERIES)) == len(sss.NONSENSE_QUERIES)
        assert all(isinstance(q, str) and q.strip() for q in sss.NONSENSE_QUERIES)


# --------------------------------------------------------------------------- #
# IMPLEMENTATION_VOCABULARY_QUERIES — finding #74's own query class (the
# fourth false-fire-union group): informant-probe-style natural-language
# DESCRIPTIONS of a mechanism, sourced verbatim from documented probes, each
# with its ground-truth target verified indexed (docstring comments in the
# survey module, never vibes).
# --------------------------------------------------------------------------- #
class TestImplementationVocabularyQueries:
    def test_is_a_nonempty_deterministic_tuple_of_distinct_strings(self) -> None:
        assert isinstance(sss.IMPLEMENTATION_VOCABULARY_QUERIES, tuple)
        assert len(sss.IMPLEMENTATION_VOCABULARY_QUERIES) >= 4
        assert len(set(sss.IMPLEMENTATION_VOCABULARY_QUERIES)) == len(
            sss.IMPLEMENTATION_VOCABULARY_QUERIES
        )
        assert all(
            isinstance(q, str) and q.strip() for q in sss.IMPLEMENTATION_VOCABULARY_QUERIES
        )

    def test_includes_the_finding_74_probe_verbatim(self) -> None:
        # The exact query text finding #74 was filed against (docs/design/
        # 2026-07-06-client-needs-consult.md:437) — the probe that motivated
        # this whole query group must itself be a member, not just "a
        # similar one".
        assert (
            "enforce the search token budget and build the elision notice "
            "naming elided hits"
        ) in sss.IMPLEMENTATION_VOCABULARY_QUERIES


# --------------------------------------------------------------------------- #
# every_nth — the identifier group's deterministic corpus-sampling rule
# --------------------------------------------------------------------------- #
class TestEveryNth:
    def test_returns_everything_when_pool_is_at_or_under_count(self) -> None:
        assert sss.every_nth(["a", "b", "c"], 5) == ["a", "b", "c"]
        assert sss.every_nth(["a", "b"], 2) == ["a", "b"]

    def test_returns_exactly_count_items_when_pool_is_larger(self) -> None:
        pool = [f"sym_{i}" for i in range(100)]
        sampled = sss.every_nth(pool, 15)
        assert len(sampled) == 15

    def test_sampling_is_deterministic_across_calls(self) -> None:
        pool = [f"sym_{i}" for i in range(37)]
        assert sss.every_nth(pool, 15) == sss.every_nth(pool, 15)

    def test_sampling_is_evenly_spread_not_a_prefix(self) -> None:
        pool = [f"sym_{i}" for i in range(100)]
        sampled = sss.every_nth(pool, 10)
        indices = [pool.index(item) for item in sampled]
        # An evenly-spread sample must reach well past the first 10 indices —
        # a bug that silently prefix-slices would fail this.
        assert max(indices) >= 80

    def test_empty_pool_returns_empty(self) -> None:
        assert sss.every_nth([], 15) == []


# --------------------------------------------------------------------------- #
# query_tokens / has_verbatim_identifier_anchor — the D3 carve-out channel
# --------------------------------------------------------------------------- #
class TestQueryTokens:
    def test_splits_on_word_boundaries_lowercased(self) -> None:
        assert sss.query_tokens("PurchaseOrder.action_confirm!") == frozenset(
            {"purchaseorder", "action_confirm"}
        )

    def test_empty_text_yields_empty_set(self) -> None:
        assert sss.query_tokens("   ") == frozenset()


class TestHasVerbatimIdentifierAnchor:
    """D3 fix (2026-07-06): the anchor now takes the RAW query text (not a
    pre-tokenized set) — it computes its own identifier-shaped query tokens
    internally (:func:`loremaster.search._identifier_shaped_query_tokens`),
    plus a whole-query fallback. Full coverage of the rule (the shape
    criteria, the measured nonsense-query non-anchoring) lives in
    ``loremaster/tests/test_search.py``; these are the survey's own smoke
    tests via the re-exported/parity-pinned production function.
    """

    def test_true_when_a_shaped_query_token_is_a_whole_token_in_ident_text(self) -> None:
        assert sss.has_verbatim_identifier_anchor(
            "find action_confirm please", "PurchaseOrder action_confirm"
        ) is True

    def test_false_on_whole_token_boundary_not_a_substring_scan(self) -> None:
        # "is_a" (shaped, underscore-bearing) must not spuriously match
        # inside the LONGER glued token "this_is_a_test" — a token-SET
        # intersection, never a raw substring scan.
        assert sss.has_verbatim_identifier_anchor("check is_a value", "this_is_a_test") is False

    def test_bare_common_english_overlap_no_longer_anchors(self) -> None:
        # D3 fix (measured defect: 9/15 nonsense queries anchored via a bare
        # word before this fix) — "client" is common English, not a pasted
        # identifier, even though it lines up with a real ident_text token.
        assert sss.has_verbatim_identifier_anchor(
            "rate limiting middleware per client IP address", "Client client"
        ) is False

    def test_empty_query_never_anchors(self) -> None:
        assert sss.has_verbatim_identifier_anchor("   ", "anything") is False


# --------------------------------------------------------------------------- #
# Predicate parity with production (S4b audit finding #1,
# REPORT-slate-audit-searchstore.md §Concern 6): the survey must run the
# IDENTICAL tokenizer / anchor-detector / verdict-firing rule production's
# ``loremaster.search._cosine_absence_verdict`` runs — an IMPORT, never a
# re-derivation that can silently drift. Identity (``is``) pins, mirroring
# the repo's own ``TestSharedMechanismPin`` precedent (finding #69,
# ``test_query_text.py``).
# --------------------------------------------------------------------------- #
class TestPredicateParityWithProduction:
    def test_query_tokens_is_the_production_function(self) -> None:
        from loremaster import search as search_module

        assert sss.query_tokens is search_module._query_tokens

    def test_has_verbatim_identifier_anchor_is_the_production_function(self) -> None:
        from loremaster import search as search_module

        assert sss.has_verbatim_identifier_anchor is search_module._has_verbatim_identifier_anchor

    def test_verdict_fires_predicate_is_the_production_function(self) -> None:
        from loremaster import search as search_module

        assert sss.cosine_absence_verdict_fires is search_module._cosine_absence_predicate


# --------------------------------------------------------------------------- #
# HitCapture aggregation — top-hit cosine, max-of-response, margin, spread,
# source concentration.
# --------------------------------------------------------------------------- #
def _hit(
    fused_score: float,
    vector_cosine: float | None,
    *,
    file_path: str = "pkg/mod.py",
    ident_text: str = "some_function",
    origin: str = "fused",
) -> sss.HitCapture:
    return sss.HitCapture(
        fused_score=fused_score, vector_cosine=vector_cosine,
        file_path=file_path, ident_text=ident_text, origin=origin,
    )


class TestTopHitCosine:
    def test_returns_the_first_hits_cosine(self) -> None:
        hits = [_hit(0.03, 0.7), _hit(0.02, 0.9)]
        assert sss.top_hit_cosine(hits) == pytest.approx(0.7)

    def test_none_when_top_hit_has_no_cosine(self) -> None:
        assert sss.top_hit_cosine([_hit(0.03, None)]) is None

    def test_none_on_empty_hits(self) -> None:
        assert sss.top_hit_cosine([]) is None


class TestMaxCosineOfResponse:
    def test_returns_the_maximum_not_the_top_fused_hits(self) -> None:
        # The design doc's own warning: a cosine-strong hit can sit BELOW a
        # cosine-weak one in fused order.
        hits = [_hit(0.03, 0.2), _hit(0.02, 0.9)]
        assert sss.max_cosine_of_response(hits) == pytest.approx(0.9)

    def test_ignores_hits_with_no_cosine(self) -> None:
        hits = [_hit(0.03, None), _hit(0.02, 0.5)]
        assert sss.max_cosine_of_response(hits) == pytest.approx(0.5)

    def test_none_when_no_hit_has_a_cosine(self) -> None:
        assert sss.max_cosine_of_response([_hit(0.03, None)]) is None


class TestFusedTopMargin:
    def test_computes_top_minus_second(self) -> None:
        hits = [_hit(0.03, 0.5), _hit(0.02, 0.5)]
        assert sss.fused_top_margin(hits) == pytest.approx(0.01)

    def test_none_with_fewer_than_two_hits(self) -> None:
        assert sss.fused_top_margin([_hit(0.03, 0.5)]) is None
        assert sss.fused_top_margin([]) is None


class TestWithinQueryCosineSpread:
    def test_computes_max_minus_min_among_cosine_bearing_hits(self) -> None:
        hits = [_hit(0.03, 0.9), _hit(0.02, 0.3), _hit(0.01, None)]
        assert sss.within_query_cosine_spread(hits) == pytest.approx(0.6)

    def test_none_with_fewer_than_two_cosine_bearing_hits(self) -> None:
        assert sss.within_query_cosine_spread([_hit(0.03, 0.9), _hit(0.02, None)]) is None
        assert sss.within_query_cosine_spread([]) is None


class TestSourceConcentration:
    def test_counts_distinct_file_paths(self) -> None:
        hits = [_hit(0.03, 0.9, file_path="a.py"), _hit(0.02, 0.3, file_path="a.py"),
                _hit(0.01, 0.1, file_path="b.py")]
        assert sss.source_concentration(hits) == 2

    def test_zero_on_empty_hits(self) -> None:
        assert sss.source_concentration([]) == 0


# --------------------------------------------------------------------------- #
# summarize_cosine_group
# --------------------------------------------------------------------------- #
def _capture(
    query: str, kind: sss.QueryKind, hits: list[sss.HitCapture], *, has_anchor: bool = False
) -> sss.QueryCapture:
    return sss.QueryCapture(
        query=query, query_kind=kind, hits=tuple(hits),
        pre_budget_pool_size=len(hits), has_verbatim_anchor=has_anchor,
    )


class TestSummarizeCosineGroup:
    def test_summarizes_top_and_max_cosine_distributions(self) -> None:
        captures = [
            _capture("q1", "real", [_hit(0.03, 0.5), _hit(0.02, 0.9)]),
            _capture("q2", "real", [_hit(0.03, 0.6)]),
        ]
        summary = sss.summarize_cosine_group(captures, label="real")

        assert summary.label == "real"
        assert summary.n == 2
        assert summary.n_with_cosine == 2
        assert summary.top_hit_mean == pytest.approx((0.5 + 0.6) / 2)
        assert summary.max_response_mean == pytest.approx((0.9 + 0.6) / 2)

    def test_raises_on_empty_capture_list(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            sss.summarize_cosine_group([], label="real")

    def test_raises_when_nothing_ever_captured_a_cosine(self) -> None:
        captures = [_capture("q1", "real", [_hit(0.03, None)])]
        with pytest.raises(ValueError, match="no cosine-bearing"):
            sss.summarize_cosine_group(captures, label="real")


# --------------------------------------------------------------------------- #
# query_capture_to_verdict_sample — the (max_cosine, has_verbatim_anchor)
# pair choose_cosine_floor scores against (S4b audit finding #1: the
# PRODUCTION predicate needs BOTH signals, never top_hit_cosine alone).
# --------------------------------------------------------------------------- #
class TestQueryCaptureToVerdictSample:
    def test_builds_a_sample_from_max_cosine_and_the_anchor_flag(self) -> None:
        capture = _capture(
            "q1", "real", [_hit(0.03, 0.2), _hit(0.02, 0.9)], has_anchor=True
        )
        sample = sss.query_capture_to_verdict_sample(capture)
        assert sample == sss.VerdictSample(max_cosine=0.9, has_verbatim_anchor=True)

    def test_none_when_the_capture_has_no_cosine_at_all(self) -> None:
        capture = _capture("q1", "real", [_hit(0.03, None)])
        assert sss.query_capture_to_verdict_sample(capture) is None


# --------------------------------------------------------------------------- #
# choose_cosine_floor (D2) / substrate_gate_passes (D1)
# --------------------------------------------------------------------------- #
class TestChooseCosineFloor:
    def test_picks_the_max_catch_floor_within_the_false_fire_ceiling(self) -> None:
        # Union has 20 samples; ceiling 5% permits at most 1 false-fire.
        union = [sss.VerdictSample(0.5, False) for _ in range(19)] + [
            sss.VerdictSample(0.1, False)  # one low outlier tolerable at 5%
        ]
        nonsense = [sss.VerdictSample(v, False) for v in (0.05, 0.15, 0.6, 0.7)]

        rec = sss.choose_cosine_floor(union, nonsense, max_false_fire_rate=0.05)

        assert rec is not None
        # floor=0.5 false-fires only on the single 0.1 sample (1/20 = 5%,
        # admissible) and catches nonsense scores strictly below 0.5:
        # 0.05 and 0.15 -> 2/4.
        assert rec.floor == pytest.approx(0.5)
        assert rec.false_fire_rate == pytest.approx(1 / 20)
        assert rec.nonsense_catch_rate == pytest.approx(2 / 4)

    def test_a_verbatim_anchored_low_cosine_query_never_counts_as_a_false_fire(
        self,
    ) -> None:
        # Production NEVER fires the absence verdict on an anchored hit
        # (D3). Without the carve-out this low-cosine sample would
        # false-fire at floor=0.5 (1/20 = 5%, right at the ceiling); WITH
        # it, the anchored sample contributes zero and the SAME floor is
        # admissible at 0% false-fire.
        union = [sss.VerdictSample(0.5, False) for _ in range(19)] + [
            sss.VerdictSample(0.1, True)
        ]
        nonsense = [sss.VerdictSample(0.05, False)]

        rec = sss.choose_cosine_floor(union, nonsense, max_false_fire_rate=0.0)

        assert rec.floor == pytest.approx(0.5)
        assert rec.false_fire_rate == pytest.approx(0.0)

    def test_a_verbatim_anchored_nonsense_query_is_never_counted_as_caught(
        self,
    ) -> None:
        union = [sss.VerdictSample(0.9, False)]
        nonsense = [sss.VerdictSample(0.01, True)]  # < any floor, but anchored

        rec = sss.choose_cosine_floor(union, nonsense, max_false_fire_rate=0.05)

        assert rec.nonsense_catch_rate == pytest.approx(0.0)

    def test_the_minimum_observed_value_is_always_admissible(self) -> None:
        # The minimum candidate false-fires on nothing (0/n), so a
        # recommendation always exists even under a very tight ceiling —
        # choose_cosine_floor is total, never None (see its own docstring).
        union = [sss.VerdictSample(v, False) for v in (0.1, 0.2, 0.3, 0.4)]
        nonsense = [sss.VerdictSample(0.05, False)]

        rec = sss.choose_cosine_floor(union, nonsense, max_false_fire_rate=0.0)

        assert rec.floor == pytest.approx(0.1)
        assert rec.false_fire_rate == pytest.approx(0.0)

    def test_prefers_minimum_false_fire_among_max_catch_floors(self) -> None:
        # Dominance geometry (operator/lead ruling on the finding #74 widened
        # re-run, 2026-07-07): the widened survey's OWN data showed a clean
        # gap — nonsense max-of-response tops out at 0.4322, the lowest
        # answered (real+identifier+impl-vocab) max sits at 0.5065 — so every
        # candidate floor in (0.4322, 0.5065] gives the IDENTICAL 100% catch,
        # yet a naive top-down "first admissible from the top" scan (the OLD
        # behaviour) stopped at a HIGHER floor (0.5370) carrying nonzero
        # false-fire, never comparing it against a LOWER floor (0.50 here)
        # that achieves the SAME catch at STRICTLY LESS false-fire. D2's own
        # precision-first name demands the latter. This fixture reproduces
        # that geometry directly (18 comfortably-high real samples + one at
        # 0.55 + one at 0.50; 0.55 alone clears the 5% ceiling at EXACTLY 5%,
        # but 0.50 clears it at 0% for the SAME 100% nonsense catch).
        union = (
            [sss.VerdictSample(0.90, False) for _ in range(18)]
            + [sss.VerdictSample(0.55, False)]
            + [sss.VerdictSample(0.50, False)]
        )
        nonsense = [sss.VerdictSample(v, False) for v in (0.05, 0.10, 0.15, 0.40)]

        rec = sss.choose_cosine_floor(union, nonsense, max_false_fire_rate=0.05)

        assert rec.floor == pytest.approx(0.50)
        assert rec.false_fire_rate == pytest.approx(0.0)
        assert rec.nonsense_catch_rate == pytest.approx(1.0)

    def test_prefers_maximum_floor_when_catch_and_false_fire_both_tie(self) -> None:
        # The THIRD dominance level: two admissible floors can tie on BOTH
        # catch AND false-fire when the anchor carve-out (D3) exempts the
        # ONLY sample that would otherwise separate them — a verbatim-
        # anchored sample contributes ZERO false-fire at every floor
        # (D3), so the candidate at its own value (0.55) and any HIGHER
        # candidate with nothing else in between (0.90 here) score
        # identically. Chosen: the LARGER floor — grounds the choice in the
        # largest defensible observed value, never an arbitrary lower one
        # within a genuine tie.
        union = [sss.VerdictSample(0.90, False) for _ in range(2)] + [
            sss.VerdictSample(0.55, True)  # verbatim-anchored: never a false-fire
        ]
        nonsense = [sss.VerdictSample(v, False) for v in (0.05, 0.10, 0.20)]

        rec = sss.choose_cosine_floor(union, nonsense, max_false_fire_rate=0.05)

        assert rec.floor == pytest.approx(0.90)
        assert rec.false_fire_rate == pytest.approx(0.0)
        assert rec.nonsense_catch_rate == pytest.approx(1.0)

    def test_meets_adoption_bar_checks_the_pre_registered_catch_threshold(self) -> None:
        rec = sss.CosineFloorRecommendation(
            floor=0.5, false_fire_rate=0.05, nonsense_catch_rate=0.6, n_union=20, n_nonsense=15
        )
        assert rec.meets_adoption_bar() is True
        assert rec.meets_adoption_bar(min_catch=0.7) is False

    def test_rejects_empty_union(self) -> None:
        with pytest.raises(ValueError, match="real_query_samples"):
            sss.choose_cosine_floor(
                [], [sss.VerdictSample(0.1, False)], max_false_fire_rate=0.05
            )

    def test_rejects_empty_nonsense(self) -> None:
        with pytest.raises(ValueError, match="nonsense"):
            sss.choose_cosine_floor(
                [sss.VerdictSample(0.1, False)], [], max_false_fire_rate=0.05
            )


class TestSubstrateGatePasses:
    def test_passes_when_median_spread_is_at_or_above_the_bar(self) -> None:
        assert sss.substrate_gate_passes([0.1, 0.2, 0.3], min_median_spread=0.05) is True

    def test_fails_when_median_spread_is_below_the_bar(self) -> None:
        assert sss.substrate_gate_passes([0.001, 0.002], min_median_spread=0.05) is False

    def test_fails_on_empty_spreads_never_assumes_pass(self) -> None:
        assert sss.substrate_gate_passes([], min_median_spread=0.05) is False


# --------------------------------------------------------------------------- #
# survey() — read-only store path (S4b audit finding #2,
# REPORT-slate-audit-searchstore.md §Concern 6): the survey's store
# connection must be READ-ONLY end to end, like ``scripts/snapshot_gc.py``'s
# read store (never ``ensure_ready``-ed) — ``hybrid_search``/``scroll`` reach
# the store via ``_ensure_connection`` alone, no schema DDL. A spy double
# (never a live connection) pins that ``ensure_ready`` is never called.
# --------------------------------------------------------------------------- #
class _SpySurrealStore:
    """Records which store calls ``survey()`` makes — no live connection."""

    def __init__(self) -> None:
        self.ensure_ready_called = False
        self.scroll_called = False
        self.hybrid_search_called = False
        self.closed = False

    async def ensure_ready(self) -> None:
        self.ensure_ready_called = True

    async def scroll(self, filters: dict[str, str], limit: int) -> list[dict[str, Any]]:
        self.scroll_called = True
        return []

    async def hybrid_search(
        self,
        *,
        query_vector: list[float],
        query_text: str,
        k: int,
        filters: dict[str, str] | None = None,
    ) -> list[Candidate]:
        self.hybrid_search_called = True
        return []

    async def close(self) -> None:
        self.closed = True


class _SpyEmbedder:
    """A minimal embedder double — one fixed-dim vector per query, no network."""

    async def embed_query(self, text: str) -> list[float]:
        return [0.0]


class TestSurveyIsReadOnly:
    async def test_survey_never_calls_ensure_ready(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = _SpySurrealStore()
        embedder = _SpyEmbedder()
        monkeypatch.setattr(sss, "_make_store", lambda: store)
        monkeypatch.setattr(sss, "_make_embedder", lambda: embedder)

        await sss.survey(["a real question"], ["a nonsense question"])

        assert store.ensure_ready_called is False, (
            "survey() must be read-only — a live run would issue a schema-DDL "
            "write transaction against production"
        )
        assert store.scroll_called is True, "identifier sampling must still scroll"
        assert store.hybrid_search_called is True, "queries must still search"
        assert store.closed is True, "the store must still be closed in the finally block"
