"""HELD-PATCH contract for packet **58** — the served supersede render + the ``blocked_by.*`` index rider.

*Authored 2026-09-26 by ``contract-58`` against ``5d549a1``; it ships WITH the held integration patch
(``REPORT-contract-58.md`` §HELD) because ``server.py`` / ``surreal_schema.py`` are 63c-shared: before the
patch lands every pin here is RED for the right reason (the old render still says STRANDED and takes a
``direct_dependents`` list; the index does not exist).*

Spec: kickoff rulings ``docs/design/2026-09-26-packet58-kickoff-rulings.md`` @ ``c8d3241`` §6 row "the render
(held patch)" + §7 item 1; amendment 1 ``docs/design/2026-09-26-packet58-amendment-1.md`` @ ``f4e96b4``
(FORK-A's ``reblocked`` K line; the index rider + its EXPLAIN pin with a control).

The render is a PURE function over the ledger's ``SupersedeResult`` (the PRE-write lists): a render that
re-read ``direct_dependents(X)`` after the write would always see ``[]`` and lie by omission.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from _governed_contract import index_served, operators, scans_table
from _reanchor_58_support import (
    CLAIMANT,
    CREATOR,
    create,
    drive_to,
    ledger58,
    raw,
)
from _surreal_harness import SurrealEnv
from loremaster.render import render_attributed
from loremaster.store.surreal_schema import TASK_TABLE, generate_task_ddl
from loremaster.tasks import STATUS_DONE, TaskLedger
from test_blocks_edge import _tool_seam

__all__ = ["ledger58"]

SERVER_SOURCE = Path(importlib.import_module("loremaster.server").__file__ or "")
# contract r5 §HELD part 4: the ONE shared EXPLAIN walker moved to ``_governed_contract`` (c9bc2c6 —
# 3.3 serves index reads as BitmapIndexScan, so the literal 'IndexScan' check retired with the old walker).


def _render(*args: Any) -> str:
    from loremaster.server import AppContext

    return str(AppContext._render_supersede_result(*args))  # noqa: SLF001 - the pure render under test


def _base(task_id: str, successor_id: str, blocked_by: list[str]) -> str:
    """Today's no-dependent render, byte for byte (the #174 clause included) — the N=0 oracle."""
    clause = ""
    if blocked_by:
        clause = f", blocked_by [{', '.join(render_attributed(b) for b in blocked_by)}]"
    return (
        f"superseded task {render_attributed(task_id)}; "
        f"successor {render_attributed(successor_id)} (status open{clause})"
    )


class TestTheRenderIsTheReanchorReceipt:
    def test_N0_is_byte_identical_to_the_pre58_render(self) -> None:
        assert _render("x-58", "s-58", [], [], []) == _base("x-58", "s-58", [])
        assert _render("x-58", "s-58", [], [], ["b1", "b2"]) == _base("x-58", "s-58", ["b1", "b2"])

    def test_N3_names_every_reanchored_dependent_and_the_count(self) -> None:
        rendered = _render("x-58", "s-58", ["d1", "d2", "d3"], [], [])
        assert rendered.startswith(_base("x-58", "s-58", [])), rendered
        assert "re-anchored 3 dependent(s)" in rendered, rendered
        for dependent in ("d1", "d2", "d3"):
            assert dependent in rendered, rendered

    def test_the_reblocked_line_is_present_IFF_non_empty_and_names_only_the_subset(self) -> None:
        plain = _render("x-58", "s-58", ["d1", "d2"], [], [])
        assert "were claimable" not in plain, plain
        rendered = _render("x-58", "s-58", ["d1", "d2"], ["d2"], [])
        line = [part for part in rendered.split("\n") if "were claimable" in part]
        assert len(line) == 1 and "d2" in line[0] and "d1" not in line[0] and "1 of them" in line[0], rendered

    def test_the_STRANDED_warning_is_gone_from_the_server(self) -> None:
        """Removed-behaviour seed §7.1 (dropped-deliberately: the strand no longer occurs).  A BARE,
        anchor-free sweep of the served module's text — prose carries no structural anchor."""
        assert "STRANDED" not in SERVER_SOURCE.read_text(encoding="utf-8")


class TestTheRenderEndToEnd:
    async def test_a_supersede_through_the_tool_seam_serves_the_receipt(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        old = await create(ledger, "X, finished")
        await drive_to(ledger, old, STATUS_DONE)
        claimable = await create(ledger, "Y — claimable before", [old])
        other = await create(ledger, "an open blocker")
        waiting = await create(ledger, "W — already waiting on an open row", [old, other])
        rendered = await _tool_seam(ledger).tasks(
            action="supersede", task_id=old, subject="X'", description="d", created_by=CREATOR
        )
        assert "re-anchored 2 dependent(s)" in rendered and claimable in rendered and waiting in rendered
        reblocked = [line for line in rendered.split("\n") if "were claimable" in line]
        assert len(reblocked) == 1 and claimable in reblocked[0] and waiting not in reblocked[0], rendered
        assert not (await ledger.claim_task(claimable, CLAIMANT)).claimed


class TestTheBlockedByElementIndexServesContainment:
    """Amendment 1 index rider: ``DEFINE INDEX … FIELDS blocked_by.*`` (store ref §2: the element path is
    the ONLY spelling that serves containment; a plain ``FIELDS blocked_by`` IndexScans ``=`` and returns
    ``[]`` — the silent trap)."""

    def test_the_task_ddl_emits_the_ELEMENT_PATH_index(self) -> None:
        ddl = generate_task_ddl()
        assert "FIELDS blocked_by.*" in ddl, "the index must be on the ELEMENT path `blocked_by.*`"

    async def test_CONTAINS_is_an_IndexScan_with_the_index_and_a_TableScan_without(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        blocker = await create(ledger, "a blocker")
        await create(ledger, "a dependent", [blocker])
        statement = f"SELECT id FROM {TASK_TABLE} WHERE blocked_by CONTAINS $x EXPLAIN"
        plan = await raw(ledger, statement, {"x": blocker})
        assert index_served(plan) and not scans_table(plan, TASK_TABLE), (
            f"`blocked_by CONTAINS $x` is not index-served: {operators(plan)}"
        )
        # CONTROL — the SAME statement with the index removed IS a TableScan (the walker can see one).
        index_rows = await raw(ledger, f"INFO FOR TABLE {TASK_TABLE}")
        names = [name for name in (index_rows or {}).get("indexes", {}) if "blocked_by" in name]
        assert len(names) == 1, f"expected exactly one blocked_by index: {names}"
        await raw(ledger, f"REMOVE INDEX {names[0]} ON TABLE {TASK_TABLE}")
        control = await raw(ledger, statement, {"x": blocker})
        assert scans_table(control, TASK_TABLE), (
            f"CONTROL failed: without the index the walker saw no TableScan: {operators(control)}"
        )
