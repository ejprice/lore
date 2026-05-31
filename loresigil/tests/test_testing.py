"""Contract tests for ``loresigil.testing.FakeEmbedder`` — the shipped double.

``FakeEmbedder`` is *production* code (it ships in the wheel) used by downstream
``loremaster``/``loresigil`` tests as a deterministic, network-free stand-in for
a real Voyage embedder. The behaviours pinned here are the exact contract those
downstream tests rely on, so they are non-negotiable:

* **Determinism** — the same text always maps to the same vector, within one
  instance and across instances. Downstream tests assert on stored vectors.
* **Correct shape** — every vector has length ``dim``.
* **Unit norm** — when ``normalized`` is set (the default), ‖v‖ ≈ 1.0, matching
  a real normalized embedder so cosine == dot-product downstream.
* **Input-aligned results** — ``embed_documents`` returns an :class:`EmbedResult`
  whose ``vectors`` list lines up 1:1 with the input texts and whose ``dim``
  matches the configured dimension.
* **Injectable failure** — texts in the configured "fail" set come back as
  ``None`` at their matching index (permanent failure), while other indices
  still carry real vectors.
* **Probe failure switch** — ``probe()`` returns ``dim`` normally, and raises
  when the double is configured to simulate an unreachable endpoint.

Expected values are derived from the spec and from independent math
(``math.hypot`` for the norm), never from the implementation's internals.
"""

from __future__ import annotations

import math

import pytest
from loresigil.base import Embedder, EmbedResult
from loresigil.testing import FakeEmbedder

DEFAULT_DIM: int = 8
DEFAULT_MAX_INPUT_TOKENS: int = 8192

# Representative inputs — real-ish prose, not "foo"/"bar".
TEXT_A: str = "Direct deposit posts on the second business day after pay-period close."
TEXT_B: str = "Embeddings map text into a dense vector space for semantic search."
TEXT_C: str = "Quarterly safety training is mandatory for all warehouse staff."

# Tolerance for the unit-norm assertion. A normalized vector should be ~1.0 to
# well within float tolerance; this independent bound (math.hypot) is not taken
# from the implementation.
NORM_TOLERANCE: float = 1e-9


class TestFakeEmbedderIsAConcreteEmbedder:
    """``FakeEmbedder`` is a real, instantiable :class:`Embedder` with sane defaults."""

    def test_is_an_embedder_instance(self) -> None:
        embedder = FakeEmbedder()
        assert isinstance(embedder, Embedder)

    def test_default_attributes(self) -> None:
        embedder = FakeEmbedder()
        assert embedder.dim == DEFAULT_DIM
        assert embedder.max_input_tokens == DEFAULT_MAX_INPUT_TOKENS
        assert embedder.normalized is True
        assert isinstance(embedder.name, str) and embedder.name

    def test_dim_is_configurable(self) -> None:
        embedder = FakeEmbedder(dim=16)
        assert embedder.dim == 16


class TestFakeEmbedderQueryDeterminismAndShape:
    """``embed_query`` is deterministic, correctly shaped, and unit-norm."""

    async def test_same_text_same_vector_within_instance(self) -> None:
        embedder = FakeEmbedder()
        first = await embedder.embed_query(TEXT_A)
        second = await embedder.embed_query(TEXT_A)
        assert first == second

    async def test_same_text_same_vector_across_instances(self) -> None:
        # Determinism must survive re-construction — downstream tests compare
        # vectors produced by separately-built embedders.
        first = await FakeEmbedder().embed_query(TEXT_A)
        second = await FakeEmbedder().embed_query(TEXT_A)
        assert first == second

    async def test_different_text_different_vector(self) -> None:
        embedder = FakeEmbedder()
        vec_a = await embedder.embed_query(TEXT_A)
        vec_b = await embedder.embed_query(TEXT_B)
        # Hash-derived vectors for distinct inputs must not collide.
        assert vec_a != vec_b

    async def test_vector_has_configured_dim(self) -> None:
        embedder = FakeEmbedder(dim=16)
        vec = await embedder.embed_query(TEXT_A)
        assert len(vec) == 16

    async def test_vector_is_unit_norm_when_normalized(self) -> None:
        embedder = FakeEmbedder()
        vec = await embedder.embed_query(TEXT_A)
        # Independent norm via math.hypot — not the implementation's formula.
        norm = math.hypot(*vec)
        assert norm == pytest.approx(1.0, abs=NORM_TOLERANCE)


