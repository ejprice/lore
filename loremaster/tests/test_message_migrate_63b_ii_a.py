"""Contract — packet 63b wave ii-a: §4.C — the TWO governed migrate legs that land in 63b, plus the
lifted ``resolve_operator_principal`` (ONE IMPLEMENTATION). Design ``docs/design/2026-09-03-packet63b-
design.md`` §4.C (RULED reading B: BOTH legs land in 63b) + §2.6 (the checked agent→message ORDER) +
§2.1 (the single-principal precondition) + §1.4 (the four-leg exempt frame). Authored by
``contract-63b-ii-a`` (Opus 4.8 contract author — CONTRACT TESTS ONLY, no production).

SPEC (executed verbatim, cited): §4.C rules that 63b ships BOTH
  · ``_migrate_agent_owner`` — stamps ``owner_principal`` on every NONE-owner ``agent`` → THE operator
    principal (via the LIFTED ``resolve_operator_principal``), REFUSING on multi-principal ambiguity;
  · ``_migrate_message_owner`` — ``owner_agent = sender``, ``owner_principal = sender.owner_principal``,
    ``scope = keep:<project>``; REFUSES if ANY ``agent.owner_principal IS NONE`` (§2.6 agent-first).
The operator-principal resolution currently INLINE in ``principals._migrate_memory_scope`` is LIFTED to
ONE ``resolve_operator_principal(principal_store)`` all three legs call (§4.C / §6 reuse ledger — ONE
IMPLEMENTATION, proven by the whole-tree route pin below).

RED-AT-HEAD: at HEAD ``migrate_governed(table="agent")`` refuses with *"does not support table 'agent'"*
and ``migrate_governed(table="message")`` refuses with *"…lands in packet 63b"* (the 63a stubs), and
``_migrate_agent_owner`` / ``_migrate_message_owner`` / ``resolve_operator_principal`` do not exist. The
DISCRIMINATING RED pins are the BACKFILL fates (agent backfills a NONE-owner agent; message backfills
when agent is migrated) — a build that keeps the stub refusal reddens. The refuse pins pair with them
(fixtures-must-discriminate: the §2.6 order is pinned by the backfill-when-clean RED + refuse-when-dirty
control TOGETHER, since the stub refuses either way).

STORE LAW cited (``docs/reference/surrealdb-31-capabilities.md``): §1.4 (governed columns are option<>
on a POPULATED table — the ``governed_overlay_ddl`` seed applies the message overlay independent of the
§4.F emitter, so this leg is testable before §4.F wires it), §2 (bound-RecordID owner links), §3
(execute_transaction / the migrate's driver-routed writes, R4). §2.6 the checked ORDER: message reads
``sender.owner_principal`` (NONE for every un-migrated agent), so message-before-agent is a REFUSAL.

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped. NO skip marker.
pytest runs ``-n auto``.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import (
    apply_ddl,
    build_principal_and_keep_stores,
    function_calls_named,
    governed_overlay_ddl,
    store_handle,
)
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database
from loremaster.agents import AgentRegistry
from loremaster.messages import MessageLedger
from loremaster.store import surreal_schema

from loremaster import principals

_MESSAGE_TABLE = surreal_schema.MESSAGE_TABLE
_AGENT_TABLE = "agent"
_PRINCIPAL_TABLE = "principal"


def _principals_source() -> str:
    """The whole ``principals.py`` source — for the ONE-IMPLEMENTATION structural (AST) route pins."""
    return Path(principals.__file__).read_text(encoding="utf-8")


def _bare(value: Any) -> str:
    text = str(getattr(value, "id", value))
    return text.split(":", 1)[-1] if ":" in text else text


class _Ref:
    """A minimal ``AgentRefLike`` (id + name) for ``MessageLedger.send`` (mirrors the message-ledger
    tests' ref shape — send resolves recipients by id against the agent table)."""

    def __init__(self, id: str, name: str) -> None:  # noqa: A002 - the Protocol's field name
        self.id = id
        self.name = name


# --------------------------------------------------------------------------- #
# Fixtures — DIRTY worlds (the test-env-is-a-fiction law: a migration is tested on a POPULATED store,
# never a virgin one). The agent world seeds NONE-owner agents; the message world seeds a real
# NONE-owner message via MessageLedger.send over MIGRATED agents.
# --------------------------------------------------------------------------- #


@pytest_asyncio.fixture()
async def agent_world() -> Any:
    """A store with the ``agent`` table + a PrincipalStore/KeepStore. NO principal is created here —
    each test creates the principal shape (single operator / multi-principal ambiguity) it needs, so
    the ambiguity-refuse fate and the backfill fate are forced by DIFFERENT fixtures (not one shared
    default that hides a branch). Reaped on exit."""
    env = make_env(database=unique_database(), dim=8)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    registry = AgentRegistry(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await registry.ensure_ready()
    try:
        yield principal_store, keep_store, registry, connection, env
    finally:
        await registry.close()
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


@pytest_asyncio.fixture()
async def message_world() -> Any:
    """A store with agent + message DDL + the message GOVERNED OVERLAY (``governed_overlay_ddl`` —
    decoupled from the §4.F emitter, so this leg is testable before §4.F wires it; on a GREEN §4.F
    build the emitter emits the same, an idempotent double-apply), a single operator principal, two
    MIGRATED agents (sender + recipient, ``owner_principal`` set), and ONE real NONE-owner message
    sent between them (``send`` does not stamp owner/scope at HEAD → a legacy message). Reaped."""
    env = make_env(database=unique_database(), dim=8)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
    await apply_ddl(connection, surreal_schema.generate_message_ddl(), url=env.url)
    await apply_ddl(connection, governed_overlay_ddl(_MESSAGE_TABLE), url=env.url)
    await principal_store.create(email="operator@example.com", role="member")
    operator = (await principal_store.list())[0]
    registry = AgentRegistry(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    ledger = MessageLedger(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    try:
        # MIGRATED agents: owner_principal set at register (so the message leg does NOT refuse on the
        # §2.6 agent-first precondition — this fixture forces the BACKFILL fate).
        sender = (
            await registry.register(
                "sender_agent", session="s1", role="builder", owner_principal_id=_bare(operator.id)
            )
        ).agent
        recipient = (
            await registry.register(
                "recipient_agent", session="s1", role="builder", owner_principal_id=_bare(operator.id)
            )
        ).agent
        result = await ledger.send(
            sender=_Ref(sender.id, sender.name),
            session="s1",
            body="a legacy message from before the cutover",
            grade="signal",
            recipients=[_Ref(recipient.id, recipient.name)],
        )
        yield principal_store, keep_store, registry, ledger, connection, env, result.message.id, sender
    finally:
        await ledger.close()
        await registry.close()
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


@pytest_asyncio.fixture()
async def ambiguous_message_world() -> Any:
    """Like ``message_world`` but with TWO principals (both members, ZERO admins) so THE operator is
    AMBIGUOUS. The two agents (sender + recipient) are MIGRATED (owned by the FIRST principal), so the
    §2.6 agent-first precondition is SATISFIED — a message migrate here refuses on the §2.1 OPERATOR
    AMBIGUITY, never on agent-first. One real NONE-owner legacy message (``send`` does not stamp owner
    at HEAD). This is the MP-3 message-leg ambiguity fixture the adversary named. Reaped."""
    env = make_env(database=unique_database(), dim=8)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
    await apply_ddl(connection, surreal_schema.generate_message_ddl(), url=env.url)
    await apply_ddl(connection, governed_overlay_ddl(_MESSAGE_TABLE), url=env.url)
    # TWO principals, ZERO admins → resolve_operator_principal is AMBIGUOUS (§2.1).
    await principal_store.create(email="operator@example.com", role="member")
    await principal_store.create(email="second@example.com", role="member")
    operator = (await principal_store.list())[0]
    registry = AgentRegistry(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    ledger = MessageLedger(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    try:
        # MIGRATED agents (owner_principal set) → agent-first is SATISFIED, so the ONLY refuse a
        # correct build can raise here is the operator AMBIGUITY (never agent-first).
        sender = (
            await registry.register(
                "sender_agent", session="s1", role="builder", owner_principal_id=_bare(operator.id)
            )
        ).agent
        recipient = (
            await registry.register(
                "recipient_agent", session="s1", role="builder", owner_principal_id=_bare(operator.id)
            )
        ).agent
        result = await ledger.send(
            sender=_Ref(sender.id, sender.name),
            session="s1",
            body="a legacy message from before the cutover",
            grade="signal",
            recipients=[_Ref(recipient.id, recipient.name)],
        )
        yield principal_store, keep_store, registry, ledger, connection, env, result.message.id, sender
    finally:
        await ledger.close()
        await registry.close()
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


async def _migrate(connection: Any, env: Any, *, table: str, keep_store: Any, principal_store: Any) -> Any:
    """Drive ``migrate_governed`` for ``table`` through a StoreHandle over the fixture connection (R4:
    the verb borrows the target store's driver, never a raw connection)."""
    handle, _calls = store_handle(connection, url=env.url)
    return await principals.migrate_governed(
        table=table, store=handle, keep_store=keep_store, principal_store=principal_store
    )


# =========================================================================== #
# resolve_operator_principal — LIFTED to principals, called by ALL THREE migrate legs (ONE
# IMPLEMENTATION, design §4.C / §6). The inline block currently in _migrate_memory_scope moves here.
# =========================================================================== #


class TestResolveOperatorPrincipalIsLifted:
    """§4.C / §6 — the operator-principal resolution (single principal, or single admin, else REFUSE)
    is ONE ``resolve_operator_principal(principal_store)`` all three migrate legs call, NOT cloned per
    leg (the #102 clone-chain class: a fix to the ambiguity rule must reach all three)."""

    def test_resolve_operator_principal_is_lifted_to_principals(self) -> None:
        """⚠ RED at HEAD — ``principals.resolve_operator_principal`` does not exist (the resolution is
        an inline block in ``_migrate_memory_scope``). REDDENS the un-lifted HEAD."""
        assert hasattr(principals, "resolve_operator_principal"), (
            "principals.resolve_operator_principal is not lifted — the operator-principal resolution is "
            "still an inline block in _migrate_memory_scope (design §4.C / §6 ONE IMPLEMENTATION)"
        )

    def test_all_three_migrate_legs_route_through_resolve_operator_principal(self) -> None:
        """⚠ RED at HEAD — each migrate leg CALLS ``resolve_operator_principal`` (structural/AST, the
        L2a ``function_calls_named`` idiom). At HEAD ``_migrate_memory_scope`` has the inline block (no
        call), and ``_migrate_agent_owner`` / ``_migrate_message_owner`` do not exist → each reds. This
        is the ONE-IMPLEMENTATION proof by ROUTING: a leg that hand-rolls its own principal-count block
        (a clone) does not call the shared helper and reddens (ROUTING-IS-NOT-SHARING — the structural
        twin of the schema route-through-emitter pins; a value-mutation proof is available but the AST
        call-check is the established L2a idiom and is unambiguously RED at HEAD)."""
        source = _principals_source()
        for leg in ("_migrate_memory_scope", "_migrate_agent_owner", "_migrate_message_owner"):
            assert function_calls_named(source, leg, "resolve_operator_principal"), (
                f"{leg} does not call resolve_operator_principal — it either does not exist yet OR "
                f"hand-rolls its own operator-principal resolution (a #102 clone, not the ONE lifted "
                f"helper; design §4.C / §6)"
            )

    async def test_the_operator_resolution_is_shared_by_mutation(
        self, agent_world: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD (adversary MP-3 — the routing-not-sharing KILLER for the AGENT leg). The
        structural ``function_calls_named`` route pin above is satisfied by a leg that CALLS
        ``resolve_operator_principal`` yet hand-rolls its OWN operator decision underneath
        (ROUTING-IS-NOT-SHARING, #102/#120). This is the VALUE-mutation that closes that door: perturb
        the SHARED ``principals.resolve_operator_principal`` and watch the AGENT leg's stamped owner
        move with it. POSITIVE CONTROL: an UNPATCHED migrate stamps the resolved operator (the
        resolution reaches the stamp at all); then, with the seam patched to a DISTINCT fixed principal
        P*, a FRESH NONE-owner agent is stamped to P* — a private copy would ignore the patch and stamp
        the real operator. RED at HEAD: the 63a stub refuses (no stamp), so neither leg's owner lands.

        SCOPING (SAID — REPORT-reviser-63b-ii-a.md §Flags): the adversary sketched 'all THREE legs'
        resolution changes'. The memory leg's routing is the EXTRACTION source
        (``_migrate_memory_scope`` becomes a caller — the structural pin covers it); the MESSAGE leg's
        value-routing is ``test_message_migrate_refuses_on_multi_principal_ambiguity`` (its ambiguity
        refuse comes from THIS shared seam). So each leg's routing is value-proven; a single-call
        'all three' shape needs a combined memory+agent+message world the split fixtures do not
        provide, and the discrimination does not require it.

        ⚠ ASSUMPTION (flagged, report §Flags): ``resolve_operator_principal`` is ASYNC — the extraction
        source ``_migrate_memory_scope`` ``await``s ``principal_store.list()`` inside the block it lifts
        — and returns a PRINCIPAL whose ``.id`` is read to stamp the owner (a ``record<principal>`` link,
        store-ref §2, which does not validate existence, so P* need not be provisioned). A sync /
        other-shape build reddens this with a legible ``await``/attribute signal — a builder-visible
        correction, never a silent trap."""
        principal_store, keep_store, registry, connection, env = agent_world
        await principal_store.create(email="operator@example.com", role="member")
        operator = (await principal_store.list())[0]
        # POSITIVE CONTROL — unpatched: the single operator resolves and the stamp lands.
        ag_control = (await registry.register("ag_control", session="s1", role="builder")).agent
        control = await _migrate(
            connection, env, table=_AGENT_TABLE, keep_store=keep_store, principal_store=principal_store
        )
        assert not control.refused and control.backfilled >= 1, (
            f"positive control: an unpatched agent migrate must stamp the resolved operator, got {control!r}"
        )
        # THE MUTATION — a DISTINCT fixed principal P* returned by the SHARED seam.
        p_star = SimpleNamespace(
            id=f"{_PRINCIPAL_TABLE}:pstar_mutation", email="pstar-mutation@example.com", role="member"
        )

        async def _fixed_operator(_principal_store: Any) -> Any:
            return p_star

        monkeypatch.setattr(principals, "resolve_operator_principal", _fixed_operator, raising=False)
        ag_mutated = (await registry.register("ag_mutated", session="s1", role="builder")).agent
        mutated = await _migrate(
            connection, env, table=_AGENT_TABLE, keep_store=keep_store, principal_store=principal_store
        )
        assert not mutated.refused and mutated.backfilled >= 1, (
            f"the patched agent migrate must still backfill the fresh NONE-owner agent, got {mutated!r}"
        )
        rows = {
            _bare(row["id"]): str(row["owner_principal"])
            for row in await run(
                connection,
                f"SELECT id, owner_principal FROM {_AGENT_TABLE} "
                f"WHERE id IN [type::record('{_AGENT_TABLE}', $c), type::record('{_AGENT_TABLE}', $m)]",
                {"c": _bare(ag_control.id), "m": _bare(ag_mutated.id)},
            )
        }
        assert rows[_bare(ag_mutated.id)] == f"{_PRINCIPAL_TABLE}:pstar_mutation", (
            f"the agent migrated UNDER THE PATCH was NOT stamped to the perturbed operator P* — the "
            f"agent leg hand-rolls its own operator resolution instead of routing through the SHARED "
            f"resolve_operator_principal (ROUTING-IS-NOT-SHARING, #102/#120; adversary MP-3): {rows}"
        )
        assert rows[_bare(ag_control.id)] == f"{_PRINCIPAL_TABLE}:{_bare(operator.id)}", (
            f"the control agent (migrated unpatched) must stay stamped to the real operator, unchanged "
            f"by the later patched run (idempotent — the migrate touches only NONE-owner agents): {rows}"
        )


# =========================================================================== #
# _migrate_agent_owner (§4.C / §2.1) — stamps owner_principal on NONE-owner agents → THE operator,
# REFUSES on multi-principal ambiguity.
# =========================================================================== #


class TestMigrateAgentOwner:
    """§4.C — ``migrate_governed(table="agent")`` backfills ``owner_principal`` on every NONE-owner
    agent to THE operator principal, and REFUSES (never guesses) on multi-principal ambiguity."""

    async def test_agent_migrate_backfills_only_none_owner_agents_to_the_operator(
        self, agent_world: Any
    ) -> None:
        """⚠ RED at HEAD (the stub refuses *"does not support table 'agent'"*). With ONE operator
        principal: a NONE-owner agent is stamped ``owner_principal = principal:<operator>``, while an
        ALREADY-OWNED agent is left UNTOUCHED (∀ fate forced by a MIX — a build that re-stamps owned
        agents reddens). Idempotent: a second run backfills 0. REDDENS the stub (no backfill)."""
        principal_store, keep_store, registry, connection, env = agent_world
        await principal_store.create(email="operator@example.com", role="member")
        operator = (await principal_store.list())[0]
        # a NONE-owner agent (register with no owner) + a pre-owned agent (owner set at register).
        none_owner = (await registry.register("ag_none", session="s1", role="builder")).agent
        pre_owned = (
            await registry.register(
                "ag_owned", session="s1", role="builder", owner_principal_id=_bare(operator.id)
            )
        ).agent
        result = await _migrate(
            connection, env, table=_AGENT_TABLE, keep_store=keep_store, principal_store=principal_store
        )
        assert not result.refused and result.backfilled >= 1, (
            f"migrate agent must backfill the NONE-owner agent to the operator, got {result!r}"
        )
        rows = {
            _bare(row["id"]): row["owner_principal"]
            for row in await run(
                connection,
                f"SELECT id, owner_principal FROM {_AGENT_TABLE} "
                f"WHERE id IN [type::record('{_AGENT_TABLE}', $a), type::record('{_AGENT_TABLE}', $b)]",
                {"a": _bare(none_owner.id), "b": _bare(pre_owned.id)},
            )
        }
        assert str(rows[_bare(none_owner.id)]) == f"{_PRINCIPAL_TABLE}:{_bare(operator.id)}", (
            f"the NONE-owner agent was not stamped to the operator principal: {rows}"
        )
        assert str(rows[_bare(pre_owned.id)]) == f"{_PRINCIPAL_TABLE}:{_bare(operator.id)}", (
            "the pre-owned agent's owner_principal changed — the migrate must touch ONLY NONE-owner "
            f"agents (∀ NONE-owner, never a re-stamp): {rows}"
        )
        second = await _migrate(
            connection, env, table=_AGENT_TABLE, keep_store=keep_store, principal_store=principal_store
        )
        assert not second.refused and second.backfilled == 0, (
            f"the second agent-migrate run must backfill 0 (idempotent), got {second!r}"
        )

    async def test_agent_migrate_refuses_on_multi_principal_ambiguity(self, agent_world: Any) -> None:
        """⚠ RED at HEAD — with TWO principals and ZERO admins the operator is AMBIGUOUS, so the verb
        REFUSES (``refused=True``) with a reason NAMING the multi-principal ambiguity, and stamps
        NOTHING. RED at HEAD for the RIGHT reason: the 63a stub refuses with *"does not support table
        'agent'"*, which does NOT mention principals/ambiguity → the reason assert reddens (this
        discriminates the real §2.1 precondition check from the stub refusal). No agent rows are needed
        — the refusal fires in resolve_operator_principal, before any agent is touched."""
        principal_store, keep_store, registry, connection, env = agent_world
        await principal_store.create(email="one@example.com", role="member")
        await principal_store.create(email="two@example.com", role="member")
        result = await _migrate(
            connection, env, table=_AGENT_TABLE, keep_store=keep_store, principal_store=principal_store
        )
        assert result.refused and result.backfilled == 0, (
            f"migrate agent must REFUSE on multi-principal ambiguity (§2.1), got {result!r}"
        )
        reason = (result.reason or "").lower()
        assert "principal" in reason and ("operator" in reason or "ambigu" in reason or "single" in reason), (
            "the agent-migrate refusal must NAME the multi-principal ambiguity (§2.1 — provision a "
            f"single operator/admin), not the 63a stub 'does not support' reason. got: {result.reason!r}"
        )

    def test_migrate_agent_owner_wraps_its_write_in_governed_exempt(self) -> None:
        """⚠ RED at HEAD (``_migrate_agent_owner`` does not exist) — the agent backfill is a governed
        WRITE, so it attributes via the NAMED ``governed_exempt`` frame (§4.C: both legs are exempt
        frames; §1.4). Structural (L2a ``function_calls_named``). ⚠ FLAG (report §Decisions): ``agent``
        is NOT a governed POPULATION until 63c (``_agent_statements`` does not call
        ``_governed_field_specs`` — the packet-62 ``owner_principal`` is a DIRECT field), so F5 does not
        OBSERVE this write in ii-a; this pins the exempt WRAPPER (forward-looking, 63c live-classifies
        it), never a live four-leg classification. REDDENS a build that omits the exempt wrapper."""
        assert function_calls_named(_principals_source(), "_migrate_agent_owner", "governed_exempt"), (
            "_migrate_agent_owner does not wrap its governed write in governed_exempt (§4.C exempt "
            "frame; §1.4) — it either does not exist yet OR writes owner_principal unattributed"
        )


# =========================================================================== #
# _migrate_message_owner (§4.C / §2.6) — stamps owner_agent=sender, owner_principal=sender.owner_
# principal, scope=keep:<project>; REFUSES before the agent table is migrated (§2.6 checked ORDER).
# =========================================================================== #


class TestMigrateMessageOwner:
    """§4.C / §2.6 — ``migrate_governed(table="message")`` backfills a legacy message's owner from its
    SENDER and its scope to the project keep, and REFUSES if any ``agent.owner_principal IS NONE``."""

    async def test_message_migrate_backfills_owner_from_sender_and_scope_to_project_keep(
        self, message_world: Any
    ) -> None:
        """⚠ RED at HEAD (the stub refuses *"…lands in packet 63b"*) — THE DISCRIMINATING PIN. With the
        agents MIGRATED (owner_principal set), the legacy message is stamped: ``owner_agent`` = the
        sender, ``owner_principal`` = the sender's owner_principal, ``scope`` = ``keep:<project>`` (a
        real minted project keep). Idempotent (a second run backfills 0). REDDENS the stub refusal."""
        principal_store, keep_store, _registry, _ledger, connection, env, message_id, sender = message_world
        before = await run(
            connection,
            f"SELECT owner_agent, owner_principal, scope FROM type::record('{_MESSAGE_TABLE}', $m)",
            {"m": message_id},
        )
        assert before and before[0]["owner_principal"] is None and before[0]["scope"] is None, (
            f"precondition: the sent message starts NONE-owner/NONE-scope (a legacy row), got {before!r}"
        )
        result = await _migrate(
            connection, env, table=_MESSAGE_TABLE, keep_store=keep_store, principal_store=principal_store
        )
        assert not result.refused and result.backfilled >= 1, (
            f"migrate message must backfill the legacy message when agents are migrated, got {result!r}"
        )
        row = (
            await run(
                connection,
                f"SELECT owner_agent, owner_principal, scope FROM type::record('{_MESSAGE_TABLE}', $m)",
                {"m": message_id},
            )
        )[0]
        assert str(row["owner_agent"]) == f"{_AGENT_TABLE}:{_bare(sender.id)}", (
            f"message.owner_agent must be the SENDER (§4.C), got {row['owner_agent']!r}"
        )
        # ⚠ MP-1 FIX (reviser-63b-ii-a, adversary REPORT-adversary-63b-ii-a.md §MP-1 BLOCKER / C-DEF).
        # The old line asserted ``str(sender.owner_principal)`` — but ``agents.Agent`` is
        # ConfigDict(extra="forbid") and has NO ``owner_principal`` field (its fields end at
        # ``declared_cadence``), so on ANY correct build the migrate SUCCEEDS, the row IS stamped, and
        # the test then raises ``AttributeError: 'Agent' object has no attribute 'owner_principal'`` —
        # UNSATISFIABLE (RED at HEAD only because the stub refuses before reaching the line). Read the
        # SENDER AGENT's stored ``owner_principal`` FROM THE STORE and compare (the adversary's door-build:
        # the fixture registered the sender with ``owner_principal_id=_bare(operator.id)``).
        sender_owner_rows = await run(
            connection,
            f"SELECT owner_principal FROM type::record('{_AGENT_TABLE}', $s)",
            {"s": _bare(sender.id)},
        )
        assert sender_owner_rows and sender_owner_rows[0]["owner_principal"] is not None, (
            "precondition: the sender agent must carry a stored owner_principal (the message_world "
            f"fixture registered it with owner_principal_id set), got {sender_owner_rows!r}"
        )
        sender_owner_principal = sender_owner_rows[0]["owner_principal"]
        assert str(row["owner_principal"]) == str(sender_owner_principal), (
            f"message.owner_principal must be the SENDER AGENT's stored owner_principal (§4.C), read "
            f"from the store (agents.Agent carries no owner_principal field — MP-1 C-DEF fix): got "
            f"{row['owner_principal']!r} vs sender agent's stored {sender_owner_principal!r}"
        )
        assert isinstance(row["scope"], str) and row["scope"].startswith("keep:"), (
            f"message.scope must be backfilled to keep:<project> (§4.C), got {row['scope']!r}"
        )
        second = await _migrate(
            connection, env, table=_MESSAGE_TABLE, keep_store=keep_store, principal_store=principal_store
        )
        assert not second.refused and second.backfilled == 0, (
            f"the second message-migrate run must backfill 0 (idempotent), got {second!r}"
        )

    async def test_message_migrate_refuses_before_the_agent_table_is_migrated(
        self, agent_world: Any
    ) -> None:
        """§2.6 the checked agent-first ORDER — a CONTROL paired with the backfill pin above (which
        carries the RED). With a NONE-owner agent present, ``migrate_governed(table="message")`` REFUSES
        and stamps NOTHING (a message's owner_principal reads sender.owner_principal, NONE for an
        un-migrated agent → member-invisible; the migrate refuses rather than half-widen). GREEN at HEAD
        (the 63a stub also refuses) AND on the correct build (the real §2.6 precondition check). The
        DISCRIMINATION between stub and real behaviour is the backfill-when-clean RED pin above; this
        control asserts the refusal writes nothing (which the stub also satisfies) so the §2.6 order is
        pinned by the PAIR."""
        principal_store, keep_store, registry, connection, env = agent_world
        await principal_store.create(email="operator@example.com", role="member")
        # a NONE-owner agent → the agent table is NOT migrated → message migrate must refuse.
        await registry.register("ag_unowned", session="s1", role="builder")
        # apply the message overlay so the refuse path has a message table to (not) touch.
        await apply_ddl(connection, surreal_schema.generate_message_ddl(), url=env.url)
        await apply_ddl(connection, governed_overlay_ddl(_MESSAGE_TABLE), url=env.url)
        result = await _migrate(
            connection, env, table=_MESSAGE_TABLE, keep_store=keep_store, principal_store=principal_store
        )
        assert result.refused and result.backfilled == 0, (
            f"migrate message must REFUSE before the agent table is migrated (§2.6), got {result!r}"
        )
        assert result.reason and "agent" in result.reason.lower(), (
            f"the message-migrate refusal must name the agent-first precondition, got {result.reason!r}"
        )

    async def test_message_migrate_refuses_before_the_agent_table_is_migrated_with_two_none_owner_agents(
        self, agent_world: Any
    ) -> None:
        """§2.6 — R5-ADJACENT (adversary residual R5): the refuse pin above uses ONE NONE-owner agent,
        so a build that refuses only when the count is EXACTLY 1 would pass it. This HARDENS the count
        to >1 — with TWO NONE-owner agents present, ``migrate_governed(table='message')`` must STILL
        REFUSE (refused=True, 0 backfilled) naming the agent-first precondition. GREEN at HEAD (the 63a
        stub refuses) AND on the correct build (a genuine count>0 check); REDDENS a build that refuses
        only at count==1 (the mild quantifier softness the adversary flagged)."""
        principal_store, keep_store, registry, connection, env = agent_world
        await principal_store.create(email="operator@example.com", role="member")
        await registry.register("ag_unowned_one", session="s1", role="builder")
        await registry.register("ag_unowned_two", session="s1", role="builder")
        await apply_ddl(connection, surreal_schema.generate_message_ddl(), url=env.url)
        await apply_ddl(connection, governed_overlay_ddl(_MESSAGE_TABLE), url=env.url)
        result = await _migrate(
            connection, env, table=_MESSAGE_TABLE, keep_store=keep_store, principal_store=principal_store
        )
        assert result.refused and result.backfilled == 0, (
            f"migrate message must REFUSE with TWO NONE-owner agents present (§2.6 agent-first is "
            f"count>0, never count==1), got {result!r}"
        )
        assert result.reason and "agent" in result.reason.lower(), (
            f"the refusal must name the agent-first precondition, got {result.reason!r}"
        )

    async def test_message_migrate_refuses_on_multi_principal_ambiguity(
        self, ambiguous_message_world: Any
    ) -> None:
        """⚠ RED at HEAD (adversary MP-3 quantifier gap — the MESSAGE leg's operator-ambiguity refuse
        is UNPINNED). The agent leg (``test_agent_migrate_refuses_on_multi_principal_ambiguity``) and
        the memory leg (63a) each pin the multi-principal ambiguity refuse; the message leg pinned only
        agent-first. With the agents MIGRATED (agent-first SATISFIED) and TWO principals / ZERO admins,
        ``migrate_governed(table='message')`` must REFUSE on the §2.1 OPERATOR AMBIGUITY — the message
        leg consults the SHARED ``resolve_operator_principal`` (for the project keep keeper, exactly as
        the memory leg does; the structural route pin already REQUIRES the call), whose ambiguity is a
        REFUSAL. The reason names the PRINCIPAL/OPERATOR ambiguity, NOT agent-first — so a message leg
        that SKIPS or hand-rolls the ambiguity decision (routing-not-sharing) reddens. RED at HEAD (the
        63a stub refuses with a DIFFERENT reason — 'lands in packet 63b' — naming neither operator nor
        ambiguity). ⚠ This pins a CONSEQUENCE of the existing structural route pin (the message leg
        calls resolve_operator_principal); flagged in REPORT-reviser-63b-ii-a.md §Flags as depending on
        the message leg resolving the project keep through that shared seam."""
        principal_store, keep_store, _registry, _ledger, connection, env, _message_id, _sender = (
            ambiguous_message_world
        )
        result = await _migrate(
            connection, env, table=_MESSAGE_TABLE, keep_store=keep_store, principal_store=principal_store
        )
        assert result.refused and result.backfilled == 0, (
            f"migrate message must REFUSE on multi-principal ambiguity when agents ARE migrated (§2.1 — "
            f"the shared resolve_operator_principal cannot pick THE operator), got {result!r}"
        )
        reason = (result.reason or "").lower()
        assert "principal" in reason and ("operator" in reason or "ambigu" in reason or "single" in reason), (
            f"the message-migrate refusal must NAME the operator ambiguity (§2.1), not agent-first (the "
            f"agents ARE migrated) and not the 63a stub 'lands in packet 63b'. got: {result.reason!r}"
        )

    def test_migrate_message_owner_wraps_its_write_in_governed_exempt(self) -> None:
        """⚠ RED at HEAD (``_migrate_message_owner`` does not exist) — the message backfill is a
        governed WRITE of the ``message`` population (a governed table once §4.F lands), so it
        attributes via the NAMED ``governed_exempt`` frame (§4.C / §1.4). Structural (L2a). The LIVE
        four-leg F5 classification of this frame is pinned in ``test_message_enforcement_63b_ii_a.py``
        (message IS a governed population). REDDENS a build that omits the exempt wrapper."""
        assert function_calls_named(_principals_source(), "_migrate_message_owner", "governed_exempt"), (
            "_migrate_message_owner does not wrap its governed write in governed_exempt (§4.C exempt "
            "frame; §1.4) — it either does not exist yet OR writes the message owner/scope unattributed"
        )
