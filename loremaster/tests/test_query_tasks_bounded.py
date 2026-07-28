"""Contract ADDENDUM for finding **#253** — the pins ``test_blocks_edge.py``'s SECTION I
does not have.

*Every claim in this file is scoped to the tree at ``98d5084`` (branch
``feat/surreal-unification``), 2026-07-28.  "RED today" means RED at that commit.*

============================================================================
WHY THIS FILE EXISTS, STATED PLAINLY
============================================================================

#253 was ruled into packet 04b-1 (``docs/plans/v2/04-comms-blocks-footer.md`` §04b SPLIT,
the ``#253`` block, committed ``0f4656c``) while the main contract was already in flight.
The mid-flight ping DID reach its author, which produced ``test_blocks_edge.py``'s
**SECTION I** (committed ``98d5084``, 14 pins).  A second author was commissioned in
parallel on the belief that it had not.  **This file is what that second pass found that
SECTION I does not pin — it is an ADDENDUM, never a second copy.**

It therefore re-pins NOTHING.  The instruments it needs (``_seed_unrelated_tasks``,
``_seed_legacy_task``, ``_drive_to``, the ``task_ledger`` fixture, the ledger vocabulary)
are **IMPORTED from** ``test_blocks_edge`` rather than cloned — repo law #102, "if two
call sites need the same POLICY it is a FUNCTION THEY CALL".

✅ **ESCALATION E-C CLOSED, 2026-07-28.**  The rows-read instrument no longer comes from a
sibling TEST module: it lives in ``_surreal_harness`` beside ``run``, as
:func:`~_surreal_harness.measure_store_traffic`, exactly as ``_enforced_relations_scaffold``
houses the migration idiom.  It also CHANGED SEAM in that move — it counts at the
CONNECTION rather than at ``TaskLedger._query`` — because ruling **R7** puts the bounded
read's two reads inside ONE transaction, and a transaction that returns results rides
``query_raw``; a ``_query``-keyed counter would have reported ZERO rows for exactly the
build R7 demands, and zero reads as *"the read did not grow"*.  See that function's
docstring.  The remaining ``test_blocks_edge`` imports are fixture VOCABULARY, which has
no other home and must agree across the two files by construction.

============================================================================
THE HOLES, EACH WITH THE WRONG BUILD THAT WALKS THROUGH IT
============================================================================

Every one was found by asking SECTION I's own question back at it — *"what WRONG build
would still pass this?"* — and **no answer below is an opinion**: each wrong build was
WRITTEN and RUN against both contracts in a provenance-asserted scratch copy (receipts,
including the full mutated bodies, in ``REPORT-contract-04b1-253.md`` §WRONG BUILDS).
Deliberately no count is stated here; two of these were added *because the measurement
contradicted this author's prediction*, and a count in a heading is the thing this repo
has the most receipts against.

* **W-1, the naive push-down** — filters into the store, ``status_by_id`` built from the
  rows the ``WHERE`` returned.  MEASURED to pass the WHOLE of SECTION I, including the two
  pins written to catch exactly it: their blockers are NON-terminal, and there this build's
  fail-closed default answers correctly by accident.  The uncaught direction — a blocker
  that is TERMINAL and outside the candidate set — drops claimable work from the answer.
  → :class:`TestATerminalBlockerOUTSIDEtheCandidateSetStillRESOLVES`.
* **W-2, the ``blocked``-fallback.**  SECTION I's growth pin measures
  ``query_tasks(owner=…)`` and ``query_tasks(status=…)``.  **Neither supplies
  ``blocked=``.**  So a build that pushes the two equality filters into the store and,
  *whenever ``blocked is not None``*, falls back to ``SELECT * FROM task`` to build
  ``status_by_id`` passes SECTION I whole — while leaving #253 unfixed on the one code
  path the finding is about (requirement 1's second clause: *"blocker resolution is
  bounded by the candidate set's blocked_by / blocks edges"*).
  → :class:`TestTheBLOCKEDPathIsBoundedToo`.
* **W-3, the transitive closure.**  04b-1 is *building* a ``blocks`` DAG and a
  ``+collect`` transitive read, and §04b SPLIT says that edge "is plausibly the bounded
  blocker-resolution mechanism the fix wants".  The partition is **ONE HOP** — a task is
  blocked iff one of its OWN ``blocked_by`` entries is non-terminal — and SECTION I's
  deepest fixture is one hop, so nothing there can tell a one-hop resolver from a closure.
  Both error directions are reachable, both are silent, and **both were built**: W-3
  over-blocks (a ``+collect`` closure), **W-3b** under-blocks (the bare ``@.{1..n}`` form,
  which probe §5.3 measured returns TERMINAL-DEPTH nodes only).  Each is killed by a
  different pin in that class, which is why the class holds a complementary PAIR and not
  one "transitivity" test.
  → :class:`TestTheBlockedPartitionIsONEHOPNeverTransitive`.
* **W-4, the narrowed projection.**  Every SECTION I assertion reads ``task.id``.  A
  rewrite emitting ``SELECT id, status, owner, blocked_by, created_at FROM task WHERE …``
  passes all of them while serving ``subject=""``, ``summary=None``, ``report_path=None``,
  ``provenance={}`` — store reference §2's silent-``None``-projection trap, which is LIVE
  for exactly this fix because "push the filters into the store" is the moment somebody
  writes a projection list.
  → :class:`TestTheServedTaskIsFieldIDENTICALToGetTask`.
* **W-5, the interpolated filter value.**  Today the filters are a Python loop, so a
  caller-supplied ``owner`` never reaches query text.  This fix's whole shape is *"put the
  caller's value into the statement"*, and #219's AST sweep found ZERO identities
  interpolated into query text package-wide — a property this change can newly break, and
  which no #253 pin observes.
  → :class:`TestAFilterVALUEIsNeverInterpolatedIntoQueryText`.
* **W-6, the disjunction.**  ``test_task_ledger.py`` pins ``status`` alone and ``owner``
  alone; SECTION I pins ``status``+``blocked`` and ``owner``+``blocked``.  **No pin
  anywhere supplies ``status`` AND ``owner`` together**, so an ``OR``-joined WHERE, or one
  that applies only the first filter it sees, is invisible.
  → :class:`TestTheFiltersAreANDedNotORed`.

============================================================================
RED-BY-DESIGN — AND WHY MOST OF THIS FILE IS GREEN
============================================================================

RED at ``98d5084``: the two legs of
``TestTheBLOCKEDPathIsBoundedToo::test_rows_read_does_NOT_grow_when_BLOCKED_is_also_asked``.
RED since 2026-07-28: every leg of :class:`TestTheLimitIsPUSHEDINTOTheStatement` (ruling
**R5**) and :class:`TestTheTwoReadsShareONESnapshot` (ruling **R7**), both of which are
requirements this file's first version predates.
Everything else is GREEN today and is a **removed-behaviour guard** (delete/replace law):
it pins what today's unbounded full read already gets right, so a bounded rewrite cannot
drop it silently.  A regression pin that is green today AND green after every plausible
rewrite is decoration — so each GREEN class below names, in its docstring, the measured
wrong build it goes RED on.

============================================================================
WHAT THIS FILE DOES NOT PIN
============================================================================

* Anything SECTION I already pins: the ``status``/``owner`` growth property, the
  out-of-filter blocker, the fail-closed phantom blocker, terminal = ``done``/``wontfix``,
  the partition∀claim agreement over ONE-HOP shapes, the duplicate-blocker divergence
  (its E-6).  Those are that section's and are not restated here.
* ~~The tool-level ``limit``~~ — **NOW IN SCOPE** by operator ruling **R5**
  (2026-07-28), which widened 04b-1's writable set into ``server.py`` by one dispatcher
  line.  Pinned in :class:`TestTheLimitIsPUSHEDINTOTheStatement`.  ⚠ Escalation E-D's
  PREMISE was wrong and the correction matters to whoever builds this: the dispatcher does
  not slice after materialisation, it **REJECTS** ``limit`` outright for every non-rollup
  action (re-derived at ``faf035d``: ``tasks(action='query', limit=5)`` raises
  ``ValueError: 'since'/'limit' apply only to action='rollup' …``).  So R5 is not a
  re-ordering, it is a new accepted parameter.
  ✅ **ESCALATION ESC-1 IS DISCHARGED, AND IT WAS UNDER-COUNTED (wave r5, 2026-07-28).**  It
  said *"TWO committed pins in ``test_mcp_server.py`` assert today's rejection"*.  MEASURED
  on a reference build: **FIVE** pins there break on a CORRECT build — the two R9 ones, R6's
  cycle class against a ``pytest.raises(ValueError)``, and TWICE
  ``_task_fakes.FakeTaskLedger.query_tasks`` not accepting R5's ``limit`` (the identical
  ripple ESC-1 reasoned about for ``ensure_ready`` and never applied to ``query_tasks``).
  **All five are now RE-AUTHORED IN PLACE**, green before the fix and after, so a builder
  meets NO red test outside this contract.  Each carries a ``RE-AUTHORED 2026-07-28``
  docstring naming the ruling that retired its old assertion and the pin that now owns the
  property; the two fake-side ones are ``_task_fakes.FakeTaskLedger.query_tasks``' new
  ``limit`` parameter.
* Result ORDER.  ``query_tasks`` promises none (``_task_fakes`` deliberately reorders to
  keep consumers honest), so store reference §7's *ORDER BY under an explicit projection*
  hazard is a REPORTED RISK for the builder, not an invented requirement pinned here.
* Concurrency.  A racing writer between the candidate read and the blocker read is a real
  TOCTOU for any two-read rewrite; a contract pin is the wrong instrument (≥8-way × 20
  consecutive green runs).  Flagged in the report, NOT silently dropped.
"""

from __future__ import annotations

import inspect
import uuid
from typing import Any

import pytest
from _sdk_guard import SDK_CONNECTION_CLASSES
from _surreal_harness import (
    PRODUCTION_DIM,
    StoreTraffic,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    measure_store_traffic,
    run,
    unique_database,
)
from loremaster.store.surreal_schema import TASK_TABLE
from loremaster.tasks import (
    STATUS_CLAIMED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    STATUS_WONTFIX,
    Task,
    TaskLedger,
)

# The instruments and vocabulary this addendum SHARES with the main contract. Imported,
# never re-implemented — a second copy of the rows-read instrument is exactly the #102
# shape, and a second copy of the fixture vocabulary is how two suites come to disagree
# about what a phantom id looks like.
from test_blocks_edge import (  # noqa: I001 - local test module, resolved via the tests dir
    ACTOR,
    CREATOR,
    DESCRIPTION,
    UNRELATED_TASK_COUNT_LARGE,
    UNRELATED_TASK_COUNT_SMALL,
    _drive_to,
    _seed_legacy_task,
    _seed_unrelated_tasks,
    task_ledger,  # noqa: F401 - re-exported pytest fixture
)

#: A second owner identity, so every owner pin has something to be WRONG about. A single
#: owner in a fixture makes ``owner=X`` and "every owned task" indistinguishable.
OTHER_ACTOR = "reviewer-04b1"

#: The cap every ruling-R5 pin asks for.  Strictly between 1 and
#: ``UNRELATED_TASK_COUNT_SMALL``, so *"served exactly this many"* is distinguishable from
#: *"served the whole answer"* AND from *"served one"* — a limit equal to either boundary
#: makes a wrong build look right.
_SERVED_LIMIT = 3

#: Filter VALUES chosen to be hostile to string interpolation, one per escape mechanism.
#: FIXTURES MUST DISCRIMINATE: a single quote alone is defeated by a build that escapes
#: quotes and nothing else, so the set spans quote, double-quote, backslash, and a
#: SurrealQL comment/terminator sequence. Each is a legal ``owner`` today — ``claim_task``
#: takes free text — so a build that binds parameters serves them all correctly.
HOSTILE_FILTER_VALUES = (
    "o'neill",
    'agent-"quoted"',
    "back\\slash",
    "x' OR record::id(id) != '' --",
)


async def _ids(ledger: TaskLedger, **filters: Any) -> set[str]:
    """The id set ``query_tasks`` serves for ``filters`` — the shape every pin compares."""
    return {task.id for task in await ledger.query_tasks(**filters)}


async def _served_rows(ledger: TaskLedger, **filters: Any) -> Any:
    """``query_tasks(**filters)``'s RAW return — the CONTAINER, not the id set.

    Reached through ``**filters`` for exactly :func:`_ids`' reason: ``limit`` is a parameter
    ruling **R5** ADDS, and a typed call site naming it would be a MYPY ERROR today rather
    than a RED pin — a contract that fails its own gate before a builder ever sees it
    (finding #133's sibling reasoning).
    """
    return await ledger.query_tasks(**filters)


