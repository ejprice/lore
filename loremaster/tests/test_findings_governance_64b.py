"""Contract — packet 64b-i: the GOVERNED WRITE SIDE of ``lore_findings`` (kickoff rulings ``e5fa7f9`` §4.1/
§4.3/§5 + §12 F3/F4 row, as confirmed by amendment 2 §7). Authored by ``contract-64b`` (Opus 5.5 —
contract tests ONLY).

EVERY pin runs over the REAL tool dispatcher (``AppContext.findings``) on a REAL store, in the F3 world
(``_governed_contract_64.finding_world``): alice (ag-a1, ag-a2) and bob (ag-b1, ag-b2) as members, carol
(ag-c1) as admin; keeps ``A`` (alice only), ``B`` (bob only), ``AB`` + ``project`` (both). Findings are
SEEDED RAW (owner + scope explicit) so each pin exercises ONLY the verb under test.

THE RULES (authz §4 3-way write rule, via the ONE PDP brain — nothing new in the PDP):
- a keep-scoped finding is WRITE-able (acknowledge/resolve/wontfix/annotate) by ANY household member;
- a ``principal-private``/``agent-private``/``server`` finding only by its EXACT (principal, agent)
  creator — a SIBLING agent of the same principal may READ a principal-private row but NOT write it;
- admin: any row, AUDITED when a member could not (+1 audit row in the SAME transaction);
- ``wontfix`` is a WRITE, never a soft-delete (nothing vanishes);
- ``report`` is a CREATE owned by the Subject; scope = ``resolve_write_scope(subject, scope, default=
  <project keep>)`` — an explicit keep the caller is not householded in DENIES; ``server`` is grantable;
- ``report(supersedes=X)`` mutates nothing on X; X resolves THROUGH the read filter;
- ``set_scope`` (NEW) = SET_SCOPE: the exact creator pair ∧ a grantable target; admin any, audited;
- ``resolve_many``/``acknowledge_many``: per ITEM, best-effort preserved — a denied item is that item's
  failure and never vetoes the rest;
- a zero-row CAS is classified by the ONE ``governed.classify_zero_row_cas``: a re-scope that landed
  between the gate and the CAS ⇒ ``GovernedConflict``; a concurrent status winner ⇒ the ledger's own
  ``IllegalTransitionError`` naming the FRESH state.

FK-6 (r1's reading — RULED by packet-64 amendment 7 §4, with the ONE-pre-read mechanism: invisibility is
DERIVED from the gate's own pre-read, ``GovernedInvisible(GovernedDenied)``): a WRITE verb addressing a
finding the caller cannot READ fails with the SAME ``FindingNotFoundError`` bytes as a nonexistent address
(no existence oracle —
63-rulings §4.3; the kickoff states it for ``report(supersedes=X)`` §5 and for reads §10, and a write
verb's number→row resolution IS a read). A row the caller CAN read but not write is a
``GovernedDenied`` (the sibling-agent case) — visible, so no oracle.

Every behavioural pin carries ``@observes_routing("lore_findings", <verb>)`` — the #420 STRUCTURAL half;
the HELD patch moves each verb from ``_GOVERNED_VERBS_PENDING_ROUTING`` to ``_GOVERNED_VERBS_ROUTED``.

Live TEST store ``:18000`` (NEVER :18500). Per-test databases, reaped.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from _governed_contract import observes_routing, patch_shared_object_everywhere
from _governed_contract_64 import (
    HOSTILE_FORGED_LINE_START,
    HOSTILE_FREE_TEXT,
    FindingWorld,
    bare,
    finding_world,
    new_row_id,
)
from _surreal_harness import run
from loremaster.findings import FindingNotFoundError, IllegalTransitionError

from loremaster import governed

if TYPE_CHECKING:
    from loremaster.findings import FindingLedger
    from loremaster.governed import classify_zero_row_cas
    from loremaster.store._txn import StoreHandle

    import lorerunes

    # 64b-i's RULED, not-yet-built signatures this file pins — TYPED CALLS (amendment 8 §5, MP-9: mypy's
    # ``[call-arg]`` checks the SHAPE, never just the name; permanent signature pins). Until the build lands
    # them,
    # mypy errors OWNED by `scripts/pending_contracts.yaml` bound `packet-64b-i-contract` (#461).
    # Runtime-inert.
    # DUAL (r2): r1's name-only ``_RULED_64B_I`` tuple (``FindingLedger.set_scope``,
    # ``classify_zero_row_cas``) is
    # replaced — a coherent wrong-SHAPE build was mypy-identical to the reference under it
    # (REPORT-adversary-64b §FK9).
    async def _ruled_64b_i_governance_shapes(
        ledger: FindingLedger, subject: lorerunes.Subject, handle: StoreHandle
    ) -> None:
        """kickoff §4.4 (set_scope) + am-7 §2 (``subject=``) + #407 / am-7 §5 FK-3 (the classifier's "
        "shape)."""
        await ledger.set_scope(7, "server", subject=subject)
        await ledger.acknowledge(7, "ag", None, subject=subject)
        await ledger.annotate(7, "ag", "n", subject=subject)
        await classify_zero_row_cas(
            handle,
            table="finding",
            row_id="x",
            subject=subject,
            action=lorerunes.Action.WRITE,
            ledger_verdict=lambda row: row,
        )


