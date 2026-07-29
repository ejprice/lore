"""Equality pins for the shared nearest-rank percentile seam (finding #198).

Finding #198: ``weighted_percentile`` was hand-rolled twice, and the same
nearest-rank policy a further two times under the name ``percentile`` — FOUR
copies, in three signatures and two unit conventions.  **THREE of the four** now
route to :mod:`loremaster.stats`, a thin face over
``numpy.quantile(..., method="inverted_cdf")``.  The fourth —
``docs/eval/smoke_p8b.py::percentile`` — **deliberately keeps its own copy** so the
deploy smoke stays self-contained and acquires no new imports at all; it is held
equal by :class:`TestSmokeP8bPercentileUnits` instead (a pinned known bound).
The three shared faces:

* :func:`loremaster.stats.nearest_rank_quantile` — the ``[0, 1]`` fraction core
* :func:`loremaster.stats.nearest_rank_percentile` — the ``[0, 100]`` percent face
* :func:`loremaster.stats.weighted_nearest_rank_percentile` — the weighted face,
  which ENFORCES the ``weights > 0`` its predecessor only promised (RULING 1)

**Why this file exists, and what would make it worthless.**  Swapping an
estimator silently changes every number the old one published.  These pins
therefore do not merely check that the new seam *runs*; they check that it is
**equal to the retired hand-roll it replaced**, over a corpus that deliberately
includes the boundaries where quantile conventions actually disagree
(``pct`` at 0 and 100, single- and two-element samples, ties, unsorted input).

The retired ceil-rank implementation is kept below as
:func:`_retired_ceil_rank_oracle` — **as a test oracle only**.  It is not live
code and must never be called by anything outside this file; it exists so the
migration can be proven by equality against the thing it replaced rather than
against the new code's own author's intent.

``TestTheHarnessCanFail`` is the control leg: it feeds plausible-but-wrong
mappings (interpolating ``method="linear"``; a dropped percent→fraction unit
conversion) through the *same* corpus and asserts they DISAGREE.  A harness that
cannot fail cannot pass — without this leg an "all equal" result would be
consistent with a corpus too weak to discriminate anything.

**Placement took three passes and the reasoning is worth keeping.**  The seam
first lived in ``scripts/survey_stats.py``.  That is wrong twice over: production
code (packet 11-i-b's floor-calibration engine) cannot import from ``scripts/``,
which is not a package and is not in the image — so the very consumer #198 exists
to protect would have written copy #5 — and it forced ``sys.path`` manipulation on
callers, which measurably broke the deploy smoke when run detached from the repo.
The seam is therefore an installed module, mirroring the #207 fix that put the
shared backoff policy in ``loresigil/backoff.py``.

Measured 2026-07-26 on numpy 2.5.1, branch ``pkt11-i-a-floor-machinery``.
"""

from __future__ import annotations

import math
import random
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
import pytest

from loremaster import stats

# The seam under test is an installed module, imported normally above.
#
# Its CONSUMERS, however, are scripts that are deliberately NOT packages, so
# reaching them needs a path insert. This is the established idiom for exactly
# this situation in this directory — see ``test_backoff_seam.py``, which pins the
# #207 shared-backoff seam against the same ``token_survey`` consumer the same
# way. The direction matters and is the whole point of finding #198's third
# ruling: a TEST may reach out into ``scripts/`` and ``docs/eval/``, because if
# that import breaks, this gated suite goes red and we find out. The REVERSE —
# production code reaching into ``scripts/`` — is what was reverted, because
# nothing gates it and the break would be silent.
_REPO_ROOT = Path(__file__).resolve().parents[2]
for _consumer_dir in (_REPO_ROOT / "scripts", _REPO_ROOT / "docs" / "eval"):
    if str(_consumer_dir) not in sys.path:
        sys.path.insert(0, str(_consumer_dir))

