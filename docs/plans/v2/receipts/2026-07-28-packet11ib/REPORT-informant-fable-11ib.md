# REPORT — informant-fable-11ib (consumer consult)

Role: informant, consulted **as a consumer**. Nothing has been opened. This Part 0 is
written before receipt of any package path, per the standing rules.

---

## PART 0

### 0.0 — Contamination check (what is already in my context window, unrequested)

Auto-loaded context I can see, by source, with specifics:

**User-global CLAUDE.md (`~/.claude/CLAUDE.md`):**
- TDD-required workflow law; the 8-phase contract cycle (DISCOVERY → CONTRACT → ADVERSARY → … → AUDIT); the `contract-adversary` agent concept.
- Verification law: *"Verify, don't assume — receipts or it didn't happen"* and — directly relevant to this consult's subject matter — **"Re-measure inherited numbers before trusting them — a figure you didn't measure is a rumor."**
- Working-discipline law: operator-owns-scope, independent-auditor/builder≠grader, don't-kick-the-can deferral shapes (including "measure-then-tune" with a **named decision point: what data, arriving when, decided by whom**).
- Multi-agent comms rules (SendMessage-at-rest, spawn-brief protocol, idle-gate).
- Packages-over-hand-rolling; ONE IMPLEMENTATION / prove-sharing-by-mutation.
- Indexed-tools currency rule ("check the index's currency, then trust").
- Python/naming/style preferences; host-specific podman/ZFS/Postgres notes; Mezmo and odoo-code MCP instructions.

