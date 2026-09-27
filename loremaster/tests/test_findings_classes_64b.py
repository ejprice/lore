"""Contract r2 — packet 64b-i: every SURVIVOR CLASS of ``REPORT-adversary-64b.md``, pinned by a GENERATED
sweep over its domain's source of truth (packet-64 amendment 8 ``53563e7`` §6 — "one sweep each"; CLAUDE.md
"FIX THE CLASS"). Authored by ``contract-64b-r2`` (Opus 5.5 — contract tests ONLY). The adversary's own
INSTANCES are landed AST-equal in ``test_findings_adversary_pins_64b.py``; the hand cases there are extras,
these are the sweeps.

EVERY domain below is DERIVED, and every derivation carries a COMPLETENESS assertion (a domain member with no
driver/construction reds by name — INSTRUMENT-0: reach as a checked variable):

- MP-1/2/3 (reference, WB1, WB2, WB17) — ∀ capability write verb × address {id, number} × {invisible,
  nonexistent, visible-denied}: invisible ≡ nonexistent BYTES; visible-denied = ``GovernedDenied`` [domain:
  ``server._FINDING_ACTIONS``'s ``requires_capability`` True set]
- am-8 §3 (L5 order) — ∀ transition verb × {id, number} × {invisible, visible-unwritable, writable} on an
  ILLEGAL edge: not-found / ``GovernedDenied`` / ``IllegalTransitionError`` + ZERO writes [domain: the
  ``FindingLedger`` methods that call ``_transition`` (AST)]
- MP-4 (WB3) — ∀ the zero-row classifier authorizes the PASSED action — READ and the action DISAGREE in every
  fixture [domain: the ``action=`` values production passes to ``classify_zero_row_cas`` (AST) × a
  readable-but-not-actionable construction per ``pdp.Action``]
- FK-3 rider (am-7 §5) — ∀ CAS verb: a row DELETED between the gate and the CAS is the ledger's not-found,
  never a bare ``KeyError``/``TypeError``/``GovernedConflict`` [domain: the ``FindingLedger`` public methods
  whose call graph reaches ``classify_zero_row_cas`` (AST)]
- MP-5 (WB4) — ∀ authorization input × ∀ capability write verb: a degradation between two calls takes effect
  on the NEXT call [domain: the four inputs (am-8 §1: household, capability expiry, agent status, principal
  status) × the True set]
- MP-6 (WB19) — ∀ appended event: ``actor`` = the capability's agent name AND ``actor_agent`` = its RecordID;
  the served transition line names it [domain: every event observed after driving the whole True set]
- MP-7 (WB10) — ∀ capability write verb × {agent= supplied, omitted}: EXACTLY ONE statement reads ``agent``
  and EXACTLY ONE reads ``principal`` per governed call, counted at the STORE SEAM [domain: the True set ×
  {supplied, omitted}]
- FK-6 rider (am-7 §4) — ∀ row-addressing write verb × {id, number}: ONE read of the addressed ``finding``
  row before the transaction [domain: the True set's row-addressing drivers]
- MP-8 (WB21) — ∀ comparison of a dispatcher's ``agent``/``session`` against an agent row's
  ``name``/``session``: it lies in ONE function [domain: every ``Compare`` in ``server.py`` (AST)]
- MP-11 (WB22b) — ∀ migrate leg: the write set is exactly the requested table + its NAMED dependencies
  [domain: ``principals._MIGRATE_VALID_TABLES`` × every other table byte-identical]
- WB23 / MP-13 — ∀ (verb, param) where the verb does not own the param: a teaching refusal, never silent
  acceptance [domain: ``_FINDING_ACTIONS`` × the verb-owned params (``scope``: report/set_scope; ``items``:
  the batches)]

Live TEST store ``:18000`` (NEVER :18500); per-test databases, reaped.
"""

from __future__ import annotations

import ast
import contextlib
import inspect
import re
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from _governed_contract import (
    build_principal_and_keep_stores,
    member,
    patch_shared_object_everywhere,
    store_handle,
)
from _governed_contract_64 import (
    FINDING_TABLE,
    FindingWorld,
    bare,
    current_finding_ddl,
    finding_world,
    new_row_id,
    seed_finding_governed,
)
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database
from loremaster.findings import FindingLedger, FindingNotFoundError, IllegalTransitionError
from surrealdb import RecordID

import lorerunes as pdp
from loremaster import governed, principals, server

if TYPE_CHECKING:
    from loremaster.keeps import KeepStore
    from loremaster.visible_keeps import resolve_visible_keeps

    # 64b-i's RULED, not-yet-built keep-seam signature (packet-64 amendment 9 §1 — FK-r2-1's rider) — a TYPED
    # CALL (amendment 8 §5, MP-9). Until the build lands it, a mypy error OWNED by bound
    # `packet-64b-i-contract` (#461). Runtime-inert.
    async def _ruled_64b_i_keep_seam_identity(keep_store: KeepStore) -> None:
        """amendment 9 §1 — exactly one of ``member_email=`` / ``principal_id=``, keyword-only."""
        by_id: list[str] = await keep_store.list_keeps_for_member(principal_id="p")
        visible: frozenset[str] = await resolve_visible_keeps(keep_store, principal_id="p")
        assert by_id is not None and visible is not None


_SERVER_PY = Path(server.__file__)
_FINDINGS_PY = Path(inspect.getfile(FindingLedger))
_MISSING_ID = "no_such_finding_id"
_MISSING_NUMBER = 8999


# =========================================================================== #
# The derived domains.
# =========================================================================== #


def capability_write_verbs() -> set[str]:
    """THE True set — every ``lore_findings`` verb whose spec says ``requires_capability`` (F7), DERIVED from
    the spec dict itself (never a hand-list). Empty at HEAD (a tuple, no specs) ⇒ every sweep's non-vacuity
    leg reds first, for the right reason."""
    table: Any = vars(server)["_FINDING_ACTIONS"]
    if not isinstance(table, dict):
        return set()
    return {verb for verb, spec in table.items() if getattr(spec, "requires_capability", None) is True}


