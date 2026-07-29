# 44 — UNGATED GROUND: every committed instrument rides a gate
size ~0.15 wu · wave L (parallel-safe) · depends: none · DEPLOY: no (gates + tooling only)
law: repo CLAUDE.md (the `lorerunes` registration list — run `scripts/registration_sites.py`,
never read a list — and "a guard nobody runs is a hope with a filename") ·
packages-over-hand-rolling

**Provenance: MINTED by the operator-directed findings sweep of 2026-07-29** to home the
ungated-ground findings — the #188/#233/#238 second-class-tree class, recurring.
**OPERATOR-CONFIRMED 2026-07-29 (kept as-is, option 3 of the demote/fold/keep fork):** the
packet stands as a standing 0.15 row until a session picks it up. The load-bearing piece is
the DERIVED invariant (third Scope IN item) — without it this packet is instance-patch #5.

## Mission
Close the remaining trees that hold load-bearing committed code no gate covers. The class has
now bitten four ways (scripts/ untyped #188 · scripts/ ungraphed #233 · docs/eval untested
#238 · docs/eval untyped #261); each instance was found by an agent tripping over it, never by
a gate — which is the definition of the problem.

## Scope IN
- **#261** — `docs/eval` is ungated ground: the 5021-line deploy smoke that GATES PRODUCTION
  is outside `scripts/typecheck.sh`, outside lore's index, and root-mypy on it emits 7
  spurious errors so it cannot simply be added. Decide the strategy ONCE (its own typecheck
  leg with a scoped config · move the smoke under a member · a pinned, loud exclusion) —
  whichever wins, the smoke gets a type gate. (#238 already put its 190 tests in `testpaths`;
  this is the other half.)
- **#270** — the consult-battery tools hand-roll markdown table parsing while `markdown-it-py`
  is ALREADY a declared dev dependency, and they sit ungated at the repo root: adopt the
  package (packages law), and gate the tools under the SAME strategy decided for #261.
- **Sweep for siblings by DERIVATION, not by list**: any committed `.py` outside every
  typecheck member AND outside `testpaths` is a finding — `registration_sites.py`'s
  property-derivation is the model (an enumeration of places to look is the artifact this
  repo has the most receipts against). File what the sweep finds BEFORE fixing anything.

## Scope OUT (surface to operator if encountered)
- `lore.yaml` / lorerunes indexing (#260 — rides 04b-2's deploy). Any served-surface change.
- Restructuring where the smoke LIVES beyond what the #261 strategy demands.

## Entry check
`lore_findings` → #261 #270 unresolved. Run the derivation sweep FIRST — its count scopes the
packet; if it balloons past the sizing law, split before building (the law, not a suggestion).

## Exit
TDD where code changes; gates green (typecheck legs run in CI-shape, not just locally);
findings resolved with receipts; INDEX row + Log.
