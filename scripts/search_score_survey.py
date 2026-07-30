"""Search-score survey — the measured substrate behind S4b's cosine machinery.

Purpose
-------
lore_search's fused (HNSW + BM25 RRF) hybrid_search has no "no match" state: it
always returns nearest neighbors, so a nonsense query renders identically to a
confident one. S4 (REPORT-slate-builder-search.md) measured that the FUSED
score cannot discriminate this (a rank-fusion CODE, not a magnitude — see
docs/design/2026-07-06-weak-match-discrimination.md §1.2). S4b's design
(same doc, §6 "the measurement protocol") replaces the fused-score floor with
a PRE-FUSION COSINE substrate + a gated absence verdict, and this script is
that protocol's Phase B survey extension.

Three query groups, captured against the SAME live corpus:

* **Real** — the 35-pair eval set's ``<question>`` text (``loremaster/
  evaluation.xml``), authentic code-intent queries with known ground truth.
* **Identifier** — 15 exact symbol names DETERMINISTICALLY sampled from the
  indexed corpus itself (sorted qualified names, every Nth — see
  :func:`every_nth`), so the exact-lookup false-flag channel (D3's carve-out)
  is measured, never assumed.
* **Nonsense** — the fixed 15-query adversarial contrast set, unchanged from S4.

Design change from the S4 survey: connects DIRECTLY to the live store +
embedder (mirrors ``scripts/snapshot_gc.py``'s own precedent — hardcoded
connection constants, ``resolve_secret`` for credentials — rather than
``loremaster.config.load_config``, which eagerly requires ``ANTHROPIC_API_KEY``
for an unrelated reason) instead of the deployed MCP tool. Phase B needs
signals — ``vector_cosine``, per-hit provenance, the TRUE pre-render candidate
count — that are computed pre-render and never belonged on the client-facing
wire: a direct store connection measures every signal the design's Phase C
selection rule needs without any wire-shape change, keeping D4 (what the
served ``score`` field looks like) entirely out of this script's business.

Design
------
Mirrors ``token_survey.py``'s split: the deterministic core (corpus sampling,
per-hit aggregation, percentile summaries, the D1/D2 gate rules) is pure and
unit-tested (``test_search_score_survey.py``); the live client (the store +
embedder connection, one search per query) is the only network surface and is
intentionally test-exempt. Percentile math is REUSED from :mod:`token_survey`
(:func:`token_survey.percentile`), not re-implemented.

Constant-13 verdict (S4b work item 5, docs/design/2026-07-06-weak-match-
discrimination.md §7.3's last bullet): Sonnet's "13 candidates, suspiciously
constant across 5 probes" observation was traced (REPORT-slate-builder-s4b.md)
to a FIXED-PARAMETER artifact of the MCP-served response shape — default
``k=8`` code hits plus the memory block's fixed 5-entry shape (a 1-line
header + up to 3 kept + a 1-line elision notice, whenever recall's ``k=5``
exceeds the injection cap of 3) — NOT a measure of corpus richness. This
script's own :attr:`QueryCapture.pre_budget_pool_size` is immune to that
artifact: it is ``len(candidates)`` straight off ``store.hybrid_search``,
before the pipeline ever appends a memory block, a detail-miss notice, or an
elision trailer — a genuinely different (and honest) signal. It is still
recorded as EXPLORATORY only (its own pre-registered adoption rule is a later
task, per the design doc's §7.3 caution against post-hoc thresholds).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

# The percentile math is committed, unit-tested and pinned in token_survey.py;
# it lives beside this script in scripts/, not an installed package.
from loremaster.config import resolve_config_value, resolve_secret

# S4b audit finding #1 (REPORT-slate-audit-searchstore.md §Concern 6): the
# tokenizer, the verbatim-identifier-anchor detector, and the verdict-firing
# predicate are IMPORTED from production, never re-derived — a paraphrase is
# how the pre-registered ≤5%/≥60% bars silently drifted from measuring the
# rule production actually runs. `loremaster.search` is layering-reachable
# from scripts/ (this module already imports `loremaster.store.*` the same
# way), so the direct-import path applies, not the "extract a new seam"
# fallback.
from loremaster.search import (
    _cosine_absence_predicate as cosine_absence_verdict_fires,
)
from loremaster.search import (
    _has_verbatim_identifier_anchor as has_verbatim_identifier_anchor,
)
from loremaster.search import (
    _query_tokens as query_tokens,
)
from loremaster.store.candidate import Candidate
from loremaster.store.surreal import SurrealStore
from loresigil.base import Embedder
from loresigil.factory import BACKEND_TEI, EmbeddingConfig, make_embedder

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from token_survey import percentile  # noqa: E402  (path insert must precede the import)

# --------------------------------------------------------------------------- #
# Constants — no magic values
# --------------------------------------------------------------------------- #

#: The committed 35-pair eval set this survey mines for REAL, authentic
#: code-intent queries (see loremaster/EVALUATION.md).
DEFAULT_EVAL_XML: Path = (
    Path(__file__).resolve().parents[1] / "loremaster" / "evaluation.xml"
)

#: k / detail used for every survey call. All k=10 hits are captured (not
#: just the top one) per the design doc's Phase B instruction.
SURVEY_K: int = 10

QueryKind = Literal["real", "nonsense", "identifier", "implementation_vocabulary"]

#: The adversarial contrast set — deliberately absurd feature/technology
#: combinations that do not exist anywhere in this repository, so any
#: returned "hit" is necessarily a nearest-neighbor noise match, never a
#: genuine one. Fixed and deterministic (no randomness) so the survey is
#: reproducible run to run. Unchanged from the S4 survey.
NONSENSE_QUERIES: tuple[str, ...] = (
    "quantum blockchain kubernetes ingress rate limiter for photo uploads",
    "rate limiting middleware per client IP address",
    "GPU-accelerated video transcoding pipeline for livestream ingestion",
    "OAuth2 device-code flow for a smart refrigerator's firmware updater",
    "distributed consensus protocol for a fleet of autonomous drones",
    "real-time multiplayer game state synchronization over WebRTC",
    "e-commerce shopping cart abandonment email drip campaign scheduler",
    "biometric fingerprint authentication for a hotel room key card",
    "satellite telemetry decoder for weather balloon payload data",
    "cryptocurrency mining pool payout reconciliation ledger",
    "self-driving car lane-departure warning sensor fusion algorithm",
    "augmented reality furniture placement preview renderer",
    "airline seat upgrade bidding auction settlement engine",
    "smart thermostat HVAC scheduling machine learning model",
    "podcast transcript closed-caption timing alignment tool",
)

#: Informant-probe-style implementation-vocabulary queries (finding #74 fix,
#: docs/design/2026-07-06-client-needs-consult.md + docs/design/2026-07-06-
#: weak-match-discrimination.md): a query CLASS the eval.xml-mined REAL group
#: never samples — a natural-language DESCRIPTION of what a mechanism DOES
#: (informant/task-search phrasing: "enforce the search token budget and
#: build the elision notice..."), not a quiz-shaped "what is the exact name
#: of X" question. Finding #74's own live probe proved this class can
#: false-fire the absence verdict on a query the corpus genuinely answers —
#: the eval-question-shaped REAL group's 4.0% false-fire measurement was
#: therefore blind to this class, not a true measurement of it. Every member
#: below is sourced VERBATIM from a documented informant/tester probe (cited
#: per-entry), with its ground-truth target INDEPENDENTLY verified indexed
#: via lore_get_symbol/lore_search at remediation time (2026-07-07) — never
#: assumed. Deliberately a MIX of members that currently false-fire and ones
#: that currently don't (not cherry-picked to all fail), so the measured
#: false-fire rate over this group reflects the class honestly rather than a
#: manufactured 100%.
IMPLEMENTATION_VOCABULARY_QUERIES: tuple[str, ...] = (
    # Source: docs/design/2026-07-06-client-needs-consult.md:437 (Opus
    # informant) — THE #74 finding's own origin probe. Ground truth:
    # loremaster.server.AppContext._enforce_search_budget (server.py:1849) /
    # _search_elision_notice (server.py:1997) — both indexed, confirmed via
    # lore_get_symbol 2026-07-07 (top-hit sim 0.63 at that check — the score
    # had DRIFTED above the 0.5828 floor since the finding was filed, itself
    # evidence for the drift mechanism finding #74 names).
    "enforce the search token budget and build the elision notice naming elided hits",
    # Source: docs/design/2026-07-06-weak-match-discrimination.md §5 (Sonnet
    # informant, Probe 5). Ground truth: loremaster.search.SearchPipeline.
    # _apply_memory_boost (search.py:901); loremaster.memory.local.
    # LocalMemoryBackend.recall (memory/local.py:604) — confirmed indexed via
    # lore_get_symbol/lore_search 2026-07-07 (top-hit sim 0.64; no false-fire
    # observed at check time).
    "how does the memory store handle recall_memory ranking and boosting search results",
    # Source: docs/design/2026-07-06-weak-match-discrimination.md §4 (Opus
    # informant, Probe 2). Ground truth: loremaster.store.surreal.
    # SurrealStore.hybrid_search (store/surreal.py:1239) — confirmed indexed
    # via lore_get_symbol 2026-07-07. Live check 2026-07-07: false-FIRES
    # ("no confident match ... best hit similarity 0.55 ... nearest indexed:
    # 'FakeSurrealStore.hybrid_search'") — the real production method exists
    # but was elided from the shown response, exactly finding #74's shape.
    "reciprocal rank fusion search::rrf combine vector and lexical arms",
    # Source: REPORT-tester-sonnet.md §S3 (documented closure-test probe).
    # Ground truth: TestTokenBudgetCalibration (loremaster/tests/
    # test_map.py:1335), documenting the calibration constant CalibrationEngine
    # (loremaster/calibration/engine.py) serves — confirmed indexed via
    # lore_search 2026-07-07 (sim 0.55). Live check 2026-07-07: false-FIRES
    # against the 0.5828 floor, reproducibly.
    "what token budget calibration constant should I use for claude sonnet 5",
    # Source: docs/design/2026-07-06-client-needs-consult.md §7 (Opus
    # informant grounding calls). Ground truth: the embedding-resilience
    # retry/backoff wrapper (loresigil/loresigil/voyage_context.py's
    # ``_request_with_retry``/``_backoff``; loresigil/tests/
    # test_resilient.py, test_voyage_cloud.py) — confirmed indexed via
    # lore_search 2026-07-07 (top-hit sim 0.57; no false-fire observed at
    # check time — a near-boundary real answer).
    "retry/backoff for embedding requests",
    # Source: docs/design/2026-07-06-client-needs-consult.md §7 (Opus
    # informant grounding calls). Ground truth: loremaster.impact.
    # ImpactEngine._transitive_only_modules (impact.py:687) / the depth-2
    # transitive-rollup labeling contract (loremaster/tests/
    # test_impact.py:865) — confirmed indexed via lore_search 2026-07-07.
    # Live check 2026-07-07: false-FIRES ("no confident match ... nearest
    # indexed: 'TestDepthTwoTransitiveLabeling'") even though the real
    # production method is present in the SAME response at sim 0.47.
    "transitive ripple rollup for impact depth>1",
)

#: The number of identifier-shaped queries to deterministically sample from
#: the live corpus (design doc §6 Phase B: "NEW: 15 identifier-shaped real
#: queries").
IDENTIFIER_QUERY_COUNT: int = 15

#: The bound on how many chunk rows :func:`sample_identifier_queries` scrolls
#: to build its candidate identifier pool — generous headroom over this
#: repo's corpus size (a few hundred chunks), never unbounded.
IDENTIFIER_SCROLL_LIMIT: int = 20_000

#: D2 (docs/design/2026-07-06-weak-match-discrimination.md §7.2): the
#: pre-registered false-fire CEILING on the union of prose-real +
#: identifier-real queries — hedged-advisory wording mandatory, per the
#: operator ruling. Amending this after seeing the measured table would
#: un-pre-register the rule, so it is a named constant, not a CLI default a
#: run can quietly override.
D2_MAX_FALSE_FIRE_RATE: float = 0.05

#: D2's adoption bar: the aggregate absence verdict is adopted only if the
#: MAXIMUM-catch admissible floor catches at least this fraction of nonsense
#: queries (>= 9/15).
D2_MIN_NONSENSE_CATCH_RATE: float = 0.6

#: D1 (design doc §7.2): the always-on substrate ships only if within-query
#: cosine spread is genuinely informative — median spread across the REAL
#: groups (prose-real + identifier-real, never nonsense) at or above this bar.
D1_MIN_MEDIAN_SPREAD: float = 0.05

# --------------------------------------------------------------------------- #
# Live connection coordinates (this repo's lore.yaml) — hardcoded constants,
# mirroring scripts/snapshot_gc.py's OWN precedent for a narrow-purpose
# script: loremaster.config.load_config eagerly requires ANTHROPIC_API_KEY
# (a boot-time fail-fast unrelated to search/embedding), which a store+
# embedder-only script has no reason to depend on.
# --------------------------------------------------------------------------- #
DEFAULT_SURREAL_URL: str = "ws://127.0.0.1:18500/rpc"
DEFAULT_SURREAL_NAMESPACE: str = "lore"
DEFAULT_SURREAL_DATABASE: str = "lore"
DEFAULT_SURREAL_USER_ENV: str = "SURREAL_USER"
DEFAULT_SURREAL_PASSWORD_ENV: str = "SURREAL_PASS"
DEFAULT_EMBEDDING_DIM: int = 2048

#: TEI embedder coordinates (this repo's lore.yaml ``embedding:`` block).
DEFAULT_TEI_BASE_URL: str = "http://mbpsrv.firehawktransam.org:8080"
DEFAULT_TEI_MODEL: str = "voyageai/voyage-4-nano"
DEFAULT_TEI_API_KEY_ENV: str = "LORE_TEI_KEY"
DEFAULT_TEI_QUERY_PROMPT_NAME: str = "query"
DEFAULT_TEI_DOCUMENT_PROMPT_NAME: str = "document"

# The chunk payload key an identity/query-token check reads (mirrors
# loremaster.search's own ``_PAYLOAD_IDENT_TEXT``-shaped constants).
_PAYLOAD_IDENT_TEXT = "ident_text"
_PAYLOAD_FILE_PATH = "file_path"
_PAYLOAD_IDENTITY = "identity"


# --------------------------------------------------------------------------- #
# Pure core — eval mining, corpus sampling, per-hit aggregation.
# --------------------------------------------------------------------------- #
def parse_eval_questions(xml_path: Path) -> list[str]:
    """Extract every ``<question>`` text from the 35-pair eval XML, in order.

    Args:
        xml_path: Path to an eval file shaped like ``loremaster/evaluation.xml``
            (a root ``<evaluation>`` of ``<qa_pair><question>...</question>
            <answer>...</answer></qa_pair>`` elements).

    Returns:
        The stripped question text of every ``qa_pair`` that has one, in
        document order.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    questions: list[str] = []
    for qa_pair in root.findall(".//qa_pair"):
        question_elem = qa_pair.find("question")
        if question_elem is not None and question_elem.text:
            questions.append(question_elem.text.strip())
    return questions


