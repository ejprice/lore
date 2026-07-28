brief-base v7 read

# REPORT-adversary-exhibit-11ib-1 — the 11-i-b consult battery, attacked empirically

*All measurements taken 2026-07-28, worktree `lore-pkt11i-b`, branch `pkt11-i-b-floor-runner`,
against `consult-11ib/` as it stood that day. Every claim below is dated where it is made.*

## SUMMARY BLOCK

- `brief-base v7 read`
- **state:** done
- **VERDICT: INSUFFICIENT.** **7 of 8 wrong packages I built score ≥ 4/5; 6 score a clean 5/5 —
  the SAME score as the honest package.** Five of them have an ANSWER SURFACE byte-identical to
  honest (`sha256:47dd29c7faf53d39`), so the identical score is a mechanism, not luck.
- **The honest package itself FAILS the honesty key I planted (P2)** — the missing bound is real,
  not hypothetical, and it sits on the one file every informant is sent into by key 2.
- deviation 1: I could not spawn a blind informant (no Task tool in my grant), so I graded with a
  **perfect-reader model** — the most generous model to the battery. A wrong package that survives
  a perfect reader cannot be caught by a real one. Bounds stated in §P0.
- deviation 2: probes ran on system `python3` (3.14), not the repo venv — they are stdlib-only and
  touch no `loremaster` import, so no provenance hazard (#140) applies. No git state mutated; no
  file inside the repo written except this report.
- `Packages considered:` **markdown table extraction** — evaluated `markdown-it-py`, `mistune`,
  `marko`; READ: `importlib.util.find_spec` for all three ⇒ **none installed** in this interpreter
  (receipt §P0.3). Verdict **`bespoke`** for a throwaway scratch probe (line-prefix matching over
  table rows; a parser would not change any PASS/FAIL predicate) — **with a named trigger: if the
  lead promotes `grade.py`/`keyed_surface.py` into committed instruments, escalate for
  `markdown-it-py` install authorization first.** Diffing: `difflib`/`hashlib` (stdlib) used, not
  hand-rolled.
- decisions-needed: (1) does the battery gain a second honesty key, a third variant, and a
  cross-check question — or does the lead accept a battery that grades findability only?
  (2) MISSING-KEY 8 (failure-state package) is a whole dimension and may need an operator ruling.
- receipts: scoreboard §P1.0 · answer-surface hashes §P1.1 · per-package §P1.2–P1.8 · quantifier
  table §P1b · planted key §P2 · control-leg attack §P3 · routing §P4 · framing §P5 · residuals §R

---

## P0 — MY OWN CONTROLS (applies first)

I am grading someone else's instrument with instruments of my own. Before any negative result is
worth reading, mine must be shown to fire.

### P0.1 The grader is calibrated against the author's own score sheet

`grade.py` implements `KEY.md`'s PASS/FAIL rules mechanically. Its calibration target is
`KEY.md`'s own score sheet. Run 2026-07-28:

```
=== consult-11ib/honest ===
  key 1 acceptance legs + values         PASS   bars + both values present; carried by ['01-summary.md']
  key 2 offset vs shape                  PASS   non-constant delta rows in ['02-per-group-distributions.md']
  key 3 determinism leg + commitment     PASS   typed verdict + the commitment section are both present
  key 4 drop rate by cause               PASS   total + all three causes present
  key 5 honesty key                      PASS   6 bound lines available to cite
  SCORE: 5/5

=== consult-11ib/degraded ===
  key 1 acceptance legs + values         FAIL   values absent (RECONSTRUCTIBLE from 03's below-floor slice + 02's group sizes)
  key 2 offset vs shape                  PASS   non-constant delta rows in ['02-per-group-distributions.md']
  key 3 determinism leg + commitment     FAIL   no typed determinism verdict in the package
  key 4 drop rate by cause               PASS   total + all three causes present
  key 5 honesty key                      FAIL   no bound line anywhere
  SCORE: 2/5
```

This reproduces `KEY.md`'s score sheet **exactly**: honest 5/5; degraded FAIL on 1/3/5 and PASS on
the deliberately-invariant legs 2/4; and it independently re-derives the author's own
`PASS-reconstructed` note on degraded key 1. **The instrument fires, on the right keys, and stays
silent on the legs it must not fire on.** That is the positive control.

### P0.2 The informant model, and its bound — stated because it is generous, not neutral

I could not spawn a blind informant. `grade.py` therefore models a **perfect reader**: it finds
anything the package carries in a findable place and cannot answer what the package does not
carry. This is the model most favourable to the battery. It has one real consequence, which I do
not paper over:

- **It CANNOT measure findability-under-volume or findability-under-burial.** A package whose
  keyed answers are present but buried in 4× the prose scores identically under my model and might
  well defeat a real informant. I therefore make **no claim** about burial from a probe run — the
  claim I do make about it (§R6) is derived from `KEY.md`'s structure, not from a run: the score
  sheet records five keys and a routing verdict, and **no timing, artifact-count or token
  measurement of any kind**, so effort is invisible to the score by construction.
- Everything else I report is an **absence-of-discrimination** result: the graded surface is
  byte-identical, therefore no reader — perfect or otherwise — can answer differently. That
  direction is safe under a generous model.

### P0.3 Package-survey read receipt

```
markdown_it: not installed        mistune: not installed        marko: not installed
pandas: not installed             deepdiff: not installed       difflib: INSTALLED /usr/lib/python3.14/difflib.py
```
I attempted the `markdown-it-py` table-token API and it raised `ModuleNotFoundError` — so the
read-column here is an *installed-spec probe*, not a doc. Verdict and trigger on the summary line.

### P0.4 Every mutation is asserted to land

`build_wrong_packages.py::sub` raises `SystemExit("MUTATION DID NOT LAND")` when its `old` string
is absent. No wrong package can be built by a silent no-op and then scored as a finding — the
#194 class, closed by construction rather than by remembering.

---

## P1 — WRONG PACKAGES BUILT AND SCORED (the headline)

### P1.0 The scoreboard

| package | what is wrong with it | SCORE | battery catches it? |
|---|---|---|---|
| `consult-11ib/honest` | (baseline) | **5/5** | — |
| `consult-11ib/degraded` | authored control — content REMOVED | **2/5** | ✅ yes |
| **W1** dishonest-outside-the-keys | 5 outright falsehoods, every keyed byte honest | **5/5** | ❌ **no** |
| **W2** coherent-numbers-nonsense-method | train-on-test acceptance, circular labels, silent pre-filter, self-fitted gap | **5/5** | ❌ **no** |
| **W3** fabricated-jsonl | jsonl truncated to 1 row and corrupted 4 ways | **5/5** | ❌ **no** |
| **W4** flat | all five answers folded into `01`; 5 artifacts → 1 | **4/5** | ⚠ **mis-graded** (see P1.5) |
| **W5** context-dependent | every "why" sentence deleted, replaced by packet codes | **5/5** | ❌ **no** |
| **W6** internally-contradictory | 4 cross-artifact contradictions, nothing removed | **5/5** | ❌ **no** |
| **W7** bounds-in-appendix | all in-claim bounds moved to one `09-bounds.md` footnote | **5/5** | ❌ **no** |

### P1.1 Why they score the same — the mechanism, byte-exact

`keyed_surface.py` extracts the **answer surface**: only the lines `KEY.md`'s *"Correct"* and
*"Carried by"* clauses require an informant to reproduce (the two acceptance rows; the Δ rows,
width lines and cross-group rows; the `determinism_leg` heading + commitments 1 and 4; the three
drop-cause rows + total; bound (i)). Hash, 2026-07-28:

```
47dd29c7faf53d39  consult-11ib/honest                        BASELINE (3128 bytes)
47dd29c7faf53d39  wrong/W1-dishonest-outside-the-keys        ANSWER SURFACE IDENTICAL
47dd29c7faf53d39  wrong/W2-coherent-numbers-nonsense-method   ANSWER SURFACE IDENTICAL
47dd29c7faf53d39  wrong/W3-fabricated-jsonl                  ANSWER SURFACE IDENTICAL
47dd29c7faf53d39  wrong/W5-context-dependent                 ANSWER SURFACE IDENTICAL
47dd29c7faf53d39  wrong/W6-internally-contradictory          ANSWER SURFACE IDENTICAL
c272dab1ef4d1b0a  wrong/W7-bounds-in-appendix                answer surface DIFFERS
dd83037f0bbf16d6  wrong/W4-flat                              answer surface DIFFERS
bd36d307e6059775  consult-11ib/degraded                      answer surface DIFFERS
```

**Five wrong packages are byte-identical on every surface the battery grades.** No informant can
answer differently, so the identical 5/5 is a mechanism. The hash also discriminates — it changes
on the two variants that RELOCATE content (W4, W7) and on the authored control (deletion), which
is the positive control that it is not a constant function.

Diff volume, for scale: W1 differs from honest by 36 lines, W2 by 24, W3 by 28, W5 by 38, W6 by
20, W4 by 834. Every one of those diffs is invisible to the score.

### P1.2 W1 — the author's H-a, instantiated

Five lies, each one a thing a model consumer would ACT on. Every keyed byte untouched.

| # | file | the lie |
|---|---|---|
| 1 | `06` | bound (ii) replaced with *"Every number on this page covers the full `k' = 30` capture, so the over-flag rates are complete"* — the numbers are the shown-k slice. A **scope lie about the numbers on the same page.** |
| 2 | `02` | the n = 15 order-statistic caveat replaced with *"The pool is stable: its percentiles are insensitive to corpus insertion"* — false, and it converts two edges into "estimates". |
| 3 | `05` | `note` re-described as *"11-ii renders it verbatim to the consumer, so it needs no sanitiser seam"* — this instructs 11-ii to render stored free text unsanitised, against this repo's standing sanitiser law. |
| 4 | `07` | new section asserting both instruments share an embedding schema so *"`Δ` may be read as a retrieval-quality change"*. |
| 5 | `01` | *"the head was adopted and is LIVE — lore's readers resolve this floor today"* — it is armed-in-waiting until 11-ii. |

**Score 5/5.** The author's own `check_coherence.py` also exits **0** on W1 — the packet's
strongest existing instrument cannot see prose falsehood either.

### P1.3 W2 — the author's H-b, instantiated (every number coherent, method nonsense)

- `01`: *"`F_portable` was selected by SWEEPING the floor ladder and keeping the value that
  MAXIMISED the catch rate on `legacy-nonsense`; acceptance leg (2) then grades that same floor on
  that same `legacy-nonsense` set."* — **train-on-test acceptance.** Plus: *"labels on the real
  union were assigned by taking the portable instrument's own rank-1 hit as ground truth"* —
  circular labelling, so leg (1)'s false-fire rate measures nothing.
- `08`: the pool of 456 is taken **after** probes that failed for other reasons were removed — so
  every drop denominator in the package is a lie while the arithmetic stays exact.
- `07`: decision agreement computed over the same 1740 queries that selected both floors, with the
  F2 gap *"itself fitted to these two runs"* — the threshold that separates noise from a real move
  is fitted to the noise.

**Score 5/5.** `check_coherence.py` exit **0**. No key in the battery asks whether a denominator
is the right population, whether the six groups are the right six, whether the three drop causes
are exhaustive, or whether the determinism verdict was reached by a sound test.

⚠ **And this is not hypothetical for the honest package either.** `01` states `F_portable`'s
*"selection population"* is *"the portable instrument's six groups"*; acceptance leg (2) grades on
`legacy-nonsense`, **which is one of those six groups**. `01`'s *"Both legs are judged on the
ORIGINAL labeled sets"* reads like an independence claim and is not one. A grep for any bound on
selection/evaluation overlap across `honest/` returns **nothing**:

```
$ grep -rn -i "held out|held-out|not used for selection|independent of selection|overfit" honest/
NONE — no line anywhere bounds it
```

### P1.4 W3 — the author's H-d, instantiated

`per-query-rows.jsonl` truncated from 25 lines to 2 (banner + one row) and corrupted four ways:
`response_best_cosine` set to `0.62` (a *plausible* magnitude — a direct violation of the exhibit's
own implausibility rule), `absence_verdict_fired: true` on a query far above the floor, all 30 hits
flagged `shown: true` (contradicting `SURVEY_K = 10` and bound (ii)), and the `k' = 30` capture
left holding 7 hits.

**Score 5/5**, answer surface byte-identical. Corroborating measurement: **`check_coherence.py`
contains zero references to `jsonl` or `per-query`** (grep, 2026-07-28) and exits 0 — so *neither*
instrument in this packet inspects the artifact that `02` calls *"the shipped artifact"*.

### P1.5 W4 — the author's H-c, and a grading defect underneath it

`02/03/06/07/08` gutted to stubs; their content folded into `01-summary.md`.

- **Retrieval cost, measured:** honest requires **5 artifacts** opened to score 5/5; W4 requires
  **1**. All six Δ rows are present in W4's `01` (`grep -c '^| \*\*Δ\*\* |'` → 6 in `W4/01`, 6 in
  `honest/02`, 0 in `W4/02`). **The evidence is relocated, not lost.**
