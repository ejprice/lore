"""Contract — packet 61a-w4, the append-only ``audit`` table SCHEMA (the store substrate).

Written by ``contract-61a-w4`` (session ``pkt61``, 2026-08-23). The builder builds FROM
this; it writes NO production code. *Every "RED before <sha>" claim is scoped to the tree
at ``e92bd0f`` (branch ``feat/surreal-unification``): at HEAD there is NO ``audit`` table —
the tdd STUB phase adds the minimal surface (``AUDIT_TABLE``, ``_AUDITED_ACTIONS``,
``_audit_statements`` returning ``[]``, ``generate_audit_ddl`` returning ``""``), so every
pin below fails BEHAVIOURALLY, never on an ImportError.* The required stub surface is
enumerated in ``REPORT-contract-61a-w4.md``.

SPEC (the work order, executed verbatim — never re-transcribed):
``docs/design/2026-08-22-packet61-pdp-audit-rulings.md`` §Fork G — the greenfield ``audit``
table (actor ``(principal, agent)`` stamp, ``action`` over the MUTATING actions, target
table+row, ``old_value``/``new_value``, ``created_at``), ``ulid()`` id, folded into
``generate_ddl`` AFTER ``_member_of_statements()``, indexes DEFERRED. The 48/49/60 house
``(name, type_expr, constraint)`` emission format is MIRRORED from
``surreal_schema::_keep_statements``/``_principal_statements`` + ``generate_keep_ddl``.

STORE LAW binds (``docs/reference/surrealdb-31-capabilities.md``, cited never
re-transcribed): §1.1 (TABLE ``IF NOT EXISTS``, FIELD ``OVERWRITE`` — #107; ``ALTER`` is a
trap §1.3), §1.4 (a NEW table is GREENFIELD — required non-``option`` fields are legal at
birth, so ``option<>`` bites only the 63/64 retrofit, NOT here), §2 (CONTENT writes,
``type::record`` binds, ``str(RecordID)`` round-trips, an explicit projection reads a NONE
``option<>`` column back as ``None`` while ``SELECT *`` OMITS it, ``object FLEXIBLE`` keeps
arbitrary keys §1.7), §3 (a multi-statement ``query()`` validates ``statement[0]`` only —
DDL applies through ``execute_transaction``).

⚠ THE 61a/61b BOUNDARY (held): w4 builds ONLY the STORE SUBSTRATE. This contract pins the
``audit`` table + fields + the mutation-provable ``action`` domain + the fold + the live
round-trip. It does NOT pin ``requires_audit`` (a ``Decision`` field computed inside the
PDP's ``authorize`` — 61b) NOR the PDP admin short-circuit's ``audit`` carve-out
(``authorize(admin, DELETE, audit)=DENY`` — 61b, needs the PDP). Those are Fork G pins
whose HOME is 61b.

⚠ FLAG (surfaced per brief-base §2): Fork G's fold rationale says ``actor_principal``/
``actor_agent`` "reference principal/agent, which are defined earlier" in ``generate_ddl``.
``principal`` IS folded there; ``agent`` is NOT (only ``generate_agent_ddl`` standalone —
``surreal_schema.py``). The fold is nonetheless SOUND because a ``record<t>`` field-def does
not require its target table to pre-exist at DDL time (``principal_keys.py`` docstring, and
PROVEN by ``TestTheFullDdlWithAuditFoldedApplies`` here + the satisfiability receipt). See
``REPORT-contract-61a-w4.md``.

LIVE store: ws://127.0.0.1:18000 (NEVER :18500). NO skip marker — an unreachable store is a
LOUD failure, not a skip.
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from _enforced_relations_scaffold import apply_ddl
from _surreal_harness import (
    NONDEFAULT_DIM,
    SurrealConnection,
    SurrealEnv,
    admin_db,  # noqa: F401 - re-exported pytest fixture
    run,
)
from loremaster.store import surreal_schema

# The audit schema surface packet 61a-w4 adds. The tdd STUB phase makes these importable
# (``_audit_statements`` → ``[]``, ``generate_audit_ddl`` → ``""``), so the pins fail
# BEHAVIOURALLY, never on a missing symbol (the ``test_keeps_schema`` RED-STUB precedent).
from loremaster.store.surreal_schema import (
    _AUDITED_ACTIONS,
    AGENT_TABLE,
    AUDIT_TABLE,
    PRINCIPAL_TABLE,
    generate_audit_ddl,
    generate_ddl,
)

_DEFINE_TABLE = re.compile(r"^\s*DEFINE\s+TABLE\b", re.IGNORECASE)
_DEFINE_FIELD = re.compile(r"^\s*DEFINE\s+FIELD\b", re.IGNORECASE)
_DEFINE_INDEX = re.compile(r"^\s*DEFINE\s+INDEX\b", re.IGNORECASE)

# The RULED action domain — the MUTATING actions (Fork G / Fork C). READ is NEVER audited.
_RULED_AUDITED_ACTIONS = {"WRITE", "DELETE", "SET_SCOPE", "SET_OWNER"}

# A distinct, deterministic fixture stamp (FIXTURES MUST DISCRIMINATE — a monoculture of one
# value hides a build that branches on it). ``_ACTOR_EMAIL`` / ``_ACTOR_AGENT_NAME`` are the
# DENORMALIZED human identity captured at write time (Fork G addendum, §9 forensics) — DISTINCT
# from the ``_ACTOR_PRINCIPAL`` / ``_ACTOR_AGENT`` link ids, so a build that stored the id where
# the value belongs (or vice versa) is caught.
_ACTOR_PRINCIPAL = "admin_alice"
_ACTOR_AGENT = "agent_a1"
_ACTOR_EMAIL = "alice@example.com"
_ACTOR_AGENT_NAME = "agent-alice-laptop"
_TARGET_TABLE = "task"
_TARGET_ROW = "task:t_9f3"


def _statements(ddl: str) -> list[str]:
    """The DDL's individual statements, as the transaction will see them."""
    return [line.strip() for line in ddl.split(";") if line.strip()]


