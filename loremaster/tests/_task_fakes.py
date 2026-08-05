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

PKT-06 addendum (rollup / create_many / done-summary): the real ``Task``
pydantic model is imported, never redefined (see the Fidelity note above) —
but PKT-06's contract adds THREE fields (``updated_at``, ``summary``,
``report_path``) production has not landed on ``Task`` yet, and this file may
never touch production. Rather than fork a second ``Task`` shape, this fake
injects those fields onto the REAL, imported ``Task`` instances via
``object.__setattr__`` (bypasses pydantic's ``extra="forbid"`` ``__setattr__``
guard the same way ``Task.model_copy(update={...})`` does — both write
directly into the instance ``__dict__``, verified live against this repo's
pinned pydantic: a forbidden-extra ``Task(..., summary=...)`` construction
still raises, but ``object.__setattr__(task, "summary", ...)`` on an existing
instance succeeds and round-trips through ``model_copy(deep=True)``). This
keeps the fake's ``Task`` instances the SAME class as production's — never a
parallel value object — while still being constructible today, before the
builder phase adds these columns for real.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from loremaster.tasks import (
    ENGINE_RECURSION_CEILING,
    TASK_BLOCKER_MAX_DEPTH,
    ClaimResult,
    IllegalTransitionError,
    Task,
    TaskLedgerError,
    TaskNotFoundError,
    TaskStatus,
    TransitiveBlockers,
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


# PKT-06 §4 (done-summary/report_path): the cap on a done-transition's
# ``summary``, a DELIBERATE local copy of the design's decided
# ``_DONE_SUMMARY_MAX_CHARS`` constant (same independence rationale as the
# status vocabulary above — this fake enforces the CONTRACT, not a value
# imported from the not-yet-built production module).
_DONE_SUMMARY_MAX_CHARS = 300


@dataclass
class _FakeTaskActivityWindow:
    """Duck-typed stand-in for the not-yet-built ``loremaster.tasks.
    TaskActivityWindow`` — ``rows``/``total``, nothing more. Never imports the
    production class (it does not exist yet); a contract test asserts on
    these two attributes, which is exactly what the real pydantic model will
    also expose, so the fake and the real return value are
    attribute-compatible without a shared base.
    """

    rows: list[Task]
    total: int


def _validate_done_extras(
    task_id: str, target: str, summary: str | None, report_path: str | None
) -> None:
    """PKT-06 §4: enforce the done-transition's ``summary``/``report_path`` rules.

    Checked AFTER the state-machine edge is confirmed legal and BEFORE any
    mutation — mirrors the design note's ordering exactly, including the
    verbatim error texts (this fake IS the contract those texts are pinned
    against). Rule 4 (report_path's own non-empty/single-line guard) mirrors
    rule 2's template verbatim with 'summary' swapped for 'report_path' — the
    design's "mirrored text with 'report_path'" phrase, read as literally the
    SAME templated message production is expected to share between the two
    fields (flagged in the report as the one genuinely underspecified corner
    of an otherwise fully-decided contract).

    Raises:
        IllegalTransitionError: A done-transition's summary/report_path is
            missing, multi-line, or over the length cap.
        ValueError: summary/report_path was given on a NON-done target.
    """
    if target == STATUS_DONE:
        if summary is None or not summary.strip():
            raise IllegalTransitionError(
                f"transition to 'done' for task {task_id!r} requires 'summary' — a "
                f"one-line completion digest (max 300 chars) the rollup serves as "
                f"the fleet's durable completion record; pass report_path= too "
                f"when a report file exists"
            )
        if "\n" in summary or "\r" in summary:
            raise IllegalTransitionError(
                f"task {task_id!r} done-summary must be a single line — put "
                f"detail in the report file and pass its path as report_path="
            )
        if len(summary) > _DONE_SUMMARY_MAX_CHARS:
            raise IllegalTransitionError(
                f"task {task_id!r} done-summary is {len(summary)} chars — the cap "
                f"is 300; tighten it (detail belongs in the report file)"
            )
        if report_path is not None and (
            not report_path.strip() or "\n" in report_path or "\r" in report_path
        ):
            raise IllegalTransitionError(
                f"task {task_id!r} done-report_path must be a single line — put "
                f"detail in the report file and pass its path as report_path="
            )
    elif summary is not None or report_path is not None:
        raise ValueError(
            f"summary/report_path are recorded only on the transition to 'done' "
            f"(got target {target!r}) — omit them here"
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
        limit: int | None = None,
    ) -> list[Task]:
        """The fake's read.

        ⚠ ``limit`` exists here because **operator ruling R5 (2026-07-28)** makes it part of
        ``TaskLedger.query_tasks``' signature and requires the dispatcher to PASS it — and a
        double that does not accept a parameter its production twin takes turns a correct
        build into a ``TypeError`` in every test that drives this fake. That is not a
        hypothetical: it was MEASURED as two red pins in ``test_mcp_server.py`` on a reference
        build of packet 04b-1, disclosed nowhere, and it is why a contract's "removed-behaviour
        inventory" has to survey the DOUBLES as well as the callers.

        ⚠ **THE CAP APPLIES TO THE ANSWER, NEVER TO THE CANDIDATE SCAN** (ruling T1): the
        slice is the LAST thing that happens, after the ``blocked`` partition has been
        computed, so ``limit=5`` with a ``blocked`` filter serves five MATCHING rows rather
        than whatever survives filtering the first five. A fake that sliced earlier would
        teach its consumers the wrong contract, which is the one thing a double must never do.
        """
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
        if limit is not None:
            rows = rows[:limit]
        return [task.model_copy(deep=True) for task in rows]

    async def direct_dependents(self, task_id: str) -> list[str]:
        """The ids of the tasks whose ``blocked_by`` column names ``task_id``.

        ⚠ **ADDED 2026-08-01 (04b-2 wave C, slice C1) AHEAD of the production verb, and
        the reason is a MEASURED one, not a courtesy.**  Ruling **R10(iii)** makes the
        ``supersede`` render warn about the dependents it strands, and the dispatcher
        therefore asks the LEDGER for them — so a double that lacks the method turns a
        CORRECT build into an ``AttributeError`` in every test that drives this fake.  That
        was measured on the C1 reference build (two reds in
        ``test_mcp_server.py::TestTasksTool``), which is the same ripple 04b-1's contract
        hit with ``query_tasks``' ``limit``: a contract's removed-behaviour inventory has
        to survey the DOUBLES as well as the callers.  Green before the production verb
        lands and after it, so a builder meets no red test here.

        ⚠ **ONE HOP, deliberately** — the tasks whose OWN ``blocked_by`` names this id, not
        the transitive downstream reach.  The warning exists to tell a caller which rows to
        re-point; the claim CAS that strands them is itself a strictly one-hop predicate,
        so a transitive answer would name rows the supersession did not strand.
        """
        await asyncio.sleep(0)
        return sorted(
            task.id for task in self.db.tasks.values() if task_id in task.blocked_by
        )

    def _upstream_reach(self, task_id: str, depth: int) -> list[str]:
        """The ids reachable UPSTREAM from ``task_id`` within ``depth`` hops.

        Breadth-first, so the result is ordered by PROXIMITY and a truncated answer is
        still a valid FLOOR — the property
        :meth:`~loremaster.tasks.TaskLedger.transitive_blockers` states about its own
        ``+collect`` closure. ``task_id`` itself appears only if it genuinely lies on a
        cycle, because the walk never seeds it into the seen set.

        ⚠ **A ``blocked_by`` entry naming NO row is SKIPPED, and that is fidelity, not
        laziness.** Production walks the ``blocks`` EDGE, and ``ENFORCED`` forbids an edge
        to a phantom, so such an entry is in the COLUMN and never in the walk's answer
        (that residue is named in ``transitive_blockers``' own scope paragraph). It still
        blocks the task — :meth:`_is_blocked` counts it, fail-closed, exactly as the real
        claim CAS does.
        """
        reached: list[str] = []
        seen: set[str] = set()
        frontier = [task_id]
        for _hop in range(depth):
            next_frontier: list[str] = []
            for current in frontier:
                task = self.db.tasks.get(current)
                if task is None:
                    continue
                for blocker_id in task.blocked_by:
                    if blocker_id in seen or blocker_id not in self.db.tasks:
                        continue
                    seen.add(blocker_id)
                    reached.append(blocker_id)
                    next_frontier.append(blocker_id)
            if not next_frontier:
                break
            frontier = next_frontier
        return reached

    async def transitive_blockers(
        self, task_id: str, *, max_depth: int | None = None
    ) -> TransitiveBlockers:
        """Every task ``task_id`` is transitively waiting on, HONEST at its bound.

        ⚠ **ADDED 2026-08-02 (04b-2 wave C, the C-DEF fix wave) for the reason
        :meth:`direct_dependents` records one slice earlier, and it was MEASURED here
        too, not anticipated:** ``AppContext.tasks(action='blockers')`` asks the LEDGER
        for this walk, so a double lacking the method turns a CORRECT build into an
        ``AttributeError`` — four reds in
        ``test_comms_footer.py::TestTheUNRESOLVABLETeachingIsUSEFULAndStaysOffREADS`` and
        its sibling, on the committed build, once the fixture gap that hid them behind an
        earlier ``ValueError`` was closed. Green with the production verb present, which
        it is.

        The bounds and the value object come FROM ``loremaster.tasks``
        (:data:`~loremaster.tasks.TASK_BLOCKER_MAX_DEPTH`,
        :data:`~loremaster.tasks.ENGINE_RECURSION_CEILING`,
        :class:`~loremaster.tasks.TransitiveBlockers`) rather than being re-declared here
        — the module docstring's Fidelity rule, and load-bearing for this verb in
        particular: ``max_depth_used`` travels back to a RENDER, so a double carrying its
        own private default would serve a number production never would.

        ⚠ **BOUND DISCHARGED 2026-08-04 (#324 R-2).** This method USED to carry no
        fake-vs-real parity pin — the two implementations agreed by CONSTRUCTION (same
        bounds, same value object, same phantom rule, same proximity order) and not by
        MEASUREMENT. ``test_task_ledger.py::TestTransitiveBlockersCycleWalkAgreesFakeVsReal``
        now closes that: it raw-seeds the SAME ``blocks`` cycle in the live store and in
        this fake, walks both, and asserts byte-agreement on ``(ids, truncated,
        max_depth_used)`` (with an injected-drift control) — so a drift in this walk is
        MEASURED, not assumed away. The stated re-open trigger ("the day any pin asserts on
        ids/truncated content through this fake, it needs a parity leg first") is satisfied
        by that pin.
        """
        await asyncio.sleep(0)
        depth = TASK_BLOCKER_MAX_DEPTH if max_depth is None else max_depth
        if (
            isinstance(depth, bool)
            or not isinstance(depth, int)
            or not (1 <= depth < ENGINE_RECURSION_CEILING)
        ):
            raise TaskLedgerError(
                f"max_depth={depth} is out of range — it must be at least 1 and strictly "
                f"below the engine's recursion ceiling of {ENGINE_RECURSION_CEILING}"
            )
        # ``_require`` FIRST: an id naming no row and an id with no blockers are two
        # different questions, and ``[]`` cannot be the answer to both (the real verb
        # raises ``TaskNotFoundError`` for the same reason).
        self._require(task_id)
        # TRUNCATION IS MEASURED, NEVER INFERRED — the same comparison production makes,
        # for the same reason: ``len(ids) >= depth`` cannot tell a complete answer from a
        # cut one at the boundary.
        within = self._upstream_reach(task_id, depth)
        deeper = set(self._upstream_reach(task_id, depth + 1))
        return TransitiveBlockers(
            ids=within, truncated=deeper != set(within), max_depth_used=depth
        )

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
        # PKT-06 §1 (rollup leg 1): a claim is fleet-visible activity — stamp
        # ``updated_at`` inside the same (fake) compare-and-set the design
        # requires of the real guarded CAS. See the module docstring's
        # addendum for why this is an ``object.__setattr__`` injection rather
        # than a declared ``Task`` field.
        object.__setattr__(task, "updated_at", now)
        task.provenance.setdefault("events", []).append(
            {"actor": owner, "action": "claim", "at": now.isoformat()}
        )
        # --- end compare-and-set ---
        return ClaimResult(claimed=True, task=task.model_copy(deep=True))

    # -- state machine ---------------------------------------------------------

    async def transition(
        self,
        task_id: str,
        status: str,
        *,
        actor: str,
        summary: str | None = None,
        report_path: str | None = None,
    ) -> Task:
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
        # PKT-06 §4: the done-summary/report_path rules are checked AFTER the
        # state-machine edge is confirmed legal and BEFORE any mutation.
        _validate_done_extras(task_id, status, summary, report_path)
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
        # PKT-06 §1: every legal transition is fleet-visible activity.
        object.__setattr__(task, "updated_at", now)
        if target_status == STATUS_DONE:
            # PKT-06 §4(d): bound to the done edge ONLY — validated above.
            object.__setattr__(task, "summary", summary)
            object.__setattr__(task, "report_path", report_path)
        return task.model_copy(deep=True)

    # -- rollup / batch (PKT-06) ------------------------------------------------

    async def updated_since(self, since: datetime, *, limit: int) -> _FakeTaskActivityWindow:
        """The rollup's leg-1 read: tasks stamped ``updated_at`` after ``since``.

        Adversarial (mirrors ``query_tasks``'s non-insertion-order property):
        the candidate set is built in REVERSE insertion order BEFORE the real
        ``updated_at`` ASC sort is applied, so a consumer whose "it happened
        to come back in the right order" assumption secretly rode dict
        insertion order breaks here exactly as it would against a real
        ``SELECT`` with no ``ORDER BY`` guarantee.
        """
        await asyncio.sleep(0)
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"limit must be a positive integer, got {limit!r}")
        scrambled = list(reversed(list(self.db.tasks.values())))
        matching = [
            task
            for task in scrambled
            if task.updated_at is not None and task.updated_at > since
        ]
        total = len(matching)
        matching.sort(key=lambda task: task.updated_at or datetime.min.replace(tzinfo=UTC))
        rows = [task.model_copy(deep=True) for task in matching[:limit]]
        return _FakeTaskActivityWindow(rows=rows, total=total)

    async def create_many(
        self,
        specs: Any,
        *,
        created_by: str,
        ids: Sequence[str] | None = None,
    ) -> list[str]:
        """Batch-create, ALL-OR-NOTHING, ids positionally aligned with ``specs``.

        ``specs`` is typed ``Any`` here rather than the not-yet-built
        ``loremaster.tasks.TaskSpec`` (this file never imports a symbol that
        doesn't exist in production yet — that would break collection for
        every OTHER test importing this fake); it duck-types on
        ``.subject``/``.description``/``.blocked_by``, the same attributes
        the design's ``TaskSpec`` declares. Key resolution (temp keys ->
        minted ids) is a DISPATCHER concern per the design — this fake, like
        the real ledger, is key-agnostic and expects ``blocked_by`` already
        resolved to real (or intentionally pass-through) ids.

        ``ids`` is an optional caller-supplied parallel sequence: when given,
        it must align positionally with ``specs`` (a mismatch is a
        ``ValueError``, nothing written); the DISPATCHER pre-mints ids and
        wires sibling ``blocked_by`` references to them before the single
        atomic write. Omitted (``None``) — the fake mints internally
        (``uuid4().hex``) exactly as before.
        """
        await asyncio.sleep(0)
        if not specs:
            raise ValueError("create_many requires a non-empty list of specs")
        if ids is not None and len(ids) != len(specs):
            raise ValueError(
                f"create_many 'ids' must align positionally with 'specs' — "
                f"got {len(ids)} ids for {len(specs)} specs"
            )
        now = _utc_now()
        minted_ids: list[str] = []
        new_tasks: dict[str, Task] = {}
        for index, spec in enumerate(specs):
            task_id = ids[index] if ids is not None else uuid4().hex
            new_tasks[task_id] = Task(
                id=task_id,
                subject=spec.subject,
                description=spec.description,
                status=STATUS_OPEN,
                owner=None,
                claimed_at=None,
                blocked_by=list(dict.fromkeys(spec.blocked_by)),
                provenance={"created_by": created_by, "created_at": now.isoformat(), "events": []},
                superseded_by=None,
                created_at=now,
            )
            minted_ids.append(task_id)
        # ALL-OR-NOTHING: nothing is written to the shared store until every
        # spec above has built cleanly (a pydantic rejection on any one spec
        # raises BEFORE this line runs) — the fake's behavioural analogue of
        # the real ledger's single ``execute_transaction`` composing N CREATEs.
        self.db.tasks.update(new_tasks)
        return minted_ids

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
        # PKT-06 §1: a supersession is fleet-visible activity too — stamp the
        # OLD row's updated_at (the successor is a fresh create, deliberately
        # NOT stamped — see the design's "NOT stamped at create" rule).
        object.__setattr__(old_task, "updated_at", now)
        old_task.provenance.setdefault("events", []).append(
            {"actor": created_by, "action": "supersede", "successor": new_id, "at": now.isoformat()}
        )
        return new_id