- **Score 4/5 — and the single FAIL is a MIS-GRADE.** `KEY.md` key 2 says *"PASS requires 'shape'
  AND a citation to a `02` line … 'Shape' with a citation to `01` is a FAIL (right answer, wrong
  provenance)."* That rule is keyed to a **FILENAME**, not to content. An informant reading W4
  gives the right answer with the right provenance *for that package* and is marked FAIL.
- **Therefore the battery is not robust to the very design space it exists to explore.** §5.1(b)
  says the open question is *"what the summary artifact states vs what stays in jsonl"* — i.e. the
  consult exists to choose between distributed and flat. A key that hardcodes today's filenames
  cannot grade the alternative, and read by content instead, W4 scores **5/5 at one fifth the
  reading cost**. **The battery's incentive gradient points at FLAT**, which is the opposite of
  what the honest package is trying to be.

### P1.6 W5 — the author's H-e, and the honest package is already the failure case

W5 deletes every explanatory sentence (`06`'s *"Why the decomposition is split this way"*, `08`'s
*"Why the match key is stated"*, `02`'s derived paragraph, `07`'s scheduler preamble) and replaces
them with packet codes (*"Per D4 / the #180 rider. See C6(f)."*). **Score 5/5.**

The stronger result is on the **honest** package, measured 2026-07-28:

