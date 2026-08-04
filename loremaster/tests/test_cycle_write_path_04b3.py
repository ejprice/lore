"""Packet 04b-3 — the CYCLE contract (ESC-1 · #273/#272 · CA-11).

Contract author: ``contract-cycle-04b3-1`` (Opus 4.8), session ``pkt04b3``, work order
``REPORT-design-sidecar-04b3-1.md`` §C + §CYCLE-FORKS + §CYCLE-TRILEMMA.  Contract-first:
build-driving pins sit RED against HEAD; pin-the-miss / soundness legs sit green and redden the
day the invariant they guard is broken.

**THE FORKS ARE RULED, THEN THE TRILEMMA** (``REPORT-design-sidecar-04b3-1.md`` §CYCLE-FORKS
2026-08-03 + §CYCLE-TRILEMMA 2026-08-04): the contract author was confirmed right on all three
forks; then an adversary (finding #326) graded the first revision INSUFFICIENT and Fable elected
**VARIANT D** (FORK-B narrows; a single-witness bounded read is UNSOUND when a legacy cycle
coexists — MP-1).  All converged on the write-time cycle guard
:meth:`loremaster.tasks.TaskLedger._refuse_a_cycle`:

  * **FORK A (ESC-1) — Reading 1 CONFIRMED (§C-A RETRACTED).** ESC-1 does NOT ride edges and
    "columns → RED" was wrong: a cycle's CLOSING link names a not-yet-existent task, ``ENFORCED``
    forbids that edge, so it can only be a COLUMN — an edge-only guard fails the MEASURED pin
    ``test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED``.  ESC-1's real
    deliverable is to BOUND the guard's read to the pending task's ancestor CLOSURE (edges bound
    WHICH rows; read those rows' ``blocked_by`` COLUMNS for the closing link; overlay pending
    ``create_many`` sibling refs; ``find_blocked_by_cycle``).  **The satisfiable ESC-1 pin lives
    in ``test_blocks_edge.py``**: the KNOWN_BOUND pin is DELETED and
    ``test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE`` (reusing
    ``_blocked_noise_traffic``, repo #102) replaces it — RED at ``4b952f3``.  No "columns → RED"
    pin exists, deliberately.
  * **FORK B (#273) — NARROWED to VARIANT D** (§CYCLE-TRILEMMA, 2026-08-04; the adversary graded
    my first revision INSUFFICIENT and Fable RETRACTED its own from-minted reformulation).  #273
    swaps ONLY ``_record_legacy_cycles``'s enumeration to ``networkx.simple_cycles`` (deleting ITS
    OWN drop-loop); **``_drop_one_cycle_edge`` STAYS** as the write guard's single legit caller.
    The guard is NOT reformulated — its detection routes through the SHARED ``find_blocked_by_cycle``
    with the KEPT drop-loop (R6: exactly ONE ledger-owned detector; a from-minted second detector
    reddens R6's MUTATION pin, and a single-witness build is UNSOUND — see MP-1).  Pins here:
    networkx-in-production; ENUMERATION-equivalence + MP-4 (routing) live in
    ``test_blocks_edge.py``.  The helper-absence pin was REMOVED (MP-3 dissolved).
  * **FORK C (CA-11) — DEFERRED to a named trigger (§C-CA-11 RETRACTED).** A persisted-id joint
    cycle is UNREACHABLE through the verbs (no verb mutates ``blocked_by`` after birth; every
    create is a fresh SINK; the existence pre-check fails CLOSED), so a "served-cycle-under-load"
    pin cannot discriminate.  CA-11's atomicity is DEFERRED to the trigger "a verb that mutates
    ``blocked_by`` after birth lands."  The tripwire (``test_PIN_THE_MISS_...``) stays GREEN and
    reddens the day that verb lands; the 8-way liveness guard stays GREEN.  NO atomicity pin.
    CA-12 also deferred.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.tasks import TaskLedger

CREATOR = "contract-cycle-04b3-1"
DESCRIPTION = "written by the CYCLE contract"

#: The production module the #273 swap moves ``networkx`` INTO.  Read as source text so the
#: pin observes the ARTIFACT's imports, not a name it was handed.
_TASKS_SOURCE = Path(__file__).resolve().parents[1] / "loremaster" / "tasks.py"

#: ≥8-way with OVERLAPPING lifetimes (store reference §5 rule 1): never 2-way, never a lone
#: green run.  The 20-consecutive-green discipline is a RUN requirement the builder/adversary
#: must satisfy (``_RACE_ITERATIONS`` in ``test_task_ledger.py`` is 20 for the same reason).
_CONCURRENCY_WIDTH = 8


async def _ready_ledger(env: SurrealEnv) -> TaskLedger:
    ledger = TaskLedger(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await ledger.ensure_ready()
    return ledger


@pytest_asyncio.fixture
async def cycle_env() -> AsyncIterator[SurrealEnv]:
    """A fresh throwaway DB on the spike TEST store (:18000), dropped after.

    Every racer in a concurrency leg opens its OWN :class:`TaskLedger` against this ONE
    database — separate live connections are the production-realistic fleet shape and the
    only configuration that exercises the server-side guard the atomic rework must ride
    (``test_task_ledger.py::TestConcurrentTransitions`` uses the same idiom).
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = await _ready_ledger(env)
    try:
        yield env
    finally:
        await ledger.close()
        await drop_database(env)


