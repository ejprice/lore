# Weak-match discrimination for lore_search — the three-model consult

**Date:** 2026-07-06 (slate cycle) · **Consultant:** slate-consult-weakmatch (Fable) ·
**Ledger row:** 23af3c9b83974b46a78cc072be6322b5 · **Finding of record:** #68 (acknowledged)
**Status:** DESIGN RECORD — the build wave executes from §Recommendation.

**Operator framing:** how should lore_search signal low-confidence/weak-match to its
LLM clients, GIVEN the measured truth that fused (RRF) scores do not separate nonsense
from real queries on this corpus? Ruled a CLIENT design question — the models who
consume the tool decide what serves them; the operator only sequences the build.

**Method precedent:** docs/design/2026-07-04-map-test-segregation.md and
docs/design/2026-07-06-client-needs-consult.md (the binding client design law:
silent anything is cardinal; counted/honest limits with exact levers;
caveats-with-verdicts raise trust; under-claim cheap, confident-wrong ruinous;
affordances in-response).

---

## 1. Measured context

### 1.1 The S4 survey (committed: `scripts/search_score_survey.py`; finding #68)

Top-hit FUSED scores, live server, 35 real eval questions vs 15 adversarial nonsense
queries:

| group | n | mean | median | p5 | p95 | max |
|---|---|---|---|---|---|---|
| real | 35 | 0.0213 | 0.0200 | 0.0167 | 0.0286 | 0.0323 |
| nonsense | 15 | 0.0245 | 0.0266 | 0.0164 | 0.0320 | 0.0320 |

The nonsense central mass sits ABOVE the real one. The shipped
`_SEARCH_SCORE_FLOOR = 0.0167` (p5-of-real) false-flags 2.9% of real queries and
catches 6.7% of nonsense — an honest low-confidence flag, not a discriminator. The
consult's motivating 0.031-scored nonsense hit sails through unflagged.

### 1.2 Why no fused-score floor can ever work (structural, not empirical accident)

The fused score is SurrealDB `search::rrf` with `_RRF_K = 60`
(`loremaster/store/surreal.py:228`, statement builder `_hybrid_statement`
surreal.py:1324): **score = Σ over arms of 1/(60 + rank_in_arm)** — a
rank-reciprocal CODE, not a magnitude:

- single-arm rank-1 ≈ 1/61 ≈ **0.0164** — exactly the measured nonsense min/p5;
- both-arms rank-1 ≈ 2/61 ≈ **0.0328** — the ceiling both measured maxes graze
  (0.0320/0.0323).

**Live receipt (this consult, 2026-07-06):** nonsense query
*"quantum blockchain drone delivery smart fridge firmware for pet grooming"* →
top hit `TestLiveNotificationDelivery` (an utterly irrelevant test class) at
score 0.0286 rendered identically to a confident hit; second hit at
**exactly 1/61 = 0.01639344262295082** — the reciprocal-rank decode confirmed to
machine precision.

The mechanism: a nonsense query has ONE weakly-adjacent document, which trivially
tops BOTH arms (nearest neighbor and best lexical overlap are the same doc when
nothing else competes) → perfect rank agreement → a HIGH fused score. A real query
on a rich corpus has many plausible matches → the arms disagree about ordering →
a LOWER top score. **The fused score measures the corpus's consensus structure
around the query, not match quality.** All magnitude information — the vector
arm's raw cosine, the lexical arm's BM25 score — is discarded at fusion
(`Candidate` carries only the fused score; `origin` is always `"fused"` —
`store/candidate.py:30`, `_to_candidates` surreal.py:1512).

Corollary: `_MEMORY_BOOST = 1.0` (search.py) lifts boosted candidates above the
entire sub-1.0 fused range, so any pre-fusion magnitude signal stays orthogonal to
the memory boost by construction.

### 1.3 What the client actually needs (from the S4 origin)

Both prior informants hit the same shape: a semantically-adjacent-but-wrong hit
(a 429-retry test for a "rate limiter" query) rendered identically to a confident
match — "the score was present but unframed." Semantic search structurally cannot
return empty: **absence is unprovable from any single response today.** The client
need is therefore not "detect nonsense queries" (word salad is rare); it is
(a) *don't let me over-read a weak top hit as an answer*, and (b) *give me a
calibrated way to conclude "probably nothing here" without a verification
round-trip* — the absence-verdict analogue of the counted-elision notice.

---

## 2. The candidate solution space

Judged against: MORE honest without new lies (a discriminator wrong 30% of the
time is a new confident-wrong channel — the worst trade per the law), token cost,
and constants derivable by a committed deterministic survey.

**C0 — Status quo (shipped S4).** The fused-score floor + per-hit flag + all-weak
aggregate. Honest, near-inert on the motivating trap (which scores HIGH).

**C1 — Pre-fusion cosine banding.** The store additionally returns each fused
hit's raw query↔chunk cosine (in-engine projection over the stored embedding —
feasibility probe + fallbacks in §6). Survey re-run measures real vs nonsense
top-hit COSINE distributions; IF separated at pre-registered bars, a measured
cosine floor drives a per-hit flag and — the prize — an aggregate
**"no confident match"** state when the best shown cosine is below floor. Zero
tokens on confident responses. Cosine separation is a HYPOTHESIS until measured;
adoption is gated (§6), fallback C7.

**C2 — Two-arm magnitude composite.** Capture cosine AND the lexical arm's BM25
score; flag weak only when BOTH magnitudes are weak. Protects the
exact-identifier lookup (pasted symbol name: modest cosine, decisive lexical
overlap) from cosine-only false flags — the channel that would otherwise point
confident-wrong at the client's most confident queries.

**C3 — Top-vs-second margin on the fused score.** Zero store change, but the
margin of a rank-quantized code is itself rank structure. Measured for free in
the same survey re-run (all-hit scores now captured); expected to fail; adopted
only if the data shockingly says otherwise.

**C4 — Arm-agreement decode.** The fused score already encodes membership
(score > 1/61 ⇒ both arms). REJECTED as a confidence signal: the motivating
nonsense hit matches BOTH arms perfectly — "arms agree" reads as MORE confident
exactly when it should read less. An inverted discriminator is worse than none.

