"""INSTRUMENT H (finding #290) — anti-vacuity on a COMPARISON's baseline, as a SHARED guard.

Contract, RED at HEAD ``e1dfa14``: it pins ``scripts/_harness_guards.py::refuse_vacuous_baseline``,
which DOES NOT EXIST yet (imported dynamically so the typecheck gate over ``scripts/`` stays green
while pytest is red). The guard is to be EXTRACTED from the inline check now living in
``scripts/wrong_builds.py::main`` (finding #290's fix) so any harness grading N runs against a
baseline shares ONE answer to "did the baseline measure anything?".

THE DEFECT #290 NAMES. ``wrong_builds.py`` grades each mutation by comparing its collected total to
the BASELINE's total (its guard #2). Run through a python with no pytest, the baseline collected 0 —
and every build then compared ``0 == 0``, failure-free, and was reported ``❗SURVIVED``. Three
phantom survivors against a contract that had never run; over the full set the census would have
read ``21 survived`` = "this contract catches nothing", entirely an artifact of a missing pytest.

THE GENERALISATION (finding #290 body, verbatim intent): "an anti-vacuity check on a COMPARISON's
REFERENCE value is a distinct guard from anti-vacuity on the things being compared, and it is the one
that gets skipped." ``wrong_builds`` already had per-run guards (anchor-lands-exactly-once; total ==
baseline). What it lacked was a guard on the REFERENCE ITSELF. This contract pins that DISTINCT guard
AND the distinction (``TestTheZeroBaselineTrapIsReal`` shows the per-run comparison cannot see a
vacuous baseline; ``TestRefuseVacuousBaseline`` shows the reference-guard that can).

INTENDED SIGNATURE (design doc §INSTRUMENT H; the builder implements to this, the contract calls it
dynamically):

    def refuse_vacuous_baseline(measured_count: int, *, cause_hint: str, interpreter: str) -> None:
        '''Raise a hard, DIAGNOSTIC failure when ``measured_count`` is zero (the reference measured
        nothing); return None otherwise. The diagnostic NAMES the likely cause and the child
        interpreter — never a silent pass.'''

``SystemExit`` is pinned as the raised type (below), to preserve ``wrong_builds.main``'s exit-1
behaviour on extraction — see the report's decisions-needed for the SystemExit-vs-custom-exception
fork.

WHY ``scripts/`` and gated: ``scripts`` is a ``testpaths`` entry AND a ``scripts/typecheck.sh``
MEMBERS root, so this contract and the helper it pins are gated on both axes from birth.

⚠ MIXED COLOUR, stated: ``TestTheZeroBaselineTrapIsReal`` is GREEN at HEAD — it demonstrates the
DISEASE with pure arithmetic and needs no helper. Everything under ``TestRefuseVacuousBaseline`` is
RED until the helper exists.

SCOPE NOTE (this contract author's writable set is these two NEW files only): the EXTRACTION — moving
the inline guard out of ``wrong_builds.main`` into ``_harness_guards`` and having ``main`` CALL it —
plus the mutation proof "delete the call in ``main`` → a covering pin reddens" are the BUILDER's, in
``scripts/wrong_builds.py`` / ``scripts/test_wrong_builds.py`` (OUTSIDE this file). This contract
pins the helper's behaviour directly; the wiring proof is specced in the report.

How to run:  uv run pytest scripts/test_harness_guards.py -n auto -q
"""

from __future__ import annotations

import importlib
import os
import sys
from typing import Any

import pytest

# ``scripts/`` is not a package; the path insert must precede the sibling import, exactly as every
# other contract in this directory does it (test_gated_ground, test_wrong_builds, …).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

#: Distinctive sentinels the diagnostic MUST echo — a guard that raises but drops these is the
#: silent-ish failure #290 is about (it names no cause), so the message-content pins key on them.
_INTERPRETER = "/nonexistent/venv/bin/python"
_CAUSE_HINT = "the child interpreter has no pytest"


def _refuse_vacuous_baseline() -> Any:
    """Dynamic import of the NOT-YET-BUILT shared guard.

    ``importlib.import_module`` (not ``from _harness_guards import …``) so mypy does not hard-error on
    a module absent at ``e1dfa14`` — the typecheck gate over ``scripts/`` must stay GREEN while this
    pytest contract is RED. At runtime the missing module raises ``ModuleNotFoundError`` inside each
    test body, which is the RED this contract owes.
    """
    return importlib.import_module("_harness_guards").refuse_vacuous_baseline


