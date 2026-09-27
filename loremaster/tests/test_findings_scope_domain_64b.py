"""Contract r2 — packet 64b-i: the scope DOMAIN, ∀ writers (packet-64 amendment 8 ``53563e7`` §2 — MP-12, the
NEW DOOR ``REPORT-adversary-64b.md`` probed: an ADMIN ``set_scope`` stored ``banana``, a dangling ``keep:``,
and the shared hostile text VERBATIM). Authored by ``contract-64b-r2`` (Opus 5.5 — contract tests ONLY).

THE RULING: kickoff §5's "admin any (audited)" means any ROW, never any STRING. ``scope`` has a DOMAIN —
``{principal-private, agent-private, server} ∪ keep:<id of a keep that EXISTS at write time>`` — enforced ∀
writers by ONE predicate in ``lorerunes.pdp`` (``scope_shape_ok`` — the SHAPE, stdlib, no store) + ONE keep
existence read in the substrate for a ``keep:`` target. Admin bypasses only the HOUSEHOLD clause. An
out-of-domain value is a typed teaching refusal, byte-inert, +0 audit rows. The STATE leg is the F5
classifier's UNIVERSAL scope leg (amendment 9 §2 (b)) — NOT a store ASSERT: amendment 9 WITHDREW amendment
8's "Backstop at the STATE" ASSERT (63a design §4.1 stands: a populated table's ASSERT write-poisons every
batch UPDATE over a legacy row — the DD-3.c class).

WHAT IS PINNED (each class names the leg):
- the SHAPE predicate: its accept/refuse corpus, and that ``Resource`` validation ROUTES THROUGH it (proven
  by MUTATION, both directions — ONE shape predicate, never ``_is_valid_scope`` beside a second copy);
- the STATE leg: ∀ observed governed write, the LANDED scope passes the ONE shape predicate, regardless of
  the entry it classifies under (generated over the refusal corpus × {label, exempt} × {created, updated},
  with CONTROLs: in-domain classifies; a legacy row whose scope the write never touched classifies), routed
  through the ONE predicate (by mutation, both directions);
- ∀ finding scope WRITER × ∀ out-of-domain kind: member ``report``/``set_scope`` and admin ``set_scope``
  (caller-supplied), plus the three STORE-DERIVED writers (a member ``report``'s default, the finding
  migrate, the calibration system writer) against a FORGED project keep — refused, byte-inert, +0 audit;
  CONTROL: a real keep lands;
- the writer set's COMPLETENESS: every production site that writes a finding's ``scope`` is a listed writer.

DUAL (r2 → am-9): the r2 draft of this file pinned the ASSERT (a reader-aligned three-way store/shape/
``Resource`` alignment and a dirty-store write-poison KNOWN BOUND) — DROPPED DELIBERATELY with the ASSERT
(amendment 9 FK-r2-2 ERRATUM on am-8 §2); no P2 ``_ConstraintSpec`` gains a ``scope`` exemption.

STORE LAW (cited): ``docs/reference/surrealdb-31-capabilities.md`` §1.4 (a narrowing ASSERT converges schema,
never data — why no ASSERT backs this domain). Live TEST store ``:18000`` (NEVER :18500); per-test databases,
reaped.
"""

from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from _governed_contract import (
    ExemptToken,
    ObservedEffect,
    ObservedWrite,
    RowDelta,
    SchemaDelta,
    TreeMutationSite,
    TreeWriteAllowlistEntry,
    classify_tree_observed_write,
    governed_populations,
    governed_table_raw_mutation_sites_in_tree,
    observe_governed_table_writes,
    patch_shared_object_everywhere,
)
from _governed_contract_64 import (
    FINDING_TABLE,
    HOSTILE_FORGED_LINE_START,
    HOSTILE_FREE_TEXT,
    OUT_OF_DOMAIN_SCOPES,
    FindingWorld,
    finding_world,
    new_row_id,
)
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database
from surrealdb import RecordID

import lorerunes as pdp
from loremaster import governed

if TYPE_CHECKING:
    from lorerunes.pdp import scope_shape_ok

    # 64b-i's RULED, not-yet-built symbol this file pins — a TYPED CALL (amendment 8 §5 MP-9 / §2: the ONE
    # shape
    # predicate, ``(value: str) -> bool``). A permanent signature pin; until the build lands it, a mypy error
    # OWNED by bound `packet-64b-i-contract` (#461). Runtime-inert.
    def _ruled_64b_i_scope_shape(value: str) -> None:
        """amendment 8 §2 — THE shape of the scope domain (stdlib, no store): ``(value) -> bool``."""
        accepted: bool = scope_shape_ok(value)
        assert accepted in (True, False)


