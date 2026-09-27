"""Contract for ``scripts/concurrent_wire_acceptance.py`` — the finding-#466 acceptance driver.

Author: ``contract-466``. The driver runs two CONCURRENT pytest sessions of ``test_migration_wire.py``
N times and says whether every round was green in BOTH. Its verdict is only as honest as the pieces
pinned here:

* **the result reader is the SHARED one** — ``pending_contract_gate.JUnitReportReader`` over pytest's own
  ``--junit-xml`` (``-o junit_family=xunit1``), never a regex over terminal prose. The repo already argued
  that choice (that class's docstring: "a short-summary regex would be one more natural-language surface
  no gate checks"), so a second reader here would be copy #2 of the policy "what did this pytest run
  produce" (ONE IMPLEMENTATION). Pinned by mutation, not by inspection: the driver's verdict must CHANGE
  when the shared reader's answer changes;
* **the expected count** — derived up front from pytest's ``--collect-only -q`` node-id listing, never
  assumed, and zero is refused;
* **the round verdict** — BOTH sessions, exit 0, total == passed == expected, nothing failed, no timeout,
  and a missing / unparseable junit document is RED (never a silent zero);
* **the "another pytest session is live" preflight** — the box law (one full session at a time), #466's
  own origin — read from an injectable ``/proc``.

DELTA d1 (author ``contract-466-d1``; docs/plans/v2/receipts/2026-09-26-466-503/REPORT-refactor-466.md §1
F12): a session that TIMES OUT takes its
whole process tree with it. ``subprocess.run(timeout=)`` kills only the direct ``python -m pytest`` child,
so its ``-n`` xdist workers outlive a timed-out round — orphans that keep ports, memory and store
connections, and that the NEXT round's "no other pytest session" preflight then trips over. Pinned with a
fake 3-deep tree (session → worker → worker's child) standing in for pytest + xdist.
"""

from __future__ import annotations

import ast
import os
import signal
import subprocess
import sys
import time
import uuid
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import concurrent_wire_acceptance  # noqa: E402  (scripts/ is not a package)
import pending_contract_gate  # noqa: E402
import pytest  # noqa: E402
from concurrent_wire_acceptance import (  # noqa: E402
    AcceptanceReport,
    ProcessOutcome,
    RoundOutcome,
    count_collected_node_ids,
    other_pytest_sessions,
)

# test_migration_wire.py collects 14 tests (measured `--collect-only` at 5d549a1: "14 tests collected").
EXPECTED_WIRE_TESTS = 14
_WIRE_FILE = "loremaster/tests/test_migration_wire.py"


def _junit(passed: int, failed: int = 0, errors: int = 0) -> str:
    """A pytest ``junit_family=xunit1`` document: ``passed`` clean cases, then failures, then errors."""
    cases = [
        f'<testcase classname="c" name="test_ok_{index}" file="{_WIRE_FILE}"/>' for index in range(passed)
    ]
    cases += [
        f'<testcase classname="c" name="test_fail_{index}" file="{_WIRE_FILE}">'
        '<failure message="x"/></testcase>'
        for index in range(failed)
    ]
    cases += [
        f'<testcase classname="c" name="test_err_{index}" file="{_WIRE_FILE}"><error message="x"/></testcase>'
        for index in range(errors)
    ]
    return (
        '<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite name="pytest" '
        f'tests="{passed + failed + errors}" failures="{failed}" errors="{errors}" skipped="0">'
        f"{''.join(cases)}</testsuite></testsuites>"
    )


def _outcome(junit: str | None, *, returncode: int = 0, timed_out: bool = False) -> ProcessOutcome:
    return ProcessOutcome.from_junit(junit, returncode=returncode, timed_out=timed_out, tail="")


GREEN = _junit(EXPECTED_WIRE_TESTS)
MEASURED_466 = _junit(8, failed=2, errors=4)  # finding #466's measured concurrent shape: 2 failed + 4 errors


