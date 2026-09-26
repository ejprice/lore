"""Packet 58 contract r2 — adversary-58's graded PROBES PR1–PR15, landed AST-EQUAL (contract-58-r2).

*Scoped to the tree at ``ccdad34`` (branch ``feat/surreal-unification``), 2026-09-26, authored by
``contract-58-r2``.  "RED at HEAD" means RED at that commit.*

Provenance: ``9f2f580:REPORT-adversary-58.md`` §INSTRUMENTS ``test_adversary58_probes.py`` (md5
``2cf0d5f4``) — every function below is AST-equal to the adversary's (packet-63c amendment 17's rule:
lint-clean re-wraps allowed; the AST receipt + its controls are in ``REPORT-contract-58-r2.md``
§AST).  Only the import block differs (unused names dropped).  Each probe is a MISSING PIN the graded
contract ``5a43aeb`` lacked (§MISSING PINS MP1–MP14 / MP18) and was graded to FAIL on its paired
wrong build (§P1 WB1–WB17) while passing an independent reference — the kills are re-proven on
contract-58-r2's reference in the report (§MUTATION).  Rulings that apply: amendment 3
(``docs/design/2026-09-26-packet58-amendment-3.md`` @ ``7266c1b``) §4 (PR8: refuse ONLY a cycle through
X' — the supersede SUCCEEDS), §5 (PR5: a phantom head is skipped, never a boot failure), §3 (PR10: a
routine claim loss is DEBUG — stricter pins in ``test_reanchor_58_r2_rulings.py``).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import pytest
from _reanchor_58_support import (
    ACTION_REANCHORED,
    CLAIMANT,
    all_columns,
    assert_edge_mirrors_column_for_every_row,
    bulk_seed_dependents,
    column,
    create,
    drive_to,
    events_of,
    ledger58,
    new_ledger,
    raw,
    raw_relate,
    raw_seed_row,
    successor_of,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.store.surreal_schema import TASK_TABLE
from loremaster.tasks import STATUS_WONTFIX, TaskLedger

__all__ = ["ledger58"]


async def _boot(env: SurrealEnv) -> None:
    booted = new_ledger(env)
    try:
        await booted.ensure_ready()
    finally:
        await booted.close()


def _chain(tag: str, length: int) -> list[str]:
    return [f"{tag}{index:02d}chainadv5800000000000" for index in range(length)]


async def _seed_chain(ledger: TaskLedger, ids: list[str]) -> None:
    for index, task_id in reversed(list(enumerate(ids))):
        nxt = ids[index + 1] if index + 1 < len(ids) else None
        await raw_seed_row(ledger, task_id, blocked_by=[], superseded_by=nxt)


# ---------------------------------------------------------------------------------------------
# PR1 — a NON-straggler rollback must NOT be served as the R1 "retry" teaching (supersede twin of B6)
# ---------------------------------------------------------------------------------------------
async def test_PR1_a_genuine_store_fault_is_not_laundered_into_the_R1_retry_teaching(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    old = await create(ledger, "X")
    dependent = await create(ledger, "Y", [old])
    await raw(
        ledger,
        f"DEFINE EVENT adv58 ON TABLE {TASK_TABLE} WHEN $event = 'UPDATE' AND "
        f"record::id($after.id) = '{dependent}' THEN {{ THROW 'adv58-injected' }}",
    )
    with pytest.raises(Exception) as caught:  # noqa: PT011
        await supersede(ledger, old)
    text = str(caught.value).lower()
    assert "retry" not in text and "was created while" not in text, (
        f"a store fault with NO concurrent create was served as the R1 straggler teaching: {caught.value!r}"
    )


# ---------------------------------------------------------------------------------------------
# PR2 — the derived cap must follow K across a floor boundary (K = per always crosses one)
# ---------------------------------------------------------------------------------------------
async def test_PR2_the_cap_moves_with_K_across_a_floor_boundary(
    ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
) -> None:
    import importlib

    ledger, _env = ledger58
    tasks_module = importlib.import_module("loremaster.tasks")
    real = tasks_module.compose
    counts: list[int] = []

    def _spy(*fragments: Any) -> Any:
        counts.append(sum(len(f.statements) for f in fragments))
        return real(*fragments)

    async def _count(n: int, k: int) -> int:
        old = await create(ledger, "X")
        for i in range(n):
            await create(ledger, f"d{i}", [old])
        blockers = [await create(ledger, f"b{i}") for i in range(k)]
        monkeypatch.setattr(tasks_module, "compose", _spy)
        try:
            await supersede(ledger, old, blocked_by=blockers)
        finally:
            monkeypatch.setattr(tasks_module, "compose", real)
        return counts[-1]

    per = await _count(2, 0) - await _count(1, 0)
    for k in (0, per, per + 1):
        c1 = await _count(1, k)
        fixed = c1 - per
        assert ledger.max_reanchor_dependents(k) == (_txn.TXN_STATEMENT_HARD_CAP - fixed) // per, k


# ---------------------------------------------------------------------------------------------
# PR3 — the heal re-anchors EVERY superseded entry of a row, and counts ROWS (not pairs)
# ---------------------------------------------------------------------------------------------
async def test_PR3_a_straggler_naming_TWO_superseded_blockers_is_healed_fully_and_counted_once(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    chain_a, chain_b = _chain("pa", 2), _chain("pb", 2)
    await _seed_chain(ledger, chain_a)
    await _seed_chain(ledger, chain_b)
    straggler = "adv58twoblockers0000000000000000"
    await raw_seed_row(ledger, straggler, blocked_by=[chain_a[0], chain_b[0]])
    await raw_relate(ledger, chain_a[0], straggler)
    await raw_relate(ledger, chain_b[0], straggler)
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await _boot(env)
    assert await column(ledger, straggler) == [chain_a[-1], chain_b[-1]]
    await assert_edge_mirrors_column_for_every_row(ledger, where="two-blocker straggler")
    records = [r for r in caplog.records if r.getMessage() == "task.backfill.stragglers_reanchored"]
    assert len(records) == 1 and getattr(records[0], "count", None) == 1, [
        getattr(r, "count", None) for r in records
    ]


# ---------------------------------------------------------------------------------------------
# PR4 — the heal must not DOUBLE an edge when the straggler already names the head
# ---------------------------------------------------------------------------------------------
async def test_PR4_a_straggler_already_naming_the_head_gets_ONE_entry_and_ONE_edge(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    chain = _chain("pd", 2)
    await _seed_chain(ledger, chain)
    straggler = "adv58alreadyhead000000000000000"
    await raw_seed_row(ledger, straggler, blocked_by=[chain[0], chain[1]])
    await raw_relate(ledger, chain[0], straggler)
    await raw_relate(ledger, chain[1], straggler)
    await _boot(env)
    assert await column(ledger, straggler) == [chain[1]]
    await assert_edge_mirrors_column_for_every_row(ledger, where="straggler already naming head")


# ---------------------------------------------------------------------------------------------
# PR5 — a straggler whose chain head names NO row must not kill the boot (backfill's R11 twin)
# ---------------------------------------------------------------------------------------------
async def test_PR5_a_phantom_chain_head_does_not_fail_the_boot(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    blocker = "adv58phantomheadblocker00000000"
    await raw_seed_row(ledger, blocker, blocked_by=[], superseded_by="adv58nosuchrow000000000000000000")
    straggler = "adv58phantomheadstraggler000000"
    await raw_seed_row(ledger, straggler, blocked_by=[blocker])
    await raw_relate(ledger, blocker, straggler)
    healthy_old = await create(ledger, "an ordinary X")
    await _boot(env)  # must not raise
    assert await column(ledger, straggler) == [blocker]
    assert healthy_old in await all_columns(ledger)


# ---------------------------------------------------------------------------------------------
# PR6 — #130 exclusion must hold under a LIMIT (T1: a short answer is a TRUE short answer)
# ---------------------------------------------------------------------------------------------
async def test_PR6_status_open_with_a_limit_is_not_short_while_claimable_rows_exist(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    for index in range(6):
        task_id = f"0000adv58sup{index:02d}0000000000000000"
        await raw_seed_row(ledger, task_id, blocked_by=[], superseded_by="zzzzsuccessor")
    genuine = [await create(ledger, f"genuine {i}") for i in range(3)]
    served = await ledger.query_tasks(status="open", limit=3)
    assert sorted(t.id for t in served) == sorted(genuine), [t.id for t in served]


# ---------------------------------------------------------------------------------------------
# PR7 — a WONTFIX predecessor re-blocks exactly like a DONE one (TERMINAL_STATUSES, not "done")
# ---------------------------------------------------------------------------------------------
async def test_PR7_a_WONTFIX_predecessor_reports_its_reblocked_dependent(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    old = await create(ledger, "X, abandoned")
    await drive_to(ledger, old, STATUS_WONTFIX)
    dependent = await create(ledger, "Y, claimable while X is wontfix", [old])
    result = await supersede(ledger, old)
    assert list(result.reblocked) == [dependent]


# ---------------------------------------------------------------------------------------------
# PR8 — a dependent already on a LEGACY loop (not closed by this rewire) — spec-silent; the probe
#       records what the reference does (succeeds) so a refusing build is visible.
# ---------------------------------------------------------------------------------------------
async def test_PR8_a_dependent_on_a_legacy_loop_does_not_block_the_supersede(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    old = await create(ledger, "X")
    loop_l, loop_y = "adv58loopl00000000000000000000", "adv58loopy00000000000000000000"
    await raw_seed_row(ledger, loop_l, blocked_by=[loop_y])
    await raw_seed_row(ledger, loop_y, blocked_by=[old, loop_l])
    await raw_relate(ledger, loop_y, loop_l)
    await raw_relate(ledger, loop_l, loop_y)
    await raw_relate(ledger, old, loop_y)
    successor = successor_of(await supersede(ledger, old))
    assert await column(ledger, loop_y) == [successor, loop_l]


# ---------------------------------------------------------------------------------------------
# PR9 — the one-producer scan's REACH: a clone whose THROW guard is a module constant
# ---------------------------------------------------------------------------------------------
def test_PR9_a_clone_with_a_MODULE_LEVEL_guard_template_is_found() -> None:
    from test_task_guarded_shell_58 import guarded_shell_producers

    source = (
        '_ASSIGN_GUARD = "IF array::len(${var}) == 0 {{ THROW \'{msg}\' }}"\n'
        "class Ledger:\n"
        "    @staticmethod\n"
        "    def _guarded_append_fragment(row_id, *, event):\n"
        "        return ['LET $v = (UPDATE t SET provenance.events += [$ev] WHERE x)',\n"
        "                \"IF array::len($v) == 0 { THROW 'lost' }\"]\n"
        "    @staticmethod\n"
        "    def _assign_fragment(row_id, owner):\n"
        "        return ['LET $a = (UPDATE t SET owner = $o, provenance.events += [$e])',\n"
        "                _ASSIGN_GUARD.format(var='a', msg='lost')]\n"
    )
    found = guarded_shell_producers(source)
    assert "Ledger._assign_fragment" in found, found


# ---------------------------------------------------------------------------------------------
# PR10 — a ROUTINE claim loss must not emit an ERROR-level log record (it did not before 58)
# ---------------------------------------------------------------------------------------------
async def test_PR10_a_routine_claim_loss_logs_no_ERROR(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, _env = ledger58
    blocker = await create(ledger, "an open blocker")
    blocked = await create(ledger, "blocked", [blocker])
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        result = await ledger.claim_task(blocked, CLAIMANT)
    assert not result.claimed
    errors = [(r.name, r.getMessage()) for r in caplog.records if r.levelno >= logging.ERROR]
    assert not errors, errors


# ---------------------------------------------------------------------------------------------
# PR11 — the index rider must serve the PRODUCTION containment statements, not a hand-typed one
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "statement",
    [
        "SELECT record::id(id) AS id FROM task WHERE blocked_by CONTAINS $x",
        "SELECT count() FROM task WHERE blocked_by CONTAINS $x GROUP ALL",
        "SELECT record::id(id) AS id, blocked_by FROM task WHERE blocked_by CONTAINSANY [$x]",
    ],
    ids=["direct_dependents", "R1_closing_guard_count", "heal_containsany"],
)
async def test_PR11_production_containment_statements_are_index_served(
    ledger58: tuple[TaskLedger, SurrealEnv], statement: str
) -> None:
    import test_keeps_schema as keeps_schema

    walker = keeps_schema.TestTheKeeperIndexFires
    ledger, _env = ledger58
    blocker = await create(ledger, "a blocker")
    await create(ledger, "a dependent", [blocker])
    plan = await raw(ledger, f"{statement} EXPLAIN", {"x": blocker})
    assert not walker._scans_table(plan, TASK_TABLE), walker._operators(plan)


# ---------------------------------------------------------------------------------------------
# PR12 — the re-anchor note's ``at`` is the supersede's time, not a stale/constant stamp
# ---------------------------------------------------------------------------------------------
async def test_PR12_the_note_at_is_the_supersede_time(ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
    ledger, _env = ledger58
    old = await create(ledger, "X")
    dependent = await create(ledger, "Y", [old])
    before = datetime.now(UTC)
    await supersede(ledger, old)
    after = datetime.now(UTC)
    notes = [e for e in await events_of(ledger, dependent) if e.get("action") == ACTION_REANCHORED]
    stamp = datetime.fromisoformat(notes[0]["at"])
    assert before <= stamp <= after, (before, stamp, after)


# ---------------------------------------------------------------------------------------------
# PR13 — the WARN policy is SHARED: silencing SurrealStore._log_transaction_size silences the task WARN
# ---------------------------------------------------------------------------------------------
async def test_PR13_the_task_WARN_rides_the_ONE_telemetry_policy(
    ledger58: tuple[TaskLedger, SurrealEnv],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from loremaster.store.surreal import SurrealStore

    ledger, _env = ledger58
    old = await create(ledger, "a hub above the warn threshold")
    await bulk_seed_dependents(ledger, old, 300, tag="adv58warn")
    monkeypatch.setattr(SurrealStore, "_log_transaction_size", staticmethod(lambda *a, **k: None))
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await supersede(ledger, old)
    warned = [r for r in caplog.records if r.levelno == logging.WARNING and hasattr(r, "statement_count")]
    assert not warned, "the task ledger warned through a PRIVATE copy of the threshold policy"


# ---------------------------------------------------------------------------------------------
# PR14 — the hub cap follows the SHARED compose cap (mutate it; the accessor must move)
# ---------------------------------------------------------------------------------------------
async def test_PR14_the_accessor_follows_the_shared_hard_cap(
    ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger, _env = ledger58
    baseline = ledger.max_reanchor_dependents(0)
    monkeypatch.setattr(_txn, "TXN_STATEMENT_HARD_CAP", _txn.TXN_STATEMENT_HARD_CAP - 300)
    assert ledger.max_reanchor_dependents(0) == baseline - 100


# ---------------------------------------------------------------------------------------------
# PR15 — a legacy superseded_by LOOP must not hang the boot (bounded chain follow)
# ---------------------------------------------------------------------------------------------
async def test_PR15_a_superseded_by_loop_does_not_hang_the_boot(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    import asyncio

    ledger, env = ledger58
    first, second = "adv58suploopa00000000000000000", "adv58suploopb00000000000000000"
    await raw_seed_row(ledger, first, blocked_by=[], superseded_by=second)
    await raw_seed_row(ledger, second, blocked_by=[], superseded_by=first)
    straggler = "adv58suploopstraggler0000000000"
    await raw_seed_row(ledger, straggler, blocked_by=[first])
    await raw_relate(ledger, first, straggler)
    await asyncio.wait_for(_boot(env), timeout=60)
