"""Async SurrealDB manifest — the P3 port of the SQLite ``Manifest`` onto the
P2 unified store's ``file`` + ``meta`` tables.

The manifest stays the authority on per-file, per-tier indexing state (see
``loremaster.index.manifest`` for the amendment history — C1 composite
identity, the mtime+size fast path, the atomic ``replace``). This module keeps
that exact behavioural contract while trading the SQLite file + WAL for a
SurrealDB database reached over the async SDK, matching
:class:`~loremaster.store.surreal.SurrealStore`'s connection lifecycle and
self-heal idioms.

Storage-shape decisions, pinned by the P2 DDL (``surreal_schema.py``) and the
GREEN-phase probes that verified them against the live 3.1.5 engine:

* **Composite record id.** The ``file`` table carries no ``tier``/``file_path``
  columns — those two values live entirely in the record id itself, as a
  two-element array: ``file:[tier, file_path]``. A row is addressed with
  ``type::record('file', $id)`` where ``$id`` is bound as ``[tier,
  file_path]``, and a tier scope is expressed as the predicate ``id[0] =
  $tier`` (verified live: array-indexing a record id in a ``WHERE`` clause
  resolves correctly and composes with ``AND``).
* **``chunk_ids`` is ``array<string>``, no translation layer.** The DDL
  already types it as bare strings (not ``array<record<chunk>>``), so the
  manifest reads/writes it as a plain ``list[str]`` — a caller's uuid5 ids
  round-trip byte-identical, with no record-ref wrapper to strip.
* **``updated_at`` is a native SurrealDB ``datetime``, not a stored ISO
  string.** The DDL types the column ``datetime``; the SDK maps a Python
  ``datetime`` object to it directly. The public :class:`FileRow` contract
  still carries ``updated_at`` as ``str`` (the SQLite manifest's shape), so
  this module converts on read via ``.isoformat()``.
* **``meta`` is upserted by key, not by record id.** A meta key (e.g.
  ``"tier_version:community"``) is not naturally a record id's shape, so
  ``meta.k``/``meta.v`` are ordinary fields backed by a UNIQUE index on ``k``
  (``surreal_schema._meta_statements``), and ``meta_set`` uses
  ``UPSERT meta SET k = $k, v = $v WHERE k = $k`` — verified live to create
  the row on the first call and find/overwrite that SAME row (matched via the
  unique index) on every subsequent call, the exact "insert or overwrite by
  key" semantics ``meta(k PRIMARY KEY, v)`` had in SQLite.

Critical dialect gotcha this module works around (see
:func:`~loremaster.store._txn.execute_transaction`): a multi-statement
``BEGIN … COMMIT`` run through the SDK's plain ``query()`` call only inspects
the FIRST statement's per-statement status before deciding whether to raise —
verified live that a LATER statement's ``ASSERT`` violation rolls the
transaction back server-side while ``query()`` returns ``None`` with **no
exception at all**. :meth:`replace` therefore never uses plain ``query()``; it
goes through the shared :func:`~loremaster.store._txn.execute_transaction`,
which uses the lower-level ``query_raw()`` and inspects every statement's
``status`` itself, raising :class:`~loremaster.store.surreal.SurrealStoreError`
the moment any statement in the transaction failed — so a caller can never
observe the "silent success" the SDK's own ``query()`` would otherwise report.

**Shared with the store — the extraction.** The per-statement transaction
check and the transport-vs-domain error classification are NOT private to this
module: the identical gap exists in
:meth:`~loremaster.store.surreal.SurrealStore.replace_file` (it commits its own
multi-statement ``BEGIN … COMMIT``), and the single-statement ``_query`` seam
of BOTH classes must tell a genuine transport failure apart from a domain
rejection. Both concerns route through the ONE audited implementation in
:mod:`loremaster.store._txn` — :func:`~loremaster.store._txn.execute_transaction`
for the transaction, :func:`~loremaster.store._txn.run_query` for the
single-statement attempt (blindreader F3: the classify-and-signal decision
lives INSIDE that shared function now, not re-derived per seam) — so the two
can never drift apart again.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from surrealdb import AsyncSurreal

from loremaster.index.manifest import FileRow
from loremaster.store._txn import (
    TxnContentionExhaustedError,
    TxnFragment,
    bootstrap_session,
    compose,
    execute_transaction,
    run_query,
)
from loremaster.store.surreal import (
    _CONNECTION_ERRORS,
    _SIGNIN_PASS_KEY,
    _SIGNIN_USER_KEY,
    SurrealConnectionError,
    _SurrealConnection,
)
from loremaster.store.surreal_schema import FILE_TABLE, META_TABLE, generate_manifest_ddl

logger = logging.getLogger(__name__)

# The lifecycle states a file row may occupy — must agree with the DDL's
# closed domain (``surreal_schema.FILE_STATES``); a drift guard test pins this.
STATE_INDEXED = "indexed"
STATE_DIRTY = "dirty"
STATE_EMBEDDING = "embedding"
STATE_FAILED = "failed"

# The producer-namespacing prefix the manifest stamps on the bound params of
# the transaction fragment it builds, so its ``file``-row params never clobber
# a sibling producer's (chunk / file_text / graph) params in a composed
# per-file transaction (see :func:`~loremaster.store._txn.compose`). ``mf_`` =
# the ManiFest row.
MANIFEST_FRAGMENT_PARAM_PREFIX = "mf_"

# Keys the SDK adds to a returned row that are NOT part of the stored payload.
_ID_KEY = "id"

# The aggregate-projection aliases used by the ``GROUP ALL`` reads below.
_SUM_ALIAS = "total"
_COUNT_ALIAS = "count"


class SurrealManifest:
    """Async manifest over a single per-project SurrealDB database.

    Owns its OWN connection (mirroring :class:`~loremaster.store.surreal.
    SurrealStore`'s construction and lifecycle) rather than sharing the
    indexer's live store connection — a P3 trade-off, not a decision this
    module revisits. The connection is opened lazily and cached; a
    connection-class failure during an operation drops the cached handle so
    the next call transparently reconnects (the mid-life self-heal).

    Args:
        url: The SurrealDB RPC URL (e.g. ``ws://127.0.0.1:18000/rpc``).
        namespace: The namespace the database lives under.
        database: The per-project database name.
        user: The root/username to sign in with.
        password: The password to sign in with.
    """

    def __init__(
        self,
        *,
        url: str,
        namespace: str,
        database: str,
        user: str,
        password: str,
    ) -> None:
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        # Opened on first use; ``None`` means "not yet connected / closed".
        self._connection: _SurrealConnection | None = None
        # Guards the connect-time check-then-set below (mirrors
        # ``SurrealStore._connect_lock``): without it, N concurrent
        # first-callers on a fresh instance all pass the
        # ``self._connection is not None`` check before any of them finishes
        # connecting, each opening its OWN underlying SDK connection. Safe to
        # construct here (unbound to any running loop) on Python >= 3.10.
        self._connect_lock = asyncio.Lock()

    # -- connection lifecycle ------------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking (mirrors
        :meth:`~loremaster.store.surreal.SurrealStore._ensure_connection`):
        the fast path (already connected) never touches the lock. The session
        bootstrap is :func:`~loremaster.store._txn.bootstrap_session` — the
        ONE shared implementation every connection owner in the package calls
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
                await bootstrap_session(connection, self._namespace, self._database)
            except TxnContentionExhaustedError as error:
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): "
                    f"the session bootstrap exhausted its retry budget"
                ) from error
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
                "manifest.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect and apply the manifest's schema slice — idempotent.

        Applies ONLY the ``file`` + ``meta`` DDL (:func:`generate_manifest_ddl`)
        — this manifest owns no embedder ``dim``/analyzer configuration, unlike
        :class:`~loremaster.store.surreal.SurrealStore`, so it never needs the
        full store DDL to create its two tables. Applied inside ONE ``BEGIN …
        COMMIT`` transaction via :func:`~loremaster.store._txn.execute_transaction`,
        which inspects EVERY statement's status — the SDK's plain ``query()``
        inspects only the FIRST statement, so a LATER statement's rejection
        would otherwise roll the whole schema back server-side while
        ``query()`` raised nothing at all (verified live).

        Raises:
            SurrealConnectionError: The server is unreachable, rejected auth, or
                the socket died mid-apply.
            SurrealStoreError: Any DDL statement was rejected by the engine (a
                real schema bug); the connection stays healthy.
        """
        await self._ensure_connection()
        ddl = generate_manifest_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("manifest.schema.ready", extra={"database": self._database})

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
        callback) — mirrors :meth:`SurrealStore._drop_connection`.
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
            logger.debug("manifest.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection.

        Delegates to :func:`~loremaster.store._txn.run_query` — the ONE shared
        attempt body every single-statement seam in the package now calls
        (blindreader F3; see its docstring for the classify/self-heal/log
        mechanism, including its RETRYABLE-conflict path, finding #120/#108).
        """
        return await run_query(
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
            noun="query",
            label="manifest.query.rejected",
            statement=statement,
            params=params or {},
            logger=logger,
        )

    # -- record-id / row helpers ---------------------------------------------

    @staticmethod
    def _record_id(tier: str, file_path: str) -> list[str]:
        """The composite ``[tier, file_path]`` array bound as a record id."""
        return [tier, file_path]

    @staticmethod
    def _now() -> datetime:
        """The current UTC time as a timezone-aware ``datetime``.

        Bound directly as the ``updated_at`` param — the DDL types that column
        ``datetime``, so the SDK's native Python-datetime mapping is used
        rather than a stored ISO string (contrast with the SQLite manifest,
        which stores ``updated_at`` as TEXT).
        """
        return datetime.now(UTC)

    @staticmethod
    def _as_rows(result: Any) -> list[dict[str, Any]]:
        """Narrow a ``SELECT``-shaped result to its list of dict rows."""
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    @staticmethod
    def _row_to_model(row: dict[str, Any]) -> FileRow:
        """Decode a raw ``file`` row into a :class:`FileRow`.

        ``tier``/``file_path`` come from the composite record id (the table
        has no columns for them — see the module docstring); ``updated_at`` is
        converted from the stored native ``datetime`` to the ISO-8601 string
        the public :class:`FileRow` contract carries.
        """
        record_id = row[_ID_KEY]
        tier, file_path = record_id.id
        updated_at = row["updated_at"]
        return FileRow(
            tier=str(tier),
            file_path=str(file_path),
            sha512=row["sha512"],
            mtime_ns=row["mtime_ns"],
            size=row["size"],
            n_chunks=row["n_chunks"],
            chunk_ids=list(row["chunk_ids"]),
            state=row["state"],
            updated_at=updated_at.isoformat() if isinstance(updated_at, datetime) else str(updated_at),
        )

    # -- CRUD ------------------------------------------------------------

    async def get(self, tier: str, file_path: str) -> FileRow | None:
        """Return the row for ``(tier, file_path)``, or ``None`` if absent.

        Args:
            tier: The tier the file belongs to.
            file_path: The path to look up within the tier.

        Returns:
            The decoded :class:`FileRow`, or ``None``.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        rows = self._as_rows(
            await self._query(
                f"SELECT * FROM type::record('{FILE_TABLE}', $id)",
                {"id": self._record_id(tier, file_path)},
            )
        )
        return self._row_to_model(rows[0]) if rows else None

    async def all_files(self) -> list[FileRow]:
        """Return every file row, ordered by ``(tier, file_path)``.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        rows = self._as_rows(await self._query(f"SELECT * FROM {FILE_TABLE} ORDER BY id"))
        return [self._row_to_model(row) for row in rows]

    async def files_for_tier(self, tier: str) -> list[FileRow]:
        """Return every file row for ``tier``, ordered by path.

        Args:
            tier: The tier to list.

        Returns:
            The decoded rows for that tier.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        rows = self._as_rows(
            await self._query(
                f"SELECT * FROM {FILE_TABLE} WHERE id[0] = $tier ORDER BY id", {"tier": tier}
            )
        )
        return [self._row_to_model(row) for row in rows]

    async def upsert(
        self,
        *,
        tier: str,
        file_path: str,
        sha512: str,
        mtime_ns: int,
        size: int,
        n_chunks: int,
        chunk_ids: list[str],
        state: str,
    ) -> None:
        """Insert or overwrite the row for ``(tier, file_path)``.

        Args:
            tier: The tier the file belongs to.
            file_path: The file path within the tier.
            sha512: The file's SHA-512 hex digest.
            mtime_ns: The file's modification time, in nanoseconds.
            size: The file's size, in bytes.
            n_chunks: The number of chunks produced.
            chunk_ids: The point ids of those chunks (stored as a bare string
                array — no record-ref translation, see the module docstring).
            state: The lifecycle state.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        content = {
            "sha512": sha512,
            "mtime_ns": mtime_ns,
            "size": size,
            "n_chunks": n_chunks,
            "chunk_ids": chunk_ids,
            "state": state,
            "updated_at": self._now(),
        }
        await self._query(
            f"UPSERT type::record('{FILE_TABLE}', $id) CONTENT $content",
            {"id": self._record_id(tier, file_path), "content": content},
        )

    async def set_state(self, tier: str, file_path: str, state: str) -> None:
        """Transition ``(tier, file_path)`` to ``state`` (no-op if row absent).

        Args:
            tier: The tier the file belongs to.
            file_path: The file path to transition.
            state: The new lifecycle state.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
            SurrealStoreError: ``state`` violates the DDL's closed domain — a
                domain rejection, not a connection fault (see :meth:`_query`).
        """
        await self._query(
            f"UPDATE type::record('{FILE_TABLE}', $id) SET state = $state, updated_at = $now",
            {"id": self._record_id(tier, file_path), "state": state, "now": self._now()},
        )

    async def delete(self, tier: str, file_path: str) -> None:
        """Delete the row for ``(tier, file_path)`` (no-op if absent).

        Tier-scoped: the same path's rows under *other* tiers are untouched.

        Args:
            tier: The tier the file belongs to.
            file_path: The file path to delete within the tier.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        await self._query(
            f"DELETE type::record('{FILE_TABLE}', $id)", {"id": self._record_id(tier, file_path)}
        )

    async def needs_reindex(self, tier: str, file_path: str, mtime_ns: int, size: int) -> bool:
        """Decide whether ``(tier, file_path)`` must be re-indexed.

        Fast-path: a file already in the ``indexed`` state whose ``mtime_ns``
        and ``size`` are both unchanged needs no work. Anything else — an
        absent row (including the same path under a *different* tier), a
        changed mtime or size, or any non-``indexed`` state — must be
        re-attempted.

        Args:
            tier: The tier the file belongs to.
            file_path: The file to check within the tier.
            mtime_ns: The file's current modification time, in nanoseconds.
            size: The file's current size, in bytes.

        Returns:
            ``True`` if the file must be re-indexed, ``False`` otherwise.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        row = await self.get(tier, file_path)
        if row is None:
            return True
        if row.state != STATE_INDEXED:
            return True
        return row.mtime_ns != mtime_ns or row.size != size

    async def replace(
        self,
        *,
        tier: str,
        file_path: str,
        sha512: str,
        mtime_ns: int,
        size: int,
        n_chunks: int,
        chunk_ids: list[str],
        state: str,
    ) -> None:
        """Atomically replace the row for ``(tier, file_path)`` in one transaction.

        The old row is deleted and the new row created inside one ``BEGIN …
        COMMIT`` transaction, so a concurrent reader on another connection
        never observes a half-applied update (the engine's own snapshot
        isolation) and a failure mid-swap (e.g. an out-of-domain ``state``)
        rolls the whole thing back, leaving the prior row intact. Runs through
        the shared :func:`~loremaster.store._txn.execute_transaction`, which —
        unlike a bare ``query()`` call — surfaces a rolled-back transaction as a
        raised error (see the module docstring).

        Args:
            tier: The tier the file belongs to.
            file_path: The file path being replaced within the tier.
            sha512: The new SHA-512 hex digest.
            mtime_ns: The new modification time, in nanoseconds.
            size: The new size, in bytes.
            n_chunks: The new chunk count.
            chunk_ids: The new point ids.
            state: The new lifecycle state.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: The transaction was rejected/rolled back
                server-side (e.g. an out-of-domain ``state``); the prior row is
                left intact.
        """
        fragment = self.replace_fragment(
            tier=tier,
            file_path=file_path,
            sha512=sha512,
            mtime_ns=mtime_ns,
            size=size,
            n_chunks=n_chunks,
            chunk_ids=chunk_ids,
            state=state,
        )
        statement, params = compose(fragment)
        await execute_transaction(
            statement,
            params,
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )

    def replace_fragment(
        self,
        *,
        tier: str,
        file_path: str,
        sha512: str,
        mtime_ns: int,
        size: int,
        n_chunks: int,
        chunk_ids: list[str],
        state: str,
    ) -> TxnFragment:
        """Build the fragment that atomically replaces the ``(tier, file_path)`` row.

        A PURE builder: the old row is DELETEd and the new row CREATEd — composed
        into one transaction, that swap is what gives a concurrent reader the
        engine's snapshot isolation and rolls the whole thing back (leaving the
        prior row intact) on a mid-swap failure such as an out-of-domain ``state``.
        Every param is namespaced with :data:`MANIFEST_FRAGMENT_PARAM_PREFIX` so it
        never collides with a sibling producer's params in the merged transaction.

        Args:
            tier: The tier the file belongs to.
            file_path: The file path being replaced within the tier.
            sha512: The new SHA-512 hex digest.
            mtime_ns: The new modification time, in nanoseconds.
            size: The new size, in bytes.
            n_chunks: The new chunk count.
            chunk_ids: The new point ids.
            state: The new lifecycle state.

        Returns:
            The manifest-replace :class:`TxnFragment` (a DELETE then a CREATE),
            carrying no ``BEGIN``/``COMMIT`` of its own.
        """
        prefix = MANIFEST_FRAGMENT_PARAM_PREFIX
        id_key = f"{prefix}id"
        sha_key = f"{prefix}sha512"
        mtime_key = f"{prefix}mtime_ns"
        size_key = f"{prefix}size"
        n_chunks_key = f"{prefix}n_chunks"
        chunk_ids_key = f"{prefix}chunk_ids"
        state_key = f"{prefix}state"
        updated_key = f"{prefix}updated_at"
        params: dict[str, Any] = {
            id_key: self._record_id(tier, file_path),
            sha_key: sha512,
            mtime_key: mtime_ns,
            size_key: size,
            n_chunks_key: n_chunks,
            chunk_ids_key: chunk_ids,
            state_key: state,
            updated_key: self._now(),
        }
        statements = [
            f"DELETE type::record('{FILE_TABLE}', ${id_key})",
            f"CREATE type::record('{FILE_TABLE}', ${id_key}) SET "
            f"sha512 = ${sha_key}, mtime_ns = ${mtime_key}, size = ${size_key}, "
            f"n_chunks = ${n_chunks_key}, chunk_ids = ${chunk_ids_key}, "
            f"state = ${state_key}, updated_at = ${updated_key}",
        ]
        return TxnFragment(statements=statements, params=params)

    def delete_fragment(self, tier: str, file_path: str) -> TxnFragment:
        """Build the fragment that deletes the ``(tier, file_path)`` manifest row.

        Tier-scoped like :meth:`delete`; the composable counterpart a full-file
        purge composes alongside the chunk / file_text / graph deletes. Absent row
        composes to a harmless no-op DELETE.
        """
        prefix = MANIFEST_FRAGMENT_PARAM_PREFIX
        id_key = f"{prefix}id"
        return TxnFragment(
            statements=[f"DELETE type::record('{FILE_TABLE}', ${id_key})"],
            params={id_key: self._record_id(tier, file_path)},
        )

    # -- meta key/value store --------------------------------------------

    async def meta_get(self, key: str) -> str | None:
        """Return the meta value for ``key``, or ``None`` if absent.

        Args:
            key: The meta key to read (e.g. ``"tier_version:community"``).

        Returns:
            The stored value, or ``None``.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        rows = self._as_rows(
            await self._query(f"SELECT v FROM {META_TABLE} WHERE k = $k", {"k": key})
        )
        return str(rows[0]["v"]) if rows else None

    async def meta_set(self, key: str, value: str) -> None:
        """Insert or overwrite the meta value for ``key``.

        Uses ``UPSERT … WHERE k = $k`` (see the module docstring) — the UNIQUE
        index on ``meta.k`` is what makes the SAME record get found and
        overwritten on every subsequent call for the same key.

        Args:
            key: The meta key to write (e.g. a per-tier version stamp).
            value: The value to store.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        await self._query(
            f"UPSERT {META_TABLE} SET k = $k, v = $v WHERE k = $k", {"k": key, "v": value}
        )

    async def meta_delete(self, key: str) -> None:
        """Remove the meta row for ``key`` (idempotent — a no-op when absent).

        The clear half of the meta key/value store: after a bulk-sweep batch
        job's results are fully applied (or a terminal-failed job is abandoned to
        the realtime fallback), the indexer removes the in-flight-job marker under
        ``BULK_SWEEP_BATCH_JOB_META_KEY`` so a later sweep never mistakes a
        completed/dead job for a live one to REATTACH to.

        Args:
            key: The meta key to remove.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        await self._query(f"DELETE {META_TABLE} WHERE k = $k", {"k": key})

    # -- store-divergence reconcile surface --------------------------------

    async def expected_chunks(self, tier: str | None = None) -> int:
        """Return the total chunk count the manifest claims SHOULD be in the store.

        The sum of ``n_chunks`` over the ``indexed`` file rows (scoped to
        ``tier`` when given, otherwise the grand total across every tier).
        Only ``indexed`` rows count — a dirty/embedding/failed row has no live
        points to expect.

        Args:
            tier: The tier to total expected chunks for; ``None`` sums every
                tier.

        Returns:
            The expected chunk count (``0`` when nothing is indexed for the
            tier).

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        params: dict[str, Any] = {"state": STATE_INDEXED}
        statement = f"SELECT math::sum(n_chunks) AS {_SUM_ALIAS} FROM {FILE_TABLE} WHERE state = $state"
        if tier is not None:
            statement += " AND id[0] = $tier"
            params["tier"] = tier
        statement += " GROUP ALL"
        rows = self._as_rows(await self._query(statement, params))
        if not rows:
            return 0
        total = rows[0].get(_SUM_ALIAS)
        return int(total) if total is not None else 0

    async def indexed_file_count(self, tier: str | None = None, suffix: str | None = None) -> int:
        """Return the number of ``indexed`` file rows the manifest claims.

        Scoped to ``tier`` when given (otherwise every tier) and, optionally,
        to files whose path ends in ``suffix``.

        Args:
            tier: The tier to count indexed files for; ``None`` counts every
                tier.
            suffix: Restrict to files whose ``file_path`` ends with this
                suffix (e.g. ``".py"``); ``None`` counts every extension.

        Returns:
            The indexed file-row count (``0`` when nothing matches).

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        params: dict[str, Any] = {"state": STATE_INDEXED}
        conditions = ["state = $state"]
        if tier is not None:
            conditions.append("id[0] = $tier")
            params["tier"] = tier
        if suffix is not None:
            conditions.append("string::ends_with(id[1], $suffix)")
            params["suffix"] = suffix
        where = " AND ".join(conditions)
        statement = f"SELECT count() AS {_COUNT_ALIAS} FROM {FILE_TABLE} WHERE {where} GROUP ALL"
        rows = self._as_rows(await self._query(statement, params))
        if not rows:
            return 0
        count = rows[0].get(_COUNT_ALIAS)
        return int(count) if count is not None else 0

    async def reset_tier(self, tier: str) -> None:
        """Mark every row for ``tier`` as needing re-index — the count-driven heal.

        Only the lifecycle state flips (to :data:`STATE_DIRTY`, a non-
        ``indexed`` state) — the row's ``chunk_ids``/``sha512``/``size`` are
        preserved for the next sweep to compare/overwrite.

        Args:
            tier: The tier whose rows to mark for re-index.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        await self._query(
            f"UPDATE {FILE_TABLE} SET state = $state, updated_at = $now WHERE id[0] = $tier",
            {"state": STATE_DIRTY, "now": self._now(), "tier": tier},
        )
