"""Contract — packet 62 Wave 1: the ``owns`` edge = ``agent.owner_principal`` field-link.

Author: ``contract-62w1`` (Opus 4.8 CONTRACT author — tests ONLY, no production code).
The builder builds FROM this; a separate Opus contract-adversary grades it first.

SPEC (the work order, executed verbatim — never re-transcribed):
``docs/design/2026-08-24-packet62-agent-identity-rulings.md`` — FORK 3 (the ``owns`` edge
is a SCALAR field-link ``agent.owner_principal : record<principal>`` on the comms ``agent``
table, NOT a relation edge — packet-60 Fork-A ``keep.keeper`` precedent), riders
R3.1/R3.2/R3.4, the FINAL PACKET-62 SCOPE LINE items 1 & 4, and removed-behavior item I4.
Operator-RULED 2026-08-24: Fork 3 RATIFIED; principal-delete is DANGLE-TOLERATED for owned
agents (R3.2). This wave is SCOPE items 1 & 4 (the store foundation) ONLY — the register-time
owner STAMP (item 2, R3.3), the ``stamp_owner`` seam (item 3), and the anti-injection reach
pin (item 5) are LATER waves and are NOT contracted here.

STORE LAW (``docs/reference/surrealdb-31-capabilities.md`` — cited, never re-transcribed):
§1.1 (FIELD ``OVERWRITE``; INDEX ``IF NOT EXISTS`` never ``OVERWRITE`` — a flip is a
boot-time crash), §1.4 (a NEW field on a POPULATED table MUST be ``option<>`` — a required
field poisons every existing row's next UPDATE and a DEFAULT does not rescue it), §1.6 (the
dirty-store blind spot — every test mints a VIRGIN db, so no ordinary fixture can see a
migration defect), §2 (``record<t>`` links do NOT auto-clean on target delete — the tolerated
dangle; ⚠ ``SELECT *`` OMITS a NONE ``option<>`` column, explicit projection reads ``None``),
§4 (a graph TRAVERSAL is never index-served → keep a scalar owner as an INDEXED FIELD).

WHY ``option<record<principal>>`` (R3.4): ``agent`` is a PRODUCTION-POPULATED table, so
``owner_principal`` is a NEW field on a POPULATED table → §1.4 forces ``option<>``. An
ownerless agent is ALSO legal by design (Fork 2: the pre-cutover local fleet has no
credential to stamp from; item 2 fills the owner in later), so ``option<>`` is both the
migration-safe AND the semantically-correct shape.

WHY it DANGLES on principal-delete (R3.2 / I4): a principal delete is ALLOWED while it owns
agents; the owned-agent rows SURVIVE with a now-stale ``owner_principal`` back-link. Agents
are retired-not-deleted (never hard-deleted), so a surviving stale link is not a correctness
break — and cascade-deleting agent rows would erase fleet history. This mirrors
``audit.actor_principal``'s DANGLE (packet 61a-w4). The exact-set cascade-adjudication pin is
UPDATED in ``test_principal_keys_schema.py`` (this wave's other writable) to account for the
new link.

⚠ WHY the agent rows here are built by a RAW ``CREATE`` that sets ``owner_principal`` directly
(NOT ``AgentRegistry.register``): the register-time server-side owner STAMP is SCOPE item 2 (a
LATER wave), so ``register`` does not populate ``owner_principal`` yet. This wave pins the
SCHEMA (the field + index + migration) and the DELETE dangle semantics IN ISOLATION from the
stamp — a raw CREATE mimics exactly what the future stamp will write.

RED vs POSITIVE CONTROL (fixtures-must-discriminate). The RED-until-built pins assert the
field/index EXIST and a store row can carry an owner. The option-vs-required and
IF-NOT-EXISTS-vs-OVERWRITE pins are POSITIVE CONTROLS / DISCRIMINATORS: GREEN at HEAD (the
field is simply absent) and GREEN on the correct build, but RED on a specific WRONG build (a
required field, or an OVERWRITE index). Each pin says which it is and which wrong build it
reddens.

Live store: ws://127.0.0.1:18000 (NEVER :18500). Per-test unique database, reaped on exit.
NO skip marker — an unreachable store is a LOUD failure, not a skip.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealConnection,
    SurrealEnv,
    admin_db,  # noqa: F401 - re-exported pytest fixture
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.keeps import KeepStore
from loremaster.principal_keys import PrincipalKeyStore
from loremaster.principals import PrincipalStore
from loremaster.store import surreal_schema
from loremaster.store.surreal_schema import (
    _AGENT_STATUS_ACTIVE,
    AGENT_TABLE,
    PRINCIPAL_TABLE,
)
from surrealdb import RecordID

_OWNER_FIELD = "owner_principal"
_EMAIL_ALICE = "alice@example.com"

_DEFINE_FIELD = re.compile(r"^\s*DEFINE\s+FIELD\b", re.IGNORECASE)
_DEFINE_INDEX = re.compile(r"^\s*DEFINE\s+INDEX\b", re.IGNORECASE)


def _statements(ddl: str) -> list[str]:
    """The DDL's individual statements, as the transaction will see them."""
    return [line.strip() for line in ddl.split(";") if line.strip()]


