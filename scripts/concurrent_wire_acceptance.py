#!/usr/bin/env python3
"""Acceptance driver for finding #466 — two CONCURRENT pytest sessions of the wire smoke, N rounds.

#466's claim: two top-level pytest sessions on this box must not break each other's real-uvicorn wire
tests (``loremaster/tests/test_migration_wire.py``). The measured failure was ``2 failed + 4 errors``
under a concurrent pair and ``14/14`` alone. Per repo law a concurrency result is cleared by 20
CONSECUTIVE green rounds, never one — so this runs the pair ``--rounds`` times (default 20) and accepts
only if every round is green in BOTH sessions at the EXPECTED count (derived up front from pytest's
``--collect-only`` node-id listing, never assumed).

Results are read with the repo's ONE pytest-result reader, ``pending_contract_gate.JUnitReportReader``,
over pytest's own ``--junit-xml`` (``-o junit_family=xunit1`` so failing cases carry ``file``) — never a
regex over terminal prose.

This is the acceptance RECEIPT, not part of the default suite (its name is not ``test_*``). It prints one
line per round plus a summary — the counts ARE the deliverable — and the output tails of any red round
to stderr.

Usage (from the repo root, with NO other pytest session live — it checks and refuses otherwise)::

    uv run python scripts/concurrent_wire_acceptance.py                 # 20 rounds, -n 4 each
    uv run python scripts/concurrent_wire_acceptance.py --rounds 5 --keep-going

Exit status: 0 accepted · 1 a round was red (or the run stopped short) · 2 refused to start.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import re
import signal
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pending_contract_gate  # noqa: E402  (scripts/ is not a package — the shared junit reader)
from _parked_contracts import PARKED_CONTRACTS_PLUGIN_NAME  # noqa: E402

# The ONE fleet detector (lore #503): re-exported, never copied — `other_pytest_sessions` here IS
# `_pytest_sessions.other_pytest_sessions`, shared with the currency gate's worker policy. The
# redundant alias is PEP 484's explicit re-export (mypy strict: no implicit re-export).
from _pytest_sessions import other_pytest_sessions as other_pytest_sessions  # noqa: E402, PLC0414

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = "loremaster/tests/test_migration_wire.py"
DEFAULT_ROUNDS = (
    20  # CLAUDE.md: "a single green run NEVER clears a concurrency test — require 20 consecutive"
)
DEFAULT_WORKERS = 4
DEFAULT_PROCESS_TIMEOUT_S = 900.0
CONCURRENT_SESSIONS = 2
TAIL_LINES = 40
# The junit family whose failing testcases carry ``file`` — the shared reader refuses anything else.
JUNIT_FAMILY_OPTION = "junit_family=xunit1"

EXIT_ACCEPTED = 0
EXIT_REJECTED = 1
EXIT_REFUSED = 2

# A ``--collect-only -q`` node id: ``path/to/test_x.py::Name[::name...]`` — one per collected test.
# Matched with ``fullmatch`` (finding #210's seam): ``$`` alone would also accept a trailing newline.
_NODE_ID_LINE = re.compile(r"^\S+\.py::\S+$")


def count_collected_node_ids(collect_only_output: str) -> int:
    """How many node ids pytest listed — counted from the LISTING, never from the prose summary line."""
    return sum(1 for line in collect_only_output.splitlines() if _NODE_ID_LINE.fullmatch(line.strip()))


@dataclass(frozen=True)
class ProcessOutcome:
    """One pytest session: exit code, the shared reader's parse (or why there is none), timeout, tail."""

    returncode: int
    run: pending_contract_gate.PytestRun | None
    unreadable: str | None
    timed_out: bool
    tail: str

    @classmethod
    def from_junit(
        cls, junit_text: str | None, *, returncode: int, timed_out: bool, tail: str
    ) -> ProcessOutcome:
        """Read ``junit_text`` with the SHARED reader; a missing/refused document is recorded, not zeroed."""
        if junit_text is None:
            return cls(returncode, None, "no junit document was written", timed_out, tail)
        try:
            run = pending_contract_gate.JUnitReportReader.read(junit_text)
        except pending_contract_gate.BrokenInstrumentError as refusal:
            return cls(returncode, None, f"broken instrument: {refusal}", timed_out, tail)
        return cls(returncode, run, None, timed_out, tail)

    def is_green(self, expected_passed: int) -> bool:
        """Green iff it finished in time, exited 0, and ran exactly ``expected_passed`` tests, all passing."""
        return (
            not self.timed_out
            and self.returncode == 0
            and self.run is not None
            and self.run.total == expected_passed
            and self.run.passed == expected_passed
            and not self.run.outcomes
        )

    def describe(self) -> str:
        """One line for the round log: the pass tally, why there is none, or that it timed out."""
        if self.timed_out:
            return "TIMED OUT"
        if self.run is None:
            return f"{self.unreadable} (exit {self.returncode})"
        return (
            f"{self.run.passed}/{self.run.total} passed, {len(self.run.outcomes)} failed/errored "
            f"(exit {self.returncode})"
        )


