"""The local, SurrealDB-backed :class:`MemoryBackend` implementation.

:class:`LocalMemoryBackend` speaks the Spectron-derived, snake_case memory wire
vocabulary (:mod:`loremaster.memory.backend`) against a per-project SurrealDB
database. It:

* mints a deterministic ``uuid5`` memory id that is BACKWARD-COMPATIBLE with the
  v0.3 ledger convention (reusing :mod:`loremaster.memory.backend`'s
  ``derive_refs_stamp`` / ``derive_memory_id`` helpers, so a restore re-mints
  byte-identical ids);
* write-throughs the durable :class:`~loremaster.memory.ledger.MemoryLedger`
  row FIRST (FP-06), before the volatile SurrealDB write, so a Surreal failure
  never loses a memory;
* recalls via one-query HYBRID retrieval (HNSW vector ⊕ BM25 FULLTEXT fused by
  the engine's native ``search::rrf``), mirroring
  :class:`~loremaster.store.surreal.SurrealStore`'s inline-subquery shape;
* keeps a full temporal audit trail — supersession closes the old row
  (``valid_until`` + ``superseded_by``) inside ONE transaction with the new
  row's write; ``invalidate`` closes a row with no successor;
* reinforces a recalled memory's importance (a side effect visible on the NEXT
  recall, capped at ``1.0``), and drift-annotates each recalled ``lore_ref`` via
  the injected chunk-existence oracle (a FLAG, never a filter).

Connection lifecycle mirrors :class:`~loremaster.store.surreal.SurrealStore`: one
lazily-opened, signed-in WS connection, self-healed on a mid-life transport
failure (a dropped handle so the next call reconnects), reusing the shared
transaction / error-classification seams in :mod:`loremaster.store._txn` so a
transport fault surfaces as :class:`SurrealConnectionError` and a domain
rejection as :class:`SurrealStoreError` — never a raw engine string.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from loresigil.base import Embedder
from pydantic import ValidationError
from surrealdb import AsyncSurreal, RecordID

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
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    _SERVER_LOG_HINT,
    SurrealConnectionError,
    SurrealStoreError,
    TxnFragment,
    _classify_engine_error,
    _SurrealConnection,
    compose,
    execute_transaction,
    is_connection_error,
)
from loremaster.store.surreal_schema import (
    DEFAULT_ANALYZER_NAME,
    MEMORY_FULLTEXT_FIELDS,
    MEMORY_TABLE,
    generate_memory_ddl,
)

logger = logging.getLogger(__name__)

# Default cap on the number of memories a recall returns when the caller does
# not specify ``k`` (mirrors the legacy Qdrant-era memory store's default).
_DEFAULT_RECALL_K = 5

# The kind a memory defaults to when none is recorded — a pre-v2 ledger row (no
# ``kind`` in its metadata) replays as a plain ``fact`` (the plan-pinned default).
_DEFAULT_KIND = "fact"

# The ``kind`` that acquires the default TTL when saved without an explicit
# ``expires_at`` (see :data:`ONGOING_DEFAULT_TTL`).
_ONGOING_KIND = "ongoing"

# The ``MemorySource.kind`` a memory saved without an explicit source carries (an
# operator note), and the fallback for a pre-v2 ledger row lacking any source.
_DEFAULT_SOURCE_KIND = "operator"

# The inclusive importance bounds (a fraction). An explicit importance outside
# these is a caller error; the reinforcement bump is clamped to the ceiling.
_IMPORTANCE_FLOOR = 0.0
_IMPORTANCE_CEILING = 1.0

# The ``include`` value that lifts the live-only ``valid_until`` recall filter so
# retired/superseded rows also surface.
_INCLUDE_SUPERSEDED = "superseded"

# The flat ``lore_ref`` label form + its optional ``@version`` separator — the
# producer/consumer seam between a memory's ``labels`` and its versioned chunk
# refs (the id-folding stamp on write, the drift-annotated refs on read).
_LORE_REF_LABEL_PREFIX = "lore_ref="
_REF_VERSION_SEPARATOR = "@"

# The signin credential keys the SDK expects.
_SIGNIN_USER_KEY = "username"
_SIGNIN_PASS_KEY = "password"

# The ``memory`` table columns the backend reads/writes. Named once each so a
# rename is a single edit, never a hand-copied literal drifting between the write
# content, the recall filter and the row→value-object mapping.
_COL_NOTE_TEXT = "note_text"
_COL_KIND = "kind"
_COL_LABELS = "labels"
_COL_SOURCE = "source"
_COL_IMPORTANCE = "importance"
_COL_MEMORY_CATEGORY = "memory_category"
_COL_VALID_FROM = "valid_from"
_COL_VALID_UNTIL = "valid_until"
_COL_SUPERSEDES = "supersedes"
_COL_SUPERSEDED_BY = "superseded_by"
_COL_EXPIRES_AT = "expires_at"
_COL_CREATED_AT = "created_at"
_COL_EMBEDDING = "embedding"

# The durable-ledger metadata keys the write-through stamps so a future replay
# can restore the v2 wire fields (a pre-v2 row lacks them; the replay DEFAULTS
# fill in for those).
_META_KIND = "kind"
_META_IMPORTANCE = "importance"
_META_LABELS = "labels"
_META_SOURCE = "source"
_META_EXPIRES_AT = "expires_at"
_META_SUPERSEDES = "supersedes"

# SDK-added result keys and the record-id table separator.
_ID_KEY = "id"
_RRF_SCORE_KEY = "rrf_score"
_TABLE_SEPARATOR = ":"

# Hybrid-retrieval tuning — mirrors ``store.surreal``'s HNSW/RRF constants so the
# memory arm behaves like the chunk arm. Filtered KNN under-returns, so each arm
# overfetches ``k`` by :data:`_OVERFETCH_FACTOR` (bounded by :data:`_MAX_HNSW_EF`);
# EF (the HNSW search-list size) must cover the overfetch, floored at
# :data:`_MIN_HNSW_EF`; ``k`` itself is clamped (:data:`_MAX_HYBRID_K`) so an
# unclamped huge ``k`` can never overrun the engine's HNSW allocation.
_OVERFETCH_FACTOR = 4
_MIN_HNSW_EF = 64
_MAX_HNSW_EF = 1024
_MAX_HYBRID_K = 1000
# The textbook Reciprocal-Rank-Fusion smoothing constant.
_RRF_K = 60
# The query-text DoS guards (mirrors ``store.surreal``): the analyzed token list
# drives a per-token FULLTEXT OR-predicate, so both are capped before use.
_MAX_QUERY_TEXT_CHARS = 4096
_MAX_QUERY_TOKENS = 64

# The bound-parameter names/prefixes the backend uses. ``__``-prefixed read
# params can't collide with a caller value; the ``mem_`` write prefix namespaces
# the composed transaction's fragments so a supersede-close never clobbers the
# new row's params (see :func:`~loremaster.store._txn.compose`).
_QUERY_VECTOR_PARAM = "__qvec"
_AS_OF_PARAM = "__as_of"
_LABEL_PARAM_PREFIX = "__lbl"
_KIND_PARAM = "__kind"
_FULLTEXT_PARAM_PREFIX = "__ft"
_WRITE_PARAM_PREFIX = "mem_"

# A WHERE predicate that matches nothing — the fulltext arm when a query yields
# no word tokens, so the vector arm alone carries the fusion.
_NO_MATCH_PREDICATE = "false"


class LocalMemoryBackend:
    """The local :class:`~loremaster.memory.backend.MemoryBackend` over SurrealDB.

    Speaks the Spectron-derived, snake_case memory wire vocabulary
    (:mod:`loremaster.memory.backend`) against a per-project SurrealDB
    database, write-throughs to the durable :class:`MemoryLedger` (FP-06
    reuse), and drift-annotates recalled refs via an injected
    chunk-existence oracle.

    Args:
        url: The SurrealDB RPC URL.
        namespace: The SurrealDB namespace.
        database: The SurrealDB database (per-project).
        dim: The embedding width the memory table's vector index is sized for.
        user: The SurrealDB root/service username.
        password: The SurrealDB root/service password.
        embedder: The :class:`~loresigil.base.Embedder` used to embed note
            text (document side) and recall queries (query side).
        existing_chunks: An async ``chunk_keys -> set[str]`` BATCH oracle
            returning the subset of the passed keys that still exist; a recalled
            ref whose key is absent from that subset is flagged ``drifted=True``
            (never filtered out). ONE call resolves drift for a whole recall.
        ledger: The optional durable write-through
            :class:`~loremaster.memory.ledger.MemoryLedger` (the FP-06 source
            of truth a Surreal failure/wipe cannot touch).
    """

    def __init__(
        self,
        *,
        url: str,
        namespace: str,
        database: str,
        dim: int,
        user: str,
        password: str,
        embedder: Embedder,
        existing_chunks: ExistingChunksFn,
        ledger: MemoryLedger | None = None,
    ) -> None:
        """Store the backend's wiring. Does not open any connection yet.

        Args:
            url: The SurrealDB RPC URL.
            namespace: The SurrealDB namespace.
            database: The SurrealDB database (per-project).
            dim: The embedding width the memory table's vector index is sized for.
            user: The SurrealDB root/service username.
            password: The SurrealDB root/service password.
            embedder: The document/query embedder.
            existing_chunks: The async BATCH chunk-existence drift oracle.
            ledger: The optional durable write-through ledger.
        """
        self._url = url
        self._namespace = namespace
        self._database = database
        self._dim = dim
        self._user = user
        self._password = password
        self._embedder = embedder
        self._existing_chunks = existing_chunks
        self._ledger = ledger
        # The memory FULLTEXT index is built with this analyzer (see
        # ``generate_memory_ddl``); recall analyzes the query with the SAME one.
        self._analyzer_name = DEFAULT_ANALYZER_NAME
        # Opened on first use; ``None`` means "not yet connected / closed".
        self._connection: _SurrealConnection | None = None
        # Guards the connect-time check-then-set so N concurrent first-callers
        # never each open their own underlying SDK connection (mirrors
        # ``SurrealStore``'s double-checked lock).
        self._connect_lock = asyncio.Lock()

    @property
    def ledger(self) -> MemoryLedger | None:
        """The durable write-through ledger, or ``None`` when not configured."""
        return self._ledger

    # -- connection lifecycle ----------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking (mirrors :class:`SurrealStore`): the fast path
        never touches the lock; a first caller signs in, materialises the
        namespace/database idempotently and selects them. Any transport/auth
        failure is a LOUD, typed :class:`SurrealConnectionError` — never a hang
        or a silent empty result.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        if self._connection is not None:
            return self._connection
        async with self._connect_lock:
            if self._connection is not None:
                # A concurrent caller connected while this one waited; mypy can't
                # model the cross-coroutine mutation across the ``await`` above.
                return self._connection  # type: ignore[unreachable]
            connection = AsyncSurreal(self._url)
            credentials: dict[str, Any] = {
                _SIGNIN_USER_KEY: self._user,
                _SIGNIN_PASS_KEY: self._password,
            }
            try:
                await connection.signin(credentials)
                await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {self._namespace}")
                await connection.use(self._namespace, self._database)
                await connection.query(f"DEFINE DATABASE IF NOT EXISTS {self._database}")
            except _CONNECTION_ERRORS as error:
                # Close the half-open socket so a failed connect never leaks a
                # dangling connection, then surface a typed connection error.
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "memory.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect and apply the memory schema slice — idempotent and safe to re-run.

        Applies :func:`~loremaster.store.surreal_schema.generate_memory_ddl` (the
        analyzer + the ``memory`` table + its HNSW/FULLTEXT/valid_until indexes)
        inside ONE ``BEGIN … COMMIT`` via
        :func:`~loremaster.store._txn.execute_transaction`, which verifies EVERY
        statement's status (the SDK's plain ``query()`` inspects only the first).
        The DDL is ``IF NOT EXISTS`` / ``REMOVE FIELD IF EXISTS``, so a second
        call neither raises nor wipes data.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: A DDL statement was rejected by the engine.
        """
        await self._ensure_connection()
        ddl = generate_memory_ddl(dim=self._dim, analyzer_name=self._analyzer_name)
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("memory.schema.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any); tolerant of a never-connected backend."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal).

        A compare-and-swap (mirrors :class:`SurrealStore`): ``self._connection``
        is cleared only when ``connection`` is STILL the cached handle, so a late
        caller holding a stale reference can never wipe out a freshly-reconnected
        one. The handed connection is always closed regardless.
        """
        if self._connection is connection:
            self._connection = None
        await self._safe_close(connection)

    @staticmethod
    async def _safe_close(connection: _SurrealConnection) -> None:
        """Close ``connection``, swallowing an already-dead-socket failure."""
        try:
            await connection.close()
        except _CONNECTION_ERRORS:
            # The socket is already gone — nothing left to release.
            logger.debug("memory.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection, self-healing.

        Classifies a failure exactly as :class:`SurrealStore._query` does (via
        :func:`~loremaster.store._txn.is_connection_error`): a transport/socket/
        auth fault (or the SDK's ``KeyError`` response-routing race) drops the
        cached handle so the next call reconnects and surfaces a LOUD
        :class:`SurrealConnectionError`; a domain/schema rejection keeps the
        healthy connection and surfaces as
        :class:`~loremaster.store._txn.SurrealStoreError`. Never a silent empty
        result, never a raw engine string leaked to the caller.
        """
        connection = await self._ensure_connection()
        try:
            return await connection.query(statement, params or {})
        except (*_CONNECTION_ERRORS, KeyError) as error:
            if isinstance(error, KeyError) or is_connection_error(error):
                await self._drop_connection(connection)
                raise SurrealConnectionError(
                    f"SurrealDB memory query failed against {self._url!r}: {error}"
                ) from error
            # A domain/schema rejection — keep the healthy connection. Message
            # hygiene (ledger #31, mirroring ``execute_transaction``): the raw
            # engine text can echo a bound VALUE back verbatim (an ASSERT/coercion
            # rejection) and flows to MCP clients in P8, so the FULL detail is
            # logged server-side and the RAISED error carries only a CLASSIFIED,
            # generic label plus a "see the server log" hint, never the raw text.
            error_class = _classify_engine_error(error)
            logger.error(
                "memory.query.rejected",
                extra={"url": self._url, "error_class": error_class, "engine_error": str(error)},
            )
            raise SurrealStoreError(
                f"SurrealDB memory query rejected against {self._url!r} ({error_class}); "
                f"{_SERVER_LOG_HINT}"
            ) from error

    async def _apply(self, fragments: list[TxnFragment]) -> None:
        """Compose ``fragments`` into ONE transaction and run it atomically.

        Mirrors :meth:`SurrealStore.apply`: the composed ``BEGIN … COMMIT`` runs
        through :func:`~loremaster.store._txn.execute_transaction` (every
        statement's status verified, transport failure self-healed), so a
        supersede's new-row UPSERT and old-row close either both land or neither
        does — a concurrent reader never observes a half-applied supersession.
        """
        statement_text, merged_params = compose(*fragments)
        await execute_transaction(
            statement_text,
            merged_params,
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )

    # -- writes -------------------------------------------------------------

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

        Order (per the FP-06 durability + input-validation contract): validate
        ``importance`` and check ``supersedes`` existence BEFORE any write (a bad
        input never leaves a durable trace); write the durable LEDGER row FIRST
        (so a later Surreal failure loses nothing); embed document-side; then, in
        ONE transaction, UPSERT the new row and — when superseding — close the old
        row (``valid_until`` + ``superseded_by``).

        Args:
            text: The note text — the recallable content.
            kind: The memory's kind (fact/decision/gotcha/uncertainty/ongoing).
            importance: An explicit importance override in ``[0, 1]``; when
                omitted, defaults per
                :data:`~loremaster.memory.backend.IMPORTANCE_DEFAULTS_BY_KIND`.
            source: The memory's provenance; defaults when omitted.
            labels: Flat labels, including any ``lore_ref=<chunk_key>[@version]``
                labels that fold into the deterministic id and become ``refs``.
            supersedes: The id of an existing memory this note replaces.
            expires_at: An explicit TTL deadline; an ``ongoing`` memory without
                one gets :data:`ONGOING_DEFAULT_TTL` from creation.

        Returns:
            The deterministic ``uuid5`` memory id.

        Raises:
            ValueError: ``importance`` is outside ``[0, 1]``.
            MemoryNotFoundError: ``supersedes`` names an unknown memory id.
        """
        resolved_importance = self._resolve_importance(kind, importance)
        resolved_source = source if source is not None else MemorySource(kind=_DEFAULT_SOURCE_KIND)
        resolved_labels = list(labels or ())
        refs_stamp = derive_refs_stamp(self._refs_from_labels(resolved_labels))
        memory_id = derive_memory_id(text, refs_stamp)
        now = datetime.now(UTC)
        resolved_expires = self._resolve_expiry(kind, expires_at, now)

        # Unknown ``supersedes`` is a caller error raised BEFORE any write, so an
        # orphan successor never lands even in the durable ledger.
        if supersedes is not None and not await self._row_exists(supersedes):
            raise MemoryNotFoundError(
                f"cannot supersede unknown memory {supersedes!r}: no such memory exists"
            )

        # Durable write-through FIRST: the ledger row is the copy a Surreal
        # failure/wipe cannot touch, keyed on the deterministic id so a re-save
        # collapses to one row and a restore re-mints in place.
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

        vector = await self._embed_document(text, memory_id)
        content = self._build_content(
            text=text,
            kind=kind,
            labels=resolved_labels,
            source=resolved_source,
            importance=resolved_importance,
            now=now,
            expires_at=resolved_expires,
            supersedes=supersedes,
            vector=vector,
        )
        fragments = [self._upsert_fragment(memory_id, content)]
        if supersedes is not None:
            fragments.append(self._close_superseded_fragment(supersedes, memory_id, now))
        await self._apply(fragments)
        return memory_id

    async def invalidate(self, memory_id: str) -> None:
        """Retire a memory with no successor (``valid_until`` set, ``superseded_by`` None).

        Args:
            memory_id: The id of the memory to retire.

        Raises:
            MemoryNotFoundError: ``memory_id`` does not exist.
        """
        if not await self._row_exists(memory_id):
            raise MemoryNotFoundError(
                f"cannot invalidate unknown memory {memory_id!r}: no such memory exists"
            )
        await self._query(
            f"UPDATE type::record('{MEMORY_TABLE}', $id) SET {_COL_VALID_UNTIL} = $now",
            {"id": memory_id, "now": datetime.now(UTC)},
        )

    # -- reads --------------------------------------------------------------

    async def recall(
        self,
        query: str,
        *,
        k: int = _DEFAULT_RECALL_K,
        include: str | None = None,
        as_of: datetime | None = None,
        labels: list[str] | None = None,
        kind: str | None = None,
        lens: str | None = None,
    ) -> list[RecalledMemory]:
        """Embed ``query`` and return the nearest matching memories, reinforced.

        Live-only by default; ``include="superseded"`` lifts the ``valid_until``
        filter; ``as_of=T`` recalls a row whose ``[valid_from, valid_until)``
        window contains ``T``; ``labels`` is an ALL-semantics filter; ``kind``
        restricts to rows of that exact kind and composes with ``labels`` as an
        INTERSECTION (both must match). Retrieval is one-query HYBRID (HNSW ⊕
        BM25 via ``search::rrf``). The returned importance is PRE-bump; each
        returned memory's stored importance is then reinforced (visible on the
        NEXT recall). Each ref is drift-flagged via the injected oracle (a flag,
        never a filter).

        Args:
            query: The recall query text.
            k: The maximum number of memories to return.
            include: ``None`` (live-only) or ``"superseded"``.
            as_of: When set, recall as of this instant.
            labels: An ALL-semantics label filter.
            kind: When set, restrict to memories of this exact kind.
            lens: Unsupported by the local backend in P7.

        Returns:
            The matching memories, most similar first, capped at ``k``.

        Raises:
            ValueError: ``lens`` is supplied (unsupported in P7).
        """
        if lens is not None:
            raise ValueError(
                f"the local memory backend does not support a recall lens (got {lens!r}); "
                f"lens is unsupported in P7"
            )
        query_vector = await self._embedder.embed_query(query)
        filter_conditions, params = self._build_recall_filter(include, as_of, labels, kind)
        rows = await self._hybrid_search(query_vector, query, k, filter_conditions, params)
        # Resolve drift for EVERY recalled ref in ONE oracle call (the batch read),
        # then annotate each row's refs against that shared existing-chunk set —
        # never one existence fetch per ref.
        existing_chunks = await self._resolve_existing_chunks(rows)
        memories = [self._row_to_recalled(row, existing_chunks) for row in rows]
        await self._reinforce(memories)
        return memories

    async def restore_from_ledger(self) -> int:
        """Replay the durable ledger rows NOT already covered by the store.

        Membership is by deterministic id (mirrors the retired Qdrant-era
        backfill's skip pattern): a ledger row whose id the store already
        carries is skipped, so once the store
        covers the ledger a further restore is a pure no-op — 0 replays, ZERO
        document embeds (the boot-path divergence guard). A pre-v2 ledger row (no
        v2 metadata) replays with the plan-pinned defaults (``kind="fact"``,
        ``trust="experiential"``, live). Ids overwrite in place (no duplicates).

        Returns:
            The number of ledger rows actually replayed (``0`` when in sync, on an
            empty ledger, or when no ledger is configured).
        """
        if self._ledger is None:
            return 0
        records = self._ledger.all_records()
        if not records:
            # An empty ledger: nothing to replay and — crucially — nothing to
            # embed (the inert first-boot baseline the spy pins).
            return 0
        existing_ids = await self._existing_ids()
        replayed = 0
        for record in records:
            if record.memory_id in existing_ids:
                continue
            await self._replay_record(record)
            replayed += 1
        return replayed

    # -- hybrid retrieval ---------------------------------------------------

    async def _hybrid_search(
        self,
        query_vector: list[float],
        query_text: str,
        k: int,
        filter_conditions: list[str],
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """One-query hybrid retrieval over ``memory``: HNSW ⊕ BM25 fused by RRF.

        Mirrors :meth:`SurrealStore.hybrid_search`'s inline-subquery shape: each
        arm overfetches under the SAME ``filter_conditions`` (a ``LET``-bound
        ``search::rrf`` arg comes back ``None``, so the arms are spliced inline),
        and the engine's native ``search::rrf`` fuses them to ``k``. Returns the
        fused rows (embedding omitted) sorted best-first, deterministically.
        """
        k = min(k, _MAX_HYBRID_K)
        overfetch = min(max(k * _OVERFETCH_FACTOR, k), _MAX_HNSW_EF)
        ef = min(max(overfetch, _MIN_HNSW_EF), _MAX_HNSW_EF)

        params[_QUERY_VECTOR_PARAM] = query_vector
        # The KNN operator may not nest in an OR/NOT, so it is a top-level AND
        # term after the filter (whose expiry clause is itself an OR in parens).
        vector_conditions = [
            *filter_conditions,
            f"{_COL_EMBEDDING} <|{overfetch},{ef}|> ${_QUERY_VECTOR_PARAM}",
        ]
        vector_subquery = f"SELECT * FROM {MEMORY_TABLE} WHERE {' AND '.join(vector_conditions)}"

        tokens = await self._analyze_query(query_text[:_MAX_QUERY_TEXT_CHARS])
        predicate, fulltext_params = self._build_fulltext_predicate(tokens[:_MAX_QUERY_TOKENS])
        params.update(fulltext_params)
        fulltext_conditions = [*filter_conditions, predicate]
        fulltext_subquery = (
            f"SELECT * FROM {MEMORY_TABLE} WHERE {' AND '.join(fulltext_conditions)}"
        )

        statement = (
            f"SELECT * OMIT {_COL_EMBEDDING} FROM "
            f"search::rrf([({vector_subquery}), ({fulltext_subquery})], {int(k)}, {_RRF_K})"
        )
        rows = self._as_rows(await self._query(statement, params))
        # ``search::rrf`` leaves equal-scored rows in arbitrary order; impose a
        # stable best-first sort (score desc, then bare id) so ``recalled[0]`` is
        # the top hit and identical calls never shuffle.
        rows.sort(key=lambda row: (-self._row_score(row), self._bare_id(row.get(_ID_KEY))))
        return rows

    async def _analyze_query(self, query_text: str) -> list[str]:
        """Tokenize ``query_text`` with the engine's own analyzer (BM25-rescue step).

        Reuses the server-side analyzer that indexed ``note_text`` so the query
        tokens match how the text was tokenized; punctuation-only tokens (which
        the conjunctive ``@@`` would require and never find) are dropped, leaving
        the word tokens the BM25 arm ORs together.
        """
        raw: Any = await self._query(
            "RETURN search::analyze($analyzer, $text)",
            {"analyzer": self._analyzer_name, "text": query_text},
        )
        if not isinstance(raw, list):
            return []
        return [
            token
            for token in raw
            if isinstance(token, str) and any(character.isalnum() for character in token)
        ]

    @staticmethod
    def _build_fulltext_predicate(tokens: list[str]) -> tuple[str, dict[str, Any]]:
        """Build the CONJUNCTIVE FULLTEXT predicate (and its params) over word tokens.

        Each (deduplicated) query word token must match at least one FULLTEXT
        field (``@@``), and EVERY token must be present — so a memory is in the
        BM25 arm only if it contains all the query's meaningful words. With no
        word tokens the predicate matches nothing, leaving the vector arm to carry
        the fusion alone.

        Deliberate divergence from :meth:`SurrealStore._build_fulltext_predicate`'s
        OR arm: at the memory corpus's tiny scale, BM25 IDF is degenerate
        (``search::score`` returns 0 / negative for terms shared across the few
        rows), so an OR arm returns rows in arbitrary RECORD order and — since
        ``search::rrf`` ranks by subquery POSITION — would tie/invert the exact
        vector match (a token-sharing distractor could out-rank the note the query
        IS). The conjunctive arm makes the exact-text query's OWN note (which
        contains all its tokens) the dominant fulltext hit, so it wins the fusion
        cleanly, while the vector arm remains the primary semantic signal.
        """
        unique_tokens = list(dict.fromkeys(tokens))
        if not unique_tokens:
            return _NO_MATCH_PREDICATE, {}
        clauses: list[str] = []
        params: dict[str, Any] = {}
        for index, token in enumerate(unique_tokens):
            param = f"{_FULLTEXT_PARAM_PREFIX}{index}"
            params[param] = token
            # This token must appear in AT LEAST ONE fulltext field; the tokens are
            # then AND-combined below (every query word required).
            field_match = " OR ".join(f"{field} @@ ${param}" for field in MEMORY_FULLTEXT_FIELDS)
            clauses.append(f"({field_match})")
        return "(" + " AND ".join(clauses) + ")", params

    @staticmethod
    def _build_recall_filter(
        include: str | None,
        as_of: datetime | None,
        labels: list[str] | None,
        kind: str | None = None,
    ) -> tuple[list[str], dict[str, Any]]:
        """Build the recall WHERE conditions (shared by both hybrid arms) + params.

        Three temporal modes: ``as_of=T`` returns the window ``[valid_from,
        valid_until)`` containing ``T``; ``include="superseded"`` lifts the
        live-only ``valid_until`` filter (keeping the expiry gate); the default is
        live-only (``valid_until`` unset AND not past its expiry). An ALL-semantics
        ``labels`` filter (every requested label present) is appended in every
        mode, as is an exact ``kind`` filter when supplied -- ``kind`` and
        ``labels`` compose as an INTERSECTION (both conditions are ANDed into the
        same list). The condition list is never empty, so the arms always have a
        WHERE.
        """
        conditions: list[str] = []
        params: dict[str, Any] = {}
        if as_of is not None:
            params[_AS_OF_PARAM] = as_of
            conditions.append(f"{_COL_VALID_FROM} <= ${_AS_OF_PARAM}")
            conditions.append(
                f"({_COL_VALID_UNTIL} IS NONE OR {_COL_VALID_UNTIL} > ${_AS_OF_PARAM})"
            )
        else:
            if include != _INCLUDE_SUPERSEDED:
                conditions.append(f"{_COL_VALID_UNTIL} IS NONE")
            conditions.append(
                f"({_COL_EXPIRES_AT} IS NONE OR {_COL_EXPIRES_AT} > time::now())"
            )
        for index, label in enumerate(labels or ()):
            param = f"{_LABEL_PARAM_PREFIX}{index}"
            params[param] = label
            conditions.append(f"${param} IN {_COL_LABELS}")
        if kind is not None:
            params[_KIND_PARAM] = kind
            conditions.append(f"{_COL_KIND} = ${_KIND_PARAM}")
        return conditions, params

    async def _reinforce(self, memories: list[RecalledMemory]) -> None:
        """Bump each returned memory's STORED importance by the reinforcement step.

        A side effect visible on the NEXT recall (this call already returned the
        pre-bump value), persisted, and capped at :data:`_IMPORTANCE_CEILING`.

        The bump is computed SERVER-SIDE (``SET importance = math::min([$ceiling,
        importance + $step])``) rather than read-modify-written in Python: two
        concurrent recalls of the SAME memory would otherwise read the same base
        and write the same bumped value, silently losing one bump. Reading the
        stored ``importance`` inside the UPDATE makes each bump atomic; the
        ``math::min`` (a single-array form) still clamps at the ceiling.
        """
        for memory in memories:
            await self._query(
                f"UPDATE type::record('{MEMORY_TABLE}', $id) SET {_COL_IMPORTANCE} = "
                f"math::min([$ceiling, {_COL_IMPORTANCE} + $step])",
                {"id": memory.id, "ceiling": _IMPORTANCE_CEILING, "step": REINFORCEMENT_STEP},
            )

    def _row_to_recalled(
        self, row: dict[str, Any], existing_chunks: set[str]
    ) -> RecalledMemory:
        """Map a fused ``search::rrf`` row into a summarised :class:`RecalledMemory`.

        A FRESH value object (never the raw row): the stored ``labels`` are split
        into drift-annotated ``refs`` (the ``lore_ref=`` labels, drift decided by
        membership in ``existing_chunks`` — the subset the batch oracle already
        resolved for the whole recall) and the plain ``labels``, and ``source`` is
        re-validated back into a :class:`MemorySource`.
        """
        stored_labels = self._stored_labels(row)
        refs, plain_labels = self._split_labels(stored_labels, existing_chunks)
        return RecalledMemory(
            id=self._bare_id(row.get(_ID_KEY)),
            text=str(row.get(_COL_NOTE_TEXT, "")),
            score=self._row_score(row),
            kind=str(row.get(_COL_KIND, _DEFAULT_KIND)),
            importance=float(row.get(_COL_IMPORTANCE, _IMPORTANCE_FLOOR)),
            memory_category=row.get(_COL_MEMORY_CATEGORY),
            labels=plain_labels,
            refs=refs,
            source=self._source_from_value(row.get(_COL_SOURCE)),
            valid_from=self._row_datetime(row, _COL_VALID_FROM),
            valid_until=row.get(_COL_VALID_UNTIL),
            expires_at=row.get(_COL_EXPIRES_AT),
            created_at=self._row_datetime(row, _COL_CREATED_AT),
            supersedes=row.get(_COL_SUPERSEDES),
            superseded_by=row.get(_COL_SUPERSEDED_BY),
        )

    async def _resolve_existing_chunks(self, rows: list[dict[str, Any]]) -> set[str]:
        """Resolve drift for the WHOLE recall in ONE batch-oracle call.

        Collects the UNIQUE ``lore_ref`` chunk-keys across every recalled row and
        asks the injected batch oracle which of them still exist — a single
        existence query for N refs, never one point-fetch per ref. Returns the
        existing subset the per-row :meth:`_split_labels` annotation tests
        membership against. A recall carrying NO refs skips the oracle entirely
        (nothing to resolve, so no query is issued).

        Raises:
            SurrealConnectionError: The store is down — the batch query RAISES
                loudly rather than silently reporting every ref missing.
        """
        chunk_keys: set[str] = set()
        for row in rows:
            chunk_keys.update(self._ref_chunk_keys(self._stored_labels(row)))
        if not chunk_keys:
            return set()
        return await self._existing_chunks(sorted(chunk_keys))

    @staticmethod
    def _stored_labels(row: dict[str, Any]) -> list[str]:
        """The row's stored labels as plain strings (``lore_ref`` + plain alike)."""
        return [str(label) for label in (row.get(_COL_LABELS) or ())]

    @classmethod
    def _ref_chunk_keys(cls, labels: list[str]) -> list[str]:
        """The chunk-keys of a row's ``lore_ref`` labels (non-ref labels ignored)."""
        keys: list[str] = []
        for label in labels:
            parsed = cls._parse_lore_ref(label)
            if parsed is not None:
                keys.append(parsed[0])
        return keys

    def _split_labels(
        self, labels: list[str], existing_chunks: set[str]
    ) -> tuple[list[RecalledRef], list[str]]:
        """Split stored labels into drift-annotated refs + the plain labels.

        A ``lore_ref=`` label becomes a :class:`RecalledRef` whose ``drifted`` is
        decided by MEMBERSHIP in ``existing_chunks`` (the subset the batch oracle
        reported still exists for this recall) — a key absent from that set has
        drifted. Every other label stays a plain label. Drift is a FLAG, never a
        filter.
        """
        refs: list[RecalledRef] = []
        plain: list[str] = []
        for label in labels:
            parsed = self._parse_lore_ref(label)
            if parsed is None:
                plain.append(label)
                continue
            chunk_key, key_version = parsed
            drifted = chunk_key not in existing_chunks
            refs.append(RecalledRef(chunk_key=chunk_key, key_version=key_version, drifted=drifted))
        return refs, plain

    # -- ledger replay ------------------------------------------------------

    async def _existing_ids(self) -> set[str]:
        """Return the set of bare memory ids the store already carries (all rows)."""
        result = await self._query(f"SELECT VALUE record::id({_ID_KEY}) FROM {MEMORY_TABLE}")
        return {str(value) for value in self._as_list(result) if value is not None}

    async def _replay_record(self, record: MemoryRecord) -> None:
        """Re-embed one durable ledger row and upsert it under its deterministic id.

        Reconstructs the v2 wire fields from the ledger metadata, falling back to
        the plan-pinned defaults for a pre-v2 row (``kind="fact"``,
        ``trust="experiential"``, live). The id is the ledger's own
        ``memory_id``, so the upsert overwrites in place — a replay never
        duplicates.
        """
        metadata = record.metadata or {}
        kind = str(metadata.get(_META_KIND, _DEFAULT_KIND))
        raw_importance = metadata.get(_META_IMPORTANCE)
        importance = (
            float(raw_importance)
            if raw_importance is not None
            else self._default_importance(kind)
        )
        raw_labels = metadata.get(_META_LABELS)
        labels = (
            [str(label) for label in raw_labels]
            if isinstance(raw_labels, list)
            else self._labels_from_refs_stamp(record.refs_stamp)
        )
        source = self._source_from_metadata(metadata)
        expires_at = self._parse_iso(metadata.get(_META_EXPIRES_AT))
        supersedes = metadata.get(_META_SUPERSEDES)
        now = datetime.now(UTC)
        vector = await self._embed_document(record.text, record.memory_id)
        content = self._build_content(
            text=record.text,
            kind=kind,
            labels=labels,
            source=source,
            importance=importance,
            now=now,
            expires_at=expires_at,
            supersedes=supersedes if isinstance(supersedes, str) else None,
            vector=vector,
        )
        await self._apply([self._upsert_fragment(record.memory_id, content)])

    # -- write helpers ------------------------------------------------------

    def _ledger_metadata(
        self,
        kind: str,
        importance: float,
        labels: list[str],
        source: MemorySource,
        expires_at: datetime | None,
        supersedes: str | None,
    ) -> dict[str, Any]:
        """The v2 wire fields stamped into the durable ledger row's JSON metadata.

        Carried so a future replay can restore the row faithfully; a pre-v2 row
        lacks these and the replay DEFAULTS fill in. Every value is JSON-safe
        (datetimes as ISO strings) since the ledger serialises via ``json.dumps``.
        """
        return {
            _META_KIND: kind,
            _META_IMPORTANCE: importance,
            _META_LABELS: list(labels),
            _META_SOURCE: source.model_dump(),
            _META_EXPIRES_AT: expires_at.isoformat() if expires_at is not None else None,
            _META_SUPERSEDES: supersedes,
        }

    @staticmethod
    def _build_content(
        *,
        text: str,
        kind: str,
        labels: list[str],
        source: MemorySource,
        importance: float,
        now: datetime,
        expires_at: datetime | None,
        supersedes: str | None,
        vector: list[float],
    ) -> dict[str, Any]:
        """Shape the ``memory`` row content for an UPSERT (save + replay share this).

        Sets every REQUIRED column; the option columns not set here
        (``valid_until``/``superseded_by``/``memory_category``) default to
        ``NONE`` (a live, un-categorised row). ``valid_from`` == ``created_at`` ==
        ``now`` so a fresh row's temporal window opens at its creation instant.
        """
        content: dict[str, Any] = {
            _COL_NOTE_TEXT: text,
            _COL_KIND: kind,
            _COL_LABELS: list(labels),
            _COL_SOURCE: source.model_dump(),
            _COL_IMPORTANCE: importance,
            _COL_VALID_FROM: now,
            _COL_CREATED_AT: now,
            _COL_EMBEDDING: vector,
        }
        if expires_at is not None:
            content[_COL_EXPIRES_AT] = expires_at
        if supersedes is not None:
            content[_COL_SUPERSEDES] = supersedes
        return content

    @staticmethod
    def _upsert_fragment(memory_id: str, content: dict[str, Any]) -> TxnFragment:
        """The UPSERT fragment for one memory row, keyed on its deterministic id."""
        id_param = f"{_WRITE_PARAM_PREFIX}id"
        content_param = f"{_WRITE_PARAM_PREFIX}content"
        return TxnFragment(
            statements=[
                f"UPSERT type::record('{MEMORY_TABLE}', ${id_param}) CONTENT ${content_param}"
            ],
            params={id_param: memory_id, content_param: content},
        )

    @staticmethod
    def _close_superseded_fragment(old_id: str, new_id: str, now: datetime) -> TxnFragment:
        """The fragment that closes the superseded row (audit trail preserved).

        Stamps ``valid_until=now`` + ``superseded_by=<new id>`` on the old row; it
        is KEPT (never deleted) so ``include="superseded"`` / ``as_of`` can still
        surface it. Distinct param names from :meth:`_upsert_fragment` so the two
        compose without a collision.
        """
        old_param = f"{_WRITE_PARAM_PREFIX}old_id"
        now_param = f"{_WRITE_PARAM_PREFIX}now"
        by_param = f"{_WRITE_PARAM_PREFIX}superseded_by"
        return TxnFragment(
            statements=[
                f"UPDATE type::record('{MEMORY_TABLE}', ${old_param}) "
                f"SET {_COL_VALID_UNTIL} = ${now_param}, {_COL_SUPERSEDED_BY} = ${by_param}"
            ],
            params={old_param: old_id, now_param: now, by_param: new_id},
        )

    async def _embed_document(self, text: str, memory_id: str) -> list[float]:
        """Embed ``text`` document-side, raising on a permanent embed failure."""
        result = await self._embedder.embed_documents([text])
        vector = result.vectors[0]
        if vector is None:
            raise ValueError(f"the embedder permanently failed to embed memory {memory_id!r}")
        return vector

    async def _row_exists(self, memory_id: str) -> bool:
        """Whether a memory row with ``memory_id`` exists (any validity state)."""
        result = await self._query(
            f"SELECT VALUE {_ID_KEY} FROM type::record('{MEMORY_TABLE}', $id)",
            {"id": memory_id},
        )
        return any(value is not None for value in self._as_list(result))

    def _resolve_importance(self, kind: str, importance: float | None) -> float:
        """Resolve + validate the importance (explicit override or by-kind default).

        Raises:
            ValueError: An explicit/resolved importance outside ``[0, 1]`` (a
                caller error — server-side input validation).
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
        return IMPORTANCE_DEFAULTS_BY_KIND.get(
            kind, IMPORTANCE_DEFAULTS_BY_KIND[_DEFAULT_KIND]
        )

    @staticmethod
    def _resolve_expiry(
        kind: str, expires_at: datetime | None, now: datetime
    ) -> datetime | None:
        """Resolve the TTL deadline: explicit wins; an ``ongoing`` kind defaults it."""
        if expires_at is not None:
            return expires_at
        if kind == _ONGOING_KIND:
            return now + ONGOING_DEFAULT_TTL
        return None

    @classmethod
    def _refs_from_labels(cls, labels: list[str]) -> list[MemoryRef]:
        """The versioned :class:`MemoryRef`\\ s a memory's ``lore_ref`` labels fold into.

        Only ``lore_ref=`` labels contribute (non-ref labels never affect the id);
        the resulting refs feed
        :func:`~loremaster.memory.backend.derive_refs_stamp`, reproducing the v0.3
        deterministic-id derivation EXACTLY (backward compat with the ledger).
        """
        refs: list[MemoryRef] = []
        for label in labels:
            parsed = cls._parse_lore_ref(label)
            if parsed is not None:
                chunk_key, key_version = parsed
                refs.append(MemoryRef(chunk_key=chunk_key, key_version=key_version))
        return refs

    @classmethod
    def _labels_from_refs_stamp(cls, refs_stamp: str) -> list[str]:
        """Reconstruct ``lore_ref=`` labels from a ledger row's refs stamp (replay)."""
        return [
            cls._lore_ref_label(ref.chunk_key, ref.key_version)
            for ref in refs_from_stamp(refs_stamp)
        ]

    @staticmethod
    def _lore_ref_label(chunk_key: str, key_version: int) -> str:
        """Build the flat ``lore_ref=<chunk_key>@<version>`` label a memory carries."""
        return f"{_LORE_REF_LABEL_PREFIX}{chunk_key}{_REF_VERSION_SEPARATOR}{key_version}"

    @staticmethod
    def _parse_lore_ref(label: str) -> tuple[str, int] | None:
        """Parse a ``lore_ref=<chunk_key>[@version]`` label into ``(chunk_key, version)``.

        A bare label defaults its version to
        :data:`~loremaster.extension.DEFAULT_KEY_VERSION`; a versioned one carries
        that version. Returns ``None`` for a non-``lore_ref`` label (plain
        metadata, never a chunk ref).
        """
        if not label.startswith(_LORE_REF_LABEL_PREFIX):
            return None
        body = label[len(_LORE_REF_LABEL_PREFIX) :]
        chunk_key, separator, version = body.rpartition(_REF_VERSION_SEPARATOR)
        if separator and version.isdigit():
            return chunk_key, int(version)
        return body, DEFAULT_KEY_VERSION

    @classmethod
    def _source_from_metadata(cls, metadata: dict[str, Any]) -> MemorySource:
        """Reconstruct the :class:`MemorySource` from a ledger row's metadata.

        A pre-v2 row (no ``source``) defaults to an experiential operator note —
        the plan-pinned ``trust="experiential"`` default.
        """
        return cls._source_from_value(metadata.get(_META_SOURCE))

    @staticmethod
    def _source_from_value(value: Any) -> MemorySource:
        """Validate a stored ``source`` object into a :class:`MemorySource` (or default)."""
        if isinstance(value, dict):
            try:
                return MemorySource.model_validate(value)
            except ValidationError:
                # A malformed stored source falls back to the experiential default
                # rather than crashing recall — the row is still recallable.
                logger.warning("memory.source.malformed", extra={"source": value})
        return MemorySource(kind=_DEFAULT_SOURCE_KIND)

    @staticmethod
    def _parse_iso(value: Any) -> datetime | None:
        """Parse an ISO-8601 datetime string (or ``None``) back into a datetime."""
        if not isinstance(value, str):
            return None
        return datetime.fromisoformat(value)

    # -- result narrowing ---------------------------------------------------

    @staticmethod
    def _as_rows(result: Any) -> list[dict[str, Any]]:
        """Narrow a ``SELECT`` result to its list of dict rows."""
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    @staticmethod
    def _as_list(result: Any) -> list[Any]:
        """Narrow a ``SELECT VALUE`` result to a plain list."""
        return list(result) if isinstance(result, list) else []

    @staticmethod
    def _row_score(row: dict[str, Any]) -> float:
        """The fused RRF score of a recalled row (``0.0`` when absent)."""
        return float(row.get(_RRF_SCORE_KEY, 0.0))

    @staticmethod
    def _row_datetime(row: dict[str, Any], key: str) -> datetime:
        """Read a REQUIRED datetime column, refusing a corrupt/missing value loudly.

        ``valid_from`` / ``created_at`` are non-``option`` schema columns the
        backend always sets, so a faithful row always carries a real datetime; a
        missing/wrong-typed one is a corrupt row, refused rather than silently
        coerced (and it satisfies :class:`RecalledMemory`'s non-optional datetime).
        """
        value = row.get(key)
        if not isinstance(value, datetime):
            raise SurrealStoreError(
                f"memory row column {key!r} is not a datetime (got {type(value).__name__})"
            )
        return value

    @staticmethod
    def _bare_id(raw: Any) -> str:
        """Return the BARE memory id — no ``memory:`` record-table prefix."""
        if isinstance(raw, RecordID):
            return str(raw.id)
        text = str(raw)
        if _TABLE_SEPARATOR in text:
            return text.split(_TABLE_SEPARATOR, 1)[1]
        return text
