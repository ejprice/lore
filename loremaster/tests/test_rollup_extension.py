"""Contract — ``lore_tasks action=rollup`` gains messages / fleet / skew sections
(packet 05a-iii, scope B — the C0 rollup extension).

RED contract (author: contract-05aiii). The current ``AppContext._rollup`` composes
THREE legs (tasks transitioned / findings filed / reports registered) + a ``next
cursor``. This packet ADDS three sections — messages-activity, fleet-health, and
brief-ack-skew (design: ``one-of-claude-codes-nifty-garden.md`` §"PKT-06 rollup
extension"; ``comms-subsystem.md`` footer note). The extension is ADDITIVE: the
existing legs and cursor semantics are unchanged.

Pins:
- **B1 messages section** — after a message is sent, rollup renders a
  messages-activity section reflecting it. RED (no such section today).
- **B2 fleet section** — with registered agents, rollup renders a fleet-health
  section. RED.
- **B3 skew section** — with a published brief and an agent behind the head, rollup
  renders a brief-ack-skew section. RED.
- **B4 cursor semantics** — the messages section is CURSOR-BOUNDED like the existing
  legs: a message created BEFORE ``since`` does not appear; one AFTER does. RED +
  discriminating (a build that ignores ``since`` for messages shows the pre-cursor
  message).

⚠ FLAG (satisfiability): the exact CONTENT shape of the three new sections (rows vs
bare counts, section headers) is builder-adjustable — these pins key on the section
being PRESENT and on a seeded item's THREAD/name appearing, matching the existing
legs' content-row pattern (``- {subject} (id …, owner …)``). If a section renders
counts only, B4's thread sentinel must be reconciled. See REPORT §Escalations.

Tests hit spike-surreal ``ws://127.0.0.1:18000`` ONLY; ``:18500`` is NEVER touched.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.agents import Agent, AgentRegistry
from loremaster.briefs import BriefLedger
from loremaster.findings import FindingLedger
from loremaster.messages import MessageLedger
from loremaster.server import AppContext
from loremaster.tasks import TaskLedger

_SESSION = "rollup-wave"


class _RollupCtx:
    """Live harness for ``AppContext._rollup``: the two EXISTING-leg ledgers plus the
    three the extension reads, on ONE throwaway database."""

    def __init__(self, database: str) -> None:
        self._env = make_env(database=database, dim=PRODUCTION_DIM)
        coord: dict[str, Any] = {
            "url": self._env.url,
            "namespace": self._env.namespace,
            "database": self._env.database,
            "user": self._env.user,
            "password": self._env.password,
        }
        self.task_ledger = TaskLedger(**coord)
        self.finding_ledger = FindingLedger(**coord)
        self.message_ledger = MessageLedger(**coord)
        self.agent_registry = AgentRegistry(**coord)
        self.brief_ledger = BriefLedger(**coord)
        self.config = SimpleNamespace(comms=SimpleNamespace(stale_heartbeat_s=600, fleet_limit=20))

    async def start(self) -> None:
        setup = await connect_admin(self._env)
        await setup.close()
        for ledger in (
            self.task_ledger,
            self.finding_ledger,
            self.message_ledger,
            self.agent_registry,
            self.brief_ledger,
        ):
            await ledger.ensure_ready()

    async def stop(self) -> None:
        for ledger in (
            self.task_ledger,
            self.finding_ledger,
            self.message_ledger,
            self.agent_registry,
            self.brief_ledger,
        ):
            await ledger.close()
        await drop_database(self._env)

    async def register(self, name: str) -> Agent:
        await self.agent_registry.register(name, session=_SESSION, role="builder")
        agent = await self.agent_registry.get_agent(name, session=_SESSION)
        if hasattr(self.message_ledger, "register_agent"):
            self.message_ledger.register_agent(agent_id=agent.id, name=agent.name)
        return agent

    async def rollup(self, *, since: str | None = None, limit: int | None = None) -> str:
        return str(await AppContext._rollup(cast(AppContext, self), since=since, limit=limit))


@pytest_asyncio.fixture()
async def rctx() -> AsyncIterator[_RollupCtx]:
    ctx = _RollupCtx(unique_database())
    await ctx.start()
    try:
        yield ctx
    finally:
        await ctx.stop()


class TestRollupMessagesSection:
    async def test_rollup_renders_a_messages_activity_section(self, rctx: _RollupCtx) -> None:
        lead = await rctx.register("lead")
        worker = await rctx.register("worker")
        await rctx.message_ledger.send(
            sender=lead,
            session=_SESSION,
            body="a signal about the work",
            grade="signal",
            recipients=[worker],
            thread="rollup-thread-alpha",
        )
        rendered = await rctx.rollup()
        assert "message" in rendered.lower(), (
            f"rollup must gain a messages-activity section (C0 extension); render: {rendered!r}"
        )

    async def test_messages_section_is_cursor_bounded(self, rctx: _RollupCtx) -> None:
        lead = await rctx.register("lead")
        worker = await rctx.register("worker")
        await rctx.message_ledger.send(
            sender=lead,
            session=_SESSION,
            body="pre-cursor traffic",
            grade="signal",
            recipients=[worker],
            thread="rollup-thread-sentinel",
        )
        # A cursor strictly AFTER the message: the messages section must EXCLUDE it,
        # exactly as the task/finding legs exclude pre-``since`` rows.
        after = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        excluded = await rctx.rollup(since=after)
        included = await rctx.rollup(since=None)
        assert "rollup-thread-sentinel" not in excluded, (
            "a message created BEFORE `since` must not appear in the messages section "
            f"(cursor semantics); render: {excluded!r}"
        )
        assert "rollup-thread-sentinel" in included, (
            "a message created AFTER `since=epoch` MUST appear in the messages section; "
            f"render: {included!r}"
        )


class TestRollupFleetSection:
    async def test_rollup_renders_a_fleet_health_section(self, rctx: _RollupCtx) -> None:
        await rctx.register("alpha")
        await rctx.register("beta")
        rendered = await rctx.rollup()
        assert "fleet" in rendered.lower(), (
            f"rollup must gain a fleet-health section (C0 extension); render: {rendered!r}"
        )


class TestRollupSkewSection:
    async def test_rollup_renders_a_brief_ack_skew_section(self, rctx: _RollupCtx) -> None:
        # Publish a project brief, then register an agent that never acks it — the
        # maximally-behind (unbriefed) case the skew section exists to surface.
        await rctx.brief_ledger.publish("project", "the standing brief body", created_by="lead")
        await rctx.register("behind")
        rendered = await rctx.rollup()
        assert "skew" in rendered.lower(), (
            f"rollup must gain a brief-ack-skew section (C0 extension); render: {rendered!r}"
        )
