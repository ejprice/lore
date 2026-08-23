"""Contract — the packet-61b-w1 PDP CORE, the single-brain authorization engine
(``lorerunes``, stdlib-only). RED before the 61b-w1 build; authored by
``contract-61b-w1`` (session ``pkt61``).

WHAT THIS PINS (the PURE half — no store; the live-store ORACLE lives in
``loremaster/tests/test_pdp_oracle_61b.py``). Design authority:
``docs/design/2026-08-22-packet61-pdp-audit-rulings.md`` Forks A/B/C/D/G and
``docs/design/2026-08-21-lore-authorization-model.md`` §4/§5/§9. Store law (the emitter's
index behaviour, settled by finding #413 / ``scripts/probe_read_filter_61b.py``):
``docs/reference/surrealdb-31-capabilities.md`` §2.

THE MECHANISM (Fork A). A CLOSED predicate IR (a small typed algebra) with TWO TOTAL
interpreters walking ONE tree — ``to_surql()`` (the SurrealQL emitter) and ``matches()``
(the Python evaluator). ``authorize`` is DEFINED as
``authorize_filter(subject, action, resource.table).matches(resource)`` so the §5
equivalence (``authorize(s,a,row).allowed ≡ authorize_filter(s,a).matches(row)``) is TRUE
BY CONSTRUCTION; the residual risk (do ``to_surql`` and ``matches`` MEAN the same thing?)
moves entirely to the live-store oracle in the sibling file.

⚠⚠ THE ONE LOAD-BEARING CONTRACT DEVIATION FROM THE DESIGN (surfaced per brief-base §2,
NOT silently resolved). The design is INTERNALLY INCONSISTENT on how the admin audit
carve-out (Fork G / §9 — "admin canNOT delete or modify audit rows") identifies an
audit-table resource: Fork D FREEZES ``Resource`` at THREE fields
``(owner_principal, owner_agent, scope)`` with NO table identity, while Fork G says the
carve-out fires "for a Resource whose ``target_table``/type is ``audit``". An audit row
has NO owner/scope columns, so the carve-out is fundamentally a per-TABLE rule, and the
table MUST enter the PDP for a single-row ``authorize`` whose only inputs are
``(subject, action, resource)``. This contract RESOLVES the inconsistency as reading **B2**
(see ``REPORT-contract-61b-w1.md`` §Decisions-needed):
  * ``Resource`` carries a FOURTH field ``table`` (Fork D's 3 → 4; Fork G's own phrasing
    "a Resource whose target_table" anticipates it);
  * ``authorize_filter(subject, action, table)`` is 3-arg (§5 wrote it 2-arg — the table is
    needed so the carve-out picks ``NoRows`` for admin+mutating+audit and ``AllRows`` for
    admin+mutating+governed, with NO split-brain node whose ``to_surql`` and ``matches``
    could disagree);
  * ``authorize(subject, action, resource)`` STAYS 3-arg (matches §5), threading the table
    from ``resource.table``.
COUNTERMAND (a one-signature edit, like FR-4 D1): reading **B1** keeps ``Resource`` at
Fork D's 3 fields and passes ``table`` as a SEPARATE arg to both functions
(``authorize(subject, action, table, resource)``). If the operator/lead prefers B1, this
contract needs the ``Resource`` field dropped + the ``authorize`` signature widened. Every
other pin is independent of the choice.

⚠ B2 was CONFIRMED by lead-61 (§Fork-A/D addendum). It makes the equivalence STRUCTURAL:
``authorize(s,a,r) == authorize_filter(s,a,r.table).matches(r)`` uses the SAME table by
construction. **FORWARD-NOTE (#415, a comment — NOT a 61b pin):** at packets 63/64,
``Resource.table`` is DERIVED from the governed row's id (the ``table`` of ``table:xyz``),
NEVER a caller-supplied field — a forged ``table`` would bypass the audit carve-out
(anti-injection, §3.2.2). 61b defines the shape; 63/64 own that derivation.

⚠ D4(b) SECURITY REFINEMENT (lead-61 §Fork-C addendum): ``SET_SCOPE`` is NOT bare
``owner=me`` — it is ``owner=me AND the TARGET scope is GRANTABLE by the subject``
(§3.2.3 scope-on-write validation / §4.3). A member may re-scope THEIR OWN row to a keep
ONLY IF they are a member of that keep; freely to their private scopes + server. So
``authorize``/``authorize_filter`` take a keyword-only ``target_scope`` (the D1-confirmed
3-POSITIONAL-arg signature is preserved; ``target_scope`` defaults ``None`` and is required
only for ``SET_SCOPE``). A ``None`` target grants nothing (SET_SCOPE with no target denies).

RED DISCIPLINE (#133). The PDP surface does not exist at authorship HEAD; ``_pdp()`` loads
it via ``importlib`` + ``getattr`` and ``pytest.fail``s CLEANLY when absent, so this file
COLLECTS and TYPECHECKS clean and every behavioural pin is RED for the RIGHT reason (no
ImportError at collection, no mypy-RED static import of an unbuilt symbol).

FIXTURES MUST DISCRIMINATE (PKT-28 C1). No factory defaults ``role`` / ``scope`` /
``agent_id`` — every call CHOOSES (the ``_brief()``-monoculture trap). The hostile row set
carries ≥2 principals × ≥2 agents each so a SIBLING-agent refusal (reading 1) is
distinguishable from a principal-wide one (reading 2).
"""

from __future__ import annotations

import ast
import importlib
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

# --------------------------------------------------------------------------- #
# RED-safe loader (finding #133): no static import of the unbuilt PDP surface.
# --------------------------------------------------------------------------- #

_PACKAGE = "lorerunes"

# The full public PDP surface this wave must add to ``lorerunes`` (Fork B). Named here so a
# PARTIAL build (some symbols, not all) fails LOUD with the exact missing set, rather than
# an AttributeError deep in one test.
_REQUIRED_SYMBOLS = (
    # the action taxonomy (Fork C) + value objects (Fork D) + the decision
    "Action",
    "Subject",
    "Resource",
    "Decision",
    # the predicate IR (Fork A) — the closed algebra
    "Predicate",
    "ScopeEq",
    "OwnerPrincipalEq",
    "OwnerAgentEq",
    "ScopeInKeeps",
    "And",
    "Or",
    "AllRows",
    "NoRows",
    # the two entry points (Fork A)
    "authorize",
    "authorize_filter",
    # the shared vocabulary the PDP owns (homed in lorerunes — the scopes.py precedent)
    "SCOPE_AGENT_PRIVATE",
    "SCOPE_PRINCIPAL_PRIVATE",
    "SCOPE_SERVER",
    "KEEP_SCOPE_PREFIX",
    "keep_scope",
    "PRINCIPAL_ROLE_MEMBER",
    "PRINCIPAL_ROLE_ADMIN",
    "PRINCIPAL_ROLES",
    "AUDIT_TABLE",
    "PRINCIPAL_TABLE",  # R4 — the emitter's record-link table name, homed here
    "AGENT_TABLE",
)


def _pdp() -> Any:
    """Return the ``lorerunes`` PDP surface once 61b-w1 builds it, else ``pytest.fail``.

    Reads via ``importlib`` + ``getattr`` (NOT a static ``from lorerunes import ...``) so this
    file collects + typechecks clean while the surface is unbuilt (finding #133 idiom, the
    ``test_engine_rejection._load_reclassify`` precedent). A partial build names the exact
    missing symbols.
    """
    package = importlib.import_module(_PACKAGE)
    missing = [name for name in _REQUIRED_SYMBOLS if not hasattr(package, name)]
    if missing:
        pytest.fail(
            "the 61b-w1 PDP core is not built yet — "
            f"lorerunes is missing {missing}. RED before the build (this is expected "
            "pre-GREEN); the builder adds the PDP surface + re-exports it from "
            "lorerunes/__init__.py.",
            pytrace=False,
        )
    return package


# --------------------------------------------------------------------------- #
# Fixture factories — NO DEFAULT for role / scope / agent_id / table (PKT-28 C1).
# Every call CHOOSES, so a build that branches on a value cannot hide behind a
# fixture monoculture.
# --------------------------------------------------------------------------- #


