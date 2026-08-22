"""Contract — packet 60 wave 1, the ``keep`` + ``member_of`` SCHEMA (the Keep substrate).

Written by ``contract-60-w1`` (2026-08-22). The builder builds FROM this; it writes
NO production code. *Every "RED today" claim is scoped to the tree at ``f0ebbf4``
(branch ``feat/surreal-unification``): the ``keep``/``member_of`` slice is a RED STUB
(``surreal_schema::_keep_statements`` / ``_member_of_statements`` emit ``[]`` and
``generate_keep_ddl`` emits ``""``), so every pin below fails BEHAVIOURALLY.*

SPEC (the work order, executed verbatim — never re-transcribed):
``docs/design/2026-08-22-packet60-keep-substrate-rulings.md`` — Fork A (keeper is a
``keep.keeper: record<principal>`` FIELD LINK, indexed non-unique, NOT a ``keeps``
edge), Fork B (the ``keep`` field set + closed ``type`` domain, NO default, ``ulid()``
id), Fork C (``member_of.rank`` closed-flat-today ``{contributor}``, DEFAULT
``contributor``, WIDEN-safe), Fork D (``create-keep`` auto-adds the keeper to the
household — a store concern pinned in ``test_keeps_store.py``), Fork F (``member_of``
ENFORCED + UNIQUE(in, out)), the Emission plan, and the store-law checklist.

STORE LAW binds (``docs/reference/surrealdb-31-capabilities.md``, cited never
re-transcribed): §1.1 (TABLE/INDEX ``IF NOT EXISTS``, FIELD ``OVERWRITE``, RELATION
table ``OVERWRITE``; ``ALTER`` is a trap §1.3), §1.4 (the rank-widening dirty-store
hazard — the ONLY §1.4-relevant leg here, and it is FUTURE), §1.8 (a plain UNIQUE over
an ``option<>`` column admits multiple NONE — the ``name`` note), §2 (CONTENT writes,
``type::record`` binds, explicit projection reads NONE while ``SELECT *`` OMITS it),
§3 (a multi-statement ``query()`` validates ``statement[0]`` only — DDL applies through
``execute_transaction``), §4 (``ENFORCED`` validates BOTH endpoints + guards
``INSERT RELATION``; UNIQUE(in, out) is legal on our floor; a graph TRAVERSAL never
uses a secondary index — so keeper is a FIELD, and the keeper index must be PROVEN to
fire).

============================================================================
WHAT THIS CONTRACT TURNS RED IN FILES IT DOES NOT OWN
============================================================================

It reddens three pins in ``test_enforced_relations.py``, **deliberately**, by declaring
``member_of`` in ``_enforced_relations_scaffold.KNOWN_RELATION_EDGES`` (with
``(principal, keep)``) and registering ``generate_keep_ddl`` in ``ALL_DDL_GENERATORS``
BEFORE the edge is emitted — the exact ``blocks`` (packet 04b-1) forcing-function shape:

1. ``test_the_relation_edge_set_is_EXACTLY_the_six_known_edges`` — the exact-set pin
   (RE-COUNTED from five to six by this contract). RED until the builder lands
   ``surreal_schema::_member_of_statements``.
2. ``test_the_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS[member_of]``
3. ``test_the_edge_declares_its_IN_and_OUT_endpoint_tables[member_of-endpoints…]``

All go GREEN the moment the builder emits the edge, and **none may be "fixed" by
removing ``member_of`` from the declared set or by adding it to ``DEFERRED_TO_PACKET_43``**
— both are pinned shut from THIS side by :class:`TestTheMemberOfEdgeIsDeclared`, so a
packet-60 builder reading only its own contract meets the law.

The offline ∀ ENFORCED / OVERWRITE / IN-OUT pins in ``test_enforced_relations.py``
parametrise onto ``member_of`` automatically once it is emitted; they are re-asserted
HERE too (:class:`TestTheMemberOfEdgeIsGuardedFromBirth`) so this contract is
self-contained.
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from _enforced_relations_scaffold import (
    KNOWN_RELATION_EDGES,
    apply_ddl,
    every_emitted_relation_table,
    ghost_id,
    is_enforced,
    migration_db,  # noqa: F401 - re-exported pytest fixture
    old_world_ddl,
    record_exists,
    relation_table_statements,
    statements,
)
from _surreal_harness import (
    NONDEFAULT_DIM,
    SurrealConnection,
    SurrealEnv,
    admin_db,  # noqa: F401 - re-exported pytest fixture
    run,
)
from loremaster.store import surreal_schema

# The keep schema surface packet 60 adds. All EXIST as of ``f0ebbf4`` (the RED STUB),
# so this file imports them directly (no getattr gate): the pins fail BEHAVIOURALLY
# because ``generate_keep_ddl`` emits ``""``, never because a symbol is missing.
from loremaster.store.surreal_schema import (
    _KEEP_RANK_CONTRIBUTOR,
    _KEEP_RANKS,
    _KEEP_TYPES,
    KEEP_TABLE,
    MEMBER_OF_RELATION,
    PRINCIPAL_TABLE,
    generate_ddl,
    generate_keep_ddl,
    generate_principal_ddl,
)
from surrealdb import RecordID

_DEFINE_TABLE = re.compile(r"^\s*DEFINE\s+TABLE\b", re.IGNORECASE)
_DEFINE_FIELD = re.compile(r"^\s*DEFINE\s+FIELD\b", re.IGNORECASE)
_DEFINE_INDEX = re.compile(r"^\s*DEFINE\s+INDEX\b", re.IGNORECASE)

# Distinct, deterministic fixture values. Two principals + two members so a build that
# counted VERSIONS instead of AGENTS, or answered a len()==sum() trap, is caught
# (FIXTURES MUST DISCRIMINATE).
_KEEPER_ID = "keeper_alice"
_MEMBER_ID = "member_bob"
_KEEPER_EMAIL = "alice@example.com"
_MEMBER_EMAIL = "bob@example.com"


def _statements(ddl: str) -> list[str]:
    """The DDL's individual statements, as the transaction will see them."""
    return [line.strip() for line in ddl.split(";") if line.strip()]


def _keep_statements() -> list[str]:
    """The ``keep``/``member_of`` slice's statements (via ``generate_keep_ddl``)."""
    return _statements(generate_keep_ddl())


def _keep_table_statements() -> list[str]:
    """Just the statements targeting the ``keep`` NODE table (its DEFINE TABLE, its
    fields, its keeper index) — NOT the ``member_of`` edge's."""
    kept: list[str] = []
    for statement in _keep_statements():
        if f" {MEMBER_OF_RELATION} " in f"{statement} " or f"ON {MEMBER_OF_RELATION}" in statement:
            continue
        if re.search(rf"\bINDEX\b.*\bON\s+{MEMBER_OF_RELATION}\b", statement):
            continue
        kept.append(statement)
    return kept


def _field_statement(all_statements: list[str], table: str, field: str) -> str:
    """The single ``DEFINE FIELD`` for ``table.<field>`` (tolerating ``OVERWRITE``).

    Production emits ``DEFINE FIELD OVERWRITE <name> ON <table>`` (``_define_field``,
    the #107 clause), so ``OVERWRITE`` sits between ``FIELD`` and the name — a naive
    ``\\bFIELD\\s+<name>\\b`` locator would match NOTHING on a correct build.
    """
    matches = [
        statement
        for statement in all_statements
        if _DEFINE_FIELD.match(statement)
        and re.search(rf"\bFIELD\s+(?:OVERWRITE\s+)?{re.escape(field)}\b", statement)
        and f" ON {table} " in f"{statement} "
    ]
    assert len(matches) == 1, f"expected exactly one DEFINE FIELD for {table}.{field}, got {matches!r}"
    return matches[0]


