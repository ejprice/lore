"""The contract for ``scripts/wrong_builds.py`` — the committed attack harness must be RUNNABLE.

``wrong_builds.py`` grades a contract by BUILDING the wrong implementations it must reject, and
its output is a census: *N built · N killed · N survived*. A census is only worth reading if every
build in it was actually MEASURED — and nothing checked that, which is how ``WB19`` shipped a
mutation that had never parsed and was counted as a kill for as long as it existed (D13,
``coldaudit-44-1``, 2026-07-29).

⚠ **WHY THIS FILE LIVES IN ``scripts/`` (operator-ruled 2026-07-30).** ``scripts`` is a
``testpaths`` entry AND a ``scripts/typecheck.sh`` MEMBERS root, so this contract is gated on both
axes from birth — which is packet 44's whole thesis, and the alternative is a guard nobody runs.
It is also a tracked ``scripts/*.py``, so ``gated_ground.py``'s own LEG A and LEG B quantify over
it: this file is inside the invariant it helps defend.

Its sibling ``scripts/test_mutation_proof.py`` is the same idiom — a committed instrument gets a
committed contract.
"""

from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path

import pytest

# ``scripts/`` is not a package; the path insert must precede the sibling import, exactly as
# every other contract in this directory does it (test_gated_ground, test_mutation_proof, …).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gated_ground as gg  # noqa: E402  (path insert must precede the import)
import wrong_builds  # noqa: E402  (path insert must precede the import)


class TestTheCommittedWrongBuildsCanActuallyRun:
    """Every build in ``scripts/wrong_builds.py`` must LAND and PARSE against the instrument.

    ⚠ **THE CLASS THIS PINS, MEASURED (D13, ``coldaudit-44-1``, 2026-07-29).** ``WB19`` — the
    over-claiming clean render, the build ruling R9 was written to kill — shipped with an escaped
    quote inside a triple-quoted replacement. The text it installed ended in TWO quotes, so the
    patched module never parsed, the run collected ``1 error`` instead of the contract, and the
    census printed ``21 built · 20 killed``. **The kill was reported and had never been
    obtained.** The harness's own per-build guard fired correctly; nothing checked that a build
    was RUNNABLE at all, and a build that cannot run is a measurement nobody has.

    TWO failure modes, one pin, because they are the same defect at different times: a
    replacement that is not valid Python (the mutation cannot be graded) and an ANCHOR that no
    longer matches exactly once (the mutation cannot land, so the CORRECT build is graded and
    reads as a survivor). Both are silent in a census; both are one string comparison here.

    ⚠ **AND THE TRADE, STATED SO IT IS MET DELIBERATELY:** this pin couples the harness's anchors
    to the instrument they cut into, so a refactor of ``gated_ground.py`` that moves an anchored
    line reddens it. That is the intended direction — an attack harness whose anchors have rotted
    measures nothing while still printing a census — and the repair is to re-anchor the build,
    never to delete this pin. It runs no subprocess: it is string substitution and
    :func:`ast.parse`.
    """

    def test_every_committed_wrong_build_lands_exactly_once_and_parses(self) -> None:
        pristine = Path(gg.__file__).read_text(encoding="utf-8")
        assert wrong_builds.WRONG_BUILDS, (
            "the attack harness declares no builds at all, so this ∀ is vacuous and the census "
            "it guards would be a count of nothing"
        )
        broken: dict[str, str] = {}
        for name in sorted(wrong_builds.WRONG_BUILDS):
            try:
                patched = wrong_builds.apply(name, pristine)
            except SystemExit as anchor_failure:
                broken[name] = f"cannot LAND — {anchor_failure}"
                continue
            try:
                ast.parse(patched)
            except SyntaxError as syntax_failure:
                broken[name] = f"does not PARSE — {syntax_failure}"
        assert not broken, (
            f"{len(broken)} of {len(wrong_builds.WRONG_BUILDS)} committed wrong build(s) cannot "
            f"measure anything, so the census counts them without ever having graded them:\n"
            + "\n".join(f"  {name}: {why}" for name, why in sorted(broken.items()))
        )


