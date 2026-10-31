"""Contract: no test in the lore-deploy skill trees can reach the PRODUCTION SurrealDB store.

The lore law is "never point tests at :18500" (repo ``CLAUDE.md`` §Deploy). The skill's
own scaffold writes ``url: ws://127.0.0.1:18500/rpc`` into every new ``lore.yaml``, and
``test_lore_deploy.py`` carries that URL as ``_RPC_URL``. Today every test stubs the
network; nothing stops the next one from not doing so. This file pins the guard that
does (operator-approved run-wide guard, 2026-10-31, packet #165):

* a test that attempts a connection to loopback port 18500 FAILS, and its own failure
  names the attempt (``18500``);
* it fails even when the code under test SWALLOWS the guard's exception — production's
  ``lore_deploy._probe_surreal_health`` catches every ``OSError``, so a raise-only guard
  would pass silently;
* the failure lands on the test that made the attempt, never on a neighbour;
* connections to any other port — the TEST store's :18000 included — behave exactly as
  they would with no guard;
* the guard is live for tests collected from BOTH ``scripts/`` and ``tests/``, and in
  every xdist worker (lore's runs use ``-n 8``).

HOW THIS IS EXERCISED WITHOUT EVER DIALLING PRODUCTION (load-bearing, read before editing)
------------------------------------------------------------------------------------
Each pin runs an INNER pytest session in a subprocess. That subprocess first enters a
private user + network namespace (``os.unshare``), brings up its own loopback, and only
then execs pytest. Inside that namespace, 127.0.0.1:18500 is a STUB store this file
starts itself; the host's production store is unreachable by construction. The inner
modules additionally refuse to run (``pytest.exit``) if their network namespace equals the
host's. So a RED run — no guard at all — connects to the stub and nothing else.
If the namespace cannot be built (e.g. a container whose seccomp forbids user
namespaces), every test here SKIPS with that reason rather than run un-isolated: a
contract that dials production when its guard is missing is forbidden even while RED.

The inner sessions see the REAL conftest chain: the outer fixture mirrors the repository
layout under a tmp dir and symlinks every ``conftest.py`` (and every non-test ``.py``
helper beside it) found on the path ``<repo>/skills/lore-deploy/{scripts,tests}``, plus the
real ``pyproject.toml``. So whichever conftest the guard lives in, the inner sessions load
it exactly as ``uv run python -m pytest -q . ../tests`` from ``scripts/`` (or the root
``testpaths`` run) does. A CONTROL session over the same mirror with conftests disabled
proves every "door" inner test PASSES with no guard — i.e. each RED below is the guard's
absence, never a broken fixture.

Inner sources never spell the production port literally (they read it from the
environment), so ``18500`` in a failure's text can only come from the guard naming the
attempt — never from pytest echoing the inner test's source line.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

import pytest

# --- conventions -----------------------------------------------------------------------
# The PRODUCTION lore-surreal store's port. Source of truth: repo CLAUDE.md §Deploy
# (":18500 is production lore-surreal — never point tests at it") and the skill's own
# scaffold, ``lore_deploy._scaffold_lore_yaml`` (``url: ws://127.0.0.1:18500/rpc``).
PROD_STORE_PORT = 18500
# The TEST store's port (CLAUDE.md §Deploy: "spike-surreal ws://127.0.0.1:18000 is the
# test store"). A guard must leave it alone.
TEST_STORE_PORT = 18000
# A loopback port nothing listens on (discard). Inside the private namespace nothing can.
DEAD_PORT = 9
# The literal the guard's failure must carry to "name the attempt".
PROD_PORT_TEXT = str(PROD_STORE_PORT)

SKILL_DIR = Path(__file__).resolve().parents[1]  # skills/lore-deploy
REPO_ROOT = SKILL_DIR.parents[1]
SKILL_TREES = ("scripts", "tests")
# Exit code the bootstrap uses when it cannot build the isolated namespace.
ISOLATION_UNAVAILABLE_EXIT = 77
# Exit code the inner modules use if they find themselves NOT isolated.
NOT_ISOLATED_EXIT = 99
INNER_RUN_TIMEOUT_S = 120

# Environment handed to the inner session (names carry no port literal).
ENV_PROD_PORT = "GUARD_CONTRACT_PROD_PORT"
ENV_TEST_STORE_PORT = "GUARD_CONTRACT_TEST_STORE_PORT"
ENV_DEAD_PORT = "GUARD_CONTRACT_DEAD_PORT"
ENV_HOST_NETNS = "GUARD_CONTRACT_HOST_NETNS"
ENV_SCRIPTS_DIR = "GUARD_CONTRACT_SCRIPTS_DIR"

# --- the isolation bootstrap (runs in the inner subprocess, BEFORE pytest is imported) ---
_BOOTSTRAP = textwrap.dedent(
    f"""
    import fcntl, os, socket, struct, sys
    host_netns = os.readlink("/proc/self/ns/net")
    uid, gid = os.getuid(), os.getgid()
    try:
        os.unshare(os.CLONE_NEWUSER | os.CLONE_NEWNET)
        with open("/proc/self/setgroups", "w") as handle:
            handle.write("deny")
        with open("/proc/self/uid_map", "w") as handle:
            handle.write(f"0 {{uid}} 1")
        with open("/proc/self/gid_map", "w") as handle:
            handle.write(f"0 {{gid}} 1")
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # SIOCSIFFLAGS on "lo": IFF_UP | IFF_LOOPBACK | IFF_RUNNING
        fcntl.ioctl(probe, 0x8914, struct.pack("16sH14x", b"lo", 0x1 | 0x8 | 0x40))
        probe.close()
    except (AttributeError, OSError) as exc:
        print(f"ISOLATION-UNAVAILABLE: {{exc!r}}", flush=True)
        sys.exit({ISOLATION_UNAVAILABLE_EXIT})
    inner_netns = os.readlink("/proc/self/ns/net")
    if inner_netns == host_netns:
        print("ISOLATION-UNAVAILABLE: namespace did not change", flush=True)
        sys.exit({ISOLATION_UNAVAILABLE_EXIT})
    print(f"NETNS host={{host_netns}} inner={{inner_netns}}", flush=True)
    env = dict(os.environ, {ENV_HOST_NETNS}=host_netns)
    os.execve(sys.executable, [sys.executable, "-m", "pytest", *sys.argv[1:]], env)
    """
)

# --- inner test modules ------------------------------------------------------------------
# Shared prelude: refuse to run un-isolated, then serve a stub store on the production
# port and on the test-store port inside the private namespace.
_INNER_PRELUDE = textwrap.dedent(
    f"""
    import http.server
    import os
    import socket
    import sys
    import threading
    import urllib.request

    import pytest

    TARGET_PORT = int(os.environ["{ENV_PROD_PORT}"])
    TEST_STORE_PORT = int(os.environ["{ENV_TEST_STORE_PORT}"])
    DEAD_PORT = int(os.environ["{ENV_DEAD_PORT}"])


    class _StubHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        def log_message(self, *args):
            pass


    class _StubServer(http.server.ThreadingHTTPServer):
        allow_reuse_address = True
        allow_reuse_port = True
        daemon_threads = True


    @pytest.fixture(autouse=True, scope="module")
    def _isolated_stub_stores():
        if os.readlink("/proc/self/ns/net") == os.environ["{ENV_HOST_NETNS}"]:
            pytest.exit("inner session is NOT network-isolated", returncode={NOT_ISOLATED_EXIT})
        servers = [_StubServer(("127.0.0.1", port), _StubHandler) for port in (TARGET_PORT, TEST_STORE_PORT)]
        for server in servers:
            threading.Thread(target=server.serve_forever, daemon=True).start()
        yield
        for server in servers:
            server.shutdown()
            server.server_close()
    """
)

# Doors to the production port. Each one PASSES when no guard exists (the stub answers),
# so each must FAIL once the guard is in place.
_INNER_PROD_DOORS = _INNER_PRELUDE + textwrap.dedent(
    """

    def test_door_raw_socket_connect():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            sock.connect(("127.0.0.1", TARGET_PORT))


    def test_door_urlopen_health_on_loopback_ip():
        with urllib.request.urlopen(f"http://127.0.0.1:{TARGET_PORT}/health", timeout=2) as response:
            assert response.status == 200


    def test_door_urlopen_health_on_localhost():
        with urllib.request.urlopen(f"http://localhost:{TARGET_PORT}/health", timeout=2) as response:
            assert response.status == 200


    def test_swallow_production_probe_surreal_health():
        # The REAL production function: it catches every OSError and returns a bool.
        sys.path.insert(0, os.environ["GUARD_CONTRACT_SCRIPTS_DIR"])
        import lore_deploy

        lore_deploy._probe_surreal_health(f"http://127.0.0.1:{TARGET_PORT}/health")


    def test_swallow_any_exception_around_create_connection():
        try:
            socket.create_connection(("127.0.0.1", TARGET_PORT), timeout=2).close()
        except BaseException:
            pass


    def test_swallow_by_construction_connect_ex():
        # connect_ex reports failure as an errno and never raises.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            sock.connect_ex(("127.0.0.1", TARGET_PORT))


    def test_zz_innocent_neighbour_after_swallowed_attempts():
        # Runs after the attempts above (file order). Makes no connection at all.
        assert TARGET_PORT > 0
    """
)

# Benign traffic: must behave exactly as with no guard.
_INNER_BENIGN = _INNER_PRELUDE + textwrap.dedent(
    """

    def test_benign_dead_port_is_refused_as_usual():
        with pytest.raises(ConnectionRefusedError):
            socket.create_connection(("127.0.0.1", DEAD_PORT), timeout=2)


    def test_benign_test_store_health_answers():
        with urllib.request.urlopen(f"http://127.0.0.1:{TEST_STORE_PORT}/health", timeout=2) as response:
            assert response.status == 200


    def test_benign_test_store_raw_socket_connects():
        with socket.create_connection(("localhost", TEST_STORE_PORT), timeout=2):
            pass
    """
)

PROD_DOOR_TESTS = (
    "test_door_raw_socket_connect",
    "test_door_urlopen_health_on_loopback_ip",
    "test_door_urlopen_health_on_localhost",
    "test_swallow_production_probe_surreal_health",
    "test_swallow_any_exception_around_create_connection",
    "test_swallow_by_construction_connect_ex",
)
NEIGHBOUR_TEST = "test_zz_innocent_neighbour_after_swallowed_attempts"
BENIGN_TESTS = (
    "test_benign_dead_port_is_refused_as_usual",
    "test_benign_test_store_health_answers",
    "test_benign_test_store_raw_socket_connects",
)
ALL_INNER_TESTS = frozenset((*PROD_DOOR_TESTS, NEIGHBOUR_TEST, *BENIGN_TESTS))


@dataclass(frozen=True)
class InnerCase:
    """One inner testcase's verdict, read from the inner session's junit XML."""

    name: str
    outcome: str  # "passed" | "failed" | "error" | "skipped"
    text: str  # every failure/error message + body, concatenated


@dataclass(frozen=True)
class InnerRun:
    """An inner pytest session: its verdict per test, plus its raw output for diagnostics."""

    cases: dict[str, InnerCase]
    returncode: int
    output: str

    def case(self, name: str) -> InnerCase:
        assert name in self.cases, f"inner test {name} never reported; inner output:\n{self.output}"
        return self.cases[name]


def _mirror_repo(destination: Path) -> Path:
    """Mirror the repo layout the skill tests see: the conftest chain + helpers, symlinked.

    Every ``conftest.py`` and every non-``test_*`` ``.py`` file in each directory on the
    path from the repo root to ``skills/lore-deploy/{scripts,tests}`` is symlinked to the
    REAL file, so the inner session loads whatever conftest chain production has.
    """
    mirror = destination / "repo"
    chain = [
        Path("."),
        Path("skills"),
        Path("skills/lore-deploy"),
        *(Path("skills/lore-deploy") / tree for tree in SKILL_TREES),
    ]
    for relative in chain:
        target_dir = mirror / relative
        target_dir.mkdir(parents=True, exist_ok=True)
        real_dir = REPO_ROOT / relative
        for real_file in real_dir.glob("*.py"):
            if real_file.name.startswith("test_"):
                continue
            if relative == Path(".") and real_file.name != "conftest.py":
                continue
            (target_dir / real_file.name).symlink_to(real_file)
    (mirror / "pyproject.toml").symlink_to(REPO_ROOT / "pyproject.toml")
    for tree in SKILL_TREES:
        tree_dir = mirror / "skills/lore-deploy" / tree
        (tree_dir / "test_inner_prod_doors.py").write_text(_INNER_PROD_DOORS, encoding="utf-8")
        (tree_dir / "test_inner_benign.py").write_text(_INNER_BENIGN, encoding="utf-8")
    return mirror


# Worst-first: a test that failed in its call AND errored at teardown is "failed".
_OUTCOME_SEVERITY = {"passed": 0, "skipped": 1, "error": 2, "failed": 3}
_JUNIT_TAG_OUTCOME = {"failure": "failed", "error": "error", "skipped": "skipped"}


def _parse_junit(path: Path) -> dict[str, InnerCase]:
    """Read one verdict per inner test name.

    junit writes a SECOND ``<testcase>`` for a test whose call failed and whose teardown
    then errored (serial and xdist alike), so entries sharing a name are MERGED: the worst
    outcome wins and every failure text is kept. Coverage is checked by the caller.
    """
    cases: dict[str, InnerCase] = {}
    for testcase in ElementTree.parse(path).getroot().iter("testcase"):
        name = testcase.get("name", "")
        outcome = "passed"
        texts: list[str] = []
        for child in testcase:
            if child.tag in _JUNIT_TAG_OUTCOME:
                tag_outcome = _JUNIT_TAG_OUTCOME[child.tag]
                if _OUTCOME_SEVERITY[tag_outcome] > _OUTCOME_SEVERITY[outcome]:
                    outcome = tag_outcome
                texts.append(f"{child.get('message', '')}\n{child.text or ''}")
        if name in cases:
            earlier = cases[name]
            if _OUTCOME_SEVERITY[earlier.outcome] > _OUTCOME_SEVERITY[outcome]:
                outcome = earlier.outcome
            texts.insert(0, earlier.text)
        cases[name] = InnerCase(name=name, outcome=outcome, text="\n".join(texts))
    return cases


def _run_inner(
    mirror: Path, tree: str, label: str, extra_args: tuple[str, ...] = (), *, control: bool = False
) -> InnerRun:
    """Run the inner modules of ``tree`` in an isolated namespace and read their verdicts."""
    tree_dir = mirror / "skills/lore-deploy" / tree
    junit = mirror.parent / f"junit-{label}.xml"
    bootstrap = mirror.parent / "netns_bootstrap.py"
    bootstrap.write_text(_BOOTSTRAP, encoding="utf-8")
    args = [
        "-q",
        "-p",
        "no:cacheprovider",
        "--tb=short",
        f"--rootdir={mirror}",
        f"--junitxml={junit}",
        *extra_args,
    ]
    env = {key: value for key, value in os.environ.items() if not key.startswith("PYTEST_")}
    if control:
        # No conftest, no ini addopts, no auto-loaded plugins: the run "without the guard".
        args += ["--noconftest", "-o", "addopts=--import-mode=importlib"]
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    args += [str(tree_dir / "test_inner_prod_doors.py"), str(tree_dir / "test_inner_benign.py")]
    env.update(
        {
            ENV_PROD_PORT: str(PROD_STORE_PORT),
            ENV_TEST_STORE_PORT: str(TEST_STORE_PORT),
            ENV_DEAD_PORT: str(DEAD_PORT),
            ENV_SCRIPTS_DIR: str(mirror / "skills/lore-deploy/scripts"),
        }
    )
    completed = subprocess.run(
        [sys.executable, str(bootstrap), *args],
        cwd=mirror,
        env=env,
        capture_output=True,
        text=True,
        timeout=INNER_RUN_TIMEOUT_S,
        check=False,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    if completed.returncode == ISOLATION_UNAVAILABLE_EXIT and "ISOLATION-UNAVAILABLE" in output:
        pytest.skip(
            "cannot build a private network namespace, refusing to run inner tests un-isolated: "
            f"{output.strip()}"
        )
    assert completed.returncode != NOT_ISOLATED_EXIT, f"inner session was NOT isolated:\n{output}"
    netns_lines = [line for line in completed.stdout.splitlines() if line.startswith("NETNS ")]
    assert netns_lines, f"isolation receipt missing:\n{output}"
    host_part, inner_part = netns_lines[0].removeprefix("NETNS ").split(" ")
    assert host_part.removeprefix("host=") != inner_part.removeprefix("inner="), netns_lines[0]
    assert junit.exists(), f"inner session wrote no junit report:\n{output}"
    cases = _parse_junit(junit)
    assert set(cases) == ALL_INNER_TESTS, (
        f"inner session did not report exactly the inner tests: "
        f"missing={sorted(ALL_INNER_TESTS - set(cases))} "
        f"extra={sorted(set(cases) - ALL_INNER_TESTS)}\n{output}"
    )
    return InnerRun(cases=cases, returncode=completed.returncode, output=output)


@pytest.fixture(scope="module")
def mirror(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _mirror_repo(tmp_path_factory.mktemp("prod-store-guard"))


@pytest.fixture(scope="module")
def guarded_runs(mirror: Path) -> dict[str, InnerRun]:
    """One serial inner session per skill tree, under the real conftest chain."""
    return {tree: _run_inner(mirror, tree, f"guarded-{tree}") for tree in SKILL_TREES}


@pytest.fixture(scope="module")
def xdist_run(mirror: Path) -> InnerRun:
    """The ``tests`` tree's inner modules under two xdist workers (lore runs ``-n 8``)."""
    return _run_inner(mirror, "tests", "xdist-tests", ("-n", "2"))


