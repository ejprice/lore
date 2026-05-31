"""Contract tests for ``lorescribe.base.Chunker`` (the ABC).

The base class defines the two-method protocol every concrete chunker must
satisfy: ``handles(path)`` (does this chunker claim this file?) and
``chunk(source, ctx)`` (split it into chunks). The contract pinned here:

* ``Chunker`` is genuinely abstract — instantiating it directly is an error,
  and a subclass that forgets to implement an abstract method also cannot be
  instantiated. This prevents half-finished chunkers from registering.

* A *complete* subclass instantiates and its ``chunk`` receives a real
  ``ChunkContext`` whose injected ``count_tokens`` is callable — proving the
  framework wires the embedder's token counter through to chunkers.
"""

from __future__ import annotations

import pytest
from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext

from .conftest import (
    SAMPLE_FILE_PATH,
    SAMPLE_SLUG,
    VOYAGE4_MAX_INPUT_TOKENS,
    approx_token_count,
)

SAMPLE_SOURCE_TEXT: str = (
    "# Payroll\n\nDirect deposit posts on the second business day after "
    "the pay-period close."
)


class _CompleteChunker(Chunker):
    """A minimal but COMPLETE concrete chunker for protocol tests.

    It exercises the real seam: ``chunk`` calls the injected ``count_tokens``
    and stamps a non-empty identity, exactly as a production chunker must.
    """

    def handles(self, path: str) -> bool:
        return path.endswith(".md")

    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        # Use the injected token counter — the whole point of ChunkContext.
        token_count = ctx.count_tokens(source)
        return [
            Chunk(
                chunk_type="markdown_section",
                source_text=source,
                identity="payroll",
                line_start=1,
                line_end=source.count("\n") + 1,
                metadata={"token_count": token_count, "slug": ctx.slug},
            )
        ]


class _IncompleteChunker(Chunker):
    """A subclass that implements ``handles`` but NOT ``chunk`` — must not instantiate."""

    def handles(self, path: str) -> bool:  # pragma: no cover - never instantiated
        return True


class TestChunkerIsAbstract:
    """The base ``Chunker`` cannot be instantiated; incomplete subclasses can't either."""

    def test_base_chunker_cannot_be_instantiated(self) -> None:
        # Act / Assert: ABC with abstract methods -> TypeError on construction.
        with pytest.raises(TypeError):
            Chunker()  # type: ignore[abstract]

    def test_subclass_missing_chunk_method_cannot_be_instantiated(self) -> None:
        # Act / Assert: still abstract because ``chunk`` is unimplemented.
        with pytest.raises(TypeError):
            _IncompleteChunker()  # type: ignore[abstract]


class TestConcreteChunkerProtocol:
    """A complete subclass satisfies the protocol and uses the injected counter."""

    def setup_method(self) -> None:
        self.chunker = _CompleteChunker()
        self.ctx = ChunkContext(
            slug=SAMPLE_SLUG,
            file_path=SAMPLE_FILE_PATH,
            count_tokens=approx_token_count,
            max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
        )

    def test_complete_subclass_instantiates(self) -> None:
        assert isinstance(self.chunker, Chunker)

    def test_handles_returns_bool(self) -> None:
        # Contract: handles -> bool. Pin both branches.
        assert self.chunker.handles("docs/payroll.md") is True
        assert self.chunker.handles("docs/payroll.txt") is False

    def test_chunk_returns_list_of_chunks(self) -> None:
        # Act
        result = self.chunker.chunk(SAMPLE_SOURCE_TEXT, self.ctx)
        # Assert: shape contract.
        assert isinstance(result, list)
        assert all(isinstance(item, Chunk) for item in result)
        assert len(result) >= 1

    def test_chunk_invokes_injected_token_counter(self) -> None:
        # Act
        result = self.chunker.chunk(SAMPLE_SOURCE_TEXT, self.ctx)
        # Assert: the chunk carries the count produced by the SAME injected
        # counter — proves the ctx.count_tokens seam is actually traversed,
        # not bypassed. Independent expected value from the conftest counter.
        assert result[0].metadata["token_count"] == approx_token_count(SAMPLE_SOURCE_TEXT)

    def test_chunk_propagates_context_slug(self) -> None:
        # The ctx flows through to the emitted chunk's metadata.
        result = self.chunker.chunk(SAMPLE_SOURCE_TEXT, self.ctx)
        assert result[0].metadata["slug"] == SAMPLE_SLUG
