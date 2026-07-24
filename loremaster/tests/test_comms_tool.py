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

import re
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
    _FINDING_ACTIONS,
    _INSTRUCTIONS,
    _MAX_FLEET_LIMIT,
    _TASK_ACTIONS,
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


# --------------------------------------------------------------------------- #
# LAZY access to the packet-03 message module and its fake.
#
# ⚠ THESE ARE CALL-TIME IMPORTS ON PURPOSE. ``loremaster.messages`` does not
# exist until packet 03 lands, and a MODULE-LEVEL import of it here would make
# this file UNCOLLECTABLE at clean HEAD — taking its ~700 pre-existing pins with
# it. RED and UNCOLLECTABLE are different states: a red test runs and fails for
# its own reason; an uncollectable module never loads.
#
# This contract shipped exactly that defect once (via ``_comms_fakes.py``, a
# SHARED fixture module — six suites went uncollectable, ~1,220 tests stopped
# being counted, and the tail read ``no tests collected``). It was invisible to
# every satisfiability run because those ran in scratch copies where the module
# EXISTS — finding #133. Call-time import keeps each packet-03a pin failing for
# its OWN reason instead of deleting the file from the run.
#
# (PLC0415 import-outside-top-level is an ignored house idiom in this repo.)
# --------------------------------------------------------------------------- #


def _msg() -> Any:
    """The packet-03 message module, imported at CALL time. See above."""
    import loremaster.messages

    return loremaster.messages


def _msg_fakes() -> Any:
    """The packet-03 message fake, imported at CALL time. See above."""
    import _message_fakes

    return _message_fakes


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
    name: str,
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
    message_ledger: Any = None,
    stale_heartbeat_s: int = 600,
    fleet_limit: int = 20,
    drain_limit: int = 20,
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
        message_ledger=message_ledger
        if message_ledger is not None
        else _msg_fakes().FakeMessageLedger(db=_msg_fakes().FakeMessageDatabase()),
        config=SimpleNamespace(
            comms=SimpleNamespace(
                stale_heartbeat_s=stale_heartbeat_s,
                fleet_limit=fleet_limit,
                drain_limit=drain_limit,
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


def _extract_skew_group_counts(rendered: str) -> list[int]:
    """Every count named inside a skew line's breakdown (``N at vM``, ``N at
    older versions``, ``N unbriefed``) — used to prove the groups SUM to the
    line's own ``{behind}`` total (design doc §5.3's counting law, applied
    inside one line — finding #96's fix), independent of the exact prose
    around them. Fails loudly (not silently returns ``[]``) when no skew
    line is present, so a caller that expected one gets a clear signal
    rather than a vacuous empty-list pass."""
    match = re.search(r"behind head v\d+ — (.+?); surfaces at their next heartbeat", rendered)
    assert match, f"no skew breakdown line found in: {rendered!r}"
    return [int(part.split(" ", 1)[0]) for part in match.group(1).split(", ")]


def _assert_skew_group_counts_sum_to_behind(rendered: str, expected_behind: int) -> None:
    """FIRST-CLASS invariant (design doc §5.3's counting law; §9.4: "Group
    counts SUM to {behind}") — every rendered skew group count must add up
    to the line's own claimed ``{behind}`` total. This is the exact
    invariant finding #96 exists to fix, and the exact invariant a
    per-VERSION (rather than per-AGENT) remainder count silently violates:
    a build computing ``len(remainder_versions)`` instead of
    ``sum(agents_per_version)`` passes every byte-exact string assertion a
    single-agent-per-version tail can express, because ``len`` and ``sum``
    coincide whenever the tail holds exactly one agent per version — the
    small-N blind spot the C1 adversary's finding #96 audit proved
    (REPORT-c1c-contract-adversary-96.md §P1). Asserted as its own named
    function — a first-class check, not an incidental aside next to a
    byte-exact string comparison — because the law must hold at every N,
    not just the values a hand-written literal happens to cover."""
    counts = _extract_skew_group_counts(rendered)
    assert sum(counts) == expected_behind, (
        f"SUM INVARIANT (design doc §9.4) VIOLATED: rendered group counts "
        f"{counts} sum to {sum(counts)}, but the line claims {expected_behind} "
        f"agents behind: {rendered!r}"
    )


# =========================================================================== #
# Section A — the ``_COMMS_ACTIONS`` dispatch table (spec §8)
# =========================================================================== #


class TestCommsActionsTable:
    """``_COMMS_ACTIONS`` is an introspectable dict[str, CommsActionSpec] —
    the exact shape spec §8 pins verbatim (six actions, D3: a SANCTIONED
    deviation from the tasks()/findings() if/elif house idiom)."""

    # packet 03 widens the table by three (send/drain/ack) — the growth points
    # server.py:1097-1099 already names. The set stays EXACT, never a subset.
    _EXPECTED_ACTIONS = {
        "register",
        "heartbeat",
        "brief_get",
        "brief_publish",
        "brief_ack",
        "fleet",
        "send",
        "drain",
        "ack",
    }

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
        for action in sorted(_COMMS_ACTIONS):
            assert action in description, f"the tool description must name {action!r}"

    async def test_description_names_every_action_as_a_WHOLE_WORD(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MINOR m3 (adversary). ``test_description_names_every_action`` uses bare
        substring membership, so ``ack`` passes VACUOUSLY — it is a substring of
        ``brief_ack``, already in the shipped description. A build that describes
        every OTHER action but never mentions ``send``/``drain``/``ack`` as their
        own verbs slips through. Word boundaries make each a real check
        (``\\back\\b`` matches ``'ack'`` but not the ``_ack`` inside ``brief_ack``,
        because ``_`` is a word character)."""
        tools = await _tools_by_name(monkeypatch)
        description = tools["lore_comms"].description or ""
        for action in sorted(_COMMS_ACTIONS):
            assert re.search(rf"\b{re.escape(action)}\b", description), (
                f"the tool description does not name {action!r} as a whole word — a substring "
                f"match (e.g. 'ack' inside 'brief_ack') is a vacuous check"
            )

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

    async def test_limit_declares_ge_one_in_the_tool_schema(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """v7 / finding #97: ``limit`` is ``ge=1`` AT THE TOOL BOUNDARY (design
        doc §6) — the MCP schema an agent reads must advertise the bound, and
        FastMCP's own pydantic validation must reject 0/-1 before the call is
        ever dispatched. ``Annotated[int | None, Field(ge=_MIN_COUNT)]`` renders
        as ``anyOf: [{type: integer, minimum: 1}, {type: null}]`` — probed live
        against this FastMCP version, not assumed.

        Deliberately paired with the dispatcher-level teaching ValueError
        (``TestFleetLimitBounds``): the schema bound is what an MCP client sees,
        the teaching error is what a caller reading the range gets. Neither
        alone satisfies §6 — see the report's escalation note on which message
        an MCP-boundary caller actually receives.
        """
        tools = await _tools_by_name(monkeypatch)
        limit_schema = (tools["lore_comms"].inputSchema or {})["properties"]["limit"]
        branches = limit_schema.get("anyOf", [limit_schema])
        integer_branches = [branch for branch in branches if branch.get("type") == "integer"]
        assert integer_branches, f"no integer branch in the limit schema: {limit_schema!r}"
        assert all(branch.get("minimum") == 1 for branch in integer_branches), (
            f"lore_comms' 'limit' must declare a ge=1 lower bound in its tool schema "
            f"(design doc §6, finding #97): {limit_schema!r}"
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

    async def test_unknown_agent_error_is_enriched_with_a_capped_non_retired_roster(self) -> None:
        """S2's ledger-level UnknownAgentError deliberately carries no
        roster (contract decision #4, REPORT-c1-contract-ledgers.md) -- the
        SERVER enriches it. Pin the enrichment, capped/counted.

        finding #95 (REPORT-c1b-contract-9495.md): the label is
        ``non-retired agents:`` -- not ``active agents:`` -- because the set
        it lists/counts is the whole non-retired partition (active + idle +
        input_required), matching the vocabulary the rest of the comms
        surface already uses for this same set (``coverage: all N
        non-retired agents at v5``; ``skew: N non-retired agents…``)."""
        db = FakeAgentDatabase()
        harness = _harness(agent_registry=FakeAgentRegistry(db=db))
        names = [f"agent-{i}" for i in range(_COVERAGE_NAMES_CAP + 2)]
        for name in names:
            await AppContext.comms(harness, action="register", agent=name, session="wave7", role="builder")
        with pytest.raises(UnknownAgentError) as exc_info:
            await AppContext.comms(harness, action="fleet", agent="ghost", session="wave7")
        message = str(exc_info.value)
        assert "non-retired agents:" in message
        assert f"(+{len(names) - _COVERAGE_NAMES_CAP} more)" in message

    async def test_enrichment_label_agrees_with_the_set_it_lists_and_counts(self) -> None:
        """finding #95: register one of EACH non-retired status (active,
        idle, input_required) plus one retired -- all three non-retired
        names must appear in the roster and be counted; the retired agent
        must be excluded from both the list and the count (the label-vs-set
        agreement this class of defect breaks)."""
        db = FakeAgentDatabase()
        harness = _harness(agent_registry=FakeAgentRegistry(db=db))
        await AppContext.comms(harness, action="register", agent="actor", session="wave7", role="builder")
        await AppContext.comms(harness, action="register", agent="idler", session="wave7", role="builder")
        await AppContext.comms(
            harness, action="heartbeat", agent="idler", session="wave7", status="idle"
        )
        await AppContext.comms(harness, action="register", agent="parked", session="wave7", role="builder")
        await AppContext.comms(
            harness, action="heartbeat", agent="parked", session="wave7", status="input_required"
        )
        await AppContext.comms(harness, action="register", agent="retiree", session="wave7", role="builder")
        await AppContext.comms(
            harness, action="heartbeat", agent="retiree", session="wave7", status="retired"
        )

        with pytest.raises(UnknownAgentError) as exc_info:
            await AppContext.comms(harness, action="fleet", agent="ghost", session="wave7")
        message = str(exc_info.value)
        assert "non-retired agents:" in message
        for name in ("actor", "idler", "parked"):
            assert name in message, f"{name!r} is non-retired and must appear in the roster: {message!r}"
        assert "retiree" not in message, f"a RETIRED agent must not appear in the roster: {message!r}"
        # Only 3 non-retired agents, well under the cap -- the count agrees
        # with the list (no elision suffix at all).
        assert "(+" not in message, message

    async def test_enrichment_roster_is_session_scoped_no_cross_session_leak(self) -> None:
        """adversary P2 finding #2 (REPORT-c1-audit-adversary.md): mutating
        away ``_comms_enrich_unknown_agent``'s session filter left 643 tests
        green while leaking OTHER sessions' agent names into a
        session-scoped caller's teaching roster -- nothing pinned this
        before. A ``wave7``-scoped caller must see ONLY ``wave7`` names."""
        db = FakeAgentDatabase()
        harness = _harness(agent_registry=FakeAgentRegistry(db=db))
        await AppContext.comms(harness, action="register", agent="mine", session="wave7", role="builder")
        await AppContext.comms(
            harness, action="register", agent="secret-a", session="secret", role="builder"
        )
        await AppContext.comms(
            harness, action="register", agent="secret-b", session="secret", role="builder"
        )

        with pytest.raises(UnknownAgentError) as exc_info:
            await AppContext.comms(harness, action="fleet", agent="ghost", session="wave7")
        message = str(exc_info.value)
        assert "mine" in message
        assert "secret-a" not in message and "secret-b" not in message, (
            f"cross-session leak: a wave7-scoped caller must never see another "
            f"session's agent names in its teaching roster: {message!r}"
        )

    async def test_enrichment_with_no_agents_registered_renders_none(self) -> None:
        """adversary P2 finding #3: the empty-roster branch renders
        ``non-retired agents: none`` -- untested before, and the LIKELIEST
        real-world trigger of this whole enrichment path (an agent's very
        first comms call in a brand-new session, before anyone has
        registered)."""
        harness = _harness()
        with pytest.raises(UnknownAgentError) as exc_info:
            await AppContext.comms(harness, action="fleet", agent="ghost", session="wave7")
        message = str(exc_info.value)
        assert "non-retired agents: none" in message

    async def test_label_and_count_agree_at_scale_with_mixed_statuses_above_the_cap(self) -> None:
        """adversary P2 finding #5: the label/set agreement pin above is
        only N=4 -- this proves it holds ABOVE ``_MAX_FLEET_LIMIT`` (200)
        with a genuine mix of every status, including retired, mirroring
        the scale where 3 of C1's 5 confirmed defects actually lived.
        Uses the registry directly (mirrors the sibling D1 scale test
        below) -- 220 individual ``AppContext.comms`` round trips would be
        needlessly slow for a fixture this size."""
        db = FakeAgentDatabase()
        harness = _harness(agent_registry=FakeAgentRegistry(db=db))
        active_count, idle_count, parked_count, retired_count = 150, 45, 15, 10
        for i in range(active_count):
            await harness.agent_registry.register(f"active-{i:03d}", session="wave7", role="builder")
        for i in range(idle_count):
            name = f"idle-{i:03d}"
            await harness.agent_registry.register(name, session="wave7", role="builder")
            await harness.agent_registry.touch(name, session="wave7", status="idle")
        for i in range(parked_count):
            name = f"parked-{i:03d}"
            await harness.agent_registry.register(name, session="wave7", role="builder")
            await harness.agent_registry.touch(name, session="wave7", status="input_required")
        for i in range(retired_count):
            name = f"retired-{i:03d}"
            await harness.agent_registry.register(name, session="wave7", role="builder")
            await harness.agent_registry.touch(name, session="wave7", status="retired")

        total_non_retired = active_count + idle_count + parked_count
        assert total_non_retired > _MAX_FLEET_LIMIT, "sanity: fixture must genuinely cross the cap"

        with pytest.raises(UnknownAgentError) as exc_info:
            await AppContext.comms(harness, action="fleet", agent="ghost", session="wave7")
        message = str(exc_info.value)
        assert "non-retired agents:" in message
        true_remainder = total_non_retired - _COVERAGE_NAMES_CAP
        assert f"(+{true_remainder} more)" in message, (
            f"expected the TRUE non-retired total ({total_non_retired}) minus "
            f"the {_COVERAGE_NAMES_CAP}-name cap, computed over EVERY "
            f"non-retired status (active+idle+input_required) -- not just "
            f"'active' rows, and never re-derived from a display-capped "
            f"window: {message!r}"
        )
        for i in range(retired_count):
            assert f"retired-{i:03d}" not in message, "a retired agent leaked into the roster"

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

    async def test_the_publishers_own_next_heartbeat_is_honestly_silent(self) -> None:
        """§9.2's v7 consequence (finding #98): "the author's post-publish
        heartbeat is now honestly silent". Today the author is nagged, at every
        heartbeat, to catch up on the brief IT wrote — the most visible face of
        the phantom-straggler defect.
        """
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v1"
        )
        rendered = str(await AppContext.comms(harness, action="heartbeat", agent="lead", session="wave7"))
        assert rendered.count("\n") == 0, f"a current agent's heartbeat is ONE line: {rendered!r}"
        assert rendered == "heartbeat lead — status active"


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

    async def test_coverage_never_names_the_publisher_among_the_behind(self) -> None:
        """§9.3's v7 consequence (finding #98): the author counts at head in the
        coverage NUMERATOR and is absent from the behind LIST — by an ordinary
        stored ack, not a render carve-out. Pins the numerator AND the names: a
        build that merely filtered the author out of the list while leaving the
        numerator alone would render '1/3 ... behind: fixer-b, fixer-c' and the
        three numbers would stop agreeing with each other.
        """
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await _register(harness, name="fixer-b", session="wave7")
        await _register(harness, name="fixer-c", session="wave7")
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="the plan"
        )
        rendered = str(
            await AppContext.comms(
                harness, action="brief_get", agent="lead", session="wave7", name="project"
            )
        )
        assert (
            "coverage (session wave7): 1/3 non-retired agents at v1; "
            "behind: fixer-b (unbriefed), fixer-c (unbriefed)"
        ) in rendered
        assert "lead (unbriefed)" not in rendered


class TestBriefPublishAction:
    """v7 / finding #98 note that governs EVERY fixture below: ``publish``
    SELF-ACKS its author (design doc §5.1 step 2), so the PUBLISHING agent is
    never in its own skew count. Each fixture therefore uses a DEDICATED
    publisher ('lead') alongside the cohort under test — which both keeps the
    behind-sets as rich as they were pre-#98 AND makes the publisher's
    exclusion visible as a difference (a build that still counts the author
    renders a behind total one HIGHER than every byte-exact line below).
    """

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
            )
        )
        assert "brief 'project' v1 published by fixer-b" in rendered
        assert "first version" in rendered

    async def test_the_publisher_self_acks_at_the_version_it_just_published(self) -> None:
        """THE #98 wiring pin: the dispatcher must hand ``publish`` the acting
        agent's ROW ID so the ledger can write the ``via='publish'`` self-ack
        edge. Reads the stored edge back through the ledger, not the render —
        a render-only pin could be faked by a carve-out that hides the author
        from the behind list without ever recording that it read its own brief.
        """
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v1"
        )
        lead_id = FakeAgentRegistry._agent_id("wave7", "lead")
        assert await harness.brief_ledger.acked_version(agent_id=lead_id, name="project") == 1
        probe = await harness.brief_ledger.ack(
            agent_id=lead_id, agent_name="lead", name="project", version=1, via="explicit"
        )
        assert probe.already_acked is True, "the author's own explicit ack is the idempotent path (§9.5)"
        assert probe.via == "publish", "the stored self-ack must record the THIRD vocabulary word"

    @pytest.mark.parametrize("brief_name", ["project", "wave7", "base"])
    async def test_the_publisher_self_acks_under_ANY_brief_name_not_just_project(
        self, brief_name: str
    ) -> None:
        """BLOCKER pin (contract-adversary §1): the self-ack wiring must be
        NAME-AGNOSTIC. A build that passes ``agent_id`` only for the 'project'
        brief —

            agent_id=agent_row.id if name == BRIEF_NAME_PROJECT else None

        — is a one-line inference from §5.3's "only 'project' rides heartbeat and
        fleet", and it passed the ENTIRE pre-adversary contract (832 passed, 0
        failed, zero mypy delta) with finding #98 fully intact for every OTHER
        brief name. The cause was a fixture MONOCULTURE: all 37 ``brief_publish``
        calls at the tool/handler seam used ``name="project"``, and the ledger
        pins — which do use a wave name — pass ``agent_id`` themselves, so they
        structurally cannot see a SERVER that declines to pass it.

        §5.1 step 2 is unconditional: publish self-acks its author, full stop.
        The parametrisation is the pin: at least one value the code could branch
        on must differ.
        """
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await _register(harness, name="fixer-b", session="wave7")
        await AppContext.comms(
            harness,
            action="brief_publish",
            agent="lead",
            session="wave7",
            name=brief_name,
            body="the standing instruction",
        )
        lead_id = FakeAgentRegistry._agent_id("wave7", "lead")
        probe = await harness.brief_ledger.ack(
            agent_id=lead_id, agent_name="lead", name=brief_name, version=1, via="explicit"
        )
        assert probe.already_acked is True, (
            f"the author of brief {brief_name!r} must already be acked to it — the self-ack "
            f"is not conditional on the brief NAME (§5.1 step 2)"
        )
        assert probe.via == "publish"
        # ... and it shows in the served consequence line: only 'fixer-b' is behind.
        rendered = str(
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="lead",
                session="wave7",
                name=brief_name,
                body="the standing instruction, v2",
            )
        )
        # The skew TAIL is auto_ack_at_register-aware (pkt02): only the
        # standing 'project' brief surfaces universally at heartbeat; a
        # non-'project' brief with an unbriefed agent behind teaches the
        # brief_get path for those unbriefed agents instead.
        expected_tail = (
            "surfaces at their next heartbeat"
            if brief_name == "project"
            else (
                "ackers see it at next heartbeat — unbriefed agents only via "
                f"brief_get name='{brief_name}'"
            )
        )
        assert (
            f"skew (session wave7): 1 non-retired agents behind head v2 — 1 unbriefed; {expected_tail}"
        ) in rendered, f"the author of {brief_name!r} must not be counted behind itself: {rendered!r}"

    async def test_the_self_ack_is_keyed_by_the_agent_row_id_never_the_agent_name(self) -> None:
        """The edge is ``agent->briefed->brief``: only the acting agent's opaque
        ROW ID can carry it — never the agent's display NAME. A build that keyed
        the self-ack edge on the name string ``'lead'`` (rather than the uuid5
        row id ``_agent_id('wave7', 'lead')``) writes an ack under an endpoint
        that is not a real agent row, and the true author stays a phantom
        straggler. The publishing identity is now the acting agent itself (the
        old ``created_by`` display override is gone), so the discriminator is
        the row-id-vs-name distinction, not a third-party name.
        """
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await AppContext.comms(
            harness,
            action="brief_publish",
            agent="lead",
            session="wave7",
            name="project",
            body="v1",
        )
        lead_id = FakeAgentRegistry._agent_id("wave7", "lead")
        assert await harness.brief_ledger.acked_version(agent_id=lead_id, name="project") == 1
        assert await harness.brief_ledger.acked_version(agent_id="lead", name="project") is None

    async def test_zero_behind_renders_no_skew_line_through_the_tool(self) -> None:
        """THE REACHABILITY PIN (design doc §9.4, v7): "a single-agent fleet
        publishing renders NO skew line ... end-to-end pinned, not just
        render-unit-tested".

        Before #98 this branch was UNREACHABLE through the tool: the publisher
        was always counted behind its own brief, so ``behind >= 1`` for every
        possible call and the omission clause could never fire (live receipt:
        ``skew: 1 non-retired agents behind head v2 — 1 at v1`` in a store whose
        only agent IS the publisher). A pin that only drove ``_render_comms_
        brief_publish`` with an empty ``behind`` list proved nothing about that.
        """
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        first = str(
            await AppContext.comms(
                harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v1"
            )
        )
        second = str(
            await AppContext.comms(
                harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v2"
            )
        )
        for rendered in (first, second):
            assert "skew" not in rendered, (
                f"the sole agent in scope IS the publisher — it has read what it wrote, so "
                f"nobody is behind and the skew line must be omitted entirely: {rendered!r}"
            )
            assert "behind" not in rendered
        assert "brief 'project' v2 published by lead" in second

    async def test_skew_line_counts_non_retired_agents_behind(self) -> None:
        """v2 scoping ruling: this call carries an explicit session='wave7'
        -- the skew line MUST carry the '(session wave7)' tag (the same
        defect class as test_full_coverage_variant above, on brief_publish's
        twin surface, spec §9.4). v6 (finding #96): the two non-publisher
        agents registered before ANY brief existed, so at the v2 check they
        have NEVER acked anything -- the byte-exact assertion below pins the
        full REWRITTEN grammar (never-acked renders as its own 'unbriefed'
        word, not a fabricated 'had acked v1 or older'). v7 (#98): 'lead'
        publishes and is NOT among the 2 behind -- a build that still counts
        the author renders '3 non-retired agents behind'."""
        harness = _harness()
        await _register(harness, name="lead", role="lead")
        await _register(harness, name="fixer-b")
        await _register(harness, name="fixer-c")
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v1"
        )
        rendered = str(
            await AppContext.comms(
                harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v2"
            )
        )
        assert (
            "skew (session wave7): 2 non-retired agents behind head v2 — 2 unbriefed; "
            "surfaces at their next heartbeat"
        ) in rendered
        assert _extract_skew_group_counts(rendered) == [2]

    async def test_skew_line_is_fleet_wide_when_session_is_omitted(self) -> None:
        """v2 scoping law, brief_publish's twin of the brief_get roster
        test: omitting session= renders the unscoped, fleet-wide skew count
        with no '(session ...)' tag. v6: both non-publisher agents are
        unbriefed (never acked anything) -- byte-exact on the rewritten
        grammar. The two behind agents sit in DIFFERENT sessions (wave8) from
        the publisher (wave7), so a fleet-wide count is the only way to reach 2."""
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await _register(harness, name="scout-c", session="wave8")
        await _register(harness, name="scout-d", session="wave8")
        rendered = str(
            await AppContext.comms(
                harness, action="brief_publish", agent="lead", name="project", body="v1"
            )
        )
        assert "(session" not in rendered
        assert "v0" not in rendered
        assert (
            "skew: 2 non-retired agents behind head v1 — 2 unbriefed; "
            "surfaces at their next heartbeat"
        ) in rendered

    async def test_skew_line_is_session_scoped_when_session_is_explicit(self) -> None:
        """Same fixed state as above, published with an explicit session=
        -- the skew roster must be session-filtered, not fleet-wide. v6:
        byte-exact on the rewritten grammar. The scoped count (1: helper-d)
        and the fleet-wide count (2: helper-d + scout-c) are DIFFERENT
        numbers here, so a build that ignored the scope cannot pass by
        coincidence."""
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await _register(harness, name="helper-d", session="wave7")
        await _register(harness, name="scout-c", session="wave8")
        rendered = str(
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="lead",
                session="wave7",
                name="project",
                body="v1",
            )
        )
        assert (
            "skew (session wave7): 1 non-retired agents behind head v1 — 1 unbriefed; "
            "surfaces at their next heartbeat"
        ) in rendered

    async def test_first_publish_never_fabricates_v0(self) -> None:
        """THE KILLER PIN for finding #96: a FIRST publish (v1) with agents
        who registered before any brief existed must render them as their
        OWN 'unbriefed' group -- never as having 'acked v0', a version that
        has never existed (old code computed prior = result.brief.version -
        1 = 1 - 1 = 0)."""
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await _register(harness, name="fixer-b", session="wave7")
        await _register(harness, name="fixer-c", session="wave7")
        rendered = str(
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="lead",
                session="wave7",
                name="project",
                body="v1 body",
            )
        )
        assert "v0" not in rendered, f"fabricated a version that never existed: {rendered!r}"
        assert "unbriefed" in rendered
        assert (
            "skew (session wave7): 2 non-retired agents behind head v1 — 2 unbriefed; "
            "surfaces at their next heartbeat"
        ) in rendered
        assert _extract_skew_group_counts(rendered) == [2]

    async def test_skew_breakdown_groups_repeated_version_then_unbriefed_last(self) -> None:
        """Design doc §9.4's own worked example, reproduced against the real
        stack: a repeated acked-version group ('3 at v1') plus an unbriefed
        group, in that order, summing to the line's own behind count --
        never a computed version-1."""
        harness = _harness()
        brief_ledger = harness.brief_ledger
        await _register(harness, name="lead", session="wave7", role="lead")
        for name in ("acker-1", "acker-2", "acker-3", "never-acked"):
            await _register(harness, name=name, session="wave7")
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v1"
        )
        for acker in ("acker-1", "acker-2", "acker-3"):
            await brief_ledger.ack(
                agent_id=FakeAgentRegistry._agent_id("wave7", acker),
                agent_name=acker,
                name="project",
                version=1,
                via="explicit",
            )
        # v2 -- nobody but the author acks it, so the four non-publishers are
        # behind at the check (three at v1, one never-acked).
        rendered = str(
            await AppContext.comms(
                harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v2"
            )
        )
        assert "v0" not in rendered
        assert (
            "skew (session wave7): 4 non-retired agents behind head v2 — 3 at v1, 1 unbriefed; "
            "surfaces at their next heartbeat"
        ) in rendered
        assert _extract_skew_group_counts(rendered) == [3, 1]

    async def test_skew_breakdown_multiple_distinct_stored_versions_descending(self) -> None:
        """Three agents each acked a DIFFERENT stored version (v1, v2, v3);
        head is v4. Groups render DESCENDING by version, and every named
        version is a real, brief_get-able stored version -- never an
        arithmetic version-1 the caller invented."""
        harness = _harness()
        brief_ledger = harness.brief_ledger
        await _register(harness, name="lead", session="wave7", role="lead")
        for name in ("acker-v1", "acker-v2", "acker-v3", "never-acked"):
            await _register(harness, name=name, session="wave7")
        for version, acker in ((1, "acker-v1"), (2, "acker-v2"), (3, "acker-v3")):
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="lead",
                session="wave7",
                name="project",
                body=f"v{version} body",
            )
            await brief_ledger.ack(
                agent_id=FakeAgentRegistry._agent_id("wave7", acker),
                agent_name=acker,
                name="project",
                version=version,
                via="explicit",
            )
        rendered = str(
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="lead",
                session="wave7",
                name="project",
                body="v4 body",
            )
        )
        assert "v0" not in rendered
        assert (
            "skew (session wave7): 4 non-retired agents behind head v4 — "
            "1 at v3, 1 at v2, 1 at v1, 1 unbriefed; surfaces at their next heartbeat"
        ) in rendered
        assert _extract_skew_group_counts(rendered) == [1, 1, 1, 1]

    async def test_unbriefed_count_never_merges_into_a_version_group(self) -> None:
        """Distinguishes 'never acked' from any acked-version count even
        when they happen to share the same size -- guards a grouping bug
        that folds a None acked_version into a numeric bucket (e.g. a naive
        Counter needing a fabricated key for None)."""
        harness = _harness()
        brief_ledger = harness.brief_ledger
        await _register(harness, name="lead", session="wave7", role="lead")
        for name in ("acker-a", "acker-b", "never-a", "never-b"):
            await _register(harness, name=name, session="wave7")
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v1"
        )
        for acker in ("acker-a", "acker-b"):
            await brief_ledger.ack(
                agent_id=FakeAgentRegistry._agent_id("wave7", acker),
                agent_name=acker,
                name="project",
                version=1,
                via="explicit",
            )
        rendered = str(
            await AppContext.comms(
                harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v2"
            )
        )
        assert (
            "skew (session wave7): 4 non-retired agents behind head v2 — 2 at v1, 2 unbriefed; "
            "surfaces at their next heartbeat"
        ) in rendered
        assert _extract_skew_group_counts(rendered) == [2, 2]

    async def test_cap_plus_one_wiring_reaches_the_render_uncapped(self) -> None:
        """Wiring pin: the HANDLER must hand the render helper the FULL
        ``coverage.behind`` list (``BriefCoverage.behind`` is documented NOT
        capped -- capping is a render-layer concern, §S3). If the handler
        pre-truncated it (e.g. ``coverage.behind[:_SKEW_BREAKDOWN_CAP]``)
        the render's own cap+remainder logic would never see the tail, and
        the remainder group would silently vanish -- a defect the render-
        unit-level cap tests alone cannot see, since they hand the render
        helper an already-complete ``behind`` list directly."""
        from loremaster.server import _SKEW_BREAKDOWN_CAP

        cap = _SKEW_BREAKDOWN_CAP
        harness = _harness()
        brief_ledger = harness.brief_ledger
        await _register(harness, name="lead", session="wave7", role="lead")
        names = [f"acker-{i}" for i in range(cap + 1)]
        for name in names:
            await _register(harness, name=name, session="wave7")
        for version, acker in enumerate(names, start=1):
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="lead",
                session="wave7",
                name="project",
                body=f"v{version} body",
            )
            await brief_ledger.ack(
                agent_id=FakeAgentRegistry._agent_id("wave7", acker),
                agent_name=acker,
                name="project",
                version=version,
                via="explicit",
            )
        rendered = str(
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="lead",
                session="wave7",
                name="project",
                body="head body",
            )
        )
        assert "at older versions" in rendered, (
            f"remainder group missing -- handler likely pre-truncated coverage.behind: {rendered!r}"
        )
        counts = _extract_skew_group_counts(rendered)
        assert sum(counts) == cap + 1
        assert len(counts) == cap + 1  # cap named groups + 1 remainder group, all counts 1 here

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


class TestTheFirstVersionLineTeachesAnAckMechanismThatACTUALLYEXISTS:
    """THE EIGHTH §5.3 INSTANCE (cold audit REPORT-c1d-audit-979899.md §DEFECT):
    ``_render_comms_brief_publish``'s first-version variant appends
    ``" — first version; agents ack at register"`` for **every** brief name, but
    ``_comms_register`` auto-acks ONLY ``BRIEF_NAME_PROJECT``. For every other
    name that clause teaches a mechanism THAT DOES NOT EXIST — an agent reading
    it waits forever for an ack that never comes instead of calling ``brief_ack``
    — and it contradicts the skew line printed directly beneath it, which
    correctly reports those same agents as ``unbriefed``.

    Why the whole suite was green: the only assertion of that line
    (test_comms_wiring.py:609) used ``name='project'`` — the ONE name for which
    the claim is true. That is PARAMETER-VALUE MONOCULTURE, the same class that
    let a ``if name == BRIEF_NAME_PROJECT`` self-ack build pass the entire
    pre-adversary contract. Finding #98 closed the monoculture for the SELF-ACK;
    nobody closed it for the RENDER — and #98 is exactly what promotes
    non-'project' briefs to a first-class, routinely-exercised flow.

    The law (design doc §5.3 + corollaries): a served line may only describe what
    is actually TRUE of the thing it describes. Same family as a count computed
    over a set its label does not name, and a version that does not exist.

    Every test below drives the REAL ``_comms_register``/``_comms_brief_publish``
    handlers, so the register-time auto-ack under test is production's own.
    """

    _PROJECT = "project"
    _REGISTER_PROMISE = "agents ack at register"
    _EXPLICIT_ACK_TEACHING = "agents ack with lore_comms action=brief_ack"

    @pytest.mark.parametrize("brief_name", ["project", "wave9", "base"])
    async def test_only_the_project_brief_promises_the_register_time_ack(
        self, brief_name: str
    ) -> None:
        """THE KILLER PIN. Publish a FIRST version through the tool seam under
        three names; the register-teaching clause may appear for exactly the one
        name whose register-time ack actually exists. A build that appends it
        unconditionally (today's) goes RED on 'wave9' and 'base'; a build that
        drops it everywhere goes RED on 'project' (where the promise is TRUE and
        load-bearing — §1's bootstrap arc depends on it)."""
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        rendered = str(
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="lead",
                session="wave7",
                name=brief_name,
                body="the standing instruction",
            )
        )
        assert f"brief '{brief_name}' v1 published by lead" in rendered
        assert "first version" in rendered, "the first-version variant must still fire for any name"
        assert (self._REGISTER_PROMISE in rendered) == (brief_name == self._PROJECT), (
            f"the register-time auto-ack exists ONLY for {self._PROJECT!r} "
            f"(_comms_register hardcodes BRIEF_NAME_PROJECT) — a first-version line "
            f"under name={brief_name!r} may promise it IFF it is true: {rendered!r}"
        )
        if brief_name != self._PROJECT:
            assert self._EXPLICIT_ACK_TEACHING in rendered, (
                f"a non-{self._PROJECT!r} first version must teach the ack call that DOES "
                f"exist (action=brief_ack) — dropping the false clause without naming the "
                f"real mechanism leaves the agent with no way to become briefed: {rendered!r}"
            )

    async def test_register_acks_the_project_brief_and_ONLY_the_project_brief(self) -> None:
        """The mechanism the render must not misdescribe, measured directly and
        DIFFERENTIALLY: with BOTH a 'project' head and a 'wave9' head standing,
        a fresh register writes an ack for 'project' and none for 'wave9'.

        The differential is the discriminator: a probe that only checked the
        'wave9' side would also pass against a build where register acks NOTHING
        at all — and would then wrongly condemn the 'project' clause too."""
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        for brief_name in (self._PROJECT, "wave9"):
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="lead",
                session="wave7",
                name=brief_name,
                body="the standing instruction",
            )
        await _register(harness, name="newbie", session="wave7")
        newbie_id = FakeAgentRegistry._agent_id("wave7", "newbie")
        assert (
            await harness.brief_ledger.acked_version(agent_id=newbie_id, name=self._PROJECT) == 1
        ), "register DOES auto-ack the project head — the 'ack at register' clause is TRUE there"
        assert await harness.brief_ledger.acked_version(agent_id=newbie_id, name="wave9") is None, (
            "register does NOT ack any other brief — every line that says otherwise is a lie"
        )

    async def test_the_first_version_line_does_not_contradict_the_skew_line_beneath_it(self) -> None:
        """ONE render, TWO clauses, in direct contradiction on today's build:
        line 1 says the agents will ack at register; line 2 says they are
        ``unbriefed`` — and they stay unbriefed forever, because registering
        never acks a non-'project' brief. Asserted as a COHERENCE property of the
        rendered block, not as a byte-exact string, so it survives any rewording
        the builder chooses (see REPORT-c1e-contract-eighth.md)."""
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await _register(harness, name="fixer-b", session="wave7")
        rendered = str(
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="lead",
                session="wave7",
                name="wave9",
                body="the standing instruction",
            )
        )
        assert "1 unbriefed" in rendered, (
            f"fixture check: 'fixer-b' must really be behind and unbriefed here: {rendered!r}"
        )
        assert self._REGISTER_PROMISE not in rendered, (
            f"the publish line promises an ack the skew line beneath it already reports as "
            f"NOT HAVING HAPPENED, and which registering will never perform for a "
            f"non-'project' brief: {rendered!r}"
        )

    async def test_an_agent_that_registers_AFTER_a_non_project_publish_is_still_unbriefed(
        self,
    ) -> None:
        """The promise, taken at its word and measured: register the agent AFTER
        the wave9 publish (the exact reading the served line invites) and it is
        STILL unbriefed — the register-time ack never fires, and the very next
        publish's skew line says so."""
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await AppContext.comms(
            harness,
            action="brief_publish",
            agent="lead",
            session="wave7",
            name="wave9",
            body="v1 — the standing instruction",
        )
        await _register(harness, name="newbie", session="wave7")
        newbie_id = FakeAgentRegistry._agent_id("wave7", "newbie")
        assert await harness.brief_ledger.acked_version(agent_id=newbie_id, name="wave9") is None
        rendered = str(
            await AppContext.comms(
                harness,
                action="brief_publish",
                agent="lead",
                session="wave7",
                name="wave9",
                body="v2 — the standing instruction",
            )
        )
        assert (
            "skew (session wave7): 1 non-retired agents behind head v2 — 1 unbriefed; "
            "ackers see it at next heartbeat — unbriefed agents only via brief_get name='wave9'"
        ) in rendered, (
            f"an agent that registered AFTER the wave9 publish is STILL unbriefed — which is "
            f"exactly what the v1 line's 'ack at register' clause denies: {rendered!r}"
        )


class TestBriefAckAction:
    """v7 (finding #98): every fixture here uses a DEDICATED publisher, and
    'fixer-b' registers BEFORE the brief exists (§1 bootstrap: no edge). An
    agent that acks a version IT published now hits the idempotent path
    instead — pinned as its own case at the end, per §9.5's new v7 clause,
    rather than being allowed to quietly hollow out the head/behind cases.
    """

    @staticmethod
    async def _bootstrap_publisher_and_acker(harness: Any) -> None:
        await _register(harness, name="lead", session="wave7", role="lead")
        await _register(harness, name="fixer-b", session="wave7")  # bootstrap: no brief yet, no edge

    async def test_head_ack(self) -> None:
        harness = _harness()
        await self._bootstrap_publisher_and_acker(harness)
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v1"
        )
        rendered = str(
            await AppContext.comms(
                harness, action="brief_ack", agent="fixer-b", session="wave7", name="project", version=1
            )
        )
        assert rendered == "acked brief 'project' v1 (head)"

    async def test_behind_ack_is_legal_and_honest(self) -> None:
        harness = _harness()
        await self._bootstrap_publisher_and_acker(harness)
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v1"
        )
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v2"
        )
        rendered = str(
            await AppContext.comms(
                harness, action="brief_ack", agent="fixer-b", session="wave7", name="project", version=1
            )
        )
        assert rendered == (
            "acked brief 'project' v1 — head is v2; catch up: "
            "lore_comms action=brief_get name='project'"
        ), (
            "v8 §9.5 (audit instance TEN): the teach carries an EXPLICIT name= for EVERY "
            "name, 'project' included — the uniform template is what kills the default-"
            "resolution class instead of special-casing it. This assertion previously "
            "pinned the BARE `brief_get` (the old world) and is updated here, per the "
            "repo law that tests written before a semantic change certify the corpse."
        )

    async def test_nonexistent_version_teaches_the_real_head(self) -> None:
        harness = _harness()
        await self._bootstrap_publisher_and_acker(harness)
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v1"
        )
        with pytest.raises(UnknownBriefVersionError) as exc_info:
            await AppContext.comms(
                harness, action="brief_ack", agent="fixer-b", session="wave7", name="project", version=9
            )
        assert "v1" in str(exc_info.value)

    async def test_reack_is_idempotent(self) -> None:
        harness = _harness()
        await self._bootstrap_publisher_and_acker(harness)
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v1"
        )
        first = str(
            await AppContext.comms(
                harness, action="brief_ack", agent="fixer-b", session="wave7", name="project", version=1
            )
        )
        second = str(
            await AppContext.comms(
                harness, action="brief_ack", agent="fixer-b", session="wave7", name="project", version=1
            )
        )
        assert "already acked" not in first, "the FIRST explicit ack writes a genuinely new edge"
        assert second == "already acked brief 'project' v1 — no new edge"

    async def test_an_author_acking_its_own_just_published_version_is_already_acked(self) -> None:
        """§9.5's NEW v7 case (finding #98's consequence sweep): the author's
        ``via=publish`` edge already exists, so its own explicit ack of that
        version renders the idempotent variant — never a second edge, never a
        UNIQUE(in,out) explosion surfacing as a store error.
        """
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v1"
        )
        rendered = str(
            await AppContext.comms(
                harness, action="brief_ack", agent="lead", session="wave7", name="project", version=1
            )
        )
        assert rendered == "already acked brief 'project' v1 — no new edge"


