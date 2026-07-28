brief-base v7 read

# REPORT — probe-bootstrap-paired (packet 11-i, STATE §6 open risks 4 and 5)

> **Scope + date stamp, repeated here because a retrieved chunk arrives without its header:**
> every number in this report was **measured 2026-07-26** in the `lore-pkt11ia` worktree venv
> (branch `pkt11-i-a-floor-machinery` @ `38c9774`) against **scipy 1.18.0 · numpy 2.5.1 ·
> Python 3.14.6**. Nothing is carried from any document, including the ones the brief pointed at.
> Claims about scipy are claims about **1.18.0**, not about scipy in general.

---

## SUMMARY BLOCK

- **State:** done. Read-only; the only file written is this report.
- **Deviations:** none. (Probe scripts were run from the session scratch directory, never the
  worktree; per archive law a `/tmp` path is not a citable address, so the load-bearing code is
  reproduced verbatim in §A.2 and §A.5 below rather than cited.)
- **`Packages considered:`** `scipy.stats.bootstrap` (READ: installed `scipy/stats/_resampling.py`
  — `_bootstrap_iv`, `bootstrap`, `_bootstrap_resample`, `_vectorize_statistic`) → **`replace`**:
  it does express our unit, with **zero bespoke resampling code**, via two index samples ·
  `scipy.stats.quantile` (READ: installed signature, `method='linear'` default) → **`replace_with_adapter`**:
  scipy's own `.confidence_interval` does NOT implement D8's nearest-rank convention; use
  `numpy.percentile(..., method="inverted_cdf")` on `.bootstrap_distribution` (READ: measured
  byte-equal to `token_survey.percentile`) · `scipy._lib._util._transition_to_rng` (READ: full
  decorator source) → informs the `rng` ruling in §B. **No hand-rolled resampler is needed and none
  is recommended.**
- **A — resampling-unit verdict:** `paired=True` **does NOT fit**. From source: it requires all
  samples to share a length and then collapses `data` to **one** shared index array — it cannot
  express two independently-resampled groups of different sizes. **The minimal correct expression is
  scipy's own idiom applied one level down: pass TWO INDEX SAMPLES with `paired=False`** (paired
  probes as group 1, identifier probes as group 2) and let the statistic gather both legs from
  group 1's indices. Proven by **byte-exact oracle equality** with a hand-written paired resampler
  (`array_equal=True`, `bytes_equal=True`), with a draw-order-swapped control that is `False`.
- **B — `rng` vs `random_state`:** **pin `rng=`, always as a keyword, always with a fresh
  `numpy.random.Generator` (or an int).** They are **not aliases**: `rng=` is normalised by
  `np.random.default_rng` → `Generator(PCG64)`; `random_state=` reaches `check_random_state` →
  `RandomState(MT19937)`. Measured: **`rng=42` and `random_state=42` produce different bootstrap
  distributions**, with **NO warning of any kind** (`end_version` is None in the decorator).
  Passing both raises `TypeError`.
- **C — determinism:** **bit-identical, both legs.** In-process and across **5 separate processes**
  and **3 `PYTHONHASHSEED` values**, the CI endpoints are the same float64 bytes
  (`e3d4321860a1e03f8a3a1d89d341e13f`) and the full 1000-value distribution has the same SHA-256
  prefix (`f03edc62cd4f4000ff95b541c050a1e4`). Conditional on three things being pinned — `rng=`, a
  **fresh** generator per call, and `batch` — each demonstrated with a failing control.
- **Decisions needed (5):** the hold-out leg's **anchor flag** is spec-silent (§F.1 — two readings,
  different code) · whether identifier probes ever acquire hold-out legs (§F.2) · whether the
  measurement row records **scipy/numpy versions** (§F.3) · `batch`'s pinned value (§C.3) ·
  whether the archived probe gets a superseding header note (§F.4).
- **Receipt pointers:** §A.1 source facts · §A.2 the recommended call, verbatim · §A.3 the three
  wrong builds, measured · §A.4 why an outcome-only pin does NOT discriminate · §A.5 oracle
  equality · §B.1–B.6 the rng table · §C determinism legs · §D the 10 recommended pins · §E controls
  per claim · §F everything noticed outside the question.

---

## A — THE RESAMPLING UNIT

### A.0 What the unit IS (read from the ruled design, not assumed)

