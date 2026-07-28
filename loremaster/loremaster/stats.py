"""Shared statistics — ONE implementation of this repo's percentile policy.

Finding #198: the same nearest-rank percentile policy was hand-rolled four
times across this repo, under three signatures and two unit conventions.  The
copies agreed with each other by luck rather than by construction, and a fifth
was about to be written.  This module is the single seam they share.

**Call these functions; do not re-implement them.**  If one does not fit a new
caller, extend it here — a second copy is how a fix reaches one survey and not
the others, which is exactly the defect #198 records.

**Why this lives in ``loremaster`` and not in ``scripts/``** (it took three
passes to get right, so the reasoning is recorded rather than re-derived):
``scripts/`` is not a package and is not baked into the deployed image, so
production code — packet 11-i-b's floor-calibration engine — could not import a
seam placed there, and would have written copy #5.  The consumer this finding
exists to protect is production, so the seam has to be installed.  This mirrors
the #207 fix, which put the shared full-jitter backoff policy in
``loresigil/backoff.py`` for the same reason.  A placement under ``scripts/``
also forced consumers into ``sys.path`` manipulation, which measurably broke the
deploy smoke when it was run detached from the repo; a normal package import
cannot fail in any context where the caller can run at all.

The policy, stated once:

* **Nearest-rank, never interpolating.**  The returned number is always a value
  that was actually measured, never one synthesised between two samples.  A
  latency budget or a token ceiling argued from a number nothing ever observed
  is a harder thing to defend than one that really happened.
* **Two unit faces, one conversion.**  :func:`nearest_rank_quantile` takes a
  ``[0, 1]`` fraction (numpy's own unit); :func:`nearest_rank_percentile` takes a
  ``[0, 100]`` percent.  The ``/100`` exists in exactly one place, because a repo
  that converted at each call site would be one dropped division away from
  asking for the 0.95th percentile instead of the 95th.
* **Empty is an error, not zero.**  A percentile of nothing is undefined;
  returning ``0.0`` would read as "impossibly fast" in a latency receipt and as
  "no token bloat" in a ratio receipt.
* **Weights must be strictly positive, and that is ENFORCED** — see
  :func:`weighted_nearest_rank_percentile` for why the check, not merely the
  docstring, is what makes the numpy implementation sound.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np

#: The numpy quantile conventions this repo has reasoned about.  Named as a type
#: so ``QUANTILE_METHOD`` cannot be set to a string numpy would reject at
#: runtime, and so the alternatives are visible at the point of the choice.
QuantileMethod = Literal[
    "inverted_cdf", "linear", "higher", "lower", "nearest", "midpoint"
]

#: The numpy quantile convention this repo's surveys are calibrated against.
#: ``inverted_cdf`` is method 1 of Hyndman & Fan: rank ``ceil(n * q)``, clamped
#: to ``[1, n]`` — identical to the ceil-rank arithmetic the retired hand-rolls
#: used, proven by equality over the corpus in ``loremaster/tests/test_stats.py``.
#:
#: Changing this constant changes every published survey number.  Every caller's
#: equality pin is wired to it precisely so that such a change cannot be made
#: quietly: mutate it and every consumer's pin reddens.
QUANTILE_METHOD: QuantileMethod = "inverted_cdf"


def nearest_rank_quantile(values: Sequence[float], q: float) -> float:
    """The nearest-rank quantile of ``values`` at ``q`` in ``[0, 1]``.

    This is the CORE: ``q`` is numpy's own unit, so callers that already hold a
    fraction (``docs/eval/smoke_p8b.py``) reach numpy without a unit round trip.
    Callers holding a percent use :func:`nearest_rank_percentile`, which is the
    ONLY place the ``/100`` conversion happens.

    Args:
        values: The observed sample. Order is irrelevant; it is sorted here.
        q: The quantile in ``[0, 1]`` — a fraction, not a percent.

    Returns:
        The quantile, always one of the values in ``values``.

    Raises:
        ValueError: If ``values`` is empty. numpy itself raises ``IndexError``
            here, which would read as a coding bug rather than as the domain
            error it is, so it is converted.
    """
    if len(values) == 0:
        raise ValueError("cannot take a percentile of zero observations")
    return float(np.quantile(np.asarray(values, dtype=float), q, method=QUANTILE_METHOD))


def nearest_rank_percentile(values: Sequence[float], pct: float) -> float:
    """The nearest-rank percentile of ``values`` at ``pct`` in ``[0, 100]``.

    The percent-unit face of :func:`nearest_rank_quantile`.

    Args:
        values: The observed sample. Order is irrelevant; it is sorted here.
        pct: The percentile in ``[0, 100]`` — a percent, not a fraction.

    Returns:
        The ``pct``-th percentile, always one of the values in ``values``.

    Raises:
        ValueError: If ``values`` is empty.
    """
    return nearest_rank_quantile(values, pct / 100.0)


def weighted_nearest_rank_percentile(
    values: Sequence[float], weights: Sequence[float], pct: float
) -> float:
    """The WEIGHT-ed nearest-rank percentile — each value counts ``weight`` times.

    Answers "for X% of the weighted mass, the value is at most this".  Weighting
    a token ratio by token count is the motivating case: it reports the ceiling
    the token-mass actually needs, not the one an unweighted file count implies.

    **Every weight must be > 0, and that is ENFORCED here (finding #198).**  The
    retired hand-roll promised this in its docstring and never checked it, and
    the two implementations disagree precisely where the promise was broken:
    numpy skips leading zero-weight entries at ``q=0`` (``cdf[cdf == 0] = -1``
    in ``numpy/lib/_function_base_impl.py``) and rejects an all-zero weight
    vector, while the hand-roll returned a zero-weight value and a minimum
    respectively.  Rejecting non-positive weights makes both divergences
    unreachable by construction rather than by luck, so numpy and the retired
    implementation agree over the entire admissible domain.

    Args:
        values: The observed sample.
        weights: One strictly positive weight per value, same order.
        pct: The percentile in ``[0, 100]``.

    Returns:
        The weighted percentile, always one of the values in ``values``.

    Raises:
        ValueError: If ``values`` is empty, if the lengths differ, or if any
            weight is <= 0.
    """
    if len(values) == 0:
        raise ValueError("cannot take a percentile of zero observations")
    if len(values) != len(weights):
        raise ValueError(
            f"every value needs one weight: got {len(values)} values, {len(weights)} weights"
        )
    if any(weight <= 0 for weight in weights):
        raise ValueError("every weight must be > 0")
    return float(
        np.quantile(
            np.asarray(values, dtype=float),
            pct / 100.0,
            method=QUANTILE_METHOD,
            weights=np.asarray(weights, dtype=float),
        )
    )
