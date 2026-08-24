"""Contract — packet 62 Wave 2: the per-agent CAPABILITY (anti-spoofing mechanism A).

Author: ``contract-62w2`` (Opus 4.8 CONTRACT author — tests ONLY, no production code).
A separate Opus contract-adversary grades this BEFORE any builder; a dedicated Opus
security-auditor (design §10-O) attacks the built mechanism AFTER. This file is the
MECHANISM core (DDL + mint-in-register + verify_capability admission + no-leak + lifetime);
the shared seams (``stamp_owner`` / ``resolve_agent`` / ``parse_credential``) live in
``test_agent_capability_seams.py`` and the derived reach pin + register owner-derivation +
retired-prose sweep in ``test_agent_capability_reach.py``.

SPEC (the work order, executed verbatim — never re-transcribed):
``docs/design/2026-08-24-packet62-agent-identity-rulings.md`` — the WAVE-2 ADDENDUM
(W2.0–W2.7) with the operator's SF-1/SF-2 rulings stamped in W2.7, plus FORK 1 mechanism (A),
riders R1.1–R1.4 / R3.3, and the FINAL PACKET-62 SCOPE LINE items 2/3/5/6. Operator-RULED
2026-08-24: (A) application-layer per-agent capability; SF-1 = ADOPT (a VERIFIED credential
argument is admissible — identity is taken from the verification RESULT, not the asserted
value; raw ``owner=``/``as_agent=``/``created_by=``/``scope=server`` CLAIMS stay forbidden as
authz inputs); SF-2 = agent-lifecycle-scoped lifetime + the OPTIONAL ``capability_expires_at``
seam (no clock TTL by default; the binding + no-cache revocation IS the bound).

PROOF-BY-PRECEDENT: ``PrincipalKeyStore.verify`` (``loremaster/loremaster/principal_keys.py``,
the packet-49 credential store) is the exact 4-condition / single-``now`` / uniform-``None``-deny
/ no-cache / no-oracle template ``verify_capability`` mirrors (design W2.0/W2.2, R12). The wire
format + hash mirror packet-49 exactly: presented ``<name>:<secret>``; stored
``capability_hash = sha512_hex(f"{name}:{secret}")`` of the WHOLE string; the raw secret is
returned ONCE and NEVER persisted (only the hash is stored).

STORE LAW (``docs/reference/surrealdb-31-capabilities.md`` — cited, never re-transcribed):
§1.1 (FIELD ``OVERWRITE``; INDEX ``IF NOT EXISTS`` never ``OVERWRITE`` — a flip is a boot-time
crash), §1.4 (a NEW field on a POPULATED table MUST be ``option<>`` — a required field poisons
every existing row's next UPDATE and a DEFAULT does not rescue it), §1.6 (the dirty-store blind
spot — every ordinary fixture mints a VIRGIN db, so no ordinary fixture can see a migration
defect), §1.8 (a UNIQUE index over an ``option<>`` column PERMITS MULTIPLE NONE rows and rejects
duplicate NON-NONE — EXACTLY the shape ``capability_hash`` needs: many agents carry NONE, only a
real hash is unique), §2 (``SELECT *`` OMITS a NONE ``option<>`` column; explicit projection
reads ``None``).

⚠ WHY the mechanism lives on the ``agent`` ROW, not a new store (W2.2): an agent has exactly
ONE live capability (1:1) — a FIELD on the owning row, not a child table; ``register``'s create
branch already ``CREATE``s the agent row, so minting is one atomic write; ``verify`` needs
``agent.owner_principal`` (Wave 1) for the binding and it lives on the SAME row; and
``AgentRegistry._query`` is ALREADY the auto-discovered retry seam (``test_retry_seam.py``) so
verify rides it — NO new store, NO new ``_query`` to enroll (this is the design ruling that
settles the #353 fork).

RED-until-built symbols are referenced through GUARDS (``getattr`` / try-import) so COLLECTION
succeeds and each pin REDs at RUNTIME for its OWN reason (not a module-import collapse that
hides every node id from ``--collect-only``).

Live store: ws://127.0.0.1:18000 (NEVER :18500). Per-test unique database, reaped on exit.
NO skip marker — an unreachable store is a LOUD failure, not a skip.
"""

from __future__ import annotations

import inspect
import re
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from fastmcp.server.auth import AccessToken
from loremaster.agents import STATUS_RETIRED, Agent, AgentRegistry
from loremaster.index.records import sha512_hex
from loremaster.principals import PrincipalStore
from loremaster.store import surreal_schema
from loremaster.store.surreal_schema import AGENT_TABLE

_CAP_HASH_FIELD = "capability_hash"
_CAP_EXPIRES_FIELD = "capability_expires_at"
_EMAIL_ALICE = "alice@example.com"
_EMAIL_BOB = "bob@example.com"