def _subject(pdp: Any, *, principal_id: str, agent_id: str, role: str, keeps: frozenset[str]) -> Any:
    """A ``Subject`` — every field explicit (no monoculture default)."""
    return pdp.Subject(
        principal_id=principal_id, agent_id=agent_id, role=role, visible_keep_ids=keeps
    )


def _resource(pdp: Any, *, table: str, owner_principal: str, owner_agent: str, scope: str) -> Any:
    """A governed ``Resource`` — every field explicit (no monoculture default)."""
    return pdp.Resource(
        table=table, owner_principal=owner_principal, owner_agent=owner_agent, scope=scope
    )


# A governed table name used across the pure pins. The oracle file exercises the REAL
# emitted SQL against the live store; here ``table`` only needs to be a governed
# (non-audit) name for the member predicate, which is table-independent.
_GOV = "gov"


# =========================================================================== #
# Fork D — the Subject value object
# =========================================================================== #


class TestSubjectValueObject:
    """``Subject`` is a STDLIB frozen dataclass (F3 corrects Fork D — lorerunes is stdlib-only,
    NOT pydantic): ``@dataclass(frozen=True, slots=True)`` — frozen = immutable, slots = the
    ``extra='forbid'`` equivalent (unknown kwargs rejected, no extra attrs), ``__post_init__``
    validates the ``role`` domain. These pins assert the BEHAVIOUR (frozen / no-extra / validated
    / no-defaults), so they hold for a dataclass exactly as for the pydantic shape Fork D named."""

    def test_subject_is_frozen(self) -> None:
        pdp = _pdp()
        subject = _subject(
            pdp, principal_id="alice", agent_id="ag_a", role=pdp.PRINCIPAL_ROLE_MEMBER, keeps=frozenset()
        )
        with pytest.raises(Exception):  # noqa: B017,PT011 - pydantic raises on frozen mutation
            subject.role = pdp.PRINCIPAL_ROLE_ADMIN

    def test_subject_forbids_extra_fields(self) -> None:
        pdp = _pdp()
        with pytest.raises(Exception):  # noqa: B017,PT011 - extra='forbid'
            pdp.Subject(
                principal_id="alice",
                agent_id="ag_a",
                role=pdp.PRINCIPAL_ROLE_MEMBER,
                visible_keep_ids=frozenset(),
                smuggled="x",  # not a declared field
            )

    @pytest.mark.parametrize("role", ["member", "admin"])
    def test_subject_accepts_the_two_valid_roles(self, role: str) -> None:
        pdp = _pdp()
        subject = _subject(pdp, principal_id="alice", agent_id="ag_a", role=role, keeps=frozenset())
        assert subject.role == role

    @pytest.mark.parametrize("bad_role", ["owner", "root", "Member", "ADMIN", "", "guest"])
    def test_subject_rejects_a_role_outside_the_member_admin_domain(self, bad_role: str) -> None:
        pdp = _pdp()
        with pytest.raises(Exception):  # noqa: B017,PT011 - domain validation at construction
            _subject(pdp, principal_id="alice", agent_id="ag_a", role=bad_role, keeps=frozenset())

    def test_subject_role_domain_reuses_the_named_vocabulary_not_fresh_literals(self) -> None:
        """The ``{member, admin}`` domain is the lorerunes-homed vocabulary (Fork D rider —
        reuse ``principal.role``, one-column-one-vocabulary). The cross-check that it EQUALS
        ``surreal_schema._PRINCIPAL_ROLES`` lives in the oracle file (it imports loremaster)."""
        pdp = _pdp()
        assert set(pdp.PRINCIPAL_ROLES) == {pdp.PRINCIPAL_ROLE_MEMBER, pdp.PRINCIPAL_ROLE_ADMIN}
        assert pdp.PRINCIPAL_ROLE_MEMBER == "member"
        assert pdp.PRINCIPAL_ROLE_ADMIN == "admin"

    def test_visible_keep_ids_is_a_frozenset(self) -> None:
        pdp = _pdp()
        subject = _subject(
            pdp,
            principal_id="alice",
            agent_id="ag_a",
            role=pdp.PRINCIPAL_ROLE_MEMBER,
            keeps=frozenset({pdp.keep_scope("k1"), pdp.keep_scope("k2")}),
        )
        assert subject.visible_keep_ids == frozenset({"keep:k1", "keep:k2"})

    def test_subject_has_no_default_for_role(self) -> None:
        """No fixture-monoculture escape hatch: ``role`` is REQUIRED (PKT-28 C1)."""
        pdp = _pdp()
        with pytest.raises(Exception):  # noqa: B017,PT011 - role is required
            pdp.Subject(principal_id="alice", agent_id="ag_a", visible_keep_ids=frozenset())

    def test_subject_has_no_default_for_agent_id(self) -> None:
        pdp = _pdp()
        with pytest.raises(Exception):  # noqa: B017,PT011 - agent_id is required
            pdp.Subject(
                principal_id="alice", role=pdp.PRINCIPAL_ROLE_MEMBER, visible_keep_ids=frozenset()
            )

    @pytest.mark.parametrize("empty_field", ["principal_id", "agent_id"])
    def test_subject_rejects_empty_identity(self, empty_field: str) -> None:
        """F3 (confused-deputy hardening): an EMPTY principal_id/agent_id is a forgery vector —
        a subject always has a real identity (§3.2 — server-bound, non-empty)."""
        pdp = _pdp()
        kwargs: dict[str, Any] = {
            "principal_id": "alice",
            "agent_id": "ag_a",
            "role": pdp.PRINCIPAL_ROLE_MEMBER,
            "visible_keep_ids": frozenset(),
        }
        kwargs[empty_field] = ""
        with pytest.raises(Exception):  # noqa: B017,PT011 - empty identity rejected
            pdp.Subject(**kwargs)


# =========================================================================== #
# Fork D — the Resource value object (with the table field, reading B2)
# =========================================================================== #


