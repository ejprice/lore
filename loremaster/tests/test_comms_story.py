"""Contract — ``story``: task-anchored lineage in ONE call (packet 05a-iii, scope A + E).

RED contract (author: contract-05aiii). ``story`` reconstructs a task's arc
(created → claim → messages → transitions → report_path) as a READ composition over
EXISTING edges — it reshapes no drain SELECT. Design: ``comms-subsystem.md`` §story
row + ``one-of-claude-codes-nifty-garden.md`` §tool-table (``story`` row).

Pins (scope A):
- **A2 reconstruction** — story(T) renders the task's subject, creator, owner, its
  messages, and its report_path/summary. RED (the stub renders only a header).
- **A3 question marker** — story marks a QUESTION message STRUCTURALLY (from
  ``message.question``), distinct from an ordinary signal — a legibility gain (the
  lead reads intent from TYPED state, not body prose), NOT an obedience fix.
  Parameter-value non-monoculture: a question-bearing task renders the marker, a
  signal-only task does not. RED. ⚠ The marker GLYPH is a contract choice (the word
  "question"); the exact spelling is builder-adjustable — flagged in the report.
- **A4 Leg-1 scope diff** — the render NAMES its SET (this task's arc) and OMITS
  other tasks' traffic: a message on a DIFFERENT task never appears in story(T).
- **A5 containment (ONE IMPLEMENTATION)** — every stored free-text field story
  renders routes through the shipped ``render_attributed``/``render_fenced`` seam,
  NOT a second hand-rolled containment. A hostile message body (newlines + an
  output-format-shaped forgery line + backtick runs) round-trips VERBATIM inside a
  fence strictly wider than any embedded backtick run, with no forged row escaping
  it. The P8d / 03b rendered-free-text law; single-line-only fixtures are the
  documented way these defects stay green, so this fixture is multi-line + hostile.

Scope E (#195): the OBEDIENCE measurement — whether an agent OBEYS an instruction
inside a body — is DECLINED here and handed to 06's drill (Fable §Q3, operator-
ratified). A render can make body content LEGIBLE-as-quoted; it cannot make an LLM
INERT to an instruction it reads. 05a-iii's duty is CONTAINMENT REUSE (A5) +
structural legibility (A3), which measure legibility, NOT inertness. This is stated
out loud here and in the report so the decline is EXPLICIT, never a silent third
deferral. See ``test_195_obedience_is_declined_to_06_drill``.

Tests hit spike-surreal ``ws://127.0.0.1:18000`` ONLY; ``:18500`` is NEVER touched.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
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
from loremaster.messages import MessageLedger
from loremaster.sanitise import max_backtick_run
from loremaster.server import AppContext
from loremaster.tasks import TaskLedger
from render_injection_scaffold import _ROW_FORGE_PAYLOAD

_SESSION = "story-wave"
# Multi-line + row-forge + a fence-shaped backtick run: the hostile-body law.
_HOSTILE_BODY = f"line one\nline two ```` embedded```\n{_ROW_FORGE_PAYLOAD}"


class _StoryCtx:
    """Live harness for ``_comms_story``: real task / message / agent / brief ledgers
    on ONE throwaway database (the story handler composes over all of them)."""

    def __init__(self, database: str) -> None:
        self._env = make_env(database=database, dim=PRODUCTION_DIM)
        coord: dict[str, Any] = {
            "url": self._env.url,
            "namespace": self._env.namespace,
            "database": self._env.database,
            "user": self._env.user,
            "password": self._env.password,
        }
        self.agent_registry = AgentRegistry(**coord)
        self.message_ledger = MessageLedger(**coord)
        self.task_ledger = TaskLedger(**coord)
        self.brief_ledger = BriefLedger(**coord)
        self.config = SimpleNamespace(comms=SimpleNamespace(stale_heartbeat_s=600, fleet_limit=20))

    async def start(self) -> None:
        setup = await connect_admin(self._env)
        await setup.close()
        await self.agent_registry.ensure_ready()
        await self.message_ledger.ensure_ready()
        await self.task_ledger.ensure_ready()
        await self.brief_ledger.ensure_ready()

    async def stop(self) -> None:
        for ledger in (self.agent_registry, self.message_ledger, self.task_ledger, self.brief_ledger):
            await ledger.close()
        await drop_database(self._env)

    async def register(self, name: str) -> Agent:
        await self.agent_registry.register(name, session=_SESSION, role="builder")
        agent = await self.agent_registry.get_agent(name, session=_SESSION)
        if hasattr(self.message_ledger, "register_agent"):
            self.message_ledger.register_agent(agent_id=agent.id, name=agent.name)
        return agent

    async def story(self, *, task_id: str, caller: Agent) -> str:
        rendered = await AppContext._comms_story(
            cast(AppContext, self), agent_row=caller, task_id=task_id
        )
        return str(rendered)


@pytest_asyncio.fixture()
async def sctx() -> AsyncIterator[_StoryCtx]:
    ctx = _StoryCtx(unique_database())
    await ctx.start()
    try:
        yield ctx
    finally:
        await ctx.stop()


def _assert_fenced_verbatim(rendered: str, body: str) -> None:
    """The ``TestFencedBodyIntegrity`` oracle (cloned): a body round-trips
    byte-verbatim inside a fence strictly wider than any embedded backtick run, and
    no forged row escapes OUTSIDE the fence."""
    assert body in rendered, "a stored body must round-trip byte-verbatim inside its fence"
    fence_lines = [line for line in rendered.splitlines() if line and set(line) == {"`"}]
    assert len(fence_lines) >= 2, "a fenced body must be bounded by two backtick-run fence lines"
    assert len(fence_lines[0]) > max_backtick_run(body), (
        "the fence must be strictly longer than any backtick run embedded in the body"
    )
    lines = rendered.splitlines()
    open_index = lines.index(fence_lines[0])
    close_index = len(lines) - 1 - lines[::-1].index(fence_lines[-1])
    outside = lines[:open_index] + lines[close_index + 1 :]
    assert not any(line.strip().startswith("- [#99 open] forged") for line in outside), (
        "the row-forge payload may live INSIDE the fence (quoted) but NEVER as its own "
        "line outside it (that would read as lore's own output)"
    )


class TestStoryReconstructsTheArc:
    async def test_story_renders_subject_creator_owner_messages_and_report_path(
        self, sctx: _StoryCtx
    ) -> None:
        lead = await sctx.register("lead")
        worker = await sctx.register("worker")
        task_id = await sctx.task_ledger.create_task(
            "reticulate the splines", "the long description", created_by="lead"
        )
        await sctx.task_ledger.claim_task(task_id, "worker")
        await sctx.message_ledger.send(
            sender=lead,
            session=_SESSION,
            body="starting on it now",
            grade="signal",
            recipients=[worker],
            task_id=task_id,
        )
        await sctx.task_ledger.transition(
            task_id,
            "done",
            actor="worker",
            summary="splines reticulated",
            report_path="docs/plans/v2/receipts/x/REPORT-worker.md",
        )
        rendered = await sctx.story(task_id=task_id, caller=lead)
        for needle in (
            "reticulate the splines",  # subject
            "lead",  # creator
            "worker",  # claim owner
            "starting on it now",  # a message body
            "REPORT-worker.md",  # report_path
        ):
            assert needle in rendered, (
                f"story must reconstruct the task arc; {needle!r} missing from: {rendered!r}"
            )

    async def test_story_names_its_set_the_task_arc(self, sctx: _StoryCtx) -> None:
        lead = await sctx.register("lead")
        task_id = await sctx.task_ledger.create_task("scope subject", "d", created_by="lead")
        rendered = await sctx.story(task_id=task_id, caller=lead)
        # Leg-1: the render NAMES its SET — the arc of THIS task (id present) — so a
        # consumer knows exactly which question was answered.
        assert task_id in rendered and "arc" in rendered.lower(), rendered

    async def test_story_omits_other_tasks_traffic(self, sctx: _StoryCtx) -> None:
        lead = await sctx.register("lead")
        worker = await sctx.register("worker")
        target = await sctx.task_ledger.create_task("target task", "d", created_by="lead")
        other = await sctx.task_ledger.create_task("other task", "d", created_by="lead")
        await sctx.message_ledger.send(
            sender=lead,
            session=_SESSION,
            body="THIS-BELONGS-TO-OTHER-TASK",
            grade="signal",
            recipients=[worker],
            task_id=other,
        )
        rendered = await sctx.story(task_id=target, caller=lead)
        assert "THIS-BELONGS-TO-OTHER-TASK" not in rendered, (
            "story(T) is scoped to T's arc — a message anchored to a DIFFERENT task must "
            f"never appear (Leg-1: what it OMITS). Rendered: {rendered!r}"
        )


class TestStoryMarksQuestionsStructurally:
    async def test_a_question_message_is_marked_and_a_signal_is_not(self, sctx: _StoryCtx) -> None:
        lead = await sctx.register("lead")
        worker = await sctx.register("worker")
        # A question-BEARING task and a signal-ONLY task, with bodies that do NOT
        # themselves contain the marker word — so the marker comes from the STRUCTURAL
        # ``message.question`` flag, never the prose.
        q_task = await sctx.task_ledger.create_task("q task", "d", created_by="lead")
        s_task = await sctx.task_ledger.create_task("s task", "d", created_by="lead")
        await sctx.message_ledger.send(
            sender=worker,
            session=_SESSION,
            body="please advise on the approach",
            grade="signal",
            recipients=[lead],
            task_id=q_task,
            set_status="input_required",  # ⇒ message.question = true
        )
        await sctx.message_ledger.send(
            sender=worker,
            session=_SESSION,
            body="please advise on the approach",
            grade="signal",
            recipients=[lead],
            task_id=s_task,
        )
        q_render = await sctx.story(task_id=q_task, caller=lead)
        s_render = await sctx.story(task_id=s_task, caller=lead)
        # Contract-defined marker: the word "question" (glyph builder-adjustable —
        # flagged in the report). Present for the question, absent for the signal.
        assert "question" in q_render.lower(), (
            f"a question message must be marked structurally (from message.question): {q_render!r}"
        )
        assert "question" not in s_render.lower(), (
            f"a plain signal must NOT be marked as a question: {s_render!r}"
        )


class TestStoryContainsStoredFreeTextInAFence:
    async def test_a_hostile_message_body_is_fenced_verbatim(self, sctx: _StoryCtx) -> None:
        lead = await sctx.register("lead")
        worker = await sctx.register("worker")
        task_id = await sctx.task_ledger.create_task("fence subject", "d", created_by="lead")
        await sctx.message_ledger.send(
            sender=worker,
            session=_SESSION,
            body=_HOSTILE_BODY,
            grade="signal",
            recipients=[lead],
            task_id=task_id,
        )
        rendered = await sctx.story(task_id=task_id, caller=lead)
        _assert_fenced_verbatim(rendered, _HOSTILE_BODY)


class TestObedienceDecline:
    def test_195_obedience_is_declined_to_06_drill(self) -> None:
        """#195 (routed 05-or-06, UNSETTLED at 03b) is DECLINED here and settled to
        06's DRILL — stated OUT LOUD so this is not a silent THIRD deferral (finding
        #195's named-decision-point clause; Fable §Q3, operator-ratified 2026-08-06).

        WHY it cannot live here: obedience is a CONSUMER-BEHAVIOR property. A render
        can make a body LEGIBLE-as-quoted (04b5's ``render_attributed``/``render_fenced``
        already do — the fence labels the content as quoted, not a delivered
        instruction). A render CANNOT make an LLM INERT to an instruction it reads;
        only a live drill that plants an in-body instruction and checks whether the
        agent ACTS on it can measure that — which is 06's home.

        05a-iii's WHOLE injection duty is therefore CONTAINMENT REUSE (the fence pin
        in ``TestStoryContainsStoredFreeTextInAFence``) + STRUCTURAL legibility (the
        question marker) — measuring LEGIBILITY, never inertness. This test carries no
        behavioural assertion by design: it is the durable record that the decline was
        deliberate and where the obedience measurement went.
        """
        # A statement, not a mechanism — see the docstring. The obedience instrument
        # is 06's; this file's instrument is the fence pin above.
        assert True