def every_nth(items: Sequence[str], count: int) -> list[str]:
    """Deterministically sample ``count`` items from ``items``, spread evenly.

    The design doc's exact phrasing (§6 Phase B): "sorted qualified names,
    every Nth" — a fixed, reproducible sampling rule (no randomness), so two
    survey runs against the same corpus draw the SAME identifier set.

    Args:
        items: The (already sorted) candidate pool.
        count: The number of items to return.

    Returns:
        ``items`` unchanged if it already has ``count`` or fewer entries;
        otherwise exactly ``count`` items, evenly spread across the pool
        (index ``int(i * len(items) / count)`` — floor, not rounded — for
        ``i`` in ``range(count)``). Either way the sampling stays
        deterministic; only the docstring's formula was previously wrong
        (S4b audit finding #5).
    """
    if not items or len(items) <= count:
        return list(items)
    step = len(items) / count
    return [items[int(i * step)] for i in range(count)]


# query_tokens / has_verbatim_identifier_anchor are IMPORTED from
# loremaster.search above (S4b audit finding #1) — no local re-derivation.
# Both names are re-exported at module scope under this module's own public
# names (rather than re-defined) so this is the SAME function object
# production's ``_cosine_absence_verdict`` runs, pinned by an identity
# (``is``) test in ``test_search_score_survey.py``'s
# ``TestPredicateParityWithProduction`` — never a copy that can drift.
#
# D3 fix (2026-07-06): ``has_verbatim_identifier_anchor`` now absorbs its own
# query-side tokenization internally (:func:`loremaster.search.
# _identifier_shaped_query_tokens`), so ``capture_query`` forwards the raw
# query text directly and no longer calls ``query_tokens`` itself.
# ``query_tokens`` stays imported + re-exported + parity-pinned (still a
# real, unchanged production function, used internally on the ident_text
# side) for any future direct caller; ``__all__`` below keeps that
# now-internal-only re-export from reading as an unused import.
#
# ⚠ ``__all__`` NAMES ALL THREE, NOT JUST ``query_tokens`` (#188, 2026-07-29).
# Under mypy's ``no_implicit_reexport`` (part of ``strict``) an aliased import
# — ``_x as y`` — is NOT an export, so ``test_search_score_survey.py``'s six
# ``sss.<name>`` reads were ``attr-defined`` errors for the two names this list
# omitted. They were always as public as ``query_tokens``: the comment above
# says all three are re-exported, and ``TestPredicateParityWithProduction``
# pins all three by identity. The list was narrow only because it had been
# written for ruff's unused-import rule, which the other two did not trip.
# ``__all__`` affects ``import *`` alone, so this changes no runtime behaviour.
__all__ = [
    "cosine_absence_verdict_fires",
    "has_verbatim_identifier_anchor",
    "query_tokens",
]


