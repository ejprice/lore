> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# 01 — Both floors, their selection receipts, and the pre-registered acceptance legs

*C6(a). Headline scalars only. The evidence behind them is in `02`, `03`, `06`, `08`.*

## The run

One dual-instrument run over one corpus snapshot. Both instruments captured response-best
cosines for every query in the run's query set; each instrument's own labeled sets drove its
own floor selection.

## The two floors

| | `F_legacy` | `F_portable` |
|---|---|---|
| selected floor | `0.345678` | `0.456789` |
| `ci_low` | `0.303030` | `0.404040` |
| `ci_high` | `0.393939` | `0.505050` |
| selection population | the legacy labeled sets | the portable instrument's six groups |

`F_portable − F_legacy = 0.111111`.

## Pre-registered acceptance

The bars were registered before the run. Both legs are judged on the ORIGINAL labeled sets,
with response-best cosines captured by the PORTABLE instrument.

| leg | verdict |
|---|---|
| **(1)** `F_portable` false-fire rate against the legacy labeled real union | **PASS** |
| **(2)** legacy nonsense catch at `F_portable` | **PASS** |

**Both legs pass ⇒ the portable instrument is ACCEPTED as built.** Nothing here ships on a
caveat: a failed leg would have returned the instrument to design, not qualified this page.

## Validity floors

| floor | required | this run | met |
|---|---|---|---|
| `MIN_ANSWERED_PROBES` | 30 | 411 = `answered_probes` (after drops — `08`) | ✓ |
| `MIN_IDENTIFIER_PROBES` | 15 | 15 | ✓ |
| `MIN_ABSENT_SAMPLES` | 30 | 533 (after drops — `08`) | ✓ |

## Outcome

State `measured`; the head was adopted. The adopted row is rendered field-by-field in `05`.
The determinism control's verdict is in `07` — read it before assuming a re-run reproduces
these numbers.
