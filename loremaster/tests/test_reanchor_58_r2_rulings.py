"""Packet 58 contract r2 — amendment 3's five decisions + adversary-58's remaining MISSING PINS.

*Every claim in this file is scoped to the tree at ``ccdad34`` (branch ``feat/surreal-unification``),
2026-09-26, authored by ``contract-58-r2``.  "RED at HEAD" means RED at that commit.*

Spec, later wins: the kickoff rulings (``c8d3241``) · amendment 1 (``f4e96b4``) · amendment 2
(``e0760fd``) · **amendment 3** (``docs/design/2026-09-26-packet58-amendment-3.md`` @ ``7266c1b``) —
§1 the heal chunk is sized by the HEAL's own composed count (a greedy packer; the supersede's accessor
and the packer are two consumers of ONE count; the accessor is K-aware); §2 a heal STORE fault RAISES,
only a chunk's DOMAIN rejection is isolated + WARNING + continue, order backfill → heal; §3 a claim
loss is a typed ``claim_lost:`` rollback logged at DEBUG, other THROW rollbacks at WARNING; §4 refuse
ONLY a cycle through X'; §5 a phantom (or cyclic) chain head is skipped + recorded, never a failure.
Grader: ``9f2f580:REPORT-adversary-58.md`` (§MISSING PINS MP2, MP9, MP13–MP18; §AM2).

⚠ Store law read first (``docs/reference/surrealdb-31-capabilities.md`` §3 every statement verified /
a THROW is a domain rejection, §4 ENFORCED rejects a phantom endpoint — the reason §5 exists, §5 no
hand-rolled retry).  Fixtures discriminate: hub and chunk sizes come from MEASURED compositions and the
derived accessor, never a literal; populations span ≥ 6 distinct superseded blockers where the ruling
names it; every negative carries a control.
"""

from __future__ import annotations

import ast
import asyncio
import importlib
import inspect
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from _reanchor_58_support import (
    ACTION_REANCHORED,
    CLAIMANT,
    HEAL_CHAIN_CYCLE_EVENT,
    HEAL_CHUNK_REJECTED_EVENT,
    HEAL_EVENT,
    HEAL_PHANTOM_HEAD_EVENT,
    ROLLBACK_EVENT,
    WORKER,
    ApplyHook,
    ComposeSpy,
    all_columns,
    assert_edge_mirrors_column_for_every_row,
    boot,
    bulk_seed_dependents,
    column,
    create,
    drive_to,
    edge_pairs,
    ledger58,
    measure_heal_shape,
    new_ledger,
    predicted_chunks,
    raw,
    raw_relate,
    raw_seed_row,
    seed_stragglers,
    shrunk_row_caps,
    snapshot,
    successor_of,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.store._txn import SurrealConnectionError, SurrealOutcomeUnknownError, SurrealStoreError
from loremaster.store.surreal_schema import TASK_TABLE
from loremaster.tasks import (
    STATUS_BLOCKED,
    STATUS_DONE,
    IllegalTransitionError,
    TaskCycleError,
    TaskLedger,
    TaskLedgerError,
)
from test_task_guarded_shell_58 import _docstring_nodes

__all__ = ["ledger58", "shrunk_row_caps"]

PACKAGE_ROOT = Path(importlib.import_module("loremaster").__file__ or "").parent
SHELL = "_guarded_append_fragment"


def _records(caplog: pytest.LogCaptureFixture, message: str) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.getMessage() == message]


