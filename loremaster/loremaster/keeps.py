"""The ``keep`` substrate — lore's durable COLLABORATION-SPACE store (packet 60).

Introduced as the STUB half of the packet-60 wave-1 contract (contract-60-w1,
2026-08-22) — the value objects (:class:`Keep` / :class:`Membership`), the typed
errors, and the :class:`KeepStore` LIFECYCLE (connect / ``ensure_ready`` / ``close`` /
``_query``) real, with every CRUD verb raising :class:`NotImplementedError` — and
GREENED by the wave-1 builder. Every CRUD verb below is now fully implemented (against
the real ``surreal_schema`` DDL), per the design sidecar
(``docs/design/2026-08-22-packet60-keep-substrate-rulings.md``) and store law
(``docs/reference/surrealdb-31-capabilities.md`` §1.1/§2/§3/§4); the
``test_keeps_store.py`` pins are GREEN.

:class:`KeepStore` is the CRUD surface over the ``keep`` node table and the
``member_of`` household edge:

  * A ``keep`` is a collaboration space owned by exactly ONE keeper — a
    ``keep.keeper: record<principal>`` FIELD LINK (design Fork A), NOT a ``keeps`` edge.
  * Household membership is the many-to-many ``member_of`` RELATION edge
    (``principal --member_of--> keep``, ENFORCED + UNIQUE(in, out) — Fork F), carrying a
    per-Keep ``rank`` (FLAT today: ``'contributor'`` only — Fork C).
  * ``create_keep`` mints TWO facts ATOMICALLY (Fork D): the ``keep`` row AND the
    keeper's own ``member_of`` edge at ``rank='contributor'`` — both, or neither.

It rides the SAME store machinery :class:`~loremaster.principals.PrincipalStore` uses —
one lazily-opened, signed-in WS connection, self-healed on a mid-life transport
failure, reusing the shared transaction / error-classification seams in
:mod:`loremaster.store._txn` (``bootstrap_session`` / ``run_query`` /
``execute_transaction`` / ``retry_on_conflict``). It introduces NO retry /
classification / query policy of its own (finding #102/#120): every read/write routes
through the ONE shared single-statement seam ``run_query`` via
:meth:`~KeepStore._query`. Email → principal-id resolution reuses the OWNED
:meth:`~loremaster.principals.PrincipalStore.get_by_email` (a composed
``PrincipalStore``), never a cloned resolver (the
:meth:`~loremaster.principal_keys.PrincipalKeyStore._require_principal_id` precedent).

The public surface:

    Keep:                                  # a frozen value object (pydantic model)
        id: str                            # str(RecordID)
        keeper_id: str                     # the keeper principal's bare record id
        type: str                          # {project, team, session, dm}
        name: str | None                   # option<string> — NONE for a dm keep
        created_at: datetime               # tz-aware UTC, engine-stamped

    Membership:                            # a frozen value object (pydantic model)
        keep_id: str
        member_id: str                     # the member principal's bare record id
        rank: str                          # {contributor} today, DEFAULT contributor
        since: datetime                    # tz-aware UTC, engine-stamped

    KeepStore(*, url, namespace, database, user, password):
        async ensure_ready() -> None
        async create_keep(*, keeper_email, type, name=None) -> Keep
        async get_keep(keep_id) -> Keep | None
        async add_household_member(*, keep_id, member_email) -> Membership
        async remove_household_member(*, keep_id, member_email) -> None
        async set_rank(*, keep_id, member_email, rank) -> Membership
        async set_keeper(*, keep_id, new_keeper_email) -> Keep    # 61a-w1 admin set_owner
        async delete_keep(*, keep_id) -> None                     # 61a-w1 admin delete
        async list_household(keep_id) -> list[Membership]
        async list_keeps_for_keeper(keeper_email) -> list[Keep]
        async close() -> None

    Exceptions: KeepStoreError(RuntimeError);
                KeepNotFoundError(KeepStoreError).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, SecretStr
from surrealdb import AsyncSurreal, RecordID
from ulid import ULID

from loremaster.principals import PrincipalStore
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
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
    wrap_store_rejection,
)
from loremaster.store.surreal_schema import (
    KEEP_TABLE,
    MEMBER_OF_RELATION,
    PRINCIPAL_TABLE,
    generate_keep_ddl,
)

logger = logging.getLogger(__name__)

# The explicit read projections (store law §2: an explicit projection reads a NONE
# ``option<>`` column back as ``None``, where ``SELECT *`` OMITS it and a later
# ``row["name"]`` bracket access ``KeyError``s — the always-nameless ``dm`` keep would
# make that a 100%-broken read). ``keep`` carries ``name option<string>`` (NONE for a
# ``dm`` keep); ``member_of``'s columns are all present, but an explicit projection is
# named-in-one-place regardless.
_KEEP_READ_PROJECTION = "id, keeper, type, name, created_at"
_MEMBER_OF_READ_PROJECTION = "in, out, rank, since"


class Keep(BaseModel):
    """A single collaboration space in the durable ``keep`` store.

    Attributes:
        id: The keep's ``str(RecordID)`` string id.
        keeper_id: The bare record id of the keeper principal (its ``keeper`` FIELD
            LINK), the single owner who manages the household and (in 61+) may delete
            the keep.
        type: The collaboration flavour — one of ``{project, team, session, dm}``.
        name: An optional human label, or ``None`` (a ``dm`` keep is identified by its
            two members and carries no meaningful name).
        created_at: The tz-aware UTC timestamp the keep was created at.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    keeper_id: str
    type: str
    name: str | None
    created_at: datetime