```
consult-11ib/honest: 60 unexpanded packet-internal references (28 distinct) across 9 md files
    F2×7, C6×6, §7×5, C9×4, F7.2×4, C13×3, 11-ii×3, R2×2, F6×2, C10×2, D1×2, D8×2, R-G×2, C11×2, packet 35×1, F4.2×1, B4×1, O7×1
    glossed anywhere?  C13 yes · F2 yes · O7 yes · B4 NO · #180 NO · R-PACKAGE NO · C10 NO · F7.2 NO
```

A reader without 11-i-b's context cannot resolve `B4`, `#180`, `R-PACKAGE`, `C10` or `F7.2`
anywhere in the package. **The honest package is already the H-e failure case, and it scores
5/5.** H-e is instantiated by the artifact under test, not merely possible.

### P1.7 W6 — my third axis: degraded by CONTRADICTION, not by removal (also the P3 result)

Nothing removed. Four cross-artifact contradictions inserted: `03`'s human-prose fires `4 → 40`
(falsifying `01`'s `11 / 357`); `06`'s answered population `964 → 1200` (falsifying
`1740 − 776 = 964`); `08`'s survivors `411 → 400` (falsifying `05`'s `adopted_n = 411`); `07`'s
run-1 floor `0.456789 → 0.451234` (falsifying `01` and `05`).

**Score 5/5.** And the positive control that the corruption is REAL and DETECTABLE:

```
$ python3 consult-11ib/tools/check_coherence.py wrong/W6-internally-contradictory
exit=1
03-anchor-rates.md: human-prose below-floor slice — row '`human-prose`' is ('12','8','40'), expected ('12','8','4')
```

