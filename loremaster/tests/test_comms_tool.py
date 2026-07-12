"""Contract tests for the ``lore_comms`` MCP tool surface (PKT-28 C1, seam S3).

Spec: ``docs/design/2026-07-12-pkt28-c1-semantics.md`` (execute verbatim; a
genuine gap is a STOP-and-flag, never an improvised decision — see this
module's own flags below and ``REPORT-c1-contract-surface.md``) + the render
ruling ``docs/design/2026-07-11-render-safety-foundation-ruling.md`` (the
render-authoring rules this module's hostile battery enforces).

This file owns the SERVER surface only: the ``_COMMS_ACTIONS`` introspectable
dispatch table, ``AppContext.comms``'s dispatch algorithm, the six
``_render_comms_*`` render helpers, the ``lore_comms`` MCP tool wrapper, and
the four structural pins the packet names (three of the four need no edit —
see ``REPORT-c1-contract-surface.md``). It does NOT test the two comms
LEDGERS (``AgentRegistry``/``BriefLedger``) — those are ``test_agent_
registry.py``/``test_brief_ledger.py``'s contract; this file injects the
already-built adversarial fakes (``_comms_fakes.py``) to exercise the
DISPATCHER's own contract in isolation, deliberately NOT going through a
fully-built ``AppContext`` (``build_app_context``) — see the module docstring
on ``_harness`` for the justification, and the report's "contract decisions"
section for the tradeoff this makes.

None of these production symbols exist yet at contract-authoring time
(``loremaster.agents``/``loremaster.briefs`` are still RED per the sibling
ledger-contract report; ``loremaster.server`` has none of the comms additions
yet) — every test in this module is expected to fail at COLLECTION with an
``ImportError``/``ModuleNotFoundError`` naming one of those, not a fixture or
import-path typo. See ``REPORT-c1-contract-surface.md`` for the RED tail.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest
from _comms_fakes import (
    FakeAgentDatabase,
    FakeAgentRegistry,
    FakeBriefDatabase,
    FakeBriefLedger,
)
from loremaster.agents import (
    AGENT_NAME_PATTERN,
    Agent,
    AgentFleetWindow,
    AgentIdentityConflictError,
    AgentRegistryError,
    AgentRosterMember,
    FleetRoster,
    IllegalAgentStatusError,
    RetiredAgentError,
    UnknownAgentError,
)
from loremaster.briefs import (
    Brief,
    BriefAckResult,
    BriefBehindEntry,
    BriefCoverage,
    BriefPublishResult,
    UnknownBriefError,
    UnknownBriefVersionError,
)
from loremaster.config import LoreConfig
from loremaster.render import Rendered, RenderSafetyError
from loremaster.sanitise import CONTROL_CHAR_PATTERN, SafeLine, max_backtick_run
from loremaster.server import (
    _COMMS_ACTIONS,
    _COMMS_TOOL_ANNOTATIONS,
    _COVERAGE_NAMES_CAP,
    _MAX_FLEET_LIMIT,
    AppContext,
    CommsActionSpec,
    LoreServer,
    build_mcp_server,
)
from render_injection_scaffold import (
    _INJECTION_THREAT_CHARS,
    _ROW_FORGE_PAYLOAD,
    RenderCase,
    assert_render_injection_safe,
)
from test_render_seam_pins import assert_actions_covered

# --------------------------------------------------------------------------- #
# Config / server-registration fixture data
# --------------------------------------------------------------------------- #
# A LOCAL, minimal LoreConfig builder — deliberately NOT imported from
# test_mcp_server.py (that file is not a designed shared module, unlike the
# underscore-prefixed ``_*.py`` helpers; independent collectibility mirrors
# the sibling ledger-contract files' own stated property). The dict shape is
# the same schema test_mcp_server.py's own ``_config`` validates against
# (fixture DATA, not shared logic — duplicating it here carries no coupling).
_DIM = 2048


def _config(slug: str) -> LoreConfig:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "surreal": {
            "url": "ws://127.0.0.1:18000/rpc",
            "namespace": "lore_test",
            "user_env": "SURREAL_USER",
            "password_env": "SURREAL_PASS",
        },
        "roots": [],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": False,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9233},
    }
    return LoreConfig.model_validate(payload)


async def _tools_by_name(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Registration-only surface: no live store touched (mirrors
    ``TestToolRegistration`` in test_mcp_server.py — ``build_mcp_server``
    registers tools synchronously; nothing connects until the lifespan
    actually runs)."""
    monkeypatch.setenv("SURREAL_USER", "root")
    monkeypatch.setenv("SURREAL_PASS", "root")
    config = _config("test_comms_surface")
    mcp = build_mcp_server(LoreServer(config))
    return {tool.name: tool for tool in await mcp.list_tools()}


# --------------------------------------------------------------------------- #
# Domain-object factories (against the ledger contract pinned in
# REPORT-c1-contract-ledgers.md's "Exact public API surface" — Agent/Brief/etc
# are plain-``str`` pydantic models with NO charset validators, so a hostile
# battery may construct them directly with an unsafe value, exactly as the
# spec's §10 note prescribes: "the battery drives the render helpers/fakes
# directly ... even if the storage ASSERT is bypassed or later relaxed.")
# --------------------------------------------------------------------------- #


def _agent(
    *,
    name: str = "fixer-b",
    session: str = "wave7",
    role: str = "builder",
    model: str | None = None,
    status: str = "active",
    spawned_by: str | None = None,
    task_id: str | None = None,
    last_note: str | None = None,
    heartbeat_at: datetime | None = None,
) -> Agent:
    now = datetime.now(UTC)
    return Agent(
        id=FakeAgentRegistry._agent_id(session, name),
        name=name,
        session=session,
        role=role,
        model=model,
        status=status,  # type: ignore[arg-type]
        spawned_by=spawned_by,
        task_id=task_id,
        checkpoint=None,
        last_note=last_note,
        registered_at=now,
        heartbeat_at=heartbeat_at if heartbeat_at is not None else now,
    )


def _brief(
    *,
    name: str = "project",
    version: int = 1,
    body: str = "read the plan",
    created_by: str = "lead",
    note: str | None = None,
) -> Brief:
    return Brief(
        id=FakeBriefLedger._brief_id(name, version),
        name=name,
        version=version,
        body=body,
        created_by=created_by,
        note=note,
        created_at=datetime.now(UTC),
    )


def _harness(
    *,
    agent_registry: FakeAgentRegistry | None = None,
    brief_ledger: FakeBriefLedger | None = None,
    stale_heartbeat_s: int = 600,
    fleet_limit: int = 20,
    brief_body_warn_chars: int = 4000,
) -> Any:
    """A minimal ``AppContext``-shaped double: exactly the attributes
    ``AppContext.comms`` touches (``agent_registry`` / ``brief_ledger`` /
    ``config.comms``), nothing else. A deliberate, documented testing-
    strategy decision (see REPORT-c1-contract-surface.md's "contract
    decisions"): the dispatcher's own contract is exercised by calling the
    REAL, unbound ``AppContext.comms`` against this double rather than a
    fully-built ``AppContext`` (which drags in the embedder probe, code
    graph, indexer, and every other unrelated write-stack service just to
    test dispatch logic) — mirrors how the two ledger-contract files already
    validate ``AgentRegistry``/``BriefLedger`` in isolation from a real
    store. Full ``build_app_context`` wiring (constructing + injecting real
    ledgers) is flagged as an OUT-of-scope decision point in the report, not
    silently assumed covered.
    """
    return SimpleNamespace(
        agent_registry=agent_registry
        if agent_registry is not None
        else FakeAgentRegistry(db=FakeAgentDatabase()),
        brief_ledger=brief_ledger if brief_ledger is not None else FakeBriefLedger(db=FakeBriefDatabase()),
        config=SimpleNamespace(
            comms=SimpleNamespace(
                stale_heartbeat_s=stale_heartbeat_s,
                fleet_limit=fleet_limit,
                brief_body_warn_chars=brief_body_warn_chars,
            )
        ),
    )


async def _register(
    harness: Any, *, name: str = "fixer-b", session: str = "wave7", role: str = "builder", **kw: Any
) -> str:
    return str(
        await AppContext.comms(harness, action="register", agent=name, session=session, role=role, **kw)
    )


# =========================================================================== #
# Section A — the ``_COMMS_ACTIONS`` dispatch table (spec §8)
# =========================================================================== #


