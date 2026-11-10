"""Packet 58 fix-wave contract — amendment 17 §12 (cold-audit F1, #623), §12.8 item 1, #626, §12.7, #625,
#130(a).

*Every claim in this file is scoped to the tree at ``380414c`` (branch ``feat/surreal-unification``,
production identical to the graded build ``aa4ea04``), 2026-11-10, authored by ``contract-58-r53``. "RED at
HEAD" means RED on that tree.*

* **Property P (§12.2).** After a boot heal, no row the heal wrote lies on a ``blocked_by`` cycle. A straggler
  whose re-anchor would close one (alone, jointly with another straggler, or by joining a legacy loop) is
  SKIPPED WHOLE — column, edges and ``updated_at`` byte-identical, not counted — and recorded EVERY boot as
  the WARNING ``task.backfill.straggler_would_close_cycle`` (``database``, ``task_id``, ``blocker_ids``,
  ``cycle``, ``members``). Legs A, B and C of §12.4; leg B uses a two-supersession chain (X1 → X1′ → H1), so
  the cycle closes at the chain HEAD.
* **Leg D (§12.8 item 1).** A legacy ``blocked_by`` loop with no missing edge is recorded on EVERY boot
  (``task.backfill.legacy_cycle_minted``), not only on a boot that has edges to mint.
* **OB3 (#626).** A supersede removes EVERY ``blocks`` edge out of the superseded task, including a drift edge
  to a row whose column does not name it (am-17 §9.2's removed-behaviour inventory, first row).
* **Served text.** F5 (§12.7): the claim loss on a superseded blocker serves "can never resolve: block on the
  successor instead" and no longer "can never win". #130(a): the served ``lore_tasks`` schema's ``status``
  description names the superseded-row exclusion. (#625 a/b ride the legs that already raise those errors:
  ``test_reanchor_58_r3_convergence.py``'s over-weight row and ``test_supersede_reanchor_58.py``'s cap+1 hub.)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from _reanchor_58_support import (
    CREATOR,
    DESCRIPTION,
    HEAL_EVENT,
    all_columns,
    boot,
    bulk_seed_dependents,
    column,
    create,
    edge_pairs,
    ledger58,
    measure_heal_shape,
    raw,
    raw_force,
    raw_relate,
    raw_seed_row,
    snapshot,
    supersede,
    updated_at_of,
)
from _surreal_harness import SurrealEnv
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import TaskCycleError, TaskLedger, find_blocked_by_cycle
from surrealdb import RecordID
from test_blocks_edge import ACTOR
from test_query_tasks_bounded import _tool_seam

__all__ = ["ledger58"]  # the imported fixture, used by name

#: §12.2's ruled record for a straggler the heal skips because its re-anchor would close a cycle.
WOULD_CLOSE_CYCLE_EVENT = "task.backfill.straggler_would_close_cycle"
#: The backfill's existing legacy-loop record (§12.8 item 1: "legacy_cycle_minted or its existing record").
LEGACY_CYCLE_EVENT = "task.backfill.legacy_cycle_minted"
#: §12.7 F5: the ruled form of the claim-loss reason, and the retired over-claim.
F5_RULED_TAIL = "can never resolve: block on the successor instead"
F5_RETIRED = "can never win"


def _tid(tag: str) -> str:
    """A 32-character task id in the house shape (letters and digits, letter-led)."""
    return f"fw{tag}".ljust(32, "0")[:32]


def _records(caplog: pytest.LogCaptureFixture, event: str) -> list[logging.LogRecord]:
    return [record for record in caplog.records if record.getMessage() == event]


async def _boot_logged(env: SurrealEnv, caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    """ONE boot with every record captured (fresh capture per boot)."""
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await boot(env)
    return list(caplog.records)


async def _seed(ledger: TaskLedger, task_id: str, blocked_by: list[str], **kwargs: Any) -> str:
    """One raw row plus the ``blocks`` edges its column implies (a mirror-consistent legacy row)."""
    await raw_seed_row(ledger, task_id, blocked_by=blocked_by, **kwargs)
    for blocker in blocked_by:
        await raw_relate(ledger, blocker, task_id)
    return task_id


async def _row_state(ledger: TaskLedger, task_id: str) -> tuple[list[str], list[tuple[str, str]], Any]:
    """A row's column, every edge that touches it, and its ``updated_at`` — "byte-identical" means all
    three."""
    edges = [pair for pair in await edge_pairs(ledger) if task_id in pair]
    return await column(ledger, task_id), edges, await updated_at_of(ledger, task_id)


def _assert_one_skip_record(
    records: list[logging.LogRecord],
    *,
    task_id: str,
    blocker_ids: set[str],
    must_include: set[str],
    where: str,
) -> None:
    """Exactly one §12.2 WARNING for ``task_id``, carrying the ruled extras."""
    mine = [
        r
        for r in records
        if r.getMessage() == WOULD_CLOSE_CYCLE_EVENT and getattr(r, "task_id", None) == task_id
    ]
    assert len(mine) == 1, (
        f"{where}: expected exactly ONE {WOULD_CLOSE_CYCLE_EVENT} WARNING naming {task_id}, got "
        f"{[(r.getMessage(), getattr(r, 'task_id', None)) for r in records if r.levelno >= logging.WARNING]}"
    )
    record = mine[0]
    assert record.levelno == logging.WARNING, f"{where}: the skip record is {record.levelname}, not WARNING"
    assert getattr(record, "database", None), f"{where}: the skip record carries no database"
    assert set(getattr(record, "blocker_ids", None) or ()) == blocker_ids, (
        f"{where}: blocker_ids must be the superseded blockers the row still names, {sorted(blocker_ids)}; "
        f"served {getattr(record, 'blocker_ids', None)!r}"
    )
    members = set(getattr(record, "members", None) or ())
    assert must_include <= members, f"{where}: members {sorted(members)} must include {sorted(must_include)}"
    cycle = getattr(record, "cycle", None)
    assert isinstance(cycle, str) and " -> " in cycle and task_id in cycle, (
        f"{where}: cycle must be the 'a -> b -> …' string naming the row, served {cycle!r}"
    )


# =========================================================================== # §12.4 legs A–C — property P:
# the heal never writes a row onto a blocked_by cycle
# =========================================================================== #


class TestTheHealNeverWritesARowOntoACycle:
    """am-17 §12.2 / §12.4. RED at HEAD: the heal re-anchors without the write path's cycle predicate."""

    async def test_A_a_straggler_whose_reanchor_closes_a_cycle_is_skipped_WHOLE_and_recorded_every_boot(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Leg A, the audit's world plus two riders: X superseded by H with no re-anchor; H ``blocked_by
        [D]``; D ``blocked_by [X, X2]`` with X2 superseded by a healthy H2; one unrelated healthy straggler S.

        Kills: no check (D healed to [H, H2], a cycle written); check-then-write-anyway; a raise (boot
        denial); a silent skip (no WARNING); a partial re-anchor (X2 moved to H2); a record only on the first
        boot."""
        ledger, env = ledger58
        head = await create(ledger, "fw-A head H")
        head2 = await create(ledger, "fw-A healthy head H2")
        x, x2 = _tid("aX"), _tid("aX2")
        await raw_seed_row(ledger, x, blocked_by=[], superseded_by=head)
        await raw_seed_row(ledger, x2, blocked_by=[], superseded_by=head2)
        d = await _seed(ledger, _tid("aD"), [x, x2])
        # H waits on D: re-anchoring D's X to H would write D -> H -> D.
        await raw_force(ledger, head, blocked_by=[d])
        await raw_relate(ledger, d, head)
        s_head = await create(ledger, "fw-A S's head")
        xs = _tid("aXS")
        await raw_seed_row(ledger, xs, blocked_by=[], superseded_by=s_head)
        s = await _seed(ledger, _tid("aS"), [xs])
        d_before = await _row_state(ledger, d)

        records = await _boot_logged(env, caplog)  # completes: a raise here is the boot-denial build
        heal = _records(caplog, HEAL_EVENT)
        assert len(heal) == 1 and getattr(heal[0], "count", None) == 1, (
            f"the unrelated straggler S must heal and be the ONLY row counted: "
            f"{[(getattr(r, 'count', None), getattr(r, 'chunks', None)) for r in heal]}"
        )
        assert await column(ledger, s) == [s_head], "S, the healthy straggler, was not healed"
        assert await _row_state(ledger, d) == d_before, (
            f"D must be byte-identical (column, edges, updated_at): before {d_before}, after "
            f"{await _row_state(ledger, d)} — a re-anchor (full or partial: X2 moved) or a stamp"
        )
        assert find_blocked_by_cycle(await all_columns(ledger)) is None, (
            f"a blocked_by cycle exists after the heal: {find_blocked_by_cycle(await all_columns(ledger))}"
        )
        _assert_one_skip_record(
            records, task_id=d, blocker_ids={x, x2}, must_include={d, head}, where="boot 1"
        )
        assert not _records(caplog, "task.backfill.legacy_cycle_minted"), (
            "no cycle exists in the store, so no legacy-loop record may fire (§12.2)"
        )

        records = await _boot_logged(env, caplog)
        _assert_one_skip_record(
            records, task_id=d, blocker_ids={x, x2}, must_include={d, head}, where="boot 2"
        )
        assert await _row_state(ledger, d) == d_before, "boot 2 changed D"

        # CONTROL 1 — the same shape built fresh through the LIVE verbs is refused by the write path.
        x_live = await create(ledger, "fw-A live X")
        d_live = await create(ledger, "fw-A live D", blocked_by=[x_live])
        with pytest.raises(TaskCycleError):
            await supersede(ledger, x_live, blocked_by=[d_live])

        # CONTROL 2 — remove D from H's blocked_by by hand: the next boot heals D to [H, H2] with no WARNING,
        # so the skip above was the cycle's doing, not a fixture that can never heal.
        await raw_force(ledger, head, blocked_by=[])
        await raw(
            ledger,
            f"DELETE {BLOCKS_RELATION} WHERE in = $d AND out = $h",
            {"d": RecordID(TASK_TABLE, d), "h": RecordID(TASK_TABLE, head)},
        )
        records = await _boot_logged(env, caplog)
        assert await column(ledger, d) == [head, head2], (
            f"control: with the loop broken D must heal to [H, H2], got {await column(ledger, d)}"
        )
        assert not _records(caplog, WOULD_CLOSE_CYCLE_EVENT), (
            "control: a WARNING fired with no cycle to close"
        )

    async def test_B_two_stragglers_that_close_a_cycle_JOINTLY_are_both_skipped(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Leg B, joint, through a two-supersession chain: D1 ``[X1]`` with X1 → X1′ → H1; D2 ``[X2]`` with
        X2 → H2; H1 ``blocked_by [D2]``; H2 ``blocked_by [D1]``. Neither row closes a cycle alone; together
        they write D1 → H1 → D2 → H2 → D1, closing at the chain HEAD H1 (not at X1′).

        Kills a row-by-row check (heals both: the cycle is written) and a check that stops at the first
        successor (X1′ waits on nothing)."""
        ledger, env = ledger58
        h1 = await create(ledger, "fw-B chain head H1")
        h2 = await create(ledger, "fw-B head H2")
        x1, x1_mid, x2 = _tid("bX1"), _tid("bX1p"), _tid("bX2")
        await raw_seed_row(ledger, x1_mid, blocked_by=[], superseded_by=h1)
        await raw_seed_row(ledger, x1, blocked_by=[], superseded_by=x1_mid)
        await raw_seed_row(ledger, x2, blocked_by=[], superseded_by=h2)
        d1 = await _seed(ledger, _tid("bD1"), [x1])
        d2 = await _seed(ledger, _tid("bD2"), [x2])
        await raw_force(ledger, h1, blocked_by=[d2])
        await raw_relate(ledger, d2, h1)
        await raw_force(ledger, h2, blocked_by=[d1])
        await raw_relate(ledger, d1, h2)
        before = {row: await _row_state(ledger, row) for row in (d1, d2)}

        records = await _boot_logged(env, caplog)
        assert find_blocked_by_cycle(await all_columns(ledger)) is None, (
            f"the heal wrote a cycle: {find_blocked_by_cycle(await all_columns(ledger))}"
        )
        for row in (d1, d2):
            assert await _row_state(ledger, row) == before[row], (
                f"{row} changed: {await _row_state(ledger, row)}"
            )
        _assert_one_skip_record(
            records, task_id=d1, blocker_ids={x1}, must_include={d1, h1, d2, h2}, where="D1"
        )
        _assert_one_skip_record(
            records, task_id=d2, blocker_ids={x2}, must_include={d1, h1, d2, h2}, where="D2"
        )
        healed = [getattr(r, "count", 0) for r in _records(caplog, HEAL_EVENT)]
        assert sum(healed) == 0, f"a skipped row was counted as healed: {healed}"

    async def test_C_a_straggler_already_on_a_LEGACY_loop_is_skipped_stricter_than_the_live_supersede(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Leg C: D ``blocked_by [X, Z]``, Z ``blocked_by [D]`` (a legacy loop), X superseded by a healthy
        H. The heal skips D and records it, although am-3 §4 lets a LIVE supersede re-anchor such a row
        (§12.2: the heal's refusal is per row, so am-3 §4's reason does not apply).

        Kills a build that copies am-3 §4's ``minted`` choice (only the successor counts as minted, so the
        legacy loop is stepped over and D is healed to [H, Z])."""
        ledger, env = ledger58
        head = await create(ledger, "fw-C healthy head H")
        x, z, d = _tid("cX"), _tid("cZ"), _tid("cD")
        await raw_seed_row(ledger, x, blocked_by=[], superseded_by=head)
        # rows first, edges after: `blocks` is ENFORCED, so an edge to a not-yet-existing row is refused
        await raw_seed_row(ledger, d, blocked_by=[x, z])
        await raw_seed_row(ledger, z, blocked_by=[d])
        for blocker, blocked in ((x, d), (z, d), (d, z)):
            await raw_relate(ledger, blocker, blocked)
        before = await _row_state(ledger, d)

        records = await _boot_logged(env, caplog)
        assert await _row_state(ledger, d) == before, (
            f"D was re-anchored onto its legacy loop: {await column(ledger, d)}"
        )
        _assert_one_skip_record(records, task_id=d, blocker_ids={x}, must_include={d, z}, where="leg C")
        healed = [getattr(r, "count", 0) for r in _records(caplog, HEAL_EVENT)]
        assert sum(healed) == 0, f"D was counted as healed: {healed}"


# =========================================================================== # §12.8 item 1, leg D — a legacy
# loop is recorded on EVERY boot =========================================================================== #


class TestALegacyLoopIsRecordedEveryBoot:
    """am-17 §12.8 item 1. RED at HEAD: ``_backfill_blocks_edges`` returns before ``_record_legacy_cycles``
    when no edge is missing, so a mirror-consistent legacy loop is never recorded."""

    async def test_D_a_legacy_loop_with_NO_missing_edge_is_recorded_on_every_boot_and_nothing_changes(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        """A ``blocked_by [B]``, B ``blocked_by [A]``, both edges present. Two boots: each records the loop
        once, naming both members; the store is unchanged.

        Kills the early-return build (HEAD) and a record-once build (a 'have I recorded' flag)."""
        ledger, env = ledger58
        a, b = _tid("dA"), _tid("dB")
        await raw_seed_row(ledger, a, blocked_by=[b])
        await raw_seed_row(ledger, b, blocked_by=[a])
        await raw_relate(ledger, b, a)
        await raw_relate(ledger, a, b)
        before = await snapshot(ledger)
        for boot_number in (1, 2):
            await _boot_logged(env, caplog)
            loops = [
                r
                for r in _records(caplog, LEGACY_CYCLE_EVENT)
                if {a, b} <= set(getattr(r, "members", ()) or ())
            ]
            assert len(loops) == 1, (
                f"boot {boot_number}: the legacy loop {a} <-> {b} must be recorded exactly once per boot; "
                f"saw {[getattr(r, 'members', None) for r in _records(caplog, LEGACY_CYCLE_EVENT)]}"
            )
            assert loops[0].levelno == logging.WARNING
            assert await snapshot(ledger) == before, f"boot {boot_number} changed the store"


# =========================================================================== # #626 (cold audit probes F1,
# OB3) — every edge OUT of the superseded task goes, drift edges included
# =========================================================================== #


class TestTheSupersedeRemovesEveryOutEdgeOfTheOldTask:
    """am-17 §9.2's removed-behaviour inventory, row 1 ("deletes every edge whose ``in`` is the old task"),
    pinned in a world that is NOT mirror-consistent. GREEN at HEAD (the built DELETE is ``$old->blocks``); it
    is the missing pin #626 names, so it carries no RED."""

    async def test_a_DRIFT_edge_out_of_the_hub_is_deleted_with_the_dependents_edges(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """A hub with 3 dependents, one blocker of its own, and a drift edge hub → E where E's column does not
        name the hub. After the supersede: no edge leaves the hub; the edge INTO the hub survives; E's column
        is untouched and E is not reported as re-anchored.

        Kills OB3 (``DELETE … WHERE out INSIDE $dependents_read`` leaves the drift edge) and a DELETE over
        both directions (the blocker's edge into the hub goes too)."""
        ledger, _env = ledger58
        blocker = await create(ledger, "fw-OB3 the hub's own blocker")
        hub = await create(ledger, "fw-OB3 hub", blocked_by=[blocker])
        dependents = await bulk_seed_dependents(ledger, hub, 3, tag="fwob3d")
        drift = await create(ledger, "fw-OB3 drift target E")
        await raw_relate(ledger, hub, drift)  # an out-edge with no matching blocked_by entry
        assert (hub, drift) in await edge_pairs(ledger), "non-vacuity: the drift edge was not seeded"

        result = await supersede(ledger, hub)
        out_of_hub = [pair for pair in await edge_pairs(ledger) if pair[0] == hub]
        assert out_of_hub == [], (
            f"edges still leave the superseded hub {hub}: {out_of_hub} — the supersede deleted only the "
            f"edges to "
            f"the dependents it read (OB3)"
        )
        assert (blocker, hub) in await edge_pairs(ledger), "the edge INTO the hub must survive"
        assert await column(ledger, drift) == [], "the drift target's column was touched"
        assert drift not in getattr(result, "reanchored", []), "the drift target is not a dependent"
        assert sorted(getattr(result, "reanchored", [])) == sorted(dependents)


# =========================================================================== # Served text — F5 (§12.7) and
# #130(a) =========================================================================== #


class TestTheServedTextSaysWhatIsTrue:
    """am-17 §12.7. RED at HEAD: the claim render says "can never win"; the ``status`` description does not
    name the superseded-row exclusion."""

    async def test_F5_a_claim_lost_to_a_superseded_blocker_says_can_never_resolve_not_can_never_win(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """The legacy strand (raw: the blocker superseded after the dependent existed), claimed through the
        ``lore_tasks`` dispatcher. "Can never win" is false: the next boot heal re-anchors the row."""
        ledger, _env = ledger58
        successor = await create(ledger, "fw-F5 where the work went")
        blocker = _tid("f5blocker")
        await raw_seed_row(ledger, blocker, blocked_by=[], superseded_by=successor)
        dependent = await _seed(ledger, _tid("f5dependent"), [blocker])
        rendered = str(await _tool_seam(ledger).claim_task(dependent, ACTOR))
        assert blocker in rendered and successor in rendered, (
            f"the loss must name the blocker and successor: {rendered!r}"
        )
        assert F5_RULED_TAIL in rendered, f"the ruled form {F5_RULED_TAIL!r} is not served: {rendered!r}"
        assert F5_RETIRED not in rendered, (
            f"the retired over-claim {F5_RETIRED!r} is still served: {rendered!r}"
        )

    async def test_130a_the_served_status_field_names_the_superseded_row_exclusion(
        self, tmp_path: Path
    ) -> None:
        """#130 shape (a), through the served MCP tool schema (what an agent reads), never the source."""
        from loremaster.server import LoreServer, build_mcp_server
        from test_mcp_server import _config, _slug

        mcp = build_mcp_server(LoreServer(_config(_slug(), tmp_path / "live")))
        tools = {tool.name: tool for tool in await mcp.list_tools()}
        description = str(tools["lore_tasks"].parameters["properties"]["status"].get("description", ""))
        lowered = description.lower()
        assert "superseded" in lowered and "exclud" in lowered, (
            f"the served lore_tasks `status` description does not say superseded rows are excluded from the "
            f"filter: {description!r}"
        )


# =========================================================================== # am-17 §13 (#631) — the cycle
# predicate is EXACT (MP-1) and the heal's fate is ONE pass over stored ∪ proposed (D2)
# =========================================================================== #


def _reaches(columns: dict[str, list[str]], start: str, target: str) -> bool:
    """Ground-truth reachability over the ``blocked_by`` columns (``node -> its blockers``): can ``start``'s
    blockers lead back to ``target``? Deliberately NOT ``find_blocked_by_cycle``, whose first answer in these
    worlds is the legacy loop, not the cycle through the row (am-17 §13.5 item 1)."""
    seen: set[str] = set()
    stack = list(columns.get(start, ()))
    while stack:
        node = stack.pop()
        if node == target:
            return True
        if node in seen:
            continue
        seen.add(node)
        stack.extend(columns.get(node, ()))
    return False


async def _seed_world(ledger: TaskLedger, rows: dict[str, list[str]], superseded: dict[str, str]) -> None:
    """Raw rows first, then every edge their columns imply (``blocks`` is ENFORCED: an edge to a row that
    does not exist yet is refused). ``superseded`` maps an id to its ``superseded_by``."""
    for task_id, blocked_by in rows.items():
        await raw_seed_row(ledger, task_id, blocked_by=blocked_by, superseded_by=superseded.get(task_id))
    for task_id, blocked_by in rows.items():
        for blocker in blocked_by:
            await raw_relate(ledger, blocker, task_id)


class TestTheCyclePredicateIsExact:
    """am-17 §13.5 item 1, MP-1 as adversary-58-fw1 wrote it: a cycle through the asked row that SHARES an
    edge with a legacy loop whose ids sort first. RED at HEAD: the heal checks nothing, and the live
    supersede's step-over drops the shared edge and misses the cycle (#631)."""

    @pytest.mark.parametrize("order", ["legacy_ids_sort_first", "control_dependent_sorts_first"])
    async def test_E1_the_heal_never_writes_a_cycle_that_shares_an_edge_with_a_legacy_loop(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture, order: str
    ) -> None:
        """E1: X superseded by H; H ``[L1]``; L1 ``[L2]``; L2 ``[L1, D]``; D ``[X]``. Re-anchoring D writes
        D -> H -> L1 -> L2 -> D, which shares L1 -> L2 with the legacy loop L1 <-> L2. After the boot D is
        unchanged and recorded, and D is on no cycle (reachability). The control orders the ids so the
        dependent sorts first (the shape an edge-dropping predicate happens to get right).

        Kills: no check (HEAD); the step-over predicate (#631: it drops L1 -> L2 and misses the cycle when the
        legacy ids sort first); a check against the stored graph only (no cycle there)."""
        ledger, env = ledger58
        if order == "legacy_ids_sort_first":
            l1, l2, h, x, d = _tid("e1a1"), _tid("e1b2"), _tid("e1h"), _tid("e1x"), _tid("e1d")
        else:
            l1, l2, h, x, d = _tid("e1l1"), _tid("e1l2"), _tid("e1h"), _tid("e1x"), _tid("e1d")
        await _seed_world(ledger, {h: [l1], x: [], l1: [l2], l2: [l1, d], d: [x]}, {x: h})
        before = await _row_state(ledger, d)
        records = await _boot_logged(env, caplog)
        columns = await all_columns(ledger)
        assert not _reaches(columns, d, d), (
            f"the heal wrote D onto a cycle: D={columns.get(d)}, columns={columns}"
        )
        assert await _row_state(ledger, d) == before, f"D must be unchanged: {await _row_state(ledger, d)}"
        _assert_one_skip_record(
            records, task_id=d, blocker_ids={x}, must_include={d, h}, where=f"E1[{order}]"
        )

    @pytest.mark.parametrize("legacy_loop", [True, False], ids=["with_legacy_loop", "control_no_legacy_loop"])
    async def test_E3_the_live_supersede_refuses_a_cycle_that_shares_an_edge_with_a_legacy_loop(
        self, ledger58: tuple[TaskLedger, SurrealEnv], legacy_loop: bool
    ) -> None:
        """E3 (the SECURITY DOOR: a caller reaches it through ``lore_tasks supersede``): R ``[X]``; L1
        ``[L2]``; L2 ``[L1, R]`` (legacy loop L1 <-> L2, ids sorting first). ``supersede(X, blocked_by=[L1])``
        re-anchors R to the successor S and closes S -> L1 -> L2 -> R -> S, sharing L1 -> L2 with the loop →
        ``TaskCycleError``, nothing written. The control drops the back edge L2 -> L1 (no legacy loop):
        refused at HEAD too.

        Kills the step-over predicate (#631, reproduced on 25cfd16: the supersede SUCCEEDS and writes the
        cycle)."""
        ledger, env = ledger58
        x = await create(ledger, "fw-E3 live X")
        l1, l2, r = "00e3l1".ljust(32, "0"), "00e3l2".ljust(32, "0"), "00e3r".ljust(32, "0")
        await _seed_world(ledger, {r: [x], l1: [l2], l2: [l1, r] if legacy_loop else [r]}, {})
        await boot(env)  # the backfill and heal settle first (nothing to heal: X is live)
        before = await snapshot(ledger)
        with pytest.raises(TaskCycleError):
            await supersede(ledger, x, blocked_by=[l1])
        assert await snapshot(ledger) == before, "a refused supersede wrote something"


class TestTheHealsFateIsOnePassOverStoredPlusProposed:
    """am-17 §13.4 / §13.5 item 2, D2: a pending row is skipped iff one of its post-rewrite blockers can
    reach it through the stored columns PLUS every pending row's post-rewrite column. One pass, so no id order
    matters, and a row may wait one boot for another to be healed. RED at HEAD: the heal checks nothing."""

    # One id assignment from each fate class the WITHDRAWN §12.2 loop splits this world into (adversary-58-fw1
    # restore_probe, re-run on HEAD's detector + step-over by `d2_fate_classes.py`, REPORT-contract-58-r53.md
    # §FIXWAVE-13): letters sort a < b < c < d, and both X ids sort after them.
    FATE_CLASS_ID_ORDERS = {
        "old_loop_skips_D1_only": {"d1": "a", "h1": "b", "d2": "c", "h2": "d"},
        "old_loop_skips_both": {"d1": "a", "h2": "b", "h1": "c", "d2": "d"},
    }

    @pytest.mark.parametrize("assignment", sorted(FATE_CLASS_ID_ORDERS))
    async def test_D2_i_both_rows_are_skipped_whatever_the_id_order(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture, assignment: str
    ) -> None:
        """D1 ``[X1→H1]``, H1 ``[D1, D2]``; D2 ``[X2→H2]``, H2 ``[D1]``. D1 alone closes D1 -> H1 -> D1; D2
        closes D2 -> H2 -> D1 -> H1 -> D2 only through D1's STORED-plus-proposed edges. Both rows are skipped
        and recorded, under both id assignments.

        Kills the minimal fate (heal D2 once D1 is skipped) and any order-dependent build (the withdrawn loop
        skips D1 only under one of these assignments)."""
        ledger, env = ledger58
        letters = self.FATE_CLASS_ID_ORDERS[assignment]
        d1, h1, d2, h2 = (_tid(f"q{letters[name]}") for name in ("d1", "h1", "d2", "h2"))
        x1, x2 = _tid("qx1"), _tid("qx2")
        await _seed_world(
            ledger, {h1: [d1, d2], h2: [d1], x1: [], x2: [], d1: [x1], d2: [x2]}, {x1: h1, x2: h2}
        )
        before = {row: await _row_state(ledger, row) for row in (d1, d2)}
        records = await _boot_logged(env, caplog)
        for row in (d1, d2):
            assert await _row_state(ledger, row) == before[row], f"{assignment}: {row} changed"
        columns = await all_columns(ledger)
        assert not _reaches(columns, d1, d1) and not _reaches(columns, d2, d2), (
            f"{assignment}: a cycle: {columns}"
        )
        _assert_one_skip_record(
            records, task_id=d1, blocker_ids={x1}, must_include={d1, h1}, where=f"{assignment} D1"
        )
        _assert_one_skip_record(
            records, task_id=d2, blocker_ids={x2}, must_include={d2, h2}, where=f"{assignment} D2"
        )

    async def test_D2_ii_a_row_whose_cycle_runs_through_another_stragglers_STORED_edge_waits_one_boot(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        """P ``[Xp→Hp]``, Hp ``[D]``; D ``[X→H]`` with X ``blocked_by [P]``; H clean. Boot 1: P's new
        blocker Hp reaches P through D's STORED edge D -> X -> P (D may not be written: its chunk can fail
        alone), so P is skipped and recorded; D is healed to ``[H]``. Boot 2: D's stored edge is now D -> H,
        nothing reaches P, so P is healed to ``[Hp]`` with no WARNING.

        Kills the overlay rules (with every pending row applied there is no cycle, so both heal on boot 1),
        and is the pin that stops someone "fixing" the one-boot wait (am-17 §13.4)."""
        ledger, env = ledger58
        p, xp, hp = _tid("pP"), _tid("pXp"), _tid("pHp")
        d, x, h = _tid("pD"), _tid("pX"), _tid("pH")
        await _seed_world(ledger, {hp: [], h: [], xp: [], x: [], p: [xp], d: [x]}, {xp: hp, x: h})
        await raw_force(ledger, hp, blocked_by=[d])
        await raw_relate(ledger, d, hp)
        await raw_force(ledger, x, blocked_by=[p])
        await raw_relate(ledger, p, x)
        p_before = await _row_state(ledger, p)

        records = await _boot_logged(env, caplog)
        assert await column(ledger, d) == [h], f"boot 1: D must heal to [H], got {await column(ledger, d)}"
        assert await _row_state(ledger, p) == p_before, (
            f"boot 1: P must be unchanged, got {await column(ledger, p)}"
        )
        _assert_one_skip_record(records, task_id=p, blocker_ids={xp}, must_include={p, hp}, where="boot 1")

        await _boot_logged(env, caplog)
        assert await column(ledger, p) == [hp], f"boot 2: P must heal to [Hp], got {await column(ledger, p)}"
        assert not _records(caplog, WOULD_CLOSE_CYCLE_EVENT), (
            "boot 2: a WARNING fired with nothing left to close"
        )
        assert not _reaches(await all_columns(ledger), p, p), "boot 2 wrote P onto a cycle"


# =========================================================================== #
# am-17 §14 (#636, #635, #634, #638) — the guard's INPUT is every blocked_by column, in one statement
# =========================================================================== #

#: §14.2's boot WARNING when the guard's input exceeds the measured size, and its constant. The ruling leaves
#: the constant's name to the builder; this contract fixes it (REPORT-contract-58-r53.md §FIXWAVE-14).
GRAPH_LARGE_EVENT = "task.guard.graph_large"
GRAPH_LARGE_CONSTANT = "TASK_GUARD_GRAPH_LARGE_ROWS"
#: §14.2: "when the count exceeds 20,000, the largest size measured" (§14.1's top row was 19,200).
RULED_GRAPH_LARGE_ROWS = 20_000
#: #635: the audit's subject chain length (past TASK_BLOCKER_MAX_DEPTH = 32) and its control.
LONG_CHAIN_LINKS, SHORT_CHAIN_LINKS = 40, 3
#: #634: repeats inside the one test (the audit measured 20/20 at cdf1ce4).
CONCURRENT_SUPERSEDE_REPEATS = 20


def _any_cycle(columns: dict[str, list[str]]) -> list[str] | None:
    """A whole-table ``blocked_by`` cycle, by the batch-key detector (graphlib), which is NOT the
    persisted-row predicate under test — so it is an independent witness of a written loop."""
    return find_blocked_by_cycle(columns)


async def _chain_onto(ledger: TaskLedger, target: str, links: int) -> str:
    """``links`` tasks through the LIVE verbs: X_k ``[target]``, X_i ``[X_{i+1}]`` … X_0. Returns X_0."""
    previous = await create(ledger, "fw14 chain X_k", blocked_by=[target])
    for index in range(links - 1, -1, -1):
        previous = await create(ledger, f"fw14 chain X_{index}", blocked_by=[previous])
    return previous


class TestTheGuardsInputHasNoDepthBoundAndNoSeedCost:
    """am-17 §14.2: the four writers' input is every ``blocked_by`` column in one statement. RED at HEAD: the
    bounded closure walk stops at 32 hops (#635) and costs ~ rows × seeds with ``TIMEOUT 5s`` (#636)."""

    async def test_636_a_boot_with_300_stragglers_of_DISTINCT_heads_completes_and_heals_them_all(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """The audit's world: 300 stragglers, each re-anchored to its OWN head, every head blocked by one
        shared 30-deep chain (930 rows; 300 seeds for a closure read). Kills any input whose cost grows with
        the seed count (HEAD: the boot raises ``TxnDomainRejectionError`` on the read's ``TIMEOUT 5s``)."""
        ledger, env = ledger58
        now = datetime.now(UTC)

        def content(subject: str, blocked_by: list[str]) -> dict[str, Any]:
            return TaskLedger._new_task_content(subject, DESCRIPTION, blocked_by, CREATOR, now)  # noqa: SLF001

        chain = [_tid(f"g6c{i:03d}") for i in range(30)]
        heads = [_tid(f"g6h{j:03d}") for j in range(300)]
        olds = [_tid(f"g6x{j:03d}") for j in range(300)]
        dependents = [_tid(f"g6d{j:03d}") for j in range(300)]
        rows: list[dict[str, Any]] = [
            {"id": RecordID(TASK_TABLE, c), **content(c, [chain[i + 1]] if i + 1 < len(chain) else [])}
            for i, c in enumerate(chain)
        ]
        rows += [{"id": RecordID(TASK_TABLE, h), **content(h, [chain[0]])} for h in heads]
        rows += [
            {"id": RecordID(TASK_TABLE, x), **content(x, []), "superseded_by": h}
            for x, h in zip(olds, heads, strict=True)
        ]
        rows += [
            {"id": RecordID(TASK_TABLE, d), **content(d, [x])} for d, x in zip(dependents, olds, strict=True)
        ]
        await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": rows})
        edges = [
            {"in": RecordID(TASK_TABLE, chain[i + 1]), "out": RecordID(TASK_TABLE, c)}
            for i, c in enumerate(chain[:-1])
        ]
        edges += [{"in": RecordID(TASK_TABLE, chain[0]), "out": RecordID(TASK_TABLE, h)} for h in heads]
        edges += [
            {"in": RecordID(TASK_TABLE, x), "out": RecordID(TASK_TABLE, d)}
            for d, x in zip(dependents, olds, strict=True)
        ]
        await raw(ledger, f"INSERT RELATION INTO {BLOCKS_RELATION} $edges", {"edges": edges})
        await boot(env)  # completes: a raise here is #636
        columns = await all_columns(ledger)
        unhealed = [d for d, h in zip(dependents, heads, strict=True) if columns.get(d) != [h]]
        assert not unhealed, (
            f"{len(unhealed)} of 300 stragglers were not healed to their head, e.g. {unhealed[:3]}"
        )

    @pytest.mark.parametrize(
        "links", [SHORT_CHAIN_LINKS, LONG_CHAIN_LINKS], ids=["control_3_links", "40_links"]
    )
    async def test_635_S_the_live_supersede_refuses_a_cycle_through_a_LONG_chain(
        self, ledger58: tuple[TaskLedger, SurrealEnv], links: int
    ) -> None:
        """Leg S: T0; D ``[T0]``; a chain X_k ``[D]`` … X_0; ``supersede(T0, blocked_by=[X_0])``
        re-anchors D to S and closes S -> X_0 -> … -> X_k -> D -> S (k + 3 members) → ``TaskCycleError``,
        nothing written. Kills a depth-bounded input (HEAD: 32 hops, so the 40-link loop is written)."""
        ledger, _env = ledger58
        t0 = await create(ledger, "fw14 S T0")
        d = await create(ledger, "fw14 S D", blocked_by=[t0])
        x0 = await _chain_onto(ledger, d, links)
        before = await snapshot(ledger)
        with pytest.raises(TaskCycleError):
            await supersede(ledger, t0, blocked_by=[x0])
        assert await snapshot(ledger) == before, "a refused supersede wrote something"

    @pytest.mark.parametrize(
        "links", [SHORT_CHAIN_LINKS, LONG_CHAIN_LINKS], ids=["control_3_links", "40_links"]
    )
    async def test_635_H_the_heal_skips_a_straggler_whose_reanchor_closes_a_LONG_cycle(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture, links: int
    ) -> None:
        """Leg H: D; a chain onto D; T0 superseded by S ``blocked_by [X_0]`` (no dependents then); then the
        straggler a create racing the supersede leaves (D ``[T0]`` plus its edge). The boot heal must skip D
        (its re-anchor would close S -> X_0 -> … -> D -> S) and record it ONCE. Kills a depth-bounded
        input."""
        ledger, env = ledger58
        d = await create(ledger, "fw14 H D")
        x0 = await _chain_onto(ledger, d, links)
        t0 = await create(ledger, "fw14 H T0")
        await supersede(ledger, t0, blocked_by=[x0])
        await raw_force(ledger, d, blocked_by=[t0])
        await raw_relate(ledger, t0, d)
        before = await _row_state(ledger, d)
        records = await _boot_logged(env, caplog)
        assert await _row_state(ledger, d) == before, f"D was re-anchored: {await column(ledger, d)}"
        _assert_one_skip_record(
            records, task_id=d, blocker_ids={t0}, must_include={d}, where=f"{links} links"
        )
        assert _any_cycle(await all_columns(ledger)) is None, "the heal wrote a cycle"


class TestTwoConcurrentSupersedesOnOneLedgerCannotJointlyWriteACycle:
    """am-17 §14.3 / #634: an in-process lock serialises ``supersede_task``'s guard-then-write, so the
    second of two concurrent supersedes reads the first one's writes and is refused. RED at HEAD (both commit,
    20/20). The two-PROCESS bound is finding #634 plus docstrings, never a test (§14.7 item 1)."""

    async def test_634_one_of_two_concurrent_supersedes_is_refused_every_time(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """Per repeat: T1, T2; D1 ``[T1]``; X ``[T2]``. A: ``supersede(T1, blocked_by=[X])`` (re-anchors
        D1 -> S1); B: ``supersede(T2, blocked_by=[D1])`` (re-anchors X -> S2). Either alone is legal; both
        close S1 -> X -> S2 -> D1 -> S1. Started together on ONE ledger (the served shape) → exactly one
        ``TaskCycleError`` and no cycle over all columns, in every one of 20 repeats."""
        import asyncio

        ledger, _env = ledger58

        async def fate(coroutine: Any) -> str:
            try:
                await coroutine
                return "ok"
            except TaskCycleError:
                return "refused"

        failures: list[tuple[int, list[str], list[str] | None]] = []
        for repeat in range(CONCURRENT_SUPERSEDE_REPEATS):
            t1 = await create(ledger, f"fw14 T1 #{repeat}")
            t2 = await create(ledger, f"fw14 T2 #{repeat}")
            d1 = await create(ledger, f"fw14 D1 #{repeat}", blocked_by=[t1])
            x = await create(ledger, f"fw14 X #{repeat}", blocked_by=[t2])
            fates = await asyncio.gather(
                fate(supersede(ledger, t1, blocked_by=[x])), fate(supersede(ledger, t2, blocked_by=[d1]))
            )
            loop = _any_cycle(await all_columns(ledger))
            if sorted(fates) != ["ok", "refused"] or loop is not None:
                failures.append((repeat, list(fates), loop))
        assert not failures, (
            f"{len(failures)} of {CONCURRENT_SUPERSEDE_REPEATS} repeats did not refuse exactly one "
            f"supersede, or left "
            f"a cycle: {failures[:3]}"
        )


class TestTheGraphLargeWarning:
    """am-17 §14.2's named bound: the boot logs WARNING ``task.guard.graph_large`` when the dependency-bearing
    row count exceeds the constant (20,000, the largest size §14.1 measured). RED at HEAD (no constant, no
    record)."""

    @pytest.mark.parametrize("constant", ["shrunk_below_the_fixture", "shipped"])
    async def test_graph_large_is_emitted_once_when_shrunk_and_not_at_the_shipped_value(
        self,
        ledger58: tuple[TaskLedger, SurrealEnv],
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        constant: str,
    ) -> None:
        """Five dependency-bearing rows. Shrunk to 2 → exactly one WARNING per boot; shipped → none, and the
        constant carries the ruled number."""
        import loremaster.tasks as tasks_module

        ledger, env = ledger58
        blocker = await create(ledger, "fw14 graph blocker")
        for index in range(5):
            await create(ledger, f"fw14 graph row {index}", blocked_by=[blocker])
        if constant == "shipped":
            assert getattr(tasks_module, GRAPH_LARGE_CONSTANT) == RULED_GRAPH_LARGE_ROWS, (
                f"{GRAPH_LARGE_CONSTANT} must carry §14.2's measured number, {RULED_GRAPH_LARGE_ROWS}"
            )
        else:
            monkeypatch.setattr(tasks_module, GRAPH_LARGE_CONSTANT, 2, raising=True)
        await _boot_logged(env, caplog)
        warnings = [r for r in _records(caplog, GRAPH_LARGE_EVENT) if r.levelno == logging.WARNING]
        expected = 0 if constant == "shipped" else 1
        assert len(warnings) == expected, (
            f"{constant}: {len(warnings)} {GRAPH_LARGE_EVENT} WARNINGs on one boot, expected {expected}"
        )


class TestTheCycleAnswerIsDeterministicAndAskedOnceBeforePacking:
    """#638, both ruled properties of am-17 §13.2 (§14.7 item 2). GREEN at HEAD (the build is correct);
    they are the missing pins the delta audit's WB5 (unsorted) and WB2 (per-chunk) survived."""

    # One world per writer shape: (stored, proposed, asked, all_or_nothing), each with a hit.
    WRITER_WORLDS: dict[str, tuple[dict[str, list[str]], dict[str, list[str]], set[str], bool]] = {
        "create": ({"p": ["q"], "q": ["r"], "r": ["n"], "z": []}, {"n": ["p"]}, {"n"}, True),
        "create_many": ({"p": ["m2"], "q": [], "z": ["q"]}, {"m1": ["p"], "m2": ["m1"]}, {"m1", "m2"}, True),
        "supersede": (
            {"x": ["l1"], "l1": ["l2"], "l2": ["l1", "r"], "r": ["x"]},
            {"s": ["l1"], "r": ["s"]},
            {"s"},
            True,
        ),
        "heal": (
            {"d": ["x"], "h": ["l1"], "l1": ["l2"], "l2": ["l1", "d"], "x": []},
            {"d": ["h"]},
            {"d"},
            False,
        ),
    }

    @pytest.mark.parametrize("writer", sorted(WRITER_WORLDS))
    def test_638_i_the_served_and_recorded_cycle_is_identical_across_insertion_orders(
        self, writer: str
    ) -> None:
        """At least 3 permutations of the insertion order of ``stored`` and of ``proposed``: the
        predicate's answer, the served refusal sentence and the WARNING's ``cycle`` string are byte-identical.
        Kills WB5 (the ``sorted()`` calls removed)."""
        import itertools

        import loremaster.tasks as tasks_module

        stored, proposed, asked, all_or_nothing = self.WRITER_WORLDS[writer]
        answers: set[str] = set()
        orders = list(itertools.islice(itertools.permutations(sorted(stored)), 4))
        for stored_order in orders:
            for proposed_order in itertools.permutations(sorted(proposed)):
                hits = tasks_module.find_row_blocked_by_cycles(
                    {node: list(reversed(stored[node])) for node in stored_order},
                    {row: proposed[row] for row in proposed_order},
                    list(reversed(sorted(asked))),
                    all_or_nothing=all_or_nothing,
                )
                assert hits, f"{writer}: the world must hit (non-vacuity)"
                served = {
                    row: tasks_module.format_cycle_refusal(
                        noun=tasks_module.CYCLE_NOUN_PERSISTED_IDS, cycle=cycle
                    )
                    for row, cycle in hits.items()
                }
                recorded = {row: " -> ".join(cycle) for row, cycle in hits.items()}
                answers.add(repr((sorted(hits.items()), sorted(served.items()), sorted(recorded.items()))))
        assert len(orders) >= 3
        assert len(answers) == 1, f"{writer}: the cycle answer depends on insertion order: {sorted(answers)}"

    async def test_638_ii_leg_B_at_ONE_row_per_chunk_still_skips_and_records_both_rows(
        self,
        ledger58: tuple[TaskLedger, SurrealEnv],
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Leg B's world with ``TXN_ROW_WARN_THRESHOLD`` shrunk to one straggler row's measured weight,
        so the heal packs one row per chunk: both rows stay unchanged and recorded. Kills WB2 (the predicate
        per chunk, after packing: chunk 1 heals D1, chunk 2 then sees the store and skips D2)."""
        from loremaster.store import _txn

        ledger, env = ledger58
        fixed, per = await measure_heal_shape(ledger, env, "fw14shape")
        monkeypatch.setattr(_txn, "TXN_ROW_WARN_THRESHOLD", fixed + per, raising=True)
        assert min(_txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP) == fixed + per
        h1 = await create(ledger, "fw14 B chain head H1")
        h2 = await create(ledger, "fw14 B head H2")
        x1, x1_mid, x2 = _tid("gbX1"), _tid("gbX1p"), _tid("gbX2")
        await raw_seed_row(ledger, x1_mid, blocked_by=[], superseded_by=h1)
        await raw_seed_row(ledger, x1, blocked_by=[], superseded_by=x1_mid)
        await raw_seed_row(ledger, x2, blocked_by=[], superseded_by=h2)
        d1 = await _seed(ledger, _tid("gbD1"), [x1])
        d2 = await _seed(ledger, _tid("gbD2"), [x2])
        await raw_force(ledger, h1, blocked_by=[d2])
        await raw_relate(ledger, d2, h1)
        await raw_force(ledger, h2, blocked_by=[d1])
        await raw_relate(ledger, d1, h2)
        before = {row: await _row_state(ledger, row) for row in (d1, d2)}
        records = await _boot_logged(env, caplog)
        for row in (d1, d2):
            assert await _row_state(ledger, row) == before[row], f"{row} changed at one row per chunk"
        _assert_one_skip_record(records, task_id=d1, blocker_ids={x1}, must_include={d1, h1}, where="D1")
        _assert_one_skip_record(records, task_id=d2, blocker_ids={x2}, must_include={d2, h2}, where="D2")