# ===========================================================================
# INSTRUMENT H (finding #290) — the SHARING/extraction half of the fix, which
# ``test_harness_guards.py`` (the helper's OWN behaviour) cannot pin.
#
# adversary-eh's BLOCKER: the property *"``refuse_vacuous_baseline`` is the ONE
# implementation — ``wrong_builds.main`` SHARES it, not re-inlines it"* had NO RED
# HOME. A build that adds the correct shared helper AND keeps ``main``'s inline
# ``if not baseline: raise SystemExit`` (two copies of one policy, the #102/#120
# routing-not-sharing trap) passes every OTHER pin, green. These two pins are that
# missing home, per design §9.1 IDIOM 1 SHARING specialization:
#   * a ROUTING spy (main invokes the shared guard with the baseline it measured) —
#     the "delete-the-call → the covering path reddens" proof in spy form (delete the
#     call and the spy never fires); and
#   * an anti-duplication offender scan (no second inline vacuity guard) — because the
#     spy alone passes a build that routes AND keeps the inline copy.
# Neither alone is the sharing proof; together they are.
# ===========================================================================


class _SharedGuardWasCalled(Exception):
    """Distinctive signal the routing spy raises so the pin can prove ``main`` reached the
    SHARED ``refuse_vacuous_baseline`` (and with which baseline count), independent of how
    ``main`` imported it and short-circuiting ``main`` right at the guard call."""

    def __init__(self, measured_count: int) -> None:
        super().__init__(f"refuse_vacuous_baseline reached with measured_count={measured_count}")
        self.measured_count = measured_count