_REPO_ROOT = Path(__file__).resolve().parents[2]

#: SHAPE-legal scopes every correct ``scope_shape_ok`` must ACCEPT (the fixed three + keep ids of the two
#: shapes
#: the fleet mints: a ULID (``KeepStore``) and the lower-case slugs the fixtures and the project key use).
MUST_ACCEPT = (
    pdp.SCOPE_PRINCIPAL_PRIVATE,
    pdp.SCOPE_AGENT_PRIVATE,
    pdp.SCOPE_SERVER,
    "keep:01JB6Q8V0Z6X3K9M2N4P5R7S8T",
    "keep:keepalpha",
    "keep:some_project",
    "keep:a-long-ulid-id",  # a HYPHENATED id — HEAD's own PDP pin accepts it (see the alignment pin below)
)
#: SHAPE-illegal values every correct ``scope_shape_ok`` must REFUSE: non-scopes, an empty keep id, and keep
#: ids
#: carrying whitespace / newline / backtick / a colon / a row-shaped forgery (the charset half).
MUST_REFUSE = (
    "",
    "banana",
    "SERVER",
    " server",
    "server ",
    "keep:",
    "keep:a b",
    "keep:a\nb",
    "keep:a`b",
    "keep:a:b",
    HOSTILE_FREE_TEXT,
    f"keep:{HOSTILE_FREE_TEXT}",
)


#: HEAD's two PDP scope pins whose parametrize lists are the old world's ruled accept / reject sets.
_PDP_CORE_SCOPE_PINS = (
    "test_resource_accepts_every_valid_scope",
    "test_resource_rejects_a_scope_outside_the_domain",
)


def _shape_predicate() -> Any:
    """THE shape predicate, read off its ruled home ``lorerunes.pdp`` (an absent symbol is a teaching RED)."""
    from lorerunes import pdp as pdp_module  # noqa: PLC0415 - the ruled home module

    predicate = vars(pdp_module).get("scope_shape_ok")
    assert callable(predicate), "UNBUILT (amendment 8 §2): lorerunes.pdp.scope_shape_ok does not exist"
    return predicate


def _resource_constructs(scope: str) -> bool:
    try:
        pdp.Resource(table=FINDING_TABLE, owner_principal="alice", owner_agent="ag_a1", scope=scope)
    except ValueError:
        return False
    return True


# =========================================================================== #
# The ONE shape predicate.
# =========================================================================== #


