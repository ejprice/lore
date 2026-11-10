"""Contract: parked contract reds are DESELECTED by a default pytest run (lead task 7f68cbcf; spec S1-S8 +
lead ruling, operator 2026-11-09).

**WHAT IS PINNED.** ``scripts/pending_contracts.yaml`` lists, per bound, the pytest node ids a contract-ahead
packet is designed to fail (``bounds[].files[].red_nodeids``). A default pytest run must not show those reds
to every agent that runs the suite, and the currency gate must still see every one of them:

* S1 a default run deselects every listed node id of every bound that does NOT carry ``active: true``, by
  EXACT node-id membership (the gate's R31 rule: never a prefix, never a file, never a parametrize stem);
* S2 when anything was deselected that way, the run prints ONE line naming the count, the entry ids involved
  and ``--run-parked``; pytest's own ``N deselected`` count includes them (``config.hook.pytest_deselected``);
* S3 ``--run-parked`` includes every parked node;
* S4 an ``active: true`` bound is never deselected;
* S5 a registry that is absent, unreadable or invalid deselects nothing, prints one warning line naming the
  problem, and never makes pytest exit non-zero by itself;
* S6 the manifest's ``pytest`` gate (``scripts/gates.yaml``; ``wave_gate.py`` derives its leg from it) runs
  with ``--run-parked``, so a parked red is still observed RED by the gate;
* S7 ``PendingBound`` accepts an optional STRICT boolean ``active`` (default false);
* S8 ONE implementation: the hook reads the registry through ``PendingContractRegistry`` (the gate's own
  loader and model), never a second YAML parse;
* lead ruling: naming a parked node on the command line does NOT exempt it.

**HOW THE REAL HOOK REACHES THE SANDBOX (the interface these tests fix).** Each case builds a pytester
sandbox and runs a REAL pytest subprocess in it. The sandbox's root ``conftest.py`` imports the repo-root
``conftest.py`` BY PATH (so its ``__file__`` stays the repo's) and re-exports every ``pytest_*`` attribute it
has. So the hook must be reachable as ``pytest_*`` attributes of the repo-root conftest module: defined there,
imported into it, or named by its ``pytest_plugins``. The hook reads the registry at
``<rootdir>/scripts/pending_contracts.yaml``: node ids are rootdir-relative, so the registry that names them
is the one under the run's rootdir. In this repo the rootdir is the repo root, so that path IS
``pending_contract_gate.DEFAULT_REGISTRY_PATH``; in a sandbox it is the sandbox's own registry.

**WHAT WRONG BUILD WOULD STILL PASS THIS?** Asked of every case below; the fixture is built so that the
plausible wrong builds diverge:

* prefix / stem / file matching — ``test_parked_red_sibling`` extends a parked id's name, ``test_tier[warm]``
  shares a parked id's parametrize stem, and both sit in parked files; all three must still run;
* deselecting ``active: true`` bounds, or treating ``active: false`` as active — bound ``live-gamma`` is
  active, bound ``parked-beta`` spells ``active: false`` explicitly, bound ``parked-alpha`` omits the key;
* counting LISTED ids instead of DESELECTED ones — alpha lists an uncollected id and bound ``parked-delta``
  lists only an uncollected file, so the deselected count (4) differs from every listed total (5, 6, 8);
* naming every non-active bound — ``parked-delta`` deselects nothing and must not be named;
* skip/xfail instead of deselect — the native ``deselected`` count and the junit document both see that;
* a summary printed per collection or per xdist worker — the line is counted, and under ``-n 2`` the
  controller (which collects nothing) must still print it, once;
* a hand-rolled YAML parse — the registry with an unknown key and the registry whose node id is filed under
  the wrong path are rejected ONLY by the gate's pydantic model, so a parallel parser keeps deselecting there;
  and a gate model change (a renamed field) makes every sandbox registry invalid, which reddens every
  deselection case for a sharing hook and none for a parallel parser.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pending_contract_gate as pcg  # noqa: E402
from pending_contract_gate import (  # noqa: E402
    GateManifest,
    GateRunner,
    GateSpec,
    JUnitReportReader,
    PendingContractGate,
    PendingContractRegistry,
    PytestRun,
    RawGateResult,
    RegistryError,
)

pytest_plugins = ["pytester"]

# ---------------------------------------------------------------------------
# Conventions, from the same source of truth as production
# ---------------------------------------------------------------------------

#: The repo-root conftest: the hook's home (or the module that imports it).
REPO_CONFTEST = pcg.REPO_ROOT / "conftest.py"
#: Where the registry lives relative to the run's rootdir — derived from the gate's own default path.
REGISTRY_RELATIVE = pcg.DEFAULT_REGISTRY_PATH.relative_to(pcg.REPO_ROOT)
REGISTRY_FILENAME = REGISTRY_RELATIVE.name
#: The opt-in flag (S3), and the token the S2 line must carry.
RUN_PARKED_FLAG = "--run-parked"
#: The manifest gate whose command S6 governs.
PYTEST_GATE_ID = "pytest"
#: The xdist worker count the sandbox uses where a case reproduces the repo's ``-n`` runs.
SANDBOX_WORKERS = "2"
#: A ceiling on one sandbox pytest subprocess, so a looping hook fails the case instead of hanging the run.
SANDBOX_TIMEOUT_SECONDS = 120.0
#: Inherited from an outer xdist worker; a production top-level run never carries them.
XDIST_WORKER_ENV = ("PYTEST_XDIST_WORKER", "PYTEST_XDIST_WORKER_COUNT", "PYTEST_XDIST_TESTRUNUID")

# ---------------------------------------------------------------------------
# The sandbox fixture: three test files, four bounds
# ---------------------------------------------------------------------------

SANDBOX_INI = "[pytest]\naddopts = --import-mode=importlib\n"

#: Loads the REAL repo-root conftest by path and re-exports its pytest_* names (see module docstring).
SANDBOX_CONFTEST = f"""
import importlib.util
import sys