# ``smoke_p8b`` comes from ``docs/eval/``. ⚠ CORRECTED 2026-07-29 (packet 44):
# this comment used to say that tree "is not in ``testpaths`` (finding #238) — so
# the smoke's own suite never runs in the standard gate". **#238 CLOSED that on
# 2026-07-26**: ``docs/eval`` is in ``testpaths`` and its suite runs in the
# standard gate; packet 44 added the type gate too. The percentile is still
# pinned from HERE — see :class:`TestSmokeP8bPercentileUnits` for what that now
# rests on, since the reason above is no longer one of them.
import smoke_p8b as smoke  # type: ignore[import-not-found]  # noqa: E402
import survey_txn_contention_102 as txn  # type: ignore[import-not-found]  # noqa: E402
import token_survey as ts  # type: ignore[import-not-found]  # noqa: E402

# --------------------------------------------------------------------------- #
# The retired implementation, preserved ONLY as an equality oracle
# --------------------------------------------------------------------------- #
#: The percentiles production actually asks for, plus the boundaries and their
#: neighbours.  ``token_survey`` uses 5/95; ``survey_txn_contention_102`` uses
#: 50/90/99.  Pinning ONLY the live values would be parameter-value monoculture
#: — a wrong build that is correct at 5 and 95 and wrong everywhere else would
#: pass.  Pinning ONLY synthetic values would miss a regression in the numbers
#: this repo has actually published.  Both are therefore present.
PCT_GRID: tuple[float, ...] = (0, 1, 2.5, 5, 25, 33.3, 50, 66.7, 75, 90, 95, 99, 100)

#: Live call-site values, asserted to be a subset of the grid below so this
#: claim cannot silently rot if a caller starts asking for a new percentile.
LIVE_PCTS: tuple[float, ...] = (5, 50, 90, 95, 99)


def _retired_ceil_rank_oracle(values: Sequence[float], pct: float) -> float:
    """The RETIRED hand-rolled nearest-rank percentile — TEST ORACLE ONLY.

    Byte-for-byte the body that lived in
    ``survey_txn_contention_102.weighted_percentile`` (and, via uniform weights,
    the one in ``token_survey.weighted_percentile``) before finding #198 deleted
    them.  Kept so the replacement can be proven EQUAL to what it replaced.

    Do not call this from production code.  It is the corpse, retained for
    identification purposes.
    """
    if not values:
        raise ValueError("cannot take a percentile of zero observations")
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


def _retired_cumulative_weight_oracle(
    pairs: Sequence[tuple[float, float]], pct: float
) -> float:
    """The RETIRED weighted hand-roll from ``token_survey`` — TEST ORACLE ONLY.

    The equality oracle for the WEIGHTED port (RULING 1): over the admissible
    domain (every weight > 0) this and ``np.quantile(..., weights=)`` are the
    same function, which is what licensed replacing it.  Where they disagree —
    zero weights — the production guard now refuses the input outright; see
    :class:`TestTheWeightGuard`.
    """
    if not pairs:
        raise ValueError("weighted_percentile requires at least one (value, weight)")
    ordered = sorted(pairs, key=lambda vw: vw[0])
    total_weight = math.fsum(weight for _value, weight in ordered)
    threshold = (pct / 100.0) * total_weight
    cumulative = 0.0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= threshold:
            return value
    return ordered[-1][0]


