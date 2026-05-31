"""Contract tests for ``loremaster.server`` — the FastMCP integration lynchpin.

This is Deliverable 3's running MCP server: the FastMCP streamable-http server,
the :class:`AppContext` lifespan with the embedder **startup probe gate**, the
spawned live watcher + periodic reconcile tasks, the pluggable Bearer auth wiring
(D9/D11/§A1.12), and the ten MCP tools wrapping the merged services. These tests
drive the REAL wiring with a :class:`~loresigil.testing.FakeEmbedder` (dim 2048)
and a REAL local Qdrant (throwaway collections) + a real ``tmp_path`` corpus —
the embedder is loresigil's tested concern, so faking it keeps the suite fast and
deterministic while everything else is real.

The contract pinned (each maps to a plan requirement):

Startup probe gate (Deliverable 3 / "startup probe gate")
---------------------------------------------------------
* **Unreachable embedder → REFUSE.** ``probe()`` raising aborts startup with a
  :class:`ProbeGateError` — the server never comes up against a dead embedder.
* **observed dim != config.dim → REFUSE.** A probe reporting a different
  dimensionality than the config declares aborts — a wrong-dim deploy cannot
  silently corrupt retrieval.
* **collection size != config.dim → REFUSE, NEVER auto-recreate.** An EXISTING
  collection whose vector size disagrees with config aborts with a remediation
  message and the collection is left INTACT (auto-recreate would silently nuke
  the index). Proven by asserting the pre-existing wrong-dim collection still
  exists after the refusal.
* **All coherent → PASS.** probe == config.dim, and either no collection yet or a
  matching-size collection, lets startup proceed.

AppContext lifespan
-------------------
* Entering the lifespan constructs the runtime services, ensures the collections,
  spawns the live watcher + periodic reconcile as asyncio tasks, and runs the
  extension ``on_startup`` hooks; exiting stops the tasks and runs ``on_shutdown``.
* **Framework fix A surfaces:** an extension whose ``on_startup`` raises aborts
  startup (the prior extensions' ``on_shutdown`` having run) — no half-started
  server.

The ten MCP tools (end-to-end through the AppContext handlers)
-------------------------------------------------------------
* All ten — ``search_code``/``read_file``/``get_symbol``/``save_memory``/
  ``recall_memory``/``reindex``/``index_status``/``what_imports``/
  ``blast_radius``/``tests_for`` — are REGISTERED on the FastMCP app.
* Each returns the right SHAPE over a real-indexed corpus: ``search_code`` finds a
  uniquely-named symbol with a ``[SOURCE...]`` citation; ``index_status`` reports
  a healthy index; ``save_memory`` → ``recall_memory`` round-trips; ``get_symbol``
  resolves an exact definition; ``read_file`` returns a real span;
  ``blast_radius``/``what_imports``/``tests_for`` traverse the live graph;
  ``reindex`` brings a freshly-written file current.

Auth wiring (D9/D11)
--------------------
* With an ``auth`` block enabled, the built ASGI app is wrapped in the Bearer
  middleware (a keyless request is 401); with NO auth block, it is NOT wrapped
  (no-auth localhost mode).

``LoreServer.run`` + ``python -m loremaster.server``
----------------------------------------------------
* ``LoreServer.run`` no longer raises ``NotImplementedError`` — it builds and
  serves (a monkeypatched transport proves it reaches the serve call with the
  configured host/port/path). The ``__main__`` entry is importable and wired.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from loremaster.config import LoreConfig
from loremaster.server import (
    AppContext,
    LoreServer,
    ProbeGateError,
    build_app_context,
    build_mcp_server,
    configure_logging_from_config,
    run_probe_gate,
)
from loremaster.store.qdrant import QdrantStore
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient
from qdrant_client import models as qmodels

_DIM = 2048

# A real Python module with a uniquely-named symbol so search/get_symbol/graph
# have something distinctive to find. Chunked for real through python_ast.
_PY_MODULE = """\
import os

class ChampionRouter:
    \"\"\"Routes the 36-week curve champion.\"\"\"

    def route(self, week):
        return os.linesep.join(str(week))


def champion_routing(week):
    \"\"\"Route the 36-week curve champion.\"\"\"
    return week * 2
