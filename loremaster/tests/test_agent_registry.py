"""Contract tests for ``loremaster.agents`` — the durable, fleet-visible AGENT
REGISTRY (PKT-28 C1 seam S2), against the REAL SurrealDB server (parametrized
against an ADVERSARIAL in-memory fake too — see ``_comms_fakes.py``).

Binding spec: ``docs/design/2026-07-12-pkt28-c1-semantics.md`` §0-§4, §7-§8
(agent identity/schema, bootstrap, re-register, the status state machine,
config knobs, the error taxonomy, the dispatch algorithm this ledger is
called from). Where this file's contract decisions are genuinely open in the
spec, they were recorded in ``REPORT-c1-contract-ledgers.md`` — the spec is
executed verbatim everywhere it speaks; this docstring does not re-transcribe
it. NOTE: that report was deleted per repo law and never archived, and — unlike
``test_brief_ledger.py``, whose open decisions are restated at their use sites —
no restatement of them survives anywhere in this file. The list of what this
contract chose where the spec was silent is LOST; treat any such decision as
unverified and re-derive it from the spec.

The pinned contract (the public surface THIS FILE decides — the module does
not exist yet, so these names ARE the contract a later STUB/GREEN phase must
match):

    Agent:                                  # a value object (pydantic model)
        id: str                             # opaque hex — uuid5(session:name)
        name: str
        session: str
        role: str
        model: str | None
        status: Literal[active|idle|input_required|retired]
        spawned_by: str | None
        task_id: str | None
        checkpoint: dict | None             # C1 ships the column, no C1 surface
        last_note: str | None
        registered_at: datetime             # tz-aware UTC, write-once
        heartbeat_at: datetime              # tz-aware UTC, touched every action

    AgentRegisterResult:
        agent: Agent
        re_registered: bool                 # False on first register

    AgentFleetWindow:
        rows: list[Agent]                   # non-retired, ordered per §6
        retired_count: int
        total_non_retired: int              # honest total BEFORE `limit` truncation

    AgentRegistry(*, url, namespace, database, user, password):
        async ensure_ready() -> None
        async close() -> None
        async register(name, *, session, role, model=None, spawned_by=None,
                        task_id=None) -> AgentRegisterResult
        async get_agent(name, *, session=None) -> Agent
        async touch(name, *, session=None, status=None, note=None) -> Agent
        async fleet(*, session=None, limit) -> AgentFleetWindow

    Exceptions: AgentRegistryError(RuntimeError);
                UnknownAgentError(AgentRegistryError);
                AmbiguousAgentError(AgentRegistryError);
                AgentIdentityConflictError(AgentRegistryError);
                RetiredAgentError(AgentRegistryError);
                IllegalAgentStatusError(AgentRegistryError).

    Module constants: AGENT_STATUSES, LEGAL_AGENT_TRANSITIONS, AGENT_NAME_PATTERN.

``touch`` is this ledger's ONE heartbeat/status-machine primitive: the
'heartbeat' MCP action calls it with a caller-supplied ``status``/``note``;
the dispatcher's UNIFORM per-action touch (spec §8 step 4) calls it with
``status=None`` for every OTHER action, which is exactly what drives the
idle -> active auto-flip and the retired-terminal check from one shared,
tested code path (spec §8's "one site, one test, uniform by construction"
rationale, applied one layer down).

Expected until the module lands: collection ERROR in THIS FILE —
``ModuleNotFoundError: No module named 'loremaster.agents'``.
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

import pytest
import pytest_asyncio
from _comms_fakes import FakeAgentDatabase, FakeAgentRegistry
from _governed_contract import identity_sweep_miss_message, patch_shared_object_everywhere
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealConnection,
    SurrealEnv,
    assert_domain_rejection,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from hypothesis import given, settings
from hypothesis import strategies as st
from loremaster.agents import (
    AGENT_NAME_PATTERN,
    AGENT_STATUSES,
    LEGAL_AGENT_TRANSITIONS,
    Agent,
    AgentIdentityConflictError,
    AgentRegistry,
    AgentRegistryError,
    AgentRosterMember,
    AmbiguousAgentError,
    FleetRoster,
    IllegalAgentStatusError,
    RetiredAgentError,
    UnknownAgentError,
)
from loremaster.render import render_fenced
from loremaster.server import _MAX_FLEET_LIMIT
from loremaster.store._txn import SurrealConnectionError, SurrealStoreError, _SurrealConnection
from loremaster.store.surreal_schema import AGENT_TABLE
from pydantic import SecretStr
from render_injection_scaffold import _ROW_FORGE_PAYLOAD
from surrealdb.errors import ErrorKind, ServerError
from test_comms_schema import _HOSTILE_IDENTIFIERS, _LEGAL_IDENTIFIER_WITNESSES

# --- the domain's status vocabulary (the convention this contract decides) ---
STATUS_ACTIVE = "active"
STATUS_IDLE = "idle"
STATUS_INPUT_REQUIRED = "input_required"
STATUS_RETIRED = "retired"

# --- realistic fleet identities (the spec's own §9.6 worked example names) ---
SESSION_WAVE7 = "wave7"
SESSION_WAVE8 = "wave8"
AGENT_FIXER_B = "fixer-b"
AGENT_AUDIT_C = "audit-c"
AGENT_SCOUT_D = "scout-d"
ROLE_BUILDER = "builder"
ROLE_AUDITOR = "auditor"
ROLE_SCOUT = "scout"
MODEL_OPUS = "opus"
MODEL_SONNET = "sonnet"
SPAWNER_LEAD = "comms-c1-lead"

_TIMESTAMP_TOLERANCE = timedelta(seconds=10)


def _agent_id(session: str, name: str) -> str:
    """The spec's pinned id recipe, computed independently of the ledger under
    test — a structural pin, not a shortcut that imports the ledger's own
    private helper.
    """
    return uuid5(NAMESPACE_URL, f"lore://agent/{session}/{name}").hex


def _assert_recent_utc(stamp: datetime, *, not_before: datetime, not_after: datetime) -> None:
    assert stamp.tzinfo is not None, "timestamp must be timezone-aware (fleet-comparable), not naive"
    assert not_before - _TIMESTAMP_TOLERANCE <= stamp <= not_after + _TIMESTAMP_TOLERANCE


# A factory that builds one more ready ``AgentRegistry`` on the SAME database —
# the second live connection the resolution/fleet-visibility pins need.
AgentRegistryFactory = Callable[[], Awaitable[AgentRegistry]]


@pytest_asyncio.fixture(params=["real", "fake"])
async def agent_registry_factory(request: pytest.FixtureRequest) -> AsyncIterator[AgentRegistryFactory]:
    """A factory yielding independent ready registries on the SAME per-test
    backing store — parametrized over BOTH the real SurrealDB-backed
    ``AgentRegistry`` and the adversarial ``FakeAgentRegistry``. Clones
    ``task_ledger_factory``'s shape (see that fixture's docstring for the
    pytest-asyncio 1.4 ``Runner``-reentrancy rationale for NOT depending on
    ``surreal_env``).
    """
    created: list[AgentRegistry] = []

    if request.param == "real":
        env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()

        async def make() -> AgentRegistry:
            registry = AgentRegistry(
                url=env.url,
                namespace=env.namespace,
                database=env.database,
                user=env.user,
                password=env.password,
            )
            await registry.ensure_ready()
            created.append(registry)
            return registry
    else:
        shared_db = FakeAgentDatabase()

        async def make() -> AgentRegistry:
            fake_registry = FakeAgentRegistry(db=shared_db)
            await fake_registry.ensure_ready()
            typed_registry = cast(AgentRegistry, fake_registry)
            created.append(typed_registry)
            return typed_registry

    try:
        yield make
    finally:
        for registry in created:
            await registry.close()
        if request.param == "real":
            await drop_database(env)


@pytest_asyncio.fixture()
async def agent_registry(agent_registry_factory: AgentRegistryFactory) -> AgentRegistry:
    """A single ready registry on a fresh unique database (the common per-test case)."""
    return await agent_registry_factory()


class TestRegisterCreatesRow:
    """First register: id recipe, birth state, ``re_registered=False``."""

    async def test_id_matches_the_pinned_uuid5_recipe(self, agent_registry: AgentRegistry) -> None:
        result = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        assert result.agent.id == _agent_id(SESSION_WAVE7, AGENT_FIXER_B)

    async def test_birth_state_is_active_and_unretired(self, agent_registry: AgentRegistry) -> None:
        before = datetime.now(UTC)
        result = await agent_registry.register(
            AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER, model=MODEL_OPUS, spawned_by=SPAWNER_LEAD
        )
        after = datetime.now(UTC)
        agent = result.agent
        assert result.re_registered is False
        assert agent.name == AGENT_FIXER_B
        assert agent.session == SESSION_WAVE7
        assert agent.role == ROLE_BUILDER
        assert agent.model == MODEL_OPUS
        assert agent.spawned_by == SPAWNER_LEAD
        assert agent.status == STATUS_ACTIVE
        assert agent.task_id is None
        assert agent.checkpoint is None
        assert agent.last_note is None
        _assert_recent_utc(agent.registered_at, not_before=before, not_after=after)
        _assert_recent_utc(agent.heartbeat_at, not_before=before, not_after=after)

    async def test_optional_fields_default_to_none_when_omitted(self, agent_registry: AgentRegistry) -> None:
        result = await agent_registry.register(AGENT_SCOUT_D, session=SESSION_WAVE7, role=ROLE_SCOUT)
        agent = result.agent
        assert agent.model is None
        assert agent.spawned_by is None
        assert agent.task_id is None

    async def test_same_name_in_two_sessions_are_two_distinct_rows(
        self, agent_registry: AgentRegistry
    ) -> None:
        first = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        second = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE8, role=ROLE_BUILDER)
        assert first.agent.id != second.agent.id
        assert first.re_registered is False
        assert second.re_registered is False


class TestReRegisterIdempotence:
    """§2: idempotent re-register on the SAME (session, name) — same id,
    ``registered_at`` write-once, ``heartbeat_at`` advances.
    """

    async def test_re_register_reuses_the_same_id(self, agent_registry: AgentRegistry) -> None:
        first = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        second = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        assert second.agent.id == first.agent.id
        assert second.re_registered is True

    async def test_registered_at_is_write_once(self, agent_registry: AgentRegistry) -> None:
        first = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await asyncio.sleep(0.01)
        second = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        assert second.agent.registered_at == first.agent.registered_at

    async def test_heartbeat_at_advances_on_re_register(self, agent_registry: AgentRegistry) -> None:
        first = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await asyncio.sleep(0.01)
        second = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        assert second.agent.heartbeat_at > first.agent.heartbeat_at

    async def test_re_register_with_the_same_role_is_not_a_conflict(
        self, agent_registry: AgentRegistry
    ) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        second = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        assert second.agent.role == ROLE_BUILDER


class TestReRegisterMutableFields:
    """§2: ``model``/``task_id`` overwritten when provided, kept when omitted."""

    async def test_model_overwritten_when_provided(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(
            AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER, model=MODEL_OPUS
        )
        second = await agent_registry.register(
            AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER, model=MODEL_SONNET
        )
        assert second.agent.model == MODEL_SONNET

    async def test_model_kept_when_omitted(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(
            AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER, model=MODEL_OPUS
        )
        second = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        assert second.agent.model == MODEL_OPUS

    async def test_task_id_overwritten_when_provided(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(
            AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER, task_id="task-1"
        )
        second = await agent_registry.register(
            AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER, task_id="task-2"
        )
        assert second.agent.task_id == "task-2"

    async def test_task_id_kept_when_omitted(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(
            AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER, task_id="task-1"
        )
        second = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        assert second.agent.task_id == "task-1"


class TestReRegisterWriteOnceConflict:
    """§2: a role/spawned_by mismatch on re-register is a TEACHING
    ``AgentIdentityConflictError`` — the name-reuse tripwire.
    """

    async def test_differing_role_raises_identity_conflict(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        with pytest.raises(AgentIdentityConflictError) as exc_info:
            await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_AUDITOR)
        message = str(exc_info.value)
        assert AGENT_FIXER_B in message
        assert ROLE_BUILDER in message
        assert ROLE_AUDITOR in message

    async def test_role_conflict_leaves_the_row_untouched(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        with pytest.raises(AgentIdentityConflictError):
            await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_AUDITOR)
        persisted = await agent_registry.get_agent(AGENT_FIXER_B, session=SESSION_WAVE7)
        assert persisted.role == ROLE_BUILDER

    async def test_differing_spawned_by_raises_identity_conflict(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(
            AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER, spawned_by="lead-a"
        )
        with pytest.raises(AgentIdentityConflictError):
            await agent_registry.register(
                AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER, spawned_by="lead-b"
            )

    async def test_a_first_time_spawned_by_fills_in_without_conflict(
        self, agent_registry: AgentRegistry
    ) -> None:
        """Contract decision (see report): write-once is compared only when BOTH
        sides carry a concrete value; a bootstrap register with no ``spawned_by``
        followed by a re-register that supplies one FILLS it in rather than
        conflicting (there is no prior value to disagree with).
        """
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        second = await agent_registry.register(
            AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER, spawned_by=SPAWNER_LEAD
        )
        assert second.agent.spawned_by == SPAWNER_LEAD


class TestReRegisterStatusReset:
    """§2: status resets to ``active`` unconditionally on a successful re-register."""

    async def test_idle_agent_resets_to_active_on_re_register(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_IDLE)
        second = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        assert second.agent.status == STATUS_ACTIVE

    async def test_input_required_agent_resets_to_active_on_re_register(
        self, agent_registry: AgentRegistry
    ) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_INPUT_REQUIRED)
        second = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        assert second.agent.status == STATUS_ACTIVE


class TestReRegisterFromRetiredIsTerminal:
    """§2/§3: re-registering an ALREADY-retired name is a teaching ``RetiredAgentError``."""

    async def test_register_after_retire_raises_retired_agent_error(
        self, agent_registry: AgentRegistry
    ) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_RETIRED)
        with pytest.raises(RetiredAgentError) as exc_info:
            await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        assert AGENT_FIXER_B in str(exc_info.value)

    async def test_retired_row_is_untouched_by_the_refused_register(
        self, agent_registry: AgentRegistry
    ) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_RETIRED)
        with pytest.raises(RetiredAgentError):
            await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_AUDITOR)
        persisted = await agent_registry.get_agent(AGENT_FIXER_B, session=SESSION_WAVE7)
        assert persisted.status == STATUS_RETIRED
        assert persisted.role == ROLE_BUILDER


class TestBareNameResolution:
    """§0.3: optional ``session=``; 0 matches -> unknown; >1 -> ambiguous naming
    the candidate sessions; retired rows excluded from bare-name search.
    """

    async def test_unknown_name_raises_unknown_agent_error(self, agent_registry: AgentRegistry) -> None:
        with pytest.raises(UnknownAgentError) as exc_info:
            await agent_registry.get_agent(AGENT_FIXER_B)
        assert AGENT_FIXER_B in str(exc_info.value)

    async def test_unique_name_resolves_without_session(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        resolved = await agent_registry.get_agent(AGENT_FIXER_B)
        assert resolved.session == SESSION_WAVE7

    async def test_same_name_in_two_sessions_is_ambiguous(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE8, role=ROLE_BUILDER)
        with pytest.raises(AmbiguousAgentError) as exc_info:
            await agent_registry.get_agent(AGENT_FIXER_B)
        message = str(exc_info.value)
        assert SESSION_WAVE7 in message
        assert SESSION_WAVE8 in message

    async def test_session_qualified_lookup_disambiguates(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(
            AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER, model=MODEL_OPUS
        )
        await agent_registry.register(
            AGENT_FIXER_B, session=SESSION_WAVE8, role=ROLE_BUILDER, model=MODEL_SONNET
        )
        resolved = await agent_registry.get_agent(AGENT_FIXER_B, session=SESSION_WAVE7)
        assert resolved.model == MODEL_OPUS

    async def test_retired_only_name_is_unknown_not_retired(self, agent_registry: AgentRegistry) -> None:
        """A name whose ONLY row is retired is invisible to bare-name search — the
        caller sees ``UnknownAgentError``, not ``RetiredAgentError`` (§0.3).
        """
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_RETIRED)
        with pytest.raises(UnknownAgentError):
            await agent_registry.get_agent(AGENT_FIXER_B)

    async def test_session_qualified_lookup_still_finds_a_retired_row(
        self, agent_registry: AgentRegistry
    ) -> None:
        """Direct id lookup (session given) DOES resolve a retired row — so the
        downstream retired-terminal check can fire with a teaching error rather
        than a confusing "unknown agent".
        """
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_RETIRED)
        with pytest.raises(RetiredAgentError):
            await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, note="still dead")

    async def test_never_minted_name_and_session_is_unknown(self, agent_registry: AgentRegistry) -> None:
        with pytest.raises(UnknownAgentError):
            await agent_registry.get_agent(AGENT_FIXER_B, session=SESSION_WAVE7)


class TestStatusStateMachineLegalEdges:
    """§3: every LEGAL_AGENT_TRANSITIONS edge succeeds, landing exactly on target."""

    @pytest.mark.parametrize(("from_status", "to_status"), sorted(LEGAL_AGENT_TRANSITIONS))
    async def test_legal_edge_succeeds(
        self, agent_registry: AgentRegistry, from_status: str, to_status: str
    ) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        if from_status != STATUS_ACTIVE:
            await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=from_status)
        updated = await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=to_status)
        assert updated.status == to_status


class TestStatusStateMachineIllegalEdges:
    """§3: illegal edges raise a teaching ``IllegalAgentStatusError``; the row is untouched."""

    async def test_input_required_to_idle_is_illegal(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_INPUT_REQUIRED)
        with pytest.raises(IllegalAgentStatusError) as exc_info:
            await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_IDLE)
        message = str(exc_info.value)
        assert STATUS_INPUT_REQUIRED in message
        assert STATUS_IDLE in message

    async def test_illegal_edge_leaves_status_untouched(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_INPUT_REQUIRED)
        with pytest.raises(IllegalAgentStatusError):
            await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_IDLE)
        persisted = await agent_registry.get_agent(AGENT_FIXER_B, session=SESSION_WAVE7)
        assert persisted.status == STATUS_INPUT_REQUIRED

    async def test_status_orphaned_is_never_a_legal_write(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        with pytest.raises(IllegalAgentStatusError) as exc_info:
            await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status="orphaned")
        message = str(exc_info.value)
        assert "derived" in message.lower()
        assert "heartbeat" in message.lower()

    async def test_orphaned_write_attempt_leaves_the_row_active(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        with pytest.raises(IllegalAgentStatusError):
            await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status="orphaned")
        persisted = await agent_registry.get_agent(AGENT_FIXER_B, session=SESSION_WAVE7)
        assert persisted.status == STATUS_ACTIVE

    async def test_garbage_status_value_is_illegal(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        with pytest.raises(IllegalAgentStatusError):
            await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status="on-fire")


class TestSelfEdgeNoOp:
    """§3: a self-edge (explicit status == current) is a legal no-op — idempotent
    heartbeats must never error.
    """

    @pytest.mark.parametrize(
        "status",
        [STATUS_ACTIVE, STATUS_IDLE, STATUS_INPUT_REQUIRED],
        ids=["active", "idle", "input_required"],
    )
    async def test_self_edge_succeeds_and_advances_heartbeat(
        self, agent_registry: AgentRegistry, status: str
    ) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        if status != STATUS_ACTIVE:
            await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=status)
        before = await agent_registry.get_agent(AGENT_FIXER_B, session=SESSION_WAVE7)
        await asyncio.sleep(0.01)
        after = await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=status)
        assert after.status == status
        assert after.heartbeat_at > before.heartbeat_at


class TestIdleAutoFlip:
    """§3: any comms action by an idle agent flips it active, UNLESS the call
    carries an explicit status; input_required NEVER auto-flips in C1.
    """

    async def test_idle_agent_auto_flips_to_active_with_no_explicit_status(
        self, agent_registry: AgentRegistry
    ) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_IDLE)
        touched = await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7)
        assert touched.status == STATUS_ACTIVE

    async def test_input_required_agent_does_not_auto_flip(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_INPUT_REQUIRED)
        touched = await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7)
        assert touched.status == STATUS_INPUT_REQUIRED

    async def test_active_agent_stays_active_with_no_explicit_status(
        self, agent_registry: AgentRegistry
    ) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        touched = await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7)
        assert touched.status == STATUS_ACTIVE

    async def test_explicit_status_wins_over_auto_flip(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_IDLE)
        touched = await agent_registry.touch(
            AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_INPUT_REQUIRED
        )
        assert touched.status == STATUS_INPUT_REQUIRED


class TestRetiredIsTerminalForEveryAction:
    """§3: any action where the resolved agent is retired raises ``RetiredAgentError``."""

    async def test_touch_on_a_retired_agent_raises(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_RETIRED)
        with pytest.raises(RetiredAgentError):
            await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7)

    async def test_retired_to_retired_self_edge_still_raises(self, agent_registry: AgentRegistry) -> None:
        """Retired is terminal even for a nominal self-edge — the retired check
        fires before any transition/no-op logic runs.
        """
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_RETIRED)
        with pytest.raises(RetiredAgentError):
            await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_RETIRED)


class TestHeartbeatNote:
    """``note`` overwrites ``last_note`` when given; omission preserves the prior value."""

    async def test_note_overwrites_last_note(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        touched = await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, note="blocked on review")
        assert touched.last_note == "blocked on review"

    async def test_omitted_note_preserves_the_prior_value(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, note="blocked on review")
        touched = await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7)
        assert touched.last_note == "blocked on review"

    async def test_hostile_note_round_trips_verbatim_never_sanitised_in_storage(
        self, agent_registry: AgentRegistry
    ) -> None:
        """Storage models are RAW ``str`` — sanitisation is render-time line
        policy, never storage mutation (spec §0). A hostile note (newlines + a
        row-shaped forgery line + backtick runs) must round-trip byte-identical.
        """
        hostile = f"first line\nsecond line\n{_ROW_FORGE_PAYLOAD}\n``` fence-shaped ```"
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        touched = await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, note=hostile)
        assert touched.last_note == hostile
        persisted = await agent_registry.get_agent(AGENT_FIXER_B, session=SESSION_WAVE7)
        assert persisted.last_note == hostile


class TestFleetOrdering:
    """§6: input_required rows first, then active, then idle; most-recent
    heartbeat first within a group; retired rows excluded from ``rows`` but
    counted in ``retired_count``.
    """

    async def test_status_group_ordering(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_AUDIT_C, session=SESSION_WAVE7, role=ROLE_AUDITOR)
        await agent_registry.register(AGENT_SCOUT_D, session=SESSION_WAVE7, role=ROLE_SCOUT)
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.touch(AGENT_SCOUT_D, session=SESSION_WAVE7, status=STATUS_IDLE)
        await agent_registry.touch(AGENT_FIXER_B, session=SESSION_WAVE7, status=STATUS_INPUT_REQUIRED)

        window = await agent_registry.fleet(session=SESSION_WAVE7, limit=10)
        names = [agent.name for agent in window.rows]
        assert names == [AGENT_FIXER_B, AGENT_AUDIT_C, AGENT_SCOUT_D]

    async def test_most_recent_heartbeat_first_within_a_group(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_AUDIT_C, session=SESSION_WAVE7, role=ROLE_AUDITOR)
        await asyncio.sleep(0.01)
        await agent_registry.register(AGENT_SCOUT_D, session=SESSION_WAVE7, role=ROLE_SCOUT)
        # Both active — freshest heartbeat (scout-d, registered second) sorts first.
        window = await agent_registry.fleet(session=SESSION_WAVE7, limit=10)
        names = [agent.name for agent in window.rows]
        assert names == [AGENT_SCOUT_D, AGENT_AUDIT_C]

    async def test_retired_rows_are_excluded_from_rows_but_counted(
        self, agent_registry: AgentRegistry
    ) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.register(AGENT_AUDIT_C, session=SESSION_WAVE7, role=ROLE_AUDITOR)
        await agent_registry.touch(AGENT_AUDIT_C, session=SESSION_WAVE7, status=STATUS_RETIRED)

        window = await agent_registry.fleet(session=SESSION_WAVE7, limit=10)
        names = [agent.name for agent in window.rows]
        assert AGENT_AUDIT_C not in names
        assert window.retired_count == 1
        assert window.total_non_retired == 1


class TestFleetSessionScoping:
    async def test_session_filter_excludes_other_sessions(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.register(AGENT_AUDIT_C, session=SESSION_WAVE8, role=ROLE_AUDITOR)
        window = await agent_registry.fleet(session=SESSION_WAVE7, limit=10)
        names = [agent.name for agent in window.rows]
        assert names == [AGENT_FIXER_B]

    async def test_omitted_session_spans_every_session(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.register(AGENT_AUDIT_C, session=SESSION_WAVE8, role=ROLE_AUDITOR)
        window = await agent_registry.fleet(limit=10)
        names = {agent.name for agent in window.rows}
        assert names == {AGENT_FIXER_B, AGENT_AUDIT_C}


class TestFleetLimitAndTotal:
    async def test_limit_truncates_rows_but_total_stays_honest(self, agent_registry: AgentRegistry) -> None:
        for suffix in range(5):
            await agent_registry.register(f"builder-{suffix}", session=SESSION_WAVE7, role=ROLE_BUILDER)
        window = await agent_registry.fleet(session=SESSION_WAVE7, limit=2)
        assert len(window.rows) == 2
        assert window.total_non_retired == 5


class TestFleetEmpty:
    async def test_empty_fleet_is_an_honest_empty_not_an_error(self, agent_registry: AgentRegistry) -> None:
        window = await agent_registry.fleet(session=SESSION_WAVE7, limit=10)
        assert window.rows == []
        assert window.retired_count == 0
        assert window.total_non_retired == 0


class TestRosterTrueCounts:
    """v4 audit D1 fix (docs/design/2026-07-12-pkt28-c1-semantics.md §5.3/§6,
    CHANGELOG v4): ``AgentRegistry.roster()`` -- a NEW, explicitly
    row-UNLIMITED projection -- whose ``status_counts`` are a TRUE aggregate
    (incl. ``retired``) and whose ``members`` are the COMPLETE non-retired
    membership in scope, never a display-capped window (the bug the cold
    audit reproduced: ``fleet``'s per-status header segments were counted
    over the ``_MAX_FLEET_LIMIT``-capped rows while the header total was
    already true, so the two disagreed past 200 agents).

    Real store, MODEST scale only (see REPORT-c1-contract-d1d2-b.md's
    live-vs-synthetic split): a >200-agent live fixture is slow and adds
    nothing this method's OWN plumbing needs proven at small N -- the
    over-cap ARITHMETIC (header self-consistency, the cap-disclosure
    elision variant, coverage/skew over the whole roster) is pinned with a
    synthetic ``FleetRoster``/spy fixture in test_comms_tool.py instead.
    """

    async def test_status_counts_is_a_true_aggregate_including_retired(
        self, agent_registry: AgentRegistry
    ) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.register(AGENT_AUDIT_C, session=SESSION_WAVE7, role=ROLE_AUDITOR)
        await agent_registry.register(AGENT_SCOUT_D, session=SESSION_WAVE7, role=ROLE_SCOUT)
        await agent_registry.touch(AGENT_SCOUT_D, session=SESSION_WAVE7, status=STATUS_IDLE)
        await agent_registry.touch(AGENT_AUDIT_C, session=SESSION_WAVE7, status=STATUS_RETIRED)

        roster = await agent_registry.roster(session=SESSION_WAVE7)

        assert roster.status_counts["active"] == 1
        assert roster.status_counts["idle"] == 1
        assert roster.status_counts["input_required"] == 0
        assert roster.status_counts["retired"] == 1

    async def test_members_are_the_complete_non_retired_membership(
        self, agent_registry: AgentRegistry
    ) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.register(AGENT_AUDIT_C, session=SESSION_WAVE7, role=ROLE_AUDITOR)
        await agent_registry.touch(AGENT_AUDIT_C, session=SESSION_WAVE7, status=STATUS_RETIRED)

        roster = await agent_registry.roster(session=SESSION_WAVE7)

        member_names = {member.name for member in roster.members}
        assert member_names == {AGENT_FIXER_B}
        assert AGENT_AUDIT_C not in member_names

    async def test_omitted_session_spans_every_session(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
        await agent_registry.register(AGENT_AUDIT_C, session=SESSION_WAVE8, role=ROLE_AUDITOR)

        roster = await agent_registry.roster()

        member_names = {member.name for member in roster.members}
        assert member_names == {AGENT_FIXER_B, AGENT_AUDIT_C}

    async def test_member_fields_match_the_underlying_agent_row(
        self, agent_registry: AgentRegistry
    ) -> None:
        result = await agent_registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)

        roster = await agent_registry.roster(session=SESSION_WAVE7)

        [member] = roster.members
        assert member.id == result.agent.id
        assert member.name == AGENT_FIXER_B
        assert member.status == STATUS_ACTIVE
        assert member.heartbeat_at == result.agent.heartbeat_at


class TestRosterCompletenessBeyondTheDisplayCap:
    """F2 (REPORT-c1-audit-fixwave.md, BLOCKER): ``roster().members``' row-
    UNLIMITED completeness -- the entire basis of the D1 fix's coverage/skew
    denominators -- had NO covering test. The audit proved capping
    ``members`` at ``_MAX_FLEET_LIMIT`` (in the real registry OR the fake)
    left the WHOLE SUITE GREEN (the pass COUNT it reported is struck: the suite
    has since changed shape and no in-tree instrument reproduces it): a future
    edit that silently re-adds a cap here -- exactly the shape of the defect D1 fixed --
    regresses ``brief_get`` coverage and ``brief_publish`` skew back to D1
    with every gate staying green. This pin closes that gap directly: at
    N > ``_MAX_FLEET_LIMIT`` non-retired agents, ``members`` must still be
    the COMPLETE membership, not a display-capped window.

    This pin is expected GREEN against today's (already-correct) ``roster()``.
    A mutation receipt proving it goes RED the moment ``members`` is capped
    (real registry AND fake alike) was recorded at authoring time, but its
    report was deleted per repo law and never archived -- NOTE: the receipt is
    therefore UNVERIFIED today, and by this docstring's own standard ("a pin
    that cannot be shown failing is not a pin") it is owed a re-run rather than
    trusted.

    Cost (real store, spike-surreal): 205 sequential ``register()`` calls
    per parametrization; the wall time once cited here is struck -- it was
    never stated in-tree and its report is gone.
    """

    async def test_members_length_exceeds_the_display_cap_at_true_scale(
        self, agent_registry: AgentRegistry
    ) -> None:
        total_agents = _MAX_FLEET_LIMIT + 5
        for index in range(total_agents):
            await agent_registry.register(f"agent-{index:03d}", session=SESSION_WAVE7, role=ROLE_BUILDER)

        roster = await agent_registry.roster(session=SESSION_WAVE7)

        assert len(roster.members) == total_agents, (
            f"roster().members must be the COMPLETE non-retired membership "
            f"({total_agents}), never a display-capped window "
            f"({_MAX_FLEET_LIMIT}) -- got {len(roster.members)}"
        )
        assert len(roster.members) > _MAX_FLEET_LIMIT


class TestRosterIsRowUnlimited:
    """Structural pin (spec §5.3 v4: 'a NEW, explicitly row-UNLIMITED read'):
    ``roster()`` takes no ``limit`` parameter at all -- a regression that
    re-adds one would silently reintroduce the exact cap-vs-truth confusion
    this method exists to close.
    """

    def test_roster_signature_has_no_limit_parameter(self) -> None:
        parameters = inspect.signature(AgentRegistry.roster).parameters
        assert "limit" not in parameters
        assert "session" in parameters


class TestFleetRosterModelShape:
    """Structural pins on the two NEW value objects (mirrors
    ``TestNoForwardCompatFieldsOnAgent`` below): ``FleetRoster.members`` carry
    no render-only fields (id/name/status/heartbeat_at only, spec §5.3)."""

    def test_fleet_roster_field_set(self) -> None:
        assert set(FleetRoster.model_fields) == {"members", "status_counts"}

    def test_fleet_roster_forbids_unknown_fields(self) -> None:
        assert FleetRoster.model_config.get("extra") == "forbid"

    def test_agent_roster_member_field_set(self) -> None:
        assert set(AgentRosterMember.model_fields) == {"id", "name", "status", "heartbeat_at"}

    def test_agent_roster_member_forbids_unknown_fields(self) -> None:
        assert AgentRosterMember.model_config.get("extra") == "forbid"


class TestNoForwardCompatFieldsOnAgent:
    """Structural pin: the ``Agent`` model's field set is EXACTLY the C1 §0
    schema slice — no unread/unacked/orphan-impact fields have crept in (D1/D2:
    those tables do not exist in C1).
    """

    def test_agent_field_set_is_exactly_the_c1_slice(self) -> None:
        expected = {
            "id",
            "name",
            "session",
            "role",
            "model",
            "status",
            "spawned_by",
            "task_id",
            "checkpoint",
            "last_note",
            "registered_at",
            "heartbeat_at",
            # #304 (packet 05a-iii): the aged-declaration stamp — a DELIBERATE
            # addition to the agent surface (verified present on the Agent model),
            # NOT a forward-compat unread/unacked/orphan-impact creep. Kept in this
            # exact-set pin so any FURTHER field still reddens here.
            "status_set_at",
            # W1 (packet 06a, #360): the agent's self-declared comms cadence — a
            # DELIBERATE addition (register/heartbeat `cadence` param, stored verbatim
            # on the Agent model, drives the fleet `overdue` verdict). NOT a
            # forward-compat creep. Kept in this exact-set pin so any FURTHER field
            # still reddens here.
            "declared_cadence",
        }
        assert set(Agent.model_fields) == expected

    def test_agent_model_forbids_unknown_fields(self) -> None:
        assert Agent.model_config.get("extra") == "forbid"


class TestAgentNamePatternConstant:
    """§0/§4: ``AGENT_NAME_PATTERN`` lives in ``agents.py`` — the load-bearing
    injection guard S3's dispatcher pre-validates every ``agent``/``session``/
    ``name`` argument against, before any store touch.
    """

    def test_pattern_matches_the_pinned_charset(self) -> None:
        assert AGENT_NAME_PATTERN.pattern == r"^[a-z0-9][a-z0-9_-]{0,63}$"

    @pytest.mark.parametrize("value", ["fixer-b", "audit-c2", "a", "wave7", "scout_d"])
    def test_pattern_accepts_legal_names(self, value: str) -> None:
        assert AGENT_NAME_PATTERN.fullmatch(value) is not None

    @pytest.mark.parametrize(
        "value",
        ["Fixer-B!", "-leading-hyphen", "", "has space", "a" * 65, "scout\n", "scout\r\n"],
    )
    def test_pattern_rejects_illegal_names(self, value: str) -> None:
        assert AGENT_NAME_PATTERN.fullmatch(value) is None

    def test_the_end_anchor_is_lenient_about_a_trailing_newline(self) -> None:
        """KNOWN BOUND (#210) — the reason every call site must use ``fullmatch``.

        Python's ``$`` matches at end-of-string OR immediately before a trailing
        newline, so this pattern ALONE does not close the charset: ``.match``
        accepts ``"scout\\n"``, a second identity that renders identically to
        ``"scout"`` wherever a trailing newline is invisible. That is not a
        latent hazard to fix HERE — it is the documented property the guard
        compensates for by calling ``fullmatch``
        (:meth:`AppContext._validate_comms_charset`), pinned behaviourally in
        ``test_comms_tool.py::TestCommsDispatchCharsetValidation::
        test_a_trailing_newline_agent_name_is_rejected``. The repo-wide class
        instrument is ``test_anchored_pattern_seam.py``.

        If you change the pattern's anchor (``\\Z`` instead of ``$``) this test
        goes RED. That is correct and deliberate: the ``fullmatch`` call site
        would then be belt-and-braces rather than load-bearing, so update this
        pin and say so — do not silently delete it.
        """
        assert AGENT_NAME_PATTERN.match("scout\n") is not None
        assert AGENT_NAME_PATTERN.fullmatch("scout\n") is None
        # ``$``'s leniency covers ``\n`` ONLY — a CRLF name was never accepted.
        assert AGENT_NAME_PATTERN.match("scout\r\n") is None


class TestAgentStatusesConstant:
    def test_agent_statuses_is_the_closed_four_value_domain(self) -> None:
        assert AGENT_STATUSES == frozenset(
            {STATUS_ACTIVE, STATUS_IDLE, STATUS_INPUT_REQUIRED, STATUS_RETIRED}
        )


# ---------------------------------------------------------------------------
# Connection lifecycle (global CLAUDE.md law: degradation -> recovery over a
# dropped-and-recovered store connection). Real-only — mirrors
# ``TestQueryClassifiedErrorPosture`` in test_task_ledger.py.
# ---------------------------------------------------------------------------

_AGENT_SENSITIVE_ENGINE_TEXT = "Found NONE for field `role`, with record `agent:poisonvalue`"
_AGENT_SENSITIVE_MARKER = "poisonvalue"
_AGENT_TRANSPORT_ENGINE_TEXT = "There was a problem with the database: Not allowed to do this"


class _RejectingConnection:
    """A fake SDK connection whose ``query`` raises a scripted error — clones
    ``test_task_ledger.py``'s ``_RejectingConnection`` fault-injector.
    """

    def __init__(self, error: BaseException) -> None:
        self.error = error

    async def query(self, statement: str, params: dict[str, Any]) -> Any:
        raise self.error

    async def close(self) -> None:
        return None


class TestAgentRegistryConnectionLifecycle:
    @staticmethod
    def _bare_registry() -> AgentRegistry:
        return AgentRegistry(
            url="ws://127.0.0.1:19556/rpc",  # never dialed — the fake handle short-circuits
            namespace="ns",
            database="db",
            user="root",
            password=SecretStr("root"),
        )

    async def test_domain_rejection_never_echoes_the_raw_engine_text(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        registry = self._bare_registry()
        registry._connection = cast(
            "_SurrealConnection",
            _RejectingConnection(ServerError(ErrorKind.INTERNAL, _AGENT_SENSITIVE_ENGINE_TEXT)),
        )
        connection_before = registry._connection
        with caplog.at_level(logging.ERROR, logger="loremaster.agents"):
            with pytest.raises(SurrealStoreError) as exc_info:
                await registry._query("UPDATE agent SET role = $r", {"r": "poison"})
        message = str(exc_info.value)
        assert_domain_rejection(exc_info.value)
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert registry._connection is connection_before
        assert _AGENT_SENSITIVE_ENGINE_TEXT not in message
        assert _AGENT_SENSITIVE_MARKER not in message
        assert "server log" in message.lower()

    async def test_transport_failure_drops_the_handle_and_raises_connection_error(self) -> None:
        registry = self._bare_registry()
        registry._connection = cast(
            "_SurrealConnection",
            _RejectingConnection(ServerError(ErrorKind.NOT_ALLOWED, _AGENT_TRANSPORT_ENGINE_TEXT)),
        )
        with pytest.raises(SurrealConnectionError):
            await registry._query("SELECT * FROM agent", {})
        assert registry._connection is None

    async def test_recovers_on_the_next_call_after_a_dropped_connection(self) -> None:
        """Recovery: after the cached handle is dropped, the NEXT call reconnects
        and succeeds — the ledger is never permanently wedged by a transient loss.
        Real-only (a fake holds no connection to drop).
        """
        env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()
        registry = AgentRegistry(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        try:
            await registry.ensure_ready()
            await registry.register(AGENT_FIXER_B, session=SESSION_WAVE7, role=ROLE_BUILDER)
            registry._connection = None  # simulate a dropped connection
            recovered = await registry.get_agent(AGENT_FIXER_B, session=SESSION_WAVE7)
            assert recovered.name == AGENT_FIXER_B
        finally:
            await registry.close()
            await drop_database(env)


# =========================================================================== #
# 63c-i-a — Q3 DROP+MOVE (ruling §4.2 + amendment-2 A4): the agent name/session charset + role
# non-empty checks MOVE out of the store DDL ASSERT and INTO ``AgentRegistry.register``. The DECISION
# lives in ``lorerunes.is_legal_identifier`` (``fullmatch`` over ``AGENT_NAME_PATTERN``, which MOVES to
# ``lorerunes``; ``agents.py`` re-exports it) and ``lorerunes.is_blank`` — the register refusal is a
# TEACHING ``AgentRegistryError`` subclass (field · rule in prose · remedy · the value FENCED through
# the SAME ``render_fenced`` helper ``AppContext._validate_comms_charset`` uses, never ``repr``) raised
# BEFORE any store I/O. ``_IDENTIFIER_CHARSET_PATTERN`` (surreal_schema) is NOT deleted in i-a —
# ``brief.name`` consumes it until 63c-ii (F-regex-twin).
#
# RED before the i-a build (measured @699a6e9): at HEAD ``register`` performs NO charset/role check, so
# a hostile value reaches the store CREATE and the STILL-PRESENT store ASSERT rejects it with a
# ``TxnDomainRejectionError`` (a ``SurrealStoreError``, NOT an ``AgentRegistryError``) → these pins
# ERROR (RED). On the WRONG build (ASSERT dropped, MOVE forgotten) a hostile value is WRITTEN → RED.
#
# r2 (amendment-2 §D item 10 — MP-9 / A4 / sidecar F5 + F6): the hostile matrix is the SHARED
# ``test_comms_schema._HOSTILE_IDENTIFIERS`` (12 → 13 shapes incl. the trailing newline WB11 walked
# through; r1's local 7-shape hand-list is DELETED — one corpus); the refusal's TEACHING content is
# pinned (WB5); ``is_legal_identifier`` / ``is_blank`` / the moved pattern are each proven SHARED by
# mutation, per field (WB11 / WB13 / F6).
# =========================================================================== #

_MOVE_BLANK_ROLES = ("", " ", "\t", "\n")
_LEGAL_NAME = AGENT_FIXER_B  # "fixer-b"
_LEGAL_SESSION = SESSION_WAVE7  # "wave7" — a DIFFERENT value from the name (per-field mutation legs)
#: The consumer ENTRY POINTS of the ONE identifier decision (amendment-4 A4-bis — i-a's set): the registry
#: writer, the server's REFUSE policy, the server's decision HOME (``_is_comms_charset_legal``, which the
#: refuse policy AND the ``_comms_traffic_line`` SKIP policy both read) and the fake. ii adds
#: ``BriefLedger.publish``.
#: ⚠ REACH, STATED (amendment-6 STOP-rule §4): this is a HAND-LIST — the EFFECT twin, proving by
#: mutation that each LISTED entry point moves with the shared predicate. It cannot see a call site it
#: does not name (adversary-r3 X1: the SKIP gate deciding privately, one call site above the home). The
#: ∀ over the workspace is the static TEXT pin
#: ``TestTheIdentifierCharsetTextHasOneSpelling63cIA::
#: test_the_charset_text_occurs_ONLY_in_the_lorerunes_definition``; the SKIP gate's own call site has its
#: effect legs in ``TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA``.
_IDENTIFIER_DECISION_CONSUMERS = ("register", "refuse-policy", "skip-policy", "fake")
#: The consumers of the ONE blank-role decision (``lorerunes.is_blank``): the writer and — amendment-3
#: F-2's third consumer leg — the fake that substitutes it in every fake-driven test.
_BLANK_ROLE_DECISION_CONSUMERS = ("register", "fake")


class TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA:
    """63c-i-a §4.2 MOVE — ``AgentRegistry.register`` refuses a hostile identity / blank role with a
    TEACHING ``AgentRegistryError`` BEFORE any store I/O, through the SHARED ``lorerunes`` predicates.
    Fixtures DISCRIMINATE: a hostile value AND a valid control (a too-strict guard would refuse every
    real caller); name and session carry DIFFERENT legal values so a per-field mutation can tell them
    apart."""

    @staticmethod
    async def _real_registry() -> tuple[AgentRegistry, SurrealConnection, SurrealEnv]:
        env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()
        registry = AgentRegistry(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        await registry.ensure_ready()
        admin_connection = await connect_admin(env)
        return registry, admin_connection, env

    @staticmethod
    async def _agent_row_count(connection: SurrealConnection) -> int:
        rows = await run(connection, f"SELECT count() FROM {AGENT_TABLE} GROUP ALL")
        return int(rows[0]["count"]) if rows else 0

    @pytest.mark.parametrize("field", ["name", "session"])
    @pytest.mark.parametrize("hostile_value", _HOSTILE_IDENTIFIERS)
    async def test_register_refuses_a_hostile_identifier_before_any_store_write(
        self, field: str, hostile_value: str
    ) -> None:
        """⚠ RED before i-a — ``register`` REFUSES a hostile ``name``/``session`` from the SHARED corpus
        with a TEACHING ``AgentRegistryError``, writing ZERO rows. The refusal names (i) the FIELD, (ii)
        the RULE — ``AGENT_NAME_PATTERN.pattern`` itself, DERIVED so a pattern change moves the message
        with it, (iii) the REMEDY (register again), and (iv) echoes the offending VALUE through
        ``render_fenced`` — the helper ``_validate_comms_charset`` uses — never bare, never ``repr``
        (Ruling 10 link 4: ``repr`` escapes newlines and leaves a same-line forgery readable). WB5
        (``"invalid input"``) and WB11 (``.match`` accepts ``"fixer-b\\n"``) both red here."""
        registry, admin_connection, env = await self._real_registry()
        try:
            kwargs: dict[str, Any] = {"name": _LEGAL_NAME, "session": _LEGAL_SESSION, "role": ROLE_BUILDER}
            kwargs[field] = hostile_value
            with pytest.raises(AgentRegistryError) as exc_info:
                await registry.register(
                    kwargs["name"], session=kwargs["session"], role=kwargs["role"]
                )
            message = str(exc_info.value)
            assert "assert violation" not in message.lower(), (
                f"the refusal is a laundered store ASSERT, not a TEACHING register-layer error: {message!r}"
            )
            assert field in message, f"the refusal does not name the offending FIELD {field!r}: {message!r}"
            assert AGENT_NAME_PATTERN.pattern in message, (
                f"the refusal does not state the RULE (the charset pattern {AGENT_NAME_PATTERN.pattern!r}, "
                f"derived — never restated): {message!r}"
            )
            assert "register again" in message, f"the refusal does not teach the REMEDY: {message!r}"
            assert str(render_fenced(hostile_value)) in message, (
                f"the offending value must ride render_fenced (the SAME helper "
                f"_validate_comms_charset uses — Ruling 10 link 4), never bare or repr: {message!r}"
            )
            assert await self._agent_row_count(admin_connection) == 0, (
                f"a rejected register wrote an agent row — the {field} charset check must run BEFORE "
                f"any store I/O (#97 / §4.2: a rejected write has no side effect)"
            )
        finally:
            await admin_connection.close()
            await registry.close()
            await drop_database(env)

    @pytest.mark.parametrize("blank_role", _MOVE_BLANK_ROLES)
    async def test_register_refuses_a_blank_role_before_any_store_write(self, blank_role: str) -> None:
        """⚠ RED before i-a — ``register`` REFUSES a blank ``role`` via ``lorerunes.is_blank``, TEACHING
        (the field ``role``, the rule — non-blank — and the remedy), ZERO rows written. RED at HEAD
        (``role=""`` reaches the store non-empty ASSERT — a store error, not AgentRegistryError)."""
        registry, admin_connection, env = await self._real_registry()
        try:
            with pytest.raises(AgentRegistryError) as exc_info:
                await registry.register(_LEGAL_NAME, session=_LEGAL_SESSION, role=blank_role)
            message = str(exc_info.value)
            assert "assert violation" not in message.lower(), (
                f"a blank role must be refused APP-SIDE by is_blank, teaching — not laundered as the "
                f"store's `(assert violation)`: {message!r}"
            )
            assert "role" in message, f"the refusal does not name the FIELD 'role': {message!r}"
            assert "blank" in message, f"the refusal does not state the RULE (non-blank): {message!r}"
            assert "register again" in message, f"the refusal does not teach the REMEDY: {message!r}"
            assert await self._agent_row_count(admin_connection) == 0, (
                "a rejected (blank-role) register wrote an agent row — the role check must run BEFORE "
                "any store I/O (§4.2)"
            )
        finally:
            await admin_connection.close()
            await registry.close()
            await drop_database(env)

    # r4a (amendment-9 MP-R4-3): the r4 values are KEPT (additive — no param deleted, so no DUAL row) and the
    # SHARED legal corpus ``_LEGAL_IDENTIFIER_WITNESSES`` is appended, so a MOVE guard that narrows on any
    # axis a witness carries (length 1, digit-leading, ``_``, ``-``, the 64-char cap) refuses a legal caller.
    @pytest.mark.parametrize(
        "valid_value", list(dict.fromkeys(("fixer-b", "a", "wave7", "z" * 64, *_LEGAL_IDENTIFIER_WITNESSES)))
    )
    async def test_register_accepts_a_valid_identifier_positive_control(self, valid_value: str) -> None:
        """POSITIVE CONTROL (fixtures-must-discriminate) — a build whose MOVE charset guard is too
        strict would refuse every real caller while passing the negative pins. A valid name/session
        registers and writes exactly one row. GREEN at HEAD AND on the correct build. Parametrised over
        the SHARED legal corpus too (r4a, amendment-9 MP-R4-3) — never a narrower local copy."""
        registry, admin_connection, env = await self._real_registry()
        try:
            result = await registry.register(valid_value, session=valid_value, role=ROLE_BUILDER)
            assert result.re_registered is False
            assert await self._agent_row_count(admin_connection) == 1, (
                f"a valid register must write exactly one agent row (valid={valid_value!r})"
            )
        finally:
            await admin_connection.close()
            await registry.close()
            await drop_database(env)

    # DUAL (r3, amendment-4 A4-bis): the r2 pin (params [name]/[session], register + refuse-policy in ONE
    # body) is RE-KEYED to a consumer axis. Both r2 consumers keep their legs (register, refuse-policy);
    # the skip-policy HOME leg is NEW. The r2 `assert any(... startswith("lorerunes"))` non-vacuity check
    # moved INTO the instrument (``expect_in`` — the sweep raises if the home was not patched).
    @pytest.mark.parametrize("consumer", _IDENTIFIER_DECISION_CONSUMERS)
    @pytest.mark.parametrize("field", ["name", "session"])
    async def test_the_identifier_decision_is_the_SHARED_is_legal_identifier(
        self, monkeypatch: pytest.MonkeyPatch, field: str, consumer: str
    ) -> None:
        """⚠ RED before i-a (``lorerunes.is_legal_identifier`` does not exist). ONE DECISION, proven BY
        MUTATION (A4 → amendment-4 A4-bis; WB11 / N1 / N1c are the routing-not-sharing builds this
        kills): rebind EVERY module-level binding of THE shared predicate to one that rejects ONE
        normally-legal value — the target field's — and EVERY consumer of the decision must refuse it:

        * ``register`` — the i-a writer (``AgentRegistryError``, zero rows);
        * ``refuse-policy`` — ``AppContext._validate_comms_charset`` (the REFUSE policy, ``ValueError``);
        * ``fake`` — ``FakeAgentRegistry.register`` (amendment-3 F-2 rider 2, r3 item 8: the fake that
          substitutes the registry in fake-driven tests ROUTES to the same decision);
        * ``skip-policy`` — ``AppContext._is_comms_charset_legal``, the server's ONE decision HOME, which
          BOTH server policies read (``_validate_comms_charset`` refuses on it; ``_comms_traffic_line``'s
          SKIP gate skips on it). A4 named the refuse policy and missed the home, so the literal A4
          reading licensed N1 (the home keeps ``AGENT_NAME_PATTERN.fullmatch`` — two deciders) and N1c
          (the home is a private DRIFTED ``re.fullmatch`` that admits ``fixer.b`` TODAY); both survived
          r2 at 2521/0 (adversary-r2 MP-A). This leg reds both.

        Per FIELD, so a consumer that routes ``name`` through the predicate and ``session`` through a
        private check reds on the ``session`` leg (sidecar F6). BASELINE first for the server legs:
        unpatched, the target is legal (a consumer that refuses everything cannot pass by 'also
        refusing'); the register baseline is ``test_register_accepts_a_valid_identifier_positive_control``."""
        import lorerunes

        target = _LEGAL_NAME if field == "name" else _LEGAL_SESSION
        shared_predicate = lorerunes.is_legal_identifier
        if consumer != "register":  # BASELINE: legal today (register's is the positive-control pin)
            assert not await self._identifier_consumer_refuses(consumer, target, field), (
                f"BASELINE: {consumer} refused the LEGAL {field} {target!r} before any mutation"
            )
        patched = patch_shared_object_everywhere(
            monkeypatch,
            "is_legal_identifier",
            shared_predicate,
            lambda value: value != target and shared_predicate(value),
        )  # raises unless lorerunes.is_legal_identifier (the home) was among the patched bindings
        assert await self._identifier_consumer_refuses(consumer, target, field), identity_sweep_miss_message(
            f"the {consumer} consumer's {field} decision"
            + (
                " (the server's decision HOME, read by BOTH the refuse policy and the _comms_traffic_line "
                "SKIP policy — a second decider: A4-bis / N1 / N1c)"
                if consumer == "skip-policy"
                else ""
            ),
            patched,
        )

    async def _identifier_consumer_refuses(self, consumer: str, target: str, field: str) -> bool:
        """Whether ``consumer`` REFUSES the identity whose ``field`` is ``target`` — each consumer probed
        through its own surface, and a refusal that WROTE anyway is a failure, not a refusal."""
        if consumer in ("skip-policy", "refuse-policy"):
            return self._server_policy_refuses(consumer, target, field)
        name = target if field == "name" else _LEGAL_NAME
        session = target if field == "session" else _LEGAL_SESSION
        return await self._registry_refuses(consumer, name, session)

    @staticmethod
    def _server_policy_refuses(consumer: str, target: str, field: str) -> bool:
        from loremaster.server import AppContext

        if consumer == "skip-policy":
            return AppContext._is_comms_charset_legal(target) is False  # noqa: SLF001 - the decision HOME
        try:
            AppContext._validate_comms_charset(target, field)  # noqa: SLF001 - the REFUSE policy
        except ValueError:
            return True
        return False

    async def _registry_refuses(self, consumer: str, name: str, session: str) -> bool:
        if consumer == "fake":
            fake = FakeAgentRegistry()
            try:
                await fake.register(name, session=session, role=ROLE_BUILDER)
            except AgentRegistryError:
                assert fake.db.agents == {}, "a REFUSED fake register stored a row"
                return True
            return False
        registry, admin_connection, env = await self._real_registry()
        try:
            try:
                await registry.register(name, session=session, role=ROLE_BUILDER)
            except AgentRegistryError:
                assert await self._agent_row_count(admin_connection) == 0, "a REFUSED register wrote a row"
                return True
            return False
        finally:
            await admin_connection.close()
            await registry.close()
            await drop_database(env)

    @pytest.mark.parametrize("field", ["name", "session"])
    async def test_register_charset_check_reads_the_ONE_pattern_in_its_lorerunes_home(
        self, monkeypatch: pytest.MonkeyPatch, field: str
    ) -> None:
        """⚠ REGEX-TWIN mutation proof, RED before i-a — RETARGETED to the ``lorerunes`` home (A4: the
        r1 pin patched ``agents.AGENT_NAME_PATTERN``, which after the MOVE is a RE-EXPORT — patching it
        moves nothing, so that pin went RED on a correct build and GREEN only on a build that kept a
        private pattern). ``AGENT_NAME_PATTERN`` is ONE object: ``loremaster.agents`` re-exports the
        ``lorerunes`` one. Replace that object — in every module holding it — with a pattern that
        refuses exactly the target field's legal value; ``register`` must refuse it. Per field (F6).

        ⚠ KNOWN BOUND, PINNED AS PROSE (amendment-3 F-5; r2 mutation proof WB-A4b): CPython's
        ``re.compile`` returns the CACHED object for an identical (pattern text, flags) pair
        (``re._compile``'s bounded cache — CPython-specific), so a SOURCE-TEXT twin ``AGENT_NAME_PATTERN =
        re.compile(<same text>)`` in ``agents.py`` is object-identical to the ``lorerunes`` one at birth:
        the re-export identity assert and the mutation both pass. A runtime instrument cannot see source
        text. DIRECTION — MISS-only, never a false alarm: the moment the twin's text DRIFTS it is a
        distinct object and the identity assert reds (proven: a ``{0,64}`` copy reds both legs); a cache
        eviction between the two compiles would make even a same-text twin distinct → RED on a twin, also
        correct; a correct build holds ONE object by RE-EXPORT, not by cache, so this pin cannot flake on
        it. COVERAGE of the birth-twin: the builder's DRY row (A4 says ``agents.py`` RE-EXPORTS — a
        ``re.compile`` there is a second spelling by construction) and the cold audit's contract-blind
        diff read. RE-OPEN TRIGGER: this pin REDS and the fix turns out to be a source-text twin → close
        the bound with an AST scan over the production members (``parse_production_trees`` +
        ``assert_scan_reached_every_member``): ``re.compile`` calls whose first argument is a string
        constant equal to ``AGENT_NAME_PATTERN.pattern`` → exactly one site, in ``lorerunes``."""
        import re

        import lorerunes
        from loremaster import agents as agents_module

        assert agents_module.AGENT_NAME_PATTERN is lorerunes.AGENT_NAME_PATTERN, (
            "loremaster.agents.AGENT_NAME_PATTERN is not the lorerunes object — the pattern did not MOVE "
            "(A4: agents.py re-exports it; a second compiled copy is a second spelling)"
        )
        target = _LEGAL_NAME if field == "name" else _LEGAL_SESSION
        narrowed = re.compile(rf"^(?!{re.escape(target)}$)[a-z0-9][a-z0-9_-]{{0,63}}$")
        registry, admin_connection, env = await self._real_registry()
        try:
            patched = patch_shared_object_everywhere(
                monkeypatch, "AGENT_NAME_PATTERN", lorerunes.AGENT_NAME_PATTERN, narrowed
            )  # raises unless lorerunes.AGENT_NAME_PATTERN (the home) was among the patched bindings
            try:
                await registry.register(_LEGAL_NAME, session=_LEGAL_SESSION, role=ROLE_BUILDER)
            except AgentRegistryError:
                pass
            else:
                pytest.fail(identity_sweep_miss_message(f"register's {field} charset pattern", patched))
            assert await self._agent_row_count(admin_connection) == 0
        finally:
            await admin_connection.close()
            await registry.close()
            await drop_database(env)

    # DUAL (r3, item 8 — amendment-3 F-2 rider 2): the r2 pin (register only) is RE-KEYED to a consumer
    # axis; its register leg is unchanged, the FAKE leg is new (GREEN at HEAD — ``is_blank`` exists).
    @pytest.mark.parametrize("consumer", _BLANK_ROLE_DECISION_CONSUMERS)
    async def test_the_blank_role_rule_is_the_SHARED_is_blank(
        self, monkeypatch: pytest.MonkeyPatch, consumer: str
    ) -> None:
        """⚠ RED before i-a (register leg) — ROUTING IS NOT SHARING (A4 / MP-9c, WB13: a private
        ``role.strip()`` passed every r1 pin). Perturb the SHARED ``lorerunes.is_blank`` — every
        module-level binding of THAT object — so a normal role (``builder``) counts as blank; EVERY
        consumer must now refuse it. BASELINE leg first: unpatched, ``builder`` registers (a register that
        never checks roles would otherwise 'refuse' nothing and fail only here for the wrong reason)."""
        import lorerunes

        shared_is_blank = lorerunes.is_blank
        if consumer == "fake":
            fake = FakeAgentRegistry()
            await fake.register("baseline-agent", session=_LEGAL_SESSION, role=ROLE_BUILDER)
            assert len(fake.db.agents) == 1, "BASELINE: 'builder' must register on the fake"
            patched = patch_shared_object_everywhere(
                monkeypatch,
                "is_blank",
                shared_is_blank,
                lambda value: value == ROLE_BUILDER or shared_is_blank(value),
            )
            try:
                await fake.register(_LEGAL_NAME, session=_LEGAL_SESSION, role=ROLE_BUILDER)
            except AgentRegistryError:
                pass
            else:
                pytest.fail(identity_sweep_miss_message("FakeAgentRegistry's blank-role rule", patched))
            assert len(fake.db.agents) == 1, "a fake register refused by the mutated is_blank stored a row"
            return
        registry, admin_connection, env = await self._real_registry()
        try:
            await registry.register("baseline-agent", session=_LEGAL_SESSION, role=ROLE_BUILDER)
            assert await self._agent_row_count(admin_connection) == 1, "BASELINE: 'builder' must register"
            patched = patch_shared_object_everywhere(
                monkeypatch,
                "is_blank",
                shared_is_blank,
                lambda value: value == ROLE_BUILDER or shared_is_blank(value),
            )  # raises unless lorerunes.is_blank (the home) was among the patched bindings
            try:
                await registry.register(_LEGAL_NAME, session=_LEGAL_SESSION, role=ROLE_BUILDER)
            except AgentRegistryError:
                pass
            else:
                pytest.fail(identity_sweep_miss_message("register's blank-role rule", patched))
            assert await self._agent_row_count(admin_connection) == 1, (
                "a register refused by the (mutated) shared is_blank still wrote a row"
            )
        finally:
            await admin_connection.close()
            await registry.close()
            await drop_database(env)


# =========================================================================== #
# 63c-i-a r3 — amendment-4 A4-bis rider 2: ALLOWLIST-THE-SAFE over every READ of the identifier
# pattern. The ONE decision is ``lorerunes.is_legal_identifier``; outside ``lorerunes`` the pattern
# OBJECT may be read for its PROSE (``.pattern``, e.g. a refusal naming the rule) and nothing else —
# any ``.fullmatch``/``.match``/``.search``/call/argument use of it is a SECOND DECISION, named
# ``file:line``. This kills N1 (the server home keeps ``AGENT_NAME_PATTERN.fullmatch``) and N1b
# (``.match``) STATICALLY, without leaning on ``test_anchored_pattern_seam.py`` (adversary-r2 R-9).
#
# THREAT MODEL (CLAUDE.md "a gate needs a threat model"): this catches the HONEST developer who
# reaches for the familiar ``AGENT_NAME_PATTERN.fullmatch(value)`` instead of the shared predicate.
# It is NOT a boundary against a deliberately unusual author: a pattern reached through
# ``getattr(module, "AGENT_NAME_PATTERN")``, a container, or a function return is invisible to it
# (KNOWN BOUND, stated; re-open trigger: a production module that reads the pattern through any of
# those shapes). A private DRIFTED ``re.fullmatch(<own text>, …)`` never touches the name at all —
# that door (N1c) is the decision-MUTATION pin's to kill (the ``skip-policy`` leg), not this scan's.
# =========================================================================== #

#: The ONE attribute of the pattern object that is safe to read outside its ``lorerunes`` home: its
#: source text, for PROSE (the rule a refusal states). Allowlist the safe — never a list of forbidden
#: methods (the forbidden set is unbounded: ``fullmatch``/``match``/``search``/``finditer``/``sub``…).
_SAFE_PATTERN_ATTRIBUTES = frozenset({"pattern"})
_PATTERN_NAME = "AGENT_NAME_PATTERN"
#: The ONE package where the pattern may be USED for a decision (its home, amendment-2 A4).
_PATTERN_HOME_MEMBER = "lorerunes"


def _watched_pattern_names(tree: ast.Module) -> tuple[set[str], set[int]]:
    """The names under which ``tree`` can reach ``AGENT_NAME_PATTERN`` — the name itself, every
    ``from … import AGENT_NAME_PATTERN as <alias>``, and (to a fixpoint) every plain re-binding
    ``<alias> = <watched>`` — plus the ids of those re-binding VALUE nodes (the re-export shape, which
    decides nothing: its target is watched from then on)."""
    watched = {_PATTERN_NAME}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            watched.update(
                alias.asname for alias in node.names if alias.name == _PATTERN_NAME and alias.asname
            )
    rebinding_values: set[int] = set()
    grew = True
    while grew:
        grew = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            else:
                continue
            value = node.value
            if not (isinstance(value, ast.Name) and value.id in watched):
                continue
            if not all(isinstance(target, ast.Name) for target in targets):
                continue
            rebinding_values.add(id(value))
            new_names = {target.id for target in targets if isinstance(target, ast.Name)} - watched
            grew = grew or bool(new_names)
            watched |= new_names
    return watched, rebinding_values


def _pattern_decision_sites(tree: ast.Module, filename: str) -> list[str]:
    """Every READ of ``AGENT_NAME_PATTERN`` in ``tree`` that is NOT a ``.pattern`` prose read — as
    ``"<filename>:<line>: <source of the use>"``. Aliases are FOLLOWED (:func:`_watched_pattern_names`);
    the re-export re-binding is the one other safe read. A module-attribute read
    (``agents.AGENT_NAME_PATTERN.fullmatch``) is watched by the attribute name."""
    watched, rebinding_values = _watched_pattern_names(tree)
    parents = {id(child): node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    sites: list[str] = []
    for node in ast.walk(tree):
        read_name = (
            node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else None
        )
        if read_name not in watched or not isinstance(getattr(node, "ctx", None), ast.Load):
            continue
        if id(node) in rebinding_values:
            continue
        parent = parents.get(id(node))
        if isinstance(parent, ast.Attribute) and parent.value is node:
            if parent.attr in _SAFE_PATTERN_ATTRIBUTES:
                continue
            parent = parents.get(id(parent), parent)
        shown = parent if parent is not None else node
        sites.append(f"{filename}:{getattr(node, 'lineno', 0)}: {ast.unparse(shown)}")
    return sites


class TestTheIdentifierPatternIsReadOnlyForProseOutsideLorerunes63cIA:
    """amendment-4 A4-bis rider 2 — outside ``lorerunes`` the ONLY read of ``AGENT_NAME_PATTERN`` is
    ``.pattern`` (prose). A scan over EVERY production workspace member (reach DERIVED from
    ``pyproject.toml`` and CHECKED by ``assert_scan_reached_every_member``), with synthetic positive
    and negative controls proving the scanner fires on the doors it names and stays quiet on the safe
    shapes."""

    def test_no_production_module_outside_lorerunes_DECIDES_with_the_pattern(self) -> None:
        """⚠ RED before i-a: ``server.py::AppContext._is_comms_charset_legal`` decides with
        ``AGENT_NAME_PATTERN.fullmatch(value)`` — the second decider A4-bis retires (its body becomes
        ``return is_legal_identifier(value)``). GREEN on the build: the only reads left are ``.pattern``
        (refusal prose) and the ``agents.py`` re-export binding."""
        from _logging_fixtures import assert_scan_reached_every_member, parse_production_trees

        trees = parse_production_trees(include_scripts=False)
        assert_scan_reached_every_member(trees, extra_roots=())
        sites: list[str] = []
        prose_reads = 0
        for relpath, tree in trees.items():
            if relpath.split("/", 1)[0] == _PATTERN_HOME_MEMBER:
                continue
            sites += _pattern_decision_sites(tree, relpath)
            prose_reads += sum(
                1
                for node in ast.walk(tree)
                if isinstance(node, ast.Attribute)
                and node.attr in _SAFE_PATTERN_ATTRIBUTES
                and isinstance(node.value, (ast.Name, ast.Attribute))
                and (getattr(node.value, "id", None) or getattr(node.value, "attr", None)) == _PATTERN_NAME
            )
        assert prose_reads >= 1, (
            "ANTI-VACUITY: found NO `AGENT_NAME_PATTERN.pattern` prose read in any production module "
            "outside lorerunes — the scan is broken, not the tree clean (the refusal prose in server.py "
            "reads it today)"
        )
        assert not sites, (
            "outside its lorerunes home, AGENT_NAME_PATTERN may be read ONLY for its prose (`.pattern`); "
            "each site below DECIDES with it — a second decider beside lorerunes.is_legal_identifier "
            "(amendment-4 A4-bis; ROUTING IS NOT SHARING). Call the shared predicate instead:\n  "
            + "\n  ".join(sites)
        )

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("AGENT_NAME_PATTERN.fullmatch(value)\n", id="fullmatch"),
            pytest.param("AGENT_NAME_PATTERN.match(value)\n", id="match-N1b"),
            pytest.param("AGENT_NAME_PATTERN.search(value)\n", id="search"),
            pytest.param("re.fullmatch(AGENT_NAME_PATTERN, value)\n", id="passed-as-argument"),
            pytest.param("agents.AGENT_NAME_PATTERN.fullmatch(value)\n", id="module-attribute"),
            pytest.param(
                "from lorerunes import AGENT_NAME_PATTERN as _P\n_P.fullmatch(value)\n", id="import-alias"
            ),
            pytest.param(
                "from lorerunes import AGENT_NAME_PATTERN as _R\nAGENT_NAME_PATTERN = _R\n"
                "_LOCAL = AGENT_NAME_PATTERN\n_LOCAL.finditer(value)\n",
                id="re-export-then-rebind-alias",
            ),
        ],
    )
    def test_POSITIVE_CONTROL_the_scanner_names_every_decision_door(self, source: str) -> None:
        """Each door an honest author could plausibly write is NAMED (``file:line``) — so a green
        real-tree scan is a statement about the tree, not about a blind scanner."""
        sites = _pattern_decision_sites(ast.parse(source), "synthetic.py")
        assert len(sites) == 1 and sites[0].startswith("synthetic.py:"), sites

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("message = AGENT_NAME_PATTERN.pattern\n", id="prose-read"),
            pytest.param("x = agents.AGENT_NAME_PATTERN.pattern\n", id="module-attribute-prose"),
            pytest.param(
                "from lorerunes import AGENT_NAME_PATTERN as _R\nAGENT_NAME_PATTERN = _R\n"
                "rule = AGENT_NAME_PATTERN.pattern\n",
                id="re-export-binding-then-prose",
            ),
            pytest.param("from lorerunes import AGENT_NAME_PATTERN as AGENT_NAME_PATTERN\n", id="re-export"),
            pytest.param("OTHER_PATTERN.fullmatch(value)\n", id="unrelated-pattern"),
        ],
    )
    def test_NEGATIVE_CONTROL_the_scanner_stays_quiet_on_the_safe_shapes(self, source: str) -> None:
        """A gate that refuses honest code gets switched off: prose reads, the re-export binding and
        an unrelated pattern's decision are NOT flagged."""
        assert _pattern_decision_sites(ast.parse(source), "synthetic.py") == []


