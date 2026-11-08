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
import contextlib
import contextvars
import dataclasses
import logging
import re
import secrets
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, SecretStr

from loremaster.config import (
    LoreConfig,
    load_surreal_only_config,
    resolve_config_value,
    resolve_secret,
)
from loremaster.index.records import sha512_hex
from loremaster.logging_setup import RedactingFilter, scrub_text
from loremaster.sanitise import safe_str, sanitise_line
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    StoreHandle,
    SurrealConnectionError,
    SurrealStoreError,
    TxnContentionExhaustedError,
    _SurrealConnection,
    bootstrap_session,
    ensure_ready_operation,
    execute_transaction,
    open_surreal_connection,
    record_key,
    record_text,
    required_datetime,
    run_query,
    signin_credentials,
    stored_datetime,
    wrap_store_rejection,
)
from loremaster.store.surreal_schema import (
    _KEEP_TYPES,
    _PRINCIPAL_ROLES,
    _PRINCIPAL_STATUS_ACTIVE,
    _PRINCIPAL_STATUS_SUSPENDED,
    _PRINCIPAL_STATUSES,
    AGENT_TABLE,
    BRIEF_TABLE,
    KEEP_TABLE,
    MEMORY_TABLE,
    MESSAGE_TABLE,
    PRINCIPAL_KEY_TABLE,
    PRINCIPAL_TABLE,
    generate_principal_ddl,
)

# The principal role the migration prefers as THE operator (the project keep's keeper). Kept as
# the shipped value string (mirrors ``lorerunes.pdp.PRINCIPAL_ROLE_ADMIN`` without importing the
# PDP into the store-orchestration CLI); ``Principal.role`` is validated against ``_PRINCIPAL_ROLES``.
_ROLE_ADMIN = "admin"

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterator

    from loremaster.governed import MigrateGovernedResult, MigratePreconditionCounts, OwnerClassification
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
            connection = open_surreal_connection(self._url)
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

    @ensure_ready_operation
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
        PROPAGATES (never silently read as 'absent'), and so does a wrong-shaped answer
        (:func:`loremaster.governed.map_of` raises ``SurrealStoreError``), so a caller that refuses a
        delete on this can never fail OPEN — only a genuinely-undefined table reads ``False``.
        """
        from loremaster.governed import map_of

        # am-37 §13.1 item 1 (B-D1): the ONE fail-closed INFO-map reader. A wrong-shaped answer RAISES
        # the store class — it used to read as "no tables", so ``delete`` SKIPPED the SF-63-5
        # owned-row guard on a garbage answer (fail-OPEN).
        info = map_of(
            await self._query("INFO FOR DB"), noun="INFO FOR DB (table-existence probe)", required=("tables",)
        )
        return table in info["tables"]

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
            f"could not create principal {email!r}",
        ):
            result = await self._query(
                f"CREATE {PRINCIPAL_TABLE} CONTENT $content RETURN AFTER",
                {"content": content},
            )
        rows = self._as_rows(result, noun="principal create", landed=True)
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
            ),
            noun="principal lookup by subject",
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
            ),
            noun="principal lookup by email",
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
            ),
            noun="principal list",
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
            PrincipalStoreError: The store rejected the UPDATE (wrapped by ``wrap_store_rejection``,
                am-37 §12; the engine's typed cause is chained as ``__cause__``); a transport fault /
                exhausted contention passes through untouched.
        """
        if status not in _PRINCIPAL_STATUSES:
            raise ValueError(
                f"principal status must be one of {list(_PRINCIPAL_STATUSES)}, got {status!r}"
            )
        # A store rejection on the UPDATE wraps LOUD as PrincipalStoreError (am-37 §12);
        # a transport fault / exhausted contention passes through untouched.
        with wrap_store_rejection(
            PrincipalStoreError,
            f"could not set status of principal {email!r} to {status!r}",
        ):
            result = await self._query(
                f"UPDATE {PRINCIPAL_TABLE} SET {_COL_STATUS} = $status "
                f"WHERE {_COL_EMAIL} = $email RETURN AFTER",
                {"status": status, "email": email},
            )
        rows = self._as_rows(result, noun="principal status update", landed=True)
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
            PrincipalStoreError: The store rejected the UPDATE — e.g. ``subject`` is already bound to
                another principal (the UNIQUE index); the engine's typed cause is chained as
                ``__cause__`` and printed by lore-adm (am-37 §13 A / F-13).
        """
        # The UNIQUE backstop on the UPDATE path (subject already bound elsewhere) or any other
        # store rejection — wrapped LOUD under a NEUTRAL context (am-37 §13 A / F-13: the typed cause
        # names the reason, the context never over-claims it); a transport fault / exhausted contention
        # passes through untouched. Finding #400: routed through the ONE seam.
        with wrap_store_rejection(
            PrincipalStoreError,
            f"could not bind subject to principal {email!r}",
        ):
            result = await self._query(
                f"UPDATE {PRINCIPAL_TABLE} SET {_COL_SUBJECT} = $subject "
                f"WHERE {_COL_EMAIL} = $email RETURN AFTER",
                {"subject": subject, "email": email},
            )
        rows = self._as_rows(result, noun="principal subject bind", landed=True)
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
            PrincipalStoreError: The store rejected the UPDATE (wrapped by ``wrap_store_rejection``,
                am-37 §12; the engine's typed cause is chained as ``__cause__``); a transport fault /
                exhausted contention passes through untouched.
        """
        # A store rejection on EITHER branch's UPDATE wraps LOUD as PrincipalStoreError
        # (am-37 §12); a transport fault / exhausted contention passes through untouched.
        with wrap_store_rejection(
            PrincipalStoreError,
            f"could not set expiry of principal {email!r}",
        ):
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
        rows = self._as_rows(result, noun="principal expiry update", landed=True)
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
            PrincipalStoreError: A store rejection or a wrong-shaped answer anywhere from the opening
                read through the cascade transaction (wrapped by ``wrap_store_rejection``, am-37 §12 /
                §13 B; the cause is chained as ``__cause__``) — the delete does not proceed; a transport
                fault / exhausted contention passes through untouched.
        """
        # am-37 §12: ONE wrap from the opening read THROUGH the cascade transaction — a store
        # rejection anywhere in it (incl. §10.1(a)'s malformed owned-row count) surfaces as
        # PrincipalStoreError. The typed refusals below (PrincipalNotFoundError /
        # PrincipalHasKeepsError / PrincipalOwnsGovernedRowsError) are not SurrealStoreError,
        # so the seam re-raises them untouched; a transport fault / exhausted contention too.
        with wrap_store_rejection(
            PrincipalStoreError,
            f"could not delete principal {email!r}",
        ):
            principal = await self.get_by_email(email)
            if principal is None:
                raise PrincipalNotFoundError(f"no principal with email {email!r}")
            principal_id_part = record_key(principal.id)
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
                ),
                noun="kept-keep lookup before a principal delete",
            )
            if kept_keep_rows:
                kept_keep_ids = [record_text(row[_COL_ID]) for row in kept_keep_rows]
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
            from loremaster.governed import group_all_count

            if await self._table_exists(MEMORY_TABLE):
                # am-37 §10.1(a): read through the ONE fail-CLOSED reader. A malformed answer raises
                # ``SurrealStoreError`` (the class a REJECTED count read raises too), which this
                # method's wrap (am-37 §12) surfaces as ``PrincipalStoreError("could not delete …")``;
                # either way the delete does NOT proceed — never a ``0`` that bypasses this guard and
                # dangles owned rows.
                owned_count = group_all_count(
                    await self._query(
                        f"SELECT count() FROM {MEMORY_TABLE} "
                        f"WHERE {_COL_OWNER_PRINCIPAL} = type::record('{PRINCIPAL_TABLE}', $pid) "
                        f"GROUP ALL",
                        {"pid": principal_id_part},
                    ),
                    noun="governed owned-row count",
                )
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
            # am-37 §13 B F-1: the ONE fail-closed GROUP ALL reader (a wrong-shaped answer raises —
            # it used to serve ``0`` / coerce ``"3"`` / raise ``TypeError``) — before the cascade runs.
            cascaded = group_all_count(
                await self._query(
                    f"SELECT count() FROM {PRINCIPAL_KEY_TABLE} "
                    f"WHERE {_COL_PRINCIPAL_KEY_OWNER} = type::record('{PRINCIPAL_TABLE}', $pid) "
                    f"GROUP ALL",
                    {"pid": principal_id_part},
                ),
                noun="cascaded principal-key count",
            )
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
            id=record_text(row[_COL_ID]),
            email=str(row[_COL_EMAIL]),
            subject=self._optional_str(row.get(_COL_SUBJECT)),
            display_name=self._optional_str(row.get(_COL_DISPLAY_NAME)),
            status=str(row[_COL_STATUS]),
            role=str(row[_COL_ROLE]),
            expires_at=stored_datetime(row.get(_COL_EXPIRES_AT), row="principal", column=_COL_EXPIRES_AT),
            created_at=required_datetime(row.get(_COL_CREATED_AT), row="principal", column=_COL_CREATED_AT),
        )

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        """Return ``None`` for an absent/NONE ``option<string>`` column, else its str."""
        return None if value is None else str(value)

    @staticmethod
    def _as_rows(result: Any, *, noun: str, landed: bool = False) -> _RowList:
        """A ``SELECT``/``CREATE``/``UPDATE`` result's rows, through the ONE fail-closed row-list policy
        :func:`loremaster.governed.rows_of` (am-37 §13 B): a non-list answer or a non-dict member RAISES
        ``SurrealStoreError`` — it is a store fault, never ``[]`` (which ``set_*`` / ``revoke`` / ``delete``
        would serve as "no such principal") and never a silently dropped member. ``[]`` is only ever the
        engine's own empty answer. :class:`~loremaster.keeps.KeepStore` reads through this too. ``noun`` is
        REQUIRED (am-37 §13.3 item 7: every caller names its read); ``landed=True`` marks a committed write's
        own answer (item 5)."""
        from loremaster.governed import rows_of

        return rows_of(result, noun=noun, landed=landed)




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
#: The package logger the lore-adm stderr handler attaches to (am-37 §13 A i); every store seam logs under it.
_CLI_LOGGER_NAME = "loremaster"

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

    ORDER (packet 63c-i-a; amendments 19 D-1, 21 CD-2, 22 F-1/F-2, 23 FK-3):

    1. **Validity first** — a ``table`` outside the governed set :data:`_MIGRATE_VALID_TABLES` is
       answered "not supported" with ZERO store I/O (#97: an invalid request reads nothing, and a typo
       is never answered with a store fact).
    2. **The store facts, ONCE, at the verb** — THE shared :func:`_agent_migration_preconditions`,
       and :func:`_verb_level_refusal` over its answer: an owned-but-unscoped agent (§2.1 — the
       grandfather rule is wrong for the WHOLE store) or an ownerless-but-scoped agent (a half-applied
       store) refuses EVERY valid ``--table`` with the SAME teaching, byte-inert.
    3. The table's leg (``brief``'s backfill lands at 63c-ii).

    Returns:
        A :class:`~loremaster.governed.MigrateGovernedResult` with the receipts. Refuses (sets
        ``refused=True`` + ``reason``, and ``scanned`` / ``already_migrated`` ``None`` — not
        measured) on an unsupported table, the store facts above, a leg's own precondition (the
        message leg's agent-first ORDER, dangling senders, message half-pairs) or an unresolvable
        operator — never a silent partial widening of visibility.
    """
    if _migrate_table_refusal(table) is not None:
        return _not_supported(table, table_defined=None)
    token = _OPERATOR_RESOLUTION.set(_OperatorResolution())
    try:
        return await _migrate_governed_resolved(
            table=table, store=store, keep_store=keep_store, principal_store=principal_store
        )
    finally:
        _OPERATOR_RESOLUTION.reset(token)