**C5 — Corpus-percentile framing of the FUSED score.** REJECTED: with the
nonsense mass ABOVE the real mass, "score 0.031 — p87 of real-query top hits"
borrows the authority of measurement to tell a lie about the trap case.

**C6 — Raw cosine on every hit, no verdict.** The client thresholds itself.
Rejected as a standalone: an unframed number re-creates the exact hole S4 came
from (clients don't retain calibration across 30 calls, let alone sessions);
constant token cost on every confident response. Survives as a COMPONENT: the
weak-flag render shows the number WITH the floor.

**C7 — Null verdict.** If the survey shows neither cosine nor the composite
separates, the shipped floor IS the honest maximum: retire the aspiration with
receipts on the ledger (#68), keep C0, and teach instead of pretending — one
sentence in the tool surface: *"scores are rank-fusion artifacts; judge hits by
content, not score."* Stopping the client from inventing a discriminator is
itself an honesty feature.

Named and set aside: **query-side signals** (e.g. how many documents the lexical
arm matched at all). True word salad is rare; the common trap is a plausible
absent-feature query with real words, which matches plenty lexically. The client
need is a hit-level property, not a query classifier.

### Candidate renders (exact strings)

C1 per-hit (only on below-floor hits, appended like `STALE_WARNING`):

> `⚠ weak match — semantic similarity 0.31 is below the 0.44 floor measured on real-query hits`

C1 aggregate (fires when the BEST cosine among shown code hits is below floor —
note: max-cosine-of-response, NOT top-fused-hit cosine; the list is ordered by
fused score, and a cosine-strong hit can sit below a cosine-weak one):

> `no confident match: best hit similarity 0.31 is below the range real answers measure on this corpus (≥0.44) — likely no direct answer indexed; broaden the query or treat these hits as adjacent-topic leads`

C2 per-hit:

> `⚠ weak match — neither retrieval arm is confident (similarity 0.31 < 0.44; lexical overlap negligible)`

---

## 3. Fable first-hand section (the consultant is also a client)

What I actually do with lore_search responses today: I judge relevance by reading
hit CONTENT; the score is a float I hold no calibration for, so I mostly ignore
it. When I query for something that doesn't exist, my failure mode is not
believing the adjacent hit — it is the VERIFICATION SPIRAL: rephrase-and-requery,
maybe a lore_map orient, maybe a grep fallback, before I'll write "this repo has
no X." Absence is unprovable from any single response, so I pay 1–3 extra calls
every time the true answer is "not here."

**The aggregate "no confident match" state is therefore the entire prize for me.**
It is the absence-verdict analogue of the counted-elision notice: it converts
"should I keep looking?" into a zero-call decision. The per-hit flag is secondary
triage — useful in a mixed list, but I read content anyway.

Per candidate, what I would actually do differently:

- **C0:** nothing — the flag fires at score levels the trap never occupies. Inert
  for my real usage.
- **C1 aggregate:** directly changes my next action. On "no confident match …
  likely no direct answer indexed" I stop the requery spiral: either conclude
  absence (when my prior agrees) or make ONE targeted structural check
  (lore_map / lore_impact) instead of open-ended re-search. This is the render
  that deletes the verification tax.
- **C2:** the wording is the best of the set independent of the composite
  mechanics — *"neither retrieval arm is confident"* claims weakness of the
  RETRIEVAL, not of the TRUTH. That altitude is exactly right: say what was
  measured, leave the epistemic conclusion to me. And the identifier-lookup
  protection matters: I DO paste exact symbol names into lore_search when
  lore_get_symbol misses; a cosine-only flag that fires on those is a
  confident-wrong channel aimed at my most confident queries.
- **C3:** numerology on a quantized code. Measure it since it's free; don't build
  on it.
- **C4:** as confidence, inverted — reject. As descriptive context, I'd read it
  rarely and wouldn't pay per-hit tokens for it.
- **C5:** hard reject — percentile framing of a non-discriminating signal is
  manufactured authority.
- **C6 alone:** I will not reliably self-calibrate. By call 30 the earlier scores
  are tens of thousands of tokens back; across sessions I retain nothing. An
  unframed number is the hole we're in, repeated with a second number.
- **C7:** acceptable ONLY with the measurement receipts, and I'd still want the
  teaching sentence — an honest "this signal cannot say weak" beats a decorative
  flag that implies it can.

**False-flag asymmetry, from my seat:** the per-hit flag is nearly free to
false-fire — the content is still rendered and overrides it. The aggregate
verdict licenses skipping verification, so its false-fire is the costly one; but
even then the hits remain rendered beneath it, and content wins on a read. I'd
accept ~5% aggregate false-fire for ≥60% catch, PROVIDED the wording stays
hedged ("likely", "measured range") — a hedged notice wrong 1-in-20 is a
calibrated witness; an unhedged one wrong 1-in-20 is a liar. The law's
confident-wrong ruin applies to unhedged claims.

**On the verdict-vs-always-on fork:** verdict-only-when-weak. Zero cost on the
common confident path; the always-on number is un-asked-for content I won't
calibrate against anyway.

**Replace, don't stack:** if cosine banding lands, retire `_SEARCH_SCORE_FLOOR`
and its templates. A weak-rank-structure hit with strong cosine is semantically
close — flagging it on the fused floor would be a false alarm under the better
signal. One discriminator, one grammar; two overlapping weak-flags at different
altitudes would cost more trust than they buy.

---

## 4. Opus informant section (verbatim)

I'm Claude Opus, answering as an actual consumer of `lore_search` — from what I do with these renders mid-task, not from what sounds principled. All four probes below are live against the current server (pre-fix, so no weak-match flag appears — the unframed status-quo baseline).

### Probe receipts (real renders I saw)

**Probe 1 — adversarial nonsense:** `"quantum blockchain drone delivery smart fridge firmware for pet grooming"`
- Top hit: `TestLiveNotificationDelivery` (`loremaster/tests/test_scout.py:1065`) — **score 0.02862400327131466**
- 2nd hit: `TestClientOwnershipLifecycle` (`test_calibration_counting.py:245`) — **score 0.01639344262295082** (= exactly 1/61)
- No confidence signal of any kind. An utterly irrelevant test class rendered as a confident-looking top hit. This is the brief's motivating receipt, reproduced live.

**Probe 2 — real code question (budget 3000):** `"reciprocal rank fusion search::rrf combine vector and lexical arms"`
- Top hit: `hybrid_search` (`_surreal_fakes.py:700`) — **score 0.03278688524590164** (= 2/61, the both-arms-rank-1 ceiling). Correct answer, at the maximum.
- 2nd hit: `_rank_by_fulltext` (`_surreal_fakes.py:662`) — **score 0.028531243721117136**

**Probe 3 — plausible-but-absent feature:** `"rate limiting and per-user request throttling middleware for the MCP server"`
- Top hit: `OriginValidationMiddleware` (`loremaster/loremaster/auth.py:263`) — **score 0.017446555314718008**
- This is the most instructive receipt of the four: the feature (rate limiting) does not exist; the retriever handed me the *nearest security middleware* (origin validation — a different thing). Score 0.0174, which sits **above** the shipped floor 0.0167, so C0 would stay silent exactly where I most need a signal.

**Probe 4 — real precise query:** `"weak match score floor confidence flag..."` → design-report hits at **score 0.032018442622950824** (I did not open those files per my independence rule; the score itself is the receipt).

**The ordering these receipts produce, by fused score:**
`real-correct 0.0328 > design-report 0.0320 > nonsense 0.0286 > absent-adjacent 0.0174 > shipped floor 0.0167`

Two facts jump out and drive everything below:
1. **The nonsense hit (0.0286) outscores the honest absent-feature lead (0.0174).** The fused score is not just uninformative — on my probes it is *inverted* relative to match quality.
2. **The nonsense top hit (0.0286) equals the real-query p95 (0.0286 from the committed survey) exactly.** Hold that number for C5.

A confession about my processing reality that frames all my answers: **I already mostly ignore the numeric score.** The hit content is right there — I read the docstring/code and judge relevance from it directly. The score is opaque, uncalibrated, and redundant with content I can see. So a signal that merely *decorates the score* does almost nothing for me. The one fact content-reading **cannot** cheaply establish is *absence* — "is there a better hit I didn't retrieve, or is this simply not indexed?" That is the expensive-to-establish fact, and it is the only place a tool-side confidence signal has real leverage over me.

### 1. What I'd actually DO with each render

- **C0 (shipped fused-score floor).** Per-hit: on the aggregate "every shown hit is low-confidence — broaden or treat as speculative," I *would* act (broaden or downgrade the hits to speculative). But it fires almost never (6.7% nonsense catch) and — proven on my own probes — stays silent on both the nonsense hit (0.0286) and the absent-feature hit (0.0174). Worse than inert: its **silence trains me to read no-flag as all-clear**, which is affirmatively misleading when nonsense sails through at 0.0286. I'd rather the tool say nothing about confidence than imply confidence by omission. **Changes my action almost never; misleads me by its silence.**

- **C1 (pre-fusion cosine banding).** *This* changes my behavior correctly — if the survey shows separation. The aggregate "no confident match: top hit similarity 0.31 below the range real answers measure (≥0.44) — likely no direct answer indexed" is exactly the license I want: it tells me the thing I cannot cheaply learn myself (probably nothing here), so I broaden or conclude absence **without a verification round-trip**. Cosine is a magnitude, not a rank-code — the only candidate with a physical basis for discrimination. On Probe 3, if the origin-middleware hit's raw cosine were low, this correctly tells me "rate limiting isn't indexed; this is adjacent." **Correctly changes my next action.** Caveat is real (my Probe 3 query has real words and pulled a real middleware — its cosine may be only moderate).

- **C2 (two-arm magnitude composite).** The *correct* version of C1 for how I actually query. My most confident lookups are exact-symbol pastes ("find `OriginValidationMiddleware`") where cosine is mediocre but lexical is decisive — C1 cosine-only would **false-flag my highest-confidence lookups**, the single most annoying failure. C2 flags weak only when *neither* arm is confident, which is the true "nothing good here" state. The render "neither retrieval arm is confident (similarity 0.31 < 0.44; lexical overlap negligible)" also tells me *why* and hands me an action: "lexical overlap negligible" → add exact identifiers to my query. **Best action-change, fewest false alarms on my confident cases.**

- **C3 (top-vs-second fused margin).** My receipts kill it directly: nonsense margin = 0.0286 − 0.0164 = **0.0122**; real-RRF margin = 0.0328 − 0.0285 = **0.0043**. The nonsense query had a **2.8× larger** margin than the real one — margin says nonsense is *more* confident. **I'd be misled; reject.**

- **C4 (arm-agreement decode).** Correctly rejected as *confidence* (nonsense matches both arms cleanly). As *descriptive provenance* I'd want a sliver of it — see Q6 — but never labeled as confidence. As proposed (a confidence read), I'd misread "both arms" as more confident exactly when it's less. **Don't ship as confidence; the useful half is subsumed by C2's "lexical overlap negligible."**

- **C5 (corpus-percentile framing).** The hardest reject, and my receipts make it concrete: the nonsense hit is 0.0286 = **the real-query p95 exactly**. C5 would render my nonsense match as **"p87 / p95 of real-query top hits."** A percentile *reads as calibrated confidence* — I would trust it — so this launders the rank-code's non-discrimination into an authoritative pointer aimed the wrong way. **Actively misleading; strongest reject.**

- **C6 (raw cosine on every hit, no verdict).** My sleeper favorite. Within one response I read 6–8 hits; if each carries a *raw* magnitude I see the **shape** — one hit at 0.62 with the rest at 0.30 means a standout; everything clustered at 0.28 means diffuse/probably-absent. I self-calibrate by *relative* comparison within the call, which needs **no global floor and no survey to be useful** and makes **zero claims that can be wrong**. Trivial token cost I'd gladly pay. **Changes my action and can never mislead me** — provided it surfaces raw cosine (a magnitude), NOT the fused score (which would just be C5's poison without the label).

- **C7 (null verdict).** Acceptable last resort, but I'd push back on "change nothing" — see Q5.

### 2. Ranking + amendments

**Ranking:** **C6 ≈ C2 ≥ C1 > C0 > C4(as provenance only) > C3 > C5.** C7 is the honest floor-of-last-resort.

But the honest answer is that **C6 and C2 are complementary, not competing** — my real recommendation is to ship **both**:
- **C6 as the always-on substrate** (raw per-hit magnitude, described-not-judged) — unconditional, claim-free, survives even a "nothing separates" measurement.
- **C2's aggregate "no confident match" verdict layered on top** — but *only* if the survey shows the composite separates, and *only* at the aggregate/absence level (the one conclusion I can't reach myself).

