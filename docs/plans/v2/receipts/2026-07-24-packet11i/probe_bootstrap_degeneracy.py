#!/usr/bin/env python3
"""Packet 11-i / S1 — is the nonparametric bootstrap over ``choose_cosine_floor``
degenerate in the measured 2026-07-07 regime?

Why this exists
---------------
``docs/design/2026-07-24-floor-calibration.md`` Addendum D makes a nonparametric
bootstrap confidence interval **over the floor-selection procedure** its central
innovation: one disjoint-CI test governs adoption (D3), per-tier upgrade (D6) and
staleness (D3). ``REPORT-design-blind-11i.md`` §6/S1 objects that the chosen floor
is a **tail order statistic** — the 2026-07-07 adoption recorded false-fire 1/56,
so the adopted floor is ~the 2nd-smallest admissible order statistic of the union
and its numeric value IS one real sample's own cosine — and the nonparametric
bootstrap is not consistent for extreme order statistics. If that bites, the
resampled floor distribution is lumpy or degenerate (``ci_low == ci_high``), and
BOTH pre-registered rules fail silently:

* D2's ``>= 98%`` decision-agreement stability gate passes trivially at
  ``ci_low == ci_high`` — so the N-curve adopts the SMALLEST N tried;
* D3's disjoint-CI adoption fires on ANY movement — "hysteresis falls out free"
  inverts into maximal flapping.

This script answers that as a MEASUREMENT, not an argument. It never touches a
store, an embedder, or the network: it synthesises ``VerdictSample`` corpora in
the recorded regime and drives the REAL ``choose_cosine_floor`` (imported, never
re-implemented — the same discipline S4b audit finding #1 imposed on the survey
itself).

Provenance of the synthesised regime
------------------------------------
RECORDED (reproduced exactly at N=56 by rejection sampling):

* ``n_union = 56`` — ``docs/design/2026-07-24-floor-calibration.md`` §1.5 (35
  eval-XML prose + 15 corpus-sampled identifiers + 6 implementation-vocabulary
  probes) and ``loremaster/loremaster/search.py``'s ``_COSINE_WEAK_MATCH_FLOOR``
  stamp comment ("1/56 on the union of prose-real + identifier-real +
  implementation-vocabulary-real").
* ``n_nonsense = 15`` — same §1.5; ``search_score_survey.NONSENSE_QUERIES`` is a
  fixed 15-tuple.
* false-fire ``1/56`` and catch ``15/15`` at the adopted floor — the stamp comment.
* catch ``15/15`` FORCES zero verbatim anchors on the absent arm: an anchored
  sample can never fire, so a single anchored nonsense query would cap catch at
  14/15. Hence ``absent_anchor_fraction = 0.0`` in the recorded regime (and a
  sensitivity row that violates it, so the choice is not a monoculture).
* the adopted floor is a union sample's OWN cosine, and the next admissible
  candidate up (0.5370) carried 2/56 false-fire at the identical 100% catch —
  the stamp comment's dominance-ordering ruling. So exactly ONE non-anchored
  union sample sits strictly below the adopted floor.
* the bars: ``D2_MAX_FALSE_FIRE_RATE = 0.05``, ``D2_MIN_NONSENSE_CATCH_RATE =
  0.6`` (imported from the survey, never re-typed).
* ``B >= 1000``, central 90% interval ``[p5, p95]``, the ``>= 98%``
  decision-agreement gate — Addendum D1/D2/D8.

DECLARED (the record does not fix these — the survey's raw per-query jsonl lived
at ``scratchpad/survey_out_74w/`` and is gone, blind review §6/S5) and therefore
VARIED in §6: the union/absent cosine distribution shapes, locations and spreads,
the verbatim-anchor fraction on each arm, whether anchors correlate with cosine,
and whether the absent arm scales with N (leg A: fixed at 15, what the LEGACY
instrument does — ``NONSENSE_QUERIES`` is a fixed tuple; leg B: scales with the
pool, what D2's portable hold-out runner implies).

Usage
-----
    uv run python docs/plans/v2/receipts/2026-07-24-packet11i/probe_bootstrap_degeneracy.py

Deterministic: every draw comes from a seeded ``random.Random`` and every
parallel work unit carries its own seed, so re-running reproduces every number in
``probe-bootstrap-output.txt``.
"""

from __future__ import annotations

import math
import multiprocessing
import os
import random
import statistics
import sys
import time
from collections import Counter
from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from search_score_survey import (  # noqa: E402  (path bootstrap must precede)
    D2_MAX_FALSE_FIRE_RATE,
    D2_MIN_NONSENSE_CATCH_RATE,
    CosineFloorRecommendation,
    VerdictSample,
    choose_cosine_floor,
    cosine_absence_verdict_fires,
)
from token_survey import percentile  # noqa: E402

# --------------------------------------------------------------------------- #
# Pre-registered constants, cited not invented (Addendum D1/D2/D8).
# --------------------------------------------------------------------------- #

#: Addendum D1/D8: bootstrap replicate count, pre-registered as ``B >= 1000``.
BOOTSTRAP_REPLICATES: int = 1000

#: Addendum D8: "central 90% interval" — the blind review reads this as
#: ``[p5, p95]`` (§6), and that is what the repo's own nearest-rank
#: ``token_survey.percentile`` computes (REUSED, not re-implemented).
CI_LOW_PERCENTILE: float = 5.0
CI_HIGH_PERCENTILE: float = 95.0

#: Addendum D2: the pre-registered stability gate — verdict decisions computed at
#: ``ci_low`` vs ``ci_high`` must agree on at least this fraction of the union.
STABILITY_GATE_AGREEMENT: float = 0.98

#: Recorded regime (design doc §1.5 / the ``_COSINE_WEAK_MATCH_FLOOR_STAMP``
#: comment block in ``loremaster/loremaster/search.py``).
RECORDED_UNION_N: int = 56
RECORDED_NONSENSE_N: int = 15
RECORDED_FALSE_FIRE_COUNT: int = 1
RECORDED_CATCH_RATE: float = 1.0

#: Independent-measurement pairs drawn for the flapping rate (§4). Not a
#: pre-registered value — a sample size chosen so a rate near 0 or near 1 is
#: resolved to roughly +/- 3.5 percentage points at 95% confidence.
FLAPPING_PAIRS: int = 200

#: Replicates used for the single-threaded cost timing leg (§5). Small on
#: purpose: the cost table reports per-bootstrap milliseconds extrapolated to
#: ``BOOTSTRAP_REPLICATES``; re-running the whole ladder at B=1000 purely to time
#: it would double wall clock for no extra information.
TIMING_REPLICATES: int = 40

#: The N ladder. 56 is the recorded pool size; each rung doubles, so an order
#: statistic at a FIXED RATE (~1.8% of the union) gets ~1, 2, 4, 8, 16, 32
#: samples below it — the range over which "does degeneracy resolve?" is
#: decidable at a cost this box can pay.
N_LADDER: tuple[int, ...] = (56, 112, 224, 448, 896, 1792, 3584)

#: N values at which the flapping rate (§4) is measured.
FLAPPING_LADDER: tuple[int, ...] = (56, 224, 896)

#: N values at which the DETECTION POWER of the disjoint-CI test (§7) is
#: measured — the dual of flapping, and the question that decides whether the
#: mechanism works at all rather than merely fails quietly.
POWER_LADDER: tuple[int, ...] = (56, 224)

