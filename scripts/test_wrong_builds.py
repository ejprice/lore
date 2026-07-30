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
import os
import sys
from pathlib import Path

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