# =========================================================================== #
# 63c-i-a r4 — amendment-6 MP-1 (STOP-rule §2): the identity charset TEXT has ONE spelling in the workspace.
#
# THREAT MODEL (CLAUDE.md "A GATE NEEDS A THREAT MODEL" — stated IN the instrument, as ruled): this gate
# catches the HONEST ENGINEER who PASTES the charset regex into a new call site — adversary-r2 N1c and
# adversary-r3 X1 are exactly that: the same text with one extra ``.``, deciding identity legality
# privately beside ``lorerunes.is_legal_identifier``. It is NOT a boundary against an author who REWORDS
# the class (``[0-9a-z]``, ``[a-z\d]``) to evade it; anyone who can commit here can already ship anything.
# Verdicts follow mechanically: a pasted twin caught is the gate WORKING; a reworded evasion surviving is
# NOT a defect of this gate (amendment-6: any such door is a pinned KNOWN BOUND, never a contract round).
#
# The allowlist-attribute scan above is keyed on the NAME ``AGENT_NAME_PATTERN`` and the decision-mutation
# pin on a HAND-LIST of entry points; both are blind to a regex LITERAL that never names the pattern,
# wherever it sits. This scan is keyed on the TEXT, over every production member (reach checked).
# =========================================================================== #

#: The charset text every honest paste of the agent-identity rule carries — the leading class plus the
#: OPEN second class, so a drifted twin (``[a-z0-9][a-z0-9_.-]``, N1c/X1) matches as well as a verbatim
#: one (amendment-6 STOP-rule §2, the ruled key).
_IDENTIFIER_CHARSET_TEXT = "[a-z0-9][a-z0-9_"
#: The ONE binding that may carry the text: ``AGENT_NAME_PATTERN = re.compile(<text>)`` inside its home.
_CHARSET_DEFINITION_BINDING = "AGENT_NAME_PATTERN"
#: SAFE, EVIDENCE-BACKED exemptions (amendment-7, ruling r4 FORK-D reading (a)): a DIFFERENT policy whose
#: regex happens to share the key's prefix. ``(repo-relative path, binding, EXACT text) → the policy``.
#: Each entry is (i) matched only as ``<binding> = <constant>`` in that exact file WITH that exact text — any
#: change to the text stops the exemption matching, so the constant turns PRIVATE and the pin reds
#: (RE-OPEN TRIGGER: re-adjudicate); (ii) EVIDENCED live by the pin itself, in BOTH directions (the two
#: languages differ each way: it rejects a legal agent name AND accepts a string the agent rule rejects);
#: (iii) required to be OBSERVED in the real tree (a stale exemption reds). A new entry here is an
#: operator-visible adjudication, never a builder's convenience.
_UNRELATED_CHARSET_POLICIES: dict[tuple[str, str, str], str] = {
    ("loremaster/loremaster/config.py", "SLUG_PATTERN", r"^[a-z0-9][a-z0-9_]*$"): (
        "the PROJECT-SLUG rule (no hyphen, unbounded — operator directive 2026-07-03, task #32; consumed "
        "by the pydantic SlugStr constraint), not an agent identity"
    ),
}
#: The two-direction evidence witnesses (amendment-7): legal agent identity ✓ / slug ✗, and slug ✓ / agent ✗.
_AGENT_ONLY_WITNESS = "fixer-b"
_EXEMPT_ONLY_WITNESS = "a" * 65
_SYNTHETIC = "loremaster/loremaster/synthetic.py"
_CONFIG = "loremaster/loremaster/config.py"


