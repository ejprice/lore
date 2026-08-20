"""Contract — packet 48 Wave 48-B, the ``principal`` table SCHEMA (Legs 1 + 2).

Written by ``contract-48b`` (2026-08-20). The builder builds FROM this; it writes
NO production code.

SPEC (the work order, executed verbatim — never re-transcribed):
``docs/design/2026-08-20-packet48-principals-substrate.md`` §3 (field set + closed
domains + clauses), §4 (``subject`` ``option<string>`` UNIQUE — Model B), §6
(module docstring — pinned in ``test_principals_store.py``), and §8 checklist
items 5–6 (Leg 1 offline DDL pins + Leg 2 live round-trip). Store law binds:
``docs/reference/surrealdb-31-capabilities.md`` §1.1 (TABLE/INDEX ``IF NOT
EXISTS``, FIELD ``OVERWRITE``, ALTER is a trap §1.3), §1.4 (a NEW field on a
POPULATED table must be ``option<>``), §2 (CONTENT writes; ⚠ ``SELECT *`` OMITS a
NONE ``option<>`` column → ``KeyError``, explicit projection reads ``None``).

WHAT THIS FILE DECIDES (the interface freeze the builder implements) —
``loremaster.store.surreal_schema``::

    PRINCIPAL_TABLE = "principal"
    _PRINCIPAL_STATUSES = ("active", "suspended")   # closed domain (status)
    _PRINCIPAL_ROLES    = ("member", "admin")       # closed domain (role)
    generate_principal_ddl() -> str                 # the standalone slice
    # AND ``principal`` FOLDED into the global ``generate_ddl(dim=...)`` (Variant A)

WHY THESE PINS ARE RED NOW (contract-first): none of the symbols above exist.
Every pin calls ``_require_principal_schema()`` FIRST, a dynamic ``getattr`` gate
(the sibling ``test_build_store._require_build_store`` norm) that ``pytest.fail``s
cleanly while the surface is absent — so this file stays collection- and
mypy-clean rather than reddening the typecheck gate, and each pin is RED for the
RIGHT reason (the symbol is missing), never an ImportError.

⚠⚠ A LOAD-BEARING BUILD CONSTRAINT THE CONTRACT AUTHOR FLAGS (spec §3-vs-§8):
``TestThePrincipalClosedDomainsAreDerivedIntoTheDdl`` mutates ``_PRINCIPAL_STATUSES``
/ ``_PRINCIPAL_ROLES`` at RUNTIME and demands the emitted ASSERT move — the floor
idiom (``test_floor_calibration_schema.py::TestTheClosedDomainsAreDerivedIntoTheDdl``,
whose production code builds ``allowed_states`` INSIDE ``_floor_measurement_statements``
at CALL time, ``surreal_schema.py`` ~L1972). For this pin to be satisfiable the
builder MUST derive the ``status``/``role`` ASSERT at CALL time inside
``_principal_statements()`` from the domain tuples — NOT freeze it into a
module-constant ``_PRINCIPAL_FIELD_SPECS`` string at import (the ``finding`` idiom
that spec §3's *literal sample code* shows). A frozen import-time ASSERT makes this
derivation pin FALSE-RED on an otherwise-correct build (a C-DEF trap). Call-time
derivation is ORTHOGONAL to Variant-A (the fold) and is what §8 item 5 demands
verbatim. See ``REPORT-contract-48b.md`` decisions-needed #1.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import pytest
from _surreal_harness import (
    NONDEFAULT_DIM,
    SurrealConnection,
    SurrealEnv,
    admin_db,  # noqa: F401 - re-exported pytest fixture
    run,
)
from loremaster.store import surreal_schema

# An ``Any``-typed view of the module so a reference to a principal symbol that
# does not exist until 48-B lands does not redden the mypy gate with
# ``attr-defined`` (the ``_require_build_store`` getattr trick, one level up: the
# gate returns ``Any``, and ungated helpers read through this alias). At runtime it
# IS ``surreal_schema``, so ``monkeypatch.setattr`` targets the real module.
_schema: Any = surreal_schema

_DEFINE_TABLE = re.compile(r"^\s*DEFINE\s+TABLE\b", re.IGNORECASE)
_DEFINE_FIELD = re.compile(r"^\s*DEFINE\s+FIELD\b", re.IGNORECASE)
_DEFINE_INDEX = re.compile(r"^\s*DEFINE\s+INDEX\b", re.IGNORECASE)

# The principal schema surface 48-B adds. Absent at clean HEAD ⇒ every pin is RED
# via the gate below. ``_PRINCIPAL_STATUSES`` / ``_PRINCIPAL_ROLES`` are the domain
# TUPLES the derivation pins perturb (spec §3); a build that does not expose them
# by these names cannot satisfy the mutation pins and must say so.
_REQUIRED_SCHEMA_NAMES = (
    "PRINCIPAL_TABLE",
    "generate_principal_ddl",
    "_PRINCIPAL_STATUSES",
    "_PRINCIPAL_ROLES",
)

# Distinct, deterministic fixture values. Two DIFFERENT emails so the Model-B
# two-NONE-coexist pin cannot pass for the wrong reason (a single shared email
# would be rejected by the email UNIQUE index before the subject index is reached).
_EMAIL_A = "alice@example.com"
_EMAIL_B = "bob@example.com"
_SUBJECT = "google-oauth2|118427905123456789012"
_SUBJECT_OTHER = "google-oauth2|998877665544332211009"


def _require_principal_schema() -> Any:
    """RED-now gate: return ``surreal_schema`` once 48-B has landed the principal
    surface, else ``pytest.fail`` CLEANLY (never a collection ImportError, never a
    mypy ``attr-defined`` red — the dynamic ``getattr`` keeps this file typecheck-
    and collection-clean, the sibling ``test_build_store._require_build_store``
    norm).
    """
    missing = [name for name in _REQUIRED_SCHEMA_NAMES if not hasattr(surreal_schema, name)]
    if missing:
        pytest.fail(
            f"principal schema not yet built (packet 48-B) — surreal_schema is missing "
            f"{missing}; contract is RED until it lands",
            pytrace=False,
        )
    return surreal_schema


def _statements(ddl: str) -> list[str]:
    """The DDL's individual statements, as the transaction will see them."""
    return [line.strip() for line in ddl.split(";") if line.strip()]