class TestTheBehindAckTeachNamesTheBriefItIsABOUT:
    """THE TENTH §5.3 INSTANCE (design doc v8 §9.5 + the §9.7 mechanism sweep,
    row 11): ``_render_comms_brief_ack``'s behind-ack variant teaches
    ``catch up: lore_comms action=brief_get`` — **bare**. ``brief_get``'s
    ``name`` is OPTIONAL and DEFAULTS to ``BRIEF_NAME_PROJECT``
    (``_comms_brief_get``: ``name if name is not None else BRIEF_NAME_PROJECT``),
    so an agent that acks behind on 'wave9' and follows our own served
    instruction VERBATIM reads the **project** brief. The taught command does
    not do the taught thing — and it fails SILENTLY: a brief is served, just
    the wrong one, so the reader has no signal that it caught up on nothing.

    The law (design doc §5.3's v8 mechanism-promise corollary): *a served line
    may only promise a mechanism that will actually RUN for the input it is
    describing.* Litmus: if the reader ran the taught command **with its
    DEFAULTS**, would the promised thing happen for THIS input? A bare
    ``brief_get`` under a 'wave9' line fails that litmus outright.

    The fix (v8 §9.5, ruled): explicit ``name='{name}'`` for EVERY name,
    'project' included — a UNIFORM template kills the whole default-resolution
    class rather than special-casing it, at a one-byte-stability cost on the
    project fixture that the spec takes deliberately.

    Why the whole suite was green: every brief_ack fixture in this module used
    ``name='project'`` — the ONE name whose default resolution is correct.
    Parameter-value monoculture, the same class that hid instances 8 and 9.

    Every test below drives the REAL dispatcher (``AppContext.comms``), so the
    ``brief_get`` default under test is production's own resolution, not a
    fixture's restatement of it.
    """

    _DECOY_PROJECT_BODY = "PROJECT LAW — the brief a bare brief_get resolves to"
    _TEACH_PATTERN = re.compile(
        r"catch up: lore_comms action=brief_get(?: name='(?P<name>[^']*)')?"
    )

    @classmethod
    def _catch_up_kwargs(cls, rendered: str) -> dict[str, Any]:
        """The kwargs an agent that follows the served catch-up line VERBATIM
        would pass to ``brief_get`` — ``{}`` when the line teaches a BARE call
        (today's build), ``{"name": X}`` when it names a brief. Parsed out of
        the render rather than hand-written, so the pin below exercises the
        line AS SERVED and cannot drift from it. The bare case really OMITS the
        kwarg (never ``name=None``), so the default resolution under test is
        production's own, reached exactly as an obedient reader would reach it."""
        match = cls._TEACH_PATTERN.search(rendered)
        assert match, f"no catch-up teach found in the behind-ack render: {rendered!r}"
        taught_name = match.group("name")
        return {} if taught_name is None else {"name": taught_name}

    async def _publish(self, harness: Any, *, name: str, body: str) -> None:
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name=name, body=body
        )

    async def _behind_ack(self, harness: Any, *, name: str) -> str:
        """Fixture arc: 'fixer-b' registers FIRST (§1 bootstrap — no briefs yet, so
        no register-time auto-ack edge; registering after a 'project' head would
        hand it a v1 ack and turn the ack below into the idempotent variant), a
        'project' brief EXISTS (so a bare ``brief_get`` resolves to something and
        the defect fails SILENTLY rather than raising), ``name`` is published to
        v2, and 'fixer-b' acks v1 of it — legitimately behind."""
        await _register(harness, name="lead", session="wave7", role="lead")
        await _register(harness, name="fixer-b", session="wave7")
        await self._publish(harness, name="project", body=self._DECOY_PROJECT_BODY)
        if name != "project":
            await self._publish(harness, name=name, body="v1 — the wave law")
        await self._publish(harness, name=name, body="v2 — the wave law, amended")
        return str(
            await AppContext.comms(
                harness, action="brief_ack", agent="fixer-b", session="wave7", name=name, version=1
            )
        )

    @pytest.mark.parametrize("brief_name", ["wave9", "base", "project"])
    async def test_the_catch_up_teach_names_the_brief_the_line_is_about(
        self, brief_name: str
    ) -> None:
        """THE KILLER PIN. A behind-ack under three names — two of them NOT
        'project' (the monoculture that hid this) — must teach a ``brief_get``
        that names the brief the reader is behind ON. Today's bare teach goes
        RED on 'wave9' and 'base'; the 'project' leg is the v8 uniformity ruling
        (the teach is explicit there too — do NOT special-case it away)."""
        harness = _harness()
        rendered = await self._behind_ack(harness, name=brief_name)
        assert "head is v2" in rendered, (
            f"fixture check: 'fixer-b' must really be behind on {brief_name!r} here: {rendered!r}"
        )
        assert f"catch up: lore_comms action=brief_get name='{brief_name}'" in rendered, (
            f"the behind-ack teach must name the brief it is ABOUT: brief_get's `name` "
            f"DEFAULTS to 'project', so a bare `brief_get` under a {brief_name!r} line sends "
            f"the reader to the WRONG brief (design doc v8 §9.5): {rendered!r}"
        )

    @pytest.mark.parametrize("brief_name", ["wave9", "base"])
    async def test_following_the_taught_command_verbatim_serves_the_acked_brief(
        self, brief_name: str
    ) -> None:
        """THE LITMUS, EXECUTED. Parse the taught call out of the served line and
        actually RUN it through the same dispatcher, exactly as an agent obeying
        the instruction would — with the defaults it teaches. The brief that comes
        back must be the one the ack line was about.

        On today's build the taught call is bare, resolves to 'project', and
        serves the DECOY project brief: no error, no signal, wrong law read. This
        is the mechanism-promise litmus in its strongest form — it grades what the
        instruction DOES, not how it is worded, and survives any rewording the
        builder chooses."""
        harness = _harness()
        rendered = await self._behind_ack(harness, name=brief_name)
        followed = str(
            await AppContext.comms(
                harness,
                action="brief_get",
                agent="fixer-b",
                session="wave7",
                **self._catch_up_kwargs(rendered),
            )
        )
        assert f"brief '{brief_name}' v2" in followed, (
            f"an agent that FOLLOWED the served catch-up line got a different brief than the "
            f"one it was told to catch up on. taught: {rendered!r} -> served: {followed!r}"
        )
        assert self._DECOY_PROJECT_BODY not in followed, (
            f"the taught command silently served the PROJECT brief — brief_get's default "
            f"name — instead of {brief_name!r}: {followed!r}"
        )

    async def test_the_behind_ack_line_is_byte_exact_under_a_non_project_name(self) -> None:
        """The de-monoculture sibling of ``TestBriefAckAction``'s byte-exact
        project pin (design doc v8's standing rule: every brief-grammar battery
        carries ≥1 non-'project' fixture — the ``_brief()`` factory's
        ``name='project'`` default is precisely why instances 8, 9 and 10 were
        invisible). Pins §9.5's grammar whole, not just the teach fragment."""
        harness = _harness()
        rendered = await self._behind_ack(harness, name="wave9")
        assert rendered == (
            "acked brief 'wave9' v1 — head is v2; catch up: "
            "lore_comms action=brief_get name='wave9'"
        )

    async def test_the_head_ack_and_reack_variants_are_unchanged_under_a_non_project_name(
        self,
    ) -> None:
        """The scope fence: v8 changes the BEHIND-ack teach and nothing else.
        The head-ack and idempotent-reack variants promise no mechanism (§9.7
        carries no row for them) and must stay byte-identical — a builder that
        bolts ``name=`` onto every variant, or reworks the grammar wholesale,
        goes RED here. Also the first non-'project' fixture these two variants
        have ever had."""
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await _register(harness, name="fixer-b", session="wave7")
        await self._publish(harness, name="wave9", body="v1 — the wave law")
        first = str(
            await AppContext.comms(
                harness, action="brief_ack", agent="fixer-b", session="wave7", name="wave9", version=1
            )
        )
        second = str(
            await AppContext.comms(
                harness, action="brief_ack", agent="fixer-b", session="wave7", name="wave9", version=1
            )
        )
        assert first == "acked brief 'wave9' v1 (head)"
        assert second == "already acked brief 'wave9' v1 — no new edge"