def _is_charset_carrying_constant(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and _IDENTIFIER_CHARSET_TEXT in node.value
    )


def _assigned_binding(value_node: ast.AST, parents: dict[int, ast.AST]) -> str | None:
    """The single ``Name`` a plain/annotated assignment binds ``value_node`` to, else ``None``."""
    parent = parents.get(id(value_node))
    if isinstance(parent, ast.Assign) and parent.value is value_node and len(parent.targets) == 1:
        target = parent.targets[0]
        return target.id if isinstance(target, ast.Name) else None
    if (
        isinstance(parent, ast.AnnAssign)
        and parent.value is value_node
        and isinstance(parent.target, ast.Name)
    ):
        return parent.target.id
    return None


def _classify_charset_constants(tree: ast.Module, filename: str) -> dict[str, list[str]]:
    """Every string constant in ``tree`` carrying :data:`_IDENTIFIER_CHARSET_TEXT`, classified as
    ``definition`` (``AGENT_NAME_PATTERN = re.compile(<const>)`` inside a ``lorerunes`` module — the ONE
    allowed spelling), ``exempt`` (a :data:`_UNRELATED_CHARSET_POLICIES` binding in its own file) or
    ``private`` (EVERYTHING else: ``re.compile``/``re.fullmatch``/``re.match``/``re.search`` arguments, a
    raw-literal constant, an f-string part, a docstring — any spelling of the text is a second copy of the
    rule). Each entry is ``"<filename>:<line>: <source>"``."""
    parents = {id(child): node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    in_home = filename.split("/", 1)[0] == _PATTERN_HOME_MEMBER
    classified: dict[str, list[str]] = {"definition": [], "exempt": [], "private": []}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and _is_charset_carrying_constant(node)):
            continue
        site = f"{filename}:{getattr(node, 'lineno', 0)}: {ast.unparse(parents.get(id(node), node))}"
        call = parents.get(id(node))
        is_compile_argument = (
            isinstance(call, ast.Call)
            and bool(call.args)
            and call.args[0] is node
            and (
                (isinstance(call.func, ast.Attribute) and call.func.attr == "compile")
                or (isinstance(call.func, ast.Name) and call.func.id == "compile")
            )
        )
        defines_the_pattern = (
            call is not None and _assigned_binding(call, parents) == _CHARSET_DEFINITION_BINDING
        )
        if in_home and is_compile_argument and defines_the_pattern:
            classified["definition"].append(site)
        elif (filename, _assigned_binding(node, parents) or "", node.value) in _UNRELATED_CHARSET_POLICIES:
            classified["exempt"].append(site)
        else:
            classified["private"].append(site)
    return classified