# --------------------------------------------------------------------------- #
# THE ANSWER-CAP SANDWICH — ONE seeder, called by BOTH suites that pin ruling T1.
#
# Repo law #102 / brief-base §6: *"if two call sites need the same POLICY, it is a FUNCTION
# THEY CALL — never a pattern they clone."*  The sandwich is policy, not trivia: its SHAPE
# (blocked noise / unblocked filling / blocked noise) is what makes T1's discrimination
# deterministic under insertion order AND reverse-insertion order instead of merely
# improbable, and its sizes are what the caller's probability analysis is computed from.  A
# second copy would be a second thing to keep in step with that analysis.
#
# It lives HERE — beside the double rather than beside either suite — because the two
# callers are ``test_query_tasks_bounded.py`` (the REAL ledger only) and
# ``test_task_ledger.py`` (parametrised over the real ledger AND ``FakeTaskLedger``), and
# this is the one module both may import without dragging a SurrealDB dependency into the
# fake-only legs.  It is ledger-AGNOSTIC by construction: it touches ``create_task`` and
# ``create_many`` and nothing else, so the same seeding runs against either implementation.
#
# ⚠ Sharing is provable by MUTATION, which is the only proof that distinguishes DRY from
# looks-DRY: change ``blocked_each_side`` at a call site, or break this function, and pins
# in BOTH suites move.
# --------------------------------------------------------------------------- #


