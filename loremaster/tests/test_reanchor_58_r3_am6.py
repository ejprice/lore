"""Packet 58 contract r3 — adversary-58-r2's amendment-6 probes, landed (am-17's rule), one re-keyed by am-7.

*Every claim in this file is scoped to the tree at ``c9e5eb8`` (branch ``feat/surreal-unification``),
2026-09-26, authored by ``contract-58-r3``.  "RED at HEAD" means RED at that commit.*

Source: ``REPORT-adversary-58-r2.md`` (``821be62``) §INSTRUMENTS ``test_adv58r2_am6_probes.py`` (md5
``d3f96789``).  Amendment 6 (``dcf6b0f``) FORK-3 (the tier table, deny-by-default ERROR) and FORK-4 (E11,
whole-column dedupe).  Every function is AST-equal to the adversary's EXCEPT
``test_P6_mutation_dropping_ONE_table_entry_moves_ONLY_that_tier``, whose dropped key follows amendment 7 §4's
re-key of ``_ROLLBACK_LOG_TIERS`` from PREFIX to CLASS (``REPORT-contract-58-r3.md`` §DEVIATIONS D-AM7KEY).
The per-THROW-text legs stay valid under am-7 unchanged: the classifier maps each marker to its class, and
the class carries the tier (the same information one step later — am-7 §4).  The GENERATED per-class form
lives in ``test_reanchor_58_r3_tiers.py``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from _reanchor_58_support import (
    ROLLBACK_EVENT,
    ApplyHook,
    boot,
    column,
    create,
    drive_to,
    edge_pairs,
    ledger58,
    new_ledger,
    raw_relate,
    raw_seed_row,
    successor_of,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.tasks import STATUS_BLOCKED, STATUS_DONE, IllegalTransitionError, TaskLedger

if TYPE_CHECKING:
    # ⚠ packet 58's RULED, not-yet-built symbol, named STATICALLY for the typecheck gate (lead #17055, the
    # #461 shape): a mypy error at HEAD owned by `scripts/pending_contracts.yaml` bound `packet-58-contract`,
    # which owns this file's RED@HEAD pytest legs too and self-destructs with the build.  Runtime-inert.
    from loremaster.store._txn import TxnCasLostError

    _RULED_58: tuple[object, ...] = (TxnCasLostError,)

__all__ = ["ledger58"]

#: am-6 FORK-3's table, TRANSCRIBED from the ruling (dcf6b0f) — the probe's oracle, not production's.
RULED_TIERS = [
    ("claim_lost:x", logging.DEBUG),
    ("governed_conflict:t:x", logging.WARNING),
    ("cas_lost: x", logging.WARNING),
    ("reanchor_straggler: x", logging.WARNING),
    ("heal_chunk: x", logging.WARNING),
    ("an unprefixed app throw", logging.ERROR),  # deny-by-default
]


async def _rollback_levels(ledger: TaskLedger, caplog: pytest.LogCaptureFixture, message: str) -> list[int]:
    caplog.clear()
    with caplog.at_level(logging.DEBUG), pytest.raises(_txn.SurrealStoreError):
        await _txn.execute_transaction(
            f"BEGIN;\nTHROW '{message}';\nCOMMIT;\n",
            {},
            acquire=ledger._ensure_connection,
            drop=ledger._drop_connection,
            url=ledger._url,  # noqa: SLF001
        )
    return [r.levelno for r in caplog.records if r.getMessage() == ROLLBACK_EVENT]


@pytest.mark.parametrize(
    ("message", "tier"), RULED_TIERS, ids=[m.split(":")[0].replace(" ", "_") for m, _ in RULED_TIERS]
)
async def test_P6_each_ruled_tier_and_the_deny_by_default(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture, message: str, tier: int
) -> None:
    ledger, _env = ledger58
    assert await _rollback_levels(ledger, caplog, message) == [tier]


async def test_P6_mutation_dropping_ONE_table_entry_moves_ONLY_that_tier(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """am-6 pin (iii): the table is the ONE source — drop `cas_lost:` and a lost transition race logs ERROR,
    while `reanchor_straggler:` stays WARNING."""
    ledger, env = ledger58
    table = dict(_txn._ROLLBACK_LOG_TIERS)  # noqa: SLF001 - am-6 names the table
    # ⚠ DEVIATION D-AM7KEY (REPORT-contract-58-r3.md §DEVIATIONS): amendment 7 §4 (01565f9) RE-KEYS the table
    # from the THROW-marker prefix to the CLASSIFIED CLASS, so the entry dropped is the class the `cas_lost:`
    # marker classifies to (resolved at CALL time: absent at HEAD, finding #133), never the prefix string.
    table.pop(getattr(_txn, "TxnCasLostError"))  # a ruled, not-yet-built name (mypy-clean at HEAD)
    monkeypatch.setattr(_txn, "_ROLLBACK_LOG_TIERS", table)
    task_id = await create(ledger, "raced")
    racer = new_ledger(env)
    hook = ApplyHook(ledger, lambda: racer.transition(task_id, STATUS_BLOCKED, actor="racer-am6"))
    caplog.clear()
    try:
        with hook.installed(), caplog.at_level(logging.DEBUG), pytest.raises(IllegalTransitionError):
            await ledger.transition(task_id, STATUS_BLOCKED, actor="worker-am6")
    finally:
        await racer.close()
    assert [r.levelno for r in caplog.records if r.getMessage() == ROLLBACK_EVENT] == [logging.ERROR]
    assert await _rollback_levels(ledger, caplog, "reanchor_straggler: x") == [logging.WARNING]


async def test_P6_E11_a_legacy_duplicate_collapses_WHOLE_column_and_the_claim_then_wins(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    """am-6 FORK-4 pin: Y raw [A, A, X] → supersede(X→X') → [A, X']; one A→Y, one X'→Y, no X→Y; the claim CAS
    on Y (A and X' done) WINS.  Control: [A, X] → [A, X']."""
    ledger, _env = ledger58
    blocker_a = await create(ledger, "A")
    old = await create(ledger, "X")
    y, control = "am6dupey" + "0" * 24, "am6ctrly" + "0" * 24
    await raw_seed_row(ledger, y, blocked_by=[blocker_a, blocker_a, old])
    await raw_seed_row(ledger, control, blocked_by=[blocker_a, old])
    for row in (y, control):
        await raw_relate(ledger, blocker_a, row)
        await raw_relate(ledger, old, row)
    successor = successor_of(await supersede(ledger, old))
    assert await column(ledger, y) == [blocker_a, successor]
    assert await column(ledger, control) == [blocker_a, successor]
    edges = [pair for pair in await edge_pairs(ledger) if pair[1] == y]
    assert sorted(edges) == sorted([(blocker_a, y), (successor, y)]), edges
    await drive_to(ledger, blocker_a, STATUS_DONE)
    await drive_to(ledger, successor, STATUS_DONE)
    assert (await ledger.claim_task(y, "claimant-am6")).claimed


async def test_P6_E11_through_the_boot_heal(ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
    ledger, env = ledger58
    blocker_a = await create(ledger, "A")
    head = await create(ledger, "X'")
    legacy = "am6legacyx" + "0" * 22
    await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
    y = "am6healdupe" + "0" * 21
    await raw_seed_row(ledger, y, blocked_by=[blocker_a, blocker_a, legacy])
    await raw_relate(ledger, blocker_a, y)
    await raw_relate(ledger, legacy, y)
    await boot(env)
    assert await column(ledger, y) == [blocker_a, head]
