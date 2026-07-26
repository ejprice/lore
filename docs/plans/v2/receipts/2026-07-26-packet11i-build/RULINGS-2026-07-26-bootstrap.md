# Packet 11-i — the bootstrap-seam rulings, 2026-07-26

**Ruled by `lead-11ia`.** These close STATE §6 open risks **4** and **5**, and dispose of the five
decisions raised by `probe-bootstrap-paired` under scope law.

**Source of record for every measurement cited here:**
`docs/plans/v2/receipts/2026-07-26-packet11i-build/REPORT-probe-bootstrap-paired.md` (this
directory). Numbers are **not** re-transcribed below — cite that report's section, never this file,
when you need the receipt.

**Who must read this:** 11-i-b's contract author, before writing a single pin. It is named as a
required read in that spawn brief. 11-i-a's author needs only §R-C and §R-D (the row shape).

---

## R-A — The resampling unit: `paired=True` does NOT fit. Two index samples, `paired=False`.

**RULED: adopt the report's §A.2 expression.** Pass **two index samples** with `paired=False`
(paired probes as group 1, identifier probes as group 2) and let the statistic gather both legs
from group 1's drawn indices. Zero bespoke resampling code; scipy's own idiom applied one level
down.

**Why this is a derivation and not a preference:** `paired=True` requires all samples to share a
length and collapses `data` to one shared index array, so it *cannot express* two independently
resampled groups of different sizes. That is read from the installed source, and the recommended
form is proven by **byte-exact oracle equality** against a hand-written paired resampler with a
draw-order-swapped control that fails. This is packages-over-hand-rolling landing on the right
side: the package does the job, and no hand-rolled resampler is authorised.

⚠ **The pin that does NOT work, and this is the load-bearing part:** an outcome pin on the CI
endpoints **cannot** distinguish the paired build from the arm-independent build — measured
identical on 21/30 corpora. The pin must instrument **what the statistic RECEIVED** (report §D.2).
A contract that pins only the interval has pinned nothing here.

## R-B — Seeding: pin `rng=`, never `random_state=`, never `None`.

**RULED.** They are **not aliases**: `rng=` normalises through `np.random.default_rng` →
`Generator(PCG64)`; `random_state=` reaches `check_random_state` → `RandomState(MT19937)`. Measured:
the same integer through the two names produces **different bootstrap distributions, with no warning
of any kind**. Passing both raises.

**Instrument (report §D.5), and it follows the repo's own instrument law:** do **not** enumerate
forbidden spellings — the forbidden set is unbounded. **Allowlist the safe**: exactly ONE function
may call `scipy.stats.bootstrap`, and a structural (AST) pin asserts that call site passes `rng=`
and never `random_state=` and never `None`.

⚠ A third silent stream exists: `rng=np.random.RandomState(3)` is **accepted** on numpy 2.5.1 and
yields a distribution different from both `rng=3` and `random_state=RandomState(3)`. The decorator's
own docstring reads as though this is rejected; that reading is falsified by measurement (report
§F.5). **One more receipt for the repo's "a doc is a source, not an oracle" law** — the same law
whose violation cost us #107.

## R-C — Explicit parameters, because three scipy defaults are traps

**RULED: `method`, `vectorized`, `batch`, `confidence_level` and `n_resamples` are ALL passed
explicitly at the seam and asserted there** (report §D.8). Each default is a live hazard, measured:

- **`method` defaults to `'BCa'`** — which ruled decision 21 explicitly **rules out** — and it
  silently returns a materially narrower interval **with no warning**. A builder who omits `method=`
  ships an interval the design pre-registered against. Pass `method="percentile"`.
- **`vectorized` is inferred** from whether the statistic merely *names* a parameter `axis`. A
  harmless-looking refactor therefore changes the contract silently. Pass `vectorized=False`.
- **`batch` changes the answer** whenever there is more than one sample, because it changes the
  interleaving of draws from the shared generator — measured to change the CI on **6 of 25** corpora,
  with a one-sample control proving batching itself is inert. **RULED: pin `batch=None` explicitly
  and RECORD it in the measurement row.** The value is a measure-then-tune item; the *explicitness*
  is not. **Re-open trigger:** a measured memory or wall-clock need — at which point the row already
  carries the old value, so the change is visible instead of silent.

## R-D — The served interval is NOT `result.confidence_interval`

**RULED.** scipy computes its interval with `method='linear'` (its `scipy.stats.quantile` default).
D8 pre-registers a **central 90% percentile** interval and this repo's convention is **nearest-rank**.
Take `.bootstrap_distribution` and apply `np.percentile(..., method="inverted_cdf")`, which is
measured **equal** to the repo's existing convention; do not serve scipy's interval.

⚠ **And the fixture rider, which is the half that gets dropped:** on our floor statistic the two
conventions **coincide on 24/25 corpora**, because the statistic is discrete. **A discrete-only
fixture waves the wrong build straight through.** The pin MUST carry a **continuous** leg (report
§C.5 measured the divergence on a bootstrapped mean). This is the "fixtures must discriminate" law
caught prospectively rather than by an auditor.

