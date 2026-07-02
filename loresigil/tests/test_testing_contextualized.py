"""Contract tests for ``FakeEmbedder``'s contextualized (document-grouped) capability.

``FakeEmbedder`` ships in the wheel as the deterministic, offline stand-in for a
real embedder. In v0.4 it grows the optional contextualized seam so downstream
tests (loremaster's indexer, …) can exercise doc-grouped embedding without a
network. The pinned behaviours:

* ``supports_contextualized`` is ``True`` — the fake advertises the capability.
* ``embed_document_chunks(docs)`` returns one input-aligned
  :class:`~loresigil.base.EmbedResult` per doc, per-chunk vectors aligned 1:1.
* **Context sensitivity — the observable point of contextualization**: a chunk
  embedded INSIDE a doc gets a different vector than the same text embedded
  alone via ``embed_documents``, and a different vector again when its
  SURROUNDING doc differs. Downstream tests rely on this to prove the grouping
  actually happened (a fake that ignored the doc would certify a non-grouping
  pipeline as contextualized).
* Chunks remain individually distinguishable (no collapse to one doc vector).
* Determinism within and across instances; unit norm when ``normalized``.
* ``fail_inputs`` applies per chunk: a failing chunk is ``None`` at its slot,
  doc-siblings and sibling docs unaffected (same injectable-failure convention
  as ``embed_documents``).

Expected values come from the spec and independent math (``math.hypot``), never
from the implementation's hashing internals.
"""

from __future__ import annotations

import math

import pytest
from _contextualized_fixtures import DOC_POLICY, DOC_RUNBOOK, DOC_SINGLE
from loresigil.base import Embedder, EmbedResult
from loresigil.testing import FakeEmbedder

DEFAULT_DIM: int = 8
WIDE_DIM: int = 16

# DOC_RUNBOOK / DOC_POLICY / DOC_SINGLE (grouped chunks of one source document
# each) are shared with ``test_voyage_context.py`` via ``_contextualized_fixtures``
# — same fixture, exercised against two different backends.

# One chunk that appears inside two DIFFERENT documents — the fixture that makes
# context sensitivity observable.
SHARED_CHUNK: str = "Failover requires the standby replica to be within two seconds of lag."
DOC_CONTEXT_POSTGRES: list[str] = [
    SHARED_CHUNK,
    "This procedure applies to the primary Postgres cluster.",
]
DOC_CONTEXT_REDIS: list[str] = [
    SHARED_CHUNK,
    "This procedure applies to the Redis cache tier.",
]

# Independent unit-norm tolerance (math.hypot oracle, same as the flat-path suite).
NORM_TOLERANCE: float = 1e-9


class TestFakeEmbedderContextCapability:
    """The fake advertises and satisfies the contextualized seam."""

    def test_is_still_an_embedder(self) -> None:
        assert isinstance(FakeEmbedder(), Embedder)

    def test_supports_contextualized_is_true(self) -> None:
        embedder = FakeEmbedder()
        assert embedder.supports_contextualized is True

    async def test_returns_one_aligned_result_per_doc(self) -> None:
        embedder = FakeEmbedder()
        docs = [DOC_SINGLE, DOC_RUNBOOK, DOC_POLICY]  # varying sizes: 1, 3, 2
        results = await embedder.embed_document_chunks(docs)
        assert len(results) == len(docs)
        for result, chunks in zip(results, docs, strict=True):
            assert isinstance(result, EmbedResult)
            assert result.dim == embedder.dim
            assert len(result.vectors) == len(chunks)
            for vector in result.vectors:
                assert vector is not None
                assert len(vector) == embedder.dim

    async def test_empty_docs_list_returns_empty_list(self) -> None:
        embedder = FakeEmbedder()
        assert await embedder.embed_document_chunks([]) == []

    async def test_configured_dim_is_honored(self) -> None:
        embedder = FakeEmbedder(dim=WIDE_DIM)
        results = await embedder.embed_document_chunks([DOC_SINGLE])
        vector = results[0].vectors[0]
        assert vector is not None
        assert len(vector) == WIDE_DIM
        assert results[0].dim == WIDE_DIM