# --------------------------------------------------------------------------- #
# The corpus — each entry names the axis it exists to cover
# --------------------------------------------------------------------------- #
def _named_fixtures() -> list[tuple[str, list[float]]]:
    """Hand-built fixtures, one per boundary axis the brief names."""
    return [
        ("single-element", [7.5]),
        ("two-elements", [2.0, 9.0]),
        ("two-elements-reversed", [9.0, 2.0]),
        ("all-equal-values", [4.0] * 6),
        ("duplicate-values", [1.0, 2.0, 2.0, 2.0, 5.0]),
        ("unsorted", [9.0, 1.0, 5.0, 3.0, 7.0]),
        ("already-sorted", [1.0, 3.0, 5.0, 7.0, 9.0]),
        ("descending", [9.0, 7.0, 5.0, 3.0, 1.0]),
        ("negative-values", [-5.0, -1.0, 0.0, 2.0]),
        ("floats-near-each-other", [1.0000001, 1.0000002, 1.0000003]),
        # n chosen so pct/100*n lands EXACTLY on an integer for several grid
        # values (n=40: 5%->2, 25%->10, 50%->20, 75%->30, 95%->38).  Exact-hit
        # ranks are where ceil-rank and interpolating conventions diverge, so a
        # corpus without them cannot discriminate.
        ("exact-rank-boundaries-n40", [float(i) for i in range(40)]),
        ("n20-exact-and-inexact", [float(i) * 0.5 for i in range(20)]),
        ("large-magnitude", [1e9, 2e9, 3e9]),
        ("tiny-magnitude", [1e-9, 2e-9, 3e-9]),
    ]


def _randomized_fixtures(trials: int, seed: int) -> list[tuple[str, list[float]]]:
    """Seeded random samples across a spread of sizes and value shapes."""
    rng = random.Random(seed)
    out: list[tuple[str, list[float]]] = []
    for i in range(trials):
        n = rng.randint(1, 60)
        shape = i % 3
        if shape == 0:  # small integer pool -> many ties
            values = [float(rng.randint(0, 5)) for _ in range(n)]
        elif shape == 1:  # continuous
            values = [rng.uniform(-100.0, 100.0) for _ in range(n)]
        else:  # heavy-tailed, the shape latency samples actually have
            values = [rng.lognormvariate(0.0, 1.5) for _ in range(n)]
        out.append((f"random[seed={seed},i={i},n={n},shape={shape}]", values))
    return out


#: The full corpus.  200 randomized fixtures × 13 percentiles = 2600 randomized
#: comparisons per equality pin, far above the brief's ≥20 floor.
RANDOM_TRIALS = 200
RANDOM_SEED = 198

CORPUS: list[tuple[str, list[float]]] = _named_fixtures() + _randomized_fixtures(
    RANDOM_TRIALS, RANDOM_SEED
)


def _disagreements(
    candidate: Callable[[Sequence[float], float], float],
    corpus: Sequence[tuple[str, list[float]]],
) -> list[str]:
    """Every (fixture, pct) where ``candidate`` differs from the retired oracle."""
    bad: list[str] = []
    for name, values in corpus:
        for pct in PCT_GRID:
            expected = _retired_ceil_rank_oracle(values, pct)
            actual = candidate(list(values), pct)
            if actual != expected:
                bad.append(f"{name} pct={pct}: got {actual!r}, oracle {expected!r}")
    return bad


# --------------------------------------------------------------------------- #
# The corpus must actually contain the axes it claims
# --------------------------------------------------------------------------- #
class TestTheCorpusCoversItsClaimedAxes:
    """A fixture set that does not contain the axis it names is decoration."""

    def test_every_named_axis_is_present(self) -> None:
        names = {name for name, _ in _named_fixtures()}
        for required in (
            "single-element",
            "two-elements",
            "all-equal-values",
            "duplicate-values",
            "unsorted",
            "exact-rank-boundaries-n40",
        ):
            assert required in names, f"corpus lost its {required!r} axis"

    def test_boundary_percentiles_are_in_the_grid(self) -> None:
        assert 0 in PCT_GRID, "pct=0 is a boundary the conventions disagree on"
        assert 100 in PCT_GRID, "pct=100 is a boundary the conventions disagree on"

    def test_live_call_site_percentiles_are_covered(self) -> None:
        missing = [pct for pct in LIVE_PCTS if pct not in PCT_GRID]
        assert not missing, f"grid does not cover live call-site percentiles {missing}"

    def test_corpus_contains_a_tie_heavy_and_a_single_element_case(self) -> None:
        sizes = {len(values) for _, values in CORPUS}
        assert 1 in sizes, "no single-element fixture — the n=1 clamp is untested"
        assert max(sizes) >= 40, "no large fixture — exact-rank boundaries untested"


