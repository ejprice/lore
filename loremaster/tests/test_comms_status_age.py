"""Contract — #304 age-the-declaration: the latched fleet badge (packet 05a-iii, scope D).

RED contract (author: contract-05aiii). Operator-ratified design: Fable §Q4 —
render the stored ``input_required`` self-declaration WITH the age since it was
declared, so a LATCHED VERDICT becomes a DATED FACT (a fresh ``hb`` beside a stale
declaration IS the signal). #332: the ``⚠ STALE`` badge is ALREADY derived-at-render
and is NOT touched here; the latch being fixed is the ``{status}`` CELL itself.

Pins (grouped):
- **D4 schema** — ``agent`` gains ``status_set_at option<datetime>`` via
  ``DEFINE FIELD OVERWRITE`` (store §1.1). Parses the FIELD statement (house idiom
  ``_field_statement``), never substrings the DDL blob. GREEN (the stub field spec).
- **D5 write-on-change** — a status CHANGE stamps ``status_set_at``. RED (the stub
  never stamps).
- **D6 no-restamp-on-same** — a SAME-status heartbeat leaves ``status_set_at``
  UNCHANGED (mutation-provable: "same status twice ⇒ unchanged"). RED via the
  precondition (a change must first stamp a non-None value), and DISCRIMINATING
  against a blind-stamp-every-heartbeat build.
- **D7 age render** — an ``input_required`` row renders the DECLARATION age inside
  the status bracket, DISTINCT from the liveness ``hb`` age. RED (no age today).
- **D8 NONE render** — a legacy row (``status_set_at`` NONE) renders an EXPLICIT
  unknown, NEVER a fabricated ``0s``: a NONE cell must render DIFFERENTLY from a
  0-second cell. RED, and DISCRIMINATING against a fabricate-zero build.
- **D9 vocabulary pair** — the fleet renders the STORED ``agent.status``, NEVER the
  DERIVED ``awaiting_answer`` question-debt (DD-2's two-vocabulary rule). Both
  fixtures, different values: (1) ``active`` + an outstanding question → fleet shows
  ``active`` (a conflating build wrongly badges input_required); (2)
  ``input_required`` + NO question → fleet still shows ``input_required`` (an
  awaiting_answer-derived build shows nothing = false-not-waiting). GREEN now
  (stored-status render), RED against the conflation.
- **D10 no-poison** — a row written WITHOUT ``status_set_at`` (as every production
  agent row is) survives a subsequent UPDATE — store §1.4: an ``option<>`` no-assert
  field cannot write-poison. GREEN now, RED against a required/asserted-field build.

RULING — FORK (D/#304 age SCOPE), RESOLVED = **input_required-ONLY** (Fable ruling
FORK 1, 2026-08-06, operator-delegated; ``REPORT-fable-design-05a.md`` §Follow-up
rulings, ``lore_recall("Fable rulings 05a-iii forks")``). ``input_required`` is the one
status that WINS over the idle→active auto-flip, so it alone goes stale WHILE the agent
works — aging it exposes the CONTRADICTION between fresh liveness and a stale
self-declaration. ``idle``/``active`` carry no such contradiction (a fresh heartbeat
keeps them current), and aging them both renders pure churn AND breaks the green
``test_comms_fleet_grouping`` ``[idle]``/``[active]`` brackets (a C-DEF trap);
``retired`` renders in the ``+K retired`` trailer, moot. RIDER (property-keying + named
re-open trigger): the build keys the age-render on the PROPERTY that a status LATCHES,
NOT a bare ``== "input_required"`` literal — see ``TestFleetAgesTheDeclaration`` and
``test_input_required_shows_the_declaration_age_beside_the_liveness_age`` for the note
the builder-brief inherits.

Tests hit spike-surreal ``ws://127.0.0.1:18000`` ONLY; ``:18500`` is NEVER touched.
"""

from __future__ import annotations

import re
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
from loremaster.messages import MessageLedger
from loremaster.server import AppContext
from loremaster.store.surreal_schema import AGENT_TABLE, generate_agent_ddl
from test_comms_schema import _field_statement

_SESSION = "age-wave"
# A rendered age token (``0s`` / ``47m`` / ``3h`` / ``2d``) — used by D8/F6 to detect a
# fabricated numeric declaration age inside a legacy row's status bracket.
_AGE_TOKEN = re.compile(r"\d+[smhd]")


