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
from typing import TYPE_CHECKING, Any

from loresigil.base import Embedder
from pydantic import SecretStr, ValidationError
from surrealdb import AsyncSurreal, RecordID

from loremaster import governed
from loremaster.audit import AuditStore
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
    StoreHandle,
    SurrealConnectionError,
    SurrealStoreError,
    TxnContentionExhaustedError,
    TxnFragment,
    _SurrealConnection,
    bootstrap_session,
    compose,
    execute_transaction,
    run_query,
    signin_credentials,
)

# The shared hybrid-search lexical-arm bounding mechanism (finding #69): this
# module used to carry its OWN independent copy of finding #66/#67's
# constants (``_MAX_QUERY_TEXT_CHARS`` / a hardcoded ``_MAX_QUERY_TOKENS``) —
# exactly the "copy-paste twin" pattern that let this defect class recur. See
# :mod:`loremaster.store.query_text` for the measured rationale.
# ``truncate_at_word_boundary`` is explicitly re-exported (see ``__all__``
# below — the redundant ``as X`` alias mypy's ``no_implicit_reexport`` also
# accepts is a lint smell under this repo's ruff config, PLC0414): the
# sharing pin (``test_query_text.py::TestSharedMechanismPin``) asserts THIS
# module's attribute IS the shared function, not a hand-copied twin.
from loremaster.store.query_text import (
    MAX_FULLTEXT_OR_CLAUSES,
    max_query_tokens,
    truncate_at_word_boundary,
)
from loremaster.store.surreal_schema import (
    AGENT_TABLE,
    DEFAULT_ANALYZER_NAME,
    KEEP_TABLE,
    MEMORY_FULLTEXT_FIELDS,
    MEMORY_TABLE,
    PRINCIPAL_TABLE,
    generate_memory_ddl,
)

# packet 63a governed retrofit: the shared substrate seams (read_filter / guarded_write) + the
# scope-grant predicate. ``pdp`` is imported as a MODULE so a ``_grantable`` monkeypatch on
# ``lorerunes.pdp._grantable`` lands at the call site (the mutation-proof of the scope validation —
# a ``from … import _grantable`` binding would NOT see the patch; ROUTING-IS-NOT-SHARING).
from lorerunes import pdp

if TYPE_CHECKING:  # pragma: no cover - typing only
    from lorerunes.pdp import Subject

logger = logging.getLogger(__name__)

# The public surface. ``truncate_at_word_boundary`` is imported (not defined)
# here, so naming it EXPLICITLY marks it as a re-export for mypy-strict
# (``no_implicit_reexport``) — the sharing pin
# (``test_query_text.py::TestSharedMechanismPin``) accesses it as
# ``loremaster.memory.local.truncate_at_word_boundary`` from another module.
__all__ = ["LocalMemoryBackend", "truncate_at_word_boundary"]

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

# (The signin credential keys moved to the ONE shared
# ``store._txn.signin_credentials`` seam — #211/#102.)

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
# packet 63a GOVERNED columns (design §4.1): the owner pair (record<> links) + the scope string.
_COL_OWNER_PRINCIPAL = "owner_principal"
_COL_OWNER_AGENT = "owner_agent"
_COL_SCOPE = "scope"
# The canonical PROJECT-keep natural key is ONE shared constant (``governed.PROJECT_KEEP_KEY``) so
# ``remember``'s default-scope read and the migration mint address the SAME keep (design §2.2).

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

