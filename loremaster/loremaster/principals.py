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

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, SecretStr
from surrealdb import AsyncSurreal

from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    SurrealStoreError,
    TxnContentionExhaustedError,
    _SurrealConnection,
    bootstrap_session,
    execute_transaction,
    run_query,
    signin_credentials,
)
from loremaster.store.surreal_schema import (
    _PRINCIPAL_STATUSES,
    PRINCIPAL_TABLE,
    generate_principal_ddl,
)

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
        try:
            result = await self._query(
                f"CREATE {PRINCIPAL_TABLE} CONTENT $content RETURN AFTER",
                {"content": content},
            )
        except (SurrealConnectionError, TxnContentionExhaustedError):
            # A transport fault / exhausted contention is never a domain rejection —
            # propagate untouched (it must not masquerade as a UNIQUE collision).
            raise
        except SurrealStoreError as error:
            # The UNIQUE backstop (email or subject) — wrap LOUD.
            raise PrincipalStoreError(
                f"could not create principal {email!r}: a principal with that email "
                f"or subject already exists"
            ) from error
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
        try:
            result = await self._query(
                f"UPDATE {PRINCIPAL_TABLE} SET {_COL_SUBJECT} = $subject "
                f"WHERE {_COL_EMAIL} = $email RETURN AFTER",
                {"subject": subject, "email": email},
            )
        except (SurrealConnectionError, TxnContentionExhaustedError):
            # A transport fault / exhausted contention is never a domain rejection.
            raise
        except SurrealStoreError as error:
            # The UNIQUE backstop on the UPDATE path — subject already bound elsewhere.
            raise PrincipalStoreError(
                f"could not bind subject to principal {email!r}: that subject is "
                f"already bound to another principal"
            ) from error
        rows = self._as_rows(result)
        if not rows:
            raise PrincipalNotFoundError(f"no principal with email {email!r}")
        return self._row_to_principal(rows[0])

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