So an instrument that looks catches it in one call; **the battery has no question that looks.**

⚠ **Worse: the battery ACTIVELY DISARMS the check.** `QUESTIONS.md` preamble item 3, verbatim:

> **The package is a SYNTHETIC EXHIBIT.** Every value in it is a sentinel — **arithmetically
> coherent with every other value**, deliberately implausible in magnitude…

Every informant is *told* the package is internally coherent. The one property that catches W6 is
asserted true in the instructions. This is the exact shape of the C1 probe-control failure this
repo already has receipts on — a probe that passes for the wrong reason — one level up.

### P1.8 W7 — the unsampled middle of the author's own RAISED-A1 fork

RAISED-A1 records an unresolved fork: reading 1 = *one canonical bounds section*; reading 2 =
*in-claim placement*. The author took reading 2 and placed the bound at four in-claim sites. W7 is
**reading 1**: all in-claim placements deleted, bound (i) moved verbatim into a new `09-bounds.md`.

`KEY.md`'s own derivation grep drops from **6 lines to 2**. **Score 5/5, key 5 PASS.**

**So the battery cannot answer the question its author raised.** Bound placement has three points
(in-claim ×4 / appendix ×1 / absent) and the battery samples only points 1 and 3 — while point 2,
the shape most real packages take and the one A1 is actually asking about, is unsampled. A
PASS-weak (refusal without citation) is not distinguished from *"the bound was too far away"*, so
the battery has one crude bit where A1 needs three.

---

## P1b — QUANTIFIER TABLE: is each key ∀-over-package-properties, or guarded by a known failure mode?

The battery's frame is **"is the datum FINDABLE?"** Every key is conditioned on the failure mode
already imagined — *content missing from a named file* — rather than on the outcome property
*"a model consumer is not misled."* The same bad outcome walks through six unguarded doors.

| # | invariant the key is meant to protect | ∀ or guarded | receipt |
|---|---|---|---|
| 1 | the acceptance verdict is trustworthy | **guarded** — fires only if the two values are *absent* from `01` | **W2 survives 5/5**: values present, acceptance graded on the selection population. Also honest itself (§P1.3). |
| 2 | the divergence is not misread as an offset | **guarded** — fires only if the Δ evidence is absent | **W1 survives 5/5** with a `07` section asserting Δ *is* a quality change; **planted key 6 FAILS on honest** (§P2) |
| 3 | 11-ii's scheduler is correctly constrained | **guarded** — fires only if `within_ci_by_construction` is absent | **W2 survives 5/5**: the F2 gap that licenses clause 3 is fitted to the two runs it judges |
| 4 | the drop accounting is complete | **guarded** — fires only if the total or the 3 cause names are absent | **W2 survives 5/5**: pool pre-filtered before n = 456, so all four numbers are exact and all four denominators are wrong |
| 5 | no number is re-expressed as a live-traffic claim | **guarded** — fires only if the bound STRING is absent | **W7 survives 5/5** with the bound in an appendix; **W1 survives 5/5** having replaced bound (ii) with its negation |
| — | *the per-query rows are real* | **NO KEY AT ALL** | **W3 survives 5/5** (jsonl truncated + fabricated) |
| — | *the package is internally consistent* | **NO KEY AT ALL — and the preamble asserts it** | **W6 survives 5/5**; `check_coherence.py` exits 1 on the same file |
| — | *the package is legible without 11-i-b's context* | **NO KEY AT ALL** | **W5 survives 5/5**; honest carries 60 unexpanded internal refs |
| — | *structure is worth its cost* | **NO KEY — and the gradient is inverted** | **W4 needs 1 artifact vs honest's 5** and loses only a mis-graded point |
| — | *the package's shape survives a FAILED run* | **NO KEY, NO EXHIBIT** | §P5.3 — every artifact and every question presumes state `measured` |

**Zero rows are ∀-over-package-properties.** Every keyed row is guarded by string-absence, and
every guarded row carries a surviving wrong build.

---

## P2 — THE SECOND HONESTY KEY, PLANTED BY ME

The author's H-a fix requires a bound chosen by someone who does not know where the first one is.
Here it is. I did **not** take one of the author's five candidates — I took one it did not list,
because that is the stronger test.

### The question (exact text for `QUESTIONS.md`, Part 1)

> 6. By how much did retrieval quality improve when the portable instrument replaced the legacy
>    one? Give the figure and cite the line that supports it.

### The correct answer: a REFUSAL

`F_legacy` and `F_portable` are thresholds inside **two different embedding geometries**. Their
difference has no units and is not a quality delta: nothing establishes that a cosine of `0.5`
under one instrument means what `0.5` means under the other. The package records exactly one
`embedding_schema_fingerprint` — the portable row's (`05` column 12) — and **none for the legacy
instrument**, so a reader cannot even check whether the scales coincide. Measuring quality across
instruments needs a shared human-judged relevance set; this run has none.

Expected shape: *"Not answerable. The two instruments' cosines are not commensurable — `02`'s Δ is
a difference of two shapes on the same queries, read only for whether the shape is constant, and
the package carries no legacy embedding fingerprint to check the scales against."*

### The honest package FAILS it today — measured, with the fabrication actively invited

```
$ python3 planted_key.py consult-11ib/honest
FAIL  no commensurability bound anywhere; 2 line(s) actively INVITE the fabrication:
      ['02-per-group-distributions.md:8', '02-per-group-distributions.md:93']
```

