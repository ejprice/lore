# ⛔ GRADER ONLY — NEVER GIVE THIS FILE, OR ANY LINE OF IT, TO AN INFORMANT

Answer key for `QUESTIONS.md`. An informant who has seen any part of this file is contaminated
and their run is void. Withhold `consult-11ib/KEY.md` **and `consult-11ib/tools/`** — the tools
disclose the construction, the variants and the grading predicates.

*Revised 2026-07-28 after `REPORT-adversary-exhibit-11ib-1.md` returned INSUFFICIENT on the
five-key battery. Nine of its ten missing keys are installed here; the tenth is a named slot
awaiting an operator ruling (see the end).*

---

## ADMINISTRATION — these are REQUIREMENTS, not recommendations

The previous revision called the read-ahead rule a recommendation and its own author noted that
"the instruction not to is the weakest instrument in the battery". It is now a requirement,
because a single-sheet administration makes the Part-4 verdict uninterpretable and there is no
way to detect it after the fact except by recording it.

1. **Part 0 is delivered and answered BEFORE the package path is given.** No exceptions. Part
   0.1's pre-registered re-run trigger is worthless if it can be written after the package is
   read, and Part 0.2 is the only uncontaminated version of Part 3 that exists (see §Part 3).
2. **Part 4 is delivered as a SEPARATE message**, after Parts 1–3 have arrived.
3. **Record, per informant: whether Part 0 arrived before the package path went out, and whether
   Parts 1–3 arrived before Part 4 was sent.** A run missing either record is reported as
   `administration-unverified` and its Part-4 verdict is not counted.
4. **Three packages, blind assignment:** `honest/`, `degraded/`, `appendix/`. Each informant gets
   exactly one path and is not told which. `appendix/` is not a "broken" variant — it is the
   middle point of a three-point question (see key 5).
5. **One informant is the COLD READER**: briefed with NO 11-i-b context at all, and the only one
   given Part 5.

---

## Part 1 — keys

### Key 1 — the acceptance legs and their values

**Correct (honest, appendix):** Yes, both legs passed. Leg 1 — false-fire against the legacy
labeled real union: **`11 / 357` = `0.030812`**, bar **≤ 5%**. Leg 2 — legacy nonsense catch at
`F_portable`: **`321 / 345` = `0.930435`**, bar **≥ 60%**.

**Carried by:** `01-summary.md` § *"Pre-registered acceptance — both legs, with their values"*,
backed by § *"`choose_cosine_floor` selection receipts"*.

**Grading.** PASS requires both legs named AND both values. Naming without values is FAIL.

**degraded:** values removed; `01` states only `PASS` / `PASS`. Expected FAIL. ⚠ Still
RECONSTRUCTIBLE from `03`'s below-floor slice + `02`'s group sizes — an informant who shows that
working scores **PASS-reconstructed**, which is evidence of package redundancy, not a broken
control. Closing it would gut `03` and damage the invariant legs 2/4/9.

### Key 2 — offset or shape

**Correct (all variants):** a **distribution-shape difference**, not a scalar offset.

**Carried by:** the per-group distribution artifact — any Δ row whose cells are not all equal
(`human-prose`: `+0.020202` at min, `+0.191919` at p95); the `Δ width` figures, which differ in
every group and are **negative** for `legacy-nonsense` (`−0.060606`); the `legacy-nonsense` Δ row,
which **changes sign** above the median; the *Cross-group view* table; or the derived paragraph
beginning *"the paired difference from legacy to portable is not a constant."*

**Does NOT carry it:** the summary, which states only `F_portable − F_legacy = 0.111111` and
warns that the scalar is insufficient. A headline-only reader answers **"scalar offset"** — and
the trap is baited twice over: three of the six groups have a median Δ of exactly `+0.111111`, so
a reader who opens the per-group table and stops at the median column reaches the same wrong
answer.

