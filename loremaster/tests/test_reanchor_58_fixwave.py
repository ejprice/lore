"""Packet 58 fix-wave contract — amendment 17 §12 (cold-audit F1, #623), §12.8 item 1, #626, §12.7, #625,
#130(a).

*Every claim in this file is scoped to the tree at ``380414c`` (branch ``feat/surreal-unification``,
production
identical to the graded build ``aa4ea04``), 2026-11-10, authored by ``contract-58-r53``. "RED at HEAD"
means RED on
that tree.*

* **Property P (§12.2).** After a boot heal, no row the heal wrote lies on a ``blocked_by`` cycle. A
  straggler whose
  re-anchor would close one (alone, jointly with another straggler, or by joining a legacy loop) is SKIPPED
  WHOLE —
  column, edges and ``updated_at`` byte-identical, not counted — and recorded EVERY boot as the WARNING
  ``task.backfill.straggler_would_close_cycle`` (``database``, ``task_id``, ``blocker_ids``, ``cycle``,
  ``members``). Legs A, B and C of §12.4; leg B uses a two-supersession chain (X1 → X1′ → H1), so the cycle
  closes
  at the chain HEAD.
* **Leg D (§12.8 item 1).** A legacy ``blocked_by`` loop with no missing edge is recorded on EVERY boot
  (``task.backfill.legacy_cycle_minted``), not only on a boot that has edges to mint.
* **OB3 (#626).** A supersede removes EVERY ``blocks`` edge out of the superseded task, including a drift
  edge to a
  row whose column does not name it (am-17 §9.2's removed-behaviour inventory, first row).
* **Served text.** F5 (§12.7): the claim loss on a superseded blocker serves "can never resolve: block on the
  successor instead" and no longer "can never win". #130(a): the served ``lore_tasks`` schema's ``status``
  description names the superseded-row exclusion. (#625 a/b ride the legs that already raise those errors:
  ``test_reanchor_58_r3_convergence.py``'s over-weight row and ``test_supersede_reanchor_58.py``'s cap+1 hub.)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest
from _reanchor_58_support import (
    HEAL_EVENT,
    all_columns,
    boot,
    bulk_seed_dependents,
    column,
    create,
    edge_pairs,
    ledger58,
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


# =========================================================================== #
# §12.4 legs A–C — property P: the heal never writes a row onto a blocked_by cycle
# =========================================================================== #


class TestTheHealNeverWritesARowOntoACycle:
    """am-17 §12.2 / §12.4. RED at HEAD: the heal re-anchors without the write path's cycle predicate."""

    async def test_A_a_straggler_whose_reanchor_closes_a_cycle_is_skipped_WHOLE_and_recorded_every_boot(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Leg A, the audit's world plus two riders: X superseded by H with no re-anchor; H ``blocked_by
        [D]``;
        D ``blocked_by [X, X2]`` with X2 superseded by a healthy H2; one unrelated healthy straggler S.

        Kills: no check (D healed to [H, H2], a cycle written); check-then-write-anyway; a raise (boot
        denial);
        a silent skip (no WARNING); a partial re-anchor (X2 moved to H2); a record only on the first boot."""
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
        they
        write D1 → H1 → D2 → H2 → D1, closing at the chain HEAD H1 (not at X1′).

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
        H. The
        heal skips D and records it, although am-3 §4 lets a LIVE supersede re-anchor such a row (§12.2: the
        heal's refusal is per row, so am-3 §4's reason does not apply).

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


# =========================================================================== #
# §12.8 item 1, leg D — a legacy loop is recorded on EVERY boot
# =========================================================================== #


class TestALegacyLoopIsRecordedEveryBoot:
    """am-17 §12.8 item 1. RED at HEAD: ``_backfill_blocks_edges`` returns before ``_record_legacy_cycles``
    when no
    edge is missing, so a mirror-consistent legacy loop is never recorded."""

    async def test_D_a_legacy_loop_with_NO_missing_edge_is_recorded_on_every_boot_and_nothing_changes(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        """A ``blocked_by [B]``, B ``blocked_by [A]``, both edges present. Two boots: each records the loop
        once,
        naming both members; the store is unchanged.

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


# =========================================================================== #
# #626 (cold audit probes F1, OB3) — every edge OUT of the superseded task goes, drift edges included
# =========================================================================== #


class TestTheSupersedeRemovesEveryOutEdgeOfTheOldTask:
    """am-17 §9.2's removed-behaviour inventory, row 1 ("deletes every edge whose ``in`` is the old task"),
    pinned in
    a world that is NOT mirror-consistent. GREEN at HEAD (the built DELETE is ``$old->blocks``); it is the
    missing
    pin #626 names, so it carries no RED."""

    async def test_a_DRIFT_edge_out_of_the_hub_is_deleted_with_the_dependents_edges(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """A hub with 3 dependents, one blocker of its own, and a drift edge hub → E where E's column does not
        name the hub. After the supersede: no edge leaves the hub; the edge INTO the hub survives; E's
        column is
        untouched and E is not reported as re-anchored.

        Kills OB3 (``DELETE … WHERE out INSIDE $dependents_read`` leaves the drift edge) and a DELETE over
        both
        directions (the blocker's edge into the hub goes too)."""
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


# =========================================================================== #
# Served text — F5 (§12.7) and #130(a)
# =========================================================================== #


class TestTheServedTextSaysWhatIsTrue:
    """am-17 §12.7. RED at HEAD: the claim render says "can never win"; the ``status`` description does not
    name
    the superseded-row exclusion."""

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