# --------------------------------------------------------------------------- #
# The equality proof
# --------------------------------------------------------------------------- #
class TestSharedSeamEqualsTheRetiredHandRoll:
    """The migration's safety net: numpy == the implementation it replaced."""

    def test_shared_seam_matches_oracle_over_the_whole_corpus(self) -> None:
        bad = _disagreements(stats.nearest_rank_percentile, CORPUS)
        assert not bad, "shared seam diverged from the retired hand-roll:\n" + "\n".join(
            bad[:20]
        )

    def test_the_corpus_is_actually_large(self) -> None:
        comparisons = len(CORPUS) * len(PCT_GRID)
        assert comparisons >= 20, "the brief's floor is 20 randomized trials"
        assert len(CORPUS) >= RANDOM_TRIALS

    def test_token_survey_percentile_matches_the_oracle(self) -> None:
        bad = _disagreements(ts.percentile, CORPUS)
        assert not bad, "token_survey.percentile diverged:\n" + "\n".join(bad[:20])

    def test_survey_txn_summarise_matches_the_oracle(self) -> None:
        """``survey_txn_contention_102`` has no percentile function of its own
        any more — its call sites go straight to the shared seam — so the pin
        drives the real ``summarise`` seam that publishes the #102 receipts."""
        for name, values in CORPUS:
            results = [
                txn.MintResult(attempts=int(abs(v)) + 1, elapsed_seconds=v, exhausted=False)
                for v in values
            ]
            summary = txn.summarise(results)
            attempts = [float(r.attempts) for r in results]
            latencies = [r.elapsed_seconds for r in results]
            for pct in txn.PERCENTILES:
                assert summary[f"attempts_p{pct}"] == _retired_ceil_rank_oracle(
                    attempts, pct
                ), f"{name}: attempts_p{pct} moved"
                assert summary[f"latency_p{pct}_s"] == round(
                    _retired_ceil_rank_oracle(latencies, pct), 4
                ), f"{name}: latency_p{pct}_s moved"

    def test_result_is_a_plain_float_not_a_numpy_scalar(self) -> None:
        # A numpy scalar compares equal to a float but serialises differently,
        # and these values are written into JSON receipts.
        for fn in (stats.nearest_rank_percentile, ts.percentile):
            got = fn([1.0, 2.0, 3.0], 50)
            assert type(got) is float, f"{fn} returned {type(got)}, not float"
        summary = txn.summarise(
            [txn.MintResult(attempts=1, elapsed_seconds=0.5, exhausted=False)]
        )
        assert type(summary["attempts_p50"]) is float
        assert type(summary["latency_p50_s"]) is float

    def test_returned_value_was_actually_observed(self) -> None:
        """Nearest-rank never synthesises a value between two samples."""
        for name, values in CORPUS:
            for pct in PCT_GRID:
                got = stats.nearest_rank_percentile(list(values), pct)
                assert got in values, f"{name} pct={pct}: {got} is not an observed value"