_SPEC = importlib.util.spec_from_file_location("lore_repo_root_conftest", {str(REPO_CONFTEST)!r})
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)
globals().update({{name: value for name, value in vars(_MODULE).items() if name.startswith("pytest_")}})
"""

SANDBOX_TEST_FILES = {
    "test_parked": """
import pytest


def test_parked_red():
    assert "build" == "landed", "parked: the build that greens this has not landed"


def test_parked_red_sibling():
    assert "sibling" == "parked", "NOT parked: its name only extends a parked id"


def test_parked_green():
    assert "build" == "build"


@pytest.mark.parametrize("tier", ["cold", "warm"])
def test_tier(tier):
    assert tier == "warm", "the cold parameter is parked; the warm one is not"
""",
    "test_shelved": """
class TestShelved:
    def test_method(self):
        assert "shelved" == "built", "parked under a bound that spells active: false"


def test_unrelated_green():
    assert "unrelated" == "unrelated"
""",
    "test_live": """
def test_live_red():
    assert "live" == "green", "registered under an ACTIVE bound: never deselected"


def test_live_green():
    assert "live" == "live"
""",
}

PARKED_RED = "test_parked.py::test_parked_red"
PARKED_GREEN = "test_parked.py::test_parked_green"
PARKED_PARAMETER = "test_parked.py::test_tier[cold]"
PARKED_UNCOLLECTED = "test_parked.py::test_renamed_away"
SIBLING_RED = "test_parked.py::test_parked_red_sibling"
UNPARKED_PARAMETER = "test_parked.py::test_tier[warm]"
SHELVED_METHOD = "test_shelved.py::TestShelved::test_method"
UNRELATED_GREEN = "test_shelved.py::test_unrelated_green"
LIVE_RED = "test_live.py::test_live_red"
LIVE_GREEN = "test_live.py::test_live_green"
GONE_ID = "test_gone.py::test_removed"

ALPHA_ID = "parked-alpha-contract"  # no ``active`` key
BETA_ID = "parked-beta-contract"  # ``active: false``
GAMMA_ID = "live-gamma-contract"  # ``active: true``
DELTA_ID = "parked-delta-contract"  # lists only an uncollected file

ALL_COLLECTED = frozenset(
    {
        PARKED_RED,
        SIBLING_RED,
        PARKED_GREEN,
        PARKED_PARAMETER,
        UNPARKED_PARAMETER,
        SHELVED_METHOD,
        UNRELATED_GREEN,
        LIVE_RED,
        LIVE_GREEN,
    }
)
#: Listed under a non-active bound AND collected: exactly what a default run deselects.
PARKED_COLLECTED = frozenset({PARKED_RED, PARKED_GREEN, PARKED_PARAMETER, SHELVED_METHOD})
#: The deselected count a correct build reports for the whole sandbox (hand-counted from the fixture).
EXPECTED_PARKED_COUNT = 4
#: Totals a wrong build would print instead: listed ids of the involved entries (alpha 4 + beta 1), every
#: non-active listed id (+ delta 1), every listed id (+ gamma 2), or the count summed over two xdist workers.
WRONG_COUNTS = frozenset({5, 6, 8})


def _bound(bound_id: str, files: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    """One registry bound, shaped like the committed ``pending_contracts.yaml`` entries."""
    return {
        "id": bound_id,
        "owner": "contract-parked-1 (lead task 7f68cbcf)",
        "reopen_trigger": f"the build that discharges {bound_id} lands; delete the entry with the fix",
        "ruling": "lead ruling 2026-11-09: contract-ahead reds owned until the build",
        "rationale": "designed RED at HEAD: the symbols the contract pins do not exist yet",
        "files": files,
        **extra,
    }


def registry_document(
    *,
    alpha_ids: tuple[str, ...] = (PARKED_RED, PARKED_GREEN, PARKED_PARAMETER, PARKED_UNCOLLECTED),
    beta_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The sandbox registry: four bounds that make the plausible wrong builds diverge (module docstring)."""
    return {
        "version": 1,
        "bounds": [
            _bound(ALPHA_ID, [{"path": "test_parked.py", "red_nodeids": list(alpha_ids)}]),
            _bound(
                BETA_ID,
                [{"path": "test_shelved.py", "red_nodeids": [SHELVED_METHOD]}],
                active=False,
                **(beta_extra or {}),
            ),
            _bound(GAMMA_ID, [{"path": "test_live.py", "red_nodeids": [LIVE_RED, LIVE_GREEN]}], active=True),
            _bound(DELTA_ID, [{"path": "test_gone.py", "red_nodeids": [GONE_ID]}]),
        ],
    }


