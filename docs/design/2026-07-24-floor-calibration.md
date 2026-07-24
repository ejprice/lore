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