@dataclass(frozen=True)
class HitCapture:
    """One fused hit's captured signals — every pre-fusion magnitude the
    design doc's Phase B/C measurement protocol needs, not just the top hit.

    Attributes:
        fused_score: The RRF-fused score (S4's original, rank-fusion-coded
            signal — kept for continuity/audit, never the discriminator).
        vector_cosine: The raw pre-fusion query<->chunk cosine, or ``None``
            if the store never projected it (see :class:`Candidate`).
        file_path: The hit's source file (source-concentration input).
        ident_text: The hit's identifier text (the verbatim-anchor channel).
        origin: Which retrieval arm produced the hit.
    """

    fused_score: float
    vector_cosine: float | None
    file_path: str
    ident_text: str
    origin: str


def _to_hit_capture(candidate: Candidate) -> HitCapture:
    """Build one :class:`HitCapture` from a live :class:`Candidate`."""
    return HitCapture(
        fused_score=candidate.score,
        vector_cosine=candidate.vector_cosine,
        file_path=str(candidate.payload.get(_PAYLOAD_FILE_PATH, "")),
        ident_text=str(candidate.payload.get(_PAYLOAD_IDENT_TEXT, "")),
        origin=candidate.origin,
    )


@dataclass(frozen=True)
class QueryCapture:
    """One surveyed query's full per-hit capture (not just its top score).

    Attributes:
        query: The query text actually sent.
        query_kind: Which of the three groups this query belongs to.
        hits: Every captured hit, in the store's own fused order.
        pre_budget_pool_size: ``len(hits)`` straight off ``hybrid_search`` —
            see the module docstring's constant-13 verdict for why this is
            immune to the old MCP-observed artifact. EXPLORATORY only.
        has_verbatim_anchor: True iff ANY hit's ``ident_text`` carries a
            verbatim token from ``query`` (the D3 carve-out channel).
    """

    query: str
    query_kind: QueryKind
    hits: tuple[HitCapture, ...]
    pre_budget_pool_size: int
    has_verbatim_anchor: bool