class TestFleetAction:
    async def test_lists_registered_agents(self) -> None:
        harness = _harness()
        await _register(harness, name="fixer-b")
        await _register(harness, name="scout-c")
        rendered = str(await AppContext.comms(harness, action="fleet", agent="fixer-b", session="wave7"))
        assert "fixer-b" in rendered
        assert "scout-c" in rendered
        assert "2 non-retired agents" in rendered

    async def test_the_publishers_own_fleet_row_renders_current(self) -> None:
        """§9.6's v7 consequence (finding #98): "author's row renders current".
        Today the publisher's own row reads ``project unbriefed`` — the fleet, the
        surface a lead scans to see who is behind, accuses the author of not
        having read its own brief.
        """
        harness = _harness()
        await _register(harness, name="lead", session="wave7", role="lead")
        await _register(harness, name="fixer-b", session="wave7")  # bootstrap: no brief yet
        await AppContext.comms(
            harness, action="brief_publish", agent="lead", session="wave7", name="project", body="v1"
        )
        rendered = str(await AppContext.comms(harness, action="fleet", agent="lead", session="wave7"))
        lead_row = next(line for line in rendered.splitlines() if line.startswith("- lead ["))
        fixer_row = next(line for line in rendered.splitlines() if line.startswith("- fixer-b ["))
        assert "project v1" in lead_row
        assert "unbriefed" not in lead_row
        assert "project unbriefed" in fixer_row, "the genuinely-unbriefed agent still says so"


class TestFleetActionBriefCellRendering:
    """finding #94 (REPORT-c1b-contract-9495.md): a CORRECTNESS regression
    guard for the upcoming grouped-join rewrite of the fleet action's
    per-row acked-version lookup (today's per-row ``acked_version()`` loop
    is already correct, just slow -- these assertions are GREEN today and
    must STAY green after the fix). Pinned through the RENDERED fleet
    output -- what an agent actually reads -- not the ledger method in
    isolation (test_brief_ledger.py's ``TestAckedVersionsForIds`` pins that
    separately): an unbriefed agent must still render ``project unbriefed``
    and MUST NOT vanish from the listing; an agent behind head renders
    ``project vX (head vY)``; an agent at head renders ``project vY``; an agent
    acked at MULTIPLE versions (out of order) resolves to the MAX.
    """

    async def test_unbriefed_behind_at_head_and_out_of_order_multi_ack_all_render_correctly(
        self,
    ) -> None:
        brief_ledger = FakeBriefLedger(db=FakeBriefDatabase())
        harness = _harness(brief_ledger=brief_ledger)

        # All four bootstrap BEFORE any 'project' brief exists -- register's
        # own auto-ack-on-existing-brief side effect (TestRegisterAction)
        # deliberately never fires here, so every ack below is explicit and
        # under this test's control.
        await _register(harness, name="ghost", session="wave7")
        await _register(harness, name="behind", session="wave7")
        await _register(harness, name="athead", session="wave7")
        await _register(harness, name="multiack", session="wave7")

        await brief_ledger.publish("project", "v1 body", created_by="lead")
        await AppContext.comms(
            harness, action="brief_ack", agent="behind", session="wave7", name="project", version=1
        )
        await AppContext.comms(
            harness, action="brief_ack", agent="multiack", session="wave7", name="project", version=1
        )
        await brief_ledger.publish("project", "v2 body", created_by="lead")  # head now v2
        await AppContext.comms(
            harness, action="brief_ack", agent="athead", session="wave7", name="project", version=2
        )
        # multiack acks v2 AFTER already having acked v1 -- out-of-order --
        # must resolve to the MAX (v2), not the first- or last-written edge.
        await AppContext.comms(
            harness, action="brief_ack", agent="multiack", session="wave7", name="project", version=2
        )

        rendered = str(
            await AppContext.comms(harness, action="fleet", agent="ghost", session="wave7", limit=10)
        )
        row_by_name = {
            line.split(" [")[0].removeprefix("- "): line
            for line in rendered.splitlines()
            if line.startswith("- ")
        }
        assert set(row_by_name) == {"ghost", "behind", "athead", "multiack"}, (
            "every registered agent must still be listed -- an unbriefed agent "
            f"must not vanish from the fleet: {rendered!r}"
        )
        assert "project unbriefed" in row_by_name["ghost"], row_by_name["ghost"]
        assert "project v1 (head v2)" in row_by_name["behind"], row_by_name["behind"]
        assert "project v2" in row_by_name["athead"] and "(head" not in row_by_name["athead"], (
            row_by_name["athead"]
        )
        assert "project v2" in row_by_name["multiack"] and "(head" not in row_by_name["multiack"], (
            f"multiack acked v1 then v2 out of order -- must resolve to the MAX "
            f"(v2), not the first/last-written edge: {row_by_name['multiack']!r}"
        )


class TestFleetActionQueryCountIsBounded:
    """finding #94, adversary BLOCKER (REPORT-c1-audit-adversary.md §P2): the
    prior contract pinned ``BriefLedger.acked_versions_for_ids`` in
    isolation, but NOTHING required the ``fleet`` ACTION to actually call
    it. The adversary shipped a perfect bulk method, left ``_comms_fleet``'s
    per-row loop untouched, and got the whole suite green -- finding #94
    would survive its own fix. This pins the ACTION itself.

    The counter wraps EVERY acked-status lookup the ledger exposes (today's
    per-row ``acked_version``, and ``acked_versions_for_ids`` a fix
    introduces) so the instrumentation stays valid across the exact rewrite
    finding #94 asks for -- it is not tied to one method name, and would
    equally catch a fix that calls the bulk method once per row (a
    different way to fail the same invariant).
    """

    @staticmethod
    def _install_call_counter(brief_ledger: FakeBriefLedger) -> list[int]:
        count = [0]
        original_acked_version = brief_ledger.acked_version

        async def _counting_acked_version(*, agent_id: str, name: str) -> int | None:
            count[0] += 1
            return await original_acked_version(agent_id=agent_id, name=name)

        brief_ledger.acked_version = _counting_acked_version  # type: ignore[method-assign]

        bulk_method = getattr(brief_ledger, "acked_versions_for_ids", None)
        if bulk_method is not None:

            async def _counting_bulk(agent_ids: Any, *, name: str) -> dict[str, int]:
                count[0] += 1
                return cast(dict[str, int], await bulk_method(agent_ids, name=name))

            brief_ledger.acked_versions_for_ids = _counting_bulk  # type: ignore[method-assign]

        return count

    async def _fleet_acked_lookup_count(self, *, agent_count: int, limit: int) -> int:
        """Register+ack ``agent_count`` agents at head, then call the
        ``fleet`` action at ``limit`` with the counter installed AFTER
        setup so only the ``fleet`` call itself is measured."""
        brief_ledger = FakeBriefLedger(db=FakeBriefDatabase())
        harness = _harness(brief_ledger=brief_ledger, fleet_limit=limit)
        for index in range(agent_count):
            await _register(harness, name=f"agent-{index:03d}", session="wave7")
        await brief_ledger.publish("project", "v1 body", created_by="lead")
        for index in range(agent_count):
            await AppContext.comms(
                harness,
                action="brief_ack",
                agent=f"agent-{index:03d}",
                session="wave7",
                name="project",
                version=1,
            )
        count = self._install_call_counter(brief_ledger)
        await AppContext.comms(
            harness, action="fleet", agent="agent-000", session="wave7", limit=limit
        )
        return count[0]

    async def test_lookup_count_does_not_grow_with_displayed_row_count(self) -> None:
        small_n_count = await self._fleet_acked_lookup_count(agent_count=5, limit=5)
        large_n_count = await self._fleet_acked_lookup_count(agent_count=50, limit=50)
        assert large_n_count == small_n_count, (
            f"the fleet action issued {small_n_count} acked-status lookups at "
            f"N=5 but {large_n_count} at N=50 -- expected a lookup count "
            f"independent of the number of DISPLAYED rows (one bulk call, "
            f"not one per row)"
        )

    async def test_lookup_count_does_not_grow_above_the_display_cap(self) -> None:
        """adversary P2 finding #4: the defect was MEASURED at limit=200
        (``_MAX_FLEET_LIMIT``) -- 407 round-trips at that exact scale. The
        sibling test above never crosses the cap; this fixture does."""
        above_cap_count = await self._fleet_acked_lookup_count(
            agent_count=_MAX_FLEET_LIMIT + 5, limit=_MAX_FLEET_LIMIT
        )
        small_n_count = await self._fleet_acked_lookup_count(agent_count=5, limit=5)
        assert above_cap_count == small_n_count, (
            f"the fleet action issued {small_n_count} acked-status lookups at "
            f"N=5 but {above_cap_count} at N={_MAX_FLEET_LIMIT + 5}/"
            f"limit={_MAX_FLEET_LIMIT} -- expected a lookup count independent "
            f"of scale, even above the display cap"
        )


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
        self.publish_agent_ids: list[str | None] = []

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
        self,
        name: str,
        body: str,
        *,
        created_by: str,
        note: str | None = None,
        agent_id: str | None = None,
    ) -> BriefPublishResult:
        """v7 (#98): records the ``agent_id`` the handler passes — the self-ack
        endpoint. ``None`` here would mean the dispatcher never handed the
        ledger an author to ack, so the pin below is a REAL check, not a
        signature-compat shim."""
        del name, body, created_by, note
        self.publish_agent_ids.append(agent_id)
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
        assert f"{_TRUE_NON_RETIRED_TOTAL} non-retired agents" in rendered  # v7 label (#99)
        assert f"{_TRUE_PARKED} input_required" in rendered
        assert f"{_TRUE_ACTIVE} active" in rendered
        assert f"{_TRUE_IDLE} idle" in rendered  # the true 45 -- NOT the window's capped 40
        remainder = _TRUE_NON_RETIRED_TOTAL - _MAX_FLEET_LIMIT
        assert f"+{remainder} more beyond the display cap ({_MAX_FLEET_LIMIT})" in rendered
        assert "re-run with limit=200" not in rendered  # the dead-end re-ask this variant replaces
        assert f"+{_TRUE_RETIRED} retired" in rendered


class TestFleetHandlerOnAnAllRetiredScope:
    """v7 (finding #99): the HANDLER must carry an all-retired scope through to
    the render as a zeroed header + a true trailer — it must not short-circuit
    on an empty row window, and it must not let the render's empty branch fire.

    Driven at the HANDLER (``_comms_fleet``), not through ``comms()``: the
    dispatcher resolves the CALLER inside the scope it is given, so an
    all-retired scope is unreachable through the tool in C1 (the caller would
    have to be a non-retired member of it, which is a contradiction, or a
    retired one, which raises ``RetiredAgentError``). FLAGGED in the report:
    that makes the all-retired render latent-but-unreachable today, exactly the
    way §9.4's zero-behind omission was before #98 — and it becomes reachable
    the moment C2 adds an ``include_retired``/foreign-scope re-ask. The fix is
    still load-bearing (the lie is in the served render path), and this pin is
    the strongest instrument that can reach it.
    """

    async def test_a_scope_whose_agents_are_all_retired_renders_the_zeroed_header(self) -> None:
        registry = FakeAgentRegistry(db=FakeAgentDatabase())
        harness = _harness(agent_registry=registry)
        await _register(harness, name="lead", session="wave7", role="lead")  # the live caller
        await _register(harness, name="ghost-a", session="wave8")
        await _register(harness, name="ghost-b", session="wave8")
        for ghost in ("ghost-a", "ghost-b"):
            await registry.touch(ghost, session="wave8", status="retired")

        rendered = str(
            await AppContext._comms_fleet(
                cast(AppContext, harness),
                agent_row=_agent(name="lead", session="wave7", role="lead"),
                session="wave8",
                limit=None,
            )
        )
        assert "no agents registered" not in rendered, (
            "two agents ARE registered in wave8 — they are retired. The empty variant "
            "lies about a scope it can see the rows of (finding #99, self-caught instance)"
        )
        assert rendered.splitlines() == [
            "fleet (session wave8): 0 non-retired agents — 0 input_required, 0 active, 0 idle",
            "+2 retired",
        ]

    async def test_a_genuinely_rowless_scope_still_renders_the_empty_variant(self) -> None:
        """The other half of the same ruling, through the same handler: with NO
        rows of any status in scope, the empty variant is the honest render.
        """
        registry = FakeAgentRegistry(db=FakeAgentDatabase())
        harness = _harness(agent_registry=registry)
        await _register(harness, name="lead", session="wave7", role="lead")

        rendered = str(
            await AppContext._comms_fleet(
                cast(AppContext, harness),
                agent_row=_agent(name="lead", session="wave7", role="lead"),
                session="wave9",  # nobody ever registered here
                limit=None,
            )
        )
        assert rendered == "no agents registered (session wave9)"


class TestFleetLimitBounds:
    """v7 / finding #97 (design doc §6, §1.2): ``limit`` is ``ge=1`` at the tool
    boundary — BELOW 1 TEACHES (a ValueError naming the offending value and the
    valid range ``1..{_MAX_FLEET_LIMIT}``), ABOVE the cap CLAMPS (honest
    clamping; the §9.6 cap-disclosure elision line then discloses what the clamp
    withheld). Today ``limit=-1`` silently renders a partial fleet — the render
    slices ``ordered[:-1]`` and drops the last row with no notice at all, and
    ``limit=0`` renders a fleet with no rows in it.
    """

    @pytest.mark.parametrize("bad_limit", [0, -1, -200])
    async def test_a_limit_below_one_teaches_the_valid_range(self, bad_limit: int) -> None:
        harness = _harness()
        await _register(harness, name="fixer-b", session="wave7")
        with pytest.raises(ValueError) as exc_info:
            await AppContext.comms(
                harness, action="fleet", agent="fixer-b", session="wave7", limit=bad_limit
            )
        message = str(exc_info.value)
        assert "limit" in message
        assert str(bad_limit) in message, "a teaching error names the offending value (§7)"
        assert f"1..{_MAX_FLEET_LIMIT}" in message, (
            "the error must name the VALID RANGE — §7: no comms error is ever a bare "
            "'invalid input'; each names the offending value, the legal domain, and the next move"
        )

    @pytest.mark.parametrize("bad_limit", [0, -1])
    async def test_a_rejected_limit_never_touches_the_callers_row(self, bad_limit: int) -> None:
        """Contract-adversary §2: the bound is a caller/SHAPE error, so it must
        fire in the DISPATCHER — BEFORE the uniform heartbeat touch (§8 step 4),
        not inside the fleet handler.

        A build that validates in the handler passes every other limit pin
        (554/554) while a REJECTED call has already mutated the store: the
        caller's ``heartbeat_at`` is stamped and an idle agent is auto-flipped to
        active. A rejected call must be a NO-OP on the fleet's own state — an
        agent whose status silently changed because it typo'd a limit is the
        quietest kind of wrong.

        The caller is parked ``idle`` precisely so the touch would be VISIBLE:
        the auto-flip (§3) is the loudest side effect available at this seam.
        """
        registry = FakeAgentRegistry(db=FakeAgentDatabase())
        harness = _harness(agent_registry=registry)
        await _register(harness, name="fixer-b", session="wave7")
        await registry.touch("fixer-b", session="wave7", status="idle")
        before = await registry.get_agent("fixer-b", session="wave7")

        with pytest.raises(ValueError):
            await AppContext.comms(
                harness, action="fleet", agent="fixer-b", session="wave7", limit=bad_limit
            )

        after = await registry.get_agent("fixer-b", session="wave7")
        assert after.status == "idle", (
            "a REJECTED fleet call must not auto-flip the caller idle->active — the bound "
            "is a shape error and belongs ahead of the uniform heartbeat touch (§8 step 4)"
        )
        assert after.heartbeat_at == before.heartbeat_at, (
            "a REJECTED fleet call must not stamp the caller's heartbeat_at"
        )

    async def test_limit_one_is_legal_and_shows_exactly_one_row(self) -> None:
        """The ge=1 BOUNDARY from the legal side: 1 is valid (an off-by-one
        guard rejecting it would be caught here, not in production)."""
        harness = _harness()
        await _register(harness, name="fixer-b", session="wave7")
        await _register(harness, name="fixer-c", session="wave7")
        rendered = str(
            await AppContext.comms(
                harness, action="fleet", agent="fixer-b", session="wave7", limit=1
            )
        )
        rows = [line for line in rendered.splitlines() if line.startswith("- ")]
        assert len(rows) == 1
        assert "+1 more — re-run with limit=2" in rendered

    async def test_a_limit_above_the_cap_clamps_and_discloses_instead_of_raising(self) -> None:
        """Above the cap is NOT an error (§1.2 honest clamping): the rows are
        capped at ``_MAX_FLEET_LIMIT`` and the cap-disclosure line tells the
        caller what the clamp withheld. A build that raised here — or that
        honoured the oversized limit and rendered 205 rows — fails.
        """
        registry = FakeAgentRegistry(db=FakeAgentDatabase())
        harness = _harness(agent_registry=registry)
        total = _MAX_FLEET_LIMIT + 5
        for index in range(total):
            await _register(harness, name=f"agent-{index:03d}", session="wave7")
        rendered = str(
            await AppContext.comms(
                harness,
                action="fleet",
                agent="agent-000",
                session="wave7",
                limit=_MAX_FLEET_LIMIT + 50,
            )
        )
        rows = [line for line in rendered.splitlines() if line.startswith("- ")]
        assert len(rows) == _MAX_FLEET_LIMIT, "the display cap bounds the ROWS, whatever was asked for"
        assert rendered.splitlines()[0] == (
            f"fleet (session wave7): {total} non-retired agents — 0 input_required, "
            f"{total} active, 0 idle"
        ), "the header still counts the WHOLE scope (§5.3 counting law), not the clamped window"
        assert f"+5 more beyond the display cap ({_MAX_FLEET_LIMIT})" in rendered
        assert "re-run with limit" not in rendered, "a re-ask past the cap is a dead end (§9.6)"


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

    @pytest.mark.parametrize("brief_name", ["project", "wave7"])
    async def test_the_handler_hands_the_ledger_the_callers_row_id_to_self_ack(
        self, brief_name: str
    ) -> None:
        """v7 / finding #98, at the seam: the ledger writes the self-ack edge,
        but only the DISPATCHER knows who the author is. This pins the exact
        value crossing that seam — the acting agent's ``id``, not its name (the
        old ``created_by`` display override is gone), and never ``None`` (which
        would silently mean "no
        self-ack" and restore the phantom-straggler defect with every other test
        still green).

        Parametrised over the brief NAME (contract-adversary §1): the value that
        crosses the seam must not depend on it. A ``name == BRIEF_NAME_PROJECT``
        guard here passes the 'project' case and hands ``None`` for every other
        brief in the fleet.
        """
        caller = _agent(name="caller", session="wave7")
        registry_spy = _OverCapRosterSpyRegistry()
        ledger_spy = _CoverageSkewSpyBriefLedger(head_brief=_brief(name=brief_name, version=4))
        ctx = SimpleNamespace(
            agent_registry=registry_spy,
            brief_ledger=ledger_spy,
            config=SimpleNamespace(comms=SimpleNamespace(brief_body_warn_chars=4000)),
        )

        await AppContext._comms_brief_publish(
            cast(AppContext, ctx),
            agent_row=caller,
            session=None,
            name=brief_name,
            body="standing instructions",
            note=None,
        )

        assert ledger_spy.publish_agent_ids == [caller.id]


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
            _agent(), project_head_version=3, project_acked_version=3, subscribed_skew=[]
        )
        assert rendered.count("\n") == 0

    def test_no_project_brief_yet_is_silent_one_line(self) -> None:
        rendered = AppContext._render_comms_heartbeat(
            _agent(), project_head_version=None, project_acked_version=None, subscribed_skew=[]
        )
        assert rendered.count("\n") == 0

    def test_skew_is_two_lines(self) -> None:
        rendered = AppContext._render_comms_heartbeat(
            _agent(), project_head_version=5, project_acked_version=4, subscribed_skew=[]
        )
        assert rendered.count("\n") == 1
        assert "v5" in rendered and "v4" in rendered

    def test_unbriefed_with_head_is_two_lines(self) -> None:
        rendered = AppContext._render_comms_heartbeat(
            _agent(), project_head_version=5, project_acked_version=None, subscribed_skew=[]
        )
        assert rendered.count("\n") == 1
        assert "not acked" in rendered


class TestRenderCommsBriefGet:
    def test_full_coverage(self) -> None:
        coverage = BriefCoverage(name="project", head_version=5, total_agents=5, current_count=5, behind=[])
        rendered = AppContext._render_comms_brief_get(
            _brief(name="project", version=5, body="body text"), 7200, coverage, session=None
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
            _brief(name="project", version=5, body="body text"), 0, coverage, session=None
        )
        assert "1/3" in rendered
        assert "fixer-b (v4)" in rendered
        assert "scout-c (unbriefed)" in rendered

    def test_session_scoped_names_the_session(self) -> None:
        coverage = BriefCoverage(name="project", head_version=1, total_agents=1, current_count=1, behind=[])
        rendered = AppContext._render_comms_brief_get(
            _brief(name="project", version=1, body="b"), 0, coverage, session="wave7"
        )
        assert "wave7" in rendered


