# Addendum F — floor calibration: the measured-repair addendum (DRAFT, not ruled)

> ⚠ **DRAFT — NOT RULED.** Authored 2026-07-25 by `fable-design-11i-b` (design sidecar, second
> sitting) at the lead's commission on the operator's instruction. Every item is a recommendation
> with its cost; the operator rules; **this file is superseded in every particular by whatever the
> operator rules.** It amends `docs/design/2026-07-24-floor-calibration.md` (R1–R8 + Addenda A–E)
> and adjudicates the fourteen recommendations of
> `docs/plans/v2/receipts/2026-07-24-packet11i/CONTRACT-FREEZE-DECISIONS.md` §C.

**Evidence base (all committed; sha-qualified because repo-root reports archive at close-out):**
`REPORT-probe-bootstrap-11i.md` @ `803c191` ("the probe") with its instrument + raw output at
`docs/plans/v2/receipts/2026-07-24-packet11i/probe_bootstrap_degeneracy.py` / `probe-bootstrap-output.txt` ·
`REPORT-adversary-c1c14-11i.md` @ `6c18bfb` ("the adversary") ·
`docs/plans/v2/receipts/2026-07-24-packet11i/CLIENT-CONSULT-SYNTHESIS.md` @ `e9b570f` ("the consult") ·
`REPORT-design-blind-11i.md` / `REPORT-scout-11i.md` / `REPORT-fable-design-11i.md` @ `5484ae4` ·
`REPORT-fable-design-11i-b.md` @ `66066e3` (this author's Q1–Q5 + FU1).

Claim tags: **[design-cited]** (R/B/C/D/E/§ or a cited report section) · **[source-verified]** (read
in this worktree at `0ff8868`, symbol named) · **[my judgement]** (isolated deliberately). Where a
number is the probe's or the adversary's, it is cited to their section — re-read there, never
re-derived here (two populations of measurement, kept apart).

Every item carries **FILLS-A-BLANK** (the design was silent) or **AMENDS-RULED-TEXT** (the ruled
clause is named and quoted). Marking policy, stated once: anything that *adds or changes words in a
ruled sentence* is marked AMENDS even when the addition is a disambiguation the ruled words admit —
a conservative rule so no amendment can hide as a blank.

---

## F0 — TOP FLAGS: what here touches the operator's own §0 rulings, and the one provisional input

1. **F10 touches the §0 §B ruling** (the R2 vehicle). §0.2 itself assigned the #134 verification to
   the adversary pass and pre-ruled the fallback (*"the vehicle still stands; the verb must FAIL
   LOUD on absent provenance"*). The measurement is in (adversary §1): #134 **does** reach a
   baked-image run, a fourth cause exists, and **C7's receipt clause is inert in-container**. F10
   proposes additions to the §B rider set. **Riders on an operator ruling are the operator's; F10 is
   flagged here, not folded in quietly.**
2. **The §0 §A split ruling's own hold condition has RESOLVED.** §0 held the split rewrite "until S1
   lands, because a DEGENERATE verdict forks to design repair." S1 landed: **NOT DEGENERATE** (probe
   headline). The split can proceed; nothing in this addendum re-opens it. The freeze-order
   constraint from the sidecar's Q4 stands: **this addendum → 11-i-a's contract → 11-i-b's contract.**
3. **The §0 §C ruling is being executed, not amended:** the adversary attacked C1–C14 first; F8 is
   the adjudication the operator asked to rule from.
4. ⚠ **One input is PROVISIONAL:** the probe's §4b (detection power) was still filling at authoring
   time (**[source-verified]**: its §6.2 reads *"(filling from the re-run)"*, and
   `probe-bootstrap-output.txt` carries uncommitted modifications). Per the lead's instruction, the
   §6.3 flap-rate NUMBERS (0.0% → 4.5% → 7.0%) are treated as provisional here. **F2 is deliberately
   designed so it does not depend on those numbers**: it rests on the mechanism (final sections:
   interval widths shrink erratically with N while point jitter does not concentrate) and it
   *measures* the null rate per run rather than assuming any value from §6.3. If §4b revises the
   numbers, F2 self-corrects; if §4b shows the mechanism cannot detect real shifts, that is a NEW
   design fork and F2 says so below.

---

## F1 — The D2 adopted-N rule · **AMENDS-RULED-TEXT**

**Ruled text amended** [design-cited D2]: *"Adopted N is the smallest where the interval passes the
pre-registered stability gate."*

**Why it cannot stand:** measured twice, blind, in two instruments. The probe's leg B:
FAIL·FAIL·FAIL·**PASS(448)**·FAIL·FAIL·PASS (probe §5.2/§5.3); the adversary, independently:
"smallest passing rung" adopts N=100 where N=200 fails, and nesting does not repair it (adversary
§2.4). On the real-regime leg A the literal rule adopts N=112, whose interval is **8× wider** than a
rung that also passes (adversary §9.2, reading the probe's committed output). A smallest-N rule over
a non-monotone curve adopts a rung that passed by luck **[design-cited probe §5.3]**.

**Replacement rule (recommendation):**

> Adopted N is the **smallest ladder rung R such that R and every larger evaluated rung passes the
> gate**. N counts **PROBES, not samples** — each rung's subsample is the first N probes in
> point_id-key order, and that rung's answered, absent and identifier legs are exactly the legs
> derived from those N probes (the pairing is nested with them). The full ladder's
> `(N, ci_width, agreement)` triples are **persisted in the row**, so the choice is auditable. If no
> qualifying rung exists at any N up to the ladder's top, the run records
> `measured_not_adopted · cause = stability_gate_unmet` — an honest standing condition, ruled in
> advance so nobody improvises (E5-parity: the same move E5 made for the determinism pin's RED case).

**What I deliberately did NOT adopt, and why [my judgement]:** the adversary's §9.2 tiebreak
("among qualifying rungs adopt the NARROWEST interval") is necessary **only in the absence of F2's
calibrated adoption bound**. Under F2, interval width no longer silently sets the false-adoption
rate, so the tiebreak's motivation dissolves — and the narrowest-interval rule would actively
maximise adoption-test sensitivity, which is F2's measured hazard. With F2 in place, smallest
qualifying N is also the cheapest steady state (O(adopted-N) embeds, D5) and is retained.
Divergence from the adversary's C4 missing-words on the no-qualifying-rung outcome
(`measurement_failed` there, `measured_not_adopted` here) is argued in F5.

---

## F2 — The D2/D3 tension: named, and resolved by measuring the noise it rides on · **AMENDS-RULED-TEXT**

**Ruled text amended** [design-cited D3]: *"Adopt iff the fresh measurement's CI and the adopted CI
are DISJOINT — interval-vs-interval, not point-outside-interval … hysteresis falls out free."*

**The tension, named (it is currently invisible in ruled text):** D2 pushes N **up** to pass the
stability gate; D3's false-adoption rate under the null **rises** as N grows. Mechanism, from final
probe sections **[design-cited probe §5.1 width column, §6.3 mechanism]**: the bootstrap CI is a
*within-capture resampling* object and narrows (erratically) with N, while the *between-run* point
jitter does not concentrate (mean |Δfloor| ≈ 0.014–0.015 at every rung measured). A narrowing
interval around an equally-jittery point eventually stops overlapping its successor — so at exactly
the N that D2 demands, D3 adopts on noise. The specific rates (0.0/4.5/7.0% at 56/224/896) are
provisional pending §4b (F0.4); **the direction is mechanical and does not depend on them.**

**Resolution (recommendation) — O1, the calibrated adoption bound:**

> Disjointness remains the adoption test's SHAPE. Each run additionally **measures its own null
> disjointness rate at the adopted N**: draw paired pseudo-measurements by bootstrap (two
> independent resamples of the same captures, each through the full selection procedure), and record
> the fraction of pairs whose intervals are disjoint — arithmetic only, zero embeds, the same
> economics as D1. **Pre-registered bound: the null false-adoption rate must be ≤ 2%** (the same
> standing and the same value-class as the gate's 2% — one wobble budget, not a new constant). If
> raw disjointness exceeds the bound at the adopted N, adoption additionally requires the two
> intervals to be separated by at least the measured null-gap 98th percentile — an **inflation
> measured from the run's own captures, never an invented constant**. Both the null rate and the
> applied gap threshold are persisted in the row.

**Why this shape [my judgement]:** it hedges *both* noises (D3's stated rationale for
interval-vs-interval) with measured quantities; it is robust to §4b's pending revision because it
measures rather than assumes; it preserves D3's soul (staleness is a measurement) and D6's one-test
unification (the same calibrated test governs adoption, per-tier, and — if it ever separates —
per-shape); and it dissolves F1's tiebreak dilemma. Alternatives considered: **O2** (adopt only on
two consecutive disjoint measurements — a clock-free debounce in run units; rejected: under
measure-every-changed-sweep, consecutive runs see different corpora, so "confirmation" conflates
noise with real drift, and it halves responsiveness for free); **O3** (keep D2's smallest-N and
accept wide intervals; rejected: the adversary's §9.2 shows the wide-interval rung *never adopts
again* — a deaf staleness detector, which defeats the design's purpose). **Named re-open trigger:**
if §4b lands showing detection power against real shifts is poor at the N the gate selects even
under O1, the interval mechanism has failed in the OTHER direction and the K1 decision-distance
frame (this author's Q1.2, `REPORT-fable-design-11i-b.md` @ `66066e3`) is the prepared fallback.

---

## F3 — The ≥98% gate's denominator: one reading, and the fork the operator must close · **AMENDS-RULED-TEXT**

**Ruled text amended** [design-cited D2]: *"verdict decisions computed at ci_low vs ci_high agree on
≥98% of the union's samples."*

**Why this is a STOP, not a preference** [design-cited adversary §2.2(b), §6.8]: the *which-pool*
axis alone moves the measured quantity by **4.1 points at N=100 — more than the entire 2% budget the
bar enforces** — and the probe had to choose a *which-samples* reading just to proceed (probe §7.1).
Repo law makes an ambiguity larger than the quantity it feeds an escalation. Both axes are fixed
below; one fork inside the first axis is genuinely the operator's.

**The two axes, fixed:**

1. **Which POOL (settled — accept the adversary):** agreement is evaluated **at each ladder rung
   over that rung's own subsample** — the same probes the rung's interval was computed from, an
   in-sample agreement *stated as such* — and the row records the full-pool agreement beside it as a
   diagnostic **[design-cited adversary §2.2 missing-words]**.
2. **Which SAMPLES (the operator's fork — three readings exist in the record):**
   - **R-literal** — the answered union only, anchored included: what D2's words say ("the union" is
     §1.5's 56-sample union) and what the probe implemented (probe §7.1).
   - **R-package** — answered + identifier + hold-out-absent, anchored excluded: what §C's C2
     recommends.
   - **Recommended: R-package, with its receipts** [my judgement, argued]: (a) anchored samples
     cannot flip at ANY floor (**[source-verified]**: `_cosine_absence_predicate` returns False on
     any anchored sample regardless of floor), so including them is pure denominator inflation — the
     fixture-composition defect class as a gate; (b) the hold-out-absent leg guards the CATCH bar's
     stability — the verdict exists to fire on absent queries, and a gate blind to absent-side flips
     certifies stability of only half the served contract. Cost of R-package honestly stated:
     absent-leg maxima cluster near the floor by construction, so the gate is harder and adopted N
     (and steady-state cost) rises. Cost of R-literal: catch can wobble across the CI under a
     "stable" gate, silently.
3. **Refusals, either way** [design-cited adversary §2.2(a) missing-words]: the gate **REFUSES to
   pass on a degenerate interval** (`ci_high == ci_low` — a `measured_not_adopted ·
   interval_degenerate`, never a 100%-agreement pass) **and on a denominator below the F4 validity
   minimums**. The row records the anchored-excluded count. The addendum also states, so the first
   auditor does not read it as a bug: **this denominator excludes anchored samples while
   `choose_cosine_floor`'s false-fire denominator includes them** (**[source-verified]**:
   `n_union = len(real_query_samples)`) — two denominators, two purposes: the selection bar prices
   the served population as it arrives; the stability gate measures wobble only where wobble is
   possible.

---

## F4 — The two damaged states, re-predicated · **AMENDS-RULED-TEXT**

**Ruled text amended** [design-cited] — this section RETIRES `stale_remeasuring` and replaces it
with `invalidated_remeasuring`: §7's state rows for `stale_remeasuring` (*"leg fired; run
queued/in flight"*) and `insufficient_corpus` (*"min samples unreachable"*); B6-F4's *"LIVE-on-the-
old-floor under churn staleness"* disposition; read with D0's retirement sentence (*"the fixed-N
minimums as the N rule"*) and blind review C3/C4, which identified both damages.

1. **`stale_remeasuring` → renamed `invalidated_remeasuring`, predicate = leg 1 ONLY:**
   *vector-identity/embedding-fingerprint invalidation; the adopted floor is known-invalid in the new
   space; re-measure queued/awaiting reconcile settle.* Under D3 this is the only surviving
   waiting-stale condition — churn staleness is deleted, and a disjoint fresh measurement causes
   immediate adoption, not a stale interlude [design-cited D3]. The old name asserts *aging*; the
   surviving predicate is *known-invalid* — prose-derives-from-behaviour law applied to a state name,
   at the one moment renaming is free [my judgement]. B6-F4's churn-leg clause is recorded as
   superseded (E1 darkened the per-hit flag independently; the aggregate disposition — disarmed
   whenever state ≠ `measured` — carries over unchanged).
2. **`insufficient_corpus` → predicate RESTORED: the 30/15/30 validity floors** (≥30 derivable
   answered probes, ≥15 identifier probes, ≥30 absent-leg samples *after* C9-rule drops), gating
   VALIDITY only — adopted N is chosen solely by F1. Recorded explicitly as **restoring a predicate
   D0's retirement sentence removed** (the §C-ter composition of ESC-9 + blind C4, both satisfied);
   the values stay adversary-attackable pre-registration.
3. **The C3↔C4 join, ruled rather than left to a builder** [design-cited adversary §2.3]: the ladder
   is `[50, 100, 200, 400, …]` **truncated at pool size, with a final rung equal to pool size
   whenever pool size is not already a rung**; a pool of 30–49 valid probes is evaluated at pool
   size as a single-rung ladder; below the minimums ⇒ `insufficient_corpus`. The row records the
   adopted subsample's ACTUAL size, never a nominal rung.
4. The full 8-string closed set (with the rename) ships with the exact-set distinctness pin and the
   typed-cause-fields pin (`REPORT-fable-design-11i-b.md` Q5 @ `66066e3`), discharging the
   adversary's §4.5 (the set itself was covered by none of the fourteen).

---

## F5 — The typed non-adoption cause enum · **FILLS-A-BLANK**

The design has no cause field anywhere in R1–R8/A–E; the requirement is client-sourced: two blind
informants independently carved out degeneracy as the ONE non-adoption reason worth serving, *as a
corpus property* [design-cited consult §2.1], and the lead's synthesis §4.3 reads it as a schema
requirement — a reading this author confirmed in FU1 (the render cannot serve a distinction the row
never recorded).

**The enum (per-row `non_adoption_cause`, closed, exact-set-pinned):**

> `head_retained_overlap` (routine: fresh measurement not distinguishable from the adopted head —
> the steady-state normal) · `catch_bar_unmet` (the D2 license failed) · `substrate_indiscriminate`
> (the corpus property: `substrate_gate_passes` failed — median within-query spread below
> `D1_MIN_MEDIAN_SPREAD` **[source-verified]**) · `interval_degenerate` (the instrument property:
> the interval collapsed, predicate below) · `stability_gate_unmet` (F1: no qualifying rung).

**The two degeneracies must never share a value** [my judgement, grounded in ruled law]: the
consult's carve-out earns the corpus-property sentence ("semantic search discriminates poorly here —
downgrade the positives too") **only** for `substrate_indiscriminate`. `interval_degenerate` can
occur on a perfectly discriminating corpus; projecting it into the corpus sentence would serve a
confident corpus claim licensed by an instrument artifact — the confident-wrong class §1.3 prices at
session authority. The projection function (11-ii, ONE pinned function per the synthesis §4.2) maps
`substrate_indiscriminate` to the ruled corpus-property render and `interval_degenerate` to the
uncalibrated collapse unless `substrate_indiscriminate` co-fires.

**`interval_degenerate`'s precise predicate — the lead's dead-code challenge, answered:** *fires iff
the bootstrap interval at the evaluated rung is a point (`ci_high == ci_low`) or spans fewer than 3
distinct resampled candidate values.* On THIS corpus's regime it will not fire — measured: modal
mass 25.8–64.8% across 31 runs, never within 25 points of the ≥90% collapse requires, with the
mechanism (a resample omits any given sample with probability → 1/e, capping modal mass ≈63.5%)
[design-cited probe headline]. It is **not dead code but a guarded branch**, because the collapse
IS reachable where the union has few DISTINCT cosine values — a tiny or duplicate-heavy foreign
corpus — which is measured, not conjectured: the probe's differently-broken control (a constant
union → `distinct resampled values = 1`, modal 100%) is exactly this branch firing [design-cited
probe §3]. **The contract pins the branch with that control as its fixture** — a
few-distinct-values corpus MUST produce `interval_degenerate`, the recorded regime MUST NOT.

---

## F6 — `head_identity(axes)` and the reserved `query_shape` axis · **AMENDS-RULED-TEXT** (B4's head key)

**Ruled text amended** [design-cited B4]: *"plus one minted head pointer per scope."* This chooses
D6's reading — the served unit is *(statistic, point, CI, scope)* — over B4's sentence, written one
addendum earlier (blind C2 named the collision; deciding after the table ships is a record-identity
migration, the one non-OVERWRITE-able freeze in 11-i-a).

> **The head is keyed on its axis mapping — today (`statistic`, `scope`).** Identity is computed by
> ONE function, `head_identity(axes) -> str` = `records.sha512_hex` over the sorted
> `(axis_name, value)` pairs joined by `\x00`, where `statistic` and `scope` always serialize and
> any FUTURE axis serializes **only when its value differs from its registered default**.
> Consequence, pinned by a mutation fixture: registering a new axis at its default changes **no
> existing head id** (byte-identical); a non-default value mints a new head. The axis-name registry
> is a closed set under the same exact-set pin discipline as the states; **`query_shape` is
> registered now at default `"any"`** (Sonnet's consult finding; the in-tree evidence that the axis
> is real — #74 as a shape-miscalibration incident, the anchor carve-out as an existing
> shape-conditional mechanism — is in `REPORT-fable-design-11i-b.md` FU1.3). `statistic` and `scope`
> also travel as queryable FIELDS on rows and heads (a RecordID's string component cannot be
> indexed — [design-cited capabilities §2]); the record id is only the uniqueness/CAS anchor. The
> hash id sidesteps both the `:`-in-scope parse ambiguity and the `str(RecordID)` angle-bracket
> landmine. `read_adopted_head` takes an **axes mapping**, not positional arguments. **The
> single-flight lease stays instance-global** — one run measures every statistic/scope/shape from
> one capture set [design-cited B2/§5]; one sentence in 11-i-a's contract prevents a builder
> scoping the lease per head.

Serving per-shape, if the D6 test ever demands it, needs a serve-time shape classifier with its own
honesty story — the anchor detector is the in-repo precedent that this is buildable; nothing here
builds it, and nothing here forecloses it.

---

## F7 — The no-regret pins, re-evaluated post-S1 (one KEPT-strengthened, one KEPT-reframed, one DROPPED) · **FILLS-A-BLANK**

Per the commission: not carried on inertia.

1. **The gate's degeneracy refusal — KEEP, grounds STRENGTHENED.** The hazard did not materialise on
   this corpus (probe headline), but: (a) the adversary demonstrated the trivial-pass door with
   running code — a collapsed interval passes at the smallest rung unconditionally, and the sentence
   must not depend on S1's corpus-specific answer [design-cited adversary §2.2(a), §9.1: LATENT,
   not live — and latent doors close cheaply]; (b) the live regime for the hazard is few-distinct-
   value corpora — tiny/foreign deployments, exactly where #179-class damage happens unwatched, and
   exactly the branch the probe's own control shows is reachable [design-cited probe §3]; (c) the
   consult now requires degeneracy to be a served, typed condition (§2.1) — the refusal is what
   routes a collapse into F5's cause enum instead of a silent 100%-agreement pass. Cost: two lines
   plus a fixture the probe already wrote.
2. **The row's degeneracy telemetry — KEEP, REFRAMED as the probe's own method made durable:**
   persist `ci_distinct_candidate_values`, `ci_modal_mass`, `floor_rank`, and `floor_tail_depth`
   (count of non-anchored union samples strictly below the floor). These are the exact columns by
   which the probe distinguished "erratic" from "frozen" and its differently-broken control from its
   headline [design-cited probe §3: "separable by a reported column"] — free at measurement time,
   and they make any future degeneracy **visible rather than inferred**. (The consult bars them from
   the SERVED surface — CI/sample-count refusal, §1.3 — these are row fields for engineers and the
   F5 predicate, not render content.)
3. **The "≥K samples strictly below the floor" adoption gate — DROPPED, explicitly.** My Q1.1
   proposed it; the measurement refuted its premise: the recorded regime sits at depth ≈2 and is
   healthy (un-freezable by mechanism), so a K-depth gate would have wrongly blocked the very
   adoption that produced 0.50649. Depth is now telemetry (item 2), not a gate. [my judgement,
   revised by probe evidence — recorded so the drop is deliberate, not silent.]

---

## F8 — The fourteen adversary recommendations, adjudicated

Verdict key: **ACCEPT** (the adversary's missing words, cited to its section — not re-transcribed) ·
**ACCEPT-MODIFIED** (change named, reason given) · none REJECTED — the adversary's demonstrated
wrong builds survived my attempts to dismiss them, and five carry running-code receipts.

| item | verdict | disposition (missing words per adversary §2.x unless noted) | mark |
|---|---|---|---|
| **C1** seed/replay | **ACCEPT** | per-(scope,leg,N)-derived seed; generator passed explicitly; no-module-level-`random` pin (monkeypatch-raise); **fixture N ≥ 200** (the small-N blindness is measured — 20/20 identical unseeded at N=50); control mutation-proven; replay mismatch ⇒ `measurement_failed` + finding, never the TEI leg, never nothing (§2.1) | blank |
| **C2** gate denominator | **ACCEPT-MODIFIED** | folded into **F3**; which-pool per adversary; which-samples is an operator fork F3 surfaces (the package's reading and the ruled words diverge — a STOP per §6.8); refusals + two-denominator documentation accepted (§2.2) | AMENDS (F3) |
| **C3** 30/15/30 | **ACCEPT** | validity floors restored per **F4.2**; the 30–49 no-rung boundary ruled per **F4.3** (§2.3) | AMENDS (F4) |
| **C4** adopted-N | **ACCEPT-MODIFIED** | "R and every larger evaluated rung passes" + probes-not-samples + persisted triples accepted; §9.2's narrowest-interval tiebreak **replaced by F2's calibrated bound** (reason in F1); no-qualifying-rung ⇒ `measured_not_adopted · stability_gate_unmet`, not `measurement_failed` (reason in F5/F8-note) (§2.4, §9.2) | AMENDS (F1) |
| **C5** evidence address | **ACCEPT** | six named artefacts, each a file, regenerating script for (b)/(f), run's own UTC date (§2.5); plus §6.7(b): R2's receipts dir named **`<run-date>-11i-r2`** to avoid colliding with `2026-07-24-packet11i` | blank |
| **C6** R2 adopts | **ACCEPT** | classification via `_txn.is_retryable_conflict_error` — no message match anywhere in the calibration module; mutation-proven via the existing `_MUTATED_CONFLICT_TEXT` discipline; new entry points added to the observed-coverage driver set in the same change (§2.6) | blank |
| **C7** verb + receipt | **ACCEPT-MODIFIED** | `LORE_VERSION` + image digest as the identity fields, refuse on `unknown`; `loremaster.__file__` demoted to a namespace check (it is build-invariant — measured across four topologies); **all three** of url/namespace/database explicit, no defaults (A2); git-provenance handling per **F10**, which is the operator's (§1.4, §2.7) | AMENDS §B riders (F10) |
| **C8** exhaustive scroll | **ACCEPT-MODIFIED** | count-vs-returned mismatch ⇒ **discard-requeue through the settled-index gate** (the design's own mechanism), reserving `measurement_failed` for `returned == limit`; narrowed projection accepted as a NEED — but it is a store-surface addition inside a `DEPLOY: no` packet ⇒ **decision-needed**: recommend authorizing it as an 11-i-a store-half addition (a new unserved read alters no served byte; the adversary's ⚠ says rule it, and I concur) (§2.8) | blank + 1 decision |
| **C9** k′/short leg | **ACCEPT** | exactly-k non-source hits or NO absent sample; `has_verbatim_anchor` **recomputed over the non-source hits**, never inherited; drops counted split by cause; ≥30 evaluated after drops; the source-concentrated fixture demanded (the measured False→True adoption flip is the page's strongest receipt) (§2.9) | blank |
| **C10** skip datum | **ACCEPT** | skip predicate = digest **AND** embedding fingerprint AND bars tuple AND instrument version AND k′; all persisted so the comparison is a row read (§2.10) | blank |
| **C11** probe manifest | **ACCEPT-MODIFIED** | full-derivable-pool manifest + `len` recorded; BOTH fixtures (determinism re-run **and** the changed-corpus mutation fixture); size measured at R2 — **proposed bound supplied** (decision-needed): in-row up to a measured 1 MB/row; above it, the manifest moves to a side table, decided at R2 review, not after 11-ii ships (§2.11). Note steady-state rows carry adopted-N manifests (hundreds); only R2's full-pool row is large | blank + 1 decision |
| **C12** identifier sampling | **ACCEPT** | DISTINCT-dedup second fixture (many-chunks-one-identity); row records distinct-identity count + anchored split; the adversary's own negative measurement (composition is second-order) recorded so nobody re-derives it (§2.12) | blank |
| **C13** self-retrieval key | **ACCEPT-MODIFIED** | matched on `Candidate.key` (verified: it IS the bare point_id — the escalation branch is dead and is deleted); both-keys drop rates reported, R2 publishes the delta; missing point_id ⇒ `measurement_failed`, never a non-match; **modification: the ≤20% bar's re-registration is a NAMED decision point** — at R2 review, the operator re-registers the bar against the chunk-scoped key using the published delta (measure-then-tune, named data/decider/date) (§2.13) | blank + 1 decision |
| **C14** affordability | **ACCEPT-MODIFIED → escalated as F9** | the reconciling sentence stands; the ladder mandate is re-grounded per **F9** (design fork, operator's) (§2.14, §6.1) | AMENDS (F9) |

**Note on the C4/F5 divergence (the one place I override the adversary's words):** filing a finding
for a corpus that never stabilizes treats a standing corpus-shaped limitation as an incident — §4.5's
own asymmetry (failures escalate; routine conditions log and render). `measurement_failed` + a
deduped finding stays reserved for instrument-convicting outcomes (replay mismatch, missing
point_id, real truncation); `measured_not_adopted` + typed cause is the honest standing state for
corpus-shaped ones. The distinction is exactly F5's enum doing its job.

**The adversary's §4 uncovered-items, dispositioned:** §4.1 lease → the sidecar's Q2 fencing design
(`REPORT-fable-design-11i-b.md` Q2 @ `66066e3`) is the fifteenth recommendation, before the operator
with two options; §4.2 embed cost → F9; §4.3 bars' meaning under paired legs → R2's acceptance is
judged against the LEGACY labeled sets (the anchor that keeps 5%/60% meaning fixed), and C6(b) now
publishes the S3 dominance fact + C9/C13 drop diagnostics so the F3-consult sees them; §4.4 gate
never passes → F1's pre-ruled outcome; §4.5 state set → F4.

---

## F9 — C14's affordability: the bootstrap's implementation is a design decision, resolved here for ruling · **AMENDS-RULED-TEXT**

**Ruled text amended** [design-cited]: D1's *"interval-carrying is free at any N"* — **measured
FALSE** (probe §8: growth exponent ≈1.92; 8–9 min single-threaded at N=3584; adversary §2.14:
**5.7 h for ONE rung at pool 20k**, 32.9 h at 50k; ladder ≈1.35× its top rung). D2's ladder *"up to
pool size"* is unaffordable over the current `choose_cosine_floor`. B2's constant-cost claim was
already superseded (blind FA4); this addendum ledgers all three (F11).

**Resolution (recommendation), in order:**

1. **E2 — the sort-based one-pass sweep, proven equal (primary).** Replace the per-candidate
   rescan inside the bootstrap with a single sorted sweep computing every candidate floor's
   false-fire/catch in O((U+A)·log(U+A)) per replicate, shipped with a **property pin asserting
   byte-equality with `choose_cosine_floor` over randomised inputs** — the identity-pin discipline
   one level up [design-cited blind §7.13(b); adversary §2.14 missing-words]. `choose_cosine_floor`
   remains the single definition of the SELECTION RULE; the sweep is an equivalent evaluator, and
   the equality pin is what stops it becoming copy #2. Projected effect: per-replicate cost falls
   from O(N²) to O(N log N) — minutes, not hours, at pool scale; the ladder to pool size survives
   as ruled. **A numpy/scipy install (E1) is NOT the exit it looks like** [my judgement]: the cost
   lives in the pure-Python double loop, so vectorising means rewriting the selection rule — the
   same twin hazard as E2 with a dependency added; E1 is deferred unless E2's equality proof fails.
2. **E3 — the affordability receipt (belt-and-braces, regardless).** Before any ladder runs, the
   runner times one `choose_cosine_floor`-equivalent call at pool size and records the projected
   ladder total; the ladder extends to pool size **or to the largest rung the projection allows,
   whichever is smaller, recording BOTH** so a truncated curve is visible in the receipt, never
   inferred [design-cited adversary §2.14 missing-words].
3. **The embed pass gets the same honesty** [design-cited adversary §4.2]: R2's full-pool embed is
   O(pool) calls against the production TEI. The verb **requires an explicit `--max-embeds`
   argument — no default** (the same refusal shape as the coordinate rule), prints the derivable-
   pool count and projected embed total before embedding, and aborts loudly if the count exceeds
   the given bound. The operator sets the number per run; the verb never invents one.

**Scope-law flag riding this item:** B1 homes the steady-state engine in the server's asyncio loop;
minutes of CPU-bound arithmetic in-process starves the MCP serving path. In 11-i the only driver is
the one-shot verb (own process — no issue); **11-ii's chokepoint wiring must move the arithmetic off
the event loop** (worker process or equivalent). Not 11-i's work; raised so 11-ii's packet carries
it deliberately (F12.4).

---

## F10 — The §B vehicle's provenance · **AMENDS the §0 §B rider set — OPERATOR'S ITEM, flagged at F0.1**

**What is now measured** [design-cited adversary §1]: (a) #134 reaches a baked-image run — the
failure belongs to the MOUNTED TREE (`git -C /workspace rev-parse HEAD` → `fatal: not a git
repository: …/worktrees/lore-pkt11i` → `capture_git_identity` → silent `(None, None)`); (b) FOUR
distinct causes collapse to that one sentinel, one (`dubious ownership`) named by neither #134 nor
#131; (c) **C7's receipt field is inert in the authorized vehicle** — `loremaster.__file__` is
`/app/loremaster/loremaster/__init__.py` for every image ever built; (d) the discriminating baked
field exists: `LORE_VERSION` (host `git describe` at build time; defaults `unknown` when the
build-arg is omitted); (e) the runtime fix works: bind-mount the parent `.git` at its host-absolute
path `:ro` (case D, measured returning the worktree's real sha/branch).

**Recommended rider additions (the operator rules; §0.2 pre-ruled the fail-loud half):**

1. **Build-time provenance is primary.** The §B image build MUST pass the worktree's
   `git describe --tags --always --dirty` as the `LORE_VERSION` build-arg, and the verb **REFUSES
   to run when `LORE_VERSION` is unset or `unknown`**; the run receipt records `LORE_VERSION` + the
   image digest + the store coordinate + the run's own corpus fingerprint + UTC date.
   `loremaster.__file__` is recorded as a namespace check only. **Verification item for the §B
   audit** (I cannot verify the build path from this seat): confirm the build script actually
   passes the build-arg from the WORKTREE's git state — a build that inherits a stale or main-tree
   describe string is the same defect wearing a receipt.
2. **Runtime git identity becomes OPTIONAL under (1)** [my judgement]: build-time capture identifies
   the tree without exposing `.git` to the container. If the operator wants runtime-verified git
   identity anyway, case D's `:ro` gitdir mount is the measured mechanism. **Either way, per §0.2's
   own pre-ruling: if the row carries git fields and `capture_git_identity` returns `(None, None)`,
   the verb FAILS LOUD — it never writes a row with silently-empty provenance.**
3. **Raised, not folded** (adversary §6.5, seconded): `capture_git_identity`'s four-causes-one-
   sentinel shape is a live production defect (#131 one level up), invisible because nothing renders
   the field. Not 11-i's; it needs an owner and a finding.

---

## F11 — Amendment ledger carried by this addendum

Sentences in the ruled design this addendum amends or corrects (per the blind review's §7.25
discipline; the design doc itself is outside this author's writable set — the lead applies markers):

| ruled clause | disposition here |
|---|---|
| D2 *"Adopted N is the smallest where the interval passes"* | replaced by F1 |
| D2 gate sentence (denominator) | completed by F3 (one fork to the operator) |
| D3 *"Adopt iff … DISJOINT"* + *"hysteresis falls out free"* | calibrated by F2 (the free-hysteresis claim does not survive the measured mechanism at large N) |
| D1 *"interval-carrying is free at any N"* | FALSE, measured — corrected by F9 (zero-embeds half stands) |
| D2 ladder *"up to pool size"* | conditional per F9.2 |
| B2 constant-cost claim | superseded (blind FA4); ledgered |
| §7 `stale_remeasuring` row + B6-F4 churn clause | re-predicated and RETIRED/renamed by F4 to `invalidated_remeasuring` |
| §7 `insufficient_corpus` row ↔ D0 retirement | predicate restored by F4 |
| B4 *"one minted head pointer per scope"* | re-keyed by F6 |
| §0 §B riders | additions proposed by F10 (operator's) |

Blind §7.25's six previously-identified superseded statements remain the lead's design-doc edit;
this table adds this addendum's own, so the ledger stays one list.

---

## F12 — Raised under scope law (found while drafting; not this addendum's to fold in)

1. **`weighted_percentile` exists twice, hand-rolled both times** (probe §9.1) — and 11-i adds a
   third percentile consumer. Promote one to a shared home before the third arrives (ONE
   IMPLEMENTATION). Owner needed.
2. **`scripts/` has no `testpaths` entry** — the identity pins and the dominance suite that produced
   0.50649 have never run in any gate (probe §9.2, adversary §6.6, scout RAISED-4 — three
   independent reports now). Operator's call, third time of asking.
3. **`capture_git_identity`'s silent `(None, None)`** — live production defect, four
   indistinguishable causes (F10.3; adversary §6.5). Needs an owner and a finding.
4. **11-ii must move the engine's CPU-bound arithmetic off the server's event loop** (F9's flag) —
   a B1-consequence no packet currently carries.
5. **The probe's §4b re-run is actively writing `probe-bootstrap-output.txt` in this worktree**
   (uncommitted modifications observed at authoring time) — the lead should not archive or commit
   over it until the probe agent lands §4b and lifts its DRAFT banner.

---

## Decisions-needed for the operator, consolidated

| # | decision | recommendation | where |
|---|---|---|---|
| 1 | F1+F2: replace D2's adopted-N rule; adopt the calibrated adoption bound | as drafted (O1); K1 held as the named fallback if §4b shows poor detection power | F1, F2 |
| 2 | F3: the gate's sample population — R-literal vs R-package | R-package (answered + identifier + absent, anchored excluded), costs stated both ways | F3 |
| 3 | F4: state rename + restored minimums + the 30–49 join | as drafted | F4 |
| 4 | F5: the cause enum + the two-degeneracy split + projection constraint | as drafted | F5 |
| 5 | F6: head key = axis mapping via `head_identity`; `query_shape` reserved at `"any"` | as drafted | F6 |
| 6 | F7: keep pins 1–2, drop the K-depth gate | as drafted | F7 |
| 7 | F8: the fourteen adjudications (11 ACCEPT / 3 ACCEPT-MODIFIED beyond wording) | rule per table; the C4-outcome divergence is argued in F5/F8-note | F8 |
| 8 | C8's narrowed-projection store read inside `DEPLOY: no` | authorize as an 11-i-a store-half addition (new unserved read) | F8/C8 |
| 9 | C11's manifest size bound | in-row to a measured 1 MB/row; side-table decision at R2 review | F8/C11 |
| 10 | C13's ≤20% bar re-registration | named decision point at R2 review, on the published both-keys delta | F8/C13 |
| 11 | F9: the bootstrap's implementation (E2 sweep + equality pin; E3 receipt; `--max-embeds`) | as drafted; E1 (numpy) only if E2's proof fails | F9 |
| 12 | F10: the §B rider additions (LORE_VERSION primary; optional gitdir mount; fail-loud) | as drafted — **touches the operator's own §B ruling** | F10 |
| 13 | The lease (the missing fifteenth item) | Q2's Option A (epoch-fenced, clock-free reclamation) at `REPORT-fable-design-11i-b.md` @ `66066e3` | — |

*— end of draft. The operator rules; nothing above is settled until then.*
