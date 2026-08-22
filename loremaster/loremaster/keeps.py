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
        try:
            await execute_transaction(
                statement_text,
                merged_params,
                acquire=self._ensure_connection,
                drop=self._drop_connection,
                url=self._url,
            )
            created = await self.get_keep(keep_id)
        except (SurrealConnectionError, TxnContentionExhaustedError):
            # Transport fault / exhausted contention belongs to the retry/lifecycle
            # layer (store reference §3) — propagate untouched (both SUBCLASS
            # SurrealStoreError, so this re-raise MUST precede the wrap below).
            raise
        except SurrealStoreError as error:
            # A store rejection — an unruled ``type`` ASSERT or the ghost-keeper
            # ENFORCED edge — rolls the whole transaction back. Wrap LOUD as the domain
            # error (consumer law: no raw engine error reaches the caller).
            raise KeepStoreError(
                f"could not create {type!r} keep for keeper {keeper_email!r}: "
                f"the store rejected the keep create or the keeper's household edge"
            ) from error
        if created is None:  # pragma: no cover - a just-committed row must read back
            raise KeepStoreError(f"created keep {keep_id!r} did not read back")
        return created

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
        try:
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
        except (SurrealConnectionError, TxnContentionExhaustedError):
            # Transport / exhausted contention belongs to the retry/lifecycle layer
            # (store reference §3) — re-raise FIRST (both subclass SurrealStoreError).
            raise
        except SurrealStoreError as error:
            raise KeepStoreError(
                f"could not add member {member_email!r} to keep {keep_id!r}'s household: "
                f"the store rejected the membership edge"
            ) from error
        if membership is None:  # pragma: no cover - a just-written edge must read back
            raise KeepStoreError(f"member_of edge for {member_email!r} did not read back")
        return membership

    async def remove_household_member(self, *, keep_id: str, member_email: str) -> None:
        """Remove a member from a keep's household (Fork F rider).

        DELETEs the ``member_of`` edge (endpoints untouched). REFUSES to remove the
        current ``keep.keeper`` — removing the keeper would lock them out of writing
        their own keep (undoing the Fork-D auto-add) — raising :class:`KeeperLockoutError`
        BEFORE any delete, so the refusal changes nothing.

        Raises:
            KeepStoreError: No principal carries ``member_email``, OR the store rejected
                a store operation in this verb. The raw engine ``SurrealStoreError`` is
                WRAPPED as this domain error (consumer-law parity); transport /
                exhausted-contention faults pass through untouched (store reference §3).
            KeeperLockoutError: ``member_email`` resolves to the keep's keeper (a
                :class:`KeepStoreError` subclass — the refusal raised BEFORE the delete,
                so it is never re-wrapped).
        """
        member_id = await self._resolve_principal_id(member_email)
        bare_keep = self._record_id_part(keep_id)
        try:
            keep = await self.get_keep(keep_id)
            if keep is not None and keep.keeper_id == member_id:
                # A domain refusal (not a SurrealStoreError) — passes through the wrap
                # below untouched, unchanged store state (no delete has run yet).
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
        except (SurrealConnectionError, TxnContentionExhaustedError):
            # Transport / exhausted contention belongs to the retry/lifecycle layer
            # (store reference §3) — re-raise FIRST (both subclass SurrealStoreError).
            raise
        except SurrealStoreError as error:
            raise KeepStoreError(
                f"could not remove member {member_email!r} from keep {keep_id!r}'s household: "
                f"the store rejected the removal"
            ) from error

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
        try:
            await self._query(
                f"UPDATE {MEMBER_OF_RELATION} SET rank = $rank WHERE in = $member AND out = $keep",
                {
                    "rank": rank,
                    "member": RecordID(PRINCIPAL_TABLE, member_id),
                    "keep": RecordID(KEEP_TABLE, bare_keep),
                },
            )
            membership = await self._read_membership(bare_keep, member_id)
        except (SurrealConnectionError, TxnContentionExhaustedError):
            # Transport / exhausted contention belongs to the retry/lifecycle layer
            # (store reference §3) — re-raise FIRST (both subclass SurrealStoreError).
            raise
        except SurrealStoreError as error:
            raise KeepStoreError(
                f"could not set rank {rank!r} for member {member_email!r} on keep {keep_id!r}: "
                f"the store rejected the rank update"
            ) from error
        if membership is None:
            raise KeepNotFoundError(
                f"no member_of edge for member {member_email!r} on keep {keep_id!r}"
            )
        return membership

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