#: (actor agent, owner agent, scope key, allowed?, audit delta) — the 3-way rule's discriminating cases.
#: ≥2 principals, ≥2 agents each, disjoint households, the admin control (kickoff §12 fixture floor).
_WRITE_CASES: tuple[tuple[str, str, str, bool, int], ...] = (
    ("ag-b1", "ag-a1", "AB", True, 0),  # household non-reporter on a keep row: allowed, unaudited
    ("ag-b2", "ag-a1", "project", True, 0),  # the project keep's household (a second keep value)
    ("ag-a1", "ag-a1", "principal-private", True, 0),  # the exact creator pair
    ("ag-c1", "ag-a1", "principal-private", True, 1),  # admin bypass: allowed, AUDITED
    ("ag-a2", "ag-a1", "principal-private", False, 0),  # SIBLING agent: can READ, may not WRITE
)
#: (actor, owner, scope) where the caller cannot even READ the row ⇒ not-found, byte-identical (FK-6).
_INVISIBLE_CASES: tuple[tuple[str, str, str], ...] = (
    ("ag-b1", "ag-a1", "A"),  # alice's keep, bob not householded
    ("ag-b2", "ag-a2", "principal-private"),  # another principal's private row
)

_VERB_EDGES: dict[str, tuple[str, str | None]] = {
    # verb → (seed status, the status the verb lands; None ⇒ status-preserving)
    "acknowledge": ("open", "acknowledged"),
    "resolve": ("acknowledged", "resolved"),
    "wontfix": ("open", "wontfix"),
    "annotate": ("resolved", None),
}


def _verb_kwargs(verb: str, number: int) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"action": verb, "id_or_number": number}
    if verb == "annotate":
        kwargs["note"] = "a correction"
    return kwargs


def _normalise_address(text: str, number: int) -> str:
    return re.sub(rf"\b{number}\b", "<N>", text)


async def _drive_write_cases(world: FindingWorld, *, action: str) -> None:
    """Run every ``_WRITE_CASES`` row for ``action`` on its own fresh row; assert allow/deny + audit."""
    verb = action
    seed_status, landed = _VERB_EDGES[verb]
    for index, (actor, owner, scope_key, allowed, audit_delta) in enumerate(_WRITE_CASES):
        number = 2000 + index
        row_id = await world.seed(
            row_id=new_row_id(verb), number=number, owner=owner, scope_key=scope_key, status=seed_status
        )
        before = await world.row(row_id)
        audit_before = await world.audit_count()
        label = f"{verb} by {actor} on {owner}'s {scope_key} finding"
        if not allowed:
            with pytest.raises(governed.GovernedDenied):
                await world.findings(actor, **_verb_kwargs(verb, number))
            assert await world.row(row_id) == before, f"{label}: a DENIED write mutated the row"
            assert await world.audit_count() == audit_before, f"{label}: a denied write left an audit row"
            continue
        await world.findings(actor, **_verb_kwargs(verb, number))
        after = await world.row(row_id)
        if landed is not None:
            assert after["status"] == landed, f"{label}: status {after['status']!r}, expected {landed!r}"
        assert (
            len((after["provenance"] or {}).get("events") or [])
            == len((before["provenance"] or {}).get("events") or []) + 1
        ), label
        for column in ("owner_principal", "owner_agent", "scope", "number", "created_by"):
            assert after[column] == before[column], (
                f"{label}: a status verb moved the governed/identity column {column}"
            )
        assert await world.audit_count() == audit_before + audit_delta, (
            f"{label}: audit delta {await world.audit_count() - audit_before}, expected {audit_delta}"
        )


