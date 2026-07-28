# REPORT-informant-opus-11ib

Consumer informant, packet 11i consult. Nothing has been read: at the time of writing this
file I have opened **zero** files, run zero searches, and used exactly one tool (Write, to
create this report). Everything in Part 0 comes from my context window as it was handed to
me, plus my own judgement.

---

## PART 0

### 0.0 — CONTAMINATION CHECK (measured, not assumed)

Substantial project-specific context is already auto-loaded in my window. Enumerated
honestly, grouped by source, with the pieces most likely to seed my later answers marked ⚠.

**A. Global operator law (`~/.claude/CLAUDE.md`), verbatim-present in my context:**
- Strict TDD; the 8-phase contract-first cycle by name: **DISCOVERY → CONTRACT → ADVERSARY →
  STUB → RED → GREEN → REFACTOR → AUDIT**; the `contract-adversary` agent and its INSUFFICIENT
  verdict routing.
- "Investigation order: tests before code"; lifecycle/degradation/recovery test requirements.
- **Scope law**: "THE OPERATOR DETERMINES SCOPE — NOT CLAUDE"; nothing may be declared out of
  scope; escalate everything.
- **Verification law**: "receipts or it didn't happen"; "re-measure inherited numbers before
  trusting them"; "a figure you didn't measure is a rumor"; independent auditor ≠ builder.
- ⚠ **Deferral law**: legitimate deferral has exactly three shapes, and *"measure-then-tune"*
  requires a **NAMED decision point — what data, arriving when, decided by whom"**; *"a deferral
  without a decision point is a can-kick."* This is *directly* about scheduling a re-measurement.
- ⚠ Rename/reshape sweep law; "green-at-gate defects hide in natural-language surfaces";
  "every audit-caught defect class becomes a repo-local invariant test".
- Packages-over-hand-rolling; ONE IMPLEMENTATION / "prove sharing by MUTATION".
- Multi-agent comms discipline (SendMessage only to agents at rest; durable pull channels;
  `brief-base.md` receipt line; never reuse a teammate name; idle-gate hooks).
- Communication style: concise, zero pandering; the exact "There are N failing tests unrelated
  to our present scope…" closing line.
- Host gotchas (podman, PG18, OpenZFS, cron), Mezmo log fields, `odoo-code` vs `odoo-dev`.
- ⚠ The description of **lore itself**: "generic, per-project code+docs RAG MCP", collection
  `lore_<slug>`, and its tool names — `search_code`, `get_symbol`, `tests_for`, `what_imports`,
  `blast_radius`, `read_file`, `save_memory`/`recall_memory`. So I already know the *consumer
  surface* whose absence-declaration threshold this package is presumably about.

**B. Project law (`lore/CLAUDE.md`), verbatim-present:**
- ⚠⚠ **THE CONSUMER LAW + THE TRUST DOCTRINE** — "lore's clients are AGENTS … never humans";
  "TRUST is the paramount property of every served surface"; "a served count describes the whole
  set its label claims; failures are LOUD, never silent; teaching prose matches measured
  behaviour; no render over-claims"; "rigor-vs-speed trades on serving surfaces resolve toward
  RIGOR"; the **CALL_AGAIN vs ROUTE_AROUND** routing test; packet 03b rulings §C5; DESIGN-LAW §1.
  *This is the single largest contamination risk for this consult:* a threshold that decides
  when a search says "absent" is exactly a served-surface trust question, and I already hold the
  doctrine's vocabulary and its verdict direction.
- ⚠ **"WHEN YOU CANNOT CLOSE A HOLE, PIN IT"** (#137/#138) and **"Every bound carries a NAMED
  RE-OPEN TRIGGER"** — the condition under which the trade changes. This is *literally* the
  concept "the scheduler" implements.
- ⚠ **"THE RIDER IS PART OF THE RULING"** (packet 03b, DD-3.c) including *"a ">5% p50" re-open
  trigger with nothing measuring p50 — a trigger nobody measures is a hope."* I hold, pre-package,
  the belief that a trigger without an instrument is worthless.
- ⚠ **"A DIAGNOSIS IS NOT AN INSTRUMENT"**; **"FILING A RULE DOES NOT INSTALL IT"** (#194,
  `scripts/mutation_proof.py`, declare expected-RED ids from `--collect-only`, diff BOTH ways);
  **"THE LEVER: write laws as QUESTIONS"**.
- ⚠ **"FIXTURES MUST DISCRIMINATE — what WRONG build would still pass this?"** with its three
  measured axes (small-N; parameter-value monoculture; arithmetic alignment) and **THE QUANTIFIER
  LAW** ("never condition an invariant on the failure mode that prompted the work"; ∀-vs-guarded
  tables; force each fate with a fixture). Also "a probe needs a CONTROL"; "pair every negative
  result with a POSITIVE CONTROL".
- ⚠ "A FAILURE MESSAGE THAT PROMISES A CHECK THE ASSERTION DOES NOT PERFORM IS A FALSE GATE".
- The instrument-lesson table (six defeats: label literal → substring; symbol name → numeric
  claim; `async def _query` → `scout.py`; 3 method names → the other 30; 2 receivers → six doors;
  runtime gate → a path no test ran) and **"allowlist the safe, never enumerate the forbidden"**.
- #107 (`DEFINE FIELD IF NOT EXISTS` is a silent no-op → 100% `brief_publish` outage; the answer
  was already in `docs/reference/surrealdb-31-capabilities.md`); #131 (no `git` in the image);
  **"THE TEST ENVIRONMENT IS A FICTION"**; #139/#140/#24 ("prove which tree you are testing",
  `scripts/scratch_copy.sh`); #134/#125/#136 (no worktrees); #152/#153 (archive reports, never
  delete; cite symbols not line numbers; "never cite a bare `REPORT-*.md`").
- `lorerunes` workspace layout; `scripts/registration_sites.py` and the warning that the
  registration-site list has been wrong four times.
- Gates: `scripts/typecheck.sh`, `uv run ruff check .`, `pytest -n auto` (846s→88s, 666 passed),
  "a green claim requires a passed-COUNT in the tail".
- Dogfood protocol: `lore_index()` freshness ages, `reconcile=True` before trusting graph answers,
  `lore_findings action=report`, `lore_remember`/`lore_recall`; finding #46 near-miss.
- Deploy facts: `ws://127.0.0.1:18000` = spike/test store, `:18500` = prod `lore-surreal`;
  SurrealDB 3.2.1 forward-only; plan of record `docs/plans/v2/INDEX.md`.

**C. Session/environment context:**
- Branch `feat/surreal-unification`; modified files listed in git status
  (`loremaster/tests/_surreal_harness.py`, `test_blocks_edge.py`, `test_query_tasks_bounded.py`,
  `test_surreal_harness.py`, `test_surreal_store.py`); untracked `REPORT-contractfix-04b1.md`;
  recent commit subjects naming a **Fable design sidecar**, a **contract-adversary INSUFFICIENT
  verdict** ("3 wrong builds survive 80/80"), "#253 addendum — the diff, not the twin", "C-DEF
  blocker", "limit push-down, one cycle detector, TOCTOU closed by construction".
- My own report path, `/home/ejprice/PycharmProjects/lore-pkt11i-b/`, tells me this is a sibling
  checkout for **packet 11i**, run "b" — i.e. this consult is probably one of a matched pair/panel.
- Tooling in my system prompt: Claude-in-Chrome browser automation, Workflow orchestration,
  Artifact publishing, skills. None project-specific.

**D. Terminology I already hold, unprompted by the package:** floor/threshold, packet, contract,
adversary, cold audit, mutation proof, pin, receipt, rider, trust doctrine, ROUTE_AROUND, tier
(`surrealdb-docs`, `surrealql-tests`), finding numbers.

**What this means for weighing my answers.** I have *not* read any packet-11i material, any
design doc, any prior consult, or any source. But I arrive with a strong, specific prior about
(i) what a served surface owes an agent consumer, (ii) that bounds need named re-open triggers,
(iii) that triggers need instruments, and (iv) that any control set must discriminate and be
paired with a positive control. Expect my 0.1 and 0.2 to be shaped by those. I will flag it again
at any later point where I catch an answer leaning on context rather than on the package.

---

### 0.1 — THE RE-RUN TRIGGER (recorded pre-package; not revisable)

