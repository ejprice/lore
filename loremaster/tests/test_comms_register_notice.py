"""CONTRACT (RED) for finding #262 — register discloses a task-holder's LIVENESS.

`lore_comms register(task_id=X)` silently accepts a task_id another agent holds.
The fix (design of record: `docs/plans/v2/design/2026-08-11-task-coordination-substrate.md`
§2A + ADDENDUM A-262, Reading 1 = DISCLOSE-NOT-REFUSE) resolves X -> owner Y via the
task ledger, resolves Y in the agent registry, derives Y's liveness via the SHARED STALE
predicate (today inline `heartbeat_age_s > stale_after_s` in `_render_comms_fleet_row`),
and renders an ADVISORY notice on the register surface — NEVER refusing (register stays
cheap + idempotent).

These tests are the CONTRACT: RED at HEAD `c0071cd` (no notice is emitted today), GREEN
against a correct build. Author: contract-verbs-05b (Opus-4.8). No production code here.

Harness: a thin LIVE ctx over the shared `_surreal_harness` primitives (spike-surreal
ws://127.0.0.1:18000), wiring the SAME store into `agent_registry` + `task_ledger` +
`brief_ledger` (the register handler reads all three under the fix). Rolled per-file from
shared primitives exactly as `test_comms_status_age.py::_LiveCtx` /
`test_comms_footer.py` do — the shared IMPLEMENTATION is `AgentRegistry`/`TaskLedger`,
not the ctx.

SCOPE (brief): ONLY the register-path notice + the STALE-predicate share. NOT the
query/fleet enrichment, NOT `reap`, NOT `assign`. #262 is the FIRST instance of the
owner->registry reconciliation seam.

TRUST (Consumer Law): an unresolvable holder renders "not found in registry", NEVER a
false "active" — that false clear is the fatal case (Forgery-pin leg).
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest
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
from loremaster.server import AppContext
from loremaster.tasks import TaskLedger

pytestmark = pytest.mark.asyncio

# The registering caller and the default holder session.
_SESSION = "regnotice"
_ROLE = "builder"

# A minutes-token detector for the STALE "last seen 21m ago" clause (largest-fit unit,
# no padding — see `AppContext._render_age`). We assert the SHAPE, not a brittle exact
# integer, so a few seconds of clock drift never flips the pin.
_MINUTES_AGO = re.compile(r"\d+m ago")


def _notice_line(text: str) -> str:
    """The single advisory ``note:`` line the register render composes for #262, or ``""``
    if none. Liveness-token assertions MUST scope to THIS line: the register HEAD always
    renders ``... — status active`` for the REGISTERING agent, so a bare ``"active" in text``
    is non-discriminating (it passes on the head alone, holder liveness notwithstanding).
    """
    for line in text.splitlines():
        if line.lstrip().startswith("note:"):
            return line
    return ""


class _RegisterCtx:
    """A duck-typed AppContext: real registry + task ledger + brief ledger on ONE store.

    The register handler (`AppContext._comms_register`) reads `self.agent_registry`,
    `self.brief_ledger`, and — under the #262 fix — `self.task_ledger` + `self.config`.
    We call the handler directly (bypassing the tool footer) to isolate the notice.
    """

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
        self.task_ledger = TaskLedger(**coord)
        self.brief_ledger = BriefLedger(**coord)
        # Fake config namespace exactly as the live comms harnesses do; the STALE
        # threshold is the mutable knob the ONE-IMPLEMENTATION proof perturbs.
        self.config = SimpleNamespace(
            comms=SimpleNamespace(stale_heartbeat_s=600, fleet_limit=20, drain_limit=20)
        )

    async def start(self) -> None:
        setup = await connect_admin(self._env)
        await setup.close()
        await self.agent_registry.ensure_ready()
        await self.task_ledger.ensure_ready()
        await self.brief_ledger.ensure_ready()

    async def stop(self) -> None:
        await self.agent_registry.close()
        await self.task_ledger.close()
        await self.brief_ledger.close()
        await drop_database(self._env)

    # -- setup helpers --------------------------------------------------------

    async def register_agent(
        self, name: str, *, session: str = _SESSION, role: str = _ROLE
    ) -> Agent:
        """Register (or re-register) an agent and return its fresh row."""
        result = await self.agent_registry.register(name, session=session, role=role)
        return result.agent

    async def retire(self, name: str, *, session: str = _SESSION) -> None:
        await self.agent_registry.touch(name, session=session, status="retired")

    async def backdate_heartbeat(self, agent: Agent, *, seconds_ago: int) -> None:
        """Test-only raw write: age a row's heartbeat so it reads STALE.

        Mirrors the `test_comms_status_age.py` `set_status_set_at` idiom; a CONTENT
        datetime binds as a Python datetime (store law §2).
        """
        await self.agent_registry._query(  # noqa: SLF001 - test-only raw write
            "UPDATE type::record('agent', $id) SET heartbeat_at = $ts",
            {"id": agent.id, "ts": datetime.now(UTC) - timedelta(seconds=seconds_ago)},
        )

    async def held_task(self, *, owner: str, subject: str = "held work") -> str:
        """Create a task and drive it to claimed by `owner`; return its id."""
        task_id = await self.task_ledger.create_task(
            subject, "a real description", created_by="creator-262"
        )
        claim = await self.task_ledger.claim_task(task_id, owner)
        assert claim.claimed, "fixture precondition: the claim must win"
        return task_id

    async def open_task(self, *, subject: str = "unheld work") -> str:
        """Create an OPEN, never-claimed task (owner is None)."""
        return await self.task_ledger.create_task(
            subject, "a real description", created_by="creator-262"
        )

    # -- exercise -------------------------------------------------------------

    async def register_notice(
        self, *, agent: str, task_id: str | None, session: str = _SESSION
    ) -> str:
        """Register `agent` (with `task_id`) and return the rendered register output."""
        rendered = await AppContext._comms_register(
            cast(AppContext, self),
            agent=agent,
            session=session,
            role=_ROLE,
            model=None,
            spawned_by=None,
            task_id=task_id,
        )
        return str(rendered)

    async def fleet_line(self, *, caller: Agent, name: str) -> str:
        """Render the fleet and return the single row line for `name`."""
        rendered = await AppContext._comms_fleet(
            cast(AppContext, self), agent_row=caller, session=_SESSION, limit=None
        )
        for line in str(rendered).splitlines():
            if line.lstrip().startswith(f"- {name} "):
                return line
        raise AssertionError(f"no fleet row for {name!r} in:\n{rendered}")


@pytest_asyncio.fixture()
async def ctx() -> AsyncIterator[_RegisterCtx]:
    live = _RegisterCtx(unique_database())
    await live.start()
    try:
        yield live
    finally:
        await live.stop()


# ---------------------------------------------------------------------------
# The discriminating self/other/unheld triple (Fable A-262 pin set).
# NOTE: the "no notice" pins are GREEN at HEAD (HEAD emits no notice ever) — they are
# REGRESSION GUARDS that the fix must not OVER-fire; their positive control is the
# other-held pin (RED at HEAD), which proves the notice fires when it should.
# ---------------------------------------------------------------------------


class TestSelfOtherUnheldTriple:
    async def test_other_held_emits_the_notice(self, ctx: _RegisterCtx) -> None:
        """RED at HEAD: a task held by ANOTHER live agent -> a disclosing notice."""
        await ctx.register_agent("holder-y")
        task_id = await ctx.held_task(owner="holder-y")

        text = await ctx.register_notice(agent="reg-agent", task_id=task_id)

        notice = _notice_line(text)
        assert "is held by" in notice
        assert "holder-y" in notice
        # never refuses: the registration itself still succeeds.
        assert "registered reg-agent" in text or "re-registered reg-agent" in text

    async def test_self_held_emits_NO_notice(self, ctx: _RegisterCtx) -> None:
        """The holder registering its OWN task gets no disclosure (discriminator)."""
        task_id = await ctx.held_task(owner="reg-agent")

        text = await ctx.register_notice(agent="reg-agent", task_id=task_id)

        assert "is held by" not in text
        assert "registered reg-agent" in text or "re-registered reg-agent" in text

    async def test_unheld_task_emits_NO_notice(self, ctx: _RegisterCtx) -> None:
        """An OPEN (unclaimed, owner=None) task is a legitimate association, silent."""
        task_id = await ctx.open_task()

        text = await ctx.register_notice(agent="reg-agent", task_id=task_id)

        assert "is held by" not in text
        assert "not found" not in text  # the task DOES exist

    async def test_no_task_id_is_unchanged(self, ctx: _RegisterCtx) -> None:
        """register with no task_id keeps the pre-#262 output (notice is ADDITIVE)."""
        text = await ctx.register_notice(agent="reg-agent", task_id=None)

        assert "is held by" not in text
        assert "not found" not in text
        assert "registered reg-agent" in text