"""


@pytest_asyncio.fixture()
async def qdrant() -> AsyncIterator[AsyncQdrantClient]:
    """A real Qdrant client with exact-name (concurrency-safe) teardown."""
    from conftest import QDRANT_URL, _qdrant_api_key

    client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
    created: list[str] = []
    client._lore_created = created  # type: ignore[attr-defined]
    try:
        yield client
    finally:
        # build_app_context creates the project collection AND a ``<name>_memory``
        # sibling; reap BOTH for every tracked name so the server tests leave no
        # lore_test_ collection behind (exact-name, never a prefix sweep).
        for name in created:
            for candidate in (name, f"{name}_memory"):
                if await client.collection_exists(candidate):
                    await client.delete_collection(candidate)
        await client.close()


def _slug() -> str:
    return f"test_{uuid.uuid4().hex}"


def _config(slug: str, live_path: Path, *, auth: dict[str, Any] | None = None) -> LoreConfig:
    payload: dict[str, Any] = {
        "schema_version": 1,
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
        "qdrant": {"url": "http://127.0.0.1:16333", "api_key_env": "QDRANT__SERVICE__API_KEY"},
        "roots": [
            {"tier": "custom", "watch": "live", "path": str(live_path), "include": ["**/*.py"]}
        ],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9233},
    }
    if auth is not None:
        payload["auth"] = auth
    return LoreConfig.model_validate(payload)


def _store(client: AsyncQdrantClient, slug: str) -> QdrantStore:
    """Build a QdrantStore and register its collection for fixture teardown."""
    store = QdrantStore(client=client, slug=slug)
    client._lore_created.append(store.collection_name)  # type: ignore[attr-defined]
    return store


async def _make_context(
    *,
    config: LoreConfig,
    client: AsyncQdrantClient,
    tmp_path: Path,
    embedder: FakeEmbedder | None = None,
    start_tasks: bool = False,
) -> AppContext:
    """Build a live :class:`AppContext` with injected fakes (the test wiring seam).

    ``build_app_context`` runs the probe gate, constructs every runtime service,
    ensures the collections, and (when ``start_tasks``) spawns the watcher +
    reconcile tasks — the same path the lifespan takes, but with the embedder /
    client / paths injected so a test needs no real TEI endpoint.
    """
    # build_app_context creates the project AND ``_memory`` collections internally
    # (from the config slug), so register both for the fixture's exact-name reap.
    slug = config.project.slug
    client._lore_created.append(f"lore_{slug}")  # type: ignore[attr-defined]
    client._lore_created.append(f"lore_{slug}_memory")  # type: ignore[attr-defined]
    return await build_app_context(
        server=LoreServer(config),
        embedder=embedder or FakeEmbedder(dim=_DIM),
        qdrant_client=client,
        manifest_path=tmp_path / "m.db",
        graph_path=tmp_path / "graph.db",
        snapshot_root=tmp_path / "snap",
        start_tasks=start_tasks,
    )


# --------------------------------------------------------------------------- #
# Logging wiring (env-over-config)
# --------------------------------------------------------------------------- #
class TestLoggingWiring:
    """``configure_logging_from_config`` reads LORE_LOG_LEVEL over config.logging."""

    def _restore(self) -> None:
        import logging as _logging

        from loremaster.logging_setup import LORE_NAMESPACES

        for name in LORE_NAMESPACES:
            logger = _logging.getLogger(name)
            logger.handlers = []
            logger.setLevel(_logging.NOTSET)
            logger.propagate = True

    def test_uses_config_level_when_env_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LORE_LOG_LEVEL", raising=False)
        config = _config(_slug(), Path("/tmp/live"))
        try:
            configure_logging_from_config(config)
            # config default level is INFO → INFO enabled, DEBUG not.
            assert logging.getLogger("loremaster").isEnabledFor(logging.INFO)
            assert not logging.getLogger("loremaster").isEnabledFor(logging.DEBUG)
        finally:
            self._restore()

    def test_env_overrides_config_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LORE_LOG_LEVEL", "DEBUG")
        config = _config(_slug(), Path("/tmp/live"))  # config default INFO
        try:
            configure_logging_from_config(config)
            assert logging.getLogger("loremaster").isEnabledFor(logging.DEBUG)
        finally:
            self._restore()


# --------------------------------------------------------------------------- #
# Startup probe gate
# --------------------------------------------------------------------------- #
class TestProbeGate:
    """The startup probe gate refuses on unreachable / dim-mismatch (no auto-recreate)."""

    async def test_unreachable_embedder_refuses(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> None:
        slug = _slug()
        store = _store(qdrant, slug)
        config = _config(slug, tmp_path / "live")
        with pytest.raises(ProbeGateError):
            await run_probe_gate(
                embedder=FakeEmbedder(dim=_DIM, probe_fails=True), store=store, config=config
            )

    async def test_observed_dim_mismatch_refuses(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> None:
        # The embedder probes a DIFFERENT dim than the config declares → refuse.
        slug = _slug()
        store = _store(qdrant, slug)
        config = _config(slug, tmp_path / "live")  # config.dim == 2048
        with pytest.raises(ProbeGateError, match="(?i)dim"):
            await run_probe_gate(embedder=FakeEmbedder(dim=1024), store=store, config=config)

    async def test_existing_collection_wrong_size_refuses_without_recreate(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> None:
        # An EXISTING collection at the WRONG size must refuse AND leave the
        # collection intact (never auto-recreate — that silently nukes the index).
        slug = _slug()
        store = _store(qdrant, slug)
        # Pre-create the collection at a wrong size (1024, not config's 2048).
        await qdrant.create_collection(
            collection_name=store.collection_name,
            vectors_config=qmodels.VectorParams(size=1024, distance=qmodels.Distance.COSINE),
        )
        config = _config(slug, tmp_path / "live")
        with pytest.raises(ProbeGateError, match="(?i)collection|size|dim"):
            await run_probe_gate(embedder=FakeEmbedder(dim=_DIM), store=store, config=config)
        # The wrong-size collection still exists, unmodified (no auto-recreate).
        assert await qdrant.collection_exists(store.collection_name)
        info = await qdrant.get_collection(store.collection_name)
        assert info.config.params.vectors.size == 1024  # type: ignore[union-attr]

    async def test_coherent_dims_pass(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> None:
        # probe == config.dim and no collection yet → the gate passes (returns the
        # observed dim).
        slug = _slug()
        store = _store(qdrant, slug)
        config = _config(slug, tmp_path / "live")
        observed = await run_probe_gate(
            embedder=FakeEmbedder(dim=_DIM), store=store, config=config
        )
        assert observed == _DIM

    async def test_passing_gate_logs_probe_gate_pass(
        self, tmp_path: Path, qdrant: AsyncQdrantClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        store = _store(qdrant, slug)
        config = _config(slug, tmp_path / "live")
        with caplog.at_level(logging.INFO, logger="loremaster.server"):
            await run_probe_gate(embedder=FakeEmbedder(dim=_DIM), store=store, config=config)
        events = [r for r in caplog.records if r.message == "startup.probe_gate.pass"]
        assert len(events) == 1
        assert events[0].levelno == logging.INFO
        assert events[0].observed_dim == _DIM  # type: ignore[attr-defined]

    async def test_refusing_gate_logs_probe_gate_refuse(
        self, tmp_path: Path, qdrant: AsyncQdrantClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        store = _store(qdrant, slug)
        config = _config(slug, tmp_path / "live")  # config.dim == 2048
        with caplog.at_level(logging.ERROR, logger="loremaster.server"):
            with pytest.raises(ProbeGateError):
                await run_probe_gate(embedder=FakeEmbedder(dim=1024), store=store, config=config)
        events = [r for r in caplog.records if r.message == "startup.probe_gate.refuse"]
        assert events, "a refusing gate must log startup.probe_gate.refuse at ERROR"
        assert events[0].levelno == logging.ERROR
        # A reason string is attached (no secret, no embedder object).
        assert isinstance(events[0].reason, str) and events[0].reason  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
# AppContext lifespan
# --------------------------------------------------------------------------- #
class TestAppContextLifespan:
    """The lifespan builds services, spawns tasks, runs hooks; teardown reverses."""

    async def test_build_context_ensures_collection_and_services(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        ctx = await _make_context(config=config, client=qdrant, tmp_path=tmp_path)
        try:
            # The collection now exists at the configured dim.
            store = QdrantStore(client=qdrant, slug=slug)
            assert await store.collection_dim() == _DIM
            # The runtime services are wired and reachable.
            assert ctx.search_pipeline is not None
            assert ctx.indexer is not None
            assert ctx.code_graph is not None
        finally:
            await ctx.aclose()

    async def test_lifespan_spawns_watcher_and_reconcile_tasks(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        live.mkdir()
        config = _config(slug, live)
        ctx = await _make_context(
            config=config, client=qdrant, tmp_path=tmp_path, start_tasks=True
        )
        try:
            # The watcher observer is running and the periodic reconcile task is live.
            assert ctx.watcher_started is True
            assert ctx.reconcile_task is not None
            assert not ctx.reconcile_task.done()
        finally:
            await ctx.aclose()
            # After close, the periodic reconcile task is stopped.
            assert ctx.reconcile_task is None or ctx.reconcile_task.done()

    async def test_startup_logs_initial_reconcile_and_watcher_started(
        self, tmp_path: Path, qdrant: AsyncQdrantClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        # When start_tasks=True the lifespan runs an INITIAL reconcile and starts
        # the watcher — each must emit its structured startup event.
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "boot.py").write_text("def boot():\n    return 1\n", encoding="utf-8")
        config = _config(slug, live)
        with caplog.at_level(logging.INFO, logger="loremaster.server"):
            ctx = await _make_context(
                config=config, client=qdrant, tmp_path=tmp_path, start_tasks=True
            )
            try:
                initial = [r for r in caplog.records if r.message == "startup.reconcile.initial"]
                started = [r for r in caplog.records if r.message == "startup.watcher.started"]
                assert len(initial) == 1
                assert initial[0].levelno == logging.INFO
                # The initial reconcile event carries the indexed count (a summary).
                assert isinstance(initial[0].files_indexed, int)  # type: ignore[attr-defined]
                assert len(started) == 1
                assert started[0].levelno == logging.INFO
            finally:
                await ctx.aclose()

    async def test_failing_extension_startup_aborts_lifespan(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> None:
        # Framework fix A: an extension whose on_startup raises must abort the
        # lifespan startup — no half-started server. The collection may exist (core
        # resources came up first), but the context build raises.
        from loremaster.extension import Extension, ExtensionContext

        class _BoomExtension(Extension):
            @property
            def name(self) -> str:
                return "boom"

            async def on_startup(self, ctx: ExtensionContext) -> None:
                raise RuntimeError("extension refused to start")

        slug = _slug()
        config = _config(slug, tmp_path / "live")
        server = LoreServer(config).register_extension(_BoomExtension())
        # The core collections come up before the (failing) extension hook, so
        # register them for the fixture's exact-name reap (no leak on the abort).
        qdrant._lore_created.append(f"lore_{slug}")  # type: ignore[attr-defined]
        qdrant._lore_created.append(f"lore_{slug}_memory")  # type: ignore[attr-defined]
        with pytest.raises(RuntimeError, match="refused to start"):
            await build_app_context(
                server=server,
                embedder=FakeEmbedder(dim=_DIM),
                qdrant_client=qdrant,
                manifest_path=tmp_path / "m.db",
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=False,
            )

    async def test_failed_startup_closes_sqlite_connections(
        self, tmp_path: Path, qdrant: AsyncQdrantClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Lifecycle hygiene (owner rule): when startup aborts (a failing extension
        # hook AFTER the manifest + graph were opened), those SQLite connections
        # must be CLOSED, not leaked. A leaked connection on a half-built server is
        # the degradation case the rule targets. Spy on the manifest + graph
        # connections and assert both were closed after the abort — a discriminator
        # that fails on the un-hardened build (which leaks them).
        import loremaster.graph as graph_module
        import loremaster.index.manifest as manifest_module
        from loremaster.extension import Extension, ExtensionContext

        opened: list[Any] = []

        class _TrackedManifest(manifest_module.Manifest):
            def __init__(self, db_path: str) -> None:
                super().__init__(db_path)
                opened.append(self)

        class _TrackedGraph(graph_module.CodeGraph):
            def __init__(self, db_path: str) -> None:
                super().__init__(db_path)
                opened.append(self)

        # build_app_context imports these from their source modules at call time,
        # so patching the source attribute is what the local ``from ... import``
        # resolves.
        monkeypatch.setattr(manifest_module, "Manifest", _TrackedManifest)
        monkeypatch.setattr(graph_module, "CodeGraph", _TrackedGraph)

        class _BoomExtension(Extension):
            @property
            def name(self) -> str:
                return "boom"

            async def on_startup(self, ctx: ExtensionContext) -> None:
                raise RuntimeError("extension refused to start")

        slug = _slug()
        config = _config(slug, tmp_path / "live")
        qdrant._lore_created.append(f"lore_{slug}")  # type: ignore[attr-defined]
        qdrant._lore_created.append(f"lore_{slug}_memory")  # type: ignore[attr-defined]
        with pytest.raises(RuntimeError, match="refused to start"):
            await build_app_context(
                server=LoreServer(config).register_extension(_BoomExtension()),
                embedder=FakeEmbedder(dim=_DIM),
                qdrant_client=qdrant,
                manifest_path=tmp_path / "m.db",
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=False,
            )
        # Both SQLite handles were opened during the (aborted) build and must now
        # be closed. A closed sqlite3 connection raises on use — that is the probe.
        assert len(opened) == 2, "manifest + graph should both have been opened"
        for handle in opened:
            with pytest.raises(Exception):  # noqa: B017 - ProgrammingError on a closed conn
                handle.connection.execute("SELECT 1")

    async def test_startup_runs_an_initial_reconcile_so_offline_edits_index_now(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> None:
        # Fix #1 (HIGH): a fresh ``start`` (start_tasks=True) over a corpus that
        # was edited while offline must delta-index IMMEDIATELY — NOT wait out the
        # 600s periodic interval. Build with start_tasks=True over a live root that
        # already holds an un-indexed .py file, then read index_status right away:
        # files_indexed must reflect the on-disk file (the initial reconcile ran).
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "offline_edit.py").write_text(
            "def added_while_offline():\n    return 1\n", encoding="utf-8"
        )
        config = _config(slug, live)
        ctx = await _make_context(
            config=config, client=qdrant, tmp_path=tmp_path, start_tasks=True
        )
        try:
            # Right after start (no sleep, no edit), the offline file is indexed.
            status = await ctx.index_status()
            assert status.files_indexed >= 1, (
                "the on-disk file must be indexed by the startup reconcile, not "
                "left stale until the periodic interval"
            )
            # And it is actually searchable / resolvable now (end-to-end, not just a count).
            symbol = await ctx.get_symbol("added_while_offline")
            assert symbol.file_path == "pkg/offline_edit.py"
        finally:
            await ctx.aclose()

    async def test_aborted_startup_after_watcher_started_stops_the_watcher(
        self, tmp_path: Path, qdrant: AsyncQdrantClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Fix #4 (LOW): when startup aborts AFTER the watcher's observer thread
        # started (start_tasks=True), the abort handler must STOP the watcher — no
        # orphaned observer thread. Force the post-start step (the initial
        # reconcile sweep) to raise, and assert the watcher's stop() ran. We spy on
        # LiveWatcher.stop and make run_sweep raise once start() has returned.
        import loremaster.index.watcher as watcher_module

        stopped: list[bool] = []
        original_start = watcher_module.LiveWatcher.start
        original_stop = watcher_module.LiveWatcher.stop

        async def _start_then_arm_failure(self: Any) -> None:
            await original_start(self)
            # After the observer is live, make the next sweep blow up — simulating
            # a post-watcher-start failure during the remaining startup steps.
            async def _boom() -> None:
                raise RuntimeError("post-start step failed")

            self.run_sweep = _boom

        async def _tracked_stop(self: Any) -> None:
            stopped.append(True)
            await original_stop(self)

        monkeypatch.setattr(watcher_module.LiveWatcher, "start", _start_then_arm_failure)
        monkeypatch.setattr(watcher_module.LiveWatcher, "stop", _tracked_stop)

        slug = _slug()
        live = tmp_path / "live"
        live.mkdir()
        config = _config(slug, live)
        qdrant._lore_created.append(f"lore_{slug}")  # type: ignore[attr-defined]
        qdrant._lore_created.append(f"lore_{slug}_memory")  # type: ignore[attr-defined]
        with pytest.raises(RuntimeError, match="post-start step failed"):
            await build_app_context(
                server=LoreServer(config),
                embedder=FakeEmbedder(dim=_DIM),
                qdrant_client=qdrant,
                manifest_path=tmp_path / "m.db",
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=True,
            )
        # The started watcher was torn down on the abort (no orphaned thread).
        assert stopped == [True], "an aborted startup must stop a watcher it had started"


# --------------------------------------------------------------------------- #
# Tool registration + end-to-end tool behaviour
# --------------------------------------------------------------------------- #
_EXPECTED_TOOLS = {
    "search_code",
    "read_file",
    "get_symbol",
    "save_memory",
    "recall_memory",
    "reindex",
    "index_status",
    "what_imports",
    "blast_radius",
    "tests_for",
}


class TestToolRegistration:
    """All ten MCP tools are registered on the FastMCP app."""

    async def test_all_ten_tools_registered(self, tmp_path: Path) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        assert _EXPECTED_TOOLS <= names


class TestToolBehaviourEndToEnd:
    """Each tool returns the right shape over a real-indexed corpus."""

    @pytest_asyncio.fixture()
    async def indexed_context(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> AsyncIterator[AppContext]:
        """An AppContext with a real Python file indexed (vectors + graph)."""
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, client=qdrant, tmp_path=tmp_path)
        # Index the live tier so the store + graph are populated.
        await ctx.indexer.index_all()
        try:
            yield ctx
        finally:
            await ctx.aclose()

    async def test_search_code_finds_indexed_symbol(self, indexed_context: AppContext) -> None:
        results = await indexed_context.search_code("champion routing", k=10)
        assert results
        # The base citation format is present, and the unique symbol's file shows.
        joined = "\n".join(r.formatted for r in results)
        assert "[SOURCE:" in joined
        assert "pkg/router.py" in joined

    async def test_index_status_reports_healthy(self, indexed_context: AppContext) -> None:
        status = await indexed_context.index_status()
        assert status.files_indexed >= 1
        assert status.files_failed == 0

    async def test_get_symbol_resolves_exact_definition(
        self, indexed_context: AppContext
    ) -> None:
        symbol = await indexed_context.get_symbol("champion_routing")
        assert symbol.qualified_name == "champion_routing"
        assert symbol.file_path == "pkg/router.py"
        assert "def champion_routing" in symbol.source

    async def test_read_file_returns_real_span(self, indexed_context: AppContext) -> None:
        span = await indexed_context.read_file("custom", "pkg/router.py", 1, 1)
        assert span.text.startswith("import os")
        assert span.header.startswith("[SOURCE:custom:pkg/router.py:1-1]")

    async def test_save_then_recall_memory_roundtrips(
        self, indexed_context: AppContext
    ) -> None:
        await indexed_context.save_memory("champion routing lives in pkg/router.py")
        recalled = await indexed_context.recall_memory("where is champion routing", k=5)
        assert any("pkg/router.py" in m.text for m in recalled)

    async def test_what_imports_traverses_graph(self, indexed_context: AppContext) -> None:
        importers = await indexed_context.what_imports("os")
        assert any(n.qualified_name == "pkg.router" for n in importers)

    async def test_blast_radius_traverses_graph(self, indexed_context: AppContext) -> None:
        # ChampionRouter inherits nothing, but the module DEFINES it, so the
        # module is a reverse-dependency of the class within depth 1.
        radius = await indexed_context.blast_radius("pkg.router.ChampionRouter", depth=2, max_results=20)
        names = {n.qualified_name for n in radius}
        assert "pkg.router" in names

    async def test_tests_for_returns_list(self, indexed_context: AppContext) -> None:
        # No test files in this corpus, so the result is an empty list — the tool
        # returns a well-formed (empty) list, never an error.
        result = await indexed_context.tests_for("champion_routing")
        assert isinstance(result, list)

    async def test_reindex_brings_a_new_file_current(
        self, indexed_context: AppContext, tmp_path: Path
    ) -> None:
        # Write a NEW file then reindex: it becomes searchable (read-your-writes).
        live = tmp_path / "live"
        (live / "pkg" / "extra.py").write_text(
            "def freshly_added_symbol():\n    return 7\n", encoding="utf-8"
        )
        await indexed_context.reindex()
        symbol = await indexed_context.get_symbol("freshly_added_symbol")
        assert symbol.file_path == "pkg/extra.py"


class _FakeRequestContext:
    """A stand-in for the MCP request context exposing the lifespan AppContext."""

    def __init__(self, app_context: AppContext) -> None:
        self.lifespan_context = app_context


class _FakeToolContext:
    """A stand-in FastMCP ``Context`` whose ``request_context`` carries our AppContext.

    The registered tool wrappers read ``context.request_context.lifespan_context``;
    this minimal double lets a test drive the REAL ``@mcp.tool`` wrapper body
    (including its ``.model_dump()`` serialisation) without standing up the full
    streamable-http session machinery.
    """

    def __init__(self, app_context: AppContext) -> None:
        self.request_context = _FakeRequestContext(app_context)


class TestRegisteredToolWrappers:
    """Drive the REGISTERED FastMCP tool wrappers (not the handlers) — fix #3.

    The end-to-end tests above call the :class:`AppContext` HANDLERS directly, so
    the ``@mcp.tool``-decorated wrapper bodies in ``_register_tools`` (their
    ``.model_dump()`` serialisation) had zero coverage. These drive the registered
    tool functions through the FastMCP tool manager against a real-indexed corpus,
    asserting the SERIALISED shape — a wrapper that returned the raw pydantic
    object instead of ``.model_dump()`` fails here.
    """

    @pytest_asyncio.fixture()
    async def indexed(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> AsyncIterator[tuple[Any, AppContext]]:
        """A built FastMCP server + a real-indexed AppContext sharing one corpus."""
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, client=qdrant, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        mcp = build_mcp_server(LoreServer(config))
        try:
            yield mcp, ctx
        finally:
            await ctx.aclose()

    @staticmethod
    async def _call(mcp: Any, name: str, ctx: AppContext, /, **kwargs: Any) -> Any:
        """Invoke a registered tool's wrapper fn with a fake lifespan Context."""
        tool = mcp._tool_manager.get_tool(name)  # noqa: SLF001 - test-only introspection
        return await tool.fn(_FakeToolContext(ctx), **kwargs)

    async def test_search_code_wrapper_returns_serialised_dicts(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        out = await self._call(mcp, "search_code", ctx, query="champion routing", k=10)
        # The wrapper must return a list of PLAIN dicts (.model_dump()'d), not
        # SearchResult objects — and each carries the base citation fields.
        assert isinstance(out, list) and out
        assert all(isinstance(item, dict) for item in out)
        assert any("[SOURCE:" in item["formatted"] for item in out)
        assert any("pkg/router.py" in item["formatted"] for item in out)

    async def test_get_symbol_wrapper_returns_serialised_dict(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        out = await self._call(mcp, "get_symbol", ctx, qualified_name="champion_routing")
        # A PLAIN dict, not a ResolvedSymbol — proving the wrapper's .model_dump().
        assert isinstance(out, dict)
        assert out["qualified_name"] == "champion_routing"
        assert out["file_path"] == "pkg/router.py"

    async def test_index_status_wrapper_returns_serialised_dict(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        out = await self._call(mcp, "index_status", ctx)
        assert isinstance(out, dict)
        assert out["files_indexed"] >= 1
        assert out["files_failed"] == 0


# --------------------------------------------------------------------------- #
# Double-lifespan guard (per-process heavy startup runs exactly once)
# --------------------------------------------------------------------------- #
class TestLifespanRunsOncePerProcess:
    """The heavy startup fires exactly once per process, not once per MCP session.

    Root cause: FastMCP's streamable-http composition hands the user lifespan to
    the LOW-LEVEL ``MCPServer`` (``lifespan_wrapper`` →
    ``mcp._mcp_server.lifespan``), and the session manager enters
    ``MCPServer.run`` — and therefore that lifespan — ONCE PER MCP SESSION (see
    ``StreamableHTTPSessionManager._handle_stateful_request`` → ``run_server`` →
    ``self.app.run`` → ``lifespan(self)``). So in a single uvicorn process, every
    new client session re-runs loremaster's heavy startup (probe gate → initial
    reconcile → watcher start), spawning a second watcher + a second startup
    reconcile. That is wasteful and risks manifest contention between two watchers.

    This drives the EXACT callable the framework hands each session — the composed
    ``mcp._mcp_server.lifespan`` produced by ``build_mcp_server`` →
    ``build_asgi_app`` — once per simulated session (two sessions in one process),
    spying on the heavy-startup primitives. The contract: across N sessions the
    probe gate / watcher start / initial reconcile each run exactly ONCE.
    """

    async def test_heavy_startup_runs_once_across_two_sessions(
        self, tmp_path: Path, qdrant: AsyncQdrantClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import loremaster.embedding as embedding_module
        import loremaster.server as server_module
        from conftest import _qdrant_api_key

        # The real ``_lifespan`` builds its own AsyncQdrantClient from the config's
        # api_key_env; export the throwaway server's key so it connects (the local
        # ``qdrant`` fixture reads the same key from the dotenv file).
        monkeypatch.setenv("QDRANT__SERVICE__API_KEY", _qdrant_api_key())

        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "boot.py").write_text("def boot():\n    return 1\n", encoding="utf-8")
        config = _config(slug, live)
        # The lifespan builds its own Qdrant client + collections from the config
        # slug; register both for the fixture's exact-name reap.
        qdrant._lore_created.append(f"lore_{slug}")  # type: ignore[attr-defined]
        qdrant._lore_created.append(f"lore_{slug}_memory")  # type: ignore[attr-defined]

        # Keep the lifespan hermetic: a FakeEmbedder (no live TEI), the throwaway
        # Qdrant, and tmp-path SQLite/snapshot dirs — but otherwise the REAL
        # composed lifespan the framework runs.
        # ``_lifespan`` does ``from loremaster.embedding import
        # make_embedder_from_config`` at call time, so patch it at its source.
        monkeypatch.setattr(
            embedding_module,
            "make_embedder_from_config",
            lambda _embedding_config: FakeEmbedder(dim=_DIM),
        )
        monkeypatch.setattr(server_module, "_DEFAULT_MANIFEST_DIR", tmp_path / "state")
        monkeypatch.setattr(server_module, "_DEFAULT_SNAPSHOT_ROOT", tmp_path / "snap")
        (tmp_path / "state").mkdir()

        # Spy on the heavy-startup primitives WITHOUT changing their behaviour.
        probe_calls = 0
        watcher_starts = 0
        real_probe_gate = server_module.run_probe_gate
        import loremaster.index.watcher as watcher_module

        real_watcher_start = watcher_module.LiveWatcher.start

        async def _counting_probe_gate(**kwargs: Any) -> int:
            nonlocal probe_calls
            probe_calls += 1
            return await real_probe_gate(**kwargs)

        async def _counting_watcher_start(self: Any) -> None:
            nonlocal watcher_starts
            watcher_starts += 1
            await real_watcher_start(self)

        monkeypatch.setattr(server_module, "run_probe_gate", _counting_probe_gate)
        monkeypatch.setattr(watcher_module.LiveWatcher, "start", _counting_watcher_start)

        # Build the REAL ASGI app (build_mcp_server → build_asgi_app), then reach
        # the EXACT lifespan callable the framework hands each session: the
        # low-level MCPServer's lifespan (lifespan_wrapper'd user lifespan).
        mcp = build_mcp_server(LoreServer(config))
        build_asgi_app(mcp, config)  # composes the streamable-http app (session mgr)
        per_session_lifespan = mcp._mcp_server.lifespan  # noqa: SLF001

        contexts: list[AppContext] = []
        open_cms: list[Any] = []
        try:
            # Simulate TWO MCP sessions in ONE process — the framework enters the
            # lifespan once per MCPServer.run (once per session).
            for _ in range(2):
                cm = per_session_lifespan(mcp._mcp_server)  # noqa: SLF001
                app_context = await cm.__aenter__()
                contexts.append(app_context)
                open_cms.append(cm)
        finally:
            for cm in open_cms:
                await cm.__aexit__(None, None, None)

        # The heavy startup must have run EXACTLY ONCE across the two sessions —
        # not once per session.
        assert probe_calls == 1, (
            f"probe gate ran {probe_calls}x across 2 sessions; the heavy startup "
            f"must run once per PROCESS, not once per session"
        )
        assert watcher_starts == 1, (
            f"watcher started {watcher_starts}x across 2 sessions; exactly one "
            f"watcher per process"
        )
        # Both sessions saw the SAME shared AppContext (reuse, not a rebuild).
        assert contexts[0] is contexts[1], (
            "the second session must reuse the first session's AppContext, not "
            "build a second one"
        )


class TestProcessLifespanGuard:
    """The run-once guard's lease lifecycle: reuse, last-release teardown, retry.

    These drive the guard's contract directly with lightweight async doubles (no
    Qdrant / embedder needed) so the build/reuse/teardown/recovery behaviour is
    pinned independently of the full lifespan integration above.
    """

    @staticmethod
    def _build_factory(builds: list[int], *, fail_times: int = 0) -> Any:
        """Return an async ``(context, client)`` factory that records each build.

        Args:
            builds: A list each successful build appends to (so a test counts them).
            fail_times: The number of leading builds that raise before one succeeds
                (to exercise the no-cache-on-failure retry path).
        """

        class _FakeContext:
            def __init__(self) -> None:
                self.closed = False

            async def aclose(self) -> None:
                self.closed = True

        class _FakeClient:
            def __init__(self) -> None:
                self.closed = False

            async def close(self) -> None:
                self.closed = True

        attempts = {"n": 0}

        async def _factory() -> tuple[Any, Any]:
            attempts["n"] += 1
            if attempts["n"] <= fail_times:
                raise RuntimeError("build failed")
            builds.append(1)
            return _FakeContext(), _FakeClient()

        return _factory

    async def test_two_sessions_build_once_and_reuse(self) -> None:
        from loremaster.server import _ProcessLifespanGuard

        builds: list[int] = []
        guard = _ProcessLifespanGuard(self._build_factory(builds))
        first: Any = await guard.acquire()
        second: Any = await guard.acquire()
        assert first is second  # reuse, not rebuild
        assert len(builds) == 1
        await guard.release()
        await guard.release()

    async def test_context_stays_live_until_last_release(self) -> None:
        from loremaster.server import _ProcessLifespanGuard

        builds: list[int] = []
        guard = _ProcessLifespanGuard(self._build_factory(builds))
        first: Any = await guard.acquire()
        await guard.acquire()
        # Release ONE lease: the still-leased context must NOT be torn down.
        await guard.release()
        assert first.closed is False, (
            "a context with a still-active session lease must not be closed"
        )
        # Release the LAST lease: now it tears down (aclose + client close).
        await guard.release()
        assert first.closed is True

    async def test_sequential_sessions_rebuild_after_full_release(self) -> None:
        from loremaster.server import _ProcessLifespanGuard

        builds: list[int] = []
        guard = _ProcessLifespanGuard(self._build_factory(builds))
        first: Any = await guard.acquire()
        await guard.release()  # drop to zero — the first generation is torn down
        assert first.closed is True
        # A later session over the SAME guard rebuilds (the guard tracks "live",
        # not "ever-built"), so a clean idle process still comes back up.
        second: Any = await guard.acquire()
        assert second is not first
        assert len(builds) == 2
        await guard.release()

    async def test_build_failure_is_not_cached_and_next_lease_retries(self) -> None:
        from loremaster.server import _ProcessLifespanGuard

        builds: list[int] = []
        guard = _ProcessLifespanGuard(self._build_factory(builds, fail_times=1))
        # The first lease's build raises — the failure must propagate and NOT be
        # cached (a transient embedder outage must not wedge the process).
        with pytest.raises(RuntimeError, match="build failed"):
            await guard.acquire()
        assert builds == []
        # The next lease retries and succeeds.
        ctx: Any = await guard.acquire()
        assert ctx is not None
        assert len(builds) == 1
        await guard.release()

    async def test_extra_release_is_a_noop(self) -> None:
        from loremaster.server import _ProcessLifespanGuard

        builds: list[int] = []
        guard = _ProcessLifespanGuard(self._build_factory(builds))
        ctx: Any = await guard.acquire()
        await guard.release()
        assert ctx.closed is True
        # An extra release (more exits than enters can't happen normally, but the
        # guard must be robust) is a no-op — no negative refcount, no double-close.
        await guard.release()
        assert ctx.closed is True


# --------------------------------------------------------------------------- #
# Auth wiring
# --------------------------------------------------------------------------- #
class TestAuthWiring:
    """The built ASGI app is Bearer-gated iff an enabled auth block is configured."""

    async def test_no_auth_block_leaves_app_ungated(self, tmp_path: Path) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")  # no auth block
        mcp = build_mcp_server(LoreServer(config))
        app = build_asgi_app(mcp, config)
        # An ungated app is NOT the Bearer middleware.
        from loremaster.auth import BearerAuthMiddleware

        assert not isinstance(app, BearerAuthMiddleware)

    async def test_enabled_auth_block_wraps_in_bearer_middleware(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from loremaster.auth import BearerAuthMiddleware

        monkeypatch.setenv("LORE_KEY_DEV", "dev-secret")
        slug = _slug()
        config = _config(
            slug,
            tmp_path / "live",
            auth={"enabled": True, "keys": [{"name": "dev", "key_env": "LORE_KEY_DEV"}]},
        )
        mcp = build_mcp_server(LoreServer(config))
        app = build_asgi_app(mcp, config)
        assert isinstance(app, BearerAuthMiddleware)


# Imported here so the auth-wiring tests above can reference it; defined in the
# server module as the single place the streamable-http app is assembled + gated.
from loremaster.server import build_asgi_app  # noqa: E402


# --------------------------------------------------------------------------- #
# LoreServer.run + __main__
# --------------------------------------------------------------------------- #
class TestRunAndMain:
    """``LoreServer.run`` serves (no longer NotImplementedError); ``__main__`` is wired."""

    def test_run_serves_the_asgi_app_on_the_configured_bind(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ``run`` must build the FastMCP streamable-http app (auth-wrapped when
        # configured) and serve it via uvicorn on the configured host/port. Spy on
        # the uvicorn Server.serve so we prove it is reached with the configured
        # bind, WITHOUT binding a socket. The lifespan is uvicorn's to drive, so a
        # spied-out serve never touches the real embedder either.
        import uvicorn

        captured: dict[str, Any] = {}

        async def _fake_serve(self: uvicorn.Server, *args: Any, **kwargs: Any) -> None:
            captured["host"] = self.config.host
            captured["port"] = self.config.port

        monkeypatch.setattr(uvicorn.Server, "serve", _fake_serve)

        slug = _slug()
        config = _config(slug, tmp_path / "live")  # host 127.0.0.1, port 9233
        LoreServer(config).run()
        assert captured["host"] == "127.0.0.1"
        assert captured["port"] == 9233

    def test_main_module_is_importable_and_has_main(self) -> None:
        import loremaster.server as server_module

        assert hasattr(server_module, "main")
        assert callable(server_module.main)

    def test_run_configures_lore_logging_before_fastmcp_root_handler(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``run`` installs the lore JSON handler BEFORE FastMCP's root handler.

        Root-cause regression (NIT4): FastMCP's ``__init__`` calls
        ``logging.basicConfig`` with a stderr ``RichHandler`` on the ROOT logger
        (``mcp.server.fastmcp.utilities.logging.configure_logging``). That fires
        inside ``build_mcp_server`` → ``FastMCP(...)``. If lore's scoped handler
        is configured LATER (only inside the per-session lifespan), then a
        ``loremaster.server`` startup event (``startup.probe_gate.pass`` etc.)
        emitted while only the root handler exists PROPAGATES to that root handler
        and renders via the default/uvicorn formatter (``server.py:743``), not our
        :class:`JsonFormatter` — so Mezmo never indexes it. The fix is to call
        ``configure_logging`` as the FIRST thing in ``run`` (before
        ``build_mcp_server`` installs the root handler), so the ``loremaster``
        namespace handler with ``propagate=False`` already exists.

        This drives the REAL ``run`` build (uvicorn ``serve`` spied out so no
        socket binds), records what root handlers existed at the instant FastMCP
        was constructed, then proves a ``loremaster.server`` record is caught by a
        lore JSON handler and does NOT escape to the root handler.
        """
        import io
        import json
        import logging as _logging

        import loremaster.server as server_module
        import uvicorn
        from loremaster.logging_setup import JsonFormatter

        # Spy: capture the root handlers present the moment FastMCP is constructed.
        real_build = server_module.build_mcp_server
        observed: dict[str, Any] = {}

        def _spy_build(server: Any) -> Any:
            # FastMCP.__init__ runs inside here and installs its root RichHandler;
            # the lore handler must ALREADY be on the loremaster logger by now.
            ns = _logging.getLogger("loremaster")
            observed["lore_handler_present_at_fastmcp_build"] = bool(ns.handlers)
            observed["lore_propagate_at_fastmcp_build"] = ns.propagate
            return real_build(server)

        monkeypatch.setattr(server_module, "build_mcp_server", _spy_build)

        async def _fake_serve(self: uvicorn.Server, *args: Any, **kwargs: Any) -> None:
            return None

        monkeypatch.setattr(uvicorn.Server, "serve", _fake_serve)

        # Reset the lore loggers so the assertion is about what ``run`` does, not
        # leftover state from another test (the autouse-style hygiene rule).
        for name in ("loremaster", "loresigil", "lorescribe"):
            lg = _logging.getLogger(name)
            lg.handlers = []
            lg.setLevel(_logging.NOTSET)
            lg.propagate = True
        try:
            slug = _slug()
            config = _config(slug, tmp_path / "live")
            LoreServer(config).run()

            # 1) The lore handler was already installed when FastMCP was built.
            assert observed["lore_handler_present_at_fastmcp_build"] is True, (
                "configure_logging must run BEFORE build_mcp_server so FastMCP's "
                "root RichHandler cannot capture loremaster.server startup events"
            )
            assert observed["lore_propagate_at_fastmcp_build"] is False

            # 2) A loremaster.server record routes to the lore JSON handler and does
            #    NOT escape to the root handler (FastMCP's RichHandler).
            ns = _logging.getLogger("loremaster")
            assert len(ns.handlers) == 1
            handler = ns.handlers[0]
            assert isinstance(handler, _logging.StreamHandler)
            assert isinstance(handler.formatter, JsonFormatter)

            lore_buf = io.StringIO()
            handler.setStream(lore_buf)
            root_buf = io.StringIO()
            root_handler = _logging.StreamHandler(root_buf)
            root_handler.setFormatter(_logging.Formatter("ROOT %(message)s %(filename)s"))
            root_logger = _logging.getLogger()
            root_logger.addHandler(root_handler)
            try:
                _logging.getLogger("loremaster.server").info(
                    "startup.probe_gate.pass", extra={"observed_dim": _DIM}
                )
            finally:
                root_logger.removeHandler(root_handler)

            # The lore handler emitted parseable JSON carrying the structured extra.
            lore_lines = [ln for ln in lore_buf.getvalue().splitlines() if ln.strip()]
            assert len(lore_lines) == 1
            payload = json.loads(lore_lines[0])
            assert payload["msg"] == "startup.probe_gate.pass"
            assert payload["logger"] == "loremaster.server"
            assert payload["observed_dim"] == _DIM
            # And NOTHING leaked to the root handler (propagation stopped at lore).
            assert root_buf.getvalue() == ""
        finally:
            for name in ("loremaster", "loresigil", "lorescribe"):
                lg = _logging.getLogger(name)
                lg.handlers = []
                lg.setLevel(_logging.NOTSET)
                lg.propagate = True