def _install_guard_spy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the SHARED ``refuse_vacuous_baseline`` with a spy, reaching every binding a
    builder might have made — ``import _harness_guards`` (patch the module attribute, which a
    call-time lookup reads) AND ``from _harness_guards import refuse_vacuous_baseline`` (patch
    the name bound on ``wrong_builds`` itself).

    RED at HEAD for the RIGHT reason: ``_harness_guards`` does not exist yet
    (``ModuleNotFoundError``), so ``main`` cannot route through a helper that has not been
    extracted — exactly the state this pin exists to move off.
    """
    guard_module = importlib.import_module("_harness_guards")

    def spy(measured_count: int, **_kwargs: object) -> None:
        raise _SharedGuardWasCalled(measured_count)

    monkeypatch.setattr(guard_module, "refuse_vacuous_baseline", spy, raising=True)
    if hasattr(wrong_builds, "refuse_vacuous_baseline"):
        monkeypatch.setattr(wrong_builds, "refuse_vacuous_baseline", spy, raising=True)


def _fake_scratch(tmp_path: Path) -> Path:
    """The minimal scratch ``main`` accepts before it computes a baseline: a ``.git``
    DIRECTORY (not a worktree file) and the instrument file it reads for pristine. Nothing
    here is mutated — ``run_contract`` is stubbed, so no subprocess and no real contract run.
    """
    (tmp_path / ".git").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "gated_ground.py").write_text("# pristine\n", encoding="utf-8")
    return tmp_path


class TestMainSharesTheVacuousBaselineGuard:
    """``wrong_builds.main`` ROUTES the vacuity decision through the shared guard.

    Proven by a routing spy driven through ``main``'s real baseline path. RED at HEAD:
    ``_harness_guards`` does not exist and ``main`` does not call it (it carries the inline
    copy). This is the delete-the-call mutation proof in spy form — delete ``main``'s call to
    ``refuse_vacuous_baseline`` and the spy never fires, so this pin reddens.
    """

    @pytest.mark.parametrize("baseline_count", [0, 315])
    def test_main_routes_the_measured_baseline_through_the_shared_guard(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, baseline_count: int
    ) -> None:
        """Drive ``main``'s baseline decision and prove it hands the SHARED guard the count it
        MEASURED — for a vacuous (0) AND a real (315) baseline (design §9.4 monoculture: a
        hardcoded ``0`` echo cannot match 315, and the 315 leg FORCES the unconditional
        ``refuse_vacuous_baseline(baseline, ...)`` form — a ``if not baseline: refuse(...)``
        half-extraction keeps the vacuity predicate inline and never calls the guard on 315).

        The spy raises, so ``main`` stops at the guard call; that the guard is REACHED with
        the right count is the routing proof.
        """
        _install_guard_spy(monkeypatch)
        monkeypatch.setattr(
            wrong_builds,
            "run_contract",
            lambda *_args, **_kwargs: (baseline_count, 0, 0, f"{baseline_count} collected"),
        )
        with pytest.raises(_SharedGuardWasCalled) as excinfo:
            wrong_builds.main(["--scratch", str(_fake_scratch(tmp_path))])
        assert excinfo.value.measured_count == baseline_count, (
            f"main reached the shared guard with measured_count={excinfo.value.measured_count} "
            f"but measured a baseline of {baseline_count} — it is not forwarding the count it "
            f"computed (a hardcoded value, not the baseline)"
        )


def _is_name_vacuity_test(test: ast.expr) -> bool:
    """``not <name>`` or ``<name> == 0`` — the shape of a test that fires when a measured
    count is empty (the HEAD inline guard is ``if not baseline:``).

    Deliberately does NOT match the legitimate raises around it, structurally rather than by
    a denylist: ``if not (scratch / ".git").is_dir():`` (operand is a Call, not a Name),
    ``if failed or errors:`` (a BoolOp), ``if unknown:`` (a truthiness test, not ``not``),
    ``if not (passed or failed or errors):`` (operand is a BoolOp) — none is ``not <name>`` /
    ``<name> == 0``.
    """
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return isinstance(test.operand, ast.Name)
    if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
        left, right = test.left, test.comparators[0]
        return (isinstance(left, ast.Name) and isinstance(right, ast.Constant) and right.value == 0) or (
            isinstance(right, ast.Name) and isinstance(left, ast.Constant) and left.value == 0
        )
    return False


def _inline_vacuity_guards(source_path: Path) -> dict[str, str]:
    """Every inline "the measurement is empty → raise" guard in ``source_path``, as
    ``{"file:line": test-dump}`` — the offender-enumeration shape of
    ``test_retry_seam._all_sdk_call_sites`` (derive the set from the AST, NAME each offender
    by ``file:line``, fail-closed), NOT a search for a fixed string.

    An offender is an ``if`` whose test is a vacuity test on a NAME
    (:func:`_is_name_vacuity_test`) and whose body raises — exactly the HEAD inline guard
    ``if not baseline: raise SystemExit(...)``.
    """
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    offenders: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not _is_name_vacuity_test(node.test):
            continue
        if any(isinstance(descendant, ast.Raise) for descendant in ast.walk(node)):
            offenders[f"{source_path.name}:{node.lineno}"] = ast.dump(node.test)
    return offenders


class TestNoSecondInlineVacuousBaselineGuard:
    """``wrong_builds.py`` must not re-implement the vacuity refusal inline once
    ``refuse_vacuous_baseline`` is the shared home — two copies of one policy is the
    #102/#120 routing-not-sharing trap, and it was adversary-eh's H BLOCKER (a correct helper
    + the KEPT inline copy passes every other pin, and the routing spy above passes a build
    that routes AND keeps the inline copy).

    RED at HEAD: ``main`` carries the inline ``if not baseline: raise SystemExit`` the fix
    extracts. GREEN once it routes through the shared guard instead.

    ⚠ BOUND (design §9.1, stated not hidden): the scan is pattern-keyed, so a differently
    shaped private copy (``if baseline < 1:``, ``if len(x) == 0:``) escapes it — the
    un-derivable tail INSTRUMENT 0's reach-attack owns. It catches the copy that EXISTS at
    HEAD and the natural two-copies build; it does not claim to catch every conceivable
    re-inlining. There is no allowlist today because ``wrong_builds.py`` has exactly one such
    site (the offender); a FUTURE legitimate ``not <name>: raise`` must be allowlisted with an
    evidence-backed reason or routed through a helper (allowlist-the-safe).
    """

    def test_wrong_builds_has_no_inline_vacuous_baseline_guard(self) -> None:
        offenders = _inline_vacuity_guards(Path(wrong_builds.__file__))
        assert not offenders, (
            "wrong_builds.py re-implements the vacuous-baseline refusal inline instead of "
            "routing through the shared _harness_guards.refuse_vacuous_baseline — two copies "
            "of one policy (finding #290 / #102). Offending site(s):\n"
            + "\n".join(f"  {where}: {test}" for where, test in sorted(offenders.items()))
        )