def _agent_statements() -> list[str]:
    """The ``agent`` slice's statements (``generate_agent_ddl`` — the comms store's own
    ``ensure_ready`` slice; ``agent`` is NOT folded into ``generate_ddl``)."""
    return _statements(surreal_schema.generate_agent_ddl())


def _owner_field_statement() -> str | None:
    """The single ``DEFINE FIELD`` for ``agent.owner_principal`` (None if unbuilt).

    Tolerates the ``OVERWRITE`` clause (production emits ``DEFINE FIELD OVERWRITE …``).
    Asserts at-most-one so a duplicate emitter is a loud failure, not a silent last-wins.
    """
    matches = [
        statement
        for statement in _agent_statements()
        if _DEFINE_FIELD.match(statement)
        and re.search(rf"\bFIELD\s+(?:OVERWRITE\s+)?{_OWNER_FIELD}\b", statement)
    ]
    assert len(matches) <= 1, (
        f"expected at most one DEFINE FIELD for agent.{_OWNER_FIELD}, got {matches!r}"
    )
    return matches[0] if matches else None


def _owner_index_statement() -> str | None:
    """The single ``DEFINE INDEX`` over ``agent.owner_principal`` (None if unbuilt)."""
    matches = [
        statement
        for statement in _agent_statements()
        if _DEFINE_INDEX.match(statement)
        and re.search(rf"FIELDS\s+{_OWNER_FIELD}\b", statement, re.IGNORECASE)
    ]
    assert len(matches) <= 1, (
        f"expected at most one DEFINE INDEX over agent.{_OWNER_FIELD}, got {matches!r}"
    )
    return matches[0] if matches else None


def _agent_ddl_without_owner_principal() -> str:
    """The agent slice as it stood BEFORE this packet — every statement that does NOT
    mention ``owner_principal``.

    At HEAD this EQUALS ``generate_agent_ddl()`` (no ``owner_principal`` present); on a
    correct build it is the real slice minus the ``owner_principal`` field def AND its index,
    so applying the real slice OVER it IS the field-add migration (§1.6 dirty-store idiom
    without needing a hand-mirrored synthetic table — the OLD/NEW pair share the real emitter).
    """
    kept = [statement for statement in _agent_statements() if _OWNER_FIELD not in statement]
    return ";\n".join(kept) + ";\n"


def _one(rows: Any) -> Any:
    assert rows, f"expected one row, got {rows!r}"
    return rows[0]


async def _apply_agent_ddl(connection: SurrealConnection) -> None:
    await run(connection, surreal_schema.generate_agent_ddl())