**If the package does not contain the labelled discrimination evidence for the floor itself — a
control set with BOTH known-absent and known-present queries and the resulting error rate in each
direction at the chosen threshold — I demand a re-run, because a floor without a demonstrated
ability to separate "absent" from "weak but present" is an unfalsifiable number, and no amount of
downstream reasoning can reconstruct that evidence from the artifact.**

*(Contamination flag, per 0.0: this answer is plausibly seeded by "FIXTURES MUST DISCRIMINATE",
"a probe needs a CONTROL — pair every negative result with a POSITIVE CONTROL", and the trust
doctrine's "failures are LOUD, never silent". I record it anyway because it is what I would
actually demand. Runner-up, deliberately NOT chosen: missing provenance/conditioning of the
measurement — that one I judge recoverable by asking the runner, so it is a request-for-info,
not a re-run.)*

---

### 0.2 — WHAT I EXPECT TO NEED (pre-package expectations)

Data I expect the package to supply so I can write the **input contract for a scheduler that
decides when the floor must be re-measured**. Each is phrased so I can later check present/absent.

1. **The floor itself, fully specified.** The numeric value; the metric and scale it applies to
   (cosine similarity vs distance, normalised or not, higher-is-better direction); whether it is
   one global number or per-tier / per-corpus / per-query-kind; and where the served code reads it
   from (a constant, config, computed). A number without its metric is not usable as a contract input.
2. **The conditioning variables — what the floor is a function of.** Embedding model identity and
   version, index/config parameters, corpus snapshot identifier, chunking/normalisation settings,
   tool version, date of measurement. *These are the scheduler's candidate triggers*, so an
   unrecorded conditioning variable is a trigger the scheduler structurally cannot fire on.
3. **Sensitivity / slope per conditioning variable.** How far the measured floor moved per unit of
   change (corpus grew by N docs → floor moved Δ; model swapped → floor moved Δ). Without a slope,
   any "re-measure when X changes by Y" threshold I write is arbitrary — invented, not derived.
4. **The control sets themselves.** Counts and construction method for the known-absent arm and
   the known-present arm; whether they are reusable, whether they must be re-labelled when the
   corpus changes, and by whom. This drives both the cost of a re-measure and whether the
   scheduler may trigger one autonomously.
5. **Error rates at the chosen floor, both directions, with N and spread.** False-absent rate
   (real content declared missing) and false-present rate (weak match served as a hit), per arm,
   with sample sizes and confidence/variance. The scheduler's "must re-measure NOW" band is defined
   against these; without them I have no degradation budget to write into the contract.
6. **The score distributions or at least the separation margin.** Per-query top-score distributions
   for both arms, or the gap between the arms' nearest edges at the floor. Margin is headroom: it
   tells the scheduler how much drift is tolerable before the floor is actually wrong, which is a
   different question from how wrong the floor is today.
7. **Run-to-run variance of the calibration itself.** Repeat runs of the same measurement on the
   same corpus/model. This sets the minimum detectable change — a scheduler that triggers on a
   movement smaller than the measurement's own noise will re-measure forever and learn nothing.
8. **The cost and preconditions of one re-measurement.** Wall clock, token/compute cost, whether it
   needs a human labelling pass, whether it can run against the live store or needs a fixture
   corpus, and whether it is safe to run concurrently with serving. A scheduler with no cost model
   cannot choose a cadence, and cadence is the whole output.
9. **Cheap serve-time proxy signals, and evidence they correlate with floor staleness.** e.g. the
   rate of absence declarations, the live score histogram, or an observed near-floor hit rate — plus
   the calibration data showing such a proxy actually tracks the thing it proxies. A proxy with no
   correlation evidence is a trigger nobody has measured.
10. **Known bounds and already-named re-open triggers of the calibration.** Query kinds, languages,
    tiers or corpus regions the run did NOT cover, and any conditions the runners themselves flagged
    as invalidating. These become either explicit contract preconditions or explicit scheduler
    triggers — and a bound the package knows but did not write down is one I will otherwise pin as
    an unknown.

---

---

## PART 1 — RETRIEVAL

**Scope receipt.** I opened only `consult-11ib/honest/`. I listed that directory (not its parent),
read all nine artifacts, and inspected `per-query-rows.jsonl` programmatically. No other repository
file was opened. Every value below is a sentinel from a synthetic exhibit and is quoted only inside
this consult.

### 1.1 — Did the portable instrument pass its pre-registered acceptance? Name the two legs and their values.

**Yes — both legs PASS, and the pass is unconditional.**

| leg | bar | measured | verdict |
|---|---|---|---|
| **(1)** `F_portable` false-fire rate against the legacy labeled real union (n = 357) | ≤ 5% (`0.05`) | `11 / 357` = `0.030812` | PASS |
| **(2)** legacy nonsense catch at `F_portable` (n = 345) | ≥ 60% (`0.60`) | `321 / 345` = `0.930435` | PASS |

Cited: *"**Both legs pass ⇒ the portable instrument is ACCEPTED as built.** Nothing here ships on a
caveat: a failed leg would have returned the instrument to design, not qualified this page."*
Pre-registration is asserted in prose: *"The bars were registered before the run."*

Three riders I would carry forward, because the bare "PASS" is not the whole answer:
- Both legs are judged *"on the ORIGINAL labeled sets, with response-best cosines captured by the
  PORTABLE instrument"* — same sets, new ruler.
- Neither leg is held out (see 1.7).
- **The bars themselves are not persisted.** `05` lists *"bars tuple | false-fire `≤ 0.05`, catch
  `≥ 0.60` | §7 persistence"* in the **proposed**-column table, under the heading *"They are NOT in
  the shipped schema as of 2026-07-28"*. So the pre-registration receipt exists as prose in this
  package and nowhere in the ledger — a later reader of the row cannot see what bars it cleared.

### 1.2 — Scalar offset or distribution-shape difference?

**A distribution-shape difference.** The line that settles it, quoted verbatim from `02`:

> *"A scalar offset would show one number in every cell of the Δ rows and zero in every width-Δ
> cell. This is a distribution-shape difference, not an offset."*

Its four supporting observations, also from `02`, each independently sufficient:
- Δ varies across percentiles **within** a group — *"`human-implementation-vocabulary`:
  `−0.030303` at p5, `+0.151515` at p95"*.
- Δ varies across groups at the same percentile — *"median Δ ranges `+0.030303` to `+0.111111`"*.
- Δ **changes sign** — *"it **changes sign** in `legacy-nonsense` above the median"* (p75/p95/max
  all negative there).
- The p5–p95 width changes by a different amount in every group, *"including one negative"*
  (`legacy-nonsense`, `−0.060606`).

