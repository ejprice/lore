"""The P7 ``MemoryBackend`` wire vocabulary + protocol over SurrealDB.

This module replaces the Qdrant-only :mod:`loremaster.memory.store` payload
shapes with the Spectron-derived, snake_case memory wire vocabulary the local
SurrealDB-backed implementation (:mod:`loremaster.memory.local`) speaks:

* :class:`MemorySource` — the provenance of a memory note (``kind``/``ref``/
  ``trust``). ``trust`` is a two-value **enum**
  (``"authoritative"``/``"experiential"``), NOT the P2 schema's float trust
  column — that was wrong, and a float or an out-of-vocabulary string is
  rejected.
* :class:`RecalledRef` / :class:`RecalledMemory` — the summarised recall value
  objects a backend returns (never a raw SurrealDB row).
* :class:`MemoryNotFoundError` — the typed not-found raised by
  ``invalidate(<unknown id>)`` and ``remember(supersedes=<unknown id>)``.
* :data:`IMPORTANCE_DEFAULTS_BY_KIND` / :data:`ONGOING_DEFAULT_TTL` /
  :data:`REINFORCEMENT_STEP` — the plan-pinned defaults every backend honours.
* :class:`MemoryBackend` — the structural protocol every memory backend
  implementation (local SurrealDB today, a future ``FakeMemoryBackend`` /
  Spectron-backed implementation later) satisfies.

STUB PHASE: the value objects carry real field shapes + validation (they have
no behaviour to defer — pydantic model construction IS the contract), but
:class:`MemoryBackend` is a pure structural protocol with no implementation of
its own. See :mod:`loremaster.memory.local` for the (stub) local
implementation.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from loremaster.memory.ledger import MemoryLedger

# --- Plan-pinned constants (P7 requirement, NOT tunable at call sites) ------

#: Default importance (a fraction in ``[0, 1]``) applied to a ``remember``ed
#: memory when the caller supplies no explicit ``importance``, keyed by the
#: memory's ``kind``.
IMPORTANCE_DEFAULTS_BY_KIND: dict[str, float] = {
    "decision": 0.9,
    "gotcha": 0.8,
    "ongoing": 0.7,
    "uncertainty": 0.6,
    "fact": 0.5,
}

#: Default time-to-live applied to an ``ongoing`` memory saved without an
#: explicit ``expires_at`` (relative to its ``created_at``).
ONGOING_DEFAULT_TTL: timedelta = timedelta(days=7)

#: The reinforcement bump applied to a recalled memory's stored ``importance``
#: (visible on the NEXT recall, capped at ``1.0``).
REINFORCEMENT_STEP: float = 0.05

# The two-value trust vocabulary. A stored memory is either sourced from an
# authoritative document/spec or from experiential (operator-note) provenance;
# the P2 schema's float trust SCORE was the wrong shape and is being migrated.
TrustLevel = Literal["authoritative", "experiential"]

#: The default ``trust`` a :class:`MemorySource` carries when not specified.
DEFAULT_TRUST: TrustLevel = "experiential"

#: The async chunk-existence oracle a backend is constructed with — the drift
#: input for :class:`RecalledRef.drifted`. ``True`` means the referenced chunk
#: still exists in the code index.
ChunkExistsFn = Callable[[str], Awaitable[bool]]


class MemorySource(BaseModel):
    """The provenance of a memory note.

    Attributes:
        kind: A free-form provenance category (e.g. ``"operator"``,
            ``"spec"``) — NOT the memory's own kind (fact/decision/…).
        ref: An optional pointer into the provenance (e.g. a doc anchor or a
            chat transcript reference). ``None`` when the source carries no
            such pointer.
        trust: The two-value trust enum. Defaults to ``"experiential"``
            (an operator note) unless explicitly marked ``"authoritative"``.
            Rejects a float or any string outside the vocabulary — the P2
            schema's float trust column was wrong and is being migrated away
            from.
    """

    model_config = ConfigDict(extra="forbid")

    kind: str
    ref: str | None = None
    trust: TrustLevel = DEFAULT_TRUST


class RecalledRef(BaseModel):
    """A recalled memory's reference to an indexed chunk, drift-annotated.

    Attributes:
        chunk_key: The semantic chunk-key this memory references (the same
            point-id shape production indexing mints).
        key_version: The keying-scheme version the ``chunk_key`` was minted
            under (the shared :data:`~loremaster.extension.DEFAULT_KEY_VERSION`
            when the originating label carried no explicit version).
        drifted: ``True`` when the injected chunk-existence oracle reports the
            referenced chunk no longer exists (a refactor deleted it). Drift is
            a FLAG, never a filter — the memory is still recalled.
    """

    model_config = ConfigDict(extra="forbid")

    chunk_key: str
    key_version: int
    drifted: bool


class RecalledMemory(BaseModel):
    """A summarised recalled memory — never a raw SurrealDB row.

    Attributes:
        id: The memory's deterministic ``uuid5`` id.
        text: The note text — the recallable content.
        score: The similarity score of this memory against the recall query.
        kind: The memory's own kind (one of the memory-kind vocabulary:
            ``fact``/``decision``/``gotcha``/``uncertainty``/``ongoing``).
        importance: The memory's current importance, a fraction in ``[0, 1]``
            (kind default, caller override, or the reinforced value).
        memory_category: An optional secondary categorisation tag, reserved
            for a later wave (unused by the P7 behavioural surface).
        labels: The memory's flat ``key=value`` / bare labels, EXCLUDING the
            ``lore_ref=`` labels that were promoted into ``refs``.
        refs: The memory's versioned, drift-annotated chunk references.
        source: The memory's provenance (:class:`MemorySource`).
        valid_from: When this row became live.
        valid_until: When this row stopped being live (``None`` while live).
        expires_at: The row's TTL deadline (``None`` when it never expires).
        created_at: When this row was first written.
        supersedes: The id of the memory this row replaced, if any.
        superseded_by: The id of the memory that replaced this row, if any.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    score: float
    kind: str
    importance: float
    memory_category: str | None = None
    labels: list[str] = Field(default_factory=list)
    refs: list[RecalledRef] = Field(default_factory=list)
    source: MemorySource
    valid_from: datetime
    valid_until: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime
    supersedes: str | None = None
    superseded_by: str | None = None