**Amendments to make my top choice work:**
- Surface **both arm magnitudes** (raw cosine *and* the BM25 lexical score), not cosine alone — so the render can say "lexical overlap negligible," which is directly actionable for me.
- Keep the aggregate verdict **specificity-biased**: fire only when the *top* hit is weak on the composite (not per-hit noise).
- Per-hit: prefer the bare magnitude (C6) over a per-hit verdict — if I have the number I don't need the tool to judge each hit; I need it to judge *absence*.
- Pre-register the aggregate's precision bar on real-answerable queries (see Q3), and measure within-query spread too (see Q5/Q6).

### 3. The false-flag asymmetry

Two completely different risk classes, and the design must treat them separately:

- **Per-hit false-flag** (weak flag on a hit that IS the answer, content fully rendered): **nearly harmless.** The content is right there; I read it, see it answers me, and the flag costs one extra beat of scrutiny — no wrong action. I do not discard a hit whose content obviously matches just because it's flagged. **I'd tolerate 10–15% here.**

- **Aggregate "no confident match / likely no answer indexed":** **a different animal**, because it *licenses a conclusion (absence)* I'd otherwise pay a round-trip to establish, and if it's wrong I **stop searching** and may report "this isn't in the codebase" when it is — with no self-correction, because the flag told me to distrust the very content that would have corrected me. So the aggregate must be **rare and high-precision**. I'd tolerate **≤2–3% false "no confident match" on real answerable queries; hard ceiling ~5%.** Above that I stop trusting the verdict and go back to reading everything myself, which defeats it. (Note: C0's aggregate is *already* at 2.9% real false-flag — its problem is recall, not precision. For C1/C2, precision is the thing to pre-register and guard.)