# ---------------------------------------------------------------------------
# The liveness render set — every holder-liveness FATE forced by a fixture
# (the quantifier law). Each "notice present + token" pin is RED at HEAD.
# ---------------------------------------------------------------------------


class TestHolderLivenessRenderSet:
    async def test_live_holder_renders_active(self, ctx: _RegisterCtx) -> None:
        await ctx.register_agent("holder-y")  # fresh heartbeat, status active
        task_id = await ctx.held_task(owner="holder-y")

        text = await ctx.register_notice(agent="reg-agent", task_id=task_id)

        notice = _notice_line(text)
        assert "is held by" in notice and "holder-y" in notice
        assert "active" in notice
        assert "STALE" not in notice
        assert "not found in registry" not in notice

    async def test_stale_holder_renders_STALE_with_age(self, ctx: _RegisterCtx) -> None:
        holder = await ctx.register_agent("holder-y")
        await ctx.backdate_heartbeat(holder, seconds_ago=1300)  # 21m > 600s default
        task_id = await ctx.held_task(owner="holder-y")

        text = await ctx.register_notice(agent="reg-agent", task_id=task_id)

        notice = _notice_line(text)
        assert "is held by" in notice and "holder-y" in notice
        assert "STALE" in notice
        assert "last seen" in notice
        assert _MINUTES_AGO.search(notice), f"expected an 'Nm ago' age token in:\n{notice}"

    async def test_retired_holder_renders_retired(self, ctx: _RegisterCtx) -> None:
        """Retired takes precedence; fixture keeps the heartbeat FRESH (dodges F4)."""
        await ctx.register_agent("holder-y")  # fresh heartbeat
        await ctx.retire("holder-y")
        task_id = await ctx.held_task(owner="holder-y")

        text = await ctx.register_notice(agent="reg-agent", task_id=task_id)

        notice = _notice_line(text)
        assert "is held by" in notice and "holder-y" in notice
        assert "retired" in notice
        # a retired holder is DISTINCT from an unresolvable one (get_agent conflates
        # them into UnknownAgentError — this pin forces the retired-inclusive resolve).
        assert "not found in registry" not in notice

    async def test_unresolvable_holder_never_says_active(self, ctx: _RegisterCtx) -> None:
        """TRUST / Forgery-pin: an owner with NO registry row -> 'not found', never alive."""
        # 'ghost-owner' is never registered.
        task_id = await ctx.held_task(owner="ghost-owner")

        text = await ctx.register_notice(agent="reg-agent", task_id=task_id)

        notice = _notice_line(text)
        assert "is held by" in notice and "ghost-owner" in notice
        assert "not found in registry" in notice
        # THE fatal false clear: a dead holder rendered as alive (scoped to the NOTICE —
        # the register HEAD's own "status active" must never satisfy this pin).
        assert "active" not in notice
        assert "idle" not in notice
        assert "STALE" not in notice

    async def test_no_such_task_discloses_and_still_registers(
        self, ctx: _RegisterCtx
    ) -> None:
        text = await ctx.register_notice(agent="reg-agent", task_id="deadbeef" * 4)

        assert "not found" in text  # "task <X> not found"
        assert "is held by" not in text  # no holder to disclose
        assert "registered reg-agent" in text  # never refuses

    async def test_ambiguous_holder_picks_most_recent_heartbeat(
        self, ctx: _RegisterCtx
    ) -> None:
        """Same name in two sessions -> most-recent-heartbeat wins, NEVER a raise.

        This pin FORCES the resolve off `get_agent` (which raises AmbiguousAgentError):
        the notice must disclose the freshest holder's liveness without failing.
        """
        older = await ctx.register_agent("dupe-y", session="sess-old")
        await ctx.backdate_heartbeat(older, seconds_ago=1300)  # STALE
        await ctx.register_agent("dupe-y", session="sess-new")  # fresh -> active
        task_id = await ctx.held_task(owner="dupe-y")

        # must not raise:
        text = await ctx.register_notice(agent="reg-agent", task_id=task_id)

        notice = _notice_line(text)
        assert "is held by" in notice and "dupe-y" in notice
        assert "active" in notice  # the fresher row won
        assert "STALE" not in notice


