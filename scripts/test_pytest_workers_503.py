"""Contract (#503 ruling item 3) — the currency gate's pytest leg sizes its workers by the FLEET policy.

Session ``297217bd``, tdd-light. Author: ``contract-503`` (TESTS ONLY). Operator ruling 2026-09-26 ("All 4
recs"), item 3: the currency gate's pytest leg runs ``-n 12`` when another lore pytest session is live, and
``-n auto`` otherwise. Item 4: no fleet session cap — so "live" is a yes/no, never a count to divide by.

WHY (``REPORT-measure-503.md``, 388c604, §Side answer): every ``pending_contract_gate.py --currency``
close-out spawned a full suite at ``-n auto`` = 64 workers on this box, outside the measured envelope and
against the MEMORY.md fleet rule (cap a FULL suite at ``-n 12`` when another lore suite is live).

CLASS: the worker count of EVERY manifested pytest-reader gate is decided by ONE policy function at the
moment the gate runs, and that policy's "is another session live?" answer comes from the ONE detector
(``other_pytest_sessions``, which lives in ``_pytest_sessions.py`` — the #503 build MOVED it there from
``concurrent_wire_acceptance.py``, which re-exports it). Domains, generated:
  * gates — every gate in the SHIPPED ``scripts/gates.yaml`` whose reader is the junit reader;
  * render paths — ``GateRunner.run`` directly and via ``_run_selected_gates`` (forwarded pytest args);
  * detector definitions — every non-test ``scripts/*.py`` (AST): exactly one ``other_pytest_sessions``.

INTERFACE this contract DEFINES (absent at HEAD ``884ca63`` — REPORT-contract-503.md §Stub expectations):
  * ``scripts/_pytest_sessions.py`` — the shared home both scripts import (``concurrent_wire_acceptance``
    imports ``pending_contract_gate``, so the gate cannot import the driver without a cycle):
    ``PROC_ROOT``, ``other_pytest_sessions(*, proc_root=PROC_ROOT, own_pids)`` (MOVED, not copied —
    ``concurrent_wire_acceptance.other_pytest_sessions`` must BE it), ``FLEET_CAPPED_PYTEST_WORKERS = "12"``,
    ``SOLO_PYTEST_WORKERS = "auto"``, ``pytest_worker_count(*, proc_root=PROC_ROOT, own_pids) -> str``;
  * ``pending_contract_gate.WORKERS_PLACEHOLDER = "{workers}"`` — substituted by ``GateRunner.run`` at run
    time; the manifest's pytest command carries ``"-n", "{workers}"``; ``GateManifest`` refuses a junit gate
    whose command hardcodes a worker count (``-n <literal>`` / ``-n<literal>`` / ``--numprocesses``).

HERMETIC: no pytest is ever spawned — ``subprocess.Popen`` is replaced by a recorder that raises; "live" is
injected (a fake ``/proc`` tree, or a stubbed detector), never read from this busy box.

RED dating: HEAD ``884ca63`` (sections 1-4, author ``contract-503``).

DELTA d1 (author ``contract-503-d1``, lead rulings 2026-09-26 after the Phase 5 audit, RED-dated to HEAD
``f66a190`` + the Phase 4 build in the working tree) — section 5 below:
  1. ENFORCE AT THE STATE: on EVERY render path the rendered argv's LAST worker flag is the policy's
     ``-n <count>``, after any forwarded args / ``--wave`` selector — so the policy wins under any spelling
     (xdist honours the LAST ``-n``: measured, REPORT-refactor-503.md §6, and re-read here through xdist's
     own option parser);
  2. LOUD, NOT SILENT: forwarded args carrying a worker flag the shared ``_hardcoded_worker_counts``
     recognises are REFUSED before any gate spawns, by that ONE helper (mutation-by-stub proves the routing);
  3. KNOWN BOUND #503 F8: a clustered short flag (``-qn3``) escapes that helper — pinned as a miss;
  4. the gate's own pid is excluded on EVERY render path, not only the direct one.

DELTA d2 (author ``contract-503-d2``, section 6, GREEN-dated to HEAD ``f66a190`` + the d1 build): the
dropped rider of ruling D1-F3 (a refused argument is typed and labelled as one, never MANIFEST / CONFIG
ERROR), and two PINNED MISSES — #503 D-1 (``--derive`` / ``--verify-registry`` ignore forwarded args)
and #503 maxprocesses (a forwarded ``--maxprocesses`` is not refused and can only LOWER the count).
"""

from __future__ import annotations

import ast
import functools
import importlib
import inspect
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import concurrent_wire_acceptance  # noqa: E402
import pending_contract_gate  # noqa: E402
import wave_gate  # noqa: E402
from pending_contract_gate import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    READERS,
    GateManifest,
    GateRunner,
    GateSpec,
    JUnitReportReader,
    ManifestError,
)

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
SHARED_SESSIONS_MODULE = "_pytest_sessions"
DETECTOR_NAME = "other_pytest_sessions"

# The operator's ruling (2026-09-26, item 3) and MEMORY.md's fleet rule — INDEPENDENT expected values.
RULED_WORKERS_WHEN_ANOTHER_SESSION_IS_LIVE = "12"
RULED_WORKERS_WHEN_ALONE = "auto"
XDIST_WORKERS_FLAG = "-n"
# The spelling of the count the gate replaced — the retired literal no served manifest string may teach.
RETIRED_WORKERS_LITERAL = "-n auto"

# ---------------------------------------------------------------------------------------------------------
# Fixture argvs — SHAPES OBSERVED LIVE on this box, 2026-09-26 (``/proc/<pid>/cmdline``), not invented:
# ---------------------------------------------------------------------------------------------------------
# A lore agent's session in a ``scratch_copy.sh`` copy (cwd OUTSIDE the repo root — it is still lore).
LORE_SCRATCH_SESSION_ARGV = [
    ".venv/bin/python", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-n", "6", "--tb=line", "-rfE",
    "loremaster/tests/test_supersede_reanchor_58.py",
]  # fmt: skip
# The currency gate's own pytest leg as its ALONE branch renders it (the manifest spells ``-n {workers}``;
# ``auto`` is the solo value the policy substitutes), running from the repo root.
LORE_GATE_SESSION_ARGV = [
    "uv", "run", "pytest", "-q", "-n", "auto", "-o", "junit_family=xunit1",
    "--junit-xml=/var/tmp/tmpk2l3/junit.xml",
]  # fmt: skip
# An xdist worker of such a session: execnet's bootstrap — its argv never names pytest.
XDIST_WORKER_ARGV = [".venv/bin/python", "-u", "-c", "import sys;exec(eval(sys.stdin.readline()))"]
# A process that is not a test session at all.
NOT_A_SESSION_ARGV = ["/usr/bin/python3.14", "-m", "http.server", "8765"]

# pids: realistic magnitudes (this box's pid_max is 4194304; live sessions sat in the 3.8M range).
OWN_PID = 3_895_470
OTHER_SESSION_PID = 3_874_001
SECOND_SESSION_PID = 3_891_494
THIRD_SESSION_PID = 3_895_372
XDIST_WORKER_PID = 3_874_013
NOT_A_SESSION_PID = 1_204_377


class _PopenCaptured(Exception):  # noqa: N818 — a control-flow sentinel, not an error
    """Raised by the recording ``Popen``: the argv is captured and NOTHING is spawned."""


def _shared_sessions_module() -> ModuleType:
    """The shared detector home (absent at HEAD — imported per test so this file still collects)."""
    return importlib.import_module(SHARED_SESSIONS_MODULE)


def _fake_proc(root: Path, processes: dict[int, tuple[list[str], Path]]) -> Path:
    """A ``/proc``-shaped tree: ``<pid>/cmdline`` (NUL-separated, NUL-terminated, as the kernel writes it)
    and a ``<pid>/cwd`` symlink, plus the non-pid entries every real ``/proc`` carries."""
    proc = root / "proc"
    proc.mkdir()
    for non_pid_entry in ("self", "sys", "meminfo"):
        (proc / non_pid_entry).mkdir()
    for pid, (argv, cwd) in processes.items():
        entry = proc / str(pid)
        entry.mkdir()
        (entry / "cmdline").write_bytes(b"\0".join(part.encode() for part in argv) + b"\0")
        (entry / "cwd").symlink_to(cwd)
    return proc