async def _drive_invisible_cases(world: FindingWorld, *, action: str) -> None:
    """FK-6: an invisible row ⇒ ``FindingNotFoundError`` with the SAME bytes as a nonexistent address."""
    verb = action
    seed_status, _landed = _VERB_EDGES[verb]
    nonexistent = 9990
    with pytest.raises(FindingNotFoundError) as missing:
        await world.findings("ag-b1", **_verb_kwargs(verb, nonexistent))
    for index, (actor, owner, scope_key) in enumerate(_INVISIBLE_CASES):
        number = 3000 + index
        row_id = await world.seed(
            row_id=new_row_id(f"inv_{verb}"),
            number=number,
            owner=owner,
            scope_key=scope_key,
            status=seed_status,
        )
        before = await world.row(row_id)
        with pytest.raises(FindingNotFoundError) as invisible:
            await world.findings(actor, **_verb_kwargs(verb, number))
        # the by-ID address too (the one-pre-read path — it never touches the number index): an invisible id
        # must be the SAME not-found as a nonexistent id, never a GovernedDenied that confirms existence.
        with pytest.raises(FindingNotFoundError) as invisible_by_id:
            await world.findings(actor, **{**_verb_kwargs(verb, number), "id_or_number": row_id})
        with pytest.raises(FindingNotFoundError) as missing_by_id:
            await world.findings(
                actor, **{**_verb_kwargs(verb, number), "id_or_number": "no_such_finding_id"}
            )
        assert str(invisible_by_id.value).replace(row_id, "<ID>") == str(missing_by_id.value).replace(
            "no_such_finding_id", "<ID>"
        ), (str(invisible_by_id.value), str(missing_by_id.value))
        assert _normalise_address(str(invisible.value), number) == _normalise_address(
            str(missing.value), nonexistent
        ), (
            f"{verb} on an INVISIBLE finding must be byte-identical to a nonexistent one "
            "(no existence oracle): "
            f"{str(invisible.value)!r} vs {str(missing.value)!r}"
        )
        assert await world.row(row_id) == before