# --------------------------------------------------------------------------- #
# D4 — schema (offline).
# --------------------------------------------------------------------------- #
class TestStatusSetAtSchema:
    def test_status_set_at_is_option_datetime_via_overwrite(self) -> None:
        # ``_field_statement`` returns the field's own ``DEFINE FIELD OVERWRITE``
        # statement or fails naming the #107 IF-NOT-EXISTS regression — the house
        # idiom (parses the statement, never substrings the blob).
        statement = _field_statement(generate_agent_ddl(), AGENT_TABLE, "status_set_at")
        assert "option<datetime>" in statement, (
            "status_set_at must be option<datetime> — store reference §1.4: a NEW field "
            f"on the POPULATED agent table must be option<> or it write-poisons every "
            f"existing row's next UPDATE. Served: {statement!r}"
        )


# --------------------------------------------------------------------------- #
# Live-ledger harness (spike-surreal :18000) shared by D5/D6/D7/D8/D9/D10.
# --------------------------------------------------------------------------- #
class _LiveCtx:
    """A minimal live ``_comms_fleet`` harness: real agent/message/brief ledgers on
    ONE throwaway database, plus the ``config.comms`` shape the handler reads."""

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
        self.brief_ledger = BriefLedger(**coord)
        self.config = SimpleNamespace(
            comms=SimpleNamespace(stale_heartbeat_s=600, fleet_limit=20, drain_limit=20)
        )

    async def start(self) -> None:
        setup = await connect_admin(self._env)
        await setup.close()
        await self.agent_registry.ensure_ready()
        await self.message_ledger.ensure_ready()
        await self.brief_ledger.ensure_ready()

    async def stop(self) -> None:
        await self.agent_registry.close()
        await self.message_ledger.close()
        await self.brief_ledger.close()
        await drop_database(self._env)

    async def register(self, name: str, *, status: str = "active") -> Agent:
        await self.agent_registry.register(name, session=_SESSION, role="builder")
        if status != "active":
            await self.agent_registry.touch(name, session=_SESSION, status=status)
        agent = await self.agent_registry.get_agent(name, session=_SESSION)
        self.message_ledger.register_agent(agent_id=agent.id, name=agent.name) if hasattr(
            self.message_ledger, "register_agent"
        ) else None
        return agent

    async def set_status_set_at(self, agent: Agent, value: datetime | None) -> None:
        """Raw-write ``status_set_at`` (the write-side stamp is the builder's; this
        manufactures a backdated / legacy value deterministically, the
        ``_backdate_heartbeat`` idiom)."""
        await self.agent_registry._query(  # noqa: SLF001 - test-only raw write
            "UPDATE type::record('agent', $id) SET status_set_at = $ts",
            {"id": agent.id, "ts": value},
        )

    async def render_fleet(self, *, caller: Agent) -> str:
        # Drive the real handler with this harness as ``self`` (the ``_harness() ->
        # Any`` idiom, made explicit): the handler duck-types only the ledgers/config
        # this class provides.
        rendered = await AppContext._comms_fleet(
            cast(AppContext, self), agent_row=caller, session=_SESSION, limit=None
        )
        return str(rendered)


@pytest_asyncio.fixture()
async def live() -> AsyncIterator[_LiveCtx]:
    ctx = _LiveCtx(unique_database())
    await ctx.start()
    try:
        yield ctx
    finally:
        await ctx.stop()


def _fleet_row(rendered: str, name: str) -> str:
    prefix = f"- {name} ["
    matches = [line for line in rendered.splitlines() if line.startswith(prefix)]
    assert len(matches) == 1, f"expected exactly one fleet row for {name!r}: {matches!r}"
    return matches[0]


def _status_bracket(row: str) -> str:
    return row[row.index("[") : row.index("]") + 1]


# --------------------------------------------------------------------------- #
# D5 / D6 — the write-side stamp (live registry).
# --------------------------------------------------------------------------- #
class TestStatusSetAtWriteSide:
    async def test_a_status_change_stamps_status_set_at(self, live: _LiveCtx) -> None:
        await live.register("changer", status="active")
        await live.agent_registry.touch("changer", session=_SESSION, status="input_required")
        after = await live.agent_registry.get_agent("changer", session=_SESSION)
        assert after.status == "input_required"
        assert after.status_set_at is not None, (
            "a status CHANGE (active → input_required) must stamp status_set_at so the "
            "fleet render can age the declaration"
        )

    async def test_the_same_status_does_not_restamp(self, live: _LiveCtx) -> None:
        # Establish a stamp via a real change, then prove a same-status heartbeat
        # leaves it — the mutation-provable "same status twice ⇒ unchanged" pin.
        await live.register("stable", status="active")
        await live.agent_registry.touch("stable", session=_SESSION, status="input_required")
        first = (await live.agent_registry.get_agent("stable", session=_SESSION)).status_set_at
        assert first is not None, (
            "precondition: the status change must have stamped status_set_at (RED here "
            "means the write-side stamp is unbuilt)"
        )
        await live.agent_registry.touch("stable", session=_SESSION, status="input_required")
        second = (await live.agent_registry.get_agent("stable", session=_SESSION)).status_set_at
        assert second == first, (
            "a heartbeat that does NOT change the status must not re-stamp status_set_at "
            "(else every heartbeat resets the declaration age to ~0 — the latch bug inverted)"
        )


