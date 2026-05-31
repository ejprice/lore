"""Shared test configuration for the ``loresigil`` contract tests.

The single responsibility of this module is to *prove the offline guarantee*:
``VoyageTokenCounter`` must load the pinned, committed tokenizer from disk and
never reach the network. We force Hugging Face's offline switches **at import
time** (before ``tokenizers`` / ``transformers`` are imported anywhere) so that
any accidental download attempt fails loudly instead of silently fetching a
model. If the counter relied on a network fetch, the token-counter tests would
error out under these flags rather than pass.
"""

from __future__ import annotations

import os

# Set before tokenizers/transformers are imported by the modules under test.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