### 4. The fork — verdict-only-when-weak vs always-visible magnitude

**Always-visible magnitude (C6) serves me better** — with a nuance. Because: (a) it's unconditional, surviving a "nothing separates" outcome; (b) the relative shape across hits *in a single call* is information I use immediately, no session-length calibration needed; (c) it makes zero claims, so it can never push me to a wrong conclusion — interpretation stays with me, where the content also is; (d) token cost is trivial. The verdict-only appeal (zero cost on confident responses, crisp "no answer") is real, but a verdict can be *wrong* in a way a bare number can't, and its silence-on-confident is the C0 trap that trains a false all-clear.

**Resolution of the fork:** not either/or. **Always-visible magnitude for per-hit** (C6), **verdict only for the aggregate absence-state** (C2). Per-hit verdicts are redundant once I have per-hit magnitude; the aggregate verdict earns its keep because "does a better hit exist / is it absent" is the expensive fact I can't cheaply get myself.

### 5. If the measurement comes back "nothing separates" (C7 branch)

I still want **C6** — raw per-hit magnitude (both arms, ideally), described not judged. Even if the *absolute* real-vs-nonsense distributions overlap (no floor settable), the *relative* magnitudes **across hits within one response** still carry shape (one dominant hit vs a flat diffuse cluster), and C6 asserts nothing a separation-failure would falsify. So C7 should **not** be "change nothing in the render" — it should be "**drop to C6, the claim-free substrate, and retire only the verdicts, with receipts.**" The render still improves; it just stops interpreting.

**One honest caveat that should gate even C6:** the survey must measure **within-query cosine spread**, not only cross-query separation. If cosines are flat *within* a result set too (every hit ~equal regardless of query), then C6 is also inert and true "change nothing" C7 is the honest call. C6 is justified iff within-set spread is informative even when cross-query separation fails.

### 6. What the candidate space misses / my design

- **(a) The combination is the design.** C6 substrate + aggregate-only C2 verdict. Neither alone is as good; the space presents them as rivals.
- **(b) Survey must also measure within-query spread** (justifies C6 independently of any floor — see Q5).
- **(c) Arm provenance as *description*** (the salvageable sliver of C4): tag each hit `both-arms` / `vector-only` / `lexical-only`, never as confidence. `lexical-only` warns me a hit matched my tokens but may be semantically off; `vector-only` warns me it's semantically near with no term overlap (could be the right concept under a different name — or topic drift). I read those failure textures differently and would act on them (e.g., `vector-only` when I pasted an exact symbol name = suspicious). Orthogonal to magnitude, cheap.
- **(d) Extend lore's "nearest path" honesty to semantic near-misses.** On the aggregate absence-verdict, don't just say "broaden the query" — say **"no chunk shares your key terms; the feature may be unindexed or named differently — nearest indexed symbol/path is `X`."** That turns "no answer" from a dead end into a redirect. This is the single highest-value addition for me, and it's in lore's existing idiom (a path-miss already teaches the nearest real path).

### Net verdict

Ship **C6 (raw per-hit magnitude, both arms, described-not-judged) as the always-on substrate**, and layer **C2's aggregate "no confident match" verdict** on top **only if the survey shows the composite separates** (precision-gated at ≤3% false-absence on real queries); **reject C3 and C5 outright — my live receipts show both invert on nonsense** — and keep C0's confidence-silence out, because a silent all-clear over a 0.0286 nonsense hit misleads me worse than saying nothing.

---

## 5. Sonnet informant section (verbatim)

### Probe receipts (live server, current status quo — bare scores, no weak-match flag anywhere)

**Probe 1 — nonsense/adversarial:** `"quantum blockchain drone delivery smart fridge firmware for pet grooming"`
- Top hit: `[SOURCE:loremaster/tests/test_scout.py:1065]` score **0.02862400327131466** — `class TestLiveNotificationDelivery: """A LIVE notification drains pending WITHOUT waiting a poll interval."""` (zero semantic relation to the query)
- 2nd hit: `[SOURCE:loremaster/tests/test_calibration_counting.py:245]` score **0.01639344262295082** — exactly 1/61, `class TestClientOwnershipLifecycle:`
- Notice: `+11 entries elided by budget=1100 — top elided ... score=0.016`