#: True-floor movements (in cosine units) whose detection rate §7 measures.
#: 0.000 IS the flapping null. The upper end is deliberately larger than any
#: plausible real drift, so a test that cannot detect even THAT is convicted
#: without argument. For scale: the whole retired floor is 0.50649.
POWER_SHIFTS: tuple[float, ...] = (0.000, 0.010, 0.020, 0.050, 0.100, 0.200)


# --------------------------------------------------------------------------- #
# Synthesis.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RegimeParameters:
    """The generative parameters of one synthetic (union, absent) corpus.

    Every field is either RECORDED (see the module docstring) or DECLARED — the
    ``provenance`` string says which, and §6 varies every DECLARED one so no
    verdict rests on a single unrecorded choice.
    """

    label: str
    union_mean: float
    union_stdev: float
    absent_mean: float
    absent_stdev: float
    anchor_fraction: float
    #: ``"gaussian"`` or ``"uniform"`` — the SHAPE of the cosine distribution.
    #: A DECLARED choice; §6 runs both, because "the tail is thin because I drew
    #: Gaussians" is exactly the artifact a sensitivity leg has to rule out. A
    #: uniform of the same mean/stdev spans ``mean +/- sqrt(3)*stdev``.
    distribution: str = "gaussian"
    #: RECORDED as 0.0 by catch 15/15 (an anchored sample cannot fire, so any
    #: anchored nonsense query caps catch below 100%). Varied in §6 anyway.
    absent_anchor_fraction: float = 0.0
    #: ``"random"`` — anchors independent of cosine; ``"high_cosine"`` — anchors
    #: land on the highest-cosine samples (the "an identifier lookup that found
    #: its own definition" reading of D3's carve-out).
    anchor_mode: str = "random"
    max_false_fire_rate: float = D2_MAX_FALSE_FIRE_RATE
    provenance: str = ""


@dataclass(frozen=True)
class SyntheticCorpus:
    """One drawn corpus plus the receipts that prove which regime it is in."""

    union: tuple[VerdictSample, ...]
    absent: tuple[VerdictSample, ...]
    recommendation: CosineFloorRecommendation
    draws_attempted: int

    @property
    def false_fire_count(self) -> int:
        """The number of union samples the adopted floor false-fires on."""
        return round(self.recommendation.false_fire_rate * len(self.union))

    @property
    def distinct_union_cosines(self) -> int:
        """How many DISTINCT cosine values the union carries.

        Load-bearing for the differently-broken control: a degenerate bootstrap
        because the corpus is CONSTANT (this is 1 — there is only one candidate
        floor in existence) is a different failure from a degenerate bootstrap
        because the statistic is a TAIL ORDER STATISTIC (this is ~N — the
        candidates exist and the selection rule still collapses onto one).
        """
        return len({s.max_cosine for s in self.union})

    @property
    def floor_rank_in_union(self) -> int:
        """1-based rank of the adopted floor among the sorted union cosines.

        The whole S1 objection is that this rank is ~2 out of N. Reporting it
        makes "is this a tail order statistic?" a measured number, not a claim.
        """
        ordered = sorted(s.max_cosine for s in self.union)
        return ordered.index(self.recommendation.floor) + 1


class CorpusGenerator:
    """Draws ``VerdictSample`` corpora from a :class:`RegimeParameters` regime.

    Cosines come from a clipped Gaussian — the simplest shape carrying a location
    and a spread, and one whose lower tail is exactly what the question is about.
    The shape is a DECLARED choice (§6 varies both locations and both spreads);
    what is RECORDED and enforced here is the *regime*: how much of the union
    sits below the adopted floor, and the catch rate.
    """

    _COSINE_MIN: float = 0.001
    _COSINE_MAX: float = 0.999

    def __init__(self, parameters: RegimeParameters) -> None:
        self.parameters = parameters

    def _draw_cosines(
        self, count: int, mean: float, stdev: float, rng: random.Random
    ) -> list[float]:
        if self.parameters.distribution == "uniform":
            half_width = math.sqrt(3.0) * stdev
            draw = lambda: rng.uniform(mean - half_width, mean + half_width)  # noqa: E731
        else:
            draw = lambda: rng.gauss(mean, stdev)  # noqa: E731
        return [min(self._COSINE_MAX, max(self._COSINE_MIN, draw())) for _ in range(count)]

    def _attach_anchors(
        self, cosines: Sequence[float], fraction: float, rng: random.Random
    ) -> list[VerdictSample]:
        if self.parameters.anchor_mode == "high_cosine":
            anchor_count = round(fraction * len(cosines))
            ranked = sorted(range(len(cosines)), key=lambda index: cosines[index])
            anchored = set(ranked[len(cosines) - anchor_count :]) if anchor_count else set()
            return [
                VerdictSample(max_cosine=cosine, has_verbatim_anchor=(index in anchored))
                for index, cosine in enumerate(cosines)
            ]
        return [
            VerdictSample(max_cosine=cosine, has_verbatim_anchor=(rng.random() < fraction))
            for cosine in cosines
        ]

    def draw(
        self,
        union_size: int,
        absent_size: int,
        rng: random.Random,
        *,
        accept: Callable[[SyntheticCorpus], bool] | None = None,
        max_attempts: int = 50_000,
    ) -> SyntheticCorpus:
        """Draw one corpus, optionally rejecting until it lands in the regime.

        Args:
            union_size: Number of answered/union samples.
            absent_size: Number of nonsense/absent samples.
            rng: The seeded source of randomness (determinism receipt).
            accept: Optional regime predicate. Rejection sampling is how a
                RECORDED regime (false-fire exactly 1/56, catch 15/15) is
                reproduced rather than approximated.
            max_attempts: Guard against an unsatisfiable predicate.

        Returns:
            The accepted corpus, carrying its own ``draws_attempted`` receipt.

        Raises:
            RuntimeError: The predicate was never satisfied — a synthesis bug, to
                be reported, never papered over.
        """
        for attempt in range(1, max_attempts + 1):
            union = self._attach_anchors(
                self._draw_cosines(
                    union_size, self.parameters.union_mean, self.parameters.union_stdev, rng
                ),
                self.parameters.anchor_fraction,
                rng,
            )
            absent = self._attach_anchors(
                self._draw_cosines(
                    absent_size, self.parameters.absent_mean, self.parameters.absent_stdev, rng
                ),
                self.parameters.absent_anchor_fraction,
                rng,
            )
            recommendation = choose_cosine_floor(
                union, absent, max_false_fire_rate=self.parameters.max_false_fire_rate
            )
            corpus = SyntheticCorpus(
                union=tuple(union),
                absent=tuple(absent),
                recommendation=recommendation,
                draws_attempted=attempt,
            )
            if accept is None or accept(corpus):
                return corpus
        raise RuntimeError(
            f"regime predicate unsatisfied after {max_attempts} draws "
            f"(regime={self.parameters.label!r}, union_size={union_size})"
        )


def recorded_regime_predicate(corpus: SyntheticCorpus) -> bool:
    """The RECORDED 2026-07-07 regime, exactly: false-fire 1/56, catch 15/15."""
    return (
        corpus.false_fire_count == RECORDED_FALSE_FIRE_COUNT
        and corpus.recommendation.nonsense_catch_rate == RECORDED_CATCH_RATE
    )


def scaled_regime_predicate(corpus: SyntheticCorpus) -> bool:
    """The recorded regime's SHAPE, generalised past N=56: 100% catch and a
    non-empty slice of the union below the adopted floor. Holds the shape (a
    floor pinned just above the absent arm's maximum) while the count below it
    scales with N — which is what "the same regime at larger N" means."""
    return (
        corpus.recommendation.nonsense_catch_rate == RECORDED_CATCH_RATE
        and corpus.false_fire_count >= 1
    )