class MemoryNotFoundError(Exception):
    """Raised when a referenced memory id does not exist.

    Surfaced by ``invalidate(<unknown id>)`` and by
    ``remember(supersedes=<unknown id>)`` — a caller-error case (server-side
    input validation), never a silent no-op.
    """


@runtime_checkable
class MemoryBackend(Protocol):
    """The structural contract every memory backend implementation satisfies.

    Both the local SurrealDB-backed implementation
    (:class:`~loremaster.memory.local.LocalMemoryBackend`) and any later
    fake/Spectron-backed implementation conform to this async surface, so
    callers (and a parametrised test suite) can depend on the protocol rather
    than a concrete class.
    """

    @property
    def ledger(self) -> MemoryLedger | None:
        """The durable write-through ledger, or ``None`` when not configured."""
        ...

    async def ensure_ready(self) -> None:
        """Prepare the backend's underlying storage for use (idempotent)."""
        ...

    async def close(self) -> None:
        """Release the backend's underlying connection(s), tolerating a
        never-connected backend."""
        ...

    async def remember(
        self,
        text: str,
        *,
        kind: str,
        importance: float | None = None,
        source: MemorySource | None = None,
        labels: list[str] | None = None,
        supersedes: str | None = None,
        expires_at: datetime | None = None,
    ) -> str:
        """Persist a memory note and return its deterministic id.

        Args:
            text: The note text — the recallable content.
            kind: The memory's kind (fact/decision/gotcha/uncertainty/ongoing).
            importance: An explicit importance override in ``[0, 1]``; when
                omitted, defaults per :data:`IMPORTANCE_DEFAULTS_BY_KIND`.
            source: The memory's provenance; defaults when omitted.
            labels: Flat labels, including any ``lore_ref=<chunk_key>[@version]``
                labels that fold into the deterministic id and become ``refs``.
            supersedes: The id of an existing memory this note replaces (the
                old row is kept for audit, closed, and wired forward).
            expires_at: An explicit TTL deadline; an ``ongoing`` memory without
                one gets :data:`ONGOING_DEFAULT_TTL` from creation.

        Returns:
            The deterministic ``uuid5`` memory id.

        Raises:
            ValueError: ``importance`` is outside ``[0, 1]``.
            MemoryNotFoundError: ``supersedes`` names an unknown memory id.
        """
        ...

    async def invalidate(self, memory_id: str) -> None:
        """Retire a memory with no successor.

        Args:
            memory_id: The id of the memory to retire.

        Raises:
            MemoryNotFoundError: ``memory_id`` does not exist.
        """
        ...

    async def recall(
        self,
        query: str,
        *,
        k: int = 5,
        include: str | None = None,
        as_of: datetime | None = None,
        labels: list[str] | None = None,
        lens: str | None = None,
    ) -> list[RecalledMemory]:
        """Embed ``query`` and return the nearest matching memories.

        Args:
            query: The recall query text.
            k: The maximum number of memories to return.
            include: ``None`` (live-only, the default) or ``"superseded"`` to
                also surface retired/superseded rows.
            as_of: When set, recall as of this instant (a row whose
                ``[valid_from, valid_until)`` window contains it is returned
                even if it is no longer live now).
            labels: An ALL-semantics label filter (every requested label must
                be present on a row for it to match).
            lens: Unsupported by the local backend in P7.

        Returns:
            The matching memories, most similar first, capped at ``k``. Each
            returned memory's stored importance is reinforced by
            :data:`REINFORCEMENT_STEP` (visible on the NEXT recall), and each
            ref is drift-flagged via the injected chunk-existence oracle.

        Raises:
            ValueError: ``lens`` is supplied (unsupported in P7).
        """
        ...

    async def restore_from_ledger(self) -> int:
        """Replay every durable ledger row into the backend, idempotently.

        Rows lacking v2 wire metadata (pre-v2 ledger rows) default to
        ``kind="fact"``, ``trust="experiential"``, live (``valid_until=None``).

        Returns:
            The number of ledger rows replayed.
        """
        ...
