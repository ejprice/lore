"""Packet 58 contract r2 — adversary-58's graded probes PR16–PR17, landed AST-EQUAL.

Source: batch 2 (md5 ``1328e035``), contract-58-r2.

*Scoped to the tree at ``ccdad34``, 2026-09-26.*  PR16 = MP2's harm (the accessor at K=3 must never
serve ``compose``'s bare cap error); PR17 = §DECISIONS 2 constructed (1300 legacy stragglers must not
fail the boot — amendment 3 §1's packer).  Provenance + AST receipt: ``REPORT-contract-58-r2.md``.
"""

from __future__ import annotations

import pytest
from _reanchor_58_support import (
    RETIRED_STATEMENT_CAP,
    ComposeSpy,
    assert_unpatched_row_cap,
    bulk_seed_dependents,
    column,
    create,
    ledger58,
    measure_heal_shape,
    new_ledger,
    raw_seed_row,
    shrunk_row_caps,
)
from _surreal_harness import SurrealEnv
from loremaster.store._txn import SurrealStoreError, TxnRowCapExceededError
from loremaster.tasks import TaskLedger

__all__ = ["ledger58", "shrunk_row_caps"]


# PR16 — WB2's HARM: with the accessor over-stating the cap at K=3, a supersede of exactly `cap`
# dependents must still be a TEACHING refusal or a success — never compose's bare count error.
@pytest.mark.usefixtures("shrunk_row_caps")
async def test_PR16_a_hub_at_the_accessors_cap_with_K3_is_never_the_bare_compose_error(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    k = 3
    cap = ledger.max_reanchor_dependents(k)
    old = await create(ledger, "the hub")
    blockers = [await create(ledger, f"successor blocker {i}") for i in range(k)]
    await bulk_seed_dependents(ledger, old, cap, tag="adv58k3cap")
    try:
        await ledger.supersede_task(
            old, subject="s", description="d", created_by="adv58", blocked_by=blockers
        )
    except SurrealStoreError as error:
        # ⚠ DUAL (contract r5, am-15 §8.2): by TYPE, not the retired text — no longer AST-equal to batch 2
        bare = (error, error.__cause__)
        assert not any(isinstance(link, TxnRowCapExceededError) for link in bare), (
            f"the derived cap ({cap} at K={k}) over-states the bound: compose's bare error served: {error}"
        )


# PR17 — DECISIONS 2 CONSTRUCTED: a large legacy straggler population vs the heal's ONE transaction.
@pytest.mark.usefixtures("shrunk_row_caps")
async def test_PR17_the_boot_heal_at_scale_does_not_fail_the_boot(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    head = await create(ledger, "the successor")
    legacy = "adv58scalelegacyblocker00000000"
    await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
    stragglers = await bulk_seed_dependents(ledger, legacy, 1300, tag="adv58scale")
    booted = new_ledger(env)
    try:
        await booted.ensure_ready()  # the probe's claim: a boot survives 1300 legacy stragglers
    finally:
        await booted.close()
    assert await column(ledger, stragglers[0]) == [head]


# L3 (contract r5, packet 58 amendment 15 §1.4; §8.1: REQUIRED, run WITHOUT the fixture): at the UNPATCHED row
# cap, a straggler population whose heal composes MORE rows than SDK3's retired 5 000-statement cap heals
# in ONE transaction. A build that never left the statement cap chunks it and passes every 5 000-shrunk pin.
async def test_L3_REAL_CAP_a_heal_past_the_RETIRED_statement_cap_is_ONE_transaction(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    assert_unpatched_row_cap()
    fixed, per = await measure_heal_shape(ledger, env, "l3shape")
    count = (RETIRED_STATEMENT_CAP - fixed) // per + 1
    head = await create(ledger, "the L3 successor")
    legacy = "l3scalelegacyblocker000000000000"
    await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
    stragglers = await bulk_seed_dependents(ledger, legacy, count, tag="l3scale")
    spy = ComposeSpy()
    booted = new_ledger(env)
    try:
        with spy.installed():
            await booted.ensure_ready()
    finally:
        await booted.close()
    chunks = spy.heal_rows()
    assert len(chunks) == 1 and chunks[0] > RETIRED_STATEMENT_CAP, (
        f"{count} one-blocker stragglers compose {fixed + per * count} heal rows (> the retired "
        f"{RETIRED_STATEMENT_CAP}) under the real row cap: ONE chunk expected, got {chunks}"
    )
    assert await column(ledger, stragglers[0]) == [head] and await column(ledger, stragglers[-1]) == [head]
    # r5.2 (am-16 §2.4, MP-4): the un-annotated rider at the size the contract builds, not only at 3 — a
    # `rows=` under-declaration switched on above some size slips the row bound and delays the WARN.
    assert spy.annotated_calls() == [], (
        f"(rows, statements) of transactions whose fragment_rows ≠ statement count at {count} stragglers: "
        f"{spy.annotated_calls()} — a `rows=` annotation on 58's fragments (am-15 §2)"
    )