def _member_of_statement(ddl: str) -> str:
    """The ``member_of`` ``DEFINE TABLE`` statement inside ``ddl``, or a teaching failure."""
    emitted = relation_table_statements(ddl)
    assert MEMBER_OF_RELATION in emitted, (
        f"this DDL emits no {MEMBER_OF_RELATION!r} relation table. Packet 60 adds it to "
        f"surreal_schema::_member_of_statements — emitted here (STUB emits ``[]``): "
        f"{sorted(emitted)}"
    )
    return emitted[MEMBER_OF_RELATION]


# --------------------------------------------------------------------------- #
# Live-store seeding helpers (a keep needs a keeper principal; member_of needs both
# endpoints). Local rather than a scaffold edit: ``seed_endpoint`` cannot express a
# ``keep`` row's required ``record<principal>`` keeper.
# --------------------------------------------------------------------------- #


async def _apply_keep_and_principal_schema(connection: SurrealConnection, url: str) -> None:
    """Apply the ``principal`` slice THEN the ``keep``/``member_of`` slice, exactly as
    production layers them (principal is ``member_of``'s ``IN`` endpoint and ``keep``'s
    ``keeper`` link target). Through ``execute_transaction`` (store law §3), never a
    lax ``query()``."""
    await apply_ddl(connection, generate_principal_ddl(), url=url)
    await apply_ddl(connection, generate_keep_ddl(), url=url)


async def _seed_principal(connection: SurrealConnection, principal_id: str, email: str) -> None:
    """CREATE a minimal ``principal`` row (an admission-only email pre-create)."""
    await run(
        connection,
        f"CREATE type::record('{PRINCIPAL_TABLE}', $id) CONTENT {{ email: $email }}",
        {"id": principal_id, "email": email},
    )


async def _seed_keep(
    connection: SurrealConnection,
    keep_id: str,
    keeper_id: str,
    *,
    keep_type: str = "project",
    name: str | None = None,
    include_keeper: bool = True,
    include_type: bool = True,
) -> Any:
    """CREATE a ``keep`` row via a bound CONTENT object (store law §2).

    ``keeper`` binds as ``type::record('principal', $kid)`` (a record link, never a
    bare string — store law §2/§4). ``name`` is written ONLY when provided (so an
    omitted ``option<>`` decodes to NONE); ``type``/``keeper`` are written unless a
    negative pin omits them to test the REQUIRED discipline. ``created_at`` self-stamps.
    """
    fragments: list[str] = []
    params: dict[str, Any] = {"id": keep_id}
    if include_keeper:
        fragments.append(f"keeper: type::record('{PRINCIPAL_TABLE}', $kid)")
        params["kid"] = keeper_id
    if include_type:
        fragments.append("type: $type")
        params["type"] = keep_type
    if name is not None:
        fragments.append("name: $name")
        params["name"] = name
    return await run(
        connection,
        f"CREATE type::record('{KEEP_TABLE}', $id) CONTENT {{ {', '.join(fragments)} }}",
        params,
    )


async def _relate_member_of(
    connection: SurrealConnection,
    principal_id: str,
    keep_id: str,
    *,
    rank: str | None = None,
) -> Any:
    """RELATE ``principal --member_of--> keep`` with endpoints bound as ``RecordID``.

    ``$from``/``$to`` bound (NOT ``type::record()`` at the RELATE arrow — a PARSE ERROR,
    store law §4). ``rank`` set only when named, so an omitted rank takes the DDL DEFAULT.
    """
    set_clause = " SET rank = $rank" if rank is not None else ""
    params: dict[str, Any] = {
        "from": RecordID(PRINCIPAL_TABLE, principal_id),
        "to": RecordID(KEEP_TABLE, keep_id),
    }
    if rank is not None:
        params["rank"] = rank
    return await run(
        connection,
        f"RELATE $from->{MEMBER_OF_RELATION}->$to{set_clause}",
        params,
    )


def _one(rows: Any) -> Any:
    """The single row of a result the engine returns as a list."""
    assert rows, f"expected one row, got {rows!r}"
    return rows[0]


# =========================================================================== #
# LEG 1 — OFFLINE DDL pins (no server; string-level over the generator output).
# =========================================================================== #