def usable_regime_predicate(corpus: SyntheticCorpus) -> bool:
    """A corpus a real adoption would ACCEPT: the catch bar is met and at least
    one union sample sits below the floor. Used for the §6 sensitivity regimes,
    several of which cannot reach 100% catch by construction — demanding the
    recorded catch there would silently exclude exactly the variations the
    sensitivity leg exists to test."""
    return (
        corpus.recommendation.meets_adoption_bar(min_catch=D2_MIN_NONSENSE_CATCH_RATE)
        and corpus.false_fire_count >= 1
    )


# --------------------------------------------------------------------------- #
# The bootstrap.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class BootstrapResult:
    """The resampled distribution of one statistic, plus its degeneracy receipts."""

    label: str
    point_estimate: float
    ci_low: float
    ci_high: float
    #: How many DISTINCT values the resampled statistic took across B replicates.
    distinct_values: int
    #: The most common resampled value and the fraction of replicates on it.
    modal_value: float
    modal_mass: float
    histogram: tuple[tuple[float, int], ...]
    stdev: float
    minimum: float
    maximum: float
    #: Fraction of replicates that reproduced the ORIGINAL point estimate exactly.
    #: A tail order statistic that is genuinely pinned to one sample shows a mass
    #: near 1.0 here; a lumpy-but-moving one shows a mass well below it.
    point_mass: float

    @property
    def is_degenerate(self) -> bool:
        """True iff the pre-registered central-90% interval is a single point."""
        return self.ci_low == self.ci_high

    @property
    def ci_width(self) -> float:
        return self.ci_high - self.ci_low


def summarise_bootstrap(
    label: str, point_estimate: float, values: Sequence[float]
) -> BootstrapResult:
    """Reduce B resampled statistic values to the pre-registered interval plus the
    degeneracy receipts (distinct count, modal mass, histogram, range)."""
    counter = Counter(values)
    modal_value, modal_count = counter.most_common(1)[0]
    return BootstrapResult(
        label=label,
        point_estimate=point_estimate,
        ci_low=percentile(list(values), CI_LOW_PERCENTILE),
        ci_high=percentile(list(values), CI_HIGH_PERCENTILE),
        distinct_values=len(counter),
        modal_value=modal_value,
        modal_mass=modal_count / len(values),
        histogram=tuple(counter.most_common(8)),
        stdev=statistics.pstdev(values) if len(values) > 1 else 0.0,
        minimum=min(values),
        maximum=max(values),
        point_mass=counter.get(point_estimate, 0) / len(values),
    )


class ProcedureBootstrap:
    """Resamples the union AND the absent arm JOINTLY (Addendum D1) and re-runs
    the REAL ``choose_cosine_floor`` per replicate — never a proxy statistic and
    never a re-implementation of the selection rule."""

    def __init__(self, corpus: SyntheticCorpus, *, max_false_fire_rate: float) -> None:
        self.corpus = corpus
        self.max_false_fire_rate = max_false_fire_rate

    def one_replicate(self, rng: random.Random) -> float:
        union = self.corpus.union
        absent = self.corpus.absent
        resampled_union = [union[rng.randrange(len(union))] for _ in range(len(union))]
        resampled_absent = [absent[rng.randrange(len(absent))] for _ in range(len(absent))]
        return choose_cosine_floor(
            resampled_union, resampled_absent, max_false_fire_rate=self.max_false_fire_rate
        ).floor

    def run(self, replicates: int, rng: random.Random, *, label: str) -> BootstrapResult:
        values = [self.one_replicate(rng) for _ in range(replicates)]
        return summarise_bootstrap(label, self.corpus.recommendation.floor, values)

    def time_replicates(self, replicates: int, rng: random.Random) -> float:
        """Single-threaded seconds per replicate — the honest cost unit."""
        start = time.perf_counter()
        for _ in range(replicates):
            self.one_replicate(rng)
        return (time.perf_counter() - start) / replicates


class MedianStatisticBootstrap:
    """POSITIVE CONTROL leg 1 — the same resampler and the same CI code over a
    statistic squarely in the BULK (the union's median cosine). If THIS comes
    back degenerate, the harness is broken and every other number here is void."""

    def __init__(self, corpus: SyntheticCorpus) -> None:
        self.corpus = corpus

    def run(self, replicates: int, rng: random.Random, *, label: str) -> BootstrapResult:
        union = self.corpus.union
        values = [
            statistics.median(
                [union[rng.randrange(len(union))].max_cosine for _ in range(len(union))]
            )
            for _ in range(replicates)
        ]
        point = statistics.median([sample.max_cosine for sample in union])
        return summarise_bootstrap(label, point, values)


# --------------------------------------------------------------------------- #
# The two silent-failure measurements (Addendum D2 gate, Addendum D3 adoption).
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StabilityGateMeasurement:
    """D2's ``>= 98%`` decision-agreement gate, evaluated on a real interval."""

    agreement: float
    disagreeing_samples: int
    union_size: int
    passes: bool
    trivially: bool


def measure_stability_gate(
    union: Sequence[VerdictSample], ci_low: float, ci_high: float
) -> StabilityGateMeasurement:
    """Run D2's gate: how often does the verdict decision differ at ``ci_low`` vs
    ``ci_high``, over the union's own samples?

    ``trivially`` is the load-bearing field: when ``ci_low == ci_high`` the gate
    CANNOT disagree, so a pass carries no information about stability at all.
    """
    disagreements = sum(
        1
        for sample in union
        if cosine_absence_verdict_fires(sample.max_cosine, ci_low, sample.has_verbatim_anchor)
        != cosine_absence_verdict_fires(sample.max_cosine, ci_high, sample.has_verbatim_anchor)
    )
    agreement = 1.0 - disagreements / len(union)
    return StabilityGateMeasurement(
        agreement=agreement,
        disagreeing_samples=disagreements,
        union_size=len(union),
        passes=agreement >= STABILITY_GATE_AGREEMENT,
        trivially=ci_low == ci_high,
    )


def intervals_are_disjoint(first: BootstrapResult, second: BootstrapResult) -> bool:
    """D3's adoption test: adopt iff the fresh CI and the adopted CI are DISJOINT."""
    return first.ci_high < second.ci_low or second.ci_high < first.ci_low


@dataclass(frozen=True)
class PairMeasurement:
    """How often two independent measurements would trigger D3's disjoint-CI
    adoption. At ``shift == 0`` this is the FLAPPING rate (adoption when nothing
    real moved); at ``shift > 0`` it is the DETECTION POWER (adoption when the
    true floor genuinely moved by ``shift``). One instrument, both directions —
    a false-positive rate without a detection rate says nothing about whether a
    test works."""

    label: str
    shift: float
    pairs: int
    disjoint: int
    point_moved: int
    mean_absolute_point_difference: float

    @property
    def adoption_rate(self) -> float:
        return self.disjoint / self.pairs

    @property
    def point_movement_rate(self) -> float:
        return self.point_moved / self.pairs


@dataclass(frozen=True)
class PairJob:
    """One independent-pair work unit — picklable, fully seeded, so the parallel
    run reproduces the serial one exactly."""

    regime: RegimeParameters
    union_size: int
    absent_size: int
    accept_name: str
    seed_first: int
    seed_second: int
    replicates: int
    #: Cosine offset applied to BOTH arms of the SECOND corpus. Shifting both
    #: translates the whole regime, so false-fire and catch are preserved and the
    #: TRUE floor moves by exactly this much — which is what "the floor moved"
    #: means, and it keeps the same regime predicate satisfiable on both sides.
    shift: float = 0.0