class TestFakeEmbedderDocuments:
    """``embed_documents`` returns an input-aligned :class:`EmbedResult`."""

    async def test_returns_embed_result_aligned_to_inputs(self) -> None:
        embedder = FakeEmbedder()
        texts = [TEXT_A, TEXT_B, TEXT_C]
        result = await embedder.embed_documents(texts)
        assert isinstance(result, EmbedResult)
        assert len(result.vectors) == len(texts)
        assert result.dim == embedder.dim

    async def test_each_document_vector_is_unit_norm(self) -> None:
        embedder = FakeEmbedder()
        result = await embedder.embed_documents([TEXT_A, TEXT_B])
        for vector in result.vectors:
            assert vector is not None
            assert math.hypot(*vector) == pytest.approx(1.0, abs=NORM_TOLERANCE)

    async def test_documents_match_query_for_same_text(self) -> None:
        # The document path and the query path must agree for identical input —
        # downstream code embeds queries and documents with the same model and
        # expects them in the same space.
        embedder = FakeEmbedder()
        result = await embedder.embed_documents([TEXT_A])
        query_vec = await embedder.embed_query(TEXT_A)
        assert result.vectors[0] == query_vec

    async def test_empty_batch_returns_empty_aligned_result(self) -> None:
        embedder = FakeEmbedder()
        result = await embedder.embed_documents([])
        assert result.vectors == []
        assert result.dim == embedder.dim


class TestFakeEmbedderInjectedFailures:
    """Configured "fail" inputs come back as ``None`` at the matching index."""

    async def test_failed_input_is_none_at_its_index(self) -> None:
        # TEXT_B is configured to permanently fail.
        embedder = FakeEmbedder(fail_inputs={TEXT_B})
        result = await embedder.embed_documents([TEXT_A, TEXT_B, TEXT_C])
        assert result.vectors[1] is None

    async def test_non_failed_inputs_still_have_vectors(self) -> None:
        embedder = FakeEmbedder(fail_inputs={TEXT_B})
        result = await embedder.embed_documents([TEXT_A, TEXT_B, TEXT_C])
        # Indices 0 and 2 are unaffected by the failure at index 1.
        assert result.vectors[0] is not None
        assert result.vectors[2] is not None
        assert len(result.vectors[0]) == embedder.dim

    async def test_no_failures_means_no_none(self) -> None:
        embedder = FakeEmbedder()
        result = await embedder.embed_documents([TEXT_A, TEXT_B, TEXT_C])
        assert all(vector is not None for vector in result.vectors)


class TestFakeEmbedderProbe:
    """``probe`` reports the dimension, or raises when set to simulate downtime."""

    async def test_probe_returns_dim_normally(self) -> None:
        embedder = FakeEmbedder(dim=16)
        assert await embedder.probe() == 16

    async def test_probe_raises_when_configured_unreachable(self) -> None:
        embedder = FakeEmbedder(probe_fails=True)
        with pytest.raises(Exception):
            await embedder.probe()


class TestFakeEmbedderTokenCounting:
    """``count_tokens`` returns a per-input, non-negative, input-aligned list."""

    def test_count_tokens_aligned_to_inputs(self) -> None:
        embedder = FakeEmbedder()
        texts = [TEXT_A, TEXT_B, TEXT_C]
        counts = embedder.count_tokens(texts)
        assert len(counts) == len(texts)
        assert all(isinstance(count, int) and count >= 0 for count in counts)

    def test_empty_string_counts_zero_or_more(self) -> None:
        embedder = FakeEmbedder()
        counts = embedder.count_tokens(["", TEXT_A])
        assert counts[0] >= 0
        # A non-empty realistic input has at least one token.
        assert counts[1] >= 1
