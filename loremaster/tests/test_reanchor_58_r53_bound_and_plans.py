"""Packet 58 contract r5.3 — amendment 17 §6.1 (the heal chunk's bound) and §9.4 (both edge DELETEs, by plan).

*Every claim in this file is scoped to the tree at ``9e2f59d`` + builder-58-1's uncommitted build (branch
``feat/surreal-unification``), 2026-11-09, authored by ``contract-58-r53``. "RED at HEAD" means RED on that
tree.*

Spec: ``docs/design/2026-11-09-packet58-amendment-17.md`` §2, §6.1, §9.2–§9.4.

* **The bound (§2 / §6.1).** The boot heal packs its chunks against ``min(_txn.TXN_ROW_WARN_THRESHOLD,
  _txn.TXN_ROW_HARD_CAP)``, both read live; the weight stays ``_txn.fragment_rows``. The rule is stated
  ONCE for the
  tests (:func:`_reanchor_58_support.heal_chunk_bound`) and every ``fit`` here is derived from it and from
  the heal
  shape MEASURED at ``compose`` — never a literal row count.
  - leg 1, WARN below hard (the 5 000 / 800 shrink): ``2·fit + 1`` stragglers heal in exactly the greedy
    packer's
    chunks, each at most 800 rows;
  - leg 2, read live: shrinking the WARN threshold by ``per·d`` drops ``fit`` by exactly ``d``, boot to boot;
  - leg 3, hard below WARN: the existing ``_HEAL_DRIVER_FIT`` world (``test_reanchor_58_r4_state.py``) and
    the door
    world (``test_reanchor_58_r2_rulings.py::TestAHealStoreFaultIsLOUD``), which now ASSERT that precondition;
  - leg 4, the real constants once: one past a full chunk heals in exactly two chunks, the first at the
    WARN bound.
* **The DELETEs (§9.4).** No statement the supersede or the heal sends iterates the whole ``blocks`` table.
  Each
  leg takes the edge DELETE from the transaction the ledger hands its ONE write door (``TaskLedger._apply``),
  found by its bound ``RecordID`` parameters — never by its text — EXPLAINs it over the pre-write world, and
  asserts: no ``blocks`` table iteration; ``Iterate Record`` count == the anchor record's own degree; nothing
  deleted by the EXPLAIN. Each leg carries its C+ control: the table-anchored form over the same world DOES
  trip
  the walker, and a SELECT over the same table trips its other arm.

Stated bound (am-17 §9.4): ``Iterate Record`` / ``Iterate Table`` are engine-3.3.5 plan vocabulary; an engine
upgrade that renames them reds the C+ control first.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

import pytest
from _governed_contract import iterated_records, scans_table
from _reanchor_58_support import (
    SHRUNK_ROW_HARD_CAP,
    SHRUNK_ROW_WARN_THRESHOLD,
    UNPATCHED_ROW_WARN_THRESHOLD,
    ComposeSpy,
    assert_edge_mirrors_column_for_every_row,
    assert_unpatched_row_cap,
    boot,
    bulk_seed_dependents,
    column,
    create,
    heal_chunk_bound,
    ledger58,
    measure_heal_shape,
    new_ledger,
    predicted_chunks,
    raw,
    raw_relate,
    raw_seed_row,
    seed_stragglers,
    shrunk_row_caps,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import TaskLedger
from surrealdb import RecordID

__all__ = ["ledger58", "shrunk_row_caps"]  # imported fixtures USED by name — keep ruff from pruning them

#: §6.1 leg 2: how many rows' worth (``per·d``) the WARN threshold is shrunk by inside the leg.
_LIVE_READ_DELTA = 3
#: §9.4: the hub's own dependents (N) and the unrelated edges under another blocker (E ≥ 20).
_HUB_DEPENDENTS = 5
_UNRELATED_EDGES = 25
#: §9.4 heal leg: the superseded blocker's OTHER dependents (≥ 5), so a blocker-anchored DELETE (V2) iterates
#: more records than the dependent's own blocker count (2).
_OTHER_DEPENDENTS_OF_THE_OLD_BLOCKER = 6
#: A SurrealQL parameter reference in a statement — how a statement names a bound parameter (``$name``).
_PARAMETER_REFERENCE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


# =========================================================================== #
# §6.1 — the heal chunk's bound: min(WARN threshold, hard cap), read live
# =========================================================================== #


async def _heal_rows_of_one_boot(env: SurrealEnv) -> list[int]:
    """The ROW count of every boot-heal chunk ONE boot composes (``ComposeSpy`` on ``compose``)."""
    spy = ComposeSpy()
    with spy.installed():
        await boot(env)
    return spy.heal_rows()


class TestTheHealChunkBoundIsTheWarnThresholdUnderTheHardCap:
    """am-17 §2 / §6.1: the packer's ``max_size`` is ``min(TXN_ROW_WARN_THRESHOLD, TXN_ROW_HARD_CAP)``, read
    live. RED on builder-58-1's tree (its packer is at the hard cap)."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_WARN_below_hard_every_heal_chunk_is_within_the_WARN_threshold_in_the_greedy_chunks(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """Leg 1 (the F-RB-5 world, 800 under 5 000): ``2·fit + 1`` one-blocker stragglers → exactly
        ``[fixed + per·fit, fixed + per·fit, fixed + per]`` heal rows (three chunks, each ≤ 800).

        Kills a packer still at the hard cap: ``2·fit + 1`` rows price at about twice 800, under 5 000, so
        that
        packer composes ONE chunk of more than 800 rows."""
        ledger, env = ledger58
        assert heal_chunk_bound() == SHRUNK_ROW_WARN_THRESHOLD < SHRUNK_ROW_HARD_CAP, (
            "leg 1's world must hold the WARN threshold BELOW the hard cap"
        )
        fixed, per = await measure_heal_shape(ledger, env, "r53wshape")
        fit = (heal_chunk_bound() - fixed) // per
        rows = 2 * fit + 1
        assert fixed + per * rows <= SHRUNK_ROW_HARD_CAP, (
            f"non-vacuity: the whole population ({fixed + per * rows} rows) must fit ONE hard-cap chunk, "
            f"else a "
            f"hard-cap packer would chunk it too"
        )
        head, ids = await seed_stragglers(ledger, rows, 1, "r53w")
        sizes = await _heal_rows_of_one_boot(env)
        assert sizes == [fixed + per * fit, fixed + per * fit, fixed + per], (
            f"{rows} one-blocker stragglers (fixed={fixed}, per={per}, fit={fit} under the "
            f"{heal_chunk_bound()}-row chunk bound): the heal composed {sizes} — a packer at the "
            f"{_txn.TXN_ROW_HARD_CAP}-row hard cap composes ONE chunk of {fixed + per * rows}"
        )
        assert len(sizes) == predicted_chunks(rows, fixed, per, heal_chunk_bound())
        assert all(size <= SHRUNK_ROW_WARN_THRESHOLD for size in sizes), sizes
        for task_id in (ids[0], ids[fit], ids[-1]):  # one row from each chunk healed
            assert await column(ledger, task_id) == [head], task_id

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_the_WARN_threshold_is_read_LIVE_shrinking_it_by_per_d_drops_fit_by_exactly_d(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Leg 2 (am-15 L4's form): two boots in one leg, ``fit + 1`` fresh stragglers each. Boot A at the
        shrunk WARN → ``[fixed + per·fit, fixed + per]``; then ``TXN_ROW_WARN_THRESHOLD −= per·d`` and boot
        B →
        ``[fixed + per·(fit − d), fixed + per·(d + 1)]``.

        Kills a copied value (an import-time ``10_000`` or a ``from _txn import`` copy: boot A packs at the
        hard cap) and a value read once and cached (boot B packs as boot A did)."""
        ledger, env = ledger58
        fixed, per = await measure_heal_shape(ledger, env, "r53lshape")
        fit = (heal_chunk_bound() - fixed) // per
        assert fit > _LIVE_READ_DELTA + 1, f"fit {fit} too small for d = {_LIVE_READ_DELTA}"
        head_a, ids_a = await seed_stragglers(ledger, fit + 1, 1, "r53la")
        boot_a = await _heal_rows_of_one_boot(env)
        assert boot_a == [fixed + per * fit, fixed + per], (
            f"boot A ({fit + 1} stragglers, bound {heal_chunk_bound()}): heal rows {boot_a}"
        )
        monkeypatch.setattr(
            _txn, "TXN_ROW_WARN_THRESHOLD", _txn.TXN_ROW_WARN_THRESHOLD - per * _LIVE_READ_DELTA, raising=True
        )
        assert heal_chunk_bound() == SHRUNK_ROW_WARN_THRESHOLD - per * _LIVE_READ_DELTA
        head_b, ids_b = await seed_stragglers(ledger, fit + 1, 1, "r53lb")
        boot_b = await _heal_rows_of_one_boot(env)
        assert boot_b == [fixed + per * (fit - _LIVE_READ_DELTA), fixed + per * (_LIVE_READ_DELTA + 1)], (
            f"boot B: the WARN threshold was shrunk by per·d = {per * _LIVE_READ_DELTA} rows, so fit must "
            f"drop "
            f"from {fit} to {fit - _LIVE_READ_DELTA}; heal rows {boot_b} (boot A: {boot_a}) — the packer "
            f"did not "
            f"read the threshold LIVE"
        )
        assert await column(ledger, ids_a[-1]) == [head_a] and await column(ledger, ids_b[-1]) == [head_b]

    async def test_REAL_CONSTANTS_one_past_a_full_chunk_heals_in_TWO_chunks_the_first_at_the_WARN_bound(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """Leg 4 (run WITHOUT the shrink): the shipped constants, once. ``fit = (WARN − fixed) // per``
        with the
        heal shape measured at ``compose``; ``fit + 1`` one-blocker stragglers → heal rows exactly
        ``[fixed + per·fit, fixed + per]``. (am-17 §6.1 says 2,501 stragglers: that is ``fit + 1`` at the
        measured shape; the count is derived here, never spelled.)

        Kills a packer at the 50 000-row hard cap (ONE chunk) and any other bound than the shipped WARN value.
        L3 (``test_reanchor_58_r2_scale.py``, ONE transaction above the retired 5 000) is unchanged and still
        kills a surviving 5 000."""
        ledger, env = ledger58
        hard = assert_unpatched_row_cap()
        assert _txn.TXN_ROW_WARN_THRESHOLD == UNPATCHED_ROW_WARN_THRESHOLD, "leg 4 inherited a WARN shrink"
        assert heal_chunk_bound() == UNPATCHED_ROW_WARN_THRESHOLD < hard, (
            "the shipped constants must hold the WARN threshold below the hard cap"
        )
        fixed, per = await measure_heal_shape(ledger, env, "r53rshape")
        fit = (heal_chunk_bound() - fixed) // per
        count = fit + 1
        assert heal_chunk_bound() < fixed + per * count <= hard, (
            f"non-vacuity: {count} stragglers ({fixed + per * count} rows) must exceed ONE chunk and fit the "
            f"hard cap"
        )
        head, ids = await seed_stragglers(ledger, count, 1, "r53r")
        sizes = await _heal_rows_of_one_boot(env)
        assert sizes == [fixed + per * fit, fixed + per], (
            f"{count} one-blocker stragglers at the shipped constants (fixed={fixed}, per={per}, "
            f"fit={fit} under "
            f"the {heal_chunk_bound()}-row bound): heal rows {sizes} — a packer at the {hard}-row hard cap "
            f"composes ONE chunk of {fixed + per * count}"
        )
        assert await column(ledger, ids[0]) == [head] and await column(ledger, ids[-1]) == [head]


# =========================================================================== #
# §9.4 — both edge DELETEs, by what their plan iterates
# =========================================================================== #


def _binds(params: dict[str, Any], statement: str, record: RecordID) -> bool:
    """True iff ``statement`` references a parameter whose bound VALUE is ``record`` (the parameter, not the
    statement's form, identifies it — am-17 §9.4, the ``test_brief_ledger.py`` captured-Q2 precedent)."""
    return any(params.get(name) == record for name in _PARAMETER_REFERENCE.findall(statement))


def _statements_with_params(fragments: Sequence[Any]) -> list[tuple[str, dict[str, Any]]]:
    """Every statement of a transaction, each with the parameters it references (as ``compose`` merges
    them)."""
    merged: dict[str, Any] = {}
    for fragment in fragments:
        merged.update(fragment.params)
    return [
        (
            statement,
            {name: merged[name] for name in _PARAMETER_REFERENCE.findall(statement) if name in merged},
        )
        for fragment in fragments
        for statement in fragment.statements
    ]


class _ExplainBeforeTheWrite:
    """Wrap ONE ledger's write door (``TaskLedger._apply``): at the first transaction holding a statement that
    binds every record in ``anchors``, EXPLAIN that statement over the world as it stands BEFORE the write (on
    a SECOND connection), record the plan and the ``blocks`` edge count around the EXPLAIN, then let the write
    through. Fails closed: :attr:`matches` lists every matching statement, and a leg asserts exactly one."""

    def __init__(self, ledger: Any, explainer: TaskLedger, anchors: Sequence[RecordID]) -> None:
        self._ledger = ledger
        self._explainer = explainer
        self._anchors = list(anchors)
        self._original: Callable[[Any], Awaitable[Any]] = ledger._apply  # noqa: SLF001 - the one write door
        self.matches: list[tuple[str, dict[str, Any]]] = []
        self.plan: Any = None
        self.edges_around_explain: tuple[int, int] | None = None

    async def __call__(self, fragments: Any) -> Any:
        if self.plan is None:
            hits = [
                (statement, params)
                for statement, params in _statements_with_params(fragments)
                if all(_binds(params, statement, anchor) for anchor in self._anchors)
            ]
            if hits:
                self.matches = hits
                statement, params = hits[0]
                before = await _edge_count(self._explainer)
                self.plan = await raw(self._explainer, f"{statement} EXPLAIN", params)
                self.edges_around_explain = (before, await _edge_count(self._explainer))
        return await self._original(fragments)

    def install(self) -> None:
        self._ledger._apply = self  # noqa: SLF001

    def restore(self) -> None:
        self._ledger._apply = self._original  # noqa: SLF001


async def _edge_count(ledger: TaskLedger) -> int:
    rows = await raw(ledger, f"SELECT count() AS n FROM {BLOCKS_RELATION} GROUP ALL")
    rows = rows if isinstance(rows, list) else [rows]
    return int(rows[0]["n"]) if rows else 0


async def _seed_unrelated_edges(ledger: TaskLedger, tag: str) -> None:
    """E ≥ 20 edges under a blocker that plays no part in the statement under test."""
    noise = await create(ledger, f"{tag} unrelated blocker")
    await bulk_seed_dependents(ledger, noise, _UNRELATED_EDGES, tag=f"{tag}n")


async def _assert_the_walker_sees_a_table_scan(
    explainer: TaskLedger, params: dict[str, Any], anchor: str
) -> None:
    """C+ control (both walker arms, live 3.3.5 shapes): the TABLE-anchored DELETE over the same world, and a
    SELECT over the same table, each DO iterate ``blocks``; neither deletes anything."""
    before = await _edge_count(explainer)
    table_anchored = await raw(explainer, f"DELETE {BLOCKS_RELATION} WHERE in = ${anchor} EXPLAIN", params)
    select_plan = await raw(
        explainer, f"SELECT * FROM {BLOCKS_RELATION} WHERE in = ${anchor} EXPLAIN", params
    )
    assert scans_table(table_anchored, BLOCKS_RELATION), (
        f"C+ control: the walker does not see the table-anchored DELETE's table iteration — plan "
        f"{table_anchored}"
    )
    assert iterated_records(table_anchored) == 0, table_anchored
    assert scans_table(select_plan, BLOCKS_RELATION), f"C+ control (SELECT arm): plan {select_plan}"
    assert await _edge_count(explainer) == before, "an EXPLAIN deleted edges"


class TestNoEdgeDeleteIteratesTheBlocksTable:
    """am-17 §9.2–§9.4: the supersede's and the heal's edge DELETEs are anchored on a record, so their plan
    iterates that record's own edges, never the ``blocks`` table. RED on builder-58-1's tree (both statements
    are table-anchored)."""

    async def test_the_SUPERSEDE_edge_delete_iterates_only_the_hubs_own_edges(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """A hub with N = 5 dependents (and one blocker of its own, whose edge INTO the hub must not be
        counted),
        beside E = 25 unrelated edges. The statement binding the hub's ``RecordID`` in the supersede
        transaction
        → its plan iterates no table and exactly N records (am-17 §9.4 assertions 1–3).

        Kills the table-anchored supersede DELETE kept (assertion 1; §9.5 wrong build 6) and a DELETE anchored
        on both directions of the hub (N + 1 records)."""
        ledger, env = ledger58
        hub_blocker = await create(ledger, "r53s the hub's own blocker")
        hub = await create(ledger, "r53s the hub", blocked_by=[hub_blocker])
        await bulk_seed_dependents(ledger, hub, _HUB_DEPENDENTS, tag="r53sd")
        await _seed_unrelated_edges(ledger, "r53s")
        explainer = new_ledger(env)
        try:
            hook = _ExplainBeforeTheWrite(ledger, explainer, [RecordID(TASK_TABLE, hub)])
            hook.install()
            try:
                await supersede(ledger, hub)
            finally:
                hook.restore()
            assert len(hook.matches) == 1, (
                f"non-vacuity: exactly ONE statement of the supersede transaction must bind the hub's "
                f"RecordID "
                f"(the edge DELETE); found {[statement for statement, _ in hook.matches]}"
            )
            plan = hook.plan
            assert not scans_table(plan, BLOCKS_RELATION), (
                f"the supersede's edge DELETE iterates the whole {BLOCKS_RELATION} table — plan {plan}; "
                f"anchor it on "
                f"the superseded task's own edges (am-17 §9.2)"
            )
            assert iterated_records(plan) == _HUB_DEPENDENTS, (
                f"the supersede's edge DELETE must iterate the hub's own {_HUB_DEPENDENTS} outgoing "
                f"edges; plan {plan}"
            )
            before, after = hook.edges_around_explain or (None, None)
            assert before == after, f"the EXPLAIN deleted edges ({before} → {after})"
            await _assert_the_walker_sees_a_table_scan(explainer, {"old": RecordID(TASK_TABLE, hub)}, "old")
        finally:
            await explainer.close()

    async def test_the_HEAL_edge_delete_iterates_only_the_dependents_own_blocker_edges(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """One straggler with TWO blockers (the superseded one and a live one), under a superseded blocker
        with
        6 other dependents, beside E = 25 unrelated edges. The heal statement binding both the straggler's and
        the superseded blocker's ``RecordID`` → its plan iterates no table and exactly 2 records (the
        straggler's
        own blocker count).

        Kills the table-anchored heal DELETE kept (assertion 1) and the blocker-anchored DELETE, V2 (it
        iterates
        the superseded blocker's 7 edges; §9.5 wrong build 7)."""
        ledger, env = ledger58
        head = await create(ledger, "r53h head")
        live = await create(ledger, "r53h live blocker")
        old = "r53hlegacy00000000000000000000aa"
        await raw_seed_row(ledger, old, blocked_by=[], superseded_by=head)
        await bulk_seed_dependents(ledger, old, _OTHER_DEPENDENTS_OF_THE_OLD_BLOCKER, tag="r53ho")
        target = "r53htarget00000000000000000000aa"
        await raw_seed_row(ledger, target, blocked_by=[old, live])
        await raw_relate(ledger, old, target)
        await raw_relate(ledger, live, target)
        await _seed_unrelated_edges(ledger, "r53h")
        booted, explainer = new_ledger(env), new_ledger(env)
        try:
            hook = _ExplainBeforeTheWrite(
                booted, explainer, [RecordID(TASK_TABLE, target), RecordID(TASK_TABLE, old)]
            )
            hook.install()
            await booted.ensure_ready()  # the boot heal is the only door to this statement
            assert len(hook.matches) == 1, (
                f"non-vacuity: exactly ONE heal statement must bind both the straggler's and the superseded "
                f"blocker's RecordID (the edge DELETE); found {[statement for statement, _ in hook.matches]}"
            )
            plan = hook.plan
            assert not scans_table(plan, BLOCKS_RELATION), (
                f"the heal's edge DELETE iterates the whole {BLOCKS_RELATION} table — plan {plan}; anchor "
                f"it on the "
                f"dependent (am-17 §3)"
            )
            assert iterated_records(plan) == 2, (
                f"the heal's edge DELETE must iterate the straggler's own 2 blocker edges, not the "
                f"superseded "
                f"blocker's {_OTHER_DEPENDENTS_OF_THE_OLD_BLOCKER + 1}; plan {plan}"
            )
            before, after = hook.edges_around_explain or (None, None)
            assert before == after, f"the EXPLAIN deleted edges ({before} → {after})"
            assert sorted(await column(ledger, target)) == sorted([head, live]), "the straggler did not heal"
            # a pair-loose DELETE (`DELETE $dependent<-blocks`, no WHERE) iterates the same 2 records but
            # also deletes the LIVE blocker's edge: the plan cannot see it, the edge mirror can.
            await assert_edge_mirrors_column_for_every_row(ledger, where="r5.3 heal EXPLAIN world")
            await _assert_the_walker_sees_a_table_scan(explainer, {"old": RecordID(TASK_TABLE, live)}, "old")
            v2 = await raw(
                explainer,
                f"DELETE $old->{BLOCKS_RELATION} WHERE out = $dependent EXPLAIN",
                {"old": RecordID(TASK_TABLE, head), "dependent": RecordID(TASK_TABLE, target)},
            )
            # C+ for the count: a blocker-anchored form iterates the BLOCKER's edges (the head now carries the
            # healed population), so the count the pin reads can see a different number.
            assert iterated_records(v2) == _OTHER_DEPENDENTS_OF_THE_OLD_BLOCKER + 1, v2
        finally:
            await booted.close()
            await explainer.close()