def _record_popen(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Replace ``subprocess.Popen`` (the base of ``run``/``check_output``/…) with a recorder that raises —
    so whatever spawn API the gate uses, the argv is captured and no suite ever starts."""
    argvs: list[list[str]] = []

    def _recording_popen(args: Any, *_args: Any, **_kwargs: Any) -> Any:
        argvs.append([str(part) for part in args])
        raise _PopenCaptured

    monkeypatch.setattr(subprocess, "Popen", _recording_popen)
    return argvs


def _stub_detector(
    monkeypatch: pytest.MonkeyPatch, live_sessions: list[tuple[int, str]]
) -> list[dict[str, Any]]:
    """Replace the SHARED detector; return the list of kwargs each call received."""
    calls: list[dict[str, Any]] = []

    def _detector(**kwargs: Any) -> list[tuple[int, str]]:
        calls.append(kwargs)
        return list(live_sessions)

    monkeypatch.setattr(_shared_sessions_module(), DETECTOR_NAME, _detector)
    return calls


def _shipped_worker_sized_gates() -> list[GateSpec]:
    """Every SHIPPED gate the worker policy governs: the junit-reader (pytest) gates."""
    return [
        spec
        for spec in GateManifest.load(DEFAULT_MANIFEST_PATH).gates
        if READERS[spec.reader] is JUnitReportReader
    ]


def _workers_in(argv: list[str]) -> str:
    """The value after ``-n`` in a rendered argv (exactly one ``-n``, or the render is ambiguous)."""
    assert argv.count(XDIST_WORKERS_FLAG) == 1, f"expected exactly one {XDIST_WORKERS_FLAG} in {argv}"
    return argv[argv.index(XDIST_WORKERS_FLAG) + 1]


_LIVE = [(OTHER_SESSION_PID, " ".join(LORE_SCRATCH_SESSION_ARGV))]
_ALONE: list[tuple[int, str]] = []
_BRANCHES = [
    pytest.param(_LIVE, RULED_WORKERS_WHEN_ANOTHER_SESSION_IS_LIVE, id="another-lore-session-live"),
    pytest.param(_ALONE, RULED_WORKERS_WHEN_ALONE, id="alone"),
]


# =========================================================================================================
# 1. The policy — one function, named constants, both branches, over the REAL detector and a fake /proc.
# =========================================================================================================
class TestTheWorkerPolicy:
    """Given who else is running, the policy answers ``"12"`` or ``"auto"`` — nothing else."""

    def test_the_policy_constants_carry_the_ruled_values(self) -> None:
        shared = _shared_sessions_module()
        assert shared.FLEET_CAPPED_PYTEST_WORKERS == RULED_WORKERS_WHEN_ANOTHER_SESSION_IS_LIVE
        assert shared.SOLO_PYTEST_WORKERS == RULED_WORKERS_WHEN_ALONE

    @pytest.mark.parametrize(
        ("others", "expected"),
        [
            pytest.param({}, RULED_WORKERS_WHEN_ALONE, id="empty-proc"),
            pytest.param(
                {OTHER_SESSION_PID: "scratch"},
                RULED_WORKERS_WHEN_ANOTHER_SESSION_IS_LIVE,
                id="one-scratch-session",
            ),
            pytest.param(
                {OTHER_SESSION_PID: "repo"}, RULED_WORKERS_WHEN_ANOTHER_SESSION_IS_LIVE, id="one-repo-session"
            ),
            # Ruling item 4 — no fleet session cap: three sessions are still "12", never 12/3 or a refusal.
            pytest.param(
                {OTHER_SESSION_PID: "scratch", SECOND_SESSION_PID: "repo", THIRD_SESSION_PID: "scratch"},
                RULED_WORKERS_WHEN_ANOTHER_SESSION_IS_LIVE,
                id="three-sessions-still-12",
            ),
            # The gate's OWN process never counts as "another" session, whatever its argv says.
            pytest.param({OWN_PID: "repo"}, RULED_WORKERS_WHEN_ALONE, id="only-own-pid"),
            # A worker and a non-test process are not sessions.
            pytest.param(
                {XDIST_WORKER_PID: "worker", NOT_A_SESSION_PID: "not-a-session"},
                RULED_WORKERS_WHEN_ALONE,
                id="worker-and-non-test-process",
            ),
        ],
    )
    def test_the_policy_over_the_real_detector(
        self, tmp_path: Path, others: dict[int, str], expected: str
    ) -> None:
        scratch_copy = tmp_path / "scratchpad" / "ref"
        scratch_copy.mkdir(parents=True)
        shapes: dict[str, tuple[list[str], Path]] = {
            "scratch": (LORE_SCRATCH_SESSION_ARGV, scratch_copy),
            "repo": (LORE_GATE_SESSION_ARGV, REPO_ROOT),
            "worker": (XDIST_WORKER_ARGV, scratch_copy),
            "not-a-session": (NOT_A_SESSION_ARGV, tmp_path),
        }
        proc = _fake_proc(tmp_path, {pid: shapes[shape] for pid, shape in others.items()})
        shared = _shared_sessions_module()
        assert shared.pytest_worker_count(proc_root=proc, own_pids={OWN_PID}) == expected

    @pytest.mark.parametrize(("live_sessions", "expected"), _BRANCHES)
    def test_the_policy_asks_the_shared_detector_at_call_time(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        live_sessions: list[tuple[int, str]],
        expected: str,
    ) -> None:
        # Sharing proven by MUTATION (ONE IMPLEMENTATION law): replace the shared detector and the policy
        # MUST follow it. The fake /proc says the OPPOSITE of the stub, so a policy with a private scan
        # answers wrong in this row.
        opposite = {} if live_sessions else {OTHER_SESSION_PID: (LORE_SCRATCH_SESSION_ARGV, tmp_path)}
        proc = _fake_proc(tmp_path, opposite)
        calls = _stub_detector(monkeypatch, live_sessions)
        shared = _shared_sessions_module()
        assert shared.pytest_worker_count(proc_root=proc, own_pids={OWN_PID}) == expected
        assert len(calls) == 1, f"the policy consulted the shared detector {len(calls)} times"


# =========================================================================================================
# 2. ONE detector — moved to the shared home, never cloned.
# =========================================================================================================
class TestThereIsOneDetector:
    """``other_pytest_sessions`` has ONE definition, and the acceptance driver uses THAT object."""

    def test_exactly_one_definition_across_the_non_test_scripts(self) -> None:
        definitions: list[str] = []
        for script in sorted(SCRIPTS_DIR.glob("*.py")):
            if script.name.startswith("test_"):
                continue
            for node in ast.walk(ast.parse(script.read_text(encoding="utf-8"))):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == DETECTOR_NAME:
                    definitions.append(f"{script.name}:{node.lineno}")
        assert len(definitions) == 1 and definitions[0].startswith(f"{SHARED_SESSIONS_MODULE}.py:"), (
            f"{DETECTOR_NAME} is defined at {definitions} — it must live ONCE, in "
            f"{SHARED_SESSIONS_MODULE}.py, which both the gate and the acceptance driver import "
            "(a second copy is copy #2)"
        )

    def test_the_acceptance_driver_re_exports_the_shared_detector(self) -> None:
        shared = _shared_sessions_module()
        assert getattr(concurrent_wire_acceptance, DETECTOR_NAME) is getattr(shared, DETECTOR_NAME), (
            "concurrent_wire_acceptance.other_pytest_sessions is not the shared object — a private copy"
        )


# =========================================================================================================
# 3. The gate — the REAL rendered argv of the SHIPPED manifest carries the resolved count.
# =========================================================================================================
class TestTheGateRendersTheResolvedCount:
    """What ``GateRunner`` would actually spawn, captured at ``Popen`` — generated over every shipped
    pytest-reader gate and over both render paths."""

    def test_the_shipped_manifest_has_a_gate_the_policy_governs(self) -> None:
        # Non-vacuity for every sweep below.
        assert _shipped_worker_sized_gates(), (
            "the shipped manifest has no pytest-reader gate — sweeps are empty"
        )

    @pytest.mark.parametrize(("live_sessions", "expected"), _BRANCHES)
    def test_every_pytest_gate_runs_with_the_policy_count(
        self, monkeypatch: pytest.MonkeyPatch, live_sessions: list[tuple[int, str]], expected: str
    ) -> None:
        detector_calls = _stub_detector(monkeypatch, live_sessions)
        spawned = _record_popen(monkeypatch)
        runner = GateRunner(REPO_ROOT)
        for spec in _shipped_worker_sized_gates():
            with pytest.raises(_PopenCaptured):
                runner.run(spec)
            argv = spawned[-1]
            assert _workers_in(argv) == expected, (
                f"gate {spec.id!r} would spawn {argv} — with the shared detector reporting {live_sessions!r} "
                f"the fleet policy says -n {expected}"
            )
            placeholder = pending_contract_gate.WORKERS_PLACEHOLDER
            assert not any(placeholder in part for part in argv), (
                f"an unresolved {placeholder} reached {argv}"
            )
        # The gate excluded ITSELF from "another session" (a gate whose own argv names pytest must not cap
        # itself), and asked once per run.
        assert len(detector_calls) == len(_shipped_worker_sized_gates())
        assert all(os.getpid() in call.get("own_pids", set()) for call in detector_calls), detector_calls

    @pytest.mark.parametrize(("live_sessions", "expected"), _BRANCHES)
    def test_forwarded_pytest_args_keep_the_policy_count(
        self, monkeypatch: pytest.MonkeyPatch, live_sessions: list[tuple[int, str]], expected: str
    ) -> None:
        # The second render path: ``_run_selected_gates`` copies the spec with the forwarded args appended.
        _stub_detector(monkeypatch, live_sessions)
        spawned = _record_popen(monkeypatch)
        manifest = GateManifest.load(DEFAULT_MANIFEST_PATH)
        forwarded = ["loremaster/tests/test_migration_wire.py"]
        for spec in _shipped_worker_sized_gates():
            with pytest.raises(_PopenCaptured):
                pending_contract_gate._run_selected_gates(  # noqa: SLF001
                    GateRunner(REPO_ROOT), manifest, [spec.id], forwarded
                )
            argv = spawned[-1]
            assert _workers_in(argv) == expected
            # DUAL (contract-503-d1, lead ruling 1, 2026-09-26): this line was
            # ``argv[-len(forwarded):] == forwarded`` — the forwarded args pinned at the argv TAIL.
            # Ruling 1 moves the policy's ``-n <count>`` AFTER every forwarded arg, which that tail pin
            # contradicts. Kept: every forwarded arg arrives, unchanged, contiguous and in order. The
            # position relative to the policy flag is pinned (stronger) by
            # TestThePolicyFlagIsTheLastWorkerFlag.
            assert _contiguous_run_start(argv, forwarded) is not None, f"the forwarded args were lost: {argv}"

    def test_the_count_is_resolved_when_the_gate_runs_not_when_it_loads(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A currency run spends minutes in typecheck before the pytest leg starts; a session that ends (or
        # starts) meanwhile must be seen. One runner, one spec, the fleet changes between two runs.
        spawned = _record_popen(monkeypatch)
        runner = GateRunner(REPO_ROOT)
        spec = _shipped_worker_sized_gates()[0]
        observed: list[str] = []
        for live_sessions in (_LIVE, _ALONE):
            _stub_detector(monkeypatch, live_sessions)
            with pytest.raises(_PopenCaptured):
                runner.run(spec)
            observed.append(_workers_in(spawned[-1]))
        assert observed == [RULED_WORKERS_WHEN_ANOTHER_SESSION_IS_LIVE, RULED_WORKERS_WHEN_ALONE], observed


# =========================================================================================================
# 4. The manifest — expresses the policy, and cannot hardcode past it.
# =========================================================================================================
_MANIFEST_TEMPLATE = textwrap.dedent(
    """\
    version: 1
    gates:
      - id: pytest
        description: "the suite"
        command: {command}
        reader: pytest_junit
        adjudicated_by: pending-contracts
    """
)
_PYTEST_HEAD = ["uv", "run", "pytest", "-q"]
_PYTEST_TAIL = ["-o", "junit_family=xunit1", "--junit-xml={junit_xml}"]


def _manifest_with(tmp_path: Path, worker_tokens: list[str]) -> Path:
    command = [*_PYTEST_HEAD, *worker_tokens, *_PYTEST_TAIL]
    path = tmp_path / "gates.yaml"
    path.write_text(_MANIFEST_TEMPLATE.format(command=command).replace("'", '"'))
    return path


class TestTheManifestExpressesThePolicy:
    """The manifest names the policy (a placeholder), never a count that bypasses it."""

    def test_every_shipped_pytest_gate_takes_its_count_from_the_placeholder(self) -> None:
        placeholder = pending_contract_gate.WORKERS_PLACEHOLDER
        for spec in _shipped_worker_sized_gates():
            command = list(spec.command)
            assert _workers_in(command) == placeholder, (
                f"shipped gate {spec.id!r} hardcodes -n {_workers_in(command)!r}; it must carry "
                f"-n {placeholder} so the fleet policy decides"
            )

    def test_no_shipped_gate_description_teaches_the_retired_count(self) -> None:
        # Rename-sweep law: prose describing behaviour must not keep teaching the retired literal.
        for spec in GateManifest.load(DEFAULT_MANIFEST_PATH).gates:
            assert RETIRED_WORKERS_LITERAL not in spec.description, (
                f"gate {spec.id!r}'s description still says {RETIRED_WORKERS_LITERAL!r}: {spec.description!r}"
            )

    @pytest.mark.parametrize(
        "worker_tokens",
        [
            pytest.param(["-n", "auto"], id="the-retired-literal"),
            pytest.param(["-n", "8"], id="a-literal-count"),
            pytest.param(["-n12"], id="joined-short-form"),
            pytest.param(["--numprocesses", "4"], id="long-form"),
            pytest.param(["--numprocesses=auto"], id="long-form-joined"),
        ],
    )
    def test_the_loader_refuses_a_hardcoded_worker_count(
        self, tmp_path: Path, worker_tokens: list[str]
    ) -> None:
        with pytest.raises(ManifestError):
            GateManifest.load(_manifest_with(tmp_path, worker_tokens))

    @pytest.mark.parametrize(
        "worker_tokens",
        [
            pytest.param(None, id="the-placeholder"),
            pytest.param([], id="no-worker-flag-runs-serial"),
        ],
    )
    def test_control_the_loader_accepts_the_placeholder_and_a_serial_gate(
        self, tmp_path: Path, worker_tokens: list[str] | None
    ) -> None:
        tokens = (
            [XDIST_WORKERS_FLAG, pending_contract_gate.WORKERS_PLACEHOLDER]
            if worker_tokens is None
            else worker_tokens
        )
        manifest = GateManifest.load(_manifest_with(tmp_path, tokens))
        assert manifest.ids == ("pytest",)


# =========================================================================================================
# 5. DELTA d1 (lead rulings 2026-09-26) — the policy wins at the STATE, forwarded worker flags are refused,
#    the clustered spelling is a pinned KNOWN BOUND, and own-pid exclusion holds on every render path.
# =========================================================================================================
FORWARDED_SELECTOR = "loremaster/tests/test_migration_wire.py"
SECOND_FORWARDED_SELECTOR = "loremaster/tests/test_migration_wire_budget_503.py"
# #503 F8: pytest's short-option clustering — ``-q`` then ``-n 3``. xdist honours it
# (REPORT-refactor-503.md §6 measured 3 workers; the in-process parser leg below agrees), and the shared
# helper does not see it.
CLUSTERED_WORKER_FLAG = "-qn3"
CLUSTERED_WORKER_COUNT = "3"
KNOWN_BOUND_F8_MESSAGE = (
    "this is a KNOWN BOUND (#503 F8) — if you closed it deliberately, delete this pin and say so"
)
# Re-open trigger for F8 (lead ruling 3, 2026-09-26): the first clustered worker flag seen in a REAL gate
# invocation. Until then ruling 1 (the policy flag is rendered LAST) makes the miss harmless.

# Forwarded args with NO worker flag — realistic ``pytest_args`` / ``--wave`` selectors an agent passes.
_FORWARDED_PLAIN = [FORWARDED_SELECTOR]
_FORWARDED_WITH_FLAGS = ["-x", "--tb=line", "-k", "budget and not slow", FORWARDED_SELECTOR]
_FORWARDED_TWO_SELECTORS = [FORWARDED_SELECTOR, SECOND_FORWARDED_SELECTOR]
_FORWARDED_CLUSTERED = [CLUSTERED_WORKER_FLAG, FORWARDED_SELECTOR]

# Every spelling ``_hardcoded_worker_counts`` recognises (its docstring: ``-n <x>``, ``-n<x>``,
# ``--numprocesses <x>``, ``--numprocesses=<x>``, and a flag with no value) — each placed as an agent would
# forward it, beside a real selector. ``-n auto`` is the habit CLAUDE.md's Quality-gates bullet teaches.
_REFUSED_FORWARDED_SPELLINGS = [
    pytest.param([FORWARDED_SELECTOR, "-n", "auto"], id="short-separate-auto"),
    pytest.param([FORWARDED_SELECTOR, "-n", "3"], id="short-separate-count"),
    pytest.param([FORWARDED_SELECTOR, "-n12"], id="short-joined"),
    pytest.param(["--numprocesses", "4", FORWARDED_SELECTOR], id="long-separate"),
    pytest.param(["--numprocesses=auto", FORWARDED_SELECTOR], id="long-joined"),
    pytest.param([FORWARDED_SELECTOR, "-n"], id="flag-without-value"),
]
# The single-token spellings — the only ones ``wave_gate``'s ``--wave=<token>`` can carry through argparse.
_REFUSED_SINGLE_TOKEN_SPELLINGS = ["-n12", "--numprocesses=auto"]

# The render paths a pytest-reader gate's argv is built on. Hand-listed, so it carries a COMPLETENESS pin
# (``test_the_render_path_domain_is_complete``) derived from the non-test scripts' AST.
RENDER_PATH_DIRECT = "GateRunner.run"
RENDER_PATH_SELECTED = "_run_selected_gates"
RENDER_PATH_GATE_CLI = "pending_contract_gate.main"
RENDER_PATH_WAVE_CLI = "wave_gate.main"
# (module file, enclosing function) of every non-test call of ``_run_selected_gates`` / ``GateRunner(``.
KNOWN_RENDER_CALLERS = {
    ("pending_contract_gate.py", "_dispatch"),
    ("wave_gate.py", "main"),
}
_RENDER_ENTRY_NAMES = {"_run_selected_gates", "GateRunner"}


@functools.cache
def _xdist_option_parser() -> Any:
    """pytest's OWN argument parser with pytest-xdist's options registered — the oracle for which worker
    count xdist would run. Read: ``_pytest/config/argparsing.py`` (``allow_abbrev=False``) and a live
    probe that agrees with REPORT-refactor-503.md §6's spawned-worker measurements (``-n 2 -n 3`` → 3,
    ``-qn3`` → 3)."""
    from _pytest.config import get_config  # noqa: PLC0415 — private pytest API, test-only oracle

    config = get_config()
    config.pluginmanager.import_plugin("xdist.plugin")
    return config._parser  # noqa: SLF001


def _xdist_resolved_workers(argv: list[str]) -> str:
    """The worker count pytest-xdist would resolve from the argv's pytest arguments (last ``-n`` wins)."""
    pytest_index = next((i for i, part in enumerate(argv) if Path(part).name == "pytest"), None)
    assert pytest_index is not None, f"no pytest token in the rendered argv {argv}"
    namespace = _xdist_option_parser().parse_known_args(argv[pytest_index + 1 :])
    return str(namespace.numprocesses)