def top_hit_cosine(hits: Sequence[HitCapture]) -> float | None:
    """The FUSED-ORDER TOP hit's cosine, or ``None`` if it has none/there are no hits."""
    if not hits:
        return None
    return hits[0].vector_cosine


def max_cosine_of_response(hits: Sequence[HitCapture]) -> float | None:
    """The MAXIMUM cosine among all captured hits, or ``None`` if none carry one.

    Deliberately NOT the top-fused-hit's cosine (design doc §2's C1-aggregate
    note): the list is ordered by fused score, and a cosine-STRONG hit can sit
    below a cosine-weak one — the absence verdict must check the best shown
    cosine, not the first one.
    """
    cosines = [hit.vector_cosine for hit in hits if hit.vector_cosine is not None]
    return max(cosines) if cosines else None


def fused_top_margin(hits: Sequence[HitCapture]) -> float | None:
    """The fused-score gap between the top and second hit, or ``None`` if <2 hits.

    Settles C3 with data (design doc §6): expected to be UNINFORMATIVE (Opus's
    live probes already showed it inverted — a nonsense query's margin 2.8x
    the real one) — captured for completeness, never built on without its own
    re-derivation.
    """
    if len(hits) < 2:
        return None
    return hits[0].fused_score - hits[1].fused_score


def within_query_cosine_spread(hits: Sequence[HitCapture]) -> float | None:
    """The max-min cosine spread across ``hits``, or ``None`` if <2 have one.

    Gates the D1 always-on substrate (design doc §7.2): a flat spread
    (every hit ~equally (dis)similar regardless of query) means the number
    carries no relative-shape signal even before any cross-query floor is set.
    """
    cosines = [hit.vector_cosine for hit in hits if hit.vector_cosine is not None]
    if len(cosines) < 2:
        return None
    return max(cosines) - min(cosines)


def source_concentration(hits: Sequence[HitCapture]) -> int:
    """The count of DISTINCT source files among ``hits`` (Sonnet's exploratory
    signal, §7.3: many independent files converging vs. one file monopolizing
    the list). ``0`` for an empty response."""
    return len({hit.file_path for hit in hits})


@dataclass(frozen=True)
class GroupCosineSummary:
    """Percentile statistics for one query-kind group's cosine distributions."""

    label: str
    n: int
    n_with_cosine: int
    top_hit_mean: float
    top_hit_median: float
    top_hit_p5: float
    top_hit_p95: float
    max_response_mean: float
    max_response_median: float
    max_response_p5: float
    max_response_p95: float


def summarize_cosine_group(
    captures: Sequence[QueryCapture], *, label: str
) -> GroupCosineSummary:
    """Aggregate top-hit-cosine AND max-cosine-of-response percentiles for one group.

    Raises:
        ValueError: ``captures`` is empty, or none of them ever captured a
            cosine value (nothing to summarize).
    """
    if not captures:
        raise ValueError(f"cannot summarize an empty capture set ({label!r})")
    top_scores = [
        s for c in captures if (s := top_hit_cosine(c.hits)) is not None
    ]
    max_scores = [
        s for c in captures if (s := max_cosine_of_response(c.hits)) is not None
    ]
    if not top_scores or not max_scores:
        raise ValueError(
            f"{label!r} group has no cosine-bearing measurements to summarize "
            f"(0 of {len(captures)} queries captured a vector_cosine)"
        )
    return GroupCosineSummary(
        label=label,
        n=len(captures),
        n_with_cosine=len(top_scores),
        top_hit_mean=statistics.fmean(top_scores),
        top_hit_median=percentile(top_scores, 50.0),
        top_hit_p5=percentile(top_scores, 5.0),
        top_hit_p95=percentile(top_scores, 95.0),
        max_response_mean=statistics.fmean(max_scores),
        max_response_median=percentile(max_scores, 50.0),
        max_response_p5=percentile(max_scores, 5.0),
        max_response_p95=percentile(max_scores, 95.0),
    )