class TestRenderCommsBriefPublish:
    """v6 (finding #96): ``skew_count: int`` is replaced by ``behind:
    Sequence[BriefBehindEntry]`` — the render helper itself now owns the
    grouping/descending-sort/cap logic (§9.4), so it needs the raw entries,
    not a pre-collapsed count. Every test below calls the NEW signature —
    they are EXPECTED RED against today's shipped code (``TypeError:
    _render_comms_brief_publish() got an unexpected keyword argument
    'behind'``) until the builder lands the signature change; that is the
    intended, disclosed RED, not an accidental break of a passing test."""

    def test_first_version(self) -> None:
        result = BriefPublishResult(brief=_brief(name="project", version=1), first_version=True)
        rendered = AppContext._render_comms_brief_publish(
            result, behind=[], body_chars=10, warn_threshold_chars=4000,
            session=None, auto_ack_at_register=True,
        )
        assert "first version" in rendered
        assert "skew" not in rendered

    @pytest.mark.parametrize("brief_name", ["project", "wave9", "base"])
    def test_the_first_version_ack_clause_is_brief_name_AWARE(self, brief_name: str) -> None:
        """Render-unit twin of TestTheFirstVersionLineTeachesAnAckMechanismThat
        ACTUALLYEXISTS's killer pin (the eighth §5.3 instance), isolating the
        helper where the fix lands: the register-time auto-ack is hardcoded to
        BRIEF_NAME_PROJECT in ``_comms_register``, so only a 'project'
        first-version line may promise it. ``test_first_version`` above cannot
        see this — ``_brief()`` defaults to name='project', the one name for
        which today's unconditional clause happens to be true (the monoculture,
        in miniature)."""
        result = BriefPublishResult(brief=_brief(name=brief_name, version=1), first_version=True)
        rendered = AppContext._render_comms_brief_publish(
            result,
            behind=[],
            body_chars=10,
            warn_threshold_chars=4000,
            session=None,
            auto_ack_at_register=(brief_name == "project"),
        )
        assert "first version" in rendered
        assert ("agents ack at register" in rendered) == (brief_name == "project"), (
            f"only the 'project' brief is acked at register — a first-version line under "
            f"name={brief_name!r} may promise it IFF it is true: {rendered!r}"
        )
        if brief_name != "project":
            assert "agents ack with lore_comms action=brief_ack" in rendered

    def test_skew_line_renders_only_when_behind_is_nonempty(self) -> None:
        result = BriefPublishResult(brief=_brief(name="project", version=2), first_version=False)
        rendered = AppContext._render_comms_brief_publish(
            result,
            behind=[
                BriefBehindEntry(agent_name="a", acked_version=1),
                BriefBehindEntry(agent_name="b", acked_version=1),
                BriefBehindEntry(agent_name="c", acked_version=None),
            ],
            body_chars=10,
            warn_threshold_chars=4000,
            session=None,
            auto_ack_at_register=True,
        )
        assert (
            "skew: 3 non-retired agents behind head v2 — 2 at v1, 1 unbriefed; "
            "surfaces at their next heartbeat"
        ) in rendered
        assert "(session" not in rendered

    def test_session_scoped_names_the_session(self) -> None:
        """The scoping law's render-helper leg (spec §5.3/§9.4, v2 amendment)
        -- mirrors TestRenderCommsBriefGet.test_session_scoped_names_the_
        session, brief_publish's twin surface."""
        result = BriefPublishResult(brief=_brief(name="project", version=2), first_version=False)
        rendered = AppContext._render_comms_brief_publish(
            result,
            behind=[BriefBehindEntry(agent_name="a", acked_version=1)],
            body_chars=10,
            warn_threshold_chars=4000,
            session="wave7",
            auto_ack_at_register=True,
        )
        assert (
            "skew (session wave7): 1 non-retired agents behind head v2 — 1 at v1; "
            "surfaces at their next heartbeat"
        ) in rendered

    def test_first_publish_never_names_a_fabricated_v0(self) -> None:
        """Render-unit twin of TestBriefPublishAction.test_first_publish_
        never_fabricates_v0 (finding #96's killer pin), isolating the render
        function from the ledger/registry stack: a first-version publish
        result with never-acked agents must never name v0 -- old code
        computed prior = result.brief.version - 1 = 1 - 1 = 0."""
        result = BriefPublishResult(brief=_brief(name="project", version=1), first_version=True)
        rendered = AppContext._render_comms_brief_publish(
            result,
            behind=[
                BriefBehindEntry(agent_name="a", acked_version=None),
                BriefBehindEntry(agent_name="b", acked_version=None),
            ],
            body_chars=10,
            warn_threshold_chars=4000,
            session=None,
            auto_ack_at_register=True,
        )
        assert "v0" not in rendered
        assert (
            "skew: 2 non-retired agents behind head v1 — 2 unbriefed; "
            "surfaces at their next heartbeat"
        ) in rendered

    def test_groups_render_descending_regardless_of_input_order(self) -> None:
        """Hostile input: ``behind`` arrives in SCRAMBLED (non-descending)
        order -- the render helper must sort by stored version itself,
        never trust caller ordering (§9.4: 'stored-acked version groups,
        DESCENDING')."""
        result = BriefPublishResult(brief=_brief(name="project", version=5), first_version=False)
        rendered = AppContext._render_comms_brief_publish(
            result,
            behind=[
                BriefBehindEntry(agent_name="a", acked_version=1),
                BriefBehindEntry(agent_name="b", acked_version=3),
                BriefBehindEntry(agent_name="c", acked_version=2),
            ],
            body_chars=10,
            warn_threshold_chars=4000,
            session=None,
            auto_ack_at_register=True,
        )
        assert (
            "skew: 3 non-retired agents behind head v5 — 1 at v3, 1 at v2, 1 at v1; "
            "surfaces at their next heartbeat"
        ) in rendered

    def test_breakdown_cap_boundary_exact_cap_names_every_group(self) -> None:
        """Exactly ``_SKEW_BREAKDOWN_CAP`` distinct acked versions -- every
        group is named, no ``at older versions`` remainder appears."""
        from loremaster.server import _SKEW_BREAKDOWN_CAP

        cap = _SKEW_BREAKDOWN_CAP
        behind = [BriefBehindEntry(agent_name=f"agent-{v}", acked_version=v) for v in range(cap, 0, -1)]
        result = BriefPublishResult(brief=_brief(name="project", version=cap + 1), first_version=False)
        rendered = AppContext._render_comms_brief_publish(
            result, behind=behind, body_chars=10, warn_threshold_chars=4000,
            session=None, auto_ack_at_register=True,
        )
        expected_breakdown = ", ".join(f"1 at v{v}" for v in range(cap, 0, -1))
        assert (
            f"skew: {cap} non-retired agents behind head v{cap + 1} — {expected_breakdown}; "
            "surfaces at their next heartbeat"
        ) in rendered
        assert "at older versions" not in rendered
        assert _extract_skew_group_counts(rendered) == [1] * cap

    def test_breakdown_cap_boundary_cap_plus_one_collapses_the_remainder(self) -> None:
        """``_SKEW_BREAKDOWN_CAP + 1`` distinct acked versions -- exactly the
        cap's worth of named groups plus ONE counted remainder group naming
        NO version, and the groups still sum to the full behind total."""
        from loremaster.server import _SKEW_BREAKDOWN_CAP

        cap = _SKEW_BREAKDOWN_CAP
        behind = [
            BriefBehindEntry(agent_name=f"agent-{v}", acked_version=v) for v in range(cap + 1, 0, -1)
        ]
        result = BriefPublishResult(brief=_brief(name="project", version=cap + 2), first_version=False)
        rendered = AppContext._render_comms_brief_publish(
            result, behind=behind, body_chars=10, warn_threshold_chars=4000,
            session=None, auto_ack_at_register=True,
        )
        shown = ", ".join(f"1 at v{v}" for v in range(cap + 1, 1, -1))
        assert (
            f"skew: {cap + 1} non-retired agents behind head v{cap + 2} — {shown}, "
            "1 at older versions; surfaces at their next heartbeat"
        ) in rendered
        counts = _extract_skew_group_counts(rendered)
        assert sum(counts) == cap + 1
        assert counts[-1] == 1  # the remainder group, collapsed, names no version
        assert len(counts) == cap + 1  # cap named groups + 1 remainder group

    def test_remainder_group_counts_agents_not_versions(self) -> None:
        """BLOCKER (C1 adversary, finding #96 audit —
        REPORT-c1c-contract-adversary-96.md §P1/§MISSING PINS #1): the
        collapsed remainder group's count must be the number of AGENTS
        behind at older versions, not the number of DISTINCT VERSIONS in
        the tail. Both cap-boundary fixtures above (`..._exact_cap_...`,
        `..._cap_plus_one_...`) put exactly ONE agent at ONE version in
        the tail, so ``len(remainder_versions)`` and
        ``sum(agents_per_version)`` are indistinguishable there — a build
        that computes ``len()`` instead of ``sum()`` passes both of them
        (and the whole 489-test contract) while serving a line whose
        groups do not sum to their own claimed total. This fixture spreads
        the tail across MULTIPLE agents at MULTIPLE versions (2 agents at
        one older version, 3 at another — tail = 5 agents / 2 versions),
        forcing ``len() (== 2) != sum() (== 5)`` into the open."""
        from loremaster.server import _SKEW_BREAKDOWN_CAP

        cap = _SKEW_BREAKDOWN_CAP
        head_version = cap + 3
        # cap named groups, one agent each, at the cap highest versions
        # below head (head-1 .. head-cap).
        named_versions = list(range(head_version - 1, head_version - 1 - cap, -1))
        # two MORE, lower, versions collapse into the remainder -- 2 agents
        # at the higher of the two, 3 at the lower (tail = 5 agents).
        tail_versions = [head_version - 1 - cap, head_version - 2 - cap]
        tail_counts = [2, 3]

        behind: list[BriefBehindEntry] = [
            BriefBehindEntry(agent_name=f"agent-v{v}", acked_version=v) for v in named_versions
        ]
        for version, count in zip(tail_versions, tail_counts, strict=True):
            for i in range(count):
                behind.append(BriefBehindEntry(agent_name=f"agent-v{version}-{i}", acked_version=version))

        result = BriefPublishResult(brief=_brief(name="project", version=head_version), first_version=False)
        rendered = AppContext._render_comms_brief_publish(
            result, behind=behind, body_chars=10, warn_threshold_chars=4000,
            session=None, auto_ack_at_register=True,
        )

        tail_total = sum(tail_counts)
        expected_behind = cap + tail_total
        named_str = ", ".join(f"1 at v{v}" for v in named_versions)
        assert (
            f"skew: {expected_behind} non-retired agents behind head v{head_version} — "
            f"{named_str}, {tail_total} at older versions; surfaces at their next heartbeat"
        ) in rendered

        counts = _extract_skew_group_counts(rendered)
        assert counts[-1] == tail_total, (
            f"remainder group must count AGENTS ({tail_total}), not the number of "
            f"distinct VERSIONS in the tail ({len(tail_versions)}): got {counts!r}"
        )
        assert len(counts) == cap + 1  # cap named groups + 1 remainder group
        _assert_skew_group_counts_sum_to_behind(rendered, expected_behind=expected_behind)

    def test_skew_line_omitted_on_a_non_first_publish_with_zero_behind(self) -> None:
        """MEDIUM (C1 adversary, finding #96 audit — REPORT-c1c-contract-
        adversary-96.md §MISSING PINS #2): the omission branch
        (``behind == 0`` -> no skew line at all, never `skew: 0 ...`) was
        previously pinned by exactly ONE test in this class
        (``test_first_version``), which happens to combine
        ``first_version=True`` WITH ``behind=[]``. A mutant that gates the
        omission on ``result.first_version`` rather than on ``behind``
        being empty (e.g. "always render a skew line once this is not the
        first version") is invisible to that test — it never fires for a
        first-version call — while serving the ugly ``skew: 0 non-retired
        agents behind head v2 — ; surfaces at their next heartbeat`` (empty
        breakdown, dangling em-dash) on every non-first publish where
        nobody happens to be behind. This pin isolates the two conditions:
        ``first_version=False`` AND ``behind=[]``.

        DEVIATION from the adversary's proposed framing: its report names
        this pin "action-level" (publish scoped to a session with no
        registered agents). That fixture is NOT reachable through the live
        dispatch stack: design doc §0.3 makes ``session`` a single
        universal param that BOTH resolves the ACTING agent's own row
        (``uuid5(session, name)``, via ``AgentRegistry.touch``) AND scopes
        the coverage/skew roster (§5.3) — a publisher can only address a
        scope it is itself a live, non-retired member of, so the publisher
        always appears in "non-retired agents in scope" and (§5.3/§9.4) is
        always behind its own freshly-minted head. ``behind == 0`` is
        therefore reachable ONLY at the render layer — which is exactly
        where this pin lives. Flagged, not silently decided, per this
        module's report."""
        result = BriefPublishResult(brief=_brief(name="project", version=2), first_version=False)
        rendered = AppContext._render_comms_brief_publish(
            result, behind=[], body_chars=10, warn_threshold_chars=4000,
            session=None, auto_ack_at_register=True,
        )
        assert "skew" not in rendered

    def test_warn_line_only_past_threshold(self) -> None:
        result = BriefPublishResult(brief=_brief(name="project", version=1), first_version=True)
        under = AppContext._render_comms_brief_publish(
            result, behind=[], body_chars=100, warn_threshold_chars=4000,
            session=None, auto_ack_at_register=True,
        )
        over = AppContext._render_comms_brief_publish(
            result, behind=[], body_chars=5000, warn_threshold_chars=4000,
            session=None, auto_ack_at_register=True,
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

    @pytest.mark.parametrize("brief_name", ["project", "wave9"])
    def test_the_behind_ack_teach_is_name_EXPLICIT(self, brief_name: str) -> None:
        """The TENTH instance at the render helper (design doc v8 §9.5; the
        end-to-end mechanism litmus lives in
        ``TestTheBehindAckTeachNamesTheBriefItIsABOUT``). Both legs are
        load-bearing: 'wave9' proves the teach is name-AWARE (a bare
        ``brief_get`` resolves to 'project' and reads the wrong brief),
        'project' proves the v8 UNIFORMITY ruling (the explicit ``name=`` is
        rendered there too — a build that emits it only for non-'project'
        names, i.e. special-cases the class instead of killing it, goes RED
        here). This class's every other fixture is ``name='project'``: that
        monoculture is exactly what hid the defect."""
        result = BriefAckResult(
            name=brief_name, version=4, head_version=5, already_acked=False, via="explicit"
        )
        rendered = AppContext._render_comms_brief_ack(result)
        assert f"catch up: lore_comms action=brief_get name='{brief_name}'" in rendered
        assert rendered.count("\n") == 0

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
        assert "project" not in rendered

    def test_brief_cell_current(self) -> None:
        rendered = AppContext._render_comms_fleet_row(
            _agent(), project_head_version=5, acked_version=5, stale_after_s=600, heartbeat_age_s=1
        )
        assert "project v5" in rendered
        assert "head" not in rendered

    def test_brief_cell_behind(self) -> None:
        rendered = AppContext._render_comms_fleet_row(
            _agent(), project_head_version=5, acked_version=4, stale_after_s=600, heartbeat_age_s=1
        )
        assert "project v4 (head v5)" in rendered

    def test_brief_cell_unbriefed(self) -> None:
        rendered = AppContext._render_comms_fleet_row(
            _agent(), project_head_version=5, acked_version=None, stale_after_s=600, heartbeat_age_s=1
        )
        assert "project unbriefed" in rendered

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
        """v7 (finding #99): the header's ``{total}`` IS the NON-RETIRED
        partition and must now SAY so — ``{total} non-retired agents``, the
        sibling vocabulary §9.3/§9.4/§7 already use for exactly this set. The
        retired agents it excludes are disclosed separately by the ``+K
        retired`` trailer, so the retired row below is what makes the old label
        ('3 agents' would be true of the registry, '2 agents' is what it
        printed) a LIE about its own set rather than a harmless shorthand.

        Byte-exact on the whole line: a substring pin ('2 non-retired') would
        pass a build that mangled the rest of the grammar.
        """
        rows = [_agent(name="a", status="input_required"), _agent(name="b", status="active")]
        rendered = str(
            AppContext._render_comms_fleet(
                _fleet_window(rows, retired_count=1),
                session=None,
                limit=20,
                stale_after_s=600,
                project_head_version=None,
                acked_versions={},
                heartbeat_age_seconds={},
                status_counts=_status_counts(rows, retired_count=1),
            )
        )
        assert rendered.splitlines()[0] == (
            "fleet: 2 non-retired agents — 1 input_required, 1 active, 0 idle"
        )
        assert "+1 retired" in rendered

    def test_scoped_header_names_the_session_and_the_non_retired_set(self) -> None:
        """The scoped variant of the same grammar (v7/#99) — byte-exact. Both
        variants ship the label; a builder who fixed only the one its eye landed
        on is caught here.
        """
        rows = [
            _agent(name="a", session="wave7", status="active"),
            _agent(name="b", session="wave7", status="idle"),
        ]
        rendered = str(
            AppContext._render_comms_fleet(
                _fleet_window(rows),
                session="wave7",
                limit=20,
                stale_after_s=600,
                project_head_version=None,
                acked_versions={},
                heartbeat_age_seconds={},
                status_counts=_status_counts(rows),
            )
        )
        assert rendered.splitlines()[0] == (
            "fleet (session wave7): 2 non-retired agents — 0 input_required, 1 active, 1 idle"
        )

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
        """The empty variant fires ONLY on a registry with no rows of ANY status
        (v7-precise, §9.6). Byte-exact, and explicitly NOT the zeroed header —
        which is the all-retired render (below), a different fact.
        """
        rendered = str(
            AppContext._render_comms_fleet(
                _fleet_window([]),
                session=None,
                limit=20,
                stale_after_s=600,
                project_head_version=None,
                acked_versions={},
                heartbeat_age_seconds={},
                status_counts=_status_counts([]),
            )
        )
        assert rendered == "no agents registered"

    def test_empty_scoped_names_the_session(self) -> None:
        rendered = str(
            AppContext._render_comms_fleet(
                _fleet_window([]),
                session="wave7",
                limit=20,
                stale_after_s=600,
                project_head_version=None,
                acked_versions={},
                heartbeat_age_seconds={},
                status_counts=_status_counts([]),
            )
        )
        assert rendered == "no agents registered (session wave7)"

    def test_all_retired_is_not_empty_and_never_says_no_agents_registered(self) -> None:
        """v7 (finding #99's self-caught seventh instance): agents EXIST — they
        are all retired — so ``no agents registered`` is a confident-wrong
        render ("registered" they demonstrably are; the trailer they'd never see
        proves the code knows it). The honest render is the TRUE zeroed
        non-retired header + the true ``+K retired`` trailer.

        This is the pin that kills BOTH wrong builds: a build that keeps the
        old branch renders the lie; a build that deletes the empty branch
        outright renders '0 non-retired agents' for a genuinely EMPTY registry
        (caught by the two byte-exact empty pins above). Only the ruled
        semantics — empty iff NO rows of ANY status — passes all three.
        """
        rendered = str(
            AppContext._render_comms_fleet(
                _fleet_window([], retired_count=3),
                session=None,
                limit=20,
                stale_after_s=600,
                project_head_version=None,
                acked_versions={},
                heartbeat_age_seconds={},
                status_counts=_status_counts([], retired_count=3),
            )
        )
        assert "no agents registered" not in rendered
        assert rendered.splitlines() == [
            "fleet: 0 non-retired agents — 0 input_required, 0 active, 0 idle",
            "+3 retired",
        ]

    def test_all_retired_scoped_renders_the_zeroed_header_and_the_true_trailer(self) -> None:
        rendered = str(
            AppContext._render_comms_fleet(
                _fleet_window([], retired_count=2),
                session="wave7",
                limit=20,
                stale_after_s=600,
                project_head_version=None,
                acked_versions={},
                heartbeat_age_seconds={},
                status_counts=_status_counts([], retired_count=2),
            )
        )
        assert "no agents registered" not in rendered
        assert rendered.splitlines() == [
            "fleet (session wave7): 0 non-retired agents — 0 input_required, 0 active, 0 idle",
            "+2 retired",
        ]

    def test_all_retired_renders_no_rows_and_no_elision_line(self) -> None:
        """The zeroed header must not drag an elision line in behind it: there
        are no non-retired rows to elide, so ``+K more`` (whose k = total −
        shown = 0) must stay silent, and no ``- name [...]`` row may appear.
        """
        rendered = str(
            AppContext._render_comms_fleet(
                _fleet_window([], retired_count=5),
                session=None,
                limit=1,
                stale_after_s=600,
                project_head_version=None,
                acked_versions={},
                heartbeat_age_seconds={},
                status_counts=_status_counts([], retired_count=5),
            )
        )
        assert "more" not in rendered
        assert not [line for line in rendered.splitlines() if line.startswith("- ")]
        assert rendered.splitlines() == [
            "fleet: 0 non-retired agents — 0 input_required, 0 active, 0 idle",
            "+5 retired",
        ]

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
        assert f"{_TRUE_NON_RETIRED_TOTAL} non-retired agents" in rendered  # v7 label (#99)
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
        brief=_brief(name="project", created_by=value),
        brief_age_s=0,
    )


