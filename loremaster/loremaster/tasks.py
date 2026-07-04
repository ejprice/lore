"""The durable, fleet-visible TASK LEDGER (lore v2 P7 orchestration spine).

:class:`TaskLedger` is the fleet-coordination primitive: a SurrealDB table of
work items many concurrent agent/orchestrator sessions can SEE
(:meth:`~TaskLedger.query_tasks`), CLAIM atomically
(:meth:`~TaskLedger.claim_task` — a compare-and-set exactly one racer wins),
drive through a state machine (:meth:`~TaskLedger.transition`), and reframe
without losing history (:meth:`~TaskLedger.supersede_task`). It rides the SAME
store machinery the rest of the layer uses:

* one lazily-opened, signed-in WS connection, self-healed on a mid-life
  transport failure (a dropped handle so the next call reconnects), reusing the
  shared transaction / error-classification seams in
  :mod:`loremaster.store._txn` — a transport fault surfaces as
  :class:`~loremaster.store._txn.SurrealConnectionError`, a domain rejection as
  :class:`~loremaster.store._txn.SurrealStoreError`, never a raw engine string
  (the exact posture :class:`~loremaster.memory.local.LocalMemoryBackend` and
  :class:`~loremaster.store.surreal.SurrealStore` share);
* THE load-bearing atomic claim rides :func:`~loremaster.store._txn.compose` +
  :func:`~loremaster.store._txn.execute_transaction` — a single
  ``BEGIN … COMMIT`` with per-statement verification and bounded
  optimistic-concurrency retry — so the eligibility check (open ∧ unowned ∧ not
  superseded ∧ no unresolved blockers) and the mutation (owner / ``claimed`` /
  ``claimed_at``) are decided together and two racers can never both win.

The public surface (transcribed verbatim from the contract test's module
docstring — that file is the authoritative spec):

    Task:                                  # a value object (pydantic model)
        id: str                            # OPAQUE — never a raw RecordID
        subject: str
        description: str
        status: Literal[open|claimed|in_progress|done|blocked|wontfix]
        owner: str | None                  # an agent/session identity
        claimed_at: datetime | None        # tz-aware UTC when claimed
        blocked_by: list[str]              # task ids this depends on
        provenance: dict                   # who created/changed + timestamps
        superseded_by: str | None
        created_at: datetime               # tz-aware UTC

    ClaimResult:
        claimed: bool
        task: Task                         # updated (win) OR current state (loss)

    TaskLedger(*, url, namespace, database, user, password):
        async ensure_ready() -> None
        async close() -> None
        async create_task(subject, description, *, blocked_by=None, created_by) -> str
        async get_task(task_id) -> Task
        async query_tasks(*, status=None, owner=None, blocked=None) -> list[Task]
        async claim_task(task_id, owner) -> ClaimResult
        async transition(task_id, status, *, actor) -> Task
        async supersede_task(task_id, *, subject, description, created_by) -> str

    Exceptions: TaskLedgerError(RuntimeError);
                TaskNotFoundError(TaskLedgerError);
                IllegalTransitionError(TaskLedgerError).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from surrealdb import AsyncSurreal, RecordID

from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    SurrealStoreError,
    TxnFragment,
    _SurrealConnection,
    compose,
    execute_transaction,
    is_connection_error,
)
from loremaster.store.surreal_schema import TASK_TABLE, generate_task_ddl

logger = logging.getLogger(__name__)

# The status vocabulary this contract decides (mirrors the six statuses named in
# the test module's ``STATUS_*`` constants and the schema's ``_TASK_STATUSES``).
# Kept as a ``Literal`` alias so :class:`Task.status` is typed against the closed
# set the state machine enforces, without hardcoding the set a second time.
TaskStatus = Literal["open", "claimed", "in_progress", "done", "blocked", "wontfix"]

# --- the six statuses, as named constants (never bare literals in logic) ------
STATUS_OPEN: TaskStatus = "open"
STATUS_CLAIMED: TaskStatus = "claimed"
STATUS_IN_PROGRESS: TaskStatus = "in_progress"
STATUS_DONE: TaskStatus = "done"
STATUS_BLOCKED: TaskStatus = "blocked"
STATUS_WONTFIX: TaskStatus = "wontfix"

# The closed status domain — membership is what makes a transition target a
# legal *value* at all (a garbage target is refused before the edge check).
TASK_STATUSES: frozenset[str] = frozenset(
    {STATUS_OPEN, STATUS_CLAIMED, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_BLOCKED, STATUS_WONTFIX}
)

# The two TERMINAL statuses — no transition may leave them — which are ALSO the
# exact set that "resolves" a blocker (a ``blocked_by`` entry stops blocking once
# its blocker reaches one of these). One source of truth for both semantics, so a
# claimer and the ``query_tasks(blocked=…)`` partition can never disagree.
TERMINAL_STATUSES: frozenset[str] = frozenset({STATUS_DONE, STATUS_WONTFIX})

# The full legal transition matrix (the state machine, transcribed verbatim from
# the contract test's ``LEGAL_TRANSITIONS``): every ``(from, to)`` edge NOT in
# this frozen set is illegal — including the claim-only ``open -> claimed`` edge
# (reachable ONLY through :meth:`~TaskLedger.claim_task`, never here), the no-op
# self-edges, and every edge out of a terminal status.
LEGAL_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        (STATUS_CLAIMED, STATUS_IN_PROGRESS),
        (STATUS_IN_PROGRESS, STATUS_DONE),
        (STATUS_OPEN, STATUS_BLOCKED),
        (STATUS_CLAIMED, STATUS_BLOCKED),
        (STATUS_IN_PROGRESS, STATUS_BLOCKED),
        (STATUS_BLOCKED, STATUS_OPEN),
        (STATUS_BLOCKED, STATUS_IN_PROGRESS),
        (STATUS_OPEN, STATUS_WONTFIX),
        (STATUS_CLAIMED, STATUS_WONTFIX),
        (STATUS_IN_PROGRESS, STATUS_WONTFIX),
        (STATUS_BLOCKED, STATUS_WONTFIX),
    }
)

# The ``task`` table columns the ledger reads/writes. Named once each so a rename
# is a single edit, never a hand-copied literal drifting between the write
# content, the atomic-claim WHERE and the row → value-object mapping.
_COL_SUBJECT = "subject"
_COL_DESCRIPTION = "description"
_COL_STATUS = "status"
_COL_OWNER = "owner"
_COL_CLAIMED_AT = "claimed_at"
_COL_BLOCKED_BY = "blocked_by"
_COL_PROVENANCE = "provenance"
_COL_SUPERSEDED_BY = "superseded_by"
_COL_CREATED_AT = "created_at"

# The provenance blob's keys + the audit-event action names. ``provenance`` is a
# FLEXIBLE object whose exact layout the contract leaves open (it asserts only
# that an acting identity appears as a value somewhere inside), so these are the
# ledger's OWN chosen shape: a ``created_by`` stamp + an append-only ``events``
# log, each event naming its ``actor`` and ``action``.
_PROV_CREATED_BY = "created_by"
_PROV_CREATED_AT = "created_at"
_PROV_EVENTS = "events"
_PROV_ACTOR = "actor"
_PROV_ACTION = "action"
_PROV_AT = "at"
_PROV_TO = "to"
_PROV_SUCCESSOR = "successor"
_ACTION_TRANSITION = "transition"
_ACTION_SUPERSEDE = "supersede"

# The signin credential keys the SDK expects, and the record-id table separator.
_SIGNIN_USER_KEY = "username"
_SIGNIN_PASS_KEY = "password"
_TABLE_SEPARATOR = ":"
_ID_KEY = "id"

# The atomic-claim transaction's bound-parameter names (the ``clm_`` prefix
# namespaces the composed fragment so nothing collides). ``clm_resolved`` is the
# LET-bound list of blocker record-ids that have reached a terminal status; the
# CAS is eligible only when EVERY blocker resolved, expressed as
# ``array::len(blocked_by) = array::len($clm_resolved)`` — a never-minted or
# still-open blocker is simply absent from that list, so the lengths differ and
# the claim fails CLOSED.
_CLAIM_ID_PARAM = "clm_id"
_CLAIM_OWNER_PARAM = "clm_owner"
_CLAIM_BLOCKED_BY_PARAM = "clm_blocked_by"
_CLAIM_TERMINAL_PARAM = "clm_terminal"
_CLAIM_OPEN_PARAM = "clm_open"
_CLAIM_CLAIMED_PARAM = "clm_claimed"
_CLAIM_RESOLVED_VAR = "clm_resolved"

# The supersede transaction's bound-parameter names (the ``sup_`` prefix).
_SUPERSEDE_NEW_ID_PARAM = "sup_new_id"
_SUPERSEDE_CONTENT_PARAM = "sup_content"
_SUPERSEDE_OLD_ID_PARAM = "sup_old_id"
# The single new provenance EVENT this supersede appends SERVER-SIDE (never the
# whole provenance object — a Python read-modify-write would silently clobber a
# concurrently-committed transition's event on the SAME row; see
# :meth:`TaskLedger._supersede_fragment`).
_SUPERSEDE_EVENT_PARAM = "sup_event"
# The LET-bound variable holding the guarded stamp's result rows, and the
# FIXED message its zero-row guard THROWs. The message is a constant (never a
# bound value), so the rolled-back rejection carries no interpolated data
# (ledger #31); it surfaces only server-side, mapped to IllegalTransitionError.
_SUPERSEDE_STAMPED_VAR = "sup_stamped"
_SUPERSEDE_ALREADY_MESSAGE = "task is already superseded"

# The transition UPDATE's bound-parameter names (the ``tr_`` prefix).
_TRANSITION_ID_PARAM = "tr_id"
_TRANSITION_STATUS_PARAM = "tr_status"
# The single new provenance EVENT this transition appends SERVER-SIDE (never
# the whole provenance object — see :meth:`TaskLedger._transition_fragment`).
_TRANSITION_EVENT_PARAM = "tr_event"
# The transition CAS's ``expected_from`` guard param — the exact status the
# pre-read saw; the guarded UPDATE mutates ONLY while the row is STILL there.
_TRANSITION_EXPECTED_FROM_PARAM = "tr_expected_from"
# The LET-bound variable holding the guarded transition's result rows (mirrors
# the supersede fragment's ``$sup_stamped`` shape), and the FIXED message its
# zero-row guard THROWs. A concurrent writer that already moved the row OFF
# ``expected_from`` — to ANY status, including this call's OWN target — makes
# this UPDATE match zero rows; the THROW rolls the whole transaction back so a
# lost race is ALWAYS a typed, detectable rollback, never a silent no-op a
# caller could mistake for success (a same-target race a bare post-CAS
# ``status`` re-read cannot distinguish from a genuine win).
_TRANSITION_UPDATED_VAR = "tr_updated"
_TRANSITION_ALREADY_MESSAGE = "task transition lost a concurrent compare-and-set"

# The single-read existence-check / create param names.
_ROW_ID_PARAM = "id"
_ROW_CONTENT_PARAM = "content"


class Task(BaseModel):
    """A single work item in the fleet-visible task ledger.

    Attributes:
        id: The task's OPAQUE, hashable string id — never a raw SurrealDB
            ``RecordID``.
        subject: The short human-readable title of the work item.
        description: The longer free-text description of the work item.
        status: The task's current state in the six-status vocabulary.
        owner: The agent/session identity currently holding the task, or
            ``None`` when unclaimed.
        claimed_at: The tz-aware UTC timestamp the task was claimed at, or
            ``None`` when never claimed.
        blocked_by: The ids of the tasks this task depends on (may be empty).
        provenance: Who created/changed the task and when, as a free-form dict.
        superseded_by: The id of the successor task this one was superseded
            by, or ``None`` when not superseded.
        created_at: The tz-aware UTC timestamp the task was created at.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    subject: str
    description: str
    status: TaskStatus
    owner: str | None = None
    claimed_at: datetime | None = None
    blocked_by: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    superseded_by: str | None = None
    created_at: datetime


