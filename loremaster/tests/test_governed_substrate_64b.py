"""Contract — packet 64b-i: the SUBSTRATE touches the findings retrofit needs (kickoff rulings ``e5fa7f9``
§4.3 / §11; amendment 1 §7 keeps ``Resource`` 4-field for 64b). Authored by ``contract-64b`` (Opus 5.5,
contract tests ONLY — no production code).

WHAT IS PINNED (each class names its ruling row):
- #414/#415 — ``governed.resource_from_row(row)`` is the ONE row→``Resource`` constructor and DERIVES
  ``table`` from the row's id (never a caller field); ``authorize_guarded`` refuses a pre-read row whose
  id table disagrees with its ``table`` argument; the AST allowlist admits ``Resource(`` in production
  ONLY inside ``resource_from_row`` (reach DERIVED over every workspace member).
- #418 — ``And(())``/``Or(())`` are the identity elements (``true``/``false``), ``to_surql`` ≡ ``matches``
  on the empty case, live on the engine.
- #411 — ``AuditStore.append`` CONSUMES ``append_fragment`` (an EFFECT spy, not text equality).
- #407 — ``governed.classify_zero_row_cas`` is the ONE zero-row classifier: fresh-row DENY ⇒
  ``GovernedConflict``; vanished ⇒ the ledger verdict on ``None``; else the ledger verdict on the FRESH
  row; driver-routed; never through ``wrap_store_rejection``.
- §4.3 — ``GuardedPlan.guard()`` / ``GuardedPlan.compose()`` (the ONE audit attach site) /
  ``authorize_guarded(projection=…)`` (the ledger's columns ride the ONE governed pre-read).
- #429 — the ``guarded_write`` SET_SCOPE and DELETE branches, each with positive controls.
- the ledger accessors ``FindingLedger.handle`` / ``FindingLedger.audit_store`` (F-9; the
  ``StoreHandle`` docstring's promise).

NAMING CHOICES MADE HERE (the kickoff left them to the contract author — REPORT §FORKS lists each):
``classify_zero_row_cas(store, *, table, row_id, subject, action, ledger_verdict)`` with a SYNC
``ledger_verdict(row | None)``; ``authorize_guarded``/``guarded_write`` gain ``target_scope=`` (the PDP's
own keyword) and ``guarded_write`` gains ``params=`` (a pass-through to the existing
``GuardedPlan.fragments(set_fragment, params)``).

RED@HEAD reasons: every new symbol/keyword is absent at ``6a09954`` (read via ``vars(module).get`` /
``inspect.signature`` FIRST, so the RED names the unbuilt feature, never a ``TypeError``/
``AttributeError``); #418's ``And(())`` emits ``"()"``; ``authorize_guarded`` builds ``Resource`` from its
argument. GREEN@HEAD instruments (mutation-proven in the report): the #411 spy and the #429 DELETE legs.

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique database, reaped.
"""

from __future__ import annotations

import ast
import inspect
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
import pytest_asyncio
from _governed_contract import (
    admin,
    apply_ddl,
    function_calls_named,
    governed_overlay_ddl,
    member,
    store_handle,
)
from _governed_contract_64 import (
    FINDING_TABLE,
    current_finding_ddl,
    finding_row,
    seed_finding_governed,
)
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database
from loremaster.store import surreal_schema
from loremaster.store._txn import StoreHandle
from pydantic import SecretStr
from surrealdb import RecordID

import lorerunes as pdp
from loremaster import governed

if TYPE_CHECKING:
    from loremaster.findings import FindingLedger
    from loremaster.governed import classify_zero_row_cas, resource_from_row

    # 64b-i's RULED, not-yet-built symbols this file pins — named STATICALLY for the typecheck gate. Until the
    # build lands them each is a mypy error OWNED by `scripts/pending_contracts.yaml` bound
    # `packet-64b-i-contract`, which self-destructs (delete the entry) once they exist (lead #17055, #461).
    # Runtime-inert: never executed, so every pin still REDs at HEAD on its own teaching message.
    _RULED_64B_I: tuple[object, ...] = (
        resource_from_row,  # #414/#415
        classify_zero_row_cas,  # #407
        governed.GuardedPlan.guard,  # kickoff §4.3
        governed.GuardedPlan.compose,  # kickoff §4.3
        FindingLedger.handle,  # F-9
        FindingLedger.audit_store,  # F-9
    )

_DIM = 8
_GOVERNED_PY = Path(governed.__file__)

_KEEP_A = pdp.keep_scope("keepalpha")
_KEEP_B = pdp.keep_scope("keepbravo")
_KEEP_AB = pdp.keep_scope("keepalphabravo")


def _required(module: Any, name: str) -> Any:
    """The RED-for-the-right-reason accessor: an absent symbol is an AssertionError NAMING the unbuilt
    seam, never an ``AttributeError`` at collection."""
    value = vars(module).get(name)
    assert value is not None, f"UNBUILT: `{module.__name__}.{name}` does not exist (kickoff §4.3/§11)"
    return value


def _require_keyword(function: Any, keyword: str, ruling: str) -> None:
    params = inspect.signature(function).parameters
    assert keyword in params, (
        f"UNBUILT ({ruling}): `{function.__qualname__}` has no `{keyword}=` keyword — got {list(params)}"
    )


