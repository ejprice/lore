"""Packet 58 contract r3 — amendment 8 §2/§4: the boot heal CONVERGES (a GENERATED straggler-shape sweep).

*Every claim in this file is scoped to the tree at ``c9e5eb8`` (branch ``feat/surreal-unification``),
2026-09-26, authored by ``contract-58-r3``.  "RED at HEAD" means RED at that commit.*

Spec: ``docs/design/2026-09-26-packet58-amendment-8.md`` @ ``03cb6d0`` §2 (the third-strike property) + §4
F4 + §2's edge (F10). Rounds 1–3 of 58's contract loop each found one more straggler shape the heal's chunk
sizing mispriced (r1 → am-2's defect → am-3 → N3, two-blocker rows). This file pins the PROPERTY, not a
fourth instance:

    ∀ straggler populations whose heads resolve, ONE boot heals ALL of them — ``count == |population|`` and
    every sent transaction ≤ ``TXN_ROW_HARD_CAP`` — where each row's WEIGHT is its own composed ROW
    count, ``_txn.fragment_rows`` (am-8 §2; r5: am-15 §2, at the §8.1 5 000-row shrink, read live).

**The domain is GENERATED** (CLAUDE.md *Fix the CLASS*, rule 3) from the heal's own cost ingredients — the
things one straggler row can carry that change what the heal composes for it:

* ``entries`` ∈ {1, 2, 3} superseded blockers named by the row (each costs its own edge retirement and
  re-anchor);
* ``heads`` ∈ {distinct, shared} — whether those entries resolve to one head or to one head each (a shared
  head is ONE new edge for several entries);
* ``head_present`` ∈ {absent, present} — whether the row already names its head(s) (then no new edge at all).

Every combination is a cost CLASS (``SHAPES``; the ingredients are asserted realized by every fixture, and
each value of each ingredient occurs — ``TestTheShapeSpaceIsNotVacuous``).  For each class the packer's own
per-chunk capacity is MEASURED off ``compose`` (never a literal: 1, 2 and 3 rows of the class, linearity
checked), and the population is swept at ``fit − 1``, ``fit``, ``fit + 1`` and ``2·fit + 1`` rows (the last
added by contract r4, amendment 12 §3 F-E) → one boot, exactly 1, 1, 2 and 3 composed heal transactions (a
greedy packer — am-8 §1 rules ``more_itertools.constrained_batches``,
which IS greedy), each ≤ the cap, every row healed and counted, edges mirroring columns, a second boot silent.
Two MIXED populations put a chunk boundary between cost classes; there the greedy closure is checked
order-free (every chunk but the smallest is within one max-weight of the cap).

The unresolvable side (am-8 §4 F4 — RULED: the ROW is the unit) is generated over
``{one bad, bad + healable, two bad, healable + healable, bad among two healable}`` × the bad entry's
POSITION ``{first, middle, last}`` (contract r4, am-12 §3 F-G) × ``{phantom, cyclic}``: a row with any
unresolvable entry is skipped WHOLE (byte-identical), UNCOUNTED, and recorded with ONE WARNING PER
UNRESOLVABLE ENTRY carrying that entry's ``blocker_id`` (FK-r3-6), every boot.

The edge (F10): ONE row whose own weight exceeds the cap fails the boot LOUD with the typed
``StragglerHealPackerError`` naming the row and its weight, and NOTHING changes — not even a healable row
elsewhere in the same population (a packer that applies batches lazily before reaching the monster reds).

RED at HEAD ``c9e5eb8``: HEAD has no heal (am-1's re-anchor is unbuilt), so no straggler is ever re-anchored.
"""

from __future__ import annotations