class TestTheKeepDdlDecisionRuleIsEnforcedMechanically:
    """Store reference §1.1. Each pin names the failure it prevents — a clause is
    invisible in review and catastrophic in production (#107)."""

    def test_the_keep_table_definition_is_IF_NOT_EXISTS(self) -> None:
        table_defs = [
            statement
            for statement in _keep_statements()
            if _DEFINE_TABLE.match(statement) and "TYPE RELATION" not in statement.upper()
        ]
        assert table_defs, "the keep slice emits no plain DEFINE TABLE at all"
        for statement in table_defs:
            assert "IF NOT EXISTS" in statement.upper(), (
                f"the plain keep table must be `IF NOT EXISTS` (§1.1): {statement!r}"
            )

    def test_every_keep_field_definition_is_OVERWRITE(self) -> None:
        """#107, verbatim: ``IF NOT EXISTS`` on an existing field silently keeps the OLD
        definition, so a changed ASSERT never reaches a live store. Only ``OVERWRITE``
        migrates."""
        offenders = [
            statement
            for statement in _keep_statements()
            if _DEFINE_FIELD.match(statement) and "OVERWRITE" not in statement.upper()
        ]
        assert not offenders, (
            f"every keep/member_of FIELD must be `DEFINE FIELD OVERWRITE` (#107): {offenders}"
        )

    def test_no_field_definition_uses_IF_NOT_EXISTS(self) -> None:
        """The same rule from the other side — a build emitting BOTH clauses would pass
        the pin above."""
        offenders = [
            statement
            for statement in _keep_statements()
            if _DEFINE_FIELD.match(statement) and "IF NOT EXISTS" in statement.upper()
        ]
        assert not offenders, offenders

    def test_the_keeper_index_is_IF_NOT_EXISTS_and_NON_unique(self) -> None:
        """The keeper index (Fork A rider): a NON-UNIQUE index (a principal keeps MANY
        keeps), ``IF NOT EXISTS`` (flipping an index to ``OVERWRITE`` rebuilds it over
        every row — a boot-time crash, §1.5)."""
        keeper_indexes = [
            statement
            for statement in _keep_statements()
            if _DEFINE_INDEX.match(statement)
            and re.search(rf"\bON\s+{KEEP_TABLE}\b", statement)
            and re.search(r"\bFIELDS\s+keeper\b", statement)
        ]
        assert keeper_indexes, f"the keep slice emits no index on {KEEP_TABLE}.keeper"
        for statement in keeper_indexes:
            assert "IF NOT EXISTS" in statement.upper(), statement
            assert "OVERWRITE" not in statement.upper(), statement
            assert "UNIQUE" not in statement.upper(), (
                f"the keeper index must be NON-unique (a principal keeps many keeps — Fork A): {statement!r}"
            )

    def test_the_member_of_unique_index_is_IF_NOT_EXISTS(self) -> None:
        """The ``member_of`` UNIQUE(in, out) index — ``IF NOT EXISTS`` (§1.1)."""
        member_of_indexes = [
            statement
            for statement in _keep_statements()
            if _DEFINE_INDEX.match(statement) and re.search(rf"\bON\s+{MEMBER_OF_RELATION}\b", statement)
        ]
        assert member_of_indexes, f"the keep slice emits no index on {MEMBER_OF_RELATION}"
        for statement in member_of_indexes:
            assert "IF NOT EXISTS" in statement.upper(), statement
            assert "OVERWRITE" not in statement.upper(), statement
            assert "UNIQUE" in statement.upper(), (
                f"the member_of endpoint-pair index must be UNIQUE (Fork F): {statement!r}"
            )
            assert re.search(r"FIELDS\s+in\s*,\s*out", statement), (
                f"the member_of UNIQUE index must be over (in, out): {statement!r}"
            )

    def test_the_member_of_relation_table_is_OVERWRITE_and_ENFORCED_never_IF_NOT_EXISTS(self) -> None:
        """§1.1 RELATION-TABLE row: ``IF NOT EXISTS`` is a MEASURED silent no-op on an
        existing edge table (#107's shape). ``OVERWRITE`` is the only clause that lands a
        changed ``IN``/``OUT``/``ENFORCED``, and ``ENFORCED`` (Fork F) is the only guard
        that validates BOTH endpoints and covers ``INSERT RELATION`` (§4)."""
        statement = _member_of_statement(generate_keep_ddl())
        assert statement.startswith(f"DEFINE TABLE OVERWRITE {MEMBER_OF_RELATION} "), (
            f"member_of's relation clause must be OVERWRITE — IF NOT EXISTS is a measured "
            f"silent no-op on an existing edge table (§1.1): {statement!r}"
        )
        assert is_enforced(statement), f"member_of must be declared ENFORCED (Fork F): {statement!r}"

    def test_the_word_ALTER_appears_in_no_statement(self) -> None:
        """§1.3: ``ALTER`` cannot CREATE a field, and ``ALTER … IF EXISTS`` on a missing
        one silently no-ops — adopting it re-commits #107 on the fresh-DB path."""
        offenders = [
            statement for statement in _keep_statements() if re.search(r"\bALTER\b", statement, re.I)
        ]
        assert not offenders, offenders

    def test_the_generator_returns_the_house_terminated_shape(self) -> None:
        """Every other ``generate_*_ddl`` returns ``";\\n".join(...) + ";\\n"``. A slice
        that did not would break the caller's ``BEGIN … COMMIT`` wrap."""
        ddl = generate_keep_ddl()
        assert ddl.endswith(";\n")
        assert _statements(ddl)

    def test_the_generator_emits_keep_fields_not_just_the_table_name(self) -> None:
        """CONTROL: a generator emitting a bare ``DEFINE TABLE`` and ZERO ``DEFINE
        FIELD`` would make ``test_every_keep_field_definition_is_OVERWRITE`` vacuously
        green — the signature failure of a mechanical gate. It DEMANDS fields."""
        fields = [
            statement
            for statement in _keep_statements()
            if _DEFINE_FIELD.match(statement) and f" ON {KEEP_TABLE} " in f"{statement} "
        ]
        assert fields, f"the slice for {KEEP_TABLE!r} emits no DEFINE FIELD at all"

    def test_keep_and_member_of_are_FOLDED_into_the_global_generate_ddl(self) -> None:
        """Variant A (Emission plan step 4): ``keep`` + ``member_of`` are folded into the
        global ``generate_ddl`` so the primary ``write_store.ensure_ready()`` creates the
        tables the moment packet 60 ships — without wiring a ``KeepStore`` into
        ``build_app_context``. A build that shipped only the standalone slice would leave
        production without the tables until a store is wired in."""
        full = generate_ddl(dim=NONDEFAULT_DIM)
        assert f"DEFINE TABLE IF NOT EXISTS {KEEP_TABLE} SCHEMAFULL" in full, (
            "keep is NOT folded into generate_ddl() — the table will not exist in "
            "production until a KeepStore is wired in (Emission plan)"
        )
        assert MEMBER_OF_RELATION in relation_table_statements(full), (
            "member_of is NOT folded into generate_ddl()"
        )
        assert any(
            _DEFINE_FIELD.match(statement) and f" ON {KEEP_TABLE} " in f"{statement} "
            for statement in _statements(full)
        ), "generate_ddl() carries the keep table but none of its fields"

    def test_the_keep_slice_ROUTES_THROUGH_the_shared_field_emitter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ONE IMPLEMENTATION, proven by MUTATION: nothing REQUIRES the keep slice to
        CALL ``_define_field`` — a hand-written ``DEFINE FIELD`` string would pass every
        clause pin while silently not sharing the #107 ``OVERWRITE`` policy. Perturb the
        shared emitter; the emitted DDL must move."""
        original = surreal_schema._define_field
        monkeypatch.setattr(
            surreal_schema,
            "_define_field",
            lambda *args, **kwargs: f"{original(*args, **kwargs)} COMMENT 'keep-mutation-probe'",
        )
        assert "keep-mutation-probe" in generate_keep_ddl(), (
            "the keep slice does not route through surreal_schema._define_field"
        )

    def test_the_member_of_slice_ROUTES_THROUGH_define_relation_table(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ONE IMPLEMENTATION, by MUTATION: the ``member_of`` edge table must be emitted
        by the SHARED ``_define_relation_table`` (which owns the ``OVERWRITE … ENFORCED``
        policy), not a hand-written string. Perturb it; the DDL must move."""
        original = surreal_schema._define_relation_table
        monkeypatch.setattr(
            surreal_schema,
            "_define_relation_table",
            lambda *args, **kwargs: f"{original(*args, **kwargs)} COMMENT 'edge-mutation-probe'",
        )
        assert "edge-mutation-probe" in generate_keep_ddl(), (
            "the member_of slice does not route through surreal_schema._define_relation_table"
        )


