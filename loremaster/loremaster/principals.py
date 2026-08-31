"""The ``principal`` substrate — lore's durable HUMAN-IDENTITY store (packet 48).

:class:`PrincipalStore` is the CRUD surface over the ``principal`` table: the
persistent record of a person who authenticates. A principal is admitted by an
admin (email pre-create) and later bound to its runtime OAuth identity on first
login — Model B: ``subject`` (the value ``fastmcp``'s
``get_access_token()`` surfaces as ``AccessToken.client_id`` — Google OAuth ``sub``
or an API-key name) is ``option<string>`` and starts NONE, filled by
:meth:`~PrincipalStore.set_subject` when packet 39 admits the login. The two UNIQUE
keys are ``email`` (the human admission key 49's CLI operates on) and ``subject``
(the runtime identity 39 admits by ``WHERE subject = $client_id``).

STANDING LAW — ``principal`` is a THIRD, DISTINCT identity vocabulary
(one-column-one-identity-vocabulary, the law near ``server``'s
``_TRACE_DECLARED_KEYS`` — *"the same dishonesty as overloading ``session`` with a
transport id"*). It must NEVER be conflated with the other two:

1. **Ledger-actor strings** (``created_by`` / ``actor`` / ``owner`` on ``finding`` /
   ``task`` / ``memory``) are free-form audit strings and are **NOT retro-fitted**
   to ``principal``. A finding's ``created_by`` is not a ``principal`` FK and must
   not become one here.
2. **The comms ``agent`` table** (``_AGENT_FIELD_SPECS``) is the fleet-coordination
   identity, and it ALREADY carries columns named ``role`` and ``status`` with
   DIFFERENT domains — ``agent.role`` is a free non-empty string
   (``builder``/``auditor``/…) and ``agent.status ∈ {active, idle, input_required,
   retired}``. ``principal.role ∈ {member, admin}`` and ``principal.status ∈
   {active, suspended}`` are NARROWER, principal-specific closed domains with their
   OWN vocabulary tuples (:data:`~loremaster.store.surreal_schema._PRINCIPAL_ROLES`
   / :data:`~loremaster.store.surreal_schema._PRINCIPAL_STATUSES`). The identical
   column NAMES across the two tables are a coincidence of English, not shared
   vocabulary — never wire ``principal.role``/``status`` to the ``agent`` tuples.

⚠ RELATED, NOT CONFLATED (packet 62, I1/I2). The distinct-vocabulary law above is
UNCHANGED, but as of packet 62 the two identity NODES are no longer *unrelated*: the
``agent`` table carries an ``owner_principal`` OWNS back-link
(``option<record<principal>>`` — a principal OWNS its agents; Fork 3), stamped
server-side at register from the authenticated credential (R3.3), and the packet-62
capability binding checks ``agent.owner_principal`` against the transport principal. So
principal and agent are RELATED by that edge — but the edge links NODES; it does NOT
merge the closed domains. ``principal.role``/``status`` and ``agent.role``/``status``
keep their SEPARATE vocabularies (still never wired one to the other, per item 2); an
ownerless agent is legal (Fork 2), and on principal-delete the link is DANGLE-tolerated
(R3.2). Relating the nodes is not conflating the vocabularies.

It rides the SAME store machinery :mod:`loremaster.findings` uses — one lazily-opened,
signed-in WS connection, self-healed on a mid-life transport failure, reusing the
shared transaction / error-classification seams in :mod:`loremaster.store._txn`
(``bootstrap_session`` / ``run_query`` / ``execute_transaction`` /
``retry_on_conflict``). It introduces NO retry / classification / query policy of
its own (finding #102/#120): every read/write routes through the ONE shared
single-statement seam ``run_query`` via :meth:`~PrincipalStore._query`.

The public surface:

    Principal:                             # a frozen value object (pydantic model)
        id: str                            # str(RecordID)
        email: str                         # REQUIRED, UNIQUE — the admission key
        subject: str | None                # option<string> UNIQUE — NONE until 39 fills it
        display_name: str | None
        status: str                        # {active, suspended}, DEFAULT active
        role: str                          # {member, admin}, DEFAULT member (least-privilege)
        expires_at: datetime | None
        created_at: datetime               # tz-aware UTC, engine-stamped

    PrincipalStore(*, url, namespace, database, user, password):
        async ensure_ready() -> None
        async create(*, email, subject=None, role=None, display_name=None,
                     expires_at=None) -> Principal
        async get_by_subject(subject) -> Principal | None
        async get_by_email(email) -> Principal | None
        async list() -> list[Principal]
        async set_status(*, email, status) -> Principal
        async set_subject(*, email, subject) -> Principal   # 39's fill-on-login primitive
        async close() -> None

    Exceptions: PrincipalStoreError(RuntimeError);
                PrincipalNotFoundError(PrincipalStoreError).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, SecretStr
from surrealdb import AsyncSurreal

from loremaster.config import (
    LoreConfig,
    load_surreal_only_config,
    resolve_config_value,
    resolve_secret,
)
from loremaster.index.records import sha512_hex
from loremaster.sanitise import safe_str
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    StoreHandle,
    SurrealConnectionError,
    SurrealStoreError,
    TxnContentionExhaustedError,
    _SurrealConnection,
    bootstrap_session,
    execute_transaction,
    run_query,
    signin_credentials,
    wrap_store_rejection,
)
from loremaster.store.surreal_schema import (
    _KEEP_TYPES,
    _PRINCIPAL_ROLES,
    _PRINCIPAL_STATUS_ACTIVE,
    _PRINCIPAL_STATUS_SUSPENDED,
    _PRINCIPAL_STATUSES,
    KEEP_TABLE,
    MEMORY_TABLE,
    PRINCIPAL_KEY_TABLE,
    PRINCIPAL_TABLE,
    generate_principal_ddl,
)

# The principal role the migration prefers as THE operator (the project keep's keeper). Kept as
# the shipped value string (mirrors ``lorerunes.pdp.PRINCIPAL_ROLE_ADMIN`` without importing the
# PDP into the store-orchestration CLI); ``Principal.role`` is validated against ``_PRINCIPAL_ROLES``.
_ROLE_ADMIN = "admin"

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from loremaster.governed import MigrateGovernedResult
    from loremaster.keeps import KeepStore
    from loremaster.principal_keys import PrincipalKey, PrincipalKeyStore

    # The uniform admin-verb handler signature (dict-dispatched by ``main``). A lazy
    # (``from __future__`` string) annotation, so ``PrincipalKeyStore`` need not be
    # imported at runtime — its module imports THIS one (``Principal``), and a runtime
    # import here would be a cycle.
    _VerbHandler = Callable[
        [argparse.Namespace, "PrincipalStore", "PrincipalKeyStore"], Awaitable[int]
    ]

    # The keep-verb handler signature (dict-dispatched by :func:`_dispatch_keep`). Keep
    # verbs route through a :class:`~loremaster.keeps.KeepStore` — which COMPOSES its own
    # ``PrincipalStore`` for email resolution — so they need neither the standalone
    # ``PrincipalStore`` nor the ``PrincipalKeyStore`` the principal verbs take. ``keeps``
    # imports THIS module (``PrincipalStore``), so ``KeepStore`` is a TYPE_CHECKING-only
    # import (the string annotation never triggers a runtime cycle).
    _KeepVerbHandler = Callable[[argparse.Namespace, "KeepStore"], Awaitable[int]]

logger = logging.getLogger(__name__)

# The ``principal`` columns the store reads/writes — named once so a rename is a
# single edit, never a literal drifting between the write CONTENT, the guarded
# UPDATEs and the row → value-object mapping (the ``finding`` ledger's ``_COL_*``
# idiom).
_COL_ID = "id"
_COL_EMAIL = "email"
_COL_SUBJECT = "subject"
_COL_DISPLAY_NAME = "display_name"
_COL_STATUS = "status"
_COL_ROLE = "role"
_COL_EXPIRES_AT = "expires_at"
_COL_CREATED_AT = "created_at"

# The ``principal_key.principal`` owner-link column — the cascade in :meth:`delete`
# filters key rows by it. Named once here so the DELETE literal never drifts from the
# ``principal_key`` schema (which owns the table + column definitions).
_COL_PRINCIPAL_KEY_OWNER = "principal"

# The ``keep.keeper`` owner-link column — the refuse-while-keeping read in :meth:`delete`
# (§FR-4) filters keep rows by it (an IndexScan on the ``keep_keeper`` index, packet-60
# Fork A). Named once here so the literal never drifts from the ``keep`` schema (which
# owns the table + column + index definitions).
_COL_KEEP_KEEPER = "keeper"

# The EXPLICIT read projection — NEVER ``SELECT *``. Store law §2: ``SELECT *`` OMITS
# a NONE-valued ``option<>`` column entirely (``row["subject"]`` KeyErrors on an
# email-pre-created row), whereas an explicit projection reads it back as ``None``.
# The ``option<>`` columns (subject/display_name/expires_at) are exactly why the
# reader must list its columns.
_READ_COLUMNS: tuple[str, ...] = (
    _COL_ID,
    _COL_EMAIL,
    _COL_SUBJECT,
    _COL_DISPLAY_NAME,
    _COL_STATUS,
    _COL_ROLE,
    _COL_EXPIRES_AT,
    _COL_CREATED_AT,
)
_READ_PROJECTION = ", ".join(_READ_COLUMNS)


class Principal(BaseModel):
    """A single human identity in the durable ``principal`` store.

    Attributes:
        id: The principal's ``str(RecordID)`` string id.
        email: The REQUIRED, UNIQUE human admission key.
        subject: The runtime OAuth identity (``AccessToken.client_id``), or ``None``
            for an email-pre-created principal not yet bound to a login (Model B).
        display_name: An optional presentational label.
        status: The admission state — one of ``{active, suspended}``.
        role: The authorization role — one of ``{member, admin}``.
        expires_at: An optional expiry instant (tz-aware UTC), or ``None`` to never
            expire.
        created_at: The tz-aware UTC timestamp the principal was created at.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    email: str
    subject: str | None
    display_name: str | None
    status: str
    role: str
    expires_at: datetime | None
    created_at: datetime