def _count(rows: Any) -> int:
    return int(rows[0]["count"]) if isinstance(rows, list) and rows else 0


def _audit_store(env: Any) -> Any:
    from loremaster.audit import AuditStore  # noqa: PLC0415

    password = env.password if isinstance(env.password, SecretStr) else SecretStr(str(env.password))
    return AuditStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=password
    )


@pytest_asyncio.fixture()
async def substrate_world() -> AsyncIterator[dict[str, Any]]:
    """One unified test DB: the CURRENT ``finding`` DDL + the governed overlay (idempotent with the 64b
    emitter; lets governed rows seed at HEAD) + the ``audit`` DDL + a ready ``AuditStore``. Subjects are
    SYNTHETIC (``member``/``admin``) — record links need no live target for the PDP's equality."""
    env = make_env(database=unique_database(), dim=_DIM)
    connection = await connect_admin(env)
    audit_store = _audit_store(env)
    try:
        await apply_ddl(connection, current_finding_ddl(), url=env.url)
        await apply_ddl(connection, governed_overlay_ddl(FINDING_TABLE), url=env.url)
        await apply_ddl(connection, surreal_schema.generate_audit_ddl(), url=env.url)
        await audit_store.ensure_ready()
        yield {"env": env, "connection": connection, "audit": audit_store}
    finally:
        await audit_store.close()
        await connection.close()
        await drop_database(env)


async def _audit_rows(connection: Any) -> int:
    return _count(await run(connection, "SELECT count() FROM audit GROUP ALL"))


# =========================================================================== #
# #414 / #415 — resource_from_row: the table is DERIVED from the row id.
# =========================================================================== #