**Probe 2 — real code question:** `"how is the RRF fused score computed and where does the search score floor get applied"`
- Top hit: `[SOURCE:REPORT-slate-scout-seams.md:73]` score **0.016741147768986983** — genuinely on-topic (discusses `SearchPipeline._to_result` as the flag seam), but scored *right at* the eventual p5 floor (0.0167) — a real, relevant hit sitting a hair's breadth from where it'd get flagged as "weak."

**Probe 3 — borderline plausible-but-absent:** `"rate limiting middleware for the MCP server's HTTP endpoints"` (no rate limiter exists in this repo)
- Top hit: `[SOURCE:loremaster/loremaster/auth.py:263]` score **0.027629397679130595** — `class OriginValidationMiddleware` — a real, richly-documented, confidently-worded ASGI middleware class, but it's a DNS-rebinding Origin-header guard, not rate limiting. Fully plausible, wrong answer, comfortably mid-pack score.

**Probe 4 — plausible-but-absent feature:** `"GraphQL API endpoint for querying the code graph"` (lore has no GraphQL surface at all — it's an MCP tool server)
- Top hit: `[SOURCE:loremaster/tests/test_graph.py:46]` score **0.03177805800756621** — a bare import list from a code-graph test file. Nothing about GraphQL. This is the **highest score across all five of my probes**, one tick below the survey's measured max (0.0323), attached to the single most definitively wrong answer I got.
- 2nd/3rd hits also test_graph.py / test_cli.py, scores 0.0274 / 0.0238 — all three top hits piling onto the same "graph" lexical/semantic magnet, none touching the actual question.

**Probe 5 — real query, modest score:** `"how does the memory store handle recall_memory ranking and boosting search results"`
- Top hit: `[SOURCE:loremaster/tests/test_search.py:1113]` score **0.018634987188446306** — `test_memory_cap_elision_is_announced`, genuinely on-topic (memory-cap elision/notice architecture).

I also grepped `loremaster/search.py` directly — confirmed the in-tree-but-undeployed C0 code (`_WEAK_MATCH_WARNING_TEMPLATE`, `_SEARCH_SCORE_FLOOR`, `_all_hits_weak_notice`) exists but isn't live yet, matching what I saw: every probe returned a bare `"score": <float>` JSON field with **zero interpretive framing**, no verdict text anywhere.

---

### 1. What I'd actually do on seeing each render

- **C0 (shipped floor on fused score):** Would have flagged my Probe-2 hit (0.0167, genuinely relevant) as borderline while leaving Probe-1's nonsense top hit (0.0286) and Probe-4's completely-wrong GraphQL hit (0.0318 — the *highest score I saw*) unflagged. Net effect: teaches me the exact wrong lesson — that low-scored things are suspect and high-scored things are safe — when my own data says the reverse. I'd learn within a session to ignore it.
- **C1 (pre-fusion cosine banding):** If cosine actually separates, this is the one that would have caught my worst case (Probe 4) — assuming "GraphQL API" embeds meaningfully farther from that import list than a real graph question would. I'd act on the aggregate "no confident match" line by broadening the query instead of citing test_graph.py as evidence of a nonexistent feature.
- **C2 (two-arm AND-gate):** Good instinct for protecting exact-identifier pastes, but my own Probe 4 exposes a flaw: the query lexically overlaps hard on "graph," so the lexical arm may read as strong even though the answer is wrong. An AND-gate keyed on "both arms weak" could **under-catch exactly the case I most want caught**, because a topically-adjacent wrong answer often wins on lexical overlap even when semantically off-target.
- **C3 (top-vs-second margin):** I'd predict, same as the design doc, that this fails for the same rank-quantization reason — cheap to test, I wouldn't bet on it.
- **C4 (arm-agreement decode) as a confidence signal:** Actively wrong — my nonsense probe's runner-up hit landed at the exact single-arm floor (1/61) and the winner clearly had cross-arm agreement; "both arms agree" reads as *more* confident precisely when the corpus has nothing better to compete with it. Correctly rejected. As bare *descriptive* metadata (not a verdict) it's mildly useful — "matched by lexical only" would tell me to try a more literal query.
- **C5 (percentile framing):** My Probe 4 score (0.0318) is essentially at the survey's p95–max band for REAL queries — under C5 this would render as an elite, top-percentile match for a feature that does not exist. Confirmed actively dangerous. Reject.
- **C6 (raw cosine, no verdict):** Useful but leaves all interpretation to me every single hit, at nonzero constant cost across a whole session of searches.
- **C7 (null verdict):** Acceptable floor, but see Q5 — I still want something to change even here.

### 2. Ranking + amendments to my top choice

**Ranking (best → worst):** C1 (gated) + C6-style number > C2 (with a fix, below) > C6 alone > C0 > C7 > C3 > C4-as-verdict > C5.

My actual top choice is a **hybrid of C1 and C6**, not C1 alone:
- Always render the bare cosine number on **every** hit, confident or not (a handful of tokens — "sim 0.51"). Verdict-only-when-weak (pure C1/status-quo philosophy) means I get zero magnitude anchor among hits that all clear the floor — 0.45 and 0.85 both read as "not flagged," but they are not equally trustworthy, and I can't tell without a number.
- Verbal weak-flag text appears **only** below the measured floor, as designed — that's the expensive, LLM-legible part and it should stay rare.
- **Decouple the per-hit floor from the aggregate "no confident answer" floor.** The per-hit annotation should stay conservative (low false-positive, ~p5) since it's advisory and I read the content regardless. The aggregate "stop and broaden" verdict should sit at a *higher*, more sensitive bar (closer to p15–p20) because that's the one signal that can actually save me a wasted trust round-trip — I'd rather it fire a bit more often at low cost than miss cases like my Probe-4 GraphQL non-answer.
- If C2's AND-gate ships instead, fix the lexical-overlap loophole my Probe 4 exposed: gate the "protect exact lookups" carve-out on whether the **query itself contains a literal identifier token found verbatim in the hit** (i.e., a real symbol-paste), not on the BM25 arm's raw score — otherwise topic-word overlap (like "graph") launders a wrong answer past the AND-gate the same way it fooled RRF.

### 3. False-flag asymmetry

Per-hit flag on a hit that IS the right answer: cheap for me. The content is still fully rendered, I read it regardless, and worst case I hedge a sentence in my own answer or do one confirming read. I'd tolerate **15–20%+** false-flag rate on the per-hit annotation without complaint.

The aggregate "no confident answer" verdict is different in kind — it's the one thing that could make me stop searching or discount content I should have used. But note the shipped wording is advisory ("broaden the query or treat these as speculative"), not declarative ("no answer exists") — that softness matters. Given the soft phrasing, I'd tolerate roughly **10–15%** false-fire-on-actually-correct-content before it starts costing me real answers; if the phrasing were ever hardened to something absolute, my tolerance would drop close to zero.

More important than either false-flag rate: the asymmetry runs the *other* direction. My worst outcome across all five probes wasn't a flag on a good hit — it was **zero flag on my single worst hit** (Probe 4, 0.0318, a fabricated-by-omission "GraphQL API" answer sourced from an unrelated import list). A false negative there is categorically worse than any false positive, because it lets me cite a real `[SOURCE:...]` in support of a claim that source doesn't actually make — a grounded-looking hallucination. Any design should bias toward killing false negatives even at real cost in false positives, precisely because the render keeps full content visible and the false-positive cost is just "I read it anyway."

### 4. The fork: verdict-only vs always-visible (C6)

Neither alone is right for me. Verdict-only-when-weak (current shipped philosophy) is token-efficient but gives me no anchor for *degree* of confidence among passing hits. Always-visible-magnitude (pure C6) hands me full self-calibration responsibility every hit, at constant cost, and depends on me correctly inferring/recalling a threshold rather than being told one. I'm reasonably good at *relative* ordering within one result list, weaker at knowing whether a given absolute number is corpus-wide-good without an anchor — which is exactly what a floor-derived verdict supplies. The hybrid — cheap number always, expensive verdict only when it crosses a measured line — gets me both without doubling cost on the common case.

### 5. If nothing separates (C7 branch)

Even here I want two things changed, not "nothing":
- **Strip or caveat the bare `score` field I already see today.** All five of my probes returned a raw float in the JSON with zero framing. Nothing stops me from inventing my own naive "higher = better" heuristic off that number — which, per the measured truth, is actively backwards (my highest score, 0.0318, went to my worst answer). A silent, undocumented number is a footgun regardless of whether a *new* signal ships. Minimum fix: the tool's own instructions state outright that this score is not a confidence measure and must not be used to decide trust.
- **Don't leave a known-non-discriminating flag live.** An inert-but-present verdict (C0's 2.9%/6.7% numbers) is worse than silence, because its mere existence implies interpretive authority — I will eventually trust it in a low-scrutiny moment. If the survey kills the aspiration, retire the flag text entirely rather than leaving a corpse that still fires sometimes.