async def _collect(ledger: TaskLedger, sink: set[str], **filters: Any) -> None:
    """Run ``query_tasks(**filters)`` and record the served ids into ``sink``.

    :func:`~_surreal_harness.measure_store_traffic` takes a zero-argument callable and
    returns TRAFFIC, so the served ANSWER has to leave by a side channel; this is that
    channel. Both halves are asserted by every caller — see
    :meth:`TestTheBLOCKEDPathIsBoundedToo._measure`.
    """
    sink.clear()
    sink.update(task.id for task in await ledger.query_tasks(**filters))


async def _fresh_ledger() -> tuple[TaskLedger, SurrealEnv]:
    """A ready :class:`TaskLedger` on its own database.

    The growth pins need TWO ledgers of DIFFERENT sizes inside one test, which the
    session's ``task_ledger`` fixture (one ledger per test) cannot give them; the caller
    closes and drops. Deliberately the same construction SECTION I's ``_measure`` uses.
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = TaskLedger(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await ledger.ensure_ready()
    return ledger, env


# =========================================================================== #
# HOLE 1 — the ``blocked`` partition's OWN read is unbounded, and SECTION I never
# supplies ``blocked=`` to the instrument that would see it.
# =========================================================================== #


class TestTheBLOCKEDPathIsBoundedToo:
    """⛔ **RED at ``98d5084``** — kills measured wrong build **W-2**.

    Requirement 1 has two clauses and SECTION I pins one: *"``status``/``owner`` push into
    the store"* (pinned there) **AND** *"blocker resolution is bounded by the candidate
    set's ``blocked_by`` / ``blocks`` edges"* (pinned HERE).  The second clause is the
    load-bearing one, because it is the read whose unboundedness the method's own
    docstring justifies — and SECTION I's growth measurement never asks for it: both of
    its legs call ``query_tasks`` with exactly one keyword, neither of them ``blocked``.

    W-2 — *push the equality filters down; when ``blocked is not None``, keep
    ``SELECT * FROM task`` for ``status_by_id``* — is the natural conservative rewrite (it
    is even the SAFE one semantically, which is why it survives every correctness pin) and
    it fixes #253 on no path that matters.

    THE DISCRIMINATION IS A GROWTH COMPARISON, not a threshold — a threshold is a fixture
    value a builder tunes until it passes.  The ANSWER is held identical at both ledger
    sizes by construction, so any difference in rows-read is caused by the LEDGER.
    """

    @staticmethod
    async def _measure(unrelated_count: int, *, by_owner: bool) -> tuple[int, set[str]]:
        """Rows read AND the answer served, for one ``blocked``-bearing filtered query.

        The answer is returned alongside the count because a rows-read pin ALONE is
        satisfied perfectly by a build that reads nothing and answers nothing: "it did not
        grow" is true of ``return []``.  Both legs are asserted at both sizes.
        """
        ledger, env = await _fresh_ledger()
        try:
            await _seed_unrelated_tasks(ledger, unrelated_count)
            blocker = await ledger.create_task("a resolved blocker", DESCRIPTION, created_by=CREATOR)
            target = await ledger.create_task(
                "the target of a blocked-partition query",
                DESCRIPTION,
                blocked_by=[blocker],
                created_by=CREATOR,
            )
            await _drive_to(ledger, blocker, STATUS_DONE)
            if by_owner:
                claim = await ledger.claim_task(target, OTHER_ACTOR)
                assert claim.claimed, (
                    "the fixture could not claim its target, so this measurement would "
                    "compare two empty answers and could not discriminate anything"
                )
                served: set[str] = set()
                rows = (
                    await measure_store_traffic(
                        ledger,
                        lambda: _collect(ledger, served, owner=OTHER_ACTOR, blocked=False),
                    )
                ).rows
                return rows, served
            await ledger.transition(target, STATUS_WONTFIX, actor=ACTOR)
            served = set()
            rows = (
                await measure_store_traffic(
                    ledger,
                    lambda: _collect(ledger, served, status=STATUS_WONTFIX, blocked=False),
                )
            ).rows
            return rows, served
        finally:
            await ledger.close()
            await drop_database(env)

    @pytest.mark.parametrize("by_owner", [False, True], ids=["status-filter", "owner-filter"])
    async def test_rows_read_does_NOT_grow_when_BLOCKED_is_also_asked(self, by_owner: bool) -> None:
        """Both equality filters, because a fix may reach only one of them."""
        small_rows, small_answer = await self._measure(UNRELATED_TASK_COUNT_SMALL, by_owner=by_owner)
        large_rows, large_answer = await self._measure(UNRELATED_TASK_COUNT_LARGE, by_owner=by_owner)

        # ⚠ CARDINALITY, never id equality: the two measurements run against two SEPARATE
        # databases and every id is a fresh uuid4, so the id SETS can never be equal. An
        # earlier draft asserted equality and went red for that reason alone — a pin that
        # fails before it can measure anything is not a stricter pin, it is a broken one.
        assert len(small_answer) == len(large_answer) == 1, (
            f"the two measurements served {len(small_answer)} and {len(large_answer)} tasks; "
            f"each must serve the ONE target. TWO readings, and both matter: either the "
            f"fixture drifted (a rows-read comparison between different answers measures "
            f"nothing), or the build HID the target — its only blocker is `done` and sits "
            f"OUTSIDE the caller's candidate set, so a rewrite that resolves blockers only "
            f"from the rows its WHERE returned marks it unresolved and drops claimable work "
            f"from the answer. That second reading has its own pin: see "
            f"TestATerminalBlockerOUTSIDEtheCandidateSetStillRESOLVES"
        )
        assert small_rows > 0, (
            "the instrument counted ZERO rows for a query that returned a task — it is not "
            "observing this call path at all, so its 'did not grow' verdict is worthless"
        )
        assert large_rows == small_rows, (
            f"query_tasks read {small_rows} rows against a ledger of "
            f"{UNRELATED_TASK_COUNT_SMALL} unrelated tasks but {large_rows} against one of "
            f"{UNRELATED_TASK_COUNT_LARGE}, for the SAME one-task answer — so the read is "
            f"scaling with the LEDGER. ⚠ SECTION I's growth pin passes for a build that "
            f"fails this one: it never supplies blocked=, so a rewrite that keeps "
            f"'SELECT * FROM task' whenever the blocked partition is requested satisfies it "
            f"while leaving #253 unfixed. Blocker resolution must be bounded by the "
            f"CANDIDATE set's blocked_by / blocks edges, not by the table"
        )

    async def test_the_UNFILTERED_blocked_read_is_ALLOWED_to_grow(self) -> None:
        """⛔ The positive control, and a DELIBERATE non-requirement stated as a pin.

        Two jobs in one measurement.  (1) A control: the pin above is a negative result
        ("this number did not grow"), and a negative result from a blind instrument is
        indistinguishable from a negative result from a working one — so the SAME
        instrument, on the SAME call, must be shown GROWING when the answer legitimately
        grows.  (2) A boundary declaration: ``query_tasks(blocked=…)`` with no
        ``status``/``owner`` asks about EVERY task, so its cost is the ANSWER's cost and
        bounding it is not a requirement.  A builder who "fixes" this number — by capping
        the unfiltered read — has changed the served answer, and this pin says so.
        """

        async def _unfiltered(unrelated_count: int) -> tuple[int, int]:
            ledger, env = await _fresh_ledger()
            try:
                await _seed_unrelated_tasks(ledger, unrelated_count)
                served: set[str] = set()
                rows = (
                    await measure_store_traffic(
                        ledger, lambda: _collect(ledger, served, blocked=False)
                    )
                ).rows
                return rows, len(served)
            finally:
                await ledger.close()
                await drop_database(env)

        small_rows, small_answer = await _unfiltered(UNRELATED_TASK_COUNT_SMALL)
        large_rows, large_answer = await _unfiltered(UNRELATED_TASK_COUNT_LARGE)
        assert (small_answer, large_answer) == (
            UNRELATED_TASK_COUNT_SMALL,
            UNRELATED_TASK_COUNT_LARGE,
        ), (
            f"the unfiltered blocked=False read answered {small_answer} / {large_answer} "
            f"tasks where every seeded task is unblocked — the fixture, not the pin, is wrong"
        )
        assert large_rows > small_rows, (
            f"the rows-read instrument reported {small_rows} then {large_rows} for a read "
            f"whose ANSWER grew from {UNRELATED_TASK_COUNT_SMALL} to "
            f"{UNRELATED_TASK_COUNT_LARGE} tasks. Either the instrument is blind — in which "
            f"case every 'did not grow' result in this file is worthless — or the unfiltered "
            f"read has been capped, which silently truncates a served answer"
        )


# =========================================================================== #
# HOLE 1b — the out-of-candidate blocker that is TERMINAL.  SECTION I pins the
# out-of-filter blocker only where it is NON-terminal, and there the naive push-down's
# fail-closed default happens to give the right answer.
# =========================================================================== #


class TestATerminalBlockerOUTSIDEtheCandidateSetStillRESOLVES:
    """GREEN at ``98d5084`` — a removed-behaviour guard.  Kills measured wrong build **W-1**.

    ⛔⛔ **THIS IS THE HOLE IN THE PIN CLASS WRITTEN TO GUARD THIS PROPERTY, and it was
    found by BUILDING the naive push-down rather than by reading the pins.**

    SECTION I's ``TestTheBoundedReadKeepsTheClaimAgreement`` pins *"a blocker excluded by
    the caller's filter still counts"* twice — with an ``in_progress`` blocker and with a
    ``claimed`` blocker.  **Both are NON-TERMINAL, so both expect BLOCKED**, and the naive
    rewrite (build ``status_by_id`` from the rows the WHERE returned, and let
    ``_is_blocked``'s fail-closed default handle the rest) answers BLOCKED for *every*
    blocker it cannot see.  It therefore passes both pins **for the wrong reason** — and
    MEASURED, it passes the whole of SECTION I: the third out-of-filter pin's blocker is a
    phantom (fail-closed is genuinely right there) and the ∀ agreement pin queries
    ``blocked=False`` with NO status/owner, so its candidate set is the whole table and the
    rewrite is indistinguishable from correct.

    The direction nothing reaches is a blocker that is **TERMINAL and outside the candidate
    set**.  Truth: it resolves, the dependent is claimable.  The naive rewrite: unresolved,
    therefore blocked, therefore **dropped from the answer** — claimable work made invisible
    to the fleet, with no error anywhere and the claim CAS cheerfully granting it to anyone
    who asks by id.  This is the SAME defect class as the "hidden work" the finding is about,
    reached from the opposite side.
    """

    @staticmethod
    async def _blocked_by_a_done_task(ledger: TaskLedger) -> str:
        """A task that is OPEN, unowned, and whose single blocker has reached ``done``."""
        blocker = await ledger.create_task("a blocker that got finished", DESCRIPTION, created_by=CREATOR)
        dependent = await ledger.create_task(
            "open work whose dependency is already done",
            DESCRIPTION,
            blocked_by=[blocker],
            created_by=CREATOR,
        )
        await _drive_to(ledger, blocker, STATUS_DONE)
        return dependent

    async def test_a_DONE_blocker_outside_the_STATUS_candidate_set_still_RESOLVES(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811 - the imported fixture
    ) -> None:
        """The blocker is ``done``; the caller asks for ``open`` — so it is NOT a candidate."""
        ledger, _env, _seed = task_ledger
        dependent = await self._blocked_by_a_done_task(ledger)

        served = await _ids(ledger, status=STATUS_OPEN, blocked=False)
        assert dependent in served, (
            "a task whose ONLY blocker has reached `done` was dropped from "
            "query_tasks(status='open', blocked=False). The blocker is `done`, so the "
            "caller's status filter excludes it from the CANDIDATE set — and a rewrite that "
            "builds status_by_id from the rows its WHERE returned then cannot see it and "
            "falls back to UNRESOLVED. Fail-closed is right for an id that names NO row; it "
            "is WRONG for a row the filter merely hid. ⚠ SECTION I's two out-of-filter pins "
            "use NON-terminal blockers, where this same wrong build answers correctly by "
            "accident — this is the direction that hides claimable work from the fleet"
        )
        claim = await ledger.claim_task(dependent, ACTOR)
        assert claim.claimed, (
            "the claim CAS refused a task whose only blocker is done, so the partition was "
            "right to hide it and this pin's premise is wrong — escalate, do not 'fix' the query"
        )

    async def test_a_DONE_blocker_outside_the_OWNER_candidate_set_still_RESOLVES(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811 - the imported fixture
    ) -> None:
        """The second filter: the blocker is unowned, the caller asks for an owner's work."""
        ledger, _env, _seed = task_ledger
        dependent = await self._blocked_by_a_done_task(ledger)
        claim = await ledger.claim_task(dependent, OTHER_ACTOR)
        assert claim.claimed, "the fixture could not claim its dependent, so nothing below can be seen"

        served = await _ids(ledger, owner=OTHER_ACTOR, blocked=False)
        assert dependent in served, (
            f"a task held by {OTHER_ACTOR!r} was dropped from its owner's own unblocked "
            f"view because its resolved `done` blocker is held by nobody and so falls "
            f"outside the owner candidate set. An agent asking 'what of MINE can I work "
            f"on?' is served an incomplete answer — the worst direction for a trust surface"
        )


# =========================================================================== #
# HOLE 2 — the partition is ONE HOP, and every #253 fixture is one hop deep.
# =========================================================================== #


class TestTheBlockedPartitionIsONEHOPNeverTransitive:
    """GREEN at ``98d5084`` — a removed-behaviour guard.  Kills measured wrong build **W-3**.

    ⛔ **THE TEMPTATION IS BUILT INTO THIS PACKET.**  04b-1 mints a ``blocks`` DAG and a
    ``+collect`` transitive blocker read in the same wave; §04b SPLIT says that edge "is
    plausibly the bounded blocker-resolution mechanism the fix wants".  It is the right
    mechanism at the WRONG DEPTH: ``query_tasks``' partition and the claim CAS
    (``tasks.py::TaskLedger._claim_fragment``) both ask a strictly ONE-HOP question — *are
    MY OWN ``blocked_by`` entries terminal* — and the CAS cannot be changed to agree,
    because it is a single ``array::len`` comparison against this row's own column.

    Both error directions are reachable, and each is forced by its own fixture:

    * **over-blocking** (a closure): a task whose direct blocker is TERMINAL but whose
      blocker's blocker is not.  Served as blocked; the CAS claims it happily.
    * **under-blocking** (the ``@.{1..n}`` terminal-depth read, which probe §5.3 measured
      returns terminal-depth nodes ONLY): a task whose direct blocker is OPEN but whose
      deeper chain is terminal.  Served as claimable; the CAS refuses it forever.

    ⚠ The mid-chain terminal blocker is reached by ``open -> wontfix``, which
    ``_validate_transition`` allows REGARDLESS of that task's own blockers — so this is a
    state the production ledger reaches today, not a contrivance.
    """

    async def test_a_task_whose_DIRECT_blocker_is_TERMINAL_is_UNBLOCKED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811 - the imported fixture
    ) -> None:
        """Over-blocking: ``root``(open) ← ``mid``(wontfix) ← ``leaf``.  ``leaf`` is FREE."""
        ledger, _env, _seed = task_ledger
        root = await ledger.create_task("the root, left open", DESCRIPTION, created_by=CREATOR)
        mid = await ledger.create_task(
            "the mid link, wontfixed while its own blocker is open",
            DESCRIPTION,
            blocked_by=[root],
            created_by=CREATOR,
        )
        await ledger.transition(mid, STATUS_WONTFIX, actor=ACTOR)
        leaf = await ledger.create_task(
            "the leaf, blocked only by the wontfixed mid",
            DESCRIPTION,
            blocked_by=[mid],
            created_by=CREATOR,
        )

        unblocked = await _ids(ledger, blocked=False)
        assert leaf in unblocked, (
            "a task whose ONLY blocker is terminal (wontfix) was served as BLOCKED because "
            "something deeper in the chain is open. The partition is ONE HOP — the claim CAS "
            "compares array::len(blocked_by) against this row's OWN resolved blockers and "
            "knows nothing about the chain — so a transitive/+collect resolver makes the two "
            "disagree in the direction that hides claimable work from the fleet forever"
        )
        assert mid not in unblocked, (
            "the MID link was served as unblocked, but its own blocker is open — a task's "
            "own terminal STATUS does not resolve its dependencies. This fixture cannot "
            "discriminate a one-hop resolver from a closure unless mid is genuinely blocked"
        )
        claim = await ledger.claim_task(leaf, ACTOR)
        assert claim.claimed, (
            "the claim CAS refused the leaf, so the divergence is on the CAS side and this "
            "pin's premise is wrong — escalate rather than 'fixing' the query"
        )

    async def test_a_task_whose_DIRECT_blocker_is_OPEN_is_BLOCKED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811 - the imported fixture
    ) -> None:
        """Under-blocking: ``root``(done) ← ``mid``(open) ← ``leaf``.  ``leaf`` is BLOCKED."""
        ledger, _env, _seed = task_ledger
        root = await ledger.create_task("the root, driven to done", DESCRIPTION, created_by=CREATOR)
        await _drive_to(ledger, root, STATUS_DONE)
        mid = await ledger.create_task(
            "the mid link, left open above a done root",
            DESCRIPTION,
            blocked_by=[root],
            created_by=CREATOR,
        )
        leaf = await ledger.create_task(
            "the leaf, blocked by the open mid", DESCRIPTION, blocked_by=[mid], created_by=CREATOR
        )

        unblocked = await _ids(ledger, blocked=False)
        assert leaf not in unblocked, (
            "a task whose direct blocker is OPEN was served as claimable because the DEEPER "
            "chain is terminal. Probe §5.3 measured that the bare @.{1..n} recursive form "
            "returns TERMINAL-DEPTH nodes only — resolve blockers with it and the direct "
            "blocker vanishes from the answer. The claim CAS reads this row's own column and "
            "refuses forever, so the fleet is told to attempt a claim that can never win"
        )
        assert mid in unblocked, (
            "the MID link was served as blocked although its only blocker is done — the "
            "fixture cannot discriminate under-blocking unless mid is genuinely free"
        )
        claim = await ledger.claim_task(leaf, ACTOR)
        assert not claim.claimed, (
            "the claim CAS ACCEPTED a task whose direct blocker is open — a different and "
            "worse defect than the one this pin was written for"
        )

    async def test_the_partition_AGREES_with_the_CLAIM_over_a_DEEP_BRANCHING_dag(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811 - the imported fixture
    ) -> None:
        """⛔ The packet's non-negotiable fixture floor: **≥3 deep AND branching**.

        §04b SPLIT's #253 block: *"a 2-node chain cannot tell the closure from the
        terminal-depth read."*  SECTION I's agreement pin is a ∀ over one-hop SHAPES; this
        is the same agreement over DEPTH and BRANCHING, which is the axis a DAG-based
        rewrite is graded on.  Four levels, a diamond, and a node with two blockers whose
        statuses differ.

        ⚠ Ordering: the partition is read for the whole DAG FIRST, then every claim is
        attempted — a claim is destructive.  No claim in this sweep can reach a TERMINAL
        status (``claimed`` is not terminal), so no claim can change another task's
        blockedness mid-sweep; a fixture that could would make this pin order-dependent.

        ⚠⚠ **THE AGREEMENT SWEEP COVERS OPEN, UNOWNED TASKS ONLY, AND THAT IS LOAD-BEARING.**
        "Unblocked" and "claimable" are DIFFERENT predicates: the CAS also guards ``status =
        'open'``, ``owner IS NONE`` and ``superseded_by IS NONE``.  A ``done`` task with no
        dependencies is legitimately in ``blocked=False`` and legitimately unclaimable, so
        sweeping it would report a divergence that is not one — this pin's first draft did
        exactly that and went red at ``98d5084`` on ``L0 root done``, which is NOT a defect.
        The non-open nodes stay in the DAG as STRUCTURE and get their own partition
        assertions below; the membership guard makes the restriction impossible to lose.
        """
        ledger, _env, _seed = task_ledger
        shapes: dict[str, str] = {}

        # L0 — two roots with opposite fates.
        root_open = await ledger.create_task("L0 root, open", DESCRIPTION, created_by=CREATOR)
        root_done = await ledger.create_task("L0 root, done", DESCRIPTION, created_by=CREATOR)
        await _drive_to(ledger, root_done, STATUS_DONE)
        shapes["L0 root open"] = root_open

        # L1 — one terminal-above-an-open-blocker, one open-above-a-done-blocker.
        mid_wontfix = await ledger.create_task(
            "L1 mid, wontfixed above an open root", DESCRIPTION, blocked_by=[root_open], created_by=CREATOR
        )
        await ledger.transition(mid_wontfix, STATUS_WONTFIX, actor=ACTOR)
        mid_open = await ledger.create_task(
            "L1 mid, open above a done root", DESCRIPTION, blocked_by=[root_done], created_by=CREATOR
        )
        shapes["L1 mid open"] = mid_open

        # L2 — the branch: one leaf per mid, plus a DIAMOND node depending on both.
        leaf_free = await ledger.create_task(
            "L2 leaf under the wontfixed mid", DESCRIPTION, blocked_by=[mid_wontfix], created_by=CREATOR
        )
        leaf_stuck = await ledger.create_task(
            "L2 leaf under the open mid", DESCRIPTION, blocked_by=[mid_open], created_by=CREATOR
        )
        leaf_diamond = await ledger.create_task(
            "L2 leaf under BOTH mids",
            DESCRIPTION,
            blocked_by=[mid_wontfix, mid_open],
            created_by=CREATOR,
        )
        shapes["L2 leaf free"] = leaf_free
        shapes["L2 leaf stuck"] = leaf_stuck
        shapes["L2 leaf diamond"] = leaf_diamond

        # L3 — depth four, under a leaf that is itself free but NOT terminal.
        deep = await ledger.create_task(
            "L3 under a free-but-open leaf", DESCRIPTION, blocked_by=[leaf_free], created_by=CREATOR
        )
        shapes["L3 deep"] = deep

        unblocked = await _ids(ledger, blocked=False)
        partition_says = {label: task_id in unblocked for label, task_id in shapes.items()}

        # The two structural nodes the agreement sweep deliberately excludes, pinned on the
        # PARTITION alone — they carry the depth this DAG is built for, so a rewrite that
        # mishandled them would otherwise leave no trace.
        assert root_done in unblocked, (
            "the done root has NO dependencies, so it belongs to the unblocked partition "
            "however terminal its own status is — 'blocked' is a statement about a task's "
            "blocked_by entries, never about the task's own status"
        )
        assert mid_wontfix not in unblocked, (
            "the wontfixed mid link was served as unblocked although its own blocker is "
            "open — a task's terminal status does not resolve its dependencies, and this is "
            "the node that makes the leaf below it free while the chain above it is not"
        )

        for label, task_id in shapes.items():
            task = await ledger.get_task(task_id)
            assert task.status == STATUS_OPEN and task.owner is None, (
                f"{label} ({task_id}) is {task.status!r}/owner={task.owner!r}, not open and "
                f"unowned. The claim CAS guards status/owner/superseded as well as blockers, "
                f"so sweeping such a task compares 'unblocked' against 'claimable' and "
                f"reports a divergence that is not one — see this pin's docstring"
            )

        disagreements: list[str] = []
        for label, task_id in shapes.items():
            claim = await ledger.claim_task(task_id, f"claimer-{uuid.uuid4().hex[:8]}")
            if claim.claimed != partition_says[label]:
                disagreements.append(
                    f"{label} ({task_id}): query_tasks(blocked=False) said "
                    f"{partition_says[label]}, the claim CAS said {claim.claimed}"
                )
        assert disagreements == [], (
            "over a FOUR-DEEP BRANCHING dag the query partition and the atomic claim's "
            "server-side array::len CAS disagree. Both ask a strictly ONE-HOP question; a "
            "resolver that walks the blocks edge transitively (over-blocks) or with the bare "
            "@.{1..n} form (under-blocks, terminal depth only) diverges here and nowhere in "
            f"SECTION I, whose fixtures are one hop deep. Diverging shapes: {disagreements}"
        )
        assert partition_says["L2 leaf free"] and not partition_says["L2 leaf stuck"], (
            "the two sibling leaves landed on the SAME side of the partition, so the "
            "agreement above holds for a fixture reason — a build answering one constant "
            f"would pass it. partition: {partition_says}"
        )
        assert not partition_says["L3 deep"] and not partition_says["L2 leaf diamond"], (
            "the depth-4 node and the diamond node were both served as free, although each "
            "has a non-terminal direct blocker — the branching half of this fixture is not "
            f"discriminating. partition: {partition_says}"
        )


