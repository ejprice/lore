"""Coverage-gap closure for PKT-28 C1's comms surface: REAL WIRING, not fakes.

The three existing C1 contract files never drive the real production path:
``test_comms_tool.py`` deliberately exercises ``AppContext.comms`` against a
lightweight ``SimpleNamespace`` harness carrying fake ledgers (its own
"Contract decisions" #3 says so explicitly, and flags the gap under "Things
NOT covered"); ``test_agent_registry.py``/``test_brief_ledger.py`` drive
``AgentRegistry``/``BriefLedger`` directly, never through
:func:`~loremaster.server.build_app_context`. Consequence: ``lore_comms``
could be registered as an MCP tool while the two comms ledgers are never
constructed, never ``ensure_ready()``'d, and never torn down — and the whole
suite would stay green. This file closes that gap plus the second, related
one: ``CommsConfig`` (spec §4) is claimed by no contract file, so nothing
proves its three knobs are actually CONSUMED rather than hardcoded.

Spec: ``docs/design/2026-07-12-pkt28-c1-semantics.md`` (execute verbatim).
Everything here runs against a REAL, throwaway SurrealDB database on the
spike test store (``ws://127.0.0.1:18000`` — never :18500, production) via
:func:`~loremaster.server.build_app_context`, mirroring
``test_mcp_server.py``'s own ``cutover_ctx``/``_make_context`` idiom. This
module is independently collectible (no import from ``test_mcp_server.py``,
which is not a designed shared module — mirrors the sibling contract files'
own stated property).

None of this is wired yet: ``AppContext`` has no ``comms``/``agent_registry``/
``brief_ledger`` attributes today, and ``LoreConfig`` has no ``comms:``
section. Every test below is expected to FAIL for exactly that reason —
``AttributeError`` on ``ctx.comms``/``ctx.agent_registry``/``ctx.brief_ledger``,
a ``pydantic.ValidationError`` on a config payload carrying a ``comms:`` block,
or (for the write-stack-unwind tests) a ``Failed: DID NOT RAISE`` because the
fault-injected ledger is never constructed at all — never a collection-time
import error, since every name this file imports already exists on disk
(``loremaster.agents``/``loremaster.briefs`` landed this session; ``AppContext``/
``LoreServer``/``build_app_context`` predate this packet).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import drop_database as drop_surreal_database
from _surreal_harness import make_env, surreal_password, surreal_url, surreal_user
from loremaster.agents import AgentRegistry
from loremaster.briefs import BriefLedger
from loremaster.config import LoreConfig
from loremaster.sanitise import FENCE_CHAR, MIN_FENCE_WIDTH, max_backtick_run
from loremaster.server import AppContext, LoreServer, build_app_context
from loresigil.testing import FakeEmbedder
from render_injection_scaffold import _ROW_FORGE_PAYLOAD

# --------------------------------------------------------------------------- #
# Config / store fixture plumbing (local, deliberately not shared with
# test_mcp_server.py — mirrors the sibling contract files' independent-
# collectibility property).
# --------------------------------------------------------------------------- #

_DIM = 2048
_SURREAL_TEST_NAMESPACE = "lore_test"
_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"

# spec §4 (docs/design/2026-07-12-pkt28-c1-semantics.md): the enforceable
# fleet re-ask clamp. Hardcoded here deliberately, NOT imported from
# ``loremaster.server`` — this constant is exactly what the clamp test below
# proves the production code honours, so the test must not source its
# expectation from the same value it is checking.
_SPEC_MAX_FLEET_LIMIT = 200

# A hostile-but-modest brief body (brief-base §3: newlines + a row-forge
# payload) — well under any default warn threshold, used by the end-to-end
# arc to prove the body round-trips verbatim through the REAL store, and that
# the real ``render_fenced`` fence at the end of the arc still outruns the
# widest embedded backtick run, through production code, not a fake.
_HOSTILE_BRIEF_BODY = f"read the plan\n{_ROW_FORGE_PAYLOAD}\ntrailing line"

_pending_surreal_slugs: list[str] = []


def _slug() -> str:
    """A unique per-test project slug, also the throwaway SurrealDB database name."""
    slug = f"test_{uuid.uuid4().hex}"
    _pending_surreal_slugs.append(slug)
    return slug


@pytest_asyncio.fixture(autouse=True)
async def _surreal_test_env(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    """Export the harness's root SurrealDB credentials; reap every slug-named database."""
    monkeypatch.setenv(_SURREAL_USER_ENV, surreal_user())
    monkeypatch.setenv(_SURREAL_PASS_ENV, surreal_password())
    try:
        yield
    finally:
        for slug in _pending_surreal_slugs:
            await drop_surreal_database(make_env(database=slug, dim=_DIM))
        _pending_surreal_slugs.clear()