### 6. Missing from the candidate space

Two orthogonal signals, neither about score magnitude at all, both visible in my own probes:
- **Source concentration / hit diversity.** My nonsense probe's top-2 hits came from two unrelated test files (no convergence). My GraphQL probe's top-3 hits all piled onto the *same* file (`test_graph.py`) — a single lexically-strong document monopolizing the list rather than independent corroboration. A real answer in a rich corpus often shows multiple independent files converging; an absent-topic query often collapses onto one "least-bad" document. This is cheap to compute (distinct source files among top-k) and structurally different from the RRF pathology, so it's worth adding to the same survey as an independent candidate, not a replacement.
- **Candidate-pool size.** The elision notices told me exactly how many total candidates existed pre-budget (13, 13, 13, 13, 13 in my five probes — suspiciously constant, worth the design team checking whether that's a fixed retrieval-stage `k` rather than a real count). A genuinely near-empty candidate pool for a query is a different and possibly more robust "this doesn't exist here" tell than any per-hit score — worth verifying it isn't just an artifact of a fixed top-k cutoff before treating it as signal.

**Net verdict:** ship C1 gated on its pre-registered survey, rendered as a hybrid (cheap raw cosine on every hit + verbal flag only below a conservative per-hit floor + a separately-tuned, more sensitive aggregate "broaden or treat as leads" floor), fix C2's lexical-overlap loophole before ever adopting its AND-gate, never ship C4/C5 as confidence claims, and regardless of survey outcome stop serving the bare uninterpreted `score` field I saw in every one of my probes today — it's already a footgun and my highest-scoring hit was my worst answer.

---

## 6. The measurement protocol (build-time; constants are measured, never guessed)

**Phase A — feasibility probe** (spike-surreal ws://127.0.0.1:18000, never
production):

1. Cosine capture, preferred form — outer projection over the fused rows:
   `SELECT *, vector::similarity::cosine(embedding, $query_vector) AS
   vector_cosine OMIT embedding FROM search::rrf([...], k, 60)`.
   Verify `search::rrf` passes the `embedding` field through from its
   `SELECT *` subqueries and the outer projection computes.
   **Fallback (a):** project the cosine inside each arm subquery; verify
   projected fields survive fusion. **Fallback (b):** a second bounded query —
   `SELECT id, vector::similarity::cosine(embedding, $qv) AS vector_cosine FROM
   chunk WHERE id IN $fused_ids` — always works, bounded at k.
2. BM25 capture — DEMOTED to optional [informant amendment, D3 in §7]: the
   composite's exact-lookup protection no longer needs the BM25 magnitude (the
   verbatim-identifier anchor replaces it, computable in search.py from query
   tokens × the hit's `ident_text` — no store change). If cheap
   (`search::score(N)` is only legal alongside its `@N@`-annotated MATCHES
   predicate, i.e. INSIDE the fulltext subquery, and must survive fusion),
   capture it for survey completeness; if not, skip without penalty.

**Phase B — survey extension** (`scripts/search_score_survey.py`, same committed
deterministic-survey discipline):

- Capture per-hit: fused score, `vector_cosine`, `bm25_score` (nullable), for
  all k=10 hits — not just the top hit.
- THREE query groups: (i) the 35 real prose eval questions (existing);
  (ii) the 15 fixed nonsense queries (existing); (iii) **NEW: 15
  identifier-shaped real queries** — exact symbol names deterministically
  sampled from the indexed corpus (sorted qualified names, every Nth) — so the
  exact-lookup false-flag channel is measured, not assumed.
- Stats per group: top-hit cosine AND max-cosine-of-response
  (mean/median/p5/p95/min/max); same for BM25 where captured; fused top1−top2
  margin (settles C3 with data — Opus's live probes already show it INVERTED:
  nonsense margin 2.8× the real one).
- [Informant amendments] Additionally capture, per query: **within-query cosine
  spread** (max−min and stdev across the response's hits — gates even the
  substrate, §7 D1); **source concentration** (distinct source files among
  top-k); **pre-budget candidate-pool size**. The latter two are EXPLORATORY
  candidate signals (Sonnet §6) — measured in this run, but any adoption
  requires its own pre-registered follow-up rule, never a post-hoc threshold
  from this same data.
- [Verbatim-anchor channel] For the identifier group, record whether each hit
  contains a query token verbatim in its `ident_text` — the false-flag channel
  for the composite's carve-out (§7 D3).

**Phase C — pre-registered adoption rule** (amended per §7 rulings; operator may
further amend):

- **Substrate gate (D1):** the always-on per-hit magnitude ships iff
  within-query cosine spread is informative (the response's hits are not flat —
  e.g. median within-query max−min spread ≥ 0.05 across the real groups). If
  cosines are flat within result sets regardless of query, the substrate is
  inert and does not ship.
- **Verdict floor (D2 — precision-first):** admissible floors are those with
  aggregate false-fire ≤ 5% on the UNION of prose-real + identifier-real
  queries (wording stays hedged-advisory; a hardened wording would drop the
  tolerance near zero — Sonnet). Among admissible floors, choose the one with
  MAXIMUM nonsense catch. Adopt the aggregate verdict iff that catch ≥ 60%
  (≥9/15). Two-tier floors (a more sensitive aggregate bar, Sonnet's p15–p20)
  are admissible only as one of the candidate floors under the same ceiling.
- **Composite carve-out (D3):** the verdict's condition is
  `max cosine of shown code hits < floor AND no shown hit carries a
  verbatim-identifier anchor` (a query token appearing exactly in the hit's
  `ident_text`). Raw BM25 magnitude is NOT the gate (topic-word overlap
  launders wrong answers — Sonnet Probe 4).
- If no admissible floor catches ≥ 60% → **C7-as-amended**: retire the
  aspiration AND the S4 flag corpse entirely (no decorative confidence
  surface), resolve finding #68's follow-up with the receipt table, add the
  teaching sentence ("scores are rank-fusion artifacts; judge hits by content,
  not score") to the tool surface — and the substrate still ships if it passed
  its own gate.
- Constants land in search.py as MEASURED constants with the full comment
  discipline `_SEARCH_SCORE_FLOOR` already models; the run's summary.md + jsonl
  cited in the builder's report.

**Model/plumbing changes if adopted:** `Candidate` gains
`vector_cosine: float | None` (extra="forbid" stays; the field is explicit),
`_to_candidates` maps the projection, `_to_result` / `_all_weak_notice` swap
their predicate from the fused floor to the cosine floor, S4's fixtures repoint
(`_FixedCandidatesStore` grows a cosine knob). The weak-render tests keep their
hostile-fixture obligations.

---

## 7. Synthesis and recommendation (Fable, after both informant returns)

### 7.1 Three-way convergences — design law

1. **The aggregate absence-state is the prize.** All three clients
   independently: semantic search cannot return empty, so absence is the one
   fact content-reading cannot cheaply establish — every "not here" answer
   currently costs a 1–3-call verification spiral. A calibrated, hedged
   "no confident match" notice is the absence-verdict analogue of the
   counted-elision grammar: it converts "should I keep looking?" into a
   zero-call decision. This is where a tool-side signal has real leverage;
   per-hit decoration has almost none (all three mostly ignore bare scores and
   judge by content).
2. **Magnitude or nothing.** Only pre-fusion magnitudes have a physical basis
   for discrimination. The rank-code derivatives are now dead WITH LIVE
   RECEIPTS, not just theory: C3's margin measured INVERTED (nonsense margin
   2.8× the real one — Opus); C5 would have rendered Sonnet's worst answer
   (0.0318, absent feature) as an elite top-percentile match; C4-as-confidence
   is inverted by construction (nonsense = perfect arm agreement). All three
   candidates are permanently rejected as confidence signals.
3. **Always-on magnitude substrate + rare gated verdicts** — both informants
   independently derived the same hybrid against the consultant's
   verdict-only preference (see D1): a claim-free number on every hit (read
   RELATIVELY within one response — no calibration memory needed, cannot be
   wrong, survives the null branch) plus verdict text only where a measured
   floor licenses it.
4. **The false-flag asymmetry is two-tier.** Per-hit flags are nearly free
   (content is rendered and overrides them; tolerances 10–20%). The aggregate
   verdict is the guarded surface — it licenses skipping verification and
   disables its own correction (it tells the client to discount the very
   content that would correct it — Opus). Precision is pre-registered there.
   And the deepest cost today runs the OTHER way: the un-flagged wrong answer
   (Sonnet's Probe 4) is a **grounded-looking hallucination channel** — a real
   `[SOURCE:...]` citation attached to a claim the source doesn't make.
5. **Silence and corpses both lie.** C0's near-inert flag trains "no flag =
   all clear" (both informants); a known-non-discriminating flag left live
   implies interpretive authority it doesn't have. If the aspiration dies at
   measurement, the S4 flag text retires entirely — no decorative confidence.
6. **The served fused score is a standing footgun.** Every probe returned a
   bare `"score": <float>` that invites a "higher = better" heuristic which is
   measurably backwards on the trap cases. The client-visible number must be a
   magnitude, or carry explicit non-confidence framing (see D4).

### 7.2 Disagreements — named, with rulings

**D1 — verdict-only-when-weak (Fable §3) vs always-on magnitude substrate (both
informants).** RULED FOR THE INFORMANTS; the consultant concedes. Two of three
consuming clients, independently, with grounded mechanics: within-response
relative reading needs no cross-call calibration; a bare number makes no claim
and cannot open a confident-wrong channel; it survives the null branch. Cost
~4–6 tokens/hit. (Precedent: the T10 downgrade — informants correcting the
synthesizing model is this protocol working as designed.) One consultant
condition carried into the spec: the substrate ships only if within-query
spread proves informative (Opus's own gate) — a flat number on every hit is
noise, not signal.

**D2 — aggregate false-fire tolerance: ≤2–3% hard-5 (Opus) vs 10–15% given
advisory wording (Sonnet) vs ~5% hedged (Fable).** RULED: precision-first,
ceiling 5% on the union of real groups, advisory wording MANDATORY (hardening
the wording voids the ruling); among admissible floors take maximum catch —
which grants Sonnet's sensitivity whenever the data allows it without ever
breaching Opus's ceiling. Rationale: the law's under-claim/confident-wrong
asymmetry plus Opus's self-correction argument outweigh recall appetite; recall
is bought back through the carve-out design (D3) and the redirect (7.3), not
through a looser floor.

**D3 — the exact-lookup protection: BM25-magnitude arm (Opus/C2-as-briefed) vs
verbatim-identifier anchor (Sonnet's amendment).** RULED FOR SONNET'S
AMENDMENT: topic-word overlap ("graph") launders a wrong answer past a
BM25-magnitude gate exactly the way it fooled RRF; a verbatim identifier token
from the query appearing in the hit's `ident_text` is the honest signature of
a symbol-paste. Bonus: computable in search.py from data already served — the
BM25-capture leg of the store work is demoted to optional.

**D4 — the wire `score` field: strip/rename (Sonnet) vs leave-with-framing.**
Nobody defended serving it bare; whether to drop it from the served entries,
rename it (e.g. `fusion_rank`), or keep it with an instructions caveat is a
WIRE-SHAPE decision (response pins, compat) outside client-fit judgment —
carried to the operator as a named decision point. Client-fit minimum: the
rendered text must stop presenting the rank code as the salient number once
the substrate ships.

### 7.3 Informant additions accepted into the spec

- **Within-query spread measurement** (Opus) — gates the substrate (Phase C).
- **Nearest-indexed redirect on the absence verdict** (Opus): the notice names
  the top hit's identity — *"nearest indexed: `auth.OriginValidationMiddleware`"* —
  turning "no answer" into a redirect, in lore's existing miss-teaches idiom.
- **Source concentration + pre-budget pool size** (Sonnet) — measured as
  exploratory signals in the same survey run; adoption only via their own
  pre-registered follow-up (no post-hoc thresholds from the same data).
- **Retire-the-corpse rule** on the null branch (Sonnet).
- Flag for the builder (Sonnet, incidental): the constant "13 entries"
  pre-budget count across five different probes — likely structural
  (k=8 hits + memory cap + headers) but worth one look; if it IS the fixed
  retrieval `k`, the elision notice's "all N entries" phrasing is honest but
  the pool-size signal above is void.

### 7.4 The recommended design — magnitude substrate + gated absence verdict

One design, three layers, each independently honest:

1. **Store:** capture per-hit raw query↔chunk cosine (Phase A probe with
   specced fallbacks — one of the three forms is guaranteed to work).
   `Candidate` gains `vector_cosine: float | None`.
2. **Substrate (unconditional once its gate passes):** every code hit renders a
   compact magnitude — `sim 0.51` — claim-free, read relatively within the
   response. Ships on EITHER branch of the verdict measurement.
3. **Verdicts (survey-gated, Phase C):** the per-hit weak line (conservative
   cosine floor; kept — it is cheap, already built as a seam, and aids
   skimming) and the aggregate hedged notice:

   > `no confident match: best hit similarity 0.31 is below the range real
   > answers measure on this corpus (≥0.44) and no hit matches your
   > identifiers verbatim — likely no direct answer indexed; nearest indexed:
   > 'auth.OriginValidationMiddleware' — broaden the query or treat these
   > hits as adjacent-topic leads`

   firing iff max shown-hit cosine < floor AND no verbatim-identifier anchor.
4. **Replace, don't stack:** `_SEARCH_SCORE_FLOOR` and the S4 fused-floor
   templates retire when the cosine verdicts adopt; on the null branch they
   retire anyway (7.1 #5) in favor of the teaching sentence, and the substrate
   still ships if spread-informative.

**Sizing: build THIS cycle.** One builder task: store projection + model field
+ survey extension + render swap; every render seam already exists
(`_to_result`, `_all_weak_notice`, `_FixedCandidatesStore` grows a cosine
knob; S4's tests repoint with their hostile-fixture obligations intact). The
NAMED DECISION POINT is the Phase C receipt table — it, not anyone's judgment,
selects adopt / composite-adjust / null. Token cost: substrate ~4–6
tokens/hit; verdicts ~25–50 tokens only when firing; C0's templates retire on
either branch.

### 7.5 Decisions needed (operator)

1. **D4 wire-shape:** drop vs rename vs caveat-only for the served fused
   `score` field (response-shape pins/compat implicated).
2. **Phase C bars:** confirm or amend the pre-registered ceiling (5%
   false-fire) and catch bar (60%) before the builder runs the survey —
   amending after seeing the table would un-pre-register the rule.
3. **Sequencing:** this build item (S4b) within the slate cycle — the design
   is ready to execute as one task.


---

## Outcome (slate-lead close-out, 2026-07-07)

Executed as §7.4 specced. First survey run: D1 PASS; D2 floor 0.6661, catch 40% —
DO-NOT-ADOPT under the locked bars, with the failure isolated to the D3 carve-out
firing on bare English words (9/15 nonsense anchored; one genuine identifier paste
missed). Operator ruled the spec-intent fix (option b): anchor requires an
identifier-SHAPED token. Re-run under UNCHANGED bars: floor 0.5828 (real
max-cosine p5), false-fire 4.0% (2/50), catch 100% (15/15) → **ADOPT**. Substrate
live (D1 passed both runs). Shipped in commits d4f283f (dark machinery) +
94a9568 (adoption). External validation: 2026-07-06-weak-match-external-validation.md
(all elements confirmed; floor bound to the embedder+prompt configuration —
re-measure on any change). D4 wire-shape: score stays on the wire demoted in
render; rename ledgered. Exploratory signals (source concentration, pool size)
remain unadopted pending their own pre-registered rules.
