brief-base v6 read

# REPORT-probe-bootstrap-11i — blind-review residual S1, measured

> ⚠ **DRAFT — §4b (detection power) is still filling from a re-run. Every other section is
> final and matches the committed output file.** This banner is removed when §4b lands.

## SUMMARY BLOCK

- **state** — done-with-deviations (see below).
- **deviation 1** — my own instrument shipped a bug on its first full run: the `§4b` power leg
  never passed `shift=shift` to `measure_pairs`, so all six "power" rows silently re-measured
  the null. Caught by reading the output (all six rows printed `shift 0.000`), fixed, and the
  whole script re-run so the committed output comes from one coherent run of the committed
  script. The script now prints a shift-plumbing sanity check so the same bug cannot look
  plausible again.
- **deviation 2** — the worktree HEAD moved under me during the run, `5484ae4` → `e9b570f`
  (the lead landed the §0 operator rulings and the client consult). Nothing I read changed:
  the diff touches only `REPORT-consult-*.md`, `CLIENT-CONSULT-SYNTHESIS.md` and
  `CONTRACT-FREEZE-DECISIONS.md`. My measurement is against `scripts/search_score_survey.py`
  and `loremaster/loremaster/search.py`, neither of which moved.
- **deviation 3** — lore was NOT used for code structure. `lore_index()` (called this session)
  reports its only watched root as `/workspace` on `feat/surreal-unification` @ `69abba0` —
  the MAIN checkout, not this worktree (finding #125). I fell back to grep/Read in the
  worktree and say so here rather than pretend otherwise. No new friction filed: this is #125
  exactly, already open.
- **decisions-needed**
  1. **The D2 stability gate's denominator is ambiguous and I had to choose.** I evaluated it
     over the ANSWERED UNION only. Reading 2 is union + absent arm. The two give different
     numbers and the design does not say. → §7.1.
  2. **D2's "adopt the smallest N that passes" assumes a monotone curve that the measurement
     does not show.** Measured non-monotonic on leg B: FAIL, FAIL, FAIL, **PASS(448)**, FAIL,
     FAIL, PASS. → §5.2. This is a defect in D2 as written, independent of S1.
  3. **D2 and D3 pull in opposite directions and the design does not name the tension.** D2
     pushes N up to narrow the interval; D3's false-adoption rate RISES as the interval
     narrows (0.0% → 4.5% → 7.0% across N = 56 → 224 → 896). → §6.3.

### HEADLINE VERDICT — **NOT DEGENERATE**

At the recorded 2026-07-07 regime (N=56, false-fire 1/56, catch 15/15), the bootstrap over the
real `choose_cosine_floor` produces `ci = [0.474091, 0.554359]` — **width 0.080268 cosine units
on a point floor of 0.529054, i.e. 15.2% of the floor's own value**, over 7 distinct resampled
values with 56.7% of replicates on the mode. `ci_low != ci_high` at every one of the 31
bootstrap runs in this probe except the differently-broken control. **No rung of either N ladder
was degenerate, at any N from 56 to 3584.**

**Why the reviewer's reasoning does not apply here — and it is a mechanism, not a quibble.** S1's
premise is correct: the floor IS a tail order statistic (measured: **order statistic #2 of 56**,
3.57% of the way up the union), and the nonparametric bootstrap genuinely is not consistent for
extreme order statistics. But **inconsistency's symptom here is ERRATIC, not FROZEN.** A
nearest-rank `[p5, p95]` interval collapses to a point only if one value carries **≥90%** of the
resampled mass. The floor's value is one specific union sample's own cosine, so reproducing it
requires that sample to be present in the resample — and a given sample is absent from a size-N
bootstrap resample with probability `(1 − 1/N)^N` → `1/e`. That caps the expected modal mass at
**≈63.5% at N=56** (`1 − (1 − 1/56)^56 = 0.6354`), falling to `1 − 1/e ≈ 0.6321` asymptotically.
Measured modal masses across all 31 runs: **25.8% – 64.8%**, the maximum sitting ~1 Monte-Carlo
standard error above the bound (B=1000 ⇒ SE ≈ 1.5 pp) and **never within 25 points of the 90%
that degeneracy requires**. The very resampling noise that makes the bootstrap inconsistent for
this statistic is what makes it un-freezable.

**So the packet does NOT fork to design repair on S1's stated ground.** But the objection was
right that the two pre-registered rules fail — they fail in the *opposite direction*, and §5/§6
below say what actually breaks. Read those before treating "NOT DEGENERATE" as "all clear".

### Receipt pointers

| what | where |
|---|---|
| the instrument (re-runnable, regenerates every number) | `docs/plans/v2/receipts/2026-07-24-packet11i/probe_bootstrap_degeneracy.py` |
| its raw output, verbatim | `docs/plans/v2/receipts/2026-07-24-packet11i/probe-bootstrap-output.txt` |
| controls (both legs) | output §0 · this report §3 |
| headline N=56 | output §1 · this report §2 |
| N ladders, both legs | output §2 · this report §5 |
| D2 gate measurement | output §3 · this report §5.2 |
| D3 flapping + power | output §4 / §4b · this report §6 |
| cost table + numpy/scipy | output §5 · this report §8 |
| sensitivity (10 regimes) | output §6 · this report §4 |

---

## 1. What I measured, and what I did not

I drove the **real** `choose_cosine_floor` (imported from `scripts/search_score_survey.py`,
which in turn imports `loremaster.search._cosine_absence_predicate` as its verdict rule — the
S4b audit finding #1 identity-pinning). I re-implemented no part of the selection logic. The
percentile is `token_survey.percentile`, reused rather than re-written.

**Provenance receipt, printed by the script into its own output** — the tree under test:

```
search_score_survey.__file__ = /home/ejprice/PycharmProjects/lore-pkt11i/scripts/search_score_survey.py
loremaster.search.__file__   = /home/ejprice/PycharmProjects/lore-pkt11i/loremaster/loremaster/search.py
choose_cosine_floor          = search_score_survey.choose_cosine_floor
verdict predicate            = loremaster.search._cosine_absence_predicate
```

No store, no embedder, no network. `ws://127.0.0.1:18500` was never opened (nor `:18000`).

**Helper-suite receipt.** `scripts/` is not in `pyproject.toml`'s `testpaths` (verified: it lists
only `lorescribe/tests`, `loresigil/tests`, `loremaster/tests`), so the two modules I depend on
have never run in any repo gate. I ran them myself:

```
$ uv run python -m pytest -q scripts/test_token_survey.py scripts/test_search_score_survey.py
110 passed in 0.25s
```

**I did not touch** `loremaster/`, `scripts/`, `docs/design/`, the packet doc, or
`CONTRACT-FREEZE-DECISIONS.md`. `git status` at the end of my run shows exactly my three
writable paths (plus `REPORT-fable-design-11i-b.md`, another agent's, untouched by me).

---

## 2. The synthesis, parameter by parameter, with provenance

Every parameter is either **RECORDED** (fixed by the repo's own record of the 2026-07-07
adoption) or **DECLARED** (my choice — and every declared one is varied in §4).

### RECORDED — and re-derived from source in this session, not inherited from a report

| parameter | value | how I re-derived it |
|---|---|---|
| union size | **56** | ran the survey's own code: `len(parse_eval_questions(loremaster/evaluation.xml))` = 35, `IDENTIFIER_QUERY_COUNT` = 15, `len(IMPLEMENTATION_VOCABULARY_QUERIES)` = 6 → 35+15+6 = **56** |
| absent (nonsense) size | **15** | `len(NONSENSE_QUERIES)` = 15 |
| false-fire at the adopted floor | **1/56** (1.79%) | `_COSINE_WEAK_MATCH_FLOOR_STAMP`'s comment block in `loremaster/loremaster/search.py`; design doc §1.5 |
| catch at the adopted floor | **15/15** (100%) | same |
| the dominated candidate | **0.5370 at 2/56** (3.6%), identical 100% catch | same comment block's dominance-ordering ruling |
| ⇒ exactly ONE non-anchored union sample strictly below the floor | derived | 1/56 false-fire, scored by the production predicate |
| ⇒ the absent arm carries ZERO verbatim anchors | derived | an anchored sample can never fire, so one anchored nonsense query would cap catch at 14/15; catch was 15/15 |
| the bars | `D2_MAX_FALSE_FIRE_RATE=0.05`, `D2_MIN_NONSENSE_CATCH_RATE=0.6` | imported from the survey module, never re-typed |
| `B ≥ 1000`, central 90% = `[p5, p95]`, `≥98%` gate | Addendum D1/D2/D8 | used as stated |

The N=56 headline corpus is **rejection-sampled** until it reproduces the recorded regime
exactly — false-fire 1/56 AND catch 15/15. It landed in **2 draws**. The resulting adopted floor
is **order statistic #2 of 56**, which is S1's premise measured rather than asserted.

### DECLARED — my choices, every one varied in §4

| parameter | headline value | why it is a choice |
|---|---|---|
| union cosine distribution | `N(0.600, 0.045)` | the survey's raw per-query jsonl lived at `scratchpad/survey_out_74w/` and is **gone** (blind review §6/S5; `scratchpad/` is unrecoverable by construction, #154). Nothing in the tree records the shape. |
| absent cosine distribution | `N(0.440, 0.035)` | same |
| verbatim-anchor fraction on the union | 0.25 | the identifier group is 15/56 = 26.8% of the union, but nothing records how many carried an anchor — one identifier probe demonstrably did not (it is the recorded false-firer) |
| anchor/cosine correlation | independent | D3's carve-out could plausibly correlate anchors with high cosine |
| does the absent arm scale with N? | **both legs run** | leg A = fixed 15 (what the LEGACY instrument does — `NONSENSE_QUERIES` is a fixed tuple); leg B = scales with the pool (what D2's portable hold-out runner implies) |

**Interrogating my own fixtures — "what wrong conclusion would this still support?"** Three
answers, each turned into a leg:

1. *"Degeneracy is absent because I drew a smooth Gaussian with a thin tail."* → §4 runs a
   **uniform** (bounded-support) union, and narrow/wide spreads. Same verdict.
2. *"Anchors are a monoculture."* → §4 runs anchor fractions 0.00 and 0.50, a high-cosine-
   correlated anchor mode, and a run that violates the recorded zero-anchor absent arm. Same
   verdict.
3. *"The floor is only shallow because of where I put the absent arm."* → §4 moves the absent
   arm to 0.500 and the union to 0.620/0.060. Same verdict; §5's ladders move the floor's rank
   from #2 to #226 and it still never degenerates.

---

## 3. THE CONTROLS — the probe firing, and firing for two different reasons

A negative result on a degeneracy hunt is worthless until the instrument is shown resolving a
non-degenerate interval, and shown distinguishing "degenerate for reason X" from "degenerate for
reason Y". Both legs ran **before** the headline, and the script `return 1`s on a failed control
rather than reporting a headline over a broken harness.

### Positive control 1 — same resampler, same CI code, a BULK statistic

The union's **median** cosine, on the *very same* synthetic corpus as the headline:

```
point=0.604534  ci=[0.589420, 0.621304]  width=0.031884  [non-degenerate]
distinct resampled values=92  modal=0.604534 @ 4.8%  sd=0.009489
```

**PASSES** — the harness resolves spread when spread exists.

### Positive control 2 — the REAL `choose_cosine_floor`, only the statistic's DEPTH changed

Same N=56, but the absent arm overlaps the union and the false-fire ceiling is relaxed to 50%
(both DECLARED), so the dominance rule selects a floor in the **bulk**: rank **43 of 56**.

```
selected floor rank in union = 43 / 56  (false-fire 0.446, catch 0.800)
point=0.620900  ci=[0.584559, 0.638416]  width=0.053857  [non-degenerate]
distinct resampled values=16  modal=0.633522 @ 27.2%
```

**PASSES** — and this is the control that matters, because it holds the *procedure* fixed and
varies only the statistic's depth. It rules out "`choose_cosine_floor` is intrinsically
degenerate under resampling", which is the hypothesis a degenerate headline would have needed.

### Differently-broken control — degenerate, for a DIFFERENT and named reason

A **constant** union (zero variance):

```
point=0.600000  ci=[0.600000, 0.600000]  width=0.000000  [DEGENERATE]
distinct resampled values=1  modal=0.600000 @ 100.0%
distinct OBSERVED union cosines: constant-control=1  vs  headline-corpus=56
```

The two failure modes are **separable by a reported column**: the constant control has exactly
**one candidate floor in existence** (`distinct_union_cosines = 1`); the headline corpus has 56
distinct candidates. Had the headline come back degenerate, that column is what would have told
the reader whether it was "the selection rule collapsed onto a tail sample" or "I generated a
constant". It did not come back degenerate — but the instrument can tell, and that is the point
of running the leg.

---

## 4. SENSITIVITY — ten regimes, every declared parameter varied

Every row is a fresh N=56 corpus, all ten landing under the **RECORDED** acceptance predicate
(false-fire exactly 1/56 = 0.0179, catch 15/15 = 1.000), so they are like-for-like.

| regime | floor | rank | ci_low | ci_high | width | distinct | modal% | degenerate |
|---|---|---|---|---|---|---|---|---|
| tail-order-statistic (recorded regime) | 0.535146 | 4 | 0.478266 | 0.540737 | 0.062471 | 7 | 48.1% | **no** |
| narrow union spread (sd 0.030) | 0.540613 | 3 | 0.515755 | 0.553524 | 0.037769 | 8 | 47.7% | **no** |
| wide union spread (sd 0.070) | 0.475617 | 2 | 0.465790 | 0.509090 | 0.043300 | 6 | 45.8% | **no** |
| no anchors at all (0.00) | 0.527393 | 2 | 0.470869 | 0.530720 | 0.059851 | 8 | 57.7% | **no** |
| half the union anchored (0.50) | 0.508663 | 3 | 0.487548 | 0.525166 | 0.037618 | 7 | 56.2% | **no** |
| anchors on HIGH-cosine samples | 0.508553 | 2 | 0.462839 | 0.535646 | 0.072806 | 8 | 61.3% | **no** |
| absent arm ANCHORED too (0.20) | 0.512177 | 2 | 0.458237 | 0.542001 | 0.083764 | 9 | 59.1% | **no** |
| absent arm closer to union (0.500) | 0.544016 | 3 | 0.524788 | 0.545540 | 0.020752 | 7 | 60.4% | **no** |
| heavier union lower tail (0.620/0.060) | 0.534281 | 4 | 0.494035 | 0.555198 | 0.061163 | 8 | 46.3% | **no** |
| **UNIFORM** cosines, not Gaussian | 0.537938 | 3 | 0.527831 | 0.545948 | 0.018117 | 8 | 46.0% | **no** |

**Ten for ten non-degenerate.** The verdict is not an artifact of any single unrecorded choice —
not the distribution shape, not the spread, not the anchor fraction, not the anchor/cosine
correlation, not the absent arm's location, and not the zero-anchor reading of catch 15/15.

*(Note on the `rank` column: it ranks the floor among ALL union cosines including anchored ones,
while false-fire counts only non-anchored samples. A rank of 4 with false-fire 1/56 therefore
means two of the three samples below the floor carried a verbatim anchor and were exempt — the
anchor carve-out is doing exactly what D3 says it does.)*

---

## 5. THE N LADDER, and SILENT FAILURE (a) — the ≥98% stability gate

### 5.1 Leg A — absent arm FIXED at 15 (what the legacy instrument does)

| N | \|absent\| | floor | rank | ff | catch | ci_low | ci_high | width | distinct | modal% | degen | agreement | gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 56 | 15 | 0.518029 | 4 | 0.0179 | 1.000 | 0.489419 | 0.541116 | 0.051697 | 7 | 42.9% | no | 94.64% | **FAIL** |
| 112 | 15 | 0.510510 | 2 | 0.0089 | 1.000 | 0.510510 | 0.529576 | 0.019066 | 8 | 63.0% | no | 98.21% | PASS |
| 224 | 15 | 0.502503 | 2 | 0.0045 | 1.000 | 0.502503 | 0.509919 | 0.007416 | 10 | 64.8% | no | 98.66% | PASS |
| 448 | 15 | 0.495457 | 3 | 0.0045 | 1.000 | 0.472530 | 0.505591 | 0.033061 | 9 | 46.4% | no | 99.11% | PASS |
| 896 | 15 | 0.490894 | 5 | 0.0011 | 1.000 | 0.490894 | 0.493170 | 0.002275 | 8 | 64.7% | no | 99.78% | PASS |
| 1792 | 15 | 0.484338 | 11 | 0.0033 | 1.000 | 0.466349 | 0.488163 | 0.021815 | 13 | 38.6% | no | 99.61% | PASS |
| 3584 | 15 | 0.506332 | 63 | 0.0103 | 1.000 | 0.480816 | 0.506499 | 0.025683 | 22 | 42.0% | no | 99.14% | PASS |

### 5.2 Leg B — absent arm SCALES with the pool (what D2's portable runner implies)

| N | \|absent\| | floor | rank | ff | catch | ci_low | ci_high | width | distinct | modal% | degen | agreement | gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 56 | 15 | 0.495004 | 3 | 0.0179 | 1.000 | 0.486834 | 0.506899 | 0.020065 | 7 | 47.1% | no | 94.64% | **FAIL** |
| 112 | 30 | 0.510664 | 1 | 0.0000 | 1.000 | 0.510664 | 0.542003 | 0.031339 | 7 | 63.8% | no | 97.32% | **FAIL** |
| 224 | 60 | 0.515249 | 9 | 0.0357 | 0.967 | 0.495490 | 0.539450 | 0.043960 | 17 | 35.3% | no | 94.64% | **FAIL** |
| 448 | 120 | 0.502770 | 4 | 0.0045 | 1.000 | 0.502770 | 0.515872 | 0.013102 | 8 | 62.8% | no | 99.33% | **PASS** |
| 896 | 240 | 0.519252 | 38 | 0.0324 | 0.988 | 0.513878 | 0.530741 | 0.016863 | 23 | 28.3% | no | 96.76% | **FAIL** |
| 1792 | 480 | 0.530831 | 111 | 0.0435 | 0.992 | 0.521435 | 0.536251 | 0.014817 | 32 | 27.3% | no | 97.43% | **FAIL** |
| 3584 | 960 | 0.528720 | 226 | 0.0477 | 0.996 | 0.520676 | 0.532527 | 0.011851 | 33 | 25.8% | no | 98.13% | **PASS** |

### 5.3 Answer to silent-failure (a): the gate does NOT pass trivially — and that is not the good news it sounds like

- **No rung of either ladder produced a single-point interval.** `trivially` is `False`
  everywhere. So the "the gate passes trivially and adopts the smallest N" failure S1 predicted
  **does not occur**.
- At the smallest N tried (56) the gate **FAILS**, non-trivially, on both legs (94.64%,
  3 of 56 decisions flip between `ci_low` and `ci_high`).
- **BUT — and this is a defect S1 did not name — the gate is NON-MONOTONIC in N on leg B:**
  FAIL(56) · FAIL(112) · FAIL(224) · **PASS(448)** · FAIL(896) · FAIL(1792) · PASS(3584).
  D2 says *"Adopted N is the smallest where the interval passes the stability gate."* Applied
  literally to this curve, D2 adopts **N=448** — a rung whose two immediate successors both
  fail. The rule is written as if agreement converges monotonically with N; it does not, because
  the interval's width is set by the *spacing between adjacent low-order union values*, which is
  not monotone in N, and because the floor's own rank drifts (leg B: rank 3 → 1 → 9 → 4 → 38 →
  111 → 226) as N changes which order statistic the ≤5% ceiling selects.
  **A "smallest N that passes" rule over a non-monotone curve adopts a rung that passed by
  luck.** That needs a decision — a monotone-run requirement (k consecutive passing rungs), a
  largest-N rule, or a different statistic — and it is a contract-freeze item, not a builder's
  judgement call.

---

## 6. SILENT FAILURE (b) — D3's disjoint-CI adoption

### 6.1 The flapping rate: measured, and it is NOT "any movement"

200 independent pairs per row. Both corpora drawn from the SAME generator — **the true floor has
not moved.** D3 adopts iff the two CIs are disjoint.

| regime | pairs | disjoint | flap rate | point floor moved | mean \|Δfloor\| |
|---|---|---|---|---|---|
| tail regime, leg A, N=56 | 200 | 0 | **0.0%** | 100.0% | 0.014879 |
| tail regime, leg A, N=224 | 200 | 9 | **4.5%** | 100.0% | 0.013840 |
| tail regime, leg A, N=896 | 200 | 14 | **7.0%** | 100.0% | 0.014916 |
| POSITIVE CONTROL (bulk floor), N=56 | 200 | 4 | **2.0%** | 100.0% | 0.013391 |

**S1's second prediction — "disjoint-CI adoption fires on ANY movement, so hysteresis inverts
into maximal flapping" — is REFUTED at the recorded N.** The point floor moves in **100%** of
pairs (of course: it is a different sample's cosine each time), and D3 adopts in **0%** of them.
The interval is doing exactly the job the design claims: it absorbs point movement that is pure
measurement noise. At N=56 the mechanism behaves as advertised.

### 6.2 §4b — detection power (PENDING)

*(filling from the re-run)*

### 6.3 The tension the design does not name

Flapping is **0.0% at N=56, 4.5% at N=224, 7.0% at N=896** — it *rises* with N. The reason is
mechanical: as N grows the CI narrows (leg A widths 0.0517 → 0.0074 → 0.0023 at those rungs)
while the mean point-floor movement between two independent measurements stays essentially
constant (0.0149 → 0.0138 → 0.0149). A narrowing interval around an equally-jittery point
eventually stops overlapping.

**So D2 and D3 pull against each other, and nothing in Addendum D says so:** D2's stability gate
demands a LARGER N to pass; D3's freedom-from-flapping is best at the SMALLEST N. On leg A, D2
would adopt N=112 or larger, and every rung at or above N=224 carries a measured false-adoption
rate of 4.5–7.0% *on a corpus that did not change*. Under D3's "measure at every post-sweep where
at least one chunk changed", a several-percent false-adoption rate per sweep is not a rounding
error — it is a floor that re-writes itself regularly for no reason, on the serving surface the
trust doctrine governs.

---

## 7. Ambiguities I had to resolve, written down rather than chosen silently

### 7.1 The ≥98% gate's denominator — I chose, and here is the other reading

D2: *"verdict decisions computed at ci_low vs ci_high agree on ≥98% of the union's samples."*

- **Reading A (what I implemented):** the denominator is the ANSWERED UNION only. At the headline
  N=56 that gives 3 flips / 56 = 94.64% agreement.
- **Reading B:** the denominator is every sample the measurement holds — union + absent arm. On
  leg A at N=56 that would be 3 flips / 71.

These differ, they can straddle the 98% bar, and **the design does not say which**. Blind review
§6 already flags the denominator as "unstated". I picked A because D2 says *"the union's
samples"* and because the gate's stated intent is *"flips ≤2% of KNOWN DECISIONS"* — the absent
arm's decisions are all "fires", which dilutes the denominator with samples that cannot flip and
makes the gate strictly easier to pass. **I would keep A.** But it is a contract-freeze decision,
not mine, and swapping it is one line in `measure_stability_gate`'s caller.

### 7.2 What "the same regime at larger N" means

At N > 56 the recorded false-fire count of exactly 1 cannot be held — the regime is a *rate*
(1/56 ≈ 1.8%), not a count. I held the SHAPE (100% catch, a non-empty admissible slice of the
union below the floor) and let the count scale. Stated in the script as
`scaled_regime_predicate`. The alternative — holding the count at 1 while N grows — would make
the floor an ever-more-extreme order statistic and is not what a larger pool of the same corpus
produces.

---

## 8. COST — Addendum D1's "free at any N" is FALSE, confirmed by measurement

Single-threaded seconds per bootstrap replicate (resample both arms + one real
`choose_cosine_floor` call), timed over 40 replicates per rung.

| N | \|absent\| | ms / replicate (leg A) | s @ B=1000 (leg A) | ms / replicate (leg B) | s @ B=1000 (leg B) |
|---|---|---|---|---|---|
| 56 | 15 / 15 | 0.161 | 0.16 | 0.164 | 0.16 |
| 112 | 15 / 30 | 0.567 | 0.57 | 0.580 | 0.58 |
| 224 | 15 / 60 | 2.087 | 2.09 | 2.104 | 2.10 |
| 448 | 15 / 120 | 10.352 | 10.35 | 8.043 | 8.04 |
| 896 | 15 / 240 | 30.363 | 30.36 | 30.905 | 30.90 |
| 1792 | 15 / 480 | 118.620 | 118.62 | 122.848 | 122.85 |
| 3584 | 15 / 960 | 478.897 | **478.90** | 543.613 | **543.61** |

**Empirical growth exponent (log-log least squares): leg A = 1.925, leg B = 1.943.** That is the
O(N²) FA3 predicted, measured rather than reasoned.

**The honest statement of the claim.** Addendum D1 says the bootstrap *"costs ZERO embeds … so
interval-carrying is free at any N."* **Zero embeds is TRUE** — nothing in this probe called an
embedder. **"Free at any N" is FALSE**, and the falsity is not academic: one B=1000 bootstrap at
a 3584-probe pool costs **8–9 minutes of single-threaded CPU**, and D3 schedules a measurement at
**every post-sweep where at least one chunk changed**. At the recorded N=56 it genuinely is free
(0.16 s). The claim's failure is exactly at the pool scales D2's own N-noise curve is designed to
reach.

Two mitigations exist and neither is in the design: the bootstrap is embarrassingly parallel
(this probe used a 32-worker pool for §4/§4b), and `choose_cosine_floor`'s inner loop is
recomputed from scratch per candidate where an incremental sweep over sorted candidates would be
O(U log U). **Neither is my call to make** — flagging both.

### numpy / scipy — re-verified in this session, three independent ways

```
import numpy  -> ABSENT (ModuleNotFoundError: No module named 'numpy')
import scipy  -> ABSENT (ModuleNotFoundError: No module named 'scipy')
loremaster/pyproject.toml    -> no numpy/scipy mention
lorescribe/pyproject.toml    -> no numpy/scipy mention
loresigil/pyproject.toml     -> no numpy/scipy mention
pyproject.toml               -> no numpy/scipy mention
uv.lock                      -> numpy: absent
uv.lock                      -> scipy: absent
```

The **import** test is the one that matters — it is the only one that catches a *transitive*
dependency a `pyproject.toml` grep cannot see. The `uv.lock` test catches one pinned but not
installed. **FA3's claim is CONFIRMED, and independently.** The blind reviewer checked four
`pyproject.toml` files; I checked those four plus the lock file plus the live interpreter.

---

## 9. Raised under scope law — things I found that are not mine

1. **ONE IMPLEMENTATION: `weighted_percentile` exists twice, hand-rolled both times.**
   `scripts/token_survey.py::weighted_percentile` (cumulative-weight scan over `(value, weight)`
   pairs) and `scripts/survey_txn_contention_102.py::weighted_percentile` (ceil-rank index over a
   bare `list[float]`). Same POLICY — nearest-rank percentile — two implementations, two
   signatures. I checked them for uniform weights at several percentiles and they agree, so this
   is latent, not live. But it is copy #2 of a policy, which repo law makes a design decision to
   escalate rather than a thing to notice. **11-i will add a third percentile consumer** (the
   bootstrap's `[p5, p95]`); I routed mine through `token_survey.percentile` deliberately.
   Recommendation: promote one to a shared home before the third arrives.

2. **`scripts/` is outside `testpaths`, so `scripts/test_search_score_survey.py` (50 tests) has
   never run in any gate** — and `choose_cosine_floor`, the function the entire floor-calibration
   design is built on, lives there and is covered only by those 50. They pass (110 with
   `test_token_survey.py`), but they pass because I ran them, not because anything requires it.
   Adding `scripts` to `testpaths` is a one-line change with an unknown blast radius (the other
   scripts' suites would join the gate); **not mine to make**, flagged.

3. **`scripts/search_score_survey.py`'s `DEFAULT_SURREAL_URL` is `ws://127.0.0.1:18500/rpc`** —
   the PRODUCTION store, as this script's own default. The design doc §1.5 already notes it, and
   §0's operator ruling authorises a `:18500` run only via an ephemeral container with the rider
   *"the verb REFUSES to run without an explicit store coordinate — no default of any kind"*. The
   rider is written for the new runner; **the existing survey script still carries the hazardous
   default**, and it is the instrument someone would reach for first. Flagging, not fixing.

4. **A bug in my own first run, disclosed rather than buried** — see deviation 1. The lesson is
   the one this repo keeps re-learning: a table that *looks* like a power curve, with plausible
   varying numbers in the rightmost column, was six copies of the null. It was caught only
   because the `shift` column printed the value it was supposed to have applied. The fixed script
   now prints an explicit sanity check tying `mean |Δfloor|` to the shift column.

---

## 10. What this means for the packet, stated plainly

**The §A sizing ruling is unblocked.** `CONTRACT-FREEZE-DECISIONS.md` §0 makes the split
conditional: *"not until S1 lands, because a DEGENERATE verdict forks to design repair and moots
the slice."* **S1 is NOT DEGENERATE.** The disjoint-CI mechanism does not need replacing on the
ground the blind review named, and the 11-i-a / 11-i-b split can proceed.

**But three things the blind review did not name now need contract-freeze decisions**, and all
three are cheap to settle now and expensive after the table ships:

1. **D2's "smallest N that passes" over a non-monotone curve** (§5.3). Needs a monotone-run
   requirement or a different rule.
2. **The D2/D3 tension** (§6.3): the N that D2's gate demands is an N at which D3's measured
   false-adoption rate is 4.5–7.0% per measurement on an unchanged corpus.
3. **The gate's denominator** (§7.1): I chose the answered union; the design does not say.

And one already-known item is now **measured rather than argued**: FA3's cost claim (§8).