def _config(slug: str, *, comms: dict[str, int] | None = None) -> LoreConfig:
    """Build a minimal, valid :class:`LoreConfig` pointed at the spike test store.

    ``comms`` is passed through verbatim as the ``comms:`` payload block when
    given — this is the ONLY way this file exercises a non-default
    ``CommsConfig``, so a genuine config-wiring test never hand-constructs a
    ``CommsConfig`` object directly.
    """
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
            "url": surreal_url(),
            "namespace": _SURREAL_TEST_NAMESPACE,
            "user_env": _SURREAL_USER_ENV,
            "password_env": _SURREAL_PASS_ENV,
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
    if comms is not None:
        payload["comms"] = comms
    return LoreConfig.model_validate(payload)


async def _open_context(
    *, tmp_path: Path, comms: dict[str, int] | None = None, embedder: FakeEmbedder | None = None
) -> AppContext:
    """Build a REAL :class:`AppContext` via the genuine ``build_app_context`` wiring.

    ``start_tasks=False`` skips the watcher/initial sweep (irrelevant to comms)
    — the same test seam ``test_mcp_server.py``'s ``cutover_ctx`` uses.
    """
    slug = _slug()
    config = _config(slug, comms=comms)
    return await build_app_context(
        server=LoreServer(config),
        embedder=embedder or FakeEmbedder(dim=_DIM),
        manifest_path=tmp_path / f"{slug}-m.db",
        snapshot_root=tmp_path / f"{slug}-snap",
        start_tasks=False,
    )


@pytest_asyncio.fixture()
async def ctx(tmp_path: Path) -> AsyncIterator[AppContext]:
    """A real, default-config :class:`AppContext` over an empty corpus."""
    context = await _open_context(tmp_path=tmp_path)
    try:
        yield context
    finally:
        await context.aclose()


def _expected_fence(body: str) -> str:
    """The exact fence delimiter :func:`~loremaster.render.render_fenced` must
    produce for ``body`` — strictly longer than any backtick run embedded in it."""
    return FENCE_CHAR * max(MIN_FENCE_WIDTH, max_backtick_run(body) + 1)


def _fleet_row(rendered: str, name: str) -> str:
    """The single fleet row line for ``name`` — fails loudly if not exactly one."""
    prefix = f"- {name} ["
    matches = [line for line in rendered.splitlines() if line.startswith(prefix)]
    assert len(matches) == 1, (
        f"expected exactly one fleet row starting with {prefix!r}, found "
        f"{len(matches)}: {matches!r}"
    )
    return matches[0]


async def _backdate_heartbeat(ctx: AppContext, *, name: str, session: str, seconds_ago: int) -> None:
    """Directly rewrite an agent's ``heartbeat_at`` into the past via the real store.

    ``touch()`` always stamps ``now()`` — this is the only way to
    deterministically manufacture a stale row without a real-time sleep.
    """
    agent_id = AgentRegistry._agent_id(session, name)  # noqa: SLF001 - test-only id recipe reuse
    backdated = datetime.now(UTC) - timedelta(seconds=seconds_ago)
    await ctx.agent_registry._query(  # noqa: SLF001 - test-only raw write
        "UPDATE type::record('agent', $id) SET heartbeat_at = $ts",
        {"id": agent_id, "ts": backdated},
    )


async def _seed_extra_agents(ctx: AppContext, *, session: str, count: int) -> None:
    """Bulk-INSERT ``count`` minimal, non-retired agent rows directly.

    Bypasses ``register()``'s per-call round trip — the fleet-clamp test only
    needs realistic ROWS to count/elide/clamp over, not registry behaviour.
    """
    now = datetime.now(UTC)
    rows = [
        {
            "name": f"seed-{index}",
            "session": session,
            "role": "builder",
            "status": "active",
            "registered_at": now,
            "heartbeat_at": now,
        }
        for index in range(count)
    ]
    await ctx.agent_registry._query(  # noqa: SLF001 - test-only bulk seed
        "INSERT INTO agent $rows", {"rows": rows}
    )