class TestResourceValueObject:
    """``Resource`` is a STDLIB frozen dataclass (F3) carrying the governed row's authorization
    columns + its ``table`` (reading B2 — see the module header). frozen+slots = immutable +
    no-extra; ``__post_init__`` validates ``scope`` and non-empty ``table``."""

    def test_resource_is_frozen(self) -> None:
        pdp = _pdp()
        resource = _resource(
            pdp, table=_GOV, owner_principal="alice", owner_agent="ag_a", scope=pdp.SCOPE_SERVER
        )
        with pytest.raises(Exception):  # noqa: B017,PT011 - frozen
            resource.scope = pdp.SCOPE_AGENT_PRIVATE

    def test_resource_forbids_extra_fields(self) -> None:
        pdp = _pdp()
        with pytest.raises(Exception):  # noqa: B017,PT011 - extra='forbid'
            pdp.Resource(
                table=_GOV,
                owner_principal="alice",
                owner_agent="ag_a",
                scope=pdp.SCOPE_SERVER,
                smuggled="x",
            )

    @pytest.mark.parametrize(
        "scope",
        ["agent-private", "principal-private", "server", "keep:k1", "keep:a-long-ulid-id"],
    )
    def test_resource_accepts_every_valid_scope(self, scope: str) -> None:
        pdp = _pdp()
        resource = _resource(
            pdp, table=_GOV, owner_principal="alice", owner_agent="ag_a", scope=scope
        )
        assert resource.scope == scope

    @pytest.mark.parametrize("bad_scope", ["public", "keep", "keep:", "private", "", "Server"])
    def test_resource_rejects_a_scope_outside_the_domain(self, bad_scope: str) -> None:
        """The 4 scope values or ``keep:<non-empty>`` — nothing else (Fork D rider). A bare
        ``keep:`` with no id is invalid."""
        pdp = _pdp()
        with pytest.raises(Exception):  # noqa: B017,PT011 - scope domain validation
            _resource(
                pdp, table=_GOV, owner_principal="alice", owner_agent="ag_a", scope=bad_scope
            )

    def test_resource_rejects_an_empty_table(self) -> None:
        """``table`` is a non-empty string (Fork G — governed table names are not a closed
        domain at 61; the audit ``target_table`` non-empty idiom)."""
        pdp = _pdp()
        with pytest.raises(Exception):  # noqa: B017,PT011 - non-empty table
            _resource(
                pdp, table="", owner_principal="alice", owner_agent="ag_a", scope=pdp.SCOPE_SERVER
            )

    def test_resource_has_no_default_for_scope(self) -> None:
        pdp = _pdp()
        with pytest.raises(Exception):  # noqa: B017,PT011 - scope required (no monoculture)
            pdp.Resource(table=_GOV, owner_principal="alice", owner_agent="ag_a")

    @pytest.mark.parametrize("owner_field", ["owner_principal", "owner_agent"])
    def test_resource_accepts_an_absent_owner(self, owner_field: str) -> None:
        """F2: an ABSENT owner (``None``) is legal — a governed table's ``option<>`` owner column
        is NONE for an unowned/legacy row (§7 grandfathering). The read path must tolerate it."""
        pdp = _pdp()
        kwargs: dict[str, Any] = {
            "table": _GOV,
            "owner_principal": "alice",
            "owner_agent": "ag_a",
            "scope": pdp.SCOPE_SERVER,
        }
        kwargs[owner_field] = None
        resource = pdp.Resource(**kwargs)
        assert getattr(resource, owner_field) is None

    @pytest.mark.parametrize("owner_field", ["owner_principal", "owner_agent"])
    def test_resource_rejects_an_empty_owner(self, owner_field: str) -> None:
        """F3: an owner WHEN PRESENT is non-empty — an empty-string identity is a forgery vector
        (distinct from ``None``, which is a legitimate absent owner)."""
        pdp = _pdp()
        kwargs: dict[str, Any] = {
            "table": _GOV,
            "owner_principal": "alice",
            "owner_agent": "ag_a",
            "scope": pdp.SCOPE_SERVER,
        }
        kwargs[owner_field] = ""
        with pytest.raises(Exception):  # noqa: B017,PT011 - empty owner rejected
            pdp.Resource(**kwargs)

    def test_absent_owner_matches_no_owner_predicate_but_scope_still_applies(self) -> None:
        """F2 (matches side): a NONE-owner row is owned by nobody — the owner predicates don't
        match it (None != any id), but a scope predicate (server) still does. A member READS a
        NONE-owner ``server`` row (server = everyone) but cannot WRITE it (not the owner); a
        NONE-owner ``agent-private`` row is readable by nobody. matches() must handle None."""
        pdp = _pdp()
        none_server = pdp.Resource(
            table=_GOV, owner_principal=None, owner_agent=None, scope=pdp.SCOPE_SERVER
        )
        assert pdp.OwnerPrincipalEq("alice").matches(none_server) is False
        assert pdp.OwnerAgentEq("ag_a").matches(none_server) is False
        assert pdp.ScopeEq(pdp.SCOPE_SERVER).matches(none_server) is True
        alice = _alice_member(pdp)
        assert pdp.authorize(alice, pdp.Action.READ, none_server).allowed is True
        assert pdp.authorize(alice, pdp.Action.WRITE, none_server).allowed is False
        none_private = pdp.Resource(
            table=_GOV, owner_principal=None, owner_agent=None, scope=pdp.SCOPE_AGENT_PRIVATE
        )
        assert pdp.authorize(alice, pdp.Action.READ, none_private).allowed is False


# =========================================================================== #
# The Decision (Fork A/G) — allowed + requires_audit
# =========================================================================== #


class TestDecision:
    """``Decision`` carries ``allowed`` + ``requires_audit`` (Fork G). It is a value object."""

    def test_decision_carries_allowed_and_requires_audit(self) -> None:
        pdp = _pdp()
        subject = _subject(
            pdp, principal_id="alice", agent_id="ag_a", role=pdp.PRINCIPAL_ROLE_MEMBER, keeps=frozenset()
        )
        resource = _resource(
            pdp, table=_GOV, owner_principal="alice", owner_agent="ag_a", scope=pdp.SCOPE_SERVER
        )
        decision = pdp.authorize(subject, pdp.Action.READ, resource)
        assert isinstance(decision.allowed, bool)
        assert isinstance(decision.requires_audit, bool)

    def test_requires_audit_implies_allowed(self) -> None:
        """A denied action is never audited — you do not audit what did not happen. Over the
        whole hostile cross-product, ``requires_audit`` is never True while ``allowed`` is
        False (Fork G: the audit fires on a LOAD-BEARING bypass that actually ALLOWED)."""
        pdp = _pdp()
        for subject, action, resource, target in _cross_product(pdp):
            decision = pdp.authorize(subject, action, resource, target_scope=target)
            if decision.requires_audit:
                assert decision.allowed, (
                    f"requires_audit=True with allowed=False for {action} on "
                    f"{resource.scope}/{resource.table} — a denied action must not be audited"
                )


# =========================================================================== #
# Fork C — the action taxonomy (a closed domain)
# =========================================================================== #


class TestTheActionTaxonomy:
    """``Action`` is a CLOSED domain of exactly five actions (Fork C — the house
    closed-domain idiom, mirroring ``_PRINCIPAL_ROLES``/``_KEEP_TYPES``)."""

    def test_action_is_exactly_the_five_ruled_actions(self) -> None:
        pdp = _pdp()
        names = {member.name for member in pdp.Action}
        assert names == {"READ", "WRITE", "DELETE", "SET_SCOPE", "SET_OWNER"}, (
            "the action taxonomy is closed at exactly READ/WRITE/DELETE/SET_SCOPE/SET_OWNER "
            "(Fork C) — a NEW action grows this set and reds the pin until ruled"
        )

    def test_the_mutating_actions_match_the_audit_domain(self) -> None:
        """The four MUTATING actions (everything but READ) are exactly the audited-action
        domain the shipped ``audit`` store enforces (61a ``_AUDITED_ACTIONS``). The
        cross-check against ``surreal_schema._AUDITED_ACTIONS`` lives in the oracle file."""
        pdp = _pdp()
        mutating = {m.name for m in pdp.Action} - {"READ"}
        assert mutating == {"WRITE", "DELETE", "SET_SCOPE", "SET_OWNER"}


# =========================================================================== #
# Fork A — the predicate IR is a CLOSED algebra with TWO TOTAL interpreters
# (coverage-as-checked-variable, reach law #344/#345)
# =========================================================================== #


def _concrete_nodes(pdp: Any) -> list[type]:
    """DERIVE every concrete ``Predicate`` subclass (production truth, not a hand-list).

    Reach law: the covered set is derived, so a NEW node grows it and the coverage pins
    below red until BOTH interpreters handle it.
    """
    seen: set[type] = set()
    frontier = [pdp.Predicate]
    while frontier:
        klass = frontier.pop()
        for sub in klass.__subclasses__():
            if sub not in seen:
                seen.add(sub)
                frontier.append(sub)
    # concrete = instantiable (no abstractmethods left)
    return [k for k in seen if not getattr(k, "__abstractmethods__", frozenset())]


def _one_of_each_node(pdp: Any) -> dict[type, Any]:
    """Construct ONE instance of each concrete node, with valid args."""
    instances: dict[type, Any] = {
        pdp.ScopeEq: pdp.ScopeEq(pdp.SCOPE_SERVER),
        pdp.OwnerPrincipalEq: pdp.OwnerPrincipalEq("alice"),
        pdp.OwnerAgentEq: pdp.OwnerAgentEq("ag_a"),
        pdp.ScopeInKeeps: pdp.ScopeInKeeps(frozenset({pdp.keep_scope("k1")})),
        pdp.And: pdp.And((pdp.ScopeEq(pdp.SCOPE_SERVER), pdp.OwnerPrincipalEq("alice"))),
        pdp.Or: pdp.Or((pdp.ScopeEq(pdp.SCOPE_SERVER), pdp.NoRows())),
        pdp.AllRows: pdp.AllRows(),
        pdp.NoRows: pdp.NoRows(),
    }
    return instances


