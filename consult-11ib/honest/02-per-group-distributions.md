> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# 02 — Response-best cosine distributions, six groups, both instruments

*C6(b). The per-query rows themselves are in `per-query-rows.jsonl`.*

> **Bound (iii) — the two instruments' cosines are NOT commensurable. Read this before the
> first table.** `F_legacy` and `F_portable` are thresholds inside two DIFFERENT embedding
> geometries. Their difference `0.111111` has no units and is **not a retrieval-quality
> change**: nothing here establishes that a cosine of `0.5` under one instrument means what a
> cosine of `0.5` means under the other. This package records one
> `embedding_schema_fingerprint` — the portable row's (`05`, column 12) — and **none for the
> legacy instrument**, so the two scales cannot even be checked for coincidence. Every `Δ` on
> this page is a difference of two SHAPES measured on the same queries, read only for whether
> the shape is constant. **No `Δ` here may be re-expressed as an improvement, a regression, a
> quality delta, or a percentage of anything.** Measuring quality across instruments needs a
> shared human-judged relevance set; this run has none.

Both instruments captured a response-best cosine for every query in all six groups on the same
corpus snapshot. That buys exactly one thing: the two instruments saw the same queries against
the same corpus, so their `Δ` is **PAIRED** — which licenses reading the SHAPE of the
difference, and nothing about its magnitude. `Δ` throughout is `portable − legacy`.

`n` values are the group sizes; the six sum to **1740**, the run's full query set.

---

## Group 1 — `human-prose` (n = 123)

| instrument | min | p5 | p25 | median | p75 | p95 | max | mean |
|---|---|---|---|---|---|---|---|---|
| legacy | `0.313131` | `0.373737` | `0.454545` | `0.535353` | `0.616161` | `0.696969` | `0.777777` | `0.525252` |
| portable | `0.333333` | `0.404040` | `0.494949` | `0.646464` | `0.757575` | `0.888888` | `0.939393` | `0.636363` |
| **Δ** | `+0.020202` | `+0.030303` | `+0.040404` | `+0.111111` | `+0.141414` | `+0.191919` | `+0.161616` | `+0.111111` |

p5–p95 width: legacy `0.323232` · portable `0.484848` · **Δ width `+0.161616`**

## Group 2 — `human-implementation-vocabulary` (n = 234)

| instrument | min | p5 | p25 | median | p75 | p95 | max | mean |
|---|---|---|---|---|---|---|---|---|
| legacy | `0.474747` | `0.494949` | `0.515151` | `0.535353` | `0.555555` | `0.575757` | `0.595959` | `0.535353` |
| portable | `0.414141` | `0.464646` | `0.606060` | `0.646464` | `0.686868` | `0.727272` | `0.767676` | `0.646464` |
| **Δ** | `−0.060606` | `−0.030303` | `+0.090909` | `+0.111111` | `+0.131313` | `+0.151515` | `+0.171717` | `+0.111111` |

p5–p95 width: legacy `0.080808` · portable `0.262626` · **Δ width `+0.181818`**

## Group 3 — `synthesized-identifier` (n = 15)

| instrument | min | p5 | p25 | median | p75 | p95 | max | mean |
|---|---|---|---|---|---|---|---|---|
| legacy | `0.606060` | `0.616161` | `0.636363` | `0.666666` | `0.696969` | `0.717171` | `0.737373` | `0.666666` |
| portable | `0.646464` | `0.656565` | `0.686868` | `0.727272` | `0.767676` | `0.797979` | `0.818181` | `0.727272` |
| **Δ** | `+0.040404` | `+0.040404` | `+0.050505` | `+0.060606` | `+0.070707` | `+0.080808` | `+0.080808` | `+0.060606` |

p5–p95 width: legacy `0.101010` · portable `0.141414` · **Δ width `+0.040404`**

⚠ n = 15 is the pre-registered identifier pool (the first 15 identities in ascending
`sha512_hex(identity)` order). At n = 15, `p5` and `p95` are single order statistics: they move
by a whole sample under one insertion. Read them as edges, not as estimates.

## Group 4 — `self-supervised-answered` (n = 456)