_ACCEPT_PREDICATES: dict[str, Callable[[SyntheticCorpus], bool] | None] = {
    "recorded": recorded_regime_predicate,
    "scaled": scaled_regime_predicate,
    "usable": usable_regime_predicate,
    "none": None,
}


def run_pair_job(job: PairJob) -> tuple[bool, bool, float]:
    """Bootstrap two independently-drawn corpora and report ``(cis_disjoint,
    point_floor_moved, |point difference|)``. Module-level so it survives
    pickling into a worker process."""
    accept = _ACCEPT_PREDICATES[job.accept_name]
    first_generator = CorpusGenerator(job.regime)
    second_regime = replace(
        job.regime,
        union_mean=job.regime.union_mean + job.shift,
        absent_mean=job.regime.absent_mean + job.shift,
    )
    second_generator = CorpusGenerator(second_regime)
    rng_first = random.Random(job.seed_first)
    rng_second = random.Random(job.seed_second)
    first_corpus = first_generator.draw(job.union_size, job.absent_size, rng_first, accept=accept)
    second_corpus = second_generator.draw(job.union_size, job.absent_size, rng_second, accept=accept)
    first = ProcedureBootstrap(
        first_corpus, max_false_fire_rate=job.regime.max_false_fire_rate
    ).run(job.replicates, rng_first, label="a")
    second = ProcedureBootstrap(
        second_corpus, max_false_fire_rate=second_regime.max_false_fire_rate
    ).run(job.replicates, rng_second, label="b")
    return (
        intervals_are_disjoint(first, second),
        first.point_estimate != second.point_estimate,
        abs(first.point_estimate - second.point_estimate),
    )


def measure_pairs(
    regime: RegimeParameters,
    *,
    union_size: int,
    absent_size: int,
    accept_name: str,
    seed: int,
    replicates: int,
    pairs: int,
    label: str,
    executor: ProcessPoolExecutor | None,
    shift: float = 0.0,
) -> PairMeasurement:
    """Draw ``pairs`` INDEPENDENT pairs of corpora, the second from a regime
    translated by ``shift``, bootstrap each, and count how often D3's disjoint-CI
    test fires.

    ``shift == 0`` measures FLAPPING (adoption when nothing moved); ``shift > 0``
    measures DETECTION POWER (adoption when the true floor moved by exactly
    ``shift``). Both are needed: a test that never fires has a perfect
    false-positive rate and is useless."""
    jobs = [
        PairJob(
            regime=regime,
            union_size=union_size,
            absent_size=absent_size,
            accept_name=accept_name,
            seed_first=seed + 2 * index,
            seed_second=seed + 2 * index + 1,
            replicates=replicates,
            shift=shift,
        )
        for index in range(pairs)
    ]
    outcomes = (
        list(executor.map(run_pair_job, jobs, chunksize=1))
        if executor is not None
        else [run_pair_job(job) for job in jobs]
    )
    return PairMeasurement(
        label=label,
        shift=shift,
        pairs=pairs,
        disjoint=sum(1 for disjoint, _moved, _diff in outcomes if disjoint),
        point_moved=sum(1 for _disjoint, moved, _diff in outcomes if moved),
        mean_absolute_point_difference=statistics.fmean(
            [difference for _disjoint, _moved, difference in outcomes]
        ),
    )


# --------------------------------------------------------------------------- #
# Rendering + small numeric helpers (stdout is this script's only output).
# --------------------------------------------------------------------------- #
def heading(text: str) -> None:
    print()
    print("=" * 100)
    print(text)
    print("=" * 100)


def render_bootstrap(result: BootstrapResult, *, indent: str = "") -> None:
    verdict = "DEGENERATE" if result.is_degenerate else "non-degenerate"
    print(
        f"{indent}{result.label}: point={result.point_estimate:.6f}  "
        f"ci=[{result.ci_low:.6f}, {result.ci_high:.6f}]  width={result.ci_width:.6f}  "
        f"[{verdict}]"
    )
    print(
        f"{indent}  distinct resampled values={result.distinct_values}  "
        f"modal={result.modal_value:.6f} @ {result.modal_mass:.1%} of replicates  "
        f"point reproduced in {result.point_mass:.1%}  "
        f"sd={result.stdev:.6f}  range=[{result.minimum:.6f}, {result.maximum:.6f}]"
    )
    top = "  ".join(f"{value:.5f}x{count}" for value, count in result.histogram)
    print(f"{indent}  top resampled values: {top}")


def fit_log_log_exponent(sizes: Sequence[int], seconds: Sequence[float]) -> float:
    """Least-squares slope of log(seconds) vs log(size) — the empirical growth
    exponent. Pure Python: this repo has no numpy (re-verified by
    :func:`verify_numeric_stack_absence` in this same run)."""
    log_sizes = [math.log(size) for size in sizes]
    log_seconds = [math.log(second) for second in seconds]
    mean_x = statistics.fmean(log_sizes)
    mean_y = statistics.fmean(log_seconds)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(log_sizes, log_seconds))
    denominator = sum((x - mean_x) ** 2 for x in log_sizes)
    return numerator / denominator


def verify_numeric_stack_absence() -> list[str]:
    """Independently re-verify the blind review's "no numpy, no scipy anywhere in
    the dependency closure" claim, from inside the project venv. The IMPORT test
    is the one that catches a TRANSITIVE dependency a ``pyproject.toml`` grep
    cannot see; the lock-file test catches one pinned but not yet installed."""
    lines: list[str] = []
    for module_name in ("numpy", "scipy"):
        try:
            module = __import__(module_name)
        except ImportError as error:
            lines.append(f"    import {module_name:6s} -> ABSENT ({type(error).__name__}: {error})")
        else:
            lines.append(f"    import {module_name:6s} -> PRESENT at {module.__file__}")
    pyprojects = sorted(
        {*_REPO_ROOT.glob("pyproject.toml"), *_REPO_ROOT.glob("*/pyproject.toml")}
    )
    for pyproject in pyprojects:
        text = pyproject.read_text(encoding="utf-8")
        hits = [name for name in ("numpy", "scipy") if name in text]
        relative = pyproject.relative_to(_REPO_ROOT)
        lines.append(f"    {str(relative):28s} -> {hits if hits else 'no numpy/scipy mention'}")
    lock = _REPO_ROOT / "uv.lock"
    if lock.exists():
        lock_text = lock.read_text(encoding="utf-8")
        for name in ("numpy", "scipy"):
            present = f'name = "{name}"' in lock_text
            lines.append(
                f"    uv.lock                      -> {name}: "
                f"{'PRESENT' if present else 'absent'}"
            )
    return lines


# --------------------------------------------------------------------------- #
# The regimes.
# --------------------------------------------------------------------------- #
#: The headline regime: union bulk near 0.60, absent arm near 0.44, so the
#: adopted floor lands just above the absent arm's maximum with a thin slice of
#: the union below it — the RECORDED 1/56, 15/15 shape.
HEADLINE_REGIME = RegimeParameters(
    label="tail-order-statistic (recorded 2026-07-07 regime)",
    union_mean=0.600,
    union_stdev=0.045,
    absent_mean=0.440,
    absent_stdev=0.035,
    anchor_fraction=0.25,
    absent_anchor_fraction=0.0,
    anchor_mode="random",
    provenance="n and rates RECORDED; distribution shape DECLARED (varied in §6)",
)