@dataclass(frozen=True)
class VerdictSample:
    """One query's ``(max_cosine_of_response, has_verbatim_anchor)`` pair —

    the EXACT two signals :func:`loremaster.search._cosine_absence_predicate`
    (imported here as :func:`cosine_absence_verdict_fires`) consumes to decide
    whether the aggregate absence verdict fires for that query. D2's floor
    selection scores admissibility/catch against THIS predicate, never a bare
    cosine-vs-floor comparison (S4b audit finding #1) — a query the
    production verdict would never fire on (an anchored identifier lookup)
    must never count as a false-fire OR a catch, regardless of its cosine.
    """

    max_cosine: float
    has_verbatim_anchor: bool


def query_capture_to_verdict_sample(capture: QueryCapture) -> VerdictSample | None:
    """Build one :class:`VerdictSample` from a :class:`QueryCapture`.

    Returns:
        ``None`` if the capture has no cosine-bearing hit at all (mirrors
        production's own "no cosines -> the verdict cannot evaluate" branch,
        :func:`loremaster.search._cosine_absence_verdict`); otherwise the
        capture's max-cosine-of-response paired with its already-captured
        verbatim-anchor flag.
    """
    max_cosine = max_cosine_of_response(capture.hits)
    if max_cosine is None:
        return None
    return VerdictSample(max_cosine=max_cosine, has_verbatim_anchor=capture.has_verbatim_anchor)


@dataclass(frozen=True)
class CosineFloorRecommendation:
    """D2's max-catch admissible cosine floor (or the absence of one)."""

    floor: float
    false_fire_rate: float
    nonsense_catch_rate: float
    n_union: int
    n_nonsense: int

    def meets_adoption_bar(self, *, min_catch: float = D2_MIN_NONSENSE_CATCH_RATE) -> bool:
        """D2's adoption gate: catch >= the pre-registered bar (>= 9/15 = 0.6)."""
        return self.nonsense_catch_rate >= min_catch


def choose_cosine_floor(
    real_query_samples: Sequence[VerdictSample],
    nonsense_samples: Sequence[VerdictSample],
    *,
    max_false_fire_rate: float = D2_MAX_FALSE_FIRE_RATE,
) -> CosineFloorRecommendation:
    """D2 (design doc §7.2, precision-first): the MAX-CATCH floor admissible
    at ``max_false_fire_rate`` false-fire on the UNION of prose-real +
    identifier-real + implementation-vocabulary-real samples (finding #74
    widened this from a 2-way to a 3-way union — see
    :data:`IMPLEMENTATION_VOCABULARY_QUERIES`'s module-level docstring for
    why the eval-question-shaped prose-real group alone under-measures the
    false-fire rate).

    Both "false-fire" and "catch" are scored by
    :func:`cosine_absence_verdict_fires` — the IDENTICAL predicate
    production's aggregate absence verdict runs (``max_cosine < floor AND not
    has_verbatim_anchor``, S4b audit finding #1) — never a bare
    ``cosine < floor`` comparison, so a query the production verdict would
    never fire on (a verbatim-identifier anchor present) never counts as
    either a false-fire or a catch, no matter how low its cosine is.

    Candidate floors are exactly the union's own OBSERVED ``max_cosine``
    values (a floor strictly between two observed values changes neither
    rate — the same nearest-rank discipline :func:`token_survey.percentile`
    uses).

    Dominance ordering (operator/lead ruling, finding #74 widened re-run,
    2026-07-07 — supersedes the prior "largest admissible floor" shortcut):
    among ADMISSIBLE floors (false-fire <= ``max_false_fire_rate``), prefer,
    in order:

    1. **Maximum catch** — D2's own adoption criterion.
    2. **Minimum false-fire** — D2's precision-first name. Catch can genuinely
       TIE across many admissible floors (catch only changes where a floor
       crosses a NONSENSE sample's value, and candidate floors are drawn from
       the REAL/union samples — usually distinct values), while a naive
       "first admissible floor scanning from the top" can stop at a HIGHER
       floor with strictly MORE false-fire than a lower floor that achieves
       the identical catch (the live receipt: floor 0.5370 at 3.6% false-fire
       vs. floor 0.5065 at a strictly lower rate, both 100% catch — see
       ``docs/design`` / the finding #74 closure record for the exact
       numbers). The prior version of this function returned the dominated
       (higher-false-fire) floor because it stopped at the first admissible
       candidate scanning top-down, never comparing it against a lower one
       that ties on catch — fixed here by scoring EVERY admissible candidate
       before choosing.
    3. **Maximum floor** — the final tie-break, for the (rarer) case where
       BOTH catch and false-fire tie across two floors. This happens when a
       verbatim-identifier anchor (D3) exempts the only sample that would
       otherwise separate two candidates' false-fire counts (an anchored
       sample contributes a constant zero regardless of floor). Grounds the
       choice in the largest defensible OBSERVED value, never an arbitrary
       lower one within a genuine tie.

    A recommendation ALWAYS exists (never ``None``): at the lowest observed
    ``max_cosine``, no sample's cosine is STRICTLY below it, so false-fire is
    always 0 there regardless of anchors — always admissible in the worst
    case. The real decision point is whether the returned recommendation
    clears the SEPARATE adoption bar — see
    :meth:`CosineFloorRecommendation.meets_adoption_bar` (D2's "no admissible
    floor catches >= 60%" branch in the design doc is about the CATCH bar,
    not floor admissibility itself).

    Args:
        real_query_samples: Samples pooled from EVERY "should be answered"
            query group — prose-real, identifier-real, and (finding #74)
            implementation-vocabulary-real — never any one group alone.
        nonsense_samples: Samples from the adversarial group.
        max_false_fire_rate: The pre-registered ceiling (default
            :data:`D2_MAX_FALSE_FIRE_RATE` — amending it after seeing the
            table un-pre-registers the rule; a caller doing that must say so).

    Returns:
        The dominance-ordered admissible recommendation (see above).

    Raises:
        ValueError: Either sequence is empty.
    """
    if not real_query_samples:
        raise ValueError("real_query_samples must be non-empty")
    if not nonsense_samples:
        raise ValueError("nonsense_samples must be non-empty")
    n_union = len(real_query_samples)
    n_nonsense = len(nonsense_samples)
    candidate_floors = sorted({s.max_cosine for s in real_query_samples}, reverse=True)

    # Score EVERY admissible candidate (never stop at the first pass) — see
    # the docstring's dominance-ordering rationale for why an early return on
    # the first admissible (highest) floor can silently pick a DOMINATED one.
    admissible: list[tuple[float, float, float]] = []  # (floor, false_fire_rate, catch_rate)
    for floor in candidate_floors:
        false_fire_rate = (
            sum(
                1 for s in real_query_samples
                if cosine_absence_verdict_fires(s.max_cosine, floor, s.has_verbatim_anchor)
            )
            / n_union
        )
        if false_fire_rate <= max_false_fire_rate:
            catch = sum(
                1 for s in nonsense_samples
                if cosine_absence_verdict_fires(s.max_cosine, floor, s.has_verbatim_anchor)
            )
            admissible.append((floor, false_fire_rate, catch / n_nonsense))

    if not admissible:
        # Unreachable in practice (the minimum candidate is always admissible
        # — see the docstring), but keeps the function total rather than
        # assuming.
        raise AssertionError(
            "no admissible floor found — the minimum candidate should always qualify"
        )

    # Dominance order: maximize catch, THEN minimize false-fire (maximize its
    # negation), THEN maximize the floor itself.
    best_floor, best_false_fire_rate, best_catch_rate = max(
        admissible, key=lambda entry: (entry[2], -entry[1], entry[0])
    )
    return CosineFloorRecommendation(
        floor=best_floor,
        false_fire_rate=best_false_fire_rate,
        nonsense_catch_rate=best_catch_rate,
        n_union=n_union,
        n_nonsense=n_nonsense,
    )