# ======================================================================================
# #273 — the networkx swap (FORK B, Reading 1 confirmed).
# ======================================================================================


class TestTheAllCycleEnumeratorIsNetworkxInPRODUCTION:
    """RED at ``9983191``.  ⛔ §C-#273 + FORK B (NARROWED by §CYCLE-TRILEMMA, variant D):
    ``_record_legacy_cycles`` swaps ITS hand-rolled drop-an-edge enumeration for
    ``networkx.simple_cycles`` (a PRODUCTION import), deleting ITS OWN drop-loop.

    ⚠ **``_drop_one_cycle_edge`` STAYS** — variant D keeps it as the write guard
    ``_refuse_a_cycle``'s single legitimate caller (the guard's step-over-legacy drop-loop routes
    through the SHARED ``find_blocked_by_cycle``, which R6 forbids replacing with a second
    detector).  The earlier helper-absence pin was REMOVED (§CYCLE-TRILEMMA MP-3 dissolved: it
    was false under D and name-keyed / rename-defeatable — the six-defeats class).  The
    enumeration-twin deletion is instead guarded by this networkx-import pin + MP-4 (routing) +
    the count-equality + member-coverage pins in ``test_blocks_edge.py``.

    ⚠ **Production FLAG owed to the builder (outside a contract author's writable set), do
    NOT skip it:** moving ``networkx`` from test-oracle to production import flips its
    dependency group ``dev → runtime`` and RE-SCOPES the ``[[tool.mypy.overrides]]`` block
    comment (#272, resolved for the TEST tree at ``af3551c``).  The exact edit and the
    IMAGE-dependency consequence are in ``REPORT-contract-cycle-04b3-1.md`` §273-FLAGS.
    """

    def test_networkx_is_imported_by_the_PRODUCTION_tasks_module(self) -> None:
        """The enumerator is the package, in the served artifact — not a hand-rolled twin.

        DISCRIMINATION — "what wrong build still passes this?": a build that keeps the
        hand-rolled enumeration inside ``_record_legacy_cycles`` and never imports ``networkx``
        in production.  That is the build at HEAD, and it fails here.  ⚠ It requires the
        ``import networkx`` MODULE form (not ``from networkx import simple_cycles``), which is
        also what MP-4's ``networkx.simple_cycles`` mutation patches.
        """
        assert _TASKS_SOURCE.is_file(), f"production tasks module not found at {_TASKS_SOURCE}"
        source = _TASKS_SOURCE.read_text(encoding="utf-8")
        assert "import networkx" in source, (
            "the #273 swap moves the ALL-CYCLE enumeration of _record_legacy_cycles onto "
            "networkx.simple_cycles, which makes networkx a PRODUCTION import of "
            "loremaster/loremaster/tasks.py. At HEAD tasks.py imports networkx NOWHERE "
            "(it is imported only by the test-side oracle), so the hand-rolled enumerator is "
            "still live. See §C-#273 and the dev->runtime dependency FLAG in the report."
        )


# ======================================================================================
# CA-11 — DEFERRED (FORK C).  A persisted-id joint cycle is verb-unreachable, so the honest
# contract is the PIN-THE-MISS tripwire + a liveness no-regression guard.  NO atomicity pin.
# ======================================================================================


