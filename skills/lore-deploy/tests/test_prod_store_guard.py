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
  every xdist worker (lore's runs use ``-n 8``);
* EVERY attempt fails the report of the node in whose PHASE it happened — fixture setup and
  teardown at every scope (function, class, module, session) and module import (collection)
  — and it does so regardless of a later ``pytest.skip`` or an ``xfail`` mark (lead ruling,
  ``docs/plans/v2/receipts/2026-10-31-165/RULING-guard-forks.md`` §Addendum). A guard that
  only watches the test function's own window drops, or mis-charges, an attempt made by a
  shared fixture — exactly the T8 shape (a shared fixture defaulting to the production URL).

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
INNER_DOOR_MODULES = ("test_inner_prod_doors.py", "test_inner_benign.py")

# --- phase doors: attempts made OUTSIDE the test function's own call ---------------------
# Every attempt here is SWALLOWED, so only a recorder that charges the right report can fail
# the right node. Each module is run in the order of PHASE_MODULES, in ONE session, so the
# "next node" after each attempt is a known innocent test.
_INNER_PHASE_PRELUDE = _INNER_PRELUDE + textwrap.dedent(
    """

    def _swallowed_attempt():
        try:
            socket.create_connection(("127.0.0.1", TARGET_PORT), timeout=2).close()
        except BaseException:
            pass
    """
)

# Collection: the attempt happens while the module is IMPORTED, before any test runs.
_INNER_PHASE_IMPORT = _INNER_PHASE_PRELUDE + textwrap.dedent(
    f"""

    # The bootstrap already refuses to exec pytest un-isolated; re-check BEFORE the import-time
    # attempt, because the prelude's isolation fixture only runs after collection.
    if os.readlink("/proc/self/ns/net") == os.environ["{ENV_HOST_NETNS}"]:
        pytest.exit("inner session is NOT network-isolated", returncode={NOT_ISOLATED_EXIT})
    _swallowed_attempt()


    def test_import_door_module_test():
        assert TARGET_PORT > 0
    """
)

# Collection, then a module-level SKIP: the common "probe the store at import, skip the module
# when it is unreachable" idiom. Under a guard the refusal is what makes it unreachable. A
# transient stub serves the probe so the module does NOT skip with no guard (the control).
_INNER_PHASE_IMPORT_SKIP = _INNER_PHASE_PRELUDE + textwrap.dedent(
    f"""

    if os.readlink("/proc/self/ns/net") == os.environ["{ENV_HOST_NETNS}"]:
        pytest.exit("inner session is NOT network-isolated", returncode={NOT_ISOLATED_EXIT})
    _import_stub = _StubServer(("127.0.0.1", TARGET_PORT), _StubHandler)
    threading.Thread(target=_import_stub.serve_forever, daemon=True).start()
    try:
        with socket.create_connection(("127.0.0.1", TARGET_PORT), timeout=2):
            pass
    except OSError:
        pytest.skip("store unreachable", allow_module_level=True)
    finally:
        _import_stub.shutdown()
        _import_stub.server_close()


    def test_import_skip_door_module_test():
        assert TARGET_PORT > 0
    """
)

# Module-scoped fixture SETUP: runs inside the setup phase of its FIRST user, which is not
# the module's first test (so "charge the module's first test" is a wrong answer).
_INNER_PHASE_MODULE_SETUP = _INNER_PHASE_PRELUDE + textwrap.dedent(
    """

    @pytest.fixture(scope="module")
    def module_fixture_that_dials():
        _swallowed_attempt()
        return TARGET_PORT


    def test_phase_innocent_first():
        # The first test the session RUNS: an import-time attempt deferred to "the next
        # setup" would land here.
        assert TARGET_PORT > 0


    def test_module_fixture_first_user(module_fixture_that_dials):
        assert module_fixture_that_dials > 0


    def test_module_fixture_second_user(module_fixture_that_dials):
        # Same fixture, cached: no attempt in this test's phases.
        assert module_fixture_that_dials > 0
    """
)

# Class-scoped fixture SETUP.
_INNER_PHASE_CLASS_SETUP = _INNER_PHASE_PRELUDE + textwrap.dedent(
    """

    @pytest.fixture(scope="class")
    def class_fixture_that_dials():
        _swallowed_attempt()
        return TARGET_PORT


    class TestClassScopedFixture:
        def test_class_fixture_first_user(self, class_fixture_that_dials):
            assert class_fixture_that_dials > 0

        def test_class_fixture_second_user(self, class_fixture_that_dials):
            assert class_fixture_that_dials > 0
    """
)

# Module-scoped fixture TEARDOWN: runs inside the teardown phase of the module's LAST test.
_INNER_PHASE_MODULE_TEARDOWN = _INNER_PHASE_PRELUDE + textwrap.dedent(
    """

    @pytest.fixture(scope="module")
    def module_fixture_that_dials_on_teardown():
        yield TARGET_PORT
        _swallowed_attempt()


    def test_module_teardown_fixture_user(module_fixture_that_dials_on_teardown):
        assert module_fixture_that_dials_on_teardown > 0
    """
)

# Skip and xfail. The skip door is the realistic one: a shared fixture probes the store and
# SKIPS when it is unreachable — and the guard's own refusal is what makes it unreachable.
_INNER_PHASE_SKIP_XFAIL = _INNER_PHASE_PRELUDE + textwrap.dedent(
    """

    @pytest.fixture(scope="module")
    def store_or_skip():
        try:
            with socket.create_connection(("127.0.0.1", TARGET_PORT), timeout=2):
                pass
        except OSError:
            pytest.skip("store unreachable")
        return TARGET_PORT


    def test_innocent_after_module_teardown():
        # The first test after the previous module's teardown attempt.
        assert TARGET_PORT > 0


    def test_skip_fixture_first_user(store_or_skip):
        assert store_or_skip > 0


    def test_skip_fixture_second_user(store_or_skip):
        # Re-raises the CACHED skip under a guard: no attempt in this test's phases.
        assert store_or_skip > 0


    @pytest.mark.xfail(reason="an xfail mark must not absorb a production-store attempt")
    def test_xfail_marked_attempt():
        # Not swallowed: under a guard the refusal raises, and the xfail mark would absorb it.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            sock.connect(("127.0.0.1", TARGET_PORT))
    """
)

# Session-scoped fixture TEARDOWN: runs inside the teardown phase of the session's LAST test.
_INNER_PHASE_SESSION_TEARDOWN = _INNER_PHASE_PRELUDE + textwrap.dedent(
    """

    @pytest.fixture(scope="session")
    def session_fixture_that_dials_on_teardown():
        yield TARGET_PORT
        _swallowed_attempt()


    def test_session_teardown_fixture_user(session_fixture_that_dials_on_teardown):
        assert session_fixture_that_dials_on_teardown > 0
    """
)

# Run order (command-line order) — load-bearing: each module's first test is the innocent
# "next node" after the previous module's last attempt, and the session-teardown user is last.
PHASE_MODULES: dict[str, str] = {
    "test_inner_phase_import.py": _INNER_PHASE_IMPORT,
    "test_inner_phase_import_skip.py": _INNER_PHASE_IMPORT_SKIP,
    "test_inner_phase_module_setup.py": _INNER_PHASE_MODULE_SETUP,
    "test_inner_phase_class_setup.py": _INNER_PHASE_CLASS_SETUP,
    "test_inner_phase_module_teardown.py": _INNER_PHASE_MODULE_TEARDOWN,
    "test_inner_phase_skip_xfail.py": _INNER_PHASE_SKIP_XFAIL,
    "test_inner_phase_session_teardown.py": _INNER_PHASE_SESSION_TEARDOWN,
}
PHASE_TREE = "tests"
# junit names a COLLECTION failure after the module's dotted path (``mangle_test_address``
# in ``_pytest.junitxml``, pytest 9.0.3, read 2026-10-31): nodeid ``skills/lore-deploy/tests/
# test_inner_phase_import.py`` -> testcase name ``skills.lore-deploy.tests.test_inner_phase_import``.
IMPORT_COLLECT_CASE = f"skills.lore-deploy.{PHASE_TREE}.test_inner_phase_import"
IMPORT_MODULE_TEST = "test_import_door_module_test"
IMPORT_SKIP_COLLECT_CASE = f"skills.lore-deploy.{PHASE_TREE}.test_inner_phase_import_skip"
IMPORT_SKIP_MODULE_TEST = "test_import_skip_door_module_test"

# Each charged node -> the door whose attempt it must carry.
PHASE_CHARGED: dict[str, str] = {
    "test_module_fixture_first_user": "module-scoped fixture setup",
    "test_class_fixture_first_user": "class-scoped fixture setup",
    "test_module_teardown_fixture_user": "module-scoped fixture teardown",
    "test_session_teardown_fixture_user": "session-scoped fixture teardown",
    IMPORT_COLLECT_CASE: "module import (collection)",
    IMPORT_SKIP_COLLECT_CASE: "module import followed by a module-level skip",
    "test_skip_fixture_first_user": "attempt followed by pytest.skip",
    "test_xfail_marked_attempt": "attempt in an xfail-marked test",
}
# Every node NOT charged, with the outcome it has under a correct guard.
PHASE_UNCHARGED_OUTCOME: dict[str, str] = {
    IMPORT_MODULE_TEST: "passed",  # absent when its module's collection failed
    IMPORT_SKIP_MODULE_TEST: "passed",  # absent when its module's collection failed or skipped
    "test_phase_innocent_first": "passed",
    "test_module_fixture_second_user": "passed",
    "test_class_fixture_second_user": "passed",
    "test_innocent_after_module_teardown": "passed",
    "test_skip_fixture_second_user": "skipped",  # the cached skip, re-raised without an attempt
}
PHASE_COLLECT_CASES = frozenset({IMPORT_COLLECT_CASE, IMPORT_SKIP_COLLECT_CASE})
PHASE_TESTS = frozenset(
    {*(name for name in PHASE_CHARGED if name not in PHASE_COLLECT_CASES), *PHASE_UNCHARGED_OUTCOME}
)
# What a guarded run must report whatever the guard does; the import modules' own tests and
# their collection cases appear depending on whether collection failed (or skipped).
PHASE_ALWAYS_REPORTED = PHASE_TESTS - {IMPORT_MODULE_TEST, IMPORT_SKIP_MODULE_TEST}
PHASE_MAY_REPORT = PHASE_TESTS | PHASE_COLLECT_CASES


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
        for module_name, source in PHASE_MODULES.items():
            (tree_dir / module_name).write_text(source, encoding="utf-8")
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
    mirror: Path,
    tree: str,
    label: str,
    extra_args: tuple[str, ...] = (),
    *,
    control: bool = False,
    modules: tuple[str, ...] = INNER_DOOR_MODULES,
    must_report: frozenset[str] = ALL_INNER_TESTS,
    may_report: frozenset[str] = ALL_INNER_TESTS,
) -> InnerRun:
    """Run ``modules`` of ``tree`` in an isolated namespace and read their verdicts.

    The run must report every name in ``must_report`` and nothing outside ``may_report``.
    """
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
    args += [str(tree_dir / module_name) for module_name in modules]
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
    missing = must_report - set(cases)
    extra = set(cases) - may_report
    assert not missing and not extra, (
        f"inner session did not report the expected inner tests: "
        f"missing={sorted(missing)} extra={sorted(extra)}\n{output}"
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


# --- phase attribution (lead ruling, RULING-guard-forks.md §Addendum) ----------------------
# Extra inner args for the phase session: an import-time attempt must fail its module's
# COLLECTION, and pytest otherwise interrupts the whole session on a collection error, so
# the later phase modules would never run. The flag changes session continuation only.
PHASE_RUN_ARGS = ("--continue-on-collection-errors",)


@pytest.fixture(scope="module")
def phase_run(mirror: Path) -> InnerRun:
    """The phase modules, in PHASE_MODULES order, as ONE serial session under the real conftests."""
    return _run_inner(
        mirror,
        PHASE_TREE,
        "phase-guarded",
        PHASE_RUN_ARGS,
        modules=tuple(PHASE_MODULES),
        must_report=PHASE_ALWAYS_REPORTED,
        may_report=PHASE_MAY_REPORT,
    )


@pytest.fixture(scope="module")
def phase_control_run(mirror: Path) -> InnerRun:
    """The phase modules with every conftest/plugin disabled: the no-guard baseline."""
    return _run_inner(
        mirror,
        PHASE_TREE,
        "phase-control",
        PHASE_RUN_ARGS,
        control=True,
        modules=tuple(PHASE_MODULES),
        must_report=PHASE_TESTS,
        may_report=PHASE_TESTS,
    )


class TestPhaseControlWithoutAnyGuard:
    """Positive control for the phase doors: with no guard, every phase inner test PASSES.

    So each phase pin below that goes RED is the guard's charging, never a broken door: the
    stub answers, the import-time attempt is harmless, the probe fixture does not skip, and the
    xfail-marked test XPASSes (non-strict, which junit files as a pass).
    """

    def test_every_phase_inner_test_passes_without_a_guard(self, phase_control_run: InnerRun) -> None:
        not_passed = {
            name: case.outcome
            for name, case in phase_control_run.cases.items()
            if case.outcome != "passed"
        }
        assert not not_passed, (
            f"phase control (no guard) has non-passing inner tests {not_passed}:\n"
            f"{phase_control_run.output}"
        )


class TestEveryAttemptFailsTheNodeWhosePhaseMadeIt:
    """∀ attempts: the report of the node whose phase made the attempt fails and names the port.

    Wrong guards each pin catches (none of them is hypothetical — the first is the reference
    guard this contract was satisfied against before the ruling):
    * "clear the record when the TEST's own fixture sets up, check when it tears down":
      discards attempts made by module/class/session fixtures and at import, and checks before
      a module/session fixture's teardown has run;
    * "check pending attempts at the next test's setup": charges module-teardown and
      import-time attempts to an INNOCENT next test, and drops the session-teardown attempt;
    * "flip a passed report to failed": misses the skipped report (skip after an attempt) and
      the xfailed report (the xfail mark absorbs the guard's own refusal).
    """

    @pytest.mark.parametrize("charged", tuple(PHASE_CHARGED), ids=tuple(PHASE_CHARGED.values()))
    def test_attempt_fails_the_node_whose_phase_made_it(self, phase_run: InnerRun, charged: str) -> None:
        _assert_blocked_and_named(phase_run, charged, f"phase: {PHASE_CHARGED[charged]}")

    def test_no_node_whose_phases_made_no_attempt_is_charged(self, phase_run: InnerRun) -> None:
        # Quantified over every REPORTED node that is not charged: a guard that defers an
        # attempt to "whoever runs next", or never drains, fails an innocent node here.
        wrong = {
            name: case.outcome
            for name, case in phase_run.cases.items()
            if name not in PHASE_CHARGED and case.outcome != PHASE_UNCHARGED_OUTCOME[name]
        }
        assert not wrong, (
            f"nodes that made no attempt have the wrong outcome {wrong} "
            f"(expected {PHASE_UNCHARGED_OUTCOME}):\n{phase_run.output}"
        )
