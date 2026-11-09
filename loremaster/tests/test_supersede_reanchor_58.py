"""Contract for packet **58** — ``supersede(X → X')`` RE-ANCHORS every dependent of X (#356).

*Every claim in this file is scoped to the tree at ``1206233`` (branch ``feat/surreal-unification``),
2026-09-26, authored by ``contract-58``.  "RED at HEAD" means RED at that commit.*

Spec, in precedence order (later wins):

* ``docs/plans/v2/58-supersede-reanchor.md`` — Mission, Scope IN 1 + 3, Exit's required pins.
* ``docs/plans/v2/design/2026-08-11-task-coordination-substrate.md`` §ADDENDUM A-174.
* ``docs/design/2026-09-26-packet58-kickoff-rulings.md`` @ ``c8d3241`` — F-1 (a refuse-and-teach hub
  cap DERIVED from the composed statement count, pinned cap−1/cap/cap+1), F-2 (rewire ∀ dependents
  including terminal ones), §6 (this contract's worklist), §7 (the removed-behaviour seeds).

What 58 changes, in one sentence: on a supersede, every row whose ``blocked_by`` names X has that entry
rewritten to X' (deduped), its ``X→blocks→Y`` edge replaced by ``X'→blocks→Y``, and a
``{actor, action: "dependency_reanchored", from: X, to: X', at}`` event appended — all in the SAME
transaction as the stamp and the successor CREATE, so no dependent is ever stranded on a superseded row.

⚠ **Store law read first** (``docs/reference/surrealdb-31-capabilities.md`` §2 THROW-on-zero CAS +
server-side ``+=``; §3 ``execute_transaction``; §4 RELATE bound RecordIDs / ``ENFORCED`` / an edge's
endpoints cannot be UPDATEd — re-point = DELETE + RELATE).  The kickoff §1 FLAG (``array::map`` +
``IF … THEN … ELSE … END`` inside the guarded UPDATE) was PROBED on 3.2.4 by
``scripts/probe_reanchor_58.py`` (exit 0) — the spelling works; nothing here depends on which spelling a
build picks.

Amendment 1 (``docs/design/2026-09-26-packet58-amendment-1.md`` @ ``f4e96b4``, later wins) rules FORK-A =
A1 (a terminal X re-anchors ∀; the re-blocked subset is SERVED —
:class:`TestSupersedeOfATerminalPredecessorA1`), FORK-C R1 closed in-transaction as a typed teaching
refusal (:class:`TestAConcurrentCreateIsRefusedNotStranded`)
and R2 healed at boot (:class:`TestTheBootHealReanchorsStragglers`).

Fixtures DISCRIMINATE (CLAUDE.md): ≥7 dependents across every status the public verbs reach with an OPEN
blocker (``open``, ``blocked``, ``in_progress``, ``done``, ``wontfix``) + a raw-forced ``claimed`` row + a
SUPERSEDED dependent AND its #174-inheriting successor + a dual-blocker row; the superseder is a
DIFFERENT identity from every row's creator; hub sizes come from the DERIVED accessor, never a literal.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pytest
import pytest_asyncio
from _reanchor_58_support import (
    ACTION_REANCHORED,
    CLAIMANT,
    CREATOR,
    PHANTOM_ID,
    RETIRED_STATEMENT_CAP,
    SUPERSEDER,
    ApplyHook,
    all_columns,
    assert_edge_mirrors_column_for_every_row,
    assert_unpatched_row_cap,
    bulk_seed_dependents,
    column,
    composed_rows,
    create,
    drive_to,
    edge_pairs,
    events_of,
    ledger58,
    new_ledger,
    raw,
    raw_force,
    raw_relate,
    raw_seed_row,
    row_count,
    shrunk_row_caps,
    snapshot,
    successor_of,
    supersede,
    updated_at_of,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import (
    STATUS_BLOCKED,
    STATUS_CLAIMED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    STATUS_WONTFIX,
    IllegalTransitionError,
    TaskCycleError,
    TaskLedger,
    TaskLedgerError,
)

__all__ = ["ledger58", "shrunk_row_caps"]  # imported fixtures USED by name — keep ruff from pruning them

# The module whose ``compose`` / ``_apply`` the supersede routes through (the statement-count spy's seam).
TASKS_MODULE = "loremaster.tasks"


# =========================================================================== #
# THE MAIN WORLD — one open X, NINE dependents of distinct shapes, a bystander.
# =========================================================================== #


@dataclass
class World:
    """The main re-anchor fixture, captured BEFORE and AFTER the supersede."""

    ledger: TaskLedger
    env: SurrealEnv
    old: str
    other: str
    bystander: str
    #: dependent label → id (every row whose blocked_by names ``old`` at supersede time)
    dependents: dict[str, str]
    events_before: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    updated_before: dict[str, Any] = field(default_factory=dict)
    columns_before: dict[str, list[str]] = field(default_factory=dict)
    result: Any = None
    successor: str = ""


async def _build_world(ledger: TaskLedger, env: SurrealEnv) -> World:
    old = await create(ledger, "X — the task that will be reframed")
    other = await create(ledger, "Other — a live blocker nobody supersedes")
    bystander = await create(ledger, "a bystander blocked only on Other", [other])
    dependents: dict[str, str] = {}
    for label, status in (
        ("open", STATUS_OPEN),
        ("blocked", STATUS_BLOCKED),
        ("in_progress", STATUS_IN_PROGRESS),
        ("done", STATUS_DONE),
        ("wontfix", STATUS_WONTFIX),
    ):
        task_id = await create(ledger, f"dependent in {label}", [old])
        await drive_to(ledger, task_id, status)
        dependents[label] = task_id
    dependents["dual"] = await create(ledger, "dependent on X AND Other", [old, other])
    # A dependent that was ITSELF superseded (its row still names X) and its #174 successor, which
    # INHERITED X (blocked_by=None).  Both name X; both are dependents; a build that filters superseded
    # rows out of the rewire leaves the first stranded forever.
    superseded_dependent = await create(ledger, "a dependent that was itself reframed", [old])
    inherited = successor_of(await supersede(ledger, superseded_dependent))
    dependents["superseded"] = superseded_dependent
    dependents["inherited_successor"] = inherited
    # RAW-FORCED ``claimed``: claim-only, and unclaimable while X is open — so this is a legacy /
    # FORK-A-shaped row, seeded so the ∀-status pin does not lean on the fork.
    claimed = await create(ledger, "a dependent forced into claimed (legacy shape)", [old])
    await raw_force(ledger, claimed, status=STATUS_CLAIMED, owner=CLAIMANT)
    dependents["claimed_raw"] = claimed
    world = World(
        ledger=ledger, env=env, old=old, other=other, bystander=bystander, dependents=dependents
    )
    for task_id in [*dependents.values(), old, other, bystander]:
        world.events_before[task_id] = await events_of(ledger, task_id)
        world.updated_before[task_id] = await updated_at_of(ledger, task_id)
        world.columns_before[task_id] = await column(ledger, task_id)
    assert sorted(await ledger.direct_dependents(old)) == sorted(dependents.values()), (
        "fixture self-check: every labelled dependent must name X before the supersede"
    )
    return world


@pytest_asyncio.fixture()
async def world(ledger58: tuple[TaskLedger, SurrealEnv]) -> World:
    ledger, env = ledger58
    built = await _build_world(ledger, env)
    built.result = await supersede(ledger, built.old)
    built.successor = successor_of(built.result)
    return built


class TestEveryDependentFollowsTheWorkToTheSuccessor:
    """RED at HEAD (#356: supersede touches no dependent).  Kickoff §6 row 1 + F-2."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_every_dependent_names_the_successor_and_NOT_the_superseded_task(
        self, world: World
    ) -> None:
        for label, task_id in world.dependents.items():
            got = await column(world.ledger, task_id)
            assert world.old not in got and world.successor in got, (
                f"dependent {label!r} ({task_id}) has blocked_by={got} after supersede("
                f"{world.old} → {world.successor}). F-2 rules EVERY dependent is rewired, whatever "
                f"its status (open/blocked/in_progress/done/wontfix/claimed, a superseded dependent "
                f"and its inheriting successor alike): a skipped row keeps naming a superseded task "
                f"forever — #356's strand"
            )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_only_the_X_entry_is_rewritten_order_and_other_blockers_kept(
        self, world: World
    ) -> None:
        dual = world.dependents["dual"]
        assert await column(world.ledger, dual) == [world.successor, world.other], (
            "a dependent on [X, Other] must become exactly [X', Other] — X replaced IN PLACE, the "
            "other blocker untouched, order preserved (a rewrite that rebuilds the list from "
            "scratch, drops Other, or appends X' at the end is a different dependency list)"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_the_bystander_row_is_byte_unchanged(self, world: World) -> None:
        assert await column(world.ledger, world.bystander) == [world.other]
        assert await events_of(world.ledger, world.bystander) == world.events_before[world.bystander]
        assert await updated_at_of(world.ledger, world.bystander) == world.updated_before[
            world.bystander
        ], "a row that does not name X must not be written at all (updated_at moved)"

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_the_edge_mirrors_the_column_for_EVERY_row_and_no_edge_leaves_X(
        self, world: World
    ) -> None:
        """⛔ Kills the column-only rewire (the boot backfill would 'heal' the missing X'→Y edge
        LATER — this pin runs BEFORE any boot) and the leftover-X→Y-edge rewire.  ∀ ROWS, derived."""
        checked = await assert_edge_mirrors_column_for_every_row(
            world.ledger, where="after supersede with 9 dependents"
        )
        assert checked == await row_count(world.ledger), "coverage: every row was checked"
        pairs = await edge_pairs(world.ledger)
        assert not [pair for pair in pairs if pair[0] == world.old], (
            f"edges still leave the superseded task {world.old}: "
            f"{[pair for pair in pairs if pair[0] == world.old]}"
        )
        for label, task_id in world.dependents.items():
            assert pairs.count((world.successor, task_id)) == 1, (
                f"dependent {label!r} must carry EXACTLY ONE {world.successor}→{task_id} edge; "
                f"got {pairs.count((world.successor, task_id))}"
            )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_direct_dependents_of_X_is_EMPTY_and_of_the_successor_is_the_whole_set(
        self, world: World
    ) -> None:
        """Removed-behaviour seed §7.2: ``direct_dependents(X)`` after a supersede CHANGES from
        "the stranded ids" to ``[]`` by construction."""
        assert await world.ledger.direct_dependents(world.old) == []
        assert sorted(await world.ledger.direct_dependents(world.successor)) == sorted(
            world.dependents.values()
        )


class TestEachDependentCarriesTheReanchorNote:
    """RED at HEAD.  P58 Scope IN 1: ``{actor, action: "dependency_reanchored", from: X, to: X', at}``."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_exactly_ONE_new_event_per_dependent_naming_X_X_prime_and_the_SUPERSEDER(
        self, world: World
    ) -> None:
        for label, task_id in world.dependents.items():
            before = world.events_before[task_id]
            after = await events_of(world.ledger, task_id)
            assert after[: len(before)] == before, (
                f"dependent {label!r}: the re-anchor REWROTE prior provenance events instead of "
                f"appending (server-side `+=` is the store idiom — never a Python-merged object)"
            )
            new = after[len(before):]
            assert len(new) == 1, f"dependent {label!r}: expected ONE new event, got {new}"
            event = new[0]
            assert event.get("action") == ACTION_REANCHORED, event
            assert event.get("from") == world.old and event.get("to") == world.successor, (
                f"dependent {label!r}: the note must name the ORIGINAL blocker (from) and the "
                f"successor (to): {event}"
            )
            assert event.get("actor") == SUPERSEDER, (
                f"dependent {label!r}: the note's actor must be the identity that PERFORMED the "
                f"supersede ({SUPERSEDER!r}), not the row's creator ({CREATOR!r}) nor a worker: "
                f"{event}"
            )
            assert isinstance(event.get("at"), str) and datetime.fromisoformat(event["at"]), event

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_the_note_lands_on_the_DEPENDENT_never_on_X_or_the_successor(
        self, world: World
    ) -> None:
        old_events = await events_of(world.ledger, world.old)
        assert not [e for e in old_events if e.get("action") == ACTION_REANCHORED], old_events
        successor_events = await events_of(world.ledger, world.successor)
        assert not [e for e in successor_events if e.get("action") == ACTION_REANCHORED], (
            successor_events
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_updated_at_is_stamped_on_every_rewired_dependent(self, world: World) -> None:
        """Kickoff §4 rider iv: the shell stamps ``updated_at`` ∀ callers; the re-anchor now does too
        (§2: a re-anchored ``done`` row re-appears in the next rollup window — ACCEPTED, §7.9)."""
        for label, task_id in world.dependents.items():
            after = await updated_at_of(world.ledger, task_id)
            before = world.updated_before[task_id]
            assert after is not None and (before is None or after > before), (
                f"dependent {label!r}: updated_at {before!r} → {after!r} — not stamped by the rewrite"
            )


class TestTheSupersedeItselfIsUnchanged:
    """The #174 / stamp behaviour 58 must PRESERVE (required-green)."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_X_is_stamped_and_the_successor_is_open_unowned(self, world: World) -> None:
        old = await world.ledger.get_task(world.old)
        assert old.superseded_by == world.successor
        successor = await world.ledger.get_task(world.successor)
        assert successor.status == STATUS_OPEN and successor.owner is None
        assert successor.blocked_by == world.columns_before[world.old] == [], (
            "X had no blockers, so the #174 INHERIT default gives the successor none"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_the_result_names_exactly_the_reanchored_dependents(self, world: World) -> None:
        """Kickoff §7.7: ``SupersedeResult(successor_id, reanchored)`` — the PRE-write list, because
        a post-write ``direct_dependents(X)`` is ``[]`` by construction."""
        reanchored = list(world.result.reanchored)
        assert len(reanchored) == len(set(reanchored)), f"duplicates in reanchored: {reanchored}"
        assert sorted(reanchored) == sorted(world.dependents.values()), (
            f"SupersedeResult.reanchored={sorted(reanchored)} is not the dependent set "
            f"{sorted(world.dependents.values())}"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_the_result_is_the_typed_carrier(self, world: World) -> None:
        from loremaster.tasks import SupersedeResult

        assert isinstance(world.result, SupersedeResult)
        assert world.result.successor_id == world.successor


class TestTheRewireDedupes:
    """RED at HEAD.  Kickoff §2 rider: a dependent that would name X' twice holds it ONCE, ONE edge.

    ⚠ The kickoff's fixture *"a dependent already naming X'"* is UNREACHABLE: X' is minted INSIDE the
    supersede (``uuid4().hex``), so no pre-existing row can name it.  The REACHABLE duplicate is the
    LEGACY ``[X, X]`` row (ruling T5's shape — rows that predate the birth-time dedupe), seeded raw.
    """

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_legacy_duplicate_X_X_becomes_ONE_successor_entry_and_ONE_edge(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        old = await create(ledger, "X")
        legacy = "legacy0058dup00000000000000000000"
        await raw_seed_row(ledger, legacy, blocked_by=[old, old])
        await raw_relate(ledger, old, legacy)
        result = await supersede(ledger, old)
        successor = successor_of(result)
        assert await column(ledger, legacy) == [successor]
        pairs = await edge_pairs(ledger)
        assert pairs.count((successor, legacy)) == 1 and (old, legacy) not in pairs, pairs
        assert list(result.reanchored).count(legacy) == 1

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_legacy_PHANTOM_entry_is_left_untouched_and_carries_no_edge(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """Required-green (kickoff §6): only the X entry is rewritten; the phantom stays (it still
        blocks — the claim CAS counts it) and never gets an ENFORCED edge (it names no row)."""
        ledger, _env = ledger58
        old = await create(ledger, "X")
        assert not await raw(
            ledger, f"SELECT id FROM type::record('{TASK_TABLE}', $id)", {"id": PHANTOM_ID}
        ), "the phantom id must genuinely name no row"
        legacy = "legacy0058phantom000000000000000"
        await raw_seed_row(ledger, legacy, blocked_by=[old, PHANTOM_ID])
        await raw_relate(ledger, old, legacy)
        successor = successor_of(await supersede(ledger, old))
        assert await column(ledger, legacy) == [successor, PHANTOM_ID]
        await assert_edge_mirrors_column_for_every_row(ledger, where="phantom-bearing dependent")


class TestTheSupersedeIsONETransaction:
    """RED at HEAD (nothing to roll back — no dependent is written).  P58 Exit: *"one injected failure
    at dependent k of N ⇒ X unstamped, X' absent, ALL N unchanged — constructed, with a positive
    control"*.

    The injection is SERVER-SIDE and build-agnostic: a test-only ``DEFINE EVENT`` on the fresh
    database THROWs when dependent k's row is UPDATEd (or when its new edge is CREATEd).  Store ref §10:
    sync events run IN the triggering transaction and can THROW to abort.  Each leg carries its OWN
    control that the event is armed (a raw write to row k is refused), so a supersede that failed for
    some OTHER reason cannot pass as "atomic".
    """

    INJECTED = "injected-58"

    async def _three(self, ledger: TaskLedger) -> tuple[str, list[str]]:
        old = await create(ledger, "X")
        dependents = sorted([await create(ledger, f"dependent {index}", [old]) for index in range(3)])
        return old, dependents

    @pytest.mark.usefixtures("shrunk_row_caps")
    @pytest.mark.parametrize("position", [0, 1, 2], ids=["k=1", "k=2", "k=3"])
    @pytest.mark.parametrize("point", ["row_update", "edge_create"])
    async def test_a_failure_at_dependent_k_rolls_back_EVERYTHING(
        self, ledger58: tuple[TaskLedger, SurrealEnv], position: int, point: str
    ) -> None:
        ledger, _env = ledger58
        old, dependents = await self._three(ledger)
        target = dependents[position]
        if point == "row_update":
            event = (
                f"DEFINE EVENT inject58 ON TABLE {TASK_TABLE} WHEN $event = 'UPDATE' AND "
                f"record::id($after.id) = '{target}' THEN {{ THROW '{self.INJECTED}' }}"
            )
        else:
            event = (
                f"DEFINE EVENT inject58 ON TABLE {BLOCKS_RELATION} WHEN $event = 'CREATE' AND "
                f"record::id($after.out) = '{target}' THEN {{ THROW '{self.INJECTED}' }}"
            )
        await raw(ledger, event)
        before = await snapshot(ledger)
        with pytest.raises(Exception):  # noqa: B017, PT011 - ANY failure; the state is the assertion
            await supersede(ledger, old)
        assert await snapshot(ledger) == before, (
            f"an injected failure at dependent k={position + 1} of 3 ({point}) left the ledger "
            f"CHANGED: the stamp, the successor, a rewire, a note or an edge committed without the "
            f"rest. A-174: a partial rewire that strands SOME dependents is worse than none — "
            f"stamp + CREATE + every re-anchor ride ONE BEGIN…COMMIT"
        )
        # CONTROL: the event is armed (so the supersede failed BECAUSE of the injection) …
        with pytest.raises(Exception):  # noqa: B017, PT011
            if point == "row_update":
                await raw_force(ledger, target, updated_at=datetime.now().astimezone())
            else:
                other = await create(ledger, "a fresh blocker for the control")
                await raw_relate(ledger, other, target)
        # … and without it the SAME fixture completes (so the fixture can succeed at all).
        injected_table = TASK_TABLE if point == "row_update" else BLOCKS_RELATION
        await raw(ledger, f"REMOVE EVENT inject58 ON TABLE {injected_table}")
        successor = successor_of(await supersede(ledger, old))
        for task_id in dependents:
            assert successor in await column(ledger, task_id)


class TestACycleClosingRewireIsRefusedWhole:
    """RED at HEAD.  P58 Scope IN 1: *"a rewire CAN close a cycle: X' transitively blocked_by Y"*.

    Y blocked_by [X]; Z blocked_by [Y]; supersede X with ``blocked_by=[Z]``.  BEFORE the rewire there is
    no cycle (X' → Z → Y → X); AFTER it Y → X' → Z → Y.  A cycle check over the UN-rewired graph —
    today's ``_refuse_a_cycle({X': [Z]})`` — finds nothing.
    """

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_refused_as_a_cycle_naming_it_and_NOTHING_changed(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        old = await create(ledger, "X")
        dependent = await create(ledger, "Y waits on X", [old])
        downstream = await create(ledger, "Z waits on Y", [dependent])
        before = await snapshot(ledger)
        with pytest.raises(TaskCycleError) as caught:
            await supersede(ledger, old, blocked_by=[downstream])
        message = str(caught.value)
        assert dependent in message and downstream in message, (
            f"the refusal must NAME the cycle the rewire would close (Y={dependent}, Z={downstream}): "
            f"{message!r}"
        )
        assert await snapshot(ledger) == before, (
            "a refused cycle-closing supersede must roll back WHOLE: X un-stamped, no successor, "
            "Y/Z columns + edges + provenance unchanged"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_CONTROL_the_same_shape_without_the_closing_dependency_succeeds(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        old = await create(ledger, "X")
        dependent = await create(ledger, "Y waits on X", [old])
        await create(ledger, "Z waits on Y", [dependent])
        unrelated = await create(ledger, "W, unrelated")
        successor = successor_of(await supersede(ledger, old, blocked_by=[unrelated]))
        assert await column(ledger, dependent) == [successor]

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_CONTROL_a_legacy_cycle_ELSEWHERE_does_not_refuse_a_reanchor(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """``_refuse_a_cycle``'s own step-over rule: a pre-existing loop among rows this call does not
        write must not block it (a build that refuses on ANY cycle in the closure fails here)."""
        ledger, _env = ledger58
        loop_a, loop_b = "legacyloop58a000000000000000000", "legacyloop58b000000000000000000"
        await raw_seed_row(ledger, loop_a, blocked_by=[loop_b])
        await raw_seed_row(ledger, loop_b, blocked_by=[loop_a])
        await raw_relate(ledger, loop_b, loop_a)
        await raw_relate(ledger, loop_a, loop_b)
        old = await create(ledger, "X, itself blocked by the legacy loop", [loop_a])
        dependent = await create(ledger, "Y waits on X", [old])
        successor = successor_of(await supersede(ledger, old))
        assert await column(ledger, dependent) == [successor]


class TestAConcurrentCreateIsRefusedNotStranded:
    """RED at HEAD.  Amendment 1 FORK-C **R1** (``docs/design/2026-09-26-packet58-amendment-1.md``):
    CLOSED in-transaction.

    A ``create_task(Y2, blocked_by=[X])`` COMMITS after the supersede's pre-reads and BEFORE its
    transaction (constructed at the ONE seam every task write composes through — ``_apply``).  Ruled:
    the composed supersede ends with a closing guard (any row still naming X → THROW), the rollback is a
    TYPED, TEACHING refusal (*"… created while this supersede was being prepared — nothing changed;
    retry the supersede"*), and the ledger does NOT retry on its own (a hand-rolled retry is the #102
    class).  A build that rewires only its pre-read list strands Y2 and returns success.
    """

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_the_supersede_is_REFUSED_byte_inert_and_TEACHES_retry(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, env = ledger58
        old = await create(ledger, "X")
        first = await create(ledger, "Y1 waits on X", [old])
        racer = new_ledger(env)
        created: list[str] = []
        at_apply: list[tuple[list[str], list[tuple[str, str]]]] = []
        apply_calls: list[int] = []

        async def _concurrent_create() -> None:
            created.append(await create(racer, "Y2 created while X was being superseded", [old]))
            at_apply.append(await snapshot(ledger))

        hook = ApplyHook(ledger, _concurrent_create)
        real_call = hook.__call__

        async def _counting(fragments: Any) -> None:
            apply_calls.append(1)
            await real_call(fragments)

        try:
            with hook.installed():
                ledger._apply = _counting  # type: ignore[method-assign]  # noqa: SLF001
                with pytest.raises(TaskLedgerError) as caught:
                    await supersede(ledger, old)
        finally:
            await racer.close()
        assert hook.fired and created, "the constructed interleaving never ran — the pin saw nothing"
        assert len(apply_calls) == 1, (
            f"the ledger sent the supersede {len(apply_calls)} times — amendment 1 rules NO automatic "
            f"retry in the ledger (the refusal teaches the CALLER to retry)"
        )
        message = str(caught.value)
        assert old in message and "nothing changed" in message.lower() and "retry" in message.lower(), (
            f"the R1 refusal must name X, say nothing changed, and teach a retry: {message!r}"
        )
        assert await snapshot(ledger) == at_apply[0], (
            "the refused supersede changed the ledger: X stamped, a successor minted, or a dependent "
            "rewired — the closing guard must roll the WHOLE transaction back"
        )
        # POSITIVE CONTROL: a second call sees both dependents and re-anchors them.
        successor = successor_of(await supersede(ledger, old))
        assert await column(ledger, first) == [successor]
        assert await column(ledger, created[0]) == [successor]


class TestTheHubBoundIsDERIVED:
    """RED at HEAD (no accessor; a hub supersede fails with ``compose``'s bare count error).

    Kickoff F-1: refuse-and-teach at a DERIVED cap.  The derivation is checked against the transaction
    the ledger ACTUALLY composes: a spy on ``loremaster.tasks.compose`` counts the body statements of a
    successful supersede at N=1, 2, 3 dependents; ``per = c(2) − c(1)``, ``fixed = c(1) − per``,
    linearity checked at N=3, and ``max_reanchor_dependents(K)`` must equal
    ``(TXN_ROW_HARD_CAP − fixed) // per`` (r5: rows, am-15 §1.2).  A literal cap cannot survive the
    in-suite mutation leg.
    """

    @staticmethod
    async def _composed_count(
        ledger: TaskLedger, monkeypatch: pytest.MonkeyPatch, dependents: int, successor_deps: int
    ) -> int:
        """Supersede a fresh X with ``dependents`` dependents and ``successor_deps`` successor blockers;
        return the body-statement count of the LAST transaction ``compose`` built for it."""
        import importlib

        tasks_module = importlib.import_module(TASKS_MODULE)
        counts: list[int] = []
        real_compose = tasks_module.compose

        def _spy(*fragments: Any) -> Any:
            counts.append(composed_rows(fragments))  # r5: the ROW count compose bounds (am-15 §1.1)
            return real_compose(*fragments)

        old = await create(ledger, "X")
        for index in range(dependents):
            await create(ledger, f"dependent {index}", [old])
        blockers = [await create(ledger, f"successor blocker {i}") for i in range(successor_deps)]
        monkeypatch.setattr(tasks_module, "compose", _spy, raising=True)
        try:
            await supersede(ledger, old, blocked_by=blockers)
        finally:
            monkeypatch.setattr(tasks_module, "compose", real_compose, raising=True)
        assert counts, "the spy saw no compose call — the supersede does not route through compose"
        return counts[-1]

    async def _derive(
        self, ledger: TaskLedger, monkeypatch: pytest.MonkeyPatch, successor_deps: int
    ) -> tuple[int, int]:
        c1 = await self._composed_count(ledger, monkeypatch, 1, successor_deps)
        c2 = await self._composed_count(ledger, monkeypatch, 2, successor_deps)
        c3 = await self._composed_count(ledger, monkeypatch, 3, successor_deps)
        per = c2 - c1
        fixed = c1 - per
        assert per > 0 and c3 == fixed + 3 * per, (
            f"the composed statement count is not linear in dependents (c1={c1}, c2={c2}, c3={c3}) — "
            f"the cap derivation assumes a fixed + per-dependent shape (kickoff §1)"
        )
        return fixed, per

    @pytest.mark.parametrize("successor_deps", [0, 2])
    async def test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies(
        self,
        ledger58: tuple[TaskLedger, SurrealEnv],
        monkeypatch: pytest.MonkeyPatch,
        successor_deps: int,
    ) -> None:
        ledger, _env = ledger58
        assert_unpatched_row_cap()  # am-15 §1.4 L1 / §8.1: this leg runs at the REAL row cap
        fixed, per = await self._derive(ledger, monkeypatch, successor_deps)
        expected = (_txn.TXN_ROW_HARD_CAP - fixed) // per
        assert ledger.max_reanchor_dependents(successor_deps) == expected, (
            f"max_reanchor_dependents({successor_deps}) must be derived from the builder's own counts "
            f"(fixed={fixed}, per={per} measured off the composed transaction) → {expected}"
        )

    async def test_REAL_CAP_a_supersede_past_the_RETIRED_statement_cap_SUCCEEDS(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """am-15 §1.4 L2 (§8.1: REQUIRED, run WITHOUT the fixture): at the unpatched row cap, one supersede
        whose composed rows exceed SDK3's retired 5 000-statement cap re-anchors every dependent.  At the
        5 000 shrink a build that never left the statement cap (a literal, or ``min(old, new)``) passes
        every other pin — this leg refuses it."""
        ledger, _env = ledger58
        assert_unpatched_row_cap()
        fixed, per = await self._derive(ledger, monkeypatch, 0)
        dependents = (RETIRED_STATEMENT_CAP - fixed) // per + 1
        assert fixed + per * dependents > RETIRED_STATEMENT_CAP, "the leg must cross the retired bound"
        old = await create(ledger, "a hub past the retired statement cap")
        hub = await bulk_seed_dependents(ledger, old, dependents, tag="realcapx")
        result = await supersede(ledger, old)
        assert sorted(result.reanchored) == sorted(hub), (
            f"{dependents} dependents ({fixed + per * dependents} rows > the retired "
            f"{RETIRED_STATEMENT_CAP}) "
            f"must re-anchor at the real row cap — a statement bound survives beside the row bound (F12)"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_MUTATION_an_extra_per_dependent_statement_MOVES_the_cap(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Kickoff §1 rider ii, in-suite: every per-dependent write routes through the shell (§4), so
        appending ONE harmless statement to the shell's output raises ``per`` by one — and the
        accessor MUST follow.  A literal cap (or a hand-kept formula) stays put and reddens here."""
        from loremaster.store._txn import TxnFragment
        from loremaster.tasks import TaskLedger as Ledger

        ledger, _env = ledger58
        baseline = ledger.max_reanchor_dependents(0)
        original = Ledger._guarded_append_fragment

        def _padded(*args: Any, **kwargs: Any) -> Any:
            fragment = original(*args, **kwargs)
            return TxnFragment(statements=[*fragment.statements, "RETURN NONE"], params=fragment.params)

        monkeypatch.setattr(Ledger, "_guarded_append_fragment", staticmethod(_padded), raising=True)
        fixed, per = await self._derive(ledger, monkeypatch, 0)
        mutated = ledger.max_reanchor_dependents(0)
        assert mutated == (_txn.TXN_ROW_HARD_CAP - fixed) // per and mutated < baseline, (
            f"after padding the shell by one statement the composed per-dependent cost is {per}, so "
            f"the cap must move from {baseline} to {(_txn.TXN_ROW_HARD_CAP - fixed) // per}; "
            f"the accessor returned {mutated} — it is not derived from the builder"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    @pytest.mark.parametrize("successor_deps", [0, 2])
    @pytest.mark.parametrize("offset", [-1, 0], ids=["cap-1", "cap"])
    async def test_at_and_just_below_the_cap_EVERY_dependent_is_reanchored(
        self, ledger58: tuple[TaskLedger, SurrealEnv], successor_deps: int, offset: int
    ) -> None:
        ledger, _env = ledger58
        cap = ledger.max_reanchor_dependents(successor_deps)
        old = await create(ledger, "the hub")
        blockers = [await create(ledger, f"successor blocker {i}") for i in range(successor_deps)]
        hub = await bulk_seed_dependents(ledger, old, cap + offset, tag=f"hub{successor_deps}{offset + 1}x")
        result = await supersede(ledger, old, blocked_by=blockers)
        successor = successor_of(result)
        assert sorted(result.reanchored) == sorted(hub)
        stranded = [t for t, b in (await all_columns(ledger)).items() if old in b]
        assert not stranded, f"{len(stranded)} of {len(hub)} hub dependents still name X"
        await assert_edge_mirrors_column_for_every_row(ledger, where=f"hub of {len(hub)}")
        assert (await ledger.get_task(old)).superseded_by == successor

    @pytest.mark.usefixtures("shrunk_row_caps")
    @pytest.mark.parametrize("successor_deps", [0, 2])
    async def test_one_past_the_cap_is_REFUSED_byte_inert_and_TEACHES(
        self, ledger58: tuple[TaskLedger, SurrealEnv], successor_deps: int
    ) -> None:
        ledger, _env = ledger58
        cap = ledger.max_reanchor_dependents(successor_deps)
        old = await create(ledger, "the hub")
        blockers = [await create(ledger, f"successor blocker {i}") for i in range(successor_deps)]
        await bulk_seed_dependents(ledger, old, cap + 1, tag=f"over{successor_deps}x")
        before = await snapshot(ledger)
        with pytest.raises(TaskLedgerError) as caught:
            await supersede(ledger, old, blocked_by=blockers)
        message = str(caught.value)
        assert old in message and str(cap + 1) in message and str(cap) in message, (
            f"the refusal must name the task, its {cap + 1} dependents and the derived cap {cap}: "
            f"{message!r}"
        )
        assert "nothing changed" in message.lower(), (
            f"the refusal must SAY nothing changed (kickoff F-1 sentence): {message!r}"
        )
        # r5 (am-15 §8.2, A-9): r1's text check keyed on the RETIRED statement-cap wording and could no
        # longer fail. By TYPE now: neither the error nor its __cause__ is compose's own row-cap refusal …
        assert not isinstance(caught.value, _txn.TxnRowCapExceededError), (
            "the bare compose() row-cap refusal was served — F-1 rules a TEACHING refusal before any write"
        )
        assert not isinstance(caught.value.__cause__, _txn.TxnRowCapExceededError), (
            "the ledger re-wrapped compose()'s row-cap refusal — F-1 decides at the DERIVED cap, "
            "before compose"
        )
        # … and the positive control, same leg: composing cap+1 rows DOES raise it, so the
        # negative half above is shown able to fire (no message text is asserted).
        rows_needed = _txn.TXN_ROW_HARD_CAP + 1
        with pytest.raises(_txn.TxnRowCapExceededError):
            _txn.compose(_txn.TxnFragment(statements=["RETURN NONE"] * rows_needed, params={}))
        assert await snapshot(ledger) == before, "a refused hub supersede must write NOTHING"

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_crossing_the_WARN_threshold_logs_ONE_warning_and_SUCCEEDS(
        self,
        ledger58: tuple[TaskLedger, SurrealEnv],
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Kickoff §1 rider iv: the 800-statement WARN is a LOG, never a refusal.  Sized from the SAME
        measured ``fixed``/``per`` — the smallest hub whose transaction crosses the threshold."""
        ledger, _env = ledger58
        fixed, per = await self._derive(ledger, monkeypatch, 0)
        crossing = (_txn.TXN_ROW_WARN_THRESHOLD - fixed) // per + 1
        assert fixed + per * crossing > _txn.TXN_ROW_WARN_THRESHOLD >= fixed + per * (crossing - 1)
        below_old = await create(ledger, "a hub just BELOW the warn threshold")
        await bulk_seed_dependents(ledger, below_old, crossing - 1, tag="warnbelow")
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            await supersede(ledger, below_old)
        below = [r for r in caplog.records if r.levelno >= logging.WARNING and hasattr(r, "row_count")]
        assert not below, f"a below-threshold supersede warned: {[r.getMessage() for r in below]}"
        old = await create(ledger, "a hub just ABOVE the warn threshold")
        hub = await bulk_seed_dependents(ledger, old, crossing, tag="warnabove")
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            result = await supersede(ledger, old)
        warnings = [
            r for r in caplog.records if r.levelno == logging.WARNING and hasattr(r, "row_count")
        ]
        assert len(warnings) == 1, (
            f"expected exactly ONE WARNING carrying `row_count` for a {fixed + per * crossing}-"
            f"row supersede; got {[r.getMessage() for r in warnings]}"
        )
        assert getattr(warnings[0], "row_count") > _txn.TXN_ROW_WARN_THRESHOLD  # noqa: B009
        assert sorted(result.reanchored) == sorted(hub)


class TestTheBootBackfillAfterAReanchorIsANoOp:
    """GREEN at HEAD (measured at ``5d549a1``: the strand leaves column [X] AND edge X→Y, so the backfill
    has nothing to mint) — these are DISCRIMINATORS for wrong 58 builds, not HEAD: a re-anchor that
    rewrites the column but skips the RELATE makes the backfill mint X'→Y here (the boot would
    "heal" it, which is exactly why this runs BEFORE any boot is trusted).  Kickoff §2 rider + §6."""

    @staticmethod
    async def _backfill(ledger: TaskLedger, caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            await ledger._backfill_blocks_edges()  # noqa: SLF001 - the boot step, driven directly
        return [
            r for r in caplog.records
            if r.getMessage().startswith("task.backfill.")
        ]

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_after_a_reanchor_the_backfill_mints_nothing_and_records_nothing(
        self, world: World, caplog: pytest.LogCaptureFixture
    ) -> None:
        before = await edge_pairs(world.ledger)
        records = await self._backfill(world.ledger, caplog)
        assert await edge_pairs(world.ledger) == before, (
            "the boot backfill minted edges after a re-anchor — the re-anchor left a column entry "
            "without its edge (the backfill 'heals' it, so this is only visible HERE, before a boot)"
        )
        assert not records, [r.getMessage() for r in records]

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_after_a_REFUSED_supersede_the_backfill_mints_nothing(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger, _env = ledger58
        old = await create(ledger, "X")
        dependent = await create(ledger, "Y", [old])
        downstream = await create(ledger, "Z", [dependent])
        with pytest.raises(TaskCycleError):
            await supersede(ledger, old, blocked_by=[downstream])
        before = await edge_pairs(ledger)
        records = await self._backfill(ledger, caplog)
        assert await edge_pairs(ledger) == before and not records


HEAL_EVENT = "task.backfill.stragglers_reanchored"
HEAL_ACTOR = "boot-heal"
HEAL_REASON = "straggler"


class TestTheBootHealReanchorsStragglers:
    """RED at HEAD (no heal exists).  Amendment 1 FORK-C **R2**: the write-skew window (a create whose
    R10(ii) pre-check saw X live commits AFTER the supersede) is a NAMED bound HEALED at every boot by
    ``_reanchor_stragglers()`` beside ``_backfill_blocks_edges`` — the SAME re-anchor fragment, through
    the ONE shell, to the chain HEAD, noted ``actor: "boot-heal"`` / ``reason: "straggler"``, counted
    at INFO (``task.backfill.stragglers_reanchored``, ``count``), silent at 0, idempotent.  The same
    statement heals the fleet's LEGACY pre-58 strands at the 65 boot.  Stragglers are seeded RAW — the
    only door to a strand once the verbs re-anchor.
    """

    @staticmethod
    async def _superseded_chain(ledger: TaskLedger, length: int, tag: str) -> list[str]:
        """``length`` rows, each (but the last) raw-stamped ``superseded_by`` the next — a chain whose
        HEAD is the last element.  Raw: a pre-58 world the verbs can no longer produce."""
        ids = [f"{tag}{index:02d}chain0000000000000000000" for index in range(length)]
        for index, task_id in reversed(list(enumerate(ids))):
            nxt = ids[index + 1] if index + 1 < length else None
            await raw_seed_row(ledger, task_id, blocked_by=[], superseded_by=nxt)
        return ids

    @staticmethod
    async def _boot(env: SurrealEnv, caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
        booted = new_ledger(env)
        caplog.clear()
        try:
            with caplog.at_level(logging.DEBUG):
                await booted.ensure_ready()
        finally:
            await booted.close()
        return [r for r in caplog.records if r.getMessage() == HEAL_EVENT]

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_boot_heals_every_straggler_to_its_successor_and_COUNTS_them(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger, env = ledger58
        chain_a = await self._superseded_chain(ledger, 2, "ha")
        chain_b = await self._superseded_chain(ledger, 2, "hb")
        stragglers = {"y1": chain_a[0], "y2": chain_b[0], "y3": chain_b[0]}
        for label, blocker in stragglers.items():
            task_id = f"straggler{label}000000000000000000000"
            await raw_seed_row(ledger, task_id, blocked_by=[blocker])
            await raw_relate(ledger, blocker, task_id)
        records = await self._boot(env, caplog)
        for label, blocker in stragglers.items():
            task_id = f"straggler{label}000000000000000000000"
            head = chain_a[-1] if blocker == chain_a[0] else chain_b[-1]
            assert await column(ledger, task_id) == [head], label
            notes = [e for e in await events_of(ledger, task_id) if e.get("action") == ACTION_REANCHORED]
            assert len(notes) == 1, notes
            assert notes[0].get("actor") == HEAL_ACTOR and notes[0].get("reason") == HEAL_REASON, notes
            assert notes[0].get("from") == blocker and notes[0].get("to") == head, notes
        await assert_edge_mirrors_column_for_every_row(ledger, where="after the boot heal")
        assert len(records) == 1 and getattr(records[0], "count", None) == len(stragglers), (
            f"the heal must log ONE {HEAL_EVENT} carrying count={len(stragglers)} (three stragglers over "
            f"TWO chains — a count of chains or of blockers is a different number): "
            f"{[(r.getMessage(), getattr(r, 'count', None)) for r in records]}"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_second_boot_changes_NOTHING_and_is_SILENT(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger, env = ledger58
        chain = await self._superseded_chain(ledger, 2, "hi")
        await raw_seed_row(ledger, "stragglerid0000000000000000000", blocked_by=[chain[0]])
        await raw_relate(ledger, chain[0], "stragglerid0000000000000000000")
        await self._boot(env, caplog)
        before = await snapshot(ledger)
        records = await self._boot(env, caplog)
        assert await snapshot(ledger) == before and not records, (
            "the heal is not idempotent: a second boot wrote or logged again"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_three_hop_chain_reanchors_to_the_HEAD(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger, env = ledger58
        chain = await self._superseded_chain(ledger, 3, "h3")
        await raw_seed_row(ledger, "straggler3hop00000000000000000", blocked_by=[chain[0]])
        await raw_relate(ledger, chain[0], "straggler3hop00000000000000000")
        await self._boot(env, caplog)
        assert await column(ledger, "straggler3hop00000000000000000") == [chain[-1]], (
            "a straggler must follow superseded_by to the chain HEAD, not stop at the first successor "
            "(which is itself superseded — a second strand)"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_DONE_head_frees_the_straggler(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Amendment 1: *"a straggler whose X' is ITSELF superseded but whose head is done → re-anchored to
        the head (and, per FORK-A, its claimability follows the head's status)"*."""
        ledger, env = ledger58
        chain = await self._superseded_chain(ledger, 3, "hd")
        await raw_force(ledger, chain[-1], status=STATUS_DONE)
        straggler = "stragglerdone00000000000000000"
        await raw_seed_row(ledger, straggler, blocked_by=[chain[0]])
        await raw_relate(ledger, chain[0], straggler)
        assert not (await ledger.claim_task(straggler, CLAIMANT)).claimed, "fixture: stranded before boot"
        await self._boot(env, caplog)
        assert await column(ledger, straggler) == [chain[-1]]
        assert (await ledger.claim_task(straggler, CLAIMANT)).claimed, (
            "after the heal the straggler waits only on a DONE head — it must be claimable"
        )


class TestRequiredGreen:
    """Builds prior rulings require GREEN (63c amendment 14's lesson) — each reddens a build that
    regresses them while "adding" the re-anchor.  GREEN at HEAD except where the re-anchor is asserted."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_ZERO_dependents_reanchors_nothing(self, ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
        ledger, _env = ledger58
        live = await create(ledger, "a live blocker")
        old = await create(ledger, "X with one blocker and no dependents", [live])
        edges_before = await edge_pairs(ledger)
        result = await supersede(ledger, old)
        successor = successor_of(result)
        assert list(result.reanchored) == []
        assert sorted(await edge_pairs(ledger)) == sorted([*edges_before, (live, successor)]), (
            "a zero-dependent supersede must add exactly the successor's #174 edge and touch nothing else"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    @pytest.mark.parametrize("sentinel", ["inherit", "clear", "replace"])
    async def test_the_174_sentinel_still_resolves_the_SUCCESSOR_while_dependents_are_rewired(
        self, ledger58: tuple[TaskLedger, SurrealEnv], sentinel: str
    ) -> None:
        ledger, _env = ledger58
        inherited = await create(ledger, "X's own blocker")
        replacement = await create(ledger, "a replacement blocker")
        old = await create(ledger, "X", [inherited])
        dependent = await create(ledger, "Y", [old])
        kwargs: dict[str, Any] = {}
        want: list[str] = [inherited]
        if sentinel == "clear":
            kwargs, want = {"blocked_by": []}, []
        elif sentinel == "replace":
            kwargs, want = {"blocked_by": [replacement]}, [replacement]
        successor = successor_of(await supersede(ledger, old, **kwargs))
        assert (await ledger.get_task(successor)).blocked_by == want
        assert await column(ledger, dependent) == [successor]
        await assert_edge_mirrors_column_for_every_row(ledger, where=f"#174 {sentinel}")

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_DOUBLE_supersede_race_reanchors_EXACTLY_ONCE_to_the_WINNER(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """The loser's WHOLE transaction rolls back — its re-anchors included (no second note, no
        second edge, no dependent pointing at a successor that was never minted)."""
        import asyncio

        ledger, env = ledger58
        old = await create(ledger, "X")
        dependents = [await create(ledger, f"Y{i}", [old]) for i in range(3)]
        racers = [new_ledger(env) for _ in range(4)]
        try:
            outcomes = await asyncio.gather(
                *(supersede(racer, old) for racer in racers), return_exceptions=True
            )
        finally:
            for racer in racers:
                await racer.close()
        winners = [o for o in outcomes if not isinstance(o, BaseException)]
        losers = [o for o in outcomes if isinstance(o, BaseException)]
        assert len(winners) == 1, f"exactly one supersede may win: {outcomes}"
        assert all(isinstance(o, IllegalTransitionError) for o in losers), losers
        successor = successor_of(winners[0])
        for task_id in dependents:
            assert await column(ledger, task_id) == [successor]
            notes = [e for e in await events_of(ledger, task_id) if e.get("action") == ACTION_REANCHORED]
            assert len(notes) == 1 and notes[0]["to"] == successor, notes
        await assert_edge_mirrors_column_for_every_row(ledger, where="after a 4-way supersede race")

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_loser_that_PASSED_its_pre_read_rolls_back_WHOLE_via_the_in_txn_CAS(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """⛔ Added after mutation M1 (``REPORT-contract-58.md`` §MUTATION): with the shell's THROW
        disabled, the 4-way gather race above stayed GREEN — its losers lose at the SEQUENTIAL pre-read
        (``superseded_by is not None``), so the in-transaction stamp CAS was never exercised.  Constructed
        here: the winner's WHOLE supersede commits between the loser's pre-reads and the loser's
        transaction (at the ONE ``_apply`` seam).  The loser must be refused as already-superseded, and
        its transaction must leave NOTHING — no second successor, no second note, no second edge."""
        ledger, env = ledger58
        old = await create(ledger, "X")
        dependents = [await create(ledger, f"Y{i}", [old]) for i in range(3)]
        rows_before = await row_count(ledger)
        racer = new_ledger(env)
        won: list[str] = []

        async def _winner_commits_first() -> None:
            won.append(successor_of(await supersede(racer, old)))

        hook = ApplyHook(ledger, _winner_commits_first)
        try:
            with hook.installed():
                with pytest.raises(IllegalTransitionError):
                    await supersede(ledger, old)
        finally:
            await racer.close()
        assert hook.fired and won, "the constructed interleaving never ran"
        assert await row_count(ledger) == rows_before + 1, "the loser minted a second successor"
        for task_id in dependents:
            assert await column(ledger, task_id) == [won[0]]
            notes = [e for e in await events_of(ledger, task_id) if e.get("action") == ACTION_REANCHORED]
            assert len(notes) == 1 and notes[0]["to"] == won[0], notes
        await assert_edge_mirrors_column_for_every_row(ledger, where="after a pre-read-passing loser")

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_superseded_X_still_does_not_UNBLOCK_its_dependents(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """R10's rejected reading stays rejected: the work MOVED, so the dependent now waits on the
        OPEN successor — not claimable, and not served as claimable."""
        ledger, _env = ledger58
        old = await create(ledger, "X")
        dependent = await create(ledger, "Y", [old])
        await supersede(ledger, old)
        assert not (await ledger.claim_task(dependent, CLAIMANT)).claimed
        assert dependent not in {t.id for t in await ledger.query_tasks(blocked=False)}


class TestSupersedeOfATerminalPredecessorA1:
    """RED at HEAD.  Amendment 1 FORK-A = **A1** (``docs/design/2026-09-26-packet58-amendment-1.md``):
    a ``done``/``wontfix`` X re-anchors ∀ dependents to the OPEN X' — no status branch.  X is DONE here,
    so its dependents reach EVERY status through the public verbs (including ``claimed``).

    Leg-1 rider: the consequence is SERVED — ``SupersedeResult.reblocked`` is the subset of re-anchored
    dependents that were CLAIMABLE before (``open``, unowned, every OTHER blocker terminal), derived from
    the ledger's PRE-write read; a ``claimed``/``in_progress`` dependent keeps working (``blocked_by``
    gates CLAIMS only).
    """

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_reblocked_names_exactly_the_previously_CLAIMABLE_dependents(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        old = await create(ledger, "X, finished")
        await drive_to(ledger, old, STATUS_DONE)
        finished_other = await create(ledger, "another finished blocker")
        await drive_to(ledger, finished_other, STATUS_DONE)
        open_other = await create(ledger, "an OPEN other blocker")
        claimable = await create(ledger, "Y: open, unowned, only blocker X is done", [old])
        claimable_two = await create(ledger, "Y2: open, X + a DONE other", [old, finished_other])
        not_claimable = await create(
            ledger, "W: open but ALSO waits on an open row", [old, open_other]
        )
        held = await create(ledger, "Z: claimed before the supersede", [old])
        await drive_to(ledger, held, STATUS_CLAIMED)
        # V: an OPEN, unowned dependent that was itself SUPERSEDED — never claimable (the CAS refuses
        # a superseded row), so it must NOT be served as re-blocked; its #174 successor V' INHERITED
        # [X] and IS claimable before, so it MUST be (a build reusing the partition without the
        # dependent's own superseded_by check gets exactly one of these two wrong).
        reframed = await create(ledger, "V: reframed while X was done", [old])
        reframed_successor = successor_of(await supersede(ledger, reframed))
        held_status_before = (await ledger.get_task(held)).status
        result = await supersede(ledger, old)
        successor = successor_of(result)
        assert sorted(result.reblocked) == sorted([claimable, claimable_two, reframed_successor]), (
            f"reblocked={sorted(result.reblocked)}: must be EXACTLY the dependents that were claimable "
            f"before (open, unowned, NOT superseded, every other blocker terminal) — Y, Y2 and V' — not "
            f"W (already blocked on an open row), not Z (claimed; blocked_by gates claims only), not V "
            f"(itself superseded)"
        )
        assert reframed in result.reanchored and reframed not in result.reblocked
        assert set(result.reblocked) <= set(result.reanchored)
        assert not_claimable in result.reanchored and not_claimable not in result.reblocked
        unblocked = {t.id for t in await ledger.query_tasks(blocked=False)}
        assert claimable not in unblocked and claimable_two not in unblocked
        loss = await ledger.claim_task(claimable, CLAIMANT)
        assert not loss.claimed and successor in loss.task.blocked_by
        assert (await ledger.get_task(held)).status == held_status_before, "Z's status must be untouched"

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_an_OPEN_predecessor_reblocks_NOTHING(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """No dependent of an OPEN X was claimable, so ``reblocked`` is empty (the render's K line is
        absent — byte-identical to the plain re-anchor render; held patch)."""
        ledger, _env = ledger58
        old = await create(ledger, "X, open")
        await create(ledger, "Y", [old])
        result = await supersede(ledger, old)
        assert list(result.reblocked) == [] and len(result.reanchored) == 1

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_every_status_is_rewired_including_claimed(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        old = await create(ledger, "X, finished")
        await drive_to(ledger, old, STATUS_DONE)
        dependents = {}
        for status in (STATUS_OPEN, STATUS_CLAIMED, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_WONTFIX):
            task_id = await create(ledger, f"dependent {status}", [old])
            await drive_to(ledger, task_id, status)
            dependents[status] = task_id
        successor = successor_of(await supersede(ledger, old))
        for status, task_id in dependents.items():
            assert await column(ledger, task_id) == [successor], status
        await assert_edge_mirrors_column_for_every_row(ledger, where="terminal X")
        assert not (await ledger.claim_task(dependents[STATUS_OPEN], CLAIMANT)).claimed, (
            "A1: the open dependent now waits on the OPEN successor"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_claim_whose_PRE_READ_predates_the_reanchor_can_NOT_win(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """⛔ 58 BREAKS an invariant the claim path states it leans on: *"``blocked_by`` never changes
        after creation, so reading it here is consistent"* (``TaskLedger.claim_task``; echoed in
        ``direct_dependents``'s docstring).  The claim CAS resolves blockers from the PRE-READ list and
        compares COUNTS.  Construct: Y's blocker X is DONE (Y claimable); the claim pre-reads [X]; a
        supersede re-anchors Y to the OPEN X' BEFORE the claim's transaction; the stale list resolves
        [X] → 1 == len([X']) → the claim WINS a task whose only blocker is open.  Any correct build
        (resolve in-transaction, or CAS on the column) loses here."""
        ledger, env = ledger58
        old = await create(ledger, "X, finished")
        await drive_to(ledger, old, STATUS_DONE)
        dependent = await create(ledger, "Y, claimable while X is done", [old])
        racer = new_ledger(env)

        async def _concurrent_supersede() -> None:
            await supersede(racer, old)

        hook = ApplyHook(ledger, _concurrent_supersede)
        try:
            with hook.installed():
                result = await ledger.claim_task(dependent, CLAIMANT)
        finally:
            await racer.close()
        assert hook.fired, "the constructed interleaving never ran"
        current = await column(ledger, dependent)
        assert old not in current, "fixture: the supersede did not re-anchor Y"
        assert not result.claimed and (await ledger.get_task(dependent)).owner is None, (
            f"the claim WON task {dependent} whose only blocker is now the OPEN successor "
            f"({current}) — its eligibility was decided on a blocked_by list read BEFORE the "
            f"re-anchor. 58 makes blocked_by MUTABLE; the claim CAS must decide on the column it "
            f"writes against"
        )