class TestConcurrentCreatesAreCycleSafeByConstruction:
    """The CA-11 cluster — DEFERRED (``REPORT-design-sidecar-04b3-1.md`` §CYCLE-FORKS FORK C,
    ruled 2026-08-03; §C-CA-11 RETRACTED).

    ⚠ **Verified at ``4b952f3``:** a persisted-id cycle is UNREACHABLE through the ledger
    verbs.  Every created task is a fresh SINK, no verb mutates ``blocked_by`` after birth (the
    three ``SET`` sites write owner/status/claimed_at, status, superseded_by — never
    blocked_by), and the existence pre-check fails CLOSED on a forward reference to a
    not-yet-persisted id — so a task's ancestor set is fixed at birth and no create (concurrent
    or not) can place a task on a cycle.  ``test_a_PERSISTED_ID_cycle_is_UNREACHABLE_at_the_
    TOOL_SEAM_by_construction`` says the same.  CA-11's atomicity is therefore DEFERRED to the
    named trigger "a verb that mutates ``blocked_by`` after birth lands"; no atomicity pin is
    built now, because its "served-cycle-under-load" discriminator cannot discriminate (the
    wrong build serves no cycle either).
    """

    async def test_PIN_THE_MISS_a_tasks_blocked_by_is_FIXED_at_birth(
        self, cycle_env: SurrealEnv
    ) -> None:
        """⛔ **PIN THE MISS / the CA-11 deferral tripwire** (repo law: *"when you cannot close
        a hole, pin it"*).  Green at ``4b952f3``; it REDDENS the day a verb lets an existing
        task gain a dependency — which is the exact FORK-C deferral trigger.

        The invariant that makes FORK C's joint cycle unreachable: creating a DEPENDENT of
        ``blocker`` must NOT add anything to ``blocker``'s own ancestor set.  The blocker stays
        a source; the new task is the sink.  A build that grows a task's ancestor set after
        birth (an ``add_blocker`` / re-parent verb) breaks this AND makes the CA-11 joint cycle
        reachable — at which point CA-11's atomic check-and-write earns its keep.

        ⚠ **NAMED RE-OPEN TRIGGER (= the CA-11 deferral trigger):** the first verb that mutates
        ``blocked_by`` after CREATE.  If you added one deliberately, this pin goes RED — do not
        weaken it; build the CA-11 atomic guard (bounded read inside the write
        ``execute_transaction``, retry via ``_txn.retry_on_conflict``) that its reachability was
        waiting on, with a synthetic-adversary discriminator.
        """
        ledger = await _ready_ledger(cycle_env)
        try:
            blocker = await ledger.create_task("a blocker", DESCRIPTION, created_by=CREATOR)
            before = set((await ledger.transitive_blockers(blocker)).ids)
            assert before == set(), "a freshly created blocker already has dependencies"
            for index in range(3):
                await ledger.create_task(
                    f"dependent {index}", DESCRIPTION, blocked_by=[blocker], created_by=CREATOR
                )
            after = set((await ledger.transitive_blockers(blocker)).ids)
            assert after == before == set(), (
                "creating dependents of a task MUTATED that task's own transitive blocker "
                "set — a task's ancestor set is no longer fixed at birth. FORK C's "
                "unreachability argument is void and the CA-11 joint cycle is now reachable: "
                "build the deferred atomic guard. "
                f"before={sorted(before)} after={sorted(after)}"
            )
        finally:
            await ledger.close()

    async def test_LIVENESS_eight_way_concurrent_creates_on_a_SHARED_blocker_all_land(
        self, cycle_env: SurrealEnv
    ) -> None:
        """The no-regression guard the ESC-1 bounded-read rework must not break (store
        reference §5): at least ``_CONCURRENCY_WIDTH``-way, OVERLAPPING lifetimes, every create
        lands exactly once with no loss and no corruption, its conflicts absorbed by the ONE
        shared retry driver.

        ⚠ This is a LIVENESS guard, not a CA-11 fix-discriminator (CA-11 is deferred — a joint
        cycle is verb-unreachable): 8-way contention here can only prove "no loss / no storm,"
        which the current build already satisfies (that green is itself the FORK-C evidence).
        It is kept because the ESC-1 bounded read still touches shared blocker rows under
        contention, so it must not reintroduce a storm.  The 20-consecutive-green discipline is
        a run requirement on the builder.

        DISCRIMINATION — "what wrong build fails this?": one whose create path drops the shared
        retry driver, so ≥8 racers on a shared blocker storm to txn-exhaustion and some creates
        never land (store reference §5: the pre-fix deterministic backoff measured 43%
        exhaustion at N=8).
        """
        racers = [await _ready_ledger(cycle_env) for _ in range(_CONCURRENCY_WIDTH)]
        try:
            shared = await racers[0].create_task("shared blocker", DESCRIPTION, created_by=CREATOR)

            async def _one(ledger: TaskLedger, index: int) -> list[str]:
                # OVERLAPPING lifetimes: each racer creates TWO dependents so the racers'
                # wire-time transactions genuinely interleave (a start-barrier synchronises
                # Python, not the wire — store reference §5).
                out: list[str] = []
                for step in range(2):
                    out.append(
                        await ledger.create_task(
                            f"racer {index} step {step}",
                            DESCRIPTION,
                            blocked_by=[shared],
                            created_by=CREATOR,
                        )
                    )
                return out

            results = await asyncio.gather(
                *(_one(ledger, index) for index, ledger in enumerate(racers)),
                return_exceptions=True,
            )
            errors = [r for r in results if isinstance(r, BaseException)]
            assert not errors, (
                f"{len(errors)} of {_CONCURRENCY_WIDTH} concurrent create streams RAISED under "
                f"contention on a shared blocker — a create path that does not ride the shared "
                f"retry driver storms to txn-exhaustion (store reference §5). errors={errors!r}"
            )
            landed = {task_id for stream in results for task_id in stream}  # type: ignore[union-attr]
            assert len(landed) == _CONCURRENCY_WIDTH * 2, (
                f"expected {_CONCURRENCY_WIDTH * 2} distinct dependents to land, got "
                f"{len(landed)} — a concurrent create was LOST or an id collided."
            )
            served = {task.id for task in await racers[0].query_tasks()}
            assert landed <= served, (
                f"{len(landed - served)} concurrently-created tasks are missing from a fresh "
                f"read — committed rows were lost under contention."
            )
        finally:
            for ledger in racers:
                await ledger.close()
