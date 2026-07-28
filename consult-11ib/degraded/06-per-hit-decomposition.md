> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# 06 — Per-hit cosine distribution and the over-flag decomposition

*C6(f), the #180 rider. Aggregated from the run's own per-query rows — zero extra embeds, zero
extra searches, no distortion of the run.*

## Population

**`verdict_not_fired_queries`** (the absence verdict did not fire): **964** of 1740 — see `03`.
Shown slice: `SURVEY_K = 10`. Shown hits over `verdict_not_fired_queries`: `964 × 10` = **9640**.

⚠ This is one of THREE populations this package could loosely call "answered", and it is the
only one used on this page. The other two are `answered_probes` (411, the surviving probe count
`MIN_ANSWERED_PROBES` is checked against) and `probe_manifest_pool` (456, the
`self-supervised-answered` group). `00` names all three. **Do not use 964 as a probe count or
411 as a query count.**

## Per-hit cosine distribution over the 9640 shown hits

| n | min | p5 | p25 | median | p75 | p95 | max | mean |
|---|---|---|---|---|---|---|---|---|
| 9640 | `0.212121` | `0.272727` | `0.363636` | `0.515151` | `0.616161` | `0.757575` | `0.898989` | `0.525252` |

## Over-flag decomposition at `F_portable` = `0.456789`

A hit is "over-flagged" when it was SHOWN to the caller on a `verdict_not_fired_queries` query and its own cosine
is below the chosen floor.

| slice | hits below floor | of | rate |
|---|---|---|---|
| **all shown hits** | 3456 | 9640 | `3456 / 9640` = `0.358506` |
| **best hit (rank 1)** | 39 | 964 | `39 / 964` = `0.040456` |
| **mid-list (ranks 2–10)** | 3417 | 8676 | `3417 / 8676` = `0.393845` |

`39 + 3417 = 3456`; `964 + 8676 = 9640`.

All 39 best-hit-below-floor queries are anchored queries — that is precisely why they were
answered rather than refused, and 39 is the same anchored-and-below-floor count `03` reports.

## Why the decomposition is split this way

A floor that over-flags the best hit is refusing on results the caller would have found useful;
a floor that over-flags only mid-list hits is refusing on tail results the caller was going to
ignore. The two failure modes carry different costs and the aggregate rate hides which one is
happening, so the aggregate is never reported here without the split.