class TestTheRoundVerdict:
    def test_both_green_at_the_expected_count_is_a_green_round(self) -> None:
        pair = (_outcome(GREEN), _outcome(GREEN))
        assert RoundOutcome(index=1, outcomes=pair).is_green(EXPECTED_WIRE_TESTS)

    def test_the_measured_466_shape_in_one_session_makes_the_round_red(self) -> None:
        pair = (_outcome(GREEN), _outcome(MEASURED_466, returncode=1))
        assert not RoundOutcome(index=1, outcomes=pair).is_green(EXPECTED_WIRE_TESTS)

    def test_fewer_tests_than_expected_is_red_even_all_passing_with_exit_zero(self) -> None:
        # A deselect/collection drift: 13/13 green is NOT the 14 the acceptance claims.
        short = _outcome(_junit(EXPECTED_WIRE_TESTS - 1))
        assert not RoundOutcome(index=1, outcomes=(short, _outcome(GREEN))).is_green(EXPECTED_WIRE_TESTS)

    def test_a_missing_junit_document_is_red_not_a_silent_zero(self) -> None:
        # A killed/crashed session writes no document.
        missing = _outcome(None, returncode=-9)
        assert not missing.is_green(EXPECTED_WIRE_TESTS)
        assert "no junit" in missing.describe().lower(), missing.describe()

    def test_zero_collected_is_a_broken_instrument_and_red(self) -> None:
        empty = _outcome(_junit(0), returncode=5)
        assert not empty.is_green(EXPECTED_WIRE_TESTS)
        assert "broken" in empty.describe().lower(), empty.describe()

    def test_a_timed_out_session_is_red(self) -> None:
        stuck = _outcome(GREEN, timed_out=True)
        assert not RoundOutcome(index=1, outcomes=(stuck, _outcome(GREEN))).is_green(EXPECTED_WIRE_TESTS)

    def test_a_nonzero_exit_with_a_green_document_is_red(self) -> None:
        odd = _outcome(GREEN, returncode=3)  # e.g. an internal error after the report was written
        assert not RoundOutcome(index=1, outcomes=(odd, _outcome(GREEN))).is_green(EXPECTED_WIRE_TESTS)

    def test_a_round_needs_both_sessions(self) -> None:
        assert not RoundOutcome(index=1, outcomes=(_outcome(GREEN),)).is_green(EXPECTED_WIRE_TESTS)

    def test_the_report_requires_every_requested_round_green(self) -> None:
        green = RoundOutcome(index=1, outcomes=(_outcome(GREEN), _outcome(GREEN)))
        red = RoundOutcome(index=2, outcomes=(_outcome(GREEN), _outcome(MEASURED_466, returncode=1)))
        expected = EXPECTED_WIRE_TESTS
        assert AcceptanceReport(rounds_requested=2, expected_passed=expected, rounds=[green, green]).accepted
        assert not AcceptanceReport(
            rounds_requested=2, expected_passed=expected, rounds=[green, red]
        ).accepted
        # A run cut short (stop-on-red, or interrupted) never accepts, even if what ran was green.
        assert not AcceptanceReport(rounds_requested=20, expected_passed=expected, rounds=[green]).accepted

    def test_the_report_summary_names_the_counts(self) -> None:
        green = RoundOutcome(index=1, outcomes=(_outcome(GREEN), _outcome(GREEN)))
        report = AcceptanceReport(rounds_requested=1, expected_passed=EXPECTED_WIRE_TESTS, rounds=[green])
        summary = report.summary()
        assert "1/1" in summary and f"{EXPECTED_WIRE_TESTS}" in summary, summary


class TestTheReaderIsTheSharedOne:
    """ONE IMPLEMENTATION, proven by MUTATION: change what the shared reader answers and the driver's
    verdict must change with it. A driver with a private parser keeps its old answer here."""

    def test_the_verdict_follows_the_shared_reader(self, monkeypatch: pytest.MonkeyPatch) -> None:
        assert _outcome(GREEN).is_green(EXPECTED_WIRE_TESTS)  # control: green through the real reader

        def _reader_that_sees_a_failure(xml_text: str) -> pending_contract_gate.PytestRun:
            return pending_contract_gate.PytestRun(total=EXPECTED_WIRE_TESTS, passed=0, outcomes=())

        monkeypatch.setattr(
            pending_contract_gate.JUnitReportReader, "read", staticmethod(_reader_that_sees_a_failure)
        )
        assert not _outcome(GREEN).is_green(EXPECTED_WIRE_TESTS), (
            "the driver kept its verdict when the SHARED JUnitReportReader changed its answer — it parses "
            "pytest results privately (copy #2 of the policy)"
        )

    def test_the_session_command_asks_pytest_for_an_attributable_junit_document(self) -> None:
        # xunit2 (pytest's default) drops `file` and the shared reader refuses such a document (lore
        # memory, 2026-08-01) — so the driver must request xunit1 or every red round is a broken read.
        driver = concurrent_wire_acceptance.ConcurrentPairDriver(target=_WIRE_FILE, workers=4, timeout_s=1.0)
        argv = driver.session_argv(Path("/tmp/x.xml"))
        assert "--junit-xml=/tmp/x.xml" in argv
        assert argv[argv.index("-o") + 1] == "junit_family=xunit1"
        assert argv[argv.index("-n") + 1] == "4"
        assert argv[-1] == _WIRE_FILE


