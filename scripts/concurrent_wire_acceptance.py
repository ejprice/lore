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
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pending_contract_gate  # noqa: E402  (scripts/ is not a package — the shared junit reader)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = "loremaster/tests/test_migration_wire.py"
DEFAULT_ROUNDS = (
    20  # CLAUDE.md: "a single green run NEVER clears a concurrency test — require 20 consecutive"
)
DEFAULT_WORKERS = 4
DEFAULT_PROCESS_TIMEOUT_S = 900.0
CONCURRENT_SESSIONS = 2
TAIL_LINES = 40
PROC_ROOT = Path("/proc")
# The junit family whose failing testcases carry ``file`` — the shared reader refuses anything else.
JUNIT_FAMILY_OPTION = "junit_family=xunit1"

EXIT_ACCEPTED = 0
EXIT_REJECTED = 1
EXIT_REFUSED = 2

# A ``--collect-only -q`` node id: ``path/to/test_x.py::Name[::name...]`` — one per collected test.
_NODE_ID_LINE = re.compile(r"^\S+\.py::\S+$")


def count_collected_node_ids(collect_only_output: str) -> int:
    """How many node ids pytest listed — counted from the LISTING, never from the prose summary line."""
    return sum(1 for line in collect_only_output.splitlines() if _NODE_ID_LINE.match(line.strip()))


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
        return (
            not self.timed_out
            and self.returncode == 0
            and self.run is not None
            and self.run.total == expected_passed
            and self.run.passed == expected_passed
            and not self.run.outcomes
        )

    def describe(self) -> str:
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
        return sum(1 for round_outcome in self.rounds if round_outcome.is_green(self.expected_passed))

    @property
    def accepted(self) -> bool:
        return len(self.rounds) == self.rounds_requested and self.green_rounds == self.rounds_requested

    def summary(self) -> str:
        verdict = "ACCEPTED" if self.accepted else "NOT ACCEPTED"
        return (
            f"#466 concurrent-pair acceptance: {verdict} — "
            f"{self.green_rounds}/{self.rounds_requested} rounds green in both sessions "
            f"({len(self.rounds)} run; expected {self.expected_passed} passed per session)"
        )


def other_pytest_sessions(*, proc_root: Path = PROC_ROOT, own_pids: set[int]) -> list[tuple[int, str]]:
    """``(pid, cmdline)`` of every live process whose argv mentions pytest, excluding ``own_pids``."""
    sessions: list[tuple[int, str]] = []
    for entry in sorted(proc_root.iterdir(), key=lambda path: path.name):
        if not entry.name.isdigit() or int(entry.name) in own_pids:
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except OSError:  # the process exited between the listing and the read
            continue
        argv = [part.decode("utf-8", "replace") for part in raw.split(b"\0") if part]
        if any("pytest" in part for part in argv):
            sessions.append((int(entry.name), " ".join(argv)))
    return sessions


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

    def expected_passed(self) -> int:
        """How many tests the target collects — derived, never assumed. Fails loud on zero."""
        argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--collect-only", self.target]
        completed = subprocess.run(  # noqa: S603 — argv is ours, no shell
            argv, cwd=REPO_ROOT, capture_output=True, text=True, timeout=self.timeout_s, check=False
        )
        collected = count_collected_node_ids(completed.stdout)
        if collected <= 0:
            raise SystemExit(f"--collect-only listed no tests in {self.target} — refusing an empty run")
        return collected

    def _run_session(self, junit_path: Path) -> ProcessOutcome:
        try:
            completed = subprocess.run(  # noqa: S603 — argv is ours, no shell
                self.session_argv(junit_path),
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as expired:
            partial = expired.stdout if isinstance(expired.stdout, str) else ""
            return ProcessOutcome.from_junit(None, returncode=-1, timed_out=True, tail=partial)
        output = f"{completed.stdout}\n{completed.stderr}"
        tail = "\n".join(output.splitlines()[-TAIL_LINES:])
        junit_text = junit_path.read_text(encoding="utf-8") if junit_path.exists() else None
        return ProcessOutcome.from_junit(
            junit_text, returncode=completed.returncode, timed_out=False, tail=tail
        )

    def run_round(self, index: int) -> RoundOutcome:
        with tempfile.TemporaryDirectory(prefix="acceptance-466-") as scratch:
            paths = [Path(scratch) / f"round{index}-session{side}.xml" for side in range(CONCURRENT_SESSIONS)]
            with ThreadPoolExecutor(max_workers=CONCURRENT_SESSIONS) as pool:
                outcomes = tuple(pool.map(self._run_session, paths))
        return RoundOutcome(index=index, outcomes=outcomes)


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
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