async def _migrate_governed_resolved(
    *, table: str, store: StoreHandle, keep_store: KeepStore, principal_store: PrincipalStore
) -> MigrateGovernedResult:
    """:func:`migrate_governed`'s body, run with THIS call's :class:`_OperatorResolution` record installed.

    Every operator resolution on the call — the precondition's classification read AND any leg's — fills
    that ONE record (amendment 36 FK-8); after the leg, its ``(total, admins)`` land on the ONE counts
    model whenever any resolution ran, and a leg's unresolved-operator refusal is rendered FROM that model.
    """
    preconditions = await _agent_migration_preconditions(store, table=table)
    # amendment 37 §6 M-2: THE one derivation of ``table_defined`` — ``INFO FOR DB`` has run by here (the
    # precondition read raises rather than answer without it), so every result from this point on carries
    # the MEASURED answer, handed to each constructor below; nothing carries a default.
    table_defined = table in preconditions.defined_tables
    counts = await _measured_counts(preconditions, principal_store)
    refusal = await _verb_level_refusal(preconditions, counts, principal_store)
    if refusal is not None:
        result = _refused(table, refusal, table_defined=table_defined)
    elif table not in _MIGRATE_LEGS:
        result = _not_supported(table, table_defined=table_defined)
    elif not table_defined:
        from loremaster.governed import MigrateGovernedResult

        result = MigrateGovernedResult(
            table=table,
            scanned=0,
            backfilled=0,
            already_migrated=0,
            refused=False,
            table_defined=table_defined,
            messages_left_unmigrated=None,
        )
    else:
        result = await _MIGRATE_LEGS[table](
            _LegCall(
                store=store,
                keep_store=keep_store,
                principal_store=principal_store,
                preconditions=preconditions,
                counts=counts,
                table_defined=table_defined,
            )
        )
    resolution = _OPERATOR_RESOLUTION.get()
    if resolution is not None and resolution.ran and counts.total_principals is None:
        from loremaster.governed import MigratePreconditionCounts

        counts = MigratePreconditionCounts(
            **{
                **counts.model_dump(),
                "total_principals": resolution.total_principals,
                "admin_principals": resolution.admin_principals,
            }
        )
    if isinstance(result.reason, _UnresolvedPurpose):
        result = dataclasses.replace(
            result,
            reason=_operator_unresolved_sentence(
                str(result.reason),
                total_principals=counts.total_principals,
                admin_principals=counts.admin_principals,
            ),
        )
    return dataclasses.replace(result, preconditions=counts)


async def _measured_counts(
    preconditions: AgentMigrationPreconditions, principal_store: PrincipalStore
) -> MigratePreconditionCounts:
    """THE measured counts (amendments 30/31/32): a field is ``None`` iff its read was gated off."""
    from loremaster.governed import MigratePreconditionCounts

    agent = preconditions.agent_facts_read
    message = preconditions.message_facts_read
    owners = {record_text(owner) for _row_id, owner in preconditions.owned_unscoped}
    classification: OwnerClassification | None = "empty" if agent else None
    total_principals: int | None = None
    admin_principals: int | None = None
    if agent and owners:
        operator = await resolve_operator_principal(principal_store)
        resolution = _OPERATOR_RESOLUTION.get()
        if resolution is not None:
            total_principals, admin_principals = resolution.total_principals, resolution.admin_principals
        if operator is None:
            classification = "unclassified"
        elif owners == {operator.id}:
            classification = "operator"
        elif operator.id in owners:
            classification = "mixed"
        else:
            classification = "foreign"
    return MigratePreconditionCounts(
        unscoped_agents=preconditions.unscoped_count if agent else None,
        owned_but_unscoped_agents=len(preconditions.owned_unscoped) if agent else None,
        scoped_but_ownerless_agents=len(preconditions.ownerless_scoped) if agent else None,
        dangling_sender_messages=len(preconditions.dangling_senders) if message else None,
        owned_but_unscoped_messages=len(preconditions.messages_owned_unscoped) if message else None,
        scoped_but_ownerless_messages=len(preconditions.messages_scoped_ownerless) if message else None,
        distinct_owner_principals=len(owners) if agent else None,
        owner_classification=classification,
        total_principals=total_principals,
        admin_principals=admin_principals,
    )


#: The ruled VALID ``--table`` set (amendment 22 F-1 / amendment 23 FK-3): the governed tables amendment
#: 19 D-1 names. ``brief`` is valid — a multi-principal or half-applied store is refused on it like every
#: other governed table — but its backfill leg lands at 63c-ii.
_MIGRATE_VALID_TABLES = (AGENT_TABLE, MEMORY_TABLE, MESSAGE_TABLE, BRIEF_TABLE)

#: The ``--table`` help's domain clause, DERIVED from :data:`_MIGRATE_VALID_TABLES` for BOTH table verbs
#: (am-37 §13 C N-3 / F-15) — never a restated list that drifts from the validator.
_TABLE_HELP_DOMAIN = f"one of: {', '.join(_MIGRATE_VALID_TABLES)}"

#: The two ``--table`` verbs' names, as the ONE validator renders them in a refusal.
_MIGRATE_VERB = "migrate-governed"
_REPORT_VERB = "report-unmigrated"


def _report_table_help_domain() -> str:
    """``report-unmigrated``'s ``--table`` help domain, DERIVED: the migrate set first (in its order), then
    every OTHER governed table (:func:`~loremaster.governed.governed_tables`, sorted) — the report accepts the
    whole governed set (am-37 §13.4), so its help must name all of it."""
    from loremaster.governed import governed_tables

    others = sorted(governed_tables() - set(_MIGRATE_VALID_TABLES))
    return f"one of: {', '.join((*_MIGRATE_VALID_TABLES, *others))}"


def _backticked(names: tuple[str, ...]) -> str:
    """``names`` as prose — each in its own backtick span, ``, ``-joined with a final ``and`` — so a refusal's
    table list is DERIVED from the constant it describes (the derived-prose class, am-37 §13.3 #31)."""
    spans = [f"`{name}`" for name in names]
    return spans[0] if len(spans) == 1 else f"{', '.join(spans[:-1])} and {spans[-1]}"


def _migrate_table_refusal(table: str) -> ValueError | None:
    """THE one validator (:func:`loremaster.governed.validate_governed_table`, am-37 §13.4) over the MIGRATE
    domain :data:`_MIGRATE_VALID_TABLES`: ``None`` when ``table`` is valid, else the refusal it raised.
    ``migrate-governed`` asks it inside :func:`migrate_governed` AND in :func:`_dispatch_migrate_governed`
    before any store is built — ``table`` is interpolated into the verb's statements, so no unvalidated name
    reaches one. (``report-unmigrated`` passes the wider GOVERNED domain to the same function.)"""
    from loremaster.governed import GovernedTableRefusedError, validate_governed_table

    try:
        validate_governed_table(table, domain=_MIGRATE_VALID_TABLES, verb=_MIGRATE_VERB)
    except GovernedTableRefusedError as refusal:
        return refusal
    return None


def _backfill_lands(table: str) -> str:
    """Where a valid-but-legless table's backfill lands, DERIVED from its
    :data:`~loremaster.governed.PENDING_GOVERNED_TABLES` entry (am-37 §13.4.2) — never a restated packet."""
    from loremaster.governed import PENDING_GOVERNED_TABLES

    pending = PENDING_GOVERNED_TABLES.get(table)
    return f"lands at packet {pending.owning_packet}" if pending is not None else "has no migrate leg yet"


def _refused(table: str, reason: str, *, table_defined: bool | None) -> MigrateGovernedResult:
    """A refusal receipt. ``scanned`` / ``already_migrated`` are ``None`` — a refusal serves ``None`` for any
    count it did not measure, and states in ``reason`` the counts its precondition DID read (amendment 22 §4 /
    amendment 24 FK-a: a ``0`` would be a served count describing no set); ``backfilled`` is the measured
    ``0``; ``messages_left_unmigrated`` is ``None`` (no refusal measures it). ``table_defined`` is the
    caller's derived answer (amendment 37 §6 M-2): the measured truth for a refusal AFTER
    ``INFO FOR DB``, ``None`` iff that read never ran.

    A ``refused=True`` result writes NOTHING: every refusal returns before any keep mint or stamp. (A leg
    whose backfill UPDATE RAISES after its idempotent project-keep mint is not a refusal — that keep may
    remain, cold audit 63c-i-a CA-2 / R-4.)"""
    from loremaster.governed import MigrateGovernedResult

    return MigrateGovernedResult(
        table=table,
        scanned=None,
        backfilled=0,
        already_migrated=None,
        refused=True,
        reason=reason,
        table_defined=table_defined,
        messages_left_unmigrated=None,
    )


def _not_supported(table: str, *, table_defined: bool | None) -> MigrateGovernedResult:
    """The "not supported" refusal. ``table_defined`` is the verb's derived answer (amendment 37 §6 M-2) and
    says what the verb actually DID before answering: ``None`` — an invalid name, answered with zero store
    I/O; a ``bool`` — a valid table with no migrate leg yet (``brief``), answered only after the store facts
    were read (and passed) at the verb, carrying whether that table is defined.

    Both table lists are DERIVED (am-37 §13.3 item 9 / #31): the "today:" list from
    :data:`_MIGRATING_TABLES`, the governed list from :data:`_MIGRATE_VALID_TABLES`."""
    if table_defined is not None:
        return _refused(
            table,
            f"{_MIGRATE_VERB} does not yet migrate `{table}` — its backfill {_backfill_lands(table)} "
            f"(today: {_backticked(_MIGRATING_TABLES)}); the store's governed-table preconditions were read "
            "and passed, and nothing was written",
            table_defined=table_defined,
        )
    refusal = _migrate_table_refusal(table)
    if refusal is None:
        raise AssertionError(f"`{table}` is a valid migrate table, answered not-supported with no store read")
    legless = "; ".join(
        f"`{name}`'s backfill {_backfill_lands(name)}"
        for name in _MIGRATE_VALID_TABLES
        if name not in _MIGRATING_TABLES
    )
    return _refused(
        table,
        f"{refusal}{f' ({legless})' if legless else ''}; nothing was read or written",
        table_defined=None,
    )