#: POSITIVE CONTROL leg 2 — the SAME procedure and the SAME code path, but the
#: absent arm overlaps the union's bulk and the false-fire ceiling is relaxed to
#: 50%, so ``choose_cosine_floor``'s dominance rule selects a floor near the
#: union's MEDIAN instead of its 2nd order statistic. Everything except the
#: statistic's DEPTH in the distribution is held fixed — which is exactly what an
#: instrument control has to do.
BULK_CONTROL_REGIME = RegimeParameters(
    label="POSITIVE CONTROL: same procedure, BULK order statistic",
    union_mean=0.600,
    union_stdev=0.045,
    absent_mean=0.580,
    absent_stdev=0.035,
    anchor_fraction=0.25,
    absent_anchor_fraction=0.0,
    anchor_mode="random",
    max_false_fire_rate=0.50,
    provenance="DECLARED control — a 50% ceiling and an overlapping absent arm move "
    "the selected floor into the bulk",
)

#: DIFFERENTLY-BROKEN CONTROL — a constant union. This is ALSO degenerate, but
#: for a different, nameable reason: only ONE candidate floor exists at all. The
#: instrument must distinguish this from the tail case, and does so by reporting
#: ``distinct_union_cosines`` beside ``distinct_values``.
CONSTANT_CONTROL_REGIME = RegimeParameters(
    label="DIFFERENTLY-BROKEN CONTROL: constant union (zero variance)",
    union_mean=0.600,
    union_stdev=0.0,
    absent_mean=0.440,
    absent_stdev=0.0,
    anchor_fraction=0.0,
    absent_anchor_fraction=0.0,
    provenance="DECLARED control — zero spread, so exactly one candidate floor exists",
)

#: §6 sensitivity leg: every DECLARED synthesis parameter, varied. A regime that
#: comes back NON-degenerate would mean the headline rests on one arbitrary
#: choice — which is the monoculture question, asked of my own fixtures.
SENSITIVITY_REGIMES: tuple[RegimeParameters, ...] = (
    HEADLINE_REGIME,
    RegimeParameters(
        label="narrow union spread (sd 0.030)",
        union_mean=0.600, union_stdev=0.030, absent_mean=0.470, absent_stdev=0.030,
        anchor_fraction=0.25, provenance="DECLARED — union spread varied down",
    ),
    RegimeParameters(
        label="wide union spread (sd 0.070)",
        union_mean=0.600, union_stdev=0.070, absent_mean=0.400, absent_stdev=0.045,
        anchor_fraction=0.25, provenance="DECLARED — union spread varied up",
    ),
    RegimeParameters(
        label="no anchors at all (anchor_fraction 0.00)",
        union_mean=0.600, union_stdev=0.045, absent_mean=0.440, absent_stdev=0.035,
        anchor_fraction=0.00, provenance="DECLARED — anchor monoculture guard, low end",
    ),
    RegimeParameters(
        label="half the union anchored (anchor_fraction 0.50)",
        union_mean=0.600, union_stdev=0.045, absent_mean=0.440, absent_stdev=0.035,
        anchor_fraction=0.50, provenance="DECLARED — anchor monoculture guard, high end",
    ),
    RegimeParameters(
        label="anchors on the HIGH-cosine samples (correlated)",
        union_mean=0.600, union_stdev=0.045, absent_mean=0.440, absent_stdev=0.035,
        anchor_fraction=0.25, anchor_mode="high_cosine",
        provenance="DECLARED — anchor/cosine correlation varied",
    ),
    RegimeParameters(
        label="absent arm ANCHORED too (absent_anchor_fraction 0.20)",
        union_mean=0.600, union_stdev=0.045, absent_mean=0.440, absent_stdev=0.035,
        anchor_fraction=0.25, absent_anchor_fraction=0.20,
        provenance="DECLARED — violates the catch-15/15-implies-no-absent-anchors reading",
    ),
    RegimeParameters(
        label="absent arm closer to the union (mean 0.500)",
        union_mean=0.600, union_stdev=0.045, absent_mean=0.500, absent_stdev=0.025,
        anchor_fraction=0.25, provenance="DECLARED — absent-arm location varied",
    ),
    RegimeParameters(
        label="heavier union lower tail (mean 0.620, sd 0.060)",
        union_mean=0.620, union_stdev=0.060, absent_mean=0.430, absent_stdev=0.040,
        anchor_fraction=0.25, provenance="DECLARED — union location + spread varied",
    ),
    RegimeParameters(
        label="UNIFORM cosines, not Gaussian (shape varied)",
        union_mean=0.600, union_stdev=0.045, absent_mean=0.470, absent_stdev=0.040,
        anchor_fraction=0.25, distribution="uniform",
        provenance="DECLARED — distribution SHAPE varied; a Gaussian's thin tail is "
        "the obvious artifact candidate, so a bounded-support shape is run too",
    ),
)


@dataclass
class LadderRow:
    """One rung of the N ladder."""

    union_size: int
    absent_size: int
    corpus: SyntheticCorpus
    bootstrap: BootstrapResult
    gate: StabilityGateMeasurement
    seconds_per_replicate: float


def run_ladder(
    regime: RegimeParameters,
    *,
    absent_size_for: Callable[[int], int],
    accept_for: Callable[[int], Callable[[SyntheticCorpus], bool] | None],
    seed: int,
    replicates: int,
    ladder: Sequence[int] = N_LADDER,
) -> list[LadderRow]:
    """Run the corpus draw, the bootstrap, D2's stability gate and the cost timing
    at every rung of ``ladder``."""
    generator = CorpusGenerator(regime)
    rows: list[LadderRow] = []
    for index, union_size in enumerate(ladder):
        rng = random.Random(seed + index)
        absent_size = absent_size_for(union_size)
        corpus = generator.draw(union_size, absent_size, rng, accept=accept_for(union_size))
        bootstrap = ProcedureBootstrap(corpus, max_false_fire_rate=regime.max_false_fire_rate)
        result = bootstrap.run(replicates, rng, label=f"N={union_size}")
        gate = measure_stability_gate(corpus.union, result.ci_low, result.ci_high)
        seconds = bootstrap.time_replicates(TIMING_REPLICATES, rng)
        rows.append(
            LadderRow(
                union_size=union_size,
                absent_size=absent_size,
                corpus=corpus,
                bootstrap=result,
                gate=gate,
                seconds_per_replicate=seconds,
            )
        )
        print(f"    ... rung N={union_size} done ({time.strftime('%H:%M:%S')})")
    return rows


def render_ladder(rows: Sequence[LadderRow], *, title: str) -> None:
    print()
    print(title)
    print(
        f"{'N':>6} {'|absent|':>9} {'floor':>10} {'rank':>6} {'ff':>7} {'catch':>7} "
        f"{'ci_low':>10} {'ci_high':>10} {'width':>9} {'distinct':>9} {'modal%':>8} "
        f"{'degen':>6} {'agree':>8}  gate"
    )
    for row in rows:
        gate_note = "PASS" if row.gate.passes else "FAIL"
        if row.gate.trivially:
            gate_note += " (TRIVIALLY: ci_low == ci_high)"
        print(
            f"{row.union_size:>6} {row.absent_size:>9} "
            f"{row.corpus.recommendation.floor:>10.6f} "
            f"{row.corpus.floor_rank_in_union:>6} "
            f"{row.corpus.recommendation.false_fire_rate:>7.4f} "
            f"{row.corpus.recommendation.nonsense_catch_rate:>7.3f} "
            f"{row.bootstrap.ci_low:>10.6f} {row.bootstrap.ci_high:>10.6f} "
            f"{row.bootstrap.ci_width:>9.6f} {row.bootstrap.distinct_values:>9} "
            f"{row.bootstrap.modal_mass:>7.1%} "
            f"{'YES' if row.bootstrap.is_degenerate else 'no':>6} "
            f"{row.gate.agreement:>7.2%}  {gate_note}"
        )