# =========================================================================== #
# HOLE 3 — every #253 assertion reads ``task.id``, so a narrowed projection is invisible.
# =========================================================================== #


class TestTheServedTaskIsFieldIDENTICALToGetTask:
    """GREEN at ``98d5084`` — a removed-behaviour guard.  Kills measured wrong build **W-4**.

    ⛔ Store reference §2: a column absent from an explicit SELECT projection reads back as
    ``None``, SILENTLY.  ``_row_to_task`` then maps that to ``subject=""``,
    ``provenance={}``, ``summary=None`` — a served :class:`Task` that is structurally valid
    and materially false.  ``created_at`` is the only column that would refuse loudly
    (``_require_aware_utc``), which is exactly why the quiet ones need a pin.

    THE ORACLE IS ``get_task``, not a hand-written field list.  ``get_task`` is a
    single-record ``type::record(...)`` read that #253 verdicted a NON-defect, so it is not
    being rewritten in this packet and it stays a ``SELECT *``; equality against it is a ∀
    over the model's fields that no rename or new column can silently escape.  A pin
    enumerating the fields it cares about is the name-list instrument shape this repo has
    the most receipts against.

    ⚠ The fixture MUST populate every optional column somewhere, or it cannot see a
    narrowed projection: a fixture whose tasks are all fresh and unowned has ``owner``,
    ``claimed_at``, ``updated_at``, ``summary``, ``report_path``, ``superseded_by`` and
    ``blocked_by`` all at their defaults, and a build that dropped all seven would pass.
    The last assertion in the sweep checks that the fixture actually did this.
    """

    @staticmethod
    async def _populate(ledger: TaskLedger) -> None:
        """Mint tasks that between them carry a NON-default value in every option column."""
        done = await ledger.create_task(
            "a task carrying a completion record", DESCRIPTION, created_by=CREATOR
        )
        await _drive_to(ledger, done, STATUS_IN_PROGRESS)
        await ledger.transition(
            done,
            STATUS_DONE,
            actor=ACTOR,
            summary="the completion digest the rollup serves",
            report_path="docs/plans/v2/receipts/2026-07-28-packet04b1/REPORT-example.md",
        )
        blocker = await ledger.create_task("a blocker", DESCRIPTION, created_by=CREATOR)
        await ledger.create_task(
            "a task with a non-empty blocked_by", DESCRIPTION, blocked_by=[blocker], created_by=CREATOR
        )
        held = await ledger.create_task("a task held by an owner", DESCRIPTION, created_by=CREATOR)
        claim = await ledger.claim_task(held, OTHER_ACTOR)
        assert claim.claimed, "the fixture could not claim its owned task"
        superseded = await ledger.create_task(
            "a task about to be superseded", DESCRIPTION, created_by=CREATOR
        )
        await ledger.supersede_task(
            superseded, subject="the successor", description=DESCRIPTION, created_by=CREATOR
        )

    @pytest.mark.parametrize(
        "filters",
        [
            {},
            {"status": STATUS_OPEN},
            {"owner": OTHER_ACTOR},
            {"blocked": False},
            {"blocked": True},
            {"status": STATUS_OPEN, "blocked": False},
        ],
        ids=["no-filter", "status", "owner", "unblocked", "blocked", "status+blocked"],
    )
    async def test_every_served_task_equals_the_single_row_read(
        self,
        task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811 - the imported fixture
        filters: dict[str, Any],
    ) -> None:
        """∀ filter modes, because a rewrite narrows the projection on the paths it touches."""
        ledger, _env, _seed = task_ledger
        await self._populate(ledger)

        served = await ledger.query_tasks(**filters)
        mismatches: list[str] = []
        for task in served:
            oracle = await ledger.get_task(task.id)
            if task.model_dump() != oracle.model_dump():
                differing = {
                    field
                    for field, value in task.model_dump().items()
                    if value != oracle.model_dump()[field]
                }
                mismatches.append(f"{task.id}: fields {sorted(differing)}")
        assert mismatches == [], (
            f"query_tasks({filters}) served tasks that DIFFER from the same rows read one at "
            f"a time by get_task. A column left out of an explicit SELECT projection reads "
            f"back as None SILENTLY (store reference §2) and _row_to_task turns that into "
            f"subject='' / provenance={{}} / summary=None — a structurally valid, materially "
            f"false Task. ⚠ Every #253 assertion in SECTION I reads task.id only, so this is "
            f"invisible there. Mismatched: {mismatches}"
        )

    async def test_the_FIXTURE_itself_populates_every_optional_column(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811 - the imported fixture
    ) -> None:
        """⛔ The pin above is worthless if every optional column is at its default.

        This is the "what wrong build would still pass this?" answer made mechanical: with
        an all-defaults fixture, a build that dropped ``owner``, ``claimed_at``,
        ``updated_at``, ``summary``, ``report_path``, ``superseded_by`` and ``blocked_by``
        from its projection would compare equal on every one of them. Derived from the
        MODEL's optional fields, never from a hand-list, so a new column joins this check
        the day it is added.
        """
        ledger, _env, _seed = task_ledger
        await self._populate(ledger)
        served = await ledger.query_tasks()

        defaults = {
            name: field.get_default(call_default_factory=True)
            for name, field in Task.model_fields.items()
            if not field.is_required()
        }
        assert defaults, "Task has no optional fields — this guard is derived from the wrong thing"
        never_populated = {
            name
            for name, default in defaults.items()
            if all(getattr(task, name) == default for task in served)
        }
        assert never_populated == set(), (
            f"these optional Task columns are at their default on EVERY task the fixture "
            f"serves, so the field-identity pin above cannot see a projection that drops "
            f"them: {sorted(never_populated)}. Extend _populate — do NOT relax the pin"
        )