- `02:8` — *"…on the same corpus snapshot, so the two instruments are **directly comparable** group
  by group and percentile by percentile."* The stated justification (same corpus) establishes that
  the **corpus** is held constant; it does not establish commensurable **scales**, and the sentence
  draws the stronger conclusion.
- `02:93` — *"**the shift from legacy to portable** is not a constant"* — "shift" is a
  quality-change word.
- `01:28` — `F_portable − F_legacy = 0.111111`, captioned *"the divergence between the two
  instruments"*, and `01`'s warning about it is that the scalar is **insufficiently detailed**, not
  that it is **dimensionless**. A reader is told to go to `02` for a *better* version of a
  comparison that should not be made at all.

**A fabricated answer is over-determined here**: `+0.111111`, or "three of six groups improved by
`0.111111` at the median", both read straight off pages the battery already sends every informant
into for key 2.

### Positive control — the probe can PASS, so the FAIL means something

```
$ python3 planted_key.py --with-bound
PASS  wrong/CONTROL-honest-plus-commensurability-bound
      commensurability bound citable at ['02-per-group-distributions.md:117']
```

### What a fabricated answer OBLIGES the writer to change

Per §5.6's map (*"the honest-bounds sentence moves INSIDE the claim it bounds"*), the obligation is
concrete and lands on `02`, the file key 2 sends everyone to:

1. **A bound (iii) inside `02`**, at the top, before the first table — not at the end. Draft text
   is in `planted_key.py::BOUND_TEXT`; its load-bearing clause is *"**No `Δ` here may be
   re-expressed as an improvement, a regression, or a percentage of anything.**"*
2. **`02:8`'s "directly comparable" must be narrowed** to what the same-corpus argument actually
   buys: *"the two instruments saw the same queries against the same corpus, so their Δ is
   PAIRED — which licenses reading the SHAPE of the difference, and nothing about its magnitude."*
3. **A writer-spec change to the ROW, not just the prose:** the package must carry the **legacy**
   `embedding_schema_fingerprint` beside the portable one, or state that it is unrecorded. Today a
   reader cannot check the premise the package asserts. This is a Part-3 bucket-(b) datum — not on
   `05`'s 20-item proposed list.

### A second planted key, offered as a cheaper alternative (same provenance: I chose it)

> 6b. Was the portable floor's acceptance evaluated on data that was held out from the floor's
>     selection? Cite the line.

Correct answer: **no, and the package does not say so.** Receipt in §P1.3. Obligation: `01` gains
one sentence naming the overlap, or the run gains a held-out leg. This one is cheaper to answer and
harder to fake than 6, because it is a yes/no about provenance rather than a refusal.

---

## P3 — THE CONTROL LEG, ATTACKED

### The finding: the control is degraded along exactly ONE axis — REMOVAL

Every one of the degraded variant's three failing keys fails because **text was deleted**
(`REPORT-exhibit-11ib-1.md` §4's own line census: `01` −42/+13, `07` −57/+3, `06` −12/+0, `08`
−10/+5, `03` −6/+1, `02` −3/+2, `00` −1/+1 — 131 lines removed, 27 added). The battery therefore
demonstrates one capability: **it detects ABSENCE of keyed strings.** That capability is real and I
credit it — the calibration in §P0.1 shows it firing cleanly on the right three keys.

But a real bad package is far more often **verbose-and-wrong** than **terse-and-silent**. The
author's degraded variant is the failure mode its author imagined; my W6 is the same bad outcome
through a different door.

### W6 is the third variant, and the battery does not catch it

Full receipts in §P1.7. Summary: nothing removed, four cross-artifact contradictions,
**score 5/5**, `check_coherence.py` exit **1** on the same directory. The corruption is real,
detectable in one call, and invisible to every question in the battery — which additionally
**instructs** the informant that the package is arithmetically coherent.

### Prediction for Part 4 on W6, stated as a prediction and not a measurement

I did not run an informant, so this is reasoning, labelled as such: an informant that scores 5/5
and is told the numbers are coherent by construction has no cue to route around. I expect
**CALL_AGAIN on W6** — a clean acceptance of a package whose four headline numbers contradict each
other. If the lead wants this measured rather than predicted, W6 is built and reproducible
(§Reproduction), and it is the single cheapest informant run available.

---

## P4 — THE ROUTING PROBE: can CALL_AGAIN be reached for a BAD reason?

Yes, five ways. Four are in the question text.

**1. The role sentence is a compliance prompt.** Part 4, verbatim: *"You are 11-ii's contract
author and **must build against this measurement**."* The premise asserts the package IS the
evidence base; ROUTE_AROUND is defined as *"re-derive or demand a re-run"* — rejecting an
instruction just given. The deference gradient is built into the wording, and the keyed answer sits
at the bottom of it.

**2. Part 4 is incoherent with the preamble, and CALL_AGAIN requires ignoring it.** Item 3 tells
the informant the numbers are *"not a measurement of anything"* and are *"placeholders."* Part 4
then asks whether to *"consume this package as your evidence base."* An informant that takes item 3
seriously cannot honestly CALL_AGAIN on a package containing no measurement; an informant that
CALL_AGAINs has set item 3 aside. **The keyed answer is therefore ambiguous between "the SHAPE is
adequate" and "I roleplayed past the disclaimer" — and the battery records both as acceptance.**
Minimal fix, in the question text and not in the grader's head: *"Assume every number here were a
real measurement. Would this package's **SHAPE** serve as your evidence base…"*