# The lexical arm's OWN query-text guards (finding #69, mirroring finding
# #66/#67's fix in ``store.surreal``) — distinct from the k/EF DoS guards
# above. This module used to hand-copy ``store.surreal``'s OLD, pre-fix
# constants (``_MAX_QUERY_TEXT_CHARS=4096`` / ``_MAX_QUERY_TOKENS=64``,
# verbatim, with a comment saying "mirrors store.surreal") — the copy-paste
# seam that let the SAME class of defect recur independently of whichever fix
# landed on the chunk-store side first. Fixed by SHARING the mechanism
# (:mod:`loremaster.store.query_text`) instead of hand-maintaining a third
# copy: :data:`_MAX_QUERY_TOKENS` is DERIVED from the shared clause budget and
# THIS consumer's OWN fulltext-field count (:data:`MEMORY_FULLTEXT_FIELDS`,
# currently 1 field) — self-correcting if that field count ever changes,
# rather than a hardcoded number that can silently drift unsafe.
#
# Live-measured end-to-end through THIS module's OWN predicate shape
# (``scratchpad/probe_long_query_69.py``, against spike-surreal, never
# production) — NOT the chunk store's 39-token/117-clause boundary, because
# this module's ``_build_fulltext_predicate`` is a DIFFERENT shape (a
# CONJUNCTIVE AND-chain over 1 fulltext field, not the chunk store's
# disjunctive OR-chain over 3): the engine ACCEPTS 114 analyzed
# tokens/AND-clauses and is REJECTED at 115. ``_MAX_FULLTEXT_OR_CLAUSES``
# (imported from the shared module) is the SAME clause budget the chunk store
# derives its own cap from — roughly HALF the smaller of the two
# independently-measured safe ceilings (114 here, 117 there) — so
# :data:`_MAX_QUERY_TOKENS` below (60, at today's 1-field width) sits with
# generous margin under BOTH measured boundaries.
#
# ``_MAX_LEXICAL_QUERY_CHARS`` is a WORD-BOUNDARY text pre-truncation (never
# splits a word — see :func:`~loremaster.store.query_text.truncate_at_word_boundary`)
# applied before the ``search::analyze`` round-trip: a PERFORMANCE bound on
# that round-trip (never send an unbounded amount of text just to discard
# most of the resulting tokens), not the safety guarantee — the token clamp
# above is what actually protects correctness. Sized independently of
# ``store.surreal``'s own 300-char bound (which is tuned for that store's
# smaller 20-token cap): 900 chars comfortably covers this module's larger
# 60-token cap at ordinary English word lengths, with headroom. The VECTOR
# arm never sees either of these caps — it embeds the caller's full,
# untruncated query text upstream of :meth:`LocalMemoryBackend._hybrid_search`.
_MAX_FULLTEXT_OR_CLAUSES = MAX_FULLTEXT_OR_CLAUSES
_MAX_QUERY_TOKENS = max_query_tokens(len(MEMORY_FULLTEXT_FIELDS))
_MAX_LEXICAL_QUERY_CHARS = 900

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
        password: SecretStr,
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
        # Serialises the memory-table RECREATE against the MCP write/read path.
        # :meth:`rebuild_embeddings` holds it for the ENTIRE drop→DDL→ledger-restore
        # span, and :meth:`remember` / :meth:`recall` / :meth:`invalidate` take the
        # SAME lock around their store-touching section, so a write can never land in
        # the brief ``REMOVE TABLE`` → ``ensure_ready`` window (which would auto-create
        # ``memory`` SCHEMALESS and both fail-loud the recreate AND brick recall until
        # the process restarts). Distinct from ``_connect_lock`` and NOT re-entrant, so
        # every LOCKED public method calls only UNLOCKED internals — ``ensure_ready`` /
        # ``restore_from_ledger`` / ``_recreate_memory_table`` never re-take it (they
        # run either at boot with no serving concurrency, or already under this lock).
        self._rebuild_lock = asyncio.Lock()

    @property
    def ledger(self) -> MemoryLedger | None:
        """The durable write-through ledger, or ``None`` when not configured."""
        return self._ledger

    # -- connection lifecycle ----------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking (mirrors :class:`SurrealStore`): the fast path
        never touches the lock. The session bootstrap is
        :func:`~loremaster.store._txn.bootstrap_session` — the ONE shared
        implementation every connection owner in the package calls
        (blindreader F3; see its docstring for the mechanism). This method's
        own job is DISPOSITION: any bootstrap failure — a transport/auth fault
        OR exhausted contention alike — is wrapped as
        :class:`SurrealConnectionError` after closing the half-open socket
        (the F4 ruling: the connection never became usable, whatever the
        reason). ``bootstrap_session`` itself never performs this wrap
        (adversary P-1): scout's reconnect ladder needs the RAW exhaustion
        type, so the wrap lives here, at the seam, not in the shared helper.

        Raises:
            SurrealConnectionError: The server is unreachable, rejected auth,
                or the session bootstrap exhausted its retry budget.
        """
        if self._connection is not None:
            return self._connection
        async with self._connect_lock:
            if self._connection is not None:
                # A concurrent caller connected while this one waited; mypy can't
                # model the cross-coroutine mutation across the ``await`` above.
                return self._connection  # type: ignore[unreachable]
            connection = AsyncSurreal(self._url)
            credentials = signin_credentials(
                user=self._user, password=self._password
            )
            try:
                await connection.signin(credentials)
                await bootstrap_session(connection, self._namespace, self._database, url=self._url)
            except TxnContentionExhaustedError as error:
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): "
                    f"the session bootstrap exhausted its retry budget"
                ) from error
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
        # F5 (design §5.1 Q1 / §1.9 item 4): the boot/rebuild memory DDL apply is a SCHEMA mutation
        # of a governed population — run it inside ``governed.write_guard`` so the F5 runtime seam
        # attributes the schema delta to this frame (an unlabelled DDL apply is UNCLASSIFIED —
        # deny-by-default; and every backend fixture calls ensure_ready on a virgin DB, so the DDL
        # leg is non-satisfiable on any fixture until the boot apply is classified). Its effect
        # predicate is the after-schema == the CONSTRUCTED oracle (``generate_memory_ddl`` on a
        # virgin DB, engine-rendered — dict equality, no regex), no rows moved.
        with governed.write_guard("ensure_ready"):
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

        Delegates to :func:`~loremaster.store._txn.run_query` — the ONE shared
        attempt body every single-statement seam in the package now calls
        (blindreader F3; see its docstring for the classify/self-heal/log
        mechanism, including its RETRYABLE-conflict path, finding #120/#108).
        """
        return await run_query(
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
            noun="memory query",
            label="memory.query.rejected",
            statement=statement,
            params=params or {},
            logger=logger,
        )

    @property
    def handle(self) -> StoreHandle:
        """The connection-owner :class:`~loremaster.store._txn.StoreHandle` this backend injects
        into :func:`~loremaster.governed.guarded_write` (design §10.6) — STUB / runnable-RED (63a).

        The ONE accessor every governed store exposes over its own driver triple: the builder
        returns ``StoreHandle(acquire=self._ensure_connection, drop=self._drop_connection,
        url=self._url)`` — the SAME callables :meth:`_query` already hands the driver — so a
        composed guarded write borrows this backend's real retry/self-heal lifecycle rather than
        cloning it (ONE IMPLEMENTATION). The retrofitted ``invalidate`` write path routes through
        ``governed.guarded_write(store=self.handle)``.
        """
        return StoreHandle(
            acquire=self._ensure_connection, drop=self._drop_connection, url=self._url
        )

    @property
    def audit_store(self) -> AuditStore:
        """The :class:`~loremaster.audit.AuditStore` this backend supplies to
        :func:`~loremaster.governed.guarded_write` on its bypass-reachable CLOSE paths
        (``invalidate`` + the supersede-close), so an admin BYPASS close is AUDITED (RES-2, design
        §10.6 rider v). Built from THIS backend's OWN connection params — the SAME accessor idiom as
        :meth:`handle` — so ``build_memory_backend`` needs no new argument (ONE IMPLEMENTATION).

        Used ONLY as the composable ``append_fragment`` builder: the audit CREATE rides the guarded
        mutation's OWN ``BEGIN … COMMIT`` through :meth:`handle`, so this instance NEVER opens a
        connection of its own (``append_fragment`` is pure) — a fresh instance per access leaks
        nothing, exactly as :meth:`handle` returns a fresh ``StoreHandle`` each call.
        """
        return AuditStore(
            url=self._url,
            namespace=self._namespace,
            database=self._database,
            user=self._user,
            password=self._password,
        )

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
        subject: Subject | None = None,
        scope: str | None = None,
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
            governed.GovernedDenied: no ``subject`` (an identity-less write — the owner is
                server-derived from the credential, never absent), or an explicit ``scope=`` the
                caller may not grant.
        """
        # §10.5 removed-behavior 1: an identity-less write DENIES (never an ownerless row). The
        # owner is server-derived from the resolved Subject; a hostile ``owner_*=`` arg cannot
        # move it because there IS no such parameter (F4 — the strongest anti-injection).
        if subject is None:
            raise governed.GovernedDenied(
                "lore_remember requires a verified identity — register an owned agent "
                "(`lore_comms action=register`) and present its capability; an identity-less "
                "write is denied (the owner is server-derived, never absent)"
            )
        resolved_scope = await self._resolve_write_scope(subject, scope)
        resolved_importance = self._resolve_importance(kind, importance)
        resolved_source = source if source is not None else MemorySource(kind=_DEFAULT_SOURCE_KIND)
        resolved_labels = list(labels or ())
        refs_stamp = derive_refs_stamp(self._refs_from_labels(resolved_labels))
        # #439 (design §10.9-B): fold the RESOLVED owner pair into the id so a content
        # collision across DIFFERENT owners is UNREPRESENTABLE (the create-path UPSERT can
        # never name a foreign-owned row). ``subject`` is non-None here (an identity-less
        # write already denied above). Same (owner, text, refs) still dedups in place.
        memory_id = derive_memory_id(
            text,
            refs_stamp,
            owner_principal=subject.principal_id,
            owner_agent=subject.agent_id,
        )
        now = datetime.now(UTC)
        resolved_expires = self._resolve_expiry(kind, expires_at, now)

        # The whole store-touching section runs under the rebuild lock, so a
        # remember can never interleave with the table recreate's drop→re-define
        # window (see :attr:`_rebuild_lock`): during a rebuild this BLOCKS, then
        # lands cleanly against the healthy recreated table (and its own UPSERT is
        # a direct write, never routed through the restore divergence guard). The
        # ``supersedes`` existence check is inside the lock too, so a rebuild's
        # transiently-dropped table never spuriously reports the target missing.
        async with self._rebuild_lock:
            # Unknown ``supersedes`` is a caller error raised BEFORE any write, so an
            # orphan successor never lands even in the durable ledger.
            if supersedes is not None and not await self._row_exists(supersedes):
                raise MemoryNotFoundError(
                    f"cannot supersede unknown memory {supersedes!r}: no such memory exists"
                )

            # The supersede-CLOSE is a WRITE on an EXISTING, possibly FOREIGN-owned row (design
            # §2.5 / cold-audit §F1: "both route through guarded_write/the stamp"), so it authorizes
            # through :func:`~loremaster.governed.guarded_write` exactly like :meth:`invalidate` — a
            # member cannot retire ANOTHER principal's note (single-brain on writes; a denied close
            # raises GovernedDenied and never mutates). It runs BEFORE the durable ledger write and
            # the new-row UPSERT, so a DENIED close leaves NO orphan successor — neither a ledger row
            # nor a Surreal row (the conscious atomicity trade: the old ONE-txn compose of
            # [upsert, close] is dropped for close-first authorization; a member superseding a
            # foreign row is stopped before any part of the new note lands). The close is
            # bypass-reachable (an admin may close a foreign row), so it carries the backend's own
            # ``audit_store`` (RES-2) — an admin bypass close is AUDITED, a member self-close is not.
            if supersedes is not None:
                await governed.guarded_write(
                    subject,
                    pdp.Action.WRITE,
                    table=MEMORY_TABLE,
                    row_id=supersedes,
                    # ``superseded_by`` is ``option<string>`` (surreal_schema) — a STRING literal,
                    # NEVER ``type::record()`` (that field-coerces and rolls the txn back). The new
                    # ``memory_id`` is a deterministic uuid5 (hex+dashes — safe to inline). The
                    # close ``valid_until`` self-stamps server-side (``guarded_write``'s raw
                    # ``set_fragment`` takes no bound params of its own).
                    set_fragment=(
                        f"{_COL_VALID_UNTIL} = time::now(), "
                        f"{_COL_SUPERSEDED_BY} = '{memory_id}'"
                    ),
                    audit=self.audit_store,
                    store=self.handle,
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
            # Stamp the GOVERNED columns from the RESOLVED subject (never a caller arg — F4) + the
            # PDP-validated scope. Owners bind as record<> links (store-ref §2). ``remember`` is a
            # CREATE of a NEW row (the creator owns it), so it stamps directly — it is the WRITE on
            # an EXISTING, possibly foreign-owned row (``invalidate`` AND the supersede-close above)
            # that routes through guarded_write.
            content[_COL_OWNER_PRINCIPAL] = RecordID(PRINCIPAL_TABLE, subject.principal_id)
            content[_COL_OWNER_AGENT] = RecordID(AGENT_TABLE, subject.agent_id)
            content[_COL_SCOPE] = resolved_scope
            # F5 (design §10.9-A L2a/L2b): the create-path UPSERT is an allowlisted RAW memory
            # mutation; run it inside ``governed.write_guard`` so the F5 runtime seam attributes it
            # to this frame (a memory write outside every guard is UNCLASSIFIED — deny-by-default).
            with governed.write_guard("remember"):
                await self._apply([self._upsert_fragment(memory_id, content)])
        return memory_id

    async def invalidate(self, memory_id: str, *, subject: Subject | None = None) -> None:
        """Retire a memory with no successor (``valid_until`` set, ``superseded_by`` None).

        The GOVERNED write path (packet 63a, design §1.1/§2.5): closing a row is a WRITE on an
        EXISTING (possibly FOREIGN-owned) row, so it authorizes through
        :func:`~loremaster.governed.guarded_write` — a member cannot retire ANOTHER principal's
        note (single-brain on writes: a denied close never mutates), while the owner / a household
        member can. An identity-less call DENIES.

        Args:
            memory_id: The id of the memory to retire.
            subject: The resolved :class:`lorerunes.pdp.Subject` whose WRITE reach is checked.

        Raises:
            governed.GovernedDenied: no ``subject`` (identity-less), or the subject may not WRITE
                the target row (a foreign-owned note).
            governed.GovernedConflict: the row vanished / was re-scoped between the read and the
                guarded mutation (LOUD, never a silent no-op).
            MemoryNotFoundError: ``memory_id`` does not exist.
        """
        if subject is None:
            raise governed.GovernedDenied(
                "lore invalidate requires a verified identity — an identity-less close is denied"
            )
        # Under the rebuild lock (see :attr:`_rebuild_lock`) so the existence check and the guarded
        # write never straddle the table recreate's drop→re-define window — a transiently-dropped
        # table would otherwise report a live memory as missing.
        async with self._rebuild_lock:
            if not await self._row_exists(memory_id):
                raise MemoryNotFoundError(
                    f"cannot invalidate unknown memory {memory_id!r}: no such memory exists"
                )
            # The guarded WRITE carries authorize_filter(WRITE) in its WHERE (single-brain), so a
            # foreign-owned row is excluded in the SAME statement. ``time::now()`` self-stamps the
            # close server-side (no param through the raw set_fragment).
            await governed.guarded_write(
                subject,
                pdp.Action.WRITE,
                table=MEMORY_TABLE,
                row_id=memory_id,
                set_fragment=f"{_COL_VALID_UNTIL} = time::now()",
                # The backend's own AuditStore (RES-2) — an admin BYPASS close is AUDITED (+1 audit
                # row in the SAME txn); a member self-close (requires_audit False) writes no trail.
                audit=self.audit_store,
                store=self.handle,
            )

    async def _resolve_write_scope(self, subject: Subject, scope: str | None) -> str:
        """Resolve a ``remember`` write's scope (design §2.4). An OMITTED scope defaults to the
        canonical PROJECT keep (so a fresh fleet note stays fleet-visible, §10-N). An EXPLICIT
        ``scope=`` is a PDP-VALIDATED REQUEST, not an identity claim: it is checked by the SAME
        ``lorerunes.pdp._grantable`` predicate the SET_SCOPE action uses (the fixed scopes + the
        caller's OWN keeps are grantable) — a keep the caller is NOT householded in DENIES with a
        teaching error. Calling ``_grantable`` via the ``pdp`` MODULE (not a bound import) is what
        makes the validation mutation-provable (ROUTING-IS-NOT-SHARING)."""
        if scope is None:
            return await self._default_project_scope()
        if not pdp._grantable(subject, scope):  # noqa: SLF001 - the ruled shared grant predicate
            raise governed.GovernedDenied(
                f"scope {scope!r} is not grantable by {subject.principal_id}/{subject.agent_id} — "
                "you are not householded in that keep; run `lore-adm add-household` to join it first"
            )
        return scope

    async def _default_project_scope(self) -> str:
        """The canonical PROJECT keep's ``keep:<id>`` scope, resolved by ONE indexed read of the
        ``keep.key`` UNIQUE index (design §2.2, SF-63-4). A missing project keep is a MISCONFIGURED
        deployment, not a silent fallback to ``principal-private`` (which would hide the fleet's
        shared notebook) — it DENIES LOUD (the project keep is minted by ``lore-adm
        migrate-governed`` at the cutover)."""
        rows = self._as_rows(
            await self._query(
                f"SELECT {_ID_KEY} FROM {KEEP_TABLE} WHERE key = $k",
                {"k": governed.PROJECT_KEEP_KEY},
            )
        )
        if not rows:
            raise governed.GovernedDenied(
                f"the canonical project keep (key={governed.PROJECT_KEEP_KEY!r}) is not provisioned "
                "— a governed write cannot default its scope to the fleet's shared keep; run "
                "`lore-adm migrate-governed` at the cutover (it mints the project keep)"
            )
        return pdp.keep_scope(self._bare_id(rows[0].get(_ID_KEY)))

    # -- reads --------------------------------------------------------------

    async def recall(
        self,
        query: str,
        *,
        subject: Subject | None = None,
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
        # §10.5 removed-behavior 1: an identity-less read DENIES (never the pre-retrofit unfiltered
        # answer). An unauthenticated read of the fleet's memory is exactly what the retrofit closes.
        if subject is None:
            raise governed.GovernedDenied(
                "lore_recall requires a verified identity — register an owned agent "
                "(`lore_comms action=register`) and present its capability; an identity-less "
                "read of the fleet's memory is denied"
            )
        if lens is not None:
            raise ValueError(
                f"the local memory backend does not support a recall lens (got {lens!r}); "
                f"lens is unsupported in P7"
            )
        # The query embed does not touch the ``memory`` table, so it stays OUTSIDE
        # the lock; the store-reading section (hybrid search + reinforcement UPDATE)
        # runs UNDER the rebuild lock (see :attr:`_rebuild_lock`) so a recall can
        # never read the table mid-recreate — it BLOCKS while a rebuild holds the
        # lock, then returns against the healthy recreated table, never an empty /
        # error result off the dropped table.
        query_vector = await self._embedder.embed_query(query)
        async with self._rebuild_lock:
            filter_conditions, params = self._build_recall_filter(include, as_of, labels, kind)
            # THE read splice (R-a.3): the SAME authorize_filter(READ) fragment every governed list
            # read carries, so recall serves ONLY the caller's visible set (F3 cross-principal
            # isolation) — a row the caller cannot see never enters the answer even when it matches
            # the query. Both hybrid arms AND this fragment (single-brain with the Python gate).
            read_fragment, read_params = governed.read_filter(subject, MEMORY_TABLE)
            filter_conditions.append(f"({read_fragment})")
            params.update(read_params)
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

    async def rebuild_embeddings(self) -> int:
        """Re-embed every stored memory from its durable ledger ``note_text`` at the
        CURRENT embedding schema — the MEMORY arm of the embedding-schema rebuild.

        The memory MIRROR of the chunk-tier rebuild
        (:meth:`~loremaster.index.indexer.Indexer.rebuild_all`): the durable
        ledger's ``note_text`` is to memory what the on-disk source files are to
        chunks — the dim-independent content the re-embed reads from. Recreates the
        ``memory`` table at the current dim (:meth:`_recreate_memory_table` drops
        the old rows AND the possibly-stale-width HNSW index, then re-defines both
        at ``self._dim``), then replays the ledger — re-embedding EVERY note at the
        new schema. It therefore HEALS both a same-dim schema change (a model /
        prompt swap) AND a DIM change; the latter is where chunks punt to an
        operator-level full recreate, but memory's re-embeddable ledger lets it
        self-heal in place, so a dim change is never fail-loud or refused (the
        operator's explicit contract). No memory is lost: the ledger is the
        durable source a Surreal wipe cannot touch, written FIRST on every
        :meth:`remember`, so a note that reached only the ledger is still replayed.

        Idempotent + resumable: an interrupted pass leaves the CALLER's fingerprint
        stamp un-advanced (the stamp is the COMBINED completion evidence for both
        arms), so the next boot re-detects the mismatch and re-runs; a re-run
        recreates + replays from the ledger again, converging with no duplicates
        (deterministic ids). A ledger-less backend is a no-op — recreating would
        drop store rows with no durable source to restore them from.

        Returns:
            The number of ledger rows re-embedded into the fresh table (``0`` when
            no ledger is configured or the ledger is empty).
        """
        if self._ledger is None:
            # No durable source to re-embed from — recreating the table would drop
            # the store rows with no way to restore them. A ledger-less backend
            # cannot be safely rebuilt, so leave it untouched (mirrors the guard in
            # :meth:`restore_from_ledger`).
            return 0
        # Hold the rebuild lock for the ENTIRE drop→DDL→ledger-restore span, so no
        # concurrent MCP ``remember`` / ``recall`` / ``invalidate`` can interleave
        # with the table recreate (see :attr:`_rebuild_lock`). The lock is NOT
        # re-entrant, so the internals invoked here — :meth:`_recreate_memory_table`
        # (→ :meth:`ensure_ready`) and :meth:`restore_from_ledger` (→ :meth:`_apply`)
        # — must NOT re-acquire it; they run UNLOCKED, correctly nested under this
        # single hold.
        async with self._rebuild_lock:
            await self._recreate_memory_table()
            return await self.restore_from_ledger()

    async def _recreate_memory_table(self) -> None:
        """Drop the ``memory`` table, then re-apply the schema slice at the CURRENT dim.

        ``REMOVE TABLE IF EXISTS`` clears the old rows AND the possibly-stale-width
        HNSW index; :meth:`ensure_ready` then re-applies the SAME
        :func:`~loremaster.store.surreal_schema.generate_memory_ddl` slice, whose
        ``IF NOT EXISTS`` statements now define the table + a NEW-dim HNSW /
        FULLTEXT / ``valid_until`` index from scratch (nothing survived the drop to
        short-circuit them) — so the subsequent replay re-embeds into an index
        sized for the current dim.

        Two separate transactions, not one: SurrealDB builds the HNSW / FULLTEXT
        indexes ASYNCHRONOUSLY, so a single ``REMOVE TABLE … DEFINE INDEX``
        transaction races the drop against the still-settling index build and the
        engine rejects it with a retryable conflict. Dropping first, then applying
        the proven ``ensure_ready`` DDL, sidesteps that.

        The drop→re-define window is NOT self-safe: a store write landing in it
        would auto-create ``memory`` SCHEMALESS, so ``ensure_ready``'s
        ``DEFINE FIELD … FLEXIBLE`` is rejected, the recreate rolls back, and the
        table is left schemaless/index-less (fail-loud rebuild + bricked recall).
        So the window is closed by MUTUAL EXCLUSION, not left to chance:
        :meth:`rebuild_embeddings` holds :attr:`_rebuild_lock` across this WHOLE
        recreate (and the following ledger restore), and :meth:`remember` /
        :meth:`recall` / :meth:`invalidate` take the SAME lock around their store
        section, so no MCP write/read interleaves the window. This method therefore
        must NOT take the lock itself — its caller already holds it, and the lock is
        not re-entrant. The durable ledger still write-throughs FIRST on every
        :meth:`remember`, so a note that reached only the ledger is replayed by
        :meth:`restore_from_ledger` — no memory is lost.
        """
        # F5 (design §10.9-A L2a): the boot/admin REMOVE TABLE is an allowlisted RAW memory mutation
        # (RES-1 — reachable only from ``rebuild_embeddings``); run it inside ``governed.write_guard``
        # so it is attributable at the F5 seam like every other memory-table mutation.
        with governed.write_guard("_recreate_memory_table"):
            await self._query(f"REMOVE TABLE IF EXISTS {MEMORY_TABLE}")
        await self.ensure_ready()
        logger.debug(
            "memory.schema.recreated", extra={"database": self._database, "dim": self._dim}
        )

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

        ``query_text`` fed to the LEXICAL (BM25) arm is word-boundary
        truncated and its analyzed token count clamped
        (:data:`_MAX_LEXICAL_QUERY_CHARS` / :data:`_MAX_QUERY_TOKENS`, shared
        derivation in :mod:`loremaster.store.query_text`) so a realistically
        long recall query — e.g. a long note being searched for — can never
        trip the SurrealQL parser's own expression-recursion-depth limit on
        this arm's AND-predicate (finding #69); ``query_vector`` always
        embeds the caller's FULL, untruncated text (computed upstream by
        :meth:`recall`) and is never affected by either cap.
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

        lexical_query_text = truncate_at_word_boundary(query_text, _MAX_LEXICAL_QUERY_CHARS)
        tokens = await self._analyze_query(lexical_query_text)
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
        # F5 (design §10.9-A L2a/L2b + §10.9-C): the reinforcement bump is an allowlisted RAW memory
        # mutation on the NON-governed ``importance`` column ONLY; run it inside
        # ``governed.write_guard`` so the F5 seam attributes each observed bump to this frame.
        with governed.write_guard("_reinforce"):
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
        # F5 (design §10.9-A L2a): the ledger-replay UPSERT is an allowlisted RAW memory mutation
        # (RES-1 boot/admin — the STORED id, never a re-derivation); run it inside
        # ``governed.write_guard`` so it is attributable at the F5 seam.
        with governed.write_guard("_replay_record"):
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