def _contiguous_run_start(argv: list[str], run: list[str]) -> int | None:
    """Index where ``run`` appears in ``argv`` as a contiguous, in-order, unchanged slice (else None)."""
    for start in range(len(argv) - len(run) + 1):
        if argv[start : start + len(run)] == run:
            return start
    return None


def _one_gate_manifest(tmp_path: Path, spec: GateSpec) -> Path:
    """A manifest holding ONE shipped gate verbatim (a CLI that runs every gate reaches it first)."""
    path = tmp_path / f"gates-{spec.id}.yaml"
    path.write_text(yaml.safe_dump({"version": 1, "gates": [spec.model_dump(mode="json")]}))
    return path


def _wave_cli_argv(forwarded: list[str]) -> list[str]:
    """How an agent hands ``forwarded`` to ``wave_gate``: ``--wave=<t>`` for one token (the only form that
    carries a dash-led token through argparse), ``--wave a b`` for several plain selectors."""
    if len(forwarded) == 1:
        return [f"--wave={forwarded[0]}"]
    assert not any(part.startswith("-") for part in forwarded), forwarded
    return ["--wave", *forwarded]


def _render_on(
    path: str, spec: GateSpec, forwarded: list[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Drive ``spec`` through one render path with ``forwarded`` args; the Popen recorder captures the argv
    and raises ``_PopenCaptured`` (propagated to the caller)."""
    if path == RENDER_PATH_DIRECT:
        assert not forwarded, "the direct path forwards nothing"
        GateRunner(REPO_ROOT).run(spec)
    elif path == RENDER_PATH_SELECTED:
        manifest = GateManifest.load(DEFAULT_MANIFEST_PATH)
        pending_contract_gate._run_selected_gates(  # noqa: SLF001
            GateRunner(REPO_ROOT), manifest, [spec.id], forwarded
        )
    elif path == RENDER_PATH_GATE_CLI:
        pending_contract_gate.main(["--legs", spec.id, "--", *forwarded])
    elif path == RENDER_PATH_WAVE_CLI:
        monkeypatch.setattr(wave_gate, "DEFAULT_MANIFEST_PATH", _one_gate_manifest(tmp_path, spec))
        wave_gate.main(_wave_cli_argv(forwarded))
    else:  # pragma: no cover — a typo in a parametrize id
        raise AssertionError(f"unknown render path {path!r}")


_RENDER_CASES = [
    pytest.param(RENDER_PATH_DIRECT, [], id="direct"),
    pytest.param(RENDER_PATH_SELECTED, _FORWARDED_PLAIN, id="selected-plain"),
    pytest.param(RENDER_PATH_SELECTED, _FORWARDED_WITH_FLAGS, id="selected-with-flags"),
    pytest.param(RENDER_PATH_SELECTED, _FORWARDED_CLUSTERED, id="selected-clustered-F8"),
    pytest.param(RENDER_PATH_GATE_CLI, _FORWARDED_WITH_FLAGS, id="gate-cli-with-flags"),
    pytest.param(RENDER_PATH_GATE_CLI, _FORWARDED_CLUSTERED, id="gate-cli-clustered-F8"),
    pytest.param(RENDER_PATH_WAVE_CLI, _FORWARDED_PLAIN, id="wave-one-selector"),
    pytest.param(RENDER_PATH_WAVE_CLI, _FORWARDED_TWO_SELECTORS, id="wave-two-selectors"),
    pytest.param(RENDER_PATH_WAVE_CLI, [CLUSTERED_WORKER_FLAG], id="wave-clustered-F8"),
]


class TestThePolicyFlagIsTheLastWorkerFlag:
    """Lead ruling 1: the policy's ``-n <count>`` is the LAST worker flag of the argv handed to the runner, on
    every render path × both branches, so xdist runs the policy's count whatever was forwarded."""

    def test_the_render_path_domain_is_complete(self) -> None:
        # Completeness for the hand-listed RENDER paths: every non-test script function that builds a gate
        # runner or calls the leg-runner must be one this section drives. A new caller reddens here.
        callers: set[tuple[str, str]] = set()
        for script in sorted(SCRIPTS_DIR.glob("*.py")):
            if script.name.startswith("test_"):
                continue
            tree = ast.parse(script.read_text(encoding="utf-8"))
            for function in ast.walk(tree):
                if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                for node in ast.walk(function):
                    if isinstance(node, ast.Call):
                        called = node.func
                        name = called.attr if isinstance(called, ast.Attribute) else getattr(called, "id", "")
                        if name in _RENDER_ENTRY_NAMES:
                            callers.add((script.name, function.name))
        assert callers == KNOWN_RENDER_CALLERS, (
            f"the gate's render entry points are called from {sorted(callers)}; this section drives "
            f"{sorted(KNOWN_RENDER_CALLERS)} — add the new render path to _RENDER_CASES and "
            "KNOWN_RENDER_CALLERS"
        )

    @pytest.mark.parametrize(("live_sessions", "expected"), _BRANCHES)
    @pytest.mark.parametrize(("path", "forwarded"), _RENDER_CASES)
    def test_the_policy_count_is_the_last_worker_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        path: str,
        forwarded: list[str],
        live_sessions: list[tuple[int, str]],
        expected: str,
    ) -> None:
        _stub_detector(monkeypatch, live_sessions)
        spawned = _record_popen(monkeypatch)
        for spec in _shipped_worker_sized_gates():
            with pytest.raises(_PopenCaptured):
                _render_on(path, spec, forwarded, tmp_path, monkeypatch)
            argv = spawned[-1]
            # Behavioral: the count xdist itself would resolve from this argv.
            assert _xdist_resolved_workers(argv) == expected, (
                f"{path}: xdist would run {_xdist_resolved_workers(argv)!r} workers from {argv}, but the "
                f"fleet policy (detector reporting {live_sessions!r}) says {expected!r} — a forwarded worker "
                "flag overrode it, or the policy's flag is not the LAST one"
            )
            # State: the policy's pair is the last -n, and it follows every forwarded arg.
            policy_flag_index = len(argv) - 1 - argv[::-1].index(XDIST_WORKERS_FLAG)
            assert argv[policy_flag_index + 1] == expected, argv
            forwarded_start = _contiguous_run_start(argv, forwarded)
            assert forwarded_start is not None, f"{path}: the forwarded args {forwarded} were lost: {argv}"
            assert forwarded_start + len(forwarded) <= policy_flag_index, (
                f"{path}: the policy's {XDIST_WORKERS_FLAG} {expected} sits BEFORE the forwarded args in "
                f"{argv} — lead ruling 1 renders it after them, so no forwarded spelling can override it"
            )
            placeholder = pending_contract_gate.WORKERS_PLACEHOLDER
            assert not any(placeholder in part for part in argv), f"an unresolved {placeholder} in {argv}"

    @pytest.mark.parametrize(("live_sessions", "expected"), _BRANCHES)
    def test_a_clustered_worker_flag_in_the_manifest_still_loses_to_the_policy(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        live_sessions: list[tuple[int, str]],
        expected: str,
    ) -> None:
        # F8 at the LOADER door: the helper cannot see ``-qn3`` (pinned as a KNOWN BOUND below), so a manifest
        # may carry it AFTER the placeholder. Ruling 1 is a property of the RENDERED argv, so the policy must
        # still be the last worker flag (reading B of fork D1-F1 in REPORT-contract-503-d1.md).
        _stub_detector(monkeypatch, live_sessions)
        spawned = _record_popen(monkeypatch)
        manifest_path = _manifest_with(
            tmp_path, [XDIST_WORKERS_FLAG, pending_contract_gate.WORKERS_PLACEHOLDER, CLUSTERED_WORKER_FLAG]
        )
        (spec,) = GateManifest.load(manifest_path).gates
        with pytest.raises(_PopenCaptured):
            GateRunner(REPO_ROOT).run(spec)
        assert _xdist_resolved_workers(spawned[-1]) == expected, (
            f"a manifest {CLUSTERED_WORKER_FLAG} after -n {{workers}} overrode the policy: {spawned[-1]}"
        )


def _cli_outcome(
    capsys: pytest.CaptureFixture[str], call: Any, spawned: list[list[str]]
) -> tuple[int | None, str]:
    """Run a CLI main; return (exit code, stderr). A spawned gate is a FAILED refusal, reported loudly."""
    try:
        code = call()
    except _PopenCaptured:
        pytest.fail(f"a gate was SPAWNED with a forwarded worker flag, not refused: {spawned[-1]}")
    return code, capsys.readouterr().err


class TestForwardedWorkerFlagsAreRefused:
    """Lead ruling 2: a forwarded worker flag is REFUSED — loudly, before any gate spawns, naming the policy —
    by the ONE shared helper ``_hardcoded_worker_counts`` (never a second parser)."""

    @pytest.mark.parametrize("forwarded", _REFUSED_FORWARDED_SPELLINGS)
    def test_every_refused_row_is_a_spelling_the_shared_helper_recognises(self, forwarded: list[str]) -> None:
        # Ties this row domain to the helper's: a row the helper does not flag is not a refusal row.
        assert pending_contract_gate._hardcoded_worker_counts(forwarded), forwarded  # noqa: SLF001

    @pytest.mark.parametrize("forwarded", _REFUSED_FORWARDED_SPELLINGS)
    def test_the_leg_runner_refuses_before_any_gate_spawns(
        self, monkeypatch: pytest.MonkeyPatch, forwarded: list[str]
    ) -> None:
        _stub_detector(monkeypatch, _ALONE)
        spawned = _record_popen(monkeypatch)
        manifest = GateManifest.load(DEFAULT_MANIFEST_PATH)
        policy_name = _shared_sessions_module().pytest_worker_count.__name__
        # Every manifest leg, as both CLIs pass them: the refusal must come BEFORE the typecheck leg spends
        # minutes, not when the pytest leg is reached.
        with pytest.raises(Exception) as excinfo:  # noqa: PT011 — the type is spec-silent; see the CLI pins
            pending_contract_gate._run_selected_gates(  # noqa: SLF001
                GateRunner(REPO_ROOT), manifest, manifest.ids, forwarded
            )
        assert not isinstance(excinfo.value, _PopenCaptured), (
            f"forwarded {forwarded} was NOT refused — a gate was spawned: {spawned}"
        )
        assert spawned == [], f"a gate spawned before the refusal: {spawned}"
        assert policy_name in str(excinfo.value), (
            f"the refusal does not teach the policy ({policy_name}): {excinfo.value}"
        )

    @pytest.mark.parametrize("forwarded", _REFUSED_FORWARDED_SPELLINGS)
    def test_the_gate_cli_refuses_with_a_config_exit(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], forwarded: list[str]
    ) -> None:
        _stub_detector(monkeypatch, _ALONE)
        spawned = _record_popen(monkeypatch)
        policy_name = _shared_sessions_module().pytest_worker_count.__name__
        code, stderr = _cli_outcome(capsys, lambda: pending_contract_gate.main(["--", *forwarded]), spawned)
        # main()'s documented contract: 2 = the measurement did not happen (bad config / instrument).
        assert code == 2, f"exit {code}; stderr: {stderr}"
        assert policy_name in stderr, f"the CLI refusal does not name the policy ({policy_name}): {stderr}"
        assert spawned == []

    @pytest.mark.parametrize("token", _REFUSED_SINGLE_TOKEN_SPELLINGS)
    def test_the_wave_cli_refuses_with_a_config_exit(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        token: str,
    ) -> None:
        _stub_detector(monkeypatch, _ALONE)
        spawned = _record_popen(monkeypatch)
        policy_name = _shared_sessions_module().pytest_worker_count.__name__
        code, stderr = _cli_outcome(capsys, lambda: wave_gate.main([f"--wave={token}"]), spawned)
        assert code == 2, f"exit {code}; stderr: {stderr}"
        assert policy_name in stderr, f"the wave refusal does not name the policy ({policy_name}): {stderr}"
        assert spawned == []

    @pytest.mark.parametrize(
        "forwarded",
        [
            pytest.param(_FORWARDED_PLAIN, id="one-selector"),
            pytest.param(_FORWARDED_WITH_FLAGS, id="selector-and-flags"),
            pytest.param(["-p", "no:randomly", "-rfE", FORWARDED_SELECTOR], id="plugin-and-report-flags"),
        ],
    )
    def test_control_forwarded_args_without_a_worker_flag_pass_through_unchanged(
        self, monkeypatch: pytest.MonkeyPatch, forwarded: list[str]
    ) -> None:
        _stub_detector(monkeypatch, _ALONE)
        spawned = _record_popen(monkeypatch)
        manifest = GateManifest.load(DEFAULT_MANIFEST_PATH)
        for spec in _shipped_worker_sized_gates():
            with pytest.raises(_PopenCaptured):
                pending_contract_gate._run_selected_gates(  # noqa: SLF001
                    GateRunner(REPO_ROOT), manifest, [spec.id], forwarded
                )
            assert _contiguous_run_start(spawned[-1], forwarded) is not None, (
                f"forwarded {forwarded} did not reach the gate unchanged: {spawned[-1]}"
            )

    def test_the_refusal_routes_through_the_shared_helper(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # ONE IMPLEMENTATION, proven by MUTATION: swap the shared helper for one that flags ONLY a sentinel
        # token. The refusal must follow it both ways — refuse the sentinel, and let ``-n 3`` through (a
        # second, private parser would still refuse ``-n 3`` and so fails the second leg).
        sentinel = "--sentinel-worker-flag"
        manifest = GateManifest.load(DEFAULT_MANIFEST_PATH)
        spec = _shipped_worker_sized_gates()[0]

        def _stub_helper(command: Any) -> list[str]:
            return ["sentinel"] if sentinel in command else []

        monkeypatch.setattr(pending_contract_gate, "_hardcoded_worker_counts", _stub_helper)
        _stub_detector(monkeypatch, _ALONE)
        spawned = _record_popen(monkeypatch)
        with pytest.raises(Exception) as refused:  # noqa: PT011
            pending_contract_gate._run_selected_gates(  # noqa: SLF001
                GateRunner(REPO_ROOT), manifest, [spec.id], [sentinel, FORWARDED_SELECTOR]
            )
        assert not isinstance(refused.value, _PopenCaptured), (
            "the shared helper flagged the forwarded args and the leg-runner spawned anyway — the refusal "
            "does not consult pending_contract_gate._hardcoded_worker_counts"
        )
        assert spawned == []
        with pytest.raises(_PopenCaptured):
            pending_contract_gate._run_selected_gates(  # noqa: SLF001
                GateRunner(REPO_ROOT), manifest, [spec.id], [FORWARDED_SELECTOR, "-n", "3"]
            )


class TestKnownBoundClusteredWorkerFlag:
    """Lead ruling 3 — PIN THE MISS (#503 F8): the shared helper, and so the loader AND the forwarded refusal,
    do not recognise a clustered short flag. Harmless while ruling 1 holds (the rendered policy flag is last:
    ``TestThePolicyFlagIsTheLastWorkerFlag``'s ``…clustered-F8`` rows). Re-open trigger: the first clustered
    worker flag seen in a real gate invocation."""

    def test_the_clustered_flag_escapes_the_loader_and_the_forwarded_refusal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert pending_contract_gate._hardcoded_worker_counts([CLUSTERED_WORKER_FLAG]) == [], (  # noqa: SLF001
            KNOWN_BOUND_F8_MESSAGE
        )
        # The loader accepts a junit gate carrying it (beside the placeholder).
        manifest_path = _manifest_with(
            tmp_path, [XDIST_WORKERS_FLAG, pending_contract_gate.WORKERS_PLACEHOLDER, CLUSTERED_WORKER_FLAG]
        )
        try:
            GateManifest.load(manifest_path)
        except ManifestError as error:
            pytest.fail(f"the loader now refuses {CLUSTERED_WORKER_FLAG}: {error} — {KNOWN_BOUND_F8_MESSAGE}")
        # The forwarded path lets it through to a spawn (it is not refused).
        _stub_detector(monkeypatch, _ALONE)
        spawned = _record_popen(monkeypatch)
        manifest = GateManifest.load(DEFAULT_MANIFEST_PATH)
        spec = _shipped_worker_sized_gates()[0]
        try:
            pending_contract_gate._run_selected_gates(  # noqa: SLF001
                GateRunner(REPO_ROOT), manifest, [spec.id], _FORWARDED_CLUSTERED
            )
        except _PopenCaptured:
            pass
        except Exception as error:  # noqa: BLE001 — any refusal closes the bound
            pytest.fail(
                f"forwarded {CLUSTERED_WORKER_FLAG} is now refused ({error}) — {KNOWN_BOUND_F8_MESSAGE}"
            )
        assert spawned, KNOWN_BOUND_F8_MESSAGE
        # And the miss is REAL: xdist honours the clustered flag when nothing follows it.
        assert _xdist_resolved_workers(["pytest", CLUSTERED_WORKER_FLAG]) == CLUSTERED_WORKER_COUNT, (
            f"xdist no longer reads {CLUSTERED_WORKER_FLAG} as {CLUSTERED_WORKER_COUNT} workers — the bound "
            f"may be moot; {KNOWN_BOUND_F8_MESSAGE}"
        )


_OWN_PID_CASES = [
    pytest.param(RENDER_PATH_DIRECT, [], id="direct"),
    pytest.param(RENDER_PATH_SELECTED, _FORWARDED_PLAIN, id="selected-forwarded"),
    pytest.param(RENDER_PATH_GATE_CLI, _FORWARDED_PLAIN, id="gate-cli-forwarded"),
    pytest.param(RENDER_PATH_WAVE_CLI, _FORWARDED_PLAIN, id="wave-forwarded"),
]


class TestTheGateNeverCountsItself:
    """Lead ruling 4 (REPORT-refactor-503.md §1b): every resolution of the worker count excludes the gate's
    OWN process — on every render path, not only ``GateRunner.run`` direct. Declared wrong build: the
    refactor's survivor, a ``_run_selected_gates`` that pre-resolves ``{workers}`` with ``own_pids=set()``."""

    @pytest.mark.parametrize(("path", "forwarded"), _OWN_PID_CASES)
    def test_the_gates_own_pytest_process_does_not_cap_it(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, path: str, forwarded: list[str]
    ) -> None:
        # The REAL detector over a fake /proc whose ONLY pytest process is this gate itself (its argv names
        # pytest, as the gate's own leg does). Correct exclusion ⇒ alone ⇒ "auto"; counting itself ⇒ "12".
        shared = _shared_sessions_module()
        real_detector = shared.other_pytest_sessions
        fake_proc = _fake_proc(tmp_path, {os.getpid(): (LORE_GATE_SESSION_ARGV, REPO_ROOT)})
        calls: list[dict[str, Any]] = []

        def _detector_over_the_fake_proc(**kwargs: Any) -> list[tuple[int, str]]:
            calls.append(kwargs)
            sessions: list[tuple[int, str]] = real_detector(proc_root=fake_proc, own_pids=kwargs["own_pids"])
            return sessions

        monkeypatch.setattr(shared, DETECTOR_NAME, _detector_over_the_fake_proc)
        spawned = _record_popen(monkeypatch)
        for spec in _shipped_worker_sized_gates():
            with pytest.raises(_PopenCaptured):
                _render_on(path, spec, forwarded, tmp_path, monkeypatch)
            assert _xdist_resolved_workers(spawned[-1]) == RULED_WORKERS_WHEN_ALONE, (
                f"{path}: the gate counted ITSELF as another session and capped itself: {spawned[-1]}"
            )
        assert calls, f"{path}: the shared detector was never consulted"
        assert all(os.getpid() in call.get("own_pids", set()) for call in calls), (
            f"{path}: a worker-count resolution did not exclude the gate's own pid {os.getpid()}: {calls}"
        )


# =========================================================================================================
# 6. DELTA d2 (author ``contract-503-d2``, lead brief 2026-09-26 after REPORT-refactor-503-d1.md §1a/§2b;
#    GREEN-dated to HEAD ``f66a190`` + the d1 build in the working tree) — the dropped D1-F3 rider, and two
#    pinned KNOWN BOUNDS (D-1: the non-running CLI modes; ``--maxprocesses``).
# =========================================================================================================
# The refusal's stderr label. NOT exposed by production as a constant (both ``pending_contract_gate.main`` and
# ``wave_gate.main`` spell it inline), so the contract carries the literal.
REFUSED_ARGUMENT_LABEL = "REFUSED ARGUMENT"
# The two mislabels lead ruling D1-F3 names ("never MANIFEST ERROR for a CLI arg"; wave_gate's twin is CONFIG
# ERROR). The DERIVED sweep below must contain both, or it has gone vacuous.
RULED_OUT_LABELS = {"MANIFEST ERROR", "CONFIG ERROR"}
RULED_OUT_EXCEPTION = "ManifestError"
REFUSING_CLIS: tuple[ModuleType, ...] = (pending_contract_gate, wave_gate)


def _exit_two_handlers(cli: ModuleType) -> dict[str, str]:
    """``{caught exception name: stderr label}`` for every ``except`` in ``cli.main`` that prints a label —
    DERIVED from the CLI's source, so a new exit-2 family joins the sweep without editing this contract."""
    handlers: dict[str, str] = {}
    tree = ast.parse(textwrap.dedent(inspect.getsource(cli.main)))
    for handler in ast.walk(tree):
        if not isinstance(handler, ast.ExceptHandler) or handler.type is None:
            continue
        names = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
        for statement in ast.walk(handler):
            if (
                isinstance(statement, ast.Call)
                and getattr(statement.func, "id", "") == "print"
                and statement.args
                and isinstance(statement.args[0], ast.JoinedStr)
                and isinstance(statement.args[0].values[0], ast.Constant)
            ):
                label = str(statement.args[0].values[0].value).split(":", 1)[0]
                handlers.update({ast.unparse(name): label for name in names})
    return handlers


def _other_exit_two_families() -> tuple[set[str], tuple[type[BaseException], ...]]:
    """Every stderr label and exception type EITHER CLI uses for an exit-2 cause OTHER than a refused
    argument."""
    labels: set[str] = set()
    types: set[type[BaseException]] = set()
    refused_type = pending_contract_gate.ForwardedWorkerCountError
    for cli in REFUSING_CLIS:
        for name, label in _exit_two_handlers(cli).items():
            caught = getattr(cli, name.rsplit(".", 1)[-1])
            if caught is refused_type:
                continue
            labels.add(label)
            types.add(caught)
    return labels, tuple(types)


class TestTheRefusalIsLabelledAsARefusedArgument:
    """Lead ruling D1-F3 (2026-09-26): a refused forwarded worker count is "a typed error of its own, never
    MANIFEST ERROR for a CLI arg". CLASS: a refused CLI argument is never labelled as a manifest / config /
    registry / instrument fault, on every CLI that surfaces it. Survivor this kills: REPORT-refactor-503-d1.md
    §2b build B (``_refuse_forwarded_worker_counts`` raising ``ManifestError``), which passed 76/76."""

    def test_the_other_exit_two_families_are_derived_non_vacuously(self) -> None:
        labels, types = _other_exit_two_families()
        assert labels >= RULED_OUT_LABELS, f"the derived mislabel set {labels} lost a ruled-out label"
        assert REFUSED_ARGUMENT_LABEL not in labels, labels
        assert pending_contract_gate.ManifestError in types, types
        for cli in REFUSING_CLIS:
            handlers = _exit_two_handlers(cli)
            assert handlers.get(pending_contract_gate.ForwardedWorkerCountError.__name__) == (
                REFUSED_ARGUMENT_LABEL
            ), f"{cli.__name__}.main has no {REFUSED_ARGUMENT_LABEL!r} handler for the refusal: {handlers}"

    @pytest.mark.parametrize("forwarded", _REFUSED_FORWARDED_SPELLINGS)
    def test_the_leg_runner_raises_the_typed_refusal(
        self, monkeypatch: pytest.MonkeyPatch, forwarded: list[str]
    ) -> None:
        _stub_detector(monkeypatch, _ALONE)
        _record_popen(monkeypatch)
        manifest = GateManifest.load(DEFAULT_MANIFEST_PATH)
        with pytest.raises(Exception) as excinfo:  # noqa: PT011 — the type IS the assertion, below
            pending_contract_gate._run_selected_gates(  # noqa: SLF001
                GateRunner(REPO_ROOT), manifest, manifest.ids, forwarded
            )
        refused = excinfo.value
        assert isinstance(refused, pending_contract_gate.ForwardedWorkerCountError), (
            f"forwarded {forwarded} was refused with {type(refused).__name__}, not "
            f"ForwardedWorkerCountError (lead ruling D1-F3): {refused}"
        )
        _, other_types = _other_exit_two_families()
        assert not isinstance(refused, other_types), (
            f"the typed refusal is ALSO a {[t.__name__ for t in other_types if isinstance(refused, t)]} — "
            f"a CLI catching that family first would print its label for a CLI argument (D1-F3 rules out "
            f"{RULED_OUT_EXCEPTION})"
        )

    @pytest.mark.parametrize("forwarded", _REFUSED_FORWARDED_SPELLINGS)
    def test_the_gate_cli_labels_it_a_refused_argument(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], forwarded: list[str]
    ) -> None:
        _stub_detector(monkeypatch, _ALONE)
        spawned = _record_popen(monkeypatch)
        _, stderr = _cli_outcome(capsys, lambda: pending_contract_gate.main(["--", *forwarded]), spawned)
        self._assert_labelled_as_a_refused_argument(stderr, f"pending_contract_gate -- {forwarded}")

    @pytest.mark.parametrize("token", _REFUSED_SINGLE_TOKEN_SPELLINGS)
    def test_the_wave_cli_labels_it_a_refused_argument(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], token: str
    ) -> None:
        _stub_detector(monkeypatch, _ALONE)
        spawned = _record_popen(monkeypatch)
        _, stderr = _cli_outcome(capsys, lambda: wave_gate.main([f"--wave={token}"]), spawned)
        self._assert_labelled_as_a_refused_argument(stderr, f"wave_gate --wave={token}")

    @staticmethod
    def _assert_labelled_as_a_refused_argument(stderr: str, invocation: str) -> None:
        assert f"{REFUSED_ARGUMENT_LABEL}:" in stderr, (
            f"{invocation}: the refusal is not labelled {REFUSED_ARGUMENT_LABEL!r}: {stderr!r}"
        )
        other_labels, _ = _other_exit_two_families()
        mislabels = sorted(label for label in other_labels | RULED_OUT_LABELS if f"{label}:" in stderr)
        assert not mislabels, (
            f"{invocation}: a refused CLI argument was labelled {mislabels} (lead ruling D1-F3: never "
            f"MANIFEST ERROR / CONFIG ERROR for a CLI arg): {stderr!r}"
        )