@dataclass(frozen=True)
class RoundOutcome:
    """One round: the concurrent pair's outcomes. Green only if BOTH are green."""

    index: int
    outcomes: tuple[ProcessOutcome, ...]

    def is_green(self, expected_passed: int) -> bool:
        """Green iff BOTH concurrent sessions ran and each is green at ``expected_passed``."""
        return len(self.outcomes) == CONCURRENT_SESSIONS and all(
            outcome.is_green(expected_passed) for outcome in self.outcomes
        )


@dataclass
class AcceptanceReport:
    """Every round run. Accepted only if ALL requested rounds ran and every one was green."""

    rounds_requested: int
    expected_passed: int
    rounds: list[RoundOutcome] = field(default_factory=list)

    @property
    def green_rounds(self) -> int:
        """How many of the rounds run so far were green in both sessions."""
        return sum(1 for round_outcome in self.rounds if round_outcome.is_green(self.expected_passed))

    @property
    def accepted(self) -> bool:
        """True iff every requested round ran AND every one was green (a short run is not accepted)."""
        return len(self.rounds) == self.rounds_requested and self.green_rounds == self.rounds_requested

    def summary(self) -> str:
        """The one-line acceptance verdict with its green/requested/run counts."""
        verdict = "ACCEPTED" if self.accepted else "NOT ACCEPTED"
        return (
            f"#466 concurrent-pair acceptance: {verdict} — "
            f"{self.green_rounds}/{self.rounds_requested} rounds green in both sessions "
            f"({len(self.rounds)} run; expected {self.expected_passed} passed per session)"
        )


def _output_tail(stdout: str, stderr: str) -> str:
    """The last :data:`TAIL_LINES` lines of a session's combined output — the round log's evidence."""
    return "\n".join(f"{stdout}\n{stderr}".splitlines()[-TAIL_LINES:])


def _captured_text(captured: str | bytes | None) -> str:
    """A ``TimeoutExpired`` capture as text (typed ``str | bytes | None``; text mode yields ``str``)."""
    if isinstance(captured, bytes):
        return captured.decode("utf-8", "replace")
    return captured or ""


def _kill_process_group(session: subprocess.Popen[str]) -> None:
    """SIGKILL every process in ``session``'s group — the session leader and all its descendants.

    The leader has not been reaped yet (at worst it is a zombie), so its group id is still valid; a group
    already fully gone is not an error. Bound: a descendant that left the group (``setsid``) survives —
    xdist does not, so the tree it builds is covered.
    """
    with contextlib.suppress(ProcessLookupError):
        os.killpg(session.pid, signal.SIGKILL)


def run_as_process_group(argv: Sequence[str], *, timeout_s: float) -> subprocess.CompletedProcess[str]:
    """Run ``argv`` from the repo root as the leader of its OWN process group, capturing its output.

    The ONE subprocess runner every pytest child of this driver goes through (#466 d1 F12 + close-466):
    ``subprocess.run(timeout=)`` kills only the direct child, orphaning every descendant, so on a timeout
    — or ANY exception interrupting the wait (Ctrl-C) — this kills the WHOLE group instead.

    Args:
        argv: The command; never run through a shell.
        timeout_s: How long to wait for the command to finish.

    Returns:
        The finished command's return code and captured stdout/stderr.

    Raises:
        subprocess.TimeoutExpired: The budget expired; the group is already dead and the exception
            carries the output read before the kill (``.stdout`` / ``.stderr``), like ``subprocess.run``.
        BaseException: Anything interrupting the wait propagates unchanged, after the group kill.
    """
    with subprocess.Popen(  # noqa: S603 — argv is ours, no shell
        argv,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    ) as session:
        try:
            stdout, stderr = session.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired as expired:
            # communicate() keeps what it read across a timeout; once the tree is dead every pipe writer is
            # gone, so this drain returns the partial output instead of hanging.
            _kill_process_group(session)
            stdout, stderr = session.communicate()
            raise subprocess.TimeoutExpired(
                expired.cmd, expired.timeout, output=stdout, stderr=stderr
            ) from expired
        except BaseException:
            _kill_process_group(session)
            raise
    return subprocess.CompletedProcess(argv, session.returncode, stdout, stderr)


