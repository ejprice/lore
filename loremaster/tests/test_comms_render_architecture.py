"""Packet 02 — comms render ARCHITECTURE contract (#104 root cause + #103 + #100).

Spec: ``docs/design/2026-07-12-pkt28-c1-semantics.md`` v8 — §5.3 (head/coverage/
skew vocabulary + the mechanism-promise + subscription corollaries), §9.1/§9.2/
§9.4/§9.5/§9.6, §9.7 (the mechanism-promise sweep), §10 (RenderCase inventory).
Findings: #104 (the ROOT CAUSE of all ten render-honesty instances — 'project' is
a ROLE bound to a NAME, re-hardcoded at seven handler sites and then described
GENERICALLY by the renders), #103 (the ninth instance — heartbeat skew is
project-only in the MECHANISM but universal in the PROSE), #100 (``created_by``
splits identity). #101 (log-capture isolation) is fixed-by-4c2efbf and its
mutation-proven invariant lives in ``test_caplog_isolation.py`` — nothing is
added here for it (see REPORT-pkt02-contract.md §D).

Execute the spec verbatim; a genuine gap is a STOP-and-flag, never an improvised
decision (brief-base §1 / repo CLAUDE.md). Contract-writers turn the spec into
tests verbatim.

RED EXPECTATION AS AUTHORED — HISTORICAL, NOT CURRENT. This whole module was
the RED half of a TDD cycle; packet 02 (17277d1) shipped the fix and these pins
are GREEN today. What each pin caught, preserved because it records what the
pin is FOR:

* The ``_render_comms_brief_publish`` calls below pass a then-NEW keyword
  ``auto_ack_at_register`` that the shipped signature did not accept — the
  render re-derived that applicability from ``result.brief.name ==
  BRIEF_NAME_PROJECT`` (server.py:4936, the #104 smoking gun). Those pins were
  RED with a ``TypeError`` before 17277d1 and GREEN once the render took the
  typed flag. The DISCRIMINATING fixtures (a brief literally named 'project'
  with the flag FALSE, and a non-'project' brief with the flag TRUE) still go
  RED for any build that goes back to comparing the NAME.
* The ``TestStandingBriefIsOneSharedRole`` mutation pins monkeypatch
  ``loremaster.server.STANDING_BRIEF`` (the named-role constant the fix
  introduced) — with ``raising=False`` so the pre-fix code (which had no such
  symbol and keyed every surface off ``BRIEF_NAME_PROJECT``) simply ignored the
  patch and FAILED the "every surface followed the role" assertions: red for
  the RIGHT reason (the role is not centralised), never a ``TypeError``.
* ``TestHeartbeatSurfacesSubscribedNameSkew`` drives the real dispatcher and
  asserts on the served string only — no new symbol referenced — so it was RED
  because the pre-fix handler read only 'project' skew, not because of a
  collection error.

See REPORT-pkt02-contract.md for the RED-for-right-reason table and the
satisfiability receipts (the contract run 0-failed against a scratch reference
build).
"""

from __future__ import annotations

import ast
import inspect
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from _comms_fakes import (
    FakeAgentDatabase,
    FakeAgentRegistry,
    FakeBriefDatabase,
    FakeBriefLedger,
)
from loremaster.briefs import Brief, BriefBehindEntry, BriefPublishResult
from loremaster.render import render_attributed
from loremaster.server import AppContext

# The em-dash the render templates use verbatim (U+2014) — pinned as a named
# constant so a transcription slip in a test literal fails loudly here rather
# than silently weakening a byte-exact assertion.
_EM_DASH = "—"

_PACKAGE_ROOT = Path(inspect.getfile(AppContext)).resolve().parent


# --------------------------------------------------------------------------- #
# Local fixture factories (fixture DATA, no logic coupling — same independence
# rationale test_comms_tool.py states for its own ``_config``/``_brief``).
#
# ``_brief`` here has NO ``name`` default ON PURPOSE (finding #104 part 3: the
# defaulting factory MANUFACTURED the monoculture blind spot). Every call site
# in this module CHOOSES its name, and at least one pin per grammar deliberately
# chooses a non-'project' name (the anti-monoculture rule the spec §TEST SKETCH
# and repo CLAUDE.md mandate).
# --------------------------------------------------------------------------- #


def _brief(*, name: str, version: int = 1, body: str = "read the plan", created_by: str = "lead") -> Brief:
    return Brief(
        id=FakeBriefLedger._brief_id(name, version),
        name=name,
        version=version,
        body=body,
        created_by=created_by,
        note=None,
        created_at=datetime.now(UTC),
    )


