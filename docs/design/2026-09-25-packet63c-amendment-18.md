# Packet 63c — ruling amendment 18 (sidecar-63c-2, 2026-09-25): FINDING N-1 — G5's `target()` loses the Nmixed kill

Amends amendment-16 §G5 (`fbd4c80`). Rules `REPORT-contract-63c-i-a-r4b-fix2.md` §FINDING N-1 (working tree).
Directive: `REPORT-lead-63c.md@f15990c`. Read/awk only (lore client still down).

## The DUAL I owed and did not run
Amendment 16 closed G5 with `target(len)` graded against the builds that SURVIVED the untargeted leg. Nobody
re-ran the builds the untargeted leg had KILLED. The fix2 author did, with sets declared before the run:
Nmixed (a SKIP-gate narrowing on names carrying both `-` and `_`) went from killed to `638 passed`; G4's kill
now rests on a thinner margin. Mechanism, measured: targeting spends the 200-example budget on the length
axis and thins every other (mixed 4 → 0, doubled 10 → 1, trailing 23 → 6). This is the removed-behaviour
law — *any diff that replaces code carries an inventory of what the old code did* — applied to a test edit
I ruled: the old sample killed Nmixed, and I replaced the sample without asking what it killed.

## Ruling — (b): an UNTARGETED TWIN beside the targeted leg; no delta
- The twin is the r4b-fix generated leg — the program `adversary-63c-i-a-r4b-fix` already graded — restored
  AST-equal (amendment-17's definition of verbatim) under a second test id. By construction it restores the
  exact pre-fix2 kill set, and the targeted leg keeps G5's gain (the cap). Two samples of one language,
  two budgets, one oracle. Cost: one test, ≈200 in-memory spy calls.
- **No delta:** the twin is previously graded code landing unchanged, not a new pin — the amendment-16/17
  reading. **Conditions, in the fix2 report:** (1) the AST-equivalence receipt of the twin against the leg as
  committed at `10a33ef`, with the positive controls; (2) Nmixed RED on the FULL suite (queued — a survivor
  is a survivor only there); (3) the regression table re-run over both legs, declared before the run, so the
  union kill set is measured, not inferred.
- **(a) rejected:** Nmixed is a NARROWING — a legal agent's attribution silently missing from a served
  line. A served-output loss is not boundable under the trust doctrine; the probabilistic-coverage sentence
  amendment 16 landed is a statement of reach, not a licence to lose a kill we already had. **(c) rejected:**
  a named `"a-_b"` witness is the enumeration shape, one axis at a time, the thing derivation replaced.
- Prose: the twin's docstring says why two samples exist (*"`target` thins the untargeted axes; this leg is
  the untargeted sample whose kills the targeted one measurably loses"*) so nobody folds them believing one
  covers the other.

## §E
- Erratum against amendment-16 §G5: graded on the survivors only; the removed-behaviour leg was owed and
  not run. The askable form, for any edit to a SAMPLING instrument: *"what did the OLD sample kill, and does
  the new one still kill it?"* — a sample is a fixture, and FIXTURES MUST DISCRIMINATE cuts both ways.
