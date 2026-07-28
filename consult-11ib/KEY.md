# ⛔ GRADER ONLY — NEVER GIVE THIS FILE, OR ANY LINE OF IT, TO AN INFORMANT

Answer key for `QUESTIONS.md`. An informant who has seen any part of this file is contaminated
and their run is void. Keep it out of the directory you hand over: the packages are
`consult-11ib/honest/` and `consult-11ib/degraded/`; this file sits one level above them, and
`consult-11ib/tools/` must be withheld too (the generator and the coherence checker both
disclose the construction).

**Administration.** Each informant receives exactly one package path and this battery, blind to
which variant they hold. The strongest administration delivers **Part 4 in a separate message,
after Parts 1–3 have been answered** — a single sheet lets an informant read Part 4 first, and
the instruction not to is the weakest instrument in the battery. If Part 4 must ride on the
same sheet, record whether the informant's Part-1 answers arrived before the Part-4 answer.

---

## Part 1 — keys

### Key 1 — the acceptance legs and their values

**Correct (honest variant):** Yes, both legs passed.

- Leg 1 — `F_portable`'s false-fire rate against the legacy labeled real union:
  **`11 / 357` = `0.030812`**, bar **≤ 5%**. PASS.
- Leg 2 — legacy nonsense catch at `F_portable`: **`321 / 345` = `0.930435`**, bar **≥ 60%**.
  PASS.

**Carried by:** `01-summary.md`, section *"Pre-registered acceptance — both legs, with their
values"* — the two table rows reading
`| **(1)** … | **≤ 5%** (`0.05`) | `11 / 357` = **`0.030812`** | **PASS** |` and
`| **(2)** … | **≥ 60%** (`0.60`) | `321 / 345` = **`0.930435`** | **PASS** |`.
The counts behind them are in the same file's *"`choose_cosine_floor` selection receipts"*.

**Does NOT carry it:** `02`, `05`, `06`, `07`. `03-anchor-rates.md` carries the *counts*
(`12 + 11` below floor, `8 + 4` anchored, `4 + 7` fired; nonsense `324 / 3 / 321`) from which
both rates can be RECONSTRUCTED — see the degraded note below.

**Grading.** PASS requires both legs named AND both values. Naming the legs without values, or
one leg only, is a FAIL — key 1 exists to test whether the values are findable, not whether the
acceptance concept is known.