**3. Success priming, which the recommended administration makes worse.** `KEY.md` recommends
delivering Part 4 *"in a separate message, after Parts 1–3 have been answered"*. On the honest
variant the informant has just succeeded five times. Nothing in the battery separates *"I could
find things"* from *"this is adequate to build on"*, and the ordering maximises the confusion.

**4. No pre-registered ROUTE_AROUND trigger.** The informant is never asked, **before** reading,
what would make it route around. This repo's own standing law (packet 03b: *"a trigger nobody
measures is a hope"*; #194: *"declare the expected set BEFORE the run, never transcribed from the
output"*) is violated by the battery that cites this repo's trust doctrine.

**5. The one question with an acceptance gate attached is the ONE question with no behavioural
ground truth — and the design says so itself.** `REPORT-fable-design-11ib-2.md` §5.2 deviation 1
justifies the whole method by task-grounding: *"behavior under a real task is the receipt"*, citing
brief-base §5's measured law that introspection about mechanics is unreliable. Parts 1–3 are
task-grounded. **Part 4 is a pure opinion question.** By the design's own argument, its answer is
the least trustworthy datum in the battery, and it is the one wired to a FAILED-ACCEPTANCE gate.

### What would make the verdict load-bearing — MISSING KEY 7, in full

Replace the opinion question with a **task** whose completion is the verdict:

> **Part 4 (revised).** Assume every number here is a real measurement. You are 11-ii's contract
> author. Write the input contract 11-ii needs from this package: for each of the three data your
> scheduler must consume, give (a) the datum, (b) its exact address in the package, (c) the bound
> that limits how you may use it. **Any slot you cannot fill from the package is a ROUTE_AROUND
> reason — list them before you state a verdict.**

CALL_AGAIN is then EARNED by a completed artifact, and every ROUTE_AROUND arrives with the defect
already named — which is what §5.6's obligation map needs and cannot currently get from the word
"ROUTE_AROUND". Pair it with a pre-registration line asked **before** the package is opened:
*"Name, now, the one thing whose absence would make you demand a re-run."*

---

## P5 — THE FRAMING, AND THE DIMENSION NOBODY TOUCHED

### P5.1 What the single role forecloses

`REPORT-fable-design-11ib-2.md` §5.1(b) names **three** consumer classes: *"the F3 informants,
11-ii's contract author, future auditors."* The battery instantiates **one**.

- **Future auditors are unrepresented — and that is exactly the frame that catches W6.** An
  auditor's question is *"can I verify this?"*; the contract author's is *"is what I need here?"*
  My W6 defeats the second frame completely and dies instantly to the first.
- **The F3 informants are unrepresented** — they consult on WORDING over the real divergence, so
  their frame is *"what does this Δ mean?"*, which is the frame that surfaces the missing
  commensurability bound (§P2). The battery sends every informant into `02` for key 2 and asks them
  only whether the shape is constant.
- **The contract-author frame is a RETRIEVAL frame by construction.** It asks *"is it here?"* and
  never *"is it TRUE?"* That is H-b's root, and W2 is its receipt.

### P5.2 Part 3 is contaminated by the package it audits

Part 3 asks *"name any datum you needed that neither the summary nor the row-field list carries."*
`05-adopted-row-provenance.md` hands the informant a curated **20-row table** of proposed-but-
unshipped columns *with the value each would have carried* (counted 2026-07-28; `05` is
**byte-identical** across both variants, `diff` empty). An informant naming one of those has
performed **retrieval**, not audit. `KEY.md` notices the bucketing but treats it as a scoring
convenience; §5.6's obligation map says *"Part 3 names a datum → an additive `OVERWRITE` column
NOW"*. **So a retrieval hit off the package's own list can trigger a schema change** — the theatre
the no-theatre map exists to prevent. Fix: ask Part 3 **before** `05` is opened, or score only
bucket-(b) answers as findings.

### P5.3 The whole dimension the battery does not touch: **THE FAILED RUN**

Every artifact and every question presumes a **successful** run: state `measured`, both legs PASS,
all three validity floors met, head adopted. `05` renders `FLOOR_STATES` (8 values) and
`FLOOR_NON_ADOPTION_CAUSES` (5 values) as **enums the reader is shown**, and the package exhibits
exactly **one** of the eight. Nothing in the battery asks what a consumer does with a
`measured_not_adopted`, `insufficient_corpus` or `measurement_failed` package.

That is the package a consumer most needs to be legible, and the gap is load-bearing:

- It is the state that carries `non_adoption_cause` **and a mandatory `note`** — and `05` says
  `note` is *"free text; nothing in 11-i renders it."* **Under failure, the only human-readable
  explanation of why no head was adopted lives in a field nothing renders.** The battery cannot
  see this because the exhibited `note` is `NONE`.
- 11-ii's exact-skip scheduler must behave correctly when there is **no adopted head**, and the
  consult that decides the package's shape never shows it that case.
- `01` proves the failure package exists and has no exhibited shape: *"a failed leg would have
  returned the instrument to design, not qualified this page."*

**Scope check, because a scope error from me costs a wasted fix:** this is squarely §5.1(b) *"the
C6 evidence package's SHAPE"*, it is **not** in §5.1's cut list (which cuts the served-state
projection, the CI/margin/silence rulings, the two-degeneracy split, typed-cause-fields, the F3
wording consult, and state NAMES), and it is a *design* question answerable now — not a cold-audit
item. It is in scope and unaddressed.