def _ledger_methods() -> dict[str, ast.AsyncFunctionDef | ast.FunctionDef]:
    tree = ast.parse(_FINDINGS_PY.read_text(encoding="utf-8"))
    ledger = next(
        node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "FindingLedger"
    )
    return {
        node.name: node for node in ledger.body if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            target = child.func
            if isinstance(target, ast.Attribute):
                names.add(target.attr)
            elif isinstance(target, ast.Name):
                names.add(target.id)
    return names


def transition_verbs() -> set[str]:
    """The ``FindingLedger`` methods that call ``_transition`` — the edge-validating verbs (AST, derived)."""
    return {
        name
        for name, node in _ledger_methods().items()
        if not name.startswith("_") and "_transition" in _called_names(node)
    }


def cas_verbs() -> set[str]:
    """The PUBLIC ``FindingLedger`` methods whose same-class call graph reaches ``classify_zero_row_cas`` —
    every verb whose zero-row rollback the ONE classifier decides (FK-3's domain, derived by a transitive
    walk; a new CAS verb joins it with no test edit)."""
    methods = _ledger_methods()
    graph = {name: _called_names(node) for name, node in methods.items()}

    def _reaches(name: str, seen: frozenset[str] = frozenset()) -> bool:
        if name in seen:
            return False
        calls = graph.get(name, set())
        if "classify_zero_row_cas" in calls:
            return True
        return any(_reaches(callee, seen | {name}) for callee in calls if callee in methods)

    return {name for name in methods if not name.startswith("_") and _reaches(name)}


def classifier_actions() -> set[str]:
    """The ``pdp.Action`` member names production passes as ``action=`` to ``classify_zero_row_cas`` — every
    action the classifier SERVES (AST over the whole production tree through THE shared parse)."""
    from _logging_fixtures import parse_production_trees  # noqa: PLC0415 - house lazy-import idiom

    served: set[str] = set()
    for tree in parse_production_trees(include_scripts=False).values():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = node.func
            name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", None)
            if name != "classify_zero_row_cas":
                continue
            for keyword in node.keywords:
                if keyword.arg == "action" and isinstance(keyword.value, ast.Attribute):
                    served.add(keyword.value.attr)
    return served


# =========================================================================== #
# The per-verb drivers — ONE table, keyed by verb, completeness-checked against the derived True set.
# =========================================================================== #


@dataclass(frozen=True)
class VerbDriver:
    """How to call ONE capability write verb against ONE address. ``addresses_a_row`` is False only for a
    verb whose address is a READ inside a CREATE (``report``'s ``supersedes``) — a VISIBLE row is
    legitimately superseded, so the visible-denied state does not apply to it. ``batch`` verbs render
    per-item outcomes instead of raising."""

    kwargs: Callable[[FindingWorld, int | str], dict[str, Any]]
    addresses_a_row: bool = True
    batch: bool = False


def _report_kwargs(_world: FindingWorld, address: int | str) -> dict[str, Any]:
    return {
        "action": "report",
        "subject": "sweep",
        "body": "",
        "area": "a",
        "category": "c",
        "supersedes": address,
    }


def _edge(verb: str) -> Callable[[FindingWorld, int | str], dict[str, Any]]:
    return lambda _world, address: {"action": verb, "id_or_number": address}


VERB_DRIVERS: dict[str, VerbDriver] = {
    "report": VerbDriver(_report_kwargs, addresses_a_row=False),
    "acknowledge": VerbDriver(_edge("acknowledge")),
    "resolve": VerbDriver(_edge("resolve")),
    "wontfix": VerbDriver(_edge("wontfix")),
    "annotate": VerbDriver(lambda _w, address: {"action": "annotate", "id_or_number": address, "note": "n"}),
    "set_scope": VerbDriver(
        lambda world, address: {"action": "set_scope", "id_or_number": address, "scope": "server"}
    ),
    "resolve_many": VerbDriver(
        lambda _w, address: {"action": "resolve_many", "items": [{"id_or_number": address}]}, batch=True
    ),
    "acknowledge_many": VerbDriver(
        lambda _w, address: {"action": "acknowledge_many", "items": [{"id_or_number": address}]}, batch=True
    ),
}


def _required_drivers() -> dict[str, VerbDriver]:
    """The drivers for the DERIVED True set — non-vacuous and complete, or RED by name."""
    required = capability_write_verbs()
    assert required, (
        "no lore_findings verb requires a capability — every ∀-verb sweep here would be vacuous "
        "(kickoff §8 / "
        "F7 unbuilt: _FINDING_ACTIONS is not a spec dict)"
    )
    uncovered = required - VERB_DRIVERS.keys()
    assert not uncovered, f"capability write verbs with NO sweep driver (add one): {sorted(uncovered)}"
    return {verb: VERB_DRIVERS[verb] for verb in sorted(required)}


def _normalise(text: str, *addresses: int | str) -> str:
    for address in addresses:
        text = re.sub(rf"(?<![\w]){re.escape(str(address))}(?![\w])", "<ADDR>", text)
    return text


async def _outcome(
    world: FindingWorld, actor: str, kwargs: dict[str, Any]
) -> tuple[str, BaseException | None]:
    """Run one call; return (served text, raised error or None) — the batch verbs SERVE their failures."""
    try:
        return await world.findings(actor, **kwargs), None
    except (governed.GovernedDenied, FindingNotFoundError, IllegalTransitionError, ValueError) as error:
        return str(error), error


async def _finding_count(world: FindingWorld) -> int:
    return len(await run(world.admin_conn, f"SELECT VALUE id FROM {FINDING_TABLE}"))


# =========================================================================== #
# MP-1/2/3 — invisible ≡ nonexistent, visible-denied is a GovernedDenied: ∀ verb × address × state.
# =========================================================================== #


class TestEveryWriteVerbTreatsAnInvisibleRowAsNonexistent:
    """amendment 7 §4 (FK-6) as swept by amendment 8 §6 row 1: ∀ capability write verb (DERIVED) × address
    {id, number} × {invisible, nonexistent, visible-denied}. Invisible and nonexistent serve BYTE-IDENTICAL
    text (after address normalisation) — no existence oracle; a VISIBLE-but-unwritable row serves the deny
    (never a not-found a ``get`` of the same address would contradict). Every leg: the row unchanged, ZERO
    new findings, ZERO audit rows. Worlds: bob (ag-b1) on alice's ``keep:A`` row (invisible); alice's sibling
    ag-a2 on ag-a1's ``principal-private`` row (visible, not writable)."""

    @pytest.mark.parametrize("verb", sorted(VERB_DRIVERS))
    async def test_every_address_form_and_state(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, verb: str
    ) -> None:
        """⚠ RED at HEAD (no capability=; the True set is empty — the non-vacuity leg reds first)."""
        drivers = _required_drivers()
        if verb not in drivers:
            pytest.fail(
                f"{verb!r} has a sweep driver but is not a capability write verb — a stale driver row"
            )
        driver = drivers[verb]
        async with finding_world(monkeypatch, tmp_path) as world:
            hidden = await world.seed(row_id=new_row_id("inv"), number=8101, owner="ag-a1", scope_key="A")
            sibling_owned = await world.seed(
                row_id=new_row_id("vis"), number=8102, owner="ag-a1", scope_key="principal-private"
            )
            snapshot = {row_id: await world.row(row_id) for row_id in (hidden, sibling_owned)}
            audit_before = await world.audit_count()
            count_before = await _finding_count(world)
            for invisible_address, missing_address in ((hidden, _MISSING_ID), (8101, _MISSING_NUMBER)):
                invisible_text, invisible_error = await _outcome(
                    world, "ag-b1", driver.kwargs(world, invisible_address)
                )
                missing_text, missing_error = await _outcome(
                    world, "ag-b1", driver.kwargs(world, missing_address)
                )
                label = f"{verb} by {type(invisible_address).__name__}"
                if not driver.batch:
                    assert isinstance(missing_error, FindingNotFoundError), (label, missing_text)
                    assert isinstance(invisible_error, FindingNotFoundError), (
                        f"{label}: an INVISIBLE row must be the SAME not-found as a nonexistent one, got "
                        f"{type(invisible_error).__name__}: {invisible_text!r}"
                    )
                assert _normalise(invisible_text, invisible_address) == _normalise(
                    missing_text, missing_address
                ), (
                    f"{label}: invisible vs nonexistent differ (an existence oracle): {invisible_text!r} vs "
                    f"{missing_text!r}"
                )
                if driver.addresses_a_row:
                    visible_address = sibling_owned if isinstance(invisible_address, str) else 8102
                    visible_text, visible_error = await _outcome(
                        world, "ag-a2", driver.kwargs(world, visible_address)
                    )
                    if driver.batch:
                        assert _normalise(visible_text, visible_address) != _normalise(
                            missing_text, missing_address
                        ), f"{label}: a VISIBLE-but-unwritable item rendered as not-found: {visible_text!r}"
                    else:
                        assert isinstance(visible_error, governed.GovernedDenied) and not isinstance(
                            visible_error, FindingNotFoundError
                        ), (
                            f"{label}: a VISIBLE-but-unwritable row must be GovernedDenied, got "
                            f"{type(visible_error).__name__}: {visible_text!r}"
                        )
            for row_id, before in snapshot.items():
                assert await world.row(row_id) == before, f"{verb}: a refused call mutated {row_id}"
            assert await _finding_count(world) == count_before, f"{verb}: a refused call minted a finding"
            assert await world.audit_count() == audit_before, f"{verb}: a refused call left an audit row"


# =========================================================================== #
# am-8 §3 — authorize FIRST, then the edge.
# =========================================================================== #


class TestTheEdgeIsCheckedOnlyAfterAuthorization:
    """amendment 8 §3: the pre-read → the gate (with am-7's invisibility derivation) → edge validation → the
    CAS. ∀ transition verb (DERIVED: the ``FindingLedger`` methods that call ``_transition``) × {id, number},
    each on an ILLEGAL edge (the row is ``wontfix`` — terminal): an INVISIBLE row serves not-found bytes and
    NEVER a status; a VISIBLE-unwritable row serves ``GovernedDenied`` and never ``IllegalTransitionError``;
    a WRITABLE row serves ``IllegalTransitionError`` naming both states with ZERO writes. CONTROL: a writable
    row on a LEGAL edge lands. DUAL row R-L5 (§DUAL): the ORDER is CHANGED-DELIBERATELY (HEAD validated
    first); "validate BEFORE any write" is PRESERVED (the gate writes nothing)."""

    async def test_every_state_on_an_illegal_edge(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD (no capability=; the edge is validated first and serves the status)."""
        verbs = transition_verbs()
        assert verbs >= {"acknowledge"}, f"the transition-verb derivation found {sorted(verbs)} — vacuous"
        async with finding_world(monkeypatch, tmp_path) as world:
            number = 8200
            for verb in sorted(verbs):
                for form in ("id", "number"):
                    number += 10
                    rows = {
                        "invisible": await world.seed(
                            row_id=new_row_id("edge"),
                            number=number + 1,
                            owner="ag-a1",
                            scope_key="A",
                            status="wontfix",
                        ),
                        "visible": await world.seed(
                            row_id=new_row_id("edge"),
                            number=number + 2,
                            owner="ag-a1",
                            scope_key="principal-private",
                            status="wontfix",
                        ),
                        "writable": await world.seed(
                            row_id=new_row_id("edge"),
                            number=number + 3,
                            owner="ag-a1",
                            scope_key="AB",
                            status="wontfix",
                        ),
                    }
                    offsets = {"invisible": 1, "visible": 2, "writable": 3}
                    address: dict[str, int | str] = {
                        key: (row_id if form == "id" else number + offsets[key])
                        for key, row_id in rows.items()
                    }
                    before = {key: await world.row(row_id) for key, row_id in rows.items()}
                    missing_address = _MISSING_ID if form == "id" else _MISSING_NUMBER
                    label = f"{verb} by {form}"
                    with pytest.raises(FindingNotFoundError) as missing:
                        await world.findings("ag-b1", action=verb, id_or_number=missing_address)
                    with pytest.raises(FindingNotFoundError) as invisible:
                        await world.findings("ag-b1", action=verb, id_or_number=address["invisible"])
                    assert _normalise(str(invisible.value), address["invisible"]) == _normalise(
                        str(missing.value), missing_address
                    ), f"{label}: an invisible row on an illegal edge leaked: {invisible.value}"
                    assert "wontfix" not in str(invisible.value), (
                        f"{label}: a STATUS oracle: {invisible.value}"
                    )
                    with pytest.raises(governed.GovernedDenied) as denied:
                        await world.findings("ag-a2", action=verb, id_or_number=address["visible"])
                    assert not isinstance(denied.value, IllegalTransitionError | FindingNotFoundError), label
                    with pytest.raises(IllegalTransitionError) as illegal:
                        await world.findings("ag-b1", action=verb, id_or_number=address["writable"])
                    assert "wontfix" in str(illegal.value), f"{label}: the edge error must name the state"
                    for key, row_id in rows.items():
                        assert await world.row(row_id) == before[key], f"{label}: the {key} row was written"
            # CONTROL — a legal edge on a writable row lands (the denials above are the state, not the verb).
            legal = await world.seed(row_id=new_row_id("edge"), number=8199, owner="ag-a1", scope_key="AB")
            await world.findings("ag-b1", action="acknowledge", id_or_number=8199)
            assert (await world.row(legal))["status"] == "acknowledged"


# =========================================================================== #
# MP-4 — the classifier authorizes the PASSED action (READ and the action DISAGREE in every fixture).
# =========================================================================== #

_KEEP_AB = pdp.keep_scope("keepalphabravo")

#: action name → (the fresh row's governed columns, a subject that can READ it but NOT perform the action,
#: a subject that CAN perform it — the correct-build control). Every served action must have a row here.
_READABLE_BUT_NOT_ACTIONABLE: dict[str, tuple[dict[str, Any], Any, Any]] = {
    "WRITE": (
        {"owner_principal": "alice", "owner_agent": "ag_a1", "scope": pdp.SCOPE_PRINCIPAL_PRIVATE},
        member("alice", "ag_a2", frozenset()),  # the SIBLING: reads principal-private, may not write it
        member("alice", "ag_a1", frozenset()),  # the exact pair
    ),
    "DELETE": (
        {"owner_principal": "alice", "owner_agent": "ag_a1", "scope": _KEEP_AB},
        member("bob", "ag_b1", frozenset({_KEEP_AB})),  # a household member: reads + writes, may not delete
        member("alice", "ag_a1", frozenset({_KEEP_AB})),  # the exact pair
    ),
}


class TestTheZeroRowClassifierAuthorizesThePassedAction:
    """MP-4's CLASS (amendment 8 §6 row 2): ∀ action the classifier SERVES (DERIVED from production's
    ``classify_zero_row_cas(action=…)`` call sites), a fresh row the subject can still READ but may no longer
    perform THAT action on ⇒ ``GovernedConflict`` (the ledger verdict is never consulted); CONTROL: a subject
    that may perform it gets the ledger verdict on the FRESH row. A classifier that asks ``READ`` (WB3)
    passes every fixture where READ and the action agree — so no fixture here lets them agree."""

    async def test_every_served_action_discriminates_read_from_the_action(self) -> None:
        """⚠ RED at HEAD (``classify_zero_row_cas`` absent — no served action is derived)."""
        served = classifier_actions()
        assert served, (
            "no production call passes action= to classify_zero_row_cas — the sweep would be vacuous"
        )
        unconstructed = served - _READABLE_BUT_NOT_ACTIONABLE.keys()
        assert not unconstructed, (
            f"served classifier actions with no READ≠action construction: {sorted(unconstructed)}"
        )
        classify = vars(governed).get("classify_zero_row_cas")
        assert classify is not None, "UNBUILT (#407): governed.classify_zero_row_cas does not exist"
        env = make_env(database=unique_database(), dim=8)
        connection = await connect_admin(env)
        try:
            from _governed_contract import apply_ddl, governed_overlay_ddl  # noqa: PLC0415

            await apply_ddl(connection, current_finding_ddl(), url=env.url)
            await apply_ddl(connection, governed_overlay_ddl(FINDING_TABLE), url=env.url)
            for index, action_name in enumerate(sorted(served)):
                columns, reader_only, actor = _READABLE_BUT_NOT_ACTIONABLE[action_name]
                action = pdp.Action[action_name]
                row_id = f"mp4_{action_name.lower()}"
                await seed_finding_governed(connection, row_id=row_id, number=8300 + index, **columns)
                resource = governed.resource_from_row(
                    {"id": RecordID(FINDING_TABLE, row_id), **_links(columns)}
                )
                assert pdp.authorize(reader_only, pdp.Action.READ, resource).allowed, (
                    f"fixture: the {action_name} reader cannot READ the row — READ and the action would agree"
                )
                assert not pdp.authorize(reader_only, action, resource).allowed, f"fixture: {action_name}"
                handle, _calls = store_handle(connection, url=env.url)
                seen: list[Any] = []
                with pytest.raises(governed.GovernedConflict):
                    await classify(
                        handle,
                        table=FINDING_TABLE,
                        row_id=row_id,
                        subject=reader_only,
                        action=action,
                        ledger_verdict=lambda row, seen=seen: seen.append(row),
                    )
                assert seen == [], f"{action_name}: a DENY was mis-served as the ledger's verdict"
                outcome = await classify(
                    handle,
                    table=FINDING_TABLE,
                    row_id=row_id,
                    subject=actor,
                    action=action,
                    ledger_verdict=lambda row: ("verdict", (row or {}).get("status")),
                )
                assert outcome == ("verdict", "open"), f"{action_name} CONTROL: {outcome!r}"
        finally:
            await connection.close()
            await drop_database(env)


def _links(columns: dict[str, Any]) -> dict[str, Any]:
    return {
        "owner_principal": RecordID("principal", columns["owner_principal"]),
        "owner_agent": RecordID("agent", columns["owner_agent"]),
        "scope": columns["scope"],
    }


# =========================================================================== #
# FK-3 rider — a row that vanished between the gate and the CAS, ∀ CAS verb.
# =========================================================================== #


def _delete_after_gate(monkeypatch: pytest.MonkeyPatch, world: FindingWorld, row_id: str) -> dict[str, int]:
    """Wrap THE ``governed.authorize_guarded`` (every binding, by identity) so the addressed row is DELETED
    after the gate returned its plan and before the ledger's CAS — the vanished-row window (am-7 FK-3 rider:
    reachable only via 64d's delete, constructed now). Returns a counter proving the injection LANDED (#194).
    """
    real = governed.authorize_guarded
    landed = {"count": 0}

    async def _gate_then_delete(*args: Any, **kwargs: Any) -> Any:
        plan = await real(*args, **kwargs)
        await run(world.admin_conn, f"DELETE type::record('{FINDING_TABLE}', $id)", {"id": row_id})
        landed["count"] += 1
        return plan

    patch_shared_object_everywhere(
        monkeypatch, "authorize_guarded", real, _gate_then_delete, expect_in=("loremaster.governed",)
    )
    return landed


class TestAVanishedRowIsTheLedgersNotFoundForEveryCasVerb:
    """amendment 7 §5 FK-3 rider: ``row is None`` after a zero-row CAS is passed THROUGH to the ledger's
    verdict, and the verdict serves the ledger's not-found — ∀ CAS verb (DERIVED: the public
    ``FindingLedger`` methods whose call graph reaches ``classify_zero_row_cas``). Never a bare
    ``KeyError``/``TypeError`` (a verdict that indexes ``None``), never a ``GovernedConflict`` (nothing to
    authorize on a vanished row)."""

    async def test_every_cas_verb(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """⚠ RED at HEAD (no classifier — the CAS verbs derive to the empty set)."""
        verbs = cas_verbs()
        assert verbs, "no FindingLedger verb reaches classify_zero_row_cas — the FK-3 sweep would be vacuous"
        async with finding_world(monkeypatch, tmp_path) as world:
            for index, verb in enumerate(sorted(verbs)):
                driver = VERB_DRIVERS.get(verb)
                assert driver is not None and driver.addresses_a_row and not driver.batch, (
                    f"CAS verb {verb!r} has no single-item sweep driver (add one)"
                )
                number = 8400 + index
                row_id = await world.seed(
                    row_id=new_row_id("gone"), number=number, owner="ag-a1", scope_key="AB"
                )
                with monkeypatch.context() as scoped:
                    landed = _delete_after_gate(scoped, world, row_id)
                    try:
                        await world.findings("ag-b1", **driver.kwargs(world, number))
                    except FindingNotFoundError:
                        pass
                    except Exception as error:  # noqa: BLE001 - the pin names the wrong class
                        pytest.fail(
                            f"{verb}: a row vanished between the gate and the CAS served "
                            f"{type(error).__name__}: {error} — the ledger's not-found is the only answer"
                        )
                    else:
                        pytest.fail(f"{verb}: a vanished row was served as SUCCESS")
                    assert landed["count"] >= 1, f"{verb}: the delete injection never landed (#194)"


# =========================================================================== #
# MP-5 — every authorization input is read PER CALL (the lifecycle law).
# =========================================================================== #


async def _degrade_household(world: FindingWorld) -> None:
    await world.ctx._keep_store.remove_household_member(  # noqa: SLF001
        keep_id=world.scopes["AB"].partition(":")[2], member_email=world.emails["bob"]
    )


async def _degrade_capability_expiry(world: FindingWorld) -> None:
    await run(
        world.admin_conn,
        "UPDATE type::record('agent', $id) SET capability_expires_at = $past",
        {"id": world.agent_ids["ag-b1"], "past": datetime.now(UTC) - timedelta(hours=1)},
    )


async def _degrade_agent_retired(world: FindingWorld) -> None:
    await run(
        world.admin_conn,
        "UPDATE type::record('agent', $id) SET status = 'retired'",
        {"id": world.agent_ids["ag-b1"]},
    )


async def _degrade_principal_suspended(world: FindingWorld) -> None:
    await world.ctx._principal_store.set_status(email=world.emails["bob"], status="suspended")  # noqa: SLF001


#: amendment 8 §1 — the FOUR authorization inputs a governed call reads, each degraded between two calls.
#: ``household`` degrades the KEEP (every row verb addresses a keep:AB row; ``report`` requests scope AB);
#: the other three degrade the IDENTITY (every verb must refuse).
_DEGRADATIONS: dict[str, Callable[[FindingWorld], Awaitable[None]]] = {
    "household-removed": _degrade_household,
    "capability-expired": _degrade_capability_expiry,
    "agent-retired": _degrade_agent_retired,
    "principal-suspended": _degrade_principal_suspended,
}


class TestEveryAuthorizationInputIsReadPerCall:
    """MP-5's CLASS (amendment 8 §1's DUAL + §6 row 3): ∀ input ∈ {household, capability expiry, agent
    status, principal status} × ∀ capability write verb (DERIVED): the call BEFORE the degradation is allowed
    (the control), the degradation lands, and EVERY verb's call after it is REFUSED with the row unchanged. A
    Subject (or any authorization input) memoised across calls (WB4) passes every other pin in the contract.
    """

    @pytest.mark.parametrize("degradation", sorted(_DEGRADATIONS))
    async def test_the_next_call_sees_the_degradation(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, degradation: str
    ) -> None:
        """⚠ RED at HEAD (no capability=). Per verb: a call BEFORE the degradation on one row is ALLOWED (the
        per-verb control — a verb that is refused anyway proves nothing), then the SAME verb after it on a
        twin row is REFUSED. bob (ag-b1) acts on keep:AB rows alice filed; ``set_scope`` acts on bob's OWN
        principal-private rows (only the owner may re-scope) toward ``keep:AB``; ``report`` requests
        ``scope=keep:AB`` (grantable only while householded)."""
        drivers = _required_drivers()
        async with finding_world(monkeypatch, tmp_path) as world:
            pairs: dict[str, tuple[int, int]] = {}
            number = 8500
            for verb in sorted(drivers):
                owner, scope_key = ("ag-b1", "principal-private") if verb == "set_scope" else ("ag-a1", "AB")
                for _twin in (0, 1):
                    number += 1
                    await world.seed(
                        row_id=new_row_id("life"), number=number, owner=owner, scope_key=scope_key
                    )
                pairs[verb] = (number - 1, number)

            def _kwargs(verb: str, address: int) -> dict[str, Any]:
                kwargs = drivers[verb].kwargs(world, address)
                if verb == "report":
                    return {k: v for k, v in kwargs.items() if k != "supersedes"} | {
                        "scope": world.scopes["AB"]
                    }
                if verb == "set_scope":
                    kwargs["scope"] = world.scopes["AB"]
                return kwargs

            for verb, (before_address, _after_address) in sorted(pairs.items()):
                text, error = await _outcome(world, "ag-b1", _kwargs(verb, before_address))
                assert error is None and " 0 of " not in text, (
                    f"CONTROL ({degradation}): {verb} was refused BEFORE the degradation: {text!r}"
                )
            snapshot = {
                verb: await world.row(await _row_id_of(world, after_address))
                for verb, (_before, after_address) in pairs.items()
            }
            count_before = await _finding_count(world)
            await _DEGRADATIONS[degradation](world)
            for verb, (_before_address, after_address) in sorted(pairs.items()):
                text, error = await _outcome(world, "ag-b1", _kwargs(verb, after_address))
                refused = error is not None or (drivers[verb].batch and " 0 of " in text)
                assert refused, (
                    f"{degradation} → {verb}: the call AFTER the degradation was ALLOWED (a stale "
                    "authorization "
                    f"input authorized it): {text!r}"
                )
            for verb, (_before_address, after_address) in pairs.items():
                row = await world.row(await _row_id_of(world, after_address))
                assert row == snapshot[verb], f"{degradation} → {verb}: the refused call moved the row"
            assert await _finding_count(world) == count_before, (
                f"{degradation}: a refused report minted a row"
            )


async def _row_id_of(world: FindingWorld, number: int) -> str:
    ids = await run(
        world.admin_conn, f"SELECT VALUE id FROM {FINDING_TABLE} WHERE number = $n", {"n": number}
    )
    assert ids, f"fixture: no finding #{number}"
    return bare(ids[0])


# =========================================================================== #
# MP-6 — ∀ appended event: the derived actor name AND its agent link.
# =========================================================================== #


class TestEveryAppendedEventCarriesTheDerivedActor:
    """MP-6's CLASS (amendment 8 §6 row 5; amendment 2 §3): drive the WHOLE DERIVED True set as ag-b2 on
    keep:AB rows alice filed; EVERY event appended by any of them names ``actor == "ag-b2"`` AND
    ``actor_agent ==`` ag-b2's RecordID — quantified over the events OBSERVED, never a hand-list of
    producers. Non-vacuity: at least one event is observed. The served single-item transition line names the
    derived actor."""

    async def test_every_observed_event(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """⚠ RED at HEAD (no capability=)."""
        drivers = _required_drivers()
        async with finding_world(monkeypatch, tmp_path) as world:
            rows: dict[str, str] = {}
            for index, verb in enumerate(sorted(drivers)):
                rows[verb] = await world.seed(
                    row_id=new_row_id("ev"), number=8601 + index, owner="ag-a1", scope_key="AB"
                )
            before = {
                verb: len(((await world.row(row_id))["provenance"] or {}).get("events") or [])
                for verb, row_id in rows.items()
            }
            observed = 0
            for index, (verb, driver) in enumerate(sorted(drivers.items())):
                kwargs = driver.kwargs(world, 8601 + index)
                if verb == "report":
                    kwargs = {k: v for k, v in kwargs.items() if k != "supersedes"}
                if verb == "set_scope":
                    kwargs["scope"] = world.scopes["AB"]
                rendered = await world.findings("ag-b2" if verb != "set_scope" else "ag-a1", **kwargs)
                if "transitioned to" in rendered:
                    assert "ag-b2" in rendered, (
                        f"{verb}: the served line does not name the derived actor: {rendered!r}"
                    )
                events = ((await world.row(rows[verb]))["provenance"] or {}).get("events") or []
                for event in events[before[verb] :]:
                    observed += 1
                    actor = "ag-b2" if verb != "set_scope" else "ag-a1"
                    assert event.get("actor") == actor, (verb, event)
                    assert str(event.get("actor_agent")) == str(RecordID("agent", world.agent_ids[actor])), (
                        verb,
                        event,
                    )
            assert observed, "no event was appended by any capability write verb — the sweep observed nothing"


# =========================================================================== #
# MP-7 — ONE agent read and ONE principal read per governed call, at the STORE SEAM.
# =========================================================================== #

_FROM_TABLE = re.compile(r"\bFROM\s+(?:type::record\(\s*['\"](\w+)['\"]|(\w+))", re.IGNORECASE)


def _read_tables(statement: str) -> list[str]:
    """Every table a statement READS through a ``FROM`` clause (plain table or ``type::record``)."""
    return [first or second for first, second in _FROM_TABLE.findall(statement)]


def _record_store_statements(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Spy THE three store seams (every module-level binding, by identity) and record each statement text."""
    from loremaster.store import _txn  # noqa: PLC0415

    seen: list[str] = []
    for name in ("run_query", "execute_read_transaction", "execute_transaction"):
        real = getattr(_txn, name)

        def _wrap(real: Any = real) -> Any:
            async def _spy(*args: Any, **kwargs: Any) -> Any:
                seen.append(str(kwargs.get("statement", args[0] if args else "")))
                return await real(*args, **kwargs)

            return _spy

        patch_shared_object_everywhere(monkeypatch, name, real, _wrap(), expect_in=("loremaster.store._txn",))
    return seen


