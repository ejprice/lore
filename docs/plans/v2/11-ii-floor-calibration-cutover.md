# 11-ii — Per-corpus floor calibration · CUTOVER (resolves #83, #87, #161, #179)
size ~0.15 wu · wave L · depends: **11-i landed** · **DEPLOY: yes (both containers)**
law: DESIGN-LAW §3, §5 (store idioms), §6, §12
split provenance: see `11-i-floor-calibration-dark-machinery.md` header. Size is the lead's
split of B8's ">0.30"; re-check at kickoff.

## Mission
Wire 11-i's dark machinery to the chokepoints and swap the serving surface onto it.
Executes B7 steps 3, 4 and 6 of the ruled design. **This is the packet where behaviour
changes** — every served weak-match judgement moves from a baked-in constant to the
instance's own measured floor.

## Binding architecture (operator ruling 2026-07-24 — do not re-open)
Container detects staleness, container fixes staleness, new floor stored in the DB. Full
ruling: `lore_recall("operator ruling cosine floor SurrealDB container")`. Design:
`docs/design/2026-07-24-floor-calibration.md` R1–R8 + Addenda A/B.

## Scope IN
- **Chokepoint wiring (B7.3, Addendum A1 + B1/B2):** evaluation at boot / post-sync /
  post-sweep / adoption; single-flight, coalescing, discard-and-requeue on a mid-run churn.
  **`lore_index` becomes a PURE READ of engine state.** ⚠ A1's load-bearing correction:
  `disarmed_by_drift` currently defaults False and is populated ONLY as a side effect of
  `AppContext._build_index_status`, so a process that never serves `lore_index` keeps the
  aggregate ARMED against a drifted floor — a fail-OPEN default. **Unevaluated ⇒ disarmed**
  is the required post-state.
- **Serving cutover (B7.4, R6/R7 + B6-F4):** the module constants retire as the serving
  source; verdict and per-hit gates read engine state at the serving seam; the §7 state
  table with its exact-set distinctness pin; #87's render fixes (R5 — always render
  shift-vs-tolerance; the runner stamps its own snapshot).
- **Retirement sweep (B7.6)** per repo rename law, and the resolution notes for
  #83 / #87 / #161 / #179.

## Scope OUT (surface to operator if encountered)
- Verdict grammar/wording — **ruled law, meaning NO UNILATERAL CHANGE.** F3 is a **CLIENT
  CONSULT**, not an operator fork: the models that consume the tool decide what serves them
  (operator ruling 2026-07-06, in `docs/design/2026-07-06-weak-match-discrimination.md`;
  method in `docs/design/2026-07-06-client-needs-consult.md`). **F3's client-consult outcome
  must be recorded (design doc §C3) before this packet touches a served string.** Do not
  decide it here, and do not route it to the operator — the operator sequences the consult,
  it does not render its verdict.
- Reranker/utility-predictor confidence layers (packet 28 territory).

## Entry check
**FIRST READ: `docs/reference/surrealdb-31-capabilities.md`** (store-reading code; cite,
never re-transcribe).
- 11-i landed, its cold audit GO, and its measured floor + provenance on record.
- **F3's client-consult outcome recorded** (design doc §C3). Do not start the serving swap
  without it.
- **#180 has a ruled fix.** The BASIS MISMATCH is independent of both the F3 wording consult
  and the R1 probe redesign: the floor is calibrated on best-of-response cosines
  (`max_cosine_of_response`) and served per-hit, so mid-list hits are judged against a
  population they cannot belong to. It must be fixed under ANY wording or provenance
  outcome. **A builder may NOT pick between the two candidate fixes** (calibrate a second
  per-hit floor, vs. move the per-hit surface onto a statistic the existing floor describes)
  — that is a design choice; it comes from the packet 10 designer or an operator ruling.
- suite green at HEAD; spike-surreal up (**:18000 test store, never :18500**).

## Exit
TDD per repo law; hostile fixtures for any new render of stored text; contract-adversary;
cold audit. **Deploy BOTH containers.** Smoke: a non-lore corpus (the DI instance) measures
its own floor or renders its honest interim state — that smoke is #179's actual proof, and
it is the first time a foreign instance stops serving lore's constant.
**Resolution notes for #83 / #87 / #161 / #179 record that the MECHANISM closed each — never
a count.** #161's counts were a moving target by design; a count-match proves nothing.
INDEX row + Log.