# --------------------------------------------------------------------------- #
# Main.
# --------------------------------------------------------------------------- #
def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)
    started = time.perf_counter()
    print("probe_bootstrap_degeneracy.py — packet 11-i, blind-review residual S1")
    print("Measured 2026-07-25. Pure local statistics: no store, no embedder, no network.")
    print()
    print("PROVENANCE OF THE CODE UNDER TEST (which tree am I measuring?):")
    import loremaster.search as production_search
    import search_score_survey as survey

    print(f"    search_score_survey.__file__ = {survey.__file__}")
    print(f"    loremaster.search.__file__   = {production_search.__file__}")
    print(f"    repo root                    = {_REPO_ROOT}")
    print(
        f"    choose_cosine_floor          = "
        f"{choose_cosine_floor.__module__}.{choose_cosine_floor.__qualname__}"
    )
    print(
        f"    verdict predicate            = "
        f"{cosine_absence_verdict_fires.__module__}.{cosine_absence_verdict_fires.__qualname__}"
    )
    print(
        f"    imported bars                = D2_MAX_FALSE_FIRE_RATE={D2_MAX_FALSE_FIRE_RATE} "
        f"D2_MIN_NONSENSE_CATCH_RATE={D2_MIN_NONSENSE_CATCH_RATE}"
    )
    print(
        f"    pre-registered               = B={BOOTSTRAP_REPLICATES} "
        f"CI=[p{CI_LOW_PERCENTILE:g}, p{CI_HIGH_PERCENTILE:g}] "
        f"stability_gate>={STABILITY_GATE_AGREEMENT:.0%}"
    )
    print(f"    python                       = {sys.version.split()[0]}, cpus={os.cpu_count()}")

    # ---------------------------------------------------------------- §0 controls
    heading(
        "§0  CONTROLS FIRST — a negative result is worthless until the instrument is "
        "shown firing"
    )

    control_rng = random.Random(101)
    headline_corpus = CorpusGenerator(HEADLINE_REGIME).draw(
        RECORDED_UNION_N, RECORDED_NONSENSE_N, control_rng, accept=recorded_regime_predicate
    )
    median_control = MedianStatisticBootstrap(headline_corpus).run(
        BOOTSTRAP_REPLICATES, control_rng, label="POSITIVE CONTROL 1 — union MEDIAN cosine"
    )
    print()
    print("Positive control 1 — the same resampler and the same CI code, over a BULK statistic")
    print("(the union's median cosine), on the VERY SAME synthetic corpus as the headline run.")
    render_bootstrap(median_control, indent="    ")
    if median_control.is_degenerate:
        print("    !! CONTROL FAILED — the harness cannot see spread. Every result below is VOID.")
        return 1
    print("    -> control PASSES: the harness resolves a non-degenerate interval when one exists.")

    bulk_rng = random.Random(202)
    bulk_corpus = CorpusGenerator(BULK_CONTROL_REGIME).draw(
        RECORDED_UNION_N, RECORDED_NONSENSE_N, bulk_rng
    )
    bulk_result = ProcedureBootstrap(
        bulk_corpus, max_false_fire_rate=BULK_CONTROL_REGIME.max_false_fire_rate
    ).run(
        BOOTSTRAP_REPLICATES, bulk_rng, label="POSITIVE CONTROL 2 — choose_cosine_floor, BULK floor"
    )
    bulk_gate = measure_stability_gate(bulk_corpus.union, bulk_result.ci_low, bulk_result.ci_high)
    print()
    print("Positive control 2 — the REAL choose_cosine_floor, same N=56, but the dominance rule")
    print("selects a floor in the union's BULK (absent arm overlaps the union; ceiling relaxed to")
    print(
        f"{BULK_CONTROL_REGIME.max_false_fire_rate:.0%}, DECLARED). Only the statistic's DEPTH changes."
    )
    print(
        f"    selected floor rank in union = {bulk_corpus.floor_rank_in_union} / "
        f"{len(bulk_corpus.union)}  (false-fire "
        f"{bulk_corpus.recommendation.false_fire_rate:.3f}, catch "
        f"{bulk_corpus.recommendation.nonsense_catch_rate:.3f})"
    )
    render_bootstrap(bulk_result, indent="    ")
    print(
        f"    D2 stability gate here: agreement {bulk_gate.agreement:.2%} "
        f"({bulk_gate.disagreeing_samples}/{bulk_gate.union_size} decisions flip) -> "
        f"{'PASS' if bulk_gate.passes else 'FAIL'}"
        f"{' (TRIVIALLY)' if bulk_gate.trivially else ''}"
    )
    if bulk_result.is_degenerate:
        print("    !! CONTROL FAILED — choose_cosine_floor is degenerate even on a BULK statistic.")
        print("       That would mean the HARNESS, not the tail, produces degeneracy. Result VOID.")
        return 1
    print("    -> control PASSES: the SELECTION PROCEDURE is not intrinsically degenerate.")

    constant_rng = random.Random(303)
    constant_corpus = CorpusGenerator(CONSTANT_CONTROL_REGIME).draw(
        RECORDED_UNION_N, RECORDED_NONSENSE_N, constant_rng
    )
    constant_result = ProcedureBootstrap(
        constant_corpus, max_false_fire_rate=CONSTANT_CONTROL_REGIME.max_false_fire_rate
    ).run(
        BOOTSTRAP_REPLICATES, constant_rng, label="DIFFERENTLY-BROKEN CONTROL — constant union"
    )
    print()
    print("Differently-broken control — a CONSTANT union. Also degenerate, for a DIFFERENT and")
    print("nameable reason, and the instrument must be able to tell the two apart:")
    render_bootstrap(constant_result, indent="    ")
    print(
        f"    distinct OBSERVED union cosines: constant-control="
        f"{constant_corpus.distinct_union_cosines}  vs  headline-corpus="
        f"{headline_corpus.distinct_union_cosines}"
    )
    print("    -> separable: the constant control has ONE candidate floor in existence (zero-")
    print("       variance data). The headline corpus has N distinct candidates and collapses")
    print("       anyway — that collapse is the SELECTION RULE reaching into the tail, not an")
    print("       absence of data. Different named causes, distinguishable by this column.")

    # ---------------------------------------------------------------- §1 headline
    heading("§1  HEADLINE — the recorded 2026-07-07 regime at N=56")
    print(f"regime: {HEADLINE_REGIME.label}")
    print(f"    provenance: {HEADLINE_REGIME.provenance}")
    print(
        f"    synthesis parameters: union~N({HEADLINE_REGIME.union_mean}, "
        f"{HEADLINE_REGIME.union_stdev})  absent~N({HEADLINE_REGIME.absent_mean}, "
        f"{HEADLINE_REGIME.absent_stdev})  anchor_fraction={HEADLINE_REGIME.anchor_fraction} "
        f"absent_anchor_fraction={HEADLINE_REGIME.absent_anchor_fraction} "
        f"mode={HEADLINE_REGIME.anchor_mode}"
    )
    print(
        f"    regime match (rejection-sampled to the RECORDED values): false-fire "
        f"{headline_corpus.false_fire_count}/{len(headline_corpus.union)}  catch "
        f"{headline_corpus.recommendation.nonsense_catch_rate:.0%}  "
        f"({headline_corpus.draws_attempted} draws to land in regime)"
    )
    print(
        f"    adopted floor = {headline_corpus.recommendation.floor:.6f}, which is order "
        f"statistic #{headline_corpus.floor_rank_in_union} of {len(headline_corpus.union)} union "
        f"cosines ({headline_corpus.floor_rank_in_union / len(headline_corpus.union):.2%} of the "
        f"way up) -- the S1 objection, measured"
    )
    headline_result = ProcedureBootstrap(
        headline_corpus, max_false_fire_rate=HEADLINE_REGIME.max_false_fire_rate
    ).run(BOOTSTRAP_REPLICATES, control_rng, label="HEADLINE — choose_cosine_floor bootstrap, N=56")
    render_bootstrap(headline_result, indent="    ")
    headline_gate = measure_stability_gate(
        headline_corpus.union, headline_result.ci_low, headline_result.ci_high
    )
    print(
        f"    D2 stability gate: agreement {headline_gate.agreement:.2%} "
        f"({headline_gate.disagreeing_samples}/{headline_gate.union_size} decisions flip) -> "
        f"{'PASS' if headline_gate.passes else 'FAIL'}"
        f"{'   <-- TRIVIALLY: ci_low == ci_high, the gate CANNOT disagree' if headline_gate.trivially else ''}"
    )

    # ---------------------------------------------------------------- §2 ladders
    heading("§2  THE N LADDER — does degeneracy resolve, and at what N?")
    print("Leg A (LEGACY instrument shape): the absent arm is the FIXED 15-query nonsense set")
    print("(search_score_survey.NONSENSE_QUERIES is a fixed 15-tuple); only the union grows.")
    ladder_a = run_ladder(
        HEADLINE_REGIME,
        absent_size_for=lambda _size: RECORDED_NONSENSE_N,
        accept_for=lambda size: (
            recorded_regime_predicate if size == RECORDED_UNION_N else scaled_regime_predicate
        ),
        seed=1000,
        replicates=BOOTSTRAP_REPLICATES,
    )
    render_ladder(ladder_a, title="LEG A — absent arm FIXED at 15")

    print()
    print("Leg B (PORTABLE design shape, Addendum D1/D2): the absent/hold-out arm scales with the")
    print("pool, keeping the recorded 56:15 ratio, so BOTH arms are resampled at the ladder's N.")
    ladder_b = run_ladder(
        HEADLINE_REGIME,
        absent_size_for=lambda size: max(
            RECORDED_NONSENSE_N, round(size * RECORDED_NONSENSE_N / RECORDED_UNION_N)
        ),
        accept_for=lambda _size: None,
        seed=2000,
        replicates=BOOTSTRAP_REPLICATES,
    )
    render_ladder(ladder_b, title="LEG B — absent arm SCALES with the pool")

    # ---------------------------------------------------------------- §3 gate
    heading("§3  SILENT FAILURE (a) — does D2's >=98% decision-agreement gate pass TRIVIALLY?")
    print("D2 adopts the SMALLEST N whose interval passes the gate. If the gate passes trivially")
    print("at the smallest N tried, the N-curve is not a stability measurement at all.")
    for leg_name, rows in (("A (absent fixed 15)", ladder_a), ("B (absent scales)", ladder_b)):
        smallest = rows[0]
        print()
        print(
            f"    leg {leg_name}: at the SMALLEST N tried ({smallest.union_size}) the gate "
            f"{'PASSES' if smallest.gate.passes else 'FAILS'} at {smallest.gate.agreement:.2%} "
            f"-- {'TRIVIALLY (ci_low == ci_high)' if smallest.gate.trivially else 'non-trivially'}"
        )
        adopted = next((row for row in rows if row.gate.passes), None)
        if adopted is not None:
            print(
                f"      -> D2 would adopt N={adopted.union_size} (the first rung that passes)"
                f"{'; that pass is TRIVIAL' if adopted.gate.trivially else ''}"
            )
        else:
            print("      -> no rung passes the gate")
        trivial_rungs = [row.union_size for row in rows if row.gate.trivially]
        print(f"      -> rungs whose interval is a single point: {trivial_rungs or 'none'}")

    # ---------------------------------------------------------------- §4 flapping
    heading("§4  SILENT FAILURE (b) — the flapping rate of D3's disjoint-CI adoption")
    print("Two INDEPENDENT measurements drawn from the SAME generator: the true floor has NOT")
    print("moved. D3 adopts iff the two CIs are DISJOINT. Anything far above 0 is adoption-on-")
    print("noise, i.e. the inverse of the design's 'hysteresis falls out free'.")
    workers = max(1, min(32, (os.cpu_count() or 2) - 2))
    print(f"(parallelised over {workers} worker processes; every pair is independently seeded,")
    print(" so the result is identical to a serial run)")
    flapping_rows: list[PairMeasurement] = []
    power_rows: list[tuple[int, PairMeasurement]] = []
    context = multiprocessing.get_context("fork")
    with ProcessPoolExecutor(max_workers=workers, mp_context=context) as executor:
        for union_size in FLAPPING_LADDER:
            flapping_rows.append(
                measure_pairs(
                    HEADLINE_REGIME,
                    union_size=union_size,
                    absent_size=RECORDED_NONSENSE_N,
                    accept_name=("recorded" if union_size == RECORDED_UNION_N else "scaled"),
                    seed=5_000_000 + union_size * 1000,
                    replicates=BOOTSTRAP_REPLICATES,
                    pairs=FLAPPING_PAIRS,
                    label=f"tail regime, leg A, N={union_size}",
                    executor=executor,
                )
            )
            print(f"    ... flapping N={union_size} done ({time.strftime('%H:%M:%S')})")
        flapping_rows.append(
            measure_pairs(
                BULK_CONTROL_REGIME,
                union_size=RECORDED_UNION_N,
                absent_size=RECORDED_NONSENSE_N,
                accept_name="none",
                seed=7_000_000,
                replicates=BOOTSTRAP_REPLICATES,
                pairs=FLAPPING_PAIRS,
                label="POSITIVE CONTROL (bulk floor), N=56",
                executor=executor,
            )
        )
        print()
        print(
            f"{'regime':>46} {'pairs':>7} {'disjoint':>9} {'flap rate':>11} {'point moved':>13} "
            f"{'mean |dfloor|':>14}"
        )
        for measurement in flapping_rows:
            print(
                f"{measurement.label:>46} {measurement.pairs:>7} {measurement.disjoint:>9} "
                f"{measurement.adoption_rate:>11.1%} {measurement.point_movement_rate:>13.1%} "
                f"{measurement.mean_absolute_point_difference:>14.6f}"
            )

        # ------------------------------------------------------- §7 detection power
        heading("§4b  THE DUAL — can D3's disjoint-CI test detect a REAL move?")
        print("A false-positive rate is meaningless without a detection rate: a test that NEVER")
        print("fires has a perfect flapping rate and detects nothing. Same instrument, same pairs,")
        print("but the SECOND corpus is drawn from a regime translated by a known cosine SHIFT")
        print("(both arms, so false-fire/catch are preserved and the TRUE floor moves by exactly")
        print("that much). shift=0.000 is §4's flapping row; every other row is D3's POWER.")
        for union_size in POWER_LADDER:
            for shift in POWER_SHIFTS:
                power_rows.append(
                    (
                        union_size,
                        measure_pairs(
                            HEADLINE_REGIME,
                            union_size=union_size,
                            absent_size=RECORDED_NONSENSE_N,
                            accept_name=(
                                "recorded" if union_size == RECORDED_UNION_N else "scaled"
                            ),
                            seed=8_000_000 + union_size * 10_000 + round(shift * 1000),
                            replicates=BOOTSTRAP_REPLICATES,
                            pairs=FLAPPING_PAIRS,
                            label=f"N={union_size}, shift={shift:+.3f}",
                            executor=executor,
                            shift=shift,
                        ),
                    )
                )
            print(f"    ... power ladder N={union_size} done ({time.strftime('%H:%M:%S')})")
    print()
    print(
        f"{'N':>6} {'true floor shift':>18} {'pairs':>7} {'CIs disjoint':>13} "
        f"{'D3 ADOPTS':>11} {'mean |dfloor|':>14}  note"
    )
    for union_size, measurement in power_rows:
        note = (
            "<- the null: FALSE-adoption rate"
            if measurement.shift == 0.0
            else "<- DETECTION rate for a real move"
        )
        print(
            f"{union_size:>6} {measurement.shift:>18.3f} {measurement.pairs:>7} "
            f"{measurement.disjoint:>13} {measurement.adoption_rate:>11.1%} "
            f"{measurement.mean_absolute_point_difference:>14.6f}  {note}"
        )
    print()
    print("    SANITY CHECK on the shift plumbing: mean |dfloor| must track the shift column.")
    print("    (A previous revision of this script omitted `shift=shift` at the call site, so")
    print("     every row silently re-measured the null. The check below is why that is now")
    print("     visible rather than plausible-looking.)")

    # ---------------------------------------------------------------- §5 cost
    heading("§5  COST — is 'free at any N' (Addendum D1) true?")
    print("Single-threaded seconds per bootstrap replicate (resample both arms + one real")
    print(f"choose_cosine_floor call), timed over {TIMING_REPLICATES} replicates per rung.")
    print()
    print(f"{'N':>6} {'|absent|':>9} {'ms/replicate':>14} {'s @ B=1000':>12} {'leg':>5}")
    for leg_name, rows in (("A", ladder_a), ("B", ladder_b)):
        for row in rows:
            print(
                f"{row.union_size:>6} {row.absent_size:>9} "
                f"{row.seconds_per_replicate * 1000:>14.3f} "
                f"{row.seconds_per_replicate * BOOTSTRAP_REPLICATES:>12.2f} {leg_name:>5}"
            )
    exponent_a = fit_log_log_exponent(
        [row.union_size for row in ladder_a], [row.seconds_per_replicate for row in ladder_a]
    )
    exponent_b = fit_log_log_exponent(
        [row.union_size for row in ladder_b], [row.seconds_per_replicate for row in ladder_b]
    )
    print()
    print(
        f"    empirical growth exponent (log-log least squares): leg A = {exponent_a:.3f}, "
        f"leg B = {exponent_b:.3f}"
    )
    print("    Addendum D1 claims the bootstrap is 'free at any N' because it costs ZERO embeds.")
    print("    Zero embeds is TRUE. 'Free at any N' is a claim about COST, and cost is the table")
    print("    above: choose_cosine_floor is O(U*(U+A)) per call, times B calls per measurement.")
    print()
    print("    numpy/scipy availability (re-verified in THIS run, nothing inherited):")
    for line in verify_numeric_stack_absence():
        print(line)

    # ---------------------------------------------------------------- §6 sensitivity
    heading("§6  SENSITIVITY — is the verdict an artifact of an unrecorded parameter?")
    print("Every DECLARED synthesis parameter, varied. A regime that came back DEGENERATE where")
    print("the headline did not (or vice versa) would mean the headline rests on one arbitrary")
    print("choice. The 'accept' column says which regime predicate each row landed under: the")
    print("RECORDED one (false-fire exactly 1/56, catch 15/15) where reachable, else 'usable'")
    print("(catch >= the 60% adoption bar AND >=1 union sample below the floor) — several")
    print("variations cannot reach 100% catch by construction, and demanding it would silently")
    print("exclude exactly the variations this leg exists to test.")
    print()
    print(
        f"{'regime':>52} {'accept':>9} {'floor':>10} {'rank':>6} {'ff':>7} {'catch':>7} "
        f"{'ci_low':>10} {'ci_high':>10} {'width':>9} {'distinct':>9} {'modal%':>8} {'degen':>6}"
    )
    for index, regime in enumerate(SENSITIVITY_REGIMES):
        rng = random.Random(9000 + index)
        generator = CorpusGenerator(regime)
        try:
            corpus = generator.draw(
                RECORDED_UNION_N,
                RECORDED_NONSENSE_N,
                rng,
                accept=recorded_regime_predicate,
                max_attempts=5_000,
            )
            accept_used = "recorded"
        except RuntimeError:
            corpus = generator.draw(
                RECORDED_UNION_N, RECORDED_NONSENSE_N, rng, accept=usable_regime_predicate
            )
            accept_used = "usable"
        result = ProcedureBootstrap(
            corpus, max_false_fire_rate=regime.max_false_fire_rate
        ).run(BOOTSTRAP_REPLICATES, rng, label=regime.label)
        print(
            f"{regime.label[:52]:>52} {accept_used:>9} {corpus.recommendation.floor:>10.6f} "
            f"{corpus.floor_rank_in_union:>6} {corpus.recommendation.false_fire_rate:>7.4f} "
            f"{corpus.recommendation.nonsense_catch_rate:>7.3f} "
            f"{result.ci_low:>10.6f} {result.ci_high:>10.6f} {result.ci_width:>9.6f} "
            f"{result.distinct_values:>9} {result.modal_mass:>7.1%} "
            f"{'YES' if result.is_degenerate else 'no':>6}"
        )

    # ---------------------------------------------------------------- verdict
    heading("MEASURED SUMMARY (the verdict is argued in REPORT-probe-bootstrap-11i.md)")
    degenerate_a = [row.union_size for row in ladder_a if row.bootstrap.is_degenerate]
    degenerate_b = [row.union_size for row in ladder_b if row.bootstrap.is_degenerate]
    first_clean_a = next(
        (row.union_size for row in ladder_a if not row.bootstrap.is_degenerate), None
    )
    first_clean_b = next(
        (row.union_size for row in ladder_b if not row.bootstrap.is_degenerate), None
    )
    print(f"    headline N=56 CI degenerate: {headline_result.is_degenerate}")
    print(f"    leg A (absent fixed 15)  — degenerate rungs: {degenerate_a or 'none'}")
    print(f"    leg B (absent scales)    — degenerate rungs: {degenerate_b or 'none'}")
    print(f"    smallest NON-degenerate N: leg A = {first_clean_a}, leg B = {first_clean_b}")
    print(f"    controls: median={'DEGENERATE' if median_control.is_degenerate else 'clean'}, "
          f"bulk-floor={'DEGENERATE' if bulk_result.is_degenerate else 'clean'}, "
          f"constant={'DEGENERATE (expected)' if constant_result.is_degenerate else 'clean (UNEXPECTED)'}")
    print(f"    headline N=56 CI width: {headline_result.ci_width:.6f} cosine units "
          f"on a floor of {headline_result.point_estimate:.6f} "
          f"({headline_result.ci_width / headline_result.point_estimate:.1%} of the floor); "
          f"{headline_result.distinct_values} distinct resampled values")
    print(f"    D2 stability gate at N=56: {headline_gate.agreement:.2%} -> "
          f"{'PASS' if headline_gate.passes else 'FAIL'}")
    print(f"    D3 flapping rate at N=56 (nothing moved): "
          f"{flapping_rows[0].adoption_rate:.1%}")
    for union_size, measurement in power_rows:
        if union_size == RECORDED_UNION_N:
            print(
                f"    D3 adoption rate at N=56, true floor moved {measurement.shift:+.3f}: "
                f"{measurement.adoption_rate:.1%}"
            )
    print(f"    total wall clock: {time.perf_counter() - started:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
