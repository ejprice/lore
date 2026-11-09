"""Packet 58 contract r3 — adversary-58-r2's graded kill probes, landed AST-EQUAL (am-17's rule).

*Every claim in this file is scoped to the tree at ``c9e5eb8`` (branch ``feat/surreal-unification``),
2026-09-26, authored by ``contract-58-r3``.  "RED at HEAD" means RED at that commit.*

Source: ``REPORT-adversary-58-r2.md`` (``821be62``) §INSTRUMENTS ``test_adv58r2_probes.py`` (md5 ``55aac187``)
and ``test_adv58r2_probes_e.py`` (md5 ``439570bc``).  Each function below is AST-equal to the adversary's
(receipt: ``REPORT-contract-58-r3.md`` §AST); only this docstring and the merged import block differ.

* PA1 / PA2 — am-3 §3 → am-6/am-7: a lost SUPERSEDE race and an R1 straggler roll back at WARNING (F2).
* PB — am-8 §0 row (2): a routine claim loss raises no alarm from ANY ``loremaster`` logger (F3).
* PC — am-8 §2: two-blocker stragglers at scale heal in ONE boot, every chunk ≤ the cap (F1).
* PD1 / PD2 — am-8 §4 F4: a MIXED row with a phantom / cyclic chain is skipped WHOLE and uncounted.
* PE — am-8 §2 edge (F10): one straggler whose own weight exceeds the cap fails the boot LOUD, nothing
  changed.

The GENERATED forms of each property live in ``test_reanchor_58_r3_convergence.py`` /
``test_reanchor_58_r3_tiers.py``; these are the adversary's hand instances, kept as extra examples.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from _reanchor_58_support import (
    CREATOR,
    DESCRIPTION,
    HEAL_CHAIN_CYCLE_EVENT,
    HEAL_EVENT,
    HEAL_PHANTOM_HEAD_EVENT,
    ROLLBACK_EVENT,
    ApplyHook,
    ComposeSpy,
    all_columns,
    boot,
    column,
    create,
    ledger58,
    new_ledger,
    raw,
    raw_relate,
    raw_seed_row,
    shrunk_row_caps,
    snapshot,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import IllegalTransitionError, TaskLedger, TaskLedgerError
from surrealdb import RecordID

if TYPE_CHECKING:
    # ⚠ packet 58's RULED, not-yet-built symbol, named STATICALLY for the typecheck gate (lead #17055, the
    # #461 shape): a mypy error at HEAD owned by `scripts/pending_contracts.yaml` bound `packet-58-contract`,
    # which owns this file's RED@HEAD pytest legs too and self-destructs with the build.  Runtime-inert.
    from loremaster.tasks import StragglerHealPackerError

    _RULED_58: tuple[object, ...] = (StragglerHealPackerError,)

__all__ = ["ledger58", "shrunk_row_caps"]


def _levels(caplog: pytest.LogCaptureFixture, message: str) -> list[int]:
    return [r.levelno for r in caplog.records if r.getMessage() == message]


# P-A (am-3 §3, ∀ "every OTHER THROW-rooted rollback … transition/supersede lost races, R1's straggler …
# WARNING")
@pytest.mark.usefixtures("shrunk_row_caps")
async def test_PA1_a_lost_SUPERSEDE_race_logs_its_rollback_at_WARNING(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    old = await create(ledger, "X")
    racer = new_ledger(env)
    hook = ApplyHook(ledger, lambda: supersede(racer, old))
    caplog.clear()
    try:
        with hook.installed(), caplog.at_level(logging.DEBUG), pytest.raises(IllegalTransitionError):
            await supersede(ledger, old)
    finally:
        await racer.close()
    assert hook.fired
    assert _levels(caplog, ROLLBACK_EVENT) == [logging.WARNING], [
        logging.getLevelName(level) for level in _levels(caplog, ROLLBACK_EVENT)
    ]


@pytest.mark.usefixtures("shrunk_row_caps")
async def test_PA2_an_R1_straggler_rollback_logs_at_WARNING(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    old = await create(ledger, "X")
    await create(ledger, "Y", [old])
    racer = new_ledger(env)
    hook = ApplyHook(ledger, lambda: create(racer, "late Y", [old]))
    caplog.clear()
    try:
        with hook.installed(), caplog.at_level(logging.DEBUG), pytest.raises(TaskLedgerError):
            await supersede(ledger, old)
    finally:
        await racer.close()
    assert hook.fired
    assert _levels(caplog, ROLLBACK_EVENT) == [logging.WARNING], [
        logging.getLevelName(level) for level in _levels(caplog, ROLLBACK_EVENT)
    ]


# P-B (am-3 §3 principle: "a routine claim LOSS is not an error" — from ANY lore logger, not only the
# driver's)
@pytest.mark.usefixtures("shrunk_row_caps")
async def test_PB_an_8_way_claim_race_raises_no_alarm_from_ANY_lore_logger(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    task_id = await create(ledger, "contended")
    racers = [new_ledger(env) for _ in range(8)]
    caplog.clear()
    try:
        with caplog.at_level(logging.DEBUG):
            results = await asyncio.gather(
                *(r.claim_task(task_id, f"racer-{i}") for i, r in enumerate(racers))
            )
    finally:
        for racer in racers:
            await racer.close()
    assert sum(r.claimed for r in results) == 1
    loud = [
        (r.name, r.levelname, r.getMessage())
        for r in caplog.records
        # ⚠ DUAL (packet 58 contract r4 — amendment 12 §3 F-H): USED to filter
        # `r.name.startswith("loremaster")`;
        # every captured record, ANY logger name, is in scope (a root-logger alarm is the same alarm).
        if r.levelno >= logging.WARNING
    ]
    assert not loud, loud


# P-C (am-3 §1: the packer BUILDS each row's fragments — ∀ rows, incl. a row naming TWO superseded blockers)
@pytest.mark.usefixtures("shrunk_row_caps")
async def test_PC_stragglers_naming_TWO_superseded_blockers_at_scale_heal_in_ONE_boot(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    head_a, head_b = await create(ledger, "head A"), await create(ledger, "head B")
    legacy_a, legacy_b = "pcleg" + "a" * 27, "pcleg" + "b" * 27
    await raw_seed_row(ledger, legacy_a, blocked_by=[], superseded_by=head_a)
    await raw_seed_row(ledger, legacy_b, blocked_by=[], superseded_by=head_b)
    count = 1300
    now = datetime.now(UTC)
    ids = [f"pcrow{index:05d}" for index in range(count)]
    rows = [
        {
            "id": RecordID(TASK_TABLE, task_id),
            **TaskLedger._new_task_content(f"row {task_id}", DESCRIPTION, [legacy_a, legacy_b], CREATOR, now),
        }  # noqa: SLF001
        for task_id in ids
    ]
    await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": rows})
    edges = [
        {"in": RecordID(TASK_TABLE, b), "out": RecordID(TASK_TABLE, t)}
        for t in ids
        for b in (legacy_a, legacy_b)
    ]
    await raw(ledger, f"INSERT RELATION INTO {BLOCKS_RELATION} $edges", {"edges": edges})
    spy = ComposeSpy()
    caplog.clear()
    with spy.installed(), caplog.at_level(logging.DEBUG):
        await boot(
            env
        )  # a packer that under-counts a two-blocker row composes > cap: compose refuses, the BOOT fails
    columns = await all_columns(ledger)
    assert all(columns[t] == [head_a, head_b] for t in ids)
    heal = [r for r in caplog.records if r.getMessage() == HEAL_EVENT]
    assert len(heal) == 1 and getattr(heal[0], "count", None) == count
    assert all(rows <= _txn.TXN_ROW_HARD_CAP for rows in spy.heal_rows()), spy.heal_rows()


# P-D (am-3 §5: "a row whose head is a phantom is SKIPPED" — the WHOLE row, excluded from count; ∀ rows
# incl. MIXED)
@pytest.mark.usefixtures("shrunk_row_caps")
async def test_PD1_a_MIXED_row_phantom_head_plus_healable_blocker_is_skipped_WHOLE(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    phantom_head = "pdphantomhead" + "0" * 19
    pblocker, hblocker = "pdpblocker" + "0" * 22, "pdhblocker" + "0" * 22
    head = await create(ledger, "a real head")
    await raw_seed_row(ledger, pblocker, blocked_by=[], superseded_by=phantom_head)
    await raw_seed_row(ledger, hblocker, blocked_by=[], superseded_by=head)
    mixed = "pdmixedrow" + "0" * 22
    await raw_seed_row(ledger, mixed, blocked_by=[pblocker, hblocker])
    await raw_relate(ledger, pblocker, mixed)
    await raw_relate(ledger, hblocker, mixed)
    before = [row for row in (await snapshot(ledger))[0] if mixed in row]
    edges_before = [e for e in (await snapshot(ledger))[1] if e[1] == mixed]
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await boot(env)
    assert [row for row in (await snapshot(ledger))[0] if mixed in row] == before, (
        "the mixed row was half-healed"
    )
    assert [e for e in (await snapshot(ledger))[1] if e[1] == mixed] == edges_before
    assert len([r for r in caplog.records if r.getMessage() == HEAL_PHANTOM_HEAD_EVENT]) == 1
    assert not [r for r in caplog.records if r.getMessage() == HEAL_EVENT], "a skipped row was counted"


@pytest.mark.usefixtures("shrunk_row_caps")
async def test_PD2_a_MIXED_row_cyclic_chain_plus_healable_blocker_is_skipped_WHOLE(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    first, second = "pdcyca" + "0" * 26, "pdcycb" + "0" * 26
    await raw_seed_row(ledger, first, blocked_by=[], superseded_by=second)
    await raw_seed_row(ledger, second, blocked_by=[], superseded_by=first)
    head = await create(ledger, "a real head")
    hblocker = "pdhblock2" + "0" * 23
    await raw_seed_row(ledger, hblocker, blocked_by=[], superseded_by=head)
    mixed = "pdmixcyc" + "0" * 24
    await raw_seed_row(ledger, mixed, blocked_by=[first, hblocker])
    await raw_relate(ledger, first, mixed)
    await raw_relate(ledger, hblocker, mixed)
    before = await snapshot(ledger)
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await asyncio.wait_for(boot(env), timeout=60)
    assert await snapshot(ledger) == before, "a cyclic-chain row was half-healed"
    assert len([r for r in caplog.records if r.getMessage() == HEAL_CHAIN_CYCLE_EVENT]) == 1
    assert not [r for r in caplog.records if r.getMessage() == HEAL_EVENT]


@pytest.mark.usefixtures("shrunk_row_caps")
async def test_PE_a_single_straggler_that_alone_exceeds_the_cap_fails_the_boot_LOUD_and_changes_nothing(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    head = await create(ledger, "the head")
    now = datetime.now(UTC)
    legacy = [f"peleg{index:05d}" + "0" * 22 for index in range(1700)]
    rows = [
        {
            "id": RecordID(TASK_TABLE, lid),
            **TaskLedger._new_task_content(f"legacy {lid}", DESCRIPTION, [], CREATOR, now),  # noqa: SLF001
            "superseded_by": head,
        }
        for lid in legacy
    ]
    await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": rows})
    monster = "pemonster" + "0" * 23
    content = TaskLedger._new_task_content("monster", DESCRIPTION, legacy, CREATOR, now)  # noqa: SLF001
    await raw(ledger, f"CREATE type::record('{TASK_TABLE}', $id) CONTENT $c", {"id": monster, "c": content})
    before = await column(ledger, monster)
    assert len(before) == 1700
    with pytest.raises((TaskLedgerError, Exception)) as caught:
        await boot(env)
    assert "cap" in str(caught.value).lower() or "row" in str(caught.value).lower(), repr(caught.value)
    print("RAISED:", type(caught.value).__name__, str(caught.value)[:160])
    assert await column(ledger, monster) == before
