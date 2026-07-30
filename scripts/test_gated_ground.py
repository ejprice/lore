"""CONTRACT for ``scripts/gated_ground.py`` — the DERIVED, PER-AXIS gated-ground invariant.

**WHAT THIS PINS, in one sentence:** every committed ``.py`` in this repository is either
registered with the type gate, or carries a pinned exemption, or is archived ground — and,
separately, every committed test-shaped file is registered with the execution gate under the
same three outs. Two legs, quantified over INPUTS (tracked files), never over gate sets.

**WHY PER-AXIS AND NOT BINARY — the single load-bearing design point.** The packet's own
sentence words the property as *"a committed ``.py`` outside every typecheck member AND
outside every ``testpaths`` entry"*. That is a **union**, and a union is green over a tree
whose ``scripts/`` is in ``testpaths`` while no type gate has ever read it, and whose
``skills/`` is a typecheck member while no pytest run has ever collected its tests. **Three
of the four historical instances of this class (#188, #233, #261) were HALF-gaps** — covered
on one axis, naked on the other. A guard implementing the packet's sentence literally is a
wrong build that ships green, and killing it is this contract's first job
(:class:`TestThePropertyIsPerAxisNotBinary`).

**THE READ-BOUNDARY, stated because this file was written blind to the implementation.**
Behavioural expectations here come from the ruled specification
(``REPORT-design-sidecar-44-1.md`` §Q3.1–§Q3.8 and its ``FU1 ANSWERS`` A/C/D, archived with
the packet-44 receipts). Repository FACTS — real member names, the real ``MEMBERS=(…)``
declaration shape, the real ``testpaths`` list, the real archived-receipts address — are read
LIVE from the configuration files at runtime so that no expectation here is a hand-copied
mirror. A mirrored config list is the stale-mirror hazard ``CLAUDE.md`` records against
``scratch_provenance.py::WORKSPACE_MEMBERS``, and this instrument exists to catch that class,
not to join it.

**⚠ FIXTURE REPOSITORIES ARE ``git init`` FROM EMPTY — NEVER A COPY OF THIS CHECKOUT.** This
work happens in a git WORKTREE, whose ``.git`` is a **FILE** naming the original repository's
absolute gitdir. A ``cp -a`` / ``scratch_copy.sh`` copy inherits that file, so ``git add`` in
the supposedly-isolated copy **mutates the real worktree's index**, silently — #140's poison
mode wearing git clothing. Every fixture in this file is therefore a fresh empty repository
built field by field by :class:`FixtureRepository`, which is also why every reader in the
contracted surface takes an explicit ``repo_root`` (§Q3.3 / FU1-C).

**THE RECURSION, AND HOW IT IS CLOSED (ruled by the lead; the mechanism, not the first design).**
This instrument lands in ``scripts/`` — a ``testpaths`` entry (LEG B ✓) which ruling **F1** also
made a plain ``MEMBERS`` typecheck root at debt zero (LEG A ✓). Left ungated it would be the
fifth instance of the class it exists to close, and the fix is a mechanism rather than a special
case: **a root covers ITSELF, component-wise, BEFORE any exemption is consulted**, so the tree
holding the instrument is covered by the same rule as every other tree.

⚠ **AN EARLIER DESIGN — a FROZEN ROSTER of ``scripts`` files derived live from one commit — IS
RETIRED (F1), and every mechanism belonging to it is DELETED**: no roster, no ``FROZEN_SHA``, no
``git ls-tree`` reader, no exemption row. Read the retirement as ruled: an enumeration of an OPEN
set whose staleness is silent is the shape that has defeated every instrument in this
repository's lesson table, so the debt was RESOLVED instead of exempted, and
:data:`gg.EXEMPTIONS` lands empty (:meth:`TestTheExemptionTableIsAnAllowlistOfTheSafe.
test_the_table_lands_EMPTY_and_the_emptiness_is_a_fact_about_the_TREE`).

**The guard contains no mention of its own path anywhere** — a build that hardcodes "except me"
is wrong build #2, killed by
:meth:`TestThisGuardIsItselfGated.test_the_guard_names_no_path_of_its_own_anywhere_in_its_source`.
Two consequences follow, and BOTH axes of each are pinned in :class:`TestThisGuardIsItselfGated`
and :class:`TestTheInstrumentIsSelfContained`: the instrument and this contract are inside a
``MEMBERS`` root *and* inside a ``testpaths`` entry (an earlier revision pinned the execution
half only — a HALF-gap in the contract against half-gaps), and the instrument imports the
standard library and nothing else so that it resolves with no ``MYPYPATH`` of its own.

**HOW TO READ A FAILURE HERE.** A red test in
:class:`TestTheRealRepositoryIsFullyGated` means the TREE grew ungated ground. A red test
anywhere else means the GUARD is wrong. That distinction is the whole reason the fixture
repositories exist: they exercise the guard against trees whose answer is known independently
of this repository's current state.

**WHAT REVISION 6 CHANGED, and why the change is STRUCTURAL rather than another pin.**
``adversary-44-gatedground-3`` built 21 wrong implementations against revision 5 and **6 passed
at 171/171**, because revision 5 had fixed the INSTANCES the previous adversary named and not the
QUANTIFIER: blindness-monotonicity was pinned for FIVE named doors, held for 6 of a derived 26,
and a build honouring exactly those five served **17 false clears** — broken states rendering
bytes identical to a healthy tree. Its dual was unpinned outright: a build serving one finding
with ``is_clean=True``, ``exit_code=0`` and the clean sentence passed every pin. So revision 6
does three things, in this order of preference:

1. **Makes the inconsistency UNREPRESENTABLE.** ``is_clean``, ``exit_code`` and ``render()`` are
   derived from ONE classifier, :attr:`gg.Verdict.state`; the exit code IS that state's enum
   value, so there is no second place for it to disagree; and a verdict carrying findings AND
   blind sources — the incoherent cell — cannot be constructed at all
   (:class:`TestTheServedSurfaceIsOneDerivation`).
2. **Quantifies over a failure set DERIVED FROM THE INSTRUMENT, never a list written here.**
   Every refusal carries a stable door identity; this file AST-reads the door set out of the
   instrument's own source and demands a CONSTRUCTED broken state for each one, diffed BOTH ways
   (:class:`TestTheDerivedFailureSetIsFullyProbed`). A door added without a state is RED.
3. **Pins what could not be closed.** The bounds that remain are stated in
   :data:`gg.STATED_BOUNDS` with named re-open triggers, and this file asserts each is true of
   the mechanism it describes rather than merely present as prose.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import json
import os
import re
import shlex
import subprocess
import sys
import types
from collections.abc import Callable, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

import pytest

# ``scripts/`` is not a package; the path insert must precede the sibling import, exactly as
# every other contract in this directory does it (test_token_survey, test_snapshot_gc, …).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gated_ground as gg  # noqa: E402  (path insert must precede the import)

# ---------------------------------------------------------------------------
# Anchors — every one either derived from the tree or citing the ruling that fixes it.
# ---------------------------------------------------------------------------

#: This checkout. ``registration_sites.py``'s own idiom; resolves correctly inside a git
#: worktree, which is where packet 44 is being built.
REPO_ROOT = Path(__file__).resolve().parent.parent

#: §Q3.4 / FU1-A, both SUPERSEDED: the operator ruled ``scripts/`` to type-debt ZERO and made it
#: a plain typecheck root, so the table lands EMPTY and the roster mechanism is retired.

#: §Q3.2: the lore-index axis is a NAMED BOUND, not a covered case; its re-open trigger is
#: #260 landing.
LORE_INDEX_BOUND_FINDING = "#260"

#: §Q3.5 / §Q3.2: the bounds and threat model the instrument must STATE. Identifiers, not
#: prose — the contract requires the bound to exist and to appear in the module docstring;
#: the builder writes the words.
REQUIRED_BOUND_IDENTIFIERS = frozenset(
    {
        # "This proves REGISTRATION in the gates' config; it does not prove mypy or pytest
        # ran, or passed."
        "registration-not-execution",
        # LEG B quantifies over test-shaped files and conftest only. Execution coverage of
        # ordinary library modules is a coverage-measurement problem this does not claim.
        "execution-axis-covers-test-shaped-files-only",
        # A file full of asserts named outside pytest's collection convention is invisible
        # to pytest EVERYWHERE — a different defect class.
        "collection-convention",
        # #233/#260's third direction: lore's index is a gate this instrument does not model.
        "lore-index-axis",
        # LEG B models [tool.pytest.ini_options]; collection hooks in a conftest.py
        # (collect_ignore / collect_ignore_glob) are NOT modelled — a reader must meet that.
        "conftest-collection-hooks",
        # Untracked ground is out of scope BY CONSTRUCTION. Pinned as behaviour since r1, but
        # never STATED, so no reader of the guard met it.
        "untracked-ground",
        # ⚠ R6 — THIS BOUND'S RE-OPEN TRIGGER FIRED THE DAY IT WAS WRITTEN: the derived
        # shellcheck leg is live in typecheck.sh, so `.sh` IS gated on the type axis. The bound
        # must now teach CLOSURE there and an open hole only on the execution axis. A bound
        # describing a hole already closed is the natural-language defect inverted — false in
        # the safe direction is still false. Its CONTENT is pinned against the mechanism by
        # TestEveryStatedBoundIsTrueOfItsMechanism — r5 wrote this correction as a comment and
        # nothing enforced it, which is how its SIBLING one entry down stayed false.
        "file-types-modelled",
        # ⚠ REVISION 6, and the sharpest of the three: a gate's configuration is the file the
        # TOOL reads, not the file this guard reads. A committed `mypy.ini` OUTRANKS
        # `pyproject.toml` in mypy's own search order, so `exclude`d roots or a global
        # `ignore_errors` would switch LEG A off while the guard served bytes identical to a
        # healthy tree — #107 verbatim, measured against the installed mypy's own constants.
        "gate-configuration-precedence",
        # REVISION 6 / R10: the collector answer is memoised, and the memo's INVALIDATION is
        # part of the contract — a cache serving a stale healthy answer is itself a false clear.
        "collector-memoisation",
        # REVISION 6: LEG B's test-shapedness reproduces pytest's own matcher, whose POSIX
        # branch is the only one ported. Three surveys recorded `fnmatch` as an exact
        # replacement without opening pytest's matcher; it is not one.
        "collection-pattern-platform",
    }
)

#: §Q3.7: the message's first line. Pinned because the hostile-path forgery test counts
#: header lines, and a header nobody can recognise is a header nobody can forge-check.
_MESSAGE_HEADER = "UNGATED GROUND"

#: Scope spellings that widen to the whole repository, or escape it. **ONE constant shared by
#: BOTH axes' pins**, because they used to carry DIFFERENT hand-written sets: ``./`` was pinned on
#: the testpaths axis and not on the MEMBERS axis, and measured,
#: ``MEMBERS=(loremaster ./)`` walked through a build that passed all 171 pins, marked every
#: tracked file COVERED and served bytes identical to a healthy tree. Two lists that must agree
#: are one list; the divergence is not a fixture detail, it is the false clear.
#:
#: The entries are chosen to exercise the DERIVED property rather than to enumerate spellings:
#: ``PurePosixPath`` normalises ``.``, ``./`` and ``./.`` to ``parts == ()``, so a guard keying on
#: a denylist of literal spellings fails here while one keying on ``parts`` passes. ``docs/..``
#: escapes by traversal without being absolute, and ``""``/``" "`` are the blank forms.
WHOLE_TREE_SCOPE_SPELLINGS: tuple[str, ...] = (
    ".",
    "./",
    "./.",
    "..",
    "docs/..",
    "/",
    "/home",
    "",
    " ",
)

#: §Q3.7: substrings the failure message must carry regardless of axis. Each exists because
#: its absence would make the message promise a check the assertion does not perform.
MESSAGE_MUST_MENTION_REGISTRATION = "registration"
MESSAGE_MUST_DISCLAIM_EXECUTION = "does not prove"
#: ⚠ R4 — THESE REPLACE `finding number` / `re-open trigger`, WHICH WERE A FALSE GATE IN THE
#: INSTRUMENT'S OWN MOUTH. Under F1 there is no exemption mechanism, so a message offering "add a
#: pinned exemption row" named a route the system does not perform — this repo's false-gate law
#: turned inward. The sanctioned outs are now: gate-cover it, or escalate.
MESSAGE_MUST_DEMAND_ESCALATION = "escalate"
MESSAGE_MUST_DENY_AN_EXEMPTION_MECHANISM = "there is no exemption mechanism"
MESSAGE_MUST_REFUSE_RECEIPTS_WIDENING = "do not widen the receipts class"

#: A realistic module body. Not ``x = 1``: fixture files stand in for real committed
#: instruments, and a body that reads like one keeps the fixture legible when it fails.
_MODULE_BODY = '''"""A committed instrument, standing in for the real thing."""


def answer() -> int:
    """Return the value this module exists to compute."""
    return 42
'''

_TEST_BODY = '''"""A committed test, standing in for the real thing."""


def test_the_instrument_answers() -> None:
    assert True
'''


# ---------------------------------------------------------------------------
# The fixture repository builder
# ---------------------------------------------------------------------------


class FixtureRepository:
    """A throwaway git repository shaped like this workspace, built field by field.

    ⚠ **NEVER a copy of this checkout** — see the module docstring. ``git init`` from empty,
    ``git add`` (no commit: ``git ls-files`` reads the INDEX, so staging is sufficient and
    needs no committer identity).

    Nothing here defaults a value the guard can branch on: every call site states its
    ``testpaths``, its workspace members and its ruff exclusions explicitly. A fixture
    factory that defaults a branched-on parameter MANUFACTURES a blind spot — the repo has
    receipts (``_brief()``'s ``name="project"`` default, which made every render fixture test
    the one value for which the served prose happened to be true).
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=root, check=True)

    # -- rendering -------------------------------------------------------

    @staticmethod
    def render_members_line(roots: Sequence[str]) -> str:
        """The ``MEMBERS=(…)`` declaration, rendered the way the real runner writes it.

        Pinned against the live ``scripts/typecheck.sh`` by
        :meth:`TestConfigReadersComeFromTheRealFiles.test_fixture_members_line_matches_the_real_runner`
        — so if the real runner ever changes the shape of its declaration, these fixtures
        stop being representative LOUDLY rather than silently.
        """
        # shlex.quote is the exact mirror of the shlex.split the parser must use: a root with
        # no shell-unsafe character renders unchanged (so this still reproduces the real
        # runner's line byte-for-byte), and one containing a space renders QUOTED — which is
        # the case `str.split` gets wrong. Measured: shlex.split('a "docs/my eval" b') is three
        # tokens; str.split is four.
        return f"MEMBERS=({' '.join(shlex.quote(root) for root in roots)})"

    # -- writers ---------------------------------------------------------

    def write_typecheck_runner(
        self,
        *,
        members: Sequence[str] | None,
        include_decoy_comment: bool,
    ) -> None:
        """Write ``scripts/typecheck.sh``.

        ``members=None`` writes a runner with NO declaration at all — the blind-guard case.
        ``include_decoy_comment`` puts a ``MEMBERS=(…)`` mention inside a comment, which the
        declaration parser must not mistake for the declaration.
        """
        lines = [
            "#!/usr/bin/env bash",
            "# Canonical type-check for this fixture workspace.",
            "set -uo pipefail",
            'cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/.."',
        ]
        if include_decoy_comment:
            lines.append("# The MEMBERS=(decoy) mention below is prose, not the declaration.")
        if members is not None:
            lines.append(self.render_members_line(members))
        lines += [
            "status=0",
            'for member in "${MEMBERS[@]}"; do uv run mypy "${member}" || status=1; done',
            'exit "${status}"',
        ]
        runner = self.root / "scripts" / "typecheck.sh"
        runner.parent.mkdir(parents=True, exist_ok=True)
        runner.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def write_pyproject(
        self,
        *,
        testpaths: Sequence[str] | None,
        workspace_members: Sequence[str],
        ruff_extend_exclude: Sequence[str],
        python_files: Sequence[str] | None,
        pytest_ini_extra: dict[str, object] | None,
        mypy_exclude: Sequence[str] | None,
        mypy_table_extra: dict[str, object] | None,
        mypy_overrides: Sequence[dict[str, object]],
        omit_pytest_table: bool,
    ) -> None:
        """Write ``pyproject.toml``. Lists are rendered as TOML arrays via ``json.dumps``
        (JSON string arrays are valid TOML arrays), so the fixture is parsed back by
        ``tomllib`` — the same parser production reads with."""
        blocks = [
            '[project]\nname = "fixture-workspace"\nversion = "0.0.0"\n',
            f"[tool.uv.workspace]\nmembers = {json.dumps(list(workspace_members))}\n",
            f"[tool.ruff]\nextend-exclude = {json.dumps(list(ruff_extend_exclude))}\n",
        ]
        mypy_lines = ['[tool.mypy]\npython_version = "3.14"\nstrict = true']
        if mypy_exclude is not None:
            mypy_lines.append(f"exclude = {json.dumps(list(mypy_exclude))}")
        for key, value in (mypy_table_extra or {}).items():
            mypy_lines.append(f"{key} = {json.dumps(value)}")
        blocks.append("\n".join(mypy_lines) + "\n")
        for override in mypy_overrides:
            rendered = "\n".join(f"{key} = {json.dumps(value)}" for key, value in override.items())
            blocks.append(f"[[tool.mypy.overrides]]\n{rendered}\n")
        if not omit_pytest_table:
            extra = dict(pytest_ini_extra or {})
            pytest_lines = ["[tool.pytest.ini_options]"]
            if "asyncio_mode" not in extra:
                pytest_lines.append('asyncio_mode = "auto"')
            if testpaths is not None:
                pytest_lines.append(f"testpaths = {json.dumps(list(testpaths))}")
            if python_files is not None:
                pytest_lines.append(f"python_files = {json.dumps(list(python_files))}")
            for key, value in extra.items():
                pytest_lines.append(f"{key} = {json.dumps(value)}")
            blocks.append("\n".join(pytest_lines) + "\n")
        (self.root / "pyproject.toml").write_text("\n".join(blocks), encoding="utf-8")

    def add_python_file(self, relative_path: str, *, body: str = _MODULE_BODY) -> str:
        """Create a ``.py`` at ``relative_path`` and return the path as git will report it."""
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        return relative_path

    def add_raw_file(self, relative_path: str, *, body: str = "not python\n") -> str:
        """Create a NON-``.py`` file. Used for the ``.py``-substring hazard: a guard testing
        ``".py" in name`` rather than ``name.endswith(".py")`` invents a finding for
        ``notes.py.txt``, and a false positive is how a gate gets switched off."""
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        return relative_path

    def add_untracked_python_file(self, relative_path: str) -> str:
        """Create a ``.py`` that will NOT be staged — untracked ground is out of scope."""
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_MODULE_BODY, encoding="utf-8")
        return relative_path

    def stage(self, *, exclude: Sequence[str] = ()) -> None:
        """Stage everything except ``exclude``, then COMMIT.

        The commit is kept after the frozen roster's retirement because a fixture repository
        with a real commit is the realistic shape, and ``head_sha`` remains useful for a probe.
        """
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True, capture_output=True)
        for path in exclude:
            subprocess.run(
                ["git", "rm", "--cached", "-q", "--", path],
                cwd=self.root,
                check=True,
                capture_output=True,
            )
        subprocess.run(
            ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
             "commit", "-q", "-m", "fixture"],
            cwd=self.root,
            check=True,
            capture_output=True,
        )

    @property
    def head_sha(self) -> str:
        """This fixture repository's own HEAD."""
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True
        ).stdout.strip()


def _mypy_override(module: Sequence[str], **settings: object) -> dict[str, object]:
    """One ``[[tool.mypy.overrides]]`` block, shaped like the real ones in this repo."""
    return {"module": list(module), **settings}


# ---------------------------------------------------------------------------
# The reusable, ∀-over-INPUTS accounting helper (the quantifier law, mechanised)
# ---------------------------------------------------------------------------


def assert_every_tracked_file_is_accounted_for(
    repo_root: Path,
    *,
    exemptions: Sequence[gg.Exemption],
) -> list[gg.FileVerdict]:
    """Every tracked ``.py`` has EXACTLY ONE fate per axis, and every UNGATED fate is
    REPORTED. Applied in every case in this suite, not in one bespoke test.

    **This is quantified over INPUTS and conditioned on no cause.** PR93's six pins all said
    *"no silent drop WHEN SUPPLY FAILS"*; the rewrite dropped an input through the emission
    plumbing with supply fine, totals conserved and keys unique, and every pin stayed green.
    So the question asked here is never *"did the exemption logic behave"* but *"where did
    each of the N tracked files GO"* — a file can vanish from a report through doors nobody
    has imagined, and this helper does not care which door.

    Returns the verdicts so a caller can make its own, sharper assertion on top.
    """
    tracked = gg.tracked_python_files(repo_root)
    verdicts = gg.classify(repo_root, exemptions=exemptions)

    verdict_paths = [verdict.path for verdict in verdicts]
    assert len(verdict_paths) == len(set(verdict_paths)), (
        f"a tracked file was classified twice, so a count over verdicts is not a count over "
        f"files: {sorted({p for p in verdict_paths if verdict_paths.count(p) > 1})}"
    )
    assert set(verdict_paths) == set(tracked), (
        f"classification is not total over tracked .py.\n"
        f"  tracked but unclassified (VANISHED — the PR93 shape): "
        f"{sorted(set(tracked) - set(verdict_paths))}\n"
        f"  classified but not tracked (INVENTED): {sorted(set(verdict_paths) - set(tracked))}"
    )

    for verdict in verdicts:
        assert set(verdict.fates) == set(gg.GateAxis), (
            f"{verdict.path} carries fates for {sorted(a.name for a in verdict.fates)}, not for "
            f"every axis — an unjudged axis is an axis nothing guards"
        )
        for axis, fate in verdict.fates.items():
            assert isinstance(fate, gg.Fate), f"{verdict.path} on {axis.name}: {fate!r} is not a Fate"
        assert verdict.fates[gg.GateAxis.TYPES] is not gg.Fate.NOT_APPLICABLE, (
            f"{verdict.path} is NOT_APPLICABLE on the types axis; every committed .py is "
            f"type-gateable, so this fate would be a silent third exemption class"
        )

    findings = findings_of(repo_root, exemptions=exemptions)
    reported = {(finding.path, finding.axis) for finding in findings}
    ungated = {
        (verdict.path, axis)
        for verdict in verdicts
        for axis, fate in verdict.fates.items()
        if fate is gg.Fate.UNGATED
    }
    assert reported == ungated, (
        f"the report and the classification disagree, so a file can be UNGATED and unreported.\n"
        f"  classified UNGATED but not reported: {sorted((p, a.name) for p, a in ungated - reported)}\n"
        f"  reported but not classified UNGATED: {sorted((p, a.name) for p, a in reported - ungated)}"
    )
    return verdicts


def _mypy_declared_configuration_filenames() -> tuple[str, ...]:
    """mypy's OWN configuration search order, read out of the installed ``mypy.defaults``.

    ``CONFIG_NAMES + SHARED_CONFIG_NAMES``, in that order, is exactly what
    ``mypy.config_parser._find_config_file`` iterates, taking the FIRST that parses. Read rather
    than restated: this is the constant whose meaning #107 turned on, and a hand-copied order is a
    second copy of a vendor's decision.
    """
    from mypy import defaults

    return tuple(defaults.CONFIG_NAMES) + tuple(defaults.SHARED_CONFIG_NAMES)


def _pytest_declared_configuration_filenames() -> tuple[str, ...]:
    """pytest's OWN configuration search order, read out of ``locate_config``'s source.

    The list is a LOCAL inside the function, so there is no constant to import; the honest read is
    the source. Private API and an AST literal, deliberately — the alternative is restating four
    names that outrank ``pyproject.toml`` and hoping the next pytest release agrees.
    """
    import textwrap

    from _pytest.config.findpaths import locate_config

    source = textwrap.dedent(inspect.getsource(locate_config))
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "config_names" for target in node.targets
        ):
            names = ast.literal_eval(node.value)
            return tuple(str(name) for name in names)
    raise AssertionError(
        "locate_config no longer declares a `config_names` list, so this derivation cannot see "
        "pytest's search order — do not read any precedence verdict below it"
    )