| instrument | min | p5 | p25 | median | p75 | p95 | max | mean |
|---|---|---|---|---|---|---|---|---|
| legacy | `0.353535` | `0.424242` | `0.505050` | `0.575757` | `0.646464` | `0.727272` | `0.808080` | `0.575757` |
| portable | `0.393939` | `0.464646` | `0.575757` | `0.686868` | `0.797979` | `0.909090` | `0.949494` | `0.676767` |
| **Δ** | `+0.040404` | `+0.040404` | `+0.070707` | `+0.111111` | `+0.151515` | `+0.181818` | `+0.141414` | `+0.101010` |

p5–p95 width: legacy `0.303030` · portable `0.444444` · **Δ width `+0.141414`**

## Group 5 — `hold-out-absent` (n = 567)

| instrument | min | p5 | p25 | median | p75 | p95 | max | mean |
|---|---|---|---|---|---|---|---|---|
| legacy | `0.101010` | `0.161616` | `0.222222` | `0.282828` | `0.343434` | `0.404040` | `0.464646` | `0.292929` |
| portable | `0.121212` | `0.191919` | `0.262626` | `0.333333` | `0.414141` | `0.494949` | `0.565656` | `0.343434` |
| **Δ** | `+0.020202` | `+0.030303` | `+0.040404` | `+0.050505` | `+0.070707` | `+0.090909` | `+0.101010` | `+0.050505` |

p5–p95 width: legacy `0.242424` · portable `0.303030` · **Δ width `+0.060606`**

## Group 6 — `legacy-nonsense` (n = 345)

| instrument | min | p5 | p25 | median | p75 | p95 | max | mean |
|---|---|---|---|---|---|---|---|---|
| legacy | `0.121212` | `0.151515` | `0.191919` | `0.232323` | `0.363636` | `0.515151` | `0.646464` | `0.303030` |
| portable | `0.131313` | `0.171717` | `0.212121` | `0.262626` | `0.303030` | `0.474747` | `0.606060` | `0.292929` |
| **Δ** | `+0.010101` | `+0.020202` | `+0.020202` | `+0.030303` | `−0.060606` | `−0.040404` | `−0.040404` | `−0.010101` |

p5–p95 width: legacy `0.363636` · portable `0.303030` · **Δ width `−0.060606`**

---

## Cross-group view

| group | median Δ | p5 Δ | p95 Δ | Δ p5–p95 width |
|---|---|---|---|---|
| `human-prose` | `+0.111111` | `+0.030303` | `+0.191919` | `+0.161616` |
| `human-implementation-vocabulary` | `+0.111111` | `−0.030303` | `+0.151515` | `+0.181818` |
| `synthesized-identifier` | `+0.060606` | `+0.040404` | `+0.080808` | `+0.040404` |
| `self-supervised-answered` | `+0.111111` | `+0.040404` | `+0.181818` | `+0.141414` |
| `hold-out-absent` | `+0.050505` | `+0.030303` | `+0.090909` | `+0.060606` |
| `legacy-nonsense` | `+0.030303` | `+0.020202` | `−0.040404` | `−0.060606` |

**Derived from the columns above, and the reason the headline scalar in `01` is not sufficient:**
the paired difference from legacy to portable is not a constant. It differs across percentiles WITHIN a
group (`human-implementation-vocabulary`: `−0.030303` at p5, `+0.151515` at p95), it differs
across groups at the same percentile (median Δ ranges `+0.030303` to `+0.111111`), it **changes
sign** in `legacy-nonsense` above the median, and the p5–p95 width changes by a different amount
in every group — including one negative. A scalar offset would show one number in every cell of
the Δ rows and zero in every width-Δ cell. This is a distribution-shape difference, not an offset.

The three groups whose median Δ is exactly `+0.111111` are the reason the headline number looks
like an offset if you stop at medians.

## The per-query rows

`per-query-rows.jsonl` carries the rows themselves. It is a **deterministic four-per-group
sample** (24 rows) of the run's 1740; the full file is the shipped artifact. Each row carries
`query_id`, `group`, `query_text`, `response_best_cosine`, `has_verbatim_anchor`,
`absence_verdict_fired`, `source_point_id`, `self_retrieved`, and the `k' = 30` hit capture with
each hit's `rank`, `point_id` and `vector_cosine`. The first line is a banner object; every row
carries `"_synthetic": true`.

Because the file is a sample, its per-group counts do not reproduce the group rates in this file
or in `03` — they are consistent with them, not equal to them.
