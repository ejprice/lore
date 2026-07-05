"""Shared pytest fixtures for the loremaster test suite.

Currently limited to import-path wiring for sibling test helper modules (see
below). Qdrant was retired from the boot path AND its real-server test harness
at P8a (the store tests now run against the real local SurrealDB dev server via
``_surreal_harness.py``, not a real Qdrant collection).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

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