class TestTheStatusVerbsFollowTheThreeWayRule:
    """Kickoff §4.1 / §5 table rows 3–4: ∀ status verb × the discriminating cases. Kills: a verb that checks
    READ only (the sibling agent would pass), one that checks the principal only (same), one that ignores
    household (bob on keep:AB would deny), a status verb that also moves a governed column, an admin
    bypass without its audit, and an invisible-row oracle."""

    @observes_routing("lore_findings", "acknowledge")
    async def test_acknowledge(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """⚠ RED at HEAD (no capability=; no governance)."""
        async with finding_world(monkeypatch, tmp_path) as world:
            await _drive_write_cases(world, action="acknowledge")
            await _drive_invisible_cases(world, action="acknowledge")

    @observes_routing("lore_findings", "resolve")
    async def test_resolve(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """⚠ RED at HEAD."""
        async with finding_world(monkeypatch, tmp_path) as world:
            await _drive_write_cases(world, action="resolve")
            await _drive_invisible_cases(world, action="resolve")

    @observes_routing("lore_findings", "wontfix")
    async def test_wontfix_is_a_write_never_a_soft_delete(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD. And ``wontfix`` VANISHES nothing: every closed row is still in the store with its
        number and its history (the household member closed it; the 3-way delete clause never fires)."""
        async with finding_world(monkeypatch, tmp_path) as world:
            await _drive_write_cases(world, action="wontfix")
            await _drive_invisible_cases(world, action="wontfix")
            closed = await run(world.admin_conn, "SELECT number FROM finding WHERE status = 'wontfix'")
            assert len(closed) == sum(1 for case in _WRITE_CASES if case[3]), closed

    @observes_routing("lore_findings", "annotate")
    async def test_annotate_is_a_status_preserving_write(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD. ``annotate`` by a household NON-reporter is allowed (the collaborative correction
        a keep exists for); the status never moves (seeded ``resolved``)."""
        async with finding_world(monkeypatch, tmp_path) as world:
            await _drive_write_cases(world, action="annotate")
            await _drive_invisible_cases(world, action="annotate")
            assert not await run(
                world.admin_conn,
                "SELECT id FROM finding WHERE number >= 2000 AND number < 3000 AND status != 'resolved'",
            )


# =========================================================================== #
# report — the CREATE-OWNS-IT write.
# =========================================================================== #


class TestReportStampsTheSubjectAndResolvesItsScope:
    """Kickoff §5 table row 2 / §12 F4 row / F4 fuzz (amendment 2 §4 hostile set, the ``scope=`` half —
    the retired names are refused at the MCP layer in the identity file)."""

    @observes_routing("lore_findings", "report")
    async def test_a_report_is_owned_by_the_subject_and_defaults_to_the_project_keep(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD. Two reporters of two principals: each row's owner pair is EXACTLY that reporter's
        (principal, agent) and its scope is the PROJECT keep (not the reporter's session keep, not a
        keep:AB it could also grant). The render names the landed scope (a scope is SEEN, never silent)."""
        async with finding_world(monkeypatch, tmp_path) as world:
            for agent in ("ag-a2", "ag-b1"):
                rendered = await world.findings(
                    agent, action="report", subject=f"by {agent}", body="", area="a", category="c"
                )
                assert world.scopes["project"] in rendered, (
                    f"the report render must name the landed scope: {rendered!r}"
                )
            rows = {
                row["subject"]: row
                for row in await run(
                    world.admin_conn, "SELECT subject, owner_principal, owner_agent, scope FROM finding"
                )
            }
            for agent in ("ag-a2", "ag-b1"):
                row = rows[f"by {agent}"]
                assert bare(row["owner_agent"]) == world.agent_ids[agent], (agent, row)
                assert bare(row["owner_principal"]) == world.pids[world.principal_of(agent)], (agent, row)
                assert row["scope"] == world.scopes["project"], (agent, row)

    @pytest.mark.parametrize(
        ("scope_key", "lands"),
        [("AB", True), ("A", True), ("B", False), ("server", True), ("principal-private", True)],
    )
    async def test_an_explicit_scope_is_a_pdp_validated_request(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, scope_key: str, lands: bool
    ) -> None:
        """⚠ RED at HEAD. alice's explicit ``scope=``: her keeps and the fixed scopes land AS REQUESTED
        (``server`` IS grantable — lands as server, not refused); bob's keep:B DENIES (not householded),
        writing NOTHING. Kills: a build that ignores ``scope=`` (always project) and one that trusts it."""
        async with finding_world(monkeypatch, tmp_path) as world:
            target = world.scopes.get(scope_key, scope_key)
            if not lands:
                with pytest.raises(governed.GovernedDenied):
                    await world.findings(
                        "ag-a1", action="report", subject="x", body="", area="a", category="c", scope=target
                    )
                assert await run(world.admin_conn, "SELECT VALUE id FROM finding") == []
                return
            await world.findings(
                "ag-a1", action="report", subject="x", body="", area="a", category="c", scope=target
            )
            assert await run(world.admin_conn, "SELECT VALUE scope FROM finding") == [target]

    @pytest.mark.parametrize("action", ["report", "set_scope"])
    async def test_a_hostile_scope_is_refused_and_never_forged_into_the_served_text(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, action: str
    ) -> None:
        """⚠ RED at HEAD (``scope=`` is not a finding param). 64b-i makes ``scope`` a CALLER-SUPPLIED served
        param for the first time on ``lore_findings`` — and the shared grant refusal (``governed.
        resolve_write_scope``) echoes the requested scope into its served text. So a hostile ``scope=``
        (newlines + a row-shaped forgery + backtick runs) must be REFUSED (it is not grantable), write
        NOTHING (report) / change NOTHING (set_scope), and its forged row must never reach a LINE START of
        the served refusal. Both ``scope=``-taking verbs. CONTROL: the detector fires on an unescaped echo
        of the same value, so a pass is not the detector being blind."""
        unescaped_echo = f"scope {HOSTILE_FREE_TEXT} is not grantable"
        assert HOSTILE_FORGED_LINE_START in unescaped_echo, "CONTROL: the forgery detector cannot fire"
        async with finding_world(monkeypatch, tmp_path) as world:
            own = await world.seed(
                row_id=new_row_id("hostile"), number=4101, owner="ag-a1", scope_key="principal-private"
            )
            before = await world.row(own)
            kwargs: dict[str, Any] = (
                {"subject": "x", "body": "", "area": "a", "category": "c"}
                if action == "report"
                else {"id_or_number": 4101}
            )
            with pytest.raises(governed.GovernedDenied) as refused:
                await world.findings("ag-a1", action=action, scope=HOSTILE_FREE_TEXT, **kwargs)
            served = str(refused.value)
            assert HOSTILE_FORGED_LINE_START not in served, (
                f"the hostile scope's row-shaped forgery reached a LINE START of the refusal: {served!r}"
            )
            assert len(await run(world.admin_conn, "SELECT VALUE id FROM finding")) == 1, (
                "a refused hostile scope wrote a row"
            )
            assert await world.row(own) == before, "a refused hostile scope changed the row"

    async def test_a_supersede_of_an_invisible_finding_is_byte_identical_to_a_nonexistent_one(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD (unfiltered ``supersedes`` resolution — an existence oracle). Bob superseding
        alice's keep:A finding ⇒ ``FindingNotFoundError`` with the SAME bytes as superseding a number that
        does not exist (address normalised); nothing written."""
        async with finding_world(monkeypatch, tmp_path) as world:
            await world.seed(row_id=new_row_id("hidden"), number=4001, owner="ag-a1", scope_key="A")
            with pytest.raises(FindingNotFoundError) as invisible:
                await world.findings(
                    "ag-b1", action="report", subject="s", body="", area="a", category="c", supersedes=4001
                )
            with pytest.raises(FindingNotFoundError) as missing:
                await world.findings(
                    "ag-b1", action="report", subject="s", body="", area="a", category="c", supersedes=4999
                )
            assert _normalise_address(str(invisible.value), 4001) == _normalise_address(
                str(missing.value), 4999
            )
            assert len(await run(world.admin_conn, "SELECT VALUE id FROM finding")) == 1

    async def test_a_supersede_mints_a_row_in_the_superseders_scope_never_the_predecessors(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD. Bob supersedes alice's VISIBLE keep:AB finding: the successor is owned by BOB, its
        scope is the DEFAULT (project) — NOT inherited keep:AB — and the predecessor is byte-unchanged (a
        finding supersede mutates nothing on X). An explicit ``scope=keep:B`` then lands keep:B."""
        async with finding_world(monkeypatch, tmp_path) as world:
            predecessor = await world.seed(
                row_id=new_row_id("pred"), number=4002, owner="ag-a1", scope_key="AB"
            )
            before = await world.row(predecessor)
            await world.findings(
                "ag-b1", action="report", subject="succ", body="", area="a", category="c", supersedes=4002
            )
            await world.findings(
                "ag-b1",
                action="report",
                subject="succ2",
                body="",
                area="a",
                category="c",
                supersedes=4002,
                scope=world.scopes["B"],
            )
            successors = {
                row["subject"]: row
                for row in await run(
                    world.admin_conn,
                    "SELECT subject, scope, owner_agent FROM finding WHERE supersedes != NONE",
                )
            }
            assert successors["succ"]["scope"] == world.scopes["project"], successors
            assert successors["succ2"]["scope"] == world.scopes["B"], successors
            assert bare(successors["succ"]["owner_agent"]) == world.agent_ids["ag-b1"], successors
            assert await world.row(predecessor) == before, "a finding supersede mutated its predecessor"


# =========================================================================== #
# set_scope — the NEW served SET_SCOPE verb (#429's served consumer).
# =========================================================================== #


class TestSetScopeIsOwnerOnlyToAGrantableTarget:
    """Kickoff §5 table (``set_scope`` row) + §0 reading 3: owner-only (exact creator pair), grantable
    target; admin any, audited. The substrate branch is pinned in ``test_governed_substrate_64b.py``; this
    is the SERVED verb over the real dispatcher."""

    @observes_routing("lore_findings", "set_scope")
    async def test_the_owner_admin_and_the_refusals(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD (``set_scope`` is not a finding verb). Four legs, one world."""
        async with finding_world(monkeypatch, tmp_path) as world:
            own = await world.seed(
                row_id=new_row_id("ss"), number=5001, owner="ag-a1", scope_key="principal-private"
            )
            rendered = await world.findings(
                "ag-a1", action="set_scope", id_or_number=5001, scope=world.scopes["A"]
            )
            assert (await world.row(own))["scope"] == world.scopes["A"] and world.scopes["A"] in rendered
            shared = await world.seed(row_id=new_row_id("ss"), number=5002, owner="ag-a1", scope_key="AB")
            with pytest.raises(governed.GovernedDenied):  # a household NON-owner may not re-scope
                await world.findings("ag-b1", action="set_scope", id_or_number=5002, scope=world.scopes["B"])
            with pytest.raises(governed.GovernedDenied):  # the owner, to a keep she is not householded in
                await world.findings("ag-a1", action="set_scope", id_or_number=5002, scope=world.scopes["B"])
            assert (await world.row(shared))["scope"] == world.scopes["AB"]
            foreign = await world.seed(
                row_id=new_row_id("ss"), number=5003, owner="ag-b1", scope_key="principal-private"
            )
            audit_before = await world.audit_count()
            await world.findings("ag-c1", action="set_scope", id_or_number=5003, scope=world.scopes["AB"])
            assert (await world.row(foreign))["scope"] == world.scopes["AB"]
            assert await world.audit_count() == audit_before + 1, (
                "an admin re-scope of a foreign row must be audited"
            )


# =========================================================================== #
# The best-effort batches — per ITEM.
# =========================================================================== #


class TestTheBatchesAreBestEffortPerItem:
    """Kickoff §5 table (batch row): each item runs its own gate + shell; a DENIED item renders as that
    item's failure (its ``GovernedDenied`` text) and NEVER vetoes the rest."""

    @pytest.mark.parametrize(
        ("verb", "seed_status", "landed"),
        [
            pytest.param("resolve_many", "acknowledged", "resolved", marks=[]),
            pytest.param("acknowledge_many", "open", "acknowledged", marks=[]),
        ],
    )
    async def test_a_denied_item_is_its_own_failure(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, verb: str, seed_status: str, landed: str
    ) -> None:
        """⚠ RED at HEAD. ag-a2 (alice's SIBLING agent) over [ag-a1's principal-private (visible, NOT
        writable), a keep:AB row, a project row]: the two keep rows land, the private one is untouched, and
        the render carries the denied item's failure. Kills: a batch where one deny vetoes all, and one that
        silently skips the denied item."""
        async with finding_world(monkeypatch, tmp_path) as world:
            denied = await world.seed(
                row_id=new_row_id("b"),
                number=6001,
                owner="ag-a1",
                scope_key="principal-private",
                status=seed_status,
            )
            ok_ids = [
                await world.seed(
                    row_id=new_row_id("b"), number=6002, owner="ag-b1", scope_key="AB", status=seed_status
                ),
                await world.seed(
                    row_id=new_row_id("b"),
                    number=6003,
                    owner="ag-b2",
                    scope_key="project",
                    status=seed_status,
                ),
            ]
            denied_before = await world.row(denied)
            rendered = await world.findings(
                "ag-a2",
                action=verb,
                items=[{"id_or_number": 6001}, {"id_or_number": 6002}, {"id_or_number": 6003}],
            )
            assert await world.row(denied) == denied_before, "the denied item was mutated"
            for row_id in ok_ids:
                assert (await world.row(row_id))["status"] == landed, "a denied item VETOED its siblings"
            assert "6001" in rendered and ("denied" in rendered.lower() or "may not" in rendered.lower()), (
                rendered
            )

    @observes_routing("lore_findings", "resolve_many")
    async def test_resolve_many_routes_each_item_through_the_gate(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD. The routing observation for ``resolve_many``: a bob batch over bob-writable rows
        only lands, and an admin batch over a foreign private row lands AUDITED once per item."""
        async with finding_world(monkeypatch, tmp_path) as world:
            await world.seed(
                row_id=new_row_id("rm"),
                number=6101,
                owner="ag-a1",
                scope_key="principal-private",
                status="open",
            )
            await world.seed(
                row_id=new_row_id("rm"),
                number=6102,
                owner="ag-b1",
                scope_key="principal-private",
                status="open",
            )
            before = await world.audit_count()
            await world.findings(
                "ag-c1", action="resolve_many", items=[{"id_or_number": 6101}, {"id_or_number": 6102}]
            )
            assert await world.audit_count() == before + 2
            assert not await run(
                world.admin_conn,
                "SELECT id FROM finding WHERE number IN [6101, 6102] AND status != 'resolved'",
            )

    @observes_routing("lore_findings", "acknowledge_many")
    async def test_acknowledge_many_routes_each_item_through_the_gate(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD. bob acknowledges two keep:AB rows alice filed: both land, unaudited."""
        async with finding_world(monkeypatch, tmp_path) as world:
            await world.seed(
                row_id=new_row_id("am"), number=6201, owner="ag-a1", scope_key="AB", status="open"
            )
            await world.seed(
                row_id=new_row_id("am"), number=6202, owner="ag-a2", scope_key="AB", status="open"
            )
            before = await world.audit_count()
            await world.findings(
                "ag-b2", action="acknowledge_many", items=[{"id_or_number": 6201}, {"id_or_number": 6202}]
            )
            assert await world.audit_count() == before
            assert not await run(
                world.admin_conn,
                "SELECT id FROM finding WHERE number IN [6201, 6202] AND status != 'acknowledged'",
            )


# =========================================================================== #
# The zero-row CAS — TOCTOU and the lost race, through the ONE classifier (#407).
# =========================================================================== #


def _inject_after_gate(
    monkeypatch: pytest.MonkeyPatch, world: FindingWorld, statement: str, params: dict[str, Any]
) -> list[Any]:
    """Wrap ``governed.authorize_guarded`` (EVERY module-level binding, by identity) so the injected
    ``statement`` lands AFTER the Python gate returned its plan and BEFORE the ledger's guarded CAS runs —
    the deterministic TOCTOU window (63-rulings §10.6 rider iii; no 8-way race)."""
    real = governed.authorize_guarded
    plans: list[Any] = []

    async def _gate_then_inject(*args: Any, **kwargs: Any) -> Any:
        plan = await real(*args, **kwargs)
        plans.append(plan)
        await run(world.admin_conn, statement, params)
        return plan

    patch_shared_object_everywhere(
        monkeypatch, "authorize_guarded", real, _gate_then_inject, expect_in=("loremaster.governed",)
    )
    return plans


def _spy_classifier(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    real = vars(governed).get("classify_zero_row_cas")
    assert real is not None, "UNBUILT (#407): governed.classify_zero_row_cas does not exist"
    calls: list[Any] = []

    async def _spy(*args: Any, **kwargs: Any) -> Any:
        calls.append(kwargs.get("row_id"))
        return await real(*args, **kwargs)

    patch_shared_object_everywhere(
        monkeypatch, "classify_zero_row_cas", real, _spy, expect_in=("loremaster.governed",)
    )
    return calls


class TestAZeroRowCasIsClassifiedByTheOneHelper:
    """Kickoff §4.3 item 4 / §11 #407 row / rider (ii): two CONSTRUCTIONS, one helper — the ledger routes
    its zero-row rollback through ``governed.classify_zero_row_cas`` (spied, by identity)."""

    async def test_a_rescope_between_the_gate_and_the_cas_is_a_governed_conflict(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD. Bob resolves alice's keep:AB finding; between the gate and the CAS the row moves
        to keep:A (out of bob's WRITE reach). The in-store guard matches ZERO rows ⇒ ``GovernedConflict``
        (never a silent no-op, never "already resolved"); the status is untouched."""
        async with finding_world(monkeypatch, tmp_path) as world:
            row_id = await world.seed(
                row_id=new_row_id("toctou"), number=7001, owner="ag-a1", scope_key="AB", status="open"
            )
            calls = _spy_classifier(monkeypatch)
            _inject_after_gate(
                monkeypatch,
                world,
                "UPDATE type::record('finding', $id) SET scope = $scope",
                {"id": row_id, "scope": world.scopes["A"]},
            )
            with pytest.raises(governed.GovernedConflict):
                await world.findings("ag-b1", action="resolve", id_or_number=7001)
            row = await world.row(row_id)
            assert row["status"] == "open" and row["scope"] == world.scopes["A"], row
            assert calls, (
                "the ledger's zero-row rollback did not route through governed.classify_zero_row_cas (#407)"
            )

    async def test_a_concurrent_status_winner_is_the_ledgers_own_illegal_transition(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD. Bob resolves; between the gate and the CAS a concurrent writer resolved it first
        (the row is STILL bob-writable). ⇒ ``IllegalTransitionError`` naming the FRESH state
        ``resolved`` — the ledger's own lost-race verdict, NOT a ``GovernedConflict``."""
        async with finding_world(monkeypatch, tmp_path) as world:
            row_id = await world.seed(
                row_id=new_row_id("race"), number=7002, owner="ag-a1", scope_key="AB", status="acknowledged"
            )
            calls = _spy_classifier(monkeypatch)
            _inject_after_gate(
                monkeypatch,
                world,
                "UPDATE type::record('finding', $id) SET status = 'resolved'",
                {"id": row_id},
            )
            with pytest.raises(IllegalTransitionError) as lost:
                await world.findings("ag-b1", action="wontfix", id_or_number=7002)
            assert "resolved" in str(lost.value), str(lost.value)
            assert calls, "the lost race did not route through governed.classify_zero_row_cas (#407)"

    async def test_an_annotate_on_a_row_rescoped_away_is_a_governed_conflict(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD. The THIRD construction (the WHERE-less append): annotate has no status CAS, so its
        ONLY conjunct is the guard — a re-scope in the window ⇒ ``GovernedConflict`` and no event lands."""
        async with finding_world(monkeypatch, tmp_path) as world:
            row_id = await world.seed(row_id=new_row_id("annot"), number=7003, owner="ag-a1", scope_key="AB")
            before_events = len(((await world.row(row_id))["provenance"] or {}).get("events") or [])
            _inject_after_gate(
                monkeypatch,
                world,
                "UPDATE type::record('finding', $id) SET scope = $scope",
                {"id": row_id, "scope": world.scopes["A"]},
            )
            with pytest.raises(governed.GovernedConflict):
                await world.findings("ag-b1", action="annotate", id_or_number=7003, note="late")
            assert len(((await world.row(row_id))["provenance"] or {}).get("events") or []) == before_events


# =========================================================================== #
# #417 — the guard enters the ledger's shell AND-bound at the top level; ONE pre-read.
# =========================================================================== #


def _record_transactions(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    from loremaster.store import _txn  # noqa: PLC0415

    real = _txn.execute_transaction
    statements: list[str] = []

    async def _recording(statement_text: str, *args: Any, **kwargs: Any) -> Any:
        statements.append(statement_text)
        return await real(statement_text, *args, **kwargs)

    patch_shared_object_everywhere(
        monkeypatch, "execute_transaction", real, _recording, expect_in=("loremaster.store._txn",)
    )
    return statements


def _balanced_group_end(text: str, start: int) -> int:
    """Index just past the parenthesised group opening at ``text[start] == '('``."""
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    raise AssertionError(f"unbalanced parentheses from {start}: {text!r}")


class TestTheGuardIsAndBoundAtTheTopLevelOfTheShell:
    """#417 (kickoff §11 row): 64 composes NO new IR node — the write guard enters the ledger's shell as
    caller SurrealQL, ``WHERE (<cas>) AND (<guard>)``, the ledger predicate PARENTHESISED by the shell,
    so no top-level ``OR`` in a ledger predicate can escape the guard. Observed on the EXECUTED statement."""

    async def test_the_executed_update_carries_the_plans_guard_and_bound(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD (the shell carries no guard). The plan's own ``guard_fragment`` appears in the
        executed ``UPDATE … finding`` statement immediately after ``WHERE (<balanced group>) AND``."""
        async with finding_world(monkeypatch, tmp_path) as world:
            await world.seed(
                row_id=new_row_id("g417"), number=8001, owner="ag-a1", scope_key="AB", status="open"
            )
            plans = _inject_after_gate(monkeypatch, world, "RETURN true", {})
            statements = _record_transactions(monkeypatch)
            await world.findings("ag-b1", action="acknowledge", id_or_number=8001)
            assert plans, (
                "the acknowledge never passed through governed.authorize_guarded (kickoff §4.3 item 1)"
            )
            guard = plans[-1].guard_fragment
            updates = [text for text in statements if re.search(r"UPDATE\s+type::record\('finding'", text)]
            assert updates, f"no guarded finding UPDATE was executed: {statements!r}"
            text = updates[-1]
            where = text.index("WHERE", text.index("UPDATE"))
            cursor = where + len("WHERE")
            while text[cursor] == " ":
                cursor += 1
            assert text[cursor] == "(", (
                f"the ledger's CAS predicate is not parenthesised by the shell: {text!r}"
            )
            after_cas = _balanced_group_end(text, cursor)
            tail = text[after_cas:].lstrip()
            assert tail.startswith("AND"), f"the guard is not AND-bound at the top level: {text!r}"
            assert tail[3:].lstrip().lstrip("(").startswith(guard.lstrip("(")), (
                f"the conjunct after the CAS is not the plan's own guard ({guard!r}): {text!r}"
            )


class TestAStatusVerbPreReadsItsRowOnce:
    """Kickoff §4.3 item 1 + rider (v), findings' twin: the ledger's own pre-read is DELETED — the
    governed pre-read (``authorize_guarded(projection=…)``) is the ONE read of the addressed row before the
    CAS (no second TOCTOU window between two reads). Addressed by ID (a number needs its index lookup)."""

    async def test_one_read_of_the_row_before_the_transaction(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD (the only pre-read is the ledger's ``SELECT *`` — it projects no governed column).
        Counts every single-statement read touching the addressed finding before the first transaction:
        exactly ONE, and it is the governed pre-read (projects ``owner_principal``)."""
        from loremaster.store import _txn  # noqa: PLC0415

        async with finding_world(monkeypatch, tmp_path) as world:
            row_id = await world.seed(
                row_id=new_row_id("onepre"), number=8101, owner="ag-a1", scope_key="AB", status="open"
            )
            events: list[tuple[str, str]] = []
            real_query = _txn.run_query
            real_txn = _txn.execute_transaction

            async def _q(*args: Any, **kwargs: Any) -> Any:
                events.append(("read", str(kwargs.get("statement", ""))))
                return await real_query(*args, **kwargs)

            async def _t(statement_text: str, *args: Any, **kwargs: Any) -> Any:
                events.append(("txn", statement_text))
                return await real_txn(statement_text, *args, **kwargs)

            patch_shared_object_everywhere(
                monkeypatch, "run_query", real_query, _q, expect_in=("loremaster.store._txn",)
            )
            patch_shared_object_everywhere(
                monkeypatch, "execute_transaction", real_txn, _t, expect_in=("loremaster.store._txn",)
            )
            await world.findings("ag-b1", action="acknowledge", id_or_number=row_id)
            first_txn = next((index for index, (kind, _s) in enumerate(events) if kind == "txn"), len(events))
            row_reads = [
                statement
                for kind, statement in events[:first_txn]
                if kind == "read" and "finding" in statement and "keep" not in statement
            ]
            assert len(row_reads) == 1, f"{len(row_reads)} reads of the finding before the CAS: {row_reads}"
            assert "owner_principal" in row_reads[0], (
                f"the one pre-read is not the governed pre-read: {row_reads[0]!r}"
            )
