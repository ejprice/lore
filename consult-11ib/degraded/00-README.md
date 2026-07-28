> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# R2 floor-calibration evidence package — contents

Nine artifacts. Every number in every artifact is a sentinel: arithmetically coherent with
every other number here, and drawn from a visibly artificial family so that no value can be
quoted anywhere as a lore measurement. R2 has not run.

| file | what it carries |
|---|---|
| `00-README.md` | this map |
| `01-summary.md` | both floors and the two pre-registered acceptance verdicts |
| `02-per-group-distributions.md` | response-best cosine distributions for the six measurement groups under both instruments, with per-percentile deltas |
| `per-query-rows.jsonl` | the per-query rows themselves (deterministic sample) |
| `03-anchor-rates.md` | verbatim-anchor rate per group |
| `04-probe-texts.md` | ten self-supervised probe texts beside ten human questions |
| `05-adopted-row-provenance.md` | the adopted measurement row's typed fields with values, and the two closed enums behind them |
| `06-per-hit-decomposition.md` | the per-hit cosine distribution and the over-flag decomposition |
| `07-determinism-and-run-receipt.md` | the determinism control's verdict, and the run's provenance receipt |
| `08-drop-diagnostics.md` | probe drops by cause, and the validity floors |

## How the sentinel values are built

- Every **independently chosen** real value is either an ascending digit run
  (`0.123456`, `0.234567`, `0.345678`, `0.456789`) or a two-digit repunit
  (`0.ababab` — e.g. `0.313131`, `0.696969`). Every independently chosen count is a
  strictly monotone digit run (`12`, `23`, `123`, `234`, `345`, `456`, `567`, `987`).
- Every **derived** value — a sum, a difference, a rate, a remainder — is the exact
  arithmetic consequence of its inputs, and therefore usually carries no signature at all.
  That is what coherence costs, and it is deliberate: the derived values are what let you
  audit this package against itself.
- Rates are always shown as `k / n` beside their decimal. The fraction is exact; the decimal
  is rounded to six places, so independently rounded components may miss their rounded total
  by one unit in the last place.
- Field names, the artifact list, the state enum and the non-adoption-cause enum are REAL —
  read from the shipped schema. Only the values are synthetic.
