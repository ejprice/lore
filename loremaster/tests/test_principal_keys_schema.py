"""Contract — packet 49, the ``principal_key`` table SCHEMA (Legs 1 + 2).

Written by ``contract-49-1`` (2026-08-20). The builder builds FROM this; it writes
NO production code. HISTORICAL (authoring-time, 2026-08-20 RED phase): the emitter
surfaces were then stubs — ``generate_principal_key_ddl`` returned ``""``,
``_principal_key_statements`` returned ``[]``, and ``principal_key`` was NOT yet folded
into ``generate_ddl`` — so every pin was RED for the RIGHT reason (a behavioural failure
of the emitter, never an ImportError). Those surfaces are NOW BUILT AND GREEN:
``_principal_key_statements`` emits the real DDL, is folded into ``generate_ddl`` and is
consumed by the standalone ``generate_principal_key_ddl`` (``surreal_schema.py``). This
note is kept as the authoring origin, not a current claim (retired 2026-08-23,
packet 61a-w3, #398/#399).

DESIGN (the work order, executed verbatim — never re-transcribed):
``docs/design/2026-08-20-packet49-cli-keys.md`` §F7 (module layout + the exact
``principal_key`` field/index table) and §F2 (the cascade forward-scope PIN THE
MISS). Store law binds: ``docs/reference/surrealdb-31-capabilities.md`` §1.1
(TABLE/INDEX ``IF NOT EXISTS``, FIELD ``OVERWRITE``, ALTER is a trap §1.3), §1.4 (a
NEW field on a POPULATED table must be ``option<>`` — N/A here: ``principal_key`` is
a brand-new empty table, so its owner link is REQUIRED), §1.6 (the dirty-store
migration blind spot), §1.8 (UNIQUE over ``option<>`` — N/A: both UNIQUE indexes are
over REQUIRED columns), §2 (CONTENT writes; ⚠ ``SELECT *`` OMITS a NONE ``option<>``
column → ``KeyError``, explicit projection reads ``None``), §4 (``record<t>`` links
do NOT auto-clean + no existence check — probed 2026-08-20).

THE ``principal_key`` SCHEMA (design §F7, the interface freeze the builder implements):

    | column      | type              | clause                   | why                                |
    |-------------|-------------------|--------------------------|------------------------------------|
    | hash        | string            | non-empty ASSERT         | SHA-512 hex; UNIQUE; the credential |
    | name        | string            | non-empty ASSERT         | the key label; UNIQUE(principal,name)|
    | principal   | record<principal> | (link) REQUIRED          | the owner (new empty table ⇒ required)|
    | created_at  | datetime          | DEFAULT time::now()      | engine-stamped mint time            |
    | expires_at  | option<datetime>  | (none — no DEFAULT)      | optional key expiry; NONE = never   |
    | revoked_at  | option<datetime>  | (none — no DEFAULT)      | NONE until revoked; IS NONE = active |

    Indexes: UNIQUE(hash), UNIQUE(principal, name).

LIVE store: ws://127.0.0.1:18000 (NEVER :18500). NO skip marker — an unreachable
store is a LOUD failure, not a skip.
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

_DEFINE_TABLE = re.compile(r"^\s*DEFINE\s+TABLE\b", re.IGNORECASE)
_DEFINE_FIELD = re.compile(r"^\s*DEFINE\s+FIELD\b", re.IGNORECASE)
_DEFINE_INDEX = re.compile(r"^\s*DEFINE\s+INDEX\b", re.IGNORECASE)

# Every ``record<principal>`` DEFINE FIELD, captured as ``(field, table)`` — the
# forward-scope PIN THE MISS scanner (design §F2). Tolerates the ``OVERWRITE`` clause AND
# an ``option<record<principal>>`` wrapper (a future nullable link must ALSO be caught).
# ⚠ ADVERSARY FINDING 2: NO trailing ``\b`` — ``record<principal>`` is followed by ``;`` in
# the DDL (non-word → non-word, no boundary), so ``...principal>\b`` matches ZERO sites (a
# zero-reach guard: permanently RED on a correct build AND unable to fire when a new link is
# added). ``[^;]*?`` spans the type expr within one statement; ``(?![\w<])`` rejects a longer
# type name (e.g. a hypothetical ``record<principals>``).
_RECORD_PRINCIPAL = re.compile(
    r"\bFIELD\s+(?:OVERWRITE\s+)?(?P<field>\w+)\s+ON\s+(?P<table>\w+)\s+TYPE\b[^;]*?record<principal>(?![\w<])",
    re.IGNORECASE,
)

_EMAIL_A = "alice@example.com"
_EMAIL_B = "bob@example.com"
_HASH_A = "a" * 128  # a plausible sha512 hex digest (128 hex chars)
_HASH_B = "b" * 128


def _statements(ddl: str) -> list[str]:
    """The DDL's individual statements, as the transaction will see them."""
    return [line.strip() for line in ddl.split(";") if line.strip()]