# =========================================================================== #
# HOLE 4 — the filters are about to become query TEXT, and nothing pins what happens
# to a caller's VALUE on the way there.
# =========================================================================== #


class TestAFilterVALUEIsNeverInterpolatedIntoQueryText:
    """GREEN at ``98d5084`` — a removed-behaviour guard.  Kills measured wrong build **W-5**.

    Today ``status``/``owner`` are compared in a Python loop, so a caller's value cannot
    reach query text at all.  This fix's entire shape is *"put the caller's value into the
    statement"*, and an f-string is the shortest way to do it — which is why #219's AST
    sweep of all 187 production files found ZERO identities interpolated into query text
    and why that property is worth a behavioural pin at the one seam about to acquire the
    hazard.  ``owner`` is unconstrained free text (``claim_task`` takes any string), so
    these are values production can genuinely hold, not laboratory strings.

    A DISCRIMINATING PAIR, because "the query did not explode" proves nothing on its own:
    a hostile value that IS an owner must match exactly its own task, and a hostile value
    that is NOBODY's owner must match nothing while the ledger is demonstrably non-empty.
    An interpolating build fails one leg or the other — a parse error on the first, or a
    predicate the engine reads as always-true on the second.
    """

    @pytest.mark.parametrize("hostile", HOSTILE_FILTER_VALUES)
    async def test_a_hostile_OWNER_value_matches_EXACTLY_its_own_task(
        self,
        task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811 - the imported fixture
        hostile: str,
    ) -> None:
        ledger, _env, _seed = task_ledger
        mine = await ledger.create_task("held by a hostile identity", DESCRIPTION, created_by=CREATOR)
        theirs = await ledger.create_task("held by an ordinary identity", DESCRIPTION, created_by=CREATOR)
        assert (await ledger.claim_task(mine, hostile)).claimed
        assert (await ledger.claim_task(theirs, ACTOR)).claimed

        assert await _ids(ledger, owner=hostile) == {mine}, (
            f"query_tasks(owner={hostile!r}) did not serve exactly the one task that "
            f"identity holds. An owner is unconstrained free text; if this filter is being "
            f"pushed into the store it must travel as a BOUND PARAMETER, never interpolated "
            f"into the statement (#219: zero identities are interpolated into query text "
            f"anywhere in the package today)"
        )

    @pytest.mark.parametrize("field", ["owner", "status"])
    async def test_a_hostile_value_matching_NOTHING_serves_an_EMPTY_list(
        self,
        task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811 - the imported fixture
        field: str,
    ) -> None:
        """The negative leg — and the one an injected always-true predicate fails loudly."""
        ledger, _env, _seed = task_ledger
        for index in range(3):
            await ledger.create_task(f"ordinary backlog item {index}", DESCRIPTION, created_by=CREATOR)
        population = await _ids(ledger)
        assert len(population) >= 3, (
            "the ledger is too small for this pin to distinguish 'matched nothing' from "
            "'there was nothing to match'"
        )

        injection = "' OR 1 = 1 --"
        assert await _ids(ledger, **{field: injection}) == set(), (
            f"query_tasks({field}={injection!r}) served tasks. Nothing has that "
            f"{field}, so a non-empty answer means the value was spliced into the statement "
            f"and the engine evaluated it as a predicate rather than comparing it as data. "
            f"The ledger holds {len(population)} tasks"
        )


# =========================================================================== #
# HOLE 5 — no pin anywhere supplies ``status`` AND ``owner`` together.
# =========================================================================== #


class TestTheFiltersAreANDedNotORed:
    """GREEN at ``98d5084`` — a removed-behaviour guard.  Kills measured wrong build **W-6**.

    ``query_tasks``' first contract sentence is *"the tasks matching every supplied filter,
    **AND-combined**"*.  Re-derived 2026-07-28 over the whole test tree: ``test_task_ledger``
    pins ``status`` alone and ``owner`` alone; SECTION I pins ``status``+``blocked`` and
    ``owner``+``blocked``.  **The ``status``∧``owner`` conjunction is pinned nowhere**, and
    it is the one a WHERE-clause rewrite can get wrong in two ordinary ways: joining the
    predicates with ``OR``, or applying whichever filter it checked first and dropping the
    rest.  Each decoy below is excluded by EXACTLY ONE conjunct, so a build that honours
    only some of them names itself in the diff.
    """

    async def test_status_AND_owner_together_are_a_CONJUNCTION(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811 - the imported fixture
    ) -> None:
        ledger, _env, _seed = task_ledger
        wanted = await ledger.create_task("claimed by ACTOR", DESCRIPTION, created_by=CREATOR)
        await _drive_to(ledger, wanted, STATUS_CLAIMED)
        other_owner = await ledger.create_task("claimed by someone else", DESCRIPTION, created_by=CREATOR)
        assert (await ledger.claim_task(other_owner, OTHER_ACTOR)).claimed
        other_status = await ledger.create_task("ACTOR took it further", DESCRIPTION, created_by=CREATOR)
        await _drive_to(ledger, other_status, STATUS_IN_PROGRESS)

        served = await _ids(ledger, status=STATUS_CLAIMED, owner=ACTOR)
        assert served == {wanted}, (
            f"query_tasks(status='claimed', owner={ACTOR!r}) served {served}, expected "
            f"exactly {{{wanted!r}}}. The filters are AND-combined: {other_owner!r} matches "
            f"the status only and {other_status!r} matches the owner only, so an OR-joined "
            f"WHERE serves all three and a first-filter-only build serves two. ⚠ No other pin "
            f"in this tree supplies status AND owner together"
        )

    async def test_status_AND_owner_AND_blocked_together_are_a_CONJUNCTION(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811 - the imported fixture
    ) -> None:
        """The three-way conjunction, with a decoy excluded by the ``blocked`` conjunct alone.

        The blocked decoy is RAW-SEEDED: a ``claimed`` task that is ALSO dependency-blocked
        is unreachable through the ledger (the claim CAS refuses a blocked task, and a
        terminal blocker can never regress), but it is exactly what a row written under the
        pre-04b-1 fail-open ``blocked_by`` looks like after a claim — see
        ``test_blocks_edge._seed_legacy_task``.
        """
        ledger, env, _seed = task_ledger
        wanted = await ledger.create_task("claimed by ACTOR, unblocked", DESCRIPTION, created_by=CREATOR)
        await _drive_to(ledger, wanted, STATUS_CLAIMED)

        # ⚠ THIS DECOY WAS ADDED AFTER A MEASUREMENT, and the reason is the point. Without
        # it, an OR-joined WHERE served {wanted, blocked_decoy} and the `blocked` conjunct
        # then removed the decoy — so the pin passed a build it was written to kill, for a
        # FIXTURE-ARITHMETIC reason. An owner-mismatched but UNBLOCKED task is the row an OR
        # admits and no later conjunct removes.
        or_decoy = await ledger.create_task(
            "claimed by someone else, unblocked", DESCRIPTION, created_by=CREATOR
        )
        assert (await ledger.claim_task(or_decoy, OTHER_ACTOR)).claimed

        blocked_decoy = f"legacy_claimed_{uuid.uuid4().hex}"
        setup = await connect_admin(env)
        try:
            await _seed_legacy_task(
                setup, blocked_decoy, blocked_by=["never-minted-blocker"], status=STATUS_CLAIMED
            )
            await run(
                setup,
                f"UPDATE type::record('{TASK_TABLE}', $id) SET owner = $owner",
                {"id": blocked_decoy, "owner": ACTOR},
            )
        finally:
            await setup.close()

        assert blocked_decoy in await _ids(ledger, status=STATUS_CLAIMED, owner=ACTOR), (
            "the raw-seeded decoy is not visible to the two-way filter, so the three-way "
            "assertion below could pass for a reason that has nothing to do with `blocked`"
        )
        served = await _ids(ledger, status=STATUS_CLAIMED, owner=ACTOR, blocked=False)
        assert served == {wanted}, (
            f"query_tasks(status='claimed', owner={ACTOR!r}, blocked=False) served {served}, "
            f"expected exactly {{{wanted!r}}}. Each decoy is excluded by exactly ONE "
            f"conjunct: {blocked_decoy!r} by `blocked` alone, {or_decoy!r} by `owner` alone "
            f"while remaining unblocked — so an OR-joined WHERE serves {or_decoy!r} and no "
            f"later filter removes it, and a build that stops AND-ing after two filters "
            f"serves {blocked_decoy!r}"
        )