async def _render_heartbeat_name(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_heartbeat(
        _agent(name=value), project_head_version=None, project_acked_version=None, subscribed_skew=[]
    )


async def _render_brief_get_name(value: str, _ctx: Any) -> str:
    coverage = BriefCoverage(name=value, head_version=1, total_agents=1, current_count=1, behind=[])
    return AppContext._render_comms_brief_get(_brief(name=value), 0, coverage, session=None)


async def _render_brief_get_author(value: str, _ctx: Any) -> str:
    coverage = BriefCoverage(name="project", head_version=1, total_agents=1, current_count=1, behind=[])
    return AppContext._render_comms_brief_get(
        _brief(name="project", created_by=value), 0, coverage, session=None
    )


async def _render_brief_get_behind_names(value: str, _ctx: Any) -> str:
    coverage = BriefCoverage(
        name="project",
        head_version=2,
        total_agents=2,
        current_count=1,
        behind=[BriefBehindEntry(agent_name=value, acked_version=1)],
    )
    return AppContext._render_comms_brief_get(_brief(name="project", version=2), 0, coverage, session=None)


async def _render_brief_publish_name(value: str, _ctx: Any) -> str:
    result = BriefPublishResult(brief=_brief(name=value), first_version=True)
    return AppContext._render_comms_brief_publish(
        result, behind=[], body_chars=1, warn_threshold_chars=4000, session=None, auto_ack_at_register=True
    )


async def _render_brief_publish_publisher(value: str, _ctx: Any) -> str:
    result = BriefPublishResult(brief=_brief(name="project", created_by=value), first_version=True)
    return AppContext._render_comms_brief_publish(
        result, behind=[], body_chars=1, warn_threshold_chars=4000, session=None, auto_ack_at_register=True
    )


async def _render_brief_publish_session(value: str, _ctx: Any) -> str:
    """LOW (C1 adversary, finding #96 audit — REPORT-c1c-contract-
    adversary-96.md §MISSING PINS #3): the skew line's ``{session}`` is
    the ONLY agent-controlled free text the v6 grammar renders, and the
    §10 inventory previously carried no ``brief_publish.session`` case --
    both existing brief_publish cases pass ``behind=[]``, so the skew line
    (and its ``{session}`` slot) never rendered under the hostile battery
    at all. ``behind`` is non-empty here so the scoped skew line actually
    renders and the battery reaches the field."""
    result = BriefPublishResult(brief=_brief(name="project", version=2), first_version=False)
    return AppContext._render_comms_brief_publish(
        result,
        behind=[BriefBehindEntry(agent_name="a", acked_version=1)],
        body_chars=1,
        warn_threshold_chars=4000,
        session=value,
        auto_ack_at_register=True,
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


# --------------------------------------------------------------------------- #
# packet 03 — send / drain / ack render fixtures.
#
# HOSTILE-FIXTURE LAW: a message body is STORED FREE TEXT written by another
# agent, so every one of these is driven with the full threat-char corpus plus
# the row-forge payload by ``TestC1RenderInjectionBattery`` below. A drain row
# is a SINGLE line (the design's numbered ``#seq [grade] sender->you: body``
# form), so the body is sanitised into it rather than fenced — which is exactly
# why the injection battery, not the fence-integrity class, is its oracle.
# --------------------------------------------------------------------------- #


def _message(
    *,
    question: bool,
    seq: int = 1,
    grade: str = "signal",
    body: str = "the body",
    sender_name: str = "lead",
    session: str = "wave7",
    thread: str | None = None,
    task_id: str | None = None,
    refs: list[str] | None = None,
) -> Any:
    """A ``Message`` for the send-render fixtures.

    ``question`` carries NO DEFAULT ON PURPOSE (packet 03b). The 03b send render
    BRANCHES on it — S4.1's question-teach line is emitted IFF ``message.question``
    — and repo law is explicit that a fixture factory must not default a parameter
    the code branches on: ``_brief()`` defaulting to ``name='project'``
    MANUFACTURED the #104 blind spot, where every render fixture silently tested
    the one value for which the served prose was true. No default ⇒ every call
    site chooses ⇒ the monoculture cannot re-form silently on this field."""
    return _msg().Message(
        id=f"{seq:026x}",
        seq=seq,
        session=session,
        thread=thread if thread is not None else session,
        sender_id="lead-id-0000",
        sender_name=sender_name,
        grade=cast(Any, grade),
        body=body,
        refs=refs if refs is not None else [],
        task_id=task_id,
        question=question,
        created_at=datetime.now(UTC),
    )


def _inbox_entry(
    *,
    seq: int = 1,
    grade: str = "signal",
    body: str = "the body",
    sender_name: str = "lead",
    thread: str,
    task_id: str | None = None,
    refs: list[str] | None = None,
    acked_at: datetime | None = None,
) -> Any:
    """An ``InboxEntry`` for the drain-render drivers.

    AUTHORIZED AMENDMENT 10 / D10 (operator 2026-07-24): ``thread`` carries NO
    DEFAULT. S4.2's branch 3 (D2 → reading A) makes the drain render BRANCH on
    ``thread != session``, which brings this field under the same law that removed
    ``acked_at``'s default from this factory's sibling ``_p03_entry`` (amendment 8,
    where a defaulted branch-comparand WAS R3's root cause).

    Two things this docstring must say, because both were argued and both decided
    the shape:

    * **"Today's pins already discriminate" is a DATED RECEIPT, not a standing
      property.** The exposure of a defaulted comparand is definitionally to the
      NEXT pin — written on the one day nobody re-runs the coverage analysis. This
      packet's own S1 exists because an untested coverage premise hands a hole an
      alibi; a fresh one was not ratified over a field this packet made
      branched-on.
    * **The comparison has TWO comparands, so half the law is none of it.** Closing
      only this factory leaves the generator alive one layer down: a pin routed
      through a session-defaulting DRIVER tests one branch exactly as silently as
      one routed through a thread-defaulting FACTORY. ``_render``'s ``session`` is
      required for the same reason and in the same wave.

    Every existing call site states ``thread="wave7"``; no rendered value moved."""
    return _msg().InboxEntry(
        seq=seq,
        message_id=f"{seq:026x}",
        grade=cast(Any, grade),
        sender_name=sender_name,
        thread=thread,
        task_id=task_id,
        body=body,
        refs=refs if refs is not None else [],
        created_at=datetime.now(UTC),
        acked_at=acked_at,
        ack_note=None,
    )


def _send_result(*, message: Any, recipient_names: list[str] | None = None) -> Any:
    """A ``MessageSendResult``. ``message`` is REQUIRED (03b): the old
    ``message=None -> _message()`` default would have to pick a ``question`` value
    on the caller's behalf, re-creating exactly the monoculture :func:`_message`'s
    docstring explains. ``recipient_names`` keeps its default — the send render
    does not BRANCH on a name, it interpolates it (the cap branch is driven
    explicitly, and derived from ``_COVERAGE_NAMES_CAP``, by the cap pins)."""
    names = recipient_names if recipient_names is not None else ["fixer-b"]
    return _msg().MessageSendResult(
        message=message,
        recipient_names=names,
        recipient_count=len(names),
    )


def _drain_result(
    *,
    entries: list[Any] | None = None,
    total_pending: int | None = None,
    directive_pending: int | None = None,
    peeked: bool = False,
) -> Any:
    rows = entries if entries is not None else [_inbox_entry(thread="wave7")]
    return _msg().MessageDrainResult(
        entries=rows,
        total_pending=total_pending if total_pending is not None else len(rows),
        directive_pending=directive_pending
        if directive_pending is not None
        else sum(1 for row in rows if row.grade == "directive"),
        stamped_seqs=[] if peeked else [row.seq for row in rows],
        peeked=peeked,
    )


def _ack_result(*, entries: list[Any] | None = None) -> Any:
    default = [_msg().MessageAckEntry(seq=1, outcome="acked", acked_at=datetime.now(UTC))]
    rows = entries if entries is not None else default
    return _msg().MessageAckResult(
        entries=rows,
        acked_count=sum(1 for row in rows if row.outcome == "acked"),
        already_acked_count=sum(1 for row in rows if row.outcome == "already_acked"),
    )


async def _render_send_recipients(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_send(
        _send_result(message=_message(question=False), recipient_names=[value]),
        broadcast=False,
        session="wave7",
    )


async def _render_send_sender(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_send(
        _send_result(message=_message(sender_name=value, question=False)),
        broadcast=False,
        session="wave7",
    )


async def _render_send_thread(value: str, _ctx: Any) -> str:
    """AUTHORIZED AMENDMENT R7 (operator 2026-07-24; design ruling S4.1).

    ``thread`` is CALLER-SUPPLIED free text and, before 03b, the send render never
    rendered it — so the committed battery carried only ``send.recipients`` /
    ``send.sender``. S4.1's question-teach line puts ``'{thread}'`` into the send
    render for the first time, which makes an injection case MANDATORY.

    ⚠ ``question=True`` IS THE WHOLE CASE. The question line is the ONLY place the
    send render emits ``thread``; with ``question=False`` this fixture renders a
    receipt that never contains the value and the case passes VACUOUSLY — testing
    nothing, exactly as ``brief_publish.session`` did with ``behind=[]`` until the
    #96 adversary caught it. ``TestSendThreadInjectionCaseIsNotVACUOUS`` below
    asserts the value really reaches the render, so this can never rot back into
    decoration."""
    return AppContext._render_comms_send(
        _send_result(message=_message(thread=value, question=True)),
        broadcast=False,
        session="wave7",
    )


async def _render_drain_body(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_drain(
        _drain_result(entries=[_inbox_entry(body=value, thread="wave7")]),
        session="wave7",
    )


async def _render_drain_sender(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_drain(
        _drain_result(entries=[_inbox_entry(sender_name=value, thread="wave7")]),
        session="wave7",
    )


async def _render_drain_task_id(value: str, _ctx: Any) -> str:
    """MINOR m2 (adversary). ``task_id`` is caller-controlled free text that enters
    the row's context cell (``(task {task_id})``) — the battery was per-ACTION and
    had no case for it. Defence-in-depth: the ``SafeLine`` seam makes an
    unsanitised build awkward, but the completeness pin cannot see the gap."""
    return AppContext._render_comms_drain(
        _drain_result(entries=[_inbox_entry(task_id=value, thread="wave7")]),
        session="wave7",
    )


async def _render_drain_refs(value: str, _ctx: Any) -> str:
    """MINOR m2 (adversary). ``refs`` are caller-controlled free text entering the
    row's refs variant (``({refs})``) — no committed injection case drove them."""
    return AppContext._render_comms_drain(
        _drain_result(entries=[_inbox_entry(refs=[value], thread="wave7")]),
        session="wave7",
    )


async def _render_drain_thread(value: str, _ctx: Any) -> str:
    """AUTHORIZED AMENDMENT 10 (operator 2026-07-24; design ruling D2 → reading A, S8).

    ⚠ THIS CASE SURVIVES READING A, AND THE REASON IS THE FIXTURE'S: the injected
    ``value`` is a HOSTILE string from ``_INJECTION_THREAT_CHARS``, never the
    session ``"wave7"``, so ``thread != session`` holds on every threat character
    and the context cell RENDERS — which is what keeps the sanitisation of
    ``thread`` under test. Were this driver ever re-pointed at a session-default
    thread, the cell would vanish and the case would pass VACUOUSLY, testing
    nothing (the ``brief_publish.session``/``behind=[]`` shape the #96 adversary
    caught). ``TestDrainThreadInjectionCaseIsNotVACUOUS`` asserts the value really
    reaches the render, so that cannot happen silently."""
    return AppContext._render_comms_drain(
        _drain_result(entries=[_inbox_entry(thread=value)]),
        session="wave7",
    )


async def _render_ack_agent_name(value: str, _ctx: Any) -> str:
    return AppContext._render_comms_ack(
        _ack_result(entries=[_msg().MessageAckEntry(seq=1, outcome="not_addressed", acked_at=None)]),
        agent_name=value,
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
    RenderCase("brief_publish.session", _render_brief_publish_session),
    RenderCase("brief_ack.name", _render_brief_ack_name),
    RenderCase("fleet.name", _render_fleet_name),
    RenderCase("fleet.role", _render_fleet_role),
    RenderCase("fleet.model", _render_fleet_model),
    RenderCase("fleet.task_id", _render_fleet_task_id),
    RenderCase("fleet.note", _render_fleet_note),
    RenderCase("fleet.session", _render_fleet_session),
    RenderCase("send.recipients", _render_send_recipients),
    RenderCase("send.sender", _render_send_sender),
    RenderCase("send.thread", _render_send_thread),  # R7 (03b) — see the driver's docstring
    RenderCase("drain.body", _render_drain_body),
    RenderCase("drain.sender", _render_drain_sender),
    RenderCase("drain.thread", _render_drain_thread),
    RenderCase("drain.task_id", _render_drain_task_id),  # m2 (03b) — see the driver's docstring
    RenderCase("drain.refs", _render_drain_refs),  # m2 (03b) — see the driver's docstring
    RenderCase("ack.name", _render_ack_agent_name),
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
            brief=_brief(name="project", body=self._HOSTILE_BODY),
            brief_age_s=0,
        )
        self._assert_fence_integrity(rendered, self._HOSTILE_BODY)

    def test_brief_get_body_round_trips_verbatim_inside_a_wider_fence(self) -> None:
        coverage = BriefCoverage(name="project", head_version=1, total_agents=1, current_count=1, behind=[])
        rendered = AppContext._render_comms_brief_get(
            _brief(name="project", body=self._HOSTILE_BODY), 0, coverage, session=None
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


# =========================================================================== #
# PACKET 03a — send / drain / ack at the DISPATCHER
#
# ⚠ PACKET LABEL (SPLIT, operator-ruled 2026-07-19): everything in this file
# and in test_comms_promise_registry.py is **packet 03a** (the surface; deploys
# both). The store + ledger groups are **packet 03** (test-only, no deploy) and
# live in test_comms_schema.py + test_message_ledger.py. The contract is
# deliberately kept WHOLE — one file per concern, run per packet by selector;
# see REPORT-contract-pkt03.md §UPDATE 5eb445b for the exact pytest invocations.
#
# The message LEDGER's own contract lives in ``test_message_ledger.py``. What
# is pinned HERE is everything the dispatcher owns and the ledger deliberately
# does not (the ``briefs.py:79-89`` decoupling: the ledger stays key-agnostic,
# the CALLER resolves the roster) — which is precisely where kickoff rulings 1
# and 7 live.
# =========================================================================== #


class TestNewActionSpecs:
    def test_send_params_and_required(self) -> None:
        spec = _COMMS_ACTIONS["send"]
        # ``set_status`` is IN (operator-ruled 2026-07-19, pulled in from the
        # design's tool table): a sender may park itself in the same call — the
        # one-call operator question. Per ruling 9 it does NOT store a waiting
        # state; it MARKS the message as the question the derivation reads.
        assert spec.params == frozenset(
            {"to", "body", "grade", "thread", "task_id", "refs", "set_status"}
        )
        assert spec.required == frozenset({"body", "grade"})
        assert spec.requires_registration is True

    def test_drain_params(self) -> None:
        spec = _COMMS_ACTIONS["drain"]
        assert spec.params == frozenset({"limit", "peek"})
        assert spec.required == frozenset()
        assert spec.requires_registration is True

    def test_ack_params_and_required(self) -> None:
        spec = _COMMS_ACTIONS["ack"]
        assert spec.params == frozenset({"seqs", "note"})
        assert spec.required == frozenset({"seqs"})
        assert spec.requires_registration is True

    def test_grade_is_REQUIRED_for_send(self) -> None:
        """A defaulted grade is a silent policy decision: every message would
        become a ``signal`` (never ack-tracked) or every one a ``directive``
        (ack-nagging on trivia). The design's own table lists it unqualified.
        """
        assert "grade" in _COMMS_ACTIONS["send"].required


class TestBroadcastFanOut:
    """RULING 1 (binding): ``to=[]`` / omitted ⇒ ALL NON-RETIRED agents
    (active + idle + input_required), never ``status == 'active'`` alone. An
    idle or parked agent silently missing a broadcast is message LOSS — the
    failure this subsystem exists to remove — and a parked agent MUST receive
    messages, since that is how its answer arrives.

    RULING 7: a broadcast does NOT deliver to its own sender.

    The fixture carries one agent of EVERY status plus a second SESSION, so it
    can discriminate all four wrong builds at once. A fixture of active agents
    only is decoration here.
    """

    @staticmethod
    def _fleet() -> tuple[Any, Any]:
        db = FakeAgentDatabase()
        registry = FakeAgentRegistry(db=db)
        message_ledger = _msg_fakes().FakeMessageLedger(db=_msg_fakes().FakeMessageDatabase())
        return _harness(agent_registry=registry, message_ledger=message_ledger), message_ledger

    @staticmethod
    async def _populate(harness: Any, message_ledger: Any) -> None:
        registry: FakeAgentRegistry = harness.agent_registry
        for name, session, status in (
            ("lead", "wave7", "active"),  # the SENDER
            ("fixer-b", "wave7", "active"),
            ("idle-c", "wave7", "idle"),
            ("parked-d", "wave7", "input_required"),
            ("retired-e", "wave7", "retired"),
            ("other-f", "wave9", "active"),  # the CROSS-SESSION control
        ):
            await registry.register(name, session=session, role="builder")
            if status != "active":
                await registry.touch(name, session=session, status=status)
            agent = await registry.get_agent(name, session=session)
            message_ledger.register_agent(agent_id=agent.id, name=agent.name)

    async def _broadcast_recipients(self) -> list[str]:
        harness, message_ledger = self._fleet()
        await self._populate(harness, message_ledger)
        await AppContext.comms(
            harness,
            action="send",
            agent="lead",
            session="wave7",
            body="all hands: the gate is red",
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
        )
        [message] = list(message_ledger.db.messages.values())
        return sorted(
            message_ledger.db.agents[agent_id]
            for (message_id, agent_id) in message_ledger.db.edges
            if message_id == message.id
        )

    async def test_broadcast_reaches_active_idle_and_parked(self) -> None:
        recipients = await self._broadcast_recipients()
        assert "fixer-b" in recipients
        assert "idle-c" in recipients, (
            "an IDLE agent missed a broadcast — a build fanning out over status=='active' "
            "alone loses exactly the traffic this subsystem exists to make durable (ruling 1)"
        )
        assert "parked-d" in recipients, (
            "an INPUT_REQUIRED agent missed a broadcast — a parked agent MUST receive "
            "messages, since that is how its answer arrives (ruling 1)"
        )

    async def test_broadcast_excludes_retired_agents(self) -> None:
        assert "retired-e" not in await self._broadcast_recipients()

    async def test_broadcast_never_crosses_sessions(self) -> None:
        assert "other-f" not in await self._broadcast_recipients()

    async def test_broadcast_does_not_deliver_to_its_own_sender(self) -> None:
        assert "lead" not in await self._broadcast_recipients(), (
            "ruling 7: a broadcast does not deliver to its own sender"
        )

    async def test_the_exact_broadcast_set(self) -> None:
        """The four assertions above, stated once as an EXACT set — an
        individually-passing build that ALSO delivers somewhere unexpected
        (say, to every session) fails here and only here.
        """
        assert await self._broadcast_recipients() == ["fixer-b", "idle-c", "parked-d"]

    async def test_broadcast_is_not_bounded_by_the_fleet_display_limit(self) -> None:
        """DISCRIMINATOR: ``AgentRegistry.fleet()`` is a display window (limited
        and status-ordered); ``roster()`` is the row-UNLIMITED membership. A
        build resolving the broadcast through ``fleet()`` silently drops every
        recipient past the limit — invisible at small N.
        """
        harness, message_ledger = self._fleet()
        registry: FakeAgentRegistry = harness.agent_registry
        names = ["lead"] + [f"agent-{index:02d}" for index in range(30)]
        for name in names:
            await registry.register(name, session="wave7", role="builder")
            agent = await registry.get_agent(name, session="wave7")
            message_ledger.register_agent(agent_id=agent.id, name=agent.name)
        await AppContext.comms(
            harness,
            action="send",
            agent="lead",
            session="wave7",
            body="all hands",
            grade=_msg().MESSAGE_GRADE_SIGNAL,
        )
        [message] = list(message_ledger.db.messages.values())
        delivered = {
            agent_id
            for (message_id, agent_id) in message_ledger.db.edges
            if message_id == message.id
        }
        assert len(delivered) == len(names) - 1, (
            f"broadcast reached {len(delivered)} of {len(names) - 1} non-sender agents — the "
            f"fan-out was bounded by a DISPLAY limit"
        )

    async def test_an_explicit_recipient_list_is_not_a_broadcast(self) -> None:
        """PARAMETER MONOCULTURE: every pin above omits ``to=``. A build that
        ignores ``to=`` entirely and always broadcasts passes all of them.
        """
        harness, message_ledger = self._fleet()
        await self._populate(harness, message_ledger)
        await AppContext.comms(
            harness,
            action="send",
            agent="lead",
            session="wave7",
            to=["fixer-b"],
            body="just for you",
            grade=_msg().MESSAGE_GRADE_SIGNAL,
        )
        [message] = list(message_ledger.db.messages.values())
        recipients = sorted(
            message_ledger.db.agents[agent_id]
            for (message_id, agent_id) in message_ledger.db.edges
            if message_id == message.id
        )
        assert recipients == ["fixer-b"]

    async def test_a_broadcast_with_no_other_agent_is_a_teaching_error(self) -> None:
        harness, message_ledger = self._fleet()
        registry: FakeAgentRegistry = harness.agent_registry
        await registry.register("lead", session="wave7", role="lead")
        agent = await registry.get_agent("lead", session="wave7")
        message_ledger.register_agent(agent_id=agent.id, name=agent.name)
        with pytest.raises(_msg().EmptyRecipientSetError):
            await AppContext.comms(
                harness,
                action="send",
                agent="lead",
                session="wave7",
                body="anybody out there",
                grade=_msg().MESSAGE_GRADE_SIGNAL,
            )

    async def test_a_broadcast_receipt_names_the_true_fan_out_and_the_session(self) -> None:
        """CRITICAL C4 (adversary W2b, W2c, W3). ``broadcast=True`` is a
        parameter-value MONOCULTURE: not one committed call site sets it, so the
        WHOLE broadcast receipt branch is untested (#96's law, on a boolean).

        Driven through the REAL dispatcher so it catches all three at once: a
        correct handler passes ``broadcast=True`` to the render, so W2b (count
        hardcoded 1) and W2c (session slot fed the message's thread) fire here,
        AND W3 (handler always passes ``broadcast=False``) fails because the named
        receipt has no ``broadcast:`` clause. The broadcast carries an EXPLICIT
        thread ``q:cap`` so it differs from the session — otherwise the default
        thread equals the session and W2c cannot be seen."""
        harness, message_ledger = self._fleet()
        await self._populate(harness, message_ledger)  # 3 non-sender recipients in wave7
        rendered = str(
            await AppContext.comms(
                harness,
                action="send",
                agent="lead",
                session="wave7",
                body="all hands",
                grade=_msg().MESSAGE_GRADE_SIGNAL,
                thread="q:cap",
            )
        )
        assert "broadcast: 3 agents in session wave7" in rendered, (
            "the broadcast receipt did not name the true fan-out (3) and the caller's SESSION "
            "(wave7) — W2b hardcodes the count to 1, W2c names the message's thread where the "
            f"session belongs, and W3 never renders the broadcast variant at all: {rendered!r}"
        )
        receipt = _drain_line_containing(rendered, "broadcast:")
        assert "q:cap" not in receipt, (
            f"the broadcast receipt named the thread 'q:cap' where the session belongs (W2c): {receipt!r}"
        )

    async def test_the_question_teach_survives_a_BROADCAST(self) -> None:
        """CRITICAL C5 (adversary W33). An agent that asks the WHOLE fleet still
        carries thread debt and must still be told how it clears. The question
        teach is emitted IFF ``message.question`` — orthogonal to broadcast — so a
        build gating it on ``not broadcast`` silently drops it for the one sender
        who most needs it."""
        harness, message_ledger = self._fleet()
        await self._populate(harness, message_ledger)
        rendered = str(
            await AppContext.comms(
                harness,
                action="send",
                agent="lead",
                session="wave7",
                body="does anyone know the cap?",
                grade=_msg().MESSAGE_GRADE_SIGNAL,
                thread="q:cap",
                set_status="input_required",
            )
        )
        assert "broadcast:" in rendered, (
            "POSITIVE CONTROL FAILED: this send was not a broadcast, so the assertion below "
            f"proves nothing about the broadcast branch: {rendered!r}"
        )
        assert "awaiting an answer on thread 'q:cap'" in rendered, (
            "a BROADCAST question dropped its clearing-rule teach — a build gating the question "
            f"line on 'not broadcast' fails exactly the sender who asked the fleet (W33): {rendered!r}"
        )

    async def test_a_broadcast_with_session_OMITTED_stays_in_the_callers_session(self) -> None:
        """CRITICAL C9 (adversary W32). ``session`` is optional on every non-register
        action and all 13 committed sends pass it — a value monoculture. Recipient
        resolution is scoped to ``agent_row.session`` (the caller's REGISTERED
        session), never the nullable ``session`` parameter; a build scoping the
        roster by the parameter delivers a broadcast into every session when the
        caller omits it."""
        harness, message_ledger = self._fleet()
        registry: FakeAgentRegistry = harness.agent_registry
        for name, session in (("lead", "wave7"), ("fixer-b", "wave7"), ("outsider", "wave9")):
            await registry.register(name, session=session, role="builder")
            agent = await registry.get_agent(name, session=session)
            message_ledger.register_agent(agent_id=agent.id, name=agent.name)
        await AppContext.comms(
            harness,
            action="send",
            agent="lead",
            body="all hands",  # NOTE: session= deliberately OMITTED
            grade=_msg().MESSAGE_GRADE_SIGNAL,
        )
        [message] = list(message_ledger.db.messages.values())
        recipients = sorted(
            message_ledger.db.agents[agent_id]
            for (message_id, agent_id) in message_ledger.db.edges
            if message_id == message.id
        )
        assert "outsider" not in recipients, (
            "a broadcast with session= OMITTED crossed into wave9 — the roster was scoped by the "
            f"nullable session parameter instead of the caller's registered session (W32): {recipients!r}"
        )
        assert recipients == ["fixer-b"], (
            f"the broadcast should reach exactly the caller's own session: {recipients!r}"
        )


class TestUnregisteredRecipientIsTheEXISTINGTeachingError:
    """RULING 2: packet 03 builds its own scoped ``unregistered recipient =
    teaching error`` and routes it through the EXISTING
    ``_comms_enrich_unknown_agent`` (``server.py:4527-4545``) rather than
    minting a second one. ONE IMPLEMENTATION — a second roster-enrichment
    helper is copy #2 of a policy.

    The fixture uses a recipient name that DOES NOT EXIST. A fixture where
    every recipient is registered cannot discriminate (probe consequence #1).
    """

    async def test_an_unknown_recipient_names_itself_and_the_live_roster(self) -> None:
        db = FakeAgentDatabase()
        registry = FakeAgentRegistry(db=db)
        message_ledger = _msg_fakes().FakeMessageLedger(db=_msg_fakes().FakeMessageDatabase())
        harness = _harness(agent_registry=registry, message_ledger=message_ledger)
        for name in ("lead", "fixer-b"):
            await registry.register(name, session="wave7", role="builder")
            agent = await registry.get_agent(name, session="wave7")
            message_ledger.register_agent(agent_id=agent.id, name=agent.name)
        with pytest.raises((UnknownAgentError, _msg().UnknownRecipientError)) as excinfo:
            await AppContext.comms(
                harness,
                action="send",
                agent="lead",
                session="wave7",
                to=["fixer-b", "typo-agent"],
                body="who are you",
                grade=_msg().MESSAGE_GRADE_SIGNAL,
            )
        text = str(excinfo.value)
        assert "typo-agent" in text, "the teaching error must NAME the unresolvable recipient"
        assert "fixer-b" in text, (
            "the teaching error must carry the capped/counted live roster the existing "
            "_comms_enrich_unknown_agent produces — a second, roster-less error is copy #2"
        )

    async def test_nothing_is_delivered_when_one_recipient_is_unknown(self) -> None:
        db = FakeAgentDatabase()
        registry = FakeAgentRegistry(db=db)
        message_ledger = _msg_fakes().FakeMessageLedger(db=_msg_fakes().FakeMessageDatabase())
        harness = _harness(agent_registry=registry, message_ledger=message_ledger)
        for name in ("lead", "fixer-b"):
            await registry.register(name, session="wave7", role="builder")
            agent = await registry.get_agent(name, session="wave7")
            message_ledger.register_agent(agent_id=agent.id, name=agent.name)
        with pytest.raises(Exception):  # noqa: B017 - either teaching error is acceptable here
            await AppContext.comms(
                harness,
                action="send",
                agent="lead",
                session="wave7",
                to=["fixer-b", "typo-agent"],
                body="who are you",
                grade=_msg().MESSAGE_GRADE_SIGNAL,
            )
        assert message_ledger.db.messages == {}, "a rejected send wrote a message row"
        assert message_ledger.db.edges == {}, "a rejected send wrote a delivery edge"


class TestDrainAndAckAtTheDispatcher:
    @staticmethod
    async def _ready() -> tuple[Any, Any]:
        db = FakeAgentDatabase()
        registry = FakeAgentRegistry(db=db)
        message_ledger = _msg_fakes().FakeMessageLedger(db=_msg_fakes().FakeMessageDatabase())
        harness = _harness(agent_registry=registry, message_ledger=message_ledger, drain_limit=5)
        for name in ("lead", "fixer-b"):
            await registry.register(name, session="wave7", role="builder")
            agent = await registry.get_agent(name, session="wave7")
            message_ledger.register_agent(agent_id=agent.id, name=agent.name)
        return harness, message_ledger

    async def test_drain_defaults_to_the_configured_limit_not_a_hardcoded_one(self) -> None:
        """The drain window is CONFIG (``comms.drain_limit``), like
        ``fleet_limit`` — never a literal buried in the handler. The harness
        sets 5; a build hardcoding 20 serves 8 rows here.
        """
        harness, message_ledger = await self._ready()
        for index in range(8):
            await AppContext.comms(
                harness,
                action="send",
                agent="lead",
                session="wave7",
                to=["fixer-b"],
                body=f"message {index}",
                grade=_msg().MESSAGE_GRADE_SIGNAL,
            )
        rendered = str(
            await AppContext.comms(harness, action="drain", agent="fixer-b", session="wave7")
        )
        assert rendered.count("#") >= 5
        remaining = sum(
            1 for edge in message_ledger.db.edges.values() if edge.seen_at is None
        )
        assert remaining == 3, (
            f"the default drain window was not the configured 5 (3 expected still unread, "
            f"got {remaining}) — {rendered!r}"
        )

    async def test_peek_is_a_real_boolean_param_the_dispatcher_forwards(self) -> None:
        harness, message_ledger = await self._ready()
        await AppContext.comms(
            harness,
            action="send",
            agent="lead",
            session="wave7",
            to=["fixer-b"],
            body="peek me",
            grade=_msg().MESSAGE_GRADE_SIGNAL,
        )
        await AppContext.comms(
            harness, action="drain", agent="fixer-b", session="wave7", peek=True
        )
        assert all(edge.seen_at is None for edge in message_ledger.db.edges.values()), (
            "peek=True stamped anyway — the dispatcher dropped the flag on the floor"
        )

    async def test_ack_forwards_the_seqs_list(self) -> None:
        harness, message_ledger = await self._ready()
        await AppContext.comms(
            harness,
            action="send",
            agent="lead",
            session="wave7",
            to=["fixer-b"],
            body="ack me",
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
        )
        [message] = list(message_ledger.db.messages.values())
        await AppContext.comms(
            harness, action="ack", agent="fixer-b", session="wave7", seqs=[message.seq]
        )
        assert all(edge.acked_at is not None for edge in message_ledger.db.edges.values())

    @pytest.mark.parametrize(
        ("action", "foreign"),
        [("send", {"peek": True}), ("drain", {"grade": "signal"}), ("ack", {"body": "x"})],
    )
    async def test_the_strict_param_law_covers_the_new_actions(
        self, action: str, foreign: dict[str, Any]
    ) -> None:
        harness, _ = await self._ready()
        with pytest.raises(ValueError, match="omit it for"):
            await AppContext.comms(
                harness, action=action, agent="fixer-b", session="wave7", **foreign
            )

    async def test_the_dispatcher_HANDS_THE_RENDER_A_SESSION_and_it_is_the_right_one(
        self,
    ) -> None:
        """AUTHORIZED AMENDMENT 10's WIRING leg (D2 -> reading A, S8).

        Every other amendment-10 pin calls ``_render_comms_drain`` DIRECTLY and
        hands it a session, so all of them stay green for a dispatcher that
        forgets to forward one or forwards the wrong thing — and the dispatcher is
        the only path production ever takes. That is this repo's #131 shape in
        miniature: the fixture guarantees the one condition (a session is present
        and correct) under which the wiring bug is invisible.

        Two messages, ONE drain: the first rides the SESSION-DEFAULT thread (the
        send omits ``thread``, which the ledger defaults to ``session`` — asserted
        below as a fixture check, because if that default ever changed this pin
        would silently stop testing branch 3), the second a deliberate thread. The
        row-level discrimination must survive the whole real call path.

        ⚠ KNOWN BOUND, stated so it is met deliberately: registration ties the
        caller to ``session="wave7"``, so a dispatcher forwarding a HARDCODED
        ``"wave7"`` (or ``agent_row.session``, which is equal here by
        construction) is indistinguishable at this seam. The literal-vs-argument
        discrimination is pinned one layer down, at the render, by
        ``TestRenderCommsDrainShape::
        test_the_SUPPRESSED_thread_is_the_SESSION_ARGUMENT_not_a_LITERAL``. The
        two together are what cover the property; neither does alone."""
        harness, message_ledger = await self._ready()
        await AppContext.comms(
            harness,
            action="send",
            agent="lead",
            session="wave7",
            to=["fixer-b"],
            body="on the default thread",
            grade=_msg().MESSAGE_GRADE_SIGNAL,
        )
        await AppContext.comms(
            harness,
            action="send",
            agent="lead",
            session="wave7",
            to=["fixer-b"],
            body="on a deliberate thread",
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            thread="q:cap",
        )
        stored = {message.body: message for message in message_ledger.db.messages.values()}
        assert stored["on the default thread"].thread == "wave7", (
            "fixture check: a send that omits `thread` must land on the SESSION thread — "
            "without that, the first row below is not on the default thread and this pin "
            f"tests branch 2 twice instead of discriminating: {stored['on the default thread']!r}"
        )

        rendered = str(
            await AppContext.comms(harness, action="drain", agent="fixer-b", session="wave7")
        )
        default_row = _drain_line_containing(rendered, "on the default thread")
        deliberate_row = _drain_line_containing(rendered, "on a deliberate thread")
        assert "(thread " not in default_row, (
            "through the REAL dispatcher, a row on the session-default thread drew a thread "
            "cell — either the dispatcher never forwarded the caller's session or it forwarded "
            f"a value that matches nothing: {default_row!r}"
        )
        assert "(thread q:cap)" in deliberate_row, (
            f"the deliberate-thread row lost its cell through the dispatcher: {deliberate_row!r}"
        )

    async def test_the_SEND_dispatcher_serves_the_SEND_RENDER(self) -> None:
        """BLOCKER B1 (adversary W1) — THE NO-OP FIX, send half.

        ``_render_comms_send`` can be built PERFECTLY and never called: a handler
        returning a hardcoded ``render_line("no unread messages")`` passes every
        render-shape pin in this file, because they all call the render DIRECTLY.
        The drain has ``test_the_dispatcher_HANDS_THE_RENDER_A_SESSION_and_it_is_
        the_right_one``; send had NO equivalent, and this is the #94 shape verbatim
        (repo CLAUDE.md: "every pin tested a new method NOTHING REQUIRED THE CODE
        TO CALL"). Only a pin that drives the REAL dispatcher and reads its output
        can see the wire; this is that pin.

        The send carries all three of S4.1's emitted lines at once — the receipt,
        the directive ack-trailer (grade=directive) and the question teach
        (set_status=input_required marks the message a question, ruling 9) — so the
        no-op build fails on every one of them, and a build that wires the render
        but drops the question/trailer forwarding fails on the specific line it
        dropped."""
        harness, _ = await self._ready()
        rendered = str(
            await AppContext.comms(
                harness,
                action="send",
                agent="lead",
                session="wave7",
                to=["fixer-b"],
                body="answer me",
                grade=_msg().MESSAGE_GRADE_DIRECTIVE,
                set_status="input_required",
                thread="q:cap",
            )
        )
        assert "sent #1 [directive] → fixer-b" in rendered, (
            "the send dispatcher did not serve _render_comms_send's RECEIPT line — a handler "
            f"that never calls the render (the no-op fix, W1) survives every other pin: {rendered!r}"
        )
        assert "recipients must ack: lore_comms action=ack seqs=[1]" in rendered, (
            f"the directive ack-trailer never reached the dispatcher output: {rendered!r}"
        )
        assert "awaiting an answer on thread 'q:cap'" in rendered, (
            "the question-teach line never reached the dispatcher output — either the render is "
            f"unwired (W1) or set_status did not mark the message a question: {rendered!r}"
        )

    async def test_the_ACK_dispatcher_serves_the_ACK_RENDER(self) -> None:
        """BLOCKER B2 (adversary W10) — THE NO-OP FIX, ack half.

        Same class as B1: ``_render_comms_ack`` can be built perfectly and never
        called. This drives the REAL ``action=ack`` dispatch and reads its output,
        so a handler returning a hardcoded string fails. En route it also exercises
        the counts (W11), the acked/already-acked distinction (W12) and the
        not-addressed IDENTITY at the dispatcher (W15b — the handler must hand the
        render the CALLER's name, not its session)."""
        harness, message_ledger = await self._ready()
        # A third agent so the not_addressed group is reachable through the real
        # dispatcher: it acks a seq addressed to fixer-b, so it holds no edge.
        registry: FakeAgentRegistry = harness.agent_registry
        await registry.register("idle-c", session="wave7", role="builder")
        idle_c = await registry.get_agent("idle-c", session="wave7")
        message_ledger.register_agent(agent_id=idle_c.id, name=idle_c.name)

        await AppContext.comms(
            harness,
            action="send",
            agent="lead",
            session="wave7",
            to=["fixer-b"],
            body="ack me",
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
        )
        [message] = list(message_ledger.db.messages.values())

        first = str(
            await AppContext.comms(
                harness, action="ack", agent="fixer-b", session="wave7", seqs=[message.seq]
            )
        )
        assert f"acked 1 of 1: #{message.seq}" in first, (
            "the ack dispatcher did not serve _render_comms_ack's acked line with the TRUE "
            f"counts — the render is unwired (W10) or the counts are wrong (W11): {first!r}"
        )

        second = str(
            await AppContext.comms(
                harness, action="ack", agent="fixer-b", session="wave7", seqs=[message.seq, 999]
            )
        )
        assert f"already acked: #{message.seq} — no new stamp" in second, (
            "a re-ack of an already-discharged seq was not reported as ALREADY ACKED — W12 folds "
            f"it into the acked group and re-reports a fresh stamp: {second!r}"
        )
        assert "acked 1 of" not in second, (
            f"a re-ack fabricated a fresh 'acked' line for a seq that was already stamped: {second!r}"
        )
        assert "unknown message seq(s): #999" in second, (
            f"the unknown-seq teach never reached the dispatcher output: {second!r}"
        )

        not_mine = str(
            await AppContext.comms(
                harness, action="ack", agent="idle-c", session="wave7", seqs=[message.seq]
            )
        )
        assert "not addressed to you" in not_mine and "to idle-c" in not_mine, (
            "the not-addressed line named something other than the CALLER — the handler passed "
            f"the render its session, not its name (W15b): {not_mine!r}"
        )

    async def test_send_forwards_set_status_task_id_and_refs(self) -> None:
        """CRITICAL C6 (adversary W28, W29). The send handler must forward the
        caller's ``set_status``, ``task_id`` and ``refs`` to the ledger.

        W29 is the sharper half: drop ``set_status`` and NO production message is
        ever a question, so S4.1's whole question-teach line — this packet's
        headline addition — is unreachable through the real path while its
        render-level 2×2 proof stays green (the P5 fake-mutation receipt is exact:
        breaking ``question`` in the fake reddens 16 tests, ALL in
        test_message_ledger.py, NONE in this surface). W28 drops ``task_id``/``refs``
        so the next drain row loses its task cell and its refs.
        """
        harness, message_ledger = await self._ready()
        send_render = str(
            await AppContext.comms(
                harness,
                action="send",
                agent="lead",
                session="wave7",
                to=["fixer-b"],
                body="the plan is ready",
                grade=_msg().MESSAGE_GRADE_SIGNAL,
                thread="q:cap",
                set_status="input_required",
                task_id="T-9",
                refs=["REPORT-x.md"],
            )
        )
        assert "awaiting an answer on thread 'q:cap'" in send_render, (
            "the send render carried no question line — set_status was dropped between the "
            "dispatcher and the ledger, so no message becomes a question through the real path "
            f"and the whole S4.1 question teach is dead code in production (W29): {send_render!r}"
        )
        drain_render = str(
            await AppContext.comms(harness, action="drain", agent="fixer-b", session="wave7")
        )
        row = _drain_line_containing(drain_render, "the plan is ready")
        assert "(task T-9)" in row, (
            f"the drained row lost its task anchor — task_id was dropped at the send (W28): {row!r}"
        )
        assert "REPORT-x.md" in row, (
            f"the drained row lost its refs — refs were dropped at the send (W28): {row!r}"
        )

    async def test_drain_honours_an_EXPLICIT_limit_at_the_dispatcher(self) -> None:
        """MAJOR M6 (adversary W9). ``limit`` is a declared ``drain`` param that no
        committed pin exercises with a value that DIFFERS from the served count.

        The harness config sets ``drain_limit=5``; three pending, ``limit=1`` must
        serve ONE and leave TWO unread. A build ignoring the caller's ``limit`` and
        always using config serves all three and leaves none."""
        harness, message_ledger = await self._ready()
        for index in range(3):
            await AppContext.comms(
                harness,
                action="send",
                agent="lead",
                session="wave7",
                to=["fixer-b"],
                body=f"message {index}",
                grade=_msg().MESSAGE_GRADE_SIGNAL,
            )
        rendered = str(
            await AppContext.comms(
                harness, action="drain", agent="fixer-b", session="wave7", limit=1
            )
        )
        assert rendered.count("→you") == 1, (
            f"an explicit limit=1 served more than one row — the caller's limit was ignored "
            f"and the config window used instead (W9): {rendered!r}"
        )
        unread = sum(1 for edge in message_ledger.db.edges.values() if edge.seen_at is None)
        assert unread == 2, (
            f"limit=1 left {unread} unread (expected 2) — the drain window was not the caller's "
            f"explicit limit (W9)"
        )

    async def test_ack_forwards_the_NOTE(self) -> None:
        """MAJOR M8 (adversary W27). ``note=`` is accepted and stored on the edge
        the CAS wins (S4.3: "recorded as deliberate, not forgotten"); storage is
        asserted nowhere at the surface. A build dropping the note at the
        dispatcher stores ``None`` and the deliberate record is silently lost."""
        harness, message_ledger = await self._ready()
        await AppContext.comms(
            harness,
            action="send",
            agent="lead",
            session="wave7",
            to=["fixer-b"],
            body="do the thing",
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
        )
        [message] = list(message_ledger.db.messages.values())
        await AppContext.comms(
            harness,
            action="ack",
            agent="fixer-b",
            session="wave7",
            seqs=[message.seq],
            note="done — see REPORT-x.md",
        )
        acked = [edge for edge in message_ledger.db.edges.values() if edge.acked_at is not None]
        assert len(acked) == 1, f"fixture check: exactly one edge should be acked: {acked!r}"
        assert acked[0].ack_note == "done — see REPORT-x.md", (
            "the ack note never reached the winning delivery edge — the dispatcher dropped it "
            f"on the floor (W27): {acked[0].ack_note!r}"
        )

    async def test_to_EMPTY_LIST_is_a_broadcast(self) -> None:
        """MAJOR M1 (adversary W31). The served instructions teach ``to=[]`` as the
        broadcast form (S5: "to=[] broadcasts to all non-retired"); ``to=[]``
        appears in the whole contract ONLY inside a docstring. A build spelling the
        broadcast test ``to is None`` treats an explicit empty list as "name every
        recipient", finds none, and raises ``EmptyRecipientSetError`` — refusing the
        exact call the instructions promise works."""
        harness, message_ledger = await self._ready()
        await AppContext.comms(
            harness,
            action="send",
            agent="lead",
            session="wave7",
            to=[],
            body="all hands",
            grade=_msg().MESSAGE_GRADE_SIGNAL,
        )
        [message] = list(message_ledger.db.messages.values())
        recipients = sorted(
            message_ledger.db.agents[agent_id]
            for (message_id, agent_id) in message_ledger.db.edges
            if message_id == message.id
        )
        assert recipients == ["fixer-b"], (
            "to=[] did not broadcast to the caller's session — a build treating [] as an "
            f"explicit (empty) recipient list refuses the send S5 teaches as broadcast (W31): "
            f"{recipients!r}"
        )

    async def test_an_oversize_body_is_a_teaching_reject_at_the_surface(self) -> None:
        harness, message_ledger = await self._ready()
        with pytest.raises(Exception) as excinfo:  # noqa: B017 - MessageBodyError surface
            await AppContext.comms(
                harness,
                action="send",
                agent="lead",
                session="wave7",
                to=["fixer-b"],
                body="z" * (_msg().MESSAGE_BODY_MAX_CHARS + 1),
                grade=_msg().MESSAGE_GRADE_SIGNAL,
            )
        assert "refs" in str(excinfo.value)
        assert message_ledger.db.messages == {}


# =========================================================================== #
# PACKET 03b — THE SERVED SHAPES (design rulings S4.1 / S4.2 / S5 in
# docs/plans/v2/03b-comms-surface-design-rulings.md, which are BINDING and
# VERBATIM: a builder must not improvise any of them).
#
# The committed 03a contract pinned the send/drain/ack renders only through (a)
# the promise-registry emit/no-emit proofs and (b) the hostile injection
# battery. Neither can see SHAPE: which cell wins, what number the re-ask
# carries, whether a peek nags. Those are this section's pins.
# =========================================================================== #


def _drain_line_containing(rendered: str, fragment: str) -> str:
    """The ONE rendered line containing ``fragment``, or a loud failure.

    Trailer assertions must be made against the TRAILER LINE, never against the
    whole block: ``"82" not in rendered`` would also be satisfied by a build that
    dropped the row itself, so a whole-block assertion cannot tell "the trailer
    excluded the acked seq" from "the drain served nothing". Failing loudly on a
    missing/duplicated line keeps a vacuous pass impossible."""
    matches = [line for line in rendered.splitlines() if fragment in line]
    assert len(matches) == 1, (
        f"expected EXACTLY one line containing {fragment!r}, found {len(matches)}: {rendered!r}"
    )
    return matches[0]


class TestSendThreadInjectionCaseIsNotVACUOUS:
    """AUTHORIZED AMENDMENT R7's companion — the discrimination check the
    ``brief_publish.session`` case needed and did not have until #96's adversary
    wrote its docstring by hand.

    A ``RenderCase`` whose field never reaches the render is DECORATION: it
    drives the whole threat-char corpus through a string that is thrown away and
    reports green forever. This pin asserts the value really is served, so
    ``send.thread``'s battery coverage is a CHECKED fact."""

    async def test_the_send_render_actually_emits_the_thread_value(self) -> None:
        rendered = await _render_send_thread("q:cap-boundary", None)
        assert "q:cap-boundary" in rendered, (
            "the send.thread RenderCase never reaches the render — the injection battery is "
            f"driving a value the output discards, i.e. testing nothing: {rendered!r}"
        )

    async def test_and_it_is_the_QUESTION_line_that_carries_it(self) -> None:
        """Non-vacuity with the MECHANISM named: the thread must arrive via
        S4.1's question line, not via some other incidental echo — otherwise the
        case would keep passing after the question line was dropped."""
        with_question = await _render_send_thread("q:cap-boundary", None)
        without = AppContext._render_comms_send(
            _send_result(message=_message(thread="q:cap-boundary", question=False)),
            broadcast=False,
            session="wave7",
        )
        assert "q:cap-boundary" not in str(without), (
            "the send render emits the thread even when the message is NOT a question — the "
            "R7 injection case is then not testing S4.1's line, and the question line's own "
            f"emit/no-emit proof is weaker than it looks: {without!r}"
        )
        assert "q:cap-boundary" in with_question


class TestRenderCommsSendShape:
    """S4.1 — the send confirmation."""

    _QUESTION_CLAUSE = "awaiting an answer on thread"
    _DIRECTIVE_CLAUSE = "recipients must ack"

    @pytest.mark.parametrize("question", [True, False])
    @pytest.mark.parametrize("grade", ["signal", "directive"])
    async def test_the_question_teach_and_the_ack_trailer_are_ORTHOGONAL(
        self, question: bool, grade: str
    ) -> None:
        """THE ∀-PIN over the whole 2x2 product (the QUANTIFIER LAW: pin the
        outcome property for EVERY input and FORCE each fate with a fixture).

        ``question`` and ``grade`` are orthogonal by design — a signal can ask, a
        directive need not (03a2 / adversary W1). The committed directive-trailer
        proof holds ``question`` fixed and the new question-line proof holds
        ``grade`` fixed, so each is a single-variable discrimination and NEITHER
        can see a build that CORRELATES them. This can: a build emitting the
        question line only for signals, or the ack trailer only for non-questions,
        fails one of these four cells and only these four."""
        rendered = str(
            AppContext._render_comms_send(
                _send_result(message=_message(grade=grade, question=question)),
                broadcast=False,
                session="wave7",
            )
        )
        assert (self._QUESTION_CLAUSE in rendered) is question, (
            f"the question-teach line must be emitted IFF message.question (S4.1: TYPED "
            f"applicability, never a set_status string compare) — grade={grade!r} must not "
            f"move it: {rendered!r}"
        )
        assert (self._DIRECTIVE_CLAUSE in rendered) is (grade == "directive"), (
            f"the ack trailer must be emitted IFF grade == 'directive' — question={question!r} "
            f"must not move it: {rendered!r}"
        )

    async def test_the_question_line_names_the_MESSAGES_thread_not_the_session(self) -> None:
        """The value slot, discriminated. ``thread`` defaults TO the session at
        send, so a fixture where they are equal cannot tell a build that
        interpolates ``session`` from one that interpolates ``thread`` — the
        arithmetic-alignment class, in string form. Here they DIFFER."""
        rendered = str(
            AppContext._render_comms_send(
                _send_result(message=_message(thread="q:cap-boundary", question=True)),
                broadcast=False,
                session="wave7",
            )
        )
        line = _drain_line_containing(rendered, self._QUESTION_CLAUSE)
        assert "q:cap-boundary" in line, (
            f"the question line must name the MESSAGE's thread — the debt is thread-scoped "
            f"(03a2-R5: one thread carries one open question): {line!r}"
        )
        assert "wave7" not in line, (
            f"the question line named the SESSION where the THREAD belongs — an agent told to "
            f"watch the wrong thread is told to watch the wrong debt: {line!r}"
        )

    async def test_the_recipient_list_shares_ONE_display_cap_with_the_coverage_surface(
        self,
    ) -> None:
        """S4.1: the recipient list is capped at the SHARED ``_COVERAGE_NAMES_CAP``
        — ONE display-cap policy, not a second constant. Derived from the
        constant, never hardcoded, so changing it re-derives this fixture instead
        of silently unbinding the branch (the ``_P7A``/``_P7B`` discipline)."""
        names = [f"agent-{index:02d}" for index in range(_COVERAGE_NAMES_CAP + 2)]
        rendered = str(
            AppContext._render_comms_send(
                _send_result(message=_message(question=False), recipient_names=names),
                broadcast=False,
                session="wave7",
            )
        )
        shown = [name for name in names if name in rendered]
        assert len(shown) == _COVERAGE_NAMES_CAP, (
            f"the send receipt showed {len(shown)} of {len(names)} recipients — the shared "
            f"display cap is {_COVERAGE_NAMES_CAP}: {rendered!r}"
        )
        assert f"(+{len(names) - _COVERAGE_NAMES_CAP} more)" in rendered, (
            f"the over-cap variant must carry the TRUE remainder "
            f"({len(names) - _COVERAGE_NAMES_CAP}), not a window-relative one: {rendered!r}"
        )

    async def test_an_AT_CAP_recipient_list_does_not_claim_a_remainder(self) -> None:
        """The boundary the over-cap pin cannot see (cap vs cap+1 — the fixture
        scale no comms contract had written before #96). A build using ``>=``
        where ``>`` belongs renders ``(+0 more)`` here and nowhere else."""
        names = [f"agent-{index:02d}" for index in range(_COVERAGE_NAMES_CAP)]
        rendered = str(
            AppContext._render_comms_send(
                _send_result(message=_message(question=False), recipient_names=names),
                broadcast=False,
                session="wave7",
            )
        )
        assert "more)" not in rendered, rendered
        assert all(name in rendered for name in names), rendered

    async def test_the_send_receipt_names_the_MESSAGES_seq_and_grade(self) -> None:
        """MAJOR M7 (adversary W22, W23). The receipt's ``{seq}`` and ``{grade}``
        slots are unread by any committed pin. The seq matters twice over: the
        directive trailer tells the recipients to ack THAT seq, so a wrong receipt
        seq and a wrong trailer seq must both be caught. Seq 41 and grade
        ``directive`` are chosen so neither can pass by accident (41 is not a
        substring of any grade; ``directive`` is not a substring of the session)."""
        rendered = str(
            AppContext._render_comms_send(
                _send_result(
                    message=_message(seq=41, grade="directive", question=False, session="wave7")
                ),
                broadcast=False,
                session="wave7",
            )
        )
        receipt = _drain_line_containing(rendered, "sent #")
        assert "sent #41 [directive]" in receipt, (
            "the send receipt named the wrong seq or grade — W22 shows seq+1, W23 hardcodes the "
            f"grade (here it renders the session): {receipt!r}"
        )
        trailer = _drain_line_containing(rendered, "recipients must ack")
        assert "seqs=[41]" in trailer, (
            f"the directive trailer told recipients to ack a seq that is not the message's: {trailer!r}"
        )

    async def test_the_capped_recipient_list_shows_the_FIRST_names(self) -> None:
        """MINOR m1 (adversary W42). The cap pins count how MANY names show; none
        checks WHICH. A build slicing the TAIL (``[-cap:]``) shows exactly the cap
        count and passes them — but names the wrong recipients. cap+2 names, all
        distinct: the first name must show and the last must not, tested by EXACT
        membership in the comma-split list so a future rename cannot make one name
        a substring of another and silently double-count."""
        names = [f"agent-{index:02d}" for index in range(_COVERAGE_NAMES_CAP + 2)]
        rendered = str(
            AppContext._render_comms_send(
                _send_result(message=_message(question=False), recipient_names=names),
                broadcast=False,
                session="wave7",
            )
        )
        receipt = _drain_line_containing(rendered, "sent #")
        recipients_field = receipt.split("→", 1)[1].split("(+")[0]
        listed = {segment.strip() for segment in recipients_field.split(",")}
        assert names[0] in listed, (
            f"the first recipient is missing — a build slicing the TAIL of the list shows the "
            f"LAST cap names instead of the first (W42): {receipt!r}"
        )
        assert names[-1] not in listed, (
            f"the LAST (over-cap) recipient appears — the list was sliced from the tail (W42): {receipt!r}"
        )


class TestRenderCommsDrainShape:
    """S4.2 — the drain block: header, rows, trailers, elision.

    ⚠ ESCALATION D2, RAISED HERE AND NOW RULED (design sidecar 2026-07-24, S8;
    AUTHORIZED AMENDMENT 10). S4.2 rules the context cell's precedence as
    ``task_id present -> ' (task {task_id})'; else thread != session ->
    ' (thread {thread})'; else empty``. The predecessor contract author found the
    THIRD branch UNREACHABLE — it needs the SESSION, which neither the signature
    S4.2 itself stated (``_render_comms_drain(result, *, agent_name, limit)``, the
    one the committed drivers pinned by calling it) nor
    ``MessageDrainResult``/``InboxEntry`` carried — pinned branches 1 and 2 plus
    the SINGULARITY property, and left branch 3 deliberately unpinned rather than
    improvising a design decision.

    **RULED: reading A.** ``_render_comms_drain`` gains a REQUIRED ``session: str``
    kwarg — the house shape (``_render_comms_send`` already takes one), REQUIRED
    and never defaulted so that no call site can silently make the branch
    unreachable again (a defaulted branch-comparand is the fixture-monoculture
    hazard moved down to the SIGNATURE layer). Branch 3 is pinned below.

    **AUTHORIZED AMENDMENT R5-OUTCOME-2 (design sidecar 2026-07-24): the ruled
    signature is now ``_render_comms_drain(result, *, session)``.** The adversary's
    R5/m4 flagged ``agent_name`` and ``limit`` as DEAD ruled params — ``agent_name``
    never had a consumer (no drain template carries ``{name}``; the row is
    ``{sender}→you`` with a literal second person — a recorded deliberate choice,
    NOT to be re-added as a header/label) and ``limit`` was orphaned when the
    elision was ruled fully result-derived (``more = total_pending − shown``;
    ``next_limit == more``). Both are dropped. The dropped signature IS the pin:
    every driver now calls ``_render_comms_drain(result, session=…)``, so a build
    whose render still requires either param is a ``TypeError`` at the call sites.

    **Reading B — "drop branch 3; always render the thread cell when ``task_id``
    is None" — was REFUSED, and the reason BINDS A BUILDER**, so it is recorded in
    the instrument rather than only in the ruling: most fleet traffic rides the
    session-default thread, so under B every row of this subsystem's
    highest-volume render carries a ``(thread wave7)`` cell that teaches nothing
    — and it destroys the signal S5's one-thread-one-debt teaching leans on, where
    a thread label MEANS "a deliberate conversation" only because default-thread
    rows stay bare. Suppression is load-bearing, not cosmetic."""

    _ACK_REQUIRED = "ACK REQUIRED"
    _ALREADY_ACKED = "ALREADY ACKED"
    _ELISION = "more unread"
    _THREAD_CELL = "(thread "

    @staticmethod
    def _render(
        entries: list[Any],
        *,
        total_pending: int | None = None,
        peeked: bool = False,
        session: str,
    ) -> str:
        """Drive the REAL drain render (AMENDMENT 10 added ``session``).

        ``session`` carries a default ONLY so that the twenty committed call sites
        below keep rendering exactly what they rendered before this amendment —
        it is the mechanical half of the amendment, not a design choice about the
        production signature, which is REQUIRED and un-defaulted per the ruling.
        The default cannot manufacture a value monoculture here because
        :meth:`test_the_SUPPRESSED_thread_is_the_SESSION_ARGUMENT_not_a_LITERAL`
        drives a DIFFERENT session and inverts which of two rows draws the cell;
        a build hardcoding ``"wave7"`` fails there and only there.

        AUTHORIZED AMENDMENT R5-OUTCOME-2 (design sidecar 2026-07-24): the render's
        ``agent_name`` and ``limit`` kwargs are DROPPED — the elision is fully
        result-derived (``more = total_pending − len(entries)``; ``next_limit ==
        more``; emit predicate ``total_pending > shown``), so the render never read
        ``limit``, and no drain template carries ``{name}`` (the row is
        ``{sender}→you`` with a literal second person). This driver no longer
        forwards either; passing them to ``_render_comms_drain`` is now a
        ``TypeError``."""
        return str(
            AppContext._render_comms_drain(
                _drain_result(entries=entries, total_pending=total_pending, peeked=peeked),
                session=session,
            )
        )

    # -- AUTHORIZED AMENDMENT R3: the acked_at monoculture, closed -------------

    async def test_an_ACKED_directive_row_draws_NO_ack_demand(self) -> None:
        """AUTHORIZED AMENDMENT R3 (operator 2026-07-24) — THE LIVE FALSE GATE.

        The committed emit/no-emit proof for ``ACK REQUIRED`` varies only the
        GRADE and leaves ``acked_at=None`` on BOTH legs: an ``acked_at``
        MONOCULTURE. A build keying the trailer on ``grade == 'directive'`` ALONE
        — ignoring ``acked_at is None`` — passes both committed legs with the
        defect fully intact, and then re-nags every directive the agent has
        already discharged. That is 03a2-R6's render law clause 1 violated
        ("ack-nudges key on ``acked_at``, NEVER on ``seen_at``; an acked directive
        never re-nags"), enforced here on 03b's OWN surface rather than only on
        packet 04's footer."""
        rendered = self._render(
            [_inbox_entry(seq=82, grade="directive", acked_at=datetime.now(UTC), thread="wave7")],
            session="wave7",
        )
        assert "#82" in rendered, f"fixture check: the acked directive row must still be SERVED: {rendered!r}"
        assert self._ACK_REQUIRED not in rendered, (
            "an ALREADY-ACKED directive drew an ACK REQUIRED demand — the trailer is keyed on "
            f"grade alone, which is the exact build the committed proofs cannot see: {rendered!r}"
        )

    async def test_the_ack_demand_lists_ONLY_the_UNACKED_directives(self) -> None:
        """THE DISCRIMINATING PIN. One acked directive and one unacked directive
        in the SAME drain: the trailer must fire (so this is not the trivially
        satisfiable "emit nothing" build) and must name the unacked seq ONLY.

        A grade-only build lists both and fails here; an "emit nothing when any
        row is acked" build fails the presence half. Seqs are 71 and 82 — two
        digits, no shared substring — so neither assertion can pass by accident."""
        rendered = self._render(
            [
                _inbox_entry(seq=71, grade="directive", acked_at=None, thread="wave7"),
                _inbox_entry(seq=82, grade="directive", acked_at=datetime.now(UTC), thread="wave7"),
            ],
            session="wave7",
        )
        line = _drain_line_containing(rendered, self._ACK_REQUIRED)
        assert "71" in line, f"the UNACKED directive must be demanded: {line!r}"
        assert "82" not in line, (
            f"an already-acked directive appears in the ACK REQUIRED demand — the trailer is "
            f"keyed on grade alone (R3): {line!r}"
        )

    async def test_POSITIVE_CONTROL_two_unacked_directives_are_BOTH_listed(self) -> None:
        """The control the pin above needs: with nothing acked, the trailer really
        can carry two seqs. Without it, a build that lists only the FIRST
        directive would pass the discrimination for the wrong reason."""
        rendered = self._render(
            [
                _inbox_entry(seq=71, grade="directive", acked_at=None, thread="wave7"),
                _inbox_entry(seq=82, grade="directive", acked_at=None, thread="wave7"),
            ],
            session="wave7",
        )
        line = _drain_line_containing(rendered, self._ACK_REQUIRED)
        assert "71" in line and "82" in line, line

    # -- S4.2's ALREADY ACKED trailer -----------------------------------------

    async def test_an_acked_SIGNAL_row_also_draws_the_ALREADY_ACKED_trailer(self) -> None:
        """The trailer's predicate is ``acked_at is not None``, NOT the grade.

        The registry proof for this line uses a DIRECTIVE on both legs (so its
        single variable is ``acked_at``); this pin supplies the other value of the
        parameter the code could branch on — repo law: "if the code can branch on
        a value, at least one pin must use a DIFFERENT value". A build that only
        reports already-acked DIRECTIVES passes the proof and fails here."""
        rendered = self._render(
            [_inbox_entry(seq=93, grade="signal", acked_at=datetime.now(UTC), thread="wave7")],
            session="wave7",
        )
        line = _drain_line_containing(rendered, self._ALREADY_ACKED)
        assert "93" in line, line

    async def test_the_two_trailers_partition_the_served_rows(self) -> None:
        """Both trailers in ONE drain, each naming only its own seqs. This is the
        render-layer statement of 03a2-R6 clause 3: a re-served acked message is
        self-explanatory, which was TRUE only of a model field the LLM consumer
        never sees until this line existed (DESIGN-LAW §1.6)."""
        rendered = self._render(
            [
                _inbox_entry(seq=71, grade="directive", acked_at=None, thread="wave7"),
                _inbox_entry(seq=82, grade="directive", acked_at=datetime.now(UTC), thread="wave7"),
            ],
            session="wave7",
        )
        demanded = _drain_line_containing(rendered, self._ACK_REQUIRED)
        settled = _drain_line_containing(rendered, self._ALREADY_ACKED)
        assert "71" in demanded and "82" not in demanded, demanded
        assert "82" in settled and "71" not in settled, settled

    async def test_no_ALREADY_ACKED_trailer_when_nothing_is_acked(self) -> None:
        rendered = self._render(
            [_inbox_entry(seq=71, grade="directive", acked_at=None, thread="wave7")],
            session="wave7",
        )
        assert self._ALREADY_ACKED not in rendered, rendered

    # -- S4.2's elision arithmetic --------------------------------------------

    async def test_the_elision_re_ask_is_the_REMAINDER_not_the_running_total(self) -> None:
        """S4.2, pinned WITH THE CONTRAST NAMED: ``next_limit = more``, NOT
        fleet's ``shown + more``.

        Fleet's window re-serves from the top, so its honest re-ask is the running
        total. A drain STAMPS what it serves, so stamped rows never come back and
        the honest re-ask is the REMAINDER. A builder copying
        ``_render_comms_fleet``'s arithmetic ships a re-ask that asks for rows the
        caller has already read — and the fixture is chosen so the two answers
        differ: 2 shown of 7 pending gives more=5 and shown+more=7."""
        rendered = self._render(
            [
                _inbox_entry(seq=61, thread="wave7"),
                _inbox_entry(seq=62, thread="wave7")], total_pending=7, session="wave7",
            
        )
        line = _drain_line_containing(rendered, self._ELISION)
        assert "+5" in line, f"the elided count must be total_pending - shown = 5: {line!r}"
        assert "limit=5" in line, (
            f"the re-ask must name the REMAINDER (5), not fleet's shown+more (7) — a drain "
            f"stamps what it serves, so the elided rows are all that is left: {line!r}"
        )
        assert "limit=7" not in line, line
        assert "limit=2" not in line, f"the re-ask must not merely echo the caller's limit: {line!r}"

    async def test_no_elision_line_when_the_window_covered_everything(self) -> None:
        rendered = self._render(
            [_inbox_entry(seq=61, thread="wave7"), _inbox_entry(seq=62, thread="wave7")],
            total_pending=2,
            session="wave7",
        )
        assert self._ELISION not in rendered, rendered

    # -- S4.2's peek rule (binding) -------------------------------------------

    async def test_a_PEEK_serves_no_ack_demand(self) -> None:
        """S4.2 (binding): trailers and the elision render on STAMPING drains
        ONLY. A peek is look-don't-consume; an ack demand on a peek MANUFACTURES
        the peek->ack anomaly 03a2-R6's render law exists to contain (the agent
        acks what it never had served, and the row then re-serves)."""
        entries = [_inbox_entry(seq=71, grade="directive", acked_at=None, thread="wave7")]
        assert self._ACK_REQUIRED not in self._render(entries, peeked=True, session="wave7")
        assert self._ACK_REQUIRED in self._render(entries, peeked=False, session="wave7"), (
            "POSITIVE CONTROL FAILED: the trailer does not fire on the STAMPING drain either, "
            "so the peek assertion above passes for the wrong reason"
        )

    async def test_a_PEEK_serves_no_ALREADY_ACKED_trailer(self) -> None:
        entries = [_inbox_entry(seq=82, grade="directive", acked_at=datetime.now(UTC), thread="wave7")]
        assert self._ALREADY_ACKED not in self._render(entries, peeked=True, session="wave7")
        assert self._ALREADY_ACKED in self._render(
            entries, peeked=False, session="wave7"
        ), "POSITIVE CONTROL FAILED"

    async def test_a_PEEK_serves_no_elision_line(self) -> None:
        entries = [_inbox_entry(seq=61, thread="wave7"), _inbox_entry(seq=62, thread="wave7")]
        assert self._ELISION not in self._render(
            entries, total_pending=7, peeked=True, session="wave7"
        ), (
            "a peek rendered the elision re-ask — its own header already discloses 'shown of "
            "total', and the re-ask would teach a re-run that stamps what the caller asked NOT "
            "to stamp"
        )
        assert self._ELISION in self._render(
            entries, total_pending=7, peeked=False, session="wave7"
        ), "POSITIVE CONTROL FAILED"

    async def test_a_PEEK_still_serves_its_header_and_rows(self) -> None:
        """The discrimination that stops "a peek renders nothing" from passing the
        three pins above: header + rows are exactly what a peek DOES serve."""
        rendered = self._render(
            [_inbox_entry(seq=71, grade="directive", thread="wave7")],
            peeked=True,
            session="wave7",
        )
        assert "#71" in rendered, rendered
        assert "nothing stamped" in rendered, rendered

    # -- S4.2's context cell ---------------------------------------------------

    async def test_the_context_cell_prefers_the_TASK_over_the_thread(self) -> None:
        """S4.2: the cell is SINGULAR with ``task_id`` first. The fixture supplies
        BOTH a task and a non-session thread — a fixture with only one of them
        cannot see a build that renders both cells, or one that picks the wrong
        winner."""
        rendered = self._render(
            [_inbox_entry(seq=71, task_id="T-9", thread="q:cap-boundary")],
            session="wave7",
        )
        row = _drain_line_containing(rendered, "#71")
        assert "T-9" in row, f"the task cell must win when task_id is present: {row!r}"
        assert "q:cap-boundary" not in row, (
            f"the context cell is SINGULAR — a row carrying both cells doubles the row's "
            f"vocabulary and is not the ruled shape: {row!r}"
        )

    async def test_the_context_cell_falls_back_to_the_THREAD(self) -> None:
        rendered = self._render(
            [_inbox_entry(seq=71, task_id=None, thread="q:cap-boundary")],
            session="wave7",
        )
        row = _drain_line_containing(rendered, "#71")
        assert "q:cap-boundary" in row, row

    # -- AUTHORIZED AMENDMENT 10: S4.2 branch 3, ruled reachable (D2 -> reading A)

    def test_the_session_kwarg_is_REQUIRED_and_never_DEFAULTED(self) -> None:
        """The half of the ruling that is otherwise only PROSE.

        D2 ruled the kwarg "REQUIRED, never defaulted", and gave the reason: a
        defaulted branch-comparand lets any call site silently make branch 3
        unreachable again — the fixture-monoculture hazard moved down to the
        SIGNATURE layer. Nothing else in this contract enforces it. A builder who
        ships ``session: str = ""`` satisfies every behavioural pin above (they
        all pass a session explicitly) while leaving the door the ruling closed
        standing wide open for the next call site — and this repo has already paid
        for exactly that shape twice, at ``_p03_entry``'s ``acked_at`` (amendment
        8, which pinned the same property as a ``TypeError``) and at ``_brief()``'s
        ``name``.

        Keyword-ONLY is pinned with it: the house shape is
        ``_render_comms_send(result, *, broadcast, session)``, and a positional
        ``session`` would let an argument land there by position — the same silent
        wrong value from the other direction."""
        import inspect

        parameter = inspect.signature(AppContext._render_comms_drain).parameters["session"]
        assert parameter.default is inspect.Parameter.empty, (
            "`session` carries a DEFAULT — D2 ruled it REQUIRED precisely so that no call site "
            f"can silently make branch 3 unreachable again (default was {parameter.default!r})"
        )
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, (
            f"`session` must be keyword-only, matching `_render_comms_send`: {parameter.kind}"
        )

    def test_POSITIVE_CONTROL_the_default_probe_can_actually_see_a_default(self) -> None:
        """The control the pin above needs: `inspect` reporting ``empty`` must
        MEAN something. A probe that reported ``empty`` unconditionally — or that
        read the wrong parameter — would green-light the very build the pin
        exists to reject, which is the "passed for the WRONG REASON" class this
        repo made standing law."""
        import inspect

        def _defaulted(result: Any, *, session: str = "wave7") -> None:  # pragma: no cover
            """A deliberately WRONG-shaped twin of the ruled signature."""

        wrong = inspect.signature(_defaulted).parameters["session"]
        assert wrong.default == "wave7", (
            "POSITIVE CONTROL FAILED: the probe cannot see a default that is demonstrably "
            f"there, so its verdict on the real signature is worthless: {wrong.default!r}"
        )
        assert wrong.default is not inspect.Parameter.empty

    async def test_a_SESSION_DEFAULT_thread_draws_no_cell_but_a_DELIBERATE_one_does(
        self,
    ) -> None:
        """THE DISCRIMINATING PAIR the ruling requires — ONE render, TWO rows.

        Row #71 rides ``thread == session``; row #72 rides a deliberate thread.
        The pair is what a single-thread fixture cannot be: a build that IGNORES
        ``session`` and always renders the cell fails on #71; a build that never
        renders it fails on #72; a build that inverts the comparison fails on
        both. Neither row alone discriminates — that is precisely why the two
        committed context-cell pins above (both on non-default threads) could not
        see this branch at all.

        Both rows are in ONE render so the discrimination is PER-ROW, not
        per-call: a build deciding the cell once for the whole drain (from the
        first entry, or from ``result``) renders the same thing on both rows and
        fails here."""
        rendered = self._render(
            [
                _inbox_entry(seq=71, task_id=None, thread="wave7"),
                _inbox_entry(seq=72, task_id=None, thread="q:cap-boundary"),
            ],
            session="wave7",
        )
        default_row = _drain_line_containing(rendered, "#71")
        deliberate_row = _drain_line_containing(rendered, "#72")
        assert self._THREAD_CELL not in default_row, (
            "a row on the SESSION-DEFAULT thread drew a thread cell — S4.2 branch 3 rules it "
            "EMPTY, and reading B was refused because labelling the default thread on every "
            "row of the highest-volume comms render teaches nothing AND destroys the signal "
            "S5's one-thread-one-debt teaching leans on (a thread label must MEAN a deliberate "
            f"conversation): {default_row!r}"
        )
        assert "wave7" not in default_row, (
            f"the session leaked into the default-thread row by some other route: {default_row!r}"
        )
        assert self._THREAD_CELL in deliberate_row and "q:cap-boundary" in deliberate_row, (
            "a row on a DELIBERATE (non-session) thread drew NO thread cell — branch 2 is the "
            f"half of the cell that must still fire: {deliberate_row!r}"
        )

    async def test_the_SUPPRESSED_thread_is_the_SESSION_ARGUMENT_not_a_LITERAL(self) -> None:
        """THE MONOCULTURE KILLER: the same two thread values, SWAPPED ROLES.

        Every other drain driver in this contract passes ``session="wave7"`` — so
        a build spelling the branch ``entry.thread != "wave7"`` (a hardcoded
        literal, ignoring its own argument) passes the pair above and every other
        pin in this file. Here the session is ``"wave9"``: the row that was BARE
        in the pair now draws a cell, and a ``"wave9"`` row is the bare one. The
        value suppressed in one pin is the value REQUIRED to render in the other,
        so no single literal can satisfy both.

        Repo law, applied literally: "if the code can branch on a value, at least
        one pin must use a DIFFERENT value"."""
        rendered = self._render(
            [
                _inbox_entry(seq=71, task_id=None, thread="wave9"),
                _inbox_entry(seq=72, task_id=None, thread="wave7"),
            ],
            session="wave9",
        )
        matching_row = _drain_line_containing(rendered, "#71")
        other_row = _drain_line_containing(rendered, "#72")
        assert self._THREAD_CELL not in matching_row, (
            "the cell was suppressed for a hardcoded 'wave7' rather than for the SESSION this "
            f"render was given ('wave9') — the branch ignores its own argument: {matching_row!r}"
        )
        assert self._THREAD_CELL in other_row and "wave7" in other_row, (
            "the row whose thread differs from the session ('wave7' vs 'wave9') drew no cell — "
            f"the build suppresses on a literal, not on the argument: {other_row!r}"
        )

    async def test_a_TASK_row_on_the_SESSION_thread_STILL_draws_its_TASK_cell(self) -> None:
        """The wrong build reading A NEWLY ADMITS, and which no committed pin sees.

        Branch 1 (task) is unconditional; only branch 2 is gated on
        ``thread != session``. A builder who wraps the WHOLE cell in that gate —
        ``if thread != session: <task or thread cell>`` — still passes
        ``test_the_context_cell_prefers_the_TASK_over_the_thread`` (whose fixture
        rides a NON-session thread, so its gate happens to be open) and silently
        drops the task anchor from every task row on the session-default thread,
        which is where most task traffic actually lives. The fixture that catches
        it is the one no committed pin has: ``task_id`` set AND
        ``thread == session``."""
        rendered = self._render(
            [_inbox_entry(seq=71, task_id="T-9", thread="wave7")], session="wave7"
        )
        row = _drain_line_containing(rendered, "#71")
        assert "(task T-9)" in row, (
            "a task-anchored row on the session-default thread lost its TASK cell — branch 1 is "
            "UNCONDITIONAL; only the thread cell is gated on 'thread != session' (S4.2), and a "
            f"build gating both drops the anchor exactly where task traffic lives: {row!r}"
        )
        assert self._THREAD_CELL not in row, (
            f"the context cell is SINGULAR — the task cell wins and stands alone: {row!r}"
        )

    # -- S4.2's header, ordering, refs, row slots (adversary's unread numbers) -

    async def test_the_header_names_the_TRUE_pending_total(self) -> None:
        """CRITICAL C1 (adversary W4, W5). The header's ``{shown}``/``{total}`` are
        read by no committed pin, so a build reporting ``drained 2 of 2`` while five
        wait passes 1092/1092. The peek variant is worse: S4.2 lets a peek skip the
        elision line BECAUSE its header already discloses ``shown of total`` — a
        lying header removes the only disclosure a peek has. Two shown, seven
        pending, on the stamping AND the peek header."""
        entries = [_inbox_entry(seq=61, thread="wave7"), _inbox_entry(seq=62, thread="wave7")]
        stamping = self._render(entries, total_pending=7, session="wave7")
        assert stamping.splitlines()[0] == "drained 2 of 7 pending", (
            f"the stamping header did not name the TRUE pending total (7) — W4 reports the window "
            f"size (2) as the total: {stamping.splitlines()[0]!r}"
        )
        peek = self._render(entries, total_pending=7, peeked=True, session="wave7")
        assert peek.splitlines()[0] == (
            "peeked 2 of 7 pending — nothing stamped; re-run without peek=true to mark them seen"
        ), (
            f"the peek header did not name the TRUE pending total (7) — W5 lies the same way, and "
            f"a peek's header is its ONLY disclosure of what it left behind: {peek.splitlines()[0]!r}"
        )

    async def test_an_unacked_SIGNAL_is_not_demanded(self) -> None:
        """CRITICAL C2 (adversary W41). Amendment R3 closed the ``acked_at``
        monoculture on the ACK REQUIRED trailer and left the GRADE monoculture
        untouched — every committed ACK-REQUIRED fixture is directive-only or a
        lone signal. One unacked signal AND one unacked directive in ONE drain: the
        demand names the DIRECTIVE only. A grade-blind build (fires when ANY
        directive is unacked, then lists every unacked row) lists the signal too."""
        rendered = self._render(
            [
                _inbox_entry(seq=93, grade="signal", acked_at=None, thread="wave7"),
                _inbox_entry(seq=71, grade="directive", acked_at=None, thread="wave7"),
            ],
            session="wave7",
        )
        line = _drain_line_containing(rendered, self._ACK_REQUIRED)
        assert "71" in line, f"the unacked DIRECTIVE must be demanded (positive control): {line!r}"
        assert "93" not in line, (
            "an unacked SIGNAL was listed in the ACK REQUIRED demand — the trailer is grade-blind "
            f"(W41): only unacked DIRECTIVES are owed an ack: {line!r}"
        )

    async def test_the_ACK_REQUIRED_command_is_RUNNABLE(self) -> None:
        """CRITICAL C3 (adversary W6). The registry proof marker stops at
        ``ACK REQUIRED: #71`` — one character before the part that has to be TRUE.
        §9.7's litmus: "if the reader ran the taught command WITH ITS DEFAULTS,
        would the promised thing happen?" With ``seqs=[]`` it acks nothing. The
        taught command must name every demanded seq."""
        rendered = self._render(
            [
                _inbox_entry(seq=71, grade="directive", acked_at=None, thread="wave7"),
                _inbox_entry(seq=72, grade="directive", acked_at=None, thread="wave7"),
            ],
            session="wave7",
        )
        line = _drain_line_containing(rendered, self._ACK_REQUIRED)
        taught = re.search(r"action=ack seqs=\[([^\]]*)\]", line)
        assert taught is not None, (
            f"the ACK REQUIRED trailer taught no runnable 'action=ack seqs=[...]' command: {line!r}"
        )
        taught_seqs = taught.group(1)
        assert "71" in taught_seqs and "72" in taught_seqs, (
            "the ACK REQUIRED command's seqs=[...] does not name every demanded seq — running it "
            f"with its defaults acks nothing (W6 renders seqs=[]): {line!r}"
        )

    async def test_the_drain_serves_its_rows_in_LEDGER_order(self) -> None:
        """MAJOR M2 (adversary W25). The committed pins locate rows by seq, never by
        POSITION, so a build serving the ledger's oldest-first order in REVERSE
        passes them all. #61 must render above #62."""
        rendered = self._render(
            [_inbox_entry(seq=61, thread="wave7"), _inbox_entry(seq=62, thread="wave7")],
            session="wave7",
        )
        assert rendered.index("#61") < rendered.index("#62"), (
            "the drain served its rows out of ledger order — the render reversed the oldest-first "
            f"ordering the ledger guarantees (W25): {rendered!r}"
        )

    async def test_every_served_row_renders_ABOVE_the_first_trailer(self) -> None:
        """MAJOR M3 (adversary W8). S4.2 rules the composition header · rows ·
        trailers · elision. Block order is UNPINNED: a build rendering the ACK
        REQUIRED demand and the elision ABOVE the messages passes every committed
        pin, and an LLM reads the demand before the rows it is about."""
        rendered = self._render(
            [
                _inbox_entry(seq=61, grade="directive", acked_at=None, thread="wave7"),
                _inbox_entry(seq=62, grade="directive", acked_at=None, thread="wave7"),
            ],
            total_pending=7,
            session="wave7",
        )
        last_row = max(rendered.index("#61"), rendered.index("#62"))
        assert last_row < rendered.index(self._ACK_REQUIRED), (
            f"a served row rendered BELOW the ACK REQUIRED trailer — S4.2's composition inverted "
            f"(W8): {rendered!r}"
        )
        assert last_row < rendered.index("more unread"), (
            f"a served row rendered BELOW the elision line — S4.2's composition inverted (W8): "
            f"{rendered!r}"
        )

    async def test_a_row_with_REFS_renders_them(self) -> None:
        """MAJOR M4 (adversary W7). The refs row variant is live only as a STATIC
        literal in the promise registry; nothing RENDERS it. A build dropping refs
        entirely (``if False:``) passes, and a caller's pointers vanish."""
        rendered = self._render(
            [_inbox_entry(seq=71, refs=["REPORT-x.md"], thread="wave7")],
            session="wave7",
        )
        row = _drain_line_containing(rendered, "#71")
        assert "REPORT-x.md" in row, (
            f"a row carrying refs did not render them — the refs variant is dead code (W7): {row!r}"
        )

    async def test_the_row_names_the_GRADE_and_the_SENDER_in_the_right_slots(self) -> None:
        """MAJOR M5 (adversary W24, W24b). The row's ``{grade}``/``{sender}`` slots
        are read by no committed pin. Grade ``signal`` in the bracket slot and
        sender ``lead`` in the arrow slot are not confusable, so a build feeding the
        grade slot the sender (or the sender slot the thread/grade) is caught. A
        SIGNAL grade is used deliberately so no ACK REQUIRED trailer also carries
        the seq, keeping the row line uniquely locatable."""
        rendered = self._render(
            [_inbox_entry(seq=71, grade="signal", sender_name="lead", thread="wave7")],
            session="wave7",
        )
        row = _drain_line_containing(rendered, "#71")
        assert "[signal]" in row, (
            f"the grade slot did not carry the grade — a build swapping grade and sender puts the "
            f"sender name in the bracket (W24b): {row!r}"
        )
        assert "lead→you" in row, (
            "the sender slot did not name the SENDER — W24 feeds it the thread, W24b feeds it the "
            f"grade: {row!r}"
        )


class TestRenderCommsAckShape:
    """S4.3 — the ack confirmation, which the committed contract left UNPINNED end
    to end (adversary W10–W15b). Four group-lines in FIXED order (acked ·
    already-acked · not-addressed · unknown), seqs within each group in REQUEST
    order, the receipt's own counts, and the not-addressed identity — all driven
    against the REAL ``_render_comms_ack`` here; the WIRING (that the handler calls
    it at all) is pinned at the dispatcher by
    ``TestDrainAndAckAtTheDispatcher::test_the_ACK_dispatcher_serves_the_ACK_RENDER``.
    """

    @staticmethod
    def _entry(*, seq: int, outcome: str) -> Any:
        return _msg().MessageAckEntry(
            seq=seq,
            outcome=outcome,
            acked_at=datetime.now(UTC) if outcome in {"acked", "already_acked"} else None,
        )

    def test_the_four_groups_render_in_FIXED_order(self) -> None:
        """W13. All four outcomes in ONE ack, input order deliberately NOT the
        rendered order: the render must impose acked · already · not-addressed ·
        unknown regardless. A build composing the lines in reverse fails here."""
        rendered = str(
            AppContext._render_comms_ack(
                _ack_result(
                    entries=[
                        self._entry(seq=4, outcome="unknown_message"),
                        self._entry(seq=3, outcome="not_addressed"),
                        self._entry(seq=2, outcome="already_acked"),
                        self._entry(seq=1, outcome="acked"),
                    ]
                ),
                agent_name="fixer-b",
            )
        )
        order = [
            rendered.index("acked 1 of"),
            rendered.index("already acked:"),
            rendered.index("not addressed to you:"),
            rendered.index("unknown message seq(s):"),
        ]
        assert order == sorted(order), (
            "the ack groups did not render in the FIXED order acked · already-acked · "
            f"not-addressed · unknown (S4.3) — the composition was scrambled (W13): {rendered!r}"
        )

    def test_seqs_within_a_group_stay_in_REQUEST_order(self) -> None:
        """W14. The ledger result is per-seq request-ordered; the render groups
        WITHOUT re-sorting. Two acked seqs supplied 9 then 3: the render must keep
        ``#9, #3``. A build sorting each bucket renders ``#3, #9``."""
        rendered = str(
            AppContext._render_comms_ack(
                _ack_result(
                    entries=[
                        self._entry(seq=9, outcome="acked"),
                        self._entry(seq=3, outcome="acked"),
                    ]
                ),
                agent_name="fixer-b",
            )
        )
        line = _drain_line_containing(rendered, "acked 2 of")
        assert line.index("#9") < line.index("#3"), (
            f"the acked group re-sorted its seqs — S4.3 keeps REQUEST order (W14): {line!r}"
        )

    def test_the_receipt_counts_are_the_TRUE_counts(self) -> None:
        """W11. ``acked {acked} of {requested}`` — acked is the count of freshly
        stamped edges, requested is the number of seqs asked. One acked + one
        already-acked ⇒ ``acked 1 of 2``. A build hardcoding ``0 of 0`` passes every
        other pin (the group still lists its seq)."""
        rendered = str(
            AppContext._render_comms_ack(
                _ack_result(
                    entries=[
                        self._entry(seq=1, outcome="acked"),
                        self._entry(seq=2, outcome="already_acked"),
                    ]
                ),
                agent_name="fixer-b",
            )
        )
        line = _drain_line_containing(rendered, "acked ")
        assert "acked 1 of 2:" in line, (
            f"the acked receipt did not carry the TRUE counts (1 of 2) — W11 renders 0 of 0: {line!r}"
        )

    def test_already_acked_is_a_DISTINCT_group_from_acked(self) -> None:
        """W12. A re-served already-acked seq must render on the ALREADY-ACKED line,
        never folded into the acked line — folding reports a fresh stamp for a seq
        the caller never actually stamped this call."""
        rendered = str(
            AppContext._render_comms_ack(
                _ack_result(
                    entries=[
                        self._entry(seq=1, outcome="acked"),
                        self._entry(seq=2, outcome="already_acked"),
                    ]
                ),
                agent_name="fixer-b",
            )
        )
        acked_line = _drain_line_containing(rendered, "acked 1 of 2:")
        already_line = _drain_line_containing(rendered, "already acked:")
        assert "#1" in acked_line and "#2" not in acked_line, (
            f"the already-acked seq was folded into the acked group (W12): {acked_line!r}"
        )
        assert "#2" in already_line and "#1" not in already_line, already_line

    def test_not_addressed_names_the_CALLER(self) -> None:
        """W15. ``not addressed to you: ... no delivery to {name}`` names the caller
        — the render's only use of ``agent_name``. A build hardcoding a name teaches
        the wrong identity."""
        rendered = str(
            AppContext._render_comms_ack(
                _ack_result(entries=[self._entry(seq=5, outcome="not_addressed")]),
                agent_name="fixer-b",
            )
        )
        line = _drain_line_containing(rendered, "not addressed to you:")
        assert "to fixer-b" in line, (
            f"the not-addressed line named an identity other than the CALLER (W15): {line!r}"
        )


class TestDrainThreadInjectionCaseIsNotVACUOUS:
    """AMENDMENT 10's companion — the premise the ruling ASSERTS, CHECKED.

    The ruling keeps the battery's ``drain.thread`` RenderCase valid on the
    grounds that "hostile values are never ``'wave7'``, so the cell renders and
    sanitisation is still exercised". That is a PREMISE about the corpus and the
    driver, and reading A is what made it load-bearing: the day the driver's
    thread rides the session, the context cell VANISHES, the injected value never
    reaches the output, and twenty-one battery cases go on reporting green while
    testing nothing — the ``brief_publish.session``/``behind=[]`` shape the #96
    adversary caught, re-manufactured by a branch rather than by a fixture.

    So the premise is asserted over the REAL corpus rather than trusted."""

    @pytest.mark.parametrize("threat", _INJECTION_THREAT_CHARS, ids=lambda t: f"U+{ord(t):04X}")
    async def test_every_battery_value_still_reaches_the_context_cell(self, threat: str) -> None:
        """Driven with exactly what ``TestC1RenderInjectionBattery`` drives."""
        rendered = await _render_drain_thread(f"benign{threat}{_ROW_FORGE_PAYLOAD}", None)
        assert "(thread " in rendered, (
            "the drain.thread injection case renders NO context cell — the hostile value is "
            "discarded before it can be sanitised, so the battery's twenty-one green cases for "
            f"this field are decoration: {rendered!r}"
        )

    async def test_the_batterys_BENIGN_baseline_reaches_it_too(self) -> None:
        """The other arm of every battery case: its baseline render."""
        rendered = await _render_drain_thread("benign", None)
        assert "(thread benign)" in rendered, rendered

    async def test_POSITIVE_CONTROL_the_check_can_actually_see_a_suppressed_cell(self) -> None:
        """The control this pin needs to be worth anything: drive the SAME driver
        with the value that DOES collide with its session and show the cell really
        does disappear. Without it, the two assertions above could be passing
        because the cell is unconditional — i.e. because branch 3 was never built
        — and this class would then be certifying a build the pair pin rejects."""
        rendered = await _render_drain_thread("wave7", None)
        assert "(thread " not in rendered, (
            "POSITIVE CONTROL FAILED: a thread equal to the driver's session STILL drew a cell, "
            f"so this non-vacuity check cannot distinguish emitted from suppressed: {rendered!r}"
        )


class TestDrainTaskIdAndRefsInjectionCasesAreNotVACUOUS:
    """MINOR m2's companion — the same non-vacuity guard the ``drain.thread`` case
    needed, for the two fields this wave adds to the battery. A RenderCase whose
    field never reaches the render is decoration that reports green forever."""

    async def test_the_drain_task_id_case_reaches_the_context_cell(self) -> None:
        rendered = await _render_drain_task_id("T-benign", None)
        assert "(task T-benign)" in rendered, (
            "the drain.task_id injection case renders no task cell — the value is discarded before "
            f"it can be sanitised, so its battery cases are decoration: {rendered!r}"
        )

    async def test_the_drain_refs_case_reaches_the_row(self) -> None:
        rendered = await _render_drain_refs("REPORT-benign.md", None)
        assert "REPORT-benign.md" in rendered, (
            "the drain.refs injection case never renders the ref — the value is discarded, so its "
            f"battery cases are decoration: {rendered!r}"
        )


class TestTheDrainSurfaceConvergesOnAnAckedButUndrainedMessage:
    """03a2-R6's convergence, at the SURFACE (inherited delta row 8).

    ``seen_at`` and ``acked_at`` are independent write-once facts: seen = served
    by a stamping drain, acked = actioned by the recipient, and neither implies
    the other IN THE STORE (implications belong to renders). The consumer-visible
    consequence — an acked-but-never-drained message is still counted pending and
    IS served once more — was ruled coherent, transient, and in the safe
    direction, **on the condition that the render explains itself**. This drives
    the whole path through the REAL dispatcher and pins all four halves of that
    condition: served, labelled, counted, converged.

    ⚠ SCOPE NOTE (contract author): the LEDGER-level ``[fake]``/``[real]`` legs of
    inherited delta row 8 belong in ``test_message_ledger.py``, which 03b's
    authorization freezes except for two mypy fixes. Flagged to the lead."""

    @staticmethod
    async def _ready() -> tuple[Any, Any]:
        registry = FakeAgentRegistry(db=FakeAgentDatabase())
        message_ledger = _msg_fakes().FakeMessageLedger(db=_msg_fakes().FakeMessageDatabase())
        harness = _harness(agent_registry=registry, message_ledger=message_ledger)
        for name in ("lead", "fixer-b"):
            await registry.register(name, session="wave7", role="builder")
            agent = await registry.get_agent(name, session="wave7")
            message_ledger.register_agent(agent_id=agent.id, name=agent.name)
        return harness, message_ledger

    async def test_an_acked_but_undrained_directive_is_served_labelled_counted_then_converges(
        self,
    ) -> None:
        harness, message_ledger = await self._ready()
        await AppContext.comms(
            harness,
            action="send",
            agent="lead",
            session="wave7",
            to=["fixer-b"],
            body="ack me without draining me",
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
        )
        [message] = list(message_ledger.db.messages.values())
        # Ack from out-of-band seq knowledge — the ONLY path into the anomaly.
        await AppContext.comms(
            harness, action="ack", agent="fixer-b", session="wave7", seqs=[message.seq]
        )
        assert all(edge.seen_at is None for edge in message_ledger.db.edges.values()), (
            "fixture check: ack must NOT stamp seen_at (03a2-R6) — without that the anomaly "
            "this pin exists for is unreachable and the whole test is decoration"
        )

        first = str(await AppContext.comms(harness, action="drain", agent="fixer-b", session="wave7"))
        assert f"#{message.seq}" in first, (
            f"the acked-but-unseen message was NOT served — the queue count would then be "
            f"lying about what a drain serves (03a2-R6 clause 2): {first!r}"
        )
        assert "of 1 pending" in first, (
            f"the acked row must be COUNTED in total_pending — counts key on seen_at and must "
            f"AGREE with what the drain then serves: {first!r}"
        )
        assert "ALREADY ACKED" in first, (
            "the re-served acked row carries no render-layer explanation — 03a2-R6 clause 3 "
            f"was true only of a model field the LLM consumer never sees: {first!r}"
        )
        assert "ACK REQUIRED" not in first, (
            f"a message the agent has ALREADY acked was nagged for an ack: {first!r}"
        )

        second = str(await AppContext.comms(harness, action="drain", agent="fixer-b", session="wave7"))
        assert f"#{message.seq}" not in second, (
            f"the anomaly did not CONVERGE — the first drain must stamp seen_at, so the row "
            f"is served exactly once more and never again: {second!r}"
        )
        assert "no unread messages" in second, second


class TestTheServedInstructionsTeachCommsMechanismsThatEXIST:
    """S5 — the instructions block, which is where an LLM consumer LEARNS the
    comms contract (DESIGN-LAW §1.5: strategy -> read-once instructions).

    Generalises ``TestTheFirstVersionLineTeachesAnAckMechanismThatACTUALLYEXISTS``
    from one clause to a ∀-pin: prose describing behaviour must be DERIVED from
    the behaviour, never re-stated beside it (#104). A retired or misspelled verb
    in served teaching goes RED mechanically."""

    @staticmethod
    def _action_tokens(text: str) -> set[str]:
        """Every ``action=<verb>`` token, including the ``a/b/c`` slash form the
        block uses to teach a family in one breath."""
        return {
            verb
            for group in re.findall(r"action=([a-z_]+(?:/[a-z_]+)*)", text)
            for verb in group.split("/")
        }

    @staticmethod
    def _comms_paragraph() -> str:
        paragraphs = [
            paragraph
            for paragraph in _INSTRUCTIONS.split("\n\n")
            if paragraph.startswith("COMMS:")
        ]
        assert len(paragraphs) == 1, (
            "the served instructions must carry exactly ONE 'COMMS:' paragraph (S5) — the "
            f"message verbs are taught nowhere else: {_INSTRUCTIONS!r}"
        )
        return paragraphs[0]

    def test_every_served_action_token_names_an_action_that_EXISTS(self) -> None:
        """THE ∀-PIN, over the WHOLE block and DERIVED from the dispatch tables —
        never a hand-list of verbs, which would rot the moment a table changed."""
        existing = set(_COMMS_ACTIONS) | set(_TASK_ACTIONS) | set(_FINDING_ACTIONS)
        served = self._action_tokens(_INSTRUCTIONS)
        assert served, "the instructions block teaches no action at all — the scan found nothing"
        unknown = sorted(served - existing)
        assert not unknown, (
            "the served instructions teach an action=<verb> that NO dispatch table declares — "
            "an agent following it gets a teaching error instead of the mechanism it was "
            f"promised (#104's class, in the one text every agent reads): {unknown!r}"
        )

    def test_the_comms_paragraph_teaches_ONLY_comms_actions(self) -> None:
        """The scoped half. The global pin above accepts any real verb anywhere,
        so it cannot see ``lore_comms action=rollup`` — a real verb attributed to
        the wrong tool. This paragraph names ONE tool, so its verbs must be that
        tool's."""
        paragraph = self._comms_paragraph()
        tools = set(re.findall(r"lore_[a-z_]+", paragraph))
        assert tools == {"lore_comms"}, (
            "the COMMS paragraph names a tool other than lore_comms, so the scoping premise "
            f"of this pin no longer holds — re-derive it before trusting it: {sorted(tools)!r}"
        )
        stray = sorted(self._action_tokens(paragraph) - set(_COMMS_ACTIONS))
        assert not stray, (
            f"the COMMS paragraph attributes a non-comms verb to lore_comms: {stray!r}"
        )

    def test_the_comms_paragraph_teaches_the_three_verbs_this_packet_ships(self) -> None:
        """COVERAGE AS A CHECKED VARIABLE: the two pins above are both satisfied by
        a paragraph that teaches NOTHING. 03b puts the message graph on the wire;
        an agent that never learns ``send``/``drain``/``ack`` cannot use it."""
        taught = self._action_tokens(self._comms_paragraph())
        assert {"send", "drain", "ack"} <= taught, sorted(taught)

    def test_the_thread_debt_rule_is_TAUGHT_not_merely_implemented(self) -> None:
        """S5 + 03a2-R5. Thread-debt was ruled KEEP: one answer discharges a
        THREAD's whole debt, and the partial-reply failure mode is recoverable
        ONLY by an asker who knows the rule. The send-time thread scan was
        REFUSED (a hot-path cost for a teaching job), so this static text is the
        ONLY place the consumer can learn it — an unlearnable protocol is an
        unfollowed one."""
        assert "separate questions take separate threads" in _INSTRUCTIONS, (
            "03a2-R5's one-thread-one-debt rule is not taught in the served instructions, and "
            "the send-time thread scan that would otherwise catch it was REFUSED"
        )

    def test_the_self_answer_rule_is_TAUGHT_too(self) -> None:
        """03a2-R2's fourth conjunct, in the consumer's language. With
        ``sender != me`` there is NO self-service clearing of a question — an
        agent that does not know this waits for a state change its own sends can
        never produce."""
        assert "your own sends never clear" in _INSTRUCTIONS.lower(), _INSTRUCTIONS

    def test_the_body_cap_is_DERIVED_from_the_constant(self) -> None:
        """CRITICAL C7 (adversary W16). The COMMS paragraph teaches a body cap; a
        build serving ``bodies cap at 20000 chars`` while the ledger rejects at
        2000 passes 1092/1092. Repo #104: "prose describing behaviour must be
        DERIVED from the behaviour, not re-stated beside it" — and the number is an
        importable constant. The served integer is extracted and compared to
        ``MESSAGE_BODY_MAX_CHARS``, so the two cannot drift."""
        paragraph = self._comms_paragraph()
        served = re.search(r"cap at (\d+) chars", paragraph)
        assert served is not None, (
            f"the COMMS paragraph states no 'cap at N chars' body-cap teach at all: {paragraph!r}"
        )
        assert int(served.group(1)) == _msg().MESSAGE_BODY_MAX_CHARS, (
            f"the served body cap ({served.group(1)}) does not match the enforced cap "
            f"({_msg().MESSAGE_BODY_MAX_CHARS}) — an agent is taught a limit the ledger does not "
            f"honour (W16, #104's class)"
        )

    def test_the_grade_and_peek_and_broadcast_semantics_taught_are_the_ones_IMPLEMENTED(
        self,
    ) -> None:
        """CRITICAL C8 (adversary W17, W18, W19). S5 rules this paragraph VERBATIM;
        the committed pins check 2 substrings of ~7 claims, so five ruled claims
        may be freely rewritten — and INVERTING peek, grade or broadcast semantics
        passes 1092/1092. Each teaches an agent the OPPOSITE of the behaviour:
        peek-inverted tells it a plain drain does not stamp (re-read forever);
        grade-inverted tells it signals demand acks; broadcast-inverted tells it
        ``to=[]`` sends to nobody. The ruled forms are asserted present and their
        inversions absent, so a rewrite of any one goes RED."""
        paragraph = self._comms_paragraph()
        # peek (W17): a plain drain STAMPS; peek=true LOOKS.
        assert "stamps what it serves as seen" in paragraph, (
            f"the peek semantics were inverted — a plain drain must be taught to STAMP (W17): {paragraph!r}"
        )
        assert "peek=true looks without stamping" in paragraph, (
            f"the peek clause no longer teaches that peek=true LOOKS without stamping (W17): {paragraph!r}"
        )
        # grade (W19): signal is fire-and-forget; directive demands an ack.
        assert "grade=signal is fire-and-forget" in paragraph, (
            f"the grade semantics were inverted — signal must be taught fire-and-forget (W19): {paragraph!r}"
        )
        assert "grade=directive demands an ack" in paragraph, (
            f"the grade clause no longer teaches that a directive demands an ack (W19): {paragraph!r}"
        )
        # broadcast (W18): to=[] broadcasts to all non-retired.
        assert "to=[] broadcasts to all non-retired" in paragraph, (
            "the broadcast teach was inverted — S5 rules to=[] as the broadcast form, and M1 "
            f"pins that the dispatcher agrees (W18): {paragraph!r}"
        )


class TestTheHarnessDoubleDoesNotHideAMissingProductionSurface:
    """THE TEST ENVIRONMENT IS A FICTION (repo CLAUDE.md), in miniature — and
    this file is where the fiction lives.

    ``_harness`` is a ``SimpleNamespace`` double carrying exactly the attributes
    ``AppContext.comms`` touches. That is a deliberate, documented testing
    strategy and it is the right one for dispatch logic — but it means the double
    DECLARES the production surface rather than checking it. Measured at 03b's
    contract wave (2026-07-24), against a full reference build of the S4/S5
    surface: the ENTIRE comms contract went **1060 passed / 0 failed** while the
    real ``CommsConfig`` had no ``drain_limit`` field and the real ``AppContext``
    took no ``message_ledger`` argument. No test could see it — every one of them
    was handed a namespace that had both. Only mypy against the real classes did,
    and 03b owns global mypy-zero.

    "What CONDITION does this fixture guarantee, and does production guarantee the
    opposite?" The double guarantees the dependency EXISTS. Production, today,
    guarantees it does not.

    The committed contract already leans on both:
    ``TestDrainAndAckAtTheDispatcher::test_drain_defaults_to_the_configured_limit_
    not_a_hardcoded_one`` states the drain window is ``comms.drain_limit`` config
    "like ``fleet_limit``, never a literal buried in the handler" — a premise
    nothing checked. These pins check it.
    """

    def test_CommsConfig_declares_the_drain_window_as_CONFIG(self) -> None:
        from loremaster.config import CommsConfig

        assert "drain_limit" in CommsConfig.model_fields, (
            "CommsConfig has no 'drain_limit' — the drain window is then a literal buried in "
            "the handler, which the committed dispatcher pin explicitly forbids, and the "
            "SimpleNamespace harness cannot see the difference"
        )
        assert isinstance(CommsConfig().drain_limit, int), (
            "drain_limit must carry a usable default like its fleet_limit sibling — a "
            "required field would break every existing lore.yaml"
        )

    def test_AppContext_actually_TAKES_a_message_ledger(self) -> None:
        import inspect

        parameters = inspect.signature(AppContext.__init__).parameters
        assert "message_ledger" in parameters, (
            "AppContext takes no 'message_ledger' — the dispatcher's handlers reach for "
            "self.message_ledger, so every lore_comms send/drain/ack raises AttributeError "
            "in the ARTIFACT while this suite stays green on a namespace double that has it"
        )

    def test_POSITIVE_CONTROL_the_already_wired_siblings_pass_the_same_checks(self) -> None:
        """A PROBE NEEDS A CONTROL. ``fleet_limit`` and ``agent_registry`` are the
        wired siblings of the two above; if the introspection below could not see
        THEM, the two pins would be failing for a reason that has nothing to do
        with the comms surface."""
        import inspect

        from loremaster.config import CommsConfig

        assert "fleet_limit" in CommsConfig.model_fields
        assert isinstance(CommsConfig().fleet_limit, int)
        parameters = inspect.signature(AppContext.__init__).parameters
        assert "agent_registry" in parameters and "brief_ledger" in parameters