class ConcurrentPairDriver:
    """Runs the target under two concurrent pytest sessions, ``rounds`` times."""

    def __init__(self, *, target: str, workers: int, timeout_s: float) -> None:
        self.target = target
        self.workers = workers
        self.timeout_s = timeout_s

    def session_argv(self, junit_path: Path) -> list[str]:
        """One session's command: xdist ``-n workers`` and an attributable junit document."""
        return [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "-n",
            str(self.workers),
            f"--junit-xml={junit_path}",
            "-o",
            JUNIT_FAMILY_OPTION,
            self.target,
        ]

    def collect_argv(self) -> list[str]:
        """The command that lists the target's node ids without running them (``--collect-only``)."""
        # ``-p no:<parked plugin>``: the expected pass count must include every collected node, parked ones
        # too (parked-contracts ruling A7).
        return [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "-p",
            f"no:{PARKED_CONTRACTS_PLUGIN_NAME}",
            "--collect-only",
            self.target,
        ]

    def expected_passed(self) -> int:
        """How many tests the target collects — derived, never assumed. Fails loud on zero.

        Runs through :func:`run_as_process_group`, so a timed-out collect takes its whole tree with it
        (``subprocess.TimeoutExpired`` propagates after the kill).
        """
        completed = run_as_process_group(self.collect_argv(), timeout_s=self.timeout_s)
        collected = count_collected_node_ids(completed.stdout)
        if collected <= 0:
            raise SystemExit(f"--collect-only listed no tests in {self.target} — refusing an empty run")
        return collected

    def _run_session(self, junit_path: Path) -> ProcessOutcome:
        """Run one pytest session to completion (or timeout) and read its junit with the shared reader.

        Runs through :func:`run_as_process_group`, so a timeout kills the whole tree — its xdist workers
        and their children included — not just the direct child (#466 d1 F12).
        """
        try:
            completed = run_as_process_group(self.session_argv(junit_path), timeout_s=self.timeout_s)
        except subprocess.TimeoutExpired as expired:
            return ProcessOutcome.from_junit(
                None,
                returncode=-1,
                timed_out=True,
                tail=_output_tail(_captured_text(expired.stdout), _captured_text(expired.stderr)),
            )
        junit_text = junit_path.read_text(encoding="utf-8") if junit_path.exists() else None
        return ProcessOutcome.from_junit(
            junit_text,
            returncode=completed.returncode,
            timed_out=False,
            tail=_output_tail(completed.stdout, completed.stderr),
        )

    def run_round(self, index: int) -> RoundOutcome:
        """Run the two sessions CONCURRENTLY, each writing its own junit document in a scratch dir."""
        with tempfile.TemporaryDirectory(prefix="acceptance-466-") as scratch:
            paths = [Path(scratch) / f"round{index}-session{side}.xml" for side in range(CONCURRENT_SESSIONS)]
            with ThreadPoolExecutor(max_workers=CONCURRENT_SESSIONS) as pool:
                outcomes = tuple(pool.map(self._run_session, paths))
        return RoundOutcome(index=index, outcomes=outcomes)


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse and validate the command line (``--rounds`` and ``--workers`` must be at least 1)."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0] if __doc__ else None)
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="xdist -n per session")
    parser.add_argument("--target", default=DEFAULT_TARGET)
    parser.add_argument("--timeout-s", type=float, default=DEFAULT_PROCESS_TIMEOUT_S)
    parser.add_argument("--keep-going", action="store_true", help="run every round even after a red one")
    parser.add_argument(
        "--allow-other-sessions", action="store_true", help="start even if another pytest session is live"
    )
    arguments = parser.parse_args(argv)
    if arguments.rounds < 1:
        parser.error("--rounds must be at least 1")
    if arguments.workers < 1:
        parser.error("--workers must be at least 1")
    return arguments


def main(argv: Sequence[str] | None = None) -> int:
    """Refuse if another pytest session is live, then run the rounds; return the exit status."""
    arguments = parse_arguments(argv)
    if not arguments.allow_other_sessions:
        live = other_pytest_sessions(own_pids={os.getpid(), os.getppid()})
        if live:
            listing = "\n  ".join(f"{pid}: {cmdline}" for pid, cmdline in live)
            print(
                "refusing to start: another pytest session is live (one full session at a time):"
                f"\n  {listing}",
                file=sys.stderr,
            )
            return EXIT_REFUSED
    driver = ConcurrentPairDriver(
        target=arguments.target, workers=arguments.workers, timeout_s=arguments.timeout_s
    )
    report = AcceptanceReport(rounds_requested=arguments.rounds, expected_passed=driver.expected_passed())
    for index in range(1, arguments.rounds + 1):
        round_outcome = driver.run_round(index)
        report.rounds.append(round_outcome)
        green = round_outcome.is_green(report.expected_passed)
        sides = " · ".join(outcome.describe() for outcome in round_outcome.outcomes)
        print(f"round {index:02d}/{arguments.rounds}: {sides} — {'GREEN' if green else 'RED'}", flush=True)
        if not green:
            for side, outcome in enumerate(round_outcome.outcomes, start=1):
                print(f"--- round {index} session {side} tail ---\n{outcome.tail}", file=sys.stderr)
            if not arguments.keep_going:
                break
    print(report.summary())
    return EXIT_ACCEPTED if report.accepted else EXIT_REJECTED


if __name__ == "__main__":
    raise SystemExit(main())