And the trap it disarms: *"The three groups whose median Δ is exactly `+0.111111` are the reason the
headline number looks like an offset if you stop at medians."* `01`'s `F_portable − F_legacy =
0.111111` coincides with three median Δs — a reader who checks only medians would wrongly conclude
"constant offset". I note this is a coincidence *by construction* in a synthetic exhibit, but the
shape argument does not depend on it.

### 1.3 — Which determinism leg held, and what does it commit 11-ii's exact-skip scheduler to?

**The typed verdict is `determinism_leg = within_ci_by_construction`** — the third of the closed
three-value enum (`bit_identical_cold` · `bit_identical_via_cache` · `within_ci_by_construction`).
Stated as *"This run recorded the third: **the two runs' derived payloads are NOT byte-equal.**"*

Precision matters here, because "which leg held" has two readings and the artifact separates them:
- **Leg A (arithmetic determinism, suite pin)** held completely: two in-process runs byte-equal,
  subprocess run byte-equal, and the failing control behaved — *"one `Generator` object reused
  across both runs must NOT be bit-identical | **PASS** (differed, as required)"*.
- **Leg B (end-to-end, the verb run twice on the live corpus)** did **not** reproduce bytes. It was
  rescued by two conditions that both had to hold: `|Δfloor|` = `0.000012` < the F2-calibrated gap
  `0.010101`, and decision agreement `1739 / 1740` = `0.999425` ≥ `0.98`.
- Byte-inequality cannot be blamed on caching: *"Probe-embed cache hits, run 2: **0**. There is no
  embedding cache in this packet."*

**What it commits 11-ii to**, quoting the artifact's own four commitments:
1. *"Change detection must key on `corpus_content_digest` equality — the C10 datum, persisted on
   every row — and on nothing else. Digest equal ⇔ zero chunks added, removed or edited ⇔ skip."*
2. *"Any 11-ii logic that infers 'nothing changed' by comparing a fresh floor to the adopted floor
   is invalid: the floors differ run-to-run even when nothing changed."*
3. *"Any 11-ii logic that treats a re-measured floor's difference from the adopted one as evidence
   of corpus drift is invalid for the same reason; the F2-calibrated gap (`0.010101` here) is the
   only threshold that separates noise from a real move."*
4. *"The `bit_identical_cold` outcome is what would license a stricter scheduler. It was not
   obtained."*

Consumer reading: the scheduler's **skip** branch is fully specified (digest equality, nothing
else) and its **compare-floors** branch is forbidden outright. What is *not* specified is the
re-measure branch — see 3.b.

### 1.4 — Self-retrieval drop rate, split by cause

Over `probe_manifest_pool` = 456 (`08`):

| cause | dropped | rate |
|---|---|---|
| `source_chunk_absent_from_kprime` | 23 | `23 / 456` = `0.050439` |
| `sibling_chunk_same_file_only` | 12 | `12 / 456` = `0.026316` |
| `holdout_file_exclusion_applied` | 10 | `10 / 456` = `0.021930` |
| **total** | **45** | `45 / 456` = **`0.098684`** |

Gate: *"the run is recorded `measurement_failed` if the self-retrieval drop rate exceeds **20%**.
`0.098684 ≤ 0.20` — **PASS**."* Survivors: `456 − 45` = **411** = `answered_probes` = the row's
`adopted_n`.

Two things I checked rather than assumed:
- `23 + 12 + 10 = 45` ✓, and the three decimals sum to `0.098685` against a stated total of
  `0.098684` — a one-ulp miss, exactly as `00` pre-warns (*"independently rounded components may
  miss their rounded total by one unit in the last place"*). The package's own reading instruction
  is live, not decorative.
- The match-key counterfactual is carried, not hidden: *"Under path matching this run would have
  reported `33 / 456` = `0.072368` instead of `0.098684` — a drop rate understated by a quarter,
  against a 20% gate."* (`33 = 23 + 10`; the 12 sibling drops are exactly the ones a path key would
  have scored as hits.) This is the single most self-incriminating number in the package, and it is
  in the package.

### 1.5 — What fraction of LIVE PRODUCTION queries would fire the absence verdict?

**REFUSED — the package cannot answer this, and says so in three places.** How I know:

> `01`: *"It is not a sample of live production traffic, and nothing in this package supports a
> statement about what fraction of live queries would fire the absence verdict. Packet 35 is the
> instrument that would measure that; it has not run."*

> `06`, bound (i): *"**This package cannot tell you what fraction of live production queries would
> fire the absence verdict**, or what fraction of live shown hits would be over-flagged, and no
> number here may be re-expressed as such a fraction: the query mix that produced these rates was
> constructed, not sampled from traffic."*

> `03`: *"A different query mix — production traffic, for one — would produce different anchor rates
> and therefore a different rate of absence verdicts, and this package does not measure that mix."*

The number that exists and that I am declining to launder: the SURVEY fire rate is `776 / 1740` =
`0.445977`. It is a property of a constructed six-group mix whose composition (`hold-out-absent` 567
+ `legacy-nonsense` 345 = 912 of 1740, i.e. the majority of the survey is *deliberately absent or
nonsense material*) has no reason to resemble traffic. Quoting it as a production estimate would be
the exact re-expression bound (i) forbids.

### 1.6 — By how much did retrieval quality improve when the portable instrument replaced the legacy one?

**REFUSED — the question's premise is not licensed by the package, and no figure in it may be used
as the answer.** The line I am acting on, from `02`'s bound (iii):

> *"**No `Δ` here may be re-expressed as an improvement, a regression, a quality delta, or a
> percentage of anything.** Measuring quality across instruments needs a shared human-judged
> relevance set; this run has none."*

Reinforced at `01`: *"⚠ **That scalar is DIMENSIONLESS and it is not a quality delta.** The two
floors are thresholds in two different embedding geometries."* And the deeper reason, which is the
part I would escalate rather than merely note: *"the package carries an
`embedding_schema_fingerprint` for the portable instrument and none for the legacy one, so the two
scales cannot be checked for coincidence."* `05` names that gap explicitly — *"the **LEGACY**
instrument's `embedding_schema_fingerprint` | unrecorded — no such value exists | nothing yet"*.

So the honest answer is not "0.111111" and not "unknown pending analysis" — it is **the run was not
designed to measure quality at all**, and the artifact that would license the claim (a shared
human-judged relevance set) does not exist. `02` does license one thing: reading the SHAPE of a
paired difference. Shape is not magnitude and magnitude is not quality.

### 1.7 — Was the acceptance evaluated on data held out from the floor's selection?

**No.** Cited, verbatim:

> *"**Bound (iv) — the acceptance was NOT evaluated on held-out data, and here is exactly what that
> costs.** `legacy-nonsense` is **one of the six groups `F_portable` was selected over** (`02`,
> group 6), and the legacy labeled real union is the union of two more of them (groups 1 and 2).
> **No leg of this acceptance is independent of the selection population.**"*

The bound also states what limits the damage — *"`F_portable` was chosen off the pooled ladder
across all six groups, **not** by sweeping for the value that maximises catch on `legacy-nonsense`
or minimises false-fire on the real union — no single group's statistic was optimised, and no
group's labels were derived from either instrument's own output"* — and what the legs therefore do
and do not establish: *"these legs establish **'the portable floor clears the original bars on the
original labeled sets'** and they do **not** establish that it generalises to any set not in the
six."*

Note for the record: *"A held-out leg is not in this run; adding one is a design decision, not a
re-analysis of these numbers."* That sentence names a gap and assigns it to nobody, on no date. I
flag it in 3.b.

### 1.8 — First `absence_verdict_fired: true` row in `per-query-rows.jsonl`

The file is 25 lines: a banner object (`{"_banner": "SYNTHETIC EXHIBIT — no value in this document
is a measurement"}`) plus 24 rows. The first row with `absence_verdict_fired: true` is the **fourth
data row**, `query_id: "q_human_prose_3"` (group `human-prose`, `sampled_at_position: "min"`,
`query_text: "which module owns the chunk model the indexer consumes"`).

- **Rank-1 hit's cosine: `0.333333`** (`{"rank": 1, "point_id": "chunk:synthetic_human_prose_3_01",
  "vector_cosine": 0.333333, "shown": true}`).
- **Hits marked `shown`: 10** — ranks 1–10 inclusive; ranks 11–30 are `"shown": false`. The row
  carries all 30 captured hits.

**Consistency — three checks pass, one does not, and the one that does not is worth the whole
question.**

✔ *Floor consistency.* Rank-1 cosine `0.333333` = the row's `response_best_cosine` (`0.333333`),
which is below `F_portable` = `0.456789`, and `has_verbatim_anchor` is `false`. `03`'s predicate —
*"it fires on `max_cosine < floor AND NOT has_verbatim_anchor`"* — therefore fires. ✓

✔ *Distribution consistency.* `0.333333` is exactly the portable **min** for group 1 in `02`
(`human-prose`, portable min `0.333333`), and the row is tagged `sampled_at_position: "min"`. ✓

✔ *Shown-slice count.* 10 = `SURVEY_K`, glossed in `00` as *"the shown slice, 10 — the hits a caller
actually sees"*, out of a `k' = 30` capture — matching bound (ii): *"Every number on this page covers
ranks 1–10. The instrument captures `k' = 30` hits per query; ranks 11–30 are excluded here by
design, because they were never shown to a caller."* ✓

✘ **`shown: true` on a query whose absence verdict FIRED contradicts the meaning `06` assigns to
"shown".** `06` defines the over-flag population as *"A hit is 'over-flagged' when it was SHOWN to
the caller on a `verdict_not_fired_queries` query"*, and computes *"Shown hits over
`verdict_not_fired_queries`: `964 × 10` = **9640**"*. A floor's entire purpose is that below it the
tool declares absence **instead of** returning weak matches — so on `q_human_prose_3` the caller saw
nothing, yet ten hits are flagged `shown: true`, all ten of them below the floor. Both readings
cannot be right:
- If `shown` means *rank ≤ SURVEY_K* (a capture-slice marker the instrument writes regardless of
  verdict), the row is fine and `06`'s prose *"SHOWN to the caller"* is loose — and a consumer who
  computed shown-hit totals by counting `shown == true` across all rows would get `1740 × 10` =
  `17400`, not `9640`, an **80% overcount** with no error anywhere.