def shadowing_configuration_filenames() -> tuple[str, ...]:
    """Every configuration filename that OUTRANKS the manifest for either gate tool.

    DERIVED from the two tools' own declared orders, not written down here: a name that appears
    BEFORE ``pyproject.toml`` in mypy's or pytest's search list is a file the tool reads INSTEAD of
    the one this guard models. That is #107's exact shape — a declaration the tool does not
    execute — and it is measurable rather than arguable: a committed ``mypy.ini`` carrying
    ``exclude`` switches LEG A off while the guard serves bytes identical to a healthy tree.

    Names AFTER the manifest are lower precedence and therefore harmless *as long as the manifest
    is itself accepted*, which the guard guarantees by refusing when the modelled table is absent.
    """
    shadowing: list[str] = []
    for order in (
        _mypy_declared_configuration_filenames(),
        _pytest_declared_configuration_filenames(),
    ):
        assert gg.MANIFEST_RELATIVE_PATH in order, (
            f"{gg.MANIFEST_RELATIVE_PATH} is not in {order} — this guard models a file the tool "
            f"does not even consult, which is a bigger problem than precedence"
        )
        for name in order:
            if name == gg.MANIFEST_RELATIVE_PATH:
                break
            if name not in shadowing:
                shadowing.append(name)
    assert shadowing, (
        "no filename outranks the manifest in either tool's order, which contradicts both "
        "installed sources — the derivation is broken, not the world"
    )
    return tuple(shadowing)


def _pytest_declared_default_patterns() -> list[str]:
    """Pytest's OWN declared ``python_files`` default, read from pytest at test time.

    ``_pytest.python.pytest_addoption`` declares ``default=["test_*.py", "*_test.py"]``; this
    reads the value out of the parser rather than restating it, so the check is a DERIVATION
    and not a second copy of the thing it is checking. Private API, deliberately: the public
    ``Config.getini`` requires a parsed configuration, which would make the answer depend on
    whatever directory the suite happens to run from.
    """
    from _pytest.config import get_config

    inidict = get_config([])._parser._inidict
    return [str(pattern) for pattern in inidict["python_files"][2]]


def findings_of(repo_root: Path, *, exemptions: Sequence[gg.Exemption] = ()) -> list[gg.UngatedFile]:
    """The findings of a verdict, for the pins that only care about those.

    ``ungated_ground`` returns a :class:`gg.Verdict`, not a list, precisely so a blind state
    cannot be served as a clean one (:class:`TestBlindnessIsMonotoneToTheServedSurface`). This
    helper keeps that design change from obscuring the pins that are about findings.
    """
    return list(gg.ungated_ground(repo_root, exemptions=exemptions).findings)


def fates_of(verdicts: Sequence[gg.FileVerdict], path: str) -> dict[gg.GateAxis, gg.Fate]:
    """The per-axis fates of one path, by identity — never by index or count."""
    for verdict in verdicts:
        if verdict.path == path:
            return dict(verdict.fates)
    raise AssertionError(f"{path} has no verdict at all, which the accounting helper should have caught")


def _is_module_function(module: types.ModuleType, candidate: object) -> bool:
    """Is ``candidate`` a function DEFINED IN ``module``, rather than one it imported?

    The distinction matters for any ∀ over a module's public surface: a re-exported stdlib
    function would otherwise be judged as part of the instrument's contract.
    """
    return isinstance(candidate, types.FunctionType) and candidate.__module__ == module.__name__