# --------------------------------------------------------------------------- #
# D7 / D8 — the fleet age render (live handler; declaration age computed off the
# same ``now`` as heartbeat age).
# --------------------------------------------------------------------------- #
class TestFleetAgesTheDeclaration:
    """RULING FORK 1 RIDER (property-keying + named re-open trigger) — the note the
    builder-brief inherits.

    The build MUST key the age-render conditional on the PROPERTY that a status
    LATCHES — i.e. it wins over the idle→active auto-flip, so it (and only
    ``input_required``, today) can go STALE while the agent keeps heartbeating —
    NOT on a bare ``status == "input_required"`` literal that a future latching
    status would silently escape (the enumerate-the-forbidden law: the forbidden
    set is unbounded; key on the property).

    NAMED RE-OPEN TRIGGER: the day any status OTHER than ``input_required`` is made
    to win over the idle→active auto-flip, it JOINS the aged set — the age-scope
    re-opens (Fable ruling FORK 1). That trigger is MECHANICAL, not a hope: it is
    already guarded by the existing suite —
    ``test_agent_registry.py::TestAgentStatusesConstant`` (reds on ANY change to the
    closed four-value status domain) and
    ``test_agent_registry.py::TestIdleAutoFlip`` (``test_input_required_agent_does_not_auto_flip``
    + ``test_idle_agent_auto_flips_to_active_with_no_explicit_status`` pin the
    current auto-flip winner-set). A newly-introduced latching status trips BOTH,
    forcing the "does it latch → re-open the age-scope?" review.

    WHY a docstring note and NOT a new render-side structural guard: with a
    single-member latch set, a property-keyed render and a literal-keyed render are
    behaviourally IDENTICAL for every current input — undiscriminable — so a
    render-side guard could only ban the literal, which is itself the
    enumerate-the-forbidden antipattern (a property-keyed build may legitimately
    reference ``"input_required"`` while COMPUTING the latch set). The mechanical
    re-open trigger already lives in the status-domain pins above; duplicating it
    here would violate ONE IMPLEMENTATION.
    """

    async def test_input_required_shows_the_declaration_age_beside_the_liveness_age(
        self, live: _LiveCtx
    ) -> None:
        agent = await live.register("parked", status="input_required")
        # Declared ~47m ago; heartbeat is fresh (register/touch just ran).
        await live.set_status_set_at(agent, datetime.now(UTC) - timedelta(minutes=47, seconds=30))
        rendered = await live.render_fleet(caller=agent)
        row = _fleet_row(rendered, "parked")
        assert "input_required" in row
        assert "47m" in row, (
            f"the input_required declaration must be aged (≈47m) in the status cell — a "
            f"latched verdict becomes a dated fact (#304). Row: {row!r}"
        )
        # The declaration age (47m) sits in the status bracket, BEFORE the liveness
        # ``hb`` cell — the two ages are distinct, which is the whole signal.
        assert "hb " in row and row.index("47m") < row.index("hb "), row

    async def test_none_status_set_at_renders_unknown_not_a_fabricated_zero(
        self, live: _LiveCtx
    ) -> None:
        """RULING FORK 1 nudge (D8 NONE render honesty) + F6 (adversary residual). A
        legacy row (``status_set_at`` NONE) must render an HONEST unknown
        (``declared: unknown`` / an age-since-hb) — NEVER a fabricated age. The
        specific wording is builder latitude. TWO legs, because the first is
        timing-fragile alone: (1) the NONE cell renders DIFFERENTLY from a
        just-declared 0-second cell (the ``!=`` below) — reddens a fabricate-zero
        build sub-second, but on a slow >1s render ``fresh`` becomes "1s" and the
        fabricated "0s" DIFFERS, false-clearing it (adversary F6); (2) the NONE cell
        carries an EXPLICIT unknown token / NO age pattern — timing-INDEPENDENT, so a
        NONE→'0s' build reddens regardless of render latency. A single-value fixture
        (only NONE, or only 0s) would pass a fabricate-zero build; the PAIR
        discriminates, and leg (2) closes the timing hole."""
        legacy = await live.register("legacy", status="input_required")
        fresh = await live.register("fresh", status="input_required")
        await live.set_status_set_at(legacy, None)  # a pre-#304 row
        await live.set_status_set_at(fresh, datetime.now(UTC))  # declared ~0s ago
        rendered = await live.render_fleet(caller=legacy)
        legacy_cell = _status_bracket(_fleet_row(rendered, "legacy"))
        fresh_cell = _status_bracket(_fleet_row(rendered, "fresh"))
        assert legacy_cell != fresh_cell, (
            "a legacy row (status_set_at NONE ⇒ age UNKNOWN) must NOT render identically "
            f"to a just-declared 0-second row — NONE must not fabricate an age. "
            f"legacy={legacy_cell!r} fresh={fresh_cell!r}"
        )
        assert "input_required" in legacy_cell
        # F6 (residual fix): the ``!= fresh`` check above is TIMING-FRAGILE — on a slow
        # (>1s) render ``fresh`` becomes "1s" and a fabricate-zero build's legacy "0s"
        # DIFFERS from it, false-clearing the exact build D8 targets. This leg is
        # timing-INDEPENDENT: the legacy (NONE) cell must render an EXPLICIT unknown — it
        # names "unknown" OR carries NO age token (``\d+[smhd]``) in its status bracket —
        # so a NONE→"0s" fabricate-zero build reddens REGARDLESS of render timing.
        assert "unknown" in legacy_cell.lower() or not _AGE_TOKEN.search(legacy_cell), (
            "a legacy row (status_set_at NONE ⇒ declaration age UNKNOWN) must render an "
            "EXPLICIT unknown (e.g. 'declared: unknown'), never a fabricated numeric age; a "
            "NONE→'0s' fabricate-zero build reddens here independent of render timing "
            f"(unlike the != fresh check above). legacy_cell={legacy_cell!r}"
        )