- If `shown` means *served to a caller*, this row is internally inconsistent with its own
  `absence_verdict_fired: true`.

The package never defines the field. Worse, **`02`'s description of the artifact omits it entirely**:
*"the `k' = 30` hit capture with each hit's `rank`, `point_id` and `vector_cosine`"* — three fields
named, four fields shipped. The one undocumented field is the one carrying the shown-slice semantics
that `06`'s entire denominator rests on. That is a served-surface description that does not match
the served artifact.

### 1.9 — Do `01` and `03` reconcile — with each other, with the survivor count, and with the adopted row?

**With each other: yes, exactly.** `03`'s per-group below-floor slice at `F_portable`, restricted to
the two human groups:

```
below floor : human-prose 12 + human-impl-vocab 11 = 23
anchored    : 8 + 4                                 = 12
fired       : 4 + 7                                 = 11
group sizes : 123 + 234                             = 357
false-fire  : 11 / 357 = 0.030812324…  → 0.030812   ✓ = 01's leg (1)
```
`01` reports for the same population *"at `F_portable` = `0.456789`, portable instrument | 23 | 12 |
11 → `11 / 357` = `0.030812`"*, and `03` states the identity itself: *"The two human groups' rows
here are the same counts `01` reports as the legacy labeled real union (`12 + 11 = 23` below floor,
`8 + 4 = 12` anchored, `4 + 7 = 11` false fires)."* Nonsense leg likewise: `03` gives
`legacy-nonsense` 324 below / 3 anchored / 321 fired; `01` gives `324 | 3 | 321 → 321 / 345 =
0.930435`. `321 / 345 = 0.930434782…` → `0.930435` ✓.

**Internal totals of `03`: all check.**
```
below floor : 12 + 11 + 0 + 12 + 456 + 324 = 815   ✓ (stated 815)
anchored    :  8 +  4 + 0 +  6 +  18 +   3 =  39   ✓ (stated 39)
fired       :  4 +  7 + 0 +  6 + 438 + 321 = 776   ✓ (stated 776)
815 − 39 = 776                                     ✓
group sizes : 123+234+15+456+567+345 = 1740        ✓ (02's stated total)
not fired   : 1740 − 776 = 964                     ✓ (03 → 06's denominator)
anchor total: 12+123+12+234+23+3 = 407; 407/1740 = 0.233908  ✓
```
And the `39` propagates cleanly to a third artifact: `06`'s best-hit slice is `39 / 964` =
`0.040456` ✓, with the reconciling claim *"All 39 best-hit-below-floor queries are anchored queries
— that is precisely why they were answered rather than refused, and 39 is the same
anchored-and-below-floor count `03` reports."* That is logically forced, not asserted: a query whose
best hit is below the floor and which nonetheless did not fire must have been anchor-suppressed.
`05` records the same 39 as *"anchored-excluded count | `39` | C2"*. Three artifacts, one number,
no drift.

**With the survivor count: they reconcile by NOT being equal, and that is the correct answer.**
```
probe_manifest_pool 456 − drops 45 = answered_probes 411   (08)
03/02 use 456 as the self-supervised-answered GROUP size   (a QUERY count)
05 writes adopted_n = 411                                  (a PROBE count)
```
The 45 dropped probes remain in the query-level tables (the group is n = 456 in both `02` and `03`)
while being excluded from the probe-level floor selection (`adopted_n` = 411). So **no denominator
in `03` equals `adopted_n`, and none should.** `00` pre-empts precisely this: *"Three different
counts in this package could each loosely be called 'the answered set'… a consumer that picks the
wrong one gets a wrong denominator with no error anywhere"*, and `06` repeats the guard: *"**Do not
use 964 as a probe count or 411 as a query count.**"* Both stated identities hold: `411 = 456 − 45`
✓ and `964 = 1740 − 776` ✓.

⚠ One legibility hazard I would fix even though the arithmetic is right: **`456` appears as two
unrelated quantities** — `probe_manifest_pool` / group-4 size (456 queries) and `hold-out-absent`'s
below-floor count (456 of 567) in `03`. Same digits, different populations, adjacent tables. A
sentinel collision in a synthetic exhibit, but the collision is in the *shape*, and a reader who
matched on the number would cross-wire two populations the package spends a whole section
separating.

**With the adopted row: yes, on every field they share.**
```
floor        05 #6  0.456789  = 01's F_portable = 03's slice header = 06's decomposition   ✓
ci_low/high  05 #7,#8 0.404040 / 0.505050 = 01's table                                     ✓
adopted_n    05 #9  411 = 08's 456 − 45 = 01's MIN_ANSWERED_PROBES row                     ✓
state        05 #3  measured; non_adoption_cause NONE; note NONE  (consistent: adopted)    ✓
head_revision 05 #2  12 = floor_head.revision 12                                           ✓
corpus digest 05 #11 fedcba98…3210 = 07's run-1 AND run-2 pre-condition value              ✓
fingerprint   05 #12 SYNTHETIC-EXHIBIT-FINGERPRINT-… = 07's receipt                        ✓
validity      01's 411 / 15 / 533 = 08's post-drop counts (533 = 567 − 34)                 ✓
```

**What does NOT reconcile onto the row — and this is the finding, not a nitpick.** The row carries
14 columns. Every number I just reconciled across `01`/`02`/`03`/`06`/`08` — the bars, the per-group
results, the anchored-excluded count 39, `k'` = 30, the drop diagnostics, the probe manifest, the F2
null-rate and applied gap, the sensitivity floor, the degeneracy telemetry, the run cost, the
paired decomposition — is in `05`'s **proposed**-column table, i.e. *"They are NOT in the shipped
schema as of 2026-07-28 — no column exists for any of them."* The artifacts reconcile with each
other beautifully **as documents**; the ledger row they all describe would not let a future reader
redo a single one of these checks. `05` says it plainly: *"Everything in that table exists in this
package only as prose in these documents. A distinction the row never recorded is a distinction no
later render can serve."*

---

## PART 2 — BEHAVIOUR (what I actually did)

Labelled **OBSERVED** (I can point at the tool call) vs **BELIEVED** (introspection, unverifiable).

### Which artifacts did I open? — OBSERVED
All ten. In this order, batched:
1. `ls` of `consult-11ib/honest/` (the package dir only; I did not list or touch its parent).
2. `00-README.md` + `01-summary.md` (one batch).
3. `02-per-group-distributions.md` + `03-anchor-rates.md` (one batch).
4. `05-adopted-row-provenance.md` + `06-per-hit-decomposition.md` (one batch).
5. `07-determinism-and-run-receipt.md` + `08-drop-diagnostics.md` (one batch).
6. `04-probe-texts.md` + a Python structural scan of `per-query-rows.jsonl` (one batch).
7. A second Python call dumping the full first fired row and its 30 hits.

**Deviation worth reporting:** I read `04` **last**, out of numerical order — not by plan, but
because after `03` I was chasing the floor/anchor arithmetic and `04` is the one artifact carrying
no numbers. That is a bias I should name: I sequenced the package by *what I was auditing*, and the
qualitative artifact fell to the end. Had `04` contained something load-bearing I would have met it
after my model of the package was already set.

**I read `per-query-rows.jsonl` with Python, not with Read** — a field-key scan, a 24-row summary
table, then one full row. I never rendered the other 23 rows' hit arrays.

### What did I read fully vs skim? — OBSERVED
- **Fully, every line:** `00`, `01`, `02`, `03`, `05`, `06`, `07`, `08`. They are short (~1.5–7.5 KB
  each); there was no reason to skim and I did not.
