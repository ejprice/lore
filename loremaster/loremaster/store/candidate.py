"""The neutral search-result value object returned by :class:`SurrealStore`.

The unified SurrealDB store fuses two retrieval arms — an HNSW vector search and
a BM25 FULLTEXT search — with the engine's native ``search::rrf`` (Reciprocal
Rank Fusion). Whatever the arm, a hit is handed back as this single, backend-
neutral :class:`Candidate`: the loremaster callers depend on *these* four fields,
never on any raw vector-store point type (a ``ScoredPoint``-style object) or raw
``surrealdb`` type. Keeping
the return type neutral is what let the store swap Qdrant for SurrealDB without a
caller rewrite.

``extra="forbid"`` is load-bearing, not cosmetic: it guarantees no stray
backend attribute (a leaked ``ScoredPoint.version``, a raw ``RecordID``) can ride
along on a candidate and couple a caller back to a concrete engine.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

# The three retrieval arms a candidate can originate from. ``vector`` = HNSW
# nearest-neighbour only; ``fulltext`` = BM25 lexical only; ``fused`` = a
# ``search::rrf`` fusion of both. Pinned as a ``Literal`` so a typo or a leaked
# backend-ism (e.g. ``"backend_hit"``) fails validation loudly rather than coercing.
CandidateOrigin = Literal["vector", "fulltext", "fused"]


class Candidate(BaseModel):
    """One backend-neutral search hit — the store's only search return type.

    Attributes:
        key: The chunk's BARE ``uuid5`` point id (no ``chunk:`` record-table
            prefix), identical to what the indexer minted via
            :func:`loremaster.index.records.point_id`. This is the key the
            memory-ref / chunk-key conventions already use unchanged.
        score: The derived relevance/fusion score (the RRF score for a fused
            hit). Finite and non-negative.
        payload: The stored chunk fields (tier, file_path, source_text, …), never
            the vector itself.
        origin: Which retrieval arm produced the hit — see :data:`CandidateOrigin`.
        vector_cosine: The raw pre-fusion query<->chunk cosine similarity (the
            HNSW arm's own magnitude, projected server-side alongside the fused
            ``search::rrf`` row — see
            :meth:`~loremaster.store.surreal.SurrealStore.hybrid_search`), or
            ``None`` when a caller (a test double, an older store) never
            projects it. Unlike ``score`` (a rank-fusion CODE that cannot
            discriminate match quality — docs/design/2026-07-06-weak-match-
            discrimination.md §1.2), this is a genuine magnitude in
            ``[-1.0, 1.0]`` — the substrate the weak-match/absence-verdict
            machinery in ``search.py`` is built on.
    """

    # ``forbid`` blocks any backend attribute from leaking onto a candidate.
    model_config = ConfigDict(extra="forbid")

    key: str
    score: float
    payload: dict[str, Any]
    origin: CandidateOrigin
    vector_cosine: float | None = None
