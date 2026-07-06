"""Async SurrealDB store — the P2 unification's replacement for ``QdrantStore``.

One :class:`SurrealStore` owns a single per-project SurrealDB database and
exposes the async surface the loremaster callers already depend on (upsert /
scroll / count / the three deletes) plus the two behaviours the unification
adds: one-query **hybrid retrieval** (HNSW vector ⊕ BM25 FULLTEXT fused by the
engine's native ``search::rrf``) and an **atomic per-file replace** (a single
transaction so a concurrent reader never observes a half-applied file).

Everything runs against a real SurrealDB server (``ws://…/rpc``) via the
``surrealdb`` async SDK — the hybrid recall, the BM25 rescue, the RRF fusion and
the snapshot isolation are all server-side properties, so there is no in-memory
shortcut.

Dialect facts this store is built on (verified against the 3.0.5 engine; re-verified
byte-for-byte on 3.1.5 with no deltas — 3.1.x is the floor going forward, matching
Spectron's runtime floor so a future self-hosted Spectron memory backend can share
this server):

* **Filtered KNN under-returns**, so each hybrid arm *overfetches* (``k`` scaled
  by :data:`_OVERFETCH_FACTOR`) inside the filtered subquery and the final ``k``
  is honoured only after fusion.
* **The HNSW KNN operator's bare ``<|K|>`` form is valid** (it uses the
  index's default EF search-list size); this store always spells the EXPLICIT
  ``<|K,EF|>`` form instead, so the search-list size can be sized to the
  overfetch deliberately rather than left to an implicit default. It also may
  not be nested in an ``OR``/``NOT``, so the vector arm ANDs its filters and
  never ORs.
* **``search::rrf`` accepts only INLINE subqueries** (a ``LET``-bound arg comes
  back ``None``); it returns the fused rows with an added ``rrf_score``.
* **The FULLTEXT ``@@`` match is conjunctive over the ANALYZED query tokens**,
  and the analyzer keeps punctuation tokens (``.``/``_``). A raw dotted phrase
  such as ``PurchaseOrder.action_confirm`` therefore matches nothing. The store
  fixes this by analyzing the query with the engine's own ``code_ident``
  analyzer, dropping the punctuation tokens, and ORing the word tokens — the
  identifier-tokenization step that makes the BM25 rescue work.

Trust-boundary hardening (this store sits behind the ``lore_search`` tool in P6,
so an agent supplies its filter keys, ``k`` and query text):

* **Filter KEYS are allow-listed** against :data:`_ALLOWED_FILTER_KEYS` (the
  schema's chunk-column set) BEFORE any clause is built, so a key can never be
  string-interpolated into a statement — only VALUES are bound. An unknown key
  raises :class:`SurrealStoreError` and never reaches a query.
* **``scroll`` is bounded** — it takes a required ``limit`` emitted as a bound
  ``LIMIT`` param, so a read is never unbounded.
* **``k`` and the query text are clamped** — see :data:`_MAX_HYBRID_K`,
  :data:`_MAX_HNSW_EF`, :data:`_MAX_QUERY_TEXT_CHARS` and
  :data:`_MAX_QUERY_TOKENS`. An unclamped huge ``k`` overran the engine's HNSW
  search-list allocation and crashed the shared server, so the clamp is
  load-bearing, not cosmetic.
* **Write-path sizes are bounded too** — a composed transaction's body-
  statement count is capped at
  :data:`~loremaster.store._txn.TXN_STATEMENT_HARD_CAP` (in ``compose()``) and
  a single ``file_text`` body is capped at :data:`FILE_TEXT_MAX_BYTES`, both
  refused at BUILD time, before anything reaches the server.

Deliberate divergences from the retired ``QdrantStore`` (module deleted at P8a;
not oversights):

* **Server, never embedded.** :data:`_SurrealConnection` is typed as the SDK's
  full return union (including ``AsyncEmbeddedSurrealConnection``) because
  that is what :func:`surrealdb.AsyncSurreal` can hand back for *some* URL
  scheme, but this store only ever opens a networked ``ws://``/``http://`` URL —
  never a local/embedded engine — because the hybrid-search dialect behaviours
  it depends on (server-side HNSW, BM25 FULLTEXT, ``search::rrf``) are
  properties of the standalone server, the same real-server-only posture
  ``QdrantStore`` takes with ``AsyncQdrantClient``.
* **No retry-with-backoff layer, but a self-healing connection.**
  ``QdrantStore`` wraps every client call in ``_with_retry`` (capped exponential
  backoff on a transient 5xx/transport failure). This store does not layer a
  backoff loop: each operation runs over ONE signed-in, stateful WS connection,
  and a connection-class failure *during* an operation nulls ``self._connection``
  (see :meth:`_query`) so the lazy reconnect in :meth:`_ensure_connection`
  re-establishes a freshly signed-in connection on the caller's next call — the
  mid-life self-heal. The failed op itself still raises immediately as a typed
  :class:`SurrealConnectionError` (LOUD, never a silent empty result); an
  app-level retry/backoff layer analogous to Qdrant's is left for a later phase
  if production traffic shows the fail-fast-then-reconnect behaviour insufficient.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from pathlib import PurePosixPath
from typing import Any

from surrealdb import AsyncSurreal, RecordID

from loremaster.index.records import Record
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    _SERVER_LOG_HINT,
    TXN_STATEMENT_WARN_THRESHOLD,
    SurrealConnectionError,
    SurrealStoreError,
    TxnFragment,
    _classify_engine_error,
    _SurrealConnection,
    compose,
    execute_transaction,
    is_connection_error,
)
from loremaster.store.candidate import Candidate, CandidateOrigin
from loremaster.store.surreal_schema import (
    CHUNK_COLUMNS,
    CHUNK_FILTER_KEYS,
    CHUNK_FULLTEXT_FIELDS,
    CHUNK_TABLE,
    DEFAULT_ANALYZER_NAME,
    FILE_TEXT_TABLE,
    TRACE_HIT_COUNT_FIELD,
    TRACE_LATENCY_MS_FIELD,
    TRACE_MODEL_FIELD,
    TRACE_PARAMS_HASH_FIELD,
    TRACE_SESSION_FIELD,
    TRACE_TABLE,
    TRACE_TOKEN_COST_FIELD,
    TRACE_TOOL_FIELD,
    TRACE_TS_FIELD,
    generate_ddl,
)

logger = logging.getLogger(__name__)

# The public surface. The connection/error vocabulary below is imported from
# :mod:`loremaster.store._txn` (see the note under the imports); naming it in
# ``__all__`` marks it as an EXPLICIT re-export so mypy-strict
# (``no_implicit_reexport``) keeps the historical
# ``from loremaster.store.surreal import …`` seam every caller and test uses.
__all__ = [
    "SurrealStore",
    "SurrealStoreError",
    "SurrealConnectionError",
    "VectorDimensionError",
    "_CONNECTION_ERRORS",
    "_SurrealConnection",
]

# The connection/transport error vocabulary (:class:`SurrealStoreError`,
# :class:`SurrealConnectionError`, :data:`_CONNECTION_ERRORS`,
# :data:`_SurrealConnection`) and the shared transaction / error-classification
# seams (:func:`execute_transaction`, :func:`is_connection_error`) live in
# :mod:`loremaster.store._txn` so the store and the manifest raise/catch one
# audited set — they are imported (and thereby re-exported) above; see that
# module's docstring for why.

# The signin credential keys the SDK expects.
_SIGNIN_USER_KEY = "username"
_SIGNIN_PASS_KEY = "password"

# Filtered KNN under-returns, so each hybrid arm requests this multiple of the
# caller's ``k`` before the tier filter thins the result; RRF re-imposes ``k``.
# Value from the P0 spike's empirical under-return measurements on filtered KNN.
_OVERFETCH_FACTOR = 4

# The HNSW search-list size (``EF``) floor. EF must comfortably exceed the
# overfetch for the index to actually surface that many filtered neighbours.
# Floor from the P0 spike: below it, the index under-fills the overfetch itself.
_MIN_HNSW_EF = 64

# The store-level ceilings that bound the numbers spliced into the HNSW
# ``<|K,EF|>`` operator and the ``search::rrf`` arity (defense-in-depth DoS
# guards). The agent-facing tool layer already clamps ``k`` at its request schema
# (server.py ``_MAX_SEARCH_K`` = 100), but a non-tool / future caller reaches
# :meth:`hybrid_search` directly, so ``k`` — and thus the derived overfetch and
# EF — are clamped again HERE. An unclamped huge ``k`` overran the engine's HNSW
# search-list allocation and SIGSEGV'd the shared server, so these bounds are
# load-bearing, not cosmetic.
_MAX_HYBRID_K = 1000  # 10x the tool-layer cap — generous headroom, still bounded.
# The practical HNSW search-list (EF) ceiling; the KNN overfetch (the ``K`` of
# ``<|K,EF|>``) is bounded by the same value because EF must cover the requested
# ``K`` for the index to return it, so both share this one ceiling.
_MAX_HNSW_EF = 1024

# The query-text DoS guards: the analyzed token list drives a per-token FULLTEXT
# OR-predicate, so both the raw text length and the resulting token count are
# capped before tokenization / predicate construction. Real queries (identifiers
# or short natural-language phrases) sit far below both caps.
_MAX_QUERY_TEXT_CHARS = 4096
_MAX_QUERY_TOKENS = 64

# The Reciprocal-Rank-Fusion smoothing constant (the standard RRF ``k``); larger
# values flatten the rank-position weighting. The textbook default the P0 spike
# validated against this engine's ``search::rrf``.
_RRF_K = 60

# The chunk text fields a hybrid query's word tokens are matched against (BM25) —
# imported from the schema module so the ``@@`` predicate always targets exactly
# the fields that carry a FULLTEXT index (single source of truth, never a
# hand-copied twin that could drift out of sync with the DDL).
_FULLTEXT_FIELDS = CHUNK_FULLTEXT_FIELDS

# The closed allow-list of chunk columns a caller may filter on, imported from
# the schema so it can never drift from the columns the DDL defines (single
# source of truth). Every filter KEY is validated against this set at the store's
# trust boundary BEFORE any clause is built, so an agent-supplied key can never be
# interpolated into a SurrealQL statement — only VALUES are bound (injection
# defense).
_ALLOWED_FILTER_KEYS = frozenset(CHUNK_FILTER_KEYS)

# A WHERE predicate that matches nothing — used for the fulltext arm when a query
# yields no word tokens, so the vector arm alone carries the fusion.
_NO_MATCH_PREDICATE = "false"

# The bound-parameter name for the hybrid query's embedding vector — shared by
# name between the params dict and the vector-arm SurrealQL fragment below so
# the two can never drift out of sync.
_QUERY_VECTOR_PARAM = "__qvec"

# The bound-parameter name for a read's row LIMIT — bound (never interpolated) so
# the cap is data, and ``__``-prefixed so it can't collide with a filter param.
_LIMIT_PARAM = "__limit"

# Keys the SDK adds to a returned row that are NOT part of the stored payload.
_ID_KEY = "id"
_RRF_SCORE_KEY = "rrf_score"
_EMBEDDING_KEY = "embedding"
_COUNT_KEY = "count"

# The chunk table's ``metadata`` column — a REQUIRED (non-``option``) FLEXIBLE
# object (see ``surreal_schema._CHUNK_FIELD_SPECS``) that nests any payload key
# NOT among the schema's declared chunk columns, so a write always emits a
# well-formed row even when nothing needs nesting (an empty object).
_METADATA_KEY = "metadata"

# The chunk table's REQUIRED, BM25-indexed identifier-retrieval column — the
# plan's DERIVED field (identity + bare name + file stem). No production
# translator emits it, so ``_chunk_content`` derives it when absent.
_IDENT_TEXT_KEY = "ident_text"

# The declared chunk columns that are spread top-level rather than nested into
# ``_METADATA_KEY`` — every schema column EXCEPT ``metadata`` itself (the
# extras bucket) and ``embedding`` (assembled separately from the caller's
# vector, never carried in ``record.payload``). Derived from the schema's own
# field specs (``CHUNK_COLUMNS``), never a hand-copied parallel list, so it can
# never drift from the DDL.
_DECLARED_CHUNK_COLUMNS = frozenset(CHUNK_COLUMNS) - {_METADATA_KEY, _EMBEDDING_KEY}

# The record-id table separator in a stringified ``RecordID`` (``chunk:uuid``).
_TABLE_SEPARATOR = ":"

# Every hybrid hit is a fusion of both arms, so it is reported as ``fused``.
_FUSED_ORIGIN: CandidateOrigin = "fused"

# The producer-namespacing prefixes the store stamps on the bound params of
# the transaction fragments it builds, so a chunk fragment and a ``file_text``
# fragment (and the manifest / graph fragments they compose with) never clobber
# one another's params in the merged transaction (see
# :func:`~loremaster.store._txn.compose`). ``st_`` = the STore's chunk rows;
# ``ft_`` = the File-Text body rows.
CHUNK_FRAGMENT_PARAM_PREFIX = "st_"
FILE_TEXT_FRAGMENT_PARAM_PREFIX = "ft_"

# The ``file_text`` row's two content columns (see
# ``surreal_schema._file_text_statements``): the verbatim body + its SHA-512.
_FILE_TEXT_TEXT_KEY = "text"
_FILE_TEXT_SHA_KEY = "sha512"

# The per-row byte ceiling on a ``file_text`` body — defense-in-depth against
# one pathological file (a giant generated/vendored blob) inflating a single
# row, and the composed transaction it rides in (see
# ``loremaster.store._txn.TXN_STATEMENT_HARD_CAP`` for the sibling statement-
# count guard), without limit. Measured in UTF-8 BYTES, not code points — the
# actual on-the-wire/row size a multi-byte body (CJK, emoji, …) really costs —
# comfortably above realistic large generated/vendored source files (a few MB).
FILE_TEXT_MAX_BYTES = 10 * 1024 * 1024


class VectorDimensionError(SurrealStoreError):
    """A vector's width does not match the store's configured dimension."""


class SurrealStore:
    """Async store over a single per-project SurrealDB database.

    The connection is opened lazily and cached: the first operation (or an
    explicit :meth:`ensure_ready`) signs in, selects the namespace/database and
    applies the schema; subsequent operations reuse the live connection. A
    connection-class failure during an operation drops the cached handle so the
    next call transparently reconnects (the mid-life self-heal).

    Args:
        url: The SurrealDB RPC URL (e.g. ``ws://127.0.0.1:18000/rpc``).
        namespace: The namespace the database lives under.
        database: The per-project database name.
        dim: The embedding width; wired into the schema's HNSW indexes and
            enforced (loudly) on every upserted vector.
        user: The root/username to sign in with.
        password: The password to sign in with.
        analyzer_name: The code-identifier analyzer name (must match the schema);
            defaults to :data:`DEFAULT_ANALYZER_NAME`.
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
        analyzer_name: str = DEFAULT_ANALYZER_NAME,
    ) -> None:
        self._url = url
        self._namespace = namespace
        self._database = database
        self._dim = dim
        self._user = user
        self._password = password
        self._analyzer_name = analyzer_name
        # Opened on first use; ``None`` means "not yet connected / closed".
        self._connection: _SurrealConnection | None = None
        # Guards the connect-time check-then-set below: without it, N
        # concurrent first-callers on a fresh instance all pass the
        # ``self._connection is not None`` check before any of them finishes
        # connecting, each opening its OWN underlying SDK connection. Safe to
        # construct here (unbound to any running loop) on Python >= 3.10.
        self._connect_lock = asyncio.Lock()

    # -- connection lifecycle ----------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking: the fast path (already connected) never
        touches the lock; a first caller acquires :attr:`_connect_lock` and
        re-checks — a concurrent racer that lost the race to acquire the lock
        finds the connection already assigned by the winner and returns it
        without opening a second one. Signs in, materialises the
        namespace/database (idempotent) and selects them. Any transport or
        auth failure is wrapped in :class:`SurrealConnectionError` — a down
        server or bad password is a LOUD, typed failure, never a hang or a
        silent empty result.

        Returns:
            The cached, signed-in connection bound to this store's ns/db.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        if self._connection is not None:
            return self._connection
        async with self._connect_lock:
            # Re-check: another caller may have already connected while this
            # one was waiting for the lock. mypy narrows ``self._connection``
            # to ``None`` from the outer guard and can't model the
            # cross-coroutine mutation across the ``await`` inside
            # ``__aenter__`` above, hence the unreachable ignore (mirrors
            # ``watcher.py``'s identical double-checked-lock pattern).
            if self._connection is not None:
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
                # Close the half-open socket (if any) so a failed connect never
                # leaks a dangling connection, then surface a typed connection
                # error.
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "store.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    @property
    def file_text_max_bytes(self) -> int:
        """The per-body UTF-8 byte ceiling the indexer's clause-4 pre-check reads.

        Exposed as the SINGLE source of truth the indexer consults before it decides
        whether to compose the ``file_text`` fragment for a file (see
        :meth:`Indexer._file_text_within_cap`) — the indexer never hardcodes the cap.
        A body over this ceiling is indexed WITHOUT its ``file_text`` fragment
        (chunks / manifest / graph still land); :meth:`file_text_fragment` enforces
        the SAME ceiling as a build-time hard refusal for any direct caller.
        """
        return FILE_TEXT_MAX_BYTES

    async def ensure_ready(self) -> None:
        """Connect and apply the schema — idempotent and safe to re-run.

        The DDL is generated ``IF NOT EXISTS`` from the configured ``dim``, so a
        second call neither raises nor wipes existing data. Applied inside ONE
        ``BEGIN … COMMIT`` transaction via :func:`~loremaster.store._txn.
        execute_transaction`, which inspects EVERY statement's status — the
        SDK's plain ``query()`` inspects only the FIRST statement, so a LATER
        statement's rejection would otherwise roll the whole schema back
        server-side while ``query()`` raised nothing at all (verified live).

        Raises:
            SurrealConnectionError: The server is unreachable, rejected auth, or
                the socket died mid-apply.
            SurrealStoreError: Any DDL statement was rejected by the engine (a
                real schema bug); the connection stays healthy.
        """
        await self._ensure_connection()
        ddl = generate_ddl(dim=self._dim, analyzer_name=self._analyzer_name)
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("store.schema.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any); safe to call more than once."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal).

        A COMPARE-AND-SWAP, not an unconditional null: ``self._connection`` is
        cleared only when ``connection`` IS STILL the currently cached handle.
        A late caller can be holding a STALE connection reference captured
        BEFORE an earlier self-heal already replaced ``self._connection`` with
        a fresh one; nulling unconditionally would let that late caller wipe
        out a perfectly healthy, freshly-reconnected handle out from under
        every other in-flight caller. The connection HANDED to this call is
        always closed regardless, since it is the dead/stale one either way.
        Shared by :meth:`_query` and the transaction seam
        (:func:`~loremaster.store._txn.execute_transaction`, via the ``drop``
        callback).
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
            logger.debug("store.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection.

        Launders the SDK's wide ``Value`` return union to ``Any`` at this private
        seam so the public methods stay strictly typed without union-narrowing
        noise (the same pattern the test harness uses).

        This is also the store's single self-heal seam, and it CLASSIFIES a
        failure (see :func:`~loremaster.store._txn.is_connection_error`): a
        transport/socket/auth failure (the WS socket died mid-life) drops the
        cached handle so the NEXT call transparently reconnects via
        :meth:`_ensure_connection`, and is surfaced as a typed, LOUD
        :class:`SurrealConnectionError`; a domain/schema/type rejection of the
        write itself (an ``ASSERT`` violation, a type-coercion failure) is NOT a
        connection fault — it keeps the healthy connection and surfaces as a
        :class:`SurrealStoreError`. Either way it is LOUD, never a silent empty
        result.

        Message hygiene (ledger #31, mirroring :func:`~loremaster.store._txn.
        execute_transaction`): a domain rejection's raw engine text can echo a
        bound VALUE back verbatim (an ``ASSERT``/coercion rejection), and that text
        flows to MCP clients in P8 — so the raised :class:`SurrealStoreError`
        carries only a CLASSIFIED, generic label
        (:func:`~loremaster.store._txn._classify_engine_error`) plus a "see the
        server log" hint; the full engine detail is logged server-side instead.

        The ``except`` also catches a raw ``KeyError``: probe-verified live (a
        socket drop with a query in flight), the installed SDK's OWN response
        routing raises ``builtins.KeyError(<request-uuid>)`` straight out of
        ``connection.query(...)`` — never a domain rejection — so it is ALWAYS
        classified as a connection fault (self-heal + :class:`SurrealConnectionError`),
        never mistaken for a domain rejection of the statement itself. The
        ``except`` wraps ONLY the bare SDK call above — never our own
        dict-indexing code — so this can never misclassify a ``KeyError``
        raised by application logic.
        """
        connection = await self._ensure_connection()
        try:
            return await connection.query(statement, params or {})
        except (*_CONNECTION_ERRORS, KeyError) as error:
            if isinstance(error, KeyError) or is_connection_error(error):
                # A genuine transport/auth fault: self-heal and surface loudly.
                await self._drop_connection(connection)
                raise SurrealConnectionError(
                    f"SurrealDB query failed against {self._url!r}: {error}"
                ) from error
            # A domain/schema rejection of the write — the connection is healthy
            # and must not be thrown away for a fault that is not the transport's.
            # Message hygiene (ledger #31, mirroring ``execute_transaction``): the
            # raw engine text can echo a bound VALUE back verbatim (an ASSERT /
            # coercion rejection), and that text flows to MCP clients in P8 — so the
            # FULL detail is logged server-side and the RAISED error carries only a
            # CLASSIFIED, generic label plus a "see the server log" correlation
            # hint, never the raw engine text itself.
            error_class = _classify_engine_error(error)
            logger.error(
                "store.query.rejected",
                extra={"url": self._url, "error_class": error_class, "engine_error": str(error)},
            )
            raise SurrealStoreError(
                f"SurrealDB query rejected against {self._url!r} ({error_class}); "
                f"{_SERVER_LOG_HINT}"
            ) from error

    # -- writes -------------------------------------------------------------

    def _validate_dimensions(
        self, records_with_vectors: Sequence[tuple[Record, list[float]]]
    ) -> None:
        """Reject the whole batch if ANY vector is the wrong width.

        Validated up front, before any write, so a wrong-width vector can never
        partially persist — the probe-gate discipline the resilience contract
        pins.

        Raises:
            VectorDimensionError: A vector's length differs from ``dim``.
        """
        for record, vector in records_with_vectors:
            if len(vector) != self._dim:
                raise VectorDimensionError(
                    f"vector for chunk {record.point_id!r} has width {len(vector)}, "
                    f"expected {self._dim}"
                )

    @classmethod
    def _chunk_content(cls, record: Record, vector: list[float]) -> dict[str, Any]:
        """The full chunk row content — declared columns top-level, extras nested.

        ``record.payload`` is production-shaped: declared chunk columns plus
        arbitrary chunker metadata keys spread top-level (see
        ``records.chunk_to_record``), usually with NO ``"metadata"`` key at
        all. This splits it via :meth:`_split_payload` so the write always
        matches the schema's shape — the ``metadata`` column is a REQUIRED
        (non-``option``) field, so it is emitted even when empty. A payload
        that already carries an explicit ``"metadata"`` dict (the legacy
        nested-producer shape) is still accepted: its contents merge into the
        same extras bucket alongside any top-level extras.

        ``ident_text`` — the plan's DERIVED identifier-retrieval field
        (identity + bare name + file stem, BM25-indexed twice) — is another
        REQUIRED column no production translator emits
        (``records.chunk_to_record`` has no such field), so when the payload
        does not carry one it is derived HERE, at the single point every
        chunk write funnels through. A producer-supplied value always wins.
        """
        declared, metadata = cls._split_payload(record.payload)
        if not declared.get(_IDENT_TEXT_KEY):
            declared[_IDENT_TEXT_KEY] = cls._derive_ident_text(declared)
        return {**declared, _METADATA_KEY: metadata, _EMBEDDING_KEY: vector}

    @staticmethod
    def _derive_ident_text(declared: dict[str, Any]) -> str:
        """The plan's ``ident_text`` derivation: identity + bare name + file stem.

        Deduplicated in order (a module-level chunk's identity often IS the
        file stem). A chunk with no identity still gets its file stem, so any
        ``chunk_to_record``-built payload (which always carries ``file_path``)
        derives non-empty; a pathological payload lacking BOTH identity and
        file_path derives ``''`` — stored without error (no ASSERT on the
        column), just unsearchable by identifier.
        """
        identity = str(declared.get("identity") or "")
        bare_name = identity.rsplit(".", 1)[-1] if identity else ""
        file_stem = PurePosixPath(str(declared.get("file_path") or "")).stem
        parts: list[str] = []
        for part in (identity, bare_name, file_stem):
            if part and part not in parts:
                parts.append(part)
        return " ".join(parts)

    @staticmethod
    def _split_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Split a payload into declared top-level columns + metadata extras.

        Every key in :data:`_DECLARED_CHUNK_COLUMNS` passes through
        top-level, faithfully — including a value already resolved from a
        metadata-key collision upstream (``records.chunk_to_record`` spreads
        the chunk's metadata LAST, so a colliding key like ``chunk_type`` is
        already resolved to one value before the record ever reaches the
        store). Every other key nests into the metadata bucket; an explicit
        ``"metadata"`` dict (the legacy nested-producer shape) contributes its
        own contents to that SAME bucket rather than round-tripping as a
        literal nested key.

        Args:
            payload: The record's payload, in either production (flattened)
                or legacy (nested-``"metadata"``) shape.

        Returns:
            ``(declared, metadata)`` — the top-level column values and the
            extras to nest under :data:`_METADATA_KEY`.

        Raises:
            SurrealStoreError: The payload carries a reserved key the store
                cannot round-trip faithfully — a non-dict ``"metadata"``
                value (neither the production nor the legacy shape; silently
                dropping it would be data loss) or an ``"embedding"`` key
                (would nest on write and spuriously reappear top-level on
                read-merge). Refused BEFORE any statement is built, so
                nothing persists.
        """
        declared: dict[str, Any] = {}
        metadata: dict[str, Any] = {}
        for key, value in payload.items():
            if key == _METADATA_KEY:
                if not isinstance(value, dict):
                    raise SurrealStoreError(
                        f"payload key {_METADATA_KEY!r} is reserved for the nested "
                        f"metadata column and only accepts a dict (the legacy "
                        f"nested-producer shape); got {type(value).__name__} — "
                        f"refusing the write rather than silently dropping the value"
                    )
                metadata.update(value)
                continue
            if key == _EMBEDDING_KEY:
                raise SurrealStoreError(
                    f"payload key {_EMBEDDING_KEY!r} is reserved for the vector "
                    f"column; a chunker metadata key by this name would nest on "
                    f"write and spuriously reappear top-level on read-merge — "
                    f"refusing the write"
                )
            if key in _DECLARED_CHUNK_COLUMNS:
                declared[key] = value
            else:
                metadata[key] = value
        return declared, metadata

    async def upsert(self, records_with_vectors: Sequence[tuple[Record, list[float]]]) -> None:
        """Upsert ``(record, vector)`` pairs by their deterministic point id.

        The deterministic, tier-keyed id means a re-upsert of an unchanged chunk
        overwrites in place (never duplicates) and two tiers' copies of one path
        coexist. A duplicate id within a single batch collapses to the last write.

        Args:
            records_with_vectors: ``(Record, vector)`` pairs to persist.

        Raises:
            VectorDimensionError: Any vector is the wrong width (nothing persists).
        """
        self._validate_dimensions(records_with_vectors)
        for record, vector in records_with_vectors:
            await self._query(
                f"UPSERT type::record('{CHUNK_TABLE}', $id) CONTENT $content",
                {"id": record.point_id, "content": self._chunk_content(record, vector)},
            )

    async def record_trace(
        self,
        *,
        tool: str,
        params_hash: str,
        hit_count: int,
        latency_ms: float,
        session: str,
        token_cost: int | None = None,
        model: str | None = None,
    ) -> None:
        """Persist one observability trace row — the mcp role's async write path.

        The ``trace`` table is lore's per-tool-invocation OBSERVABILITY row (see
        ``surreal_schema._TRACE_FIELD_SPECS``): the six core fields describe one
        served request, and the two optional accounting columns
        (``token_cost``/``model``) ride alongside when supplied. ``ts`` is stamped
        SERVER-SIDE by the schema's ``DEFAULT time::now()`` — this method never
        computes or sends it — so a caller need only describe the invocation.

        A single awaitable insert through the store's self-healing,
        error-classifying :meth:`_query` seam: a transport failure self-heals and
        raises :class:`SurrealConnectionError`; a domain/schema rejection (e.g. a
        wrong-type field) keeps the healthy connection and raises
        :class:`SurrealStoreError` — never a raw engine error, never a silent
        success. The row is written with ``CONTENT`` (a single bound object)
        rather than ``SET session = $session`` because ``session`` is a SurrealDB
        PROTECTED variable name: a top-level ``$session`` bound param is rejected
        outright ("'session' is a protected variable and cannot be set"), while
        ``session`` as a CONTENT object KEY is legal. Each call appends a DISTINCT
        row — a trace is an append-only event, never keyed/deduped. The async
        fire-and-forget EMISSION that schedules these writes, and the aggregates
        over the rows, are a later serving-layer phase (P8d).

        Args:
            tool: The tool name that was served (e.g. ``"lore_search"``).
            params_hash: A stable digest of the call's parameters.
            hit_count: How many results the call returned.
            latency_ms: The call's wall-clock latency in milliseconds; fractional
                is preserved (the column is ``number``, not ``int``).
            session: The fleet/session identity that issued the call.
            token_cost: Optional per-call token accounting; omitted stores NONE.
            model: Optional model that produced the call; omitted stores NONE.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: The engine rejected the write (a domain/schema
                rejection); the healthy connection is left untouched.
        """
        content: dict[str, Any] = {
            TRACE_TOOL_FIELD: tool,
            TRACE_PARAMS_HASH_FIELD: params_hash,
            TRACE_HIT_COUNT_FIELD: hit_count,
            TRACE_LATENCY_MS_FIELD: latency_ms,
            TRACE_SESSION_FIELD: session,
        }
        # Omit the optional accounting columns when unset so the ``option`` fields
        # store NONE cleanly (a caller that skips accounting never poisons the row).
        if token_cost is not None:
            content[TRACE_TOKEN_COST_FIELD] = token_cost
        if model is not None:
            content[TRACE_MODEL_FIELD] = model
        await self._query(f"CREATE {TRACE_TABLE} CONTENT $content", {"content": content})

    async def trace_aggregates(self) -> list[dict[str, Any]]:
        """Return per-tool call counts + each tool's latest trace timestamp.

        ONE bounded ``GROUP BY`` aggregate over the whole ``trace`` table (P8d
        Wave 3 — the "later serving-layer phase" the :meth:`record_trace`
        docstring flagged): ``count()`` per group is the call count,
        ``time::max(ts)`` per group is that tool's most recent trace instant.
        Live-verified against the project's pinned SurrealDB (3.1.5): ``count()``
        + ``time::max()`` combine correctly under ``GROUP BY`` for a ``datetime``
        column, whereas ``math::max()``/``array::max()`` do NOT (they silently
        return ``-inf``/``[None, ...]`` on a datetime field) — ``time::max`` is
        the only correct choice here.

        Returns:
            One row per distinct ``tool`` that has EVER traced, each
            ``{"tool": str, "calls": int, "latest": datetime}`` (``latest`` is a
            tz-aware :class:`datetime.datetime`, the same native-object idiom
            :meth:`record_trace` writes); ``[]`` for an empty trace table
            (nothing recorded yet) — never an error. Row order is NOT
            guaranteed; the caller sorts if it needs determinism.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: The engine rejected the read (a domain fault).
        """
        return self._as_rows(
            await self._query(
                f"SELECT {TRACE_TOOL_FIELD} AS tool, count() AS calls, "
                f"time::max({TRACE_TS_FIELD}) AS latest "
                f"FROM {TRACE_TABLE} GROUP BY {TRACE_TOOL_FIELD}"
            )
        )

    def replace_file_fragment(
        self,
        tier: str,
        file_path: str,
        records_with_vectors: Sequence[tuple[Record, list[float]]],
    ) -> TxnFragment:
        """Build the transaction fragment that atomically replaces a file's chunks.

        A PURE builder (no I/O): it validates every vector's width and reshapes
        each production-shaped payload into the schema's row shape at BUILD time —
        so a wrong-width vector (:class:`VectorDimensionError`) or a reserved
        metadata key (:class:`SurrealStoreError` from :meth:`_split_payload`) is
        rejected LOUDLY here, before anything is composed or applied. The fragment
        DELETEs every existing chunk of ``(tier, file_path)`` and UPSERTs the new
        ones; composed into a single transaction (see :meth:`apply`) that DELETE +
        UPSERT set is what makes a concurrent reader observe only the complete pre-
        or post-replace state. Every param is namespaced with
        :data:`CHUNK_FRAGMENT_PARAM_PREFIX` so it never collides with a sibling
        producer's params in the merged transaction.

        Args:
            tier: The tier whose copy of the file is being replaced.
            file_path: The file path being replaced.
            records_with_vectors: The new ``(Record, vector)`` pairs (may be empty
                — the DELETE still runs, purging any stale chunks).

        Returns:
            The chunk-replace :class:`TxnFragment` (a DELETE followed by the
            per-record UPSERTs), carrying no ``BEGIN``/``COMMIT`` of its own.

        Raises:
            VectorDimensionError: Any vector is the wrong width (nothing is built).
            SurrealStoreError: A payload carries a reserved key that cannot be
                round-tripped faithfully.
        """
        self._validate_dimensions(records_with_vectors)
        prefix = CHUNK_FRAGMENT_PARAM_PREFIX
        tier_param, file_param = f"{prefix}tier", f"{prefix}file"
        params: dict[str, Any] = {tier_param: tier, file_param: file_path}
        statements = [
            f"DELETE {CHUNK_TABLE} WHERE tier = ${tier_param} AND file_path = ${file_param}"
        ]
        for index, (record, vector) in enumerate(records_with_vectors):
            id_param = f"{prefix}id{index}"
            content_param = f"{prefix}content{index}"
            params[id_param] = record.point_id
            params[content_param] = self._chunk_content(record, vector)
            statements.append(
                f"UPSERT type::record('{CHUNK_TABLE}', ${id_param}) CONTENT ${content_param}"
            )
        return TxnFragment(statements=statements, params=params)

    def delete_file_fragment(self, tier: str, file_path: str) -> TxnFragment:
        """Build the fragment that purges every chunk of ``(tier, file_path)``.

        The composable counterpart to :meth:`delete_by_file`, tier- and
        file-scoped so a custom override of a community file purges only the named
        tier's copy. A pair with no chunks composes to a harmless no-op DELETE.
        """
        prefix = CHUNK_FRAGMENT_PARAM_PREFIX
        tier_param, file_param = f"{prefix}tier", f"{prefix}file"
        return TxnFragment(
            statements=[
                f"DELETE {CHUNK_TABLE} WHERE tier = ${tier_param} AND file_path = ${file_param}"
            ],
            params={tier_param: tier, file_param: file_path},
        )

    def file_text_fragment(
        self, tier: str, file_path: str, text: str, sha512: str
    ) -> TxnFragment:
        """Build the fragment that stores a file's VERBATIM body + its SHA-512.

        The NEW ``file_text`` writer: the row is keyed by the SAME
        ``[tier, file_path]`` composite id discipline the ``file`` manifest table
        uses (via ``type::record``), so a tier override and the community original
        of one path coexist rather than the second overwriting the first. UPSERT so
        a re-index of the same path overwrites in place (idempotent). Params are
        namespaced with :data:`FILE_TEXT_FRAGMENT_PARAM_PREFIX`.

        A PURE builder (no I/O): ``text``'s UTF-8 byte length is checked against
        :data:`FILE_TEXT_MAX_BYTES` at BUILD time, so an oversized body is
        refused LOUDLY here, before anything is composed or applied.

        Args:
            tier: The tier the body belongs to.
            file_path: The file path within the tier.
            text: The verbatim source body to store unmodified.
            sha512: The body's SHA-512 hex digest (shared with the manifest row —
                never a hand-copied twin).

        Returns:
            The ``file_text`` UPSERT :class:`TxnFragment`.

        Raises:
            SurrealStoreError: ``text``'s UTF-8 byte length exceeds
                :data:`FILE_TEXT_MAX_BYTES`.
        """
        body_bytes = len(text.encode("utf-8"))
        if body_bytes > FILE_TEXT_MAX_BYTES:
            raise SurrealStoreError(
                f"file_text body for {file_path!r} is {body_bytes} bytes, "
                f"exceeding the {FILE_TEXT_MAX_BYTES}-byte cap — refused before "
                f"anything was composed or sent to the server"
            )
        prefix = FILE_TEXT_FRAGMENT_PARAM_PREFIX
        id_param, content_param = f"{prefix}id", f"{prefix}content"
        return TxnFragment(
            statements=[
                f"UPSERT type::record('{FILE_TEXT_TABLE}', ${id_param}) CONTENT ${content_param}"
            ],
            params={
                id_param: [tier, file_path],
                content_param: {_FILE_TEXT_TEXT_KEY: text, _FILE_TEXT_SHA_KEY: sha512},
            },
        )

    def file_text_delete_fragment(self, tier: str, file_path: str) -> TxnFragment:
        """Build the fragment that removes the ``file_text`` body of one path.

        Tier-scoped like :meth:`file_text_fragment`; the composable counterpart a
        full-file purge composes alongside the chunk / manifest / graph deletes.
        """
        prefix = FILE_TEXT_FRAGMENT_PARAM_PREFIX
        id_param = f"{prefix}id"
        return TxnFragment(
            statements=[f"DELETE type::record('{FILE_TEXT_TABLE}', ${id_param})"],
            params={id_param: [tier, file_path]},
        )

    async def apply(self, fragments: Sequence[TxnFragment]) -> None:
        """Compose ``fragments`` into ONE transaction and run it atomically.

        The correctness-critical heart of the per-file update: the store's OWN
        signed-in connection runs a single ``BEGIN … COMMIT`` spanning every
        producer's fragment (chunks + ``file_text`` body + manifest row + code
        graph). Because a SurrealDB transaction is connection-scoped, running all
        four producers' fragments through THIS connection is exactly what makes
        the update atomic across all four tables — a concurrent reader on another
        connection never observes a half-applied file, and one rejected statement
        rolls the WHOLE thing back (the manifest/graph instances that produced the
        fragments read the committed rows back over their own connections).

        The composed transaction's size is logged (statement + param counts) and a
        WARNING is emitted above :data:`~loremaster.store._txn.
        TXN_STATEMENT_WARN_THRESHOLD` — the guard against an accidentally-huge
        batch. Runs through the shared :func:`~loremaster.store._txn.
        execute_transaction`, which verifies EVERY statement's status (never the
        SDK's first-statement-only ``query()``) and self-heals a transport failure.

        Args:
            fragments: The producer fragments to apply as one transaction (at
                least one — an empty apply names no work and raises ``ValueError``
                from :func:`~loremaster.store._txn.compose`).

        Raises:
            ValueError: No fragments were given.
            TxnParamCollisionError: Two fragments bound the same param name.
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: The transaction was rejected/rolled back
                server-side; nothing is left half-applied.
        """
        statement_text, merged_params = compose(*fragments)
        statement_count = sum(len(fragment.statements) for fragment in fragments)
        self._log_transaction_size(statement_count, len(merged_params))
        await execute_transaction(
            statement_text,
            merged_params,
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )

    @staticmethod
    def _log_transaction_size(statement_count: int, param_count: int) -> None:
        """Emit the transaction-size telemetry, WARNing above the ceiling.

        A DEBUG record for a normal-sized transaction; a WARNING once the body
        statement count crosses :data:`~loremaster.store._txn.
        TXN_STATEMENT_WARN_THRESHOLD`, so a runaway batch is visible before it
        strains the engine. Both records carry ``statement_count`` / ``param_count``
        as structured fields.
        """
        extra = {"statement_count": statement_count, "param_count": param_count}
        if statement_count > TXN_STATEMENT_WARN_THRESHOLD:
            logger.warning("store.apply.large_transaction", extra=extra)
        else:
            logger.debug("store.apply.transaction", extra=extra)

    async def replace_file(
        self,
        tier: str,
        file_path: str,
        records_with_vectors: Sequence[tuple[Record, list[float]]],
    ) -> None:
        """Atomically replace a file's chunks in a single transaction.

        The self-contained chunk writer, now expressed over the ONE
        statement-producing path: it builds its :meth:`replace_file_fragment` and
        runs it through :meth:`apply`, so there is no second, drifting copy of the
        DELETE-then-UPSERT statement text. A concurrent reader on another
        connection only ever observes the complete pre- or post-replace state, and
        a mid-transaction rejection surfaces as a raised
        :class:`SurrealStoreError` (never a silent success).

        Args:
            tier: The tier whose copy of the file is being replaced.
            file_path: The file path being replaced.
            records_with_vectors: The new ``(Record, vector)`` pairs.

        Raises:
            VectorDimensionError: Any new vector is the wrong width (nothing runs).
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: The transaction was rejected/rolled back
                server-side (e.g. a type-coercion failure); nothing is left
                half-applied.
        """
        await self.apply([self.replace_file_fragment(tier, file_path, records_with_vectors)])

    # -- deletes ------------------------------------------------------------

    async def delete_by_file(self, tier: str, file_path: str) -> None:
        """Purge every chunk matching ``(tier, file_path)`` exactly.

        Scoped to the ``(tier, file_path)`` pair, so a custom override of a
        community file purges only the named tier's copy. A pair with no chunks
        is a harmless no-op. Expressed over the ONE statement-producing path:
        it composes its :meth:`delete_file_fragment` through :meth:`apply` rather
        than carrying a second, drifting copy of the DELETE text.
        """
        await self.apply([self.delete_file_fragment(tier, file_path)])

    async def delete_by_tier(self, tier: str) -> None:
        """Purge every chunk in ``tier`` — the per-tier rebuild primitive.

        A tier with no chunks is a harmless no-op.
        """
        await self._query(f"DELETE {CHUNK_TABLE} WHERE tier = $tier", {"tier": tier})

    async def delete_points(self, ids: Sequence[str]) -> None:
        """Purge exactly the named point ids — the upsert-before-purge enabler.

        A per-file update upserts the NEW chunks first, then purges only the
        STALE ids (``old − new``), keeping the fresh content continuously
        visible. An empty list issues no request (the common "nothing went
        stale" case).

        Args:
            ids: The exact bare point ids to delete.
        """
        if not ids:
            return
        record_ids = [RecordID(CHUNK_TABLE, point_id) for point_id in ids]
        await self._query(f"DELETE {CHUNK_TABLE} WHERE id IN $ids", {"ids": record_ids})

    # -- reads --------------------------------------------------------------

    async def count(self, tier: str | None = None) -> int:
        """Return the LIVE server-side chunk count — total or tier-scoped.

        Args:
            tier: When given, count only that tier (an absent tier counts 0);
                ``None`` returns the grand total.

        Returns:
            The live chunk count (never negative).
        """
        if tier is None:
            result = await self._query(f"SELECT count() FROM {CHUNK_TABLE} GROUP ALL")
        else:
            result = await self._query(
                f"SELECT count() FROM {CHUNK_TABLE} WHERE tier = $tier GROUP ALL",
                {"tier": tier},
            )
        return self._first_count(result)

    async def existing_point_ids(self, ids: Sequence[str]) -> set[str]:
        """Return the subset of ``ids`` that currently exist — the batch drift read.

        ONE query resolves N ids (``SELECT VALUE record::id(id) ... WHERE id IN
        $ids``), collapsing what would otherwise be N point-fetches: the memory
        backend's drift oracle asks this once per recall for every referenced
        chunk-key at once. The returned set is exactly the ids still present; the
        ids NOT in it have drifted (a refactor deleted the referenced chunk).
        Mirrors :meth:`delete_points`'s id-list idiom — each id is bound as a
        :class:`RecordID` under the ``chunk`` table, and the projection is
        ``record::id`` so the bare ids come back as plain strings
        (:class:`RecordID` is unhashable, so it can never enter the returned set).

        An empty ``ids`` issues NO request and returns the empty set (the common
        "this recall carried no refs" case). A DOWN server RAISES rather than
        silently reporting the whole batch missing — a silent empty set would be
        misread as "every ref was deleted".

        Args:
            ids: The BARE chunk point ids (``chunk_key``\\ s) to test for existence.

        Returns:
            The subset of ``ids`` that currently exist as chunk points.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: The engine rejected the read (a domain fault).
        """
        if not ids:
            return set()
        record_ids = [RecordID(CHUNK_TABLE, point_id) for point_id in ids]
        result = await self._query(
            f"SELECT VALUE record::id({_ID_KEY}) FROM {CHUNK_TABLE} WHERE {_ID_KEY} IN $ids",
            {"ids": record_ids},
        )
        values = result if isinstance(result, list) else []
        return {str(value) for value in values if value is not None}

    async def file_text(self, tier: str, file_path: str) -> dict[str, str] | None:
        """Return the stored ``{text, sha512}`` body of ``(tier, file_path)``, or ``None``.

        The read counterpart to :meth:`file_text_fragment`: a bounded, FILTER-ONLY
        keyed lookup of the one ``file_text`` row addressed by the SAME
        ``[tier, file_path]`` composite record id the writer keys on (via
        ``type::record``), so a tier override and the community original of one
        path never collide. The row's verbatim ``text`` and its ``sha512`` come
        back together; nothing matching yields ``None``.

        Rides the store's self-healing, error-classifying :meth:`_query` seam (a
        transport failure self-heals and raises :class:`SurrealConnectionError`; a
        domain rejection keeps the healthy connection and raises
        :class:`SurrealStoreError`), and binds the composite id as a parameter —
        caller input is NEVER interpolated into the statement text.

        Args:
            tier: The tier whose copy of the file to read.
            file_path: The file path within the tier.

        Returns:
            ``{"text": <verbatim body>, "sha512": <digest>}`` for the stored row,
            or ``None`` when no ``file_text`` row exists for the pair.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: The engine rejected the read (a domain fault), OR the
                stored row is PARTIAL — it exists but is missing (or NULL for) its
                ``text``/``sha512`` column (an out-of-band / legacy corruption the
                faithful ``file_text_fragment`` writer can never produce). A partial
                row is refused with a typed, laundered store error (naming only the
                tier/path, never the row body) rather than a bare ``KeyError`` or a
                silent ``None`` that would flow downstream as a phantom integrity
                failure.
        """
        rows = self._as_rows(
            await self._query(
                f"SELECT {_FILE_TEXT_TEXT_KEY}, {_FILE_TEXT_SHA_KEY} "
                f"FROM type::record('{FILE_TEXT_TABLE}', $id)",
                {"id": [tier, file_path]},
            )
        )
        if not rows:
            return None
        row = rows[0]
        # A partial row (an explicit projection yields the column as NULL, a
        # ``SELECT *`` omits the key entirely) is refused loudly and store-typed —
        # ``.get(...) is None`` catches both shapes. The message names the tier/path
        # and the diagnosis, never the (possibly sensitive) row body.
        text = row.get(_FILE_TEXT_TEXT_KEY)
        sha512 = row.get(_FILE_TEXT_SHA_KEY)
        if text is None or sha512 is None:
            raise SurrealStoreError(
                f"file_text row for {file_path!r} in tier {tier!r} is a partial "
                f"file_text row (missing its {_FILE_TEXT_TEXT_KEY!r}/"
                f"{_FILE_TEXT_SHA_KEY!r} column) — refusing to serve an incomplete row"
            )
        return {
            _FILE_TEXT_TEXT_KEY: text,
            _FILE_TEXT_SHA_KEY: sha512,
        }

    async def scroll(self, filters: dict[str, str], limit: int) -> list[dict[str, Any]]:
        """Return the chunk rows matching ``filters`` — a bounded FILTER-ONLY lookup.

        A pure payload-filter lookup with NO query vector (the ``get_symbol``
        path): all supplied conditions AND together. The heavy ``embedding`` is
        omitted from the projection. Nothing matching yields ``[]``.

        Args:
            filters: Field → exact-value conditions, AND-combined. Each KEY is
                validated against the chunk-column allow-list at the trust
                boundary before any query is built (SurrealQL-injection defense);
                values are always bound as parameters.
            limit: The maximum number of rows to return — a REQUIRED bound,
                emitted as a bound ``LIMIT`` param so a scroll is never unbounded.

        Returns:
            The matching rows (payload fields, embedding omitted), at most
            ``limit`` of them, in DETERMINISTIC ascending record-id order (an
            explicit ``ORDER BY`` — never left to engine iteration order); ``[]``
            when nothing matches.

        Raises:
            SurrealStoreError: A filter key is not an allowed chunk filter column.
        """
        where, params = self._build_where(filters)
        statement = f"SELECT * OMIT {_EMBEDDING_KEY} FROM {CHUNK_TABLE}"
        if where:
            statement += f" WHERE {where}"
        statement += f" ORDER BY {_ID_KEY} LIMIT ${_LIMIT_PARAM}"
        params[_LIMIT_PARAM] = limit
        rows = self._as_rows(await self._query(statement, params))
        return [self._normalize_row(row) for row in rows]

    async def hybrid_search(
        self,
        *,
        query_vector: list[float],
        query_text: str,
        k: int,
        filters: dict[str, str] | None = None,
    ) -> list[Candidate]:
        """One-query hybrid retrieval: HNSW vector ⊕ BM25 FULLTEXT via RRF.

        The vector arm and the (identifier-tokenized) BM25 arm each overfetch
        under the same optional filter, and the engine's native ``search::rrf``
        fuses them to the final ``k``. A healthy but empty/no-match store returns
        ``[]``; a DOWN server RAISES (never a silent empty).

        ``k`` (and the derived overfetch / EF), plus the query text length and
        token count, are clamped to the store-level ceilings before being spliced
        into the query — a DoS guard (an unclamped huge ``k`` crashed the engine).

        Args:
            query_vector: The query embedding (same width as the store's ``dim``).
            query_text: The natural query; identifier-shaped text is tokenized
                via the engine analyzer before matching (the BM25-rescue step).
            k: The maximum number of fused results (clamped to
                :data:`_MAX_HYBRID_K`).
            filters: Optional field → exact-value scope (e.g. ``{"tier": …}``),
                applied inside both arms; each KEY is allow-list-validated.

        Returns:
            Up to ``k`` fused :class:`Candidate` hits, keyed by bare point id.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
            SurrealStoreError: A filter key is not an allowed chunk filter column.
        """
        # Establish the connection first so a down server RAISES here, before any
        # search work — never a silent empty result.
        await self._ensure_connection()

        # Validate + scope the filter at the trust boundary: a hostile filter key
        # raises here, before any query is built (the injection defense).
        filter_where, params = self._build_where(filters or {})

        # DoS guard: clamp ``k`` before it drives the overfetch, the EF search
        # list and the rrf arity (an unclamped huge ``k`` overran the engine's
        # HNSW allocation and crashed the server). EF must cover the overfetch, so
        # both share the same practical ceiling.
        k = min(k, _MAX_HYBRID_K)
        overfetch = min(max(k * _OVERFETCH_FACTOR, k), _MAX_HNSW_EF)
        ef = min(max(overfetch, _MIN_HNSW_EF), _MAX_HNSW_EF)

        # The vector arm: an overfetching HNSW KNN under the shared filter.
        params[_QUERY_VECTOR_PARAM] = query_vector
        vector_subquery = self._vector_subquery(filter_where, overfetch, ef)

        # The BM25 arm: cap the query text (DoS guard), identifier-tokenize it via
        # the analyzer round-trip, cap the token count, then OR the word tokens
        # under the same filter.
        tokens = await self._analyze_query(query_text[:_MAX_QUERY_TEXT_CHARS])
        fulltext_predicate, fulltext_params = self._build_fulltext_predicate(
            tokens[:_MAX_QUERY_TOKENS]
        )
        params.update(fulltext_params)
        fulltext_subquery = self._fulltext_subquery(filter_where, fulltext_predicate)

        # Fuse both arms server-side with the engine's native RRF and run (through
        # the self-healing ``_query`` seam).
        statement = self._hybrid_statement(vector_subquery, fulltext_subquery, k)
        return self._to_candidates(await self._query(statement, params))

    # -- hybrid-search query construction ----------------------------------

    @staticmethod
    def _vector_subquery(filter_where: str, overfetch: int, ef: int) -> str:
        """The HNSW arm: an overfetching ``<|K,EF|>`` KNN under the filter.

        The KNN operator may not be nested in ``OR``/``NOT``, so the filter is
        AND-ed ahead of it.
        """
        conditions = []
        if filter_where:
            conditions.append(filter_where)
        conditions.append(f"{_EMBEDDING_KEY} <|{overfetch},{ef}|> ${_QUERY_VECTOR_PARAM}")
        return f"SELECT * FROM {CHUNK_TABLE} WHERE {' AND '.join(conditions)}"

    @staticmethod
    def _fulltext_subquery(filter_where: str, fulltext_predicate: str) -> str:
        """The BM25 arm: the token OR-predicate under the same filter."""
        conditions = []
        if filter_where:
            conditions.append(filter_where)
        conditions.append(fulltext_predicate)
        return f"SELECT * FROM {CHUNK_TABLE} WHERE {' AND '.join(conditions)}"

    @staticmethod
    def _hybrid_statement(vector_subquery: str, fulltext_subquery: str, k: int) -> str:
        """The final fused ``SELECT`` — both arms combined via ``search::rrf``.

        ``search::rrf`` accepts only INLINE subqueries (see module docstring), so
        the two arms are spliced directly into the call rather than bound as
        params. ``k`` is the caller's already-clamped fused result cap.
        """
        return (
            f"SELECT * OMIT {_EMBEDDING_KEY} FROM "
            f"search::rrf([({vector_subquery}), ({fulltext_subquery})], {int(k)}, {_RRF_K})"
        )

    async def _analyze_query(self, query_text: str) -> list[str]:
        """Tokenize ``query_text`` with the engine's own ``code_ident`` analyzer.

        Reusing the server-side analyzer (rather than a hand-rolled splitter)
        guarantees the query tokens match the way indexed text was tokenized.
        Punctuation-only tokens (``.``/``_``) — which ``@@``'s conjunctive match
        would otherwise require and never find — are dropped, leaving the word
        tokens the BM25 rescue ORs together. Runs through the self-healing
        :meth:`_query` seam so a mid-life socket drop heals here too.

        Args:
            query_text: The raw (already length-capped) query string.

        Returns:
            The lower-cased word tokens (punctuation tokens removed).

        Note:
            Every :meth:`hybrid_search` call makes this analyzer round-trip even
            when a caller repeats the same ``query_text``. The result is a pure
            function of ``(self._analyzer_name, query_text)`` so a per-store
            cache is theoretically safe, but sizing/eviction it correctly (a
            bounded ``cachetools.TTLCache``, not an unbounded dict) is real
            design surface with its own test coverage — deferred as a P6
            optimization rather than folded into this refactor.
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
        """Build the BM25 OR-predicate (and its params) over the word tokens.

        Each token is matched against every searchable field with ``@@`` and all
        matches are ORed, so a chunk containing ANY token surfaces via BM25 (the
        rescue). With no word tokens the predicate matches nothing, leaving the
        vector arm to carry the fusion alone.

        Returns:
            ``(predicate, params)`` — the WHERE fragment and its bound tokens.
        """
        if not tokens:
            return _NO_MATCH_PREDICATE, {}
        clauses: list[str] = []
        params: dict[str, Any] = {}
        for index, token in enumerate(tokens):
            param = f"__ft{index}"
            params[param] = token
            clauses += [f"{field} @@ ${param}" for field in _FULLTEXT_FIELDS]
        return "(" + " OR ".join(clauses) + ")", params

    # -- result / filter helpers -------------------------------------------

    @staticmethod
    def _build_where(filters: dict[str, str]) -> tuple[str, dict[str, Any]]:
        """Build an AND-combined equality WHERE fragment and its params.

        Every filter KEY is validated against :data:`_ALLOWED_FILTER_KEYS` (the
        schema's chunk-column allow-list) BEFORE any clause is built, so an
        unknown/hostile key raises :class:`SurrealStoreError` and never reaches a
        query — the SurrealQL statement-injection defense. Values are always
        bound as parameters (safe as data, even when hostile).

        Args:
            filters: Field → exact-value conditions, AND-combined.

        Returns:
            ``(where_fragment, params)`` — the fragment is ``""`` when there are
            no filters.

        Raises:
            SurrealStoreError: A filter key is not an allowed chunk filter column.
        """
        # Validate EVERY key up front, before any clause is built, so a hostile
        # key can never be interpolated into a statement that then executes.
        for field in filters:
            if field not in _ALLOWED_FILTER_KEYS:
                raise SurrealStoreError(
                    f"illegal filter key {field!r}: not an allowed chunk filter column "
                    f"(allowed: {sorted(_ALLOWED_FILTER_KEYS)})"
                )
        clauses: list[str] = []
        params: dict[str, Any] = {}
        for index, (field, value) in enumerate(filters.items()):
            param = f"__f{index}"
            clauses.append(f"{field} = ${param}")
            params[param] = value
        return " AND ".join(clauses), params

    @staticmethod
    def _first_count(result: Any) -> int:
        """Extract the ``count`` from a ``SELECT count() … GROUP ALL`` result."""
        if isinstance(result, list) and result:
            row = result[0]
            if isinstance(row, dict):
                return int(row.get(_COUNT_KEY, 0))
        return 0

    @staticmethod
    def _as_rows(result: Any) -> list[dict[str, Any]]:
        """Narrow a ``SELECT`` result to its list of dict rows."""
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    @staticmethod
    def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
        """Reconcile an internal row back to the canonical production shape.

        The read-side mirror of :meth:`_split_payload`: spreads the
        ``metadata`` column's contents top-level and drops the wrapper key,
        so every returned row/payload matches exactly what
        ``records.chunk_to_record`` would have produced — no ``"metadata"``
        key ever survives to a caller. On a name collision (only reachable
        from adversarial/legacy input — a faithful write via
        :meth:`_chunk_content` can never produce one, since a declared
        column's value is never also duplicated into the metadata bucket),
        the declared column's own value wins.

        Args:
            row: A raw row/payload as stored (may carry ``id``/other SDK
                fields alongside the chunk columns and ``metadata``).

        Returns:
            ``row`` with ``metadata``'s contents merged top-level and the
            ``"metadata"`` key itself removed.
        """
        metadata = row.get(_METADATA_KEY)
        rest = {key: value for key, value in row.items() if key != _METADATA_KEY}
        if isinstance(metadata, dict) and metadata:
            # ``rest`` is applied LAST so a declared column's real value wins
            # over a same-named metadata key on the (adversarial-only) clash.
            return {**metadata, **rest}
        return rest

    def _to_candidates(self, result: Any) -> list[Candidate]:
        """Turn fused ``search::rrf`` rows into neutral :class:`Candidate`s.

        Each row's bare point id becomes the key, ``rrf_score`` the score, and
        the remaining chunk fields the payload; the origin is always ``fused``.
        The result is sorted deterministically (score descending, then key) so
        identical calls never shuffle — see below.
        """
        candidates: list[Candidate] = []
        for row in self._as_rows(result):
            payload = self._normalize_row(
                {
                    field: value
                    for field, value in row.items()
                    if field not in (_ID_KEY, _RRF_SCORE_KEY)
                }
            )
            candidates.append(
                Candidate(
                    key=self._bare_id(row.get(_ID_KEY)),
                    score=float(row.get(_RRF_SCORE_KEY, 0.0)),
                    payload=payload,
                    origin=_FUSED_ORIGIN,
                )
            )
        # ``search::rrf`` returns equal-scored rows in an arbitrary order, so a
        # stable, deterministic sort (score descending, then key ascending) is
        # imposed here: two identical calls must yield an identical ordering
        # (pagination/caching coherence) while best-first relevance is kept.
        candidates.sort(key=lambda candidate: (-candidate.score, candidate.key))
        return candidates

    @staticmethod
    def _bare_id(raw: Any) -> str:
        """Return the BARE point id — no ``chunk:`` record-table prefix.

        The SDK returns a chunk id as a :class:`RecordID` whose ``.id`` is the
        bare ``uuid5`` string; a stringified fallback strips any ``table:`` prefix.
        """
        if isinstance(raw, RecordID):
            return str(raw.id)
        text = str(raw)
        if _TABLE_SEPARATOR in text:
            return text.split(_TABLE_SEPARATOR, 1)[1]
        return text