class TestTheIdentifierCharsetTextHasOneSpelling63cIA:
    """amendment-6 MP-1 — the static ∀ (allowlist the SAFE, keyed on the TEXT, never on names or sites):
    over every production member, the identity charset text occurs in exactly ONE string constant — the
    ``lorerunes`` ``AGENT_NAME_PATTERN`` definition — plus the evidence-backed unrelated-policy
    exemptions. Threat model: the section header above."""

    def test_the_charset_text_occurs_ONLY_in_the_lorerunes_definition(self) -> None:
        """⚠ RED before i-a, RIGHT reason: ``agents.py`` still DEFINES the pattern (the A4 MOVE is unbuilt)
        and ``surreal_schema._IDENTIFIER_CHARSET_PATTERN`` is a raw-string TWIN of its text (amendment-6:
        the builder rebinds it ``= AGENT_NAME_PATTERN.pattern``, imported from ``lorerunes``). GREEN on
        the build: one definition, in ``lorerunes``; every other reader goes through the object.

        REACH PARAMETER, STATED (amendment-8 KB-3 — accepted, not a hole): ``include_scripts=False`` — the
        same reach the attribute scan above and #124's coverage pin run at; ``scripts/`` holds gates, deploy
        tooling and wrong-build fixtures, none of which decides identity legality. The bound is
        self-revealing: flipping the flag without adjudicating ``scripts/c3_wrongbuild_driver.py`` reds
        this scan on that fixture string. RE-OPEN TRIGGER: a ``scripts/`` module that imports
        ``lorerunes.is_legal_identifier`` or ``AGENT_NAME_PATTERN`` to DECIDE — at which point this scan's
        reach grows to ``scripts/``.

        STALE-EXEMPTION KEY (amendment-9 R-3): the stale check below keys on the exemption's PATH only —
        moot with one entry. RE-OPEN TRIGGER: the day a second exemption enters the SAME file, the key
        becomes ``(path, binding)`` (else a live sibling masks a stale one)."""
        from _logging_fixtures import assert_scan_reached_every_member, parse_production_trees

        assert _IDENTIFIER_CHARSET_TEXT in AGENT_NAME_PATTERN.pattern, (
            f"the gate's KEY {_IDENTIFIER_CHARSET_TEXT!r} no longer occurs in the live rule "
            f"{AGENT_NAME_PATTERN.pattern!r} — re-derive the key from the rule, or this scan watches nothing"
        )
        trees = parse_production_trees(include_scripts=False)
        assert_scan_reached_every_member(trees, extra_roots=())
        found: dict[str, list[str]] = {"definition": [], "exempt": [], "private": []}
        for relpath, tree in trees.items():
            for kind, sites in _classify_charset_constants(tree, relpath).items():
                found[kind] += sites
        assert not found["private"], (
            "the agent-identity charset TEXT is spelled OUTSIDE its one definition — each site below is a "
            "PRIVATE copy of the rule deciding (or able to decide) identity legality beside "
            "lorerunes.is_legal_identifier (amendment-6 MP-1; adversary-r2 N1c / adversary-r3 X1). Fix: "
            "call lorerunes.is_legal_identifier, or read AGENT_NAME_PATTERN.pattern where you need the "
            "rule's TEXT for prose/DDL — never paste it. A DOCSTRING or served prose QUOTING the rule is a "
            "second spelling too (amendment-8 KB-4: the P8d natural-language-corpse class — the next rule "
            "change leaves it false with every gate green): reference the constant "
            "(`lorerunes.AGENT_NAME_PATTERN` / `.pattern` derived into served text), never quote its "
            "text:\n  "
            + "\n  ".join(found["private"])
        )
        assert len(found["definition"]) == 1, (
            f"expected EXACTLY ONE `AGENT_NAME_PATTERN = re.compile(<text>)` definition inside lorerunes "
            f"(amendment-2 A4: the pattern MOVES to its lorerunes home), found {found['definition']}"
        )
        observed_exemptions = {site.split(":", 1)[0] for site in found["exempt"]}
        stale = sorted(
            path for path, _binding, _text in _UNRELATED_CHARSET_POLICIES if path not in observed_exemptions
        )
        assert not stale, (
            f"exemption(s) for {stale} matched NOTHING in the real tree — a stale allowlist entry is "
            f"decay (or the exempt constant's TEXT changed and it now reds above as private); delete or "
            f"re-adjudicate it (the SAFE set must describe the tree, never a memory of it)"
        )
        self._assert_every_exemption_is_a_DIFFERENT_language()

    @staticmethod
    def _assert_every_exemption_is_a_DIFFERENT_language() -> None:
        """The exemption's EVIDENCE, computed live (amendment-7 rider — never a prose claim): each exempt
        constant, read from its module, still carries the exact adjudicated text AND decides a language that
        differs from the agent-identity rule in BOTH directions. Two languages that differ both ways are two
        policies, allowed two patterns; if either direction fails the languages have CONVERGED."""
        import importlib
        import re

        for (path, binding, exact_text), policy in _UNRELATED_CHARSET_POLICIES.items():
            module = importlib.import_module(path.removesuffix(".py").split("/", 1)[1].replace("/", "."))
            exempt_text = getattr(module, binding)
            assert exempt_text == exact_text, (
                f"{path}::{binding} no longer carries its adjudicated text {exact_text!r} (now "
                f"{exempt_text!r}) — RE-OPEN TRIGGER: re-adjudicate the exemption (amendment-7)"
            )
            agent_accepts = {
                witness: AGENT_NAME_PATTERN.fullmatch(witness) is not None
                for witness in (_AGENT_ONLY_WITNESS, _EXEMPT_ONLY_WITNESS)
            }
            exempt_accepts = {
                witness: re.fullmatch(exempt_text, witness) is not None
                for witness in (_AGENT_ONLY_WITNESS, _EXEMPT_ONLY_WITNESS)
            }
            expected = (
                {_AGENT_ONLY_WITNESS: True, _EXEMPT_ONLY_WITNESS: False},
                {_AGENT_ONLY_WITNESS: False, _EXEMPT_ONLY_WITNESS: True},
            )
            assert (agent_accepts, exempt_accepts) == expected, (
                f"{path}::{binding} ({policy}) and the agent-identity rule no longer differ in BOTH "
                f"directions (agent={agent_accepts}, exempt={exempt_accepts}) — the two languages have "
                f"CONVERGED. That is NOT a new exemption: it is a design fork — one language with two "
                f"spellings goes to lorerunes as ONE predicate (the is_blank precedent; amendment-7)"
            )

    @pytest.mark.parametrize(
        ("source", "filename"),
        [
            pytest.param(
                'X = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n', _SYNTHETIC, id="pasted-twin-compile"
            ),
            pytest.param(
                'ok = re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", value)\n',
                _SYNTHETIC,
                id="drifted-dot-twin-N1c-X1"
            ),
            pytest.param('ok = re.match(r"^[a-z0-9][a-z0-9_-]{0,63}$", value)\n', _SYNTHETIC, id="match"),
            pytest.param('ok = re.search(r"^[a-z0-9][a-z0-9_-]{0,63}$", value)\n', _SYNTHETIC, id="search"),
            pytest.param(
                '_IDENTIFIER_CHARSET_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,63}$"\n', _SYNTHETIC, id="raw-literal"
            ),
            pytest.param(
                "DDL = f\"ASSERT string::matches($value, '^[a-z0-9][a-z0-9_-]{{0,63}}$') ON {table}\"\n",
                _SYNTHETIC,
                id="f-string-part",
            ),
            pytest.param(
                'AGENT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n',
                _SYNTHETIC,
                id="the-definition-OUTSIDE-lorerunes",
            ),
            pytest.param(
                'SLUG_PATTERN = r"^[a-z0-9][a-z0-9_]*$"\n', _SYNTHETIC, id="exempt-binding-in-the-WRONG-file"
            ),
            pytest.param(
                'SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_-]*$"\n',
                _CONFIG,
                id="exempt-binding-with-DRIFTED-text"
            ),
        ],
    )
    def test_POSITIVE_CONTROL_every_pasted_spelling_is_named(self, source: str, filename: str) -> None:
        """Each spelling an honest engineer could paste is named ``file:line`` — including the drifted-
        dot twin (N1c/X1), which the attribute scan above cannot see, and an exempt binding whose FILE or
        exact TEXT no longer matches its adjudication (amendment-7) — so a green real-tree scan is a
        statement about the tree, not about a blind scanner."""
        classified = _classify_charset_constants(ast.parse(source), filename)
        assert len(classified["private"]) == 1, classified
        assert classified["private"][0].startswith(f"{filename}:1:"), classified

    def test_POSITIVE_CONTROL_a_second_spelling_INSIDE_lorerunes_is_named_too(self) -> None:
        """The home is not a free zone: ONE definition — a pasted twin beside it in ``lorerunes`` (or a
        docstring quoting the text) is a second spelling."""
        source = (
            '"""Identity rule: ^[a-z0-9][a-z0-9_-]{0,63}$."""\n'
            'AGENT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n'
        )
        classified = _classify_charset_constants(ast.parse(source), "lorerunes/lorerunes/identifiers.py")
        assert len(classified["definition"]) == 1 and len(classified["private"]) == 1, classified

    @pytest.mark.parametrize(
        ("source", "filename", "kind"),
        [
            pytest.param(
                "_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern\n",
                "loremaster/loremaster/store/surreal_schema.py",
                None,
                id="dot-pattern-read-is-the-safe-shape",
            ),
            pytest.param(
                'AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n',
                "lorerunes/lorerunes/identifiers.py",
                "definition",
                id="the-one-definition-in-lorerunes",
            ),
            pytest.param(
                'SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_]*$"\n',
                _CONFIG,
                "exempt",
                id="evidence-backed-exemption",
            ),
            pytest.param(
                'X = re.compile(r"^[a-z]+$")\n', "loremaster/loremaster/x.py", None, id="unrelated-regex"
            ),
        ],
    )
    def test_NEGATIVE_CONTROL_the_safe_shapes_are_not_private(
        self, source: str, filename: str, kind: str | None
    ) -> None:
        """A gate that refuses honest code gets SWITCHED OFF: a ``.pattern`` read, the one definition, an
        evidence-backed exemption and an unrelated regex are never flagged private."""
        classified = _classify_charset_constants(ast.parse(source), filename)
        assert classified["private"] == [], classified
        if kind is not None:
            assert len(classified[kind]) == 1, classified

    # r4a (amendment-8 KB-2 — PINNED KNOWN BOUND, CLAUDE.md "WHEN YOU CANNOT CLOSE A HOLE, PIN IT"): the
    # reworded / runtime-assembled class is OUTSIDE this gate's threat model (the header: the HONEST
    # engineer who PASTES). r4's negative controls carried no reworded-class case, so this is the one
    # control r4a adds. First param = adversary-r4 TWR's text VERBATIM (a full-suite survivor, 2905/0 +
    # 11428/0 — the bound, measured).
    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(
                '_LEGACY_NAME_RE = re.compile(r"^[0-9a-z][0-9a-z_-]{0,63}$")\n', id="reworded-class-TWR"
            ),
            pytest.param(
                '_NAME_RE = re.compile(r"^[a-z\\d][a-z\\d_-]{0,63}$")\n', id="reworded-digit-escape"
            ),
            pytest.param(
                '_NAME_RE = re.compile("^[a-z0-9]" + "[a-z0-9_-]{0,63}$")\n', id="runtime-assembled"
            ),
        ],
    )
    def test_KNOWN_BOUND_a_REWORDED_or_ASSEMBLED_charset_is_NOT_named(self, source: str) -> None:
        """⚠ KNOWN BOUND (amendment-8 KB-2): a charset twin that REWORDS the class (``[0-9a-z]``,
        ``[a-z\\d]``) or ASSEMBLES the text at runtime evades this text-keyed scan BY DESIGN — it is an
        adversarial-only door (anyone who can commit here can already ship anything), not a defect of a
        gate built for the honest paste. This control asserts the hole EXISTS and REDS the day someone
        closes it. RE-OPEN TRIGGER (verbatim from #138): the threat model changes — untrusted contributors
        or a hosted deployment (packet 39 consults it)."""
        classified = _classify_charset_constants(ast.parse(source), "loremaster/loremaster/agents.py")
        assert classified["private"] == [], (
            "KNOWN BOUND — threat model: honest paste (amendment-6 §1); if you closed it deliberately, "
            f"delete this control and say so. The scan now names a reworded/assembled class: {classified}"
        )


