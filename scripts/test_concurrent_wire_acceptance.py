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
"""

from __future__ import annotations

import os
import sys
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
