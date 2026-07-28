brief-base v7 read

# REPORT-exhibit-11ib-1 — the consult exhibit package for packet 11-i-b

## SUMMARY BLOCK

- `brief-base v7 read`
- **state:** done
- deviation 1: C6(d)'s self-supervised probe texts use an EXHIBIT-AUTHORED derivation rule, not
  the shipped one — the shipped derivation does not exist yet (11-i-b builds it). The human
  questions half IS real and verbatim.
- deviation 2: the exhibit's store coordinate is `ws://SYNTHETIC-STORE:00000/rpc`, not the real
  `:18500` — real SHAPE, withheld VALUE, so the page cannot be copy-pasted into a production run.
- deviation 3: two tool scripts written under `consult-11ib/tools/` beyond the brief's named
  deliverables (a jsonl generator and a coherence checker). Rationale in §6; both are inside the
  brief's writable path.
- `Packages considered:` **none — no mechanism specified.** This packet builds documents plus two
  throwaway generators. `json` / `decimal` / `re` / `xml.etree` (stdlib) cover the generators
  entirely; no third-party surface was needed and none was added.
- decisions-needed: (1) is the honest bound's placement mine to choose or the lead's? — §5.3 of
  the spec says placement is under test but never says what 11-i-b INTENDS (RAISED-A1);
  (2) RAISED-1's proposed columns are unruled and I rendered them as NOT-SHIPPED (RAISED-A3);
  (3) whether `consult-11ib/` gets committed, and where (RAISED-A9).
- receipts: manifest §1 · key-distribution table §2 · implausibility rule §3 · honest↔degraded
  diff §4 · instrument controls §5 (11 declared, 11 fired, byte-identical restore) · the
  self-check §7 · RAISED §8.

---

## 0. What was built, and against what

Spec: `REPORT-fable-design-11ib-2.md` §5 (§5.1 scope, §5.2 method, §5.3 exhibit rules, §5.4 the
battery, §5.5 the control leg, §5.6 the obligation map). Real shapes were read from the tree, not
from any report's transcription:

- `FLOOR_MEASUREMENT_COLUMNS` (14), `FLOOR_STATES` (8), `FLOOR_NON_ADOPTION_CAUSES` (5) read
  directly from `loremaster/loremaster/store/surreal_schema.py`. The shipped spelling is
  **`substrate_indiscriminate`**, and that is what the exhibit uses.
- `SURVEY_K = 10` verified at source (`scripts/search_score_survey.py::SURVEY_K`), so the
  exhibit's shown-k slice and the design's `k' = 30` ("3× `SURVEY_K`") are consistent rather
  than asserted.
- The C6 (a)–(f) list from `docs/plans/v2/receipts/2026-07-26-packet11i-fixwave/REPORT-fable-design-11i.md`
  (the six sub-deliverables), addressed per CONTRACT-FREEZE-DECISIONS §C5, adoption per §C6,
  verb mechanics per §C7, drop causes per §C9/§C13.

**Tool honesty (brief-base §4, repo CLAUDE.md).** I did **not** use lore's index for any of this.
lore watches the MAIN checkout at `2b8aa01` and is blind to this worktree's commits (#125), which
the brief flagged; every file lookup here was `grep` + `Read` against the worktree, plus two
`python` extractions (the eval XML and an AST walk). Saying so out loud per the fallback rule.
This is the known #125 gap, not a new one, so I did not file a friction row for it.

---

## 1. Manifest — every file written

All paths relative to `/home/ejprice/PycharmProjects/lore-pkt11i-b/`. No git operations were run.

