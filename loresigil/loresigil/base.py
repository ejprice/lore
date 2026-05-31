"""Core abstractions for the loresigil embedding layer.

This module defines the two contracts every embedder in the lore project shares:

* :class:`EmbedResult` — the strict, input-aligned envelope returned from a
  batch document-embedding call. The ``vectors`` list is positionally aligned
  with the input texts; a ``None`` element marks an input the backend
  *permanently* failed to embed (distinct from a transient error a caller would
  retry). ``extra="forbid"`` ensures a mistyped field is a loud
  :class:`~pydantic.ValidationError` rather than silent data loss.

* :class:`Embedder` — the abstract base class every concrete embedder (the
  Voyage client, the shipped :class:`~loresigil.testing.FakeEmbedder`, …) must
  satisfy. It is genuinely abstract: ``ABCMeta`` blocks instantiation of the
  base class or of any subclass that has not implemented the full method
  contract, so a half-finished embedder can never be wired into a pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict


class EmbedResult(BaseModel):
    """Input-aligned envelope of embedding vectors returned by an embedder.

    Attributes:
        vectors: One entry per input text, in the same order. Each entry is the
            embedding vector for that input, or ``None`` when the backend
            permanently failed to embed it.
        dim: Dimensionality of the (non-``None``) vectors in this result.
    """

    model_config = ConfigDict(extra="forbid")

    vectors: list[list[float] | None]
    dim: int


class Embedder(ABC):
    """Abstract base class for all concrete embedders.

    Concrete subclasses expose four read-only properties describing the model
    (``name``, ``dim``, ``max_input_tokens``, ``normalized``) and implement the
    four behavioural methods below. Because every member is abstract, neither
    this class nor an incomplete subclass can be instantiated.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable, human-readable identifier for this embedder/model."""

    @property
    @abstractmethod
    def dim(self) -> int:
        """Dimensionality of the embedding vectors this embedder produces."""

    @property
    @abstractmethod
    def max_input_tokens(self) -> int:
        """Hard per-input token cap; inputs exceeding it are rejected, not truncated."""

    @property
    @abstractmethod
    def normalized(self) -> bool:
        """Whether returned vectors are L2-normalized to unit length."""

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        """Embed a batch of documents.

        Args:
            texts: The documents to embed.

        Returns:
            An :class:`EmbedResult` whose ``vectors`` are positionally aligned
            with ``texts`` (``None`` for any permanently-failed input).
        """

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string into one vector."""

    @abstractmethod
    async def probe(self) -> int:
        """Return the embedding dimension observed from the live endpoint.

        Returns:
            The observed embedding dimensionality.

        Raises:
            Exception: If the embedding endpoint is unreachable.
        """

    @abstractmethod
    def count_tokens(self, texts: list[str]) -> list[int]:
        """Return an input-aligned list of exact token counts for ``texts``."""
