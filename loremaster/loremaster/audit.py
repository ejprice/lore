"""The ``audit`` substrate — lore's durable APPEND-ONLY governance trail (packet 61a-w4).

Introduced by the packet-61a-w4 contract (``test_audit_schema.py`` + ``test_audit_store.py``,
session ``pkt61``, 2026-08-23), per the design sidecar
(``docs/design/2026-08-22-packet61-pdp-audit-rulings.md`` §Fork G / §Fork I) and store law
(``docs/reference/surrealdb-31-capabilities.md`` §1.1/§2/§3). It builds ONLY the store
SUBSTRATE (61a); ``requires_audit`` and the PDP admin ``audit`` carve-out are 61b.

:class:`AuditStore` is the narrow, append-only write surface over the ``audit`` node table
(:func:`~loremaster.store.surreal_schema.generate_audit_ddl`): every governed ADMIN mutation
records the resolved ``(principal, agent)`` actor stamp, the mutating ``action``, the
affected ``target_table``/``target_row``, and the ``old_value``/``new_value`` before/after
row states. It rides the SAME store machinery the record-substrate stores use — one
lazily-opened, signed-in WS connection, self-healed on a mid-life transport failure, reusing
the shared transaction / error-classification seams in :mod:`loremaster.store._txn`
(``bootstrap_session`` / ``execute_transaction`` / ``retry_on_conflict`` /
``wrap_store_rejection``). It introduces NO retry / classification / query policy of its own
(#102/#120), and — unlike :class:`~loremaster.keeps.KeepStore` — composes NO
``PrincipalStore``: :meth:`AuditStore.append` takes ALREADY-RESOLVED principal/agent ids.

The public surface (append-only):

    AuditStore(*, url, namespace, database, user, password):
        async ensure_ready() -> None
        async append(*, actor_principal, actor_agent, action, target_table, target_row,
                     old_value=None, new_value=None) -> str          # the created row's id
        append_fragment(*, ...) -> TxnFragment                       # the composable seam
        async close() -> None

    Exceptions: AuditStoreError(RuntimeError).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from pydantic import SecretStr
from surrealdb import AsyncSurreal, RecordID
from ulid import ULID

from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    TxnContentionExhaustedError,
    TxnFragment,
    _SurrealConnection,
    bootstrap_session,
    compose,
    execute_transaction,
    signin_credentials,
    wrap_store_rejection,
)
from loremaster.store.surreal_schema import (
    AGENT_TABLE,
    AUDIT_TABLE,
    PRINCIPAL_TABLE,
    generate_audit_ddl,
)

logger = logging.getLogger(__name__)

# Every ``append`` param the composable fragment binds is namespaced under this prefix, so a
# co-composed governed-mutation fragment (63/64) can never collide with it (the ``TxnFragment``
# contract — ``TxnParamCollisionError``; the ``GRAPH_FRAGMENT_PARAM_PREFIX`` precedent).
_AUDIT_FRAGMENT_PARAM_PREFIX = "audit_"


class AuditStoreError(RuntimeError):
    """Base class for every error :class:`AuditStore` raises (the ``KeepStoreError`` parity)."""


class AuditStore:
    """Durable APPEND-ONLY governance-trail store over a single SurrealDB database.

    Owns the ``audit`` node table (see
    :func:`~loremaster.store.surreal_schema.generate_audit_ddl`) and rides the shared
    :mod:`loremaster.store._txn` transaction / error-classification seams, so every append is
    atomic and every failure surfaces as a typed store error. It clones the
    :class:`~loremaster.keeps.KeepStore` connection-owner idiom but composes NO identity store
    — :meth:`append` takes already-resolved actor ids.

    THE APPEND-ONLY THREAT MODEL (a gate needs a threat model, stated in the instrument —
    design Fork G). Append-only is enforced IN-PROCESS, in TWO layers:

      * **Layer 1 (this wave, 61a-w4):** the NARROW class SURFACE — the only public members,
        across the FULL MRO, are ``append`` / ``append_fragment`` / ``ensure_ready`` /
        ``close``. There is NO ``update`` / ``delete`` / ``purge`` / ``set_*`` verb, own OR
        inherited, so an in-process caller holding an :class:`AuditStore` cannot rewrite or
        erase the trail: you cannot CALL what is not there.
      * **Layer 2 (61b, the PDP):** the policy-decision point's admin short-circuit carves the
        ``audit`` table OUT of the admin DELETE/SET_* powers
        (``authorize(admin, DELETE, audit) = DENY``), so no governed admin verb can reach it
        either.

    ⚠ ACCEPTED BOUND — this is NOT a boundary against DIRECT-STORE / ROOT access. lore connects
    to SurrealDB as ROOT (Version A), and native SurrealDB PERMISSIONS are inert under a root
    session — so a root operator (or any code holding the store credentials) can still delete
    or rewrite ``audit`` rows by talking to the engine directly, BENEATH this in-process
    surface. A future auditor must NOT call that a hole: it is the deliberate Version-A trade.
    RE-OPEN TRIGGER (**Version B**): per-principal record authentication, under which native
    SurrealDB PERMISSIONS could enforce append-only IN-ENGINE and this accepted bound closes.

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
        # Guards the connect-time check-then-set so N concurrent first-callers never each open
        # their own underlying SDK connection (mirrors ``KeepStore``).
        self._connect_lock = asyncio.Lock()

    # -- connection lifecycle ----------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking cloned from
        :meth:`~loremaster.keeps.KeepStore._ensure_connection`: the fast path never touches the
        lock, the session bootstrap is the ONE shared
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
                "audit.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect and apply the audit schema slice — idempotent, safe to re-run.

        Applies :func:`~loremaster.store.surreal_schema.generate_audit_ddl` (the ``audit``
        node table + its field set) inside ONE ``BEGIN … COMMIT`` via
        :func:`~loremaster.store._txn.execute_transaction`, which verifies EVERY statement's
        status (the SDK's plain ``query()`` inspects only the first — store reference §3). The
        table is ``IF NOT EXISTS`` and every FIELD is ``DEFINE FIELD OVERWRITE`` (finding
        #107). ⚠ Neither ``principal`` NOR ``agent`` need pre-exist: a ``record<t>`` field-def
        needs no target table at DDL time (the ``principal_keys.py`` precedent, proven live by
        ``TestTheFullDdlWithAuditFoldedApplies``).

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: A DDL statement was rejected by the engine.
        """
        await self._ensure_connection()
        ddl = generate_audit_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("audit.schema.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any)."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal).

        A compare-and-swap (cloned from :class:`~loremaster.keeps.KeepStore`):
        ``self._connection`` is cleared only when ``connection`` is STILL the cached handle, so
        a late caller holding a stale reference can never wipe out a freshly-reconnected one.
        The handed connection is always closed.
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
            logger.debug("audit.close.already_closed")

    # -- the append-only write surface -------------------------------------

    def append_fragment(
        self,
        *,
        actor_principal: str,
        actor_agent: str,
        actor_email: str,
        actor_agent_name: str,
        action: str,
        target_table: str,
        target_row: str,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
    ) -> TxnFragment:
        """Build the composable :class:`~loremaster.store._txn.TxnFragment` for ONE append.

        A SINGLE-statement ``CREATE`` into the ``audit`` table carrying NO ``BEGIN``/``COMMIT``
        of its own (the ``purge_file_fragment`` precedent), so a caller — 63/64 — can
        :func:`~loremaster.store._txn.compose` it alongside a governed-mutation fragment and
        land ``[governed_mutation, audit_append]`` ATOMICALLY in ONE ``execute_transaction``.
        The record id is a client-minted ``ulid()`` (creation-ordered, sortable — no hot-row
        contention). Actor ids bind through ``type::record`` (record LINKS, never bare strings
        — store reference §2/§4); ``actor_email``/``actor_agent_name`` are written as
        DENORMALIZED string VALUES (Fork G §9 forensics — captured at write time so the human
        identity survives even when the links dangle on a principal-delete). ``old_value``/
        ``new_value`` are written ONLY when provided, so an omitted ``option<object>`` decodes
        to NONE (a from-nothing action has no old, a DELETE no new); ``created_at`` self-stamps
        (OMITTED). Every param is namespaced under :data:`_AUDIT_FRAGMENT_PARAM_PREFIX` so a
        co-composed producer's params never collide.

        Args:
            actor_principal: The resolved principal id (bare — the ``xyz`` of ``principal:xyz``).
            actor_agent: The resolved agent id (bare).
            actor_email: The actor principal's email — the DENORMALIZED human identity captured
                at write time (§9 forensics), stored as a VALUE that outlives a principal-delete.
            actor_agent_name: The actor agent's name — the denormalized agent identity, likewise
                captured as a surviving VALUE.
            action: The mutating action (one of the store-side closed domain — WRITE / DELETE /
                SET_SCOPE / SET_OWNER); an unaudited value is rejected by the engine ASSERT.
            target_table: The governed table the mutation touched.
            target_row: The ``str(RecordID)`` of the affected row.
            old_value: The before-state governed row (``None`` for a from-nothing action).
            new_value: The after-state governed row (``None`` for a DELETE).

        Returns:
            A one-statement :class:`TxnFragment` (its ``params`` carry the minted id under the
            ``audit_id`` key).
        """
        record_id = str(ULID())  # a bare, client-minted ULID (Crockford, colon-free)
        content_fragments = [
            f"actor_principal: type::record('{PRINCIPAL_TABLE}', $audit_ap)",
            f"actor_agent: type::record('{AGENT_TABLE}', $audit_aa)",
            "actor_email: $audit_email",
            "actor_agent_name: $audit_agent_name",
            "action: $audit_action",
            "target_table: $audit_tt",
            "target_row: $audit_tr",
        ]
        params: dict[str, Any] = {
            "audit_id": record_id,
            "audit_ap": actor_principal,
            "audit_aa": actor_agent,
            "audit_email": actor_email,
            "audit_agent_name": actor_agent_name,
            "audit_action": action,
            "audit_tt": target_table,
            "audit_tr": target_row,
        }
        if old_value is not None:
            content_fragments.append("old_value: $audit_old")
            params["audit_old"] = old_value
        if new_value is not None:
            content_fragments.append("new_value: $audit_new")
            params["audit_new"] = new_value
        statement = (
            f"CREATE type::record('{AUDIT_TABLE}', $audit_id) "
            f"CONTENT {{ {', '.join(content_fragments)} }}"
        )
        return TxnFragment(statements=[statement], params=params)

    async def append(
        self,
        *,
        actor_principal: str,
        actor_agent: str,
        actor_email: str,
        actor_agent_name: str,
        action: str,
        target_table: str,
        target_row: str,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
    ) -> str:
        """Append ONE governed-mutation record to the trail; return the created row's id.

        Executes :meth:`append_fragment`'s SINGLE composable statement through
        :func:`~loremaster.store._txn.compose` + the VERIFIED
        :func:`~loremaster.store._txn.execute_transaction` seam (store reference §3 — which
        checks EVERY statement, never the lax ``.query()`` first-statement-only path). The
        write IS the composable fragment (ONE path — ``append`` never hand-rolls a second,
        non-composable CREATE), so it can never drift from what 63/64 compose.

        Born WRAPPED (Fork I, the 9th consumer of finding #400's ONE seam): a raw engine
        ``SurrealStoreError`` — e.g. an unaudited ``action`` refused by the closed-domain
        ASSERT — is WRAPPED LOUD as :class:`AuditStoreError` (consumer law); a transport fault
        / exhausted contention (:class:`SurrealConnectionError` /
        :class:`TxnContentionExhaustedError`, both SUBCLASSing ``SurrealStoreError``) passes
        through UNTOUCHED (store reference §3). The single CREATE is atomic — a rejected append
        leaves NO row.

        Args:
            actor_principal: The resolved principal id (bare).
            actor_agent: The resolved agent id (bare).
            actor_email: The actor principal's email — the DENORMALIZED human identity captured
                at write time (§9 forensics), surviving a later principal-delete as a VALUE.
            actor_agent_name: The actor agent's name — the denormalized agent identity, likewise.
            action: The mutating action (WRITE / DELETE / SET_SCOPE / SET_OWNER).
            target_table: The governed table the mutation touched.
            target_row: The ``str(RecordID)`` of the affected row.
            old_value: The before-state governed row (``None`` for a from-nothing action).
            new_value: The after-state governed row (``None`` for a DELETE).

        Returns:
            The created audit row's ``str(RecordID)`` id (``audit:<ulid>``) — a useful handle.

        Raises:
            AuditStoreError: The store rejected the append (e.g. an unaudited ``action`` or a
                missing/empty required field). The raw engine ``SurrealStoreError`` is WRAPPED
                as this domain error; transport / exhausted-contention faults pass through
                untouched (store reference §3).
        """
        fragment = self.append_fragment(
            actor_principal=actor_principal,
            actor_agent=actor_agent,
            actor_email=actor_email,
            actor_agent_name=actor_agent_name,
            action=action,
            target_table=target_table,
            target_row=target_row,
            old_value=old_value,
            new_value=new_value,
        )
        record_id = str(fragment.params["audit_id"])
        statement_text, merged_params = compose(fragment)
        # A store rejection (e.g. an unaudited ``action`` ASSERT violation) is wrapped LOUD as
        # the domain error (consumer law); a transport fault / exhausted contention passes
        # through untouched (both SUBCLASS SurrealStoreError, store reference §3). Finding #400:
        # routed through the ONE seam, born wrapped (Fork I).
        with wrap_store_rejection(
            AuditStoreError,
            f"could not append {action!r} audit record for "
            f"{target_table}/{target_row}: the store rejected the append",
        ):
            await execute_transaction(
                statement_text,
                merged_params,
                acquire=self._ensure_connection,
                drop=self._drop_connection,
                url=self._url,
            )
        return str(RecordID(AUDIT_TABLE, record_id))