# --------------------------------------------------------------------------- #
# The control leg — if the harness cannot fail, it cannot pass
# --------------------------------------------------------------------------- #
class TestTheHarnessCanFail:
    """Plausible-but-wrong mappings must be REJECTED by the same corpus."""

    def test_control_interpolating_linear_method_diverges(self) -> None:
        def wrong_linear(values: Sequence[float], pct: float) -> float:
            return float(np.quantile(values, pct / 100.0, method="linear"))

        bad = _disagreements(wrong_linear, CORPUS)
        assert bad, (
            "CONTROL FAILED: the interpolating method='linear' passed the corpus, "
            "so the corpus cannot tell the two conventions apart and every "
            "'equal' result above is vacuous."
        )

    def test_control_dropped_unit_conversion_diverges(self) -> None:
        def wrong_units(values: Sequence[float], pct: float) -> float:
            # Passes a 0-100 percent straight in as a 0-1 fraction.
            clamped = min(pct, 1.0)
            return float(np.quantile(values, clamped, method="inverted_cdf"))

        bad = _disagreements(wrong_units, CORPUS)
        assert bad, "CONTROL FAILED: dropping the percent→fraction conversion passed"

    def test_control_higher_method_diverges(self) -> None:
        def wrong_higher(values: Sequence[float], pct: float) -> float:
            return float(np.quantile(values, pct / 100.0, method="higher"))

        bad = _disagreements(wrong_higher, CORPUS)
        assert bad, "CONTROL FAILED: method='higher' passed the corpus"

    def test_controls_fail_loudly_not_marginally(self) -> None:
        """Record HOW MANY comparisons each control breaks.

        A control that diverges on one fixture out of 2782 is a weak control —
        it would pass a corpus that had merely got lucky.  These counts are the
        receipt that the corpus discriminates broadly.
        """

        def wrong_linear(values: Sequence[float], pct: float) -> float:
            return float(np.quantile(values, pct / 100.0, method="linear"))

        def wrong_higher(values: Sequence[float], pct: float) -> float:
            return float(np.quantile(values, pct / 100.0, method="higher"))

        linear_failures = len(_disagreements(wrong_linear, CORPUS))
        higher_failures = len(_disagreements(wrong_higher, CORPUS))
        assert linear_failures > 100, f"linear control too weak: {linear_failures}"
        assert higher_failures > 10, f"higher control too weak: {higher_failures}"


# --------------------------------------------------------------------------- #
# Contract preserved from the retired implementations
# --------------------------------------------------------------------------- #
class TestEmptyInputContract:
    """numpy raises IndexError on an empty sample; both hand-rolls raised
    ValueError.  The seam preserves ValueError — an IndexError escaping a survey
    would read as a coding bug rather than "you asked for a percentile of
    nothing"."""

    def test_shared_seam_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="zero observations"):
            stats.nearest_rank_percentile([], 50)

    def test_token_survey_percentile_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            ts.percentile([], 50)

    def test_survey_txn_summarise_still_rejects_an_empty_run(self) -> None:
        """``summarise`` reached ``max(attempts)`` before any percentile, so an
        empty run already raised ValueError; routing to the shared seam must not
        turn that into an IndexError from numpy."""
        with pytest.raises(ValueError):
            txn.summarise([])

    def test_raw_numpy_would_have_raised_index_error(self) -> None:
        """The behaviour the guard exists to convert — pinned so that if a
        future numpy starts raising ValueError itself, we find out."""
        with pytest.raises(IndexError):
            np.quantile([], 0.5, method="inverted_cdf")