class TestCommsActionsTable:
    """``_COMMS_ACTIONS`` is an introspectable dict[str, CommsActionSpec] —
    the exact shape spec §8 pins verbatim (six actions, D3: a SANCTIONED
    deviation from the tasks()/findings() if/elif house idiom)."""

    _EXPECTED_ACTIONS = {"register", "heartbeat", "brief_get", "brief_publish", "brief_ack", "fleet"}

    def test_exact_action_set(self) -> None:
        assert set(_COMMS_ACTIONS) == self._EXPECTED_ACTIONS

    def test_every_value_is_a_comms_action_spec(self) -> None:
        for action, spec in _COMMS_ACTIONS.items():
            assert isinstance(spec, CommsActionSpec), f"{action}'s spec must be a CommsActionSpec"
            assert callable(spec.handler)
            assert isinstance(spec.params, frozenset)
            assert isinstance(spec.required, frozenset)
            assert isinstance(spec.requires_registration, bool)

    def test_register_does_not_require_prior_registration(self) -> None:
        assert _COMMS_ACTIONS["register"].requires_registration is False

    def test_every_other_action_requires_prior_registration(self) -> None:
        for action in self._EXPECTED_ACTIONS - {"register"}:
            assert _COMMS_ACTIONS[action].requires_registration is True, (
                f"{action} must require a prior register (the uniform heartbeat touch)"
            )

    def test_register_params_and_required(self) -> None:
        spec = _COMMS_ACTIONS["register"]
        assert spec.params == frozenset({"role", "model", "spawned_by", "task_id"})
        assert spec.required == frozenset({"session", "role"})

    def test_heartbeat_params(self) -> None:
        spec = _COMMS_ACTIONS["heartbeat"]
        assert spec.params == frozenset({"note", "status"})
        assert spec.required == frozenset()

    def test_brief_get_params(self) -> None:
        spec = _COMMS_ACTIONS["brief_get"]
        assert spec.params == frozenset({"name"})
        assert spec.required == frozenset()

    def test_brief_publish_params_and_required(self) -> None:
        spec = _COMMS_ACTIONS["brief_publish"]
        assert spec.params == frozenset({"name", "body", "note"})
        assert spec.required == frozenset({"name", "body"})

    def test_brief_ack_params_and_required(self) -> None:
        spec = _COMMS_ACTIONS["brief_ack"]
        assert spec.params == frozenset({"name", "version"})
        assert spec.required == frozenset({"name", "version"})

    def test_fleet_params(self) -> None:
        spec = _COMMS_ACTIONS["fleet"]
        assert spec.params == frozenset({"limit"})
        assert spec.required == frozenset()

    def test_required_is_always_a_subset_of_params_or_universal(self) -> None:
        # 'session'/'role' (register's required set) are NOT re-declared in
        # 'params' per spec §8's "agent/session are universal ... NOT
        # re-declared per-spec" — role IS action-specific so it must appear
        # in either params or required; session is universal so it need not.
        universal = {"agent", "session"}
        for action, spec in _COMMS_ACTIONS.items():
            for name in spec.required:
                assert name in spec.params or name in universal, (
                    f"{action}'s required {name!r} must be declared in params "
                    f"(or be a universal name) for the strict-param law to accept it"
                )


