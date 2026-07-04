"""Generic, durable project memory over a dedicated ``lore_<slug>_memory`` collection.

This layer generalises odoo-code's ``correction.py`` into a domain-neutral note
store. Where ``correction.py`` embedded a *query* and stored a pointer to the
"correct" chunk (and carried per-author scope + a rate-limiter), this store
embeds **the note text itself** and makes that text the recallable content. The
multi-user scope and rate-limit are deliberately dropped (the lore deployment is
single-user/localhost or service-gated upstream); what is *kept and generalised*
is the durable, separate memory collection and the deterministic, dedup-safe id.

The contract:

* :class:`~loremaster.memory.backend.MemoryRef` — a **versioned** reference from
  a memory to an indexed chunk-key. It (and the deterministic-id helpers below)
  now live in :mod:`loremaster.memory.backend`, the storage-agnostic id-minting
  source of truth; this module re-exports ``MemoryRef`` and delegates its
  ``_refs_stamp`` / ``_refs_from_stamp`` / ``_memory_id`` classmethods to
  backend's ``derive_refs_stamp`` / ``refs_from_stamp`` / ``derive_memory_id``,
  so the two paths cannot drift while this Qdrant-era module awaits deletion.
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

from datetime import UTC, datetime
from typing import Any

from loresigil.base import Embedder
from pydantic import BaseModel, ConfigDict, Field

from loremaster.index.records import Record
from loremaster.memory.backend import (
    MemoryRef,
    derive_memory_id,
    derive_refs_stamp,
    refs_from_stamp,
)
from loremaster.memory.ledger import MemoryLedger, MemoryRecord
from loremaster.store.qdrant import QdrantStore

# Default number of notes a recall returns when the caller does not specify ``k``.
_DEFAULT_RECALL_K = 5

# Page size for the FP-06 ledger backfill sweep over the memory collection. A
# memory store holds far fewer points than a code collection, so a single
# moderate page typically covers the whole collection in one round-trip while
# the underlying ``scroll_all`` still follows the cursor if it does not.
_BACKFILL_SCROLL_PAGE = 256

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


class MemoryCollectionDimMismatchError(RuntimeError):
    """Raised when a pre-existing memory collection has the WRONG vector size (FP-12).

    Mirrors ``run_probe_gate``'s existing-collection refusal for the CODE
    collection: a memory collection left at an old model's dim must NOT be used
    silently (a wrong dim silently corrupts recall) and must NEVER be
    auto-recreated (that would destroy the very memories the gate protects). The
    message names the collection and both sizes so the operator can re-create it
    deliberately or fix the config.
    """


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
        """Ensure the memory collection at the embedder's dim, REFUSING a wrong-dim one.

        FP-12 memory-dim gate: a memory collection that ALREADY exists at a
        vector size != the embedder's ``dim`` (e.g. left behind by an older
        model) must NOT be used silently and must NEVER be auto-recreated —
        mirroring ``run_probe_gate``'s existing-collection refusal for the code
        collection. The embedder's ``dim`` is the source of truth here (it equals
        ``config.embedding.dim`` once the probe gate has passed). A matching dim
        or an ABSENT collection proceeds: the collection is created at the
        embedder's dim (COSINE), idempotently. A mismatch raises and leaves the
        wrong-dim collection INTACT.

        Raises:
            MemoryCollectionDimMismatchError: When the collection already exists
                at a vector size that differs from the embedder's ``dim``.
        """
        expected_dim = self._embedder.dim
        # Check the EXISTING collection's size BEFORE ensuring it: an absent
        # collection reports ``None`` (create it); a mismatch refuses up front so
        # ``ensure_collection`` never touches a wrong-dim collection.
        existing_dim = await self._store.collection_dim()
        if existing_dim is not None and existing_dim != expected_dim:
            raise MemoryCollectionDimMismatchError(
                f"existing memory collection {self.collection_name!r} has vector size "
                f"{existing_dim} but the embedder dim is {expected_dim}; refusing to start "
                f"and leaving the collection INTACT (never auto-recreated). Re-create it "
                f"deliberately, or fix the model/config to match."
            )
        await self._store.ensure_collection(expected_dim)

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

    async def backfill_ledger_from_store(self) -> int:
        """Capture pre-v0.3.6 Qdrant memories into the durable ledger (FP-06 backfill).

        The write-through ledger only protects memories saved AFTER v0.3.6; a
        memory written by an OLDER build lives only in Qdrant, so a wipe still
        loses it. This closes the gap: scroll EVERY point in the memory
        collection, reconstruct each memory's text / metadata / refs from its
        payload, recompute the refs stamp via the SAME stamping the id folds in,
        and record it under its existing (deterministic) point id — so a later
        :meth:`restore_if_diverged` re-embeds it and a re-mint overwrites the
        Qdrant point in place rather than duplicating.

        Idempotent and no-op-friendly: a point ALREADY in the ledger is skipped
        (membership by id), so the steady-state post-v0.3.6 boot records nothing
        and a second pass adds nothing.

        Returns:
            The number of NEW ledger rows backfilled (``0`` when the ledger
            already covers every store memory, or when no ledger is configured).
        """
        # No ledger ⇒ legacy Qdrant-only store: nothing durable to backfill into.
        if self._ledger is None:
            return 0

        # Membership-by-id: only points NOT yet in the ledger are new rows, so a
        # steady-state boot (every memory already recorded) records nothing and
        # returns 0 — never re-recording (the no-op / idempotence guarantee).
        existing_ids = {record.memory_id for record in self._ledger.all_records()}

        points = await self._store.scroll_all(_BACKFILL_SCROLL_PAGE)
        backfilled = 0
        for point in points:
            # The deterministic point id IS the ledger's natural key; recording
            # under it keeps the two in lock-step (a later restore overwrites in
            # place). Skip points the ledger already knows.
            point_id = str(point.id)
            if point_id in existing_ids:
                continue
            payload = point.payload or {}
            text = payload.get(_PAYLOAD_NOTE_TEXT, "")
            metadata = dict(payload.get(_PAYLOAD_METADATA, {}) or {})
            refs = self._refs_from_payload(payload)
            # Recompute the stamp from the payload's refs (NOT read back) so the
            # row re-mints the SAME id the existing point was minted under.
            refs_stamp = self._refs_stamp(refs)
            self._ledger.record(
                memory_id=point_id,
                text=text,
                metadata=metadata,
                refs_stamp=refs_stamp,
            )
            backfilled += 1
        return backfilled

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

    @classmethod
    def _to_recalled(cls, payload: dict[str, Any], score: float) -> RecalledMemory:
        """Map a stored payload + score into a summarised :class:`RecalledMemory`."""
        return RecalledMemory(
            text=payload.get(_PAYLOAD_NOTE_TEXT, ""),
            metadata=dict(payload.get(_PAYLOAD_METADATA, {}) or {}),
            refs=cls._refs_from_payload(payload),
            score=score,
        )

    @classmethod
    def _refs_stamp(cls, refs: list[MemoryRef]) -> str:
        """Fold a memory's versioned refs into an order-insensitive stamp.

        Thin delegator to :func:`~loremaster.memory.backend.derive_refs_stamp`
        (the storage-agnostic id-minting source of truth); kept so this Qdrant-era
        module stays green until its deletion, with NO duplicated stamping logic.
        See the backend function for the full contract.

        Args:
            refs: The memory's versioned refs.

        Returns:
            The order-insensitive refs stamp.
        """
        return derive_refs_stamp(refs)

    @classmethod
    def _refs_from_stamp(cls, refs_stamp: str) -> list[MemoryRef]:
        """Reconstruct the versioned refs from a persisted refs stamp.

        Thin delegator to :func:`~loremaster.memory.backend.refs_from_stamp` (the
        inverse of :meth:`_refs_stamp`); kept for backward-compat until this
        module is deleted, with NO duplicated parsing logic.

        Args:
            refs_stamp: The order-insensitive refs stamp persisted in the ledger.

        Returns:
            The reconstructed versioned refs (empty for an empty stamp).
        """
        return refs_from_stamp(refs_stamp)

    @classmethod
    def _refs_from_payload(cls, payload: dict[str, Any]) -> list[MemoryRef]:
        """Reconstruct the versioned refs from a stored Qdrant memory payload.

        The backfill reads the payload's ``refs`` (a list of
        :class:`MemoryRef`-shaped dicts, the inverse of :meth:`_build_payload`'s
        ``model_dump``) back into :class:`MemoryRef` objects, from which the
        refs stamp is recomputed so the ledger row re-mints the SAME id the
        existing point carries. A missing/empty ``refs`` key yields no refs.

        Args:
            payload: A stored Qdrant memory-point payload.

        Returns:
            The reconstructed versioned refs (empty when the payload has none).
        """
        raw_refs = payload.get(_PAYLOAD_REFS, []) or []
        return [MemoryRef.model_validate(raw_ref) for raw_ref in raw_refs]

    @classmethod
    def _memory_id(cls, text: str, refs_stamp: str) -> str:
        """Derive the deterministic ``uuid5`` id for a note + its refs stamp.

        Thin delegator to :func:`~loremaster.memory.backend.derive_memory_id` (the
        storage-agnostic id-minting source of truth); kept so this Qdrant-era
        module stays green until its deletion, with NO duplicated id logic. See
        the backend function for the full contract.

        Args:
            text: The note text.
            refs_stamp: The order-insensitive refs stamp (from :meth:`_refs_stamp`).

        Returns:
            The deterministic point id as a canonical UUID string.
        """
        return derive_memory_id(text, refs_stamp)