# =========================================================================== #
# HOLE 7 — the tool-level ``limit`` (operator ruling **R5**, 2026-07-28).
# =========================================================================== #


def _tool_seam(ledger: TaskLedger) -> Any:
    """``AppContext``'s ``lore_tasks`` dispatcher, wired to a REAL ledger and nothing else.

    Deliberately the SAME construction ``test_blocks_edge._tool_seam`` uses, and NOT an
    import of it: escalation E-C closed the instrument-in-a-sibling-test-module smell for
    the MEASUREMENT, and re-opening it for a three-line fixture would trade one wrong
    address for another.  It carries no policy — see that function's docstring for the
    ``__new__``-without-``__init__`` rationale and its stated bound.
    """
    from loremaster.server import AppContext

    context = AppContext.__new__(AppContext)
    context.task_ledger = ledger
    return context


class TestTheLimitIsPUSHEDINTOTheStatement:
    """RED since 2026-07-28.  ⛔ **Operator ruling R5** — *"a bounded ``query_tasks`` that
    still materialises every matching row before the dispatcher slices is a HALF-FIX THAT
    READS AS A FIX — the trust hazard, not merely an inefficiency."*

    ⚠⚠ **THE ESCALATION THAT PRODUCED R5 DESCRIBED A BEHAVIOUR THAT DOES NOT EXIST, AND THE
    BUILDER NEEDS THE CORRECTION MORE THAN THE RULING.**  E-D (raised by both #253 authors)
    says the dispatcher *"slices AFTER materialisation"*.  RE-DERIVED at ``faf035d``,
    through the real handler: it does not slice at all — ``AppContext.tasks`` REJECTS
    ``limit`` for every non-rollup action, ``ValueError: 'since'/'limit' apply only to
    action='rollup' — omit them for 'query'``.  So R5 is not a re-ordering of an existing
    cap; it makes ``limit`` a NEWLY ACCEPTED parameter of ``action='query'``.
    ✅ **The committed pins in ``test_mcp_server.py`` that asserted today's rejection have
    been RE-AUTHORED in place (wave r5, 2026-07-28)** — they now pin only what survives R9,
    are green before the fix and after, and each says so in its own docstring. So does
    ``_task_fakes.FakeTaskLedger.query_tasks``, which gained the ``limit`` this ruling makes
    the dispatcher pass. **A builder meets no red test outside this contract.**

    THE PROPERTY, stated over the outcome: a caller asking for N rows causes the ENGINE to
    hand back a number of rows bounded by N, not by the ledger.  A post-materialisation
    slice serves the same ANSWER, which is why an answer-only pin cannot see it and why the
    instrument here is :func:`~_surreal_harness.measure_store_traffic`.
    """

    @staticmethod
    async def _measure_limited(matching_count: int) -> tuple[StoreTraffic, int]:
        """Traffic and answer size for ``query_tasks(status=…, limit=_LIMIT)``.

        Every seeded task MATCHES the filter — that is the difference from
        :class:`TestTheBLOCKEDPathIsBoundedToo`, whose noise is deliberately excluded.  Here
        the WHERE is satisfied by all of them, so only the ``LIMIT`` can keep the read small
        and a build that pushes the filter but not the cap is measurably distinct.
        """
        ledger, env = await _fresh_ledger()
        try:
            ids = await _seed_unrelated_tasks(ledger, matching_count)
            for task_id in ids:
                await ledger.transition(task_id, STATUS_WONTFIX, actor=ACTOR)
            served: set[str] = set()
            traffic = await measure_store_traffic(
                ledger,
                lambda: _collect(ledger, served, status=STATUS_WONTFIX, limit=_SERVED_LIMIT),
            )
            return traffic, len(served)
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_query_tasks_ACCEPTS_a_limit_and_SERVES_at_most_that_many(self) -> None:
        """The surface half: the parameter exists, and the answer obeys it.

        ⚠ Routed through :func:`_ids` (``**filters``) rather than calling
        ``ledger.query_tasks(limit=…)`` directly, for the reason
        ``test_blocks_edge._transitive_blockers`` exists: ``limit`` does not exist on the
        signature YET, and a directly-typed call is a MYPY ERROR today rather than a RED
        pin — which would make this contract fail its own gate before a builder saw it.
        A build that spells the parameter differently gets a ``TypeError`` here, naming it.
        """
        ledger, env = await _fresh_ledger()
        try:
            await _seed_unrelated_tasks(ledger, UNRELATED_TASK_COUNT_SMALL)
            served = await _ids(ledger, limit=_SERVED_LIMIT)
            assert len(served) == _SERVED_LIMIT, (
                f"query_tasks(limit={_SERVED_LIMIT}) served {len(served)} of "
                f"{UNRELATED_TASK_COUNT_SMALL} tasks. R5: the ledger takes the limit — the "
                f"dispatcher must have somewhere to pass it to"
            )
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_the_LIMIT_bounds_the_ROWS_READ_not_just_the_ROWS_SERVED(self) -> None:
        """⛔ The half a post-materialisation slice passes and R5 exists to close.

        A GROWTH comparison, never a threshold: the same capped question is asked of a
        ledger where 5 rows match and one where 60 do.  The ANSWER is ``_SERVED_LIMIT`` at
        both sizes by construction, so any growth in ROWS READ is the ledger's size leaking
        into a read the caller explicitly bounded.
        """
        small, small_answer = await self._measure_limited(UNRELATED_TASK_COUNT_SMALL)
        large, large_answer = await self._measure_limited(UNRELATED_TASK_COUNT_LARGE)
        assert small_answer == large_answer == _SERVED_LIMIT, (
            f"the two measurements served {small_answer} and {large_answer} tasks; each must "
            f"serve exactly {_SERVED_LIMIT}. Either the fixture drifted — a rows-read "
            f"comparison between different answers measures nothing — or the cap is not "
            f"being applied at all"
        )
        assert small.rows > 0, (
            f"the instrument saw no rows for a query that served {small_answer} tasks: {small}"
        )
        assert large.rows == small.rows, (
            f"a capped query_tasks read {small.rows} rows where "
            f"{UNRELATED_TASK_COUNT_SMALL} rows matched and {large.rows} where "
            f"{UNRELATED_TASK_COUNT_LARGE} did, for the SAME {_SERVED_LIMIT}-row answer. The "
            f"cap is being applied AFTER materialisation — a half-fix that reads as a fix "
            f"(R5). Push the limit into the STATEMENT. "
            f"small={small.statements} large={large.statements}"
        )

    async def test_the_TOOL_SEAM_passes_the_limit_through_to_the_ledger(self) -> None:
        """⛔ **R5's second clause — *"the dispatcher passes it"* — observed where a caller
        stands.**

        Every other pin in this file calls the ledger directly and would be satisfied by a
        ledger that accepts ``limit`` while the dispatcher still refuses it, which is
        exactly today's state and exactly the half-fix R5 names.
        """
        ledger, env = await _fresh_ledger()
        try:
            await _seed_unrelated_tasks(ledger, UNRELATED_TASK_COUNT_SMALL)
            rendered = await _tool_seam(ledger).tasks(action="query", limit=_SERVED_LIMIT)
            lines = [line for line in str(rendered).splitlines() if line.startswith("- ")]
            assert len(lines) == _SERVED_LIMIT, (
                f"lore_tasks action=query limit={_SERVED_LIMIT} rendered {len(lines)} task "
                f"rows out of {UNRELATED_TASK_COUNT_SMALL}. ⚠ At faf035d this call RAISES "
                f"ValueError ('since'/'limit' apply only to action='rollup'), so the builder "
                f"must relax that guard — R9 splits it, it is not deleted. The pins in "
                f"test_mcp_server.py that asserted the old rejection were re-authored in "
                f"wave r5 and need no builder edit. rendered={rendered!r}"
            )
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_POSITIVE_CONTROL_an_UNLIMITED_query_still_serves_EVERYTHING(self) -> None:
        """The control every cap pin needs: a build that served ``_SERVED_LIMIT`` rows
        unconditionally — or one that truncated every read — would pass all three legs above.

        ⚠ **AND IT NOW HAS A NAMED, MEASURED WRONG BUILD, which it did not when it was
        written.**  Probed 2026-07-28 against spike-surreal 3.2.1 (``ws://127.0.0.1:18000``,
        the TEST store; ``docs/reference/surrealdb-31-capabilities.md`` documents no ``LIMIT``
        behaviour, which is why this was measured rather than looked up)::

            SELECT * FROM t LIMIT $k, $k = NONE  ->  0 rows, NO ERROR

        So the most natural build of ruling R5 — always emit ``LIMIT $limit`` and bind
        ``None`` when the caller supplied no cap — turns **every unlimited query in the fleet
        into an empty answer**, silently, with no error anywhere and no round-trip cost to
        hint at it.  This leg is the only thing in either contract file that catches it.
        """
        ledger, env = await _fresh_ledger()
        try:
            await _seed_unrelated_tasks(ledger, UNRELATED_TASK_COUNT_LARGE)
            served = await ledger.query_tasks()
            assert len(served) == UNRELATED_TASK_COUNT_LARGE, (
                f"an UNLIMITED query_tasks served {len(served)} of "
                f"{UNRELATED_TASK_COUNT_LARGE} tasks. A cap that applies when the caller did "
                f"not ask for one is a silently truncated served answer — the trust-doctrine "
                f"defect, in the fix for a trust-doctrine defect"
            )
        finally:
            await ledger.close()
            await drop_database(env)


#: The cap ruling **T1**'s pins ask for.  Bigger than :data:`_SERVED_LIMIT` on purpose: the
#: discrimination below is combinatorial in this value (see
#: :class:`TestTheCapAppliesToTheANSWERNotTheCandidateScan`), and 5 buys three more orders of
#: magnitude than 3 for four extra fixture rows.
_ANSWER_CAP = 5

#: BLOCKED rows seeded BEFORE and AFTER the unblocked ones, so the unblocked population is a
#: SANDWICH FILLING rather than a prefix or a suffix.  That is what makes the discrimination
#: below deterministic under insertion order and reverse-insertion order instead of merely
#: improbable — see the class docstring's three-ordering analysis.
_BLOCKED_NOISE_EACH_SIDE = 30