@pytest.fixture(scope="module")
def control_run(mirror: Path) -> InnerRun:
    """The same inner modules with every conftest/plugin disabled: the no-guard baseline."""
    return _run_inner(mirror, "scripts", "control", control=True)


def _assert_blocked_and_named(run: InnerRun, name: str, where: str) -> None:
    case = run.case(name)
    assert case.outcome in ("failed", "error"), (
        f"[{where}] {name} reached the production port and the guard did not fail it "
        f"(outcome={case.outcome}).\ninner output:\n{run.output}"
    )
    assert PROD_PORT_TEXT in case.text, (
        f"[{where}] {name} failed, but its failure does not name the attempt (no {PROD_PORT_TEXT!r} "
        f"in its failure text):\n{case.text}"
    )


class TestControlWithoutAnyGuard:
    """Positive control: with no guard, every inner test PASSES.

    This is what makes each RED below the guard's absence and not a broken fixture: the
    stub store answers on the production port, so every door test succeeds unguarded.
    Green before and after the guard exists.
    """

    def test_every_inner_test_passes_without_a_guard(self, control_run: InnerRun) -> None:
        not_passed = {
            name: case.outcome for name, case in control_run.cases.items() if case.outcome != "passed"
        }
        assert not not_passed, (
            f"control (no guard) has non-passing inner tests {not_passed}:\n{control_run.output}"
        )