def _key_statements() -> list[str]:
    """The ``principal_key`` slice's statements (RED while the emitter is a stub)."""
    return _statements(surreal_schema.generate_principal_key_ddl())


def _field_statement(statements: list[str], field: str) -> str:
    """The single ``DEFINE FIELD`` for ``principal_key.<field>`` (fails if absent/dup).

    Tolerates the ``OVERWRITE`` clause: production emits ``DEFINE FIELD OVERWRITE
    <name> ON <table>`` (``_define_field``, the #107 clause).
    """
    matches = [
        statement
        for statement in statements
        if _DEFINE_FIELD.match(statement)
        and re.search(rf"\bFIELD\s+(?:OVERWRITE\s+)?{re.escape(field)}\b", statement)
    ]
    assert len(matches) == 1, (
        f"expected exactly one DEFINE FIELD for principal_key.{field}, got {matches!r}"
    )
    return matches[0]


async def _apply_key_ddl(connection: SurrealConnection) -> None:
    """Apply the ``principal_key`` slice, refusing an EMPTY slice with a CLEAN message.

    On the stub ``generate_principal_key_ddl()`` returns ``""``; running "" through the
    SDK surfaces as an opaque ``IndexError`` deep in ``async_ws.py``. This guard turns
    that into a legible RED ("the slice is unbuilt") so a reader of the RED run is never
    misled into thinking the TEST is broken rather than the FEATURE unbuilt. On a real
    build the guard passes and the DDL applies."""
    key_ddl = surreal_schema.generate_principal_key_ddl()
    assert key_ddl.strip(), (
        "generate_principal_key_ddl() is EMPTY — the principal_key slice is unbuilt "
        "(RED until packet 49 lands the emitter, per design §F7)"
    )
    await run(connection, key_ddl)


async def _apply_principal_and_key_ddl(connection: SurrealConnection) -> None:
    """Apply BOTH slices (principal first — the record link's target), so a key row
    can be created against a real owner."""
    await run(connection, surreal_schema.generate_principal_ddl())
    await _apply_key_ddl(connection)


async def _create_principal(connection: SurrealConnection, *, pid: str, email: str) -> None:
    """A ``principal`` row with an explicit id (so a key can bind it as a link)."""
    await run(
        connection,
        f"CREATE type::record('{surreal_schema.PRINCIPAL_TABLE}', $id) CONTENT {{ email: $email }}",
        {"id": pid, "email": email},
    )