class Membership(BaseModel):
    """A single household ``member_of`` edge in the durable store.

    Attributes:
        keep_id: The bare record id of the keep the member belongs to.
        member_id: The bare record id of the member principal.
        rank: The per-Keep collaboration rank — ``{contributor}`` today (FLAT),
            DEFAULT ``contributor``.
        since: The tz-aware UTC timestamp the membership was established at.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    keep_id: str
    member_id: str
    rank: str
    since: datetime


class KeepStoreError(RuntimeError):
    """Base class for every error :class:`KeepStore` raises."""


class KeepNotFoundError(KeepStoreError):
    """Raised when a keep id does not resolve to any row in the store."""


class KeeperLockoutError(KeepStoreError):
    """Raised when ``remove_household_member`` would remove the current keeper.

    Removing the keeper from the household would lock the keeper out of writing rows
    in their own keep (undoing the Fork-D auto-add). ``remove_household_member`` refuses
    it (design Fork F rider); re-open trigger: packet 61's keeper-reassign verb.
    """


class KeepStore:
    """Durable collaboration-space store over a single SurrealDB database.

    Owns the ``keep`` table + the ``member_of`` household edge (see
    :func:`~loremaster.store.surreal_schema.generate_keep_ddl`) and rides the shared
    :mod:`loremaster.store._txn` transaction / error-classification seams, so every
    mutation is atomic and every failure surfaces as a typed store error. It clones the
    :class:`~loremaster.principals.PrincipalStore` connection-owner idiom verbatim and
    introduces NO query/retry policy of its own (#102/#120). It COMPOSES a
    ``PrincipalStore`` to resolve keeper/member emails to principal ids (the ONE shared
    lookup — never a cloned resolver).

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
        password: SecretStr,
    ) -> None:
        """Store the wiring. Does not open any connection yet."""
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        # Opened on first use; ``None`` means "not yet connected / closed".
        self._connection: _SurrealConnection | None = None
        # Guards the connect-time check-then-set so N concurrent first-callers never
        # each open their own underlying SDK connection (mirrors ``PrincipalStore``).
        self._connect_lock = asyncio.Lock()
        # The composed identity store: resolves keeper/member emails to principal ids
        # via the OWNED ``PrincipalStore.get_by_email`` (never a cloned resolver — the
        # ``PrincipalKeyStore._require_principal_id`` precedent). Lazily connects on
        # first use; closed alongside this store.
        self._principals = PrincipalStore(
            url=url,
            namespace=namespace,
            database=database,
            user=user,
            password=password,
        )

    # -- connection lifecycle ----------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking cloned from
        :meth:`~loremaster.principals.PrincipalStore._ensure_connection`: the fast path
        never touches the lock, the session bootstrap is the ONE shared
        :func:`~loremaster.store._txn.bootstrap_session`, and any bootstrap failure —
        transport/auth fault OR exhausted contention alike — is wrapped as
        :class:`SurrealConnectionError` after the half-open socket is closed.
        """
        if self._connection is not None:
            return self._connection
        async with self._connect_lock:
            if self._connection is not None:
                return self._connection  # type: ignore[unreachable]
            connection = AsyncSurreal(self._url)
            credentials = signin_credentials(user=self._user, password=self._password)
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
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "keep.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect and apply the keep schema slice — idempotent, safe to re-run.

        Applies :func:`~loremaster.store.surreal_schema.generate_keep_ddl` (the ``keep``
        table + its ``keeper`` index THEN the ``member_of`` edge + its UNIQUE(in, out)
        index) inside ONE ``BEGIN … COMMIT`` via
        :func:`~loremaster.store._txn.execute_transaction`, which verifies EVERY
        statement's status (the SDK's plain ``query()`` inspects only the first). The
        table/indexes are ``IF NOT EXISTS`` and every FIELD is ``DEFINE FIELD
        OVERWRITE`` (finding #107); the ``member_of`` RELATION table is
        ``OVERWRITE … ENFORCED`` (store reference §1.1). ⚠ The ``member_of`` edge's
        ENFORCED ``IN principal`` / ``OUT keep`` endpoints require the ``principal``
        table to already exist — a standalone ``KeepStore.ensure_ready`` presumes the
        primary store (or a ``PrincipalStore``) readied ``principal`` first.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: A DDL statement was rejected by the engine.
        """
        await self._ensure_connection()
        ddl = generate_keep_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("keep.schema.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any) and the composed principal store."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None
        await self._principals.close()

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal).

        A compare-and-swap (cloned from :class:`~loremaster.principals.PrincipalStore`):
        ``self._connection`` is cleared only when ``connection`` is STILL the cached
        handle, so a late caller holding a stale reference can never wipe out a
        freshly-reconnected one. The handed connection is always closed.
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
            logger.debug("keep.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection, self-healing.

        Delegates to :func:`~loremaster.store._txn.run_query` — the ONE shared
        single-statement attempt body every seam in the package calls (finding
        #120/#108). ``KeepStore`` hand-rolls NO retry/classification of its own: this
        seam is auto-discovered by ``test_retry_seam.py``'s ``_query`` scan, so the
        shared retry/backoff/exhaustion pins prove the sharing by mutation.
        """
        return await run_query(
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
            noun="keep query",
            label="keep.query.rejected",
            statement=statement,
            params=params or {},
            logger=logger,
        )

    async def _resolve_principal_id(self, email: str) -> str:
        """Resolve ``email`` to its principal's bare record id (the ``xyz`` of
        ``principal:xyz``), for binding through ``type::record('principal', $pid)``.

        Delegates to the OWNED
        :meth:`~loremaster.principals.PrincipalStore.get_by_email` (the ONE shared
        lookup + row→Principal mapper — never a cloned resolver, the
        :meth:`~loremaster.principal_keys.PrincipalKeyStore._require_principal_id`
        precedent). Called by the create/mutation/list verbs to resolve keeper/member
        emails to principal ids.

        Raises:
            KeepStoreError: No principal carries ``email``.
        """
        principal = await self._principals.get_by_email(email)
        if principal is None:
            raise KeepStoreError(f"no principal with email {email!r}")
        record_id = principal.id
        _, separator, id_part = record_id.partition(":")
        return id_part if separator else record_id

    @staticmethod
    def _to_aware_utc(value: Any) -> datetime | None:
        """Coerce a stored datetime into a tz-aware UTC datetime (or ``None``).

        Reuses the fleet-comparable-anchor coercion policy verbatim from
        :meth:`~loremaster.principals.PrincipalStore._to_aware_utc` (the shared
        datetime seam — never a cloned coercion).
        """
        return PrincipalStore._to_aware_utc(value)

    # -- row mappers (keep-specific, mirroring PrincipalStore._row_to_principal) ---

    @staticmethod
    def _record_id_part(record_id: str) -> str:
        """The id portion of a ``str(RecordID)`` (``keep:xyz`` → ``xyz``), for binding
        through ``type::record('keep', $id)`` (store law §2/§4). A bare id (no ``:``)
        passes through unchanged — mirrors ``_resolve_principal_id``'s partition and the
        :meth:`~loremaster.principal_keys.PrincipalKeyStore._record_id_part` precedent.
        """
        _, separator, id_part = record_id.partition(":")
        return id_part if separator else record_id

    def _row_to_keep(self, row: dict[str, Any]) -> Keep:
        """Map a raw ``keep`` row into a FRESH :class:`Keep` value object.

        ``keeper`` comes back as a ``RecordID`` (``principal:xyz``) — reduced to its
        bare id. ``name`` reads through the shared
        :meth:`~loremaster.principals.PrincipalStore._optional_str` — ``None`` for the
        NONE ``option<string>`` (a nameless ``dm`` keep, store law §2, read via the
        explicit :data:`_KEEP_READ_PROJECTION`, never ``SELECT *``). ``created_at`` is a
        required self-stamped datetime coerced to the fleet-comparable tz-aware UTC anchor.
        """
        created_at = self._to_aware_utc(row.get("created_at"))
        if created_at is None:
            raise KeepStoreError("a keep row is missing its required created_at stamp")
        return Keep(
            id=str(row["id"]),
            keeper_id=self._record_id_part(str(row["keeper"])),
            type=str(row["type"]),
            name=PrincipalStore._optional_str(row.get("name")),
            created_at=created_at,
        )

    def _row_to_membership(self, row: dict[str, Any]) -> Membership:
        """Map a raw ``member_of`` edge row into a FRESH :class:`Membership`.

        ``in``/``out`` come back as ``RecordID``s (``principal:xyz`` / ``keep:xyz``) —
        each reduced to its bare id. ``rank``/``since`` are always present (``rank``
        DEFAULTs, ``since`` self-stamps). ``since`` coerces to tz-aware UTC.
        """
        since = self._to_aware_utc(row.get("since"))
        if since is None:
            raise KeepStoreError("a member_of row is missing its required since stamp")
        return Membership(
            keep_id=self._record_id_part(str(row["out"])),
            member_id=self._record_id_part(str(row["in"])),
            rank=str(row["rank"]),
            since=since,
        )

    async def _read_membership(self, keep_id: str, member_id: str) -> Membership | None:
        """Read the single ``member_of`` edge for ``(member_id, keep_id)``, or ``None``.

        Reads the edge table as a PLAIN table (``WHERE in = $member AND out = $keep``,
        endpoints bound as ``RecordID``) — never an arrow traversal (store law §4: a
        graph traversal never uses a secondary index). Both ids are BARE.
        """
        rows = PrincipalStore._as_rows(
            await self._query(
                f"SELECT {_MEMBER_OF_READ_PROJECTION} FROM {MEMBER_OF_RELATION} "
                f"WHERE in = $member AND out = $keep",
                {
                    "member": RecordID(PRINCIPAL_TABLE, member_id),
                    "keep": RecordID(KEEP_TABLE, keep_id),
                },
            )
        )
        return self._row_to_membership(rows[0]) if rows else None

    # -- create / read / mutation -------------------------------------------

    async def create_keep(
        self, *, keeper_email: str, type: str, name: str | None = None
    ) -> Keep:  # noqa: A002 - ``type`` is the ruled field name (design Fork B)
        """Create a keep and atomically auto-add its keeper to the household (Fork B/D).

        Resolves ``keeper_email`` to a principal id (via the composed
        :meth:`~loremaster.principals.PrincipalStore.get_by_email`), then — in ONE
        :func:`~loremaster.store._txn.execute_transaction` (store law §3) — CREATEs the
        ``keep`` row (a Python-minted ``str(ULID())`` id, ``keeper`` bound as
        ``type::record('principal', $id)``, ``type`` server-validated by the closed
        ASSERT, ``name`` written only when provided so an omitted ``option<>`` decodes
        to NONE) AND RELATEs the keeper's own ``member_of`` edge at the default
        ``rank='contributor'``. Both land or neither does: a keep whose keeper edge is
        refused (ENFORCED, a ghost keeper) rolls the CREATE back too — no orphan keep
        (Fork D: the keeper's write access rides household membership, so a keeper who
        was never householded could not write their own keep).

        Args:
            keeper_email: The email of the principal who will keep (own) the space.
            type: The collaboration flavour — one of ``{project, team, session, dm}``.
            name: An optional human label; omitted/``None`` for a nameless ``dm`` keep.

        Returns:
            The created :class:`Keep`, read back through :meth:`get_keep`.

        Raises:
            KeepStoreError: No principal carries ``keeper_email``, OR the store rejected
                the create (an unruled ``type``) or the keeper edge (a ghost keeper
                endpoint). The raw engine ``SurrealStoreError`` is WRAPPED as this domain
                error (consumer-law parity with
                :meth:`~loremaster.principals.PrincipalStore.create`); the whole
                transaction rolls back (no orphan keep). Transport / exhausted-contention
                faults (:class:`SurrealConnectionError` /
                :class:`TxnContentionExhaustedError`) pass through untouched — they belong
                to the retry/lifecycle layer (store reference §3).
        """
        keeper_id = await self._resolve_principal_id(keeper_email)
        keep_id = str(ULID())  # a bare, client-minted ULID (Crockford, colon-free)
        content_fragments = [f"keeper: type::record('{PRINCIPAL_TABLE}', $kid)", "type: $type"]
        params: dict[str, Any] = {"keep_id": keep_id, "kid": keeper_id, "type": type}
        if name is not None:
            content_fragments.append("name: $name")
            params["name"] = name
        params["keeper_edge"] = RecordID(PRINCIPAL_TABLE, keeper_id)
        params["keep_edge"] = RecordID(KEEP_TABLE, keep_id)
        fragment = TxnFragment(
            statements=[
                f"CREATE type::record('{KEEP_TABLE}', $keep_id) "
                f"CONTENT {{ {', '.join(content_fragments)} }}",
                f"RELATE $keeper_edge->{MEMBER_OF_RELATION}->$keep_edge",
            ],
            params=params,
        )
        statement_text, merged_params = compose(fragment)
        # A store rejection — an unruled ``type`` ASSERT or the ghost-keeper ENFORCED edge —
        # rolls the whole transaction back and is wrapped LOUD as the domain error (consumer
        # law); a transport fault / exhausted contention passes through untouched (both
        # SUBCLASS SurrealStoreError, store reference §3). Finding #400: routed through the
        # ONE seam.
        with wrap_store_rejection(
            KeepStoreError,
            f"could not create {type!r} keep for keeper {keeper_email!r}: "
            f"the store rejected the keep create or the keeper's household edge",
        ):
            await execute_transaction(
                statement_text,
                merged_params,
                acquire=self._ensure_connection,
                drop=self._drop_connection,
                url=self._url,
            )
            created = await self.get_keep(keep_id)
        if created is None:  # pragma: no cover - a just-committed row must read back
            raise KeepStoreError(f"created keep {keep_id!r} did not read back")
        return created

    async def get_or_create_keyed(
        self, key: str, *, type: str, keeper_email: str, name: str | None = None  # noqa: A002
    ) -> Keep:
        """Get-or-create the keep addressed by the deterministic natural key ``key`` (SF-63-4;
        packet 63a — STUB / runnable-RED, contract-63a).

        The idempotent, race-safe mint behind the canonical project keep (``key='project:lore'``,
        design §2.2) and 63b's session keeps (``key='session:<session>'``). Reads by the UNIQUE
        ``keep.key`` index; on a miss, CREATEs (like :meth:`create_keep`, with ``key`` set) and,
        on a concurrent-``register`` UNIQUE conflict, RE-READS and returns the winner — the
        hot-row CAS mint (store reference §5: a UNIQUE index is the backstop, never a
        de-duplicator; re-read on conflict, never a second row). Store law §1.8: the many manual
        keeps carrying a NONE key coexist under the UNIQUE index. STUB: builder fills.

        Args:
            key: The deterministic natural key (e.g. ``'project:lore'``, ``'session:<id>'``).
            type: The keep type (``project``/``session``/…); server-validated by the closed ASSERT.
            keeper_email: The principal who keeps the space (auto-householded, Fork D).
            name: An optional human label.

        Returns:
            The existing or freshly-minted :class:`Keep` bearing ``key``.

        Raises:
            KeepStoreError: No principal carries ``keeper_email``, OR the store rejected the create.
                The WHOLE verb (including its internal reads) wraps a raw engine
                ``SurrealStoreError`` as this domain error (consumer law); transport /
                exhausted-contention faults pass through untouched (store reference §3/§5).
        """
        # The WHOLE verb — the key read, the keeper resolution, the CAS create, the read-back — is
        # under ONE wrap (finding #400): a raw engine rejection at ANY step surfaces as
        # KeepStoreError, while transport / exhausted contention passes through (both SUBCLASS
        # SurrealStoreError, store-ref §3). This is what the corpse-C rejection-wrap pin demands
        # (the injection hits the initial key READ first).
        with wrap_store_rejection(
            KeepStoreError,
            f"could not get-or-create the {type!r} keep keyed {key!r} for keeper {keeper_email!r}",
        ):
            existing = await self.get_by_key(key)
            if existing is not None:
                return existing
            keeper_id = await self._resolve_principal_id(keeper_email)
            keep_id = str(ULID())  # a bare, client-minted ULID (Crockford, colon-free)
            content_fragments = [
                f"keeper: type::record('{PRINCIPAL_TABLE}', $kid)",
                "type: $type",
                "key: $key",
            ]
            params: dict[str, Any] = {
                "keep_id": keep_id, "kid": keeper_id, "type": type, "key": key,
            }
            if name is not None:
                content_fragments.append("name: $name")
                params["name"] = name
            params["keeper_edge"] = RecordID(PRINCIPAL_TABLE, keeper_id)
            params["keep_edge"] = RecordID(KEEP_TABLE, keep_id)
            fragment = TxnFragment(
                statements=[
                    f"CREATE type::record('{KEEP_TABLE}', $keep_id) "
                    f"CONTENT {{ {', '.join(content_fragments)} }}",
                    f"RELATE $keeper_edge->{MEMBER_OF_RELATION}->$keep_edge",
                ],
                params=params,
            )
            statement_text, merged_params = compose(fragment)
            try:
                await execute_transaction(
                    statement_text,
                    merged_params,
                    acquire=self._ensure_connection,
                    drop=self._drop_connection,
                    url=self._url,
                )
            except (SurrealConnectionError, TxnContentionExhaustedError):
                # Transport / exhausted contention belongs to the retry/lifecycle layer — it is
                # NOT a UNIQUE conflict, and must NEVER be swallowed by the CAS re-read (store-ref
                # §5: re-read a genuine CONFLICT, never a dropped socket).
                raise
            except SurrealStoreError:
                # The hot-row CAS (store-ref §5): a concurrent ``register`` may have minted this
                # UNIQUE key between our read-miss and this CREATE. If the key now resolves, that
                # IS the conflict → return the winner, never a second row. If it still does not,
                # the rejection was genuine (an unruled type, a ghost keeper) → re-raise (the wrap
                # translates it to KeepStoreError).
                winner = await self.get_by_key(key)
                if winner is not None:
                    return winner
                raise
            created = await self.get_keep(keep_id)
            if created is None:  # pragma: no cover - a just-committed row must read back
                raise KeepStoreError(f"created keyed keep {keep_id!r} did not read back")
            return created

    async def get_by_key(self, key: str) -> Keep | None:
        """Read the keep bearing the deterministic natural ``key`` (SF-63-4), or ``None`` on a miss.

        The UNIQUE ``keep.key`` index makes a real (non-NONE) key map to ≤1 row (§1.8); a manual
        keep carrying a NONE key is never matched by ``WHERE key = $k`` (store-ref §1.8). Uses the
        explicit :data:`_KEEP_READ_PROJECTION` (never ``SELECT *`` — store-ref §2) and the ``key``
        index (a plain equality on the indexed column IndexScans — schema pin P6). The natural-key
        address the write path resolves the canonical project keep by (design §2.2).
        """
        rows = PrincipalStore._as_rows(
            await self._query(
                f"SELECT {_KEEP_READ_PROJECTION} FROM {KEEP_TABLE} WHERE key = $k",
                {"k": key},
            )
        )
        return self._row_to_keep(rows[0]) if rows else None

    async def get_keep(self, keep_id: str) -> Keep | None:
        """Read a keep by id, or ``None`` on a miss.

        Uses the explicit :data:`_KEEP_READ_PROJECTION` (never ``SELECT *`` — store law
        §2: ``SELECT *`` OMITS a NONE ``option<>`` column, so a ``dm`` keep's absent
        ``name`` would KeyError a bracket read; the projection reads it back as ``None``).
        Accepts either a bare id or a ``keep:xyz`` string.
        """
        rows = PrincipalStore._as_rows(
            await self._query(
                f"SELECT {_KEEP_READ_PROJECTION} FROM type::record('{KEEP_TABLE}', $id)",
                {"id": self._record_id_part(keep_id)},
            )
        )
        return self._row_to_keep(rows[0]) if rows else None

    async def add_household_member(self, *, keep_id: str, member_email: str) -> Membership:
        """Add a member to a keep's household — IDEMPOTENT (Fork F).

        Resolves ``member_email``, then RELATEs ``member_of`` at the default rank. A
        re-add of an existing member is a BENIGN no-op (check-first: the existing edge is
        returned unchanged, never an error, and no second edge is written — the
        UNIQUE(in, out) index is the backstop, not the mechanism). Returns the
        :class:`Membership`.

        Raises:
            KeepStoreError: No principal carries ``member_email``, OR the store rejected
                the membership edge (e.g. a ghost keep OUT endpoint under ENFORCED). The
                raw engine ``SurrealStoreError`` is WRAPPED as this domain error
                (consumer-law parity with
                :meth:`~loremaster.principals.PrincipalStore.create`); transport /
                exhausted-contention faults pass through untouched (store reference §3).
        """
        member_id = await self._resolve_principal_id(member_email)
        bare_keep = self._record_id_part(keep_id)
        # A store rejection is wrapped LOUD; a transport fault / exhausted contention passes
        # through untouched (store reference §3). Finding #400: routed through the ONE seam.
        with wrap_store_rejection(
            KeepStoreError,
            f"could not add member {member_email!r} to keep {keep_id!r}'s household: "
            f"the store rejected the membership edge",
        ):
            existing = await self._read_membership(bare_keep, member_id)
            if existing is not None:
                return existing  # idempotent re-add — a benign no-op
            await self._query(
                f"RELATE $member->{MEMBER_OF_RELATION}->$keep",
                {
                    "member": RecordID(PRINCIPAL_TABLE, member_id),
                    "keep": RecordID(KEEP_TABLE, bare_keep),
                },
            )
            membership = await self._read_membership(bare_keep, member_id)
        if membership is None:  # pragma: no cover - a just-written edge must read back
            raise KeepStoreError(f"member_of edge for {member_email!r} did not read back")
        return membership

    async def remove_household_member(self, *, keep_id: str, member_email: str) -> None:
        """Remove a member from a keep's household (Fork F rider).

        DELETEs the ``member_of`` edge (endpoints untouched). Two guards fire BEFORE any
        delete — so a refusal changes nothing: a GHOST keep (an id that was never created)
        is LOUD, raising :class:`KeepNotFoundError` (FR-3, sidecar reading (a): ``remove``
        is an access-control verb, so a typo'd ``keep_id`` must not read as a silent
        *"access removed"*); and removing the current ``keep.keeper`` is REFUSED with
        :class:`KeeperLockoutError` (removing the keeper would lock them out of writing
        their own keep, undoing the Fork-D auto-add). Folded into the ONE ``get_keep`` read
        the keeper guard already does — the DIRECT keep-row SELECT, not a keeper-is-None
        proxy. A REAL principal who is simply not a member of a REAL keep stays a BENIGN
        idempotent no-op (the deliberate member-dimension asymmetry: you can idempotently
        remove a nonexistent membership, but never from a nonexistent keep).

        Raises:
            KeepStoreError: No principal carries ``member_email``, OR the store rejected
                a store operation in this verb. The raw engine ``SurrealStoreError`` is
                WRAPPED as this domain error (consumer-law parity); transport /
                exhausted-contention faults pass through untouched (store reference §3).
            KeepNotFoundError: ``keep_id`` resolves to no keep (a :class:`KeepStoreError`
                subclass — raised BEFORE the delete, so store state is unchanged and it is
                never re-wrapped).
            KeeperLockoutError: ``member_email`` resolves to the keep's keeper (a
                :class:`KeepStoreError` subclass — the refusal raised BEFORE the delete,
                so it is never re-wrapped).
        """
        member_id = await self._resolve_principal_id(member_email)
        bare_keep = self._record_id_part(keep_id)
        # A store rejection is wrapped LOUD; a transport fault / exhausted contention passes
        # through untouched (store reference §3). The deliberate KeepNotFoundError /
        # KeeperLockoutError refusals raised INSIDE this block are NOT SurrealStoreError
        # subclasses, so the seam never re-wraps them. Finding #400: routed through the ONE seam.
        with wrap_store_rejection(
            KeepStoreError,
            f"could not remove member {member_email!r} from keep {keep_id!r}'s household: "
            f"the store rejected the removal",
        ):
            keep = await self.get_keep(keep_id)
            if keep is None:
                # FR-3 (sidecar reading (a)): a GHOST keep is LOUD — a typo'd ``keep_id``
                # on this access-control verb must not read as a silent "access removed".
                # Raised BEFORE the DELETE (folded into the keeper-guard read), so store
                # state is unchanged; a REAL non-member of a REAL keep stays a benign no-op
                # (the DELETE below simply no-matches — the deliberate member asymmetry).
                # KeepNotFoundError subclasses KeepStoreError (not SurrealStoreError), so
                # the seam never re-wraps it — it propagates like KeeperLockoutError.
                raise KeepNotFoundError(
                    f"no keep {keep_id!r} exists — cannot remove a household member from it"
                )
            if keep.keeper_id == member_id:
                # A domain refusal (not a SurrealStoreError) — passes through the seam
                # untouched, unchanged store state (no delete has run yet).
                raise KeeperLockoutError(
                    f"refusing to remove the keeper of keep {keep.id!r} from its own household "
                    f"(keeper lockout — the keeper's write access rides household membership)"
                )
            await self._query(
                f"DELETE {MEMBER_OF_RELATION} WHERE in = $member AND out = $keep",
                {
                    "member": RecordID(PRINCIPAL_TABLE, member_id),
                    "keep": RecordID(KEEP_TABLE, bare_keep),
                },
            )

    async def set_rank(self, *, keep_id: str, member_email: str, rank: str) -> Membership:
        """Set a household member's per-Keep ``rank`` (Fork F rider).

        UPDATEs the edge's ``rank`` field (the store-side ASSERT validates the value).
        TRIVIAL today — the only legal value is ``'contributor'``; the seam becomes
        meaningful when the domain widens in 61+. Returns the updated :class:`Membership`.

        Raises:
            KeepStoreError: No principal carries ``member_email``, OR the store rejected
                the rank update (e.g. an unruled ``rank`` value refused by the closed-domain
                ASSERT). The raw engine ``SurrealStoreError`` is WRAPPED as this domain
                error (consumer-law parity); transport / exhausted-contention faults pass
                through untouched (store reference §3).
            KeepNotFoundError: ``member_email`` is not a household member of ``keep_id``
                (a :class:`KeepStoreError` subclass, raised after a no-match readback).
        """
        member_id = await self._resolve_principal_id(member_email)
        bare_keep = self._record_id_part(keep_id)
        # A store rejection (e.g. an unruled ``rank`` refused by the closed-domain ASSERT) is
        # wrapped LOUD; a transport fault / exhausted contention passes through untouched
        # (store reference §3). Finding #400: routed through the ONE seam.
        with wrap_store_rejection(
            KeepStoreError,
            f"could not set rank {rank!r} for member {member_email!r} on keep {keep_id!r}: "
            f"the store rejected the rank update",
        ):
            await self._query(
                f"UPDATE {MEMBER_OF_RELATION} SET rank = $rank WHERE in = $member AND out = $keep",
                {
                    "rank": rank,
                    "member": RecordID(PRINCIPAL_TABLE, member_id),
                    "keep": RecordID(KEEP_TABLE, bare_keep),
                },
            )
            membership = await self._read_membership(bare_keep, member_id)
        if membership is None:
            raise KeepNotFoundError(
                f"no member_of edge for member {member_email!r} on keep {keep_id!r}"
            )
        return membership

    async def set_keeper(self, *, keep_id: str, new_keeper_email: str) -> Keep:
        """Reassign a keep's keeper (owner) to a new principal — admin set_owner
        (packet 61a-w1, §FR-4/D1: the keep-flavoured spelling of the design's §4.3
        ``set_owner``, one root with ``set_rank``).

        CHECK-FIRST, so a refusal changes nothing and no phantom keep is upserted:
          1. a GHOST keep is LOUD — :class:`KeepNotFoundError` raised via the ONE
             :meth:`get_keep` read BEFORE any UPDATE (D2 parity; and an ``UPDATE`` on a
             specific record id would otherwise UPSERT a phantom keep at the ghost id);
          2. the new-keeper email is RESOLVED FIRST — a ``record<principal>`` field link
             does NOT validate existence (store law §2), so email resolution
             (:meth:`_resolve_principal_id`, raising :class:`KeepStoreError` on an unknown
             email) is the ENFORCED-flavoured backstop, raised BEFORE the UPDATE.
        Only then does it UPDATE ``keep.keeper`` to the resolved successor and read the
        keep back. The departing keeper's ``member_of`` edge is left as-is (separately
        managed — §FR-4). Returns the updated :class:`Keep`.

        Args:
            keep_id: The keep to reassign (a bare id or a ``keep:xyz`` string).
            new_keeper_email: The email of the principal to make the new keeper.

        Returns:
            The updated :class:`Keep`, read back through :meth:`get_keep`.

        Raises:
            KeepNotFoundError: ``keep_id`` resolves to no keep (raised BEFORE any UPDATE —
                a :class:`KeepStoreError` subclass, never re-wrapped).
            KeepStoreError: No principal carries ``new_keeper_email`` (raised BEFORE any
                UPDATE), OR the store rejected the update. The raw engine
                ``SurrealStoreError`` is WRAPPED as this domain error (consumer-law
                parity); transport / exhausted-contention faults pass through untouched
                (store reference §3).
        """
        # The check-first ``get_keep`` and email resolution run INSIDE the try (the
        # ``remove_household_member`` idiom) so a raw engine ``SurrealStoreError`` from
        # EITHER internal read is wrapped as ``KeepStoreError`` — the FR-2 Q2b consumer-law
        # invariant covers the WHOLE verb, internal reads included. ``KeepNotFoundError`` /
        # the ghost-email ``KeepStoreError`` are NOT ``SurrealStoreError`` subclasses, so
        # they pass through both ``except`` clauses untouched (deliberate refusals).
        bare_keep = self._record_id_part(keep_id)
        # A store rejection is wrapped LOUD; a transport fault / exhausted contention passes
        # through untouched (store reference §3). The deliberate KeepNotFoundError / ghost-email
        # KeepStoreError refusals raised INSIDE this block are not SurrealStoreError subclasses,
        # so the seam never re-wraps them. Finding #400: routed through the ONE seam.
        with wrap_store_rejection(
            KeepStoreError,
            f"could not set keeper of keep {keep_id!r} to {new_keeper_email!r}: "
            f"the store rejected the keeper update",
        ):
            keep = await self.get_keep(keep_id)
            if keep is None:
                raise KeepNotFoundError(
                    f"no keep {keep_id!r} exists — cannot set its keeper"
                )
            # Resolve the successor email BEFORE the UPDATE (KeepStoreError on a ghost
            # email): a record<principal> write does NOT validate existence (store law §2),
            # so this is the only guard against writing a dangling keeper. A refused
            # resolution leaves keep.keeper untouched (no UPDATE has run).
            new_keeper_id = await self._resolve_principal_id(new_keeper_email)
            await self._query(
                f"UPDATE type::record('{KEEP_TABLE}', $id) "
                f"SET keeper = type::record('{PRINCIPAL_TABLE}', $kid)",
                {"id": bare_keep, "kid": new_keeper_id},
            )
            updated = await self.get_keep(keep_id)
        if updated is None:  # pragma: no cover - a just-updated (existing) keep must read back
            # The keep was CONFIRMED to exist by the check-first above, so a None readback
            # here is a store anomaly (a TOCTOU delete / engine fault), NOT a "not found" —
            # KeepStoreError, mirroring create_keep's "did not read back" (the check-first
            # is therefore the SOLE KeepNotFoundError guard, #403).
            raise KeepStoreError(f"keep {keep_id!r} did not read back after its keeper update")
        return updated

    async def delete_keep(self, *, keep_id: str) -> None:
        """Delete a keep node and cascade its household — admin delete (packet 61a-w1,
        §FR-4/D2: the natural remediation for a sole-member / ``dm`` keep whose keeper is
        being deleted).

        CHECK-FIRST: a GHOST keep is LOUD — :class:`KeepNotFoundError` raised via the ONE
        :meth:`get_keep` read BEFORE any DELETE (D2: a destructive access-control verb on
        a typo'd id must not read as a silent *"deleted"* when nothing was; the FR-3
        ghost-keep-loud class). Otherwise DELETEs the ``keep`` node — its ``member_of``
        edges auto-cascade on the ``out``-endpoint (keep-node) delete (store law §4 —
        probed, ``scripts/probe_member_of_cascade.py`` LEG C), so NO explicit
        ``member_of`` DELETE is issued; the member/keeper PRINCIPALS are untouched.

        ⚠ 63/64 FORWARD-BOUNDARY (§FR-4/D2): at 61 a keep holds no keep-scoped governed
        rows, so this cascades keep + member_of only. When 63/64 add
        ``scope='keep:<id>'`` governed rows, ``delete_keep`` MUST revisit whether it
        cascades or orphans them (record-link cascade discipline — the #402 class one
        layer out).

        Args:
            keep_id: The keep to delete (a bare id or a ``keep:xyz`` string).

        Raises:
            KeepNotFoundError: ``keep_id`` resolves to no keep (raised BEFORE any DELETE —
                a :class:`KeepStoreError` subclass, never re-wrapped).
            KeepStoreError: The store rejected the delete. The raw engine
                ``SurrealStoreError`` is WRAPPED as this domain error (consumer-law
                parity); transport / exhausted-contention faults pass through untouched
                (store reference §3).
        """
        # The check-first ``get_keep`` runs INSIDE the try (the ``remove_household_member``
        # idiom) so a raw engine ``SurrealStoreError`` from that internal read is wrapped as
        # ``KeepStoreError`` — the FR-2 Q2b consumer-law invariant covers the whole verb.
        # ``KeepNotFoundError`` is not a ``SurrealStoreError`` subclass, so the deliberate
        # ghost-keep refusal passes through both ``except`` clauses untouched.
        bare_keep = self._record_id_part(keep_id)
        # A store rejection is wrapped LOUD; a transport fault / exhausted contention passes
        # through untouched (store reference §3). The deliberate ghost-keep KeepNotFoundError
        # raised INSIDE this block is not a SurrealStoreError subclass, so the seam never
        # re-wraps it. Finding #400: routed through the ONE seam.
        with wrap_store_rejection(
            KeepStoreError,
            f"could not delete keep {keep_id!r}: the store rejected the delete",
        ):
            keep = await self.get_keep(keep_id)
            if keep is None:
                raise KeepNotFoundError(
                    f"no keep {keep_id!r} exists — cannot delete it"
                )
            # DELETE the keep NODE — the member_of edges auto-cascade on the out-endpoint
            # delete (store law §4, probed LEG C); ONE statement, so ``_query`` suffices
            # (no multi-statement txn needed).
            await self._query(
                f"DELETE type::record('{KEEP_TABLE}', $id)",
                {"id": bare_keep},
            )

    async def list_household(self, keep_id: str) -> list[Membership]:
        """List a keep's household memberships (store law §4).

        Reads the ``member_of`` edges scoped to ``keep_id`` as a PLAIN table
        (``WHERE out = $keep``, endpoint bound as ``RecordID``) — never an arrow
        traversal — mapping each to a :class:`Membership`.
        """
        rows = PrincipalStore._as_rows(
            await self._query(
                f"SELECT {_MEMBER_OF_READ_PROJECTION} FROM {MEMBER_OF_RELATION} WHERE out = $keep",
                {"keep": RecordID(KEEP_TABLE, self._record_id_part(keep_id))},
            )
        )
        return [self._row_to_membership(row) for row in rows]

    async def list_keeps_for_keeper(self, keeper_email: str) -> list[Keep]:
        """List every keep a principal keeps (design Fork A rider).

        Resolves ``keeper_email``, then SELECTs ``keep`` rows
        ``WHERE keeper = type::record('principal', $pid)`` — an IndexScan on the
        NON-UNIQUE ``keeper`` index (store law §4: a scalar filtered through a hop is
        un-indexable, which is why keepership is a FIELD LINK). Reads through the explicit
        :data:`_KEEP_READ_PROJECTION` so a nameless keep round-trips as ``name=None``.

        Raises:
            KeepStoreError: No principal carries ``keeper_email``.
        """
        keeper_id = await self._resolve_principal_id(keeper_email)
        rows = PrincipalStore._as_rows(
            await self._query(
                f"SELECT {_KEEP_READ_PROJECTION} FROM {KEEP_TABLE} "
                f"WHERE keeper = type::record('{PRINCIPAL_TABLE}', $pid)",
                {"pid": keeper_id},
            )
        )
        return [self._row_to_keep(row) for row in rows]

    async def list_keeps_for_member(self, *, member_email: str) -> list[str]:
        """List the BARE ids of every keep whose household ``member_email`` is in.

        The symmetric twin of :meth:`list_keeps_for_keeper` (Fork F, packet 61b-w2):
        reads the ``member_of`` edge AS A PLAIN table filtered on the LEADING column
        ``in`` (``SELECT out FROM member_of WHERE in = $principal``, the ``in`` endpoint
        bound as a ``RecordID``) — an IndexScan on the existing ``UNIQUE(in, out)`` (store
        reference §2: a leading-column ``WHERE in = $p`` IndexScans; §4: a graph traversal
        never uses a secondary index, so ``member_of`` is read as a PLAIN table, NEVER an
        arrow traversal). Direction: "keeps whose HOUSEHOLD I am in" (``member_of`` FROM
        the principal) — the mirror of :meth:`list_household`'s reverse ``WHERE out =
        $keep``. Returns the BARE keep ids (the ``xyz`` of ``keep:xyz``); the resolver
        (:func:`loremaster.visible_keeps.resolve_visible_keeps`) maps each to its
        ``keep:<id>`` scope via the shared ``lorerunes.pdp.keep_scope`` helper (the ONE
        spelling — the resolver never hand-rolls the prefix).

        ⚠ BORN-WRAPPED — WHOLE METHOD (design sidecar D1). Unlike the unwrapped
        :meth:`list_keeps_for_keeper` (a pre-existing #406 read-gap, NOT the standard),
        this read FEEDS THE PDP's ``visible_keep_ids`` via ``resolve_visible_keeps`` — so a
        raw engine ``SurrealStoreError`` escaping it would land in the AUTHORIZATION path.
        The ENTIRE body (the email-resolution read AND the ``member_of`` SELECT) is wrapped
        in ONE :func:`~loremaster.store._txn.wrap_store_rejection`, so no raw engine error
        reaches the authz path from EITHER; transport / exhausted-contention faults pass
        through untouched (store reference §3 — they belong to the retry/lifecycle layer).

        Args:
            member_email: The email of the principal whose household keeps to list.

        Returns:
            The bare ids of the keeps whose household ``member_email`` is in (``[]`` for a
            member of no keep — never ``None``).

        Raises:
            KeepStoreError: No principal carries ``member_email`` (via the composed
                :meth:`_resolve_principal_id`, raised BEFORE the read — never ``[]`` for a
                typo'd identity, which would silently under-authorize), OR the store
                rejected the read. The raw engine ``SurrealStoreError`` is WRAPPED as this
                domain error (consumer law: no raw engine error reaches the authz path);
                transport / exhausted-contention faults pass through untouched (store
                reference §3).
        """
        # WHOLE-METHOD born-wrap (D1): the email resolution AND the member_of SELECT both
        # ride ONE wrap seam, so a raw SurrealStoreError from EITHER is wrapped LOUD as
        # KeepStoreError before it can reach the PDP's authorization path. The deliberate
        # unknown-email KeepStoreError raised by _resolve_principal_id is not a
        # SurrealStoreError subclass, so the seam passes it through untouched. Finding #400:
        # routed through the ONE seam (wrap_store_rejection), never hand-rolled.
        with wrap_store_rejection(
            KeepStoreError,
            f"could not list keeps for member {member_email!r}: "
            f"the store rejected the household read",
        ):
            member_id = await self._resolve_principal_id(member_email)
            rows = PrincipalStore._as_rows(
                await self._query(
                    f"SELECT out FROM {MEMBER_OF_RELATION} WHERE in = $principal",
                    {"principal": RecordID(PRINCIPAL_TABLE, member_id)},
                )
            )
        # Pure mapping (no store call): each member_of row's ``out`` is the keep RecordID;
        # reduce it to its BARE id (Fork F — the resolver adds the ``keep:`` prefix).
        return [self._record_id_part(str(row["out"])) for row in rows]
