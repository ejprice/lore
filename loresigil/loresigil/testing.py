"""Shipped, deterministic test double for :class:`~loresigil.base.Embedder`.

:class:`FakeEmbedder` is **production code** — it ships in the loresigil wheel so
that downstream packages (``loremaster``, and loresigil's own tests) can exercise
embedding-dependent logic without network access, API keys, or non-determinism.

It satisfies the full :class:`~loresigil.base.Embedder` contract:

* Vectors are derived deterministically from a stable hash of the input text, so
  the same text always yields the same vector — within a process and across
  separately-constructed instances.
* When ``normalized`` is set (the default) every vector is L2-normalized to unit
  length, matching a real normalized embedder so cosine similarity equals the dot
  product downstream.
* Failure is injectable: any text in ``fail_inputs`` comes back as ``None`` at its
  position in :meth:`embed_documents`, simulating a permanently-failed input; and
  ``probe_fails`` makes :meth:`probe` raise, simulating an unreachable endpoint.
* Token counting uses a cheap, dependency-light ``len // 4`` heuristic by default
  (so the double stays fast and import-light); pass ``use_exact_tokenizer=True`` to
  delegate to the exact :class:`~loresigil.tokens.VoyageTokenCounter`.
"""

from __future__ import annotations

import hashlib
import math
import struct
from collections.abc import Set

from loresigil.base import Embedder, EmbedResult
from loresigil.tokens import VoyageTokenCounter

# Default model parameters mirror the small-model shape used across the project.
_DEFAULT_DIM: int = 8
_DEFAULT_MAX_INPUT_TOKENS: int = 8192
_DEFAULT_NAME: str = "fake-embedder"

# Approximate characters-per-token for the cheap heuristic token counter. A
# faithful behavioural stand-in for a BPE tokenizer on prose (~4 chars/token).
_CHARS_PER_TOKEN: int = 4

# Number of bytes consumed from the hash digest per vector component (float64).
_BYTES_PER_COMPONENT: int = 8


class FakeEmbedder(Embedder):
    """Deterministic, offline :class:`Embedder` for tests and downstream fixtures."""

    def __init__(
        self,
        dim: int = _DEFAULT_DIM,
        max_input_tokens: int = _DEFAULT_MAX_INPUT_TOKENS,
        normalized: bool = True,
        fail_inputs: Set[str] | None = None,
        probe_fails: bool = False,
        name: str = _DEFAULT_NAME,
        use_exact_tokenizer: bool = False,
    ) -> None:
        """Configure the fake embedder.

        Args:
            dim: Dimensionality of the produced vectors.
            max_input_tokens: Reported hard per-input token cap.
            normalized: Whether produced vectors are L2-normalized to unit length.
            fail_inputs: Texts that should come back as ``None`` (permanent
                failure) from :meth:`embed_documents`.
            probe_fails: When ``True``, :meth:`probe` raises to simulate an
                unreachable endpoint.
            name: Reported model name.
            use_exact_tokenizer: When ``True``, :meth:`count_tokens` delegates to
                the exact :class:`VoyageTokenCounter`; otherwise a ``len // 4``
                heuristic is used.
        """
        self._dim = dim
        self._max_input_tokens = max_input_tokens
        self._normalized = normalized
        self._fail_inputs: frozenset[str] = frozenset(fail_inputs or ())
        self._probe_fails = probe_fails
        self._name = name
        self._token_counter: VoyageTokenCounter | None = (
            VoyageTokenCounter() if use_exact_tokenizer else None
        )

    @property
    def name(self) -> str:
        """Reported model name."""
        return self._name

    @property
    def dim(self) -> int:
        """Dimensionality of the produced vectors."""
        return self._dim

    @property
    def max_input_tokens(self) -> int:
        """Reported hard per-input token cap."""
        return self._max_input_tokens

    @property
    def normalized(self) -> bool:
        """Whether produced vectors are L2-normalized to unit length."""
        return self._normalized

    def _vector_for(self, text: str) -> list[float]:
        """Derive a deterministic vector from a stable hash of ``text``.

        A SHA-256-based digest is expanded to ``dim`` float components (so the
        result is identical across processes and instances), then L2-normalized
        to unit length when ``normalized`` is set.

        Args:
            text: The input to embed.

        Returns:
            The deterministic embedding vector for ``text``.
        """
        # Expand the digest deterministically until we have enough bytes for all
        # components (dim * 8 bytes), then unpack to signed float64-friendly ints.
        needed = self._dim * _BYTES_PER_COMPONENT
        digest = b""
        counter = 0
        while len(digest) < needed:
            block = f"{text}\x00{counter}".encode()
            digest += hashlib.sha256(block).digest()
            counter += 1

        components: list[float] = []
        for index in range(self._dim):
            start = index * _BYTES_PER_COMPONENT
            chunk = digest[start : start + _BYTES_PER_COMPONENT]
            # Map 8 bytes -> an unsigned int -> a float centered around zero so
            # vectors point in varied directions rather than all-positive.
            raw = struct.unpack(">Q", chunk)[0]
            components.append(float(raw) - float(1 << 63))

        if self._normalized:
            norm = math.hypot(*components)
            if norm == 0.0:
                # Degenerate (astronomically unlikely): emit a canonical unit axis.
                components = [1.0] + [0.0] * (self._dim - 1)
            else:
                components = [value / norm for value in components]
        return components

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        """Embed a batch, returning a result positionally aligned with ``texts``."""
        vectors: list[list[float] | None] = [
            None if text in self._fail_inputs else self._vector_for(text) for text in texts
        ]
        return EmbedResult(vectors=vectors, dim=self._dim)

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string into one deterministic vector."""
        return self._vector_for(text)

    async def probe(self) -> int:
        """Return ``dim`` normally, or raise when configured to fail.

        Raises:
            ConnectionError: When ``probe_fails`` was set, simulating an
                unreachable embedding endpoint.
        """
        if self._probe_fails:
            raise ConnectionError("FakeEmbedder configured with probe_fails=True")
        return self._dim

    def count_tokens(self, texts: list[str]) -> list[int]:
        """Return an input-aligned list of token counts.

        Uses the exact :class:`VoyageTokenCounter` when configured, otherwise a
        ``len // 4`` heuristic (non-empty inputs report at least one token).
        """
        if self._token_counter is not None:
            return self._token_counter.count_tokens(texts)
        return [self._heuristic_count(text) for text in texts]

    @staticmethod
    def _heuristic_count(text: str) -> int:
        """Cheap ``len // 4`` token estimate; non-empty text yields at least one."""
        if not text:
            return 0
        return max(1, len(text) // _CHARS_PER_TOKEN)