# =========================================================================== #
# 63c-i-a r4 — amendment-6 MP-1 (STOP-rule §3): the ``_comms_traffic_line`` SKIP gate's OWN call site moves
# with the shared decision (adversary-r3 X1 / KP-X1's shape). A4-bis ruled the gate "reads the home and is
# NOT rewired"; the decision-mutation pin probes the HOME, never the gate, so a gate deciding privately
# survived 2807/0. These legs observe the gate's EFFECT — a registry READ — so a private decider at that
# call site is visible when it WIDENS (the hostile corpus is looked up), REPLACES (the shared-decision
# mutation leaves it looking up), or NARROWS on any axis a legal witness carries (a witness of
# ``_LEGAL_IDENTIFIER_WITNESSES`` is not looked up). r4a (amendment-9 R-2): that is what the legs OBSERVE;
# a ∀ over every spelling is not something fixture witnesses can deliver, and this header no longer
# claims it (the r4 wording "whatever it spells" was falsified by adversary-r4 G1, a narrowing conjunct
# that survived the full suite). r4b-fix (amendment 13 §G4): the ∀ is now a separate GENERATED leg — witnesses
# drawn from the identity language itself (``from_regex`` over ``lorerunes.AGENT_NAME_PATTERN``), 200
# derandomized examples, oracle-equal to ``lorerunes.is_legal_identifier`` — so a narrowing conjunct on an
# axis NO hand-listed witness carries (adversary-r4b G4: doubled separators) is in its sample space.
# =========================================================================== #


class _LookupCountingRegistry:
    """A spy ``agent_registry``: counts ``get_agent`` reads and resolves nobody (R1: the traffic line is
    then honest silence either way, so only the READ is observed)."""

    def __init__(self) -> None:
        self.lookups: list[str] = []

    async def get_agent(self, name: str, *, session: str | None = None) -> Any:
        self.lookups.append(name)
        raise AgentRegistryError(f"no agent {name!r}")


async def _traffic_line_lookups(attribution: str) -> list[str]:
    """The registry reads ``AppContext._comms_traffic_line`` performs for ONE identity-less attribution."""
    import types

    from loremaster.server import AppContext

    spy = _LookupCountingRegistry()
    context = types.SimpleNamespace(agent_registry=spy, message_ledger=None)
    await AppContext._comms_traffic_line(  # noqa: SLF001 - the SKIP gate under test
        cast(Any, context), agent=None, session=None, attributions=(attribution,)
    )
    return spy.lookups


def _the_identity_language() -> st.SearchStrategy[str]:
    """r4b-fix (amendment 13 §G4): the legal identity LANGUAGE as a generator — ``from_regex`` over THE
    pattern object ``lorerunes.AGENT_NAME_PATTERN`` (resolved at draw time; it MOVES there in i-a),
    ``fullmatch=True``.
    Deriving from the pattern is not circular for the SKIP-gate leg: its property is "the gate agrees with the
    predicate everywhere", and the pattern's own text is pinned elsewhere."""
    import re

    import lorerunes

    identity_pattern: re.Pattern[str] = lorerunes.AGENT_NAME_PATTERN
    return st.from_regex(identity_pattern, fullmatch=True)


def _text_the_shared_predicate_rejects() -> st.SearchStrategy[str]:
    """r4b-fix (amendment 13 §G4): arbitrary text the SHARED predicate rejects (resolved at draw time)."""
    import lorerunes

    def _rejected_by_the_shared_predicate(value: str) -> bool:
        return not lorerunes.is_legal_identifier(value)

    return st.text().filter(_rejected_by_the_shared_predicate)


class TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA:
    """amendment-6 MP-1 §3 — BASELINE: a legal attribution is looked up ONCE; under the shared-decision
    mutation it is looked up ZERO times; and ∀ the shared hostile corpus, ZERO lookups (R8's read budget —
    "a value that cannot BE a name is never looked up" — as an EFFECT over the corpus, not one value)."""

    # r4a (amendment-9 MP-R4-3): the r4 params (``_LEGAL_NAME``, ``_LEGAL_SESSION``) are KEPT and the SHARED
    # legal corpus is appended (additive — no param deleted, so no DUAL row). The BASELINE ("looked up
    # exactly once") now runs at every boundary point, so a narrowing conjunct dies on its witness.
    @pytest.mark.parametrize(
        "attribution", list(dict.fromkeys((_LEGAL_NAME, _LEGAL_SESSION, *_LEGAL_IDENTIFIER_WITNESSES)))
    )
    async def test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier(
        self, monkeypatch: pytest.MonkeyPatch, attribution: str
    ) -> None:
        """⚠ RED before i-a (``lorerunes.is_legal_identifier`` does not exist). DIFFERENT legal
        attributions (no parameter monoculture) — the two r4 values plus every witness of the shared
        legal corpus, the 64-char cap included. A gate that decides with a private regex keeps looking
        the value up under the mutation — X1's door; a gate that NARROWS with a private conjunct never
        looks the witness up at all — adversary-r4 G1's door (``or len(attribution) > 32``), which the
        ``"a" * 64`` baseline kills."""
        import lorerunes

        assert await _traffic_line_lookups(attribution) == [attribution], (
            f"BASELINE: the legal attribution {attribution!r} was not looked up exactly once"
        )
        shared_predicate = lorerunes.is_legal_identifier
        patched = patch_shared_object_everywhere(
            monkeypatch,
            "is_legal_identifier",
            shared_predicate,
            lambda value: value != attribution and shared_predicate(value),
        )
        lookups = await _traffic_line_lookups(attribution)
        assert lookups == [], identity_sweep_miss_message(
            f"the _comms_traffic_line SKIP gate (it still looked up {attribution!r}, which the SHARED "
            f"decision now rejects — a private decider at the gate's call site: amendment-6 MP-1 / X1)",
            patched,
        )

    async def test_the_SKIP_gate_never_looks_up_any_value_of_the_hostile_corpus(self) -> None:
        """∀ ``_HOSTILE_IDENTIFIERS``: ZERO registry reads (GREEN at HEAD — the home rejects every shape
        today; a gate that widens its private charset past the shared one reds on the shapes it admits —
        incl. r4a's dotted ``"fixer.b"``, which kills adversary-r4 G2). POSITIVE CONTROL first: the spy
        DOES see exactly one lookup for EVERY legal witness (r4a, amendment-9 MP-R4-3 — the control runs
        over the shared legal corpus, never one value)."""
        for legal_value in (_LEGAL_NAME, *_LEGAL_IDENTIFIER_WITNESSES):
            assert await _traffic_line_lookups(legal_value) == [legal_value], (
                f"CONTROL: the legal witness {legal_value!r} was not looked up exactly once — the spy (or "
                f"the gate) cannot observe a legal read"
            )
        looked_up: dict[str, list[str]] = {}
        for value in _HOSTILE_IDENTIFIERS:
            if lookups := await _traffic_line_lookups(value):
                looked_up[value] = lookups
        assert not looked_up, (
            f"the SKIP gate looked up value(s) that cannot BE an identity (R8's read budget; amendment-6 "
            f"MP-1 §3): {looked_up!r}"
        )

    # r4b-fix (amendment 13 §G4): the ORACLE-EQUALITY legs — the ∀ the hand-listed corpus above is not.
    # PURE and in-memory (the spy registry; no store, no network), so 200 examples cost milliseconds under
    # ``-n 12``. ``derandomize=True`` fixes the example set per test (deterministic under xdist, the failing
    # example printed by the framework); ``database=None`` writes no ``.hypothesis/`` into the tree (and the
    # in-image conformance run mounts the repo ``:ro``); ``deadline=None`` because a loaded ``-n 12`` box is
    # not a performance test. The strategies are DEFERRED: ``lorerunes.AGENT_NAME_PATTERN`` /
    # ``is_legal_identifier`` do not exist before i-a, so resolving them at collection time would error the
    # whole module; deferred, each leg is RED at HEAD for exactly that reason and nothing else.
    @settings(derandomize=True, max_examples=200, database=None, deadline=None)
    @given(attribution=st.deferred(_the_identity_language))
    def test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_GENERATED_identity_language(
        self, attribution: str
    ) -> None:
        """⚠ RED before i-a (the pattern has not MOVED to ``lorerunes``). ∀ values GENERATED from the ONE
        pattern object (``from_regex(lorerunes.AGENT_NAME_PATTERN, fullmatch=True)``): the gate looks the
        value up EXACTLY when the shared predicate accepts it — ``looked_up_once ==
        is_legal_identifier(value)`` — and never more than once. The oracle is the predicate, not the pattern,
        so a generated value the predicate rejects (should the generator ever emit one) is still judged
        correctly. Kills adversary-r4b G4 (a
        private ``or "--" in attribution or "__" in attribution`` at the gate) and every narrowing conjunct on
        an axis of the language, named or not; the hand-listed baseline legs above stay as NAMED controls."""
        import lorerunes

        lookups = asyncio.run(_traffic_line_lookups(attribution))
        assert lookups in ([], [attribution]), (
            f"the SKIP gate read the registry {len(lookups)} time(s) for ONE attribution {attribution!r}: "
            f"{lookups!r}"
        )
        looked_up_once = lookups == [attribution]
        assert looked_up_once == lorerunes.is_legal_identifier(attribution), (
            f"the SKIP gate {'LOOKED UP' if looked_up_once else 'SKIPPED'} {attribution!r}, which the SHARED "
            f"decision {'rejects' if looked_up_once else 'accepts'} — a private decider at the gate's call "
            f"site (amendment 13 §G4 / adversary-r4b G4: a narrowing conjunct on an axis no hand-listed "
            f"witness carries)"
        )

    @settings(derandomize=True, max_examples=200, database=None, deadline=None)
    @given(value=st.deferred(_text_the_shared_predicate_rejects))
    def test_the_SKIP_gate_never_looks_up_GENERATED_text_the_SHARED_predicate_rejects(
        self, value: str
    ) -> None:
        """⚠ RED before i-a (``lorerunes.is_legal_identifier`` does not exist). The hostile companion of the
        leg above: ∀ arbitrary text the shared predicate REJECTS (``st.text()`` filtered by ``not
        is_legal_identifier``), the gate performs ZERO registry reads — ``looked_up_once is False`` — so a
        gate that WIDENS past the shared charset reds on a generated shape, not only on the hand-listed
        ``_HOSTILE_IDENTIFIERS``."""
        lookups = asyncio.run(_traffic_line_lookups(value))
        assert lookups == [], (
            f"the SKIP gate looked up {value!r}, which the SHARED predicate rejects — it cannot BE an "
            f"identity (R8's read budget; amendment 13 §G4 hostile companion): {lookups!r}"
        )


