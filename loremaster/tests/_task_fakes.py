"""ADVERSARIAL in-memory ``FakeTaskLedger`` — the P7 task-ledger fake-vs-real
parity pin (mirrors the house style of ``_surreal_fakes.py``).

``test_task_ledger.py``'s own ``task_ledger_factory`` fixture is parametrized
over BOTH the real SurrealDB-backed ``TaskLedger`` and this fake, so the exact
same contract suite runs against both. That parity pin is only as good as this
fake is UNFRIENDLY: a fake that quietly promises more than production (stable
insertion order, a lucky non-atomic CAS, a shared mutable ``Task`` reference)
would let a consumer bug pass green here and then break for real. Each
adversarial property below exists to catch one such bug:

1. :meth:`FakeTaskLedger.query_tasks` returns rows in a DETERMINISTIC but
   NON-insertion order (reverse-sorted by opaque id) — production SurrealDB
   makes no ordering promise, so a consumer assuming "creation order" breaks
   here exactly as it would against the real store.
2. Every public ``async`` method opens with ``await asyncio.sleep(0)`` — a
   real event-loop yield point, so concurrent callers (``TestClaimRace``)
   actually interleave the way two live socket-backed calls would, rather than
   running start-to-finish back-to-back because nothing ever awaited.
3. :meth:`FakeTaskLedger.claim_task` yields (``sleep(0)``) BEFORE its
   compare-and-set check, then runs the check-and-mutate with NO ``await``
   between them. The race window is honestly open (two racers can both reach
   the check before either mutates); the CAS itself is honestly atomic
   (asyncio's cooperative single-thread scheduling means nothing can preempt a
   stretch of code with no ``await`` in it) — the same shape production's
   single-transaction ``BEGIN … COMMIT`` claim gets from the server, not a
   fake-only accident.
4. Every returned :class:`~loremaster.tasks.Task` is a FRESH
   ``model_copy(deep=True)`` — production deserializes a fresh row on every
   call; a consumer that mutates a returned ``Task`` (e.g. appends to
   ``blocked_by``) must never corrupt this fake's store.
5. Task ids are opaque ``uuid4().hex`` strings, never ``task-1``/``task-2``
   shapes a consumer could accidentally sort or index by.

Fidelity: :class:`~loremaster.tasks.Task`, :class:`~loremaster.tasks.ClaimResult`,
:class:`~loremaster.tasks.TaskStatus` and every exception are IMPORTED from
``loremaster.tasks`` — never redefined here, so this fake can never drift from
the real value objects it stands in for. The six-status vocabulary and the
legal-transition matrix are the contract ``test_task_ledger.py`` itself pins
(see that module's ``STATUS_*`` / ``LEGAL_TRANSITIONS`` constants); this file
keeps its OWN copy of both (exactly as ``test_task_ledger.py`` does), because a
fake importing its state machine FROM the test it is graded against would be
circular, not independent, verification.

Two :class:`FakeTaskLedger` instances built over the SAME
:class:`FakeTaskDatabase` are two independent "connections" to one store —
mirroring the single SurrealDB database every real ``TaskLedger`` handle
shares — which is what makes ``TestClaimRace`` (two racing handles) and
``TestFleetVisibility`` (a second handle reading the first's writes)
meaningful against this fake at all.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from loremaster.tasks import (
    ClaimResult,
    IllegalTransitionError,
    Task,
    TaskNotFoundError,
    TaskStatus,
)

# --- the domain's status vocabulary + legal-transition matrix ---------------
# A DELIBERATE local copy of the same vocabulary/matrix ``test_task_ledger.py``
# pins (see that module's ``STATUS_*`` / ``LEGAL_TRANSITIONS`` constants) — an
# independent implementation of the contract, not a shortcut that imports the
# test's own fixtures. Typed against ``TaskStatus`` (imported, never
# redefined) so every constant here is statically a legal ``Task.status``
# value.
STATUS_OPEN: TaskStatus = "open"
STATUS_CLAIMED: TaskStatus = "claimed"
STATUS_IN_PROGRESS: TaskStatus = "in_progress"
STATUS_DONE: TaskStatus = "done"
STATUS_BLOCKED: TaskStatus = "blocked"
STATUS_WONTFIX: TaskStatus = "wontfix"

ALL_STATUSES: frozenset[TaskStatus] = frozenset(
    {STATUS_OPEN, STATUS_CLAIMED, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_BLOCKED, STATUS_WONTFIX}
)

# The two TERMINAL statuses — also the exact set that "resolves" a blocker.
TERMINAL_STATUSES: frozenset[TaskStatus] = frozenset({STATUS_DONE, STATUS_WONTFIX})

# The full legal transition matrix (verbatim shape of the contract's own
# ``LEGAL_TRANSITIONS``): everything NOT listed here is illegal, including the
# claim-only ``open -> claimed`` edge and every edge out of a terminal status.
LEGAL_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset(
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


@dataclass
class FakeTaskDatabase:
    """The shared in-memory task table two or more ``FakeTaskLedger`` handles
    read/write.

    Mirrors the single SurrealDB database every real ``TaskLedger`` connection
    shares: build several :class:`FakeTaskLedger` instances over the SAME
    :class:`FakeTaskDatabase` and they behave like several independent
    sessions against one fleet-visible store (the exact topology
    ``TestClaimRace`` and ``TestFleetVisibility`` require).
    """

    tasks: dict[str, Task] = field(default_factory=dict)


def _utc_now() -> datetime:
    """A tz-aware UTC timestamp — every stamped time in this fake uses this."""
    return datetime.now(UTC)


class FakeTaskLedger:
    """ADVERSARIAL in-memory stand-in for :class:`~loremaster.tasks.TaskLedger`.

    See the module docstring for the five deliberate adversarial behaviours.
    Every method's PUBLIC surface (name, parameters, return type, raised
    exceptions) matches :class:`~loremaster.tasks.TaskLedger` exactly; only
    the storage is a plain in-memory dict rather than a SurrealDB connection.
    """

    def __init__(self, *, db: FakeTaskDatabase | None = None) -> None:
        self.db = db if db is not None else FakeTaskDatabase()

    # -- lifecycle ----------------------------------------------------------

    async def ensure_ready(self) -> None:
        """No-op (the fake holds no connection to establish)."""
        await asyncio.sleep(0)

    async def close(self) -> None:
        """No-op (the fake holds no connection to close)."""
        await asyncio.sleep(0)

    # -- internal helpers -----------------------------------------------------

    def _require(self, task_id: str) -> Task:
        """The LIVE (mutable, store-owned) row for ``task_id``, or raise.

        Never returned directly to a caller — every public method hands back
        ``.model_copy(deep=True)`` of whatever this returns, so the store's own
        reference is never exposed for a caller to accidentally corrupt.
        """
        task = self.db.tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"no task with id {task_id!r}")
        return task

    def _is_blocked(self, task: Task) -> bool:
        """Whether ``task`` is genuinely blocked: fail-closed on EVERY entry.

        A blocker resolves once its status is terminal (done/wontfix). A
        ``blocked_by`` entry naming an id that was NEVER minted (not present in
        the store at all) counts as UNRESOLVED — the same fail-closed default
        ``claim_task`` and ``query_tasks``'s ``blocked`` partition both apply,
        from this one shared implementation.
        """
        for blocker_id in task.blocked_by:
            blocker = self.db.tasks.get(blocker_id)
            if blocker is None or blocker.status not in TERMINAL_STATUSES:
                return True
        return False

    # -- create / read --------------------------------------------------------

    async def create_task(
        self,
        subject: str,
        description: str,
        *,
        blocked_by: list[str] | None = None,
        created_by: str,
    ) -> str:
        await asyncio.sleep(0)
        task_id = uuid4().hex  # opaque, non-sequential (adversarial property 5)
        now = _utc_now()
        task = Task(
            id=task_id,
            subject=subject,
            description=description,
            status=STATUS_OPEN,
            owner=None,
            claimed_at=None,
            # ``blocked_by`` is a SET of dependencies: a DUPLICATE id must not
            # double-count against the claim gate's eligibility check, so it is
            # deduped (order-preserving) at birth — the same normalisation the
            # real store must apply for the claim gate and query partition to agree.
            blocked_by=list(dict.fromkeys(blocked_by)) if blocked_by is not None else [],
            provenance={"created_by": created_by, "created_at": now.isoformat(), "events": []},
            superseded_by=None,
            created_at=now,
        )
        self.db.tasks[task_id] = task
        return task_id

    async def get_task(self, task_id: str) -> Task:
        await asyncio.sleep(0)
        return self._require(task_id).model_copy(deep=True)

    async def query_tasks(
        self,
        *,
        status: str | None = None,
        owner: str | None = None,
        blocked: bool | None = None,
    ) -> list[Task]:
        await asyncio.sleep(0)
        rows = list(self.db.tasks.values())
        if status is not None:
            rows = [task for task in rows if task.status == status]
        if owner is not None:
            rows = [task for task in rows if task.owner == owner]
        if blocked is not None:
            rows = [task for task in rows if self._is_blocked(task) == blocked]
        # Deterministic NON-insertion order (adversarial property 1): reverse
        # sort by opaque id, never the dict's insertion order.
        rows.sort(key=lambda task: task.id, reverse=True)
        return [task.model_copy(deep=True) for task in rows]

    # -- the atomic claim -----------------------------------------------------

    async def claim_task(self, task_id: str, owner: str) -> ClaimResult:
        # The race window is honestly OPEN before the check (adversarial
        # property 3): two concurrent callers can both reach this point before
        # either one mutates.
        await asyncio.sleep(0)
        task = self._require(task_id)
        # --- the compare-and-set: NO ``await`` between check and mutation ---
        eligible = (
            task.superseded_by is None
            and task.status == STATUS_OPEN
            and task.owner is None
            and not self._is_blocked(task)
        )
        if not eligible:
            return ClaimResult(claimed=False, task=task.model_copy(deep=True))
        now = _utc_now()
        task.status = STATUS_CLAIMED
        task.owner = owner
        task.claimed_at = now
        task.provenance.setdefault("events", []).append(
            {"actor": owner, "action": "claim", "at": now.isoformat()}
        )
        # --- end compare-and-set ---
        return ClaimResult(claimed=True, task=task.model_copy(deep=True))

    # -- state machine ---------------------------------------------------------

    async def transition(self, task_id: str, status: str, *, actor: str) -> Task:
        await asyncio.sleep(0)
        task = self._require(task_id)
        current_status = task.status
        legal = (
            task.superseded_by is None
            and status in ALL_STATUSES
            and (current_status, status) in LEGAL_TRANSITIONS
        )
        if not legal:
            raise IllegalTransitionError(
                f"illegal transition for task {task_id!r} from {current_status!r} to {status!r}"
            )
        target_status = cast(TaskStatus, status)
        task.status = target_status
        if target_status == STATUS_OPEN:
            # Re-entering ``open`` always means unowned/unclaimed (the ONLY
            # ways into ``open`` are creation and this release edge) — the
            # invariant ``claim_task`` relies on when it checks ``owner is
            # None`` alongside ``status == open``.
            task.owner = None
            task.claimed_at = None
        now = _utc_now()
        task.provenance.setdefault("events", []).append(
            {"actor": actor, "action": "transition", "to": target_status, "at": now.isoformat()}
        )
        return task.model_copy(deep=True)

    # -- supersession ------------------------------------------------------

    async def supersede_task(
        self,
        task_id: str,
        *,
        subject: str,
        description: str,
        created_by: str,
    ) -> str:
        await asyncio.sleep(0)
        old_task = self._require(task_id)
        # A superseded task is terminal-like: it can never be superseded again,
        # sequentially OR as the racing loser. This check sits AFTER the sleep(0)
        # yield (so two racers both open the window) and BEFORE any store
        # mutation, with NO ``await`` between it and the stamp below — so the
        # first racer stamps ``superseded_by`` atomically and the second reads the
        # now-stamped row and fails. Exactly one successor is ever minted.
        if old_task.superseded_by is not None:
            raise IllegalTransitionError(
                f"task {task_id!r} is already superseded by "
                f"{old_task.superseded_by!r} and cannot be superseded again"
            )
        new_id = uuid4().hex
        now = _utc_now()
        successor = Task(
            id=new_id,
            subject=subject,
            description=description,
            status=STATUS_OPEN,
            owner=None,
            claimed_at=None,
            blocked_by=[],
            provenance={"created_by": created_by, "created_at": now.isoformat(), "events": []},
            superseded_by=None,
            created_at=now,
        )
        self.db.tasks[new_id] = successor
        old_task.superseded_by = new_id
        old_task.provenance.setdefault("events", []).append(
            {"actor": created_by, "action": "supersede", "successor": new_id, "at": now.isoformat()}
        )
        return new_id