async def _create_key(
    connection: SurrealConnection,
    *,
    key_id: str,
    principal_id: str,
    name: str = "laptop",
    key_hash: str = _HASH_A,
    include_hash: bool = True,
    include_name: bool = True,
    include_principal: bool = True,
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> Any:
    """CREATE a ``principal_key`` row via a bound CONTENT object (store law §2).

    The owner link is written as ``type::record('principal', $pid)`` — the probed
    2026-08-20 shape (a ``record<>`` value in a CONTENT position). A column is
    written ONLY when its ``include_*`` flag is set, so an omitted required column
    exercises SCHEMAFULL rejection and an omitted ``option<>`` column decodes to NONE.
    """
    fragments: list[str] = []
    params: dict[str, Any] = {"id": key_id}
    if include_principal:
        fragments.append(f"principal: type::record('{surreal_schema.PRINCIPAL_TABLE}', $pid)")
        params["pid"] = principal_id
    if include_hash:
        fragments.append("hash: $hash")
        params["hash"] = key_hash
    if include_name:
        fragments.append("name: $name")
        params["name"] = name
    if expires_at is not None:
        fragments.append("expires_at: $expires_at")
        params["expires_at"] = expires_at
    if revoked_at is not None:
        fragments.append("revoked_at: $revoked_at")
        params["revoked_at"] = revoked_at
    return await run(
        connection,
        f"CREATE type::record('{surreal_schema.PRINCIPAL_KEY_TABLE}', $id) "
        f"CONTENT {{ {', '.join(fragments)} }}",
        params,
    )


def _one(rows: Any) -> Any:
    assert rows, f"expected one row, got {rows!r}"
    return rows[0]


# --------------------------------------------------------------------------- #
# LEG 1 — OFFLINE DDL pins (no server; string-level over the generator output).
# The "emits X" existence pins carry the RED on the empty stub; the "every X is Y"
# clause pins are GUARDED by them (a clause pin over [] passes vacuously, which is
# why each is paired with an existence pin — the test_principals_schema idiom).
# --------------------------------------------------------------------------- #


class TestThePrincipalKeyDdlDecisionRuleIsEnforcedMechanically:
    """Store reference §1.1. Each pin names the failure it prevents — a clause is
    invisible in review and catastrophic in production (#107)."""

    def test_the_slice_emits_the_table_and_fields(self) -> None:
        """CONTROL against a vacuous green (adversary F1c): the clause pins below
        iterate the slice's statements; an EMPTY slice passes them all trivially.
        This DEMANDS a ``DEFINE TABLE principal_key`` AND at least one ``DEFINE
        FIELD`` on it — RED against the ``""`` stub."""
        statements = _key_statements()
        table = surreal_schema.PRINCIPAL_KEY_TABLE
        tables = [
            s for s in statements
            if _DEFINE_TABLE.match(s) and re.search(rf"\b{re.escape(table)}\b", s)
        ]
        fields = [
            s for s in statements
            if _DEFINE_FIELD.match(s) and f" ON {table} " in f"{s} "
        ]
        assert tables, f"the slice emits no DEFINE TABLE for {table!r}: {statements!r}"
        assert fields, f"the slice for {table!r} emits no DEFINE FIELD at all"

    def test_the_table_definition_is_IF_NOT_EXISTS(self) -> None:
        offenders = [
            s for s in _key_statements()
            if _DEFINE_TABLE.match(s) and "IF NOT EXISTS" not in s.upper()
        ]
        assert not offenders, f"plain TABLE must be `IF NOT EXISTS` (§1.1): {offenders}"

    def test_every_field_definition_is_OVERWRITE(self) -> None:
        """#107 verbatim: ``IF NOT EXISTS`` on an existing field silently keeps the OLD
        definition, so a changed ASSERT never reaches a live store. Only ``OVERWRITE``
        migrates. (Guarded by the emits-fields existence pin above.)"""
        offenders = [
            s for s in _key_statements()
            if _DEFINE_FIELD.match(s) and "OVERWRITE" not in s.upper()
        ]
        assert not offenders, f"every FIELD must be `DEFINE FIELD OVERWRITE` (#107): {offenders}"

    def test_no_field_definition_uses_IF_NOT_EXISTS(self) -> None:
        offenders = [
            s for s in _key_statements()
            if _DEFINE_FIELD.match(s) and "IF NOT EXISTS" in s.upper()
        ]
        assert not offenders, offenders

    def test_both_indexes_are_IF_NOT_EXISTS_and_never_OVERWRITE(self) -> None:
        """Flipping an index to ``OVERWRITE`` converts a silent no-op into a BOOT-TIME
        CRASH: a define REBUILDS, blocking, over every existing row (§1.5)."""
        indexes = [s for s in _key_statements() if _DEFINE_INDEX.match(s)]
        assert indexes, "the principal_key slice emits no DEFINE INDEX at all"
        for statement in indexes:
            assert "IF NOT EXISTS" in statement.upper(), statement
            assert "OVERWRITE" not in statement.upper(), statement

    def test_the_word_ALTER_appears_in_no_statement(self) -> None:
        """§1.3: ``ALTER`` cannot CREATE a field, and ``ALTER … IF EXISTS`` on a missing
        one silently no-ops — re-committing #107 on the fresh-DB path this slice runs
        on every new deployment."""
        offenders = [s for s in _key_statements() if re.search(r"\bALTER\b", s, re.I)]
        assert not offenders, offenders

    def test_the_generator_returns_the_house_terminated_shape(self) -> None:
        """Every ``generate_*_ddl`` returns ``";\\n".join(...) + ";\\n"``. A slice that
        did not would break the caller's ``BEGIN … COMMIT`` wrap."""
        ddl = surreal_schema.generate_principal_key_ddl()
        assert ddl.endswith(";\n"), f"slice not house-terminated: {ddl!r}"
        assert _statements(ddl), "slice is empty"

    def test_the_slice_ROUTES_THROUGH_the_shared_ddl_emitters(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ONE IMPLEMENTATION, proven by MUTATION: nothing REQUIRES the slice to CALL
        ``_define_field`` — a hand-written ``DEFINE FIELD`` string would pass every
        clause pin while silently not sharing the #107 ``OVERWRITE`` policy. Perturb
        the shared emitter; the emitted DDL must move."""
        original = surreal_schema._define_field
        monkeypatch.setattr(
            surreal_schema,
            "_define_field",
            lambda *a, **k: f"{original(*a, **k)} COMMENT 'mutation-probe'",
        )
        assert "mutation-probe" in surreal_schema.generate_principal_key_ddl(), (
            "the principal_key slice does not route through surreal_schema._define_field"
        )


class TestThePrincipalKeyFieldTypesAndClauses:
    """The exact field typing (design §F7) — each clause bought a production incident."""

    def test_principal_is_a_required_record_link(self) -> None:
        """The owner is ``record<principal>`` and REQUIRED (NOT ``option<>``): §1.4's
        "new field on a POPULATED table must be option<>" does NOT apply — ``principal_key``
        is a brand-new empty table, so every key has an owner at mint. A build that made
        it ``option<record<principal>>`` would admit an OWNERLESS key (a credential
        belonging to nobody — the #206 identity hole from the other side)."""
        statement = _field_statement(_key_statements(), "principal")
        assert "record<principal>" in statement, statement
        assert "option<" not in statement.lower(), (
            f"principal_key.principal must be a REQUIRED record<principal> link, "
            f"never option<> (design §F2a): {statement}"
        )

    def test_hash_and_name_are_required_non_empty_strings(self) -> None:
        """``hash`` and ``name`` are REQUIRED (plain ``string``, never ``option<>``) and
        carry the trim-aware non-empty ASSERT — a present-but-empty credential/label
        names nothing and is rejected as loudly as a missing one (live pin below)."""
        statements = _key_statements()
        for field in ("hash", "name"):
            statement = _field_statement(statements, field)
            assert "option<" not in statement.lower(), (
                f"principal_key.{field} must be a REQUIRED string, never option<>: {statement}"
            )
            assert "ASSERT" in statement.upper(), (
                f"principal_key.{field} must carry the non-empty ASSERT: {statement}"
            )

    def test_created_at_self_stamps_via_default(self) -> None:
        """``created_at`` is engine-stamped via ``DEFAULT time::now()`` (the store OMITS
        it on write). A build without the DEFAULT would force every mint to supply a
        timestamp the store deliberately does not."""
        statement = _field_statement(_key_statements(), "created_at")
        assert "DEFAULT" in statement.upper() and "TIME::NOW()" in statement.upper(), statement

    def test_expires_at_and_revoked_at_are_option_datetime_with_NO_default(self) -> None:
        """⚠ The ``seen_at``/``acked_at`` "IS NONE is live" idiom (design §F7): both are
        ``option<datetime>`` with NO ``DEFAULT`` — ``WHERE revoked_at IS NONE`` is the
        "active" predicate, and a ``DEFAULT`` would make every key look already-stamped
        (revoked / expired) the instant it is minted."""
        statements = _key_statements()
        for field in ("expires_at", "revoked_at"):
            statement = _field_statement(statements, field)
            assert "option<datetime>" in statement.lower(), (
                f"principal_key.{field} must be option<datetime> (NONE = unset): {statement}"
            )
            assert "DEFAULT" not in statement.upper(), (
                f"principal_key.{field} must carry NO DEFAULT — a default would make every "
                f"key look already-stamped, breaking the IS NONE = active predicate: {statement}"
            )


class TestThePrincipalKeyIndexes:
    """Design §F7: UNIQUE(hash) (the lookup + dedup backstop) and UNIQUE(principal,name)
    (per-principal label uniqueness)."""

    def test_unique_hash_index_present(self) -> None:
        """The credential lookup rides ``WHERE hash = $h`` over a UNIQUE hash index —
        O(1), uniform-timing over a preimage-resistant digest (no name-existence
        oracle). A build that dropped or plain-ified it loses the dedup backstop."""
        indexes = [s for s in _key_statements() if _DEFINE_INDEX.match(s)]
        hash_unique = [
            s for s in indexes
            if "UNIQUE" in s.upper() and re.search(r"FIELDS\s+hash\b", s, re.I)
        ]
        assert hash_unique, f"expected a UNIQUE index on principal_key.hash, indexes={indexes!r}"

    def test_unique_principal_name_is_composite_and_per_principal(self) -> None:
        """⚠ PER-PRINCIPAL (design §F7): the UNIQUE index is over ``(principal, name)``,
        NOT ``name`` alone. Global name uniqueness would force every human to invent
        globally-unique labels (poor UX + an information leak about others' key names).
        A build that indexed ``name`` alone would REJECT a second human naming a key
        ``laptop`` — the live per-principal pin below catches it, this pins the shape."""
        indexes = [s for s in _key_statements() if _DEFINE_INDEX.match(s)]
        composite = [
            s for s in indexes
            if "UNIQUE" in s.upper()
            and re.search(r"FIELDS\s+principal\s*,\s*name\b", s, re.I)
        ]
        assert composite, (
            f"expected a UNIQUE composite index on principal_key (principal, name) — "
            f"NOT on name alone (per-principal label reuse); indexes={indexes!r}"
        )


class TestThePrincipalKeyDdlIsFoldedIntoGenerateDdl:
    """#131 dirty-store class: the fold is what makes the table exist in production."""

    def test_principal_key_is_FOLDED_into_the_global_generate_ddl(self) -> None:
        """Design §F7 / pin 12: ``principal_key`` is folded into ``generate_ddl`` so the
        PRIMARY ``write_store.ensure_ready()`` creates the table on ship. A build that
        folds it into the standalone SLICE but forgets ``generate_ddl`` leaves the
        primary store WITHOUT the table — every virgin-DB fixture passes, a real deploy
        fails (the exact #131 shape)."""
        full = surreal_schema.generate_ddl(dim=NONDEFAULT_DIM)
        table = surreal_schema.PRINCIPAL_KEY_TABLE
        assert f"DEFINE TABLE IF NOT EXISTS {table} SCHEMAFULL" in full, (
            "principal_key is NOT folded into generate_ddl — the table will not exist in "
            "production (the #131 dirty-store class; design §F7)"
        )
        assert any(
            _DEFINE_FIELD.match(s) and f" ON {table} " in f"{s} "
            for s in _statements(full)
        ), "generate_ddl carries the principal_key table but none of its fields"

    def test_principal_is_defined_before_principal_key_in_generate_ddl(self) -> None:
        """Design §F7: fold ``_principal_key_statements()`` immediately AFTER
        ``_principal_statements()`` (the ``briefed`` → ``agent`` precedent — the record
        link's target table is defined first). A build folding it BEFORE ``principal``
        contradicts the design's ordering."""
        full = surreal_schema.generate_ddl(dim=NONDEFAULT_DIM)
        principal_table = f"DEFINE TABLE IF NOT EXISTS {surreal_schema.PRINCIPAL_TABLE} SCHEMAFULL"
        key_table = f"DEFINE TABLE IF NOT EXISTS {surreal_schema.PRINCIPAL_KEY_TABLE} SCHEMAFULL"
        assert principal_table in full and key_table in full, "both tables must be folded in"
        assert full.index(principal_table) < full.index(key_table), (
            "principal must be defined BEFORE principal_key (design §F7 fold-after-principal)"
        )


class TestTheCascadeForwardScopeIsPinned:
    """⚠ PIN THE MISS (design §F2, pin 14) — a KNOWN BOUND, not a prohibition.

    ⚠ REVISED 2026-08-23 (packet 61a-w1, finding #402, design
    ``2026-08-22-packet61-pdp-audit-rulings.md`` §FR-4). Packet-60 Fork A added a SECOND
    ``record<principal>`` link — ``keep.keeper`` — which reddened the original single-link
    exact-set pin EXACTLY as designed (PIN THE MISS working). Under §FR-4 the delete of a
    principal who KEEPS a keep is now REFUSED-WHILE-KEEPING (a ``keep.keeper`` dangle
    becomes unreachable — you cannot delete a keeper while they keep), so ``keep.keeper``
    is a DELIBERATE, adjudicated, cascade-handled addition and is added to the expected
    set. The behavioural cascade-correctness guard lives in
    ``test_principal_delete_cascade_61.py``; this class stays the STATIC tripwire.
    """

    def test_the_record_principal_link_set_matches_the_cascade_adjudication(self) -> None:
        """The set of ``record<principal>`` links is EXACTLY the three whose deletion
        disposition ``PrincipalStore.delete`` accounts for, as of §FR-4 (2026-08-23) + the
        packet-61a-w4 ``audit`` substrate (2026-08-23). Each link is CLASSIFIED, not
        flat-absorbed (the sidecar prefers a classified disposition per link):

        * ``principal_key.principal`` — **CASCADE-DELETE-OWNED-DATA**: a principal's keys are its
          own owned children, deleted children-first with it (no orphan key).
        * ``keep.keeper`` — **REFUSE-LIVE-DEPENDENCY**: a keeper cannot be deleted while they keep
          (refuse-while-keeping), so no ``keep.keeper`` dangle can occur.
        * ``audit.actor_principal`` — **DANGLE-TOLERATED** (packet 61a-w4, operator/sidecar RULED,
          §9 forensics): the audit trail is IMMUTABLE HISTORY. Cascade-deleting audit rows on a
          principal-delete would let an admin ERASE THEIR OWN TRAIL by deleting themselves — the
          §9 hole; refusing the principal-delete would make every actor un-deletable forever. So
          the link is deliberately allowed to DANGLE, and the human identity is preserved by the
          DENORMALIZED ``audit.actor_email``/``actor_agent_name`` VALUE columns (they survive the
          delete — proven by ``test_audit_store.py::TestTheDenormalizedIdentitySurvivesActorDelete``).

        Ledger actors are free strings and ``agent`` is unrelated (§1A). This scans the FULL
        ``generate_ddl`` for every ``record<principal>`` field and asserts the set is exactly
        these three.

        ⚠ FORMERLY ``test_principal_key_is_the_ONLY_record_principal_link`` — the name
        cited by finding #402 / §FR-4 as the RED_ORPHANED gate. Renamed here because it is
        no longer "the ONLY" link (that would be a false natural-language surface, the P8d
        drift class); grep the old name to land here.

        ⚠ RE-OPEN TRIGGER (STAYS ARMED): the day ANY new ``record<principal>`` link is added
        (63/64's ``owner_principal`` next — a LIVE-DEPENDENCY-class link, so cascade-or-refuse,
        NOT dangle: unlike immutable audit history a governed row's owner must not silently point
        at a ghost), this pin goes RED again — a deliberate signal that ``PrincipalStore.delete``'s
        cascade/refusal MUST be revisited to avoid dangling links (record links do NOT auto-clean,
        store law §4). If you added the link deliberately, CLASSIFY its disposition, revisit the
        delete AND update this pin's expected set, then say so."""
        full = surreal_schema.generate_ddl(dim=NONDEFAULT_DIM)
        found = {(m.group("field"), m.group("table")) for m in _RECORD_PRINCIPAL.finditer(full)}
        expected = {
            ("principal", surreal_schema.PRINCIPAL_KEY_TABLE),  # CASCADE-DELETE-OWNED-DATA
            ("keeper", surreal_schema.KEEP_TABLE),  # REFUSE-LIVE-DEPENDENCY
            ("actor_principal", surreal_schema.AUDIT_TABLE),  # DANGLE-TOLERATED (§9 immutable history)
        }
        assert found == expected, (
            f"the set of record<principal> links changed — cascade forward-scope PIN THE "
            f"MISS (design §F2 / §FR-4). expected exactly {expected}, found {found}. If you "
            f"added a new link (e.g. 63/64 owner_principal), CLASSIFY its disposition, revisit "
            f"PrincipalStore.delete's cascade/refusal AND update this pin."
        )

    def test_the_forward_scope_regex_has_nonzero_reach(self) -> None:
        """⚠ POSITIVE CONTROL (adversary FINDING 2): prove the forward-scope regex CAN fire
        for its purpose. A zero-reach regex (the original ``record<principal>\\b`` bug) would
        pass the exact-set pin above only by finding NOTHING — and could NEVER redden when a
        real new link is added. Run the regex against a SYNTHETIC DDL carrying the two REAL
        links (``principal_key.principal`` required, ``keep.keeper`` required) PLUS a
        hypothetical ``memory.owner: option<record<principal>>`` and assert it finds ALL
        THREE (required AND option-wrapped). Always GREEN — it guards the INSTRUMENT, not a
        build."""
        synthetic = (
            "DEFINE FIELD OVERWRITE principal ON principal_key TYPE record<principal>;\n"
            "DEFINE FIELD OVERWRITE keeper ON keep TYPE record<principal>;\n"
            "DEFINE FIELD OVERWRITE owner ON memory TYPE option<record<principal>>;\n"
            "DEFINE FIELD OVERWRITE tier ON snapshot_entry TYPE string;\n"
        )
        found = {(m.group("field"), m.group("table")) for m in _RECORD_PRINCIPAL.finditer(synthetic)}
        assert found == {
            ("principal", "principal_key"),
            ("keeper", "keep"),
            ("owner", "memory"),
        }, (
            f"the forward-scope regex has broken/zero reach — it must match EVERY "
            f"record<principal> link (required OR option-wrapped) so the PIN THE MISS can "
            f"fire the day 63/64 adds one; found {found}"
        )


# --------------------------------------------------------------------------- #
# LEG 2 — LIVE round-trip on ws://127.0.0.1:18000 (NEVER :18500). NO skip marker.
# --------------------------------------------------------------------------- #


class TestThePrincipalKeySchemaAppliesToTheLiveEngine:
    """The generated DDL against the real engine — the recipe proven on the cake."""

    async def test_the_slice_creates_the_table(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, _ = admin_db
        await _apply_principal_and_key_ddl(connection)
        tables = set((await run(connection, "INFO FOR DB")).get("tables", {}))
        assert surreal_schema.PRINCIPAL_KEY_TABLE in tables

    async def test_the_slice_is_safely_re_appliable(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """``ensure_ready`` re-applies the DDL on EVERY boot — a statement that raises on
        re-application is a boot-time crash."""
        connection, _ = admin_db
        await run(connection, surreal_schema.generate_principal_ddl())
        for _ in range(2):
            await _apply_key_ddl(connection)


class TestThePrincipalKeyRoundTrip:
    """The ``principal_key`` table (live behavioural) — the design §F7 property set."""

    async def test_a_key_round_trips_and_derefs_its_owner(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """A minted key reads back with its owner link, and the link DEREFERENCES to the
        principal's fields (the design's preferred verify shape — probed 2026-08-20)."""
        connection, _ = admin_db
        table = surreal_schema.PRINCIPAL_KEY_TABLE
        await _apply_principal_and_key_ddl(connection)
        await _create_principal(connection, pid="p1", email=_EMAIL_A)
        await _create_key(connection, key_id="k1", principal_id="p1", name="laptop", key_hash=_HASH_A)
        row = _one(
            await run(
                connection,
                f"SELECT hash, name, principal.email AS owner_email, created_at "
                f"FROM {table} WHERE hash = $h",
                {"h": _HASH_A},
            )
        )
        assert row["name"] == "laptop"
        assert row["owner_email"] == _EMAIL_A
        assert row["created_at"] is not None  # self-stamped

    async def test_option_datetime_columns_read_back_as_none_under_explicit_projection(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Store-law §2: a key minted with no ``expires_at``/``revoked_at`` reads those
        back as ``None`` under an EXPLICIT projection — this is why the store's readers
        list their columns, never ``SELECT *`` (which OMITS a NONE ``option<>`` column —
        the control below)."""
        connection, _ = admin_db
        table = surreal_schema.PRINCIPAL_KEY_TABLE
        await _apply_principal_and_key_ddl(connection)
        await _create_principal(connection, pid="p1", email=_EMAIL_A)
        await _create_key(connection, key_id="k1", principal_id="p1")
        row = _one(
            await run(
                connection,
                f"SELECT hash, name, expires_at, revoked_at FROM {table} WHERE hash = $h",
                {"h": _HASH_A},
            )
        )
        assert row["expires_at"] is None
        assert row["revoked_at"] is None

    async def test_select_star_OMITS_the_none_option_column_the_control(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ THE §2 DISCRIMINATING CONTROL: under ``SELECT *`` a NONE ``option<>`` column
        is OMITTED entirely (``row["revoked_at"]`` would ``KeyError``). A build whose
        reader used ``SELECT *`` would blow up reading every un-revoked key."""
        connection, _ = admin_db
        table = surreal_schema.PRINCIPAL_KEY_TABLE
        await _apply_principal_and_key_ddl(connection)
        await _create_principal(connection, pid="p1", email=_EMAIL_A)
        await _create_key(connection, key_id="k1", principal_id="p1")
        row = _one(await run(connection, f"SELECT * FROM type::record('{table}', 'k1')"))
        assert "hash" in row  # a present column IS there
        assert "revoked_at" not in row, (
            "SELECT * unexpectedly returned the NONE revoked_at key — store-law §2 says an "
            "option<> NONE column is omitted; if the engine changed, re-derive the reader"
        )

    async def test_duplicate_hash_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """UNIQUE(hash): a duplicate credential digest is rejected (the dedup backstop)."""
        connection, _ = admin_db
        await _apply_principal_and_key_ddl(connection)
        await _create_principal(connection, pid="p1", email=_EMAIL_A)
        await _create_key(connection, key_id="k1", principal_id="p1", name="a", key_hash=_HASH_A)
        with pytest.raises(Exception):  # noqa: B017 - engine UNIQUE index rejection
            await _create_key(connection, key_id="k2", principal_id="p1", name="b", key_hash=_HASH_A)

    async def test_same_principal_and_name_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """UNIQUE(principal, name): one principal may not hold two keys named ``laptop``
        (so ``revoke-key --email e --name laptop`` is deterministic). Different HASHES,
        SAME (principal, name) → rejected."""
        connection, _ = admin_db
        await _apply_principal_and_key_ddl(connection)
        await _create_principal(connection, pid="p1", email=_EMAIL_A)
        await _create_key(connection, key_id="k1", principal_id="p1", name="laptop", key_hash=_HASH_A)
        with pytest.raises(Exception):  # noqa: B017 - engine UNIQUE composite rejection
            await _create_key(connection, key_id="k2", principal_id="p1", name="laptop", key_hash=_HASH_B)

    async def test_two_principals_may_share_a_key_name(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ THE PER-PRINCIPAL LOAD-BEARING PIN (design §F7): two DIFFERENT humans may
        each name a key ``laptop``. A build that indexed ``name`` alone (global
        uniqueness) would REJECT the second — a monoculture single-principal fixture
        cannot see it, so this uses TWO principals with the SAME key name."""
        connection, _ = admin_db
        await _apply_principal_and_key_ddl(connection)
        await _create_principal(connection, pid="p1", email=_EMAIL_A)
        await _create_principal(connection, pid="p2", email=_EMAIL_B)
        await _create_key(connection, key_id="k1", principal_id="p1", name="laptop", key_hash=_HASH_A)
        # SAME name, DIFFERENT principal — must succeed under UNIQUE(principal, name).
        await _create_key(connection, key_id="k2", principal_id="p2", name="laptop", key_hash=_HASH_B)

    @pytest.mark.parametrize("empty", ["", " ", "\t"])
    async def test_empty_or_whitespace_hash_and_name_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv], empty: str  # noqa: F811
    ) -> None:
        """The trim-aware non-empty ASSERT: a present-but-empty ``hash`` or ``name`` is
        rejected as loudly as a missing one."""
        connection, _ = admin_db
        await _apply_principal_and_key_ddl(connection)
        await _create_principal(connection, pid="p1", email=_EMAIL_A)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation (empty hash)
            await _create_key(connection, key_id="bh", principal_id="p1", name="ok", key_hash=empty)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation (empty name)
            await _create_key(connection, key_id="bn", principal_id="p1", name=empty, key_hash=_HASH_B)

    async def test_missing_required_columns_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """SCHEMAFULL discipline: a key omitting a REQUIRED column (hash / name /
        principal) is rejected — no ownerless or credential-less key can exist."""
        connection, _ = admin_db
        await _apply_principal_and_key_ddl(connection)
        await _create_principal(connection, pid="p1", email=_EMAIL_A)
        with pytest.raises(Exception):  # noqa: B017 - missing hash
            await _create_key(connection, key_id="nh", principal_id="p1", include_hash=False)
        with pytest.raises(Exception):  # noqa: B017 - missing name
            await _create_key(connection, key_id="nn", principal_id="p1", include_name=False)
        with pytest.raises(Exception):  # noqa: B017 - missing principal (ownerless)
            await _create_key(connection, key_id="np", principal_id="p1", include_principal=False)

    async def test_undeclared_field_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """SCHEMAFULL discipline (store §1.7): an undeclared top-level key RAISES, so a
        typo'd column can never silently become a phantom attribute (e.g. a raw
        ``secret`` column would be caught here)."""
        connection, _ = admin_db
        table = surreal_schema.PRINCIPAL_KEY_TABLE
        await _apply_principal_and_key_ddl(connection)
        await _create_principal(connection, pid="p1", email=_EMAIL_A)
        with pytest.raises(Exception):  # noqa: B017 - engine SCHEMAFULL rejection
            await run(
                connection,
                f"CREATE type::record('{table}', 'rogue') CONTENT "
                f"{{ principal: type::record('principal','p1'), hash: $h, name: 'x', "
                f"secret: 'RAW-SECRET-MUST-NOT-EXIST' }}",
                {"h": _HASH_A},
            )


class TestSchemaMigrationAgainstAnExistingStore:
    """⚠ Store §1.6 — the dirty-store blind spot (every test mints a VIRGIN DB, so no
    fixture can see a migration defect). ``principal_key`` is a brand-new table with no
    field CHANGE to migrate, so the §1.6 shape here proves the slice is RE-APPLIABLE to
    a POPULATED store (``ensure_ready`` re-runs every boot): apply the slice → dirty it
    with a real key row → apply the slice AGAIN → the row SURVIVES and the UNIQUE
    constraint still fires. A build whose indexes were ``OVERWRITE`` (boot-crash) or
    whose re-apply wiped rows would redden here where every virgin-DB pin stays green.
    """

    async def test_the_slice_reapplies_to_a_dirty_store_without_loss_or_crash(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, _ = admin_db
        table = surreal_schema.PRINCIPAL_KEY_TABLE
        # OLD world: the slice, plus a real key row (the field must ALREADY EXIST).
        await _apply_principal_and_key_ddl(connection)
        await _create_principal(connection, pid="p1", email=_EMAIL_A)
        await _create_key(connection, key_id="k1", principal_id="p1", name="laptop", key_hash=_HASH_A)

        # NEW world: re-apply the slice against the now-DIRTY store (the boot re-run).
        await _apply_key_ddl(connection)

        # The pre-existing key SURVIVED …
        survived = _one(
            await run(connection, f"SELECT hash, name FROM {table} WHERE hash = $h", {"h": _HASH_A})
        )
        assert survived["name"] == "laptop"
        # … and the UNIQUE(hash) constraint STILL fires (the re-apply did not drop it).
        with pytest.raises(Exception):  # noqa: B017 - UNIQUE(hash) still enforced post-reapply
            await _create_key(connection, key_id="k2", principal_id="p1", name="other", key_hash=_HASH_A)