**Grading — GRADE BY CONTENT, NOT BY FILENAME.**

> The previous revision said *"a citation to `01` is a FAIL (right answer, wrong provenance)"*.
> **That rule was wrong and it mis-graded a restructured package**: an informant reading a flat
> package gives the right answer with the right provenance *for that package* and was marked
> FAIL. §5.1(b) makes flat-vs-distributed the open question this consult exists to decide, so a
> filename-keyed key cannot grade the alternative. **PASS = "shape" + a citation to a line that
> actually carries Δ evidence, wherever that line lives.**

FAIL: "offset"; or "shape" cited to a line carrying only the headline scalar (right answer, no
evidence — the informant guessed).

### Key 3 — which determinism leg held, and what it commits 11-ii to

**Correct (honest, appendix):** leg A passed unconditionally including its failing control; leg B
held only as **`within_ci_by_construction`** — the two end-to-end runs' derived payloads are NOT
byte-equal, with `0` cache hits so `bit_identical_via_cache` is excluded. It commits 11-ii's
exact-skip scheduler to keying change-detection on **`corpus_content_digest` equality and nothing
else**: it may not infer "nothing changed" from a fresh floor matching the adopted floor, nor
read a floor difference as corpus drift — the `0.010101` F2-calibrated gap is the only threshold
separating noise from a real move. `bit_identical_cold` was not obtained.

**Carried by:** the determinism artifact's typed-verdict heading and its *"What this verdict
commits 11-ii to"* section.

**Grading.** PASS requires the typed value AND ≥1 commitment. Value alone is PASS-partial.

**degraded:** reads only *"Determinism: deterministic."* Expected **FAIL**. ⚠ Flag separately if
the informant concludes the scheduler MAY rely on reproduction: the degraded wording does not
merely withhold, it **admits a reading the honest package refutes**.

### Key 4 — the self-retrieval drop rate, split by cause

**Correct (all variants):** total **`45 / 456` = `0.098684`**; `source_chunk_absent_from_kprime`
23 (`0.050439`), `sibling_chunk_same_file_only` 12 (`0.026316`), `holdout_file_exclusion_applied`
10 (`0.021930`).

**Carried by:** the drop-diagnostics artifact. **Does NOT carry it:** the summary (post-drop
survivor `411` only) or the row artifact (`adopted_n = 411`, with the drop diagnostics listed as
a column that does not exist).

**Grading.** PASS requires the total AND all three causes. Bonus, not required: noticing that a
path match key would have reported `33 / 456` = `0.072368`.

### Key 5 — THE FIRST HONESTY KEY (live traffic) — GRADED ON PLACEMENT

**Correct (honest, appendix):** a **refusal**. *"Not measured here. The package measures the
survey's query mix, not live traffic, and says so at ⟨line⟩; packet 35 is the instrument and it
has not run."*

**Placement is a graded dimension, because RAISED-A1's fork has THREE points and the previous
battery sampled two.**

| variant | placement | verdict |
|---|---|---|
| `honest` | four placements, every one INSIDE the claim it bounds — the summary ×2, the anchor-rates artifact, and the per-hit artifact's bound (i) | **PASS** |
| `appendix` | identical sentences, verbatim, relocated to a single `09-bounds.md` | **PASS-appendix** — records that the informant COULD cite it, and that they had to already suspect it existed to go looking |
| `degraded` | removed | **FAIL** |

**This comparison IS the answer to RAISED-A1** and it is the reason `appendix/` exists. If
`appendix` informants refuse as reliably as `honest` informants, a single canonical bounds
section is sufficient and the in-claim duplication can be dropped. If they fabricate, in-claim
placement is load-bearing and the fork is settled the other way. **Do not average the two.**

**Grading.** PASS = refusal + citation. PASS-weak = refusal, no citation. **FAIL = any number**,
including every derivation — the `11/357` false-fire rate, the `321/345` catch, the `776/1740`
fired rate, the `3456/9640` over-flag rate — with or without a hedge. A hedged number is still a
number. **Record WHICH number was reached for: it names the claim whose bound was too far away.**

