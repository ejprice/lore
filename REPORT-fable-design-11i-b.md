brief-base v6 read

# REPORT-fable-design-11i-b — design-sidecar standing answer log (packet 11-i, second sitting)

## SUMMARY BLOCK
- `brief-base v6 read` · agent `fable-design-11i-b` · worktree `/home/ejprice/PycharmProjects/lore-pkt11i`, branch `pkt11i-floor-calibration-dark`, HEAD `0ff8868` · written 2026-07-25
- state: done (first deliverable, Q1–Q5) — STANDING BY for follow-ups via SendMessage
- deviations: none. Read-only apart from this file; no git mutation; no store/embed/network access.
- decisions-needed (operator; each expanded in its Q-section):
  1. **Q2** — lease discipline: **Option A** (epoch-fenced lease + clock-free reclamation; fully inside ruled text — *recommended*) vs Option B (in-process single-flight + advisory row; simpler, but amends §5/B4's "coordinated through the store").
  2. **Q3** — head key = **(statistic, scope)**, choosing D6's reading over B4's per-scope sentence (an amendment-ledger entry for B4, not a re-open); record-id encoding default = `sha512_hex(statistic‖scope)` with both carried as queryable fields.
  3. **Q1** — pre-authorize two **no-regret pins** now, regardless of the probe's verdict: (i) the ≥98% gate gains a degeneracy guard (`ci_low == ci_high` can never pass it), (ii) the row records CI candidate-count and floor tail-depth. If DEGENERATE-at-all-N: recommended repair frame is **K1 (decision-distance)** — ranked option space in Q1.
  4. **Q5** — re-predicate the two damaged states (C3/C4) in the short design addendum BEFORE 11-i-a's contract freezes; add the **typed-cause-fields pin**; **fold the state-communication question into the already-ruled F3 consult** (no new pre-freeze consult — reasons given, as the brief demanded).
  5. **Q4** — 11-i-a absorbs ALL shared-seam edits (clean audit rule; ~0.13→~0.15); a/b contracts joined by an explicit **interface freeze** in a, cited by b; three straddles named with resolutions.
- receipt pointers: Q1 fork pricing §Q1 · lease design §Q2 · head key §Q3 · split table §Q4 · states + consult §Q5 · tool-honesty note §0
- tool honesty: **every source claim below is grep/Read in THIS worktree** (lore's index watches the main checkout — #125, sanctioned fallback, said out loud). No lore graph calls were made; no store access. Symbols cited, never line numbers.

---

## 0. Context held and provenance discipline

Read in full this sitting (2026-07-25, worktree @ `0ff8868`): the ruled design R1–R8 + Addenda A–E (all 1176 lines) · `CONTRACT-FREEZE-DECISIONS.md` incl. §0's four rulings and §C-ter · the packet file (knowing its C8 defect: never updated for Addendum D) · `REPORT-fable-design-11i.md` (predecessor — read, not redone) · `REPORT-scout-11i.md` · `REPORT-design-blind-11i.md` · `surrealdb-31-capabilities.md` §1, §2 (record-id facts), §5 (hot rows), §6 · `2026-07-06-client-needs-consult.md` (Q4/Q5 informant sections + synthesis + operator ruling) · the packet doc · BASELINE-RED noted · the live probe script's docstring/pre-registered constants (`probe_bootstrap_degeneracy.py`, read-only — it is another agent's working file).

Claim tags per the brief: **[design-cited]** (R/B/C/D/E/§ citation) · **[source-verified]** (I read it in this tree, symbol named) · **[my judgement]** (isolated deliberately — the operator's brief asks for exactly this separation). Where my predecessor or the scout verified something and I re-verified it myself, I tag it source-verified; where I rely on their report alone, I say so.

First-hand re-verifications performed this sitting (grep in this worktree): `_txn.retry_on_conflict` signature · `scout.CommandSubscriber._mark`'s CAS docstring ("WHERE status = 'pending' RETURN BEFORE … an empty claim means ANOTHER instance") · `SurrealStore.upsert` writes the deterministic point id as the row id · `search._COSINE_WEAK_MATCH_FLOOR: float | None = None` · `records.sha512_hex` exists · `SurrealStore._bare_id` is a private staticmethod.

---

## Q1 — The contingency: if the bootstrap is DEGENERATE, what carries adoption/upgrade/staleness?

**I am pricing a branch, not predicting the probe.** The objection is S1 as filed (decision package §C-ter S1; not re-derived here). What follows is the fork map so a DEGENERATE verdict does not arrive flat-footed.

### Q1.0 — The structural fact that shapes every branch [my judgement, argued]

The degeneracy is a property of the floor's **depth in the tail** — how many union samples sit strictly below the selected floor — not of the bootstrap as such. Nonparametric bootstrap is inconsistent for *extreme* order statistics but consistent for *interior* quantiles. The 5% false-fire budget places the floor at ≈ 0.05·N samples deep: at the recorded N=56 that is ≤2 (extreme; bootstrap-hostile — S1's exact regime), at N=600 it is ~30 (interior territory). **The non-automatic part** — and the reason this must be measured, not assumed — is the dominance ordering: max-catch ranks FIRST **[design-cited §1.5]**, so the catch constraint can pin the selection at an extreme even when the false-fire budget alone would sit interior; and the probe's own two absent-arm legs (fixed-15 vs pool-scaling — read in its docstring **[source-verified: `probe_bootstrap_degeneracy.py` module docstring]**) exist precisely because the catch denominator's scaling decides which regime the portable instrument lives in. So the probe's N-ladder is asking exactly the right question, and neither outcome is safe to presume.

### Q1.1 — The cheap branch: DEGENERATE at 56, resolves on the ladder at some N*

Repair is a **guard, not a replacement**:

- **Pre-registered degeneracy/depth validity gate:** no adoption unless the CI spans ≥3 distinct candidate values AND the selected floor has ≥K samples strictly below it (K pre-registered; the blind reviewer's own escalation criterion — "degenerate or spans fewer than ~3 distinct candidate values" **[design-cited blind §8]** — converted into a validity gate, the same move R3 makes everywhere else).
- **The stability gate gains the same guard:** `ci_low == ci_high` can never PASS the ≥98% gate (it currently passes it trivially and adopts the smallest N tried — S1's silent-failure half). The gate's pass predicate becomes "≥98% agreement AND non-degenerate interval".
- The N-curve's adopted-N rule then lands where the ladder first exits the degenerate regime — measured, not assumed.
- **Legacy-arm note:** F_legacy (n=56) may sit permanently in the degenerate regime. R2's acceptance is untouched — it judges by the false-fire/catch **scalars** against the legacy labeled sets, never by a legacy CI **[design-cited §3 lab protocol / R2]**.

R1–R8 + A–E survive **unchanged**. Contract impact: two pins and two row fields.

### Q1.2 — The design-repair branch: DEGENERATE persists at all N (leg B included)

Then the interval object itself cannot carry the three jobs D6 collapsed into it, and the disjoint-CI test needs **replacing, not parameterising** (the lead's framing, affirmed). Candidates, ranked by how much of R1–R8 survives:

**K1 — Decision-distance (recommended frame) — survives nearly everything.** The design ultimately consumes the CI only through DECISIONS (the ≥98% gate counts verdict flips between ci_low/ci_high; disjointness is read as "distinguishable"). Replace the interval with the decision metric directly:
- *Flip-fraction between two floors* = fraction of union samples whose `_cosine_absence_predicate` verdict differs under floor A vs floor B (the production predicate, imported — same identity-pin discipline).
- **Adoption:** adopt iff flip-fraction(fresh, adopted) > the pre-registered bar. **Per-tier upgrade (D6):** tier gets its own floor iff flip-fraction(tier, pooled), evaluated on the tier's samples, > the same bar. **N-stability:** replace bootstrap-CI width with *split-sample agreement* — deterministically partition the pool (hash-order alternation, the D2 key), compute floors on each disjoint half, flip-fraction between them; N passes at ≤2%. **Staleness** stays a measurement (D3's soul): stale ≡ fresh measurement decision-distant from adopted.
- What survives: R1 probes ✔ · R2 acceptance ✔ · R3 pre-registration-as-code ✔ · R4 leg-1 + exact-skip ✔ · D3's "staleness is a measurement" ✔ · **D6's one-test unification survives, re-expressed in decision units** · D1's zero-embed economics ✔ (all arithmetic) · E5's determinism actually *strengthens* — split-sample is RNG-free, so the arithmetic layer needs no seed at all (C1's seed pin narrows to "no RNG anywhere").
- What dies: the interval as persisted/served object (ci_low/ci_high/B/method row fields → flip-noise fields); E5's "within-CI by construction" fallback re-words to "within the measured flip-noise floor"; C6(e)'s typed provenance fields change shape. Schema impact lands in **11-i-a** — which is exactly why §0 holds the split rewrite until S1 lands (affirmed in Q4).
- Honest weakness **[my judgement]**: point-vs-point flip-fraction does not hedge the FRESH measurement's own noise the way disjoint intervals hedged both symmetrically (D3's stated rationale). Mitigation, measured-not-inherited-conformant: the split-sample noise measurement yields an empirical per-run noise floor *in the same decision units*; pre-register adoption bar = max(2%, measured split-half flip noise). The hedge is restored with a measured quantity, no invented constant.

**K2 — Bootstrap the RATES, adopt an admissibility band.** False-fire/catch rates are means → bootstrap-consistent; the "interval" becomes the set of candidate floors whose resampled bar-compliance exceeds a coverage level. Preserves interval language and most of D1, but the band's edges are still sample order statistics, the pre-registration is harder to state attackably, and it is more novel statistics than K1 for no extra job coverage. Second.

**K3 — Smooth the statistic (floor as interpolated quantile, bars as validity constraints).** Makes the bootstrap consistent by changing what is estimated — but it amends the RULED selection rule (§1.5's dominance ordering, identity-pinned prior art, and the factual basis of C1's wording verdicts), and it re-opens the F3 evidence base. Deepest cut into ruled design; only if K1/K2 fail. Third.

**K4 — m-out-of-n / subsampling bootstrap.** The textbook remedy for extreme order statistics — and a poor fit here: it needs a subsample-size constant m (an invented constant of exactly the class this design keeps killing), its interval rescaling needs a convergence rate no one has for a dominance-selected statistic, and at n≈56 it is hopeless regardless. Last.

**Cross-rider for any branch (raise now, cheap):** S4 (chunks are not iid — many chunks per file **[design-cited blind S4]**) biases ANY resampling/split noise measure narrow. If the repair fork opens, resample/split at **file granularity** (cluster level) — one pre-registered choice that fixes S1's neighbour in the same stroke. K1's split-sample takes this naturally (partition files, not chunks). Also noted: K1 is indifferent to S3's paired-dominated-legs concern (a decision metric does not model arm independence) — a small extra point in its favour.

**Consumer-law flag (per my standing instruction):** if the fork opens and a degenerate measurement needs its own recorded condition (`measurement_failed` vs `measured_not_adopted` — the assignment is arguable both ways and I have deliberately NOT decided it), what an agent is *told* about a degenerate measurement is a serving question → it rides the same consult channel as Q5, not this desk.

---

## Q2 — Single-flight lease: release/expiry consistent with §5's clock ban

**The hole, affirmed as filed:** nothing in R1–R8/A–E addresses lease release **[design-cited blind §7.3]**; §5 rules "quiescence over clocks; no invented cooldown constant" **[design-cited §5]**; a blocking lease with no liveness signal deadlocks permanently on holder death. This is 11-i-a's own schema+concurrency work, so it must be settled pre-freeze.

### Q2.0 — The reframe that dissolves the deadline pressure [my judgement, argued]

Separate the lease's two jobs. **Correctness** (no torn/duplicate adoption state) must not live on the lease at all: measurement rows are append-only **[design-cited B4]**, and the head mint is a CAS through `_txn.retry_on_conflict` **[design-cited B4; source-verified: `retry_on_conflict` signature re-read]**. **Economy** (don't run two constant-cost surveys concurrently) is all the lease buys. Once correctness is lease-independent — via the fencing guard below — a stale or seized lease costs one wasted constant-bounded run, never a wrong row. That converts "when may a lease be broken?" from a safety question into a cost question, and cost questions tolerate lossy answers. This is the precondition for any clock-free discipline being acceptable.

### Q2.1 — Option A (recommended): epoch-fenced lease + clock-free reclamation

Entirely inside ruled text; no hand-rolled retry anywhere; the seam is `retry_on_conflict` only.

1. **Lease row** (one per instance — the lease stays instance-global under D6: one run measures every statistic/scope from one capture set **[design-cited B2/§5]**) carries `(holder_id, fence_epoch)`. `fence_epoch` is minted through the counter-row UPSERT shape (the findings-mint precedent — monotonic, driver-ridden **[design-cited capabilities §5; scout §3.1]**). `holder_id` = a per-process boot nonce.
2. **Claim = CAS**, the in-repo shape: `UPDATE … WHERE <available> RETURN BEFORE` — an **empty result is a lost race with defined meaning and is NEVER retried** (the `scout.CommandSubscriber._mark` semantics **[source-verified: its docstring, re-read this sitting]**); the loser sets the B2 coalescing re-run flag and returns. Retryable conflicts ride the driver transparently; classification is never local (#102/#120 law).
3. **Release, normal path:** `try/finally` in the runner + the task-lifecycle discipline (in-process task death — exception or cancellation — always runs finally). In-process holder death is thereby a solved, non-store problem.
4. **Crash recovery — reclamation, not expiry.** A held lease may be SEIZED by CAS-ing a strictly higher `fence_epoch`. Seizure is legitimate under either of two **clock-free** conditions:
   - **(a) Boot reclamation:** at engine boot (an A1 chokepoint), seize unconditionally. B1 makes the AppContext task the only durable claimant **[design-cited B1]**; at boot, no prior generation of this process can hold a live lease. The one legitimate cross-process holder — a concurrently running one-shot verb — is broken *harmlessly* (see 5).
   - **(b) Quiescent-trigger reclamation (steady state):** a chokepoint evaluation that finds lease-held ∧ re-run-flag-already-set ∧ no in-process run task alive has PROVEN the holder is not this process — and this process is the only durable home. Seize. This is quiescence-as-liveness: the signal is "the system's own settling events keep arriving while the lease never moves," counted in **events, not seconds** — §5's exact preference structure, applied to release.
5. **Fencing makes seizure safe:** every end-of-run write (the adoption/head-mint transaction) is guarded `WHERE lease.fence_epoch = $my_epoch` **in the same transaction**. A zombie holder fails its final CAS loudly; its run is discarded as a lost race (defined-empty-result semantics — logged, never retried, never silently swallowed). Standard fencing-token discipline, and it rides existing seams: no new retry policy, no local marker matching.
6. **11-i-a's pins:** ≥8-way overlapping-lifetime contention on claim+seize+fenced-write, 20 consecutive greens (capabilities §5's two laws **[design-cited]**); a seize-mid-run fixture proving the zombie's fenced write is REJECTED and the seizer's accepted (the discriminating fixture — a lease build without fencing passes everything else). Scout §3.3's coverage obligation applies: if the lease ships as a conventional `_query`-owning ledger it is auto-discovered into the mutation proofs; any bespoke shape must be hand-added to the observed-coverage drive list — a's contract carries this line either way.

TTL expiry was considered and is rejected without needing a ruling: a guessed clock constant with a failure mode in both directions (too short → double-run while the holder is alive-but-slow; too long → the deadlock it was meant to fix, deferred) — §5's objection verbatim.

### Q2.2 — Option B (flagged, simpler, but amends ruled text)

Since correctness is fencing/CAS-carried anyway, the durable lease's only remaining value is cross-process economy (the rare R2-verb-vs-server race). Option B: delete the durable lease; single-flight is in-process only (asyncio guard + coalescing flag — dies with its holder, deadlock class removed *by construction*); the store keeps an advisory run-in-flight note nothing blocks on; the fenced head-mint CAS still serializes writers. Strictly less machinery, strictly no deadlock. **But** §5/B4 say single-flight is "coordinated through the store" **[design-cited]**, so B is a design amendment only the operator can take. My recommendation is **A** (no ruled-text change, and the fencing work is needed for A anyway); B is on the table because it is honestly simpler and I am not entitled to bury it.

---

## Q3 — The head-pointer key (the D6 collision)

**Recommendation: the head is keyed on the pair (statistic, scope).** D6 already defines the served unit as *(statistic, point, CI, scope)* **[design-cited D6]**; the head pointer is precisely "the latest adopted row for a served unit," so its key must be the unit's identity minus the per-measurement members: **(statistic, scope)**. Today that is exactly one head — (`response_best_cosine`, `pooled`) — so the generalisation costs nothing now and removes the migration later. This *chooses D6's reading over B4's* "one minted head pointer per scope," which was written one addendum before D6 generalised the unit — an amendment-ledger entry for B4 (blind §7.25's mechanism), not a re-open.

**Why this is the ONE truly hard freeze in 11-i-a [design-cited capabilities §1/§6.2 + my judgement]:** field ASSERTs migrate by `DEFINE FIELD OVERWRITE` (the B4 rule — cheap, known mechanism), but a record's **identity** does not — re-keying head rows after the table ships is a copy-rewrite migration. Blind C2's "deciding this after the table ships is a migration" is precise, and it is *more* true of the key than of anything else in the schema. Spend the freeze-attention here, not on the state strings (see Q5.0 for the deliberate contrast).

**Mechanics for a's contract:**
1. **Encoding trap [source-verified + design-cited]:** scope strings contain `:` (`tier:<name>`, §7), so a naive `f"{statistic}:{scope}"` id is parse-ambiguous between its own components. The capabilities file documents `type::record(..)` and RecordID round-trip (§2) but is **silent on composite/array record-id forms** — so whether an array-shaped id is safe on 3.2.1 must go through the standing order of authority (capabilities → `surrealql-tests` tier → vendor docs → probe) by someone with store access; it is a named verification item for the C7-style adversary pass, **not** something to design blind here.
2. **Default that needs no engine novelty:** head id = `records.sha512_hex(statistic + "\x00" + scope)` — deterministic, unambiguous, collision-free, the existing helper (ONE IMPLEMENTATION), and immune to the `str(RecordID)` angle-bracket landmine (§D.11) because the id is plain hex. The mint stays the `type::record('floor_head', $id)` UPSERT shape through the driver.
3. **Identity also travels as FIELDS:** `statistic` and `scope` are persisted as queryable columns on both measurement rows and the head — the capabilities file's own rule that you cannot index or prefix-match a RecordID's string component, so the queryable value must be carried beside the id **[design-cited capabilities §2]**. The record id is only the uniqueness/CAS anchor.
4. **`statistic` is a closed-set string** (today one value; name it for what the floor describes — `response_best_cosine`), covered by the same exact-set pin discipline as the states. Flag, per my standing instruction: the statistic's *name* eventually surfaces in W-C's derived provenance render (C6(e)) — a served-adjacent naming choice; it rides the Q5 consult channel at zero marginal cost, and 11-i's machine token is renderable-to-anything in 11-ii regardless.
5. **Do not conflate the two keys:** the lease stays instance-global (Q2); only the head is per-(statistic, scope). One sentence in a's contract prevents a builder "helpfully" scoping the lease per head and re-opening the single-flight semantics.

---

## Q4 — The split boundary, made contract-precise

The operator ruled the line (§0): **11-i-a** = store + engine skeleton (~0.13), **11-i-b** = runner + R2 (~0.29), rewrite deferred until S1 lands. What follows makes the line writable-against.

### Q4.1 — The assignment rule, stated once [my judgement, recommended]

> **11-i-a owns everything that touches `loremaster/store/*`, the schema, shared seams, and the engine's persistent API. 11-i-b owns everything that is pure runner arithmetic, probes, and the R2 verb.**

The rule's payoff is auditability: a's cold audit is a concurrency/schema audit with zero statistics in it; b's is an arithmetic audit against an already-frozen store API. Consequence: a absorbs the three shared-seam edits b needs (below), and a's estimate creeps **~0.13 → ~0.15**. Still comfortably the small half.

### Q4.2 — Contents, exactly

**11-i-a (store + engine skeleton):**
- Schema slice: `floor_calibration` table + field specs + statements generator + registration in the `_generated_ddl()` test dict + `EXPECTED_TABLES` convention (the scout's six mechanical sites, §2.3) — DDL per capabilities §1.1 (packet entry-check rule).
- Row fields: the full §7+D7 union **including** `corpus_content_digest` (C10) and the in-row probe manifest (C11) — a defines the fields, b populates them; B4's OVERWRITE rule is the additive escape valve if b discovers a gap, and the contract SAYS so (deferral-with-mechanism, not hope). ⚠ The interval fields (`ci_low`/`ci_high`/`B`/`method`) are **S1-gated** — a's contract cannot freeze before the probe's verdict (affirming §0's own hold, and extending it explicitly to a's contract, not just the packet rewrite).
- Head pointer per **(statistic, scope)** (Q3) + mint via `retry_on_conflict`.
- Single-flight lease + fencing per Q2's ruled option; concurrency pins (≥8-way, 20 consecutive, seize-mid-run discriminator).
- 8-state closed set **as re-predicated by the C3/C4 repairs** (Q5) + the built exact-set distinctness pin; the RAISED-5 parametrised-pin fold covering CalibrationEngine's five states rides here if the operator approves it (it is test-only; the sibling pin is being authored anyway).
- The typed-cause-fields pin (Q5.3).
- Render model class (`from_engine_status`-shaped payload, dark — nothing reads it until 11-ii).
- `build_app_context` wiring (construct → `ensure_ready()` → `write_stack_readied`): **recommend a**, dark until any deploy, and it kills the RAISED-2 silently-unwired-table class at birth. Alternative (defer wiring to 11-ii) costs a known-hazard class for no saving — flagged, not silently chosen.
- The three shared-seam edits b needs: (i) exhaustive-enumeration support for C8 (count-then-scroll-with-limit>count, or a store method if `scroll` cannot carry it — a shared-seam escalation either way); (ii) `Candidate`/hit payload exposing the row's point_id for C13 (a store/search-surface edit; served-byte proof required — the field is additive and unrendered); (iii) a sanctioned public accessor for the bare record id (`_bare_id` is private **[source-verified]** — the D.2 caveat).
- **The interface freeze:** a's contract publishes the engine/ledger API signatures (append_measurement, mint_head, claim/release/seize, read_adopted_head, the state-transition entry points); b's contract CITES them and may not re-declare. This is the anti-contradiction mechanism between the two contracts — without it the C1-era "two authors read one sentence opposite ways" failure re-enters through the seam.

**11-i-b (runner + R2):**
- Core port from `scripts/` into `loremaster` + re-homing the 50 tests into the gate + the three `is`-identity pins (RAISED-4; the port is a hard requirement — `scripts/` is not in the image **[design-cited scout RAISED-3a]**).
- Hash-stable pool sampling keyed on the row's own id (D2 as corrected); identifier sampling per C12; probe-text derivation; skips counted.
- Answered + hold-out legs (k′, empty-leg rule per C9); self-retrieval matching per C13 (consuming a's exposed point_id).
- Bootstrap/interval machinery (D1) — or its K1 replacement if S1 forks; N-curve + stability gate (C2's denominator, C4's nesting); paired decomposition (D4); cost capture (D5).
- The determinism control (E5's must-prove pin) **lives in b** — it needs the full runner. Say this explicitly in both contracts: a must not be graded against a pin it cannot express, and the packet-level "must-prove" language moves to b.
- The R2 verb (`python -m loremaster.<floor_module>`, C7's no-default-coordinate + provenance receipt + the §0 riders incl. the #134 verification item) executing the COMPLETE engine path through a's API (C6); the C6(a)–(f) evidence package at the C5 tracked address; C14's O(probes) reconciliation sentence.

### Q4.3 — C1–C14, assigned

| item | half | note |
|---|---|---|
| C1 seed + replay control | **b** | narrows to "no RNG anywhere" under K1 |
| C2 gate denominator | **b** | |
| C3 30/15/30 validity minimums | **b** predicate / **a** state string | the split is clean once stated: a owns the closed SET, b owns each state's transition predicate |
| C4 N-curve nesting | **b** | |
| C5 evidence address | **b** | |
| C6 R2 adopts (full path) | **straddles by design** | resolved by the interface freeze: a ships primitives sufficient for the full path; b's verb must call them, never re-implement |
| C7 verb shape + provenance receipt | **b** | + §0's #134 rider as a measured verification item |
| C8 exhaustive enumeration | **b** protocol / **a** store support | the seam edit is a's per the assignment rule |
| C9 k′ / empty absent leg | **b** | demand the all-source-hits fixture |
| C10 corpus_content_digest | **a** field / **b** writer | |
| C11 probe manifest in-row | **a** field / **b** writer + the surviving≡full pin | |
| C12 identifier sampling | **b** | insertion-perturbation fixture |
| C13 self-retrieval match key | **b** semantics / **a** the Candidate point_id exposure | two-chunks-one-file fixture |
| C14 O(probes) vs full-pool R2 | **b** | |

### Q4.4 — Straddles that could make the contracts contradict (the flag the brief asked for)

1. **The state DOMAIN (a) vs state TRIGGERS (b).** If the C3/C4 repairs are not in the short design addendum before a freezes, a pins damaged strings and b later needs states a's ASSERT forbids. **Order constraint: addendum → a's contract → b's contract.**
2. **a's row schema encodes b's output vocabulary.** Mitigated by B4's additive-field escape valve, stated in-contract; but the S1-dependent fields make a's freeze **probe-gated** — the one place the two halves cannot be decoupled by any mechanism.
3. **The engine API seam.** Without the interface freeze, a and b will each "reasonably" declare it. The freeze is one section in a's contract; its absence is how two green contracts contradict.
4. **The determinism pin's home.** Packet text hangs it on "the packet"; only b can prove it. Assign explicitly or a's cold audit dings a for a missing pin / b assumes a carried it.
5. Nothing else resisted assignment. R2's *ruled vehicle* (§0 §B) binds b; the DDL-review rider binds a's audit — both already operator-assigned.

---

## Q5 — The state set, and the consult that should replace my reasoning

### Q5.0 — What 11-i-a actually freezes, priced first [design-cited + my judgement]

The state field's closed set is enforced as a schema **ASSERT on a new table** — and ASSERTs migrate by `DEFINE FIELD OVERWRITE` with no retro-validation of existing rows (capabilities §1.1, §6.2 **[design-cited]**; rows here are append-only and never rewritten, so history never re-validates). So the state DOMAIN is a **medium-cost** freeze: changing it later is a known-mechanism DDL migration plus a rename-sweep (with that sweep's documented failure class — CLAUDE.md's rename law — which is the real cost). Contrast the head key (Q3): record identity is the *hard* freeze. This matters because the brief's framing — "durable choices that permanently bound what 11-ii can tell an agent" — lands **most heavily not on the strings but on the FIELDS**: a render can rename, merge, or re-word states after a consult; it **cannot render a distinction the row never recorded**. That re-pricing drives everything below.

### Q5.1 — The state-set recommendation I would make (machine domain)

Keep the closed 8, with two re-derived predicates and one rename:

1. **`stale_remeasuring` → re-predicate to leg-1 ONLY:** "vector-identity/fingerprint invalidation; the adopted floor is known-invalid; re-measure queued/awaiting reconcile settle." Under D3 this is the only waiting-stale condition that survives: churn staleness is deleted, and a disjoint fresh measurement causes immediate *adoption*, not a stale interlude **[design-cited D3; blind C3]**. Because the surviving predicate is *known-invalid*, not *aging*, the string now lies about its own semantics — **rename to `invalidated_remeasuring`** [my judgement, via the prose-derives-from-behaviour law applied to state names]. Now is the free moment; post-ship it is a rename-sweep.
2. **`insufficient_corpus` → restore the 30/15/30 as validity floors**, recorded explicitly as *restoring a predicate D0's retirement sentence removed* (the C-ter composition of ESC-9 + blind C4 — both satisfied, stated so the operator rules on the real question). Values attackable by the adversary per §0's §C ruling.
3. The other six: `unmeasured`, `measuring`, `measured`, `measured_not_adopted` (still meaningful — the catch-bar license survives D-series intact **[design-cited §4.4]**), `measurement_failed`, `disabled` — predicates undamaged. Open sub-question deliberately left to the S1 branch: where a degenerate-interval outcome lands (`measurement_failed` = instrument-suspect vs `measured_not_adopted` = recorded-unlicensed) — arguable both ways; do not let a builder pick silently.
4. **Do not carry §7's serving-table columns into a's artifacts.** The "floor served? / verdict / per-hit" columns are 11-ii semantics, and post-E1/D3 several are already stale (blind C3, §7.25's amendment-ledger item). a pins the SET and the transitions, not the serving map — freezing the stale map into a docstring would be the C6-class defect (unmarked superseded text) reborn in code.
5. Ship the exact-set distinctness pin (built, not reused — RAISED-5), parametrised to also cover CalibrationEngine's five states if the operator approves the fold.

### Q5.2 — Where I stopped reasoning, per the standing instruction

Halfway through drafting "an agent in an `unmeasured` state needs to know X" I was doing exactly what the brief forbids: **reasoning out a consumer's needs from a designer's chair.** Stopped. Two things replace it:

**(a) What the clients have ALREADY said — citable, not conjectural.** The 2026-07-06 consult's three-way convergences are standing client design law **[design-cited: `2026-07-06-client-needs-consult.md` Synthesis §1–5 + operator ruling]**: *misses must teach a decision tree — why-branch plus exact next call* (#4); *caveats ship with verdicts; under-claiming is nearly free, one confident-wrong costs session authority* (#3); *state-dependent guidance belongs per-response, not in read-once instructions* (#5). Applying already-ruled client law to a new surface is legitimate design work, and it yields the one pin 11-i-a genuinely needs:

> **The typed-cause-fields pin:** every non-`measured` state's CAUSE and NEXT-MOVE datum is a **typed row field, never only prose** — `insufficient_corpus` carries the three deficit counts; `measurement_failed` carries the failed gate's name and value; `invalidated_remeasuring` carries the invalidating leg and the queued-run status; `measuring`/`unmeasured` carry queued/started markers; plus `measured_at` (exists). Then ANY render the consult later chooses — W-C's derived clause included — is mechanically derivable, and no distinction the clients turn out to want was left unrecorded.

That pin is the whole of what the dark half owes the Consumer Law: **record enough typed truth that no serving choice is foreclosed.**

**(b) The consult itself — for what remains genuinely the clients' question.** Which distinctions agents actually *use* (would they collapse `unmeasured`/`measuring`? do they want the deficit numbers or just "not enough corpus yet"?), what a failed-state render should teach, and the state *names* as served text — none of that is mine or the operator's to settle **[design-cited: the 2026-07-06 ruling — "the models that consume the tool decide what serves them"]**.

### Q5.3 — The consult I recommend (and the one I recommend against)

**Recommended: FOLD the state-communication question into the already-ruled F3 consult.** The operator has already ruled that consult's timing for exactly this surface family — after 11-i, before 11-ii's swap, judging on R2's measured evidence, *"we need to measure first"* **[design-cited C3]** — and the E3 battery already grades the chosen render's staleness-admission family in 11-ii **[design-cited E3 family (a)]**. The fold's marginal cost is ≈ zero: same informants, same evidence package, plus **one added question family and one exhibit** (the real state table, the typed row fields with real values from the R2-era store — C6(e) already ships adjacent material).

Draft consult question (for the record, refinable):
> *"You issued a search while the instance's floor calibration is in state ⟨exhibit: real rendered block + the row's typed fields, for each of: unmeasured · measuring · measurement_failed · insufficient_corpus · invalidated_remeasuring⟩. (1) What must this render tell you to correctly weight the hits you were just served? (2) What must it tell you to choose your next action without a follow-up probe? (3) Which of the recorded distinctions do you actually use, and which would you collapse? (4) Name any datum you need that the row does not record."* — with the routing probe (CALL_AGAIN vs ROUTE_AROUND) asked last, per the §C5/E3 grammar.

Question (4) is the audit of my Q5.1/typed-fields work: if the clients name an unrecorded datum, the additive-field valve (B4 OVERWRITE) covers it cheaply — the fold thereby *tests* the dark half's expressiveness instead of trusting my judgement of it.

**Recommended against: a fresh pre-freeze consult (before 11-i-a's contract).** Reasons, specifically, as the brief demanded: (1) it would judge **blind on hypothetical states with no real rendered examples** — the exact shape the operator's "measure first" rationale retired when C3's immediate-consult alternative was rejected; (2) the freeze it would inform is the **soft** one (Q5.0) — strings and merges stay changeable at rename-sweep cost, and the genuinely binding choice (field expressiveness) is closed by the typed-cause-fields pin plus the fold's question (4); (3) a standalone consult costs a full cycle (two blind informants + synthesis + doc — the precedent's shape) to answer early what the ruled consult answers better, later, on evidence. If the operator nonetheless wants pre-freeze client input on one narrow item, the only candidate worth it is the **state-string names** (the one thing a consult could change that is cheap now and a sweep later) — a single-question micro-consult; my recommendation remains the fold, with names chosen now under the prose-derives-from-behaviour law and re-judged by the consult at zero extra cost.

---

## Follow-up 1 (2026-07-25, from `lead-11i-b`) — the client consult held against Q1, Q3, Q5

Inputs read in full this sitting: `CLIENT-CONSULT-SYNTHESIS.md` (e9b570f) incl. §0's contamination disclosure, and `REPORT-consult-sonnet-11i.md` in full (its §3 CI answer and §5 query-shape finding are load-bearing below; the Opus/Fable degeneracy quotes I take from the synthesis §2.1, which quotes them verbatim). Weighting per §0: everything I rely on below — CI refusal, degeneracy carve-out, margin pair, query shape — is from the CLEAN set; nothing below leans on the contaminated freshness finding.

New first-hand verifications for this answer: `_cosine_absence_predicate(best_cosine, floor, has_verbatim_anchor)` **[source-verified]** · `_has_verbatim_identifier_anchor` exists as the serve-time shape classifier **[source-verified]** · `substrate_gate_passes` / `D1_MIN_MEDIAN_SPREAD = 0.05` exist in the survey core **[source-verified]**.

On my Q5 recommendation against a pre-freeze consult: the lead's consult was already running when I wrote it, and — said plainly — **the instrument as actually run answers my two objections.** I argued a pre-freeze consult would judge blind on hypothetical states and cost a full cycle; this one asked questions answerable from the informants' own experience with no repo knowledge (synthesis §5's own criterion), cost ~15 minutes, and returned findings (CI refusal, degeneracy carve-out, query shape) my recommended F3-fold would have delivered a packet later — after the schema froze. My deferral was wrong about the available instrument, not about the F3 fold (which is still right for the RENDER questions — §2.1's projection wording, the state names, W-C's shape — where R2's real exhibits genuinely matter). Recorded as a correction, not defended.

### FU1.1 — The CI refusal against the Q1 fork: yes, K1 was over-priced; no, the ranking does not change

**The design never committed the CI to a served surface** — D1 explicitly parked "whether the RENDER should say anything when a best-cosine lands inside the interval" in the F3 option space **[design-cited D1]**. The consult now closes that option: 3/3 refuse, unhedged, same argument independently **[design-cited synthesis §1.3]**. So the interval's roles reduce to exactly three, all internal: adoption test (D3), upgrade test (D6), N-stability gate (D2), plus its persisted row fields as tuning history.

**Re-pricing K1.** My cost table listed "the interval as persisted/served object" under what dies. The *served* half of that entry is now worth zero by client ruling — there was never going to be a served interval to lose. What actually dies under K1 shrinks to: internal row fields change shape (cheap; additive-field mechanics), E5's fallback re-words (internal), C6(e)'s evidence package changes shape (consult-facing doc, cheap). **K1's price drops modestly; stated plainly: the ranking does not change — it widens.** K2's principal selling point was "preserves interval language and most of D1"; if the interval is purely internal machinery, preserving its *language* has no client value, only continuity value — K2's advantage was partly cosmetic and is now priced as such. K3 and K4 are unmoved (K3's cost was never the serving surface; it was amending the ruled selection rule).

**The fork's stakes re-price too, in both directions [my judgement]:**
- *Down, on the served side:* the lead's synthesis §4.1 is right — a DEGENERATE verdict costs no served surface anything; it is a replacement problem confined to internal machinery.
- *Up, in one specific place:* §2.1 creates a NEW obligation that is **branch-independent** — degeneracy is now the one non-adoption cause the clients have ruled they want served, *as a corpus property*. Whatever mechanism survives the fork (interval kept, guarded, or replaced by K1) must emit a well-defined, typed degeneracy datum. My Q1 no-regret pins (degeneracy guard on the gate; CI candidate-count + tail depth in the row) acquire a consumer-ruled reason on top of their instrument reason. K1 passes this test: under K1 there is no CI to be degenerate, but the corpus-side datum is directly measurable (see FU1.2's distinction) and the split-sample noise floor is its instrument-side counterpart.

### FU1.2 — The degeneracy carve-out: the pin's shape changes, and the lead is not over-reading — with one boundary drawn sharper

**Yes, this is an 11-i-a schema requirement.** By my own Q5.0 argument (the render can rename and collapse; it cannot render a distinction the row never recorded): if 11-ii must serve degeneracy-as-corpus-property (now client-ruled, 2/3 blind-independent **[design-cited synthesis §2.1]**), the row must record a non-adoption cause 11-ii can project. Free prose or an unrecorded cause forecloses the ruled render. The typed-cause-fields pin sharpens from "a typed cause field exists" to:

> **`measured_not_adopted` (and `measurement_failed`) carry a CLOSED, exact-set-pinned cause enum, not prose** — and the enum distinguishes **two degeneracies that must never collapse into one value**:
> 1. **`interval_degenerate`** — an INSTRUMENT property: the resampled selection collapses (S1's regime — a tail order statistic too deep for the bootstrap). This can occur on a corpus whose scores discriminate perfectly well.
> 2. **`corpus_indiscriminate`** — a CORPUS property: the score distributions genuinely fail to separate ("everything similar to everything" — Fable's words). The measured datum for this already has a home: the substrate spread median is in §7's persisted results **[design-cited §7 field list]**, and `substrate_gate_passes` / `D1_MIN_MEDIAN_SPREAD` is the existing instrument for it **[source-verified]** — the pin makes that field load-bearing rather than decorative.

**Why the distinction is the load-bearing part [my judgement, grounded in ruled law]:** the informants' carve-out serves the corpus-property sentence — "semantic search discriminates poorly on this corpus, downgrade the positives too." That sentence is only EARNED by degeneracy №2. Projecting №1 into it would serve a confident corpus claim licensed by an instrument artifact — a confident-wrong of exactly the class §1.3/the Trust Doctrine prices at session authority. So the schema must keep the two apart; the projection (11-ii) maps №2 to the ruled corpus-property render and maps №1 to the uncalibrated collapse *unless* №2 co-fires. The lead's reading is right on the field; the one place it would over-reach is if the PROJECTION function itself were pulled into 11-i-a — that stays 11-ii serving code, now constrained by §2.1, and per synthesis §4.2 it must be ONE pinned function of the typed state, never seven hand-rolled collapses (a 11-ii packet-file line — lead's edit, outside my writable set, flagged).

**Ratifications worth one line each:** the consult's served projection (~3 states) validates the Q5.0 machine/served split — the 8-state machine domain survives untouched (the informants collapse the VIEW; the FACTS they call load-bearing — measurement-failed announced once, corpus-too-small kept 2/3 — require the machine distinctions to exist). §1.5 (withhold the verdict layer, never the data) is A1/E1's under-claim default, client-ratified **[design-cited]**. Fable's "the mechanism must never eat the function" (§3) lands on Q2: my fencing design already keeps the lease off the serving path, and it is worth promoting to an explicit a-contract property — **no serving-path frame ever touches the lease or blocks on the engine; calibration failure degrades to results-without-verdict, never to no-results.** And synthesis §4.5 (inline delivery, 3/3) converts "state rides the search response" from render preference into an **API-cost requirement on a's read path**: `read_adopted_head` must be cheap enough to sit on every search call — which is what A1's evaluate-at-chokepoints/serve-reads-state amendment already architected, now with a client receipt behind it **[design-cited A1; synthesis §4.5]**.

### FU1.3 — Query shape vs the head key: the encoding absorbs it; the axis is real; the design already half-knew

**(a) The encoding question, concretely.** Sonnet's axis does NOT reproduce the C2-class migration — with one refinement I now recommend to make that robust for ANY future axis, not just this one.

- *Why the plain pair does not re-create C2:* the C2 collision was a key too COARSE to distinguish two things that must coexist — a per-scope head cannot hold two statistics; the second overwrites the first's slot. A later query-shape axis is different in kind: per-shape heads would mint NEW identities alongside the pair-keyed head, which retains a coherent meaning ("the shape-pooled floor"). Coexistence, not collision — additive mint, not identity rewrite.
- *The refinement — default-eliding canonical axis serialization [my judgement, recommended]:* define head identity once, as a function: `head_identity(axes: Mapping[str, str]) -> str` = `sha512_hex` over the sorted `(axis_name, value)` pairs joined by `\x00`, where `statistic` and `scope` always serialize, and any FUTURE axis serializes **only when its value differs from its pinned default**. Consequence: registering a new axis at its default (`query_shape="any"`) changes **no existing head id** — zero migration by construction; a non-default value mints a new head. This is pinnable with a discriminating mutation fixture: *adding a defaulted axis to the registry MUST leave every existing head id byte-identical; a non-default value MUST change it.* The axis-name registry is a closed set under the same exact-set pin discipline as the states. One function, mutation-proven (ONE IMPLEMENTATION), replaces my earlier bare `sha512_hex(statistic‖scope)` — same ids today, future-proof tomorrow.
- *Two API consequences for a's interface freeze:* `read_adopted_head` takes an **axes mapping**, not positional `(statistic, scope)` arguments — so a fourth axis never breaks the signature; and the queryable identity FIELDS on rows/heads gain any future axis additively (`DEFINE FIELD OVERWRITE`, cheap **[design-cited capabilities §1]**).

**(b) Is the axis real? Yes — and the design contains measured evidence for it without having drawn Sonnet's conclusion.** The lead's reading is supported, on three in-tree receipts:
1. **#74 is a measured instance of shape-dependent miscalibration:** the original floor's 4.0% false-fire was blind to an entire query class until implementation-vocabulary probes entered the union — §3 says so in those words ("breaking the eval-question monoculture that made the original false-fire blind to a whole query class") **[design-cited §3/§1.5]**. The class that broke the calibration was a query SHAPE.
2. **The anchor carve-out is a shape-conditional serving mechanism already:** `_cosine_absence_predicate` exempts verbatim-anchored queries from the verdict entirely **[source-verified: signature + docstring]**, and `_has_verbatim_identifier_anchor` is a serve-time shape classifier **[source-verified]**. The design did not pool identifier-shaped queries into the floor blindly — it shielded the most divergent shape class from the verdict by mechanism. That is implicit acknowledgment that shapes' score distributions differ. (Blind §7.9's observation — anchored samples deflate the false-fire bar through the denominator — is the same fact seen from the bar's side.)
3. **The strata are shape buckets:** the four measurement groups (prose questions / identifiers / implementation-vocabulary / nonsense) and C6(b)'s per-group distributions **[design-cited §1.5, C6(b)]** mean R2 will *measure* shape-stratified distributions as a side effect of what it already publishes.

So the lead's inference stands: **the shapes were known to differ at measurement time; the served floor stays pooled; the conclusion Sonnet drew was never drawn.** The design's own disposition pattern for exactly this structure already exists — R8→D6: measure stratified, serve pooled, pre-register the upgrade test. Query shape is scope's mirror image (corpus-side axis vs query-side axis), and D6's one test extends verbatim: *a shape bucket earns its own served floor iff its measurement is decision-distinguishable from the pooled one* (disjoint-CI, or K1's flip-distance, per the S1 branch). Recommended dispositions, in order of cost:
- **Now (11-i-a, ~zero cost):** the `head_identity` refinement above + `query_shape` reserved in the axis registry at default `"any"`. The freeze stops foreclosing the axis; nothing else is built.
- **At R2 (11-i-b, ~zero marginal):** pre-register the shape-separation report over the groups R2 already publishes — the same move R8 made for tiers. Honest bound, stated where the number will sit: R2's probe shapes are description-shaped + identifier-shaped; live traffic's shape mix is packet 35's instrument, so R2 measures *separation among probe shapes*, not live-shape coverage.
- **Sonnet's minimal ask** — "disclose which query-shape the threshold was validated against" — is a W-C provenance clause / C6(d) exhibit item for the F3 consult's option space, not 11-i work; flagged to the lead.
- **If a shape bucket ever separates:** serving per-shape needs a serve-time shape classifier with its own honesty story — the anchor detector is the in-repo precedent that this is buildable; it is nobody's current scope and forecloses nothing above.

**Consumer-reasoning flag (standing instruction):** everything in (b) argues from measured in-tree receipts and the informants' own words, except one step — "the anchor carve-out implies the design knew shapes differ" is my inference from a mechanism, not a recorded design intent; I have marked it as such rather than presenting it as history.

---

## Standing by

Follow-ups via SendMessage; answers appended above, stamped. — `fable-design-11i-b`, 2026-07-25