# --------------------------------------------------------------------------- #
# The WEIGHTED site — ported under RULING 1 (lead-11ia, 2026-07-26)
# --------------------------------------------------------------------------- #
# The former ``TestKnownWeightedDivergence`` class lived here and asserted that
# ``token_survey.weighted_percentile`` did NOT agree with numpy.  That bound was
# CLOSED DELIBERATELY by ruling, so — exactly as that pin's own message
# instructed — it has been deleted rather than edited into agreement.  What
# replaces it is the pair of things the ruling actually rests on: an equality
# proof over the ADMISSIBLE domain, and pins on the guard that defines it.
class TestWeightedSeamEqualsTheRetiredHandRoll:
    """Equality over the admissible domain — weights strictly positive.

    This is the pin that LICENSES the port.  The retired cumulative-weight
    hand-roll and ``np.quantile(..., weights=)`` disagree on zero weights (see
    :class:`TestTheWeightGuard`); with every weight > 0 they are the same
    function, so rejecting non-positive weights makes the swap sound rather
    than merely convenient.
    """

    def test_matches_the_retired_oracle_over_a_positive_weight_corpus(self) -> None:
        rng = random.Random(1198)
        compared = 0
        for _ in range(120):
            n = rng.randint(1, 20)
            pairs = [
                (float(rng.randint(0, 12)), float(rng.randint(1, 6))) for _ in range(n)
            ]
            for pct in PCT_GRID:
                expected = _retired_cumulative_weight_oracle(pairs, pct)
                actual = stats.weighted_nearest_rank_percentile(
                    [v for v, _ in pairs], [w for _, w in pairs], pct
                )
                assert actual == expected, f"pct={pct} diverged on {pairs}"
                compared += 1
        assert compared >= 20, "the brief's floor is 20 randomized trials"

    def test_token_survey_weighted_percentile_matches_the_oracle(self) -> None:
        """Drives the real ported call site, not just the seam."""
        rng = random.Random(51198)
        for _ in range(60):
            n = rng.randint(1, 15)
            pairs = [
                (rng.uniform(0.5, 4.0), float(rng.randint(1, 900))) for _ in range(n)
            ]
            for pct in PCT_GRID:
                assert ts.weighted_percentile(pairs, pct) == (
                    _retired_cumulative_weight_oracle(pairs, pct)
                ), f"token_survey.weighted_percentile diverged at pct={pct}"

    def test_summarize_token_weighted_percentiles_match_the_oracle(self) -> None:
        """End-to-end through the seam that publishes the ratio receipts."""
        rng = random.Random(77198)
        measurements = [
            ts.FileMeasurement(
                project="p",
                path=f"f{i}.py",
                ext=".py",
                bytes=10,
                voyage=rng.randint(1, 5000),
                claude=rng.randint(1, 9000),
            )
            for i in range(40)
        ]
        summary = ts.summarize(measurements)
        pairs = [(m.ratio, float(m.voyage)) for m in measurements]
        assert summary.token_weighted_p5 == _retired_cumulative_weight_oracle(
            pairs, ts.PCT_P5
        )
        assert summary.token_weighted_p95 == _retired_cumulative_weight_oracle(
            pairs, ts.PCT_P95
        )

    def test_control_dropping_the_weights_diverges(self) -> None:
        """The weighted path needs its own control: if weights were ignored, an
        unweighted quantile would still return a plausible observed value."""
        pairs = [(1.0, 90.0), (2.0, 1.0), (3.0, 1.0), (4.0, 1.0), (5.0, 1.0)]
        weighted = ts.weighted_percentile(pairs, 50)
        unweighted = stats.nearest_rank_percentile([v for v, _ in pairs], 50)
        assert weighted == 1.0, "90% of the mass sits at 1.0"
        assert unweighted == 3.0, "ignoring weights would report the middle value"
        assert weighted != unweighted, (
            "CONTROL FAILED: this fixture cannot tell a weighted implementation "
            "from one that silently drops the weights."
        )