async def _boot_logged(env: SurrealEnv, caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await boot(env)
    return list(caplog.records)


def _pad_the_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    """Append ONE harmless statement to every shell output (kickoff §1 rider ii's mutation, in-suite).

    ``LET $pad58r2 = NONE`` — NOT ``RETURN NONE``: measured on 3.2.4, a ``RETURN`` inside the composed
    ``BEGIN … COMMIT`` ends the transaction's work early, so the heal's rows silently stay stranded and
    the next boot heals them (the first measurement of this pin read c = [5, 9, 18], not linear)."""
    from loremaster.store._txn import TxnFragment

    original = getattr(TaskLedger, SHELL)

    def _padded(*args: Any, **kwargs: Any) -> Any:
        fragment = original(*args, **kwargs)
        return TxnFragment(statements=[*fragment.statements, "LET $pad58r2 = NONE"], params=fragment.params)

    monkeypatch.setattr(TaskLedger, SHELL, staticmethod(_padded), raising=True)


# =========================================================================== #
# §1 — the hub cap follows K ACROSS floor boundaries (adversary MP2 / PR2 / PR16)
# =========================================================================== #


async def _supersede_count(ledger: TaskLedger, dependents: int, successor_deps: int) -> int:
    """Composed ROW count (``fragment_rows``, am-15 §1.1) of a real supersede with ``dependents`` /
    ``successor_deps``."""
    old = await create(ledger, "X")
    for index in range(dependents):
        await create(ledger, f"dependent {index}", [old])
    blockers = [await create(ledger, f"successor blocker {i}") for i in range(successor_deps)]
    spy = ComposeSpy()
    with spy.installed():
        await supersede(ledger, old, blocked_by=blockers)
    assert spy.calls, "the supersede composed nothing"
    return spy.rows[-1]


class TestTheHubCapFollowsKAcrossFloorBoundaries:
    """RED at HEAD (no accessor).  Amendment 3 §1 (iv): *"the supersede accessor at K ∈ {0, 1, 2, 3, per,
    per+1} — cap+1 dependents at each K refused with the teaching, cap succeeds, and the served count
    equals compose's."*  K ∈ {0, 2} (the r1 contract) only discriminates a K-blind accessor when
    ``fixed ≢ 0 (mod per)`` — WB2 survived on a legit layout (fixed₀ = 6) and PR16 constructed the harm
    (compose's bare error at K = 3).  ``per`` is MEASURED, so ``K = per`` always crosses a floor."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    @pytest.mark.parametrize("k_spec", ["0", "1", "2", "3", "per", "per+1"])
    async def test_at_K_the_accessor_is_the_composed_cap_cap_succeeds_and_cap_plus_1_teaches(
        self, ledger58: tuple[TaskLedger, SurrealEnv], k_spec: str
    ) -> None:
        ledger, _env = ledger58
        per = await _supersede_count(ledger, 2, 0) - await _supersede_count(ledger, 1, 0)
        assert per > 0, (
            "a supersede with one more dependent composed NO more statements — nothing re-anchors the "
            "dependents (P58 Mission), so there is no per-dependent cost to derive a cap from"
        )
        k = {"per": per, "per+1": per + 1}.get(k_spec, int(k_spec) if k_spec.isdigit() else -1)
        c1 = await _supersede_count(ledger, 1, k)
        assert await _supersede_count(ledger, 2, k) - c1 == per, "per must not depend on K"
        fixed = c1 - per
        cap = (_txn.TXN_ROW_HARD_CAP - fixed) // per
        assert ledger.max_reanchor_dependents(k) == cap, (
            f"at K={k} the composed supersede is fixed={fixed} + {per}·N, so the derived cap is "
            f"{cap}; the accessor says {ledger.max_reanchor_dependents(k)} — it must BUILD the "
            f"fixed part for THIS K (amendment 3 §1: never a sampled constant)"
        )
        blockers = [await create(ledger, f"K blocker {i}") for i in range(k)]
        hub = await create(ledger, "the hub at the cap")
        seeded = await bulk_seed_dependents(ledger, hub, cap, tag=f"kcap{k_spec.replace('+', 'p')}x")
        result = await supersede(ledger, hub, blocked_by=blockers)
        assert sorted(result.reanchored) == sorted(seeded)
        over = await create(ledger, "the hub one past the cap")
        await bulk_seed_dependents(ledger, over, cap + 1, tag=f"kover{k_spec.replace('+', 'p')}x")
        before = await snapshot(ledger)
        with pytest.raises(TaskLedgerError) as caught:
            await supersede(ledger, over, blocked_by=blockers)
        message = str(caught.value)
        assert "nothing changed" in message.lower(), message
        # r5 (am-15 §8.2): compose's bare refusal by TYPE, never by the retired text
        assert not isinstance(caught.value, _txn.TxnRowCapExceededError), message
        assert not isinstance(caught.value.__cause__, _txn.TxnRowCapExceededError), message
        assert str(cap + 1) in message and str(cap) in message, message
        assert await snapshot(ledger) == before, "a refused hub supersede wrote something"


# =========================================================================== #
# §1 — the heal packs by its OWN composed count (MP16; am-2's defect PR19; mutation (v))
# =========================================================================== #


class TestTheHealPacksByItsOwnComposedCount:
    """RED at HEAD (no heal).  Amendment 3 §1 (i)/(iii)/(v)."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_cap_plus_1_stragglers_over_SIX_blockers_all_heal_in_ONE_boot_every_chunk_within_the_cap(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger, env = ledger58
        cap = ledger.max_reanchor_dependents(0)
        head, ids = await seed_stragglers(ledger, cap + 1, 6, "am3six")
        spy = ComposeSpy()
        with spy.installed():
            records = await _boot_logged(env, caplog)
        heal = _records(caplog, HEAL_EVENT)
        chunks = spy.heal_calls()
        assert len(heal) == 1 and getattr(heal[0], "count", None) == cap + 1, [
            (getattr(r, "count", None), getattr(r, "chunks", None)) for r in heal
        ]
        assert getattr(heal[0], "chunks", None) == len(chunks) >= 2, (
            f"the logged `chunks` must equal the heal transactions actually composed ({len(chunks)}); "
            f"{cap + 1} rows over six blockers cannot fit one {_txn.TXN_ROW_HARD_CAP}-row "
            f"transaction"
        )
        sizes = spy.heal_rows()  # r5: the ROW count of each heal chunk (am-15 §2)
        assert all(size <= _txn.TXN_ROW_HARD_CAP for size in sizes), sizes
        noisy = [
            # ⚠ DUAL (packet 58 contract r4 — amendment 12 §3 F-H, the same class): USED to also require
            # `r.name.startswith("loremaster")`; a clean heal emits no alarm from ANY logger.
            r.getMessage() for r in records
            if r.levelno >= logging.WARNING
            and not hasattr(r, "row_count")  # the size WARN is the WARN doing its job (am-2 (b))
        ]
        assert not noisy, f"a clean heal logged a warning/error: {noisy}"
        columns = await all_columns(ledger)
        assert all(columns[task_id] == [head] for task_id in ids), "a straggler was left stranded"
        await assert_edge_mirrors_column_for_every_row(ledger, where="six-blocker heal")
        before = await snapshot(ledger)
        await _boot_logged(env, caplog)
        assert not _records(caplog, HEAL_EVENT) and await snapshot(ledger) == before, (
            "the sweep did not converge: a second boot healed or wrote again"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_MUTATION_padding_the_shell_moves_the_packer_AND_the_accessor(
        self,
        ledger58: tuple[TaskLedger, SurrealEnv],
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """(v): *"pad the shell by one statement → the packer's chunk boundary AND the accessor move (two
        consumers of one count); a literal cap or chunk anywhere reds."*"""
        ledger, env = ledger58
        baseline_cap = ledger.max_reanchor_dependents(0)
        _pad_the_shell(monkeypatch)
        assert ledger.max_reanchor_dependents(0) < baseline_cap, "the accessor ignored the padded shell"
        fixed, per = await measure_heal_shape(ledger, env, "padshape")
        rows = baseline_cap + 1
        expected = predicted_chunks(rows, fixed, per, _txn.TXN_ROW_HARD_CAP)
        await seed_stragglers(ledger, rows, 1, "padone")
        records = await _boot_logged(env, caplog)
        heal = [r for r in records if r.getMessage() == HEAL_EVENT]
        assert len(heal) == 1 and getattr(heal[0], "count", None) == rows, heal
        assert getattr(heal[0], "chunks", None) == expected >= 2, (
            f"with the shell padded the heal chunk measures fixed={fixed}, per={per}: {rows} rows need "
            f"{expected} chunk(s); the packer produced {getattr(heal[0], 'chunks', None)} — a packer "
            f"that does not consume the shared count cannot follow the shell"
        )


# =========================================================================== #
# §2 — a heal STORE fault RAISES; a chunk's DOMAIN rejection is isolated; order backfill → heal
# =========================================================================== #


#: r5.2 (am-16 §2.5): stragglers one heal chunk fits under the in-test shrink, and the chunks a
#: ``2·fit + 1`` world therefore spans.
_DOOR_FIT = 4
_DOOR_CHUNKS = 3


def _exception_chain(error: BaseException) -> list[BaseException]:
    """``error`` and every exception it was raised from or during (``__cause__`` / ``__context__``)."""
    chain: list[BaseException] = []
    current: BaseException | None = error
    while current is not None and current not in chain:
        chain.append(current)
        current = current.__cause__ or current.__context__
    return chain


class _HealDoors:
    """Fault injection at every store door the heal opens AFTER the backfill (the sweep's own idiom).

    Arms when ``_backfill_blocks_edges`` returns (so it also PINS the ruled order: a heal that ran
    before the backfill opens no armed door and the control count is 0), then counts ``_query`` /
    ``_apply`` calls on the booting ledger; ``fault_at=k`` raises ``fault`` at the k-th armed call
    INSTEAD of calling (no side effect).  Bound: a heal that reaches the store by any seam other than
    the ledger's own ``_query`` / ``_apply`` is not counted (the FAILS_LOUD sweep, derived by seam
    identity, is the wider instrument — ``scripts/test_forgery_door_sweep.py``).
    """

    def __init__(self, fault_at: int | None, fault: Exception | None) -> None:
        self.fault_at = fault_at
        self.fault = fault
        self.armed = False
        self.calls = 0
        #: r5.2 (am-16 §2.5): the seam each armed door went through, in order (``_query`` read · ``_apply``
        #: write), so the control can show the heal's WRITE doors — one per chunk.
        self.seams: list[str] = []

    def install(self, ledger: TaskLedger) -> None:
        original_backfill = ledger._backfill_blocks_edges  # noqa: SLF001

        async def _backfill() -> None:
            await original_backfill()
            self.armed = True

        ledger._backfill_blocks_edges = _backfill  # type: ignore[method-assign]  # noqa: SLF001
        for name in ("_query", "_apply"):
            setattr(ledger, name, self._wrap(getattr(ledger, name), name))

    def _wrap(self, original: Callable[..., Awaitable[Any]], seam: str) -> Callable[..., Awaitable[Any]]:
        async def _door(*args: Any, **kwargs: Any) -> Any:
            if self.armed:
                self.calls += 1
                self.seams.append(seam)
                if self.calls == self.fault_at and self.fault is not None:
                    raise self.fault
            return await original(*args, **kwargs)

        return _door


class TestAHealStoreFaultIsLOUD:
    """RED at HEAD (no heal, so no armed door).  Amendment 3 §2: *"a STORE fault at any heal door (the
    straggler read, a chunk's apply) RAISES — loud, as every ``ensure_ready`` door must"*.  The door set
    is DERIVED from a control boot (every armed call), and each door is faulted at its own k."""

    async def _boot_with(self, env: SurrealEnv, doors: _HealDoors) -> None:
        booted = new_ledger(env)
        doors.install(booted)
        try:
            await booted.ensure_ready()
        finally:
            await booted.close()

    @pytest.mark.usefixtures("shrunk_row_caps")
    @pytest.mark.parametrize(
        "fault",
        [
            SurrealStoreError("injected-58r2 store fault"),
            SurrealConnectionError("injected-58r2 transport"),
            SurrealOutcomeUnknownError("injected-58r5.2 outcome unknown"),
        ],
        ids=["store", "transport", "outcome_unknown"],
    )
    async def test_every_heal_door_after_the_backfill_RAISES(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch, fault: Exception
    ) -> None:
        """r5.2 (packet 58 amendment 16 §2.5, MP-5): a store fault at ANY heal door raises, for EVERY chunk.

        The row cap is shrunk INSIDE the test so one chunk fits :data:`_DOOR_FIT` stragglers (cap = the
        measured ``fixed + fit·per``); the world is ``2·fit + 1`` stragglers — :data:`_DOOR_CHUNKS` chunks,
        so the second and third chunk's applies are doors too. Door k = 1, 2, … is faulted in turn on a
        FRESH world (an unfaulted boot first drains what the last faulted boot left, so every k boots the
        same world): the boot must RAISE, open no armed door after the fault (nothing more is written),
        and leave the world unhealed in part. The first k the boot never reaches is the CONTROL: it
        completes, heals all ``2·fit + 1``, and shows ≥ :data:`_DOOR_CHUNKS` WRITE-seam doors (or the leg
        fails naming the count). Fault classes: store, transport, and SDK3's
        ``SurrealOutcomeUnknownError``."""
        ledger, env = ledger58
        fixed, per = await measure_heal_shape(ledger, env, "doorshape")
        monkeypatch.setattr(_txn, "TXN_ROW_HARD_CAP", fixed + _DOOR_FIT * per, raising=True)
        population = 2 * _DOOR_FIT + 1
        k = 0
        while True:
            k += 1
            assert k < 50, "runaway door count"
            await boot(env)  # drain: heal whatever the previous faulted boot left behind
            head, stragglers = await seed_stragglers(ledger, population, 1, f"door{k:02d}")
            doors = _HealDoors(k, fault)
            try:
                await self._boot_with(env, doors)
            except SurrealStoreError as raised:
                assert fault in _exception_chain(raised), (
                    f"door k={k} raised {type(raised).__name__}: {raised} — not the injected fault "
                    f"(nor caused by it)"
                )
                assert doors.calls == k, (
                    f"after the fault at door k={k} the boot opened {doors.calls - k} more armed door(s) "
                    f"({doors.seams}) — a heal fault was swallowed and the heal went on writing"
                )
                columns = await all_columns(ledger)
                assert any(columns[s] != [head] for s in stragglers), (
                    f"door k={k} ({doors.seams[-1]}) faulted, yet every straggler healed — the fault was "
                    f"not at a heal door, or the heal re-ran past it"
                )
                continue
            break
        assert doors.calls == k - 1, f"the completing boot opened {doors.calls} doors, expected {k - 1}"
        writes = doors.seams.count("_apply")
        assert writes >= _DOOR_CHUNKS, (
            f"non-vacuity: the control boot opened {writes} write-seam door(s) ({doors.seams}); "
            f"{population} stragglers at fit {_DOOR_FIT} are {_DOOR_CHUNKS} chunks, one apply each"
        )
        columns = await all_columns(ledger)
        assert all(columns[s] == [head] for s in stragglers), (
            "CONTROL: the unfaulted boot heals every straggler (so the doors above were the heal's)"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_chunk_DOMAIN_rejection_is_isolated_WARNED_and_healed_next_boot(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        """*"a chunk domain rejection → chunk k's rows byte-identical, chunk k+1 healed, one WARNING, the
        boot completes, the next boot heals chunk k's rows"*.  The rejection is injected server-side (a
        ``DEFINE EVENT`` THROW on one straggler's UPDATE — a THROW is a domain rejection, store ref §3);
        the population is one row past a MEASURED chunk, so it spans exactly two chunks."""
        ledger, env = ledger58
        fixed, per = await measure_heal_shape(ledger, env, "rejshape")
        fit = (_txn.TXN_ROW_HARD_CAP - fixed) // per
        head, ids = await seed_stragglers(ledger, fit + 1, 1, "rej")
        victim = ids[len(ids) // 2]
        await raw(
            ledger,
            f"DEFINE EVENT reject58r2 ON TABLE {TASK_TABLE} WHEN $event = 'UPDATE' AND "
            f"record::id($after.id) = '{victim}' THEN {{ THROW 'injected-58r2-domain' }}",
        )
        before = {task_id: value for task_id, value in (await all_columns(ledger)).items() if task_id in ids}
        records = await _boot_logged(env, caplog)
        rejected = [r for r in records if r.getMessage() == HEAL_CHUNK_REJECTED_EVENT]
        assert len(rejected) == 1 and rejected[0].levelno == logging.WARNING, [
            (r.getMessage(), r.levelname) for r in rejected
        ]
        columns = await all_columns(ledger)
        stranded = sorted(t for t in ids if columns[t] != [head])
        assert victim in stranded and sorted(getattr(rejected[0], "rows", [])) == stranded, (
            f"the WARNING must name exactly the rejected chunk's rows ({len(stranded)} stranded)"
        )
        assert isinstance(getattr(rejected[0], "chunk", None), int)
        assert all(columns[t] == before[t] for t in stranded), "a rejected chunk's rows changed"
        assert 0 < len(stranded) < len(ids), "the OTHER chunk must heal in the same boot"
        heal = [r for r in records if r.getMessage() == HEAL_EVENT]
        assert len(heal) == 1 and getattr(heal[0], "count", None) == len(ids) - len(stranded), heal
        await raw(ledger, f"REMOVE EVENT reject58r2 ON TABLE {TASK_TABLE}")
        await _boot_logged(env, caplog)
        assert all(c == [head] for t, c in (await all_columns(ledger)).items() if t in ids)
        assert [getattr(r, "count", None) for r in _records(caplog, HEAL_EVENT)] == [len(stranded)]

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_the_heal_READS_what_the_backfill_minted_in_the_SAME_boot(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Order RULED backfill → heal (amendment 3 §2): a straggler seeded with NO edge → the backfill
        mints ``X→Y``, the heal then retires it; after the boot exactly one ``head→Y``, no ``X→Y``, and
        the backfill's mint record PRECEDES the heal's record in the same boot."""
        ledger, env = ledger58
        head = await create(ledger, "the successor")
        legacy = "orderlegacyblocker00000000000000"
        await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
        straggler = "orderstraggler000000000000000000"
        await raw_seed_row(ledger, straggler, blocked_by=[legacy])
        records = await _boot_logged(env, caplog)
        messages = [r.getMessage() for r in records]
        assert "task.backfill.blocks_edges_minted" in messages and HEAL_EVENT in messages, messages
        assert messages.index("task.backfill.blocks_edges_minted") < messages.index(HEAL_EVENT), (
            "the heal ran BEFORE the backfill — amendment 3 §2 rules backfill → heal"
        )
        pairs = [pair for pair in await edge_pairs(ledger) if pair[1] == straggler]
        assert pairs == [(head, straggler)], pairs


# =========================================================================== #
# §5 — a phantom chain head / a superseded_by cycle: skipped + recorded, never a failure (MP5, MP18)
# =========================================================================== #


class TestAPhantomChainHeadIsSkippedAndRECORDED:
    """RED at HEAD (no heal record).  Amendment 3 §5 + its CONTROL."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_phantom_head_skipped_recorded_every_boot_sibling_healed_and_hand_fix_heals(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger, env = ledger58
        phantom_head = "phantomheadnosuchrow000000000000"
        blocker = "phantomheadblocker00000000000000"
        await raw_seed_row(ledger, blocker, blocked_by=[], superseded_by=phantom_head)
        orphan = "phantomheadstraggler000000000000"
        await raw_seed_row(ledger, orphan, blocked_by=[blocker])
        await raw_relate(ledger, blocker, orphan)
        head = await create(ledger, "a real head")
        healable_blocker = "phantomsiblingblocker00000000000"
        await raw_seed_row(ledger, healable_blocker, blocked_by=[], superseded_by=head)
        healable = "phantomsiblingstraggler000000000"
        await raw_seed_row(ledger, healable, blocked_by=[healable_blocker])
        await raw_relate(ledger, healable_blocker, healable)
        orphan_before = [row for row in (await snapshot(ledger))[0] if orphan in row]
        records = await _boot_logged(env, caplog)
        phantoms = [r for r in records if r.getMessage() == HEAL_PHANTOM_HEAD_EVENT]
        assert len(phantoms) == 1 and phantoms[0].levelno == logging.WARNING, phantoms
        named = {k: getattr(phantoms[0], k, None) for k in ("task_id", "blocker_id", "phantom_head_id")}
        assert named == {"task_id": orphan, "blocker_id": blocker, "phantom_head_id": phantom_head}, named
        assert [getattr(r, "count", None) for r in _records(caplog, HEAL_EVENT)] == [1]
        assert await column(ledger, healable) == [head]
        assert [row for row in (await snapshot(ledger))[0] if orphan in row] == orphan_before, (
            "the phantom-headed straggler must be byte-identical (skipped, never half-healed)"
        )
        await _boot_logged(env, caplog)
        assert not _records(caplog, HEAL_EVENT), "the healed sibling must be silent on the second boot"
        assert len(_records(caplog, HEAL_PHANTOM_HEAD_EVENT)) == 1, (
            "a recorded bound is re-recorded every boot"
        )
        await raw_seed_row(ledger, phantom_head, blocked_by=[])
        await _boot_logged(env, caplog)
        assert await column(ledger, orphan) == [phantom_head], (
            "CONTROL: once the head exists the heal heals it"
        )
        assert [getattr(r, "count", None) for r in _records(caplog, HEAL_EVENT)] == [1]


class TestASupersededByCycleIsBoundedAndRECORDED:
    """RED at HEAD (no heal record).  MP18 + amendment 3 §5 (*"a chain that CYCLES … recorded as
    ``straggler_chain_cycle``"*): bounded time, the straggler untouched, NO note appended per boot."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_cycle_is_recorded_each_boot_and_never_rewrites_the_straggler(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger, env = ledger58
        first, second = "cyclea00000000000000000000000000", "cycleb00000000000000000000000000"
        await raw_seed_row(ledger, first, blocked_by=[], superseded_by=second)
        await raw_seed_row(ledger, second, blocked_by=[], superseded_by=first)
        straggler = "cyclestraggler000000000000000000"
        await raw_seed_row(ledger, straggler, blocked_by=[first])
        await raw_relate(ledger, first, straggler)
        before = await snapshot(ledger)
        for _boot_index in range(2):
            caplog.clear()
            with caplog.at_level(logging.DEBUG):
                await asyncio.wait_for(boot(env), timeout=60)
            cycles = _records(caplog, HEAL_CHAIN_CYCLE_EVENT)
            assert len(cycles) == 1 and cycles[0].levelno == logging.WARNING, cycles
            assert getattr(cycles[0], "task_id", None) == straggler
            assert not _records(caplog, HEAL_EVENT)
            assert await snapshot(ledger) == before, "a cyclic chain rewrote the straggler or appended a note"


# =========================================================================== #
# §3 — a claim LOSS is DEBUG and typed (MP14)
# =========================================================================== #


class TestAClaimLossIsDEBUGNeverAnAlarm:
    """RED at HEAD for the typed legs (no ``TxnClaimLostError``).  Amendment 3 §3."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_an_8_way_race_logs_NO_warning_or_error_for_its_7_losers(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger, env = ledger58
        task_id = await create(ledger, "contended")
        racers = [new_ledger(env) for _ in range(8)]
        caplog.clear()
        try:
            with caplog.at_level(logging.DEBUG):
                results = await asyncio.gather(
                    *(racer.claim_task(task_id, f"racer-{i}") for i, racer in enumerate(racers))
                )
        finally:
            for racer in racers:
                await racer.close()
        assert sum(r.claimed for r in results) == 1
        loud = [
            (r.name, r.levelname, r.getMessage())
            for r in caplog.records
            # ⚠ DUAL (packet 58 contract r3 — REPORT-contract-58-r3.md §DUAL R3-D3; amendment 8 §0 row
            # (2), F3): this filter USED to be `loremaster.store` — the DRIVER's loggers only.  Amendment 8
            # rules reading (b): *"a routine loss is not an alarm"* from ANY lore logger (an alarm from
            # `loremaster.tasks` is the same switched-off scanner), so the filter is every lore logger.
            # ⚠ DUAL (packet 58 contract r4 — amendment 12 §3 F-H, adversary-58-r3 W-F3-ROOT): the filter USED
            # to be `r.name.startswith("loremaster")` — a hand-set reach: seven WARNINGs per race on the ROOT
            # logger
            # (`logging.warning(...)`) passed it.  "A routine loss is not an alarm" is about what the run
            # EMITS, so
            # every record captured at the root, ANY logger name, is in scope.
            if r.levelno >= logging.WARNING
        ]
        assert not loud, f"a ROUTINE claim loss logged at WARNING/ERROR (amendment 3 §3): {loud}"
        debug = [r for r in _records(caplog, ROLLBACK_EVENT) if r.levelno == logging.DEBUG]
        assert len(debug) == 7, (
            f"each of the 7 losers' rolled-back claim must be recorded at DEBUG — got {len(debug)}"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_CONTROL_a_lost_TRANSITION_race_still_logs_at_WARNING(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger, env = ledger58
        task_id = await create(ledger, "raced")
        racer = new_ledger(env)

        async def _racer_moves_it() -> None:
            await racer.transition(task_id, STATUS_BLOCKED, actor="racer-58r2")

        hook = ApplyHook(ledger, _racer_moves_it)
        caplog.clear()
        try:
            with hook.installed(), caplog.at_level(logging.DEBUG), pytest.raises(IllegalTransitionError):
                await ledger.transition(task_id, STATUS_BLOCKED, actor=WORKER)
        finally:
            await racer.close()
        assert hook.fired
        levels = [r.levelno for r in _records(caplog, ROLLBACK_EVENT)]
        assert levels == [logging.WARNING], (
            f"a lost TRANSITION race is a domain decision worth seeing: WARNING, never ERROR, never "
            f"DEBUG (amendment 3 §3) — got {[logging.getLevelName(level) for level in levels]}"
        )

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_the_ledger_catches_the_TYPE_never_the_text(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Re-type every domain rejection as a plain ``TxnDomainRejectionError`` at the driver's ONE
        mapping helper: a claim LOSS is then no longer a ``TxnClaimLostError``, so a ledger that catches
        the type must RAISE (it cannot recognise the loss) — a ledger that matches the marker TEXT would
        still serve a loss.  Control: unpatched, the same loss is a ``ClaimResult``."""
        ledger, _env = ledger58
        blocked = await create(ledger, "blocked", [await create(ledger, "an open blocker")])
        assert (await ledger.claim_task(blocked, CLAIMANT)).claimed is False, "CONTROL: a loss is a RESULT"
        from loremaster.store._txn import TxnDomainRejectionError

        # r5 re-base (66 / 63c-i-a): the ONE mapping helper is now called with ``kind=`` (and constructors
        # take ``error_class=`` / ``kind=``) — the stand-in accepts both and still erases the type.
        monkeypatch.setattr(
            _txn,
            "_domain_rejection_error",
            lambda _label, message, **_typed: TxnDomainRejectionError(message),
        )
        with pytest.raises(TxnDomainRejectionError):
            await ledger.claim_task(blocked, CLAIMANT)

    def test_the_claim_lost_marker_is_ONE_literal_per_side(self) -> None:
        """*"the marker→type mapping lives ONCE in ``_txn`` (an AST pin: ``claim_lost`` appears in
        ``tasks.py`` only as the throw_message constant and in ``_txn`` only in the classifier)"*.
        Derived over every production tree (``_logging_fixtures.parse_production_trees`` — the ONE
        whole-tree parser; the reach floor: ``_txn`` must be found)."""
        from _logging_fixtures import parse_production_trees

        hits: dict[str, int] = {}
        for key, tree in parse_production_trees().items():  # THE one tree parser (lead #17068)
            prose = _docstring_nodes(tree)  # a docstring MENTIONING the marker is prose, not a producer
            count = sum(
                1 for node in ast.walk(tree)
                if id(node) not in prose
                and isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and "claim_lost" in node.value
            )
            if count:
                hits[key] = count
        txn, tasks = "loremaster/loremaster/store/_txn.py", "loremaster/loremaster/tasks.py"
        assert hits.get(txn) == 1, f"_txn must carry the marker exactly once: {hits}"
        assert set(hits) <= {txn, tasks} and hits.get(tasks, 0) <= 1, hits


class TestTheClaimLostHierarchy:
    """RED at HEAD (no ``TxnClaimLostError``).  Amendment 4's hierarchy pin, KEPT by amendment 5 §2: the
    typed claim catch is safe BY TYPE only while ``TxnClaimLostError`` sits in a subtree that cannot hold
    exhausted contention; a re-parenting flips it into the §HELD index's door set by derivation.  (The
    typed EXACT SET is 63c-i-a a28b's ``test_retry_seam._TYPED_CAS_CATCHES``; the runtime ∀ is the driver
    SEAM, ``test_reanchor_58_r3_cas_seam.py`` + ``test_reanchor_58_r4_state.py`` — ⚠ DUAL (packet 58 contract
    r4, amendment 12 §3 R-2): this sentence USED to point at the DELETED
    ``test_reanchor_58_r2_cas_runtime.py``
    and the withdrawn r2 §HELD re-key.)"""

    def test_the_claim_lost_class_cannot_hold_exhausted_contention(self) -> None:
        from loremaster.store._txn import TxnContentionExhaustedError, TxnDomainRejectionError

        claim_lost = getattr(_txn, "TxnClaimLostError")  # noqa: B009 - absent before 58's build
        assert not issubclass(TxnContentionExhaustedError, claim_lost)
        assert issubclass(claim_lost, TxnDomainRejectionError)


# =========================================================================== #
# §4 — a legacy loop through ANOTHER blocker does not block the supersede (MP8 + its two controls)
# =========================================================================== #


class TestOnlyACycleThroughXPrimeIsRefused:
    """PR8 (``test_reanchor_58_r2_probes.py``) pins the success leg; this adds amendment 3 §4's
    "untouched" leg and its two refusal CONTROLS."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_the_legacy_loop_is_untouched_and_Y_follows_the_work(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        old = await create(ledger, "X")
        loop_z, loop_y = "legacyloopz000000000000000000000", "legacyloopy000000000000000000000"
        await raw_seed_row(ledger, loop_z, blocked_by=[loop_y])
        await raw_seed_row(ledger, loop_y, blocked_by=[old, loop_z])
        await raw_relate(ledger, loop_y, loop_z)
        await raw_relate(ledger, loop_z, loop_y)
        await raw_relate(ledger, old, loop_y)
        successor = successor_of(await supersede(ledger, old))
        assert await column(ledger, loop_y) == [successor, loop_z]
        assert await column(ledger, loop_z) == [loop_y], "the legacy loop member was touched"

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_CONTROL_a_successor_explicitly_blocked_by_its_dependent_is_REFUSED_whole(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        old = await create(ledger, "X")
        dependent = await create(ledger, "Y", [old])
        before = await snapshot(ledger)
        with pytest.raises(TaskCycleError):
            await supersede(ledger, old, blocked_by=[dependent])
        assert await snapshot(ledger) == before

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_CONTROL_an_INHERITED_blocker_that_closes_a_loop_through_X_prime_is_REFUSED(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """X ⇄ Y legacy loop (raw): X' INHERITS ``blocked_by = [Y]`` (#174 sentinel) and Y is rewired to
        X' — ``Y → X' → Y`` passes THROUGH X', so it is the supersede's own cycle and is refused."""
        ledger, _env = ledger58
        loop_x, loop_y = "inheritloopx0000000000000000000a", "inheritloopy0000000000000000000a"
        await raw_seed_row(ledger, loop_x, blocked_by=[loop_y])
        await raw_seed_row(ledger, loop_y, blocked_by=[loop_x])
        await raw_relate(ledger, loop_y, loop_x)
        await raw_relate(ledger, loop_x, loop_y)
        before = await snapshot(ledger)
        with pytest.raises(TaskCycleError):
            await supersede(ledger, loop_x)
        assert await snapshot(ledger) == before


# =========================================================================== #
# MP13 — every RELATE in the supersede comes from the shared ``_relate_fragment`` (D9's false prose)
# =========================================================================== #


class TestEveryRELATEComesFromTheSharedFragment:
    """RED at HEAD (no dependent RELATEs to count).  K16 (dependents' ``X'→Y`` RELATEs hand-rolled
    beside the shared seam) survived the r1 contract: D9's pin is PRESENCE-only.  Spy both ``compose`` and
    ``TaskLedger._relate_fragment``: every RELATE statement the supersede composes must be one the shared
    fragment produced, and the counts must agree."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_the_supersede_composes_only_shared_fragment_RELATEs(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ledger, _env = ledger58
        old = await create(ledger, "X")
        for index in range(3):
            await create(ledger, f"Y{index}", [old])
        blockers = [await create(ledger, f"B{i}") for i in range(2)]
        produced: list[str] = []
        original = TaskLedger._relate_fragment  # noqa: SLF001

        def _spy(*args: Any, **kwargs: Any) -> Any:
            fragment = original(*args, **kwargs)
            produced.extend(fragment.statements)
            return fragment

        monkeypatch.setattr(TaskLedger, "_relate_fragment", staticmethod(_spy), raising=True)
        spy = ComposeSpy()
        with spy.installed():
            await supersede(ledger, old, blocked_by=blockers)
        relates = [s for s in spy.calls[-1][0] if re.match(r"\s*RELATE\b", s)]
        assert len(relates) == 3 + 2, relates
        assert all(s in produced for s in relates), (
            f"a RELATE reached the transaction that `_relate_fragment` never produced: "
            f"{[s for s in relates if s not in produced]}"
        )


# =========================================================================== #
# MP9 — the RUNTIME one-producer pin (the AST scan's reach is source text; this is the transaction)
# =========================================================================== #


@dataclass(frozen=True)
class _Spec:
    """A ``TaskSpecLike`` item for ``create_many`` (subject / description / blocked_by)."""

    subject: str
    description: str
    blocked_by: list[str]


_WRITE_VERB = re.compile(r"\b(UPDATE|UPSERT)\b")
_LET_WRITE = re.compile(r"LET\s+\$(\w+)\s*=\s*\(\s*(UPDATE|UPSERT|DELETE|CREATE|INSERT|RELATE)\b")


def _apply_callers() -> set[str]:
    """Every ``TaskLedger`` method whose body calls ``self._apply`` — DERIVED from the AST."""
    tree = ast.parse((PACKAGE_ROOT / "tasks.py").read_text(encoding="utf-8"))
    callers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "TaskLedger":
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "_apply"
                    for call in ast.walk(method)
                ):
                    callers.add(method.name)
    return callers


class TestEveryComposedGuardedWriteCameFromTheShell:
    """RED at HEAD (``_guarded_append_fragment`` absent).  MP9: WB12 (a 4th hand-rolled guarded append
    whose THROW template is a MODULE CONSTANT) escaped the per-function AST scan.  This pin watches the
    TRANSACTION instead of the source: while driving every task write verb, every ``UPDATE``/``UPSERT``
    statement ``compose`` receives must be one the shell produced, and a THROW the shell did not produce
    may not read a LET-bound WRITE.  Reach is a CHECKED variable: the set of ``TaskLedger`` methods that
    call ``_apply`` is DERIVED from the AST and must equal the set this pin OBSERVED composing."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_every_verb_composes_guarded_writes_only_through_the_shell(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ledger, env = ledger58
        shell_statements: set[str] = set()
        original = getattr(TaskLedger, SHELL)

        def _shell(*args: Any, **kwargs: Any) -> Any:
            fragment = original(*args, **kwargs)
            shell_statements.update(fragment.statements)
            return fragment

        monkeypatch.setattr(TaskLedger, SHELL, staticmethod(_shell), raising=True)
        observed: dict[str, list[list[str]]] = {}
        tasks_module = importlib.import_module("loremaster.tasks")
        real_compose = tasks_module.compose

        def _compose(*fragments: Any) -> Any:
            caller = next(
                (frame.function for frame in inspect.stack()[1:]
                 if frame.function != "_apply" and isinstance(frame.frame.f_locals.get("self"), TaskLedger)),
                "<unknown>",
            )
            observed.setdefault(caller, []).append([s for f in fragments for s in f.statements])
            return real_compose(*fragments)

        monkeypatch.setattr(tasks_module, "compose", _compose, raising=True)
        # Drive every write verb.
        done_blocker = await create(ledger, "a blocker to finish")
        await drive_to(ledger, done_blocker, STATUS_DONE)
        claimable = await create(ledger, "claimable", [done_blocker])
        assert (await ledger.claim_task(claimable, CLAIMANT)).claimed
        assert not (await ledger.claim_task(claimable, "second-claimant-58r2")).claimed
        specs: list[Any] = [_Spec("batch a", "d", []), _Spec("batch b", "d", [done_blocker])]
        await ledger.create_many(
            specs,
            created_by="batch-58r2",
        )
        old = await create(ledger, "X")
        await create(ledger, "Y", [old])
        await supersede(ledger, old)
        head = await create(ledger, "a head")
        legacy = "runtimelegacy0000000000000000000"
        await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
        await raw_seed_row(ledger, "runtimestraggler0000000000000000", blocked_by=[legacy])
        booted = new_ledger(env)
        try:
            await booted.ensure_ready()  # backfill mints the straggler's edge, the heal re-anchors it
        finally:
            await booted.close()
        derived = _apply_callers()
        assert derived <= set(observed), (
            f"reach: TaskLedger methods that call `_apply` = {sorted(derived)}; this pin drove "
            f"{sorted(observed)}. A method in the derived set that no leg drives is UNCOVERED — add a leg"
        )
        for caller, transactions in observed.items():
            for statements in transactions:
                writes = [s for s in statements if _WRITE_VERB.search(s)]
                rogue = [s for s in writes if s not in shell_statements]
                assert not rogue, f"{caller}: a guarded write NOT produced by the shell: {rogue}"
                bound = {m.group(1) for s in statements for m in [_LET_WRITE.search(s)] if m}
                for statement in statements:
                    if "THROW" in statement and statement not in shell_statements:
                        read = set(re.findall(r"\$(\w+)", statement)) & bound
                        assert not read, (
                            f"{caller}: a hand-rolled THROW guards a LET-bound write: {statement}"
                        )


# =========================================================================== #
# MP17 — the FAKE re-anchors in lockstep (the house parity idiom)
# =========================================================================== #


class TestTheFakeReanchorsInLockstepWithTheReal:
    """RED at HEAD (the fake's supersede returns ``str``).  Adversary P5: removing the fake's §HELD
    re-anchor loop left 1299 tests green — no test drove a supersede-with-dependents through the fake."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    @pytest.mark.parametrize("kind", ["fake", "real"])
    async def test_a_done_X_reanchors_and_reblocks_on_both(
        self, ledger58: tuple[TaskLedger, SurrealEnv], kind: str
    ) -> None:
        if kind == "fake":
            from _task_fakes import FakeTaskLedger

            subject: Any = FakeTaskLedger()
        else:
            subject, _env = ledger58
        old = await subject.create_task("X", "d", blocked_by=[], created_by="creator-58r2")
        await subject.transition(old, STATUS_BLOCKED, actor=WORKER)
        await subject.transition(old, "in_progress", actor=WORKER)
        await subject.transition(old, STATUS_DONE, actor=WORKER, summary="done")
        dependent = await subject.create_task("Y", "d", blocked_by=[old], created_by="creator-58r2")
        result = await subject.supersede_task(old, subject="X2", description="d", created_by="sup-58r2")
        assert list(result.reanchored) == [dependent] and list(result.reblocked) == [dependent], kind
        assert (await subject.get_task(dependent)).blocked_by == [result.successor_id], kind
        notes = [
            e for e in (await subject.get_task(dependent)).provenance.get("events", [])
            if e.get("action") == ACTION_REANCHORED
        ]
        assert len(notes) == 1, kind
        assert notes[0].get("from") == old and notes[0].get("to") == result.successor_id, kind


# =========================================================================== #
# MP15 — amendment 2 (a)'s remaining legs (PR20 lands the owner=/owner+status= pair)
# =========================================================================== #


class TestAHeldSupersededRowUnderOwnerQueries:
    """RED at HEAD for the ``blocked=False`` leg (#130 not built).  Amendment 2 (a): *"``query owner=alice
    blocked=False`` — Y is NOT claimable-partition material (superseded) → excluded; ``get Y`` serves it
    decorated; a ``transition`` by alice → ``IllegalTransitionError`` naming the supersession"*."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_blocked_False_excludes_it_get_serves_it_and_the_holder_cannot_transition_it(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        held = await create(ledger, "Y — held, then reframed")
        kept = await create(ledger, "Z — held")
        assert (await ledger.claim_task(held, CLAIMANT)).claimed
        assert (await ledger.claim_task(kept, CLAIMANT)).claimed
        successor = successor_of(await supersede(ledger, held))
        partition = {t.id for t in await ledger.query_tasks(owner=CLAIMANT, blocked=False)}
        assert held not in partition, sorted(partition)
        assert (await ledger.get_task(held)).superseded_by == successor
        with pytest.raises(IllegalTransitionError) as caught:
            await ledger.transition(held, "in_progress", actor=CLAIMANT)
        assert successor in str(caught.value) or "supersed" in str(caught.value).lower(), str(caught.value)