class TestTheKeepClosedDomainsAreDerivedIntoTheDdl:
    """ONE IMPLEMENTATION, proven by MUTATION rather than by reading the source. The
    ``type``/``rank`` ASSERTs must be GENERATED FROM ``_KEEP_TYPES`` / ``_KEEP_RANKS``
    at CALL TIME (the ``_principal_statements`` idiom), never hand-typed beside them — a
    frozen import-time ASSERT cannot move under a runtime monkeypatch of the tuple."""

    def test_changing_the_KEEP_TYPES_tuple_changes_the_emitted_ASSERT(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        before = generate_keep_ddl()
        monkeypatch.setattr(
            surreal_schema, "_KEEP_TYPES", (*surreal_schema._KEEP_TYPES, "mutation_probe_type")
        )
        after = generate_keep_ddl()
        assert after != before, (
            "adding a keep type changed no emitted DDL — the type ASSERT is a hand-typed twin "
            "of _KEEP_TYPES (or a frozen import-time constant) rather than a CALL-TIME derivation"
        )
        assert "mutation_probe_type" in after

    def test_changing_the_KEEP_RANKS_tuple_changes_the_emitted_ASSERT(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        before = generate_keep_ddl()
        monkeypatch.setattr(
            surreal_schema, "_KEEP_RANKS", (*surreal_schema._KEEP_RANKS, "mutation_probe_rank")
        )
        after = generate_keep_ddl()
        assert after != before, (
            "adding a rank changed no emitted DDL — the rank ASSERT is a hand-typed twin of "
            "_KEEP_RANKS (or a frozen import-time constant) rather than a CALL-TIME derivation"
        )
        assert "mutation_probe_rank" in after

    def test_every_ruled_type_and_rank_reaches_the_ddl(self) -> None:
        """Membership control alongside the mutation pins: an over-narrow ASSERT that
        dropped a legal value would silently break that value forever."""
        ddl = generate_keep_ddl()
        missing_type = [value for value in _KEEP_TYPES if f"'{value}'" not in ddl]
        missing_rank = [value for value in _KEEP_RANKS if f"'{value}'" not in ddl]
        assert not missing_type, f"keep types absent from the DDL: {missing_type}"
        assert not missing_rank, f"member_of ranks absent from the DDL: {missing_rank}"

    def test_type_has_NO_default(self) -> None:
        """Fork B: ``type`` is the essential discriminator — every create must CHOOSE it,
        so the ``type`` field-def carries NO ``DEFAULT`` (a silent default would mislabel
        keeps). Contrast ``rank``, which DOES default."""
        type_field = _field_statement(_keep_statements(), KEEP_TABLE, "type")
        assert "DEFAULT" not in type_field.upper(), (
            f"keep.type must carry NO DEFAULT — every create must choose it (Fork B): {type_field!r}"
        )
        assert "ASSERT" in type_field.upper(), (
            f"keep.type must carry the closed-domain ASSERT: {type_field!r}"
        )

    def test_rank_DEFAULTS_to_contributor(self) -> None:
        """Fork C: ``rank`` DEFAULT ``'contributor'`` (the flat plain-collaborator today),
        so an ``add-household`` that names no rank takes it."""
        rank_field = _field_statement(_keep_statements(), MEMBER_OF_RELATION, "rank")
        assert "DEFAULT" in rank_field.upper() and f"'{_KEEP_RANK_CONTRIBUTOR}'" in rank_field, rank_field

    def test_the_ruled_type_domain_is_EXACTLY_the_closed_set(self) -> None:
        """⚠ THE QUANTIFIER PIN: pin the RULED SET ∀, not just known-bad-rejected +
        known-good-accepted. The derivation + membership pins ALL PASS on a build that
        WIDENS the domain (``_KEEP_TYPES += 'workspace'``): the ASSERT still derives from
        the tuple and every ruled value still reaches the DDL. A widening slips through
        the whole contract unless the set itself is pinned as an invariant."""
        assert set(_KEEP_TYPES) == {"project", "team", "session", "dm"}, (
            f"the ruled keep-type domain is {{project, team, session, dm}} (Fork B); "
            f"_KEEP_TYPES={_KEEP_TYPES!r} — if you changed it deliberately, update this pin and say so"
        )

    def test_the_ruled_rank_domain_is_EXACTLY_contributor_today(self) -> None:
        """⚠ THE FLATNESS PIN (Fork C): today ``rank`` is FLAT — a single-value
        ``{contributor}`` domain MAKES that flatness a store invariant, and it is
        mutation-provable. A build that widened ``_KEEP_RANKS`` early (before packet 61's
        seam) REDS here, carrying 'if you differentiated the rank seam deliberately,
        update this pin and KEEP contributor (widening is safe; narrowing is a data
        migration, §1.4)'."""
        assert set(_KEEP_RANKS) == {"contributor"}, (
            f"the ruled member_of.rank domain is FLAT today — exactly {{contributor}} (Fork C); "
            f"_KEEP_RANKS={_KEEP_RANKS!r}"
        )


class TestTheMemberOfEdgeIsDeclared:
    """The DELIBERATE DECLARATION, and the exemption door pinned shut from THIS side.

    RED today: the STUB emits no member_of relation table, so the ∀ pins that read the
    emitted set fail. GREEN today: the two declaration pins — this contract already added
    ``member_of`` to ``KNOWN_RELATION_EDGES`` and did NOT add it to
    ``DEFERRED_TO_PACKET_43``.

    ⛔ Kills wrong-build W-C (escape the ∀ by widening the exemption), from a file the
    packet-60 builder IS running — the ``test_blocks_edge.py::TestTheBlocksEdgeIsDeclared``
    model. It does NOT remove the obligation to run ``test_enforced_relations.py`` (whose
    ∀ sweep + exact-set pin still guard the exemption's exact contents)."""

    def test_the_schema_exports_KEEP_TABLE_and_MEMBER_OF_RELATION_constants(self) -> None:
        """The table/edge names are module CONSTANTS, like their siblings — never a
        literal typed at each site."""
        assert getattr(surreal_schema, "KEEP_TABLE", None) == "keep", (
            f"surreal_schema must export KEEP_TABLE == 'keep', got "
            f"{getattr(surreal_schema, 'KEEP_TABLE', None)!r}"
        )
        assert getattr(surreal_schema, "MEMBER_OF_RELATION", None) == "member_of", (
            f"surreal_schema must export MEMBER_OF_RELATION == 'member_of', got "
            f"{getattr(surreal_schema, 'MEMBER_OF_RELATION', None)!r}"
        )

    def test_member_of_is_in_the_DECLARED_edge_set(self) -> None:
        assert KNOWN_RELATION_EDGES.get(MEMBER_OF_RELATION) == (PRINCIPAL_TABLE, KEEP_TABLE), (
            "member_of must be declared in _enforced_relations_scaffold.KNOWN_RELATION_EDGES "
            f"with its endpoints, and they must be ({PRINCIPAL_TABLE}, {KEEP_TABLE})"
        )

    def test_member_of_is_NOT_in_the_DEFERRED_exemption_set(self) -> None:
        """⛔ W-C. The ∀ ENFORCED pin takes exactly ONE deny-by-default exemption,
        ``DEFERRED_TO_PACKET_43`` (the two code-graph edges). ``member_of`` is packet
        60's, ships ENFORCED from BIRTH (Fork F) — deferring its guard is a SCOPE decision
        for the operator, never a way to silence a red ∀ pin."""
        from _enforced_relations_scaffold import DEFERRED_TO_PACKET_43

        assert MEMBER_OF_RELATION not in DEFERRED_TO_PACKET_43, (
            f"{MEMBER_OF_RELATION} was added to DEFERRED_TO_PACKET_43 — that set exempts the two "
            f"code-graph edges (refers/answers_to). Deferring the member_of guard is an operator "
            f"scope decision; Fork F says member_of ships ENFORCED from BIRTH"
        )

    def test_the_universal_pin_now_covers_member_of(self) -> None:
        """The ∀ instrument reaches the sixth edge once emitted. RED today (nothing emits
        it), and the pin that makes ``member_of`` subject to the same law as its siblings.
        Re-asserted HERE so a packet-60 builder reading only its own contract sees it."""
        emitted = every_emitted_relation_table()
        assert MEMBER_OF_RELATION in emitted, (
            f"the ∀ sweep over every DDL generator found no {MEMBER_OF_RELATION!r} relation "
            f"table. Emitted: {sorted(emitted)}"
        )
        _label, statement = emitted[MEMBER_OF_RELATION]
        assert is_enforced(statement), statement


class TestTheMemberOfEdgeIsEmittedByBOTHGenerationPaths:
    """RED today. ⛔ The pin that kills "declared in the wrong place".

    ``member_of`` must be emitted IDENTICALLY by ``generate_keep_ddl`` (a future
    ``KeepStore.ensure_ready``) AND ``generate_ddl`` (the primary store, Variant A). If
    one path defines it and the other does not, the store built by the other path holds
    ``member_of`` as an AUTO-CREATED ``TYPE ANY`` table on first RELATE (store §5), which
    silently discards the ``IN``/``OUT``/``ENFORCED`` guard — a defect no per-path pin can
    see."""

    @pytest.mark.parametrize(
        ("label", "generator"),
        [
            ("generate_keep_ddl", generate_keep_ddl),
            ("generate_ddl", lambda: generate_ddl(dim=NONDEFAULT_DIM)),
        ],
    )
    def test_the_path_emits_the_member_of_relation_table(self, label: str, generator: Any) -> None:
        assert _member_of_statement(generator()), label

    def test_BOTH_paths_emit_the_IDENTICAL_member_of_statement(self) -> None:
        """⛔ Kills a build declaring the edge TWICE, differently. DERIVED equality — not
        two hand-written expectations that could agree with each other and disagree with
        production."""
        from_slice = _member_of_statement(generate_keep_ddl())
        from_full = _member_of_statement(generate_ddl(dim=NONDEFAULT_DIM))
        assert from_slice == from_full, (
            "the keep SLICE and the FULL ddl emit DIFFERENT member_of declarations. There "
            "must be exactly one emitter (surreal_schema::_member_of_statements), consumed "
            f"by both: slice={from_slice!r} full={from_full!r}"
        )

    def test_member_of_is_declared_AFTER_keep_in_BOTH_paths(self) -> None:
        """``member_of``'s ``OUT keep`` endpoint must be defined before the edge — so the
        ``keep`` DEFINE TABLE precedes ``member_of``'s in every path that emits both."""
        for label, generator in (
            ("generate_keep_ddl", generate_keep_ddl),
            ("generate_ddl", lambda: generate_ddl(dim=NONDEFAULT_DIM)),
        ):
            emitted = statements(generator())
            keep_at = next(
                (
                    i
                    for i, s in enumerate(emitted)
                    if s.startswith(f"DEFINE TABLE IF NOT EXISTS {KEEP_TABLE} ")
                ),
                None,
            )
            member_of_at = next(
                (i for i, s in enumerate(emitted) if f" {MEMBER_OF_RELATION} TYPE RELATION" in s), None
            )
            assert keep_at is not None, f"{label}: no DEFINE TABLE for {KEEP_TABLE!r}"
            assert member_of_at is not None, f"{label}: no {MEMBER_OF_RELATION!r} relation table"
            assert keep_at < member_of_at, (
                f"{label}: {MEMBER_OF_RELATION!r} (pos {member_of_at}) is declared BEFORE the "
                f"{KEEP_TABLE!r} table it names as its OUT endpoint (pos {keep_at})"
            )

    def test_member_of_is_declared_AFTER_principal_in_the_FULL_ddl(self) -> None:
        """In ``generate_ddl`` (which composes both endpoint slices) the ``IN principal``
        endpoint must precede the edge too. (``generate_keep_ddl`` does NOT emit
        ``principal`` — it presumes the primary store readied it first.)"""
        emitted = statements(generate_ddl(dim=NONDEFAULT_DIM))
        principal_at = next(
            (
                i
                for i, s in enumerate(emitted)
                if s.startswith(f"DEFINE TABLE IF NOT EXISTS {PRINCIPAL_TABLE} ")
            ),
            None,
        )
        member_of_at = next(
            (i for i, s in enumerate(emitted) if f" {MEMBER_OF_RELATION} TYPE RELATION" in s), None
        )
        assert principal_at is not None, f"generate_ddl emits no DEFINE TABLE for {PRINCIPAL_TABLE!r}"
        assert member_of_at is not None, f"generate_ddl emits no {MEMBER_OF_RELATION!r} relation table"
        assert principal_at < member_of_at, (
            f"member_of (pos {member_of_at}) is declared BEFORE its IN endpoint {PRINCIPAL_TABLE!r} "
            f"(pos {principal_at}) in generate_ddl"
        )


class TestTheMemberOfEdgeIsGuardedFromBirth:
    """RED today. The clause pins — ``ENFORCED``, ``OVERWRITE``, endpoint types — for the
    edge 60 owns, re-asserted here (they also parametrise onto ``member_of`` in
    ``test_enforced_relations.py`` once emitted)."""

    @pytest.mark.parametrize("label", ["generate_keep_ddl", "generate_ddl"])
    def test_member_of_carries_ENFORCED_in_its_own_slice(self, label: str) -> None:
        ddl = generate_keep_ddl() if label == "generate_keep_ddl" else generate_ddl(dim=NONDEFAULT_DIM)
        statement = _member_of_statement(ddl)
        assert is_enforced(statement), (
            f"{label}: member_of must be declared ENFORCED from birth (Fork F): {statement!r}"
        )

    def test_member_of_declares_IN_principal_OUT_keep(self) -> None:
        """``ENFORCED`` is meaningless without ``IN``/``OUT``: the clause validates the
        endpoints EXIST, the typing validates they are of the right TABLE."""
        statement = _member_of_statement(generate_keep_ddl())
        assert f"IN {PRINCIPAL_TABLE} OUT {KEEP_TABLE}" in statement, (
            f"member_of must declare IN {PRINCIPAL_TABLE} OUT {KEEP_TABLE}: {statement!r}"
        )


# =========================================================================== #
# LEG 2 — LIVE round-trip on ws://127.0.0.1:18000 (NEVER :18500). NO skip marker:
# an unreachable store is a LOUD failure, not a skip.
# =========================================================================== #


class TestTheKeepSchemaAppliesToTheLiveEngine:
    """The generated DDL against the real engine — the recipe proven on the cake."""

    async def test_the_slice_creates_the_keep_and_member_of_tables(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        tables = set((await run(connection, "INFO FOR DB")).get("tables", {}))
        assert KEEP_TABLE in tables, f"the keep table was not created: {sorted(tables)}"
        assert MEMBER_OF_RELATION in tables, f"the member_of edge table was not created: {sorted(tables)}"

    async def test_the_slice_is_safely_re_appliable(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """``ensure_ready`` re-applies the DDL on EVERY boot. A statement that raises on
        re-application is a boot-time crash, not a style issue."""
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await apply_ddl(connection, generate_keep_ddl(), url=env.url)


class TestTheKeepRoundTrip:
    """The ``keep`` table (live behavioural) — Fork B's property set."""

    async def test_create_keep_reads_back_by_id_and_by_keeper(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await _seed_principal(connection, _KEEPER_ID, _KEEPER_EMAIL)
        await _seed_keep(connection, "k1", _KEEPER_ID, keep_type="project", name="Q3 launch")
        by_id = _one(
            await run(
                connection,
                f"SELECT id, keeper, type, name, created_at FROM type::record('{KEEP_TABLE}', 'k1')",
            )
        )
        assert by_id["type"] == "project"
        assert by_id["name"] == "Q3 launch"
        assert str(by_id["keeper"]).endswith(_KEEPER_ID)
        by_keeper = await run(
            connection,
            f"SELECT id FROM {KEEP_TABLE} WHERE keeper = $p",
            {"p": RecordID(PRINCIPAL_TABLE, _KEEPER_ID)},
        )
        assert by_keeper, "the keep did not read back by its keeper"

    async def test_multiple_keeps_with_no_name_coexist(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Fork B / §1.8: ``name`` is ``option<>`` and NON-unique — a ``dm`` keep carries
        no meaningful name, so multiple keeps with NONE name coexist. TWO keeps (small-N
        would let a build that rejected the second NONE pass)."""
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await _seed_principal(connection, _KEEPER_ID, _KEEPER_EMAIL)
        await _seed_keep(connection, "dm1", _KEEPER_ID, keep_type="dm")  # name omitted → NONE
        await _seed_keep(connection, "dm2", _KEEPER_ID, keep_type="dm")  # name omitted → NONE
        for keep_id in ("dm1", "dm2"):
            row = _one(
                await run(
                    connection,
                    f"SELECT id, name FROM type::record('{KEEP_TABLE}', $id)",
                    {"id": keep_id},
                )
            )
            assert row["name"] is None, f"{keep_id} should carry name=None"

    async def test_empty_string_name_rejected_while_none_is_accepted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Fork B: ``name`` is ``option<string>`` with the trim-aware non-empty ASSERT —
        SKIPPED on NONE (a nameless keep is legal), FIRES on a present empty string (a
        garbage ``name = ''`` is rejected). The ``principal.subject`` idiom exactly."""
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await _seed_principal(connection, _KEEPER_ID, _KEEPER_EMAIL)
        # NONE accepted (ASSERT skipped) …
        await _seed_keep(connection, "noname", _KEEPER_ID, keep_type="session")
        # … a present empty string rejected (ASSERT fires).
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation on present empty value
            await _seed_keep(connection, "empty", _KEEPER_ID, keep_type="project", name="")

    async def test_unknown_type_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await _seed_principal(connection, _KEEPER_ID, _KEEPER_EMAIL)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation
            await _seed_keep(connection, "badtype", _KEEPER_ID, keep_type="not_a_type")

    async def test_a_plausible_but_unruled_type_is_rejected_by_the_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ THE QUANTIFIER PIN, live belt-and-braces. The offline exact-set pin catches a
        domain widened THROUGH the tuple; this catches one widened in the store's runtime
        DDL by ANY means. ``workspace`` is PLAUSIBLE-but-unruled (exactly what a careless
        widening would add) — a build that widened the ruled set would ACCEPT it, so the
        store MUST reject it."""
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await _seed_principal(connection, _KEEPER_ID, _KEEPER_EMAIL)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation (unruled type)
            await _seed_keep(connection, "ws", _KEEPER_ID, keep_type="workspace")

    async def test_every_ruled_type_is_accepted_positive_control(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """THE POSITIVE CONTROL for the rejection pins: an over-strict ASSERT (accepting
        only one type) would silently pass both negatives while breaking every real create.
        Every ruled type must be accepted."""
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await _seed_principal(connection, _KEEPER_ID, _KEEPER_EMAIL)
        for index, keep_type in enumerate(_KEEP_TYPES):
            await _seed_keep(connection, f"ok{index}", _KEEPER_ID, keep_type=keep_type)
            row = _one(
                await run(connection, f"SELECT type FROM type::record('{KEEP_TABLE}', 'ok{index}')")
            )
            assert row["type"] == keep_type

    async def test_type_is_REQUIRED_a_keep_with_no_type_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Fork B: ``type`` has NO default and is a required (non-``option``) SCHEMAFULL
        field, so a keep omitting it is rejected. (Contrast a defaulted column, which the
        store may omit.)"""
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await _seed_principal(connection, _KEEPER_ID, _KEEPER_EMAIL)
        with pytest.raises(Exception):  # noqa: B017 - engine required-field rejection
            await _seed_keep(connection, "notype", _KEEPER_ID, include_type=False)

    async def test_keeper_is_REQUIRED_a_keep_with_no_keeper_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Fork A: ``keeper`` is a required ``record<principal>`` link (greenfield table,
        §1.4 N/A) — a keep with no keeper is a space belonging to nobody, rejected."""
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        with pytest.raises(Exception):  # noqa: B017 - engine required-field rejection
            await _seed_keep(connection, "nokeeper", _KEEPER_ID, include_keeper=False)

    async def test_keep_rejects_an_undeclared_field(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """SCHEMAFULL discipline (§1.7): an undeclared top-level key RAISES, so a typo'd
        column can never silently become a phantom attribute."""
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await _seed_principal(connection, _KEEPER_ID, _KEEPER_EMAIL)
        with pytest.raises(Exception):  # noqa: B017 - engine SCHEMAFULL rejection
            await run(
                connection,
                f"CREATE type::record('{KEEP_TABLE}', $id) CONTENT "
                f"{{ keeper: type::record('{PRINCIPAL_TABLE}', $kid), type: 'project', rogue: 'x' }}",
                {"id": "rogue", "kid": _KEEPER_ID},
            )

    async def test_created_at_self_stamps(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """``created_at`` DEFAULT ``time::now()`` — the store OMITS it on write and the
        engine stamps a real datetime."""
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await _seed_principal(connection, _KEEPER_ID, _KEEPER_EMAIL)
        await _seed_keep(connection, "stamped", _KEEPER_ID, keep_type="team")
        row = _one(await run(connection, f"SELECT created_at FROM type::record('{KEEP_TABLE}', 'stamped')"))
        assert row["created_at"] is not None, "created_at did not self-stamp"


class TestTheKeeperIndexFires:
    """⚠ Fork A rider (load-bearing): PROVE the keeper index actually fires, so the field
    escapes store §4's "a graph TRAVERSAL never uses a secondary index" trap — the whole
    reason keepership is a FIELD LINK and not a ``keeps`` edge. An EXPLAIN plan, with a
    positive control (an unindexed predicate IS a TableScan) so the pin can never be
    silently vacuous."""

    @staticmethod
    def _operators(plan: Any) -> list[str]:
        found: list[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                for key in ("operator", "operation"):
                    op = node.get(key)
                    if isinstance(op, str):
                        found.append(op)
                for child in node.values():
                    walk(child)
            elif isinstance(node, list):
                for child in node:
                    walk(child)

        walk(plan)
        return found

    @staticmethod
    def _scans_table(plan: Any, table: str) -> bool:
        found = False

        def walk(node: Any) -> None:
            nonlocal found
            if isinstance(node, dict):
                attributes = node.get("attributes")
                if (
                    node.get("operator") == "TableScan"
                    and isinstance(attributes, dict)
                    and attributes.get("table") == table
                ):
                    found = True
                for child in node.values():
                    walk(child)
            elif isinstance(node, list):
                for child in node:
                    walk(child)

        walk(plan)
        return found

    async def test_WHERE_keeper_uses_the_index_not_a_keep_tablescan(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)

        # The schema under EXPLAIN is the REAL schema (the index built), else EXPLAIN is
        # meaningless.
        keep_table_info = await run(connection, f"INFO FOR TABLE {KEEP_TABLE}")
        indexes = keep_table_info.get("indexes", {})
        assert any("keeper" in str(definition) for definition in indexes.values()), (
            f"keep.keeper index not built — the EXPLAIN controls are invalid: {keep_table_info!r}"
        )

        # POSITIVE CONTROL — the plan-inspection can SEE a keep TableScan (an unindexed
        # predicate over `type`, which has no index). If TableScan rendered differently
        # this fails, so the main pin is never silently vacuous (coverage is checked).
        unindexed_plan = await run(
            connection, f"SELECT id FROM {KEEP_TABLE} WHERE type = $probe EXPLAIN", {"probe": "project"}
        )
        assert self._scans_table(unindexed_plan, KEEP_TABLE), (
            f"positive control failed: an unindexed `type =` predicate did NOT register as a "
            f"{KEEP_TABLE} TableScan — the plan format changed and the pin is now vacuous. "
            f"operators={self._operators(unindexed_plan)}"
        )

        # THE INVARIANT — `WHERE keeper = $p` must use the index, NOT a TableScan.
        keeper_plan = await run(
            connection,
            f"SELECT id FROM {KEEP_TABLE} WHERE keeper = $p EXPLAIN",
            {"p": RecordID(PRINCIPAL_TABLE, _KEEPER_ID)},
        )
        assert not self._scans_table(keeper_plan, KEEP_TABLE), (
            f"keep.keeper predicate is a {KEEP_TABLE} TableScan — the keeper index does not fire, "
            f"so the field fell into store §4's traversal-never-indexes trap the FIELD LINK was "
            f"chosen to avoid (Fork A). operators={self._operators(keeper_plan)}"
        )
        assert "IndexScan" in self._operators(keeper_plan), (
            f"expected an IndexScan for the indexed `keeper =` predicate. "
            f"operators={self._operators(keeper_plan)}"
        )


class TestTheMemberOfEdgeLiveBehaviour:
    """The ``member_of`` edge against the real engine — ENFORCED, defaulted rank,
    UNIQUE(in, out), the ``since`` stamp."""

    async def _seed_keeper_and_keep(self, connection: SurrealConnection) -> None:
        await _seed_principal(connection, _KEEPER_ID, _KEEPER_EMAIL)
        await _seed_keep(connection, "k1", _KEEPER_ID, keep_type="project", name="space")

    async def test_a_relate_between_two_REAL_endpoints_is_accepted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await self._seed_keeper_and_keep(connection)
        await _seed_principal(connection, _MEMBER_ID, _MEMBER_EMAIL)
        await _relate_member_of(connection, _MEMBER_ID, "k1")
        rows = await run(
            connection,
            f"SELECT id FROM {MEMBER_OF_RELATION} WHERE out = $k",
            {"k": RecordID(KEEP_TABLE, "k1")},
        )
        assert rows, "a member_of RELATE between two REAL endpoints must be accepted"

    async def test_rank_defaults_to_contributor_when_unset(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await self._seed_keeper_and_keep(connection)
        await _seed_principal(connection, _MEMBER_ID, _MEMBER_EMAIL)
        await _relate_member_of(connection, _MEMBER_ID, "k1")  # rank omitted → DEFAULT
        row = _one(
            await run(
                connection,
                f"SELECT rank FROM {MEMBER_OF_RELATION} WHERE out = $k",
                {"k": RecordID(KEEP_TABLE, "k1")},
            )
        )
        assert row["rank"] == _KEEP_RANK_CONTRIBUTOR, (
            f"member_of.rank did not default to contributor: {row!r}"
        )

    async def test_an_unruled_rank_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """The rank ASSERT: a value outside ``_KEEP_RANKS`` is rejected. Positive control
        provided by ``test_rank_defaults_to_contributor_when_unset`` (a legal rank lands)."""
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await self._seed_keeper_and_keep(connection)
        await _seed_principal(connection, _MEMBER_ID, _MEMBER_EMAIL)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation (unruled rank)
            await _relate_member_of(connection, _MEMBER_ID, "k1", rank="overlord")

    async def test_a_relate_to_a_GHOST_keep_is_REFUSED_by_ENFORCED(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Fork F / store §4: ``ENFORCED`` refuses a RELATE whose OUT endpoint (the keep)
        does not exist — the dangling-edge hazard (#105) closed on a VIRGIN store. The
        dirty-store migration proof is :class:`TestTheMemberOfEnforcedFlipMigratesADirtyStore`."""
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await _seed_principal(connection, _MEMBER_ID, _MEMBER_EMAIL)
        ghost_keep = ghost_id("ghost_keep")
        assert not await record_exists(connection, KEEP_TABLE, ghost_keep)
        with pytest.raises(Exception):  # noqa: B017 - the engine's NotFoundError surface
            await _relate_member_of(connection, _MEMBER_ID, ghost_keep)

    async def test_UNIQUE_in_out_rejects_a_DUPLICATE_membership(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Fork F: UNIQUE(in, out) makes a double-add of the SAME (principal, keep) pair a
        loud ERR, not a second edge (the store's idempotency backstop). Positive control:
        a DIFFERENT (principal, keep) pair is accepted."""
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await self._seed_keeper_and_keep(connection)
        await _seed_principal(connection, _MEMBER_ID, _MEMBER_EMAIL)
        await _relate_member_of(connection, _MEMBER_ID, "k1")
        with pytest.raises(Exception):  # noqa: B017 - engine UNIQUE index rejection
            await _relate_member_of(connection, _MEMBER_ID, "k1")
        # POSITIVE CONTROL — a DIFFERENT member on the same keep IS accepted.
        await _seed_principal(connection, "member_carol", "carol@example.com")
        await _relate_member_of(connection, "member_carol", "k1")

    async def test_since_self_stamps(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, env = admin_db
        await _apply_keep_and_principal_schema(connection, env.url)
        await self._seed_keeper_and_keep(connection)
        await _seed_principal(connection, _MEMBER_ID, _MEMBER_EMAIL)
        await _relate_member_of(connection, _MEMBER_ID, "k1")
        row = _one(
            await run(
                connection,
                f"SELECT since FROM {MEMBER_OF_RELATION} WHERE out = $k",
                {"k": RecordID(KEEP_TABLE, "k1")},
            )
        )
        assert row["since"] is not None, "member_of.since did not self-stamp"


# =========================================================================== #
# LEG 3 — THE DIRTY-STORE MIGRATIONS (THE TEST ENVIRONMENT IS A FICTION; §1.6).
#
# Every ordinary test mints a VIRGIN database, and on a virgin database ANY clause
# creates the table with whatever the generator says — so a guard that never MIGRATES
# (the #107 shape) is invisible to every offline pin and every ordinary live pin. These
# pins install an OLD world on an EXISTING store, dirty it, then apply today's DDL.
# =========================================================================== #


class TestTheOldMemberOfWorldIsGenuinelyOlder:
    """RED today, and the pin that keeps the migration section honest: if the OLD world is
    byte-identical to today's, every migration pin migrates a schema to ITSELF and proves
    nothing while looking green. (At the STUB stage the derivation RAISES because nothing
    is emitted — a legitimate RED.)"""

    def test_the_old_member_of_world_DIFFERS_from_todays_keep_ddl(self) -> None:
        old = old_world_ddl(MEMBER_OF_RELATION, PRINCIPAL_TABLE, KEEP_TABLE, generate_keep_ddl)
        assert old != generate_keep_ddl(), (
            "re-emitting member_of with enforced=False does not change the DDL, so today's "
            "generator already emits it un-enforced — the ENFORCED flip has not happened"
        )


class TestTheMemberOfEnforcedFlipMigratesADirtyStore:
    """⛔ THE #107 SHAPE for ``member_of``, load-bearing (store checklist §F). ``IF NOT
    EXISTS`` is a MEASURED silent no-op on an existing edge table and ``OVERWRITE`` is the
    only clause that lands the flip (§1.1). A virgin-DB fixture cannot see it. These pins
    install the OLD (un-enforced) member_of world, dirty it with a dangling edge legal
    under it, then apply today's ``generate_keep_ddl``.

    RED today (the STUB emits nothing); the BASELINE / positive-control / survival legs
    are GREEN after the builder lands the edge (they describe the OLD world or a preserved
    behaviour)."""

    async def _dirty_old_world(
        self, connection: SurrealConnection, env: SurrealEnv
    ) -> tuple[str, str]:
        """Install the OLD (un-enforced) member_of world and write ONE dangling edge.

        Returns ``(live_member_id, ghost_keep_id)`` — a real IN principal and an OUT keep
        verified NOT to exist. ``principal`` (the IN endpoint + the keeper link target) is
        applied first; the OLD keep+member_of world (member_of un-enforced) second.
        """
        await apply_ddl(connection, generate_principal_ddl(), url=env.url)
        await apply_ddl(
            connection,
            old_world_ddl(MEMBER_OF_RELATION, PRINCIPAL_TABLE, KEEP_TABLE, generate_keep_ddl),
            url=env.url,
        )
        live_member = ghost_id("live_member")
        await _seed_principal(connection, live_member, "live@example.com")
        ghost_keep = ghost_id("ghost_keep")
        assert not await record_exists(connection, KEEP_TABLE, ghost_keep), (
            "the negative fixture's OUT keep must genuinely NOT exist"
        )
        await _relate_member_of(connection, live_member, ghost_keep)
        return live_member, ghost_keep

    async def _seed_real_keep(self, connection: SurrealConnection, keep_id: str) -> None:
        """A real keep needs a keeper principal — seed both."""
        keeper = ghost_id("keeper")
        await _seed_principal(connection, keeper, f"{keeper}@example.com")
        await _seed_keep(connection, keep_id, keeper, keep_type="project")

    async def test_BASELINE_the_old_world_really_ACCEPTS_a_dangling_edge(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Without this control, "the guard is live after migrating" could be true because
        it was ALWAYS live — and the migration never tested. GREEN before and after the flip
        (it describes the OLD world)."""
        connection, env = migration_db
        _live_member, ghost_keep = await self._dirty_old_world(connection, env)
        rows = await run(connection, f"SELECT id FROM {MEMBER_OF_RELATION}")
        assert rows, (
            f"the OLD (un-enforced) member_of definition was supposed to ACCEPT a RELATE to the "
            f"non-existent {KEEP_TABLE}:{ghost_keep} — if it did not, the fixture installs the wrong world"
        )

    async def test_the_guard_is_LIVE_after_applying_todays_ddl_to_a_DIRTY_store(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """RED today. THE load-bearing pin: a definition that emits perfectly and never
        LANDS is invisible to every offline pin. The rejection is demanded BEHAVIOURALLY
        (a new dangling RELATE is refused), never by reading back a stored DDL string."""
        connection, env = migration_db
        live_member, _ghost_keep = await self._dirty_old_world(connection, env)
        await apply_ddl(connection, generate_keep_ddl(), url=env.url)

        fresh_ghost = ghost_id("still_absent")
        assert not await record_exists(connection, KEEP_TABLE, fresh_ghost)
        with pytest.raises(Exception):  # noqa: B017 - the engine's NotFoundError surface
            await _relate_member_of(connection, live_member, fresh_ghost)

    async def test_POSITIVE_CONTROL_a_REAL_endpoint_is_still_accepted_after_the_flip(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """A guard that refuses EVERYTHING is not a guard, it is an outage — and it would
        satisfy the pin above. GREEN after the flip."""
        connection, env = migration_db
        live_member, _ghost_keep = await self._dirty_old_world(connection, env)
        await apply_ddl(connection, generate_keep_ddl(), url=env.url)
        await self._seed_real_keep(connection, "real_keep")
        await _relate_member_of(connection, live_member, "real_keep")
        rows = await run(
            connection,
            f"SELECT id FROM {MEMBER_OF_RELATION} WHERE out = $k",
            {"k": RecordID(KEEP_TABLE, "real_keep")},
        )
        assert rows, "a member_of RELATE between two REAL endpoints must still be accepted after the flip"

    async def test_the_PRE_EXISTING_dangling_edge_SURVIVES_the_flip(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """GREEN today and after: ``ENFORCED`` is a write-path guard, NOT a retro-validation
        (§4). Pinned because the opposite belief is attractive — "we turned ENFORCED on, so
        the ghosts are gone." They are not; cleanup is a separate data migration."""
        connection, env = migration_db
        _live_member, ghost_keep = await self._dirty_old_world(connection, env)
        before = await run(connection, f"SELECT id FROM {MEMBER_OF_RELATION}")
        await apply_ddl(connection, generate_keep_ddl(), url=env.url)
        after = await run(
            connection,
            f"SELECT id, out FROM {MEMBER_OF_RELATION} WHERE out = $k",
            {"k": RecordID(KEEP_TABLE, ghost_keep)},
        )
        assert len(before) == 1, "fixture: exactly one dangling edge should exist pre-flip"
        assert after, "the pre-existing dangling edge must SURVIVE the flip (ENFORCED is not retroactive)"

    async def test_the_migration_is_IDEMPOTENT_on_an_already_migrated_store(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """``ensure_ready`` re-applies this DDL on EVERY boot, so a second and third apply
        must be a clean no-op that neither raises nor loses the guard."""
        connection, env = migration_db
        live_member, _ghost_keep = await self._dirty_old_world(connection, env)
        for _ in range(3):
            await apply_ddl(connection, generate_keep_ddl(), url=env.url)
        await self._seed_real_keep(connection, "real_keep")
        await _relate_member_of(connection, live_member, "real_keep")


class TestTheRankDomainWidensSafelyOnADirtyStore:
    """⚠ Fork C rider — the ONLY §1.4-relevant hazard in wave 1, and it is FUTURE. Growing
    ``_KEEP_RANKS`` while RETAINING ``'contributor'`` is a pure WIDENING (§1.4: rows intact,
    still writable, new value accepted). This pins that a member_of row written under the
    one-value DDL SURVIVES a widened DDL and stays writable, the new value is accepted, and
    — the POSITIVE CONTROL — the constraint is WIDER, not GONE (a garbage rank is STILL
    rejected). RED today (the STUB emits nothing)."""

    async def _member_of_row_under_todays_ddl(
        self, connection: SurrealConnection, env: SurrealEnv
    ) -> tuple[str, str]:
        """principal + keep + member_of (today's 1-value rank DDL), plus one edge at the
        default rank. Returns ``(member_id, keep_id)``."""
        await apply_ddl(connection, generate_principal_ddl(), url=env.url)
        await apply_ddl(connection, generate_keep_ddl(), url=env.url)
        keeper = ghost_id("keeper")
        member = ghost_id("member")
        await _seed_principal(connection, keeper, f"{keeper}@example.com")
        await _seed_principal(connection, member, f"{member}@example.com")
        await _seed_keep(connection, "wk", keeper, keep_type="project")
        await _relate_member_of(connection, member, "wk")  # rank defaults to contributor
        return member, "wk"

    async def test_widening_the_rank_domain_preserves_the_row_and_accepts_the_new_value(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        member, keep_id = await self._member_of_row_under_todays_ddl(*migration_db)
        connection, env = migration_db

        # WIDEN _KEEP_RANKS (retaining contributor) and re-apply the DDL (OVERWRITE fields).
        monkeypatch.setattr(surreal_schema, "_KEEP_RANKS", (_KEEP_RANK_CONTRIBUTOR, "steward"))
        await apply_ddl(connection, generate_keep_ddl(), url=env.url)

        # The existing row SURVIVES, still at contributor.
        row = _one(
            await run(
                connection,
                f"SELECT rank FROM {MEMBER_OF_RELATION} WHERE out = $k",
                {"k": RecordID(KEEP_TABLE, keep_id)},
            )
        )
        assert row["rank"] == _KEEP_RANK_CONTRIBUTOR, f"the pre-widen member_of row did not survive: {row!r}"

        # The NEW value is now accepted (the row is still writable — not poisoned).
        await run(
            connection,
            f"UPDATE {MEMBER_OF_RELATION} SET rank = 'steward' WHERE out = $k",
            {"k": RecordID(KEEP_TABLE, keep_id)},
        )
        widened = _one(
            await run(
                connection,
                f"SELECT rank FROM {MEMBER_OF_RELATION} WHERE out = $k",
                {"k": RecordID(KEEP_TABLE, keep_id)},
            )
        )
        assert widened["rank"] == "steward", "the widened rank value was not accepted after migration"
        assert member  # bind the seeded member id (documents the row's IN endpoint)

    async def test_POSITIVE_CONTROL_the_widened_constraint_is_WIDER_not_GONE(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A migration that "landed" by DROPPING the ASSERT would accept EVERYTHING and
        satisfy the pin above. So after widening, a value OUTSIDE the widened set must
        STILL be rejected — proving the constraint is wider, not gone."""
        _member, keep_id = await self._member_of_row_under_todays_ddl(*migration_db)
        connection, env = migration_db
        monkeypatch.setattr(surreal_schema, "_KEEP_RANKS", (_KEEP_RANK_CONTRIBUTOR, "steward"))
        await apply_ddl(connection, generate_keep_ddl(), url=env.url)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation (still outside the widened set)
            await run(
                connection,
                f"UPDATE {MEMBER_OF_RELATION} SET rank = 'overlord' WHERE out = $k",
                {"k": RecordID(KEEP_TABLE, keep_id)},
            )