class TestTheCapAppliesToTheANSWERNotTheCandidateScan:
    """RED since 2026-07-28.  ⛔ **Ruling T1 — NO SILENT SHORT ANSWERS.**

    T1, verbatim: *"A ``LIMIT`` pushed into the statement cuts rows BEFORE the client-side
    ``blocked`` filter, so ``query_tasks(status=…, blocked=False, limit=5)`` can serve FEWER
    than 5 while more exist, with no signal. … RULED: the cap applies to the ANSWER, not the
    candidate scan; and where the scan is exhausted before the cap fills, it SAYS SO."*
    ``DESIGN-LAW`` §1.4 names silent truncation the cardinal failure class.

    ⚠ **THIS IS THE ONE PLACE WHERE R5 AND #253 PULL IN OPPOSITE DIRECTIONS, and a builder
    who satisfies either alone ships the other's defect.**  R5 says push the cap into the
    statement; #253 says the ``blocked`` partition is decided client-side over the candidate
    set.  Compose them naively — ``… WHERE status = $s LIMIT 5`` and then drop the blocked
    ones — and the caller asked for five claimable tasks, got two, and is told nothing.  It
    will conclude the backlog is nearly empty.  *That is not a slow query; it is a false
    answer about the fleet's own work queue.*

    **THE FIXTURE IS A SANDWICH, and the reason is that ``LIMIT`` without ``ORDER BY``
    returns rows in an order this contract must not assume.**  ``_BLOCKED_NOISE_EACH_SIDE``
    blocked rows are seeded, then ``_ANSWER_CAP`` unblocked ones, then that many blocked rows
    again — so the unblocked population is neither a prefix nor a suffix of insertion order.
    Three candidate orderings, all three adjudicated rather than hoped at:

    * **insertion order** — the first ``_ANSWER_CAP`` rows are the root blocker plus blocked
      noise, so a candidate-cap build serves ONE. Deterministic RED.
    * **reverse insertion order** — the first ``_ANSWER_CAP`` rows are all blocked noise, so
      it serves ZERO. Deterministic RED.
    * **record-id order** (uuid4 hex, i.e. effectively a fresh random permutation each run) —
      a candidate-cap build passes only if its whole window happens to be unblocked:
      ``C(6, 5) / C(66, 5)`` = 6 / 8,936,928 ≈ **7e-7** per run.

    **STATED BOUND, because a fixture that a wrong build passes one run in a million is still
    a fixture a wrong build can pass:** the third case is a probability, not a proof. It is
    stated here rather than left for an auditor to find, and it is why the cap is 5 and not
    3 — the same fixture at ``_SERVED_LIMIT`` would be ≈1e-4, which is a flake rate, not a
    negligible one.
    """

    @staticmethod
    async def _sandwich_ledger() -> tuple[TaskLedger, SurrealEnv, str, int]:
        """A ledger holding blocked noise / unblocked filling / blocked noise, all ``open``.

        Returns the ledger, its env, the root blocker's id, and the TRUE size of the
        unblocked-and-matching population — which every leg asserts against rather than
        recomputing, because a fixture that silently produced a different population would
        turn a discrimination into a tautology.
        """
        from loremaster.tasks import TaskSpec

        ledger, env = await _fresh_ledger()
        root = await ledger.create_task(
            "the root blocker, which is itself unblocked", DESCRIPTION, created_by=CREATOR
        )

        async def _blocked_noise(tag: str) -> None:
            await ledger.create_many(
                [
                    TaskSpec(
                        subject=f"blocked backlog item {tag}-{index}",
                        description=DESCRIPTION,
                        blocked_by=[root],
                    )
                    for index in range(_BLOCKED_NOISE_EACH_SIDE)
                ],
                created_by=CREATOR,
            )

        await _blocked_noise("before")
        await ledger.create_many(
            [
                TaskSpec(subject=f"claimable backlog item {index}", description=DESCRIPTION)
                for index in range(_ANSWER_CAP)
            ],
            created_by=CREATOR,
        )
        await _blocked_noise("after")
        return ledger, env, root, _ANSWER_CAP + 1  # + the root, which is unblocked too

    async def test_a_capped_BLOCKED_query_serves_the_FULL_cap_when_the_answer_is_bigger(
        self,
    ) -> None:
        """⛔ **The pin R-20 flagged and deliberately left unwritten.**

        ``status`` AND ``blocked`` AND ``limit``, together, for the first time anywhere in
        either contract file — which is why the hazard survived a contract, an adversary pass
        and a fix wave: no pin combined the two parameters that interact.
        """
        ledger, env, root, true_answer_size = await self._sandwich_ledger()
        try:
            unlimited = await _ids(ledger, status=STATUS_OPEN, blocked=False)
            assert len(unlimited) == true_answer_size, (
                f"the fixture served {len(unlimited)} unblocked open tasks where it built "
                f"{true_answer_size}; the sandwich did not come out as intended, so nothing "
                f"below discriminates anything. root={root!r}"
            )
            capped = await _ids(ledger, status=STATUS_OPEN, blocked=False, limit=_ANSWER_CAP)
            assert len(capped) == _ANSWER_CAP, (
                f"query_tasks(status=open, blocked=False, limit={_ANSWER_CAP}) served "
                f"{len(capped)} tasks while {len(unlimited)} genuinely qualify. The cap was "
                f"applied to the CANDIDATE SCAN, so rows the `blocked` filter then dropped "
                f"were spent out of the caller's budget — and the caller is told nothing, so "
                f"it concludes the backlog holds {len(capped)} claimable items when it holds "
                f"{len(unlimited)} (ruling T1). The cap belongs on the ANSWER: keep drawing "
                f"candidates until the cap fills or the scan is exhausted"
            )
            assert capped <= unlimited, (
                f"the capped answer is not a SUBSET of the uncapped one — it served "
                f"{sorted(capped - unlimited)}, which the same query without a cap does not. "
                f"A cap must window an answer, never change it"
            )
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_a_SHORT_answer_means_the_scan_was_EXHAUSTED_never_silently_truncated(
        self,
    ) -> None:
        """⛔ **T1's second clause, at the layer this packet owns.**

        *"Where the scan is exhausted before the cap fills, it SAYS SO."*  A ``list[Task]``
        has nowhere to carry a flag, so the ledger-level form of that promise is the property
        the flag would ATTEST: **a short answer is a TRUE short answer.**  If the ledger
        serves fewer rows than the caller's cap, then there genuinely are no more — asking
        the identical question with no cap at all returns exactly the same number.

        A candidate-cap build fails this for a cap of ``2 × _BLOCKED_NOISE_EACH_SIDE`` even
        though that cap is far larger than the answer: it spends its window on blocked rows,
        serves short, and its shortness is a lie about the ledger rather than a fact about it.

        ⚠ The RENDERED half of T1 — the counted-elision line R9 rules for the no-limit
        display cap (``+K more — re-run with limit=N``) — is 04b-2's surface and is NOT
        pinned here.  This is the ledger half, and it is the half that has to be TRUE before
        any render of it can be honest.
        """
        generous_cap = 2 * _BLOCKED_NOISE_EACH_SIDE
        ledger, env, root, true_answer_size = await self._sandwich_ledger()
        try:
            assert generous_cap > true_answer_size, (
                f"this pin needs a cap the answer cannot fill ({generous_cap} vs "
                f"{true_answer_size}); the fixture constants have drifted apart"
            )
            capped = await _ids(ledger, status=STATUS_OPEN, blocked=False, limit=generous_cap)
            unlimited = await _ids(ledger, status=STATUS_OPEN, blocked=False)
            assert len(capped) < generous_cap, (
                f"the fixture filled a cap of {generous_cap} with {len(capped)} rows, so this "
                f"measurement never reaches the short-answer case it exists to test. "
                f"root={root!r}"
            )
            assert capped == unlimited, (
                f"a capped query served {len(capped)} tasks and the SAME query with no cap "
                f"served {len(unlimited)} — so the short answer was not the scan running out, "
                f"it was rows being thrown away inside the cap. That is a silent truncation "
                f"of a served answer (ruling T1, DESIGN-LAW §1.4's cardinal class): the caller "
                f"cannot distinguish 'that is all there is' from 'that is all I looked at'. "
                f"missing={sorted(unlimited - capped)}"
            )
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_POSITIVE_CONTROL_the_SANDWICH_really_holds_blocked_rows_the_WHERE_cannot_see(
        self,
    ) -> None:
        """The control both legs above need, and it is not decoration.

        Their discrimination rests entirely on the noise rows being (a) genuinely BLOCKED and
        (b) INDISTINGUISHABLE from the answer to the ``status`` filter — if the noise were a
        different status, the store-side ``WHERE`` would exclude it and a candidate-cap build
        would pass both legs while the defect stayed wide open.  So both halves are asserted
        directly, at the same ledger, in the same shape the legs use.
        """
        ledger, env, root, true_answer_size = await self._sandwich_ledger()
        try:
            every_open = await _ids(ledger, status=STATUS_OPEN)
            blocked_only = await _ids(ledger, status=STATUS_OPEN, blocked=True)
            expected_noise = 2 * _BLOCKED_NOISE_EACH_SIDE
            assert len(blocked_only) == expected_noise, (
                f"{len(blocked_only)} rows are blocked where the fixture seeded "
                f"{expected_noise}; the noise is not blocked, so it would never be dropped "
                f"by the client-side filter and the legs above discriminate nothing. "
                f"root={root!r}"
            )
            assert len(every_open) == expected_noise + true_answer_size, (
                f"the `status=open` candidate set holds {len(every_open)} rows, not the "
                f"{expected_noise + true_answer_size} the fixture built — so the noise is NOT "
                f"indistinguishable from the answer to the store-side WHERE, and a "
                f"candidate-cap build would never spend its window on it"
            )
        finally:
            await ledger.close()
            await drop_database(env)


class TestLimitIsLEGALForQueryAtTheToolSeam:
    """RED since 2026-07-28.  ⛔ **Operator ruling R9's 04b-1 half** — *"``limit`` becomes
    legal for ``query``"*.

    ⚠ **R9 STATES A CONSEQUENCE NO EARLIER RULING DID, and it is a SERVED-SCHEMA change.**
    R5 ruled that the tool-level ``limit`` pushes down; re-derived at ``5a2dca9``, through the
    real handler, ``limit`` is not merely applied late — it is **REFUSED**::

        tasks(action='query', limit=5)
        -> ValueError: 'since'/'limit' apply only to action='rollup' — omit them for 'query'

    So R5 is not a re-ordering of an existing cap, and the sidecar measured the cost of the
    gap it leaves: with no cap available, an unfiltered ``query`` served it *the entire
    ~110-row ledger*.

    **THE POINT OF THIS CLASS IS THAT THE WIDENING IS SURGICAL.**  The single existing seam
    pin (``TestTheLimitIsPUSHEDINTOTheStatement::test_the_TOOL_SEAM_passes_the_limit_through_to_the_ledger``)
    observes that ``limit`` now WORKS on ``query`` — and is equally satisfied by a builder who
    deleted the strict-parameter guard outright, which would silently accept ``since`` on
    ``create`` and ``limit`` on ``transition`` and quietly retire a real teaching surface.
    R9 widened one parameter for one action; the three legs below say exactly that.

    ✅ ``test_mcp_server.py``'s pins on the OLD rejection were RE-AUTHORED in wave r5
    (2026-07-28) rather than left as escalation ESC-1's "exact edits the builder must make":
    a contract that hands a builder a list of red tests in a file it may not edit has moved
    the defect, not removed it. They now assert only what survives R9 — that ``since`` on
    ``query`` is still refused and names the parameter, and that ``limit`` on ``create`` is
    still refused and names both — which are exactly the assertions the two legs below make
    of a REAL ledger. **Green before the fix and after.**
    """

    #: The retired claim, BY VALUE.  A failure message that promises a check the code no
    #: longer performs is a FALSE GATE (P2, 2026-07-14), and this one would tell an agent to
    #: omit a parameter that is now the documented way to bound its own answer.
    RETIRED_CLAIM = "'since'/'limit' apply only to action='rollup'"

    # ⚠ THERE IS NO "limit ON query IS ACCEPTED" LEG HERE, AND ITS ABSENCE IS A MEASURED
    # DECISION.  This class shipped with one; a mutation proof that DELETED the strict
    # parameter guard outright left it **GREEN** while the two legs below reddened — so it
    # discriminated nothing that its siblings do not, and its presence was false comfort of
    # exactly the kind this contract polices ("what WRONG build would still pass this?").
    # R9's positive direction is pinned END TO END, one class away, by
    # ``TestTheLimitIsPUSHEDINTOTheStatement::test_the_TOOL_SEAM_passes_the_limit_through_to_the_ledger``,
    # which drives the same dispatcher and asserts the RENDERED ROW COUNT equals the cap — a
    # build whose guard still refuses `limit` on `query` cannot reach that assertion at all.
    # Duplicating it here would have been copy #2 of a served-surface pin (repo law #102).

    async def test_SINCE_on_action_QUERY_is_STILL_REFUSED_and_stops_claiming_limit_is_too(
        self,
    ) -> None:
        """⛔ The leg a builder who deleted the guard fails, and the one that keeps the
        served sentence honest.

        Two assertions, two different wrong builds: the guard vanishing entirely (no raise),
        and the guard surviving with its OLD sentence (a refusal that teaches an agent to
        drop the very parameter R9 just made legal). The second is the subtler and is exactly
        the class ``CLAUDE.md`` calls *natural-language surfaces whose consistency with code
        no gate checks*.
        """
        ledger, env = await _fresh_ledger()
        try:
            with pytest.raises(ValueError) as caught:  # noqa: PT011 - the TEXT is the assertion
                await _tool_seam(ledger).tasks(action="query", since="2026-07-01T00:00:00Z")
            message = str(caught.value)
            assert "since" in message, (
                f"the refusal does not name the parameter it rejected: {message!r}"
            )
            assert self.RETIRED_CLAIM not in message, (
                f"the strict-parameter refusal still tells a caller that 'since'/'limit' "
                f"apply only to action='rollup'. Under ruling R9 that is FALSE for 'limit' on "
                f"'query', and the reader is an agent learning this tool's contract from the "
                f"sentence — it will omit the parameter that is now the documented way to "
                f"bound its own answer. Split the guard; do not widen the behaviour and leave "
                f"the prose: {message!r}"
            )
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_limit_on_a_NON_query_NON_rollup_action_is_STILL_REFUSED(self) -> None:
        """⛔ The leg that makes the widening SURGICAL rather than a deletion.

        ``create`` is chosen because the strict-parameter guard runs BEFORE the
        required-argument checks, so this observes the guard itself and not a missing
        ``subject``. R9 widened ONE parameter to ONE action.
        """
        ledger, env = await _fresh_ledger()
        try:
            with pytest.raises(ValueError) as caught:  # noqa: PT011 - the TEXT is the assertion
                await _tool_seam(ledger).tasks(action="create", limit=_SERVED_LIMIT)
            message = str(caught.value)
            assert "limit" in message and "create" in message, (
                f"a 'limit' on action='create' was refused without naming the parameter and "
                f"the action, so a caller cannot tell which of the two to change: {message!r}"
            )
        finally:
            await ledger.close()
            await drop_database(env)


