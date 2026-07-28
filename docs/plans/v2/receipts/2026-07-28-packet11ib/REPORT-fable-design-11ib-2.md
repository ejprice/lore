brief-base v7 read

# REPORT-fable-design-11ib-2 — design sidecar, packet 11-i-b (floor-calibration: runner + R2), first deliverable Q1–Q6

## SUMMARY BLOCK
- `brief-base v7 read` · agent `fable-design-11ib-2` · worktree `/home/ejprice/PycharmProjects/lore-pkt11i-b`, branch `pkt11-i-b-floor-runner`, HEAD **`2bf7631`** (one commit past the briefed base `2b8aa01` — the lead's baseline pin; noted, not a deviation of mine) · written 2026-07-28
- state: **done** (Q1–Q6) — STANDING BY for follow-ups via SendMessage
- deviations: none. Read-only apart from this file; no git mutation; no store/network access. `REPORT-scout-11ib-1.md` had not landed at writing time — sizing inputs are marked ASSUMED where the scout owns them.
- `Packages considered:` `sklearn.metrics.roc_curve` / `scipy.stats.bootstrap` / `np.percentile(method="inverted_cdf")` → **replace** (read: R9.1 + R-A..R-H installed-source receipts, plus `loremaster/stats.py` in THIS tree — the #198-consolidated home exists) · `kubernetes.leaderelection.try_acquire_or_renew` → **replace_with_adapter, already shipped** (read: shipped `store/lease.py` + installed `leaderelection.py::try_acquire_or_renew`, grepped this sitting) · consult instrument → **bespoke** (in-house method doc `2026-07-06-client-needs-consult.md` is the prior art; no package runs a model consult)
- decisions-needed (each expanded in its Q-section):
  1. **Q1** — keep 11-i-b WHOLE at ~0.24±0.03 (rec) vs pre-split at the offline/live seam. Wrong-split cost: a full second contract→adversary→audit cycle (measured overhead on 11-i-a: seven stages for ~0.15 of build). Wrong-keep cost: an ungradable contract if the scout's number crosses 0.30.
  2. **Q3** — the R2 verb consumes the shipped lease via ONE `try_acquire_or_renew()` + fenced commit + `release_if_held` in finally (rec — derived from E3/R2.4, no new machinery); the mid-run-seize discard window is DISCLOSED, not hidden. Alternative (unfenced, no lease) amends ruled text.
  3. **Q5** — authorize the receipts-consult battery (rec: pre-contract, synthetic exhibits, 3 informants + 1 degraded-variant control leg, keyed tasks + routing probe). Cost of skipping: the C6 evidence package is built to a designer's guess and graded only after R2 — C5's own "late-and-unrecoverable" class.
  4. **RAISED-1** — rule ownership of the measurement-row columns the rulings promised and 11-i-a did not ship (R-C's `batch`, R-G's two version columns, F6's queryable axis fields on ROWS, telemetry/sensitivity/results columns). Rec: assign to b explicitly as B4 `OVERWRITE` additions, list attached. Cost of silence: b's builder discovers by SCHEMAFULL refusal mid-build — the C-DEF trap.
  5. **RAISED-6** — close the `trigger` column's vocabulary (exact-set, `("manual",)` in 11-i) before two writers invent spellings.
- receipt pointers: Q1 §1 · Q2 §2 (pin table §2.3) · Q3 §3 (shipped-tree inventory §3.1) · Q4 §4 (wrong-build table §4.3) · Q5 §5 (battery text §5.4, obligation map §5.6) · Q6 §6 (seam table §6.1) · RAISED §7 · tool honesty §0

---

## 0. Context held, provenance, tool honesty

Read IN FULL this sitting (worktree @ `2bf7631` unless stamped): the packet file `11-i-floor-calibration-dark-machinery.md` · the ruled design R1–R8 + Addenda A–E (all 1185 lines) · Addendum F-r2 §R1–R10 complete (including the same-day corrections §R8/§R9/§R10) · Addendum F's F1–F9 + the F8 adjudication table · my predecessor's full report (`receipts/2026-07-26-packet11i-fixwave/REPORT-fable-design-11i-b.md`, all 518 lines, FU1–FU5 included) · `RULINGS-2026-07-25.md` · `STATE-2026-07-25.md` · `CLIENT-CONSULT-SYNTHESIS.md` · `CONTRACT-FREEZE-DECISIONS.md` §0/§B/§C5–C7/§E · all three `RULINGS-2026-07-26-*.md` · `REPORT-contract-11ia-1.md` · `REPORT-builder-11ia-1.md` · `REPORT-coldaudit-11ia-1.md` · `REPORT-probe-bootstrap-paired.md` §D/§E · `2026-07-06-client-needs-consult.md` (method + synthesis + closure rounds) · INDEX row 11-i + Log tail.

**Tool honesty:** lore's index watches the MAIN checkout (`feat/surreal-unification`) — byte-identical to my briefed base for unedited files but blind to this worktree's own commits (#125). **Every in-tree claim below is grep/Read in THIS worktree, said out loud as the sanctioned fallback.** No lore calls were made; no store access; no network. Symbols cited, never line numbers. First-hand re-verifications this sitting: `FLOOR_STATES` (8, incl. `invalidated_remeasuring`) and `FLOOR_NON_ADOPTION_CAUSES` (5, incl. `interval_degenerate` / **`substrate_indiscriminate`**) in `store/surreal_schema.py` · `FLOOR_MEASUREMENT_COLUMNS` = 14 names · `head_identity` REQUIRED on `floor_measurement` (O7 landed; the docstring carries the trade) · `_COSINE_WEAK_MATCH_FLOOR: float | None = None` in `search.py` · `choose_cosine_floor` still lives in `scripts/search_score_survey.py` · zero production importers of `FloorCalibrationStore`/`SurrealLeaseStore`/`SurrealLeaderLock`/`enumerate_calibration_pool`/`lease_election_config` outside the slice (cold-audit R2 reproduced by grep) · `kubernetes.leaderelection.leaderelection.try_acquire_or_renew` exists in the installed venv · `loremaster/stats.py` exists with `QUANTILE_METHOD = "inverted_cdf"` and the #237 convention-discriminating fixtures in `test_stats.py` · store reference: *"Undeclared top-level keys on a SCHEMAFULL table RAISE in 3.x"* (§ probed row).

Tags: **[design-cited]** (ruled R/B/C/D/E/F/§ citation) · **[source-verified]** (read in THIS tree, symbol named) · **[my judgement]**.

---

## 1. Q1 — Does 11-i-b split again? RECOMMEND: KEEP WHOLE, with the contingency seam pre-named

**Recommendation: no split.** Grounds:

1. **The number is under the line.** ~0.24 ± 0.03 [design-cited F-r2 §R9.5, superseding the 0.29]; even the +1σ edge (0.27) clears the ≥0.30 clause. What has moved since R9.5, both directions [my judgement, assembled from the ruled record]: **added to b** — the R-A..R-H seam-pin obligations (largely inside R9.5's "pin suite ~0.05" already), E4's ladder generator [design-cited RULINGS-contract-11ia E4], the E6 pool-column extension + its two inherited hazards, and (if RAISED-1 rules my way) the remaining row columns; **removed from b** — the #198/#237 percentile home and its convention pins ALREADY SHIPPED (`loremaster/stats.py` + `test_stats.py` [source-verified]), and the interface freeze is now real shipped code b cites rather than a document b hopes about. Net: roughly a wash. ⚠ ASSUMED pending the scout's re-check — the scout owns the derived number; this section prices the DECISION, not the count.

2. **A split buys no parallelism here.** The R2 verb consumes the runner; the halves are strictly sequential. The a/b split's payoff was *independently landable and independently auditable* [design-cited packet Mission]; a b1/b2 split delivers only the second half of that payoff while paying full packet overhead — and 11-i-a just measured that overhead: contract → adversary (INSUFFICIENT) → fix wave → build → closure → cold audit → audit-fix, seven stages for the ~0.15 half.

3. **The split's real payoff is buyable at audit time for free** [my judgement, the load-bearing point]. b has two auditable characters: (i) **offline statistics + pins** — port, roc-path, bootstrap seam, oracle/convention/determinism-leg-A pins: auditable with ZERO store access, pure arithmetic-vs-oracle; (ii) **live instrument + R2** — captures, hold-out legs, the verb against production `:18500`, the evidence package: an I/O-provenance-safety audit. Brief the COLD AUDIT as two legs with those two characters, and the auditability payoff of a split arrives without a second packet cycle.

**If it must split** (scout lands >0.30): the ruled D7 sub-split line ("pool+bootstrap+gate" vs "paired-decomposition+cost-capture") is DEAD — its second half shrank to ~0.03 under #201 [design-cited R9.5's item shrinkage] and a 0.03 packet is bureaucracy. The honest seam is now the **store boundary**: **b1 = the offline core** (port + roc production path + bootstrap seam + oracle/convention/determinism-leg-A pin suite; no store, no embeds, landable and auditable alone) / **b2 = the live instrument** (probes, captures, hold-out, the R2 verb, evidence package, determinism leg B). Same character rule as the a/b split, and b1 carries no production risk at all. State plainly: b2 still waits on b1, so this costs a full second cycle — which is why it is the contingency, not the recommendation.

---

## 2. Q2 — The library cutover: what b actually BUILDS

### 2.1 The entry points b drives (all ruled; none is a choice left to a builder)

| library call | role | ruling |
|---|---|---|
| `sklearn.metrics.roc_curve(y_true, y_score, drop_intermediate=False)` over NEGATED non-anchored cosines, absent=1 | the PRODUCTION selection sweep — the +∞-prepended row read as strict-`<` counts at index j, rates rescaled to full-set denominators, candidates restricted to distinct union cosines, dominance = masked-array ops | decisions 19 + 20 RULED (ADOPT · THE ORACLE) [design-cited RULINGS-2026-07-25 §2; F-r2 §R9.1/§R9.3] |
| `scipy.stats.bootstrap(data=(paired_idx, identifier_idx), statistic=…, paired=False, vectorized=False, method="percentile", confidence_level=0.90, n_resamples≥1000, batch=<pinned>, rng=<Generator>)` | the interval shell — two 1-D integer index samples; the statistic gathers both legs of group 1's drawn indices | R-A/R-B/R-C RULED [design-cited RULINGS-bootstrap] |
| `np.percentile(result.bootstrap_distribution, [5, 95], method="inverted_cdf")` — **routed through `loremaster.stats`**, never a raw literal at the floor seam | the served interval (never `result.confidence_interval` — scipy's is `linear`) | R-D RULED; ONE-IMPLEMENTATION: `loremaster/stats.py::QUANTILE_METHOD` is the repo's single convention home [source-verified], and a second `method=` literal in floor code is convention copy #2 |
| `numpy.random.default_rng(seed)` — ONE explicitly-passed Generator, seed derived per-(scope, leg, N) | all resampling randomness; module-level `random.*`/`np.random.*` pinned out | F8-C1 as restated library-neutral [design-cited F-r2 §R1 C1 row] |
| `kubernetes.leaderelection` — `try_acquire_or_renew()`, single attempt | §3's verb single-flight | E3 RULED [design-cited RULINGS-contract-11ia E3] |

### 2.2 The equality control AS A SHIPPED PIN — a probe proves it once, this proves it forever

The R9 probe (20/20 exact equality, 44/75 differently-broken control) was a one-off in an ephemeral env. The shipped form, three pins:

1. **The oracle-equality property pin.** `choose_cosine_floor` — ported into `loremaster` as the executable spec / test ORACLE (decision 20) — versus the roc-derived production path: on EVERY suite run, over randomized fixtures from a seeded Generator (fixture N ≥ 200 per F8-C1; fixtures must include duplicate cosines, anchors on BOTH arms, and dominance tie-breaks — R9.1's fixture recipe), assert **exact equality of the full selection triple** (floor, false-fire, catch) by `==` on float64, never approx. Legitimate because the computation is counting-and-selection, no float accumulation [design-cited §R3.2].
2. **The differently-broken control leg, shipped INSIDE the test.** A deliberately mis-mapped evaluator — the naive un-shifted index mapping — asserted to DISAGREE with the oracle on the same fixtures. Without it, N/N agreement is unverifiable as non-vacuous (the C1 probe-control law). It lives as a local function in the test file, never in production — a shipped wrong twin would be a defect generator.
3. **The convention pin at the interval seam** — `inverted_cdf` on `.bootstrap_distribution`, **with a continuous-statistic leg** (the discrete floor statistic makes the two conventions coincide on 24/25 corpora; a discrete-only fixture waves the wrong build through) [design-cited R-D rider; probe-paired §C.5]. Routing through `loremaster.stats` means #237's convention-discriminating fixtures [source-verified: `test_stats.py`] already guard the home; b's marginal pin is that the FLOOR seam actually calls it.

**Builder mutation-proof obligations** (declared-set discipline, `scripts/mutation_proof.py`): shift the roc index mapping by one → pin 1 RED · swap `inverted_cdf`→`linear` at the seam → pin 3's continuous leg RED · swap `rng=`→`random_state=` → D.5's AST pin RED.

Plus the rest of the ruled seam-pin catalogue, cited not re-transcribed: **D.1–D.10 of `REPORT-probe-bootstrap-paired.md` §D** — call shape, **pairing-mechanism-not-outcome** (D.2: instrument what the statistic RECEIVED; the CI-endpoint pin is measured non-discriminating on 21/30 corpora), identifier-arm-present, no-2-D-samples, the `rng=` deny-by-default AST allowlist (exactly ONE function may call `scipy.stats.bootstrap`), determinism-on-bytes with its failing control, explicit-parameter assertion, `batch` recorded, boundary fates forced 0/1/2-per-group → `insufficient_corpus`, never a raw scipy `ValueError`.

### 2.3 What stays hand-rolled after the sweep — each survivor justified under the two-sided rule

| survivor | why the package does not do the job |
|---|---|
| `choose_cosine_floor` (oracle) | RETAINED BY RULING (decision 20) as the equality pin's other leg — deleting it deletes the control. Not on the hot path. |
| `_cosine_absence_predicate` / `_has_verbatim_identifier_anchor` / `_query_tokens` / the D2 bars | domain POLICY, identity-pinned with production (`is`-pins carry verbatim) — no library ships lore's absence predicate |
| probe-text derivation (docstring/heading rules) + hold-out source-file exclusion + k′/C9 logic | domain semantics of the instrument |
| the hash-stable sampler | stdlib `hashlib`/`uuid` ARE the library [design-cited R10.6] |
| the ladder generator (`[50,100,200,400…]` truncated, final rung = pool size) | five lines of ruled domain arithmetic (E4 assigned to b) |
| F2's calibrated bound, the ≥98% gate flip-counts, the R2.5 sensitivity floor, D4's paired decomposition | boolean/array glue over numpy primitives — "no new machinery" is the ruled verdict [design-cited §R9.2] |
| capture pipeline, jsonl/report writers, `VerdictSample`/`HitCapture` shapes, `parse_eval_questions`, the C6 writer | I/O and deliverable shapes, not statistics |

The one to WATCH [my judgement]: the dominance ordering as masked-array ops sits nearest the statistics — the oracle-equality pin is precisely the instrument that keeps it honest, which is one more reason pin 1 runs on every suite run, not once. Retired outright at the port: `every_nth` (D2), the survey's private percentile/mean/median arithmetic (dissolves into `loremaster.stats`/np one-liners per #198/#201 — the scripts-side copies retire with the port; `scripts/` is not in the image, so nothing served is touched).

---

## 3. Q3 — The lease: what 11-i-a actually left, and what b consumes

### 3.1 The shipped tree, determined [source-verified at `2bf7631` unless noted]

- **The whole lease stack EXISTS, is merged, and rides the deployed `e91e37b9` image unserved**: `store/lease.py` ships `SurrealLeaseStore` (conventional `_query` seam), `SurrealLeaderLock` (the six library members + `fence_epoch`/`release_if_held`/`stop`), `lease_election_config`, and the L2 tunables **15/10/2 (operator-confirmed upstream defaults)**.
- **The `kubernetes` dependency is TAKEN and shipped** (decision 22 executed in 11-i-a; `try_acquire_or_renew` present in the installed venv). **b adds NO dependency under any option — the question is moot at the workspace level.**
- **`FloorCalibrationStore.record_measurement(fence=None)` is legal and documented as "the single-process lab path"** — its own docstring [source-verified]. A fenced commit carries the guard INSIDE the transaction; `FenceLostError` is classified from store STATE with all three fates pinned.
- **ZERO production consumers** of any of it (cold-audit R2, reproduced by grep this sitting): neither `ensure_ready()` is on any boot path. **Ruled consequence for b: the verb must call BOTH `ensure_ready()`s before first use** — an undeclared `lease` table READ **RAISES** on 3.2.1 [design-cited ruling O3 + builder probe P8], and undeclared-table concurrent first-writes storm (§5/#144).
- **NOT built, by ruling:** the election thread, renew loop, `MaintenanceLoop` — R5 layer 2 is 11-ii B7.3. `run()` blocks forever with no stop mechanism [design-cited contract §4(d)]; nothing in b may drive it.

### 3.2 The answer, plainly

**b needs no election machinery and no new dependency. What b's one-shot verb consumes:** `enumerate_calibration_pool` · `FloorCalibrationStore.{ensure_ready, record_measurement, read_adopted_head, measurement_history}` · `SurrealLeaseStore.ensure_ready` · `lease_election_config` + **ONE `try_acquire_or_renew()`** at verb start · the fence snapshot into `record_measurement(fence=…)` · `release_if_held()` in `finally`. Nothing else.

**Recommended shape (L-1): single-attempt acquire, fenced commit, release in finally — no renewal thread.** This is a DERIVATION, not a preference: E3's ruling text says the contract drives `try_acquire_or_renew()` *"and 11-i-b's one-shot verb depends on it"*; R2.4/R10.4 make the R2 verb the lease's FIRST consumer by design [design-cited]; and the shipped `fence=None` docstring reserves unfenced for "no lease held" — a verb that acquires and then commits unfenced would contradict the shipped teaching. On a lost race (`False`): **REFUSE to run, loudly** — "lease held; another measurement in flight" — never retry, never block (R2.2's ruled ACQUIRE discipline verbatim). The library callbacks are wired via `lease_election_config` as no-ops for the one-shot: `try_acquire_or_renew` performs the CAS only; callbacks fire only from `run()`, which b never calls. ⚠ One named builder verification (not designable blind from this seat): that a lone `try_acquire_or_renew()` success populates `SurrealLeaderLock.fence_epoch` via the adapter's observed state — the contract's adapter pins exercise it under the real algorithm, so this is a read-the-pin check, not new design.

**The disclosed property, stated where it will bite [my judgement — this is the honest cost of L-1 and it must go in the verb's docstring and receipt]:** with `lease_duration=15s` and no renewal, a run longer than 15s holds a LAPSED-but-unseized lease. Unseized ⇒ fence intact ⇒ the commit LANDS (the fence checks holder+epoch, not freshness) — correct. But a second verb started mid-run CAN acquire after 15s; the first run's final commit then fails its fence and the ENTIRE run's row is discarded as a lost race (jsonl evidence files survive on disk; only the store write is refused). That is R10's semantics working as designed — economy degraded, correctness intact, and the discard is LOUD (`FenceLostError`). The alternative — an in-verb renewal heartbeat — would hand-roll the exact loop R10.6 says dissolved INTO the library, and drags 11-ii's `MaintenanceLoop` into b: machinery ahead of need. If the operator prefers zero-discard over the 15s start-guard, that is the unfenced/no-lease reading — an AMENDMENT to E3/R2.4's expectation, so it needs a ruling; my recommendation stays L-1.

---

## 4. Q4 — The determinism control (E5's MUST-PROVE pin), exact shape

### 4.1 Two legs BY CONSTRUCTION — because the only honest nondeterminism source is the embedder

**Leg A — arithmetic determinism (a suite pin; unconditional; the E5 fallback NEVER applies to it).**
- *Held fixed:* a fixture capture set (persisted cosines + anchor flags; N ≥ 200; includes a continuous-statistic sibling per the R-D rider), the config tuple (bars, ladder, B, k′), the per-(scope,leg,N) seed derivation, library versions (whatever the venv has — recorded).
- *Compared:* the ENTIRE derived output — selection triple, `ci_low`/`ci_high`, ladder `(N, ci_width, agreement)` triples, F2 null-rate + applied gap, sensitivity floor, degeneracy telemetry, paired decomposition — as **identical float64 BYTES** (`.tobytes()`-grade, never `repr`, never approx), across two in-process runs AND one subprocess run (hash-seed independence). This is probe-paired **D.6 widened from the CI pair to the full derived row**.
- *Passing:* byte equality on every field. *Failing control (what makes it a pin):* reusing ONE Generator object across the two runs must NOT be bit-identical [design-cited D.6's control].
- A RED here is a REAL DEFECT (seed plumbing, set/dict iteration order) — TEI is not in this leg, so the packet file's fallback clause may not be invoked for it.

**Leg B — end-to-end reproduction (the R2 receipt: the verb run TWICE on the live corpus).**
- *Pre-conditions asserted, not assumed:* both runs' settled-index start/end checks pass; `corpus_content_digest` AND `embedding_schema_fingerprint` identical across the two runs; **two DISTINCT measurement rows were created** (ids and `created_at` differ) — the anti-vacuity clause (see wrong-build 3).
- *Compared:* the two rows' full derived payloads, byte-wise, same field set as leg A.
- *Verdict, typed — never prose* (prose-derives-from-behaviour law): a closed enum recorded in the run receipt:
  - `bit_identical_cold` — byte-equal with zero probe-embed cache hits (the cache is E4-contingent and does not exist in 11-i unless R2's measured cost demands it);
  - `bit_identical_via_cache` — byte-equal but the second run re-used cached embeddings for >0 probes: this is leg A wearing leg B's clothes and MUST NOT be reported as embedder determinism;
  - `within_ci_by_construction` — bytes differ; then BOTH of these must hold or the run is `measurement_failed` + finding: (i) the two runs are NOT disjoint under the F2-calibrated adoption test (fresh-vs-fresh: no adoption would fire — no flap), and (ii) decision-agreement between the two floors over the L1 R-PACKAGE gate population meets the gate bar. Per-field deltas recorded beside the verdict.
- **Recording WHICH leg held is the packet file's own ban on unqualified "deterministic", made a typed field instead of a sentence** — with cache-hit counts, TEI endpoint identity, and `scipy/numpy` versions beside it.

### 4.2 Where the pin LIVES (predecessor Q4.2 carried; restated because both contracts must say it)

Leg A is a b-suite pin. Leg B is an R2-receipt obligation of the VERB (11-i has no scheduler — D3's exact-skip lands in 11-ii and RESTS on this pin; the receipt is what 11-ii's entry check cites).

### 4.3 "What WRONG build would still pass this pin?" — asked of my own answer

| wrong build | why it would pass a weaker pin | what kills it here |
|---|---|---|
| compares only the floor POINT | a discrete order statistic collides across runs while the distribution moved | full-field byte comparison |
| leg B warmed by the E4 cache | byte-equal via cached embeds; TEI never measured; 11-ii's exact-skip inherits an unverified assumption that detonates on first cache miss | the typed three-value verdict — `via_cache` is a DIFFERENT claim, and cache hits are counted in the receipt |
| "reproduces" by skipping | an exact-skip in the verb returns the prior row; run 2 is a read | the verb ships NO skip (scheduler is 11-ii) + the two-distinct-rows pre-condition |
| trivial fixture | small-N quantization makes seeded and unseeded coincide (measured 20/20 identical unseeded at N=50) | fixture N ≥ 200 + the failing Generator-reuse control + the continuous leg |
| compares formatted text | two different float64s print equal at 6 places | BYTES, stated as bytes |
| a pin that exists but never runs | `testpaths`-orphaned guard — a hope with a filename | b's contract lists leg A's node id in its gate set; leg B's verdict field is REQUIRED in the receipt schema, so its absence is loud |

**Builder mutation proofs:** perturb one fixture cosine between leg A's "two runs" → RED (proves the comparison reads the data) · alter the seed-derivation string → RED · reorder two captures (same multiset) → must stay GREEN if and only if the pipeline is genuinely order-independent — if it goes RED, that is a real ordering dependency DISCOVERED, which is the pin earning its keep either way.

---

## 5. Q5 — THE CONSUMER CONSULT (the operator's explicit ask)

### 5.1 Scope: what b decides NOW that binds model consumers — and what is CUT as theatre

**Already ruled or already recorded — re-asking changes nothing, so these are CUT, with citations:** the served-state projection (~3 states — 2026-07-25 consult §2) · CI refusal / margin pair / inline delivery / silence-beats-hedge (consult §1, unanimous) · the two-degeneracy split (decision 4 RULED; enum shipped [source-verified]) · typed-cause-fields (shipped; O7 landed) · the F3 WORDING consult (ruled to run AFTER 11-i on R2's real divergence — C3; asking now judges blind on the one measurement that matters) · state NAMES (rename-sweep-cheap; rides F3 per predecessor Q5.3).

**Genuinely open, decided IN b, consumed BY models:**
- **(a) the row's remaining recordables** — b adds the outstanding columns (RAISED-1 list); the consult's audit question tests whether any consumer-needed datum is still unrecorded while the additive valve is cheap. After 11-ii arms the surface, an unrecorded distinction is foreclosed — my predecessor's hinge law.
- **(b) the C6 evidence package's SHAPE** — what the summary artifact states vs what stays in jsonl; where the honest-bounds sentences sit; how F_legacy↔F_portable divergence is presented. Its consumers are ALL models: the F3 informants, 11-ii's contract author, future auditors.
- **(c) the verb's provenance receipt** — field set and rendering (LORE_VERSION, image digest, explicit coordinates, corpus fingerprint, the §4 determinism verdict, cache accounting, `--max-embeds` accounting).

### 5.2 Method: where I follow `2026-07-06-client-needs-consult.md`, and two deviations with reasons

**Followed:** three blind informants (Sonnet 5, Opus, Fable), independence rule (no consult docs, no sibling reports), a synthesis pass whose convergences become design law, mandatory contamination disclosure, findings mapped to design consequences or explicitly discarded.

**Deviation 1 — task-grounded probes over pure introspection.** The informants perform a STAGED READING TASK against the exhibit package (keyed questions with known answers, §5.4) before any opinion question. Reason: the method doc's own strongest sections were probe-grounded, and brief-base §5's measured law is that introspection about mechanics is unreliable — behavior under a real task is the receipt. The 2026-07-25 consult was pure introspection and worked, but its questions were PREFERENCE questions; ours are USABILITY questions, which have behavioral ground truth.

**Deviation 2 — a control leg, because a probe needs a control [design-cited CLAUDE.md]:** one additional informant run receives a deliberately DEGRADED package variant (§5.5). The 2026-07-06 method had no control; without one, a unanimous CALL_AGAIN cannot be distinguished from informants who accept anything.

**Contamination, disclosed in the design rather than discovered later:** CLAUDE.md (auto-loaded, unavoidable) legislates receipts and reports extensively — summary blocks, receipt pointers, dated claims. Any informant OPINION about "what a receipt should contain" is seeded by construction, and worse than the 2026-07-25 case because the subject matter overlaps the contamination directly. Mitigation: the keyed-task grades and the routing decision are BEHAVIORAL (contamination-resistant); the synthesis marks opinion findings that coincide with CLAUDE.md doctrine as corroborated-but-contaminated, exactly the §0 discipline of the prior synthesis.

### 5.3 Exhibits — all must be SYNTHESIZED, and what an honest synthetic exhibit may and may not do

R2 has not run; no real package exists, and the packet's own law says R2's numbers are never synthesised in advance. An honest exhibit therefore:
- **MAY** use the REAL shapes: field names from the shipped schema [source-verified: `FLOOR_MEASUREMENT_COLUMNS` + the RAISED-1 additions], the ruled C6 (a)–(f) artifact list, the real state/cause enums, real probe-text EXAMPLES (C6(d)'s side-by-side is derivable today from the corpus deterministically — the ONE exhibit component that can be real).
- **MUST** carry a top banner on every page: *"SYNTHETIC EXHIBIT — no value in this document is a measurement"*, AND use arithmetically COHERENT but magnitude-implausible values (floors like `0.123456`, n's that sum) — coherent so the keyed tasks are answerable, implausible so no value can be quoted as real. A plausible fake floor WILL escape into circulation; that is the #152/#154 class and the reason plausible values are banned, not just labeled.
- **MUST NOT** state or imply a measured divergence, bias direction, or cost — the honest-bounds LINES are exhibited (their placement is exactly what is under test), their numeric content is sentinel.

### 5.4 The battery — exact question text, per informant

Each informant receives: the synthetic package + this sheet. Parts 1→4 in order; Part 4 asked LAST [design-cited §C5/E3 grammar].

**Part 1 — keyed retrieval (graded against known answers):**
1. *"Did the portable instrument pass its pre-registered acceptance? Name the two acceptance legs and their values."* (keyed: present in the summary)
2. *"Is the legacy↔portable divergence a scalar offset or a distribution-shape difference? Cite the exhibit line that told you."* (keyed: requires the per-group table (b), not the headline (a))
3. *"Which determinism leg held, and what does that commit 11-ii's exact-skip scheduler to?"* (keyed: the §4 typed verdict)
4. *"What was the self-retrieval drop rate, split by cause?"* (keyed: C9/C13 diagnostics)
5. **HONESTY KEY** — *"What fraction of live production queries would fire the absence verdict under the portable floor?"* The package CANNOT answer this (it measures the survey's query mix, not live traffic — C6(f) bound (i); packet 35 is the instrument). Correct answer: "not measured here, and the package says so at ⟨line⟩." A derived number = a failed key — and the FIX is the package's bound placement, not the informant.
**Part 2 — behavior introspection, labeled as such:** which artifacts did you open; what did you read fully vs skim; the single most useful line; what you would DELETE from the summary.
**Part 3 — the audit question:** *"Name any datum you needed that neither the summary nor the row-field list carries."*
**Part 4 — ROUTING PROBE, LAST:** *"You are 11-ii's contract author and must build against this measurement. CALL_AGAIN — consume this package as your evidence base — or ROUTE_AROUND — re-derive or demand a re-run? State why."* Keyed CALL_AGAIN on the honest variant. **A ROUTE_AROUND on the honestly-rendered variant is a FAILED ACCEPTANCE of the package design — fixed and re-run, never waived** [design-cited CLAUDE.md trust doctrine; standing law restated in my brief].

### 5.5 The control leg

One further run (a fourth informant, or one of the three on a later blinded pass) receives the DEGRADED variant: honest-bounds lines removed, acceptance legs stated as verdicts without values, determinism verdict as the bare word "deterministic". Expected: failed keys 3/5 and/or ROUTE_AROUND. **If the degraded variant also scores clean CALL_AGAIN, the battery does not discriminate and its acceptance verdict means nothing** — redesign before trusting it (the C1 probe-control law, applied to my own instrument).

### 5.6 What each answer OBLIGES b to change — the no-theatre map

| result | obligation |
|---|---|
| failed key 1–4 (couldn't find / misread) | the datum moves into the summary or gains a receipt pointer — C6 writer spec change |
| fabrication on key 5 | the honest-bounds sentence moves INSIDE the claim it bounds (Opus's survive-quotation law) — writer change |
| Part 2 convergent "delete X" | X leaves the summary, stays in jsonl — writer change |
| Part 3 names a datum | an additive `OVERWRITE` column or package field NOW (B4 valve), or an explicit ruled "will not record" with reason |
| Part 4 ROUTE_AROUND (honest variant) | failed acceptance → redesign → re-run battery |
| control leg fails to discriminate | battery redesigned before any verdict is trusted |
| everything green | the C6 spec freezes as exhibited — and the exhibit becomes the writer's golden fixture, so the shipped package cannot drift from the accepted shape |

**Timing and cost:** pre-contract (or during contract authoring) — the answers must be able to change the writer's spec, or the consult is theatre by my brief's own definition. ~4 informant runs + synthesis ≈ the 2026-07-25 consult's ~15-minute shape. Precedent that pre-build consults on experience-answerable questions work: the lead's 2026-07-25 run, and my predecessor's recorded correction of its own contrary advice (FU1).

---

## 6. Q6 — Where 11-i-b could touch a SERVED BYTE

### 6.1 The seams, enumerated, each with its disposition

| # | seam | risk | disposition / proof obligation |
|---|---|---|---|
| 1 | `loremaster/search.py` — the identity-pinned imports (`_cosine_absence_predicate`, `_has_verbatim_identifier_anchor`, `_query_tokens`, bars) | ANY edit is presumptively served: the E1 disarm note is byte-frozen, `_COSINE_WEAK_MATCH_FLOOR = None` is the deployed disarm [source-verified], templates live here | b IMPORTS, never edits, never relocates. A port that "needs" a symbol moved is a STOP-and-escalate |
| 2 | served model CLASS docstrings — anywhere b touches shared files | **measured trap: docstrings render verbatim into `lore_index`'s `outputSchema` — a "harmless docstring edit" IS a served byte** [design-cited §E] | b's writable set names the exact shared files (`store/surreal.py` for the pool constant); no served-model class may be edited; the existing render pins are the detector |
| 3 | the MCP tool surface | registering the verb as a tool changes `instructions` (`test_instructions_names_every_tool`) — a served byte; NOT registering an added tool is a Trust-Doctrine defect — both branches bad | RULED already: `python -m loremaster.<floor_module>`, never an MCP tool [design-cited §B/C7]. b's contract cites it |
| 4 | `lore_index`'s calibration block | it renders the drift-check/disarm state today; nothing reads the new tables | untouched — pure-read wiring is 11-ii (A1). The consumer-zero pin (below) is the instrument |
| 5 | `lore.yaml` config (`calibration.extra_answered_queries` hook, R1 mitigation (a)) | new config parsing/validation changes BOOT behavior on every deployment — served behavior | **recommend deferring the hook to 11-ii**: no R2 consumer needs it (lore's legacy sets live in-repo). If b takes it anyway, unknown-key/absent-key behavior must be byte-identical to today — flagged as a scope question, not silently decided |
| 6 | the production store `:18500` — DDL (`ensure_ready`), measurement rows, an adopted head, possibly a `measurement_failed` FINDING row | dark tables: no served surface reads them (consumer-zero). But a finding row is CONTENT on an EXISTING served surface (`lore_findings`) | sanctioned: the §B ruling authorizes the writes (post-cold-audit, explicit coordinates, no defaults); the finding rides the EXISTING findings pipeline whose render already has the hostile-fixture sanitiser — b writes no new render |
| 7 | `smoke_p8b` | render-shape-coupled — *"a builder editing smoke here is a tell that the boundary slipped"* [design-cited §E verbatim] | untouched; its edit appearing in b's diff is itself the alarm |
| 8 | the image / deploy | DEPLOY: no — `lore-lore` never receives b's code; the verb runs in an ephemeral container from a worktree-built image [design-cited §B] | the C7/decision-12 provenance riders (LORE_VERSION + image digest + fail-loud-on-null git identity + path-identical mount) are the receipt that the right artifact ran |

### 6.2 The proof obligation, and the cheapest sufficient instrument

Three instruments, all cheap, together sufficient [my judgement, argued]:
1. **The diff manifest (code half):** b's writable set structurally excludes every serving module; the close-out proof is `git diff --name-only <base>..<head>` ∩ {serving modules} = ∅ — one command. Where b MUST touch a shared file (`store/surreal.py`'s `CALIBRATION_POOL_COLUMNS`), the diff is reviewed hunk-by-hunk against the constant-and-projection seam only.
2. **The consumer-zero pin (seam half):** promote cold-audit R2's finding into a SUITE PIN — an AST scan asserting no production module outside `floor_calibration/`, `store/lease.py`, the schema module, and the verb's `__main__` imports the new surface. This is a deliberately dark-state pin with a **named delete trigger**: 11-ii's wiring deletes it in the same diff that adds the first consumer, so un-darking is a visible reviewed change, never drift (the pin-the-bound law, pointed at a state instead of a hole).
3. **The existing render/instructions pins (byte half):** any served-byte movement — instructions text, `outputSchema` docstrings, index render shape — already reddens standing pins (`test_instructions_names_every_tool`, the render seam pins, the exact-set registration pin). b does not rebuild these; it inherits them as the detector, and the packet close-out cites their green run AT b's HEAD as the served-byte receipt.

A deployed-image byte-diff is NOT needed: nothing deploys (`DEPLOY: no`), and instruments 1–3 cover the tree the next deploy will bake.

---

## 7. RAISED — everything noticed, none resolved silently

1. **Dropped/unassigned row-shape riders (decision-needed 4).** Ruling **R-C** says *"pin `batch=None` explicitly and RECORD it in the measurement row"*; ruling **R-G** says the row records `scipy.__version__`/`numpy.__version__` and calls itself *"an 11-i-a row-shape obligation"*, premised on *"the row already carries `B`, `N`, `method`"*. **The shipped row carries NONE of these** — `FLOOR_MEASUREMENT_COLUMNS` is 14 names with no `batch`, no versions, no `B`/`method`, no F7.2 degeneracy telemetry, no R2.5 sensitivity floor, no per-group results, no run cost, no C11 manifest [source-verified]. Contract §1.6's own description also promised the F7.2/R2.5 fields. Whether this was a deliberate fix-wave narrowing (E6-style "b's columns") or a dropped rider, **no ruling I can find assigns the remainder to b** — and THE RIDER IS PART OF THE RULING is this repo's named failure class. Failure direction if left: LOUD, not silent (SCHEMAFULL undeclared top-level keys RAISE on 3.x [source-verified: store reference probed row]) — but it fires MID-BUILD as a C-DEF trap between b's builder and a frozen schema. **Recommendation:** the lead rules one line — *"b owns the remaining measurement columns as B4 `OVERWRITE` additions"* — with the list: `batch`, `n_resamples`, `method`, `scipy_version`, `numpy_version`, `k_prime`, the bars tuple, gate triples, F2 null-rate + applied gap, sensitivity floor, `ci_distinct_candidate_values`/`ci_modal_mass`/`floor_rank`/`floor_tail_depth`, per-group results, run cost (embeds, wall-clock), the C9/C13 drop diagnostics, the C11 manifest (in-row ≤ the proposed 1 MB bound, side-table decision at R2 review), and per-payload-key **read-back pins** (write→read→present) so no key silently dies at a future schema edit.
2. **F6 ruled-text divergence:** F6/decision 5 say `statistic` and `scope` *"also travel as queryable FIELDS on rows and heads"*. Shipped: heads yes, **measurement rows no** — the row's only axis linkage is the one-way `head_identity` digest [source-verified]. Machine reads are fine (the ledger recomputes the digest from axes), but a never-adopted head has NO `floor_head` row (the mint is adoption-only), so a `measured_not_adopted` history row's axes are recoverable only by digest-matching over the known axis universe — O7's "unattributable forever" argument, half-reopened at the SELF-DESCRIPTION level. Cheap close: fold the two axis columns into RAISED-1's addition list (queryable, `option<>` on rows per §1.4). Needs a ruling only because it touches ruled text both ways.
3. **The brief's own vocabulary drift, so nobody greps for a ghost:** my spawn brief (and some fixwave-era prose) names the corpus-property degeneracy `corpus_indiscriminate`; the SHIPPED enum value is **`substrate_indiscriminate`** [source-verified]. Same concept, one spelling; all future citations should use the shipped name.
4. **#241 rides into b's R2 run:** the verb drives the same head mint against PRODUCTION under the shared 2.0 s conflict deadline; if the cold audit's mechanism hypothesis (store-wide slowdown → mass deadline exhaustion) is right, an R2 run during heavy store activity could see `TxnContentionExhaustedError` (which propagates untouched — correct). Cheap rider for b's verb receipt: record driver retry/exhaustion counters for the run, which is also the instrument #241's disposition wants.
5. **`LeaseError` stays dead surface after b** (builder E-5, cold-audit F6c: declared by the frozen interface, raised by nothing, zero test references). The Q3-recommended verb uses refusal semantics, not raises — so b will NOT become its raiser. Its named trigger (11-ii's election thread) or deletion needs an owner; flagging so 11-ii's brief inherits it deliberately.
6. **The `trigger` column is an open vocabulary** [source-verified: `option<string>`, no ASSERT]: 11-i has no trigger legs (scheduler is 11-ii), so b's manual run must write SOMETHING and nothing closes the spelling. Recommendation: close it exact-set now — `("manual",)` — extended by 11-ii when the legs arm; two writers inventing `"manual"`/`"lab"`/`"r2"` is the drift the closed-domain discipline exists to stop.
7. **Post-R2 instrument-version hygiene:** R2 writes an adopted head to production BEFORE anything serves it. If a defect in b's instrument is found after the run and before 11-ii, the head sits armed-in-waiting. Cheap close: 11-ii's entry check re-reads the adopted head's `instrument_version` against then-current and re-runs the verb on mismatch — one line in 11-ii's packet file (the lead's edit; outside my writable set).
8. **Q5's structural contamination bound is recorded in the design** (§5.2): a consult about receipts is CLAUDE.md-contaminated by construction; the battery's keyed/behavioral legs are the mitigation, and the synthesis must weight opinion-legs accordingly.
9. **Scout report absent at writing time** — §1's sizing paragraph marks its assumptions; if the scout's derived number contradicts ~0.24±0.03, §1's recommendation re-prices mechanically (the DECISION logic stands; the NUMBER is the scout's).

---

*Written 2026-07-28 at worktree `lore-pkt11i-b` HEAD `2bf7631` (branch `pkt11-i-b-floor-runner`). All in-tree claims verified at that commit; all ruled-text claims cited to their section. — `fable-design-11ib-2`*

---

## Follow-up 1 (2026-07-28, from `lead-11ib`) — sizing reconciled to ONE number; three scout finds adjudicated

Inputs this sitting: `REPORT-scout-11ib-1.md` read IN FULL (all 688 lines — its §G arithmetic, §B-6 gap table, §C.3 open items, §D hazard list, both retractions). New first-hand verifications: `SurrealStore.enumerate_calibration_pool`'s two refusal branches read at source (the `len(rows) == limit` → `CalibrationPoolTruncatedError` branch and its disclosed-trade comment) · `SurrealLeaderLock` bridges sync→async via `asyncio.run_coroutine_threadsafe(coroutine, self._loop).result(timeout=call_timeout_seconds)` [source-verified] · `FloorCalibrationStore._validate_domain` is a pre-I/O staticmethod and the shipped home of the cross-field state↔cause refusals [source-verified].

### FU1.1 — ONE sizing number, item-by-item adjudication — and my KEEP-WHOLE does not survive unconditionally

**Base: 0.25 accepted** — the scout re-derived §R9.5's own deltas and found the 0.01 rounding slip; I verified the subtraction (0.29 − 0.03 − 0.01 − 0.01 − 0.01 + 0.02 = 0.25). The six additions, adjudicated:

| # | scout's line | verdict | granted |
|---|---|---|---|
| 1 | D.1–D.10 pin suite **+0.03** | **REAL, HALF-DOUBLE-COUNTED.** §R9.5's own "determinism/equality pin suite ~0.05" already priced the oracle, convention, and determinism pins. Genuinely post-dating §R9.5: D.2's instrumented-statistic pairing pin (the CI-endpoint pin's non-discrimination is a 2026-07-26 measurement), D.5's AST allowlist seam, D.6's subprocess + failing-control legs, D.10's 3×2 boundary fates, D.3/D.4 | **+0.015** (0.01–0.02) |
| 2 | `floor_measurement` field gap **+0.03** | **REAL AS b-COST ONLY IF RAISED-1 ASSIGNS IT TO b.** The populate half was already inside §R9.5's runner/verb pricing; the schema half (OVERWRITE lines + migration legs + DDL-text pins + read-back pins) is cost TRANSFERRED across the a/b line, not invented — but from b's ledger it is new | **+0.025** (0.02–0.03) — see the carve-out below |
| 3 | election thread lifecycle **+0.02** | **DISSOLVED by my Q3-L-1, as the scout itself anticipated.** No thread, no renewal, no poison: the verb's single `try_acquire_or_renew()` runs off-loop via `await asyncio.to_thread(...)` — REQUIRED, not stylistic: the adapter's sync methods block on `run_coroutine_threadsafe(...).result(timeout)` [source-verified], so calling them from the loop's own thread deadlocks until the call timeout. One bridge call + the refusal path + its pin | **+0.005** |
| 4 | R2 vehicle mechanics **+0.02** | **HALF-DOUBLE-COUNTED** with §R9.5's 0.06 "R2 verb + C6 package" (the verb's code incl. C7's receipt was priced there); genuinely new: the decision-12 riders (fail-loud git identity, LORE_VERSION refuse) and image-build receipts — and part of the vehicle is lead-side wall-clock, not builder wu | **+0.01** (0.005–0.02) |
| 5 | R-E arity-4 **+0.005** | **REAL** (ruled 2026-07-26) | **+0.005** |
| 6 | `ensure_ready` both slices **+0.005** | **REAL** (O3 forbade the coupling; scout D-1) | **+0.005** |

**The one number: ~0.31, band 0.29–0.34** (0.25 + 0.015 + 0.025 + 0.005 + 0.01 + 0.005 + 0.005 = 0.315; the band's ends are the granted ranges, not the scout's raw 0.34 vs my optimism).

**Said plainly, per the lead's instruction: at ~0.31 the ≥0.30 clause fires at its letter, and my §1 KEEP-WHOLE — priced against ~0.24 — does not survive unconditionally.** The decision changes when the count does. But the adjudication also exposes the STRUCTURAL fix, which is better than either keep-or-split as posed:

> **Carve the a-owned residue out as a micro-wave, and b re-prices UNDER the line in its ruled character.** Line 2 (+0.025) plus FU1.2's classifier fix plus FU1.3's guard are ALL edits to a-owned files (`store/surreal_schema.py`, `store/surreal.py`, `floor_calibration/store.py`) under Q4.1's assignment rule — the work that crosses the ownership line is exactly the work that pushes b over the split line. Recommendation: a focused **"11-i-a-r" residue wave (~0.03–0.04)** — schema fields per the scout's §B-6 gap table, the FU1.2 recount classifier, the FU1.3 adopt-guard, the two frozen-fixture edits, each pre-authorized by value (the O2 precedent) — sequenced **a-r → b's contract → b's build** (the Q4.4-1 order constraint, one level down). b then re-prices to **~0.28–0.29**, stays whole, and stays what Q4.1 said it is: *"pure runner arithmetic, probes, and the R2 verb."* **This REVISES my own RAISED-1 recommendation** ("authorize b to extend `surreal_schema.py`") — the sizing evidence argues the other disposition, and I am revising rather than defending it.
> **If the operator declines the carve-out** and assigns the schema half to b: b ≈ 0.31, the clause fires, and the split seam is my §1 contingency (offline statistics + pins / live instrument + R2) — preferred over the scout's §G seam because the scout's b-2 puts bootstrap statistics AND the production run in one half, mixing the two audit characters again. Note §B's ruled sequencing (the R2 run happens only AFTER the cold audit) already gives the run-phase isolation cheaply in either branch.

### FU1.2 — the `counted_total + 1` growth trap: the reading is CORRECT, and the fix is E2's own pattern

**Verified at source, not relayed:** `enumerate_calibration_pool` raises `CalibrationPoolTruncatedError` ("`measurement_failed` territory") whenever `len(rows) == limit`, and `limit = counted_total + 1` — so **growth of ANY size between the count and the walk lands in the truncation branch** (grew by exactly 1 ⇒ full result at the limit; grew by ≥2 ⇒ genuinely cut at the limit; both read `len == limit`). Shrinkage lands in the gentler mismatch/requeue branch. The builder disclosed the trade in the shipped comment; the scout's §D-12 reading stands.

**Why it matters more than a disclosed trade [my judgement]:** on a LIVE instance (`:18500`, watcher indexing continuously) growth during an R2 run is ORDINARY, and the consequence is not just a lost run — it is a `measurement_failed` row plus a deduped FINDING on the production ledger attributing an instrument failure that never happened, on a served findings surface. That is a false incident of the class the F5 enum was built to prevent (C8's own ruling rationale: *"one type for both would file an incident for a corpus that merely moved"* — growth IS the corpus merely moving).

**Disposition recommendation — implement C8's INTENT with a sharper classifier; it amends C8's operational words, so it needs the lead's stamp, not a builder's tweak (the builder said exactly this):**
- On `len(rows) == limit`, do not classify from the ambiguous count — **RE-COUNT and classify from store state** (E2/`_fence_verdict`'s exact discipline, applied one table over): fresh count ≠ `counted_total` ⇒ the corpus moved ⇒ `CalibrationPoolCountMismatchError` (discard-requeue; the settled-index gate absorbs it, and the re-run's fresh count includes the growth). Fresh count == `counted_total` while the walk returned MORE than it ⇒ instrument-inconsistent ⇒ `CalibrationPoolTruncatedError` (`measurement_failed`, honestly earned). If the confirming re-count itself fails, that store error propagates AS ITSELF — never dressed as either verdict (E2's rider).
- **NOT a new non-adoption cause:** growth never reaches a measurement row — the run requeues before measuring. Do not widen the F5 enum for it.
- **Fixture consequences, named so the rider is not dropped:** the frozen truncation fixture (count monkeypatched to 5 against 12 rows) would now RE-COUNT 12 ≠ 5 and correctly route to requeue — so it must ALSO pin the re-count (mock both reads at 5) to stay a genuine instrument-bug fixture; and a NEW growth fixture (count 5, corpus grown to 7, re-count 7) pins the requeue path. Both discriminate; the ABA edge (grew then shrank back between count and re-count ⇒ classified Truncated) is a disclosed bound the run-end snapshot check backstops.
- **Hosting:** ONE classifier, store-side in `enumerate_calibration_pool` (two callers are coming — b's verb and 11-ii's loop; two call sites needing one policy is a function they call). a-owned file ⇒ folds into the FU1.1 carve-out wave.

### FU1.3 — `adopt=True` on a non-`measured` state: yes, the guard is needed, and it is a-owned

**Is there any legitimate adopt-on-non-`measured`? No — by construction.** Adoption is the bars-met outcome and bars-met IS `measured`; `measured_not_adopted` is non-adoption BY NAME; `measuring`/`measurement_failed`/`insufficient_corpus`/`invalidated_remeasuring` are non-outcomes or invalidations; `unmeasured`/`disabled` are not run results. So `adopt=True ∧ state ≠ "measured"` is always a caller bug — and the caller is b's runner, then 11-ii's loop. The failure it permits post-11-ii is a served floor whose adopted head names a row that measured nothing — the confident-wrong class the Trust Doctrine prices at session authority. Under the gate-threat-model law this is a door an HONEST runner bug walks through: close it.

**Home: `FloorCalibrationStore._validate_domain`** [source-verified: the shipped pre-I/O home of exactly this class — the state↔cause cross-field refusals live there, per E5's ruling and the `_require_non_empty_area_category` precedent; a store ASSERT cannot see `adopt` since it is a parameter, not a column]. One branch: `adopt=True` requires `state == "measured"`. Pins: force all four non-`measured`-adoptable fates with fixtures (adopt=True × {measuring, measured_not_adopted, insufficient_corpus, measurement_failed} → `ValueError`) plus the positive control (adopt=True + measured → lands), mutation-proven. The public `Raises:` enumeration gains the new fate in the same diff — that docstring has been wrong once already (cold-audit R4), and a refusal the consumer-facing surface does not name is a half-shipped guard.

**Does it belong in b? No — it is a `floor_calibration/store.py` edit, a-owned under Q4.1** ⇒ third passenger in the FU1.1 carve-out wave. The builder's hesitation ("an unpinned refusal risks a false gate for b's runner") is answered by ordering, not by omission: the guard + its pins land in a-r BEFORE b's contract freezes, so b's contract is written against the refusal rather than surprised by it.

### FU1.4 — the `via_cache` verdict, pushed: what forces COLD to ever run? Today, nothing. The pin:

**The wrong build, named:** the E4 cache lands (in b if R2's measured cost demands it, else 11-ii); every subsequent leg-B replicate run hits 100% cache; the verdict is forever `bit_identical_via_cache` — **true, typed, and empty**: embedder determinism is never measured again, while 11-ii's exact-skip rationale silently rests on a claim whose test can no longer fail. My Q4 three-valued verdict does not prevent this; the lead's push is correct.

**The fix — treat the cold-determinism answer EXACTLY as the floor treats its own validity: as a measurement with a fingerprint-scoped citation** [my judgement, and it reuses the design's own leg-1 logic rather than inventing a scheduler]:

1. **The receipt-schema constraint (the pin's core):** a leg-B verdict of `bit_identical_via_cache` is WRITABLE only when the receipt also carries a **cold citation** — `cold_verdict` + `cold_measured_at` + `cold_fingerprint` — and `cold_fingerprint` equals the run's current embedding-schema fingerprint (plus the TEI image digest where introspectable; where not, record `"unknown"` and the citation instead expires on a NAMED cadence — stated plainly as the weaker leg). A `via_cache` with no citation, or citing a retired fingerprint, is REFUSED at receipt-write — the run must run its cold arm first. This is the floor's own "measured in a retired space is not a measurement" invariant, applied to the instrument's claim about itself.
2. **The forced-cold arm:** the verb takes a cache-bypass mode for determinism replicates (bypass at READ for the run — never a cache wipe). Its cheapness is structural: the D5 cache key includes the embedder fingerprint, so **every fingerprint change makes the next run cold by construction** — the citation scheme only has to force cold at cache BIRTH and on the TEI-image axis the fingerprint does not cover.
3. **Coverage as a CHECKED variable, because a bypass flag can lie:** the cold arm's receipt records `cache_hits == 0` **counted at the cache seam itself** (the cache instruments its own reads), never asserted from the caller's belief — a "cold" run that silently read cache is `via_cache` in disguise, and the counter is what makes that loud. (The runtime-gate-reach law, applied to my own pin.)
4. **Fixtures, four fates forced:** cold run → `bit_identical_cold` accepted · cached run + valid citation → `via_cache` accepted · cached run + NO citation → refused · cached run + stale-fingerprint citation → refused. Mutation proof: break the fingerprint comparison and watch the stale-citation fixture go green → declared RED.
5. **Ships NOW, armed later:** in 11-i every run is cold by construction (no cache exists), so the pin costs fixtures only — but the E4 cache is RULED to arrive, and "ship the instrument in the same breath as the law" is exactly the rule this repo keeps re-learning. If b builds the cache under R2's measured cost, the pin is already standing.

**Asked once more of the fixed pin (the recursive discipline):** the residual wrong build is a TEI stack change that alters batching without moving the embedding-schema fingerprint AND without a readable image digest — the `"unknown"`-digest cadence leg is the honest bound covering it, and it is named as weaker rather than papered over.

*Appended 2026-07-28 at worktree HEAD `2bf7631`; all new claims verified at that commit. — `fable-design-11ib-2`*

## STANDING BY

Follow-ups via SendMessage; answers will be APPENDED here as stamped sections. — `fable-design-11ib-2`, 2026-07-28
