"""Shared pytest fixtures for the loremaster test suite.

Currently limited to import-path wiring for sibling test helper modules (see
below). Qdrant was retired from the boot path AND its real-server test harness
at P8a (the store tests now run against the real local SurrealDB dev server via
``_surreal_harness.py``, not a real Qdrant collection).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import tempfile
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from hypothesis.configuration import set_hypothesis_home_dir
from loremaster.logging_setup import LORE_NAMESPACES

# Make sibling test helper modules (e.g. ``_extension_helpers``) importable as
# plain top-level modules under ``--import-mode=importlib``: that mode does NOT
# add each test file's directory to ``sys.path``, and ``loremaster`` is the
# *installed* package (with no ``tests`` subpackage), so neither a bare
# ``_extension_helpers`` nor a ``loremaster.tests._extension_helpers`` import
# would otherwise resolve. Inserting this directory keeps the shared fake
# extension in one reviewable module without polluting the shipped package.
_TESTS_DIR = str(Path(__file__).parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

# r4b-fix (packet 63c, amendment 13 §G4 rider): ``hypothesis`` writes its CACHES (the unicode charmap, the
# per-module constants scan) under ``<cwd>/.hypothesis`` even with ``database=None`` — measured 2026-09-25 on
# hypothesis 6.168.1. Redirect its home OUTSIDE the tree, per-user, so no suite run writes into the repo
# (the in-image conformance run mounts the repo ``:ro``; hypothesis already swallows a failed cache write
# there — ``except Exception: pass`` in ``internal/charmap.py`` / ``internal/constants_ast.py`` — so this is
# tree hygiene, not a correctness fix). ``set_hypothesis_home_dir`` is the package's own seam.
_HYPOTHESIS_HOME = Path(tempfile.gettempdir()) / f"lore-hypothesis-{os.getuid()}"
set_hypothesis_home_dir(_HYPOTHESIS_HOME)

# The env-var NAME the suite's fixtures reference for the REQUIRED P8c
# ``anthropic`` block. Mirrors the production ``lore.yaml`` (api_key_env:
# ANTHROPIC_API_KEY) so every fixture that boots through ``load_config`` — which
# resolves this key EAGERLY — sees a value.
_ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"


@pytest.fixture(autouse=True)
def _dummy_anthropic_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Export a dummy ``ANTHROPIC_API_KEY`` so eager key resolution passes.

    ``load_config`` resolves ``anthropic.api_key_env`` at load (fail-fast). Suite
    fixtures reference ``ANTHROPIC_API_KEY``; setting a dummy value here lets any
    test that boots through ``load_config`` succeed without a real key. Tests that
    exercise the MISSING/EMPTY-key path use a DISTINCT env-var name (or delenv
    this one via their own monkeypatch) and are unaffected — function-scoped
    monkeypatch restores the environment after each test.
    """
    monkeypatch.setenv(_ANTHROPIC_API_KEY_ENV, "test-dummy-anthropic-key")


@pytest.fixture(autouse=True)
def _reset_cosine_floor_drift_state() -> Iterator[None]:
    """Reset finding #74's cosine-floor drift-disarm state around every test.

    ``AppContext._build_index_status`` (loremaster/server.py) calls
    ``loremaster.search.apply_cosine_floor_drift_check`` on EVERY
    ``lore_index()``/``AppContext.index()`` read — a REAL mutation of
    ``loremaster.search``'s module-level runtime state (an attribute on
    ``_cosine_floor_runtime_state``), not something a caller opts into.
    Because most fixtures across this suite index only a handful of files
    (nowhere near the production stamp's measured file count), an unrelated
    test calling ``ctx.index()`` trips drift detection for real and disarms
    the absence verdict for every test that runs AFTER it in the same
    session — exactly the state-leakage class the global CLAUDE.md's
    lifecycle-test rule warns about (proven live: the full ``test_mcp_
    server.py`` suite failed 4 tests in ``TestSearchParamsCutBudgetAndTeachingMiss``
    until this fixture was added; each of those 4 passed in isolation).
    Autouse (not opt-in) because the hazard is triggered by ANY
    ``ctx.index()`` call, not just the tests that know this mechanism
    exists. ``monkeypatch`` cannot express this reset (it would restore
    whatever value was ALREADY leaked in at test start, not force a clean
    baseline), so this calls the module's own test-only reset function
    directly, before AND after every test.
    """
    import loremaster.search as search_module

    search_module._reset_cosine_floor_drift_state_for_tests()
    yield
    search_module._reset_cosine_floor_drift_state_for_tests()


