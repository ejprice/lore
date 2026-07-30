#!/usr/bin/env python3
"""wrong_builds.py — attack a contract by BUILDING the wrong implementations it must reject.

WHAT THIS IS, AND WHAT IT IS NOT. This is an ATTACK HARNESS, hand-run, and it is deliberately
wired into no gate: it mutates a copy of an instrument, runs that instrument's real contract
against each mutation, and reports which mutations the contract WAVES THROUGH. A gate answers
"is the tree correct?"; this answers "could the gate tell if it weren't?" — and the second
question has no answer a green suite can give, because a contract that cannot fail passes.

WHY IT IS COMMITTED (finding #278). The measurement it produced is load-bearing — packet 44's
revision 6 exists because 21 such builds ran against revision 5 and SIX passed at 171/171 — and
this class of instrument has now evaporated with its scratch tree TWICE in this repository, once
from a cold audit whose ~40-line door sweep settled the central claim an operator-accepted bound
rested on, and once from an adversary whose seven probes are quoted in a report nobody can re-run.
*"It is in my scratch" is a plan to lose it.* The perversity is that the BETTER the instrument, the
more likely it dies unremarked: a clean result needs no explanation, so the report carries the
number and drops the tool.

WHAT IT MEASURES, stated so a reader does not over-read the output. A SURVIVOR is a build the
contract cannot distinguish from a correct one. That is not automatically a defect — some
survivors are BEHAVIOURALLY EQUIVALENT builds, and the honest disposition is to say so rather than
contort a pin to detect a difference with no observable consequence. Every survivor needs a
verdict written down; "all remaining survivors are equivalent" is banned output.

THE TWO GUARDS THAT MAKE THE OUTPUT MEAN SOMETHING, both of which have fired for real:

  1. **An anchor that does not match EXACTLY ONCE is a hard error.** A patch that silently fails to
     land leaves the CORRECT build under test, which passes — and reads exactly like a survivor.
     *"If step N silently no-opped, would step N+1 still print something that reads as success?"*
  2. **Every run's COLLECTED TOTAL is compared to the baseline's.** A mutation that breaks the
     syntax collects nothing, exits 1, and prints `1 error` — which a count of failures reads as
     "killed" when in truth nothing was measured. Those runs are reported NOT COMPARABLE, in
     their own summary category and with a non-zero exit. This fired on the first outing (a wrong
     build whose replacement was not valid Python) — and then AGAIN, on the committed set:
     `WB19` shipped with an escaped quote inside a triple-quoted replacement, so it had never
     parsed and had never measured anything, while the summary line
     (`len(names) - len(survivors)`) counted it as one of 20 kills. Found by `coldaudit-44-1`
     (D13) 2026-07-29, repaired 2026-07-30. **The per-build guard was right and the SUMMARY was
     the lie** — which is why the summary now counts three outcomes and not two: *"if step N
     silently no-opped, would step N+1 still print something that reads as success?"*

HOW TO RUN IT. The scratch repository must NOT be a copy of a git WORKTREE (#284): a worktree's
``.git`` is a FILE naming the real gitdir, so a copy's ``git add`` mutates the real index while
every receipt reads as isolated. Build it from an ARCHIVE instead:

    mkdir -p /somewhere/refrepo
    git archive HEAD -o /somewhere/head.tar
    tar -xf /somewhere/head.tar -C /somewhere/refrepo
    # THIS FILE goes in too, and it is not optional: the contract pins that every build declared
    # here LANDS and PARSES against the instrument
    # (`TestTheCommittedWrongBuildsCanActuallyRun`), so a scratch carrying a stale copy of this
    # harness grades a registry that is not the one being run, and the baseline fails for a
    # reason that has nothing to do with the tree.
    cp scripts/gated_ground.py scripts/test_gated_ground.py scripts/wrong_builds.py \
       /somewhere/refrepo/scripts/
    git -C /somewhere/refrepo init -q -b main . && git -C /somewhere/refrepo add -A
    git -C /somewhere/refrepo -c user.name=s -c user.email=s@e.invalid commit -q -m base
    ln -s "$PWD/.venv" /somewhere/refrepo/.venv
    test -d /somewhere/refrepo/.git || exit 1       # PROVENANCE: a DIRECTORY, not a worktree file

    .venv/bin/python scripts/wrong_builds.py --scratch /somewhere/refrepo          # all 21
    .venv/bin/python scripts/wrong_builds.py --scratch /somewhere/refrepo WB1_... WB2_...

⚠ RUN IT WITH THE PROJECT'S VENV PYTHON, NOT THROUGH ITS SHEBANG. The child is
``sys.executable -m pytest``, so a bare ``./scripts/wrong_builds.py`` inherits
``/usr/bin/env python3`` — which on this host has no pytest. Measured 2026-07-30: every child
then printed nothing, the baseline collected 0, and three builds were reported ❗SURVIVED
against a contract that had never run. That specific hole is now a hard refusal (see the
baseline anti-vacuity check in ``main``), but the invocation above is the one that WORKS.

Exit 0 means every requested build was MEASURED and killed. Exit 1 means at least one survived —
or at least one was NOT COMPARABLE, which is a build with no result rather than a kill, and is
named as its own category for exactly that reason (D13).

⚠ BOUNDS, stated because an instrument that hides its own bound converts "unproven" into "proven":

  * The build set is an ENUMERATION, and enumerations are what this repository has the most
    receipts against. Six of these 21 survived their first outing — evidence the enumeration was
    doing work, never evidence that a 22nd would not survive.
  * It grades a CONTRACT, not a tree. A survivor says the contract cannot see that mutation; it
    says nothing about whether the shipped build has it.
  * It asserts the restore is byte-exact, but it restores from CONTENT held in memory for the run.
    Nothing here protects an uncommitted tree from a crash mid-run — commit first.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

#: The mutations, as (anchor, replacement) pairs against ``scripts/gated_ground.py``. Each name
#: says what the WRONG build believes; the report's census table says what happened to it.
WRONG_BUILDS: dict[str, list[tuple[str, str]]] = {}

# ---------------------------------------------------------------------------
# adversary-3's two survivors, restated against revision 6
# ---------------------------------------------------------------------------

# WB1 — blindness reported only for a hand-picked subset of doors, everything else swallowed into
# a CLEAN verdict. Survived revision 5 at 171/171 with 17 false clears.
WRONG_BUILDS["WB1_blindness_only_for_five_named_doors"] = [(
    """    try:
        scopes = _derive(repo_root)
    except GuardIsBlind as blindness:
        return Verdict(findings=(), blind_sources=(str(blindness),))""",
    """    try:
        scopes = _derive(repo_root)
    except GuardIsBlind as blindness:
        pinned = {
            "members-declaration-absent",
            "members-entry-widens-to-the-whole-tree",
            "git-is-unexecutable",
            "manifest-unreadable",
            "receipts-root-is-not-lint-excluded",
        }
        if blindness.door in pinned:
            return Verdict(findings=(), blind_sources=(str(blindness),))
        return Verdict(findings=(), blind_sources=())""")]

# WB2 — the served surface ignores findings. Survived revision 5 at 171/171 serving
# findings=1 / is_clean=True / exit 0 / the clean sentence.
WRONG_BUILDS["WB2_served_surface_ignores_findings"] = [
    ("""    @property
    def is_clean(self) -> bool:
        \"\"\"No ungated ground AND no input the guard failed to read. Both, or it is not clean.\"\"\"
        return self.state is VerdictState.GATED_GROUND""",
     """    @property
    def is_clean(self) -> bool:
        \"\"\"No ungated ground AND no input the guard failed to read. Both, or it is not clean.\"\"\"
        return not self.blind_sources"""),
    ("""            case VerdictState.UNGATED_GROUND:
                return "\\n\\n".join(finding.message for finding in self.findings)""",
     """            case VerdictState.UNGATED_GROUND:
                return (
                    "GATED GROUND — every tracked module is registered with the type gate, and "
                    "every tracked test-shaped file is one the collector reaches."
                )"""),
]

# ---------------------------------------------------------------------------
# my own, derived against revision 6's new surfaces
# ---------------------------------------------------------------------------

# WB3 — the state classifier prefers findings over blindness, so a blind verdict that happens to
# hold a finding exits 1 rather than 2. (Cannot be constructed today; this asks whether the pins
# depend on that or on the ordering.)
WRONG_BUILDS["WB3_state_prefers_findings_over_blindness"] = [(
    """        if self.blind_sources:
            return VerdictState.BLIND
        if self.findings:
            return VerdictState.UNGATED_GROUND
        return VerdictState.GATED_GROUND""",
    """        if self.findings:
            return VerdictState.UNGATED_GROUND
        if self.blind_sources:
            return VerdictState.BLIND
        return VerdictState.GATED_GROUND""")]

# WB4 — exit codes become a SECOND mapping that agrees today and can drift tomorrow.
WRONG_BUILDS["WB4_exit_code_is_a_second_mapping"] = [(
    """    @property
    def exit_code(self) -> int:
        \"\"\"The state, as a number. Blindness dominates because the state ordering says so.\"\"\"
        return self.state.exit_code""",
    """    @property
    def exit_code(self) -> int:
        \"\"\"The state, as a number. Blindness dominates because the state ordering says so.\"\"\"
        if self.blind_sources:
            return _EXIT_BLIND
        return _EXIT_UNGATED_GROUND if self.findings else _EXIT_CLEAN""")]

# WB5 — the incoherent cell is permitted again (the construction-time refusal deleted).
WRONG_BUILDS["WB5_incoherent_verdict_permitted"] = [(
    """    def __post_init__(self) -> None:
        if self.findings and self.blind_sources:""",
    """    def __post_init__(self) -> None:
        if False and self.findings and self.blind_sources:""")]

# WB6 — the shadowing check models only mypy's sidecars, missing pytest's four.
WRONG_BUILDS["WB6_shadow_check_covers_mypy_only"] = [(
    """        for filename in SHADOWING_CONFIGURATION_FILENAMES
        if (repo_root / filename).exists()""",
    """        for filename in SHADOWING_CONFIGURATION_FILENAMES
        if "mypy" in filename and (repo_root / filename).exists()""")]

# WB7 — the precedence constant is present and the reader never consults it.
WRONG_BUILDS["WB7_shadow_reader_never_consulted"] = [(
    """    shadowing = shadowing_configuration_files(repo_root)
    if shadowing:""",
    """    shadowing: list[str] = []
    if shadowing:""")]

# WB8 — the pattern matcher reverts to the basename-only `fnmatch` three surveys called exact.
WRONG_BUILDS["WB8_basename_only_pattern_match"] = [(
    """    if "/" not in pattern:
        candidate = absolute_path.name
    else:
        candidate = str(absolute_path)
        if absolute_path.is_absolute() and not pattern.startswith("/"):
            pattern = f"*/{pattern}"
    return fnmatch.fnmatch(candidate, pattern)""",
    """    return fnmatch.fnmatch(absolute_path.name, pattern)""")]

# WB9 — the memo is keyed on the repo_root alone: fast, and serves a stale answer to a tree that
# changed under it.
WRONG_BUILDS["WB9_memo_keyed_on_identity_alone"] = [(
    """    memo_key = (
        str(repo_root.resolve()),
        _collector_input_fingerprint(
            repo_root, pytest_testpaths(repo_root), tracked_python_files(repo_root)
        ),
    )""",
    """    memo_key = (str(repo_root.resolve()), "")""")]

# WB10 — the memo is keyed on the FINGERPRINT alone, so two trees with identical inputs but
# different roots share an answer.
WRONG_BUILDS["WB10_memo_ignores_the_root"] = [(
    """    memo_key = (
        str(repo_root.resolve()),
        _collector_input_fingerprint(""",
    """    memo_key = (
        "",
        _collector_input_fingerprint(""")]

# WB11 — the fingerprint swallows an unreadable input instead of refusing: a PARTIAL key that
# collides with the healthy one.
WRONG_BUILDS["WB11_fingerprint_swallows_unreadable_inputs"] = [(
    """        try:
            content = path.read_bytes()
        except OSError as error:
            raise _blind(
                "collector-inputs-unreadable",""",
    """        try:
            content = path.read_bytes()
        except OSError:
            continue
        if False:
            raise _blind(
                "collector-inputs-unreadable",""")]

# WB12 — the fingerprint covers only the config files, not the .py content (so a silenced test
# module or an added untracked test is invisible to it).
WRONG_BUILDS["WB12_fingerprint_covers_config_only"] = [(
    """    paths.update(repo_root / relative for relative in tracked)""",
    """    paths.update(repo_root / relative for relative in tracked[:0])""")]

# WB13 — the shadow refusal names no file, so a consumer cannot tell which sidecar to remove.
WRONG_BUILDS["WB13_shadow_refusal_names_nothing"] = [(
    """        f"{filename} is present in this checkout and OUTRANKS {MANIFEST_RELATIVE_PATH} in the "
        f"search order the gate's own tool declares, so every setting this guard read from the "
        f"manifest is being ignored; model {filename} or remove it\"""",
    """        f"a higher-precedence configuration file is present in this checkout, so every setting "
        f"this guard read from the manifest is being ignored\"""")]

# WB14 — an absent [tool.mypy] table is accepted again (mypy would fall through to setup.cfg, an
# ancestor, or ~/.config/mypy/config).
WRONG_BUILDS["WB14_absent_mypy_table_accepted"] = [(
    """    table = _section(_manifest(repo_root), "tool", "mypy")
    if table is None:
        return [
            f"{MANIFEST_RELATIVE_PATH} declares no [tool.mypy] table, so mypy's search does not \"""",
    """    table = _section(_manifest(repo_root), "tool", "mypy")
    if table is None:
        return []
    if table is None:
        return [
            f"{MANIFEST_RELATIVE_PATH} declares no [tool.mypy] table, so mypy's search does not \"""")]

# WB15 — member_mypypath is no longer consulted, so one door is unreachable from any verdict.
WRONG_BUILDS["WB15_mypypath_reader_not_consulted"] = [(
    """    roots = typecheck_roots(repo_root)
    member_mypypath(repo_root)""",
    """    roots = typecheck_roots(repo_root)""")]

# WB16 — the whole-tree test reverts to a denylist of literal spellings (`./` walks through).
WRONG_BUILDS["WB16_whole_tree_test_is_a_spelling_denylist"] = [(
    """    if not entry.strip():
        return True
    candidate = PurePosixPath(entry)
    return candidate.is_absolute() or candidate.parts == () or ".." in candidate.parts""",
    """    if not entry.strip():
        return True
    candidate = PurePosixPath(entry)
    return candidate.is_absolute() or entry in {".", ".."} or ".." in candidate.parts""")]

# WB17 — the door identity becomes a computed value, invisible to the derivation.
WRONG_BUILDS["WB17_door_identity_computed_not_literal"] = [(
    """        raise _blind("declared-key-absent", f"{described_as} is not declared")""",
    """        raise _blind("declared-key" + "-absent", f"{described_as} is not declared")""")]

# WB18 — a refusal constructed directly, bypassing the door helper entirely.
WRONG_BUILDS["WB18_refusal_bypasses_the_door_helper"] = [(
    """        raise _blind("declared-paths-empty", f"{described_as} is empty")""",
    '        raise GuardIsBlind("", f"{described_as} is empty — the GUARD is blind, '
    'not the tree clean")')]

# WB19 — the clean render over-claims: one axis named, two measured.
#
# ⚠ THIS BUILD HAD NEVER MEASURED ANYTHING (D13, `coldaudit-44-1`, 2026-07-29). Its replacement
# was written as a triple-quoted literal ending in an ESCAPED quote, which Python resolves — so
# the text it installed ended in TWO quotes, the patched module never parsed, and the run
# collected `1 error` instead of the contract. Guard #2 fired correctly on the per-build line;
# the SUMMARY folded that unmeasured run into the kill count, which is this file's own diagnosed
# failure mode shipped as an instance. Both halves are repaired: the replacement is a plain
# single-quoted string with NO escape (an escaped quote inside a triple-quoted literal is a
# defect generator, not a style choice), and NOT COMPARABLE is now its own summary category.
# The measurement it was always supposed to yield: killed, comparable at 315 == 315.
WRONG_BUILDS["WB19_clean_render_over_claims"] = [(
    """                return (
                    "GATED GROUND — every tracked module is registered with the type gate, and "
                    "every tracked test-shaped file is one the collector reaches."
                )""",
    '                return "GATED GROUND: every committed .py is registered on both axes."')]

# WB20 — _is_test_shaped answers for the process cwd rather than repo_root (the seventh call site
# of the repo_root property, now that the matcher needs an absolute path).
WRONG_BUILDS["WB20_test_shapedness_uses_the_process_cwd"] = [(
    """    absolute = PurePosixPath(str(repo_root.resolve())) / path""",
    """    absolute = PurePosixPath(str(Path.cwd().resolve())) / path""")]

# WB21 — the memo is written BEFORE the anti-vacuity check, so a zero-shaped answer is cached and
# every later ask reads the cached emptiness instead of refusing.
WRONG_BUILDS["WB21_memo_written_before_the_anti_vacuity_check"] = [(
    """    if completed.returncode == _EXIT_CLEAN and not contributing:
        raise _blind(
            "collector-output-is-not-the-shape-read",""",
    """    _COLLECTOR_MEMO[memo_key] = contributing
    if completed.returncode == _EXIT_CLEAN and not contributing:
        raise _blind(
            "collector-output-is-not-the-shape-read",""")]

def apply(name: str, pristine: str) -> str:
    """The named build's source, or a hard error if any anchor does not match exactly once."""
    patched = pristine
    for anchor, replacement in WRONG_BUILDS[name]:
        found = patched.count(anchor)
        if found != 1:
            raise SystemExit(
                f"{name}: anchor matched {found} times, so the patch would not land as written "
                f"and the CORRECT build would be graded instead:\n{anchor[:160]}"
            )
        patched = patched.replace(anchor, replacement)
    if patched == pristine:
        raise SystemExit(f"{name}: the patch changed nothing")
    return patched


def run_contract(scratch: Path, contract: str) -> tuple[int, int, int, str]:  # noqa: D401
    """Run the contract inside ``scratch`` and return (passed, failed, errors, tail)."""
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", contract, "-p", "no:randomly"],
        cwd=scratch,
        capture_output=True,
        text=True,
        check=False,
    )
    lines = completed.stdout.strip().splitlines()
    tail = lines[-1] if lines else ""
    passed = int(match.group(1)) if (match := re.search(r"(\d+) passed", tail)) else 0
    failed = int(match.group(1)) if (match := re.search(r"(\d+) failed", tail)) else 0
    errors = int(match.group(1)) if (match := re.search(r"(\d+) error", tail)) else 0
    if not (passed or failed or errors):
        # ⚠ NOTHING COUNTABLE CAME BACK, so pytest never started or died before its summary —
        # and stderr is the ONLY place that says why. Discarding it is how a failed-to-start run
        # became a silent zero: measured 2026-07-30, this file's own HOW TO RUN recipe
        # (`./scripts/wrong_builds.py`) executes under the SHEBANG interpreter, whose `python3`
        # has no pytest, so every child printed nothing on stdout — and three builds were
        # reported ❗SURVIVED against a baseline that had collected NOTHING.
        stderr_lines = completed.stderr.strip().splitlines()
        why = stderr_lines[-1] if stderr_lines else "<no output on stdout or stderr>"
        tail = f"exit={completed.returncode}: {tail or why}"
    return passed, failed, errors, tail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--scratch",
        required=True,
        type=Path,
        help="an ISOLATED repository (see the module docstring)",
    )
    parser.add_argument(
        "--instrument",
        default="scripts/gated_ground.py",
        help="the file to mutate, relative to --scratch",
    )
    parser.add_argument(
        "--contract",
        default="scripts/test_gated_ground.py",
        help="the contract to run, relative to --scratch",
    )
    parser.add_argument("names", nargs="*", help="build names to run (default: all)")
    arguments = parser.parse_args(argv)

    scratch: Path = arguments.scratch
    if not (scratch / ".git").is_dir():
        raise SystemExit(
            f"{scratch}/.git is not a DIRECTORY. A git WORKTREE's .git is a FILE naming the real "
            f"gitdir, so mutating a copy of one reaches the original repository (#284). Build the "
            f"scratch from `git archive` + a fresh `git init` — see the module docstring."
        )
    instrument = scratch / arguments.instrument
    pristine = instrument.read_text(encoding="utf-8")

    names = arguments.names or sorted(WRONG_BUILDS)
    unknown = sorted(set(names) - set(WRONG_BUILDS))
    if unknown:
        raise SystemExit(f"no such wrong build: {unknown}")

    print("=== baseline (correct build) ===")
    passed, failed, errors, tail = run_contract(scratch, arguments.contract)
    baseline = passed + failed + errors
    print(f"REF => {tail}   [collected total: {baseline}]")
    if failed or errors:
        raise SystemExit("the correct build is not green in the scratch — nothing below is comparable")
    # ⚠ ANTI-VACUITY ON THE BASELINE ITSELF, and it is not hypothetical (found 2026-07-30 while
    # repairing D13, by running this harness exactly as its own docstring said to). Guard #2
    # compares each build's collected total to the BASELINE's — so a baseline of ZERO makes every
    # build comparable to it, failure-free, and therefore ❗SURVIVED. Three builds were reported
    # as survivors against a contract that had never run; over all 21 the line would have read
    # `21 survived`, i.e. "this contract catches nothing", which is the most alarming output this
    # file can print and it would have been an artifact of a missing pytest. A guard that
    # compares two numbers must first know that either number is a measurement.
    if not baseline:
        raise SystemExit(
            f"the baseline collected NOTHING, so every build below would compare 0 to 0 and read "
            f"as a SURVIVOR — the contract never ran. Tail: {tail!r}. The usual cause is the "
            f"interpreter: the child runs {sys.executable!r} -m pytest, so invoke this harness "
            f"with the project's venv python rather than through its shebang."
        )

    survivors: list[str] = []
    killed: list[str] = []
    unmeasured: list[str] = []
    for name in names:
        instrument.write_text(apply(name, pristine), encoding="utf-8")
        passed, failed, errors, tail = run_contract(scratch, arguments.contract)
        total = passed + failed + errors
        comparable = "" if total == baseline else f"  ⚠ NOT COMPARABLE ({total} != {baseline})"
        # THREE outcomes, not two. A run whose collected total does not match the baseline
        # measured NOTHING, and `len(names) - len(survivors)` counted it as a KILL — the exact
        # over-reading guard #2 exists to prevent, in the summary line of the file that
        # diagnosed it (D13, `coldaudit-44-1`, 2026-07-29: WB19 had never parsed, so its kill
        # was reported and had never been obtained).
        if comparable:
            unmeasured.append(name)
            outcome = "⚠ NOT MEASURED"
        elif failed == 0 and errors == 0:
            survivors.append(name)
            outcome = "❗SURVIVED"
        else:
            killed.append(name)
            outcome = "killed"
        print(f"{name:52s} {tail:34s} {outcome}{comparable}")
        instrument.write_text(pristine, encoding="utf-8")
        if instrument.read_text(encoding="utf-8") != pristine:
            raise SystemExit(f"{name}: the restore is not byte-exact — STOP and restore by hand")

    print(
        f"\n{len(names)} built · {len(killed)} killed · {len(survivors)} survived · "
        f"{len(unmeasured)} NOT COMPARABLE (nothing measured)"
    )
    for name in survivors:
        print(f"  SURVIVOR: {name} — needs a written verdict; an equivalent build is not a pass")
    for name in unmeasured:
        print(
            f"  NOT MEASURED: {name} — the patched module did not collect the baseline's tests, "
            f"so this build has no result at all. Repair the mutation and re-run it."
        )
    return 1 if survivors or unmeasured else 0


if __name__ == "__main__":
    raise SystemExit(main())