import itertools
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from _reanchor_58_support import (
    CREATOR,
    DESCRIPTION,
    HEAL_CHAIN_CYCLE_EVENT,
    HEAL_EVENT,
    HEAL_PHANTOM_HEAD_EVENT,
    ComposeSpy,
    all_columns,
    assert_edge_mirrors_column_for_every_row,
    boot,
    column,
    create,
    edge_pairs,
    ledger58,
    raw,
    raw_relate,
    raw_seed_row,
    shrunk_row_caps,
    snapshot,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import TaskLedger
from surrealdb import RecordID

if TYPE_CHECKING:
    # ⚠ packet 58's RULED, not-yet-built symbol, named STATICALLY for the typecheck gate (lead #17055, the
    # #461 shape): a mypy error at HEAD owned by `scripts/pending_contracts.yaml` bound `packet-58-contract`,
    # which owns this file's RED@HEAD pytest legs too and self-destructs with the build.  Runtime-inert.
    from loremaster.tasks import StragglerHealPackerError

    _RULED_58: tuple[object, ...] = (StragglerHealPackerError,)

__all__ = ["ledger58", "shrunk_row_caps"]

ENTRIES = (1, 2, 3)
HEADS = ("distinct", "shared")
HEAD_PRESENT = (False, True)


@dataclass(frozen=True)
class Shape:
    """One cost CLASS of straggler row (the heal's own cost ingredients)."""

    entries: int
    heads: str
    head_present: bool

    @property
    def head_count(self) -> int:
        return self.entries if self.heads == "distinct" else 1

    @property
    def label(self) -> str:
        return f"e{self.entries}-{self.heads}-{'present' if self.head_present else 'absent'}"


#: GENERATED: every combination of the ingredients (one entry has no distinct/shared distinction).
SHAPES = sorted(
    {
        Shape(entries, heads if entries > 1 else "distinct", present)
        for entries, heads, present in itertools.product(ENTRIES, HEADS, HEAD_PRESENT)
    },
    key=lambda shape: shape.label,
)
# ⚠ DUAL (packet 58 contract r4 — amendment 12 §3 F-E): SCALES USED to be offsets ``{fit−1, fit, fit+1}``, so
# no
# generated population ever FILLED a chunk opened by a carried row (W-PACK-OBO died only on PC's hand count,
# by
# 49 rows).  It gains ``2·fit + 1`` — three chunks, the second FULL — and every scale is a function of the
# MEASURED
# fit; ``expected_chunks = ceil(rows / fit)`` stays the generated oracle.
SCALES: dict[str, Callable[[int], int]] = {
    "fit-1": lambda fit: fit - 1,
    "fit": lambda fit: fit,
    "fit+1": lambda fit: fit + 1,
    "2fit+1": lambda fit: 2 * fit + 1,
}
# SDK3 R8 F12 / R12 F19 / F21 + packet 58 amendment 15 §2 / §8.1 (contract r5): the ROW bound replaced the
# statement cap. Every leg requests the 5 000-row shrink (``shrunk_row_caps``) and reads the cap LIVE through
# ``_cap()`` — never a module-level copy taken at import (the wrong build F21 forbids).


#: The over-cap row's entry count (am-8 §2 edge) — under the 5 000 shrink one such row cannot be packed.
_MONSTER_ENTRIES = 1700


def _cap() -> int:
    """The row cap as ``compose`` and the packer see it right now (read live — F21)."""
    return _txn.TXN_ROW_HARD_CAP


def _pad(text: str) -> str:
    return text.ljust(32, "0")[:32]


@dataclass
class Population:
    """A seeded straggler population of one shape: the rows and the column each must end with."""

    rows: list[str]
    expected: dict[str, list[str]]
    heads: list[str]
    legacies: list[str]


async def seed_population(ledger: TaskLedger, shape: Shape, count: int, tag: str) -> Population:
    """``count`` raw stragglers of ``shape`` (rows + mirrored edges in bulk), their heads real open tasks.

    Legacy blocker ``i`` is superseded by head ``i`` (distinct) or head 0 (shared).  A ``head_present`` row
    already names its head(s) after its legacy entries, with the edges mirrored — the backfill mints nothing,
    so the heal's composed work is exactly the shape's.
    """
    heads = [await create(ledger, f"{tag} head {index}") for index in range(shape.head_count)]
    legacies = [_pad(f"{tag}leg{index}") for index in range(shape.entries)]
    for index, legacy in enumerate(legacies):
        await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=heads[index % shape.head_count])
    column_value = list(legacies) + (list(heads) if shape.head_present else [])
    now = datetime.now(UTC)
    rows = [_pad(f"{tag}r{index:05d}") for index in range(count)]
    documents = [
        {
            "id": RecordID(TASK_TABLE, row),
            **TaskLedger._new_task_content(f"straggler {row}", DESCRIPTION, column_value, CREATOR, now),  # noqa: SLF001
        }
        for row in rows
    ]
    if documents:
        await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": documents})
        edges = [
            {"in": RecordID(TASK_TABLE, blocker), "out": RecordID(TASK_TABLE, row)}
            for row in rows
            for blocker in column_value
        ]
        await raw(ledger, f"INSERT RELATION INTO {BLOCKS_RELATION} $edges", {"edges": edges})
    mapped = [heads[legacies.index(b) % shape.head_count] if b in legacies else b for b in column_value]
    final = list(dict.fromkeys(mapped))
    return Population(rows=rows, expected=dict.fromkeys(rows, final), heads=heads, legacies=legacies)