@pytest.fixture(autouse=True)
def _restore_lore_logger_propagation() -> Iterator[None]:
    """Restore the lore-namespace loggers' handlers/level/propagate around every test.

    Finding #101: ``configure_logging()`` (loremaster/logging_setup.py) sets
    ``propagate = False`` on every :data:`LORE_NAMESPACES` logger — correct for
    production, where lore's structured stream must not double-emit through
    uvicorn's root handler. But pytest's ``caplog`` fixture captures via a
    handler it installs on the ROOT logger, reached ONLY by propagation. Any
    test that triggers ``configure_logging()`` (a server startup does) therefore
    silently blinds ``caplog`` for every LATER test in the same worker process —
    a state leak ACROSS test boundaries, not a single module's concern, so it is
    guarded here rather than in any one test file.
    ``test_logging_setup.py`` already carries the identical snapshot/restore for
    its own tests; this extends the same protection to every OTHER module so a
    caplog assertion is never at the mercy of test ORDER (see
    ``test_caplog_isolation.py``, finding #102's own root-cause pins depend on
    this).

    Production behaviour is unchanged: :func:`~loremaster.logging_setup.
    configure_logging` still disables propagation exactly as designed. This
    fixture only undoes that mutation between tests, the same way any other
    piece of leaked global state is reset here.
    """
    saved: dict[str, tuple[list[logging.Handler], int, bool]] = {}
    for name in LORE_NAMESPACES:
        logger = logging.getLogger(name)
        saved[name] = (list(logger.handlers), logger.level, logger.propagate)
    try:
        yield
    finally:
        for name, (handlers, level, propagate) in saved.items():
            logger = logging.getLogger(name)
            logger.handlers = list(handlers)
            logger.setLevel(level)
            logger.propagate = propagate


class _InertCalibrationTokenCounter:
    """A network-free stand-in for :class:`~loremaster.calibration.counting.
    AsyncClaudeTokenCounter` — the calibration engine's ONLY outbound seam.

    Constructed with the same ``(api_key, *, model=...)`` shape the engine's
    :meth:`~loremaster.calibration.engine.CalibrationEngine._default_counter_factory`
    uses, but it owns no ``httpx`` client and opens no socket. Its :meth:`count`
    raises :class:`~loremaster.calibration.counting.TerminalCountError`
    immediately — the SAME terminal outcome a real dummy-key probe reaches on a
    401. The engine's probe loop treats ``TerminalCountError`` as terminal: it
    flips to the ``cached`` serving state (keeping the committed constant), logs at
    ERROR, and returns — so the probe never touches the network, never retries,
    and never files a drift finding.

    Raising the terminal error (rather than returning baseline-matching counts) is
    the cleaner composition: it needs no per-file count table, drives NO drift/cache
    side effects, and mirrors the exact real-world dummy-key behaviour hermetically.
    """

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        # Absorb (and ignore) the real counter's ``(api_key, model=...)`` signature.
        pass

    async def count(self, text: str) -> int:
        """Raise the terminal-count error a real dummy-key probe would hit on a 401."""
        from loremaster.calibration.counting import TerminalCountError

        raise TerminalCountError("inert test counter: outbound token-count blocked")

    async def aclose(self) -> None:
        """No client to close — the inert counter never created one."""
        return None