def substrate_gate_passes(
    within_query_spreads: Sequence[float], *, min_median_spread: float = D1_MIN_MEDIAN_SPREAD
) -> bool:
    """D1 (design doc §7.2): the always-on substrate ships iff the MEDIAN
    within-query cosine spread across the real groups is at/above
    ``min_median_spread``. ``False`` on an empty sequence (nothing measured
    yet — never assume the gate passes)."""
    if not within_query_spreads:
        return False
    return percentile(list(within_query_spreads), 50.0) >= min_median_spread


# --------------------------------------------------------------------------- #
# Live client — direct store + embedder connection (network surface,
# test-exempt; see the module docstring for why this bypasses the MCP tool).
# --------------------------------------------------------------------------- #
def _make_store() -> SurrealStore:
    return SurrealStore(
        url=DEFAULT_SURREAL_URL,
        namespace=DEFAULT_SURREAL_NAMESPACE,
        database=DEFAULT_SURREAL_DATABASE,
        dim=DEFAULT_EMBEDDING_DIM,
        # The USERNAME is not a secret and the SDK needs a real ``str`` on the
        # wire: a ``SecretStr`` here raises ``BufferError: no encoder for type
        # SecretStr`` at signin (#211 / cold-audit Defect A). ``signin_credentials``
        # deliberately unwraps only the password, so the username is read as a plain
        # config value (#226) at this and the other four former round-trip sites.
        user=resolve_config_value(DEFAULT_SURREAL_USER_ENV),
        password=resolve_secret(DEFAULT_SURREAL_PASSWORD_ENV),
    )


def _make_embedder() -> Embedder:
    # ⚠ THIS IS A COMPOSITION ROOT (#233 / ruling R31). It builds the loresigil
    # config DIRECTLY rather than through ``loremaster.embedding.to_loresigil_config``,
    # so it is one of only two production construction sites of that model — and the
    # one no type gate can see, because ``scripts/`` is not a typecheck member. The
    # credential is therefore resolved HERE, by the shared resolver, and arrives
    # already wrapped: ``loresigil`` reads no environment variable (#222).
    config = EmbeddingConfig(
        # ⚠ THE CAST IS A WORKAROUND FOR AN UPSTREAM ANNOTATION, NOT A SILENCER (#188,
        # 2026-07-29). ``loresigil.factory`` declares ``BACKEND_TEI: str = "tei"`` — an
        # explicit ``str`` that WIDENS away from ``EmbeddingConfig.backend``'s
        # ``Literal["tei", "voyage-cloud", "voyage-context"]``, so passing the constant
        # is an ``arg-type`` error. The constants' own comment there says they are
        # "kept as constants so dispatch and the schema agree"; at type level they do
        # not. The real fix is upstream — annotate the three discriminators
        # ``Literal[...]`` in ``loresigil/loresigil/factory.py`` — which was outside
        # packet 44's writable set; DELETE THIS CAST the day that lands. The VALUE still
        # comes from the constant, so a renamed backend is still a one-place change.
        backend=cast(Literal["tei"], BACKEND_TEI),
        api_key=resolve_secret(DEFAULT_TEI_API_KEY_ENV),
        base_url=DEFAULT_TEI_BASE_URL,
        model=DEFAULT_TEI_MODEL,
        dim=DEFAULT_EMBEDDING_DIM,
        query_prompt_name=DEFAULT_TEI_QUERY_PROMPT_NAME,
        document_prompt_name=DEFAULT_TEI_DOCUMENT_PROMPT_NAME,
    )
    return make_embedder(config)


