> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# 01 — Both floors, their selection receipts, and the pre-registered acceptance legs

*C6(a). Headline scalars only. The evidence behind them is in `02`, `03`, `06`, `08`.*

## The run

One dual-instrument run over one corpus snapshot. Both instruments captured response-best
cosines for every query in the run's query set; each instrument's own labeled sets drove its
own floor selection.

**Measured population — read this before quoting anything below.** Every rate on this page is
computed over the SURVEY's query set (1740 queries across six groups, `02`). It is not a
sample of live production traffic, and nothing in this package supports a statement about
what fraction of live queries would fire the absence verdict. Packet 35 is the instrument
that would measure that; it has not run.

## The two floors

| | `F_legacy` | `F_portable` |
|---|---|---|
| selected floor | `0.345678` | `0.456789` |
| `ci_low` | `0.303030` | `0.404040` |
| `ci_high` | `0.393939` | `0.505050` |
| selection population | the legacy labeled sets | the portable instrument's six groups |

`F_portable − F_legacy = 0.111111`.

⚠ **That scalar is DIMENSIONLESS and it is not a quality delta.** The two floors are thresholds
in two different embedding geometries; the package carries an `embedding_schema_fingerprint` for
the portable instrument and none for the legacy one, so the two scales cannot be checked for
coincidence. It may not be re-expressed as an improvement, a regression or a percentage —
`02`'s bound (iii) states this in full, beside the tables it governs. What `02` does carry is
the per-percentile and per-group SHAPE of the paired difference, which this single number
averages away.

## `choose_cosine_floor` selection receipts

Counts are of queries whose response-best cosine fell **below** the floor, with the anchor gate
applied afterwards: the absence verdict fires on `max_cosine < floor AND NOT has_verbatim_anchor`.

**Legacy labeled real union** — the union of the two human groups (`human-prose` n = 123 +
`human-implementation-vocabulary` n = 234), **n = 357**:

| | below floor | of those, anchored (verdict suppressed) | false fires |
|---|---|---|---|
| at `F_legacy` = `0.345678`, legacy instrument | 5 | 2 | 3 → `3 / 357` = `0.008403` |
| at `F_portable` = `0.456789`, portable instrument | 23 | 12 | 11 → `11 / 357` = `0.030812` |

**Legacy labeled nonsense set** — the `legacy-nonsense` group, **n = 345**:

| | below floor | of those, anchored (verdict suppressed) | absence verdict fired (catch) |
|---|---|---|---|
| at `F_legacy` = `0.345678`, legacy instrument | 237 | 3 | 234 → `234 / 345` = `0.678261` |
| at `F_portable` = `0.456789`, portable instrument | 324 | 3 | 321 → `321 / 345` = `0.930435` |

## Pre-registered acceptance — both legs, with their values

The bars were registered before the run. Both legs are judged on the ORIGINAL labeled sets,
with response-best cosines captured by the PORTABLE instrument.

| leg | bar | measured | verdict |
|---|---|---|---|
| **(1)** `F_portable` false-fire rate against the legacy labeled real union | **≤ 5%** (`0.05`) | `11 / 357` = **`0.030812`** | **PASS** |
| **(2)** legacy nonsense catch at `F_portable` | **≥ 60%** (`0.60`) | `321 / 345` = **`0.930435`** | **PASS** |

**Both legs pass ⇒ the portable instrument is ACCEPTED as built.** Nothing here ships on a
caveat: a failed leg would have returned the instrument to design, not qualified this page.

> **Bound (iv) — the acceptance was NOT evaluated on held-out data, and here is exactly what
> that costs.** `legacy-nonsense` is **one of the six groups `F_portable` was selected over**
> (`02`, group 6), and the legacy labeled real union is the union of two more of them (groups 1
> and 2). **No leg of this acceptance is independent of the selection population.** What the
> selection did NOT do is the part that bounds the damage: `F_portable` was chosen off the
> pooled ladder across all six groups, **not** by sweeping for the value that maximises catch on
> `legacy-nonsense` or minimises false-fire on the real union — no single group's statistic was
> optimised, and no group's labels were derived from either instrument's own output. So these
> legs establish **"the portable floor clears the original bars on the original labeled sets"**
> and they do **not** establish that it generalises to any set not in the six. A held-out leg
> is not in this run; adding one is a design decision, not a re-analysis of these numbers.

Both acceptance rates are properties of the survey's labeled sets. Neither is an estimate of
how often the absence verdict would fire in production — that population was not sampled here
(packet 35).

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
