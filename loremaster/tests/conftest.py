"""Shared pytest fixtures for the loremaster test suite.

Currently limited to import-path wiring for sibling test helper modules (see
below). Qdrant was retired from the boot path AND its real-server test harness
at P8a (the store tests now run against the real local SurrealDB dev server via
``_surreal_harness.py``, not a real Qdrant collection).
"""

from __future__ import annotations

import sys
from pathlib import Path

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