class TestResourceFromRowDerivesTheTable:
    """#414/#415 (kickoff §11 row): the ONE row→``Resource`` constructor derives ``table`` from
    ``row['id']`` (``RecordID.table_name``) — a caller cannot hand a row of one table to the PDP as
    another. TWO table values (finding, audit) so a build that hard-codes ``finding`` reds."""

    @pytest.mark.parametrize(
        ("table", "scope"),
        [("finding", "server"), ("audit", pdp.SCOPE_PRINCIPAL_PRIVATE), ("memory", _KEEP_AB)],
    )
    def test_the_table_comes_from_the_row_id(self, table: str, scope: str) -> None:
        """⚠ RED at HEAD (``resource_from_row`` absent). Kills: a constructor that reads a ``table``
        argument; one that hard-codes ``finding``; one that drops the owner links' bare ids."""
        resource_from_row = _required(governed, "resource_from_row")
        row = {
            "id": RecordID(table, "row1"),
            "owner_principal": RecordID("principal", "alice"),
            "owner_agent": RecordID("agent", "ag_a1"),
            "scope": scope,
        }
        assert resource_from_row(row) == pdp.Resource(
            table=table, owner_principal="alice", owner_agent="ag_a1", scope=scope
        )

    def test_a_dirty_row_maps_absent_columns_to_None(self) -> None:
        """⚠ RED at HEAD. A legacy NONE/NONE/NONE row (``SELECT`` omits NONE columns — store-ref §2) maps
        to the absent-owner / absent-scope ``Resource`` (FORK 1, §10.1), never a KeyError, never ``""``."""
        resource_from_row = _required(governed, "resource_from_row")
        assert resource_from_row({"id": RecordID("finding", "legacy1")}) == pdp.Resource(
            table="finding", owner_principal=None, owner_agent=None, scope=None
        )

    async def test_authorize_guarded_refuses_a_pre_read_row_from_another_table(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD. The #414/#415 door: ``authorize_guarded(table='finding')`` handed a pre-read
        row whose id is ``audit:x`` must REFUSE (``GovernedDenied`` naming BOTH tables) — an internal
        invariant, taught, never a silent trust of the argument. ADMIN subject on purpose: at HEAD the
        admin ``AllRows`` predicate ALLOWS, so HEAD returns a plan (RED); a correct build raises before
        the PDP is consulted. CONTROL: the SAME row shape with a ``finding:x`` id is NOT refused — the
        refusal is keyed on the mismatch, not on the subject or the row."""
        _required(governed, "resource_from_row")

        async def _forged_pre_read(**_kwargs: Any) -> list[dict[str, Any]]:
            return [
                {
                    "id": RecordID(forged["table"], "x"),
                    "owner_principal": RecordID("principal", "bob"),
                    "owner_agent": RecordID("agent", "ag_b1"),
                    "scope": pdp.SCOPE_SERVER,
                }
            ]

        forged = {"table": "audit"}
        monkeypatch.setattr(governed, "run_query", _forged_pre_read)
        handle = StoreHandle(acquire=_never_acquire, drop=_never_drop, url="ws://127.0.0.1:18000/rpc")
        with pytest.raises(governed.GovernedDenied) as refusal:
            await governed.authorize_guarded(
                admin("alice", "ag_a1"),
                pdp.Action.WRITE,
                table="finding",
                row_id="x",
                audit=object(),
                store=handle,
            )
        text = str(refusal.value)
        assert "audit" in text and "finding" in text, (
            f"the mismatch refusal must NAME both the row's table and the argument's: {text!r}"
        )
        forged["table"] = "finding"  # CONTROL — the id agrees with the argument
        plan = await governed.authorize_guarded(
            admin("alice", "ag_a1"),
            pdp.Action.WRITE,
            table="finding",
            row_id="x",
            audit=object(),
            store=handle,
        )
        assert plan.table == "finding"

    def test_resource_from_row_is_the_only_production_Resource_constructor(self) -> None:
        """⚠ RED at HEAD (the constructor lives inline in ``authorize_guarded``). The R-a.2-style AST
        allowlist, REACH DERIVED: every production ``Resource(`` call across EVERY workspace member's
        source (THE shared ``parse_production_trees`` — never a file hand-list) must sit inside
        ``governed.resource_from_row``. Non-vacuity: the derivation must find ≥1 site (a scan that finds
        nothing reds). A second constructor anywhere — a private copy that reads a caller ``table`` —
        grows the derived set and reds by name."""
        allowed = {("loremaster/loremaster/governed.py", "resource_from_row")}
        sites = _resource_construction_sites()
        assert sites, "the Resource( scan found NO production construction site — a vacuous scan"
        stray = sorted(site for site in sites if (site[0], site[1]) not in allowed)
        assert not stray, (
            "production constructs lorerunes.Resource outside governed.resource_from_row (#414/#415 — the "
            f"table must be DERIVED from the row id, in ONE place): {stray}"
        )


async def _never_acquire() -> Any:
    raise AssertionError("the pre-read was patched — nothing may acquire a real connection here")


async def _never_drop(_connection: Any) -> None:
    return None


def _resource_construction_sites() -> list[tuple[str, str, int]]:
    """(repo-relative file, enclosing function, line) of every production ``Resource(`` / ``*.Resource(``
    call — over THE shared production parse (``_logging_fixtures.parse_production_trees``: every workspace
    member's package root, tests excluded by construction), with its reach a CHECKED variable
    (``assert_scan_reached_every_member`` — a member that stops being scanned reds, never shrinks the set)."""
    from _logging_fixtures import (  # noqa: PLC0415 - house lazy-import idiom
        assert_scan_reached_every_member,
        parse_production_trees,
    )

    trees = parse_production_trees(include_scripts=False)
    assert_scan_reached_every_member(trees, extra_roots=())
    sites: list[tuple[str, str, int]] = []
    for relative, tree in trees.items():
        owners: dict[int, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                for child in ast.walk(node):
                    owners.setdefault(id(child), node.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            named = (isinstance(func, ast.Name) and func.id == "Resource") or (
                isinstance(func, ast.Attribute) and func.attr == "Resource"
            )
            if named:
                sites.append((relative, owners.get(id(node), "<module>"), node.lineno))
    return sites


# =========================================================================== #
# #418 — the empty conjunction / disjunction are the identity elements.
# =========================================================================== #


class TestTheEmptyPredicateIsTheIdentityElement:
    """#418 (kickoff §11 row): ``And(())`` is the AND identity (``true``), ``Or(())`` the OR identity
    (``false``); ``to_surql`` ≡ ``matches`` on the empty case; single-child nodes unchanged."""

    def test_empty_And_emits_true_and_matches_everything(self) -> None:
        """⚠ RED at HEAD (``And(()).to_surql()`` is ``("()", {})`` — a parse error in a WHERE)."""
        resource = pdp.Resource(table="finding", owner_principal=None, owner_agent=None, scope="server")
        assert pdp.And(()).to_surql() == ("true", {})
        assert pdp.And(()).matches(resource) is True

    def test_empty_Or_emits_false_and_matches_nothing(self) -> None:
        """⚠ RED at HEAD (``Or(()).to_surql()`` is ``("()", {})``)."""
        resource = pdp.Resource(table="finding", owner_principal=None, owner_agent=None, scope="server")
        assert pdp.Or(()).to_surql() == ("false", {})
        assert pdp.Or(()).matches(resource) is False

    def test_a_single_child_node_is_unchanged(self) -> None:
        """GREEN at HEAD (a control): the identity guard touches ONLY the empty case — a build that
        rewrites every node's emission (dropping the parentheses #416 relies on) reds here."""
        child = pdp.ScopeEq(pdp.SCOPE_SERVER)
        child_text, child_params = child.to_surql()
        assert pdp.And((child,)).to_surql() == (f"({child_text})", child_params)
        assert pdp.Or((child,)).to_surql() == (f"({child_text})", child_params)

    async def test_the_empty_nodes_run_on_the_engine_as_their_identities(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD (``WHERE ()`` does not parse). to_surql ≡ matches, LIVE: the empty ``And``
        selects every row and the empty ``Or`` none, over two seeded rows (≥2 so ``all`` ≠ ``any``)."""
        connection = substrate_world["connection"]
        for index in (1, 2):
            await seed_finding_governed(
                connection,
                row_id=f"idem{index}",
                number=900 + index,
                owner_principal="alice",
                owner_agent="ag_a1",
                scope=pdp.SCOPE_SERVER,
            )
        and_fragment, and_params = pdp.And(()).to_surql()
        or_fragment, or_params = pdp.Or(()).to_surql()
        everything = await run(
            connection, f"SELECT VALUE id FROM {FINDING_TABLE} WHERE {and_fragment}", and_params
        )
        nothing = await run(
            connection, f"SELECT VALUE id FROM {FINDING_TABLE} WHERE {or_fragment}", or_params
        )
        assert len(everything) == 2 and nothing == [], (everything, nothing)


# =========================================================================== #
# #411 — AuditStore.append consumes append_fragment (an effect, not text).
# =========================================================================== #


class TestAuditAppendConsumesItsFragment:
    """#411 (kickoff §11 row, "IN (cheap)"): the routing pin was text-equality; this is the EFFECT spy.
    GREEN at HEAD (the code is right; the instrument was weak) — mutation-proven in the report by
    hand-rolling a second CREATE inside ``append`` (the spy then sees zero calls → RED)."""

    async def test_append_builds_its_write_from_append_fragment(
        self, substrate_world: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from loremaster.audit import AuditStore  # noqa: PLC0415

        audit_store = substrate_world["audit"]
        real = AuditStore.append_fragment
        produced: list[str] = []

        def _spy(self: Any, **kwargs: Any) -> Any:
            fragment = real(self, **kwargs)
            produced.append(str(fragment.params["audit_id"]))
            return fragment

        monkeypatch.setattr(AuditStore, "append_fragment", _spy)
        created = await audit_store.append(
            actor_principal="alice",
            actor_agent="ag_a1",
            actor_email="alice@example.com",
            actor_agent_name="ag-a1",
            action="WRITE",
            target_table="finding",
            target_row="finding:f1",
        )
        assert len(produced) == 1, f"append did not consume append_fragment exactly once: {produced}"
        assert created.endswith(produced[0]), (created, produced)
        stored = await run(
            substrate_world["connection"],
            "SELECT VALUE id FROM type::record('audit', $id)",
            {"id": produced[0]},
        )
        assert stored, "the fragment append_fragment built is not the row that landed"


# =========================================================================== #
# #407 — classify_zero_row_cas: the ONE zero-row classifier.
# =========================================================================== #


class TestTheZeroRowCasClassifierIsOneHelper:
    """#407 (kickoff §11 / §4.3 item 4): on a zero-row CAS rollback the ONE helper re-reads the row
    (through the injected handle — R4), asks ``authorize(subject, action, resource_from_row(fresh))``:
    DENY ⇒ ``GovernedConflict`` (a re-scope/re-own landed between gate and CAS — loud, never a ledger
    verdict); vanished ⇒ ``ledger_verdict(None)``; else ``ledger_verdict(fresh)``. The four legs use
    DIFFERENT subjects and scopes so a build that skips the authorize step, or that never re-reads,
    reds on at least one."""

    @staticmethod
    def _verdict_recorder() -> tuple[list[Any], Any]:
        seen: list[Any] = []

        def _verdict(row: Any) -> Any:
            seen.append(row)
            return ("verdict", None if row is None else row.get("status"))

        return seen, _verdict

    async def test_a_fresh_row_the_subject_may_no_longer_write_is_a_governed_conflict(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD. The row now sits in ``keep:B`` (bob's household); alice (keeps {A}) may not
        WRITE it ⇒ ``GovernedConflict``, and the ledger verdict is NEVER consulted."""
        classify = _required(governed, "classify_zero_row_cas")
        connection, env = substrate_world["connection"], substrate_world["env"]
        await seed_finding_governed(
            connection,
            row_id="rescoped",
            number=501,
            owner_principal="bob",
            owner_agent="ag_b1",
            scope=_KEEP_B,
            status="acknowledged",
        )
        handle, calls = store_handle(connection, url=env.url)
        seen, verdict = self._verdict_recorder()
        with pytest.raises(governed.GovernedConflict):
            await classify(
                handle,
                table=FINDING_TABLE,
                row_id="rescoped",
                subject=member("alice", "ag_a1", frozenset({_KEEP_A})),
                action=pdp.Action.WRITE,
                ledger_verdict=verdict,
            )
        assert seen == [], "a DENY must never be mis-served as the ledger's own lost-race verdict"
        assert calls["acquire"] >= 1, "the re-read bypassed the injected handle (R4)"

    async def test_a_fresh_row_the_subject_may_still_write_gets_the_ledger_verdict_on_the_FRESH_row(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD. Bob (householded in ``keep:AB``) on alice's ``keep:AB`` row now ``resolved``:
        ALLOW ⇒ the helper RETURNS ``ledger_verdict(fresh)`` and the verdict saw the FRESH status (a
        build that hands the verdict the stale pre-read, or nothing, reds)."""
        classify = _required(governed, "classify_zero_row_cas")
        connection, env = substrate_world["connection"], substrate_world["env"]
        await seed_finding_governed(
            connection,
            row_id="raced",
            number=502,
            owner_principal="alice",
            owner_agent="ag_a1",
            scope=_KEEP_AB,
            status="resolved",
        )
        handle, _calls = store_handle(connection, url=env.url)
        seen, verdict = self._verdict_recorder()
        outcome = await classify(
            handle,
            table=FINDING_TABLE,
            row_id="raced",
            subject=member("bob", "ag_b1", frozenset({_KEEP_AB, _KEEP_B})),
            action=pdp.Action.WRITE,
            ledger_verdict=verdict,
        )
        assert outcome == ("verdict", "resolved"), outcome
        assert len(seen) == 1 and seen[0] is not None and seen[0].get("status") == "resolved", seen

    async def test_a_vanished_row_gets_the_ledger_verdict_on_None(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD. The row is gone ⇒ ``ledger_verdict(None)`` (the ledger decides its own
        not-found wording) — never a ``GovernedConflict`` (nothing to authorize) and never a crash."""
        classify = _required(governed, "classify_zero_row_cas")
        handle, _calls = store_handle(substrate_world["connection"], url=substrate_world["env"].url)
        seen, verdict = self._verdict_recorder()
        outcome = await classify(
            handle,
            table=FINDING_TABLE,
            row_id="never_existed",
            subject=member("alice", "ag_a1", frozenset({_KEEP_A})),
            action=pdp.Action.WRITE,
            ledger_verdict=verdict,
        )
        assert outcome == ("verdict", None) and seen == [None], (outcome, seen)

    async def test_an_admin_is_never_a_conflict_on_a_foreign_row(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD. The admin control (``AllRows``): a foreign ``principal-private`` row returns
        the ledger verdict — the DENY branch is the PDP's verdict, not a hard-coded ownership compare."""
        classify = _required(governed, "classify_zero_row_cas")
        connection, env = substrate_world["connection"], substrate_world["env"]
        await seed_finding_governed(
            connection,
            row_id="foreign",
            number=503,
            owner_principal="bob",
            owner_agent="ag_b1",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
            status="wontfix",
        )
        handle, _calls = store_handle(connection, url=env.url)
        seen, verdict = self._verdict_recorder()
        outcome = await classify(
            handle,
            table=FINDING_TABLE,
            row_id="foreign",
            subject=admin("carol", "ag_c1"),
            action=pdp.Action.WRITE,
            ledger_verdict=verdict,
        )
        assert outcome == ("verdict", "wontfix"), outcome

    def test_the_helper_never_routes_through_wrap_store_rejection_and_builds_its_resource_in_one_place(
        self,
    ) -> None:
        """⚠ RED at HEAD. #407's own warning: ``wrap_store_rejection`` DELETES the re-read (a
        regression). And the fresh row's ``Resource`` comes from THE constructor (#414/#415)."""
        _required(governed, "classify_zero_row_cas")
        source = _GOVERNED_PY.read_text(encoding="utf-8")
        assert not function_calls_named(source, "classify_zero_row_cas", "wrap_store_rejection"), (
            "classify_zero_row_cas routes through wrap_store_rejection — that seam deletes the re-read (#407)"
        )
        assert function_calls_named(source, "classify_zero_row_cas", "resource_from_row"), (
            "classify_zero_row_cas builds its Resource without governed.resource_from_row (#414/#415)"
        )


# =========================================================================== #
# §4.3 — GuardedPlan.guard / GuardedPlan.compose / authorize_guarded(projection=)
# =========================================================================== #


class TestGuardedPlanExposesTheGuardAndTheOneAuditAttachSite:
    """Kickoff §4.3 items 2–3: ``guard()`` exposes the in-store conjunct a ledger shell ANDs into its own
    WHERE; ``compose(*caller_fragments)`` is THE one place the audit append attaches (``guarded_write``
    becomes ``compose(fragments(set))``), so the by-id path and the compose-with-caller path share the
    attach site — ROUTING-IS-NOT-SHARING by construction."""

    async def _admin_bypass_plan(self, world: dict[str, Any], row_id: str) -> Any:
        await seed_finding_governed(
            world["connection"],
            row_id=row_id,
            number=600 + len(row_id),
            owner_principal="bob",
            owner_agent="ag_b1",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        handle, _calls = store_handle(world["connection"], url=world["env"].url)
        return await governed.authorize_guarded(
            admin("carol", "ag_c1"),
            pdp.Action.WRITE,
            table=FINDING_TABLE,
            row_id=row_id,
            audit=world["audit"],
            store=handle,
        )

    async def test_guard_returns_the_plans_own_fragment_and_params(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD (no ``guard``). ONE accessor over the two existing fields — a build that
        recomputes a DIFFERENT predicate for the shell reds on the equality."""
        plan = await self._admin_bypass_plan(substrate_world, "guardacc")
        guard = getattr(plan, "guard", None)
        assert callable(guard), "UNBUILT (kickoff §4.3 item 2): GuardedPlan has no guard() accessor"
        assert guard() == (plan.guard_fragment, plan.guard_params)

    async def test_compose_attaches_the_audit_exactly_once_and_fragments_never_does(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD (no ``compose``; ``fragments`` attaches the audit itself). A ``requires_audit``
        plan: ``fragments(set)`` alone carries ZERO audit statements; ``compose(caller…)`` returns the
        caller's fragments unchanged + EXACTLY ONE audit fragment. A build that keeps the attach in
        ``fragments`` AND adds it in ``compose`` double-audits (2) and reds."""
        plan = await self._admin_bypass_plan(substrate_world, "composeaud")
        assert plan.requires_audit is True, "fixture: the admin write on bob's private row is a bypass"
        compose = getattr(plan, "compose", None)
        assert callable(compose), "UNBUILT (kickoff §4.3 item 3): GuardedPlan has no compose()"
        mutation = plan.fragments("body = 'x'")
        assert _audit_statements(mutation) == 0, (
            "GuardedPlan.fragments still attaches the audit — the ONE attach site is compose() (§4.3)"
        )
        composed = compose(*mutation)
        assert composed[: len(mutation)] == mutation, (
            "compose must return the caller's fragments first, unchanged"
        )
        assert _audit_statements(composed) == 1, (
            f"compose attached {_audit_statements(composed)} audit appends"
        )

    async def test_compose_attaches_nothing_when_no_audit_is_required(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD. A member writing its OWN private row: ``requires_audit`` False ⇒ ``compose``
        is the identity on the caller's fragments (no trail for a non-bypass — 61 Fork G)."""
        connection, env = substrate_world["connection"], substrate_world["env"]
        await seed_finding_governed(
            connection,
            row_id="ownrow",
            number=611,
            owner_principal="alice",
            owner_agent="ag_a1",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        handle, _calls = store_handle(connection, url=env.url)
        plan = await governed.authorize_guarded(
            member("alice", "ag_a1", frozenset()),
            pdp.Action.WRITE,
            table=FINDING_TABLE,
            row_id="ownrow",
            audit=substrate_world["audit"],
            store=handle,
        )
        compose = getattr(plan, "compose", None)
        assert callable(compose), "UNBUILT (kickoff §4.3 item 3): GuardedPlan has no compose()"
        mutation = plan.fragments("body = 'y'")
        assert compose(*mutation) == mutation

    async def test_guarded_write_attaches_its_audit_through_compose(
        self, substrate_world: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD. ``guarded_write`` = ``compose(fragments(set))``: a spy on ``GuardedPlan.compose``
        sees exactly ONE call for an admin bypass, and exactly ONE audit row lands (not 0, not 2)."""
        compose = vars(governed.GuardedPlan).get("compose")
        assert compose is not None, "UNBUILT (kickoff §4.3 item 3): GuardedPlan has no compose()"
        calls: list[int] = []

        def _spy(self: Any, *fragments: Any) -> Any:
            calls.append(len(fragments))
            return compose(self, *fragments)

        monkeypatch.setattr(governed.GuardedPlan, "compose", _spy)
        connection, env = substrate_world["connection"], substrate_world["env"]
        await seed_finding_governed(
            connection,
            row_id="gwaudit",
            number=612,
            owner_principal="bob",
            owner_agent="ag_b1",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        handle, _calls = store_handle(connection, url=env.url)
        before = await _audit_rows(connection)
        await governed.guarded_write(
            admin("carol", "ag_c1"),
            pdp.Action.WRITE,
            table=FINDING_TABLE,
            row_id="gwaudit",
            set_fragment="body = 'admin-touched'",
            audit=substrate_world["audit"],
            store=handle,
        )
        assert calls == [1], f"guarded_write must attach its audit via ONE compose() call, saw {calls}"
        assert await _audit_rows(connection) == before + 1


def _audit_statements(fragments: Any) -> int:
    return sum(
        1
        for fragment in fragments
        for statement in fragment.statements
        if "type::record('audit'" in statement.replace('"', "'")
    )


class TestAuthorizeGuardedProjectsTheLedgersColumnsInOneRead:
    """Kickoff §4.3 item 1: ``authorize_guarded(..., projection=(…))`` returns the pre-read row WITH the
    ledger's extra columns — so the ledger's own pre-read is DELETED (ONE read, no second TOCTOU window
    between two reads of the same row). Default ``()`` keeps memory/comms byte-identical."""

    async def test_a_projection_rides_the_single_governed_pre_read(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD (no ``projection``). ``projection=('status', 'provenance')`` ⇒ the plan's
        ``pre_read_row`` carries the seeded ``status`` AND the row ``id`` (so ``resource_from_row`` can
        derive the table), in EXACTLY ONE acquire of the injected handle."""
        _require_keyword(governed.authorize_guarded, "projection", "kickoff §4.3 item 1")
        connection, env = substrate_world["connection"], substrate_world["env"]
        await seed_finding_governed(
            connection,
            row_id="projected",
            number=620,
            owner_principal="alice",
            owner_agent="ag_a1",
            scope=_KEEP_AB,
            status="acknowledged",
        )
        handle, calls = store_handle(connection, url=env.url)
        authorize_guarded: Any = governed.authorize_guarded  # the unbuilt keyword — typecheck-safe at HEAD
        plan = await authorize_guarded(
            member("bob", "ag_b1", frozenset({_KEEP_AB})),
            pdp.Action.WRITE,
            table=FINDING_TABLE,
            row_id="projected",
            audit=None,
            store=handle,
            projection=("status", "provenance"),
        )
        row = plan.pre_read_row or {}
        assert row.get("status") == "acknowledged", row
        assert "provenance" in row, row
        assert str(getattr(row.get("id"), "table_name", "")) == FINDING_TABLE, row
        assert calls["acquire"] == 1, (
            f"the projection took {calls['acquire']} acquires — ONE read is the rule"
        )

    async def test_the_default_projection_reads_only_the_governed_columns(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD (the pre-read carries no ``id``). Default ``projection=()``: the pre-read row's
        keys are ⊆ ``{id, owner_principal, owner_agent, scope}`` (memory/comms byte-identical beyond the
        ``id`` the table derivation needs) and it DOES carry the id."""
        connection, env = substrate_world["connection"], substrate_world["env"]
        await seed_finding_governed(
            connection,
            row_id="plainread",
            number=621,
            owner_principal="alice",
            owner_agent="ag_a1",
            scope=pdp.SCOPE_SERVER,
        )
        handle, _calls = store_handle(connection, url=env.url)
        plan = await governed.authorize_guarded(
            member("alice", "ag_a1", frozenset()),
            pdp.Action.WRITE,
            table=FINDING_TABLE,
            row_id="plainread",
            audit=None,
            store=handle,
        )
        row = plan.pre_read_row or {}
        assert set(row) <= {"id", "owner_principal", "owner_agent", "scope"}, sorted(row)
        assert "id" in row, (
            "the governed pre-read must project the row id (resource_from_row derives the table)"
        )


# =========================================================================== #
# #429 — the guarded_write SET_SCOPE and DELETE branches, positive-controlled.
# =========================================================================== #


class TestSetScopeBranchIsExercised:
    """#429 (kickoff §11 row) — SET_SCOPE: the exact creator pair ∧ a GRANTABLE target (member); admin
    any row, AUDITED. ``target_scope=`` threads into BOTH the Python gate and the in-store guard (at HEAD
    neither receives it, so the member branch is ``NoRows`` for every target — the branch is DEAD)."""

    async def _set_scope(self, world: dict[str, Any], subject: Any, row_id: str, target: str) -> None:
        _require_keyword(governed.guarded_write, "target_scope", "#429 / kickoff §5 set_scope")
        _require_keyword(governed.guarded_write, "params", "#429 — the set fragment's bound target")
        handle, calls = store_handle(world["connection"], url=world["env"].url)
        guarded_write: Any = governed.guarded_write  # the unbuilt keywords — typecheck-safe at HEAD
        await guarded_write(
            subject,
            pdp.Action.SET_SCOPE,
            table=FINDING_TABLE,
            row_id=row_id,
            set_fragment="scope = $new_scope",
            params={"new_scope": target},
            target_scope=target,
            audit=world["audit"],
            store=handle,
        )
        assert calls["acquire"] >= 1

    async def test_the_owner_moves_its_row_to_a_keep_it_is_householded_in_unaudited(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD. alice's own private row → ``keep:A`` (hers): moved, +0 audit."""
        connection = substrate_world["connection"]
        await seed_finding_governed(
            connection,
            row_id="ss_owner",
            number=701,
            owner_principal="alice",
            owner_agent="ag_a1",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        before = await _audit_rows(connection)
        await self._set_scope(
            substrate_world, member("alice", "ag_a1", frozenset({_KEEP_A})), "ss_owner", _KEEP_A
        )
        assert (await finding_row(connection, "ss_owner"))["scope"] == _KEEP_A
        assert await _audit_rows(connection) == before

    async def test_a_non_owner_household_member_may_not_re_scope(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD (keyword absent). Bob is in ``keep:AB`` (WRITE-able) but NOT the creator:
        SET_SCOPE denies (authz §4.3 — a member may not re-scope a row it doesn't own); row unchanged."""
        connection = substrate_world["connection"]
        await seed_finding_governed(
            connection,
            row_id="ss_member",
            number=702,
            owner_principal="alice",
            owner_agent="ag_a1",
            scope=_KEEP_AB,
        )
        with pytest.raises(governed.GovernedDenied):
            await self._set_scope(
                substrate_world, member("bob", "ag_b1", frozenset({_KEEP_AB, _KEEP_B})), "ss_member", _KEEP_B
            )
        assert (await finding_row(connection, "ss_member"))["scope"] == _KEEP_AB

    async def test_the_owner_may_not_move_its_row_to_a_keep_it_is_not_householded_in(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD (keyword absent). The grantability leg: alice → ``keep:B`` (bob's) denies."""
        connection = substrate_world["connection"]
        await seed_finding_governed(
            connection,
            row_id="ss_grant",
            number=703,
            owner_principal="alice",
            owner_agent="ag_a1",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        with pytest.raises(governed.GovernedDenied):
            await self._set_scope(
                substrate_world, member("alice", "ag_a1", frozenset({_KEEP_A})), "ss_grant", _KEEP_B
            )
        assert (await finding_row(connection, "ss_grant"))["scope"] == pdp.SCOPE_PRINCIPAL_PRIVATE

    async def test_an_admin_re_scopes_a_foreign_row_and_is_audited(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD. The admin control: carol moves bob's private row → ``keep:AB``: moved, +1 audit
        (a bypass a member could not make). Proves the branch can SUCCEED under audit."""
        connection = substrate_world["connection"]
        await seed_finding_governed(
            connection,
            row_id="ss_admin",
            number=704,
            owner_principal="bob",
            owner_agent="ag_b1",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        before = await _audit_rows(connection)
        await self._set_scope(substrate_world, admin("carol", "ag_c1"), "ss_admin", _KEEP_AB)
        assert (await finding_row(connection, "ss_admin"))["scope"] == _KEEP_AB
        assert await _audit_rows(connection) == before + 1


class TestDeleteBranchIsExercised:
    """#429 — the DELETE branch on a ``finding`` fixture row (no served delete verb on the ledger —
    kickoff §5 table; 64d-ii owns a served delete). GREEN at HEAD (the branch exists, it was merely
    unexercised) — mutation-proven in the report (drop the ``RETURN BEFORE`` guard / make DELETE
    scope-dependent ⇒ these red)."""

    async def _delete(self, world: dict[str, Any], subject: Any, row_id: str) -> None:
        handle, _calls = store_handle(world["connection"], url=world["env"].url)
        await governed.guarded_write(
            subject,
            pdp.Action.DELETE,
            table=FINDING_TABLE,
            row_id=row_id,
            set_fragment=None,
            audit=world["audit"],
            store=handle,
        )

    async def test_the_owner_deletes_its_keep_row_after_leaving_the_keep(
        self, substrate_world: dict[str, Any]
    ) -> None:
        """D4(a) scope-INDEPENDENCE: alice's row sits in ``keep:A`` but alice's Subject no longer sees
        ``keep:A`` (she left) — DELETE is the exact owner pair, any scope ⇒ the row is gone, +0 audit."""
        connection = substrate_world["connection"]
        await seed_finding_governed(
            connection,
            row_id="del_owner",
            number=801,
            owner_principal="alice",
            owner_agent="ag_a1",
            scope=_KEEP_A,
        )
        before = await _audit_rows(connection)
        await self._delete(substrate_world, member("alice", "ag_a1", frozenset()), "del_owner")
        assert await run(connection, "SELECT VALUE id FROM type::record('finding', 'del_owner')") == []
        assert await _audit_rows(connection) == before

    async def test_a_household_non_owner_may_not_delete(self, substrate_world: dict[str, Any]) -> None:
        """Bob can WRITE alice's ``keep:AB`` row but NOT delete it (members correct, they do not vanish
        each other's work — authz §4): denied, row intact."""
        connection = substrate_world["connection"]
        await seed_finding_governed(
            connection,
            row_id="del_member",
            number=802,
            owner_principal="alice",
            owner_agent="ag_a1",
            scope=_KEEP_AB,
        )
        with pytest.raises(governed.GovernedDenied):
            await self._delete(substrate_world, member("bob", "ag_b1", frozenset({_KEEP_AB})), "del_member")
        assert (await finding_row(connection, "del_member"))["scope"] == _KEEP_AB

    async def test_an_admin_delete_of_a_foreign_row_is_audited(self, substrate_world: dict[str, Any]) -> None:
        """The admin control: carol deletes bob's row ⇒ gone, +1 audit."""
        connection = substrate_world["connection"]
        await seed_finding_governed(
            connection,
            row_id="del_admin",
            number=803,
            owner_principal="bob",
            owner_agent="ag_b1",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        before = await _audit_rows(connection)
        await self._delete(substrate_world, admin("carol", "ag_c1"), "del_admin")
        assert await run(connection, "SELECT VALUE id FROM type::record('finding', 'del_admin')") == []
        assert await _audit_rows(connection) == before + 1


# =========================================================================== #
# F-9 — the ledger's own StoreHandle / AuditStore accessors.
# =========================================================================== #


class TestTheFindingLedgerExposesItsDriverAndAuditSink:
    """F-9 (kickoff §1): 64 adds the accessor the ``StoreHandle`` docstring promises — the SAME driver
    callables the ledger's own ``_query`` hands the retry driver (ONE IMPLEMENTATION: a composed guarded
    write borrows the ledger's real lifecycle), plus the audit sink an admin bypass composes."""

    def _ledger(self) -> Any:
        from loremaster.findings import FindingLedger  # noqa: PLC0415

        return FindingLedger(
            url="ws://127.0.0.1:18000/rpc",
            namespace="lore_test",
            database="accessor_probe",
            user="root",
            password=SecretStr("unused"),
        )

    def test_the_handle_is_wired_to_the_ledgers_own_driver(self) -> None:
        """⚠ RED at HEAD (no ``handle``)."""
        from loremaster.findings import FindingLedger  # noqa: PLC0415

        assert isinstance(inspect.getattr_static(FindingLedger, "handle", None), property), (
            "UNBUILT (kickoff F-9): FindingLedger has no `handle` property"
        )
        ledger = self._ledger()
        handle = ledger.handle
        assert isinstance(handle, StoreHandle)
        assert handle.url == ledger._url  # noqa: SLF001
        assert getattr(handle.acquire, "__func__", None) is FindingLedger._ensure_connection  # noqa: SLF001
        assert getattr(handle.drop, "__func__", None) is FindingLedger._drop_connection  # noqa: SLF001

    def test_the_audit_sink_is_built_from_the_ledgers_own_wiring(self) -> None:
        """⚠ RED at HEAD (no ``audit_store``)."""
        from loremaster.audit import AuditStore  # noqa: PLC0415
        from loremaster.findings import FindingLedger  # noqa: PLC0415

        assert isinstance(inspect.getattr_static(FindingLedger, "audit_store", None), property), (
            "UNBUILT (kickoff §4.3 / F-7): FindingLedger has no `audit_store` property"
        )
        sink = self._ledger().audit_store
        assert isinstance(sink, AuditStore)
        assert sink._database == "accessor_probe"  # noqa: SLF001
