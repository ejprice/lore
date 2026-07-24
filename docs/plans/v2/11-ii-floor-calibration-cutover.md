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
- Verdict grammar/wording — **ruled law, and F3 is the operator's fork.** If R2's lab
  validation (landed in 11-i) did NOT pass, the wording amendment goes BACK to the operator
  before this packet touches a served string. Do not decide it here.
- Reranker/utility-predictor confidence layers (packet 28 territory).

## Entry check
**FIRST READ: `docs/reference/surrealdb-31-capabilities.md`** (store-reading code; cite,
never re-transcribe).
- 11-i landed, its cold audit GO, and its measured floor + provenance on record.
- **F3's disposition known** — either the operator approved the conditional default and R2
  passed, or the amendment has been ruled. Do not start the serving swap without it.
- suite green at HEAD; spike-surreal up (**:18000 test store, never :18500**).

## Exit
TDD per repo law; hostile fixtures for any new render of stored text; contract-adversary;
cold audit. **Deploy BOTH containers.** Smoke: a non-lore corpus (the DI instance) measures
its own floor or renders its honest interim state — that smoke is #179's actual proof, and
it is the first time a foreign instance stops serving lore's constant.
**Resolution notes for #83 / #87 / #161 / #179 record that the MECHANISM closed each — never
a count.** #161's counts were a moving target by design; a count-match proves nothing.
INDEX row + Log.
