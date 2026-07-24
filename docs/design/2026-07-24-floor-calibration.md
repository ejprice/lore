# Per-corpus cosine-floor calibration — packet 10 design

**Date:** 2026-07-24 · **Consultant:** fable-design-pkt10 (Fable design sidecar, worktree
`pkt10-floor-calibration-design` forked from `7f23223`) · **Findings of record:** #83
(primary), #87, #161; read with #160, #74, #75 · **Governing law:** DESIGN-LAW §3
(weak-match), §6 (measurement pins); binding operator spec of 2026-07-07 (carried in #83's
ruling trail; restated in `docs/plans/v2/10-floor-calibration-design.md`).
**Status:** DESIGN RECORD — awaiting operator ruling; packet 11 builds from
§Recommendation once ruled.

**The binding spec, restated:** (1) the drift trigger reruns calibration automatically —
re-measure + adopt, not disarm-and-wait; (2) drift measurement and thresholds are
determined here, measured never guessed; (3) interim state stays honest.

---

## 1. Measured context (all measurements dated 2026-07-24 unless stamped otherwise)

### 1.1 The live symptom, today

`lore_index()` against the deployed lore-lore instance (serving `/workspace` =
`feat/surreal-unification` @ `7f23223`), read 2026-07-24:

```
cosine_floor:
  state                : "stale"
  floor                : 0.50649
  measured_file_count  : 214
  current_file_count   : 2935
  measured fingerprint : b4dd657bebd6…
  current  fingerprint : f6e2ee347797…   (embedding schema version 2)
  note: "floor stale — re-measure needed: embedding schema fingerprint changed
         since measurement … the corpus was very likely fully re-embedded"
```

Two facts, worse than #161 recorded (2026-07-21: 214→353, count leg):

- The staleness today is on the **fingerprint leg**. Per DESIGN-LAW §3's binding
  invariant (external-validation amendment: *the floor is valid only for the exact
  embedder + prompt configuration it was measured on*), 0.50649 is not merely aging —
  it was measured in a **retired embedding space**. Every cosine in the corpus moved.
- The corpus is **2935 files**, 13.7× the measurement corpus. (The INDEX's "2764 by
  design" is already superseded; counts are a moving target — this design pins no
  count anywhere, per the packet-11 warning.)

### 1.2 What still serves against that floor (verified at source, worktree @ 7f23223)

`loremaster.search.SearchPipeline._to_result` appends the per-hit weak-match warning
whenever `_COSINE_WEAK_MATCH_FLOOR is not None and candidate.vector_cosine < floor` —
**no drift consult on that path**. `_cosine_absence_verdict`'s own docstring states it:
drift disarms *"the AGGREGATE verdict … the per-hit weak-match flag/substrate line are
unaffected."* So, as of 2026-07-24 at `7f23223`:

- the aggregate absence verdict is disarmed (honest under-claim, as designed);
- the **per-hit weak flags and the substrate keep serving**, comparing new-space cosines
  against an old-space floor. #161's live render receipt ("similarity 0.46 is below the
  0.51 floor") is this surface. The comparison is not "possibly drifted" — under a
  fingerprint change it is **numerically meaningless**.
- Corollary nobody has named: on every **non-lore deployment**, the per-hit flags serve
  against lore's baked-in 0.50649 today, with no calibration claim at all. #83's "no
  instance serves a WRONG verdict" is true of the aggregate only. (Surfaced to the
  operator in the packet report; this design closes it either way.)

### 1.3 The current drift trigger is edit-blind (source receipt)

