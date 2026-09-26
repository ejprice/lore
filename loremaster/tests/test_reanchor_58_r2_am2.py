"""Packet 58 contract r2 — amendment 2 (``e0760fd``) as CORRECTED by amendment 3 (``7266c1b``) §1.

*Scoped to the tree at ``ccdad34`` (branch ``feat/surreal-unification``), 2026-09-26, authored by
``contract-58-r2``.  "RED at HEAD" means RED at that commit.*

PR19 and PR20 are adversary-58's batch-3 probes (``9f2f580:REPORT-adversary-58.md`` §INSTRUMENTS,
md5 ``cdb99104``) landed AST-EQUAL.  PR18 is NOT landed as written: its ``chunks == 2`` literal is
amendment 2's ruled shape, which amendment 3 §1 ERRATUM retires (it passes the defective
supersede-sized chunker AM2L and reds a correct heal-sized packer AM2C, PR18 §FOLLOWUP).  It is
RE-KEYED here (``test_PR18r2_…``) to the packer's own predicted chunk count, MEASURED off
``compose`` — never a literal (``REPORT-contract-58-r2.md`` §DEVIATIONS D-PR18, its kill re-proven).
"""

from __future__ import annotations

import logging

import pytest
from _reanchor_58_support import (
    CLAIMANT,
    bulk_seed_dependents,
    column,
    create,
    ledger58,
    measure_heal_shape,
    new_ledger,
    predicted_chunks,
    raw_seed_row,
    successor_of,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.tasks import TaskLedger

__all__ = ["ledger58"]
HEAL_EVENT = "task.backfill.stragglers_reanchored"


async def _boot(env: SurrealEnv, caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    booted = new_ledger(env)
    caplog.clear()
    try:
        with caplog.at_level(logging.DEBUG):
            await booted.ensure_ready()
    finally:
        await booted.close()
    return [r for r in caplog.records if r.getMessage() == HEAL_EVENT]


async def _stragglers(ledger: TaskLedger, total: int, blockers: int, tag: str) -> list[str]:
    head = await create(ledger, f"{tag} head")
    ids: list[str] = []
    per = -(-total // blockers)
    for index in range(blockers):
        legacy = f"{tag}legacy{index:03d}0000000000000000"
        await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
        count = min(per, total - len(ids))
        if count <= 0:
            break
        ids += await bulk_seed_dependents(ledger, legacy, count, tag=f"{tag}{index:03d}x")
    return ids


# PR18r2 — amendment 3 §1 (ii): the ONE-blocker population STAYS, but `chunks` is the packer's OWN
# prediction for it (measured shape, greedy fit), never amendment 2's literal 2.
async def test_PR18r2_cap_plus_one_of_ONE_blocker_heals_in_the_PACKERS_predicted_chunks(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    fixed, per = await measure_heal_shape(ledger, env, "am3shape")
    cap = ledger.max_reanchor_dependents(0)
    ids = await _stragglers(ledger, cap + 1, 1, "am3one")
    expected = predicted_chunks(cap + 1, fixed, per, _txn.TXN_STATEMENT_HARD_CAP)
    records = await _boot(env, caplog)
    assert len(records) == 1 and getattr(records[0], "count", None) == cap + 1, [
        (getattr(r, "count", None), getattr(r, "chunks", None)) for r in records
    ]
    assert getattr(records[0], "chunks", None) == expected, (
        f"{cap + 1} one-blocker stragglers; the heal chunk measures fixed={fixed}, per={per}, so a "
        f"greedy packer against the {_txn.TXN_STATEMENT_HARD_CAP}-statement cap needs {expected} "
        f"chunk(s) — got {getattr(records[0], 'chunks', None)}. A chunk sized by the SUPERSEDE's "
        f"accessor (amendment 2's literal) is the defect amendment 3 §1 corrects"
    )
    for task_id in (ids[0], ids[-1]):
        assert len(await column(ledger, task_id)) == 1, task_id


# PR19 — the SAME population spread over TEN distinct superseded blockers (the fleet's real shape).
async def test_PR19_cap_plus_one_stragglers_over_TEN_blockers_all_heal_in_ONE_boot(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    cap = ledger.max_reanchor_dependents(0)
    await _stragglers(ledger, cap + 1, 10, "am2ten")
    records = await _boot(env, caplog)
    assert records and getattr(records[-1], "count", None) == cap + 1, [
        (getattr(r, "count", None), getattr(r, "chunks", None)) for r in records
    ]
    second = await _boot(env, caplog)
    assert not second, "the sweep did not converge: a second boot still found stragglers to heal"


# PR20 — amendment 2 (a): owner= serves a HELD superseded row, decorated; owner=+status= excludes it.
async def test_PR20_owner_query_serves_a_held_superseded_row_and_status_excludes_it(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    held = await create(ledger, "Y — alice holds it, then it is reframed")
    kept = await create(ledger, "Z — alice holds it, never reframed")
    assert (await ledger.claim_task(held, CLAIMANT)).claimed
    assert (await ledger.claim_task(kept, CLAIMANT)).claimed
    successor = successor_of(await supersede(ledger, held))
    by_owner = {t.id: t for t in await ledger.query_tasks(owner=CLAIMANT)}
    assert set(by_owner) == {held, kept}, sorted(by_owner)
    assert by_owner[held].superseded_by == successor and by_owner[kept].superseded_by is None
    with_status = {t.id for t in await ledger.query_tasks(owner=CLAIMANT, status="claimed")}
    assert with_status == {kept}, sorted(with_status)