_DEFINE_FIELD = re.compile(r"^\s*DEFINE\s+FIELD\b", re.IGNORECASE)
_DEFINE_INDEX = re.compile(r"^\s*DEFINE\s+INDEX\b", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Offline DDL helpers (string-level over generate_agent_ddl — the wave-1 idiom).
# --------------------------------------------------------------------------- #
def _statements(ddl: str) -> list[str]:
    return [line.strip() for line in ddl.split(";") if line.strip()]


def _agent_statements() -> list[str]:
    return _statements(surreal_schema.generate_agent_ddl())


def _field_statement(field: str) -> str | None:
    """The single ``DEFINE FIELD`` for ``agent.<field>`` (None if unbuilt); tolerates the
    ``OVERWRITE`` clause. At-most-one, so a duplicate emitter is a loud failure."""
    matches = [
        statement
        for statement in _agent_statements()
        if _DEFINE_FIELD.match(statement)
        and re.search(rf"\bFIELD\s+(?:OVERWRITE\s+)?{field}\b", statement)
    ]
    assert len(matches) <= 1, f"expected at most one DEFINE FIELD for agent.{field}, got {matches!r}"
    return matches[0] if matches else None


def _index_statement_over(field: str) -> str | None:
    """The single ``DEFINE INDEX`` whose FIELDS are EXACTLY ``field`` (None if unbuilt)."""
    matches = [
        statement
        for statement in _agent_statements()
        if _DEFINE_INDEX.match(statement)
        and re.search(rf"FIELDS\s+{field}\s*$", statement, re.IGNORECASE)
    ]
    assert len(matches) <= 1, f"expected at most one DEFINE INDEX over agent.{field}, got {matches!r}"
    return matches[0] if matches else None


# --------------------------------------------------------------------------- #
# Live-store fixture: a unified DB carrying the principal + agent tables, a real
# AgentRegistry, a PrincipalStore (create/suspend/expire owners) and a raw admin
# connection (row inspection + dirty-store). Mirrors test_agent_owns_principal
# _schema.py::dangle_env. TWO principals so the binding + isolation pins have an
# A≠B to discriminate (FIXTURES MUST DISCRIMINATE).
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture()
async def cap_env() -> Any:
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    principal_store = PrincipalStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    registry = AgentRegistry(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await principal_store.ensure_ready()  # principal table = the owner_principal link target
    await registry.ensure_ready()  # agent table (+ the wave-2 capability columns on a correct build)
    alice = await principal_store.create(email=_EMAIL_ALICE)
    bob = await principal_store.create(email=_EMAIL_BOB)
    admin = await connect_admin(env)
    try:
        yield SimpleNamespace(
            env=env,
            registry=registry,
            principals=principal_store,
            admin=admin,
            alice_bare=_bare(alice.id),
            bob_bare=_bare(bob.id),
        )
    finally:
        await admin.close()
        await registry.close()
        await principal_store.close()
        await drop_database(env)


def _bare(record_id: str) -> str:
    """``principal:abc`` -> ``abc``; a bare id passes through."""
    return record_id.partition(":")[2] or record_id


def _token(email: str, *, role: str = "member") -> AccessToken:
    """A minimal transport ``AccessToken`` whose PRINCIPAL identity is ``email`` — the
    api-key-branch shape ``LoreTokenVerifier._mint_api_key_identity`` mints (subject = the
    principal email; ``claims["agent"]`` is None — the token carries NO agent, W2.4/SF-3)."""
    return AccessToken(
        token=f"tok-{email}",
        client_id=f"api_key:{email}",
        scopes=["lore:read", "lore:write"],
        subject=email,
        claims={"role": role, "agent": None, "key_name": "local"},
    )


async def _register_owned(env: Any, *, name: str, session: str, owner_bare: str | None) -> Any:
    """Register an agent whose ``owner_principal`` is ``owner_bare`` (server-derived — R3.3),
    minting its capability. RED-until-built: ``register`` gains an ``owner_principal_id`` kw and
    an ``AgentRegisterResult.capability`` in wave 2, so at HEAD this raises TypeError/AttributeError."""
    return await env.registry.register(
        name, session=session, role="worker", owner_principal_id=owner_bare
    )


async def _stored_capability_hash(env: Any, agent_id: str) -> Any:
    """The raw stored ``capability_hash`` for an agent row (explicit projection — store §2: a
    NONE ``option<>`` column reads back as ``None`` under an explicit projection, is OMITTED
    under ``SELECT *``)."""
    rows = await run(
        env.admin,
        f"SELECT {_CAP_HASH_FIELD} FROM type::record('{AGENT_TABLE}', $id)",
        {"id": agent_id},
    )
    assert rows, f"agent row {agent_id!r} not found"
    return rows[0][_CAP_HASH_FIELD]


def _verify_capability(env: Any) -> Any:
    """The ``verify_capability`` bound method, or None if unbuilt (RED-carrier guard)."""
    return getattr(env.registry, "verify_capability", None)


# --------------------------------------------------------------------------- #
# LEG 1 — OFFLINE DDL pins (W2-R7, store §1.1/§1.4/§1.8). Existence pins carry the
# RED; clause pins are GUARDED by them (a clause pin over an absent field passes
# vacuously) — the wave-1 / test_principal_keys_schema idiom.
# --------------------------------------------------------------------------- #
class TestTheCapabilityHashFieldDdl:
    """W2.2 + W2-R7 + store §1.1/§1.4 — ``agent.capability_hash : option<string>`` OVERWRITE."""

    def test_the_capability_hash_field_is_emitted(self) -> None:
        """⚠ RED at HEAD — ``capability_hash`` is not in ``_AGENT_FIELD_SPECS`` yet. The
        existence CONTROL for the clause pins below."""
        assert _field_statement(_CAP_HASH_FIELD) is not None, (
            "generate_agent_ddl() emits no DEFINE FIELD for agent.capability_hash — the "
            "per-agent capability is unbuilt (packet 62 wave 2, W2.2)"
        )

    def test_the_capability_hash_field_is_option_string(self) -> None:
        """⚠ store §1.4: ``agent`` is a POPULATED table, so a NEW field MUST be ``option<>`` — a
        required ``string`` poisons every existing agent row's next UPDATE (a DEFAULT does not
        rescue it), and an agent minted before this field (or a legacy row) legitimately carries
        NONE. RED at HEAD; REDDENS a required-not-option build."""
        statement = _field_statement(_CAP_HASH_FIELD)
        assert statement is not None, "unbuilt (see test_the_capability_hash_field_is_emitted)"
        collapsed = statement.replace(" ", "")
        assert "option<string>" in collapsed, (
            f"agent.{_CAP_HASH_FIELD} must be option<string> (§1.4 — a required field on a "
            f"POPULATED table poisons every legacy agent row): {statement}"
        )

    def test_the_capability_hash_field_is_OVERWRITE(self) -> None:
        """⚠ #107 verbatim (§1.1): ``IF NOT EXISTS`` on an existing field is a SILENT no-op. Only
        ``OVERWRITE`` lands a changed definition on a live store. RED at HEAD; REDDENS an
        ``IF NOT EXISTS`` build."""
        statement = _field_statement(_CAP_HASH_FIELD)
        assert statement is not None, "unbuilt (see test_the_capability_hash_field_is_emitted)"
        assert "OVERWRITE" in statement.upper(), statement
        assert "IF NOT EXISTS" not in statement.upper(), statement

    def test_the_capability_hash_field_routes_through_the_shared_emitter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ ONE IMPLEMENTATION, proven by MUTATION: nothing REQUIRES the slice to CALL
        ``_define_field`` — a hand-written ``DEFINE FIELD`` string would pass every clause pin
        above while silently not sharing the #107 ``OVERWRITE`` policy. Perturb the shared
        emitter; the ``capability_hash`` field def must move. RED at HEAD (nothing to move)."""
        original = surreal_schema._define_field
        monkeypatch.setattr(
            surreal_schema,
            "_define_field",
            lambda *a, **k: f"{original(*a, **k)} COMMENT 'cap-mutation-probe'",
        )
        hits = [
            statement
            for statement in _agent_statements()
            if _DEFINE_FIELD.match(statement) and re.search(rf"\b{_CAP_HASH_FIELD}\b", statement)
        ]
        assert hits, f"no DEFINE FIELD for agent.{_CAP_HASH_FIELD} — unbuilt or renamed off the emitter"
        assert all("cap-mutation-probe" in statement for statement in hits), (
            f"agent.{_CAP_HASH_FIELD} does not route through surreal_schema._define_field — a "
            f"hand-written DEFINE FIELD bypasses the #107 OVERWRITE policy"
        )


class TestTheCapabilityHashUniqueIndex:
    """W2.2 + store §1.1/§1.8 — a UNIQUE index over ``option<string>`` capability_hash gives
    'multiple NONE coexist + a real hash is unique' (the exact shape needed; §1.8)."""

    def test_the_capability_hash_index_is_emitted(self) -> None:
        """⚠ RED at HEAD — the capability lookup is a UNIQUE-hash-index probe (uniform timing,
        no name-existence oracle, the packet-49 precedent), so the index must exist."""
        assert _index_statement_over(_CAP_HASH_FIELD) is not None, (
            f"generate_agent_ddl() emits no DEFINE INDEX over agent.{_CAP_HASH_FIELD} — the "
            f"UNIQUE-hash lookup is unbuilt (W2.2)"
        )

    def test_the_capability_hash_index_is_UNIQUE(self) -> None:
        """⚠ W2.2: the index is UNIQUE — a duplicate capability hash across agents is rejected
        (the collision backstop), while §1.8 lets the MANY agents with NONE coexist. RED at HEAD;
        REDDENS a non-unique build."""
        statement = _index_statement_over(_CAP_HASH_FIELD)
        assert statement is not None, "unbuilt (see test_the_capability_hash_index_is_emitted)"
        assert "UNIQUE" in statement.upper(), (
            f"agent.{_CAP_HASH_FIELD} index must be UNIQUE (the collision backstop, W2.2): {statement}"
        )

    def test_the_capability_hash_index_is_IF_NOT_EXISTS_never_OVERWRITE(self) -> None:
        """⚠ store §1.1: ``OVERWRITE`` on an index REBUILDS it over every row on every
        ``ensure_ready`` boot → a boot-time crash. Indexes stay ``IF NOT EXISTS``. RED at HEAD;
        REDDENS an ``OVERWRITE`` index."""
        statement = _index_statement_over(_CAP_HASH_FIELD)
        assert statement is not None, "unbuilt (see test_the_capability_hash_index_is_emitted)"
        assert "IF NOT EXISTS" in statement.upper(), statement
        assert "OVERWRITE" not in statement.upper(), statement


class TestTheOptionalCapabilityExpiresSeam:
    """SF-2 / W2-R4 — the OPTIONAL ``capability_expires_at : option<datetime>`` defense-in-depth
    seam (mirrors ``principal_key.expires_at``). Present, defaults to NEVER; the lifecycle bound
    (binding + no-cache revocation) is the default, NOT a clock TTL (pinned live below)."""

    def test_the_capability_expires_field_is_emitted_as_option_datetime(self) -> None:
        """⚠ RED at HEAD — the optional expiry seam is unbuilt. It is ``option<datetime>``
        (§1.4, a new field on a POPULATED table) OVERWRITE (§1.1). Present but defaulting to
        NONE = never expires (SF-2)."""
        statement = _field_statement(_CAP_EXPIRES_FIELD)
        assert statement is not None, (
            f"generate_agent_ddl() emits no DEFINE FIELD for agent.{_CAP_EXPIRES_FIELD} — the "
            f"optional capability-expiry seam is unbuilt (SF-2 / W2-R4)"
        )
        collapsed = statement.replace(" ", "")
        assert "option<datetime>" in collapsed, statement
        assert "OVERWRITE" in statement.upper() and "IF NOT EXISTS" not in statement.upper(), statement


# --------------------------------------------------------------------------- #
# LEG 2 — DIRTY-STORE MIGRATION (store §1.4/§1.6). Every ordinary fixture mints a
# VIRGIN db, so none can see the "new field on a POPULATED table" defect. Apply the
# OLD slice -> dirty it with a legacy agent -> apply the CURRENT slice, and demand
# capability_hash lands as an OPTIONAL column without poisoning. Mirrors wave-1
# TestOwnerPrincipalMigratesOntoAPopulatedAgentTable.
# --------------------------------------------------------------------------- #
def _agent_ddl_without_capability() -> str:
    """The agent slice with every capability_* statement stripped — the OLD (pre-wave-2) world.
    At HEAD this EQUALS generate_agent_ddl() (nothing to strip); on a correct build it is the
    real slice minus the capability field(s) + index, so applying the real slice OVER it IS the
    field-add migration (§1.6 idiom; OLD/NEW share the real emitter)."""
    kept = [statement for statement in _agent_statements() if "capability" not in statement.lower()]
    return ";\n".join(kept) + ";\n"


class TestCapabilityHashMigratesOntoAPopulatedAgentTable:
    """Store §1.4 + §1.6 — the dirty-store blind spot, exercised for real."""

    async def test_a_legacy_agent_survives_the_field_add_and_reads_capability_none(
        self, cap_env: Any
    ) -> None:
        """A migration that converges the schema by poisoning the rows under it has migrated
        nothing. The legacy agent (written under the OLD slice) must survive the field-add and
        read ``capability_hash`` back as ``None`` (option<> unset; explicit projection, §2). GREEN
        at HEAD (OLD==NEW slice) and on the option<> build."""
        await run(cap_env.admin, _agent_ddl_without_capability())
        await run(
            cap_env.admin,
            f"CREATE type::record('{AGENT_TABLE}', 'legacy') CONTENT $c",
            {"c": _legacy_agent_content()},
        )
        await run(cap_env.admin, surreal_schema.generate_agent_ddl())  # the boot re-run adds the field
        rows = await run(
            cap_env.admin,
            f"SELECT name, {_CAP_HASH_FIELD} FROM type::record('{AGENT_TABLE}', 'legacy')",
        )
        assert rows and rows[0]["name"] == "legacy_agent"
        assert rows[0][_CAP_HASH_FIELD] is None, rows

    async def test_the_field_add_does_not_write_poison_the_legacy_row(self, cap_env: Any) -> None:
        """⚠ THE §1.4 DISCRIMINATOR (option<> vs required). After the field-add, an UPDATE of an
        UNRELATED column on the legacy row must SUCCEED — the whole record is re-validated on
        write, so a REQUIRED ``capability_hash`` would reject it (``Expected string but found
        NONE``). GREEN at HEAD (no field to poison) and on the option<> build; a required-not-option
        build reddens here. The pin no virgin-db fixture can carry — the exact #107/#131 shape."""
        await run(cap_env.admin, _agent_ddl_without_capability())
        await run(
            cap_env.admin,
            f"CREATE type::record('{AGENT_TABLE}', 'legacy') CONTENT $c",
            {"c": _legacy_agent_content()},
        )
        await run(cap_env.admin, surreal_schema.generate_agent_ddl())
        await run(
            cap_env.admin,
            f"UPDATE type::record('{AGENT_TABLE}', 'legacy') SET last_note = $n",
            {"n": "touched"},
        )
        rows = await run(
            cap_env.admin, f"SELECT last_note FROM type::record('{AGENT_TABLE}', 'legacy')"
        )
        assert rows and rows[0]["last_note"] == "touched", rows


def _legacy_agent_content() -> dict[str, Any]:
    now = datetime.now(UTC)
    return {
        "name": "legacy_agent",
        "session": "old_sess",
        "role": "worker",
        "status": "active",
        "registered_at": now,
        "heartbeat_at": now,
    }


# --------------------------------------------------------------------------- #
# LEG 3 — MINT-IN-REGISTER (W2.3, W2-R6). The create branch mints the secret,
# stores only the hash, returns the raw <name>:<secret> ONCE. Re-register does NOT
# rotate a live secret (mint-once-on-create).
# --------------------------------------------------------------------------- #
class TestMintInRegister:
    """W2.3: ``register``'s create branch mints ``secrets.token_urlsafe(32)``, stores
    ``capability_hash = sha512_hex(f"{name}:{secret}")``, returns the raw credential ONCE."""

    async def test_first_register_returns_a_raw_capability_once(self, cap_env: Any) -> None:
        """⚠ RED at HEAD — ``AgentRegisterResult`` has no ``capability`` field yet (extra=forbid).
        On a correct build the FIRST register of a (session, name) returns a non-blank raw
        ``<name>:<secret>`` credential."""
        result = await cap_env.registry.register("alice_worker", session="s1", role="worker")
        capability = getattr(result, "capability", None)
        assert capability, (
            "register(...).capability must be the raw one-time <name>:<secret> credential on a "
            "first register (W2.3) — absent/blank means the mint is unbuilt"
        )
        assert ":" in capability and capability.rsplit(":", 1)[1].strip(), (
            f"the returned capability must be a parseable <name>:<secret> (W2.1): {capability!r}"
        )

    async def test_the_stored_hash_is_sha512_of_the_whole_returned_credential(
        self, cap_env: Any
    ) -> None:
        """⚠ RED at HEAD. THE wire-format invariant (packet-49 mirror, W2.1): the stored
        ``capability_hash`` is ``sha512_hex`` of the WHOLE returned ``<name>:<secret>`` string —
        so the credential the caller holds hashes to exactly the row's stored digest. REDDENS a
        build that stores the raw secret, or hashes only the secret half, or a different digest."""
        result = await cap_env.registry.register("alice_worker", session="s1", role="worker")
        capability = getattr(result, "capability", None)
        assert capability, "unbuilt (see test_first_register_returns_a_raw_capability_once)"
        stored = await _stored_capability_hash(cap_env, result.agent.id)
        assert stored == sha512_hex(capability), (
            "the stored capability_hash must equal sha512_hex(returned_credential) — the packet-49 "
            "wire-format invariant (W2.1); a mismatch means the raw secret is stored, the hash "
            "covers the wrong bytes, or a non-sha512 digest was used"
        )

    async def test_the_raw_secret_is_never_persisted_as_a_readable_column(
        self, cap_env: Any
    ) -> None:
        """⚠ RED at HEAD (§F3a / W2-R6). The store NEVER persists the raw secret — only the hash.
        A hostile, secret-shaped credential must appear in NO readable column of the agent row.
        REDDENS a build that stores the raw ``<name>:<secret>`` anywhere on the row."""
        result = await cap_env.registry.register("alice_worker", session="s1", role="worker")
        capability = getattr(result, "capability", None)
        assert capability, "unbuilt (see test_first_register_returns_a_raw_capability_once)"
        _, _, secret = capability.partition(":")
        rows = await run(
            cap_env.admin, f"SELECT * FROM type::record('{AGENT_TABLE}', $id)", {"id": result.agent.id}
        )
        blob = repr(rows)
        assert secret not in blob, (
            "the raw secret is readable off the stored agent row — only sha512_hex(credential) "
            "may be persisted (§F3a / W2-R6); the raw secret is returned once and never stored"
        )
        assert capability not in blob, blob

    async def test_re_register_does_not_rotate_a_live_secret(self, cap_env: Any) -> None:
        """⚠ MINT-ONCE-ON-CREATE (W2.3 / W2-R6): the idempotent re-register branch does NOT
        rotate the secret (a running agent already holds it; rotating breaks it mid-session). The
        second register returns ``capability = None`` (nothing minted), the stored hash is
        UNCHANGED, and the FIRST credential still hashes to it. RED at HEAD; REDDENS a build that
        re-mints on every register."""
        first = await cap_env.registry.register("alice_worker", session="s1", role="worker")
        first_cap = getattr(first, "capability", None)
        assert first_cap, "unbuilt (see test_first_register_returns_a_raw_capability_once)"
        first_hash = await _stored_capability_hash(cap_env, first.agent.id)

        second = await cap_env.registry.register("alice_worker", session="s1", role="worker")
        assert second.re_registered is True
        assert getattr(second, "capability", "SENTINEL") is None, (
            "re-register must NOT mint a new secret (mint-once-on-create, W2.3) — capability must "
            "be None on a re-register, not a fresh <name>:<secret>"
        )
        assert await _stored_capability_hash(cap_env, second.agent.id) == first_hash, (
            "re-register rotated the stored capability_hash — the live secret the agent holds is "
            "now dead (mint-once-on-create violated, W2-R6)"
        )
        assert first_hash == sha512_hex(first_cap)


class TestTheCapabilityNeverLeaksOntoTheAgentValueObject:
    """§F3a / W2-R6 — the raw secret AND its hash live ONLY in the store row / the one-time
    register return; the fleet-visible ``Agent`` value object (returned by register/get_agent/
    fleet) carries NEITHER, so no rendered/logged surface can leak them."""

    def test_the_agent_model_has_no_capability_or_hash_or_secret_field(self) -> None:
        """⚠ A STATIC GUARD (green at HEAD, RED on a leaky build): ``Agent`` — the value object
        every render/list serialises — must expose no ``capability`` / ``capability_hash`` /
        ``secret`` field. REDDENS a build that threads the hash onto the model (where ``SELECT *``
        + a fleet render would serialise it into a §F3a credential-in-a-log defect)."""
        forbidden = {"capability", _CAP_HASH_FIELD, "secret"}
        leaked = forbidden & set(Agent.model_fields)
        assert not leaked, (
            f"Agent (the fleet-rendered value object) exposes {sorted(leaked)!r} — the capability "
            f"hash/secret must live only in the store row + the one-time register return (§F3a)"
        )

    async def test_a_secret_shaped_value_never_appears_in_a_rendered_agent(
        self, cap_env: Any
    ) -> None:
        """⚠ RED at HEAD (HOSTILE fixture, §F3a). After a real mint, the raw secret must appear in
        NO serialisation of the returned ``Agent`` nor of a ``get_agent`` re-read — only in the
        ``.capability`` field of the register RESULT itself. REDDENS a build that carries the
        secret through the agent render."""
        result = await cap_env.registry.register("alice_worker", session="s1", role="worker")
        capability = getattr(result, "capability", None)
        assert capability, "unbuilt (see test_first_register_returns_a_raw_capability_once)"
        _, _, secret = capability.partition(":")
        assert secret not in result.agent.model_dump_json(), "secret leaked into the returned Agent"
        reread = await cap_env.registry.get_agent("alice_worker", session="s1")
        assert secret not in reread.model_dump_json(), "secret leaked into a get_agent() render"


# --------------------------------------------------------------------------- #
# LEG 4 — verify_capability ADMISSION (W2.2). Re-checked EVERY call, one `now`, no
# cache, uniform None deny, no oracle — the PrincipalKeyStore.verify template. Four
# conditions: (1) hash match; (2) agent NOT retired; (3) THE BINDING owner_principal
# == token principal; (4) owning principal active + unexpired.
# --------------------------------------------------------------------------- #
class TestVerifyCapabilityAdmission:
    """W2.2 admission conditions, each with a POSITIVE CONTROL (the good input accepted) so a
    deny is never a probe passing for the WRONG reason."""

    async def test_a_valid_capability_under_its_owners_token_resolves_the_agent(
        self, cap_env: Any
    ) -> None:
        """⚠ RED at HEAD (verify_capability absent). THE POSITIVE CONTROL for every deny below:
        agent-A's valid capability, presented under principal-A's transport token, resolves to
        A's agent id. If this cannot pass, the deny pins are meaningless."""
        verify = _verify_capability(cap_env)
        assert verify is not None, "AgentRegistry.verify_capability is unbuilt (W2.2)"
        result = await _register_owned(
            cap_env, name="alice_worker", session="s1", owner_bare=cap_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"
        resolved = await verify(capability, _token(_EMAIL_ALICE))
        assert resolved == result.agent.id, (
            f"a valid capability under its OWNER's token must resolve the bound agent id "
            f"{result.agent.id!r}, got {resolved!r}"
        )

    async def test_a_forged_capability_without_the_secret_is_denied(self, cap_env: Any) -> None:
        """⚠ PREIMAGE RESISTANCE (W2.2). A credential with the right NAME half but a wrong secret
        hashes to no stored row → uniform None. Positive control: the real secret resolves. RED at
        HEAD; REDDENS a build that matches on the name half instead of the hash."""
        verify = _verify_capability(cap_env)
        assert verify is not None, "verify_capability unbuilt"
        result = await _register_owned(
            cap_env, name="alice_worker", session="s1", owner_bare=cap_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"
        name = capability.partition(":")[0]
        assert await verify(f"{name}:not-the-real-secret", _token(_EMAIL_ALICE)) is None, (
            "a forged capability (right name, wrong secret) must DENY — no hash match (preimage)"
        )
        assert await verify(capability, _token(_EMAIL_ALICE)) == result.agent.id  # positive control

    async def test_the_binding_denies_a_valid_capability_under_a_DIFFERENT_principals_token(
        self, cap_env: Any
    ) -> None:
        """⚠ THE LOAD-BEARING BINDING PIN (W2-R2, W2.2 condition 3). Agent-A's VALID capability,
        presented under principal-B's transport token, DENIES — this is what makes a leaked
        capability useless to anyone but its owner (the ONLY accepted residual, Fork 1). Positive
        control: A's capability under A's token resolves. RED at HEAD; REDDENS a build that skips
        the (principal, agent) binding — the confused-deputy hole §3.2 forbids."""
        verify = _verify_capability(cap_env)
        assert verify is not None, "verify_capability unbuilt"
        result = await _register_owned(
            cap_env, name="alice_worker", session="s1", owner_bare=cap_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"
        # A's valid capability under B's token -> DENY (binding mismatch).
        assert await verify(capability, _token(_EMAIL_BOB)) is None, (
            "agent-A's valid capability presented under principal-B's token must DENY (W2-R2) — "
            "the binding agent.owner_principal == the transport principal is the anti-spoof bar"
        )
        # A's valid capability under A's token -> ACCEPT (positive control: nothing else changed).
        assert await verify(capability, _token(_EMAIL_ALICE)) == result.agent.id

    async def test_a_retired_agents_capability_is_denied_next_call_no_cache(
        self, cap_env: Any
    ) -> None:
        """⚠ NO-CACHE REVOCATION (W2-R3, W2.2 condition 2). Retiring the agent denies its
        capability on the VERY NEXT call — no residual window (verify re-checks the live row every
        call, the R12 no-cache discipline). Positive control: the live capability is accepted
        BEFORE the retire. RED at HEAD; REDDENS a build that caches the verdict."""
        verify = _verify_capability(cap_env)
        assert verify is not None, "verify_capability unbuilt"
        result = await _register_owned(
            cap_env, name="alice_worker", session="s1", owner_bare=cap_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"
        assert await verify(capability, _token(_EMAIL_ALICE)) == result.agent.id  # live: accepted
        await cap_env.registry.touch("alice_worker", session="s1", status=STATUS_RETIRED)
        assert await verify(capability, _token(_EMAIL_ALICE)) is None, (
            "a retired agent's capability must DENY on the very next call — no residual window "
            "(no-cache revocation, W2-R3, condition 2)"
        )

    async def test_a_suspended_owning_principal_denies_the_capability(self, cap_env: Any) -> None:
        """⚠ W2.2 condition 4 (owning principal active). Suspending the OWNING principal denies
        its agents' capabilities on the next call (transitive, via owner_principal). Positive
        control: an active owner is accepted. RED at HEAD; REDDENS a build that omits the
        owning-principal admission check."""
        verify = _verify_capability(cap_env)
        assert verify is not None, "verify_capability unbuilt"
        result = await _register_owned(
            cap_env, name="alice_worker", session="s1", owner_bare=cap_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"
        assert await verify(capability, _token(_EMAIL_ALICE)) == result.agent.id  # active: accepted
        await cap_env.principals.set_status(email=_EMAIL_ALICE, status="suspended")
        assert await verify(capability, _token(_EMAIL_ALICE)) is None, (
            "a capability whose OWNING principal is suspended must DENY (W2.2 condition 4, "
            "transitive via owner_principal)"
        )

    async def test_an_expired_owning_principal_denies_the_capability(self, cap_env: Any) -> None:
        """⚠ W2.2 condition 4 (owning principal unexpired), the second half. An owner whose
        ``expires_at`` is in the past denies; positive control: the same owner unexpired is
        accepted. RED at HEAD."""
        verify = _verify_capability(cap_env)
        assert verify is not None, "verify_capability unbuilt"
        result = await _register_owned(
            cap_env, name="alice_worker", session="s1", owner_bare=cap_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"
        assert await verify(capability, _token(_EMAIL_ALICE)) == result.agent.id  # unexpired: accepted
        await cap_env.principals.set_expires(
            email=_EMAIL_ALICE, expires_at=datetime.now(UTC) - timedelta(days=1)
        )
        assert await verify(capability, _token(_EMAIL_ALICE)) is None, (
            "a capability whose OWNING principal has expired must DENY (W2.2 condition 4)"
        )


class TestVerifyCapabilityUniformDenyNoOracle:
    """W2.2 — malformed / injected input is a UNIFORM None deny (no oracle), and the presented
    string is a BOUND param, never interpolated."""

    @pytest.mark.parametrize(
        "presented",
        ["", "   ", "no-colon-at-all", "name-only:", ":secret-only", "   :   "],
        ids=["blank", "whitespace", "no-colon", "blank-secret", "blank-name", "blank-halves"],
    )
    async def test_a_malformed_credential_denies_uniformly(
        self, cap_env: Any, presented: str
    ) -> None:
        """⚠ RED at HEAD. Every malformed shape (blank, no colon, blank half) is a uniform None —
        the shared parse-credential reject (W2.6 DRY). REDDENS a build that raises, or that leaks
        a distinct error per shape (an oracle)."""
        verify = _verify_capability(cap_env)
        assert verify is not None, "verify_capability unbuilt"
        assert await verify(presented, _token(_EMAIL_ALICE)) is None, (
            f"malformed credential {presented!r} must be a uniform None deny (no raise, no oracle)"
        )

    async def test_an_injection_laden_credential_is_a_bound_param_not_interpolated(
        self, cap_env: Any
    ) -> None:
        """⚠ RED at HEAD. A presented string full of SurrealQL metacharacters must be a BOUND
        parameter (``$h`` = sha512_hex(presented)), never interpolated — it hashes to no row and
        denies uniformly, and it must NOT corrupt the query or the agent table. Positive control:
        the legitimate capability still resolves AFTER the hostile call (the table is intact)."""
        verify = _verify_capability(cap_env)
        assert verify is not None, "verify_capability unbuilt"
        result = await _register_owned(
            cap_env, name="alice_worker", session="s1", owner_bare=cap_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"
        hostile = "x':secret'; DELETE agent; --"
        assert await verify(hostile, _token(_EMAIL_ALICE)) is None, "injection payload must deny"
        # positive control: the table survived and the real capability still resolves.
        assert await verify(capability, _token(_EMAIL_ALICE)) == result.agent.id, (
            "the hostile presented string corrupted the query/table — it must be a bound $h param"
        )


class TestCapabilityLifetimeIsLifecycleScopedNotAClockTtl:
    """SF-2 / W2-R4 — the lifetime bound is the BINDING + no-cache revocation, NOT a clock TTL.
    Pinned OUT LOUD (a pin-the-miss so a future engineer meets the bound deliberately). The
    OPTIONAL ``capability_expires_at`` seam, when SET, IS enforced (a field that exists but is
    never checked is a decorative lie — the trust doctrine forbids a surface that looks like it
    limits and does not); when NONE (the default) it never time-gates."""

    async def test_a_capability_with_no_expiry_is_not_time_gated(self, cap_env: Any) -> None:
        """⚠ THE PIN-THE-MISS (SF-2): a freshly-minted capability carries NO ``capability_expires_at``
        (defaults to never), and verify_capability takes no clock/TTL that would age it out — so it
        is accepted purely on the live-row admission conditions, with no time bound. RED at HEAD.
        (The bound is the lifecycle + revocation, W2-R3 — NOT a clock; if a future engineer adds a
        default clock TTL, delete this pin and say so.)"""
        verify = _verify_capability(cap_env)
        assert verify is not None, "verify_capability unbuilt"
        result = await _register_owned(
            cap_env, name="alice_worker", session="s1", owner_bare=cap_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"
        # No expiry was set; the row's capability_expires_at is NONE.
        expiry = await run(
            cap_env.admin,
            f"SELECT {_CAP_EXPIRES_FIELD} FROM type::record('{AGENT_TABLE}', $id)",
            {"id": result.agent.id},
        )
        assert expiry and expiry[0][_CAP_EXPIRES_FIELD] is None, (
            "a freshly-minted capability must default to NO expiry (never) — SF-2 lifecycle-scoped"
        )
        assert await verify(capability, _token(_EMAIL_ALICE)) == result.agent.id, (
            "a capability with no expiry must be accepted on the live-row conditions alone — there "
            "is NO default clock TTL (SF-2; the bound is the binding + no-cache revocation)"
        )

    async def test_a_capability_whose_optional_expiry_is_in_the_past_is_denied(
        self, cap_env: Any
    ) -> None:
        """⚠ THE DEFENSE-IN-DEPTH SEAM IS REAL WHEN USED (SF-2 / W2-R4). If an operator SETS
        ``capability_expires_at`` in the past, verify denies (the ``_absolute_expiry``-style
        re-check on the same field). Positive control: an expiry in the FUTURE is accepted. RED at
        HEAD (the field is undeclared, so this admin UPDATE is rejected). REDDENS a build that adds
        the field but never checks it — a decorative-expiry lie.
        ⚠ NOTE (contract author): SF-2 frames enforcement as OPTIONAL defense-in-depth. I pin
        enforced-when-SET so the field is not a false surface; if the operator wants it
        present-but-unenforced, delete this pin DELIBERATELY (per the pin-the-miss law)."""
        verify = _verify_capability(cap_env)
        assert verify is not None, "verify_capability unbuilt"
        result = await _register_owned(
            cap_env, name="alice_worker", session="s1", owner_bare=cap_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"
        await run(
            cap_env.admin,
            f"UPDATE type::record('{AGENT_TABLE}', $id) SET {_CAP_EXPIRES_FIELD} = $t",
            {"id": result.agent.id, "t": datetime.now(UTC) - timedelta(minutes=1)},
        )
        assert await verify(capability, _token(_EMAIL_ALICE)) is None, (
            "a capability whose capability_expires_at is in the past must DENY when the seam is "
            "used (SF-2 defense-in-depth) — a field that exists but is never checked is a lie"
        )
        # positive control: a FUTURE expiry is accepted (the seam denies only on real expiry).
        await run(
            cap_env.admin,
            f"UPDATE type::record('{AGENT_TABLE}', $id) SET {_CAP_EXPIRES_FIELD} = $t",
            {"id": result.agent.id, "t": datetime.now(UTC) + timedelta(days=1)},
        )
        assert await verify(capability, _token(_EMAIL_ALICE)) == result.agent.id


# --------------------------------------------------------------------------- #
# LEG 5 — the retry seam (W2.2: verify rides the EXISTING AgentRegistry._query;
# NO new store, NO new _query to enroll). Mutation-proven so a hand-rolled
# connection cannot masquerade as sharing.
# --------------------------------------------------------------------------- #
class TestVerifyCapabilityRidesTheSharedQuerySeam:
    """W2.2 / #102/#120 — verify_capability's DB access routes through ``AgentRegistry._query``
    (already auto-discovered + mapped by test_retry_seam.py), never a private connection."""

    async def test_verify_capability_routes_through_agent_registry_query(
        self, cap_env: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD. Perturb ``AgentRegistry._query`` to a loud sentinel; verify_capability's
        lookup must surface it — proving it rides the ONE shared seam, not a hand-rolled query.
        REDDENS a build whose verify opens its own connection (a private copy that dodges the
        shared retry/classification policy and the test_retry_seam scan)."""
        verify = _verify_capability(cap_env)
        assert verify is not None, "verify_capability unbuilt"
        result = await _register_owned(
            cap_env, name="alice_worker", session="s1", owner_bare=cap_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"

        sentinel = RuntimeError("shared-seam-probe")

        async def _boom(*_a: Any, **_k: Any) -> Any:
            raise sentinel

        monkeypatch.setattr(cap_env.registry, "_query", _boom)
        with pytest.raises(RuntimeError, match="shared-seam-probe"):
            await verify(capability, _token(_EMAIL_ALICE))


# --------------------------------------------------------------------------- #
# LEG 6 — the register-time server-side OWNER stamp (R3.3 / scope item 2). The
# owner is derived from the AUTHENTICATED credential (server-side), NEVER from a
# tool argument; an absent credential leaves the agent OWNERLESS (pre-cutover legal,
# Fork 2), NOT a fabricated owner.
# --------------------------------------------------------------------------- #
class TestRegisterStampsOwnerPrincipalFromTheCredential:
    """R3.3 — ``AgentRegistry.register`` stamps ``agent.owner_principal`` from a SERVER-derived
    ``owner_principal_id`` (the transport credential's principal), never a display argument. The
    only owner channel is that server-derived id; a caller-facing ``owner=`` does not exist."""

    async def test_register_stamps_owner_principal_from_the_server_derived_id(
        self, cap_env: Any
    ) -> None:
        """⚠ RED at HEAD — ``register`` gains an ``owner_principal_id`` kw in wave 2 (TypeError at
        HEAD). On a correct build the created agent's ``owner_principal`` names exactly the
        server-derived principal."""
        result = await _register_owned(
            cap_env, name="alice_worker", session="s1", owner_bare=cap_env.alice_bare
        )
        rows = await run(
            cap_env.admin,
            f"SELECT owner_principal FROM type::record('{AGENT_TABLE}', $id)",
            {"id": result.agent.id},
        )
        assert rows and str(rows[0]["owner_principal"]).endswith(f":{cap_env.alice_bare}"), (
            f"register must stamp owner_principal from the server-derived id (R3.3); got {rows!r}"
        )

    async def test_register_without_a_credential_is_ownerless_not_fabricated(
        self, cap_env: Any
    ) -> None:
        """⚠ RED at HEAD — the ``owner_principal_id`` kw is unbuilt. On a correct build, a register
        with NO resolvable credential (``owner_principal_id=None``) leaves ``owner_principal`` NONE
        (the pre-cutover ownerless local fleet, Fork 2) — it does NOT fabricate an owner. REDDENS a
        build that stamps a default/sentinel owner when none was supplied."""
        result = await _register_owned(cap_env, name="free_worker", session="s2", owner_bare=None)
        rows = await run(
            cap_env.admin,
            f"SELECT owner_principal FROM type::record('{AGENT_TABLE}', $id)",
            {"id": result.agent.id},
        )
        assert rows and rows[0]["owner_principal"] is None, (
            f"a register with no credential must be OWNERLESS (owner_principal None, Fork 2), never "
            f"a fabricated/sentinel owner; got {rows!r}"
        )

    async def test_register_exposes_no_display_owner_argument(self) -> None:
        """⚠ RED at HEAD (R3.3 / §3.2.2). The ONLY owner input is the server-derived
        ``owner_principal_id`` — ``register`` must expose NO caller-facing ``owner`` / ``as_agent``
        / ``created_by`` / ``scope`` parameter that could ASSERT ownership (the confused-deputy
        surface). REDDENS a build that adds a display-owner argument alongside the server-derived
        one."""
        params = set(inspect.signature(AgentRegistry.register).parameters)
        assert "owner_principal_id" in params, (
            "register must gain the SERVER-derived owner_principal_id kw (R3.3) — unbuilt"
        )
        display_owner = {"owner", "as_agent", "created_by", "scope"} & params
        assert not display_owner, (
            f"register exposes caller-facing owner argument(s) {sorted(display_owner)!r} — the owner "
            f"is server-derived only; a display owner is the confused-deputy hole (§3.2.2)"
        )