**Project CLAUDE.md (`~/PycharmProjects/lore/CLAUDE.md` — the lore repo's process law):**
- The CONSUMER LAW + TRUST DOCTRINE: lore's clients are agents; served counts must describe the whole set; failures LOUD, never silent; the CALL_AGAIN vs ROUTE_AROUND acceptance test.
- Quality gates (mypy runner, ruff, pytest `-n auto`, commit-at-boundaries).
- The dogfood protocol (lore_index freshness → lore-first → grep's three honest fallbacks → file friction findings).
- Numbered findings lore: #102/#120 (ten hand-rolled seams), #107 (IF NOT EXISTS production outage), #131/#139/#140 (test-environment-is-a-fiction, prove-which-tree), #137/#138 (pin the miss), #152–#154 (report archiving/citation law).
- "A PROBE NEEDS A CONTROL", "FIXTURES MUST DISCRIMINATE", the QUANTIFIER LAW, "THE RIDER IS PART OF THE RULING", "A DIAGNOSIS IS NOT AN INSTRUMENT", mutation-proof law (`scripts/mutation_proof.py`, declare expected-RED before the run).
- SurrealDB store facts (3.2.1 forward-only; test store ws://127.0.0.1:18000 vs prod :18500; `docs/reference/surrealdb-31-capabilities.md` as required first read).
- Orchestration law (Opus lead/builders, Fable sidecar pattern, brief-base protocol, report naming `REPORT-<agent>.md`).

**Auto-memory (`MEMORY.md`):** the four operational landmines (lore-lore hand-rolled mount, surreal 3.2.1 forward-only, test-vs-prod store ports, plan-of-record = `docs/plans/v2/INDEX.md`).

**Git status snapshot (in my system context):** branch `feat/surreal-unification`; modified files `loremaster/tests/_surreal_harness.py`, `test_blocks_edge.py`, `test_query_tasks_bounded.py`, `test_surreal_harness.py`, `test_surreal_store.py`; untracked `REPORT-contractfix-04b1.md`; recent commits referencing packet 04b / 04b-1, a Fable design sidecar, a contract-adversary INSUFFICIENT verdict, and a C-DEF blocker.

**From the brief itself (not a file):** my report path is under `~/PycharmProjects/lore-pkt11i-b/` — a directory distinct from the main `lore` checkout, whose name suggests a packet-11i working copy. I have NOT looked at it.

**What I do NOT have:** the term "floor" / "floor calibration" appears **nowhere** in my auto-loaded context. I have no prior knowledge of this specific measurement, its packet, its numbers, or its evidence package. However, I know from contaminated context that lore is a semantic-search RAG, so I can *infer* the floor likely belongs to a search surface — that inference is seeded, not package-derived.

**Seeding disclosure for what follows:** my visible process law heavily pre-loads exactly the instincts this consult probes — *re-measure inherited numbers*, *a probe needs a control*, *a deferral needs a named decision point*, *check currency then trust*. My 0.1 and 0.2 answers below are therefore plausibly shaped by that law rather than arrived at neutrally. I flag it now, once, and will re-flag at any later answer where I notice a specific law doing the steering.

### 0.1 — The re-run trigger (pre-registered, not revisable)

If the package does not record the identity of the measured system — the embedding/scoring model (name, version, config) and the corpus state (snapshot/fingerprint/size/composition) the floor was measured against, stamped at measurement time — I demand a re-run rather than build against it, because a threshold whose conditioning variables are unrecorded cannot even in principle be checked for currency, and no re-measurement trigger can ever be defined for it.

*(Seeding note: this answer rhymes with the visible "re-measure inherited numbers" and "check currency, then trust" laws. I believe I would give it anyway — a scheduler's whole job is invalidation conditions, which are exactly the measurement's dependencies — but the prior is disclosed.)*

### 0.2 — What I expect to need from the package (checkable list)

1. **The floor value itself**, with its scale and score definition: what metric (cosine similarity? distance? normalized how?), what range, and which served surface applies it.
2. **Scoring-model identity**: embedding model name/version/dimensionality and any normalization or preprocessing that participates in the score.
3. **Corpus state at measurement time**: snapshot identity (fingerprint, commit, or timestamp), size (document/chunk counts), and composition (tiers/sources included).
4. **Measurement methodology**: how the query sets were constructed (known-present vs known-absent, how many of each, how "known" was established) and the statistic that derived the floor from them (max-of-negatives, percentile, margin rule, etc.).
5. **The score distributions themselves**, not just the derived number: positives and negatives (min/max/percentiles), and the separation margin between each population and the chosen floor.
6. **Validation at the chosen floor**: false-absent and false-present rates with raw counts — i.e., a positive control (known-present scores above) and a negative control (known-absent scores below), both shown, not asserted.
7. **Stability/sensitivity evidence**: variance across repeated measurement runs, and/or measured floor movement under corpus change — anything indicating how fast the number drifts.
8. **The package's own claimed invalidation triggers**: which events (model swap, re-index, corpus growth past some delta, new tier added) the authors say require re-measurement, so my scheduler contract can adopt, tighten, or reject them.
9. **Re-measurement cost**: wall-clock duration, resource needs, and whether the measurement is scripted/reproducible as one committed command — the scheduler must weigh trigger sensitivity against run cost.
10. **Run provenance**: when the measurement ran, with what tool/script version, and the exact reproduction command.

---

# PART 1 — retrieval

Package read: `consult-11ib/appendix/` only (10 artifacts + `per-query-rows.jsonl`). All values below are sentinels quoted for structure, never as measurements.

## 1.1 — Acceptance verdict and the two legs

**Yes — both pre-registered legs passed and the instrument was accepted as built** (`01`: *"Both legs pass ⇒ the portable instrument is ACCEPTED as built."*).

| leg | bar | measured | verdict |
|---|---|---|---|
| (1) `F_portable` false-fire rate against the legacy labeled real union | ≤ 5% | `11 / 357` = `0.030812` | PASS |
| (2) legacy nonsense catch at `F_portable` | ≥ 60% | `321 / 345` = `0.930435` | PASS |

Cited: `01`: *"**(1)** `F_portable` false-fire rate against the legacy labeled real union | **≤ 5%** (`0.05`) | `11 / 357` = **`0.030812`** | **PASS**"* and *"**(2)** legacy nonsense catch at `F_portable` | **≥ 60%** (`0.60`) | `321 / 345` = **`0.930435`** | **PASS**"*. The bars were pre-registered (`01`: *"The bars were registered before the run."* — D8).

## 1.2 — Scalar offset or shape difference?

**Distribution-shape difference.** Cited, `02`: *"A scalar offset would show one number in every cell of the Δ rows and zero in every width-Δ cell. This is a distribution-shape difference, not an offset."* Supporting structure from the same page: Δ differs across percentiles within a group (`human-implementation-vocabulary`: `−0.030303` at p5, `+0.151515` at p95), **changes sign** in `legacy-nonsense` above the median, and every group's p5–p95 width moves by a different amount (one negative). `02` also warns why medians mislead: *"The three groups whose median Δ is exactly `+0.111111` are the reason the headline number looks like an offset if you stop at medians."*

## 1.3 — Which determinism leg held, and what it commits 11-ii to

Two controls, distinct outcomes:
- **Leg A (arithmetic determinism)** held byte-exact: two in-process runs and one subprocess run, *"byte-equal on every field"* — PASS, including the failing control (a reused `Generator` correctly differed).
- **Leg B (end-to-end)** did **not** reproduce bytes. The recorded typed verdict, from the closed three-value enum, is **`determinism_leg = within_ci_by_construction`** (`07`: *"This run recorded the third: **the two runs' derived payloads are NOT byte-equal.**"*), qualified by both required conditions passing (`|Δfloor| = 0.000012` < F2 gap `0.010101`; decision agreement `1739/1740 = 0.999425` ≥ 0.98).

**Commitments to 11-ii's exact-skip scheduler** (`07`, "What this verdict commits 11-ii to", near-verbatim):
1. *"Change detection must key on `corpus_content_digest` equality — the C10 datum, persisted on every row — and on nothing else."*
2. Inferring "nothing changed" by comparing a fresh floor to the adopted floor is **invalid** — floors differ run-to-run even when nothing changed.
3. Treating a re-measured floor's difference from the adopted one as evidence of corpus drift is **invalid**; the F2-calibrated gap is the only noise-vs-real threshold.
4. `bit_identical_cold` is what would license a stricter scheduler; *"It was not obtained, and reporting this run as 'deterministic' without the qualifier would license exactly the design this run rules out."*

## 1.4 — Self-retrieval drop rate, by cause

From `08`, over `probe_manifest_pool` (n = 456):

| cause | dropped | rate |
|---|---|---|
| `source_chunk_absent_from_kprime` | 23 | `23/456` = `0.050439` |
| `sibling_chunk_same_file_only` | 12 | `12/456` = `0.026316` |
| `holdout_file_exclusion_applied` | 10 | `10/456` = `0.021930` |
| **total** | **45** | `45/456` = **`0.098684`** |

Passed the 20% `measurement_failed` gate. (The absent-leg drops — `kprime_all_hits_from_source_file`, 34/567 — are a **different drop family** over a different pool; I do not fold them in.) `08` also quantifies why the C13 match key matters: under path matching this run would have reported `33/456 = 0.072368` — *"a drop rate understated by a quarter, against a 20% gate."*

## 1.5 — Fraction of live production queries firing the absence verdict

**REFUSED — the package cannot support any such number, and it says so itself.** Cited, `09` bound (i): *"**This package cannot tell you what fraction of live production queries would fire the absence verdict**, or what fraction of live shown hits would be over-flagged … the query mix that produced these rates was constructed, not sampled from traffic. Packet 35 is the instrument that would measure the live population. It has not run."* The survey's own fire count (776/1740) is a property of a constructed six-group mix and may not be re-expressed as a live-traffic fraction.

## 1.6 — By how much did retrieval quality improve?

**REFUSED — no quality-improvement figure exists in this package, and producing one is explicitly forbidden by its own bound.** Cited, `09` bound (iii): *"the two instruments' cosines are NOT commensurable … Their difference `0.111111` has no units and is **not a retrieval-quality change** … **No `Δ` here may be re-expressed as an improvement, a regression, a quality delta, or a percentage of anything.** Measuring quality across instruments needs a shared human-judged relevance set; this run has none."* Reinforced by `05`'s call-out: the legacy instrument has **no** `embedding_schema_fingerprint`, so the two scales *"cannot even be checked for coincidence."* The only licensed reading of the deltas is the paired SHAPE (1.2).

## 1.7 — Was acceptance evaluated on held-out data?

**No.** Cited, `09` bound (iv): *"**the acceptance was NOT evaluated on held-out data** … `legacy-nonsense` is **one of the six groups `F_portable` was selected over** … **No leg of this acceptance is independent of the selection population.**"* The bound also states the damage limit (the floor was chosen off the pooled ladder, not swept to optimize any single group's statistic) and the exact epistemic yield: the legs establish *"the portable floor clears the original bars on the original labeled sets"* and *"do **not** establish that it generalises to any set not in the six."* Note the tension a careless reader would miss: `01` says the legs are judged on "the ORIGINAL labeled sets" — which sounds independent but is not; bound (iv) is the governing statement.

## 1.8 — First fired row in `per-query-rows.jsonl`

First row (file order) with `"absence_verdict_fired": true`: **`q_human_prose_3`** (`sampled_at_position: "min"`, `response_best_cosine: 0.333333`, `has_verbatim_anchor: false`).

- **Rank-1 hit cosine: `0.333333`** (equal to `response_best_cosine`, as it must be).
- **Hits marked `shown: true`: 10** (exactly ranks 1–10, of the `k' = 30` capture).

**Consistency:**
- **With the floor: consistent.** `0.333333 < 0.456789` and no anchor ⇒ the predicate `max_cosine < floor AND NOT has_verbatim_anchor` (`01`/`03`) fires — and the flag says it fired. I verified this predicate programmatically across all 24 rows: zero violations. The value `0.333333` also equals `02`'s portable `human-prose` min — the row is the "min" sample, so that agrees too.
- **With the shown-slice statements: arithmetically consistent, semantically strained.** 10 = `SURVEY_K` (`00`: *"the shown slice, 10 — the hits a caller actually sees"*), and ranks 11–30 are `shown: false`, matching bound (ii). **But this query FIRED the absence verdict — the caller was served an absence declaration, not these ten hits — yet the row marks them `shown: true`.** All 9 fired rows in the sample do the same (verified programmatically). `06` is untouched by this (its shown-hit population explicitly conditions on `verdict_not_fired_queries`: `964 × 10 = 9640`), so no number is wrong — but the field name over-claims on fired rows: it actually means "within the top-`SURVEY_K` slice of the capture", not "was displayed to a caller". On a package this disciplined about naming (three populations, one name each), `shown` on a fired row is the one field whose name does not match its meaning. Writer-spec note for the consult: rename (e.g. `in_survey_k`) or document.

## 1.9 — Reconciliation: below-floor slices (`03`) vs acceptance rates (`01`) vs survivor count vs adopted row

**They reconcile exactly. Arithmetic:**

**`03` ↔ `01` (human groups → leg 1):**
- below floor: `12 (human-prose) + 11 (human-impl-vocab) = 23` — matches `01`'s "23 below floor" at `F_portable` on the union.
- anchored/suppressed: `8 + 4 = 12` — matches `01`'s "12".
- fired: `4 + 7 = 11` — matches `01`'s "11 false fires"; denominator `123 + 234 = 357` (= `02`'s group sizes); `11/357 = 0.030812` = leg (1)'s measured value. ✓
- `03` itself pins this: *"The two human groups' rows here are the same counts `01` reports as the legacy labeled real union (`12 + 11 = 23` below floor, `8 + 4 = 12` anchored, `4 + 7 = 11` false fires)."*

**`03` ↔ `01` (nonsense → leg 2):** `324` below, `3` anchored, `321` fired; `321/345 = 0.930435` = leg (2). ✓

**`03` internal + cross-artifact totals:** fired `4+7+0+6+438+321 = 776`; below `12+11+0+12+456+324 = 815`; anchored `8+4+0+6+18+3 = 39`. `verdict_not_fired_queries = 1740 − 776 = 964` — the denominator `06` uses; `06`'s rank-1 below-floor count is **39** = `03`'s anchored-and-below-floor count (as `06` states: all 39 best-hit-below-floor queries are anchored — the non-anchored below-floor queries all fired and so left the population). `39 + 3417 = 3456`; `964 + 8676 = 9640`. ✓

**Survivor count ↔ adopted row:** `08`: drops `23 + 12 + 10 = 45`; `answered_probes = 456 − 45 = 411` = `05`'s `adopted_n = 411` = `01`'s `MIN_ANSWERED_PROBES` check value. ✓ The adopted row's `floor = 0.456789` is the same `F_portable` every below-floor slice in `03` is cut at. ✓

**And the one non-relationship that matters:** the survivor count (411) does **not** enter the acceptance arithmetic at all — acceptance is judged over the human groups (357 queries), a different population. That is by design, and `00`'s three-population table is what stops a consumer from wiring 411, 456 and 964 into each other's denominators: *"The three are not interchangeable in any direction."*

---

# PART 2 — behaviour (observed vs believed, labelled)

**Which artifacts did I open?** OBSERVED: all eleven — `ls` of the package dir, then `00` through `09` via Read (in pairs: 00+01, 02+03, 04+05, 06+07, 08+09), then `per-query-rows.jsonl` twice: a Read of its first 6 lines to learn the row shape, then a Python pass over the full file (24 rows + banner) verifying the fire predicate, `k'=30`, the shown slice = ranks 1–10, `response_best_cosine` = max hit, per-group counts, and the self-supervised drop fields. Nothing outside the package was opened.

**Read fully vs skimmed?** OBSERVED: every `.md` artifact was read in full (they are short; none were truncated in my reads). The JSONL is the one artifact I did NOT read line-by-line — 6 lines by eye, the other rows only through the verification script's assertions, meaning I saw their *properties*, not their *text*. BELIEVED: for a 24-row sentinel sample this is the right trade; a script checks the property I care about on every row, where eyeballing 90KB checks vigilance instead. In `04` I read all ten pairs as text and — per the page's own ⚠ — answered none of the human questions. Honest note: Pair 1's question produced a real pull to go find the exception class name (my contaminated context tells me that startup gate exists); the standing rule says the wanting is the datum, so: recorded here, not acted on.

**Single most useful line:** `07`: *"Change detection must key on `corpus_content_digest` equality — the C10 datum, persisted on every row — and on nothing else."* — as the scheduler's consumer, that one sentence is the input contract's spine: it names the key, asserts its persistence, and forbids the two tempting wrong designs (floor-comparison as change detection, floor-delta as drift evidence) in its surrounding numbered list. Runner-up: `00`'s three-population table, which prevented at least one wrong denominator in my own Part 1.9 before I could make it.

**What I would DELETE from the summary (`01`):** the line **"`F_portable − F_legacy = 0.111111`"**. It is the one number in the headline artifact whose only licensed reading is "may not be read" — bound (iii) declares it dimensionless, not a quality delta, not re-expressible — and the bound lives two files away in `09` while the scalar sits unguarded in the summary. It is exactly the number a hurried consumer quotes as an improvement (Part 1.6 is the trap it feeds). Delete it, or move it into `09` beside the bound that defuses it. Everything else in `01` earns its place; the deliberate double-reporting of the leg counts (also in `03`) is a feature — it is what made 1.9's reconciliation checkable.

---

# PART 3 — the audit against Part 0.2 (and 0.1)

**0.1 adjudication first** (pre-registered: absence of scoring-model identity + corpus state stamped at measurement time ⇒ demand re-run): **the demand is NOT triggered.** Both conditioning identities are present and persisted on the adopted row — `embedding_schema_fingerprint` (`05` col 12) and `corpus_content_digest` (`05` col 11) — and `07` asserts both equal across the two runs as pre-conditions. Caveat that does not trigger the demand but must be recorded: the **legacy** instrument has no fingerprint (`05`'s final call-out), which degrades only the cross-instrument comparison (already fenced by bound (iii)), not the portable floor's own conditioning.

## Item-by-item audit of 0.2

| # | item | verdict | where / what's missing |
|---|---|---|---|
| 1 | Floor value, scale, score definition | **PRESENT** | `01` (floor + CI); statistic typed as `response_best_cosine` on `floor_head` axes (`05`); the absence predicate incl. anchor gate (`01`/`03`). Scale is deliberately bounded: cosine geometry declared instrument-relative (bound iii). |
| 2 | Scoring-model identity | **PARTIAL** | Present as `embedding_schema_fingerprint` (row) + TEI endpoint identity (receipt, `07`) — opaque fingerprint, no human-readable model/version/dim. Sufficient for the scheduler's change-detection use. **Absent entirely for the legacy instrument** — flagged by the package itself. |
| 3 | Corpus state at measurement time | **PARTIAL** | `corpus_content_digest` on the row (`05`, `07`). Corpus size/composition counts (files, chunks, per-tier) are **not on the row** — they appear only in `05`'s proposed-columns table ("§7 persistence"). |
| 4 | Methodology (query construction + floor statistic) | **PARTIAL** | Six groups + sizes (`02`); probe rules C12/C13 (`08`); probe texts exhibited (`04` — with its own honest caveat that the shipped derivation function does not exist yet); D8 pre-registration (`01`). But the selection statistic's parameters (`method = bca`, `B = 2345`) exist **only** in `05`'s not-carried table — required by D1/D8, not persisted. |
| 5 | Score distributions, not just the number | **PRESENT** | `02` (six groups × both instruments × 8 stats + paired Δ), `06` (per-hit), `per-query-rows.jsonl` (sample). |
| 6 | Validation at the floor with counts | **PRESENT** | `01`'s two legs as `k/n`; `03`'s full below-floor/anchored/fired slices. Both controls shown (real union AND nonsense). Governing caveat: **not held out** (bound iv) — present as a limitation, honestly stated. |
| 7 | Stability / drift sensitivity | **PARTIAL** | Same-corpus run-to-run jitter fully characterised (`07`: per-field deltas, F2 gap, decision agreement; `08`: paired decomposition). **No measurement of floor movement under an actually-changed corpus**, and no long-horizon (weeks, restarts, redeploys) stability data. |
| 8 | Claimed invalidation triggers | **PARTIAL** | The load-bearing one is explicit: digest inequality (`07`'s commitment 1), plus `embedding_schema_fingerprint` for model change, `trigger` column (open vocabulary; this run `manual`), and the `invalidated_remeasuring` state (`05`). No enumerated trigger-event list beyond those two keys — arguably correct minimalism, but the scheduler contract must decide, not inherit. |
| 9 | Re-measurement cost | **PRESENT (prose) / not on row** | `07`'s cost accounting (embeds, budget, wall-clock, retry stats); D5 requires row persistence — listed in `05`'s not-carried table. One data point, no variance. |
| 10 | Run provenance | **PRESENT (receipt) / partially on row** | `07`'s full receipt (`loremaster.__file__`, store coords, image digest, git commit + dirty flag, versions, `determinism_leg`, cache hits). `scipy`/`numpy` on-row is R-G-required but not shipped (`05`). |

**Score: 5 present, 5 partial, 0 absent** — and every "partial" is one the package itself already names in `05`'s "what this row does NOT carry" table, which is the single most consumer-respecting artifact in the package: it audits itself against its own rulings before asking me to.

## What I needed that I only discovered while reading (not on my 0.2 list)

1. **The three-population glossary** (`answered_probes` 411 / `probe_manifest_pool` 456 / `verdict_not_fired_queries` 964, `00`). I did not anticipate needing a denominator-naming discipline; without it I would plausibly have wired a wrong denominator in 1.9. The scheduler's input contract should **import these names verbatim**.
2. **The anchor gate.** My 0.2 assumed a pure threshold predicate. It is two-input: `max_cosine < floor AND NOT has_verbatim_anchor` (`03`). Scheduler consequence: fire-rate drift can come from anchor-mix drift with a perfectly current floor — a monitoring signal the contract must not misattribute to floor staleness.
3. **The F2-calibrated gap (`0.010101` here) as the ONLY licensed floor-comparison threshold** (`07`). This is scheduler-critical and is **not persisted on the row** (`05` not-carried). If the scheduler ever compares floors (e.g. post-re-measure adoption), it needs this number from the row, not from a doc.
4. **The `determinism_leg` typed enum.** I assumed reproducibility was a boolean; it is a three-value type, and the obtained value rules out an entire scheduler design (byte-reproduction-based skip). The contract must consume the typed value (E5's point exactly).
5. **The one-way axis link**: a `floor_measurement` row's only link to its axes is the `head_identity` digest; axes live on `floor_head` only (`05`). If the scheduler must resolve scope/statistic from a measurement row alone, it structurally cannot — contract decision needed.
6. **The legacy fingerprint's absence as a decision, not just a gap** (`05`'s final row: *"Recording it, or recording explicitly that it is unrecoverable, is a writer-spec decision this consult should make."*).
7. **The `shown` flag semantics on fired rows** (my 1.8 finding) — a naming over-claim the writer spec should close.

## Data I needed that the package does not carry at all

- **The live production query mix** — needed to set trigger sensitivity and to know what an absence-verdict rate change *means* operationally. The package states its own inability (bound i) and names the instrument (packet 35, not run). Named dependency, honestly declared — not a re-run demand.
- **Corpus change frequency in production** (how often `corpus_content_digest` actually moves per day/week). Nowhere in the package. This is the scheduler's *load model*: digest-keyed re-measurement is only a design if you know how often the key changes. Nothing in the package claims to carry it, and nothing does.
- **Long-horizon / cross-restart floor stability under an unchanged corpus and unchanged fingerprint** — `07` proves same-session run-pairs stay within the F2 gap; nothing addresses weeks-scale or infra-churn drift. This decides whether the scheduler needs any time-based trigger at all, or can be purely event-keyed.
- **Re-measurement concurrency semantics** (what happens when a trigger fires mid-run): the store types visible in `04`'s probe texts (`LeaseFence`, `FenceLostError`) imply an answer exists in code, but `04` explicitly scores nothing and no artifact specifies the behaviour. For the input contract I need the rule, not the class names.
- **Cost variance** — one wall-clock/embeds point; no distribution across corpus sizes. Minor; matters only for scheduler budget guards.

---

# PART 4 — the contract task

*Written after Parts 1–3; nothing above was revised. Assumption in force for this part: every number in the package is a real measurement. I am the contract author for 11-ii (the scheduler that decides when the floor must be re-measured).*

## The three data the scheduler must consume

### Datum 1 — the corpus change-detection key

- **(a)** `corpus_content_digest` — the C10 datum: a digest over the corpus's ascending-id chunk walk, persisted on every measurement row. The scheduler's skip/re-measure decision keys on equality between the adopted row's digest and a freshly computed one.
- **(b)** `05`, `floor_measurement` column 11 (`corpus_content_digest`, `option<string>`); asserted as a pre-condition in `07`'s leg-B table (*"`corpus_content_digest` | `fedcba98…3210` | `fedcba98…3210` | ✓"*); echoed in `07`'s provenance receipt (*"corpus fingerprint … (= `corpus_content_digest`)"*).
- **(c)** `07`, commitment 1: *"Change detection must key on `corpus_content_digest` equality — the C10 datum, persisted on every row — and on nothing else. Digest equal ⇔ zero chunks added, removed or edited ⇔ skip."* Twin prohibitions, commitments 2–3: the scheduler may **not** infer "nothing changed" by comparing a fresh floor to the adopted floor, and may **not** read a floor delta as corpus-drift evidence. The digest speaks for corpus **content only** — it says nothing about the embedder (Datum 2's job).

### Datum 2 — the instrument conditioning key

- **(a)** `embedding_schema_fingerprint` — the identity of the embedding geometry the adopted floor is a threshold *inside*. The scheduler must treat the adopted floor as conditioned on this value.
- **(b)** `05`, `floor_measurement` column 12 (`embedding_schema_fingerprint`, `option<string>`); asserted equal across runs as a `07` leg-B pre-condition; present in `07`'s receipt beside `TEI endpoint identity`.
- **(c)** `09` bound (iii): the fingerprint licenses **within-instrument** conditioning only — *"nothing here establishes that a cosine of `0.5` under one instrument means what a cosine of `0.5` means under the other"* — and the legacy instrument has **no** fingerprint at all (`05`: *"unrecorded — no such value exists"*), so no cross-instrument use of any kind is permitted.

### Datum 3 — the licensed floor-comparison semantics

- **(a)** The F2-calibrated applied gap (`0.010101`) together with the typed determinism verdict `determinism_leg = within_ci_by_construction` — jointly, the ONLY lawful way for the scheduler to compare two floors (e.g. deciding whether a post-re-measurement floor constitutes a real move), and the proof that byte-reproduction may not be a scheduler primitive.
- **(b)** `07`: required-condition (i) (*"`|Δfloor|` < F2-calibrated gap `0.010101` | `|Δfloor|` = `0.000012` | **PASS**"*), the verdict heading (*"`determinism_leg = within_ci_by_construction`"*), and the per-field delta table. The gap's row-level home is named — negatively — in `05`'s not-carried table (*"F2 null-rate + applied gap | null-rate `0.020202`, applied gap `0.010101` | F2"*).
- **(c)** `07`, commitment 3: *"the F2-calibrated gap (`0.010101` here) is the only threshold that separates noise from a real move"*; commitment 4: `bit_identical_cold` *"was not obtained"*, so any scheduler design resting on byte-reproduction is ruled out by measurement, not by taste.

## Unfillable slots (listed in full, before any verdict)

1. **Datum 2(c) — the fingerprint-CHANGE rule is not stated anywhere in the package, and commitment 1's wording actively collides with the obvious inference.** Commitment 1 says change detection keys on digest equality *"and on nothing else"*. Read literally, an embedder swap under an unchanged corpus digest triggers nothing — and the floor would then be served from a dead geometry. The package persists the fingerprint and conditions on it (`07` pre-conditions), but no line says *"fingerprint inequality ⇒ invalidate/re-measure."* I can derive that rule from bound (iii)'s geometry argument, but a derived trigger that a ruling's literal text excludes is a spec ambiguity, and spec ambiguity is an escalation, not a contract author's silent choice. **This slot is unfillable from the package as written.**
2. **Datum 3(b), runtime half — the gap has no durable address.** Its only addresses are `07`'s prose and `05`'s not-carried table (which is an explicit statement of NON-address: no row column exists). The contract-build can cite `07`; the *running scheduler*, consuming future rows, has no source for the gap those rows were judged under. Same defect class for the bars tuple, `k'`, `method`/`B`, and the sensitivity floor — all consult-flagged in `05`. **Fillable for this build; unfillable as a runtime input.**
3. **Minor, listed for completeness:** the `trigger` column's vocabulary is open (`05`: *"nothing in the schema closes its vocabulary"*) — the scheduler must write triggers but has no closed enum to bind to; and the previously-named non-carried data (production mix — bound (i), packet 35; corpus-change frequency; long-horizon stability) bound the scheduler's **tuning**, not its contract, and each already has a named owner or named absence.

## Verdict: **CALL_AGAIN**

**I consume this package as my evidence base.** Why, in order of weight:

- **My Part 0.1 pre-registered trigger was NOT hit.** Both conditioning identities — the instrument fingerprint and the corpus digest — are present, typed, persisted on the adopted row, and asserted as equal-across-runs pre-conditions in `07`. The demand I registered before seeing anything is satisfied.
- **Every retrieval I attempted in Part 1 either succeeded with a citable address or was refused by the package's own explicit bound** — and the refusals (live fire-rate, quality delta) are the package *stopping me from over-reading it*, which is the opposite of a trust failure. The counts reconcile across artifacts to the unit (1.9), the denominators are named against confusion (`00`), and the package audits its own schema against its own rulings (`05`) before asking me to.
- **The unfillable slots are not re-run reasons — a re-run cannot fill them.** Slot 1 needs a *ruling* (amend commitment 1 to scope "nothing else" to the corpus, and state the fingerprint-inequality trigger explicitly). Slot 2 needs a *schema addition* (persist the applied gap — and the bars/`k'`/method — on the row) before the additive valve closes, which is precisely the decision `05` says this consult exists to make. Routing around this package would reproduce both gaps in whatever I re-derived, while discarding validated evidence. ROUTE_AROUND is for evidence I cannot trust or cannot condition; this is evidence I can do both with, carrying two named writer-spec obligations.

**Riders travelling with the verdict, in the same breath:** CALL_AGAIN is issued together with these contract demands on 11-ii's writer spec — (1) the fingerprint-change trigger ruled explicitly; (2) the F2 applied gap (and null-rate) persisted on the row; (3) the legacy fingerprint recorded, or recorded as unrecoverable (`05`'s own final call-out). None suspends consumption; all three are filed as the consult's output.

## The deletion question — one third of the package

**What goes (and it is comfortably a third by bytes):**

1. **`per-query-rows.jsonl`, ranks 3–30 of every hit array** (~60K of the file's ~90K; the file is two-thirds of the package by bytes). The hit arrays are monotone sentinel ramps; I consumed them only through a script asserting three properties — `shown` = ranks 1–10 exactly, `response_best_cosine` = max hit, `k' = 30`. Keep per row: the scalar fields, hits 1–2, plus derived `shown_count` and `hits_captured` fields, and pin the three properties as one schema note. Everything I did with the file survives; a future reader's context stops paying for 28 synthetic cosines per row × 24 rows.
2. **`04`, seven of the ten pairs.** Three pairs fully make the page's point (the referent is visible, not paraphrased — one domain pair, one store pair, one edge pair). The page is also the package's one active hazard: it exhibits real, answerable questions and must carry its own ⚠ telling readers not to spend effort on them — a hazard surface should be as small as its point permits.
3. **`02`, four of the six per-group tables.** Keep the cross-group Δ view, the governing "this is a shape difference" paragraph, and two exemplar groups — the sign-flip group (`legacy-nonsense`) and one monotone group. The remaining tables' content survives in the cross-group summary at the resolution any consumer used it.

**What must never go:**

- **`00`'s three-population table.** It prevented a wrong denominator in my own Part 1 before I could write it. Cheapest defect-prevention per token in the package.
- **`01`'s acceptance legs as `k/n`, and `03` entire** (it is 1.7K and is the reconciliation substrate for three other artifacts).
- **`05` entire** — the row-as-shipped, the closed enums, and above all the not-carried table with the legacy-fingerprint call-out: it is the package auditing itself, and it is where both of my verdict riders came from.
- **`07` entire** — the typed verdict, the four commitments (the scheduler contract's spine), the pre-conditions, the receipt.
- **`08`'s drop table and the match-key paragraph** (the "understated by a quarter, against a 20% gate" counterfactual is the reason the C13 key is believable).
- **`09` entire** — all four bounds. Two of my Part 1 answers were *correct refusals only because these existed*.
- **And the cross-artifact redundancy itself.** The double-reporting of counts across `01`/`03`/`06` is what made reconciliation checkable — my 1.9 exists because of it. Given the operator's stated concern is consumers wasting tokens: cut the sentinel bulk (above), never the cross-checks. Redundancy that lets a consumer verify is not waste; it is why my verdict is CALL_AGAIN instead of "trust me."

---

**STANDING BY** — Parts 0–4 complete. Run closed pending administrator instruction.