def _audit_slice_statements() -> list[str]:
    """The ``audit`` slice's statements (via ``generate_audit_ddl``)."""
    return _statements(generate_audit_ddl())


def _field_statement(all_statements: list[str], table: str, field: str) -> str:
    """The single ``DEFINE FIELD`` for ``table.<field>`` (tolerating ``OVERWRITE``).

    Production emits ``DEFINE FIELD OVERWRITE <name> ON <table>`` (``_define_field``, the
    #107 clause), so ``OVERWRITE`` sits between ``FIELD`` and the name — a naive
    ``\\bFIELD\\s+<name>\\b`` locator would match NOTHING on a correct build.
    """
    matches = [
        statement
        for statement in all_statements
        if _DEFINE_FIELD.match(statement)
        and re.search(rf"\bFIELD\s+(?:OVERWRITE\s+)?{re.escape(field)}\b", statement)
        and f" ON {table} " in f"{statement} "
    ]
    assert len(matches) == 1, (
        f"expected exactly one DEFINE FIELD for {table}.{field}, got {matches!r}"
    )
    return matches[0]


def _audit_table_def(all_statements: list[str]) -> str:
    """The plain ``DEFINE TABLE`` for ``audit`` (there is exactly one; ``audit`` is a NODE
    table, never a RELATION)."""
    table_defs = [
        statement
        for statement in all_statements
        if _DEFINE_TABLE.match(statement) and f" {AUDIT_TABLE} " in f"{statement} "
    ]
    assert len(table_defs) == 1, (
        f"expected exactly one DEFINE TABLE for {AUDIT_TABLE!r}, got {table_defs!r}"
    )
    return table_defs[0]


# --------------------------------------------------------------------------- #
# Live-store seeding helpers.
# --------------------------------------------------------------------------- #


async def _seed_principal(connection: SurrealConnection, principal_id: str) -> None:
    """CREATE a minimal ``principal`` row so ``actor_principal`` names a REAL owner. A
    ``record<principal>`` link does not VALIDATE existence (store §4), but a faithful audit
    row names a real actor."""
    await run(
        connection,
        f"CREATE type::record('{PRINCIPAL_TABLE}', $id) CONTENT {{ email: $email }}",
        {"id": principal_id, "email": f"{principal_id}@example.com"},
    )


async def _write_audit_row(
    connection: SurrealConnection,
    row_id: str,
    *,
    action: str = "WRITE",
    actor_principal: str = _ACTOR_PRINCIPAL,
    actor_agent: str = _ACTOR_AGENT,
    actor_email: str = _ACTOR_EMAIL,
    actor_agent_name: str = _ACTOR_AGENT_NAME,
    target_table: str = _TARGET_TABLE,
    target_row: str = _TARGET_ROW,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    include_action: bool = True,
    include_actor_principal: bool = True,
    include_actor_agent: bool = True,
    include_actor_email: bool = True,
    include_actor_agent_name: bool = True,
    include_target_table: bool = True,
    include_target_row: bool = True,
) -> Any:
    """CREATE one ``audit`` row via a bound CONTENT object (store §2), mirroring how
    ``AuditStore.append`` writes it.

    ``actor_principal``/``actor_agent`` bind as ``type::record(<table>, $id)`` (record
    links, never bare strings — store §2/§4). ``actor_email``/``actor_agent_name`` are the
    DENORMALIZED human-identity VALUE columns (Fork G addendum). ``old_value``/``new_value``
    are written ONLY when provided (so an omitted ``option<object>`` decodes to NONE — a CREATE
    has no old, a DELETE no new). ``created_at`` self-stamps (OMITTED). Required fields may be
    omitted by a negative pin to exercise the REQUIRED discipline.
    """
    fragments: list[str] = []
    params: dict[str, Any] = {"id": row_id}
    if include_actor_principal:
        fragments.append(f"actor_principal: type::record('{PRINCIPAL_TABLE}', $ap)")
        params["ap"] = actor_principal
    if include_actor_agent:
        fragments.append(f"actor_agent: type::record('{AGENT_TABLE}', $aa)")
        params["aa"] = actor_agent
    if include_actor_email:
        fragments.append("actor_email: $ae")
        params["ae"] = actor_email
    if include_actor_agent_name:
        fragments.append("actor_agent_name: $aan")
        params["aan"] = actor_agent_name
    if include_action:
        fragments.append("action: $action")
        params["action"] = action
    if include_target_table:
        fragments.append("target_table: $tt")
        params["tt"] = target_table
    if include_target_row:
        fragments.append("target_row: $tr")
        params["tr"] = target_row
    if old_value is not None:
        fragments.append("old_value: $old")
        params["old"] = old_value
    if new_value is not None:
        fragments.append("new_value: $new")
        params["new"] = new_value
    return await run(
        connection,
        f"CREATE type::record('{AUDIT_TABLE}', $id) CONTENT {{ {', '.join(fragments)} }}",
        params,
    )


_AUDIT_READ_PROJECTION = (
    "actor_principal, actor_agent, actor_email, actor_agent_name, action, "
    "target_table, target_row, old_value, new_value, created_at"
)