@dataclass
class _OperatorResolution:
    """What :func:`resolve_operator_principal` measured on ONE ``migrate_governed`` call (amendment 36 FK-8).

    Installed per call in :data:`_OPERATOR_RESOLUTION` (a ``ContextVar``, so concurrent calls never share
    one); EVERY resolution on the call writes it, and the verb carries its two counts onto the ONE
    :class:`~loremaster.governed.MigratePreconditionCounts`. Both ``None`` ⇔ no resolution ran.
    """

    total_principals: int | None = None
    admin_principals: int | None = None

    @property
    def ran(self) -> bool:
        """Whether any operator resolution ran on this call."""
        return self.total_principals is not None


_OPERATOR_RESOLUTION: contextvars.ContextVar[_OperatorResolution | None] = contextvars.ContextVar(
    "_operator_resolution", default=None
)


class _UnresolvedPurpose(str):
    """A leg's unresolved-operator refusal REASON before it is rendered: the leg knows only WHAT it needed
    the operator for; :func:`_migrate_governed_resolved` renders the sentence FROM the counts model once the
    call's resolution has landed on it (amendment 36 FK-8 — the counts are fields, never restated)."""


def _operator_unresolved_sentence(
    purpose: str, *, total_principals: int | None, admin_principals: int | None
) -> str:
    """THE teaching for an unresolvable operator — the ONE template every refusal renders (the verb-level
    one, each leg's, and the out-of-verb fallback): what the operator is needed FOR, the principal and
    admin counts it was resolved against (measured, never restated), and the remedy."""
    return (
        f"cannot resolve THE operator principal {purpose} ({total_principals} principals, "
        f"{admin_principals} admins) — provision a single operator principal (or a single admin) before "
        "migrating"
    )


async def resolve_operator_principal(principal_store: PrincipalStore) -> Principal | None:
    """THE operator principal, or ``None`` on ambiguity (packet 63b-ii-a, ruling §4.C / design §2.1).

    The single-principal fleet's ONE principal, or its single admin; ``None`` when neither disambiguates
    (0 principals, or ≥2 principals without exactly one admin). ONE IMPLEMENTATION all three governed
    migrate legs call (the #102 clone-chain class: the ambiguity rule lives ONCE, so a fix reaches
    memory AND agent AND message — proven by the value-mutation route pin). It answers "who keeps the
    canonical project keep" (memory / message scope backfill) and "who owns a legacy agent" (agent
    owner backfill). Ambiguity is a REFUSAL at each caller — a leg turns ``None`` into a teaching
    :class:`~loremaster.governed.MigrateGovernedResult` ``refused``, NEVER a fabricated guess.
    """
    principals = await principal_store.list()
    admins = [principal for principal in principals if principal.role == _ROLE_ADMIN]
    resolution = _OPERATOR_RESOLUTION.get()
    if resolution is not None:
        resolution.total_principals, resolution.admin_principals = len(principals), len(admins)
    if len(admins) == 1:
        return admins[0]
    if len(principals) == 1:
        return principals[0]
    return None


async def _operator_unresolved(principal_store: PrincipalStore, *, purpose: str) -> str:
    """A leg's refusal when :func:`resolve_operator_principal` answered ``None`` — ``purpose`` names what the
    operator is needed FOR at that call site.

    Inside a ``migrate_governed`` call (the only production caller) it answers the :class:`_UnresolvedPurpose`
    the verb renders from the counts model. Outside one there is no model to render from, so it measures the
    counts itself and renders THE same template (:func:`_operator_unresolved_sentence`) directly.
    """
    if _OPERATOR_RESOLUTION.get() is not None:
        return _UnresolvedPurpose(purpose)
    principals = await principal_store.list()
    admins = [principal for principal in principals if principal.role == _ROLE_ADMIN]
    return _operator_unresolved_sentence(
        purpose, total_principals=len(principals), admin_principals=len(admins)
    )


async def _migrate_memory_scope(
    store: StoreHandle,
    keep_store: KeepStore,
    principal_store: PrincipalStore,
    *,
    table_defined: bool,
    defined_fields: frozenset[str],
) -> MigrateGovernedResult:
    """Backfill the ``memory`` legacy rows' NONE scope to the canonical PROJECT keep (§2.1/§2.2).

    UNOWNED-LEGACY: memory has no author column, so a legacy row's owner stays NONE/NONE (never
    fabricated) and only its ``scope`` is backfilled to ``keep:<project>`` — the fleet's shared
    keep, so a fleet member of the project household regains sight of its own memory. Idempotent:
    a re-run finds 0 NONE-scope rows and backfills nothing. All store access routes through the
    injected ``store`` handle's driver (R4).

    ORDERING BOUND (am-37 §13.2): this leg's pre-boot schema gate (:func:`_schema_predates_refusal`) is its
    FIRST action — it runs before any leg read or write (operator resolution, keep mint, counts, backfill).
    A verb-level refusal (:func:`_verb_level_refusal`) may precede this gate; each such refusal is true
    independently of the schema, and this gate runs before any leg read or write.
    """
    from lorerunes.pdp import keep_scope

    from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult, governed_exempt

    # §1.9 item 1: the backfill statement is a FUNCTION-LOCAL literal passed to BOTH the statement-scoped
    # exemption and the execution — built FIRST so the pre-boot schema gate (am-37 §13 D) derives the
    # columns it needs from THIS text, before any read or write.
    backfill_statement = f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE"
    schema_refusal = _schema_predates_refusal(MEMORY_TABLE, backfill_statement, defined_fields)
    if schema_refusal is not None:
        return _refused(MEMORY_TABLE, schema_refusal, table_defined=table_defined)

    # Resolve THE operator principal (the project keep's keeper) through the ONE shared helper
    # (ruling §4.C / §6 ONE IMPLEMENTATION — memory AND agent AND message route through it, proven by
    # the value-mutation route pin). Ambiguity is a REFUSAL, never a guess (§2.1 hard rule).
    operator = await resolve_operator_principal(principal_store)
    if operator is None:
        return _refused(
            MEMORY_TABLE,
            await _operator_unresolved(principal_store, purpose="to keep the project keep"),
            table_defined=table_defined,
        )

    # Mint / get the canonical project keep (idempotent CAS on the UNIQUE key, SF-63-4).
    project_keep = await keep_store.get_or_create_keyed(
        key=PROJECT_KEEP_KEY, type="project", keeper_email=operator.email, name="lore"
    )
    project_scope = keep_scope(record_key(project_keep.id))

    unmigrated = await _scope_count(store, MEMORY_TABLE, none=True)
    already = await _scope_count(store, MEMORY_TABLE, none=False)
    if unmigrated == 0:
        return MigrateGovernedResult(
            table=MEMORY_TABLE,
            scanned=unmigrated + already,
            backfilled=0,
            already_migrated=already,
            refused=False,
            table_defined=table_defined,
            messages_left_unmigrated=None,
        )
    # The backfill UPDATE, driver-routed (R4). ``scope IS NONE`` is index-served on the scope index
    # (probe-63 P5), so this is bounded even on a large dirty store. It is NOT member-reachable
    # (admin-CLI-only), so it attributes at the F5 runtime seam via the NAMED
    # ``governed_exempt("migrate-governed")`` frame rather than a per-caller ``write_guard`` (design
    # §10.9-A CORRECTION step 4 / L2b) — exempt-WITH-JUSTIFICATION (the allowlist's second
    # evidence-backed triple), never a silently unattributed governed write.
    # §1.9 item 1 (adversary F-TRAP-2): the adjudicated statement is a FUNCTION-LOCAL variable,
    # NEVER a module constant. L1 attributes a module-level literal to ``<module>`` scope (an L1
    # orphan → RED), and R1 self-containment demands the literal, the seam call, and the exempt entry
    # live in the SAME symbol. ONE source in code, passed to BOTH the statement-scoped exemption (the
    # golden the F5 classifier's leg 2 matches) AND the executed statement.
    with governed_exempt("migrate-governed", statement=backfill_statement):
        stamped = await run_query(
            acquire=store.acquire,
            drop=store.drop,
            url=store.url,
            noun="governed memory-scope backfill",
            label="governed.memory_backfill.rejected",
            statement=backfill_statement,
            params={"scope": project_scope},
            logger=logger,
        )
    return MigrateGovernedResult(
        table=MEMORY_TABLE,
        scanned=unmigrated + already,
        backfilled=_rows_stamped(stamped, noun="governed memory-scope backfill"),
        already_migrated=already,
        refused=False,
        table_defined=table_defined,
        messages_left_unmigrated=None,
    )