@pytest.fixture
def _inert_calibration_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch the calibration engine's counter construction to a network-free double.

    OPT-IN (not autouse): only the modules that drive the PRODUCTION lifespan —
    which now calls ``AppContext.start_calibration_probe`` → ``engine.start()`` →
    the background probe — need it, and applying it globally would defeat
    ``test_calibration_counting.py``'s deliberate exercise of the REAL counter.

    The seam patched is the engine module's ``AsyncClaudeTokenCounter`` binding
    (what ``_default_counter_factory`` resolves), NOT the ``counting`` module's own
    binding — so ``test_calibration_counting.py`` (imports the real class from
    ``loremaster.calibration.counting``) and ``test_calibration_engine.py``
    (injects its own ``counter_factory``) are untouched. This closes the
    hermeticity regression where a lifespan-driven test fired a live
    ``count_tokens`` POST to ``api.anthropic.com`` with the dummy key.
    """
    import loremaster.calibration.engine as calibration_engine_module

    monkeypatch.setattr(
        calibration_engine_module,
        "AsyncClaudeTokenCounter",
        _InertCalibrationTokenCounter,
    )


# ===========================================================================
# THE RUNTIME SDK GUARD — AUTOUSE, SUITE-WIDE. (findings #108/#120)
#
# `_sdk_guard.install` wraps every public coroutine on the real SurrealDB connection
# classes and records any call a production frame makes without the retry driver above it.
#
# IT IS AUTOUSE BECAUSE COVERAGE BECAME THE NEW NAME-LIST. The v4 gate was a runtime gate
# — armed inside four tests. It therefore watched only what those four tests drove, and
# `scout.py::_drain_pending` was never among them: an unretried SELECT there scored
# 932 passed / 0 failed and shipped finding #120 ALIVE in the tree certified as having
# fixed it. A runtime gate is an invariant only over code it actually RUNS, and arming it
# by hand is a list of remembered flows wearing a different hat.
#
# Armed for EVERY test, it watches every production path any test drives — by nobody's
# memory. Inert (and loudly so) until the shared driver exists, so the un-repaired tree
# fails on the contract's own pins rather than on 800 confusing ones.
# ===========================================================================
@pytest.fixture(autouse=True)
def _no_sdk_call_escapes_the_retry_driver(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    from _sdk_guard import install

    report = install(monkeypatch)
    yield
    assert not report.escapes, (
        f"{len(report.escapes)} SurrealDB call(s) escaped the retry driver during this "
        f"test:\n  " + "\n  ".join(str(escape) for escape in report.escapes) + "\n\n"
        "Every call on a live connection must be an attempt the driver runs (hand it to "
        "retry_on_conflict, and CLASSIFY the conflict into the shared signal — routing "
        "alone retries zero times). Checked at RUNTIME on the real SDK class, so it cannot "
        "be evaded by aliasing, a helper module, `getattr`, a detached `gather`, or an SDK "
        "method nobody has listed."
    )
    assert not report.multi_statement_violations, (
        f"{len(report.multi_statement_violations)} bare .query() call(s) carried MORE THAN "
        f"ONE statement during this test:\n  "
        + "\n  ".join(str(violation) for violation in report.multi_statement_violations)
        + "\n\n"
        "The SDK's .query() validates statement[0] ONLY (store reference §3): a later "
        "statement can fail and roll the whole transaction back while .query() raises "
        "nothing (#124/#144). Multi-statement SurrealQL must ride execute_transaction "
        "(query_raw), never bare .query(). Checked at RUNTIME on the real SDK class (the "
        "#144 posture), replacing the per-module hand-list."
    )


# ===========================================================================
# #486 item 2 — THE TEST-DATABASE LIFECYCLE: every database a test opens was minted by
# ``_surreal_harness.unique_database()`` in THIS process, and none outlives the session.
#
# Quantified over the STATE, never over call sites: the engine creates a database on a bare
# ``use()`` (measured 2026-09-26, 3.2.4), so the door every test database a test SELECTS passes
# through is the connection's session selection — observed here on the real SDK class through
# the runtime guard's persistent hook chain, whoever made the call (a test, a harness fixture,
# production code a test drives). Provenance, not shape: a hand-forged
# ``test_<pid>_<hex32>`` fails exactly like a bare slug.
#
# BOUNDS, stated: the observer fires only while the per-test guard is armed, so a
# higher-scoped fixture's ``use()`` is unobserved (none mints a database today) — and since
# #534 the session-end reap dials the store only when a test OPENED a minted database, so such a
# fixture's database would also go unreaped in a session where no test opened one; a raw
# ``DEFINE DATABASE <name>`` creates a database with NO ``use()``, so it is not "one door" for
# creation, and this observer never sees such a database (no live test does this today); a
# namespace other than ``TEST_NAMESPACE`` is out of scope; a KILLED session never reaches the
# reap (operator ruling D2 — strays are removed by periodic operator wipes).
# ===========================================================================

# The ``workeroutput`` key an xdist worker's leak report crosses back to the controller under.
_LEAK_REPORT_WORKEROUTPUT_KEY = "lore_486_leaked_test_databases"

# The ``workeroutput`` key an xdist worker's FAILED session-end reap crosses back under (#534): a
# worker cannot change the controller's exit status, so a failure it only raised or logged would
# end the run rc 0 with the database unreaped — the xdist false clear contract-486-r3 found.
_UNREAPED_REPORT_WORKEROUTPUT_KEY = "lore_534_unreaped_test_databases"

# The session-end reap's whole wall-clock budget (#534). Explicit, so no reap ever relies on the
# SDK's or websockets' defaults to end (a muted store holds a request until websockets' keepalive,
# ~40s, closes the socket; the SDK's request await has no timeout of its own). Healthy reaps take
# well under a second; 30s covers the connect, the ``INFO``, the reader's drop and a dozen removals
# each spending the store retry seam's full per-operation conflict deadline.
_SESSION_END_REAP_BUDGET_SECONDS = 30.0

# A failed session-end reap's outcome: the TEST store could not be reached (a transport fault or the
# budget ran out) vs. it answered and the reap still failed (a wrong-shaped answer, contention).
_STORE_UNREACHABLE = "unreachable"
_REAP_FAILED = "failed"

# Every ``TEST_NAMESPACE`` database a ``use()`` selected during the current test, in call order.
_DATABASES_OPENED_THIS_TEST: list[str] = []

# Every ``TEST_NAMESPACE`` database a ``use()`` selected during this whole SESSION (#534): the
# session-end reap needs the store only if a test actually OPENED one of this process's mints — a
# session that minted names but opened nothing ends with pytest's own verdict, whatever the store.
_DATABASES_OPENED_THIS_SESSION: set[str] = set()

# ``(database, minting test)`` for every leak the session-end reap removed — this process's own
# (``-n 0``) or those xdist workers reported back to this controller.
_REAPED_LEAKS: list[tuple[str, str]] = []

# ``(outcome, cause, databases)`` for every session-end reap that FAILED (#534) — this process's own
# or those xdist workers reported back — ``databases`` being the minted ones this process opened and
# the reap could not verify were removed.
_UNREAPED_AT_SESSION_END: list[tuple[str, str, list[str]]] = []


def _record_database_selection(event: _sdk_guard.CallEvent, coro: Any) -> Any:
    """``_sdk_guard`` call hook: record the database each ``use()`` selects in the test namespace.

    Records and never raises: a raise here would surface inside whatever code made the call,
    and production code under test may legitimately wrap or swallow connection errors — the
    verdict is rendered at the test's teardown instead, where nothing can swallow it.
    """
    if event.method == "use":
        from _surreal_harness import TEST_NAMESPACE

        namespace = event.args[0] if event.args else event.kwargs.get("namespace")
        database = event.args[1] if len(event.args) > 1 else event.kwargs.get("database")
        if namespace == TEST_NAMESPACE and database is not None:
            _DATABASES_OPENED_THIS_TEST.append(str(database))
            _DATABASES_OPENED_THIS_SESSION.add(str(database))
    return coro


# Appended ONCE at import, never per test (``_governed_contract`` GOTCHA-B: a per-test append
# would re-arm behind a detach pin's ``_CALL_HOOKS.clear()``). Idempotent against a reload.
import _sdk_guard  # noqa: E402 - the sys.path wiring above must run first

if _record_database_selection not in _sdk_guard._CALL_HOOKS:
    _sdk_guard._CALL_HOOKS.append(_record_database_selection)


@pytest.fixture(autouse=True)
def _every_database_a_test_opens_was_minted_by_the_harness() -> Iterator[None]:
    """Fail a test that opened a test-namespace database its process did not mint.

    A database nothing in this process minted is one nothing in this process will reap if the
    test forgets to — the source of the 2186 ``test_<hex32>`` databases found in ``lore_test``
    (measured 2026-09-26, contract-486 M2).
    """
    from _surreal_harness import _MINTED_DATABASES

    _DATABASES_OPENED_THIS_TEST.clear()
    yield
    foreign = sorted({name for name in _DATABASES_OPENED_THIS_TEST if name not in _MINTED_DATABASES})
    _DATABASES_OPENED_THIS_TEST.clear()
    if foreign:
        pytest.fail(
            f"this test opened {len(foreign)} test database(s) NOT minted by "
            f"`_surreal_harness.unique_database()` in this process: {foreign}. Nothing will reap "
            f"such a database if the test forgets to; mint every test database (and every project "
            f"slug that becomes one) with `unique_database()`."
        )


def _reap_within_budget(budget_seconds: float) -> BaseException | None:
    """Run the harness's session-end reap with a hard wall-clock bound; return its failure, if any.

    The reap runs on its own event loop in a DAEMON thread that is abandoned when the budget runs
    out. A timeout inside the loop (``asyncio.timeout``) is not a bound: cancelling the reap runs its
    ``finally`` — closing the connection and dropping the reader database — and those awaits wait on
    the same silent store, uncancelled. A ``concurrent.futures`` worker is no better: the interpreter
    joins those at exit, so a hung reap would hang the process after pytest's verdict.

    Returns:
        ``None`` when the reap completed; the exception it raised; or a :class:`TimeoutError` naming
        the budget when it was still running at the deadline.
    """
    from _surreal_harness import reap_minted_databases

    failures: list[BaseException] = []

    def _reap() -> None:
        try:
            asyncio.run(reap_minted_databases())
        except BaseException as error:  # handed to the caller, which classifies and reports it
            failures.append(error)

    reaper = threading.Thread(target=_reap, name="lore-session-end-reap", daemon=True)
    reaper.start()
    reaper.join(budget_seconds)
    if reaper.is_alive():
        return TimeoutError(f"no answer within the {budget_seconds:g}s session-end reap budget")
    return failures[0] if failures else None


def _reap_failure_outcome(error: BaseException) -> str:
    """Classify a failed session-end reap through the store package's ONE transport classifier.

    "Unreachable" is exactly what the store's own SDK-await boundary calls a transport fault: a
    member of ``_SDK_AWAIT_BOUNDARY_ERRORS`` that is a request-routing ``KeyError`` (a socket dropped
    under an in-flight request) or that ``is_connection_error`` classifies as transport — which takes
    in the reap budget's own :class:`TimeoutError` (an ``OSError``). Anything else (a wrong-shaped
    ``INFO`` answer, contention past the seam's budget) is the store ANSWERING and the reap failing.
    """
    from loremaster.store._txn import _SDK_AWAIT_BOUNDARY_ERRORS, is_connection_error

    transport_fault = isinstance(error, _SDK_AWAIT_BOUNDARY_ERRORS) and (
        isinstance(error, KeyError) or is_connection_error(error)
    )
    return _STORE_UNREACHABLE if transport_fault else _REAP_FAILED


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Reap this process's leaked test databases at session end — LOUDLY, and in bounded time.

    The store is dialed only when a test OPENED one of this process's mints (#534): a session that
    minted names and opened nothing has nothing to reap, so it keeps pytest's own verdict whatever
    the state of the TEST store. A reap that fails — the store unreachable, or answering wrongly —
    never raises out of here: it is recorded with the opened databases it could not verify removed,
    named in one line by :func:`pytest_terminal_summary`, and fails the session.

    An xdist worker ships both reports to the controller (``workeroutput``), which merges them in
    :func:`pytest_testnodedown`; the process that owns the terminal records its own and fails the
    session. A reaped leak is still a test that skipped its teardown, so it is never silent.
    """
    from _surreal_harness import _MINTED_DATABASES

    failure = None
    if _DATABASES_OPENED_THIS_SESSION & _MINTED_DATABASES.keys():
        failure = _reap_within_budget(_SESSION_END_REAP_BUDGET_SECONDS)
    # One snapshot: an abandoned (timed-out) reap thread may still be marking entries.
    registry = dict(_MINTED_DATABASES)
    # Report from the registry, not from this last reap's return: a leak a mid-session reaper
    # call already removed is marked reaped there and must still be named (contract-486-r2 F2).
    report = sorted((database, minted_by) for database, (minted_by, reaped) in registry.items() if reaped)
    unreaped: list[tuple[str, str, list[str]]] = []
    if failure is not None:
        unverified = sorted(
            database
            for database in _DATABASES_OPENED_THIS_SESSION
            if database in registry and not registry[database][1]
        )
        unreaped.append((_reap_failure_outcome(failure), f"{type(failure).__name__}: {failure}", unverified))
    workeroutput = getattr(session.config, "workeroutput", None)
    if workeroutput is not None:
        workeroutput[_LEAK_REPORT_WORKEROUTPUT_KEY] = json.dumps(report)
        workeroutput[_UNREAPED_REPORT_WORKEROUTPUT_KEY] = json.dumps(unreaped)
        return
    _REAPED_LEAKS.extend(report)
    _UNREAPED_AT_SESSION_END.extend(unreaped)
    if (_REAPED_LEAKS or _UNREAPED_AT_SESSION_END) and session.exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node: Any, error: Any) -> None:
    """xdist controller: merge a finished worker's leak and failed-reap reports into this session's."""
    workeroutput = getattr(node, "workeroutput", {})
    serialized = workeroutput.get(_LEAK_REPORT_WORKEROUTPUT_KEY)
    if serialized:
        _REAPED_LEAKS.extend((database, test) for database, test in json.loads(serialized))
    serialized_unreaped = workeroutput.get(_UNREAPED_REPORT_WORKEROUTPUT_KEY)
    if serialized_unreaped:
        _UNREAPED_AT_SESSION_END.extend(
            (outcome, cause, list(databases)) for outcome, cause, databases in json.loads(serialized_unreaped)
        )


