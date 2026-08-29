"""ADVERSARIAL in-memory ``FakeMemoryBackend`` — the P7 memory-backend fake-vs-
real parity pin (mirrors the house style of ``_task_fakes.py``).

``test_memory_backend.py``'s own ``make_backend`` fixture is parametrized over
BOTH the real SurrealDB-backed :class:`~loremaster.memory.local.LocalMemoryBackend`
and this fake, so the exact same 46-test contract suite runs against both. That
parity pin is only as good as this fake is UNFRIENDLY: a fake that quietly
promises more than production (insertion-ordered recall, a shared mutable
:class:`~loremaster.memory.backend.RecalledMemory`, cosmetic/bookkeeping scores
instead of a real similarity) would let a consumer bug pass green here and then
break for real. Each deliberate adversarial property below exists to catch one
such bug:

1. :meth:`FakeMemoryBackend.recall` ranks by a REAL cosine similarity — the dot
   product of the injected embedder's own (L2-normalized) query and document
   vectors, never insertion-order or a bookkeeping counter — and ties break on
   the memory's opaque ``uuid5`` id (ascending), mirroring
   :meth:`~loremaster.memory.local.LocalMemoryBackend`'s own
   ``(-score, bare_id)`` tiebreak: a consumer assuming "creation order" or a
   fabricated score breaks here exactly as it would against the real backend.
2. Every public ``async`` method opens with ``await asyncio.sleep(0)`` — a real
   event-loop yield point, matching what a live socket-backed call would do.
3. Every returned :class:`~loremaster.memory.backend.RecalledMemory` is built
   FRESH per call (a new value object from the CURRENT stored row state, with
   its own ``source`` copy) — production deserialises a fresh row on every
   query; a consumer that stashes a returned memory and expects it to reflect a
   LATER reinforcement bump must never observe that through this fake either.
4. The reinforcement bump is applied to the STORED row only AFTER the returned
   snapshot is built, so the current call sees the PRE-bump value and only a
   SUBSEQUANT call observes it — the exact ordering the contract pins.
5. The durability seam is honoured HONESTLY: the durable ledger write-through
   happens FIRST, and only THEN (never before) does the store-side write fail
   for a backend built against the dead-URL marker — see
   ``store_unreachable`` below.

IDENTITY: memory ids are minted via the SAME production pure helpers this fake
imports — :func:`~loremaster.memory.backend.derive_refs_stamp` /
:func:`~loremaster.memory.backend.derive_memory_id` /
:func:`~loremaster.memory.backend.refs_from_stamp` — so a wrong id
here would be a wrong id in the SAME source of truth production uses, not a
fake-only drift. The ``lore_ref=<chunk_key>[@version]`` label parsing, by
contrast, is the WIRE CONTRACT itself (documented in
``loremaster.memory.backend`` and independently reconstructed by
``test_memory_backend.py``'s own ``lore_ref_label`` helper) — this fake
reimplements that parsing independently rather than reaching into
:class:`~loremaster.memory.local.LocalMemoryBackend`'s private parser, exactly
as ``_task_fakes.py`` keeps its own copy of the task status vocabulary rather
than importing the test's.

Fidelity: :class:`~loremaster.memory.backend.MemorySource`,
:class:`~loremaster.memory.backend.RecalledMemory`,
:class:`~loremaster.memory.backend.RecalledRef`,
:class:`~loremaster.memory.backend.MemoryNotFoundError`, and the plan-pinned
``IMPORTANCE_DEFAULTS_BY_KIND`` / ``ONGOING_DEFAULT_TTL`` / ``REINFORCEMENT_STEP``
constants are all IMPORTED from ``loremaster.memory.backend`` — never
redefined here, so this fake can never drift from the real wire vocabulary it
stands in for. The durable ledger is the REAL
:class:`~loremaster.memory.ledger.MemoryLedger` (SQLite) the fixture hands in —
this fake never substitutes a fake ledger, so the write-through and replay
seams are exercised against the actual durable store both backends share.

DEAD-URL MECHANISM: :class:`FakeMemoryBackend` takes an explicit
``store_unreachable: bool`` constructor flag (never a probe against ``url`` —
there is nothing to probe in-process). The ``make_backend`` fixture's "fake"
branch derives that flag itself by comparing the caller's ``url`` argument
against ``_DEAD_URL`` (the one url this suite ever passes deliberately, for the
durability seam) — "a constructor flag the fixture derives", per the brief.
When set, :meth:`FakeMemoryBackend.remember` writes the ledger row first (the
durability guarantee) and ONLY THEN raises
:class:`~loremaster.store._txn.SurrealConnectionError` — the same exception
type a real unreachable SurrealDB surfaces — so a caller catching that
specific type in production is not accidentally let off the hook here.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from loremaster.extension import DEFAULT_KEY_VERSION
from loremaster.memory.backend import (
    IMPORTANCE_DEFAULTS_BY_KIND,
    ONGOING_DEFAULT_TTL,
    REINFORCEMENT_STEP,
    ExistingChunksFn,
    MemoryNotFoundError,
    MemoryRef,
    MemorySource,
    RecalledMemory,
    RecalledRef,
    derive_memory_id,
    derive_refs_stamp,
    refs_from_stamp,
)
from loremaster.memory.ledger import MemoryLedger, MemoryRecord
from loremaster.store._txn import SurrealConnectionError
from loresigil.base import Embedder
from pydantic import ValidationError

# The kind a memory defaults to when none is recorded (mirrors
# ``loremaster.memory.local``'s plan-pinned default for a pre-v2 ledger row).
_DEFAULT_KIND = "fact"

# The ``kind`` that acquires the default TTL when saved without an explicit
# ``expires_at``.
_ONGOING_KIND = "ongoing"

# The ``MemorySource.kind`` a memory saved without an explicit source carries.
_DEFAULT_SOURCE_KIND = "operator"

# The inclusive importance bounds (a fraction).
_IMPORTANCE_FLOOR = 0.0
_IMPORTANCE_CEILING = 1.0

# The ``include`` value that lifts the live-only ``valid_until`` recall filter.
_INCLUDE_SUPERSEDED = "superseded"

# The default cap on the number of memories a recall returns.
_DEFAULT_RECALL_K = 5

# The flat ``lore_ref`` label form + its optional ``@version`` separator — the
# wire contract's own convention (independently reconstructed here, see the
# module docstring's IDENTITY section).
_LORE_REF_LABEL_PREFIX = "lore_ref="
_REF_VERSION_SEPARATOR = "@"

# The durable-ledger metadata keys this fake's own write/replay round-trips
# through (a private convention of THIS fake — internally consistent, not
# required to match ``loremaster.memory.local``'s own metadata key strings).
_META_KIND = "kind"
_META_IMPORTANCE = "importance"
_META_LABELS = "labels"
_META_SOURCE = "source"
_META_EXPIRES_AT = "expires_at"
_META_SUPERSEDES = "supersedes"


def _parse_lore_ref_label(label: str) -> tuple[str, int] | None:
    """Parse a ``lore_ref=<chunk_key>[@version]`` label, or ``None`` for a plain label.

    Independent reimplementation of the wire contract (see the module
    docstring's IDENTITY section) — NOT a call into
    :class:`~loremaster.memory.local.LocalMemoryBackend`'s private parser. A
    bare label (no ``@version``) defaults to
    :data:`~loremaster.extension.DEFAULT_KEY_VERSION`.
    """
    if not label.startswith(_LORE_REF_LABEL_PREFIX):
        return None
    body = label[len(_LORE_REF_LABEL_PREFIX) :]
    chunk_key, separator, version = body.rpartition(_REF_VERSION_SEPARATOR)
    if separator and version.isdigit():
        return chunk_key, int(version)
    return body, DEFAULT_KEY_VERSION


def _build_lore_ref_label(chunk_key: str, key_version: int) -> str:
    """Build the flat ``lore_ref=<chunk_key>@<version>`` label (replay reconstruction)."""
    return f"{_LORE_REF_LABEL_PREFIX}{chunk_key}{_REF_VERSION_SEPARATOR}{key_version}"


def _refs_from_labels(labels: list[str]) -> list[MemoryRef]:
    """The versioned :class:`MemoryRef`\\ s a memory's ``lore_ref`` labels fold into.

    Feeds :func:`~loremaster.memory.backend.derive_refs_stamp` — reproducing the
    v0.3 deterministic-id derivation EXACTLY (the SAME production pure helper
    :class:`~loremaster.memory.local.LocalMemoryBackend` itself calls).
    """
    refs: list[MemoryRef] = []
    for label in labels:
        parsed = _parse_lore_ref_label(label)
        if parsed is not None:
            chunk_key, key_version = parsed
            refs.append(MemoryRef(chunk_key=chunk_key, key_version=key_version))
    return refs


def _labels_from_refs_stamp(refs_stamp: str) -> list[str]:
    """Reconstruct ``lore_ref=`` labels from a ledger row's refs stamp (replay)."""
    return [
        _build_lore_ref_label(ref.chunk_key, ref.key_version)
        for ref in refs_from_stamp(refs_stamp)
    ]


def _parse_iso(value: Any) -> datetime | None:
    """Parse an ISO-8601 datetime string (or ``None``) back into a datetime."""
    if not isinstance(value, str):
        return None
    return datetime.fromisoformat(value)


def _utc_now() -> datetime:
    """A tz-aware UTC timestamp — every stamped time in this fake uses this."""
    return datetime.now(UTC)


@dataclass
class _StoredMemory:
    """One in-memory row — the fake's stand-in for a ``memory`` table record.

    Mutable (unlike the immutable :class:`RecalledMemory` this fake hands back
    to callers): supersession and reinforcement mutate a row'S OWN fields in
    place, exactly as production's ``UPDATE ... SET`` fragments do — never a
    caller-visible object.
    """

    id: str
    text: str
    kind: str
    labels: list[str]
    source: MemorySource
    importance: float
    valid_from: datetime
    created_at: datetime
    vector: list[float]
    valid_until: datetime | None = None
    expires_at: datetime | None = None
    supersedes: str | None = None
    superseded_by: str | None = None


class FakeMemoryBackend:
    """ADVERSARIAL in-memory stand-in for
    :class:`~loremaster.memory.local.LocalMemoryBackend`.

    See the module docstring for the five deliberate adversarial behaviours.
    Every method's PUBLIC surface matches the
    :class:`~loremaster.memory.backend.MemoryBackend` protocol exactly; only
    the storage is a plain in-memory dict rather than a SurrealDB connection.

    Args:
        embedder: The document/query embedder (the SAME injected embedder a
            real backend would use — recall scores are its real cosine
            similarity, never fabricated).
        existing_chunks: The async BATCH chunk-existence drift oracle
            (``chunk_keys -> set[str]``); ONE call resolves drift for a whole
            recall, exactly as the real backend's does.
        ledger: The optional durable write-through ledger — a REAL
            :class:`~loremaster.memory.ledger.MemoryLedger`, never a fake one.
        store_unreachable: When ``True``, every ``remember`` writes its ledger
            row FIRST and then raises :class:`SurrealConnectionError` — the
            dead-URL durability seam (see the module docstring's DEAD-URL
            MECHANISM section).
        url: Cosmetic — folded into the unreachable-store error message only.
    """

    def __init__(
        self,
        *,
        embedder: Embedder,
        existing_chunks: ExistingChunksFn,
        ledger: MemoryLedger | None = None,
        store_unreachable: bool = False,
        url: str = "",
    ) -> None:
        self._embedder = embedder
        self._existing_chunks = existing_chunks
        self._ledger = ledger
        self._store_unreachable = store_unreachable
        self._url = url
        self._rows: dict[str, _StoredMemory] = {}

    @property
    def ledger(self) -> MemoryLedger | None:
        """The durable write-through ledger, or ``None`` when not configured."""
        return self._ledger

    # -- lifecycle ------------------------------------------------------------

    async def ensure_ready(self) -> None:
        """No-op (the fake holds no connection to establish)."""
        await asyncio.sleep(0)

    async def close(self) -> None:
        """No-op (the fake holds no connection to close)."""
        await asyncio.sleep(0)

    # -- writes -----------------------------------------------------------

    async def remember(
        self,
        text: str,
        *,
        kind: str,
        subject: Any = None,
        scope: str | None = None,
        importance: float | None = None,
        source: MemorySource | None = None,
        labels: list[str] | None = None,
        supersedes: str | None = None,
        expires_at: datetime | None = None,
    ) -> str:
        """Persist a memory note and return its deterministic id.

        Order (mirrors the FP-06 durability + input-validation contract):
        validate ``importance`` and check ``supersedes`` existence BEFORE any
        write; write the durable LEDGER row FIRST; THEN — and only then — the
        volatile "store" write (which raises when this fake was built
        ``store_unreachable``).
        """
        await asyncio.sleep(0)
        resolved_importance = self._resolve_importance(kind, importance)
        resolved_source = source if source is not None else MemorySource(kind=_DEFAULT_SOURCE_KIND)
        resolved_labels = list(labels or ())
        refs_stamp = derive_refs_stamp(_refs_from_labels(resolved_labels))
        memory_id = derive_memory_id(text, refs_stamp)
        now = _utc_now()
        resolved_expires = self._resolve_expiry(kind, expires_at, now)

        # Unknown ``supersedes`` is a caller error raised BEFORE any write, so
        # an orphan successor never lands even in the durable ledger.
        if supersedes is not None and supersedes not in self._rows:
            raise MemoryNotFoundError(
                f"cannot supersede unknown memory {supersedes!r}: no such memory exists"
            )

        # Durable write-through FIRST: a Surreal failure below must never lose
        # this memory.
        if self._ledger is not None:
            self._ledger.record(
                memory_id=memory_id,
                text=text,
                metadata=self._ledger_metadata(
                    kind, resolved_importance, resolved_labels, resolved_source,
                    resolved_expires, supersedes,
                ),
                refs_stamp=refs_stamp,
            )

        if self._store_unreachable:
            raise SurrealConnectionError(
                f"could not connect to SurrealDB at {self._url!r} (fake: store_unreachable)"
            )

        vector = await self._embed_document(text, memory_id)
        row = _StoredMemory(
            id=memory_id,
            text=text,
            kind=kind,
            labels=resolved_labels,
            source=resolved_source,
            importance=resolved_importance,
            valid_from=now,
            created_at=now,
            vector=vector,
            expires_at=resolved_expires,
            supersedes=supersedes,
        )
        self._rows[memory_id] = row
        if supersedes is not None:
            old_row = self._rows[supersedes]
            old_row.valid_until = now
            old_row.superseded_by = memory_id
        return memory_id

    async def invalidate(self, memory_id: str, *, subject: Any = None) -> None:
        """Retire a memory with no successor (``valid_until`` set, ``superseded_by`` None).

        ``subject`` is accepted for governed-signature parity with
        :class:`~loremaster.memory.local.LocalMemoryBackend` (packet 63a) and IGNORED — this fake
        pins pre-retrofit MEMORY behaviour, not governance (the 63a contract pins that)."""
        await asyncio.sleep(0)
        row = self._rows.get(memory_id)
        if row is None:
            raise MemoryNotFoundError(
                f"cannot invalidate unknown memory {memory_id!r}: no such memory exists"
            )
        row.valid_until = _utc_now()

    # -- reads ------------------------------------------------------------

    async def recall(
        self,
        query: str,
        *,
        subject: Any = None,
        k: int = _DEFAULT_RECALL_K,
        include: str | None = None,
        as_of: datetime | None = None,
        labels: list[str] | None = None,
        kind: str | None = None,
        lens: str | None = None,
    ) -> list[RecalledMemory]:
        """Embed ``query`` and return the nearest matching memories, reinforced.

        Ranks by a REAL cosine similarity (the injected embedder's own
        normalized vectors), tiebreaking on the opaque memory id — never
        insertion order (adversarial property 1). The returned importance is
        PRE-bump; the reinforcement bump is applied to the stored row only
        AFTER the snapshot is built (adversarial property 4).
        """
        await asyncio.sleep(0)
        if lens is not None:
            raise ValueError(
                f"the fake memory backend does not support a recall lens (got {lens!r}); "
                f"lens is unsupported in P7"
            )
        query_vector = await self._embedder.embed_query(query)
        candidates = [
            row
            for row in self._rows.values()
            if self._matches_filter(row, include, as_of, labels, kind)
        ]
        scored = [(self._score(query_vector, row), row) for row in candidates]
        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        top = scored[: max(k, 0)]
        # Resolve drift for EVERY recalled ref in ONE batch-oracle call, then
        # annotate each row against that shared existing-chunk set — mirrors the
        # real backend's single-query drift resolution (never per-ref lookups).
        existing_chunks = await self._resolve_existing_chunks([row for _, row in top])
        memories = [self._to_recalled(row, score, existing_chunks) for score, row in top]
        await self._reinforce(memories)
        return memories

    async def restore_from_ledger(self) -> int:
        """Replay the durable ledger rows NOT already covered by the store.

        Membership is by deterministic id: a ledger row whose id is already a
        key in ``self._rows`` is skipped, so once the store covers the ledger a
        further restore is a pure no-op — 0 replays, ZERO document embeds (the
        boot-path divergence guard). Calls ``embedder.embed_documents`` exactly
        like production would for each row it genuinely replays, so the
        CountingEmbedder spy tests pass for the right reason.
        """
        await asyncio.sleep(0)
        if self._ledger is None:
            return 0
        records = self._ledger.all_records()
        if not records:
            return 0
        replayed = 0
        for record in records:
            if record.memory_id in self._rows:
                continue
            await self._replay_record(record)
            replayed += 1
        return replayed

    async def rebuild_embeddings(self) -> int:
        """Clear the in-memory store, then replay the ledger — the fake's mirror of
        :meth:`~loremaster.memory.local.LocalMemoryBackend.rebuild_embeddings`.

        There is no table / HNSW index to resize here, so clearing the ``_rows``
        dict stands in for the real backend's drop+recreate; the subsequent
        ledger replay re-embeds every note document-side (the CountingEmbedder spy
        sees the re-embeds). A ledger-less fake is a no-op, matching the real
        backend's guard.
        """
        await asyncio.sleep(0)
        if self._ledger is None:
            return 0
        self._rows.clear()
        return await self.restore_from_ledger()

    # -- recall helpers -----------------------------------------------------

    @staticmethod
    def _matches_filter(  # noqa: PLR0911 - test infra, not restructured in a lint pass
        row: _StoredMemory,
        include: str | None,
        as_of: datetime | None,
        labels: list[str] | None,
        kind: str | None = None,
    ) -> bool:
        """The recall WHERE-equivalent: live-only default, include, as_of, labels, kind.

        Mirrors :meth:`LocalMemoryBackend._build_recall_filter`'s three temporal
        modes exactly: ``as_of=T`` checks the ``[valid_from, valid_until)``
        window (no expiry gate); otherwise live-only unless
        ``include="superseded"`` (plus the expiry gate in both non-``as_of``
        cases). Labels are an ALL-semantics filter appended in every mode;
        ``kind`` (when supplied) is an exact-match filter that composes with
        ``labels`` as an INTERSECTION (both must match).
        """
        if as_of is not None:
            if row.valid_from > as_of:
                return False
            if row.valid_until is not None and row.valid_until <= as_of:
                return False
        else:
            if include != _INCLUDE_SUPERSEDED and row.valid_until is not None:
                return False
            now = _utc_now()
            if row.expires_at is not None and row.expires_at <= now:
                return False
        if labels:
            row_labels = set(row.labels)
            if not all(label in row_labels for label in labels):
                return False
        if kind is not None and row.kind != kind:
            return False
        return True

    @staticmethod
    def _score(query_vector: list[float], row: _StoredMemory) -> float:
        """The real similarity of ``query_vector`` against a stored row's vector.

        A plain dot product: both the fake embedder's query and document
        vectors are L2-normalized by default, so this equals cosine similarity
        — a REAL ranking signal, never insertion-order bookkeeping (adversarial
        property 1/4).
        """
        return sum(q * v for q, v in zip(query_vector, row.vector, strict=True))

    def _to_recalled(
        self, row: _StoredMemory, score: float, existing_chunks: set[str]
    ) -> RecalledMemory:
        """Build a FRESH :class:`RecalledMemory` from a row's CURRENT state.

        Never cached/reused across calls (adversarial property 3): a caller
        that stashes this object must never see a later reinforcement bump
        leak into it. Refs are drift-annotated by MEMBERSHIP in
        ``existing_chunks`` (the subset the batch oracle already resolved for the
        whole recall), exactly as the real backend does.
        """
        refs, plain_labels = self._split_labels(row.labels, existing_chunks)
        return RecalledMemory(
            id=row.id,
            text=row.text,
            score=score,
            kind=row.kind,
            importance=row.importance,
            memory_category=None,
            labels=plain_labels,
            refs=refs,
            source=row.source.model_copy(deep=True),
            valid_from=row.valid_from,
            valid_until=row.valid_until,
            expires_at=row.expires_at,
            created_at=row.created_at,
            supersedes=row.supersedes,
            superseded_by=row.superseded_by,
        )

    async def _resolve_existing_chunks(self, rows: list[_StoredMemory]) -> set[str]:
        """Resolve drift for the WHOLE recall in ONE batch-oracle call.

        Collects the UNIQUE ``lore_ref`` chunk-keys across every recalled row and
        asks the injected batch oracle which still exist — a single call for N
        refs, never one per ref. A recall carrying NO refs skips the oracle
        entirely (nothing to resolve), matching the real backend.
        """
        chunk_keys: set[str] = set()
        for row in rows:
            for label in row.labels:
                parsed = _parse_lore_ref_label(label)
                if parsed is not None:
                    chunk_keys.add(parsed[0])
        if not chunk_keys:
            return set()
        return await self._existing_chunks(sorted(chunk_keys))

    def _split_labels(
        self, labels: list[str], existing_chunks: set[str]
    ) -> tuple[list[RecalledRef], list[str]]:
        """Split stored labels into drift-annotated refs + the plain labels.

        A ``lore_ref=`` label's ``drifted`` is decided by MEMBERSHIP in
        ``existing_chunks`` (the batch oracle's resolved subset) — a key absent
        from that set has drifted; every other label stays plain. Drift is a
        FLAG, never a filter.
        """
        refs: list[RecalledRef] = []
        plain: list[str] = []
        for label in labels:
            parsed = _parse_lore_ref_label(label)
            if parsed is None:
                plain.append(label)
                continue
            chunk_key, key_version = parsed
            drifted = chunk_key not in existing_chunks
            refs.append(RecalledRef(chunk_key=chunk_key, key_version=key_version, drifted=drifted))
        return refs, plain

    async def _reinforce(self, memories: list[RecalledMemory]) -> None:
        """Bump each returned memory's STORED importance by the reinforcement step.

        Mutates ``self._rows`` ONLY — the already-built ``memories`` snapshots
        (about to be returned to the caller) are untouched, so THIS call still
        returns the pre-bump value (adversarial property 4).
        """
        for memory in memories:
            row = self._rows.get(memory.id)
            if row is None:
                continue
            row.importance = min(_IMPORTANCE_CEILING, row.importance + REINFORCEMENT_STEP)

    # -- ledger replay ------------------------------------------------------

    async def _replay_record(self, record: MemoryRecord) -> None:
        """Re-embed one durable ledger row and upsert it under its deterministic id.

        Reconstructs the v2 wire fields from the ledger metadata, falling back
        to the plan-pinned defaults for a pre-v2 row (``kind="fact"``,
        ``trust="experiential"``, live).
        """
        metadata = record.metadata or {}
        kind = str(metadata.get(_META_KIND, _DEFAULT_KIND))
        raw_importance = metadata.get(_META_IMPORTANCE)
        importance = (
            float(raw_importance) if raw_importance is not None else self._default_importance(kind)
        )
        raw_labels = metadata.get(_META_LABELS)
        labels = (
            [str(label) for label in raw_labels]
            if isinstance(raw_labels, list)
            else _labels_from_refs_stamp(record.refs_stamp)
        )
        source = self._source_from_metadata(metadata)
        expires_at = _parse_iso(metadata.get(_META_EXPIRES_AT))
        supersedes = metadata.get(_META_SUPERSEDES)
        now = _utc_now()
        vector = await self._embed_document(record.text, record.memory_id)
        self._rows[record.memory_id] = _StoredMemory(
            id=record.memory_id,
            text=record.text,
            kind=kind,
            labels=labels,
            source=source,
            importance=importance,
            valid_from=now,
            created_at=now,
            vector=vector,
            expires_at=expires_at,
            supersedes=supersedes if isinstance(supersedes, str) else None,
        )

    @staticmethod
    def _source_from_metadata(metadata: dict[str, Any]) -> MemorySource:
        """Reconstruct the :class:`MemorySource` from a ledger row's metadata.

        A pre-v2 row (no ``source``) defaults to an experiential operator note.
        """
        raw_source = metadata.get(_META_SOURCE)
        if isinstance(raw_source, dict):
            try:
                return MemorySource.model_validate(raw_source)
            except ValidationError:
                pass
        return MemorySource(kind=_DEFAULT_SOURCE_KIND)

    # -- write helpers ------------------------------------------------------

    @staticmethod
    def _ledger_metadata(
        kind: str,
        importance: float,
        labels: list[str],
        source: MemorySource,
        expires_at: datetime | None,
        supersedes: str | None,
    ) -> dict[str, Any]:
        """The v2 wire fields stamped into the durable ledger row's JSON metadata."""
        return {
            _META_KIND: kind,
            _META_IMPORTANCE: importance,
            _META_LABELS: list(labels),
            _META_SOURCE: source.model_dump(),
            _META_EXPIRES_AT: expires_at.isoformat() if expires_at is not None else None,
            _META_SUPERSEDES: supersedes,
        }

    async def _embed_document(self, text: str, memory_id: str) -> list[float]:
        """Embed ``text`` document-side, raising on a permanent embed failure."""
        result = await self._embedder.embed_documents([text])
        vector = result.vectors[0]
        if vector is None:
            raise ValueError(f"the embedder permanently failed to embed memory {memory_id!r}")
        return vector

    def _resolve_importance(self, kind: str, importance: float | None) -> float:
        """Resolve + validate the importance (explicit override or by-kind default).

        Raises:
            ValueError: An explicit/resolved importance outside ``[0, 1]``.
        """
        resolved = importance if importance is not None else self._default_importance(kind)
        if not (_IMPORTANCE_FLOOR <= resolved <= _IMPORTANCE_CEILING):
            raise ValueError(
                f"importance {resolved} is outside the valid range "
                f"[{_IMPORTANCE_FLOOR}, {_IMPORTANCE_CEILING}]"
            )
        return resolved

    @staticmethod
    def _default_importance(kind: str) -> float:
        """The by-kind default importance, falling back to the plain-fact prior."""
        return IMPORTANCE_DEFAULTS_BY_KIND.get(kind, IMPORTANCE_DEFAULTS_BY_KIND[_DEFAULT_KIND])

    @staticmethod
    def _resolve_expiry(kind: str, expires_at: datetime | None, now: datetime) -> datetime | None:
        """Resolve the TTL deadline: explicit wins; an ``ongoing`` kind defaults it."""
        if expires_at is not None:
            return expires_at
        if kind == _ONGOING_KIND:
            return now + ONGOING_DEFAULT_TTL
        return None