`docs/design/2026-07-24-floor-calibration.md` §3, "Known-absent probes — the hold-out
construction": each **answered probe** is scored **twice from one search call** —

- *answered leg*: max-cosine over **all** shown hits → contributes one observation to the **union**;
- *absent leg*: max-cosine over the **same hit list minus the probe's source file** → contributes
  one observation to the **hold-out/absent** arm.

So one probe produces **two observations in two different arms**. That is a paired unit, and it
carries a structural consequence I verified holds on every fixture I built: **absent ≤ answered,
per probe**, because the hold-out leg maxes over a *subset* of the answered leg's hits.

`docs/design/2026-07-24-floor-calibration.md` §3, "Identifier probes — port as-is": identifier
probes are **answered-only**. They enter the union (§3: *"measured on self-supervised answered +
identifier unions"*) and have **no** hold-out leg. That is the **unpaired arm**.

Therefore, at N probes: `|union| = n_paired + n_identifier`, `|absent| = n_paired`, and the two
groups must be resampled **independently of each other** while each paired probe's **two legs move
together**.

### A.1 What `paired=True` is, read from the installed source

`scipy/stats/_resampling.py::_bootstrap_iv`, the `if paired:` branch, does exactly two things:

1. **Rejects unequal lengths** — *"When `paired is True`, all samples must have the same length
   along `axis`"*;
2. **Replaces `data` with a single sample `xp.arange(n)`** and wraps the caller's statistic so it
   gathers every array at those indices.

**`paired=True` IS the index-array idiom** — over exactly **one** index set. That is the whole
mechanism, and it is why our structure does not fit: one index set cannot resample two groups of
different sizes independently.

Probed (all four legs in one run):

| leg | call | result |
|---|---|---|
| A1.a | `paired=True`, lengths (40, 16) | `ValueError: When 'paired is True', all samples must have the same length along 'axis'` |
| A1.b | **positive control** — `paired=True`, lengths (40, 40) | OK, distribution size 25 |
| A1.c | **differently-broken control** — `paired=False`, lengths (40, 16) | **OK** — so A1.a's rejection is about *pairing*, not about unequal lengths |
| A1.d | instrumented statistic, 20 calls each | `paired=True` → both arrays carry the **identical permutation**: `True`. `paired=False` → identical permutation: `False` |

A1.d is the check that stops A1.a from being a pass-for-the-wrong-reason: it shows the probe is
observing the pairing mechanism itself, not just an argument validator.

### A.2 The minimal correct expression (and it is not a workaround)

Pass **two index samples** with `paired=False`. Pairing then lives *inside* group 1, where the
design puts it; independence lives *between* the groups, where the design puts that. This is
**scipy's own mechanism** (`data_iv = [xp.arange(n)]` + a gathering wrapper), applied at the
granularity our design actually has.

```python
import numpy as np
from scipy.stats import bootstrap

def floor_statistic(paired_index, identifier_index):
    """The unit of observation is the PROBE: a paired index carries its answered leg
    into the union AND its hold-out leg into the absent arm."""
    union = (
        [answered_sample(i) for i in paired_index]
        + [identifier_sample(j) for j in identifier_index]
    )
    absent = [holdout_sample(i) for i in paired_index]
    return choose_cosine_floor(union, absent, max_false_fire_rate=...).floor

result = bootstrap(
    (np.arange(n_paired), np.arange(n_identifier)),
    floor_statistic,
    paired=False,                     # the two GROUPS are independent
    vectorized=False,                 # explicit — see C.4
    n_resamples=1000,                 # Addendum D1: B >= 1000
    batch=None,                       # PINNED and RECORDED — see C.3
    method="percentile",              # decision 21; scipy's default is BCa
    confidence_level=0.90,            # D8 central 90%, two-sided
    rng=np.random.default_rng(seed),  # a FRESH generator per call — see B and C.2
)
ci_low  = float(np.percentile(result.bootstrap_distribution, 5.0,  method="inverted_cdf"))
ci_high = float(np.percentile(result.bootstrap_distribution, 95.0, method="inverted_cdf"))
```

**Residual bespoke surface: the statistic (domain code) and one `np.percentile` call.** No
resampling loop, no seed plumbing, no interval arithmetic. That satisfies the packages rule's
minimal-surface clause without a parallel re-implementation.

`confidence_level=0.90` with the default `alternative='two-sided'` **is** the central 90% interval —
verified directly: scipy's own CI equals `np.percentile(dist, [5, 95])` on a control distribution.

### A.3 The three alternatives, measured rather than assumed

Same corpus (`n_paired=40`, `n_identifier=16`, `|union|=56`, `|absent|=40`), same seed, B=1000,
point floor `0.519699`:

| expression | measured CI (nearest-rank) | verdict |
|---|---|---|
| **(1) two index samples, `paired=False`** | `[0.519699, 0.539285]` | **CORRECT** |
| (2) **arm-independent** — resample the 56-value union and the 40-value absent arm separately (the archived probe's shape) | `[0.519699, 0.539285]` | WRONG — destroys the pairing |
| (3) `paired=True` over the four paired arrays (answered cos/anchor + hold-out cos/anchor) | `[0.525841, 0.544211]` | WRONG — **runs**, and silently drops the entire identifier arm from the union |
| (4) **"pass the pair as one sample of tuples"** — a 2-D sample with `axis=0`, `vectorized=False` | *no error at all* | **WRONG AND SILENT** — see below |

**(4) is the dangerous one and it must be banned by name.** It is **ACCEPTED with no error**:
`_vectorize_statistic` concatenates along the working axis and `np.apply_along_axis` then calls the
statistic **once per column per resample** — measured **8 calls for 4 resamples**, each receiving
shapes `((40,), (16,))`, i.e. **one channel at a time, with the pair split apart**. The returned
`confidence_interval.low` has shape `(2,)` and `bootstrap_distribution` has shape `(2, 4)`. A
contract author who tries this candidate gets a plausible-looking result object containing garbage.

Across 10 corpora × 2 hold-out-anchor rates (B=200 each), **at least one wrong shape produced a
different interval in 18 of 20 cases**; shape (3) alone differed in most of them.

### A.4 ⚠ THE PIN THAT WOULD NOT HAVE WORKED — an outcome-only pin does not discriminate

This is the most important thing in the report for whoever writes 11-i-b's contract.

Asked of my own fixtures: *"what wrong build would this still pass?"* — and the answer was **the
arm-independent build**. Over **30 independently drawn corpora** at B=400, the correct expression
and the arm-independent one produced the **identical CI endpoints in 21 of 30** (they differed in
9/30; mean widths `0.050358` vs `0.050034`). On the headline corpus they were identical to the last
bit. **A pin that asserts CI endpoints would have waved the wrong build through on 70% of corpora.**

The discriminating pin has to be on the **mechanism**, and there it is absolute. Instrumenting the
two expressions and reading which indices each leg actually received, over 2000 replicates:

- correct expression: **one** index array per unit exists — the two legs *cannot* disagree, because
  there is nothing for them to disagree with (structural, 2000/2000 calls shaped as declared);
- arm-independent: the hold-out arm's indices coincide with the union's paired-part indices in
  **0 of 2000 (0.00%)** of replicates.

Secondary, and useful as a numeric pin: the dispersion of `mean(answered) − mean(hold-out)` across
replicates is **0.006325** under the correct unit and **0.012001** under independent arms — pairing
is exactly what controls that spread, and a ~1.9× difference is easy to assert.

### A.5 Oracle equality — is scipy's shell *exactly* the paired resampler we want?

A hand-written reference draws the same indices scipy's loop draws (`rng.integers(0, n, (batch, n))`
per sample, **in sample order, per batch** — read from `bootstrap`'s batch loop and
`_bootstrap_resample`) and evaluates the same statistic:

```python
def reference(n_paired, n_identifier, n_resamples, batch, rng):
    out, batch_nominal = [], batch or n_resamples or 1
    for k in range(0, n_resamples, batch_nominal):
        b = min(batch_nominal, n_resamples - k)
        pi = rng.integers(0, n_paired,     (b, n_paired),     dtype="int64")
        ii = rng.integers(0, n_identifier, (b, n_identifier), dtype="int64")
        for r in range(b):
            out.append(floor_statistic(pi[r], ii[r]))
    return np.array(out, dtype=np.float64)
```

- **reference == `scipy`'s `bootstrap_distribution`: `array_equal=True`, `bytes_equal=True`** (B=1000).
- **Differently-broken control:** the same reference with only the **draw order** of the two samples
  swapped → `array_equal=False`. So the equality test can fail, and the agreement is not vacuous.

**Do not ship the reference.** It is a probe instrument, not a second implementation — keeping it
would be copy #2 of a library primitive, and it pins a scipy *internal* (per-sample draw order) that
carries no correctness meaning. The honest guard for the same risk is the determinism pin (§D.6),
which reddens if a scipy upgrade changes the stream. See §F.3.

---

## B — `rng` VS `random_state` IN scipy 1.18.0

### B.1 The mechanism, from source

`bootstrap` is decorated `@_transition_to_rng('random_state')` with **no `end_version`** and **no
`position_num`**. Consequences, each read from `scipy/_lib/_util.py::_transition_to_rng` and then
measured:

1. `random_state` is **not a real parameter**. The decorator *appends* it to
   `wrapper.__signature__` as a keyword-only parameter. Measured: `inspect.signature(bootstrap)`
   lists `[..., 'rng', 'random_state']`; `inspect.signature(bootstrap.__wrapped__)` lists
   `[..., 'rng']` and nothing else. *(This resolves F-r2 §R9.1's "both exist in 1.18.0" — they
   exist in the signature object; only one exists in the function.)*
2. `rng=<value>` (keyword) → the decorator runs `np.random.default_rng(value)` → a
   **`Generator`**.
3. `random_state=<value>` (keyword) → the decorator **renames it to `rng` without normalisation**;
   it then reaches `_bootstrap_iv`'s `check_random_state`, which turns an int into
   **`np.random.RandomState`** (MT19937) and `None` into the **global `np.random` singleton**.
4. `rng_integers` dispatches on type: `Generator` → `.integers(...)`; `RandomState` → `.randint(...)`.
   **Different families, different algorithms, different streams.**

### B.2 Measured consequences

| # | probe | result |
|---|---|---|
| B.a | `rng=42` vs `random_state=42`, everything else identical | **bootstrap distributions differ** (`array_equal=False`) |
| B.a | the underlying streams | `default_rng(42).integers(0,40,5) = [3, 30, 26, 17, 17]` vs `RandomState(42).randint(0,40,5) = [38, 28, 14, 7, 20]` |
| B.b | **positive control** — same name, same seed, twice | identical for **both** names (so B.a's difference is the parameter, not noise) |
| B.c | both passed | `TypeError: bootstrap() got multiple values for argument now known as 'rng'. Specify one of 'rng' or 'random_state'.` |
| B.d | warnings emitted when using `random_state=` | **NONE** — no `DeprecationWarning`, no `FutureWarning` |
| B.e | a `RandomState` **instance** | `random_state=` accepted; `rng=` **also accepted** (numpy 2.5.1's `default_rng` wraps it → `Generator(MT19937)`) — and the two give **different** results (`array_equal=False`), because one calls `.integers()` and the other `.randint()` on the same bit generator |
| B.e′ | a `SeedSequence` | `rng=` accepted; `random_state=` raises `ValueError: 'SeedSequence(entropy=3)' cannot be used to seed a numpy.random.RandomState instance` |
| B.f | `random_state=None` | reads the **global `np.random` singleton**: reproducible only if you re-seed `np.random.seed(11)` (measured identical), and **not reproducible** without it (measured different — the global state is consumed) |
| B.f′ | `rng=None` | fresh OS entropy; **not** reproducible even under `np.random.seed` (measured different) |
| B.g | **control** — `rng=3` under `np.random.seed(1)` vs `np.random.seed(2)` | identical → `rng=<int>` is genuinely insulated from global state |

### B.3 Recommendation

**Pin `rng=`, passed as a keyword, with a fresh `numpy.random.Generator` (or a plain int).**

- It is the parameter the function actually has; `random_state` exists only as a decorator alias.
- It is insulated from `np.random`'s global state (B.g) — which is what C1's
  no-module-level-randomness discipline is *for*, and `random_state=None` reads that global state
  by design (B.f).
- It accepts the type set we want (`Generator`, `SeedSequence`, int) and is the API that survives
  the transition.

**Drift risk of the other, stated plainly and sharper than STATE §6 risk 4 framed it.** Risk 4 calls
this *"#198's drift class waiting to happen"*, i.e. a naming-duplication hazard. It is worse than
that: **the two names select different random-number families and therefore different numbers**,
and because `end_version` is None there is **no warning at all** to catch it. A future scipy that
finishes the transition will delete the alias — at best a `TypeError` (loud, fine), at worst, if a
call site is ever edited from one name to the other, **a silently changed served floor interval on
an unchanged corpus**, which is precisely the property 11-i must prove. The mitigation is not a
convention; it is §D.5's structural pin.

---

## C — DETERMINISM

### C.1 In-process — bit-identical

Two calls, each given a **fresh** `np.random.default_rng(20260726)`, B=1000:

```
run1 ci hex = e3d4321860a1e03f8a3a1d89d341e13f
run2 ci hex = e3d4321860a1e03f8a3a1d89d341e13f
bit-identical endpoints: True
bit-identical full distribution (1000 float64s): True
```

Passing the int seed directly (`rng=20260726`) is identical to passing a fresh
`default_rng(20260726)` — measured `True` — so either form is acceptable.

### C.2 Cross-process — bit-identical, and hash-seed independent

Five separate interpreter processes, three `PYTHONHASHSEED` values (`0`, `1`, `12345`, and unset
twice). Every one printed the same endpoint bytes and the same distribution digest:

```
pid=2933753 PYTHONHASHSEED=0     ci_hex=e3d4321860a1e03f8a3a1d89d341e13f dist_sha=f03edc62cd4f4000ff95b541c050a1e4
pid=2934006 PYTHONHASHSEED=1     ci_hex=e3d4321860a1e03f8a3a1d89d341e13f dist_sha=f03edc62cd4f4000ff95b541c050a1e4
pid=2934150 PYTHONHASHSEED=12345 ci_hex=e3d4321860a1e03f8a3a1d89d341e13f dist_sha=f03edc62cd4f4000ff95b541c050a1e4
pid=2934303 PYTHONHASHSEED=<unset> …same…
pid=2934449 PYTHONHASHSEED=<unset> …same…
```

The cross-process bytes are the **same** as the in-process bytes in C.1. `choose_cosine_floor`'s
candidate set is built with `sorted({...})` over floats, so it carries no hash-order dependence —
the hash-seed sweep confirms that rather than assuming it.

**DIFFERENTLY-BROKEN CONTROL (this is what proves C.1/C.2 are not vacuous):** **reusing one
`Generator` object across two calls** consumes its state → the second call's distribution differs
(`array_equal=False`). Bit-identity is therefore a property of *how the generator is supplied*, and
the pin must assert the fresh-generator discipline, not merely "we passed a seed somewhere".

### C.3 ⚠ `batch` IS LOAD-BEARING FOR REPRODUCIBILITY — and only because we have two samples

From `bootstrap`'s batch loop: for each batch it iterates **over the samples** and calls
`_bootstrap_resample` for each. With **more than one sample**, changing `batch` changes the
**interleaving** of draws from the shared generator, hence the resample indices, hence the answer.

| leg | measurement |
|---|---|
| our shape (2 samples), same seed, B=400 | `batch=None` vs `batch=100` → distributions **differ**; `batch=None` vs `batch=1` → **differ** |
| CI impact, headline corpus | endpoints happened to coincide — the statistic is discrete (10 distinct floors), so a changed resample often lands on the same order statistic. **That is luck, not stability.** |
| CI impact, across 25 corpora | `batch=None` vs `batch=7` **changes the CI on 6 of 25** |
| **CONTROL — ONE sample**, same sweep | `batch=None` vs `batch=100` → **identical**; vs `batch=1` → **identical** |

The control is what names the cause: batching itself is inert; the **per-batch interleaving across
samples** is the mechanism. So `batch` must be an explicit, pinned, **recorded** parameter of the
measurement — a future memory/performance tweak that changes it would otherwise silently move a
served interval on an unchanged corpus.

### C.4 `vectorized` and `method` are silent-default traps

- **`vectorized`**: scipy infers it as `'axis' in inspect.signature(statistic).parameters`
  (measured: a statistic that merely *names* a parameter `axis` is auto-treated as vectorized). A
  harmless-looking refactor that adds an `axis` parameter changes the contract silently. **Pass
  `vectorized=False` explicitly.**
- **`method`**: scipy's default is **`'BCa'`**, which decision 21 rules out. Measured on the
  headline corpus: default (BCa) gives `(0.519699, 0.525841)` against percentile's
  `(0.519699, 0.539285)` — a **materially narrower** interval — **with no warning raised**. **Pass
  `method="percentile"` explicitly.**

### C.5 ⚠ THE INTERVAL CONVENTION — and a second collapsed fixture I had to control for

`bootstrap` computes its interval with `scipy.stats.quantile(theta_hat_b, interval, axis=-1)` — no
`method` argument, so **`method='linear'`**, scipy's default (read from the installed
`scipy.stats.quantile` signature). D8 pre-registers a *central 90% percentile* interval, and the
repo's convention (`token_survey.percentile`, and `choose_cosine_floor`'s own candidate rule) is
**nearest-rank**.

On our floor statistic they *appear* to agree:

```
scipy .confidence_interval            = [0.5196991417530196, 0.5392854383479329]
np.percentile(inverted_cdf)           = [0.5196991417530196, 0.5392854383479329]
token_survey.percentile (nearest-rank)= [0.5196991417530196, 0.5392854383479329]
```

**That agreement is a fixture artifact, not a fact about the conventions.** The floor statistic is
**discrete** (its values are observed cosines), so linear interpolation between two *equal* order
statistics returns the same number. Controls:

- on a **continuous** statistic (bootstrapped mean cosine), same code path, same call:
  scipy `(0.5868024046617173, 0.6100252825825457)` vs nearest-rank
  `(0.5867608923210502, 0.6100217644016839)` — **different**, `Δlow = +4.151e-05`;
- on **our** statistic across 25 corpora, scipy's CI differs from the repo's nearest-rank CI in
  **1 of 25** — rare, non-zero, and unpredictable.

**Measured and confirmed (this is R9.2's proposal, verified rather than inherited):**
`np.percentile(dist, p, method="inverted_cdf")` **equals** `token_survey.percentile(dist, p)` on our
data (`True`), while `method="linear"` does not. So: take `.bootstrap_distribution` and apply
`inverted_cdf`; **do not serve `result.confidence_interval`.** A discrete-only fixture would pass a
build that serves scipy's interval — §D.7's pin must therefore carry a continuous leg.

---

## D — THE PINS 11-i-b's CONTRACT SHOULD CARRY

Phrased so a contract author can act on them. Each names the wrong build it kills.

1. **`D.1` Call-shape pin.** The bootstrap seam passes exactly **two index samples** with
   `paired=False`. *Kills:* the `paired=True` build (which cannot even run at unequal sizes) and the
   4-array drop-the-identifier-arm build (which runs and differs on most corpora).
2. **`D.2` PAIRING MECHANISM pin — assert on what the statistic RECEIVED, not on the interval.**
   Instrument the statistic; assert that for every replicate the hold-out observations are exactly
   the hold-out legs **of the drawn paired indices**. *Kills:* the arm-independent build. **⚠ An
   outcome pin on CI endpoints does NOT kill it — measured identical on 21/30 corpora (§A.4).** If
   you want a numeric leg alongside, pin the dispersion of `mean(answered) − mean(hold-out)`
   (measured 0.006325 paired vs 0.012001 independent).
3. **`D.3` Identifier-arm-present pin.** A fixture in which the identifier probes materially move
   the floor, asserting the distribution changes when that arm changes. *Kills:* any build that
   drops or merges the unpaired arm.
4. **`D.4` No-2-D-samples pin.** Ban the "one sample of tuples" shape structurally (assert every
   sample passed to `bootstrap` is 1-D integer). *Kills:* candidate (4), which **produces no error**
   — an `(2, N)` distribution and a 2-vector CI (§A.3).
5. **`D.5` `rng=` pin, deny-by-default with an allowlisted seam.** Per the repo's own instrument
   lesson: do not enumerate forbidden spellings. **Allowlist the safe** — exactly one function may
   call `scipy.stats.bootstrap`, and a structural (AST) pin asserts that call passes `rng=` and
   never `random_state=`, and never `None`. *Kills:* the silent MT19937/PCG64 swap (§B.2) and the
   global-singleton door.
6. **`D.6` Determinism pin, on BYTES, with its own failing control.** Same seed → **identical
   float64 bytes** for `ci_low`/`ci_high` (not `round()`, not `pytest.approx`), asserted
   in-process **and** in a subprocess. Include the control leg that makes it a real pin: **reusing
   one `Generator` object across two calls must NOT be bit-identical.** This is the direct
   instrument for 11-i's MUST-PROVE "an unchanged corpus reproduces its measurement".
7. **`D.7` Interval-convention pin, WITH a continuous leg.** The served interval is
   `np.percentile(.bootstrap_distribution, [5, 95], method="inverted_cdf")`, never
   `result.confidence_interval`. **The fixture must include a continuous statistic**, because on the
   discrete floor statistic the two conventions coincide on 24/25 corpora and a discrete-only
   fixture waves the wrong build through (§C.5).
8. **`D.8` Explicit-parameter pin.** `method="percentile"`, `vectorized=False`, `confidence_level=0.90`,
   `n_resamples>=1000`, `batch=<pinned>` are all passed **explicitly** and asserted at the seam.
   *Kills:* the BCa default (measured materially narrower, no warning) and the `axis`-in-signature
   auto-vectorization trap.
9. **`D.9` `batch` recorded in the measurement row** beside `B`, `N`, and `method`. *Reason:*
   changing `batch` changes the resample stream whenever there is more than one sample — measured to
   change the CI on 6/25 corpora, with a one-sample control proving batching itself is inert (§C.3).
10. **`D.10` Boundary pin — force each fate.** scipy raises
    `ValueError: each sample in 'data' must contain two or more observations along 'axis'` when
    **either** group has fewer than 2 observations. Measured: `n_identifier ∈ {0, 1}` → raise;
    `n_identifier = 2` → OK; `n_paired = 1` → raise; `n_paired = 2` → OK. The engine must map that
    to the design's honest `insufficient_corpus` state (§7), **not** surface a raw scipy
    `ValueError`. Pin 0, 1, and 2 for each group.

**Plus one hazard worth a cheap assert (not a full pin):** if a *value* array is ever passed
alongside an index array, `_vectorize_statistic`'s concatenate **promotes the index array to
float64** — measured: the statistic received `(float64, float64)` where it expected
`(int64, int64)`. Both samples must be integer index arrays; a one-line dtype assert at the top of
the statistic costs nothing and makes the failure loud.

---

## E — CONTROLS, PER CLAIM

| claim | positive control | differently-broken control |
|---|---|---|
| `paired=True` rejects our shape (A1.a) | `paired=True` at equal lengths succeeds (A1.b) | `paired=False` at unequal lengths succeeds (A1.c) — so the rejection is about pairing, not lengths |
| the probe sees the pairing mechanism (A1.d) | `paired=True` → identical permutation `True` | `paired=False` → identical permutation `False` |
| scipy's shell == the paired resampler (A.5) | byte-equality `True` | draw-order-swapped reference → `False` |
| `rng=42` ≠ `random_state=42` (B.a) | same name + same seed twice → identical, both names (B.b) | `rng=3` unaffected by `np.random.seed` (B.g), while `random_state=None` **is** affected (B.f) |
| bit-identical determinism (C.1, C.2) | 5 processes × 3 hash seeds → same bytes | reusing one `Generator` across calls → **not** identical |
| `batch` changes the stream (C.3) | two-sample sweep differs | **one-sample** sweep identical → names interleaving as the cause |
| `inverted_cdf` == repo nearest-rank (C.5) | equality `True` on our data | `method="linear"` differs; continuous statistic separates the conventions by `4.15e-05` |
| the fixture can distinguish wrong builds | 18/20 corpora show a differing interval for at least one wrong shape | **21/30 corpora show NO difference for the arm-independent build** — the reason D.2 must pin the mechanism, not the outcome |

Fixtures were interrogated with *"what wrong build would this still pass?"*, and that question
**changed two conclusions**: the CI-endpoint pin (§A.4) and the percentile-convention pin (§C.5)
were both collapsed on first construction and both are reported here with their controls.

---

## F — RAISED UNDER SCOPE LAW (noticed outside the question; you decide)

1. **⚠ SPEC GAP, and it lands directly on the statistic I was asked to specify: what is the
   hold-out leg's ANCHOR FLAG?** `VerdictSample` is `(max_cosine, has_verbatim_anchor)`, and
   `search_score_survey.QueryCapture` documents `has_verbatim_anchor` as *"True iff **ANY hit's**
   `ident_text` carries a verbatim-identifier anchor"* — a property of the **shown hit set**.
   Excluding the probe's source file changes that set, so the flag **can differ between the two
   legs**. Design §3 defines the hold-out leg purely in terms of max-cosine and is silent on the
   anchor. **Two readings, and they produce different code:**
   *(a)* the anchor is **recomputed** over the reduced hit set → the paired unit carries **four**
   values `(answered_cos, answered_anchor, holdout_cos, holdout_anchor)`;
   *(b)* the anchor is **inherited** from the full capture → the unit carries **three**.
   **I would pick (a)**: the hold-out leg exists to sample "the corpus's best response when the real
   answer is not there", and `cosine_absence_verdict_fires` consumes the anchor as a *veto* — an
   anchor supplied by the very file being held out would let the excluded answer suppress the
   verdict it was removed to measure. But this is a design decision, not mine, and per repo law a
   sentence admitting two readings is a **STOP**, not a contract-author judgement call. *(My probe
   used reading (a); the §A verdict is unaffected either way — the arity of the paired unit changes,
   the expression does not.)*
2. **Do identifier probes ever acquire hold-out legs?** Design §3 says they "port as-is", so today
   they are the unpaired arm — which is what your brief states and what I measured against. If that
   ever changes, or if a third probe group appears, the expression **generalises with no new
   machinery**: N index samples with `paired=False`, one per group. Worth one line in the contract
   so nobody re-opens it as a limitation.
3. **The determinism guarantee is scoped to a library version, and nothing currently records it.**
   The resample stream is produced by scipy's internal per-sample, per-batch draw order. I did not
   find a stream-stability guarantee in the installed docstrings **and I did not verify that one
   exists** — so a scipy or numpy upgrade could change a served floor interval on a completely
   unchanged corpus. Cheap mitigation, and it fits D5/D8's existing row shape: **record
   `scipy.__version__` and `numpy.__version__` in the measurement row**, alongside `B`, `N`,
   `method`, and `batch`. Then §D.6's determinism pin is the detector and the row is the
   explanation. Named re-open trigger: **any scipy/numpy upgrade** re-runs D.6 before the measurement
   row is trusted across the version boundary.
4. **The archived probe's docstring says something a contract author will carry forward wrongly.**
   `probe_bootstrap_degeneracy.py::ProcedureBootstrap`'s docstring reads *"Resamples the union AND
   the absent arm JOINTLY (Addendum D1)"*, while its `one_replicate` resamples the two arms
   **independently**. **That was CORRECT for the instrument it measured** — the legacy absent arm is
   the fixed 15-query `NONSENSE_QUERIES` set, which is genuinely unpaired with the union, and D1's
   "jointly" means "in the same replicate". It is **not** correct as a template for the portable
   hold-out instrument, where the absent arm *is* the answered probes. Since S1's verdict is
   load-bearing and the file is archived and citable, I recommend a **one-line header note** on it:
   *"the resampler here is the LEGACY unpaired shape; the portable instrument's unit is paired — see
   this report §A."* Archive law already contemplates exactly this (a superseded-in-part header
   rather than silent preservation). **Your call — I wrote no file but this report.**
5. **A vendor doc claim that is false-adjacent, in the exact area we are pinning.**
   `_transition_to_rng`'s own docstring states that *"`np.random` or an instance of `RandomState`
   … will result in an error."* That sentence is scoped to **positional** use, which `bootstrap`
   does not permit (`position_num` is None) — so it is not strictly false. But the reading a
   careful engineer takes from it — that `RandomState` is rejected under the new `rng` semantics —
   **is falsified by measurement**: `rng=np.random.RandomState(3)` is **silently accepted** on numpy
   2.5.1 (`default_rng` wraps it into `Generator(MT19937)`) and yields a **third distinct stream**,
   different from both `rng=3` and `random_state=RandomState(3)`. Filed here as the §D.5 pin's
   justification, and as one more receipt for the repo's *docs are a source, not an oracle* law.
6. **Type-set asymmetry between the two names**, for completeness: `rng=` accepts `SeedSequence`,
   `random_state=` rejects it (`ValueError`). Another reason a name swap is not a rename.
7. **STATE §6 risks 4 and 5 can both be closed** on the strength of §A, §B and §C — subject to F.1,
   which is a *design* question the sidecar's honest "I read the signature, not the full paired
   semantics" did not reach either.
