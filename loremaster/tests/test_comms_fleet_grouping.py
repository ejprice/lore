"""Contract tests for ``lore_comms`` ``fleet``'s per-session grouping — PKT-28
C1 fix-wave defect 2.

Spec: ``docs/design/2026-07-12-pkt28-c1-semantics.md`` §6: "When >1 session is
in scope, group by session under a per-session header line rather than
interleaving." ``AppContext._render_comms_fleet`` ships WITHOUT this today —
its own docstring names the gap as a deliberately-deferred "growth point, not
a regression" — but it is a real correctness defect, not a nicety: fleet row
grammar (§9.6) carries no session cell, and agent identity is
``uuid5(session:name)`` — names are unique only PER SESSION. Calling
``fleet`` with ``session`` omitted spans every session, so two genuinely
different agents that happen to share a name in two different sessions
render as the SAME, indistinguishable row today. That is a confident-wrong
render (DESIGN-LAW §1.3/§1.4), not a missing convenience.

This module is independently collectible (own local ``_agent``/``_fleet_
window``/``_render`` fixtures — mirrors the sibling C1 contract files' own
stated "independently collectible" property, e.g. ``test_comms_tool.py``'s
module docstring) and owns exactly the grouping law + its interaction with
the existing ordering/elision laws (spec §6, fix-wave defect 3) + a hostile
session-name fixture. The three-status-precedence law, the counted-elision-
reask clamp, and the retired trailer are ALREADY pinned in
``test_comms_tool.py::TestRenderCommsFleet`` (untouched here except for two
gap-pins added there: heartbeat-recency-within-a-status and elision-cuts-
from-the-bottom, both single-session) — this module only pins what changes
or newly matters once >1 session is in scope.

DECISION FLAGGED (no spec literal exists for this — see
``REPORT-c1-contract-fixwave.md``): the per-session header line's exact
grammar (``"session {session}:"``) and the group-ordering rule (alphabetical
by session name) are THIS report's proposed contract, not a spec-dictated
grammar — the implementer builds to what this file pins; the lead/operator
may override the literal wording.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from _comms_fakes import FakeAgentRegistry
from loremaster.agents import Agent, AgentFleetWindow
from loremaster.server import AppContext
from render_injection_scaffold import (
    _INJECTION_THREAT_CHARS,
    _ROW_FORGE_PAYLOAD,
    assert_render_injection_safe,
)


def _agent(
    *,
    name: str = "fixer-b",
    session: str = "wave7",
    role: str = "builder",
    status: str = "active",
    heartbeat_at: datetime | None = None,
) -> Agent:
    now = datetime.now(UTC)
    return Agent(
        id=FakeAgentRegistry._agent_id(session, name),
        name=name,
        session=session,
        role=role,
        model=None,
        status=status,  # type: ignore[arg-type]
        spawned_by=None,
        task_id=None,
        checkpoint=None,
        last_note=None,
        registered_at=now,
        heartbeat_at=heartbeat_at if heartbeat_at is not None else now,
    )


def _fleet_window(rows: list[Agent], *, retired_count: int = 0) -> AgentFleetWindow:
    return AgentFleetWindow(rows=rows, retired_count=retired_count, total_non_retired=len(rows))


def _status_counts(rows: list[Agent], *, retired_count: int = 0) -> dict[str, int]:
    """TRUE per-status aggregate over ``rows`` (this module's fixtures never
    carry a non-zero ``retired_count`` -- see ``_fleet_window``'s sole call
    site below -- so this always agrees with the window-derived arithmetic
    it replaces; ``"retired"`` is present-with-zero, never absent)."""
    counts = {"input_required": 0, "active": 0, "idle": 0, "retired": retired_count}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    return counts


def _render(rows: list[Agent], *, session: str | None = None, limit: int = 20) -> str:
    return str(
        AppContext._render_comms_fleet(
            _fleet_window(rows),
            session=session,
            limit=limit,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
            status_counts=_status_counts(rows),
        )
    )


class TestFleetMultiSessionGrouping:
    """spec §6: >1 session in scope -> per-session header lines, rows
    grouped beneath, never interleaved; exactly 1 session in scope -> the
    existing flat rendering (no redundant header)."""

    def test_two_sessions_same_agent_name_render_unambiguously(self) -> None:
        """THE broken case today: two DIFFERENT agents share a name across
        two sessions; fleet(session=None) renders them with no attribution
        at all. Grouping must make each agent's session unambiguous."""
        now = datetime.now(UTC)
        wave7_row = _agent(
            name="fixer-b", session="wave7", status="idle", heartbeat_at=now - timedelta(minutes=5)
        )
        wave8_row = _agent(name="fixer-b", session="wave8", status="active", heartbeat_at=now)
        rendered = _render([wave7_row, wave8_row], session=None)
        assert "session wave7:" in rendered
        assert "session wave8:" in rendered
        wave7_section, _, wave8_section = rendered.partition("session wave8:")
        assert "[idle]" in wave7_section
        assert "[active]" not in wave7_section
        assert "[active]" in wave8_section

    def test_single_session_in_scope_has_no_redundant_header(self) -> None:
        # session=None (unscoped call) but only ONE distinct session is
        # actually present in the roster -- no redundant group header.
        rows = [_agent(name="a", session="wave7"), _agent(name="b", session="wave7")]
        rendered = _render(rows, session=None)
        assert "session wave7:" not in rendered

    def test_explicit_session_filter_never_groups(self) -> None:
        # An explicit session= scope already tells the caller which session
        # they're looking at -- a redundant per-row header would be noise;
        # the existing flat shape + top-level "(session wave7)" tag stands.
        rows = [_agent(name="a", session="wave7"), _agent(name="b", session="wave7")]
        rendered = _render(rows, session="wave7")
        assert "session wave7:" not in rendered
        assert "fleet (session wave7):" in rendered

    def test_group_order_is_alphabetical_by_session(self) -> None:
        rows = [_agent(name="a", session="zeta"), _agent(name="b", session="alpha")]
        rendered = _render(rows, session=None)
        assert "session alpha:" in rendered
        assert "session zeta:" in rendered
        assert rendered.index("session alpha:") < rendered.index("session zeta:")

    def test_ordering_within_a_group_survives_grouping(self) -> None:
        """fix-wave defect 3: input_required -> active -> idle must hold
        WITHIN each session group once grouping is added, not just globally."""
        now = datetime.now(UTC)
        rows = [
            _agent(name="idle-1", session="wave7", status="idle", heartbeat_at=now),
            _agent(name="active-1", session="wave7", status="active", heartbeat_at=now),
            _agent(name="parked-1", session="wave7", status="input_required", heartbeat_at=now),
            _agent(name="other", session="wave8", status="active", heartbeat_at=now),
        ]
        rendered = _render(rows, session=None)
        assert "session wave7:" in rendered
        assert "session wave8:" in rendered
        wave7_section = rendered.split("session wave8:")[0]
        assert wave7_section.index("parked-1") < wave7_section.index("active-1") < wave7_section.index(
            "idle-1"
        )

    def test_elision_stays_honest_across_grouped_rows(self) -> None:
        """fix-wave defect 3: '+K more' must stay honest when the shown/
        elided rows span >1 session group."""
        now = datetime.now(UTC)
        rows = [_agent(name=f"a{i}", session="wave7", status="active", heartbeat_at=now) for i in range(2)]
        rows += [_agent(name=f"b{i}", session="wave8", status="active", heartbeat_at=now) for i in range(2)]
        rendered = _render(rows, session=None, limit=2)
        assert "+2 more" in rendered

    def test_elision_survival_is_global_priority_not_per_group_position(self) -> None:
        """A genuine interaction spec §6's text does not resolve explicitly
        (flagged in the report as a decision, not a spec-dictated grammar):
        does grouping partition rows BEFORE deciding who survives a tight
        limit, or does survival stay a GLOBAL status/heartbeat priority with
        grouping applied only to the SURVIVORS for display? This test pins
        the latter: a parked row in an alphabetically-LATER session must
        still outrank (and survive ahead of) an idle row in an
        alphabetically-EARLIER session. A naive 'flatten groups in
        alphabetical order, then slice' implementation would elide the
        parked row instead -- silently reintroducing defect 3's 'idle/
        oldest out first' break the moment >1 session is in scope. Passes
        today (grouping doesn't exist yet, so today's flat global sort
        already gets this right by construction) -- a forward guard against
        the specific way a naive grouping fix could regress it, not a
        currently-red defect proof."""
        now = datetime.now(UTC)
        rows = [
            _agent(name="idle-in-alpha", session="alpha", status="idle", heartbeat_at=now),
            _agent(name="parked-in-zeta", session="zeta", status="input_required", heartbeat_at=now),
        ]
        rendered = _render(rows, session=None, limit=1)
        assert "parked-in-zeta" in rendered
        assert "idle-in-alpha" not in rendered
        assert "+1 more" in rendered


class TestFleetGroupHeaderHostileSession:
    """A hostile SESSION name must not be able to forge a fleet group header
    -- the brief-base §3 hostile-fixture law, extended to this NEW render
    surface (the pre-fix code never rendered per-row session text at all, so
    this exact threat surface did not previously exist)."""

    @pytest.mark.parametrize("threat", _INJECTION_THREAT_CHARS, ids=lambda t: f"U+{ord(t):04X}")
    def test_hostile_session_cannot_forge_a_group_header_row(self, threat: str) -> None:
        hostile_session = f"benign{threat}{_ROW_FORGE_PAYLOAD}"
        baseline = _render(
            [_agent(name="a", session="benign"), _agent(name="b", session="other")], session=None
        )
        hostile_out = _render(
            [_agent(name="a", session=hostile_session), _agent(name="b", session="other")], session=None
        )
        assert_render_injection_safe(baseline, hostile_out)