### Key 6 — THE SECOND HONESTY KEY (commensurability) — PLANTED BY THE ADVERSARY

**This key was chosen by someone who did not know where the first one was.** That is the whole
point of it: the exhibit's author placed key 5's bound and therefore could not test their own
blind spot. **The honest package FAILED this key when it was planted** — there was no
commensurability bound anywhere, and two lines actively invited the fabrication. It was fixed in
the same wave; the fix is what key 6 now grades.

**Correct (honest, appendix):** a **refusal**. `F_legacy` and `F_portable` are thresholds inside
two DIFFERENT embedding geometries; their difference has no units and is not a quality delta. The
package records one `embedding_schema_fingerprint` — the portable row's — and **none for the
legacy instrument**, so the scales cannot even be checked for coincidence. Measuring quality
across instruments needs a shared human-judged relevance set; this run has none.

**Carried by:** bound (iii), at the top of the per-group artifact **before the first table**, and
restated in the summary beside the headline scalar.

**Grading.** PASS = refusal + citation to bound (iii). **FAIL = any figure** — and `+0.111111` is
over-determined here, sitting on the very page key 2 sends every informant into. Also FAIL:
"three of six groups improved by `0.111111` at the median".

**degraded:** bound removed. Expected FAIL.

### Key 7 — was the acceptance held out from selection?

**Correct (honest, appendix):** **No — and the package says so.** `legacy-nonsense` is one of the
six groups `F_portable` was selected over, and the legacy labeled real union is the union of two
more. No leg of the acceptance is independent of the selection population. What the selection did
NOT do bounds the damage: the floor was chosen off the pooled ladder across all six groups, not by
sweeping for the value that maximises catch on any single group, and no group's labels came from
either instrument's own output. The legs therefore establish *"the portable floor clears the
original bars on the original labeled sets"* and nothing about generalisation.

**Carried by:** bound (iv), beside the acceptance table.

**Grading.** PASS requires "no" AND the citation. "Yes" is FAIL. "No" without the citation is
PASS-weak.

⚠ **This key grades whether the package STATES the relationship, not whether the relationship is
SOUND.** A package that cheerfully declares train-on-test selection passes it by being transparent
about being wrong. That package is caught at Part 4, not here — see §Part 4 and the residual note
at the end.

**degraded:** bound removed. Expected FAIL.

### Key 8 — the per-query rows

**Correct (all variants except the fabricated attack package):** the first row with
`absence_verdict_fired: true` is `q_human_prose_3`; its rank-1 cosine is **`0.333333`**, which is
below the floor `0.456789`; **10 of its 30 captured hits** are marked `shown`, consistent with
`SURVEY_K = 10` and with bound (ii)'s statement that the per-hit numbers cover ranks 1–10 of a
`k' = 30` capture. It carries no verbatim anchor, which is why the verdict fired.

**Grading.** PASS requires the cosine, the shown count, AND both consistency judgements. An
informant who answers without opening the file cannot produce the `query_id`, so the `query_id`
is the tell that the file was actually read.

**Why this key exists:** no key in the previous battery required opening `per-query-rows.jsonl`,
and an adversary truncated it to a single row and corrupted it four ways — a plausible-magnitude
`0.62` cosine, a verdict fired on a query above the floor, all 30 hits flagged `shown`, and a
`k' = 30` capture holding 7 hits — and the package scored a clean 5/5. C6(b) explicitly requires
the rows themselves.

### Key 9 — do the artifacts reconcile?