def _heal_chunks(spy: ComposeSpy) -> list[int]:
    """The ROW count (``fragment_rows``) of each heal chunk the boot composed (am-15 §2)."""
    return spy.heal_rows()


async def _boot_spied(env: SurrealEnv, caplog: pytest.LogCaptureFixture) -> ComposeSpy:
    spy = ComposeSpy()
    caplog.clear()
    with spy.installed(), caplog.at_level(logging.DEBUG):
        await boot(env)
    return spy


def _heal_records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.getMessage() == HEAL_EVENT]


async def measure_weight(
    ledger: TaskLedger, env: SurrealEnv, shape: Shape, tag: str, caplog: pytest.LogCaptureFixture
) -> tuple[int, int]:
    """``(fixed, weight)`` of the shape's heal chunk, MEASURED off ``compose`` at 1, 2, 3 rows (linearity)."""
    counts: list[int] = []
    for n in (1, 2, 3):
        await seed_population(ledger, shape, n, f"{tag}m{n}")
        chunks = _heal_chunks(await _boot_spied(env, caplog))
        assert len(chunks) == 1, f"measuring {shape.label}: {len(chunks)} heal chunks for n={n}"
        counts.append(chunks[0])
    weight = counts[1] - counts[0]
    fixed = counts[0] - weight
    assert weight > 0 and counts[2] == fixed + 3 * weight, (
        f"{shape.label}: the heal chunk's composed count is not linear in its rows (c1..c3 = {counts})"
    )
    return fixed, weight


#: r5.2 (am-16 §2.1 sibling): the entry counts the monster's per-row weight is measured at (a one-row heal
#: chunk each), then extrapolated linearly to the monster's own entry count.
_WEIGHT_PROBE_ENTRIES = (2, 3, 4)


async def one_row_weight(
    ledger: TaskLedger, env: SurrealEnv, entries: int, tag: str, caplog: pytest.LogCaptureFixture
) -> int:
    """The ROW count of a ONE-row heal chunk for a ``Shape(entries, "shared", False)`` straggler, measured
    at ``compose`` at :data:`_WEIGHT_PROBE_ENTRIES` and extrapolated (linearity checked) — what that row
    alone costs to heal, i.e. ``fragment_rows`` of its own fragments (am-16 §2.1), derived from the
    composed transaction, never from the builder's code."""
    measured: list[int] = []
    for probe in _WEIGHT_PROBE_ENTRIES:
        await seed_population(ledger, Shape(probe, "shared", False), 1, f"{tag}w{probe}")
        chunks = _heal_chunks(await _boot_spied(env, caplog))
        assert len(chunks) == 1, f"measuring a one-row chunk at {probe} entries: {len(chunks)} chunks"
        measured.append(chunks[0])
    first, second, third = measured
    slope = second - first
    assert slope > 0 and third == second + slope, (
        f"a row's heal weight is not linear in its entries (at {_WEIGHT_PROBE_ENTRIES}: {measured})"
    )
    return first + slope * (entries - _WEIGHT_PROBE_ENTRIES[0])


async def _assert_converged(
    ledger: TaskLedger,
    env: SurrealEnv,
    population: Population,
    spy: ComposeSpy,
    caplog: pytest.LogCaptureFixture,
    *,
    where: str,
) -> None:
    columns = await all_columns(ledger)
    wrong = {row: columns.get(row) for row, final in population.expected.items() if columns.get(row) != final}
    assert not wrong, (
        f"{where}: {len(wrong)} rows not re-anchored to their head(s), e.g. {list(wrong.items())[:3]}"
    )
    heal = _heal_records(caplog)
    assert len(heal) == 1 and getattr(heal[0], "count", None) == len(population.rows), (
        f"{where}: ONE boot must heal and COUNT every row: {[getattr(r, 'count', None) for r in heal]} "
        f"for {len(population.rows)} rows"
    )
    sent = _heal_chunks(spy)
    assert sent and all(size <= _cap() for size in sent), f"{where}: heal transactions {sent} vs cap {_cap()}"
    assert getattr(heal[0], "chunks", None) == len(sent), (
        f"{where}: `chunks` ({getattr(heal[0], 'chunks', None)}) != composed heal transactions ({len(sent)})"
    )
    await assert_edge_mirrors_column_for_every_row(ledger, where=where)
    before = await snapshot(ledger)
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await boot(env)
    assert not _heal_records(caplog), f"{where}: the SECOND boot healed again — the first did not converge"
    assert await snapshot(ledger) == before, f"{where}: the second boot wrote"