class TestCommsToolRegistration:
    """``lore_comms`` is registered, annotated as mutating/non-idempotent
    (mirrors ``_TASK_TOOL_ANNOTATIONS``), and its description teaches the
    six actions."""

    async def test_lore_comms_is_registered(self, monkeypatch: pytest.MonkeyPatch) -> None:
        tools = await _tools_by_name(monkeypatch)
        assert "lore_comms" in tools

    async def test_lore_comms_annotations_mirror_task_tool_annotations(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        tools = await _tools_by_name(monkeypatch)
        annotations = tools["lore_comms"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False
        assert annotations.idempotentHint is False
        assert annotations.openWorldHint is False
        assert annotations == _COMMS_TOOL_ANNOTATIONS

    async def test_description_names_every_action(self, monkeypatch: pytest.MonkeyPatch) -> None:
        tools = await _tools_by_name(monkeypatch)
        description = tools["lore_comms"].description or ""
        for action in ("register", "heartbeat", "brief_get", "brief_publish", "brief_ack", "fleet"):
            assert action in description, f"the tool description must name {action!r}"

    async def test_param_honesty__every_spec_param_is_in_the_tool_signature(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Spec §8's param-honesty pin: a drifted ``_COMMS_ACTIONS`` table
        (a builder adds a handler param but forgets the MCP-visible
        parameter) must be caught, not shipped."""
        tools = await _tools_by_name(monkeypatch)
        properties = set((tools["lore_comms"].inputSchema or {}).get("properties", {}))
        declared_params: set[str] = {"action", "agent", "session"}
        for spec in _COMMS_ACTIONS.values():
            declared_params |= spec.params | spec.required
        missing = declared_params - properties
        assert not missing, (
            f"lore_comms tool wrapper is missing MCP-visible parameter(s) {missing!r} "
            f"declared in _COMMS_ACTIONS"
        )

    async def test_all_builtin_tools_still_include_lore_comms(self, monkeypatch: pytest.MonkeyPatch) -> None:
        tools = await _tools_by_name(monkeypatch)
        # A cheap, self-contained echo of the exact-set pin's shape (the
        # authoritative 14->15 pin lives in test_mcp_server.py per the brief;
        # this just proves lore_comms doesn't vanish from THIS module's own
        # registration path in isolation).
        assert "lore_comms" in tools
        assert "lore_tasks" in tools, "lore_comms must coexist with the pre-existing tool surface"


# =========================================================================== #
# Section A (cont.) — the dispatch ALGORITHM, in the spec's exact order
# =========================================================================== #


class TestCommsDispatchUnknownAction:
    async def test_unknown_action_lists_the_valid_set(self) -> None:
        harness = _harness()
        with pytest.raises(ValueError, match="unknown comms action") as exc_info:
            await AppContext.comms(harness, action="bogus", agent="fixer-b")
        message = str(exc_info.value)
        assert "'bogus'" in message
        for action in ("register", "heartbeat", "brief_get", "brief_publish", "brief_ack", "fleet"):
            assert action in message

    async def test_unknown_action_fires_before_charset_validation(self) -> None:
        # An invalid agent name AND an unknown action -> the unknown-action
        # ValueError wins (dispatch algorithm step 1 precedes step 2).
        harness = _harness()
        with pytest.raises(ValueError, match="unknown comms action"):
            await AppContext.comms(harness, action="bogus", agent="Not A Legal Name!")


class TestCommsDispatchCharsetValidation:
    """Step 2: charset-validate agent (+session/name when present) BEFORE
    any store touch — the store is never reached for a malformed identity."""

    _BAD_NAME = "Fixer B!"

    async def test_bad_agent_name_is_rejected_before_any_store_touch(self) -> None:
        # The fake ledger has NO row for this name; if charset validation
        # ran AFTER the store touch we would see UnknownAgentError instead.
        harness = _harness()
        with pytest.raises(ValueError) as exc_info:
            await AppContext.comms(harness, action="heartbeat", agent=self._BAD_NAME)
        message = str(exc_info.value)
        assert "agent name" in message
        assert repr(self._BAD_NAME) in message
        assert AGENT_NAME_PATTERN.pattern in message
        assert "safe charset" in message
        assert not isinstance(exc_info.value, AgentRegistryError)

    async def test_bad_session_is_rejected(self) -> None:
        harness = _harness()
        with pytest.raises(ValueError) as exc_info:
            await AppContext.comms(
                harness, action="register", agent="fixer-b", session=self._BAD_NAME, role="builder"
            )
        message = str(exc_info.value)
        assert "session" in message
        assert repr(self._BAD_NAME) in message
        assert AGENT_NAME_PATTERN.pattern in message

    async def test_bad_brief_name_is_rejected(self) -> None:
        harness = _harness()
        with pytest.raises(ValueError) as exc_info:
            await AppContext.comms(harness, action="brief_get", agent="fixer-b", name=self._BAD_NAME)
        message = str(exc_info.value)
        assert "brief name" in message
        assert repr(self._BAD_NAME) in message

    async def test_a_legal_charset_name_is_not_rejected_by_charset_validation(self) -> None:
        # Positive control: hyphens/digits/underscores are legal (spec §0).
        harness = _harness()
        await _register(harness, name="fixer-b2", session="wave-7_a", role="builder")


class TestCommsDispatchStrictParamLaw:
    """Step 3: a foreign (non-None) param is a loud ValueError naming which
    action(s) it applies to — never silently ignored."""

    async def test_single_owner_param_names_that_one_action(self) -> None:
        harness = _harness()
        with pytest.raises(ValueError) as exc_info:
            await AppContext.comms(harness, action="heartbeat", agent="fixer-b", version=5)
        message = str(exc_info.value)
        assert "'version'" in message
        assert "brief_ack" in message
        assert "heartbeat" in message

    async def test_multi_owner_param_names_every_owning_action(self) -> None:
        # 'note' is declared by BOTH heartbeat and brief_publish.
        harness = _harness()
        with pytest.raises(ValueError) as exc_info:
            await AppContext.comms(
                harness, action="register", agent="fixer-b", session="wave7", role="builder", note="hi"
            )
        message = str(exc_info.value)
        assert "'note'" in message
        assert "heartbeat" in message
        assert "brief_publish" in message

    async def test_foreign_param_wins_over_a_missing_required_param(self) -> None:
        # register also carries no session/role here -- the FOREIGN param
        # error must still win (dispatch order: strict-param law before
        # required-param enforcement, per spec §8 step 3).
        harness = _harness()
        with pytest.raises(ValueError) as exc_info:
            await AppContext.comms(harness, action="register", agent="fixer-b", version=5)
        assert "'version'" in str(exc_info.value)

    async def test_universal_params_are_never_foreign(self) -> None:
        # agent/session are accepted by every action even though only
        # register declares session as required.
        harness = _harness()
        await _register(harness)
        await AppContext.comms(harness, action="fleet", agent="fixer-b", session="wave7")


class TestCommsDispatchRequiredParamLaw:
    async def test_register_missing_session(self) -> None:
        harness = _harness()
        with pytest.raises(ValueError) as exc_info:
            await AppContext.comms(harness, action="register", agent="fixer-b", role="builder")
        message = str(exc_info.value)
        assert "'session'" in message
        assert "action='register'" in message

    async def test_register_missing_role(self) -> None:
        harness = _harness()
        with pytest.raises(ValueError) as exc_info:
            await AppContext.comms(harness, action="register", agent="fixer-b", session="wave7")
        assert "'role'" in str(exc_info.value)

    async def test_brief_publish_missing_body(self) -> None:
        harness = _harness()
        with pytest.raises(ValueError) as exc_info:
            await AppContext.comms(harness, action="brief_publish", agent="fixer-b", name="project")
        assert "'body'" in str(exc_info.value)

    async def test_brief_ack_missing_version(self) -> None:
        harness = _harness()
        with pytest.raises(ValueError) as exc_info:
            await AppContext.comms(harness, action="brief_ack", agent="fixer-b", name="project")
        assert "'version'" in str(exc_info.value)


class TestCommsDispatchUniformHeartbeatTouch:
    """Step 4: one site (the dispatcher) stamps heartbeat_at + drives the
    idle auto-flip for every non-register action; an unregistered agent
    surfaces UnknownAgentError from that SAME statement."""

    async def test_every_non_register_action_on_an_unknown_agent_raises_unknown_agent(self) -> None:
        for action, kwargs in (
            ("heartbeat", {}),
            ("brief_get", {}),
            ("brief_publish", {"name": "project", "body": "x"}),
            ("brief_ack", {"name": "project", "version": 1}),
            ("fleet", {}),
        ):
            harness = _harness()
            with pytest.raises(UnknownAgentError):
                await AppContext.comms(harness, action=action, agent="ghost", **kwargs)

    async def test_heartbeat_stamps_a_fresh_heartbeat_at(self) -> None:
        db = FakeAgentDatabase()
        harness = _harness(agent_registry=FakeAgentRegistry(db=db))
        await AppContext.comms(harness, action="register", agent="fixer-b", session="wave7", role="builder")
        registered = await harness.agent_registry.get_agent("fixer-b", session="wave7")
        before = registered.heartbeat_at
        await AppContext.comms(harness, action="fleet", agent="fixer-b", session="wave7")
        after = await harness.agent_registry.get_agent("fixer-b", session="wave7")
        assert after.heartbeat_at >= before

    async def test_idle_agent_auto_flips_active_on_any_non_heartbeat_action(self) -> None:
        db = FakeAgentDatabase()
        harness = _harness(agent_registry=FakeAgentRegistry(db=db))
        await AppContext.comms(harness, action="register", agent="fixer-b", session="wave7", role="builder")
        await harness.agent_registry.touch("fixer-b", session="wave7", status="idle")
        await AppContext.comms(harness, action="fleet", agent="fixer-b", session="wave7")
        agent = await harness.agent_registry.get_agent("fixer-b", session="wave7")
        assert agent.status == "active"

    async def test_explicit_heartbeat_status_wins_over_auto_flip(self) -> None:
        db = FakeAgentDatabase()
        harness = _harness(agent_registry=FakeAgentRegistry(db=db))
        await AppContext.comms(harness, action="register", agent="fixer-b", session="wave7", role="builder")
        await AppContext.comms(
            harness, action="heartbeat", agent="fixer-b", session="wave7", status="input_required"
        )
        agent = await harness.agent_registry.get_agent("fixer-b", session="wave7")
        assert agent.status == "input_required"

    async def test_retired_agent_raises_retired_agent_error(self) -> None:
        db = FakeAgentDatabase()
        harness = _harness(agent_registry=FakeAgentRegistry(db=db))
        await AppContext.comms(harness, action="register", agent="fixer-b", session="wave7", role="builder")
        await harness.agent_registry.touch("fixer-b", session="wave7", status="retired")
        with pytest.raises(RetiredAgentError):
            await AppContext.comms(harness, action="fleet", agent="fixer-b", session="wave7")

    async def test_illegal_status_transition_propagates_unchanged(self) -> None:
        db = FakeAgentDatabase()
        harness = _harness(agent_registry=FakeAgentRegistry(db=db))
        await AppContext.comms(harness, action="register", agent="fixer-b", session="wave7", role="builder")
        await AppContext.comms(
            harness, action="heartbeat", agent="fixer-b", session="wave7", status="input_required"
        )
        with pytest.raises(IllegalAgentStatusError):
            # input_required -> idle is illegal (spec §3).
            await AppContext.comms(
                harness, action="heartbeat", agent="fixer-b", session="wave7", status="idle"
            )

    async def test_unknown_agent_error_is_enriched_with_a_capped_active_roster(self) -> None:
        """S2's ledger-level UnknownAgentError deliberately carries no active
        roster (contract decision #4, REPORT-c1-contract-ledgers.md) -- the
        SERVER enriches it. Pin the enrichment, capped/counted."""
        db = FakeAgentDatabase()
        harness = _harness(agent_registry=FakeAgentRegistry(db=db))
        names = [f"agent-{i}" for i in range(_COVERAGE_NAMES_CAP + 2)]
        for name in names:
            await AppContext.comms(harness, action="register", agent=name, session="wave7", role="builder")
        with pytest.raises(UnknownAgentError) as exc_info:
            await AppContext.comms(harness, action="fleet", agent="ghost", session="wave7")
        message = str(exc_info.value)
        assert "active agents:" in message
        assert f"(+{len(names) - _COVERAGE_NAMES_CAP} more)" in message

    async def test_unknown_agent_error_remainder_is_the_true_total_not_the_capped_fleet_window(
        self,
    ) -> None:
        """v4 audit F1 (REPORT-c1-audit-fixwave.md, BLOCKER): the enrichment's
        ``(+K more)`` remainder must come from the roster's TRUE total (the
        honest ``AgentFleetWindow.total_non_retired``), never
        ``len(window.rows)`` -- a ``_MAX_FLEET_LIMIT``-capped window. Below the
        cap the two coincide (the sibling test above, at
        ``_COVERAGE_NAMES_CAP + 2`` agents, never crosses it and so can never
        catch this) -- this fixture registers past ``_MAX_FLEET_LIMIT`` so the
        capped-window count and the true total diverge, exactly the D1 class
        the counting law (design doc §5.3 v4) forbids: 'a served count is
        computed over the WHOLE set its label claims to describe ... never a
        silently-capped window.'

        Current production defect (server.py's
        ``_comms_enrich_unknown_agent``): ``remainder = len(names) -
        len(shown)`` where ``names`` comes from a ``limit=_MAX_FLEET_LIMIT``-
        capped ``fleet()`` call -- at N=205 this renders ``(+195 more)``
        where the truth is ``(+200 more)``. The fix is
        ``remainder = window.total_non_retired - len(shown)``.
        """
        db = FakeAgentDatabase()
        harness = _harness(agent_registry=FakeAgentRegistry(db=db))
        total_agents = _MAX_FLEET_LIMIT + 5
        for index in range(total_agents):
            await harness.agent_registry.register(f"agent-{index:03d}", session="wave7", role="builder")

        with pytest.raises(UnknownAgentError) as exc_info:
            await AppContext.comms(harness, action="fleet", agent="ghost", session="wave7")

        message = str(exc_info.value)
        true_remainder = total_agents - _COVERAGE_NAMES_CAP
        capped_window_remainder = _MAX_FLEET_LIMIT - _COVERAGE_NAMES_CAP
        assert f"(+{true_remainder} more)" in message, (
            f"expected the TRUE remainder (+{true_remainder} more) computed over "
            f"the whole {total_agents}-agent roster, not the display-capped "
            f"window's (+{capped_window_remainder} more) -- got: {message!r}"
        )


# =========================================================================== #
# Section A (cont.) — per-action behavior (register/heartbeat/brief_*/fleet)
# =========================================================================== #


class TestRegisterAction:
    async def test_bootstrap_writes_no_ack_edge_and_renders_a_notice(self) -> None:
        harness = _harness()
        rendered = await _register(harness)
        assert "no 'project' brief published yet" in rendered
        assert "brief_get" in rendered

    async def test_registered_line_names_session_and_role(self) -> None:
        harness = _harness()
        rendered = await _register(harness, name="fixer-b", session="wave7", role="builder")
        assert "registered fixer-b" in rendered
        assert "wave7" in rendered
        assert "builder" in rendered
        assert "re-registered" not in rendered

    async def test_reregister_says_re_registered_not_registered(self) -> None:
        harness = _harness()
        await _register(harness)
        rendered = await _register(harness)
        assert "re-registered fixer-b" in rendered

    async def test_register_after_a_project_brief_exists_acks_it(self) -> None:
        brief_ledger = FakeBriefLedger(db=FakeBriefDatabase())
        await brief_ledger.publish("project", "read the plan", created_by="lead")
        harness = _harness(brief_ledger=brief_ledger)
        rendered = await _register(harness)
        assert "brief 'project' v1" in rendered
        assert "ack recorded" in rendered
        assert "read the plan" in rendered, "the brief body must round-trip verbatim inside the fence"
        assert "brief project v1 read" in rendered, "the C4 brief-base receipt-line grammar"
        acked = await brief_ledger.acked_version(
            agent_id=FakeAgentRegistry._agent_id("wave7", "fixer-b"), name="project"
        )
        assert acked == 1

    async def test_role_conflict_on_reregister_propagates(self) -> None:
        harness = _harness()
        await _register(harness, role="builder")
        with pytest.raises(AgentIdentityConflictError):
            await _register(harness, role="auditor")


class TestHeartbeatAction:
    async def test_current_or_no_brief_is_silent_one_line(self) -> None:
        harness = _harness()
        await _register(harness)
        rendered = str(await AppContext.comms(harness, action="heartbeat", agent="fixer-b", session="wave7"))
        assert rendered.count("\n") == 0
        assert "heartbeat fixer-b" in rendered
        assert "status active" in rendered

    async def test_skew_names_the_catch_up_call(self) -> None:
        brief_ledger = FakeBriefLedger(db=FakeBriefDatabase())
        await brief_ledger.publish("project", "v1 body", created_by="lead")
        harness = _harness(brief_ledger=brief_ledger)
        await _register(harness)
        await brief_ledger.publish("project", "v2 body", created_by="lead")
        rendered = str(await AppContext.comms(harness, action="heartbeat", agent="fixer-b", session="wave7"))
        assert "v2" in rendered and "v1" in rendered
        assert "brief_get" in rendered


class TestBriefGetAction:
    async def test_unknown_brief_name_teaches_known_names(self) -> None:
        brief_ledger = FakeBriefLedger(db=FakeBriefDatabase())
        await brief_ledger.publish("project", "body", created_by="lead")
        harness = _harness(brief_ledger=brief_ledger)
        await _register(harness)
        with pytest.raises(UnknownBriefError) as exc_info:
            await AppContext.comms(
                harness, action="brief_get", agent="fixer-b", session="wave7", name="bogus"
            )
        assert "project" in str(exc_info.value)

    async def test_full_coverage_variant(self) -> None:
        """v2 scoping ruling (spec §5.3, CHANGELOG amendment): this call
        carries an EXPLICIT session='wave7' -- the render MUST be
        session-scoped. The pre-fix assertion here ("coverage: all 1", the
        UNSCOPED grammar) was itself the defect the consultant named: it
        conflated §0.3 identity resolution with §5.3 render scoping."""
        brief_ledger = FakeBriefLedger(db=FakeBriefDatabase())
        harness = _harness(brief_ledger=brief_ledger)
        await _register(harness)  # bootstrap, no project brief yet
        await brief_ledger.publish("project", "the plan", created_by="lead")
        await _register(harness)  # re-register acks it
        rendered = str(
            await AppContext.comms(
                harness, action="brief_get", agent="fixer-b", session="wave7", name="project"
            )
        )
        assert "the plan" in rendered
        assert "coverage (session wave7): all 1 non-retired agents at v1" in rendered

    async def test_coverage_is_fleet_wide_when_session_is_omitted(self) -> None:
        """v2 scoping law: identity resolution (bare-name lookup, §0.3) and
        render scoping are independent. Omitting session= on the CALL must
        render the unscoped, fleet-wide count with NO '(session ...)' tag --
        even though the caller ('fixer-b') resolves to one particular
        session under the hood."""
        brief_ledger = FakeBriefLedger(db=FakeBriefDatabase())
        harness = _harness(brief_ledger=brief_ledger)
        await _register(harness, name="fixer-b", session="wave7")  # bootstrap
        await _register(harness, name="scout-c", session="wave8")  # bootstrap
        await brief_ledger.publish("project", "the plan", created_by="lead")
        await _register(harness, name="fixer-b", session="wave7")  # re-register acks v1

        rendered = str(
            await AppContext.comms(harness, action="brief_get", agent="fixer-b", name="project")
        )
        assert "(session" not in rendered
        assert "coverage: 1/2 non-retired agents at v1; behind: scout-c (unbriefed)" in rendered

    async def test_coverage_roster_is_session_filtered_when_session_is_explicit(self) -> None:
        """Same fixed state as above, read through BOTH sessions' explicit
        scopes -- proves the roster handed to BriefLedger.coverage is the
        registry's non-retired partition, session-filtered iff explicit
        session= (spec §5.3's 'Roster plumbing' clause), not a coincidence
        of a single shared fleet-wide count."""
        brief_ledger = FakeBriefLedger(db=FakeBriefDatabase())
        harness = _harness(brief_ledger=brief_ledger)
        await _register(harness, name="fixer-b", session="wave7")
        await _register(harness, name="scout-c", session="wave8")
        await brief_ledger.publish("project", "the plan", created_by="lead")
        await _register(harness, name="fixer-b", session="wave7")  # acks v1

        scoped_wave7 = str(
            await AppContext.comms(
                harness, action="brief_get", agent="fixer-b", session="wave7", name="project"
            )
        )
        scoped_wave8 = str(
            await AppContext.comms(
                harness, action="brief_get", agent="scout-c", session="wave8", name="project"
            )
        )
        assert "coverage (session wave7): all 1 non-retired agents at v1" in scoped_wave7
        assert (
            "coverage (session wave8): 0/1 non-retired agents at v1; behind: scout-c (unbriefed)"
            in scoped_wave8
        )


class TestBriefPublishAction:
    async def test_first_version_variant(self) -> None:
        harness = _harness()
        await _register(harness)
        rendered = str(
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="fixer-b",
                session="wave7",
                name="project",
                body="v1 body",
                created_by="fixer-b",
            )
        )
        assert "brief 'project' v1 published by fixer-b" in rendered
        assert "first version" in rendered

    async def test_skew_line_counts_non_retired_agents_behind(self) -> None:
        """v2 scoping ruling: this call carries an explicit session='wave7'
        -- the skew line MUST carry the '(session wave7)' tag (the same
        defect class as test_full_coverage_variant above, on brief_publish's
        twin surface, spec §9.4)."""
        harness = _harness()
        await _register(harness, name="fixer-b")
        await _register(harness, name="fixer-c")
        await AppContext.comms(
            harness, action="brief_publish", agent="fixer-b", session="wave7", name="project", body="v1"
        )
        rendered = str(
            await AppContext.comms(
                harness, action="brief_publish", agent="fixer-b", session="wave7", name="project", body="v2"
            )
        )
        assert "skew (session wave7): 2" in rendered

    async def test_skew_line_is_fleet_wide_when_session_is_omitted(self) -> None:
        """v2 scoping law, brief_publish's twin of the brief_get roster
        test: omitting session= renders the unscoped, fleet-wide skew count
        with no '(session ...)' tag."""
        harness = _harness()
        await _register(harness, name="fixer-b", session="wave7")
        await _register(harness, name="scout-c", session="wave8")
        rendered = str(
            await AppContext.comms(
                harness, action="brief_publish", agent="fixer-b", name="project", body="v1"
            )
        )
        assert "(session" not in rendered
        assert "skew: 2" in rendered

    async def test_skew_line_is_session_scoped_when_session_is_explicit(self) -> None:
        """Same fixed state as above, published with an explicit session=
        -- the skew roster must be session-filtered, not fleet-wide."""
        harness = _harness()
        await _register(harness, name="fixer-b", session="wave7")
        await _register(harness, name="scout-c", session="wave8")
        rendered = str(
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="fixer-b",
                session="wave7",
                name="project",
                body="v1",
            )
        )
        assert "skew (session wave7): 1" in rendered

    async def test_warn_line_only_past_the_threshold(self) -> None:
        harness = _harness(brief_body_warn_chars=10)
        await _register(harness)
        rendered = str(
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="fixer-b",
                session="wave7",
                name="project",
                body="x" * 20,
            )
        )
        assert "exceeds" in rendered
        assert "10" in rendered


class TestBriefAckAction:
    async def test_head_ack(self) -> None:
        harness = _harness()
        await _register(harness)
        await AppContext.comms(
            harness, action="brief_publish", agent="fixer-b", session="wave7", name="project", body="v1"
        )
        rendered = str(
            await AppContext.comms(
                harness, action="brief_ack", agent="fixer-b", session="wave7", name="project", version=1
            )
        )
        assert "acked brief 'project' v1" in rendered
        assert "(head)" in rendered

    async def test_behind_ack_is_legal_and_honest(self) -> None:
        harness = _harness()
        await _register(harness)
        await AppContext.comms(
            harness, action="brief_publish", agent="fixer-b", session="wave7", name="project", body="v1"
        )
        await AppContext.comms(
            harness, action="brief_publish", agent="fixer-b", session="wave7", name="project", body="v2"
        )
        rendered = str(
            await AppContext.comms(
                harness, action="brief_ack", agent="fixer-b", session="wave7", name="project", version=1
            )
        )
        assert "head is v2" in rendered

    async def test_nonexistent_version_teaches_the_real_head(self) -> None:
        harness = _harness()
        await _register(harness)
        await AppContext.comms(
            harness, action="brief_publish", agent="fixer-b", session="wave7", name="project", body="v1"
        )
        with pytest.raises(UnknownBriefVersionError) as exc_info:
            await AppContext.comms(
                harness, action="brief_ack", agent="fixer-b", session="wave7", name="project", version=9
            )
        assert "v1" in str(exc_info.value)

    async def test_reack_is_idempotent(self) -> None:
        harness = _harness()
        await _register(harness)
        await AppContext.comms(
            harness, action="brief_publish", agent="fixer-b", session="wave7", name="project", body="v1"
        )
        await AppContext.comms(
            harness, action="brief_ack", agent="fixer-b", session="wave7", name="project", version=1
        )
        rendered = str(
            await AppContext.comms(
                harness, action="brief_ack", agent="fixer-b", session="wave7", name="project", version=1
            )
        )
        assert "already acked" in rendered


class TestFleetAction:
    async def test_lists_registered_agents(self) -> None:
        harness = _harness()
        await _register(harness, name="fixer-b")
        await _register(harness, name="scout-c")
        rendered = str(await AppContext.comms(harness, action="fleet", agent="fixer-b", session="wave7"))
        assert "fixer-b" in rendered
        assert "scout-c" in rendered
        assert "2 agents" in rendered


# =========================================================================== #
# Section A.5 — v4 audit D1: over-cap TRUE counts (docs/design/2026-07-12-
# pkt28-c1-semantics.md CHANGELOG v4, §5.3/§6). The cold audit reproduced a
# self-contradicting fleet header past `_MAX_FLEET_LIMIT` agents: the total
# was already true (computed over the whole, unbounded query result) but the
# per-status segments, brief_get coverage, and brief_publish skew were all
# counted over the `_MAX_FLEET_LIMIT`-capped window and rendered as
# fleet-wide truths. RULED fix: `AgentRegistry.roster()` (new, row-unlimited)
# is the ONE source of true counts; `_MAX_FLEET_LIMIT` bounds rendered ROWS
# only, never a served number.
#
# These handler-level tests use a LOCAL spy (deliberately NOT
# `_comms_fakes.py`, frozen this contract wave — see report) whose `fleet()`
# window and `roster()` truth DISAGREE by construction, so a still-buggy
# handler that reads counts from `fleet()`'s capped rows is caught
# red-handed rather than coincidentally passing. This is the chosen
# live-vs-synthetic split (see report): a >200-agent LIVE fixture is slow;
# this is a pure in-memory fixture exercising the wiring, complemented by
# ONE live `AgentRegistry.roster()` test in test_agent_registry.py.
# =========================================================================== #

_TRUE_PARKED = 10
_TRUE_ACTIVE = 150
_TRUE_IDLE = 45
_TRUE_RETIRED = 7
_TRUE_NON_RETIRED_TOTAL = _TRUE_PARKED + _TRUE_ACTIVE + _TRUE_IDLE  # 205, > _MAX_FLEET_LIMIT (200)
assert _TRUE_NON_RETIRED_TOTAL > _MAX_FLEET_LIMIT


class _OverCapRosterSpyRegistry:
    """A local spy `agent_registry` double: `fleet()` returns exactly
    `_MAX_FLEET_LIMIT` display rows whose OWN per-status breakdown
    (10 parked / 150 active / 40 idle = 200) DISAGREES with the true
    breakdown `roster()` reports (10 / 150 / 45 = 205) -- a handler that
    (bug) recounts from `fleet()`'s rows/window instead of calling
    `roster()` is caught red-handed by a wrong number, not a coincidence.
    """

    def __init__(self) -> None:
        self.status_counts = {
            "input_required": _TRUE_PARKED,
            "active": _TRUE_ACTIVE,
            "idle": _TRUE_IDLE,
            "retired": _TRUE_RETIRED,
        }
        now = datetime.now(UTC)
        self.members = [
            AgentRosterMember(id=f"member-{i}", name=f"member-{i}", status="active", heartbeat_at=now)
            for i in range(_TRUE_NON_RETIRED_TOTAL)
        ]
        capped_idle_count = _MAX_FLEET_LIMIT - _TRUE_PARKED - _TRUE_ACTIVE  # 40, NOT the true 45
        self._capped_rows = (
            [_agent(name=f"parked-{i}", status="input_required") for i in range(_TRUE_PARKED)]
            + [_agent(name=f"active-{i}", status="active") for i in range(_TRUE_ACTIVE)]
            + [_agent(name=f"idle-{i}", status="idle") for i in range(capped_idle_count)]
        )
        assert len(self._capped_rows) == _MAX_FLEET_LIMIT

    async def fleet(self, *, session: str | None = None, limit: int) -> AgentFleetWindow:
        return AgentFleetWindow(
            rows=self._capped_rows[:limit],
            retired_count=_TRUE_RETIRED,
            total_non_retired=_MAX_FLEET_LIMIT,  # the OLD, WRONG total a buggy caller might still trust
        )

    async def roster(self, *, session: str | None = None) -> FleetRoster:
        return FleetRoster(members=list(self.members), status_counts=dict(self.status_counts))


class _NoProjectBriefLedger:
    """A minimal spy `brief_ledger`: no 'project' brief exists yet, so the
    `fleet` handler's ``get_head`` branch short-circuits to
    ``project_head_version=None`` -- keeps this fixture focused on the
    header/elision/retired-trailer numbers alone."""

    async def get_head(self, name: str) -> Brief:
        raise UnknownBriefError(
            f"no briefs published yet — lore_comms action=brief_publish creates {name!r} v1"
        )


class _CoverageSkewSpyBriefLedger:
    """A local spy `brief_ledger`: records the SIZE of `active_agents`
    `coverage()` is actually called with -- the direct proof that
    `brief_get`/`brief_publish` source their coverage/skew denominator from
    the COMPLETE roster, never the display-capped `fleet()` window.
    """

    def __init__(self, *, head_brief: Brief) -> None:
        self._head_brief = head_brief
        self.coverage_calls: list[int] = []

    async def get_head(self, name: str) -> Brief:
        return self._head_brief

    async def coverage(self, name: str, *, active_agents: Any) -> BriefCoverage:
        roster = list(active_agents)
        self.coverage_calls.append(len(roster))
        return BriefCoverage(
            name=name,
            head_version=self._head_brief.version,
            total_agents=len(roster),
            current_count=0,
            behind=[],
        )

    async def publish(
        self, name: str, body: str, *, created_by: str, note: str | None = None
    ) -> BriefPublishResult:
        del name, body, created_by, note
        return BriefPublishResult(brief=self._head_brief, first_version=False)


class TestFleetHandlerSourcesTrueCountsFromRoster:
    """v4 audit D1 LOAD-BEARING fixture: the `_comms_fleet` HANDLER (not just
    the render helper) must source its header total/segments, elision `k`,
    and retired trailer from `agent_registry.roster().status_counts` --
    never a recount of the display-capped `fleet()` window.
    """

    async def test_header_elision_and_retired_trailer_use_the_true_roster(self) -> None:
        registry_spy = _OverCapRosterSpyRegistry()
        ctx = SimpleNamespace(
            agent_registry=registry_spy,
            brief_ledger=_NoProjectBriefLedger(),
            config=SimpleNamespace(
                comms=SimpleNamespace(stale_heartbeat_s=600, fleet_limit=20, brief_body_warn_chars=4000)
            ),
        )
        rendered = str(
            await AppContext._comms_fleet(
                cast(AppContext, ctx), agent_row=_agent(name="caller"), session=None, limit=_MAX_FLEET_LIMIT
            )
        )
        assert f"{_TRUE_NON_RETIRED_TOTAL} agents" in rendered
        assert f"{_TRUE_PARKED} input_required" in rendered
        assert f"{_TRUE_ACTIVE} active" in rendered
        assert f"{_TRUE_IDLE} idle" in rendered  # the true 45 -- NOT the window's capped 40
        remainder = _TRUE_NON_RETIRED_TOTAL - _MAX_FLEET_LIMIT
        assert f"+{remainder} more beyond the display cap ({_MAX_FLEET_LIMIT})" in rendered
        assert "re-run with limit=200" not in rendered  # the dead-end re-ask this variant replaces
        assert f"+{_TRUE_RETIRED} retired" in rendered


class TestBriefGetCoverageOverTheWholeRoster:
    """v4 audit D1: `brief_get`'s coverage denominator is the COMPLETE
    in-scope membership (`AgentRegistry.roster().members`), never the
    `_MAX_FLEET_LIMIT`-capped `fleet()` window."""

    async def test_coverage_denominator_is_the_true_roster_not_the_capped_window(self) -> None:
        head = _brief(name="project", version=3)
        registry_spy = _OverCapRosterSpyRegistry()
        ledger_spy = _CoverageSkewSpyBriefLedger(head_brief=head)
        ctx = SimpleNamespace(agent_registry=registry_spy, brief_ledger=ledger_spy)

        await AppContext._comms_brief_get(
            cast(AppContext, ctx), agent_row=_agent(name="caller"), session=None, name="project"
        )

        assert ledger_spy.coverage_calls == [_TRUE_NON_RETIRED_TOTAL]


class TestBriefPublishSkewOverTheWholeRoster:
    """v4 audit D1: `brief_publish`'s skew count rides the SAME §5.3
    plumbing as coverage -- `roster().members`, never the capped window."""

    async def test_skew_denominator_is_the_true_roster_not_the_capped_window(self) -> None:
        head = _brief(name="project", version=4)
        registry_spy = _OverCapRosterSpyRegistry()
        ledger_spy = _CoverageSkewSpyBriefLedger(head_brief=head)
        ctx = SimpleNamespace(
            agent_registry=registry_spy,
            brief_ledger=ledger_spy,
            config=SimpleNamespace(comms=SimpleNamespace(brief_body_warn_chars=4000)),
        )

        await AppContext._comms_brief_publish(
            cast(AppContext, ctx),
            agent_row=_agent(name="caller"),
            session=None,
            name="project",
            body="standing instructions",
            note=None,
        )

        assert ledger_spy.coverage_calls == [_TRUE_NON_RETIRED_TOTAL]


# =========================================================================== #
# Section B — the render helpers, unit-tested directly (no live store, no
# AppContext instance: all are @staticmethod, contract decision below).
# =========================================================================== #
# NB (contract decision, see the report): every `_render_comms_*` helper is
# pinned as a @staticmethod, NOT the `self`-taking shape the spec's worked
# pseudocode shows literally. This mirrors the EXISTING C0 idiom exactly
# (`AppContext._render_task_transition` is `@staticmethod`, no `self`,
# server.py:3192) and lets these tests call the helper as a pure function
# with no AppContext/harness needed at all.


def _fleet_window(rows: list[Agent], *, retired_count: int = 0) -> AgentFleetWindow:
    return AgentFleetWindow(rows=rows, retired_count=retired_count, total_non_retired=len(rows))


def _status_counts(rows: list[Agent], *, retired_count: int = 0) -> dict[str, int]:
    """TRUE per-status aggregate over ``rows`` — mirrors ``test_comms_fleet_
    grouping.py``'s identically-named helper. Required now that
    ``_render_comms_fleet``'s ``status_counts`` keyword is non-optional (v4
    audit D1 fix: no ``len()``-derived fallback path may exist in production,
    so every direct caller of the render helper — including these tests —
    must supply the true aggregate itself; see REPORT-c1-builder-d1d2.md's
    disclosed deviation)."""
    counts = {"input_required": 0, "active": 0, "idle": 0, "retired": retired_count}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    return counts


class TestRenderAge:
    """spec §9's unit-boundary pins: <120s -> s, <120m -> m, <48h -> h, else d."""

    @pytest.mark.parametrize(
        ("seconds", "expected"),
        [
            (0, "0s"),
            (57, "57s"),
            (119, "119s"),
            (120, "2m"),
            (7199, "119m"),
            (7200, "2h"),
            (172799, "47h"),
            (172800, "2d"),
            (259200, "3d"),
        ],
    )
    def test_boundaries(self, seconds: int, expected: str) -> None:
        assert str(AppContext._render_age(seconds)) == expected

    def test_returns_a_safe_line(self) -> None:
        assert isinstance(AppContext._render_age(42), SafeLine)


class TestRenderCommsRegister:
    def test_bootstrap_variant_has_no_brief_section(self) -> None:
        rendered = AppContext._render_comms_register(
            _agent(), re_registered=False, registered_age_s=0, brief=None, brief_age_s=0
        )
        assert isinstance(rendered, Rendered)
        assert "no 'project' brief published yet" in rendered
        assert "brief_get" in rendered

    def test_full_variant_carries_the_fenced_body_and_receipt_line(self) -> None:
        rendered = AppContext._render_comms_register(
            _agent(),
            re_registered=False,
            registered_age_s=0,
            brief=_brief(name="project", version=5, body="the plan", created_by="lead"),
            brief_age_s=7200,
        )
        assert "brief 'project' v5" in rendered
        assert "the plan" in rendered
        assert "ack recorded (via register)" in rendered
        assert "brief project v5 read" in rendered

    def test_reregistered_names_the_original_age(self) -> None:
        rendered = AppContext._render_comms_register(
            _agent(), re_registered=True, registered_age_s=3600, brief=None, brief_age_s=0
        )
        assert "re-registered" in rendered
        assert "registered" in rendered  # substring of re-registered too


class TestRenderCommsHeartbeat:
    def test_current_is_silent_one_line(self) -> None:
        rendered = AppContext._render_comms_heartbeat(
            _agent(), project_head_version=3, project_acked_version=3
        )
        assert rendered.count("\n") == 0

    def test_no_project_brief_yet_is_silent_one_line(self) -> None:
        rendered = AppContext._render_comms_heartbeat(
            _agent(), project_head_version=None, project_acked_version=None
        )
        assert rendered.count("\n") == 0

    def test_skew_is_two_lines(self) -> None:
        rendered = AppContext._render_comms_heartbeat(
            _agent(), project_head_version=5, project_acked_version=4
        )
        assert rendered.count("\n") == 1
        assert "v5" in rendered and "v4" in rendered

    def test_unbriefed_with_head_is_two_lines(self) -> None:
        rendered = AppContext._render_comms_heartbeat(
            _agent(), project_head_version=5, project_acked_version=None
        )
        assert rendered.count("\n") == 1
        assert "not acked" in rendered


class TestRenderCommsBriefGet:
    def test_full_coverage(self) -> None:
        coverage = BriefCoverage(name="project", head_version=5, total_agents=5, current_count=5, behind=[])
        rendered = AppContext._render_comms_brief_get(
            _brief(version=5, body="body text"), 7200, coverage, session=None
        )
        assert "body text" in rendered
        assert "coverage: all 5" in rendered

    def test_partial_coverage_lists_behind_agents(self) -> None:
        coverage = BriefCoverage(
            name="project",
            head_version=5,
            total_agents=3,
            current_count=1,
            behind=[
                BriefBehindEntry(agent_name="fixer-b", acked_version=4),
                BriefBehindEntry(agent_name="scout-c", acked_version=None),
            ],
        )
        rendered = AppContext._render_comms_brief_get(
            _brief(version=5, body="body text"), 0, coverage, session=None
        )
        assert "1/3" in rendered
        assert "fixer-b (v4)" in rendered
        assert "scout-c (unbriefed)" in rendered

    def test_session_scoped_names_the_session(self) -> None:
        coverage = BriefCoverage(name="project", head_version=1, total_agents=1, current_count=1, behind=[])
        rendered = AppContext._render_comms_brief_get(
            _brief(version=1, body="b"), 0, coverage, session="wave7"
        )
        assert "wave7" in rendered


class TestRenderCommsBriefPublish:
    def test_first_version(self) -> None:
        result = BriefPublishResult(brief=_brief(version=1), first_version=True)
        rendered = AppContext._render_comms_brief_publish(
            result, skew_count=0, body_chars=10, warn_threshold_chars=4000, session=None
        )
        assert "first version" in rendered
        assert "skew" not in rendered

    def test_skew_count_renders_only_when_positive(self) -> None:
        result = BriefPublishResult(brief=_brief(version=2), first_version=False)
        rendered = AppContext._render_comms_brief_publish(
            result, skew_count=3, body_chars=10, warn_threshold_chars=4000, session=None
        )
        assert "skew: 3" in rendered
        assert "(session" not in rendered

    def test_session_scoped_names_the_session(self) -> None:
        """The scoping law's render-helper leg (spec §5.3/§9.4, v2 amendment)
        -- mirrors TestRenderCommsBriefGet.test_session_scoped_names_the_
        session, brief_publish's twin surface."""
        result = BriefPublishResult(brief=_brief(version=2), first_version=False)
        rendered = AppContext._render_comms_brief_publish(
            result, skew_count=3, body_chars=10, warn_threshold_chars=4000, session="wave7"
        )
        assert "skew (session wave7): 3" in rendered

    def test_warn_line_only_past_threshold(self) -> None:
        result = BriefPublishResult(brief=_brief(version=1), first_version=True)
        under = AppContext._render_comms_brief_publish(
            result, skew_count=0, body_chars=100, warn_threshold_chars=4000, session=None
        )
        over = AppContext._render_comms_brief_publish(
            result, skew_count=0, body_chars=5000, warn_threshold_chars=4000, session=None
        )
        assert "exceeds" not in under
        assert "exceeds" in over
        assert "5000" in over and "4000" in over


class TestRenderCommsBriefAck:
    def test_head_ack(self) -> None:
        result = BriefAckResult(
            name="project", version=5, head_version=5, already_acked=False, via="explicit"
        )
        rendered = AppContext._render_comms_brief_ack(result)
        assert "acked brief 'project' v5" in rendered
        assert "(head)" in rendered
        assert rendered.count("\n") == 0

    def test_behind_ack(self) -> None:
        result = BriefAckResult(
            name="project", version=4, head_version=5, already_acked=False, via="explicit"
        )
        rendered = AppContext._render_comms_brief_ack(result)
        assert "head is v5" in rendered

    def test_idempotent_reack(self) -> None:
        result = BriefAckResult(name="project", version=5, head_version=5, already_acked=True, via="explicit")
        rendered = AppContext._render_comms_brief_ack(result)
        assert "already acked" in rendered


class TestRenderCommsFleetRow:
    def test_not_stale_at_the_exact_threshold(self) -> None:
        rendered = AppContext._render_comms_fleet_row(
            _agent(), project_head_version=None, acked_version=None, stale_after_s=600, heartbeat_age_s=600
        )
        assert "STALE" not in rendered

    def test_stale_one_second_past_the_threshold(self) -> None:
        rendered = AppContext._render_comms_fleet_row(
            _agent(), project_head_version=None, acked_version=None, stale_after_s=600, heartbeat_age_s=601
        )
        assert "STALE" in rendered

    def test_brief_cell_omitted_when_no_project_brief(self) -> None:
        rendered = AppContext._render_comms_fleet_row(
            _agent(), project_head_version=None, acked_version=None, stale_after_s=600, heartbeat_age_s=1
        )
        assert "brief" not in rendered

    def test_brief_cell_current(self) -> None:
        rendered = AppContext._render_comms_fleet_row(
            _agent(), project_head_version=5, acked_version=5, stale_after_s=600, heartbeat_age_s=1
        )
        assert "brief v5" in rendered
        assert "head" not in rendered

    def test_brief_cell_behind(self) -> None:
        rendered = AppContext._render_comms_fleet_row(
            _agent(), project_head_version=5, acked_version=4, stale_after_s=600, heartbeat_age_s=1
        )
        assert "brief v4 (head v5)" in rendered

    def test_brief_cell_unbriefed(self) -> None:
        rendered = AppContext._render_comms_fleet_row(
            _agent(), project_head_version=5, acked_version=None, stale_after_s=600, heartbeat_age_s=1
        )
        assert "brief unbriefed" in rendered

    def test_optional_cells_omitted_when_unset(self) -> None:
        rendered = AppContext._render_comms_fleet_row(
            _agent(model=None, task_id=None, last_note=None),
            project_head_version=None,
            acked_version=None,
            stale_after_s=600,
            heartbeat_age_s=1,
        )
        assert "model" not in rendered
        assert "task " not in rendered
        assert "note:" not in rendered

    def test_task_id_is_truncated(self) -> None:
        rendered = AppContext._render_comms_fleet_row(
            _agent(task_id="4f2a1c9e-full-uuid-here"),
            project_head_version=None,
            acked_version=None,
            stale_after_s=600,
            heartbeat_age_s=1,
        )
        assert "4f2a1c9e" in rendered
        assert "4f2a1c9e-full-uuid-here" not in rendered


class TestRenderCommsFleet:
    def test_header_names_total_and_per_status_counts(self) -> None:
        rows = [_agent(name="a", status="input_required"), _agent(name="b", status="active")]
        rendered = AppContext._render_comms_fleet(
            _fleet_window(rows),
            session=None,
            limit=20,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
            status_counts=_status_counts(rows),
        )
        assert "2 agents" in rendered
        assert "1 input_required" in rendered
        assert "1 active" in rendered
        assert "0 idle" in rendered

    def test_ordering_input_required_then_active_then_idle(self) -> None:
        rows = [
            _agent(name="idle-1", status="idle"),
            _agent(name="active-1", status="active"),
            _agent(name="parked-1", status="input_required"),
        ]
        rendered = AppContext._render_comms_fleet(
            _fleet_window(rows),
            session=None,
            limit=20,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
            status_counts=_status_counts(rows),
        )
        assert rendered.index("parked-1") < rendered.index("active-1") < rendered.index("idle-1")

    def test_session_scoped_header(self) -> None:
        rendered = AppContext._render_comms_fleet(
            _fleet_window([]),
            session="wave7",
            limit=20,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
            status_counts=_status_counts([]),
        )
        assert "wave7" in rendered

    def test_empty_unscoped(self) -> None:
        rendered = AppContext._render_comms_fleet(
            _fleet_window([]),
            session=None,
            limit=20,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
            status_counts=_status_counts([]),
        )
        assert "no agents registered" in rendered

    def test_empty_scoped_names_the_session(self) -> None:
        rendered = AppContext._render_comms_fleet(
            _fleet_window([]),
            session="wave7",
            limit=20,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
            status_counts=_status_counts([]),
        )
        assert "no agents registered" in rendered
        assert "wave7" in rendered

    def test_retired_trailer(self) -> None:
        rows = [_agent()]
        rendered = AppContext._render_comms_fleet(
            _fleet_window(rows, retired_count=3),
            session=None,
            limit=20,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
            status_counts=_status_counts(rows, retired_count=3),
        )
        assert "+3 retired" in rendered

    def test_elision_names_a_clamped_reask(self) -> None:
        rows = [_agent(name=f"a{i}") for i in range(4)]
        rendered = AppContext._render_comms_fleet(
            _fleet_window(rows),
            session=None,
            limit=2,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
            status_counts=_status_counts(rows),
        )
        assert "+2 more" in rendered
        assert "limit=4" in rendered

    def test_elision_reask_is_clamped_to_the_max_fleet_limit(self) -> None:
        rows = [_agent(name=f"a{i}") for i in range(_MAX_FLEET_LIMIT + 10)]
        rendered = AppContext._render_comms_fleet(
            _fleet_window(rows),
            session=None,
            limit=_MAX_FLEET_LIMIT - 1,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
            status_counts=_status_counts(rows),
        )
        assert f"limit={_MAX_FLEET_LIMIT}" in rendered

    def test_heartbeat_recency_orders_within_the_same_status(self) -> None:
        """Gap identified (fix-wave defect 3 audit): the existing ordering
        test above only pins the three-status precedence (parked > active >
        idle); no test previously proved 'within a group, most-recent
        heartbeat first' (spec §6) for two rows sharing the SAME status."""
        now = datetime.now(UTC)
        rows = [
            _agent(name="older", status="active", heartbeat_at=now - timedelta(minutes=10)),
            _agent(name="newer", status="active", heartbeat_at=now),
        ]
        rendered = AppContext._render_comms_fleet(
            _fleet_window(rows),
            session=None,
            limit=20,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
            status_counts=_status_counts(rows),
        )
        assert rendered.index("newer") < rendered.index("older")

    def test_elision_cuts_from_the_bottom_idle_and_oldest_first(self) -> None:
        """Gap identified (fix-wave defect 3 audit): no existing test proved
        row elision cuts from the BOTTOM of the sort order (idle/oldest rows
        out first, spec §6) so parked + freshest-active rows always survive
        a tight limit."""
        now = datetime.now(UTC)
        rows = [
            _agent(name="parked", status="input_required", heartbeat_at=now - timedelta(hours=1)),
            _agent(name="fresh-active", status="active", heartbeat_at=now),
            _agent(name="stale-active", status="active", heartbeat_at=now - timedelta(minutes=30)),
            _agent(name="oldest-idle", status="idle", heartbeat_at=now - timedelta(hours=2)),
        ]
        rendered = AppContext._render_comms_fleet(
            _fleet_window(rows),
            session=None,
            limit=3,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
            status_counts=_status_counts(rows),
        )
        assert "parked" in rendered
        assert "fresh-active" in rendered
        assert "stale-active" in rendered
        assert "oldest-idle" not in rendered
        assert "+1 more" in rendered


class TestRenderCommsFleetTrueStatusCounts:
    """v4 audit D1: `_render_comms_fleet` gains an OPTIONAL `status_counts`
    keyword (a true aggregate incl. `retired`, e.g. `AgentRegistry.roster().
    status_counts`). When given, it is TRUSTED for the header total,
    per-status segments, the elision `k`, and the retired trailer -- never
    re-derived from `window.rows` (which may be a display-capped window that
    disagrees with the truth past `_MAX_FLEET_LIMIT`).

    Contract decision (flagged in the report): `status_counts` is OPTIONAL,
    falling back to the pre-v4 window-derived computation when omitted,
    SOLELY because `test_comms_fleet_grouping.py` (frozen this contract
    wave) calls this helper without it at small N (where the two methods of
    counting coincide, so the fallback renders identically either way). The
    fallback is never exercised in production -- the real `_comms_fleet`
    handler always passes `status_counts` explicitly, pinned separately in
    `TestFleetHandlerSourcesTrueCountsFromRoster` above.
    """

    _STATUS_COUNTS = {
        "input_required": _TRUE_PARKED,
        "active": _TRUE_ACTIVE,
        "idle": _TRUE_IDLE,
        "retired": _TRUE_RETIRED,
    }

    @staticmethod
    def _disagreeing_window() -> AgentFleetWindow:
        """Exactly `_MAX_FLEET_LIMIT` rows whose OWN per-status breakdown
        (10/150/40) disagrees with `_STATUS_COUNTS` above (10/150/45) --
        proves the header trusts `status_counts`, never a window recount.
        `total_non_retired`/`retired_count` are likewise deliberately WRONG
        (200/99) so a caller that still reads them instead is caught too.
        """
        capped_idle_count = _MAX_FLEET_LIMIT - _TRUE_PARKED - _TRUE_ACTIVE  # 40, not the true 45
        rows = (
            [_agent(name=f"parked-{i}", status="input_required") for i in range(_TRUE_PARKED)]
            + [_agent(name=f"active-{i}", status="active") for i in range(_TRUE_ACTIVE)]
            + [_agent(name=f"idle-{i}", status="idle") for i in range(capped_idle_count)]
        )
        assert len(rows) == _MAX_FLEET_LIMIT
        return AgentFleetWindow(rows=rows, retired_count=99, total_non_retired=_MAX_FLEET_LIMIT)

    def test_status_counts_overrides_the_window_derived_header(self) -> None:
        rendered = AppContext._render_comms_fleet(
            self._disagreeing_window(),
            status_counts=self._STATUS_COUNTS,
            session=None,
            limit=_MAX_FLEET_LIMIT,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
        )
        assert f"{_TRUE_NON_RETIRED_TOTAL} agents" in rendered
        assert f"{_TRUE_PARKED} input_required" in rendered
        assert f"{_TRUE_ACTIVE} active" in rendered
        assert f"{_TRUE_IDLE} idle" in rendered
        assert f"+{_TRUE_RETIRED} retired" in rendered
        assert "+99 retired" not in rendered

    def test_cap_disclosure_variant_when_shown_equals_the_display_cap(self) -> None:
        rendered = AppContext._render_comms_fleet(
            self._disagreeing_window(),
            status_counts=self._STATUS_COUNTS,
            session=None,
            limit=_MAX_FLEET_LIMIT,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
        )
        remainder = _TRUE_NON_RETIRED_TOTAL - _MAX_FLEET_LIMIT
        assert f"+{remainder} more beyond the display cap ({_MAX_FLEET_LIMIT})" in rendered
        assert "re-run with limit" not in rendered

    def test_reask_variant_still_renders_when_shown_is_under_the_display_cap(self) -> None:
        """The re-ask variant (unchanged) must still fire when the caller's
        OWN `limit` (not the display cap) is what elides -- only
        `shown == _MAX_FLEET_LIMIT` triggers the cap-disclosure variant."""
        rendered = AppContext._render_comms_fleet(
            self._disagreeing_window(),
            status_counts=self._STATUS_COUNTS,
            session=None,
            limit=_MAX_FLEET_LIMIT - 1,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
        )
        assert "beyond the display cap" not in rendered
        assert f"re-run with limit={_MAX_FLEET_LIMIT}" in rendered


# =========================================================================== #
# Section C — the hostile RenderCase battery (spec §10: 19 cases) + the
# completeness pin (default FAIL).
# =========================================================================== #


async def _render_register_name(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_register(
        _agent(name=value), re_registered=False, registered_age_s=0, brief=None, brief_age_s=0
    )


async def _render_register_session(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_register(
        _agent(session=value), re_registered=False, registered_age_s=0, brief=None, brief_age_s=0
    )


async def _render_register_role(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_register(
        _agent(role=value), re_registered=False, registered_age_s=0, brief=None, brief_age_s=0
    )


async def _render_register_brief_author(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_register(
        _agent(),
        re_registered=False,
        registered_age_s=0,
        brief=_brief(created_by=value),
        brief_age_s=0,
    )


async def _render_heartbeat_name(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_heartbeat(
        _agent(name=value), project_head_version=None, project_acked_version=None
    )


async def _render_brief_get_name(value: str, _ctx: Any) -> str:
    coverage = BriefCoverage(name=value, head_version=1, total_agents=1, current_count=1, behind=[])
    return AppContext._render_comms_brief_get(_brief(name=value), 0, coverage, session=None)


async def _render_brief_get_author(value: str, _ctx: Any) -> str:
    coverage = BriefCoverage(name="project", head_version=1, total_agents=1, current_count=1, behind=[])
    return AppContext._render_comms_brief_get(_brief(created_by=value), 0, coverage, session=None)


async def _render_brief_get_behind_names(value: str, _ctx: Any) -> str:
    coverage = BriefCoverage(
        name="project",
        head_version=2,
        total_agents=2,
        current_count=1,
        behind=[BriefBehindEntry(agent_name=value, acked_version=1)],
    )
    return AppContext._render_comms_brief_get(_brief(version=2), 0, coverage, session=None)


async def _render_brief_publish_name(value: str, _ctx: Any) -> str:
    result = BriefPublishResult(brief=_brief(name=value), first_version=True)
    return AppContext._render_comms_brief_publish(
        result, skew_count=0, body_chars=1, warn_threshold_chars=4000, session=None
    )


async def _render_brief_publish_publisher(value: str, _ctx: Any) -> str:
    result = BriefPublishResult(brief=_brief(created_by=value), first_version=True)
    return AppContext._render_comms_brief_publish(
        result, skew_count=0, body_chars=1, warn_threshold_chars=4000, session=None
    )


async def _render_brief_ack_name(value: str, _ctx: Any) -> str:
    result = BriefAckResult(name=value, version=1, head_version=1, already_acked=False, via="explicit")
    return AppContext._render_comms_brief_ack(result)


async def _render_fleet_name(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_fleet_row(
        _agent(name=value),
        project_head_version=None,
        acked_version=None,
        stale_after_s=600,
        heartbeat_age_s=1,
    )


async def _render_fleet_role(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_fleet_row(
        _agent(role=value),
        project_head_version=None,
        acked_version=None,
        stale_after_s=600,
        heartbeat_age_s=1,
    )


async def _render_fleet_model(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_fleet_row(
        _agent(model=value),
        project_head_version=None,
        acked_version=None,
        stale_after_s=600,
        heartbeat_age_s=1,
    )


async def _render_fleet_task_id(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_fleet_row(
        _agent(task_id=value),
        project_head_version=None,
        acked_version=None,
        stale_after_s=600,
        heartbeat_age_s=1,
    )


async def _render_fleet_note(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_fleet_row(
        _agent(last_note=value),
        project_head_version=None,
        acked_version=None,
        stale_after_s=600,
        heartbeat_age_s=1,
    )


async def _render_fleet_session(value: str, _ctx: Any) -> str:
    rows = [_agent()]
    return AppContext._render_comms_fleet(
        _fleet_window(rows),
        session=value,
        limit=20,
        stale_after_s=600,
        project_head_version=None,
        acked_versions={},
        heartbeat_age_seconds={},
        status_counts=_status_counts(rows),
    )


# The FENCE cases (register.brief_body / brief_get.body) are deliberately
# NOT in this list -- see TestFencedBodyIntegrity below and the report's
# "genuine spec tension" flag: bodies are contractually verbatim/newline-
# preserving (render_fenced never sanitises), so `assert_render_injection_
# safe`'s assertion 1 ("no ADDED \n vs baseline") is definitionally violated
# by the "\n" entry in `_INJECTION_THREAT_CHARS` for ANY fenced field -- the
# two are mutually exclusive requirements, not a gap in this test file.
C1_RENDER_CASES: list[RenderCase] = [
    RenderCase("register.name", _render_register_name),
    RenderCase("register.session", _render_register_session),
    RenderCase("register.role", _render_register_role),
    RenderCase("register.brief_author", _render_register_brief_author),
    RenderCase("heartbeat.name", _render_heartbeat_name),
    RenderCase("brief_get.name", _render_brief_get_name),
    RenderCase("brief_get.author", _render_brief_get_author),
    RenderCase("brief_get.behind_names", _render_brief_get_behind_names),
    RenderCase("brief_publish.name", _render_brief_publish_name),
    RenderCase("brief_publish.publisher", _render_brief_publish_publisher),
    RenderCase("brief_ack.name", _render_brief_ack_name),
    RenderCase("fleet.name", _render_fleet_name),
    RenderCase("fleet.role", _render_fleet_role),
    RenderCase("fleet.model", _render_fleet_model),
    RenderCase("fleet.task_id", _render_fleet_task_id),
    RenderCase("fleet.note", _render_fleet_note),
    RenderCase("fleet.session", _render_fleet_session),
]

# The two FENCE-labeled cases from spec §10, tracked separately (see
# TestFencedBodyIntegrity) but STILL counted toward family coverage below --
# 'register'/'brief_get' are already covered by their non-fence cases above,
# so the completeness pin does not need these families exempted.
_FENCE_CASE_LABELS = {"register.brief_body", "brief_get.body"}


class TestC1RenderInjectionBattery:
    """spec §10: every RenderCase driven with every non-fence-breaking threat
    char + the row-forge payload, against the shared oracle."""

    @pytest.mark.parametrize("case", C1_RENDER_CASES, ids=lambda c: c.label)
    @pytest.mark.parametrize("threat", _INJECTION_THREAT_CHARS, ids=lambda t: f"U+{ord(t):04X}")
    async def test_no_comms_render_forges_a_row_under_injection(self, case: RenderCase, threat: str) -> None:
        hostile = f"benign{threat}{_ROW_FORGE_PAYLOAD}"
        baseline = await case.render("benign", None)
        hostile_out = await case.render(hostile, None)
        assert_render_injection_safe(baseline, hostile_out)

    def test_completeness_pin_default_fail(self) -> None:
        """spec §8/§10: assert_actions_covered(_COMMS_ACTIONS, C1_RENDER_CASES,
        exemptions={}) -- zero exemptions in C1 (every action renders at
        least one agent-controlled field)."""
        assert_actions_covered(_COMMS_ACTIONS, C1_RENDER_CASES, exemptions={})

    def test_every_action_has_at_least_one_registered_case(self) -> None:
        covered = {case.label.split(".", 1)[0] for case in C1_RENDER_CASES}
        assert covered == set(_COMMS_ACTIONS)


class TestFencedBodyIntegrity:
    """register.brief_body / brief_get.body (spec §10 FENCE cases): a body
    must round-trip byte-verbatim AND an embedded backtick run must never
    close the fence early -- the render_fenced sizing rule (ruling
    §ENFORCEMENT, render.py's own contract), confirmed at the CALL SITE
    rather than re-deriving render_fenced's own math (already pinned by
    Phase 0's test_render.py)."""

    _HOSTILE_BODY = f"line one\nline two ```` embedded```{_ROW_FORGE_PAYLOAD}"

    def test_register_body_round_trips_verbatim_inside_a_wider_fence(self) -> None:
        rendered = AppContext._render_comms_register(
            _agent(),
            re_registered=False,
            registered_age_s=0,
            brief=_brief(body=self._HOSTILE_BODY),
            brief_age_s=0,
        )
        self._assert_fence_integrity(rendered, self._HOSTILE_BODY)

    def test_brief_get_body_round_trips_verbatim_inside_a_wider_fence(self) -> None:
        coverage = BriefCoverage(name="project", head_version=1, total_agents=1, current_count=1, behind=[])
        rendered = AppContext._render_comms_brief_get(
            _brief(body=self._HOSTILE_BODY), 0, coverage, session=None
        )
        self._assert_fence_integrity(rendered, self._HOSTILE_BODY)

    @staticmethod
    def _assert_fence_integrity(rendered: str, body: str) -> None:
        assert body in rendered, "a fenced body must round-trip byte-verbatim"
        fence_lines = [line for line in rendered.splitlines() if line and set(line) == {"`"}]
        assert len(fence_lines) >= 2, "a fenced body must be bounded by two backtick-run fence lines"
        fence_width = len(fence_lines[0])
        assert fence_width > max_backtick_run(body), (
            "the fence must be strictly longer than any backtick run embedded in the body, "
            "so an embedded fence-shaped run can never close the fence early"
        )
        # No line OUTSIDE the fence boundaries is the forged row shape (the
        # payload is legitimately preserved INSIDE the fence -- that is
        # explicitly not a forgery, it is quoted content).
        open_index = rendered.splitlines().index(fence_lines[0])
        close_index = len(rendered.splitlines()) - 1 - rendered.splitlines()[::-1].index(fence_lines[-1])
        outside_lines = rendered.splitlines()[:open_index] + rendered.splitlines()[close_index + 1 :]
        assert not any(line.strip().startswith("- [#99 open] forged") for line in outside_lines)


# =========================================================================== #
# Section D — render-safety seam usage sanity (mypy strict / the AST pins
# already scan these call sites tree-wide once production code exists; here
# we only sanity-check the imports the comms surface is expected to use are
# the RIGHT ones, e.g. RenderSafetyError is importable from render.py).
# =========================================================================== #


def test_render_safety_error_is_importable_from_render_module() -> None:
    assert issubclass(RenderSafetyError, Exception)


def test_control_char_pattern_and_max_backtick_run_are_the_shared_seam() -> None:
    # Sanity: the comms battery's hostile fixtures ride the SAME threat class
    # sanitise.py/render.py already enforce -- not a locally re-derived one.
    assert CONTROL_CHAR_PATTERN.search("a\nb") is not None
    assert max_backtick_run("```") == 3