class TestThePredicateIRIsAClosedAlgebra:
    """The IR node set is closed and BOTH interpreters are TOTAL over it (Fork A rider —
    no ``else: return True`` fall-through; a node one interpreter misses reds a pin)."""

    def test_predicate_is_abstract_with_both_interpreter_methods(self) -> None:
        """``Predicate`` is an ABC whose ``to_surql`` + ``matches`` are abstract, so a node
        missing EITHER interpreter cannot be instantiated — the coverage guarantee is
        structural, not disciplinary."""
        pdp = _pdp()
        abstract = getattr(pdp.Predicate, "__abstractmethods__", frozenset[str]())
        assert "to_surql" in abstract and "matches" in abstract, (
            "Predicate must declare to_surql AND matches abstract, so a subclass that "
            "implements only one cannot be instantiated (Fork A: no silent fall-through)"
        )

    def test_the_concrete_node_set_is_exactly_the_closed_algebra(self) -> None:
        pdp = _pdp()
        names = {k.__name__ for k in _concrete_nodes(pdp)}
        assert names == {
            "ScopeEq",
            "OwnerPrincipalEq",
            "OwnerAgentEq",
            "ScopeInKeeps",
            "And",
            "Or",
            "AllRows",
            "NoRows",
        }, (
            "the predicate IR is a CLOSED algebra (Fork A). A NEW node here grows the "
            "derived set and reds this pin until the node is ruled into the algebra AND "
            "handled by both interpreters (see the coverage pins below)."
        )

    def test_no_predicate_subclass_is_partially_abstract(self) -> None:
        """The reach-law mutation the brief names: a node handled by ONLY ONE interpreter reds
        THIS pin. Every ``Predicate`` subclass (the base excepted) must be CONCRETE — an empty
        ``__abstractmethods__``. A node implementing only ``matches`` leaves ``to_surql``
        abstract (``__abstractmethods__ == {'to_surql'}``) → non-empty → RED. (It also could
        not be instantiated, but this pin catches the DEFINITION, not just a use site — the
        derived-set filter for concreteness would otherwise silently exclude it.)"""
        pdp = _pdp()
        partial: dict[str, frozenset[str]] = {}
        frontier = [pdp.Predicate]
        seen: set[type] = set()
        while frontier:
            klass = frontier.pop()
            for sub in klass.__subclasses__():
                if sub in seen:
                    continue
                seen.add(sub)
                frontier.append(sub)
                unimplemented = getattr(sub, "__abstractmethods__", frozenset[str]())
                if unimplemented:
                    partial[sub.__name__] = unimplemented
        assert not partial, (
            f"partially-abstract Predicate subclass(es) {partial} — a node must implement BOTH "
            "to_surql AND matches (Fork A: no interpreter silently misses a node)"
        )

    def test_the_derived_node_set_is_non_empty(self) -> None:
        """Guard the guard (INSTRUMENT-0): if the derivation finds nothing (a renamed base,
        a moved module), fail loudly rather than vacuously pass every coverage pin."""
        assert _concrete_nodes(_pdp()), (
            "no concrete Predicate subclasses derived — the coverage derivation is broken, "
            "so its ∀ pins are vacuous"
        )

    def test_every_node_has_a_working_to_surql(self) -> None:
        """to_surql is TOTAL: every concrete node emits ``(fragment, params)`` with no
        NotImplementedError / fall-through."""
        pdp = _pdp()
        instances = _one_of_each_node(pdp)
        covered = {type(v) for v in instances.values()}
        assert covered == set(_concrete_nodes(pdp)), (
            "a concrete node has no constructed instance in this coverage pin — extend "
            "_one_of_each_node so a NEW node is exercised, never silently skipped"
        )
        for node in instances.values():
            fragment, params = node.to_surql()
            assert isinstance(fragment, str)
            assert isinstance(params, dict)

    def test_every_node_has_a_working_matches(self) -> None:
        """matches is TOTAL: every concrete node evaluates a Resource to a bool."""
        pdp = _pdp()
        resource = _resource(
            pdp, table=_GOV, owner_principal="alice", owner_agent="ag_a", scope=pdp.SCOPE_SERVER
        )
        for node in _one_of_each_node(pdp).values():
            assert isinstance(node.matches(resource), bool)


def _has_unparenthesised_top_level_or(fragment: str) -> bool:
    """True iff ``fragment`` has an ``" OR "`` at paren-depth 0 — i.e., it is NOT self-contained.

    Such a fragment LEAKS a disjunct when embedded as a child of an And (``(x AND <fragment>)``),
    because SurrealQL binds AND tighter than OR: ``(x AND a OR b)`` parses as ``(x AND a) OR b``,
    so ``b`` escapes the And. The whole IR assumes self-containment; this detects a node that
    opts out (#416).
    """
    depth = 0
    for index, char in enumerate(fragment):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif depth == 0 and fragment[index : index + 4] == " OR ":
            return True
    return False


class TestPredicateFragmentsAreSelfContained:
    """#416 (security MEDIUM — a latent cross-principal LEAK): every node's ``to_surql`` fragment
    is SELF-CONTAINED (no top-level ``OR`` outside parens), so composing it under an And
    (``(owner=$p AND <fragment>)``) cannot let a disjunct ESCAPE the owner constraint and return
    OTHER principals' rows. And/Or/ScopeInKeeps ALL emit ``(…)``; this pins the property for every
    node so one that opts out (an unparenthesised ScopeInKeeps) reds. The live-store proof (the
    leak is real, the parens fix it) is in the oracle file's composition-safety pin."""

    def test_scope_in_keeps_with_multiple_keeps_is_parenthesised(self) -> None:
        pdp = _pdp()
        fragment, _params = pdp.ScopeInKeeps(
            frozenset({pdp.keep_scope("k1"), pdp.keep_scope("k2")})
        ).to_surql()
        assert not _has_unparenthesised_top_level_or(fragment), (
            f"ScopeInKeeps(≥2) emits an UNPARENTHESISED OR {fragment!r} — under an And a keep "
            "disjunct escapes the owner constraint and leaks other principals' rows (#416)"
        )

    def test_no_node_emits_an_unparenthesised_top_level_or(self) -> None:
        """Reach-law coverage over the multi-disjunct emitters + one-of-each: a node whose
        fragment carries a top-level OR is a #416 leak-in-waiting."""
        pdp = _pdp()
        multi_disjunct = [
            pdp.ScopeInKeeps(frozenset({pdp.keep_scope("k1"), pdp.keep_scope("k2")})),
            pdp.Or((pdp.ScopeEq(pdp.SCOPE_SERVER), pdp.ScopeEq(pdp.SCOPE_AGENT_PRIVATE))),
        ]
        nodes = list(_one_of_each_node(pdp).values()) + multi_disjunct
        offenders = {
            type(node).__name__: node.to_surql()[0]
            for node in nodes
            if _has_unparenthesised_top_level_or(node.to_surql()[0])
        }
        assert not offenders, (
            f"node(s) emit an UNPARENTHESISED top-level OR {offenders} — a #416 cross-principal "
            "leak under an And. Multi-disjunct emits must wrap: `(a OR b)`."
        )