# KNOWN BOUND #503 D-1 (REPORT-refactor-503-d1.md §1a, measured 2026-09-26): the gate CLI's non-running modes
# accept ``pytest_args`` and neither refuse nor apply them — ``--derive`` spawns the typecheck gate with the
# forwarded args dropped; ``--verify-registry`` spawns nothing and exits 0. Harmless to the worker count (the
# args never reach a pytest gate), but a forwarded argument vanishes without a word.
# RE-OPEN TRIGGER: either mode starts running the pytest gate (then the args WOULD be applied, unrefused).
KNOWN_BOUND_D1_MESSAGE = (
    "this is a KNOWN BOUND (#503 D-1) — if you closed it deliberately, delete this pin and say so"
)
KNOWN_BOUND_D1_UNREFUSED_MODES = {"--derive", "--verify-registry"}
# The one mode flag that runs the leg-runner, and so refuses (lead ruling 2).
REFUSING_MODE_FLAGS = {"--currency"}
_D1_FORWARDED = [FORWARDED_SELECTOR, "-n", "3"]


def _gate_cli_mode_flags() -> list[str]:
    """Every boolean MODE flag of the gate CLI, DERIVED from its parser (store_true actions)."""
    return sorted(
        action.option_strings[-1]
        for action in pending_contract_gate._build_parser()._actions  # noqa: SLF001
        if action.option_strings and action.nargs == 0 and action.const is True
    )