class TestTheWeightGuard:
    """``weights > 0`` was a docstring PROMISE for the life of the hand-roll and
    was never CHECKED.  Finding #198 turned it into a check (RULING 1).

    The guard is not tidiness: it is the thing that makes the numpy swap sound,
    because the two implementations disagree exactly where the promise was
    broken.  :meth:`test_the_guard_is_load_bearing` records that divergence, so
    a future reader deleting the guard can see what it was holding.
    """

    def test_a_zero_weight_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="every weight must be > 0"):
            ts.weighted_percentile([(1.0, 0.0), (2.0, 1.0)], 0)

    def test_a_negative_weight_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="every weight must be > 0"):
            ts.weighted_percentile([(1.0, -1.0), (2.0, 1.0)], 50)

    def test_all_zero_weights_are_rejected(self) -> None:
        with pytest.raises(ValueError, match="every weight must be > 0"):
            ts.weighted_percentile([(1.0, 0.0), (2.0, 0.0)], 50)

    def test_mismatched_lengths_are_rejected(self) -> None:
        with pytest.raises(ValueError, match="one weight"):
            stats.weighted_nearest_rank_percentile([1.0, 2.0], [1.0], 50)

    def test_empty_is_still_a_value_error(self) -> None:
        with pytest.raises(ValueError):
            ts.weighted_percentile([], 50)

    def test_the_guard_is_load_bearing(self) -> None:
        """WITHOUT the guard the two implementations genuinely disagree.

        Kept as the receipt for why the guard exists: the retired hand-roll
        returns the zero-weight value at pct=0, numpy skips it.  If someone
        deletes the guard, this is the behaviour they are re-admitting.
        """
        pairs = [(1.0, 0.0), (2.0, 1.0), (3.0, 1.0)]
        assert _retired_cumulative_weight_oracle(pairs, 0) == 1.0
        numpy_result = float(
            np.quantile(
                [v for v, _ in pairs],
                0.0,
                method="inverted_cdf",
                weights=[w for _, w in pairs],
            )
        )
        assert numpy_result == 2.0
        assert _retired_cumulative_weight_oracle(pairs, 0) != numpy_result