class TestScopeInKeepsExpansion:
    """``ScopeInKeeps`` EMITS the keep set EXPANDED to per-keep equality disjuncts (finding
    #413 / store-ref §2 — a literal ``scope IN $set`` inside an OR is a TableScan trap).
    The IndexScan proof itself is the live-store pin in the oracle file; here we pin the
    EMITTED SHAPE (no ``IN``) and the empty-set omission + bound params."""

    def test_scope_in_keeps_expands_to_per_keep_equalities_never_a_literal_IN(self) -> None:
        pdp = _pdp()
        node = pdp.ScopeInKeeps(frozenset({pdp.keep_scope("k1"), pdp.keep_scope("k2")}))
        fragment, params = node.to_surql()
        assert " IN " not in f" {fragment} ", (
            "ScopeInKeeps must EXPAND to `scope = $k0 OR scope = $k1 ...`, never emit a "
            "literal `scope IN $set` — the #413 IN-inside-OR TableScan trap (store-ref §2)"
        )
        # two keeps -> two bound `scope = $...` equality clauses, values only in params
        assert fragment.count("scope =") == 2 or fragment.count("scope=") == 2
        assert set(params.values()) == {"keep:k1", "keep:k2"}
        assert "keep:k1" not in fragment and "keep:k2" not in fragment, (
            "keep values must be BOUND params, never interpolated into the fragment (store-ref §2)"
        )

    def test_empty_keep_set_emits_no_keep_clause(self) -> None:
        """The probe verdict (#413): OMIT the clause when the keep set is empty (an empty
        ``IN``/OR is a needless planner hazard). matches is False for any scope."""
        pdp = _pdp()
        node = pdp.ScopeInKeeps(frozenset())
        fragment, params = node.to_surql()
        assert "scope" not in fragment or fragment.strip() in ("", "false"), (
            "an empty ScopeInKeeps must contribute NO scope clause (or a benign `false`) — "
            "never a dangling `scope IN []` inside the READ OR (#413)"
        )
        resource = _resource(
            pdp, table=_GOV, owner_principal="bob", owner_agent="ag_b", scope="keep:k9"
        )
        assert node.matches(resource) is False

    def test_scope_in_keeps_matches_membership(self) -> None:
        pdp = _pdp()
        node = pdp.ScopeInKeeps(frozenset({pdp.keep_scope("k1")}))
        in_keep = _resource(
            pdp, table=_GOV, owner_principal="bob", owner_agent="ag_b", scope="keep:k1"
        )
        out_keep = _resource(
            pdp, table=_GOV, owner_principal="bob", owner_agent="ag_b", scope="keep:k2"
        )
        assert node.matches(in_keep) is True
        assert node.matches(out_keep) is False


class TestToSurqlBindsParamsNeverInterpolates:
    """The emitter binds every value as a param (store-ref §2 — injection-safe). A hostile
    principal id is a bound param, never SQL text."""

    def test_owner_and_scope_values_are_bound_not_interpolated(self) -> None:
        pdp = _pdp()
        subject = _subject(
            pdp,
            principal_id="alice",
            agent_id="ag_a",
            role=pdp.PRINCIPAL_ROLE_MEMBER,
            keeps=frozenset({pdp.keep_scope("k1")}),
        )
        fragment, params = pdp.authorize_filter(subject, pdp.Action.READ, _GOV).to_surql()
        # every $name in the fragment is a key in params; no literal owner/scope value leaks
        assert "alice" not in fragment
        assert "ag_a" not in fragment
        assert params, "a member READ predicate binds params (owner/scope/keeps)"

    def test_a_hostile_principal_id_is_a_bound_param(self) -> None:
        """Confused-deputy / injection containment (§9): a principal id carrying SurrealQL
        is bound, not interpolated — the fragment carries no injected clause."""
        pdp = _pdp()
        hostile = "alice'; REMOVE TABLE gov; --"
        subject = _subject(
            pdp, principal_id=hostile, agent_id="ag_a", role=pdp.PRINCIPAL_ROLE_MEMBER, keeps=frozenset()
        )
        fragment, params = pdp.authorize_filter(subject, pdp.Action.READ, _GOV).to_surql()
        assert "REMOVE TABLE" not in fragment
        assert hostile in set(params.values()), "the hostile id must survive as a BOUND value"


# =========================================================================== #
# Fork C — per-action predicate correctness (matches side; hostile fixture)
# =========================================================================== #

# The hostile fixture row set: ≥2 principals x ≥2 agents each, EVERY scope value, keep rows
# in AND out of a caller's keep set, a server row (Fork A rider). Built as (id, principal,
# agent, scope) so the oracle file can seed the identical set (byte-parity is the point).
_HOSTILE_ROWS: tuple[tuple[str, str, str, str], ...] = (
    ("r1", "alice", "ag_a", "agent-private"),
    ("r2", "alice", "ag_b", "agent-private"),  # a sibling agent's private row
    ("r3", "alice", "ag_a", "principal-private"),
    ("r4", "alice", "ag_b", "principal-private"),  # sibling's principal-private (read yes / write no)
    ("r5", "bob", "ag_c", "principal-private"),  # another principal — never visible to alice
    ("r6", "bob", "ag_c", "agent-private"),
    ("r7", "alice", "ag_a", "server"),
    ("r8", "bob", "ag_c", "server"),
    ("r9", "alice", "ag_a", "keep:k1"),  # in alice's keeps
    ("r10", "bob", "ag_c", "keep:k1"),  # a keep row alice can see/write (household), owned by bob
    ("r11", "alice", "ag_a", "keep:k9"),  # NOT in alice's keeps
    ("r12", "bob", "ag_c", "keep:k9"),
)


def _hostile_resources(pdp: Any, table: str = _GOV) -> list[Any]:
    return [
        _resource(pdp, table=table, owner_principal=p, owner_agent=a, scope=s)
        for (_id, p, a, s) in _HOSTILE_ROWS
    ]


def _row_id(index: int) -> str:
    return _HOSTILE_ROWS[index][0]


# Alice, a plain member, whose visible keeps are {k1} only.
def _alice_member(pdp: Any) -> Any:
    return _subject(
        pdp,
        principal_id="alice",
        agent_id="ag_a",
        role=pdp.PRINCIPAL_ROLE_MEMBER,
        keeps=frozenset({pdp.keep_scope("k1")}),
    )


def _allowed_ids(
    pdp: Any, subject: Any, action: Any, resources: list[Any], target_scope: str | None = None
) -> set[str]:
    return {
        _HOSTILE_ROWS[i][0]
        for i, resource in enumerate(resources)
        if pdp.authorize(subject, action, resource, target_scope=target_scope).allowed
    }


class TestReadPredicate:
    """Member READ (Fork C row 1 / §4): own agent-private, own-principal principal-private
    (any SIBLING agent reads it), all server, keep rows whose household I'm in."""

    def test_member_read_visible_set(self) -> None:
        pdp = _pdp()
        alice = _alice_member(pdp)
        resources = _hostile_resources(pdp)
        allowed = _allowed_ids(pdp, alice, pdp.Action.READ, resources)
        assert allowed == {
            "r1",  # alice/ag_a agent-private — the owning agent
            "r3",  # alice/ag_a principal-private — owning principal + agent
            "r4",  # alice/ag_b principal-private — a SIBLING agent's row: READ yes (owner_principal)
            "r7",  # alice server
            "r8",  # bob server — server is everyone
            "r9",  # alice keep:k1 — in alice's keeps
            "r10",  # bob keep:k1 — household row, visible
        }

    def test_sibling_agent_private_is_NOT_readable(self) -> None:
        """agent-private is the OWNING AGENT only: alice/ag_a cannot READ alice/ag_b's
        agent-private row (r2) — the read asymmetry vs principal-private."""
        pdp = _pdp()
        allowed = _allowed_ids(pdp, _alice_member(pdp), pdp.Action.READ, _hostile_resources(pdp))
        assert "r2" not in allowed

    def test_cross_principal_isolation_on_read(self) -> None:
        """§9 cross-principal isolation: alice never reads bob's private rows (r5/r6)."""
        pdp = _pdp()
        allowed = _allowed_ids(pdp, _alice_member(pdp), pdp.Action.READ, _hostile_resources(pdp))
        assert "r5" not in allowed and "r6" not in allowed

    def test_a_keep_row_outside_my_keeps_is_not_readable(self) -> None:
        pdp = _pdp()
        allowed = _allowed_ids(pdp, _alice_member(pdp), pdp.Action.READ, _hostile_resources(pdp))
        assert "r11" not in allowed and "r12" not in allowed


