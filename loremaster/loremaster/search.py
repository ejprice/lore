"""The query-time search pipeline — the engine behind the ``search_code`` tool.

:class:`SearchPipeline` is the read side of lore. It is OOP and fully
dependency-injected (the unified SurrealDB store, the embedder, the composed
:class:`~loremaster.server.LoreServer` that resolves the extension hooks, the
manifest, the code graph, an optional
:class:`~loremaster.memory.backend.MemoryBackend`, an optional config-gated reranker
seam, and the config), so a test wires the in-memory
:func:`~_surreal_fakes.fake_surreal_trio` + a :class:`~loresigil.testing.FakeEmbedder`
while the live server wires the deployed SurrealDB / embedder resources.

**P6 read-path cutover (plan §6).** The pipeline reads from the unified store's
:meth:`~loremaster.store.surreal.SurrealStore.hybrid_search` (an HNSW vector arm
⊕ a BM25 FULLTEXT arm fused with Reciprocal Rank Fusion), which returns
backend-neutral :class:`~loremaster.store.candidate.Candidate`\\ s (``key`` = bare
uuid5, ``score`` = RRF-scale < 1.0, ``payload`` = the flattened canonical chunk
fields incl. the chunker's ``signature``) — never a raw vector-store point type
(a ``ScoredPoint``-style object). The read result is a list of summarised :class:`SearchResult`
value objects, never a raw candidate dump (the Anthropic token-efficiency rule).

The v2 pipeline for one ``search_code(query, k, filters, wait_for_fresh,
detail_level)`` call:

1. **(bounded) ``wait_for_fresh``** — when set, poll the manifest for the
   in-flight files matching the query's ``path``/``file_path`` filter until they
   reach ``indexed`` OR a hard timeout elapses. ALWAYS bounded: on timeout the
   search proceeds and serves the stale content *with a warning* — it never hangs
   (the embedder can be slow or down).
2. **Embed the query** via :meth:`~loresigil.base.Embedder.embed_query` for the
   HNSW arm; the RAW query text is forwarded UNCHANGED for the BM25 arm (dropping
   it, or sending the vector/prompt text, is the classic seam bug this closes).
3. **Hybrid search** — ``store.hybrid_search(query_vector, query_text, k,
   filters)`` returns the RRF-fused :class:`Candidate`\\ s, optionally
   payload-filtered (tier / file_path) server-side. A down store RAISES here
   (never a silent ``[]``); the public ``path`` alias is translated to the
   canonical ``file_path`` before the query.
4. **Extension search-pipeline hook (seam 4 / C3)** — ``augment_candidates`` (an
   extension may inject extra candidates) THEN ``rerank`` (an extension may
   reorder/rescore). Both are the identity for the bare generic server.
5. **Memory (generic)** — recall project memory once, then (a) *boost*: any
   candidate a recalled memory references is lifted by :data:`_MEMORY_BOOST` (an
   RRF-scale-aware constant, so a remembered correction reliably overtakes an
   unboosted hit) and the candidates re-sorted; and (b) *inject*: the ≤
   :data:`_MEMORY_INJECTION_CAP` top-scored recalled memories are rendered as
   VISIBLE, provenance-stamped entries, distinct from the silent boost and NEVER
   masquerading as source citations — segregated behind a TRAILING ``memories:``
   section header (P8d' #54 tweak T3: memory noise was crowding out code hits
   under a tight response budget), with a counted elision notice when recall
   found more matching memories than the cap. No memory store ⇒ all of this is
   inert.
6. **Config-gated reranker seam (item 9)** — when ``search.reranker`` is
   configured AND a reranker seam object is injected, the candidates pass through
   it AFTER RRF fusion and BEFORE formatting. Config, not the mere presence of the
   seam object, is the gate.
7. **Format (seam 5) + graph enrichment + freshness** — the extension
   ``format_result`` wins if it claims the result; otherwise the base default
   citation: ``[SOURCE:<file>:<line>]`` + a stable ``Key:`` line + the v2 short
   citation ``[S:<tier>:<path>:<start>-<end>@<hash6>]`` + a fenced source block.
   A function/method hit (non-``None`` ``signature``) additionally carries its
   ref-join line (``← N prod / M test · tests: K`` from the code graph) + its
   signature — enrichment is CAPPED at :data:`_ENRICHMENT_CAP` graph joins (the
   top hits by score), and a graph that raises mid-enrichment still returns the
   hit, annotated with :data:`_ENRICHMENT_UNAVAILABLE`. Each in-flight
   (``dirty``/``embedding``) chunk is flagged stale (annotate, NEVER block). All
   non-fenced rendered fields (identities / paths / memory lines) are
   render-sanitised so control chars / newlines cannot break a citation line or
   escape a fence.
8. **detail_level partition (seam 11 / C2)** — ``"summary"`` keeps only
   summary-classified hits, ``"source"`` only source-classified, ``"auto"`` keeps
   both. Injected memory entries are NOT partitioned — they always trail, in
   their own segregated ``memories:`` block.

The return is a list of summarised :class:`SearchResult` value objects.
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict

from loremaster.extension import DetailLevel, ExtensionContext
from loremaster.index.manifest import STATE_INDEXED
from loremaster.render import render_fenced

# ``_sanitise_line``/``_max_backtick_run``/etc. are explicitly re-exported
# under their ORIGINAL private names (see the module-level ``__all__`` below
# and the item-10/finding-#34 note further down) -- mirrors
# ``loremaster.memory.local``'s own ``truncate_at_word_boundary`` precedent:
# an ``__all__`` entry, not a redundant ``as X`` same-name alias (a lint smell
# under this repo's ruff config, PLC0414).
from loremaster.sanitise import BACKTICK_RUN_PATTERN as _BACKTICK_RUN_PATTERN
from loremaster.sanitise import CONTROL_CHAR_PATTERN as _CONTROL_CHAR_PATTERN
from loremaster.sanitise import FENCE_CHAR as _FENCE_CHAR
from loremaster.sanitise import MIN_FENCE_WIDTH as _MIN_FENCE_WIDTH
from loremaster.sanitise import max_backtick_run as _max_backtick_run
from loremaster.sanitise import sanitise_line as _sanitise_line
from loremaster.store.candidate import Candidate

__all__ = [
    "_BACKTICK_RUN_PATTERN",
    "_CONTROL_CHAR_PATTERN",
    "_FENCE_CHAR",
    "_MIN_FENCE_WIDTH",
    "_max_backtick_run",
    "_sanitise_line",
]

if TYPE_CHECKING:
    from loresigil.base import Embedder

    from loremaster.config import LoreConfig
    from loremaster.graph_surreal import SurrealCodeGraph
    from loremaster.index.surreal_manifest import SurrealManifest
    from loremaster.memory.backend import MemoryBackend, RecalledMemory
    from loremaster.server import LoreServer
    from loremaster.store.surreal import SurrealStore

# The detail-level selector the caller passes; ``"auto"`` keeps every level.
DetailSelector = Literal["auto", "summary", "source"]
_DETAIL_AUTO = "auto"

# The discriminator on every :class:`SearchResult`: a real code hit vs a visible,
# provenance-stamped injected memory line (item 5) vs a server-composed teaching
# NOTICE (P8d Wave 4a: a filter-miss teach, a budget-elision trailer, or a
# caller_model honesty note — never a cited source span, never memory guidance).
ResultKind = Literal["hit", "memory", "notice"]
HIT_KIND: ResultKind = "hit"
MEMORY_KIND: ResultKind = "memory"
NOTICE_KIND: ResultKind = "notice"

# The per-chunk freshness warning (plan: "⚠ re-indexing — may be stale"). A
# returned chunk whose file is in-flight is flagged with this — never blocked.
STALE_WARNING = "⚠ re-indexing — may be stale"

# Payload keys the base format / freshness / classification / enrichment read.
# They match the keys ``records.chunk_to_record`` stamps into every point payload.
_PAYLOAD_FILE_PATH = "file_path"
_PAYLOAD_TIER = "tier"
_PAYLOAD_LINE_START = "line_start"
_PAYLOAD_LINE_END = "line_end"
_PAYLOAD_CHUNK_TYPE = "chunk_type"
_PAYLOAD_SOURCE_TEXT = "source_text"
_PAYLOAD_CONTENT_HASH = "content_hash"
_PAYLOAD_IDENTITY = "identity"
# item 12d (S4b, D3): the chunk's identifier text — the verbatim-anchor
# channel's haystack (see :func:`_has_verbatim_identifier_anchor`).
_PAYLOAD_IDENT_TEXT = "ident_text"
# The chunker stamps ``signature`` (a rendered ``(params) -> ret`` string) on
# function/method chunks and ``None`` on everything else — so a non-``None`` str
# here is exactly "this hit is a callable worth a graph ref-join" (item 7).
_PAYLOAD_SIGNATURE = "signature"

# The filter keys that scope the in-flight wait to a path. ``file_path`` is the
# stored payload key; ``path`` is the friendlier alias a caller may pass.
_FILTER_FILE_PATH_KEYS = ("file_path", "path")

# How much a memory reference lifts a matching candidate's score (item 4). The
# store's fused RRF scores are strictly < 1.0 (rank-1/rank-1 tops out well below
# it — see :class:`~loremaster.store.candidate.Candidate`), so a boost of one full
# unit guarantees a referenced hit overtakes ANY unreferenced one regardless of
# the raw fused ordering, while a stable sort preserves the relative order among
# equally-boosted candidates. (Re-grounded on the RRF scale — the pre-P6 value was
# sized for a cosine gap, an order of magnitude the fused score never reaches.)
_MEMORY_BOOST = 1.0

# item 5: at most this many recalled memories are injected as visible entries,
# highest-score first — a deterministic cap so a noisy recall can never flood the
# response with guidance lines. Raised 2 -> 3 (P8d' #54 tweak T3) alongside the
# trailing-block reorder; anything recalled beyond this cap is named in a
# counted elision notice (:data:`_MEMORY_ELISION_TEMPLATE`), never silently
# dropped.
_MEMORY_INJECTION_CAP = 3

# item 4/5: how many memories a single pipeline recall pulls from the backend.
# One recall drives BOTH the silent boost (over every returned memory's refs) and
# the visible injection (capped at :data:`_MEMORY_INJECTION_CAP`), so this is
# sized to cover a handful of the most relevant notes — matching the backend's
# own default recall width — never per-hit fan-out.
_MEMORY_RECALL_K = 5

# item 5: the provenance marker that stamps an injected memory line (so it is
# tellable apart from a real citation) and the (overview) detail level such an
# entry carries — memory guidance is response-level, never a source body.
_MEMORY_MARKER = "[MEMORY]"
_MEMORY_DETAIL_LEVEL: DetailLevel = "summary"

# T3 (P8d' #54 tweak): the section-label row leading the trailing memories:
# block — a plain, static NOTICE_KIND entry (no stored free text, so no
# sanitiser pass is needed) that segregates the injected memory entries from
# the code hits above them, so a memory line can never be mistaken for part
# of the code-hit list.
_MEMORY_SECTION_HEADER = "memories:"

# T3: the counted elision notice for recalled memories beyond the injection
# cap — never a silent drop. "matching memory hit(s)" (not "entries", cf.
# :data:`_SEARCH_ELISION_TEMPLATE` in server.py) since this counts ONLY the
# memory side of the response.
_MEMORY_ELISION_TEMPLATE = "+{elided} more matching memory hit(s) not shown (cap={cap})"

# item 6: the v2 short-citation grammar. Full form
# ``[S:<tier>:<file_path>:<line_start>-<line_end>@<hash6>]``; ``hash6`` is the
# first six hex of the chunk's file content hash. Coexists with the kept
# ``[SOURCE:file:line]`` grammar — it does NOT replace or shorten ``chunk_key``.
_SHORT_CITATION_PREFIX = "[S:"
_SHORT_HASH_LEN = 6

# item 7: the per-hit graph ref-join line ``← N prod / M test · tests: K`` — N/M
# from ``graph.references`` (production/test split), K from ``graph.tests_for``.
_ENRICHMENT_ARROW = "←"  # "←"
_ENRICHMENT_MIDDOT = "·"  # "·"
# item 7: the maximum number of hits enriched per response (a bounded graph-join
# fan-out). A wide result set never issues one graph round-trip per hit — only the
# top ``_ENRICHMENT_CAP`` by score are joined.
_ENRICHMENT_CAP = 10
# item 7: the explicit marker annotating a hit whose enrichment could not be
# computed (the graph raised mid-enrichment) — annotate the hit, never blanket-fail.
_ENRICHMENT_UNAVAILABLE = "⚠ enrichment unavailable"  # "⚠ enrichment unavailable"

# item 12 (S4b — RETIRES S4's fused-score floor, docs/design/2026-07-06-weak-
# match-discrimination.md): the fused RRF score is a rank-fusion CODE, not a
# magnitude (score = sum over arms of 1/(60 + rank_in_arm)) — structurally
# incapable of discriminating nonsense from real queries (§1.2: the shipped
# S4 floor false-flagged 2.9% of real queries while catching only 6.7% of
# nonsense, and a live nonsense hit sailed through unflagged at 0.0286). S4's
# fused-floor mechanism (``_SEARCH_SCORE_FLOOR``, the per-hit warning, the
# aggregate all-weak notice) is RETIRED — replaced by the machinery below,
# built on the store's PRE-FUSION cosine projection (:class:`Candidate.
# vector_cosine <loremaster.store.candidate.Candidate>`), a genuine magnitude.
#
# MEASURED and ADOPTED (2026-07-06, SUPERSEDED 2026-07-07 — finding #74) —
# original: live search_score_survey.py re-run (post-D3-fix; scratchpad/
# survey_out_rerun/search_score_survey_summary.md + .jsonl, that session):
# D1 PASSES; D2 returned floor=0.5828, false-fire 4.0% (2/50 on the union of
# prose-real + identifier-real queries), nonsense catch 100.0% (15/15).
# ADOPTED on that data.
#
# SUPERSEDED (2026-07-07, P8d closure-fixer-74, finding #74 remediation):
# finding #74 showed the eval-question-shaped "real" group under-measured
# the false-fire rate — it never sampled informant-probe-style implementation-
# vocabulary queries (docs/design/2026-07-06-client-needs-consult.md +
# 2026-07-06-weak-match-discrimination.md), the exact class the #74 probe
# belongs to. Fix: widened the survey's real-query union to a THIRD group,
# :data:`~scripts.search_score_survey.IMPLEMENTATION_VOCABULARY_QUERIES`
# (scripts/search_score_survey.py), and re-ran live (scratchpad/
# survey_out_74w/search_score_survey_summary.md + .jsonl, team-lead's run,
# 2026-07-07). D1 substrate gate PASSES (median within-query cosine spread
# over real+identifier+implementation-vocabulary clears the 0.05 bar). D2
# verdict floor selection, computed from that run's own jsonl (never
# hand-estimated from the summary prose — a live check turned up ONE
# additional unavoidable false-firer, an identifier-sampled query whose own
# definition never surfaced in its top-10 pool, that a hand-read of the
# summary table would have missed): floor=0.50649 (5 decimal places, not
# this file's usual 4 — see the dominance-ordering note below for why),
# false-fire 1.8% (1/56 on the union of prose-real + identifier-real +
# implementation-vocabulary-real queries, under the 5% ceiling), nonsense
# catch 100.0% (15/15) — clears the >= 60% (9/15) adoption bar.
#
# DOMINANCE-ORDERING RULING (operator/lead, 2026-07-07): the widened run's
# own data exposed a genuine selection-rule gap in
# :func:`~scripts.search_score_survey.choose_cosine_floor` — catch can tie
# across many admissible floors (a naive "largest admissible floor, scanning
# top-down" — this function's OLD behavior — silently returned a DOMINATED
# floor, 0.5370 at 3.6% false-fire, when a LOWER floor achieved the
# IDENTICAL 100% catch at strictly less false-fire). Fixed there: among
# admissible floors, maximize catch, THEN minimize false-fire, THEN maximize
# the floor (the final tie-break — see that function's own docstring).
# 0.50649 is the corrected algorithm's answer, not 0.5370. The precision
# (5 not 4 decimal places) is deliberate: 0.50649 is a REAL sample's own
# measured cosine (the "transitive ripple rollup for impact depth>1" probe),
# and rounding it to 4 places (0.5065) would push the floor to just ABOVE
# that sample's own exact value, flipping it from "does not fire" to
# "fires" and silently doubling the measured false-fire rate — verified
# live before committing this value.
#
# ADOPTED, never re-guessed: flipping either constant again requires a
# fresh survey run's receipts, exactly as this one did.
#
# DISARMED 2026-07-24 (packet 10-d, docs/plans/v2/10-d-weak-match-disarm.md,
# ruled by docs/design/2026-07-24-floor-calibration.md Addendum E1). The
# floor above is UNCHANGED as a historical record (see the stamp below) —
# but it is no longer SERVED, because the judgement it powers is
# confident-wrong three source-verified ways: the per-hit flag consults no
# drift state, so it compares live cosines against a floor measured in a
# retired embedding space (#176); the constant was measured on lore's own
# corpus and ships in the image to every foreign instance with no validity
# claim there (#179); and it was calibrated on best-of-response cosines and
# is applied to every INDIVIDUAL hit, a population those hits cannot belong
# to (#180). DESIGN-LAW §1.3 prices this: under-claiming is nearly free,
# ONE confident-wrong costs authority for the session.
#
# ``None`` here is the constant's own DESIGNED rollback state (see the
# gates in ``_cosine_absence_verdict`` and ``SearchPipeline._format_result``
# — both already read it), not a pre-measurement default. Note what does
# NOT change: :data:`_COSINE_SUBSTRATE_ENABLED` stays ``True``, because a
# raw magnitude with no judgement attached is claim-free and D1-gated.
#
# The re-arm is packet 11-ii, from the INSTANCE'S OWN measurement rather
# than a baked-in constant — so the "fresh survey run's receipts" rule
# above still governs any future serving value; it is not repealed here,
# it is superseded by per-instance calibration.
_COSINE_SUBSTRATE_ENABLED = True
_COSINE_WEAK_MATCH_FLOOR: float | None = None

# --- finding #74 part 3: the floor's drift-detection stamp -----------------
# The floor above is a MEASURED constant -- its validity is conditioned on
# the corpus it was measured against, not eternal. Finding #74 showed the
# rot mechanism concretely: the SAME implementation-vocabulary query
# ("enforce the search token budget and build the elision notice naming
# elided hits") false-fired the absence verdict when filed, then stopped
# false-firing after a routine, unrelated edit to the very method it asks
# about changed that method's own embedding -- the floor never moved, but
# the corpus underneath it did. A floor with no re-measure trigger rots
# exactly like the token-budget calibration constant did before
# CalibrationEngine (loremaster/calibration/engine.py) existed -- the SAME
# mechanical-trigger idea, deliberately NOT the same weight: no network
# probe, no background task, no persisted cache file, just a stamped
# snapshot compared against ``lore_index()``'s own already-cheap status
# fields (files_indexed, embedding_schema.fingerprint) at status-read time
# (wired in server.py's ``AppContext._build_index_status``).
@dataclass(frozen=True)
class CosineFloorMeasurement:
    """The corpus snapshot :data:`_COSINE_WEAK_MATCH_FLOOR` was measured against.

    Attributes:
        floor: The measured floor value this stamp documents (kept as its
            own field, not re-read from the module global, so a stamp stays
            a self-contained snapshot even if a future refactor separates
            the two).
        measured_file_count: ``lore_index()``'s ``files_indexed`` count at
            measurement time.
        measured_embedding_schema_fingerprint: ``lore_index()``'s
            ``embedding_schema.fingerprint`` at measurement time -- folds in
            BOTH the embedding config AND ``config.chunkers`` (see
            :func:`~loremaster.index.schema.embedding_schema_fingerprint`),
            so this one field stands in for "chunker-config identity" —
            reused, never re-derived.
    """

    floor: float
    measured_file_count: int
    measured_embedding_schema_fingerprint: str


# Re-stamped 2026-07-07 (P8d closure-fixer-74, finding #74 remediation, part
# 2) against a live ``lore_index()`` read taken immediately after the
# team-lead's widened survey re-run (files_indexed=214, the closest
# available snapshot to that run's own corpus state — the survey script
# itself does not capture a lore_index() reading, so this is the nearest
# proxy, same discipline as the mechanism's first (2026-07-07 part 3)
# baseline). embedding_schema.fingerprint is UNCHANGED from that first
# baseline (b4dd657beb...) — confirms no chunker/embedding-config drift
# happened between the two stamps, only routine file-count churn (210 ->
# 214, well inside the 10% tolerance either way). Every SUBSEQUENT floor
# change (a fresh survey re-run) re-stamps BOTH fields here from that run's
# own ``lore_index()`` read -- never guessed, never left stale.
#
# Packet 10-d (2026-07-24): this stamp deliberately DISAGREES with the
# serving constant now -- it records floor=0.50649 while
# :data:`_COSINE_WEAK_MATCH_FLOOR` is ``None``. That is not staleness: the
# disarm is not a survey re-run, so there is nothing to re-stamp, and this
# snapshot is the historical record of WHAT 0.50649 WAS MEASURED AGAINST.
# Packet 11-i reads it as provenance; 11-ii owns its retirement.
_COSINE_WEAK_MATCH_FLOOR_STAMP: CosineFloorMeasurement | None = CosineFloorMeasurement(
    floor=0.50649,
    measured_file_count=214,
    measured_embedding_schema_fingerprint=(
        "b4dd657bebd69a951358a163fd24243aedd0ab2d6169547950ce38055b863af8"
    ),
)

# The drift bar (finding #74 part 3): a chunker/embedding-schema fingerprint
# change is an EXACT-MATCH gate below (any change disqualifies on its own —
# lore's OWN rebuild machinery already treats any such change as "re-embed
# everything," which necessarily moves every cosine in the corpus). File
# count is a SOFTER, percentage bar: routine edits between remediation waves
# add/remove a file or two without shifting the corpus's overall vocabulary
# distribution, and a +/-10% band mirrors the survey's own tolerance for
# "still basically the same corpus" while still catching a genuinely
# reshaped corpus (a new tier onboarded, a large doc dump indexed) that
# SHOULD force a re-measure.
_COSINE_FLOOR_DRIFT_FILE_COUNT_TOLERANCE: float = 0.10

# Packet 10-d (2026-07-24): what the ``disabled`` state SAYS. Finding #4's
# lesson is that disabled-BY-CONFIG and disarmed-PENDING-CALIBRATION are
# different conditions and must not share a rendering — a null note renders
# as "this surface was simply never turned on", which is a different (and,
# today, false) fact about the instance. §C5 family (a) by construction:
# the failure is admitted loudly, the findings that caused it are citable,
# the packets that resolve it are named, and what STILL serves is stated so
# a reader does not conclude the whole cosine surface went away.
_COSINE_FLOOR_DISARMED_NOTE = (
    "weak-match confidence surfaces disarmed pending per-instance calibration "
    "(findings #83/#176/#179/#180; packets 11-i/11-ii) — per-hit similarity "
    "substrate remains served."
)

@dataclass
class _CosineFloorRuntimeState:
    """The runtime-mutable half of the disarm seam — an attribute holder, not

    a bare module global, so (re)arming is an ATTRIBUTE mutation rather than
    a ``global`` rebind (keeps ruff's PLW0603 clean and matches this
    codebase's OOP-over-functional house style even for module-scoped
    state). Reflects the LAST status-read's drift observation: consulted
    (never mutated) by ``_cosine_absence_verdict`` on the query hot path;
    mutated ONLY by :func:`apply_cosine_floor_drift_check`. Deliberately
    recomputed fresh on every call (never a one-way latch) — unlike
    CalibrationEngine's retry/cache state, a stamp comparison is a cheap,
    deterministic, no-network computation, so "last observed" is exactly the
    current truth as of the last status read, never a permanently-stuck
    disable that would itself need a redeploy to lift.

    Attributes:
        disarmed_by_drift: ``True`` iff the last drift check found the
            floor's stamp had drifted beyond its bar.
    """

    disarmed_by_drift: bool = False


_cosine_floor_runtime_state = _CosineFloorRuntimeState()


@dataclass(frozen=True)
class CosineFloorDriftStatus:
    """One :func:`apply_cosine_floor_drift_check` outcome — pure data, no I/O.

    Attributes:
        state: ``"measured"`` (stamp still holds, verdict armed), ``"stale"``
            (drift exceeded the bar, verdict disarmed), or ``"disabled"``
            (the floor itself is ``None`` — nothing to drift-check).
        floor: The floor value the stamp documents, or ``None`` when disabled.
        measured_file_count: The stamp's recorded file count, or ``None`` when
            disabled.
        current_file_count: The file count this check was run against.
        measured_embedding_schema_fingerprint: The stamp's recorded
            fingerprint, or ``None`` when disabled.
        current_embedding_schema_fingerprint: The fingerprint this check was
            run against.
        note: A human-readable explanation of a NON-serving state — the
            drift reason when ``state == "stale"``, or
            :data:`_COSINE_FLOOR_DISARMED_NOTE` when ``state == "disabled"``
            (packet 10-d). ``None`` iff ``state == "measured"``, the one
            state that needs no explanation because the surface is serving.
    """

    state: Literal["measured", "stale", "disabled"]
    floor: float | None
    measured_file_count: int | None
    current_file_count: int
    measured_embedding_schema_fingerprint: str | None
    current_embedding_schema_fingerprint: str
    note: str | None


def _cosine_floor_drift_note(
    stamp: CosineFloorMeasurement,
    current_file_count: int,
    current_embedding_schema_fingerprint: str,
) -> str | None:
    """The drift reason, or ``None`` when ``stamp`` still holds (pure, no I/O).

    Two independent gates, either one alone disqualifies the stamp:

    1. ANY embedding-schema-fingerprint change (exact-match — it already
       folds in ``config.chunkers``, see :func:`~loremaster.index.schema.
       embedding_schema_fingerprint`) — checked FIRST, so a query that
       drifted on both signals at once gets one clear reason, not two.
    2. A file-count swing beyond :data:`_COSINE_FLOOR_DRIFT_FILE_COUNT_TOLERANCE`
       (a percentage band, not an exact match — routine edits are expected).
    """
    if current_embedding_schema_fingerprint != stamp.measured_embedding_schema_fingerprint:
        return (
            f"embedding schema fingerprint changed since measurement "
            f"({stamp.measured_embedding_schema_fingerprint[:12]}… -> "
            f"{current_embedding_schema_fingerprint[:12]}…) — the chunker/"
            f"embedding config moved; the corpus was very likely fully re-embedded"
        )
    measured_count = stamp.measured_file_count
    if measured_count <= 0:
        # Defensive: a non-positive stamped count cannot form a ratio — treat
        # as unconditional drift rather than divide by zero (mirrors
        # CalibrationEngine._apply_measurement's own non-positive-baseline
        # guard).
        return f"stamped file count ({measured_count}) is non-positive — cannot verify"
    shift = abs(current_file_count - measured_count) / measured_count
    if shift > _COSINE_FLOOR_DRIFT_FILE_COUNT_TOLERANCE:
        return (
            f"indexed file count shifted {shift * 100:.1f}% since measurement "
            f"({measured_count} -> {current_file_count}), beyond the "
            f"{_COSINE_FLOOR_DRIFT_FILE_COUNT_TOLERANCE * 100:.0f}% tolerance"
        )
    return None


def apply_cosine_floor_drift_check(
    *, current_file_count: int, current_embedding_schema_fingerprint: str
) -> CosineFloorDriftStatus:
    """Re-check the floor's stamp against the CURRENT corpus, (re)setting the disarm flag.

    Called by ``AppContext._build_index_status`` on every ``lore_index()``
    read (a cheap, no-embeds status read) — never on the query hot path.
    Recomputes :attr:`_CosineFloorRuntimeState.disarmed_by_drift` fresh every
    call (see that attribute's own docstring for why this is a deliberate
    non-latch).

    Args:
        current_file_count: The CURRENT ``files_indexed`` count (from the
            same status read this is called from).
        current_embedding_schema_fingerprint: The CURRENT
            ``embedding_schema.fingerprint`` (same status read; an unstamped
            fresh deploy passes ``""``, which never matches a real stamp and
            is therefore fail-safe — treated as drift, mirroring
            :func:`~loremaster.index.schema.rebuild_needed`'s own
            provenance-unknown-is-unsafe rule).

    Returns:
        The :class:`CosineFloorDriftStatus` snapshot this call just applied.
    """
    stamp = _COSINE_WEAK_MATCH_FLOOR_STAMP
    if _COSINE_WEAK_MATCH_FLOOR is None or stamp is None:
        _cosine_floor_runtime_state.disarmed_by_drift = False
        return CosineFloorDriftStatus(
            state="disabled",
            floor=None,
            measured_file_count=None,
            current_file_count=current_file_count,
            measured_embedding_schema_fingerprint=None,
            current_embedding_schema_fingerprint=current_embedding_schema_fingerprint,
            note=_COSINE_FLOOR_DISARMED_NOTE,
        )
    note = _cosine_floor_drift_note(
        stamp, current_file_count, current_embedding_schema_fingerprint
    )
    _cosine_floor_runtime_state.disarmed_by_drift = note is not None
    return CosineFloorDriftStatus(
        state="stale" if note is not None else "measured",
        floor=stamp.floor,
        measured_file_count=stamp.measured_file_count,
        current_file_count=current_file_count,
        measured_embedding_schema_fingerprint=stamp.measured_embedding_schema_fingerprint,
        current_embedding_schema_fingerprint=current_embedding_schema_fingerprint,
        note=(f"floor stale — re-measure needed: {note}" if note is not None else None),
    )


def _reset_cosine_floor_drift_state_for_tests() -> None:
    """Test-only reset of the runtime disarm state (lifecycle-test seam).

    Module-level mutable state must not leak across tests (global CLAUDE.md's
    lifecycle-test rule) — tests reset this via an autouse fixture rather
    than relying on call order.
    """
    _cosine_floor_runtime_state.disarmed_by_drift = False


# item 12a: the always-on per-hit magnitude (design doc §7.4 item 2) — a
# claim-free number, read RELATIVELY within one response (no cross-call
# calibration needed); ships only once :data:`_COSINE_SUBSTRATE_ENABLED` is
# measured on.
_COSINE_SUBSTRATE_TEMPLATE = "sim {cosine:.2f}"

# item 12b: the per-hit weak-match warning (design doc §7.4 item 3) — fires
# unconditionally below :data:`_COSINE_WEAK_MATCH_FLOOR` (no verbatim-anchor
# carve-out here; that carve-out is the AGGREGATE verdict's condition only,
# D3) — cheap, advisory, aids skimming a mixed list.
_COSINE_WEAK_MATCH_WARNING_TEMPLATE = (
    "⚠ weak match — semantic similarity {cosine:.2f} is below the {floor:.2f} "
    "floor measured on real-query hits"
)

# item 12c: the aggregate hedged absence verdict (design doc §7.4 item 3,
# §7.5's exact recommended wording) — the absence-verdict analogue of the
# counted-elision notice: converts "should I keep looking?" into a zero-call
# decision. Fires iff the max cosine among SHOWN code hits is below the floor
# AND no shown hit carries a verbatim-identifier anchor (D3) — "nearest
# indexed" names the identity of WHICHEVER candidate actually produced that
# max cosine (finding #76 fix, 2026-07-07: previously hardcoded to the
# fused-order top hit's identity, which silently diverges from the candidate
# ``best_cosine`` describes whenever a cosine-strong hit sits below a
# cosine-weak one), turning "no answer" into a redirect (Opus's addition,
# §7.3).
# Finding #71 budget-protection marker: the notice's own fixed, never-
# varying lead-in — named as an explicit, EXPORTED constant so a budget-
# reservation check elsewhere (server.py's ``_enforce_search_budget``) can
# identify THIS specific notice among sibling NOTICE_KIND entries by the
# pipeline's own stable mark, never a freshly-guessed substring and never
# matching against the templated PROSE that follows it (the per-query
# cosine/identity text, which legitimately varies call to call). Mirrors
# the existing ``_FILTER_MISS_MARKER``/``_DETAIL_MISS_MARKER`` convention
# (server.py / this module) — the rendered text is UNCHANGED, byte-for-byte
# (a pure extraction, not a wording change).
_ABSENCE_VERDICT_MARKER = "no confident match"
_COSINE_ABSENCE_VERDICT_TEMPLATE = (
    _ABSENCE_VERDICT_MARKER + ": best hit similarity {best_cosine:.2f} is below the range "
    "real answers measure on this corpus (≥{floor:.2f}) and no hit matches "
    "your identifiers verbatim — likely no direct answer indexed; nearest "
    "indexed: {nearest!r} — broaden the query or treat these hits as "
    "adjacent-topic leads"
)

# item 12d (D3): the verbatim-identifier-anchor carve-out's tokenizer — a
# simple, deterministic word-boundary split (mirrors ``scripts/
# search_score_survey.py``'s own ``query_tokens``). An approximation of the
# engine's ``code_ident`` analyzer, not a store round-trip: the conservative
# failure mode (a missed anchor) just means the carve-out doesn't fire,
# falling back to the ordinary absence verdict — never a confident-wrong flag
# on an exact-identifier lookup.
_QUERY_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")

# item 12d fix (D3 carve-out miscalibration — docs/design/2026-07-06-weak-
# match-discrimination.md §7.2 D3, operator-ruled fix 2026-07-06): an
# UNGATED token-set intersection fires on a bare common-English word that
# happens to intersect an unrelated identifier fragment inside a hit's
# derived ``ident_text`` (``SurrealStore._derive_ident_text`` space-joins
# identity + bare_name + file_stem, so an English-shaped heading/file-stem
# token sits in the SAME set as real code identifiers) — that is not
# evidence the caller pasted a real symbol. Measured
# (scripts/search_score_survey.py run, 2026-07-06): 9/15 nonsense queries
# anchored this way (e.g. "rate limiting middleware per client IP address"
# anchored via bare "rate"/"client"), capping nonsense catch at 40% against
# D2's 60% adoption bar. The QUERY side of the anchor is therefore
# restricted to identifier-SHAPED tokens (:func:`_identifier_shaped_query_tokens`)
# — underscore-bearing, a segment of a dot-qualified chain, or internally
# case-changing (camelCase) — plus a substantial-length whole-query fallback
# (:func:`_has_whole_query_identity_match`) for an exact non-code identity
# paste (a doc heading sampled straight off the corpus) that carries none of
# those three shapes.
_MIN_WHOLE_QUERY_ANCHOR_LENGTH = 12

# Matches a dot-qualified identifier chain (``Class.method``, ``os.path``) as
# ONE run so each 2+-character segment can be marked identifier-shaped even
# when, alone, it carries neither an underscore nor an internal case change
# (a bare lowercase leaf after the dot, e.g. ``"get"`` in ``"requests.get"``).
# Each segment requires >= 2 characters so a prose abbreviation like "e.g."
# or "i.e." (single-letter segments) never qualifies.
_DOTTED_IDENTIFIER_CHAIN_PATTERN = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]+(?:\.[A-Za-z_][A-Za-z0-9_]+)+"
)

# item 13 (S3, finding #61 — confirmed live, not just a static-reading lead):
# a non-``"auto"`` ``detail_level`` can legitimately zero EVERY code hit after
# ``_partition_pairs_by_detail`` even though the pre-partition candidate set was
# non-empty — the injected memory entries are appended UNCONDITIONALLY after
# this (they are never partitioned), so without a notice the response renders
# memories-only with zero explanation of why the code side went to zero
# (client-needs-consult §S3; Opus's exact reported shape, live-reproduced —
# see REPORT-slate-builder-search.md). Mirrors
# ``AppContext._filter_miss_notice``'s teaching grammar (server.py) for the
# analogous path/tier-filter-miss case, kept entirely in THIS module (no
# server.py change needed): the server-side budget enforcer was investigated
# and REFUTED as an alternate mechanism (it is a strict front-to-back prefix
# walk over ``[*hits, *memory_entries]``, so it can never elide a leading hit
# while keeping a trailing memory).
_DETAIL_MISS_MARKER = "[DETAIL MISS]"
_DETAIL_LEVEL_MISS_TEMPLATE = (
    "{marker} 0 code hits matched detail_level={detail_level!r} — {total} candidate(s) "
    'were found before filtering, none classify at this level — retry with '
    'detail_level="auto" to see them'
)

# item 10 / finding #34: the hostile-char sanitiser + fence-sizing helpers now
# live in the shared public seam ``loremaster.sanitise`` (imported tree-wide so
# no renderer re-hand-rolls or skips the launder; see the top-of-file import +
# module-level ``__all__``). Re-exported here under the original private
# names for zero downstream breakage -- this module's own internal callers,
# ``server.py``, and ``diff.py`` all still import these private names from
# ``loremaster.search`` unchanged.

# Default bound on the in-flight wait, in seconds. Always finite — the wait can
# never hang (the embedder may be slow or down).
_DEFAULT_WAIT_TIMEOUT_S = 10.0

# Poll interval for the bounded in-flight wait.
_WAIT_POLL_INTERVAL_S = 0.05


def _refjoin_line(production_references: int, test_references: int, covering_tests: int) -> str:
    """Render the item-7 ref-join line ``← N prod / M test · tests: K``.

    The counts are forwarded verbatim from the code graph (``references`` split
    production/test, ``tests_for`` covering-node count); this is the single place
    the exact ref-join grammar is composed.
    """
    return (
        f"{_ENRICHMENT_ARROW} {production_references} prod / {test_references} test "
        f"{_ENRICHMENT_MIDDOT} tests: {covering_tests}"
    )


def _cosine_substrate_line(cosine: float) -> str:
    """Render the item-12a always-on per-hit magnitude for ``cosine``."""
    return _COSINE_SUBSTRATE_TEMPLATE.format(cosine=cosine)


def _cosine_weak_match_warning(cosine: float, floor: float) -> str:
    """Render the item-12b per-hit weak-match warning for ``cosine`` vs ``floor``."""
    return _COSINE_WEAK_MATCH_WARNING_TEMPLATE.format(cosine=cosine, floor=floor)


def _query_tokens(query: str) -> frozenset[str]:
    """The lower-cased word-token set of ``query`` (item 12d, the D3 anchor unit)."""
    return frozenset(token.lower() for token in _QUERY_TOKEN_PATTERN.findall(query))


def _has_internal_case_change(token: str) -> bool:
    """True iff ``token`` has a lowercase-then-uppercase transition (camelCase/PascalCase merge).

    A single leading capital (``"Kubernetes"``) or an all-caps acronym
    (``"HVAC"``, ``"GPU"``) has no SUCH transition and is not identifier-
    shaped by this test alone — only a genuine multi-word merge
    (``"TestScoutMainGuard"``, ``"OriginValidationMiddleware"``) counts,
    which is exactly the shape a pasted class/symbol name carries and a
    plain English word or acronym never does.
    """
    return any(a.islower() and b.isupper() for a, b in zip(token, token[1:]))


def _identifier_shaped_query_tokens(query: str) -> frozenset[str]:
    """The lower-cased SUBSET of ``query``'s tokens that look like a pasted identifier (D3 fix).

    A token qualifies iff it is underscore-bearing, a segment of a
    dot-qualified chain (``Class.method``), or internally case-changing
    (camelCase/PascalCase) — never a bare common-English word, no matter how
    it happens to line up with an unrelated identifier fragment in some
    hit's ``ident_text``. See the comment above
    :data:`_MIN_WHOLE_QUERY_ANCHOR_LENGTH` for the measured defect this
    closes.
    """
    shaped: set[str] = set()
    for chain in _DOTTED_IDENTIFIER_CHAIN_PATTERN.findall(query):
        shaped.update(segment.lower() for segment in chain.split("."))
    for raw_token in _QUERY_TOKEN_PATTERN.findall(query):
        if "_" in raw_token or _has_internal_case_change(raw_token):
            shaped.add(raw_token.lower())
    return frozenset(shaped)


def _has_whole_query_identity_match(query: str, ident_text: str) -> bool:
    """The D3 fallback: a substantial, verbatim whole-query match inside ``ident_text``.

    Protects an exact NON-code identity paste (a doc heading, a title
    sampled straight off the corpus — e.g. ``"Summary > Fix — DISCLOSE-AND-
    SERVE"``) that carries none of :func:`_identifier_shaped_query_tokens`'s
    three shapes but is, taken as a whole, the caller reproducing a real
    stored identity character-for-character. Gated on
    :data:`_MIN_WHOLE_QUERY_ANCHOR_LENGTH` so a short common phrase can never
    coincidentally qualify.
    """
    normalised_query = " ".join(query.lower().split())
    if len(normalised_query) < _MIN_WHOLE_QUERY_ANCHOR_LENGTH:
        return False
    normalised_ident_text = " ".join(ident_text.lower().split())
    return normalised_query in normalised_ident_text


def _has_verbatim_identifier_anchor(query: str, ident_text: str) -> bool:
    """True iff ``ident_text`` carries a verbatim-identifier anchor for ``query`` (D3).

    Two admission paths, both requiring the QUERY side to look like a
    pasted identifier/identity — never a bare topical-word overlap:

    1. An identifier-shaped query token (:func:`_identifier_shaped_query_tokens`)
       appears as a WHOLE token in ``ident_text``'s own tokenization — a
       token-SET intersection, never a raw substring scan, so a short shaped
       token (e.g. ``"is_a"``) cannot spuriously match inside an unrelated
       longer glued token (e.g. ``"this_is_a_test"``).
    2. The entire (whitespace-normalised) query is a substantial, verbatim
       substring of ``ident_text`` (:func:`_has_whole_query_identity_match`)
       — the non-code identity-paste fallback.
    """
    shaped_tokens = _identifier_shaped_query_tokens(query)
    if shaped_tokens and shaped_tokens & _query_tokens(ident_text):
        return True
    return _has_whole_query_identity_match(query, ident_text)


def _cosine_absence_predicate(best_cosine: float, floor: float, has_verbatim_anchor: bool) -> bool:
    """True iff the D2/D3 aggregate absence-verdict condition holds.

    Fires iff ``best_cosine`` (the MAXIMUM cosine among shown code hits) is
    strictly below ``floor`` AND no shown hit carries a verbatim-identifier
    anchor (D3's exact-lookup protection). Extracted as its own pure function
    — not left inlined in :func:`_cosine_absence_verdict` — so ``scripts/
    search_score_survey.py``'s Phase C floor selection can IMPORT this exact
    rule and measure the pre-registered ≤5%/≥60% bars (docs/design/2026-07-06-
    weak-match-discrimination.md §7.2 D2) against the IDENTICAL predicate
    production fires on, never a re-derived paraphrase that can silently
    drift (S4b audit finding #1, REPORT-slate-audit-searchstore.md §Concern 6:
    the survey previously measured ``top_hit_cosine`` with no anchor
    carve-out at all — a different rule than this one).
    """
    return best_cosine < floor and not has_verbatim_anchor


def _cosine_absence_verdict(
    partitioned_pairs: list[tuple[SearchResult, Candidate]], query: str
) -> SearchResult | None:
    """The item-12c aggregate absence verdict, or ``None`` when it does not apply.

    Dark while :data:`_COSINE_WEAK_MATCH_FLOOR` is ``None`` — which, since
    packet 10-d (2026-07-24), is the SHIPPED state on every instance: the
    floor is measured but DISARMED from serving pending per-instance
    calibration (#176/#179/#180; 11-ii arms it). This gate is therefore not
    a dormant rollback lever today; it is the live production path — OR
    while
    :attr:`_cosine_floor_runtime_state`\\ ``.disarmed_by_drift`` is ``True``
    (finding #74 part 3: the last ``lore_index()`` status read
    detected the floor's stamp had drifted beyond its bar — under-claim is
    cheap, a confidently-wrong absence claim is not, so the AGGREGATE
    verdict goes silent rather than keep serving a possibly-rotted claim;
    the per-hit weak-match flag/substrate line are unaffected — see their
    own gates below). Once armed, fires per :func:`_cosine_absence_predicate`:
    there is at least one shown code hit, the MAXIMUM cosine among them (never just the
    top-fused-order hit's — a cosine-strong hit can sit below a cosine-weak
    one) is strictly below the floor, AND no shown hit carries a
    verbatim-identifier anchor (D3's exact-lookup protection). "Nearest
    indexed" names the identity of whichever candidate actually produced
    ``best_cosine`` — NOT necessarily the fused-order top hit (finding #76:
    hardcoding the top hit's identity here let the rendered similarity number
    and the rendered identity describe two different candidates, reading as
    one false claim about whichever of the two was actually shown).
    """
    if _COSINE_WEAK_MATCH_FLOOR is None or _cosine_floor_runtime_state.disarmed_by_drift:
        return None
    code_pairs = [(hit, candidate) for hit, candidate in partitioned_pairs if hit.kind == HIT_KIND]
    if not code_pairs:
        return None
    # (cosine, candidate) pairs, restricted to candidates that carry a cosine
    # at all -- the comprehension's own `if` clause narrows `vector_cosine`
    # from `float | None` to `float` for the yielded tuple (same idiom the
    # pre-fix code used for its `cosines` list).
    cosine_candidates = [
        (candidate.vector_cosine, candidate)
        for _hit, candidate in code_pairs
        if candidate.vector_cosine is not None
    ]
    if not cosine_candidates:
        return None
    best_cosine, best_candidate = max(cosine_candidates, key=lambda pair: pair[0])
    has_anchor = any(
        _has_verbatim_identifier_anchor(query, str(candidate.payload.get(_PAYLOAD_IDENT_TEXT, "")))
        for _hit, candidate in code_pairs
    )
    if not _cosine_absence_predicate(best_cosine, _COSINE_WEAK_MATCH_FLOOR, has_anchor):
        return None
    nearest = _sanitise_line(str(best_candidate.payload.get(_PAYLOAD_IDENTITY, "")))
    text = _COSINE_ABSENCE_VERDICT_TEMPLATE.format(
        best_cosine=best_cosine, floor=_COSINE_WEAK_MATCH_FLOOR, nearest=nearest
    )
    return SearchResult(
        formatted=text,
        chunk_key="",
        detail_level="summary",
        stale=False,
        score=0.0,
        kind=NOTICE_KIND,
    )


def _detail_level_miss_notice(detail_level: str, total_before_filter: int) -> SearchResult:
    """The item-13 notice: ``detail_level`` zeroed every code hit."""
    text = _DETAIL_LEVEL_MISS_TEMPLATE.format(
        marker=_DETAIL_MISS_MARKER, detail_level=detail_level, total=total_before_filter
    )
    return SearchResult(
        formatted=text,
        chunk_key="",
        detail_level="summary",
        stale=False,
        score=0.0,
        kind=NOTICE_KIND,
    )


class _Reranker(Protocol):
    """The config-gated cross-encoder reranker seam (item 9) — interface only.

    P6 ships no live reranker client; the pipeline calls this seam ONLY when
    ``config.search.reranker`` is set, passing the RRF-fused candidates through
    after fusion and before formatting.
    """

    async def rerank(
        self, query: str, candidates: list[Candidate], ctx: ExtensionContext
    ) -> list[Candidate]:
        """Re-score/reorder ``candidates`` for ``query`` and return them."""
        ...


class SearchResult(BaseModel):
    """A summarised search result — a formatted citation or an injected memory line.

    Attributes:
        formatted: The rendered block — for a ``hit``, the base
            ``[SOURCE:file:line]`` + ``Key:`` + short ``[S:…]`` citation + fenced
            source (or an extension's custom format), plus any graph ref-join /
            signature / stale warning; for a ``memory`` entry, the sanitised,
            provenance-stamped memory line.
        chunk_key: The result's stable key — the extension semantic key if one
            claims it, else the structural bare-uuid5 point id; empty for an
            injected memory entry (a memory is not a cited chunk).
        detail_level: The chunk's classified detail level (``summary``/``source``).
        stale: Whether the chunk's file is in-flight (``dirty``/``embedding``) in
            the manifest at query time (always ``False`` for a memory entry).
        score: The (possibly memory-boosted) fusion score, or the memory's recall
            score for a ``memory`` entry.
        kind: ``"hit"`` (a real code citation) or ``"memory"`` (an injected,
            provenance-stamped project-memory line) — see :data:`ResultKind`.
    """

    model_config = ConfigDict(extra="forbid")

    formatted: str
    chunk_key: str
    detail_level: DetailLevel
    stale: bool
    score: float
    kind: ResultKind = HIT_KIND


class SearchPipeline:
    """The query-time pipeline behind ``search_code`` (dependency-injected, OOP).

    Args:
        store: The unified :class:`~loremaster.store.surreal.SurrealStore` — the
            read path is its ``hybrid_search`` (HNSW ⊕ BM25 via RRF).
        embedder: The active :class:`~loresigil.base.Embedder` (query side).
        server: The composed :class:`~loremaster.server.LoreServer`, which
            resolves the extension hooks (``augment_candidates``/``rerank``/
            ``format_result``/``chunk_key``/``classify_detail``) — identity/base
            for a bare server.
        manifest: The :class:`~loremaster.index.surreal_manifest.SurrealManifest`,
            the authority on per-(tier, file) freshness.
        config: The validated :class:`~loremaster.config.LoreConfig` — its
            ``search.reranker`` block gates the reranker seam (item 9).
        extension_context: The RUNTIME :class:`~loremaster.extension.ExtensionContext`
            handed to every context-taking search seam (4/5/6/11). It carries the
            REAL shared services — the live embedder, the manifest, and the
            embedder's working ``count_tokens`` — so an extension's search hooks
            see functional resources, NOT the composition-time placeholder the
            server's :meth:`~loremaster.server.LoreServer.extension_context`
            returns. The owner (``build_app_context``) constructs it over the live
            services and shares the SAME object with the startup hooks, so seam-9
            ``state`` set at startup is visible to the search seams.
        code_graph: The :class:`~loremaster.graph_surreal.SurrealCodeGraph` the
            per-hit ref-join enrichment (item 7) joins against.
        memory_store: Optional :class:`~loremaster.memory.backend.MemoryBackend`
            for the memory boost + visible injection; ``None`` disables both
            (the generic, no-memory deploy). Its ``recall(query, k=...)`` is the
            single memory read the pipeline drives.
        reranker: Optional config-gated cross-encoder reranker seam (item 9);
            called ONLY when ``config.search.reranker`` is set.
    """

    def __init__(
        self,
        *,
        store: SurrealStore,
        embedder: Embedder,
        server: LoreServer,
        manifest: SurrealManifest,
        config: LoreConfig,
        extension_context: ExtensionContext,
        code_graph: SurrealCodeGraph,
        memory_store: MemoryBackend | None = None,
        reranker: _Reranker | None = None,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._server = server
        self._manifest = manifest
        self._config = config
        self._extension_context = extension_context
        self._code_graph = code_graph
        self._memory_store = memory_store
        self._reranker = reranker

    async def search_code(
        self,
        query: str,
        k: int,
        filters: dict[str, str] | None = None,
        *,
        wait_for_fresh: bool = False,
        detail_level: str = _DETAIL_AUTO,
        wait_timeout_s: float = _DEFAULT_WAIT_TIMEOUT_S,
    ) -> list[SearchResult]:
        """Run the full query-time pipeline and return summarised results.

        Args:
            query: The natural-language search query.
            k: The maximum number of candidates to retrieve from the store.
            filters: Optional payload keyword filters (e.g. ``{"tier": ...}`` or
                ``{"file_path": ...}``), applied server-side in BOTH fused arms.
                The public alias ``"path"`` is translated to the canonical
                ``"file_path"`` payload key before the store query.
            wait_for_fresh: When ``True``, bounded-wait for in-flight files
                matching the query's path filter to reach ``indexed`` before
                searching; on timeout, serve stale-with-warning (never hang).
            detail_level: ``"auto"`` (both), ``"summary"``, or ``"source"`` — the
                detail-level partition applied to the code hits (injected memory
                entries always trail and are never partitioned).
            wait_timeout_s: The hard ceiling on the ``wait_for_fresh`` poll.

        Returns:
            The summarised :class:`SearchResult` list — the ranked, formatted
            code hits FIRST, then any injected memory entries segregated
            behind a trailing ``memories:`` section header — never a raw
            :class:`~loremaster.store.candidate.Candidate` dump.
        """
        ctx = self._extension_context

        # Step 1: bounded read-your-writes wait (never hangs).
        if wait_for_fresh:
            await self._wait_for_fresh(filters, wait_timeout_s)

        # Steps 2 + 3: embed for the vector arm, forward the RAW text for the BM25
        # arm, and fetch the RRF-fused candidates (a down store RAISES here).
        vector = await self._embedder.embed_query(query)
        candidates = await self._store.hybrid_search(
            query_vector=vector,
            query_text=query,
            k=k,
            filters=self._normalize_filters(filters),
        )

        # Step 4 (seam 4 / C3): extension candidate-augmentation then rerank
        # (identity for the bare generic server).
        candidates = self._server.augment_candidates(query, candidates, ctx)
        candidates = self._server.rerank(candidates, ctx)

        # Step 5: recall project memory ONCE, then boost referenced candidates and
        # (below, after formatting) inject the visible memory entries.
        recalled = await self._recall_memory(query)
        candidates = self._apply_memory_boost(candidates, recalled, ctx)

        # Step 6 (item 9): config-gated reranker seam (post-RRF, pre-format).
        candidates = await self._maybe_rerank(query, candidates, ctx)

        # Step 7: format each candidate (base/extension citation + capped graph
        # enrichment + freshness flag), keeping each hit paired with its
        # originating candidate (S4b: the aggregate absence verdict needs the
        # candidate's vector_cosine/ident_text, which SearchResult itself
        # never carries -- no wire-shape change; see the module docstring).
        enrichment_targets = self._select_enrichment_targets(candidates)
        hit_candidate_pairs = [
            (
                await self._to_result(candidate, ctx, enrich=candidate.key in enrichment_targets),
                candidate,
            )
            for candidate in candidates
        ]
        hits = [hit for hit, _candidate in hit_candidate_pairs]

        # Step 8: partition the (hit, candidate) PAIRS by detail level in
        # lockstep, then append the visible memory entries as a trailing,
        # segregated block (T3, P8d' #54 tweak -- they never partition, and
        # now never lead either).
        partitioned_pairs = self._partition_pairs_by_detail(hit_candidate_pairs, detail_level)
        partitioned_hits = [hit for hit, _candidate in partitioned_pairs]

        # Step 8b (item 13 / S3): a non-auto detail_level that zeroed EVERY
        # code hit gets an explicit teaching notice -- never a silent
        # memories-only response (finding #61, confirmed live). Mutually
        # exclusive with step 9 below: this fires only when partitioned_hits
        # is empty, in which case step 9's absence-verdict check (which
        # requires >=1 code hit) can never also fire.
        detail_miss_notice = self._detail_miss_check(hits, partitioned_hits, detail_level)

        # Step 9 (item 12c, S4b): the gated cosine absence verdict -- dark
        # until its floor is measured (see _cosine_absence_verdict) -- placed
        # right after the hits it describes, before the trailing memories:
        # block. Replaces S4's retired fused-score all-weak notice.
        absence_notice = _cosine_absence_verdict(partitioned_pairs, query)

        memory_entries = self._inject_memories(recalled)
        return [
            *partitioned_hits,
            *([detail_miss_notice] if detail_miss_notice is not None else []),
            *([absence_notice] if absence_notice is not None else []),
            *memory_entries,
        ]

    # -- filter normalisation ---------------------------------------------------

    @staticmethod
    def _normalize_filters(
        filters: dict[str, str] | None,
    ) -> dict[str, str] | None:
        """Translate the public ``path`` alias to the canonical ``file_path`` key.

        The store's filter allow-list uses dict keys verbatim as payload field
        names, and no chunk carries a ``path`` field — only ``file_path``. This
        helper returns a new dict with the alias translated so callers can use
        either spelling without silently matching nothing.

        Precedence: if BOTH ``path`` and ``file_path`` are present the explicit
        canonical ``file_path`` wins and the alias is dropped. All other keys
        (e.g. ``tier``) pass through untouched. A ``None`` or empty dict is
        returned unchanged.

        The canonical target is :data:`_PAYLOAD_FILE_PATH` — the field name
        ``records.chunk_to_record`` actually stamps into every point — so the
        translation is decoupled from the ORDER of :data:`_FILTER_FILE_PATH_KEYS`
        (reordering that tuple, e.g. to surface ``path`` first, cannot silently
        reintroduce the bug). The alias set is every recognised path-filter key
        except the canonical one, keeping a single constant authoritative for
        both the wait-scoping path (``_path_filter``) and this store-query path.
        """
        if not filters:
            return filters

        # The canonical payload field (what the indexer stamps); everything else
        # in the recognised path-filter key set is an alias.  Aliases never reach
        # the store — only the canonical field name does.
        canonical = _PAYLOAD_FILE_PATH
        aliases = {key for key in _FILTER_FILE_PATH_KEYS if key != canonical}

        # Fast path: nothing to do when no alias key is present.
        if not aliases.intersection(filters):
            return filters

        normalised: dict[str, str] = {}
        for key, value in filters.items():
            if key in aliases:
                # Translate alias → canonical, but only when the caller did NOT
                # also supply the canonical key explicitly (canonical wins).
                if canonical not in filters:
                    normalised[canonical] = value
                # else: drop the alias — the explicit canonical key takes precedence.
            else:
                normalised[key] = value
        return normalised

    # -- step 1: bounded read-your-writes wait ------------------------------

    async def _wait_for_fresh(
        self, filters: dict[str, str] | None, timeout_s: float
    ) -> None:
        """Bounded-wait for the path-filtered in-flight files to reach ``indexed``.

        Polls the manifest for the file(s) named by the query's
        ``file_path``/``path`` filter until every such row is ``indexed`` OR the
        timeout elapses, whichever comes first. ALWAYS returns within
        ``timeout_s`` — a file that never settles (slow/down embedder) is served
        stale-with-warning rather than hanging the search. With no path filter
        there is no single file to wait on, so this returns at once (the freshness
        flags still annotate any in-flight chunk that surfaces).
        """
        file_path = self._path_filter(filters)
        if file_path is None:
            return
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if await self._all_rows_indexed_for_path(file_path):
                return
            await asyncio.sleep(_WAIT_POLL_INTERVAL_S)

    @staticmethod
    def _path_filter(filters: dict[str, str] | None) -> str | None:
        """Extract the path the wait should scope to from the filters, or ``None``."""
        if not filters:
            return None
        for key in _FILTER_FILE_PATH_KEYS:
            if key in filters:
                return filters[key]
        return None

    async def _all_rows_indexed_for_path(self, file_path: str) -> bool:
        """True iff every manifest row for ``file_path`` (any tier) is ``indexed``.

        A path may exist under multiple tiers (C1); a wait is satisfied only when
        no copy is still in-flight. An absent path (no rows) is vacuously settled.
        """
        rows = [row for row in await self._manifest.all_files() if row.file_path == file_path]
        return all(row.state == STATE_INDEXED for row in rows)

    # -- step 5: memory recall / boost / visible injection ------------------

    async def _recall_memory(self, query: str) -> list[RecalledMemory]:
        """Recall project memory for ``query`` once (``[]`` with no memory store).

        A single recall drives BOTH the silent score-boost and the visible
        injection, so the two never double-query the memory collection.
        """
        if self._memory_store is None:
            return []
        # P7 cutover: the memory dependency is the SurrealDB-backed
        # ``MemoryBackend`` protocol, whose read is ``recall(query, k=...)``
        # (the retired ``MemoryStore.recall_memory`` shape is gone).
        return list(await self._memory_store.recall(query, k=_MEMORY_RECALL_K))

    def _apply_memory_boost(
        self,
        candidates: list[Candidate],
        recalled: list[RecalledMemory],
        ctx: ExtensionContext,
    ) -> list[Candidate]:
        """Boost candidates a recalled memory references, then re-sort by score.

        Collects the chunk-keys the recalled memories reference; any candidate
        whose key is in that set has its score lifted by :data:`_MEMORY_BOOST`
        (enough — on the RRF scale — to overtake an unboosted chunk the store
        ranked higher) and the candidates are re-sorted descending. The lift uses
        :meth:`~loremaster.store.candidate.Candidate.model_copy` so the boost never
        mutates the store's returned candidate. Empty recall ⇒ unchanged.
        """
        referenced_keys = {ref.chunk_key for memory in recalled for ref in memory.refs}
        if not referenced_keys:
            return candidates

        boosted: list[Candidate] = []
        for candidate in candidates:
            if self._chunk_key(candidate, ctx) in referenced_keys:
                # model_copy so the boost never mutates the store's returned candidate.
                boosted.append(
                    candidate.model_copy(update={"score": candidate.score + _MEMORY_BOOST})
                )
            else:
                boosted.append(candidate)
        # Stable sort: equally-boosted candidates keep their incoming relative order.
        boosted.sort(key=lambda candidate: candidate.score, reverse=True)
        return boosted

    def _inject_memories(self, recalled: list[RecalledMemory]) -> list[SearchResult]:
        """Render the ≤ cap top-scored recalled memories as a trailing block (item 5).

        The injected entries are provenance-stamped (so they never masquerade
        as a source citation) and capped at :data:`_MEMORY_INJECTION_CAP` by
        descending score. The block is segregated behind a
        :data:`_MEMORY_SECTION_HEADER` label (T3, P8d' #54 tweak) — emitted
        ONLY when there is at least one memory entry to segregate — and a
        recall that found more matching memories than the cap gets a counted
        elision notice, never a silent drop. Empty recall ⇒ nothing (no
        header, no notice).
        """
        if not recalled:
            return []
        top = sorted(recalled, key=lambda memory: memory.score, reverse=True)
        kept = top[:_MEMORY_INJECTION_CAP]
        entries = [self._memory_section_header(), *[self._memory_result(m) for m in kept]]
        elided = len(top) - len(kept)
        if elided:
            entries.append(self._memory_elision_notice(elided))
        return entries

    @staticmethod
    def _memory_section_header() -> SearchResult:
        """The static section-label row leading the trailing memories: block.

        No stored free text is rendered here (a fixed constant), so no
        sanitiser pass applies — the sanitiser guards untrusted content, not
        this server-composed label.
        """
        return SearchResult(
            formatted=_MEMORY_SECTION_HEADER,
            chunk_key="",
            detail_level=_MEMORY_DETAIL_LEVEL,
            stale=False,
            score=0.0,
            kind=NOTICE_KIND,
        )

    @staticmethod
    def _memory_elision_notice(elided: int) -> SearchResult:
        """The counted notice for recalled memories squeezed out by the cap."""
        text = _MEMORY_ELISION_TEMPLATE.format(elided=elided, cap=_MEMORY_INJECTION_CAP)
        return SearchResult(
            formatted=text,
            chunk_key="",
            detail_level=_MEMORY_DETAIL_LEVEL,
            stale=False,
            score=0.0,
            kind=NOTICE_KIND,
        )

    @staticmethod
    def _memory_result(memory: RecalledMemory) -> SearchResult:
        """Build one provenance-stamped, sanitised memory :class:`SearchResult`.

        The line carries the :data:`_MEMORY_MARKER`, the memory text, and its refs'
        keys — and is render-sanitised to a single logical line (item 10) so a
        hostile memory text cannot smuggle framing or a fake extra result. It
        deliberately carries NEITHER citation grammar, so it is never mistaken for
        a cited source span.
        """
        ref_keys = ", ".join(ref.chunk_key for ref in memory.refs)
        line = _sanitise_line(f"{_MEMORY_MARKER} {memory.text} (refs: {ref_keys})")
        return SearchResult(
            formatted=line,
            chunk_key="",  # a memory is provenance, not a cited chunk
            detail_level=_MEMORY_DETAIL_LEVEL,
            stale=False,
            score=memory.score,
            kind=MEMORY_KIND,
        )

    # -- step 6: config-gated reranker seam ---------------------------------

    async def _maybe_rerank(
        self, query: str, candidates: list[Candidate], ctx: ExtensionContext
    ) -> list[Candidate]:
        """Route candidates through the reranker seam iff CONFIG enables it (item 9).

        The gate is ``config.search.reranker`` — NOT the mere presence of the
        injected seam object. With the reranker unconfigured the seam is provably
        never called (an injected reranker double stays inert).
        """
        if self._config.search.reranker is None or self._reranker is None:
            return candidates
        return await self._reranker.rerank(query, candidates, ctx)

    # -- step 7: per-hit graph enrichment (capped) --------------------------

    @staticmethod
    def _select_enrichment_targets(candidates: list[Candidate]) -> set[str]:
        """The keys of the hits to graph-enrich — the top ``_ENRICHMENT_CAP`` by score.

        Only a function/method hit (a non-``None`` string ``signature``) is a
        candidate for a ref-join; of those, the top :data:`_ENRICHMENT_CAP` by
        score are selected so a wide result set never fans out one graph
        round-trip per hit. Ties break on ascending key (deterministic).
        """
        symbol_hits = [
            candidate
            for candidate in candidates
            if isinstance(candidate.payload.get(_PAYLOAD_SIGNATURE), str)
        ]
        ranked = sorted(symbol_hits, key=lambda candidate: (-candidate.score, candidate.key))
        return {candidate.key for candidate in ranked[:_ENRICHMENT_CAP]}

    async def _enrichment_lines(self, payload: dict[str, Any]) -> list[str]:
        """The ref-join + signature lines for one symbol hit (item 7), fail-soft.

        Joins the code graph on the chunk's ``identity``: ``references`` gives the
        production/test split, ``tests_for`` the covering-test count. A graph that
        raises mid-enrichment yields the single :data:`_ENRICHMENT_UNAVAILABLE`
        marker line instead of dropping the hit or failing the whole search.
        """
        symbol = str(payload.get(_PAYLOAD_IDENTITY, ""))
        signature = payload.get(_PAYLOAD_SIGNATURE)
        try:
            summary = await self._code_graph.references(symbol)
            covering = await self._code_graph.tests_for(symbol)
        except Exception:
            # Annotate, never blanket-fail: the hit is still cited, its enrichment
            # explicitly marked unavailable (a mid-enrichment graph outage).
            return [_sanitise_line(_ENRICHMENT_UNAVAILABLE)]
        refjoin = _refjoin_line(
            summary.production_references, summary.test_references, len(covering)
        )
        return [_sanitise_line(refjoin), _sanitise_line(str(signature))]

    # -- step 7: per-result formatting --------------------------------------

    async def _to_result(
        self, candidate: Candidate, ctx: ExtensionContext, *, enrich: bool
    ) -> SearchResult:
        """Format one candidate, enrich it, flag freshness, classify its detail."""
        payload = candidate.payload
        key = self._chunk_key(candidate, ctx)
        stale = await self._is_stale(payload)
        detail = self._server.classify_detail(payload.get(_PAYLOAD_CHUNK_TYPE, "")) or "source"

        enrichment_lines = await self._enrichment_lines(payload) if enrich else []

        # Seam 5: an extension's custom format wins; otherwise the base citation
        # (which folds the enrichment lines in BEFORE its fenced source block).
        core = self._server.format_result(candidate, ctx)
        if core is None:
            formatted = self._base_format(payload, key, enrichment_lines)
        else:
            formatted = core
            if enrichment_lines:
                formatted = f"{formatted}\n" + "\n".join(enrichment_lines)
        if stale:
            formatted = f"{formatted}\n{STALE_WARNING}"
        # item 12 (S4b): the cosine substrate/weak-flag machinery, each behind
        # its OWN gate constant (see those constants for the exact semantics).
        # As shipped since packet 10-d (2026-07-24) the two gates disagree
        # deliberately: the SUBSTRATE is on (a claim-free magnitude), the
        # weak-match FLAG is dark (its floor is disarmed pending per-instance
        # calibration, #176/#179/#180) — so this block renders the number and
        # never the judgement.
        if _COSINE_SUBSTRATE_ENABLED and candidate.vector_cosine is not None:
            formatted = f"{formatted}\n{_cosine_substrate_line(candidate.vector_cosine)}"
        if (
            _COSINE_WEAK_MATCH_FLOOR is not None
            and candidate.vector_cosine is not None
            and candidate.vector_cosine < _COSINE_WEAK_MATCH_FLOOR
        ):
            formatted = (
                f"{formatted}\n"
                f"{_cosine_weak_match_warning(candidate.vector_cosine, _COSINE_WEAK_MATCH_FLOOR)}"
            )

        return SearchResult(
            formatted=formatted,
            chunk_key=key,
            detail_level=detail,
            stale=stale,
            score=candidate.score,
            kind=HIT_KIND,
        )

    def _chunk_key(self, candidate: Candidate, ctx: ExtensionContext) -> str:
        """The result's stable key — the extension semantic key, else the point id.

        Seam 6: an extension may supply a versioned semantic key for a payload;
        when none claims it, the candidate's bare-uuid5 key (``records.point_id``)
        is the key. Carried on every result so a caller can cite it and a memory
        ref can match it. This stays the FULL stable key — the short ``[S:…]``
        citation never shortens or replaces it (item 6).
        """
        key = self._server.chunk_key(candidate.payload, ctx)
        return key if key is not None else candidate.key

    def _base_format(
        self, payload: dict[str, Any], key: str, enrichment_lines: list[str]
    ) -> str:
        """The base default citation (item 6): kept ``[SOURCE:]`` + ``Key:`` + fence,
        plus the added v2 short ``[S:…]`` citation and any graph enrichment.

        The path/identity-carrying lines are render-sanitised (item 10) so a
        hostile ``file_path`` cannot break a citation line; the source body is
        wrapped VERBATIM in a backtick fence sized to survive an embedded run.
        """
        file_path = str(payload.get(_PAYLOAD_FILE_PATH, ""))
        tier = str(payload.get(_PAYLOAD_TIER, ""))
        line_start = payload.get(_PAYLOAD_LINE_START, 0)
        line_end = payload.get(_PAYLOAD_LINE_END, line_start)
        content_hash = str(payload.get(_PAYLOAD_CONTENT_HASH, ""))
        source_text = payload.get(_PAYLOAD_SOURCE_TEXT, "") or ""
        hash6 = content_hash[:_SHORT_HASH_LEN]

        # Non-fenced rendered fields — each sanitised to a single logical line.
        lines = [
            _sanitise_line(f"[SOURCE:{file_path}:{line_start}]"),
            _sanitise_line(f"Key: {key}"),
            _sanitise_line(
                f"{_SHORT_CITATION_PREFIX}{tier}:{file_path}:{line_start}-{line_end}@{hash6}]"
            ),
            *enrichment_lines,
        ]
        # The source body: verbatim, wrapped in the SHARED render fence — the ONE fence
        # construction home (render_fenced). search.py no longer sizes or builds a fence of
        # its own (operator ruling 2026-08-05: FULL route-through; #102 one implementation).
        # render_fenced consumes the SAME sanitise.fence_width policy the old private width
        # clone did, so this is byte-preserving (pinned in test_task_read_surface.py).
        lines.append(str(render_fenced(source_text)))
        return "\n".join(lines)

    async def _is_stale(self, payload: dict[str, Any]) -> bool:
        """True iff the chunk's manifest file row is in-flight (not ``indexed``).

        The manifest — not the store — is the freshness authority. A row absent
        from the manifest is treated as settled (nothing in-flight to warn about).
        """
        tier = payload.get(_PAYLOAD_TIER, "")
        file_path = payload.get(_PAYLOAD_FILE_PATH, "")
        row = await self._manifest.get(tier, file_path)
        if row is None:
            return False
        return row.state != STATE_INDEXED

    # -- step 8: detail-level partition -------------------------------------

    @staticmethod
    def _partition_pairs_by_detail(
        pairs: list[tuple[SearchResult, Candidate]], detail_level: str
    ) -> list[tuple[SearchResult, Candidate]]:
        """Keep only the (hit, candidate) pairs matching ``detail_level`` (``auto`` = all).

        S4b: partitions hit/candidate PAIRS in lockstep (rather than hits
        alone) so the aggregate absence verdict (step 9) can read each shown
        hit's originating candidate (``vector_cosine``/``ident_text``) after
        filtering. Applied to the code hits only; injected memory entries are
        appended after this and are never partitioned (they are response-level
        guidance).
        """
        if detail_level == _DETAIL_AUTO:
            return pairs
        return [(hit, candidate) for hit, candidate in pairs if hit.detail_level == detail_level]

    # -- step 8b (item 13 / S3): detail-level-miss notice --------------------

    @staticmethod
    def _detail_miss_check(
        hits: list[SearchResult], partitioned_hits: list[SearchResult], detail_level: str
    ) -> SearchResult | None:
        """The item-13 notice, or ``None`` when it does not apply.

        Fires ONLY when the pre-partition ``hits`` were non-empty but the
        ``detail_level`` partition removed every one of them. ``"auto"`` can
        never trigger this (it never filters); a genuinely empty ``hits``
        (nothing was "zeroed BY the filter" — some other, unrelated cause) is
        NOT this defect either.
        """
        if detail_level == _DETAIL_AUTO or not hits or partitioned_hits:
            return None
        return _detail_level_miss_notice(detail_level, len(hits))