async def sample_identifier_queries(
    store: SurrealStore, *, count: int = IDENTIFIER_QUERY_COUNT, scroll_limit: int = IDENTIFIER_SCROLL_LIMIT
) -> list[str]:
    """Deterministically sample ``count`` exact symbol names off the live corpus.

    Scrolls up to ``scroll_limit`` chunk rows (unfiltered), collects every
    DISTINCT non-empty ``identity``, sorts them, and applies :func:`every_nth`
    — the design doc's exact "sorted qualified names, every Nth" rule.
    """
    rows = await store.scroll({}, limit=scroll_limit)
    identities = sorted({str(row[_PAYLOAD_IDENTITY]) for row in rows if row.get(_PAYLOAD_IDENTITY)})
    return every_nth(identities, count)


async def capture_query(store: SurrealStore, embedder, query: str, query_kind: QueryKind) -> QueryCapture:  # type: ignore[no-untyped-def]
    """Run ``query`` against the live store + embedder and capture every hit.

    The FULL, untruncated query text is sent to BOTH arms — the store's own
    internal lexical-arm bounding (finding #66/#67/#69, ``store.surreal.
    _MAX_LEXICAL_QUERY_CHARS``/``_MAX_QUERY_TOKENS``) now handles an
    arbitrarily long query safely, so this survey no longer needs its own
    truncation workaround (the S4 survey's ``MAX_QUERY_CHARS`` is retired).
    """
    vector = await embedder.embed_query(query)
    candidates = await store.hybrid_search(query_vector=vector, query_text=query, k=SURVEY_K)
    hits = tuple(_to_hit_capture(c) for c in candidates)
    has_anchor = any(has_verbatim_identifier_anchor(query, hit.ident_text) for hit in hits)
    return QueryCapture(
        query=query,
        query_kind=query_kind,
        hits=hits,
        pre_budget_pool_size=len(candidates),
        has_verbatim_anchor=has_anchor,
    )


async def survey(
    real_questions: Sequence[str], nonsense_questions: Sequence[str]
) -> list[QueryCapture]:
    """Capture every real + identifier + implementation-vocabulary + nonsense
    query against the live server.

    READ-ONLY end to end (S4b audit finding #2, REPORT-slate-audit-
    searchstore.md §Concern 6): this never calls ``store.ensure_ready()`` (a
    schema-DDL ``BEGIN…COMMIT`` WRITE transaction) — ``scroll``/
    ``hybrid_search`` reach the store via ``_ensure_connection`` alone,
    mirroring ``scripts/snapshot_gc.py``'s own read-store precedent (its read
    store is deliberately never ``ensure_ready``-ed either).
    """
    store = _make_store()
    embedder = _make_embedder()
    try:
        identifier_queries = await sample_identifier_queries(store)
        captures: list[QueryCapture] = []
        for kind, questions in (
            ("real", real_questions),
            ("identifier", identifier_queries),
            ("implementation_vocabulary", IMPLEMENTATION_VOCABULARY_QUERIES),
            ("nonsense", nonsense_questions),
        ):
            for question in questions:
                captures.append(await capture_query(store, embedder, question, kind))  # type: ignore[arg-type]
        return captures
    finally:
        await store.close()


