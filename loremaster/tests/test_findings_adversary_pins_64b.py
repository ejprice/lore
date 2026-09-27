"""Contract r2 — packet 64b-i: the adversary's MISSING PINS (``REPORT-adversary-64b.md`` §A, graded
``d8ea4ba``), LANDED AST-EQUAL (contract-64b-r2; tests ONLY). Every test body below is byte-for-byte the
adversary's ``test_adv64b_missing_pins.py`` (pasted in its §INSTRUMENTS); the ONLY differences — each proven
by the AST receipt in ``REPORT-contract-64b-r2.md`` §AST — are (1) this docstring (the original said "never
committed to the repo", false here), (2) the import SOURCES: the adversary imported the post-fold
``_governed_contract`` (its reference applied §HELD), and at HEAD the finding substrate still lives in the
packet-64 ADD-ONLY module until the §HELD fold repoints these very lines, (3) four imports the original
bound but never used (``inspect``, ``principals``, ``IllegalTransitionError``, ``bare`` — ruff F401), and (4)
``noqa`` comments + line re-wraps (neither is AST), and (5) ONE adapted leg — MP-8's "one site" bucket
(DEVIATION D-r2-MP8, commented in place).

Each pin kills a named wrong build that SURVIVED the r1 contract (MP-1 WB1 set_scope oracle · MP-2 WB2
visible-deny served as not-found · MP-3 WB17 supersedes-by-id unfiltered · MP-4 WB3 classifier authorizes
READ · MP-5 WB4 cached Subject · MP-6 WB19 annotate drops ``actor_agent`` · MP-7 WB10 a second registry read
· MP-8 WB21 a private identity compare · MP-11 WB22b ``--table finding`` also migrates memory). The CLASS
each belongs to is swept GENERATED in ``test_findings_classes_64b.py`` (amendment 8 §6); these are the
instances.

Live TEST store ``:18000`` (NEVER :18500); per-test databases, reaped.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from _governed_contract_64 import finding_world, new_row_id
from _surreal_harness import run
from loremaster.findings import FindingNotFoundError
from surrealdb import RecordID
from test_findings_governance_64b import _inject_after_gate

from loremaster import governed, server

if TYPE_CHECKING:
    from loremaster.server import AppContext

    # NOT an adversary line (added by contract-64b-r2; comments and this block are outside the AST receipt's
    # body compare — it is an import-guarded declaration): the RULED dispatcher surface every pin below
    # drives, as a TYPED CALL (amendment 8 §5 MP-9). Until the build lands it, a mypy error OWNED by bound
    # ``packet-64b-i-contract`` (#461) — which is what REGISTERS this file's RED@HEAD legs with the currency
    # gate.
    async def _ruled_64b_i_dispatcher_shape(context: AppContext) -> None:
        """kickoff §6 / am-2 §1: ``capability=``; kickoff §5: ``scope=``."""
        await context.findings(action="set_scope", id_or_number=7, scope="server", capability="cap")


_MISSING_ID = "no_such_finding_id"


def _same_bytes(invisible: BaseException, missing: BaseException, row_id: str) -> None:
    left = str(invisible).replace(row_id, "<ID>")
    right = str(missing).replace(_MISSING_ID, "<ID>")
    assert left == right, f"invisible vs nonexistent differ (existence oracle): {left!r} vs {right!r}"


# MP-1 (WB1) — FK-6 ∀ WRITE verbs × ∀ address forms: set_scope was the one write verb never driven invisible.
async def test_MP1_set_scope_on_an_invisible_row_is_not_found_byte_identical_by_id_and_number(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        row_id = await world.seed(row_id=new_row_id("mp1"), number=7801, owner="ag-a1", scope_key="A")
        before = await world.row(row_id)
        for address, missing_address in ((row_id, _MISSING_ID), (7801, 7899)):
            with pytest.raises(FindingNotFoundError) as invisible:
                await world.findings(
                    "ag-b1", action="set_scope", id_or_number=address, scope=world.scopes["B"]
                )
            with pytest.raises(FindingNotFoundError) as missing:
                await world.findings(
                    "ag-b1", action="set_scope", id_or_number=missing_address, scope=world.scopes["B"]
                )
            if isinstance(address, str):
                _same_bytes(invisible.value, missing.value, row_id)
            else:
                assert str(invisible.value).replace("7801", "<N>") == str(missing.value).replace(
                    "7899", "<N>"
                )
        assert await world.row(row_id) == before


# MP-2 (WB2) — the OTHER direction, ∀ address forms: a VISIBLE-but-unwritable row is a GovernedDenied, never a
# not-found that contradicts `get` (the sibling agent can READ ag-a1's principal-private row).
@pytest.mark.parametrize("verb", ["acknowledge", "annotate", "set_scope"])
async def test_MP2_a_visible_but_unwritable_row_by_ID_is_denied_never_not_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, verb: str
) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        row_id = await world.seed(
            row_id=new_row_id("mp2"), number=7811, owner="ag-a1", scope_key="principal-private"
        )
        before = await world.row(row_id)
        extra: dict[str, Any] = {"note": "n"} if verb == "annotate" else {}
        if verb == "set_scope":
            extra = {"scope": "server"}
        with pytest.raises(governed.GovernedDenied) as denied:
            await world.findings("ag-a2", action=verb, id_or_number=row_id, **extra)
        assert not isinstance(denied.value, FindingNotFoundError)
        assert await world.row(row_id) == before


# MP-3 (WB17) — report(supersedes=) through the read filter ∀ address forms (the contract drives a NUMBER
# only).
async def test_MP3_supersedes_an_invisible_ID_is_not_found_byte_identical_and_writes_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        hidden = await world.seed(row_id=new_row_id("mp3"), number=7821, owner="ag-a1", scope_key="A")
        kwargs = {"action": "report", "subject": "s", "body": "", "area": "a", "category": "c"}
        with pytest.raises(FindingNotFoundError) as invisible:
            await world.findings("ag-b1", supersedes=hidden, **kwargs)
        with pytest.raises(FindingNotFoundError) as missing:
            await world.findings("ag-b1", supersedes=_MISSING_ID, **kwargs)
        _same_bytes(invisible.value, missing.value, hidden)
        assert len(await run(world.admin_conn, "SELECT VALUE id FROM finding")) == 1, "a successor linked it"


# MP-4 (WB3) — the zero-row classifier's DENY branch is keyed on the PASSED action: a fresh row the subject
# can still READ but no longer WRITE (re-scoped to its principal's private scope) is a GovernedConflict, never
# the ledger's "lost a concurrent race … status moved to <same status>" (a false statement: nothing moved).
async def test_MP4_rescoped_to_readable_but_unwritable_is_a_governed_conflict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        row_id = await world.seed(
            row_id=new_row_id("mp4"), number=7831, owner="ag-a1", scope_key="AB", status="acknowledged"
        )
        _inject_after_gate(
            monkeypatch,
            world,
            "UPDATE type::record('finding', $id) SET scope = 'principal-private'",
            {"id": row_id},
        )
        with pytest.raises(governed.GovernedConflict):
            await world.findings("ag-a2", action="resolve", id_or_number=7831)
        assert (await world.row(row_id))["status"] == "acknowledged"


# MP-5 (WB4) — LIFECYCLE: a household revocation takes effect on the NEXT call (no Subject outlives its call).
async def test_MP5_a_revoked_household_member_is_refused_on_its_next_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        first = await world.seed(row_id=new_row_id("mp5"), number=7841, owner="ag-a1", scope_key="AB")
        second = await world.seed(row_id=new_row_id("mp5"), number=7842, owner="ag-a1", scope_key="AB")
        await world.findings("ag-b1", action="acknowledge", id_or_number=7841)  # CONTROL: bob is householded
        assert (await world.row(first))["status"] == "acknowledged"
        keep_store = world.ctx._keep_store  # noqa: SLF001
        await keep_store.remove_household_member(
            keep_id=world.scopes["AB"].partition(":")[2], member_email=world.emails["bob"]
        )
        before = await world.row(second)
        with pytest.raises((governed.GovernedDenied, FindingNotFoundError)):
            await world.findings("ag-b1", action="acknowledge", id_or_number=7842)
        assert await world.row(second) == before, (
            "a REVOKED member's write landed (a stale Subject authorized it)"
        )


# MP-6 (WB19) — am-2 §3 ∀ appended events: every event-appending verb stamps `actor_agent` (the contract pins
# it on `resolve` only; `annotate` builds its own event dict).
@pytest.mark.parametrize(
    ("verb", "seed_status", "extra"),
    [("acknowledge", "open", {}), ("wontfix", "open", {}), ("annotate", "resolved", {"note": "n"})],
)
async def test_MP6_every_appended_event_carries_the_actor_agent_link(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, verb: str, seed_status: str, extra: dict[str, Any]
) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        row_id = await world.seed(
            row_id=new_row_id("mp6"), number=7851, owner="ag-a1", scope_key="AB", status=seed_status
        )
        rendered = await world.findings("ag-b2", action=verb, id_or_number=7851, **extra)
        event = ((await world.row(row_id))["provenance"] or {})["events"][-1]
        assert event.get("actor") == "ag-b2", event
        assert str(event.get("actor_agent")) == str(RecordID("agent", world.agent_ids["ag-b2"])), event
        if verb != "annotate":
            assert "ag-b2" in rendered, (
                f"the served transition line does not name the derived actor: {rendered!r}"
            )


# MP-7 (WB10) — R8 on the REAL identity path: ONE agent-row read per governed write, counted at the store seam
# (every statement touching the `agent` table), not at one registry method name.
async def test_MP7_a_governed_write_reads_the_agent_row_at_most_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from _governed_contract import patch_shared_object_everywhere  # noqa: PLC0415, F401
    from loremaster.store import _txn  # noqa: PLC0415, F401

    async with finding_world(monkeypatch, tmp_path) as world:
        registry = world.ctx.agent_registry
        calls = {"get_agent": 0, "_select_row": 0}
        for name in list(calls):
            real = getattr(registry, name)

            def _wrap(real: Any = real, name: str = name) -> Any:
                async def _spy(*args: Any, **kwargs: Any) -> Any:
                    calls[name] += 1
                    return await real(*args, **kwargs)

                return _spy

            monkeypatch.setattr(registry, name, _wrap())
        await world.findings("ag-a1", action="report", subject="s", body="", area="a", category="c")
        assert calls["get_agent"] + calls["_select_row"] <= 1, calls


# MP-8 (WB21) — kickoff §6 rider (iv), as amended (am-2 §1 item 2): EXACTLY ONE production comparison of a
# supplied agent=/session= against the capability's own row — a second compare is a private copy.
def test_MP8_exactly_one_identity_compare_site_in_production() -> None:
    # DEVIATION D-r2-MP8 (REPORT-contract-64b-r2 §DEVIATIONS): the adversary's "one site" leg bucketed LINE
    # NUMBERS
    # (``line // 25``) — two compares 5 lines apart straddle a bucket boundary on a CORRECT build (measured
    # on the
    # r2 reference: lines 3897/3902 → buckets 155/156, RED). "One site" is re-keyed to its meaning: the SAME
    # enclosing function. Everything else is the adversary's, verbatim.
    tree = ast.parse(Path(server.__file__).read_text(encoding="utf-8"))
    owners: dict[int, str] = {}
    for function in ast.walk(tree):
        if isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
            for child in ast.walk(function):
                owners.setdefault(id(child), function.name)
    sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and any(isinstance(op, ast.NotEq) for op in node.ops):
            text = ast.unparse(node)
            if re.search(r"\b(agent|session)\b\s*!=\s*own_row\.(name|session)", text):
                sites.append((owners.get(id(node), "<module>"), text))
    assert len(sites) == 2, f"expected ONE agent= and ONE session= compare (one site): {sites}"
    assert len({function for function, _ in sites}) == 1, f"the compares are not in one site: {sites}"


# MP-11 (WB22b) — ∀ table dispositions: a PROCEEDING --table finding writes NOTHING outside `finding` (+ the
# project-keep mint). The contract asserts byte-inertness of the OTHER tables on the REFUSAL path only.
async def test_MP11_migrate_finding_leaves_every_other_governed_table_byte_identical() -> None:
    from _governed_contract import seed_memory_legacy  # noqa: PLC0415
    from _governed_contract_64 import frozen_asserted_finding_ddl  # noqa: PLC0415
    from test_findings_migrate_64b import (  # noqa: PLC0415
        _migrate_world,
        _seed_legacy,
        _upgrade_finding_schema,
    )

    async with _migrate_world(frozen_asserted_finding_ddl()) as world:
        await seed_memory_legacy(world.connection, row_id="legacy_memory", dim=8)
        await _seed_legacy(world, 2)
        await _upgrade_finding_schema(world)
        before = await run(world.connection, "SELECT * FROM memory ORDER BY id")
        result = await world.migrate()
        assert not result.refused and result.backfilled == 2, result
        assert await run(world.connection, "SELECT * FROM memory ORDER BY id") == before, (
            "--table finding migrated MEMORY rows too"
        )