def _principal_statements() -> list[str]:
    """The ``principal`` slice's statements (RED-gated)."""
    schema = _require_principal_schema()
    return _statements(schema.generate_principal_ddl())


def _field_statement(statements: list[str], field: str) -> str:
    """The single ``DEFINE FIELD`` for ``principal.<field>`` (fails if absent/dup).

    ⚠ The locator TOLERATES the ``OVERWRITE`` clause: production emits
    ``DEFINE FIELD OVERWRITE <name> ON <table>`` (``_define_field``, the #107 clause),
    so ``OVERWRITE`` sits between ``FIELD`` and the field name. A locator of
    ``\\bFIELD\\s+<name>\\b`` matches NOTHING on a correct build (adversary r2 blocker 1,
    a C-DEF: the pin was RED on a correct build).
    """
    matches = [
        statement
        for statement in statements
        if _DEFINE_FIELD.match(statement)
        and re.search(rf"\bFIELD\s+(?:OVERWRITE\s+)?{re.escape(field)}\b", statement)
    ]
    assert len(matches) == 1, f"expected exactly one DEFINE FIELD for principal.{field}, got {matches!r}"
    return matches[0]


async def _create_principal(
    connection: SurrealConnection,
    *,
    principal_id: str,
    email: str | None = _EMAIL_A,
    subject: str | None = None,
    display_name: str | None = None,
    status: str | None = None,
    role: str | None = None,
    expires_at: datetime | None = None,
    include_subject: bool = False,
    include_display_name: bool = False,
    include_status: bool = False,
    include_role: bool = False,
    include_expires_at: bool = False,
    include_email: bool = True,
) -> Any:
    """CREATE a ``principal`` row via a bound CONTENT object (store law §2).

    Mirrors ``test_surreal_schema._create_finding``: a column is written ONLY when
    its ``include_*`` flag is set (or it is a REQUIRED column), so an OMITTED
    ``option<>`` column decodes to NONE and an omitted defaulted column takes its
    DDL DEFAULT — exactly the store's own ``create`` omit-to-default behaviour.
    Uses ``CONTENT`` (not ``SET``), and binds an explicit record id so read-back is
    deterministic (the store mints its own id; the SCHEMA does not care about id
    origin). Returns the raw engine result (the caller asserts on read-back).
    """
    fragments: list[str] = []
    params: dict[str, Any] = {"id": principal_id}
    if include_email:
        fragments.append("email: $email")
        params["email"] = email
    if include_subject:
        fragments.append("subject: $subject")
        params["subject"] = subject
    if include_display_name:
        fragments.append("display_name: $display_name")
        params["display_name"] = display_name
    if include_status:
        fragments.append("status: $status")
        params["status"] = status
    if include_role:
        fragments.append("role: $role")
        params["role"] = role
    if include_expires_at:
        fragments.append("expires_at: $expires_at")
        params["expires_at"] = expires_at
    return await run(
        connection,
        f"CREATE type::record('{_schema.PRINCIPAL_TABLE}', $id) "
        f"CONTENT {{ {', '.join(fragments)} }}",
        params,
    )