class TestTheScopeShapeIsOnePredicate:
    """amendment 8 §2: ``lorerunes.pdp.scope_shape_ok(value)`` is THE shape of the domain (stdlib, no store).
    ``Resource`` already validates a scope (``_is_valid_scope``) — a SECOND shape predicate beside it is the
    #102 clone the ONE-IMPLEMENTATION law forbids, so ``Resource`` must ROUTE THROUGH it (proven by
    #mutation)."""

    def test_the_corpus(self) -> None:
        """⚠ RED at HEAD (``scope_shape_ok`` absent)."""
        predicate = _shape_predicate()
        wrong = [value for value in MUST_ACCEPT if predicate(value) is not True]
        wrong += [value for value in MUST_REFUSE if predicate(value) is not False]
        assert not wrong, f"scope_shape_ok misjudges: {wrong!r}"

    def test_resource_validation_routes_through_the_predicate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """⚠ RED at HEAD. PROVE SHARING BY MUTATION: rebinding THE predicate (by identity, every module-level
        binding) to refuse everything makes ``Resource(scope='server')`` refuse; rebinding it to accept
        everything makes ``Resource(scope='banana')`` construct. A ``Resource`` with a private shape check
        keeps working — the private copy this pin names."""
        predicate = _shape_predicate()
        assert _resource_constructs(pdp.SCOPE_SERVER) and not _resource_constructs("banana"), "fixture"
        with monkeypatch.context() as scoped:
            patch_shared_object_everywhere(
                scoped, "scope_shape_ok", predicate, lambda _value: False, expect_in=("lorerunes.pdp",)
            )
            assert not _resource_constructs(pdp.SCOPE_SERVER), (
                "Resource accepted 'server' with THE shape predicate refusing everything — its validation "
                "is a "
                "private copy (or a binding the identity sweep cannot reach)"
            )
        with monkeypatch.context() as scoped:
            patch_shared_object_everywhere(
                scoped, "scope_shape_ok", predicate, lambda _value: True, expect_in=("lorerunes.pdp",)
            )
            assert _resource_constructs("banana"), (
                "Resource refused 'banana' with THE shape predicate accepting everything — a private copy"
            )

    def test_the_shape_agrees_with_every_scope_the_pdp_core_pins_rule_on(self) -> None:
        """⚠ RED at HEAD (no predicate). ONE ORACLE, both ways: HEAD's own PDP pins
        (``lorerunes/tests/test_pdp_core.py`` — ``test_resource_accepts_every_valid_scope`` /
        ``test_resource_rejects_a_scope_outside_the_domain``, the Fork D rider "keep:<non-empty>") are READ
        by AST, never re-typed: every scope they accept passes ``scope_shape_ok``, every one they reject
        fails it. DUAL (r2 → SAT): the r2 reference's keep-id charset refused a HYPHEN
        (``keep:a-long-ulid-id``) — a narrowing the old world never made, caught only by the full SAT; this
        pin makes the old world's accept-set a checked floor instead of a fixture someone must remember."""
        predicate = _shape_predicate()
        source = (_REPO_ROOT / "lorerunes" / "tests" / "test_pdp_core.py").read_text(encoding="utf-8")
        ruled: dict[str, list[str]] = {}
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.FunctionDef) or node.name not in _PDP_CORE_SCOPE_PINS:
                continue
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and len(decorator.args) == 2:
                    values = ast.literal_eval(decorator.args[1])
                    ruled[node.name] = [value for value in values if isinstance(value, str)]
        assert set(ruled) == set(_PDP_CORE_SCOPE_PINS), (
            f"non-vacuity: the pdp_core scope pins moved: {sorted(ruled)}"
        )
        refused = [v for v in ruled["test_resource_accepts_every_valid_scope"] if not predicate(v)]
        accepted = [v for v in ruled["test_resource_rejects_a_scope_outside_the_domain"] if predicate(v)]
        assert not refused, f"scope_shape_ok REFUSES scopes HEAD's PDP pin accepts (a narrowing): {refused}"
        assert not accepted, f"scope_shape_ok ACCEPTS scopes HEAD's PDP pin rejects (a widening): {accepted}"

    def test_the_predicate_is_pure_stdlib(self) -> None:
        """⚠ RED at HEAD. ``lorerunes`` depends on nothing but the stdlib (CLAUDE.md ``lorerunes`` law): the
        predicate's module imports no sibling and the function opens no store."""
        predicate = _shape_predicate()
        source = inspect.getsource(predicate)
        assert "await" not in source and "run_query" not in source, "the SHAPE predicate touches a store"
        module = inspect.getmodule(predicate)
        assert module is not None and module.__name__.startswith("lorerunes"), module


# =========================================================================== #
# The STATE leg — the F5 classifier's UNIVERSAL scope-domain leg (amendment 9 §2 (b); ASSERT WITHDRAWN).
# =========================================================================== #

#: The synthetic site both channel entries below attribute to (a pure-unit classifier input; no tree scan).
_PROBE_SITE = TreeMutationSite(
    file="loremaster/loremaster/findings.py", function="_scope_leg_probe", verb="UPDATE"
)
_PROBE_LABEL = "scope_leg_probe"
_PROBE_EXEMPT = "scope-leg-probe"
_PROBE_GOLDEN = "UPDATE finding SET scope = $scope"


def _permissive(_effect: ObservedEffect) -> bool:
    """An entry effect predicate that admits EVERY effect — so the ONLY thing that can refuse the probe write
    is the universal leg (the discrimination the CONTROLs below prove)."""
    return True


_PROBE_ALLOWLIST = (
    TreeWriteAllowlistEntry(
        site=_PROBE_SITE, justification="probe", pin="probe", frames=(_PROBE_LABEL,), effect=_permissive
    ),
    TreeWriteAllowlistEntry(
        site=_PROBE_SITE,
        justification="probe",
        pin="probe",
        frames=(),
        exempt_name=_PROBE_EXEMPT,
        statement=_PROBE_GOLDEN,
        effect=_permissive,
    ),
)

_EMPTY_SCHEMA_DELTA = SchemaDelta(added=frozenset(), removed=frozenset(), changed=frozenset())
_ABSENT = (
    object()
)  # the landed row carries NO scope key (a None landing — rider (ii): not this leg's business)


def _landing(kind: str, scope: object) -> RowDelta:
    """One row delta that LANDS ``scope`` (``_ABSENT`` ⟹ the row's after-image has no scope key)."""
    before = None if kind == "created" else {"id": "f1", "scope": pdp.SCOPE_SERVER, "subject": "t"}
    after: dict[str, Any] = {"id": "f1", "subject": "t"}
    if scope is not _ABSENT:
        after["scope"] = scope
    changed = frozenset(after) - {"id"} if kind == "created" else frozenset({"scope"})
    return RowDelta(id="f1", kind=kind, changed_columns=changed, before=before, after=after)