def registry_text(document: dict[str, Any]) -> str:
    return yaml.safe_dump(document, sort_keys=False)


VALID_REGISTRY = registry_text(registry_document())


def _standalone_integers(line: str) -> set[int]:
    """The integers a line states as numbers (not digits inside a path segment or an identifier)."""
    return {int(match) for match in re.findall(r"(?<![\w./-])\d+(?![\w/-]|\.\d)", line)}


@dataclass(frozen=True)
class SandboxRun:
    """One sandbox pytest run: pytest's own result plus the junit document the gate's reader parsed."""

    result: pytest.RunResult
    junit: PytestRun

    @property
    def ran(self) -> frozenset[str]:
        """Every node id that RAN (a deselected node writes no junit testcase)."""
        return self.junit.collected

    @property
    def failed(self) -> frozenset[str]:
        return frozenset(outcome.node_id for outcome in self.junit.outcomes)

    @property
    def lines(self) -> list[str]:
        return [*self.result.outlines, *self.result.errlines]

    def lines_containing(self, needle: str) -> list[str]:
        return [line for line in self.lines if needle in line]

    def native_deselected(self) -> int:
        return self.result.parseoutcomes().get("deselected", 0)

    def summary_line(self) -> str:
        """The ONE S2 line (the line naming ``--run-parked``); fails the case if there are zero or several."""
        summary = self.lines_containing(RUN_PARKED_FLAG)
        assert len(summary) == 1, (
            f"S2: expected exactly ONE line naming {RUN_PARKED_FLAG}, found {len(summary)}: {summary}\n"
            f"--- output ---\n{os.linesep.join(self.lines)}"
        )
        return summary[0]