class TestTheTwoReadsShareONESnapshot:
    """RED since 2026-07-28.  ⛔ **Operator ruling R7** — *"the TOCTOU is CLOSED BY
    CONSTRUCTION, not measured and accepted."*

    Any bounded rewrite is a TWO-read operation (candidates, then their blockers), and a
    writer committing between them can make the served ``blocked`` partition disagree with
    the claim CAS **without either read being wrong** — a window today's single full read
    does not have, i.e. a hazard this fix INTRODUCES.  R7 rejects both the
    named-hazard-only posture (*"accepts a correctness window on a SERVED answer on the
    strength of an argument, with no instrument"*) and a characterisation measurement
    (≥8-way × 20 consecutive runs — expensive, and it measures what this removes).

    **THE INSTRUMENT IS ROUND TRIPS, AND THE REASONING IS WHY IT IS NOT A TEXT PIN.**  One
    round trip is one snapshot, whatever its shape: a ``BEGIN … COMMIT`` through
    ``query_raw``, or a single ``SELECT`` whose blocker resolution is a sub-select.  A pin
    demanding the literal token ``BEGIN`` would redden the second build, which is strictly
    stronger than what R7 asks for — a contract must not forbid a better answer than the one
    its author imagined.

    ⚠ **AND IT COMPOSES WITH MP-4a / R7's rider**, which is pinned on the WRITE path in
    ``test_blocks_edge.py``'s
    ``TestCreateRefusesToFormACycle::test_the_cycle_WALK_is_ONE_round_trip_however_DEEP_the_chain``.
    The two must be satisfied together: the cycle guard cannot be moved onto the engine to
    save round trips (the closing dependency of a cycle cannot carry an edge), and the
    bounded read cannot be split into per-blocker reads to keep the guard simple.
    """

    @staticmethod
    async def _traffic_for(blocker_count: int) -> tuple[StoreTraffic, set[str]]:
        """Traffic for ONE ``query_tasks(status=…, blocked=False)`` over N blockers.

        The candidate is a single ``wontfix`` task whose ``blocked_by`` names
        ``blocker_count`` DISTINCT resolved blockers, so the blocker-resolution read has N
        rows to fetch while the candidate read has exactly one — which is the only way to
        tell "one read per blocker" from "one read for all of them".
        """
        ledger, env = await _fresh_ledger()
        try:
            blockers = await _seed_unrelated_tasks(ledger, blocker_count)
            for blocker in blockers:
                await ledger.transition(blocker, STATUS_WONTFIX, actor=ACTOR)
            target = await ledger.create_task(
                "the candidate", DESCRIPTION, blocked_by=blockers, created_by=CREATOR
            )
            served: set[str] = set()
            traffic = await measure_store_traffic(
                ledger,
                lambda: _collect(ledger, served, status=STATUS_OPEN, blocked=False),
            )
            assert target in served, (
                f"the fixture's candidate {target!r} is not in the served answer, so this "
                f"measurement observes nothing about resolving its blockers: {served}"
            )
            return traffic, served
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_the_bounded_read_is_ONE_round_trip_however_MANY_blockers(self) -> None:
        """⛔ The pin that separates "two reads in one transaction" from "N reads in N".

        A GROWTH comparison on ROUND TRIPS: 3 blockers versus 30.  Rows legitimately grow
        with the number of blockers and are deliberately NOT compared here — that would
        forbid the correct build.  ``TestTheBLOCKEDPathIsBoundedToo`` owns the rows question.
        """
        few, _few_served = await self._traffic_for(3)
        many, _many_served = await self._traffic_for(30)
        assert few.calls > 0, (
            f"the instrument saw no traffic for a query that served an answer: {few}"
        )
        assert many.calls == few.calls, (
            f"resolving 3 blockers cost {few.calls} round trips and resolving 30 cost "
            f"{many.calls}. The reads are per-blocker, so they do NOT share a snapshot: a "
            f"writer committing between them makes the served `blocked` partition disagree "
            f"with the claim CAS while neither read is wrong. Ruling R7: both reads go "
            f"inside ONE BEGIN…COMMIT (or one statement), so the window is closed BY "
            f"CONSTRUCTION. few={few.statements} many={many.statements}"
        )

    async def test_the_read_does_NOT_re_enter_the_store_per_CANDIDATE_either(self) -> None:
        """The other axis of the same hazard, and it is a different wrong build.

        A build can batch its blocker reads and still issue one candidate read per served
        row (an N+1 over the ANSWER rather than over the blockers).  Same missing snapshot,
        same growth, different loop — so it needs its own fixture: many candidates, each
        with ONE blocker, instead of one candidate with many blockers.
        """

        async def _many_candidates(count: int) -> StoreTraffic:
            ledger, env = await _fresh_ledger()
            try:
                blocker = await ledger.create_task(
                    "one shared blocker", DESCRIPTION, created_by=CREATOR
                )
                await _drive_to(ledger, blocker, STATUS_DONE)
                from loremaster.tasks import TaskSpec

                await ledger.create_many(
                    [
                        TaskSpec(
                            subject=f"candidate {index}",
                            description=DESCRIPTION,
                            blocked_by=[blocker],
                        )
                        for index in range(count)
                    ],
                    created_by=CREATOR,
                )
                served: set[str] = set()
                traffic = await measure_store_traffic(
                    ledger,
                    lambda: _collect(ledger, served, status=STATUS_OPEN, blocked=False),
                )
                assert len(served) == count, (
                    f"the fixture served {len(served)} of {count} candidates, so the "
                    f"comparison would not be like-for-like"
                )
                return traffic
            finally:
                await ledger.close()
                await drop_database(env)

        few = await _many_candidates(3)
        many = await _many_candidates(30)
        assert few.calls > 0, few
        assert many.calls == few.calls, (
            f"serving 3 candidates cost {few.calls} round trips and serving 30 cost "
            f"{many.calls} — the read re-enters the store per served row. That is an N+1 "
            f"over the ANSWER, and it carries the same open TOCTOU window R7 closes. "
            f"few={few.statements} many={many.statements}"
        )