def _one(rows: Any) -> Any:
    """The single row of a result the engine returns as a list."""
    assert rows, f"expected one row, got {rows!r}"
    return rows[0]


# --------------------------------------------------------------------------- #
# LEG 1 — OFFLINE DDL pins (no server; string-level over the generator output).
# Clones ``test_floor_calibration_schema.TestTheDdlDecisionRuleIsEnforcedMechanically``.
# --------------------------------------------------------------------------- #


class TestThePrincipalDdlDecisionRuleIsEnforcedMechanically:
    """Store reference §1.1. Each pin names the failure it prevents, because a
    clause is invisible in review and catastrophic in production (#107)."""

    def test_the_table_definition_is_IF_NOT_EXISTS(self) -> None:
        offenders = [
            statement
            for statement in _principal_statements()
            if _DEFINE_TABLE.match(statement) and "IF NOT EXISTS" not in statement.upper()
        ]
        assert not offenders, f"plain TABLE must be `IF NOT EXISTS` (§1.1): {offenders}"

    def test_every_field_definition_is_OVERWRITE(self) -> None:
        """#107, verbatim: ``IF NOT EXISTS`` on an existing field returns OK and
        silently keeps the OLD definition, so a changed ASSERT never reaches a
        live store. Only ``OVERWRITE`` migrates."""
        offenders = [
            statement
            for statement in _principal_statements()
            if _DEFINE_FIELD.match(statement) and "OVERWRITE" not in statement.upper()
        ]
        assert not offenders, f"every FIELD must be `DEFINE FIELD OVERWRITE` (#107): {offenders}"

    def test_no_field_definition_uses_IF_NOT_EXISTS(self) -> None:
        """The same rule from the other side — a build emitting BOTH clauses would
        pass the pin above."""
        offenders = [
            statement
            for statement in _principal_statements()
            if _DEFINE_FIELD.match(statement) and "IF NOT EXISTS" in statement.upper()
        ]
        assert not offenders, offenders

    def test_both_indexes_are_IF_NOT_EXISTS_and_never_OVERWRITE(self) -> None:
        """Flipping an index to ``OVERWRITE`` converts a silent no-op into a
        BOOT-TIME CRASH: a define REBUILDS, blocking, over every existing row
        (§1.5)."""
        indexes = [statement for statement in _principal_statements() if _DEFINE_INDEX.match(statement)]
        assert indexes, "the principal slice emits no DEFINE INDEX at all"
        for statement in indexes:
            assert "IF NOT EXISTS" in statement.upper(), statement
            assert "OVERWRITE" not in statement.upper(), statement

    def test_both_unique_indexes_are_present_on_email_and_subject(self) -> None:
        """Model B's load-bearing structure (spec §4): TWO UNIQUE indexes, one on
        ``email`` (the human admission key) and one on ``subject`` (the runtime
        identity). A build that dropped the ``subject`` UNIQUE index — or made it
        plain — would let two principals claim one OAuth identity, which packet 39's
        ``WHERE subject = $client_id`` admission must never see."""
        indexes = [statement for statement in _principal_statements() if _DEFINE_INDEX.match(statement)]
        email_unique = [
            statement
            for statement in indexes
            if "UNIQUE" in statement.upper() and re.search(r"FIELDS\s+email\b", statement, re.I)
        ]
        subject_unique = [
            statement
            for statement in indexes
            if "UNIQUE" in statement.upper() and re.search(r"FIELDS\s+subject\b", statement, re.I)
        ]
        assert email_unique, f"expected a UNIQUE index on principal.email, indexes={indexes!r}"
        assert subject_unique, f"expected a UNIQUE index on principal.subject, indexes={indexes!r}"

    def test_the_word_ALTER_appears_in_no_statement(self) -> None:
        """§1.3: ``ALTER`` cannot CREATE a field, and ``ALTER … IF EXISTS`` on a
        missing one silently no-ops — adopting it re-commits #107 from the other
        side, on the fresh-DB path this slice runs on every new deployment."""
        offenders = [
            statement for statement in _principal_statements() if re.search(r"\bALTER\b", statement, re.I)
        ]
        assert not offenders, offenders

    def test_the_slice_contains_neither_a_relation_table_nor_a_sequence(self) -> None:
        """⚠ A PINNED KNOWN BOUND (not a prohibition). ``principal`` is a plain
        table; if this ever grows a ``TYPE RELATION`` table the TABLE clause INVERTS
        to ``OVERWRITE`` (§1.1's RELATION row — ``IF NOT EXISTS`` is a measured
        silent no-op on an existing edge table), and a ``DEFINE SEQUENCE`` carries
        #146's un-migratable ``BATCH``/``START`` residual. Re-read store §1 first,
        then update this pin deliberately."""
        for statement in _principal_statements():
            assert "TYPE RELATION" not in statement.upper(), statement
            assert not re.search(r"\bDEFINE\s+SEQUENCE\b", statement, re.I), statement

    def test_the_generator_returns_the_house_terminated_shape(self) -> None:
        """Every other ``generate_*_ddl`` returns ``";\\n".join(...) + ";\\n"``. A
        slice that did not would break the caller's ``BEGIN … COMMIT`` wrap."""
        schema = _require_principal_schema()
        ddl = schema.generate_principal_ddl()
        assert ddl.endswith(";\n")
        assert _statements(ddl)

    def test_the_generator_emits_fields_not_just_the_table_name(self) -> None:
        """CONTROL: a generator emitting a bare ``DEFINE TABLE`` and ZERO
        ``DEFINE FIELD`` would make ``test_every_field_definition_is_OVERWRITE``
        vacuously green — the signature failure of a mechanical gate (adversary
        F1c). It DEMANDS fields."""
        schema = _require_principal_schema()
        table = schema.PRINCIPAL_TABLE
        fields = [
            statement
            for statement in _principal_statements()
            if _DEFINE_FIELD.match(statement) and f" ON {table} " in f"{statement} "
        ]
        assert fields, f"the slice for {table!r} emits no DEFINE FIELD at all"

    def test_principal_is_FOLDED_into_the_global_generate_ddl(self) -> None:
        """Variant A (spec §2): ``principal`` is folded into the global
        ``generate_ddl`` so the primary ``write_store.ensure_ready()`` creates the
        table the moment 48 ships — without 48 wiring a ``PrincipalStore`` into
        ``build_app_context``. The fold is what makes the table exist in production;
        a build that shipped only the standalone slice would leave production
        without the table until 39/49 wired the store in."""
        schema = _require_principal_schema()
        full = schema.generate_ddl(dim=NONDEFAULT_DIM)
        table = schema.PRINCIPAL_TABLE
        assert f"DEFINE TABLE IF NOT EXISTS {table} SCHEMAFULL" in full, (
            "principal is NOT folded into generate_ddl() — the table will not exist in "
            "production until a PrincipalStore is wired in (spec §2)"
        )
        assert any(
            _DEFINE_FIELD.match(statement) and f" ON {table} " in f"{statement} "
            for statement in _statements(full)
        ), "generate_ddl() carries the principal table but none of its fields"

    def test_the_slice_ROUTES_THROUGH_the_shared_ddl_emitters(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ONE IMPLEMENTATION, proven by MUTATION (§6 / floor residual 8): nothing
        REQUIRES the principal slice to CALL ``_define_field`` — a hand-written
        ``DEFINE FIELD`` string would pass every clause pin above while silently not
        sharing the #107 ``OVERWRITE`` policy. Perturb the shared emitter; the
        emitted DDL must move."""
        schema = _require_principal_schema()
        original = schema._define_field
        monkeypatch.setattr(
            schema,
            "_define_field",
            lambda *args, **kwargs: f"{original(*args, **kwargs)} COMMENT 'mutation-probe'",
        )
        assert "mutation-probe" in schema.generate_principal_ddl(), (
            "the principal slice does not route through surreal_schema._define_field"
        )


class TestThePrincipalClosedDomainsAreDerivedIntoTheDdl:
    """ONE IMPLEMENTATION, proven by MUTATION rather than by reading the source
    (CLAUDE.md 'A DIAGNOSIS IS NOT AN INSTRUMENT'). The ``status``/``role`` ASSERTs
    must be GENERATED FROM ``_PRINCIPAL_STATUSES`` / ``_PRINCIPAL_ROLES``, not
    hand-typed beside them.

    ⚠ REQUIRES CALL-TIME DERIVATION (see the module docstring's build-constraint
    flag): a frozen import-time ASSERT string cannot move under a runtime
    monkeypatch of the tuple, so these two pins FORCE the floor idiom
    (``_floor_measurement_statements`` builds ``allowed_states`` at call time). This
    is the spec §3-vs-§8 fork surfaced in REPORT-contract-48b.md decisions-needed #1.
    """

    def test_changing_the_status_tuple_changes_the_emitted_ASSERT(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        schema = _require_principal_schema()
        before = schema.generate_principal_ddl()
        monkeypatch.setattr(
            schema,
            "_PRINCIPAL_STATUSES",
            (*schema._PRINCIPAL_STATUSES, "mutation_probe_status"),
        )
        after = schema.generate_principal_ddl()
        assert after != before, (
            "adding a status changed no emitted DDL — the status ASSERT is a hand-typed "
            "twin of _PRINCIPAL_STATUSES (or a frozen import-time constant) rather than a "
            "CALL-TIME derivation of it (build-constraint flag, decisions-needed #1)"
        )
        assert "mutation_probe_status" in after

    def test_changing_the_role_tuple_changes_the_emitted_ASSERT(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        schema = _require_principal_schema()
        before = schema.generate_principal_ddl()
        monkeypatch.setattr(
            schema,
            "_PRINCIPAL_ROLES",
            (*schema._PRINCIPAL_ROLES, "mutation_probe_role"),
        )
        after = schema.generate_principal_ddl()
        assert after != before, (
            "adding a role changed no emitted DDL — the role ASSERT is a hand-typed twin "
            "(or frozen import-time constant) rather than a CALL-TIME derivation of "
            "_PRINCIPAL_ROLES (build-constraint flag, decisions-needed #1)"
        )
        assert "mutation_probe_role" in after

    def test_every_ruled_status_and_role_reaches_the_ddl(self) -> None:
        """Membership control alongside the mutation pins: an over-narrow ASSERT
        that dropped a legal value would silently break that transition forever."""
        schema = _require_principal_schema()
        ddl = schema.generate_principal_ddl()
        missing_status = [value for value in schema._PRINCIPAL_STATUSES if f"'{value}'" not in ddl]
        missing_role = [value for value in schema._PRINCIPAL_ROLES if f"'{value}'" not in ddl]
        assert not missing_status, f"statuses absent from the DDL: {missing_status}"
        assert not missing_role, f"roles absent from the DDL: {missing_role}"

    def test_status_and_role_default_to_the_least_privilege_values(self) -> None:
        """Spec §3: ``status`` DEFAULT ``active``, ``role`` DEFAULT ``member``
        (least-privilege — a principal is a member unless explicitly elevated). A
        build that omitted the DEFAULT would force every creator to name the value,
        which the store's email-only ``create`` deliberately does not."""
        statements = _principal_statements()
        status = _field_statement(statements, "status")
        role = _field_statement(statements, "role")
        assert "DEFAULT" in status and "'active'" in status, status
        assert "DEFAULT" in role and "'member'" in role, role

    def test_the_ruled_status_and_role_domains_are_EXACTLY_the_closed_set(self) -> None:
        """⚠ THE QUANTIFIER PIN (adversary r2 blocker 2): pin the RULED SET ∀, not
        just known-bad-rejected + known-good-accepted.

        The derivation + membership + reject pins above ALL PASS on a build that
        WIDENS the closed domain (``_PRINCIPAL_STATUSES += 'archived'``,
        ``_PRINCIPAL_ROLES += 'superadmin'``): the ASSERT still derives from the
        tuple, every ruled value still reaches the DDL, and the known-bad reject
        pins still reject THEIR specific garbage value. Nothing pinned the domain
        is EXACTLY the ruled set — so a widening slips through the entire contract.
        ``role`` is the AUTHZ domain (``role → AccessToken.scopes``, design R2): a
        leaked ``'superadmin'`` is a privilege-escalation hole. This pins the set as
        an invariant — a widened tuple REDS here, carrying "if you changed the ruled
        domain deliberately (design §3), update this pin and say so".
        """
        schema = _require_principal_schema()
        assert set(schema._PRINCIPAL_STATUSES) == {"active", "suspended"}, (
            f"the ruled status domain is {{active, suspended}} (design §3); "
            f"_PRINCIPAL_STATUSES={schema._PRINCIPAL_STATUSES!r}"
        )
        assert set(schema._PRINCIPAL_ROLES) == {"member", "admin"}, (
            f"the ruled role domain is {{member, admin}} (design §3) — role is the AUTHZ "
            f"domain, so a leaked value is a security hole; _PRINCIPAL_ROLES={schema._PRINCIPAL_ROLES!r}"
        )


# --------------------------------------------------------------------------- #
# LEG 2 — LIVE round-trip on ws://127.0.0.1:18000 (NEVER :18500). NO skip marker:
# an unreachable store is a LOUD failure, not a skip. Clones
# ``test_surreal_schema.TestFindingRoundTrip`` / floor's live-engine class.
# --------------------------------------------------------------------------- #


class TestThePrincipalSchemaAppliesToTheLiveEngine:
    """The generated DDL against the real engine — the recipe proven on the cake."""

    async def test_the_slice_creates_the_table(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        schema = _require_principal_schema()
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        tables = set((await run(connection, "INFO FOR DB")).get("tables", {}))
        assert schema.PRINCIPAL_TABLE in tables

    async def test_the_slice_is_safely_re_appliable(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """``ensure_ready`` re-applies the DDL on EVERY boot. A statement that raises
        on re-application is a boot-time crash, not a style issue."""
        schema = _require_principal_schema()
        connection, _ = admin_db
        for _ in range(2):
            await run(connection, schema.generate_principal_ddl())


class TestThePrincipalRoundTrip:
    """The ``principal`` table (live behavioural) — the Model-B property set (§8-6).

    ⚠ THE LOAD-BEARING PIN is ``test_two_email_only_creates_both_none_subject_coexist``:
    a single-NONE fixture cannot see it, and the whole packet's admin-pre-create flow
    turns on it. The dirty-store half lives in
    ``test_surreal_store.TestSchemaMigrationAgainstAnExistingStore``.
    """

    async def test_create_with_subject_reads_back_by_subject_and_by_email(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """(d) The OAuth-direct path: a principal created WITH a subject is found by
        both of its UNIQUE keys."""
        schema = _require_principal_schema()
        table = schema.PRINCIPAL_TABLE
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        await _create_principal(
            connection, principal_id="p1", email=_EMAIL_A, subject=_SUBJECT, include_subject=True
        )
        by_subject = _one(
            await run(
                connection,
                f"SELECT id, email, subject, display_name, status, role, expires_at, created_at "
                f"FROM {table} WHERE subject = $subject",
                {"subject": _SUBJECT},
            )
        )
        by_email = _one(
            await run(
                connection,
                f"SELECT id, email, subject, display_name, status, role, expires_at, created_at "
                f"FROM {table} WHERE email = $email",
                {"email": _EMAIL_A},
            )
        )
        assert by_subject["email"] == _EMAIL_A
        assert by_subject["subject"] == _SUBJECT
        assert by_email["subject"] == _SUBJECT

    async def test_two_email_only_creates_both_none_subject_coexist(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ THE LOAD-BEARING MODEL-B PIN (spec §4, probe Q1). Two email-only
        principals (subject OMITTED → NONE) BOTH succeed under the plain UNIQUE index
        on ``option<string> subject`` — a UNIQUE index over a nullable column admits
        any number of NULLs. A single-NONE fixture cannot discriminate this from a
        build where the second NONE is rejected, which would break admin pre-create
        for every principal after the first."""
        schema = _require_principal_schema()
        table = schema.PRINCIPAL_TABLE
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        # Two DIFFERENT emails (the email UNIQUE index would reject a shared one
        # BEFORE the subject index was ever reached — a wrong-reason pass).
        await _create_principal(connection, principal_id="p1", email=_EMAIL_A)
        await _create_principal(connection, principal_id="p2", email=_EMAIL_B)
        for email in (_EMAIL_A, _EMAIL_B):
            row = _one(
                await run(
                    connection,
                    f"SELECT id, email, subject FROM {table} WHERE email = $email",
                    {"email": email},
                )
            )
            assert row["subject"] is None, f"{email} pre-created row should carry subject=None"

    async def test_create_with_subject_also_works_alongside_none_rows(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """The other half of Q1: a NON-NONE subject row coexists with NONE rows — so
        the UNIQUE index rejects only genuine non-NONE collisions, never a NULL."""
        schema = _require_principal_schema()
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        await _create_principal(connection, principal_id="p1", email=_EMAIL_A)  # subject NONE
        await _create_principal(
            connection, principal_id="p2", email=_EMAIL_B, subject=_SUBJECT, include_subject=True
        )  # must succeed alongside the NONE row

    async def test_duplicate_non_none_subject_rejected_on_CREATE(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """(b/CREATE) Two principals may never claim ONE OAuth identity."""
        schema = _require_principal_schema()
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        await _create_principal(
            connection, principal_id="p1", email=_EMAIL_A, subject=_SUBJECT, include_subject=True
        )
        with pytest.raises(Exception):  # noqa: B017 - engine UNIQUE index rejection
            await _create_principal(
                connection, principal_id="p2", email=_EMAIL_B, subject=_SUBJECT, include_subject=True
            )

    async def test_duplicate_non_none_subject_rejected_on_UPDATE_fill(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """(b/UPDATE) ⚠ THE PATH THE PROBE CAUGHT (spec §4, Q3), which a CREATE-only
        pin misses: filling a NONE subject via UPDATE to a value ALREADY bound on
        another principal is rejected by the UNIQUE index — this is 39's
        fill-on-login path, protected. Positive control: the SAME UPDATE to a FREE
        subject succeeds, so the rejection is the index firing, not the UPDATE
        failing for an unrelated reason."""
        schema = _require_principal_schema()
        table = schema.PRINCIPAL_TABLE
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        await _create_principal(
            connection, principal_id="owner", email=_EMAIL_A, subject=_SUBJECT, include_subject=True
        )
        await _create_principal(connection, principal_id="filler", email=_EMAIL_B)  # subject NONE
        with pytest.raises(Exception):  # noqa: B017 - engine UNIQUE index rejection on UPDATE
            await run(
                connection,
                f"UPDATE type::record('{table}', 'filler') SET subject = $subject",
                {"subject": _SUBJECT},
            )
        # POSITIVE CONTROL — the same UPDATE to a FREE subject lands.
        await run(
            connection,
            f"UPDATE type::record('{table}', 'filler') SET subject = $subject",
            {"subject": _SUBJECT_OTHER},
        )
        row = _one(
            await run(
                connection,
                f"SELECT subject FROM type::record('{table}', 'filler')",
            )
        )
        assert row["subject"] == _SUBJECT_OTHER

    async def test_duplicate_email_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """(c) ``email`` is the REQUIRED+UNIQUE admin key — a duplicate is rejected
        even when both rows carry NONE subject (proving the email index, not the
        subject one, does the work)."""
        schema = _require_principal_schema()
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        await _create_principal(connection, principal_id="p1", email=_EMAIL_A)
        with pytest.raises(Exception):  # noqa: B017 - engine UNIQUE index rejection
            await _create_principal(connection, principal_id="p2", email=_EMAIL_A)

    @pytest.mark.parametrize("empty_email", ["", " ", "\t"])
    async def test_empty_or_whitespace_email_rejected(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
        empty_email: str,
    ) -> None:
        """(c) A present-but-empty/whitespace email names no real person — the
        trim-aware non-empty ASSERT rejects it as loudly as a missing one."""
        schema = _require_principal_schema()
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation
            await _create_principal(connection, principal_id="bad", email=empty_email)

    async def test_missing_email_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """(c) ``email`` is REQUIRED (plain, non-``option`` string) — a row omitting
        it entirely is rejected by SCHEMAFULL discipline."""
        schema = _require_principal_schema()
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine required-field rejection
            await _create_principal(
                connection,
                principal_id="noemail",
                include_email=False,
                subject=_SUBJECT,
                include_subject=True,
            )

    async def test_unknown_status_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        schema = _require_principal_schema()
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation
            await _create_principal(
                connection, principal_id="badstatus", email=_EMAIL_A, status="not_a_status",
                include_status=True,
            )

    async def test_unknown_role_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        schema = _require_principal_schema()
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation
            await _create_principal(
                connection, principal_id="badrole", email=_EMAIL_A, role="not_a_role", include_role=True
            )

    async def test_a_plausible_but_unruled_status_or_role_is_rejected_by_the_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ THE QUANTIFIER PIN, live belt-and-braces (adversary r2 blocker 2). The
        offline exact-set pin catches a domain widened THROUGH the tuple; this
        catches one widened in the store's runtime DDL by ANY means. The values are
        PLAUSIBLE-but-unruled (``archived`` / ``superadmin``) — exactly what a
        careless widening would add — not obvious garbage: a build that widened the
        ruled set would ACCEPT them, so the store MUST reject them. ``superadmin`` is
        the privilege-escalation value ``role`` (the authz domain) must never admit."""
        schema = _require_principal_schema()
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation (unruled status)
            await _create_principal(
                connection, principal_id="archived", email=_EMAIL_A, status="archived",
                include_status=True,
            )
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation (unruled role — authz)
            await _create_principal(
                connection, principal_id="superadmin", email=_EMAIL_B, role="superadmin",
                include_role=True,
            )

    async def test_every_valid_status_and_role_is_accepted_positive_control(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """THE POSITIVE CONTROL for the two rejection pins above: an over-strict
        ASSERT (e.g. one accepting only the DEFAULT) would silently pass both
        negative tests while breaking every real transition. Every ruled status ×
        role combination must be accepted."""
        schema = _require_principal_schema()
        table = schema.PRINCIPAL_TABLE
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        index = 0
        for status in schema._PRINCIPAL_STATUSES:
            for role in schema._PRINCIPAL_ROLES:
                index += 1
                await _create_principal(
                    connection,
                    principal_id=f"ok{index}",
                    email=f"user{index}@example.com",
                    status=status,
                    role=role,
                    include_status=True,
                    include_role=True,
                )
                row = _one(
                    await run(
                        connection,
                        f"SELECT status, role FROM type::record('{table}', 'ok{index}')",
                    )
                )
                assert row["status"] == status
                assert row["role"] == role

    async def test_omitted_option_columns_read_back_as_none_under_explicit_projection(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """The store-law §2 hostile fixture: a principal created with NO subject /
        display_name / expires_at reads those back as ``None`` under an EXPLICIT
        projection — NOT a ``KeyError``. This is exactly why the store's readers use
        explicit column lists (``get_by_*`` / ``list`` in ``test_principals_store``),
        never ``SELECT *`` (which OMITS a NONE ``option<>`` column — the control
        below)."""
        schema = _require_principal_schema()
        table = schema.PRINCIPAL_TABLE
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        await _create_principal(connection, principal_id="p1", email=_EMAIL_A)  # only email
        row = _one(
            await run(
                connection,
                f"SELECT id, email, subject, display_name, status, role, expires_at, created_at "
                f"FROM type::record('{table}', 'p1')",
            )
        )
        assert row["subject"] is None
        assert row["display_name"] is None
        assert row["expires_at"] is None

    async def test_select_star_OMITS_the_none_option_column_the_control(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ THE §2 DISCRIMINATING CONTROL that proves WHY explicit projection is
        mandatory: under ``SELECT *`` a NONE-valued ``option<>`` column is OMITTED
        ENTIRELY — the key is not present at all (``row["subject"]`` would
        ``KeyError``). A build whose ``get_by_*`` used ``SELECT *`` would blow up on
        every email-pre-created principal; this pin is the reason the store may
        not."""
        schema = _require_principal_schema()
        table = schema.PRINCIPAL_TABLE
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        await _create_principal(connection, principal_id="p1", email=_EMAIL_A)  # subject NONE
        row = _one(await run(connection, f"SELECT * FROM type::record('{table}', 'p1')"))
        assert "email" in row  # a present column IS there
        assert "subject" not in row, (
            "SELECT * unexpectedly returned the NONE subject key — store-law §2 says an "
            "option<> NONE column is omitted; if the engine changed, the store's reader "
            "strategy must be re-derived"
        )

    async def test_empty_string_subject_rejected_while_none_is_accepted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Spec §3 refinement: ``subject`` is ``option<string>`` carrying the
        trim-aware non-empty ASSERT. The ASSERT is SKIPPED on NONE (so the
        pre-created email-only row is legal) but FIRES on a present-but-empty value
        (so a garbage ``subject = ''`` — which 39's ``WHERE subject = ''`` would
        match — is rejected).

        ⚠ CONDITIONAL PIN: if the lead/operator drops the ASSERT to a BARE
        ``option<string>`` (spec §3 offers this one-line alternative), DELETE this
        pin and say so (REPORT-contract-48b.md decisions-needed #3)."""
        schema = _require_principal_schema()
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        # NONE accepted (the ASSERT is skipped) …
        await _create_principal(connection, principal_id="none_ok", email=_EMAIL_A)  # subject omitted
        # … a present empty string rejected (the ASSERT fires).
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation on present empty value
            await _create_principal(
                connection, principal_id="empty_subj", email=_EMAIL_B, subject="", include_subject=True
            )

    async def test_principal_rejects_an_undeclared_field(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """SCHEMAFULL discipline: an undeclared top-level key RAISES (store §1.7),
        so a typo'd column can never silently become a phantom attribute."""
        schema = _require_principal_schema()
        table = schema.PRINCIPAL_TABLE
        connection, _ = admin_db
        await run(connection, schema.generate_principal_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine SCHEMAFULL rejection
            await run(
                connection,
                f"CREATE type::record('{table}', $id) CONTENT "
                f"{{ email: $email, rogue_field: 'not in the schema' }}",
                {"id": "rogue", "email": _EMAIL_A},
            )