# --------------------------------------------------------------------------- #
# The deploy smoke — routed to the seam, and its UNIT is the hazard
# --------------------------------------------------------------------------- #
class TestSmokeP8bPercentileUnits:
    """**PINNED KNOWN BOUND (#198): `smoke_p8b.percentile` is a DELIBERATE 4th copy
    of the nearest-rank policy, and THIS CLASS IS THE ONLY THING STOPPING IT DRIFTING.**

    The other three copies were deleted in favour of :mod:`loremaster.stats`.
    This one stays hand-rolled, because ``smoke_p8b.py`` is the DEPLOY SMOKE —
    the instrument that caught both #107 and #131, each time after the fact and
    each time because it was the only thing looking.  A detector that can fail to
    *start* is strictly worse than a detector carrying a duplicated three-line
    percentile, so it acquires **no new imports at all**.

    So the duplication is bought deliberately, and this is the price: the copy may
    exist, but it **may not drift**.

    ⚠ **THE RE-OPEN TRIGGER HAS FIRED — recorded here 2026-07-29, finding #282.**
    This docstring used to argue that ``docs/eval/`` was *"outside ``testpaths``
    (finding #238), so no gate watches its imports"*, and named its own trigger:
    *"the day ``docs/eval/`` gains a ``testpaths`` entry, the trade changes — the
    smoke's own suite would then be gated, an import break would be caught, and
    consolidating could be reconsidered."*  **That day was 2026-07-26** (#238),
    and packet 44 then added the type gate as well, so ``docs/eval`` is now
    covered on BOTH axes.  The premise the trade rested on is gone, and for three
    days the class went on teaching a retired fact — which is the whole of #282.

    **What is discharged and what is NOT.** Discharged: the stale premise, above.
    **NOT discharged: whether to consolidate.** The trigger says the trade "could
    be reconsidered", not that it must be resolved one way — and the surviving
    half of the original argument is untouched by gating: the smoke is a
    detachable instrument pointed at a deployed image, and *any* new import is a
    new way for it to fail to start.  Choosing between "consolidate now that
    imports are watched" and "keep the copy, the import-count argument stands"
    is a DESIGN decision about a settled trade, and it belongs to the operator,
    not to the agent that noticed the trigger.  **It is surfaced, not settled.**

    Until it IS settled, the standing instruction is unchanged: do not
    "helpfully" port this.  These pins stay, and they are load-bearing either
    way — under consolidation they become the equality oracle for the port.

    Two UNITS meet here: this takes a ``[0, 1]`` FRACTION while every other caller
    takes a ``[0, 100]`` PERCENT, which is how a ``/100`` goes missing.  Measured
    on this corpus, treating the fraction as a percent gets **1856 of 2782**
    comparisons wrong — loud, but loud in a deploy gate's latency numbers, which
    is the worst place to find out.  Hence the explicit unit pins below.
    """

    def test_does_not_drift_from_the_shared_seam(self) -> None:
        """THE load-bearing pin: the 4th copy must agree with the shared seam.

        This is what makes keeping the duplication safe, so it stands in for the
        port that was NOT taken.  It compares against the SEAM (not merely the
        oracle), so a change to either side that separates them goes RED.
        """
        bad: list[str] = []
        for name, values in CORPUS:
            for pct in PCT_GRID:
                fraction = pct / 100.0
                mine = smoke.percentile(values, fraction)
                seam = stats.nearest_rank_quantile(values, fraction)
                if mine != seam:
                    bad.append(f"{name} fraction={fraction}: smoke {mine} != seam {seam}")
        assert not bad, (
            "smoke_p8b.percentile has DRIFTED from loremaster.stats (#198). The copy "
            "is allowed to exist only because this pin holds it equal:\n"
            + "\n".join(bad[:20])
        )

    def test_a_fraction_means_what_a_percent_would(self) -> None:
        values = [float(i) for i in range(1, 21)]
        # NOTE the non-exact ranks (0.07/0.33/0.66 -> 1.4/6.6/13.2 on n=20).
        # The boundary-and-quarter fractions all land on WHOLE ranks, where
        # ceil and floor agree — a fixture of only those cannot tell a
        # nearest-rank build from a rank-rule drift, which is the arithmetic
        # ALIGNMENT trap this repo has been bitten by before.
        cases = (
            (0.0, 0),
            (0.07, 7),
            (0.25, 25),
            (0.33, 33),
            (0.5, 50),
            (0.66, 66),
            (0.9, 90),
            (1.0, 100),
        )
        for fraction, pct in cases:
            assert smoke.percentile(values, fraction) == _retired_ceil_rank_oracle(
                values, pct
            ), f"fraction {fraction} should mean the {pct}th percentile"

    def test_matches_the_retired_oracle_across_the_corpus(self) -> None:
        bad: list[str] = []
        for name, values in CORPUS:
            for pct in PCT_GRID:
                got = smoke.percentile(values, pct / 100.0)
                expected = _retired_ceil_rank_oracle(values, pct)
                if got != expected:
                    bad.append(f"{name} fraction={pct / 100.0}: {got} != {expected}")
        assert not bad, "smoke_p8b.percentile diverged:\n" + "\n".join(bad[:20])

    def test_control_treating_the_fraction_as_a_percent_diverges(self) -> None:
        """If the port had wrongly divided by 100 again, or not at all."""
        values = [float(i) for i in range(1, 101)]
        assert smoke.percentile(values, 0.9) == 90.0
        # A build that passed 0.9 where 90 was meant would answer 1.0.
        assert smoke.percentile(values, 0.009) == 1.0
        assert smoke.percentile(values, 0.9) != smoke.percentile(values, 0.009)

    def test_the_two_unit_faces_agree(self) -> None:
        values = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0]
        for pct in PCT_GRID:
            assert stats.nearest_rank_percentile(
                values, pct
            ) == stats.nearest_rank_quantile(values, pct / 100.0)

    def test_empty_still_raises_SmokeCheckFailed_not_value_error(self) -> None:
        """The deploy harness reports SmokeCheckFailed; the shared seam raises
        ValueError. The local guard must keep winning."""
        with pytest.raises(smoke.SmokeCheckFailed, match="EMPTY sample"):
            smoke.percentile([], 0.5)

    def test_the_returned_latency_was_actually_measured(self) -> None:
        samples = [12.0, 5.0, 99.0, 3.0, 41.0]
        for fraction in (0.0, 0.25, 0.5, 0.75, 0.9, 1.0):
            assert smoke.percentile(samples, fraction) in samples