async def _create_agent(
    connection: SurrealConnection,
    *,
    agent_id: str,
    name: str,
    session: str,
    owner_bare_id: str | None = None,
    role: str = "worker",
) -> Any:
    """CREATE a full ``agent`` row via a bound CONTENT object — the house
    ``test_comms_schema._create_agent`` idiom (store law §2: ``session`` is a PROTECTED
    variable name, so the whole payload rides ONE ``$content`` bind with ``session`` as an
    inner KEY — a top-level ``$session`` param is rejected outright).

    Supplies every REQUIRED (non-``option``, no-DEFAULT) column: ``name``/``session`` (the
    identifier-charset ASSERT), ``role`` (non-empty ASSERT), ``status`` (the closed domain),
    and the two app-stamped datetimes. ``owner_principal`` is written as a bound
    :class:`~surrealdb.RecordID` (the ``record<>``-value shape) ONLY when ``owner_bare_id`` is
    given — so an ownerless CREATE exercises the ``option<>`` unset path.
    """
    now = datetime.now(UTC)
    content: dict[str, Any] = {
        "name": name,
        "session": session,
        "role": role,
        "status": _AGENT_STATUS_ACTIVE,
        "registered_at": now,
        "heartbeat_at": now,
    }
    if owner_bare_id is not None:
        content[_OWNER_FIELD] = RecordID(PRINCIPAL_TABLE, owner_bare_id)
    return await run(
        connection,
        f"CREATE type::record('{AGENT_TABLE}', $id) CONTENT $content",
        {"id": agent_id, "content": content},
    )


def _bare(record_id: str) -> str:
    """The id part of a ``table:id`` string (``principal:abc`` -> ``abc``); a bare id passes
    through. Mirrors ``PrincipalStore.delete``'s own ``partition(':')[2] or id``."""
    return record_id.partition(":")[2] or record_id


# --------------------------------------------------------------------------- #
# LEG 1 — OFFLINE DDL pins (no server; string-level over generate_agent_ddl).
# The "emits X" existence pins carry the RED at HEAD; the clause pins are GUARDED
# by them (a clause pin over an absent field passes vacuously) — the
# test_principal_keys_schema idiom.
# --------------------------------------------------------------------------- #