# --------------------------------------------------------------------------- #
# D9 — the two-vocabulary discriminating pair (DD-2): fleet renders the STORED
# status, never the derived awaiting_answer.
# --------------------------------------------------------------------------- #
class TestFleetRendersStoredStatusNeverQuestionDebt:
    async def test_active_with_an_outstanding_question_still_shows_active(
        self, live: _LiveCtx
    ) -> None:
        asker = await live.register("asker", status="active")
        other = await live.register("other", status="active")
        # asker asks a question (set_status='input_required' marks message.question);
        # asker's STORED status stays 'active' (send never touches the status row).
        await live.message_ledger.send(
            sender=asker,
            session=_SESSION,
            body="need a ruling — proceed?",
            grade="signal",
            recipients=[other],
            set_status="input_required",
        )
        assert await live.message_ledger.awaiting_answer(agent_id=asker.id) is not None, (
            "fixture precondition: the asker must have an outstanding question so a "
            "conflating build has something to (wrongly) badge on"
        )
        row = _fleet_row(await live.render_fleet(caller=asker), "asker")
        assert "[active" in row and "input_required" not in row, (
            "an agent with an outstanding QUESTION but a STORED 'active' status must show "
            f"active in fleet — the debt is the agent's OWN surface, not fleet (DD-2). "
            f"A build deriving the badge from awaiting_answer wrongly badges. Row: {row!r}"
        )

    async def test_input_required_with_no_question_still_shows_input_required(
        self, live: _LiveCtx
    ) -> None:
        parked = await live.register("declared", status="input_required")
        assert await live.message_ledger.awaiting_answer(agent_id=parked.id) is None, (
            "fixture precondition: this agent has NO outstanding lore question"
        )
        row = _fleet_row(await live.render_fleet(caller=parked), "declared")
        assert "input_required" in row, (
            "an agent that self-declared 'input_required' (via heartbeat) but has NO lore "
            "question must STILL badge input_required — a build deriving from "
            f"awaiting_answer shows nothing (false-not-waiting). Row: {row!r}"
        )


# --------------------------------------------------------------------------- #
# D10 — store §1.4: a NONE-status_set_at (legacy) row survives a later UPDATE.
# --------------------------------------------------------------------------- #
class TestOptionFieldDoesNotWritePoison:
    async def test_a_row_without_status_set_at_survives_a_later_update(
        self, live: _LiveCtx
    ) -> None:
        agent = await live.register("legacy2", status="active")
        await live.set_status_set_at(agent, None)  # a production-shaped legacy row
        # A subsequent heartbeat UPDATEs the whole record; store §1.4 says an
        # option<> no-assert field cannot poison it. A required/asserted field would.
        await live.agent_registry.touch("legacy2", session=_SESSION)
        survived = await live.agent_registry.get_agent("legacy2", session=_SESSION)
        assert survived.name == "legacy2"