class TestTheZeroBaselineTrapIsReal:
    """GREEN control — the DISEASE, with pure arithmetic and no helper.

    This is the DISTINCTION the brief asks for, made concrete: the per-run comparison
    (``total == baseline``) that ``wrong_builds`` already performs is SATISFIED by a zero baseline, so
    it can never be the guard that catches a vacuous reference. That is WHY anti-vacuity on the
    REFERENCE value has to be a separate guard.
    """

    def test_a_zero_baseline_makes_a_broken_run_read_as_survived(self) -> None:
        baseline = 0  # the reference measured NOTHING (e.g. the child interpreter had no pytest)
        broken_run_total = 0  # a broken build also collects nothing
        broken_run_failures = 0
        comparable = broken_run_total == baseline  # wrong_builds guard #2 — SATISFIED by 0 == 0
        reads_as_survived = comparable and broken_run_failures == 0
        assert reads_as_survived, (
            "the per-run comparison alone cannot see a vacuous baseline: 0 == 0 is 'comparable', "
            "0 failures reads as 'survived' — the #290 phantom survivor exactly"
        )

    def test_a_real_baseline_would_not_hide_a_broken_run(self) -> None:
        """NEGATIVE CONTROL: with a real (non-zero) baseline, a broken run's zero total is NOT
        comparable, so the per-run guard DOES fire. This proves the trap is specific to the vacuous
        REFERENCE, not a defect in the comparison itself."""
        baseline = 315
        broken_run_total = 0
        assert broken_run_total != baseline


class TestRefuseVacuousBaseline:
    """RED — ``_harness_guards.refuse_vacuous_baseline(measured_count, *, cause_hint, interpreter)``.

    THE PROPERTY: a baseline/reference of zero is a HARD failure that NAMES the likely cause and the
    child interpreter — never a silent pass. A non-zero baseline passes untouched and returns None.
    """

    @staticmethod
    def _guard() -> Any:
        return _refuse_vacuous_baseline()

    def test_a_zero_baseline_raises(self) -> None:
        """POSITIVE CONTROL — the guard fires on the vacuous reference. Kills a build that returns
        None on 0 (i.e. no guard at all — the HEAD-minus-#290-fix state)."""
        with pytest.raises(SystemExit):
            self._guard()(0, cause_hint=_CAUSE_HINT, interpreter=_INTERPRETER)

    def test_a_nonzero_baseline_passes_and_returns_none(self) -> None:
        """NEGATIVE CONTROL — a guard that refused a REAL measurement would block every honest run
        and get switched off. Kills a build that always raises."""
        assert self._guard()(315, cause_hint=_CAUSE_HINT, interpreter=_INTERPRETER) is None

    def test_a_baseline_of_one_is_a_real_measurement_and_passes(self) -> None:
        """BOUNDARY — one collected item IS a measurement. The refusal is keyed on 'nothing
        measured', not on 'small'. Kills a build thresholding on ``< 2`` / ``<= 1``."""
        assert self._guard()(1, cause_hint=_CAUSE_HINT, interpreter=_INTERPRETER) is None

    def test_the_refusal_names_the_interpreter(self) -> None:
        """#290's core: the guard must NAME THE LIKELY CAUSE, not fail silently. The most common
        cause is the child interpreter (a python with no pytest), so the diagnostic must ECHO it.
        Kills a build that raises but drops the interpreter — a guard that says nothing is the
        silent-ish failure #290 is about."""
        with pytest.raises(SystemExit) as excinfo:
            self._guard()(0, cause_hint=_CAUSE_HINT, interpreter=_INTERPRETER)
        assert _INTERPRETER in str(excinfo.value)

    def test_the_refusal_carries_the_cause_hint(self) -> None:
        """The caller's cause hint is surfaced too — a REUSABLE guard cannot hardcode ``wrong_builds``'
        own cause, so the diagnostic must include what the caller passed. Kills a build that ignores
        ``cause_hint`` and hardcodes a message."""
        with pytest.raises(SystemExit) as excinfo:
            self._guard()(0, cause_hint=_CAUSE_HINT, interpreter=_INTERPRETER)
        assert _CAUSE_HINT in str(excinfo.value)

    def test_the_guard_is_about_the_reference_not_the_per_run_comparison(self) -> None:
        """THE DISTINCTION, pinned end-to-end. The SAME zero the per-run comparison waves through
        (``TestTheZeroBaselineTrapIsReal``) is REFUSED by this guard. Two guards, two places: this
        one on the reference value, guard #2 on each run — and only THIS one can catch a vacuous
        baseline."""
        baseline = 0
        broken_run_total = 0
        # per-run comparison would call this baseline 'comparable' to a broken run (the DISEASE):
        assert broken_run_total == baseline
        # the reference guard refuses it outright (the CURE):
        with pytest.raises(SystemExit):
            self._guard()(baseline, cause_hint=_CAUSE_HINT, interpreter=_INTERPRETER)