class PrincipalStoreError(RuntimeError):
    """Base class for every error :class:`PrincipalStore` raises."""


class PrincipalNotFoundError(PrincipalStoreError):
    """Raised when a principal email does not resolve to any row in the store."""


class PrincipalHasKeepsError(PrincipalStoreError):
    """Raised when a hard-delete is REFUSED because the principal keeps ≥1 keep.

    §FR-4 refuse-while-keeping: ``keep.keeper`` is a ``record<principal>`` FIELD LINK,
    which does NOT auto-clean on a keeper delete (store law §2) — so hard-deleting a
    principal who keeps ≥1 keep would leave a dangling ``keep.keeper`` (a #105-class
    ghost link on a surviving keep). The delete is REFUSED (loud, typed) instead,
    naming the kept keep ids AND the remediation, before any row is removed.

    Subclasses :class:`PrincipalStoreError` so the CLI's existing
    ``except PrincipalStoreError`` (:func:`_dispatch`) launders it to a ``lore-adm:``
    stderr line + ``exit 1`` with NO new catch clause. Remediation: reassign the keeper
    (``lore-adm set-keeper``) or delete the keep (``lore-adm delete-keep``), then re-run
    the delete.
    """


class PrincipalOwnsGovernedRowsError(PrincipalStoreError):
    """Raised when a hard-delete is REFUSED because the principal owns ≥1 GOVERNED row
    (packet 63a-ii, SF-63-5 / design §10.7-Z — the INTERIM refuse).

    ``memory.owner_principal`` is the FIRST ``record<principal>`` link on a GOVERNED row: a
    governed row's owner is a LIVE dependency (never the retired-history dangle the agent /
    audit back-links tolerate). Hard-deleting the owner would silently dangle it. Packet 64's
    admin ``set_owner`` orphans every owned governed row to NONE (audited) IN the delete
    transaction; until that mechanism lands the delete REFUSES loud instead — naming the count
    and the packet-64 mechanism — so nothing dangles and nothing leaks.

    Subclasses :class:`PrincipalStoreError` so the CLI's existing ``except PrincipalStoreError``
    (:func:`_dispatch`) launders it to a ``lore-adm:`` stderr line + ``exit 1`` with NO new catch
    clause — symmetric with :class:`PrincipalHasKeepsError`.
    """


# The GOVERNED owner column SF-63-5's refuse read filters on (design §4.1; the ONE name the
# schema emitter defines — ``surreal_schema._governed_field_specs``).
_COL_OWNER_PRINCIPAL = "owner_principal"


# :meth:`PrincipalStore.list` shadows the builtin ``list`` in the class namespace, so
# a bare ``list[...]`` return annotation on a method defined AFTER it would resolve to
# the METHOD, not the type (mypy ``valid-type``). These module-scope aliases resolve
# ``list`` where it is unambiguously the builtin, so the annotations stay correct.
_RowList = list[dict[str, Any]]
_PrincipalList = list[Principal]