`apply_cosine_floor_drift_check` has exactly two legs: embedding-schema fingerprint
(exact match) and **file COUNT** ±10% (`_COSINE_FLOOR_DRIFT_FILE_COUNT_TOLERANCE`).
But finding #74's own rot mechanism — recorded verbatim in the stamp's comment block in
`search.py` — was *"a routine, unrelated edit to the very method it asks about changed
that method's own embedding — the floor never moved, but the corpus underneath it
did."* **An edit changes no file count.** A session that rewrites half the corpus in
place trips neither leg. The trigger, as built, cannot detect the mechanism that
motivated it; it detects only bulk adds/removes (#161's case) and config changes
(today's case). §5 replaces the count leg with a churn leg.

### 1.4 The #87 accounting, verified at source (design question 4)

`Indexer.index_status` (loremaster/index/indexer.py): `files_indexed` = count of
manifest rows with `state == STATE_INDEXED`, summed **across every tier**, zero embeds.
That is the number both the stamp and the drift check consume
(`AppContext._build_index_status` → `apply_cosine_floor_drift_check`).

#87's observed tension (state=`measured` while 214 ≠ 207) resolves to #87's own
possibility (1): a −3.3% shift is inside the 10% tolerance, so `measured` with
`note: null` is per design. The render is honest **but unexplained** — it shows two
disagreeing counts with no hint that a tolerance exists, and #74's resolution note
("any file-count change disarms") overstated the mechanism. The later 33.6%-shift
observation in #87's routing note (2026-07-14) is the count leg working (state stale,
aggregate disarmed) while the per-hit surface kept serving — i.e. §1.2, not a second
accounting bug. Fixes fold into the serving contract in §7.

Residual accounting gaps, named: the aggregate count conflates tiers (a receipts dump
and a production-code churn read identically), and the original stamp was taken from a
`lore_index()` read *"the nearest available proxy"* after the survey ran — the
instrument never captured its own corpus snapshot (admitted in the stamp's comment).
Both fixed in §6/§7.

### 1.5 What produced 0.50649 (prior art, not re-derived)

`scripts/search_score_survey.py` (committed, deterministic): four query groups — 35
eval-XML prose questions, 15 fixed nonsense queries, 15 corpus-sampled identifiers,
6 implementation-vocabulary informant probes — scored against the **identical
production predicate** (identity-pinned imports, S4b audit finding #1), floor chosen by
`choose_cosine_floor`'s dominance ordering (max catch → min false-fire → max floor)
under pre-registered bars `D2_MAX_FALSE_FIRE_RATE = 0.05`,
`D2_MIN_NONSENSE_CATCH_RATE = 0.6`, substrate gate `D1_MIN_MEDIAN_SPREAD = 0.05`.
Result (stamped 2026-07-07): floor 0.50649, false-fire 1/56, catch 15/15.

**Not executed this session:** the script's own default store coordinate is
`ws://127.0.0.1:18500/rpc` — the production store, which this packet's brief forbids
touching. I read the instrument end to end; I did not run it. (The per-instance runner
in §Recommendation retires this hardcoded coordinate anyway — a portable runner runs
against *its own* instance's store by construction.)

---

## 2. Question 5 first — is ONE floor over a mixed corpus the right model?

The corpus is now production code + repo docs + archived agent receipts + two static
vendor tiers (`surrealdb-docs`, `surrealql-tests`) in one semantic space. The floor's
served promise is *"the range real answers measure on this corpus."* Three candidate
models:

**M-A — one pooled floor, per instance (status-quo shape, portably measured).**
Honest for unscoped queries: the aggregate verdict's claim ("likely no direct answer
indexed") quantifies over the whole corpus, and the whole corpus is what the query
competed against. Risk: if per-tier cosine distributions differ materially (plausible —
#74's false-fires appeared exactly when design PROSE entered a code-dominated corpus;
prose↔query geometry differs from code↔query geometry), a pooled floor over-fires on
the low-cosine sub-population and under-fires on the high one.

**M-B — per-tier floors, serving keyed on the query's scope.** `lore_search` already
takes a `tier` filter. A tier-scoped search competes only against that tier, so that
tier's floor is the honest bar; an unscoped search uses the pooled floor. Each floor is
measured over exactly the population its queries compete against. Cost: T+1
distributions to measure (same instrument, stratified), T+1 rows to persist, a serving
lookup keyed on the request's tier filter.

**M-C — separate spaces / receipts out of the space entirely.** This is #160's maximal
reading, not a floor mechanism. It reshapes the corpus; it does not calibrate it.

**Ruling recommendation: measure stratified, adopt pooled first, pre-register the
per-tier upgrade.** Whether tiers separate is an empirical question, and this design's
own law says measured-never-guessed — so the portable survey (§3) **always** captures
and persists per-tier answered/absent distributions alongside the pooled ones, and the
first build **adopts only the pooled floor**. A pre-registered conditional rule (bars
fixed *before* the first stratified run, exact values proposed in §Recommendation R8)
upgrades tier-scoped serving to per-tier floors **only if the measured separation
demands it**. That keeps packet 11 at size, makes the M-A→M-B decision data's rather
than anyone's, and produces the separation measurement as a side effect of the first
run on every instance.

**Why this dissolves the "#160 first" sequencing (#161's ask).** Every #160 candidate
outcome is absorbed by this design rather than reshaping it:
- *chunk-header dated-record marker* (the #160-preferred fix): render-side; changes no
  embedding, no distribution, no floor.
- *rank penalty for dated records:* reorders served hits; cosines unchanged; the
  verdict already evaluates **max cosine of shown hits**, not rank — unaffected. (If a
  penalty ever *excludes* hits from the shown set, that is a shown-set change the
  verdict already handles by construction.)
- *receipts to a separate tier or out of the space:* a corpus reshape — the churn leg
  (§5) triggers, the instance re-measures, the floor adapts automatically. That is the
  designed-for case, not an exception.

So packet 10/11 need not wait on #160, and #160 need not hurry for packet 11. This is
presented as a fork (F2) because #161 explicitly requested the opposite ordering — the
operator rules, and the evidence that would change my recommendation is a #160 ruling
that *removes receipts from the search surface entirely AND retroactively*, in which
case re-measuring before that lands would calibrate against a corpus about to vanish
(cost: one extra automatic re-measure — the mechanism absorbs even that).

---

## 3. Question 1 — portable labeled query sets

Group by group, against the four that produced 0.50649 (§1.5):

**Identifier probes — port as-is.** `sample_identifier_queries` already derives them
from the live corpus deterministically (sorted distinct identities, every Nth). No
change beyond per-tier stratified sampling (§2).

**Answered probes — self-supervised, with a named optimism bias.** For each
deterministically sampled chunk (stratified per tier, fixed per-scope sample sizes,
§Recommendation R3): derive a natural-language query from the chunk's own descriptive
text — a code chunk's docstring first paragraph; a doc/markdown chunk's heading plus
first sentence; skip chunks with no derivable text (and count the skips). Ground truth
is the source chunk itself. **Bias, stated:** the query text is drawn from (often
verbatim inside) its target — even under voyage-4's asymmetric query/document prompts
this inflates cosines relative to genuinely independent human phrasings, so a floor
percentile taken over self-supervised answered cosines sits HIGHER than one over real
queries, which pushes toward **more** false absence verdicts. The lab-validation
protocol below measures this bias on the one corpus that has ground truth; it is never
assumed small.

**Known-absent probes — the hold-out construction (the genuinely new piece).** The
fixed `NONSENSE_QUERIES` do **not** port: their absences are lore-relative ("rate
limiting middleware per client IP address" is nonsense here and a real feature in half
the world's web repos — #83 said this; the receipt is the list itself). Portable
replacement: **leave-source-file-out scoring of the same self-supervised probes.** Each
answered probe is scored twice from one search call (capture k′ > k hits to survive
filtering):
- *answered leg:* max-cosine over all shown hits (ground truth: its own chunk);
- *absent leg:* max-cosine over hits **excluding the probe's source file** — the true
  answer is removed by construction, so this samples exactly the distribution the
  verdict must fire on: "the corpus's best response when the real answer is not there,"
  in the corpus's own vocabulary.

Residual, named with its direction: a semantic twin in another file (a wrapper, a fake,
a test exercising the same mechanism) can legitimately answer the held-out query, so
some absent-leg samples are not truly absent → measured catch **understates** true
catch → the adoption bar gets *harder*, never easier. The error is conservative on the
guarded surface (D2 is precision-first; catch is the licensing bar). One embedding pass
serves both legs — the portable survey costs the same as the answered survey alone.

**Implementation-vocabulary probes — do not port; their ROLE ports.** The six lore
probes are verbatim informant receipts with lore ground truths. Their function —
breaking the eval-question monoculture that made the original 4.0% false-fire blind to
a whole query class (#74) — is partially covered by docstring-shaped probes (which are
description-shaped, not quiz-shaped). The residual is honest: a fresh corpus has no
informant-grade real-query samples until it accumulates its own. Two mitigations:
(a) a per-project config hook (`calibration.extra_answered_queries` /
`extra_absent_queries` in `lore.yaml`) so an operator MAY supply labeled sets that
widen the union — never required, always additive; (b) lore's own instance keeps its
legacy labeled groups as a regression control forever.

**The lab-validation protocol (the instrument's own satisfiability receipt).** Before
the portable instrument is trusted anywhere, it is graded on lore's corpus — the one
corpus where both instruments exist. One run, both instruments, same corpus snapshot:
1. legacy labeled survey (56 real + 15 nonsense) → floor F_legacy (this is also the
   re-measure #161 asks for);
2. portable self-supervised instrument → floor F_portable;
3. acceptance, pre-registered: F_portable's false-fire measured against the **legacy
   labeled real union** ≤ 5%, AND legacy nonsense catch at F_portable ≥ 60% — i.e. the
   portable floor must pass the original bars *as judged by the original labeled
   sets*. Report the F_legacy↔F_portable delta as the instrument's measured bias.
If it fails, the portable instrument is INSUFFICIENT as built → back to design
(probe-text derivation, percentile choice), not to shipping with a caveat.

**What the bars' promises become — said explicitly, as the packet demands.**
False-fire ≤5% survives portably (measured on self-supervised answered + identifier
unions). Catch ≥60% survives portably **re-denominated over hold-out absents**
(conservative direction as above). What is genuinely weaker: "real answers" in the
served wording is calibrated from *the corpus's own self-descriptions*, not from human
questions. If lab validation passes, the current wording remains defensible as-is; if
the operator judges otherwise, the wording change is a ruled-law amendment (packet 11
Scope OUT) — fork F3. On corpora too small to yield the minimum probe counts, the bars
are not weakened — the verdict simply stays disarmed with an honest
`insufficient_corpus` state (§7): small corpora get under-claiming, never a diluted
promise.

---

## 4. Question 2 — what "pre-registered" means under automatic recalibration

The original rule assumed a human ran the survey and could be tempted to move the bars
after seeing the table; pre-registration bound the human. Under automation the
temptation moves and the binding must move with it:

1. **The bars and the selection rule are versioned code, shared by construction.** The
   ceiling/catch/substrate constants and the dominance-ordered `choose_cosine_floor`
   already live as named constants + one function, identity-pinned against production's
   predicate. The runner moves into `loremaster` (§7) and *imports the same objects* —
   an automatic run structurally cannot amend a bar. Amendment = code change + operator
   ruling, exactly as for any measured constant (search.py's own "ADOPTED, never
   re-guessed" discipline).
2. **Every adoption row records the bars it ran under** (values + instrument version).
   Bar drift across adoptions becomes an auditable query, not an archaeology project.
3. **Adoption gains validity gates the human implicitly provided.** A human wouldn't
   adopt a floor from a half-indexed corpus or a failed run; the machine must be told:
   - *minimum samples* per scope (proposed: ≥30 answered probes with derivable text,
     ≥15 identifier probes, ≥30 absent-leg samples; below → `insufficient_corpus`,
     disarmed, honest note — no adoption);
   - *probe self-retrieval sanity:* an answered probe that fails to retrieve its own
     chunk in top-k′ is dropped AND counted; drop-rate > 20% fails the run
     (`measurement_failed` + a finding — the instrument, not the corpus, is suspect);
   - *settled-index gate:* the corpus snapshot (fingerprint, counts, churn cursor) is
     captured at run start and re-verified at run end; a mid-run change discards the
     run and re-queues it — a measurement of a moving corpus is not a measurement;
   - *determinism control:* same corpus + same config ⇒ bit-identical floor (sampling
     is deterministic, the embedder is pinned) — pinned by a test, and doubling as the
     flap-guard: a no-drift re-measure reproduces its predecessor.
4. **The catch bar keeps its meaning as a LICENSE, not a formality.** Measured hold-out
   catch < 60% ⇒ the floor is recorded (`measured_not_adopted`) and the aggregate
   verdict stays disarmed on that instance. Under-claim is cheap; that was the ruling's
   whole asymmetry and automation does not soften it.
5. **Failures escalate; routine adoptions log.** `measurement_failed` files a deduped
   finding (CalibrationEngine's drift-finding seam is the in-repo precedent). A routine
   drift-triggered adoption is normal operation — it logs a store row and renders in
   `lore_index`, and does NOT spam the findings ledger.

---

## 5. Question 3 — drift measurement, thresholds, and the re-measure's own bounds

Three trigger legs replace the current two (§1.3 receipt: the count leg misses edits):

**Leg 1 — embedding-schema fingerprint, exact match (kept, unconditional).** Any
embedder/prompt/chunker change invalidates the floor by DESIGN-LAW §3's binding
invariant. Automation nuance: the re-measure is queued but can only run *after* the
rebuild machinery finishes re-embedding and the index settles (the settled-index gate
does this for free). During that window the floor is dead, not aging — see the
interim-honesty rule below.

**Leg 2 — cumulative re-embed churn (replaces the file-count leg).** The indexer knows
every chunk it re-embeds. The stamp records a churn cursor at measurement time; the
trigger fires when the fraction of the corpus re-embedded since the stamp (adds +
removes + **edits**, at chunk granularity) exceeds the tolerance. This subsumes
everything the count leg caught (#161's bulk archive dump) and closes the edit
blindness (#74's actual mechanism). Threshold: **inherit 10% initially — declared as a
cost-bound pragmatic bar, not a measured error bound.** No churn threshold can bound
floor error (one edit moved one query across the floor in #74); what the tolerance
actually prices is re-measure frequency, and under automation a false fire costs one
cheap survey that reproduces the old floor (the determinism control). The
measure-then-tune structure, per the deferral law: every adoption row records
churn-at-trigger, floor delta, and run cost; **decision point: after 10 automatic
adoptions (or 3 months, whichever first) the operator reviews floor-delta-vs-churn
history and re-sets the tolerance from data.** Named data, named decider, named date.

**Leg 3 — live per-hit cosine distributions (packet 35's input, interface designed
now, armed later).** Contract for packet 35: a rolling window of per-query
`max_cosine_of_response` (+ whether the verdict fired), summarized (n, median, p5) and
compared against the adoption row's stamped survey distribution. **The comparison
threshold must be measured by packet 35** — the natural run-to-run variance of the live
signal on a stable corpus — and pre-registered before the leg arms, per the standing
exploratory-signal law (prior art §7.3: no post-hoc thresholds from the same data).
Until then the leg is absent, not defaulted. Value over legs 1–2: it is the only leg
that sees drift the index never wrote — query-mix shift, the corpus's vocabulary
migrating out from under a stable file set.

**The re-measure's own false-fire bounds and discipline:**
- *Single-flight:* one measurement in flight per instance, coordinated through the
  store via the shared retry driver (`_txn.retry_on_conflict` — DESIGN-LAW §5; ONE
  IMPLEMENTATION law: no private lease loop).
- *Quiescence over clocks:* the trigger defers while the index is unsettled and dedupes
  while a run is queued/running. No invented cooldown constant; a continuously-churning
  corpus renders `stale_remeasuring` honestly until it settles. (A clock-based cooldown
  is a guessed constant with a failure mode; quiescence is a measured condition.)
- *Flap bound:* determinism control (§4) — an unchanged corpus reproduces its floor
  exactly, so back-to-back triggers converge instead of oscillating.
- *Cost, measured not assumed:* each run records embed count and wall-clock in its row.
  Expected order: ~100 query embeds against the instance's own TEI + k′-deep searches —
  but the row, not this sentence, is the authority.

**Interim honesty (binding spec point 3), sharpened by §1.2:** while stale or
re-measuring —
- the aggregate verdict is disarmed (as today);
- the **per-hit weak flag disarms on fingerprint-leg staleness** (an old-space floor
  against new-space cosines is a meaningless comparison, live today) but **stays live
  on churn-leg staleness** (same space, aging corpus — the per-hit surface's 10–20%
  false tolerance was ruled for exactly this softness, and automation makes the window
  minutes long). This is a serving-behavior change → fork F4;
- the substrate (`sim 0.62`) never disarms — it is claim-free by construction;
- the rendered state says which leg fired and that re-measurement is queued/running —
  the disarm-and-wait note's "re-measure needed" becomes "re-measuring" with a live
  status, which is the whole point of the packet.

---

## 6. Question 4 — the #87 fold (accounting truthfulness as a serving contract)

Verified mechanism in §1.4. Contract changes:

1. **The instrument stamps itself.** The runner captures its own corpus snapshot
   (fingerprint, file count, chunk count, per-tier counts, churn cursor) from the same
   manifest read, atomically at run start — retiring the "nearest available proxy"
   stamp admitted in search.py's comment. A floor row's provenance is the run's own
   observation, never a neighboring read.
2. **Always render the shift, not only the breach.** `lore_index`'s cosine_floor block
   renders current shift vs tolerance in every state ("churn 3.3% of 10% tolerance"),
   so #87's honest-but-unexplained render class (two disagreeing counts, no visible
   rule) is structurally gone. The state string alone never carries the whole truth.
3. **Per-tier counts in the row and the render.** One aggregate count conflates a
   receipts dump with production churn (#161's growth was 100% docs). Per-tier
   accounting feeds the Q5 stratification and gives the churn leg tier resolution for
   free.
4. **Closed-domain, mutually distinct state strings** (§7) — the #4 defect class.
   (#4 itself is RESOLVED — P8d W3 shipped `integrity_failed`; packet 11's "if still
   open, fold its fix in" entry check is already satisfied. The pin worth carrying:
   the new state set ships with an exact-set distinctness test.)

---

## 7. The engine: states, persistence, serving

**Shape:** a floor-calibration engine in `loremaster` (beside
`calibration/engine.py`, whose probe-at-boot / drift-adopt / findings-seam pattern is
the in-repo precedent — *pattern by reuse of its seams where genuinely shared, never a
clone of its loops*; ONE IMPLEMENTATION law). `scripts/search_score_survey.py` becomes
a thin CLI over the same engine (manual runs + the lab-validation mode); the selection
rule, predicates, and bars remain single objects imported everywhere, with the
existing identity-pin tests extended to the engine.

**Per-instance persistence (that instance's store; DDL per
`docs/reference/surrealdb-31-capabilities.md` — packet 11's required first read):**
one row per (scope, measurement), append-only with latest-adopted resolution; scope ∈
{`pooled`, `tier:<name>`}. Fields: floor · adopted flag · state · measured_at ·
instrument_version · bars used · results (false-fire, hold-out catch, n per group,
substrate spread median, self-retrieval drop-rate) · corpus snapshot (embedding-schema
fingerprint, embedder+prompt identity, file/chunk/per-tier counts, churn cursor) · run
cost (embeds, wall-clock) · trigger (which leg fired). History stays: the leg-2 tuning
decision point (§5) reads it.

**The code constants retire from serving.** `_COSINE_WEAK_MATCH_FLOOR` and its stamp
stop being the served truth on any instance; serving reads the instance's adopted
pooled row (in-process cached, refreshed on status reads and adoptions). Retirement
follows repo rename-sweep law: bare-pattern greps for the retired constants, test-tree
sweep for pins certifying the old world, and lore's legacy groups re-homed as the
regression control, not deleted.

**States (closed set, each string distinct, note mandatory unless `measured`):**

| state | floor served? | aggregate verdict | per-hit flag |
|---|---|---|---|
| `unmeasured` (fresh instance; initial run queued — the boot-probe pattern) | no | disarmed | dark |
| `measuring` (first run in flight) | no | disarmed | dark |
| `measured` (adopted; bars met) | yes | armed | live |
| `measured_not_adopted` (catch bar failed) | yes (per-hit only) | disarmed | live |
| `stale_remeasuring` (leg fired; run queued/in flight) | per F4 (§5) | disarmed | leg-dependent (F4) |
| `measurement_failed` (validity gate failed; finding filed) | last adopted if fingerprint-valid, else no | disarmed | leg-dependent (F4) |
| `insufficient_corpus` (min samples unreachable) | no | disarmed | dark |
| `disabled` (config off) | no | disarmed | dark |

The non-lore interim (#83's binding point 3) falls out: a fresh DI deployment boots
`unmeasured` → auto-measures its own floor → `measured` (or lands in an honest
disarmed state) — never lore's constant, never a permanent unsatisfiable
"re-measure needed."

---

## 8. Buildability against packet 11

Scope IN maps one-to-one: measurement runner + persistence (R1–R3, R6) · drift
trigger → automatic re-measure + adopt with ruled thresholds (R4) · lore_index honest
states + #87 accounting at source (R5) · floor bound to embedder+prompt fingerprint
(leg 1). Additions this design makes inside that envelope: the hold-out absent leg
(same probe calls, one filter), stratified per-tier *reporting* (same instrument), the
per-hit fingerprint gate (one conditional, F4), and the one-time lab-validation run on
lore. Deliberately **deferred out of 11**: per-tier *adoption/serving* (pre-registered
conditional R8 — a follow-up packet if the measured separation demands it) and leg 3
(packet 35 owns its threshold measurement). Verdict: **the design is buildable into
packet 11's Scope IN at its ~0.25 wu sizing.** If the operator instead rules immediate
per-tier serving (F1), packet 11 crosses its own ≥0.30 split line and should split at
kickoff, per its header.

---

## Recommendation

> **2026-07-24, post-ruling:** R1–R8 stand as written; Addendum B §B7 carries the
> consolidated build ORDER a packet-11 builder executes from, and Addendum B §B6 the
> fork dispositions. Read R1–R8 for the WHAT, B7 for the sequence.

Execute as one engine, in this order:

- **R1 — Portable probe sets:** identifier sampling as-is; self-supervised answered
  probes (docstring/heading-derived, deterministic, stratified per tier, skips
  counted); hold-out absent legs from the same calls (source-file exclusion, k′ > k).
  Lore's legacy labeled groups become that instance's standing regression control.
- **R2 — Lab validation before trust:** one dual-instrument run on lore's corpus
  (which is also #161's overdue re-measure). Pre-registered acceptance: the portable
  floor passes the ORIGINAL bars as judged by the LEGACY labeled sets (§3). Fail ⇒
  instrument returns to design; nothing ships on a caveat.
- **R3 — Pre-registration as code:** bars + dominance rule imported by runner and
  serving alike; adoption rows record bars + instrument version; validity gates: min
  samples (30/15/30), self-retrieval drop ≤20%, settled-index snapshot start-and-end,
  determinism pin.
- **R4 — Trigger legs:** fingerprint exact-match (re-measure after rebuild settles);
  churn-fraction ≥10% at chunk granularity (edits count; tolerance re-set from
  adoption-row history at the named decision point — 10 adoptions or 3 months);
  packet-35 live-distribution leg specified but unarmed until its threshold is
  measured. Single-flight via the shared retry driver; quiescence-gated, no clock
  constants.
- **R5 — Serving contract:** the §7 closed state set with exact-set distinctness pin;
  shift-vs-tolerance rendered in every state; per-tier counts in row and render; the
  runner stamps its own snapshot (#87 closed at source).
- **R6 — Retire the constants:** `_COSINE_WEAK_MATCH_FLOOR`/stamp leave the serving
  path on every instance (lore's included — dogfood); rename-sweep law applies.
- **R7 — Interim honesty:** aggregate disarmed while not `measured`; per-hit flag
  disarmed on fingerprint-leg staleness, live on churn-leg staleness (F4); substrate
  always on; every non-measured state carries a note naming the leg and the run
  status.
- **R8 — Per-tier upgrade, pre-registered now, decided by data:** if any tier's
  answered-leg p5 differs from the pooled p5 by more than the pooled survey's own
  observed answered-leg p5↔p10 gap (a scale-free separation bar derived from the same
  run, fixed here before any stratified run exists), tier-scoped serving upgrades to
  that tier's floor in a follow-up packet. Until then, pooled serves everything.

## Forks awaiting operator ruling

> **2026-07-24, post-ruling ("let it decide the details"):** F1/F2/F4/F5/F6 are now
> DECIDED BY DELEGATION — dispositions with rationale in Addendum B §B6. **F3 was
> first routed to the operator and that was a MIS-FRAME (twice over — operator
> challenge, same day): the corrected disposition is a CLIENT CONSULT, Addendum C.**
> The list below is preserved as the record of the original option space.

- **F1 — Corpus model (Q5):** pooled-first + measured per-tier conditional (R8) —
  *recommended* — vs immediate per-tier serving (packet 11 splits) vs pooled-forever.
  Evidence that changes it: the first stratified run's per-tier distributions.
- **F2 — #160 sequencing:** proceed now; the floor design is invariant to every #160
  outcome (§2) — *recommended* — vs holding packet 11 for #160. Evidence that changes
  it: a #160 ruling that removes receipts from the search surface retroactively.
- **F3 — Verdict wording under self-supervised calibration:** keep the ruled wording
  iff lab validation (R2) passes — *recommended*; else the wording amendment comes
  back to the operator (wording is ruled law; not touched here).
- **F4 — Per-hit flag during staleness:** disarm on fingerprint-leg, stay live on
  churn-leg — *recommended* (today it serves old-space comparisons, §1.2) — vs
  keep-current (never disarm) vs disarm-on-any-staleness. Serving behavior change
  either way; needs the ruling.
- **F5 — Known-absent strategy:** hold-out probes with the conservative-direction
  residual — *recommended* — vs verdict-dark-on-foreign-corpora until an operator
  supplies labeled absents via the config hook. Evidence: R2's catch comparison.
- **F6 — Churn tolerance:** inherit 10% with the named re-set decision point —
  *recommended* — vs measuring a tolerance before first arming (delays the packet for
  a number whose cost of being wrong is one cheap survey run).

---

## Addendum A (2026-07-24, same day — post lead-filed #176/#177 and #179)

Written after the lead's independent verification pass; three amendments, each with
its receipt. The §Recommendation numbering stands; R4/R5/R7 are sharpened below.

**A1 — Armedness must be evaluated at the serving seam, never warmed by an unrelated
tool call (#176's second-order fact; amends §5 and §7).** Re-derived at `7f23223`:
`apply_cosine_floor_drift_check` has exactly ONE production caller —
`AppContext._build_index_status` — and `_CosineFloorRuntimeState.disarmed_by_drift`
defaults to `False`. So in any server process where `lore_index()` has never been
called, the aggregate verdict is **armed against a possibly-drifted floor**: the
disarm is a cache warmed by an unrelated tool call, and its unevaluated default is
fail-OPEN. (This design's §1.1 measurement itself warmed that cache on the production
process — the instrument arming the safety it was reading.) My own §7 as first
committed inherited a milder copy of the defect ("in-process cached, refreshed on
status reads and adoptions"). Amended design, binding on packet 11:
- trigger evaluation is **event-driven at the indexer's own chokepoints** (boot, and
  the post-sync/post-sweep chokepoints that already stamp
  `META_LAST_SYNC_AT_KEY`/`META_LAST_SWEEP_AT_KEY`) plus at every adoption —
  `lore_index` becomes a **pure read** of engine state, never the thing that computes
  it;
- the fail-safe default inverts: **unevaluated ⇒ disarmed** (state `unmeasured` /
  `measuring` in the §7 table — under-claim until the engine has actually evaluated),
  never armed-by-default;
- F4's per-hit gate reads the same engine state at the same serving seam — one
  evaluation, every consumer, no second cache (ONE IMPLEMENTATION).
This does not change F4's recommendation; it strengthens its rationale and closes the
dark-process hole on the aggregate too.

**A2 — The survey script's write-surface, answered for #177 (re-derived at
`7f23223`).** The script's own query surface is read-only by construction and
documented as such (`survey()`'s docstring, S4b audit finding #2: `scroll` +
`hybrid_search` only; it deliberately never calls `store.ensure_ready()`, which IS a
schema-DDL write transaction). But it is not literally write-free at the wire: the
lazy connect (`SurrealStore._ensure_connection` → `_txn.bootstrap_session`) transmits
`DEFINE NAMESPACE IF NOT EXISTS` + `use()` + `DEFINE DATABASE IF NOT EXISTS` on first
use. Against the existing production ns/db these no-op by the engine's IF-NOT-EXISTS
semantics (`docs/reference/surrealdb-31-capabilities.md` — the #107 fact). The real
residual hazard is a **mistyped coordinate**: a wrong namespace/database against the
production endpoint would be silently MATERIALIZED as empty ns/db, not rejected. The
per-instance runner (§Recommendation) retires the hardcoded production coordinate;
until then, #177's entry-check hazard stands as filed.

**A3 — The foreign-instance per-hit surface is now ledgered as finding #179** (filed
2026-07-24 by this packet, scoped to what #176 does not cover: non-lore deployments
serving lore-calibrated per-hit judgements with no validity claim on the host corpus).
R6/R7 + F4 are its closure path; packet 11 resolves it alongside #83/#87/#161 — its
resolution note should record that the constant's retirement, not any count, closed it.

---

## Addendum B (2026-07-24, later same day — the operator's architecture ruling: the remediation half)

**B0 — The ruling, and what it changes here.** Operator, 2026-07-24, relayed by the
packet lead and recorded durably in lore memory (id `f464cfda-f871-5149-8c95-4bbf443960a8`,
kind=decision — re-read from the store before writing this addendum, not from the
inbox): the floor is **store state in SurrealDB**; staleness ⇒ **recalculation**
(disarm-and-wait is dead; frequent staleness on an active codebase is the NORMAL
LOOP); the whole detect → re-measure → write loop runs **in-container** — no outside
caller, no host toolchain, no operator-run script in the durable path (the #166
architectural shape); the high-level design stands, details delegated. Points 1–2
were already this design's R6/R4 (the 2026-07-07 binding spec required automatic
re-measure); Addendum A1 already owns the DETECTION half. What this addendum adds:
the in-container REMEDIATION mechanics, the thrash/cost story "often stale" demands,
and the fork dispositions the delegation authorizes.

**B1 — Execution home: an AppContext-owned async engine task. Packet 30 dependency
REJECTED.** The loop runs in the server process each container already runs: trigger
evaluation at A1's chokepoints (boot, post-sync, post-sweep, adoption); the
re-measure itself is an asyncio background task owned by the app context — the
CalibrationEngine boot-probe precedent, extended from boot-only to chokepoint-driven.
Everything the runner needs is already in-process: the store handle, the query-embed
seam the search path uses, the production predicate. Packet 30's enrichment worker
was considered as the execution home and rejected: it is wave F, depends on packet
29, and is loresage-coupled — calibration needs no LLM, and chaining packet 11 behind
wave F buys nothing. No new dependency.

**B2 — Thrash bounds and cost (the "often" failure mode, addressed head-on).**
- *Per-run cost is CONSTANT-BOUNDED, not corpus-proportional.* Probe counts are
  fixed-N by design (R3 minimums; per-tier stratified reporting allocates from the
  same fixed budget) → order tens of query embeds + k′-deep searches + one write
  txn, independent of corpus size. Contrast: the 11a/11b reconciler's re-embed costs
  ARE corpus-proportional, and the operator ruled NO cost gate even there (#171 §13:
  "reconciles run unattended") — a constant-cost loop needs none a fortiori. Each
  adoption row records embeds + wall-clock; the row, not this paragraph, is the
  authority on cost.
- *Rate is structurally capped.* Chokepoint EVALUATIONS are cheap comparisons and run
  every time; RUNS launch only at boot / post-sweep with in-flight zero. Single-flight
  with coalescing: N triggers during a run set one re-run flag, never a queue of N. A
  run whose end snapshot disagrees with its start snapshot is discarded and re-queued
  to the NEXT post-sweep completion — a clock-free debounce that defers to the
  system's own settling signal instead of burning discarded surveys in a tight loop.
  Net bound: ≤1 run per sweep cycle per instance; in steady state, one run per
  tolerance-crossing of churn.

**B3 — Composition with 11a/11b (#168 → #171): the two loops must not fight.**
- *Post-11b, leg 1 keys on the reconciler's CHANGE CLASS, not the raw fingerprint*:
  vector-identity change → floor invalid, re-measure queued for after the reconcile
  completes; chunk-boundary change → flows through leg 2 as ACTUAL re-embed counts;
  additive chunker-map change (#168's `.xyz` case) → zero re-embeds → zero churn →
  **no re-measure**. The #168 false-invalidation class dies for the floor exactly as
  it dies for embeddings.
- *The churn cursor counts chunk re-embed commits at the ONE shared embed wrapper*
  (#169/11a already route every embed through it) — hook that seam, never a parallel
  counter (ONE IMPLEMENTATION).
- *Pre-11b interim:* packet 11 may ship keying leg 1 on the raw fingerprint; an
  additive chunker change then over-fires exactly one constant-cost survey —
  accepted, bounded, self-correcting when 11b lands. No hard dependency in either
  direction; if 11a/11b land first, build the change-class keying directly.

**B4 — Store schema + migration mechanism (required read honored:
`docs/reference/surrealdb-31-capabilities.md`, esp. §1.1–§1.3, §1.5, §5 — cited,
never re-transcribed).** A NEW table for floor calibration: `DEFINE TABLE IF NOT
EXISTS` + every field `DEFINE FIELD OVERWRITE` per the §1.1 decision rule; `ALTER`
is the documented trap (§1.3); any index rides `IF NOT EXISTS`, never `OVERWRITE`
(§1.5). Rows are **append-only measurements** (each run writes a new row — history
carries the F6 tuning data and takes no field-migration pressure) plus one minted
head pointer per scope. The head mint and the single-flight lease are hot rows →
`_txn.retry_on_conflict` is the ONE driver (DESIGN-LAW §5; #102/#120 receipts); a
private retry loop of any shape is the defect those findings exist to remove.
Multi-statement DDL rides the per-statement-checked `_txn` path, never bare
`query()` (the statement[0]-only validation gotcha).

**B5 — CalibrationEngine: sibling engine, shared seams; wholesale reuse REJECTED at
source.** `calibration/engine.py`'s measurement loop is inseparable from token-ratio
mechanics — its measurement compares token-weighted live totals against a SHIPPED
baseline corpus, and its state set assumes a committed constant to scale. A cosine
survey shares none of that mechanism; forcing it through the same loop would be
routing-not-sharing. What IS shared, reused not cloned: (a) the findings seam
Protocol (`has_open_drift_finding` / `report_drift_finding` — deduped filing; reuse
as-is for `measurement_failed` rows); (b) the `from_engine_status` construction-seam
pattern for the render model; (c) the closed-distinct-state discipline (#4's lesson)
with the exact-set pin. If the build uncovers a further genuinely-shared policy
(e.g. probe-task lifecycle), extract a helper both engines call — escalate, never
copy (repo law).

**B6 — Fork dispositions under "let it decide the details."**
- **F1 — DECIDED:** pooled-first + pre-registered per-tier upgrade (R8).
- **F2 — DECIDED:** proceed without #160; the design is #160-outcome-invariant (§2).
- **F4 — DECIDED as specced:** the aggregate verdict is disarmed whenever state ≠
  `measured` — including the whole remediation window (A1's unevaluated ⇒ disarmed
  holds there: a running remediation is `measuring`/`stale_remeasuring`, both ≠
  `measured`). The per-hit flag is DARK under vector-identity staleness (old-space
  comparison is meaningless — §1.2's live receipt) and LIVE-on-the-old-floor under
  churn staleness until adoption swaps it. The substrate never disarms.
- **F5 — DECIDED:** hold-out absents + the config hook; re-opens only if R2's lab
  validation fails its catch leg.
- **F6 — DECIDED as the default:** churn tolerance 10% inherited, with the named
  re-tune point (10 automatic adoptions or 3 months; operator reviews the
  floor-delta-vs-churn history the rows accumulate).
- **F3 — RE-DISPOSED (Addendum C, same day):** first framed here as "the one operator
  fork" — that framing was WRONG twice over (operator challenge, 2026-07-24), and the
  corrected disposition is a CLIENT CONSULT with a named decision point. See C2–C4;
  this entry is preserved as the record of the error.

**B7 — Consolidated build order for packet 11** (the sequence a builder executes;
scope is R1–R8 + Addenda A/B, nothing new):
1. **Engine + store:** floor-calibration engine module (B5 seams), schema per B4,
   append-only rows + head mint via `retry_on_conflict`.
2. **Portable runner, in-container (R1/R3):** fixed-N stratified probes, answered +
   hold-out legs, identity-pinned predicate/bars/dominance rule.
3. **Chokepoint wiring (A1 + B1/B2):** boot/post-sync/post-sweep/adoption
   evaluation; single-flight, coalescing, discard-requeue; `lore_index` becomes a
   pure read of engine state.
4. **Serving cutover (R6/R7 + B6-F4):** constants retire; verdict + per-hit gates
   read engine state at the serving seam; the §7 state table with its exact-set
   distinctness pin; #87 render fixes (R5).
5. **Lab validation on lore's instance (R2):** an in-container one-shot verb; the
   legacy script survives only as a dev harness (#177: the durable path no longer
   runs it at all — the script's own coordinate fix stays #177's).
6. **Retirement sweep** per repo rename law; #83/#87/#161/#179 resolution notes
   (the mechanism, never a count, is what closes each).

**B8 — Packet 11 sizing re-check: SPLIT recommended.** The earlier "~0.25 wu fits"
predates the now-explicit in-container remediation mechanics (engine-task lifecycle,
single-flight/coalescing/discard-requeue, churn counting at the shared seam,
head-mint concurrency). Honest re-estimate crosses the 0.30 line in packet 11's own
header. Recommended split at kickoff: **11-i "dark machinery"** (B7 steps 1–2 + the
R2 lab validation; serving untouched; independently landable and auditable) and
**11-ii "cutover"** (B7 steps 3–4 + 6; deploy both + smoke). *(Executed: operator
approved 2026-07-24; the lead split it as exactly this line —
`11-i-floor-calibration-dark-machinery.md` / `11-ii-floor-calibration-cutover.md`,
reviewed by this sidecar as faithful to B7.)*

---

## Addendum C (2026-07-24, third round — F3 re-disposed after two operator challenges)

**C0 — The challenges, and why both land.** Operator, verbatim: *(A)* "How can a
ruling on F3 be done if R2 lab verification is not done?" *(B)* "Me, the operator, is
not the consumer of the F3 ruling. The consumer is agents (Sonnet 5, Opus, Fable) and
each model has its own opinion on these matters… The question should be put to the
clients, which are models."
(B) has binding precedent this design already cited as prior art: the 2026-07-06
weak-match consult's own header rules wording a **client design question** — *"the
models who consume the tool decide what serves them; the operator only sequences the
build"* (method precedent: `2026-07-04-map-test-segregation.md`,
`2026-07-06-client-needs-consult.md`). The current wording is ruled law **because a
three-model consult produced it** — "ruled law" means *no unilateral change*, not
*the operator decides*. Routing F3 to the operator inverted the precedent; this
sidecar wrote that routing and owns the error (the B6 entry is preserved, marked, not
laundered). (A) is the repo's deferral law: "keep the wording iff R2 passes" was a
conditional whose condition lands in 11-i — legitimate ONLY as measure-then-tune with
a named decision point, and the *decider* named was the wrong one. Fixing the decider
(C3) dissolves (A).

**C1 — The factual half, settled at source (worktree @ `7f23223`): is the served
phrase accurate TODAY?** What actually fed 0.50649, verified in
`search_score_survey.py::main` and `choose_cosine_floor`:
- The floor was selected over a **56-sample union**: 35 eval-XML prose questions
  (human-authored) + 6 implementation-vocabulary informant probes (human-authored,
  documented provenance per entry) + **15 identifier probes synthesized from the
  corpus** (`sample_identifier_queries`: scrolled chunk identities, sorted, every
  Nth — machine-derived instances of a real query class). Candidate floors are drawn
  ONLY from that union's observed values; the nonsense set co-determines *which*
  candidate wins (admissibility + catch), never contributes a value.
- The specific value 0.50649 is one real sample's own measured cosine — the
  "transitive ripple rollup for impact depth>1" probe, i.e. a HUMAN-authored
  implementation-vocabulary query (the stamp's comment block in `search.py` records
  this, including why 5 decimal places).
- The measurement basis is **response-best cosines**: `VerdictSample.max_cosine` =
  `max_cosine_of_response` — one sample per QUERY (its best shown hit), never a
  distribution over individual hits.

Verdict, per surface:
- `_COSINE_ABSENCE_VERDICT_TEMPLATE` ("the range real answers measure on this
  corpus"): **accurate today.** The floor bounds best-answer similarities of
  answered queries on this corpus, and the aggregate verdict compares like with
  like (max-of-shown-hits against a max-of-response floor).
- `_COSINE_WEAK_MATCH_WARNING_TEMPLATE` ("below the {floor} floor **measured on
  real-query hits**"): **a compression with two live precision gaps, today, before
  any redesign:**
  1. *Basis mismatch:* the floor was measured on response-BEST cosines, but the
     per-hit flag applies it to EVERY individual hit while claiming hit-level
     measurement. Mid-list hits of a well-answered query routinely sit below the
     best-of-response distribution; the implied calibration basis was never
     performed. Not a falsehood (the best hit is a hit) — an imprecision.
     *(Ledgered as finding #180 by the lead, verified at source both ends; its
     magnitude is deliberately unclaimed — measured in 11-i per C6's rider.)*
  2. *Provenance blend:* "real-query" pools 41 human-authored with 15
     corpus-synthesized probes; the phrase does not distinguish. Defensible today.
     Under R1's self-supervised redesign the answered union becomes (near-)wholly
     corpus-derived — the unmodified phrase would then claim a provenance the
     instrument no longer has.

**So the lead's hypothesis is CONFIRMED in shape:** F3 is not "will the redesign
break this sentence" — the sentence is already imprecise on gap 1 and
blend-dependent on gap 2; the redesign makes precision mandatory rather than
optional. Gap 1 is provenance-independent and should be fixed under ANY wording
outcome.

**C2 — Corrected disposition.** F3 splits into the two questions it always was:
(1) the factual question — settled above, no consult needed; (2) the client-fit
question — *what wording best serves the model clients under self-supervised
calibration* — which goes to a **three-model client consult** per the binding
precedent. Not the operator's ruling; not this sidecar's alone.

**C3 — The consult, with its decision point fully named.**
- **Who:** Sonnet 5 + Opus informants, briefed BLIND (live probes against the 11-i
  instance encouraged — the precedent's strongest sections were probe-grounded), a
  Fable synthesis. **This sidecar is itself a consuming client: its preference (C4)
  enters as a labeled first-hand data point, never the verdict** — the precedent's
  own shape (its consultant conceded D1 to the informants; that is the protocol
  working).
- **Shown:** C1's factual finding; the R1 instrument design; **R2's lab-validation
  receipts** (both floors, the measured divergence/bias); the C4 option space; the
  standing D2 register constraint (hedged-advisory wording is ruled — hardening
  voids the adoption ruling — and survives this consult unless re-opened with the
  same three-model force).
- **When — RULED (operator, 2026-07-24):** after 11-i lands, before 11-ii's serving
  swap. The operator's own words carry the rationale, not just the verdict: *"I have
  no particular guidance on timing, other than we need to measure first."* The
  consult judges on R2's measured divergence, published per **C6** — nothing in 11-i
  needs the wording; 11-ii's entry check gates on the consult's recorded outcome.
  (The now-retired alternative — consulting immediately on C1's finding alone —
  would have judged blind on the one measurement that matters.)
- **Recorded by:** a dated consult doc in `docs/design/` (house format), cited by
  11-ii's contract; outcome noted on #83's ruling trail.

**C4 — The option space the consult judges (including the option this fork's
original framing structurally barred).**
- **W-A:** keep both phrases unchanged.
- **W-B:** static re-word to match the new instrument (e.g. "below the floor
  measured on this corpus's answered-probe survey").
- **W-C — derived provenance:** the render composes its provenance clause from
  TYPED fields of the adopted calibration row (probe basis, scope; the row is
  dated), so a mechanism change updates the served description mechanically — repo
  law applied to the one prose surface this design serves: *"prose that describes
  behaviour must be DERIVED from the behaviour, not re-stated beside it."* A
  wording change per mechanism becomes a type error at the render, not a prose bug
  nobody can see — and F3 stops recurring at every future instrument change.
- **This sidecar's data point (labeled as such):** W-C, with the consult judging
  the SHAPE (which fields, what register) while the row supplies the content; and
  gap 1 (basis mismatch) fixed regardless of which option wins.

**C5 — Downstream edits this re-disposition owes (out of this packet's writable
set — flagged for the lead, exact lines):** `11-i…dark-machinery.md` Scope OUT
("F3 is the operator's, still open at time of writing") and `11-ii…cutover.md`
Scope OUT + entry check ("F3 is the operator's fork" / "the operator approved the
conditional default") should re-point at Addendum C: the gate becomes *"F3's
client-consult outcome recorded (C3) — do not start the serving swap without it."*

**C6 — What R2 must PUBLISH (the consult's evidence package, and #180's
measurement). "We measured it" is not sufficient — the ruling makes R2's output the
input to a decision, so this section is the handoff's content spec (11-i's Exit
carries the handoff obligation; this defines its shape).**

**The divergence is NOT a single scalar.** The wording claims quantify over "the
range real answers measure" — a range comparison is a distribution-shape question,
and a small floor delta can hide shape divergence (or a large one overstate it). R2
publishes, from one dual-instrument run on one corpus snapshot:

- **(a) The two floors with their selection receipts** — F_legacy and F_portable,
  each with its `choose_cosine_floor` output (false-fire rate, catch rate, n) — plus
  the two pre-registered acceptance legs: F_portable's false-fire measured against
  the HUMAN-labeled union, and legacy-nonsense catch at F_portable. (Scalars — the
  headline, not the evidence.)
- **(b) Per-group response-best cosine DISTRIBUTIONS** — summary stats (n, mean,
  median, p5, p25, p75, p95, min, max) for each group separately: human-prose,
  human-implementation-vocabulary, synthesized-identifier, self-supervised-answered,
  hold-out-absent, legacy-nonsense — AND the per-query jsonl rows themselves (small;
  the informants can see actual values, the precedent's probe-grounded style).
- **(c) Verbatim-anchor rates per group** — the predicate is anchor-gated; any
  wording that mentions identifiers needs this visible.
- **(d) Probe texts, side by side** — ten deterministically-chosen self-supervised
  probe texts beside ten human questions. The consult is judging what "the corpus's
  own self-descriptions" concretely ARE; the referent must be visible, not
  paraphrased.
- **(e) The adopted row's typed provenance fields, with real values** — so W-C's
  derived clause can be judged as a rendered SHAPE against actual field content,
  not as an idea.
- **(f) The #180 rider — the per-hit distribution and the measured over-flag
  decomposition.** Answering the lead's question at source: **yes, cheaply — it is
  aggregation over data the instrument already captures AND persists.** Receipt
  (worktree @ `7f23223`): `HitCapture.vector_cosine` is captured for EVERY hit,
  `QueryCapture.hits` holds all k, and `_write_jsonl` persists each hit's
  `vector_cosine` — so the per-hit cosine distribution and the over-flag rate
  (fraction of SHOWN hits below the chosen floor on answered queries, decomposed
  best-hit vs mid-list, and conditional on the response itself being answered)
  are computable from the run's own jsonl with **zero extra embeds, zero extra
  searches, no distortion of R2**. Two honest bounds, stated where the number will
  sit: (i) this measures the SURVEY's query mix, not live traffic — packet 35's
  live per-hit distributions remain the confirming instrument for served reality;
  (ii) hold-out legs capture k′ > k hits — serving-relevant per-hit stats are
  computed over the SHOWN-k slice only. This turns #180's fix choice (a second
  per-hit-calibrated floor vs moving the per-hit surface onto a statistic the
  existing floor legitimately describes) into a measured decision; **the number is
  never synthesised in advance of the run** (the lead's instruction in 11-i's Exit
  is exactly right, and nothing here contradicts it).

---

## Addendum D (2026-07-24, fifth round — the cost unlock rebuilds the staleness model: measured intervals, not inherited thresholds)

**D0 — The two directives, and what dies.** Operator, 2026-07-24: *(1)* build the
mansion — self-supervision removed the human-labeling cap on N, so N is chosen by a
MEASURED noise floor, the adopted floor becomes an INTERVAL, and interval-stability
GATES the cutover; *(2)* **"what makes the floor stale has to be measured, not
inherited."** Directive 2 convicts this design's own leg 2 out of its own mouth —
§5 already conceded *"no churn threshold can bound floor error"* and inherited 10%
anyway. Churn was a proxy wrong in both directions: additive doc dumps trip it while
moving the floor ~nothing; #74's surgical edit moves the floor at ~0% churn and it
never fires. Retired by this addendum: **the churn tolerance as the DEFINITION of
stale** (and with it `_COSINE_FLOOR_DRIFT_FILE_COUNT_TOLERANCE`, into the R6
retirement sweep); the fixed-N minimums as the N rule; R8's improvised p5↔p10
separation bar (superseded in D6). Surviving unchanged: **leg 1 as a DISARM signal**
(a fingerprint/vector-identity change is KNOWN-invalid, not measured-moved — a
different signal class, per the lead's constraint, and the one leg that was always
right); the B2 run-rate machinery (single-flight, coalescing, discard-requeue);
the F6 review, narrowed to residual tuning (D5).

**D1 — The floor becomes an interval (built first; D3 stands on it).** Each
measurement bootstraps the ENTIRE selection procedure — resample the answered union
AND the absent set jointly, re-run `choose_cosine_floor` (dominance rule, anchor
carve-out and all) per resample, B≥1000 — and reports (floor_point, ci_low,
ci_high, N, B, method). **Bootstrap costs ZERO embeds**: it is arithmetic over
already-captured cosines, so interval-carrying is free at any N. The adopted row
carries the interval; serving still fires on the point (a verdict needs one bar);
whether the RENDER should say anything when a best-cosine lands inside the interval
is a wording question and is added to the F3 consult's option space, not decided
here. Today's 0.50649 — ONE probe's own cosine, an order statistic of n=41 with no
interval — is the cardboard box this replaces.

**D2 — N by measured noise, on a sampler that cannot jump.** Two parts:
- *The sampler defect this round caught (the lead's question (a), traced to its real
  mechanism):* porting `sample_identifier_queries`'s every-Nth rule to a churning
  corpus is BRITTLE — one inserted identity shifts the every-Nth phase and can swap
  out a large fraction of the probe set in one sweep, producing a floor jump that
  reflects SAMPLING discontinuity, not distribution change. Replaced by
  **hash-stable sampling keyed on the chunk's IDENTITY, not its content**: a chunk
  joins the probe pool iff its deterministic key — `records.point_id`, the EXISTING
  uuid5 over (slug, tier, file_path, chunk_type, identity, sub_ordinal,
  key_version) — falls under the inclusion threshold. Every input is in the
  scrolled payload (`SurrealStore.scroll` is `SELECT * OMIT embedding` — verified),
  so membership is computed at measurement time by calling the existing function;
  uuid5 is uniform, so sampling is unbiased. An identity key is strictly BETTER
  here than any content hash: membership is insertion-independent AND survives
  edits — an edited chunk STAYS in the pool while its probe text and embedding
  refresh (the ruler tracking its referent), so the pool churns only on chunk
  add/remove, never by phase shift and never by the re-rolled dice a content-keyed
  membership would throw on every edit. The content-keyed pieces that remain
  (the D5 cache key; D4's surviving-probe test) hash the PROBE TEXT in-hand via
  the existing `records.sha512_hex` helper.
  ⚠ *Correction, preserved rather than laundered (lead-caught, 2026-07-24):* this
  bullet first shipped keying membership on *"#170's `embedding_text_sha512`"* —
  **a store field that does not exist in the tree** (#170 is the OPEN finding that
  no such hash is persisted; its persisted form is 11b's deliverable). As written
  it would have made 11-i depend on 11b. The fix above DISSOLVES the dependency
  rather than declaring it: 11-i still depends only on "packet 10 ruled," no bytes
  need agree with 11b's future field because the membership key is not a content
  key at all, and ONE IMPLEMENTATION is honored through the existing
  `point_id`/`sha512_hex` functions instead of a phantom.
- *The N rule:* R2 embeds the full derivable-text pool once, then measures the
  **N-noise curve** — bootstrap CI width of the floor as a function of N
  (subsample at N = 50, 100, 200, 400, … up to pool size; arithmetic only, zero
  additional embeds). Adopted N is the smallest where the interval passes the
  **pre-registered stability gate: verdict decisions computed at ci_low vs ci_high
  agree on ≥98% of the union's samples** — i.e. the floor's own wobble flips ≤2% of
  known decisions. (Decision-agreement, not a width in cosine units, so the bar
  carries no arbitrary physical constant; the 98% is a pre-registration of the same
  standing as D2's 5%/60%, attackable before 11-i codes it — D8.) **Per directive
  1, this gate PASSING in 11-i is an entry condition for 11-ii's serving swap**, not
  a later review item.

**D3 — Staleness is a measurement, and the threshold dies entirely.** The adopted
model, replacing leg 2:
- **Measure at every post-sweep where at least one chunk changed since the last
  measurement; skip otherwise — and the skip is EXACT, not approximate.** Zero
  corpus change ⇒ identical probe pool ⇒ identical captures (the determinism
  control) ⇒ bit-identical floor. Skipping a no-change sweep is a correctness-
  preserving optimization, so the scheduler needs NO threshold at all: the 10%
  tolerance is not re-tuned, it is deleted.
- **Adopt iff the fresh measurement's CI and the adopted CI are DISJOINT** —
  interval-vs-interval, not point-outside-interval. This answers the lead's (b):
  the fresh measurement has its own noise, and a fresh POINT outside the adopted CI
  can be pure fresh-run noise; disjointness hedges both noises symmetrically, and
  the fresh bootstrap is free (D1). No wider hysteresis band is needed, for a
  structural reason: adoption RE-CENTERS the interval on the new measurement, so a
  borderline value that adopts is comfortably interior on the next cycle —
  sustained flapping requires the true floor to genuinely oscillate across a CI
  width, which is real movement the serving SHOULD track; and an adoption is a
  cheap store write, not a rebuild, so the cost of tracking is negligible.
  Overlapping intervals ⇒ statistically indistinguishable ⇒ keep the adopted floor:
  hysteresis falls out free, as the frontier framing predicted.
- **Leg 1 unchanged and un-folded** (the lead's constraint 1, affirmed): a
  vector-identity/fingerprint change disarms IMMEDIATELY — the old floor is
  known-invalid in the new space, and no measured-movement test is meaningful
  across spaces. Disarm on the event; re-measure queued for after the reconcile
  settles; the F4/B6 per-hit dispositions carry over unchanged.
- Stale ≡ "a fresh measurement lands disjoint from the adopted interval" ALSO
  catches the #74 class churn was blind to: a surgical edit that moves answered
  cosines moves the fresh measurement regardless of how many chunks changed.

**D4 — The ruler-and-measurand question (the lead's (a)), answered at the
mechanism.** *No feedback loop through serving exists*: the capture pipeline
consumes raw cosines and the anchor predicate — the CURRENT floor is not an input
to any capture, selection, or bootstrap step (verified against the survey's data
flow, `capture_query` → `VerdictSample` → `choose_cosine_floor`), so adopting a
floor cannot change the next measurement. The self-referential-looking part —
corpus churn moves both the answer distribution and the probe set — is the
definition TRACKING ITS REFERENT, not circularity: the floor's contract is "the
range answers measure on this corpus, now." The genuine instability mechanism was
the sampler discontinuity, fixed in D2. Residual honesty: under MASSIVE churn the
ruler and the measurand co-move and the fresh-vs-adopted comparison conflates the
two — so each run also logs a **paired decomposition** (the fresh floor recomputed
on the SURVIVING-probe subset — same `point_id` present AND unchanged probe-text
sha via `records.sha512_hex`, i.e. a fixed ruler isolating distribution movement —
beside the full-pool floor that adoption actually uses; arithmetic only). The
paired stat is the clean drift diagnostic; the full stat is the honest new truth;
divergence between them is itself a logged signal that the corpus reshaped rather
than drifted.

**D5 — Cost honesty under measure-every-sweep (the lead's constraint 2).** The B2
bounds are UNCHANGED and still hold: runs launch only at post-sweep quiescence,
single-flight with coalescing, discard-requeue on mid-run churn — so the steady-
state rate on an actively-edited tree is **exactly one run per sweep cycle**
(against the old model's one per 10%-churn; the increase is the point — staleness
is now measured). What one run costs, cold: O(N) query embeds + O(N) k′-deep
searches + arithmetic; **measured at R2 and recorded per row before 11-ii wires
the loop — measure-first applied to this design's own mechanism.** Two PRICED
CONTINGENCIES, built only if R2's measured cost demands them (YAGNI until the
number exists): (i) a probe-embedding cache keyed on (probe-text sha via the existing
`records.sha512_hex`, embedder fingerprint) — a probe whose source chunk did not
change re-uses its query embedding, collapsing steady-state embed cost to
O(changed probes) ∝ churn;
(ii) a scheduler throttle (every-Kth sweep or accumulate-M-changed-chunks) as an
F6-tunable residual — a COST knob, never a staleness definition. If measured cost
exceeds what a sweep cycle absorbs even with (i), that is reported as a limit, not
forced past.

**D6 — Composition: #180 and per-tier ride the same machinery (the lead's (c)).**
The engine's served unit generalizes to **(statistic, point, CI, scope)**: today
one row — (response-best floor, point, CI, pooled). A future per-hit floor (#180's
candidate fix (a)) is another statistic with its OWN interval and its OWN
disjointness-staleness, measured from the same captures — no new machinery, one
more row. R8's per-tier upgrade is RE-EXPRESSED in the same test and its
improvised p5↔p10 bar is superseded: **a tier gets its own served floor iff the
tier's floor CI is DISJOINT from the pooled floor's CI** (same instrument, same
adoption test, pre-registered before any stratified run exists). One test now
governs adoption, per-tier upgrade, and staleness — three rules collapsed into
one measured comparison.

**D7 — Reworked 11-i build steps (replacing the churn-threshold items) + sizing.**
B7 step 2 becomes: hash-stable pool sampling (D2) · answered + hold-out legs
(unchanged) · bootstrap interval machinery (D1) · N-noise curve + stability gate
(D2) · paired decomposition logging (D4) · per-run cost capture (D5). B7 step 3
(11-ii) becomes: exact-skip per-sweep scheduling + disjoint-CI adoption (D3)
replacing the churn trigger; leg-1 disarm wiring unchanged; contingencies (i)/(ii)
only as R2's measured cost directs. Persistence gains interval + N + bootstrap
params + paired-stat fields (B4's OVERWRITE rule covers additive fields on the new
table). **Sizing, said plainly: 11-i grows ~0.20 → ~0.25–0.30** (bootstrap +
sampler + gate analysis are arithmetic-heavy but plumbing-light; the embed cache
deferring to 11-ii keeps 11-i lean). Still inside the split's envelope and still
gated behind 11-ii; if the 11-i builder's kickoff estimate crosses 0.30, the
sub-split line is "pool+bootstrap+gate" vs "paired-decomposition+cost-capture".

**D8a — Contingency-order note (superseded-in-part by Addendum E, ruling E4):** the
D5 contingencies stand, but their ORDER is now ruled — the probe-embed cache is the
ruled response to measured cost (build it, preserve freshness); the throttle is an
ESCALATION to the operator with measured numbers, never a silently-adopted F6
tunable, because it trades served-floor freshness for compute — a rigor-vs-speed
trade on a serving surface, which the trust doctrine resolves toward rigor.

**D8 — Pre-registered vs measured, so nothing is synthesised.** MEASURED at R2,
never before: the N-noise curve; the adopted N; the CI widths; the per-run cost;
the per-hit over-flag decomposition (C6f); per-tier separations. PRE-REGISTERED
rule-shapes (same standing as the 5%/60% bars — values proposed here, attackable
by the contract-adversary BEFORE 11-i codes them): bootstrap B≥1000, central 90%
interval; the ≥98% decision-agreement stability gate; disjoint-CI as the one
adoption/upgrade/staleness test. Nothing in this addendum states a floor value, a
noise magnitude, or a run cost — those numbers do not exist yet, and the first
instrument that can produce them is the R2 run.

---

## Addendum E (2026-07-24, seventh round — RULINGS under the Trust Doctrine; delegated authority)

**E0 — Authority and instruments.** The operator elevated THE CONSUMER LAW + THE TRUST
DOCTRINE into repo CLAUDE.md (2026-07-24, "the fixed star") and delegated the ruling on
what it changes here to this sidecar; per that delegation these are RULINGS, not
recommendations — the lead executes them as given. Law read in full before ruling:
the new CLAUDE.md section (via `lore_read`, `stale:false, integrity_verified:true` —
this worktree's fork predates the change, so the indexed main tree was the sanctioned
channel); `docs/plans/v2/03b-design-rulings-r2.md` §C5 complete (same channel — the
file postdates this fork; note CLAUDE.md's shorthand "packet 03b rulings §C5" resolves
to the **-r2** file); DESIGN-LAW §1 (this tree). The measured ancestor doing the work
below is §1.3: *caveats ship WITH verdicts; under-claiming is nearly free; ONE
confident-wrong costs authority for the session (authority→witness, ~doubles calls).*

**E1 — RULED: the weak-match confidence surfaces go DARK NOW, not at 11-ii.** A new
micro-packet (proposed name `10-d-weak-match-disarm`, ~0.05 wu, DEPLOY both, owned by
the lead's packet files) ships immediately and independently of 11-i:
- `_COSINE_WEAK_MATCH_FLOOR: float | None = None` — the DESIGNED rollback lever (its
  own docstring names `None` "the disabled/rollback state"). This darkens BOTH the
  per-hit weak flag and the aggregate absence verdict on every instance. The stamp
  constant stays as a historical record with its comment block; the substrate
  (`sim 0.62`) STAYS ON — claim-free, D1-gated, honest.
- The `disabled` state's note stops being `null` (the #4 lesson — disabled-by-config
  and disarmed-pending-calibration are different conditions): the drift check's
  disabled branch serves a constant string in the shape *"weak-match confidence
  surfaces disarmed pending per-instance calibration (findings #83/#176/#179/#180;
  packets 11-i/11-ii) — per-hit similarity substrate remains served."* Failure
  admitted loudly, named next move — §C5 family (a) by construction.
- Test sweep per rename-sweep law: grep the test tree for pins certifying the old
  serving (pins that monkeypatch their own floor stay valid); add the disarm pin
  (floor `None` ⇒ no flag line, no verdict, substrate still renders, the disarm note
  serves); `smoke_p8b` is render-shape-coupled — update in step.
**Why, in trust terms:** the flag is confident-wrong three source-verified ways TODAY
(#176 cross-space comparisons on lore's own instance — the fingerprint is retired;
#179 an unmeasured constant on every foreign instance; #180 a best-of-response floor
applied per-hit). §1.3 prices one confident-wrong at session authority; the disarm
costs one beat of scrutiny on hits whose raw magnitude the substrate still shows. The
aggregate is ALREADY dark on the only instance it was ever calibrated for, so the
marginal loss is nil — and the flip also closes the edge nobody had named: a foreign
corpus within ±10% of 214 files trips NEITHER drift leg and serves lore's floor with
full confidence today. Weeks of that against a ~0.05 wu reversible disarm is not a
close call. **No wording-law issue arises: the templates go dark unchanged; the F3
consult still owns any future wording.** 11-ii then REVIVES the surfaces measured —
the cutover's framing changes from "swap constants for engine state" to "arm the
disarmed surfaces from the instance's own measurement," same work.

**E2 — RULED: the F3 consult and the §C5 battery are BOTH kept, composed — neither
replaces the other.** They answer different questions at different phases: the consult
is design-choice ELICITATION (choose among W-A/W-B/W-C — no keyed answer exists for a
preference); the battery is acceptance VERIFICATION of a built surface (keyed probes,
3-run gate). Forcing the acceptance instrument to do design elicitation would be a
different policy wearing a shared name — the routing-is-not-sharing inverse, not ONE
IMPLEMENTATION. The composition IS ruled: (a) fixtures are shared where genuinely
shared — the consult's live probes become battery fixture candidates; (b) the
consult's chosen wording is then GRADED by the E3 battery (family (c),
teaching-vs-behavior, is exactly "does the wording's claim match what the floor
measurably describes"); (c) if the battery fails the chosen wording, that is a FAILED
acceptance returned to the consult with receipts — never waived.

**E3 — RULED: 11-ii's Exit gains a §C5-keyed consumer battery over the three
calibration surfaces.** Exact text for the lead's 11-ii edit: *"Acceptance: a
§C5-keyed consumer-agent battery over the per-hit weak flag, the aggregate absence
verdict, and lore_index's calibration render — four probe families: (a)
failure/staleness admission (the disarmed / measuring / insufficient_corpus states
read as admitted conditions with a named next move); (b) count-consistency (the
render's shift-vs-tolerance and per-tier counts agree with the served rows); (c)
teaching-vs-behavior (the consult-chosen wording's claim matches what the floor
measurably describes — fixtures: one below-floor and one above-floor probe); (d) the
routing test asked LAST, keyed CALL_AGAIN, same fixtures, 3-run gate — a ROUTE_AROUND
on an honestly-rendered surface is a FAILED acceptance to fix, never waived."* C5's
cost discipline carries: the probes ride existing fixtures; if a probe is expensive to
stage, the surface lacks an honest render of the condition being probed — itself a
finding.

**E4 — RULED: the cost-contingency ORDER re-biases; the N rule does not.** (Recorded
inline at D8a.) The probe-embed cache is PROMOTED to the ruled response to measured
cost — freshness is preserved by spending build tokens, which the operator
pre-authorized. The throttle is DEMOTED to an operator escalation carrying the
measured numbers — a throttle trades served-floor freshness for compute, a
rigor-vs-speed trade on a serving surface, and the doctrine resolves those toward
rigor; it may never be adopted silently, and if ever adopted its staleness window
renders in lore_index (honest limits with exact levers, §1 idiom). **The N rule is an
authorized no-op:** the stability gate already spends until the floor's wobble stops
flipping decisions; N beyond the gate buys no trust the serving can feel — the
doctrine directs spend toward trust returns, not spend as display. The rigor dial is
the gate's pre-registered bar (≥98% decision-agreement), which stays
adversary-attackable — the doctrine biases the adversary toward TIGHTENING it, never
loosening. The exact-skip scheduler is also a no-op under the doctrine: the skip is
exact; no freshness is traded. Secondary discovery, recorded: the cache is ALSO a
determinism instrument — cached embeddings make repeat runs bit-identical for
unchanged probes by construction (load-bearing for E5).

**E5 — RULED: GO stands — with the lead's determinism condition AFFIRMED and given a
designed fallback.** The determinism control is load-bearing for D3's exact-skip and
is a must-prove pin in 11-i, as the lead conditioned. The honest risk it will meet:
TEI inference nondeterminism (GPU batch-composition floating point) can break
BIT-exactness at the embedder. Ruled in advance so a red pin is not a STOP: if
bit-exactness fails, the exact-skip rationale falls back from "bit-identical" to
"within-CI by construction" — an unchanged corpus's re-measurement differs only by
instrument noise, which the disjoint-CI adoption test absorbs (no adoption, no flap,
still no threshold) — and the E4-promoted cache RESTORES bit-exactness for unchanged
probes by construction. The 11-i builder records which leg held in the run receipts.
The doctrine's additions to the GO, in full: the E1 disarm ships first in wall-clock
(no dependency edges — 10-d and 11-i are independent; every day the disarm waits
serves confident-wrong output); the E3 battery is 11-ii acceptance; the E4 order
binds the contingencies. Everything else in R1–R8 + A–D is an authorized no-op: the
mechanisms (intervals, identity-keyed sampler, disjoint-CI, paired decomposition)
were already rigor-first — the doctrine changes SEQUENCING, ACCEPTANCE, and the
COST-TRADE ORDER, and nothing else. That "nothing else" is asserted, not assumed:
each of D1–D8 was re-read against the doctrine's four operational clauses before this
sentence was written.

**E6 — Packet-file edits the lead executes (named precisely; my writable set excludes
them):**
1. NEW `docs/plans/v2/10-d-weak-match-disarm.md` per E1 (~0.05 wu, DEPLOY both,
   independent of 11-i, ships first in wall-clock).
2. `11-ii-floor-calibration-cutover.md` Mission/Scope IN: reframe "swap the serving
   surface onto it" as "ARM the E1-disarmed surfaces from the instance's own
   measurement"; Exit: add the E3 battery text verbatim; the C5-of-Addendum-C F3-gate
   re-point stands as previously flagged.
3. `11-i-floor-calibration-dark-machinery.md`: the determinism pin gains E5's
   fallback sentence (a red pin selects the within-CI rationale + the cache; it does
   not stop the packet).