# =========================================================================== #
# A — wiring is real: build_app_context constructs + readies both ledgers
# =========================================================================== #


class TestAgentRegistryAndBriefLedgerAreConstructed:
    """``build_app_context`` must construct + ``ensure_ready()`` an
    ``AgentRegistry`` and a ``BriefLedger`` — the eager two-call
    ``TaskLedger``/``FindingLedger`` pattern (server.py:4660-4680) — or the
    entire ``lore_comms`` surface silently has nothing behind it while every
    other test suite stays green."""

    async def test_app_context_exposes_a_real_agent_registry(self, ctx: AppContext) -> None:
        registry = ctx.agent_registry
        assert isinstance(registry, AgentRegistry)

    async def test_app_context_exposes_a_real_brief_ledger(self, ctx: AppContext) -> None:
        ledger = ctx.brief_ledger
        assert isinstance(ledger, BriefLedger)


class TestSchemaIsActuallyAppliedNotJustConstructed:
    """Constructing the ledgers is necessary but not sufficient —
    ``ensure_ready()`` must actually have RUN and applied the SCHEMAFULL DDL
    (spec §0), or the schema-level charset/non-empty ASSERTs (defense-in-depth
    behind the dispatcher's app-side pre-validation) are silently absent.
    Proven by exercising the ASSERT itself against a value the LEDGER layer
    deliberately does not validate (``REPORT-c1-contract-ledgers.md`` contract
    decisions #5/#6) — a real ``SurrealStoreError`` here is possible only if
    the DDL was genuinely applied on THIS connection."""

    async def test_agent_registry_charset_assert_is_enforced_by_the_applied_schema(
        self, ctx: AppContext
    ) -> None:
        from loremaster.store._txn import SurrealStoreError

        with pytest.raises(SurrealStoreError):
            await ctx.agent_registry.register(
                "Not A Legal Name!", session="wave7", role="builder"
            )

    async def test_brief_ledger_non_empty_body_assert_is_enforced_by_the_applied_schema(
        self, ctx: AppContext
    ) -> None:
        from loremaster.store._txn import SurrealStoreError

        await ctx.agent_registry.register(
            "lead", session="wave7", role="lead"
        )
        with pytest.raises(SurrealStoreError):
            await ctx.brief_ledger.publish(
                "project", "", created_by="lead"
            )