class TestTheOwnerPrincipalFieldDdl:
    """FORK 3 + R3.4 + store §1.1/§1.4 — the field's exact shape, pinned mechanically."""

    def test_the_owner_principal_field_is_emitted(self) -> None:
        """⚠ RED at HEAD — ``agent.owner_principal`` is not in ``_AGENT_FIELD_SPECS`` yet.
        The existence CONTROL for the clause pins below (a clause pin over an absent field
        passes vacuously)."""
        assert _owner_field_statement() is not None, (
            "generate_agent_ddl() emits no DEFINE FIELD for agent.owner_principal — the "
            "owns back-link is unbuilt (packet 62, Fork 3 / scope item 1)"
        )

    def test_the_owner_principal_field_is_option_wrapped_record_principal(self) -> None:
        """⚠ R3.4 / store §1.4: ``agent`` is a POPULATED table, so a NEW field MUST be
        ``option<record<principal>>`` — a required ``record<principal>`` poisons every
        existing agent row's next UPDATE (a DEFAULT does not rescue it), and an ownerless
        agent is legal by design (Fork 2). RED at HEAD; REDDENS a required-not-option build."""
        statement = _owner_field_statement()
        assert statement is not None, "unbuilt (see test_the_owner_principal_field_is_emitted)"
        collapsed = statement.replace(" ", "")
        assert "option<record<principal>>" in collapsed, (
            f"agent.{_OWNER_FIELD} must be option<record<principal>> (§1.4 — a required link on "
            f"a POPULATED table poisons every legacy agent row): {statement}"
        )

    def test_the_owner_principal_field_is_OVERWRITE(self) -> None:
        """⚠ #107 verbatim (§1.1): ``IF NOT EXISTS`` on an existing field is a SILENT no-op,
        so a changed definition never migrates a live store. Only ``OVERWRITE`` lands. RED at
        HEAD; REDDENS an ``IF NOT EXISTS`` build."""
        statement = _owner_field_statement()
        assert statement is not None, "unbuilt (see test_the_owner_principal_field_is_emitted)"
        assert "OVERWRITE" in statement.upper(), (
            f"agent.{_OWNER_FIELD} must be DEFINE FIELD OVERWRITE (#107): {statement}"
        )
        assert "IF NOT EXISTS" not in statement.upper(), statement

    def test_the_owner_principal_field_carries_no_default_and_no_assert(self) -> None:
        """⚠ store §1.4: a NEW field on a POPULATED table must be un-poisoning — an
        ``option<>`` with NO ASSERT and NO DEFAULT. A DEFAULT does NOT rescue a legacy row
        (it applies at CREATE, not to an existing row's missing value), and an ASSERT on the
        link would poison the legacy rows the option<> exists to spare. RED at HEAD; REDDENS a
        build that adds a DEFAULT or ASSERT to the link."""
        statement = _owner_field_statement()
        assert statement is not None, "unbuilt (see test_the_owner_principal_field_is_emitted)"
        assert "DEFAULT" not in statement.upper(), (
            f"agent.{_OWNER_FIELD} must carry NO DEFAULT — a DEFAULT does not rescue a legacy "
            f"row and misrepresents an ownerless agent as owned: {statement}"
        )
        assert "ASSERT" not in statement.upper(), (
            f"agent.{_OWNER_FIELD} must carry NO ASSERT — an ASSERT poisons the legacy rows "
            f"option<> exists to spare (§1.4): {statement}"
        )

    def test_the_owner_principal_field_routes_through_the_shared_emitter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ ONE IMPLEMENTATION, proven by MUTATION: nothing REQUIRES the slice to CALL
        ``_define_field`` — a hand-written ``DEFINE FIELD`` string would pass every clause pin
        above while silently not sharing the #107 ``OVERWRITE`` policy. Perturb the shared
        emitter; the ``owner_principal`` field def must move. RED at HEAD (no statement to
        move); REDDENS a hand-rolled field."""
        original = surreal_schema._define_field
        monkeypatch.setattr(
            surreal_schema,
            "_define_field",
            lambda *a, **k: f"{original(*a, **k)} COMMENT 'owns-mutation-probe'",
        )
        owner_statements = [
            statement
            for statement in _agent_statements()
            if _DEFINE_FIELD.match(statement) and re.search(rf"\b{_OWNER_FIELD}\b", statement)
        ]
        assert owner_statements, (
            f"no DEFINE FIELD for agent.{_OWNER_FIELD} to route-check — unbuilt (packet 62) or "
            f"renamed off the shared emitter"
        )
        assert all("owns-mutation-probe" in statement for statement in owner_statements), (
            f"agent.{_OWNER_FIELD} does not route through surreal_schema._define_field — a "
            f"hand-written DEFINE FIELD bypasses the #107 OVERWRITE policy"
        )


class TestTheOwnerPrincipalIndex:
    """FORK 3 (store §4: keep a scalar owner as an INDEXED field — a traversal is never
    index-served) + R3.4 (index clause rule)."""

    def test_the_owner_principal_index_is_emitted(self) -> None:
        """⚠ RED at HEAD. The owns back-link is indexed so "which agents does principal X
        own" is an index-served plain-table read (store §4: a scalar filtered through a hop is
        un-indexable, so the owner is a FIELD, and it is indexed)."""
        assert _owner_index_statement() is not None, (
            f"generate_agent_ddl() emits no DEFINE INDEX over agent.{_OWNER_FIELD} — the owns "
            f"back-link is not indexed (packet 62, Fork 3 / scope item 1)"
        )

    def test_the_owner_principal_index_is_IF_NOT_EXISTS_never_OVERWRITE(self) -> None:
        """⚠ store §1.1: ``OVERWRITE`` on an index REBUILDS it over every row on every
        ``ensure_ready`` boot → a boot-time crash. Indexes stay ``IF NOT EXISTS``. RED at HEAD;
        REDDENS an ``OVERWRITE`` index (also caught live by the re-appliability pin)."""
        statement = _owner_index_statement()
        assert statement is not None, "unbuilt (see test_the_owner_principal_index_is_emitted)"
        assert "IF NOT EXISTS" in statement.upper(), statement
        assert "OVERWRITE" not in statement.upper(), statement

    def test_the_owner_principal_index_is_NOT_unique(self) -> None:
        """⚠ A principal owns MANY agents, so ``owner_principal`` is NOT unique across agent
        rows — a UNIQUE index would REJECT a principal's 2nd owned agent. RED at HEAD; REDDENS
        a UNIQUE build (guarded by the existence pin)."""
        statement = _owner_index_statement()
        assert statement is not None, "unbuilt (see test_the_owner_principal_index_is_emitted)"
        assert "UNIQUE" not in statement.upper(), (
            f"agent.{_OWNER_FIELD} must be a NON-unique index — a principal owns many agents; "
            f"a UNIQUE index rejects the 2nd owned agent: {statement}"
        )


# --------------------------------------------------------------------------- #
# LEG 2 — LIVE round-trip on ws://127.0.0.1:18000 (NEVER :18500). NO skip marker.
# --------------------------------------------------------------------------- #


class TestTheOwnerPrincipalFieldOnTheLiveEngine:
    """The generated DDL against the real engine — the recipe proven on the cake."""

    async def test_an_owned_agent_stores_and_reads_back_its_principal_link(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ RED at HEAD — the field is undeclared, so a SCHEMAFULL CREATE that sets
        ``owner_principal`` is REJECTED. On a correct build the owner link stores and reads
        back as the principal record id."""
        connection, _ = admin_db
        await _apply_agent_ddl(connection)
        await _create_agent(
            connection, agent_id="owned", name="owned_agent", session="fleet_one", owner_bare_id="p1"
        )
        row = _one(
            await run(
                connection,
                f"SELECT {_OWNER_FIELD} FROM type::record('{AGENT_TABLE}', 'owned')",
            )
        )
        assert str(row[_OWNER_FIELD]) == f"{PRINCIPAL_TABLE}:p1", row

    async def test_an_ownerless_agent_reads_owner_principal_as_none(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ POSITIVE CONTROL / option<> DISCRIMINATOR (store §2). An agent created without an
        owner (the pre-cutover local fleet / legacy path, Fork 2) reads ``owner_principal``
        back as ``None`` under an EXPLICIT projection — proving the field is OPTIONAL. GREEN at
        HEAD (the projection of an absent column is also None) and on the option<> build; a
        required-not-option build REJECTS this ownerless CREATE and reddens here."""
        connection, _ = admin_db
        await _apply_agent_ddl(connection)
        await _create_agent(connection, agent_id="free", name="free_agent", session="fleet_two")
        row = _one(
            await run(
                connection,
                f"SELECT {_OWNER_FIELD} FROM type::record('{AGENT_TABLE}', 'free')",
            )
        )
        assert row[_OWNER_FIELD] is None, row

    async def test_a_principal_may_own_many_agents(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ THE NON-UNIQUE LOAD-BEARING PIN. One principal owns MANY agents — two agents
        sharing an ``owner_principal`` must BOTH persist. RED at HEAD (undeclared field);
        REDDENS a UNIQUE-index build (which the 2nd CREATE would reject) that the offline
        clause pin only pins statically."""
        connection, _ = admin_db
        await _apply_agent_ddl(connection)
        await _create_agent(
            connection, agent_id="a1", name="agent_one", session="fleet_a", owner_bare_id="pshared"
        )
        # SAME owner, DIFFERENT agent — must succeed under a NON-unique index.
        await _create_agent(
            connection, agent_id="a2", name="agent_two", session="fleet_b", owner_bare_id="pshared"
        )
        rows = await run(
            connection,
            f"SELECT count() FROM {AGENT_TABLE} "
            f"WHERE {_OWNER_FIELD} = type::record('{PRINCIPAL_TABLE}', $p) GROUP ALL",
            {"p": "pshared"},
        )
        assert _one(rows)["count"] == 2, rows

    async def test_the_agent_slice_is_safely_re_appliable(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ DISCRIMINATOR (§1.1). ``ensure_ready`` re-applies the slice on EVERY boot — a
        statement that raises on re-application is a boot-time crash. GREEN at HEAD and on the
        correct build; REDDENS a build whose ``owner_principal`` INDEX is ``OVERWRITE`` (which
        rebuilds over every row on the 2nd apply)."""
        connection, _ = admin_db
        for _ in range(2):
            await _apply_agent_ddl(connection)


# --------------------------------------------------------------------------- #
# LEG 3 — DIRTY-STORE MIGRATION (store §1.6). Every ordinary test mints a VIRGIN
# db, so no ordinary fixture can see the "new field on a POPULATED table" defect
# (#107/#131). Apply the OLD slice -> dirty it with a legacy agent -> apply the
# CURRENT slice, and demand the field lands as an OPTIONAL column without poisoning.
# --------------------------------------------------------------------------- #


class TestOwnerPrincipalMigratesOntoAPopulatedAgentTable:
    """Store §1.4 + §1.6 — the dirty-store blind spot, exercised for real."""

    async def test_a_legacy_agent_survives_the_field_add_and_reads_owner_none(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """A migration that "converges" the schema by destroying the rows under it has
        migrated nothing. The legacy agent (written under the OLD slice, before the field
        existed) must survive the field-add and read ``owner_principal`` back as ``None``
        (option<> unset; explicit projection, store §2). GREEN at HEAD (OLD==NEW slice, so the
        legacy row is untouched and the projection is None) and on the option<> build; the
        RED-carrier for this class is the sibling ``…is_writable_after_the_migration``."""
        connection, _ = admin_db
        # OLD world: the agent slice WITHOUT owner_principal + a legacy agent row.
        await run(connection, _agent_ddl_without_owner_principal())
        await _create_agent(connection, agent_id="legacy", name="legacy_agent", session="old_sess")
        # NEW world: the real slice (adds owner_principal on a correct build) — the boot re-run.
        await _apply_agent_ddl(connection)
        survived = _one(
            await run(
                connection,
                f"SELECT name, {_OWNER_FIELD} FROM type::record('{AGENT_TABLE}', 'legacy')",
            )
        )
        assert survived["name"] == "legacy_agent"
        assert survived[_OWNER_FIELD] is None, survived

    async def test_the_field_add_does_not_write_poison_the_legacy_row(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ THE §1.4 DISCRIMINATOR (option<> vs required). After the field-add, an UPDATE of
        an UNRELATED column on the legacy row must SUCCEED — the whole record is re-validated
        on write, so a REQUIRED ``owner_principal`` would reject it (``Expected
        record<principal> but found NONE``). GREEN at HEAD (no field to poison) and on the
        option<> build; a required-not-option build reddens here. This is the pin no
        virgin-db fixture can carry — the exact #107/#131 shape."""
        connection, _ = admin_db
        await run(connection, _agent_ddl_without_owner_principal())
        await _create_agent(connection, agent_id="legacy", name="legacy_agent", session="old_sess")
        await _apply_agent_ddl(connection)
        # UPDATE an unrelated option column — a wrongly-REQUIRED owner ASSERT would trip here.
        await run(
            connection,
            f"UPDATE type::record('{AGENT_TABLE}', 'legacy') SET last_note = $note",
            {"note": "touched"},
        )
        row = _one(
            await run(
                connection,
                f"SELECT last_note FROM type::record('{AGENT_TABLE}', 'legacy')",
            )
        )
        assert row["last_note"] == "touched"

    async def test_a_new_owned_agent_is_writable_after_the_migration(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ RED at HEAD — the migration RED-carrier. After applying the CURRENT slice over
        the OLD one, ``owner_principal`` must be a DECLARED column so a NEW agent can carry an
        owner. At HEAD the field never lands (OLD==NEW slice), so the SCHEMAFULL CREATE with
        ``owner_principal`` is REJECTED. On a correct build the field is added and the new
        owned agent reads its owner back."""
        connection, _ = admin_db
        await run(connection, _agent_ddl_without_owner_principal())
        await _create_agent(connection, agent_id="legacy", name="legacy_agent", session="old_sess")
        await _apply_agent_ddl(connection)
        await _create_agent(
            connection, agent_id="fresh", name="fresh_agent", session="new_sess", owner_bare_id="p9"
        )
        row = _one(
            await run(
                connection,
                f"SELECT {_OWNER_FIELD} FROM type::record('{AGENT_TABLE}', 'fresh')",
            )
        )
        assert str(row[_OWNER_FIELD]) == f"{PRINCIPAL_TABLE}:p9", row


# --------------------------------------------------------------------------- #
# LEG 4 — DANGLE on principal delete (R3.2 / I4, store §2). A principal delete is
# ALLOWED while it owns agents; the owned-agent rows SURVIVE with a now-stale
# owner_principal (record<> links do NOT auto-clean). Not refuse, not cascade.
# --------------------------------------------------------------------------- #


@pytest_asyncio.fixture()
async def dangle_env() -> Any:
    """A principal + principal_key + keep + member_of + agent world on a fresh unique DB.

    Mirrors ``test_principal_delete_cascade_61.py``'s ``delete_env``: ``PrincipalStore.delete``
    reads the ``keep`` table (refuse-while-keeping) and counts ``principal_key`` on its OWN
    connection, so BOTH tables MUST exist — the ``PrincipalKeyStore``/``KeepStore``
    ``ensure_ready``s provide them. PLUS the ``agent`` table (``owner_principal``'s home),
    applied on a raw admin connection: the DANGLE property is about agent rows surviving a
    principal delete, and all four tables share the ONE unified-store database. Alice is
    seeded (keeps nothing, holds no keys) so her delete proceeds cleanly. Reaped on exit.
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    principal_store = PrincipalStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    key_store = PrincipalKeyStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    keep_store = KeepStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await principal_store.ensure_ready()  # principal (the owner_principal link target)
    await key_store.ensure_ready()  # principal_key (delete counts it)
    await keep_store.ensure_ready()  # keep + member_of (delete's refuse-while-keeping read)
    await principal_store.create(email=_EMAIL_ALICE)
    admin = await connect_admin(env)
    await _apply_agent_ddl(admin)  # the agent table, in the SAME database
    try:
        yield principal_store, admin, env
    finally:
        await admin.close()
        await keep_store.close()
        await key_store.close()
        await principal_store.close()
        await drop_database(env)


class TestPrincipalDeleteDanglesTheOwnedAgentBackLink:
    """R3.2 (operator-RULED DANGLE-TOLERATED) + removed-behavior I4. Agents are
    retired-not-deleted, so a stale ``owner_principal`` back-link is not a correctness break —
    and cascading agent rows would erase fleet history. Mirrors ``audit.actor_principal``'s
    dangle (61a-w4)."""

    async def test_deleting_a_principal_that_owns_an_agent_succeeds_and_the_agent_survives(
        self, dangle_env: Any
    ) -> None:
        """⚠ RED at HEAD — ``owner_principal`` is undeclared, so creating an OWNED agent is
        rejected at the store (the whole feature is unbuilt). On a correct build the delete
        SUCCEEDS (NOT refused — the discriminator against a refuse build), the owned agent row
        SURVIVES (NOT cascade-deleted — the discriminator against a cascade build), and
        ``owner_principal`` STILL names the now-deleted principal (a tolerated dangle — the
        discriminator against a build that nulls/cleans the link)."""
        principal_store, admin, _env = dangle_env
        alice = await principal_store.get_by_email(_EMAIL_ALICE)
        assert alice is not None
        alice_bare = _bare(alice.id)
        await _create_agent(
            admin, agent_id="owned", name="owned_agent", session="fleet_sess", owner_bare_id=alice_bare
        )
        # control: the agent is owned by a LIVE principal pre-delete.
        pre = _one(
            await run(admin, f"SELECT {_OWNER_FIELD} FROM type::record('{AGENT_TABLE}', 'owned')")
        )
        assert str(pre[_OWNER_FIELD]) == f"{PRINCIPAL_TABLE}:{alice_bare}", pre

        # DANGLE-TOLERATED: the delete is NOT refused even though alice owns an agent, and it
        # cascades only alice's OWN children (her zero principal_keys) — never the agent.
        cascaded = await principal_store.delete(email=_EMAIL_ALICE)
        assert cascaded == 0, f"alice holds no keys; delete must cascade 0, got {cascaded!r}"
        assert await principal_store.get_by_email(_EMAIL_ALICE) is None, "alice was not deleted"

        # The owned agent SURVIVED (not cascade-deleted) …
        rows = await run(admin, f"SELECT {_OWNER_FIELD} FROM type::record('{AGENT_TABLE}', 'owned')")
        assert rows, (
            "the owned agent row was cascade-deleted on principal delete — it must DANGLE "
            "(agents are retired-not-deleted; cascading erases fleet history, R3.2)"
        )
        # … with a now-STALE owner_principal still naming the deleted principal.
        assert str(rows[0][_OWNER_FIELD]) == f"{PRINCIPAL_TABLE}:{alice_bare}", (
            "owner_principal was cleaned/nulled on principal delete — record<> links do NOT "
            "auto-clean (store §2); the tolerated dangle preserves the stale back-link"
        )

    async def test_deleting_a_principal_that_owns_MANY_agents_dangles_them_ALL(
        self, dangle_env: Any
    ) -> None:
        """⚠ RED at HEAD (THE QUANTIFIER LAW — the dangle is ∀ owned agents, not just one).
        A principal that owns MULTIPLE agents is deleted; EVERY owned agent row survives with a
        stale ``owner_principal``. N=2 (not 1) so a build that dangles the FIRST owned agent but
        drops/cleans the rest (or loops over owned agents at all) reddens here where the
        single-agent pin would pass. The delete must not touch ``agent`` at all."""
        principal_store, admin, _env = dangle_env
        alice = await principal_store.get_by_email(_EMAIL_ALICE)
        assert alice is not None
        alice_bare = _bare(alice.id)
        await _create_agent(
            admin, agent_id="own_a", name="owned_a", session="fleet_a", owner_bare_id=alice_bare
        )
        await _create_agent(
            admin, agent_id="own_b", name="owned_b", session="fleet_b", owner_bare_id=alice_bare
        )

        await principal_store.delete(email=_EMAIL_ALICE)
        assert await principal_store.get_by_email(_EMAIL_ALICE) is None, "alice was not deleted"

        # BOTH owned agents survive with the stale back-link (∀, not just the first).
        survivors = await run(
            admin,
            f"SELECT {_OWNER_FIELD} FROM {AGENT_TABLE} "
            f"WHERE {_OWNER_FIELD} = type::record('{PRINCIPAL_TABLE}', $p)",
            {"p": alice_bare},
        )
        assert len(survivors) == 2, (
            f"both agents owned by the deleted principal must DANGLE (survive with the stale "
            f"owner_principal), got {len(survivors)} — a build that dropped/cleaned any of them "
            f"reddens here (R3.2, ∀ owned agents)"
        )