class TestWritePredicate:
    """Member WRITE (Fork C row 2 / §4): owner-of-private (EXACT (principal,agent) — reading
    1), any household member of a keep row, owner of a server row."""

    def test_member_write_visible_set(self) -> None:
        pdp = _pdp()
        alice = _alice_member(pdp)
        allowed = _allowed_ids(pdp, alice, pdp.Action.WRITE, _hostile_resources(pdp))
        assert allowed == {
            "r1",  # alice/ag_a agent-private — owner
            "r3",  # alice/ag_a principal-private — EXACT owner (reading 1)
            "r7",  # alice/ag_a server — owner of a server row
            "r9",  # alice keep:k1 — household member may write
            "r10",  # bob keep:k1 — household member (alice) may write another's keep row
        }

    def test_reading_1_a_sibling_agent_cannot_write_a_principal_private_row(self) -> None:
        """THE reading-1 discriminator (Fork C flag, RULED exact (principal,agent)): alice/ag_a
        may READ alice/ag_b's principal-private row (r4) but may NOT WRITE it. A single-agent
        fixture cannot tell reading 1 from reading 2 — r4 (alice/ag_b) is that fixture."""
        pdp = _pdp()
        alice = _alice_member(pdp)
        r4 = _hostile_resources(pdp)[3]  # alice/ag_b principal-private
        assert pdp.authorize(alice, pdp.Action.READ, r4).allowed is True
        assert pdp.authorize(alice, pdp.Action.WRITE, r4).allowed is False, (
            "reading 1: a sibling agent may NOT write another sibling's principal-private row"
        )

    def test_member_cannot_write_a_keep_row_outside_their_keeps(self) -> None:
        pdp = _pdp()
        allowed = _allowed_ids(pdp, _alice_member(pdp), pdp.Action.WRITE, _hostile_resources(pdp))
        assert "r11" not in allowed and "r12" not in allowed

    def test_member_cannot_write_another_principals_server_row(self) -> None:
        """server is broadcast: everyone READS, only the OWNER (or admin) WRITES — a member
        cannot vandalise bob's server row (r8)."""
        pdp = _pdp()
        allowed = _allowed_ids(pdp, _alice_member(pdp), pdp.Action.WRITE, _hostile_resources(pdp))
        assert "r8" not in allowed


class TestDeletePredicate:
    """Member DELETE (Fork C row 3 / §4.3 + D4(a)): the row's OWNER only (exact stamp), ANY
    scope — household members edit/supersede but never VANISH each other's keep rows.

    ⚠ D4(a), CONFIRMED INTENDED (ownership ≠ scope): DELETE is owner-gated and
    scope-INDEPENDENT, so an owner may DELETE a ``keep:<id>`` row of a keep they have LEFT (r11
    below — alice owns it, is not in k9, cannot READ or WRITE it, but CAN delete it). Adding a
    household conjunct to DELETE would create UN-DELETABLE orphans (a row whose owner left the
    keep could never be cleaned) — so if this ever looks wrong, reconsider owner-cleanup first."""

    def test_member_delete_is_owner_only_across_every_scope(self) -> None:
        pdp = _pdp()
        alice = _alice_member(pdp)
        allowed = _allowed_ids(pdp, alice, pdp.Action.DELETE, _hostile_resources(pdp))
        assert allowed == {
            "r1",  # alice/ag_a agent-private — owner
            "r3",  # alice/ag_a principal-private — owner
            "r7",  # alice/ag_a server — owner
            "r9",  # alice/ag_a keep:k1 — owner (NOT r10: bob owns it)
            "r11",  # alice/ag_a keep:k9 — owner may DELETE even a keep they're not in (owner-only)
        }

    def test_a_household_member_cannot_delete_another_members_keep_row(self) -> None:
        """r10 is bob's keep:k1 row; alice (household) may WRITE it but NOT DELETE it (§4.3)."""
        pdp = _pdp()
        alice = _alice_member(pdp)
        r10 = _hostile_resources(pdp)[9]
        assert pdp.authorize(alice, pdp.Action.WRITE, r10).allowed is True
        assert pdp.authorize(alice, pdp.Action.DELETE, r10).allowed is False


class TestSetScopePredicate:
    """Member SET_SCOPE (Fork C row 4 / §4.3 + D4(b) SECURITY refinement): the row's OWNER
    only AND the TARGET scope must be GRANTABLE by the subject (§3.2.3 scope-on-write) — a
    member may re-scope their own row to a keep ONLY IF they are in it; freely to private +
    server. Fork C under-specified this as bare ``owner=me``."""

    @pytest.mark.parametrize("target", ["principal-private", "agent-private", "server", "keep:k1"])
    def test_set_scope_to_a_grantable_target_is_owner_only(self, target: str) -> None:
        pdp = _pdp()
        alice = _alice_member(pdp)  # keeps={k1} — so keep:k1 is grantable, private/server always
        allowed = _allowed_ids(
            pdp, alice, pdp.Action.SET_SCOPE, _hostile_resources(pdp), target_scope=target
        )
        assert allowed == {"r1", "r3", "r7", "r9", "r11"}, (
            f"grantable target {target!r}: SET_SCOPE is owner-only over every scope"
        )

    def test_set_scope_to_a_keep_the_member_is_not_in_is_refused_for_every_row(self) -> None:
        """D4(b): a member cannot GRANT a keep scope they are not a member of — not even to
        their OWN row. So SET_SCOPE to keep:k9 (alice ∉ k9) → NoRows over the whole table."""
        pdp = _pdp()
        alice = _alice_member(pdp)
        allowed = _allowed_ids(
            pdp, alice, pdp.Action.SET_SCOPE, _hostile_resources(pdp), target_scope=pdp.keep_scope("k9")
        )
        assert allowed == set()

    def test_the_discriminating_own_row_fixture(self) -> None:
        """fixtures-must-discriminate (D4(b)): alice SET_SCOPE her OWN row (r1) → to keep:k9
        (∉) REFUSED, to keep:k1 (∈) allowed. A build reading SET_SCOPE as bare owner=me passes
        the grantable case; only this non-grantable-own-row case tells them apart."""
        pdp = _pdp()
        alice = _alice_member(pdp)
        r1 = _hostile_resources(pdp)[0]  # alice/ag_a — alice owns it
        assert (
            pdp.authorize(alice, pdp.Action.SET_SCOPE, r1, target_scope=pdp.keep_scope("k9")).allowed
            is False
        )
        assert (
            pdp.authorize(alice, pdp.Action.SET_SCOPE, r1, target_scope=pdp.keep_scope("k1")).allowed
            is True
        )

    def test_set_scope_with_no_target_grants_nothing(self) -> None:
        """A SET_SCOPE with no target scope grants nothing (denies every row) — you must name
        the target you are setting (a None target is not grantable)."""
        pdp = _pdp()
        alice = _alice_member(pdp)
        allowed = _allowed_ids(pdp, alice, pdp.Action.SET_SCOPE, _hostile_resources(pdp))
        assert allowed == set()

    def test_authorize_filter_set_scope_to_non_grantable_is_norows(self) -> None:
        pdp = _pdp()
        predicate = pdp.authorize_filter(
            _alice_member(pdp), pdp.Action.SET_SCOPE, _GOV, target_scope=pdp.keep_scope("k9")
        )
        assert isinstance(predicate, pdp.NoRows)


class TestSetOwnerPredicate:
    """Member SET_OWNER (Fork C row 5 / §4.3): NONE — admin-only, even on your OWN row."""

    def test_member_set_owner_is_never_allowed_even_on_own_row(self) -> None:
        pdp = _pdp()
        alice = _alice_member(pdp)
        allowed = _allowed_ids(pdp, alice, pdp.Action.SET_OWNER, _hostile_resources(pdp))
        assert allowed == set(), "SET_OWNER is admin-only; a member cannot even give away own row"

    def test_authorize_filter_set_owner_for_a_member_is_norows(self) -> None:
        pdp = _pdp()
        predicate = pdp.authorize_filter(_alice_member(pdp), pdp.Action.SET_OWNER, _GOV)
        assert isinstance(predicate, pdp.NoRows)


# =========================================================================== #
# Fork A/G — the admin short-circuit + the audit carve-out
# =========================================================================== #


def _admin(pdp: Any) -> Any:
    """An admin whose OWN identity is alice/ag_a (so own-row vs cross-owner discriminates)."""
    return _subject(
        pdp, principal_id="alice", agent_id="ag_a", role=pdp.PRINCIPAL_ROLE_ADMIN, keeps=frozenset()
    )