class ParkedSandbox:
    """A pytester sandbox wired to the REAL repo-root conftest, with a registry the case chooses."""

    def __init__(self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
        self.pytester = pytester
        for name in XDIST_WORKER_ENV:
            monkeypatch.delenv(name, raising=False)
        pytester.makefile(".ini", pytest=SANDBOX_INI)
        pytester.makeconftest(SANDBOX_CONFTEST)
        pytester.makepyfile(**SANDBOX_TEST_FILES)
        (pytester.path / REGISTRY_RELATIVE.parent).mkdir(parents=True, exist_ok=True)

    @property
    def registry_path(self) -> Path:
        return self.pytester.path / REGISTRY_RELATIVE

    def write_registry(self, text: str | None) -> None:
        """Write the registry, or remove it when ``text`` is ``None`` (the absent case)."""
        if text is None:
            self.registry_path.unlink(missing_ok=True)
        else:
            self.registry_path.write_text(text, encoding="utf-8")

    def run_argv(self, argv: list[str], junit_xml: Path) -> SandboxRun:
        result = self.pytester.runpytest_subprocess(*argv, timeout=SANDBOX_TIMEOUT_SECONDS)
        assert junit_xml.exists(), (
            f"the sandbox run wrote no junit document (exit {result.ret}):\n"
            f"{os.linesep.join([*result.outlines, *result.errlines])}"
        )
        return SandboxRun(result=result, junit=JUnitReportReader.read(junit_xml.read_text(encoding="utf-8")))

    def run(self, *args: str) -> SandboxRun:
        junit_xml = self.pytester.path / "junit.xml"
        argv = ["-rA", "-o", "junit_family=xunit1", f"--junit-xml={junit_xml}", *args]
        return self.run_argv(argv, junit_xml)


@pytest.fixture
def sandbox(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> ParkedSandbox:
    box = ParkedSandbox(pytester, monkeypatch)
    box.write_registry(VALID_REGISTRY)
    return box


# ---------------------------------------------------------------------------
# S1 / S4 — which nodes a default run deselects
# ---------------------------------------------------------------------------


class TestDefaultRunDeselection:
    """S1 + S4: a default run deselects exactly the collected ids of non-active bounds — nothing more.

    S4 rides the set equality of the first case: the active bound's red and green ids must both have run.
    """

    def test_default_run_runs_exactly_the_unparked_nodes(self, sandbox: ParkedSandbox) -> None:
        run = sandbox.run()
        # Set equality: the parked four are gone, and the prefix sibling, the warm parameter and the active
        # bound's ids all still ran.
        assert run.ran == ALL_COLLECTED - PARKED_COLLECTED

    def test_unparked_red_in_a_parked_file_still_fails_the_run(self, sandbox: ParkedSandbox) -> None:
        run = sandbox.run()
        assert run.failed == {SIBLING_RED, LIVE_RED}
        assert run.result.ret == pytest.ExitCode.TESTS_FAILED

    def test_parked_nodes_are_deselected_under_xdist(self, sandbox: ParkedSandbox) -> None:
        # Every repo run uses -n (CLAUDE.md TEST SCOPE); under xdist the WORKERS collect, not the controller.
        run = sandbox.run("-n", SANDBOX_WORKERS)
        assert run.ran == ALL_COLLECTED - PARKED_COLLECTED

    def test_naming_a_parked_node_on_the_command_line_does_not_exempt_it(
        self, sandbox: ParkedSandbox
    ) -> None:
        # Lead ruling: only --run-parked (or active: true) includes a parked node.
        run = sandbox.run(PARKED_RED, UNRELATED_GREEN)
        assert run.ran == {UNRELATED_GREEN}
        assert run.native_deselected() == 1


# ---------------------------------------------------------------------------
# S2 — what the run reports
# ---------------------------------------------------------------------------


class TestDeselectionReport:
    """S2: the native ``deselected`` count includes parked nodes; ONE line names count, entries and flag."""

    def test_native_deselected_count_includes_the_parked_nodes(self, sandbox: ParkedSandbox) -> None:
        run = sandbox.run()
        # Deselected, never skipped/xfailed: the native outcome counts are exact.
        run.result.assert_outcomes(passed=3, failed=2, deselected=EXPECTED_PARKED_COUNT)

    def test_native_count_adds_parked_nodes_to_other_deselection(self, sandbox: ParkedSandbox) -> None:
        run = sandbox.run("-k", "not test_unrelated_green")
        assert run.native_deselected() == EXPECTED_PARKED_COUNT + 1

    def test_summary_line_names_count_involved_entries_and_flag(self, sandbox: ParkedSandbox) -> None:
        line = sandbox.run().summary_line()
        assert EXPECTED_PARKED_COUNT in _standalone_integers(line), line
        assert not (WRONG_COUNTS & _standalone_integers(line)), line
        assert ALPHA_ID in line and BETA_ID in line, line
        # Delta deselected nothing and gamma is active: neither is involved.
        assert DELTA_ID not in line and GAMMA_ID not in line, line

    def test_summary_count_excludes_nodes_deselected_by_other_means(self, sandbox: ParkedSandbox) -> None:
        line = sandbox.run("-k", "not test_unrelated_green").summary_line()
        assert EXPECTED_PARKED_COUNT in _standalone_integers(line), line
        assert EXPECTED_PARKED_COUNT + 1 not in _standalone_integers(line), line

    def test_summary_names_only_entries_whose_nodes_this_run_deselected(self, sandbox: ParkedSandbox) -> None:
        # A run scoped to one file: alpha's ids are not collected, so alpha is not involved.
        line = sandbox.run("test_shelved.py").summary_line()
        assert BETA_ID in line and ALPHA_ID not in line, line
        stated = _standalone_integers(line)
        assert 1 in stated and EXPECTED_PARKED_COUNT not in stated, line

    def test_summary_line_is_printed_once_under_xdist(self, sandbox: ParkedSandbox) -> None:
        # Under xdist the controller collects nothing and worker stdout is not shown: the line must still
        # reach the terminal, once, with the count of ONE collection (not summed over workers).
        line = sandbox.run("-n", SANDBOX_WORKERS).summary_line()
        assert EXPECTED_PARKED_COUNT in _standalone_integers(line), line
        assert not (WRONG_COUNTS & _standalone_integers(line)), line
        assert ALPHA_ID in line and BETA_ID in line, line


# ---------------------------------------------------------------------------
# S3 — the opt-in flag
# ---------------------------------------------------------------------------


class TestRunParkedFlag:
    """S3: ``--run-parked`` includes every parked node, so nothing is deselected and no S2 line prints."""

    def test_run_parked_runs_every_collected_node(self, sandbox: ParkedSandbox) -> None:
        run = sandbox.run(RUN_PARKED_FLAG)
        assert run.ran == ALL_COLLECTED
        assert run.failed == {PARKED_RED, PARKED_PARAMETER, SHELVED_METHOD, SIBLING_RED, LIVE_RED}
        run.result.assert_outcomes(passed=4, failed=5, deselected=0)
        assert run.lines_containing(RUN_PARKED_FLAG) == []


# ---------------------------------------------------------------------------
# S5 + S8 — a registry the gate's model refuses deselects nothing
# ---------------------------------------------------------------------------


def _unknown_key_registry() -> str:
    return registry_text(registry_document(beta_extra={"parked_until": "2026-12-01"}))


def _string_active_registry() -> str:
    document = registry_document()
    document["bounds"][1]["active"] = "true"
    return registry_text(document)


def _misfiled_node_registry() -> str:
    # The gate's R30 rider: a node id filed under another file's entry invalidates the registry. Only the
    # gate's model knows this rule; a hand-rolled parse would accept it and keep deselecting.
    return registry_text(registry_document(alpha_ids=(PARKED_GREEN, SHELVED_METHOD)))


#: (case id, registry text or None for absent, the token the ONE warning line must carry beyond the filename).
BROKEN_REGISTRIES = [
    ("absent", None, REGISTRY_FILENAME),
    ("unparseable", "version: 1\nbounds: [\n  {id: parked-alpha-contract, files: [\n", REGISTRY_FILENAME),
    ("unknown-key", _unknown_key_registry(), "parked_until"),
    ("non-boolean-active", _string_active_registry(), "active"),
    ("misfiled-node-id", _misfiled_node_registry(), SHELVED_METHOD),
]


class TestBrokenRegistry:
    """S5 + S8: absent, unreadable or invalid registry: nothing deselected, ONE warning, exit not forced."""

    @pytest.mark.parametrize(
        ("text", "problem_token"),
        [pytest.param(text, token, id=case) for case, text, token in BROKEN_REGISTRIES],
    )
    def test_broken_registry_deselects_nothing_and_warns_once(
        self, sandbox: ParkedSandbox, text: str | None, problem_token: str
    ) -> None:
        sandbox.write_registry(text)
        # Two GREEN nodes, one of them parked in the sandbox registry: if anything is still deselected the
        # parked one vanishes, and if the hook forces a failure the exit code shows it.
        run = sandbox.run(PARKED_GREEN, LIVE_GREEN)
        assert run.ran == {PARKED_GREEN, LIVE_GREEN}
        assert run.native_deselected() == 0
        assert run.result.ret == pytest.ExitCode.OK, os.linesep.join(run.lines)
        warnings = run.lines_containing(REGISTRY_FILENAME)
        assert len(warnings) == 1, f"S5: expected ONE line naming {REGISTRY_FILENAME}, got {warnings}"
        assert problem_token in warnings[0], warnings[0]


# ---------------------------------------------------------------------------
# S7 — the registry schema
# ---------------------------------------------------------------------------


class TestActiveField:
    """S7: ``PendingBound.active`` is an optional STRICT boolean, read through the gate's own loader."""

    def test_active_is_read_per_bound_with_false_default(self, tmp_path: Path) -> None:
        path = tmp_path / REGISTRY_FILENAME
        path.write_text(VALID_REGISTRY, encoding="utf-8")
        registry = PendingContractRegistry.load(path)
        # model_dump: the field is read through the model's own serialisation, not a hand parse.
        active = {bound.id: bound.model_dump()["active"] for bound in registry.bounds}
        assert active == {ALPHA_ID: False, BETA_ID: False, GAMMA_ID: True, DELTA_ID: False}

    @pytest.mark.parametrize("value", [pytest.param("true", id="string"), pytest.param(1, id="integer")])
    def test_non_boolean_active_is_a_registry_error(self, tmp_path: Path, value: object) -> None:
        # Control first, failing for a different reason than the refusal: a real boolean IS accepted, so the
        # refusal below is about the value's type and not about an unknown ``active`` key.
        path = tmp_path / REGISTRY_FILENAME
        path.write_text(VALID_REGISTRY, encoding="utf-8")
        PendingContractRegistry.load(path)
        document = registry_document()
        document["bounds"][2]["active"] = value
        path.write_text(registry_text(document), encoding="utf-8")
        with pytest.raises(RegistryError, match="active"):
            PendingContractRegistry.load(path)


# ---------------------------------------------------------------------------
# S6 — the currency gate still observes every registered red
# ---------------------------------------------------------------------------


class _RecordingRunner(GateRunner):
    """A gate runner that records the argv it was asked to run and stops before spawning anything."""

    class Stop(Exception):
        """Raised after recording, so nothing downstream reads a fake result."""

    def __init__(self) -> None:
        super().__init__(pcg.REPO_ROOT)
        self.commands: list[list[str]] = []

    def run(self, spec: GateSpec) -> RawGateResult:
        self.commands.append(spec.resolved_command(Path("junit.xml"), SANDBOX_WORKERS))
        raise self.Stop


def _manifest() -> GateManifest:
    return GateManifest.load(pcg.DEFAULT_MANIFEST_PATH)


class TestGateRunsParked:
    """S6: the manifest's pytest gate, as the gate and ``wave_gate`` run it, carries ``--run-parked``."""

    def test_manifest_pytest_gate_command_carries_run_parked(self) -> None:
        command = _manifest().gate(PYTEST_GATE_ID).resolved_command(Path("junit.xml"), SANDBOX_WORKERS)
        assert RUN_PARKED_FLAG in command, command

    @pytest.mark.parametrize(
        "pytest_args",
        [pytest.param((), id="full-run"), pytest.param(("scripts/test_parked_contracts.py",), id="wave-run")],
    )
    def test_leg_runner_spawns_the_pytest_gate_with_run_parked(self, pytest_args: tuple[str, ...]) -> None:
        # The leg runner wave_gate composes (``_run_selected_gates``): full runs pass no args, --wave passes
        # selectors that are appended to the manifest command.
        runner = _RecordingRunner()
        with pytest.raises(_RecordingRunner.Stop):
            pcg._run_selected_gates(runner, _manifest(), [PYTEST_GATE_ID], pytest_args)
        assert len(runner.commands) == 1
        assert RUN_PARKED_FLAG in runner.commands[0], runner.commands[0]

    def test_gate_command_observes_parked_reds_end_to_end(self, sandbox: ParkedSandbox) -> None:
        junit_xml = sandbox.pytester.path / "gate-junit.xml"
        command = _manifest().gate(PYTEST_GATE_ID).resolved_command(junit_xml, SANDBOX_WORKERS)
        # Drop the launcher (``uv run``): the sandbox subprocess already runs pytest on the repo interpreter.
        argv = command[command.index("pytest") + 1 :]
        run = sandbox.run_argv(argv, junit_xml)
        gate = PendingContractGate(
            registry=PendingContractRegistry.load(sandbox.registry_path), repo_root=sandbox.pytester.path
        )
        expected = {outcome.node_id for outcome in gate.partition_pytest(run.junit).expected}
        # Every parked red is collected, fails, and is OWNED by its bound — not STALE, not missing.
        assert {PARKED_RED, PARKED_PARAMETER, SHELVED_METHOD} <= expected
        assert PARKED_GREEN in run.ran