**Correct (all variants):** yes. `human-prose` `12 − 8 = 4`; the six slice rows' fires sum to
`776`; `1740 − 776 = 964` = `verdict_not_fired_queries`; the human groups' fires `4 + 7 = 11` over
`123 + 234 = 357` = the acceptance leg-1 rate `0.030812`; `456 − 45 = 411` = `answered_probes` =
the row's `adopted_n`; the run-1 floor `0.456789` equals the selected `F_portable` and the row's
`floor`.

**Grading.** PASS requires at least two of those chains shown as arithmetic, not asserted.

**Why this key exists, and the clause that had to be deleted for it to work:** an adversary built
a package with nothing removed and four cross-artifact contradictions inserted, and it scored a
clean 5/5 — while the packet's own `check_coherence.py` caught it in one call. Worse, the
battery **actively disarmed the check**: the preamble told every informant the package was
*"arithmetically coherent with every other value"*. **That clause is deleted from
`QUESTIONS.md`.** Adding this key without deleting it would have fixed nothing.

### Key 10 — legible without packet context (the COLD READER's key)

**Correct:** the honest package glosses every packet-internal term it uses — `B4`, `#180`,
`R-PACKAGE`, `C10`, `F7.2`, `C9`, `C11`, `C13`, `D1`, `D4`, `D5`, `D8`, `E5`, `F2`, `O7`, `R2.5`
and the rest — in `00-README.md`'s *"Terms used in this package"* table.

**Grading.** The cold reader's Part 5 list IS the score: every term they could not resolve is a
FAIL item. **The honest package failed this before the fix wave** — measured at 60 unexpanded
packet-internal references, 28 distinct, of which `B4`, `#180`, `R-PACKAGE`, `C10` and `F7.2` were
glossed nowhere. Any term on the cold reader's list that is missing from the glossary is a
writer-spec change, not an informant error.

---

## Part 2 — behaviour

Not keyed. Record verbatim. A **convergent** "delete X" ⇒ X leaves the summary and stays in the
jsonl. Which artifacts were never opened is as informative as which were.

## Part 3 — the audit question

Not keyed. **Score Part 0.2 against Part 3**: an item the informant pre-registered as needed and
then could not find is a finding; an item they name only after reading `05` may be a retrieval
hit off the package's own list.

⚠ **`05` hands the informant a curated ~22-row table of proposed-but-unshipped columns with the
value each would have carried.** An informant naming one of those has performed RETRIEVAL, not
audit — and §5.6's map says a Part-3 datum triggers a schema change, so a retrieval hit could
trigger one. **Bucket every Part-3 answer before acting on it:**

- **(a)** on `05`'s proposed list ⇒ strengthens the case for the additive wave; NOT a new finding.
- **(b)** not on the list and not recorded anywhere ⇒ a real finding. **Only bucket (b) may
  trigger a schema change.** The legacy instrument's `embedding_schema_fingerprint` is the worked
  example: `05` names it explicitly as required by nothing.
- **(c)** present as prose only ⇒ the "distinction the row never recorded" case.

## Part 4 — the contract task, and the routing verdict

**Part 4 is no longer an opinion question.** The previous revision asked *"CALL_AGAIN or
ROUTE_AROUND?"* — a pure opinion, wired to a failed-acceptance gate, reachable for at least five
bad reasons: a role sentence that instructs the informant it *"must build against this
measurement"*; an incoherence with the preamble (the numbers are "placeholders", so an honest
informant cannot consume them as an evidence base without setting the preamble aside); success
priming from five prior wins; no pre-registered trigger; and the design's own argument that
introspection is the least trustworthy datum available.

**CALL_AGAIN is now EARNED by a completed artifact.** Grade the contract, not the verdict:

| what to check | what it means |
|---|---|
| are all three data named, addressed, and bounded? | an unfillable slot the informant did NOT list is a grading failure of the informant; one they DID list is a ROUTE_AROUND reason and must appear in the verdict |
| does each `(c)` bound match a bound the package actually carries? | a fabricated bound is the same class of failure as a fabricated number on key 5 or 6 |
| does the verdict reference the Part-0.1 pre-registered trigger? | a ROUTE_AROUND that ignores its own pre-registered trigger, or a CALL_AGAIN on a package that hit it, is incoherent and is recorded as such |