class TestWriteStackUnwindIncludesCommsLedgers:
    """Construction-time partial-failure guard (server.py:4568-4692,
    ``write_stack_readied``): if the agent registry or brief ledger fails to
    ready, every write-stack collaborator ALREADY readied before it must be
    closed — the C6-audit #3 guard this packet must not silently exempt the
    two new ledgers from. Mirrors ``test_mcp_server.py``'s
    ``test_ready_guard_closes_earlier_backends_on_a_mid_ready_failure``
    exactly, fault-injecting ``AgentRegistry.ensure_ready`` /
    ``BriefLedger.ensure_ready`` instead of the code graph. Tracks only
    ``SurrealStore``/``SurrealManifest`` (guaranteed to construct first,
    regardless of exactly where the comms ledgers land in the sequence) — a
    representative, not exhaustive, proof that the SAME guard mechanism
    embraces them."""

    async def test_agent_registry_ready_failure_closes_everything_readied_before_it(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import loremaster.agents as agents_module
        import loremaster.index.surreal_manifest as manifest_module
        import loremaster.store.surreal as store_module

        opened: list[Any] = []

        class _TrackedStore(store_module.SurrealStore):
            def __init__(self, **kwargs: Any) -> None:
                super().__init__(**kwargs)
                opened.append(self)

        class _TrackedManifest(manifest_module.SurrealManifest):
            def __init__(self, **kwargs: Any) -> None:
                super().__init__(**kwargs)
                opened.append(self)

        class _FailingAgentRegistry(agents_module.AgentRegistry):
            async def ensure_ready(self) -> None:
                raise RuntimeError("agent registry socket refused")

        monkeypatch.setattr(store_module, "SurrealStore", _TrackedStore)
        monkeypatch.setattr(manifest_module, "SurrealManifest", _TrackedManifest)
        monkeypatch.setattr(agents_module, "AgentRegistry", _FailingAgentRegistry)

        slug = _slug()
        config = _config(slug)
        leaked_ctx: AppContext | None = None
        try:
            with pytest.raises(RuntimeError, match="agent registry socket refused"):
                leaked_ctx = await build_app_context(
                    server=LoreServer(config),
                    embedder=FakeEmbedder(dim=_DIM),
                    manifest_path=tmp_path / "m.db",
                    snapshot_root=tmp_path / "snap",
                    start_tasks=False,
                )
        finally:
            if leaked_ctx is not None:
                await leaked_ctx.aclose()

        assert len(opened) == 2, "the write store + manifest should both have been opened"
        for handle in opened:
            assert handle._connection is None, (  # noqa: SLF001 - the closure signal
                f"{type(handle).__name__} must be closed after the agent registry's "
                "ensure_ready failed — a non-None _connection means it leaked"
            )

    async def test_brief_ledger_ready_failure_closes_everything_readied_before_it(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import loremaster.briefs as briefs_module
        import loremaster.index.surreal_manifest as manifest_module
        import loremaster.store.surreal as store_module

        opened: list[Any] = []

        class _TrackedStore(store_module.SurrealStore):
            def __init__(self, **kwargs: Any) -> None:
                super().__init__(**kwargs)
                opened.append(self)

        class _TrackedManifest(manifest_module.SurrealManifest):
            def __init__(self, **kwargs: Any) -> None:
                super().__init__(**kwargs)
                opened.append(self)

        class _FailingBriefLedger(briefs_module.BriefLedger):
            async def ensure_ready(self) -> None:
                raise RuntimeError("brief ledger socket refused")

        monkeypatch.setattr(store_module, "SurrealStore", _TrackedStore)
        monkeypatch.setattr(manifest_module, "SurrealManifest", _TrackedManifest)
        monkeypatch.setattr(briefs_module, "BriefLedger", _FailingBriefLedger)

        slug = _slug()
        config = _config(slug)
        leaked_ctx: AppContext | None = None
        try:
            with pytest.raises(RuntimeError, match="brief ledger socket refused"):
                leaked_ctx = await build_app_context(
                    server=LoreServer(config),
                    embedder=FakeEmbedder(dim=_DIM),
                    manifest_path=tmp_path / "m.db",
                    snapshot_root=tmp_path / "snap",
                    start_tasks=False,
                )
        finally:
            if leaked_ctx is not None:
                await leaked_ctx.aclose()

        assert len(opened) == 2, "the write store + manifest should both have been opened"
        for handle in opened:
            assert handle._connection is None, (  # noqa: SLF001 - the closure signal
                f"{type(handle).__name__} must be closed after the brief ledger's "
                "ensure_ready failed — a non-None _connection means it leaked"
            )


class TestAppContextAcloseClosesCommsLedgers:
    """Steady-state teardown: ``AppContext.aclose()`` must close BOTH new
    ledgers' connections, or they outlive the server as leaked sockets — the
    exact posture ``aclose()`` already holds for ``task_ledger``/
    ``finding_ledger`` (server.py:4221-4226)."""

    async def test_aclose_closes_the_agent_registry_connection(self, tmp_path: Path) -> None:
        context = await _open_context(tmp_path=tmp_path)
        registry = context.agent_registry
        assert registry._connection is not None, "sanity: ensure_ready must have opened it"  # noqa: SLF001
        await context.aclose()
        assert registry._connection is None, (  # noqa: SLF001 - the closure signal
            "aclose() must close the agent registry's connection — a live socket "
            "afterwards is a leak"
        )

    async def test_aclose_closes_the_brief_ledger_connection(self, tmp_path: Path) -> None:
        context = await _open_context(tmp_path=tmp_path)
        ledger = context.brief_ledger
        assert ledger._connection is not None, "sanity: ensure_ready must have opened it"  # noqa: SLF001
        await context.aclose()
        assert ledger._connection is None, (  # noqa: SLF001 - the closure signal
            "aclose() must close the brief ledger's connection — a live socket "
            "afterwards is a leak"
        )


class TestCommsReachesTheRealLedgersNotAFake:
    """``AppContext.comms(...)`` must write through the SAME ledger instances
    exposed publicly as ``ctx.agent_registry``/``ctx.brief_ledger`` — not a
    private, separately-wired pair the dispatcher alone can see."""

    async def test_register_through_comms_is_visible_via_the_public_agent_registry(
        self, ctx: AppContext
    ) -> None:
        await ctx.comms(
            action="register", agent="fixer-b", session="wave7", role="builder"
        )
        agent = await ctx.agent_registry.get_agent("fixer-b", session="wave7")
        assert agent.role == "builder"

    async def test_brief_publish_through_comms_is_visible_via_the_public_brief_ledger(
        self, ctx: AppContext
    ) -> None:
        await ctx.comms(
            action="register", agent="lead", session="wave7", role="lead"
        )
        await ctx.comms(
            action="brief_publish", agent="lead", session="wave7", name="project", body="the plan"
        )
        head = await ctx.brief_ledger.get_head("project")
        assert head.body == "the plan"
        assert head.created_by == "lead", (
            "the publishing identity is the universal 'agent' param, not a separate "
            "'created_by' kwarg — spec §8's _COMMS_ACTIONS table declares "
            "brief_publish's params as exactly {name, body, note}"
        )


# =========================================================================== #
# B — end-to-end through the real tool surface (the arc a deploy smoke runs)
# =========================================================================== #


class TestEndToEndCommsArcThroughTheRealToolSurface:
    """bootstrap register -> publish 'project' -> second register (auto-ack)
    -> brief_get -> heartbeat -> brief_ack -> fleet — spec §1/§9's worked
    arc, pinned end-to-end so it can never silently rot. Every assertion
    reads the RENDERED text (what an agent actually sees), never the return
    object's internals. Split into one helper per step (not one long test
    body) so each step's assertions stay legible and locally scoped; the top
    test just drives the sequence."""

    async def test_the_full_arc(self, ctx: AppContext) -> None:
        await self._bootstrap_register_with_no_project_brief(ctx)
        await self._publish_the_first_project_brief(ctx)
        await self._second_register_auto_acks_the_head_brief(ctx)
        await self._brief_get_shows_partial_coverage(ctx)
        await self._heartbeat_names_the_catch_up_call(ctx)
        await self._brief_ack_records_the_catch_up(ctx)
        await self._fleet_renders_both_agents_current(ctx)

    @staticmethod
    async def _bootstrap_register_with_no_project_brief(ctx: AppContext) -> None:
        rendered = str(
            await ctx.comms(action="register", agent="lead", session="wave7", role="lead")
        )
        assert "registered lead (session wave7, role lead) — status active" in rendered
        assert (
            "no 'project' brief published yet — work from your spawn brief; "
            "re-check with lore_comms action=brief_get"
        ) in rendered

    @staticmethod
    async def _publish_the_first_project_brief(ctx: AppContext) -> None:
        rendered = str(
            await ctx.comms(
                action="brief_publish",
                agent="lead",
                session="wave7",
                name="project",
                body=_HOSTILE_BRIEF_BODY,
            )
        )
        assert (
            "brief 'project' v1 published by lead — first version; agents ack at register"
        ) in rendered

    @staticmethod
    async def _second_register_auto_acks_the_head_brief(ctx: AppContext) -> None:
        rendered = str(
            await ctx.comms(
                action="register", agent="fixer-b", session="wave7", role="builder"
            )
        )
        assert "registered fixer-b (session wave7, role builder) — status active" in rendered
        assert "brief 'project' v1 (published " in rendered
        assert " ago by lead) — ack recorded (via register)" in rendered
        assert _HOSTILE_BRIEF_BODY in rendered, "the brief body must round-trip verbatim inside the fence"
        assert _expected_fence(_HOSTILE_BRIEF_BODY) in rendered, (
            "the fence must strictly outrun the widest backtick run embedded in the "
            "hostile body, through the REAL production render path"
        )
        assert "echo in your report: brief project v1 read" in rendered

    @staticmethod
    async def _brief_get_shows_partial_coverage(ctx: AppContext) -> None:
        rendered = str(
            await ctx.comms(
                action="brief_get", agent="lead", session="wave7", name="project"
            )
        )
        assert _HOSTILE_BRIEF_BODY in rendered
        assert "ack recorded" not in rendered, "brief_get's header mirrors register's minus the ack clause"
        assert (
            "coverage (session wave7): 1/2 non-retired agents at v1; behind: lead (unbriefed)"
        ) in rendered

    @staticmethod
    async def _heartbeat_names_the_catch_up_call(ctx: AppContext) -> None:
        rendered = str(
            await ctx.comms(action="heartbeat", agent="lead", session="wave7")
        )
        assert "heartbeat lead — status active" in rendered
        assert (
            "you have not acked brief 'project' (head v1) — lore_comms action=brief_get"
        ) in rendered

    @staticmethod
    async def _brief_ack_records_the_catch_up(ctx: AppContext) -> None:
        rendered = str(
            await ctx.comms(
                action="brief_ack", agent="lead", session="wave7", name="project", version=1
            )
        )
        assert "acked brief 'project' v1 (head)" in rendered

    @staticmethod
    async def _fleet_renders_both_agents_current(ctx: AppContext) -> None:
        rendered = str(
            await ctx.comms(action="fleet", agent="lead", session="wave7")
        )
        assert (
            "fleet (session wave7): 2 agents — 0 input_required, 2 active, 0 idle"
        ) in rendered
        assert "STALE" not in rendered
        lead_row = _fleet_row(rendered, "lead")
        assert "role lead" in lead_row
        assert "brief v1" in lead_row
        fixer_row = _fleet_row(rendered, "fixer-b")
        assert "role builder" in fixer_row
        assert "brief v1" in fixer_row


# =========================================================================== #
# C — CommsConfig knobs are honestly wired (spec §4: repo law, no hardcoded
# values). Each pair below CHANGES the config value and observes the served
# behaviour change — a test that only asserted "the field exists on the
# config object" would still pass a hardcoded implementation; these cannot.
# =========================================================================== #


class TestConfigKnobStaleHeartbeatIsConsumed:
    """``comms.stale_heartbeat_s`` must genuinely gate the fleet ``STALE``
    marker — proven BIDIRECTIONALLY so neither direction can be satisfied by
    a hardcoded 600s default.

    The row under test ('fixer-b') is backdated but is NEVER the ``fleet``
    caller — the dispatcher's uniform heartbeat touch (spec §8 step 4) stamps
    the CALLING agent's own ``heartbeat_at`` to ``now()`` on every action,
    which would silently re-freshen a self-called backdate before the
    render even runs. A separate 'lead' agent calls ``fleet`` so 'fixer-b's
    backdated row survives untouched to be judged.
    """

    async def test_raising_the_threshold_suppresses_a_marker_that_would_otherwise_fire(
        self, tmp_path: Path
    ) -> None:
        context = await _open_context(tmp_path=tmp_path, comms={"stale_heartbeat_s": 800})
        try:
            await context.comms(action="register", agent="lead", session="wave7", role="lead")
            await context.comms(
                action="register", agent="fixer-b", session="wave7", role="builder"
            )
            await _backdate_heartbeat(context, name="fixer-b", session="wave7", seconds_ago=700)
            rendered = str(await context.comms(action="fleet", agent="lead", session="wave7"))
            assert "STALE" not in rendered, (
                "stale_heartbeat_s=800 must suppress the marker for a 700s-old "
                "heartbeat — a hardcoded 600s default would incorrectly show it here"
            )
        finally:
            await context.aclose()

    async def test_lowering_the_threshold_triggers_a_marker_that_would_not_otherwise_fire(
        self, tmp_path: Path
    ) -> None:
        context = await _open_context(tmp_path=tmp_path, comms={"stale_heartbeat_s": 1})
        try:
            await context.comms(action="register", agent="lead", session="wave7", role="lead")
            await context.comms(
                action="register", agent="fixer-b", session="wave7", role="builder"
            )
            await _backdate_heartbeat(context, name="fixer-b", session="wave7", seconds_ago=5)
            rendered = str(await context.comms(action="fleet", agent="lead", session="wave7"))
            assert "STALE" in rendered, (
                "stale_heartbeat_s=1 must mark a 5s-old heartbeat STALE — a hardcoded "
                "600s default would incorrectly hide it here"
            )
        finally:
            await context.aclose()


class TestConfigKnobFleetLimitIsConsumed:
    """``comms.fleet_limit`` must genuinely gate the fleet row cap/elision,
    and the counted re-ask value stays honest and clamped to
    ``_MAX_FLEET_LIMIT`` (DESIGN-LAW §1.2) even when it comes from config."""

    async def test_a_low_limit_elides_with_an_honest_reask(self, tmp_path: Path) -> None:
        context = await _open_context(tmp_path=tmp_path, comms={"fleet_limit": 1})
        try:
            await context.comms(
                action="register", agent="fixer-b", session="wave7", role="builder"
            )
            await context.comms(
                action="register", agent="fixer-c", session="wave7", role="builder"
            )
            rendered = str(
                await context.comms(action="fleet", agent="fixer-b", session="wave7")
            )
            assert "+1 more — re-run with limit=2" in rendered
        finally:
            await context.aclose()

    async def test_the_default_limit_shows_both_rows_with_no_elision(self, tmp_path: Path) -> None:
        context = await _open_context(tmp_path=tmp_path)  # default fleet_limit=20
        try:
            await context.comms(
                action="register", agent="fixer-b", session="wave7", role="builder"
            )
            await context.comms(
                action="register", agent="fixer-c", session="wave7", role="builder"
            )
            rendered = str(
                await context.comms(action="fleet", agent="fixer-b", session="wave7")
            )
            assert "more —" not in rendered, (
                "the SAME two agents must not elide under the default fleet_limit=20 — "
                "a hardcoded internal limit of 1 would incorrectly elide here too"
            )
        finally:
            await context.aclose()

    async def test_the_reask_value_is_clamped_to_the_enforceable_cap(self, tmp_path: Path) -> None:
        context = await _open_context(tmp_path=tmp_path, comms={"fleet_limit": 1})
        try:
            await context.comms(
                action="register", agent="lead", session="wave7", role="lead"
            )
            # 200 seeded + lead = 201 non-retired agents; shown=1, k=200,
            # unclamped next=201 > _SPEC_MAX_FLEET_LIMIT=200 — must clamp.
            await _seed_extra_agents(context, session="wave7", count=200)
            rendered = str(
                await context.comms(action="fleet", agent="lead", session="wave7")
            )
            assert f"+200 more — re-run with limit={_SPEC_MAX_FLEET_LIMIT}" in rendered, (
                "the honest re-ask is min(1+200, 200) — the DESIGN-LAW §1.2 clamp to "
                "_MAX_FLEET_LIMIT=200, never the unclamped 201"
            )
        finally:
            await context.aclose()


class TestConfigKnobBriefBodyWarnCharsIsConsumed:
    """``comms.brief_body_warn_chars`` must genuinely gate the oversize-body
    warn line (spec §5.2/§9.4) — never reject, always warn-only."""

    async def test_a_low_threshold_fires_the_warn_line(self, tmp_path: Path) -> None:
        context = await _open_context(tmp_path=tmp_path, comms={"brief_body_warn_chars": 10})
        try:
            await context.comms(
                action="register", agent="lead", session="wave7", role="lead"
            )
            body = "0123456789ABCDEF"  # 16 chars > 10
            rendered = str(
                await context.comms(
                    action="brief_publish",
                    agent="lead",
                    session="wave7",
                    name="project",
                    body=body,
                )
            )
            assert "exceeds the 10-char warn threshold" in rendered
            assert "prefer a doc + pointer" in rendered
            assert "brief 'project' v1 published by lead" in rendered, (
                "an oversize body warns — it must never be rejected (spec §5.2)"
            )
        finally:
            await context.aclose()

    async def test_the_default_threshold_does_not_warn_on_the_same_short_body(
        self, tmp_path: Path
    ) -> None:
        context = await _open_context(tmp_path=tmp_path)  # default 4000
        try:
            await context.comms(
                action="register", agent="lead", session="wave7", role="lead"
            )
            body = "0123456789ABCDEF"
            rendered = str(
                await context.comms(
                    action="brief_publish",
                    agent="lead",
                    session="wave7",
                    name="project",
                    body=body,
                )
            )
            assert "warn threshold" not in rendered, (
                "the SAME 16-char body must not warn under the default 4000-char "
                "threshold — a hardcoded low internal threshold would incorrectly warn here"
            )
        finally:
            await context.aclose()