- **Read in full but deliberately not engaged:** `04`. I read all ten pairs as text and **did not
  answer any human question**, per its own instruction (*"⚠ **The human questions below are
  exhibited as TEXT. Do not answer them.**"*). I did not verify its provenance claims either —
  doing so would have meant opening `loremaster/evaluation.xml` and
  `loremaster/loremaster/floor_calibration/*.py`, which is outside my package.
  ⚠ **Contamination note (new, this run):** `04` is the one page that is *not* synthetic, so reading
  it put real facts about lore's codebase into my context — that a startup gate raises a dedicated
  exception, that a reference-counted lease class enforces once-per-process startup, that
  `evaluation.xml` holds 35 pairs, that a `floor_calibration` package with `domain.py`/`store.py`
  exists and has symbols named `LeaseFence`, `FenceLostError`, `MeasurementReceipt`,
  `FloorCalibrationStore`. I did not seek this; it arrived as exhibit text. Some of it shaped 3.b
  below (the lease/concurrency gap), and I say so there rather than pretending the idea came from a
  numbered artifact.
- **Skimmed / sampled, not read:** the JSONL. I looked at 12 of 30 hits in one row and the field
  keys of one other; the remaining ~700 hit objects I touched only through aggregate Python
  (`max`, `sum`, counts). **BELIEVED:** had a single row carried an anomalous hit at rank 17, I
  would not have seen it.
- **Not read at all:** nothing in the package.

### The single most useful line — OBSERVED (I can name what it changed)
> *"Change detection must key on `corpus_content_digest` equality — the C10 datum, persisted on
> every row — and on nothing else. Digest equal ⇔ zero chunks added, removed or edited ⇔ skip."*
> (`07`)

Because it is the only line in the package that hands me a *decision rule* rather than a
measurement, and it is the load-bearing input to the exact thing I am being asked to specify. It
also comes with its own negations (items 2–4: what the scheduler may **not** infer), which is rarer
and more useful than the positive half.

Runner-up, and I name it because it is the line that stopped me making a real error: `00`'s
three-population table (*"`answered_probes` 411 · `probe_manifest_pool` 456 ·
`verdict_not_fired_queries` 964"*). Before reading it I had begun to treat 456 and 411 as the same
population wearing two names; the table is why 1.9's survivor-count answer is "correctly unequal"
rather than a false discrepancy report.

### What would I DELETE from the summary? — a judgement, stated as one
**`01`'s line `F_portable − F_legacy = 0.111111`.** Delete the scalar; keep the pointer to `02`.

Reasons, in order of weight:
1. **It is a number that arrives with a prohibition on every use.** The 8 lines immediately
   following it say it is dimensionless, not a quality delta, not an improvement, not a regression,
   not a percentage, and that the two scales *"cannot be checked for coincidence"*. A value with no
   permitted use is not information; it is an attractive nuisance sitting in the one document
   labelled *"Headline scalars only"* — the document most likely to be quoted alone.
2. **The package itself says the number misleads:** *"The three groups whose median Δ is exactly
   `+0.111111` are the reason the headline number looks like an offset if you stop at medians."*
   The prohibition and the trap are two artifacts away from each other in a reader's memory; the
   scalar travels, the caveat does not.
3. **Its only legitimate content is already carried better elsewhere** — `02`'s per-percentile,
   per-group Δ tables, which the summary already points at (*"What `02` does carry is the
   per-percentile and per-group SHAPE of the paired difference, which this single number averages
   away."*).

What I would put in its place: one sentence stating that the two floors are thresholds in
non-commensurable geometries, that no scalar difference between them is defined, and that the
paired SHAPE is in `02`. That preserves every true thing the passage says and removes the only
quotable falsehood-generator on the page.

I would delete nothing else from `01`. Specifically I would **not** delete the measured-population
paragraph, the bound (iv) block, or the "Nothing here ships on a caveat" sentence — those are the
page's load.

---

## PART 3 — THE AUDIT QUESTION

### 3.a — My Part 0.2 list, item by item

| # | expected | verdict | where / how I know |
|---|---|---|---|
| 1 | floor fully specified (value, metric, scale, scope, direction) | **PRESENT, with a structural gap** | `05` #6–#8 (`floor` `0.456789`, `ci_low`, `ci_high`); statistic/scope on `floor_head` (`axes.statistic = response_best_cosine`, `axes.scope`, `axes.query_shape = any`); direction from `03`'s predicate. **Gap:** *"The axis columns live on `floor_head`. **They are not columns on `floor_measurement`** — a measurement row's only link to its axes is the one-way `head_identity` digest."* A row alone cannot say what statistic it thresholds. `05` lists the axis columns as a *proposed* addition (F6 / decision 5). |
| 2 | conditioning variables / provenance | **PRESENT — strongest part of the package** | `05` #10–#12 (`instrument_version`, `corpus_content_digest`, `embedding_schema_fingerprint`), #14 `created_at`; `07`'s receipt adds `loremaster.__file__`, store URL/ns/db, `LORE_VERSION`, image digest, git commit, git-dirty, TEI endpoint identity, scipy/numpy. **Gaps:** scipy/numpy are *proposed* columns (*"required by ruling R-G"*), so the receipt is stdout only; and *"the **LEGACY** instrument's `embedding_schema_fingerprint` | unrecorded — no such value exists"*. |
| 3 | sensitivity / slope per conditioning variable | **ABSENT** | Nothing in nine artifacts relates a corpus/model change to a floor movement. The near-misses are not slopes: the F2 *"null-rate `0.020202`, applied gap `0.010101`"* is a **noise band**, and the *"sensitivity floor `0.434343`"* is an R2.5/F2 bar, not d(floor)/d(corpus). How I know it is absent rather than elsewhere: `05`'s not-carried inventory is explicit and contains no such quantity, and I read all nine files end to end. **This was my #3 expectation and it is the biggest miss.** |
| 4 | control sets, construction, reusability | **PARTIAL** | Present: six groups with n (`02`), the C11 manifest (*"**456** `(point_id, probe_text_sha512)` pairs"*, persisted in-row), C12's rule (*"the first 15 identities in ascending `sha512_hex(identity)` order"*) with its stability property (*"a single corpus insertion changes membership by at most one"*), C13's match key and its counterfactual. **Absent:** how the two human groups were constructed, by whom, and whether they are regenerable at re-measure time. `04` sources ten exhibited questions to `loremaster/evaluation.xml`, but says nothing about the groups' own provenance. |
| 5 | error rates both directions, with N | **PRESENT** | `01`'s two legs (`11 / 357`, `321 / 345`) and both instruments' selection receipts; `03`'s full per-group below-floor slice with n. **Caveats:** no interval on either acceptance rate (the CI is on the floor, not on the rates), and bound (iv) — neither rate is held out. |
| 6 | score distributions / separation margin | **PRESENT, generously** | `02` (6 groups × 2 instruments × 8 order statistics + p5–p95 widths + cross-group view), `06` (per-hit over 9640 shown), and the 24-row sample. Margin is computable in-package, e.g. `hold-out-absent` portable p95 `0.494949` sits **above** `F_portable` `0.456789` — the absent distribution's upper tail already crosses the floor. |
| 7 | run-to-run variance of the calibration itself | **PARTIAL** | `07`'s per-field deltas (`floor +0.000012`, `ci_low +0.000023`, `ci_high +0.000034`, sensitivity floor `+0.000045`, `adopted_n` `0`) and the typed leg. **But n = 2.** Two runs give a difference, not a variance; and the operative threshold (`0.010101`) comes from an F2 calibration whose derivation is not in the package. |
| 8 | cost and preconditions of a re-measurement | **PRESENT in prose, ABSENT from the ledger** | `07` cost accounting: budget `34567`, embeds used `23456`, remaining `11111` (`34567 − 23456 = 11111` ✓), wall-clock `3456.789` s, `retry_on_conflict` attempts `12` / conflicts `3` / exhausted `0`. Preconditions: *"settled-index start/end checks"*, and *"the verb carries no default coordinate of any kind and refuses to run without one"*. **Gap:** *"run cost (embeds, wall-clock) | `23456` embeds, `3456.789` s | D5 / §7"* sits in the **not-carried** table — so the scheduler cannot learn cost from history. |
| 9 | cheap serve-time proxy signals + correlation evidence | **ABSENT, and explicitly out of reach** | Bound (i) forbids any live-traffic statement; *"Packet 35 is the instrument that would measure the live population. It has not run."* `06`'s over-flag decomposition is the nearest thing and is survey-mix only. There is therefore **no measured signal a scheduler could watch between full re-measurements**, and no evidence any candidate proxy tracks staleness. |
| 10 | known bounds + named re-open triggers | **BOUNDS: PRESENT and unusually well-placed. TRIGGERS: PARTIAL.** | Four bounds, each inside the claim it governs (`00`'s table maps them; *"There is no bounds section; if you are looking for one, you have the wrong package."*). Triggers: `07`'s four commitments are a real trigger rule for the digest axis. **Absent:** any trigger for re-running the **acceptance** — bound (iv) ends *"adding one is a design decision, not a re-analysis of these numbers"*, which names the gap but names no data, no date and no decider. ⚠ *Contamination flag: my instinct that a deferral needs a named decision point is verbatim in my auto-loaded operator law (0.0-A). I would hold the objection anyway — a scheduler cannot fire on a trigger nobody assigned — but the phrasing is borrowed.* |

Score: **3 present, 4 partial, 2 absent, 1 present-with-structural-gap.** The package is strongest
exactly where I expected it to be weakest (provenance, bounds, self-incriminating counterfactuals)
and weakest exactly where a *scheduler* lives (sensitivity, proxies, cost persistence).

### 3.b — What I needed that the package does not carry

Ordered by how badly it blocks the input contract. Items marked **[NEW]** were not on my 0.2 list —
I discovered I needed them only while reading.

1. **[NEW, and the sharpest gap] The re-measure branch has no threshold — only the skip branch does.**
   `07` gives an exact-skip rule (*"Digest equal ⇔ zero chunks added, removed or edited ⇔ skip"*) and
   then stops. `corpus_content_digest` is a **whole-corpus** digest over *"the corpus's ascending-id
   chunk walk"* (`00`, C10): it changes on a one-character edit to one chunk out of `23456`. So
   `digest ≠ digest` fires on essentially every commit, and the package supplies **nothing** to
   decide how much change warrants paying `23456` embeds and `3456.789` s. A scheduler built strictly
   on what is here is either "skip" or "re-measure everything, constantly". I need at least one of:
   a chunk-level delta count, a per-tier or partial digest, or a measured slope (item 3.a #3). This
   is the datum whose absence I would escalate first, and it is *not* the one I named in 0.1.
2. **[NEW] A staleness axis that is not the corpus.** `created_at` exists; nothing anywhere says a
   floor expires. A floor can go stale with an unchanged corpus — TEI endpoint swap, embedder
   revision, query-mix shift. `embedding_schema_fingerprint` covers the model-schema case; the
   receipt's *"TEI endpoint identity"* is printed but **not** a persisted column. No max-age, no
   non-corpus trigger.
3. **[NEW] `trigger` is an open vocabulary.** `05`: *"`trigger` is an open `option<string>` today:
   nothing in the schema closes its vocabulary. This run wrote `manual`."* The scheduler is the
   component that will write this field on every automatic run. An open string here means the
   measurement history cannot be aggregated by cause (scheduled vs manual vs invalidation) without
   string archaeology — and 11-ii is exactly the packet that starts writing non-`manual` values. A
   closed enum is a cheap decision to make **now**, before the additive valve closes.
4. **[NEW] The state machine's transitions.** `FLOOR_STATES` is pinned at 8 values, but nothing says
   which transitions are legal or which states the scheduler may act from. `invalidated_remeasuring`
   implies an invalidation path with no documented author; may the scheduler fire from
   `insufficient_corpus`? Does `disabled` block it (and who sets it)? Does a `measurement_failed` run
   retry, and with what backoff? An input contract cannot be written against an enum alone.
5. **[NEW] The lease / concurrency contract.** `08` and `04` surface `LeaseFence`, `FenceLostError`
   (*"The end-of-run commit was refused because the lease fence moved"*) and B4's hot-row mint, and
   `07` counts `retry_on_conflict` attempts — so a scheduled run plainly must take a lease and can
   lose it. The package never states that contract: who may hold, what the fence epoch is, what the
   scheduler does on `FenceLostError`, or whether two schedulers may race. (Honest provenance: I got
   these names from `04`'s exhibit text — see the Part 2 contamination note — not from a numbered
   artifact.)
6. **What the served surface does when there is no adopted floor.** `08`: *"Had any of the three
   failed, the run would have been recorded `insufficient_corpus` and no head would have been
   adopted."* The ledger is append-only and `head_retained_overlap` hints the prior head survives —
   but the package never states whether the previous floor keeps serving, for how long, and whether
   the consumer is told it is serving a stale floor. For a trust-critical absence verdict that is an
   input to the contract, not an implementation detail.
7. **Per-group persistence.** R3 requires it; `05` lists *"per-group results | the whole of `02`"*
   as **not carried**. Without it the scheduler can never detect that one group degraded while the
   aggregate held — the exact signal that should trigger a re-measure.
8. **The legacy instrument's fingerprint** (`05`'s final row), or an explicit record that it is
   unrecoverable. Not a scheduler input, but it is the premise the whole legacy↔portable comparison
   rests on, and it is *"required by nothing"*. The package flags it as a writer-spec decision this
   consult should make; I concur and would make it: record it, or record its unrecoverability.
9. **A definition of the `shown` field**, plus a corrected artifact description in `02` (see 1.8).
   Undocumented, semantically ambiguous, and load-bearing for `06`'s denominator.
10. **The bars, persisted.** Pre-registration (D8) is only as good as its receipt; today the bars
    live in prose. A future scheduler comparing runs cannot tell whether two rows cleared the same
    bars.

**Where my 0.1 stands.** My locked re-run trigger was the absence of two-armed labelled
discrimination evidence with error rates in both directions. **It is present** — `01`'s two legs
give a false-fire arm (`11 / 357`) and a catch arm (`321 / 345`) on labelled sets, and `02`/`03`
show the arms separating. So I do **not** demand a re-run. What I did not anticipate is that the
evidence would be present and **non-independent** (bound iv), which weakens it without voiding it,
and that the true blocker for *my actual assignment* would be item 1 above — a datum about change
magnitude that I never thought to ask for, because in 0.2 I was still imagining a scheduler that
watches drift rather than one that has been handed an exact equality test and nothing on either side
of it.

---

---

## PART 4 — THE INPUT CONTRACT (numbers assumed real)

Parts 1–3 stand unrevised.

The scheduler has exactly three branches, and each one needs exactly one datum. I state the
contract that way deliberately: a slot that does not map to a branch is a datum I do not need, and
a branch with no datum is a route-around reason.

### SLOT 1 — the SKIP branch

**(a) Datum.** `corpus_content_digest` — the C10 exact-skip change-detection datum, compared for
**equality** against the digest on the adopted measurement row.

**(b) Address.**
- Primary: `05-adopted-row-provenance.md` → *"The adopted `floor_measurement` row — all 14 shipped
  columns, in write order"* → **row 11**, `corpus_content_digest`, type `option<string>`, value
  `fedcba98…3210`.
- Corroboration that it is stable across runs: `07-determinism-and-run-receipt.md` → *"Pre-conditions,
  asserted rather than assumed"* → row `corpus_content_digest`, run 1 = run 2, ✓.
- Definition: `00-README.md` glossary → *"`C10` | the exact-skip change-detection datum:
  `corpus_content_digest` over the corpus's ascending-id chunk walk"*.

**(c) Bound.** `07`, commitment 1: *"Change detection must key on `corpus_content_digest` equality —
the C10 datum, persisted on every row — and on nothing else. Digest equal ⇔ zero chunks added,
removed or edited ⇔ skip."* Three consequences I must write into the contract, not around:
1. **Equality is licensed in ONE direction only.** `digest == digest` ⇒ skip is sound. `digest !=
   digest` licenses *"something changed"* and **nothing about how much** — it is a whole-corpus
   digest over an ascending-id chunk walk, so a single edited chunk out of `23456` flips it exactly
   as hard as a re-index. The scheduler may not read magnitude out of inequality. (This is U1 below.)
2. **No substitute key is permitted.** `07` commitments 2 and 3 forbid inferring change from a
   floor comparison, in both directions.
3. **The column is `option<string>`.** Only `head_identity` and `created_at` are REQUIRED on that
   row; `corpus_content_digest` is nullable, and the package never says what a NONE digest means.
   The contract must therefore treat *digest absent* as **"skip test unavailable ⇒ do not skip"*,
   which is my choice, not the package's instruction. (U13.)

### SLOT 2 — the INVALIDATE branch

**(a) Datum.** `embedding_schema_fingerprint` (paired with `instrument_version`) — compared for
equality; **inequality invalidates the adopted floor outright, regardless of the digest.**

**(b) Address.**
- Primary: `05` → adopted row **row 12**, `embedding_schema_fingerprint`, `option<string>`, value
  `SYNTHETIC-EXHIBIT-FINGERPRINT-0123456789abcdef`; **row 10**, `instrument_version`,
  `0.0.0-SYNTHETIC`.
- Corroboration: `07` → pre-conditions table, `embedding_schema_fingerprint` run 1 / run 2 / ✓; and
  the provenance receipt's own line for the same value.

**(c) Bound.** `02`, bound (iii): *"`F_legacy` and `F_portable` are thresholds inside two DIFFERENT
embedding geometries… nothing here establishes that a cosine of `0.5` under one instrument means
what a cosine of `0.5` means under the other."* So across a fingerprint change the scheduler must
**invalidate and re-measure — it may not compare, subtract, or interpolate.** The failure mode is
already exhibited in the package rather than hypothesised: `05`'s final not-carried row — *"the
**LEGACY** instrument's `embedding_schema_fingerprint` | unrecorded — no such value exists"* —
is precisely why bound (iii) has to say the scales *"cannot even be checked for coincidence"*. A
row with a NONE fingerprint is, by that same logic, permanently uncomparable: the contract treats
it as invalid-on-read, not as "assume unchanged".

### SLOT 3 — the ADOPT / flap-suppression branch

**(a) Datum.** The **F2-calibrated applied gap**, `0.010101` — the only licensed discriminator
between a floor move that is noise and one that is real, hence the only licensed basis for deciding
whether a freshly measured floor replaces the adopted head or the head is retained.

**(b) Address.**
- `07` → *"The verdict — typed, from the closed three-value enum"* → required-condition table, row
  (i): *"`|Δfloor|` < F2-calibrated gap `0.010101`"*, measured `|Δfloor|` = `0.000012`, PASS.
- `07`, commitment 3: *"the F2-calibrated gap (`0.010101` here) is the only threshold that separates
  noise from a real move."*
- ⚠ **Not on the row.** `05`'s not-carried table: *"F2 null-rate + applied gap | null-rate
  `0.020202`, applied gap `0.010101` | F2"*, under *"They are NOT in the shipped schema as of
  2026-07-28."*

**(c) Bound.** Two, and the second is the sharp one:
1. The gap is a **noise floor for the ADOPT decision, not a change trigger**. Using it to decide
   *whether to run* would be commitment-3 violation wearing a different verb; the two runs here
   differed by `0.000012` over a **byte-identical** corpus, so a sub-gap difference is evidence of
   nothing at all.
2. **It is unpersisted, so it is a config constant in my component, not a read.** That means my
   scheduler's most safety-critical constant lives outside the ledger it governs, cannot be
   attributed to the instrument version that calibrated it, and has no stated re-derivation
   condition. I can fill the slot — I cannot fill it *from a row*. (U12.)

### Unfillable slots — every one, before the verdict

Grouped by what they block. None of these is a slot in the three-branch contract above; each is a
question the contract must answer and the package cannot.

**Blocks a branch I must build anyway:**
- **U1 — change MAGNITUDE.** Digest inequality carries none; there is no chunk-delta count, no
  per-tier or partial digest, no measured slope of floor-vs-corpus-change. With `23456` chunks and
  a re-measure costing `23456` embeds / `3456.789` s, a contract built strictly on what is here is
  binary: skip, or re-measure on every commit. **This is the one I escalate first.**
- **U2 — cost history.** `07` carries this run's cost in prose; `05` lists *"run cost (embeds,
  wall-clock) | `23456` embeds, `3456.789` s | D5 / §7"* as not-carried. The scheduler cannot learn
  from past runs what a re-measure costs on the current corpus.
- **U3 — any staleness axis that is not corpus or embedding schema.** No max-age; `created_at`
  exists but nothing expires. TEI endpoint identity is printed in `07`'s receipt and is **not** a
  column, so an endpoint swap under an unchanged fingerprint is invisible to the ledger.
- **U5 — state-transition legality.** `FLOOR_STATES` is pinned at 8 values (`05`), with no
  transition map: which states may the scheduler fire from, is `disabled` a hard stop and who sets
  it, does `measurement_failed` retry and with what backoff, who writes `invalidated_remeasuring`.
- **U6 — the lease/fence contract.** `FenceLostError` (*"The end-of-run commit was refused because
  the lease fence moved"*), `LeaseFence`, B4's hot-row mint and `07`'s `retry_on_conflict attempts
  12 / conflicts 3 / exhausted 0` all establish that a scheduled run takes a lease and can lose it.
  The contract for that is nowhere. (Provenance: the names reach me from `04`'s exhibit text — see
  Part 2's contamination note.)
- **U7 — serving behaviour with no adopted head.** `08`: *"Had any of the three failed, the run
  would have been recorded `insufficient_corpus` and no head would have been adopted."* Whether the
  prior floor keeps serving, for how long, and whether the consumer is told it is stale, is
  unstated — and for an absence verdict that is a trust question, not an implementation detail.
- **U4 — `trigger` vocabulary.** *"`trigger` is an open `option<string>` today: nothing in the
  schema closes its vocabulary. This run wrote `manual`."* My component is the one that starts
  writing non-`manual` values; an open string makes the history unaggregatable by cause.

**Blocks a health signal I would otherwise have used:**
- **U8 — per-group persistence (R3).** *"per-group results | the whole of `02`"* is not-carried, so
  single-group degradation — the most natural "re-measure now" signal in the whole package — cannot
  be detected from the ledger.
- **U9 — serve-time proxy + correlation evidence.** Absent by construction: bound (i), and *"Packet
  35 is the instrument that would measure the live population. It has not run."*
- **U14 — `shown` is undefined** and omitted from `02`'s field list (Part 1.8), so any consumer
  recomputing over-flag rates as a health metric can silently overcount by 80%.

**Blocks verification of the evidence itself:**
- **U10 — the bars are not persisted** (*"bars tuple | false-fire `≤ 0.05`, catch `≥ 0.60` | §7
  persistence"*, not-carried): two rows cannot be shown to have cleared the same bars.
- **U11 — the axes are not on the measurement row.** *"They are not columns on `floor_measurement`
  — a measurement row's only link to its axes is the one-way `head_identity` digest."* A scheduler
  holding a row cannot confirm it is scheduling the right head without resolving the head row.
- **U12 — the F2 gap is unpersisted** (slot 3's own bound).
- **U13 — nullability is unspecified.** 12 of 14 columns are `option<>`; the package never says what
  a NONE in slots 1 or 2 means.
- **U15 — no held-out acceptance leg and no re-open trigger for one.** Bound (iv) closes with *"A
  held-out leg is not in this run; adding one is a design decision, not a re-analysis of these
  numbers"* — a gap named, with no data, no date and no owner attached.

### VERDICT — **CALL_AGAIN**

I consume this package as my evidence base. Reasons, in order:

1. **All three slots fill, from named addresses, with explicit bounds.** That is the whole test. I
   did not have to derive, infer, or interpolate a single one of them; each has a primary address on
   the row and at least one corroborating address elsewhere in the package.
2. **Every bound I need is attached to the claim it governs**, not to an appendix — *"There is no
   bounds section; if you are looking for one, you have the wrong package."* I never had to guess
   whether a number was usable; the package told me, at the number.
3. **The package discloses its own worst results.** The path-matching counterfactual (*"a drop rate
   understated by a quarter, against a 20% gate"*), bound (iv)'s *"No leg of this acceptance is
   independent of the selection population"*, and `05`'s entire not-carried inventory are all
   volunteered. A package that hands me the map of its own silences is one I can build against,
   because I can enumerate what to escalate instead of re-deriving what is already here.
4. **The unfillable slots are almost all 11-ii's own design surface, or writer-spec decisions
   this consult exists to make** — not defects in the evidence. U1 is the exception and it is a
   genuine gap in the measurement programme, but it is a gap I can *name precisely* because the
   package is explicit about what the digest does and does not mean. A vaguer package would have let
   me build the wrong thing confidently.
5. **Re-deriving would cost more and produce less.** A re-run costs `23456` embeds and `3456.789` s
   and would return the same three data with the same bounds — U1 is not fixed by re-running this
   design, it is fixed by *adding a datum to the design*. Demanding a re-run here would be
   theatre.

**CALL_AGAIN is conditional in one respect, and I state the condition rather than burying it:** I
escalate **U1 (change magnitude)** as a design fork before writing 11-ii, because slot 1's bound
licenses only the skip branch, and the re-measure branch is the one that spends the budget. I do not
treat that as a reason to reject the package; I treat it as the package having told me exactly where
my component's design decision lives.

⚠ *Contamination flag: `CALL_AGAIN` / `ROUTE_AROUND` is the routing test from the trust doctrine in
my auto-loaded project law (0.0-B), including the clause that a route-around on an honestly-rendered
surface is a failed acceptance. My verdict is not a courtesy to that clause — the three slots
genuinely fill — but the vocabulary and the framing are seeded, and a reader weighing this verdict
should know that.*

### Was my Part 0.1 trigger hit? — **No. It was met.** Plainly, and unsoftened:

I pre-registered: *the absence of labelled discrimination evidence — a control set with BOTH
known-absent and known-present queries and the resulting error rate in each direction at the chosen
threshold.*

**Both arms are present, with addresses:**
- Present-material arm: `01` → *"`F_portable` false-fire rate against the legacy labeled real
  union | ≤ 5% | `11 / 357` = `0.030812` | PASS"* over n = 357 of labelled real questions.
- Absent-material arm: `01` → *"legacy nonsense catch at `F_portable` | ≥ 60% | `321 / 345` =
  `0.930435` | PASS"* over n = 345, plus a second absent pool (`hold-out-absent`, n = 567) whose
  full distribution is in `02` and whose below-floor slice (456 / 18 / 438) is in `03`.

So the floor is **falsifiable**: a materially wrong floor would show up in one arm or the other, and
the package reports both arms at the same threshold. My trigger is not hit and I am not demanding a
re-run.

**And the part I will not soften, because it cuts against me rather than against the package:** the
evidence is met **and non-independent** — bound (iv), no leg held out. That does not un-meet my
trigger, because **I did not pre-register independence.** I asked for discrimination in both
directions and I got it. If I wanted a held-out arm I should have said so in 0.1, and I did not
think of it; the package thought of it, wrote it down against its own interest, and told me exactly
what it costs. **My pre-registration was one clause short, and the package is the reason I know
that** — which is close to the highest thing I can say about an evidence package.

---

### Q1 — Delete one third. What goes, what must never go?

I am answering by **reader cost**, which for a model reader is bytes-in-context, not page count. The
package is ~48 KB of markdown and a **90 KB** JSONL — the sample file alone is roughly two-thirds of
the whole artifact. So "one third" is reachable without touching a single analytic claim.

**GOES (in cut order):**
1. **~80% of `per-query-rows.jsonl` — the largest, cheapest cut by far.** 24 rows × 30 hits = 720
   hit objects, and the file's entire analytic job is *one worked example per verdict branch*. Keep
   4 rows — one fired-unanchored, one below-floor-but-anchored (the `39` case), one clean pass, one
   self-retrieval drop with its `self_retrieval_drop_cause` populated — and keep the full `k' = 30`
   array on **one** of them to demonstrate the `SURVEY_K`/`k'` distinction. Everything else is the
   same shape repeated. I used exactly one row this run and read 12 of its 30 hits.
2. **8 of `04`'s 10 pairs.** The page's stated job is *"The referent is visible, not paraphrased"* —
   two pairs discharge that. Ten do not make the referent more visible; they multiply a liability.
   For a model reader specifically, this page is the worst byte-for-byte in the package: it costs
   ~6.7 KB, it embeds a *"do not answer these"* instruction that every reader must spend attention
   obeying, and — measured on me this run — it is the one page that injects real out-of-package
   facts into a reader's context. Keep the derivation rule verbatim, keep the *"⚠ **The shipped
   probe-derivation function was NOT run, because it does not exist yet**"* disclosure, keep two
   pairs.
3. **The duplicate validity-floor table.** Identical three rows in `01` and `08`. Keep `08`'s (it
   sits with the drops that produce the counts) and replace `01`'s with a pointer.
4. **`01`'s second statement of bound (i)** (`00` records it appears there *"×2"*). Keep the
   statement that sits with the numbers in `06` and the once-per-artifact statements in `01` and
   `03`; a fourth restatement in the same document is redundancy without a new reader.
5. **`01`'s `F_portable − F_legacy = 0.111111`** — already argued in Part 2, and it is the one cut
   that *reduces* risk rather than trading against it.

**MUST NEVER GO** — these are the lines that made this package usable rather than merely readable:
1. **`00`'s three-population table** (`answered_probes` 411 · `probe_manifest_pool` 456 ·
   `verdict_not_fired_queries` 964) with *"a consumer that picks the wrong one gets a wrong
   denominator with no error anywhere."* Twelve lines that prevent a whole class of silent error.
   Highest value-per-byte in the package by a distance.
2. **The four bounds, IN SITU.** Not relocated, not summarised, not appendixed. Bound (iii) and
   bound (iv) especially — they are what stop a reader manufacturing a quality claim and a
   generalisation claim respectively.
3. **`08`'s path-matching counterfactual** (`33 / 456` = `0.072368` vs `45 / 456` = `0.098684`,
   *"understated by a quarter, against a 20% gate"*). The package's own falsification receipt. Delete
   it and the drop rate becomes a number nobody can second-guess.
4. **`05`'s "What this row does NOT carry" inventory.** This is the artifact that converts unknown
   unknowns into a worklist, and it is the single reason my verdict is CALL_AGAIN rather than
   ROUTE_AROUND.
5. **`07`'s four commitments** — the only decision rules in the package — together with the typed
   `determinism_leg` value and the per-field deltas that justify it.
6. **The `n` on every rate, and the `k / n` beside every decimal.** Cheap, and it is what let me
   re-check every number in Part 1.9 instead of trusting it.

Net: the cuts above are well past a third of the bytes, and every analytic claim survives intact.

### Q2 — The one change that would most increase my TRUST in the number

**Report the acceptance legs as a FUNCTION of the candidate floor — the admissible band — instead of
as one row at one value.**

Today `01` shows that `F_portable = 0.456789` clears both bars. It does not show that any *other*
floor would have failed them. If `0.35` and `0.55` also clear ≤5% false-fire and ≥60% catch on these
same sets, then the two legs do not **identify** the floor — they merely fail to reject it, and the
adopted value is being carried by the selection ladder alone while the acceptance table supplies the
appearance of validation. I currently cannot tell those two worlds apart, and that is the specific
thing that limits my trust in `0.456789` as opposed to my understanding of it.

The change: publish, for a sweep of candidate floors across the ladder, the two acceptance rates and
the resulting pass/fail — i.e. the **set of floors that pass both bars** — with `ci_low`/`ci_high`
and the selected point marked on it. Then the trust question becomes visible in one glance: is the
admissible band tight around the CI (the legs are discriminating), or does it run half the scale
(the legs are decoration)?

Three reasons this beats every runner-up:
- **It costs nothing to produce.** All response-best cosines and anchor flags for all 1740 queries
  already exist in the run; this is a re-aggregation, exactly the precedent `06` sets for itself —
  *"Aggregated from the run's own per-query rows — zero extra embeds, zero extra searches, no
  distortion of the run."*
- **It is a control, and the package currently has none for the floor itself.** `07` includes a
  deliberate failing control (*"one `Generator` object reused across both runs must NOT be
  bit-identical | PASS (differed, as required)"*) and `08` includes a counterfactual match key. The
  acceptance table — the load-bearing claim of the entire package — has neither. This supplies it.
- **It survives bound (iv).** It does not pretend to independence and does not need it: the question
  *"do these legs distinguish this floor from a materially different one on the same sets?"* is
  answerable on exactly the data already in hand, whereas a held-out leg (my runner-up, and the
  right thing to add eventually) requires new labelled data and a design decision.

⚠ *Contamination flag: "what wrong build would still pass this?" is verbatim law in my auto-loaded
context (0.0-B, FIXTURES MUST DISCRIMINATE), and this answer is that question pointed at a
threshold instead of a test suite. The provenance is borrowed; the gap is real and specific to this
package — the acceptance table has one column where it needs a curve.*

---

**STANDING BY.** Part 4 complete. Verdict: **CALL_AGAIN**, with U1 escalated as a design fork.
Package read; nothing outside it opened at any point in this run.