def _publish_result(*, name: str, version: int, first_version: bool) -> BriefPublishResult:
    return BriefPublishResult(brief=_brief(name=name, version=version), first_version=first_version)


def _harness() -> tuple[Any, FakeAgentRegistry, FakeBriefLedger]:
    """A minimal ``AppContext``-shaped double over the two shared fake DBs —
    the exact attributes ``AppContext.comms`` touches, nothing else (the
    documented isolation strategy test_comms_tool.py's ``_harness`` uses)."""
    registry = FakeAgentRegistry(db=FakeAgentDatabase())
    ledger = FakeBriefLedger(db=FakeBriefDatabase())
    harness = SimpleNamespace(
        agent_registry=registry,
        brief_ledger=ledger,
        config=SimpleNamespace(
            comms=SimpleNamespace(stale_heartbeat_s=600, fleet_limit=20, brief_body_warn_chars=4000)
        ),
    )
    return harness, registry, ledger


async def _comms(harness: Any, **kwargs: Any) -> str:
    return str(await AppContext.comms(harness, **kwargs))


# =========================================================================== #
# A2 — #104 TYPED APPLICABILITY: the publish render receives what is TRUE
# (auto_ack_at_register), never a NAME it compares (server.py:4936).
#
# The discriminating fixtures are the whole point: a brief LITERALLY NAMED
# 'project' with the flag FALSE MUST render the brief_ack tail; a non-'project'
# brief with the flag TRUE MUST render the register tail. A build that compares
# ``result.brief.name`` inside the render FAILS BOTH — the parameter-value
# diversity the repo law demands ("if the code can branch on a value, at least
# one pin uses a DIFFERENT value").
# =========================================================================== #


class TestFirstVersionTailIsTypedNotNameDerived:
    """§9.4 first-version tail (audit instance EIGHT) — the render must branch
    on the typed ``auto_ack_at_register``, never re-derive it from the name."""

    def test_flag_true_renders_the_register_tail(self) -> None:
        result = _publish_result(name="wave9", version=1, first_version=True)
        rendered = str(
            AppContext._render_comms_brief_publish(
                result,
                behind=[],
                body_chars=10,
                warn_threshold_chars=4000,
                session=None,
                auto_ack_at_register=True,
            )
        )
        assert "first version; agents ack at register" in rendered
        assert "action=brief_ack" not in rendered

    def test_flag_false_renders_the_brief_ack_tail(self) -> None:
        result = _publish_result(name="wave9", version=1, first_version=True)
        rendered = str(
            AppContext._render_comms_brief_publish(
                result,
                behind=[],
                body_chars=10,
                warn_threshold_chars=4000,
                session=None,
                auto_ack_at_register=False,
            )
        )
        assert "first version; agents ack with lore_comms action=brief_ack" in rendered
        assert "ack at register" not in rendered

    def test_DISCRIMINATOR_project_named_but_flag_false_renders_brief_ack(self) -> None:
        """The anti-name-comparison pin: name IS 'project' but the flag is
        FALSE. A build comparing ``result.brief.name == BRIEF_NAME_PROJECT``
        renders 'ack at register' here and FAILS."""
        result = _publish_result(name="project", version=1, first_version=True)
        rendered = str(
            AppContext._render_comms_brief_publish(
                result,
                behind=[],
                body_chars=10,
                warn_threshold_chars=4000,
                session=None,
                auto_ack_at_register=False,
            )
        )
        assert "agents ack with lore_comms action=brief_ack" in rendered
        assert "ack at register" not in rendered, (
            "the render re-derived applicability from the NAME 'project' instead "
            f"of the typed flag (#104): {rendered!r}"
        )

    def test_DISCRIMINATOR_non_project_named_but_flag_true_renders_register(self) -> None:
        """The mirror: name is NOT 'project' but the flag is TRUE. A build
        comparing the name renders 'brief_ack' here and FAILS."""
        result = _publish_result(name="wave9", version=1, first_version=True)
        rendered = str(
            AppContext._render_comms_brief_publish(
                result,
                behind=[],
                body_chars=10,
                warn_threshold_chars=4000,
                session=None,
                auto_ack_at_register=True,
            )
        )
        assert "agents ack at register" in rendered
        assert "action=brief_ack" not in rendered, (
            "the render re-derived applicability from the NAME 'wave9' instead of "
            f"the typed flag (#104): {rendered!r}"
        )