# ---------------------------------------------------------------------------
# TRUST: register NEVER refuses / NEVER raises, in EVERY holder state.
# ---------------------------------------------------------------------------


class TestRegisterNeverRefuses:
    @pytest.mark.parametrize("owner", ["holder-y", "ghost-owner"])
    async def test_registration_succeeds_regardless(
        self, ctx: _RegisterCtx, owner: str
    ) -> None:
        if owner == "holder-y":
            await ctx.register_agent("holder-y")
        task_id = await ctx.held_task(owner=owner)

        text = await ctx.register_notice(agent="reg-agent", task_id=task_id)

        # idempotent registration ALWAYS lands, notice or not.
        assert "registered reg-agent" in text or "re-registered reg-agent" in text

    async def test_bogus_task_id_does_not_raise(self, ctx: _RegisterCtx) -> None:
        text = await ctx.register_notice(agent="reg-agent", task_id="not-a-real-id")
        assert "registered reg-agent" in text


# ---------------------------------------------------------------------------
# ONE IMPLEMENTATION — the STALE threshold is SHARED with the fleet render.
# The brief's own proof: "mutate the 600s constant -> BOTH fleet AND notice move."
# A cloned/hardcoded 600 in the notice would NOT respond to the config change; this
# behavioral proof catches that divergence.
# ---------------------------------------------------------------------------


