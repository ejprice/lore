"""INSTRUMENT H (finding #290) — anti-vacuity on a COMPARISON's baseline, as the ONE shared guard.

Contract: ``scripts/test_harness_guards.py``. Design doc
``docs/plans/v2/design/2026-08-09-defect-class-prevention.md`` §INSTRUMENT H.

WHY THIS EXISTS. ``wrong_builds.py`` grades each mutation by comparing its collected total to a
BASELINE's total. Run through an interpreter with no pytest, the baseline collected 0 — and every
build then compared ``0 == 0``, failure-free, and was reported ``❗SURVIVED``. Three phantom
survivors against a contract that had never run; over the full set the census would have read
``21 survived`` = "this contract catches nothing", entirely an artifact of a missing pytest.

THE GENERALISATION (finding #290): *an anti-vacuity check on a COMPARISON's REFERENCE value is a
distinct guard from anti-vacuity on the things being compared, and it is the one that gets skipped.*
``wrong_builds`` already had per-run guards; it lacked a guard on the REFERENCE ITSELF. This is that
guard, extracted so any harness grading N runs against a baseline shares ONE answer to *"did the
baseline measure anything?"* — not a second inline copy per harness (the #102/#120 routing-not-
sharing trap).
"""

from __future__ import annotations


def refuse_vacuous_baseline(
    measured_count: int, *, cause_hint: str, interpreter: str
) -> None:
    """Raise a hard, DIAGNOSTIC failure when ``measured_count`` is zero; return ``None`` otherwise.

    A baseline/reference of zero measured NOTHING, so every later comparison against it is vacuous
    (``0 == 0`` reads as "comparable" and, with no failures, "survived"). This refuses that state
    LOUDLY — naming the likely cause and the child interpreter — never a silent pass. One collected
    item IS a measurement, so the refusal is keyed on ``== 0`` ("nothing measured"), not on "small".

    Args:
        measured_count: the number of items the reference run collected.
        cause_hint: the caller's description of the likely cause (a REUSABLE guard cannot hardcode
            any one caller's cause, so this is surfaced in the diagnostic).
        interpreter: the child interpreter the reference ran under — the most common cause of a
            zero baseline is an interpreter with no pytest, so the diagnostic echoes it.

    Raises:
        SystemExit: when ``measured_count == 0``. ``SystemExit`` (not a custom exception) preserves
            ``wrong_builds.main``'s exit-1 behaviour on extraction — the caller need not catch and
            convert (contract-eh Fork 1; a behaviour-preserving choice, ruled for this cycle).
    """
    if measured_count == 0:
        raise SystemExit(
            "the reference/baseline run collected NOTHING (0 items), so every build compared "
            "against it would read 0 == 0 as 'comparable' and, with no failures, as 'survived' — "
            f"the #290 phantom-survivor class. Likely cause: {cause_hint}. Child interpreter: "
            f"{interpreter}. A guard that compares two numbers must first know either number is a "
            "measurement; refusing to grade against a baseline that measured nothing."
        )
