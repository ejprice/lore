"""Shared fixtures for the lorescribe core-framework contract tests.

These fixtures are intentionally grounded in production-realistic values:

* ``VOYAGE4_MAX_INPUT_TOKENS`` mirrors the *hard*, rejection-not-truncation
  token cap of the voyage-4-nano TEI embedder (the embedder
  rejects over-length inputs with HTTP 422; it never silently truncates).
  A chunker that respects this number keeps every emitted chunk embeddable.
  Picking a "round" toy number like 100 here would let an off-by-scale bug
  (e.g. a chunker emitting 16k-token chunks) pass inertly, so the real cap
  is used.

* ``approx_token_count`` is the kind of token-counter the *consumer* injects
  into ``ChunkContext`` from the embedder side. The real counter calls the
  voyage-4 tokenizer; the ~4-chars-per-token heuristic here is a faithful
  *behavioural* stand-in (a genuine callable that returns plausible counts),
  not a value picked to make arithmetic clean.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

# Hard token cap of the voyage-4-nano TEI embedder: over-length inputs are
# REJECTED (HTTP 422), never truncated. This is the value the consumer passes
# as ``ChunkContext.max_input_tokens`` in production.
VOYAGE4_MAX_INPUT_TOKENS: int = 8192

# Realistic identifiers a project ("slug") and an on-disk source file carry as
# they flow from lorescribe into loremaster's deterministic point-ID derivation
# (slug, file_path, chunk_type, identity, sub_ordinal, key_version).
SAMPLE_SLUG: str = "firehawk-handbook"
SAMPLE_FILE_PATH: str = "docs/onboarding/payroll.md"


def approx_token_count(text: str) -> int:
    """Behavioural stand-in for the embedder's injected token counter.

    Roughly 4 characters per token — a faithful approximation of how a
    BPE/Qwen3 tokenizer behaves on prose, used purely so tests can assert a
    consumer *calls through* this callable. Not a clean-arithmetic convenience
    value; it reflects the real counter's contract: ``str -> int``.
    """
    return max(1, len(text) // 4)


@pytest.fixture
def count_tokens() -> Callable[[str], int]:
    """The token-counter callable a consumer injects into ``ChunkContext``."""
    return approx_token_count