async def seed_answer_cap_sandwich(
    ledger: Any,
    *,
    blocked_each_side: int,
    unblocked_filling: int,
    created_by: str,
    description: str,
    root_subject: str = "the root blocker, which is itself unblocked",
    blocked_subject: str = "blocked backlog item",
    filling_subject: str = "claimable backlog item",
) -> tuple[str, int]:
    """Seed ``ledger`` with blocked noise, unblocked filling, then blocked noise again.

    The unblocked population is therefore a SANDWICH FILLING rather than a prefix or a
    suffix of insertion order — which is what a cap-applied-to-the-candidate-scan build has
    to survive, and cannot, under either insertion order or its reverse.

    Args:
        ledger: Any ledger exposing ``create_task`` and ``create_many`` — the real
            :class:`~loremaster.tasks.TaskLedger` or :class:`FakeTaskLedger`.
        blocked_each_side: Blocked noise rows seeded BEFORE and again AFTER the filling.
        unblocked_filling: Unblocked rows in the middle.
        created_by: Provenance for every row.
        description: Body text for every row.
        root_subject: Subject of the single shared blocker (itself unblocked).
        blocked_subject: Subject prefix for the noise rows.
        filling_subject: Subject prefix for the filling rows.

    Returns:
        ``(root_blocker_id, true_unblocked_population)`` — the second being
        ``unblocked_filling + 1``, because the root blocker is unblocked too and every
        caller asserts against it rather than recomputing it (a fixture that silently
        produced a different population turns a discrimination into a tautology).
    """
    from loremaster.tasks import TaskSpec

    root = await ledger.create_task(root_subject, description, created_by=created_by)

    async def _blocked_noise(tag: str) -> None:
        await ledger.create_many(
            [
                TaskSpec(
                    subject=f"{blocked_subject} {tag}-{index}",
                    description=description,
                    blocked_by=[root],
                )
                for index in range(blocked_each_side)
            ],
            created_by=created_by,
        )

    await _blocked_noise("before")
    await ledger.create_many(
        [
            TaskSpec(subject=f"{filling_subject} {index}", description=description)
            for index in range(unblocked_filling)
        ],
        created_by=created_by,
    )
    await _blocked_noise("after")
    return root, unblocked_filling + 1
