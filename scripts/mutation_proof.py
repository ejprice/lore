#!/usr/bin/env python3
"""mutation_proof.py — prove a pin can actually FAIL (finding #196).

WHY THIS EXISTS, and why the obvious version of it is not enough.

A mutation proof is the only evidence that a test is a pin rather than
decoration: break the production code, watch the test go RED, restore. Done by
hand it produces a receipt that looks the same whether it worked or not, and in
one session it silently produced a worthless one TWICE, in two DIFFERENT ways:

  1. THE MUTATION NEVER LANDED (#194). A guessed anchor matched nothing. The
     helper printed an error; the next line of the same shell block ran the test
     anyway, against an UNMUTATED tree, and printed ``1 passed``. That reads as a
     proof. Guarded here by exactly-once anchor matching plus an exit code — a
     correct assertion whose exit status nothing consumes is indistinguishable
     from no assertion at all.

  2. THE MUTATION LANDED AND REDDENED THE WRONG TESTS. ``set -e`` does nothing
     about this one: setup succeeded, something went red, and the tail says
     ``1 failed`` — byte-identical to a successful proof. What actually caught it
     both times was a person knowing which test SHOULD redden and noticing the
     count did not match. THAT is what this mechanises.

So the load-bearing feature is not the mutating; it is that the observed RED set
is diffed **both ways** against a set the caller declares BEFORE the run:

    unexpected reds        something you did not predict broke  -> FAIL
    declared reds STILL GREEN   the pin never fired at all      -> FAIL

The second direction is the one people leave out, and it is the one that catches
a mutation landing in code no test exercises: the anchor matches, the edit is
real, every test passes — and a one-directional check calls that a pass while
the pin has never been shown to fail.

USAGE

    ./scripts/mutation_proof.py \\
        --file loremaster/loremaster/server.py \\
        --anchor '  ↳ body from {sender}, quoted verbatim' \\
        --replacement '' \\
        --expect-red 'loremaster/tests/test_comms_tool.py::TestX::test_y' \\
        -- uv run pytest -q loremaster/tests/test_comms_tool.py

Exit 0 means: the anchor matched EXACTLY once, the mutation landed, the observed
RED set equalled the declared one, and the file was restored byte-exact. Any
other outcome is non-zero and says which.

Use ``--anchor-file`` / ``--replacement-file`` when the text is a whole block —
shell-quoting a multi-line anchor is its own defect generator.

⚠ BOUNDS. Stated here because an instrument that hides its own bound is how
"unproven" silently becomes "proven":

  * ⚠ THE DECLARED SET MUST BE WRITTEN DOWN BEFORE THE RUN. Nothing here can
    tell a set typed from knowledge apart from one transcribed after peeking at
    the output, and a transcribed set is the tautology in a new costume — the
    same shape as an assertion fitted to whatever the code already does. This
    BOUND cannot be closed mechanically; it lives with the caller.
  * ⚠ TAKE DECLARED NODE IDS FROM ``pytest --collect-only -q``, NOT FROM THE
    SOURCE. pytest ASCII-ESCAPES non-ASCII characters in parametrised ids — an
    em-dash in a parameter becomes a literal ``—`` on the wire — so an id
    transcribed from the test file can be unmatchable, and the proof reports a
    two-way mismatch on a mutation that was perfectly correct. Collecting is not
    peeking: it names the tests without running them, so the declared set is
    still fixed BEFORE any result exists.
  * ⚠ DO NOT PIPE THIS INTO ``tail``/``head`` WITHOUT ``PIPESTATUS``. The pipe's
    exit status is the LAST command's, so a non-zero verdict from this tool is
    discarded and the block reads as a pass — #194's mechanism exactly, one
    level up, and it bit the author of this file on its first live run. Pipe
    only where a human reads the words, never where a shell decides.
  * Node ids are parsed from pytest's ``FAILED``/``ERROR`` summary lines, split
    at the FIRST ``" - "``. A parametrised id that itself contains ``" - "`` will
    truncate. Colour is disabled for the child so the prefixes stay parseable.
  * ⚠ ONLY lines inside pytest's ``short test summary info`` section are read. A
    command that suppresses that section (``--no-summary``, ``-p no:terminal``, or
    anything that is not pytest) therefore yields NO node ids — which surfaces as
    the loud ``unparseable`` exit below, or as a loud declared-but-green mismatch,
    never as a quiet pass. That is a MOVED bound, stated rather than hidden: the
    previous output-wide scan mistook a test's own captured ``ERROR ``/``FAILED ``
    log line for a summary line and failed correct proofs.
  * Restoration is by CONTENT (an md5-verified copy), so it survives a crashing
    command and a non-zero exit. It does NOT survive ``SIGKILL`` of this process.
  * It restores ONE file. A command with side effects of its own is out of scope.

NOTE ON OUTPUT. This prints on success, against the house "silent on success"
idiom for scripts. Deliberate: the receipt IS the deliverable here, and a proof
tool that succeeds silently gives the caller nothing to paste into a report.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_EXIT_OK = 0
_EXIT_ANCHOR = 3
_EXIT_MISMATCH = 4
_EXIT_RESTORE = 5
_EXIT_UNPARSEABLE = 6

_SUMMARY_PREFIXES = ("FAILED ", "ERROR ")

# pytest's own section banner: ``==== short test summary info ====``. Everything AFTER it
# is summary lines; everything before it is captured output, tracebacks and progress.
_SUMMARY_HEADER = "short test summary info"


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _summary_section(output: str) -> list[str]:
    """The lines of pytest's ``short test summary info`` section, or ``[]``.

    Searched from the END so that a fixture or a captured log line containing the banner
    text cannot shadow the real section, which is always last.
    """
    lines = output.splitlines()
    for index in range(len(lines) - 1, -1, -1):
        stripped = lines[index].strip()
        if stripped.startswith("=") and _SUMMARY_HEADER in stripped:
            return lines[index + 1 :]
    return []


def parse_red_node_ids(output: str) -> set[str]:
    """Extract failing node ids from a pytest run's short summary.

    ⚠ **ONLY from inside the ``short test summary info`` SECTION**, and that scoping is
    load-bearing rather than tidy. A ``Captured log call`` line reads::

        ERROR    loremaster.floor_calibration.store:_txn.py:1199 floor_calibration.query.rejected

    It begins with ``ERROR `` — a summary prefix — so an output-wide scan turns it into a
    phantom node id and reports a two-way mismatch on a proof that was perfectly correct.
    Met live by the packet 11-i-a cold audit; in a repo whose seams log every rejection at
    ERROR, that is most proofs.

    The scoping is an ALLOWLIST (where a summary line may legally appear), never a list of
    forbidden prefixes: the forbidden set is unbounded — log levels, a test's own
    ``print``, a doctest — and this repo has six receipts for name-list instruments losing
    to the entry nobody enumerated.

    Split at the FIRST ``" - "``: pytest emits ``FAILED <nodeid> - <message>`` and the
    message routinely contains further dashes, so splitting at the last one (or on
    whitespace) yields ids that match nothing.
    """
    reds: set[str] = set()
    for raw in _summary_section(output):
        line = raw.strip()
        for prefix in _SUMMARY_PREFIXES:
            if line.startswith(prefix):
                node = line[len(prefix) :].split(" - ", 1)[0].strip()
                if node:
                    reds.add(node)
                break
    return reds


def _read_text_arg(inline: str | None, from_file: str | None) -> str | None:
    """Resolve a ``--x`` / ``--x-file`` pair to its text."""
    if from_file is not None:
        return Path(from_file).read_text(encoding="utf-8")
    return inline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mutation_proof.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", required=True, help="the file to mutate (relative to cwd)")
    parser.add_argument("--anchor", help="exact text to replace; must match EXACTLY once")
    parser.add_argument("--anchor-file", help="read the anchor text from this file instead")
    parser.add_argument("--replacement", default="", help="text to substitute (default: delete)")
    parser.add_argument("--replacement-file", help="read the replacement text from this file instead")
    parser.add_argument(
        "--expect-red",
        action="append",
        required=True,
        metavar="NODEID",
        help="a node id that MUST go red. Repeatable. Declare these BEFORE running.",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- <test command to run>")
    return parser


def _report_mismatch(declared: set[str], observed: set[str]) -> None:
    unexpected = sorted(observed - declared)
    still_green = sorted(declared - observed)
    print("\nPROOF FAILED — the observed RED set is not the declared one.", file=sys.stderr)
    if still_green:
        print(
            "\n  DECLARED RED but STAYED GREEN "
            "(the pin never fired — the mutation may have landed in code no test reaches):",
            file=sys.stderr,
        )
        for node in still_green:
            print(f"    - {node}", file=sys.stderr)
    if unexpected:
        print(
            "\n  WENT RED but was NOT DECLARED "
            "(the mutation broke something else; a bare '1 failed' tail cannot see this):",
            file=sys.stderr,
        )
        for node in unexpected:
            print(f"    + {node}", file=sys.stderr)
    print(f"\n  declared: {sorted(declared)}", file=sys.stderr)
    print(f"  observed: {sorted(observed)}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("no test command given — pass it after `--`")

    anchor = _read_text_arg(args.anchor, args.anchor_file)
    if anchor is None:
        parser.error("one of --anchor or --anchor-file is required")
    replacement = _read_text_arg(args.replacement, args.replacement_file) or ""

    target = Path(args.file)
    if not target.is_file():
        print(f"mutation_proof: --file {target} is not a file", file=sys.stderr)
        return _EXIT_ANCHOR

    # BYTES throughout: no encoding or newline translation can perturb what we
    # write back, and the anchor is matched against exactly what is on disk.
    original = target.read_bytes()
    anchor_bytes = anchor.encode("utf-8")
    matches = original.count(anchor_bytes)
    if matches != 1:
        print(
            f"mutation_proof: anchor matched {matches} times, expected EXACTLY 1 — "
            f"NOTHING WAS MUTATED and no proof was run.\n"
            f"  (0 means the anchor is stale or mis-quoted — the #194 shape, where the test then "
            f"runs against an unmutated tree and its 'passed' reads as a proof.\n"
            f"   >1 means the site proven would be ambiguous.)",
            file=sys.stderr,
        )
        return _EXIT_ANCHOR

    backup_dir = Path(tempfile.mkdtemp(prefix="mutation_proof_"))
    backup = backup_dir / target.name
    # CONTENT backup, not a hash: an md5 list is a DETECTOR, not a BACKUP — it
    # tells you the file changed and leaves you with nothing to restore from.
    shutil.copy2(target, backup)
    original_md5 = _md5(target)

    try:
        target.write_bytes(original.replace(anchor_bytes, replacement.encode("utf-8"), 1))
        print(f"mutation LANDED (anchor matched exactly once) in {target}")
        print(f"running: {' '.join(command)}\n")

        env = {**os.environ, "PY_COLORS": "0", "NO_COLOR": "1"}
        run = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
        output = run.stdout + run.stderr
        print(output)
    finally:
        shutil.copy2(backup, target)
        restored_md5 = _md5(target)
        shutil.rmtree(backup_dir, ignore_errors=True)

    if restored_md5 != original_md5:
        print(
            f"mutation_proof: ⚠ RESTORE FAILED — {target} does not match its pre-mutation content "
            f"({original_md5} -> {restored_md5}). THE TREE IS DIRTY; fix it before anything else "
            f"runs a gate against it.",
            file=sys.stderr,
        )
        return _EXIT_RESTORE
    print(f"tree restored byte-exact ({target}: md5 {original_md5})")

    observed = parse_red_node_ids(output)
    declared = set(args.expect_red)

    if not observed and run.returncode != 0:
        print(
            "mutation_proof: the command exited non-zero but emitted no parseable "
            "`FAILED <nodeid>` lines. Nothing can be concluded about which tests fired — "
            "this is NOT a proof. (Is the command pytest? Did it die during collection?)",
            file=sys.stderr,
        )
        return _EXIT_UNPARSEABLE

    if observed != declared:
        _report_mismatch(declared, observed)
        return _EXIT_MISMATCH

    print(f"\nPROOF HELD — the declared RED set fired EXACTLY: {sorted(declared)}")
    return _EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