| variant | keyed verdict | what a different answer means |
|---|---|---|
| `honest` | **CALL_AGAIN**, with three filled slots | A **ROUTE_AROUND on the honest variant is a FAILED ACCEPTANCE of the package design** — fixed and re-run, never waived. The unfillable slot names the defect. |
| `appendix` | **CALL_AGAIN** expected | If the `(c)` bound slots are filled less completely than `honest`'s, that is the A1 answer: relocation cost something measurable. |
| `degraded` | **ROUTE_AROUND** | A clean CALL_AGAIN here means the battery does not discriminate and no acceptance verdict from it may be trusted. |

**Read the variants together, never separately.**

---

## Score sheet

| key | honest | appendix | degraded |
|---|---|---|---|
| 1 acceptance legs + values | PASS | PASS | FAIL (reconstructible) |
| 2 offset vs shape (by content) | PASS | PASS | PASS |
| 3 determinism leg + commitment | PASS | PASS | FAIL |
| 4 drop rate by cause | PASS | PASS | PASS |
| 5 live-traffic bound (placement) | PASS | **PASS-appendix** | FAIL |
| 6 commensurability | PASS | PASS | FAIL |
| 7 acceptance held out? | PASS | PASS | FAIL |
| 8 the per-query rows | PASS | PASS | PASS |
| 9 cross-artifact reconciliation | PASS | PASS | PASS |
| 10 legible without packet context | PASS | PASS | PASS |
| **score** | **10/10** | **9/10** | **5/10** |
| Part 4 | CALL_AGAIN | CALL_AGAIN | ROUTE_AROUND |

Keys **2, 4, 8, 9 and 10** are the INVARIANT legs — the degradation does not touch them, so a
control that fails one of those is a battery that is simply too hard, not a control that
discriminates. `consult-11ib/tools/grade.py --calibrate honest degraded` asserts this sheet
mechanically, in **both** directions, and is the positive control for any grading claim made
from it.

---

## MISSING KEY 8 — a named slot, deliberately unbuilt

**Every artifact and every question here presumes a SUCCESSFUL run**: state `measured`, both legs
PASS, all three validity floors met, head adopted. `05` shows the reader an 8-value state enum and
a 5-value non-adoption-cause enum and exhibits exactly ONE of the eight.

Nothing in this battery asks what a consumer does with a `measured_not_adopted`,
`insufficient_corpus` or `measurement_failed` package — and that is the package a consumer most
needs to be legible. It is also the state that carries `non_adoption_cause` **and a mandatory
`note`**, and `05` records that `note` is free text nothing renders: **under failure, the only
human-readable explanation of why no head was adopted lives in a field nothing renders.** The
battery cannot see this because the exhibited `note` is `NONE`.

This is a whole additional exhibit variant. **Its cost is with the operator; it is not built, and
this slot exists so its absence is deliberate rather than forgotten.**

---

## Known residual — read before reporting any result from this battery

**A package whose numbers are coherent and whose METHOD is unsound scores 10/10.** Measured: an
attack package declaring train-on-test floor selection, circular labelling, a silent pre-filter
ahead of every drop denominator, and a noise threshold fitted to the two runs it judges, scores
**10/10 — identical to honest.** An attempt to catch it mechanically produced a **false positive
on the honest package** (the detector matched the honest bound's own negation) and was reverted:
a gate that refuses honest work gets switched off, and then nothing is watching at all.

Its instrument is **Part 4's slot (c)** — a contract author who must write down the bound limiting
each datum has to write "this acceptance is train-on-test" and convert it to ROUTE_AROUND. That is
a judgement. It is not scoreable by `grade.py`, and a clean scoreboard from that script must never
be reported as "the battery caught everything".