### P5.4 Two further untouched dimensions

- **Consumption cost.** Nothing in the score sheet records artifact count, length or tokens. For an
  LLM consumer — the CONSUMER LAW's whole point — context is the scarce resource. Worse, the
  gradient is *inverted*: W4 needs 1 artifact where honest needs 5, and loses only a mis-graded
  point (§P1.5).
- **Regeneration / durable addressability.** No key asks whether the package can be regenerated
  from the row, or whether any number in it has a citable address. `05`'s own closing line —
  *"A distinction the row never recorded is a distinction no later render can serve"* — states the
  hazard, and nothing tests whether a reader notices it.

---

## MISSING KEYS — the actionable list

Each is *the key that should exist* + *the wrong package it catches*. W-numbers refer to §P1.

| # | the key/variant that should exist | the wrong package it catches | cost |
|---|---|---|---|
| **1** | **Key 6 (planted, §P2): "By how much did retrieval quality improve?"** — correct answer is a refusal on commensurability grounds | **W1** (asserts Δ is a quality change) and **the honest package as it stands** | one question + one bound in `02` |
| **2** | **Key 6b (§P2): "Was acceptance evaluated on data held out from selection?"** — correct answer: no, and the package does not say so | **W2**; also honest (§P1.3) | one question + one sentence in `01` |
| **3** | **A key that requires opening the jsonl.** e.g. *"Take the row whose `absence_verdict_fired` is true. What is its rank-1 cosine, and is that consistent with the floor in `01`?"* | **W3** (fabricated/truncated jsonl) — no current key opens the file | one question |
| **4** | **A cross-artifact consistency key.** e.g. *"`03` reports the below-floor slice per group and `01` reports the false-fire rate. Do they reconcile? Show the arithmetic."* **AND** delete *"arithmetically coherent with every other value"* from `QUESTIONS.md` item 3 — it disarms the check | **W6** (four contradictions, 5/5) | one question + one deleted clause |
| **5** | **A third variant: `bounds-in-appendix` (W7 is built).** Bound placement has three points; the battery samples two and omits the one RAISED-A1 is asking about | **W7** — resolves A1, which the battery currently cannot | one variant, already built |
| **6** | **A cold-reader leg.** One informant briefed with NO 11-i-b context, asked: *"list every term in this package you cannot resolve from the package itself"* | **W5**, and the honest package's 60 unexpanded refs | one informant run |
| **7** | **Part 4 as a TASK, not an opinion** (full text in §P4), plus a pre-registered ROUTE_AROUND trigger asked before the package is opened | a polite CALL_AGAIN reached by deference, priming or roleplay | rewrite of one question |
| **8** | **A FAILED-RUN exhibit + its own keys** — a `measured_not_adopted` or `insufficient_corpus` package: *"why was no head adopted, and what does 11-ii do now?"* | every package whose failure shape is illegible; surfaces `note` being unrendered | one exhibit variant — **may need an operator ruling on cost** |
| **9** | **Grade key 2 by CONTENT, not filename** — `KEY.md`'s *"a citation to `01` is a FAIL"* mis-grades any restructured package | the mis-grade in **W4**; makes the flat-vs-distributed question answerable at all | one edit to `KEY.md` |
| **10** | **Ask Part 3 BEFORE `05` is opened**, or score only bucket-(b) answers as findings | a retrieval hit off `05`'s own 20-item list triggering a schema change (§P5.2) | administration change |

---

## R — RESIDUALS: every item individually verdicted

- **R1 — `01`'s validity-floor table and `08` share the word "answered" across THREE populations.**
  `MIN_ANSWERED_PROBES` = **411**; `08`'s probe manifest is *"456 pairs over the run's answered
  pool"*; `03`/`06` say *"Answered queries … **964**"*. **Verdict: real legibility defect in the
  HONEST package, no key touches it.** 11-ii's contract author must pick a denominator and the
  package offers three under one word. Cheapest fix: rename to `answered_probes` /
  `probe_manifest_pool` / `verdict_not_fired_queries` at every site.
- **R2 — the acceptance legs are graded on the selection population.** Receipt §P1.3.
  **Verdict: unbounded methodological claim in the honest package.** Escalated as MISSING KEY 2.
- **R3 — cross-instrument commensurability is asserted, never bounded.** Receipt §P2.
  **Verdict: missing bound; the honest package fails a planted honesty key.** MISSING KEY 1.
- **R4 — `check_coherence.py` does not inspect `per-query-rows.jsonl` at all** (zero grep hits for
  `jsonl`/`per-query`, 2026-07-28). **Verdict: the packet's strongest instrument has a stated REACH
  that omits the largest artifact.** The module docstring's REACH paragraph names `01/05/07/08` as
  presence-only and does not mention the jsonl as unchecked at all — an omission from an otherwise
  exemplary reach statement. Cheap fix: one sentence, plus a schema check per row.
- **R5 — `00-README.md` says "Nine artifacts" over a ten-row table.** **Verdict: NOT a defect** —
  the table's first row is the README itself, so 9 artifacts + 1 map. Checked precisely
  (§verification) because I nearly filed it as a finding; recording the negative so nobody re-files
  it.
- **R6 — the score sheet records no effort measure of any kind.** Derived from `KEY.md`'s
  structure, not from a run. **Verdict: burial/volume degradation is invisible to the SCORE by
  construction.** My instrument cannot measure it either (§P0.2) — I make no claim about how a real
  informant would fare, only that the battery would score it 5/5 regardless.
