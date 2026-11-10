"""Packet 58 contract r3 — amendment 8 §4 F11: every composed ``blocks`` RELATE came from the one fragment.

*Every claim in this file is scoped to the tree at ``c9e5eb8`` (branch ``feat/surreal-unification``),
2026-09-26, authored by ``contract-58-r3``.  "RED at HEAD" means RED at that commit.*

Spec: ``docs/design/2026-09-26-packet58-amendment-8.md`` @ ``03cb6d0`` §4 F11, under amendment 1's rider
(*"the SAME re-anchor fragment the supersede uses"*) and MP13.  r2 pinned this for the SUPERSEDE only
(``RU::TestEveryRELATEComesFromTheSharedFragment``); a heal that hand-rolls its chunk's RELATEs beside the
shared seam passed everything (adversary-58-r2 F11) — routing-not-sharing: the day ``_relate_fragment``
changes (endpoint binding, direction, a dedupe), that verb does not.

GENERATED: the RELATE-composing verbs are DERIVED from ``loremaster.tasks``' call graph with the SAME walk
as the CAS population (``_reanchor_58_support.cas_verbs_in`` seeded on ``_relate_fragment`` — one
derivation, two seeds): a minimal function that reaches both ``_relate_fragment`` and a driver seam.  The
driver registry below must EQUAL that set, both ways (a new RELATE-composing verb arrives undriven → RED by
name; a stale driver → RED).  Per verb: drive it with ``compose`` and ``TaskLedger._relate_fragment`` both
spied; every ``RELATE`` statement ``compose`` received must be one the fragment produced, and the verb must
compose at least one.

RED at HEAD ``c9e5eb8``: the boot heal (``_reanchor_stragglers``) does not exist, so its driver is stale;
the supersede composes no dependent RELATE (the r1/r2 reds already cover that leg's reason)."""

from __future__ import annotations

import ast
import importlib
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from _reanchor_58_support import (
    ComposeSpy,
    cas_verbs_in,
    create,
    ledger58,
    new_ledger,
    raw_relate,
    raw_seed_row,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.tasks import TaskLedger

if TYPE_CHECKING:
    # ⚠ DISCHARGED 2026-11-10 (a77f72e): the build landed this symbol; bound packet-58-contract is deleted.
    # ⚠ packet 58's RULED, not-yet-built symbol, named STATICALLY for the typecheck gate (lead #17055, the
    # #461 shape): a mypy error at HEAD owned by `scripts/pending_contracts.yaml` bound `packet-58-contract`,
    # which owns this file's RED@HEAD pytest legs too and self-destructs with the build.  Runtime-inert.
    _RULED_58: tuple[object, ...] = (TaskLedger._reanchor_stragglers,)

__all__ = ["ledger58"]

RELATE_SEED = "_relate_fragment"
_RELATE = re.compile(r"\s*RELATE\b")


def derive_relate_verbs() -> set[str]:
    """The minimal ``loremaster.tasks`` functions that reach ``_relate_fragment`` AND a driver seam."""
    tasks_module = importlib.import_module("loremaster.tasks")
    tree = ast.parse(Path(tasks_module.__file__ or "").read_text(encoding="utf-8"))
    return cas_verbs_in(tree, vars(tasks_module), shell=RELATE_SEED)


@dataclass(frozen=True)
class _Spec:
    subject: str
    description: str
    blocked_by: list[str]


async def _drive_create_task(ledger: TaskLedger, _env: SurrealEnv) -> None:
    blocker = await create(ledger, "a blocker")
    await create(ledger, "a dependent", [blocker])


async def _drive_create_many(ledger: TaskLedger, _env: SurrealEnv) -> None:
    blocker = await create(ledger, "a blocker")
    specs: list[Any] = [_Spec("batch a", "d", [blocker]), _Spec("batch b", "d", [blocker])]
    await ledger.create_many(specs, created_by="batch-58r3")


async def _drive_supersede(ledger: TaskLedger, _env: SurrealEnv) -> None:
    old = await create(ledger, "X")
    for index in range(2):
        await create(ledger, f"Y{index}", [old])
    blocker = await create(ledger, "a successor dependency")
    await supersede(ledger, old, blocked_by=[blocker])


async def _drive_backfill(ledger: TaskLedger, env: SurrealEnv) -> None:
    blocker = await create(ledger, "a blocker")
    await raw_seed_row(
        ledger, "relbackfillrow".ljust(32, "0"), blocked_by=[blocker]
    )  # no edge: backfill mints it
    booted = new_ledger(env)
    try:
        await booted.ensure_ready()
    finally:
        await booted.close()


async def _drive_heal(ledger: TaskLedger, env: SurrealEnv) -> None:
    head = await create(ledger, "a head")
    legacy = "relheallegacy".ljust(32, "0")
    await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
    straggler = "relhealrow".ljust(32, "0")
    await raw_seed_row(ledger, straggler, blocked_by=[legacy])
    await raw_relate(ledger, legacy, straggler)
    booted = new_ledger(env)
    try:
        await booted.ensure_ready()
    finally:
        await booted.close()


#: One driver per derived RELATE-composing verb (== ``derive_relate_verbs()``, both ways).
RELATE_DRIVERS: dict[str, Callable[[TaskLedger, SurrealEnv], Awaitable[None]]] = {
    "create_task": _drive_create_task,
    "create_many": _drive_create_many,
    "supersede_task": _drive_supersede,
    "_backfill_blocks_edges": _drive_backfill,
    "_reanchor_stragglers": _drive_heal,
}


class TestTheRELATEVerbsAreDerivedAndDriven:
    def test_the_driver_registry_equals_the_derived_RELATE_verbs(self) -> None:
        derived = derive_relate_verbs()
        assert set(RELATE_DRIVERS) == derived, (
            f"derived RELATE-composing verbs with NO driver: {sorted(derived - set(RELATE_DRIVERS))}; "
            f"drivers for no derived verb (stale): {sorted(set(RELATE_DRIVERS) - derived)}"
        )


class TestEveryComposedRELATECameFromTheSharedFragment:
    """am-8 §4 F11 — GENERATED over the derived verbs (the parametrisation is derived ∪ registry)."""

    @pytest.mark.parametrize("verb", sorted(derive_relate_verbs() | set(RELATE_DRIVERS)))
    async def test_the_verb_composes_only_RELATEs_the_fragment_produced(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch, verb: str
    ) -> None:
        ledger, env = ledger58
        assert verb in RELATE_DRIVERS, f"{verb} composes a RELATE (derived) but no leg drives it"
        produced: list[str] = []
        original = TaskLedger._relate_fragment  # noqa: SLF001

        def _spy(*args: Any, **kwargs: Any) -> Any:
            fragment = original(*args, **kwargs)
            produced.extend(fragment.statements)
            return fragment

        monkeypatch.setattr(TaskLedger, RELATE_SEED, staticmethod(_spy), raising=True)
        spy = ComposeSpy()
        with spy.installed():
            await RELATE_DRIVERS[verb](ledger, env)
        relates = [
            statement
            for statements, _params in spy.calls
            for statement in statements
            if _RELATE.match(statement)
        ]
        assert relates, f"{verb}: its driver composed NO RELATE — the leg is vacuous"
        rogue = [statement for statement in relates if statement not in produced]
        assert not rogue, (
            f"{verb}: RELATE statements reached `compose` that `_relate_fragment` never produced — a "
            f"hand-rolled edge beside the shared seam (routing is not sharing): {rogue[:3]}"
        )