async def _read_audit_row(connection: SurrealConnection, row_id: str) -> Any:
    """Read one ``audit`` row through an EXPLICIT projection (store §2: an explicit
    projection reads a NONE ``option<>`` column back as ``None``, where ``SELECT *`` OMITS
    it and a later bracket access ``KeyError``s — the always-NONE ``old_value``/``new_value``
    on a CREATE/DELETE make that a real hazard)."""
    rows = await run(
        connection,
        f"SELECT {_AUDIT_READ_PROJECTION} FROM type::record('{AUDIT_TABLE}', $id)",
        {"id": row_id},
    )
    assert rows, f"expected one audit row for {row_id!r}, got {rows!r}"
    return rows[0]


# =========================================================================== #
# LEG 1 — OFFLINE DDL pins (no server; string-level over the generator output).
# =========================================================================== #


class TestTheAuditDdlDecisionRuleIsEnforcedMechanically:
    """Store reference §1.1. Each pin names the failure it prevents — a clause is invisible
    in review and catastrophic in production (#107)."""

    def test_the_audit_table_definition_is_SCHEMAFULL_IF_NOT_EXISTS(self) -> None:
        statement = _audit_table_def(_audit_slice_statements())
        assert "IF NOT EXISTS" in statement.upper(), (
            f"the audit table must be `IF NOT EXISTS` (§1.1): {statement!r}"
        )
        assert "SCHEMAFULL" in statement.upper(), (
            f"the audit table must be SCHEMAFULL (undeclared keys rejected, §1.7): {statement!r}"
        )
        assert "TYPE RELATION" not in statement.upper(), (
            f"audit is a NODE table, never a RELATION: {statement!r}"
        )

    def test_every_audit_field_definition_is_OVERWRITE(self) -> None:
        """#107, verbatim: ``IF NOT EXISTS`` on an existing field silently keeps the OLD
        definition, so a changed ASSERT never reaches a live store. Only ``OVERWRITE``
        migrates."""
        offenders = [
            statement
            for statement in _audit_slice_statements()
            if _DEFINE_FIELD.match(statement) and "OVERWRITE" not in statement.upper()
        ]
        assert not offenders, (
            f"every audit FIELD must be `DEFINE FIELD OVERWRITE` (#107): {offenders}"
        )

    def test_no_audit_field_definition_uses_IF_NOT_EXISTS(self) -> None:
        """The same rule from the other side — a build emitting BOTH clauses would pass the
        pin above."""
        offenders = [
            statement
            for statement in _audit_slice_statements()
            if _DEFINE_FIELD.match(statement) and "IF NOT EXISTS" in statement.upper()
        ]
        assert not offenders, offenders

    def test_the_word_ALTER_appears_in_no_statement(self) -> None:
        """§1.3: ``ALTER`` cannot CREATE a field, and ``ALTER … IF EXISTS`` on a missing one
        silently no-ops — adopting it re-commits #107 on the fresh-DB path."""
        offenders = [
            statement
            for statement in _audit_slice_statements()
            if re.search(r"\bALTER\b", statement, re.I)
        ]
        assert not offenders, offenders

    def test_the_generator_returns_the_house_terminated_shape(self) -> None:
        """Every other ``generate_*_ddl`` returns ``";\\n".join(...) + ";\\n"``. A slice that
        did not would break the caller's ``BEGIN … COMMIT`` wrap."""
        ddl = generate_audit_ddl()
        assert ddl.endswith(";\n")
        assert _statements(ddl)

    def test_the_generator_emits_audit_fields_not_just_the_table_name(self) -> None:
        """CONTROL: a generator emitting a bare ``DEFINE TABLE`` and ZERO ``DEFINE FIELD``
        would make ``test_every_audit_field_definition_is_OVERWRITE`` vacuously green — the
        signature failure of a mechanical gate. It DEMANDS fields."""
        fields = [
            statement
            for statement in _audit_slice_statements()
            if _DEFINE_FIELD.match(statement) and f" ON {AUDIT_TABLE} " in f"{statement} "
        ]
        assert fields, f"the slice for {AUDIT_TABLE!r} emits no DEFINE FIELD at all"

    def test_the_audit_slice_ROUTES_THROUGH_the_shared_field_emitter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ONE IMPLEMENTATION, proven by MUTATION: nothing REQUIRES the audit slice to CALL
        ``_define_field`` — a hand-written ``DEFINE FIELD`` string would pass every clause pin
        while silently not sharing the #107 ``OVERWRITE`` policy. Perturb the shared emitter;
        the emitted DDL must move (the ``_keep_statements`` precedent)."""
        original = surreal_schema._define_field
        monkeypatch.setattr(
            surreal_schema,
            "_define_field",
            lambda *args, **kwargs: f"{original(*args, **kwargs)} COMMENT 'audit-mutation-probe'",
        )
        assert "audit-mutation-probe" in generate_audit_ddl(), (
            "the audit slice does not route through surreal_schema._define_field"
        )

    def test_the_audit_table_uses_the_shared_define_table_emitter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ONE IMPLEMENTATION, by MUTATION: the ``audit`` table must be emitted by the SHARED
        ``_define_table`` (which owns the SCHEMAFULL ``IF NOT EXISTS`` policy), not a
        hand-written string."""
        original = surreal_schema._define_table
        monkeypatch.setattr(
            surreal_schema,
            "_define_table",
            lambda name: f"{original(name)} COMMENT 'audit-table-probe'",
        )
        assert "audit-table-probe" in generate_audit_ddl(), (
            "the audit slice does not route through surreal_schema._define_table"
        )