class TestFakeEmbedderContextDeterminism:
    """Same docs always map to the same vectors — within and across instances."""

    async def test_same_docs_same_vectors_within_instance(self) -> None:
        embedder = FakeEmbedder()
        first = await embedder.embed_document_chunks([DOC_RUNBOOK, DOC_POLICY])
        second = await embedder.embed_document_chunks([DOC_RUNBOOK, DOC_POLICY])
        assert [result.vectors for result in first] == [result.vectors for result in second]

    async def test_same_docs_same_vectors_across_instances(self) -> None:
        # Downstream tests compare vectors produced by separately-built fakes.
        first = await FakeEmbedder().embed_document_chunks([DOC_RUNBOOK])
        second = await FakeEmbedder().embed_document_chunks([DOC_RUNBOOK])
        assert [result.vectors for result in first] == [result.vectors for result in second]


class TestFakeEmbedderContextSensitivity:
    """The surrounding document observably changes a chunk's vector."""

    async def test_chunk_in_doc_differs_from_chunk_embedded_alone(self) -> None:
        embedder = FakeEmbedder()
        in_doc = (await embedder.embed_document_chunks([DOC_CONTEXT_POSTGRES]))[0].vectors[0]
        alone = (await embedder.embed_documents([SHARED_CHUNK])).vectors[0]
        # THE observable point of contextualization: if these were equal, a
        # downstream test could never prove the grouping happened.
        assert in_doc != alone

    async def test_same_chunk_in_different_docs_gets_different_vectors(self) -> None:
        embedder = FakeEmbedder()
        in_postgres = (await embedder.embed_document_chunks([DOC_CONTEXT_POSTGRES]))[0].vectors[0]
        in_redis = (await embedder.embed_document_chunks([DOC_CONTEXT_REDIS]))[0].vectors[0]
        # Identical chunk text, different surrounding document -> different vector.
        assert in_postgres != in_redis

    async def test_chunks_within_a_doc_remain_distinguishable(self) -> None:
        embedder = FakeEmbedder()
        result = (await embedder.embed_document_chunks([DOC_POLICY]))[0]
        # Guards against collapsing every chunk to one whole-doc vector —
        # per-chunk retrieval semantics must survive contextualization.
        assert result.vectors[0] != result.vectors[1]


class TestFakeEmbedderContextNorm:
    """Contextualized vectors honor the ``normalized`` contract."""

    async def test_vectors_are_unit_norm_when_normalized(self) -> None:
        embedder = FakeEmbedder()
        results = await embedder.embed_document_chunks([DOC_RUNBOOK])
        for vector in results[0].vectors:
            assert vector is not None
            # Independent norm oracle via math.hypot — not the impl's formula.
            assert math.hypot(*vector) == pytest.approx(1.0, abs=NORM_TOLERANCE)


class TestFakeEmbedderContextInjectedFailures:
    """``fail_inputs`` chunks come back ``None`` at their slot; siblings survive."""

    async def test_failing_chunk_is_none_at_its_slot(self) -> None:
        embedder = FakeEmbedder(fail_inputs={DOC_POLICY[1]})
        results = await embedder.embed_document_chunks([DOC_POLICY, DOC_SINGLE])
        assert results[0].vectors[1] is None

    async def test_doc_siblings_and_sibling_docs_are_unaffected(self) -> None:
        embedder = FakeEmbedder(fail_inputs={DOC_POLICY[1]})
        results = await embedder.embed_document_chunks([DOC_POLICY, DOC_SINGLE])
        # Same-doc sibling keeps a real vector at its own slot…
        assert results[0].vectors[0] is not None
        # …and the sibling DOC is entirely unaffected by the failure next door.
        assert results[1].vectors[0] is not None