class TestAdminShortCircuit:
    """admin is a full superuser (§4.2/§10-K): ``authorize_filter`` returns ``AllRows`` for
    every action on a GOVERNED table, EXCEPT the audit-table carve-out for mutating actions
    (Fork G)."""

    @pytest.mark.parametrize("action", ["READ", "WRITE", "DELETE", "SET_SCOPE", "SET_OWNER"])
    def test_admin_gets_all_rows_on_a_governed_table(self, action: str) -> None:
        pdp = _pdp()
        admin = _admin(pdp)
        predicate = pdp.authorize_filter(admin, pdp.Action[action], _GOV)
        assert isinstance(predicate, pdp.AllRows), (
            f"admin {action} on a governed table is AllRows (the superuser short-circuit)"
        )
        # and every hostile row is allowed for admin
        allowed = _allowed_ids(pdp, admin, pdp.Action[action], _hostile_resources(pdp))
        assert allowed == {r[0] for r in _HOSTILE_ROWS}

    def test_admin_short_circuit_is_a_role_branch_not_a_bypass(self) -> None:
        """§5: admin is the ``role==admin`` BRANCH of authorize_filter; the equivalence still
        holds trivially (all-vs-all) — a member of the SAME identity is filtered."""
        pdp = _pdp()
        member = _subject(
            pdp, principal_id="alice", agent_id="ag_a", role=pdp.PRINCIPAL_ROLE_MEMBER, keeps=frozenset()
        )
        admin = _admin(pdp)
        member_allowed = _allowed_ids(pdp, member, pdp.Action.READ, _hostile_resources(pdp))
        admin_allowed = _allowed_ids(pdp, admin, pdp.Action.READ, _hostile_resources(pdp))
        assert member_allowed < admin_allowed, "admin READ strictly dominates member READ"


class TestTheAuditCarveOut:
    """The ONE carve-out from admin-is-full (Fork G / §9): admin canNOT mutate ``audit``
    rows. ``authorize(admin, {mutating}, audit_resource) = DENY`` — admin cannot erase its
    own trail. READ of audit is still allowed (only mutation is carved out)."""

    def _audit_resource(self, pdp: Any) -> Any:
        # An audit row carries no governed owner/scope columns; the carve-out is TABLE-driven,
        # so owner/scope are placeholders here (documented in the module header, reading B2).
        return _resource(
            pdp,
            table=pdp.AUDIT_TABLE,
            owner_principal="alice",
            owner_agent="ag_a",
            scope=pdp.SCOPE_SERVER,
        )

    @pytest.mark.parametrize("action", ["WRITE", "DELETE", "SET_SCOPE", "SET_OWNER"])
    def test_admin_cannot_mutate_an_audit_row(self, action: str) -> None:
        pdp = _pdp()
        decision = pdp.authorize(_admin(pdp), pdp.Action[action], self._audit_resource(pdp))
        assert decision.allowed is False, (
            f"admin {action} on an audit row must be DENIED (Fork G carve-out — admin cannot "
            "erase its own trail)"
        )

    @pytest.mark.parametrize("action", ["WRITE", "DELETE", "SET_SCOPE", "SET_OWNER"])
    def test_audit_carve_out_predicate_is_norows(self, action: str) -> None:
        pdp = _pdp()
        predicate = pdp.authorize_filter(_admin(pdp), pdp.Action[action], pdp.AUDIT_TABLE)
        assert isinstance(predicate, pdp.NoRows), (
            "the audit carve-out is a NoRows NODE inside the one expression (Fork A) — not a "
            "bypass beside it, so the §5 equivalence still holds"
        )

    def test_admin_can_still_READ_audit(self) -> None:
        """The carve-out is mutation-only: admin READS the trail (§9 — only DELETE/UPDATE
        are refused)."""
        pdp = _pdp()
        decision = pdp.authorize(_admin(pdp), pdp.Action.READ, self._audit_resource(pdp))
        assert decision.allowed is True

    def test_a_mutating_audit_decision_is_not_audited(self) -> None:
        """A DENIED audit mutation is not itself audited (requires_audit False — nothing
        happened)."""
        pdp = _pdp()
        decision = pdp.authorize(_admin(pdp), pdp.Action.DELETE, self._audit_resource(pdp))
        assert decision.requires_audit is False


# =========================================================================== #
# Fork G — requires_audit: fires IFF the admin bypass was LOAD-BEARING
# =========================================================================== #