class ClaimResult(BaseModel):
    """The outcome of an atomic :meth:`TaskLedger.claim_task` compare-and-set.

    Attributes:
        claimed: Whether THIS call won the claim.
        task: The task's state after the call — the freshly-claimed state on a
            win, or the current (unmodified) state on a loss.
    """

    model_config = ConfigDict(extra="forbid")

    claimed: bool
    task: Task


class TaskLedgerError(RuntimeError):
    """Base class for every error :class:`TaskLedger` raises."""


class TaskNotFoundError(TaskLedgerError):
    """Raised when a task id does not resolve to any row in the ledger."""


class IllegalTransitionError(TaskLedgerError):
    """Raised when a requested status transition is not a legal state-machine edge."""


class TaskLedger:
    """Durable, fleet-visible task ledger over a single SurrealDB database.

    Speaks the six-status task wire vocabulary (see the module docstring)
    against a per-project SurrealDB ``task`` table, mints OPAQUE ``uuid4`` string
    ids (never a raw ``RecordID``), and rides the shared
    :mod:`loremaster.store._txn` transaction / error-classification seams so the
    atomic claim is a genuine server-side compare-and-set and every failure
    surfaces as a typed store error.

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
        """Store the ledger's wiring. Does not open any connection yet.

        Args:
            url: The SurrealDB RPC URL.
            namespace: The namespace the database lives under.
            database: The per-project database name.
            user: The root/username to sign in with.
            password: The password to sign in with.
        """
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        # Opened on first use; ``None`` means "not yet connected / closed".
        self._connection: _SurrealConnection | None = None
        # Guards the connect-time check-then-set so N concurrent first-callers
        # never each open their own underlying SDK connection (mirrors
        # ``SurrealStore`` / ``LocalMemoryBackend``'s double-checked lock).
        self._connect_lock = asyncio.Lock()

    # -- connection lifecycle ----------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking (mirrors :class:`LocalMemoryBackend`): the fast
        path never touches the lock; a first caller signs in, materialises the
        namespace/database idempotently and selects them. Any transport/auth
        failure is a LOUD, typed :class:`SurrealConnectionError` — never a hang
        or a silent empty result.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        if self._connection is not None:
            return self._connection
        async with self._connect_lock:
            if self._connection is not None:
                # A concurrent caller connected while this one waited; mypy can't
                # model the cross-coroutine mutation across the ``await`` above.
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
                # Close the half-open socket so a failed connect never leaks a
                # dangling connection, then surface a typed connection error.
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "task.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect and apply the task schema slice — idempotent and safe to re-run.

        Applies :func:`~loremaster.store.surreal_schema.generate_task_ddl` (the
        ``task`` table + its status index) inside ONE ``BEGIN … COMMIT`` via
        :func:`~loremaster.store._txn.execute_transaction`, which verifies EVERY
        statement's status (the SDK's plain ``query()`` inspects only the first).
        The DDL is ``IF NOT EXISTS``, so a second call neither raises nor wipes
        data — every per-test fresh database depends on this.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: A DDL statement was rejected by the engine.
        """
        await self._ensure_connection()
        ddl = generate_task_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("task.schema.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any); tolerant of a never-connected ledger."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal).

        A compare-and-swap (mirrors :class:`LocalMemoryBackend`):
        ``self._connection`` is cleared only when ``connection`` is STILL the
        cached handle, so a late caller holding a stale reference can never wipe
        out a freshly-reconnected one. The handed connection is always closed.
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
            logger.debug("task.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection, self-healing.

        Classifies a failure exactly as :meth:`LocalMemoryBackend._query` does
        (via :func:`~loremaster.store._txn.is_connection_error`): a transport /
        socket / auth fault (or the SDK's ``KeyError`` response-routing race)
        drops the cached handle so the next call reconnects and surfaces a LOUD
        :class:`SurrealConnectionError`; a domain/schema rejection keeps the
        healthy connection and surfaces as :class:`SurrealStoreError`. Never a
        silent empty result, never a raw engine string leaked to the caller.
        """
        connection = await self._ensure_connection()
        try:
            return await connection.query(statement, params or {})
        except (*_CONNECTION_ERRORS, KeyError) as error:
            if isinstance(error, KeyError) or is_connection_error(error):
                await self._drop_connection(connection)
                raise SurrealConnectionError(
                    f"SurrealDB task query failed against {self._url!r}: {error}"
                ) from error
            # A domain/schema rejection — keep the healthy connection.
            raise SurrealStoreError(
                f"SurrealDB task query rejected against {self._url!r}: {error}"
            ) from error

    async def _apply(self, fragments: list[TxnFragment]) -> None:
        """Compose ``fragments`` into ONE transaction and run it atomically.

        Mirrors :meth:`LocalMemoryBackend._apply`: the composed ``BEGIN … COMMIT``
        runs through :func:`~loremaster.store._txn.execute_transaction` (every
        statement's status verified, transport failure self-healed, retryable
        write-write conflict bounded-retried), so a claim's eligibility read and
        mutation — or a supersede's successor-CREATE and old-row stamp — either
        both land or neither does, and two racers can never both win.
        """
        statement_text, merged_params = compose(*fragments)
        await execute_transaction(
            statement_text,
            merged_params,
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )

    # -- create / read ------------------------------------------------------

    async def create_task(
        self,
        subject: str,
        description: str,
        *,
        blocked_by: list[str] | None = None,
        created_by: str,
    ) -> str:
        """Create a new, open, unowned task and return its opaque id.

        The task starts ``open`` / unowned / unclaimed, with ``created_by``
        recorded in ``provenance`` and a tz-aware UTC creation stamp. Unlike the
        memory model (which uuid5s over content and collapses duplicates), tasks
        are NEVER content-deduped: a fresh ``uuid4`` id is minted every call, so
        two tasks sharing a subject are two distinct work items.

        Args:
            subject: The short human-readable title of the work item.
            description: The longer free-text description of the work item.
            blocked_by: Optional ids of tasks this new task depends on;
                DUPLICATE ids are collapsed to set semantics (order-preserving)
                so a repeated id never double-counts against the claim gate.
            created_by: The identity of the caller creating this task, recorded
                in ``provenance``.

        Returns:
            The newly created task's opaque, hashable string id.
        """
        task_id = uuid4().hex  # OPAQUE, non-sequential; never content-derived.
        now = datetime.now(UTC)
        content = self._new_task_content(subject, description, blocked_by, created_by, now)
        await self._query(
            f"CREATE type::record('{TASK_TABLE}', ${_ROW_ID_PARAM}) CONTENT ${_ROW_CONTENT_PARAM}",
            {_ROW_ID_PARAM: task_id, _ROW_CONTENT_PARAM: content},
        )
        return task_id

    async def get_task(self, task_id: str) -> Task:
        """Fetch a single task by its opaque id.

        Args:
            task_id: The opaque task id to fetch.

        Returns:
            The matching :class:`Task` (a FRESH value object, never a raw row).

        Raises:
            TaskNotFoundError: No task with ``task_id`` exists.
        """
        return await self._get_or_raise(task_id)

    async def query_tasks(
        self,
        *,
        status: str | None = None,
        owner: str | None = None,
        blocked: bool | None = None,
    ) -> list[Task]:
        """Return the tasks matching every supplied filter, AND-combined.

        The fleet-visible read: exact ``status`` / ``owner`` equality filters
        plus a dependency-aware ``blocked`` partition. A task is BLOCKED iff ANY
        of its ``blocked_by`` entries is unresolved — the blocker's row is
        missing (a never-minted id ⇒ fail-closed UNRESOLVED) or its status is not
        terminal (``done`` / ``wontfix``). Blocker statuses are resolved against
        the full table so a blocker filtered OUT by the ``status`` / ``owner``
        filter still counts.

        Args:
            status: When given, restrict to tasks in this exact status.
            owner: When given, restrict to tasks currently owned by this
                identity.
            blocked: When given, restrict to genuinely-blocked (``True``) or
                genuinely-unblocked (``False``) tasks.

        Returns:
            The matching tasks (empty when nothing matches).
        """
        rows = self._as_rows(await self._query(f"SELECT * FROM {TASK_TABLE}"))
        tasks = [self._row_to_task(row) for row in rows]
        # Resolve blockers against EVERY task, not the post-filter subset, so a
        # blocker excluded by ``status``/``owner`` still contributes its status.
        status_by_id = {task.id: str(task.status) for task in tasks}

        selected: list[Task] = []
        for task in tasks:
            if status is not None and task.status != status:
                continue
            if owner is not None and task.owner != owner:
                continue
            if blocked is not None and self._is_blocked(task, status_by_id) != blocked:
                continue
            selected.append(task)
        return selected

    # -- the atomic claim ---------------------------------------------------

    async def claim_task(self, task_id: str, owner: str) -> ClaimResult:
        """Atomically claim an open, unblocked task for ``owner``.

        THE load-bearing compare-and-set: the eligibility check (status ``open``
        ∧ unowned ∧ not superseded ∧ every blocker terminal) and the mutation
        (owner / ``claimed`` / ``claimed_at = time::now()``) are decided inside
        ONE ``BEGIN … COMMIT`` (see :meth:`_claim_fragment`). The blocker
        statuses are read INSIDE that transaction (a LET-bound subquery), so the
        decision and the write are transactionally consistent; two genuinely
        concurrent racers are serialised by
        :func:`~loremaster.store._txn.execute_transaction`'s write-write conflict
        retry, and the ``WHERE status = 'open'`` compare-and-set handles the
        sequential case — exactly one racer ever wins. Victory is read back from
        OWNER IDENTITY ALONE (``owner`` is written only by this CAS, so it is
        unforgeable) — never a status re-check, which would be a TOCTOU against a
        concurrent legal transition off ``claimed``. A losing claim writes
        NOTHING and is a RESULT (``claimed=False`` + the current state naming the
        holder), never an exception.

        Args:
            task_id: The opaque id of the task to claim.
            owner: The identity attempting to claim the task.

        Returns:
            The :class:`ClaimResult` of this attempt.

        Raises:
            TaskNotFoundError: No task with ``task_id`` exists.
        """
        # Existence + the (immutable) dependency list. ``blocked_by`` never
        # changes after creation, so reading it here is consistent; the blocker
        # STATUSES are read inside the claim transaction, not here.
        row = await self._select_row(task_id)
        if row is None:
            raise TaskNotFoundError(f"no task with id {task_id!r}")
        blocked_by = [str(blocker) for blocker in (row.get(_COL_BLOCKED_BY) or ())]

        await self._apply([self._claim_fragment(task_id, owner, blocked_by)])

        # The winner is decided by OWNER IDENTITY ALONE on the post-CAS read:
        # ``owner`` is written solely by the guarded claim CAS (from ``NONE``,
        # under the ``owner IS NONE`` guard), so exactly one claimant can ever
        # equal it — it is unforgeable. Any extra status/claimed_at freshness
        # condition would be a re-read TOCTOU: a concurrent legal
        # ``claimed -> in_progress`` transition (or a ``blocked -> open`` release
        # of a DIFFERENT racer) between the CAS commit and this read could flip a
        # genuine winner's status away from ``claimed`` and wrongly report a loss.
        updated = await self._get_or_raise(task_id)
        won = updated.owner == owner
        return ClaimResult(claimed=won, task=updated)

    @staticmethod
    def _claim_fragment(task_id: str, owner: str, blocked_by: list[str]) -> TxnFragment:
        """The atomic-claim fragment: LET-resolve blockers, then the guarded CAS.

        ``$clm_resolved`` binds the blocker record-ids that have reached a
        terminal status (read inside the transaction, so consistent with the
        mutation). The UPDATE mutates ONLY when the row is still open, unowned,
        not superseded, AND every blocker resolved — expressed as
        ``array::len(blocked_by) = array::len($clm_resolved)``: a never-minted or
        still-open blocker is simply absent from the resolved list, so the counts
        differ and the claim fails CLOSED. A failed guard matches zero rows and
        writes nothing.
        """
        resolve_blockers = (
            f"LET ${_CLAIM_RESOLVED_VAR} = "
            f"(SELECT VALUE record::id({_ID_KEY}) FROM {TASK_TABLE} "
            f"WHERE record::id({_ID_KEY}) IN ${_CLAIM_BLOCKED_BY_PARAM} "
            f"AND {_COL_STATUS} IN ${_CLAIM_TERMINAL_PARAM})"
        )
        guarded_claim = (
            f"UPDATE type::record('{TASK_TABLE}', ${_CLAIM_ID_PARAM}) SET "
            f"{_COL_OWNER} = ${_CLAIM_OWNER_PARAM}, "
            f"{_COL_STATUS} = ${_CLAIM_CLAIMED_PARAM}, "
            f"{_COL_CLAIMED_AT} = time::now() "
            f"WHERE {_COL_STATUS} = ${_CLAIM_OPEN_PARAM} "
            f"AND {_COL_OWNER} IS NONE "
            f"AND {_COL_SUPERSEDED_BY} IS NONE "
            f"AND array::len({_COL_BLOCKED_BY}) = array::len(${_CLAIM_RESOLVED_VAR})"
        )
        return TxnFragment(
            statements=[resolve_blockers, guarded_claim],
            params={
                _CLAIM_ID_PARAM: task_id,
                _CLAIM_OWNER_PARAM: owner,
                _CLAIM_BLOCKED_BY_PARAM: blocked_by,
                # Sorted so the bound list is deterministic; membership is
                # order-insensitive regardless.
                _CLAIM_TERMINAL_PARAM: sorted(TERMINAL_STATUSES),
                _CLAIM_OPEN_PARAM: STATUS_OPEN,
                _CLAIM_CLAIMED_PARAM: STATUS_CLAIMED,
            },
        )

    # -- state machine ------------------------------------------------------

    async def transition(self, task_id: str, status: str, *, actor: str) -> Task:
        """Drive a task through a legal state-machine edge.

        Validates the target and the edge BEFORE any write: a superseded task
        refuses ALL transitions; a target outside the six-status vocabulary or a
        ``(from, to)`` pair not in :data:`LEGAL_TRANSITIONS` raises
        :class:`IllegalTransitionError` naming BOTH states and leaves the row
        untouched. A legal transition stamps ``actor`` into ``provenance``;
        re-entering ``open`` (the ``blocked -> open`` release edge) clears
        ``owner`` / ``claimed_at`` so the row is genuinely re-claimable.

        The write is a guarded, THROW-on-zero-rows compare-and-set (see
        :meth:`_transition_fragment`): a concurrent writer that already moved
        the row away from the state THIS call's pre-read saw — to ANY other
        status, including this call's OWN target — makes the transaction roll
        back, which is ALWAYS detected here (never silently treated as success,
        even when the concurrent winner happened to reach the same target).

        Args:
            task_id: The opaque id of the task to transition.
            status: The target status; must be a legal edge from the task's
                current status (``open -> claimed`` is reachable ONLY through
                :meth:`claim_task`, never here).
            actor: The identity performing the transition, recorded in
                ``provenance``.

        Returns:
            The task's updated state.

        Raises:
            TaskNotFoundError: No task with ``task_id`` exists.
            IllegalTransitionError: ``status`` is not a legal edge from the
                task's current status (or the task is superseded), OR this
                call lost a concurrent race to transition the same row.
        """
        row = await self._select_row(task_id)
        if row is None:
            raise TaskNotFoundError(f"no task with id {task_id!r}")
        current = str(row.get(_COL_STATUS))
        superseded_by = row.get(_COL_SUPERSEDED_BY)
        self._validate_transition(task_id, current, status, superseded_by)

        now = datetime.now(UTC)
        event = {
            _PROV_ACTOR: actor,
            _PROV_ACTION: _ACTION_TRANSITION,
            _PROV_TO: status,
            _PROV_AT: now.isoformat(),
        }
        release = status == STATUS_OPEN
        try:
            # The write is a guarded compare-and-set inside ONE transaction: it
            # mutates ONLY while the row is STILL in the exact state the
            # pre-read saw (``status = current``) and un-superseded, and the
            # guard's THROW (see ``_transition_fragment``) turns a zero-row CAS
            # into a rolled-back ``SurrealStoreError`` — never a silent no-op —
            # so a concurrent writer that already drove the row to ANY other
            # status (including, crucially, THIS call's own target) is ALWAYS
            # detected, never masked as success.
            await self._apply(
                [self._transition_fragment(task_id, status, current, event, release)]
            )
        except SurrealConnectionError:
            # A genuine transport fault — never a lost race; propagate untouched
            # (must not be masked as an illegal-transition rejection).
            raise
        except SurrealStoreError as error:
            # The transaction rolled back: this call's CAS matched zero rows,
            # meaning a concurrent writer committed first. Re-validate from the
            # FRESH state so the raised error names BOTH the (now-current) state
            # and the refused target — e.g. a same-target race where the winner
            # already drove ``in_progress -> done`` makes this call's own
            # ``in_progress -> done`` request into the illegal ``done -> done``
            # self-edge (the audit-#1 false-success this guard fixes). A
            # vanished row (the ledger never deletes, so unreachable in
            # practice) still raises typed ``TaskNotFoundError``.
            fresh = await self._select_row(task_id)
            if fresh is None:
                raise TaskNotFoundError(f"no task with id {task_id!r}") from error
            fresh_status = str(fresh.get(_COL_STATUS))
            # Refuse from the FRESH edge when it is itself illegal (the common
            # case, e.g. the done -> done self-edge above).
            self._validate_transition(
                task_id, fresh_status, status, fresh.get(_COL_SUPERSEDED_BY)
            )
            # The fresh edge is somehow legal (a benign concurrent reorder, not
            # exercised by the pins) — still refuse: this call's CAS never
            # landed, so it did not perform the transition it promised.
            raise IllegalTransitionError(
                f"lost a concurrent transition race for task {task_id!r}: the status "
                f"moved to {fresh_status!r} before this {current!r} -> {status!r} "
                f"transition could apply"
            ) from error

        updated = await self._select_row(task_id)
        if updated is None:
            raise TaskNotFoundError(f"no task with id {task_id!r}")
        return self._row_to_task(updated)

    @staticmethod
    def _transition_fragment(
        task_id: str,
        target: str,
        expected_from: str,
        event: dict[str, Any],
        release: bool,
    ) -> TxnFragment:
        """The guarded-CAS transition fragment: LET-bind, THROW on zero rows.

        Mirrors :meth:`_supersede_fragment`'s shape: a guarded ``UPDATE`` binds
        its affected rows to ``$tr_updated`` — mutating ONLY while the row is
        STILL in ``expected_from`` and un-superseded — and
        ``IF array::len($tr_updated) == 0 { THROW … }`` rolls the WHOLE
        transaction back the instant a concurrent writer already moved the row
        away, so a zero-row CAS is ALWAYS a typed, detectable rollback — never a
        silent no-op a caller could mistake for success (the same-target race a
        bare post-CAS ``status`` re-read cannot distinguish from a genuine win).
        The new provenance EVENT is appended SERVER-SIDE
        (``provenance.events += [$tr_event]``) rather than written as a whole
        Python-merged object, so a concurrent :meth:`supersede_task` committing
        against the SAME row (a DIFFERENT guard column — ``superseded_by``, not
        ``status``) can never clobber this call's event, or vice versa.
        ``release`` (the ``blocked -> open`` edge) additionally clears
        ``owner``/``claimed_at`` so the released row is genuinely re-claimable.
        """
        set_parts = [
            f"{_COL_STATUS} = ${_TRANSITION_STATUS_PARAM}",
            f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [${_TRANSITION_EVENT_PARAM}]",
        ]
        if release:
            # The ONLY ways into ``open`` are creation and this release edge; a
            # released task must be unowned/unclaimed for the claim CAS (which
            # checks ``owner IS NONE`` alongside ``status = open``) to see it.
            set_parts.append(f"{_COL_OWNER} = NONE")
            set_parts.append(f"{_COL_CLAIMED_AT} = NONE")
        guarded_transition = (
            f"LET ${_TRANSITION_UPDATED_VAR} = (UPDATE "
            f"type::record('{TASK_TABLE}', ${_TRANSITION_ID_PARAM}) SET "
            f"{', '.join(set_parts)} "
            f"WHERE {_COL_STATUS} = ${_TRANSITION_EXPECTED_FROM_PARAM} "
            f"AND {_COL_SUPERSEDED_BY} IS NONE)"
        )
        guard_updated = (
            f"IF array::len(${_TRANSITION_UPDATED_VAR}) == 0 "
            f"{{ THROW '{_TRANSITION_ALREADY_MESSAGE}' }}"
        )
        return TxnFragment(
            statements=[guarded_transition, guard_updated],
            params={
                _TRANSITION_ID_PARAM: task_id,
                _TRANSITION_STATUS_PARAM: target,
                _TRANSITION_EVENT_PARAM: event,
                _TRANSITION_EXPECTED_FROM_PARAM: expected_from,
            },
        )

    @staticmethod
    def _validate_transition(
        task_id: str, current: str, target: str, superseded_by: Any
    ) -> None:
        """Refuse an illegal transition (typed, naming both states), else pass.

        Order (most-terminal first): a superseded row refuses everything; a
        target outside the vocabulary is not a legal value; a ``(current,
        target)`` pair absent from :data:`LEGAL_TRANSITIONS` is an illegal edge.

        Raises:
            IllegalTransitionError: Any of the three refusals above — the message
                always names both ``current`` and ``target`` so a caller/operator
                can see exactly what was refused.
        """
        if superseded_by is not None:
            raise IllegalTransitionError(
                f"task {task_id!r} is superseded and cannot transition "
                f"from {current!r} to {target!r}"
            )
        if target not in TASK_STATUSES:
            raise IllegalTransitionError(
                f"cannot transition task {task_id!r} from {current!r} to {target!r}: "
                f"{target!r} is not one of the valid statuses {sorted(TASK_STATUSES)}"
            )
        if (current, target) not in LEGAL_TRANSITIONS:
            raise IllegalTransitionError(
                f"illegal transition from {current!r} to {target!r} for task {task_id!r}: "
                f"not a legal state-machine edge"
            )

    # -- supersession -------------------------------------------------------

    async def supersede_task(
        self,
        task_id: str,
        *,
        subject: str,
        description: str,
        created_by: str,
    ) -> str:
        """Reframe a task: create a fresh open successor, stamp the old row.

        The successor CREATE and the old-row stamp ride ONE ``BEGIN … COMMIT``
        (see :meth:`_supersede_fragment`): a fresh ``open`` / unowned successor is
        CREATEd AND the old row is stamped ``superseded_by = <new id>`` (with a
        supersede event appended SERVER-SIDE to its provenance). The stamp is a
        compare-and-set (``WHERE superseded_by IS NONE``) and the CREATE is
        conditional on it, so EXACTLY ONE successor is ever minted even under a
        concurrent double supersede — the loser's whole transaction rolls back
        (no orphan) and surfaces as :class:`IllegalTransitionError`. The old row
        is KEPT (never deleted) so its history survives; a superseded task is
        terminal-like — it can no longer be claimed (the claim CAS guards on
        ``superseded_by IS NONE``), transitioned (:meth:`_validate_transition`
        refuses it), or superseded again.

        Args:
            task_id: The opaque id of the task being superseded.
            subject: The successor task's short human-readable title.
            description: The successor task's longer free-text description.
            created_by: The identity of the caller performing the supersession.

        Returns:
            The newly created successor task's opaque id.

        Raises:
            TaskNotFoundError: No task with ``task_id`` exists.
            IllegalTransitionError: The task is ALREADY superseded (sequentially,
                or as the loser of a concurrent double supersede).
        """
        row = await self._select_row(task_id)
        if row is None:
            raise TaskNotFoundError(f"no task with id {task_id!r}")
        # Sequential guard: a superseded task is terminal-like (exactly as it
        # refuses transitions), so a second supersede is refused up front. The
        # RACING double-supersede is caught transactionally below (the guarded
        # stamp + IF/THROW), not here — this pre-read only fast-fails the already
        # -settled sequential case.
        if row.get(_COL_SUPERSEDED_BY) is not None:
            raise IllegalTransitionError(
                f"task {task_id!r} is already superseded by "
                f"{row.get(_COL_SUPERSEDED_BY)!r} and cannot be superseded again"
            )

        new_id = uuid4().hex
        now = datetime.now(UTC)
        content = self._new_task_content(subject, description, None, created_by, now)
        event = {
            _PROV_ACTOR: created_by,
            _PROV_ACTION: _ACTION_SUPERSEDE,
            _PROV_SUCCESSOR: new_id,
            _PROV_AT: now.isoformat(),
        }
        try:
            await self._apply(
                [self._supersede_fragment(task_id, new_id, content, event)]
            )
        except SurrealConnectionError:
            # A genuine transport fault — never a lost race; propagate untouched
            # (must not be masked as an already-superseded rejection).
            raise
        except SurrealStoreError as error:
            # The transaction rolled back. The in-contract cause is the guarded
            # stamp matching zero rows (a concurrent supersede won the race and
            # stamped the old row first), whose IF/THROW aborts the WHOLE txn so
            # NO orphan successor is left behind. Confirm the row is now
            # superseded by someone else and surface the decided lost-race
            # semantics; anything else is a genuine store fault, re-raised as-is.
            settled = await self._select_row(task_id)
            if settled is not None and settled.get(_COL_SUPERSEDED_BY) is not None:
                raise IllegalTransitionError(
                    f"task {task_id!r} is already superseded by "
                    f"{settled.get(_COL_SUPERSEDED_BY)!r} and cannot be superseded again"
                ) from error
            raise
        return new_id

    @staticmethod
    def _supersede_fragment(
        old_id: str, new_id: str, content: dict[str, Any], event: dict[str, Any]
    ) -> TxnFragment:
        """The supersede fragment: guarded stamp-first, THROW-guard, then CREATE.

        THREE ordered statements, one transaction, exactly-ONE-successor:

        1. a guarded ``UPDATE`` that stamps ``superseded_by`` ONLY while the old
           row is STILL ``superseded_by IS NONE`` (the CAS) and appends the new
           supersede EVENT server-side (``provenance.events += [$sup_event]`` —
           never a whole Python-merged provenance object, so a concurrent
           :meth:`transition` committing against the SAME row via its OWN,
           DIFFERENT guard column (``status``) can never clobber this event),
           binding its result rows to ``$sup_stamped``;
        2. ``IF array::len($sup_stamped) == 0 { THROW … }`` — a zero-row stamp
           (a concurrent supersede already won) THROWs, which rolls the WHOLE
           transaction back server-side so statement 3 never runs;
        3. ``CREATE`` the fresh open successor.

        So a raced double-supersede yields ONE successor + one rolled-back loser
        (surfaced as ``SurrealStoreError`` the caller maps to
        ``IllegalTransitionError``) + ZERO orphan rows — the CREATE can never
        outlive a stamp that did not land.
        """
        stamp_old = (
            f"LET ${_SUPERSEDE_STAMPED_VAR} = (UPDATE "
            f"type::record('{TASK_TABLE}', ${_SUPERSEDE_OLD_ID_PARAM}) SET "
            f"{_COL_SUPERSEDED_BY} = ${_SUPERSEDE_NEW_ID_PARAM}, "
            f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [${_SUPERSEDE_EVENT_PARAM}] "
            f"WHERE {_COL_SUPERSEDED_BY} IS NONE)"
        )
        guard_stamped = (
            f"IF array::len(${_SUPERSEDE_STAMPED_VAR}) == 0 "
            f"{{ THROW '{_SUPERSEDE_ALREADY_MESSAGE}' }}"
        )
        create_successor = (
            f"CREATE type::record('{TASK_TABLE}', ${_SUPERSEDE_NEW_ID_PARAM}) "
            f"CONTENT ${_SUPERSEDE_CONTENT_PARAM}"
        )
        return TxnFragment(
            statements=[stamp_old, guard_stamped, create_successor],
            params={
                _SUPERSEDE_NEW_ID_PARAM: new_id,
                _SUPERSEDE_CONTENT_PARAM: content,
                _SUPERSEDE_OLD_ID_PARAM: old_id,
                _SUPERSEDE_EVENT_PARAM: event,
            },
        )

    # -- write helpers ------------------------------------------------------

    @staticmethod
    def _new_task_content(
        subject: str,
        description: str,
        blocked_by: list[str] | None,
        created_by: str,
        now: datetime,
    ) -> dict[str, Any]:
        """Shape a fresh ``task`` row's CONTENT (create + supersede-successor share it).

        Sets every REQUIRED column to the open/unowned birth state; the option
        columns not set here (``owner`` / ``claimed_at`` / ``superseded_by``)
        default to ``NONE`` on the SCHEMAFULL table (decoding back to ``None``).
        ``provenance`` records ``created_by`` + a tz-aware UTC ISO stamp and opens
        an empty append-only ``events`` log. ``blocked_by`` is deduped
        (order-preserving) so a duplicate dependency id never double-counts.
        """
        return {
            _COL_SUBJECT: subject,
            _COL_DESCRIPTION: description,
            _COL_STATUS: STATUS_OPEN,
            # ``blocked_by`` is a SET of dependencies: a DUPLICATE id must not
            # double-count against the claim gate's ``array::len`` CAS (which
            # compares against the DISTINCT resolved-blocker set), so it is
            # deduped (order-preserving) at birth — the single normalisation that
            # keeps the stored row, the claim gate and ``query_tasks``' partition
            # in agreement BY CONSTRUCTION.
            _COL_BLOCKED_BY: list(dict.fromkeys(blocked_by or ())),
            _COL_PROVENANCE: {
                _PROV_CREATED_BY: created_by,
                _PROV_CREATED_AT: now.isoformat(),
                _PROV_EVENTS: [],
            },
            _COL_CREATED_AT: now,
        }

    # -- reads / mapping ----------------------------------------------------

    async def _select_row(self, task_id: str) -> dict[str, Any] | None:
        """Return the raw ``task`` row dict for ``task_id``, or ``None`` if absent."""
        rows = self._as_rows(
            await self._query(
                f"SELECT * FROM type::record('{TASK_TABLE}', ${_ROW_ID_PARAM})",
                {_ROW_ID_PARAM: task_id},
            )
        )
        return rows[0] if rows else None

    async def _get_or_raise(self, task_id: str) -> Task:
        """Fetch ``task_id`` as a :class:`Task`, or raise :class:`TaskNotFoundError`."""
        row = await self._select_row(task_id)
        if row is None:
            raise TaskNotFoundError(f"no task with id {task_id!r}")
        return self._row_to_task(row)

    def _row_to_task(self, row: dict[str, Any]) -> Task:
        """Map a raw ``task`` row into a FRESH :class:`Task` value object.

        Never returns the raw row: the ``RecordID`` is reduced to its bare
        opaque string, both datetimes are normalised to tz-aware UTC (the
        fleet-comparable anchor the contract requires), and the option columns
        decode back to ``None``.
        """
        return Task(
            id=self._bare_id(row.get(_ID_KEY)),
            subject=str(row.get(_COL_SUBJECT, "")),
            description=str(row.get(_COL_DESCRIPTION, "")),
            status=cast(TaskStatus, row.get(_COL_STATUS)),
            owner=row.get(_COL_OWNER),
            claimed_at=self._to_aware_utc(row.get(_COL_CLAIMED_AT)),
            blocked_by=[str(blocker) for blocker in (row.get(_COL_BLOCKED_BY) or ())],
            provenance=dict(row.get(_COL_PROVENANCE) or {}),
            superseded_by=row.get(_COL_SUPERSEDED_BY),
            created_at=self._require_aware_utc(row.get(_COL_CREATED_AT)),
        )

    def _is_blocked(self, task: Task, status_by_id: dict[str, str]) -> bool:
        """Whether ``task`` is genuinely blocked: fail-closed on EVERY entry.

        A blocker resolves once its status is terminal (``done`` / ``wontfix``).
        A ``blocked_by`` entry naming an id absent from ``status_by_id`` (never
        minted) counts as UNRESOLVED — the same fail-closed default the atomic
        claim's ``array::len`` guard applies server-side, so the query partition
        and the claim gate can never disagree.
        """
        for blocker_id in task.blocked_by:
            blocker_status = status_by_id.get(blocker_id)
            if blocker_status is None or blocker_status not in TERMINAL_STATUSES:
                return True
        return False

    # -- result narrowing / normalisation -----------------------------------

    @staticmethod
    def _as_rows(result: Any) -> list[dict[str, Any]]:
        """Narrow a ``SELECT`` result to its list of dict rows."""
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    def _require_aware_utc(self, value: Any) -> datetime:
        """Normalise a REQUIRED datetime column to tz-aware UTC, refusing a bad value.

        ``created_at`` is a non-``option`` schema column the ledger always sets,
        so a faithful row always carries a real datetime; a missing/uncoercible
        one is a corrupt row, refused LOUDLY rather than silently coerced.

        Raises:
            SurrealStoreError: The value is missing or cannot be read as a datetime.
        """
        coerced = self._to_aware_utc(value)
        if coerced is None:
            raise SurrealStoreError(
                f"task row column {_COL_CREATED_AT!r} is missing or not a datetime "
                f"(got {type(value).__name__})"
            )
        return coerced

    @staticmethod
    def _to_aware_utc(value: Any) -> datetime | None:
        """Coerce a stored datetime into a tz-aware UTC datetime (or ``None``).

        The SDK's CBOR decoder returns tz-aware datetimes, but a naive datetime
        or an ISO-string/wrapper shape is normalised defensively so
        ``Task.created_at`` / ``Task.claimed_at`` are ALWAYS tz-aware (a naive
        stamp is the classic wrong-anchor bug for a value fleet agents in
        different timezones compare). ``None`` (an unset option column) passes
        through as ``None``.
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            aware = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
            return aware.astimezone(UTC)
        # An ISO-string / wrapper fallback (``str()`` covers the SDK's
        # IsoDateTimeWrapper, whose repr is the ISO-8601 text).
        text = str(value).replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        aware = parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
        return aware.astimezone(UTC)

    @staticmethod
    def _bare_id(raw: Any) -> str:
        """Return the BARE task id — no ``task:`` record-table prefix.

        The API speaks bare ``str`` everywhere because the SDK's ``RecordID`` is
        unhashable (it must work as a dict key / set member); this reduces a
        ``RecordID`` (or a ``table:id`` string) to just its opaque id component.
        """
        if isinstance(raw, RecordID):
            return str(raw.id)
        text = str(raw)
        if _TABLE_SEPARATOR in text:
            return text.split(_TABLE_SEPARATOR, 1)[1]
        return text
