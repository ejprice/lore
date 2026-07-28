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

It therefore re-pins NOTHING.  The instruments it needs (``_rows_read``,
``_seed_unrelated_tasks``, ``_seed_legacy_task``, ``_drive_to``, the ``task_ledger``
fixture, the ledger vocabulary) are **IMPORTED from** ``test_blocks_edge`` rather than
cloned — repo law #102, "if two call sites need the same POLICY it is a FUNCTION THEY
CALL".  ⚠ **ESCALATED, NOT SETTLED:** a test module importing a sibling test module is
the DRY-correct move but the wrong long-term home.  ``_rows_read`` belongs beside
``_surreal_harness.run`` in a shared helper, exactly as ``_enforced_relations_scaffold``
already houses the migration idiom; that file is outside this author's writable set, so
the import stands and the move is proposed in ``REPORT-contract-04b1-253.md`` §RESIDUALS.

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
* The tool-level ``limit``, which slices AFTER materialisation at ``server.py``'s
  dispatcher — outside 04b-1's writable set.  SECTION I flags it; this file flags it
  again in its report rather than folding it in.
* Result ORDER.  ``query_tasks`` promises none (``_task_fakes`` deliberately reorders to
  keep consumers honest), so store reference §7's *ORDER BY under an explicit projection*
  hazard is a REPORTED RISK for the builder, not an invented requirement pinned here.
* Concurrency.  A racing writer between the candidate read and the blocker read is a real
  TOCTOU for any two-read rewrite; a contract pin is the wrong instrument (≥8-way × 20
  consecutive green runs).  Flagged in the report, NOT silently dropped.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
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
    _rows_read,
    _seed_legacy_task,
    _seed_unrelated_tasks,
    task_ledger,  # noqa: F401 - re-exported pytest fixture
)

#: A second owner identity, so every owner pin has something to be WRONG about. A single
#: owner in a fixture makes ``owner=X`` and "every owned task" indistinguishable.
OTHER_ACTOR = "reviewer-04b1"

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


async def _collect(ledger: TaskLedger, sink: set[str], **filters: Any) -> None:
    """Run ``query_tasks(**filters)`` and record the served ids into ``sink``.

    ``_rows_read`` takes a zero-argument callable and returns the ROW count, so the served
    ANSWER has to leave by a side channel; this is that channel. Both halves are asserted
    by every caller — see :meth:`TestTheBLOCKEDPathIsBoundedToo._measure`.
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
                rows = await _rows_read(
                    ledger,
                    lambda: _collect(ledger, served, owner=OTHER_ACTOR, blocked=False),
                )
                return rows, served
            await ledger.transition(target, STATUS_WONTFIX, actor=ACTOR)
            served = set()
            rows = await _rows_read(
                ledger,
                lambda: _collect(ledger, served, status=STATUS_WONTFIX, blocked=False),
            )
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
                rows = await _rows_read(ledger, lambda: _collect(ledger, served, blocked=False))
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