def _observed(channel: str, delta: RowDelta, **effect_fields: Any) -> ObservedWrite:
    """A pure-unit observed write on ``channel``; ``effect_fields`` adds the observer-read fields (the built
    ``resolved_keep_scopes`` — passed ONLY by the pins that exercise existence, so the shape pins construct
    at HEAD)."""
    effect = ObservedEffect(row_deltas=(delta,), schema_delta=_EMPTY_SCHEMA_DELTA, **effect_fields)
    if channel == "label":
        return ObservedWrite(label=_PROBE_LABEL, statement=_PROBE_GOLDEN, effect=effect)
    token = ExemptToken(
        name=_PROBE_EXEMPT, statement=_PROBE_GOLDEN, origin=(_PROBE_SITE.file, _PROBE_SITE.function)
    )
    return ObservedWrite(label=None, exempt=token, statement=_PROBE_GOLDEN, effect=effect)


_CHANNELS = ("label", "exempt")
_KINDS = ("created", "updated")
#: the live probe's keep row id (it EXISTS) and a well-formed keep scope that names NO keep (rider (iii)).
_LIVE_PRESENT_KEEP = "present"
_LIVE_MISSING_KEEP_SCOPE = "keep:absent"


def _governed_population_names() -> list[str]:
    """∀ governed populations (DERIVED from the emitted schema — 63c's and 64's alike, am-35 §6)."""
    from _enforced_relations_scaffold import emitted_schema_ddl  # noqa: PLC0415

    return sorted(governed_populations(emitted_ddl=emitted_schema_ddl()))