# =========================================================================== #
# 63c-i-a r3 — amendment-4 MP-E + amendment-3 F-2 rider 1, MERGED: ONE parity matrix driven through BOTH
# the REAL ``AgentRegistry`` and ``FakeAgentRegistry``. "The fake mirrors the WRITER" (amendment-2 A2)
# was pinned only by a signature-equality PROXY; the fake's stamps were read by NO test, so a fake
# stamping ``'WRONG'`` passed 2521/0 (adversary-r2 N5). This MEASURES the mirror instead of asserting
# it: same inputs → same OUTCOME CLASS (registered | refused-with-AgentRegistryError, zero writes) and,
# on success, the same STAMPS (owner_principal, owner_agent == self, scope == keep_scope(K)).
# Message parity is deliberately NOT compared (amendment-3 F-2: a fake serves no consumer).
# =========================================================================== #

_PARITY_KEEP = "sessionkeep7"
#: r4b (amendment-11 C2): a SECOND keep, for the re-register keep axis (never equal to ``_PARITY_KEEP``).
_PARITY_OTHER_KEEP = "sessionkeep8"


def _parity_cases() -> list[Any]:
    """The matrix rows: the provenance pairs (consistent ×2, mixed ×2), every hostile identity of the
    SHARED corpus × {name, session}, every blank role — one ``pytest.param`` each, ids derived."""
    base = {"name": _LEGAL_NAME, "session": _LEGAL_SESSION, "role": ROLE_BUILDER}
    pairs = {
        "pair-both-set": ("alice_pid", _PARITY_KEEP),
        "pair-alpha-none": (None, None),
        "pair-owner-only": ("alice_pid", None),
        "pair-keep-only": (None, _PARITY_KEEP),
    }
    rows: list[Any] = [
        pytest.param({**base, "owner_principal_id": owner, "session_keep_id": keep}, id=row_id)
        for row_id, (owner, keep) in pairs.items()
    ]
    for index, hostile_value in enumerate(_HOSTILE_IDENTIFIERS):
        for field in ("name", "session"):
            rows.append(pytest.param({**base, field: hostile_value}, id=f"hostile-{index:02d}-{field}"))
    for index, blank_role in enumerate(_MOVE_BLANK_ROLES):
        rows.append(pytest.param({**base, "role": blank_role}, id=f"blank-role-{index}"))
    return rows


class TestTheFakeRegistryMirrorsTheWriter63cIA:
    """amendment-4 MP-E (merged with amendment-3 F-2 rider 1) — outcome-class + stamp parity, real vs
    fake, over the whole matrix. ⚠ RED before i-a on the real side (the ``session_keep_id`` kwarg, the
    MOVE and the stamps are unbuilt) and, for the identity rows, on the fake side too (its identity
    leg is inert until ``lorerunes.is_legal_identifier`` exists — FORK-C)."""

    @staticmethod
    async def _real_outcome(kwargs: dict[str, Any]) -> tuple[Any, ...]:
        harness = TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA
        registry, admin_connection, env = await harness._real_registry()  # noqa: SLF001
        try:
            try:
                result = await registry.register(
                    kwargs["name"], session=kwargs["session"], role=kwargs["role"],
                    owner_principal_id=kwargs.get("owner_principal_id"),
                    session_keep_id=kwargs.get("session_keep_id"),
                )
            except AgentRegistryError:
                written = await harness._agent_row_count(admin_connection)  # noqa: SLF001
                assert written == 0, f"REAL: a refused register wrote {written} row(s)"
                return ("refused",)
            bare_id = str(result.agent.id).split(":", 1)[-1]
            stamped = await run(
                admin_connection,
                f"SELECT owner_principal, owner_agent, scope FROM type::record('{AGENT_TABLE}', $id)",
                {"id": bare_id},
            )
            row = stamped[0]
            owner = row.get("owner_principal")
            owner_agent = row.get("owner_agent")
            return (
                "registered",
                str(owner).split(":", 1)[-1] if owner is not None else None,
                owner_agent is not None and str(owner_agent) == f"{AGENT_TABLE}:{bare_id}",
                row.get("scope"),
            )
        finally:
            await admin_connection.close()
            await registry.close()
            await drop_database(env)

    @staticmethod
    async def _fake_outcome(kwargs: dict[str, Any]) -> tuple[Any, ...]:
        fake = FakeAgentRegistry()
        try:
            result = await fake.register(
                kwargs["name"], session=kwargs["session"], role=kwargs["role"],
                owner_principal_id=kwargs.get("owner_principal_id"),
                session_keep_id=kwargs.get("session_keep_id"),
            )
        except AgentRegistryError:
            assert fake.db.agents == {}, f"FAKE: a refused register stored a row: {fake.db.agents!r}"
            return ("refused",)
        agent_id = str(result.agent.id).split(":", 1)[-1]
        return (
            "registered",
            fake.db.owners.get(agent_id),
            fake.db.owner_agents.get(agent_id) == agent_id,
            fake.db.scopes.get(agent_id),
        )

    @pytest.mark.parametrize("kwargs", _parity_cases())
    async def test_the_fake_and_the_real_writer_agree_on_outcome_class_and_stamps(
        self, kwargs: dict[str, Any]
    ) -> None:
        """Same inputs → same outcome class, and on success the same governed stamps. The expected
        stamps for the consistent pairs are ALSO asserted absolutely (never only 'equal to each other' —
        two builds that both stamp nothing would agree): ``(alice_pid, owner_agent == self,
        keep_scope(K))`` for both-set, ``(None, …, None)`` for the α pair."""
        from lorerunes.pdp import keep_scope

        real = await self._real_outcome(kwargs)
        fake = await self._fake_outcome(kwargs)
        assert fake == real, (
            f"FakeAgentRegistry does NOT mirror the writer on {kwargs!r}: real={real!r} fake={fake!r} "
            f"(amendment-4 MP-E — outcome class + stamps; a fake that accepts what the writer refuses, or "
            f"stamps what it does not, is the fixture that hides a tool-layer bug)"
        )
        legal_identity = (kwargs["name"], kwargs["session"], kwargs["role"]) == (
            _LEGAL_NAME,
            _LEGAL_SESSION,
            ROLE_BUILDER,
        )
        owner, keep = kwargs.get("owner_principal_id"), kwargs.get("session_keep_id")
        if legal_identity and owner is not None and keep is not None:
            assert real == ("registered", "alice_pid", True, keep_scope(_PARITY_KEEP)), real
        elif legal_identity and owner is None and keep is None:
            assert real[0] == "registered" and real[1] is None and real[3] is None, real
        else:
            assert real == ("refused",), real

    # --- r4 (amendment-6 MP-5): the RE-register door (THE QUANTIFIER LAW on MP-E — the mirror above was
    # measured on the CREATE door only; adversary-r3 FX1, the fake healing an unstamped row on
    # re-register, passed 2807/0). Additive — no pin deleted, so no DUAL row.
    # r4a (amendment-8 KB-5 as CORRECTED by amendment-9 MP-R4-1/-6): a FOURTH sequence — a STAMPED row
    # re-registered with a DIFFERENT consistent pair (bob = a householded joiner: same session keep K,
    # different owner — reachable through ``_comms_register``, which admits any principal householded in
    # the session keep). Additive — no sequence deleted, so no DUAL row.
    _RE_REGISTER_SEQUENCES: dict[str, tuple[tuple[str | None, str | None], tuple[str | None, str | None]]] = {
        "alpha-then-credentialed": ((None, None), ("alice_pid", _PARITY_KEEP)),
        "consistent-then-owner-only": (("alice_pid", _PARITY_KEEP), ("alice_pid", None)),
        "consistent-then-keep-only": (("alice_pid", _PARITY_KEEP), (None, _PARITY_KEEP)),
        "consistent-then-householded-joiner-pair": (("alice_pid", _PARITY_KEEP), ("bob_pid", _PARITY_KEEP)),
        # r4b (amendment-11 C2 / amendment-10 C-2 — the registry-seam row): the KEEP axis. A writer (or fake)
        # that re-stamps when the caller's keep differs from the stamped one (adversary-r4a C2) passed the
        # full suite, because every sequence above re-registers with ``_PARITY_KEEP``. Unreachable through
        # the tool today (the keep is ``session:{session}``, UNIQUE-keyed — amendment 10 C-2), so pinned at
        # the registry seam. Both owners, so the second pairs span the 2×2 {same, different} owner × keep
        # grid (same/same is the r2 mint-once pin). Additive — no sequence deleted, so no DUAL row.
        "consistent-then-different-keep": (("alice_pid", _PARITY_KEEP), ("alice_pid", _PARITY_OTHER_KEEP)),
        "consistent-then-different-owner-and-keep": (
            ("alice_pid", _PARITY_KEEP),
            ("bob_pid", _PARITY_OTHER_KEEP),
        ),
    }
    # DUAL (r4a — RE-KEYED, values PRESERVED): r4's absolute leg was an ``if sequence == "alpha-…" / else``
    # pair; it is now this table, with the r4 values carried byte-for-byte for the three r4 sequences
    # (alpha → ``("re-registered", None, True, None)``; each mixed pair → ``("refused", "alice_pid", True,
    # keep:K)``), so a fourth sequence cannot silently fall into the ``else`` branch's REFUSED expectation.
    #: The ABSOLUTE expected REAL outcome per sequence (never only ``fake == real`` — two builds that both
    #: heal, or both re-stamp, would agree their way past a parity-only row: adversary-r4 RS1 + FX2 together).
    #: Built at call time (``keep_scope`` is imported lazily, as every pin in this class does).
    _RE_REGISTER_EXPECTED_REAL: dict[str, tuple[str, str | None, bool, bool]] = {
        # (second-call outcome, owner_principal, owner_agent == self, scope == keep_scope(K) [False ⇒ NONE])
        "alpha-then-credentialed": ("re-registered", None, True, False),
        "consistent-then-owner-only": ("refused", "alice_pid", True, True),
        "consistent-then-keep-only": ("refused", "alice_pid", True, True),
        "consistent-then-householded-joiner-pair": ("re-registered", "alice_pid", True, True),
        # r4b (amendment-11 C2): the FIRST keep survives — ``True`` is ``scope == keep_scope(_PARITY_KEEP)``,
        # never the second call's ``_PARITY_OTHER_KEEP``.
        "consistent-then-different-keep": ("re-registered", "alice_pid", True, True),
        "consistent-then-different-owner-and-keep": ("re-registered", "alice_pid", True, True),
    }

    @staticmethod
    async def _real_re_register_outcome(
        first: tuple[str | None, str | None], second: tuple[str | None, str | None]
    ) -> tuple[Any, ...]:
        harness = TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA
        registry, admin_connection, env = await harness._real_registry()  # noqa: SLF001
        try:
            created = await registry.register(
                _LEGAL_NAME, session=_LEGAL_SESSION, role=ROLE_BUILDER,
                owner_principal_id=first[0], session_keep_id=first[1],
            )
            try:
                await registry.register(
                    _LEGAL_NAME, session=_LEGAL_SESSION, role=ROLE_BUILDER,
                    owner_principal_id=second[0], session_keep_id=second[1],
                )
                second_outcome = "re-registered"
            except AgentRegistryError:
                second_outcome = "refused"
            assert await harness._agent_row_count(admin_connection) == 1, "REAL: a re-register minted a row"  # noqa: SLF001
            bare_id = str(created.agent.id).split(":", 1)[-1]
            row = (
                await run(
                    admin_connection,
                    f"SELECT owner_principal, owner_agent, scope FROM type::record('{AGENT_TABLE}', $id)",
                    {"id": bare_id},
                )
            )[0]
            owner, owner_agent = row.get("owner_principal"), row.get("owner_agent")
            return (
                second_outcome,
                str(owner).split(":", 1)[-1] if owner is not None else None,
                owner_agent is not None and str(owner_agent) == f"{AGENT_TABLE}:{bare_id}",
                row.get("scope"),
            )
        finally:
            await admin_connection.close()
            await registry.close()
            await drop_database(env)

    @staticmethod
    async def _fake_re_register_outcome(
        first: tuple[str | None, str | None], second: tuple[str | None, str | None]
    ) -> tuple[Any, ...]:
        fake = FakeAgentRegistry()
        created = await fake.register(
            _LEGAL_NAME, session=_LEGAL_SESSION, role=ROLE_BUILDER,
            owner_principal_id=first[0], session_keep_id=first[1],
        )
        try:
            await fake.register(
                _LEGAL_NAME, session=_LEGAL_SESSION, role=ROLE_BUILDER,
                owner_principal_id=second[0], session_keep_id=second[1],
            )
            second_outcome = "re-registered"
        except AgentRegistryError:
            second_outcome = "refused"
        assert len(fake.db.agents) == 1, "FAKE: a re-register minted a row"
        agent_id = str(created.agent.id).split(":", 1)[-1]
        return (
            second_outcome,
            fake.db.owners.get(agent_id),
            fake.db.owner_agents.get(agent_id) == agent_id,
            fake.db.scopes.get(agent_id),
        )

    @pytest.mark.parametrize("sequence", list(_RE_REGISTER_SEQUENCES))
    async def test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door(self, sequence: str) -> None:
        """amendment-6 MP-5 — (α register → credentialed consistent re-register) and (consistent register →
        each mixed pair): same second-call outcome class and the same three stamps read back afterwards,
        real vs fake (KP-FX1's shape). ⚠ RED before i-a on the real side (the ``session_keep_id`` kwarg).
        ABSOLUTE expectations too (two builds that both heal would agree): mint-once ∀ rows — the α row
        stays unstamped after the credentialed re-register (MP-F), and a mixed pair after a consistent
        register is REFUSED (A3 XOR on the re-register path, MP-B) leaving the CREATE stamps intact.
        r4a (amendment-8 KB-5 / amendment-9 MP-R4-6): the fourth sequence — a DIFFERENT consistent pair —
        re-registers and leaves the FIRST caller's stamps intact, real AND fake (adversary-r4 FX2: the fake
        re-stamping alone passed 2905/0). r4b (amendment-11 C2): two more — a DIFFERENT KEEP (same and
        different owner) re-registers and leaves the FIRST keep's scope, real AND fake (adversary-r4a C2)."""
        from lorerunes.pdp import keep_scope

        first, second = self._RE_REGISTER_SEQUENCES[sequence]
        real = await self._real_re_register_outcome(first, second)
        fake = await self._fake_re_register_outcome(first, second)
        assert fake == real, (
            f"FakeAgentRegistry does NOT mirror the writer on the RE-register door ({sequence}): "
            f"real={real!r} fake={fake!r} (amendment-6 MP-5 — a fake that heals or re-stamps on re-register "
            f"lets every fake-driven test observe a scope the production writer never stamps)"
        )
        outcome, owner, owner_agent_is_self, scoped = self._RE_REGISTER_EXPECTED_REAL[sequence]
        assert real == (outcome, owner, owner_agent_is_self, keep_scope(_PARITY_KEEP) if scoped else None), (
            f"the REAL writer's RE-register outcome for {sequence!r} is not the ruled one: {real!r} "
            f"(ruling §2.2 row 2 — a re-register leaves owner_principal / owner_agent / scope UNTOUCHED, "
            f"from ANY caller; A3 XOR refuses a mixed pair)"
        )

    async def test_the_REAL_writer_never_re_stamps_a_stamped_row_from_a_DIFFERENT_householded_principal(
        self,
    ) -> None:
        """⚠ RED before i-a (the ``session_keep_id`` kwarg). amendment-9 MP-R4-1 (GATING) — ruling §2.2
        row 2 pinned ∀ CALLERS, not only ∀ rows: register ``(alice_pid, K)``, re-register ``(bob_pid, K)``
        (a householded joiner — same session keep, different owner) → the second call re-registers and the
        row keeps ``owner_principal = alice_pid``, ``owner_agent = self``, ``scope = keep:K``. The r2 pin
        ``test_agent_governance_63c_i_a.py::…::test_re_register_does_not_restamp_the_governed_triple_mint_once``
        re-registers with the SAME principal (re-stamping writes identical bytes), and MP-F's rows are
        UNSTAMPED — so a writer that re-stamps an ALREADY-stamped row from the caller's pair (an ownership
        TAKEOVER through an ordinary tool call) passed the full suite (adversary-r4 RS1, 11426/0 with the
        other survivors). KP-RS1's shape, ABSOLUTE expectation (independent of the fake, so a fake that
        re-stamps too cannot agree its way past it)."""
        from lorerunes.pdp import keep_scope

        real = await self._real_re_register_outcome(("alice_pid", _PARITY_KEEP), ("bob_pid", _PARITY_KEEP))
        assert real == ("re-registered", "alice_pid", True, keep_scope(_PARITY_KEEP)), (
            f"a re-register from a DIFFERENT householded principal changed the governed triple: {real!r} — "
            f"mint-once is ∀ callers (ruling §2.2 row 2; amendment-9 MP-R4-1): a re-register never re-stamps "
            f"owner_principal / owner_agent / scope, whoever calls it"
        )


