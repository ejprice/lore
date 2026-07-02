"""Contract tests for the OPTIONAL contextualized-embedding seam on ``Embedder``.

New capability on :class:`loresigil.base.Embedder` (v0.4, P1):

* ``supports_contextualized`` — a **read-only property**, default ``False``, and
  **non-abstract**: every pre-existing concrete embedder (TEI, voyage-cloud, the
  shipped fake before it opts in) keeps instantiating with ZERO changes. A
  subclass that implements only the eight pre-existing abstract members is still
  a complete, instantiable embedder.
* ``async def embed_document_chunks(self, docs: list[list[str]]) -> list[EmbedResult]``
  — non-abstract default that raises :class:`NotImplementedError` with a teaching
  message naming ``supports_contextualized``, so a caller that forgot to
  feature-detect learns exactly which flag to check. ``docs`` is a list of
  documents, each a list of chunk texts; a capable backend returns one
  :class:`~loresigil.base.EmbedResult` per document, its ``vectors`` aligned 1:1
  with that document's chunks (``None`` marks a permanently-failed chunk — the
  exact convention ``embed_documents`` already uses).

The behavioural expectations come from the v0.4 feature spec, not from any
implementation — the implementation does not exist when this file is written.
The pre-existing abstractness contract (base class and incomplete subclasses
cannot instantiate) stays pinned in ``test_base.py`` and must keep holding.
"""

from __future__ import annotations

import pytest
from _contextualized_fixtures import DOC_RUNBOOK
from loresigil.base import Embedder, EmbedResult

# Small-model shape for the legacy stand-in; the value itself is not
# load-bearing arithmetic, just a plausible non-toy dimension.
LEGACY_DIM: int = 8
LEGACY_MAX_INPUT_TOKENS: int = 8192

# Heuristic used only by the stand-in's count_tokens (mirrors the shipped
# fake's ~4 chars/token prose heuristic).
_CHARS_PER_TOKEN: int = 4


class _LegacyCompleteEmbedder(Embedder):
    """Implements EXACTLY the eight pre-existing abstract members and nothing else.

    This class is the back-compat probe: it must remain instantiable after the
    new members land, proving both new members are non-abstract defaults. Its
    embedding outputs are never asserted as embeddings — only the NEW default
    members are under test here.
    """

    @property
    def name(self) -> str:
        return "legacy-complete"

    @property
    def dim(self) -> int:
        return LEGACY_DIM

    @property
    def max_input_tokens(self) -> int:
        return LEGACY_MAX_INPUT_TOKENS

    @property
    def normalized(self) -> bool:
        return True

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        return EmbedResult(vectors=[[0.0] * LEGACY_DIM for _ in texts], dim=LEGACY_DIM)

    async def embed_query(self, text: str) -> list[float]:
        return [0.0] * LEGACY_DIM

    async def probe(self) -> int:
        return LEGACY_DIM

    def count_tokens(self, texts: list[str]) -> list[int]:
        return [max(1, len(text) // _CHARS_PER_TOKEN) if text else 0 for text in texts]


class TestContextualizedSeamIsOptional:
    """The new members are non-abstract defaults — existing embedders are untouched."""

    def test_subclass_without_new_members_still_instantiates(self) -> None:
        # THE back-compat pin: a subclass written before v0.4 (eight members,
        # nothing contextualized) must not become abstract when the seam lands.
        embedder = _LegacyCompleteEmbedder()
        assert isinstance(embedder, Embedder)

    def test_supports_contextualized_defaults_to_false(self) -> None:
        embedder = _LegacyCompleteEmbedder()
        # ``is False`` (not falsy): the flag is a bool the factory/indexer
        # branches on, so a None/0 lookalike must not pass.
        assert embedder.supports_contextualized is False

    def test_supports_contextualized_is_read_only(self) -> None:
        embedder = _LegacyCompleteEmbedder()
        # The capability is declared by the CLASS, not toggled per instance —
        # a property without a setter rejects assignment.
        with pytest.raises(AttributeError):
            # ignore[misc]: assignment to a read-only property. Pre-STUB,
            # mypy reports attr-defined + unused-ignore here instead — both
            # resolve once the property exists.
            embedder.supports_contextualized = True  # type: ignore[misc]


class TestDefaultEmbedDocumentChunksTeaches:
    """The default ``embed_document_chunks`` fails loud with a teaching message."""

    async def test_raises_not_implemented_error_by_default(self) -> None:
        embedder = _LegacyCompleteEmbedder()
        # NotImplementedError specifically — not TypeError (which would mean
        # the method was made abstract and broke instantiation) and not
        # AttributeError (which would mean the seam is missing entirely).
        with pytest.raises(NotImplementedError):
            await embedder.embed_document_chunks([DOC_RUNBOOK])

    async def test_error_message_names_the_capability_flag(self) -> None:
        embedder = _LegacyCompleteEmbedder()
        with pytest.raises(NotImplementedError) as exc_info:
            await embedder.embed_document_chunks([DOC_RUNBOOK])
        # The message must teach feature-detection: a caller who hits this
        # learns the exact flag to check before calling.
        assert "supports_contextualized" in str(exc_info.value)