# =========================================================================== #
# B — #103 THREE NAME-CONDITIONED SKEW TAILS (§9.4, audit instance NINE).
#
# THE QUANTIFIER LAW (repo CLAUDE.md): pin the tail ∀ (is-standing, has-unbriefed)
# and FORCE each fate with a fixture — never condition the invariant on the
# debugged mode. The four combinations, each forced:
#   (standing,     has_unbriefed) -> tail 1  "; surfaces at their next heartbeat or drain"
#   (standing,     no_unbriefed)  -> tail 1
#   (non-standing, no_unbriefed)  -> tail 2  "; surfaces at their next heartbeat or drain"
#   (non-standing, has_unbriefed) -> tail 3  "; ackers see it at next heartbeat or drain — ..."
# ``auto_ack_at_register`` carries is-standing (coextensive with the standing
# role — see the report's contract-decision on the flag naming); ``has_unbriefed``
# is derived by the render from ``behind`` (an entry with acked_version=None).
# =========================================================================== #

# ONE IMPLEMENTATION (repo CLAUDE.md §ONE IMPLEMENTATION) — the SINGLE test-side
# home of the skew block's surfacing teach. Every assertion in this package that
# pins the served wording imports these two names rather than re-typing the
# sentence (`test_comms_tool`, `test_comms_promise_registry`, `test_comms_wiring`);
# server.py carries the only other authoritative copies, and the promise registry
# keys them byte-exactly, so a drift in EITHER direction goes RED.
#
# WORDING AUTHORITY: design ruling E-S5(c) (`docs/plans/v2/03b-design-rulings-r2.md`
# §G, committed `aa25e79`) — the block is served by heartbeat AND, per FK-6, by
# drain, so naming `heartbeat` alone taught the wrong verb to the agent consumer
# the trust doctrine protects.
# NAMED RE-OPEN TRIGGER (E-S5(c), verbatim intent): any packet 04/05 verb that also
# surfaces this block re-opens the wording — do NOT accrete a verb list past two; at
# a THIRD surfacing verb, reword to name the mechanism generically. Because every
# test-side pin reads these two constants, discharging that trigger is a change to
# TWO strings here plus server.py's four literals, not a fifty-site sweep.
_SKEW_SURFACING_TEACH = "surfaces at their next heartbeat or drain"
_SKEW_ACKER_TEACH = "ackers see it at next heartbeat or drain"

_TAIL_SURFACES = f"; {_SKEW_SURFACING_TEACH}"
_TAIL3_TEMPLATE = (
    f"; {_SKEW_ACKER_TEACH} {_EM_DASH} unbriefed agents only via brief_get name='{{name}}'"
)

_BEHIND_ACKER_ONLY = [
    BriefBehindEntry(agent_name="a", acked_version=1),
    BriefBehindEntry(agent_name="b", acked_version=1),
]
_BEHIND_WITH_UNBRIEFED = [
    BriefBehindEntry(agent_name="a", acked_version=1),
    BriefBehindEntry(agent_name="c", acked_version=None),
]


class TestSkewTailIsNameConditioned:
    """§9.4's tail is ONE of three literals, conditioned on exactly where the
    heartbeat mechanism runs (§5.3 mechanism-promise corollary)."""

    def _render(self, *, name: str, version: int, behind: list[BriefBehindEntry], standing: bool) -> str:
        result = _publish_result(name=name, version=version, first_version=False)
        return str(
            AppContext._render_comms_brief_publish(
                result,
                behind=behind,
                body_chars=10,
                warn_threshold_chars=4000,
                session=None,
                auto_ack_at_register=standing,
            )
        )

    def test_standing_with_unbriefed_uses_tail_1(self) -> None:
        rendered = self._render(
            name="project", version=2, behind=_BEHIND_WITH_UNBRIEFED, standing=True
        )
        assert rendered.endswith(_TAIL_SURFACES), rendered
        assert _SKEW_ACKER_TEACH not in rendered

    def test_standing_without_unbriefed_uses_tail_1(self) -> None:
        rendered = self._render(name="project", version=2, behind=_BEHIND_ACKER_ONLY, standing=True)
        assert rendered.endswith(_TAIL_SURFACES), rendered
        assert _SKEW_ACKER_TEACH not in rendered

    def test_nonstanding_without_unbriefed_uses_tail_2(self) -> None:
        rendered = self._render(name="wave9", version=2, behind=_BEHIND_ACKER_ONLY, standing=False)
        assert rendered.endswith(_TAIL_SURFACES), rendered
        assert _SKEW_ACKER_TEACH not in rendered

    def test_nonstanding_with_unbriefed_uses_tail_3_naming_the_brief(self) -> None:
        rendered = self._render(
            name="wave9", version=2, behind=_BEHIND_WITH_UNBRIEFED, standing=False
        )
        assert rendered.endswith(_TAIL3_TEMPLATE.format(name="wave9")), rendered
        assert _SKEW_SURFACING_TEACH not in rendered

    def test_DISCRIMINATOR_project_named_but_flag_false_with_unbriefed_uses_tail_3(self) -> None:
        """Name IS 'project' but the standing flag is FALSE and an unbriefed
        agent is behind: the tail MUST be tail 3 (non-standing). A build that
        keys the tail off ``name == 'project'`` renders tail 1 and FAILS —
        and it names the brief 'project' in the tail 3 teach, from the value,
        not a comparison."""
        rendered = self._render(
            name="project", version=2, behind=_BEHIND_WITH_UNBRIEFED, standing=False
        )
        assert rendered.endswith(_TAIL3_TEMPLATE.format(name="project")), rendered
        assert _SKEW_SURFACING_TEACH not in rendered, (
            "the skew tail re-derived standingness from the NAME 'project' instead "
            f"of the typed flag (#103/#104): {rendered!r}"
        )