# DUAL (r4, amendment-6 MP-3): the r3 FORK-C rider-2 SOURCE-TEXT pin
# ``test_the_fakes_HEAD_RED_import_guard_is_deleted_once_the_predicate_exists`` (an AST scan for an
# ``except`` handler NAMING ``ImportError`` in ``_comms_fakes.py``) is DELETED, not kept beside this one:
# two pins for one property, one of them a proxy, is decoration that reads as coverage. Its virtue ("the
# HEAD-RED guard must not outlive its premise", incl. its HEAD anti-vacuity control) now lives in this
# EFFECT pin, which also reds every silent-skip spelling the text pin waved through (adversary-r3 X3
# ``except Exception:``, a bare ``except:``, ``builtins.ImportError``, ``getattr(lorerunes, …, None)``)
# AND the originally ruled spelling (X3b).
# ⚠ ERRATUM (r4a, amendment-9 MP-R4-5 — against amendment-6 MP-3): the deletion above was a DUAL LOSS. The
# two pins observed DIFFERENT properties — the effect pin observes *silent skip*, the deleted pin observed
# *the guard outlives its premise* — and adversary-r4 FXf (a guard KEPT with a NON-silent private-regex
# fallback) separates them: 11428/0 on the full suite with the effect pin green. The presence property is
# RESTORED below, property-shaped rather than as the r3 spelling (``except ImportError``):
# ``test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists``.
_FAKE_SKIP_HEAD_CONTROL = "fixer-b\n"  # a hostile name the HEAD guard lets through (finding #210's shape)


async def test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """amendment-6 MP-3 (replaces amendment-5 FORK-C rider 2's spelling pin) — the property is EFFECT, not
    text: once ``lorerunes.is_legal_identifier`` EXISTS, the fake's identity leg has NO silent-skip path.
    With the shared predicate made UNIMPORTABLE (``monkeypatch.delattr``), a hostile fake register must NOT
    succeed — ∀ the shared hostile corpus × {name, session} — any exception is fine (an ``ImportError`` is
    the honest outcome; a module-top import that still refuses is too), and ``fake.db.agents`` stays empty.

    HEAD CONTROL (anti-vacuity, while the predicate is absent the guard is LEGITIMATE — amendment-5 FORK-C):
    the hostile ``"fixer-b\\n"`` DOES register on the fake at HEAD, proving this instrument can SEE a silent
    skip (a pin that could not observe one would pass the post-build leg vacuously). REDs on the build until
    the builder deletes the guard in REFACTOR (its one granted test-tree edit).

    DUAL (r4a, amendment-9 MP-R4-4 — the simulation's REACH is re-keyed; virtues kept: the HEAD control, the
    ∀ corpus × {name, session} leg, "any exception is non-silent"): r4 removed the predicate at ONE binding
    (``monkeypatch.delattr(lorerunes, …)`` — the PACKAGE attribute), so a guard whose ``try`` imports from
    the defining SUBMODULE never raised and outlived its premise with this pin green (adversary-r4 FXg,
    full-suite survivor). "Predicate absent" is now simulated at EVERY ``lorerunes*`` module-level binding
    of THE object (``module_level_bindings_of`` — the ONE by-identity finder; anti-vacuity: ≥ 1 home
    found), layout-independent (adversary-r4 R-5). The fake's OWN binding (``_comms_fakes``) is not a
    ``lorerunes*`` module and is deliberately left: a module-top import that still refuses is the honest
    outcome. What this pin CANNOT see — a guard KEPT with a non-silent fallback (FXf) — is the presence
    pin's property (``test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_
    exists``); two pins, two properties."""
    from _logging_fixtures import module_level_bindings_of

    import lorerunes

    shared_predicate = getattr(lorerunes, "is_legal_identifier", None)
    if shared_predicate is None:
        fake = FakeAgentRegistry()
        await fake.register(_FAKE_SKIP_HEAD_CONTROL, session=_LEGAL_SESSION, role=ROLE_BUILDER)
        assert len(fake.db.agents) == 1, (
            "CONTROL: at HEAD (predicate absent) the fake's guard must visibly SKIP the identity leg — "
            "otherwise this instrument cannot observe the silent skip it exists to catch"
        )
        return
    lorerunes_homes = [
        (module_name, module, attribute)
        for module_name, module, attribute in module_level_bindings_of(shared_predicate)
        if _is_lorerunes_module(module_name)
    ]
    assert lorerunes_homes, (
        "ANTI-VACUITY: no lorerunes* module-level binding of is_legal_identifier was found — the "
        "'predicate absent' simulation would remove nothing, and every leg below would be vacuous"
    )
    for _module_name, module, attribute in lorerunes_homes:
        monkeypatch.delattr(module, attribute)
    silently_registered: list[str] = []
    for hostile_value in _HOSTILE_IDENTIFIERS:
        for field in ("name", "session"):
            kwargs = {"name": _LEGAL_NAME, "session": _LEGAL_SESSION}
            kwargs[field] = hostile_value
            fake = FakeAgentRegistry()
            try:
                await fake.register(kwargs["name"], session=kwargs["session"], role=ROLE_BUILDER)
            except Exception:  # noqa: BLE001 - ANY refusal (incl. ImportError) is the non-silent outcome
                assert fake.db.agents == {}, (
                    f"a REFUSED fake register stored a row ({field}={hostile_value!r})"
                )
                continue
            silently_registered.append(f"{field}={hostile_value!r}")
    assert not silently_registered, (
        f"the fake REGISTERED hostile identities while the shared predicate was unavailable: "
        f"{silently_registered} — a surviving guard turns 'predicate absent' into 'skip the check', whatever "
        f"its except-clause spells (amendment-5 FORK-C / amendment-6 MP-3). Fix: delete the HEAD-RED guard; "
        f"import the predicate at module top (``from lorerunes import is_legal_identifier``). Removed at: "
        f"{[f'{module_name}.{attribute}' for module_name, _module, attribute in lorerunes_homes]}"
    )


# r4a (amendment-9 MP-R4-5, reading (b) — the presence property RESTORED, property-shaped): ALLOWLIST THE SAFE
# post-build state instead of enumerating the forbidden spellings (the r3 pin keyed on ``except ImportError``
# and so could never see ``except Exception``, a bare ``except:`` or a fallback — adversary-r3 X3).
_PREDICATE_NAME = "is_legal_identifier"


def _is_lorerunes_module(module_name: str | None) -> bool:
    """``lorerunes`` itself or one of its submodules (never a sibling such as ``lorerunes_x``) — the ONE
    home test shared by the effect pin's binding sweep and the shape pin's import scan."""
    return module_name is not None and (
        module_name == _PATTERN_HOME_MEMBER or module_name.startswith(f"{_PATTERN_HOME_MEMBER}.")
    )


def _is_lorerunes_import(node: ast.AST) -> bool:
    """An ``import lorerunes…`` or a level-0 ``from lorerunes… import …`` statement."""
    if isinstance(node, ast.Import):
        return any(_is_lorerunes_module(alias.name) for alias in node.names)
    return isinstance(node, ast.ImportFrom) and node.level == 0 and _is_lorerunes_module(node.module)


def _fake_predicate_import_violations(tree: ast.Module) -> list[str]:
    """How ``tree`` departs from the ONE safe post-build shape of the fake's predicate import: (i) a
    MODULE-LEVEL ``from lorerunes… import is_legal_identifier`` (a direct child of the module body — never
    inside a function, an ``if`` or a ``try``), AND (ii) NO ``try`` node anywhere in the file wraps any
    import from ``lorerunes*``, AND (iii) — r4b, amendment-11 MP-A1, an ALLOWLIST — the NAME
    ``is_legal_identifier`` occurs in exactly two shapes: that ONE module-top import alias, and bare
    ``Name`` READS (``ast.Load`` — every one resolves to the module-top binding). Every OTHER occurrence is a
    violation naming its line: an ``Attribute`` (``lorerunes.is_legal_identifier``), ANY string constant
    equal to the name (which is how ``getattr`` / ``hasattr`` / ``vars(…).get`` / ``sys.modules[…]`` /
    ``importlib`` lookups all spell it), any other import alias or ``as`` rebinding, a ``Name`` that
    STORES or DELETES (a rebind to a private rule), a parameter, ``def``, ``global`` or ``except … as`` of
    that name. Clause (iii) is receiver-blind: it inspects every string-valued field of every AST node, so
    there is no list of forbidden node types to extend. AND (iv) — r4b-fix, amendment 13 §W-5 (a STATIC twin;
    KB-FXt is CLOSED by the effect leg, amendment 15): no bare ``Name`` of the predicate occurs INSIDE any
    ``try`` (its body, its handlers, its ``else`` / ``finally``; ``try`` and ``try*``) — a ``try`` around the
    shared decision is where a SECOND decision hides, in an ``except`` handler that never names the predicate
    (adversary-r4b FXt: ``try: legal = is_legal_identifier(value)`` / ``except Exception:`` → a PRIVATE regex
    decides; full suite 11486/0 at r4b). Empty list ⇒ safe.

    Scope, stated honestly (the r4a sentence "the ``try`` is the tell: it subsumes … FXf (any fallback)"
    over-claimed — adversary-r4a FXh, a ``try``-free ``getattr`` with a NON-silent private fallback,
    falsified it): (ii) catches X3 / X3b / FXf / FXg / a bare ``except:``; (iii) catches FXh, X3d and every
    lookup that SPELLS the name; (iv) catches FXt wherever the guarded call NAMES the predicate.
    STATIC REACH — THE EFFECT LEG IS THE ∀ (amendment 15): these clauses are the TEACHING TWINS that tell a
    builder WHICH line broke the shape; they cannot see a lookup that never spells the name in one token
    (an OBFUSCATED name —
    ``test_the_STATIC_allowlist_cannot_see_an_OBFUSCATED_predicate_name_the_effect_leg_does``)
    nor a ``try`` around a local ALIAS of the predicate (FXt on the uncollapsed helper —
    REPORT-contract-63c-i-a-r4b-fix §FORK F5-REACH). The runtime property — the shared decision is REACHED
    and TRUSTED — is
    ``test_the_fake_PROPAGATES_the_shared_decision_on_a_LEGAL_identity_once_the_predicate_exists``,
    which kills both. Neither this scanner nor the effect leg may be deleted on the belief that the other
    covers it.
    ⚠ NOT COVERED HERE, and covered ELSEWHERE — do not delete those pins believing this allowlist covers it:
    a STAR-IMPORT SHADOW placed after the honest import (``from _private_rules import *`` rebinding the name
    without ever spelling it — adversary-r4b FXs) is invisible to every clause above. It is killed by the
    r3/r4 SHARING pins (``TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA::
    test_the_identifier_decision_is_the_SHARED_is_legal_identifier`` ``[name-fake]`` / ``[session-fake]``,
    measured by adversary-r4b §4), which patch THE shared object and watch the fake follow it."""
    violations: list[str] = []
    top_level = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.level == 0
        and _is_lorerunes_module(node.module)
        and any(alias.name == _PREDICATE_NAME for alias in node.names)
    ]
    if not top_level:
        violations.append(
            f"no MODULE-LEVEL `from lorerunes import {_PREDICATE_NAME}` (a call-time or conditional read "
            f"is a guard's premise waiting to outlive it)"
        )
    violations.extend(_predicate_name_occurrence_violations(tree, top_level))
    try_types = tuple(kind for kind in (ast.Try, getattr(ast, "TryStar", None)) if kind is not None)
    for try_node in ast.walk(tree):
        if not isinstance(try_node, try_types):
            continue
        for inner in ast.walk(try_node):
            if _is_lorerunes_import(inner):
                violations.append(
                    f"line {getattr(inner, 'lineno', 0)}: a `try` (line {getattr(try_node, 'lineno', 0)}) "
                    f"wraps a lorerunes "
                    f"import: {ast.unparse(inner)}"
                )
            # clause (iv) — r4b-fix (amendment 13 §W-5): the predicate's Name anywhere inside ANY `try`.
            if isinstance(inner, ast.Name) and inner.id == _PREDICATE_NAME:
                violations.append(
                    f"line {getattr(inner, 'lineno', 0)}: `{_PREDICATE_NAME}` occurs INSIDE a `try` (line "
                    f"{getattr(try_node, 'lineno', 0)}) — an `except` around the shared decision is where a "
                    f"second, private decision hides (adversary-r4b FXt)"
                )
    return violations


def _predicate_name_occurrence_violations(tree: ast.Module, top_level: list[ast.ImportFrom]) -> list[str]:
    """Clause (iii) of ``_fake_predicate_import_violations`` (amendment-11 MP-A1): every occurrence of the
    predicate's name OUTSIDE the two allowed shapes, one entry per occurrence, naming its line. An
    occurrence is ANY string-valued field of ANY AST node equal to the name (``ast.iter_fields`` — a
    ``Name.id``, an ``Attribute.attr``, a ``Constant.value``, an ``alias.name``/``asname``, an ``arg.arg``, a
    ``FunctionDef.name``, a ``Global.names`` entry, an ``ExceptHandler.name`` …) — receiver-blind, so the
    safe set is what is enumerated, never the forbidden one. Allowed: (1) the name in the FIRST module-top
    import alias that names it WITHOUT an ``as`` rebinding (a second such alias is a second route); (2) a
    ``Name`` in ``ast.Load`` context."""
    allowed_alias: ast.alias | None = None
    for import_node in top_level:
        for alias in import_node.names:
            if allowed_alias is None and alias.name == _PREDICATE_NAME and alias.asname is None:
                allowed_alias = alias
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            continue  # shape (2): a bare read of the module-top binding
        if node is allowed_alias:
            continue  # shape (1): THE module-top import
        for field_name, value in ast.iter_fields(node):
            values = value if isinstance(value, list) else [value]
            if any(isinstance(item, str) and item == _PREDICATE_NAME for item in values):
                line = getattr(node, "lineno", 0)  # alias / arg / keyword carry their own lineno on 3.10+
                violations.append(
                    f"line {line}: `{_PREDICATE_NAME}` occurs as {type(node).__name__}.{field_name} — only "
                    f"the ONE module-top import and bare Name READS may name the shared predicate "
                    f"(a lookup, an attribute re-read, a rebind or a second import is a second route to the "
                    f"identity decision): {_unparse_or_type(node)}"
                )
    return violations


def _unparse_or_type(node: ast.AST) -> str:
    """``ast.unparse`` for a node that has a source form, else its type name (an ``ExceptHandler`` or a
    bare ``arg`` still renders; this is only for the violation text)."""
    try:
        return ast.unparse(node)
    except (AttributeError, TypeError, ValueError):
        return type(node).__name__


def test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists() -> None:
    """⚠ RED on the build until the builder deletes the HEAD-RED guard AND imports the predicate at module
    top (its one granted test-tree edit — the builder brief names exactly this shape). amendment-9 MP-R4-5
    (restores the property amendment-6 MP-3's deletion lost — see the ERRATUM above the effect pin): once
    ``lorerunes.is_legal_identifier`` EXISTS, ``_comms_fakes.py`` has a module-level ``ImportFrom`` of it and
    no ``try`` wraps any ``lorerunes*`` import (adversary-r4 FXf: a guard with a private-regex fallback; FXg:
    the submodule import inside a ``try`` — both full-suite survivors of r4).
    r4b (amendment-11 MP-A1 — ERRATUM: the r4a sentence here, "the HEAD-RED guard cannot outlive its premise
    in ANY spelling, silent or not", over-claimed; adversary-r4a FXh, a ``try``-free call-time
    ``getattr(lorerunes, "is_legal_identifier", None)`` with a NON-silent private fallback, survived the
    full suite with this pin and the effect pin green): clause (iii) is an ALLOWLIST — the name occurs only
    as that ONE module-top import and as bare ``Name`` reads; any other occurrence (an attribute re-read, a
    string constant spelling it, a rebind, a second import) is a violation. What it covers, precisely:
    every guard that SPELLS the predicate's name. STATIC REACH — THE EFFECT LEG IS THE ∀ (amendment 15):
    an OBFUSCATED name and a ``try`` around a local alias are outside this pin's reach and inside
    ``test_the_fake_PROPAGATES_the_shared_decision_on_a_LEGAL_identity_once_the_predicate_exists``'s
    (r4b-fix; the amendment-11 obfuscation KNOWN BOUND is CLOSED by that leg). The effect pin above stays
    for the SILENT-skip property (adversary-r4a FXhS proves it fires). Three pins, three
    properties; none may be deleted believing another covers it.

    HEAD CONTROL (anti-vacuity): while the predicate is ABSENT the guard is legitimate (amendment-5 FORK-C),
    and this scanner must SEE it — at HEAD the file's guarded call-time import is reported as a violation.
    Synthetic controls: ``test_the_fake_import_shape_scanner_*`` below."""
    import _comms_fakes

    import lorerunes

    source = Path(_comms_fakes.__file__).read_text(encoding="utf-8")
    violations = _fake_predicate_import_violations(ast.parse(source))
    if getattr(lorerunes, _PREDICATE_NAME, None) is None:
        assert any("wraps a lorerunes import" in violation for violation in violations), (
            "CONTROL: at HEAD (predicate absent) the fake's HEAD-RED guard is a `try` around a lorerunes "
            f"import, and the scanner must SEE it — it reported {violations!r}"
        )
        return
    assert not violations, (
        "the fake's HEAD-RED guard outlived its premise (amendment-5 FORK-C removal trigger; amendment-9 "
        "MP-R4-5; amendment-11 MP-A1): once lorerunes.is_legal_identifier exists, _comms_fakes.py must "
        "import it at MODULE TOP with NO `try` around any lorerunes import, and name it NOWHERE else but "
        "bare reads — any guard, whatever it catches, looks up or falls back to, is a second path to an "
        "identity decision:\n  " + "\n  ".join(violations)
    )


class _SharedDecisionReached(Exception):  # noqa: N818 - a sentinel, not an error condition
    """r4b-fix (amendment 15): raised by the stub that replaces THE shared predicate — proof the shared
    decision was REACHED. The fake must PROPAGATE it; swallowing it is a second decision."""