class TestTheInstrumentsOwnREACHIsACheckedVariable:
    """RED at ``5a2dca9``.  ⛔ **Ruling T4 — instrument reach is a CHECKED VARIABLE, not a
    stated bound.**

    T4, verbatim: *"``measure_store_traffic`` is blind to non-``query_raw`` SDK calls
    (contractfix R-22, disclosed as a docstring bound). This repo's six-defeats lesson says a
    guard is an invariant only over the code it RUNS: enumerate the call sites and ASSERT
    each was observed, so reach cannot silently become the next name-list."*

    ⚠ **WHY THIS MATTERS MORE HERE THAN IN MOST PLACES.**  Nearly every #253 pin is a
    NEGATIVE result — *"the rows read did not grow"* — and a blind instrument produces that
    result perfectly.  ``measure_store_traffic`` counts at ``query_raw``; an SDK call that
    reaches the engine another way (``select`` / ``create`` / ``insert`` / ``upsert`` /
    ``relate``) was counted as **zero**, and zero reads as *"the read did not grow"*.  The
    instrument would have lied in the direction of false confidence, about the exact
    property this whole file exists to establish — and its predecessor had already been
    defeated once the same way (``_rows_read``, keyed on ``TaskLedger._query``, blind to the
    ``query_raw`` door ruling R7 requires).

    **THE FIX IS DENY-BY-DEFAULT, NOT A LONGER LIST.**  Every door the instrument cannot
    count is shadowed and RECORDED, the countable set is two names derived from the SDK's own
    delegation, and :meth:`~_surreal_harness.StoreTraffic.require_full_reach` runs before
    every reading is returned — so a caller cannot forget the check, which is how the last
    runtime gate in this repo went blind (armed in four tests; the offending path was in a
    fifth).
    """

    @staticmethod
    async def _measure_a_real_read(**kwargs: Any) -> tuple[StoreTraffic, TaskLedger, SurrealEnv]:
        """One ordinary ``query_tasks`` measurement, with the ledger left open."""
        ledger, env = await _fresh_ledger()
        await _seed_unrelated_tasks(ledger, UNRELATED_TASK_COUNT_SMALL)
        served: set[str] = set()
        traffic = await measure_store_traffic(
            ledger, lambda: _collect(ledger, served, status=STATUS_OPEN), **kwargs
        )
        assert served, "the measured read served nothing, so it exercised no door at all"
        return traffic, ledger, env

    async def test_a_REAL_measured_read_uses_ONLY_doors_the_instrument_can_COUNT(self) -> None:
        """The ∀ over the flow every other pin in this file measures.

        A door the instrument cannot count is NAMED here rather than absorbed into a small
        number — which is the whole difference between *"the read did not grow"* and
        *"I did not see the read"*.
        """
        traffic, ledger, env = await self._measure_a_real_read()
        try:
            assert traffic.doors, (
                f"the measured read used NO SDK door at all, so this instrument observed "
                f"nothing and every number it reports is vacuous: {traffic}"
            )
            assert traffic.unobserved == (), (
                f"query_tasks reached the engine through {list(traffic.unobserved)}, which "
                f"measure_store_traffic cannot count — so every rows-read and round-trip "
                f"number in this file is an UNDERCOUNT of unknown size (ruling T4)"
            )
            traffic.require_full_reach("query_tasks(status=…)")
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_POSITIVE_CONTROL_an_UNCOUNTABLE_door_is_NAMED_and_the_reading_REFUSED(
        self,
    ) -> None:
        """⛔⛔ **THE CONTROL WITHOUT WHICH THE LEG ABOVE IS DECORATION.**

        ``unobserved == ()`` is a negative result, and a negative result from a detector that
        cannot fire is indistinguishable from one from a working detector.  So: make a real
        SDK call the instrument cannot count, in the middle of a measured window, and require
        it to be (a) NAMED and (b) REFUSED.

        ``version`` is used because it is a genuine server round trip that sends its OWN
        request message rather than a SurrealQL statement — the real shape of this
        instrument's blind spot (see :data:`~_surreal_harness.StoreTraffic.COUNTABLE_DOORS`
        for why the four methods R-22 NAMED as invisible turned out not to be) — and
        because it mutates nothing, so the control cannot damage the fixture it runs in.

        BOTH halves are asserted.  A build that recorded the door but returned the reading
        anyway leaves every caller free to act on a number it has been told is wrong, and
        *"a guard nobody runs is a hope with a filename"*.
        """
        ledger, env = await _fresh_ledger()
        try:
            await _seed_unrelated_tasks(ledger, UNRELATED_TASK_COUNT_SMALL)
            connection = await ledger._ensure_connection()  # noqa: SLF001 - the seam IS the probe
            assert "version" in StoreTraffic.uncountable_doors(), (
                "this control needs a door the instrument genuinely cannot count; `version` "
                "is no longer one, so it would prove nothing"
            )

            async def _reach_the_server_through_an_uncountable_door() -> None:
                await connection.version()

            recorded = await measure_store_traffic(
                ledger, _reach_the_server_through_an_uncountable_door, allow_unobserved=True
            )
            assert any(entry.startswith("version") for entry in recorded.unobserved), (
                f"a live `connection.version()` inside the measured window was NOT recorded "
                f"as an uncountable door, so this instrument is still blind to exactly the "
                f"class of call ruling T4 exists to close: {recorded}"
            )
            assert recorded.calls == 0, (
                f"the instrument COUNTED a `version()` — it counts at `query_raw`, which "
                f"`version` does not pass through, so a non-zero count here means the "
                f"accounting no longer matches the doors: {recorded}"
            )
            with pytest.raises(AssertionError) as refusal:
                recorded.require_full_reach("a deliberately uncountable call")
            assert "version" in str(refusal.value), (
                f"the refusal does not name the door it could not count, so a reader cannot "
                f"tell which call to fix: {str(refusal.value)!r}"
            )
            with pytest.raises(AssertionError):
                await measure_store_traffic(ledger, _reach_the_server_through_an_uncountable_door)
        finally:
            await ledger.close()
            await drop_database(env)

    def test_the_UNCOUNTABLE_door_set_is_DERIVED_from_the_SDK_and_DENIES_BY_DEFAULT(
        self,
    ) -> None:
        """⛔ The property that stops reach becoming the next name-list.

        The set is not asserted to EQUAL a list of methods — that would be the name-list
        again, one level up, and it would need editing on every SDK release.  What is
        asserted is the PARTITION: every public awaitable door on a real SDK connection is
        in exactly one of *countable*, *uncountable*, or ``_sdk_guard``'s evidence-backed
        safe set.  A method the SDK ships next year lands in *uncountable* with nobody
        touching this file — which is the deny-by-default property, stated as a check.

        The named samples are a NON-VACUITY guard on BOTH sides, not the requirement: an
        empty ``uncountable_doors()`` would satisfy the partition trivially and make the
        instrument blind again, and an empty ``COUNTABLE_DOORS`` would make every ordinary
        read look like a blind spot.

        ⚠ **THE COUNTABLE SAMPLES ARE A CORRECTION, PINNED SO IT CANNOT SILENTLY REGRESS.**
        This instrument's docstring used to state as a bound that ``select`` / ``create`` /
        ``insert`` / ``upsert`` were invisible to it. Reading SDK 2.0.0's source shows all
        four build SurrealQL and send it through ``query_raw``, so all four were already
        counted — the "bound" was an author's expectation, never a reading, and it is
        exactly the failure ``CLAUDE.md`` records as *reverse-engineering what is written
        down*. The real blind spot is the own-RPC surface below.
        """
        from _sdk_guard import SAFE_CONNECTION_METHODS

        uncountable = StoreTraffic.uncountable_doors()
        countable = StoreTraffic.COUNTABLE_DOORS
        every_door = {
            name
            for connection_class in SDK_CONNECTION_CLASSES
            for name, function in inspect.getmembers(connection_class, inspect.isfunction)
            if not name.startswith("_")
            and (
                inspect.iscoroutinefunction(function)
                or getattr(function, "_sdk_guarded", False)
            )
        }
        assert every_door, "no public awaitable methods were found on the SDK connection classes"
        assert uncountable | countable | set(SAFE_CONNECTION_METHODS) >= every_door, (
            f"these SDK connection doors are in NO bucket: "
            f"{sorted(every_door - uncountable - countable - set(SAFE_CONNECTION_METHODS))}. "
            f"Every door is countable, uncountable, or in _sdk_guard's evidence-backed safe "
            f"set — an unbucketed one is a call this instrument neither counts nor refuses"
        )
        assert not (uncountable & countable), (
            f"a door is declared both countable and uncountable: {sorted(uncountable & countable)}"
        )
        for routed_through_query_raw in ("select", "create", "insert", "upsert", "delete"):
            assert routed_through_query_raw in countable, (
                f"{routed_through_query_raw!r} is no longer derived as routing through "
                f"query_raw. Either the SDK changed — in which case every measurement in "
                f"this file now undercounts and the derivation must be re-read against the "
                f"new source — or the derivation broke and is silently returning less than "
                f"the SDK offers. countable={sorted(countable)}"
            )
        for own_rpc_door in ("begin", "commit", "cancel", "live", "kill", "use"):
            assert own_rpc_door in uncountable, (
                f"{own_rpc_door!r} is not in the uncountable set. It sends its OWN request "
                f"message rather than a SurrealQL statement, so a build that used it would "
                f"be measured as FREE. `begin`/`commit` are the ones with teeth: ruling R7 "
                f"is a claim about TRANSACTIONS, and a transaction opened by RPC rather than "
                f"by a BEGIN-bearing statement would undercount round trips in the pin that "
                f"exists to prove the two reads share one snapshot"
            )

    async def test_the_query_DELEGATION_this_instrument_RESTS_ON_is_CHECKED(self) -> None:
        """⛔ The assumption the instrument's own docstring makes, turned into a measurement.

        *"``query()``'s body is ``response = await self.query_raw(...)``"* is a READ of SDK
        2.0.0's source, and it is load-bearing: if it stopped being true, ``query`` calls
        would be counted as zero round trips while still LOOKING observed, and this whole
        file's growth comparisons would compare two zeros.

        A doc is a source, not an oracle (``CLAUDE.md``, #107): the SDK's behaviour is
        checked against the SDK, here, in the same run as the pins that depend on it. Exactly
        one round trip for one statement also kills the double-counting bug the instrument's
        first version had (measured: one two-row read reported ``calls=2, rows=4``).
        """
        ledger, env = await _fresh_ledger()
        try:
            connection = await ledger._ensure_connection()  # noqa: SLF001 - the seam IS the probe

            async def _one_statement_through_query() -> None:
                await connection.query(f"SELECT count() FROM {TASK_TABLE} GROUP ALL")

            traffic = await measure_store_traffic(ledger, _one_statement_through_query)
            assert "query" in traffic.doors, (
                f"the `query` door was not recorded, so its delegation cannot be checked at "
                f"all: {traffic}"
            )
            assert traffic.calls == 1, (
                f"ONE statement through `connection.query()` was counted as "
                f"{traffic.calls} round trip(s). 0 means `query` no longer delegates to "
                f"`query_raw` and every measurement in this file is fiction; more than 1 "
                f"means both doors are being counted and every round-trip number is "
                f"inflated: {traffic}"
            )
        finally:
            await ledger.close()
            await drop_database(env)


# =========================================================================== #
# HOLE 7 — R9's HONEST TOTAL, resolved as an ASSERTED EMPTINESS (added 2026-07-28, wave r4).
#
# ``CLAUDE.md`` § TRUST — THE HARD DEFINITION, leg 2, owed-construction table
# (``docs/design/2026-07-28-04b-model-consumer-audit.md`` §11.1, last row):
#
#   | ``query``'s R9 elision line | store × error on the honest-total count | a fabricated
#   | or absent total beside a capped listing | construct the failed count; the line goes
#   | loud or drops the NUMBER, never invents one |
#
# ⚠ **RE-DERIVED HERE, AND THE ANSWER IS THAT 04b-1 HAS NO TOTAL TO CONSTRUCT AGAINST.**
# ``TaskLedger.query_tasks`` serves ``list[Task]``: rows, and nothing beside them.  Ruling
# R9's counted-elision line (*"+K more — re-run with limit=N"*) is a RENDER, routed to
# 04b-2 by the previous wave (``REPORT-contractfix-04b1-r3.md`` §RESIDUALS R-7), and the
# store-side count that would feed it does not exist at this layer.
#
# The law's own §12.2 step 4 says what to do with a derived pair that has no construction:
# *"every derived pair carries either a CONSTRUCTED forgery pin or a RECORDED named bound;
# a pair with neither is the gap report … a verb reaching no seam is pure-render — and that
# emptiness is ASSERTED, not assumed."*  So the emptiness is asserted below rather than
# claimed in prose, and the bound is recorded as a FACT:
#
#   **04b-1's task-read surface serves no total.  The construction for R9's elision line is
#   OWED BY 04b-2, in the packet that builds the line** — a failed count must go loud or
#   drop the NUMBER, and must never restate ``len(rows)`` as a ledger-wide total, which is
#   the retiring clause's *"an `n` restated beside a claim rather than DERIVED from the
#   computation that produced it"* wearing a capped listing.
#
# RED TODAY: neither leg — this class is GREEN at ``70cc5a4`` and must STAY green until
# someone adds a total, at which point it reddens WITH the instruction it owes.
# =========================================================================== #


class TestNoTOTALIsServedThatWasNotMEASURED:
    """A PINNED BOUND, in the *"when you cannot close a hole, pin it"* sense (``CLAUDE.md``,
    #137/#138).

    ⚠ **COLOUR, DERIVED rather than assumed** (an earlier draft of this docstring said
    *"green before and after"* and was wrong): BOTH legs are **RED at ``70cc5a4``** for ONE
    reason that has nothing to do with totals — ``query_tasks`` does not accept ``limit``
    yet, and ruling **R5** adds it.  The cap is not decoration here: the fabrication hazard
    §11.1 names is *"a total beside a CAPPED listing"*, so a leg without the cap would be
    describing a different surface.  Both go green with R5 and must STAY green.

    An unpinned known limitation is indistinguishable from an unknown one.  This one says,
    mechanically: *the ledger serves ROWS and nothing beside them, so there is no number
    here that could be invented.*  The day a builder wraps the answer in a result object
    carrying a count, this pin goes RED carrying its own re-open instruction — which is
    exactly the behaviour a bound is supposed to have, rather than being silently inherited
    or silently "fixed".
    """

    async def test_query_tasks_serves_ROWS_and_NOTHING_BESIDE_THEM(self) -> None:
        """⛔ The asserted emptiness.  Deny-by-default: the SAFE shape is one thing (a list
        of rows) and the set of names a fabricated total could wear is unbounded — the same
        reasoning ``TestTheResultIsSELFDESCRIBING``'s exact-field-set pin uses for the
        transitive read's own uncountable tail.
        """
        ledger, env = await _fresh_ledger()
        try:
            await _seed_unrelated_tasks(ledger, UNRELATED_TASK_COUNT_SMALL)
            served = await _served_rows(ledger, limit=_SERVED_LIMIT)
            assert type(served) is list, (
                f"query_tasks served a {type(served).__name__} rather than a plain list. If "
                f"that wrapper carries a TOTAL beside a capped listing, it has just acquired "
                f"the leg-2 construction §11.1 owes: build the failed-count world and prove "
                f"the line goes LOUD or drops the NUMBER — never restates len(rows), which "
                f"is not a total at all once ruling R5 pushed the limit into the statement. "
                f"Then delete this pin and say so in the wave report"
            )
            assert all(isinstance(row, Task) for row in served), (
                f"query_tasks served something that is not a Task: "
                f"{[type(row).__name__ for row in served]}"
            )
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_POSITIVE_CONTROL_the_capped_read_really_DOES_serve_rows(self) -> None:
        """Without this, the leg above is satisfied perfectly by ``return []`` — a build
        that serves nothing serves no invented total either, and the emptiness assertion
        would be measuring the absence of an answer rather than the absence of a claim.
        """
        ledger, env = await _fresh_ledger()
        try:
            await _seed_unrelated_tasks(ledger, UNRELATED_TASK_COUNT_LARGE)
            served = await _served_rows(ledger, limit=_SERVED_LIMIT)
            assert len(served) == _SERVED_LIMIT, (
                f"the capped read served {len(served)} rows against a ledger holding "
                f"{UNRELATED_TASK_COUNT_LARGE}; the control cannot show that the emptiness "
                f"pin is looking at a real answer"
            )
        finally:
            await ledger.close()
            await drop_database(env)