# =========================================================================== #
# A1 — #104 NAME THE ROLE via ONE accessor. Prove sharing BY MUTATION (repo
# ONE-implementation law): change the standing-brief definition in ONE place
# (monkeypatch ``server.STANDING_BRIEF``) and EVERY surface must follow. A
# surface that keeps its own ``== BRIEF_NAME_PROJECT`` copy goes RED here.
#
# Each surface is its own test, so a HALF-DRY build (one surface centralised,
# another not) gets a precise red naming exactly which surface leaked.
#
# raising=False: today's code has no ``STANDING_BRIEF`` symbol and keys off
# ``BRIEF_NAME_PROJECT``, so the patch is inert and the surface treats 'project'
# (not 'governance') as standing — the assertion then fails for the RIGHT reason.
# =========================================================================== #

_ROLE = "governance"  # a novel standing-brief name, distinct from 'project'


def _install_role(monkeypatch: pytest.MonkeyPatch) -> None:
    import loremaster.server as server_module

    monkeypatch.setattr(server_module, "STANDING_BRIEF", _ROLE, raising=False)


class TestStandingBriefIsOneSharedRole:
    """All four standing-brief surfaces route through ONE named role — proven
    by mutating the role and asserting each surface follows it."""

    async def test_register_auto_acks_the_role_not_a_hardcoded_project(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_role(monkeypatch)
        harness, _registry, ledger = _harness()
        await ledger.publish(_ROLE, "the standing law", created_by="lead")
        rendered = await _comms(
            harness, action="register", agent="fixer-b", session="wave7", role="builder"
        )
        assert f"brief '{_ROLE}' v1" in rendered, (
            "register did not auto-serve the standing ROLE brief — it is still "
            f"hardcoded to 'project' (#104): {rendered!r}"
        )
        assert "ack recorded (via register)" in rendered

    async def test_heartbeat_universal_skew_tracks_the_role(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_role(monkeypatch)
        harness, _registry, ledger = _harness()
        await ledger.publish(_ROLE, "v1 body", created_by="lead")
        await _comms(harness, action="register", agent="fixer-b", session="wave7", role="builder")
        # Bump the role's head past the register-time auto-ack.
        await ledger.publish(_ROLE, "v2 body", created_by="lead")
        rendered = await _comms(harness, action="heartbeat", agent="fixer-b", session="wave7")
        # The STANDING (universal) skew line's LABEL stays the literal word
        # 'project' (§9.2 byte-stable); the mutation proof is that its VERSIONS
        # track the role (governance: head v2, acked v1). Today's code reads
        # BRIEF_NAME_PROJECT (no such brief), so NO standing skew line renders.
        assert "v2 is head — you acked v1; catch up: lore_comms action=brief_get" in rendered, (
            "heartbeat's universal skew is still hardcoded to the 'project' brief, not "
            f"the standing role (#104): {rendered!r}"
        )

    async def test_fleet_project_column_tracks_the_role(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_role(monkeypatch)
        harness, _registry, ledger = _harness()
        await ledger.publish(_ROLE, "v1 body", created_by="lead")
        await _comms(harness, action="register", agent="fixer-b", session="wave7", role="builder")
        await ledger.publish(_ROLE, "v2 body", created_by="lead")
        rendered = await _comms(harness, action="fleet", agent="fixer-b", session="wave7")
        # The COLUMN label stays the literal word 'project' (§9.6), but the cell
        # tracks the standing role: acked v1, head v2. Today's code reads
        # BRIEF_NAME_PROJECT (no such brief exists) and OMITS the cell entirely.
        assert "project v1 (head v2)" in rendered, (
            "fleet's ack column is still hardcoded to the 'project' brief (#104): "
            f"{rendered!r}"
        )

    async def test_publish_first_version_tail_tracks_the_role(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_role(monkeypatch)
        harness, _registry, ledger = _harness()
        await _comms(harness, action="register", agent="lead", session="wave7", role="lead")
        rendered = await _comms(
            harness,
            action="brief_publish",
            agent="lead",
            session="wave7",
            name=_ROLE,
            body="the standing law",
        )
        assert "first version; agents ack at register" in rendered, (
            "the first-version tail's 'ack at register' promise is still keyed off "
            f"the NAME 'project' instead of the standing role (#104): {rendered!r}"
        )


# =========================================================================== #
# #103 — HEARTBEAT SURFACES SUBSCRIBED NON-'project' NAME SKEW (§9.2 v8).
# End-to-end through the real dispatcher + fakes; asserts on the served string
# only (no internal type referenced), so RED = the handler reads only 'project'.
# =========================================================================== #


async def _register(harness: Any, name: str, session: str = "wave7", role: str = "builder") -> None:
    await _comms(harness, action="register", agent=name, session=session, role=role)


async def _publish(harness: Any, agent: str, name: str, session: str = "wave7") -> None:
    await _comms(
        harness, action="brief_publish", agent=agent, session=session, name=name, body=f"{name} body"
    )


class TestHeartbeatSurfacesSubscribedNameSkew:
    """§9.2 v8: after the 'project' line, ONE line per SUBSCRIBED non-project
    name with acked<head, with the EXPLICIT ``name=`` teach; UNSUBSCRIBED
    non-project names are NEVER mentioned; 'project' skew stays byte-stable."""

    async def test_subscribed_behind_name_surfaces_with_explicit_name_teach(self) -> None:
        harness, _registry, _ledger = _harness()
        await _register(harness, "author")
        # author subscribes to wave9 by publishing v1 (self-ack via='publish').
        await _publish(harness, "author", "wave9")
        # lead bumps wave9 to v3 — author now behind (acked v1, head v3).
        await _register(harness, "lead", role="lead")
        await _publish(harness, "lead", "wave9")
        await _publish(harness, "lead", "wave9")
        rendered = await _comms(harness, action="heartbeat", agent="author", session="wave7")
        assert (
            f"brief 'wave9' v3 is head {_EM_DASH} you acked v1; "
            "catch up: lore_comms action=brief_get name='wave9'"
        ) in rendered, (
            "heartbeat did not surface the subscribed non-'project' brief skew "
            f"(#103 / instance 9): {rendered!r}"
        )

    async def test_unsubscribed_non_project_name_is_never_mentioned(self) -> None:
        """The naive-generalization guard: an agent that NEVER acked 'wave9' is
        not behind on it (§5.3 subscription) — nagging it is the noise failure a
        naive 'skew for every published name' build would produce."""
        harness, _registry, _ledger = _harness()
        await _register(harness, "bystander")
        await _register(harness, "lead", role="lead")
        # wave9 exists and moves, but 'bystander' never acked it.
        await _publish(harness, "lead", "wave9")
        await _publish(harness, "lead", "wave9")
        rendered = await _comms(harness, action="heartbeat", agent="bystander", session="wave7")
        assert "wave9" not in rendered, (
            "heartbeat nagged an UNSUBSCRIBED agent about 'wave9' — subscription "
            f"bound violated (§5.3): {rendered!r}"
        )

    async def test_project_unbriefed_is_still_noticed_universally(self) -> None:
        """'project' is UNIVERSALLY subscribed — even a project-unbriefed agent
        gets its notice (register-before-project-brief bootstrap path)."""
        harness, _registry, _ledger = _harness()
        # Register BEFORE any project brief -> no auto-ack -> unbriefed on project.
        await _register(harness, "early")
        await _register(harness, "lead", role="lead")
        await _publish(harness, "lead", "project")
        rendered = await _comms(harness, action="heartbeat", agent="early", session="wave7")
        assert "project" in rendered and "not acked" in rendered, (
            f"project-unbriefed universal notice regressed: {rendered!r}"
        )

    async def test_ninth_instances_promise_is_true_end_to_end(self) -> None:
        """The ninth's promise, proven where it is MADE (spec §TEST SKETCH):
        publish wave9 v2, then a prior acker's NEXT heartbeat (through the real
        tool) actually surfaces wave9 — the skew tail 'surfaces at their next
        heartbeat or drain' was a lie for non-'project' names until this ran.
        The heartbeat leg is the one driven here; the drain leg (FK-6) is pinned
        with the drain surface."""
        harness, _registry, _ledger = _harness()
        await _register(harness, "acker")
        await _publish(harness, "acker", "wave9")  # acker subscribes at v1
        await _register(harness, "lead", role="lead")
        await _publish(harness, "lead", "wave9")  # head -> v2
        rendered = await _comms(harness, action="heartbeat", agent="acker", session="wave7")
        assert "wave9" in rendered and "v2 is head" in rendered, (
            "publish promised the straggler would see wave9 at its next heartbeat "
            f"or drain, and the heartbeat did not deliver it (#103): {rendered!r}"
        )

    def test_over_cap_subscribed_skews_collapse_ordered_by_magnitude(self) -> None:
        """§9.2 v8 CAP + collapse + ORDER (the adversary-found gap): with MORE
        than ``_HEARTBEAT_SKEW_NAMES_CAP`` subscribed-behind non-'project'
        names, the heartbeat renders EXACTLY the cap-many LARGEST-skew names as
        individual per-name lines, skew-DESCENDING, then ONE counted collapse
        line naming the remainder — and the smaller-skew names never appear as
        individual lines.

        Driven at the render directly (like ``TestSkewTailIsNameConditioned``),
        NOT through the dispatcher, on purpose: ``BriefLedger.subscribed_name_skew``
        returns skews in arbitrary store order, so only a CONTROLLED input order
        that DIFFERS from skew-descending can prove the render itself sorts.
        Every sibling fixture holds ≤1 subscribed-behind name, so this
        cap/collapse/order branch was dead code no test reached — two wrong
        builds (``_HEARTBEAT_SKEW_NAMES_CAP`` raised to 99 → never collapses; the
        skew-descending sort removed → store order) each passed the FULL render
        contract with zero failures (REPORT-pkt02-adversary.md §"surviving wrong
        builds"; the pass COUNT it reported is not restated here — the suite has
        since changed shape and no in-tree instrument reproduces it).

        RED before 17277d1: ``_render_comms_heartbeat`` had no
        ``subscribed_skew`` parameter ⇒ ``TypeError`` (the right RED). The
        cap/coverage constants are read only AFTER that call, so the pre-fix
        tree — which had no ``_HEARTBEAT_SKEW_NAMES_CAP`` symbol — never
        reached them.
        """
        import loremaster.server as server_module

        # Five subscribed-and-behind non-'project' briefs, DISTINCT skews, and
        # every head/acked number distinct (no small-N / arithmetic-alignment
        # coincidence a sort-by-head, sort-by-acked, or count-not-version build
        # could ride). Names are chosen so ALPHABETICAL order is neither the same
        # as nor the reverse of skew order. The input order below is deliberately
        # scrambled — neither skew-ascending nor -descending — so a render that
        # emits store/input order (no sort) picks the WRONG names as individuals.
        subscribed_skew: list[tuple[str, int, int]] = [
            ("zeta", 26, 23),   # skew 3
            ("mike", 30, 25),   # skew 5  <- largest
            ("romeo", 19, 18),  # skew 1  <- smallest
            ("alpha", 28, 24),  # skew 4
            ("delta", 22, 20),  # skew 2
        ]
        agent = SimpleNamespace(name="fixer-b", status="active")

        # First production touch — RED here (TypeError, missing kwarg) against a
        # clean tree, BEFORE any constant lookup.
        rendered = str(
            AppContext._render_comms_heartbeat(
                agent,
                project_head_version=None,  # no 'project' skew line: isolate the mechanism
                project_acked_version=None,
                subscribed_skew=subscribed_skew,
            )
        )

        skew_cap = server_module._HEARTBEAT_SKEW_NAMES_CAP
        coverage_cap = server_module._COVERAGE_NAMES_CAP
        # Precondition AND the cap-not-binding kill in one: the fixture must have
        # at least cap + 2 subscribed skews so >cap names force a plural collapse.
        # A build whose per-name cap is >= the number of subscribed skews (e.g.
        # _HEARTBEAT_SKEW_NAMES_CAP raised to 99) NEVER collapses, so every agent
        # behind on many briefs gets unbounded per-name heartbeat spam (#103) —
        # that build fails HERE, naming the non-binding cap. If a smaller cap was
        # deliberately raised at/above the fixture size, grow the fixture instead.
        assert len(subscribed_skew) >= skew_cap + 2, (
            "_HEARTBEAT_SKEW_NAMES_CAP does not bind on this fixture: a cap >= the "
            "number of subscribed skews never collapses and spams every heartbeat "
            "(#103) — grow the fixture only if the cap was deliberately raised: "
            f"cap={skew_cap}, subscribed_skews={len(subscribed_skew)}"
        )

        ordered = sorted(subscribed_skew, key=lambda row: (-(row[1] - row[2]), row[0]))
        shown, remainder = ordered[:skew_cap], ordered[skew_cap:]

        def _skew_line(name: str, head: int, acked: int) -> str:
            return (
                f"brief '{name}' v{head} is head {_EM_DASH} you acked v{acked}; "
                f"catch up: lore_comms action=brief_get name='{name}'"
            )

        # ORDER: exactly the cap-many largest skews, skew-DESCENDING, as one
        # contiguous block — a store-order (no-sort) build renders other names
        # here and FAILS.
        shown_block = "\n".join(_skew_line(*row) for row in shown)
        assert shown_block in rendered, (
            "heartbeat did not render the top-cap subscribed skews in "
            f"skew-descending order (#103 order gap): {rendered!r}"
        )
        # CAP: no MORE than the cap individual per-name lines — a build that
        # raised the cap (never collapses) renders one per name and FAILS. The
        # per-name teach carries the explicit ``name=``; the bare-'project' skew
        # line (absent here) and the collapse line do not, so this counts only
        # the individual non-project skew lines.
        name_line_count = rendered.count("catch up: lore_comms action=brief_get name=")
        assert name_line_count == skew_cap, (
            "heartbeat rendered a per-name skew line for MORE than "
            f"_HEARTBEAT_SKEW_NAMES_CAP={skew_cap} names (counted {name_line_count}) — "
            f"the cap never collapsed (unbounded heartbeat spam, #103): {rendered!r}"
        )
        # COLLAPSE: the smaller-skew remainder is ABSENT as individual lines...
        for name, head, acked in remainder:
            assert _skew_line(name, head, acked) not in rendered, (
                f"over-cap brief '{name}' leaked as an individual skew line "
                f"instead of collapsing (#103): {rendered!r}"
            )
        # ...and appears ONLY in ONE counted collapse line naming the remainder
        # (names capped _COVERAGE_NAMES_CAP, '(+{j} more)' suffix when over — both
        # derived from the constants, never hardcoded).
        remainder_names = [row[0] for row in remainder]
        names_text = ", ".join(remainder_names[:coverage_cap])
        if len(remainder_names) > coverage_cap:
            names_text += f" (+{len(remainder_names) - coverage_cap} more)"
        collapse_line = (
            f"behind on {len(remainder_names)} more briefs: {names_text} "
            f"{_EM_DASH} brief_get each by name"
        )
        assert collapse_line in rendered, (
            "heartbeat did not counted-collapse the over-cap remainder into one "
            f"line (#103): expected {collapse_line!r} in {rendered!r}"
        )


# =========================================================================== #
# #104 STRUCTURAL — a RENDER helper must NEVER reference the standing-brief NAME
# CONSTANT: renders receive TYPED applicability, they never name the role.
# This catches the `== BRIEF_NAME_PROJECT` comparison at server.py:4936 (an
# ``ast.Name`` load of the constant inside ``_render_comms_brief_publish``) while
# allowing legitimate 'project' STRING LITERALS in teaching templates (the
# byte-stable project skew/bootstrap lines are prose, not a name comparison).
# =========================================================================== #

_BANNED_NAME_CONSTANTS: frozenset[str] = frozenset({"BRIEF_NAME_PROJECT", "STANDING_BRIEF"})


def _render_helper_name_constant_refs() -> list[tuple[str, int, str]]:
    """Every ``ast.Name``/``ast.Attribute`` load of a banned name-constant that
    appears TEXTUALLY inside a ``_render_comms_*`` function in server.py."""
    source = (_PACKAGE_ROOT / "server.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="server.py")
    offenders: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if not node.name.startswith("_render_comms"):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and sub.id in _BANNED_NAME_CONSTANTS:
                offenders.append((node.name, sub.lineno, sub.id))
            elif isinstance(sub, ast.Attribute) and sub.attr in _BANNED_NAME_CONSTANTS:
                offenders.append((node.name, sub.lineno, sub.attr))
    return offenders


class TestRendersNeverNameTheStandingBriefConstant:
    """#104 part 2, structural: renders receive typed applicability; a render
    that names the standing-brief constant is re-deriving a role from a name."""

    def test_no_render_helper_references_a_standing_brief_name_constant(self) -> None:
        offenders = _render_helper_name_constant_refs()
        assert not offenders, (
            "a comms render helper references a standing-brief NAME CONSTANT — it "
            "must take typed applicability (auto_ack_at_register) instead (#104):\n"
            + "\n".join(f"  {fn}:{line}: {name}" for fn, line, name in offenders)
        )

    def test_the_scanner_actually_reaches_the_render_helpers(self) -> None:
        """Coverage is a CHECKED variable (repo law): prove the scan reached the
        render surface, so a rename/removal of the helpers cannot make the pin
        vacuously pass by scanning nothing."""
        source = (_PACKAGE_ROOT / "server.py").read_text(encoding="utf-8")
        tree = ast.parse(source, filename="server.py")
        render_helpers = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name.startswith("_render_comms")
        }
        assert "_render_comms_brief_publish" in render_helpers
        assert len(render_helpers) >= 8, render_helpers


# =========================================================================== #
# #100 — REMOVE ``created_by`` from ``AppContext.comms``. The acting agent IS
# the author (#98's self-ack already asserts this). Removed-behavior inventory
# (repo DUAL law) in REPORT-pkt02-contract.md §C: DROPPED-DELIBERATELY, test-only
# affordance, no production caller (the MCP tool never sent it).
# =========================================================================== #


class TestCreatedByIsGoneFromTheDispatcher:
    def test_comms_signature_has_no_created_by(self) -> None:
        params = inspect.signature(AppContext.comms).parameters
        assert "created_by" not in params, (
            "AppContext.comms still accepts created_by — it splits identity "
            "(author X vs. self-ack for acting agent Y) and is a test-only "
            "affordance the MCP tool never sends (#100)"
        )

    async def test_publish_records_the_acting_agent_as_author(self) -> None:
        """With created_by gone, the recorded author IS the acting agent — the
        one contract that wanted a different author registers+publishes AS it."""
        harness, _registry, _ledger = _harness()
        await _register(harness, "fixer-b")
        rendered = await _comms(
            harness, action="brief_publish", agent="fixer-b", session="wave7", name="project", body="b"
        )
        assert f"published by {render_attributed('fixer-b')}" in rendered, rendered


# =========================================================================== #
# FLEET CELL RENAME (§9.6 / v8 item-4): `brief v{n}` -> `project v{n}`. The cell
# label must name the set it describes now that non-'project' briefs are
# first-class. Byte pins flip; the RETIRED string must not appear in the fleet
# render — a BARE, anchor-free dead-name scan (repo rename-sweep law).
# =========================================================================== #


class TestFleetCellIsLabelledProject:
    async def _fleet_row(self, *, acked: int | None, head: int) -> str:
        """Build a fleet where 'fixer-b' is acked at ``acked`` (None = unbriefed)
        while 'project' head is ``head``. Register-time auto-ack pins fixer-b at
        whatever the head was WHEN IT REGISTERED, so the sequence is what sets
        its ack level — not a later brief_ack (an idempotent no-op past the
        auto-ack)."""
        harness, _registry, _ledger = _harness()
        await _register(harness, "lead", role="lead")
        if acked is None:
            # Register BEFORE any project brief -> no auto-ack -> unbriefed.
            await _register(harness, "fixer-b")
            for _ in range(head):
                await _publish(harness, "lead", "project")
        else:
            for _ in range(acked):
                await _publish(harness, "lead", "project")
            await _register(harness, "fixer-b")  # auto-acks at the current head (`acked`)
            for _ in range(head - acked):
                await _publish(harness, "lead", "project")
        rendered = await _comms(harness, action="fleet", agent="lead", session="wave7")
        row = next(line for line in rendered.splitlines() if line.startswith("- fixer-b"))
        return row

    async def test_current_cell_says_project_not_brief(self) -> None:
        row = await self._fleet_row(acked=2, head=2)
        assert "project v2" in row, row
        assert "brief v" not in row, f"retired 'brief v' cell wording still present: {row!r}"

    async def test_behind_cell_says_project(self) -> None:
        row = await self._fleet_row(acked=1, head=2)
        assert "project v1 (head v2)" in row, row
        assert "brief v" not in row, row

    async def test_unbriefed_cell_says_project(self) -> None:
        row = await self._fleet_row(acked=None, head=2)
        assert "project unbriefed" in row, row
        assert "brief unbriefed" not in row, row

    async def test_no_retired_brief_cell_wording_anywhere_in_the_fleet_render(self) -> None:
        """Bare anchor-free dead-name scan over the WHOLE fleet render (repo
        rename-sweep law): neither 'brief v' nor 'brief unbriefed' may survive."""
        harness, _registry, ledger = _harness()
        await _register(harness, "lead", role="lead")
        await _publish(harness, "lead", "project")
        await _publish(harness, "lead", "project")
        await _register(harness, "fixer-b")  # unbriefed on project
        rendered = await _comms(harness, action="fleet", agent="lead", session="wave7")
        assert "brief v" not in rendered, rendered
        assert "brief unbriefed" not in rendered, rendered