| path | bytes | what it is |
|---|---|---|
| `consult-11ib/QUESTIONS.md` | 2655 | the battery, Parts 1→4 in order, verbatim question text |
| `consult-11ib/KEY.md` | 12565 | **GRADER ONLY** — answers, carrying lines, per-variant verdicts, score sheet |
| `consult-11ib/honest/00-README.md` | 2404 | package map + the sentinel-construction rule |
| `consult-11ib/honest/01-summary.md` | 3895 | C6(a): both floors, selection receipts, both acceptance legs with values |
| `consult-11ib/honest/02-per-group-distributions.md` | 6500 | C6(b): six groups × two instruments × nine stats, Δ rows, widths, cross-group view |
| `consult-11ib/honest/03-anchor-rates.md` | 1840 | C6(c): anchor rate per group + the below-floor slice |
| `consult-11ib/honest/04-probe-texts.md` | 6533 | C6(d): ten probe texts beside ten human questions |
| `consult-11ib/honest/05-adopted-row-provenance.md` | 5600 | C6(e): the 14 shipped columns with values, both closed enums, and the NOT-SHIPPED proposed set |
| `consult-11ib/honest/06-per-hit-decomposition.md` | 2643 | C6(f): per-hit distribution + over-flag split + both honest bounds |
| `consult-11ib/honest/07-determinism-and-run-receipt.md` | 5601 | the typed determinism verdict + C7 provenance receipt + cost accounting |
| `consult-11ib/honest/08-drop-diagnostics.md` | 3821 | C9/C13 drops by cause, validity floors, probe manifest |
| `consult-11ib/honest/per-query-rows.jsonl` | 90698 | C6(b)'s second half: 24 rows, banner line, `k' = 30` captures |
| `consult-11ib/degraded/*` | — | same ten filenames, same order; §4 itemises the diff |
| `consult-11ib/tools/make_exhibit_jsonl.py` | 7821 | deterministic generator for the jsonl (deviation 3) |
| `consult-11ib/tools/check_coherence.py` | 22646 | the coherence + implausibility auditor (deviation 3) |
| `REPORT-exhibit-11ib-1.md` | this file | |

**The two packages carry IDENTICAL FILE NAMES in identical order** (verified: `diff <(ls honest)
<(ls degraded)` is empty). An informant cannot infer their variant from the directory listing.

`consult-11ib/tools/` must be withheld from informants along with `KEY.md` — both scripts disclose
the construction. `KEY.md` says so at its head.

---

## 2. Every Part-1 key answers from a DIFFERENT place

This is the discriminating property the brief named. The right-hand column is the load-bearing
one: it names a file an informant would plausibly look in that does NOT contain the answer.

| key | answered by | does NOT carry it |
|---|---|---|
| **1** — acceptance legs + values | `01-summary.md` § *"Pre-registered acceptance — both legs, with their values"* (`11/357` = `0.030812` vs ≤5%; `321/345` = `0.930435` vs ≥60%), backed by § *"`choose_cosine_floor` selection receipts"* | `02`, `05`, `06`, `07`, `08` — none states a bar or a leg. ⚠ `03`'s below-floor slice carries the raw counts, so the rates are RECONSTRUCTIBLE from `03` + `02` (RAISED-H1) |
| **2** — offset or shape | `02-per-group-distributions.md` — the Δ rows, the `Δ width` figures, the sign change in `legacy-nonsense` (`+0.030303` at median, `−0.060606` at p75), the *Cross-group view* table, the derived paragraph | `01-summary.md`, which states ONLY `F_portable − F_legacy = 0.111111` and warns it is insufficient. **A headline-only reader answers "scalar offset" — wrongly.** The trap is deliberately deep: three of six groups have a median Δ of exactly `+0.111111`, so opening `02` and stopping at medians reaches the same wrong answer |
| **3** — determinism leg + commitment | `07-determinism-and-run-receipt.md` § *"`determinism_leg = within_ci_by_construction`"* and § *"What this verdict commits 11-ii to"* (four numbered clauses) | every other file. `01`'s Outcome section points at `07` and states nothing itself |
| **4** — self-retrieval drop rate by cause | `08-drop-diagnostics.md` § *"Self-retrieval drops"* — `45/456` = `0.098684`, split 23 / 12 / 10 | `01` carries only the post-drop `411` in its validity-floor table; `05` carries `adopted_n = 411` and lists the drop diagnostics among columns that **do not exist**. Neither discloses the split |
| **5** — HONESTY KEY | **unanswerable by design.** The refusal is supported at four in-claim placements: `01` × 2, `03` × 1, `06` bound (i) | nothing derives it. The tempting wrong sources are `01`'s `11/357`, `01`'s `321/345`, `03`'s `776/1740`, `06`'s `3456/9640` — `KEY.md` lists all four so the grader records WHICH one a fabricator reached for, since that names the claim whose bound sat too far away |

**Bound-placement count, derived not asserted.** `grep -rn "live traffic\|live production\|not
sampled here\|does not measure that mix\|packet 35" honest/` returns **8 lines across 3 files** =
four distinct bound statements (`01` ×2, `03` ×1, `06` ×1). The same grep over `degraded/` returns
**zero**.

---

## 3. Every value is magnitude-implausible — the rule, and its machine check

**The rule, stated once and enforced:**

> Every **independently chosen** real value is either a two-digit repunit (`0.ababab` —
> `0.313131`, `0.696969`, `0.474747`) or an ascending digit run (`0.123456`, `0.234567`,
> `0.345678`, `0.456789`). Every independently chosen count is a strictly monotone digit run
> (`12`, `23`, `39`, `123`, `234`, `345`, `456`, `567`, `987`, `1234`, `3456`, `23456`, `34567`).
> Every **derived** value — a sum, difference, rate or remainder — is the exact arithmetic
> consequence of its inputs and therefore usually carries no signature at all. That is what
> coherence costs, and it is the point: the derived values are what let a reader audit the
> package against itself.

Why this family: the repunit set spans `[0.010101, 0.989898]` in 0.010101 steps and is **closed
under ±0.010101**, so a whole distribution can be built inside it while staying visibly
artificial. No real six-decimal cosine lands on `0.ababab` except at probability ≈ 10⁻⁴, and no
real distribution is composed entirely of them.

Non-numeric sentinels follow the same discipline, and two are deliberate: `instrument_version`,
`scipy` and `numpy` all read `0.0.0-SYNTHETIC` **because "a fabricated version" is a named
PKT-28 defect class** — a plausible version string is exactly the value that escapes; and
`created_at` is `1234-05-06T07:08:09Z`, a year no deployment has.

**The machine check:** `consult-11ib/tools/check_coherence.py` re-derives every relation and
enforces the implausibility rule on every independently chosen value. It exits 0 on
`consult-11ib/honest` and exits 1 on `consult-11ib/degraded` naming exactly the eight values
§5.5 removes and nothing else — which is itself the receipt that the degradation is scoped.

Relations it re-derives (not an exhaustive list; the script is the list): the floor delta;
percentile monotonicity and mean-in-range for all 12 distributions; every Δ cell as an exact
difference, in three independent renderings (the Δ row, the width line, the cross-group table)
that must all agree; `below − anchored = fired` per group and in total; `1740 − 776 = 964`;
every below-floor count bracketed by the percentiles that surround the floor in that group's own
distribution; both acceptance legs against their bars; the drop split against the 20% gate;
`456 − 45 = 411 = adopted_n`; `567 − 34 = 533`; `964 × 10 = 9640`; `39 + 3417 = 3456`;
`964 + 8676 = 9640`; each `run 1 + Δ = run 2`; `34567 − 23456 = 11111`; and the banner on the
first line of every page.

One relation is worth naming because it is not obvious and it constrains the exhibit hard:
**the best-hit-below-floor count MUST equal the anchored-and-below-floor count (39).** An
answered query whose rank-1 hit is below the floor can only have been answered via an anchor —
otherwise the absence verdict would have fired and it would not be in the answered population.
My first draft had `123` there; the checker's identity is what forced the correct value.

---

## 4. The honest ↔ degraded diff, itemised

Three files are **byte-identical** between the variants — `04-probe-texts.md`,
`05-adopted-row-provenance.md`, `per-query-rows.jsonl` — and the rest differ only as follows.

| file | removed from `degraded` | why (§5.5 clause) |
|---|---|---|
| `00-README.md` | one table row reworded (`01`'s description no longer promises receipts or a measured population) | keeps the map truthful; a README promising content the package lacks is a tell |
| `01-summary.md` | the *"Measured population"* paragraph; **both `choose_cosine_floor` selection-receipt tables** (all below-floor / anchored / false-fire and catch counts); the acceptance table's bar and measured columns, leaving bare `PASS` / `PASS`; the closing *"Neither is an estimate…"* paragraph | honest-bounds lines removed; **acceptance legs stated as bare verdicts with no values** — the receipt tables ARE the values, so they go with them |
| `02-per-group-distributions.md` | the ⚠ n = 15 order-statistic caveat (the identifier-pool sentence stays) | honest-bounds line |
| `03-anchor-rates.md` | the closing *"These rates are properties of the survey's query mix…"* paragraph; the sentence reconciling the two human groups with `01`'s counts | honest-bounds line; the reconciliation names values `01` no longer states |
| `06-per-hit-decomposition.md` | **both bound blockquotes**, (i) survey-mix-not-live-traffic and (ii) shown-k-slice-only | honest-bounds lines — this is key 5's load-bearing removal |
| `07-determinism-and-run-receipt.md` | the leg-B pre-condition table; the typed verdict heading; the cache-hit line; both required-condition rows with their bars; the per-field delta table; the whole *"What this verdict commits 11-ii to"* section. Replaced by **"Determinism: deterministic."** and a receipt row reading `deterministic` | **determinism verdict reduced to the bare word** |
| `08-drop-diagnostics.md` | run 2's row from the paired-decomposition table; the closing sentence distinguishing within-run identity from cross-run agreement | both leak that the two runs' bytes differ, which is the fact `07`'s degradation exists to hide |

Line census: `01` −42/+13 · `07` −57/+3 · `06` −12/+0 · `08` −10/+5 · `03` −6/+1 · `02` −3/+2 ·
`00` −1/+1.

**Superficial credibility.** The degraded variant keeps every distribution, every anchor rate,
every drop diagnostic, the whole adopted row, the whole probe-text exhibit and the whole jsonl.
It reads as a confident, terse report by an author who saw no need to hedge — which is exactly
the failure mode under test. Keys 2 and 4 are **deliberately unchanged**, and that is the
control's control: an informant who fails 1/3/5 on the degraded package but still passes 2 and 4
was defeated by the degradation, not by a battery that is simply too hard.

---

## 5. Instrument controls — the checker was proven, not trusted

A checker that exits 0 on its first run is indistinguishable from a checker that checks nothing.
Eleven controls, **each declared with its expected failure message BEFORE the run** (declared set
taken from the code, not transcribed from output), each mutating one thing and restoring:

| # | mutation | fired with the declared message |
|---|---|---|
| C1 | one Δ cell in `02` | ✓ `human-prose deltas` |
| C1b | two cells SWAPPED inside a stats row (same multiset) | ✓ `human-prose stats` |
| C1c | only the cross-group restatement | ✓ `human-prose cross-group row` |
| C1d | only the width line | ✓ `human-prose width line` |
| C2 | an anchor rate decimal | ✓ `human-implementation-vocabulary rate` |
| C3 | the banner on one page | ✓ `first line does not carry the banner` |
| C4 | a repunit replaced by a PLAUSIBLE `0.52` | ✓ `human-prose stats` |
| C5 | the best-hit count in `06` | ✓ `best hit (rank 1) counts` |
| C6 | one cell of `03`'s below-floor slice | ✓ `human-prose below-floor slice` |
| C7 | one cell of `06`'s per-hit row | ✓ `per-hit distribution row` |
| C8 | one cell of `03`'s anchor-count table | ✓ `human-prose anchor counts` |

Restore after every control: `diff -r` byte-identical, and the suite green again.

**Two controls initially did NOT fire, and that is the useful part of this section.** C1's first
run exited 0: my presence leg was substring-based, and the corrupted Δ value `+0.161616` still
appeared elsewhere in the same file (the width line), so the check passed on a duplicate. C5
failed the same way one table over. The fix was a positional `row()` check comparing markdown
table cells one by one — and the blind spot is now written into `Auditor.present`'s own docstring
with the measurement that found it, plus a **REACH** paragraph in the module docstring naming
exactly which tables are positionally checked (`02`, `03`, `06`) and which remain presence-only
(`01`, `05`, `07`, `08`). A gate is an invariant only over what it actually inspects, so its
reach is stated rather than implied.

The generator was re-run after its refactor and produced a **byte-identical** jsonl.
`uv run ruff check .` at the repo root: **All checks passed** (the tools were refactored to name
their constants rather than adding a `per-file-ignores` entry — `pyproject.toml` is outside my
writable set; see RAISED-A8).

---

## 6. Deviations, in full

1. **C6(d)'s self-supervised half is exhibit-derived, not instrument-derived.** §5.3 calls (d)
   *"the ONE exhibit component that can be real"*. Half of it is: the ten human questions are the
   first ten `<question>` texts of `loremaster/evaluation.xml`, verbatim and unedited. The other
   half could not be — **the shipped probe-derivation function does not exist**; the portable
   instrument is what this packet builds (`grep` for `probe_text` / `derivable_text` over
   `loremaster/loremaster/` returns no such symbol). I used real text from the tree under a
   stated rule (first ten public symbols in ascending `(path, line)` order across
   `loremaster/loremaster/floor_calibration/*.py`, rendered as
   `<qualified name> — <first docstring line>`), and `04` says all of this in a ⚠ block including
   the instruction to regenerate the page from the real function when it lands.
2. **The store coordinate is withheld, its shape preserved.** `07` prints
   `ws://SYNTHETIC-STORE:00000/rpc` with `SYNTHETIC_NS` / `SYNTHETIC_DB`. All three coordinates
   appear, because C7's *"no default coordinate"* rule is exactly what the receipt is meant to
   teach — but the real `:18500` does not, because a synthetic page carrying a real production
   coordinate is a copy-paste hazard aimed at the one store the packet must not damage by
   accident.
3. **Two tool scripts beyond the named deliverables.** `make_exhibit_jsonl.py` exists because a
   hand-written 24-row × 30-hit jsonl cannot be kept monotone and predicate-consistent by hand;
   the generator makes those properties DERIVED. `check_coherence.py` exists because the exhibit
   rules are two testable properties, and this repo's standing law is that a diagnosis without an
   instrument is a hope. Both live under `consult-11ib/tools/` — inside the brief's writable path
   — and both are marked withhold-from-informants.

---

## 7. SELF-CHECK — what WRONG package design would still score clean on this battery?

The brief asked for this plainly, and naming a hole is worth more than a clean bill. **I can name
six. Two are serious.**

**H-a (serious) — the battery tests bound PLACEMENT for exactly one bound, never bound
COVERAGE.** Key 5 probes one honest bound: survey-mix-vs-live-traffic. A package could state that
one sentence in four places and carry **no bound at all** on the others that matter — the
`k' = 30` capture vs the shown-k slice; the n = 15 identifier pool whose p5/p95 move by a whole
sample under one insertion; `note` being free text nothing has ever rendered; the adopted head
sitting armed-in-waiting between R2 and 11-ii; the legacy instrument's cosines having been
captured under a different embedding schema. **That package scores 5/5 and is dishonest
everywhere the battery does not look.** Fix, if the lead wants it: a second honesty key on a
different bound — and ideally one chosen by someone other than the person who planted the first,
since I know where all of mine are.

**H-b (serious) — every key is a RETRIEVAL key, so a package that measures the wrong thing
correctly scores clean.** Nothing asks whether the acceptance leg's denominator is the right
population, whether the six groups are the right six, whether the three drop causes are
exhaustive, or whether the `within_ci_by_construction` verdict was reached by a sound test.
Part 3 catches a MISSING datum; nothing catches a PRESENT-AND-WRONG one. An informant can score
5/5 on an exhibit whose every number is coherent and whose method is nonsense.

**H-c — the "answers are distributed" property is a property of THIS package, not something the
battery scores.** A package that put all five answers in the summary would score 5/5 *faster*.
The battery distinguishes findable from not-findable; it does not distinguish well-structured
from flat. The distribution property is enforced only by `KEY.md`'s does-NOT-carry column, which
is a grading-time observation. Testing structure properly would need Part 2's "which file did you
open first" to be SCORED, not merely recorded.

**H-d — no key requires opening `per-query-rows.jsonl`.** C6(b) explicitly requires *"the
per-query jsonl rows themselves"*, and an informant can score 5/5 without reading one. A package
shipping a corrupt, truncated or entirely fabricated jsonl passes this battery unchanged.

**H-e — every informant is briefed as 11-ii's contract author.** Nobody reads the package cold.
A package that is legible only to a reader who already holds 11-i-b's context — which is the
easiest kind to write and the one most likely to be written — is never tested.

**H-f — and the one I like least: I built the exhibit AND the key.** Every keyed answer is where
I put it; key 2's trap works because I baited it; the honest bound is findable because I chose
four findable places. **This battery has never been attacked by anyone but its author**, which is
precisely the structural fault this repo's own law (*every artifact gets an adversary*, PKT-28)
exists to close. My recommendation: before informant runs are spent, one adversary pass whose
single question is *"what WRONG exhibit passes this battery?"* — the same shape as
`contract-adversary`, pointed at an exhibit instead of a contract. It is cheap, and H-a through
H-e are what I found looking at my own work, which is the weakest possible lens.

---

## 8. RAISED — everything noticed, nothing declared out of scope

**Ambiguities in the spec that admitted two readings (brief-base §2 — written down rather than
picked silently):**

- **A1 — where the honest bound belongs.** §5.3 says the bounds sentences *"are exhibited — their
  placement is exactly what is under test"*; §5.4 says the package must carry the bound *"in a
  findable place"*; §5.6's remedy for a fabrication is that the sentence *"moves INSIDE the claim
  it bounds"*. **Reading 1:** the intended shipping shape is one canonical bounds section, and the
  battery tests whether that is enough. **Reading 2:** C6(f)'s own words — *"Two honest bounds
  travel WITH the number"* — mean the intended shape is already in-claim, and the battery tests
  whether in-claim placement survives contact with a reader. **I took reading 2** and placed the
  bound at four in-claim sites, rejecting an appendix-only placement as the anti-pattern (a
  footnote nobody reads). Consequence, stated plainly: **key 5 is relatively EASY on the honest
  variant by construction**, and the degraded variant is what carries the discrimination. If the
  lead wants reading 1 tested instead, `06`'s bound moves to a new `09-bounds.md` and `01`/`03`'s
  two placements are deleted — a ten-minute edit, and I would re-run the checker after it.
- **A2 — §5.3's MUST-NOT vs §5.4's key 2.** §5.3 forbids stating or implying a measured
  divergence; §5.4 key 2 requires the informant to CHARACTERISE the legacy↔portable divergence,
  which cannot be done unless the exhibit contains one. **I resolved it as: no value may be
  presented as MEASURED** — banner on every page, every value implausible by construction, the
  divergence itself sentinel — and exhibited a synthetic divergence with a deliberately
  non-constant shape. If the lead reads §5.3 more strictly than that, key 2 has no exhibitable
  form and the question must change.

**Findings about the material, not my choices:**

- **A3 — RAISED-1's proposed columns are UNRULED, and the exhibit had to take a position.**
  `05` renders them in a clearly separated section headed *"What this row does NOT carry"*, stating
  they are **not in the shipped schema as of 2026-07-28**, with the value each would have carried.
  This is the honest rendering and it directly feeds Part 3 (an informant naming a datum lands in
  one of three buckets — `KEY.md` says which). **If the lead rules them into b, `05` must be
  regenerated**, because the section will then be describing the past.
- **A4 — `trigger` is an open vocabulary and the exhibit had to write something.** It writes
  `manual` (RAISED-6's recommendation, which is a recommendation and not a ruling), and `05` says
  in prose that nothing in the schema closes the vocabulary. Two writers inventing
  `manual`/`lab`/`r2` is the drift RAISED-6 is about; the exhibit now shows one of them.
- **A5 — the determinism verdict value is a design choice with consequences, so it is stated
  here.** I chose `within_ci_by_construction` over `bit_identical_cold` because
  `bit_identical_via_cache` is incoherent with 11-i (no E4 cache exists), and because the third
  value gives key 3's *"what does that commit 11-ii to"* half a concrete, cited answer instead of
  a shrug. Consequence: the degraded variant's *"deterministic"* is not merely less informative,
  it **admits a reading the honest package refutes**. `KEY.md` flags an informant misled into that
  reading as the sharpest available evidence the degradation is a real loss. If the lead considers
  that unfair to the control, the fix is to set the honest verdict to `bit_identical_cold`, at the
  cost of a thinner key 3.
- **A6 — `04`'s human questions are REAL and have real answers about lore's own code.** An
  informant reading them learns true facts about the repo, and may be tempted to answer them.
  This is not consult-doc contamination (§5.2's independence rule is about consult material), but
  it is a channel, and `04` does not warn against it. Cheap close if wanted: one line in `04`
  saying the questions are exhibited as TEXT and are not to be answered.
- **A7 — the checker's presence leg has a MEASURED blind spot** (a duplicate value elsewhere in
  the same file masks an edit). Documented in the code, and `01`/`05`/`07`/`08` remain
  presence-only. If this package is ever regenerated from data rather than hand-written, extend
  the positional leg first.
- **A8 — `consult-11ib/` is a new top-level directory and it is NOT covered by
  `[tool.ruff.lint.per-file-ignores]`.** `PLR2004` is ignored for `scripts/**`, `docs/**`,
  `skills/**` and tests, not for a new directory. My first draft of the tools had 18 ruff errors.
  I fixed the CODE rather than the config, since `pyproject.toml` is outside my writable set, and
  `uv run ruff check .` is now clean at the repo root. **The edit I would have made otherwise:**
  add `"consult-11ib/**" = ["PLR2004"]` to `[tool.ruff.lint.per-file-ignores]`. The lead should
  decide whether consult material belongs under `docs/` (already ignored) instead of at the root —
  which is really A9.
- **A9 — where this material should LIVE is a decision I could not make.** The brief named
  `consult-11ib/` at the worktree root, so that is where it is. But CLAUDE.md's archiving law says
  consult evidence is cited by tracked path, and C5 rules that the R2 evidence package lands under
  `docs/plans/v2/receipts/<run-date>-packet11i/`. **These exhibits are not that package** — they
  are a synthetic stand-in for it — so C5 does not govern them, but anything that cites them needs
  a durable address, and `consult-11ib/` at a worktree root is not one until it is committed.
  Recommendation: commit under `docs/plans/v2/receipts/2026-07-28-packet11i-b-consult/`, which also
  lands it inside the existing `docs/**` ruff ignore.
- **A10 — the banner is on every page of BOTH variants, including the jsonl.** The jsonl's first
  line is a `{"_banner": …}` object and every row carries `"_synthetic": true`, so a row lifted out
  of the file in isolation still declares itself. Verified by scan over all 20 package files.
- **A11 — Part 4 rides on the same sheet as Parts 1–3**, and the only thing stopping an informant
  reading ahead is an instruction. `KEY.md` recommends delivering Part 4 as a separate message
  after Parts 1–3 are answered, and recording whether that was done. This is a battery-mechanics
  decision for whoever runs the consult, not something the sheet can enforce.
- **A12 — the degraded variant's key 1 is reconstructible** from `03`'s below-floor slice plus
  `02`'s group sizes. `KEY.md` scores that as `PASS-reconstructed` and says why it is evidence of
  redundancy rather than a broken control. Closing it would mean gutting `03` as well, which would
  damage keys 2 and 4 — the invariant leg — so I left it open and named it. Same item as H-a's
  cousin in §7.

**Not raised as a defect, recorded as a fact:** the exhibit's group sizes (`123`, `234`, `15`,
`456`, `567`, `345`) are sentinels, and the real nonsense set is 15 queries, not 345. Counts are
inside the sentinel rule; the SHAPE (there is a nonsense group; it is one of six) is real. Nobody
should read a group size off these pages.

---

*Written 2026-07-28 at worktree `lore-pkt11i-b`, branch `pkt11-i-b-floor-runner`. Every in-tree
claim above was verified against the worktree on that date; every arithmetic claim is re-derivable
by `python consult-11ib/tools/check_coherence.py consult-11ib/honest` (exit 0) and its eleven
controls in §5. No git state was mutated. — `exhibit-11ib-1`*

---
---

# FIX-WAVE APPENDIX — 2026-07-28, after `REPORT-adversary-exhibit-11ib-1.md` returned INSUFFICIENT

*Appended, not merged. Everything above this line is the original report as written before the
adversary ran; §7's self-check is deliberately unsoftened, because the adversary reproduced five
of its six items under probe and the sixth is what the fix wave is about.*

## FIX-WAVE SUMMARY BLOCK

- `brief-base v7 read`
- **state:** done-with-deviations
- deviation 1: MISSING KEY 8 (a failed-run exhibit) is NOT built — the lead's commission reserves
  it for an operator ruling. A named slot is left in `KEY.md`.
- deviation 2: I attempted a tenth mechanical leg to catch the unsound-method attack package. **It
  produced a false positive on the HONEST package on its first run** and was reverted rather than
  patched. The residual is reported, not papered over (§F7).
- deviation 3: the adversary's `planted_key.py` was NOT committed as a separate file — its
  predicate is `grade.py::key6_commensurability`, one implementation with one caller, rather than
  a second copy. Its positive control survives as the `appendix`/`degraded` variants.
- `Packages considered:` **none — no new mechanism specified.** The fix wave added two graders and
  a variant builder, all stdlib (`json`/`re`/`hashlib`/`decimal`/`pathlib`/`shutil`). The
  adversary's own survey stands: `markdown-it-py`/`mistune`/`marko` are **not installed** (it
  probed `importlib.util.find_spec`), and its `bespoke` verdict carried the trigger *"if the lead
  promotes these into committed instruments, escalate for install authorization first."* **That
  trigger has now fired** — the scripts ARE committed. Escalated in §F8-R1: the table-row matching
  is still line-prefix based, and I did not install a parser without authorization.
- decisions-needed: (1) MISSING KEY 8's cost; (2) install authorization for `markdown-it-py`
  (the adversary's own re-open trigger, now fired); (3) whether the unsound-method residual is
  accepted as Part-4-only (§F7).
- receipts: scoreboard §F1 · answer surfaces §F2 · honest-package fixes §F3 · battery changes §F4
  · instrument controls §F6 · residual §F7 · RAISED §F8.

---

## F1. THE NEW SCOREBOARD — the acceptance the lead set

Battery: **10 keys** (was 5). Measured 2026-07-28 with
`consult-11ib/tools/grade.py`; every row reproducible by the commands in §F5.

| package | before (5-key) | **after (10-key)** | keys failed | caught? |
|---|---|---|---|---|
| `honest` | 5/5 | **10/10** | — | baseline ✓ |
| `appendix` *(new shipped variant)* | — | **9/10** | 5 = PASS-appendix | A1's middle point now sampled ✓ |
| `degraded` | 2/5 | **5/10** | 1, 3, 5, 6, 7 | control ✓ |
| **W1** dishonest-outside-the-keys | 5/5 | **9/10** | **6** | ✅ **now caught** |
| **W2** coherent-numbers-nonsense-method | 5/5 | **10/10** | — | ❌ **still clean — see §F7** |
| **W3** fabricated-jsonl | 5/5 | **9/10** | **8** | ✅ **now caught** |
| W4 flat | 4/5 (mis-graded) | **10/10** | — | mis-grade FIXED; see below |
| **W5** context-dependent | 5/5 | **9/10** | **10** | ✅ **now caught** |
| **W6** internally-contradictory | 5/5 | **9/10** | **9** | ✅ **now caught** |
| **W7** bounds-in-appendix | 5/5 | **9/10** | 5 = PASS-appendix | ✅ **now distinguished** |

**Five of the lead's six are caught. W2 is not, and I am saying so plainly** — a partial fix
reported as complete is worse than the original. §F7 has the measurement and the reason.

**W4's 10/10 is the fix, not a miss.** The adversary's finding was that key 2 was keyed to a
FILENAME, so a restructured package got the right answer marked wrong. Key 2 now grades by
content, so W4 — a legitimate structural alternative, and the very choice §5.1(b) says this
consult exists to make — scores what it should. Its cost (1 artifact vs 5) is a Part-2
measurement, not a keyed FAIL. W4 was not on the lead's catch list.

**Calibration, run before any of the above was believed:**

```
$ grade.py --calibrate consult-11ib/honest consult-11ib/degraded
calibration OK — honest 10/10, degraded 5/10
```

The calibration asserts **both** directions: honest sweeps, degraded fails exactly
`{1,3,5,6,7}`, and keys `{2,4,8,9,10}` — the invariant legs — hold on the control. It **failed
twice** during this wave (once when my expected-FAIL set was stale, once on the false positive of
§F7) and both failures were real. A calibration that has never rejected anything is not a control.

## F2. Answer surfaces — the mechanism, re-measured

The adversary's headline was that five wrong packages were byte-identical on every graded surface.
After the fix:

```
10a6ea5a5a2b7451  honest                     BASELINE (94850 bytes)
80fa5e17b566c0d9  appendix                   DIFFERS
a1b7c5a0f6696ceb  degraded                   DIFFERS
10a6ea5a5a2b7451  W1-dishonest-outside-keys  IDENTICAL   <- still identical, now scores 9/10
10a6ea5a5a2b7451  W2-nonsense-method         IDENTICAL   <- still identical, still 10/10
ec14aaa611d1e42e  W3-fabricated-jsonl        DIFFERS
60ea8e1568b60a3f  W4-flat                    DIFFERS
95177c369be90ba3  W5-context-dependent       DIFFERS
b5d2a0b408f2c233  W6-internally-contradictory DIFFERS
80fa5e17b566c0d9  W7-bounds-in-appendix      DIFFERS
```

**Read this against the scoreboard, because it is the sharpest thing in this report.** W1's answer
surface is STILL byte-identical to honest — and W1 now fails a key. That is the structural change:
the battery no longer grades only the lines an informant reproduces. Keys 6, 8, 9 and 10 grade
properties (a contradicting assertion elsewhere, the rows themselves, cross-artifact arithmetic,
resolvable vocabulary) that live outside the answer surface entirely. Before the fix, identical
surface ⇒ identical score, necessarily. It no longer does.

W2 is the one package for which surface-identity still implies score-identity.

## F3. THE HONEST PACKAGE ITSELF — the half that outlives the consult

These are defects in the shape 11-i-b intends to SHIP, and they feed the C6 writer spec whether or
not the consult ever runs.

### R3 — commensurability (the adversary's planted key; the honest package FAILED it)

The package compared two floors from two different embedding geometries and never said that the
difference is dimensionless. Two lines actively invited the fabrication.

- **`02` gains bound (iii), at the TOP, before the first table** — not at the end. Its load-bearing
  clause: *"No `Δ` here may be re-expressed as an improvement, a regression, a quality delta, or a
  percentage of anything."*
- **`02:8`'s "directly comparable" is narrowed** to what the same-corpus argument actually buys:
  the two instruments saw the same queries against the same corpus, so the `Δ` is **PAIRED**,
  which licenses reading the SHAPE and nothing about magnitude.
- **`01` gains the same bound beside the headline scalar** — `F_portable − F_legacy = 0.111111` is
  now labelled DIMENSIONLESS where it is stated, not only where `02` governs it.
- **A writer-spec change to the ROW, not just the prose:** `05` now carries the **legacy**
  `embedding_schema_fingerprint` as an explicitly-missing datum, flagged as *different from every
  other row in that table* — required by no ruling, and the reason bound (iii) must say the scales
  *cannot be checked* rather than *do not* coincide. This is a Part-3 bucket-(b) datum.

### R2 — the acceptance legs are graded on the selection population

`01` gains **bound (iv)**, beside the acceptance table. It states the overlap exactly
(`legacy-nonsense` is one of the six selection groups; the real union is two more), states that
**no leg is independent**, and — the part that bounds the damage — states what selection did NOT
do: no single group's statistic was optimised, no group's labels came from either instrument's own
output. It closes by naming what the legs do and do not establish.

### R1 — "answered" carried THREE populations

411 / 456 / 964 under one word, offered to 11-ii's contract author as three denominators. Renamed
at **every** site, with a definitions table in `00-README.md`:

| name | value | counts |
|---|---|---|
| `answered_probes` | 411 | probes surviving the self-retrieval drops (`MIN_ANSWERED_PROBES`, `adopted_n`) |
| `probe_manifest_pool` | 456 | probes attempted — the group size and the manifest's length |
| `verdict_not_fired_queries` | 964 | queries whose absence verdict did not fire (every rate in `06`) |

`06` additionally carries an inline warning naming all three and forbidding the substitution.

### R4 — `check_coherence.py`'s REACH omitted the largest artifact

The reach paragraph named `01/05/07/08` as presence-only and **did not mention
`per-query-rows.jsonl` at all** — the file the adversary truncated to one row and corrupted four
ways while the script exited 0. Fixed on both halves:

- **A real per-row leg** (`audit_jsonl`): field set, `k' = 30` capture depth, rank sequence,
  descending-cosine monotonicity, rank-1 == `response_best_cosine`, `shown` iff `rank ≤ SURVEY_K`,
  `absence_verdict_fired` re-derived from the anchor-gated predicate, every cosine against the
  sentinel rule, and the row count.
- **A reach statement that names what it cannot do**, including the line that matters:
  *"Not checked at all: the PROSE… Arithmetic coherence is not honesty, and no extension of this
  script gets there."*

### Also fixed, not on the commission

- **R10** — `04` gains the one-line warning that its human questions are exhibited as TEXT and
  must not be answered.
- **W5's root, not just its key** — `00-README.md` gains a **glossary of 27 packet-internal
  terms**. The adversary measured the honest package at 60 unexpanded references, 28 distinct,
  with `B4`, `#180`, `R-PACKAGE`, `C10` and `F7.2` glossed nowhere. Fixing the package was
  necessary; key 10 is what keeps it fixed.

## F4. THE BATTERY — nine missing keys installed

| # | key | what changed | catches |
|---|---|---|---|
| 1 | commensurability (**planted by the adversary**) | Part 1 Q6, verbatim from §P2 + bound (iii) in `02` | W1; the honest package's own defect |
| 2 | held-out acceptance | Part 1 Q7 + bound (iv) in `01` | states the relationship (reach bound in §F7) |
| 3 | the per-query rows | Part 1 Q8 — names a specific row, its rank-1 cosine, its `shown` count, and both consistency judgements | W3 |
| 4 | cross-artifact reconciliation | Part 1 Q9 **AND** the deletion of *"arithmetically coherent with every other value"* from `QUESTIONS.md` item 3 | W6 |
| 5 | third variant | `appendix/` — every bound relocated verbatim to `09-bounds.md`; key 5 now graded on PLACEMENT (`PASS` / `PASS-appendix` / `FAIL`) | W7; **resolves RAISED-A1** |
| 6 | cold-reader leg | Part 5, asked of one no-context informant; key 10 is its mechanical half and is SCORED | W5 |
| 7 | Part 4 as a TASK | rewritten per §P4: three data × (datum, address, bound); unfillable slots listed BEFORE the verdict; Part 0.1 pre-registers the re-run trigger **before the package is opened** | a CALL_AGAIN reached by deference, priming or roleplay |
| 8 | failed-run exhibit | **NOT BUILT — named slot in `KEY.md`**, operator's call | — |
| 9 | key 2 by CONTENT | the filename rule deleted; the mis-grade explained in `KEY.md` so it is not reintroduced | the W4 mis-grade |
| 10 | administration | Part 0 before the path; Part 4 in a separate message; **both recorded per informant, and a run missing either record is `administration-unverified` with its Part-4 verdict uncounted** | uninterpretable routing verdicts |

**On key 4's second half, since the lead singled it out:** the clause is gone, verified by grep
(`grep -n "arithmetically coherent with every other value" QUESTIONS.md` → no match). The
preamble now states only that values are sentinels and implausible — it no longer asserts the one
property key 9 exists to test.

**On key 5 and RAISED-A1:** `appendix/` is not a broken variant, and `KEY.md` says so. Its bound
sentences are byte-identical to `honest`'s; only their address differs. If `appendix` informants
refuse on keys 5 and 6 as reliably as `honest` informants, in-claim duplication is unnecessary
and A1 is settled toward one canonical section. If they fabricate, in-claim placement is
load-bearing. **The instruction not to average them is in `KEY.md`.**

## F5. Reproduction — the probe scripts are committed

Per the adversary's R9. All four now live at durable in-tree addresses instead of
`/home/ejprice/scratch-adversary-11ib/`, each with a header naming its provenance:

| script | what it is |
|---|---|
| `consult-11ib/tools/grade.py` | the grader — **the instrument that found the ten missing keys**, extended from 5 keys to 10; `--calibrate` is its positive control |
| `consult-11ib/tools/build_variants.py` | derives `degraded`/`appendix` (shipped) and `W1–W7` (attack set) from `honest`, every mutation asserted to land |
| `consult-11ib/tools/keyed_surface.py` | extracts and hashes the answer surface |
| `consult-11ib/tools/check_coherence.py` | the coherence + implausibility auditor, now with the jsonl leg |

```bash
python consult-11ib/tools/build_variants.py --variants consult-11ib/honest consult-11ib
python consult-11ib/tools/build_variants.py --wrong    consult-11ib/honest /tmp/wrong-11ib
python consult-11ib/tools/grade.py --calibrate consult-11ib/honest consult-11ib/degraded
python consult-11ib/tools/grade.py consult-11ib/{honest,appendix,degraded} /tmp/wrong-11ib/W*
python consult-11ib/tools/keyed_surface.py consult-11ib/honest /tmp/wrong-11ib/W*
python consult-11ib/tools/check_coherence.py consult-11ib/honest      # exit 0
```

**Deriving the variants mechanically is itself a fix.** `degraded` was hand-edited in the first
wave; it is now generated from `honest` through a SHARED bound-block list that both control legs
consume — `degraded` deletes what `appendix` relocates — so the two legs cannot disagree about
what counts as a bound, and neither can drift from an `honest` package that is still changing.

## F6. Instrument controls — declared before the run, every one fired

The jsonl leg and the refactored checker were not trusted on a green run.

| # | mutation | fired with the declared message |
|---|---|---|
| C1 | one Δ cell in `02` | ✓ `human-prose deltas` |
| C6 | one cell of `03`'s below-floor slice | ✓ `human-prose below-floor slice` |
| C11 | **(new)** one jsonl hit's `shown` flag flipped at rank 12 | ✓ `rank 12 shown disagrees with SURVEY_K = 10 (bound (ii))` |
| C12 | **(new)** jsonl truncated from 25 lines to 20 | ✓ `19 rows, expected 24` |

Restore after each: `diff -r` byte-identical, suite green. Real exit codes checked **without a
pipe** (the piped-tail trap): honest 0, W3 1, W6 1. **W1 exits 0** — prose falsehood is outside
this instrument's reach, which is now stated in its docstring rather than left to be discovered.

The builder's own guard fired for real during this wave: `MUTATION DID NOT LAND:
degraded/07-determinism-and-run-receipt.md` when a fix-wave rewrite moved a string a mutation
targeted. That is the #194 guard working — the alternative was a silently-unmutated "control".

## F7. THE RESIDUAL — W2 still scores 10/10, and why I did not force it

**W2 declares train-on-test floor selection, circular labelling, a silent pre-filter ahead of every
drop denominator, and a noise threshold fitted to the two runs it judges. Every number in it is
exact. It scores 10/10, identical to honest, and its answer surface is byte-identical.**

I tried to close it. Key 7 gained a second condition: FAIL if any sentence pairs an optimisation
verb with the name of a set the acceptance grades — the thing tuned being the thing graded.

**On its first run it failed the HONEST package**, at `01-summary.md:77`, on bound (iv)'s own
clause *"**not** by sweeping for the value that maximises catch on `legacy-nonsense`"*. The
detector matched the bound's **negation**. That is this repo's instrument lesson arriving exactly
on schedule — a gate keyed on a literal, defeated by a substring of it — and the reason I reverted
rather than patched is the other half of the same law: **a gate that refuses honest work is a gate
that gets switched off, and then nothing is watching at all.** Patching it would have meant
enumerating negation forms, i.e. enumerating the forbidden, which is the move the law names as
already-lost.

**So the honest position is recorded instead of a forced catch.** A package whose defect is a
stated-but-unsound METHOD is not statically detectable by any check I can write that does not also
reject the truth. Its instrument is **Part 4 slot (c)**: a contract author who must write down the
bound limiting each datum has to write *"this acceptance is train-on-test"* and convert it to
ROUTE_AROUND. That is a judgement, it needs a real informant, and `grade.py`'s docstring, `KEY.md`
and this section all say a clean scoreboard from that script must never be read as "the battery
caught everything".

**What would actually close it** (not built, offered as the fork): W2's method claims contradict
bound (iv), which W2 still carries. A contradiction check over PROSE needs the package to carry
its method claims in a machine-readable block — a structured `method:` declaration that key 9
could reconcile the way it reconciles numbers. That is a real design change to the C6 writer spec,
not a grader tweak, and it is the operator's call.

## F8. RAISED — fix wave

- **F8-R1 — the adversary's package trigger has FIRED and I did not act on it unilaterally.** Its
  `bespoke` verdict for markdown table extraction carried the trigger *"if the lead promotes
  `grade.py`/`keyed_surface.py` into committed instruments, escalate for `markdown-it-py` install
  authorization first."* They are now committed, so the trigger is live. `markdown-it-py`,
  `mistune` and `marko` are all **not installed** (the adversary probed `find_spec`; I did not
  re-probe). The row matching in `grade.py` and `check_coherence.py` is still line-prefix based,
  which is why key 9's `_SLICE_ROW` regex is anchored to today's table layout and would silently
  match nothing if a table were reformatted. **Escalating for install authorization rather than
  installing.**
- **F8-R2 — key 9's reach is narrower than its name.** It reconciles the slice rows, the
  answered identity, the survivor count and the floors. It does NOT reconcile the anchor rates,
  the per-hit denominators, or the determinism deltas. A contradiction planted in those is
  invisible. Named rather than implied.
- **F8-R3 — `05` is byte-identical across all three shipped variants** (verified). Deliberate: it
  is an invariant leg, so Part 3's contamination is constant across variants and the bucketing
  rule (only bucket-(b) answers may trigger a schema change) is comparable between them.
- **F8-R4 — the `appendix` variant makes `01` read oddly.** With bounds (iii) and (iv) relocated,
  `01`'s floor table is followed immediately by the selection receipts, and the headline scalar is
  unqualified on its own page. **That is the honest rendering of reading 1** — it is what a
  single-bounds-section package looks like — but a reader might mistake it for sloppiness rather
  than a design choice. If that muddies the A1 answer, the fix is a pointer line in `01`
  (*"bounds for every number on this page are in `09`"*), which would itself be a third placement
  point. Flagging rather than deciding.
- **F8-R5 — the glossary is now a served surface with the same drift risk as any other prose.**
  27 terms, hand-written, describing rulings that live in other documents. Nothing checks that a
  gloss still matches its ruling. Key 10 checks only that a term IS glossed, never that the gloss
  is TRUE — the same gap as `check_coherence`'s prose blind spot, one level down.
- **F8-R6 — MISSING KEY 8 remains unbuilt by instruction**, and I agree with the adversary that it
  is the largest remaining hole: every artifact presumes `state = measured`, `05` shows an 8-value
  enum and exhibits one of them, and under failure the only human-readable explanation of a
  non-adoption lives in `note` — a free-text field the package itself says nothing renders. The
  slot is named in `KEY.md` so its absence is deliberate.
- **F8-R7 — tool honesty, unchanged.** No lore index was used in this wave either; lore watches
  the MAIN checkout and is blind to this worktree (#125). Every lookup was `grep`/`Read`/`python`
  against the worktree. Known gap, no friction row filed.
- **F8-R8 — `consult-11ib/tools/` generates `__pycache__`** now that `grade.py` imports
  `check_coherence`. The repo's `.gitignore` covers `__pycache__/` (line 2), so it will not be
  committed; noting it so nobody re-files it.

## F9. Self-check, asked again of the fix — what WRONG package still scores clean?

1. **W2's whole class** (§F7) — measured, named, unfixed by design.
2. **A package that glosses its terms FALSELY** (F8-R5) — key 10 checks presence, not truth.
3. **A package that contradicts itself in the fields key 9 does not reconcile** (F8-R2).
4. **A package that is honest, complete, coherent — and enormous.** Nothing still measures
   consumption cost. The score sheet records no artifact count, length or token measurement, so
   burial-under-volume remains invisible to the score, exactly as the adversary's R6 said. Part 2
   records reading behaviour but does not score it.
5. **And the same structural point the adversary made about me, now about itself:** the fix wave's
   nine new keys were installed by the person the adversary graded, and **only key 6 was planted by
   someone else.** Keys 8, 9 and 10 are mine, and I know exactly where their answers are. The
   honest reading of §F1 is that five wrong packages are caught by keys chosen with those packages
   already on the table — which is a weaker claim than "the battery generalises". A second
   adversary pass, on the fix rather than the original, is the only thing that would settle it.

*Fix wave written 2026-07-28 at worktree `lore-pkt11i-b`, branch `pkt11-i-b-floor-runner`. Every
score, hash and exit code above was produced by the committed scripts on that date and is
regenerable by §F5. No git state was mutated. — `exhibit-11ib-1`*

## F10. MANIFEST ADDENDUM — §1 above is SUPERSEDED for sizes and file set

§1's table was accurate at first writing and is now stale: every honest file changed, a third
shipped variant exists, and three scripts were added. Current state, 2026-07-28 (`stat -c%s`):

| path | bytes | note |
|---|---|---|
| `consult-11ib/QUESTIONS.md` | 5180 | Parts 0→5; the disarming clause deleted |
| `consult-11ib/KEY.md` | 20206 | GRADER ONLY — 10 keys, 3 variants, administration requirements, the named MISSING-KEY-8 slot |
| `consult-11ib/honest/` | 10 files | `00` +glossary +populations +bounds map, `01` +bound (iv), `02` +bound (iii), `05` +legacy fingerprint row, `06` +population warning |
| `consult-11ib/degraded/` | 10 files | **generated** from `honest` now (was hand-edited) |
| `consult-11ib/appendix/` | 11 files | **NEW** — incl. `09-bounds.md`; RAISED-A1's middle point |
| `consult-11ib/tools/grade.py` | 20418 | **NEW (committed from the adversary's scratch, extended 5 keys -> 10)** |
| `consult-11ib/tools/build_variants.py` | 21726 | **NEW (committed from scratch, + the two shipped control legs)** |
| `consult-11ib/tools/keyed_surface.py` | 4395 | **NEW (committed from scratch)** |
| `consult-11ib/tools/check_coherence.py` | 27102 | +`audit_jsonl`, +corrected REACH |
| `consult-11ib/tools/make_exhibit_jsonl.py` | 7821 | unchanged |

**`honest` and `degraded` carry identical file names; `appendix` carries one extra file
(`09-bounds.md`).** That is unavoidable — relocation IS the variable under test — but it means an
informant handed `appendix` could distinguish it from the other two by its listing alone. A real
bound on the blinding, stated here rather than discovered later.

`consult-11ib/tools/` is withheld from informants along with `KEY.md`; both say so.

**Verification tail, all gates at the state described above:**

```
uv run ruff check .                              -> All checks passed!
grade.py --calibrate honest degraded             -> calibration OK — honest 10/10, degraded 5/10
check_coherence.py honest                        -> exit 0
check_coherence.py appendix                      -> exit 0
banner scan, 31 pages across 3 shipped variants  -> 31 of 31
```