class TestRequiresAudit:
    """``requires_audit = allowed AND role==admin AND action∈mutating AND NOT
    member_predicate(action).matches(resource)`` (Fork G — audit the USE of admin POWER, the
    load-bearing bypass; DERIVED from the same member predicate = single-brain)."""

    def test_admin_cross_owner_write_is_audited(self) -> None:
        pdp = _pdp()
        admin = _admin(pdp)  # identity alice/ag_a
        bob_private = _resource(
            pdp,
            table=_GOV,
            owner_principal="bob",
            owner_agent="ag_c",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        decision = pdp.authorize(admin, pdp.Action.WRITE, bob_private)
        assert decision.allowed is True
        assert decision.requires_audit is True, (
            "admin writing ANOTHER principal's private row exercises the superuser bypass "
            "(a member could not) — it is AUDITED (§9)"
        )

    def test_admin_own_row_write_is_NOT_audited(self) -> None:
        """THE discriminator (fixtures-must-discriminate): admin editing its OWN row exercises
        NO bypass (a member could too) → requires_audit False. Without this fixture, a build
        auditing EVERY admin action passes the cross-owner pin."""
        pdp = _pdp()
        admin = _admin(pdp)  # identity alice/ag_a
        own = _resource(
            pdp,
            table=_GOV,
            owner_principal="alice",
            owner_agent="ag_a",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        decision = pdp.authorize(admin, pdp.Action.WRITE, own)
        assert decision.allowed is True
        assert decision.requires_audit is False

    def test_member_write_is_never_audited(self) -> None:
        pdp = _pdp()
        alice = _alice_member(pdp)
        own = _resource(
            pdp, table=_GOV, owner_principal="alice", owner_agent="ag_a", scope=pdp.SCOPE_SERVER
        )
        assert pdp.authorize(alice, pdp.Action.WRITE, own).requires_audit is False

    def test_admin_set_owner_is_always_audited(self) -> None:
        """SET_OWNER is admin-only for EVERYONE (member predicate = NoRows), so EVERY admin
        SET_OWNER — even on its own row — is a load-bearing bypass → audited."""
        pdp = _pdp()
        admin = _admin(pdp)
        own = _resource(
            pdp, table=_GOV, owner_principal="alice", owner_agent="ag_a", scope=pdp.SCOPE_SERVER
        )
        decision = pdp.authorize(admin, pdp.Action.SET_OWNER, own)
        assert decision.allowed is True
        assert decision.requires_audit is True

    def test_admin_read_is_never_audited(self) -> None:
        """READ exercises no MUTATING power; it is never audited (Fork G — READ is never in
        the audited-action domain), even cross-principal."""
        pdp = _pdp()
        admin = _admin(pdp)
        bob_private = _resource(
            pdp,
            table=_GOV,
            owner_principal="bob",
            owner_agent="ag_c",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        assert pdp.authorize(admin, pdp.Action.READ, bob_private).requires_audit is False

    def test_admin_set_scope_into_a_non_grantable_keep_is_audited(self) -> None:
        """F2 (§9 single-brain): an admin re-scoping their OWN row into a keep they are NOT a
        member of exercises a LOAD-BEARING bypass — a member cannot grant that scope (§3.2.3,
        the D4(b) grantability rule) — so it MUST be audited. A build computing
        ``requires_audit`` with a member-check that DROPS grantability (a cloned/simplified
        member predicate) UNDER-audits this and passes every other pin — the ROUTING-IS-NOT-
        SHARING gap. ``requires_audit`` must share the SAME member predicate ``authorize`` uses."""
        pdp = _pdp()
        admin = _admin(pdp)  # alice/ag_a, keeps={} — NOT in k9
        own = _resource(
            pdp,
            table=_GOV,
            owner_principal="alice",
            owner_agent="ag_a",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        decision = pdp.authorize(admin, pdp.Action.SET_SCOPE, own, target_scope=pdp.keep_scope("k9"))
        assert decision.allowed is True  # admin AllRows
        assert decision.requires_audit is True, (
            "admin SET_SCOPE of its OWN row into a keep it is not a member of is a load-bearing "
            "bypass (a member could not grant that scope) — it MUST be audited (§9). If this is "
            "False, requires_audit is using a member predicate that dropped grantability."
        )

    def test_admin_set_scope_own_row_into_a_grantable_keep_is_NOT_audited(self) -> None:
        """The discriminator (fixtures-must-discriminate): admin who IS in keep k1, re-scoping
        its OWN row to k1 — a member could do exactly this → NO bypass → NOT audited. Without
        this fixture a build auditing EVERY admin SET_SCOPE passes the non-grantable pin above."""
        pdp = _pdp()
        admin = _subject(
            pdp,
            principal_id="alice",
            agent_id="ag_a",
            role=pdp.PRINCIPAL_ROLE_ADMIN,
            keeps=frozenset({pdp.keep_scope("k1")}),
        )
        own = _resource(
            pdp,
            table=_GOV,
            owner_principal="alice",
            owner_agent="ag_a",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        decision = pdp.authorize(admin, pdp.Action.SET_SCOPE, own, target_scope=pdp.keep_scope("k1"))
        assert decision.allowed is True
        assert decision.requires_audit is False


# =========================================================================== #
# Fork A / §5 — the single-brain equivalence (in-memory leg; the live-store
# ORACLE is the byte-parity leg in test_pdp_oracle_61b.py)
# =========================================================================== #


def _cross_product(pdp: Any) -> list[tuple[Any, Any, Any, str | None]]:
    """Every (subject, action, resource, target_scope) over the hostile fixture, both roles.

    SET_SCOPE carries a target scope (D4(b)); a grantable and a non-grantable one are both
    exercised so the equivalence + requires_audit pins cover the grantability branch. Every
    other action carries ``None``.
    """
    subjects = [
        _alice_member(pdp),
        _admin(pdp),
        _subject(
            pdp, principal_id="bob", agent_id="ag_c", role=pdp.PRINCIPAL_ROLE_MEMBER,
            keeps=frozenset({pdp.keep_scope("k9")}),
        ),
    ]
    quads: list[tuple[Any, Any, Any, str | None]] = []
    for subject in subjects:
        for action in pdp.Action:
            targets: list[str | None] = [None]
            if action is pdp.Action.SET_SCOPE:
                targets = [pdp.keep_scope("k1"), pdp.keep_scope("k9"), pdp.SCOPE_SERVER]
            for resource in _hostile_resources(pdp):
                for target in targets:
                    quads.append((subject, action, resource, target))
    return quads


class TestAuthorizeIsAuthorizeFilterMatches:
    """§5 (the anti-split-brain invariant), the in-memory leg: for every (s, a, row),
    ``authorize(s,a,row).allowed`` EQUALS ``authorize_filter(s,a,row.table).matches(row)``.
    True by construction (``authorize`` calls the filter's evaluator), pinned so a build
    that forks a second decision path reds."""

    def test_single_row_gate_equals_the_filter_applied_to_that_row(self) -> None:
        pdp = _pdp()
        for subject, action, resource, target in _cross_product(pdp):
            gate = pdp.authorize(subject, action, resource, target_scope=target).allowed
            filtered = pdp.authorize_filter(
                subject, action, resource.table, target_scope=target
            ).matches(resource)
            assert gate == filtered, (
                f"split brain: authorize={gate} but authorize_filter().matches()={filtered} "
                f"for {subject.role}/{action} on {resource.scope}/{resource.table} "
                f"(target_scope={target})"
            )


# =========================================================================== #
# F4 — the mutating (audited) action set is DERIVED from Action, not a hand-list
# =========================================================================== #


class TestMutatingActionsAreDerived:
    """F4 (reach law): the mutating (audited) action set is DERIVED — {every Action} − {READ} — so
    a NEW mutating action auto-audits; a hand-list would silently miss it. Pinned behaviorally: for
    an admin CROSS-owner, EVERY non-READ action requires_audit (it IS treated as mutating), and
    READ never does. This iterates ``pdp.Action`` (so a new action joins the ∀ automatically); a
    build whose mutating set omits it → that action's admin-cross-owner ``requires_audit`` is False
    → RED."""

    def test_every_non_read_action_is_treated_as_mutating(self) -> None:
        pdp = _pdp()
        admin = _admin(pdp)  # alice/ag_a, keeps={}
        bob_private = _resource(
            pdp,
            table=_GOV,
            owner_principal="bob",
            owner_agent="ag_c",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        for action in pdp.Action:
            if action is pdp.Action.READ:
                continue
            # SET_SCOPE needs a target admin cannot grant (keeps={}) so the bypass is load-bearing
            target = pdp.keep_scope("k9") if action is pdp.Action.SET_SCOPE else None
            decision = pdp.authorize(admin, action, bob_private, target_scope=target)
            assert decision.requires_audit is True, (
                f"admin cross-owner {action.name} must be audited (it is mutating). A mutating set "
                "that omits it under-audits — F4: derive from Action, never a hand-list."
            )

    def test_read_is_not_treated_as_mutating(self) -> None:
        pdp = _pdp()
        admin = _admin(pdp)
        bob_private = _resource(
            pdp,
            table=_GOV,
            owner_principal="bob",
            owner_agent="ag_c",
            scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
        )
        assert pdp.authorize(admin, pdp.Action.READ, bob_private).requires_audit is False


# =========================================================================== #
# F3 — the lorerunes stdlib-only CHARTER (reach law on the charter itself)
# =========================================================================== #


def _lorerunes_modules() -> list[Path]:
    """Every lorerunes PRODUCTION module (derived from the installed package dir — not a
    hand-list, so a NEW module is scanned automatically: coverage-as-checked-variable)."""
    package = importlib.import_module(_PACKAGE)
    package_file = package.__file__
    assert package_file is not None, "lorerunes has no __file__ — cannot scan the charter"
    return sorted(Path(package_file).resolve().parent.glob("*.py"))


class TestLorerunesStdlibOnlyCharter:
    """lorerunes depends on NOTHING but the stdlib — its charter (``pyproject dependencies == []``).
    F3 corrects Fork D: Subject/Resource are stdlib dataclasses, NOT pydantic, because a pydantic
    import here breaks lorerunes' importability by every sibling. NOTHING currently guards the
    charter, so this is the reach-law guard: ONE property — every TOP-LEVEL import in EVERY
    lorerunes module is stdlib-or-itself — catches pydantic, any external dep, AND any sibling.
    The 'stdlib' set is DERIVED from ``sys.stdlib_module_names`` (the interpreter's AUTHORITATIVE
    set), NEVER a hand-list. Mutation-prove: add ``import pydantic`` to a lorerunes module → RED."""

    def test_the_module_set_is_non_empty(self) -> None:
        """Guard the guard (INSTRUMENT-0): a broken derivation must fail, not vacuously pass."""
        assert _lorerunes_modules(), "no lorerunes modules found — the charter scan is vacuous"

    def test_every_lorerunes_module_imports_only_stdlib_or_itself(self) -> None:
        allowed = set(sys.stdlib_module_names) | {_PACKAGE}
        offenders: dict[str, set[str]] = {}
        for module_path in _lorerunes_modules():
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in tree.body:  # TOP-LEVEL imports only (module body, not in-function)
                roots: list[str] = []
                if isinstance(node, ast.Import):
                    roots = [alias.name.split(".")[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    roots = [(node.module or "").split(".")[0]]
                for root in roots:
                    if root and root not in allowed:
                        offenders.setdefault(module_path.name, set()).add(root)
        assert not offenders, (
            f"lorerunes CHARTER VIOLATED — non-stdlib top-level import(s) {offenders}. lorerunes "
            "depends on nothing but the stdlib (deps==[]); a third-party (e.g. pydantic) or "
            "sibling (loremaster/loresigil/lorescribe) import breaks its importability by every "
            "other member (F3 / the lorerunes charter)."
        )

    def test_pyproject_declares_no_dependencies(self) -> None:
        """Belt-and-braces (the charter, machine-checkable at the manifest): deps == []."""
        package = importlib.import_module(_PACKAGE)
        package_file = package.__file__
        assert package_file is not None
        pyproject = Path(package_file).resolve().parent.parent / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        deps = data.get("project", {}).get("dependencies", [])
        assert deps == [], f"lorerunes pyproject declares dependencies {deps} — must be [] (charter)"
