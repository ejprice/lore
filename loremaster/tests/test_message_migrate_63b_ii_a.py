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
from typing import Any

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
        assert str(row["owner_principal"]) == str(sender.owner_principal), (
            f"message.owner_principal must be the sender's owner_principal (§4.C), got "
            f"{row['owner_principal']!r} vs sender {sender.owner_principal!r}"
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
