"""Shared pytest fixtures for the loremaster test suite.

Currently limited to import-path wiring for sibling test helper modules (see
below). Qdrant was retired from the boot path AND its real-server test harness
at P8a (the store tests now run against the real local SurrealDB dev server via
``_surreal_harness.py``, not a real Qdrant collection).
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
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
