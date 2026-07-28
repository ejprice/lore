"""Contract tests for ``loremaster.tasks`` — the durable, fleet-visible TASK
LEDGER (lore v2 P7 orchestration spine), against the REAL SurrealDB server.

``TaskLedger`` is the fleet-coordination primitive: a table of work items that
many concurrent agent/orchestrator sessions can SEE (``query_tasks``), CLAIM
atomically (``claim_task`` — a compare-and-set that exactly one racer wins),
drive through a state machine (``transition``), and reframe without losing
history (``supersede_task``). It rides the SAME store machinery the rest of the
layer uses (one signed-in SurrealDB connection; the atomic claim rides
``compose()`` + ``execute_transaction()`` — single ``BEGIN … COMMIT`` with
per-statement verification and bounded optimistic-concurrency retry). These
tests run against a LIVE engine (see ``_surreal_harness``) because every
behaviour that matters — the atomic claim, snapshot durability, cross-session
visibility — is a server-side property no fake can stand in for at this phase.

The pinned contract (the public surface THIS FILE decides — the module does not
exist yet, so these names ARE the contract a later STUB/GREEN phase must match):

    Task:                                  # a value object (dataclass or model)
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

Expected until the module lands: collection ERROR in THIS FILE —
``ModuleNotFoundError: No module named 'loremaster.tasks'``.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from _task_fakes import FakeTaskDatabase, FakeTaskLedger
from loremaster.store._txn import (
    SurrealConnectionError,
    SurrealStoreError,
    _SurrealConnection,
)
from loremaster.store.surreal_schema import TASK_TABLE
from loremaster.tasks import (
    ClaimResult,
    IllegalTransitionError,
    Task,
    TaskLedger,
    TaskNotFoundError,
)
from pydantic import SecretStr
from surrealdb.errors import ErrorKind, ServerError

# --- the domain's status vocabulary (the convention this contract decides) ----
# Named constants, never bare literals in assertions. A later schema DDL phase
# will define the same set; because production is built FROM this contract, this
# is the single source of truth for the six statuses at this phase.
STATUS_OPEN = "open"
STATUS_CLAIMED = "claimed"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_BLOCKED = "blocked"
STATUS_WONTFIX = "wontfix"

# The two TERMINAL statuses — no transition may leave them — which are ALSO the
# exact set that "resolves" a blocker (a blocked_by entry stops blocking once its
# blocker reaches one of these). One source of truth for both semantics.
TERMINAL_STATUSES = frozenset({STATUS_DONE, STATUS_WONTFIX})

# --- realistic fleet identities (agent/session ids, NOT foo/bar) --------------
CREATOR = "orchestrator-session-7f3a"  # the team-lead session that files tasks
AGENT_A = "builder-agent-a"
AGENT_B = "builder-agent-b"
CLAIMER = AGENT_A  # the owner used when a setup path needs to claim a task
ACTOR = "grader-agent-c"  # the actor stamped on setup transitions

# Realistic work items drawn from this repo's own P7/P8 backlog — real range and
# shape of what the ledger will hold, never convenience placeholders.
SUBJECT_XML = "Add XML/data reference extractor for the Odoo dead-code target"
DESCRIPTION_XML = (
    "astroid alone false-positives on framework-mediated calls; add a non-Python "
    "extractor for XML data files so dead-code stops flagging live handlers."
)
SUBJECT_LEDGER = "Wire the durable task ledger into the P7 orchestration surface"
DESCRIPTION_LEDGER = "Expose create/claim/transition over the MCP tool surface for fleet coordination."
SUBJECT_MEMORY = "Backfill pre-existing memories into the v2 write-through ledger"
DESCRIPTION_MEMORY = "On boot, re-embed ledger rows into a wiped/short memory collection."
SUBJECT_WATCHER = "Prune watcher inotify watches at scheduling time"
DESCRIPTION_WATCHER = "Exclude dirs at watch-scheduling, not just event-filtering, to cut idle CPU."

# The race pin's iteration count — enough that a broken compare-and-set (two
# winners, or zero) lands reliably rather than hiding behind lucky scheduling.
_RACE_ITERATIONS = 20

# A generous window for the "derived timestamp is recent" sanity bound: absorbs
# clock skew + engine round-trip rounding while still catching a wrong-epoch /
# wrong-scale / stale-clock stamp (the order-of-magnitude class of bug).
_TIMESTAMP_TOLERANCE = timedelta(seconds=10)


# ---------------------------------------------------------------------------
# Helpers (reused across test classes)
# ---------------------------------------------------------------------------
def _provenance_mentions(provenance: Any, actor: str) -> bool:
    """Whether ``actor`` appears as a value ANYWHERE in a (possibly nested)
    provenance structure.

    Decouples the assertion from the exact provenance KEY layout (a dict shape
    this contract deliberately leaves open) while still pinning the real
    semantic the brief requires: the acting identity is recorded. Catches the
    "creator/actor not recorded" and "wrong identity recorded" bugs without
    over-specifying structure.
    """
    stack: list[Any] = [provenance]
    while stack:
        current = stack.pop()
        if isinstance(current, str):
            if current == actor:
                return True
        elif isinstance(current, dict):
            stack.extend(current.keys())
            stack.extend(current.values())
        elif isinstance(current, (list, tuple, set)):
            stack.extend(current)
    return False


def _mutate_into_unknown_id(real_task_id: str) -> str:
    """A same-SHAPED task id that was never minted — derived from a real one by
    flipping its last hex digit.

    Proves ``get_task``/``claim_task``/``transition``/``supersede_task`` treat an
    unknown id as a MEMBERSHIP miss (typed not-found), not a FORMAT rejection —
    without this test having to know the opaque id's internal format. ``a``/``b``
    are valid hex, so a uuid-shaped id stays a valid-but-different uuid string.
    """
    last = real_task_id[-1]
    flipped = "a" if last != "a" else "b"
    return f"{real_task_id[:-1]}{flipped}"


def _assert_recent_utc(stamp: datetime, *, not_before: datetime, not_after: datetime) -> None:
    """Sanity-bound a DERIVED timestamp: tz-aware UTC and within the call window.

    Timezone-awareness is the load-bearing anti-bug guard here — a naive stamp is
    the classic "wrong anchor" defect for a value agents in different timezones
    compare. The window bound catches a wrong-epoch / stale-clock stamp.
    """
    assert stamp.tzinfo is not None, "timestamp must be timezone-aware (fleet-comparable), not naive"
    assert not_before - _TIMESTAMP_TOLERANCE <= stamp <= not_after + _TIMESTAMP_TOLERANCE


async def _create(task_ledger: TaskLedger, subject: str, description: str) -> str:
    """Create an open task via the ledger and return its opaque id."""
    return await task_ledger.create_task(subject, description, created_by=CREATOR)


async def _drive_to_state(task_ledger: TaskLedger, target_status: str) -> str:
    """Create a task and drive it to ``target_status`` via KNOWN-LEGAL steps only.

    The reachability spine every state-machine test builds on. Uses ``claim_task``
    (never ``transition``) to reach ``claimed`` — because ``open -> claimed`` is
    deliberately NOT a legal transition — and the legal chain for the rest.
    """
    task_id = await _create(task_ledger, SUBJECT_LEDGER, DESCRIPTION_LEDGER)
    if target_status == STATUS_OPEN:
        return task_id
    if target_status == STATUS_BLOCKED:
        await task_ledger.transition(task_id, STATUS_BLOCKED, actor=ACTOR)  # open -> blocked (legal)
        return task_id
    if target_status == STATUS_WONTFIX:
        await task_ledger.transition(task_id, STATUS_WONTFIX, actor=ACTOR)  # open -> wontfix (legal)
        return task_id
    # claimed / in_progress / done all begin by CLAIMING the open task.
    claim = await task_ledger.claim_task(task_id, CLAIMER)
    assert claim.claimed, "setup precondition: a fresh open task must be claimable"
    if target_status == STATUS_CLAIMED:
        return task_id
    await task_ledger.transition(task_id, STATUS_IN_PROGRESS, actor=ACTOR)  # claimed -> in_progress
    if target_status == STATUS_IN_PROGRESS:
        return task_id
    if target_status == STATUS_DONE:
        # PKT-06 §4 breaking-change sweep: a done-transition now REQUIRES a
        # summary (mandatory, per the resolved design) — every pre-existing
        # setup path through this shared helper must supply one, or the
        # dozens of OTHER tests that merely need "a task in status done"
        # break on the new rule instead of exercising their own concern.
        await task_ledger.transition(
            task_id, STATUS_DONE, actor=ACTOR, summary="setup: driven to done via the legal chain"
        )  # in_progress -> done
        return task_id
    raise ValueError(f"unsupported target status {target_status!r}")


async def _derive_unknown_id(task_ledger: TaskLedger) -> str:
    """A never-minted, same-shaped id (via a throwaway real task)."""
    scratch_id = await _create(task_ledger, SUBJECT_WATCHER, DESCRIPTION_WATCHER)
    return _mutate_into_unknown_id(scratch_id)


async def _seed_row_naming_a_never_minted_blocker(
    task_ledger: TaskLedger,
) -> tuple[str, str]:
    """RAW-SEED an open task whose ``blocked_by`` names an id nothing ever minted.

    Returns ``(dependent_id, never_minted_blocker_id)``.

    ⚠ **WHY RAW, AND WHY THIS IS A STRONGER FIXTURE THAN THE ONE IT REPLACES.**  Operator
    ruling R3 (packet 04b-1, 2026-07-28) makes ``create_task`` REFUSE a blocked_by entry
    naming no real task — a deliberate live-verb change, *"a loud refusal replaces a silent
    black hole"*.  The two pins that use this helper were written before that change and
    built their fixture through ``create_task``; left alone they would certify the OLD
    world, which is the failure class ``CLAUDE.md`` names outright (*"a suite can be green
    BECAUSE it still asserts the corpse"*).

    But the READ property they pin — an unresolvable blocker is fail-CLOSED — does not go
    away with the write.  **Every row written before this packet lived under a FAIL-OPEN
    ``blocked_by``**, so a long-lived store holds exactly these rows and nothing will ever
    clean them (#236 is ruled OUT).  A fixture that can only produce rows the NEW guard
    allows is a fixture that guarantees the one condition under which the bug is invisible —
    the #107/#131 shape, verbatim.  Raw-seeding keeps the pins pointed at production's real
    state instead of at the test environment's fiction.

    Backend-agnostic on purpose: this module's contract runs against BOTH the real
    SurrealDB-backed ledger and ``FakeTaskLedger``, and the parity is the point.  The real
    branch writes through the ledger's OWN connection (no ``SurrealEnv`` is exposed by the
    fixture, and ``measure_store_traffic`` establishes the same access idiom); the fake
    branch writes into the in-memory table its ledger reads.  Neither branch goes near the
    guard being bypassed, which is what makes this a legacy row rather than a hole in R3.
    """
    real_blocker = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
    never_minted_blocker = _mutate_into_unknown_id(real_blocker)  # same shape, never created
    # Born through the ordinary verb with NO dependency, then given one RAW. That is the
    # order production wrote these rows in, and it means neither branch has to hand-build a
    # task row — every column but ``blocked_by`` is whatever today's create path produces.
    dependent_id = await _create(task_ledger, SUBJECT_LEDGER, DESCRIPTION_LEDGER)
    # ``Any`` on purpose: the fixture's ``"fake"`` branch hands over a ``FakeTaskLedger``
    # cast to ``TaskLedger`` (the parity pin's whole design), so an isinstance test against
    # the DECLARED type narrows to "always true" and mypy calls the fake branch unreachable.
    backend: Any = task_ledger

    if isinstance(backend, TaskLedger):
        connection = await backend._ensure_connection()  # noqa: SLF001 - the legacy seed
        await connection.query(
            f"UPDATE type::record('{TASK_TABLE}', $id) SET blocked_by = $blocked_by",
            {"id": dependent_id, "blocked_by": [never_minted_blocker]},
        )
    else:
        fake = cast(FakeTaskLedger, backend)
        fake.db.tasks[dependent_id] = fake.db.tasks[dependent_id].model_copy(
            update={"blocked_by": [never_minted_blocker]}
        )

    persisted = await task_ledger.get_task(dependent_id)
    assert persisted.blocked_by == [never_minted_blocker], (
        f"the legacy seed did not land its blocked_by column ({persisted.blocked_by!r}), so "
        f"the pins using it would assert the fail-closed property about a task that has no "
        f"unresolvable blocker at all"
    )
    return dependent_id, never_minted_blocker


# A factory that builds one more ready ``TaskLedger`` on the SAME database — the
# second live connection the fleet-visibility and race pins need.
TaskLedgerFactory = Callable[[], Awaitable[TaskLedger]]


@pytest_asyncio.fixture(params=["real", "fake"])
async def task_ledger_factory(request: pytest.FixtureRequest) -> AsyncIterator[TaskLedgerFactory]:
    """A factory yielding independent ready ledgers on the SAME per-test backing
    store — parametrized over BOTH the real SurrealDB-backed ``TaskLedger`` and
    the adversarial in-memory ``FakeTaskLedger`` (``_task_fakes.py``).

    THE single construction seam (no test builds a ledger inline) — every test
    in this module routes through here, so the SAME contract suite exercises
    both backends. This is the fake-vs-real PARITY PIN: a behaviour the fake
    gets wrong, or too friendly, shows up as a real-vs-fake divergence rather
    than a fake-only green.

    The ``"real"`` branch deliberately does NOT depend on the ``surreal_env``
    pytest fixture (neither as a normal parameter nor via
    ``request.getfixturevalue``): pytest-asyncio 1.4's function-scoped
    ``Runner`` is SHARED by every async fixture a test uses, and resolving one
    async fixture (``surreal_env``) from INSIDE another async fixture's own
    body (this one) re-enters that same ``Runner`` — verified live, it raises
    ``RuntimeError: Runner.run() cannot be called from a running event loop``.
    Calling the exact SAME underlying harness helpers ``surreal_env`` itself
    calls (``make_env`` / ``connect_admin`` / ``drop_database`` — no new
    logic) gets the identical isolated-throwaway-database guarantee without
    touching pytest's fixture graph, sidesteps the reentrancy limitation, AND
    keeps every ``TaskLedger`` this fixture creates on the SAME event loop the
    test runs on (the loop affinity its eventual real ``close()`` will need).
    The ``"fake"`` branch never touches the SurrealDB harness at all — it
    builds ONE shared ``FakeTaskDatabase`` per test; every ``make()`` call
    hands back a distinct ``FakeTaskLedger`` handle over that SAME store —
    two independent "connections" to one fleet-visible table, exactly what
    ``TestClaimRace`` and ``TestFleetVisibility`` need to be meaningful
    against the fake.
    """
    created: list[TaskLedger] = []

    if request.param == "real":
        env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()

        async def make() -> TaskLedger:
            ledger = TaskLedger(
                url=env.url,
                namespace=env.namespace,
                database=env.database,
                user=env.user,
                password=env.password,
            )
            await ledger.ensure_ready()
            created.append(ledger)
            return ledger
    else:
        shared_db = FakeTaskDatabase()

        async def make() -> TaskLedger:
            fake_ledger = FakeTaskLedger(db=shared_db)
            await fake_ledger.ensure_ready()
            # A FakeTaskLedger satisfies the TaskLedger contract behaviourally
            # (that IS this parity pin); it shares no base class with the real
            # TaskLedger, so the cast tells mypy what the test suite proves.
            typed_ledger = cast(TaskLedger, fake_ledger)
            created.append(typed_ledger)
            return typed_ledger

    try:
        yield make
    finally:
        for ledger in created:
            await ledger.close()
        if request.param == "real":
            await drop_database(env)


@pytest_asyncio.fixture()
async def task_ledger(task_ledger_factory: TaskLedgerFactory) -> TaskLedger:
    """A single ready ledger on a fresh unique database (the common per-test case)."""
    return await task_ledger_factory()


class TestCreateAndGet:
    """Create → get round-trip, default state, opaque-str ids, no content dedup.

    Pins the birth of a task: it starts ``open``/unowned/unclaimed, its id is an
    OPAQUE hashable string (never a raw RecordID), the creator is recorded in
    provenance, and — unlike the memory model it borrows machinery from — two
    tasks sharing a subject are DISTINCT (tasks are not content-deduped).
    """

    async def test_create_returns_an_opaque_string_id(self, task_ledger: TaskLedger) -> None:
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        # The API speaks bare str everywhere (RecordID is unhashable in the SDK).
        assert isinstance(task_id, str)
        assert task_id  # non-empty

    async def test_task_id_is_hashable_and_usable_as_a_key(self, task_ledger: TaskLedger) -> None:
        # Opaque-str ids must work as dict keys / set members — a raw RecordID
        # (unhashable) would raise here, catching that leak.
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        index = {task_id: "value"}
        assert task_id in index

    async def test_created_task_starts_open_unowned_unclaimed(self, task_ledger: TaskLedger) -> None:
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        task = await task_ledger.get_task(task_id)
        assert isinstance(task, Task)
        assert task.id == task_id
        assert task.status == STATUS_OPEN
        assert task.owner is None
        assert task.claimed_at is None
        assert task.superseded_by is None
        assert task.blocked_by == []  # no dependencies by default

    async def test_get_task_round_trips_subject_and_description(self, task_ledger: TaskLedger) -> None:
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        task = await task_ledger.get_task(task_id)
        assert task.subject == SUBJECT_XML
        assert task.description == DESCRIPTION_XML

    async def test_created_at_is_timezone_aware_and_recent(self, task_ledger: TaskLedger) -> None:
        before = datetime.now(UTC)
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        after = datetime.now(UTC)
        task = await task_ledger.get_task(task_id)
        assert isinstance(task.created_at, datetime)
        _assert_recent_utc(task.created_at, not_before=before, not_after=after)

    async def test_provenance_records_the_creator(self, task_ledger: TaskLedger) -> None:
        # created_by is REQUIRED at create; it must be recoverable from provenance.
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        task = await task_ledger.get_task(task_id)
        assert isinstance(task.provenance, dict)
        assert _provenance_mentions(task.provenance, CREATOR)

    async def test_duplicate_subjects_are_distinct_tasks(self, task_ledger: TaskLedger) -> None:
        # THE anti-dedup seam: the memory model uuid5s over content and collapses
        # duplicates; the ledger must NOT — two tasks with the same subject are two
        # separate work items with two distinct ids, both independently retrievable.
        first_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        second_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        assert first_id != second_id
        assert len({first_id, second_id}) == 2
        assert (await task_ledger.get_task(first_id)).id == first_id
        assert (await task_ledger.get_task(second_id)).id == second_id

    async def test_create_preserves_blocked_by_dependencies(self, task_ledger: TaskLedger) -> None:
        blocker_one = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
        blocker_two = await _create(task_ledger, SUBJECT_WATCHER, DESCRIPTION_WATCHER)
        dependent_id = await task_ledger.create_task(
            SUBJECT_LEDGER, DESCRIPTION_LEDGER, blocked_by=[blocker_one, blocker_two], created_by=CREATOR
        )
        task = await task_ledger.get_task(dependent_id)
        # Set equality: no blocker dropped or duplicated (ordering left unpinned).
        assert set(task.blocked_by) == {blocker_one, blocker_two}

    async def test_get_task_unknown_id_raises_not_found(self, task_ledger: TaskLedger) -> None:
        unknown_id = await _derive_unknown_id(task_ledger)
        with pytest.raises(TaskNotFoundError):
            await task_ledger.get_task(unknown_id)


class TestQueryTasks:
    """The fleet-visible read: exact status/owner filters + the dependency-aware
    ``blocked`` partition (blocked ⇔ a blocker not yet done/wontfix).

    Pins that ``blocked=True/False`` keys off the BLOCKER's status, so a blocker
    that has been done/wontfixed stops counting — the exact nuance a naive "any
    blocked_by ⇒ blocked" implementation would get wrong.
    """

    async def test_no_filters_returns_all_tasks(self, task_ledger: TaskLedger) -> None:
        created_ids = {
            await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML),
            await _create(task_ledger, SUBJECT_LEDGER, DESCRIPTION_LEDGER),
            await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY),
        }
        all_tasks = await task_ledger.query_tasks()
        assert {task.id for task in all_tasks} == created_ids

    async def test_status_filter_is_exact(self, task_ledger: TaskLedger) -> None:
        # Exactly one task in each of the six statuses; each filter returns only it.
        by_status = {status: await _drive_to_state(task_ledger, status) for status in
                     (STATUS_OPEN, STATUS_CLAIMED, STATUS_IN_PROGRESS, STATUS_DONE,
                      STATUS_BLOCKED, STATUS_WONTFIX)}
        for status, expected_id in by_status.items():
            rows = await task_ledger.query_tasks(status=status)
            assert {task.id for task in rows} == {expected_id}
            assert all(task.status == status for task in rows)

    async def test_owner_filter_is_exact(self, task_ledger: TaskLedger) -> None:
        agent_a_first = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        agent_a_second = await _create(task_ledger, SUBJECT_LEDGER, DESCRIPTION_LEDGER)
        agent_b_only = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
        assert (await task_ledger.claim_task(agent_a_first, AGENT_A)).claimed
        assert (await task_ledger.claim_task(agent_a_second, AGENT_A)).claimed
        assert (await task_ledger.claim_task(agent_b_only, AGENT_B)).claimed

        assert {task.id for task in await task_ledger.query_tasks(owner=AGENT_A)} == {
            agent_a_first,
            agent_a_second,
        }
        assert {task.id for task in await task_ledger.query_tasks(owner=AGENT_B)} == {agent_b_only}

    async def test_blocked_partition_keys_off_blocker_status(self, task_ledger: TaskLedger) -> None:
        # An OPEN blocker → its dependent is genuinely blocked.
        open_blocker = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
        genuinely_blocked = await task_ledger.create_task(
            SUBJECT_LEDGER, DESCRIPTION_LEDGER, blocked_by=[open_blocker], created_by=CREATOR
        )
        # A WONTFIXED blocker → its dependent is NOT blocked (blocker resolved).
        resolved_blocker = await _drive_to_state(task_ledger, STATUS_WONTFIX)
        unblocked_by_resolution = await task_ledger.create_task(
            SUBJECT_XML, DESCRIPTION_XML, blocked_by=[resolved_blocker], created_by=CREATOR
        )
        # A task with no dependencies at all is unblocked.
        free_task = await _create(task_ledger, SUBJECT_WATCHER, DESCRIPTION_WATCHER)

        blocked_ids = {task.id for task in await task_ledger.query_tasks(blocked=True)}
        unblocked_ids = {task.id for task in await task_ledger.query_tasks(blocked=False)}

        assert genuinely_blocked in blocked_ids
        assert genuinely_blocked not in unblocked_ids
        # The resolved-blocker nuance: a dependent of a wontfixed blocker is FREE.
        assert unblocked_by_resolution in unblocked_ids
        assert unblocked_by_resolution not in blocked_ids
        assert free_task in unblocked_ids

    async def test_blocked_partition_conserves_every_task(self, task_ledger: TaskLedger) -> None:
        # Sanity/conservation bound: blocked ⊎ unblocked == all tasks, disjoint —
        # no task lost or double-counted by the partition.
        open_blocker = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
        dependent = await task_ledger.create_task(
            SUBJECT_LEDGER, DESCRIPTION_LEDGER, blocked_by=[open_blocker], created_by=CREATOR
        )
        free_task = await _create(task_ledger, SUBJECT_WATCHER, DESCRIPTION_WATCHER)
        all_ids = {open_blocker, dependent, free_task}

        blocked_ids = {task.id for task in await task_ledger.query_tasks(blocked=True)}
        unblocked_ids = {task.id for task in await task_ledger.query_tasks(blocked=False)}
        assert blocked_ids.isdisjoint(unblocked_ids)
        assert blocked_ids | unblocked_ids == all_ids

    async def test_filter_matching_nothing_is_honest_empty_list(self, task_ledger: TaskLedger) -> None:
        await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)  # status open, unowned
        assert await task_ledger.query_tasks(status=STATUS_DONE) == []
        assert await task_ledger.query_tasks(owner=AGENT_A) == []


class TestAtomicClaim:
    """The compare-and-set claim: succeeds ONLY from open/unowned/unblocked; a
    losing claim is a RESULT (claimed=False + current state), never an exception,
    and NEVER mutates the row.
    """

    async def test_claim_open_task_succeeds_and_stamps_owner_status_claimed_at(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        before = datetime.now(UTC)
        result = await task_ledger.claim_task(task_id, AGENT_A)
        after = datetime.now(UTC)

        assert isinstance(result, ClaimResult)
        assert result.claimed is True
        assert result.task.owner == AGENT_A
        assert result.task.status == STATUS_CLAIMED
        assert result.task.claimed_at is not None
        _assert_recent_utc(result.task.claimed_at, not_before=before, not_after=after)
        # A fresh read from the store agrees (the write persisted, not just echoed).
        persisted = await task_ledger.get_task(task_id)
        assert persisted.owner == AGENT_A
        assert persisted.status == STATUS_CLAIMED

    async def test_second_claim_returns_false_naming_the_current_holder(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        assert (await task_ledger.claim_task(task_id, AGENT_A)).claimed is True

        loser = await task_ledger.claim_task(task_id, AGENT_B)
        assert loser.claimed is False
        # The loser MUST be able to see who holds it (fleet-coordination point).
        assert loser.task.owner == AGENT_A
        assert loser.task.status == STATUS_CLAIMED

    async def test_failed_claim_does_not_mutate_the_row(self, task_ledger: TaskLedger) -> None:
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        winning = await task_ledger.claim_task(task_id, AGENT_A)
        claimed_at_after_win = winning.task.claimed_at

        await task_ledger.claim_task(task_id, AGENT_B)  # loses; must not write anything

        persisted = await task_ledger.get_task(task_id)
        assert persisted.owner == AGENT_A  # not overwritten by the loser
        assert persisted.status == STATUS_CLAIMED
        assert persisted.claimed_at == claimed_at_after_win  # stamp untouched by the loser

    @pytest.mark.parametrize(
        "occupied_status",
        [STATUS_CLAIMED, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_BLOCKED, STATUS_WONTFIX],
    )
    async def test_claim_non_open_task_returns_false(
        self, task_ledger: TaskLedger, occupied_status: str
    ) -> None:
        # Claim succeeds ONLY from status open; any other status → claimed=False
        # with the current state, never an exception.
        task_id = await _drive_to_state(task_ledger, occupied_status)
        result = await task_ledger.claim_task(task_id, AGENT_B)
        assert result.claimed is False
        assert result.task.status == occupied_status

    async def test_claim_unknown_id_raises_not_found(self, task_ledger: TaskLedger) -> None:
        unknown_id = await _derive_unknown_id(task_ledger)
        with pytest.raises(TaskNotFoundError):
            await task_ledger.claim_task(unknown_id, AGENT_A)


class TestClaimRace:
    """THE load-bearing pin: two agents racing the SAME open task — exactly one
    wins, every time, across many iterations, on two SEPARATE live connections.

    Two connections (not two coroutines on one socket) is the production-realistic
    fleet scenario and the only configuration that actually exercises the
    server-side compare-and-set + optimistic-concurrency retry the claim rides.
    """

    async def test_exactly_one_winner_across_concurrent_claims(
        self, task_ledger_factory: TaskLedgerFactory
    ) -> None:
        ledger_a = await task_ledger_factory()
        ledger_b = await task_ledger_factory()

        for iteration in range(_RACE_ITERATIONS):
            task_id = await _create(ledger_a, f"{SUBJECT_LEDGER} #{iteration}", DESCRIPTION_LEDGER)

            result_a, result_b = await asyncio.gather(
                ledger_a.claim_task(task_id, AGENT_A),
                ledger_b.claim_task(task_id, AGENT_B),
            )

            # EXACTLY one winner — never two (broken CAS), never zero (both lost).
            assert result_a.claimed ^ result_b.claimed, (
                f"iteration {iteration}: expected exactly one winner, got "
                f"a={result_a.claimed} b={result_b.claimed}"
            )
            winner_owner = AGENT_A if result_a.claimed else AGENT_B
            loser = result_b if result_a.claimed else result_a
            # The loser sees the winner as the holder.
            assert loser.claimed is False
            assert loser.task.owner == winner_owner

            # A fresh read agrees: the winner holds it, claimed and stamped.
            persisted = await ledger_a.get_task(task_id)
            assert persisted.owner == winner_owner
            assert persisted.status == STATUS_CLAIMED
            assert persisted.claimed_at is not None


class TestBlockedClaiming:
    """Fail-closed claiming: an unresolved blocker BLOCKS the claim; the claim
    succeeds only once EVERY blocker is done/wontfix.

    Both directions pinned, plus the partial case (two blockers, resolving one is
    not enough) — the exact fail-open bug an "all-or-nothing on the wrong axis"
    implementation would introduce.
    """

    async def test_claim_blocked_by_unresolved_blocker_returns_false(
        self, task_ledger: TaskLedger
    ) -> None:
        open_blocker = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
        dependent = await task_ledger.create_task(
            SUBJECT_LEDGER, DESCRIPTION_LEDGER, blocked_by=[open_blocker], created_by=CREATOR
        )
        result = await task_ledger.claim_task(dependent, AGENT_A)
        assert result.claimed is False
        # Fail closed: the dependent is still open/unowned, not silently claimed.
        assert result.task.status == STATUS_OPEN
        assert result.task.owner is None

    async def test_blocked_claim_does_not_mutate_the_row(self, task_ledger: TaskLedger) -> None:
        open_blocker = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
        dependent = await task_ledger.create_task(
            SUBJECT_LEDGER, DESCRIPTION_LEDGER, blocked_by=[open_blocker], created_by=CREATOR
        )
        await task_ledger.claim_task(dependent, AGENT_A)  # must not write

        persisted = await task_ledger.get_task(dependent)
        assert persisted.status == STATUS_OPEN
        assert persisted.owner is None
        assert persisted.claimed_at is None

    async def test_claim_succeeds_once_blocker_is_wontfixed(self, task_ledger: TaskLedger) -> None:
        blocker = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
        dependent = await task_ledger.create_task(
            SUBJECT_LEDGER, DESCRIPTION_LEDGER, blocked_by=[blocker], created_by=CREATOR
        )
        await task_ledger.transition(blocker, STATUS_WONTFIX, actor=ACTOR)  # open -> wontfix

        result = await task_ledger.claim_task(dependent, AGENT_A)
        assert result.claimed is True
        assert result.task.owner == AGENT_A

    async def test_claim_succeeds_once_blocker_is_done(self, task_ledger: TaskLedger) -> None:
        blocker = await _drive_to_state(task_ledger, STATUS_DONE)  # legal chain to done
        dependent = await task_ledger.create_task(
            SUBJECT_LEDGER, DESCRIPTION_LEDGER, blocked_by=[blocker], created_by=CREATOR
        )
        result = await task_ledger.claim_task(dependent, AGENT_A)
        assert result.claimed is True
        assert result.task.owner == AGENT_A

    async def test_partially_resolved_blockers_still_block(self, task_ledger: TaskLedger) -> None:
        first_blocker = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
        second_blocker = await _create(task_ledger, SUBJECT_WATCHER, DESCRIPTION_WATCHER)
        dependent = await task_ledger.create_task(
            SUBJECT_LEDGER, DESCRIPTION_LEDGER,
            blocked_by=[first_blocker, second_blocker], created_by=CREATOR,
        )

        # Resolve ONLY the first blocker — the second still blocks (at least one
        # unresolved blocker ⇒ genuinely blocked).
        await task_ledger.transition(first_blocker, STATUS_WONTFIX, actor=ACTOR)
        still_blocked = await task_ledger.claim_task(dependent, AGENT_A)
        assert still_blocked.claimed is False

        # Resolve the second too — now every blocker is resolved, claim succeeds.
        await task_ledger.transition(second_blocker, STATUS_WONTFIX, actor=ACTOR)
        now_free = await task_ledger.claim_task(dependent, AGENT_A)
        assert now_free.claimed is True

    async def test_never_minted_blocker_id_fails_closed_on_claim(
        self, task_ledger: TaskLedger
    ) -> None:
        # Decided default (fail-closed): a blocked_by entry naming a task id that
        # was NEVER minted counts as an UNRESOLVED blocker. Fail-OPEN on a typo'd
        # dependency would silently unblock work in a coordination primitive; the
        # escape hatch for a genuinely bad dep is supersede_task, not a claim.
        #
        # ⚠ RE-AUTHORED for operator ruling R3 (packet 04b-1, 2026-07-28). The row is
        # RAW-SEEDED because ``create_task`` now REFUSES a phantom blocker — see
        # ``_seed_row_naming_a_never_minted_blocker`` for why that makes this pin
        # stronger rather than weaker, not merely still-green.
        dependent, never_minted_blocker = await _seed_row_naming_a_never_minted_blocker(
            task_ledger
        )
        result = await task_ledger.claim_task(dependent, AGENT_A)
        assert result.claimed is False, (
            f"a task whose blocked_by names the never-minted id {never_minted_blocker!r} "
            f"was CLAIMED. An unresolvable blocker is fail-closed: fail-OPEN on a typo'd "
            f"dependency silently unblocks work in a coordination primitive"
        )
        # Fail closed AND no mutation — still open/unowned/unclaimed.
        persisted = await task_ledger.get_task(dependent)
        assert persisted.status == STATUS_OPEN
        assert persisted.owner is None
        assert persisted.claimed_at is None

    async def test_never_minted_blocker_id_counts_as_blocked_in_query(
        self, task_ledger: TaskLedger
    ) -> None:
        # The query partition agrees with the claim gate: a dependent of a
        # never-minted blocker is genuinely blocked, never quietly unblocked.
        #
        # ⚠ RE-AUTHORED for operator ruling R3, as above.
        dependent, never_minted_blocker = await _seed_row_naming_a_never_minted_blocker(
            task_ledger
        )
        blocked_ids = {task.id for task in await task_ledger.query_tasks(blocked=True)}
        unblocked_ids = {task.id for task in await task_ledger.query_tasks(blocked=False)}
        assert dependent in blocked_ids, (
            f"query_tasks(blocked=True) omitted a task whose blocked_by names the "
            f"never-minted id {never_minted_blocker!r}"
        )
        assert dependent not in unblocked_ids, (
            f"query_tasks(blocked=False) served a task whose blocked_by names the "
            f"never-minted id {never_minted_blocker!r} as claimable — the partition and the "
            f"claim gate now disagree, and an agent is being told to attempt a claim that "
            f"can never win"
        )

    # ⚠ THE WRITE HALF OF R3 IS DELIBERATELY *NOT* PINNED HERE — ESCALATED INSTEAD.
    # The refusal itself (class, served sentence, which ids it names, both create verbs,
    # four id shapes) is pinned against the REAL ledger in ``test_blocks_edge.py`` SECTION G.
    # A pin here would run against BOTH backends, and whether ``FakeTaskLedger`` must ALSO
    # refuse is UNRULED: this module's whole design is the real-vs-fake parity pin (*"a
    # behaviour the fake gets wrong, or too friendly, shows up as a divergence rather than a
    # fake-only green"*), which argues the fake must refuse — but ``_task_fakes.py`` is in no
    # ruling's scope, so a both-backends pin would be RED on a build that is correct under the
    # other reading. Both readings and a recommendation are in
    # ``REPORT-contractfix-04b1-r3.md`` §ESCALATIONS; picking one silently was not available.


# The full legal transition matrix (the brief's state machine, verbatim).
LEGAL_TRANSITIONS = [
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
]

# Representative ILLEGAL transitions — including the two terminal states (done,
# wontfix), the claim-only ``open -> claimed`` edge, no-op self-transitions, and
# the "must pass through" skips the state machine forbids. "Legal transitions
# ONLY" means everything not in LEGAL_TRANSITIONS is illegal; this samples the
# high-value ones.
ILLEGAL_TRANSITIONS = [
    (STATUS_OPEN, STATUS_CLAIMED),        # only claim_task reaches claimed
    (STATUS_OPEN, STATUS_IN_PROGRESS),    # must claim first
    (STATUS_OPEN, STATUS_DONE),
    (STATUS_OPEN, STATUS_OPEN),           # no-op is not a legal transition
    (STATUS_CLAIMED, STATUS_DONE),        # must pass through in_progress
    (STATUS_CLAIMED, STATUS_OPEN),        # release only via blocked
    (STATUS_IN_PROGRESS, STATUS_OPEN),
    (STATUS_IN_PROGRESS, STATUS_CLAIMED),
    (STATUS_BLOCKED, STATUS_DONE),        # blocked must re-enter in_progress first
    (STATUS_BLOCKED, STATUS_CLAIMED),
    (STATUS_DONE, STATUS_OPEN),           # done is TERMINAL
    (STATUS_DONE, STATUS_IN_PROGRESS),
    (STATUS_DONE, STATUS_BLOCKED),
    (STATUS_DONE, STATUS_WONTFIX),
    (STATUS_WONTFIX, STATUS_OPEN),        # wontfix is TERMINAL
    (STATUS_WONTFIX, STATUS_IN_PROGRESS),
    (STATUS_WONTFIX, STATUS_DONE),
]


class TestTransitions:
    """The status state machine: only the declared edges are legal; illegal ones
    raise a typed error naming both states and leave the row untouched; every
    legal transition stamps provenance; the terminal states have no exits; and
    ``open -> claimed`` is reachable ONLY through ``claim_task``.
    """

    @pytest.mark.parametrize(("from_status", "to_status"), LEGAL_TRANSITIONS)
    async def test_legal_transition_moves_to_target(
        self, task_ledger: TaskLedger, from_status: str, to_status: str
    ) -> None:
        task_id = await _drive_to_state(task_ledger, from_status)
        # PKT-06 §4 breaking-change sweep: the done target now requires a
        # summary (mandatory) — every OTHER legal edge is unaffected.
        summary_kwargs = (
            {"summary": "setup: generic legal-transition pin reached done"}
            if to_status == STATUS_DONE
            else {}
        )
        updated = await task_ledger.transition(task_id, to_status, actor=ACTOR, **summary_kwargs)
        assert updated.status == to_status
        # The store agrees on read-back (persisted, not just returned).
        assert (await task_ledger.get_task(task_id)).status == to_status

    async def test_legal_transition_stamps_the_actor_in_provenance(
        self, task_ledger: TaskLedger
    ) -> None:
        # A distinct actor (not the creator) must show up after a transition.
        task_id = await _drive_to_state(task_ledger, STATUS_CLAIMED)
        await task_ledger.transition(task_id, STATUS_IN_PROGRESS, actor=ACTOR)
        persisted = await task_ledger.get_task(task_id)
        assert _provenance_mentions(persisted.provenance, ACTOR)

    @pytest.mark.parametrize(("from_status", "to_status"), ILLEGAL_TRANSITIONS)
    async def test_illegal_transition_raises_and_leaves_row_untouched(
        self, task_ledger: TaskLedger, from_status: str, to_status: str
    ) -> None:
        task_id = await _drive_to_state(task_ledger, from_status)
        before = await task_ledger.get_task(task_id)

        with pytest.raises(IllegalTransitionError) as exc_info:
            await task_ledger.transition(task_id, to_status, actor=ACTOR)
        # The error names BOTH states so a caller/operator can see what was refused.
        message = str(exc_info.value)
        assert from_status in message
        assert to_status in message

        # The row is completely untouched by the refused transition.
        after = await task_ledger.get_task(task_id)
        assert after.status == before.status
        assert after.owner == before.owner

    async def test_open_to_claimed_is_not_reachable_via_transition(
        self, task_ledger: TaskLedger
    ) -> None:
        # Emphasis on the brief's explicit rule: claiming is the ONLY way to
        # ``claimed`` — transition must refuse it, leaving the task open/unowned.
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        with pytest.raises(IllegalTransitionError):
            await task_ledger.transition(task_id, STATUS_CLAIMED, actor=ACTOR)
        persisted = await task_ledger.get_task(task_id)
        assert persisted.status == STATUS_OPEN
        assert persisted.owner is None

    async def test_transition_to_unknown_status_is_refused(self, task_ledger: TaskLedger) -> None:
        # A garbage target status is not a member of the vocabulary → refused.
        task_id = await _drive_to_state(task_ledger, STATUS_CLAIMED)
        with pytest.raises(IllegalTransitionError):
            await task_ledger.transition(task_id, "abandoned", actor=ACTOR)
        assert (await task_ledger.get_task(task_id)).status == STATUS_CLAIMED

    async def test_transition_unknown_id_raises_not_found(self, task_ledger: TaskLedger) -> None:
        unknown_id = await _derive_unknown_id(task_ledger)
        with pytest.raises(TaskNotFoundError):
            await task_ledger.transition(unknown_id, STATUS_IN_PROGRESS, actor=ACTOR)


class TestSupersession:
    """Reframing a task without losing history: ``supersede_task`` creates a fresh
    open successor AND stamps the old row ``superseded_by`` atomically; the OLD
    row is KEPT (never deleted); a superseded task is terminal-like — it cannot be
    claimed or transitioned.
    """

    async def test_supersede_returns_a_new_distinct_task_id(self, task_ledger: TaskLedger) -> None:
        old_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        new_id = await task_ledger.supersede_task(
            old_id, subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER, created_by=CREATOR
        )
        assert isinstance(new_id, str)
        assert new_id != old_id

    async def test_old_row_is_kept_and_stamped_superseded_by(self, task_ledger: TaskLedger) -> None:
        old_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        new_id = await task_ledger.supersede_task(
            old_id, subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER, created_by=CREATOR
        )
        # History is kept — get_task on the OLD id still resolves, now stamped.
        old_task = await task_ledger.get_task(old_id)
        assert old_task.superseded_by == new_id

    async def test_successor_starts_open_unowned_with_given_content(
        self, task_ledger: TaskLedger
    ) -> None:
        old_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        new_id = await task_ledger.supersede_task(
            old_id, subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER, created_by=CREATOR
        )
        successor = await task_ledger.get_task(new_id)
        assert successor.status == STATUS_OPEN
        assert successor.owner is None
        assert successor.superseded_by is None
        assert successor.subject == SUBJECT_LEDGER
        assert successor.description == DESCRIPTION_LEDGER

    async def test_superseded_task_cannot_be_claimed(self, task_ledger: TaskLedger) -> None:
        old_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        await task_ledger.supersede_task(
            old_id, subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER, created_by=CREATOR
        )
        result = await task_ledger.claim_task(old_id, AGENT_A)
        assert result.claimed is False
        # Untouched: still superseded, not claimed.
        persisted = await task_ledger.get_task(old_id)
        assert persisted.owner is None
        assert persisted.status != STATUS_CLAIMED

    async def test_superseded_task_cannot_be_transitioned(self, task_ledger: TaskLedger) -> None:
        old_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        await task_ledger.supersede_task(
            old_id, subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER, created_by=CREATOR
        )
        with pytest.raises(IllegalTransitionError):
            await task_ledger.transition(old_id, STATUS_BLOCKED, actor=ACTOR)

    async def test_supersede_unknown_id_raises_not_found(self, task_ledger: TaskLedger) -> None:
        unknown_id = await _derive_unknown_id(task_ledger)
        with pytest.raises(TaskNotFoundError):
            await task_ledger.supersede_task(
                unknown_id, subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER, created_by=CREATOR
            )


class TestFleetVisibility:
    """Durability across sessions: a SECOND ledger over the SAME database sees the
    FIRST's tasks and claims — SurrealDB's volume is the durable spine (no SQLite
    side-ledger). This is the whole point of a "fleet-visible" table.
    """

    async def test_second_ledger_reads_first_ledgers_task(
        self, task_ledger_factory: TaskLedgerFactory
    ) -> None:
        writer = await task_ledger_factory()
        task_id = await _create(writer, SUBJECT_XML, DESCRIPTION_XML)

        reader = await task_ledger_factory()  # a distinct connection, same database
        seen = await reader.get_task(task_id)
        assert seen.id == task_id
        assert seen.subject == SUBJECT_XML

    async def test_second_ledger_query_includes_first_ledgers_open_task(
        self, task_ledger_factory: TaskLedgerFactory
    ) -> None:
        writer = await task_ledger_factory()
        task_id = await _create(writer, SUBJECT_LEDGER, DESCRIPTION_LEDGER)

        reader = await task_ledger_factory()
        open_ids = {task.id for task in await reader.query_tasks(status=STATUS_OPEN)}
        assert task_id in open_ids

    async def test_second_ledger_sees_a_claim_made_by_the_first(
        self, task_ledger_factory: TaskLedgerFactory
    ) -> None:
        writer = await task_ledger_factory()
        task_id = await _create(writer, SUBJECT_XML, DESCRIPTION_XML)
        assert (await writer.claim_task(task_id, AGENT_A)).claimed is True

        reader = await task_ledger_factory()
        seen = await reader.get_task(task_id)
        assert seen.owner == AGENT_A  # the claim is durable + cross-session visible
        assert seen.status == STATUS_CLAIMED


# ---------------------------------------------------------------------------
# FIX-CYCLE pins (wave-1 audit findings #1/#2/#3) — the mutator concurrency
# holes and the blocked_by normalization gap the ORIGINAL contract never pinned.
# ---------------------------------------------------------------------------

# Resolver identities for the concurrent-terminal-transition race — DELIBERATELY
# distinct from every setup identity (CREATOR / AGENT_A / AGENT_B / ACTOR). The
# concurrent-transition pin asserts the WINNER's transition event survived in
# provenance; if the winning actor already appeared from a setup step (the claim
# stamps AGENT_A, the in_progress step stamps ACTOR) that assertion would be a
# tautology satisfied by the setup chain rather than by the transition itself.
RESOLVER_MARKS_DONE = "resolver-agent-marks-done"
RESOLVER_MARKS_WONTFIX = "resolver-agent-marks-wontfix"


async def _drive_existing_task_to_done(task_ledger: TaskLedger, task_id: str) -> None:
    """Drive an ALREADY-CREATED task to ``done`` via the legal chain.

    Unlike ``_drive_to_state`` (which mints a FRESH task), this resolves a
    specific EXISTING id — needed to drive a *blocker* to terminal in place so a
    dependent's claim gate and query partition can be checked against a genuinely
    resolved blocker. Legal chain only: open --claim--> claimed -> in_progress -> done.
    """
    claim = await task_ledger.claim_task(task_id, CLAIMER)
    assert claim.claimed, "setup precondition: a fresh open blocker must be claimable"
    await task_ledger.transition(task_id, STATUS_IN_PROGRESS, actor=ACTOR)
    # PKT-06 §4 breaking-change sweep: see ``_drive_to_state``'s matching note.
    await task_ledger.transition(
        task_id, STATUS_DONE, actor=ACTOR, summary="setup: driven to done via the legal chain"
    )


def _partition_gather(results: Sequence[Any], success_type: type) -> tuple[list[Any], list[Any], list[Any]]:
    """Split a ``gather(..., return_exceptions=True)`` result into
    (successes, IllegalTransitionError losers, any OTHER exceptions).

    A racing mutator on the FIXED backend must resolve to exactly one success and
    exactly one typed ``IllegalTransitionError`` loser (the decided lost-race
    semantics); anything else — two successes (broken CAS), zero losers, or a
    different exception type (e.g. a raw store/connection error leaking out of an
    unguarded write) — is a defect this partition surfaces distinctly.
    """
    successes = [r for r in results if isinstance(r, success_type) and not isinstance(r, BaseException)]
    illegal = [r for r in results if isinstance(r, IllegalTransitionError)]
    other = [
        r for r in results
        if isinstance(r, BaseException) and not isinstance(r, IllegalTransitionError)
    ]
    return successes, illegal, other


class TestConcurrentTransitions:
    """The state machine holds under CONCURRENCY: two agents racing a task in
    ``in_progress`` toward two DIFFERENT terminal states — one to ``done``, one to
    ``wontfix`` — must NOT both land (that is an illegal ``done <-> wontfix``
    terminal->terminal edge the module's own invariants forbid).

    The decided semantics (this file is the spec the FIX must satisfy): exactly
    ONE transition wins; the loser raises :class:`IllegalTransitionError` (its
    edge is illegal against the ALREADY-terminal state the winner committed); a
    fresh read shows the winner's terminal status; that terminal status is stable
    (never later flipped to the loser's target — no terminal->terminal composite);
    and the winner's provenance event survives (the loser must not clobber it).

    Two SEPARATE live ledger connections (not two coroutines on one socket) is the
    production-realistic fleet scenario and the only configuration that exercises
    the server-side guard the mutation must ride. The in-loop assertion means ANY
    single iteration exhibiting the two-winners bug fails the test — a race pin
    that passes only by lucky scheduling is itself a defect.
    """

    async def test_concurrent_terminal_transitions_have_exactly_one_winner(
        self, task_ledger_factory: TaskLedgerFactory
    ) -> None:
        ledger_a = await task_ledger_factory()
        ledger_b = await task_ledger_factory()

        for iteration in range(_RACE_ITERATIONS):
            task_id = await _drive_to_state(ledger_a, STATUS_IN_PROGRESS)

            # PKT-06 §4 breaking-change sweep: the done-side racer needs a
            # summary now — WITHOUT one it would deterministically lose on
            # the missing-summary check regardless of the actual CAS race
            # outcome, silently degrading this pin from "exactly one winner
            # of a genuine race" to a trivial always-B-wins case that could
            # no longer catch a broken CAS (finding caught during this
            # packet's own regression sweep, not by the design).
            results = await asyncio.gather(
                ledger_a.transition(
                    task_id, STATUS_DONE, actor=RESOLVER_MARKS_DONE, summary="race: marked done"
                ),
                ledger_b.transition(task_id, STATUS_WONTFIX, actor=RESOLVER_MARKS_WONTFIX),
                return_exceptions=True,
            )
            winners, losers, other = _partition_gather(results, Task)

            # No stray exception type — a lost race is an IllegalTransitionError,
            # never a raw store/connection error leaking from an unguarded write.
            assert not other, f"iteration {iteration}: unexpected exception(s): {other!r}"
            # EXACTLY one winner — never two (both applied an illegal terminal
            # edge), never zero — and exactly one typed loser.
            assert len(winners) == 1, (
                f"iteration {iteration}: expected exactly one winning transition, "
                f"got {len(winners)} — results={results!r}"
            )
            assert len(losers) == 1, (
                f"iteration {iteration}: expected exactly one IllegalTransitionError "
                f"loser, got {len(losers)} — results={results!r}"
            )

            winner_target = winners[0].status
            loser_target = STATUS_WONTFIX if winner_target == STATUS_DONE else STATUS_DONE

            # A fresh read agrees: the committed status is the WINNER's terminal
            # target, never the loser's (no terminal->terminal composite applied).
            persisted = await ledger_a.get_task(task_id)
            assert persisted.status in TERMINAL_STATUSES
            assert persisted.status == winner_target
            assert persisted.status != loser_target

            # The winner's provenance event survived — the loser's refused write
            # did not clobber the provenance object. The winner's actor is a fresh
            # identity that only a SUCCESSFUL transition could have stamped.
            winner_actor = (
                RESOLVER_MARKS_DONE if winner_target == STATUS_DONE else RESOLVER_MARKS_WONTFIX
            )
            assert _provenance_mentions(persisted.provenance, winner_actor)

            # The terminal state is stable — a second read is never different (no
            # late writer flips it afterward).
            reread = await ledger_a.get_task(task_id)
            assert reread.status == persisted.status


class TestConcurrentSupersession:
    """Supersession is SINGLE-successor under both racing and sequential retries.

    ``supersede_task`` mints a fresh open successor AND stamps the old row; two
    concurrent supersedes of the SAME task must NOT each mint a successor (the
    audit-#2 orphan: a live open task nobody references, polluting the backlog).

    Decided semantics (the spec the FIX satisfies): exactly ONE successor is ever
    created — one call returns a new id, the other raises
    :class:`IllegalTransitionError`; the old row's ``superseded_by`` names the
    winner's successor; and the table gains exactly the old row + one successor
    (no orphan). The sequential case the ORIGINAL contract scoped out is now
    DECIDED here too: superseding an ALREADY-superseded task raises
    :class:`IllegalTransitionError` (a superseded task is untransitionable).
    """

    async def test_supersede_of_already_superseded_raises_illegal_transition(
        self, task_ledger: TaskLedger
    ) -> None:
        old_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        first_successor = await task_ledger.supersede_task(
            old_id, subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER, created_by=CREATOR
        )
        # A second supersede of the SAME (now-superseded) row is refused — a
        # superseded task is terminal-like, exactly as it refuses transitions.
        with pytest.raises(IllegalTransitionError):
            await task_ledger.supersede_task(
                old_id, subject=SUBJECT_MEMORY, description=DESCRIPTION_MEMORY, created_by=CREATOR
            )
        # No second successor minted: the old row still points at the FIRST one.
        old_task = await task_ledger.get_task(old_id)
        assert old_task.superseded_by == first_successor

    async def test_concurrent_supersede_creates_exactly_one_successor(
        self, task_ledger_factory: TaskLedgerFactory
    ) -> None:
        ledger_a = await task_ledger_factory()
        ledger_b = await task_ledger_factory()

        for iteration in range(_RACE_ITERATIONS):
            # Snapshot the table BEFORE this iteration's task so the conservation
            # bound is a per-iteration delta (immune to prior-iteration rows).
            before_count = len(await ledger_a.query_tasks())
            old_id = await _create(ledger_a, SUBJECT_XML, DESCRIPTION_XML)

            results = await asyncio.gather(
                ledger_a.supersede_task(
                    old_id, subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER, created_by=AGENT_A
                ),
                ledger_b.supersede_task(
                    old_id, subject=SUBJECT_MEMORY, description=DESCRIPTION_MEMORY, created_by=AGENT_B
                ),
                return_exceptions=True,
            )
            successor_ids, losers, other = _partition_gather(results, str)

            assert not other, f"iteration {iteration}: unexpected exception(s): {other!r}"
            # EXACTLY one successor id returned (never two — the audit-#2 orphan),
            # and exactly one typed loser.
            assert len(successor_ids) == 1, (
                f"iteration {iteration}: expected exactly one successor id, "
                f"got {len(successor_ids)} — results={results!r}"
            )
            assert len(losers) == 1, (
                f"iteration {iteration}: expected exactly one IllegalTransitionError "
                f"loser, got {len(losers)} — results={results!r}"
            )

            winner_successor = successor_ids[0]
            old_task = await ledger_a.get_task(old_id)
            assert old_task.superseded_by == winner_successor

            # Conservation bound: the table grew by EXACTLY the old row + one
            # successor. A second (orphan) successor would make this +3.
            all_tasks = await ledger_a.query_tasks()
            assert len(all_tasks) == before_count + 2, (
                f"iteration {iteration}: expected exactly one successor created "
                f"(delta 2), table grew by {len(all_tasks) - before_count} — orphan successor"
            )
            assert winner_successor in {task.id for task in all_tasks}


class TestBlockedByNormalization:
    """A DUPLICATE id in ``blocked_by`` is normalized to set semantics, and the
    claim gate and query partition AGREE in both the blocked and unblocked phase.

    Audit #3: ``blocked_by=[X, X]`` stored verbatim gives ``array::len == 2`` while
    the resolved-blocker set can only ever be ``[X]`` (``len 1``), so the counts
    never match and the task is UNCLAIMABLE FOREVER even after X resolves — while
    the Python query side reports it unblocked. Decided fix: dedupe at create so a
    duplicate stores as a single id, the dependent is genuinely blocked while X is
    open (claim fails closed AND ``query(blocked=True)`` includes it), and once X
    reaches ``done`` the dependent is BOTH claimable AND in ``query(blocked=False)``
    — the gate and the partition can never disagree.
    """

    async def test_duplicate_blocker_is_deduped_at_create(self, task_ledger: TaskLedger) -> None:
        blocker = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
        dependent = await task_ledger.create_task(
            SUBJECT_LEDGER, DESCRIPTION_LEDGER, blocked_by=[blocker, blocker], created_by=CREATOR
        )
        task = await task_ledger.get_task(dependent)
        # Set semantics: the duplicate collapses to a SINGLE stored id.
        assert len(task.blocked_by) == 1
        assert set(task.blocked_by) == {blocker}

    async def test_duplicate_blocker_gate_and_partition_agree_across_resolution(
        self, task_ledger: TaskLedger
    ) -> None:
        blocker = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
        dependent = await task_ledger.create_task(
            SUBJECT_LEDGER, DESCRIPTION_LEDGER, blocked_by=[blocker, blocker], created_by=CREATOR
        )

        # --- Phase 1: blocker OPEN -> the dependent is genuinely blocked. -------
        # The claim GATE fails closed AND the query PARTITION reports it blocked.
        blocked_attempt = await task_ledger.claim_task(dependent, AGENT_A)
        assert blocked_attempt.claimed is False
        assert blocked_attempt.task.status == STATUS_OPEN  # fail closed, unmutated
        blocked_ids = {task.id for task in await task_ledger.query_tasks(blocked=True)}
        unblocked_ids = {task.id for task in await task_ledger.query_tasks(blocked=False)}
        assert dependent in blocked_ids
        assert dependent not in unblocked_ids

        # --- Phase 2: drive the blocker to DONE -> the dependent is free. -------
        await _drive_existing_task_to_done(task_ledger, blocker)

        # The query PARTITION now reports it unblocked (checked while still open,
        # so the partition is judged on the dependent's own open row)...
        unblocked_after = {task.id for task in await task_ledger.query_tasks(blocked=False)}
        blocked_after = {task.id for task in await task_ledger.query_tasks(blocked=True)}
        assert dependent in unblocked_after
        assert dependent not in blocked_after
        # ...and the claim GATE AGREES: the dependent is now genuinely claimable
        # (NOT unclaimable-forever from a duplicate inflating array::len).
        free_attempt = await task_ledger.claim_task(dependent, AGENT_B)
        assert free_attempt.claimed is True
        assert free_attempt.task.owner == AGENT_B


# ---------------------------------------------------------------------------
# FIX-CYCLE 2 pins (REPORT-fix-audit.md findings #1/#2) — the two provenance /
# false-success concurrency edges that SURVIVED fix cycle 1: a same-target
# transition race (false double-success) and a transition-vs-supersede
# provenance lost-update (independent guard columns, shared JSON blob).
# ---------------------------------------------------------------------------

# Identities for the SAME-target transition race — deliberately distinct from
# every other identity in this file (including RESOLVER_MARKS_DONE, which races
# a DIFFERENT target) so the winner's provenance event can be attributed
# unambiguously to THIS race, never to a coincidental setup stamp.
RACE_ACTOR_ALPHA = "resolver-agent-alpha-same-target"
RACE_ACTOR_BETA = "resolver-agent-beta-same-target"

# Identities for the transition-vs-supersede provenance race — one per mutator,
# so presence of EITHER identity in the persisted provenance unambiguously means
# THAT mutator's event specifically (never satisfied by a setup step: the setup
# chain to in_progress only ever stamps CLAIMER/ACTOR).
PROVENANCE_RACE_TRANSITION_ACTOR = "resolver-agent-transitions-to-blocked"
PROVENANCE_RACE_SUPERSEDE_ACTOR = "orchestrator-agent-supersedes-in-progress"


class TestSameTargetTransitionRace:
    """Finding 1: two agents racing the SAME legal edge on one task (both
    ``in_progress -> done``) must resolve to EXACTLY ONE winner.

    Once the first caller's transition commits, the task is ``done``; the
    SECOND caller's identical ``in_progress -> done`` request is now, from the
    row's post-commit perspective, a ``done -> done`` self-edge — which is not
    a member of ``LEGAL_TRANSITIONS`` and must be refused exactly as any other
    illegal edge is (``TestTransitions.test_illegal_transition_raises_and_leaves_row_untouched``
    already pins that a ``done -> done`` no-op is illegal). The CURRENT bug
    (REPORT-fix-audit.md finding 1, reproduced live and repeatably at authoring
    time; the reproduction COUNT is struck — it measured a build that no longer
    exists and no in-tree instrument reproduces it) instead returns TWO
    ``Task`` successes and silently drops the loser's provenance stamp — this
    pin targets exactly that: never two clean returns, never zero, and the
    winner's own transition event must still be readable afterward.
    """

    async def test_same_target_race_has_exactly_one_winner_and_a_typed_loser(
        self, task_ledger_factory: TaskLedgerFactory
    ) -> None:
        ledger_a = await task_ledger_factory()
        ledger_b = await task_ledger_factory()

        for iteration in range(_RACE_ITERATIONS):
            task_id = await _drive_to_state(ledger_a, STATUS_IN_PROGRESS)

            # PKT-06 §4 breaking-change sweep: both racers now need a summary
            # (mandatory on done) — WITHOUT one, every iteration's loser would
            # raise IllegalTransitionError for the wrong reason (missing
            # summary, not the lost race this pin targets), and the
            # ``done -> done`` self-edge is itself in-scope for §4's OWN
            # non-done-target rule 5 -- N/A here since both targets ARE done.
            result_a, result_b = await asyncio.gather(
                ledger_a.transition(
                    task_id, STATUS_DONE, actor=RACE_ACTOR_ALPHA, summary="alpha finished first"
                ),
                ledger_b.transition(
                    task_id, STATUS_DONE, actor=RACE_ACTOR_BETA, summary="beta finished first"
                ),
                return_exceptions=True,
            )

            a_won = isinstance(result_a, Task)
            b_won = isinstance(result_b, Task)

            # EXACTLY one winner — never two clean returns (the current
            # false-success bug), never zero.
            assert a_won ^ b_won, (
                f"iteration {iteration}: expected exactly one winner, got "
                f"a_won={a_won} (a={result_a!r}) b_won={b_won} (b={result_b!r})"
            )

            winner_result = result_a if a_won else result_b
            loser_result = result_b if a_won else result_a
            winner_actor = RACE_ACTOR_ALPHA if a_won else RACE_ACTOR_BETA

            assert isinstance(winner_result, Task)
            assert winner_result.status == STATUS_DONE

            # The loser's edge is illegal against the ALREADY-committed done
            # state (a done -> done self-edge) — a typed IllegalTransitionError,
            # never a silent second success and never a different exception.
            assert isinstance(loser_result, IllegalTransitionError), (
                f"iteration {iteration}: the loser must raise IllegalTransitionError, "
                f"got {loser_result!r} (this is finding 1 if it is instead a Task)"
            )
            # The refused target is named in the error, exactly the convention
            # every other illegal-transition case in this file follows.
            assert STATUS_DONE in str(loser_result)

            # A fresh read agrees: done, and the WINNER's transition event
            # survived — the loser's refused write must not have clobbered it.
            persisted = await ledger_a.get_task(task_id)
            assert persisted.status == STATUS_DONE
            assert _provenance_mentions(persisted.provenance, winner_actor), (
                f"iteration {iteration}: the winner's ({winner_actor}) transition event "
                f"was lost from provenance — persisted={persisted.provenance!r}"
            )


class TestProvenanceAppendOnly:
    """Finding 2: ``transition`` and ``supersede_task`` guard DIFFERENT columns
    (``status`` vs ``superseded_by``), so both may legitimately commit against
    the SAME claimed-or-in-progress row concurrently — that is not itself a bug.
    The bug (REPORT-fix-audit.md finding 2, reproduced live and repeatably at
    authoring time; the reproduction COUNT is struck for the same reason as
    :class:`TestSameTargetTransitionRace`'s) is that both
    mutators implement provenance as a Python read-modify-write of the WHOLE
    ``provenance`` object, so whichever commits its write LAST silently drops
    the other's appended event — violating the module's own "append-only …
    events log" promise.

    This pin races a legal transition (``in_progress -> blocked``) against a
    supersede of the SAME task and checks the coordination columns settle
    sanely (each column reflects only its OWN mutator's outcome) AND — the
    actual defect target — that BOTH mutators' events survive in the persisted
    ``provenance.events`` log whenever both commit.
    """

    async def test_transition_and_supersede_events_both_survive_when_both_commit(
        self, task_ledger_factory: TaskLedgerFactory
    ) -> None:
        ledger_a = await task_ledger_factory()
        ledger_b = await task_ledger_factory()

        for iteration in range(_RACE_ITERATIONS):
            task_id = await _drive_to_state(ledger_a, STATUS_IN_PROGRESS)

            transition_result, supersede_result = await asyncio.gather(
                ledger_a.transition(task_id, STATUS_BLOCKED, actor=PROVENANCE_RACE_TRANSITION_ACTOR),
                ledger_b.supersede_task(
                    task_id,
                    subject=f"{SUBJECT_MEMORY} (superseding race) #{iteration}",
                    description=DESCRIPTION_MEMORY,
                    created_by=PROVENANCE_RACE_SUPERSEDE_ACTOR,
                ),
                return_exceptions=True,
            )

            transition_won = isinstance(transition_result, Task)
            supersede_won = isinstance(supersede_result, str)

            # Neither mutator may fail with anything OTHER than a typed
            # IllegalTransitionError (a raw store/connection error leaking from
            # an unguarded write is its own distinct defect from this pin's target).
            if not transition_won:
                assert isinstance(transition_result, IllegalTransitionError), (
                    f"iteration {iteration}: transition must lose ONLY as a typed "
                    f"IllegalTransitionError, got {transition_result!r}"
                )
            if not supersede_won:
                assert isinstance(supersede_result, IllegalTransitionError), (
                    f"iteration {iteration}: supersede must lose ONLY as a typed "
                    f"IllegalTransitionError, got {supersede_result!r}"
                )
            # Independent guard columns: at least one of the two must commit —
            # they do not contend for the same column, so a double-loss would
            # mean some THIRD mechanism blocked both (not this pin's target, but
            # worth surfacing loudly rather than silently passing).
            assert transition_won or supersede_won, (
                f"iteration {iteration}: expected at least one of the two "
                f"independent-guard-column mutators to commit, got neither "
                f"(transition={transition_result!r}, supersede={supersede_result!r})"
            )

            persisted = await ledger_a.get_task(task_id)

            # --- coordination-state sanity: each column reflects ONLY its own
            # --- mutator's outcome, independent of what the OTHER one did.
            if transition_won:
                assert persisted.status == STATUS_BLOCKED, (
                    f"iteration {iteration}: a WINNING transition must persist its target status"
                )
            else:
                assert persisted.status == STATUS_IN_PROGRESS, (
                    f"iteration {iteration}: a LOSING transition must leave status untouched"
                )
            if supersede_won:
                # At most one successor: superseded_by names EXACTLY the id this
                # call returned, never a different (phantom) successor.
                assert persisted.superseded_by == supersede_result, (
                    f"iteration {iteration}: superseded_by must name the WINNING successor"
                )
            else:
                assert persisted.superseded_by is None, (
                    f"iteration {iteration}: a LOSING supersede must not stamp superseded_by"
                )

            # --- THE pin: the events log is APPEND-ONLY. A committed mutator's
            # --- event must survive regardless of what the OTHER mutator did to
            # --- the SAME provenance blob afterward — no read-modify-write clobber.
            if transition_won:
                assert _provenance_mentions(persisted.provenance, PROVENANCE_RACE_TRANSITION_ACTOR), (
                    f"iteration {iteration}: the WINNING transition's event was lost from "
                    f"provenance — persisted={persisted.provenance!r}"
                )
            if supersede_won:
                assert _provenance_mentions(persisted.provenance, PROVENANCE_RACE_SUPERSEDE_ACTOR), (
                    f"iteration {iteration}: the WINNING supersede's event was lost from "
                    f"provenance — persisted={persisted.provenance!r}"
                )


# ===========================================================================
# P8a #7: the SINGLE-statement ``_query`` seam's classified-error posture.
#
# ``TaskLedger._query`` splits a caught error into transport (self-heal +
# ``SurrealConnectionError``) vs domain (keep the connection + ``SurrealStoreError``),
# mirroring ``SurrealStore._query``. What it did NOT do was launder the DOMAIN
# branch's message: it interpolated the raw ``{error}`` straight into the raised
# ``SurrealStoreError``. A domain ``ASSERT``/coercion rejection's engine text can
# echo a bound VALUE back verbatim (the ledger #31 leak the multi-statement
# ``execute_transaction`` path already closes), and that text flows to MCP clients
# in P8. These pins fix the seam at BOTH branches, deterministically and without a
# live server: a fake connection raises a scripted ``ServerError`` (domain- or
# transport-``kind``), the same fault-injection shape ``test_surreal_store.py``'s
# ``TestQueryMessageHygiene`` uses.
# ===========================================================================

# A synthetic ASSERT rejection carrying a value that must NEVER reach the raised
# message (mirrors ``test_surreal_store.py``'s ``_SENSITIVE_ENGINE_TEXT``).
_TASK_SENSITIVE_MARKER = "TOP-SECRET-TASK-BOUND-VALUE-7c1f9a"
# LIVE-CAPTURED ASSERT text (SurrealDB 3.1.5, spike-surreal, 2026-07-13; the
# capture script was a scratch file and is gone, but the same wording is
# transcribed from a live probe in
# docs/reference/surrealdb-31-capabilities.md §6.1). The engine says "must conform to";
# it has NEVER said "assertion". The previous, hand-typed value here contained the
# word "assert" and so matched the classifier's marker — which is exactly why the
# ASSERT class looked alive for this repo's entire life while never once firing in
# production (audit B2). Fixture and code shared one imagination.
_TASK_SENSITIVE_ENGINE_TEXT = (
    f"Found '{_TASK_SENSITIVE_MARKER}' for field `status`, with record "
    f"`task:abc123`, but field must conform to: "
    f"$value INSIDE ['open', 'claimed']"
)
# The transport-``kind`` rejection the SDK raises when a mid-life socket drop left
# the reconnected session unauthenticated (``NotAllowed``) — a transport fault,
# never a rejection of the write we sent.
_TASK_TRANSPORT_ENGINE_TEXT = "Anonymous access to the task query is not allowed"


@dataclass
class _RejectingConnection:
    """A fake SDK connection whose ``query`` raises a scripted error — the seam
    fault-injector for ``_query``'s classified-error posture. ``close`` is a
    tolerant no-op so a ledger holding this handle still tears down cleanly.
    """

    error: BaseException

    async def query(self, statement: str, params: dict[str, Any]) -> Any:
        raise self.error

    async def close(self) -> None:
        return None


class TestQueryClassifiedErrorPosture:
    """The single-statement ``_query`` seam classifies like ``execute_transaction``
    (ledger #31): a DOMAIN rejection keeps the healthy connection and raises a
    ``SurrealStoreError`` naming a generic engine CLASS + a server-log hint, NEVER
    the raw engine text; a TRANSPORT fault self-heals (drops the handle) and raises
    ``SurrealConnectionError``. Real-only seam test — built inline with an injected
    fake connection (the fake ledger exposes no ``_query`` seam to fault-inject),
    mirroring ``test_surreal_store.py``'s ``TestQueryMessageHygiene``.
    """

    @staticmethod
    def _ledger_rejecting_with(error: BaseException) -> TaskLedger:
        ledger = TaskLedger(
            url="ws://127.0.0.1:19555/rpc",  # never dialed — the fake handle short-circuits
            namespace="ns",
            database="db",
            user="root",
            password=SecretStr("root"),
        )
        ledger._connection = cast("_SurrealConnection", _RejectingConnection(error=error))
        return ledger

    async def test_domain_rejection_message_never_echoes_the_raw_engine_text(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger = self._ledger_rejecting_with(
            ServerError(ErrorKind.INTERNAL, _TASK_SENSITIVE_ENGINE_TEXT)
        )
        connection_before = ledger._connection
        with caplog.at_level(logging.ERROR, logger="loremaster.tasks"):
            with pytest.raises(SurrealStoreError) as exc_info:
                await ledger._query("UPDATE task SET status = $s", {"s": "poison"})

        message = str(exc_info.value)
        # A domain rejection is a STORE error, not a connection error, and the
        # healthy connection is never thrown away.
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert ledger._connection is connection_before
        # The raw engine text / the value it carries NEVER reaches the message.
        assert _TASK_SENSITIVE_ENGINE_TEXT not in message
        assert _TASK_SENSITIVE_MARKER not in message
        # It DOES carry a classified label + the server-log correlation hint.
        assert "assert violation" in message.lower()
        assert "server log" in message.lower()
        # The FULL engine detail is recoverable server-side (logged before raising).
        error_records = [record for record in caplog.records if record.levelno == logging.ERROR]
        assert error_records, "the full engine detail must be logged server-side"
        logged = " ".join(
            str(value)
            for value in (error_records[0].getMessage(), getattr(error_records[0], "engine_error", ""))
        )
        assert _TASK_SENSITIVE_MARKER in logged

    async def test_transport_failure_drops_the_handle_and_raises_connection_error(self) -> None:
        # The transport branch self-heals: a ``NotAllowed`` (mid-life socket drop
        # reconnected unauthenticated) drops the cached handle so the NEXT call
        # reconnects, and surfaces the connection type — never a raw SDK exception.
        ledger = self._ledger_rejecting_with(
            ServerError(ErrorKind.NOT_ALLOWED, _TASK_TRANSPORT_ENGINE_TEXT)
        )
        with pytest.raises(SurrealConnectionError):
            await ledger._query("SELECT * FROM task", {})
        assert ledger._connection is None  # the dead handle was dropped (self-heal)


# ===========================================================================
# PKT-06 — orchestration ledger verbs: rollup leg 1 (``updated_since``, §1),
# ``updated_at`` stamping, the ledger half of batch create (``create_many``,
# §2), and the done-transition's ``summary``/``report_path`` rules (§4).
#
# The design source (comms-c0-designer, resolved contract):
#   scratchpad/PKT-06-build-design.md
# Every error text below was asserted VERBATIM against that document — it is
# the contract, not a paraphrase. NOTE: that design doc was a scratch file,
# deleted per repo law and never archived; it is gone from disk entirely, so
# the verbatim-transcription claim can no longer be re-checked against its
# source — treat the literals pinned below as the surviving contract and
# re-derive from the spec before changing any of them.
# Every test in this section routes through
# the SAME ``task_ledger``/``task_ledger_factory`` fixtures the rest of this
# file uses, so it runs against BOTH backends (fake-vs-real parity, per the
# repo's adversarial-doubles law) unless a docstring says otherwise.
#
# RED AS AUTHORED — HISTORICAL, NOT CURRENT. ``TaskLedger.create_many`` /
# ``.updated_since`` / the extended ``.transition(summary=, report_path=)`` did
# not exist on the REAL ledger when these pins were written, so this section was
# RED by construction; PKT-06 (f80e95a) shipped all three and it is GREEN today.
# The FAKE tier (``_task_fakes.py``, extended in step with these tests) already
# enforced the §4 rules and stamped ``updated_at``, so several fake-tier
# assertions were GREEN even then; the real tier was the RED that mattered.
# ===========================================================================

_ROLLUP_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


@dataclass
class _TaskSpecStub:
    """A local stand-in for the not-yet-built ``loremaster.tasks.TaskSpec``.

    A MODULE-LEVEL ``from loremaster.tasks import TaskSpec`` would break
    COLLECTION of this entire file the instant it's referenced — the symbol
    does not exist until the builder phase lands it, and this file's
    hundreds of already-green tests above must keep collecting throughout
    RED (repo law: a RED test file must fail for a behavioural reason, never
    an import error blast-radius). This stub is attribute-compatible with
    the design's ``TaskSpec`` (``subject``/``description``/``blocked_by``) —
    the ledger stays key-agnostic and duck-types on those three attributes
    per the design's own "key resolution lives in the DISPATCHER" ruling, so
    a real ``TaskSpec`` and this stub are interchangeable call arguments.
    """

    subject: str
    description: str
    blocked_by: list[str] = field(default_factory=list)


class TestUpdatedSince:
    """§1 leg 1: ``TaskLedger.updated_since`` — the rollup's task-activity read.

    Pins: NOT stamped at create (only claim/transition/supersede-of-the-OLD-
    row count as activity); ASC order by ``updated_at``; the exclusive
    ``since`` boundary; an honest ``total`` that is ``>= len(rows)`` when
    ``limit`` truncates; and the shared positive-int ``limit`` guard (same
    ValueError family as ``FindingLedger.query``'s).
    """

    async def test_never_transitioned_task_never_appears(
        self, task_ledger: TaskLedger
    ) -> None:
        await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        window = await task_ledger.updated_since(_ROLLUP_EPOCH, limit=20)
        assert window.rows == []
        assert window.total == 0

    async def test_claim_transition_and_supersede_of_old_row_all_count(
        self, task_ledger: TaskLedger
    ) -> None:
        claimed_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        await task_ledger.claim_task(claimed_id, AGENT_A)

        transitioned_id = await _drive_to_state(task_ledger, STATUS_CLAIMED)
        await task_ledger.transition(transitioned_id, STATUS_IN_PROGRESS, actor=ACTOR)

        superseded_id = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
        await task_ledger.supersede_task(
            superseded_id,
            subject=SUBJECT_WATCHER,
            description=DESCRIPTION_WATCHER,
            created_by=CREATOR,
        )

        window = await task_ledger.updated_since(_ROLLUP_EPOCH, limit=20)
        seen_ids = {task.id for task in window.rows}
        assert claimed_id in seen_ids
        assert transitioned_id in seen_ids
        # The OLD (superseded) row is what's stamped — a supersession is
        # fleet-visible activity on the row being reframed, per the design.
        assert superseded_id in seen_ids

    async def test_rows_are_ordered_ascending_by_updated_at(
        self, task_ledger: TaskLedger
    ) -> None:
        first = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        await task_ledger.claim_task(first, AGENT_A)
        second = await _create(task_ledger, SUBJECT_LEDGER, DESCRIPTION_LEDGER)
        await task_ledger.claim_task(second, AGENT_B)
        third = await _create(task_ledger, SUBJECT_MEMORY, DESCRIPTION_MEMORY)
        await task_ledger.claim_task(third, AGENT_A)

        window = await task_ledger.updated_since(_ROLLUP_EPOCH, limit=20)
        assert [task.id for task in window.rows] == [first, second, third]
        stamps = [task.updated_at for task in window.rows]
        assert None not in stamps
        typed_stamps = cast(list[datetime], stamps)
        assert typed_stamps == sorted(typed_stamps)

    async def test_boundary_is_exclusive(self, task_ledger: TaskLedger) -> None:
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        claimed = await task_ledger.claim_task(task_id, AGENT_A)
        cursor = claimed.task.updated_at
        assert cursor is not None
        window = await task_ledger.updated_since(cursor, limit=20)
        assert task_id not in {task.id for task in window.rows}

    async def test_total_is_honest_when_limit_truncates(
        self, task_ledger: TaskLedger
    ) -> None:
        for subject in (SUBJECT_XML, SUBJECT_LEDGER, SUBJECT_MEMORY):
            task_id = await _create(task_ledger, subject, DESCRIPTION_XML)
            await task_ledger.claim_task(task_id, AGENT_A)
        window = await task_ledger.updated_since(_ROLLUP_EPOCH, limit=2)
        assert len(window.rows) == 2
        assert window.total == 3

    async def test_empty_group_reports_zero_total_not_a_crash(
        self, task_ledger: TaskLedger
    ) -> None:
        # A window with genuinely nothing in it (SurrealDB's ``GROUP ALL`` over
        # an empty match returns ZERO rows on 3.1 — the missing-projection
        # idiom must default to 0, never index blindly into an empty result).
        window = await task_ledger.updated_since(datetime.now(UTC), limit=20)
        assert window.rows == []
        assert window.total == 0

    @pytest.mark.parametrize("bad_limit", [0, -1])
    async def test_limit_rejects_non_positive(
        self, task_ledger: TaskLedger, bad_limit: int
    ) -> None:
        with pytest.raises(ValueError):
            await task_ledger.updated_since(_ROLLUP_EPOCH, limit=bad_limit)


class TestUpdatedSinceSameStampTies:
    """A deliberately FORCED same-``updated_at``-stamp tie must drop neither
    row and must not crash the ASC sort.

    Deterministic ties are only constructible against a backend whose clock
    this test controls directly — the FAKE, built inline (bypassing
    ``task_ledger_factory``, mirroring how ``TestQueryClassifiedErrorPosture``
    above builds a ``TaskLedger`` inline for a scenario the parametrized
    fixture can't express). The real server clock's resolution makes a true
    tie non-deterministic to force from the client side; the exclusive-
    boundary and ASC-order pins above already cover the real backend's
    ordering contract.
    """

    async def test_tied_stamps_both_survive_and_the_window_is_not_corrupted(
        self,
    ) -> None:
        from _task_fakes import FakeTaskDatabase, FakeTaskLedger

        ledger = FakeTaskLedger(db=FakeTaskDatabase())
        typed_ledger = cast(TaskLedger, ledger)
        first_id = await _create(typed_ledger, SUBJECT_XML, DESCRIPTION_XML)
        second_id = await _create(typed_ledger, SUBJECT_LEDGER, DESCRIPTION_LEDGER)
        await ledger.claim_task(first_id, AGENT_A)
        await ledger.claim_task(second_id, AGENT_B)

        tied_stamp = (await ledger.get_task(first_id)).claimed_at
        assert tied_stamp is not None
        # Force an exact tie directly on the fake's stored rows (never
        # reachable through the public API at this precision) — the point of
        # this test is the SORT/FILTER behaviour under a tie, not how a tie
        # might arise.
        object.__setattr__(ledger.db.tasks[first_id], "updated_at", tied_stamp)
        object.__setattr__(ledger.db.tasks[second_id], "updated_at", tied_stamp)

        window = await ledger.updated_since(_ROLLUP_EPOCH, limit=20)
        assert {task.id for task in window.rows} == {first_id, second_id}
        assert window.total == 2


class TestCreateMany:
    """§2 ledger half: ``TaskLedger.create_many`` — all-or-nothing, positional
    ids, key-agnostic (already-resolved ``blocked_by``); the temp-key
    resolution + the wire-facing validation errors are a DISPATCHER concern
    (test_mcp_server.py), not pinned here.
    """

    async def test_returns_ids_positionally_aligned_with_specs(
        self, task_ledger: TaskLedger
    ) -> None:
        specs = [
            _TaskSpecStub(subject=SUBJECT_XML, description=DESCRIPTION_XML),
            _TaskSpecStub(subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER),
            _TaskSpecStub(subject=SUBJECT_MEMORY, description=DESCRIPTION_MEMORY),
        ]
        ids = await task_ledger.create_many(specs, created_by=CREATOR)
        assert len(ids) == 3
        assert len(set(ids)) == 3  # every id distinct
        for task_id, spec in zip(ids, specs, strict=True):
            task = await task_ledger.get_task(task_id)
            assert task.subject == spec.subject
            assert task.description == spec.description
            assert task.status == STATUS_OPEN

    async def test_blocked_by_is_stored_as_given_and_deduped(
        self, task_ledger: TaskLedger
    ) -> None:
        blocker_id = await _create(task_ledger, SUBJECT_WATCHER, DESCRIPTION_WATCHER)
        specs = [
            _TaskSpecStub(
                subject=SUBJECT_LEDGER,
                description=DESCRIPTION_LEDGER,
                blocked_by=[blocker_id, blocker_id],
            )
        ]
        [dependent_id] = await task_ledger.create_many(specs, created_by=CREATOR)
        dependent = await task_ledger.get_task(dependent_id)
        assert dependent.blocked_by == [blocker_id]

    async def test_provenance_records_the_batch_creator(
        self, task_ledger: TaskLedger
    ) -> None:
        [task_id] = await task_ledger.create_many(
            [_TaskSpecStub(subject=SUBJECT_XML, description=DESCRIPTION_XML)],
            created_by=CREATOR,
        )
        task = await task_ledger.get_task(task_id)
        assert _provenance_mentions(task.provenance, CREATOR)

    async def test_empty_specs_list_raises_value_error(
        self, task_ledger: TaskLedger
    ) -> None:
        # The wire's exact "create_many requires a non-empty 'items' list…"
        # text is the DISPATCHER's — the ledger only needs to refuse an empty
        # batch, not spell the wire message (design: "[] -> ValueError").
        with pytest.raises(ValueError):
            await task_ledger.create_many([], created_by=CREATOR)

    async def test_all_or_nothing_a_rejected_spec_creates_nothing(
        self, task_ledger: TaskLedger
    ) -> None:
        # PKT-06 builder CORRECTION (not a weakening): before create_many was
        # implemented, ``pytest.raises(AttributeError)`` passed COINCIDENTALLY
        # — any call at all raised AttributeError because the ledger had no
        # ``create_many`` method whatsoever, independent of the broken spec
        # below. Now that create_many is implemented (it duck-types on each
        # spec's ``.subject``/``.description``/``.blocked_by`` BEFORE building
        # any transaction fragment — see ``TaskLedger.create_many``), the SAME
        # exception type is raised for the REAL reason: attribute access on
        # ``_BrokenSpec()`` fails on its missing ``.description``. The
        # ``match=`` tightens the assertion so it can no longer pass by
        # coincidence — a future implementation that raised AttributeError for
        # an unrelated reason would now correctly fail this test.
        #
        # A spec that fails to build (missing a required attribute a real
        # TaskSpec would always carry) must abort BEFORE any row lands —
        # simulated here via a spec object missing ``description`` entirely,
        # which raises before this ledger writes anything.
        class _BrokenSpec:
            subject = SUBJECT_XML
            blocked_by: list[str] = []
            # no .description attribute at all

        before = len(await task_ledger.query_tasks())
        with pytest.raises(AttributeError, match="description"):
            await task_ledger.create_many(
                [
                    _TaskSpecStub(subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER),
                    _BrokenSpec(),  # type: ignore[list-item]
                ],
                created_by=CREATOR,
            )
        after = len(await task_ledger.query_tasks())
        assert after == before, (
            "a batch that fails partway through must create NOTHING — "
            "all-or-nothing, never a partial write"
        )

    async def test_caller_supplied_ids_are_used_verbatim(
        self, task_ledger: TaskLedger
    ) -> None:
        # D1 ruling: an optional parallel ``ids`` argument lets the DISPATCHER
        # pre-mint every id (uuid4) and wire sibling ``blocked_by`` references
        # to the REAL ids before the single atomic write — the whole batch
        # lands in ONE ``create_many`` call, never per-wave.
        specs = [
            _TaskSpecStub(subject=SUBJECT_XML, description=DESCRIPTION_XML),
            _TaskSpecStub(subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER),
        ]
        supplied = [uuid4().hex, uuid4().hex]
        returned = await task_ledger.create_many(specs, created_by=CREATOR, ids=supplied)
        assert returned == supplied
        first = await task_ledger.get_task(supplied[0])
        assert first.subject == specs[0].subject
        second = await task_ledger.get_task(supplied[1])
        assert second.subject == specs[1].subject

    async def test_mismatched_ids_length_is_a_value_error(
        self, task_ledger: TaskLedger
    ) -> None:
        specs = [
            _TaskSpecStub(subject=SUBJECT_XML, description=DESCRIPTION_XML),
            _TaskSpecStub(subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER),
        ]
        before = len(await task_ledger.query_tasks())
        with pytest.raises(ValueError) as exc_info:
            await task_ledger.create_many(specs, created_by=CREATOR, ids=[uuid4().hex])
        assert str(exc_info.value) == (
            "create_many 'ids' must align positionally with 'specs' — "
            "got 1 ids for 2 specs"
        )
        after = len(await task_ledger.query_tasks())
        assert after == before, "a rejected 'ids' mismatch must write nothing"


class TestUpdatedAtStamping:
    """``updated_at`` is ``None`` until the first mutation, then stamped by
    claim/transition/supersede (of the OLD row) — never by a mere read.
    """

    async def test_freshly_created_task_has_no_updated_at(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        task = await task_ledger.get_task(task_id)
        assert getattr(task, "updated_at", None) is None

    async def test_claim_stamps_updated_at(self, task_ledger: TaskLedger) -> None:
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        before = datetime.now(UTC)
        result = await task_ledger.claim_task(task_id, AGENT_A)
        after = datetime.now(UTC)
        assert result.task.updated_at is not None
        _assert_recent_utc(result.task.updated_at, not_before=before, not_after=after)

    async def test_transition_stamps_updated_at(self, task_ledger: TaskLedger) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_CLAIMED)
        before = datetime.now(UTC)
        updated = await task_ledger.transition(task_id, STATUS_IN_PROGRESS, actor=ACTOR)
        after = datetime.now(UTC)
        assert updated.updated_at is not None
        _assert_recent_utc(updated.updated_at, not_before=before, not_after=after)

    async def test_supersede_stamps_the_old_rows_updated_at_not_the_successor(
        self, task_ledger: TaskLedger
    ) -> None:
        old_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        before = datetime.now(UTC)
        new_id = await task_ledger.supersede_task(
            old_id, subject=SUBJECT_LEDGER, description=DESCRIPTION_LEDGER, created_by=CREATOR
        )
        after = datetime.now(UTC)
        old_task = await task_ledger.get_task(old_id)
        assert old_task.updated_at is not None
        _assert_recent_utc(old_task.updated_at, not_before=before, not_after=after)
        # The successor is a fresh CREATE — deliberately NOT stamped.
        successor = await task_ledger.get_task(new_id)
        assert getattr(successor, "updated_at", None) is None


class TestDoneSummaryReportPath:
    """§4: the done-transition's ``summary``/``report_path`` rules, checked
    AFTER the existing state-machine edge validation and BEFORE the CAS —
    every error text pinned VERBATIM against the design.
    """

    async def test_done_without_summary_is_refused_with_the_exact_text(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        with pytest.raises(IllegalTransitionError) as exc_info:
            await task_ledger.transition(task_id, STATUS_DONE, actor=ACTOR)
        assert str(exc_info.value) == (
            f"transition to 'done' for task {task_id!r} requires 'summary' — a "
            f"one-line completion digest (max 300 chars) the rollup serves as "
            f"the fleet's durable completion record; pass report_path= too "
            f"when a report file exists"
        )

    async def test_done_with_blank_summary_is_refused_identically(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        with pytest.raises(IllegalTransitionError) as exc_info:
            await task_ledger.transition(task_id, STATUS_DONE, actor=ACTOR, summary="   ")
        assert "requires 'summary'" in str(exc_info.value)

    async def test_done_row_is_untouched_by_a_refused_missing_summary(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        with pytest.raises(IllegalTransitionError):
            await task_ledger.transition(task_id, STATUS_DONE, actor=ACTOR)
        after = await task_ledger.get_task(task_id)
        assert after.status == STATUS_IN_PROGRESS

    async def test_multiline_summary_is_refused_with_the_exact_text(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        with pytest.raises(IllegalTransitionError) as exc_info:
            await task_ledger.transition(
                task_id, STATUS_DONE, actor=ACTOR, summary="line one\nline two"
            )
        assert str(exc_info.value) == (
            f"task {task_id!r} done-summary must be a single line — put "
            f"detail in the report file and pass its path as report_path="
        )

    async def test_carriage_return_in_summary_is_also_refused(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        with pytest.raises(IllegalTransitionError) as exc_info:
            await task_ledger.transition(
                task_id, STATUS_DONE, actor=ACTOR, summary="line one\rline two"
            )
        assert "must be a single line" in str(exc_info.value)

    async def test_over_cap_summary_is_refused_naming_the_actual_length(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        long_summary = "x" * 301
        with pytest.raises(IllegalTransitionError) as exc_info:
            await task_ledger.transition(
                task_id, STATUS_DONE, actor=ACTOR, summary=long_summary
            )
        assert str(exc_info.value) == (
            f"task {task_id!r} done-summary is 301 chars — the cap is 300; "
            f"tighten it (detail belongs in the report file)"
        )

    async def test_exactly_300_char_summary_is_accepted(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        summary = "x" * 300
        updated = await task_ledger.transition(
            task_id, STATUS_DONE, actor=ACTOR, summary=summary
        )
        assert updated.summary == summary

    async def test_report_path_is_optional_on_done(self, task_ledger: TaskLedger) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        updated = await task_ledger.transition(
            task_id, STATUS_DONE, actor=ACTOR, summary="shipped the fix"
        )
        assert updated.summary == "shipped the fix"
        assert updated.report_path is None

    async def test_report_path_round_trips_when_given(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        updated = await task_ledger.transition(
            task_id,
            STATUS_DONE,
            actor=ACTOR,
            summary="shipped the fix",
            report_path="REPORT-comms-c0-contract.md",
        )
        assert updated.report_path == "REPORT-comms-c0-contract.md"
        persisted = await task_ledger.get_task(task_id)
        assert persisted.summary == "shipped the fix"
        assert persisted.report_path == "REPORT-comms-c0-contract.md"

    async def test_multiline_report_path_is_refused(self, task_ledger: TaskLedger) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        with pytest.raises(IllegalTransitionError) as exc_info:
            await task_ledger.transition(
                task_id,
                STATUS_DONE,
                actor=ACTOR,
                summary="shipped the fix",
                report_path="reports/one.md\nreports/two.md",
            )
        assert str(exc_info.value) == (
            f"task {task_id!r} done-report_path must be a single line — put "
            f"detail in the report file and pass its path as report_path="
        )

    async def test_blank_report_path_is_refused(self, task_ledger: TaskLedger) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        with pytest.raises(IllegalTransitionError):
            await task_ledger.transition(
                task_id, STATUS_DONE, actor=ACTOR, summary="shipped the fix", report_path="   "
            )

    async def test_summary_on_a_non_done_target_is_a_value_error(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        with pytest.raises(ValueError) as exc_info:
            await task_ledger.transition(
                task_id, STATUS_BLOCKED, actor=ACTOR, summary="not done yet"
            )
        assert not isinstance(exc_info.value, IllegalTransitionError)
        assert str(exc_info.value) == (
            f"summary/report_path are recorded only on the transition to "
            f"'done' (got target {STATUS_BLOCKED!r}) — omit them here"
        )

    async def test_report_path_alone_on_a_non_done_target_is_also_a_value_error(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        with pytest.raises(ValueError):
            await task_ledger.transition(
                task_id, STATUS_BLOCKED, actor=ACTOR, report_path="reports/x.md"
            )

    async def test_legal_non_done_transition_leaves_summary_and_report_path_none(
        self, task_ledger: TaskLedger
    ) -> None:
        task_id = await _drive_to_state(task_ledger, STATUS_CLAIMED)
        updated = await task_ledger.transition(task_id, STATUS_IN_PROGRESS, actor=ACTOR)
        assert getattr(updated, "summary", None) is None
        assert getattr(updated, "report_path", None) is None

    async def test_summary_and_report_path_are_selectable_after_persistence(
        self, task_ledger: TaskLedger
    ) -> None:
        # Runs against BOTH backends via the parametrized ``task_ledger``
        # fixture, but the [real] tier is the one that actually matters here:
        # it proves the values round-trip through a genuine store re-SELECT
        # (get_task), not merely an echo of the in-memory transition return.
        task_id = await _drive_to_state(task_ledger, STATUS_IN_PROGRESS)
        await task_ledger.transition(
            task_id,
            STATUS_DONE,
            actor=ACTOR,
            summary="landed the ledger verbs",
            report_path="REPORT-comms-c0-contract.md",
        )
        reread = await task_ledger.get_task(task_id)
        assert reread.status == STATUS_DONE
        assert reread.summary == "landed the ledger verbs"
        assert reread.report_path == "REPORT-comms-c0-contract.md"

    async def test_a_task_never_transitioned_to_done_has_no_summary_legacy_none(
        self, task_ledger: TaskLedger
    ) -> None:
        # Legacy-row posture: a task that never reaches done reads back
        # summary/report_path as None — never a missing-attribute crash.
        task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
        task = await task_ledger.get_task(task_id)
        assert getattr(task, "summary", None) is None
        assert getattr(task, "report_path", None) is None


class TestTasksDoesNotHoldTheClassificationLabel:
    """Finding #102 — ``tasks.py`` must never hold the classification label.

    THE pin the cold adversary proved was missing. It built ``wb-string-gate``:
    an otherwise-correct #102 repair whose three rollback pass-throughs here in
    ``tasks.py`` were implemented by substring-matching the classification LABEL
    instead of catching the typed error — the *exact* coupling #102 exists to
    abolish, rebuilt one file over. It scored **545 passed, ruff clean, mypy exit
    0 — byte-identical to a correct build.** Nothing in the contract could see it.

    That build is live-fragile in precisely the #102 way: contention is let
    through only while the string "retryable conflict" happens to appear in the
    typed error's message. Reword the label — or re-classify a root cause the way
    finding #93 legitimately did — and both pass-throughs silently die. Exhausted
    contention is then reported to an agent as a lost CAS ("someone else committed
    first") when in truth nobody knows who holds the row. Zero test signal.

    The repo-wide, evasion-proof instrument is
    ``test_surreal_store.py::TestNoProductionModuleHoldsAClassificationLabel``
    (it bans the label from every production module, so no local rebinding,
    helper, ``startswith`` or f-string can hide the coupling). This pin is the
    named, local mirror of it — it fails FIRST and says exactly which file broke,
    right beside the handlers it protects.
    """

    def test_tasks_does_not_import_the_classification_label(self) -> None:
        from loremaster import tasks

        assert not hasattr(tasks, "_ERROR_CLASS_RETRYABLE_CONFLICT"), (
            "tasks.py imported the classification label. The three rollback "
            "pass-throughs (transition, supersede_task, and any future one) must "
            "catch TxnContentionExhaustedError by TYPE — never by matching label "
            "text. This is the #93 -> #102 kill chain being rebuilt: a label is a "
            "human-facing summary, and rewording one is invisible to every gate."
        )