class TestTheShapeSpaceIsNotVacuous:
    """The generated domain is the ingredients' product, and every ingredient value occurs in it."""

    def test_every_ingredient_value_occurs_in_the_generated_shapes(self) -> None:
        assert {shape.entries for shape in SHAPES} == set(ENTRIES)
        assert {shape.heads for shape in SHAPES} == set(HEADS)
        assert {shape.head_present for shape in SHAPES} == set(HEAD_PRESENT)
        assert len(SHAPES) == len(ENTRIES) * len(HEADS) * len(HEAD_PRESENT) - len(HEAD_PRESENT)

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_each_fixture_realizes_its_shape(self, ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
        ledger, _env = ledger58
        for shape in SHAPES:
            population = await seed_population(ledger, shape, 1, f"nv{shape.label.replace('-', '')}")
            seeded = await column(ledger, population.rows[0])
            assert len([b for b in seeded if b in population.legacies]) == shape.entries, (shape, seeded)
            assert len(population.heads) == shape.head_count, shape
            assert all((head in seeded) is shape.head_present for head in population.heads), (shape, seeded)
            edges = [pair for pair in await edge_pairs(ledger) if pair[1] == population.rows[0]]
            assert sorted(b for b, _ in edges) == sorted(seeded), (shape, edges)


class TestOneBootHealsEveryShapeAtTheCapBoundary:
    """am-8 §2: per cost class, ``fit − 1`` / ``fit`` / ``fit + 1`` / ``2·fit + 1`` rows → 1 / 1 / 2 / 3 heal
    transactions (the last scale: contract r4, am-12 §3 F-E)."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    @pytest.mark.parametrize("scale", sorted(SCALES))
    @pytest.mark.parametrize("shape", SHAPES, ids=[shape.label for shape in SHAPES])
    async def test_one_boot_heals_the_whole_population_in_the_predicted_chunks(
        self,
        ledger58: tuple[TaskLedger, SurrealEnv],
        caplog: pytest.LogCaptureFixture,
        shape: Shape,
        scale: str,
    ) -> None:
        ledger, env = ledger58
        tag = f"cv{shape.label.replace('-', '')}"
        fixed, weight = await measure_weight(ledger, env, shape, tag, caplog)
        fit = (_cap() - fixed) // weight
        assert fit > 1, f"{shape.label}: a chunk fits {fit} rows — the sweep needs ≥ 2"
        rows = SCALES[scale](fit)
        population = await seed_population(ledger, shape, rows, f"{tag}p")
        spy = await _boot_spied(env, caplog)
        sent = _heal_chunks(spy)
        expected_chunks = -(-rows // fit)
        assert len(sent) == expected_chunks, (
            f"{shape.label} at {scale} ({rows} rows, weight {weight}, fixed {fixed}, fit {fit}): the heal "
            f"composed {len(sent)} transactions {sent}; a GREEDY packer by each row's own weight composes "
            f"{expected_chunks}"
        )
        await _assert_converged(ledger, env, population, spy, caplog, where=f"{shape.label}@{scale}")


#: Two MIXED populations: a cheap and a dear class, sized so the chunk boundary falls BETWEEN classes.
MIXES = [
    (Shape(1, "distinct", False), Shape(3, "distinct", False)),
    (Shape(2, "shared", True), Shape(2, "distinct", False)),
]


class TestOneBootHealsAMixedPopulation:
    """am-8 §2 ``{pure, mixed cost classes}``: one boot heals all; chunks ≤ cap; greedy closure order-free."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    @pytest.mark.parametrize("mix", MIXES, ids=[f"{a.label}+{b.label}" for a, b in MIXES])
    async def test_a_mixed_population_heals_in_one_boot(
        self,
        ledger58: tuple[TaskLedger, SurrealEnv],
        caplog: pytest.LogCaptureFixture,
        mix: tuple[Shape, Shape],
    ) -> None:
        ledger, env = ledger58
        (fixed_a, weight_a), (fixed_b, weight_b) = [
            await measure_weight(ledger, env, shape, f"mx{index}", caplog) for index, shape in enumerate(mix)
        ]
        rows_a = (_cap() - fixed_a) // (2 * weight_a) + 1
        rows_b = (_cap() - fixed_b) // weight_b
        first = await seed_population(ledger, mix[0], rows_a, "mxpa")
        second = await seed_population(ledger, mix[1], rows_b, "mxpb")
        population = Population(
            rows=first.rows + second.rows,
            expected={**first.expected, **second.expected},
            heads=first.heads + second.heads,
            legacies=first.legacies + second.legacies,
        )
        spy = await _boot_spied(env, caplog)
        sent = sorted(_heal_chunks(spy), reverse=True)
        assert len(sent) >= 2, f"the mix must cross a chunk boundary: {sent}"
        heaviest = max(weight_a, weight_b) + max(fixed_a, fixed_b)
        assert all(size > _cap() - heaviest for size in sent[:-1]), (
            f"a non-final heal chunk left more than one row's weight of room: {sent} (cap {_cap()}, "
            f"heaviest row {heaviest}) — the packer is not greedy by each row's own weight"
        )
        await _assert_converged(ledger, env, population, spy, caplog, where="mixed population")


# --------------------------------------------------------------------------- #
# F4 — the unresolvable row, generated (am-8 §4: the ROW is the unit; one WARNING per unresolvable ENTRY).
# --------------------------------------------------------------------------- #

ROW_COMPOSITIONS = {
    "one_bad": (1, 0),
    "bad_plus_healable": (1, 1),
    "two_bad": (2, 0),
    "healable_plus_healable": (0, 2),
    # packet 58 contract r4 — amendment 12 §3 F-G: the composition that makes "bad in the MIDDLE" a distinct
    # row.
    "bad_among_two_healable": (1, 2),
}
# ⚠ DUAL (packet 58 contract r4 — amendment 12 §3 F-G, adversary-58-r3 W-F4-PREFIX): every mixed fixture USED
# to
# name the unresolvable entry FIRST, so a heal that re-anchored the healable PREFIX before the first bad entry
# passed.  POSITION is now an ingredient: ROW_COMPOSITIONS × {bad first, bad middle, bad last}, generated
# where the
# position yields a distinct ``blocked_by`` order.
POSITIONS = ("bad-first", "bad-middle", "bad-last")


def ordered_entries(bad: list[str], healable: list[str], position: str) -> list[str]:
    """The row's ``blocked_by`` with the unresolvable entries at ``position`` among the healable ones."""
    if position == "bad-first":
        return bad + healable
    if position == "bad-last":
        return healable + bad
    return healable[:1] + bad + healable[1:]


def _f4_legs() -> list[tuple[str, str]]:
    """(composition, position) — every position whose order is DISTINCT from the ones before it."""
    legs: list[tuple[str, str]] = []
    for composition in sorted(ROW_COMPOSITIONS):
        bad_count, healable_count = ROW_COMPOSITIONS[composition]
        bad = [f"b{index}" for index in range(bad_count)]
        healable = [f"h{index}" for index in range(healable_count)]
        seen: list[list[str]] = []
        for position in POSITIONS:
            order = ordered_entries(bad, healable, position)
            if order not in seen:
                seen.append(order)
                legs.append((composition, position))
    return legs


F4_LEGS = _f4_legs()
BAD_KINDS = ("phantom", "cyclic")
BAD_EVENT = {"phantom": HEAL_PHANTOM_HEAD_EVENT, "cyclic": HEAL_CHAIN_CYCLE_EVENT}


async def _seed_bad_entry(ledger: TaskLedger, kind: str, tag: str) -> str:
    """One legacy blocker whose superseded_by chain does NOT resolve: to a phantom head, or around a cycle."""
    legacy = _pad(f"{tag}bad")
    if kind == "phantom":
        await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=_pad(f"{tag}ghost"))
    else:
        partner = _pad(f"{tag}cyc")
        await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=partner)
        await raw_seed_row(ledger, partner, blocked_by=[], superseded_by=legacy)
    return legacy