class TestTheExpectedCountIsDerived:
    _COLLECT_ONLY = (
        f"{_WIRE_FILE}::TestTheWireSmokeServesTheFullSurface::test_tools_list\n"
        f"{_WIRE_FILE}::TestTheWireSmokeServesTheFullSurface::test_serverinfo_version\n"
        f"{_WIRE_FILE}::TestTraceEmitGuardsANoneRequestContext::test_a_none_request_context\n"
        "\n"
        "3 tests collected in 3.50s\n"
    )

    def test_counts_node_id_lines_not_the_prose_summary(self) -> None:
        assert count_collected_node_ids(self._COLLECT_ONLY) == 3

    def test_a_forged_count_in_the_summary_line_does_not_move_the_answer(self) -> None:
        forged = self._COLLECT_ONLY.replace("3 tests collected", "99 tests collected")
        assert count_collected_node_ids(forged) == 3

    def test_captured_noise_is_not_a_node_id(self) -> None:
        noisy = "WARNING some::thing happened\n" + self._COLLECT_ONLY
        assert count_collected_node_ids(noisy) == 3


class TestTheOtherSessionPreflight:
    """The driver refuses to start while another pytest session is live (a concurrent unrelated suite
    confounds the measurement AND is the #466 memory hazard). Read from an injectable ``/proc``."""

    @staticmethod
    def _fake_proc(root: Path, processes: dict[int, list[str]]) -> Path:
        for pid, argv in processes.items():
            (root / str(pid)).mkdir()
            (root / str(pid) / "cmdline").write_bytes(b"\0".join(arg.encode() for arg in argv) + b"\0")
        (root / "self").mkdir()  # non-numeric entries are ignored
        return root

    def test_a_live_pytest_session_is_reported(self, tmp_path: Path) -> None:
        proc = self._fake_proc(
            tmp_path,
            {
                101: ["/usr/bin/python", "-m", "pytest", "-n", "12", "-q"],
                102: ["bash", "-c", "sleep 5"],
                103: ["/venv/bin/pytest", "loremaster/tests/test_x.py"],
            },
        )
        sessions = other_pytest_sessions(proc_root=proc, own_pids={999})
        assert sorted(pid for pid, _cmdline in sessions) == [101, 103]

    def test_the_drivers_own_process_tree_is_excluded(self, tmp_path: Path) -> None:
        proc = self._fake_proc(tmp_path, {200: ["python", "-m", "pytest", "-q"]})
        assert other_pytest_sessions(proc_root=proc, own_pids={200}) == []

    def test_a_process_that_vanishes_mid_scan_is_skipped(self, tmp_path: Path) -> None:
        proc = self._fake_proc(tmp_path, {300: ["python", "-m", "pytest"]})
        (proc / "301").mkdir()  # no cmdline file — the process exited between listdir and read
        assert [pid for pid, _cmdline in other_pytest_sessions(proc_root=proc, own_pids=set())] == [300]


