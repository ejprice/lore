"""The durable, fleet-visible FINDING LEDGER (lore v2 P8b findings surface).

:class:`FindingLedger` is the friction/finding coordination primitive: a SurrealDB
table of findings the fleet can FILE (:meth:`~FindingLedger.report` — minting a
race-safe, human-addressable consecutive NUMBER), browse in order
(:meth:`~FindingLedger.query` — ordered by ``number`` ASC), address by that stable
number OR by opaque id (:meth:`~FindingLedger.get`), follow a supersedes chain
forward to its head (:meth:`~FindingLedger.chain_head`), and drive through a small
review state machine (:meth:`~FindingLedger.acknowledge` /
:meth:`~FindingLedger.resolve` / :meth:`~FindingLedger.wontfix`). It is the
first-class home for the ``kind="friction"`` records: the repo-root
``FRICTION.md`` file that used to hold them was migrated into this ledger as
rows #14-#36 and retired on 2026-07-06, giving them the four affordances the
di-scout entry named: enumerate-in-order, follow-the-supersedes-chain-to-its-head,
address-by-a-stable-number, and reviewable export.

It rides the SAME store machinery :mod:`loremaster.tasks` uses:

* one lazily-opened, signed-in WS connection, self-healed on a mid-life transport
  failure (a dropped handle so the next call reconnects), reusing the shared
  transaction / error-classification seams in :mod:`loremaster.store._txn` — a
  transport fault surfaces as
  :class:`~loremaster.store._txn.SurrealConnectionError`, a domain rejection as
  :class:`~loremaster.store._txn.SurrealStoreError`, never a raw engine string;
* every mutation rides :func:`~loremaster.store._txn.compose` +
  :func:`~loremaster.store._txn.execute_transaction` — a single ``BEGIN … COMMIT``
  with per-statement verification and bounded optimistic-concurrency retry.

THE load-bearing race-safe primitive is the ``number`` mint: :meth:`report` bumps
a single ``finding_counter`` row (``next += 1``) and CREATEs the finding in ONE
transaction, so two genuinely concurrent reporters contend on that ONE row, the
shared write-write conflict retry serialises them, and the ``UNIQUE`` index on
``finding.number`` is the backstop — the result is gapless, distinct, consecutive
numbers with zero failures. Every ``transition`` and the ``supersedes`` link ride
the same guarded-CAS discipline the task ledger's own state machine does.

The public surface:

    Finding:                               # a value object (pydantic model)
        id: str                            # OPAQUE — never a raw RecordID
        number: int                        # STABLE, human-addressable (#1, #2, …)
        kind: str
        status: Literal[open|acknowledged|resolved|wontfix]
        subject: str
        body: str
        area: str
        category: str
        created_by: str
        created_at: datetime               # tz-aware UTC
        supersedes: str | None             # opaque id of the finding this supersedes
        provenance: dict                   # who created/changed + timestamps

    ReportResult:
        id: str
        number: int

    ChainHead:                             # the fork-aware supersedes-chain head
        finding: Finding                   # head of the lowest-numbered branch
        forked: bool                       # did the chain fork off the walked path?
        fork_successor_numbers: list[int]  # the unwalked sibling arms' numbers

    FindingLedger(*, url, namespace, database, user, password):
        async ensure_ready() -> None
        async close() -> None
        async report(subject, body, *, kind="friction", area, category, created_by,
                     supersedes=None) -> ReportResult
        async get(id_or_number) -> Finding
        async query(*, status=None, kind=None, area=None, limit=…) -> list[Finding]
        async chain_head(id_or_number) -> ChainHead   # head + fork-surfacing marks
        async acknowledge(id_or_number, actor) -> Finding
        async resolve(id_or_number, actor, note=None) -> Finding
        async wontfix(id_or_number, actor, note=None) -> Finding

    Exceptions: FindingLedgerError(RuntimeError);
                FindingNotFoundError(FindingLedgerError);
                IllegalTransitionError(FindingLedgerError);
                FindingChainCycleError(FindingLedgerError).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, SecretStr
from surrealdb import AsyncSurreal, RecordID

from loremaster.render import render_attributed
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
    FINDING_COUNTER_SINGLETON_ID,
    FINDING_COUNTER_TABLE,
    FINDING_TABLE,
    generate_finding_ddl,
)

logger = logging.getLogger(__name__)

# The four-status review vocabulary this contract decides (mirrors the statuses the
# schema's ``_FINDING_STATUSES`` and the test module's ``STATUS_*`` constants name).
# A ``Literal`` alias so :class:`Finding.status` is typed against the closed set the
# state machine enforces, without hardcoding the set a second time.
FindingStatus = Literal["open", "acknowledged", "resolved", "wontfix"]

# --- the four statuses, as named constants (never bare literals in logic) -----
STATUS_OPEN: FindingStatus = "open"
STATUS_ACKNOWLEDGED: FindingStatus = "acknowledged"
STATUS_RESOLVED: FindingStatus = "resolved"
STATUS_WONTFIX: FindingStatus = "wontfix"

# The closed status domain — membership is what makes a transition target a legal
# *value* at all (a garbage target is refused before the edge check).
FINDING_STATUSES: frozenset[str] = frozenset(
    {STATUS_OPEN, STATUS_ACKNOWLEDGED, STATUS_RESOLVED, STATUS_WONTFIX}
)

# The two TERMINAL statuses — no transition may leave them.
TERMINAL_STATUSES: frozenset[str] = frozenset({STATUS_RESOLVED, STATUS_WONTFIX})

# The full legal transition matrix (the state machine): every ``(from, to)`` edge
# NOT in this frozen set is illegal — including every no-op self-edge and every edge
# out of a terminal status. A finding is acknowledged only from ``open``; resolved
# or wontfixed from EITHER ``open`` or ``acknowledged``.
LEGAL_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        (STATUS_OPEN, STATUS_ACKNOWLEDGED),
        (STATUS_OPEN, STATUS_RESOLVED),
        (STATUS_OPEN, STATUS_WONTFIX),
        (STATUS_ACKNOWLEDGED, STATUS_RESOLVED),
        (STATUS_ACKNOWLEDGED, STATUS_WONTFIX),
    }
)

# The default finding kind — ``friction`` is the first first-class kind (the domain
# stays open for P8c's drift auto-file to add kinds).
DEFAULT_KIND = "friction"

# The default cap on a :meth:`FindingLedger.query` result. The ordered browse is a
# bounded read; a caller wanting the whole log passes a larger explicit limit.
DEFAULT_QUERY_LIMIT = 100

# The ``finding`` table columns the ledger reads/writes. Named once each so a rename
# is a single edit, never a hand-copied literal drifting between the write content,
# the guarded UPDATEs and the row → value-object mapping.
_COL_NUMBER = "number"
_COL_KIND = "kind"
_COL_STATUS = "status"
_COL_SUBJECT = "subject"
_COL_BODY = "body"
_COL_AREA = "area"
_COL_CATEGORY = "category"
_COL_CREATED_BY = "created_by"
_COL_CREATED_AT = "created_at"
_COL_SUPERSEDES = "supersedes"
_COL_PROVENANCE = "provenance"

# The ``finding_counter`` row's single column (``next``) — the monotonic sequence.
_COL_NEXT = "next"

# The provenance blob's keys + the audit-event action name. ``provenance`` is a
# FLEXIBLE object: a ``created_by`` stamp + an append-only ``events`` log, each
# event naming its ``actor`` and ``action`` (and, for a resolve/wontfix, an optional
# ``note``) — mirrors the task ledger's chosen shape.
_PROV_CREATED_BY = "created_by"
_PROV_CREATED_AT = "created_at"
_PROV_EVENTS = "events"
_PROV_ACTOR = "actor"
_PROV_ACTION = "action"
_PROV_AT = "at"
_PROV_TO = "to"
_PROV_NOTE = "note"
_ACTION_TRANSITION = "transition"

# The record-id table separator and the
# row id key.
_TABLE_SEPARATOR = ":"
_ID_KEY = "id"

# The report transaction's bound-parameter names (the ``rep_`` prefix namespaces the
# composed fragment). ``$finding_seq`` (below) is a LET-bound scalar — the number the
# counter bump minted — consumed by the CREATE's CONTENT literal.
_REPORT_SEQ_VAR = "finding_seq"
_REPORT_ID_PARAM = "rep_id"
_REPORT_KIND_PARAM = "rep_kind"
_REPORT_STATUS_PARAM = "rep_status"
_REPORT_SUBJECT_PARAM = "rep_subject"
_REPORT_BODY_PARAM = "rep_body"
_REPORT_AREA_PARAM = "rep_area"
_REPORT_CATEGORY_PARAM = "rep_category"
_REPORT_CREATED_BY_PARAM = "rep_created_by"
_REPORT_CREATED_AT_PARAM = "rep_created_at"
_REPORT_PROVENANCE_PARAM = "rep_provenance"
_REPORT_SUPERSEDES_ID_PARAM = "rep_supersedes_id"

# The transition UPDATE's bound-parameter names (the ``tr_`` prefix).
_TRANSITION_ID_PARAM = "tr_id"
_TRANSITION_STATUS_PARAM = "tr_status"
_TRANSITION_EVENT_PARAM = "tr_event"
# The transition CAS's ``expected_from`` guard param — the exact status the pre-read
# saw; the guarded UPDATE mutates ONLY while the row is STILL in it.
_TRANSITION_EXPECTED_FROM_PARAM = "tr_expected_from"
# The LET-bound variable holding the guarded transition's result rows, and the FIXED
# message its zero-row guard THROWs (a constant, so the rolled-back rejection carries
# no interpolated data; it surfaces only server-side, mapped to
# :class:`IllegalTransitionError`). Mirrors the task ledger's transition CAS.
_TRANSITION_UPDATED_VAR = "tr_updated"
_TRANSITION_ALREADY_MESSAGE = "finding transition lost a concurrent compare-and-set"

# The query filter / limit bound-parameter names (the ``qry_`` prefix).
_QUERY_STATUS_PARAM = "qry_status"
_QUERY_KIND_PARAM = "qry_kind"
_QUERY_AREA_PARAM = "qry_area"

# The single-read select param names.
_ROW_ID_PARAM = "id"
_ROW_NUMBER_PARAM = "number"

# PKT-06 §1: ``filed_since``'s bound-parameter name and the field a
# ``SELECT count() … GROUP ALL`` result carries the total under (mirrors
# ``loremaster.tasks``'s / ``diff.py``'s own ``_COUNT_KEY`` idiom).
_FILED_SINCE_PARAM = "fs_since"
_COUNT_KEY = "count"

# The bounded number of supersedes-chain hops :meth:`FindingLedger.chain_head` will
# take before declaring a cycle — defense-in-depth ABOVE the primary visited-set
# cycle guard: even a pathological chain longer than every finding ever filed
# terminates loudly rather than walking forever.
_MAX_CHAIN_HOPS = 100_000


class Finding(BaseModel):
    """A single finding in the durable, fleet-visible finding ledger.

    Attributes:
        id: The finding's OPAQUE, hashable string id — never a raw SurrealDB
            ``RecordID``.
        number: The STABLE, human-addressable finding number (``#1``, ``#2``, …) —
            minted consecutively and never reused.
        kind: The finding kind (``"friction"`` is the first first-class kind).
        status: The finding's current state in the four-status review vocabulary.
        subject: The short human-readable title of the finding.
        body: The longer free-text description of the finding.
        area: The tool/subsystem the finding is about (e.g. ``"lore_impact"``).
        category: The finding category (e.g. ``"capability_gap"``).
        created_by: The identity that filed the finding.
        created_at: The tz-aware UTC timestamp the finding was filed at.
        supersedes: The opaque id of the finding this one reframes/supersedes, or
            ``None`` when it supersedes nothing.
        provenance: Who created/changed the finding and when, as a free-form dict.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    number: int
    kind: str
    status: FindingStatus
    subject: str
    body: str
    area: str
    category: str
    created_by: str
    created_at: datetime
    supersedes: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)