class TestTheAuditFieldSet:
    """Fork G's ``(name, type_expr, constraint)`` field set — the exact shapes that make the
    row a faithful, queryable trail."""

    def test_actor_principal_is_a_required_record_principal_link(self) -> None:
        """Fork G: ``actor_principal record<principal>`` — the ``(principal, agent)`` stamp's
        principal half. Required (non-``option``) — GREENFIELD table, §1.4 N/A (design note).
        A record LINK (mirrors ``keep.keeper``), never a bare string."""
        statement = _field_statement(_audit_slice_statements(), AUDIT_TABLE, "actor_principal")
        assert f"record<{PRINCIPAL_TABLE}>" in statement, (
            f"actor_principal must be a record<{PRINCIPAL_TABLE}> link: {statement!r}"
        )
        assert "OPTION" not in statement.upper(), (
            f"actor_principal is REQUIRED at birth (greenfield, §1.4 N/A): {statement!r}"
        )

    def test_actor_agent_is_a_required_record_agent_link(self) -> None:
        """Fork G: ``actor_agent record<agent>`` — the agent that carried the action.
        Required. ⚠ ``agent`` is NOT folded into ``generate_ddl`` (only ``generate_agent_ddl``
        standalone); the fold is sound because a ``record<t>`` field-def needs no target table
        at DDL time (proven by ``TestTheFullDdlWithAuditFoldedApplies``)."""
        statement = _field_statement(_audit_slice_statements(), AUDIT_TABLE, "actor_agent")
        assert f"record<{AGENT_TABLE}>" in statement, (
            f"actor_agent must be a record<{AGENT_TABLE}> link: {statement!r}"
        )
        assert "OPTION" not in statement.upper(), (
            f"actor_agent is REQUIRED at birth (greenfield, §1.4 N/A): {statement!r}"
        )

    def test_actor_email_and_actor_agent_name_are_required_non_empty_string_VALUES(self) -> None:
        """⚠ Fork G addendum (§9 forensics): ``actor_email`` + ``actor_agent_name`` are
        DENORMALIZED human-identity VALUE columns — plain ``string`` (NOT ``record<>`` links),
        REQUIRED and non-empty. They are captured at APPEND time so the human identity survives
        as VALUES even when the ``actor_principal``/``actor_agent`` LINKS dangle on a
        principal-delete (the survives-delete pin proves the payoff). A build that made either a
        ``record<>`` link (deref → NONE after delete) instead of a value defeats the forensics."""
        for field in ("actor_email", "actor_agent_name"):
            statement = _field_statement(_audit_slice_statements(), AUDIT_TABLE, field)
            assert "TYPE STRING" in statement.upper(), (
                f"{field} must be a plain string VALUE, NOT a record<> link (it must survive a "
                f"link-target delete — Fork G §9 forensics): {statement!r}"
            )
            assert "RECORD<" not in statement.upper(), (
                f"{field} must NOT be a record<> link — a link derefs to NONE once its target is "
                f"deleted, losing the identity the trail exists to preserve: {statement!r}"
            )
            assert "ASSERT" in statement.upper() and "STRING::LEN" in statement.upper(), (
                f"{field} must carry the trim-aware non-empty ASSERT (a forensic value is never "
                f"blank): {statement!r}"
            )
            assert "OPTION" not in statement.upper(), (
                f"{field} is REQUIRED — a principal always has an email and an agent always has a "
                f"name (agent.name is a required identifier field, verified against the substrate): "
                f"{statement!r}"
            )

    def test_target_table_and_target_row_are_non_empty_strings(self) -> None:
        """Fork G: ``target_table``/``target_row`` are ``string`` carrying the trim-aware
        non-empty ASSERT (the ``_NON_EMPTY_STRING_ASSERT`` idiom). ``target_row`` is the
        ``str(RecordID)`` of the affected row (store §2 — a RecordID's string component can't
        be indexed/prefix-matched, so it lives as a queryable value column). A closed domain
        for ``target_table`` would be a hand-list of governed tables that do NOT exist until
        63/64 — the reach-law trap; a non-empty string is correct (deferred)."""
        for field in ("target_table", "target_row"):
            statement = _field_statement(_audit_slice_statements(), AUDIT_TABLE, field)
            assert "TYPE STRING" in statement.upper(), f"{field} must be a string: {statement!r}"
            assert "ASSERT" in statement.upper() and "STRING::LEN" in statement.upper(), (
                f"{field} must carry the trim-aware non-empty ASSERT: {statement!r}"
            )
            assert "OPTION" not in statement.upper(), f"{field} is required: {statement!r}"

    def test_target_table_is_NOT_a_closed_domain(self) -> None:
        """Fork G / the reach law: ``target_table`` must NOT carry a closed ``$value IN [...]``
        ASSERT — the governed tables it would enumerate do not exist until 63/64, so a closed
        list here is the hidden-constant reach trap. A non-empty string, open by design."""
        statement = _field_statement(_audit_slice_statements(), AUDIT_TABLE, "target_table")
        assert "$VALUE IN" not in statement.upper(), (
            f"target_table must be an OPEN non-empty string, not a closed `$value IN [...]` domain "
            f"(reach-law trap — governed tables don't exist until 63/64): {statement!r}"
        )

    def test_old_value_and_new_value_are_optional_flexible_objects(self) -> None:
        """Fork G: ``old_value``/``new_value`` are ``option<object> FLEXIBLE`` — ``option<>``
        because a CREATE/SET_OWNER-from-nothing has no old and a DELETE no new; FLEXIBLE so an
        arbitrary row shape round-trips (§1.7)."""
        for field in ("old_value", "new_value"):
            statement = _field_statement(_audit_slice_statements(), AUDIT_TABLE, field)
            normalised = statement.upper().replace(" ", "")
            assert "OPTION<OBJECT>" in normalised, (
                f"{field} must be TYPE option<object> (a CREATE has no old, a DELETE no new): "
                f"{statement!r}"
            )
            assert "FLEXIBLE" in statement.upper(), (
                f"{field} must be FLEXIBLE (arbitrary before/after row shape, §1.7): {statement!r}"
            )

    def test_created_at_self_stamps_via_default_time_now(self) -> None:
        """Fork G: ``created_at datetime DEFAULT time::now()`` — engine-stamped; the store
        OMITS it on write (the ``finding``/``keep.created_at`` idiom)."""
        statement = _field_statement(_audit_slice_statements(), AUDIT_TABLE, "created_at")
        normalised = statement.upper().replace(" ", "")
        assert "TYPEDATETIME" in normalised, f"created_at must be a datetime: {statement!r}"
        assert "DEFAULTTIME::NOW()" in normalised, (
            f"created_at must DEFAULT time::now() (engine-stamped): {statement!r}"
        )

    def test_the_audit_slice_emits_NO_index(self) -> None:
        """⚠ PIN THE MISS (#137/#138 — when you cannot/should-not close a hole, pin it). Fork
        G DEFERS indexes: 61 ships no audit-query verb, so shipping an ``actor_principal`` /
        ``created_at`` index now would be a guard over a query nobody makes. This pins the
        deferral as a KNOWN BOUND. RE-OPEN TRIGGER: the first audit LISTING verb (an admin
        tool, 63/64+) — add ``actor_principal`` + ``created_at`` indexes then (a free
        ``IF NOT EXISTS`` add) and DELETE this pin, saying so."""
        indexes = [
            statement
            for statement in _audit_slice_statements()
            if _DEFINE_INDEX.match(statement) and re.search(rf"\bON\s+{AUDIT_TABLE}\b", statement)
        ]
        assert not indexes, (
            f"the audit slice emits an index while 61 ships no audit-query verb — Fork G DEFERS "
            f"indexes (KNOWN BOUND). If a listing verb landed, delete this pin and say so: {indexes}"
        )


