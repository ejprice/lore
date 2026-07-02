"""Shared test configuration for the ``loresigil`` contract tests.

Two responsibilities:

* *Prove the offline guarantee*: ``VoyageTokenCounter`` must load the pinned,
  committed tokenizer from disk and never reach the network. We force Hugging
  Face's offline switches **at import time** (before ``tokenizers`` /
  ``transformers`` are imported anywhere) so that any accidental download
  attempt fails loudly instead of silently fetching a model. If the counter
  relied on a network fetch, the token-counter tests would error out under
  these flags rather than pass.
* Make sibling test-helper modules (e.g. ``_contextualized_fixtures``)
  importable as plain top-level modules — see the ``sys.path`` note below.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Set before tokenizers/transformers are imported by the modules under test.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# Make sibling test helper modules (e.g. ``_contextualized_fixtures``) importable
# as plain top-level modules under ``--import-mode=importlib``: that mode does
# NOT add each test file's directory to ``sys.path``, and ``loresigil`` is the
# *installed* package (with no ``tests`` subpackage), so neither a bare
# ``_contextualized_fixtures`` nor a ``loresigil.tests._contextualized_fixtures``
# import would otherwise resolve. Inserting this directory keeps shared fixture
# data in one reviewable module without polluting the shipped package. Mirrors
# the identical precedent in ``loremaster/tests/conftest.py``.
_TESTS_DIR = str(Path(__file__).parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)