@pytest.mark.parametrize("tree", SKILL_TREES)
class TestProductionPortAttemptsFailTheAttemptingTest:
    """Pins 1, 2, 4, 5: every door to :18500 fails the test that used it, in both trees."""

    def test_raw_socket_connect_fails_and_names_the_port(
        self, guarded_runs: dict[str, InnerRun], tree: str
    ) -> None:
        _assert_blocked_and_named(guarded_runs[tree], "test_door_raw_socket_connect", tree)

    @pytest.mark.parametrize(
        "door",
        ["test_door_urlopen_health_on_loopback_ip", "test_door_urlopen_health_on_localhost"],
    )
    def test_urlopen_health_fails_and_names_the_port(
        self, guarded_runs: dict[str, InnerRun], tree: str, door: str
    ) -> None:
        _assert_blocked_and_named(guarded_runs[tree], door, tree)

    @pytest.mark.parametrize(
        "swallower",
        [
            "test_swallow_production_probe_surreal_health",
            "test_swallow_any_exception_around_create_connection",
            "test_swallow_by_construction_connect_ex",
        ],
    )
    def test_attempt_fails_even_when_the_code_swallows_the_error(
        self, guarded_runs: dict[str, InnerRun], tree: str, swallower: str
    ) -> None:
        # The recorder leg: a raise-only guard passes all three of these.
        _assert_blocked_and_named(guarded_runs[tree], swallower, tree)

    def test_failure_lands_on_the_attempting_test_not_its_neighbour(
        self, guarded_runs: dict[str, InnerRun], tree: str
    ) -> None:
        neighbour = guarded_runs[tree].case(NEIGHBOUR_TEST)
        assert neighbour.outcome == "passed", (
            f"[{tree}] a test that made no connection was failed (outcome={neighbour.outcome}): "
            f"the guard mis-attributes an earlier test's attempt.\n{neighbour.text}"
        )