def _unreaped_line(outcome: str, records: list[tuple[str, str, list[str]]]) -> str:
    """The ONE line naming every database a failed session-end reap could not verify removed."""
    from _surreal_harness import surreal_url

    databases = sorted({database for _outcome, _cause, names in records for database in names})
    causes = "; ".join(sorted({cause for _outcome, cause, _names in records}))
    state = (
        f"TEST store {surreal_url()} {_STORE_UNREACHABLE} at session end"
        if outcome == _STORE_UNREACHABLE
        else f"session-end reap {_REAP_FAILED} against the TEST store {surreal_url()}"
    )
    return (
        f"{state} ({causes}) — could not verify that {len(databases)} test database(s) this session "
        f"opened were removed: {', '.join(databases) or 'none recorded'}. They may still be on the store; "
        f"the periodic test-namespace wipe removes them"
    )


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """Name every reaped leak and the test that minted it, and every reap that could not run."""
    for database, minted_by in _REAPED_LEAKS:
        terminalreporter.write_line(
            f"LEAKED test database {database} (minted by {minted_by or 'no test'}) — reaped at "
            f"session end; the test that minted it never dropped it"
        )
    for outcome in (_STORE_UNREACHABLE, _REAP_FAILED):
        records = [record for record in _UNREAPED_AT_SESSION_END if record[0] == outcome]
        if records:
            terminalreporter.write_line(_unreaped_line(outcome, records))