class TestTheClassifierRefusesAnOutOfDomainLandedScope:
    """packet-64 am-9 §2 (b), CONCURRED by 63c am-35 §6 with four riders: an F5 L2b leg of the ONE shared
    classifier (``classify_tree_observed_write``; §HELD Part A item A6 — the 64-side wrapper fallback is
    REFUSED as copy #2): ∀ observed governed write, whatever entry attributes it, ``scope is not None ⇒ scope
    ∈ DOMAIN`` — DOMAIN = THE ``lorerunes.pdp.scope_shape_ok`` shape AND, for a ``keep:`` scope, a keep row
    that RESOLVES (the observer's in-lock read, carried as ``effect.resolved_keep_scopes``).

    GENERATED: the SHAPE half ∀ value in the refusal corpus (``MUST_REFUSE`` ∪ ``OUT_OF_DOMAIN_SCOPES``
    filtered by the predicate itself) × ∀ channel × ∀ landing kind, under entries whose effect predicate
    admits EVERYTHING (so only the leg can refuse); the EXISTENCE half ∀ channel × kind; the LIVE leg ∀
    governed population (derived) through the real observer on ``:18000``. CONTROLS both directions (rider
    (iii)): an in-domain scope classifies; a None landing classifies (rider (ii) — the per-entry predicate's
    business); a legacy row the write did not re-scope classifies (63a §4.1 — no write-poison inside the
    classifier). BOUND (rider (i), stated in the leg's docstring): a keep deleted between the write and the
    observer's after-read is a FALSE UNCLASSIFIED — loud, never silent."""

    @staticmethod
    def _refusal_corpus() -> list[str]:
        predicate = _shape_predicate()
        return list(dict.fromkeys(v for v in (*MUST_REFUSE, *OUT_OF_DOMAIN_SCOPES) if not predicate(v)))

    @pytest.mark.parametrize("channel", _CHANNELS)
    @pytest.mark.parametrize("kind", _KINDS)
    def test_an_out_of_shape_landed_scope_is_unclassified(self, channel: str, kind: str) -> None:
        """⚠ RED at HEAD (the classifier has no scope leg: every probe write classifies on its channel)."""
        classified = [
            value
            for value in self._refusal_corpus()
            if classify_tree_observed_write(_observed(channel, _landing(kind, value)), _PROBE_ALLOWLIST)
        ]
        assert not classified, (
            f"UNBUILT (packet-64 am-9 §2 (b) / 63c am-35 §6): the F5 classifier ATTRIBUTED a governed write "
            f"landing an out-of-shape scope on the {channel} channel ({kind}): {classified!r}"
        )

    @pytest.mark.parametrize("channel", _CHANNELS)
    @pytest.mark.parametrize("kind", _KINDS)
    def test_a_well_formed_scope_naming_a_missing_keep_is_unclassified(self, channel: str, kind: str) -> None:
        """⚠ RED at HEAD (no ``resolved_keep_scopes`` — the existence half is unbuilt). Rider (iii): the
        existence half has its OWN control — a SHAPE-legal ``keep:`` scope whose keep does not resolve is
        refused, and the SAME scope classifies when the observer resolved it."""
        missing = _observed(
            channel, _landing(kind, _LIVE_MISSING_KEEP_SCOPE), resolved_keep_scopes=frozenset()
        )
        present = _observed(
            channel,
            _landing(kind, _LIVE_MISSING_KEEP_SCOPE),
            resolved_keep_scopes=frozenset({_LIVE_MISSING_KEEP_SCOPE}),
        )
        assert _shape_predicate()(_LIVE_MISSING_KEEP_SCOPE), (
            "fixture: the missing-keep scope must be SHAPE-legal"
        )
        assert classify_tree_observed_write(present, _PROBE_ALLOWLIST), (
            "CONTROL: a resolved keep scope does not classify"
        )
        assert not classify_tree_observed_write(missing, _PROBE_ALLOWLIST), (
            "a well-formed keep scope naming NO keep row classified — the existence half is missing"
        )

    @pytest.mark.parametrize("channel", _CHANNELS)
    @pytest.mark.parametrize("kind", _KINDS)
    def test_CONTROL_an_in_domain_landed_scope_classifies(self, channel: str, kind: str) -> None:
        """CONTROL (the probe can SEE a classification): ∀ ``MUST_ACCEPT`` value the SAME probe write
        classifies (a hand-built effect carries no existence read, so keep scopes are judged on SHAPE here) —
        the refusals above are the leg's, not a broken probe entry."""
        refused = [
            value
            for value in MUST_ACCEPT
            if not classify_tree_observed_write(_observed(channel, _landing(kind, value)), _PROBE_ALLOWLIST)
        ]
        assert not refused, (
            f"an in-domain landed scope was refused on the {channel} channel ({kind}): {refused}"
        )

    @pytest.mark.parametrize("channel", _CHANNELS)
    @pytest.mark.parametrize("kind", _KINDS)
    @pytest.mark.parametrize("landed", ["none-value", "absent-key"])
    def test_CONTROL_a_none_landing_is_not_this_legs_business(
        self, channel: str, kind: str, landed: str
    ) -> None:
        """CONTROL — rider (ii): ``scope is not None ⇒ …``. A landed None (a legacy row the migrate has not
        reached; the ruled OWNERLESS register path) is adjudicated by the entry's own effect predicate, so
        the leg carries NO allowlist and never refuses it."""
        scope = None if landed == "none-value" else _ABSENT
        assert classify_tree_observed_write(_observed(channel, _landing(kind, scope)), _PROBE_ALLOWLIST), (
            f"the universal leg refused a None landing ({landed}) — rider (ii): not its business"
        )

    @pytest.mark.parametrize("channel", _CHANNELS)
    def test_CONTROL_a_legacy_row_whose_scope_is_untouched_classifies(self, channel: str) -> None:
        """CONTROL — the 63a §4.1 reason the ASSERT was withdrawn, kept true here: a row whose write does NOT
        land a scope (another column changed) is not examined, even when its CURRENT scope is out of domain.
        A leg over every after-image would re-create the DD-3.c write-poison inside the classifier."""
        delta = RowDelta(
            id="legacy",
            kind="updated",
            changed_columns=frozenset({"subject"}),
            before={"id": "legacy", "subject": "old", "scope": "banana"},
            after={"id": "legacy", "subject": "new", "scope": "banana"},
        )
        assert classify_tree_observed_write(_observed(channel, delta), _PROBE_ALLOWLIST), (
            "the scope leg refused a row whose scope the write never touched"
        )

    def test_the_leg_routes_through_the_one_shape_predicate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ONE IMPLEMENTATION (proven by MUTATION, both directions): rebinding THE predicate (by identity,
        every module-level binding — an aliased import moves too) to refuse everything makes an in-domain
        write UNCLASSIFIED; to accept everything makes an out-of-domain write classify. A classifier with a
        private shape copy keeps its verdicts (a private copy wearing the shared name)."""
        predicate = _shape_predicate()
        in_domain = _observed("label", _landing("updated", pdp.SCOPE_SERVER))
        out_of_domain = _observed("label", _landing("updated", "banana"))
        with monkeypatch.context() as scoped:
            patch_shared_object_everywhere(
                scoped, "scope_shape_ok", predicate, lambda _value: False, expect_in=("lorerunes.pdp",)
            )
            assert not classify_tree_observed_write(in_domain, _PROBE_ALLOWLIST), (
                "the classifier attributed 'server' with THE shape predicate refusing everything — its scope "
                "leg is a private copy (or absent)"
            )
        with monkeypatch.context() as scoped:
            patch_shared_object_everywhere(
                scoped, "scope_shape_ok", predicate, lambda _value: True, expect_in=("lorerunes.pdp",)
            )
            assert classify_tree_observed_write(out_of_domain, _PROBE_ALLOWLIST), (
                "the classifier refused 'banana' with THE shape predicate accepting everything — a "
                "private copy"
            )

    @pytest.mark.parametrize("table", _governed_population_names())
    async def test_live_every_governed_population_under_the_real_observer(self, table: str) -> None:
        """⚠ RED at HEAD (no leg; no in-lock existence read). ∀ governed population (DERIVED — 63c's agent /
        message / brief / memory and 64's finding / task alike), a REAL write observed by the F5 observer on
        ``:18000`` (a per-test database; the probe writes schemaless rows, since the observer and the leg are
        schema-agnostic): an existing keep scope and a fixed scope CLASSIFY; a well-formed keep scope naming
        NO keep and a non-scope are UNCLASSIFIED; and every observed effect CARRIES the observer's existence
        read (``resolved_keep_scopes`` is never None on an OBSERVED effect — the fail-safe the unit
        shape-only path relies on)."""
        cases = (
            (pdp.keep_scope(_LIVE_PRESENT_KEEP), True),
            (_LIVE_MISSING_KEEP_SCOPE, False),
            ("banana", False),
            (pdp.SCOPE_SERVER, True),
        )
        env = make_env(database=unique_database(), dim=8)
        connection = await connect_admin(env)
        try:
            await run(
                connection, f"CREATE type::record('keep', '{_LIVE_PRESENT_KEEP}') CONTENT {{ name: 'k' }}"
            )
            with observe_governed_table_writes(table) as writes:
                for index, (scope, _expected) in enumerate(cases):
                    with governed.write_guard(_PROBE_LABEL):
                        await run(
                            connection,
                            f"CREATE type::record('{table}', $id) CONTENT {{ scope: $scope }}",
                            {"id": f"probe{index}", "scope": scope},
                        )
            assert len(writes) == len(cases), (
                f"non-vacuity: {len(writes)} observed writes for {len(cases)} cases"
            )
            unread = [
                write for write in writes if getattr(write.effect, "resolved_keep_scopes", None) is None
            ]
            assert not unread, (
                "UNBUILT (63c am-35 §6 rider (i)): an OBSERVED effect carries no in-lock keep-existence read"
            )
            verdicts = {
                scope: classify_tree_observed_write(write, _PROBE_ALLOWLIST)
                for (scope, _expected), write in zip(cases, writes, strict=True)
            }
            assert verdicts == dict(cases), f"{table}: live verdicts {verdicts} != ruled {dict(cases)}"
        finally:
            await connection.close()
            await drop_database(env)


# =========================================================================== #
# ∀ writer × ∀ out-of-domain kind — the caller-supplied writers.
# =========================================================================== #

#: writer → (acting agent, the row's owner/scope seed or None for a CREATE, the call). Member writers act on
#: their OWN rows (the owner may re-scope); the admin acts on a FOREIGN row (the audited bypass).
_CALLER_WRITERS = ("member-report", "member-set_scope", "admin-set_scope")


async def _drive_writer(world: FindingWorld, writer: str, scope: str, number: int) -> None:
    if writer == "member-report":
        await world.findings(
            "ag-a1", action="report", subject=f"s{number}", body="", area="a", category="c", scope=scope
        )
    elif writer == "member-set_scope":
        await world.findings("ag-a1", action="set_scope", id_or_number=number, scope=scope)
    else:
        await world.findings("ag-c1", action="set_scope", id_or_number=number, scope=scope)


class TestEveryCallerSuppliedScopeWriterRefusesAnOutOfDomainValue:
    """MP-12 (amendment 8 §2 pins): ∀ caller-supplied writer × ∀ out-of-domain kind (a nonexistent keep —
    shape- legal, existence-illegal; a non-scope string; the hostile text; a keep-prefixed hostile id) ⇒
    refused (members: the ``GovernedDenied`` family, unchanged; admin: a ``ValueError``-family refusal NAMING
    the domain), the row byte-unchanged, ZERO new findings, ZERO audit rows, and the hostile value's forged
    row never reaches a LINE START of the served refusal. CONTROL: the same writer with a REAL keep it may
    target lands."""

    @pytest.mark.parametrize("writer", _CALLER_WRITERS)
    async def test_every_out_of_domain_kind(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, writer: str
    ) -> None:
        """⚠ RED at HEAD (no ``scope=`` / no capability=); on the r1 reference the ADMIN writer STORES all
        four."""
        async with finding_world(monkeypatch, tmp_path) as world:
            owner = "ag-b1" if writer == "admin-set_scope" else "ag-a1"
            violations: list[str] = []
            for index, (kind, value) in enumerate(sorted(OUT_OF_DOMAIN_SCOPES.items())):
                number = 9100 + index
                row_id = await world.seed(
                    row_id=new_row_id("dom"), number=number, owner=owner, scope_key="principal-private"
                )
                before = await world.row(row_id)
                audit_before = await world.audit_count()
                count_before = len(await run(world.admin_conn, f"SELECT VALUE id FROM {FINDING_TABLE}"))
                try:
                    await _drive_writer(world, writer, value, number)
                except (governed.GovernedDenied, ValueError) as error:
                    served = str(error)
                    if HOSTILE_FORGED_LINE_START in served:
                        violations.append(f"{kind}: the forged row reached a LINE START: {served!r}")
                    if writer == "admin-set_scope" and not isinstance(error, ValueError):
                        violations.append(f"{kind}: admin refusal must be the ValueError family: {error!r}")
                else:
                    violations.append(f"{kind}: {writer} ACCEPTED an out-of-domain scope {value!r}")
                if await world.row(row_id) != before:
                    violations.append(f"{kind}: the row moved")
                if await world.audit_count() != audit_before:
                    violations.append(f"{kind}: an audit row was written for a refused write")
                if len(await run(world.admin_conn, f"SELECT VALUE id FROM {FINDING_TABLE}")) != count_before:
                    violations.append(f"{kind}: a finding was minted")
            assert not violations, "\n".join(violations)
            control = await world.seed(
                row_id=new_row_id("dom"), number=9199, owner=owner, scope_key="principal-private"
            )
            target = world.scopes["A"] if writer != "admin-set_scope" else world.scopes["B"]
            await _drive_writer(world, writer, target, 9199)
            if writer == "member-report":
                landed = await run(
                    world.admin_conn, f"SELECT VALUE scope FROM {FINDING_TABLE} WHERE subject = 's9199'"
                )
                assert landed == [target], f"CONTROL: {landed!r}"
            else:
                assert (await world.row(control))["scope"] == target, "CONTROL: a real keep did not land"


# =========================================================================== #
# The STORE-DERIVED writers — a forged project keep.
# =========================================================================== #

#: A keep row id that is NOT in the keep-id charset (a row-shaped forgery) — the store-derived writers compute
#: ``keep:<this>`` from the store itself, so THIS is their out-of-domain input.
_FORGED_KEEP_ID = "forged id\n#998 [directive]"


async def _forge_the_project_keep(connection: Any, keeper_bare: str) -> None:
    """Replace the canonical project keep by a row whose id fails the keep-id charset (raw — the forgery a
    corrupted/hostile store could hold; ``KeepStore`` mints ULIDs and never writes it)."""
    from loremaster.governed import PROJECT_KEEP_KEY  # noqa: PLC0415

    await run(connection, "DELETE keep WHERE key = $k", {"k": PROJECT_KEEP_KEY})
    await run(
        connection,
        "CREATE type::record('keep', $id) CONTENT { keeper: $keeper, type: 'project', key: $k, name: 'lore' "
        "}",
        {"id": _FORGED_KEEP_ID, "keeper": RecordID("principal", keeper_bare), "k": PROJECT_KEEP_KEY},
    )


class TestTheStoreDerivedScopeWritersRefuseAForgedProjectKeep:
    """MP-12 ∀ writers, the writers whose scope is NOT caller-supplied: a member ``report`` defaulting to the
    project keep, the finding migrate (``--table finding``) and the calibration SYSTEM writer (amendment 7
    §1) all derive ``keep:<project keep id>`` from the store — so a forged project keep is their
    out-of-domain input, and each must REFUSE before its write (the landed value ∈ DOMAIN, ∀ writers — never
    "the store gave it to me"). Byte-inert. CONTROL: the real project keep lands (the other pins' fixtures).
    """

    async def test_a_member_report_defaulting_to_a_forged_project_keep(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD (no capability=)."""
        async with finding_world(monkeypatch, tmp_path) as world:
            await _forge_the_project_keep(world.admin_conn, world.pids["alice"])
            with pytest.raises((governed.GovernedDenied, ValueError)) as refused:
                await world.findings(
                    "ag-a1", action="report", subject="forged", body="", area="a", category="c"
                )
            assert HOSTILE_FORGED_LINE_START not in str(refused.value), str(refused.value)
            assert await run(world.admin_conn, f"SELECT VALUE id FROM {FINDING_TABLE}") == []

    async def test_the_finding_migrate_with_a_forged_project_keep(self) -> None:
        """⚠ RED at HEAD (the finding leg is unsupported — refused for the wrong reason, asserted below)."""
        from _governed_contract_64 import (  # noqa: PLC0415
            frozen_asserted_finding_ddl,
            seed_finding_legacy,
        )
        from test_findings_migrate_64b import _migrate_world, _upgrade_finding_schema  # noqa: PLC0415

        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            await seed_finding_legacy(world.connection, row_id="legacy_1", number=1)
            await _upgrade_finding_schema(world)
            await _forge_the_project_keep(world.connection, world.operator_bare)
            before = await run(world.connection, f"SELECT * FROM {FINDING_TABLE} ORDER BY id")
            try:
                result = await world.migrate()
            except (governed.GovernedDenied, ValueError) as error:
                assert HOSTILE_FORGED_LINE_START not in str(error), str(error)
            else:
                assert result.refused, f"the finding migrate stamped a forged project scope: {result!r}"
                assert "not supported" not in str(result.reason), (
                    "UNBUILT: the finding leg refused as unsupported, not on the forged scope: "
                    f"{result.reason!r}"
                )
                assert HOSTILE_FORGED_LINE_START not in str(result.reason), result.reason
            assert await run(world.connection, f"SELECT * FROM {FINDING_TABLE} ORDER BY id") == before

    async def test_the_system_writer_with_a_forged_project_keep(self) -> None:
        """⚠ RED at HEAD (``report_system`` absent)."""
        from test_findings_system_writer_64b import system_ledger_world  # noqa: PLC0415

        async with system_ledger_world(provision_project_keep=True) as world:
            await _forge_the_project_keep(world.connection, world.keeper_bare)
            report_system = getattr(world.ledger, "report_system", None)
            assert report_system is not None, "UNBUILT (amendment 7 §1): FindingLedger.report_system"
            with pytest.raises((governed.GovernedDenied, ValueError)) as refused:
                await world.file_drift()
            assert HOSTILE_FORGED_LINE_START not in str(refused.value), str(refused.value)
            assert await run(world.connection, f"SELECT VALUE id FROM {FINDING_TABLE}") == []


# =========================================================================== #
# The writer set is COMPLETE.
# =========================================================================== #

#: every production (file, function) that writes a finding's ``scope`` → the MP-12 writer(s) that drive it
#: above. ``set_scope`` rides ``governed.guarded_write`` (an interpolated table — no finding literal at L1,
#: #444), so it is listed by its own frame.
FINDING_SCOPE_WRITER_SITES: dict[tuple[str, str], str] = {
    ("loremaster/loremaster/findings.py", "_report_fragment"): "member-report · system-report (FK-7)",
    ("loremaster/loremaster/principals.py", "_migrate_finding_scope"): "the finding migrate",
    ("loremaster/loremaster/findings.py", "set_scope"): "member-set_scope · admin-set_scope",
}


def _function_literals(relative: str, function: str) -> list[str]:
    tree = ast.parse((_REPO_ROOT / relative).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == function:
            return [
                child.value
                for child in ast.walk(node)
                if isinstance(child, ast.Constant) and isinstance(child.value, str)
            ] + [
                "".join(str(part.value) for part in child.values if isinstance(part, ast.Constant))
                for child in ast.walk(node)
                if isinstance(child, ast.JoinedStr)
            ]
    return []


class TestTheScopeWriterSetIsComplete:
    """MP-12's reach (amendment 8 §2 "Reach: the writer set's completeness assertion"): every raw finding
    mutation site the whole-tree L1 scan DERIVES whose literals assign ``scope`` is a LISTED writer — a new
    writer of a finding's scope reds here until it joins the sweep above. Non-vacuity: ≥1 derived scope
    writer."""

    def test_every_derived_scope_writer_is_listed(self) -> None:
        """⚠ RED at HEAD (``_migrate_finding_scope`` absent; ``_report_fragment`` writes no scope)."""
        derived = {
            (site.file, site.function)
            for site in governed_table_raw_mutation_sites_in_tree(
                FINDING_TABLE, table_const_hint="FINDING_TABLE"
            )
        }
        scope_writers = {
            site
            for site in derived
            if any(re.search(r"\bscope\s*[:=]", text) for text in _function_literals(*site))
        }
        assert scope_writers, (
            "no derived finding mutation site writes scope — the completeness scan is vacuous"
        )
        unlisted = sorted(scope_writers - FINDING_SCOPE_WRITER_SITES.keys())
        assert not unlisted, f"finding scope writers NOT in the MP-12 sweep: {unlisted}"
        ghosts = sorted(
            site
            for site in FINDING_SCOPE_WRITER_SITES
            if site not in scope_writers and site[1] != "set_scope"
        )
        assert not ghosts, f"listed scope writers the tree does not derive (stale rows): {ghosts}"