@pytest.mark.parametrize("field", ["name", "session"])
async def test_the_fake_PROPAGATES_the_shared_decision_on_a_LEGAL_identity_once_the_predicate_exists(
    monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    """r4b-fix (amendment 15 — FORK F5-REACH ruled (b); KB-FXt CLOSED; amendment-11's obfuscation bound
    CLOSED): the property is RUNTIME — the shared decision's outcome IS the fake's outcome. THE shared
    predicate is replaced, at every module-level binding of THE object (``patch_shared_object_everywhere``,
    ``expect_in`` its ``lorerunes`` home), by a stub that RAISES a sentinel for ONE field's LEGAL value (and
    delegates for every other value). A fake ``register`` of that LEGAL identity must PROPAGATE the sentinel:
    no ``except`` may swallow the shared decision, whatever it wraps (a direct call, a local alias of the
    helper's return, an obfuscated lookup) and whatever the handler spells. ∀ fields (name, session — a
    ``try`` around ONE field's check is caught on that field). Kills adversary-r4b FXt on BOTH helper shapes
    (the uncollapsed helper's alias and the collapsed direct call); both honest shapes stay GREEN (the
    exception propagates through an alias exactly as through a direct call). Wider than FXt by design: a fake
    that never CONSULTS the shared predicate for a legal-looking value does not raise either → RED. The
    static twins (the allowlist, clause (iv)) tell a builder WHICH line broke the shape; this leg is the ∀.

    HEAD CONTROL (anti-vacuity, the same early return as the silent-skip effect pin): while the predicate is
    ABSENT the fake's guard is legitimate (amendment-5 FORK-C), and the hostile ``"fixer-b\\n"`` DOES
    register — the instrument can see a skipped decision."""
    import lorerunes

    shared_predicate = getattr(lorerunes, "is_legal_identifier", None)
    if shared_predicate is None:
        fake = FakeAgentRegistry()
        await fake.register(_FAKE_SKIP_HEAD_CONTROL, session=_LEGAL_SESSION, role=ROLE_BUILDER)
        assert len(fake.db.agents) == 1, (
            "CONTROL: at HEAD (predicate absent) the fake's guard must visibly SKIP the identity leg — "
            "otherwise this instrument cannot observe a skipped shared decision"
        )
        return
    target = _LEGAL_NAME if field == "name" else _LEGAL_SESSION
    assert shared_predicate(target), f"CONTROL: the {field} witness {target!r} must be LEGAL"

    def _raising_stub(value: str) -> bool:
        if value == target:
            raise _SharedDecisionReached(f"THE shared predicate was consulted for the {field} {value!r}")
        return bool(shared_predicate(value))

    patched = patch_shared_object_everywhere(
        monkeypatch, "is_legal_identifier", shared_predicate, _raising_stub
    )
    fake = FakeAgentRegistry()
    outcome: str | None = "returned normally — the fake REGISTERED the identity"
    try:
        await fake.register(_LEGAL_NAME, session=_LEGAL_SESSION, role=ROLE_BUILDER)
    except _SharedDecisionReached:
        outcome = None
    except Exception as error:  # noqa: BLE001 - any OTHER outcome is the finding; name it
        outcome = f"raised {type(error).__name__} instead: {error}"
    assert outcome is None, (
        f"the fake did not PROPAGATE the shared decision for the LEGAL {field} {target!r}: it {outcome}. "
        f"An `except` around the shared decision (a direct call OR a local alias of it) is a SECOND, private "
        f"decision (amendment 15 / adversary-r4b FXt), and a fake that never consults the shared predicate "
        f"is routing without sharing. Patched: {patched}"
    )
    assert fake.db.agents == {}, f"a fake register that raised stored a row: {fake.db.agents!r}"


_GUARDED_CALL_TIME_IMPORT = (
    "from lorerunes import is_blank\n"
    "def predicate():\n"
    "    try:\n"
    "        from lorerunes{module} import is_legal_identifier\n"
    "    {handler}\n"
    "        {fallback}\n"
    "    return is_legal_identifier\n"
)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            _GUARDED_CALL_TIME_IMPORT.format(
                module="", handler="except ImportError:", fallback="return None"
            ),
            id="X3b-the-ruled-spelling",
        ),
        pytest.param(
            _GUARDED_CALL_TIME_IMPORT.format(
                module="", handler="except Exception:  # noqa: BLE001", fallback="return None"
            ),
            id="X3-except-Exception",
        ),
        pytest.param(
            _GUARDED_CALL_TIME_IMPORT.format(
                module="", handler="except:  # noqa: E722", fallback="return None"
            ),
            id="bare-except",
        ),
        pytest.param(
            _GUARDED_CALL_TIME_IMPORT.format(
                module=".identifiers", handler="except ImportError:", fallback="return None"
            ),
            id="FXg-submodule-import-inside-a-try",
        ),
        pytest.param(
            _GUARDED_CALL_TIME_IMPORT.format(
                module="",
                handler="except ImportError:",
                fallback='return lambda value: re.fullmatch(r"[a-z]+", value) is not None',
            ),
            id="FXf-non-silent-fallback",
        ),
        pytest.param(
            "from lorerunes import is_blank, is_legal_identifier\n"
            + _GUARDED_CALL_TIME_IMPORT.format(
                module="", handler="except ImportError:", fallback="return None"
            ),
            id="module-top-import-AND-a-guarded-call-time-import",
        ),
        pytest.param(
            "try:\n    from lorerunes import is_legal_identifier\nexcept ImportError:\n"
            "    is_legal_identifier = None\n",
            id="module-level-import-inside-a-try",
        ),
        pytest.param(
            "import lorerunes\ndef predicate():\n"
            "    return getattr(lorerunes, 'is_legal_identifier', None)\n",
            id="X3d-getattr-no-module-level-import",
        ),
    ],
)
def test_the_fake_import_shape_scanner_names_every_guard_POSITIVE_CONTROL(source: str) -> None:
    """Each departure from the safe shape an honest builder could plausibly leave behind is REPORTED — so
    a green real-file scan is a statement about the file, not about a blind scanner (a probe needs a
    control). X3d is caught here by clause (i) (no module-level import), and by the effect pin besides."""
    assert _fake_predicate_import_violations(ast.parse(source)), source


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            "from lorerunes import is_blank, is_legal_identifier\n"
            "def predicate():\n    return is_legal_identifier\n",
            id="the-safe-shape-module-top-import",
        ),
        pytest.param(
            "from lorerunes.identifiers import is_legal_identifier\n"
            "try:\n    import yaml\nexcept ImportError:\n    yaml = None\n",
            id="submodule-top-import-and-an-unrelated-try",
        ),
        # r4b (amendment-11 MP-A1): THE HONEST POST-BUILD FAKE — the builder's granted edit applied to the
        # real helper (guard deleted, module-top import) leaves a bare ``return is_legal_identifier`` and a
        # call through the returned object, beside docstring PROSE that mentions the dotted name. None of
        # it may be flagged (FORK-R3: this is why shape (2) is every Load-context Name, not only a Call).
        pytest.param(
            "from lorerunes import is_blank, is_legal_identifier\n"
            "class FakeAgentRegistry:\n"
            "    @staticmethod\n"
            "    def _shared_identifier_predicate():\n"
            '        """Reads ``lorerunes.is_legal_identifier`` — the ONE shared decision."""\n'
            "        return is_legal_identifier\n"
            "    @staticmethod\n"
            "    def _refuse(name, session):\n"
            "        identifier_decision = FakeAgentRegistry._shared_identifier_predicate()\n"
            "        if identifier_decision is not None:\n"
            "            for value in (name, session):\n"
            "                if not identifier_decision(value):\n"
            "                    raise ValueError('illegal')\n"
            "        if not is_legal_identifier(name) or is_blank(session):\n"
            "            raise ValueError('illegal')\n",
            id="the-honest-post-build-fake",
        ),
        # r4b (amendment-12 — FORK-R3 ruled R-3a): the SECOND honest post-build shape — the builder MAY
        # collapse the helper to a direct call in REFACTOR; both shapes must stay quiet.
        pytest.param(
            "from lorerunes import is_blank, is_legal_identifier\n"
            "class FakeAgentRegistry:\n"
            "    @staticmethod\n"
            "    def _refuse(name, session, role):\n"
            "        for value in (name, session):\n"
            "            if not is_legal_identifier(value):\n"
            "                raise ValueError('illegal')\n"
            "        if is_blank(role):\n"
            "            raise ValueError('blank role')\n",
            id="the-collapsed-direct-call-post-build-fake",
        ),
        # r4b-fix (amendment 13 §W-5 — clause (iv)'s negatives): BOTH honest shapes beside an UNRELATED
        # ``try`` that never names the predicate (a gate that refuses every ``try`` refuses honest code).
        pytest.param(
            "from lorerunes import is_blank, is_legal_identifier\n"
            "class FakeAgentRegistry:\n"
            "    @staticmethod\n"
            "    def _shared_identifier_predicate():\n"
            "        return is_legal_identifier\n"
            "    @staticmethod\n"
            "    def _refuse(name, session, limit):\n"
            "        try:\n"
            "            bound = int(limit)\n"
            "        except ValueError:\n"
            "            bound = 0\n"
            "        identifier_decision = FakeAgentRegistry._shared_identifier_predicate()\n"
            "        for value in (name, session):\n"
            "            if not identifier_decision(value) or bound < 0:\n"
            "                raise ValueError('illegal')\n",
            id="the-honest-post-build-fake-beside-an-unrelated-try",
        ),
        pytest.param(
            "from lorerunes import is_blank, is_legal_identifier\n"
            "class FakeAgentRegistry:\n"
            "    @staticmethod\n"
            "    def _refuse(name, session, role):\n"
            "        for value in (name, session):\n"
            "            if not is_legal_identifier(value):\n"
            "                raise ValueError('illegal')\n"
            "        try:\n"
            "            role.encode('ascii')\n"
            "        except UnicodeEncodeError:\n"
            "            raise ValueError('role') from None\n",
            id="the-collapsed-post-build-fake-beside-an-unrelated-try",
        ),
    ],
)
def test_the_fake_import_shape_scanner_stays_quiet_on_the_safe_shape_NEGATIVE_CONTROL(source: str) -> None:
    """A gate that refuses honest code gets switched off: the ruled safe shape — a module-top import (from
    the package or its defining submodule) and a ``try`` that guards something OTHER than ``lorerunes`` —
    is never flagged."""
    assert _fake_predicate_import_violations(ast.parse(source)) == [], source


# r4b (amendment-11 MP-A1 — clause (iii), the fake predicate ALLOWLIST): every source below carries the
# HONEST module-top import and NO ``try`` around a lorerunes import, so clauses (i) and (ii) are satisfied
# and ONLY clause (iii) can report it — the assertion keys on clause (iii)'s own text, so a positive here
# proves the NEW clause fired, not an old one. FXh is adversary-r4a's full-suite survivor, verbatim shape.
_HONEST_TOP_IMPORT = "import lorerunes\nfrom lorerunes import is_blank, is_legal_identifier\n"
_PRIVATE_RULE = "lambda value: re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', value) is not None"


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            _HONEST_TOP_IMPORT + "def predicate():\n"
            "    if getattr(lorerunes, 'is_legal_identifier', None) is not None:\n"
            "        return is_legal_identifier\n"
            f"    return {_PRIVATE_RULE}\n",
            id="FXh-getattr-with-a-non-silent-fallback-no-try",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + "def predicate():\n"
            "    return getattr(lorerunes, 'is_legal_identifier', None)\n",
            id="X3d-getattr-beside-a-module-top-import",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + "def predicate():\n"
            "    return vars(lorerunes).get('is_legal_identifier') or is_blank\n",
            id="vars-read",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + "import sys\ndef predicate():\n"
            "    return sys.modules['lorerunes'].__dict__.get('is_legal_identifier')\n",
            id="sys-modules-read",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + "import importlib\ndef predicate():\n"
            "    return importlib.import_module('lorerunes').is_legal_identifier\n",
            id="importlib-attribute-read",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + "def predicate():\n"
            "    return is_legal_identifier if hasattr(lorerunes, 'is_legal_identifier') else None\n",
            id="hasattr-probe",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + "def predicate():\n    return lorerunes.is_legal_identifier\n",
            id="attribute-re-read",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + f"is_legal_identifier = {_PRIVATE_RULE}\n",
            id="module-global-REBOUND-to-a-private-rule",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + f"def predicate(is_legal_identifier={_PRIVATE_RULE}):\n"
            "    return is_legal_identifier\n",
            id="parameter-shadows-the-predicate",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + "def predicate():\n"
            "    from lorerunes import is_legal_identifier as _fresh  # noqa: PLC0415\n"
            "    return _fresh\n",
            id="a-second-import-inside-a-function-no-try",
        ),
        pytest.param(
            "from lorerunes import is_blank\n"
            "from lorerunes import is_legal_identifier as shared_check\n"
            f"is_legal_identifier = {_PRIVATE_RULE}\n",
            id="module-top-import-REBOUND-by-as-then-the-name-reused",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + "def predicate():\n    global is_legal_identifier\n"
            "    is_legal_identifier = None\n",
            id="global-rebind",
        ),
        # amendment-12's named RED controls beyond the r4b-provisional set: a class-body shadow and a walrus.
        pytest.param(
            _HONEST_TOP_IMPORT + "class FakeAgentRegistry:\n"
            f"    is_legal_identifier = staticmethod({_PRIVATE_RULE})\n",
            id="class-body-shadow",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + "def predicate():\n"
            f"    if (is_legal_identifier := {_PRIVATE_RULE}):\n"
            "        return is_legal_identifier\n",
            id="walrus-rebind",
        ),
    ],
)
def test_the_fake_predicate_ALLOWLIST_names_every_other_occurrence_POSITIVE_CONTROL(source: str) -> None:
    """r4b (amendment-11 MP-A1) — clause (iii) of ``_fake_predicate_import_violations`` reports each shape
    that is neither THE module-top import nor a bare ``Name`` read, and names it as an OCCURRENCE (its own
    text, so clauses (i)/(ii) cannot answer for it). The amendment's named positives are FXh, X3d, FXf, FXg
    and a ``vars(…)`` read — FXf and FXg are clause (ii)'s and live in
    ``test_the_fake_import_shape_scanner_names_every_guard_POSITIVE_CONTROL``; the rest are here, with the
    other lookups and rebinds the allowlist denies by construction (it enumerates the SAFE set)."""
    violations = _fake_predicate_import_violations(ast.parse(source))
    assert any(f"`{_PREDICATE_NAME}` occurs as" in violation for violation in violations), (
        f"clause (iii) did not name an occurrence outside the allowlist: {violations!r}\n{source}"
    )


# r4b-fix (amendment 13 §W-5 — clause (iv), the STATIC twin of amendment 15's effect leg): every source below
# carries the HONEST module-top import, names the predicate ONLY as bare Load ``Name`` reads (clause (iii)
# satisfied) and wraps no lorerunes import (clause (ii)) — ONLY clause (iv) can report it, and the assertion
# keys on clause (iv)'s own text. The first is adversary-r4b's full-suite survivor FXt in its direct-call
# form.
_FXT_PRIVATE_FALLBACK = f"({_PRIVATE_RULE})(value)"  # REUSES the file's one private-rule fixture


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            _HONEST_TOP_IMPORT + "import re\ndef refuse(value):\n"
            "    try:\n"
            "        legal = is_legal_identifier(value)\n"
            "    except Exception:\n"
            f"        legal = {_FXT_PRIVATE_FALLBACK}\n"
            "    if not legal:\n"
            "        raise ValueError('illegal')\n",
            id="FXt-try-around-the-call-private-fallback-in-the-handler",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + "import re\ndef refuse(value):\n"
            "    try:\n"
            f"        legal = {_FXT_PRIVATE_FALLBACK}\n"
            "    except re.error:\n"
            "        legal = is_legal_identifier(value)\n"
            "    if not legal:\n"
            "        raise ValueError('illegal')\n",
            id="private-rule-first-the-shared-predicate-only-in-the-handler",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + "import re\ndef refuse(value):\n"
            "    try:\n"
            "        legal = is_legal_identifier(value)\n"
            "    except* Exception:\n"
            f"        legal = {_FXT_PRIVATE_FALLBACK}\n"
            "    if not legal:\n"
            "        raise ValueError('illegal')\n",
            id="FXt-except-star-form",
        ),
    ],
)
def test_the_fake_predicate_is_never_named_inside_a_TRY_POSITIVE_CONTROL(source: str) -> None:
    """r4b-fix (amendment 13 §W-5) — clause (iv) of ``_fake_predicate_import_violations`` reports the
    predicate's ``Name`` inside any ``try`` (body, handlers, ``else``, ``finally``; ``try`` and ``try*``),
    naming its own text so clauses (i)–(iii) cannot answer for it. The negatives — both honest post-build
    shapes beside an UNRELATED ``try``, and R-A (ii)'s submodule import beside one — live in
    ``test_the_fake_import_shape_scanner_stays_quiet_on_the_safe_shape_NEGATIVE_CONTROL``. STATIC REACH —
    THE EFFECT LEG IS THE ∀ (amendment 15): clause (iv) sees a ``try`` only where the guarded call NAMES the
    predicate, so it is blind to FXt on the UNCOLLAPSED helper (the ``try`` wraps a local alias —
    REPORT-contract-63c-i-a-r4b-fix §FORK F5-REACH, measured);
    ``test_the_fake_PROPAGATES_the_shared_decision_on_a_LEGAL_identity_once_the_predicate_exists``
    kills FXt on both shapes."""
    violations = _fake_predicate_import_violations(ast.parse(source))
    assert any("occurs INSIDE a `try`" in violation for violation in violations), (
        f"clause (iv) did not name the predicate inside a `try`: {violations!r}\n{source}"
    )
    assert not any(f"`{_PREDICATE_NAME}` occurs as" in violation for violation in violations), (
        f"CONTROL: clause (iii) fired too, so this source does not isolate clause (iv): {violations!r}"
    )


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            _HONEST_TOP_IMPORT + "def predicate():\n"
            "    shared = getattr(lorerunes, 'is_legal_' + 'identifier', None)\n"
            f"    return shared if shared is not None else {_PRIVATE_RULE}\n",
            id="concatenated-name",
        ),
        pytest.param(
            _HONEST_TOP_IMPORT + "def predicate():\n"
            "    return vars(lorerunes).get(''.join(['is_legal', '_identifier']))\n",
            id="joined-name",
        ),
    ],
)
# DUAL (r4b-fix, amendment 15 — RE-KEYED, renamed from
# ``test_KNOWN_BOUND_an_OBFUSCATED_predicate_name_is_NOT_named``): this control asserted the amendment-11
# obfuscation KNOWN BOUND (the hole EXISTS; RED the day someone closes it; re-open trigger #138's
# threat-model change). The bound is CLOSED by
# ``test_the_fake_PROPAGATES_the_shared_decision_on_a_LEGAL_identity_once_the_predicate_exists``
# — an obfuscated lookup still reads THE patched object, meets the raising stub, and is caught if
# swallowed. Virtue kept: the
# control still documents the STATIC allowlist's reach (it stays quiet on an assembled name — a builder
# learns what the shape scanner can and cannot tell them). Dropped deliberately: the KNOWN-BOUND message and
# its re-open trigger (a closed bound carries no trigger).
def test_the_STATIC_allowlist_cannot_see_an_OBFUSCATED_predicate_name_the_effect_leg_does(
    source: str,
) -> None:
    """The STATIC allowlist's reach, documented (amendment 15): a lookup whose name is ASSEMBLED at runtime
    never spells ``is_legal_identifier`` in one token, so the shape scanner stays quiet on it. That is not a
    hole in the suite —
    ``test_the_fake_PROPAGATES_the_shared_decision_on_a_LEGAL_identity_once_the_predicate_exists``
    observes the runtime property and kills it. The allowlist cannot see this spelling; the effect leg
    does."""
    assert _fake_predicate_import_violations(ast.parse(source)) == [], (
        "the STATIC allowlist now names an ASSEMBLED predicate name — its reach grew. If that was "
        f"deliberate, update this reach control (the effect leg is the ∀ either way):\n{source}"
    )