class TestKnownBoundNonRunningModesIgnoreForwardedArgs:
    """KNOWN BOUND #503 D-1 — PIN THE MISS, generated over the gate CLI's mode flags."""

    def test_every_mode_flag_is_classified(self) -> None:
        # Completeness: a new mode must be classified here as refusing or as a pinned miss.
        assert set(_gate_cli_mode_flags()) == REFUSING_MODE_FLAGS | KNOWN_BOUND_D1_UNREFUSED_MODES, (
            f"the gate CLI's mode flags are {_gate_cli_mode_flags()}; classify the new one in "
            "REFUSING_MODE_FLAGS or KNOWN_BOUND_D1_UNREFUSED_MODES"
        )

    @pytest.mark.parametrize("mode", _gate_cli_mode_flags())
    def test_a_forwarded_worker_flag_under_each_mode(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], mode: str
    ) -> None:
        _stub_detector(monkeypatch, _ALONE)
        spawned = _record_popen(monkeypatch)
        try:
            code: int | None = pending_contract_gate.main([mode, "--", *_D1_FORWARDED])
        except _PopenCaptured:
            code = None
        stderr = capsys.readouterr().err
        refused = code == 2 and f"{REFUSED_ARGUMENT_LABEL}:" in stderr and spawned == []
        if mode in REFUSING_MODE_FLAGS:
            assert refused, f"{mode} -- {_D1_FORWARDED}: exit {code}, spawned {spawned}, stderr {stderr!r}"
            return
        assert not refused, f"{mode} now refuses {_D1_FORWARDED} — {KNOWN_BOUND_D1_MESSAGE}"
        # ...and the forwarded args are not APPLIED either: nothing spawned carries them.
        assert all(_contiguous_run_start(argv, _D1_FORWARDED) is None for argv in spawned), (
            f"{mode} now forwards {_D1_FORWARDED} to a gate: {spawned} — the re-open trigger fired; "
            f"{KNOWN_BOUND_D1_MESSAGE}"
        )

    def test_derive_spawns_the_typecheck_gate_and_drops_the_args(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _stub_detector(monkeypatch, _ALONE)
        spawned = _record_popen(monkeypatch)
        with pytest.raises(_PopenCaptured):
            pending_contract_gate.main(["--derive", "--", *_D1_FORWARDED])
        typecheck = pending_contract_gate._typecheck_gate(GateManifest.load(DEFAULT_MANIFEST_PATH))  # noqa: SLF001
        assert spawned == [list(typecheck.command)], (
            f"--derive spawned {spawned}, not the typecheck gate {list(typecheck.command)} alone — "
            f"{KNOWN_BOUND_D1_MESSAGE}"
        )

    def test_verify_registry_spawns_nothing_and_does_not_refuse(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _stub_detector(monkeypatch, _ALONE)
        spawned = _record_popen(monkeypatch)
        code = pending_contract_gate.main(["--verify-registry", "--", *_D1_FORWARDED])
        stderr = capsys.readouterr().err
        assert code != 2 and f"{REFUSED_ARGUMENT_LABEL}:" not in stderr, (
            f"--verify-registry exit {code}, stderr {stderr!r} — {KNOWN_BOUND_D1_MESSAGE}"
        )
        assert spawned == [], f"--verify-registry spawned {spawned} — {KNOWN_BOUND_D1_MESSAGE}"


# KNOWN BOUND #503 maxprocesses (REPORT-refactor-503-d1.md §1d P1 + §2d, measured 2026-09-26): a forwarded
# ``--maxprocesses`` is not a spelling the shared helper refuses, and xdist applies it as a CAP
# (``numprocesses = min(numprocesses, maxprocesses)`` in ``xdist.plugin.pytest_cmdline_main``, xdist 3.8.0),
# so it can only LOWER the policy's count — it errs in the safe direction.
# RE-OPEN TRIGGER: xdist makes --maxprocesses able to RAISE the worker count.
KNOWN_BOUND_MAXPROCESSES_MESSAGE = (
    "this is a KNOWN BOUND (#503 maxprocesses) — if you closed it deliberately, delete this pin and say so"
)
MAXPROCESSES_FLAG = "--maxprocesses"
# ``-n auto`` resolves through xdist's own ``pytest_xdist_auto_num_workers``; pinned via its env var
# to this box's measured core count (CLAUDE.md: "-n auto = 64 workers on this box") so the row is hermetic.
XDIST_AUTO_WORKERS_ENV = "PYTEST_XDIST_AUTO_NUM_WORKERS"
AUTO_WORKERS_ON_THIS_BOX = 64
FLEET_CAPPED_WORKERS = int(RULED_WORKERS_WHEN_ANOTHER_SESSION_IS_LIVE)

# (branch, --maxprocesses Y, policy count X as an int, expected = min(X, Y) — hand-computed from the
# lead's rule)
_MAXPROCESSES_CASES = [
    pytest.param(_LIVE, 2, FLEET_CAPPED_WORKERS, 2, id="live-12-cap-2-lowers"),
    pytest.param(_LIVE, 64, FLEET_CAPPED_WORKERS, 12, id="live-12-cap-64-no-raise"),
    pytest.param(_ALONE, 8, AUTO_WORKERS_ON_THIS_BOX, 8, id="alone-auto64-cap-8-lowers"),
    pytest.param(_ALONE, 128, AUTO_WORKERS_ON_THIS_BOX, 64, id="alone-auto64-cap-128-no-raise"),
]


def _xdist_worker_processes(argv: list[str]) -> int:
    """How many worker processes pytest-xdist would START for ``argv``: parsed by the SAME oracle parser as
    ``_xdist_resolved_workers`` (``_xdist_option_parser``), then handed to xdist's OWN
    ``pytest_cmdline_main`` — that hook, not the parser, resolves ``auto`` and applies ``--maxprocesses``, so
    the cap is xdist's code, never re-implemented here."""
    import xdist.plugin  # type: ignore[import-untyped]  # noqa: PLC0415 — test-only oracle (no stubs)

    pytest_index = next((i for i, part in enumerate(argv) if Path(part).name == "pytest"), None)
    assert pytest_index is not None, f"no pytest token in the rendered argv {argv}"
    namespace = _xdist_option_parser().parse_known_args(argv[pytest_index + 1 :])
    config = SimpleNamespace(
        option=namespace,
        getoption=lambda name, default=None: getattr(namespace, name, default),
        getvalue=lambda name: getattr(namespace, name),
    )
    config.hook = SimpleNamespace(pytest_xdist_auto_num_workers=xdist.plugin.pytest_xdist_auto_num_workers)
    xdist.plugin.pytest_cmdline_main(config)
    return len(namespace.tx)


class TestKnownBoundMaxprocessesOnlyLowersTheCount:
    """KNOWN BOUND #503 maxprocesses — PIN THE MISS (not refused) AND its harmlessness (xdist's count for the
    policy's ``-n X`` plus a forwarded ``--maxprocesses=Y`` is min(X, Y), never above the policy)."""

    @pytest.mark.parametrize("joined", [pytest.param(True, id="joined"), pytest.param(False, id="separate")])
    @pytest.mark.parametrize(("live_sessions", "cap", "policy_workers", "expected"), _MAXPROCESSES_CASES)
    def test_a_forwarded_maxprocesses_is_not_refused_and_never_raises_the_count(
        self,
        monkeypatch: pytest.MonkeyPatch,
        live_sessions: list[tuple[int, str]],
        cap: int,
        policy_workers: int,
        expected: int,
        joined: bool,
    ) -> None:
        monkeypatch.setenv(XDIST_AUTO_WORKERS_ENV, str(AUTO_WORKERS_ON_THIS_BOX))
        cap_tokens = [f"{MAXPROCESSES_FLAG}={cap}"] if joined else [MAXPROCESSES_FLAG, str(cap)]
        forwarded = [FORWARDED_SELECTOR, *cap_tokens]
        # Half 1 — the miss: the shared helper does not flag it, and the leg-runner spawns with it.
        assert pending_contract_gate._hardcoded_worker_counts(forwarded) == [], (  # noqa: SLF001
            f"the shared helper now flags {cap_tokens} — {KNOWN_BOUND_MAXPROCESSES_MESSAGE}"
        )
        _stub_detector(monkeypatch, live_sessions)
        spawned = _record_popen(monkeypatch)
        manifest = GateManifest.load(DEFAULT_MANIFEST_PATH)
        for spec in _shipped_worker_sized_gates():
            try:
                pending_contract_gate._run_selected_gates(  # noqa: SLF001
                    GateRunner(REPO_ROOT), manifest, [spec.id], forwarded
                )
            except _PopenCaptured:
                pass
            except Exception as error:  # noqa: BLE001 — any refusal closes the bound
                pytest.fail(
                    f"forwarded {cap_tokens} is now refused ({error}) — {KNOWN_BOUND_MAXPROCESSES_MESSAGE}"
                )
            argv = spawned[-1]
            assert _contiguous_run_start(argv, cap_tokens) is not None, (
                f"{cap_tokens} did not reach the gate: {argv} — {KNOWN_BOUND_MAXPROCESSES_MESSAGE}"
            )
            # Half 2 — the harmlessness, through xdist's own code: min(policy, cap), never above the policy.
            workers = _xdist_worker_processes(argv)
            assert workers <= policy_workers, (
                f"xdist would start {workers} workers from {argv}, ABOVE the policy's {policy_workers} — "
                f"--maxprocesses can now raise the count; the re-open trigger fired. "
                f"{KNOWN_BOUND_MAXPROCESSES_MESSAGE}"
            )
            assert workers == expected, (
                f"xdist would start {workers} workers from {argv}; policy -n {policy_workers} capped by "
                f"{MAXPROCESSES_FLAG}={cap} is {expected}. {KNOWN_BOUND_MAXPROCESSES_MESSAGE}"
            )
