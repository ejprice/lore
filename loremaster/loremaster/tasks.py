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
        async query_tasks(*, status=None, owner=None, blocked=None, limit=None) -> list[Task]
        async claim_task(task_id, owner) -> ClaimResult
        async transition(task_id, status, *, actor) -> Task
        async supersede_task(task_id, *, subject, description, created_by) -> str
        async transitive_blockers(task_id, *, max_depth=None) -> TransitiveBlockers

    Exceptions: TaskLedgerError(RuntimeError);
                TaskNotFoundError(TaskLedgerError);
                IllegalTransitionError(TaskLedgerError);
                UnknownBlockerError(TaskLedgerError, agent_existence.UnknownRowError);
                TaskCycleError(TaskLedgerError).

PACKET 04b-1 adds the ``task->blocks->task`` DAG edge beside the ``blocked_by``
column. The edge is a PURE MIRROR of the column — same set, every write path, every
row — and it is ``ENFORCED`` from birth, so an edge to a task that does not exist is
impossible. Two consequences worth stating once, because they decide how the rest of
this module reads:

* **the COLUMN is the authority the CLAIM reads, and the EDGE is the authority the
  TRAVERSAL reads.** They agree by construction (the mirror at every write path plus
  :meth:`~TaskLedger.ensure_ready`'s backfill of the rows that predate the edge) with
  ONE permanent residue: a legacy ``blocked_by`` naming NO task row cannot carry an
  edge. It still blocks the task — the claim CAS counts it — so the residue can only
  make the traversal SHORT, never make a blocked task look claimable.
* **the write-time acyclicity guard walks the COLUMN and the transitive read walks the
  EDGE, and neither may be swapped for the other.** A cycle closes on a dependency
  naming a task that does not exist yet; ``ENFORCED`` forbids that edge, so an engine
  traversal of ``blocks`` reports every such cycle as acyclic.
"""

from __future__ import annotations

import asyncio
import graphlib
import logging
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, NoReturn, Protocol, cast
from uuid import uuid4

import networkx
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from surrealdb import AsyncSurreal, RecordID

from loremaster.agent_existence import (
    UnknownRowError,
    reject_unknown_rows,
    resolve_existing_rows,
)
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
    execute_read_transaction,
    execute_transaction,
    run_query,
    signin_credentials,
)
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE, generate_task_ddl

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
# PKT-06 §1/§4: the rollup's leg-1 activity stamp (``updated_at``, stamped
# ``time::now()`` inside claim/transition/supersede-of-old — never at create)
# and the done-transition's two completion-record columns (``summary``
# mandatory, ``report_path`` optional). All three are ``option`` so a legacy
# (pre-deploy) row decodes them back to ``None``.
_COL_UPDATED_AT = "updated_at"
_COL_SUMMARY = "summary"
_COL_REPORT_PATH = "report_path"

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

# The record-id table separator. (The signin credential keys moved to the ONE
# shared ``store._txn.signin_credentials`` seam — #211/#102.)
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
# PKT-06 §4: the done-transition's completion-record params, written inside
# the SAME guarded CAS only when the target is ``done`` (see
# :meth:`TaskLedger._transition_fragment`).
_TRANSITION_SUMMARY_PARAM = "tr_summary"
_TRANSITION_REPORT_PATH_PARAM = "tr_report_path"
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

# The single-record read's param name. (The create path's own params moved to the
# shared ``cm<i>_`` namespacing when packet 04b-1 made ``create_task`` transactional,
# so the two create verbs compose through one fragment builder rather than two.)
_ROW_ID_PARAM = "id"

# PKT-06 §1: ``updated_since``'s bound-parameter name and the field a
# ``SELECT count() … GROUP ALL`` result carries the total under (mirrors
# ``diff.py``'s / ``store/surreal.py``'s own ``_COUNT_KEY`` idiom for the same
# shape).
_UPDATED_SINCE_PARAM = "upd_since"
_COUNT_KEY = "count"

# PKT-06 §2 (L2a): the ``create_many`` batch's ALL-OR-NOTHING per-item
# transaction-fragment param-name prefixes (``cm<i>_id`` / ``cm<i>_content``)
# — one CREATE fragment per spec, composed into ONE ``execute_transaction``.
_CREATE_MANY_ID_PARAM_FMT = "cm{index}_id"
_CREATE_MANY_CONTENT_PARAM_FMT = "cm{index}_content"

# PKT-06 §4: the done-transition's mandatory-summary cap (the approved row's
# "capped summary" — a decided value, individually strikeable per the design).
_DONE_SUMMARY_MAX_CHARS = 300

# --- packet 04b-1: the ``blocks`` DAG -----------------------------------------

#: SurrealDB's HARD recursion ceiling. [PROBED 2026-07-26, 3.2.1, packet-04 probe §5.3]
#: ``@.{..257}`` raises *"Found 257 for bound but expected 256 at most"* and an OPEN bound
#: past 256 raises *"Exceeded the idiom recursion limit"*. It is FIXED by the engine and is
#: not configurable, which is why the public ``max_depth`` bound is a property of THIS API
#: rather than of an implementation detail a caller cannot see.
ENGINE_RECURSION_CEILING = 256

#: The default depth :meth:`TaskLedger.transitive_blockers` walks. A NAMED CONSTANT rather
#: than a literal at the call site so the packet's *"explicit small bound"* is greppable and
#: changeable in ONE place — and so a caller's render can teach a concrete re-ask without
#: re-deriving it (it travels back on every result as ``max_depth_used``). It sits well
#: inside :data:`ENGINE_RECURSION_CEILING`: a default at or above the ceiling would turn a
#: silent truncation into a boot-visible crash on the first deep graph.
TASK_BLOCKER_MAX_DEPTH = 32

#: The blocker pre-check's vocabulary, handed to the SHARED row-existence policy
#: (:func:`~loremaster.agent_existence.reject_unknown_rows`). It is DATA here, never a
#: sentence typed at the call site: lead ruling **L3** rules the check a GENERALISATION of
#: packet 04a's agent policy, and a second refusal sentence would be copy #2 of a served
#: surface (#102).
_BLOCKER_NOUN = "task"
_BLOCKER_REMEDY = (
    "every blocked_by entry must name an existing task row or a task created in the same "
    "call; NOTHING was created, so a corrected resend is safe"
)

#: The two CYCLE vocabularies operator ruling **R6** permits to differ — batch-local temp
#: KEYS and PERSISTED task ids name different things — over the ONE shared sentence shape
#: (:func:`format_cycle_refusal`) and the ONE shared detector
#: (:func:`find_blocked_by_cycle`).
CYCLE_NOUN_PERSISTED_IDS = "task ids"
CYCLE_NOUN_BATCH_KEYS = "batch keys"

#: The traversal's wall-clock backstop. Probe §5.5: WHICH brake fires — the depth bound or
#: the clock — is a property of the DATA (the graph's branching factor), not of the query,
#: so the safe shape is neither brake alone: an explicit small upper bound, ``+collect``,
#: AND a ``SELECT``-level ``TIMEOUT``. It is a ``SELECT`` clause and a PARSE ERROR on a bare
#: idiom (probe §5.2), which is why the traversal is written in the ``SELECT … @ … FROM``
#: form rather than as the bare recursive idiom.
_TRAVERSAL_TIMEOUT = "5s"

# The bound-parameter names of the new statements (the house idiom: named once each, never
# a hand-copied literal drifting between the statement and its params).
_TRAVERSAL_START_PARAM = "tb_start"
#: The seed list of :meth:`TaskLedger._bounded_dependency_graph`'s closure read (ESC-1 /
#: FORK A). A LIST of ``RecordID`` starts, distinct from ``_TRAVERSAL_START_PARAM``'s single
#: start, so the two statements never share a name that means two different shapes.
_CLOSURE_START_PARAM = "closure_starts"
_TRAVERSAL_WITHIN_KEY = "within"
_TRAVERSAL_PROBE_KEY = "probe"
_QUERY_ROWS_VAR = "qt_rows"
_QUERY_STATUS_PARAM = "qt_status"
_QUERY_OWNER_PARAM = "qt_owner"
_QUERY_LIMIT_PARAM = "qt_limit"

# --- packet 04b-2 wave C: the two reads ruling R10(iii)'s renders ride -----------
#: :meth:`TaskLedger.direct_dependents`' bound id. The predicate is
#: ``blocked_by CONTAINS $dep_task_id`` — the vendor-documented containment spelling
#: (store reference §2, *"Indexing an ARRAY column"*), PROBED 2026-08-02 on spike-surreal
#: 3.2.1 against this very schema with a positive control (2 of 6 rows selected, exactly
#: the two naming the target; an id nothing names selects ZERO, so the predicate is not
#: matching everything). ⚠ Never ``blocked_by = $id``: on an array column that spelling
#: IndexScans and returns ``[]`` — fast, silent and wrong.
_DEPENDENTS_ID_PARAM = "dep_task_id"
#: :meth:`TaskLedger._superseded_among`'s bound id list.
_SUPERSEDED_AMONG_PARAM = "sup_among_ids"
_BACKFILL_IN_KEY = "blocker"
_BACKFILL_OUT_KEY = "blocked"
_RELATE_FROM_PARAM_FMT = "rel{index}_from"
_RELATE_TO_PARAM_FMT = "rel{index}_to"

# The structured log events the ``ensure_ready`` backfill emits. Ruling **R11**: a phantom
# skip is RECORDED, never silent (*"a silent skip is a false clear"*), and ESC-4 rules the
# same for a legacy CYCLE, which the backfill MINTS rather than refusing (the edge set must
# MIRROR reality; a divergence the invariant asserts does not exist is a false clear in the
# store itself). Both are WARNING because both name a pre-existing DATA defect an operator
# can act on.
_BACKFILL_PHANTOM_EVENT = "task.backfill.phantom_blocker_skipped"
_BACKFILL_CYCLE_EVENT = "task.backfill.legacy_cycle_minted"


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
        updated_at: The tz-aware UTC timestamp of the task's most recent
            fleet-visible activity (claim / transition / supersede-of-this-
            row), or ``None`` when never mutated since creation (PKT-06 §1 —
            NOT stamped at create; a mere read never stamps it either).
        summary: The one-line completion digest recorded on the transition to
            ``done`` (mandatory on that edge), or ``None`` for a task that has
            never reached ``done``.
        report_path: The optional report-file path recorded alongside
            ``summary`` on the done edge, or ``None`` when no report file
            exists (or the task has never reached ``done``).
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
    updated_at: datetime | None = None
    summary: str | None = None
    report_path: str | None = None


class TaskActivityWindow(BaseModel):
    """The rollup's leg-1 read: tasks with fleet-visible activity since a cursor.

    Attributes:
        rows: The matching tasks, ordered by ``updated_at`` ascending, capped
            at the caller's ``limit``.
        total: The HONEST total count of tasks matching the window (may exceed
            ``len(rows)`` when ``limit`` truncated the result).
    """

    model_config = ConfigDict(extra="forbid")

    rows: list[Task]
    total: int


class TaskSpec(BaseModel):
    """One task specification inside a :meth:`TaskLedger.create_many` batch.

    Key-agnostic (PKT-06 §2 — "the ledger stays key-agnostic"): ``blocked_by``
    here is ALREADY resolved to real (or intentionally pass-through) task ids
    — the caller's temp-key resolution is a DISPATCHER concern, never this
    ledger's.

    Attributes:
        subject: The short human-readable title of the work item.
        description: The longer free-text description of the work item.
        blocked_by: Already-resolved ids of tasks this one depends on.
    """

    model_config = ConfigDict(extra="forbid")

    subject: str
    description: str
    blocked_by: list[str] = Field(default_factory=list)


class TaskSpecLike(Protocol):
    """The structural shape :meth:`TaskLedger.create_many` accepts per item.

    Matches :class:`TaskSpec` STRUCTURALLY, never nominally — mirrors the
    design's "the ledger stays key-agnostic" ruling: ``create_many`` never
    isinstance-checks its ``specs``, only reads these three attributes, so any
    duck-typed caller-supplied object satisfying them (e.g. a dispatcher- or
    test-local stand-in) is interchangeable with a real :class:`TaskSpec`.
    """

    subject: str
    description: str
    blocked_by: list[str]


class ClaimResult(BaseModel):
    """The outcome of an atomic :meth:`TaskLedger.claim_task` compare-and-set.

    Attributes:
        claimed: Whether THIS call won the claim.
        task: The task's state after the call — the freshly-claimed state on a
            win, or the current (unmodified) state on a loss.
        superseded_blockers: On a LOST claim, the ``blocked_by`` entries that have
            themselves been SUPERSEDED, mapped to their successor ids; empty otherwise.
            Ruling **R10(iii)**: supersession is NOT terminal, so the claim CAS counts
            such a blocker forever and the loss is PERMANENT — *"blocked_by [...]
            unresolved"* alone invites an agent to poll a door that is nailed shut, while
            the actionable fact is that the work moved. It travels as TYPED STATE because
            the render is a pure ``staticmethod`` over this model: a render that re-read
            the store to write the sentence would be a second implementation of the
            blocker policy, and every non-MCP consumer of :meth:`TaskLedger.claim_task`
            would get nothing. ⚠ It DEFAULTS deliberately — a required field would be a
            ``TypeError`` at every existing construction site on an otherwise-correct
            build.
    """

    model_config = ConfigDict(extra="forbid")

    claimed: bool
    task: Task
    superseded_blockers: dict[str, str] = Field(default_factory=dict)


class TaskLedgerError(RuntimeError):
    """Base class for every error :class:`TaskLedger` raises."""


class TaskNotFoundError(TaskLedgerError):
    """Raised when a task id does not resolve to any row in the ledger."""


class IllegalTransitionError(TaskLedgerError):
    """Raised when a requested status transition is not a legal state-machine edge."""


class UnknownBlockerError(TaskLedgerError, UnknownRowError):
    """Raised when a ``blocked_by`` entry does not name a USABLE task row.

    TWO bases on purpose, and the second is not decoration: a task caller keeps ONE
    ``except TaskLedgerError`` for this ledger's whole vocabulary, while a caller who
    wants *"this id names no row"* across BOTH the agent and task families catches
    :class:`~loremaster.agent_existence.UnknownRowError` — the shared base of the shared
    policy (lead ruling L3, 04a's ``UnknownRecipientError`` shape).

    Operator ruling **R3** makes this a CHANGE to a live verb: a create naming a phantom
    blocker is now REFUSED where it used to produce a task that was unclaimable forever,
    silently. Ruling **R10(ii)** widens the same refusal to a SUPERSEDED blocker, naming
    its successor — supersession means the work MOVED, so a ``blocked_by`` naming a
    superseded task can never resolve.
    """


class TaskCycleError(TaskLedgerError):
    """Raised when a requested write would put a task on a ``blocked_by`` CYCLE.

    ⚠ Deliberately NOT a :class:`~loremaster.agent_existence.UnknownRowError`: a cycle and
    a phantom blocker are DIFFERENT problems needing DIFFERENT next moves (break the loop
    vs create the missing task), and every id on a cycle EXISTS — which is precisely why
    ``ENFORCED`` cannot catch it.

    Operator ruling **R6**: ONE error class for BOTH cycle vocabularies, so a
    ``lore_tasks`` caller can write one ``except`` for *"this batch has a loop"* whether
    the loop is among batch KEYS or among PERSISTED ids.
    """


class TransitiveBlockers(BaseModel):
    """What :meth:`TaskLedger.transitive_blockers` serves — HONEST at its bound (E-3).

    ⚠ **THE FIELD SET IS CLOSED, AND THE ABSENCE IS THE POINT.** The tail beyond a
    truncated closure is genuinely UNCOUNTABLE without walking it — the server does not
    know how many blockers lie past the bound — so a ``remaining``/``total``/``+K`` field
    could only ever be FABRICATED. A tool caught inventing one number is untrustworthy on
    all of them, so the safe set is enumerated here and nothing else may be added.

    Attributes:
        ids: The task's transitive UPSTREAM blockers — deduplicated and ordered by
            proximity (the ``+collect`` closure's own ordering), never including the task
            itself unless it genuinely lies on a cycle.
        truncated: Whether the walk stopped at ``max_depth_used`` with more upstream
            still reachable. NEVER a silently short list: probe §5.3 measured
            ``{..256+collect}`` returning 256 of 299 nodes with no error and no signal.
        max_depth_used: The depth the read ACTUALLY ran at — the caller's ``max_depth``
            when supplied, else :data:`TASK_BLOCKER_MAX_DEPTH`. It travels back so a
            render can teach a concrete re-ask without importing or re-deriving the
            ledger's default, which drifts the day the default changes.
    """

    model_config = ConfigDict(extra="forbid")

    ids: list[str] = Field(default_factory=list)
    truncated: bool = False
    max_depth_used: int


class TaskListing(BaseModel):
    """A CALLER-LIMITED task listing, and whether the cap cut anything off (ESC-5).

    ⚠ **THE FIELD SET IS CLOSED AT TWO, DENY-BY-DEFAULT**, for the reason
    :class:`TransitiveBlockers`' docstring gives about its own uncountable tail: the SAFE
    shape is one thing and the set of names a fabricated count could wear is unbounded.
    Adding ANY count field (``total`` / ``remaining`` / ``+K``) first acquires the
    failed-count construction — build the world where the count read FAILS and prove the
    line goes LOUD or drops the NUMBER, never restating ``len(rows)``, which is not a total
    at all once the cap is in the statement. **A number-free wrapper acquires none of that
    debt, and that is why this shape was chosen: the existence bit rides the SAME read as
    the rows, so there is no separate failure state to forge.**

    The grammar is **EXISTENCE, never quantity** (design ruling: mechanism (c), over-fetch
    by one) and it is uniform across both of :meth:`TaskLedger.query_tasks`' filter paths.

    Attributes:
        rows: The tasks actually SERVED — at most the caller's cap.
        more: Whether a further MATCHING row truly exists beyond ``rows``. It is a
            MEASUREMENT (the over-fetched row either came back or it did not), never an
            inference from ``len(rows) == limit``: at ``population == cap`` the window is
            full AND the answer is complete, so a window-fullness bit claims a surplus
            that does not exist. Always ``False`` for an uncapped listing, which is
            complete by construction.
    """

    model_config = ConfigDict(extra="forbid")

    rows: list[Task]
    more: bool


def validated_task_limit(limit: int | None) -> int | None:
    """Refuse an unusable task ``limit`` CLIENT-SIDE, naming the value (ruling **T2**).

    **THE ONE IMPLEMENTATION of "what counts as a legal cap?"**, module-level rather than
    private to the ledger so the LEDGER and the DISPATCHER share one answer instead of the
    dispatcher growing a private copy that agrees today and drifts tomorrow
    (:meth:`TaskLedger._validated_limit` delegates here). It matters because the
    disclosure's over-fetch validates the CALLER's cap and then asks the ledger for
    ``cap + 1``: two rule sets would make ``limit=0`` a refusal at one seam and a legal
    ``LIMIT 1`` read at the other.

    ``bool`` is excluded explicitly because it is an ``int`` subclass and ``limit=True``
    would otherwise silently mean ``LIMIT 1`` — and, under an over-fetch, ``LIMIT 2``.
    Nothing is bound into a statement until this passes, so an out-of-range cap costs no
    round trip at all.

    Args:
        limit: The caller's cap, or ``None`` for every match.

    Returns:
        The validated cap, or ``None`` when the caller supplied none.

    Raises:
        TaskLedgerError: ``limit`` is not a positive integer. Refused client-side naming
            the value, because the engine's own complaint (*"LIMIT/START must be a
            non-negative integer"*) is withheld by the store seam's error hygiene and the
            caller could not otherwise tell its own bad input from a broken tool.
    """
    if limit is None:
        return None
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise TaskLedgerError(
            f"limit={limit!r} is out of range — it must be a positive integer "
            f"naming how many tasks to serve, or be omitted for every match"
        )
    return limit


def find_blocked_by_cycle(edges: Mapping[str, Iterable[str]]) -> list[str] | None:
    """The ONE ``blocked_by`` cycle detector (operator ruling **R6**).

    Ledger-owned and shared: BOTH the write-time guard over PERSISTED ids and
    ``server.py``'s batch-local temp-KEY check route through it, so a cyclic batch cannot
    be refused by two detectors with two sentences and two error classes. Sharing is
    proved by MUTATION, never by inspection — neutralise this and BOTH shapes must stop
    being refused (``test_blocks_edge.py::TestTheCyclePolicyHasONEImplementation``).

    **Packages considered — ``replace``, and the library is STDLIB.**
    :class:`graphlib.TopologicalSorter` ships with Python and its
    ``CycleError.args[1]`` IS the cycle in the exact shape both call sites need: a
    2-cycle yields ``['a', 'b', 'a']`` and a SELF-loop ``['x', 'x']`` — byte-for-byte
    the format the batch-key check's own docstring already promised — and a dependency
    naming an id OUTSIDE the graph is tolerated, which is precisely what a ``blocked_by``
    entry pointing outside the read needs.

    Args:
        edges: ``{node: the nodes it is blocked_by}``. A referenced node that is not
            itself a key is tolerated (it has no dependencies of its own).

    Returns:
        The first cycle found, as an ordered path ending back at its own start, or
        ``None`` when the graph is acyclic. Nodes and their dependencies are SORTED
        before the walk so a graph with several cycles reports the same one every run —
        a refusal that names a different loop each attempt is not actionable.
    """
    graph = {node: sorted(set(refs)) for node, refs in sorted(edges.items())}
    try:
        graphlib.TopologicalSorter(graph).prepare()
    except graphlib.CycleError as cycle:
        return [str(member) for member in cycle.args[1]]
    return None


def format_cycle_refusal(*, noun: str, cycle: Sequence[str]) -> str:
    """The ONE served cycle-refusal sentence — one SHAPE, two vocabularies (**R6**).

    R6, verbatim: *"The DETECTION ALGORITHM is shared; the vocabularies may still differ
    (batch-local temp keys vs persisted ids) because they name different things."* So the
    shared thing is a formatter taking the NOUN, never a constant string — and mutating
    it must change BOTH served sentences, which is the only test that tells DRY from
    looks-DRY.

    THE CONSUMER IS AN AGENT: the sentence names EVERY member of the loop, in order,
    because a caller cannot break a cycle it cannot see; and it states the no-write fact
    for the same reason the blocker refusal does — an agent reading only *"refused"* must
    otherwise pay a reconnaissance read before it dares resend.

    Args:
        noun: What the cycle's members are (:data:`CYCLE_NOUN_BATCH_KEYS` /
            :data:`CYCLE_NOUN_PERSISTED_IDS`).
        cycle: The loop as an ordered path ending back at its own start.

    Returns:
        The refusal sentence, with no leading class name — the caller wraps it.
    """
    return (
        f"blocked_by cycle among {noun}: {' -> '.join(cycle)} — a task on a cycle can "
        f"never be claimed, because every one of its blockers must reach a terminal "
        f"status first; break the cycle. NOTHING was created, so a corrected resend "
        f"is safe"
    )


def raise_cycle_refusal(*, noun: str, cycle: Sequence[str]) -> NoReturn:
    """Refuse a cycle in the ONE error class and the ONE sentence shape (**R6**).

    The single RAISE site both consumers call, so the class and the sentence cannot drift
    apart at one of them. ``server.py`` calls THIS rather than formatting its own error:
    that is what keeps the shared formatter observable from the dispatcher — a bound copy
    of the formatter in another module would be a private copy wearing the shared name.
    """
    raise TaskCycleError(format_cycle_refusal(noun=noun, cycle=cycle))


def _drop_one_cycle_edge(
    graph: dict[str, set[str]], cycle: Sequence[str]
) -> bool:
    """Remove ONE edge of ``cycle`` from ``graph`` in place; ``True`` if one was removed.

    Used to keep looking PAST a cycle that is not the caller's business — a legacy loop
    among rows this call did not write, which the write guard must not blame a new caller
    for, and which the backfill has already RECORDED. One edge per iteration (never the
    whole member set) so a DIFFERENT loop sharing some of these nodes still surfaces on a
    later pass; progress is guaranteed because every iteration removes an edge.
    """
    for index in range(len(cycle) - 1):
        first, second = cycle[index], cycle[index + 1]
        if second in graph.get(first, ()):
            graph[first] = graph[first] - {second}
            return True
        if first in graph.get(second, ()):
            graph[second] = graph[second] - {first}
            return True
    return False


def _superseded_blocker_clause(row_id: str, row: Mapping[str, Any]) -> str | None:
    """Operator ruling **R10(ii)**: a SUPERSEDED blocker is refused, naming its successor.

    A ``blocked_by`` naming a superseded task is NEVER legitimate — the claim CAS can only
    resolve a blocker that reaches ``done``/``wontfix``, and a superseded row refuses every
    transition — so the dependency is a silent black hole of exactly the shape ruling R3
    exists to abolish, reached through a different door.

    Near-zero cost, which is why the ruling is affordable: the grouped existence read
    already holds the row, so projecting ``superseded_by`` beside existence costs nothing
    and turns a rejection into a RECOVERY — the difference between a one-edit fix and a
    reconnaissance round trip, on the served surface an agent learns the contract from.

    Returns the clause when the row is superseded, else ``None`` (the row is usable).
    """
    successor = row.get(_COL_SUPERSEDED_BY)
    if successor is None:
        return None
    return (
        f"task {row_id} is superseded by {successor} — block on {successor} instead"
    )


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
        # Guards the connect-time check-then-set so N concurrent first-callers
        # never each open their own underlying SDK connection (mirrors
        # ``SurrealStore`` / ``LocalMemoryBackend``'s double-checked lock).
        self._connect_lock = asyncio.Lock()

    # -- connection lifecycle ----------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking (mirrors :class:`LocalMemoryBackend`): the fast
        path never touches the lock. The session bootstrap is
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
        The DDL is a MIX (finding #107): the table and its index are ``IF NOT
        EXISTS``, so a second call neither raises nor wipes existing rows —
        every per-test fresh database depends on this — but every FIELD is
        ``DEFINE FIELD OVERWRITE`` (see :mod:`loremaster.store.surreal_schema`),
        so a field definition CHANGE still migrates a live store.

        THEN back-fills the ``blocks`` edge from the ``blocked_by`` COLUMNS that are
        already there (operator ruling **R11**) — see :meth:`_backfill_blocks_edges` for
        why that is a correctness requirement and not a nicety.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: A DDL statement was rejected by the engine, or the
                backfill's own reads/writes were.
            UnknownBlockerError: Never — the backfill SKIPS a phantom blocker (loudly)
                rather than refusing; listed only to say so explicitly.
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
        await self._backfill_blocks_edges()

    async def _backfill_blocks_edges(self) -> None:
        """Mint the ``blocks`` edges the EXISTING ``blocked_by`` columns already imply.

        ⚠⚠ **WITHOUT THIS THE DEPLOY SHIPS A CONFIDENT LIE** (sidecar finding S3, operator
        ruling **R11**). The mirror is ∀ verbs going FORWARD; every task row written before
        this packet carries a ``blocked_by`` COLUMN and NO edge, and
        :meth:`transitive_blockers` rides EDGES by design — so on exactly the rows a fleet
        is working the read would answer ``ids=[] truncated=False``: clean, confident and
        WRONG. That is not a missing bound, it is a positive assertion of completeness that
        is false. R11 rules the defect FIXED rather than disclosed, because a permanent tax
        on every future read is a bad trade for a one-time migration, and a separate
        one-shot script is a deploy that silently reproduces the defect the day someone
        forgets it.

        Four properties, each of which a plausible build drops:

        * **PRE-FILTERED through the SHARED row-existence policy** (L3). Legacy rows carry
          PHANTOM blockers — ``blocked_by`` was FAIL-OPEN at write until this packet — and a
          phantom endpoint meets ``ENFORCED``, so a NAKED backfill does not skip one edge:
          it ROLLS BACK THE WHOLE ONE-TRANSACTION MIGRATION and the store never boots.
        * **The skip is RECORDED, never silent**, naming the phantom AND the task it was
          skipped for: a skipped entry is a SCOPE BOUND on what the edge graph covers, and
          an unrecorded bound is one nobody can meet deliberately.
        * **A legacy CYCLE is MINTED, and RECORDED** (ESC-4). Refusing it would break
          edge ≡ ``blocked_by`` on exactly the rows the invariant is hardest to reason
          about, and ``+collect`` terminates on cycles (probe §5.4). A legacy cycle is a
          pre-existing DATA defect; the edge set must MIRROR reality rather than quietly
          diverge from it, and the RECORD is what stops the mirroring being silent.
        * **IDEMPOTENT, against the STORE's own edge set** rather than against a
          *"have I run"* flag: this runs at EVERY boot, and between two boots an ordinary
          ``create_task`` also mints edges, so the second boot meets a store whose edges
          came from two sources. Re-minting would either double the edge (no
          ``UNIQUE(in, out)``) or raise (with one — §4: *"a duplicate is a loud ERR"*),
          i.e. a silently wrong graph or a container that boots exactly once.

        The mirror is over the COLUMN, ∀ ROWS and ∀ BLOCKER STATES — not only the ``open``
        rows, not only the un-superseded blockers, not only the unfinished ones. R10(ii)
        refuses a superseded blocker at WRITE time, which is a decision about a dependency
        someone is creating NOW; reusing that refusal HERE would drop a dependency that
        already exists (R10(iii): *"supersession can happen AFTER dependents exist"*) and
        restore S3's false clear through the filter meant to prevent it.

        Cost: THREE round trips on a boot with legacy edges to mint (the graph read, the
        existence probe, the one mint transaction), TWO when there is nothing missing, and
        it never grows with the number of edges — R11's own rationale is a claim about ONE
        transaction, and a build issuing one ``RELATE`` per edge makes that rationale false.
        """
        columns, existing = await self._read_mirror_state()
        wanted = {
            (blocker, task_id)
            for task_id, blockers in columns.items()
            for blocker in dict.fromkeys(blockers)
        }
        missing = sorted(wanted - existing)
        if not missing:
            return

        resolved = await resolve_existing_rows(
            self._query, TASK_TABLE, sorted({blocker for blocker, _task in missing})
        )
        mintable: list[tuple[str, str]] = []
        for blocker, task_id in missing:
            if blocker in resolved:
                mintable.append((blocker, task_id))
                continue
            logger.warning(
                _BACKFILL_PHANTOM_EVENT,
                extra={
                    "database": self._database,
                    "task_id": task_id,
                    "phantom_blocker_id": blocker,
                },
            )
        self._record_legacy_cycles(columns)
        if not mintable:
            return
        await self._apply([self._relate_fragment(mintable)])
        logger.info(
            "task.backfill.blocks_edges_minted",
            extra={"database": self._database, "minted": len(mintable)},
        )

    async def _read_mirror_state(
        self,
    ) -> tuple[dict[str, list[str]], set[tuple[str, str]]]:
        """The whole mirror, read in ONE round trip: the columns and the edges that exist.

        BOTH reads share one snapshot, so the "what is missing" set can never be computed
        from a column read and an edge read that saw different stores. The column read is
        bounded by the DEPENDENCY-BEARING rows (``array::len(blocked_by) > 0``), never the
        whole table — the same property #253 is about, on the migration path.
        """
        results = await execute_read_transaction(
            "BEGIN;\n"
            f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_BLOCKED_BY} FROM {TASK_TABLE} "
            f"WHERE array::len({_COL_BLOCKED_BY}) > 0;\n"
            f"SELECT record::id(in) AS {_BACKFILL_IN_KEY}, record::id(out) AS "
            f"{_BACKFILL_OUT_KEY} FROM {BLOCKS_RELATION};\n"
            "COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        payloads = self._row_payloads(results)
        column_rows = self._as_rows(payloads[0] if payloads else [])
        edge_rows = self._as_rows(payloads[1] if len(payloads) > 1 else [])
        columns = {
            str(row.get(_ID_KEY)): [
                str(blocker) for blocker in (row.get(_COL_BLOCKED_BY) or ())
            ]
            for row in column_rows
        }
        edges = {
            (str(row.get(_BACKFILL_IN_KEY)), str(row.get(_BACKFILL_OUT_KEY)))
            for row in edge_rows
        }
        return columns, edges

    def _record_legacy_cycles(self, columns: Mapping[str, Sequence[str]]) -> None:
        """Record every legacy ``blocked_by`` CYCLE the backfill is about to mirror (ESC-4).

        Not a refusal — the ruling is explicit that refusing would break the mirror on the
        rows the invariant is hardest to reason about. What it buys is that a pre-existing
        DATA defect stops being invisible: an operator who is never told cannot repair the
        rows, and the next reader rediscovers it from a task that is stuck forever.

        Every member of every loop is named. ENUMERATION is ``networkx.simple_cycles`` — the
        packages-over-hand-rolling swap of #273: Johnson's algorithm returns every simple
        cycle of the directed ``blocked_by`` graph (an edge ``node -> its blocker``), so a
        component holding several loops records each of them — and it does NOT undercount a
        fully-connected component the way the retired hand-rolled drop-an-edge decomposition
        did (4 recorded vs 5 real, #273, measured 2026-07-28).

        ⚠ **The MODULE-attribute call ``networkx.simple_cycles`` is deliberate, not a style
        choice.** It is what lets ``TestTheEnumerationEQUALSNetworkxAfterTheSwap``'s MP-4
        mutation prove the LIBRARY is called rather than merely imported beside a retained
        hand-roll (routing-is-not-sharing, #102) — a ``from networkx import simple_cycles``
        binding would escape that patch. DETECTION stays the shared ``find_blocked_by_cycle``
        (R6, one ledger-owned detector); this swaps ENUMERATION only.
        """
        graph = networkx.DiGraph()
        for node, blockers in columns.items():
            graph.add_node(node)
            for blocker in blockers:
                graph.add_edge(node, blocker)
        for cycle in networkx.simple_cycles(graph):
            logger.warning(
                _BACKFILL_CYCLE_EVENT,
                extra={
                    "database": self._database,
                    "cycle": " -> ".join(cycle),
                    "members": sorted(set(cycle)),
                },
            )

    @staticmethod
    def _row_payloads(results: Sequence[Any]) -> list[list[Any]]:
        """The ROW-BEARING results of a read transaction, in statement order.

        ⚠ Filtered by SHAPE rather than indexed by position, and that is deliberate: the
        engine's envelope carries an entry for ``BEGIN`` and for ``COMMIT`` too (MEASURED
        2026-07-28 on spike-surreal 3.2.1), and a ``LET`` yields ``None``. Positional
        indexing would therefore encode an off-by-one that is invisible until the day the
        envelope changes; every ``SELECT`` returns a list and nothing else here does.
        """
        return [entry for entry in results if isinstance(entry, list)]

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

        Delegates to :func:`~loremaster.store._txn.run_query` — the ONE shared
        attempt body every single-statement seam in the package now calls
        (blindreader F3; see its docstring for the classify/self-heal/log
        mechanism, including its RETRYABLE-conflict path, finding #120/#108).
        """
        return await run_query(
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
            noun="task query",
            label="task.query.rejected",
            statement=statement,
            params=params or {},
            logger=logger,
        )

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

        PACKET 04b-1 makes this a TRANSACTION and gives it two pre-checks. The row and
        its ``blocks`` edges are written in ONE ``BEGIN … COMMIT`` (see
        :meth:`_create_fragment` / :meth:`_relate_fragment`), so a rejected edge can never
        leave an orphan task behind whose ``blocked_by`` names a blocker with no edge.
        Before that: every ``blocked_by`` entry is resolved against the ledger (operator
        rulings **R3** / **R10(ii)** — a phantom or SUPERSEDED blocker is REFUSED, by
        name, where it used to produce a task that was unclaimable forever, silently), and
        the dependency graph is walked for a CYCLE over PERSISTED ids (**R6**).

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

        Cost:
            **3 round trips** when ``blocked_by`` is non-empty — the blocker-existence
            pre-check, the acyclicity walk, and the write — against 1 before this packet,
            and **1** when there are no dependencies at all (both pre-checks short-circuit
            without touching the wire). Stated here because ruling **E-4** states the send
            path's extra trip as an ACCEPTED COST and the CREATE path takes the same kind
            of hit with no ruling naming it: an unstated cost is a surprise the next
            engineer rediscovers from a latency graph. **Re-open trigger:** the first
            measured create-path latency concern — the pre-authorised alternative is
            folding the acyclicity walk into the existence read's transaction, which costs
            the shared policy its own seam and is a contract change, not a shortcut.

        Raises:
            UnknownBlockerError: A ``blocked_by`` entry names no task row, or names a
                SUPERSEDED one (the refusal names its successor).
            TaskCycleError: The dependency would close a ``blocked_by`` cycle, so the
                task could never be claimed.
            TaskLedgerError: The blocker-existence read itself failed — a store fault,
                classified into this ledger's vocabulary rather than served raw.
        """
        dependencies = list(dict.fromkeys(blocked_by or ()))
        task_id = uuid4().hex  # OPAQUE, non-sequential; never content-derived.
        await self._reject_unusable_blockers([(entry, entry) for entry in dependencies])
        await self._refuse_a_cycle({task_id: dependencies})
        now = datetime.now(UTC)
        content = self._new_task_content(subject, description, dependencies, created_by, now)
        await self._apply(
            [
                self._create_fragment(0, task_id, content),
                self._relate_fragment([(blocker, task_id) for blocker in dependencies]),
            ]
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
        limit: int | None = None,
    ) -> list[Task]:
        """Return the tasks matching every supplied filter, AND-combined.

        The fleet-visible read: exact ``status`` / ``owner`` equality filters plus a
        dependency-aware ``blocked`` partition. A task is BLOCKED iff ANY of its OWN
        ``blocked_by`` entries is unresolved — the blocker's row is missing (a
        never-minted id ⇒ fail-closed UNRESOLVED) or its status is not terminal
        (``done`` / ``wontfix``). The partition is strictly ONE HOP, exactly like the
        atomic claim's server-side ``array::len`` CAS, which compares against THIS row's
        own column and knows nothing about the chain; a transitive resolver would make
        the two disagree, in a direction that hides claimable work from the fleet
        forever. (The TRANSITIVE view is :meth:`transitive_blockers`, and it is a
        different question.)

        **#253 — the read is BOUNDED by the caller's filter.** ``status``/``owner`` push
        into the STATEMENT, so the work scales with the ANSWER rather than with the
        ledger. ⚠ **Blocker resolution does NOT narrow with them**, and that is
        load-bearing: the blockers are resolved by their own read over the CANDIDATE
        set's ``blocked_by`` ids, so a blocker the caller's own filter excluded still
        counts. Narrowing it is the plausible rewrite that silently mis-classifies the
        partition, in a direction that depends on which filter the caller supplied — for
        a TERMINAL out-of-filter blocker it drops claimable work from the answer while
        the claim CAS still grants it to anyone asking by id.

        **R7 — both reads share ONE snapshot.** They ride ONE ``BEGIN … COMMIT``
        (:func:`~loremaster.store._txn.execute_read_transaction`), so the TOCTOU a
        two-read rewrite would otherwise INTRODUCE — a writer committing between the
        candidate read and the blocker read, making the served partition disagree with
        the claim CAS without either read being wrong — is closed BY CONSTRUCTION rather
        than named and accepted.

        **T1 — the cap applies to the ANSWER, never to the candidate scan.** With
        ``blocked`` supplied, a ``LIMIT`` in the statement would cut rows BEFORE the
        partition and serve fewer than the caller asked for while more exist, with no
        signal; so the scan is capped only where the candidates ARE the answer
        (``blocked is None``) and is otherwise exhausted before the cap is applied. A
        short answer is therefore a TRUE short answer — asking the identical question
        with no cap returns the same rows. ⚠ Consequently a *"rows read ≤ f(limit)"*
        expectation on the blocked-filtered path is wrong by design: filling an answer
        cap legitimately means scanning past non-matching candidates.

        Args:
            status: When given, restrict to tasks in this exact status.
            owner: When given, restrict to tasks currently owned by this
                identity.
            blocked: When given, restrict to genuinely-blocked (``True``) or
                genuinely-unblocked (``False``) tasks.
            limit: When given, the maximum number of tasks to SERVE (a positive int).
                It windows the answer; it never changes which tasks qualify.

        Returns:
            The matching tasks (empty when nothing matches), capped at ``limit``.

        Raises:
            TaskLedgerError: ``limit`` is not a positive integer. Refused CLIENT-SIDE,
                naming the value: the engine rejects a negative ``LIMIT`` with
                *"LIMIT/START must be a non-negative integer"* (MEASURED), which the
                store seam's error hygiene then withholds — so a caller would receive
                *"(unspecified rejection); see the server log"* and could not tell its
                own bad input from a broken tool (ruling **T2**).
        """
        cap = self._validated_limit(limit)
        statement, params = self._candidate_statement(
            status=status, owner=owner, limit=None if blocked is not None else cap
        )
        fragments = [
            f"LET ${_QUERY_ROWS_VAR} = ({statement})",
            f"${_QUERY_ROWS_VAR}",
        ]
        if blocked is not None:
            # The blocker read is DIRECT RECORD ACCESS over the candidates' own
            # ``blocked_by`` ids, built server-side inside the same snapshot: a
            # never-minted id is silently DROPPED, which is exactly the fail-closed
            # UNRESOLVED default the claim CAS applies, so the two mechanisms cannot
            # disagree about a phantom blocker.
            # ⚠ ``id`` is projected BARE and decoded client-side, NOT ``record::id(id)``.
            # MEASURED 2026-07-28 on 3.2.1: over a FROM-array holding a RecordID that
            # names no row, the projection is evaluated against a NONE record and
            # ``record::id(NONE)`` is an ENGINE ERROR that rolls the whole transaction
            # back — so the server-side decode turns exactly the fail-closed case this
            # read exists to serve into a failure. A bare ``id`` drops the ghost silently,
            # which is the behaviour the CAS matches.
            fragments.append(
                f"SELECT {_ID_KEY}, {_COL_STATUS} FROM "
                f"array::map(array::distinct(array::flatten(${_QUERY_ROWS_VAR}."
                f"{_COL_BLOCKED_BY})), |$blocker| type::record('{TASK_TABLE}', $blocker))"
            )
        payloads = self._row_payloads(
            await execute_read_transaction(
                "BEGIN;\n" + ";\n".join(fragments) + ";\nCOMMIT;\n",
                params,
                acquire=self._ensure_connection,
                drop=self._drop_connection,
                url=self._url,
            )
        )
        candidates = [self._row_to_task(row) for row in self._as_rows(payloads[0] if payloads else [])]
        if blocked is None:
            return candidates
        status_by_id = {
            self._bare_id(row.get(_ID_KEY)): str(row.get(_COL_STATUS))
            for row in self._as_rows(payloads[1] if len(payloads) > 1 else [])
        }
        selected = [
            task for task in candidates if self._is_blocked(task, status_by_id) == blocked
        ]
        return selected if cap is None else selected[:cap]

    @staticmethod
    def _validated_limit(limit: int | None) -> int | None:
        """Refuse an unusable ``limit`` CLIENT-SIDE — DELEGATED, never re-decided here.

        The rule itself lives in :func:`validated_task_limit` because the dispatcher's
        over-fetch validates the CALLER's cap before this ledger ever sees ``cap + 1``, and
        two seams deciding *"what counts as a legal cap?"* separately is the duplicated
        policy #102 exists to stop. This stays as the ledger's own in-vocabulary entry
        point (its callers read better for it) and carries no rule of its own.
        """
        return validated_task_limit(limit)

    @staticmethod
    def _candidate_statement(
        *, status: str | None, owner: str | None, limit: int | None
    ) -> tuple[str, dict[str, Any]]:
        """The candidate ``SELECT``: the caller's equality filters, pushed into the store.

        ``SELECT *`` deliberately, never a projection list: store reference §2 records
        that a column left OUT of an explicit projection reads back as ``None`` SILENTLY,
        and :meth:`_row_to_task` would map that to ``subject=''`` / ``provenance={}`` — a
        structurally valid, materially FALSE task. Pushing filters into the store is
        exactly the moment somebody writes a projection list, so the absence of one here
        is a decision.

        Every caller VALUE travels as a BOUND PARAMETER. ``owner`` is unconstrained free
        text (``claim_task`` takes any string), so an interpolated one is both an
        injection surface and a parse error waiting for an apostrophe.
        """
        clauses: list[str] = []
        params: dict[str, Any] = {}
        if status is not None:
            clauses.append(f"{_COL_STATUS} = ${_QUERY_STATUS_PARAM}")
            params[_QUERY_STATUS_PARAM] = status
        if owner is not None:
            clauses.append(f"{_COL_OWNER} = ${_QUERY_OWNER_PARAM}")
            params[_QUERY_OWNER_PARAM] = owner
        statement = f"SELECT * FROM {TASK_TABLE}"
        if clauses:
            statement = f"{statement} WHERE {' AND '.join(clauses)}"
        if limit is not None:
            # ⚠ Emitted ONLY when the caller asked for a cap. MEASURED on 3.2.1:
            # ``LIMIT $k`` with ``$k = NONE`` returns ZERO rows and NO error, so the
            # obvious build — always emit the clause and bind ``None`` — turns every
            # unlimited query in the fleet into an empty answer, silently.
            statement = f"{statement} LIMIT ${_QUERY_LIMIT_PARAM}"
            params[_QUERY_LIMIT_PARAM] = limit
        return statement, params

    async def direct_dependents(self, task_id: str) -> list[str]:
        """The ids of the tasks whose OWN ``blocked_by`` column names ``task_id``.

        Ruling **R10(iii)**: superseding a task STRANDS everything blocked on it —
        supersession is not terminal (R10 refused to make it so), so the claim CAS keeps
        counting the predecessor as unresolved and every dependent is unclaimable
        **forever**, silently. This is the read the supersede render's warning rides, so
        the caller learns WHICH rows to re-point at the successor. It only reports; the
        dependency transfer itself is R10(iv) and is DEFERRED, because ``blocked_by`` is
        immutable after creation and the claim path leans on that.

        **ONE HOP, deliberately** — the rows whose own column names this id, never the
        transitive downstream reach. The CAS that strands them is itself a strictly one-hop
        predicate, so a transitive answer would name rows this supersession did not strand.

        ⚠ **Store-side containment, not a whole-graph read.** A client-side whole-graph
        read would have answered the same question by shipping every dependency-bearing row
        to the client and filtering here; this narrows in the statement instead, so the
        payload scales with the ANSWER. See
        :data:`_DEPENDENTS_ID_PARAM` for the probed predicate and the spelling that is
        silently wrong.

        Args:
            task_id: The task whose direct dependents to list.

        Returns:
            The dependents' opaque ids, sorted, or ``[]`` when nothing depends on it. ⚠ An
            id naming NO row also yields ``[]`` — it matches no row's ``blocked_by``, and
            there is no caller-reachable engine rejection to launder here.
        """
        rows = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY} FROM {TASK_TABLE} "
                f"WHERE {_COL_BLOCKED_BY} CONTAINS ${_DEPENDENTS_ID_PARAM}",
                {_DEPENDENTS_ID_PARAM: task_id},
            )
        )
        return sorted(str(row.get(_ID_KEY)) for row in rows)

    async def _superseded_among(self, task_ids: Sequence[str]) -> dict[str, str]:
        """Which of ``task_ids`` are SUPERSEDED, mapped to their successor ids.

        The fact behind :attr:`ClaimResult.superseded_blockers`: a blocker that moved can
        never resolve, so a claim losing to one has lost PERMANENTLY and *"blocked_by [...]
        unresolved"* would teach an agent to poll forever. Read here, in the ledger, rather
        than in a render — the render is a pure function over :class:`ClaimResult`, and a
        store read from inside it would be a second implementation of the blocker policy
        that every non-MCP consumer of :meth:`claim_task` would miss.

        An EMPTY input short-circuits: an unblocked loss (already owned, or a status that
        is simply not claimable) must not buy a round trip to learn nothing.
        """
        if not task_ids:
            return {}
        rows = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_SUPERSEDED_BY} "
                f"FROM {TASK_TABLE} "
                f"WHERE record::id({_ID_KEY}) IN ${_SUPERSEDED_AMONG_PARAM} "
                f"AND {_COL_SUPERSEDED_BY} IS NOT NONE",
                {_SUPERSEDED_AMONG_PARAM: list(task_ids)},
            )
        )
        return {
            str(row.get(_ID_KEY)): str(row.get(_COL_SUPERSEDED_BY))
            for row in rows
            if row.get(_COL_SUPERSEDED_BY) is not None
        }

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
            raise TaskNotFoundError(f"no task with id {render_attributed(task_id)}")
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
        # Ruling R10(iii): a LOSS to a SUPERSEDED blocker is PERMANENT, and only the
        # ledger can say so — the CAS counts that blocker forever. Read only on a loss
        # that HAS blockers: a win owes the caller nothing to poll, and an unblocked loss
        # (already held, or an unclaimable status) must not buy a round trip to learn
        # nothing. ``_superseded_among`` short-circuits the empty case for the same reason.
        superseded_blockers = (
            {} if won else await self._superseded_among(updated.blocked_by)
        )
        return ClaimResult(
            claimed=won, task=updated, superseded_blockers=superseded_blockers
        )

    @staticmethod
    def _claim_fragment(task_id: str, owner: str, blocked_by: list[str]) -> TxnFragment:
        """The atomic-claim fragment: LET-resolve blockers, then the guarded CAS.

        ``$clm_resolved`` binds the blocker record-ids that have reached a
        terminal status (read inside the transaction, so consistent with the
        mutation). The UPDATE mutates ONLY when the row is still open, unowned,
        not superseded, AND every blocker resolved — expressed as
        ``array::len(array::distinct(blocked_by)) = array::len($clm_resolved)``: a
        never-minted or still-open blocker is simply absent from the resolved list, so
        the counts differ and the claim fails CLOSED. A failed guard matches zero rows
        and writes nothing.

        ⚠ **``array::distinct`` IS RULING T5's FIX AND IT IS NOT COSMETIC.** The resolved
        list is a SET of matching rows, so a row whose ``blocked_by`` is ``[X, X]`` with
        ``X`` done compares ``2 != 1`` and can NEVER be claimed — while ``_is_blocked``
        iterates ENTRIES and cheerfully serves it as claimable. ``_new_task_content``'s
        birth-time dedupe is the only thing that has been standing between the two
        mechanisms, i.e. the normalisation exists precisely because the CAS could not
        tolerate duplicates; a row that predates it — or any future write path that
        forgets it — is a task the fleet is told to claim and that nobody can take. A
        divergence between the SERVED partition and what the CAS actually does is a trust
        defect by definition, so the guard is made to tolerate what the normalisation was
        silently protecting it from. ⚠ It must stay INSIDE this one atomic statement:
        de-duplicating anywhere else leaves the compare-and-set itself unchanged.
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
            f"{_COL_CLAIMED_AT} = time::now(), "
            f"{_COL_UPDATED_AT} = time::now() "
            f"WHERE {_COL_STATUS} = ${_CLAIM_OPEN_PARAM} "
            f"AND {_COL_OWNER} IS NONE "
            f"AND {_COL_SUPERSEDED_BY} IS NONE "
            f"AND array::len(array::distinct({_COL_BLOCKED_BY})) = "
            f"array::len(${_CLAIM_RESOLVED_VAR})"
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

    async def transition(
        self,
        task_id: str,
        status: str,
        *,
        actor: str,
        summary: str | None = None,
        report_path: str | None = None,
    ) -> Task:
        """Drive a task through a legal state-machine edge.

        Validates the target and the edge BEFORE any write: a superseded task
        refuses ALL transitions; a target outside the six-status vocabulary or a
        ``(from, to)`` pair not in :data:`LEGAL_TRANSITIONS` raises
        :class:`IllegalTransitionError` naming BOTH states and leaves the row
        untouched. A legal transition stamps ``actor`` into ``provenance``;
        re-entering ``open`` (the ``blocked -> open`` release edge) clears
        ``owner`` / ``claimed_at`` so the row is genuinely re-claimable.

        PKT-06 §4: immediately after the edge check, :meth:`_validate_done_summary`
        enforces the done-transition's completion-record rules — a target of
        ``done`` REQUIRES a single-line, ≤300-char ``summary`` (the fleet's
        durable completion record the rollup serves) and accepts an optional
        single-line ``report_path``; any OTHER target rejects a supplied
        ``summary``/``report_path`` as caller misuse. Both are written inside the
        SAME guarded CAS as the status flip (see :meth:`_transition_fragment`),
        so the completion record and the status transition land atomically.

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
            summary: A one-line completion digest, MANDATORY when ``status`` is
                ``done``; must be omitted for every other target.
            report_path: An optional report-file path recorded alongside
                ``summary`` on the done edge; must be omitted for every other
                target.

        Returns:
            The task's updated state.

        Raises:
            TaskNotFoundError: No task with ``task_id`` exists.
            IllegalTransitionError: ``status`` is not a legal edge from the
                task's current status (or the task is superseded), the done
                edge's ``summary``/``report_path`` rules were violated, OR this
                call lost a concurrent race to transition the same row.
            ValueError: ``summary``/``report_path`` was supplied for a
                non-``done`` target.
        """
        row = await self._select_row(task_id)
        if row is None:
            raise TaskNotFoundError(f"no task with id {render_attributed(task_id)}")
        current = str(row.get(_COL_STATUS))
        superseded_by = row.get(_COL_SUPERSEDED_BY)
        self._validate_transition(task_id, current, status, superseded_by)
        self._validate_done_summary(task_id, status, summary, report_path)

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
                [
                    self._transition_fragment(
                        task_id, status, current, event, release, summary, report_path
                    )
                ]
            )
        except SurrealConnectionError:
            # A genuine transport fault — never a lost race; propagate untouched
            # (must not be masked as an illegal-transition rejection).
            raise
        except TxnContentionExhaustedError:
            # A genuine conflict outlived the retry budget — this is NOT a lost
            # CAS (finding #102): the row may be untouched and this transition
            # perfectly legal, so it must never be re-read and misreported as
            # an IllegalTransitionError below. Propagate untouched.
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
                raise TaskNotFoundError(f"no task with id {render_attributed(task_id)}") from error
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
                f"lost a concurrent transition race for task {render_attributed(task_id)}: the status "
                f"moved to {fresh_status!r} before this {current!r} -> {render_attributed(status)} "
                f"transition could apply"
            ) from error

        updated = await self._select_row(task_id)
        if updated is None:
            raise TaskNotFoundError(f"no task with id {render_attributed(task_id)}")
        return self._row_to_task(updated)

    @staticmethod
    def _transition_fragment(
        task_id: str,
        target: str,
        expected_from: str,
        event: dict[str, Any],
        release: bool,
        summary: str | None = None,
        report_path: str | None = None,
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
        Every transition stamps ``updated_at = time::now()`` (PKT-06 §1 — the
        rollup's leg-1 activity signal); a ``done`` target ADDITIONALLY writes
        ``summary``/``report_path`` (PKT-06 §4(d) — atomic with the status
        flip, already validated by :meth:`_validate_done_summary`).
        """
        set_parts = [
            f"{_COL_STATUS} = ${_TRANSITION_STATUS_PARAM}",
            f"{_COL_UPDATED_AT} = time::now()",
            f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [${_TRANSITION_EVENT_PARAM}]",
        ]
        params: dict[str, Any] = {
            _TRANSITION_ID_PARAM: task_id,
            _TRANSITION_STATUS_PARAM: target,
            _TRANSITION_EVENT_PARAM: event,
            _TRANSITION_EXPECTED_FROM_PARAM: expected_from,
        }
        if release:
            # The ONLY ways into ``open`` are creation and this release edge; a
            # released task must be unowned/unclaimed for the claim CAS (which
            # checks ``owner IS NONE`` alongside ``status = open``) to see it.
            set_parts.append(f"{_COL_OWNER} = NONE")
            set_parts.append(f"{_COL_CLAIMED_AT} = NONE")
        if target == STATUS_DONE:
            set_parts.append(f"{_COL_SUMMARY} = ${_TRANSITION_SUMMARY_PARAM}")
            set_parts.append(f"{_COL_REPORT_PATH} = ${_TRANSITION_REPORT_PATH_PARAM}")
            params[_TRANSITION_SUMMARY_PARAM] = summary
            params[_TRANSITION_REPORT_PATH_PARAM] = report_path
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
        return TxnFragment(statements=[guarded_transition, guard_updated], params=params)

    @staticmethod
    def _validate_done_summary(
        task_id: str, target: str, summary: str | None, report_path: str | None
    ) -> None:
        """PKT-06 §4: enforce the done-transition's ``summary``/``report_path`` rules.

        Checked AFTER the state-machine edge is confirmed legal (by
        :meth:`_validate_transition`) and BEFORE the CAS. Every error text is
        pinned VERBATIM against the resolved build design
        (``scratchpad/PKT-06-build-design.md`` §4):

        1. ``target == done`` and ``summary`` missing/blank →
           :class:`IllegalTransitionError` (rejected like ``claimed -> done``).
        2. ``target == done`` and ``summary`` carries a newline/carriage return →
           :class:`IllegalTransitionError` (single-line law).
        3. ``target == done`` and ``len(summary) > 300`` →
           :class:`IllegalTransitionError` naming the actual length.
        4. ``target == done`` and ``report_path`` given but blank or multi-line →
           :class:`IllegalTransitionError` (report_path is OPTIONAL, but when
           given must be non-empty and single-line).
        5. ``target != done`` and either was supplied → :class:`ValueError`
           (input misuse, not a state-machine edge rejection).

        Raises:
            IllegalTransitionError: Rules 1-4 above.
            ValueError: Rule 5 above.
        """
        if target == STATUS_DONE:
            if summary is None or not summary.strip():
                raise IllegalTransitionError(
                    f"transition to 'done' for task {render_attributed(task_id)} requires 'summary' — a "
                    f"one-line completion digest (max 300 chars) the rollup serves as "
                    f"the fleet's durable completion record; pass report_path= too "
                    f"when a report file exists"
                )
            if "\n" in summary or "\r" in summary:
                raise IllegalTransitionError(
                    f"task {render_attributed(task_id)} done-summary must be a single line — put "
                    f"detail in the report file and pass its path as report_path="
                )
            if len(summary) > _DONE_SUMMARY_MAX_CHARS:
                raise IllegalTransitionError(
                    f"task {render_attributed(task_id)} done-summary is {len(summary)} chars — the cap "
                    f"is {_DONE_SUMMARY_MAX_CHARS}; tighten it (detail belongs in the "
                    f"report file)"
                )
            if report_path is not None:
                if not report_path.strip():
                    raise IllegalTransitionError(
                        f"task {render_attributed(task_id)} done-report_path must be non-empty when "
                        f"given — omit report_path= entirely when there is no report file"
                    )
                if "\n" in report_path or "\r" in report_path:
                    raise IllegalTransitionError(
                        f"task {render_attributed(task_id)} done-report_path must be a single line — put "
                        f"detail in the report file and pass its path as report_path="
                    )
        elif summary is not None or report_path is not None:
            raise ValueError(
                f"summary/report_path are recorded only on the transition to "
                f"'done' (got target {target!r}) — omit them here"
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
                f"task {render_attributed(task_id)} is superseded and cannot transition "
                f"from {current!r} to {render_attributed(target)}"
            )
        if target not in TASK_STATUSES:
            raise IllegalTransitionError(
                f"cannot transition task {render_attributed(task_id)} from {current!r} "
                f"to {render_attributed(target)}: "
                f"{render_attributed(target)} is not one of the valid statuses {sorted(TASK_STATUSES)}"
            )
        if (current, target) not in LEGAL_TRANSITIONS:
            raise IllegalTransitionError(
                f"illegal transition from {current!r} to {render_attributed(target)} "
                f"for task {render_attributed(task_id)}: "
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
        blocked_by: list[str] | None = None,
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

        PACKET 05b (#174): the successor reframes the SAME work item, so its dependency
        structure travels with it, mirrored onto the ENFORCED ``blocks`` edge and run
        through the SAME pre-checks :meth:`create_task` runs (lead ruling L3 — ONE
        implementation, not a clone). ``blocked_by`` is a SENTINEL: ``None`` INHERITs the
        predecessor's ``blocked_by``; ``[]`` CLEARs it; ``[ids]`` REPLACEs it (never a
        merge). The resolved set is deduped (order-preserving). A phantom or SUPERSEDED
        blocker is REFUSED atomically before the write — nothing minted, the old row
        un-stamped — where it used to mint a successor that was unclaimable forever,
        silently (the harm #174 abolishes). Cost mirrors :meth:`create_task`: two extra
        round trips only when the resolved ``blocked_by`` is non-empty.

        Args:
            task_id: The opaque id of the task being superseded.
            subject: The successor task's short human-readable title.
            description: The successor task's longer free-text description.
            created_by: The identity of the caller performing the supersession.
            blocked_by: The successor's dependency SENTINEL — ``None`` (INHERIT the
                predecessor's ``blocked_by``), ``[]`` (CLEAR), or ``[ids]`` (REPLACE the
                resolved set, deduped order-preserving — NOT a merge).

        Returns:
            The newly created successor task's opaque id.

        Raises:
            TaskNotFoundError: No task with ``task_id`` exists.
            IllegalTransitionError: The task is ALREADY superseded (sequentially,
                or as the loser of a concurrent double supersede).
            UnknownBlockerError: A resolved ``blocked_by`` entry names no task row, or
                names a SUPERSEDED one (refused by the SHARED blocker-existence policy).
            TaskCycleError: The resolved ``blocked_by`` would put the successor on a
                ``blocked_by`` cycle, OR names the very task being superseded (a successor
                blocked by its predecessor is unclaimable forever).
        """
        row = await self._select_row(task_id)
        if row is None:
            raise TaskNotFoundError(f"no task with id {render_attributed(task_id)}")
        # Sequential guard: a superseded task is terminal-like (exactly as it
        # refuses transitions), so a second supersede is refused up front. The
        # RACING double-supersede is caught transactionally below (the guarded
        # stamp + IF/THROW), not here — this pre-read only fast-fails the already
        # -settled sequential case.
        if row.get(_COL_SUPERSEDED_BY) is not None:
            raise IllegalTransitionError(
                f"task {render_attributed(task_id)} is already superseded by "
                f"{row.get(_COL_SUPERSEDED_BY)!r} and cannot be superseded again"
            )

        # #174: resolve the successor's dependency SENTINEL (INHERIT / CLEAR / REPLACE),
        # deduped order-preserving, exactly as create_task normalises its own blocked_by.
        if blocked_by is None:
            dependencies = [str(blocker) for blocker in (row.get(_COL_BLOCKED_BY) or ())]
        else:
            dependencies = [str(blocker) for blocker in blocked_by]
        dependencies = list(dict.fromkeys(dependencies))
        new_id = uuid4().hex
        # A successor blocked_by the task it supersedes is UNCLAIMABLE FOREVER: the
        # predecessor is stamped ``superseded`` (a NON-terminal status) in this very
        # transaction, so the successor's claim CAS can never resolve it. Neither shared
        # pre-check below can see it — ``_reject_unusable_blockers`` finds the predecessor
        # present and not-yet-superseded at check time, and ``_refuse_a_cycle`` finds a
        # fresh successor id on no COLUMN cycle — so this dedicated guard covers BOTH the
        # explicit-override and the inherited (legacy self-loop) paths.
        if task_id in dependencies:
            raise TaskCycleError(
                f"a successor cannot be blocked by the task it supersedes: "
                f"{render_attributed(task_id)} — supersede reframes the same work item, so "
                f"re-point the dependency at the successor (or drop it) rather than at the "
                f"task being superseded"
            )
        # The SAME shared pre-checks create_task runs, over the RESOLVED deps (L3 / R6 —
        # ONE implementation): a phantom/superseded blocker or a column cycle is refused
        # atomically before any write. Both short-circuit on empty deps (no wire cost).
        await self._reject_unusable_blockers([(entry, entry) for entry in dependencies])
        await self._refuse_a_cycle({new_id: dependencies})

        now = datetime.now(UTC)
        content = self._new_task_content(subject, description, dependencies, created_by, now)
        event = {
            _PROV_ACTOR: created_by,
            _PROV_ACTION: _ACTION_SUPERSEDE,
            _PROV_SUCCESSOR: new_id,
            _PROV_AT: now.isoformat(),
        }
        try:
            # The successor CREATE (in the supersede fragment) and its blocks-edge mirror
            # ride ONE transaction: RELATE comes AFTER the CREATE so the ENFORCED ``out``
            # endpoint (the fresh successor) exists, and the loser of a raced supersede
            # rolls back the WHOLE txn (stamp + CREATE + RELATEs) — ZERO orphan edges.
            await self._apply(
                [
                    self._supersede_fragment(task_id, new_id, content, event),
                    self._relate_fragment(
                        [(blocker, new_id) for blocker in dependencies]
                    ),
                ]
            )
        except SurrealConnectionError:
            # A genuine transport fault — never a lost race; propagate untouched
            # (must not be masked as an already-superseded rejection).
            raise
        except TxnContentionExhaustedError:
            # A genuine conflict outlived the retry budget — this is NOT a lost
            # race (finding #102): the old row may be un-stamped and this
            # supersede perfectly legal, so it must never be reported as
            # "already superseded by someone else". Propagate untouched.
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
                    f"task {render_attributed(task_id)} is already superseded by "
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
            f"{_COL_UPDATED_AT} = time::now(), "
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

    # -- rollup / batch (PKT-06) --------------------------------------------

    async def updated_since(self, since: datetime, *, limit: int) -> TaskActivityWindow:
        """The rollup's leg-1 read: tasks with fleet-visible activity since ``since``.

        Reads the ``updated_at`` column — stamped ``time::now()`` inside the
        SAME guarded CAS by :meth:`claim_task`, :meth:`transition`, and
        :meth:`supersede_task` (of the OLD row) — NEVER at :meth:`create_task`,
        so a never-mutated task never appears. ``NONE > $since`` is falsy in
        SurrealDB, so a legacy (never-mutated) row is excluded by the WHERE
        clause itself. Ordered ``updated_at`` ASC, capped at ``limit``, with an
        HONEST ``total`` (a second bounded ``SELECT count() … GROUP ALL`` —
        never a second unbounded scan) so a caller can tell a truncated window
        from an exhaustive one.

        Args:
            since: The EXCLUSIVE lower bound — only tasks updated STRICTLY
                after this tz-aware UTC instant are returned.
            limit: The maximum number of rows to return (must be a positive int).

        Returns:
            The matching window: ``rows`` (ASC by ``updated_at``, capped at
            ``limit``) and the honest ``total`` (``>= len(rows)``).

        Raises:
            ValueError: ``limit`` is not a positive integer.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"limit must be a positive integer, got {limit!r}")
        params: dict[str, Any] = {_UPDATED_SINCE_PARAM: since}
        rows_result = await self._query(
            f"SELECT * FROM {TASK_TABLE} WHERE {_COL_UPDATED_AT} > ${_UPDATED_SINCE_PARAM} "
            f"ORDER BY {_COL_UPDATED_AT} ASC LIMIT {limit}",
            params,
        )
        rows = [self._row_to_task(row) for row in self._as_rows(rows_result)]
        count_result = await self._query(
            f"SELECT count() FROM {TASK_TABLE} WHERE {_COL_UPDATED_AT} > "
            f"${_UPDATED_SINCE_PARAM} GROUP ALL",
            params,
        )
        return TaskActivityWindow(rows=rows, total=self._extract_group_count(count_result))

    async def create_many(
        self,
        specs: Sequence[TaskSpecLike],
        *,
        created_by: str,
        ids: Sequence[str] | None = None,
    ) -> list[str]:
        """Batch-create tasks, ALL-OR-NOTHING, ids positionally aligned with ``specs``.

        Mints a fresh, OPAQUE ``uuid4`` id per spec (never content-derived,
        exactly like :meth:`create_task`) — unless the caller supplies ``ids``
        — and composes ONE ``execute_transaction`` from N CREATE fragments
        (each namespaced ``cm<i>_id`` / ``cm<i>_content`` so
        :func:`~loremaster.store._txn.compose` never collides) — so either
        every task in the batch lands, or none does. Every spec's
        ``.subject`` / ``.description`` / ``.blocked_by`` is read BEFORE any
        fragment is built (duck-typed attribute access via
        :class:`TaskSpecLike` — a spec object missing a required attribute
        raises BEFORE this method has touched the store, preserving
        all-or-nothing even for a malformed caller-supplied spec); the ledger
        stays KEY-AGNOSTIC (temp-key resolution is a dispatcher concern per the
        design — ``blocked_by`` here is already-resolved, real or pass-through,
        ids). Typed structurally (:class:`TaskSpecLike`, not nominally
        :class:`TaskSpec`) so a duck-typed caller-supplied object satisfying
        just those three attributes is interchangeable with a real
        :class:`TaskSpec` instance.

        ``ids`` is an optional caller-supplied parallel sequence, positionally
        aligned with ``specs``: caller-supplied ids let the DISPATCHER
        pre-mint every id and wire sibling ``blocked_by`` references to them
        before the single atomic write, so the WHOLE batch — dependency-
        chained or not — lands in this one call. When omitted (``None``), the
        ledger mints internally exactly as before; every existing ledger
        contract test (which never passes ``ids``) is unaffected.

        Args:
            specs: The task specifications to create (non-empty).
            created_by: The identity creating the batch, recorded in every
                spec's ``provenance`` (mirrors :meth:`create_task`).
            ids: Optional caller-minted ids, positionally aligned with
                ``specs``. Omitted ⇒ the ledger mints (``uuid4().hex`` per
                spec).

        Returns:
            The newly created tasks' opaque ids, positionally aligned with
            ``specs``.

        PACKET 04b-1 mirrors every item's ``blocked_by`` onto the ``blocks`` edge INSIDE
        that same transaction, and pre-checks the whole batch first. ⚠ **Every CREATE is
        emitted before every RELATE**, which is a correctness requirement rather than a
        tidiness one: ``ENFORCED`` demands both endpoints EXIST at RELATE time, and a
        batch may reference a sibling FORWARD in its own order (which is exactly what the
        dispatcher produces once it resolves temp keys against pre-minted ids), so
        interleaving ``CREATE_0, RELATE_0, CREATE_1`` would have item 0's edge reject an
        endpoint the very next statement was about to create and roll the whole batch back.
        A blocker naming an id INSIDE the batch is therefore legal and is resolved by the
        transaction itself, never by the pre-check.

        Args:
            specs: The task specifications to create (non-empty).
            created_by: The identity creating the batch, recorded in every
                spec's ``provenance`` (mirrors :meth:`create_task`).
            ids: Optional caller-minted ids, positionally aligned with
                ``specs``. Omitted ⇒ the ledger mints (``uuid4().hex`` per
                spec).

        Returns:
            The newly created tasks' opaque ids, positionally aligned with
            ``specs``.

        Raises:
            ValueError: ``specs`` is empty, or ``ids`` is given and its
                length does not match ``specs``.
            UnknownBlockerError: An item's ``blocked_by`` entry names no task row — and
                none in this batch either — or names a SUPERSEDED one. The refusal names
                every offending entry WITH the item that carried it, because an agent
                holding a twenty-item batch cannot otherwise tell which item to edit.
            TaskCycleError: The batch would close a ``blocked_by`` cycle, among its own
                ids or through PERSISTED rows.
            TaskLedgerError: The blocker-existence read itself failed — a store fault,
                classified into this ledger's vocabulary rather than served raw.
        """
        if not specs:
            raise ValueError("create_many requires a non-empty list of specs")
        if ids is not None and len(ids) != len(specs):
            raise ValueError(
                f"create_many 'ids' must align positionally with 'specs' — "
                f"got {len(ids)} ids for {len(specs)} specs"
            )
        minted_ids = [
            ids[index] if ids is not None else uuid4().hex for index in range(len(specs))
        ]
        dependencies = [list(dict.fromkeys(spec.blocked_by or ())) for spec in specs]
        within_batch = set(minted_ids)
        await self._reject_unusable_blockers(
            [
                (entry, f"{entry} (item {index})")
                for index, entries in enumerate(dependencies)
                for entry in entries
                if entry not in within_batch
            ]
        )
        await self._refuse_a_cycle(dict(zip(minted_ids, dependencies, strict=True)))

        now = datetime.now(UTC)
        creates: list[TxnFragment] = []
        pairs: list[tuple[str, str]] = []
        for index, spec in enumerate(specs):
            content = self._new_task_content(
                spec.subject, spec.description, dependencies[index], created_by, now
            )
            creates.append(self._create_fragment(index, minted_ids[index], content))
            pairs.extend((blocker, minted_ids[index]) for blocker in dependencies[index])
        await self._apply([*creates, self._relate_fragment(pairs)])
        return minted_ids

    # -- the blocks mirror, the pre-check and the acyclicity guard -----------

    @staticmethod
    def _create_fragment(index: int, task_id: str, content: dict[str, Any]) -> TxnFragment:
        """ONE task row's ``CREATE``, param-namespaced so ``compose`` never collides."""
        id_param = _CREATE_MANY_ID_PARAM_FMT.format(index=index)
        content_param = _CREATE_MANY_CONTENT_PARAM_FMT.format(index=index)
        return TxnFragment(
            statements=[
                f"CREATE type::record('{TASK_TABLE}', ${id_param}) CONTENT ${content_param}"
            ],
            params={id_param: task_id, content_param: content},
        )

    @staticmethod
    def _relate_fragment(pairs: Sequence[tuple[str, str]]) -> TxnFragment:
        """The ``blocks`` mirror: one ``RELATE`` per ``(blocker, blocked task)`` pair.

        Direction is escalation **E-1**'s — ``RELATE $blocker->blocks->$task``, so ``in``
        is the blocker and ``out`` is the task that waits. It reads as English, and it
        puts the NEWLY-CREATED row on the ``out`` side, the side packet 04a MEASURED
        resolves inside an uncommitted transaction.

        Endpoints are BOUND ``RecordID`` objects: ``RELATE type::record(..)->e->…`` is a
        PARSE ERROR and a bare ``str`` endpoint is rejected loudly (store reference §4/§7).
        An EMPTY ``pairs`` yields a fragment with no statements at all, so a create with no
        dependencies pays for no edge machinery — and never writes an edge to nothing.
        """
        statements: list[str] = []
        params: dict[str, Any] = {}
        for index, (blocker, blocked) in enumerate(pairs):
            from_param = _RELATE_FROM_PARAM_FMT.format(index=index)
            to_param = _RELATE_TO_PARAM_FMT.format(index=index)
            statements.append(
                f"RELATE ${from_param}->{BLOCKS_RELATION}->${to_param}"
            )
            params[from_param] = RecordID(TASK_TABLE, blocker)
            params[to_param] = RecordID(TASK_TABLE, blocked)
        return TxnFragment(statements=statements, params=params)

    async def _reject_unusable_blockers(
        self, identities: Sequence[tuple[str, str]]
    ) -> None:
        """Refuse, by name, every ``blocked_by`` entry that is not a USABLE task row.

        Routes through the SHARED row-existence policy (lead ruling **L3**) — the same
        implementation packet 04a's agent verbs use, parameterised by table and
        vocabulary. A ``reject_unknown_tasks`` sibling would have been copy #2 of that
        policy, which is #102's shape; the DECISION lives there and only there, and this
        method supplies the vocabulary and the error class its own callers catch.

        ⚠ **A FAILED CHECK IS NOT AN ABSENT ROW** (escalation **ESC-3**, ruled reading B).
        *"These ids name no task row"* is a FACT about the data; serving it when the check
        never RAN is a false clear wearing the same bytes, and a caller told its blocker
        does not exist goes and creates a duplicate. So a store rejection during the
        pre-check is CLASSIFIED into this ledger's vocabulary — never re-raised with the
        seam's ``(unspecified rejection); see the server log`` body, which an agent cannot
        tell from a broken tool (ruling **T2**), and never laundered into the phantom
        refusal. It also FAILS CLOSED: nothing is written either way.

        Args:
            identities: ``(blocker id, rendered identity)`` pairs. The rendering carries
                the LOCUS on the batch path (``<id> (item n)``) — without it an agent
                holding a twenty-item batch cannot tell which item carried the bad id,
                and a value appearing in two items makes the first retry a coin flip —
                and is the BARE id on the single-task path, where there is no item to
                name and ``abc (abc)`` would teach that a task has a name equal to its id.
        """
        if not identities:
            return
        try:
            await reject_unknown_rows(
                self._query,
                TASK_TABLE,
                identities,
                noun=_BLOCKER_NOUN,
                remedy=_BLOCKER_REMEDY,
                error=UnknownBlockerError,
                projection=(_COL_SUPERSEDED_BY,),
                disqualified=_superseded_blocker_clause,
            )
        except UnknownBlockerError:
            raise
        except SurrealStoreError as error:
            named = ", ".join(sorted({identity for _row_id, identity in identities}))
            raise TaskLedgerError(
                f"could not check the blocked_by entries {named} against the task "
                f"ledger: the existence read was REJECTED by the store, so the check "
                f"never ran and NOTHING was created. This is a store fault, not a bad "
                f"id — the ids may be perfectly good; retry, and escalate if it persists"
            ) from error

    async def _refuse_a_cycle(self, pending: Mapping[str, Sequence[str]]) -> None:
        """Refuse a write that would put one of ``pending``'s tasks on a ``blocked_by`` cycle.

        ⚠⚠ **THE WALK IS OVER THE ``blocked_by`` COLUMN, CLIENT-SIDE, AND IT CANNOT BE THE
        ENGINE'S SELF-REACH OPERATOR.** The reason is structural and it is caused by this
        packet's own guard: a cycle CLOSES on a dependency naming a task that does not
        exist yet, and ``ENFORCED`` rejects a ``RELATE`` to a task that does not exist — so
        that link can only ever be a COLUMN, there is no ``blocks`` edge on it, and any
        engine traversal of the edge returns *"acyclic"*. The column is also the RIGHT
        thing to walk rather than merely the possible one: the claim CAS reads
        ``blocked_by``, so a COLUMN cycle is what makes a task unclaimable forever, which
        is the harm this guard exists to prevent.

        ⚠ **AND IT COMPOSES WITH RULING R7:** a client-side walk over a chain of depth N
        is N reads, and R7 puts exactly that shape inside ONE snapshot — so the graph
        arrives in ONE round trip, bounded by the pending dependency's ANCESTOR CLOSURE
        (ESC-1 / FORK A, :meth:`_bounded_dependency_graph`) rather than seeded with the
        whole task table OR even the whole dependency-bearing backlog — either of which
        reintroduces #253 on the write path, invisibly: one round trip says nothing about
        how many rows it reads.

        A cycle among rows this call did NOT write is a pre-existing DATA defect that
        ``ensure_ready``'s backfill has already RECORDED; refusing a caller for it would
        make an unrelated legacy loop block every future create. So such a loop is stepped
        over — one edge at a time, so a DIFFERENT loop through the same rows still
        surfaces — and only a cycle a ``pending`` task actually lies on is refused. The
        step-over drop-loop is UNCHANGED by ESC-1 (variant D): it routes through the shared
        ``find_blocked_by_cycle`` (R6), and it is what keeps the guard SOUND when a legacy
        cycle coexists with the minted one in the bounded closure (MP-1) — a single-witness
        check would return the legacy cycle first and wave the minted create through.

        Args:
            pending: ``{the id about to be created: its deduped blocked_by}``.
        """
        if not any(pending.values()):
            return
        seeds = {blocker for blockers in pending.values() for blocker in blockers}
        graph: dict[str, set[str]] = {
            node: set(refs)
            for node, refs in (await self._bounded_dependency_graph(seeds)).items()
        }
        for task_id, blockers in pending.items():
            graph[task_id] = set(blockers)
        minted = set(pending)
        while True:
            cycle = find_blocked_by_cycle(graph)
            if cycle is None:
                return
            if minted.intersection(cycle):
                raise_cycle_refusal(noun=CYCLE_NOUN_PERSISTED_IDS, cycle=cycle)
            if not _drop_one_cycle_edge(graph, cycle):
                return

    async def _bounded_dependency_graph(
        self, seeds: Iterable[str]
    ) -> dict[str, list[str]]:
        """The ``blocked_by`` graph BOUNDED to the ancestor CLOSURE of ``seeds``.

        ESC-1 / FORK A (packet 04b-3). ``seeds`` are the pending task's persisted blockers.
        The write guard must not scale with the whole dependency-bearing backlog (#253 on
        the write path), and it does not need to: every row that could close a cycle THROUGH
        a pending task ``N`` is an ANCESTOR of one of ``N``'s blockers — a cycle
        ``N -> a1 -> … -> ak -> N`` has ``ak.blocked_by ∋ N``, so ``ak`` is an ancestor of
        ``N`` — hence reachable upstream over the persisted ``blocks`` EDGE. That is FORK A's
        soundness proof, resting on ESC-1's measured YES that every persisted ancestor is
        edge-reachable after ``ensure_ready``. Bounding to the closure therefore loses no
        cycle; it is sound, not a heuristic.

        ⚠ **The COLUMN is KEPT, never abandoned for the edge.** The edge walk only BOUNDS
        which rows to read; the cycle is read from the ``blocked_by`` COLUMN, because the
        closing link of a would-be cycle names a task that does not exist yet, ``ENFORCED``
        forbids that ``RELATE`` (store reference §4), so it can only ever be a COLUMN and an
        edge-only read returns *"acyclic"* — the reason
        ``test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED`` fails
        an edge-only guard.

        It is ONE round trip whatever the chain's depth (R7): the seeds, their bounded
        ancestor closure walked over ``blocks`` (a ``GraphEdgeScan`` per seed, cost bounded
        by the closure — store reference §4, and ``+collect`` with an explicit depth bound +
        ``TIMEOUT`` per §4's recursive-path rule), and every closure member's column all
        arrive together. A phantom seed (a ``create_many`` sibling ref with no row yet)
        contributes no row and no error — the ESC-1 residue, overlaid by the caller instead.

        ``record::id(id)`` decodes the id, never a hand-rolled ``str(row["id"]).split(":")``
        — right for ``task:abc`` and WRONG for a uuid-shaped id, which the SDK renders
        ``task:⟨0199c4f1-…⟩`` (store reference §7, finding #248).

        Args:
            seeds: The pending task's blocker ids to seed the ancestor-closure walk from.
        """
        starts = [RecordID(TASK_TABLE, seed) for seed in sorted(seeds)]
        rows = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_BLOCKED_BY} "
                f"FROM {TASK_TABLE} WHERE {_ID_KEY} IN array::distinct(array::flatten("
                f"array::concat([${_CLOSURE_START_PARAM}], (SELECT VALUE "
                f"@.{{1..{TASK_BLOCKER_MAX_DEPTH}+collect}}"
                f"(<-{BLOCKS_RELATION}<-{TASK_TABLE}) "
                f"FROM ${_CLOSURE_START_PARAM})))) TIMEOUT {_TRAVERSAL_TIMEOUT}",
                {_CLOSURE_START_PARAM: starts},
            )
        )
        return {
            str(row.get(_ID_KEY)): [
                str(blocker) for blocker in (row.get(_COL_BLOCKED_BY) or ())
            ]
            for row in rows
        }

    async def transitive_blockers(
        self, task_id: str, *, max_depth: int | None = None
    ) -> TransitiveBlockers:
        """Every task ``task_id`` is transitively waiting on, HONEST at its bound.

        Serves the UPSTREAM reach over the ``blocks`` EDGE — what this task is waiting on,
        which is what a critical-path render needs — deduplicated and ordered by proximity,
        so a TRUNCATED answer is still a valid **FLOOR**: the ids served are complete at
        every depth the walk reached, i.e. *"at least these must resolve first"*. Without
        that property a partial answer would be indistinguishable from an arbitrary sample
        and a consumer could not use it at all.

        **SCOPE, stated as a FACT rather than as a disclaimer.** It answers *"the tasks
        reachable upstream over ``blocks`` EDGES from this task, to a depth of at most
        ``max_depth_used``, as of this read"*. After ``ensure_ready``'s backfill the edge
        set mirrors the ``blocked_by`` COLUMN for every entry naming a live task row, so
        the two agree — with ONE permanent residue: a legacy ``blocked_by`` entry that
        names NO task row at all (a **phantom**) can never carry an edge, because
        ``ENFORCED`` forbids it and the backfill therefore skips it. Such an entry is in
        the column and NOT in this answer. It still blocks the task: the claim CAS counts
        it and refuses forever, so a phantom-blocked row is never served as claimable.

        Args:
            task_id: The task whose upstream blockers to walk.
            max_depth: The walk's depth bound; omitted ⇒ :data:`TASK_BLOCKER_MAX_DEPTH`.
                Must be at least 1 and strictly below :data:`ENGINE_RECURSION_CEILING`.

        Returns:
            A :class:`TransitiveBlockers` carrying the ids, whether the walk was
            ``truncated``, and the bound it actually ran at.

        Raises:
            TaskLedgerError: ``max_depth`` is out of range (refused CLIENT-SIDE, naming
                the value AND the range — no statement reaches the engine, whose own
                complaint the seam's hygiene would withhold), or the traversal's read was
                rejected by the store (classified, never served as a partial answer).
            TaskNotFoundError: ``task_id`` names no task row. An id that names nothing and
                an id with no blockers are two different questions, and ``[]`` cannot be
                the answer to both.
        """
        depth = TASK_BLOCKER_MAX_DEPTH if max_depth is None else max_depth
        if isinstance(depth, bool) or not isinstance(depth, int) or not (
            1 <= depth < ENGINE_RECURSION_CEILING
        ):
            raise TaskLedgerError(
                f"max_depth={depth} is out of range — it must be at least 1 and strictly "
                f"below the engine's recursion ceiling of {ENGINE_RECURSION_CEILING}"
            )
        # TRUNCATION IS MEASURED, NEVER INFERRED. The engine truncates SILENTLY at its
        # bound (probe §5.3: 256 of 299 nodes, no error, no signal), and a build that
        # inferred it from ``len(ids) >= max_depth`` cannot tell a complete answer from a
        # cut one at the boundary — it would tell every caller with a full-depth graph
        # that its critical path is incomplete. So the SAME statement also collects at
        # ONE DEEPER bound and the two reaches are compared; that is why the public range
        # stops strictly below the engine's ceiling rather than at it.
        statement = (
            f"SELECT @.{{1..{depth}+collect}}(<-{BLOCKS_RELATION}<-{TASK_TABLE}).{_ID_KEY} "
            f"AS {_TRAVERSAL_WITHIN_KEY}, "
            f"@.{{1..{depth + 1}+collect}}(<-{BLOCKS_RELATION}<-{TASK_TABLE}).{_ID_KEY} "
            f"AS {_TRAVERSAL_PROBE_KEY} "
            f"FROM ${_TRAVERSAL_START_PARAM} TIMEOUT {_TRAVERSAL_TIMEOUT}"
        )
        try:
            rows = self._as_rows(
                await self._query(
                    statement, {_TRAVERSAL_START_PARAM: RecordID(TASK_TABLE, task_id)}
                )
            )
        except SurrealStoreError as error:
            # A traversal that FAILED mid-flight is a different world from one that hit
            # its bound, and returning what we had — or an empty result — would render
            # bytes a consumer cannot tell from "this task has no blockers". The ledger
            # cannot name the engine's own reason (the hygiene boundary withholds it, and
            # a guessed one would be a fabrication), so it names what it CAN: the
            # operation, the task, the bound it ran at, and the recovery.
            raise TaskLedgerError(
                f"the upstream blocker walk for task {render_attributed(task_id)} at max_depth={depth} "
                f"was REJECTED by the store, so NO answer is served — a partial reach "
                f"would be indistinguishable from a complete one. Retry, or retry at a "
                f"smaller max_depth if the graph is deep"
            ) from error
        if not rows:
            raise TaskNotFoundError(f"no task with id {render_attributed(task_id)}")
        within = [str(record) for record in self._traversal_ids(rows[0], _TRAVERSAL_WITHIN_KEY)]
        deeper = {str(record) for record in self._traversal_ids(rows[0], _TRAVERSAL_PROBE_KEY)}
        return TransitiveBlockers(
            ids=within,
            truncated=deeper != set(within),
            max_depth_used=depth,
        )

    @staticmethod
    def _traversal_ids(row: Mapping[str, Any], key: str) -> list[str]:
        """Decode one traversal projection's node ids.

        ``str(record.id)`` for a ``RecordID`` — never ``str(record).split(":")``, which is
        right for ``task:abc`` and WRONG for the bracketed rendering the SDK gives a
        uuid-shaped id (store reference §7). A served id that ``get_task`` cannot resolve
        is worse than no answer: an agent will use it, and every call it makes with it
        fails.
        """
        return [
            str(node.id) if isinstance(node, RecordID) else str(node)
            for node in (row.get(key) or ())
        ]

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
            raise TaskNotFoundError(f"no task with id {render_attributed(task_id)}")
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
            updated_at=self._to_aware_utc_ceiling(row.get(_COL_UPDATED_AT)),
            summary=row.get(_COL_SUMMARY),
            report_path=row.get(_COL_REPORT_PATH),
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

    @classmethod
    def _to_aware_utc_ceiling(cls, value: Any) -> datetime | None:
        """Decode a SERVER-``time::now()``-stamped column, rounded UP one microsecond.

        PKT-06 §1 fix (live-verified against spike-surreal): SurrealDB's
        ``time::now()`` carries nanosecond precision server-side, but Python's
        ``datetime`` — and this SDK's CBOR decode — can only represent
        microseconds, so the decoded value is a TRUNCATED (rounded DOWN)
        approximation of the true stored instant. Re-binding that exact
        decoded value as a later query's ``$since`` parameter therefore
        compares LESS than the still-stored original (``stored > $since``
        stays true even for the row the cursor was read FROM), silently
        breaking :meth:`updated_since`'s advertised EXCLUSIVE boundary for any
        cursor round-tripped through it. Rounding the decoded value UP by one
        whole microsecond (the finest increment Python can represent)
        guarantees it is never smaller than the true stored instant,
        restoring the exclusive-boundary property. Applied ONLY where a
        decoded value may later be REBOUND as a store parameter
        (:attr:`Task.updated_at`) — never to ``created_at``, a Python-
        authored value with no server-side precision to lose. Mirrors the
        design's already-ACCEPTED microsecond-tie residual (R1): the
        vanishingly rare case of a second, genuinely-independent event
        landing inside this same sub-microsecond window is a missed *notice*
        on the NEXT poll, never lost data (``action=query`` still serves it).
        """
        aware = cls._to_aware_utc(value)
        if aware is None:
            return None
        return aware + timedelta(microseconds=1)

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
