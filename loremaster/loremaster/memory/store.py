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

Durability (FP-06): an optional :class:`~loremaster.memory.ledger.MemoryLedger`
is the durable write-through source of truth. ``save_memory`` writes the ledger
row first (the durable copy a Qdrant wipe cannot touch), then upserts Qdrant; on
startup, :meth:`MemoryStore.restore_if_diverged` re-embeds the ledger into a
wiped/short memory collection.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from loresigil.base import Embedder
from pydantic import BaseModel, ConfigDict, Field

from loremaster.extension import DEFAULT_KEY_VERSION
from loremaster.index.records import Record
from loremaster.memory.ledger import MemoryLedger, MemoryRecord
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
        ledger: The optional durable write-through
            :class:`~loremaster.memory.ledger.MemoryLedger` (the source of truth a
            Qdrant wipe cannot touch). When supplied, ``save_memory`` write-throughs
            to it and :meth:`restore_if_diverged` rebuilds a wiped/short collection
            from it. ``None`` (the default) preserves the legacy Qdrant-only store.
    """

    def __init__(
        self,
        *,
        store: QdrantStore,
        embedder: Embedder,
        ledger: MemoryLedger | None = None,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._ledger = ledger

    @property
    def collection_name(self) -> str:
        """The dedicated memory collection name (``lore_<slug>_memory``)."""
        return self._store.collection_name

    @property
    def ledger(self) -> MemoryLedger | None:
        """The durable write-through ledger, or ``None`` when not configured."""
        return self._ledger

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

        Durable write-through (FP-06): when a ledger is configured the durable
        ledger row is written FIRST — before the volatile Qdrant upsert — so even
        if the embed/upsert raises, the memory survives on the state volume and a
        later :meth:`restore_if_diverged` re-embeds it. The note text is then
        embedded document-side and stored verbatim in the Qdrant payload, so a
        later :meth:`recall_memory` returns the prose itself. The point id is
        deterministic (``uuid5`` over the note text + a stamp of its refs), so
        re-saving the same note (with the same refs) overwrites the same point and
        the same ledger row rather than multiplying either — while the same prose
        pointing at a *different* chunk is a distinct memory.

        Args:
            text: The note text — the recallable content.
            metadata: Optional caller metadata stored alongside the note.
            refs: Optional versioned chunk-key references (the migration-safe
                correction case); each carries its own ``key_version``.

        Returns:
            The deterministic point id (a canonical UUID string).
        """
        resolved_refs = list(refs or ())
        refs_stamp = self._refs_stamp(resolved_refs)
        memory_id = self._memory_id(text, refs_stamp)
        resolved_metadata = dict(metadata or {})

        # Write-through DURABLE FIRST: the ledger row is the copy a Qdrant wipe
        # cannot touch. Persisting it before the embed/upsert means a failure on
        # the volatile side still leaves a recoverable memory (zero loss).
        if self._ledger is not None:
            self._ledger.record(
                memory_id=memory_id,
                text=text,
                metadata=resolved_metadata,
                refs_stamp=refs_stamp,
            )

        embed_result = await self._embedder.embed_documents([text])
        vector = embed_result.vectors[0]
        if vector is None:
            raise ValueError(f"the embedder permanently failed to embed memory {memory_id!r}")

        payload = self._build_payload(text, resolved_metadata, resolved_refs)
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

    async def restore_if_diverged(self) -> int:
        """Rebuild a wiped/short memory collection from the durable ledger.

        When the live ``store.count_points()`` is below the ledger's row count,
        re-embed ALL ledger records into the memory collection (the deterministic
        ``uuid5`` ids overwrite in place, so the rebuild never multiplies points)
        and return the number restored. A no-op (returns ``0``, embeds nothing)
        when the collection and ledger already agree — the spy-watched guard that
        a healthy boot never needlessly re-embeds.

        Returns:
            The number of memories re-embedded into the collection (``0`` when in
            sync or when no ledger is configured).
        """
        # No ledger ⇒ legacy Qdrant-only store: nothing durable to restore from.
        if self._ledger is None:
            return 0

        ledger_count = self._ledger.count()
        # The independent divergence oracle: a SHORT live collection (e.g. wiped)
        # has fewer points than the ledger has rows. Equal/greater ⇒ in sync, so
        # do NOT embed (the spy proves a healthy boot re-embeds nothing).
        if await self._store.count_points() >= ledger_count:
            return 0

        records = self._ledger.all_records()
        return await self._restore_records(records)

    async def _restore_records(self, records: list[MemoryRecord]) -> int:
        """Re-embed every ledger record back into the memory collection.

        Each record is re-embedded document-side and re-minted with the SAME
        deterministic id (from its ``text`` + persisted ``refs_stamp``), so the
        upsert overwrites in place — a restore can run twice without multiplying
        points.

        Args:
            records: The durable ledger records to re-embed and upsert.

        Returns:
            The number of records re-embedded into the collection.
        """
        restored = 0
        for record in records:
            embed_result = await self._embedder.embed_documents([record.text])
            vector = embed_result.vectors[0]
            if vector is None:
                # A permanently un-embeddable ledger row cannot be restored; skip
                # it rather than aborting the whole rebuild (best-effort recovery).
                continue
            refs = self._refs_from_stamp(record.refs_stamp)
            payload = self._build_payload(record.text, record.metadata, refs)
            point = Record(
                point_id=record.memory_id,
                embedding_text=record.text,
                payload=payload,
            )
            await self._store.upsert([(point, vector)])
            restored += 1
        return restored

    @staticmethod
    def _build_payload(
        text: str, metadata: dict[str, Any], refs: list[MemoryRef]
    ) -> dict[str, Any]:
        """Shape the Qdrant point payload for a memory (save + restore share this)."""
        return {
            _PAYLOAD_NOTE_TEXT: text,
            _PAYLOAD_KIND: _KIND_MEMORY,
            _PAYLOAD_METADATA: dict(metadata),
            _PAYLOAD_REFS: [ref.model_dump() for ref in refs],
            _PAYLOAD_CREATED_AT: datetime.now(UTC).isoformat(),
        }

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
    def _refs_stamp(cls, refs: list[MemoryRef]) -> str:
        """Fold a memory's versioned refs into an order-insensitive stamp.

        Each ref becomes ``chunk_key@key_version``; the set is sorted (so the same
        refs in any order produce the same stamp) and joined by ``,``. An empty
        ref list stamps the empty string. This is the EXACT stamp persisted to the
        ledger and folded into the deterministic id, so a restore re-mints the
        SAME id and overwrites in place.

        Args:
            refs: The memory's versioned refs.

        Returns:
            The order-insensitive refs stamp.
        """
        stamped_refs = sorted(
            f"{ref.chunk_key}{_REF_FIELD_SEPARATOR}{ref.key_version}" for ref in refs
        )
        return _REF_JOIN.join(stamped_refs)

    @classmethod
    def _refs_from_stamp(cls, refs_stamp: str) -> list[MemoryRef]:
        """Reconstruct the versioned refs from a persisted refs stamp.

        The inverse of :meth:`_refs_stamp`: split the stamp on the join separator,
        then each piece on the field separator back into a ``(chunk_key,
        key_version)`` :class:`MemoryRef`. An empty stamp yields no refs. Used by
        the restore path to repopulate the Qdrant payload's refs from the ledger.

        Args:
            refs_stamp: The order-insensitive refs stamp persisted in the ledger.

        Returns:
            The reconstructed versioned refs (empty for an empty stamp).
        """
        if not refs_stamp:
            return []
        refs: list[MemoryRef] = []
        for piece in refs_stamp.split(_REF_JOIN):
            chunk_key, _, version = piece.rpartition(_REF_FIELD_SEPARATOR)
            refs.append(MemoryRef(chunk_key=chunk_key, key_version=int(version)))
        return refs

    @classmethod
    def _memory_id(cls, text: str, refs_stamp: str) -> str:
        """Derive the deterministic ``uuid5`` id for a note + its refs stamp.

        The id is ``uuid5(NAMESPACE_URL, "memory:{text}:{refs_stamp}")`` where the
        refs stamp comes from :meth:`_refs_stamp`. Identical (text, refs) ⇒
        identical id (dedup); the same text with different refs ⇒ a distinct id
        (distinct corrections). Taking the precomputed stamp (rather than the raw
        refs) keeps the ledger row and the id in lock-step — the ledger stores the
        SAME stamp the id is minted from.

        Args:
            text: The note text.
            refs_stamp: The order-insensitive refs stamp (from :meth:`_refs_stamp`).

        Returns:
            The deterministic point id as a canonical UUID string.
        """
        name = _ID_SEPARATOR.join((_ID_PREFIX, text, refs_stamp))
        return str(uuid.uuid5(uuid.NAMESPACE_URL, name))
