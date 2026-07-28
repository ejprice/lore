> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# 09 — Bounds

Every bound that governs any number in this package, collected in one place.

**Measured population — read this before quoting anything below.** Every rate on this page is
computed over the SURVEY's query set (1740 queries across six groups, `02`). It is not a
sample of live production traffic, and nothing in this package supports a statement about
what fraction of live queries would fire the absence verdict. Packet 35 is the instrument
that would measure that; it has not run.

---

Both acceptance rates are properties of the survey's labeled sets. Neither is an estimate of
how often the absence verdict would fire in production — that population was not sampled here
(packet 35).

---

⚠ **That scalar is DIMENSIONLESS and it is not a quality delta.** The two floors are thresholds
in two different embedding geometries; the package carries an `embedding_schema_fingerprint` for
the portable instrument and none for the legacy one, so the two scales cannot be checked for
coincidence. It may not be re-expressed as an improvement, a regression or a percentage —
`02`'s bound (iii) states this in full, beside the tables it governs. What `02` does carry is
the per-percentile and per-group SHAPE of the paired difference, which this single number
averages away.

---

These rates are properties of the survey's query mix. A different query mix — production
traffic, for one — would produce different anchor rates and therefore a different rate of
absence verdicts, and this package does not measure that mix.

---

> **Bound (i) — this measures the SURVEY's query mix, not live traffic.** The 964
> `verdict_not_fired_queries` above are the survey's own six groups in the survey's own
> proportions. **This package
> cannot tell you what fraction of live production queries would fire the absence verdict, or
> what fraction of live shown hits would be over-flagged**, and no number here may be
> re-expressed as such a fraction: the query mix that produced these rates was constructed, not
> sampled from traffic. Packet 35 is the instrument that would measure the live population. It
> has not run.
>
> **Bound (ii) — shown-k slice only.** Every number on this page covers ranks 1–10. The
> instrument captures `k' = 30` hits per query; ranks 11–30 are excluded here by design,
> because they were never shown to a caller and cannot be over-flagged.

---

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

---

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
