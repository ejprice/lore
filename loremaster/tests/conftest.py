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