# --------------------------------------------------------------------------- #
# Report rendering
# --------------------------------------------------------------------------- #
def build_markdown_report(
    captures: Sequence[QueryCapture],
    real_summary: GroupCosineSummary,
    identifier_summary: GroupCosineSummary,
    implementation_vocabulary_summary: GroupCosineSummary,
    nonsense_summary: GroupCosineSummary,
    substrate_gate: bool,
    floor_recommendation: CosineFloorRecommendation,
) -> str:
    """Render the human-readable Phase B/C survey report."""
    lines: list[str] = ["# Search-Score Survey — S4b cosine substrate + absence verdict", ""]

    lines.append("## D1 — substrate gate (always-on per-hit magnitude)")
    lines.append("")
    lines.append(
        f"**{'PASSES' if substrate_gate else 'DOES NOT PASS'}** — median within-query cosine "
        f"spread across the real groups vs. the {D1_MIN_MEDIAN_SPREAD:.2f} bar."
    )
    lines.append("")

    lines.append("## D2 — verdict floor (gated absence verdict)")
    lines.append("")
    adopt = floor_recommendation.meets_adoption_bar()
    lines.append(
        f"**floor = {floor_recommendation.floor:.4f}** — false-fire "
        f"{floor_recommendation.false_fire_rate * 100:.1f}% on "
        f"{floor_recommendation.n_union} real+identifier+implementation-vocabulary "
        f"queries; nonsense catch "
        f"{floor_recommendation.nonsense_catch_rate * 100:.1f}% "
        f"({round(floor_recommendation.nonsense_catch_rate * floor_recommendation.n_nonsense)}/"
        f"{floor_recommendation.n_nonsense})."
    )
    lines.append("")
    lines.append(
        f"**{'ADOPT' if adopt else 'DO NOT ADOPT — C7-as-amended: retire the aspiration, teach instead'}** "
        f"— catch vs. the {D2_MIN_NONSENSE_CATCH_RATE * 100:.0f}% bar (>= 9/15)."
    )
    lines.append("")

    def summary_row(summary: GroupCosineSummary) -> str:
        return (
            f"| {summary.label} | {summary.n} | {summary.n_with_cosine} "
            f"| {summary.top_hit_mean:.4f} | {summary.top_hit_median:.4f} "
            f"| {summary.top_hit_p5:.4f} | {summary.top_hit_p95:.4f} "
            f"| {summary.max_response_mean:.4f} | {summary.max_response_median:.4f} "
            f"| {summary.max_response_p5:.4f} | {summary.max_response_p95:.4f} |"
        )

    lines.append("## Cosine distributions (top-hit AND max-of-response)")
    lines.append("")
    lines.append(
        "| group | n | n w/ cosine | top mean | top median | top p5 | top p95 "
        "| max mean | max median | max p5 | max p95 |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    lines.append(summary_row(real_summary))
    lines.append(summary_row(identifier_summary))
    lines.append(summary_row(implementation_vocabulary_summary))
    lines.append(summary_row(nonsense_summary))
    lines.append("")

    lines.append("## Exploratory signals (own pre-registered adoption rule required — §7.3)")
    lines.append("")
    lines.append(
        "- `pre_budget_pool_size` is measured DIRECTLY off `store.hybrid_search` "
        "(never inflated by the pipeline's memory-block/notice additions the old "
        "MCP-observed \"13\" conflated — see REPORT-slate-builder-s4b.md's "
        "constant-13 verdict). Still exploratory: no adoption rule is pre-registered."
    )
    lines.append("- `source_concentration` (distinct files among shown hits) — exploratory.")
    lines.append("- `fused_top_margin` — settled by Opus's live probes as INVERTED; captured "
                  "for completeness only, never built on.")
    lines.append("")

    lines.append("## Per-query detail")
    lines.append("")
    lines.append("| kind | top cosine | max cosine | pool size | verbatim anchor | query |")
    lines.append("|---|---|---|---|---|---|")
    for c in captures:
        top = top_hit_cosine(c.hits)
        mx = max_cosine_of_response(c.hits)
        top_str = f"{top:.4f}" if top is not None else "(none)"
        max_str = f"{mx:.4f}" if mx is not None else "(none)"
        lines.append(
            f"| {c.query_kind} | {top_str} | {max_str} | {c.pre_budget_pool_size} "
            f"| {c.has_verbatim_anchor} | {c.query} |"
        )
    lines.append("")
    return "\n".join(lines)


def _write_jsonl(path: Path, captures: Sequence[QueryCapture]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for c in captures:
            handle.write(
                json.dumps(
                    {
                        "query": c.query,
                        "query_kind": c.query_kind,
                        "pre_budget_pool_size": c.pre_budget_pool_size,
                        "has_verbatim_anchor": c.has_verbatim_anchor,
                        "hits": [
                            {
                                "fused_score": h.fused_score,
                                "vector_cosine": h.vector_cosine,
                                "file_path": h.file_path,
                                "origin": h.origin,
                            }
                            for h in c.hits
                        ],
                    }
                )
                + "\n"
            )


def _default_output_dir() -> Path:
    scratch = os.environ.get("SEARCH_SCORE_SURVEY_OUT")
    if scratch:
        return Path(scratch)
    return Path.cwd() / "search_score_survey_out"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search-score survey — measures the S4b cosine substrate + verdict floor."
    )
    parser.add_argument("--eval-xml", type=Path, default=DEFAULT_EVAL_XML)
    parser.add_argument("--out-dir", type=Path, default=_default_output_dir())
    parser.add_argument("--summary-filename", default="search_score_survey_summary.md")
    parser.add_argument("--jsonl-filename", default="search_score_survey.jsonl")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    real_questions = parse_eval_questions(args.eval_xml)
    print(f"Loaded {len(real_questions)} real queries from {args.eval_xml}", file=sys.stderr)
    print(f"Using {len(NONSENSE_QUERIES)} nonsense queries (fixed set)", file=sys.stderr)

    captures = asyncio.run(survey(real_questions, NONSENSE_QUERIES))

    real_captures = [c for c in captures if c.query_kind == "real"]
    identifier_captures = [c for c in captures if c.query_kind == "identifier"]
    implementation_vocabulary_captures = [
        c for c in captures if c.query_kind == "implementation_vocabulary"
    ]
    nonsense_captures = [c for c in captures if c.query_kind == "nonsense"]

    real_summary = summarize_cosine_group(real_captures, label="real")
    identifier_summary = summarize_cosine_group(identifier_captures, label="identifier")
    implementation_vocabulary_summary = summarize_cosine_group(
        implementation_vocabulary_captures, label="implementation_vocabulary"
    )
    nonsense_summary = summarize_cosine_group(nonsense_captures, label="nonsense")

    # D1 (finding #74): the "real groups" whose spread gates the always-on
    # substrate now include implementation-vocabulary alongside prose-real +
    # identifier-real — it IS a third real (should-be-answered) group, never
    # nonsense.
    real_group_spreads = [
        s for c in (*real_captures, *identifier_captures, *implementation_vocabulary_captures)
        if (s := within_query_cosine_spread(c.hits)) is not None
    ]
    substrate_gate = substrate_gate_passes(real_group_spreads)

    # S4b audit finding #1: the floor selection scores VerdictSamples (max
    # cosine + verbatim-anchor flag) — the EXACT signals the production
    # predicate consumes — never bare top-hit cosines. (Named distinctly from
    # ``s`` above: the walrus target escapes its comprehension into this
    # function's scope, and reusing ``s`` for a differently-typed value here
    # would confuse mypy across the two bindings.) Finding #74: the union now
    # pools THREE "should be answered" groups, not two — prose-real +
    # identifier-real + implementation-vocabulary-real — so the admissibility
    # rule's false-fire ceiling is measured against the class that actually
    # broke (docs/design comment on IMPLEMENTATION_VOCABULARY_QUERIES).
    union_samples = [
        sample
        for c in (*real_captures, *identifier_captures, *implementation_vocabulary_captures)
        if (sample := query_capture_to_verdict_sample(c)) is not None
    ]
    nonsense_samples = [
        sample for c in nonsense_captures
        if (sample := query_capture_to_verdict_sample(c)) is not None
    ]
    floor_recommendation = choose_cosine_floor(union_samples, nonsense_samples)

    report = build_markdown_report(
        captures, real_summary, identifier_summary, implementation_vocabulary_summary,
        nonsense_summary, substrate_gate, floor_recommendation,
    )
    summary_path = args.out_dir / args.summary_filename
    summary_path.write_text(report, encoding="utf-8")
    _write_jsonl(args.out_dir / args.jsonl_filename, captures)

    print(f"Summary written to {summary_path}", file=sys.stderr)
    print(f"D1 substrate gate: {'PASSES' if substrate_gate else 'DOES NOT PASS'}", file=sys.stderr)
    print(
        f"D2 recommended floor = {floor_recommendation.floor:.4f} "
        f"(catch {floor_recommendation.nonsense_catch_rate * 100:.1f}%, "
        f"adopt={floor_recommendation.meets_adoption_bar()})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