class TestStaleThresholdIsSharedWithFleet:
    async def test_both_surfaces_flip_at_one_threshold(
        self, ctx: _RegisterCtx
    ) -> None:
        caller = await ctx.register_agent("reg-agent")
        holder = await ctx.register_agent("holder-y")
        await ctx.backdate_heartbeat(holder, seconds_ago=1300)  # age ~= 21m
        task_id = await ctx.held_task(owner="holder-y")

        # Threshold BELOW the age -> both surfaces STALE.
        ctx.config.comms.stale_heartbeat_s = 600
        notice_stale = await ctx.register_notice(agent="reg-agent", task_id=task_id)
        fleet_stale = await ctx.fleet_line(caller=caller, name="holder-y")
        assert "STALE" in _notice_line(notice_stale)
        assert "STALE" in fleet_stale

        # Threshold ABOVE the age -> NEITHER surface STALE. If the notice cloned the
        # 600 constant instead of reading config, it would stay STALE here and diverge.
        ctx.config.comms.stale_heartbeat_s = 3600
        notice_fresh = await ctx.register_notice(agent="reg-agent", task_id=task_id)
        fleet_fresh = await ctx.fleet_line(caller=caller, name="holder-y")
        assert "STALE" not in _notice_line(notice_fresh)
        assert "STALE" not in fleet_fresh

    async def test_both_surfaces_share_the_EXTRACTED_predicate(
        self, monkeypatch: pytest.MonkeyPatch, ctx: _RegisterCtx
    ) -> None:
        """ONE-IMPLEMENTATION (sharpened, adversary MINOR): the constant-share pin above
        proves a shared 600s CONSTANT; this proves a shared PREDICATE. Mutate the extracted
        `AppContext._heartbeat_is_stale` LOGIC and BOTH the fleet render AND the register
        notice must flip together — a private `age > threshold` clone in either surface
        would ignore the patch and diverge. RED at HEAD via AttributeError (the predicate is
        not extracted yet). Together with the constant pin: threshold-source AND logic shared.
        """
        caller = await ctx.register_agent("reg-agent")
        holder = await ctx.register_agent("holder-y")
        await ctx.backdate_heartbeat(holder, seconds_ago=1300)  # genuinely stale by age
        task_id = await ctx.held_task(owner="holder-y")

        # always-False: a GENUINELY-stale holder must read NOT stale on BOTH surfaces.
        monkeypatch.setattr(
            AppContext, "_heartbeat_is_stale",
            lambda age_s, stale_after_s: False, raising=True,
        )
        assert "STALE" not in _notice_line(
            await ctx.register_notice(agent="reg-agent", task_id=task_id)
        )
        assert "STALE" not in await ctx.fleet_line(caller=caller, name="holder-y")

        # always-True: a config-fresh holder must read STALE on BOTH surfaces.
        monkeypatch.setattr(
            AppContext, "_heartbeat_is_stale",
            lambda age_s, stale_after_s: True, raising=True,
        )
        assert "STALE" in _notice_line(
            await ctx.register_notice(agent="reg-agent", task_id=task_id)
        )
        assert "STALE" in await ctx.fleet_line(caller=caller, name="holder-y")
