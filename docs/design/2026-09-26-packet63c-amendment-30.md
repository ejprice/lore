# Packet 63c — ruling amendment 30 (sidecar-63c-2, 2026-09-26): FK-a28-1 — the measured precondition counts are TYPED fields; the reason text is derived from them

Rules `REPORT-contract-63c-i-a-a28.md` §F FK-a28-1. Amends amendment-28 addendum A4 ("served / receipt
fields" — under-specified; my sentence). Read-only (lore client still down).

## Ruling — Reading B, with the prose derived from the fields (one source)
- **Why B:** a count an agent ACTS on is typed, never parsed back out of prose — *"renders take typed
  applicability … never a name they compare"* (A DIAGNOSIS IS NOT AN INSTRUMENT). Reading A repeats the F-6
  defect one level up: numbers that exist only in a sentence cannot be asserted, perturbed (MP-E's legs) or
  consumed without re-parsing the sentence. The a19a precedent put counts in `reason` because no field
  existed; that is the gap, not the precedent.
- **Fields (one nested model, so `MigrateGovernedResult` grows by ONE optional field):**
  `MigrateGovernedResult.preconditions: MigratePreconditionCounts | None` — `None` when no precondition was
  evaluated (a leg that never reached one); the model:
  `unscoped_agents`, `owned_but_unscoped_agents`, `scoped_but_ownerless_agents`, `dangling_sender_messages`,
  `owned_but_unscoped_messages`, `scoped_but_ownerless_messages` — each `int | None`, `None` = NOT MEASURED
  on this run (amendment 22 §4's rule for every count), a number = measured. Names spell the population as
  the ruling names it; no abbreviations. The bounded id samples stay in `reason` (they are teaching, not a
  count an agent acts on) and are the ONLY integers `reason` may carry that are not in the fields.
- **`extra="forbid"` on the wire:** an ADDED optional field with a `None` default is a widening the model's
  own producers control; it breaks no consumer that reads by name. The "resilient construction seam"
  law holds: the model stays `extra="forbid"`; nothing loosens. `MigrateGovernedResult` is the `lore-adm`
  receipt, not an MCP render, so no served-surface pin is re-keyed — but the render pin below binds the
  text to the fields either way.
- **The reason text DOES restate the counts — DERIVED, never a second source:** ONE render function on the
  model (`MigratePreconditionCounts.describe()` or the existing refusal composer taking the model, not
  ints) produces every count clause in `reason` from the fields. **Pins:** (1) mutation — perturb one field
  on a constructed result → the `reason` clause moves, ∀ fields (parametrised over the model's own field
  names, derived by `model_fields`, never a hand-list); (2) every integer in `reason` after stripping the id
  samples is a value of some field (the F-1/F-2 admitted-set leg, now keyed on the fields instead of the
  fixture's arithmetic — which retires the birth-value guard's fragility for these clauses); (3) the MP-E
  perturbation legs read the fields.

## §W
| # | item | lands |
|---|---|---|
| 1 | `MigratePreconditionCounts` (6 optional ints) + `MigrateGovernedResult.preconditions`; the ONE describe function; pins (1)–(3) | this fix pass (a28 contract + builder) |