class FindingActivityWindow(BaseModel):
    """The rollup's leg-2 read: findings filed since a cursor.

    Attributes:
        rows: The matching findings, ordered by ``created_at`` ascending,
            capped at the caller's ``limit``.
        total: The HONEST total count of findings matching the window (may
            exceed ``len(rows)`` when ``limit`` truncated the result).
    """

    model_config = ConfigDict(extra="forbid")

    rows: list[Finding]
    total: int


class ReportResult(BaseModel):
    """The outcome of a :meth:`FindingLedger.report` — the new finding's addresses.

    Attributes:
        id: The freshly-minted OPAQUE finding id.
        number: The freshly-minted STABLE, human-addressable finding number.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    number: int


class ChainHead(BaseModel):
    """The result of walking a supersedes chain to its head — fork-aware.

    :meth:`FindingLedger.chain_head` walks successors FORWARD. The walk is
    DETERMINISTIC: at every hop it follows the LOWEST-numbered successor, so
    :attr:`finding` is always the head of the lowest-numbered branch. But a chain
    can FORK — two findings may each ``report(supersedes=X)`` the same original X
    (reachable through the public API, unlike a cycle) — and then the
    higher-numbered arm is NOT on the walked path. Rather than silently drop it
    (the old behaviour, which billed the lowest branch's head as "the newest
    record"), this result SURFACES the fork: :attr:`forked` flags it and
    :attr:`fork_successor_numbers` names the sibling successors the walk did not
    follow, so a consumer can walk them too.

    Attributes:
        finding: The head reached by the deterministic lowest-numbered walk — the
            terminal finding of the lowest-numbered branch. A finding nobody
            supersedes is its own head.
        forked: ``True`` when ANY hop on the walk had more than one successor, so
            :attr:`finding` is the head of the LOWEST-numbered branch only and at
            least one other (higher-numbered, newer) arm exists off the walked
            path. ``False`` for a linear chain or a lone finding.
        fork_successor_numbers: The STABLE numbers of the sibling successors the
            deterministic walk did NOT follow, ascending and de-duplicated — each
            the entry point of another branch (call :meth:`FindingLedger.chain_head`
            on it to reach that branch's own head). Empty when the chain did not
            fork.
    """

    model_config = ConfigDict(extra="forbid")

    finding: Finding
    forked: bool = False
    fork_successor_numbers: list[int] = Field(default_factory=list)


class FindingLedgerError(RuntimeError):
    """Base class for every error :class:`FindingLedger` raises."""


class FindingNotFoundError(FindingLedgerError):
    """Raised when a finding id/number does not resolve to any row in the ledger."""


class IllegalTransitionError(FindingLedgerError):
    """Raised when a requested status transition is not a legal state-machine edge."""


class FindingChainCycleError(FindingLedgerError):
    """Raised when a supersedes chain contains a cycle (corrupt data).

    :meth:`FindingLedger.chain_head` walks the supersedes chain forward; a cycle
    would loop forever, so it is detected (a revisited id, or an implausibly long
    walk) and surfaced as this typed error rather than hanging.
    """


class FindingLedger:
    """Durable, fleet-visible finding ledger over a single SurrealDB database.

    Speaks the four-status finding review vocabulary (see the module docstring)
    against a per-project SurrealDB ``finding`` table, mints OPAQUE ``uuid4`` string
    ids AND race-safe consecutive ``number`` s (via the ``finding_counter`` row),
    and rides the shared :mod:`loremaster.store._txn` transaction /
    error-classification seams so every mutation is atomic and every failure surfaces
    as a typed store error.

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
        # Guards the connect-time check-then-set so N concurrent first-callers never
        # each open their own underlying SDK connection (mirrors ``TaskLedger``).
        self._connect_lock = asyncio.Lock()

    # -- connection lifecycle ----------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking (mirrors :class:`~loremaster.tasks.TaskLedger`): the
        fast path never touches the lock. The session bootstrap is
        :func:`~loremaster.store._txn.bootstrap_session` — the ONE shared
        implementation every connection owner in the package calls
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
            if self._connection is not None:
                # A concurrent caller connected while this one waited; mypy can't
                # model the cross-coroutine mutation across the ``await`` above.
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
                # Close the half-open socket so a failed connect never leaks a
                # dangling connection, then surface a typed connection error.
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "finding.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect and apply the finding schema slice — idempotent and safe to re-run.

        Applies :func:`~loremaster.store.surreal_schema.generate_finding_ddl` (the
        ``finding`` table + its UNIQUE number / status indexes + the
        ``finding_counter`` sibling) inside ONE ``BEGIN … COMMIT`` via
        :func:`~loremaster.store._txn.execute_transaction`, which verifies EVERY
        statement's status (the SDK's plain ``query()`` inspects only the first).
        The DDL is a MIX (finding #107): the table and its indexes are ``IF NOT
        EXISTS``, so a second call neither raises nor wipes existing rows —
        every per-test fresh database depends on this — but every FIELD is
        ``DEFINE FIELD OVERWRITE`` (see :mod:`loremaster.store.surreal_schema`),
        so a field definition CHANGE still migrates a live store instead of
        silently no-op'ing against it.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: A DDL statement was rejected by the engine.
        """
        await self._ensure_connection()
        ddl = generate_finding_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("finding.schema.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any); tolerant of a never-connected ledger."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal).

        A compare-and-swap (mirrors :class:`~loremaster.tasks.TaskLedger`):
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
            logger.debug("finding.close.already_closed")

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
            noun="finding query",
            label="finding.query.rejected",
            statement=statement,
            params=params or {},
            logger=logger,
        )

    async def _apply(self, fragments: list[TxnFragment]) -> None:
        """Compose ``fragments`` into ONE transaction and run it atomically.

        Mirrors :meth:`~loremaster.tasks.TaskLedger._apply`: the composed
        ``BEGIN … COMMIT`` runs through
        :func:`~loremaster.store._txn.execute_transaction` (every statement's status
        verified, transport failure self-healed, retryable write-write conflict
        bounded-retried), so a report's counter bump and finding CREATE — or a
        transition's guarded CAS — either both land or neither does, and two racers
        can never both win.
        """
        statement_text, merged_params = compose(*fragments)
        await execute_transaction(
            statement_text,
            merged_params,
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )

    # -- report / read ------------------------------------------------------

    @staticmethod
    def _require_non_empty_area_category(area: str, category: str) -> None:
        """Refuse an empty / whitespace-only ``area`` or ``category`` before any I/O.

        The ledger-side guard mirroring the store's trim-aware ASSERT
        (audit-findings #2): an empty ``area``/``category`` names no real tool
        surface, so it is refused EARLY — before the counter bump / store
        round-trip — with a clean :class:`ValueError` (the same input-validation
        family :meth:`query`'s ``limit`` guard raises), rather than deferred to a
        laundered store ``ASSERT`` rejection. The schema ASSERT remains the
        store-side backstop for any non-ledger writer.

        Raises:
            ValueError: ``area`` or ``category`` is empty or whitespace-only.
        """
        for name, value in ((_COL_AREA, area), (_COL_CATEGORY, category)):
            if not value.strip():
                raise ValueError(
                    f"finding {name} must be a non-empty, non-whitespace string, "
                    f"got {value!r}"
                )

    async def report(
        self,
        subject: str,
        body: str,
        *,
        kind: str = DEFAULT_KIND,
        area: str,
        category: str,
        created_by: str,
        supersedes: int | str | None = None,
    ) -> ReportResult:
        """File a new finding, minting a race-safe consecutive ``number``.

        The finding starts ``open``, with ``created_by`` recorded in ``provenance``
        and a tz-aware UTC creation stamp. The ``number`` is minted INSIDE the same
        transaction as the CREATE by bumping the single ``finding_counter`` row, so
        two concurrent reporters contend on that one row and the shared write-write
        conflict retry serialises them into gapless consecutive numbers (the UNIQUE
        index on ``number`` is the backstop). When ``supersedes`` is given, the
        target finding must already exist (else :class:`FindingNotFoundError`) and
        the new finding records a REAL record link back to it.

        Args:
            subject: The short human-readable title of the finding.
            body: The longer free-text description of the finding.
            kind: The finding kind (defaults to ``"friction"``).
            area: The tool/subsystem the finding is about.
            category: The finding category.
            created_by: The identity filing the finding, recorded in ``provenance``.
            supersedes: An optional id OR number of an EXISTING finding this one
                reframes; the new finding links back to it.

        Returns:
            The :class:`ReportResult` naming the new finding's opaque id and stable
            number.

        Raises:
            ValueError: ``area`` or ``category`` is empty / whitespace-only.
            FindingNotFoundError: ``supersedes`` was given but names no finding.
        """
        self._require_non_empty_area_category(area, category)
        supersedes_id: str | None = None
        if supersedes is not None:
            target = await self._resolve_or_raise(supersedes)
            supersedes_id = self._bare_id(target.get(_ID_KEY))

        finding_id = uuid4().hex  # OPAQUE, non-sequential; never content-derived.
        now = datetime.now(UTC)
        provenance = {
            _PROV_CREATED_BY: created_by,
            _PROV_CREATED_AT: now.isoformat(),
            _PROV_EVENTS: [],
        }
        fragment = self._report_fragment(
            finding_id=finding_id,
            kind=kind,
            subject=subject,
            body=body,
            area=area,
            category=category,
            created_by=created_by,
            created_at=now,
            provenance=provenance,
            supersedes_id=supersedes_id,
        )
        await self._apply([fragment])
        row = await self._select_row_by_id(finding_id)
        if row is None:
            raise FindingLedgerError(
                f"finding {finding_id!r} vanished immediately after it was created"
            )
        return ReportResult(id=finding_id, number=int(row[_COL_NUMBER]))

    @staticmethod
    def _report_fragment(
        *,
        finding_id: str,
        kind: str,
        subject: str,
        body: str,
        area: str,
        category: str,
        created_by: str,
        created_at: datetime,
        provenance: dict[str, Any],
        supersedes_id: str | None,
    ) -> TxnFragment:
        """The report fragment: bump the counter, then CREATE referencing the number.

        Two ordered statements, one transaction:

        1. ``LET $finding_seq = (UPSERT finding_counter:singleton SET next += 1
           RETURN AFTER)[0].next`` — the race-safe mint; two concurrent reporters
           contend on this ONE row and the shared retry serialises them.
        2. ``CREATE … CONTENT { number: $finding_seq, … }`` — a CONTENT OBJECT
           literal (never ``SET``, so a future protected-key column can't break the
           write) referencing the freshly-minted number LET var plus the bound
           content params. ``supersedes`` is written as a REAL ``type::record`` link
           when given, or ``NONE`` when absent.
        """
        seq_bump = (
            f"LET ${_REPORT_SEQ_VAR} = (UPSERT "
            f"type::record('{FINDING_COUNTER_TABLE}', '{FINDING_COUNTER_SINGLETON_ID}') "
            f"SET {_COL_NEXT} += 1 RETURN AFTER)[0].{_COL_NEXT}"
        )
        content_fields = [
            f"{_COL_NUMBER}: ${_REPORT_SEQ_VAR}",
            f"{_COL_KIND}: ${_REPORT_KIND_PARAM}",
            f"{_COL_STATUS}: ${_REPORT_STATUS_PARAM}",
            f"{_COL_SUBJECT}: ${_REPORT_SUBJECT_PARAM}",
            f"{_COL_BODY}: ${_REPORT_BODY_PARAM}",
            f"{_COL_AREA}: ${_REPORT_AREA_PARAM}",
            f"{_COL_CATEGORY}: ${_REPORT_CATEGORY_PARAM}",
            f"{_COL_CREATED_BY}: ${_REPORT_CREATED_BY_PARAM}",
            f"{_COL_CREATED_AT}: ${_REPORT_CREATED_AT_PARAM}",
            f"{_COL_PROVENANCE}: ${_REPORT_PROVENANCE_PARAM}",
        ]
        params: dict[str, Any] = {
            _REPORT_ID_PARAM: finding_id,
            _REPORT_KIND_PARAM: kind,
            _REPORT_STATUS_PARAM: STATUS_OPEN,
            _REPORT_SUBJECT_PARAM: subject,
            _REPORT_BODY_PARAM: body,
            _REPORT_AREA_PARAM: area,
            _REPORT_CATEGORY_PARAM: category,
            _REPORT_CREATED_BY_PARAM: created_by,
            _REPORT_CREATED_AT_PARAM: created_at,
            _REPORT_PROVENANCE_PARAM: provenance,
        }
        if supersedes_id is not None:
            content_fields.append(
                f"{_COL_SUPERSEDES}: type::record('{FINDING_TABLE}', ${_REPORT_SUPERSEDES_ID_PARAM})"
            )
            params[_REPORT_SUPERSEDES_ID_PARAM] = supersedes_id
        else:
            content_fields.append(f"{_COL_SUPERSEDES}: NONE")
        create = (
            f"CREATE type::record('{FINDING_TABLE}', ${_REPORT_ID_PARAM}) "
            f"CONTENT {{ {', '.join(content_fields)} }}"
        )
        return TxnFragment(statements=[seq_bump, create], params=params)

    async def get(self, id_or_number: int | str) -> Finding:
        """Fetch a single finding, addressed by its stable number OR its opaque id.

        An ``int`` addresses by the human-addressable ``number``; anything else by
        the opaque id.

        Args:
            id_or_number: The finding's stable number (``int``) or opaque id (``str``).

        Returns:
            The matching :class:`Finding` (a FRESH value object, never a raw row).

        Raises:
            FindingNotFoundError: Nothing is addressed by ``id_or_number``.
        """
        return self._row_to_finding(await self._resolve_or_raise(id_or_number))

    async def query(
        self,
        *,
        status: str | None = None,
        kind: str | None = None,
        area: str | None = None,
        limit: int = DEFAULT_QUERY_LIMIT,
    ) -> list[Finding]:
        """Return findings matching every supplied filter, ordered by number ASC.

        The enumerate-in-order browse: exact ``status`` / ``kind`` / ``area``
        equality filters (AND-combined), ordered by the stable ``number`` ascending
        and capped at ``limit`` (so the head of the ordered log is the first
        ``limit`` findings).

        Args:
            status: When given, restrict to findings in this exact status.
            kind: When given, restrict to findings of this exact kind.
            area: When given, restrict to findings about this exact area.
            limit: The maximum number of findings to return (must be a positive int).

        Returns:
            The matching findings, ordered by number ascending (empty when nothing
            matches).

        Raises:
            ValueError: ``limit`` is not a positive integer.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"limit must be a positive integer, got {limit!r}")
        conditions: list[str] = []
        params: dict[str, Any] = {}
        if status is not None:
            conditions.append(f"{_COL_STATUS} = ${_QUERY_STATUS_PARAM}")
            params[_QUERY_STATUS_PARAM] = status
        if kind is not None:
            conditions.append(f"{_COL_KIND} = ${_QUERY_KIND_PARAM}")
            params[_QUERY_KIND_PARAM] = kind
        if area is not None:
            conditions.append(f"{_COL_AREA} = ${_QUERY_AREA_PARAM}")
            params[_QUERY_AREA_PARAM] = area
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        # ``limit`` is a validated positive int, so interpolating it is injection-safe
        # (SurrealDB's ``LIMIT`` wants a literal count, not a bound param here).
        statement = (
            f"SELECT * FROM {FINDING_TABLE}{where} ORDER BY {_COL_NUMBER} ASC LIMIT {limit}"
        )
        rows = self._as_rows(await self._query(statement, params))
        return [self._row_to_finding(row) for row in rows]

    async def filed_since(self, since: datetime, *, limit: int) -> FindingActivityWindow:
        """The rollup's leg-2 read: findings filed strictly after ``since``.

        Unlike the task ledger's ``updated_at`` (which starts ``None``), every
        finding always carries a ``created_at`` — filed-since has no
        "never appears" case. Ordered ``created_at`` ASC, capped at ``limit``,
        with an HONEST ``total`` (a second bounded ``SELECT count() … GROUP
        ALL`` — never a second unbounded scan) so a caller can tell a
        truncated window from an exhaustive one.

        Args:
            since: The EXCLUSIVE lower bound — only findings filed STRICTLY
                after this tz-aware UTC instant are returned.
            limit: The maximum number of rows to return (must be a positive int).

        Returns:
            The matching window: ``rows`` (ASC by ``created_at``, capped at
            ``limit``) and the honest ``total`` (``>= len(rows)``).

        Raises:
            ValueError: ``limit`` is not a positive integer.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"limit must be a positive integer, got {limit!r}")
        params: dict[str, Any] = {_FILED_SINCE_PARAM: since}
        rows_result = await self._query(
            f"SELECT * FROM {FINDING_TABLE} WHERE {_COL_CREATED_AT} > ${_FILED_SINCE_PARAM} "
            f"ORDER BY {_COL_CREATED_AT} ASC LIMIT {limit}",
            params,
        )
        rows = [self._row_to_finding(row) for row in self._as_rows(rows_result)]
        count_result = await self._query(
            f"SELECT count() FROM {FINDING_TABLE} WHERE {_COL_CREATED_AT} > "
            f"${_FILED_SINCE_PARAM} GROUP ALL",
            params,
        )
        return FindingActivityWindow(rows=rows, total=self._extract_group_count(count_result))

    async def chain_head(self, id_or_number: int | str) -> ChainHead:
        """Follow the supersedes chain FORWARD to its head, surfacing any fork.

        The successor of a finding X is a finding whose ``supersedes`` names X; the
        walk follows successors transitively until one has none — that terminal
        finding is the head. The walk is DETERMINISTIC: when a finding has MORE
        than one successor (a FORK — two findings each ``report(supersedes=X)`` the
        same original, reachable through the public API), it follows the
        LOWEST-numbered branch, and the returned :class:`ChainHead`'s
        :attr:`~ChainHead.forked` flag + :attr:`~ChainHead.fork_successor_numbers`
        surface the sibling arm(s) the walk did NOT follow — so a *higher-numbered*
        (newer) branch and its head are never silently dropped (audit-findings #1).
        A finding nobody supersedes is its OWN head. A cycle (corrupt data) is
        detected (a revisited id, or an implausibly long walk) and raised as
        :class:`FindingChainCycleError` rather than hung on.

        Args:
            id_or_number: Any finding in the chain, addressed by number or opaque id.

        Returns:
            A :class:`ChainHead` naming the head of the LOWEST-numbered branch and
            whether — and at which sibling numbers — the chain forked.

        Raises:
            FindingNotFoundError: Nothing is addressed by ``id_or_number``.
            FindingChainCycleError: The supersedes chain contains a cycle.
        """
        row = await self._resolve_or_raise(id_or_number)
        current_id = self._bare_id(row.get(_ID_KEY))
        visited = {current_id}
        # The numbers of every sibling successor the deterministic walk skipped —
        # a set (de-duped) surfaced sorted on the returned ChainHead.
        fork_successor_numbers: set[int] = set()
        for _ in range(_MAX_CHAIN_HOPS):
            successors = await self._select_successors(current_id)
            if not successors:
                return ChainHead(
                    finding=self._row_to_finding(row),
                    forked=bool(fork_successor_numbers),
                    fork_successor_numbers=sorted(fork_successor_numbers),
                )
            # ORDER BY number ASC: [0] is the lowest-numbered branch we walk; the
            # rest are the fork siblings we surface but do not follow.
            walked = successors[0]
            for sibling in successors[1:]:
                fork_successor_numbers.add(int(sibling[_COL_NUMBER]))
            successor_id = self._bare_id(walked.get(_ID_KEY))
            if successor_id in visited:
                raise FindingChainCycleError(
                    f"supersedes chain from finding {current_id!r} contains a cycle "
                    f"(revisited {successor_id!r}) — the finding data is corrupt"
                )
            visited.add(successor_id)
            row = walked
            current_id = successor_id
        raise FindingChainCycleError(
            f"supersedes chain from finding {self._bare_id(row.get(_ID_KEY))!r} exceeded "
            f"{_MAX_CHAIN_HOPS} hops without a head — the finding data is corrupt"
        )

    # -- state machine ------------------------------------------------------

    async def acknowledge(
        self, id_or_number: int | str, actor: str, note: str | None = None
    ) -> Finding:
        """Drive an ``open`` finding to ``acknowledged`` (a legal edge).

        Args:
            id_or_number: The finding to acknowledge (number or opaque id).
            actor: The identity performing the acknowledgement, recorded in
                ``provenance``.
            note: An optional free-text note recorded alongside the transition
                (PKT-06 §3 — mirrors ``resolve``/``wontfix``'s existing ``note``).

        Returns:
            The finding's updated state.

        Raises:
            FindingNotFoundError: Nothing is addressed by ``id_or_number``.
            IllegalTransitionError: The finding is not ``open`` (or lost a
                concurrent race).
        """
        return await self._transition(id_or_number, STATUS_ACKNOWLEDGED, actor, note)

    async def resolve(
        self, id_or_number: int | str, actor: str, note: str | None = None
    ) -> Finding:
        """Drive an ``open``/``acknowledged`` finding to ``resolved`` (terminal).

        Args:
            id_or_number: The finding to resolve (number or opaque id).
            actor: The identity resolving the finding, recorded in ``provenance``.
            note: An optional free-text note recorded alongside the transition.

        Returns:
            The finding's updated state.

        Raises:
            FindingNotFoundError: Nothing is addressed by ``id_or_number``.
            IllegalTransitionError: The finding is already terminal (or lost a
                concurrent race).
        """
        return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)

    async def wontfix(
        self, id_or_number: int | str, actor: str, note: str | None = None
    ) -> Finding:
        """Drive an ``open``/``acknowledged`` finding to ``wontfix`` (terminal).

        Args:
            id_or_number: The finding to close as wontfix (number or opaque id).
            actor: The identity closing the finding, recorded in ``provenance``.
            note: An optional free-text note recorded alongside the transition.

        Returns:
            The finding's updated state.

        Raises:
            FindingNotFoundError: Nothing is addressed by ``id_or_number``.
            IllegalTransitionError: The finding is already terminal (or lost a
                concurrent race).
        """
        return await self._transition(id_or_number, STATUS_WONTFIX, actor, note)

    async def _transition(
        self, id_or_number: int | str, target: str, actor: str, note: str | None
    ) -> Finding:
        """Drive a finding through a legal state-machine edge via a guarded CAS.

        Validates the edge BEFORE any write; a ``(from, target)`` pair not in
        :data:`LEGAL_TRANSITIONS` raises :class:`IllegalTransitionError` naming BOTH
        states and leaves the row untouched. A legal transition stamps ``actor`` (and
        any ``note``) into ``provenance`` via a guarded, THROW-on-zero-rows CAS: a
        concurrent writer that already moved the row away from the state THIS call's
        pre-read saw makes the transaction roll back, which is ALWAYS detected here
        (never silently treated as success, even when the concurrent winner reached
        the same target).
        """
        row = await self._resolve_or_raise(id_or_number)
        finding_id = self._bare_id(row.get(_ID_KEY))
        current = str(row.get(_COL_STATUS))
        self._validate_transition(finding_id, current, target)

        now = datetime.now(UTC)
        event: dict[str, Any] = {
            _PROV_ACTOR: actor,
            _PROV_ACTION: _ACTION_TRANSITION,
            _PROV_TO: target,
            _PROV_AT: now.isoformat(),
        }
        if note is not None:
            event[_PROV_NOTE] = note
        try:
            await self._apply([self._transition_fragment(finding_id, target, current, event)])
        except SurrealConnectionError:
            # A genuine transport fault — never a lost race; propagate untouched.
            raise
        except TxnContentionExhaustedError:
            # A genuine conflict outlived the retry budget — this is NOT a lost
            # CAS (finding #102): the row may be untouched and this transition
            # perfectly legal, so it must never be re-read and misreported as
            # an IllegalTransitionError below. Propagate untouched.
            raise
        except SurrealStoreError as error:
            # The transaction rolled back: this call's CAS matched zero rows, meaning
            # a concurrent writer committed first. Re-validate from the FRESH state so
            # the raised error names the (now-current) state and the refused target —
            # e.g. a race where the winner already drove ``open -> resolved`` makes
            # this call's ``open -> wontfix`` into the illegal ``resolved -> wontfix``
            # terminal edge.
            fresh = await self._select_row_by_id(finding_id)
            if fresh is None:
                raise FindingNotFoundError(
                    f"no finding with id {finding_id!r}"
                ) from error
            fresh_status = str(fresh.get(_COL_STATUS))
            # Refuse from the FRESH edge when it is itself illegal (the common case).
            self._validate_transition(finding_id, fresh_status, target)
            # The fresh edge is somehow legal (a benign concurrent reorder, not
            # exercised by the pins) — still refuse: this call's CAS never landed.
            raise IllegalTransitionError(
                f"lost a concurrent transition race for finding {finding_id!r}: the "
                f"status moved to {fresh_status!r} before this {current!r} -> "
                f"{render_attributed(target)} transition could apply"
            ) from error

        updated = await self._select_row_by_id(finding_id)
        if updated is None:
            raise FindingNotFoundError(f"no finding with id {finding_id!r}")
        return self._row_to_finding(updated)

    @staticmethod
    def _transition_fragment(
        finding_id: str, target: str, expected_from: str, event: dict[str, Any]
    ) -> TxnFragment:
        """The guarded-CAS transition fragment: LET-bind, THROW on zero rows.

        Mirrors :meth:`~loremaster.tasks.TaskLedger._transition_fragment`: a guarded
        ``UPDATE`` binds its affected rows to ``$tr_updated`` — mutating ONLY while
        the row is STILL in ``expected_from`` — and
        ``IF array::len($tr_updated) == 0 { THROW … }`` rolls the WHOLE transaction
        back the instant a concurrent writer already moved the row away, so a zero-row
        CAS is ALWAYS a typed, detectable rollback — never a silent no-op a caller
        could mistake for success. The new provenance EVENT is appended SERVER-SIDE
        (``provenance.events += [$tr_event]``) rather than written as a whole
        Python-merged object, so concurrent mutators can never clobber each other's
        events. Unlike the task ledger, a finding transition guards ONLY on
        ``status`` — a finding is never gated by supersession (the ``supersedes`` link
        lives on the successor, not the predecessor).
        """
        set_parts = [
            f"{_COL_STATUS} = ${_TRANSITION_STATUS_PARAM}",
            f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [${_TRANSITION_EVENT_PARAM}]",
        ]
        guarded_transition = (
            f"LET ${_TRANSITION_UPDATED_VAR} = (UPDATE "
            f"type::record('{FINDING_TABLE}', ${_TRANSITION_ID_PARAM}) SET "
            f"{', '.join(set_parts)} "
            f"WHERE {_COL_STATUS} = ${_TRANSITION_EXPECTED_FROM_PARAM})"
        )
        guard_updated = (
            f"IF array::len(${_TRANSITION_UPDATED_VAR}) == 0 "
            f"{{ THROW '{_TRANSITION_ALREADY_MESSAGE}' }}"
        )
        return TxnFragment(
            statements=[guarded_transition, guard_updated],
            params={
                _TRANSITION_ID_PARAM: finding_id,
                _TRANSITION_STATUS_PARAM: target,
                _TRANSITION_EVENT_PARAM: event,
                _TRANSITION_EXPECTED_FROM_PARAM: expected_from,
            },
        )

    @staticmethod
    def _validate_transition(finding_id: str, current: str, target: str) -> None:
        """Refuse an illegal transition (typed, naming both states), else pass.

        Order (most-specific first): a target outside the vocabulary is not a legal
        value; a ``(current, target)`` pair absent from :data:`LEGAL_TRANSITIONS` is
        an illegal edge.

        Raises:
            IllegalTransitionError: Either refusal — the message always names both
                ``current`` and ``target`` so a caller/operator can see exactly what
                was refused.
        """
        if target not in FINDING_STATUSES:
            raise IllegalTransitionError(
                f"cannot transition finding {finding_id!r} from {current!r} to "
                f"{render_attributed(target)}: {render_attributed(target)} is not one of the valid statuses "
                f"{sorted(FINDING_STATUSES)}"
            )
        if (current, target) not in LEGAL_TRANSITIONS:
            raise IllegalTransitionError(
                f"illegal transition from {current!r} to {render_attributed(target)} for finding "
                f"{finding_id!r}: not a legal state-machine edge"
            )

    # -- reads / mapping ----------------------------------------------------

    async def _resolve_row(self, id_or_number: int | str) -> dict[str, Any] | None:
        """Return the raw ``finding`` row addressed by an id OR a number, or ``None``.

        An ``int`` (that is not a ``bool``) addresses by the stable ``number``;
        anything else by the opaque id.
        """
        if isinstance(id_or_number, int) and not isinstance(id_or_number, bool):
            return await self._select_row_by_number(id_or_number)
        return await self._select_row_by_id(str(id_or_number))

    async def _resolve_or_raise(self, id_or_number: int | str) -> dict[str, Any]:
        """Resolve ``id_or_number`` to a raw row, or raise :class:`FindingNotFoundError`."""
        row = await self._resolve_row(id_or_number)
        if row is None:
            raise FindingNotFoundError(f"no finding addressed by {render_attributed(id_or_number)}")
        return row

    async def _select_row_by_id(self, finding_id: str) -> dict[str, Any] | None:
        """Return the raw ``finding`` row dict for ``finding_id``, or ``None`` if absent."""
        rows = self._as_rows(
            await self._query(
                f"SELECT * FROM type::record('{FINDING_TABLE}', ${_ROW_ID_PARAM})",
                {_ROW_ID_PARAM: finding_id},
            )
        )
        return rows[0] if rows else None

    async def _select_row_by_number(self, number: int) -> dict[str, Any] | None:
        """Return the raw ``finding`` row dict addressed by ``number``, or ``None``.

        ``number`` is UNIQUE, so at most one row ever matches.
        """
        rows = self._as_rows(
            await self._query(
                f"SELECT * FROM {FINDING_TABLE} WHERE {_COL_NUMBER} = ${_ROW_NUMBER_PARAM} LIMIT 1",
                {_ROW_NUMBER_PARAM: number},
            )
        )
        return rows[0] if rows else None

    async def _select_successors(self, finding_id: str) -> list[dict[str, Any]]:
        """Return EVERY finding that supersedes ``finding_id`` (its chain successors).

        A finding X's successor is a finding whose ``supersedes`` link names X.
        Ordered by ``number`` ASC, so ``[0]`` is the deterministic lowest-numbered
        branch :meth:`chain_head` walks and ``[1:]`` are the sibling arms of a FORK
        it surfaces. A linear chain yields at most one row; a fork (two findings
        each superseding X — reachable through the public API) yields several. The
        walk relies on this FULL list (never a ``LIMIT 1``) so the higher-numbered
        arm is visible, not silently dropped.
        """
        return self._as_rows(
            await self._query(
                f"SELECT * FROM {FINDING_TABLE} WHERE {_COL_SUPERSEDES} = "
                f"type::record('{FINDING_TABLE}', ${_ROW_ID_PARAM}) "
                f"ORDER BY {_COL_NUMBER} ASC",
                {_ROW_ID_PARAM: finding_id},
            )
        )

    def _row_to_finding(self, row: dict[str, Any]) -> Finding:
        """Map a raw ``finding`` row into a FRESH :class:`Finding` value object.

        Never returns the raw row: the ``RecordID`` is reduced to its bare opaque
        string, the ``supersedes`` record link decodes to a bare opaque id (or
        ``None``), and ``created_at`` is normalised to tz-aware UTC (the
        fleet-comparable anchor).
        """
        return Finding(
            id=self._bare_id(row.get(_ID_KEY)),
            number=int(row.get(_COL_NUMBER, 0)),
            kind=str(row.get(_COL_KIND, "")),
            status=cast(FindingStatus, row.get(_COL_STATUS)),
            subject=str(row.get(_COL_SUBJECT, "")),
            body=str(row.get(_COL_BODY, "")),
            area=str(row.get(_COL_AREA, "")),
            category=str(row.get(_COL_CATEGORY, "")),
            created_by=str(row.get(_COL_CREATED_BY, "")),
            created_at=self._require_aware_utc(row.get(_COL_CREATED_AT)),
            supersedes=self._bare_id_or_none(row.get(_COL_SUPERSEDES)),
            provenance=dict(row.get(_COL_PROVENANCE) or {}),
        )

    # -- result narrowing / normalisation -----------------------------------

    @staticmethod
    def _as_rows(result: Any) -> list[dict[str, Any]]:
        """Narrow a ``SELECT`` result to its list of dict rows."""
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    @classmethod
    def _extract_group_count(cls, result: Any) -> int:
        """Extract the total from a ``SELECT count() … GROUP ALL`` result.

        On SurrealDB ≥3.1 an EMPTY group returns ZERO rows (never a row with
        ``count: 0``), so the missing-projection idiom applies: default to 0
        rather than indexing blindly into an empty result.
        """
        rows = cls._as_rows(result)
        if not rows:
            return 0
        return int(rows[0].get(_COUNT_KEY, 0))

    def _require_aware_utc(self, value: Any) -> datetime:
        """Normalise a REQUIRED datetime column to tz-aware UTC, refusing a bad value.

        ``created_at`` is a non-``option`` schema column the ledger always sets, so a
        faithful row always carries a real datetime; a missing/uncoercible one is a
        corrupt row, refused LOUDLY rather than silently coerced.

        Raises:
            SurrealStoreError: The value is missing or cannot be read as a datetime.
        """
        coerced = self._to_aware_utc(value)
        if coerced is None:
            raise SurrealStoreError(
                f"finding row column {_COL_CREATED_AT!r} is missing or not a datetime "
                f"(got {type(value).__name__})"
            )
        return coerced

    @staticmethod
    def _to_aware_utc(value: Any) -> datetime | None:
        """Coerce a stored datetime into a tz-aware UTC datetime (or ``None``).

        The SDK's CBOR decoder returns tz-aware datetimes, but a naive datetime or an
        ISO-string/wrapper shape is normalised defensively so ``Finding.created_at``
        is ALWAYS tz-aware (a naive stamp is the classic wrong-anchor bug for a value
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

    @classmethod
    def _bare_id_or_none(cls, raw: Any) -> str | None:
        """Reduce a ``supersedes`` record link to its bare opaque id, or ``None``.

        An unset ``option<record<finding>>`` column decodes to ``None`` (no link); a
        present link decodes to its bare id component.
        """
        if raw is None:
            return None
        return cls._bare_id(raw)

    @staticmethod
    def _bare_id(raw: Any) -> str:
        """Return the BARE finding id — no ``finding:`` record-table prefix.

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
