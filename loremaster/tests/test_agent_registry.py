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

import asyncio
import inspect
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

import pytest
import pytest_asyncio
from _comms_fakes import FakeAgentDatabase, FakeAgentRegistry
from _governed_contract import patch_shared_object_everywhere
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
from test_comms_schema import _HOSTILE_IDENTIFIERS

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

    @pytest.mark.parametrize("valid_value", ["fixer-b", "a", "wave7", "z" * 64])
    async def test_register_accepts_a_valid_identifier_positive_control(self, valid_value: str) -> None:
        """POSITIVE CONTROL (fixtures-must-discriminate) — a build whose MOVE charset guard is too
        strict would refuse every real caller while passing the negative pins. A valid name/session
        registers and writes exactly one row. GREEN at HEAD AND on the correct build."""
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

    @pytest.mark.parametrize("field", ["name", "session"])
    async def test_the_identifier_decision_is_the_SHARED_is_legal_identifier(
        self, monkeypatch: pytest.MonkeyPatch, field: str
    ) -> None:
        """⚠ RED before i-a (``lorerunes.is_legal_identifier`` does not exist). ONE DECISION, proven BY
        MUTATION (A4; WB11 is the routing-not-sharing build this kills): perturb the SHARED predicate —
        in EVERY loaded module holding that object — to reject ONE normally-legal value, the target
        field's; ``register`` must refuse it (per FIELD, so a build that routes ``name`` through the
        predicate and ``session`` through a private ``AGENT_NAME_PATTERN.fullmatch`` reds on the
        ``session`` leg — sidecar F6), AND the TOOL-layer ``AppContext._validate_comms_charset`` must
        refuse it too (the same decision, two consumers). BASELINE leg first: unpatched, both accept."""
        from loremaster.server import AppContext

        import lorerunes

        target = _LEGAL_NAME if field == "name" else _LEGAL_SESSION
        shared_predicate = lorerunes.is_legal_identifier
        registry, admin_connection, env = await self._real_registry()
        try:
            AppContext._validate_comms_charset(target, field)  # noqa: SLF001 - BASELINE: legal today
            patched = patch_shared_object_everywhere(
                monkeypatch,
                "is_legal_identifier",
                shared_predicate,
                lambda value: value != target and shared_predicate(value),
            )
            assert any(name.startswith("lorerunes") for name in patched), (
                f"the shared predicate was not found in its lorerunes home (patched: {patched})"
            )
            with pytest.raises(AgentRegistryError):
                await registry.register(_LEGAL_NAME, session=_LEGAL_SESSION, role=ROLE_BUILDER)
            assert await self._agent_row_count(admin_connection) == 0
            with pytest.raises(ValueError):
                AppContext._validate_comms_charset(target, field)  # noqa: SLF001 - the tool-layer consumer
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

        ⚠ MEASURED BOUND (r2 mutation proof WB-A4b): CPython's ``re.compile`` CACHE returns the SAME
        object for an identical pattern string, so a "private copy" in ``agents.py`` compiled from the
        IDENTICAL text is the shared object — indistinguishable here, and behaviourally identical at
        birth. The second spelling this pin reds is a DRIFTED copy (proven: a ``{0,64}`` copy reds both
        legs on the identity assertion) — the drift is the defect, and drift is what it catches."""
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
            )
            assert any(name.startswith("lorerunes") for name in patched), (
                f"AGENT_NAME_PATTERN was not found in its lorerunes home (patched: {patched})"
            )
            with pytest.raises(AgentRegistryError):
                await registry.register(_LEGAL_NAME, session=_LEGAL_SESSION, role=ROLE_BUILDER)
            assert await self._agent_row_count(admin_connection) == 0
        finally:
            await admin_connection.close()
            await registry.close()
            await drop_database(env)

    async def test_the_blank_role_rule_is_the_SHARED_is_blank(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED before i-a — ROUTING IS NOT SHARING (A4 / MP-9c, WB13: a private ``role.strip()``
        passed every r1 pin). Perturb the SHARED ``lorerunes.is_blank`` — in every loaded module holding
        that object — so a normal role (``builder``) counts as blank; ``register`` must now refuse it.
        BASELINE leg first: unpatched, ``builder`` registers (a register that never checks roles would
        otherwise 'refuse' nothing and fail only here for the wrong reason)."""
        import lorerunes

        shared_is_blank = lorerunes.is_blank
        registry, admin_connection, env = await self._real_registry()
        try:
            await registry.register("baseline-agent", session=_LEGAL_SESSION, role=ROLE_BUILDER)
            assert await self._agent_row_count(admin_connection) == 1, "BASELINE: 'builder' must register"
            patched = patch_shared_object_everywhere(
                monkeypatch,
                "is_blank",
                shared_is_blank,
                lambda value: value == ROLE_BUILDER or shared_is_blank(value),
            )
            assert patched, "lorerunes.is_blank was not found in any loaded module"
            with pytest.raises(AgentRegistryError):
                await registry.register(_LEGAL_NAME, session=_LEGAL_SESSION, role=ROLE_BUILDER)
            assert await self._agent_row_count(admin_connection) == 1, (
                "a register refused by the (mutated) shared is_blank still wrote a row"
            )
        finally:
            await admin_connection.close()
            await registry.close()
            await drop_database(env)