async def _scope_count(store: StoreHandle, table: str, *, none: bool) -> int:
    """Count the rows of ``table`` whose ``scope`` IS (``none=True``) / IS NOT NONE, driver-routed.

    Index-served on the scope index (``= NONE`` / a real scope both IndexScan on 3.2.4 — probe-63
    P5). A ``count() … GROUP ALL`` over an empty set returns no row, so an EMPTY list reads 0; any other
    wrong-shaped answer raises (amendment 37 §6 F-12 — THE fail-closed policy :func:`_governed_select`
    applies: a wrong-shaped dependency never decides a write, via
    :func:`loremaster.governed.group_all_count`).
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
    from loremaster.governed import group_all_count

    return group_all_count(result, noun="governed scope count")


#: THE one bound on every list a governed-migration refusal serves (packet 63c-i-a, amendment 20 §8.2 —
#: one constant for "how much of a bounded list we serve", never a second literal): the offending agent
#: ids of the §2.1 and half-applied refusals, the other principals named, the dangling-sender messages,
#: and EACH message half-pair (per list). Originally the agent migrate's §2.1 row precondition's id
#: bound (ruling §6: "naming the count and the rows (ids, bounded)"; amendment-4 MP-C). WHY a bound
#: at all: the refusal is read by an operator at cutover, and on a store with thousands of
#: owned-but-unscoped rows an unbounded id list buries the remedy; the FULL count is always stated
#: beside the sample, so the reader loses no number. WHY this value: a screenful of ids is enough to
#: start adjudicating by hand. The value is NOT normative (amendment-6 R-3) — the refusal reads it
#: at CALL time, and its prose states the number of ids ACTUALLY shown, never this constant.
_REFUSAL_ID_SAMPLE_SIZE = 10


@dataclass(frozen=True)
class AgentMigrationPreconditions:
    """THE governed-migration store facts (packet 63c-i-a), read ONCE by :func:`migrate_governed` from
    :func:`_agent_migration_preconditions` and handed to the leg that needs them — the verb-level refusal
    and the message leg's guards DECIDE from this one answer, never from a private query of their own.

    Attributes:
        unscoped_count: Agents with ``scope IS NONE`` — THE unmigrated predicate ∀ governed tables. The
            message leg's agent-first ORDER guard (§2.6) refuses while it is > 0.
        owned_unscoped: ``(agent id, owner principal)`` for every agent with an owner but no scope — a
            multi-principal store, or the pkt-62–63b image population (amendment-1 E3); sorted by id.
        ownerless_scoped: Agent ids with a scope but no owner — a half-applied store (amendment 22 F-2).
        dangling_senders: ``(message id, sender)`` for every legacy (``scope IS NONE``) message whose
            ``sender`` link resolves to no row (amendment 23 FK-2). Read only for ``table='message'``.
        messages_owned_unscoped: Message ids with an owner but no scope — the message table's half-pair
            (i) (amendment 24 §2 door #2). Read only for ``table='message'``.
        messages_scoped_ownerless: Message ids with a scope but no owner — half-pair (ii) (amendment 25).
            Read only for ``table='message'``.
        defined_fields: The field names ``INFO FOR TABLE <table>`` lists for the ``--table`` being
            migrated (amendment 37 §13 D) — read ONCE, right after the ``INFO FOR DB`` gate and only when
            that table is DEFINED (empty otherwise: ``INFO FOR TABLE`` on an undefined table answers EMPTY
            maps, never an error — store-ref, so definedness is never inferred from it). Each leg's
            pre-boot schema gate (:func:`_schema_predates_refusal`) decides from THIS answer.
    """

    unscoped_count: int
    owned_unscoped: tuple[tuple[Any, Any], ...]
    ownerless_scoped: tuple[Any, ...]
    defined_tables: frozenset[str] = frozenset()
    agent_facts_read: bool = False
    message_facts_read: bool = False
    dangling_senders: tuple[tuple[Any, Any], ...] = ()
    messages_owned_unscoped: tuple[Any, ...] = ()
    messages_scoped_ownerless: tuple[Any, ...] = ()
    defined_fields: frozenset[str] = frozenset()


async def _governed_select(store: StoreHandle, *, noun: str, label: str, statement: str) -> list[Any]:
    """One parameterless governed-precondition SELECT, driver-routed (R4), read through the ONE
    fail-closed row-list policy :func:`loremaster.governed.rows_of` (amendment 37 §13 B F-7): a non-list
    answer, or a non-dict member (which a filter would have silently dropped — a precondition row that
    vanishes), RAISES :class:`SurrealStoreError`: a wrong-shaped dependency never decides a write."""
    from loremaster.governed import rows_of

    rows = await run_query(
        acquire=store.acquire,
        drop=store.drop,
        url=store.url,
        noun=noun,
        label=label,
        statement=statement,
        params={},
        logger=logger,
    )
    return rows_of(rows, noun=noun)


def _by_id(values: list[Any]) -> tuple[Any, ...]:
    """Deterministic order for a refusal's id sample: by the SDK's own rendering of the id."""
    return tuple(sorted(values, key=lambda value: str(value[0] if isinstance(value, tuple) else value)))


async def _agent_migration_preconditions(
    store: StoreHandle, *, table: str | None = None
) -> AgentMigrationPreconditions:
    """THE ONE governed-migration precondition read (packet 63c-i-a; amendments 19 D-1, 21 CD-1, 22 F-2,
    23 FK-2, 24 §2 door #2, 25, 26) — the verb-level refusal and the message leg's guards all decide from
    what THIS returns (routing is not sharing: no consumer re-derives any of it with its own query).

    A store with no ``agent`` table DEFINED (a memory-only store) has no agents: the agent reads are
    gated on ``INFO FOR DB``'s table set — the store is never queried for an undefined table, and a
    genuine store error propagates (never swallowed).

    For ``table == 'message'`` it also reads the message leg's two row facts, in THIS order — the order
    the message leg's refusal serves them in (amendment 26: deterministic, no precedence): (1) DANGLING
    SENDERS — legacy messages whose ``sender`` link resolves to no row (``sender.id IS NONE``: the
    dereference yields ``NONE`` for a missing record — store reference §6.4 — and, unlike
    ``record::exists``, is total over a NONE link; probed 2026-09-26 on the test store, instrument in
    ``REPORT-builder-63c-i-a-fix.md`` §P); (2) MESSAGE HALF-PAIRS — both halves.

    Args:
        store: The driver handle over the governed store.
        table: The ``--table`` being migrated (``message`` adds the message-leg reads).

    Returns:
        The :class:`AgentMigrationPreconditions` store facts, every list sorted by id.
    """
    from loremaster.governed import map_of

    # am-37 §13.1 item 1: the ONE fail-closed INFO-map reader (the cloned third shape policy that stood
    # here is deleted). ``tables`` is REQUIRED on this answer: a map without it is a wrong shape, never
    # "no tables defined".
    info = map_of(
        await run_query(
            acquire=store.acquire,
            drop=store.drop,
            url=store.url,
            noun="governed table probe",
            label="governed.table_probe.rejected",
            statement="INFO FOR DB",
            params={},
            logger=logger,
        ),
        noun="INFO FOR DB (governed-migration table probe)",
        required=("tables",),
    )
    defined = info["tables"]
    # am-37 §13 D: ONE ``INFO FOR TABLE`` read, immediately after the table gate and before ANY leg read or
    # write — only for a DEFINED ``--table`` (an undefined one short-circuits above: one ``INFO FOR DB``, no
    # field read). ``table`` reached here validated against ``_MIGRATE_VALID_TABLES`` by the verb.
    defined_fields: frozenset[str] = frozenset()
    if table is not None and table in defined:
        table_info = map_of(
            await run_query(
                acquire=store.acquire,
                drop=store.drop,
                url=store.url,
                noun="governed field probe",
                label="governed.field_probe.rejected",
                statement=f"INFO FOR TABLE {table}",
                params={},
                logger=logger,
            ),
            noun=f"INFO FOR TABLE {table} (governed-migration field probe)",
            required=("fields",),
        )
        defined_fields = frozenset(table_info["fields"])
    unscoped_count = 0
    owned_unscoped: list[tuple[Any, Any]] = []
    ownerless_scoped: list[Any] = []
    if AGENT_TABLE in defined:
        unscoped_count = await _scope_count(store, AGENT_TABLE, none=True)
        for row in await _governed_select(
            store,
            noun="governed agent half-pair precondition",
            label="governed.agent_precondition.rejected",
            statement=(
                f"SELECT id, owner_principal, scope FROM {AGENT_TABLE} "
                "WHERE (scope IS NONE AND owner_principal IS NOT NONE) "
                "OR (scope IS NOT NONE AND owner_principal IS NONE)"
            ),
        ):
            if row.get("scope") is None:
                owned_unscoped.append((row.get("id"), row.get("owner_principal")))
            else:
                ownerless_scoped.append(row.get("id"))
    dangling: list[tuple[Any, Any]] = []
    messages_owned_unscoped: list[Any] = []
    messages_scoped_ownerless: list[Any] = []
    if table == MESSAGE_TABLE and MESSAGE_TABLE in defined:
        dangling = [
            (row.get("id"), row.get("sender"))
            for row in await _governed_select(
                store,
                noun="governed message dangling-sender precondition",
                label="governed.message_dangling.rejected",
                statement=(
                    f"SELECT id, sender FROM {MESSAGE_TABLE} WHERE scope IS NONE AND sender.id IS NONE"
                ),
            )
        ]
        for row in await _governed_select(
            store,
            noun="governed message half-pair precondition",
            label="governed.message_half_pair.rejected",
            statement=(
                f"SELECT id, owner_principal, scope FROM {MESSAGE_TABLE} "
                "WHERE (scope IS NONE AND owner_principal IS NOT NONE) "
                "OR (scope IS NOT NONE AND owner_principal IS NONE)"
            ),
        ):
            if row.get("scope") is None:
                messages_owned_unscoped.append(row.get("id"))
            else:
                messages_scoped_ownerless.append(row.get("id"))
    return AgentMigrationPreconditions(
        defined_tables=frozenset(defined),
        agent_facts_read=AGENT_TABLE in defined,
        message_facts_read=table == MESSAGE_TABLE and MESSAGE_TABLE in defined,
        unscoped_count=unscoped_count,
        owned_unscoped=_by_id(owned_unscoped),
        ownerless_scoped=_by_id(ownerless_scoped),
        dangling_senders=_by_id(dangling),
        messages_owned_unscoped=_by_id(messages_owned_unscoped),
        messages_scoped_ownerless=_by_id(messages_scoped_ownerless),
        defined_fields=defined_fields,
    )


def _id_sample(ids: tuple[Any, ...] | list[Any]) -> str:
    """``First <shown> of <count> ids shown: <ids>.`` — the ONE bounded id render every governed-migration
    refusal serves: at most :data:`_REFUSAL_ID_SAMPLE_SIZE` (read at CALL time, never restated), each
    STORED id through THE shared :func:`~loremaster.sanitise.sanitise_line` (CA-1 / #484: a stored id is
    free text — no newline or control character reaches the served line), and the number stated is the
    number ACTUALLY shown."""
    shown = [sanitise_line(record_key(value)) for value in ids[:_REFUSAL_ID_SAMPLE_SIZE]]
    return f"First {len(shown)} of {len(ids)} ids shown: {', '.join(shown)}."


def _owned_unscoped_part(
    owned_unscoped: tuple[tuple[Any, Any], ...], operator: Principal | None, counts: MigratePreconditionCounts
) -> str:
    """The §2.1 owned-but-unscoped part — the owner sentence DERIVED from ``owner_classification`` and
    ``distinct_owner_principals`` (amendment 31); principal ids are SAMPLES."""
    head = f"{counts.owned_but_unscoped_agents} agent row(s) carry an owner but no scope (§2.1)"
    sample = _id_sample([row_id for row_id, _owner in owned_unscoped])
    classification = counts.owner_classification
    if classification == "unclassified":
        return (
            f"ALSO: {head}; their owners are UNCLASSIFIED — with the operator unresolved, any of them may "
            f"BE the operator. {sample}"
        )
    operator_id = operator.id if operator is not None else None
    # Compared through ONE text form (record_text, the form ``Principal.id`` carries — the C9 class: one
    # record compared through two text forms), SERVED as the bare key (B-2: the sentence names the table).
    bare_by_text = {
        record_text(owner): record_key(owner)
        for _row_id, owner in owned_unscoped
        if record_text(owner) != operator_id
    }
    named = [sanitise_line(bare_by_text[text]) for text in sorted(bare_by_text)[:_REFUSAL_ID_SAMPLE_SIZE]]
    if classification == "operator":
        owner_sentence = (
            "They are owned by the operator — registered by a pkt-62–63b image; see amendment-1 E3."
        )
    elif classification == "foreign":
        owner_sentence = (
            f"They are owned by {counts.distinct_owner_principals} other principal(s) "
            f"(first {len(named)} named: {', '.join(named)})."
        )
    else:
        # amendment 37 §6 F-9 (the am-34 §2 form): ONE integer, ``distinct_owner_principals``, rendered AS
        # THE TOTAL it measures (the operator included) — never labelled "other", and no second integer
        # (a shown-sample count) beside it. The ids after it are SAMPLES of the others.
        owner_sentence = (
            "They are owned by the operator — registered by a pkt-62–63b image; see amendment-1 E3 — and by "
            f"others: {counts.distinct_owner_principals} distinct principal(s) in all, the operator among "
            f"them (a sample of the others: {', '.join(named)})."
        )
    return " ".join([f"{head}.", owner_sentence, sample])


async def _verb_level_refusal(
    preconditions: AgentMigrationPreconditions,
    counts: MigratePreconditionCounts,
    principal_store: PrincipalStore,
) -> str | None:
    """The verb-level store refusal (amendment 19 D-1 / 20 §8.4 / 22 F-2 / 24 door #1), or ``None``.

    A STORE fact, so it answers every valid ``--table`` with the SAME text: owned-but-unscoped agents
    (§2.1) and ownerless-but-scoped agents (half-applied) — ONE refusal naming EVERY problem present, each
    with its true count and a bounded id sample (a refusal naming one of two problems buys the operator
    two round trips). When owned-but-unscoped rows exist and the operator is unresolvable, the operator
    remedy comes FIRST (nothing else can be diagnosed until it is resolved) and the owners are NOT
    classified."""
    parts: list[str] = []
    if preconditions.owned_unscoped:
        operator = await resolve_operator_principal(principal_store)
        if counts.owner_classification == "unclassified":
            sentence = _operator_unresolved_sentence(
                "to classify the rows below",
                total_principals=counts.total_principals,
                admin_principals=counts.admin_principals,
            )
            parts.append(f"{sentence}.")
        parts.append(_owned_unscoped_part(preconditions.owned_unscoped, operator, counts))
    if preconditions.ownerless_scoped:
        count = counts.scoped_but_ownerless_agents
        parts.append(
            f"{count} agent row(s) carry a scope but no owner — a half-applied store (one column of the "
            f"governed pair was stamped without the other). {_id_sample(preconditions.ownerless_scoped)}"
        )
    if not parts:
        return None
    parts.extend(_message_problem_parts(preconditions, counts))
    parts.append(
        f"(The store holds {counts.unscoped_agents} agent row(s) with no scope in total.) Adjudicate "
        "these "
        "rows by hand before migrating ANY governed table; no row was stamped"
    )
    return " ".join(parts)


def _message_problem_parts(
    preconditions: AgentMigrationPreconditions, counts: MigratePreconditionCounts
) -> list[str]:
    """Every MEASURED, NON-ZERO message problem, in check order (amendment 32 §2.1)."""
    parts: list[str] = []
    if counts.dangling_sender_messages:
        dangling = preconditions.dangling_senders
        shown = [
            f"{sanitise_line(record_text(message_id))} (sender {sanitise_line(record_text(sender))})"
            for message_id, sender in dangling[:_REFUSAL_ID_SAMPLE_SIZE]
        ]
        parts.append(
            f"{counts.dangling_sender_messages} legacy message(s) name a dangling sender — their `sender` "
            "link resolves to "
            f"no agent row, so no owner can be derived from it. First {len(shown)} of {len(dangling)} "
            f"shown: {', '.join(shown)}."
        )
    for ids, count, fact in (
        (
            preconditions.messages_owned_unscoped,
            counts.owned_but_unscoped_messages,
            "carry an owner but no scope",
        ),
        (
            preconditions.messages_scoped_ownerless,
            counts.scoped_but_ownerless_messages,
            "carry a scope but no owner",
        ),
    ):
        if count:
            parts.append(
                f"{count} message row(s) {fact} — a half-applied store (one column of the governed "
                f"pair was stamped without the other). {_id_sample(ids)}"
            )
    return parts


def _message_leg_refusal(
    preconditions: AgentMigrationPreconditions, counts: MigratePreconditionCounts
) -> str | None:
    """The message leg's row-fact refusal (amendments 23 FK-2, 24 §2 door #2, 25, 26), or ``None``: ONE
    refusal naming EVERY problem present, in :func:`_agent_migration_preconditions`' check order —
    dangling senders, then each message half-pair — each with its true count and a bounded sample (THE
    one :data:`_REFUSAL_ID_SAMPLE_SIZE`, per list). Byte-inert: nothing is stamped, the sound rows
    included (one statement, one verdict). ORDER-class, not store-class: it refuses ``message`` only."""
    parts: list[str] = []
    if preconditions.unscoped_count > 0:
        parts.append(
            f"cannot migrate `message` rows before the `agent` table is migrated "
            f"({counts.unscoped_agents} un-migrated (NONE-scope) agent(s) remain) — a message's "
            "owner_principal is read from sender.owner_principal, NONE for every un-migrated agent (§2.6 "
            "agent-first ORDER); run migrate-governed for `agent` first."
        )
    parts.extend(_message_problem_parts(preconditions, counts))
    order_parts = parts[:1] if preconditions.unscoped_count > 0 else []
    row_parts = parts[len(order_parts) :]
    if not row_parts:
        return order_parts[0].rstrip(".") if order_parts else None
    row_parts.append("Adjudicate these messages by hand before migrating `message`; no row was stamped")
    return " ".join(order_parts + row_parts)


class GovernedStatementError(RuntimeError):
    """A migrate leg's backfill statement that the schema gate cannot read COMPLETELY (am-37 §13.3 item 8).

    The leg statements are function-local literals (§1.9 item 1), so an unreadable one is OUR defect, never
    operator input: it is deliberately OUTSIDE the lore-adm fault handler's tuple and TRACEBACKS (the
    honest-developer gate :func:`_dispatch`'s docstring names). ``ValueError`` stays in that tuple for the
    CLI-input checks it was listed for."""


#: The keywords that END an ``UPDATE`` statement's ``SET`` clause — recognised by :func:`_set_columns` only
#: at bracket depth 0 outside a string (am-37 §13.3 item 1).
_SET_CLAUSE_END_KEYWORDS: frozenset[str] = frozenset({"WHERE", "RETURN", "TIMEOUT", "PARALLEL"})

#: The keyword that OPENS the clause, under the same depth-0 / outside-a-string rule.
_SET_CLAUSE_KEYWORD = "SET"

#: The opening → closing bracket pairs the scanner tracks as ONE depth (a call's arguments, an array, an
#: object literal — a comma inside any of them never splits an item).
_SET_CLAUSE_BRACKETS: dict[str, str] = {"(": ")", "[": "]", "{": "}"}

#: The string delimiters (SurrealQL ``'…'`` / ``"…"``; a backslash escapes the next character inside one).
_SET_CLAUSE_QUOTES: frozenset[str] = frozenset({"'", '"'})

#: One ``SET`` item: ``<column> <op>= <value>`` — ``=``, ``+=``, ``-=`` or ``+?=``, the value non-empty. A
#: column must be a bare identifier; any other target (a nested path, a quoted name) is not one this gate
#: can check against ``INFO FOR TABLE``'s field names, so it RAISES rather than guess.
_SET_ITEM = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\+\?|\+|-)?=(?!=)\s*\S", re.DOTALL)


def _keyword_at(statement: str, index: int) -> str | None:
    """The clause keyword starting at ``index`` when it stands as a whole word — preceded by whitespace (or
    the start of the text) and followed by whitespace (or the end) — compared case-insensitively; else
    ``None``. :class:`_SetClauseScanner` asks only at depth 0 outside a string."""
    if index > 0 and not statement[index - 1].isspace():
        return None
    for keyword in (_SET_CLAUSE_KEYWORD, *_SET_CLAUSE_END_KEYWORDS):
        after = index + len(keyword)
        if statement[index:after].upper() == keyword and (
            after == len(statement) or statement[after].isspace()
        ):
            return keyword
    return None


class _SetClauseScanner:
    """THE one scanner over an ``UPDATE`` statement (am-37 §13.3 item 1): a single depth- AND quote-aware
    pass. Bracket depth (``()``/``[]``/``{}``, one stack, so a mismatched closer is caught) and string state
    (``'…'``/``"…"``, a backslash escaping the next character) are tracked TOGETHER; the top-level ``SET``
    opens the clause; ``WHERE`` / ``RETURN`` / ``TIMEOUT`` / ``PARALLEL`` end it, and a comma splits it,
    ONLY at depth 0 outside a string. No regex split beside the character loop — two grammars for one
    clause is how a narrowed parse got in."""

    def __init__(self, statement: str) -> None:
        self._statement = statement
        self._closers: list[str] = []
        self._quote: str | None = None
        self._escaped = False

    def _nested(self, index: int) -> bool:
        """Advance the string/bracket state over ``statement[index]``; ``True`` when that character is not a
        top-level one (inside a string or brackets, or itself a quote/bracket)."""
        character = self._statement[index]
        if self._quote is not None:
            if self._escaped:
                self._escaped = False
            elif character == "\\":
                self._escaped = True
            elif character == self._quote:
                self._quote = None
            return True
        if character in _SET_CLAUSE_QUOTES:
            self._quote = character
            return True
        if character in _SET_CLAUSE_BRACKETS:
            self._closers.append(_SET_CLAUSE_BRACKETS[character])
            return True
        if character in _SET_CLAUSE_BRACKETS.values():
            if not self._closers or self._closers.pop() != character:
                raise GovernedStatementError(
                    f"an unbalanced {character!r} at offset {index} in {self._statement!r}"
                )
            return True
        return bool(self._closers)

    def items(self) -> list[str]:
        """The ``SET`` clause's raw items, split at top-level commas. Raises
        :class:`GovernedStatementError` when the statement cannot be read completely."""
        statement = self._statement
        in_clause = False
        clause_end = len(statement)
        item_start = 0
        items: list[str] = []
        index = 0
        while index < len(statement):
            if self._nested(index):
                index += 1
                continue
            keyword = _keyword_at(statement, index)
            if keyword == _SET_CLAUSE_KEYWORD and not in_clause:
                in_clause = True
                index += len(keyword)
                item_start = index
                continue
            if in_clause and keyword in _SET_CLAUSE_END_KEYWORDS:
                clause_end = index
                break
            if in_clause and statement[index] == ",":
                items.append(statement[item_start:index])
                item_start = index + 1
            index += 1
        if self._quote is not None:
            raise GovernedStatementError(f"an unterminated {self._quote} string in {statement!r}")
        if self._closers:
            raise GovernedStatementError(f"{len(self._closers)} unclosed bracket(s) in {statement!r}")
        if not in_clause:
            raise GovernedStatementError(f"not an `UPDATE … SET` statement: {statement!r}")
        return [*items, statement[item_start:clause_end]]


def _set_columns(statement: str) -> tuple[str, ...]:
    """The columns an ``UPDATE <table> SET <col> = <expr>, …`` statement assigns, in statement order —
    DERIVED from the statement text a leg executes (am-37 §13 D / §13.1 item 5: never a parallel column map),
    read by THE one :class:`_SetClauseScanner`.

    COMPLETE OR RAISE, never a subset (am-37 §13.3 item 1).

    Raises:
        GovernedStatementError: no top-level ``SET``; an unbalanced or mismatched bracket; an unterminated
            string; or an item that is not ``<column> <op>= <value>`` (an empty one included). A statement
            this gate cannot read completely is a programming defect, never a silently narrower requirement.
    """
    columns: list[str] = []
    for item in _SetClauseScanner(statement).items():
        match = _SET_ITEM.match(item)
        if match is None:
            raise GovernedStatementError(
                f"a SET item that is not `<column> = <value>`: {item!r} in {statement!r}"
            )
        columns.append(match.group(1))
    return tuple(columns)


def _schema_predates_refusal(table: str, statement: str, defined_fields: frozenset[str]) -> str | None:
    """The pre-boot schema teaching precondition (am-37 §13 D): the refusal reason when the columns
    ``statement``'s ``SET`` assigns are not all DEFINED on ``table`` (``defined_fields`` — the ONE
    ``INFO FOR TABLE`` read in :func:`_agent_migration_preconditions`), else ``None``.

    Derived from the SCHEMA, never from the write's outcome: on a SCHEMAFULL table an ``UPDATE`` assigning
    an undefined field is SILENT over zero rows and raises only over ≥ 1 (store-ref), so a store with no
    legacy rows would "succeed" and the next legacy row would fail later, out of context. Each missing
    column is quoted in its OWN backtick span (§13.1 item 3 — each is an identifier)."""
    missing = [column for column in _set_columns(statement) if column not in defined_fields]
    if not missing:
        return None
    columns = ", ".join(f"`{column}`" for column in missing)
    return (
        f"the `{table}` table has no {columns} column(s) — this store's schema predates the governed "
        "columns; boot the new image once (its DDL defines them), then re-run migrate-governed"
    )


def _rows_stamped(update_result: Any, *, noun: str) -> int:
    """The number of rows a backfill ``UPDATE`` actually stamped — its returned row list (amendment 24 §2
    D2: a served ``backfilled`` is MEASURED, never the pre-count). An ``UPDATE`` returns the list of rows it
    changed; anything else — a non-list, or a non-dict member that ``len()`` would have counted as a
    stamped row — is a store fault, raised as :class:`SurrealStoreError` through the ONE fail-closed
    row-list policy :func:`loremaster.governed.rows_of` (am-37 §13 B F-6: the class the CLI launders, never
    a ``TypeError``)."""
    from loremaster.governed import rows_of

    return len(rows_of(update_result, noun=noun, landed=True))


async def _migrate_agent_owner(
    store: StoreHandle,
    keep_store: KeepStore,
    principal_store: PrincipalStore,
    *,
    table_defined: bool,
    defined_fields: frozenset[str],
) -> MigrateGovernedResult:
    """Backfill every NONE-scope ``agent`` row's governed triple in ONE scope-keyed statement
    (packet 63c-i-a, ruling §6 / §2.2 grandfather; the leg is named for its pkt-63b origin).

    OWNED-BY-THE-OPERATOR: the pre-cutover local fleet IS the operator's principal (packet 62 Fork
    2 — no sentinel), so a legacy agent is stamped ``owner_principal`` = the ONE operator principal
    resolved by the shared :func:`resolve_operator_principal` (ambiguity is a REFUSAL, never a
    guess), ``owner_agent`` = its OWN id (SF-63-2), and ``scope`` = the canonical PROJECT keep's
    scope (the same ``get_or_create_keyed(PROJECT_KEEP_KEY, …)`` the memory/message legs use).
    ``scope IS NONE`` is THE unmigrated predicate ∀ governed tables, so an already-governed row
    (owned AND scoped) is never touched and a re-run backfills 0.

    §2.1's precondition (an owned-but-unscoped or ownerless-but-scoped agent) is a STORE fact, checked
    ONCE at the verb by :func:`migrate_governed` before this leg runs (amendment 19 D-1). The UPDATE is
    also SELF-GUARDING (amendment 19 F-3): ``WHERE scope IS NONE AND owner_principal IS NONE``, so a row
    that became owned-but-unscoped between that read and this write is never re-owned to the operator.
    NOT member-reachable (admin-CLI-only), so the write attributes at the F5 seam via
    the NAMED ``governed_exempt("migrate-governed")`` frame whose golden IS the executed statement;
    all store access is driver-routed (R4). The owner link is set store-side via ``type::record``
    (a bare id string does not coerce to a ``record<principal>``, store-ref §2).

    ORDERING BOUND (am-37 §13.2): this leg's pre-boot schema gate (:func:`_schema_predates_refusal`) is its
    FIRST action — it runs before any leg read or write (operator resolution, keep mint, counts, backfill).
    A verb-level refusal (:func:`_verb_level_refusal`) may precede this gate; each such refusal is true
    independently of the schema, and this gate runs before any leg read or write.
    """
    from lorerunes.pdp import keep_scope

    from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult, governed_exempt

    # §1.9 item 1: the backfill statement is a FUNCTION-LOCAL literal passed to BOTH the statement-scoped
    # exemption and the execution — built FIRST so the pre-boot schema gate (am-37 §13 D) derives the
    # columns it needs from THIS text, before any read or write.
    backfill_statement = (
        f"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner), "
        "owner_agent = id, scope = $scope WHERE scope IS NONE AND owner_principal IS NONE"
    )
    schema_refusal = _schema_predates_refusal(AGENT_TABLE, backfill_statement, defined_fields)
    if schema_refusal is not None:
        return _refused(AGENT_TABLE, schema_refusal, table_defined=table_defined)

    operator = await resolve_operator_principal(principal_store)
    if operator is None:
        return _refused(
            AGENT_TABLE,
            await _operator_unresolved(principal_store, purpose="to own the fleet's agents"),
            table_defined=table_defined,
        )

    unmigrated = await _scope_count(store, AGENT_TABLE, none=True)
    already = await _scope_count(store, AGENT_TABLE, none=False)
    if unmigrated == 0:
        return MigrateGovernedResult(
            table=AGENT_TABLE,
            scanned=unmigrated + already,
            backfilled=0,
            already_migrated=already,
            refused=False,
            table_defined=table_defined,
            messages_left_unmigrated=None,
        )
    project_keep = await keep_store.get_or_create_keyed(
        key=PROJECT_KEEP_KEY, type="project", keeper_email=operator.email, name="lore"
    )
    project_scope = keep_scope(record_key(project_keep.id))
    operator_id = record_key(operator.id)
    # ONE statement, three columns, scope-keyed (ruling §6) — built at the top of this leg (above).
    with governed_exempt("migrate-governed", statement=backfill_statement):
        stamped = await run_query(
            acquire=store.acquire,
            drop=store.drop,
            url=store.url,
            noun="governed agent backfill",
            label="governed.agent_backfill.rejected",
            statement=backfill_statement,
            params={"owner": operator_id, "scope": project_scope},
            logger=logger,
        )
    return MigrateGovernedResult(
        table=AGENT_TABLE,
        scanned=unmigrated + already,
        backfilled=_rows_stamped(stamped, noun="governed agent backfill"),
        already_migrated=already,
        refused=False,
        table_defined=table_defined,
        messages_left_unmigrated=None,
    )


async def _migrate_message_owner(  # noqa: PLR0913 - the verb's ONE derived answer rides beside the facts
    store: StoreHandle,
    keep_store: KeepStore,
    principal_store: PrincipalStore,
    preconditions: AgentMigrationPreconditions,
    counts: MigratePreconditionCounts,
    *,
    table_defined: bool,
) -> MigrateGovernedResult:
    """Backfill every legacy (NONE-scope, NONE-owner) ``message`` row's owner from its SENDER + scope to
    the project keep (§4.C / §2.6). OWNED-BY-LINK: ``owner_agent = sender``, ``owner_principal =
    sender.owner_principal``, ``scope = keep:<project>``.

    Every guard DECIDES from ``preconditions`` — THE shared :func:`_agent_migration_preconditions`
    answer :func:`migrate_governed` read (routing is not sharing: no private query here), in order:

    1. §2.6 agent-first ORDER, fail-closed: a message's owner is read from ``sender.owner_principal``,
       so this REFUSES while ANY agent is un-migrated (``scope IS NONE`` — THE unmigrated predicate,
       count > 0, never only count == 1).
    2. The message table's own row facts (amendments 23 FK-2, 24 door #2, 25, 26): dangling senders and
       both message half-pairs, in ONE refusal naming every problem present, in the check order.
    3. An unresolvable operator (the project keep's keeper) — a REFUSAL, never a guess (§2.1).

    Every refusal is byte-inert and measured nothing of the target table (``None`` receipts). Otherwise
    it mints/gets the canonical project keep (idempotent CAS, SF-63-4) and runs ONE self-guarding UPDATE
    — ``WHERE scope IS NONE AND owner_principal IS NONE AND sender.owner_principal IS NOT NONE AND
    sender.scope IS NOT NONE`` (amendment 21 CD-1: scope-keyed, and never re-stamps a row that is half of a
    governed pair even when the refusal in front of it cannot fire; the SENDER-soundness clause never
    stamps a message whose sender has no owner or no scope). The counts are SCOPE-keyed; ``backfilled`` is
    the rows the UPDATE actually stamped (amendment 24 D2). The rows still un-migrated AFTER the UPDATE —
    commonly those the sender-soundness clause SKIPPED, plus any row inserted during the run — are then
    measured by ONE separate count read into ``messages_left_unmigrated`` (am-37 §6 F-10 / §13 C F-4),
    which the CLI renders as a sentence iff it is > 0 — a skipped row is reported, never a silent fate.
    Idempotent. NOT member-reachable, so the write attributes at the F5 seam via the NAMED
    ``governed_exempt("migrate-governed")`` frame; store access is driver-routed (R4).

    ORDERING BOUND (am-37 §13.2): this leg's pre-boot schema gate (:func:`_schema_predates_refusal`) is its
    FIRST action — it runs before any leg read or write (operator resolution, keep mint, counts, backfill).
    A verb-level refusal (:func:`_verb_level_refusal`) may precede this gate; each such refusal is true
    independently of the schema, and this gate runs before any leg read or write.
    """
    from lorerunes.pdp import keep_scope

    from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult, governed_exempt, group_all_count

    # §1.9 item 1: the backfill statement is a FUNCTION-LOCAL literal passed to BOTH the statement-scoped
    # exemption and the execution — built FIRST so the pre-boot schema gate (am-37 §13 D) derives the
    # columns it needs from THIS text, before any read or write.
    backfill_statement = (
        f"UPDATE {MESSAGE_TABLE} SET owner_agent = sender, "
        "owner_principal = sender.owner_principal, scope = $scope "
        "WHERE scope IS NONE AND owner_principal IS NONE "
        "AND sender.owner_principal IS NOT NONE AND sender.scope IS NOT NONE"
    )
    schema_refusal = _schema_predates_refusal(MESSAGE_TABLE, backfill_statement, preconditions.defined_fields)
    if schema_refusal is not None:
        return _refused(MESSAGE_TABLE, schema_refusal, table_defined=table_defined)
    row_refusal = _message_leg_refusal(preconditions, counts)
    if row_refusal is not None:
        return _refused(MESSAGE_TABLE, row_refusal, table_defined=table_defined)
    operator = await resolve_operator_principal(principal_store)
    if operator is None:
        return _refused(
            MESSAGE_TABLE,
            await _operator_unresolved(principal_store, purpose="to keep the project keep"),
            table_defined=table_defined,
        )

    project_keep = await keep_store.get_or_create_keyed(
        key=PROJECT_KEEP_KEY, type="project", keeper_email=operator.email, name="lore"
    )
    project_scope = keep_scope(record_key(project_keep.id))

    unmigrated = await _scope_count(store, MESSAGE_TABLE, none=True)
    already = await _scope_count(store, MESSAGE_TABLE, none=False)
    if unmigrated == 0:
        # No legacy row at all, so none can have been left behind: the unsound set is a subset of the
        # ``scope IS NONE`` rows just MEASURED as 0 (derived from that read, never assumed).
        return MigrateGovernedResult(
            table=MESSAGE_TABLE,
            scanned=unmigrated + already,
            backfilled=0,
            already_migrated=already,
            refused=False,
            table_defined=table_defined,
            messages_left_unmigrated=0,
        )
    with governed_exempt("migrate-governed", statement=backfill_statement):
        stamped = await run_query(
            acquire=store.acquire,
            drop=store.drop,
            url=store.url,
            noun="governed message-owner backfill",
            label="governed.message_backfill.rejected",
            statement=backfill_statement,
            params={"scope": project_scope},
            logger=logger,
        )
    # amendment 37 §6 F-10 (the input-fate law) + §13 F-4: the rows the self-guarding UPDATE left un-migrated
    # are neither stamped nor refused — so they are MEASURED here, by ONE read, and reported, never left as a
    # silent fate a re-run would repeat forever. The read counts EVERY message row still unscoped and
    # ownerless after the backfill: commonly a row whose SENDER is unsound (no owner or no scope), but a row
    # inserted during the run is counted too — it is not a sender-skipped count.
    backfilled = _rows_stamped(stamped, noun="governed message-owner backfill")
    # am-37 §13 B F-5: the backfill above is COMMITTED; a failure of this read must name that landed write
    # (a raw rejection would tell the operator only that a read failed). A transport fault / exhausted
    # contention passes through untouched; lore-adm prints the typed cause (§13 A).
    with wrap_store_rejection(
        PrincipalStoreError,
        f"the backfill landed ({backfilled} message row(s) stamped) but the leftover count read failed",
    ):
        leftover = await run_query(
            acquire=store.acquire,
            drop=store.drop,
            url=store.url,
            noun="governed message-owner leftover count",
            label="governed.message_leftover.rejected",
            statement=(
                f"SELECT count() FROM {MESSAGE_TABLE} "
                "WHERE scope IS NONE AND owner_principal IS NONE GROUP ALL"
            ),
            params={},
            logger=logger,
        )
        messages_left_unmigrated = group_all_count(leftover, noun="governed message-owner leftover count")
    return MigrateGovernedResult(
        table=MESSAGE_TABLE,
        scanned=unmigrated + already,
        backfilled=backfilled,
        already_migrated=already,
        refused=False,
        table_defined=table_defined,
        messages_left_unmigrated=messages_left_unmigrated,
    )


@dataclass(frozen=True)
class _LegCall:
    """The verb's measured inputs, handed to whichever migrate leg :data:`_MIGRATE_LEGS` dispatches — one
    shape for every leg, so the leg set is ONE mapping rather than a branch per table."""

    store: StoreHandle
    keep_store: KeepStore
    principal_store: PrincipalStore
    preconditions: AgentMigrationPreconditions
    counts: MigratePreconditionCounts
    table_defined: bool


#: THE migrate-leg dispatch: ``table -> the leg that backfills it``. :func:`_migrate_governed_resolved` runs a
#: table's leg through THIS mapping and answers any other valid table "not yet migrated", so its keys ARE the
#: tables the verb actually migrates — not a list kept beside the dispatch.
_MIGRATE_LEGS: dict[str, Callable[[_LegCall], Awaitable[MigrateGovernedResult]]] = {
    MEMORY_TABLE: lambda call: _migrate_memory_scope(
        call.store,
        call.keep_store,
        call.principal_store,
        table_defined=call.table_defined,
        defined_fields=call.preconditions.defined_fields,
    ),
    AGENT_TABLE: lambda call: _migrate_agent_owner(
        call.store,
        call.keep_store,
        call.principal_store,
        table_defined=call.table_defined,
        defined_fields=call.preconditions.defined_fields,
    ),
    MESSAGE_TABLE: lambda call: _migrate_message_owner(
        call.store,
        call.keep_store,
        call.principal_store,
        call.preconditions,
        call.counts,
        table_defined=call.table_defined,
    ),
}

#: The tables ``migrate-governed`` has a backfill LEG for — DERIVED from the dispatch's own keys (the lead's
#: F-5 ruling: no hand list). The not-yet-migrated refusal's "today:" list (:func:`_not_supported`, am-37
#: §13.3 item 9 / #31) and ``report-unmigrated``'s remedy (item 6: a remedy names ``migrate-governed`` only
#: for a table the verb would actually run) read it.
_MIGRATING_TABLES: tuple[str, ...] = tuple(_MIGRATE_LEGS)


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
    # route to KeepStore via :data:`_KEEP_VERB_HANDLERS`; a KeepStoreError is laundered by
    # :func:`_dispatch`'s ONE lore-adm handler (am-37 §11).
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
        "--table", required=True, help=f"the governed table to migrate ({_TABLE_HELP_DOMAIN})"
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
        "--table", required=True, help=f"the governed table to inspect ({_report_table_help_domain()})"
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
    option AND the ``--type``, laundered by :func:`_dispatch` to a ``lore-adm:``
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
    :func:`_dispatch` to a stderr line + exit 1. Silent on success."""
    await keep_store.remove_household_member(keep_id=args.keep, member_email=args.member)
    return 0


async def _cmd_set_rank(args: argparse.Namespace, keep_store: KeepStore) -> int:
    """The ``set-rank`` verb — delegates to :meth:`KeepStore.set_rank` (TRIVIAL today:
    the only legal rank is ``contributor``; a wrong rank is a loud store error laundered
    by :func:`_dispatch`). Silent on success."""
    await keep_store.set_rank(keep_id=args.keep, member_email=args.member, rank=args.rank)
    return 0


async def _cmd_set_keeper(args: argparse.Namespace, keep_store: KeepStore) -> int:
    """The ``set-keeper`` verb — delegates to :meth:`KeepStore.set_keeper` (admin
    set_owner, §FR-4/D1: UPDATE the keep's ``keeper`` field to a new principal so a
    departing keeper's keep can be reassigned before deleting them). A ghost ``--keep``
    (:class:`~loremaster.keeps.KeepNotFoundError`) or a ghost ``--new-keeper`` email
    (:class:`~loremaster.keeps.KeepStoreError`) is laundered by :func:`_dispatch` to
    a ``lore-adm:`` stderr line + exit 1. Silent on success."""
    await keep_store.set_keeper(keep_id=args.keep, new_keeper_email=args.new_keeper)
    return 0


async def _cmd_delete_keep(args: argparse.Namespace, keep_store: KeepStore) -> int:
    """The ``delete-keep`` verb — delegates to :meth:`KeepStore.delete_keep` (admin
    delete, §FR-4/D2: remove the keep node so a sole-member/dm keep's keeper can then be
    deleted; its ``member_of`` edges auto-cascade on the node delete — store law §4,
    probed). A ghost ``--keep`` (:class:`~loremaster.keeps.KeepNotFoundError`) is
    laundered by :func:`_dispatch` to a stderr line + exit 1. Silent on success."""
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
    (loud on failure); a transport fault surfaces the same way.

    This is the ONE lore-adm fault handler (packet 63c amendment 37 §11): every verb —
    the two named branches, every keep verb, every principal/key verb — routes through the
    single ``try`` below, and any fault in its allowlist becomes ``f"{_CLI_PROG}: {error}"``
    on stderr + exit ``1``. The verb dispatchers beneath it keep only their ``try/finally``
    resource closes; none of them catches. The handler's only return is ``1`` — a fault can
    never be swallowed into a success. Anything OUTSIDE the tuple (a ``TypeError``, an
    ``OSError``) is a programming defect and is left to traceback.
    """
    # Lazy imports: ``loremaster.principal_keys`` and ``loremaster.keeps`` both import THIS
    # module (``Principal`` / ``PrincipalStore``), so a top-level import here is a cycle.
    # PLC0415 is a house-ignored idiom. They sit at the top so the handler's tuple can name
    # every lore-adm fault class (am-37 §11 item 3).
    from loremaster.keeps import KeepStoreError
    from loremaster.principal_keys import PrincipalKeyStoreError, build_principal_key_store

    # ``_require_config`` runs FIRST (before any branch, and OUTSIDE the handler), so a
    # missing ``--config`` is a loud ``SystemExit`` for EVERY verb, keep verbs included.
    config = load_surreal_only_config(_require_config(args))
    try:
        if args.command == "migrate-governed":
            return await _dispatch_migrate_governed(args, config)
        if args.command == "report-unmigrated":
            return await _dispatch_report_unmigrated(args, config)
        if args.command in _KEEP_VERB_HANDLERS:
            return await _dispatch_keep(args, config)
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
        finally:
            await keep_store.close()
            await key_store.close()
            await principal_store.close()
    except (
        PrincipalStoreError,
        PrincipalKeyStoreError,
        KeepStoreError,
        SurrealStoreError,
        ValueError,
    ) as error:
        print(_fault_line(error), file=sys.stderr)
        return 1


#: The cause-line prefix the lore-adm fault handler renders per ``__cause__`` link (am-37 §13 A ii).
_CAUSE_LINE_PREFIX = "  ← caused by: "
#: The prefix of each ``__notes__`` line :func:`_fault_line` renders (am-37 §13.5 item 1).
_NOTE_LINE_PREFIX = " ↳ "

#: The ``extra`` keys of the store seam's rejection record the CLI stderr handler renders (am-37 §13 A i) —
#: the seam's ``url`` extra is deliberately NOT rendered (it is already in the error's own message).
_CLI_LOG_EXTRA_KEYS: tuple[str, ...] = ("error_class", "engine_error")


def _fault_line(error: BaseException) -> str:
    """The lore-adm fault text: ``lore-adm: <error>`` then one cause line per ``__cause__`` link (am-37 §13
    A ii) — MESSAGES only (never a traceback), consecutive duplicates collapsed, an empty message rendered
    as its class name so a link never prints blank. The typed cause is what names the reason, so a wrap
    context never has to over-claim it (F-13).

    Every message — the error's and each cause's — renders through THE shared scrub
    :func:`loremaster.logging_setup.scrub_text`, the same function :class:`RedactingFilter` calls (am-37 §13.3
    item 2 ii): one redaction for every sink, never a second regex. The walk follows ``__cause__`` ONLY (the
    seams chain explicitly with ``from error``; the implicit ``__context__`` link would duplicate or mislead)
    and keeps a ``seen`` set of exception ids, so a cyclic chain terminates with each link rendered once
    (am-37 §13.3 item 3, #527 — the stdlib ``traceback`` shape)."""
    lines = [f"{_CLI_PROG}: {scrub_text(str(error))}"]
    previous = lines[0].removeprefix(f"{_CLI_PROG}: ")
    # PEP 678 notes (am-37 §13.5 item 1, e.g. ``mint``'s revoke repair): after the message, before causes.
    lines.extend(f"{_NOTE_LINE_PREFIX}{scrub_text(note)}" for note in getattr(error, "__notes__", ()))
    seen = {id(error)}
    cause = error.__cause__
    while cause is not None and id(cause) not in seen:
        seen.add(id(cause))
        text = scrub_text(str(cause) or type(cause).__name__)
        if text != previous:
            lines.append(f"{_CAUSE_LINE_PREFIX}{text}")
        previous = text
        cause = cause.__cause__
    return "\n".join(lines)


class _CliLogFormatter(logging.Formatter):
    """``%(message)s`` plus the store seam's ``error_class`` / ``engine_error`` extras when a record
    carries them (am-37 §13 A i): in lore-adm, "the server log" the seam's hint points at IS stderr, so the
    record must show the engine text the raised message deliberately withholds (#31 hygiene protects MCP
    consumers; this is the operator's own terminal)."""

    def format(self, record: logging.LogRecord) -> str:
        """Render the message, then ``key=value`` for each present seam extra."""
        rendered = super().format(record)
        extras = [
            f"{key}={getattr(record, key)}"
            for key in _CLI_LOG_EXTRA_KEYS
            if getattr(record, key, None) is not None
        ]
        return f"{rendered} [{'; '.join(extras)}]" if extras else rendered


class _CliStderrHandler(logging.StreamHandler):  # type: ignore[type-arg]
    """The lore-adm stderr log handler (am-37 §13 A i), a marker subclass so :func:`_cli_logging` can find
    and remove any instance a previous ``main()`` call left behind (idempotent across calls)."""


@contextlib.contextmanager
def _cli_logging() -> Iterator[None]:
    """Install ONE WARNING-level, :class:`~loremaster.logging_setup.RedactingFilter`-filtered stderr handler
    on the ``loremaster`` logger for the duration of a ``main()`` call, bound to the CURRENT ``sys.stderr``,
    and remove it on exit. Any ``_CliStderrHandler``
    already on the logger (a call that never reached its ``finally``) is removed first, so repeated
    ``main()`` calls never duplicate a record or write to a dead stream (the lifecycle pin)."""
    package_logger = logging.getLogger(_CLI_LOGGER_NAME)
    for stale in [h for h in package_logger.handlers if isinstance(h, _CliStderrHandler)]:
        package_logger.removeHandler(stale)
    handler = _CliStderrHandler(sys.stderr)
    handler.setLevel(logging.WARNING)
    handler.setFormatter(_CliLogFormatter("%(message)s"))
    # am-37 §13.3 item 2 (i): THE redaction seam, exactly as ``configure_logging`` attaches it — the filter
    # scrubs ``msg``, ``args`` and EVERY extra (``engine_error`` included) through ``scrub_text``.
    handler.addFilter(RedactingFilter())
    package_logger.addHandler(handler)
    try:
        yield
    finally:
        package_logger.removeHandler(handler)


async def _dispatch_migrate_governed(args: argparse.Namespace, config: LoreConfig) -> int:
    """Build the stores + a driver ``StoreHandle`` over the unified store and run
    :func:`migrate_governed` (packet 63a). The governed tables (``memory`` at 63a) live in the SAME
    database the principal/keep stores connect to, so a handle over the principal store's own
    driver reaches them — and every store access inside the verb routes through it (R4). Receipts to
    stdout; a REFUSAL is a stderr line + exit 1 (Unix philosophy: loud on failure). A store/domain
    fault propagates to :func:`_dispatch`'s ONE lore-adm handler (am-37 §11), which launders it to
    the same stderr line + exit 1; this frame only closes its stores.
    """
    # am-37 §13 C N-3 / F-15: an invalid ``--table`` is refused BEFORE any store I/O (no store is even
    # built), through THE one validator ``report-unmigrated`` also calls; the refusal is the verb's own
    # zero-I/O "not supported" receipt (``table_defined=None``), rendered like every other refusal.
    if _migrate_table_refusal(args.table) is not None:
        return _render_migrate_refusal(_not_supported(args.table, table_defined=None))
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
            return _render_migrate_refusal(result)
        if result.table_defined is False:
            print(
                f"migrate-governed --table {result.table}: the `{result.table}` table is not defined in this "
                "store — nothing to migrate"
            )
            return 0
        # amendment 37 §8.2 F-a rider + §10.2 (+ §13 C F-4 rename): the receipt line carries
        # ``messages_left_unmigrated`` as a
        # typed count beside its siblings, DERIVED from the result field — so a script that never reads
        # stderr still sees the leftover. ONE convention for every field on the line: rendered ALWAYS,
        # a ``None`` ("not measured for this table") served explicitly as ``None``, never by omission.
        print(
            f"migrate-governed --table {result.table}: scanned={result.scanned} "
            f"backfilled={result.backfilled} already_migrated={result.already_migrated} "
            f"messages_left_unmigrated={result.messages_left_unmigrated}"
        )
        if result.messages_left_unmigrated:
            # amendment 37 §6 F-10 / §13 C F-4: DERIVED from the measured field, iff > 0.
            print(
                f"migrate-governed --table {result.table}: {result.messages_left_unmigrated} message row(s) "
                "remain un-migrated after the backfill — commonly their sender has no owner or scope "
                f"(re-run after `--table {AGENT_TABLE}` for those); a row inserted during the run is "
                "counted here too",
                file=sys.stderr,
            )
        return 0
    finally:
        await keep_store.close()
        await principal_store.close()


def _render_migrate_refusal(result: MigrateGovernedResult) -> int:
    """Render a ``migrate-governed`` refusal receipt: ONE stderr line, exit ``1`` (a refusal wrote nothing).
    The table name is a raw operator argument on the zero-I/O path, so it passes the shared sanitiser."""
    print(
        f"{_CLI_PROG}: migrate-governed --table {sanitise_line(result.table)} REFUSED: {result.reason}",
        file=sys.stderr,
    )
    return 1


async def _dispatch_report_unmigrated(args: argparse.Namespace, config: LoreConfig) -> int:
    """Report a governed table's un-migrated (NONE-scope) row count — the read-only PREVIEW verb
    (packet 63a-ii, §10.7-W: the preview role the struck dry-run paradigm no longer fills). Builds
    a driver ``StoreHandle`` over the unified store (the ``_dispatch_migrate_governed`` idiom) and
    runs :func:`~loremaster.governed.report_unmigrated_governed_rows` (R4: no raw connection). A
    READ — it never writes; the count goes to stdout. A domain/transport failure (incl. a rejected
    SELECT on an absent table) propagates to :func:`_dispatch`'s ONE lore-adm handler (am-37 §11):
    stderr + exit 1, never a traceback. This frame only closes its store.
    """
    from loremaster.governed import governed_tables, report_unmigrated_governed_rows, validate_governed_table

    # am-37 §13 C N-3 / F-15 + §13.4: validated BEFORE any I/O (no store is even built) through THE one
    # validator, over the REPORT domain — the governed set. A refusal is a ``ValueError``: the ONE lore-adm
    # handler renders it to stderr + exit 1.
    validate_governed_table(args.table, domain=governed_tables(), verb=_REPORT_VERB)
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
    finally:
        await principal_store.close()


async def _dispatch_keep(args: argparse.Namespace, config: LoreConfig) -> int:
    """Build + ready the KeepStore, run the selected keep verb, and close both stores.

    The ``principal`` table is readied FIRST (via a ``PrincipalStore``): the
    ``member_of`` relation edge is ENFORCED with ``IN principal``, so its endpoint table
    must exist before :meth:`KeepStore.ensure_ready` applies the keep slice (the wave-1
    ``keep_env`` fixture / the :meth:`KeepStore.ensure_ready` docstring). ``KeepStore``
    composes its own ``PrincipalStore`` for email resolution but does NOT ready it.

    This frame catches NOTHING: it only closes its stores. Every store/domain fault a keep
    verb raises — ``KeepStoreError`` (which subsumes ``KeeperLockoutError`` /
    ``KeepNotFoundError``), a raw ``SurrealStoreError`` (incl. a transient
    ``SurrealConnectionError``), or the per-``type`` ``--name`` ``ValueError`` (project/team
    require a name; a ``dm`` forbids one) — propagates to :func:`_dispatch`'s ONE lore-adm
    handler, which launders it to ``f"{_CLI_PROG}: {error}"`` on stderr + exit 1.

    FR-2 D1 is RE-RULED (packet 63c amendment 37 §11 item 1). D1 once kept the raw
    ``SurrealStoreError`` OUT of this frame's catch so that an engine rejection escaping
    ``KeepStore`` un-wrapped would crash loudly as a missed-wrap BUG signal. Its premise was
    false for READS, and a traceback is never an honest operator surface for a store fault.
    The policy the code HAS (am-37 §13 C F-14): the WRITE boundaries are the PINNED minimum —
    every one sits inside ``wrap_store_rejection`` (the FR-2 / am-37 §12 wrap pins enforce
    it); a verb path MAY wrap its reads too (``PrincipalStore.delete`` and
    ``KeepStore.get_or_create_keyed`` do), and ``ensure_ready`` is un-wrapped by design. D1's
    INTENT survives in the stderr line: an un-wrapped ``SurrealStoreError`` prints its driver
    label + server-log hint (and, since am-37 §13 A, its typed cause and the seam's log record
    on stderr), distinguishable from a ``KeepStoreError`` teaching.
    """
    principal_store = build_principal_store(config)
    keep_store = build_keep_store(config)
    try:
        # The ``member_of`` ENFORCED endpoint (``principal``) FIRST, then keep+member_of.
        await principal_store.ensure_ready()
        await keep_store.ensure_ready()
        handler = _KEEP_VERB_HANDLERS[args.command]
        return await handler(args, keep_store)
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
    with _cli_logging():
        return asyncio.run(_dispatch(args))


if __name__ == "__main__":
    raise SystemExit(main())