#: amendment 8 §1's budget, keyed by the TABLE a statement reads (amendment 9 FK-r2-1 — CONFIRMED as the
#: class ruling; ERRATUM on am-8's "keep ≤ 1 (resolve_visible_keeps)": the read is ``member_of``), per
#: governed call: ONE capability-verify read of ``agent`` (the registry — R8), ONE of ``principal``
#: (``resolve_principal``) and ONE of ``member_of`` (the visible-keeps household read). A verb's OWN keep
#: reads (the report's project-keep default, an admin's keep-existence read) read ``keep`` and are not
#: identity reads. The shipped 63a/61b path read ``principal`` TWICE (``resolve_principal`` + the
#: visible-keeps email re-resolution) — hence the exactly-one keep seam pinned by
#: ``TestTheKeepSeamTakesExactlyOneIdentity``.
IDENTITY_READ_BUDGET: dict[str, int] = {"agent": 1, "principal": 1, "member_of": 1}


class TestTheRegistryIsReadOncePerGovernedCall:
    """MP-7's CLASS (amendment 8 §1 ruling (1) + its budget table): R8's budget is ONE statement against
    ``agent`` per governed call — the capability-verify SELECT IS that read (it projects the identity
    columns; the Subject, the identity compare and the footer all consume its result) — ONE against
    ``principal`` (``resolve_principal``) and ONE against ``member_of`` (``IDENTITY_READ_BUDGET``). Counted
    at the STORE SEAM over the WHOLE call (identity step + verb + footer), ∀ capability write verb (DERIVED)
    × {``agent=`` supplied, omitted}. With MP-5's per-call sweep this fixes each count at EXACTLY one. The
    ``keep`` row of the am-8 budget table is REPORT §FORKS FK-r2-1 (a verb's own keep reads — the report's
    project-keep default, admin's keep-existence read — are not identity reads)."""

    async def test_exactly_one_agent_and_one_principal_statement(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD (no capability=)."""
        drivers = _required_drivers()
        async with finding_world(monkeypatch, tmp_path) as world:
            violations: list[str] = []
            number = 8700
            seen = _record_store_statements(monkeypatch)
            for verb, driver in sorted(drivers.items()):
                for supplied in (False, True):
                    number += 1
                    await world.seed(row_id=new_row_id("r8"), number=number, owner="ag-a1", scope_key="AB")
                    kwargs = driver.kwargs(world, number)
                    if verb == "report":
                        kwargs = {k: v for k, v in kwargs.items() if k != "supersedes"}
                    actor = "ag-a1" if verb == "set_scope" else "ag-b1"
                    if verb == "set_scope":
                        kwargs["scope"] = world.scopes["A"]
                    if supplied:
                        kwargs["agent"] = actor
                    seen.clear()
                    await world.findings(actor, **kwargs)
                    counts = {
                        table: sum(1 for statement in seen if table in _read_tables(statement))
                        for table in IDENTITY_READ_BUDGET
                    }
                    if counts != IDENTITY_READ_BUDGET:
                        agent_reads = [s for s in seen if "agent" in _read_tables(s)]
                        violations.append(
                            f"{verb} (agent= {'supplied' if supplied else 'omitted'}): {counts} {agent_reads}"
                        )
            assert not violations, "R8 budget breached (amendment 8 §1):\n" + "\n".join(violations)


# =========================================================================== #
# FK-6 rider — ONE read of the addressed row before the transaction, ∀ row verb × address form.
# =========================================================================== #


#: the two seams amendment 9 §1's rider governs (``module``, ``callable``) — the visible-keeps resolver and
#: the household read it routes to; both take EXACTLY ONE of ``member_email=`` / ``principal_id=``.
_KEEP_IDENTITY_SEAMS = ("visible_keeps.resolve_visible_keeps", "keeps.KeepStore.list_keeps_for_member")
_KEEP_SEAM_EMAIL = "member-seam@example.com"


async def _call_keep_seam(seam: str, keep_store: Any, **identity: Any) -> Any:
    if seam == "visible_keeps.resolve_visible_keeps":
        from loremaster.visible_keeps import resolve_visible_keeps  # noqa: PLC0415

        return await resolve_visible_keeps(keep_store, **identity)
    return await keep_store.list_keeps_for_member(**identity)


@contextlib.asynccontextmanager
async def _keep_seam_world() -> AsyncIterator[tuple[Any, str]]:
    """A real ``KeepStore`` on :18000 with ONE principal householded into ONE keep (the keeper auto-household
    of ``get_or_create_keyed``); yields ``(keep_store, the principal's bare id)``. Reaped."""
    env = make_env(database=unique_database(), dim=8)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    try:
        principal = await principal_store.create(email=_KEEP_SEAM_EMAIL, role="member")
        await keep_store.get_or_create_keyed(
            key="seam-keep", type="project", keeper_email=_KEEP_SEAM_EMAIL, name="seam"
        )
        yield keep_store, bare(principal.id)
    finally:
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


class TestTheKeepSeamTakesExactlyOneIdentity:
    """amendment 9 §1 — FK-r2-1's rider: ``resolve_visible_keeps`` / ``list_keeps_for_member`` take EXACTLY
    ONE of ``member_email=`` / ``principal_id=`` (the governed path passes the PROVEN principal id — one
    ``principal`` read per call), REFUSED otherwise BEFORE ANY READ (``ValueError`` — the substrate's refusal
    class for a malformed request, FK-4's precedent). GENERATED ∀ seam × {both, neither}; CONTROL ∀ seam:
    each single identity returns the SAME keep set, and the id path reads NO ``principal`` row. The rider's
    lifecycle half (an id passed without the upstream proof) is MP-5's ``principal-suspended`` degradation."""

    @pytest.mark.parametrize("seam", _KEEP_IDENTITY_SEAMS)
    @pytest.mark.parametrize("identities", ["both", "neither"])
    async def test_both_or_neither_is_refused_before_any_read(
        self, monkeypatch: pytest.MonkeyPatch, seam: str, identities: str
    ) -> None:
        """⚠ RED at HEAD (the seams take ``member_email`` alone — a ``TypeError``, not the ruled refusal)."""
        async with _keep_seam_world() as (keep_store, principal_bare):
            identity = (
                {"member_email": _KEEP_SEAM_EMAIL, "principal_id": principal_bare}
                if identities == "both"
                else {}
            )
            with monkeypatch.context() as scoped:
                seen = _record_store_statements(scoped)
                with pytest.raises(ValueError):
                    await _call_keep_seam(seam, keep_store, **identity)
            assert seen == [], f"{seam} read the store before refusing {identities}: {seen!r}"

    @pytest.mark.parametrize("seam", _KEEP_IDENTITY_SEAMS)
    async def test_CONTROL_each_single_identity_resolves_the_same_keeps(
        self, monkeypatch: pytest.MonkeyPatch, seam: str
    ) -> None:
        """⚠ RED at HEAD for the id leg only (``principal_id=`` is unbuilt); the email leg is HEAD's path."""
        async with _keep_seam_world() as (keep_store, principal_bare):
            with monkeypatch.context() as scoped:
                email_seen = _record_store_statements(scoped)
                by_email = await _call_keep_seam(seam, keep_store, member_email=_KEEP_SEAM_EMAIL)
            with monkeypatch.context() as scoped:
                id_seen = _record_store_statements(scoped)
                by_id = await _call_keep_seam(seam, keep_store, principal_id=principal_bare)
            assert by_email, f"CONTROL: the seeded keep is not visible by email: {by_email!r}"
            assert sorted(by_id) == sorted(by_email), (by_id, by_email)
            email_principal_reads = sum(
                _read_tables(statement).count("principal") for statement in email_seen
            )
            id_principal_reads = sum(_read_tables(statement).count("principal") for statement in id_seen)
            assert email_principal_reads >= 1, (
                f"CONTROL: the email path read no principal row: {email_seen!r}"
            )
            assert id_principal_reads == 0, f"the proven-id path re-read the principal row: {id_seen!r}"


class TestEveryRowVerbPreReadsItsRowOnce:
    """amendment 7 §4 FK-6 rider (v): ``authorize_guarded`` takes an ADDRESS (``row_id=`` or ``number=``), so
    a by-number write is ONE read too; the invisibility derivation re-uses that same row. ∀ row-addressing
    capability write verb (DERIVED) × {id, number}: exactly ONE statement reads ``finding`` before the first
    transaction, and it is the governed pre-read (it projects ``owner_principal``)."""

    async def test_every_verb_and_address_form(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """⚠ RED at HEAD (no capability=)."""
        drivers = {verb: driver for verb, driver in _required_drivers().items() if driver.addresses_a_row}
        async with finding_world(monkeypatch, tmp_path) as world:
            from loremaster.store import _txn  # noqa: PLC0415

            events: list[tuple[str, str]] = []
            for name, kind in (
                ("run_query", "read"),
                ("execute_read_transaction", "txn"),
                ("execute_transaction", "txn"),
            ):
                real = getattr(_txn, name)

                def _wrap(real: Any = real, kind: str = kind) -> Any:
                    async def _spy(*args: Any, **kwargs: Any) -> Any:
                        events.append((kind, str(kwargs.get("statement", args[0] if args else ""))))
                        return await real(*args, **kwargs)

                    return _spy

                patch_shared_object_everywhere(
                    monkeypatch, name, real, _wrap(), expect_in=("loremaster.store._txn",)
                )
            violations: list[str] = []
            number = 8800
            for verb, driver in sorted(drivers.items()):
                for form in ("id", "number"):
                    number += 1
                    actor = "ag-a1" if verb == "set_scope" else "ag-b1"
                    row_id = await world.seed(
                        row_id=new_row_id("one"), number=number, owner="ag-a1", scope_key="AB"
                    )
                    kwargs = driver.kwargs(world, row_id if form == "id" else number)
                    if verb == "set_scope":
                        kwargs["scope"] = world.scopes["A"]
                    events.clear()
                    await world.findings(actor, **kwargs)
                    first_txn = next((i for i, (kind, _s) in enumerate(events) if kind == "txn"), len(events))
                    reads = [
                        s
                        for kind, s in events[:first_txn]
                        if kind == "read" and FINDING_TABLE in _read_tables(s)
                    ]
                    if len(reads) != 1 or "owner_principal" not in reads[0]:
                        violations.append(
                            f"{verb} by {form}: {len(reads)} finding read(s) before the CAS: {reads}"
                        )
            assert not violations, "\n".join(violations)


# =========================================================================== #
# MP-8 — ONE identity-compare site across every dispatcher.
# =========================================================================== #


def _identity_compare_sites() -> list[tuple[str, int, str]]:
    """Every ``Compare`` in ``server.py`` whose one side is a dispatcher's ``agent``/``session`` Name and
    whose other side reads ``.name``/``.session`` off anything — (enclosing function, line, text).
    Receiver-BLIND: the record's variable name is never keyed (a renamed ``own_row`` is still found)."""
    tree = ast.parse(_SERVER_PY.read_text(encoding="utf-8"))
    owners: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for child in ast.walk(node):
                owners.setdefault(id(child), node.name)
    sites: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        operands = [node.left, *node.comparators]
        names = {op.id for op in operands if isinstance(op, ast.Name)}
        attrs = {op.attr for op in operands if isinstance(op, ast.Attribute)}
        if (
            names & {"agent", "session"}
            and attrs & {"name", "session"}
            and any(isinstance(op, ast.Eq | ast.NotEq) for op in node.ops)
        ):
            sites.append((owners.get(id(node), "<module>"), node.lineno, ast.unparse(node)))
    return sites


#: The functions ALLOWED to compare a supplied ``agent``/``session`` against an agent row — ALLOWLIST THE SAFE
#: (CLAUDE.md instrument lesson): the ONE identity-policy site, plus the R8(1) footer's "link 2 of the forgery
#: closure" — a check on OUR OWN REGISTRY (a row resolved BY NAME must carry that name), never a decision
#: about
#: the caller's identity (it serves SILENCE on a mismatch; pinned by ``test_comms_footer.py``). A third site
#: anywhere in ``server.py`` reds by name.
IDENTITY_COMPARE_ALLOWLIST: dict[str, str] = {
    "_resolve_identity": "THE identity compare (kickoff §6 rider iv; am-2 §1 item 2; am-8 §1)",
    "_resolved_comms_traffic_line": (
        "R8(1) link 2 — the registry self-check on a BY-NAME resolve (not an identity decision)"
    ),
}


class TestTheIdentityCompareLivesInOneFunction:
    """MP-8's CLASS (amendment 8 §6 row 7; kickoff §6 rider iv as amended by am-2 §1 item 2): EVERY
    comparison of a supplied ``agent``/``session`` against an agent row's ``name``/``session`` — over the
    WHOLE ``server.py`` (every dispatcher: comms, findings, tasks, claim), receiver-BLIND — lies in an
    ALLOWLISTED function, and the identity policy's own compares (``agent`` AND ``session``) live in
    ``AppContext._resolve_identity``. A dispatcher that routes through the helper but ALSO compares on its
    own (WB21) is a private copy wearing the shared name (ROUTING IS NOT SHARING) and reds by name."""

    def test_every_compare_site_is_allowlisted_and_the_policy_is_in_the_one_helper(self) -> None:
        """⚠ RED at HEAD (``_resolve_identity`` absent — the policy leg names it)."""
        sites = _identity_compare_sites()
        stray = [site for site in sites if site[0] not in IDENTITY_COMPARE_ALLOWLIST]
        assert not stray, f"identity compares outside the allowlisted functions (a private copy): {stray}"
        policy = " ".join(text for function, _line, text in sites if function == "_resolve_identity")
        assert re.search(r"\bagent\b", policy) and re.search(r"\bsession\b", policy), (
            f"AppContext._resolve_identity does not compare BOTH agent= and session=: {sites}"
        )


# =========================================================================== #
# MP-11 — ∀ migrate leg: the write set is the requested table + its NAMED dependencies.
# =========================================================================== #

#: table → the OTHER tables its leg may legitimately write (the NAMED dependencies — amendment 8 §6 row 8):
#: a project-keep mint (memory, finding) writes ``keep`` + its household edge ``member_of``. COMPLETENESS:
#: every DERIVED migrate table must have a row (a new leg with no declaration reds by name).
MIGRATE_WRITE_DEPENDENCIES: dict[str, frozenset[str]] = {
    "agent": frozenset({"keep", "member_of"}),
    "memory": frozenset({"keep", "member_of"}),
    "message": frozenset(),
    "brief": frozenset(),
    "finding": frozenset({"keep", "member_of"}),
}
#: every table the sweep snapshots — the governed populations + the keep/household/principal tables a leg
#: could reach.
_SNAPSHOT_TABLES = ("agent", "memory", "message", "brief", "finding", "keep", "member_of", "principal", "to")


class TestAMigrateLegWritesOnlyItsOwnTable:
    """MP-11's CLASS (amendment 8 §6 row 8): ∀ table in ``principals._MIGRATE_VALID_TABLES`` (DERIVED), with
    a legacy row in EVERY governed table, ``migrate_governed(table=T)`` leaves every table outside ``{T} ∪
    MIGRATE_WRITE_DEPENDENCIES[T]`` byte-identical — on the PROCEED path (the r1 contract checked only the
    refusal path; WB22b migrated memory under ``--table finding`` after its precondition passed)."""

    async def test_every_leg(self) -> None:
        """⚠ RED at HEAD for ``finding`` (not in the derived set — the completeness leg names it)."""
        from _governed_contract import seed_agent_legacy, seed_memory_legacy  # noqa: PLC0415
        from _governed_contract_64 import frozen_asserted_finding_ddl, seed_finding_legacy  # noqa: PLC0415
        from test_findings_migrate_64b import _migrate_world, _upgrade_finding_schema  # noqa: PLC0415

        tables = tuple(vars(principals)["_MIGRATE_VALID_TABLES"])
        assert FINDING_TABLE in tables, (
            f"the finding leg is not a migrate table: {tables} (kickoff §2 F1 unbuilt)"
        )
        undeclared = set(tables) - MIGRATE_WRITE_DEPENDENCIES.keys()
        assert not undeclared, f"migrate tables with no declared write dependencies: {sorted(undeclared)}"
        violations: list[str] = []
        for table in tables:
            async with _migrate_world(frozen_asserted_finding_ddl()) as world:
                await seed_agent_legacy(
                    world.connection, row_id="legacy_agent", name="legacy-agent", session="s11"
                )
                await seed_memory_legacy(world.connection, row_id="legacy_memory", dim=8)
                await seed_finding_legacy(world.connection, row_id="legacy_finding", number=1)
                await _upgrade_finding_schema(world)
                allowed = {table} | MIGRATE_WRITE_DEPENDENCIES[table]
                before = {name: await _snapshot_table(world.connection, name) for name in _SNAPSHOT_TABLES}
                await world.migrate(table)
                for name in _SNAPSHOT_TABLES:
                    if name in allowed:
                        continue
                    if await _snapshot_table(world.connection, name) != before[name]:
                        violations.append(f"--table {table} wrote to {name!r} (not a named dependency)")
        assert not violations, "\n".join(violations)


async def _snapshot_table(connection: Any, table: str) -> Any:
    try:
        return await run(connection, f"SELECT * FROM {table} ORDER BY id")
    except Exception as error:  # noqa: BLE001 - an undeclared table reads as its own absence
        return f"<unreadable: {type(error).__name__}>"


# =========================================================================== #
# WB23 / MP-13 — a param outside its verb's spec is REFUSED, never ignored.
# =========================================================================== #

#: param → the verbs that OWN it (kickoff §5 table / am-2 §4): every OTHER verb refuses it with the
#: strict-param
#: teaching. COMPLETENESS: every owner is a served verb (a stale owner reds).
VERB_OWNED_PARAMS: dict[str, frozenset[str]] = {
    "scope": frozenset({"report", "set_scope"}),
    "items": frozenset({"resolve_many", "acknowledge_many"}),
}


class TestAParamOutsideItsVerbsSpecIsRefused:
    """MP-13's CLASS (amendment 8 §6 row 9; #319's shape): ∀ served verb × ∀ verb-owned param the verb does
    NOT own, a supplied value is a teaching refusal NAMING the owners — never accepted-and-ignored (WB23
    deleted the ``scope`` branch and survived 981 tests). ZERO writes, ZERO capability resolutions."""

    async def test_every_verb_param_pair(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """⚠ RED at HEAD (``scope=`` is not a finding param at all)."""
        actions = list(vars(server)["_FINDING_ACTIONS"])
        stale = {param: sorted(owners - set(actions)) for param, owners in VERB_OWNED_PARAMS.items()}
        assert not any(stale.values()), f"param owners that are not served verbs: {stale}"
        async with finding_world(monkeypatch, tmp_path) as world:
            await world.seed(row_id=new_row_id("prm"), number=8900, owner="ag-a1", scope_key="AB")
            count_before = await _finding_count(world)
            # "the capability was never resolved" is observed at the STORE SEAM (any statement reading
            # ``agent`` — the capability verify), never through ONE method name a build may route around
            # (MP-7's reach lesson).
            seen = _record_store_statements(monkeypatch)
            violations: list[str] = []
            for param, owners in sorted(VERB_OWNED_PARAMS.items()):
                value: Any = world.scopes["AB"] if param == "scope" else [{"id_or_number": 8900}]
                for verb in actions:
                    if verb in owners:
                        continue
                    seen.clear()
                    kwargs: dict[str, Any] = {"action": verb, param: value}
                    if verb not in ("query",) and param != "items":
                        kwargs["id_or_number"] = 8900
                    try:
                        if verb in capability_write_verbs():
                            await world.findings("ag-b1", **kwargs)
                        else:  # a read verb takes no capability (am-3 D-1b) — call it bare, as a reader would
                            world.act_as("ag-b1")
                            await world.ctx.findings(**kwargs)
                    except ValueError as error:
                        text = str(error)
                        if param not in text or not any(owner in text for owner in owners):
                            violations.append(f"{verb} × {param}: the refusal does not teach: {text!r}")
                    except Exception as error:  # noqa: BLE001 - any other outcome is not the teaching refusal
                        violations.append(f"{verb} × {param}: {type(error).__name__}: {error}")
                    else:
                        violations.append(f"{verb} × {param}: ACCEPTED (silently ignored)")
                    if any("agent" in _read_tables(statement) for statement in seen):
                        violations.append(f"{verb} × {param}: the capability was resolved before the refusal")
            assert not violations, "\n".join(violations)
            assert await _finding_count(world) == count_before
