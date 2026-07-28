> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# 06 — Per-hit cosine distribution and the over-flag decomposition

*C6(f), the #180 rider. Aggregated from the run's own per-query rows — zero extra embeds, zero
extra searches, no distortion of the run.*

## Population

Answered queries (the absence verdict did not fire): **964** of 1740 — see `03`.
Shown slice: `SURVEY_K = 10`. Shown hits over answered queries: `964 × 10` = **9640**.

## Per-hit cosine distribution over the 9640 shown hits

| n | min | p5 | p25 | median | p75 | p95 | max | mean |
|---|---|---|---|---|---|---|---|---|
| 9640 | `0.212121` | `0.272727` | `0.363636` | `0.515151` | `0.616161` | `0.757575` | `0.898989` | `0.525252` |

## Over-flag decomposition at `F_portable` = `0.456789`

A hit is "over-flagged" when it was SHOWN to the caller on an answered query and its own cosine
is below the chosen floor.

| slice | hits below floor | of | rate |
|---|---|---|---|
| **all shown hits** | 3456 | 9640 | `3456 / 9640` = `0.358506` |
| **best hit (rank 1)** | 39 | 964 | `39 / 964` = `0.040456` |
| **mid-list (ranks 2–10)** | 3417 | 8676 | `3417 / 8676` = `0.393845` |

`39 + 3417 = 3456`; `964 + 8676 = 9640`.

All 39 best-hit-below-floor queries are anchored queries — that is precisely why they were
answered rather than refused, and 39 is the same anchored-and-below-floor count `03` reports.

> **Bound (i) — this measures the SURVEY's query mix, not live traffic.** The 964 answered
> queries above are the survey's own six groups in the survey's own proportions. **This package
> cannot tell you what fraction of live production queries would fire the absence verdict, or
> what fraction of live shown hits would be over-flagged**, and no number here may be
> re-expressed as such a fraction: the query mix that produced these rates was constructed, not
> sampled from traffic. Packet 35 is the instrument that would measure the live population. It
> has not run.
>
> **Bound (ii) — shown-k slice only.** Every number on this page covers ranks 1–10. The
> instrument captures `k' = 30` hits per query; ranks 11–30 are excluded here by design,
> because they were never shown to a caller and cannot be over-flagged.

## Why the decomposition is split this way

A floor that over-flags the best hit is refusing on results the caller would have found useful;
a floor that over-flags only mid-list hits is refusing on tail results the caller was going to
ignore. The two failure modes carry different costs and the aggregate rate hides which one is
happening, so the aggregate is never reported here without the split.