## R-E — The hold-out leg's anchor flag: RECOMPUTE over the reduced hit set [LEAD CALL]

The spec gap the probe found (report §F.1): `VerdictSample` carries
`(max_cosine, has_verbatim_anchor)`; the anchor is a property of the **shown hit set**; excluding the
probe's source file changes that set, so the flag can differ between the two legs — and design §3 is
**silent**. Two readings, and they produce different code: **(a)** recompute the anchor over the
reduced set (the paired unit carries four values) or **(b)** inherit it from the full capture (three).

**RULED: (a), recompute.** Marked a LEAD CALL and cheap to veto, but it is a derivation, and the
derivation is verified at source rather than argued:

1. **The predicate's own stated design principle is identity with production.**
   `loremaster/loremaster/search.py::_cosine_absence_predicate` exists as a separate pure function
   precisely so the survey can import *"the IDENTICAL predicate production fires on, never a
   re-derived paraphrase that can silently drift"* (S4b audit finding #1, in its docstring). In
   production the anchor is computed over the hits actually shown. The hold-out leg's whole job is to
   simulate that state, so every component of the sample must be computed over the hit set actually
   being scored.
2. **Reading (b) is a MIXED-BASIS sample** — cosine over the reduced set, anchor over the full set.
   That is finding **#180**'s exact defect class (*"calibrated on best-of-response cosines but applied
   to every individual hit"*), which is **open in this ledger and is one of the findings packet 11
   exists to resolve**. Shipping a new instrument carrying a fresh instance of the class the packet is
   fixing is not defensible.
3. **The anchor is a VETO, verified at source** (`search.py`: the predicate fires iff best_cosine is
   below floor **AND** no shown hit carries an anchor). Under (b), the very file removed to create the
   absence can **suppress the verdict its own removal was meant to measure**. The instrument would be
   blinded by the thing it excludes.

**Re-open trigger:** if R2's real corpus shows the two legs' anchors never actually differ, the
arity reduction is free and (b) becomes a legitimate optimisation. **Measure it in R2 before
assuming either way** — do not fold this into a build as an assumption.

## R-F — Identifier probes have no hold-out leg today, and the expression generalises

**RULED: carry one line in the contract saying so.** Identifier probes are the unpaired arm
(design §3, "port as-is"). If that ever changes, or a third probe group appears, the expression
generalises with **no new machinery** — N index samples, `paired=False`, one per group. The line
exists so nobody re-opens this later as a limitation of the chosen shape.

## R-G — The measurement row records `scipy.__version__` and `numpy.__version__`

**RULED: adopt** (report §F.3). The determinism guarantee is **scoped to a library version**: the
resample stream is scipy's internal per-sample, per-batch draw order, and no stream-stability
guarantee was found in the installed docstrings (the investigator states plainly that it did not
verify one exists — that honesty is why this ruling exists). A scipy or numpy upgrade could
therefore move a served floor interval on a **completely unchanged corpus**.

The row already carries `B`, `N`, `method` and — per R-C — `batch`. Adding two version strings is
free, and it makes the determinism pin the **detector** while the row is the **explanation**.
**Re-open trigger:** any scipy/numpy upgrade re-runs the determinism pin before the measurement row
is trusted across the version boundary.

This is an **11-i-a row-shape obligation** — the append-only row + `DEFINE FIELD OVERWRITE` design
(B4) makes adding it cheap by construction, which is exactly what that choice was for.

## R-H — Boundary fates are mapped, never surfaced raw

**RULED** (report §D.10). scipy raises `ValueError` when **either** group holds fewer than two
observations — measured at `n_identifier ∈ {0,1}` and `n_paired = 1`, OK at 2. The engine maps that
to the design's honest `insufficient_corpus` state (§7); it does **not** surface a raw scipy
`ValueError`. Pin 0, 1 and 2 for **each** group — force each fate with a fixture rather than
asserting a property where the branch cannot fire.

---

## What the archived S1 probe says that is true of ITSELF and false as a TEMPLATE

`docs/plans/v2/receipts/2026-07-24-packet11i/probe_bootstrap_degeneracy.py` carries a
`ProcedureBootstrap` docstring reading *"Resamples the union AND the absent arm JOINTLY"* while its
`one_replicate` resamples the two arms **independently**. **That is CORRECT for the instrument it
measured** — the legacy absent arm is a fixed nonsense-query set, genuinely unpaired with the union,
and "jointly" there means "in the same replicate". It is **not** correct as a template for the
portable hold-out instrument, whose absent arm *is* the answered probes.

S1's NOT-DEGENERATE verdict is load-bearing and the file is citable, so it gets a header note rather
than silent preservation, per archive law. **The verdict stands; only its reusability as a pattern
is qualified.**