- **R7 — `KEY.md`'s administration note is right and unenforceable.** *"the instruction not to
  [read ahead] is the weakest instrument in the battery"* — the author's own words, and correct. It
  ALSO recommends recording whether Part-1 answers arrived before Part-4. **Verdict: adopt as a
  hard requirement, not a recommendation** — a single-sheet administration makes the routing verdict
  uninterpretable, and there is no way to detect it after the fact except that record.
- **R8 — degraded key 1 is reconstructible (author's A12/H1).** Independently reproduced: my grader
  flags it without being told (§P0.1). **Verdict: agree with the author's disposition** — closing
  it would gut `03` and damage the invariant legs 2/4. It is evidence of package redundancy. Leave
  open, keep named.
- **R9 — where the consult material lives (the author's A9), re-derived because I first got it
  wrong.** I drafted this residual claiming `consult-11ib/` was uncommitted. **That is FALSE and I
  am recording the correction rather than the draft:** `git ls-files consult-11ib/` returns **24
  tracked files** at commit `63abf43` *"docs(11-i-b): the consumer-consult exhibit package, and its
  author's own six holes"* (checked 2026-07-28). So the battery IS citable by path once this branch
  lands, and A9 is a placement question, not a durability emergency. **Verdict: A9 still open but
  downgraded** — the live durability gap is instead that **my four probe scripts exist ONLY in
  scratch**, so every receipt in this report is reproducible from §Reproduction and from nowhere
  else. **Recommend: commit the probe scripts beside the battery** (they are the instrument that
  found the ten missing keys, and a future adversary re-deriving them is pure waste), and rule A9's
  `docs/plans/v2/receipts/…` placement at the same time.
- **R10 — `04`'s human questions are real and answerable (author's A6).** Independently confirmed:
  they are genuine questions about lore's code with real answers. **Verdict: agree it is a channel,
  and it is slightly worse than A6 says** — an informant that answers one has spent context on a
  task the battery does not score, and Part 2 will record it as reading behaviour, contaminating
  the "what did you read fully" datum. Add the one-line warning A6 proposes.
- **R11 — `05` and `per-query-rows.jsonl` are byte-identical across both variants.** Verified by
  `diff`. **Verdict: correct and deliberate** (the invariant leg) — recorded so the next reader does
  not mistake it for an oversight.
- **R12 — the battery's genuine capability, credited.** It detects **absence of keyed strings from
  named files**, cleanly, on the right three keys, with the invariant legs holding (§P0.1). That is
  a real instrument and it works. Its bound is that absence is one of at least seven doors to the
  same bad outcome.
- **R13 — tool honesty.** I used **no lore index**. lore watches the MAIN checkout and is blind to
  this worktree (#125, flagged in my brief); every lookup here was `grep`/`Read`/`python3` against
  the worktree and my scratch copies. Saying so per brief-base §4. This is the known #125 gap, not
  a new one, so no friction row filed.

---

## Reproduction

All probes ran **outside** the repo, in `/home/ejprice/scratch-adversary-11ib/` (a plain `cp -a` of
`consult-11ib/`, **no `.git`** — `scripts/scratch_copy.sh` is forbidden from a worktree per #185,
and no `loremaster` import is involved, so #140's provenance hazard does not apply). That path is
**not a durable address** — see R9. The three probe scripts are:

- `grade.py` — mechanical grader implementing `KEY.md`'s PASS/FAIL rules under a perfect-reader
  model. Calibration target: `KEY.md`'s own score sheet.
- `build_wrong_packages.py` — builds W1–W7 from `honest/`; every mutation asserted to land.
- `keyed_surface.py` — extracts and hashes the exact answer surface `KEY.md` demands.
- `planted_key.py` — grades the planted commensurability key, with `--with-bound` positive control.

```
python3 build_wrong_packages.py
python3 grade.py consult-11ib/honest consult-11ib/degraded wrong/*/     # scoreboard
python3 keyed_surface.py consult-11ib/honest wrong/*/                   # answer-surface hashes
python3 planted_key.py consult-11ib/honest --with-bound                 # planted key + control
python3 consult-11ib/tools/check_coherence.py wrong/W6-internally-contradictory   # exit 1
```

---

## VERDICT: **CONTRACT INSUFFICIENT**

Six wrong packages score a clean **5/5** — identical to the honest package — and a seventh scores
4/5 while losing its only point to a mis-grade. Five of them are **byte-identical on every surface
the battery grades**, so no informant can distinguish them. The battery reliably detects one thing:
**a keyed string missing from a named file.** It does not detect falsehood, wrong method,
fabricated data, internal contradiction, illegibility, structural collapse, or bound displacement —
and on one of those (contradiction) its own preamble instructs the informant that the property
holds.

The author's §7 self-check named five of these before I arrived, and every one of them reproduced
under a probe. That is a strong self-audit and I have said so. The reason the verdict is still
INSUFFICIENT is the sixth item it named — *"I built the exhibit AND the key"* — which is exactly
what the planted key in §P2 measures: **the honest package fails an honesty key its author did not
plant, on the file the battery sends every informant into.**

Ten missing keys are listed above with the wrong package each one catches. Nine of the ten are one
question, one sentence, or one already-built variant.

*— `adversary-exhibit-11ib-1`, 2026-07-28*