class TestAnUnresolvableRowIsSkippedWHOLE:
    """am-8 §4 F4 × am-3 §5: skipped whole (byte-identical), uncounted, ONE WARNING per bad ENTRY, per boot"""

    @pytest.mark.usefixtures("shrunk_row_caps")
    @pytest.mark.parametrize("kind", BAD_KINDS)
    @pytest.mark.parametrize(("composition", "position"), F4_LEGS, ids=[f"{c}-{p}" for c, p in F4_LEGS])
    async def test_the_row_is_the_unit(
        self,
        ledger58: tuple[TaskLedger, SurrealEnv],
        caplog: pytest.LogCaptureFixture,
        composition: str,
        position: str,
        kind: str,
    ) -> None:
        ledger, env = ledger58
        bad_count, healable_count = ROW_COMPOSITIONS[composition]
        tag = f"f4{composition[:6]}{position[4:7]}{kind[:3]}"
        bad = [await _seed_bad_entry(ledger, kind, f"{tag}{index}") for index in range(bad_count)]
        head = await create(ledger, "a real head")
        healable = [_pad(f"{tag}h{index}") for index in range(healable_count)]
        for legacy in healable:
            await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
        row = _pad(f"{tag}row")
        entries = ordered_entries(bad, healable, position)
        await raw_seed_row(ledger, row, blocked_by=entries)
        for blocker in entries:
            await raw_relate(ledger, blocker, row)
        companion = await seed_population(ledger, Shape(1, "distinct", False), 1, f"{tag}c")
        row_before = [entry for entry in (await snapshot(ledger))[0] if row in entry]
        edges_before = [pair for pair in await edge_pairs(ledger) if pair[1] == row]
        for boot_number in (1, 2):
            caplog.clear()
            with caplog.at_level(logging.DEBUG):
                await boot(env)
            recorded = [r for r in caplog.records if r.getMessage() == BAD_EVENT[kind]]
            if bad:
                assert [entry for entry in (await snapshot(ledger))[0] if row in entry] == row_before, (
                    f"boot {boot_number}: a row with an unresolvable {kind} entry was (half-)healed"
                )
                assert [pair for pair in await edge_pairs(ledger) if pair[1] == row] == edges_before
                assert sorted(str(getattr(r, "blocker_id", None)) for r in recorded) == sorted(bad), (
                    f"boot {boot_number}: expected ONE {BAD_EVENT[kind]} per unresolvable entry "
                    f"{sorted(bad)}, "
                    f"got {[(getattr(r, 'task_id', None), getattr(r, 'blocker_id', None)) for r in recorded]}"
                )
                assert all(getattr(r, "task_id", None) == row for r in recorded)
            else:
                assert not recorded
                assert await column(ledger, row) == [head], "CONTROL: a fully healable row is healed"
            heal = _heal_records(caplog)
            if boot_number == 1:
                healed = 1 + (0 if bad else 1)
                assert len(heal) == 1 and getattr(heal[0], "count", None) == healed, (
                    f"the heal counted {[getattr(r, 'count', None) for r in heal]}; "
                    f"{healed} rows are healable"
                )
                assert await column(ledger, companion.rows[0]) == companion.expected[companion.rows[0]]
            else:
                assert not heal, "the second boot healed again"

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_row_with_a_PHANTOM_and_a_CYCLIC_entry_records_BOTH_and_its_healable_entry_waits(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Packet 58 amendment 9 §5 (FK-r3-6), its own pin: a row naming {phantom P, cyclic C, healable H} →
        TWO records whose ``blocker_id`` set is exactly {P, C} (one per unresolvable ENTRY, across both record
        kinds), ZERO rewrites, the row uncounted.  CONTROL: a row naming {H} alone → healed, no record."""
        ledger, env = ledger58
        phantom = await _seed_bad_entry(ledger, "phantom", "am9p")
        cyclic = await _seed_bad_entry(ledger, "cyclic", "am9c")
        head = await create(ledger, "a real head")
        healable = _pad("am9h")
        await raw_seed_row(ledger, healable, blocked_by=[], superseded_by=head)
        row, control = _pad("am9row"), _pad("am9control")
        await raw_seed_row(ledger, row, blocked_by=[phantom, cyclic, healable])
        await raw_seed_row(ledger, control, blocked_by=[healable])
        for blocker in (phantom, cyclic, healable):
            await raw_relate(ledger, blocker, row)
        await raw_relate(ledger, healable, control)
        row_before = [entry for entry in (await snapshot(ledger))[0] if row in entry]
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            await boot(env)
        records = [r for r in caplog.records if r.getMessage() in set(BAD_EVENT.values())]
        assert sorted(str(getattr(r, "blocker_id", None)) for r in records) == sorted([phantom, cyclic]), [
            (r.getMessage(), getattr(r, "blocker_id", None)) for r in records
        ]
        assert {r.getMessage() for r in records} == set(BAD_EVENT.values())
        assert [entry for entry in (await snapshot(ledger))[0] if row in entry] == row_before, (
            "the row was rewritten"
        )
        heal = _heal_records(caplog)
        assert len(heal) == 1 and getattr(heal[0], "count", None) == 1, [
            getattr(r, "count", None) for r in heal
        ]
        assert await column(ledger, control) == [head], "CONTROL: {H} alone is healed"


# --------------------------------------------------------------------------- #
# F10 — the one row that cannot be packed (am-8 §2 edge; am-3 §1's rider).
# --------------------------------------------------------------------------- #


class TestARowOverTheCapFailsTheBootLOUD:
    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_single_row_over_the_cap_raises_the_typed_packer_error_and_changes_NOTHING(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        """r5.2 (am-16 §2.1 sibling): the packer error carries TYPED ``row_id`` / ``weight`` / ``row_cap``;
        ``weight`` equals the monster's own heal cost derived off ``compose`` (:func:`one_row_weight`),
        ``row_cap`` the live cap. Its text is a boot-failure message, not a served render — not pinned."""
        import loremaster.tasks as tasks_module

        ledger, env = ledger58
        derived_weight = await one_row_weight(ledger, env, _MONSTER_ENTRIES, "ocw", caplog)
        assert derived_weight > _cap(), (
            f"non-vacuity: the monster ({derived_weight} rows) must exceed the cap"
        )
        head = await create(ledger, "the head")
        now = datetime.now(UTC)
        legacy = [_pad(f"ocleg{index:05d}") for index in range(_MONSTER_ENTRIES)]
        documents = [
            {
                "id": RecordID(TASK_TABLE, lid),
                **TaskLedger._new_task_content(f"legacy {lid}", DESCRIPTION, [], CREATOR, now),  # noqa: SLF001
                "superseded_by": head,
            }
            for lid in legacy
        ]
        await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": documents})
        monster = _pad("ocmonster")
        content = TaskLedger._new_task_content("monster", DESCRIPTION, legacy, CREATOR, now)  # noqa: SLF001
        await raw(
            ledger, f"CREATE type::record('{TASK_TABLE}', $id) CONTENT $c", {"id": monster, "c": content}
        )
        monster_edges = [
            {"in": RecordID(TASK_TABLE, lid), "out": RecordID(TASK_TABLE, monster)} for lid in legacy
        ]
        # the edges mirror the column, so the BACKFILL mints nothing and "nothing changed" isolates the heal
        await raw(ledger, f"INSERT RELATION INTO {BLOCKS_RELATION} $edges", {"edges": monster_edges})
        companion = await seed_population(ledger, Shape(1, "distinct", False), 3, "occ")
        before = await snapshot(ledger)
        packer_error = getattr(tasks_module, "StragglerHealPackerError")  # a ruled, not-yet-built name
        for boot_number in (1, 2):
            with pytest.raises(packer_error) as caught:
                await boot(env)
            message = str(caught.value)
            assert monster in message, f"boot {boot_number}: the packer error must NAME the row: {message!r}"
            facts = {name: getattr(caught.value, name, None) for name in ("row_id", "weight", "row_cap")}
            derived = {"row_id": monster, "weight": derived_weight, "row_cap": _cap()}
            assert facts == derived, (
                f"boot {boot_number}: the packer error's typed facts must EQUAL their derivations "
                f"(am-16 §2.1): served {facts}, derived {derived}"
            )
            assert await snapshot(ledger) == before, (
                f"boot {boot_number}: a boot that fails LOUD must change NOTHING — the companion rows "
                f"{companion.rows} included (a packer that applies a batch before reaching the monster reds)"
            )
