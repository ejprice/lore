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

The contextualized (document-grouped) seam added in v0.4 is OPTIONAL:
``supports_contextualized`` and :meth:`Embedder.embed_document_chunks` are
non-abstract defaults, so a subclass implementing only the eight pre-existing
abstract members remains a complete, instantiable embedder.

The token-usage / cost-telemetry seam added in the v0.4 follow-up cycle is
also OPTIONAL: :class:`EmbedUsage` and :attr:`EmbedResult.usage` (default
``None``) let a backend surface provider-billed token counts without
breaking any existing constructor call.

The overlapping-window seam (2026-07-02, ``VoyageContextEmbedder``) is
likewise OPTIONAL: :attr:`EmbedResult.windowed` (default ``False``) lets a
contextualized backend mark a result whose chunks were embedded across
multiple overlapping sub-window requests (an over-budget document split
for the provider's per-document context window) rather than one single
request — so a downstream renderer can surface "(windowed context)"
provenance instead of silently presenting partial context as whole-file
context. Every other backend/result keeps the default ``False`` unchanged.

The asynchronous Batch API seam (2026-07-03) is likewise OPTIONAL:
:attr:`Embedder.supports_batch` (default ``False``, mirroring
:attr:`supports_contextualized`) lets a backend advertise that it also
implements batch submission/polling/fetch methods (see
:mod:`loresigil.voyage_batch`) without those methods being part of the core
abstract contract every embedder must satisfy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, Field


class EmbedUsage(BaseModel):
    """Provider-billed token count for one embedding call.

    A sub-model rather than a bare ``total_tokens: int | None`` field on
    :class:`EmbedResult` because (a) it mirrors the wire's own ``usage``
    object so future provider fields (e.g. a cost breakdown) extend this
    model without another :class:`EmbedResult` migration, (b) validation
    (non-negative, strict) lives on the value object itself, and (c)
    ``usage: EmbedUsage | None`` reads unambiguously as "telemetry absent",
    where a bare ``None`` int could be misread as zero.

    Attributes:
        total_tokens: The provider-reported token count billed for the call
            (or portion of it) this result represents. Never negative.
    """

    model_config = ConfigDict(extra="forbid")

    total_tokens: int = Field(ge=0)


class EmbedResult(BaseModel):
    """Input-aligned envelope of embedding vectors returned by an embedder.

    Attributes:
        vectors: One entry per input text, in the same order. Each entry is the
            embedding vector for that input, or ``None`` when the backend
            permanently failed to embed it.
        dim: Dimensionality of the (non-``None``) vectors in this result.
        usage: Provider-billed token usage for the call that produced this
            result, or ``None`` when the backend does not report usage at
            all. ``None`` is distinct from ``EmbedUsage(total_tokens=0)``: a
            reporting backend that billed nothing says the latter.
        windowed: ``True`` when this result's chunks were produced by
            splitting an over-budget document into overlapping sub-window
            requests rather than one single request (see
            :class:`~loresigil.voyage_context.VoyageContextEmbedder`).
            Defaults to ``False`` — the byte-identical, non-windowed
            behaviour every other call site already expects.
    """

    model_config = ConfigDict(extra="forbid")

    vectors: list[list[float] | None]
    dim: int
    usage: EmbedUsage | None = None
    windowed: bool = False


class Embedder(ABC):
    """Abstract base class for all concrete embedders.

    Concrete subclasses expose four read-only properties describing the model
    (``name``, ``dim``, ``max_input_tokens``, ``normalized``) and implement the
    four behavioural methods below. Because those eight members are abstract,
    neither this class nor an incomplete subclass can be instantiated.

    The contextualized seam (``supports_contextualized`` /
    :meth:`embed_document_chunks`) is a non-abstract default — backends opt in
    by overriding both; everyone else keeps working unchanged.
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

    @property
    def supports_contextualized(self) -> bool:
        """Whether this embedder implements contextualized (document-grouped) embedding.

        ``False`` by default. A backend that implements
        :meth:`embed_document_chunks` overrides this to ``True`` so callers can
        feature-detect the capability before calling. Declared by the class,
        never toggled per instance (read-only property, no setter).
        """
        return False

    @property
    def supports_batch(self) -> bool:
        """Whether this embedder implements the asynchronous Batch API.

        ``False`` by default. A backend that implements the batch-submission
        methods (``submit_batch_documents``/``submit_batch_document_chunks``,
        ``fetch_batch_results``, ``get_batch_status``, ``await_batch_completion``)
        overrides this to ``True`` so callers can feature-detect the capability
        before calling. Declared by the class, never toggled per instance
        (read-only property, no setter) — mirrors :attr:`supports_contextualized`.
        """
        return False

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        """Embed a batch of documents.

        Args:
            texts: The documents to embed.

        Returns:
            An :class:`EmbedResult` whose ``vectors`` are positionally aligned
            with ``texts`` (``None`` for any permanently-failed input).
        """

    async def embed_document_chunks(self, docs: list[list[str]]) -> list[EmbedResult]:
        """Embed each document's grouped chunks with document-level context.

        Args:
            docs: One entry per document, each the ordered chunk texts of that
                document.

        Returns:
            One :class:`EmbedResult` per document, its ``vectors`` aligned 1:1
            with that document's chunks (``None`` marks a permanently-failed
            chunk — the same convention as :meth:`embed_documents`).

        Raises:
            NotImplementedError: Default for backends without the capability —
                check ``supports_contextualized`` before calling.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not implement contextualized embedding; "
            f"check supports_contextualized before calling embed_document_chunks"
        )

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