def _row_is_load_bearing(
    repo_root: Path, row: gg.Exemption, *, table: Sequence[gg.Exemption]
) -> bool:
    """Does deleting ``row`` from ``table`` make a finding appear under its root, on its axis?

    ONE predicate, called from three places: the ∀ over the SHIPPED table (vacuous while that
    table is empty), a fixture table holding one live row and one dead one (which is what proves
    the predicate discriminates at all), and the precedence pin. Written as a helper rather than
    inlined three times precisely because the call sites must agree — a second copy is how the
    vacuous loop would inherit a predicate nothing had ever exercised.
    """
    without = tuple(other for other in table if other is not row)
    findings = findings_of(repo_root, exemptions=without)
    return any(
        finding.axis is row.axis and gg.is_under(finding.path, row.root) for finding in findings
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def workspace_shaped_repository(tmp_path: Path) -> FixtureRepository:
    """A repository shaped like this workspace, holding one file per (axis, fate) cell.

    Deliberately NOT small-N and NOT a parameter monoculture: every cell of the
    axis × fate grid is occupied by a DIFFERENT file at a DIFFERENT path, so ``len()`` and
    ``sum()`` can never coincide and no wrong build can pass by collapsing categories.
    """
    repository = FixtureRepository(tmp_path)
    repository.write_typecheck_runner(
        members=["lorerunes", "loremaster", "skills", "docs/eval"],
        include_decoy_comment=True,
    )
    repository.write_pyproject(
        testpaths=["loremaster/tests", "scripts", "docs/eval", "skills/lore-deploy/tests"],
        workspace_members=["lorerunes", "loremaster"],
        ruff_extend_exclude=["scratchpad", "docs/plans/v2/receipts"],
        python_files=None,
        pytest_ini_extra=None,
        mypy_exclude=None,
        mypy_table_extra=None,
        mypy_overrides=[_mypy_override(["kubernetes", "kubernetes.*"], ignore_missing_imports=True)],
        omit_pytest_table=False,
    )
    # covered on both axes
    repository.add_python_file("loremaster/tests/test_store_lease.py", body=_TEST_BODY)
    # covered on types; execution not applicable (not test-shaped)
    repository.add_python_file("lorerunes/blankness.py")
    repository.add_python_file("docs/eval/smoke_p8b.py")
    # covered on both — a skill tree the config wave DID register
    repository.add_python_file("skills/lore-deploy/tests/test_port_probe.py", body=_TEST_BODY)
    # types covered by the `skills` root, execution UNGATED — the NEXT skill, which the
    # config wave's per-skill testpaths entries do not reach
    repository.add_python_file("skills/otherskill/tests/test_workspace_probe.py", body=_TEST_BODY)
    # ⚠ THESE TWO ARE UNGATED ON TYPES, AND THE COMMENTS THAT USED TO SIT HERE SAID "exempt by
    # the pinned table" — describing the OPPOSITE of the fate this file's own
    # test_each_named_fate_is_forced_by_a_fixture asserts. F1 deleted the table; every call site
    # passes exemptions=(). A fixture comment contradicting the fixture is how a reader is taught
    # a mechanism that no longer exists.
    repository.add_python_file("scripts/registration_sites.py")
    # test-shaped and inside a `scripts` testpaths entry: UNGATED on types, COVERED on execution
    repository.add_python_file("scripts/test_registration_sites.py", body=_TEST_BODY)
    # SIBLING PREFIX of both a gate root and the exemption root — must be neither
    repository.add_python_file("scripts_extra/promotion_helper.py")
    # ONE FILE PER MEMBERSHIP CALL SITE. `is_under` has a 12-row matrix, but a helper pinned
    # once and CALLED FOUR TIMES is pinned at one site: `str.startswith` at the typecheck-root,
    # testpath or receipts site passed the whole contract until these landed. Quantifier law —
    # pin the property at EVERY site, not at the definition.
    repository.add_python_file("docs/evaluation/harness.py")  # sibling of the docs/eval ROOT
    # sibling of a TESTPATH
    repository.add_python_file("loremaster/tests_extra/test_probe.py", body=_TEST_BODY)
    repository.add_python_file("skills/test_workspace_probe.py", body=_TEST_BODY)  # ANCESTOR of a testpath
    repository.add_python_file("docs/plans/v2/receipts_live/promoted_tool.py")  # sibling of the RECEIPTS root
    # P-2: TEST-SHAPED sibling of the receipts root. The non-test sibling above discriminates
    # the receipts site on TYPES only, so a build using startswith there on EXECUTION survived.
    repository.add_python_file(
        "docs/plans/v2/receipts_live/test_promoted_tool.py", body=_TEST_BODY
    )
    # REPOSITORY-ROOT-LEVEL committed Python. No fixture had any, and a stray root-level
    # probe or conftest is the single most likely way real ungated ground appears.
    repository.add_python_file("release_probe.py")
    repository.add_python_file("conftest.py", body=_TEST_BODY)
    # NOT Python, despite containing ".py"
    repository.add_raw_file("docs/consult/notes.py.txt")
    # archived receipts — exempt on both axes
    repository.add_python_file("docs/plans/v2/receipts/2026-07-20-probes/probe_budget.py")
    repository.add_python_file(
        "docs/plans/v2/receipts/2026-07-28-packet11ib/test_grade.py", body=_TEST_BODY
    )
    # live ground under neither gate
    repository.add_python_file("docs/consult/coherence_check.py")
    # a conftest outside every testpath — collected by pytest wherever it sits, and invisible
    # to the execution gate here
    repository.add_python_file("docs/consult/conftest.py", body=_TEST_BODY)
    # the OTHER default python_files pattern
    repository.add_python_file("tools/promotion_test.py", body=_TEST_BODY)
    # untracked ground is out of the threat model BY CONSTRUCTION
    repository.add_untracked_python_file("scratchpad/session_debris.py")
    repository.stage(exclude=["scratchpad/session_debris.py"])
    return repository


@pytest.fixture()
def half_gapped_repository(tmp_path: Path) -> FixtureRepository:
    """The two HALF-gaps, and nothing else — the executioner of the binary property.

    ``docs/eval`` is in ``testpaths`` and in no typecheck root (#238/#261's real shape);
    ``skills`` is a typecheck root and in no ``testpaths`` entry (#280's real shape). Under
    the packet's literal union property BOTH are "gated" and this repository reports zero
    findings, which is exactly the wrong build this fixture exists to kill.
    """
    repository = FixtureRepository(tmp_path)
    repository.write_typecheck_runner(members=["loremaster", "skills"], include_decoy_comment=False)
    repository.write_pyproject(
        testpaths=["loremaster/tests", "docs/eval"],
        workspace_members=["loremaster"],
        ruff_extend_exclude=["scratchpad", "docs/plans/v2/receipts"],
        python_files=None,
        pytest_ini_extra=None,
        mypy_exclude=None,
        mypy_table_extra=None,
        mypy_overrides=[],
        omit_pytest_table=False,
    )
    repository.add_python_file("loremaster/tests/test_store_lease.py", body=_TEST_BODY)
    repository.add_python_file("docs/plans/v2/receipts/2026-07-20-probes/probe_budget.py")
    repository.add_python_file("docs/eval/smoke_p8b.py")  # in testpaths, no type gate
    repository.add_python_file("skills/lore-deploy/tests/test_port_probe.py", body=_TEST_BODY)
    repository.stage()
    return repository


@pytest.fixture()
def distinctly_configured_repository(tmp_path: Path) -> FixtureRepository:
    """A repository where EVERY parsed value differs from this checkout's.

    Built for one job: a reader that ignores ``repo_root`` and answers about the real tree
    must be caught on every reader, not only on the ones whose fixture value happens to
    differ. Coincidence is not discrimination.
    """
    repository = FixtureRepository(tmp_path)
    repository.write_typecheck_runner(members=["loremaster", "skills"], include_decoy_comment=False)
    repository.write_pyproject(
        testpaths=["loremaster/tests"],
        workspace_members=["loremaster"],
        ruff_extend_exclude=["scratchpad", "docs/plans/v2/receipts", "dist"],
        python_files=["check_*.py"],
        pytest_ini_extra=None,
        mypy_exclude=None,
        mypy_table_extra=None,
        mypy_overrides=[],
        omit_pytest_table=False,
    )
    repository.add_python_file("loremaster/tests/check_store_lease.py", body=_TEST_BODY)
    repository.add_python_file("skills/lore-deploy/scripts/port_probe.py")
    repository.add_python_file("docs/plans/v2/receipts/2026-07-20-probes/probe_budget.py")
    repository.stage()
    return repository


def _repository_beside(tmp_path: Path, name: str, **perturbations: object) -> FixtureRepository:
    """A second fixture repository under ``tmp_path``, in its own created directory.

    ``FixtureRepository`` runs ``git init`` with ``cwd`` set to the root it is handed, so a path
    that does not exist yet fails with ``FileNotFoundError`` — which is how three pins in this
    file's first revision-6 draft failed for a FIXTURE reason rather than a guard reason, and one
    of them was the healthy CONTROL that every byte-diff is measured against. A control that
    cannot be built reads as 26 broken states; the guard was fine. One helper, so the mkdir cannot
    be forgotten at the fourth call site.
    """
    root = tmp_path / name
    root.mkdir(parents=True, exist_ok=True)
    return _minimal_repository(root, **perturbations)  # type: ignore[arg-type]


def _minimal_repository(
    tmp_path: Path,
    *,
    members: Sequence[str] | None = ("loremaster",),
    testpaths: Sequence[str] | None = ("loremaster/tests",),
    ruff_extend_exclude: Sequence[str] = ("scratchpad", "docs/plans/v2/receipts"),
    python_files: Sequence[str] | None = None,
    pytest_ini_extra: dict[str, object] | None = None,
    mypy_exclude: Sequence[str] | None = None,
    mypy_table_extra: dict[str, object] | None = None,
    mypy_overrides: Sequence[dict[str, object]] = (),
    omit_pytest_table: bool = False,
    omit_typecheck_runner: bool = False,
    extra_files: Sequence[str] = (),
) -> FixtureRepository:
    """The smallest repository the guard will accept, plus whatever a case perturbs.

    Every perturbation axis is a keyword here so a case states exactly the one thing it
    changes; the defaults are the HEALTHY values, which makes each blind-guard case a
    single-variable experiment against a known-good control.
    """
    repository = FixtureRepository(tmp_path)
    if not omit_typecheck_runner:
        repository.write_typecheck_runner(members=members, include_decoy_comment=False)
    repository.write_pyproject(
        testpaths=testpaths,
        workspace_members=["loremaster"],
        ruff_extend_exclude=ruff_extend_exclude,
        python_files=python_files,
        pytest_ini_extra=pytest_ini_extra,
        mypy_exclude=mypy_exclude,
        mypy_table_extra=mypy_table_extra,
        mypy_overrides=mypy_overrides,
        omit_pytest_table=omit_pytest_table,
    )
    repository.add_python_file("loremaster/tests/test_store_lease.py", body=_TEST_BODY)
    repository.add_python_file("loremaster/store/lease.py")
    repository.add_python_file("docs/plans/v2/receipts/2026-07-20-probes/probe_budget.py")
    for path in extra_files:
        is_test = Path(path).name.startswith(("test_", "check_")) or Path(path).name == "conftest.py"
        repository.add_python_file(path, body=_TEST_BODY if is_test else _MODULE_BODY)
    repository.stage()
    return repository


# ---------------------------------------------------------------------------
# 1. The readers come from the real files, and they honour repo_root
# ---------------------------------------------------------------------------


class TestConfigReadersComeFromTheRealFiles:
    """The inputs are PARSED from the configuration the gates actually execute — never
    mirrored. §Q3.3."""

    def test_typecheck_roots_are_the_roots_the_canonical_runner_declares(self) -> None:
        roots = gg.typecheck_roots(REPO_ROOT)

        # Derived, not asserted against a copied list: the runner's own declaration line must
        # be reproducible from what the reader returned.
        declaration = FixtureRepository.render_members_line(roots)
        runner_text = (REPO_ROOT / "scripts" / "typecheck.sh").read_text(encoding="utf-8")
        assert declaration in runner_text.splitlines(), (
            f"the reader returned {roots!r}, which does not reconstruct any line of the real "
            f"runner — the parse is not reading the declaration the gate executes"
        )

    def test_typecheck_roots_cover_every_declared_workspace_member(self) -> None:
        # §Q3.3's cross-derivation pin. A workspace member silently dropped from the runner
        # is a registration-site defect nothing else in this repo checks mechanically.
        roots = set(gg.typecheck_roots(REPO_ROOT))
        members = set(gg.workspace_members(REPO_ROOT))
        assert members <= roots, (
            f"workspace members absent from scripts/typecheck.sh MEMBERS: {sorted(members - roots)} "
            f"— declared in pyproject's [tool.uv.workspace] and type-checked by nothing"
        )

    def test_every_parsed_typecheck_root_exists_in_this_checkout(self) -> None:
        # ⚠ THIS ASSERTION USED TO DEMAND `is_dir()` WHILE ITS OWN COMMENT SAID A ROOT MAY BE A
        # SINGLE FILE — the message admitting what the assertion forbade, which is this repo's
        # false-gate shape inverted, and it would have gone RED the day anyone followed the
        # prose. What a root may never be is a PHANTOM: mypy answers `Cannot read file` and the
        # runner exits non-zero for a reason unrelated to type errors, while the guard calls the
        # phantom's tree covered. So the tree-fact asserted here is EXISTENCE, and the guard's
        # own acceptance of a file root is pinned separately (test_a_single_file_member_is_a_
        # legal_typecheck_root_that_covers_itself) — this one cannot see a guard defect at all
        # and no longer pretends to: it is named for the tree.
        for root in gg.typecheck_roots(REPO_ROOT):
            assert (REPO_ROOT / root).exists(), (
                f"typecheck root {root!r} names nothing in this checkout — the gate iterates a "
                f"phantom and checks nothing, which reads as coverage"
            )

    def test_a_single_file_member_is_a_legal_typecheck_root_that_covers_itself(
        self, tmp_path: Path
    ) -> None:
        # The GUARD-level half of the pin above, and it exists because the instrument PERMITS a
        # file entry (`typecheck_roots` requires `.exists()`, not `.is_dir()`) and an unpinned
        # permitted behaviour is untested code. `MEMBERS` stopped meaning "workspace members" at
        # ruling R9 and means "every tree mypy must cover", of which a single file is the finest
        # grain — the mechanism that closed this instrument's own recursion before F1 made the
        # entry unnecessary.
        repository = _minimal_repository(
            tmp_path,
            members=["loremaster", "docs/consult/coherence_check.py"],
            extra_files=["docs/consult/coherence_check.py", "docs/consult/other_probe.py"],
        )
        assert gg.typecheck_roots(repository.root) == [
            "loremaster",
            "docs/consult/coherence_check.py",
        ]
        verdicts = assert_every_tracked_file_is_accounted_for(repository.root, exemptions=())
        assert (
            fates_of(verdicts, "docs/consult/coherence_check.py")[gg.GateAxis.TYPES]
            is gg.Fate.COVERED
        ), "a root covers ITSELF, component-wise — that is what makes a file entry a root at all"
        assert (
            fates_of(verdicts, "docs/consult/other_probe.py")[gg.GateAxis.TYPES]
            is gg.Fate.UNGATED
        ), "a FILE root must not cover its siblings; that would be a directory entry in disguise"

    def test_every_parsed_testpath_exists_as_a_directory(self) -> None:
        for testpath in gg.pytest_testpaths(REPO_ROOT):
            assert (REPO_ROOT / testpath).is_dir(), (
                f"testpaths entry {testpath!r} is not a directory in this checkout — pytest "
                f"collects nothing there and the execution axis is satisfied by an empty tree"
            )

    def test_fixture_members_line_matches_the_real_runner(self) -> None:
        # The realism seam. If the real runner ever changes the SHAPE of its declaration
        # (multi-line array, quoted words), every fixture in this file silently stops being
        # representative. This is the pin that makes that loud.
        rendered = FixtureRepository.render_members_line(gg.typecheck_roots(REPO_ROOT))
        real_lines = (REPO_ROOT / "scripts" / "typecheck.sh").read_text(encoding="utf-8").splitlines()
        assert rendered in real_lines, (
            f"the fixture builder renders {rendered!r}, which is not a line of the real runner; "
            f"these fixtures no longer model the file the guard parses"
        )

    def test_a_members_mention_inside_a_comment_is_not_the_declaration(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # The runner's fixture carries `# The MEMBERS=(decoy) mention below is prose…`.
        roots = gg.typecheck_roots(workspace_shaped_repository.root)
        assert "decoy" not in roots, (
            f"a MEMBERS mention inside a comment was parsed as the declaration ({roots!r}); the "
            f"parse must be anchored to the start of a line"
        )
        assert roots == ["lorerunes", "loremaster", "skills", "docs/eval"]

    def test_member_mypypath_returns_only_what_the_runner_declares(self, tmp_path: Path) -> None:
        # P-4, and it is the SAME false-gate shape fixed one pin over: the MYPYPATH requirement
        # below asks a question about the RUNNER, so a reader that FABRICATES the map answers it
        # with the guard's own opinion. Measured — such a build passed the whole contract.
        repository = _minimal_repository(
            tmp_path, members=["loremaster", "scripts/registration_sites.py"]
        )
        declared = gg.member_mypypath(repository.root)
        assert declared == {}, (
            f"this runner declares no MEMBER_MYPYPATH map, yet the reader returned {declared!r}"
        )

    def test_every_declared_mypypath_entry_reconstructs_a_line_of_the_real_runner(self) -> None:
        runner = (REPO_ROOT / "scripts" / "typecheck.sh").read_text(encoding="utf-8")
        declared = gg.member_mypypath(REPO_ROOT)
        assert declared, "the real runner declares a MEMBER_MYPYPATH map; the reader found none"
        for entry, value in declared.items():
            assert f'[{entry}]="{value}"' in runner, (
                f'member_mypypath reports [{entry}]="{value}", which reconstructs no line of '
                f"scripts/typecheck.sh — the reader is not reading the file the gate executes"
            )

    @pytest.mark.parametrize(
        "reader",
        [
            gg.typecheck_roots,
            gg.pytest_testpaths,
            gg.workspace_members,
            gg.ruff_excluded_trees,
            gg.pytest_test_file_patterns,
            gg.tracked_python_files,
        ],
        ids=lambda reader: reader.__name__,
    )
    def test_readers_answer_for_repo_root_not_for_the_process_cwd(
        self, reader: object, distinctly_configured_repository: FixtureRepository
    ) -> None:
        # WRONG ANCHOR. pytest runs with the cwd inside THIS repository, so a reader that
        # shells out or opens a relative path without honouring repo_root answers about the
        # real tree while claiming to answer about the fixture — and every fixture case in
        # this file silently grades the wrong repository.
        assert Path.cwd() != distinctly_configured_repository.root, "precondition: cwd differs"
        fixture_answer = reader(distinctly_configured_repository.root)  # type: ignore[operator]
        real_answer = reader(REPO_ROOT)  # type: ignore[operator]
        assert fixture_answer != real_answer, (
            f"{reader.__name__} returned the same value for the fixture repository and for this "  # type: ignore[attr-defined]
            f"checkout, so it is not reading the repo_root it was handed"
        )


# ---------------------------------------------------------------------------
# 2. Blind is not clean
# ---------------------------------------------------------------------------


class TestTheGuardFailsLoudRatherThanBlind:
    """§Q3.3: an unparseable or empty input is a HARD FAIL, never a skip and never a pass.

    Every case here is the same shape: a silent no-op upstream would produce **zero
    findings**, which prints as a clean tree. *"If step N silently no-opped, would step N+1
    still print something that reads as success?"* — for every input below the honest answer
    was yes, so each one ends in a raise.
    """

    def test_a_runner_with_no_members_declaration_is_blind_not_clean(self, tmp_path: Path) -> None:
        repository = _minimal_repository(tmp_path, members=None)
        with pytest.raises(gg.GuardIsBlind) as raised:
            gg.typecheck_roots(repository.root)
        message = str(raised.value).lower()
        assert "members" in message and "blind" in message, (
            f"the raise must name what could not be parsed and say the GUARD is blind rather "
            f"than the tree clean; got: {raised.value}"
        )

    def test_an_empty_members_array_is_blind_not_clean(self, tmp_path: Path) -> None:
        repository = _minimal_repository(tmp_path, members=[])
        with pytest.raises(gg.GuardIsBlind):
            gg.typecheck_roots(repository.root)

    def test_a_missing_runner_is_blind_not_clean(self, tmp_path: Path) -> None:
        repository = _minimal_repository(tmp_path, omit_typecheck_runner=True)
        with pytest.raises(gg.GuardIsBlind):
            gg.typecheck_roots(repository.root)

    @pytest.mark.parametrize("wildcard", WHOLE_TREE_SCOPE_SPELLINGS)
    def test_a_whole_tree_member_is_blind_not_clean(self, tmp_path: Path, wildcard: str) -> None:
        # The nastiest silent no-op in the set: a MEMBERS parse that widens to `.` marks
        # EVERY file gated and reports zero gaps — a false clear wearing a clean bill of health.
        # Parametrized over the SHARED spelling constant, which is the whole point: this pin
        # previously carried four spellings, its testpaths twin carried five, and the guard
        # false-cleared on the two only the twin knew about.
        repository = _minimal_repository(tmp_path, members=["loremaster", wildcard])
        with pytest.raises(gg.GuardIsBlind) as raised:
            gg.typecheck_roots(repository.root)
        assert repr(wildcard) in str(raised.value) or wildcard in str(raised.value)

    def test_a_member_naming_no_directory_is_blind_not_clean(self, tmp_path: Path) -> None:
        # A MEMBERS entry may be a DIRECTORY or a single FILE (pinned by
        # test_a_single_file_member_is_a_legal_typecheck_root_that_covers_itself) — but it must
        # NAME SOMETHING. mypy's own
        # behaviour on a phantom entry is `Cannot read file … No such file or directory`,
        # measured: the runner then exits non-zero for a reason unrelated to type errors, and
        # this guard would meanwhile call the phantom's tree covered.
        repository = _minimal_repository(tmp_path, members=["loremaster", "deleted_member"])
        with pytest.raises(gg.GuardIsBlind) as raised:
            gg.typecheck_roots(repository.root)
        assert "deleted_member" in str(raised.value)

    def test_a_manifest_with_no_testpaths_key_is_blind_not_clean(self, tmp_path: Path) -> None:
        repository = _minimal_repository(tmp_path, testpaths=None)
        with pytest.raises(gg.GuardIsBlind) as raised:
            gg.pytest_testpaths(repository.root)
        assert "testpaths" in str(raised.value).lower()

    def test_a_manifest_with_no_pytest_table_is_blind_not_clean(self, tmp_path: Path) -> None:
        repository = _minimal_repository(tmp_path, omit_pytest_table=True)
        with pytest.raises(gg.GuardIsBlind):
            gg.pytest_testpaths(repository.root)

    def test_an_empty_testpaths_list_is_blind_not_clean(self, tmp_path: Path) -> None:
        repository = _minimal_repository(tmp_path, testpaths=[])
        with pytest.raises(gg.GuardIsBlind):
            gg.pytest_testpaths(repository.root)

    def test_a_testpath_naming_no_directory_is_blind_not_clean(self, tmp_path: Path) -> None:
        repository = _minimal_repository(tmp_path, testpaths=["loremaster/tests", "docs/eval"])
        with pytest.raises(gg.GuardIsBlind) as raised:
            gg.pytest_testpaths(repository.root)
        assert "docs/eval" in str(raised.value)

    @pytest.mark.parametrize("wildcard", WHOLE_TREE_SCOPE_SPELLINGS)
    def test_a_whole_tree_testpath_is_blind_not_clean(self, tmp_path: Path, wildcard: str) -> None:
        # M2 / the LEG B analogue of the MEMBERS wildcard, and the two are now parametrized over
        # the SAME constant so they cannot drift apart again (they had, and the guard false-cleared
        # in the gap). MEASURED against a build that passed the whole contract:
        # `testpaths = ["."]` makes every test-shaped file read as covered and the guard reports
        # ZERO execution findings — a false clear wearing a clean bill of health.
        repository = _minimal_repository(tmp_path, testpaths=["loremaster/tests", wildcard])
        with pytest.raises(gg.GuardIsBlind) as raised:
            gg.pytest_testpaths(repository.root)
        assert repr(wildcard) in str(raised.value) or wildcard in str(raised.value)

    def test_two_members_declarations_are_blind_not_clean(self, tmp_path: Path) -> None:
        # M3. bash's LAST assignment wins; a line-anchored search finds the FIRST. A narrowed
        # second declaration therefore certifies as the wider first, so a SHRUNKEN type gate
        # reads as unshrunken. "grep finds exactly one array today" is a fact about today, not
        # a pin — this is the pin.
        repository = _minimal_repository(tmp_path, members=["loremaster", "docs"])
        runner = repository.root / "scripts" / "typecheck.sh"
        runner.write_text(
            runner.read_text(encoding="utf-8") + "\nMEMBERS=(loremaster)\n", encoding="utf-8"
        )
        with pytest.raises(gg.GuardIsBlind) as raised:
            gg.typecheck_roots(repository.root)
        assert "MEMBERS" in str(raised.value)

    def test_a_missing_git_binary_is_blind_not_clean(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # #131 VERBATIM, constructed rather than reasoned about: the code shells out to git and
        # the deployed image had no git, and the OSError was swallowed into a silent empty
        # result for months. A build with `except OSError: return []` is INERT on any host that
        # has git — so nothing but this fixture can ever see it.
        repository = _minimal_repository(tmp_path)
        monkeypatch.setenv("PATH", str(tmp_path / "no_binaries_here"))
        with pytest.raises(gg.GuardIsBlind) as raised:
            gg.tracked_python_files(repository.root)
        assert "git" in str(raised.value).lower(), (
            f"the guard must say WHICH dependency it could not reach; got: {raised.value}"
        )

    def test_a_quoted_members_entry_containing_a_space_is_one_root(self, tmp_path: Path) -> None:
        # The token split is a MECHANISM, and `str.split` gets this wrong: measured,
        # shlex.split('a "docs/my eval" b') is 3 tokens and str.split is 4. A mis-split entry
        # names two phantom roots, and a phantom root is a blind guard.
        (tmp_path / "docs" / "my eval").mkdir(parents=True)
        repository = _minimal_repository(tmp_path, members=["loremaster", "docs/my eval"])
        assert gg.typecheck_roots(repository.root) == ["loremaster", "docs/my eval"]

    def test_a_missing_manifest_is_blind_not_clean(self, tmp_path: Path) -> None:
        repository = _minimal_repository(tmp_path)
        (repository.root / "pyproject.toml").unlink()
        with pytest.raises(gg.GuardIsBlind):
            gg.pytest_testpaths(repository.root)

    def test_a_directory_that_is_not_a_git_repository_is_blind_not_clean(self, tmp_path: Path) -> None:
        # A wrong root is indistinguishable from a clean tree if the enumeration silently
        # returns nothing.
        plain = tmp_path / "not_a_repository"
        plain.mkdir()
        with pytest.raises(gg.GuardIsBlind):
            gg.tracked_python_files(plain)

    def test_the_healthy_control_repository_raises_nothing(self, tmp_path: Path) -> None:
        # POSITIVE CONTROL for this whole class: the same builder, unperturbed, parses fine.
        # Without it, every raise above could be an artifact of the fixture rather than of
        # the perturbation.
        repository = _minimal_repository(tmp_path)
        assert gg.typecheck_roots(repository.root) == ["loremaster"]
        assert gg.pytest_testpaths(repository.root) == ["loremaster/tests"]
        assert gg.tracked_python_files(repository.root)


# ---------------------------------------------------------------------------
# 3. Mypy configuration this guard does not model
# ---------------------------------------------------------------------------


class TestMypyConfigurationThisGuardDoesNotModel:
    """§Q3.2: a file inside a member that mypy SKIPS is ungated in fact while passing a
    path-membership test. The guard does not model that, so it refuses to certify a tree
    whose configuration could hide one — #136's shape: never certify what you cannot see."""

    def test_this_repository_declares_nothing_the_guard_cannot_model(self) -> None:
        unmodelled = gg.unmodelled_mypy_configuration(REPO_ROOT)
        assert unmodelled == [], (
            f"[tool.mypy] in this checkout now carries settings this guard does not model, so "
            f"its LEG A verdict is not sound: {unmodelled}"
        )

    def test_a_mypy_exclude_makes_the_guard_refuse_rather_than_mis_model(self, tmp_path: Path) -> None:
        repository = _minimal_repository(tmp_path, mypy_exclude=["loremaster/store/.*"])
        unmodelled = gg.unmodelled_mypy_configuration(repository.root)
        assert unmodelled, "a declared [tool.mypy] exclude was accepted silently"
        joined = " ".join(unmodelled).lower()
        assert "exclude" in joined, f"the refusal must name the setting it cannot model: {unmodelled}"
        assert "extend it or remove the exclude" in joined, (
            f"§Q3.2 requires the refusal to tell the reader the two ways out; got: {unmodelled}"
        )

    @pytest.mark.parametrize(
        ("table", "override", "what"),
        [
            # Every one of these was ACCEPTED SILENTLY by a build that passed the whole
            # contract. The first is the worst: a GLOBAL ignore_errors turns the entire type
            # gate off while this guard certifies a fully-gated tree — and it is the SAME
            # setting the contract already pinned one level down, in an override.
            ({"ignore_errors": True}, None, "a global ignore_errors"),
            ({"follow_imports": "skip"}, None, "a global follow_imports=skip"),
            ({"disable_error_code": ["import-not-found"]}, None, "a global disable_error_code"),
            (None, {"follow_imports": "skip"}, "follow_imports=skip in an override"),
            (None, {"disable_error_code": ["assignment"]}, "disable_error_code in an override"),
            # THE ALLOWLIST PROPERTY ITSELF. A build carrying a longer FORBIDDEN list passes
            # every row above and fails this one: a setting nobody has thought of yet must be
            # refused BY DEFAULT. "When you catch yourself enumerating what is FORBIDDEN, you
            # have already lost — the safe set is small and enumerable, so allowlist the safe."
            ({"some_future_relaxation": True}, None, "a setting invented after this guard"),
            (None, {"another_future_relaxation": True}, "the same, in an override"),
        ],
    )
    def test_an_unmodelled_setting_is_refused_by_allowlist_not_by_name(
        self, tmp_path: Path, table: dict[str, object] | None, override: dict[str, object] | None, what: str
    ) -> None:
        repository = _minimal_repository(
            tmp_path,
            mypy_table_extra=table,
            mypy_overrides=[_mypy_override(["loremaster.store.lease"], **override)] if override else [],
        )
        unmodelled = gg.unmodelled_mypy_configuration(repository.root)
        assert unmodelled, (
            f"{what} was accepted silently. This guard's LEG A verdict is path membership; any "
            f"mypy setting it does not model can make a registered file unchecked IN FACT, so "
            f"the safe keys are allowlisted and everything else is refused."
        )

    def test_an_ignore_errors_override_makes_the_guard_refuse(self, tmp_path: Path) -> None:
        repository = _minimal_repository(
            tmp_path,
            mypy_overrides=[_mypy_override(["loremaster.store.lease"], ignore_errors=True)],
        )
        unmodelled = gg.unmodelled_mypy_configuration(repository.root)
        assert unmodelled, (
            "an [[tool.mypy.overrides]] ignore_errors block was accepted silently — the module "
            "it names is inside a typecheck root and type-ungated in fact"
        )
        assert "loremaster.store.lease" in " ".join(unmodelled)

    def test_an_unmodelled_setting_makes_the_WHOLE_VERDICT_refuse_not_just_a_reader(
        self, tmp_path: Path
    ) -> None:
        # The wrong build this kills: a guard that computes `unmodelled_mypy_configuration`
        # honestly and never consults it, so the verdict is rendered anyway. A reader nobody
        # calls is the same shape as a guard nobody runs — the report reads clean while the
        # guard's LEG A model is known-wrong.
        repository = _minimal_repository(tmp_path, mypy_exclude=["loremaster/store/.*"])
        with pytest.raises(gg.GuardIsBlind):
            gg.classify(repository.root, exemptions=())

    def test_the_relaxations_this_repository_actually_uses_do_not_trip_the_refusal(
        self, tmp_path: Path
    ) -> None:
        # POSITIVE CONTROL, and the one that stops this becoming a false gate. The real
        # manifest carries several [[tool.mypy.overrides]] blocks — ignore_missing_imports,
        # follow_untyped_imports, disallow_any_unimported. None of them makes a file
        # unchecked, and a guard that refused them would be switched off inside a week.
        repository = _minimal_repository(
            tmp_path,
            mypy_overrides=[
                _mypy_override(["astroid", "astroid.*"], follow_untyped_imports=True),
                _mypy_override(["kubernetes", "kubernetes.*"], ignore_missing_imports=True),
                _mypy_override(["lorescribe.astroid_parse"], disallow_any_unimported=False),
            ],
        )
        assert gg.unmodelled_mypy_configuration(repository.root) == []


# ---------------------------------------------------------------------------
# 4. Membership is path-component-wise
# ---------------------------------------------------------------------------


class TestMembershipIsPathComponentWise:
    """§Q3.3: ``Path.parts`` prefix, never ``str.startswith``. The sibling-prefix directory
    is the wrong build this exists to kill, and it is not hypothetical — ``scripts`` is
    simultaneously a ``testpaths`` entry and a ``MEMBERS`` typecheck root, so a substring test
    would hand a hypothetical ``scripts_extra/`` BOTH gates at once.

    (The rationale used to name ``scripts`` as *"the pinned exemption root"*. F1 deleted the
    exemption; the sibling-prefix property is unchanged and the reason is now the two GATES that
    tree carries.)"""

    @pytest.mark.parametrize(
        ("path", "tree", "expected"),
        [
            ("scripts/registration_sites.py", "scripts", True),
            ("scripts", "scripts", True),
            ("scripts_extra/promotion_helper.py", "scripts", False),
            ("scriptsy.py", "scripts", False),
            ("docs/eval/smoke_p8b.py", "docs/eval", True),
            ("docs/eval/smoke_p8b.py", "docs", True),
            ("docs/evaluation/harness.py", "docs/eval", False),
            ("docs_eval/smoke.py", "docs", False),
            ("skills/lore-deploy/tests/test_port_probe.py", "skills/lore-deploy/tests", True),
            ("skills/lore-deploy/tests_extra/test_x.py", "skills/lore-deploy/tests", False),
            ("loremaster/tests/test_store_lease.py", "loremaster/tests", True),
            ("loremaster/store/lease.py", "loremaster/tests", False),
        ],
    )
    def test_prefix_membership(self, path: str, tree: str, expected: bool) -> None:
        assert gg.is_under(path, tree) is expected

    def test_a_sibling_prefix_directory_is_neither_gated_nor_exempt(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        fates = fates_of(verdicts, "scripts_extra/promotion_helper.py")
        assert fates[gg.GateAxis.TYPES] is gg.Fate.UNGATED, (
            f"scripts_extra/ passed as being under `scripts` — a substring test gives a sibling "
            f"directory a gate that never reads it; got {fates[gg.GateAxis.TYPES]}"
        )


# ---------------------------------------------------------------------------
# 5. The property is PER-AXIS (wrong build #1)
# ---------------------------------------------------------------------------


class TestThePropertyIsPerAxisNotBinary:
    """The packet's literal union property is a wrong build that ships green. Both halves
    of the 2×2's off-diagonal are pinned here, in a repository built to hold nothing else."""

    def test_a_tree_in_testpaths_but_under_no_typecheck_root_is_reported_on_the_types_axis(
        self, half_gapped_repository: FixtureRepository
    ) -> None:
        findings = findings_of(
            half_gapped_repository.root, exemptions=()
        )
        reported = {(finding.path, finding.axis) for finding in findings}
        assert ("docs/eval/smoke_p8b.py", gg.GateAxis.TYPES) in reported, (
            f"docs/eval sits in testpaths and under no typecheck root — the #238/#261 half-gap. "
            f"A guard implementing the packet's union property calls it gated. Reported: "
            f"{sorted((p, a.name) for p, a in reported)}"
        )

    def test_a_tree_under_a_typecheck_root_but_in_no_testpath_is_reported_on_the_execution_axis(
        self, half_gapped_repository: FixtureRepository
    ) -> None:
        findings = findings_of(
            half_gapped_repository.root, exemptions=()
        )
        reported = {(finding.path, finding.axis) for finding in findings}
        assert ("skills/lore-deploy/tests/test_port_probe.py", gg.GateAxis.EXECUTION) in reported, (
            f"skills is a typecheck root and in no testpaths entry — the #280 half-gap, 117 "
            f"committed tests no gate collects. Reported: {sorted((p, a.name) for p, a in reported)}"
        )

    def test_coverage_on_one_axis_never_silences_the_other(
        self, half_gapped_repository: FixtureRepository
    ) -> None:
        # The union build's signature: exactly zero findings on this tree.
        findings = findings_of(
            half_gapped_repository.root, exemptions=()
        )
        axes = {finding.axis for finding in findings}
        assert axes == set(gg.GateAxis), (
            f"this repository is half-gapped on BOTH axes; a guard reporting only "
            f"{sorted(axis.name for axis in axes)} is collapsing the legs into a union"
        )

    def test_a_new_skill_tree_is_reported_even_though_a_sibling_skill_is_registered(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # The config wave registers `skills/lore-deploy/*` only. The guard must catch the
        # NEXT skill, not just the one that prompted the fix — the quantifier law: pin the
        # outcome over all inputs, never condition it on the instance that was found.
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        registered = fates_of(verdicts, "skills/lore-deploy/tests/test_port_probe.py")
        new_skill = fates_of(verdicts, "skills/otherskill/tests/test_workspace_probe.py")
        assert registered[gg.GateAxis.EXECUTION] is gg.Fate.COVERED
        assert new_skill[gg.GateAxis.EXECUTION] is gg.Fate.UNGATED, (
            f"a NEW skill's tests are outside every testpaths entry and must be reported; got "
            f"{new_skill[gg.GateAxis.EXECUTION]}"
        )
        assert new_skill[gg.GateAxis.TYPES] is gg.Fate.COVERED, (
            "the `skills` typecheck root does cover it on the types axis — reporting it there "
            "too would be a false positive, which is how a gate gets switched off"
        )


# ---------------------------------------------------------------------------
# 4b. Membership must discriminate AT EVERY CALL SITE, not at the definition
# ---------------------------------------------------------------------------


class TestMembershipDiscriminatesAtEveryCallSite:
    """`is_under` has a 12-row matrix — and that pins the HELPER, not its USE.

    **Measured by adversary-44-gatedground-1: `str.startswith` substituted at the
    typecheck-root site (WB28), the testpath site (WB3) or the archived-receipts site (WB29)
    passed the ENTIRE contract, 130 passed / 0 failed each, while waving real committed
    ungated ground through.** Only the exemption-root site had a fixture that could tell the
    difference. Nothing requires `classify` to call the helper it was handed.

    So the property is pinned **∀ over call sites** — one fixture file per site, each a
    sibling-prefix or ancestor of a real scope — which is the quantifier law applied to a
    helper rather than to an input.
    """

    def test_a_sibling_prefix_of_a_typecheck_root_is_not_covered(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # `docs/evaluation/` vs the `docs/eval` root. WRONG BUILD: startswith at the LEG A site.
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        assert fates_of(verdicts, "docs/evaluation/harness.py")[gg.GateAxis.TYPES] is gg.Fate.UNGATED

    def test_a_sibling_prefix_of_a_testpath_is_not_covered(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # `loremaster/tests_extra/` vs the `loremaster/tests` testpath. WRONG BUILD: startswith
        # at the LEG B site, with `is_under` itself left perfectly correct.
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        fates = fates_of(verdicts, "loremaster/tests_extra/test_probe.py")
        assert fates[gg.GateAxis.EXECUTION] is gg.Fate.UNGATED

    def test_a_sibling_prefix_of_the_archived_receipts_root_is_not_exempt(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # `docs/plans/v2/receipts_live/` vs `docs/plans/v2/receipts`. The nastiest of the three:
        # a promoted tool parked one character away from the archive silently inherits the
        # archive's law-backed exemption.
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        fates = fates_of(verdicts, "docs/plans/v2/receipts_live/promoted_tool.py")
        assert fates[gg.GateAxis.TYPES] is gg.Fate.UNGATED, (
            f"a sibling of the archived-receipts root inherited the archive's exemption; got "
            f"{fates[gg.GateAxis.TYPES]}"
        )

    def test_a_test_shaped_sibling_of_the_archived_receipts_root_is_not_exempt_on_execution(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # P-2. The non-test sibling one pin up discriminates the receipts membership site on the
        # TYPES axis only — measured, a build using `startswith` there on EXECUTION alone passed
        # the whole contract. A promoted TEST parked one character from the archive is the case
        # that needs a test-shaped fixture to see.
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root,
            exemptions=(),
        )
        fates = fates_of(verdicts, "docs/plans/v2/receipts_live/test_promoted_tool.py")
        assert fates[gg.GateAxis.EXECUTION] is gg.Fate.UNGATED, (
            f"a test-shaped sibling of the archived-receipts root inherited the archive's "
            f"exemption on the EXECUTION axis; got {fates[gg.GateAxis.EXECUTION]}"
        )
        assert fates[gg.GateAxis.TYPES] is gg.Fate.UNGATED

    def test_an_ancestor_of_a_testpath_is_not_covered_by_it(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # REVERSE CONTAINMENT. `skills/test_workspace_probe.py` sits ABOVE the
        # `skills/lore-deploy/tests` testpath. A build that asks "is the testpath under the
        # file's directory" instead of the other way round covers it, and pytest never
        # collects it.
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        fates = fates_of(verdicts, "skills/test_workspace_probe.py")
        assert fates[gg.GateAxis.EXECUTION] is gg.Fate.UNGATED

    def test_repository_root_level_python_is_ordinary_committed_ground(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # A root-level `.py` has a one-component path, so several plausible membership
        # implementations (empty-prefix comparisons, `dirname`-based lookups) call it covered
        # by everything. It is also the single most likely shape of real new ungated ground.
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        assert fates_of(verdicts, "release_probe.py")[gg.GateAxis.TYPES] is gg.Fate.UNGATED
        assert fates_of(verdicts, "conftest.py")[gg.GateAxis.EXECUTION] is gg.Fate.UNGATED


# ---------------------------------------------------------------------------
# 6. Exemptions — allowlist the safe
# ---------------------------------------------------------------------------


class TestTheExemptionTableIsAnAllowlistOfTheSafe:
    """§Q3.4 / FU1-A. Deny by default; every exemption is evidence-backed, axis-scoped, and
    carries a named re-open trigger. A row lacking a finding number or a trigger is rejected
    by the table's own validation — *a trigger nobody names is a hope*."""

    def test_the_table_lands_EMPTY_and_the_emptiness_is_a_fact_about_the_TREE(self) -> None:
        """The #188 exemption is GONE — ``scripts/`` was taken to type-debt zero and made a
        plain typecheck root, so there is nothing left to exempt.

        ⚠ **An empty table must be provably empty-because-nothing-needs-exempting, not
        empty-because-the-reader-returns-nothing** — the anti-vacuity discipline cutting the
        other way. The first assertion is the structure; the SECOND is the tree fact, and it is
        the one that can fail: it re-derives the whole verdict with NO exemptions at all.
        """
        assert gg.EXEMPTIONS == (), (
            f"the exemption table is no longer empty: "
            f"{[(row.root, row.axis.name, row.finding) for row in gg.EXEMPTIONS]}. A row is a "
            f"DESIGN decision requiring an operator ruling — and read the history before "
            f"proposing a tree-root one: a whole-tree exemption is an enumeration of an OPEN "
            f"set whose staleness is SILENT, which is why the frozen-roster design existed and "
            f"why resolving the debt was ruled better than exempting it."
        )
        with_none = gg.ungated_ground(REPO_ROOT, exemptions=())
        assert not with_none.findings, (
            f"the table is empty but the tree is not clean without it, so the emptiness is an "
            f"artifact of the reader rather than a fact about the tree:\n{with_none.render()}"
        )

    def test_the_validation_rules_survive_the_table_being_empty(self) -> None:
        # The RULES are the durable part: they are what makes a future row honest. Kept live
        # and exercised by the malformed-row matrix below, so the day someone proposes a row it
        # meets a specification rather than an empty page.
        row = gg.Exemption(
            root="docs/consult",
            axis=gg.GateAxis.TYPES,
            finding="#188",
            reason="a phrase describing why the tree cannot be gated yet",
            reopen_trigger="#188's cleanup lands; delete this row",
        )
        assert row.root == "docs/consult"

    @pytest.mark.parametrize(
        ("kwargs", "why"),
        [
            ({"finding": ""}, "no finding number"),
            ({"finding": "188"}, "a finding number without its sigil"),
            ({"finding": "see the ledger"}, "prose where a finding number belongs"),
            ({"reopen_trigger": ""}, "no named re-open trigger"),
            ({"reopen_trigger": "   "}, "whitespace where a trigger belongs"),
            ({"reason": ""}, "no reason"),
            ({"reason": "45 measured errors, its own work item"}, "a bare count in the reason"),
            ({"reason": "standing disposition since 2026-07-26"}, "a date in the reason"),
            # M8: `.strip()` truthiness admits a placeholder, while the failure message
            # promises a named condition. A trigger must cite the row's own finding.
            ({"reopen_trigger": "TBD"}, "a placeholder where a re-open trigger belongs"),
            ({"reopen_trigger": "when we get to it"}, "a trigger naming no finding"),
            ({"reason": "x"}, "a single token where a reason belongs"),
        ]
        # M4, quantified over the SHARED spelling constant instead of the two spellings someone
        # thought of: `PurePosixPath(".").parts == ()`, so a root of "." is a prefix of EVERY
        # path and ONE row silences an entire axis — the allowlist becomes an off switch. The
        # third call site of that constant, and the reason it is a constant.
        + [
            ({"root": spelling}, f"a root spelled {spelling!r} that widens or escapes")
            for spelling in WHOLE_TREE_SCOPE_SPELLINGS
        ],
    )
    def test_a_malformed_row_is_rejected_by_the_tables_own_validation(
        self, kwargs: dict[str, object], why: str
    ) -> None:
        fields: dict[str, object] = {
            "root": "docs/consult",
            "axis": gg.GateAxis.TYPES,
            "finding": "#188",
            "reason": "standing disposition: its own work item, config half first",
            "reopen_trigger": "the #188 cleanup lands; delete this row and the leg goes live",
        }
        fields.update(kwargs)
        with pytest.raises(gg.InvalidExemption):
            gg.Exemption(**fields)  # type: ignore[arg-type]

    def test_a_well_formed_row_constructs(self) -> None:
        # POSITIVE CONTROL: without it, an Exemption that rejects EVERYTHING would pass every
        # case above — the probe would be firing for the wrong reason.
        row = gg.Exemption(
            root="docs/consult",
            axis=gg.GateAxis.TYPES,
            finding="#188",
            reason="standing disposition: its own work item, config half first",
            reopen_trigger="the #188 cleanup lands; delete this row and the leg goes live",
        )
        assert row.root == "docs/consult"
        assert row.axis is gg.GateAxis.TYPES

    def test_an_exemption_is_scoped_to_its_axis(self, tmp_path: Path) -> None:
        # The wrong build this kills: treating a row as an exemption from the WHOLE guard.
        # `scripts` is exempt on types; its test files must still be reported when the tree
        # is outside testpaths.
        repository = _minimal_repository(
            tmp_path,
            testpaths=["loremaster/tests"],
            extra_files=["scripts/registration_sites.py", "scripts/test_registration_sites.py"],
        )
        rows = (
            gg.Exemption(
                root="scripts",
                axis=gg.GateAxis.TYPES,
                finding="#188",
                reason="a phrase standing in for a real disposition",
                reopen_trigger="#188's cleanup lands; delete this row",
            ),
        )
        verdicts = assert_every_tracked_file_is_accounted_for(repository.root, exemptions=rows)
        module_fates = fates_of(verdicts, "scripts/registration_sites.py")
        test_fates = fates_of(verdicts, "scripts/test_registration_sites.py")
        assert module_fates[gg.GateAxis.TYPES] is gg.Fate.EXEMPT_TABLE
        assert test_fates[gg.GateAxis.TYPES] is gg.Fate.EXEMPT_TABLE
        assert test_fates[gg.GateAxis.EXECUTION] is gg.Fate.UNGATED, (
            f"this row exempts the TYPES axis only; a scripts/ test file outside testpaths "
            f"must still be reported on execution. Got {test_fates[gg.GateAxis.EXECUTION]}"
        )

    def test_every_shipped_row_is_load_bearing(self) -> None:
        # An exemption matching nothing is a row nobody can delete, because nobody can tell
        # it is dead. Proven by MUTATION, not inspection: remove the row and findings must
        # appear under its root.
        #
        # ⚠ THIS LOOP IS VACUOUS TODAY — `gg.EXEMPTIONS` is empty by F1, so the body never
        # executes, and `assert False` as its first statement was MEASURED to leave this test
        # passing. A pin that cannot fail is not a pin, so the discrimination lives in
        # test_the_load_bearing_predicate_discriminates_on_a_fixture_table below: it runs the
        # SAME helper against a table holding one live row and one dead one. The loop stays
        # because it is the ∀ over the SHIPPED table, and it starts working the day a row lands.
        for row in gg.EXEMPTIONS:
            assert _row_is_load_bearing(REPO_ROOT, row, table=gg.EXEMPTIONS), (
                f"deleting exemption {row.root!r}/{row.axis.name} changes nothing — it protects "
                f"no committed file on that axis and is dead weight; delete it or fix its root"
            )

    def test_the_load_bearing_predicate_discriminates_on_a_fixture_table(
        self, tmp_path: Path
    ) -> None:
        # The control the ∀-over-shipped-rows loop above cannot have while the table is empty:
        # POSITIVE (a row protecting a real file) and NEGATIVE (a row protecting nothing) legs
        # for the same predicate, so a helper that returned True unconditionally — which would
        # make the loop above worthless the day a row lands — is caught NOW.
        repository = _minimal_repository(
            tmp_path,
            members=["loremaster"],
            extra_files=["docs/consult/coherence_check.py"],
        )
        live = gg.Exemption(
            root="docs/consult",
            axis=gg.GateAxis.TYPES,
            finding="#188",
            reason="a phrase standing in for a real disposition",
            reopen_trigger="#188's cleanup lands; delete this row",
        )
        dead = gg.Exemption(
            root="docs/nothing_here",
            axis=gg.GateAxis.TYPES,
            finding="#188",
            reason="a phrase standing in for a real disposition",
            reopen_trigger="#188's cleanup lands; delete this row",
        )
        assert _row_is_load_bearing(repository.root, live, table=(live,)), (
            "docs/consult holds a committed .py under no typecheck root, so the row protects it "
            "— a predicate that cannot see that is a predicate the ∀ loop inherits"
        )
        assert not _row_is_load_bearing(repository.root, dead, table=(dead,)), (
            "a row rooted at a tree with no committed file protects nothing and must read as "
            "dead weight"
        )

    def test_covered_ground_beats_an_exemption_so_a_stale_row_becomes_visible(
        self, tmp_path: Path
    ) -> None:
        # ⚠ THE SUBJECT OF THIS PIN WAS DELETED WITH THE #188 ROW AND THE PIN SURVIVED: it went
        # on passing `exemptions=()`, so there was NO exemption for coverage to beat, and a build
        # that REVERSED the precedence — exemption ahead of gate coverage — passed all 171 pins.
        # The row below is what makes the assertion mean what its name says.
        #
        # Precedence (COVERED over EXEMPT_TABLE) is what makes a stale row VISIBLE at all: a row
        # whose tree has since been gate-covered would otherwise hide behind itself, and nobody
        # could tell it was dead.
        repository = _minimal_repository(
            tmp_path,
            members=["loremaster", "scripts"],
            extra_files=["scripts/registration_sites.py"],
        )
        stale_row = gg.Exemption(
            root="scripts",
            axis=gg.GateAxis.TYPES,
            finding="#188",
            reason="a phrase standing in for a disposition the gate has since overtaken",
            reopen_trigger="#188's cleanup lands; delete this row",
        )
        verdicts = assert_every_tracked_file_is_accounted_for(
            repository.root, exemptions=(stale_row,)
        )
        fates = fates_of(verdicts, "scripts/registration_sites.py")
        assert fates[gg.GateAxis.TYPES] is gg.Fate.COVERED, (
            f"a file under BOTH a gate root and an exemption root must be COVERED, so the "
            f"exemption shows up as dead; got {fates[gg.GateAxis.TYPES]}"
        )
        assert not _row_is_load_bearing(repository.root, stale_row, table=(stale_row,)), (
            "and the consequence that makes the precedence worth having: with the tree gated, "
            "the row now reads as dead weight and can be deleted"
        )


# ---------------------------------------------------------------------------
# 6c. BLIND IS NOT CLEAN — through the VERDICT, not only at the reader
# ---------------------------------------------------------------------------


class TestBlindIsNotCleanThroughTheWholeVerdict:
    """A reader that raises correctly, behind an entry point that swallows it, is a guard that
    cannot fail.

    **Measured by adversary-44-gatedground-2: fourteen blind inputs were pinned on the READERS
    and only two through the verdict — so four builds that swallow ``GuardIsBlind`` inside
    ``classify`` passed all 174 pins, and three of them served bytes IDENTICAL to a healthy
    tree on a broken state.** That is a false clear by this repository's hard definition of
    trust, and it is the shape a reader-level pin structurally cannot see.

    So the property is quantified over the **entry point**: for every blind input, BOTH public
    entry points must refuse. Reader-level pins stay — they localise the failure — but they are
    no longer the only place the property is asserted.
    """

    def test_a_blind_members_declaration_makes_the_whole_verdict_refuse(self, tmp_path: Path) -> None:
        repository = _minimal_repository(tmp_path, members=None)
        rows: tuple[gg.Exemption, ...] = ()
        with pytest.raises(gg.GuardIsBlind):
            gg.classify(repository.root, exemptions=rows)
        # and the SERVED surface carries it as a field rather than an exception a caller
        # could swallow — byte-diffed against healthy in
        # TestBlindnessIsMonotoneToTheServedSurface.
        assert gg.ungated_ground(repository.root, exemptions=rows).blind_sources

    def test_a_whole_tree_testpath_makes_the_whole_verdict_refuse(self, tmp_path: Path) -> None:
        repository = _minimal_repository(tmp_path, testpaths=["loremaster/tests", "."])
        rows: tuple[gg.Exemption, ...] = ()
        with pytest.raises(gg.GuardIsBlind):
            gg.classify(repository.root, exemptions=rows)
        # and the SERVED surface carries it as a field rather than an exception a caller
        # could swallow — byte-diffed against healthy in
        # TestBlindnessIsMonotoneToTheServedSurface.
        assert gg.ungated_ground(repository.root, exemptions=rows).blind_sources

    def test_a_missing_git_binary_makes_the_whole_verdict_refuse(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = _minimal_repository(tmp_path)
        rows: tuple[gg.Exemption, ...] = ()
        monkeypatch.setenv("PATH", str(tmp_path / "no_binaries_here"))
        with pytest.raises(gg.GuardIsBlind):
            gg.classify(repository.root, exemptions=rows)
        # and the SERVED surface carries it as a field rather than an exception a caller
        # could swallow — byte-diffed against healthy in
        # TestBlindnessIsMonotoneToTheServedSurface.
        assert gg.ungated_ground(repository.root, exemptions=rows).blind_sources

    def test_the_healthy_control_serves_a_verdict_through_both_entry_points(
        self, tmp_path: Path
    ) -> None:
        # POSITIVE CONTROL. Without it, a build that raised GuardIsBlind unconditionally would
        # pass every case above — the probe firing for the wrong reason.
        repository = _minimal_repository(tmp_path)
        rows: tuple[gg.Exemption, ...] = ()
        assert gg.classify(repository.root, exemptions=rows)
        assert gg.ungated_ground(repository.root, exemptions=rows).blind_sources == ()


# ---------------------------------------------------------------------------
# 6c. LEG B's truth comes from the COLLECTOR, not from a parse (design directive D1)
# ---------------------------------------------------------------------------


class TestLegBIsDerivedFromTheCollector:
    """RULED (sidecar, superseding an earlier parse-symmetry instruction I was given).

    **The hole needed no wrong build: the CORRECT build served a false clear.** With
    ``norecursedirs = ["probes"]`` pytest collects ZERO items from a registered tree while the
    guard reported ``EXECUTION = COVERED`` and served zero findings — byte-identical to healthy.

    **And the fix is CONSTRUCTION, not parse-symmetry.** My first instruction was to model
    ``[tool.pytest.ini_options]`` the way LEG A models ``[tool.mypy]``. That was superseded for
    the right reason: pytest's exclusion surface includes arbitrary ``conftest.py`` code
    (``collect_ignore``, ``collect_ignore_glob``) — **an OPEN set no parser can close**, which is
    the forbidden-enumeration shape again. So LEG B asks the COLLECTOR: a tracked test-shaped
    file that contributes ZERO collected items is ungated ground, whatever mechanism silenced it,
    **including mechanisms not yet invented**.

    ⚠ **It must be a SUBPROCESS**, never the live session's items: under ``xdist`` each worker
    sees only its shard, so reading live items would manufacture false REDs — and a false
    positive is how a gate gets switched off.

    ⚠ **Scope, stated so a reader meets it:** ``conftest.py`` contributes no items BY DESIGN, so
    its reach cannot be measured this way and stays bounded by registration — a stated bound, not
    an oversight.
    """

    def test_the_collector_contributes_files_at_all(self) -> None:
        # ANTI-VACUITY 1. A failed subprocess returns "nothing contributed", which would flag
        # every test file in the tree — a storm that reads as a broken instrument, or worse, is
        # swallowed into "nothing to report".
        contributing = gg.collected_test_files(REPO_ROOT)
        assert contributing, (
            "the collector subprocess contributed no files at all. That is a broken instrument, "
            "not a tree without tests — do NOT read any LEG B verdict below it."
        )

    def test_the_collector_sees_this_very_contract(self) -> None:
        # ANTI-VACUITY 2, and the sharper one: the set must contain a file we KNOW contributes.
        # A subprocess that silently collected some unrelated subset would pass the pin above.
        relative = str(Path(__file__).resolve().relative_to(REPO_ROOT))
        assert relative in gg.collected_test_files(REPO_ROOT), (
            f"{relative} contributes items in this very run, yet the collector did not report it "
            f"— the subprocess is not collecting the tree this guard is judging"
        )

    def test_a_registered_file_that_the_manifest_silences_is_flagged(self, tmp_path: Path) -> None:
        # THE §6 HOLE, closed by construction. `norecursedirs` is the mechanism measured to work.
        repository = _minimal_repository(
            tmp_path, extra_files=["loremaster/tests/probes/test_probe.py"]
        )
        repository.write_pyproject(
            testpaths=["loremaster/tests"],
            workspace_members=["loremaster"],
            ruff_extend_exclude=["scratchpad", "docs/plans/v2/receipts"],
            python_files=None,
            pytest_ini_extra={"norecursedirs": ["probes"]},
            mypy_exclude=None,
            mypy_table_extra=None,
            mypy_overrides=[],
            omit_pytest_table=False,
        )
        repository.stage()
        verdicts = assert_every_tracked_file_is_accounted_for(repository.root, exemptions=())
        fate = fates_of(verdicts, "loremaster/tests/probes/test_probe.py")[gg.GateAxis.EXECUTION]
        assert fate is gg.Fate.UNGATED, (
            f"a REGISTERED test file that pytest collects nothing from was reported {fate.value}. "
            f"LEG B's whole claim is that a file under a testpaths entry is reached."
        )

    def test_a_conftest_level_collection_hook_is_caught_too(self, tmp_path: Path) -> None:
        # The mechanism NO PARSER CAN MODEL — arbitrary code in a conftest. This is the case that
        # makes the collector the right instrument rather than a symmetry argument.
        repository = _minimal_repository(
            tmp_path, extra_files=["loremaster/tests/test_hidden.py"]
        )
        (repository.root / "loremaster" / "tests" / "conftest.py").write_text(
            'collect_ignore_glob = ["test_hidden.py"]\n', encoding="utf-8"
        )
        repository.stage()
        verdicts = assert_every_tracked_file_is_accounted_for(repository.root, exemptions=())
        fate = fates_of(verdicts, "loremaster/tests/test_hidden.py")[gg.GateAxis.EXECUTION]
        assert fate is gg.Fate.UNGATED, (
            f"a conftest-level collect_ignore_glob silenced a registered test file and the guard "
            f"reported {fate.value}. No parse of the manifest can see this; the collector can."
        )

    def test_a_collector_subprocess_that_fails_is_blind_not_clean(self, tmp_path: Path) -> None:
        # A failed collection must NEVER read as "nothing contributed".
        repository = _minimal_repository(tmp_path)
        (repository.root / "loremaster" / "tests" / "conftest.py").write_text(
            "raise RuntimeError('a conftest that cannot import')\n", encoding="utf-8"
        )
        repository.stage()
        with pytest.raises(gg.GuardIsBlind):
            gg.collected_test_files(repository.root)

    def test_the_collector_answers_for_repo_root_not_for_the_live_session(
        self, tmp_path: Path
    ) -> None:
        # Proof it is a SUBPROCESS over `repo_root`: it reports a file this session has never
        # collected, and does NOT report this session's own contract.
        repository = _minimal_repository(tmp_path, extra_files=["loremaster/tests/test_fresh.py"])
        contributing = gg.collected_test_files(repository.root)
        assert "loremaster/tests/test_fresh.py" in contributing
        assert str(Path(__file__).resolve().relative_to(REPO_ROOT)) not in contributing


# ---------------------------------------------------------------------------
# 6d. Blindness is MONOTONE TO THE SERVED SURFACE (design directive D2)
# ---------------------------------------------------------------------------


class TestBlindnessIsMonotoneToTheServedSurface:
    """RULED: make ``GuardIsBlind`` un-swallowable BY TYPE.

    **Measured by adversary-44-gatedground-2: four builds that swallow ``GuardIsBlind`` inside
    ``classify`` passed all 174 pins, and three served bytes IDENTICAL to a healthy tree.** A
    correct reader behind a swallowing entry point is a guard that cannot fail — and pinning the
    raise at the reader structurally cannot see it.

    So the verdict OBJECT carries ``blind_sources``: non-empty ⇒ not clean, non-zero exit, and
    **served bytes distinct from healthy**. The pin form is entry-point Leg-2 forgery —
    CONSTRUCT each blind state and byte-diff served-vs-healthy — because the seam the CONSUMER
    reads is the only seam where trust lives.

    ⚠ **AND THE FOUR-VALUE PARAMETRIZATION THAT USED TO LIVE HERE IS GONE, DELIBERATELY.** It
    named four doors — ``members`` / ``testpath`` / ``git`` / ``manifest`` — and a build honouring
    exactly those and swallowing every other refusal passed all 171 pins while serving 17 false
    clears. Two lists that must agree are one list, so the property now lives ONCE, quantified
    over the door set read out of the instrument's own AST:
    :class:`TestTheDerivedFailureSetIsFullyProbed`. What stays here is the POSITIVE CONTROL,
    without which every byte-diff over there could pass for the wrong reason.
    """

    def test_a_clean_tree_serves_a_clean_verdict(self, tmp_path: Path) -> None:
        # POSITIVE CONTROL for the whole forgery matrix: a build that reported blindness
        # unconditionally would satisfy every byte-diff in section 17 — the probe firing for the
        # wrong reason, which is the failure mode a negative result cannot see.
        repository = _minimal_repository(tmp_path)
        verdict = gg.ungated_ground(repository.root, exemptions=())
        assert verdict.blind_sources == ()
        assert verdict.findings == ()
        assert verdict.exit_code == 0
        assert verdict.is_clean


# ---------------------------------------------------------------------------
# 7. The archived-receipts class
# ---------------------------------------------------------------------------


class TestTheArchivedReceiptsClass:
    """§Q3.4: ONE law-backed root, not a growing list. Receipts are preserved byte-faithful
    (#152/#153) — linting or re-typing them would falsify the evidence — so their exemption
    is anchored in a line someone actually committed, not in this guard's opinion."""

    def test_the_receipts_root_is_a_single_address_not_a_list(self) -> None:
        assert isinstance(gg.ARCHIVED_RECEIPTS_ROOT, str), (
            f"the archived-receipts class is ONE law-backed address; a collection "
            f"({type(gg.ARCHIVED_RECEIPTS_ROOT).__name__}) is a second exemption table wearing "
            f"a different name, and it will grow"
        )

    def test_the_receipts_root_is_backed_by_ruffs_own_exclusion(self) -> None:
        excluded = gg.ruff_excluded_trees(REPO_ROOT)
        assert gg.ARCHIVED_RECEIPTS_ROOT in excluded, (
            f"{gg.ARCHIVED_RECEIPTS_ROOT!r} is not in [tool.ruff] extend-exclude {excluded!r}. "
            f"The class exists because the repo declares that tree archived; if the declaration "
            f"moved, this guard is exempting a tree nothing calls archived"
        )

    def test_the_receipts_class_matches_at_least_one_committed_file(self) -> None:
        # ANTI-VACUITY. An exemption class that matches nothing is indistinguishable from a
        # class that is working — and it is the shape a renamed archive tree leaves behind.
        matched = [
            path
            for path in gg.tracked_python_files(REPO_ROOT)
            if gg.is_under(path, gg.ARCHIVED_RECEIPTS_ROOT)
        ]
        assert matched, (
            f"no committed .py sits under {gg.ARCHIVED_RECEIPTS_ROOT!r}; the archived-receipts "
            f"class is vacuous, so this guard has been exempting nothing and would not notice"
        )

    def test_a_receipts_root_absent_from_ruffs_exclusions_is_blind_not_clean(
        self, tmp_path: Path
    ) -> None:
        repository = _minimal_repository(tmp_path, ruff_extend_exclude=["scratchpad"])
        with pytest.raises(gg.GuardIsBlind) as raised:
            gg.classify(repository.root, exemptions=())
        assert gg.ARCHIVED_RECEIPTS_ROOT in str(raised.value)
        served = gg.ungated_ground(repository.root, exemptions=())
        assert served.blind_sources and not served.is_clean

    def test_a_receipts_class_matching_nothing_is_blind_not_clean(self, tmp_path: Path) -> None:
        repository = FixtureRepository(tmp_path)
        repository.write_typecheck_runner(members=["loremaster"], include_decoy_comment=False)
        repository.write_pyproject(
            testpaths=["loremaster/tests"],
            workspace_members=["loremaster"],
            ruff_extend_exclude=["scratchpad", "docs/plans/v2/receipts"],
            python_files=None,
            pytest_ini_extra=None,
            mypy_exclude=None,
            mypy_table_extra=None,
            mypy_overrides=[],
            omit_pytest_table=False,
        )
        repository.add_python_file("loremaster/tests/test_store_lease.py", body=_TEST_BODY)
        repository.stage()  # no receipts file at all
        with pytest.raises(gg.GuardIsBlind):
            gg.classify(repository.root, exemptions=())

    def test_an_archived_test_file_is_exempt_on_the_execution_axis_too(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # Forces the EXEMPT_ARCHIVED_RECEIPTS fate on LEG B. No committed receipt is
        # test-shaped in this checkout today, so without this fixture the receipts class
        # would be exercised on one axis only — a branch nothing reaches.
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        fates = fates_of(verdicts, "docs/plans/v2/receipts/2026-07-28-packet11ib/test_grade.py")
        assert fates[gg.GateAxis.TYPES] is gg.Fate.EXEMPT_ARCHIVED_RECEIPTS
        assert fates[gg.GateAxis.EXECUTION] is gg.Fate.EXEMPT_ARCHIVED_RECEIPTS


# ---------------------------------------------------------------------------
# 8. Input accounting — every tracked file has exactly one fate per axis
# ---------------------------------------------------------------------------


class TestEveryTrackedFileIsAccountedFor:
    """The quantifier law, mechanised. The helper runs on every fixture in this suite; these
    cases prove each named fate is REACHABLE — a ∀ helper evaluated only where a branch
    cannot fire is the fixture-reason pass wearing a universal quantifier."""

    def test_accounting_is_total_over_this_checkout(self) -> None:
        verdicts = assert_every_tracked_file_is_accounted_for(REPO_ROOT, exemptions=())
        assert len(verdicts) == len(gg.tracked_python_files(REPO_ROOT))

    @pytest.mark.parametrize(
        ("path", "axis_name", "fate_name"),
        [
            # TYPES — all four fates forced by a different file
            ("loremaster/tests/test_store_lease.py", "TYPES", "COVERED"),
            ("scripts/registration_sites.py", "TYPES", "UNGATED"),
            ("docs/plans/v2/receipts/2026-07-20-probes/probe_budget.py", "TYPES", "EXEMPT_ARCHIVED_RECEIPTS"),
            ("docs/consult/coherence_check.py", "TYPES", "UNGATED"),
            # EXECUTION — all five, including NOT_APPLICABLE
            ("loremaster/tests/test_store_lease.py", "EXECUTION", "COVERED"),
            (
                "docs/plans/v2/receipts/2026-07-28-packet11ib/test_grade.py",
                "EXECUTION",
                "EXEMPT_ARCHIVED_RECEIPTS",
            ),
            ("skills/otherskill/tests/test_workspace_probe.py", "EXECUTION", "UNGATED"),
            ("docs/consult/conftest.py", "EXECUTION", "UNGATED"),
            ("lorerunes/blankness.py", "EXECUTION", "NOT_APPLICABLE"),
        ],
    )
    def test_each_named_fate_is_forced_by_a_fixture(
        self,
        workspace_shaped_repository: FixtureRepository,
        path: str,
        axis_name: str,
        fate_name: str,
    ) -> None:
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        fates = fates_of(verdicts, path)
        assert fates[gg.GateAxis[axis_name]] is gg.Fate[fate_name]

    def test_the_execution_axis_exempt_table_fate_is_reachable(self, tmp_path: Path) -> None:
        # FATE COVERAGE, the honest way. The SHIPPED table has no execution-axis row, so this
        # fate is unreachable with gg.EXEMPTIONS — which would leave a branch of the guard
        # that no case in this file executes. Forced with a fixture table instead of left
        # uncovered; the shipped table's contents are pinned separately.
        repository = _minimal_repository(
            tmp_path,
            members=["loremaster", "skills"],
            testpaths=["loremaster/tests"],
            extra_files=["skills/lore-deploy/tests/test_port_probe.py"],
        )
        exemptions = (
            gg.Exemption(
                root="skills",
                axis=gg.GateAxis.EXECUTION,
                finding="#280",
                reason="hand-run idiom pending the testpaths entries",
                reopen_trigger="#280's testpaths entries land; delete this row",
            ),
        )
        verdicts = assert_every_tracked_file_is_accounted_for(repository.root, exemptions=exemptions)
        fates = fates_of(verdicts, "skills/lore-deploy/tests/test_port_probe.py")
        assert fates[gg.GateAxis.EXECUTION] is gg.Fate.EXEMPT_TABLE

    def test_an_untracked_file_is_out_of_scope_by_construction(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # §Q3.4 item 3: the derivation walks git, so scratchpad debris is not committed
        # ground. Stated as a pin so the bound is met deliberately.
        tracked = gg.tracked_python_files(workspace_shaped_repository.root)
        assert "scratchpad/session_debris.py" not in tracked
        reported = {finding.path for finding in findings_of(
            workspace_shaped_repository.root, exemptions=()
        )}
        assert "scratchpad/session_debris.py" not in reported

    def test_the_default_exemption_table_is_the_shipped_one(self) -> None:
        # ⚠ THIS PIN USED TO COMPARE `findings_of(REPO_ROOT)` WITH `findings_of(REPO_ROOT,
        # exemptions=())` AND CLAIM, IN ITS OWN COMMENT, THAT THE COMPARISON DISTINGUISHED A
        # BUILD DEFAULTING TO `()` FROM ONE DEFAULTING TO `EXEMPTIONS`. Under F1 the two ARE the
        # same object's value, so the two calls were identical by construction and the build
        # defaulting to a literal `()` passed — measured. The mechanical property that survives
        # F1 is IDENTITY of the default, and it is quantified over every entry point that takes
        # the parameter rather than over the two someone remembered.
        taking_exemptions = {
            name: parameter
            for name, function in vars(gg).items()
            if callable(function) and not name.startswith("_") and _is_module_function(gg, function)
            for parameter_name, parameter in inspect.signature(function).parameters.items()
            if parameter_name == "exemptions"
        }
        assert taking_exemptions, (
            "no public entry point takes an `exemptions` parameter — either the surface moved or "
            "this derivation is looking in the wrong place; it must not pass by finding nothing"
        )
        wrong = {
            name: parameter.default
            for name, parameter in taking_exemptions.items()
            if parameter.default is not gg.EXEMPTIONS
        }
        assert not wrong, (
            f"these entry points default `exemptions` to something that is not the SHIPPED table: "
            f"{wrong}. A literal `()` is indistinguishable from `EXEMPTIONS` today (F1 emptied "
            f"it) and stops being so the day a row lands — at which point the caller that omits "
            f"the argument silently ignores the table."
        )

    def test_findings_are_ordered_deterministically(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        first = findings_of(
            workspace_shaped_repository.root, exemptions=()
        )
        second = findings_of(
            workspace_shaped_repository.root, exemptions=()
        )
        assert first == second, "two runs over one tree disagree — a reviewer cannot diff them"
        paths = [finding.path for finding in first]
        assert paths == sorted(paths), (
            f"findings are not path-ordered, so the failure message reshuffles between runs and "
            f"a diff of two gate outputs is unreadable: {paths}"
        )


# ---------------------------------------------------------------------------
# 9. Anti-vacuity — a zero that is a result, not an artifact
# ---------------------------------------------------------------------------


class TestAntiVacuity:
    """§Q3.6. Four pins, because every silent no-op upstream of the verdict produces the SAME
    output as a clean tree: an empty file list, empty parsed roots, an empty receipts class,
    or an enumeration that reached only part of the tree. Each ends in its own assertion."""

    def test_the_tracked_python_file_list_is_not_empty(self) -> None:
        assert gg.tracked_python_files(REPO_ROOT), (
            "git ls-files returned no .py at all — the guard is blind (wrong root? wrong cwd?), "
            "not looking at a repository without Python in it"
        )

    def test_every_declared_workspace_member_contributed_files_and_all_are_covered(self) -> None:
        # DERIVED anchors, never an enumerated list of expected paths. This is also the
        # magnitude guard: if the enumeration reached only part of the tree, or membership
        # silently narrowed, a whole member stops being COVERED and this goes red.
        verdicts = gg.classify(REPO_ROOT, exemptions=())
        by_member: dict[str, list[gg.FileVerdict]] = {
            member: [v for v in verdicts if gg.is_under(v.path, member)]
            for member in gg.workspace_members(REPO_ROOT)
        }
        for member, member_verdicts in by_member.items():
            assert member_verdicts, (
                f"workspace member {member!r} contributed zero tracked .py to the enumeration — "
                f"the file list did not reach it, so any clean verdict is an artifact"
            )
            uncovered = [
                v.path for v in member_verdicts if v.fates[gg.GateAxis.TYPES] is not gg.Fate.COVERED
            ]
            assert not uncovered, (
                f"files inside declared workspace member {member!r} are not COVERED on the types "
                f"axis: {uncovered}"
            )

    def test_the_parsed_gate_scopes_are_not_empty(self) -> None:
        assert gg.typecheck_roots(REPO_ROOT), "zero typecheck roots parsed"
        assert gg.pytest_testpaths(REPO_ROOT), "zero testpaths parsed"

    def test_the_classifier_can_return_both_verdicts(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # POSITIVE + NEGATIVE control in one. A classifier stuck at COVERED prints a clean
        # tree; one stuck at UNGATED prints a catastrophe. Neither is a result.
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        observed = {fate for verdict in verdicts for fate in verdict.fates.values()}
        assert gg.Fate.COVERED in observed, "no file classified COVERED — the classifier is stuck"
        assert gg.Fate.UNGATED in observed, "no file classified UNGATED — the classifier is stuck"


# ---------------------------------------------------------------------------
# 10. Tracked-file enumeration, including hostile paths
# ---------------------------------------------------------------------------


class TestTrackedFileEnumeration:
    """``git ls-files`` is a producer↔consumer seam where an encoding convention changes:
    git quotes and backslash-escapes unusual paths on its LINE-oriented output and emits them
    raw only under NUL separation. A guard that splits lines gets a path that matches no file
    — and the ``is_under`` test then silently misfiles it."""

    def test_only_python_files_are_enumerated(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        tracked = gg.tracked_python_files(workspace_shaped_repository.root)
        assert tracked, "the enumeration returned nothing on a repository that has Python in it"
        assert all(path.endswith(".py") for path in tracked), (
            f"non-Python paths in the enumeration: {[p for p in tracked if not p.endswith('.py')]}"
        )
        assert "pyproject.toml" not in tracked
        assert "scripts/typecheck.sh" not in tracked

    def test_a_filename_merely_containing_py_is_not_python(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # `docs/consult/notes.py.txt` CONTAINS ".py" and is not Python. A guard testing
        # `".py" in name` INVENTS a finding for it — the false-positive direction, which is how
        # a gate gets switched off, and the one direction the endswith pin above cannot see.
        tracked = gg.tracked_python_files(workspace_shaped_repository.root)
        assert "docs/consult/notes.py.txt" not in tracked
        reported = {finding.path for finding in findings_of(
            workspace_shaped_repository.root, exemptions=()
        )}
        assert "docs/consult/notes.py.txt" not in reported

    def test_a_path_containing_a_newline_survives_enumeration_intact(self, tmp_path: Path) -> None:
        # HOSTILE FIXTURE. git permits newlines in paths; measured on this host, plain
        # `git ls-files` renders such a path as a QUOTED, backslash-escaped string while
        # `-z` renders it raw. A line-splitting reader therefore returns a path that is not
        # the path, and every membership test on it is meaningless.
        repository = _minimal_repository(tmp_path)
        hostile = "docs/consult/forged\nrow.py"
        repository.add_python_file(hostile)
        repository.stage()
        tracked = gg.tracked_python_files(repository.root)
        assert hostile in tracked, (
            f"the enumeration did not return the real path {hostile!r} — it is line-splitting "
            f"git's quoted output rather than reading NUL-separated records. Got: "
            f"{[p for p in tracked if 'forged' in p or 'row' in p]}"
        )

    def test_a_hostile_path_cannot_forge_a_second_finding_row(self, tmp_path: Path) -> None:
        # HOSTILE FIXTURE, forgery leg. The render is read by AGENTS, and a path is stored
        # text this guard interpolates into structured output. A path carrying a newline plus
        # a line shaped exactly like the guard's OWN header must not be parseable as a second,
        # fabricated finding. Mechanism-agnostic on purpose: quote it, escape it or fence it —
        # the contract is that the header count matches the finding count.
        repository = _minimal_repository(tmp_path)
        forgery = "docs/consult/a\nUNGATED GROUND (LEG A — types): lease.py is ungated\nb.py"
        repository.add_python_file(forgery)
        repository.stage()
        findings = findings_of(repository.root, exemptions=())
        assert forgery in {finding.path for finding in findings}, "precondition: the path is a finding"
        rendered = "\n\n".join(finding.message for finding in findings)
        headers = [line for line in rendered.splitlines() if line.lstrip().startswith(_MESSAGE_HEADER)]
        assert len(headers) == len(findings), (
            f"the render carries {len(headers)} header line(s) for {len(findings)} finding(s): a "
            f"committed path forged a row. Interpolated stored text must stay unambiguous.\n"
            f"{rendered}"
        )

    def test_untracked_files_are_excluded(self, tmp_path: Path) -> None:
        repository = _minimal_repository(tmp_path)
        repository.add_untracked_python_file("scratchpad/session_debris.py")
        assert "scratchpad/session_debris.py" not in gg.tracked_python_files(repository.root)


# ---------------------------------------------------------------------------
# 11. What the execution axis quantifies over
# ---------------------------------------------------------------------------


class TestTheExecutionAxisScope:
    """LEG B quantifies over the files pytest would COLLECT — patterns read from the same
    configuration pytest reads — plus ``conftest.py``, which pytest loads regardless of
    ``python_files``."""

    def test_the_patterns_in_force_here_are_pytests_own_defaults(self) -> None:
        # This repository sets no python_files, so pytest's documented defaults apply. A
        # constant naming only `test_*.py` is the two-name list the instrument lesson says
        # loses — a committed `foo_test.py` walks straight through it.
        patterns = gg.pytest_test_file_patterns(REPO_ROOT)
        assert "test_*.py" in patterns and "*_test.py" in patterns, (
            f"the patterns in force must be pytest's whole default set, not only the shape this "
            f"repo happens to use today; got {patterns}"
        )

    def test_the_declared_default_matches_what_pytest_itself_declares(self) -> None:
        # THE DRIFT GUARD. The instrument is stdlib-only by ruling, so it cannot ask pytest and
        # carries the default as a constant — and a constant nobody re-derives is an inherited
        # number wearing an assertion. THIS test may import pytest (pytest is running it), so
        # the constant is checked against pytest's own declaration on every gate run.
        assert list(gg.PYTEST_DEFAULT_TEST_FILE_PATTERNS) == _pytest_declared_default_patterns(), (
            f"the instrument's pinned default {list(gg.PYTEST_DEFAULT_TEST_FILE_PATTERNS)!r} no "
            f"longer matches what the installed pytest declares "
            f"({_pytest_declared_default_patterns()!r}). Update the constant and its citation."
        )

    def test_a_configured_python_files_override_replaces_the_defaults(self, tmp_path: Path) -> None:
        # The wrong build this kills: a hardcoded pattern list. It passes the case above and
        # fails here, and vice versa for a build that reads config but has no default source.
        repository = _minimal_repository(tmp_path, python_files=["check_*.py"])
        assert gg.pytest_test_file_patterns(repository.root) == ["check_*.py"]

    def test_the_execution_axis_follows_the_configured_patterns(self, tmp_path: Path) -> None:
        repository = _minimal_repository(
            tmp_path,
            python_files=["check_*.py"],
            extra_files=["docs/consult/check_coherence.py", "docs/consult/test_legacy.py"],
        )
        verdicts = assert_every_tracked_file_is_accounted_for(
            repository.root, exemptions=()
        )
        assert fates_of(verdicts, "docs/consult/check_coherence.py")[gg.GateAxis.EXECUTION] is gg.Fate.UNGATED
        assert (
            fates_of(verdicts, "docs/consult/test_legacy.py")[gg.GateAxis.EXECUTION]
            is gg.Fate.NOT_APPLICABLE
        ), "under python_files=['check_*.py'] pytest would not collect test_legacy.py anywhere"

    def test_the_second_default_pattern_is_covered(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # `*_test.py`. Zero files in this checkout use it today, which is exactly why a
        # hand-written `test_*.py` constant would ship green forever.
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        assert fates_of(verdicts, "tools/promotion_test.py")[gg.GateAxis.EXECUTION] is gg.Fate.UNGATED

    def test_a_conftest_outside_every_testpath_is_reported(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        assert fates_of(verdicts, "docs/consult/conftest.py")[gg.GateAxis.EXECUTION] is gg.Fate.UNGATED

    def test_a_conftest_is_in_scope_even_when_python_files_would_exclude_it(
        self, tmp_path: Path
    ) -> None:
        # conftest.py matches no python_files pattern; pytest loads it anyway. A guard that
        # derives LEG B's scope from python_files ALONE loses every conftest in the tree.
        repository = _minimal_repository(
            tmp_path,
            python_files=["check_*.py"],
            extra_files=["docs/consult/conftest.py"],
        )
        verdicts = assert_every_tracked_file_is_accounted_for(
            repository.root, exemptions=()
        )
        assert fates_of(verdicts, "docs/consult/conftest.py")[gg.GateAxis.EXECUTION] is gg.Fate.UNGATED

    def test_an_ordinary_module_is_not_judged_on_the_execution_axis(
        self, workspace_shaped_repository: FixtureRepository
    ) -> None:
        # The STATED BOUND, pinned: LEG B does not claim execution coverage of library code.
        # Reporting `lorerunes/blankness.py` as execution-ungated would be a false positive,
        # and a gate that refuses honest code is a gate that gets switched off.
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=()
        )
        assert fates_of(verdicts, "lorerunes/blankness.py")[gg.GateAxis.EXECUTION] is gg.Fate.NOT_APPLICABLE


# ---------------------------------------------------------------------------
# 12. The failure message
# ---------------------------------------------------------------------------


class TestTheFailureMessage:
    """§Q3.7. The message is read by an agent that will act on it without checking. It must
    name the file, the axis, the scope it is outside, and the two ways out — and it must NOT
    promise that the gate ran, because registration is precisely what this assertion checks
    and execution is precisely what it does not."""

    @pytest.fixture()
    def half_gapped_findings(self, half_gapped_repository: FixtureRepository) -> dict[str, gg.UngatedFile]:
        findings = findings_of(
            half_gapped_repository.root, exemptions=()
        )
        return {f"{finding.path}:{finding.axis.name}": finding for finding in findings}

    def test_the_types_message_names_the_file_the_axis_and_every_parsed_root(
        self, half_gapped_repository: FixtureRepository, half_gapped_findings: dict[str, gg.UngatedFile]
    ) -> None:
        message = half_gapped_findings["docs/eval/smoke_p8b.py:TYPES"].message
        assert "docs/eval/smoke_p8b.py" in message
        assert "LEG A" in message, f"the axis label is missing from: {message}"
        for root in gg.typecheck_roots(half_gapped_repository.root):
            assert root in message, (
                f"the message does not name parsed typecheck root {root!r}, so a reader cannot "
                f"tell what the file is outside OF: {message}"
            )

    def test_the_execution_message_names_the_file_the_axis_and_every_testpath(
        self, half_gapped_repository: FixtureRepository, half_gapped_findings: dict[str, gg.UngatedFile]
    ) -> None:
        message = half_gapped_findings["skills/lore-deploy/tests/test_port_probe.py:EXECUTION"].message
        assert "skills/lore-deploy/tests/test_port_probe.py" in message
        assert "LEG B" in message
        for testpath in gg.pytest_testpaths(half_gapped_repository.root):
            assert testpath in message, f"parsed testpath {testpath!r} missing from: {message}"

    @pytest.mark.parametrize(
        "required",
        [
            MESSAGE_MUST_MENTION_REGISTRATION,
            MESSAGE_MUST_DISCLAIM_EXECUTION,
            MESSAGE_MUST_DEMAND_ESCALATION,
            MESSAGE_MUST_DENY_AN_EXEMPTION_MECHANISM,
            MESSAGE_MUST_REFUSE_RECEIPTS_WIDENING,
        ],
    )
    def test_every_message_carries_the_registration_disclaimer_and_both_ways_out(
        self, half_gapped_findings: dict[str, gg.UngatedFile], required: str
    ) -> None:
        assert half_gapped_findings, "precondition: the half-gapped repository produced findings"
        for key, finding in half_gapped_findings.items():
            assert required in finding.message.lower(), (
                f"{key}'s message omits {required!r}. §Q3.7: a message that does not state the "
                f"registration/execution distinction promises a check this assertion does not "
                f"perform — and one still offering 'add a pinned exemption row' names a route F1 "
                f"DELETED, which is the same law turned inward.\n{finding.message}"
            )

    def test_the_disclaimer_is_one_contiguous_claim_not_scattered_keywords(
        self, half_gapped_findings: dict[str, gg.UngatedFile]
    ) -> None:
        # WRONG BUILD IT KILLS: a message that keyword-stuffs the five required substrings and
        # carries no actual disclaimer. Under the CONSUMER LAW this render is read by an agent
        # that will act on it without checking, so the registration/execution distinction must
        # be a sentence it can read — the two halves on ONE line — not two tokens a substring
        # test can find anywhere in the blob.
        for key, finding in half_gapped_findings.items():
            lines = [line.lower() for line in finding.message.splitlines()]
            carriers = [
                line
                for line in lines
                if MESSAGE_MUST_MENTION_REGISTRATION in line and MESSAGE_MUST_DISCLAIM_EXECUTION in line
            ]
            assert carriers, (
                f"{key}'s message never states the registration/execution distinction in one "
                f"place; the keywords are scattered, which a reader cannot assemble into a "
                f"claim.\n{finding.message}"
            )

    def test_the_message_names_the_configuration_file_a_reader_must_edit(
        self, half_gapped_findings: dict[str, gg.UngatedFile]
    ) -> None:
        types_message = half_gapped_findings["docs/eval/smoke_p8b.py:TYPES"].message
        execution_message = half_gapped_findings[
            "skills/lore-deploy/tests/test_port_probe.py:EXECUTION"
        ].message
        assert "typecheck.sh" in types_message and "MEMBERS" in types_message
        assert "pyproject.toml" in execution_message and "testpaths" in execution_message

    def test_every_message_opens_with_the_headline_a_reader_scans_for(
        self, half_gapped_findings: dict[str, gg.UngatedFile]
    ) -> None:
        for key, finding in half_gapped_findings.items():
            first_line = finding.message.splitlines()[0]
            assert first_line.startswith(_MESSAGE_HEADER), (
                f"{key}'s message opens with {first_line!r}; §Q3.7 fixes the headline so a gate "
                f"tail is scannable and so a forged row is detectable"
            )

    def test_the_message_names_the_scopes_of_the_repository_it_judged(self, tmp_path: Path) -> None:
        # ⚠ THE MESSAGE BUILDER IS A SEVENTH CALL SITE OF THE repo_root PROPERTY, and the ∀ over
        # readers (test_readers_answer_for_repo_root_not_for_the_process_cwd) covers six. A build
        # whose message scopes came from `Path.cwd()` instead of `repo_root` passed all 171 pins of
        # revision 5 — because `half_gapped_repository`'s roots and testpaths are strict SUBSETS of
        # this checkout's, so a message built from the WRONG repository satisfied every "is this
        # root in the message" assertion BY COINCIDENCE. Arithmetic alignment, in a fixture.
        #
        # This fixture's scopes are DISJOINT from the real ones, and the pin asserts both
        # directions: the fixture's scopes present, and no real-only scope leaking in.
        # Built field by field rather than through `_minimal_repository`, because that builder's
        # own paths live under `loremaster/` — a name this checkout also declares as a scope, so
        # the leak assertion below would fire on the finding's own path and prove nothing.
        repository = FixtureRepository(tmp_path)
        repository.write_typecheck_runner(members=["alpha_only"], include_decoy_comment=False)
        repository.write_pyproject(
            testpaths=["alpha_only/probes"],
            workspace_members=["alpha_only"],
            ruff_extend_exclude=["scratchpad", gg.ARCHIVED_RECEIPTS_ROOT],
            python_files=None,
            pytest_ini_extra=None,
            mypy_exclude=None,
            mypy_table_extra=None,
            mypy_overrides=[],
            omit_pytest_table=False,
        )
        repository.add_python_file("alpha_only/probes/test_alpha.py", body=_TEST_BODY)
        repository.add_python_file("beta_only/gamma_probe.py")
        repository.add_python_file("beta_only/test_gamma.py", body=_TEST_BODY)
        repository.add_python_file(
            f"{gg.ARCHIVED_RECEIPTS_ROOT}/2026-07-20-probes/probe_budget.py"
        )
        repository.stage()
        findings = findings_of(repository.root, exemptions=())
        assert findings, "precondition: beta_only/ is outside both of this fixture's scopes"
        fixture_scopes = set(gg.typecheck_roots(repository.root)) | set(
            gg.pytest_testpaths(repository.root)
        )
        real_only = (
            set(gg.typecheck_roots(REPO_ROOT)) | set(gg.pytest_testpaths(REPO_ROOT))
        ) - fixture_scopes
        assert real_only, "precondition: this checkout declares scopes the fixture does not"
        for finding in findings:
            # ⚠ The guard's own configuration ADDRESSES are repo-invariant constants, not scopes,
            # and one of them (`scripts/typecheck.sh`) CONTAINS a name this checkout also declares
            # as a scope — so a naive substring search over the whole message flags the runner's
            # path as a leaked scope. Measured: this pin's first draft failed on the CORRECT build
            # for exactly that reason, which is the false-positive direction, and a gate that
            # refuses honest code is a gate that gets switched off. Removing the addresses leaves
            # every OTHER occurrence intact, so a real leak — which lists scopes in its own clause
            # — still shows up.
            haystack = finding.message.replace(gg.RUNNER_RELATIVE_PATH, "").replace(
                gg.MANIFEST_RELATIVE_PATH, ""
            )
            leaked = sorted(scope for scope in real_only if scope in haystack)
            assert not leaked, (
                f"the message for {finding.path} ({finding.axis.name}) names scopes belonging to "
                f"THIS checkout and not to the repository it judged: {leaked}. A message built "
                f"from the process cwd teaches an agent to edit the wrong file.\n{finding.message}"
            )
        types_messages = [f.message for f in findings if f.axis is gg.GateAxis.TYPES]
        execution_messages = [f.message for f in findings if f.axis is gg.GateAxis.EXECUTION]
        assert types_messages and execution_messages, (
            "precondition: this fixture is half-gapped on BOTH axes, so both messages exist"
        )
        assert all("alpha_only" in message for message in types_messages)
        assert all("alpha_only/probes" in message for message in execution_messages)

    def test_the_axis_labels_are_the_ones_the_specification_uses(self) -> None:
        assert "LEG A" in gg.GateAxis.TYPES.label
        assert "LEG B" in gg.GateAxis.EXECUTION.label
        assert "types" in gg.GateAxis.TYPES.label.lower()
        assert "execution" in gg.GateAxis.EXECUTION.label.lower()


# ---------------------------------------------------------------------------
# 13. The instrument states its own threat model and bounds
# ---------------------------------------------------------------------------


class TestTheInstrumentStatesItsThreatModelAndBounds:
    """§Q3.5 / §Q3.2: *state the model IN the instrument*. Three audits of a previous gate
    each rendered a different verdict because nobody had written down who the gate is for;
    that absence cost two fix waves. And every bound is met deliberately or inherited
    silently — so each one carries a NAMED re-open trigger."""

    def test_the_threat_model_is_stated_and_appears_in_the_module_docstring(self) -> None:
        assert gg.THREAT_MODEL.strip(), "the instrument declares no threat model"
        assert gg.__doc__ is not None
        assert gg.THREAT_MODEL in gg.__doc__, (
            "the declared threat model does not appear in the module docstring, so a reader of "
            "the file does not meet it — it must be stated IN the instrument, not beside it"
        )

    def test_the_threat_model_names_its_subject_and_disclaims_being_a_security_boundary(
        self,
    ) -> None:
        model = gg.THREAT_MODEL.lower()
        assert "honest" in model, (
            f"the threat model must name WHO the gate is for; without it, 'a determined author "
            f"can delete this test' reads as a defect rather than as out of scope: {gg.THREAT_MODEL}"
        )
        assert "security" in model, (
            f"the threat model must say what it is NOT, or an auditor is entitled to call every "
            f"bypass a defect: {gg.THREAT_MODEL}"
        )

    def test_every_required_bound_is_stated(self) -> None:
        declared = {bound.identifier for bound in gg.STATED_BOUNDS}
        assert REQUIRED_BOUND_IDENTIFIERS <= declared, (
            f"bounds required by the ruling are not stated: "
            f"{sorted(REQUIRED_BOUND_IDENTIFIERS - declared)}"
        )

    def test_every_stated_bound_carries_a_named_re_open_trigger_and_appears_in_the_docstring(
        self,
    ) -> None:
        assert gg.__doc__ is not None
        # ⚠ A STATED BOUND, unlike an exemption row, may legitimately have NO ledger finding
        # (`finding` is optional), so a "must cite #NNN" rule would refuse honest bounds — and a
        # gate that refuses honest content is a gate that gets switched off. The mechanical
        # property that IS available is that a CONDITION is a phrase, not a token: this kills
        # `reopen_trigger="TBD"` (which passed a `.strip()` check) without inventing a
        # forbidden-word list. The message says exactly that and no more.
        triggers = [bound.reopen_trigger for bound in gg.STATED_BOUNDS]
        assert len(set(triggers)) == len(triggers), (
            f"two bounds share a re-open trigger, so at least one is boilerplate: {triggers}"
        )
        for bound in gg.STATED_BOUNDS:
            assert bound.summary.strip(), f"bound {bound.identifier!r} states nothing"
            assert len(bound.reopen_trigger.split()) > 1, (
                f"bound {bound.identifier!r}'s re-open trigger {bound.reopen_trigger!r} is a single "
                f"token, so it names no condition. NOTE: this checks the SHAPE of the trigger — it "
                f"cannot check that the condition is the right one, or that anyone watches it."
            )
            assert bound.summary in gg.__doc__, (
                f"bound {bound.identifier!r} is declared in STATED_BOUNDS but its summary does not "
                f"appear in the module docstring, so a reader of the file never meets it"
            )

    def test_the_lore_index_axis_is_a_named_bound_citing_its_finding(self) -> None:
        (bound,) = [b for b in gg.STATED_BOUNDS if b.identifier == "lore-index-axis"]
        assert bound.finding == LORE_INDEX_BOUND_FINDING, (
            f"the third gate direction (#233's, lore's index) must cite "
            f"{LORE_INDEX_BOUND_FINDING} as the finding whose landing re-opens it; got "
            f"{bound.finding!r}"
        )
        assert LORE_INDEX_BOUND_FINDING in bound.reopen_trigger


# ---------------------------------------------------------------------------
# 13b. The instrument is self-contained
# ---------------------------------------------------------------------------


class TestTheInstrumentIsSelfContained:
    """RULED: the instrument imports the standard library and nothing else.

    Two reasons, both mechanical rather than aesthetic. (1) It must typecheck as its own
    ``MEMBERS`` iteration with no project resolution of its own, which a project import would
    break. (2) A gate that imports the tree it grades acquires the tree's failure modes: a
    broken workspace member would take the guard down with it, and a guard that cannot run
    reports nothing — which reads as a clean tree.

    ⚠ **This is a claim about the INSTRUMENT, not about this contract file.** A pytest contract
    imports pytest by definition, and — under the two-file shape — it imports the instrument as
    a sibling, which mypy resolves only with a ``MYPYPATH`` for the root that holds them. That is
    the runner's job (its ``MEMBER_MYPYPATH`` map), and it is read back from the real runner by
    :meth:`TestConfigReadersComeFromTheRealFiles.
    test_every_declared_mypypath_entry_reconstructs_a_line_of_the_real_runner`. An earlier
    version of this docstring stated the rationale as if it governed both files; it did not, and
    the difference is a leg that exits non-zero. (It also cited a class that F1 deleted, which is
    the same defect one level up: a citation that does not resolve teaches a reader that a pin
    exists somewhere else.)
    """

    def _imported_roots(self) -> set[str]:
        """Every top-level module the instrument imports, at any nesting depth.

        Walks the whole AST rather than the module body, because a lazy import inside a
        function is a house idiom here (PLC0415 is ignored tree-wide) and is exactly where a
        project import would hide.
        """
        source = Path(gg.__file__).read_text(encoding="utf-8")
        roots: set[str] = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0, (
                    f"the instrument uses a relative import (level {node.level}), which makes it "
                    f"depend on a package layout and cannot resolve as a bare file iteration"
                )
                if node.module is not None:
                    roots.add(node.module.split(".")[0])
        return roots

    def test_the_instrument_imports_nothing_outside_the_standard_library(self) -> None:
        # DERIVED from sys.stdlib_module_names, never an allowlist someone maintains.
        imported = self._imported_roots()
        assert imported, "the instrument imports nothing at all — is this the right file?"
        outside = sorted(imported - sys.stdlib_module_names)
        assert not outside, (
            f"the instrument imports {outside}, which is outside the standard library. It must "
            f"typecheck as its own MEMBERS iteration with no MYPYPATH, and a gate that imports "
            f"the tree it grades goes down with that tree — reporting nothing, which reads clean."
        )

    def test_the_instrument_does_not_import_the_project(self) -> None:
        # The sharper half of the same property, and the one a reader will ask about: this is
        # NOT a ONE-IMPLEMENTATION violation. `registration_sites.py::declared_members` and the
        # instrument's `workspace_members` are two CONSUMERS of one registry
        # (`pyproject.toml`), not two copies of a policy — sharing-by-mutation passes at the
        # source, because changing pyproject changes both. Ruled; the import is forbidden.
        imported = self._imported_roots()
        project_names = {*gg.workspace_members(REPO_ROOT), "registration_sites", "scripts"}
        collisions = sorted(imported & project_names)
        assert not collisions, (
            f"the instrument imports project code {collisions}. Two small tomllib readers of one "
            f"registry are consumers, not policy clones — do not couple them."
        )


# ---------------------------------------------------------------------------
# 14. This guard is itself gated
# ---------------------------------------------------------------------------


class TestThisGuardIsItselfGated:
    """*A guard nobody runs is a hope with a filename* — and both of this repository's newest
    instruments sat outside ``testpaths`` until someone noticed. This one is collected from
    birth, and it says so mechanically rather than in a comment."""

    def test_this_contract_is_inside_a_testpaths_entry(self) -> None:
        relative = str(Path(__file__).resolve().relative_to(REPO_ROOT))
        testpaths = gg.pytest_testpaths(REPO_ROOT)
        assert any(gg.is_under(relative, testpath) for testpath in testpaths), (
            f"{relative} is outside every testpaths entry {testpaths} — the guard against "
            f"ungated ground would itself be ungated, which is the class it exists to close"
        )

    @pytest.mark.parametrize("which", ["the instrument", "this contract"])
    def test_both_of_this_instruments_files_are_inside_a_typecheck_root(self, which: str) -> None:
        # ⚠ **THE CONTRACT AGAINST HALF-GAPS SHIPPED WITH A HALF-GAP OF ITS OWN.** The pin above
        # covers the EXECUTION axis for one of the two files; the TYPES axis was covered by a class
        # F1 deleted, and the module docstring went on citing it — so the obligation was
        # unpinned and a dangling citation told a reader otherwise. This is the LEG A counterpart,
        # over BOTH files, which is the shape the rest of this file demands of everything else:
        # *three of the four historical instances of this class were HALF-gaps.*
        source = Path(gg.__file__) if which == "the instrument" else Path(__file__)
        relative = str(source.resolve().relative_to(REPO_ROOT))
        roots = gg.typecheck_roots(REPO_ROOT)
        assert any(gg.is_under(relative, root) for root in roots), (
            f"{relative} is outside every typecheck root {roots} declared in "
            f"{gg.RUNNER_RELATIVE_PATH} — mypy never reads it. Registration of this instrument is "
            f"decided by that runner and by nothing else"
        )

    def test_the_guard_grants_its_own_files_no_special_exemption(self, tmp_path: Path) -> None:
        # WRONG BUILD #2, and the reason the ruled fix is a MECHANISM rather than a carve-out.
        # The recursion the sweep escalated (an instrument landing in an ungated tree) is closed
        # by giving the instrument its own MEMBERS entry — a root covers itself. A build that
        # instead hardcodes "except my own path" passes its own gate forever, silently, and the
        # next instrument to land in the same tree inherits nothing.
        repository = _minimal_repository(
            tmp_path,
            extra_files=["tools/gated_ground.py", "tools/test_gated_ground.py"],
        )
        verdicts = assert_every_tracked_file_is_accounted_for(
            repository.root, exemptions=()
        )
        for path in ("tools/gated_ground.py", "tools/test_gated_ground.py"):
            assert fates_of(verdicts, path)[gg.GateAxis.TYPES] is gg.Fate.UNGATED, (
                f"{path} is under no gate and carries no pinned exemption, yet the guard did not "
                f"report it — the guard is exempting itself by name"
            )

    def test_every_tracked_file_here_including_this_guard_is_classified(self) -> None:
        # Once committed, this contract and its instrument are ordinary committed ground and
        # are accounted for like everything else (the totality helper proves it over the whole
        # checkout; this states the intent so a reader meets it deliberately).
        classified = {verdict.path for verdict in gg.classify(REPO_ROOT, exemptions=())}
        assert set(gg.tracked_python_files(REPO_ROOT)) == classified

    def test_the_guard_names_no_path_of_its_own_anywhere_in_its_source(self) -> None:
        # WRONG BUILD #2, and the assertion behind a docstring claim that previously had none.
        # A guard that hardcodes `if path in {"scripts/gated_ground.py", …}: COVERED` reports
        # itself covered forever — delete the MEMBERS entry and the recursion re-opens with
        # every pin still green. Measured: that build passed all 130 pins of revision 2.
        instrument = Path(gg.__file__)
        contract = Path(__file__)
        forbidden = {
            instrument.name,
            instrument.stem,
            contract.name,
            contract.stem,
            str(instrument.resolve().relative_to(REPO_ROOT)),
            str(contract.resolve().relative_to(REPO_ROOT)),
        }
        literals = {
            node.value
            for node in ast.walk(ast.parse(instrument.read_text(encoding="utf-8")))
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        named = sorted(literals & forbidden)
        assert not named, (
            f"the guard's own source names its own files {named}. Coverage of this instrument is "
            f"decided by scripts/typecheck.sh and by nothing else; a literal here makes the guard "
            f"lie about itself and stop tracking the runner."
        )

    def test_the_guard_returns_data_rather_than_an_exit_code(
        self, half_gapped_repository: FixtureRepository
    ) -> None:
        # §Q3.1: no script-with-wrapper. A wrapper is a seam where the derivation silently
        # no-ops while the wrapper still prints green, so the assertion must consume the
        # derivation's VALUES in-process, not a subprocess's exit status.
        findings = findings_of(
            half_gapped_repository.root, exemptions=()
        )
        assert isinstance(findings, list)
        assert findings and all(isinstance(finding, gg.UngatedFile) for finding in findings)
        assert all(isinstance(finding.message, str) and finding.message for finding in findings)


# ---------------------------------------------------------------------------
# 16. THE SERVED SURFACE IS ONE DERIVATION (revision 6 / ruling R9)
# ---------------------------------------------------------------------------


class TestTheServedSurfaceIsOneDerivation:
    """RULED (R9): make the inconsistency UNREPRESENTABLE rather than forbidden.

    **The hole this closes needed one wrong build and no cleverness.** A build whose
    ``is_clean`` / ``exit_code`` / ``render()`` ignored ``findings`` entirely — serving
    ``findings=1``, ``is_clean=True``, ``exit_code=0`` and the *"every tracked module is
    registered"* sentence — passed all 171 pins of revision 5, because the served surface was
    pinned for BLIND states and for CLEAN trees and never for a tree WITH FINDINGS. That is a
    guard reporting a clean tree while holding a finding: by this repository's hard definition of
    trust, a consumer who acts on it without checking is wrong in a way the response did not name.

    **The fix is structural, and the structure is worth stating because it is what makes the pins
    below short.** There is ONE classifier, :attr:`gg.Verdict.state`; the process exit code IS
    that state's enum value, so there is no second place for the mapping to live and therefore
    nowhere for it to drift; ``is_clean`` is an identity test against one member; ``render()``
    dispatches on the state. And the incoherent cell — findings AND blind sources at once — is
    refused at construction, so the four-cell product of the two fields has three legal cells
    rather than a convention.

    ⚠ **Deriving the three answers from one state is not proof that they DO.** Nothing about the
    shape stops a build from re-deriving one of them privately, which is *routing is not sharing*
    at property granularity. So the load-bearing pin here is a MUTATION:
    :meth:`test_every_served_answer_moves_when_the_one_classifier_moves` replaces ``state`` and
    requires every served answer to change with it, quantified over the served members the
    dataclass actually has rather than over the three someone listed.
    """

    @staticmethod
    def _finding() -> gg.UngatedFile:
        return gg.UngatedFile(
            path="docs/consult/coherence_check.py",
            axis=gg.GateAxis.TYPES,
            message="UNGATED GROUND (LEG A — types): a finding, standing in for the real thing.",
        )

    def test_the_four_cell_product_of_the_two_fields_has_exactly_one_answer_each(self) -> None:
        # ∀ over the PRODUCT, computed rather than listed — the cell that shipped the false clear
        # (findings present, nothing blind) is in it because the product contains it, not because
        # anyone remembered the case.
        cells = [
            (findings, blind_sources)
            for findings in ((), (self._finding(),))
            for blind_sources in ((), ("the runner could not be read",))
        ]
        assert len(cells) == 4, "the product is 2x2; a shorter list is not the product"
        observed: dict[tuple[bool, bool], str] = {}
        for findings, blind_sources in cells:
            key = (bool(findings), bool(blind_sources))
            if findings and blind_sources:
                # THE INCOHERENT CELL. A verdict cannot hold a finding it derived AND name an
                # input it could not derive: the derivation refuses before it classifies, so this
                # combination describes no world. Refused at construction rather than left to a
                # convention no reader of the type can see.
                with pytest.raises(gg.IncoherentVerdict):
                    gg.Verdict(findings=findings, blind_sources=blind_sources)
                observed[key] = "refused"
                continue
            verdict = gg.Verdict(findings=findings, blind_sources=blind_sources)
            observed[key] = verdict.state.name
        assert observed == {
            (False, False): gg.VerdictState.GATED_GROUND.name,
            (True, False): gg.VerdictState.UNGATED_GROUND.name,
            (False, True): gg.VerdictState.BLIND.name,
            (True, True): "refused",
        }, f"the product's cells do not map one-to-one onto the states: {observed}"

    def test_blindness_dominates_a_finding_even_in_the_shape_that_cannot_be_constructed(
        self,
    ) -> None:
        # ⚠ FOUND BY MY OWN WRONG-BUILD PASS (WB3): flipping the classifier's order — findings
        # tested BEFORE blind sources — passed all 307 pins, because the only input that can tell
        # the two orders apart is the incoherent cell, and that cell is refused at construction.
        # The branch was therefore DEAD CODE, which is the shape an auditor is entitled to call a
        # defect.
        #
        # It is kept as DEFENCE IN DEPTH — if the construction refusal is ever relaxed, blindness
        # must still dominate, because a verdict that could not read an input has no standing to
        # report what it found — and it is made REACHABLE here rather than left unpinned. The
        # bypass is deliberate and is the only way to reach it: `dataclasses.replace` and the
        # constructor both go through the refusal.
        verdict = gg.Verdict(findings=(), blind_sources=("the runner could not be read",))
        object.__setattr__(verdict, "findings", (self._finding(),))
        assert verdict.state is gg.VerdictState.BLIND, (
            f"with both fields populated the verdict reported {verdict.state.name}: a finding "
            f"derived from a tree the guard could not fully read would be served as if the read "
            f"had succeeded"
        )
        assert verdict.exit_code == gg.VerdictState.BLIND.exit_code
        assert not verdict.is_clean

    def test_the_exit_code_is_the_state_itself_not_a_second_mapping(self) -> None:
        # ONE IMPLEMENTATION at its smallest: the exit code is the enum member's VALUE, so a
        # build cannot hold a state of BLIND and an exit code of 0 — there is no second table to
        # disagree with the first. Every state's code is distinct, or two answers collapse.
        codes = {state: state.exit_code for state in gg.VerdictState}
        assert len(set(codes.values())) == len(codes), (
            f"two verdict states share an exit code, so a caller keyed on the code cannot tell "
            f"them apart: {codes}"
        )
        assert gg.VerdictState.GATED_GROUND.exit_code == 0, (
            "a clean tree must exit zero, or the gate fails on every honest tree and is switched "
            "off within a week"
        )
        assert gg.VerdictState.BLIND.exit_code != 0 and gg.VerdictState.UNGATED_GROUND.exit_code != 0
        for state in gg.VerdictState:
            assert state.exit_code == state.value, (
                f"{state.name}'s exit code {state.exit_code} is not its own value {state.value!r} "
                f"— a second mapping exists and can drift from this one"
            )

    def test_every_served_answer_moves_when_the_one_classifier_moves(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ⚠ THE MUTATION PROOF OF SHARING, and the only pin here that can catch *routing is not
        # sharing*: replace the ONE classifier and require every served answer to follow. A build
        # whose `is_clean` reads `self.findings` directly keeps answering True under this patch —
        # green on every other pin in this class, red here.
        #
        # Quantified over the served members the dataclass ACTUALLY has (public, non-field), so a
        # fourth served answer added tomorrow is covered by running the suite rather than by
        # anyone remembering to extend a list of three.
        clean = gg.Verdict(findings=(), blind_sources=())
        field_names = {field.name for field in dataclasses.fields(clean)}
        served = sorted(
            name
            for name in dir(type(clean))
            if not name.startswith("_") and name not in field_names and name != "state"
        )
        assert served, "the verdict serves nothing at all — is this the right object?"

        def answer(name: str) -> object:
            attribute = getattr(clean, name)
            return attribute() if callable(attribute) else attribute

        healthy = {name: answer(name) for name in served}
        monkeypatch.setattr(
            gg.Verdict, "state", property(lambda self: gg.VerdictState.BLIND), raising=True
        )
        unchanged = [name for name in served if answer(name) == healthy[name]]
        assert not unchanged, (
            f"these served answers did not change when the ONE classifier was replaced, so they "
            f"are deriving the verdict privately rather than reading it: {unchanged}. Routing is "
            f"not sharing — and a private copy of the classification is exactly how a build "
            f"served findings=1 with is_clean=True through all 171 pins of revision 5."
        )

    def test_a_tree_with_findings_serves_a_verdict_that_is_not_clean(self, tmp_path: Path) -> None:
        # THE DUAL OF BLINDNESS-MONOTONICITY, end to end rather than on a constructed object: the
        # pin above proves the OBJECT couples its answers; this proves `ungated_ground` puts the
        # findings INTO the object it serves. A build that classified correctly and then served an
        # empty verdict would pass the object-level pin and fail here.
        repository = _minimal_repository(tmp_path, extra_files=["docs/consult/coherence_check.py"])
        verdict = gg.ungated_ground(repository.root, exemptions=())
        assert verdict.findings, (
            "precondition: docs/consult/ is under no typecheck root, so this tree HAS a finding"
        )
        assert verdict.state is gg.VerdictState.UNGATED_GROUND
        assert not verdict.is_clean, "a verdict holding a finding is not clean"
        assert verdict.exit_code != 0, "a verdict holding a finding must not exit zero"
        rendered = verdict.render()
        assert "docs/consult/coherence_check.py" in rendered, (
            f"the render does not name the file it found, so a consumer cannot act on it: "
            f"{rendered}"
        )
        clean_control = _repository_beside(tmp_path, "clean_control")
        clean_verdict = gg.ungated_ground(clean_control.root, exemptions=())
        assert clean_verdict.is_clean, (
            f"POSITIVE CONTROL: the same builder without the ungated file must be clean, or the "
            f"assertions above fire for a fixture reason\n{clean_verdict.render()}"
        )
        assert rendered != clean_verdict.render(), (
            "THE FALSE CLEAR: a tree with a finding served bytes identical to a clean tree"
        )

    def test_the_clean_render_claims_only_what_the_two_legs_prove(self) -> None:
        # The served CLEAN sentence is prose an agent acts on, and it is the one render nobody
        # reads carefully because it means "nothing to do". It must name both axes — a sentence
        # claiming "every committed .py is registered" over a guard that also judges COLLECTION
        # over-claims on the axis that is measured rather than declared.
        clean = gg.Verdict(findings=(), blind_sources=()).render().lower()
        for required in ("registered", "collect"):
            assert required in clean, (
                f"the clean render omits {required!r}, so it does not say which two questions "
                f"were answered: {clean!r}"
            )
        assert "every" in clean, (
            f"the clean render must state its own quantifier — a clean verdict over an EMPTY "
            f"enumeration is the anti-vacuity hazard, and the sentence is what a reader trusts: "
            f"{clean!r}"
        )


# ---------------------------------------------------------------------------
# 17. THE DERIVED FAILURE SET (revision 6 / ruling R9)
# ---------------------------------------------------------------------------


def _environment_variables_the_instrument_reads() -> set[str]:
    """Every environment variable name the instrument reads, DERIVED from its own AST.

    Used to check a stated bound against the code rather than against prose: a bound enumerating
    what the memo key does not cover must not name a variable the key demonstrably reads.
    """
    names: set[str] = set()
    for node in ast.walk(_instrument_ast()):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        reads_environment = (
            isinstance(target, ast.Attribute)
            and target.attr == "get"
            and isinstance(target.value, ast.Attribute)
            and target.value.attr == "environ"
        ) or (isinstance(target, ast.Attribute) and target.attr == "getenv")
        if not reads_environment or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            names.add(first.value)
    return names


def _instrument_ast() -> ast.Module:
    """The instrument's own source, parsed. Read from ``gg.__file__``, never from a path."""
    return ast.parse(Path(gg.__file__).read_text(encoding="utf-8"))


def blind_doors_declared_by_the_instrument() -> dict[str, int]:
    """Every door the guard can refuse through, DERIVED from its own AST — never a list.

    A door is a call of ``_blind`` whose FIRST argument is a string literal identity. The set is
    READ OUT OF THE SOURCE, which is the entire difference between this and the four-value
    parametrization it replaces: quantified over a hand-written door list, blindness-monotonicity
    held for 6 of 26 states and a build honouring exactly the pinned five served **17 false
    clears** at 171 passed. A door added tomorrow is in this set without anyone editing this
    file, and :meth:`TestTheDerivedFailureSetIsFullyProbed.
    test_every_declared_door_is_reached_by_a_constructed_state` then demands a state for it.

    Returns door identity -> line number (the line is for the failure message only; the IDENTITY
    is the key, because a line number is stale the moment anyone inserts a line above it).
    """
    doors: dict[str, int] = {}
    problems: list[str] = []
    for node in ast.walk(_instrument_ast()):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_blind"
        ):
            continue
        first = node.args[0] if node.args else None
        if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
            problems.append(
                f"line {node.lineno}: _blind(...) carries no string-literal door identity, so "
                f"this refusal is invisible to the derivation and nothing demands a state for it"
            )
            continue
        door = str(first.value)
        if door in doors:
            problems.append(
                f"line {node.lineno}: door {door!r} is already used at line {doors[door]} — two "
                f"refusals sharing an identity are one door in this derivation, so probing one "
                f"reads as probing both"
            )
        else:
            doors[door] = node.lineno
    assert not problems, "the door derivation cannot see every refusal:\n  " + "\n  ".join(problems)
    assert doors, (
        "the derivation found NO doors at all. That is a broken instrument, not a guard that "
        "cannot go blind — do not read any coverage verdict below it"
    )
    return doors


def _refuse_to_execute(command: Sequence[str]) -> object:
    """Stand in for a collector subprocess that cannot be executed at all (#131's shape)."""
    raise OSError(f"the collector subprocess could not be executed: {list(command)[:3]}")


def _blank_collector_output(command: Sequence[str]) -> object:
    """Stand in for a collector that exits zero and names nothing — a zero that is not a result."""
    return subprocess.CompletedProcess(list(command), 0, stdout="", stderr="")


def _intercept_collector_subprocess(
    monkeypatch: pytest.MonkeyPatch,
    *,
    observed: list[list[str]],
    instead: Callable[[Sequence[str]], object] | None = None,
) -> None:
    """Intercept ONLY the collector subprocess, delegating every other call to the real one.

    ONE implementation, because three pins need the same POLICY — *which* subprocess is the
    collector, and that everything else (git, the fixture builder's own ``git init``) must still
    run for real. Three private copies of that decision is how one of them ends up recognising the
    collector differently from its siblings, and then a pin measures a subprocess that never ran.

    ``observed`` records every collector command seen, so a caller can count them; ``instead``
    replaces the collector's behaviour when a state needs it to fail.
    """
    real_run = subprocess.run

    def intercepted(*arguments: Any, **keywords: Any) -> Any:
        requested = arguments[0] if arguments else keywords["args"]
        command = [str(part) for part in requested]
        if "--collect-only" not in command:
            return real_run(*arguments, **keywords)
        observed.append(command)
        if instead is None:
            return real_run(*arguments, **keywords)
        return instead(command)

    monkeypatch.setattr(subprocess, "run", intercepted)


@dataclasses.dataclass(frozen=True)
class BrokenState:
    """One CONSTRUCTED broken world-state, labelled with the dependency and verb it breaks.

    **Constructed, never reasoned about.** A missed world-state is discoverable by accident; a
    false belief about the guard's own semantics is self-sealing, and the only instrument that
    breaks it is execution. So each of these BUILDS the state and the pins byte-diff what the
    guard serves against a healthy tree — identical bytes on a broken state is a false clear and
    a STOP, never a passing row.
    """

    dependency: str
    verb: str
    door: str
    build: Callable[[Path, pytest.MonkeyPatch], Path]


_StateBuilder = Callable[[Path, pytest.MonkeyPatch], Path]
_StateRegistrar = Callable[[str, str, str], Callable[[_StateBuilder], _StateBuilder]]


def _registrar(states: list[BrokenState]) -> _StateRegistrar:
    """A decorator factory that appends one labelled :class:`BrokenState` to ``states``.

    ONE registrar shared by every group below, so a group cannot quietly label its states
    differently from its siblings — the labels are what two separate ∀ pins read.
    """

    def state(dependency: str, verb: str, door: str) -> Callable[[_StateBuilder], _StateBuilder]:
        def register(build: _StateBuilder) -> _StateBuilder:
            states.append(BrokenState(dependency=dependency, verb=verb, door=door, build=build))
            return build

        return register

    return state


def _runner_and_manifest_states() -> tuple[BrokenState, ...]:
    """Broken states of the two configuration files the guard parses."""
    states: list[BrokenState] = []
    state = _registrar(states)
    runner = gg.RUNNER_RELATIVE_PATH
    manifest = gg.MANIFEST_RELATIVE_PATH

    @state(runner, "missing", "runner-unreadable")
    def _runner_missing(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        return _minimal_repository(tmp_path, omit_typecheck_runner=True).root

    @state(runner, "no-declaration", "members-declaration-absent")
    def _members_absent(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        return _minimal_repository(tmp_path, members=None).root

    @state(runner, "duplicated", "members-declaration-duplicated")
    def _members_duplicated(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        repository = _minimal_repository(tmp_path, members=["loremaster", "docs"])
        declaration = repository.root / "scripts" / "typecheck.sh"
        declaration.write_text(
            declaration.read_text(encoding="utf-8") + "\nMEMBERS=(loremaster)\n", encoding="utf-8"
        )
        return repository.root

    @state(runner, "empty", "members-empty")
    def _members_empty(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        return _minimal_repository(tmp_path, members=[]).root

    @state(runner, "whole-tree", "members-entry-widens-to-the-whole-tree")
    def _members_wildcard(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        # `./`, not `.` — the spelling revision 5 pinned on ONE axis, which the reference build
        # itself false-cleared on.
        return _minimal_repository(tmp_path, members=["loremaster", "./"]).root

    @state(runner, "phantom", "members-entry-names-nothing")
    def _members_phantom(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        return _minimal_repository(tmp_path, members=["loremaster", "deleted_member"]).root

    @state(runner, "duplicated-map", "mypypath-declaration-duplicated")
    def _mypypath_duplicated(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        repository = _minimal_repository(tmp_path)
        declaration = repository.root / "scripts" / "typecheck.sh"
        declaration.write_text(
            declaration.read_text(encoding="utf-8")
            + '\ndeclare -A MEMBER_MYPYPATH=([loremaster]="a")\n'
            + '\ndeclare -A MEMBER_MYPYPATH=([loremaster]="b")\n',
            encoding="utf-8",
        )
        return repository.root

    @state(manifest, "missing", "manifest-unreadable")
    def _manifest_missing(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        repository = _minimal_repository(tmp_path)
        (repository.root / manifest).unlink()
        return repository.root

    @state(manifest, "malformed", "manifest-unparseable")
    def _manifest_malformed(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        repository = _minimal_repository(tmp_path)
        (repository.root / manifest).write_text("[tool.pytest\nnot toml at all", encoding="utf-8")
        return repository.root

    @state(manifest, "table-absent", "declared-table-absent")
    def _pytest_table_absent(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        return _minimal_repository(tmp_path, omit_pytest_table=True).root

    @state(manifest, "key-absent", "declared-key-absent")
    def _testpaths_absent(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        return _minimal_repository(tmp_path, testpaths=None).root

    @state(manifest, "empty", "declared-paths-empty")
    def _testpaths_empty(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        return _minimal_repository(tmp_path, testpaths=[]).root

    @state(manifest, "not-a-list", "declared-paths-not-a-list")
    def _testpaths_not_a_list(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        repository = _minimal_repository(tmp_path)
        repository.write_pyproject(
            testpaths=None,
            workspace_members=["loremaster"],
            ruff_extend_exclude=["scratchpad", gg.ARCHIVED_RECEIPTS_ROOT],
            python_files=None,
            pytest_ini_extra={"testpaths": "loremaster/tests"},
            mypy_exclude=None,
            mypy_table_extra=None,
            mypy_overrides=[],
            omit_pytest_table=False,
        )
        repository.stage()
        return repository.root

    @state(manifest, "entry-not-a-path", "declared-paths-entry-is-not-a-path")
    def _testpaths_entry_not_a_path(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        repository = _minimal_repository(tmp_path)
        repository.write_pyproject(
            testpaths=None,
            workspace_members=["loremaster"],
            ruff_extend_exclude=["scratchpad", gg.ARCHIVED_RECEIPTS_ROOT],
            python_files=None,
            pytest_ini_extra={"testpaths": ["loremaster/tests", 7]},
            mypy_exclude=None,
            mypy_table_extra=None,
            mypy_overrides=[],
            omit_pytest_table=False,
        )
        repository.stage()
        return repository.root

    @state(manifest, "whole-tree", "testpath-widens-to-the-whole-tree")
    def _testpath_wildcard(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        return _minimal_repository(tmp_path, testpaths=["loremaster/tests", "./."]).root

    @state(manifest, "phantom", "testpath-is-not-a-directory")
    def _testpath_phantom(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        return _minimal_repository(tmp_path, testpaths=["loremaster/tests", "docs/eval"]).root

    @state(manifest, "vacuous-patterns", "python-files-empty")
    def _python_files_empty(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        return _minimal_repository(tmp_path, python_files=[]).root

    @state(manifest, "unmodelled", "mypy-configuration-unmodelled")
    def _mypy_unmodelled(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        return _minimal_repository(tmp_path, mypy_exclude=["loremaster/store/.*"]).root

    @state(manifest, "mypy-table-absent", "mypy-configuration-unmodelled")
    def _mypy_table_absent(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        # ⚠ FOUND BY MY OWN WRONG-BUILD PASS (WB14): the refusal for an ABSENT [tool.mypy] table
        # shipped with no state constructing it, because every fixture in this file writes that
        # table and the refusal SHARES a door with the unmodelled-setting one — so door coverage
        # was satisfied without it. With the table absent, mypy's search does not stop at the
        # manifest: it falls through to setup.cfg, then to an ancestor directory, then to
        # ~/.config/mypy/config, so LEG A's model would be of a file nobody reads.
        repository = _minimal_repository(tmp_path)
        manifest_path = repository.root / gg.MANIFEST_RELATIVE_PATH
        before = manifest_path.read_text(encoding="utf-8")
        table = '[tool.mypy]\npython_version = "3.14"\nstrict = true\n'
        assert before.count(table) == 1, (
            "the fixture builder no longer writes the [tool.mypy] table in the shape this state "
            "removes, so the removal would silently no-op and the state would probe nothing"
        )
        manifest_path.write_text(before.replace(table, ""), encoding="utf-8")
        assert "[tool.mypy]" not in manifest_path.read_text(encoding="utf-8")
        repository.stage()
        return repository.root

    @state(manifest, "receipts-unanchored", "receipts-root-is-not-lint-excluded")
    def _receipts_unanchored(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        return _minimal_repository(tmp_path, ruff_extend_exclude=["scratchpad"]).root

    return tuple(states)


def _dependency_states() -> tuple[BrokenState, ...]:
    """Broken states of the guard's non-parsed dependencies: the archive, git, the collector."""
    states: list[BrokenState] = []
    state = _registrar(states)

    @state(gg.ARCHIVED_RECEIPTS_ROOT, "vacuous", "receipts-class-matches-nothing")
    def _receipts_vacuous(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        repository = FixtureRepository(tmp_path)
        repository.write_typecheck_runner(members=["loremaster"], include_decoy_comment=False)
        repository.write_pyproject(
            testpaths=["loremaster/tests"],
            workspace_members=["loremaster"],
            ruff_extend_exclude=["scratchpad", gg.ARCHIVED_RECEIPTS_ROOT],
            python_files=None,
            pytest_ini_extra=None,
            mypy_exclude=None,
            mypy_table_extra=None,
            mypy_overrides=[],
            omit_pytest_table=False,
        )
        repository.add_python_file("loremaster/tests/test_store_lease.py", body=_TEST_BODY)
        repository.stage()  # no committed file under the receipts root at all
        return repository.root

    @state("git", "binary-missing", "git-is-unexecutable")
    def _git_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        repository = _minimal_repository(tmp_path)
        monkeypatch.setenv("PATH", str(tmp_path / "no_binaries_here"))
        return repository.root

    @state("git", "not-a-repository", "git-command-failed")
    def _not_a_repository(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        plain = tmp_path / "not_a_repository"
        plain.mkdir()
        return plain

    @state("git", "no-python-tracked", "tracked-python-files-empty")
    def _nothing_tracked(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        repository = FixtureRepository(tmp_path)
        repository.add_raw_file("README.md", body="a repository with no Python in it\n")
        repository.stage()
        return repository.root

    @state("collector", "failing", "collector-exit-code")
    def _collector_fails(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> Path:
        repository = _minimal_repository(tmp_path)
        (repository.root / "loremaster" / "tests" / "conftest.py").write_text(
            "raise RuntimeError('a conftest that cannot import')\n", encoding="utf-8"
        )
        repository.stage()
        return repository.root

    @state("collector", "binary-missing", "collector-is-unexecutable")
    def _collector_unexecutable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        repository = _minimal_repository(tmp_path)
        _intercept_collector_subprocess(monkeypatch, observed=[], instead=_refuse_to_execute)
        return repository.root

    @state("collector", "output-unreadable", "collector-output-is-not-the-shape-read")
    def _collector_output_unreadable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        repository = _minimal_repository(tmp_path)
        _intercept_collector_subprocess(monkeypatch, observed=[], instead=_blank_collector_output)
        return repository.root

    @state("collector", "inputs-unreadable", "collector-inputs-unreadable")
    def _collector_inputs_unreadable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        # The memo's own dependency. A fingerprint that swallows an unreadable input serves a
        # PARTIAL key, and a partial key collides with the healthy one — a stale answer wearing a
        # fresh receipt, which is the price R10 said must be paid rather than assumed.
        repository = _minimal_repository(tmp_path)
        real_read = Path.read_bytes

        def refuse(self: Path) -> bytes:
            if self.suffix == ".py" and "tests" in self.parts:
                raise OSError("a collector input could not be read")
            return real_read(self)

        monkeypatch.setattr(Path, "read_bytes", refuse)
        return repository.root

    return tuple(states)


def _shadowed_configuration_states() -> tuple[BrokenState, ...]:
    """One broken state per configuration filename that OUTRANKS the manifest, DERIVED.

    The filename list comes from the two gate tools' own declared search orders, so a vendor that
    adds a candidate adds a probe here without anyone editing this file.
    """
    states: list[BrokenState] = []
    state = _registrar(states)

    for filename in shadowing_configuration_filenames():
        @state(filename, "present", "gate-configuration-is-shadowed")
        def _shadowed(
            tmp_path: Path, _monkeypatch: pytest.MonkeyPatch, filename: str = filename
        ) -> Path:
            # #107 VERBATIM: a configuration file the TOOL reads and this guard does not. The
            # content is a REAL switch-off — an `exclude` for mypy, a redirected `testpaths` for
            # pytest — so the state is the outage rather than a shape resembling it. (The guard
            # refuses on PRESENCE, before content matters; the realistic body is what makes the
            # failure message legible to whoever meets it.)
            repository = _minimal_repository(tmp_path)
            if "mypy" in filename:
                body = "[mypy]\nexclude = loremaster/\n"
            elif filename.endswith(".toml"):
                body = '[pytest]\ntestpaths = ["nowhere"]\n'
            else:
                body = "[pytest]\ntestpaths = nowhere\n"
            (repository.root / filename).write_text(body, encoding="utf-8")
            repository.stage()
            return repository.root

    return tuple(states)


def _broken_states() -> tuple[BrokenState, ...]:
    """Every broken state this contract constructs, one per declared door.

    ⚠ **BOUND, stated so this table does not over-claim about itself:** it is complete over the
    doors the instrument DECLARES (checked both ways, mechanically) and over the configuration
    files the two gate tools declare (checked against their own constants). A world-state the
    guard has no door for and no vendor names is not in it — that is the residual the byte-diff
    legs exist to catch, and every false clear found later is a re-open trigger for this table
    rather than a retroactive pass for it.
    """
    return (
        *_runner_and_manifest_states(),
        *_dependency_states(),
        *_shadowed_configuration_states(),
    )


BROKEN_STATES: tuple[BrokenState, ...] = _broken_states()


class TestTheDerivedFailureSetIsFullyProbed:
    """RULED (R9): quantify over the DERIVED failure set, never over a list written down here.

    **What this replaces, measured.** Revision 5 parametrized blindness-monotonicity over four
    strings — ``["members", "testpath", "git", "manifest"]`` — and named three entry-point pins.
    A build honouring exactly those five doors and swallowing every other refusal into a CLEAN
    verdict passed **171 passed / 0 failed** while serving **17 false clears**, each rendering
    bytes IDENTICAL to a healthy tree. The list was the defect: *the forbidden set is unbounded,
    so stop enumerating it and enforce the property.*

    The door set here is READ OUT OF THE INSTRUMENT'S AST, and coverage is a CHECKED VARIABLE in
    both directions: a door with no constructed state is RED, and a constructed state that reaches
    no door — or the wrong one — is RED. That is what makes the ∀ real rather than decorative: a
    guard that grows a new refusal grows a new obligation at the same instant.
    """

    @staticmethod
    def _healthy_render(tmp_path: Path) -> str:
        control = _repository_beside(tmp_path, "healthy_control")
        verdict = gg.ungated_ground(control.root, exemptions=())
        assert verdict.is_clean, (
            f"precondition: the control tree is clean, or every byte-diff below fires for a "
            f"fixture reason\n{verdict.render()}"
        )
        return verdict.render()

    def test_the_door_derivation_sees_the_instruments_refusals(self) -> None:
        # POSITIVE CONTROL for the derivation itself, and it must be a SECOND derivation rather
        # than a count of anything downstream: an AST walk that silently matched a subset would
        # make every ∀ below quantify over less than it claims, and nothing else in this class can
        # see that. (This pin's first draft compared the door count to the number of constructed
        # STATES, which is not a control at all — several states legitimately share one door, so
        # the comparison was arithmetic that happened to hold rather than a property.)
        doors = blind_doors_declared_by_the_instrument()
        source = Path(gg.__file__).read_text(encoding="utf-8")
        textual = len(re.findall(r"(?<!def )\b_blind\(", source))
        assert len(doors) == textual, (
            f"the AST derivation found {len(doors)} refusals and a textual scan of the same file "
            f"found {textual}. Two derivations of one population disagree, so at least one is "
            f"blind — and the ∀ pins below quantify over whichever is short.\n"
            f"AST doors: {sorted(doors)}"
        )

    def test_no_refusal_bypasses_the_one_door_helper(self) -> None:
        # THE COMPLETENESS CLAUSE, and without it the derivation is a name list again: a refusal
        # constructed directly rather than through the helper carries no identity, so nothing
        # demands a state for it and it is exempt from every ∀ in this class — silently.
        tree = _instrument_ast()
        inside_the_helper = {
            id(inner)
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_blind"
            for inner in ast.walk(node)
        }
        assert inside_the_helper, (
            "the scan cannot find the door helper itself, so it would report every legitimate "
            "construction as a bypass — the instrument is broken, not the code"
        )
        bypasses = sorted(
            f"line {node.lineno}"
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == gg.GuardIsBlind.__name__
            and id(node) not in inside_the_helper
        )
        assert not bypasses, (
            f"these sites construct {gg.GuardIsBlind.__name__} directly instead of through the "
            f"one door helper, so their refusals carry no identity and no constructed state is "
            f"demanded for them: {bypasses}"
        )

    def test_every_declared_door_is_reached_by_a_constructed_state(self) -> None:
        # BOTH DIRECTIONS, which is the direction people leave out: an unprobed door is a refusal
        # nobody has ever seen fire, and a state naming a door that does not exist is a probe
        # aimed at nothing — the same both-ways diff scripts/mutation_proof.py performs on
        # declared-RED node ids.
        declared = set(blind_doors_declared_by_the_instrument())
        probed = {state.door for state in BROKEN_STATES}
        assert declared == probed, (
            f"the derived door set and the constructed states disagree.\n"
            f"  doors with NO constructed state (unprobed refusals — a new door was added "
            f"without a state): {sorted(declared - probed)}\n"
            f"  states naming NO declared door (a probe aimed at nothing, or a renamed door): "
            f"{sorted(probed - declared)}"
        )

    def test_every_dependency_the_guard_names_is_probed(self) -> None:
        # The other derivation, and it catches what the door set structurally cannot: a
        # dependency added WITHOUT a refusal. Addresses come from the instrument's own constants,
        # so a new input announces itself here rather than in an outage.
        addresses = {
            value
            for name, value in vars(gg).items()
            if name.endswith("_RELATIVE_PATH") and isinstance(value, str)
        }
        addresses |= set(shadowing_configuration_filenames())
        probed = {state.dependency for state in BROKEN_STATES}
        assert addresses, "the instrument names no input addresses — is this derivation looking "\
            "in the right place?"
        unprobed = sorted(addresses - probed)
        assert not unprobed, (
            f"the instrument names these inputs and no constructed state breaks them: {unprobed}. "
            f"A dependency with no probe is a dependency whose failure has never been observed — "
            f"and a dependency with no DOOR is where a false clear lives."
        )

    @pytest.mark.parametrize(
        "broken",
        BROKEN_STATES,
        ids=[f"{state.dependency}:{state.verb}" for state in BROKEN_STATES],
    )
    def test_every_broken_state_is_refused_through_its_own_door(
        self, tmp_path: Path, broken: BrokenState, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        case = tmp_path / "case"
        case.mkdir()
        repo_root = broken.build(case, monkeypatch)
        with pytest.raises(gg.GuardIsBlind) as raised:
            gg.classify(repo_root, exemptions=())
        assert raised.value.door == broken.door, (
            f"breaking {broken.dependency} ({broken.verb}) was refused through door "
            f"{raised.value.door!r}, not {broken.door!r}. Either the state constructs something "
            f"other than what it claims — in which case the door it was written for is UNPROBED "
            f"and this file cannot tell — or a refusal moved.\n{raised.value}"
        )

    @pytest.mark.parametrize(
        "broken",
        BROKEN_STATES,
        ids=[f"{state.dependency}:{state.verb}" for state in BROKEN_STATES],
    )
    def test_every_broken_state_serves_bytes_distinct_from_healthy(
        self, tmp_path: Path, broken: BrokenState, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ⚠ **LEG 2 OF THE TRUST GATE, and the only pin here that can catch a swallowed refusal.**
        # The pin above proves the READER raises; this proves the SERVED SURFACE says so. A
        # correct reader behind an entry point that swallows the refusal is a guard that cannot
        # fail, and every reader-level pin in this file structurally cannot see it.
        #
        # **Identical bytes on a broken state is a FALSE CLEAR and a STOP** — not a finding to
        # weigh, not a row to waive.
        healthy = self._healthy_render(tmp_path)
        case = tmp_path / "case"
        case.mkdir()
        repo_root = broken.build(case, monkeypatch)

        verdict = gg.ungated_ground(repo_root, exemptions=())
        assert verdict.render() != healthy, (
            f"THE FALSE CLEAR: with {broken.dependency} {broken.verb} the guard served BYTES "
            f"IDENTICAL to a healthy tree. A consumer acting on this cannot know the guard could "
            f"not see. This is a STOP naming a gap in the derived failure set."
        )
        assert verdict.blind_sources, (
            f"{broken.dependency} is {broken.verb} and the verdict names no blind source, so the "
            f"absence of findings below it means nothing was measured — and says so nowhere"
        )
        assert verdict.state is gg.VerdictState.BLIND
        assert not verdict.is_clean and verdict.exit_code != 0
        assert not verdict.findings, (
            "a blind verdict must not also carry findings: a partial answer is indistinguishable "
            "from a cleaner tree, which is why the incoherent cell is refused at construction"
        )

    @pytest.mark.parametrize(
        "broken",
        BROKEN_STATES,
        ids=[f"{state.dependency}:{state.verb}" for state in BROKEN_STATES],
    )
    def test_every_blind_render_names_the_dependency_it_could_not_read(
        self, tmp_path: Path, broken: BrokenState, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Distinct bytes are not an ACTIONABLE answer. The render is read by an agent that will
        # act on it without checking, so it must name WHAT went blind — revision 5 pinned this for
        # four doors through a hand-written token map, and the map is now the state's own
        # dependency label.
        case = tmp_path / "case"
        case.mkdir()
        repo_root = broken.build(case, monkeypatch)
        rendered = gg.ungated_ground(repo_root, exemptions=()).render().lower()
        assert "blind" in rendered, (
            f"the render does not say the guard is BLIND, so a reader concludes the tree is "
            f"clean: {rendered}"
        )
        token = Path(broken.dependency).name.lower()
        assert token in rendered or broken.dependency.lower() in rendered, (
            f"the render never names {broken.dependency!r}, so a consumer cannot tell which "
            f"input to fix: {rendered}"
        )


# ---------------------------------------------------------------------------
# 18. LEG B's test-shapedness IS pytest's (revision 6)
# ---------------------------------------------------------------------------


class TestLegBTestShapednessEqualsPytests:
    """The scope of LEG B must be the set pytest would collect — as an ORACLE, not by argument.

    **Three surveys of this seam recorded ``fnmatch`` as an exact replacement for pytest's
    matcher, and all three were wrong the same way: nobody opened pytest's matcher.** It is
    ``_pytest.pathlib.fnmatch_ex``, which is ``fnmatch.fnmatch`` wrapped in a DECISION — the
    basename when the pattern carries no separator, the WHOLE PATH when it does, with ``*/``
    prepended for an absolute path against a relative pattern. The wrapper IS the semantics.

    **Measured against the reference build: 6 divergences, every one ``guard=False /
    pytest=True``** — a committed test file judged NOT_APPLICABLE and dropped out of LEG B
    entirely. That is the vanished-input direction, invisible in the report, and the previous
    contract pinned only the OPPOSITE half of the branch (a build matching the whole path for
    EVERY pattern died on 17 pins).
    """

    #: Separator-bearing patterns are the whole point: every ``python_files`` value in every
    #: fixture was separator-FREE, which is a parameter monoculture — the branch could not fire.
    PATTERNS = (
        ["test_*.py"],
        ["*_test.py"],
        ["check_*.py"],
        ["tests/check_*.py"],
        ["loremaster/tests/test_*.py"],
        ["**/tests/test_*.py"],
        ["docs/consult/tests/*.py"],
        ["test_*.py", "**/probes/*.py"],
    )

    RELATIVE_PATHS = (
        "loremaster/tests/test_store_lease.py",
        "loremaster/tests/check_store_lease.py",
        "docs/consult/tests/check_coherence.py",
        "skills/lore-deploy/tests/test_port_probe.py",
        "tests/check_at_the_root.py",
        "promotion_test.py",
        "loremaster/store/lease.py",
        "loremaster/tests/probes/test_probe.py",
    )

    def test_the_matcher_agrees_with_pytests_own_on_every_pattern_and_path(self) -> None:
        from _pytest.pathlib import fnmatch_ex

        agreements = 0
        divergences: list[str] = []
        for patterns in self.PATTERNS:
            for relative in self.RELATIVE_PATHS:
                absolute = Path("/fixture_repository") / relative
                for pattern in patterns:
                    ours = gg._matches_collection_pattern(pattern, PurePosixPath(absolute))
                    theirs = fnmatch_ex(pattern, absolute)
                    if ours == theirs:
                        agreements += 1
                    else:
                        divergences.append(f"{pattern!r} vs {relative}: guard={ours} pytest={theirs}")
        assert agreements, (
            "the oracle comparison made no comparisons at all — a vacuous pass, which is exactly "
            "the shape this class exists to refuse"
        )
        assert not divergences, (
            "LEG B's notion of test-shaped is not pytest's. Every divergence is a file the two "
            "tools disagree about, and the dangerous direction is guard=False/pytest=True — a "
            "real test dropped out of the execution axis with nothing reported:\n  "
            + "\n  ".join(divergences)
        )

    def test_the_separator_bearing_branch_is_actually_exercised(self) -> None:
        # DISCRIMINATION CONTROL. A port that matched the basename for EVERY pattern would agree
        # with pytest on every separator-free row above, so the oracle pin must be shown to reach
        # the branch at all — and to disagree with the naive basename answer somewhere.
        import fnmatch as stdlib_fnmatch

        pattern = "tests/check_*.py"
        relative = "loremaster/tests/check_store_lease.py"
        absolute = PurePosixPath("/fixture_repository") / relative
        assert gg._matches_collection_pattern(pattern, absolute) is True
        assert stdlib_fnmatch.fnmatch(absolute.name, pattern) is False, (
            "the naive basename match must DISAGREE here, or this row cannot tell the port from "
            "the mistake three surveys made"
        )

    def test_the_matcher_is_handed_the_path_under_repo_root_not_under_the_process_cwd(
        self, tmp_path: Path
    ) -> None:
        # ⚠ FOUND BY MY OWN WRONG-BUILD PASS (WB20): reconstructing the absolute path from
        # ``Path.cwd()`` instead of ``repo_root`` passed all 307 pins. Every separator-free pattern
        # is answered from the basename, and the one separator-bearing fixture matched under BOTH
        # roots — arithmetic alignment again, in the pattern this time. This is the EIGHTH call site
        # of the repo_root property, arriving with the matcher that needs an absolute path.
        #
        # The discriminator is the fixture root's OWN basename inside the pattern: under repo_root
        # the constructed path contains it, under the process cwd it cannot.
        repository = _minimal_repository(
            tmp_path, extra_files=["loremaster/tests/check_probe.py"]
        )
        pattern = f"{repository.root.name}/loremaster/tests/check_*.py"
        assert Path.cwd().name != repository.root.name, "precondition: the two roots differ"
        assert gg._is_test_shaped(
            "loremaster/tests/check_probe.py", [pattern], repo_root=repository.root
        ), (
            f"the matcher was handed a path that does not sit under the repo_root it was given, so "
            f"a separator-bearing pattern is matched against the wrong tree entirely (pattern "
            f"{pattern!r})"
        )
        assert not gg._is_test_shaped(
            "loremaster/tests/check_probe.py", [pattern], repo_root=Path.cwd()
        ), (
            "CONTROL: the same pattern must NOT match when the root really is the process cwd, or "
            "this pin cannot tell the two apart"
        )

    def test_a_separator_bearing_pattern_puts_a_real_test_on_the_execution_axis(
        self, tmp_path: Path
    ) -> None:
        # The end-to-end leg. The oracle pins the MATCHER; this pins that `_is_test_shaped` (and
        # therefore the fate) uses it — a correct matcher nobody calls is the same shape as a
        # guard nobody runs.
        repository = _minimal_repository(
            tmp_path,
            python_files=["tests/check_*.py"],
            extra_files=["docs/consult/tests/check_coherence.py"],
        )
        verdicts = assert_every_tracked_file_is_accounted_for(repository.root, exemptions=())
        fate = fates_of(verdicts, "docs/consult/tests/check_coherence.py")[gg.GateAxis.EXECUTION]
        assert fate is gg.Fate.UNGATED, (
            f"under python_files=['tests/check_*.py'] pytest WOULD collect this file (its matcher "
            f"matches the whole path), so it is committed test-shaped ground no gate run "
            f"collects. The guard called it {fate.value} and dropped it."
        )


# ---------------------------------------------------------------------------
# 19. The collector is MEMOISED, and the memo INVALIDATES (ruling R10)
# ---------------------------------------------------------------------------


class TestTheCollectorIsMemoisedAndTheMemoInvalidates:
    """R10: restore the cache **and pin its invalidation** — the pin is the price of the speed.

    Measured 2026-07-29 on this checkout: the collector subprocess costs **~6.0 s** against
    **~29 ms** for the fingerprint that keys the memo, and this contract asks for it from over a
    hundred pins (129 s uncached for the whole file).

    ⚠ **A memo keyed on identity alone serves a STALE answer to a tree that changed under it, and
    a stale healthy answer is a FALSE CLEAR** — the one failure this instrument may not have. So
    the key is a fingerprint of the collector's inputs, and the pins below prove BOTH halves: that
    the memo is real (the subprocess runs once, not twice) and that it lets go (every input class
    that changes the answer changes the key).
    """

    @staticmethod
    def _counting_collector(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
        """Record every collector subprocess, without stubbing it — the answers stay real."""
        calls: list[list[str]] = []
        _intercept_collector_subprocess(monkeypatch, observed=calls)
        return calls

    def test_a_second_ask_about_an_unchanged_tree_runs_no_second_subprocess(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = _minimal_repository(tmp_path)
        calls = self._counting_collector(monkeypatch)
        first = gg.collected_test_files(repository.root)
        second = gg.collected_test_files(repository.root)
        assert first == second
        assert len(calls) == 1, (
            f"the collector ran {len(calls)} times for one unchanged tree — the memo is not "
            f"working, and this file pays ~6 s per ask"
        )

    @pytest.mark.parametrize(
        "change",
        ["add-a-test-file", "silence-a-test-file", "change-the-manifest", "add-an-untracked-test"],
    )
    def test_a_tree_that_changed_invalidates_the_memo(
        self, tmp_path: Path, change: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ∀ over the input CLASSES that can change the answer, each constructed. `add-an-untracked
        # -test` is the row that rules out the cheap key: pytest collects untracked files, so a
        # fingerprint over `git ls-files` would miss it — and scripts/tree_fingerprint.sh, which
        # already fingerprints this repo's TRACKED tree, cannot be reused here for exactly that
        # reason.
        repository = _minimal_repository(
            tmp_path, extra_files=["loremaster/tests/probes/test_probe.py"]
        )
        before = gg.collected_test_files(repository.root)
        assert "loremaster/tests/test_store_lease.py" in before, "precondition"

        if change == "add-a-test-file":
            repository.add_python_file("loremaster/tests/test_added.py", body=_TEST_BODY)
            repository.stage()
            expectation = "loremaster/tests/test_added.py"
        elif change == "add-an-untracked-test":
            repository.add_untracked_python_file("loremaster/tests/test_untracked.py")
            (repository.root / "loremaster" / "tests" / "test_untracked.py").write_text(
                _TEST_BODY, encoding="utf-8"
            )
            expectation = "loremaster/tests/test_untracked.py"
        elif change == "silence-a-test-file":
            (repository.root / "loremaster" / "tests" / "test_store_lease.py").write_text(
                '"""A module the collector reaches and finds nothing in."""\n', encoding="utf-8"
            )
            expectation = ""
        else:
            # ⚠ `norecursedirs` prunes RECURSION and not an explicitly named `testpaths` entry —
            # measured: `norecursedirs=["tests"]` left `loremaster/tests` fully collected, because
            # pytest is handed that path as an argument. So the silenced directory has to be
            # NESTED under the entry, which is also why the existing §6-hole pin uses "probes".
            # A row whose perturbation does not perturb is a row that proves the memo let go when
            # nothing had changed.
            repository.write_pyproject(
                testpaths=["loremaster/tests"],
                workspace_members=["loremaster"],
                ruff_extend_exclude=["scratchpad", gg.ARCHIVED_RECEIPTS_ROOT],
                python_files=None,
                pytest_ini_extra={"norecursedirs": ["probes"]},
                mypy_exclude=None,
                mypy_table_extra=None,
                mypy_overrides=[],
                omit_pytest_table=False,
            )
            expectation = ""

        after = gg.collected_test_files(repository.root)
        assert after != before, (
            f"the tree changed ({change}) and the memo served the SAME answer. A stale collector "
            f"answer is a false clear with a fresh receipt — the memo's key does not cover this "
            f"input class."
        )
        if expectation:
            assert expectation in after, (
                f"the memo let go but the new answer does not contain {expectation!r}: {after}"
            )
        elif change == "change-the-manifest":
            assert "loremaster/tests/probes/test_probe.py" not in after, (
                f"the manifest now prunes the probes directory and the answer still contains its "
                f"test: {after}"
            )
        else:
            assert "loremaster/tests/test_store_lease.py" not in after, (
                f"the file was silenced and the answer still contains it: {after}"
            )

    def test_an_inherited_pytest_addopts_moves_the_memo_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # R10's rider, paid in full (ruling 2026-07-30). The collector child INHERITS this
        # process's environment, so an inherited PYTEST_ADDOPTS decides what it answers — and a
        # value that CHANGES inside one process altered the answer while the key stood still. That
        # was a documented BOUND until the operator granted the one allowlist entry that lets the
        # fingerprint read it; a bound is what you pin when you cannot close the hole, and this one
        # is now closed rather than described.
        #
        # TWO LEGS, because either alone passes for the wrong reason: the first proves the answer
        # actually changes (so the pin is measuring collection and not a hash), the second proves
        # the KEY moves even for a value whose effect on the answer is nil (so the pin is measuring
        # the variable and not a coincidence downstream of it).
        repository = _minimal_repository(
            tmp_path, extra_files=["loremaster/tests/probes/test_probe.py"]
        )
        monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
        calls = self._counting_collector(monkeypatch)
        before = gg.collected_test_files(repository.root)
        assert "loremaster/tests/probes/test_probe.py" in before, "precondition"

        monkeypatch.setenv("PYTEST_ADDOPTS", "--ignore=loremaster/tests/probes")
        after = gg.collected_test_files(repository.root)
        assert "loremaster/tests/probes/test_probe.py" not in after, (
            f"the inherited PYTEST_ADDOPTS now hides that directory from the collector, and the "
            f"memo served the answer from before it changed — a stale healthy verdict with a "
            f"fresh receipt: {sorted(after)}"
        )
        assert len(calls) == 2, (
            f"the environment changed what the child measures and no second subprocess ran, so "
            f"the key does not cover it: {len(calls)} collector call(s)"
        )

        # LEG 2 — the key must move for the VARIABLE, not only for its consequences.
        testpaths = gg.pytest_testpaths(repository.root)
        tracked = gg.tracked_python_files(repository.root)
        monkeypatch.setenv("PYTEST_ADDOPTS", "-p no:randomly")
        inert = gg._collector_input_fingerprint(repository.root, testpaths, tracked)
        monkeypatch.setenv("PYTEST_ADDOPTS", "-p no:cacheprovider")
        other_inert = gg._collector_input_fingerprint(repository.root, testpaths, tracked)
        assert inert != other_inert, (
            "two DIFFERENT inherited PYTEST_ADDOPTS values produced the same fingerprint, so the "
            "key is blind to the variable — it would only ever notice a change whose effect it "
            "could already see in the files, which is precisely the change it does not need to "
            "notice"
        )

    def test_a_refusal_is_never_memoised(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ⚠ FOUND BY MY OWN WRONG-BUILD PASS (WB21): moving the memo write ABOVE the anti-vacuity
        # refusal passed all 307 pins. The first ask refuses correctly and CACHES the empty answer,
        # so every later ask on the same tree reads the cached emptiness and returns a clean
        # "nothing collected" — the refusal is converted into a false clear by the memo that was
        # supposed to be a speed-up. A cached refusal is the worst possible cache entry, and the
        # only pin that can see it asks TWICE.
        repository = _minimal_repository(tmp_path)
        _intercept_collector_subprocess(
            monkeypatch, observed=[], instead=_blank_collector_output
        )
        with pytest.raises(gg.GuardIsBlind):
            gg.collected_test_files(repository.root)
        with pytest.raises(gg.GuardIsBlind) as second:
            gg.collected_test_files(repository.root)
        assert "collector" in str(second.value), (
            f"the SECOND ask on an unchanged, still-broken tree must refuse for the same reason; "
            f"got: {second.value}"
        )

    def test_a_change_outside_every_collection_root_invalidates_the_memo(
        self, tmp_path: Path
    ) -> None:
        # ⚠ FOUND BY MY OWN WRONG-BUILD PASS (WB12): dropping the tracked-``.py`` population from
        # the fingerprint passed all 307 pins, because every invalidation row above perturbs a file
        # INSIDE a collection root, which the directory walk covers on its own. The tracked
        # population exists for the other half: a module outside every testpath whose content
        # decides whether collection SUCCEEDS. Break it and the collector refuses; a memo blind to
        # it serves the previous healthy answer instead — a stale clean receipt.
        repository = _minimal_repository(tmp_path)
        (repository.root / "loremaster" / "tests" / "conftest.py").write_text(
            "import pathlib\n"
            "import sys\n"
            "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'store'))\n"
            "import lease  # noqa: F401  (the point is that importing it can FAIL)\n",
            encoding="utf-8",
        )
        repository.stage()
        before = gg.collected_test_files(repository.root)
        assert "loremaster/tests/test_store_lease.py" in before, (
            "precondition: the tree collects, and its conftest imports a module outside every "
            "testpaths entry"
        )
        outside = repository.root / "loremaster" / "store" / "lease.py"
        assert not any(
            gg.is_under(str(outside.relative_to(repository.root)), testpath)
            for testpath in gg.pytest_testpaths(repository.root)
        ), "precondition: the module being broken is outside every collection root"
        outside.write_text("raise RuntimeError('a module the conftest cannot import')\n", encoding="utf-8")
        with pytest.raises(gg.GuardIsBlind) as raised:
            gg.collected_test_files(repository.root)
        assert "collector" in str(raised.value), (
            f"the collector now fails to import the tree's conftest, so the guard must refuse "
            f"rather than serve the memoised answer from before the break: {raised.value}"
        )

    def test_two_different_trees_never_share_an_answer(self, tmp_path: Path) -> None:
        # The wrong-instance verb, at the memo: a key that ignored repo_root would serve one
        # tree's collection for another's, and every fixture case in this file would grade the
        # wrong repository while reading as isolated.
        first = _repository_beside(tmp_path, "first", extra_files=["loremaster/tests/test_a.py"])
        second = _repository_beside(tmp_path, "second", extra_files=["loremaster/tests/test_b.py"])
        assert "loremaster/tests/test_a.py" in gg.collected_test_files(first.root)
        assert "loremaster/tests/test_b.py" in gg.collected_test_files(second.root)
        assert "loremaster/tests/test_a.py" not in gg.collected_test_files(second.root)

        # ⚠ AND THE HALF THE ASSERTIONS ABOVE CANNOT SEE (my own WB10 survived them): those trees
        # differ in CONTENT, so their fingerprints differ and no key could collide. The property
        # that actually rules a cross-tree collision out is that the fingerprint is computed over
        # ABSOLUTE paths, so two BYTE-IDENTICAL trees at different roots still key differently.
        # Pinned directly, because a digest rewritten to use repo-relative paths would silently
        # make the memo root-blind and every assertion above would still pass.
        twin_a = _repository_beside(tmp_path, "twin_a")
        twin_b = _repository_beside(tmp_path, "twin_b")
        assert gg.collected_test_files(twin_a.root) == gg.collected_test_files(twin_b.root), (
            "precondition: the two trees are built identically, and the served answer is a set of "
            "repo-RELATIVE paths, so identical trees must answer identically"
        )
        fingerprints = {
            gg._collector_input_fingerprint(
                twin.root, gg.pytest_testpaths(twin.root), gg.tracked_python_files(twin.root)
            )
            for twin in (twin_a, twin_b)
        }
        assert len(fingerprints) == 2, (
            "two byte-identical trees at DIFFERENT roots share a fingerprint, so the memo is "
            "root-blind: one tree's collection would be served for another's the moment their "
            "answers could differ"
        )


# ---------------------------------------------------------------------------
# 20. Every stated bound is TRUE of the mechanism it describes (revision 6)
# ---------------------------------------------------------------------------


class TestEveryStatedBoundIsTrueOfItsMechanism:
    """A bound describing a hole that is already CLOSED is the natural-language defect inverted.

    Revision 5 wrote exactly that correction into a ⚠ comment beside the ``file-types-modelled``
    bound — *"false in the safe direction is still false"* — **and did not apply it to the bound
    one entry below**, which went on claiming that ``collect_ignore`` / ``collect_ignore_glob``
    are unmodelled while this file's own passing
    :meth:`TestLegBIsDerivedFromTheCollector.test_a_conftest_level_collection_hook_is_caught_too`
    proved the collector catches them. The rider was implemented for the clause it sat next to.

    Nothing mechanical checked any bound's CONTENT: a build that rewrote one to teach a closed
    hole as open passed all 171 pins. These pins derive each checkable claim from the mechanism
    itself, so the prose cannot drift away from the code without going RED.
    """

    @staticmethod
    def _bound(identifier: str) -> gg.StatedBound:
        matches = [bound for bound in gg.STATED_BOUNDS if bound.identifier == identifier]
        assert len(matches) == 1, (
            f"expected exactly one bound identified {identifier!r}; found {len(matches)}"
        )
        return matches[0]

    def test_the_file_types_bound_agrees_with_the_runners_shell_leg(self) -> None:
        # DERIVED from the runner, never matched against prose: if typecheck.sh runs shellcheck,
        # committed `.sh` IS gated on the type axis and a bound saying otherwise is false in the
        # safe direction. Its re-open trigger fired the day it was written.
        runner = (REPO_ROOT / gg.RUNNER_RELATIVE_PATH).read_text(encoding="utf-8")
        summary = self._bound("file-types-modelled").summary.lower()
        if "shellcheck" in runner:
            assert "shellcheck" in summary or "type-gated" in summary, (
                f"the runner runs a shellcheck leg, so committed .sh is gated on the TYPE axis. "
                f"This bound must teach that closure and an open hole on the execution axis "
                f"alone: {summary!r}"
            )
            assert "gated by nothing" not in summary, (
                f"the bound teaches a hole the runner has already closed: {summary!r}"
            )
        else:
            assert "shellcheck" not in summary, (
                f"the runner has no shellcheck leg and the bound claims one: {summary!r}"
            )

    def test_the_conftest_bound_does_not_claim_a_mechanism_the_collector_catches(self) -> None:
        # The sibling the r5 correction skipped. `collect_ignore_glob` is caught BY CONSTRUCTION
        # (LEG B measures collection rather than parsing pytest's exclusion surface), and the
        # passing pin that proves it is named in this class's docstring. A bound claiming
        # otherwise teaches an agent the guard is blind where it is not.
        summary = self._bound("conftest-collection-hooks").summary.lower()
        for retired_claim in ("collect_ignore", "not modelled", "unmodelled"):
            assert retired_claim not in summary, (
                f"this bound still teaches {retired_claim!r}. The collector catches every "
                f"silencing mechanism, including ones nobody has invented; the residual bound is "
                f"that a conftest contributes no collected item BY DESIGN, so its own reach stays "
                f"bounded by registration: {summary!r}"
            )
        assert "registration" in summary, (
            f"the true residual bound is that conftest reach is bounded by REGISTRATION; the "
            f"bound must state that rather than a mechanism the collector sees: {summary!r}"
        )

    def test_the_configuration_precedence_bound_names_the_files_that_outrank_the_manifest(
        self,
    ) -> None:
        summary = self._bound("gate-configuration-precedence").summary
        assert gg.MANIFEST_RELATIVE_PATH in summary, (
            f"the bound must name the file this guard DOES model, or a reader cannot tell what is "
            f"being outranked: {summary!r}"
        )

    def test_the_instruments_precedence_constant_matches_what_the_tools_declare(self) -> None:
        # THE DRIFT GUARD, in the idiom this file already uses for `python_files`: the instrument
        # is stdlib-only by ruling and cannot import mypy or pytest, so it carries the order as a
        # CONSTANT — and a constant nobody re-derives is an inherited number wearing an assertion.
        # THIS test may import both (they are installed), so the constant is checked against the
        # vendors' own declarations on every gate run. #107 was a 100% production outage caused by
        # a declaration the tool did not execute; this is the pin that notices the next one.
        derived = shadowing_configuration_filenames()
        assert tuple(gg.SHADOWING_CONFIGURATION_FILENAMES) == derived, (
            f"the instrument's pinned precedence list "
            f"{tuple(gg.SHADOWING_CONFIGURATION_FILENAMES)!r} no longer matches what the installed "
            f"mypy and pytest declare ({derived!r}). Update the constant and its citation — a file "
            f"missing from it is a gate this guard cannot see being switched off."
        )

    def test_the_memoisation_bound_never_names_a_variable_the_key_already_covers(self) -> None:
        # ⚠ **A BOUND DESCRIBING A HOLE ALREADY CLOSED IS THE NATURAL-LANGUAGE DEFECT INVERTED** —
        # false in the safe direction is still false, and this is that rule turned on my own bound.
        # Until 2026-07-30 this bound named PYTEST_ADDOPTS as the residual; the operator then
        # granted the one allowlist entry that let the fingerprint read it, so naming it as OPEN
        # would now teach a reader that a closed door is open.
        #
        # DERIVED, never matched against prose: the environment variables the instrument actually
        # reads come from its own AST, and none of them may appear in the trigger that enumerates
        # what is still uncovered. The trigger must also name something the instrument does NOT
        # read, or the bound describes nothing at all.
        bound = self._bound("collector-memoisation")
        assert "fingerprint" in bound.summary.lower() or "memo" in bound.summary.lower()
        covered = _environment_variables_the_instrument_reads()
        assert covered, (
            "the instrument reads no environment variable, so either the allowlist-granted read "
            "was removed (and this bound must go back to naming PYTEST_ADDOPTS as open) or this "
            "derivation is broken"
        )
        stale = sorted(name for name in covered if name in bound.reopen_trigger)
        assert not stale, (
            f"the re-open trigger enumerates what the memo key does NOT cover, and it names "
            f"{stale} — variables the fingerprint demonstrably reads. A bound teaching a closed "
            f"hole as open is false in the safe direction, which is still false."
        )
        residual = [
            token.strip(",.;")
            for token in bound.reopen_trigger.split()
            if token.strip(",.;").isupper() and "_" in token
        ]
        assert residual, (
            f"the trigger names no uncovered variable at all, so this bound states nothing a "
            f"reader can watch for: {bound.reopen_trigger!r}"
        )

    def test_the_pattern_platform_bound_matches_the_port_that_was_written(self) -> None:
        # The port reproduces the POSIX branch of pytest's matcher; the Windows branch is absent
        # DELIBERATELY, and the bound is how a reader meets that instead of inheriting it.
        summary = self._bound("collection-pattern-platform").summary.lower()
        assert "posix" in summary or "windows" in summary, (
            f"the bound must name the branch that was NOT ported, or it states nothing a reader "
            f"can act on: {summary!r}"
        )
        source = Path(gg.__file__).read_text(encoding="utf-8")
        assert "startswith(\"win\")" not in source and "sys.platform" not in source, (
            "the instrument now inspects the platform, so the bound is stale — either the Windows "
            "branch was ported (delete the bound and say so) or something else reads the platform"
        )


# ---------------------------------------------------------------------------
# 15. THE INVARIANT
# ---------------------------------------------------------------------------


class TestTheRealRepositoryIsFullyGated:
    """THE instrument. Everything above proves this assertion can discriminate; this is the
    assertion.

    ⚠ **A failure here is a claim about the TREE, not about the guard.** Read the message: it
    names the file, the axis, the scope it is outside, and the two legitimate ways out — which
    are **gate-cover it, or ESCALATE**.

    ⚠ **THIS DOCSTRING USED TO OFFER A THIRD ROUTE** — *"do not add an exemption row without a
    finding number and a named re-open trigger"* — while
    :data:`MESSAGE_MUST_DENY_AN_EXEMPTION_MECHANISM` is asserted into every failure message this
    class can produce. F1 deleted the mechanism; a reader who meets the failure meets the
    docstring, so the prose beside a pinned string is part of the served surface and was
    contradicting it. There is no exemption mechanism: a row is a DESIGN decision requiring an
    operator ruling, and the archived-receipts class is not to be widened to admit anything.
    """

    def test_no_committed_python_is_ungated_on_either_axis(self) -> None:
        findings = findings_of(REPO_ROOT, exemptions=())
        assert not findings, (
            f"{len(findings)} committed file/axis pair(s) are ungated ground:\n\n"
            + "\n\n".join(finding.message for finding in findings)
        )
