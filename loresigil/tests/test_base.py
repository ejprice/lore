"""Contract tests for ``loresigil.base`` — the embedder abstraction.

This module pins two public surfaces:

* ``EmbedResult`` — the pydantic v2 envelope an :class:`Embedder` returns from
  ``embed_documents``. Its ``vectors`` list is *aligned to the input texts*:
  a ``None`` element marks an input that the backend *permanently* failed to
  embed (as opposed to a transient error the caller would retry). It forbids
  extra fields so a typo'd kwarg surfaces as a ``ValidationError`` rather than
  being silently swallowed.

* ``Embedder`` — the abstract base every concrete embedder (Voyage, the test
  double, …) must satisfy. It is genuinely abstract: instantiating it, or a
  subclass that forgets a method, is a ``TypeError``. This prevents a
  half-finished embedder from being wired into the pipeline.

The behavioural expectations here come from the feature spec, not from any
implementation — the implementation does not exist when this file is written.
"""

from __future__ import annotations

import pytest
from loresigil.base import Embedder, EmbedResult
from pydantic import ValidationError

# A vector dimensionality typical of a small embedding model. Used purely as a
# realistic shape for EmbedResult fixtures; the value is not load-bearing
# arithmetic, just a plausible non-toy dimension.
SAMPLE_DIM: int = 8


class TestEmbedResultShape:
    """``EmbedResult`` carries an input-aligned vector list and a dimension."""

    def test_holds_vectors_and_dim(self) -> None:
        # Arrange: two successfully embedded inputs.
        vectors: list[list[float] | None] = [[0.0] * SAMPLE_DIM, [1.0] * SAMPLE_DIM]
        # Act
        result = EmbedResult(vectors=vectors, dim=SAMPLE_DIM)
        # Assert
        assert result.dim == SAMPLE_DIM
        assert result.vectors == vectors
        assert len(result.vectors) == 2

    def test_vectors_may_contain_none_for_permanent_failure(self) -> None:
        # A None element marks a permanently-failed input. It must construct
        # cleanly and preserve the None at its index (alignment is the contract).
        vectors: list[list[float] | None] = [[0.5] * SAMPLE_DIM, None, [0.25] * SAMPLE_DIM]
        result = EmbedResult(vectors=vectors, dim=SAMPLE_DIM)
        assert result.vectors[1] is None
        assert result.vectors[0] is not None
        assert result.vectors[2] is not None

    def test_empty_vectors_is_valid(self) -> None:
        # Embedding an empty batch yields an empty (but valid) result.
        result = EmbedResult(vectors=[], dim=SAMPLE_DIM)
        assert result.vectors == []
        assert result.dim == SAMPLE_DIM


class TestEmbedResultRejectsGarbage:
    """``EmbedResult`` is strict: extra fields and missing fields are errors."""

    def test_rejects_extra_fields(self) -> None:
        # extra="forbid": a typo'd / unexpected kwarg must raise, not be ignored.
        with pytest.raises(ValidationError):
            EmbedResult(  # type: ignore[call-arg]
                vectors=[[0.0] * SAMPLE_DIM],
                dim=SAMPLE_DIM,
                unexpected_field="boom",
            )

    def test_requires_dim(self) -> None:
        # dim is mandatory — a result without a declared dimension is meaningless.
        with pytest.raises(ValidationError):
            EmbedResult(vectors=[])  # type: ignore[call-arg]


class _IncompleteEmbedder(Embedder):
    """Implements the attribute properties but NOT the methods — must stay abstract.

    It deliberately omits ``embed_documents``, ``embed_query``, ``probe`` and
    ``count_tokens`` so that attempting to instantiate it proves the method
    contract is enforced by ``ABCMeta``, not merely documented.
    """

    @property
    def name(self) -> str:  # pragma: no cover - never instantiated
        return "incomplete"

    @property
    def dim(self) -> int:  # pragma: no cover - never instantiated
        return SAMPLE_DIM

    @property
    def max_input_tokens(self) -> int:  # pragma: no cover - never instantiated
        return 8192

    @property
    def normalized(self) -> bool:  # pragma: no cover - never instantiated
        return True


class TestEmbedderIsAbstract:
    """The base ``Embedder`` and any incomplete subclass cannot be instantiated."""

    def test_base_embedder_cannot_be_instantiated(self) -> None:
        # ABC with abstract members -> TypeError on direct construction.
        with pytest.raises(TypeError):
            Embedder()  # type: ignore[abstract]

    def test_subclass_missing_methods_cannot_be_instantiated(self) -> None:
        # Still abstract because the four abstract methods are unimplemented.
        with pytest.raises(TypeError):
            _IncompleteEmbedder()  # type: ignore[abstract]