@pytest.mark.parametrize("tree", SKILL_TREES)
class TestOtherPortsAreUntouched:
    """Pin 3: traffic to any other port behaves exactly as with no guard."""

    @pytest.mark.parametrize("benign", BENIGN_TESTS)
    def test_benign_connection_behaves_as_without_the_guard(
        self, guarded_runs: dict[str, InnerRun], control_run: InnerRun, tree: str, benign: str
    ) -> None:
        guarded = guarded_runs[tree].case(benign)
        baseline = control_run.case(benign)
        assert guarded.outcome == baseline.outcome == "passed", (
            f"[{tree}] {benign}: guarded outcome {guarded.outcome!r} "
            f"vs no-guard {baseline.outcome!r}.\n{guarded.text}"
        )


class TestGuardIsLiveInEveryXdistWorker:
    """Lore's targeted runs use ``-n 8``: a guard that records only in the controller is blind."""

    @pytest.mark.parametrize("door", PROD_DOOR_TESTS)
    def test_every_door_fails_under_xdist(self, xdist_run: InnerRun, door: str) -> None:
        _assert_blocked_and_named(xdist_run, door, "xdist")

    @pytest.mark.parametrize("benign", (*BENIGN_TESTS, NEIGHBOUR_TEST))
    def test_benign_tests_still_pass_under_xdist(self, xdist_run: InnerRun, benign: str) -> None:
        case = xdist_run.case(benign)
        assert case.outcome == "passed", f"[xdist] {benign} outcome={case.outcome}\n{case.text}"