class TestTheAuditActionDomainIsDerivedIntoTheDdl:
    """ONE IMPLEMENTATION + THE QUANTIFIER PIN, proven by MUTATION rather than by reading the
    source. The ``action`` ASSERT must be GENERATED FROM ``_AUDITED_ACTIONS`` at CALL TIME
    (the ``_principal_statements`` / ``_keep_statements`` idiom), never hand-typed beside it —
    a frozen import-time ASSERT cannot move under a runtime monkeypatch of the tuple."""

    def test_changing_the_AUDITED_ACTIONS_tuple_changes_the_emitted_ASSERT(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        before = generate_audit_ddl()
        monkeypatch.setattr(
            surreal_schema,
            "_AUDITED_ACTIONS",
            (*surreal_schema._AUDITED_ACTIONS, "MUTATION_PROBE_ACTION"),
        )
        after = generate_audit_ddl()
        assert after != before, (
            "adding an audited action changed no emitted DDL — the action ASSERT is a hand-typed "
            "twin of _AUDITED_ACTIONS (or a frozen import-time constant) rather than a CALL-TIME "
            "derivation"
        )
        assert "MUTATION_PROBE_ACTION" in after

    def test_every_audited_action_reaches_the_ddl(self) -> None:
        """Membership control alongside the mutation pin: an over-narrow ASSERT that dropped a
        legal action would silently break that action's audit forever."""
        ddl = generate_audit_ddl()
        missing = [value for value in _AUDITED_ACTIONS if f"'{value}'" not in ddl]
        assert not missing, f"audited actions absent from the DDL: {missing}"

    def test_the_action_field_carries_the_closed_domain_assert_and_no_default(self) -> None:
        """The ``action`` field is a closed-domain string ASSERT with NO ``DEFAULT`` — every
        append must NAME its action (a silent default would mislabel the trail)."""
        statement = _field_statement(_audit_slice_statements(), AUDIT_TABLE, "action")
        upper = statement.upper()
        assert "ASSERT" in upper and "$VALUE IN" in upper, (
            f"action must carry the closed-domain `ASSERT $value IN [...]`: {statement!r}"
        )
        assert "DEFAULT" not in upper, (
            f"action must carry NO DEFAULT — every append names its action: {statement!r}"
        )

    def test_the_ruled_action_domain_is_EXACTLY_the_mutating_actions(self) -> None:
        """⚠ THE QUANTIFIER PIN (pin the RULED SET ∀, not just known-good/known-bad). The
        derivation + membership pins ALL PASS on a build that WIDENS the domain (adds a value
        to ``_AUDITED_ACTIONS``): the ASSERT still derives from the tuple and every ruled value
        still reaches the DDL. A widening slips through unless the set itself is an invariant.
        Fork G / Fork C: the MUTATING actions {WRITE, DELETE, SET_SCOPE, SET_OWNER}."""
        assert set(_AUDITED_ACTIONS) == _RULED_AUDITED_ACTIONS, (
            f"the ruled audited-action domain is {sorted(_RULED_AUDITED_ACTIONS)} (Fork G/C); "
            f"_AUDITED_ACTIONS={_AUDITED_ACTIONS!r} — if you changed it deliberately, update this "
            f"pin and say so"
        )

    def test_READ_is_NOT_an_audited_action(self) -> None:
        """Fork G, load-bearing: READ is NEVER audited (a read exercises no admin POWER). If
        READ leaked into ``_AUDITED_ACTIONS`` the store would accept audit rows for reads —
        the exact over-audit Fork G rules out. Discriminates the mutating-only set from the
        full Action taxonomy {READ, WRITE, DELETE, SET_SCOPE, SET_OWNER}."""
        assert "READ" not in set(_AUDITED_ACTIONS), (
            f"READ must NOT be an audited action (reads exercise no admin power — Fork G): "
            f"_AUDITED_ACTIONS={_AUDITED_ACTIONS!r}"
        )


class TestTheAuditSliceIsFoldedIntoGenerateDdl:
    """Fork G / the w3 fold-coverage guard (``_schema_fold_guard.py``): ``_audit_statements``
    must be FOLDED into ``generate_ddl`` AFTER ``_member_of_statements()`` (else the primary
    ``write_store.ensure_ready()`` never creates the table, and the fold guard reds)."""

    def test_audit_is_folded_into_the_global_generate_ddl(self) -> None:
        """Fork G: folded so the primary store readies ``audit`` at ship — without wiring an
        ``AuditStore`` into ``build_app_context``. A build that shipped only the standalone
        slice would leave production without the table until a store is wired in (the
        ``keep``/Emission-plan precedent). Also what keeps the w3 STRUCTURAL fold-coverage
        guard green."""
        full = generate_ddl(dim=NONDEFAULT_DIM)
        assert f"DEFINE TABLE IF NOT EXISTS {AUDIT_TABLE} SCHEMAFULL" in full, (
            "audit is NOT folded into generate_ddl() — the table will not exist in production "
            "until an AuditStore is wired in (Fork G / the w3 fold guard reds)"
        )
        assert any(
            _DEFINE_FIELD.match(statement) and f" ON {AUDIT_TABLE} " in f"{statement} "
            for statement in _statements(full)
        ), "generate_ddl() carries the audit table but none of its fields"

    def test_audit_is_folded_AFTER_member_of(self) -> None:
        """Fork G RULING: folded AFTER ``_member_of_statements()``. (The load-bearing ordering
        constraint is only that ``audit`` follow ``principal`` — its ``actor_principal`` link
        target; ``agent`` need not precede, since a ``record<t>`` field-def needs no target
        table. But the ruling pins the position after member_of, executed here verbatim.)"""
        emitted = _statements(generate_ddl(dim=NONDEFAULT_DIM))
        audit_at = next(
            (
                i
                for i, s in enumerate(emitted)
                if s.startswith(f"DEFINE TABLE IF NOT EXISTS {AUDIT_TABLE} ")
            ),
            None,
        )
        member_of_at = next(
            (i for i, s in enumerate(emitted) if " member_of TYPE RELATION" in s), None
        )
        principal_at = next(
            (
                i
                for i, s in enumerate(emitted)
                if s.startswith(f"DEFINE TABLE IF NOT EXISTS {PRINCIPAL_TABLE} ")
            ),
            None,
        )
        assert audit_at is not None, "generate_ddl emits no DEFINE TABLE for audit"
        assert member_of_at is not None, "generate_ddl emits no member_of relation table"
        assert principal_at is not None, "generate_ddl emits no principal table"
        assert principal_at < audit_at, (
            f"audit (pos {audit_at}) must follow its actor_principal link target principal "
            f"(pos {principal_at})"
        )
        assert member_of_at < audit_at, (
            f"Fork G: audit (pos {audit_at}) is folded AFTER member_of (pos {member_of_at})"
        )

    def test_the_audit_slice_is_emitted_IDENTICALLY_by_both_paths(self) -> None:
        """The audit table+fields must be emitted IDENTICALLY by ``generate_audit_ddl`` (a
        future ``AuditStore.ensure_ready``) AND folded into ``generate_ddl`` (the primary
        store). DERIVED equality — one emitter (``_audit_statements``) consumed by both — not
        two hand-written expectations that could agree with each other and disagree with
        production (the ``member_of`` both-paths precedent)."""
        slice_fields = {
            s
            for s in _audit_slice_statements()
            if _DEFINE_FIELD.match(s) and f" ON {AUDIT_TABLE} " in f"{s} "
        }
        full_fields = {
            s
            for s in _statements(generate_ddl(dim=NONDEFAULT_DIM))
            if _DEFINE_FIELD.match(s) and f" ON {AUDIT_TABLE} " in f"{s} "
        }
        assert slice_fields, "generate_audit_ddl emits no audit fields"
        assert slice_fields == full_fields, (
            "generate_audit_ddl and generate_ddl emit DIFFERENT audit field definitions — there "
            f"must be one emitter (_audit_statements) consumed by both. slice_only="
            f"{sorted(slice_fields - full_fields)} full_only={sorted(full_fields - slice_fields)}"
        )


# =========================================================================== #
# LEG 2 — LIVE round-trip on ws://127.0.0.1:18000 (NEVER :18500). NO skip marker:
# an unreachable store is a LOUD failure, not a skip.
# =========================================================================== #


class TestTheAuditSchemaAppliesToTheLiveEngine:
    """The generated DDL against the real engine — the recipe proven on the cake."""

    async def test_generate_audit_ddl_creates_the_audit_table(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """The standalone slice (a future ``AuditStore.ensure_ready``) applies cleanly and the
        table exists — even though NEITHER ``principal`` NOR ``agent`` is applied first (a
        ``record<t>`` field-def needs no target table at DDL time — ``principal_keys.py``)."""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        tables = set((await run(connection, "INFO FOR DB")).get("tables", {}))
        assert AUDIT_TABLE in tables, f"the audit table was not created: {sorted(tables)}"

    async def test_the_slice_is_safely_re_appliable(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """``ensure_ready`` re-applies the DDL on EVERY boot. A statement that raises on
        re-application is a boot-time crash, not a style issue."""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)


class TestTheFullDdlWithAuditFoldedApplies:
    """⚠ THE #131/#107-CLASS FOLD-SAFETY PROOF (load-bearing). The audit slice carries a
    ``record<agent>`` field while ``agent`` is NOT emitted by ``generate_ddl`` (only
    ``generate_agent_ddl`` standalone). If a ``record<t>`` field-def REQUIRED its target table
    to pre-exist, folding ``audit`` into ``generate_ddl`` would CRASH the primary
    ``write_store.ensure_ready()`` at boot — invisible to every offline pin, a production-only
    outage (the #131 shape). This applies the WHOLE folded ``generate_ddl`` to the live engine
    and proves it does not."""

    async def test_the_full_generate_ddl_applies_with_audit_folded(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, env = admin_db
        await apply_ddl(connection, generate_ddl(dim=NONDEFAULT_DIM), url=env.url)
        tables = set((await run(connection, "INFO FOR DB")).get("tables", {}))
        assert AUDIT_TABLE in tables, (
            f"generate_ddl (audit folded) did not create the audit table — a record<agent> "
            f"field over an absent agent table may have crashed the boot DDL: {sorted(tables)}"
        )

    async def test_the_full_generate_ddl_is_re_appliable(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Re-applied every boot (``ensure_ready``) — a second apply must be a clean no-op."""
        connection, env = admin_db
        await apply_ddl(connection, generate_ddl(dim=NONDEFAULT_DIM), url=env.url)
        await apply_ddl(connection, generate_ddl(dim=NONDEFAULT_DIM), url=env.url)


class TestTheAuditRowRoundTrip:
    """The ``audit`` table (live behavioural) — Fork G's property set."""

    async def test_a_write_audit_row_reads_back_with_the_exact_values(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """A WRITE record captures ``old_value`` + ``new_value`` (Fork G old→new). The actor
        stamp, action, target and both states round-trip."""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        await _write_audit_row(
            connection,
            "aw1",
            action="WRITE",
            old_value={"status": "open", "owner_agent": "agent_b2"},
            new_value={"status": "done", "owner_agent": "agent_b2"},
        )
        row = await _read_audit_row(connection, "aw1")
        assert row["action"] == "WRITE"
        assert str(row["actor_principal"]).endswith(_ACTOR_PRINCIPAL)
        assert str(row["actor_agent"]).endswith(_ACTOR_AGENT)
        assert row["actor_email"] == _ACTOR_EMAIL, "the denormalized actor_email did not round-trip"
        assert row["actor_agent_name"] == _ACTOR_AGENT_NAME, (
            "the denormalized actor_agent_name did not round-trip"
        )
        assert row["target_table"] == _TARGET_TABLE
        assert row["target_row"] == _TARGET_ROW
        assert row["old_value"] == {"status": "open", "owner_agent": "agent_b2"}
        assert row["new_value"] == {"status": "done", "owner_agent": "agent_b2"}
        assert row["created_at"] is not None, "created_at did not self-stamp"

    async def test_a_delete_audit_row_has_old_value_and_a_NONE_new_value(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Fork G old→new: a DELETE records ``old_value`` (the vanished state) + ``new_value``
        NONE. Read through the explicit projection so the omitted ``option<>`` reads as
        ``None`` (store §2 — ``SELECT *`` would omit the key and ``KeyError``)."""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        await _write_audit_row(
            connection,
            "ad1",
            action="DELETE",
            old_value={"body": "the finding text", "status": "open"},
            new_value=None,  # a DELETE has no after-state
        )
        row = await _read_audit_row(connection, "ad1")
        assert row["action"] == "DELETE"
        assert row["old_value"] == {"body": "the finding text", "status": "open"}
        assert row["new_value"] is None, "a DELETE's new_value must be NONE (read back as None)"

    async def test_a_create_shaped_audit_row_has_a_NONE_old_value(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """The mirror of the DELETE: a from-nothing action records ``new_value`` + a NONE
        ``old_value``. Both ``option<>`` directions exercised (the discrimination the DELETE
        pin needs)."""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        await _write_audit_row(
            connection,
            "ac1",
            action="SET_OWNER",
            old_value=None,
            new_value={"owner_principal": "member_carol", "owner_agent": "agent_c3"},
        )
        row = await _read_audit_row(connection, "ac1")
        assert row["old_value"] is None, "a from-nothing action's old_value must be NONE"
        assert row["new_value"] == {"owner_principal": "member_carol", "owner_agent": "agent_c3"}

    async def test_old_and_new_value_round_trip_an_ARBITRARY_nested_shape(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Fork G: ``old_value``/``new_value`` are ``object FLEXIBLE`` — a governed row of ANY
        shape (nested objects, lists, undeclared keys) round-trips intact (§1.7). A non-FLEXIBLE
        object would reject undeclared nested keys."""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        hostile = {
            "scope": "keep:k_42",
            "tags": ["a", "b", "c"],
            "nested": {"rank": "contributor", "meta": {"depth": 3}},
            "unexpected_column_63_will_add": "survives",
        }
        await _write_audit_row(connection, "aflex", action="SET_SCOPE", old_value=hostile, new_value=hostile)
        row = await _read_audit_row(connection, "aflex")
        assert row["old_value"] == hostile, "a FLEXIBLE object did not round-trip its arbitrary shape"
        assert row["new_value"] == hostile

    async def test_the_ulid_id_round_trips(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Fork G: the record id is a ``ulid()`` (creation-ordered, sortable — NOT a counter/
        sequence mint that would contend on a hot row). ``str(RecordID)`` round-trips (store
        §2), so a client-minted ulid id reads back cleanly. (``AuditStore.append`` mints it;
        here we prove a ulid-shaped id round-trips.)"""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        ulid_id = "01J8Z9K7Q5R7X0YB3W2V4M6N8T"  # a 26-char Crockford base32 ulid shape
        created = await _write_audit_row(connection, ulid_id, action="WRITE", new_value={"n": 1})
        assert created, "the ulid-id audit row was not created"
        row = await _read_audit_row(connection, ulid_id)
        assert row["action"] == "WRITE"


class TestTheAuditActionAssertLive:
    """The ``action`` closed domain against the real engine — belt-and-braces for the offline
    exact-set pin (which catches a widening THROUGH the tuple; this catches one widened in the
    store's runtime DDL by ANY means)."""

    async def test_a_plausible_but_unaudited_action_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """``READ`` is PLAUSIBLE (a real Action-taxonomy member) but UNAUDITED — a build that
        leaked it into ``_AUDITED_ACTIONS`` would ACCEPT it, so the store MUST reject it. The
        exact over-audit Fork G rules out, caught at the live boundary."""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation (unaudited action)
            await _write_audit_row(connection, "abad", action="READ", new_value={"n": 1})

    async def test_a_garbage_action_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation
            await _write_audit_row(connection, "agarbage", action="NOT_AN_ACTION", new_value={"n": 1})

    async def test_every_audited_action_is_accepted_positive_control(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """THE POSITIVE CONTROL for the rejection pins: an over-strict ASSERT (accepting only
        one action) would silently pass both negatives while breaking every real audit write.
        Every audited action must be accepted."""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        for index, action in enumerate(_AUDITED_ACTIONS):
            await _write_audit_row(connection, f"aok{index}", action=action, new_value={"n": index})
            row = await _read_audit_row(connection, f"aok{index}")
            assert row["action"] == action


class TestTheAuditRequiredFieldDiscipline:
    """Greenfield (§1.4 N/A) — required non-``option`` fields are legal at birth, so an audit
    row missing a required field is rejected."""

    async def test_an_empty_target_table_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """The non-empty ASSERT fires on a present empty string (a garbage ``target_table =
        ''``)."""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation (empty target_table)
            await _write_audit_row(
                connection, "aempty_tt", action="WRITE", target_table="", new_value={"n": 1}
            )

    async def test_an_empty_target_row_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation (empty target_row)
            await _write_audit_row(connection, "aempty_tr", action="WRITE", target_row="", new_value={"n": 1})

    @pytest.mark.parametrize(
        "omit",
        [
            "include_action",
            "include_actor_principal",
            "include_actor_agent",
            "include_actor_email",
            "include_actor_agent_name",
            "include_target_table",
            "include_target_row",
        ],
    )
    async def test_a_row_missing_a_required_field_is_rejected(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
        omit: str,
    ) -> None:
        """Each of the five required fields, ∀: omitting it is rejected (a greenfield table's
        required non-``option`` fields, §1.4 N/A). The ∀ discriminates a build that made any
        one of them accidentally ``option<>``."""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        kwargs: dict[str, Any] = {"action": "WRITE", "new_value": {"n": 1}, omit: False}
        with pytest.raises(Exception):  # noqa: B017 - engine required-field rejection
            await _write_audit_row(connection, "amissing", **kwargs)

    async def test_the_all_required_positive_control_is_accepted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """POSITIVE CONTROL for the omission ∀: with every required field present the row IS
        accepted — so the omission pins fail for the RIGHT reason (a missing field), not
        because the write is broken for all inputs."""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        await _write_audit_row(connection, "aallreq", action="WRITE", new_value={"n": 1})
        row = await _read_audit_row(connection, "aallreq")
        assert row["action"] == "WRITE"

    async def test_audit_rejects_an_undeclared_field(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """SCHEMAFULL discipline (§1.7): an undeclared top-level key RAISES, so a typo'd column
        can never silently become a phantom attribute on the trail."""
        connection, env = admin_db
        await apply_ddl(connection, generate_audit_ddl(), url=env.url)
        await _seed_principal(connection, _ACTOR_PRINCIPAL)
        with pytest.raises(Exception):  # noqa: B017 - engine SCHEMAFULL rejection
            await run(
                connection,
                f"CREATE type::record('{AUDIT_TABLE}', $id) CONTENT "
                f"{{ actor_principal: type::record('{PRINCIPAL_TABLE}', $ap), "
                f"actor_agent: type::record('{AGENT_TABLE}', $aa), "
                f"actor_email: $ae, actor_agent_name: $aan, action: 'WRITE', "
                f"target_table: $tt, target_row: $tr, rogue: 'x' }}",
                {
                    "id": "arogue",
                    "ap": _ACTOR_PRINCIPAL,
                    "aa": _ACTOR_AGENT,
                    "ae": _ACTOR_EMAIL,
                    "aan": _ACTOR_AGENT_NAME,
                    "tt": _TARGET_TABLE,
                    "tr": _TARGET_ROW,
                },
            )