class PrincipalStore:
    """Durable human-identity store over a single SurrealDB database.

    Owns the ``principal`` table (see :func:`generate_principal_ddl`) and rides the
    shared :mod:`loremaster.store._txn` transaction / error-classification seams, so
    every mutation is atomic and every failure surfaces as a typed store error. It
    clones the :class:`~loremaster.findings.FindingLedger` connection-owner idiom
    verbatim and introduces NO query/retry policy of its own (#102/#120).

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
        # each open their own underlying SDK connection (mirrors ``FindingLedger``).
        self._connect_lock = asyncio.Lock()

    # -- connection lifecycle ----------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking cloned verbatim from
        :meth:`~loremaster.findings.FindingLedger._ensure_connection`: the fast path
        never touches the lock, the session bootstrap is the ONE shared
        :func:`~loremaster.store._txn.bootstrap_session`, and any bootstrap failure —
        transport/auth fault OR exhausted contention alike — is wrapped as
        :class:`SurrealConnectionError` after the half-open socket is closed.

        Raises:
            SurrealConnectionError: The server is unreachable, rejected auth, or the
                session bootstrap exhausted its retry budget.
        """
        if self._connection is not None:
            return self._connection
        async with self._connect_lock:
            if self._connection is not None:
                # A concurrent caller connected while this one waited; mypy can't
                # model the cross-coroutine mutation across the ``await`` above.
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
                # Close the half-open socket so a failed connect never leaks a
                # dangling connection, then surface a typed connection error.
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "principal.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect and apply the principal schema slice — idempotent, safe to re-run.

        Applies :func:`~loremaster.store.surreal_schema.generate_principal_ddl` (the
        ``principal`` table + its two UNIQUE indexes) inside ONE ``BEGIN … COMMIT``
        via :func:`~loremaster.store._txn.execute_transaction`, which verifies EVERY
        statement's status (the SDK's plain ``query()`` inspects only the first). The
        table/indexes are ``IF NOT EXISTS`` (a second call neither raises nor wipes
        rows) while every FIELD is ``DEFINE FIELD OVERWRITE`` (finding #107 — a field
        change migrates a live store instead of silently no-op'ing against it).

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: A DDL statement was rejected by the engine.
        """
        await self._ensure_connection()
        ddl = generate_principal_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("principal.schema.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any); tolerant of a never-connected store."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal).

        A compare-and-swap (cloned from :class:`~loremaster.findings.FindingLedger`):
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
            # The socket is already gone — nothing left to release.
            logger.debug("principal.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection, self-healing.

        Delegates to :func:`~loremaster.store._txn.run_query` — the ONE shared
        single-statement attempt body every seam in the package calls (finding
        #120/#108). ``PrincipalStore`` hand-rolls NO retry/classification of its own:
        this seam is auto-discovered by ``test_retry_seam.py``'s ``_query`` scan, so
        the shared retry/backoff/exhaustion pins prove the sharing by mutation.
        """
        return await run_query(
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
            noun="principal query",
            label="principal.query.rejected",
            statement=statement,
            params=params or {},
            logger=logger,
        )

    async def _table_exists(self, table: str) -> bool:
        """Whether ``table`` is DEFINED on this database (via ``INFO FOR DB``).

        Fail-CLOSED for a safety gate (SF-63-5): a store / connection error during the probe
        PROPAGATES (never silently read as 'absent'), so a caller that refuses a delete on this can
        never fail OPEN on a transient fault — only a genuinely-undefined table reads ``False``.
        """
        info = await self._query("INFO FOR DB")
        tables = info.get("tables", {}) if isinstance(info, dict) else {}
        return table in tables

    # -- create / read ------------------------------------------------------

    async def create(
        self,
        *,
        email: str,
        subject: str | None = None,
        role: str | None = None,
        display_name: str | None = None,
        expires_at: datetime | None = None,
    ) -> Principal:
        """Create a principal, minting an engine-assigned id.

        Model B: ``email`` is REQUIRED; ``subject`` is OPTIONAL (an email-only create
        is the admin pre-create path — ``subject`` decodes to NONE until packet 39
        fills it on first login). A CONTENT write (store law §2) carries a column
        ONLY when it is provided, so an omitted ``option<>`` column takes NONE and an
        omitted defaulted column takes its DDL DEFAULT: ``status`` defaults ``active``
        (never named on create), ``role`` defaults ``member`` (least-privilege) when
        omitted, and ``created_at`` self-stamps via ``DEFAULT time::now()``.

        A duplicate ``email``, or a duplicate non-NONE ``subject``, is rejected by the
        UNIQUE backstop and wrapped LOUD as :class:`PrincipalStoreError` (Consumer
        Law — never a raw engine error bubbling through, never a silent success). Two
        email-only principals (both ``subject`` NONE) coexist — a UNIQUE index over a
        nullable column admits any number of NULLs.

        Args:
            email: The REQUIRED, UNIQUE human admission key.
            subject: The OAuth identity to bind now (the OAuth-direct path), or
                ``None`` for an email-only pre-create.
            role: The authorization role, or ``None`` to take the ``member`` default.
            display_name: An optional presentational label.
            expires_at: An optional tz-aware expiry instant (binds as a Python
                datetime — store law §2, never stringified).

        Returns:
            The created :class:`Principal` (a FRESH value object).

        Raises:
            PrincipalStoreError: The email or subject collides with the UNIQUE index.
        """
        content: dict[str, Any] = {_COL_EMAIL: email}
        if subject is not None:
            content[_COL_SUBJECT] = subject
        if role is not None:
            content[_COL_ROLE] = role
        if display_name is not None:
            content[_COL_DISPLAY_NAME] = display_name
        if expires_at is not None:
            content[_COL_EXPIRES_AT] = expires_at
        # The UNIQUE backstop (email or subject) — wrap LOUD as PrincipalStoreError; a
        # transport fault / exhausted contention passes through untouched (it must not
        # masquerade as a UNIQUE collision). Finding #400: routed through the ONE seam.
        with wrap_store_rejection(
            PrincipalStoreError,
            f"could not create principal {email!r}: a principal with that email "
            f"or subject already exists",
        ):
            result = await self._query(
                f"CREATE {PRINCIPAL_TABLE} CONTENT $content RETURN AFTER",
                {"content": content},
            )
        rows = self._as_rows(result)
        if not rows:
            raise PrincipalStoreError(
                f"principal {email!r} vanished immediately after it was created"
            )
        return self._row_to_principal(rows[0])

    async def get_by_subject(self, subject: str) -> Principal | None:
        """Return the principal whose OAuth ``subject`` equals ``subject``, or ``None``.

        The lookup packet 39's admission runs (``WHERE subject = $client_id``); the
        UNIQUE ``subject`` index guarantees at most one match. A miss is ``None`` (not
        an error) — 39 branches on ``None`` to decide pre-create-vs-fill.
        """
        rows = self._as_rows(
            await self._query(
                f"SELECT {_READ_PROJECTION} FROM {PRINCIPAL_TABLE} WHERE {_COL_SUBJECT} = $subject",
                {"subject": subject},
            )
        )
        return self._row_to_principal(rows[0]) if rows else None

    async def get_by_email(self, email: str) -> Principal | None:
        """Return the principal whose ``email`` equals ``email``, or ``None``.

        The lookup 49's admin CLI runs; the UNIQUE ``email`` index guarantees at most
        one match. A miss is ``None`` (not an error).
        """
        rows = self._as_rows(
            await self._query(
                f"SELECT {_READ_PROJECTION} FROM {PRINCIPAL_TABLE} WHERE {_COL_EMAIL} = $email",
                {"email": email},
            )
        )
        return self._row_to_principal(rows[0]) if rows else None

    async def list(self) -> _PrincipalList:
        """Return every principal, ordered by ``created_at`` ascending.

        The table is bounded by the number of humans, so a full scan is free (there is
        no ``status`` index by design — spec §3 F3). A caller wanting a status subset
        filters client-side.
        """
        rows = self._as_rows(
            await self._query(
                f"SELECT {_READ_PROJECTION} FROM {PRINCIPAL_TABLE} ORDER BY {_COL_CREATED_AT}"
            )
        )
        return [self._row_to_principal(row) for row in rows]

    # -- mutation -----------------------------------------------------------

    async def set_status(self, *, email: str, status: str) -> Principal:
        """Set a principal's admission ``status`` (49's suspend/unsuspend verb).

        Keyed on ``email`` (the human identity 49 operates on). ``status`` is
        validated client-side against the closed domain
        :data:`~loremaster.store.surreal_schema._PRINCIPAL_STATUSES` for a clean
        error (the DDL ASSERT is the store-side backstop — defence in depth, both
        loud). An unknown email is a typed :class:`PrincipalNotFoundError`, never a
        silent no-op (which a naive ``UPDATE … WHERE`` returning an empty set is).

        Args:
            email: The principal to transition (its UNIQUE admission key).
            status: The target status — one of ``{active, suspended}``.

        Returns:
            The principal's updated state (a FRESH value object).

        Raises:
            ValueError: ``status`` is not in the closed status domain.
            PrincipalNotFoundError: No principal carries ``email``.
        """
        if status not in _PRINCIPAL_STATUSES:
            raise ValueError(
                f"principal status must be one of {list(_PRINCIPAL_STATUSES)}, got {status!r}"
            )
        result = await self._query(
            f"UPDATE {PRINCIPAL_TABLE} SET {_COL_STATUS} = $status "
            f"WHERE {_COL_EMAIL} = $email RETURN AFTER",
            {"status": status, "email": email},
        )
        rows = self._as_rows(result)
        if not rows:
            raise PrincipalNotFoundError(f"no principal with email {email!r}")
        return self._row_to_principal(rows[0])

    async def set_subject(self, *, email: str, subject: str) -> Principal:
        """Bind a principal's OAuth ``subject`` — packet 39's fill-on-login primitive.

        Keyed on ``email``. This is the UNCONDITIONAL email-keyed fill (design §5 /
        §7-F1b, operator-ruled): it does NOT structurally forbid re-pointing a
        principal that already has a different subject — packet 39 owns that guard by
        orchestration (it checks ``get_by_subject`` first and only fills a row whose
        subject is NONE). Setting a row's subject to ITS OWN current value is not a
        UNIQUE conflict, so idempotent re-login is safe. Binding a subject ALREADY
        owned by ANOTHER principal (subject-theft) is rejected by the UNIQUE index on
        the UPDATE path and wrapped LOUD as :class:`PrincipalStoreError`. An unknown
        email is a typed :class:`PrincipalNotFoundError`.

        Args:
            email: The principal to fill (its UNIQUE admission key).
            subject: The OAuth identity to bind.

        Returns:
            The principal's updated state (a FRESH value object).

        Raises:
            PrincipalNotFoundError: No principal carries ``email``.
            PrincipalStoreError: ``subject`` is already bound to another principal.
        """
        # The UNIQUE backstop on the UPDATE path — subject already bound elsewhere — wrapped
        # LOUD; a transport fault / exhausted contention passes through untouched. Finding
        # #400: routed through the ONE seam.
        with wrap_store_rejection(
            PrincipalStoreError,
            f"could not bind subject to principal {email!r}: that subject is "
            f"already bound to another principal",
        ):
            result = await self._query(
                f"UPDATE {PRINCIPAL_TABLE} SET {_COL_SUBJECT} = $subject "
                f"WHERE {_COL_EMAIL} = $email RETURN AFTER",
                {"subject": subject, "email": email},
            )
        rows = self._as_rows(result)
        if not rows:
            raise PrincipalNotFoundError(f"no principal with email {email!r}")
        return self._row_to_principal(rows[0])

    async def set_expires(self, *, email: str, expires_at: datetime | None) -> Principal:
        """Set or clear a principal's ``expires_at`` — 49's
        ``set-expiry`` verb (design §F1, Reading C).

        Clones :meth:`set_status`'s shape: keyed on ``email``; an unknown email is a
        typed :class:`PrincipalNotFoundError` (never a silent no-op on an empty
        UPDATE). ``expires_at`` binds as a Python datetime (store law §2 — never
        stringified); ``None`` clears via ``SET expires_at = NONE`` (⚠ an UPDATE
        OMITTING the column would leave it unchanged, so the clear path SETs it to
        NONE explicitly). Rides ``_query`` (no new policy).

        Args:
            email: The principal to adjust (its UNIQUE admission key).
            expires_at: The new tz-aware expiry instant, or ``None`` to never expire.

        Returns:
            The principal's updated state (a FRESH value object).

        Raises:
            PrincipalNotFoundError: No principal carries ``email``.
        """
        if expires_at is None:
            # ⚠ CLEAR path (design §F1): ``SET expires_at = NONE`` — an UPDATE that
            # OMITTED the column would leave the OLD value unchanged. The literal NONE
            # explicitly clears it.
            result = await self._query(
                f"UPDATE {PRINCIPAL_TABLE} SET {_COL_EXPIRES_AT} = NONE "
                f"WHERE {_COL_EMAIL} = $email RETURN AFTER",
                {"email": email},
            )
        else:
            # SET path: bind a Python datetime (store law §2 — never stringified).
            result = await self._query(
                f"UPDATE {PRINCIPAL_TABLE} SET {_COL_EXPIRES_AT} = $expires_at "
                f"WHERE {_COL_EMAIL} = $email RETURN AFTER",
                {"expires_at": expires_at, "email": email},
            )
        rows = self._as_rows(result)
        if not rows:
            raise PrincipalNotFoundError(f"no principal with email {email!r}")
        return self._row_to_principal(rows[0])

    async def delete(self, *, email: str) -> int:
        """HARD-delete a principal and CASCADE its keys — 49's
        ``delete`` verb (design §F2), REFUSED while the principal keeps a keep (§FR-4).

        §FR-4 REFUSE-WHILE-KEEPING: a principal who keeps ≥1 keep CANNOT be hard-deleted
        — ``keep.keeper`` is a ``record<principal>`` FIELD LINK that does NOT auto-clean
        on a keeper delete (store law §2), so the delete would leave a dangling
        ``keep.keeper``. The refusal is a loud, typed :class:`PrincipalHasKeepsError`,
        raised BEFORE any row is removed (state unchanged), naming the kept keep ids +
        the remediation (reassign the keeper or delete the keep, then re-delete). A
        member-only principal (keeps nothing) deletes cleanly — its ``member_of``
        memberships auto-cascade on the node delete (store law §4, probed
        ``scripts/probe_member_of_cascade.py`` — no explicit ``member_of`` DELETE).

        For a keeps-nothing principal the delete proceeds: it removes every
        ``principal_key`` owned by the principal (children FIRST — ``record<t>`` links do
        NOT auto-clean, store law §4) THEN the ``principal`` row, inside ONE
        :func:`~loremaster.store._txn.execute_transaction` so a half-cascade can never
        leave orphaned keys. Keyed on ``email``; an unknown email is a typed
        :class:`PrincipalNotFoundError`. Needs the ``KEEP_TABLE`` + ``PRINCIPAL_KEY_TABLE``
        names (import from ``surreal_schema``); does NOT need a ``KeepStore`` /
        ``PrincipalKeyStore`` instance (both reads run on its OWN connection). ⚠ The
        ``keep`` table MUST exist on this database for the refuse read — on the CLI path
        the dispatch readies the keep slice first (§FR-4 D3 / #131 dirty-store).

        ⚠ CASCADE FORWARD-SCOPE (design §F2 / §FR-4 PIN THE MISS): the delete now
        accounts for FOUR ``record<principal>`` links, each with its operator-ruled
        disposition —
          • ``principal_key.principal`` — children-first CASCADE (deleted above);
          • ``keep.keeper`` — REFUSE-WHILE-KEEPING (the loud refusal above, §FR-4);
          • ``audit.actor_principal`` — DANGLE-TOLERATED (packet 61a-w4); and
          • ``agent.owner_principal`` — DANGLE-TOLERATED (packet 62, Fork 3 / R3.2 /
            removed-behavior I4).
        The delete deliberately does NOT touch the two dangling back-links: those rows
        are retired-not-deleted history, a stale ``record<principal>`` back-link does NOT
        auto-clean (store law §2) and is not a correctness break, and cascading them
        would erase audit / fleet history. The FIFTH ``record<principal>`` link —
        ``memory.owner_principal`` (packet 63a-ii), a GOVERNED row's owner — IS a LIVE
        dependency (not this agent-node dangle), so it takes the REFUSE-INTERIM disposition
        below (SF-63-5 / design §10.7-Z): until packet 64's admin ``set_owner`` orphans
        owned governed rows to NONE (audited) inside the delete, an owner of ≥1 governed
        row is REFUSED loud. When a further NEW ``record<principal>`` link is added this
        MUST be revisited; the exact-set pin in ``test_principal_keys_schema.py`` reds
        until it is.

        Args:
            email: The principal to delete (its UNIQUE admission key).

        Returns:
            The number of ``principal_key`` rows cascaded (0 if the principal held
            none) — the CLI's audit line reports it alongside the email.

        Raises:
            PrincipalNotFoundError: No principal carries ``email``.
            PrincipalHasKeepsError: The principal keeps ≥1 keep (§FR-4) — the delete is
                refused, no rows removed, the kept keep ids named.
            PrincipalOwnsGovernedRowsError: The principal owns ≥1 governed row (SF-63-5) —
                the delete is refused (INTERIM, until packet 64's ``set_owner`` orphaning
                mechanism), no rows removed, the count + mechanism named.
        """
        principal = await self.get_by_email(email)
        if principal is None:
            raise PrincipalNotFoundError(f"no principal with email {email!r}")
        principal_id_part = principal.id.partition(":")[2] or principal.id
        # ⚠ §FR-4 REFUSE-WHILE-KEEPING (BEFORE any DELETE, so a refusal removes NOTHING).
        # A keeper cannot be hard-deleted while they keep — a ``keep.keeper`` FIELD LINK
        # does NOT auto-clean (store law §2), so the delete would dangle it. Read the
        # kept keep ids via an IndexScan on the ``keep_keeper`` index (packet-60 Fork A),
        # bound param, mirroring the ``principal_key`` count query below — NO KeepStore
        # dependency (issued on this store's OWN connection). ≥1 kept keep ⇒ loud refusal
        # naming ALL of them + the remediation.
        kept_keep_rows = self._as_rows(
            await self._query(
                f"SELECT {_COL_ID} FROM {KEEP_TABLE} "
                f"WHERE {_COL_KEEP_KEEPER} = type::record('{PRINCIPAL_TABLE}', $pid)",
                {"pid": principal_id_part},
            )
        )
        if kept_keep_rows:
            kept_keep_ids = [str(row[_COL_ID]) for row in kept_keep_rows]
            raise PrincipalHasKeepsError(
                f"cannot delete principal {email!r}: they keep {len(kept_keep_ids)} "
                f"keep(s) ({', '.join(kept_keep_ids)}) — reassign the keeper "
                f"(lore-adm set-keeper) or delete the keep (lore-adm delete-keep) first"
            )
        # ⚠ SF-63-5 REFUSE-WHILE-OWNING-A-GOVERNED-ROW (BEFORE any DELETE — packet 63a-ii,
        # design §10.7-Z). ``memory.owner_principal`` is a ``record<principal>`` link on a GOVERNED
        # row — a LIVE dependency, NOT the retired-history dangle the agent/audit back-links
        # tolerate. Hard-deleting the owner would silently dangle it. Packet 64's admin
        # ``set_owner`` will orphan every owned governed row to NONE (audited) INSIDE the delete
        # transaction; until that mechanism lands, REFUSE loud — naming the count + the mechanism —
        # rather than dangle. The count is an IndexScan on the §4.1 ``memory_owner_principal`` index.
        # ⚠ TOLERANT of a store WITHOUT the memory table (a pre-retrofit / principal-only store owns
        # no governed rows): gated on table EXISTENCE, never on swallowing an error — a connection
        # fault during the existence probe PROPAGATES (fail-CLOSED), never read as "0 owned rows".
        if await self._table_exists(MEMORY_TABLE):
            owned_rows = self._as_rows(
                await self._query(
                    f"SELECT count() FROM {MEMORY_TABLE} "
                    f"WHERE {_COL_OWNER_PRINCIPAL} = type::record('{PRINCIPAL_TABLE}', $pid) "
                    f"GROUP ALL",
                    {"pid": principal_id_part},
                )
            )
            owned_count = int(owned_rows[0].get("count", 0)) if owned_rows else 0
            if owned_count > 0:
                raise PrincipalOwnsGovernedRowsError(
                    f"cannot delete principal {email!r}: they own {owned_count} governed "
                    f"{MEMORY_TABLE} row(s) — a governed row's owner is a LIVE dependency (never a "
                    f"silent dangle). Packet 64's admin `set_owner` orphans them to NONE (audited) "
                    f"inside the delete; until then the delete is refused (SF-63-5)"
                )
        # Count the keys about to be cascaded — the CLI's audit line reports it. A
        # separate read (execute_transaction returns None), taken just before the
        # atomic cascade; for an admin op the tiny window is acceptable.
        count_rows = self._as_rows(
            await self._query(
                f"SELECT count() FROM {PRINCIPAL_KEY_TABLE} "
                f"WHERE {_COL_PRINCIPAL_KEY_OWNER} = type::record('{PRINCIPAL_TABLE}', $pid) "
                f"GROUP ALL",
                {"pid": principal_id_part},
            )
        )
        cascaded = int(count_rows[0].get("count", 0)) if count_rows else 0
        # ⚠ CHILDREN FIRST (store law §4 — ``record<t>`` links do NOT auto-clean), THEN
        # the parent, inside ONE ``execute_transaction`` so a half-cascade can never
        # leave orphaned keys. execute_transaction verifies EVERY statement's status.
        await execute_transaction(
            f"BEGIN;\n"
            f"DELETE {PRINCIPAL_KEY_TABLE} "
            f"WHERE {_COL_PRINCIPAL_KEY_OWNER} = type::record('{PRINCIPAL_TABLE}', $pid);\n"
            f"DELETE {PRINCIPAL_TABLE} WHERE {_COL_EMAIL} = $email;\n"
            f"COMMIT;\n",
            {"pid": principal_id_part, "email": email},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        return cascaded

    # -- reads / mapping ----------------------------------------------------

    def _row_to_principal(self, row: dict[str, Any]) -> Principal:
        """Map a raw ``principal`` row into a FRESH :class:`Principal` value object.

        Uses ``row[…]`` for the REQUIRED columns (``id``/``email``/``status``/``role``
        /``created_at`` — always present) and ``row.get(…)`` for the ``option<>`` ones
        (``subject``/``display_name``/``expires_at`` — store law §2: a ``RETURN
        AFTER`` / ``SELECT *`` omits a NONE ``option<>`` column, and even an explicit
        projection reads it back as ``None``). ``created_at`` is normalised to
        tz-aware UTC (the fleet-comparable anchor).
        """
        return Principal(
            id=str(row[_COL_ID]),
            email=str(row[_COL_EMAIL]),
            subject=self._optional_str(row.get(_COL_SUBJECT)),
            display_name=self._optional_str(row.get(_COL_DISPLAY_NAME)),
            status=str(row[_COL_STATUS]),
            role=str(row[_COL_ROLE]),
            expires_at=self._to_aware_utc(row.get(_COL_EXPIRES_AT)),
            created_at=self._require_aware_utc(row.get(_COL_CREATED_AT)),
        )

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        """Return ``None`` for an absent/NONE ``option<string>`` column, else its str."""
        return None if value is None else str(value)

    @staticmethod
    def _as_rows(result: Any) -> _RowList:
        """Narrow a ``SELECT``/``CREATE``/``UPDATE`` result to its list of dict rows."""
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    def _require_aware_utc(self, value: Any) -> datetime:
        """Normalise the REQUIRED ``created_at`` to tz-aware UTC, refusing a bad value.

        ``created_at`` is a non-``option`` column the schema always stamps, so a
        faithful row always carries a real datetime; a missing/uncoercible one is a
        corrupt row, refused LOUDLY rather than silently coerced.

        Raises:
            SurrealStoreError: The value is missing or cannot be read as a datetime.
        """
        coerced = self._to_aware_utc(value)
        if coerced is None:
            raise SurrealStoreError(
                f"principal row column {_COL_CREATED_AT!r} is missing or not a datetime "
                f"(got {type(value).__name__})"
            )
        return coerced

    @staticmethod
    def _to_aware_utc(value: Any) -> datetime | None:
        """Coerce a stored datetime into a tz-aware UTC datetime (or ``None``).

        The SDK's CBOR decoder returns tz-aware datetimes; a naive datetime or an
        ISO-string/wrapper shape is normalised defensively so a principal's datetimes
        are ALWAYS tz-aware (a naive stamp is the classic wrong-anchor bug for a value
        fleet agents in different timezones compare). ``None`` passes through.
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            aware = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
            return aware.astimezone(UTC)
        text = str(value).replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        aware = parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
        return aware.astimezone(UTC)


# --------------------------------------------------------------------------- #
# The admin CLI (packet 49, design §F6): ONE CLI covering BOTH principal verbs and
# key verbs, invoked as the ``lore-adm`` console script (``[project.scripts]
# lore-adm = "loremaster.principals:main"`` in pyproject.toml; operator ruling
# 2026-08-20 — NOT ``python -m loremaster.principals``, which stays a harmless
# fallback via the kept ``__main__`` guard). Lib + CLI live in the ONE module.
#
# It clones the ``index/cli.py`` house idiom (``build_parser`` + ``main(argv) -> int``)
# and the ``comms_cli.py`` CREDS-FREE config load (``LoreConfig.model_validate``, NOT
# ``load_config`` — LEAD RULING #6) + ``SurrealConnectionError``-laundering /
# loud-on-failure shape. There is NO ``--execute`` flag and NO dry-run mode (STRUCK by
# the operator 2026-08-20): EVERY verb executes its effect directly on invocation; only
# ``list`` / ``list-keys`` are reads. The nine verbs (design §F6): ``add`` / ``list`` /
# ``delete`` / ``suspend`` / ``unsuspend`` / ``set-expiry`` / ``mint-key`` /
# ``revoke-key`` / ``list-keys``. Stores are built from config via the sibling factories
# :func:`build_principal_store` / :func:`~loremaster.principal_keys.build_principal_key_store`.
# Unix philosophy: silent on success (a mutating verb prints nothing but ``delete``'s
# one-line audit summary and ``mint-key``'s one-time credential; the reads print their
# listing), LOUD on failure (a stderr line + non-zero exit).
# --------------------------------------------------------------------------- #

# The program name users see in ``--help`` / usage / error prefixes: the installed
# console-script name (pyproject ``[project.scripts] lore-adm``), the operator-mandated
# admin invocation (2026-08-20), NOT the internal module path. ``python -m
# loremaster.principals`` still works as a harmless fallback via the ``__main__`` guard.
_CLI_PROG = "lore-adm"

# The minted key secret's entropy (design §F4): ``secrets.token_urlsafe(32)`` — 256
# bits of URL-safe randomness, the high-entropy random token a fast unsalted content
# hash is correct for (NOT a password).
_SECRET_ENTROPY_BYTES = 32

# The dash shown for an absent optional field in a rendered listing.
_ABSENT_FIELD = "-"

# The per-``type`` ``--name`` CLI policy (design Fork B / FR-2 Q1). argparse cannot
# express "``--name`` required for some ``--type`` values but forbidden for others", so
# ``_cmd_create_keep`` enforces it at DISPATCH level, BEFORE any store write: ``project``
# and ``team`` REQUIRE ``--name``; a ``dm`` keep is nameless and FORBIDS one (a stray
# ``--name`` is a mistake, caught LOUD rather than silently dropped — FR-2 Q1); ``session``
# allows either (not listed here). These sets encode the CLI-owned policy the ruling places
# in the CLI, not the store — ``keep.name`` stays ``option<string>``. Coverage of the
# ``_KEEP_TYPES`` domain is a CHECKED VARIABLE in the contract
# (``test_keeps_cli.py::test_every_keep_type_has_a_declared_name_policy``): a new keep type
# reds that pin until its ``--name`` policy is decided (reach law #344/#345).
_KEEP_NAME_REQUIRED_TYPES: frozenset[str] = frozenset({"project", "team"})
_KEEP_NAME_FORBIDDEN_TYPES: frozenset[str] = frozenset({"dm"})


def _require_config(args: argparse.Namespace) -> Path:
    """The project ``lore.yaml`` the CLI resolves its store coordinate from. Loud
    failure (non-zero exit) when ``--config`` is absent."""
    if args.config is None:
        raise SystemExit(f"{_CLI_PROG}: --config <path to lore.yaml> is required")
    return Path(args.config)


def _parse_instant(value: str) -> datetime:
    """Parse an ISO-8601 CLI argument into a tz-aware UTC datetime (a naive value is
    interpreted as UTC — the fleet-comparable anchor; store law §2 binds it as a
    Python datetime, never stringified)."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    aware = parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    return aware.astimezone(UTC)


def _render_instant(instant: datetime | None) -> str:
    """An optional datetime as an ISO-8601 string, or ``-`` when absent."""
    return instant.isoformat() if instant is not None else _ABSENT_FIELD


def _render_principal_line(principal: Principal) -> str:
    """One rendered ``list`` row for a principal — every FREE-TEXT field
    (``email`` / ``display_name``) routed through the SHARED canonical LINE sanitiser
    :func:`loremaster.sanitise.safe_str` (P8d rendered-free-text law / design §F8 — a
    hostile value cannot forge a phantom row: a survived newline collapses to a space).
    ``status`` / ``role`` are closed-domain (DDL-validated) and rendered directly;
    ``expires_at`` is an engine-typed datetime."""
    display_name = (
        safe_str(principal.display_name)
        if principal.display_name is not None
        else _ABSENT_FIELD
    )
    return "  ".join(
        [
            safe_str(principal.email),
            display_name,
            principal.status,
            principal.role,
            f"expires={_render_instant(principal.expires_at)}",
        ]
    )


def _render_key_line(key: PrincipalKey) -> str:
    """One rendered ``list-keys`` row for a key — the free-text ``name`` routed through
    the SHARED :func:`loremaster.sanitise.safe_str` (design §F8). The raw secret is
    unrecoverable (never stored, never rendered); only metadata is shown."""
    state = "revoked" if key.revoked_at is not None else "active"
    return "  ".join(
        [
            safe_str(key.name),
            state,
            f"created={_render_instant(key.created_at)}",
            f"expires={_render_instant(key.expires_at)}",
        ]
    )


def build_principal_store(config: LoreConfig) -> PrincipalStore:
    """Construct a :class:`PrincipalStore` from ``config`` — the sibling of
    :func:`loremaster.store.surreal.build_store`, reading the SAME coordinate accessors
    (``config.surreal.{url,namespace,user_env,password_env}`` +
    ``config.effective_surreal_database``) MINUS ``dim`` (an identity store is never
    embedded). Resolves the username via
    :func:`~loremaster.config.resolve_config_value` and the password via
    :func:`~loremaster.config.resolve_secret` exactly as ``build_store`` does.
    """
    return PrincipalStore(
        url=config.surreal.url,
        namespace=config.surreal.namespace,
        database=config.effective_surreal_database,
        user=resolve_config_value(config.surreal.user_env),
        password=resolve_secret(config.surreal.password_env),
    )


def build_keep_store(config: LoreConfig) -> KeepStore:
    """Construct a :class:`~loremaster.keeps.KeepStore` from ``config`` — the sibling of
    :func:`build_principal_store` and
    :func:`~loremaster.principal_keys.build_principal_key_store`, reading the SAME
    coordinate accessors (``config.surreal.{url,namespace,user_env,password_env}`` +
    ``config.effective_surreal_database``) MINUS ``dim`` (a collaboration store is never
    embedded). Resolves the username via
    :func:`~loremaster.config.resolve_config_value` and the password via
    :func:`~loremaster.config.resolve_secret`, exactly as ``build_store`` does.
    """
    # Lazy import: ``loremaster.keeps`` imports THIS module (``PrincipalStore``), so a
    # top-level import here is a cycle. PLC0415 is a house-ignored idiom.
    from loremaster.keeps import KeepStore

    return KeepStore(
        url=config.surreal.url,
        namespace=config.surreal.namespace,
        database=config.effective_surreal_database,
        user=resolve_config_value(config.surreal.user_env),
        password=resolve_secret(config.surreal.password_env),
    )


async def migrate_governed(
    *,
    table: str,
    store: StoreHandle,
    keep_store: KeepStore,
    principal_store: PrincipalStore,
    registry: Any = None,
) -> MigrateGovernedResult:
    """The idempotent governed-column backfill for ONE table (design §1.2 item 5 / §2 / §10.6 R4 —
    packet 63a STUB / runnable-RED, contract-63a). Backs the ``lore-adm migrate-governed`` CLI verb.

    Per the per-table :class:`~loremaster.governed.LegacyMapping` (§2.1): ``memory`` legacy rows
    → owner NONE/NONE, ``scope = keep:<project>`` (the canonical project keep minted via
    :meth:`KeepStore.get_or_create_keyed` ``key='project:lore'``); ``message`` rows → ``owner_agent
    = sender``, ``owner_principal = sender.owner_principal``, scope = project keep — REFUSING
    LOUD if ``agent`` has not been migrated first (§2.6 the checked ORDER: it asserts the agent
    NONE-count is 0). Idempotent: a second run backfills 0 and exits clean. NEVER run at boot
    (§2.3) — only at the 65 cutover. A one-shot cutover verb that always EXECUTES (the
    dry-run/--execute paradigm was struck 2026-08-20 — §10.7-W); the read-only preview is the
    separate ``report-unmigrated`` verb.

    The backfill UPDATE and the §2.6 agent-NONE-count both route through the injected ``store``
    :class:`~loremaster.store._txn.StoreHandle` — :func:`~loremaster.store._txn.run_query` /
    :func:`~loremaster.store._txn.execute_transaction` over ``store.acquire`` / ``store.drop`` /
    ``store.url`` (design §10.6 R4: no raw connection, no direct SDK call in this module; the verb
    borrows the target store's OWN retry/self-heal driver, so the verb and the tool path share one
    driver and one retry policy).

    Returns:
        A :class:`~loremaster.governed.MigrateGovernedResult` with the receipts. Refuses (sets
        ``refused=True`` + ``reason``) on the agent-first ORDER precondition or a multi-principal
        ``agent`` table (§2.1) — never a silent partial widening of visibility.
    """
    from loremaster.governed import MigrateGovernedResult

    if table == MEMORY_TABLE:
        return await _migrate_memory_scope(store, keep_store, principal_store)
    if table == "message":
        # §2.6 agent-first ORDER, fail-closed: a message row's owner_principal is read from
        # ``sender.owner_principal`` (NONE for every un-migrated agent), so migrating messages
        # before the ``agent`` table would silently land them member-invisible. At packet 63a only
        # ``memory`` is migrated (memory is 63a's governed consumer); the agent/message migration
        # lands in 63b, so this REFUSES rather than half-widen — naming the precondition.
        return MigrateGovernedResult(
            table=table,
            scanned=0,
            backfilled=0,
            already_migrated=0,
            refused=True,
            reason=(
                "cannot migrate `message` rows before the `agent` table is migrated — a message's "
                "owner_principal is read from sender.owner_principal, NONE for every un-migrated "
                "agent (§2.6 agent-first ORDER); run migrate-governed for `agent` first. The "
                "agent/message migration lands in packet 63b."
            ),
        )
    return MigrateGovernedResult(
        table=table,
        scanned=0,
        backfilled=0,
        already_migrated=0,
        refused=True,
        reason=(
            f"migrate-governed does not support table {table!r} at packet 63a — only `memory` "
            "(message/agent land 63b, brief lands 63c, task/finding land 64)"
        ),
    )


async def _migrate_memory_scope(
    store: StoreHandle,
    keep_store: KeepStore,
    principal_store: PrincipalStore,
) -> MigrateGovernedResult:
    """Backfill the ``memory`` legacy rows' NONE scope to the canonical PROJECT keep (§2.1/§2.2).

    UNOWNED-LEGACY: memory has no author column, so a legacy row's owner stays NONE/NONE (never
    fabricated) and only its ``scope`` is backfilled to ``keep:<project>`` — the fleet's shared
    keep, so a fleet member of the project household regains sight of its own memory. Idempotent:
    a re-run finds 0 NONE-scope rows and backfills nothing. All store access routes through the
    injected ``store`` handle's driver (R4).
    """
    from lorerunes.pdp import keep_scope

    from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult

    # Resolve THE operator principal (the project keep's keeper): the single-principal fleet's one
    # principal, or its single admin. Ambiguity is a REFUSAL, never a guess (§2.1 hard rule).
    principals = await principal_store.list()
    admins = [principal for principal in principals if principal.role == _ROLE_ADMIN]
    if len(admins) == 1:
        operator = admins[0]
    elif len(principals) == 1:
        operator = principals[0]
    else:
        return MigrateGovernedResult(
            table=MEMORY_TABLE,
            scanned=0,
            backfilled=0,
            already_migrated=0,
            refused=True,
            reason=(
                f"cannot resolve THE operator principal to keep the project keep "
                f"({len(principals)} principals, {len(admins)} admins) — provision a single "
                "operator principal (or a single admin) before migrating"
            ),
        )

    # Mint / get the canonical project keep (idempotent CAS on the UNIQUE key, SF-63-4).
    project_keep = await keep_store.get_or_create_keyed(
        key=PROJECT_KEEP_KEY, type="project", keeper_email=operator.email, name="lore"
    )
    project_scope = keep_scope(project_keep.id.partition(":")[2] or project_keep.id)

    unmigrated = await _scope_count(store, MEMORY_TABLE, none=True)
    already = await _scope_count(store, MEMORY_TABLE, none=False)
    if unmigrated == 0:
        return MigrateGovernedResult(
            table=MEMORY_TABLE,
            scanned=unmigrated + already,
            backfilled=0,
            already_migrated=already,
            refused=False,
        )
    # The backfill UPDATE, driver-routed (R4). ``scope IS NONE`` is index-served on the scope index
    # (probe-63 P5), so this is bounded even on a large dirty store.
    await run_query(
        acquire=store.acquire,
        drop=store.drop,
        url=store.url,
        noun="governed memory-scope backfill",
        label="governed.memory_backfill.rejected",
        statement=f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE",
        params={"scope": project_scope},
        logger=logger,
    )
    return MigrateGovernedResult(
        table=MEMORY_TABLE,
        scanned=unmigrated + already,
        backfilled=unmigrated,
        already_migrated=already,
        refused=False,
    )


async def _scope_count(store: StoreHandle, table: str, *, none: bool) -> int:
    """Count the rows of ``table`` whose ``scope`` IS (``none=True``) / IS NOT NONE, driver-routed.

    Index-served on the scope index (``= NONE`` / a real scope both IndexScan on 3.2.4 — probe-63
    P5). A ``count() … GROUP ALL`` over an empty set returns no row, so an absent count reads 0.
    """
    result = await run_query(
        acquire=store.acquire,
        drop=store.drop,
        url=store.url,
        noun="governed scope count",
        label="governed.scope_count.rejected",
        statement=(
            f"SELECT count() FROM {table} WHERE scope IS {'NONE' if none else 'NOT NONE'} GROUP ALL"
        ),
        params={},
        logger=logger,
    )
    if isinstance(result, list) and result and isinstance(result[0], dict):
        return int(result[0].get("count", 0) or 0)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """The argparse parser for the admin CLI (design §F6).

    ``prog`` is the installed console script ``lore-adm``; ``--config`` names the
    project ``lore.yaml`` the store coordinate is resolved from. The nine verbs are
    subcommands, each naming its principal by ``--email`` (except the ``list`` read).
    There is NO ``--execute`` flag and NO dry-run mode — every verb executes directly
    (operator ruling 2026-08-20).
    """
    parser = argparse.ArgumentParser(
        prog=_CLI_PROG,
        description=(
            "Manage lore principals (human identities) and their per-user API keys. "
            "Every verb executes directly; only `list`/`list-keys` are reads."
        ),
    )
    parser.add_argument(
        "--config", default=None, help="path to the project lore.yaml (store coordinate)"
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    def _with_email(name: str, help_text: str) -> argparse.ArgumentParser:
        sub = subcommands.add_parser(name, help=help_text)
        sub.add_argument(
            "--email", required=True, help="the principal's email (its admission key)"
        )
        return sub

    add = _with_email("add", "create a principal")
    add.add_argument("--display-name", default=None, help="an optional presentational label")
    add.add_argument(
        "--role",
        choices=list(_PRINCIPAL_ROLES),
        default=None,
        help="the authorization role (default: member, least-privilege)",
    )
    add.add_argument(
        "--expires", default=None, help="an optional ISO-8601 expiry instant (omitted = never)"
    )

    subcommands.add_parser("list", help="list every principal")

    _with_email("delete", "hard-delete a principal and cascade its keys (irreversible)")
    _with_email("suspend", "suspend a principal (reversible; denies its keys)")
    _with_email("unsuspend", "reactivate a suspended principal")

    set_expiry = _with_email("set-expiry", "set or clear a principal's expiry")
    expiry_choice = set_expiry.add_mutually_exclusive_group(required=True)
    expiry_choice.add_argument("--at", default=None, help="an ISO-8601 expiry instant")
    expiry_choice.add_argument(
        "--clear", action="store_true", help="clear the expiry (the principal never expires)"
    )

    mint_key = _with_email("mint-key", "mint a per-user API key (prints <name>:<secret> once)")
    mint_key.add_argument("--name", required=True, help="the key's label (unique per principal)")
    mint_key.add_argument(
        "--expires", default=None, help="an optional ISO-8601 key-expiry instant (omitted = never)"
    )

    revoke_key = _with_email("revoke-key", "revoke a principal's key by name")
    revoke_key.add_argument("--name", required=True, help="the label of the key to revoke")

    _with_email("list-keys", "list a principal's keys (names + flags; never a secret)")

    # -- keep (collaboration-space) verbs (packet 60 wave 2, design §6) ----------
    # Flat subcommands on the SAME lore-adm parser (like the principal verbs), routed
    # to KeepStore via a distinct handler table (:data:`_KEEP_VERB_HANDLERS`). Keeps are
    # addressed by ID (not email), so these name a keep by ``--keep`` and principals by
    # ``--keeper`` / ``--member``. NO ``--execute`` flag / dry-run (struck 2026-08-20).
    create_keep = subcommands.add_parser(
        "create-keep", help="create a keep (collaboration space); prints the new keep's id"
    )
    create_keep.add_argument(
        "--type",
        required=True,
        choices=list(_KEEP_TYPES),
        help="the keep flavour (closed domain, server-validated)",
    )
    create_keep.add_argument(
        "--keeper", required=True, help="the keeper (owner) principal's email"
    )
    create_keep.add_argument(
        "--name",
        default=None,
        help="an optional label (REQUIRED for project/team, allowed for session, omitted for dm)",
    )

    add_household = subcommands.add_parser(
        "add-household", help="add a member to a keep's household (idempotent)"
    )
    add_household.add_argument("--keep", required=True, help="the keep's id")
    add_household.add_argument("--member", required=True, help="the member principal's email")

    remove_household = subcommands.add_parser(
        "remove-household", help="remove a member from a keep's household (refuses the keeper)"
    )
    remove_household.add_argument("--keep", required=True, help="the keep's id")
    remove_household.add_argument("--member", required=True, help="the member principal's email")

    set_rank = subcommands.add_parser(
        "set-rank", help="set a household member's per-keep rank (store-validated)"
    )
    set_rank.add_argument("--keep", required=True, help="the keep's id")
    set_rank.add_argument("--member", required=True, help="the member principal's email")
    set_rank.add_argument("--rank", required=True, help="the rank to set (store-validated closed domain)")

    # -- keep remediation verbs (packet 61a-w1, §FR-4) — admin set_owner + delete on a
    # keep, so a keeper-principal blocked by refuse-while-keeping can be cleared. Both
    # route to KeepStore via :data:`_KEEP_VERB_HANDLERS` (their KeepStoreError launder).
    set_keeper = subcommands.add_parser(
        "set-keeper", help="reassign a keep's keeper (owner) to a new principal"
    )
    set_keeper.add_argument("--keep", required=True, help="the keep's id")
    set_keeper.add_argument(
        "--new-keeper", required=True, help="the new keeper (owner) principal's email"
    )

    delete_keep = subcommands.add_parser(
        "delete-keep", help="delete a keep and cascade its household edges (irreversible)"
    )
    delete_keep.add_argument("--keep", required=True, help="the keep's id")

    # -- governed migration (packet 63a, design §1.2 item 5 / §2) — the idempotent backfill verb
    # run ONCE at the 65 cutover (NEVER at boot, §2.3). 63a migrates `memory` (its consumer);
    # message/agent land 63b, brief 63c, task/finding 64.
    migrate_governed_parser = subcommands.add_parser(
        "migrate-governed",
        help="backfill a governed table's owner/scope columns (run once at the 65 cutover)",
    )
    migrate_governed_parser.add_argument(
        "--table", required=True, help="the governed table to migrate (63a supports: memory)"
    )
    # packet 63a-ii (§10.7-W): the dry-run/--execute paradigm was STRUCK (2026-08-20 operator
    # ruling); migrate-governed always EXECUTES. The read-only PREVIEW role the design wanted is
    # this SEPARATE `report-unmigrated` verb — a READ (the class the operator's ruling allows,
    # like `list`/`list-keys`) over `report_unmigrated_governed_rows`: it counts a table's
    # NONE-scope (member-invisible) rows without writing, so an operator can see what a
    # migrate-governed run WOULD backfill.
    report_unmigrated_parser = subcommands.add_parser(
        "report-unmigrated",
        help="report a governed table's un-migrated (NONE-scope) row count (a read; never writes)",
    )
    report_unmigrated_parser.add_argument(
        "--table", required=True, help="the governed table to inspect (63a supports: memory)"
    )

    return parser


# -- verb handlers (uniform signature so ``main`` dispatches by a dict) --------


async def _cmd_add(
    args: argparse.Namespace, principal_store: PrincipalStore, key_store: PrincipalKeyStore
) -> int:
    expires_at = _parse_instant(args.expires) if args.expires else None
    await principal_store.create(
        email=args.email,
        role=args.role,
        display_name=args.display_name,
        expires_at=expires_at,
    )
    return 0


async def _cmd_list(
    args: argparse.Namespace, principal_store: PrincipalStore, key_store: PrincipalKeyStore
) -> int:
    for principal in await principal_store.list():
        print(_render_principal_line(principal))
    return 0


async def _cmd_delete(
    args: argparse.Namespace, principal_store: PrincipalStore, key_store: PrincipalKeyStore
) -> int:
    cascaded = await principal_store.delete(email=args.email)
    print(f"deleted {safe_str(args.email)} ({cascaded} key(s) removed)")
    return 0


async def _cmd_suspend(
    args: argparse.Namespace, principal_store: PrincipalStore, key_store: PrincipalKeyStore
) -> int:
    await principal_store.set_status(email=args.email, status=_PRINCIPAL_STATUS_SUSPENDED)
    return 0


async def _cmd_unsuspend(
    args: argparse.Namespace, principal_store: PrincipalStore, key_store: PrincipalKeyStore
) -> int:
    await principal_store.set_status(email=args.email, status=_PRINCIPAL_STATUS_ACTIVE)
    return 0


async def _cmd_set_expiry(
    args: argparse.Namespace, principal_store: PrincipalStore, key_store: PrincipalKeyStore
) -> int:
    expires_at = None if args.clear else _parse_instant(args.at)
    await principal_store.set_expires(email=args.email, expires_at=expires_at)
    return 0


async def _cmd_mint_key(
    args: argparse.Namespace, principal_store: PrincipalStore, key_store: PrincipalKeyStore
) -> int:
    secret = secrets.token_urlsafe(_SECRET_ENTROPY_BYTES)
    credential = f"{args.name}:{secret}"
    expires_at = _parse_instant(args.expires) if args.expires else None
    await key_store.mint(
        email=args.email,
        name=args.name,
        secret_hash=sha512_hex(credential),
        expires_at=expires_at,
    )
    # The ONLY time the raw secret is ever emitted — verbatim, so the holder can present
    # it back; it is unrecoverable after this line (never stored raw).
    print(credential)
    return 0


async def _cmd_revoke_key(
    args: argparse.Namespace, principal_store: PrincipalStore, key_store: PrincipalKeyStore
) -> int:
    await key_store.revoke(email=args.email, name=args.name)
    return 0


async def _cmd_list_keys(
    args: argparse.Namespace, principal_store: PrincipalStore, key_store: PrincipalKeyStore
) -> int:
    for key in await key_store.list_for(email=args.email):
        print(_render_key_line(key))
    return 0


# -- keep-verb handlers (uniform (args, keep_store) signature; dispatched by
#    :data:`_KEEP_VERB_HANDLERS` through :func:`_dispatch_keep`) --------------------


async def _cmd_create_keep(args: argparse.Namespace, keep_store: KeepStore) -> int:
    """The ``create-keep`` verb — apply the per-``type`` ``--name`` rule, then create.

    The per-``type`` ``--name`` rule (design Fork B / FR-2 Q1) is a CLI-INPUT check
    enforced HERE at dispatch level (argparse cannot express conditional-required),
    BEFORE any store write so a rejected create leaves NO partial state: ``project`` and
    ``team`` REQUIRE ``--name`` (:data:`_KEEP_NAME_REQUIRED_TYPES`); a ``dm`` keep is
    nameless and FORBIDS ``--name`` (:data:`_KEEP_NAME_FORBIDDEN_TYPES`) — a stray one is
    a mistake caught LOUD, never silently stored as ``None``; ``session`` allows either. A
    violation raises :class:`ValueError` with a TEACHING message naming the offending
    option AND the ``--type``, laundered by :func:`_dispatch_keep` to a ``lore-adm:``
    stderr line + exit 1. Otherwise :meth:`KeepStore.create_keep` mints the keep (auto-
    adding the keeper to the household, Fork D) and its id is PRINTED — the ONE line
    ``create-keep`` emits (the :func:`_cmd_mint_key` print-the-credential precedent, so the
    operator can address the keep). Silent otherwise.
    """
    if args.type in _KEEP_NAME_REQUIRED_TYPES and args.name is None:
        raise ValueError(f"--name is required for --type {args.type}")
    if args.type in _KEEP_NAME_FORBIDDEN_TYPES and args.name is not None:
        raise ValueError(
            f"--name is not valid for --type {args.type} (a dm keep has no name concept)"
        )
    keep = await keep_store.create_keep(keeper_email=args.keeper, type=args.type, name=args.name)
    print(keep.id)
    return 0


async def _cmd_add_household(args: argparse.Namespace, keep_store: KeepStore) -> int:
    """The ``add-household`` verb — delegates to
    :meth:`KeepStore.add_household_member` (IDEMPOTENT: a re-add is a benign no-op,
    Fork F). Silent on success."""
    await keep_store.add_household_member(keep_id=args.keep, member_email=args.member)
    return 0


async def _cmd_remove_household(args: argparse.Namespace, keep_store: KeepStore) -> int:
    """The ``remove-household`` verb — delegates to
    :meth:`KeepStore.remove_household_member`; a ``KeeperLockoutError`` (removing the
    keeper) or a ``KeepNotFoundError`` (a ghost ``--keep``, FR-3) is laundered by
    :func:`_dispatch_keep` to a stderr line + exit 1. Silent on success."""
    await keep_store.remove_household_member(keep_id=args.keep, member_email=args.member)
    return 0


async def _cmd_set_rank(args: argparse.Namespace, keep_store: KeepStore) -> int:
    """The ``set-rank`` verb — delegates to :meth:`KeepStore.set_rank` (TRIVIAL today:
    the only legal rank is ``contributor``; a wrong rank is a loud store error laundered
    by :func:`_dispatch_keep`). Silent on success."""
    await keep_store.set_rank(keep_id=args.keep, member_email=args.member, rank=args.rank)
    return 0


async def _cmd_set_keeper(args: argparse.Namespace, keep_store: KeepStore) -> int:
    """The ``set-keeper`` verb — delegates to :meth:`KeepStore.set_keeper` (admin
    set_owner, §FR-4/D1: UPDATE the keep's ``keeper`` field to a new principal so a
    departing keeper's keep can be reassigned before deleting them). A ghost ``--keep``
    (:class:`~loremaster.keeps.KeepNotFoundError`) or a ghost ``--new-keeper`` email
    (:class:`~loremaster.keeps.KeepStoreError`) is laundered by :func:`_dispatch_keep` to
    a ``lore-adm:`` stderr line + exit 1. Silent on success."""
    await keep_store.set_keeper(keep_id=args.keep, new_keeper_email=args.new_keeper)
    return 0


async def _cmd_delete_keep(args: argparse.Namespace, keep_store: KeepStore) -> int:
    """The ``delete-keep`` verb — delegates to :meth:`KeepStore.delete_keep` (admin
    delete, §FR-4/D2: remove the keep node so a sole-member/dm keep's keeper can then be
    deleted; its ``member_of`` edges auto-cascade on the node delete — store law §4,
    probed). A ghost ``--keep`` (:class:`~loremaster.keeps.KeepNotFoundError`) is
    laundered by :func:`_dispatch_keep` to a stderr line + exit 1. Silent on success."""
    await keep_store.delete_keep(keep_id=args.keep)
    return 0


_VERB_HANDLERS: dict[str, _VerbHandler] = {
    "add": _cmd_add,
    "list": _cmd_list,
    "delete": _cmd_delete,
    "suspend": _cmd_suspend,
    "unsuspend": _cmd_unsuspend,
    "set-expiry": _cmd_set_expiry,
    "mint-key": _cmd_mint_key,
    "revoke-key": _cmd_revoke_key,
    "list-keys": _cmd_list_keys,
}

_KEEP_VERB_HANDLERS: dict[str, _KeepVerbHandler] = {
    "create-keep": _cmd_create_keep,
    "add-household": _cmd_add_household,
    "remove-household": _cmd_remove_household,
    "set-rank": _cmd_set_rank,
    "set-keeper": _cmd_set_keeper,
    "delete-keep": _cmd_delete_keep,
}


async def _dispatch(args: argparse.Namespace) -> int:
    """Load the (creds-free) config, build the stores, ready them, and run the selected
    verb. Keep verbs route to :func:`_dispatch_keep` (their own store); principal/key
    verbs run below. Domain failures are laundered to a stderr line + non-zero exit
    (loud on failure); a transport fault surfaces the same way."""
    # ``_require_config`` runs FIRST (before any branch), so a missing ``--config`` is a
    # loud ``SystemExit`` for EVERY verb, keep verbs included.
    config = load_surreal_only_config(_require_config(args))
    if args.command == "migrate-governed":
        return await _dispatch_migrate_governed(args, config)
    if args.command == "report-unmigrated":
        return await _dispatch_report_unmigrated(args, config)
    if args.command in _KEEP_VERB_HANDLERS:
        return await _dispatch_keep(args, config)
    # Lazy import: ``loremaster.principal_keys`` imports THIS module (``Principal``), so
    # a top-level import here is a cycle. PLC0415 is a house-ignored idiom.
    from loremaster.principal_keys import PrincipalKeyStoreError, build_principal_key_store

    principal_store = build_principal_store(config)
    key_store = build_principal_key_store(config)
    # §FR-4 D3(a) / #131: the ``delete`` verb READS the ``keep`` table (refuse-while-
    # keeping), so this branch readies the keep SLICE too (``generate_keep_ddl`` — keep +
    # member_of), NOT the full ``generate_ddl`` (the creds-free CLI has no embedder dim
    # and must not build HNSW/analyzers). Principal is readied FIRST below, satisfying
    # ``member_of``'s ENFORCED ``IN principal`` endpoint. Without this a store predating
    # packet 60 (no keep table) would crash the delete's keep-read — the dirty-store
    # blind spot every virgin-DB (full-schema) fixture cannot see (§1.6).
    keep_store = build_keep_store(config)
    try:
        # Principal FIRST (the record link's target + member_of's ENFORCED IN endpoint),
        # then the key table, then the keep slice.
        await principal_store.ensure_ready()
        await key_store.ensure_ready()
        await keep_store.ensure_ready()
        handler = _VERB_HANDLERS[args.command]
        return await handler(args, principal_store, key_store)
    except (
        PrincipalStoreError,
        PrincipalKeyStoreError,
        SurrealConnectionError,
        ValueError,
    ) as error:
        print(f"{_CLI_PROG}: {error}", file=sys.stderr)
        return 1
    finally:
        await keep_store.close()
        await key_store.close()
        await principal_store.close()


async def _dispatch_migrate_governed(args: argparse.Namespace, config: LoreConfig) -> int:
    """Build the stores + a driver ``StoreHandle`` over the unified store and run
    :func:`migrate_governed` (packet 63a). The governed tables (``memory`` at 63a) live in the SAME
    database the principal/keep stores connect to, so a handle over the principal store's own
    driver reaches them — and every store access inside the verb routes through it (R4). Receipts to
    stdout; a REFUSAL / domain failure is a stderr line + exit 1 (Unix philosophy: loud on failure).
    """
    from loremaster.keeps import KeepStoreError

    principal_store = build_principal_store(config)
    keep_store = build_keep_store(config)
    try:
        # The ``member_of`` ENFORCED endpoint (``principal``) FIRST, then keep+member_of.
        await principal_store.ensure_ready()
        await keep_store.ensure_ready()
        handle = StoreHandle(
            acquire=principal_store._ensure_connection,  # noqa: SLF001 - the driver triple, same module
            drop=principal_store._drop_connection,  # noqa: SLF001
            url=principal_store._url,  # noqa: SLF001
        )
        result = await migrate_governed(
            table=args.table,
            store=handle,
            keep_store=keep_store,
            principal_store=principal_store,
        )
        if result.refused:
            print(
                f"{_CLI_PROG}: migrate-governed --table {result.table} REFUSED: {result.reason}",
                file=sys.stderr,
            )
            return 1
        print(
            f"migrate-governed --table {result.table}: scanned={result.scanned} "
            f"backfilled={result.backfilled} already_migrated={result.already_migrated}"
        )
        return 0
    except (
        PrincipalStoreError,
        KeepStoreError,
        SurrealConnectionError,
        ValueError,
    ) as error:
        print(f"{_CLI_PROG}: {error}", file=sys.stderr)
        return 1
    finally:
        await keep_store.close()
        await principal_store.close()


async def _dispatch_report_unmigrated(args: argparse.Namespace, config: LoreConfig) -> int:
    """Report a governed table's un-migrated (NONE-scope) row count — the read-only PREVIEW verb
    (packet 63a-ii, §10.7-W: the preview role the struck dry-run paradigm no longer fills). Builds
    a driver ``StoreHandle`` over the unified store (the ``_dispatch_migrate_governed`` idiom) and
    runs :func:`~loremaster.governed.report_unmigrated_governed_rows` (R4: no raw connection). A
    READ — it never writes; the count goes to stdout, a domain/transport failure to stderr + exit 1.
    """
    from loremaster.governed import report_unmigrated_governed_rows

    principal_store = build_principal_store(config)
    try:
        await principal_store.ensure_ready()
        handle = StoreHandle(
            acquire=principal_store._ensure_connection,  # noqa: SLF001 - the driver triple, same module
            drop=principal_store._drop_connection,  # noqa: SLF001
            url=principal_store._url,  # noqa: SLF001
        )
        count = await report_unmigrated_governed_rows(handle, args.table)
        print(f"report-unmigrated --table {args.table}: unmigrated={count}")
        return 0
    except (
        PrincipalStoreError,
        # SurrealStoreError subsumes SurrealConnectionError AND a rejected SELECT (e.g. the
        # governed table does not exist on this store) — loud on failure, never a traceback.
        SurrealStoreError,
        ValueError,
    ) as error:
        print(f"{_CLI_PROG}: {error}", file=sys.stderr)
        return 1
    finally:
        await principal_store.close()


async def _dispatch_keep(args: argparse.Namespace, config: LoreConfig) -> int:
    """Build + ready the KeepStore, run the selected keep verb, and close both stores.

    The ``principal`` table is readied FIRST (via a ``PrincipalStore``): the
    ``member_of`` relation edge is ENFORCED with ``IN principal``, so its endpoint table
    must exist before :meth:`KeepStore.ensure_ready` applies the keep slice (the wave-1
    ``keep_env`` fixture / the :meth:`KeepStore.ensure_ready` docstring). ``KeepStore``
    composes its own ``PrincipalStore`` for email resolution but does NOT ready it.

    Store/domain failures are laundered to ``f"{_CLI_PROG}: {error}"`` on stderr +
    exit 1 (loud on failure), mirroring :func:`_dispatch`. Since FR-2 Q2b, ``KeepStore``
    WRAPS engine rejections as ``KeepStoreError`` at every write boundary (consumer-law
    parity with ``PrincipalStore.create``), so this catches ``KeepStoreError`` — which
    subsumes ``KeeperLockoutError`` / ``KeepNotFoundError`` — symmetric with :func:`_dispatch`
    catching ``PrincipalStoreError``, and NOT the raw ``SurrealStoreError`` (FR-2 D1). A
    transient ``SurrealConnectionError`` still passes through ``KeepStore`` untouched (a dead
    socket during a verb) and is caught here; ``ValueError`` is the per-``type`` ``--name``
    CLI-input check (project/team require a name; a ``dm`` forbids one).
    """
    # Lazy import: ``loremaster.keeps`` imports THIS module (``PrincipalStore``), so a
    # top-level import here is a cycle. PLC0415 is a house-ignored idiom.
    from loremaster.keeps import KeepStoreError

    principal_store = build_principal_store(config)
    keep_store = build_keep_store(config)
    try:
        # The ``member_of`` ENFORCED endpoint (``principal``) FIRST, then keep+member_of.
        await principal_store.ensure_ready()
        await keep_store.ensure_ready()
        handler = _KEEP_VERB_HANDLERS[args.command]
        return await handler(args, keep_store)
    except (
        KeepStoreError,
        SurrealConnectionError,
        ValueError,
    ) as error:
        print(f"{_CLI_PROG}: {error}", file=sys.stderr)
        return 1
    finally:
        await keep_store.close()
        await principal_store.close()


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint — parse args and run the verb on a fresh event loop.

    Returns a process exit code (0 = success, non-zero = failure). ``asyncio.run`` mints
    a loop, so a caller ALREADY inside one must run this off the loop (a worker thread) —
    the house ``index/cli.py`` idiom.
    """
    args = build_parser().parse_args(argv)
    return asyncio.run(_dispatch(args))


if __name__ == "__main__":
    raise SystemExit(main())
