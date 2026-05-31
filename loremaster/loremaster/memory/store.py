"""Generic, durable project memory over a dedicated ``lore_<slug>_memory`` collection.

This layer generalises odoo-code's ``correction.py`` into a domain-neutral note
store. Where ``correction.py`` embedded a *query* and stored a pointer to the
"correct" chunk (and carried per-author scope + a rate-limiter), this store
embeds **the note text itself** and makes that text the recallable content. The
multi-user scope and rate-limit are deliberately dropped (the lore deployment is
single-user/localhost or service-gated upstream); what is *kept and generalised*
is the durable, separate memory collection and the deterministic, dedup-safe id.

The contract:

* :class:`MemoryRef` — a **versioned** reference from a memory to an indexed
  chunk-key. Every ref carries a ``key_version`` (defaulting to the base
  :data:`~loremaster.extension.DEFAULT_KEY_VERSION`), so a change to the keying
  scheme is *migratable* — a stored memory pointing at an old key version is
  detectable, never a silent orphan. This is the migration-safe correction case.
* :class:`RecalledMemory` — the summarised value object :meth:`MemoryStore.recall_memory`
  returns: the note text + caller metadata + its refs + the similarity score.
  Recall never leaks a raw :class:`~qdrant_client.models.ScoredPoint`.
* :class:`MemoryStore` — an OOP store dependency-injected with a
  :class:`~loremaster.store.qdrant.QdrantStore` (named for the *memory*
  collection) and an :class:`~loresigil.base.Embedder`. It reuses the store's
  ``ensure_collection``/``upsert``/``search`` verbatim; it owns no Qdrant wiring
  of its own beyond shaping the payload and the deterministic id.

The deterministic id (``uuid5`` over the note text + a refs stamp) means saving
the **same note** twice overwrites the same point rather than multiplying it —
while the *same prose pointing at a different chunk* is a genuinely distinct
memory (two corrections), because the refs are folded into the id.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from loresigil.base import Embedder
from pydantic import BaseModel, ConfigDict, Field

from loremaster.extension import DEFAULT_KEY_VERSION
from loremaster.index.records import Record
from loremaster.store.qdrant import QdrantStore

# Default number of notes a recall returns when the caller does not specify ``k``.
_DEFAULT_RECALL_K = 5

# Payload keys. ``note_text`` is the recallable content; ``kind`` marks the point
# as a memory (the generic, domain-neutral analog of correction.py's ``source``);
# the rest carry the caller's metadata, the versioned refs, and a creation stamp.
_PAYLOAD_NOTE_TEXT = "note_text"
_PAYLOAD_KIND = "kind"
_PAYLOAD_METADATA = "metadata"
_PAYLOAD_REFS = "refs"
_PAYLOAD_CREATED_AT = "created_at"

# The constant ``kind`` stamped on every memory point.
_KIND_MEMORY = "memory"

# UUID5 name components, joined by this separator. ``memory`` namespaces the id so
# a memory id can never collide with a structural chunk point id.
_ID_PREFIX = "memory"
_ID_SEPARATOR = ":"

# Within the refs stamp, the per-ref fields and the inter-ref join. Sorting the
# refs before stamping makes the id order-insensitive (the same set of refs in
# any order dedups to one point).
_REF_FIELD_SEPARATOR = "@"
_REF_JOIN = ","


class MemoryRef(BaseModel):
    """A versioned reference from a memory to an indexed chunk-key.

    Attributes:
        chunk_key: The semantic chunk-key this memory references (e.g. the value
            an :meth:`~loremaster.extension.Extension.chunk_key` seam produces).
        key_version: The keying-scheme version the ``chunk_key`` was minted under.
            Defaults to :data:`~loremaster.extension.DEFAULT_KEY_VERSION` so a ref
            is never silently unversioned; a keying change bumps this, making the
            stored reference migratable instead of a silent orphan.
    """

    model_config = ConfigDict(extra="forbid")

    chunk_key: str
    key_version: int = DEFAULT_KEY_VERSION


class RecalledMemory(BaseModel):
    """A summarised recalled note — never a raw Qdrant point.

    Attributes:
        text: The note text — the recallable content.
        metadata: The caller-supplied metadata stored with the note.
        refs: The versioned chunk-key references attached to the note.
        score: The similarity score of this note against the recall query.
    """

    model_config = ConfigDict(extra="forbid")

    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    refs: list[MemoryRef] = Field(default_factory=list)
    score: float


class MemoryStore:
    """Durable, generic project memory over a dedicated ``lore_<slug>_memory`` collection.

    Args:
        store: The :class:`~loremaster.store.qdrant.QdrantStore` for the *memory*
            collection (its slug is ``<project_slug>_memory``, so the collection
            name is ``lore_<project_slug>_memory``). Injected so the same store
            machinery (ensure/upsert/search) is reused and tests can pass a
            real-server client.
        embedder: The :class:`~loresigil.base.Embedder`; its ``dim`` sizes the
            collection, document side embeds saved notes, query side embeds
            recalls.
    """

    def __init__(self, *, store: QdrantStore, embedder: Embedder) -> None:
        self._store = store
        self._embedder = embedder

    @property
    def collection_name(self) -> str:
        """The dedicated memory collection name (``lore_<slug>_memory``)."""
        return self._store.collection_name

    async def ensure_ready(self) -> None:
        """Create the memory collection at the embedder's dim (COSINE), idempotently."""
        await self._store.ensure_collection(self._embedder.dim)

    async def save_memory(
        self,
        text: str,
        *,
        metadata: dict[str, Any] | None = None,
        refs: list[MemoryRef] | None = None,
    ) -> str:
        """Embed and persist a note whose *text* is the recallable content.

        The note text is embedded document-side and stored verbatim in the
        payload, so a later :meth:`recall_memory` returns the prose itself. The
        point id is deterministic (``uuid5`` over the note text + a stamp of its
        refs), so re-saving the same note (with the same refs) overwrites the same
        point rather than multiplying it — while the same prose pointing at a
        *different* chunk is a distinct memory.

        Args:
            text: The note text — the recallable content.
            metadata: Optional caller metadata stored alongside the note.
            refs: Optional versioned chunk-key references (the migration-safe
                correction case); each carries its own ``key_version``.

        Returns:
            The deterministic point id (a canonical UUID string).
        """
        resolved_refs = list(refs or ())
        memory_id = self._memory_id(text, resolved_refs)

        embed_result = await self._embedder.embed_documents([text])
        vector = embed_result.vectors[0]
        if vector is None:
            raise ValueError(f"the embedder permanently failed to embed memory {memory_id!r}")

        payload: dict[str, Any] = {
            _PAYLOAD_NOTE_TEXT: text,
            _PAYLOAD_KIND: _KIND_MEMORY,
            _PAYLOAD_METADATA: dict(metadata or {}),
            _PAYLOAD_REFS: [ref.model_dump() for ref in resolved_refs],
            _PAYLOAD_CREATED_AT: datetime.now(UTC).isoformat(),
        }
        record = Record(point_id=memory_id, embedding_text=text, payload=payload)
        await self._store.upsert([(record, vector)])
        return memory_id

    async def recall_memory(self, query: str, k: int = _DEFAULT_RECALL_K) -> list[RecalledMemory]:
        """Embed a query and return the nearest saved notes, summarised.

        The query is embedded query-side and used to search the memory collection;
        each hit is mapped to a :class:`RecalledMemory` (text + metadata + refs +
        score). The result is the summarised value objects — never the raw
        :class:`~qdrant_client.models.ScoredPoint`\\ s.

        Args:
            query: The recall query text.
            k: The maximum number of notes to return.

        Returns:
            The nearest notes, most similar first, capped at ``k``.
        """
        vector = await self._embedder.embed_query(query)
        hits = await self._store.search(vector, k=k)
        return [self._to_recalled(hit.payload or {}, hit.score) for hit in hits]

    @staticmethod
    def _to_recalled(payload: dict[str, Any], score: float) -> RecalledMemory:
        """Map a stored payload + score into a summarised :class:`RecalledMemory`."""
        raw_refs = payload.get(_PAYLOAD_REFS, []) or []
        refs = [MemoryRef.model_validate(raw_ref) for raw_ref in raw_refs]
        return RecalledMemory(
            text=payload.get(_PAYLOAD_NOTE_TEXT, ""),
            metadata=dict(payload.get(_PAYLOAD_METADATA, {}) or {}),
            refs=refs,
            score=score,
        )

    @classmethod
    def _memory_id(cls, text: str, refs: list[MemoryRef]) -> str:
        """Derive the deterministic ``uuid5`` id for a note + its refs.

        The id is ``uuid5(NAMESPACE_URL, "memory:{text}:{refs_stamp}")`` where the
        refs stamp is the order-insensitive concatenation of each ref's
        ``chunk_key@key_version``. Identical (text, refs) ⇒ identical id (dedup);
        the same text with different refs ⇒ a distinct id (distinct corrections).

        Args:
            text: The note text.
            refs: The note's versioned refs.

        Returns:
            The deterministic point id as a canonical UUID string.
        """
        stamped_refs = sorted(
            f"{ref.chunk_key}{_REF_FIELD_SEPARATOR}{ref.key_version}" for ref in refs
        )
        refs_stamp = _REF_JOIN.join(stamped_refs)
        name = _ID_SEPARATOR.join((_ID_PREFIX, text, refs_stamp))
        return str(uuid.uuid5(uuid.NAMESPACE_URL, name))
