"""The durable, fleet-visible AGENT REGISTRY (PKT-28 C1 agent-comms — seam S2).

:class:`AgentRegistry` is the identity/heartbeat/status-machine primitive every
``lore_comms`` action resolves an agent row through: idempotent
:meth:`~AgentRegistry.register`, name/session resolution
(:meth:`~AgentRegistry.get_agent`), the one heartbeat/status-machine primitive
(:meth:`~AgentRegistry.touch`), and the fleet-visible listing
(:meth:`~AgentRegistry.fleet`). It rides the SAME store machinery the rest of
the layer uses (:mod:`loremaster.tasks`/:mod:`loremaster.findings`):

* one lazily-opened, signed-in WS connection, self-healed on a mid-life
  transport failure, reusing the shared error-classification seam in
  :mod:`loremaster.store._txn` — a transport fault surfaces as
  :class:`~loremaster.store._txn.SurrealConnectionError`, a domain rejection as
  :class:`~loremaster.store._txn.SurrealStoreError`, never a raw engine string;
* :func:`~loremaster.store._txn.execute_transaction` applies the ``agent``
  schema slice (:func:`~loremaster.store.surreal_schema.generate_agent_ddl`)
  at :meth:`~AgentRegistry.ensure_ready`, verifying EVERY statement's status
  (the SDK's plain ``query()`` inspects only the first).

Binding spec: ``docs/design/2026-07-12-pkt28-c1-semantics.md`` §0-§4, §7-§8.
The public surface below is the contract test's own pinned API
(``REPORT-c1-contract-ledgers.md`` §"Exact public API surface") — this module
implements it, never redefines it:

    Agent:                                  # a value object (pydantic model)
        id: str                             # opaque hex — uuid5(session:name)
        name: str
        session: str
        role: str
        model: str | None
        status: Literal[active|idle|input_required|retired]
        spawned_by: str | None
        task_id: str | None
        checkpoint: dict | None             # C1 ships the column, no C1 surface
        last_note: str | None
        registered_at: datetime             # tz-aware UTC, write-once
        heartbeat_at: datetime              # tz-aware UTC, touched every action

    AgentRegisterResult:
        agent: Agent
        re_registered: bool                 # False on first register

    AgentFleetWindow:
        rows: list[Agent]                   # non-retired, ordered per §6
        retired_count: int
        total_non_retired: int              # honest total BEFORE `limit` truncation

    AgentRegistry(*, url, namespace, database, user, password):
        async ensure_ready() -> None
        async close() -> None
        async register(name, *, session, role, model=None, spawned_by=None,
                        task_id=None) -> AgentRegisterResult
        async get_agent(name, *, session=None) -> Agent
        async touch(name, *, session=None, status=None, note=None) -> Agent
        async fleet(*, session=None, limit) -> AgentFleetWindow
        async roster(*, session=None) -> FleetRoster   # row-unlimited true counts (v4)

    Exceptions: AgentRegistryError(RuntimeError);
                UnknownAgentError(AgentRegistryError);
                AmbiguousAgentError(AgentRegistryError);
                AgentIdentityConflictError(AgentRegistryError);
                RetiredAgentError(AgentRegistryError);
                IllegalAgentStatusError(AgentRegistryError).

``touch`` is this ledger's ONE heartbeat/status-machine primitive (design doc
§8's dispatch algorithm step 4): the 'heartbeat' action calls it with a
caller-supplied ``status``/``note``; every OTHER action's uniform touch calls
it with ``status=None`` — the SAME code path drives the idle -> active
auto-flip and the retired-terminal check either way.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, SecretStr
from surrealdb import AsyncSurreal, RecordID

from loremaster.render import render_attributed
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
from loremaster.store.surreal_schema import AGENT_TABLE, generate_agent_ddl

logger = logging.getLogger(__name__)

# The domain's status vocabulary this contract decides — a ``Literal`` alias so
# :class:`Agent.status` is typed against the closed set the state machine
# enforces, without hardcoding the set a second time (mirrors
# ``loremaster.tasks.TaskStatus``).
AgentStatus = Literal["active", "idle", "input_required", "retired"]

# --- the four statuses, as named constants (never bare literals in logic) ----
STATUS_ACTIVE: AgentStatus = "active"
STATUS_IDLE: AgentStatus = "idle"
STATUS_INPUT_REQUIRED: AgentStatus = "input_required"
STATUS_RETIRED: AgentStatus = "retired"

# The closed status domain — membership is what makes a ``status=`` target a
# legal VALUE at all (a garbage target is refused before the edge check).
# ``'orphaned'`` is deliberately absent: it is DERIVED at render time from
# ``heartbeat_at`` age (design doc §3) and must NEVER be a legal stored value.
AGENT_STATUSES: frozenset[str] = frozenset(
    {STATUS_ACTIVE, STATUS_IDLE, STATUS_INPUT_REQUIRED, STATUS_RETIRED}
)

# The full legal transition matrix (design doc §3): every ``(from, to)`` pair
# NOT in this frozen set is an illegal edge — including every edge out of the
# terminal ``retired`` status and the (illegal) ``input_required -> idle``
# unpark, which C1 deliberately refuses (a parked question stays visible until
# answered or the agent dies; going quiet does not unpark it).
LEGAL_AGENT_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        (STATUS_ACTIVE, STATUS_IDLE),
        (STATUS_ACTIVE, STATUS_INPUT_REQUIRED),
        (STATUS_ACTIVE, STATUS_RETIRED),
        (STATUS_IDLE, STATUS_ACTIVE),
        (STATUS_IDLE, STATUS_INPUT_REQUIRED),
        (STATUS_IDLE, STATUS_RETIRED),
        (STATUS_INPUT_REQUIRED, STATUS_ACTIVE),
        (STATUS_INPUT_REQUIRED, STATUS_RETIRED),
    }
)

# The value DERIVED at render time from heartbeat age — never a legal stored
# status. Named here so the one status-vocabulary error message that teaches
# its derivation (:meth:`AgentRegistry._reject_illegal_status`) never
# hand-types the literal string twice.
_AGENT_STATUS_ORPHANED = "orphaned"

# The load-bearing injection guard (design doc §0/§4): every ``agent.name`` /
# ``agent.session`` is inlined as a literal into C3's live WHERE clauses, so
# the charset is enforced here (a Python-side pre-validation layer) AND by the
# store's own ``ASSERT`` (defense-in-depth, :mod:`loremaster.store.surreal_schema`).
# Configurability would make the inlining guarantee operator-breakable, so this
# stays a MODULE CONSTANT, never a config knob.
AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

# Fleet row ordering (design doc §6): input_required (parked questions, the
# actionable signal) first, then active, then idle; most-recent heartbeat
# first within a group.
_STATUS_SORT_ORDER: dict[str, int] = {
    STATUS_INPUT_REQUIRED: 0,
    STATUS_ACTIVE: 1,
    STATUS_IDLE: 2,
}

# The ``agent`` table columns the ledger reads/writes. Named once each so a
# rename is a single edit, never a hand-copied literal drifting between the
# write content, the resolution WHERE, and the row -> value-object mapping
# (mirrors ``loremaster.tasks``'s ``_COL_*`` idiom).
_COL_NAME = "name"
_COL_SESSION = "session"
_COL_ROLE = "role"
_COL_MODEL = "model"
_COL_STATUS = "status"
_COL_SPAWNED_BY = "spawned_by"
_COL_TASK_ID = "task_id"
_COL_CHECKPOINT = "checkpoint"
_COL_LAST_NOTE = "last_note"
_COL_REGISTERED_AT = "registered_at"
_COL_HEARTBEAT_AT = "heartbeat_at"
# #304 (packet 05a-iii): the tz-aware UTC instant the agent's STATUS VALUE was
# last set — stamped write-side ONLY when the status changes, so the fleet render
# can age the DECLARATION beside the liveness heartbeat (a latched verdict becomes
# a dated fact). ``option<datetime>``: every production agent row predates it and
# reads NONE, so the decode is None-tolerant (never ``_require_aware_utc``).
_COL_STATUS_SET_AT = "status_set_at"

# The record-id table separator. (The signin credential keys moved to the ONE
# shared ``store._txn.signin_credentials`` seam — #211/#102.)
_TABLE_SEPARATOR = ":"
_ID_KEY = "id"

# Bound-parameter names for the single-row lookups/writes below.
_ROW_ID_PARAM = "id"
_ROW_CONTENT_PARAM = "content"
_NAME_LOOKUP_PARAM = "name"
# NEVER literally "session" — SurrealDB rejects a top-level bound $session
# param outright ("'session' is a protected variable and cannot be set"),
# live-verified this session (see the module's schema-slice sibling suite's
# ``TestSessionProtectedVariable`` and the repo CLAUDE.md store idiom).
_SESSION_FILTER_PARAM = "flt_session"
_REG_STATUS_PARAM = "reg_status"
_REG_HEARTBEAT_PARAM = "reg_heartbeat_at"
_REG_MODEL_PARAM = "reg_model"
_REG_TASK_ID_PARAM = "reg_task_id"
_REG_SPAWNED_BY_PARAM = "reg_spawned_by"
_TOUCH_STATUS_PARAM = "touch_status"
_TOUCH_HEARTBEAT_PARAM = "touch_heartbeat_at"
_TOUCH_NOTE_PARAM = "touch_note"
# #304 (packet 05a-iii): the status_set_at stamp, threaded through the register
# re-register UPDATE and the touch UPDATE alike so the "stamp iff the status VALUE
# changed" policy is written ONCE (``_status_set_at_for``) and CALLED, never cloned.
_REG_STATUS_SET_AT_PARAM = "reg_status_set_at"
_TOUCH_STATUS_SET_AT_PARAM = "touch_status_set_at"


class Agent(BaseModel):
    """A single registered agent identity in the fleet-visible agent registry.

    Attributes:
        id: The agent's OPAQUE, hashable string id — a deterministic
            ``uuid5(session, name)`` hex digest, never a raw SurrealDB
            ``RecordID``.
        name: The agent's short identifier (unique within its session).
        session: The orchestration session this agent belongs to.
        role: The agent's role (e.g. ``"builder"``, ``"auditor"``).
        model: The model identifier the agent runs on, or ``None``.
        status: The agent's current state in the four-status vocabulary.
        spawned_by: The identity that spawned this agent, or ``None``.
        task_id: The fleet task id this agent is currently working, or
            ``None``.
        checkpoint: A free-form resumption blob (C1 ships the column; no C1
            action reads or writes it — the workflow lands in C5), or
            ``None``.
        last_note: The most recent free-text heartbeat note, or ``None``.
        registered_at: The tz-aware UTC timestamp of the FIRST registration —
            write-once, never touched again on re-register.
        heartbeat_at: The tz-aware UTC timestamp of the agent's most recent
            fleet-visible activity — touched by every comms action.
        status_set_at: The tz-aware UTC instant ``status`` last CHANGED value, or
            ``None`` for a row written before this field existed (#304). Stamped
            write-side only on a status change — NOT on every heartbeat — so the
            fleet render can age the declaration. A legacy ``None`` renders as an
            explicit unknown, never a fabricated zero age.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    session: str
    role: str
    model: str | None = None
    status: AgentStatus
    spawned_by: str | None = None
    task_id: str | None = None
    checkpoint: dict[str, Any] | None = None
    last_note: str | None = None
    registered_at: datetime
    heartbeat_at: datetime
    status_set_at: datetime | None = None


class AgentRegisterResult(BaseModel):
    """The outcome of an :meth:`AgentRegistry.register` call.

    Attributes:
        agent: The agent's state AFTER this call (freshly-created on a first
            register, or re-stamped on a re-register).
        re_registered: ``False`` on the FIRST register of a (session, name)
            pair; ``True`` on every subsequent idempotent re-register.
    """

    model_config = ConfigDict(extra="forbid")

    agent: Agent
    re_registered: bool


class AgentFleetWindow(BaseModel):
    """The result of an :meth:`AgentRegistry.fleet` listing.

    Attributes:
        rows: The non-retired agents, ordered per design doc §6 (status group,
            then most-recent heartbeat), capped at the caller's ``limit``.
        retired_count: The count of retired agents in scope — elided from
            ``rows`` entirely but honestly counted.
        total_non_retired: The HONEST total of non-retired agents in scope,
            BEFORE ``limit`` truncation (may exceed ``len(rows)``).
    """

    model_config = ConfigDict(extra="forbid")

    rows: list[Agent]
    retired_count: int
    total_non_retired: int


class AgentRosterMember(BaseModel):
    """One agent's identity/status slice inside a :class:`FleetRoster` listing.

    Attributes:
        id: The agent's opaque id.
        name: The agent's short identifier.
        status: The agent's current status.
        heartbeat_at: The agent's most recent heartbeat timestamp.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    status: AgentStatus
    heartbeat_at: datetime


class FleetRoster(BaseModel):
    """The row-UNLIMITED true-count projection over the agent registry (design
    doc §5.3 v4 — the fix for the v4 audit's D1 defect: a display-capped
    :meth:`AgentRegistry.fleet` window's per-status header segments silently
    disagreeing with an already-true total, past ``_MAX_FLEET_LIMIT`` agents).

    Attributes:
        members: The COMPLETE non-retired membership in scope — never a
            display-capped window.
        status_counts: A TRUE per-status aggregate over the WHOLE scope,
            including ``"retired"`` — every one of the four statuses is
            ALWAYS a present key (present-with-zero, never absent).
    """

    model_config = ConfigDict(extra="forbid")

    members: list[AgentRosterMember]
    status_counts: dict[str, int]


class AgentRegistryError(RuntimeError):
    """Base class for every error :class:`AgentRegistry` raises."""


class UnknownAgentError(AgentRegistryError):
    """Raised when a name/session pair resolves to no registered agent row."""


class AmbiguousAgentError(AgentRegistryError):
    """Raised when a bare name (no ``session=``) matches >1 live agent row."""


class AgentIdentityConflictError(AgentRegistryError):
    """Raised when a re-register's write-once field (role/spawned_by) mismatches."""


class RetiredAgentError(AgentRegistryError):
    """Raised when the resolved agent is retired — a terminal status."""


class IllegalAgentStatusError(AgentRegistryError):
    """Raised when a requested status is not a legal state-machine edge/value."""


class AgentRegistry:
    """Durable, fleet-visible agent registry over a single SurrealDB database.

    Mints deterministic ``uuid5(session, name)`` ids (idempotent re-register by
    construction), enforces the closed status state machine, and rides the
    shared :mod:`loremaster.store._txn` error-classification seam so every
    failure surfaces as a typed store error. Mirrors
    :class:`~loremaster.tasks.TaskLedger`'s connection-lifecycle shape exactly.

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
        """Store the registry's wiring. Does not open any connection yet."""
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        # Opened on first use; ``None`` means "not yet connected / closed".
        self._connection: _SurrealConnection | None = None
        # Guards the connect-time check-then-set so N concurrent first-callers
        # never each open their own underlying SDK connection (mirrors
        # ``TaskLedger`` / ``LocalMemoryBackend``'s double-checked lock).
        self._connect_lock = asyncio.Lock()

    # -- connection lifecycle ----------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        The session bootstrap is :func:`~loremaster.store._txn.bootstrap_session`
        — the ONE shared implementation every connection owner in the package
        calls (blindreader F3; see its docstring for the mechanism). This
        method's own job is DISPOSITION: any bootstrap failure — a
        transport/auth fault OR exhausted contention alike — is wrapped as
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
                # A concurrent caller connected while this one waited; mypy
                # can't model the cross-coroutine mutation across the
                # ``await`` above.
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
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "agent.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect and apply the agent schema slice — idempotent and safe to re-run.

        Applies :func:`~loremaster.store.surreal_schema.generate_agent_ddl`
        inside ONE ``BEGIN … COMMIT`` via
        :func:`~loremaster.store._txn.execute_transaction`, which verifies
        EVERY statement's status.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: A DDL statement was rejected by the engine.
        """
        await self._ensure_connection()
        ddl = generate_agent_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("agent.schema.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any); tolerant of a never-connected registry."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal)."""
        if self._connection is connection:
            self._connection = None
        await self._safe_close(connection)

    @staticmethod
    async def _safe_close(connection: _SurrealConnection) -> None:
        """Close ``connection``, swallowing an already-dead-socket failure."""
        try:
            await connection.close()
        except _CONNECTION_ERRORS:
            logger.debug("agent.close.already_closed")

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
            noun="agent query",
            label="agent.query.rejected",
            statement=statement,
            params=params or {},
            logger=logger,
        )

    # -- id + resolution ------------------------------------------------------

    @staticmethod
    def _agent_id(session: str, name: str) -> str:
        """The design doc's pinned id recipe: ``uuid5(session, name)`` hex."""
        return uuid5(NAMESPACE_URL, f"lore://agent/{session}/{name}").hex

    async def _select_row(self, agent_id: str) -> dict[str, Any] | None:
        """Return the raw ``agent`` row dict for ``agent_id``, or ``None`` if absent."""
        rows = self._as_rows(
            await self._query(
                f"SELECT * FROM type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM})",
                {_ROW_ID_PARAM: agent_id},
            )
        )
        return rows[0] if rows else None

    async def _select_rows_by_name(self, name: str) -> list[dict[str, Any]]:
        """Return every ``agent`` row matching ``name`` (any session, any status)."""
        return self._as_rows(
            await self._query(
                f"SELECT * FROM {AGENT_TABLE} WHERE {_COL_NAME} = ${_NAME_LOOKUP_PARAM}",
                {_NAME_LOOKUP_PARAM: name},
            )
        )

    async def _resolve_row(self, name: str, session: str | None) -> dict[str, Any]:
        """Design doc §0.3 name -> row resolution.

        With ``session`` given, resolves the deterministic id directly (this
        DOES find a retired row — the downstream retired-terminal check needs
        it to fire with a teaching error rather than a confusing "unknown
        agent"). Without it: a bare-name search over NON-retired rows only
        (0 -> :class:`UnknownAgentError`; >1 -> :class:`AmbiguousAgentError`
        naming the candidate sessions).

        Raises:
            UnknownAgentError: No matching row exists (or every same-named row
                is retired, when searching bare-name).
            AmbiguousAgentError: >1 non-retired row shares ``name`` across
                different sessions.
        """
        if session is not None:
            row = await self._select_row(self._agent_id(session, name))
            if row is None:
                raise UnknownAgentError(
                    f"agent {name!r} is not registered — every comms call requires "
                    f"a prior 'register'"
                )
            return row
        rows = await self._select_rows_by_name(name)
        candidates = [row for row in rows if row.get(_COL_STATUS) != STATUS_RETIRED]
        if not candidates:
            raise UnknownAgentError(
                f"agent {name!r} is not registered — every comms call requires "
                f"a prior 'register'"
            )
        if len(candidates) > 1:
            sessions = sorted(str(row.get(_COL_SESSION)) for row in candidates)
            raise AmbiguousAgentError(
                f"agent name {name!r} is registered in sessions "
                f"{', '.join(sessions)} — pass session= to disambiguate"
            )
        return candidates[0]

    # -- register -------------------------------------------------------------

    async def register(
        self,
        name: str,
        *,
        session: str,
        role: str,
        model: str | None = None,
        spawned_by: str | None = None,
        task_id: str | None = None,
    ) -> AgentRegisterResult:
        """Idempotently register an agent identity (design doc §1/§2).

        The FIRST call for a (session, name) pair creates the row, birth state
        ``active``, ``re_registered=False``. A later call for the SAME pair is
        an idempotent RE-register (design doc §2): ``role``/``spawned_by`` are
        write-once (a differing value is a teaching
        :class:`AgentIdentityConflictError`; a first-time value on a
        previously-unset ``spawned_by`` FILLS it in without conflict — there
        is no prior value to disagree with); ``model``/``task_id`` are
        mutable (overwritten when provided, kept when omitted); ``status``
        resets to ``active`` unconditionally UNLESS the row is currently
        ``retired``, which is terminal (:class:`RetiredAgentError` — a
        respawn registers a fresh name).

        Args:
            name: The agent's short identifier.
            session: The orchestration session this agent belongs to
                (REQUIRED — it is half of the deterministic id).
            role: The agent's role.
            model: The model identifier the agent runs on.
            spawned_by: The identity that spawned this agent.
            task_id: The fleet task id this agent is currently working.

        Returns:
            The :class:`AgentRegisterResult` of this call.

        Raises:
            RetiredAgentError: The row already exists and is retired.
            AgentIdentityConflictError: ``role`` or ``spawned_by`` differs from
                the existing row's concrete value.
        """
        agent_id = self._agent_id(session, name)
        existing_row = await self._select_row(agent_id)
        now = datetime.now(UTC)

        if existing_row is None:
            content: dict[str, Any] = {
                _COL_NAME: name,
                _COL_SESSION: session,
                _COL_ROLE: role,
                _COL_MODEL: model,
                _COL_STATUS: STATUS_ACTIVE,
                _COL_SPAWNED_BY: spawned_by,
                _COL_TASK_ID: task_id,
                _COL_CHECKPOINT: None,
                _COL_LAST_NOTE: None,
                _COL_REGISTERED_AT: now,
                _COL_HEARTBEAT_AT: now,
                # #304: birth of the ``active`` status IS a status set — stamp it,
                # so a never-changed agent still has an honest declaration instant.
                _COL_STATUS_SET_AT: self._status_set_at_for(STATUS_ACTIVE, None, None, now),
            }
            await self._query(
                f"CREATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) "
                f"CONTENT ${_ROW_CONTENT_PARAM}",
                {_ROW_ID_PARAM: agent_id, _ROW_CONTENT_PARAM: content},
            )
            created = await self._select_row(agent_id)
            if created is None:
                raise AgentRegistryError(
                    f"agent {agent_id!r} vanished immediately after it was created"
                )
            return AgentRegisterResult(agent=self._row_to_agent(created), re_registered=False)

        existing = self._row_to_agent(existing_row)
        if existing.status == STATUS_RETIRED:
            raise RetiredAgentError(
                f"agent {name!r} is retired (terminal) — respawns register a fresh name"
            )
        if existing.role != role:
            raise AgentIdentityConflictError(
                f"agent {name!r} is already registered with role {render_attributed(existing.role)} "
                f"(you sent {render_attributed(role)}) — names are never reused; register a fresh name "
                f"(e.g. {name + '2'!r})"
            )
        if (
            spawned_by is not None
            and existing.spawned_by is not None
            and existing.spawned_by != spawned_by
        ):
            raise AgentIdentityConflictError(
                f"agent {name!r} is already registered with spawned_by "
                f"{render_attributed(existing.spawned_by)} (you sent "
                f"{render_attributed(spawned_by)}) — names are never "
                f"reused; register a fresh name (e.g. {name + '2'!r})"
            )

        new_model = model if model is not None else existing.model
        new_task_id = task_id if task_id is not None else existing.task_id
        # write-once, resolved: a first-time incoming value fills a
        # previously-unset field without conflict (the mismatch case above
        # already refused a differing CONCRETE value).
        new_spawned_by = spawned_by if spawned_by is not None else existing.spawned_by
        # #304: re-register resets status to ``active`` — stamp status_set_at only
        # when that is a real CHANGE from the existing stored status (a re-register
        # of an already-``active`` agent must not reset its declaration age).
        new_status_set_at = self._status_set_at_for(
            STATUS_ACTIVE, existing.status, existing.status_set_at, now
        )
        await self._query(
            f"UPDATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) SET "
            f"{_COL_STATUS} = ${_REG_STATUS_PARAM}, "
            f"{_COL_HEARTBEAT_AT} = ${_REG_HEARTBEAT_PARAM}, "
            f"{_COL_MODEL} = ${_REG_MODEL_PARAM}, "
            f"{_COL_TASK_ID} = ${_REG_TASK_ID_PARAM}, "
            f"{_COL_SPAWNED_BY} = ${_REG_SPAWNED_BY_PARAM}, "
            f"{_COL_STATUS_SET_AT} = ${_REG_STATUS_SET_AT_PARAM}",
            {
                _ROW_ID_PARAM: agent_id,
                _REG_STATUS_PARAM: STATUS_ACTIVE,
                _REG_HEARTBEAT_PARAM: now,
                _REG_MODEL_PARAM: new_model,
                _REG_TASK_ID_PARAM: new_task_id,
                _REG_SPAWNED_BY_PARAM: new_spawned_by,
                _REG_STATUS_SET_AT_PARAM: new_status_set_at,
            },
        )
        updated = await self._select_row(agent_id)
        if updated is None:
            raise AgentRegistryError(f"agent {agent_id!r} vanished immediately after re-register")
        return AgentRegisterResult(agent=self._row_to_agent(updated), re_registered=True)

    # -- read -------------------------------------------------------------

    async def get_agent(self, name: str, *, session: str | None = None) -> Agent:
        """Resolve and fetch a single agent (design doc §0.3).

        Args:
            name: The agent's short identifier.
            session: Optional session to disambiguate a bare name shared
                across sessions.

        Returns:
            The matching :class:`Agent` (a FRESH value object).

        Raises:
            UnknownAgentError: No matching row exists.
            AmbiguousAgentError: ``session`` was omitted and >1 non-retired
                row shares ``name`` across sessions.
        """
        row = await self._resolve_row(name, session)
        return self._row_to_agent(row)

    # -- heartbeat / status machine ------------------------------------------

    async def touch(
        self,
        name: str,
        *,
        session: str | None = None,
        status: str | None = None,
        note: str | None = None,
    ) -> Agent:
        """The ONE heartbeat/status-machine primitive (design doc §3/§8).

        Resolves the agent (design doc §0.3), refuses if it is retired
        (terminal), then decides the new status: an explicit ``status``
        (validated against the closed domain + the legal-edge matrix, a
        self-edge is a legal no-op) always wins; absent an explicit status, an
        ``idle`` agent auto-flips to ``active`` (any comms action proves it is
        alive); ``input_required``/``active`` are unchanged. Always stamps
        ``heartbeat_at = now``; ``note`` overwrites ``last_note`` when given,
        else the prior value is preserved.

        Args:
            name: The agent's short identifier.
            session: Optional session to disambiguate a bare name.
            status: An optional explicit target status.
            note: An optional free-text note to record as ``last_note``.

        Returns:
            The agent's updated state.

        Raises:
            UnknownAgentError: No matching row exists.
            AmbiguousAgentError: ``session`` was omitted and the name is
                ambiguous.
            RetiredAgentError: The resolved agent is retired.
            IllegalAgentStatusError: ``status`` is out of domain (including
                the derived-only ``'orphaned'``) or not a legal edge from the
                agent's current status.
        """
        row = await self._resolve_row(name, session)
        agent = self._row_to_agent(row)
        if agent.status == STATUS_RETIRED:
            raise RetiredAgentError(
                f"agent {name!r} is retired (terminal) — respawns register a fresh name"
            )

        new_status: AgentStatus
        if status is not None:
            new_status = self._validate_status_edge(name, agent.status, status)
        elif agent.status == STATUS_IDLE:
            # Auto-flip: any comms action by an idle agent proves it active,
            # unless this call carried an explicit status (handled above).
            new_status = STATUS_ACTIVE
        else:
            # input_required never auto-flips; active stays active.
            new_status = agent.status

        now = datetime.now(UTC)
        new_note = note if note is not None else agent.last_note
        # #304: age the DECLARATION, not the heartbeat — stamp status_set_at only
        # when new_status differs from the stored status (a same-status heartbeat
        # preserves the prior stamp; a change records ``now``).
        new_status_set_at = self._status_set_at_for(
            new_status, agent.status, agent.status_set_at, now
        )
        await self._query(
            f"UPDATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) SET "
            f"{_COL_STATUS} = ${_TOUCH_STATUS_PARAM}, "
            f"{_COL_HEARTBEAT_AT} = ${_TOUCH_HEARTBEAT_PARAM}, "
            f"{_COL_LAST_NOTE} = ${_TOUCH_NOTE_PARAM}, "
            f"{_COL_STATUS_SET_AT} = ${_TOUCH_STATUS_SET_AT_PARAM}",
            {
                _ROW_ID_PARAM: agent.id,
                _TOUCH_STATUS_PARAM: new_status,
                _TOUCH_HEARTBEAT_PARAM: now,
                _TOUCH_NOTE_PARAM: new_note,
                _TOUCH_STATUS_SET_AT_PARAM: new_status_set_at,
            },
        )
        updated = await self._select_row(agent.id)
        if updated is None:
            raise AgentRegistryError(f"agent {agent.id!r} vanished immediately after touch")
        return self._row_to_agent(updated)

    @staticmethod
    def _status_set_at_for(
        new_status: str,
        prior_status: str | None,
        prior_stamp: datetime | None,
        now: datetime,
    ) -> datetime | None:
        """The ``status_set_at`` value a write must persist (#304, packet 05a-iii).

        ``now`` iff the status VALUE is changing (a new declaration), else the
        PRESERVED ``prior_stamp`` — so a same-status heartbeat leaves the
        declaration age untouched (else every heartbeat would reset it to ~0s, the
        latch bug inverted). ``prior_status is None`` is the first-registration
        birth: no prior value to disagree with, so it always stamps. The ONE place
        this policy lives — the register re-register UPDATE and the touch UPDATE
        both CALL it (never a cloned ``now if … else …`` at each site).
        """
        return now if new_status != prior_status else prior_stamp

    @staticmethod
    def _validate_status_edge(name: str, current: AgentStatus, target: str) -> AgentStatus:
        """Validate an explicit ``status=`` target, else raise a teaching error.

        Order: the derived-only ``'orphaned'`` value gets its OWN teaching
        message naming the derivation (design doc §3/§7); any other
        out-of-domain value is refused naming the legal domain; a self-edge
        (``target == current``) is always a legal no-op; any other
        ``(current, target)`` pair not in :data:`LEGAL_AGENT_TRANSITIONS` is an
        illegal edge naming both states and the legal targets from ``current``.

        Raises:
            IllegalAgentStatusError: Any of the refusals above.
        """
        if target not in AGENT_STATUSES:
            if target == _AGENT_STATUS_ORPHANED:
                raise IllegalAgentStatusError(
                    "'orphaned' is derived from heartbeat age at render time, never "
                    f"set; legal statuses: {', '.join(sorted(AGENT_STATUSES))}"
                )
            raise IllegalAgentStatusError(
                f"{render_attributed(target)} is not a legal agent status; legal statuses: "
                f"{', '.join(sorted(AGENT_STATUSES))}"
            )
        target_status = cast(AgentStatus, target)
        if target_status == current:
            return target_status
        if (current, target_status) not in LEGAL_AGENT_TRANSITIONS:
            legal_from = sorted(
                to_status for from_status, to_status in LEGAL_AGENT_TRANSITIONS if from_status == current
            )
            raise IllegalAgentStatusError(
                f"illegal status transition {current} -> {target_status} for {name!r}; "
                f"legal from {current}: {', '.join(legal_from)}"
            )
        return target_status

    # -- fleet ----------------------------------------------------------------

    async def fleet(self, *, session: str | None = None, limit: int) -> AgentFleetWindow:
        """The fleet-visible listing (design doc §6).

        Args:
            session: Optional session filter; omitted spans every session.
            limit: The maximum number of non-retired rows to return.

        Returns:
            The :class:`AgentFleetWindow`: non-retired rows ordered by status
            group then most-recent heartbeat, capped at ``limit``; the honest
            ``total_non_retired`` count BEFORE truncation; and the retired
            count (elided from ``rows`` entirely).
        """
        statement = f"SELECT * FROM {AGENT_TABLE}"
        params: dict[str, Any] = {}
        if session is not None:
            statement += f" WHERE {_COL_SESSION} = ${_SESSION_FILTER_PARAM}"
            params[_SESSION_FILTER_PARAM] = session
        rows = self._as_rows(await self._query(statement, params))
        agents = [self._row_to_agent(row) for row in rows]
        retired = [agent for agent in agents if agent.status == STATUS_RETIRED]
        non_retired = [agent for agent in agents if agent.status != STATUS_RETIRED]
        non_retired.sort(
            key=lambda agent: (_STATUS_SORT_ORDER[agent.status], -agent.heartbeat_at.timestamp())
        )
        total = len(non_retired)
        limited = non_retired[:limit]
        return AgentFleetWindow(rows=limited, retired_count=len(retired), total_non_retired=total)

    async def roster(self, *, session: str | None = None) -> FleetRoster:
        """The row-UNLIMITED true-count projection (design doc §5.3 v4).

        Unlike :meth:`fleet`, this method takes NO ``limit`` — a regression
        that re-added one would silently reintroduce the exact cap-vs-truth
        confusion this method exists to close (the v4 audit's D1 finding: a
        display-capped ``fleet()`` window's per-status header segments
        disagreeing with an already-true total past ``_MAX_FLEET_LIMIT``
        agents). ``status_counts`` comes from ONE ``GROUP BY`` aggregate over
        the whole scope (including ``retired``); ``members`` is the complete
        non-retired membership, row-unlimited.

        Args:
            session: Optional session filter; omitted spans every session.

        Returns:
            The :class:`FleetRoster`: a true per-status count (all four
            statuses present, zero-filled when a status has no rows) and the
            complete non-retired membership.
        """
        where_clause = ""
        params: dict[str, Any] = {}
        if session is not None:
            where_clause = f" WHERE {_COL_SESSION} = ${_SESSION_FILTER_PARAM}"
            params[_SESSION_FILTER_PARAM] = session

        count_rows = self._as_rows(
            await self._query(
                f"SELECT {_COL_STATUS}, count() AS count FROM {AGENT_TABLE}{where_clause} "
                f"GROUP BY {_COL_STATUS}",
                params,
            )
        )
        status_counts: dict[str, int] = dict.fromkeys(AGENT_STATUSES, 0)
        for row in count_rows:
            status = row.get(_COL_STATUS)
            if status in status_counts:
                status_counts[status] = int(row.get("count", 0))

        rows = self._as_rows(await self._query(f"SELECT * FROM {AGENT_TABLE}{where_clause}", params))
        members = [
            AgentRosterMember(
                id=agent.id, name=agent.name, status=agent.status, heartbeat_at=agent.heartbeat_at
            )
            for agent in (self._row_to_agent(row) for row in rows)
            if agent.status != STATUS_RETIRED
        ]
        return FleetRoster(members=members, status_counts=status_counts)

    # -- result narrowing / mapping -------------------------------------------

    @staticmethod
    def _as_rows(result: Any) -> list[dict[str, Any]]:
        """Narrow a ``SELECT`` result to its list of dict rows."""
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    def _row_to_agent(self, row: dict[str, Any]) -> Agent:
        """Map a raw ``agent`` row into a FRESH :class:`Agent` value object.

        Never returns the raw row: the ``RecordID`` is reduced to its bare
        opaque string, both required datetimes are normalised to tz-aware
        UTC, and the option columns decode back to ``None``.
        """
        return Agent(
            id=self._bare_id(row.get(_ID_KEY)),
            name=str(row.get(_COL_NAME, "")),
            session=str(row.get(_COL_SESSION, "")),
            role=str(row.get(_COL_ROLE, "")),
            model=row.get(_COL_MODEL),
            status=cast(AgentStatus, row.get(_COL_STATUS)),
            spawned_by=row.get(_COL_SPAWNED_BY),
            task_id=row.get(_COL_TASK_ID),
            checkpoint=row.get(_COL_CHECKPOINT),
            last_note=row.get(_COL_LAST_NOTE),
            registered_at=self._require_aware_utc(row.get(_COL_REGISTERED_AT), _COL_REGISTERED_AT),
            heartbeat_at=self._require_aware_utc(row.get(_COL_HEARTBEAT_AT), _COL_HEARTBEAT_AT),
            # #304: NONE-tolerant — a legacy row omits the column entirely (store
            # reference §2: ``SELECT *`` omits a NONE-valued option column), so a
            # required-datetime decode would wrongly raise. The write-side stamp
            # (touch/register on a status CHANGE) is the builder's; this stub only
            # threads the value through so the model round-trips.
            status_set_at=row.get(_COL_STATUS_SET_AT),
        )

    def _require_aware_utc(self, value: Any, column: str) -> datetime:
        """Normalise a REQUIRED datetime column to tz-aware UTC, refusing a bad value.

        Raises:
            SurrealStoreError: The value is missing or cannot be read as a datetime.
        """
        coerced = self._to_aware_utc(value)
        if coerced is None:
            raise SurrealStoreError(
                f"agent row column {column!r} is missing or not a datetime "
                f"(got {type(value).__name__})"
            )
        return coerced

    @staticmethod
    def _to_aware_utc(value: Any) -> datetime | None:
        """Coerce a stored datetime into a tz-aware UTC datetime (or ``None``).

        Mirrors :meth:`~loremaster.tasks.TaskLedger._to_aware_utc`: the SDK's
        CBOR decoder returns tz-aware datetimes, but a naive datetime or an
        ISO-string/wrapper shape is normalised defensively.
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

    @staticmethod
    def _bare_id(raw: Any) -> str:
        """Return the BARE agent id — no ``agent:`` record-table prefix.

        Mirrors :meth:`~loremaster.tasks.TaskLedger._bare_id`: the API speaks
        bare ``str`` everywhere because the SDK's ``RecordID`` is unhashable.
        """
        if isinstance(raw, RecordID):
            return str(raw.id)
        text = str(raw)
        if _TABLE_SEPARATOR in text:
            return text.split(_TABLE_SEPARATOR, 1)[1]
        return text