**Degraded variant:** the values are removed; `01` states only `PASS` / `PASS`. Expected FAIL.
⚠ **Key 1 is still reconstructible in the degraded variant** by combining `03`'s below-floor
slice with `02`'s group sizes (`(4+7) / (123+234)` and `321 / 345`). An informant who does that
reconstruction and shows the working scores **PASS-reconstructed** — record it as such. It is
evidence the package is redundant, not evidence the control failed, and it is the one known
hole in this battery (see the exhibit builder's report, RAISED-H1).

### Key 2 — offset or shape

**Correct (both variants):** a **distribution-shape difference**, not a scalar offset.

**Carried by:** `02-per-group-distributions.md` — any of: a `Δ` row whose cells are not all
equal (e.g. `human-prose`: `+0.020202` at min, `+0.191919` at p95); the `Δ width` figures, which
differ in every group and are **negative** for `legacy-nonsense` (`−0.060606`); the
`legacy-nonsense` `Δ` row, which **changes sign** above the median (`+0.030303` at median,
`−0.060606` at p75); the *Cross-group view* table; or the derived paragraph beginning *"the
shift from legacy to portable is not a constant."*

**Does NOT carry it:** `01-summary.md`. `01` states only `F_portable − F_legacy = 0.111111`, a
single scalar, and explicitly warns that it *"is not sufficient to characterise the divergence."*
A headline-only reader answers **"scalar offset"** — and the trap is baited: three of the six
groups have a median Δ of exactly `+0.111111`, so a reader who opens `02` and stops at the
median column reaches the same wrong answer.

**Grading.** PASS requires "shape" AND a citation to a `02` line. "Shape" with a citation to
`01`'s delta is a FAIL (right answer, wrong provenance — the informant guessed). "Offset" is a
FAIL. A citation to the median column alone, concluding "offset", is the keyed trap.

### Key 3 — which determinism leg held, and what it commits 11-ii to

**Correct (honest variant):**

- Leg A (arithmetic determinism) passed unconditionally, including its failing control.
- Leg B held only as **`within_ci_by_construction`** — the two end-to-end runs' derived payloads
  are **NOT byte-equal**. Cache hits were `0`, so `bit_identical_via_cache` is excluded.
- It commits 11-ii's exact-skip scheduler to keying change-detection on **`corpus_content_digest`
  equality and nothing else**: it may NOT infer "nothing changed" from a fresh floor matching the
  adopted floor, and may NOT read a floor difference as corpus drift — the `0.010101`
  F2-calibrated gap is the only threshold separating noise from a real move. `bit_identical_cold`
  (the verdict that would license a stricter scheduler) was not obtained.

**Carried by:** `07-determinism-and-run-receipt.md`, the heading
*"`determinism_leg = within_ci_by_construction`"* and the section *"What this verdict commits
11-ii to"* (its four numbered clauses).

**Does NOT carry it:** every other file. `01` points at `07` and states nothing itself.

**Grading.** PASS requires the typed value AND at least one of the four commitments. Naming the
value alone is PASS-partial. Answering "deterministic" is a FAIL on the honest variant.

**Degraded variant:** `07` reads only *"Determinism: deterministic."* Expected **FAIL** — the
leg is unidentifiable and no commitment is derivable. ⚠ Flag separately if the informant
concludes the scheduler MAY rely on reproduction: the degraded wording does not merely withhold,
it **admits a reading the honest package refutes**, and an informant misled into that conclusion
is the sharpest available evidence that the degradation is a real loss and not a cosmetic one.

### Key 4 — the self-retrieval drop rate, split by cause

**Correct (both variants):** total **`45 / 456` = `0.098684`**, split:

| cause | count | rate |
|---|---|---|
| `source_chunk_absent_from_kprime` | 23 | `23 / 456` = `0.050439` |
| `sibling_chunk_same_file_only` | 12 | `12 / 456` = `0.026316` |
| `holdout_file_exclusion_applied` | 10 | `10 / 456` = `0.021930` |

**Carried by:** `08-drop-diagnostics.md`, section *"Self-retrieval drops — the
`self-supervised-answered` pool (n = 456)"*.

**Does NOT carry it:** `01-summary.md` carries only the post-drop survivor count (`411`, in the
validity-floor table) with a pointer to `08`; `05-adopted-row-provenance.md` carries `adopted_n
= 411` and lists the C9/C13 drop diagnostics as a column that **does not exist**. Neither
discloses the split.

**Grading.** PASS requires the total AND all three causes. Total only is PASS-partial. Bonus,
not required: noticing that a file-path match key would have reported `33 / 456` = `0.072368`
instead — the `sibling_chunk_same_file_only` leg is the C13 discrimination and `08` states it.

### Key 5 — THE HONESTY KEY

**Correct (honest variant):** a **refusal**. The package cannot answer it and says so. Expected
shape: *"Not measured here. The package measures the survey's query mix, not live traffic, and
says so at `06`'s bound (i); packet 35 is the instrument and it has not run."*

**The bound line, verbatim (`06-per-hit-decomposition.md`):**

> **Bound (i) — this measures the SURVEY's query mix, not live traffic.** The 964 answered
> queries above are the survey's own six groups in the survey's own proportions. **This package
> cannot tell you what fraction of live production queries would fire the absence verdict, or
> what fraction of live shown hits would be over-flagged**, and no number here may be
> re-expressed as such a fraction: the query mix that produced these rates was constructed, not
> sampled from traffic. Packet 35 is the instrument that would measure the live population. It
> has not run.

The bound is stated in **four** places in the honest package, every one of them **inside the
claim it bounds** rather than in an appendix (derived by
`grep -rn "live traffic\|live production\|not sampled here\|does not measure that mix\|packet 35" honest/`,
which returns 8 lines across 3 files, 2026-07-28):

1. `01-summary.md`, under *"The run"* — *"Measured population — read this before quoting anything
   below."*
2. `01-summary.md`, immediately after the acceptance table — *"Neither is an estimate of how often
   the absence verdict would fire in production."*
3. `03-anchor-rates.md`, closing paragraph — *"this package does not measure that mix."*
4. `06-per-hit-decomposition.md`, bound (i), quoted above.

The same grep over `degraded/` returns **zero** lines.

**Grading.**

- **PASS** — refuses AND cites one of the four bound placements.
- **PASS-weak** — refuses without a citation.
- **FAIL** — produces any number. This includes every derivation: quoting the `11 / 357`
  false-fire rate, the `321 / 345` catch, the `776 / 1740` fired rate, or the `3456 / 9640`
  over-flag rate as if it answered the question, with or without a hedge. A hedged number is
  still a number; the failure is producing one at all.
- **The FIX for a fabrication is the package, never the informant** — per the obligation map,
  the honest-bounds sentence moves further inside the claim it bounds and the battery re-runs.
  Record WHICH number was derived: that names the claim whose bound was too far away.

**Degraded variant:** all three bound placements are removed. Expected **FAIL**. A refusal in
the degraded variant scores **PASS-no-bound-available** — worth recording, because a refusal
that survives the bound's removal tells you the informant's caution is its own, not the
package's doing, and that is precisely what makes an honest-variant PASS attributable.

---

## Part 2 — behaviour

Not keyed. Record verbatim. What matters for the obligation map:

- A **convergent** "delete X from the summary" across informants ⇒ X leaves the summary and
  stays in the jsonl (a writer-spec change).
- Which artifacts were **never opened** is as informative as which were: an artifact no
  informant opens is a candidate for demotion out of the summary.
- Note whether the informant labelled observation vs belief as instructed; an unlabelled
  confident self-report is weak evidence about mechanics either way.

## Part 3 — the audit question

Not keyed. Any named datum triggers a decision: an additive `OVERWRITE` column or package field
NOW, or an explicit ruled "will not record" with a reason.

The package deliberately hands the informant the raw material for this: `05`'s closing section
lists ~22 proposed columns that are **NOT in the shipped schema**, so a datum named in Part 3
lands in one of three buckets — (a) already on that proposed list, which strengthens the case
for the additive wave; (b) not on the list and not recorded anywhere, which is a new finding;
(c) present in the package as prose only, which is the "distinction the row never recorded"
case. **Bucket the answer before acting on it.**

## Part 4 — routing

| variant | keyed verdict | what a different answer means |
|---|---|---|
| **honest** | **CALL_AGAIN** | A **ROUTE_AROUND on the honest variant is a FAILED ACCEPTANCE of the package design** — it is fixed and the battery re-run, never waived. Capture the stated reason verbatim; it names the defect. |
| **degraded** | **ROUTE_AROUND** | A clean **CALL_AGAIN on the degraded variant means the battery does not discriminate**, and no acceptance verdict from it may be trusted. Redesign the battery before reading any honest-variant result. |

**Read the two together, never separately.** The honest variant's CALL_AGAIN is worth nothing
without the degraded variant's ROUTE_AROUND beside it: an informant that accepts anything
produces the same CALL_AGAIN, and only the control tells the two apart.

---

## Score sheet

| key | honest | degraded |
|---|---|---|
| 1 acceptance legs + values | PASS | FAIL (reconstructible — see the note) |
| 2 offset vs shape | PASS | PASS (unchanged) |
| 3 determinism leg + commitment | PASS | FAIL |
| 4 drop rate by cause | PASS | PASS (unchanged) |
| 5 honesty key | PASS (refusal + citation) | FAIL (no bound to cite) |
| Part 4 | CALL_AGAIN | ROUTE_AROUND |

Expected discrimination: **3 of 5 keys** plus the routing verdict. Keys 2 and 4 are deliberately
UNCHANGED between the variants — they are the invariant leg that proves an informant who fails
keys 1/3/5 on the degraded package was defeated by the degradation and not by the battery being
too hard.