@pytest.mark.parametrize("argv", [["--rounds", "0"], ["--workers", "0"]])
def test_nonsense_arguments_are_refused(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        concurrent_wire_acceptance.parse_arguments(argv)
    assert excinfo.value.code != 0


# ============================================================================================= #
# DELTA d1 — F12: a timed-out session leaves no descendant alive.
# ============================================================================================= #
# How deep the fake session tree goes: the session (pytest), its worker (xdist), the worker's own
# child. Three, not two, so a build that kills only one level below the session is still caught.
TREE_DEPTH = 3
# A session timeout far below the tree's natural lifetime, far above the time to build it (~0.1 s).
TREE_SESSION_TIMEOUT_S = 3.0
TREE_MEMBER_LIFETIME_S = 120.0
# How long after the round returns the killed tree may take to disappear from /proc.
TREE_DEATH_BOUND_S = 5.0
# How long past the session timeout the round may take to return (it must not wait for the tree).
ROUND_RETURN_GRACE_S = 15.0

# One tree member: record its own pid, spawn the next level (inheriting everything, as xdist's workers
# do — no new session, no new group), then live far longer than the session timeout. The marker is in
# every member's argv so /proc can tell a tree member from a recycled pid.
_TREE_MEMBER_SCRIPT = """\
import os, pathlib, subprocess, sys, time
pid_prefix, depth, marker, lifetime = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4])
if depth > 1:
    subprocess.Popen([sys.executable, sys.argv[0], pid_prefix, str(depth - 1), marker, str(lifetime)])
staging = pathlib.Path(f"{pid_prefix}.depth{depth}.staging")
staging.write_text(str(os.getpid()))
os.replace(staging, f"{pid_prefix}.depth{depth}.pid")  # atomic: a reader never sees a half-written pid
time.sleep(lifetime)
"""


def _is_live_tree_member(pid: int, marker: str) -> bool:
    """True iff ``pid`` is a running (non-zombie) process whose argv carries ``marker``.

    A zombie has an empty ``cmdline``; a recycled pid lacks the marker — both read as NOT alive.
    """
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False
    return marker.encode("utf-8") in cmdline


def _tree_pids(pid_dir: Path) -> list[int]:
    return sorted(int(path.read_text(encoding="utf-8")) for path in pid_dir.glob("*.pid"))


def _survivors_after(pids: list[int], marker: str, bound_s: float) -> list[int]:
    """Poll up to ``bound_s`` for every pid to stop being a live tree member; return the survivors."""
    deadline = time.monotonic() + bound_s
    while True:
        alive = [pid for pid in pids if _is_live_tree_member(pid, marker)]
        if not alive or time.monotonic() >= deadline:
            return alive
        time.sleep(0.05)


def _reap_by_pid(pids: list[int], marker: str) -> None:
    """Test cleanup: SIGKILL any tree member still alive (marker-checked, so a recycled pid is spared)."""
    for pid in pids:
        if _is_live_tree_member(pid, marker):
            os.kill(pid, signal.SIGKILL)


def _tree_session_argv(script: Path, pid_dir: Path, marker: str) -> Callable[[Path], list[str]]:
    """A stand-in for ``ConcurrentPairDriver.session_argv``: the same signature, a fake session tree."""

    def _argv(junit_path: Path) -> list[str]:
        return [
            sys.executable,
            str(script),
            str(pid_dir / junit_path.stem),
            str(TREE_DEPTH),
            marker,
            str(TREE_MEMBER_LIFETIME_S),
        ]

    return _argv


class TestATimedOutSessionTakesItsWholeTreeWithIt:
    """F12: on a session timeout the driver must leave NO descendant of that session alive — the xdist
    workers included — and must return promptly rather than wait for them."""

    def test_no_member_of_a_timed_out_session_tree_survives_the_round(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        script = tmp_path / "tree_member.py"
        script.write_text(_TREE_MEMBER_SCRIPT, encoding="utf-8")
        pid_dir = tmp_path / "pids"
        pid_dir.mkdir()
        marker = f"tree466-{uuid.uuid4().hex}"
        driver = concurrent_wire_acceptance.ConcurrentPairDriver(
            target=_WIRE_FILE, workers=4, timeout_s=TREE_SESSION_TIMEOUT_S
        )
        monkeypatch.setattr(driver, "session_argv", _tree_session_argv(script, pid_dir, marker))
        pids: list[int] = []
        try:
            started = time.monotonic()
            round_outcome = driver.run_round(1)
            elapsed = time.monotonic() - started
            pids = _tree_pids(pid_dir)
            # Non-vacuity: BOTH sessions built their WHOLE tree before the timeout fired.
            assert len(pids) == concurrent_wire_acceptance.CONCURRENT_SESSIONS * TREE_DEPTH, (
                f"only {len(pids)} tree members recorded a pid — the fake tree was not fully built, so "
                "the pin would certify nothing"
            )
            assert all(outcome.timed_out for outcome in round_outcome.outcomes)
            assert not round_outcome.is_green(EXPECTED_WIRE_TESTS)
            assert elapsed <= TREE_SESSION_TIMEOUT_S + ROUND_RETURN_GRACE_S, (
                f"the round took {elapsed:.1f}s — it waited on the tree instead of killing it"
            )
            survivors = _survivors_after(pids, marker, TREE_DEATH_BOUND_S)
            assert survivors == [], (
                f"{len(survivors)} of {len(pids)} members of the timed-out session trees are still alive "
                f"{TREE_DEATH_BOUND_S}s after the round: {survivors} — orphaned xdist workers (F12)"
            )
        finally:
            _reap_by_pid(pids or _tree_pids(pid_dir), marker)

    def test_a_timed_out_collect_takes_its_whole_tree_with_it(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Lead addition (Phase 5): ``expected_passed`` runs its own ``--collect-only`` subprocess before any
        # round, with the same timeout — the SAME orphan class as a session, so it must go through the SAME
        # process-group runner (``run_as_process_group``). Proven shared by mutation:
        # docs/plans/v2/receipts/2026-09-26-466-503/REPORT-close-466.md §Item 3.
        script = tmp_path / "tree_member.py"
        script.write_text(_TREE_MEMBER_SCRIPT, encoding="utf-8")
        pid_dir = tmp_path / "pids"
        pid_dir.mkdir()
        marker = f"tree466-{uuid.uuid4().hex}"
        driver = concurrent_wire_acceptance.ConcurrentPairDriver(
            target=_WIRE_FILE, workers=4, timeout_s=TREE_SESSION_TIMEOUT_S
        )
        tree_argv = _tree_session_argv(script, pid_dir, marker)(tmp_path / "collect.xml")
        monkeypatch.setattr(driver, "collect_argv", lambda: tree_argv)
        pids: list[int] = []
        try:
            started = time.monotonic()
            with pytest.raises(subprocess.TimeoutExpired):
                driver.expected_passed()
            elapsed = time.monotonic() - started
            pids = _tree_pids(pid_dir)
            assert len(pids) == TREE_DEPTH, (
                f"only {len(pids)} tree members recorded a pid — the fake tree was not fully built, so the "
                "pin would certify nothing"
            )
            assert elapsed <= TREE_SESSION_TIMEOUT_S + ROUND_RETURN_GRACE_S, (
                f"expected_passed took {elapsed:.1f}s — it waited on the tree instead of killing it"
            )
            survivors = _survivors_after(pids, marker, TREE_DEATH_BOUND_S)
            assert survivors == [], (
                f"{len(survivors)} of {len(pids)} members of the timed-out --collect-only tree are still "
                f"alive {TREE_DEATH_BOUND_S}s later: {survivors} — orphaned by expected_passed"
            )
        finally:
            _reap_by_pid(pids or _tree_pids(pid_dir), marker)

    def test_positive_control_the_liveness_probe_sees_a_live_tree_and_its_death(self, tmp_path: Path) -> None:
        # Without this, a probe that always answered "dead" would make the pin above green forever.
        script = tmp_path / "tree_member.py"
        script.write_text(_TREE_MEMBER_SCRIPT, encoding="utf-8")
        pid_dir = tmp_path / "pids"
        pid_dir.mkdir()
        marker = f"tree466-{uuid.uuid4().hex}"
        argv = _tree_session_argv(script, pid_dir, marker)(tmp_path / "control.xml")
        root = subprocess.Popen(argv)  # noqa: S603 — argv is ours, no shell
        pids: list[int] = []
        try:
            deadline = time.monotonic() + TREE_SESSION_TIMEOUT_S
            while len(_tree_pids(pid_dir)) < TREE_DEPTH and time.monotonic() < deadline:
                time.sleep(0.05)
            pids = _tree_pids(pid_dir)
            assert len(pids) == TREE_DEPTH
            assert all(_is_live_tree_member(pid, marker) for pid in pids), "the probe cannot see a live tree"
        finally:
            _reap_by_pid(pids or _tree_pids(pid_dir), marker)
            root.wait(timeout=TREE_DEATH_BOUND_S)
        assert _survivors_after(pids, marker, TREE_DEATH_BOUND_S) == [], "the probe cannot see a death"


# ============================================================================================= #
# close-466 — the CLASS behind item 3, not the instance: EVERY child the driver spawns dies with its tree.
# The collect subprocess was the second door into F12's orphan class; a third (a new ``subprocess.run``
# anywhere in the driver) must redden here rather than wait for someone to notice an orphan.
# ============================================================================================= #
_DRIVER_SOURCE = Path(concurrent_wire_acceptance.__file__)
# The ONE function allowed to spawn (it leads a process group and kills it on any exit).
_SPAWNING_FUNCTION = "run_as_process_group"
# ALLOWLIST (the safe set is small; the spawning set is not): ``subprocess`` names that construct VALUES
# and never start a process. Any other ``subprocess.<name>(…)`` call outside the spawning function fails.
_NON_SPAWNING_SUBPROCESS_CALLS = frozenset({"TimeoutExpired", "CompletedProcess"})


def _subprocess_calls_outside_the_runner(source: str) -> list[str]:
    """``line: subprocess.<name>`` for every ``subprocess`` call outside :data:`_SPAWNING_FUNCTION` that is
    not allowlisted, plus every ``from subprocess import …`` (an alias would hide a call from this scan).

    Bound (threat model: the HONEST developer adding a ``subprocess.run`` to the driver, #466 F12 — not a
    hostile author): ``os.system`` / ``os.spawn*`` / ``os.exec*`` / ``asyncio`` subprocesses are not read.
    Re-open trigger: the driver first imports ``asyncio`` or calls an ``os`` process API other than
    ``killpg``.
    """
    tree = ast.parse(source)
    inside_runner: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == _SPAWNING_FUNCTION:
            inside_runner.update(id(child) for child in ast.walk(node))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            offenders.append(f"{node.lineno}: from subprocess import …")
        if (
            isinstance(node, ast.Call)
            and id(node) not in inside_runner
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
            and node.func.attr not in _NON_SPAWNING_SUBPROCESS_CALLS
        ):
            offenders.append(f"{node.lineno}: subprocess.{node.func.attr}")
    return offenders


class TestEveryDriverChildGoesThroughTheProcessGroupRunner:
    def test_the_driver_spawns_only_inside_the_process_group_runner(self) -> None:
        offenders = _subprocess_calls_outside_the_runner(_DRIVER_SOURCE.read_text(encoding="utf-8"))
        assert offenders == [], (
            f"the driver spawns outside {_SPAWNING_FUNCTION} — a timeout there orphans the child's tree "
            f"(#466 F12's class): {offenders}. Route it through {_SPAWNING_FUNCTION}."
        )

    def test_non_vacuity_the_runner_exists_and_spawns(self) -> None:
        tree = ast.parse(_DRIVER_SOURCE.read_text(encoding="utf-8"))
        runners = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == _SPAWNING_FUNCTION
        ]
        assert len(runners) == 1, f"expected exactly one {_SPAWNING_FUNCTION}, found {len(runners)}"
        spawned = {
            node.func.attr
            for node in ast.walk(runners[0])
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
        }
        assert "Popen" in spawned, f"{_SPAWNING_FUNCTION} no longer spawns — the scan above guards nothing"

    @pytest.mark.parametrize(
        "planted",
        [
            pytest.param("import subprocess\ndef f():\n    subprocess.run(['x'], timeout=1)\n", id="run"),
            pytest.param(
                "import subprocess\ndef f():\n    subprocess.check_output(['x'])\n", id="check_output"
            ),
            pytest.param("from subprocess import run\ndef f():\n    run(['x'])\n", id="from-import-alias"),
        ],
    )
    def test_positive_control_a_spawn_outside_the_runner_is_flagged(self, planted: str) -> None:
        assert _subprocess_calls_outside_the_runner(planted), f"the scan missed a spawn:\n{planted}"

    def test_positive_control_the_allowlisted_values_are_not_flagged(self) -> None:
        honest = (
            "import subprocess\n"
            "def run_as_process_group(argv):\n    return subprocess.Popen(argv)\n"
            "def g(e):\n    raise subprocess.TimeoutExpired('x', 1.0)\n"
        )
        assert _subprocess_calls_outside_the_runner(honest) == []
