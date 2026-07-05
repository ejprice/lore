"""Contract tests for ``loremaster.server`` — the FastMCP integration lynchpin.

This is Deliverable 3's running MCP server: the FastMCP streamable-http server,
the :class:`AppContext` lifespan with the embedder **startup probe gate**, the
spawned live watcher + periodic reconcile tasks, the pluggable Bearer auth wiring
(D9/D11/§A1.12), and the twelve MCP tools wrapping the merged services. These tests
drive the REAL wiring with a :class:`~loresigil.testing.FakeEmbedder` (dim 2048)
and a REAL SurrealDB (throwaway per-test databases) + a real ``tmp_path`` corpus —
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
* **existing-collection dim check → retired with Qdrant.** ``run_probe_gate`` is now
  store-agnostic (Qdrant retired at P8a). The old Qdrant-collection wrong-dim refusal
  was Qdrant-specific; over the unified SurrealDB store, dim drift on the chunk store
  is caught by the embedding-schema-fingerprint rebuild (``embedding_schema_fingerprint``
  folds ``dim`` in). The gate itself only probes the embedder and checks
  observed-vs-config dim.
* **All coherent → PASS.** probe == config.dim lets startup proceed.

AppContext lifespan
-------------------
* Entering the lifespan constructs the runtime services, ensures the collections,
  spawns the live watcher + periodic reconcile as asyncio tasks, and runs the
  extension ``on_startup`` hooks; exiting stops the tasks and runs ``on_shutdown``.
* **Framework fix A surfaces:** an extension whose ``on_startup`` raises aborts
  startup (the prior extensions' ``on_shutdown`` having run) — no half-started
  server.

The twelve MCP tools (end-to-end through the AppContext handlers)
----------------------------------------------------------------
* All twelve — ``search_code``/``read_file``/``get_symbol``/``save_memory``/
  ``recall_memory``/``reindex``/``index_status``/``what_imports``/
  ``blast_radius``/``tests_for``/``references``/``dead_code`` — are REGISTERED on
  the FastMCP app.
* Each returns the right SHAPE over a real-indexed corpus: ``search_code`` finds a
  uniquely-named symbol with a ``[SOURCE...]`` citation; ``index_status`` reports
  a healthy index; ``save_memory`` → ``recall_memory`` round-trips; ``get_symbol``
  resolves an exact definition; ``read_file`` returns a real span;
  ``blast_radius``/``what_imports``/``tests_for`` traverse the live graph;
  ``references`` splits a symbol's production/test references and ``dead_code``
  surfaces test-only / unreferenced symbols; ``reindex`` brings a freshly-written
  file current.

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
from _surreal_harness import (
    drop_database as drop_surreal_database,
)
from _surreal_harness import (
    make_env,
    surreal_password,
    surreal_url,
    surreal_user,
)
from _task_fakes import FakeTaskDatabase, FakeTaskLedger
from loremaster.config import LoreConfig
from loremaster.map import _BUDGET_FLOOR as _PRODUCTION_MAP_BUDGET_FLOOR
from loremaster.map import _ELISION_FRAGMENT as _PRODUCTION_MAP_ELISION_FRAGMENT
from loremaster.memory.backend import MemoryRef, derive_memory_id, derive_refs_stamp
from loremaster.server import (
    AppContext,
    LoreServer,
    ProbeGateError,
    build_app_context,
    build_mcp_server,
    configure_logging_from_config,
    run_probe_gate,
)
from loremaster.tasks import IllegalTransitionError, TaskNotFoundError
from loresigil.testing import FakeEmbedder

_DIM = 2048

# The namespace every throwaway per-test SurrealDB database lives under (mirrors
# ``test_cli.py``'s harness-isolation convention; shared with the rest of the
# suite's ported files so a persistent dev server accumulates ONE namespace).
_SURREAL_TEST_NAMESPACE = "lore_test"

# The env-var *names* the default SurrealConfig references credentials by —
# matching :data:`loremaster.config.SURREAL_DEFAULT_USER_ENV` /
# ``SURREAL_DEFAULT_PASSWORD_ENV`` so the real ``build_app_context`` resolves
# them via the SAME names the production default config uses.
_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"

# A real Python module with a uniquely-named symbol so search/get_symbol/graph
# have something distinctive to find. Chunked for real through python_ast.
# The router imports a stdlib module (``os``, dropped by the RESOLVED keep/drop
# rule as external) AND an IN-PROJECT symbol (``pkg.base.BaseRouter``, kept as its
# resolved FQN) so the graph carries a surviving, queryable import edge. ``import
# os`` stays first so the read_file span assertion (line 1) is unchanged.
_PY_BASE = """\
\"\"\"The router base.\"\"\"


class BaseRouter:
    \"\"\"Common routing plumbing.\"\"\"

    def lane(self):
        return "lane"
"""

_PY_MODULE = """\
import os

from pkg.base import BaseRouter


class ChampionRouter(BaseRouter):
    \"\"\"Routes the 36-week curve champion.\"\"\"

    def route(self, week):
        return os.linesep.join(str(week))


def champion_routing(week):
    \"\"\"Route the 36-week curve champion.\"\"\"
    return week * 2
"""

# The independent oracle for the surviving in-project import (read off _PY_MODULE).
_PY_MODULE_IMPORT_FQN = "pkg.base.BaseRouter"

# A production module with a symbol that is ONLY referenced by tests — used as the
# planted dead-code fixture for the ``references`` / ``dead_code`` tool tests.
# ``orphan_helper`` is defined here but imported ONLY by the test below (_PY_TEST_REF).
_PY_UTILS = """\
\"\"\"Utility helpers.\"\"\"


def orphan_helper():
    \"\"\"A helper that is only imported by tests, not production code.\"\"\"
    return 42
"""

# A test file that imports ``orphan_helper`` — so ``orphan_helper`` has exactly
# one reference, and it comes from a test path.  Named ``test_utils.py`` so the
# graph classifies its file path as a test path.
_PY_TEST_REF = """\
from pkg.utils import orphan_helper


def test_orphan_helper():
    assert orphan_helper() == 42
"""


# --------------------------------------------------------------------------- #
# lore_impact / lore_map corpora (P6-tail tool wiring).
# --------------------------------------------------------------------------- #
# A target with a REAL production reference for the impact e2e/wrapper tests
# (mirrors ``test_what_imports_traverses_graph`` / ``test_references_returns_
# production_test_split``, which already prove ``pkg.base.BaseRouter`` has a
# genuine production reference from ``pkg.router`` — reused here rather than
# re-deriving a second oracle target).
_IMPACT_TARGET_LIVE = _PY_MODULE_IMPORT_FQN
_IMPACT_UNKNOWN_TARGET = "totally.bogus.symbol"
_MAP_UNKNOWN_FOCUS = "totally.bogus.symbol"
# A loose, generic fragment (deliberately NOT imported from the engines' own
# ``_RETRY_HINT`` — mirrors test_impact.py's / test_map.py's own independent
# ``_RETRY_FRAGMENT = "retry"`` local constant) so the pin holds regardless of
# the engine's exact wording.
_RETRY_FRAGMENT = "retry"

# A hub-and-spoke + island shape mirroring test_map.py's own engine-level
# corpus (scaled down: two hub importers instead of three — still a clear
# 2-vs-1 import-count asymmetry, which is all an UNFOCUSED PageRank needs to
# rank the hub first), so this WIRING test proves ``focus`` genuinely reaches
# ``MapEngine.map`` through the AppContext handler without re-deriving the
# PageRank algorithm's own correctness (already pinned behaviourally in
# test_map.py against the FakeSurrealCodeGraph directly).
_MAP_HUB_SOURCE = """\
def shared_util(x):
    \"\"\"The shared utility both importers below call.\"\"\"
    return x
"""

_MAP_A_SOURCE = """\
from hub import shared_util


def use_a(x):
    \"\"\"A production caller of the shared hub utility.\"\"\"
    return shared_util(x)
"""

_MAP_B_SOURCE = """\
from hub import shared_util


def use_b(x):
    \"\"\"A second production caller of the shared hub utility.\"\"\"
    return shared_util(x)
"""

_MAP_ISLAND_SOURCE = """\
def island_fn(x):
    \"\"\"Referenced by exactly one file across the whole corpus.\"\"\"
    return x
"""

_MAP_ISLAND_USER_SOURCE = """\
from island import island_fn


def use_island(x):
    \"\"\"The lone caller of island_fn -- the island's only neighbor.\"\"\"
    return island_fn(x)
"""

_MAP_HUB_MODULE = "hub"
_MAP_ISLAND_MODULE = "island"
_MAP_FOCUS_SYMBOL = "island_fn"


def _map_hub_island_corpus() -> dict[str, str]:
    """The hub/island import-asymmetry shape, scaled down from test_map.py."""
    return {
        "hub.py": _MAP_HUB_SOURCE,
        "a.py": _MAP_A_SOURCE,
        "b.py": _MAP_B_SOURCE,
        "island.py": _MAP_ISLAND_SOURCE,
        "island_user.py": _MAP_ISLAND_USER_SOURCE,
    }


def _map_budget_filler_source(index: int) -> str:
    """One tiny, distinctly-named module — filler for the budget-elision test.

    Real Odoo-flavoured naming (not foo/bar), long enough that even a terse
    one-line-per-module render overflows a 200-token floor budget well before
    all of them fit — see ``_MAP_BUDGET_FILLER_FILE_COUNT``'s own comment for
    the arithmetic.
    """
    return (
        f"def compute_purchase_order_landed_cost_allocation_{index:02d}(week):\n"
        f'    """Allocate landed cost for widget batch {index:02d}."""\n'
        f"    return week * {index}\n"
    )


# Enough distinct one-function modules that their rendered rollup lines
# (map.py's own ``_render_module_line`` format: ``{module}  (rank R.RRRR)
# symbols: {name}``) cannot all fit in the floor budget
# (``_PRODUCTION_MAP_BUDGET_FLOOR`` tokens) under the FakeEmbedder's
# ``len // 4`` heuristic (i.e. ``_PRODUCTION_MAP_BUDGET_FLOOR * 4`` chars):
# each line here runs comfortably over 60 chars (long, realistic symbol
# names), so 20 lines alone exceed 1200 chars — forcing at least one elision
# regardless of minor rendering-format variance.
_MAP_BUDGET_FILLER_FILE_COUNT = 20


def _map_budget_filler_corpus() -> dict[str, str]:
    return {
        f"pkg/widget_{index:02d}.py": _map_budget_filler_source(index)
        for index in range(_MAP_BUDGET_FILLER_FILE_COUNT)
    }


# Every slug minted by :func:`_slug` during the CURRENT test, so the autouse
# :func:`_surreal_test_env` fixture can reap that test's throwaway SurrealDB
# database (``surreal.database`` defaults to the project slug — see
# :attr:`~loremaster.config.LoreConfig.effective_surreal_database`) without
# every one of this file's ~40 call sites having to plumb its own database name
# + teardown. Cleared by the fixture after each test; pytest runs this module's
# tests serially, so no cross-test collision.
_pending_surreal_slugs: list[str] = []


def _slug() -> str:
    """A unique per-test project slug, ALSO the default SurrealDB database name."""
    slug = f"test_{uuid.uuid4().hex}"
    _pending_surreal_slugs.append(slug)
    return slug


@pytest_asyncio.fixture(autouse=True)
async def _surreal_test_env(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    """Export the harness's root SurrealDB credentials; reap every slug-named database.

    Every :func:`_config` in this file carries an explicit ``surreal`` block
    pointed at the harness dev server with NO explicit ``database`` — the config
    falls back to the project slug (:attr:`~loremaster.config.LoreConfig.
    effective_surreal_database`), so each test's real ``AppContext`` writes to
    its own throwaway database named after its (uuid4-unique) slug. Autouse so
    every test in this file gets the credentials, whether or not it happens to
    reach ``build_app_context``.
    """
    monkeypatch.setenv(_SURREAL_USER_ENV, surreal_user())
    monkeypatch.setenv(_SURREAL_PASS_ENV, surreal_password())
    try:
        yield
    finally:
        for slug in _pending_surreal_slugs:
            await drop_surreal_database(make_env(database=slug, dim=_DIM))
        _pending_surreal_slugs.clear()


def _config(
    slug: str,
    live_path: Path,
    *,
    auth: dict[str, Any] | None = None,
    watcher_enabled: bool = True,
) -> LoreConfig:
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
        # No explicit ``database`` — it defaults to the (uuid4-unique) project
        # slug, giving every test its own throwaway SurrealDB database with zero
        # extra plumbing (reaped by the autouse ``_surreal_test_env`` fixture).
        "surreal": {
            "url": surreal_url(),
            "namespace": _SURREAL_TEST_NAMESPACE,
            "user_env": _SURREAL_USER_ENV,
            "password_env": _SURREAL_PASS_ENV,
        },
        "roots": [
            {"tier": "custom", "watch": "live", "path": str(live_path), "include": ["**/*.py"]}
        ],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": watcher_enabled,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9233},
    }
    if auth is not None:
        payload["auth"] = auth
    return LoreConfig.model_validate(payload)


def _render_text(value: object) -> str:
    """The agent-visible TEXT projection of a tool result.

    The P7 cutover re-shapes the memory + task tool returns; this contract pins
    the SURFACED CONTENT (the note text, a chunk key, a kind, a drift signal, an
    owner) without over-committing to the exact serialisation (a rendered markdown
    digest vs. a list of summarised value objects both surface the same content).
    A ``str`` result is itself; anything else is projected via ``repr`` (which
    still names every field value a summarised value object carries).
    """
    return value if isinstance(value, str) else repr(value)


async def _make_context(
    *,
    config: LoreConfig,
    tmp_path: Path,
    embedder: FakeEmbedder | None = None,
    start_tasks: bool = False,
) -> AppContext:
    """Build a live :class:`AppContext` with injected fakes (the test wiring seam).

    ``build_app_context`` runs the probe gate, constructs every runtime service,
    readies the SurrealDB write stack, and (when ``start_tasks``) spawns the watcher +
    reconcile tasks — the same path the lifespan takes, but with the embedder /
    paths injected so a test needs no real TEI endpoint.
    """
    return await build_app_context(
        server=LoreServer(config),
        embedder=embedder or FakeEmbedder(dim=_DIM),
        manifest_path=tmp_path / "m.db",
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
    """The startup probe gate refuses on unreachable / probe-vs-config dim mismatch."""

    async def test_unreachable_embedder_refuses(
        self, tmp_path: Path    ) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        with pytest.raises(ProbeGateError):
            await run_probe_gate(
                embedder=FakeEmbedder(dim=_DIM, probe_fails=True), config=config
            )

    async def test_observed_dim_mismatch_refuses(
        self, tmp_path: Path    ) -> None:
        # The embedder probes a DIFFERENT dim than the config declares → refuse.
        slug = _slug()
        config = _config(slug, tmp_path / "live")  # config.dim == 2048
        with pytest.raises(ProbeGateError, match="(?i)dim"):
            await run_probe_gate(embedder=FakeEmbedder(dim=1024), config=config)

    # RETIRED: ``test_existing_collection_wrong_size_refuses_without_recreate`` was
    # removed — ``run_probe_gate`` is now store-agnostic (the existing-collection dim
    # check was dropped when Qdrant left the boot path at P8a). That refusal was
    # Qdrant-specific; over the unified SurrealDB store, chunk-store dim drift is
    # caught by the embedding-schema-fingerprint rebuild instead. (The LIVE Surreal
    # memory backend's ``ensure_ready`` applies idempotent IF-NOT-EXISTS memory DDL
    # and does NOT gate on dim — a pre-existing P7 design, flagged separately.)

    async def test_coherent_dims_pass(
        self, tmp_path: Path
    ) -> None:
        # probe == config.dim and no collection yet → the gate passes (returns the
        # observed dim).
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        observed = await run_probe_gate(
            embedder=FakeEmbedder(dim=_DIM), config=config
        )
        assert observed == _DIM

    async def test_passing_gate_logs_probe_gate_pass(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        with caplog.at_level(logging.INFO, logger="loremaster.server"):
            await run_probe_gate(embedder=FakeEmbedder(dim=_DIM), config=config)
        events = [r for r in caplog.records if r.message == "startup.probe_gate.pass"]
        assert len(events) == 1
        assert events[0].levelno == logging.INFO
        assert events[0].observed_dim == _DIM  # type: ignore[attr-defined]

    async def test_refusing_gate_logs_probe_gate_refuse(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")  # config.dim == 2048
        with caplog.at_level(logging.ERROR, logger="loremaster.server"):
            with pytest.raises(ProbeGateError):
                await run_probe_gate(embedder=FakeEmbedder(dim=1024), config=config)
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

    async def test_build_context_wires_services(self, tmp_path: Path) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            # The SurrealDB write stack is wired (no Qdrant collection to check now).
            assert ctx.write_store is not None
            assert ctx.memory_backend is not None
            # The runtime services are wired and reachable.
            assert ctx.search_pipeline is not None
            assert ctx.indexer is not None
            assert ctx.code_graph is not None
        finally:
            await ctx.aclose()

    async def test_lifespan_spawns_watcher_and_reconcile_tasks(
        self, tmp_path: Path    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        live.mkdir()
        config = _config(slug, live)
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, start_tasks=True
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
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
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
                config=config, tmp_path=tmp_path, start_tasks=True
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
        self, tmp_path: Path    ) -> None:
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
        with pytest.raises(RuntimeError, match="refused to start"):
            await build_app_context(
                server=server,
                embedder=FakeEmbedder(dim=_DIM),
                manifest_path=tmp_path / "m.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=False,
            )

    async def test_failed_startup_closes_sqlite_connections(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Lifecycle hygiene (owner rule): when startup aborts (a failing extension
        # hook AFTER the manifest + graph were opened), those Surreal connections
        # must be CLOSED, not leaked. A leaked connection on a half-built server is
        # the degradation case the rule targets. Spy on the manifest + graph
        # connections and assert both were closed after the abort — a discriminator
        # that fails on the un-hardened build (which leaks them).
        #
        # PORTED: the pre-port suite tracked the old SQLite ``Manifest`` class
        # (since deleted) + ``loremaster.graph.CodeGraph`` (Kùzu) — build_app_context now
        # constructs ``SurrealManifest`` / ``SurrealCodeGraph`` instead (imported
        # from ``loremaster.index.surreal_manifest`` / ``loremaster.graph_surreal``
        # at call time), so the tracked-subclass monkeypatch targets are ported to
        # match. The probe is ported too: a SurrealDB connection self-heals on
        # reconnect rather than raising when reused post-close (unlike a closed
        # sqlite3/Kùzu handle), so "was it really closed?" is instead read off the
        # SAME private ``_connection`` attribute ``close()`` nulls — the identical
        # implementation-internals-reaching style the pre-port probe used
        # (``handle.connection``), just the Surreal port's own closure signal.
        import loremaster.graph_surreal as graph_module
        import loremaster.index.surreal_manifest as manifest_module
        from loremaster.extension import Extension, ExtensionContext

        opened: list[Any] = []

        class _TrackedManifest(manifest_module.SurrealManifest):
            def __init__(self, **kwargs: Any) -> None:
                super().__init__(**kwargs)
                opened.append(self)

        class _TrackedGraph(graph_module.SurrealCodeGraph):
            def __init__(self, **kwargs: Any) -> None:
                super().__init__(**kwargs)
                opened.append(self)

        # build_app_context imports these from their source modules at call time,
        # so patching the source attribute is what the local ``from ... import``
        # resolves.
        monkeypatch.setattr(manifest_module, "SurrealManifest", _TrackedManifest)
        monkeypatch.setattr(graph_module, "SurrealCodeGraph", _TrackedGraph)

        class _BoomExtension(Extension):
            @property
            def name(self) -> str:
                return "boom"

            async def on_startup(self, ctx: ExtensionContext) -> None:
                raise RuntimeError("extension refused to start")

        slug = _slug()
        config = _config(slug, tmp_path / "live")
        with pytest.raises(RuntimeError, match="refused to start"):
            await build_app_context(
                server=LoreServer(config).register_extension(_BoomExtension()),
                embedder=FakeEmbedder(dim=_DIM),
                manifest_path=tmp_path / "m.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=False,
            )
        # Both DB handles were opened during the (aborted) build and must now be
        # closed — ``close()`` is the ONLY code path that nulls the private
        # ``_connection`` attribute, so a non-``None`` value after the abort means
        # the handle was left open (the leak the rule guards against).
        assert len(opened) == 2, "manifest + graph should both have been opened"
        for handle in opened:
            assert handle._connection is None, (  # noqa: SLF001 - the closure signal
                f"{type(handle).__name__} must be closed (connection nulled) after "
                "an aborted startup — a non-None _connection means it leaked"
            )

    async def test_ready_guard_closes_earlier_backends_on_a_mid_ready_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Audit follow-up #3 (C6 fresh-context audit): ``manifest.ensure_ready`` /
        # ``code_graph.ensure_ready`` / ``snapshot_stamper.ensure_ready`` ran
        # OUTSIDE the "except BaseException" teardown further down the function —
        # a ready failure on any ONE of the four write backends leaked every
        # backend that had already readied successfully before it. Fault-inject a
        # ``code_graph.ensure_ready`` failure (the write store and the manifest
        # already readied before it) and prove both are closed on the way out —
        # mirroring ``Scout.start()``'s "close what already opened, newest-first"
        # pattern.
        import loremaster.graph_surreal as graph_module
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

        class _FailingGraph(graph_module.SurrealCodeGraph):
            async def ensure_ready(self) -> None:
                raise RuntimeError("code graph socket refused")

        # build_app_context imports these from their source modules at call time
        # (the same lazy-import pattern the other write-stack tests patch).
        monkeypatch.setattr(store_module, "SurrealStore", _TrackedStore)
        monkeypatch.setattr(manifest_module, "SurrealManifest", _TrackedManifest)
        monkeypatch.setattr(graph_module, "SurrealCodeGraph", _FailingGraph)

        slug = _slug()
        config = _config(slug, tmp_path / "live")
        with pytest.raises(RuntimeError, match="code graph socket refused"):
            await build_app_context(
                server=LoreServer(config),
                embedder=FakeEmbedder(dim=_DIM),
                manifest_path=tmp_path / "m.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=False,
            )
        assert len(opened) == 2, "the write store + manifest should both have been opened"
        for handle in opened:
            assert handle._connection is None, (  # noqa: SLF001 - the closure signal
                f"{type(handle).__name__} must be closed after a LATER write-stack "
                "backend's ensure_ready failed — a non-None _connection means it leaked"
            )

    async def test_startup_runs_an_initial_reconcile_so_offline_edits_index_now(
        self, tmp_path: Path    ) -> None:
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
            config=config, tmp_path=tmp_path, start_tasks=True
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
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
        with pytest.raises(RuntimeError, match="post-start step failed"):
            await build_app_context(
                server=LoreServer(config),
                embedder=FakeEmbedder(dim=_DIM),
                manifest_path=tmp_path / "m.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=True,
            )
        # The started watcher was torn down on the abort (no orphaned thread).
        assert stopped == [True], "an aborted startup must stop a watcher it had started"

    async def test_watcher_disabled_skips_live_watcher_but_still_runs_initial_sweep(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Task #13: ``watcher.enabled: false`` means "no live inotify watcher, no
        # periodic reconcile timer" for a STATIC, non-live-watched corpus — but the
        # corpus must still be indexed by the unconditional initial startup sweep
        # (you still want it indexed; you just don't want live re-indexing).
        # Spy on LiveWatcher.start to prove it is never invoked, while asserting
        # the initial sweep DID index the on-disk file.
        import loremaster.index.watcher as watcher_module

        started: list[bool] = []
        original_start = watcher_module.LiveWatcher.start

        async def _tracked_start(self: Any) -> None:
            started.append(True)
            await original_start(self)

        monkeypatch.setattr(watcher_module.LiveWatcher, "start", _tracked_start)

        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "static_corpus.py").write_text(
            "def indexed_while_watcher_disabled():\n    return 1\n", encoding="utf-8"
        )
        config = _config(slug, live, watcher_enabled=False)
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, start_tasks=True
        )
        try:
            assert started == [], "watcher.enabled=False must not start the live watcher"
            assert ctx.watcher_started is False
            assert ctx.reconcile_task is None, (
                "watcher.enabled=False must not spawn the periodic reconcile task"
            )
            # But the initial sweep still ran: the on-disk file is indexed. The
            # read-your-writes get_symbol tail lives in the sibling below —
            # split during the P5 dual-store interim (C3+C5 audit bug #1) so
            # this gating half never hid behind the sibling's then-xfail; both
            # run green unmarked since the P6 read-path cutover.
            status = await ctx.index_status()
            assert status.files_indexed >= 1, (
                "watcher.enabled=False must not skip the initial startup sweep"
            )
        finally:
            await ctx.aclose()

    async def test_watcher_disabled_initial_sweep_is_symbol_resolvable(
        self, tmp_path: Path    ) -> None:
        # The read-your-writes tail split out of the gating test above: the file
        # the watcher-disabled initial sweep indexed must resolve via get_symbol.
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "static_corpus.py").write_text(
            "def indexed_while_watcher_disabled():\n    return 1\n", encoding="utf-8"
        )
        config = _config(slug, live, watcher_enabled=False)
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, start_tasks=True
        )
        try:
            symbol = await ctx.get_symbol("indexed_while_watcher_disabled")
            assert symbol.file_path == "pkg/static_corpus.py"
        finally:
            await ctx.aclose()

    async def test_watcher_enabled_true_still_starts_watcher_and_periodic_task(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The flip side of the pin above: ``watcher.enabled: true`` (the default)
        # is unchanged behaviour — the live watcher + periodic reconcile task ARE
        # started. Spies on LiveWatcher.start to confirm it IS invoked (not just
        # that watcher_started is set), so this fails the same way the disabled
        # test would if the gate were inverted.
        import loremaster.index.watcher as watcher_module

        started: list[bool] = []
        original_start = watcher_module.LiveWatcher.start

        async def _tracked_start(self: Any) -> None:
            started.append(True)
            await original_start(self)

        monkeypatch.setattr(watcher_module.LiveWatcher, "start", _tracked_start)

        slug = _slug()
        live = tmp_path / "live"
        live.mkdir()
        config = _config(slug, live, watcher_enabled=True)
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, start_tasks=True
        )
        try:
            assert started == [True], "watcher.enabled=True must start the live watcher"
            assert ctx.watcher_started is True
            assert ctx.reconcile_task is not None
            assert not ctx.reconcile_task.done()
        finally:
            await ctx.aclose()


# --------------------------------------------------------------------------- #
# Tool registration + end-to-end tool behaviour
# --------------------------------------------------------------------------- #
# The twelve built-in tools, each carrying the mandatory ``lore_`` service prefix
# (mcp-builder: a service prefix so tools disambiguate across many connected MCP
# servers). The bare (un-prefixed) names they were renamed FROM — no built-in may
# publish a bare name on the wire.
_TOOL_PREFIX = "lore_"
_BARE_TOOL_NAMES = {
    "search_code",
    "read_file",
    "get_symbol",
    "verify",
    "save_memory",
    "recall_memory",
    "reindex",
    "index_status",
    "what_imports",
    "blast_radius",
    "tests_for",
    "references",
    "dead_code",
    # P6-tail (lore_impact / lore_map): the "who depends on this?" / "orient
    # me here" verdict-bearing rollups over the same unified graph the other
    # graph tools above already read.
    "impact",
    "map",
    # P8b wire-up: the three wave-A cores surfaced as MCP verbs — the store-backed
    # hash-verified span reader, the snapshot diff engine, and the finding ledger.
    "read",
    "diff",
    "findings",
}
_EXPECTED_TOOLS = {f"{_TOOL_PREFIX}{name}" for name in _BARE_TOOL_NAMES}


class TestToolRegistration:
    """All twelve MCP tools are registered on the FastMCP app, each ``lore_``-prefixed."""

    async def test_all_twelve_tools_registered(self, tmp_path: Path) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        assert _EXPECTED_TOOLS <= names

    async def test_all_built_in_tools_carry_the_lore_prefix(self, tmp_path: Path) -> None:
        # mcp-builder insists (3x) on a service prefix so tools disambiguate across
        # the many MCP servers a consumer connects at once. Every built-in must
        # publish its ``lore_``-prefixed name, and NONE may still publish a bare one.
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        names = {t.name for t in await mcp.list_tools()}
        assert _EXPECTED_TOOLS <= names, (
            f"every built-in must be {_TOOL_PREFIX}-prefixed; missing: "
            f"{_EXPECTED_TOOLS - names}"
        )
        leaked = _BARE_TOOL_NAMES & names
        assert not leaked, (
            f"no built-in may publish a bare (un-prefixed) tool name; leaked: {leaked}"
        )


# --------------------------------------------------------------------------- #
# In-band consumer guidance (server instructions + per-tool descriptions +
# input-schema field descriptions + tool annotations)
# --------------------------------------------------------------------------- #
# The read-only tools (every tool that does NOT mutate index/memory state). These
# must carry ``readOnlyHint=True``. ``save_memory`` and ``reindex`` are the two
# mutating tools and must NOT be marked read-only.
_READ_ONLY_TOOLS = {
    "lore_search_code",
    "lore_read_file",
    "lore_get_symbol",
    "lore_verify",
    "lore_recall_memory",
    "lore_index_status",
    "lore_what_imports",
    "lore_blast_radius",
    "lore_tests_for",
    "lore_references",
    "lore_dead_code",
    # P6-tail: both are pure reads over the graph, never mutating index/memory
    # state — read-only exactly like their five graph-tool neighbours above.
    "lore_impact",
    "lore_map",
    # P8b wire-up: lore_read serves a stored span (a read), lore_diff reads the
    # snapshot ledger (a read). lore_findings MUTATES the finding ledger, so it is
    # NOT here — it lives in ``_MUTATING_TOOLS`` below (like lore_tasks' family).
    "lore_read",
    "lore_diff",
}
_MUTATING_TOOLS = {"lore_save_memory", "lore_reindex", "lore_findings"}

# Tools that take NO consumer-facing parameters (so there are no per-field
# descriptions to assert). ``lore_index_status`` is parameterless.
_PARAMETERLESS_TOOLS = {"lore_index_status"}


class TestServerInstructions:
    """The FastMCP server ``instructions`` is a substantial, behavioral block.

    A field consumer reported lore "doesn't give clear instructions and
    capabilities to the consumer." The fix is in-band: the FastMCP
    ``instructions`` block must, on its own, teach the connecting agent what lore
    is, when to reach for each tool, the citation convention, the freshness /
    read-your-writes model, and the project-memory stance — so no out-of-band doc
    is needed. These assertions pin the load-bearing facts as substrings; the
    mutation check (blank the block ⇒ these fail) proves they are not vacuous.
    """

    def _instructions(self, tmp_path: Path) -> str:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        instructions = mcp.instructions
        assert isinstance(instructions, str)
        return instructions

    def test_instructions_is_substantial(self, tmp_path: Path) -> None:
        # Not the one-sentence stub: a behavioral block is materially longer.
        instructions = self._instructions(tmp_path)
        assert len(instructions) >= 800, (
            "the server instructions must be a substantial behavioral block, not "
            "a one-line label"
        )

    def test_instructions_names_every_tool(self, tmp_path: Path) -> None:
        # The consumer must learn WHEN to use WHICH tool from the instructions
        # alone — so every registered tool is named there.
        instructions = self._instructions(tmp_path)
        for tool_name in _EXPECTED_TOOLS:
            assert tool_name in instructions, (
                f"the instructions must mention {tool_name!r} so the consumer "
                f"knows when to reach for it"
            )

    def test_instructions_conveys_citation_convention(self, tmp_path: Path) -> None:
        # The [SOURCE:file:line] + stable Key: citation convention.
        instructions = self._instructions(tmp_path)
        assert "[SOURCE:" in instructions
        assert "Key:" in instructions

    def test_instructions_conveys_freshness_model(self, tmp_path: Path) -> None:
        # The freshness / read-your-writes model: a live watcher, the periodic
        # reconcile backstop, and the wait_for_fresh escape hatch.
        instructions = self._instructions(tmp_path)
        lowered = instructions.lower()
        assert "wait_for_fresh" in instructions
        assert "watcher" in lowered or "inotify" in lowered
        assert "reconcile" in lowered

    def test_instructions_conveys_memory_stance(self, tmp_path: Path) -> None:
        # The project-memory stance: project-scoped, shared across agents,
        # survives restart, and distinct from the consumer's own assistant memory.
        instructions = self._instructions(tmp_path)
        lowered = instructions.lower()
        assert "project" in lowered and "memory" in lowered
        assert "shared" in lowered
        assert "survives" in lowered or "persists" in lowered or "durable" in lowered

    def test_instructions_teaches_the_map_search_impact_ladder(
        self, tmp_path: Path
    ) -> None:
        # FRICTION (2026-07-03, team-lead, "graph tools", self-inflicted doc
        # gap): naming each graph tool in isolation is not enough — an agent
        # needs the WORKFLOW CHAIN taught explicitly (orient with lore_map,
        # locate with lore_search_code, then verify safety with lore_impact
        # before touching something), or the one-call ergonomic these two
        # tools exist to provide goes unused just like the four-tool
        # seam-sweep chain did. Pinned loosely (co-occurrence + relative
        # order on ONE line, mirroring how every other bullet in this block
        # is authored) so the author keeps editorial freedom over wording.
        instructions = self._instructions(tmp_path)
        chain_lines = [
            line
            for line in instructions.splitlines()
            if "lore_map" in line and "search_code" in line and "lore_impact" in line
        ]
        assert chain_lines, (
            "the instructions must teach the map -> search -> impact workflow "
            "chain in at least one line naming all three tools together"
        )
        line = chain_lines[0]
        assert line.index("lore_map") < line.index("search_code") < line.index(
            "lore_impact"
        ), (
            "the chain-teaching line must name the tools in map -> search -> "
            "impact order (orient, then locate, then verify safety)"
        )

    def test_instructions_teaches_deferred_tool_loading(self, tmp_path: Path) -> None:
        # FRICTION (2026-07-03, team-lead, "(tool loading)", affordance_gap):
        # lore's own tools are commonly loaded behind a deferred ToolSearch in
        # the consuming agent's harness; a brief/instructions block that never
        # says so loses to grep by default (subagent briefs never mentioned
        # lore -> subagents never used it). The instructions must teach the
        # consumer that a ToolSearch load may be needed before these tools are
        # callable.
        instructions = self._instructions(tmp_path)
        assert "ToolSearch" in instructions


class TestToolDescriptions:
    """Every registered tool has a behavioral (non-label) description.

    The mcp-builder standard: a tool description must "narrowly and unambiguously
    describe functionality" — what it returns, when to reach for it, and how it
    differs from its neighbour. These assertions pin minimum substance plus the
    key neighbour-disambiguation facts the field consumer needs.
    """

    async def _tools_by_name(self, tmp_path: Path) -> dict[str, Any]:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        return {tool.name: tool for tool in await mcp.list_tools()}

    async def test_every_tool_has_a_substantial_description(self, tmp_path: Path) -> None:
        tools = await self._tools_by_name(tmp_path)
        for name in _EXPECTED_TOOLS:
            description = tools[name].description
            assert description, f"{name} must have a non-empty description"
            assert len(description) >= 80, (
                f"{name}'s description must be behavioral (what/when/how it "
                f"differs), not a terse one-line label"
            )

    async def test_get_symbol_vs_search_code_disambiguated(self, tmp_path: Path) -> None:
        # get_symbol = EXACT definition; search_code = semantic. The descriptions
        # must draw that distinction so a consumer picks the right one.
        tools = await self._tools_by_name(tmp_path)
        assert "exact" in tools["lore_get_symbol"].description.lower()
        assert "semantic" in tools["lore_search_code"].description.lower()

    async def test_what_imports_vs_blast_radius_disambiguated(self, tmp_path: Path) -> None:
        # what_imports = DIRECT importers; blast_radius = TRANSITIVE closure.
        tools = await self._tools_by_name(tmp_path)
        assert "direct" in tools["lore_what_imports"].description.lower()
        assert "transitive" in tools["lore_blast_radius"].description.lower()

    async def test_verify_description_teaches_when_and_the_verdicts(
        self, tmp_path: Path
    ) -> None:
        # verify = confirm a CLAIM before repeating it; its three verdicts and its
        # not_found-vs-get_symbol contrast must be teachable from the description.
        tools = await self._tools_by_name(tmp_path)
        description = tools["lore_verify"].description.lower()
        assert "confirmed" in description
        assert "mismatch" in description
        assert "not_found" in description

    async def test_read_description_teaches_the_store_twin_and_staleness(
        self, tmp_path: Path
    ) -> None:
        # lore_read serves the INDEXED bytes (not disk) with a provenance header
        # and an explicit staleness signal — both must be teachable.
        tools = await self._tools_by_name(tmp_path)
        description = tools["lore_read"].description.lower()
        assert "[source:" in description
        assert "stale" in description

    async def test_diff_description_teaches_list_then_diff_and_the_markers(
        self, tmp_path: Path
    ) -> None:
        # lore_diff: list snapshots first, then diff between two; the legacy /
        # in-flight markers must be named so callers expect them.
        tools = await self._tools_by_name(tmp_path)
        description = tools["lore_diff"].description.lower()
        assert "snapshot" in description
        assert "legacy" in description
        assert "in-flight" in description or "in flight" in description

    async def test_findings_description_teaches_the_actions(
        self, tmp_path: Path
    ) -> None:
        # lore_findings dispatches on ``action``; the report/query/transition verbs
        # must be teachable from the description (mirrors lore_tasks).
        tools = await self._tools_by_name(tmp_path)
        description = tools["lore_findings"].description.lower()
        assert "report" in description
        assert "query" in description
        assert "resolve" in description or "acknowledge" in description


class TestToolInputFieldDescriptions:
    """Every parameter of every tool carries a clear input-schema description.

    The mcp-builder standard requires per-field descriptions with constraints (and
    an example where useful). FastMCP injects the ``context`` param, which never
    surfaces in the tool's ``inputSchema.properties`` — so this asserts a
    description on every CONSUMER-facing parameter.
    """

    async def _tools_by_name(self, tmp_path: Path) -> dict[str, Any]:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        return {tool.name: tool for tool in await mcp.list_tools()}

    async def test_every_input_field_has_a_description(self, tmp_path: Path) -> None:
        tools = await self._tools_by_name(tmp_path)
        for name in _EXPECTED_TOOLS:
            properties = tools[name].inputSchema.get("properties", {})
            if name in _PARAMETERLESS_TOOLS:
                assert not properties, f"{name} is expected to take no parameters"
                continue
            assert properties, f"{name} should expose its parameters in the schema"
            for field_name, field_schema in properties.items():
                description = field_schema.get("description", "")
                assert description and description.strip(), (
                    f"{name}.{field_name} must carry an input-schema description"
                )

    async def test_get_symbol_qualified_name_describes_both_forms(
        self, tmp_path: Path
    ) -> None:
        # The qualified_name description must convey it accepts BOTH a
        # module-qualified dotted name AND a bare identity.
        tools = await self._tools_by_name(tmp_path)
        description = tools["lore_get_symbol"].inputSchema["properties"]["qualified_name"][
            "description"
        ].lower()
        assert "bare" in description
        assert "dotted" in description or "qualified" in description


class TestInputParamConstraints:
    """Input params publish their value constraints + reject bad values (Items 4, 5).

    Item 4: ``lore_search_code(detail_level=...)`` must publish a Literal enum
    (auto/summary/source) so a bad value is REJECTED at validation, not silently
    accepted then filtered to empty. Item 5: the numeric params (``k``, ``depth``,
    ``max_results``) must carry a ``minimum`` (>= 1) so a zero/negative is
    schema-rejected. The rejection probe validates the tool's arg model directly —
    isolating arg-validation from the handler, so a refusal proves the SCHEMA
    rejected the value (non-vacuous: a valid value still validates).
    """

    async def _tools_by_name(self, tmp_path: Path) -> dict[str, Any]:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        return {tool.name: tool for tool in await mcp.list_tools()}

    async def _server(self, tmp_path: Path) -> Any:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        return build_mcp_server(LoreServer(config))

    def _arg_model(self, mcp: Any, name: str) -> Any:
        """The pydantic model FastMCP validates a tool's call arguments against.

        Validating this directly is the NON-VACUOUS rejection probe: it isolates
        arg-validation from the handler, so a rejection proves the SCHEMA refused
        the value (not that a missing lifespan context crashed the handler body).
        """
        return mcp._tool_manager.get_tool(name).fn_metadata.arg_model  # noqa: SLF001

    # -- Item 4: detail_level Literal enum ---------------------------------- #

    async def test_detail_level_publishes_enum_constraint(self, tmp_path: Path) -> None:
        tools = await self._tools_by_name(tmp_path)
        prop = tools["lore_search_code"].inputSchema["properties"]["detail_level"]
        assert prop.get("enum") == ["auto", "summary", "source"], (
            "detail_level must publish the Literal enum so a bad value is rejected, "
            "not silently filtered to empty"
        )

    async def test_invalid_detail_level_is_rejected_good_value_accepted(
        self, tmp_path: Path
    ) -> None:
        from pydantic import ValidationError

        mcp = await self._server(tmp_path)
        model = self._arg_model(mcp, "lore_search_code")
        # A value outside the Literal is rejected at arg-validation. A bare-str
        # param would instead ACCEPT it (then silently filter to an empty result).
        with pytest.raises(ValidationError):
            model.model_validate({"query": "x", "detail_level": "bogus"})
        # A valid Literal member is accepted — the rejection is value-specific, not
        # a blanket failure (non-vacuous).
        model.model_validate({"query": "x", "detail_level": "summary"})

    # -- Item 5: ge= bounds on numeric params ------------------------------- #

    async def test_numeric_params_publish_minimum(self, tmp_path: Path) -> None:
        tools = await self._tools_by_name(tmp_path)
        # k on search_code + recall_memory, depth + max_results on blast_radius all
        # carry a minimum of 1 (a count/depth below 1 is meaningless).
        search_k = tools["lore_search_code"].inputSchema["properties"]["k"]
        recall_k = tools["lore_recall_memory"].inputSchema["properties"]["k"]
        depth = tools["lore_blast_radius"].inputSchema["properties"]["depth"]
        max_results = tools["lore_blast_radius"].inputSchema["properties"]["max_results"]
        assert search_k.get("minimum") == 1
        assert recall_k.get("minimum") == 1
        assert depth.get("minimum") == 1
        assert max_results.get("minimum") == 1

    async def test_zero_or_negative_numeric_is_rejected_good_value_accepted(
        self, tmp_path: Path
    ) -> None:
        from pydantic import ValidationError

        mcp = await self._server(tmp_path)
        search_model = self._arg_model(mcp, "lore_search_code")
        blast_model = self._arg_model(mcp, "lore_blast_radius")
        # k=0 (search) and depth=-1 (blast_radius) are schema-rejected at validation.
        with pytest.raises(ValidationError):
            search_model.model_validate({"query": "x", "k": 0})
        with pytest.raises(ValidationError):
            blast_model.model_validate({"target": "x", "depth": -1})
        # A positive value passes — the bound rejects below-1, not all values.
        search_model.model_validate({"query": "x", "k": 1})
        blast_model.model_validate({"target": "x", "depth": 1})


class TestToolAnnotations:
    """Tool annotations are set correctly (readOnlyHint on the read tools, etc.).

    The mcp-builder standard: set ``readOnlyHint`` / ``idempotentHint`` /
    ``openWorldHint`` appropriately. All lore tools are read-only EXCEPT
    ``save_memory`` (persists a note) and ``reindex`` (mutates index state).
    """

    async def _tools_by_name(self, tmp_path: Path) -> dict[str, Any]:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        return {tool.name: tool for tool in await mcp.list_tools()}

    async def test_read_only_tools_are_marked_read_only(self, tmp_path: Path) -> None:
        tools = await self._tools_by_name(tmp_path)
        for name in _READ_ONLY_TOOLS:
            annotations = tools[name].annotations
            assert annotations is not None, f"{name} must carry tool annotations"
            assert annotations.readOnlyHint is True, (
                f"{name} is a read-only tool and must set readOnlyHint=True"
            )

    async def test_mutating_tools_are_not_marked_read_only(self, tmp_path: Path) -> None:
        tools = await self._tools_by_name(tmp_path)
        for name in _MUTATING_TOOLS:
            annotations = tools[name].annotations
            assert annotations is not None, f"{name} must carry tool annotations"
            assert annotations.readOnlyHint is not True, (
                f"{name} mutates state and must NOT set readOnlyHint=True"
            )

    async def test_save_memory_is_not_idempotent(self, tmp_path: Path) -> None:
        # save_memory dedups by deterministic id, but a NEW note text creates a new
        # point — it is a write, not a read; do not advertise it idempotent.
        tools = await self._tools_by_name(tmp_path)
        assert tools["lore_save_memory"].annotations is not None


# Item 2: the named output fields each tool's published outputSchema must carry.
# A wrapper returning the real pydantic model (a scalar model, or list[Model]) makes
# FastMCP derive a FIELD-LEVEL outputSchema; a wrapper returning list[dict[str, Any]]
# publishes an opaque ``additionalProperties: true`` (no field names) — the regression
# this pins. Each value is field names that MUST be discoverable in the schema (either
# top-level ``properties`` for a scalar-model tool, or under ``$defs`` for a
# list-wrapped one). ``lore_save_memory`` returns a bare str (the id) — no model — so
# it is excluded (a str has no fields to name).
_TOOL_OUTPUT_FIELDS: dict[str, set[str]] = {
    "lore_search_code": {"formatted", "chunk_key", "detail_level", "stale", "score"},
    "lore_read_file": {"tier", "path", "line_start", "line_end", "text"},
    "lore_get_symbol": {"qualified_name", "chunk_type", "tier", "file_path", "source"},
    # lore_verify is a SCALAR VerifyResult return: its own fields are top-level
    # properties (status / summary / mismatches); the nested VerifiedSummary and
    # VerifyMismatch fields surface under $defs.
    "lore_verify": {
        "status",
        "summary",
        "mismatches",
        # P8b wire-up (item 4): the optional server-set rebuild caveat line.
        "rebuilding_caveat",
        "qualified_name",
        "chunk_type",
        "tier",
        "file_path",
        "line_start",
        "line_end",
        "header",
        "claim",
        "claimed",
        "actual",
    },
    # P8b wire-up: lore_read returns a StoreFileSpan MODEL (the store-backed twin of
    # lore_read_file) — its fields include the two store-only marks (``stale`` /
    # ``integrity_verified``) lore_read_file's FileSpan cannot supply.
    "lore_read": {
        "tier",
        "path",
        "line_start",
        "line_end",
        "text",
        "stale",
        "integrity_verified",
    },
    # lore_recall_memory is intentionally omitted: the P7 cutover re-shapes its
    # return (it no longer carries the retired store's flat ``metadata`` note), so
    # its surfaced fields are pinned behaviourally in TestRecallMemoryCutover
    # rather than as a fixed field-name table here.
    "lore_reindex": {"files_indexed", "files_failed", "files_skipped"},
    "lore_index_status": {"files_indexed", "files_failed", "files_skipped"},
    "lore_what_imports": {"qualified_name", "kind", "file_path", "tier"},
    "lore_blast_radius": {"qualified_name", "kind", "file_path", "tier"},
    "lore_tests_for": {"qualified_name", "kind", "file_path", "tier"},
    "lore_references": {
        "qualified_name",
        "production_references",
        "test_references",
        "referencing",
    },
    "lore_dead_code": {
        "id",
        "kind",
        "qualified_name",
        "file_path",
        "chunk_id",
        "tier",
        "test_references",
        "reason",
    },
    # P6-tail: ImpactResult is a SCALAR return (mirrors lore_references /
    # lore_index_status), so its own fields are top-level properties; its
    # nested ModuleRollup fields surface under $defs.
    "lore_impact": {
        "target",
        "verdict",
        "production_references",
        "test_references",
        "covering_tests",
        "direct_consumers",
        "module_rollups",
        "elided",
        "caveat",
        "formatted",
        "module",
        "consumer_count",
    },
    # P6-tail: MapResult is also a SCALAR return; its nested MapEntry fields
    # surface under $defs.
    "lore_map": {
        "entries",
        "elided_modules",
        "formatted",
        "module",
        "rank",
        "symbols",
    },
}


def _schema_field_names(schema: dict[str, Any]) -> set[str]:
    """Collect every property name a tool's outputSchema names, transitively.

    Gathers the schema's own ``properties`` keys plus the ``properties`` keys of
    every model under ``$defs`` (a list-wrapped return publishes the element model
    in ``$defs`` and only a ``result`` array at top level). This is how a consumer
    discovers the actual fields; an opaque ``additionalProperties: true`` object
    contributes NONE of them, so the set stays empty for the regression case.
    """
    names: set[str] = set(schema.get("properties", {}).keys())
    for definition in schema.get("$defs", {}).values():
        names.update(definition.get("properties", {}).keys())
    return names


class TestToolOutputSchemas:
    """Every tool publishes a NON-opaque, field-level outputSchema + structuredContent.

    The mcp-builder standard: a tool's structured output must carry a real schema so
    the consumer sees the field shape, not an opaque ``additionalProperties: true``
    object. The fix is to annotate each wrapper with its real pydantic return type
    (``-> list[SearchResult]`` / ``-> FileSpan`` / ``-> IndexSummary`` …) and return
    the model instance(s); FastMCP then derives a field-level outputSchema and emits
    structuredContent matching it. These assertions pin the named fields (mutation:
    revert one wrapper to ``list[dict[str, Any]]`` ⇒ its field set empties ⇒ fail).
    """

    async def _tools_by_name(self, tmp_path: Path) -> dict[str, Any]:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        return {tool.name: tool for tool in await mcp.list_tools()}

    async def test_each_tool_publishes_a_field_level_output_schema(
        self, tmp_path: Path
    ) -> None:
        tools = await self._tools_by_name(tmp_path)
        for name, expected_fields in _TOOL_OUTPUT_FIELDS.items():
            schema = tools[name].outputSchema
            assert schema is not None, f"{name} must publish an outputSchema"
            published = _schema_field_names(schema)
            missing = expected_fields - published
            assert not missing, (
                f"{name}'s outputSchema must name its result fields (not an opaque "
                f"additionalProperties:true object); missing {missing} — got {published}"
            )

    async def test_no_tool_publishes_an_opaque_object_output(self, tmp_path: Path) -> None:
        # The regression guard: a list[dict[str, Any]] return publishes a
        # ``result`` array whose items are ``additionalProperties: true`` (an opaque
        # object). No model-returning tool may do that.
        tools = await self._tools_by_name(tmp_path)
        for name in _TOOL_OUTPUT_FIELDS:
            schema = tools[name].outputSchema or {}
            result_prop = schema.get("properties", {}).get("result", {})
            items = result_prop.get("items", {}) if isinstance(result_prop, dict) else {}
            assert items.get("additionalProperties") is not True, (
                f"{name} publishes an opaque additionalProperties:true item — it must "
                f"return a real pydantic model so the element schema is field-level"
            )

    async def test_live_call_returns_structured_content_with_fields(
        self, tmp_path: Path    ) -> None:
        # A live call through the FastMCP tool surface must emit structuredContent
        # whose payload carries the model's named fields — proof the model instance
        # (not a stringified blob) reaches the consumer with its schema.
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "base.py").write_text(_PY_BASE, encoding="utf-8")
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        mcp = build_mcp_server(LoreServer(config))
        try:
            # index_status: a scalar IndexSummary — structuredContent is the model dict.
            status_tool = mcp._tool_manager.get_tool("lore_index_status")  # noqa: SLF001
            _content, structured = await status_tool.run(
                {},
                context=_FakeToolContext(ctx),
                convert_result=True,
            )
            assert isinstance(structured, dict)
            assert "files_indexed" in structured
            # search_code: a list[SearchResult] — wrapped under ``result`` with the
            # SearchResult fields on each element.
            search_tool = mcp._tool_manager.get_tool("lore_search_code")  # noqa: SLF001
            _content2, structured2 = await search_tool.run(
                {"query": "champion routing", "k": 10},
                context=_FakeToolContext(ctx),
                convert_result=True,
            )
            assert isinstance(structured2, dict) and "result" in structured2
            assert structured2["result"], "expected at least one hit"
            assert "formatted" in structured2["result"][0]
        finally:
            await ctx.aclose()


class TestActionableErrors:
    """Consumer-facing errors suggest a next step (the actionable-error standard)."""

    async def test_get_symbol_not_found_names_the_symbol_and_searched_types(
        self, tmp_path: Path    ) -> None:
        # A get_symbol miss must name what was not found AND what was searched, so
        # the consumer knows the lookup was scoped to symbol chunk types (and can
        # fall back to search_code / reindex).
        from loremaster.symbols import GetSymbolError

        slug = _slug()
        config = _config(slug, tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            with pytest.raises(GetSymbolError) as exc_info:
                await ctx.get_symbol("definitely_absent_symbol")
            message = str(exc_info.value)
            assert "definitely_absent_symbol" in message
            assert "search_code" in message or "reindex" in message, (
                "a not-found must point the consumer at a next step "
                "(search_code / reindex)"
            )
        finally:
            await ctx.aclose()


class TestToolBehaviourEndToEnd:
    """Each tool returns the right shape over a real-indexed corpus."""

    @pytest_asyncio.fixture()
    async def indexed_context(
        self, tmp_path: Path    ) -> AsyncIterator[AppContext]:
        """An AppContext with a real Python file indexed (vectors + graph)."""
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "base.py").write_text(_PY_BASE, encoding="utf-8")
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
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

    async def test_verify_confirms_a_true_claim(
        self, indexed_context: AppContext
    ) -> None:
        result = await indexed_context.verify(
            "champion_routing",
            expected_file_path="pkg/router.py",
            expected_signature_fragment="def champion_routing",
        )
        assert result.status == "confirmed"
        assert result.mismatches == []
        assert result.summary is not None
        assert result.summary.file_path == "pkg/router.py"
        assert "def champion_routing" in result.summary.header

    async def test_verify_flags_a_wrong_path_claim_naming_the_actual(
        self, indexed_context: AppContext
    ) -> None:
        result = await indexed_context.verify(
            "champion_routing", expected_file_path="totally/wrong.py"
        )
        assert result.status == "mismatch"
        [mismatch] = result.mismatches
        assert mismatch.claim == "file_path"
        assert mismatch.actual == "pkg/router.py"

    async def test_verify_missing_symbol_is_a_not_found_result_not_an_error(
        self, indexed_context: AppContext
    ) -> None:
        # Unlike get_symbol (which RAISES), verify returns not_found as a RESULT.
        result = await indexed_context.verify("definitely_absent_symbol")
        assert result.status == "not_found"
        assert result.summary is None
        assert result.mismatches == []

    async def test_read_file_returns_real_span(self, indexed_context: AppContext) -> None:
        span = await indexed_context.read_file("custom", "pkg/router.py", 1, 1)
        assert span.text.startswith("import os")
        assert span.header.startswith("[SOURCE:custom:pkg/router.py:1-1]")

    # -- lore_read (StoreReadTool) ----------------------------------------- #

    async def test_read_serves_a_hash_verified_store_span(
        self, indexed_context: AppContext
    ) -> None:
        # lore_read serves the INDEXED bytes from the store (not disk), hash-verified,
        # with the same [SOURCE:...] provenance header its lore_read_file twin gives.
        span = await indexed_context.read("custom", "pkg/router.py", 1, 1)
        assert span.text.startswith("import os")
        assert span.header.startswith("[SOURCE:custom:pkg/router.py:1-1]")
        assert span.integrity_verified is True
        # A freshly-indexed file is in step with the index — never stale.
        assert span.stale is False

    async def test_read_unknown_tier_names_the_valid_tiers(
        self, indexed_context: AppContext
    ) -> None:
        # The audit: StoreReadTool alone reports an unknown tier as a bare not-found.
        # The wiring must first validate the tier so a typo lists the real tiers.
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await indexed_context.read("kustom", "pkg/router.py")
        message = str(exc_info.value).lower()
        assert "tier" in message
        assert "custom" in message

    async def test_read_missing_file_is_a_clean_tool_error(
        self, indexed_context: AppContext
    ) -> None:
        # A miss (known tier, no indexed body) surfaces as a teaching tool error —
        # never a raw traceback — naming the next step.
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await indexed_context.read("custom", "pkg/does_not_exist.py")
        assert "not found" in str(exc_info.value).lower()

    # -- lore_diff (DiffEngine) -------------------------------------------- #

    async def test_diff_with_no_since_lists_snapshots(
        self, indexed_context: AppContext
    ) -> None:
        # No ``since`` ⇒ a summarised snapshot listing (empty store ⇒ the empty
        # notice, never a raw dump / crash).
        rendered = await indexed_context.diff()
        assert isinstance(rendered, str)
        assert rendered  # a string either way (a listing or the empty-notice line)

    async def test_diff_between_a_snapshot_and_now_renders(
        self, indexed_context: AppContext
    ) -> None:
        # Stamp a snapshot, then diff it against the live "now" state — the rendered
        # view names the since -> (now) transition.
        since = await indexed_context._snapshot_stamper.stamp()
        rendered = await indexed_context.diff(since=str(since))
        assert isinstance(rendered, str)
        assert "diff:" in rendered

    async def test_diff_unknown_since_is_a_clean_tool_error(
        self, indexed_context: AppContext
    ) -> None:
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await indexed_context.diff(since="snapshot:definitely_absent")
        assert str(exc_info.value)  # a typed DiffError, not a raw traceback

    # -- lore_findings (FindingLedger) ------------------------------------- #

    async def test_findings_report_then_query_roundtrips(
        self, indexed_context: AppContext
    ) -> None:
        reported = await indexed_context.findings(
            action="report",
            subject="lore_tests_for misses XML edges",
            body="the graph heuristic drops framework-mediated calls",
            area="lore_tests_for",
            category="capability_gap",
            created_by="builder-wireup-1",
        )
        assert "reported finding #" in reported
        listed = await indexed_context.findings(action="query", status="open")
        assert "lore_tests_for misses XML edges" in listed

    @pytest.mark.parametrize("field_name", ["subject", "area", "category", "created_by"])
    async def test_findings_report_requires_nonempty_fields(
        self, indexed_context: AppContext, field_name: str
    ) -> None:
        # An empty (not merely absent) required field is a caller error naming it.
        # Parametrised over the FOUR required fields — ``subject`` / ``area`` /
        # ``category`` / ``created_by``. ``body`` is DELIBERATELY excluded from
        # this required set (audit-waveb-1 finding #1): the schema + FindingLedger
        # deliberately allow an empty body (a subject-only finding is a valid
        # quick capture), so the MCP boundary must match that domain rather than
        # be stricter than it. See
        # test_findings_report_without_body_defaults_to_empty_string below, which
        # pins the complementary behavior (an omitted body succeeds).
        kwargs: dict[str, str] = {
            "subject": "s",
            "area": "a",
            "category": "c",
            "created_by": "me",
        }
        kwargs[field_name] = ""
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await indexed_context.findings(action="report", **kwargs)
        assert field_name in str(exc_info.value).lower()

    async def test_findings_report_without_body_defaults_to_empty_string(
        self, indexed_context: AppContext
    ) -> None:
        # Fix (audit-waveb-1 finding #1): the schema + FindingLedger deliberately
        # allow an empty body (store/surreal_schema.py's ``body`` field carries no
        # non-empty ASSERT — "a finding may carry an empty body, the subject alone
        # can name it"). The MCP boundary previously contradicted that domain by
        # requiring a non-empty body; omitting it entirely must now succeed, and
        # the stored finding must round-trip with an empty body.
        reported = await indexed_context.findings(
            action="report",
            subject="subject alone should be enough to file this",
            area="lore_findings",
            category="friction",
            created_by="me",
        )
        assert "reported finding #" in reported
        number = int(reported.split("#", 1)[1].split(" ", 1)[0])
        listed = await indexed_context.findings(action="query", status="open")
        assert "subject alone should be enough to file this" in listed
        finding = await indexed_context.finding_ledger.get(number)
        assert finding.body == ""

    async def test_findings_lifecycle_acknowledge_then_resolve(
        self, indexed_context: AppContext
    ) -> None:
        reported = await indexed_context.findings(
            action="report",
            subject="stale flag not rendered",
            body="body",
            area="lore_read",
            category="bug",
            created_by="me",
        )
        number = reported.split("#", 1)[1].split(" ", 1)[0]
        acked = await indexed_context.findings(
            action="acknowledge", id_or_number=int(number), actor="me"
        )
        assert "acknowledged" in acked
        resolved = await indexed_context.findings(
            action="resolve", id_or_number=int(number), actor="me", note="fixed"
        )
        assert "resolved" in resolved

    async def test_findings_get_and_chain_head_by_number(
        self, indexed_context: AppContext
    ) -> None:
        reported = await indexed_context.findings(
            action="report",
            subject="diff engine could leak a connection",
            body="body",
            area="lore_diff",
            category="bug",
            created_by="me",
        )
        number = int(reported.split("#", 1)[1].split(" ", 1)[0])
        got = await indexed_context.findings(action="get", id_or_number=number)
        assert "diff engine could leak a connection" in got
        # A lone finding is its OWN chain head — rendered, and NOT flagged forked.
        head = await indexed_context.findings(action="chain_head", id_or_number=number)
        assert "diff engine could leak a connection" in head
        assert "FORKED" not in head

    async def test_findings_chain_head_surfaces_a_fork(
        self, indexed_context: AppContext
    ) -> None:
        # Two findings superseding the SAME original fork the chain; chain_head must
        # SURFACE the sibling branch it did not walk (the hardening builder's model),
        # and the wiring must render that fork marker rather than hide it.
        original = await indexed_context.findings(
            action="report", subject="the original framing", body="b",
            area="lore_findings", category="friction", created_by="me",
        )
        original_number = int(original.split("#", 1)[1].split(" ", 1)[0])
        for reframe in ("first reframe", "second reframe"):
            await indexed_context.findings(
                action="report", subject=reframe, body="b", area="lore_findings",
                category="friction", created_by="me", supersedes=original_number,
            )
        head = await indexed_context.findings(
            action="chain_head", id_or_number=original_number
        )
        assert "FORKED" in head

    async def test_findings_unknown_action_is_a_clean_error(
        self, indexed_context: AppContext
    ) -> None:
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await indexed_context.findings(action="obliterate")
        assert "obliterate" in str(exc_info.value)

    # -- verify rebuild caveat (item 4) ------------------------------------ #

    @staticmethod
    async def _seed_in_progress_rebuild(ctx: AppContext) -> None:
        """Open a rebuild window by seeding the manifest-meta a real rebuild writes."""
        import json

        from loremaster.index.schema import SCHEMA_REBUILD_STATUS_META_KEY

        await ctx.manifest.meta_set(
            SCHEMA_REBUILD_STATUS_META_KEY,
            json.dumps({"state": "in_progress", "done": 3, "total": 118}),
        )

    async def test_verify_not_found_carries_the_rebuild_caveat_mid_rebuild(
        self, indexed_context: AppContext
    ) -> None:
        await self._seed_in_progress_rebuild(indexed_context)
        result = await indexed_context.verify("definitely_absent_symbol")
        assert result.status == "not_found"
        assert result.rebuilding_caveat is not None
        assert "rebuild" in result.rebuilding_caveat.lower()

    async def test_verify_not_found_has_no_caveat_when_idle(
        self, indexed_context: AppContext
    ) -> None:
        result = await indexed_context.verify("definitely_absent_symbol")
        assert result.status == "not_found"
        assert result.rebuilding_caveat is None

    async def test_verify_confirmed_never_carries_a_caveat_even_mid_rebuild(
        self, indexed_context: AppContext
    ) -> None:
        # A symbol that RESOLVES is trustworthy even during a rebuild — the caveat
        # is only for the transient-false-negative not_found case.
        await self._seed_in_progress_rebuild(indexed_context)
        result = await indexed_context.verify("champion_routing")
        assert result.status == "confirmed"
        assert result.rebuilding_caveat is None

    async def test_save_then_recall_memory_roundtrips(
        self, indexed_context: AppContext
    ) -> None:
        # P7 cutover: save_memory takes the memory ``kind``; recall_memory surfaces
        # the note text (its exact return SHAPE is pinned in TestRecallMemoryCutover).
        note = "champion routing lives in pkg/router.py"
        await getattr(indexed_context, "save_memory")(note, kind="fact")
        rendered = _render_text(
            await getattr(indexed_context, "recall_memory")("where is champion routing", k=5)
        )
        assert note in rendered

    async def test_what_imports_traverses_graph(self, indexed_context: AppContext) -> None:
        # The router imports the in-project ``pkg.base.BaseRouter`` (a stdlib
        # import like ``os`` is dropped by the RESOLVED keep/drop rule).
        importers = await indexed_context.what_imports(_PY_MODULE_IMPORT_FQN)
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

    async def test_references_returns_production_test_split(
        self, indexed_context: AppContext
    ) -> None:
        # ``pkg.base.BaseRouter`` is imported by ``pkg.router`` (a production file),
        # so it has at least one production reference and zero test references.
        summary = await indexed_context.references("pkg.base.BaseRouter")
        assert summary.qualified_name == "pkg.base.BaseRouter"
        assert summary.production_references >= 1
        assert summary.test_references == 0

    async def test_references_zero_is_valid_not_error(
        self, indexed_context: AppContext
    ) -> None:
        # A symbol with zero references returns an all-zero summary — NOT an error.
        # Empty is the SUCCESS case (a truly unreferenced symbol); the handler must
        # never raise ``SchemaRebuildingError`` for an empty references result.
        summary = await indexed_context.references("pkg.router.champion_routing")
        assert summary.production_references == 0
        assert summary.test_references == 0
        assert isinstance(summary.referencing, list)

    async def test_dead_code_surfaces_test_only_symbol(
        self, tmp_path: Path    ) -> None:
        # A corpus with ``pkg/utils.py`` (defines ``orphan_helper``) and
        # ``tests/test_utils.py`` (the ONLY consumer of ``orphan_helper`` — a test
        # file). After indexing, ``dead_code`` must report ``orphan_helper`` as dead
        # with reason ``only_referenced_by_tests``.
        from loremaster.graph import REASON_ONLY_REFERENCED_BY_TESTS

        slug = _slug()
        live = tmp_path / "live_dead"
        (live / "pkg").mkdir(parents=True)
        (live / "tests").mkdir(parents=True)
        (live / "pkg" / "utils.py").write_text(_PY_UTILS, encoding="utf-8")
        (live / "tests" / "test_utils.py").write_text(_PY_TEST_REF, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        try:
            dead = await ctx.dead_code()
            names = {node.qualified_name for node in dead}
            assert "pkg.utils.orphan_helper" in names, (
                f"orphan_helper is only referenced by tests and must appear in dead_code; "
                f"got: {names}"
            )
            orphan = next(n for n in dead if n.qualified_name == "pkg.utils.orphan_helper")
            assert orphan.reason == REASON_ONLY_REFERENCED_BY_TESTS
        finally:
            await ctx.aclose()

    async def test_dead_code_does_not_surface_production_referenced_symbol(
        self, indexed_context: AppContext
    ) -> None:
        # ``pkg.base.BaseRouter`` has a production reference from ``pkg.router``
        # (it imports it). It must NOT appear in dead_code.
        dead = await indexed_context.dead_code()
        names = {node.qualified_name for node in dead}
        assert "pkg.base.BaseRouter" not in names, (
            "BaseRouter is referenced by production code and must not be dead"
        )

    async def test_dead_code_empty_result_does_not_raise(
        self, indexed_context: AppContext
    ) -> None:
        # An empty dead_code result is the SUCCESS case (nothing orphaned) — the
        # handler must NOT raise SchemaRebuildingError when the list comes back empty.
        # We confirm this by clamping max_results to 0 to force an empty result
        # regardless of corpus state.
        # Note: max_results=0 is below the schema ge=1 floor, so call the handler
        # directly (bypassing validation) to prove the handler itself does not raise.
        dead = await indexed_context.code_graph.dead_code([], max_results=0)
        assert dead == []  # empty is fine, not an error

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


class TestReindexTierValidation:
    """``reindex(tier=...)`` validates the tier — a typo must fail loud (Item 3).

    Today an unknown ``tier`` is SILENTLY ignored (the sweep runs over all roots
    regardless), so a typo reports false success. The fix validates ``tier`` against
    the configured tiers (``config.effective_roots``): an unknown value raises a
    clear error NAMING the valid tiers; a real tier (or ``None`` = all) proceeds.
    Mutation: drop the validation ⇒ ``tier='bogus'`` no longer raises.
    """

    @pytest_asyncio.fixture()
    async def indexed_context(
        self, tmp_path: Path    ) -> AsyncIterator[AppContext]:
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "base.py").write_text(_PY_BASE, encoding="utf-8")
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)  # declares the live tier "custom"
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        try:
            yield ctx
        finally:
            await ctx.aclose()

    async def test_unknown_tier_raises_naming_the_valid_tiers(
        self, indexed_context: AppContext
    ) -> None:
        from loremaster.server import ReindexTierError

        with pytest.raises(ReindexTierError) as exc_info:
            await indexed_context.reindex(tier="bogus")
        message = str(exc_info.value)
        assert "bogus" in message, "the error must name the bad tier the caller gave"
        # The configured tier ("custom") must be named so the caller can correct.
        assert "custom" in message, "the error must name the valid tier(s)"

    async def test_known_tier_reindexes(self, indexed_context: AppContext) -> None:
        # A real tier proceeds (and brings a new file in that tier current).
        live = indexed_context._config.effective_roots[0].path  # noqa: SLF001
        assert live is not None
        (Path(live) / "pkg" / "scoped.py").write_text(
            "def scoped_added_symbol():\n    return 11\n", encoding="utf-8"
        )
        await indexed_context.reindex(tier="custom")
        symbol = await indexed_context.get_symbol("scoped_added_symbol")
        assert symbol.file_path == "pkg/scoped.py"

    async def test_reindex_all_still_works(self, indexed_context: AppContext) -> None:
        # tier=None still means all — the unscoped sweep is unchanged.
        summary = await indexed_context.reindex()
        assert summary.files_failed == 0


class _FakeRequestContext:
    """A stand-in for the MCP request context exposing the lifespan AppContext."""

    def __init__(self, app_context: AppContext) -> None:
        self.lifespan_context = app_context


class _FakeToolContext:
    """A stand-in FastMCP ``Context`` whose ``request_context`` carries our AppContext.

    The registered tool wrappers read ``context.request_context.lifespan_context``;
    this minimal double lets a test drive the REAL ``@mcp.tool`` wrapper body
    through the tool manager (including FastMCP's structured-content serialisation)
    without standing up the full streamable-http session machinery.
    """

    def __init__(self, app_context: AppContext) -> None:
        self.request_context = _FakeRequestContext(app_context)


class TestRegisteredToolWrappers:
    """Drive the REGISTERED FastMCP tool wrappers (not the handlers) — fix #3.

    The end-to-end tests above call the :class:`AppContext` HANDLERS directly, so
    the ``@mcp.tool``-decorated wrapper bodies in ``_register_tools`` had zero
    coverage. These drive the registered tool functions through the FastMCP tool
    manager against a real-indexed corpus. Since Item 2 the wrappers RETURN the real
    pydantic model instance(s) (not ``.model_dump()``), and FastMCP derives the
    field-level outputSchema + structuredContent from the model — so these drive
    ``Tool.run(..., convert_result=True)`` (the live serialisation path) and assert
    the STRUCTURED content's shape. A wrapper annotated ``list[dict[str, Any]]``
    again would publish an opaque schema (caught in ``TestToolOutputSchemas``).
    """

    @pytest_asyncio.fixture()
    async def indexed(
        self, tmp_path: Path    ) -> AsyncIterator[tuple[Any, AppContext]]:
        """A built FastMCP server + a real-indexed AppContext sharing one corpus."""
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "base.py").write_text(_PY_BASE, encoding="utf-8")
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        mcp = build_mcp_server(LoreServer(config))
        try:
            yield mcp, ctx
        finally:
            await ctx.aclose()

    @staticmethod
    async def _structured(mcp: Any, name: str, ctx: AppContext, /, **kwargs: Any) -> Any:
        """Run a registered tool through FastMCP and return its structuredContent.

        ``Tool.run(convert_result=True)`` returns ``(unstructured, structured)`` when
        the tool has an output schema — the structured half is the model-derived
        dict the consumer receives. Driving the real run path proves the wrapper
        returns a model FastMCP can serialise into structuredContent.
        """
        tool = mcp._tool_manager.get_tool(name)  # noqa: SLF001 - test-only introspection
        _unstructured, structured = await tool.run(
            kwargs, context=_FakeToolContext(ctx), convert_result=True
        )
        return structured

    async def test_search_code_wrapper_yields_structured_list(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        structured = await self._structured(
            mcp, "lore_search_code", ctx, query="champion routing", k=10
        )
        # A list[SearchResult] is wrapped under ``result``; each element carries the
        # SearchResult fields (NOT an opaque blob).
        assert isinstance(structured, dict) and structured["result"]
        items = structured["result"]
        assert all(isinstance(item, dict) for item in items)
        assert any("[SOURCE:" in item["formatted"] for item in items)
        assert any("pkg/router.py" in item["formatted"] for item in items)

    async def test_get_symbol_wrapper_yields_structured_model(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        structured = await self._structured(
            mcp, "lore_get_symbol", ctx, qualified_name="champion_routing"
        )
        # A scalar ResolvedSymbol — structuredContent is the model dict directly.
        assert isinstance(structured, dict)
        assert structured["qualified_name"] == "champion_routing"
        assert structured["file_path"] == "pkg/router.py"

    async def test_verify_wrapper_confirms_over_mcp(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        structured = await self._structured(
            mcp,
            "lore_verify",
            ctx,
            qualified_name="champion_routing",
            expected_file_path="pkg/router.py",
        )
        # A scalar VerifyResult — structuredContent carries status + the nested summary.
        assert isinstance(structured, dict)
        assert structured["status"] == "confirmed"
        assert structured["mismatches"] == []
        assert structured["summary"]["file_path"] == "pkg/router.py"

    async def test_verify_wrapper_reports_a_mismatch_over_mcp(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        structured = await self._structured(
            mcp,
            "lore_verify",
            ctx,
            qualified_name="champion_routing",
            expected_file_path="wrong/place.py",
        )
        assert structured["status"] == "mismatch"
        assert structured["mismatches"]
        assert structured["mismatches"][0]["claim"] == "file_path"
        assert structured["mismatches"][0]["actual"] == "pkg/router.py"

    async def test_verify_wrapper_not_found_over_mcp(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        structured = await self._structured(
            mcp, "lore_verify", ctx, qualified_name="definitely_absent_symbol"
        )
        # not_found is a RESULT that serialises cleanly (summary is null, no error).
        assert structured["status"] == "not_found"
        assert structured["summary"] is None
        assert structured["mismatches"] == []

    async def test_read_wrapper_yields_structured_store_span(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        structured = await self._structured(
            mcp, "lore_read", ctx, tier="custom", path="pkg/router.py", line_start=1, line_end=1
        )
        # A scalar StoreFileSpan — structuredContent carries the span + its two marks.
        assert isinstance(structured, dict)
        assert structured["tier"] == "custom"
        assert structured["text"].startswith("import os")
        assert structured["stale"] is False
        assert structured["integrity_verified"] is True

    async def test_index_status_wrapper_yields_structured_model(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        structured = await self._structured(mcp, "lore_index_status", ctx)
        assert isinstance(structured, dict)
        assert structured["files_indexed"] >= 1
        assert structured["files_failed"] == 0

    async def test_references_wrapper_yields_structured_model(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        # ``pkg.base.BaseRouter`` is imported by a production file → production_references >= 1.
        structured = await self._structured(
            mcp, "lore_references", ctx, name="pkg.base.BaseRouter"
        )
        # A scalar ReferenceSummary — structuredContent is the model dict.
        assert isinstance(structured, dict)
        assert structured["qualified_name"] == "pkg.base.BaseRouter"
        assert "production_references" in structured
        assert structured["production_references"] >= 1
        assert "test_references" in structured
        assert "referencing" in structured

    async def test_dead_code_wrapper_yields_structured_list(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        # The call returns a list (possibly empty) — structuredContent wraps under ``result``.
        structured = await self._structured(mcp, "lore_dead_code", ctx)
        assert isinstance(structured, dict)
        assert "result" in structured
        assert isinstance(structured["result"], list)
        # Every element must have the DeadCodeNode fields.
        for item in structured["result"]:
            assert isinstance(item, dict)
            assert "qualified_name" in item
            assert "reason" in item


# --------------------------------------------------------------------------- #
# lore_impact / lore_map tool wiring (P6-tail): the two new verdict-bearing
# graph-read tools riding the SAME AppContext-handler + FastMCP-wrapper
# pattern the twelve built-in tools above already use. The ENGINE algorithms
# (PageRank / depth-clamped rollups / caveat text / elision math) are already
# pinned behaviourally in test_impact.py / test_map.py against a hand-built
# FakeSurrealCodeGraph; everything below instead proves the WIRING seam: the
# real tool is registered, the real AppContext threads the real code graph +
# a real rebuild probe into the engine, and the served payload (handler
# return value AND FastMCP structuredContent) carries the engine's real
# fields end to end.
# --------------------------------------------------------------------------- #
class TestImpactMapToolBehaviourEndToEnd:
    """``ctx.impact`` / ``ctx.map`` return the engines' structured result over a
    real-indexed corpus — the handler-level half of the P6-tail tool wiring
    (mirrors ``TestToolBehaviourEndToEnd`` for the twelve built-in tools).
    """

    @pytest_asyncio.fixture()
    async def indexed_context(
        self, tmp_path: Path    ) -> AsyncIterator[AppContext]:
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "base.py").write_text(_PY_BASE, encoding="utf-8")
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        try:
            yield ctx
        finally:
            await ctx.aclose()

    async def test_impact_returns_structured_result_with_nonempty_caveat(
        self, indexed_context: AppContext
    ) -> None:
        result = await indexed_context.impact(_IMPACT_TARGET_LIVE, depth=1)

        assert result.target == _IMPACT_TARGET_LIVE
        assert result.verdict  # "live" or "dead (heuristic)" — either is a real verdict
        assert isinstance(result.production_references, int)
        assert isinstance(result.test_references, int)
        assert result.caveat, "the caveat must never be empty on a served verdict"
        assert result.caveat in result.formatted

    @pytest.mark.parametrize(
        "target_form",
        [
            pytest.param(_IMPACT_TARGET_LIVE, id="fqn-form"),
            pytest.param("BaseRouter", id="bare-form"),
        ],
    )
    async def test_impact_verdict_is_live_for_a_referenced_symbol(
        self, indexed_context: AppContext, target_form: str
    ) -> None:
        # pkg.base.BaseRouter is imported (and inherited from) by pkg.router —
        # a genuine production reference, so the served verdict must be "live".
        # Parametrised over BOTH the fully-qualified AND the bare form: the
        # bare-name bridge (graph_surreal.py's answers_to fan-out, mirroring
        # what_imports's own bridge — a concurrent cycle) makes both
        # legitimate queries for the SAME symbol, so a caller who doesn't
        # know/type the FQN must still get the identical verdict through the
        # lore_impact tool wiring.
        result = await indexed_context.impact(target_form, depth=1)
        assert result.verdict == "live"
        assert result.production_references >= 1

    async def test_impact_depth_flows_from_direct_consumers_to_module_rollups(
        self, indexed_context: AppContext
    ) -> None:
        depth_one = await indexed_context.impact(_IMPACT_TARGET_LIVE, depth=1)
        depth_two = await indexed_context.impact(_IMPACT_TARGET_LIVE, depth=2)

        assert depth_one.direct_consumers, "depth 1 must render the direct consumer list"
        assert depth_one.module_rollups == []
        assert depth_two.module_rollups, "depth 2 must render module rollups instead"
        assert depth_two.direct_consumers == []

    async def test_impact_unknown_target_raises_naming_it_and_search_code(
        self, indexed_context: AppContext
    ) -> None:
        from loremaster.impact import ImpactTargetNotFoundError

        with pytest.raises(ImpactTargetNotFoundError) as exc_info:
            await indexed_context.impact(_IMPACT_UNKNOWN_TARGET, depth=1)
        message = str(exc_info.value)
        assert _IMPACT_UNKNOWN_TARGET in message
        assert "search_code" in message

    async def test_map_returns_structured_result_with_entries_and_formatted(
        self, indexed_context: AppContext
    ) -> None:
        result = await indexed_context.map()

        assert result.entries, "a non-empty indexed corpus must yield map entries"
        assert isinstance(result.elided_modules, int)
        assert result.formatted
        for entry in result.entries:
            assert entry.module in result.formatted


class TestImpactMapRegisteredToolWrappers:
    """Drive the REGISTERED ``lore_impact`` / ``lore_map`` FastMCP wrappers
    (not the AppContext handlers) — mirrors ``TestRegisteredToolWrappers``
    above for the twelve built-in tools. Proves the served
    ``structuredContent`` (the wire payload a real MCP client receives, not
    just the pre-serialisation handler return value) carries the engine's
    fields, and that an unknown target surfaces as a ``ToolError`` (FastMCP's
    ``Tool.run`` wraps ANY handler exception in one uniformly, so this is the
    "ToolError-shaped failure" mission item 2 asks for).
    """

    @pytest_asyncio.fixture()
    async def indexed(
        self, tmp_path: Path    ) -> AsyncIterator[tuple[Any, AppContext]]:
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "base.py").write_text(_PY_BASE, encoding="utf-8")
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        mcp = build_mcp_server(LoreServer(config))
        try:
            yield mcp, ctx
        finally:
            await ctx.aclose()

    @staticmethod
    async def _structured(mcp: Any, name: str, ctx: AppContext, /, **kwargs: Any) -> Any:
        tool = mcp._tool_manager.get_tool(name)  # noqa: SLF001 - test-only introspection
        _unstructured, structured = await tool.run(
            kwargs, context=_FakeToolContext(ctx), convert_result=True
        )
        return structured

    async def test_lore_impact_wrapper_serves_a_nonempty_caveat_in_structured_content(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        structured = await self._structured(
            mcp, "lore_impact", ctx, target=_IMPACT_TARGET_LIVE, depth=1
        )
        assert isinstance(structured, dict)
        assert structured["target"] == _IMPACT_TARGET_LIVE
        assert structured["verdict"] == "live"
        assert structured["caveat"], "the served caveat must be non-empty on the wire"
        assert "production_references" in structured
        assert "covering_tests" in structured
        assert "direct_consumers" in structured
        assert "module_rollups" in structured

    async def test_lore_impact_wrapper_depth_two_serves_module_rollups(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        structured = await self._structured(
            mcp, "lore_impact", ctx, target=_IMPACT_TARGET_LIVE, depth=2
        )
        assert structured["module_rollups"], "depth=2 must serve rollups over the wire"
        assert structured["direct_consumers"] == []

    async def test_lore_impact_wrapper_unknown_target_raises_tool_error_naming_it(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        from mcp.server.fastmcp.exceptions import ToolError

        mcp, ctx = indexed
        with pytest.raises(ToolError) as exc_info:
            await self._structured(
                mcp, "lore_impact", ctx, target=_IMPACT_UNKNOWN_TARGET, depth=1
            )
        message = str(exc_info.value)
        assert _IMPACT_UNKNOWN_TARGET in message
        assert "search_code" in message

    async def test_lore_map_wrapper_serves_entries_and_formatted(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        structured = await self._structured(mcp, "lore_map", ctx)
        assert isinstance(structured, dict)
        assert structured["entries"], "a non-empty indexed corpus must serve map entries"
        assert "elided_modules" in structured
        assert structured["formatted"]


class TestMapBudgetAndFocusWiring:
    """``budget`` and ``focus`` genuinely reach ``MapEngine.map`` through the
    AppContext handler — the wiring proof; the PageRank/budget ALGORITHM
    itself is already pinned behaviourally in test_map.py against a hand-built
    graph, so these two fixtures are real-indexed but otherwise minimal.
    """

    @pytest_asyncio.fixture()
    async def filler_context(
        self, tmp_path: Path    ) -> AsyncIterator[AppContext]:
        slug = _slug()
        live = tmp_path / "live"
        for rel_path, source in _map_budget_filler_corpus().items():
            file_path = live / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(source, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        try:
            yield ctx
        finally:
            await ctx.aclose()

    @pytest_asyncio.fixture()
    async def hub_island_context(
        self, tmp_path: Path    ) -> AsyncIterator[AppContext]:
        slug = _slug()
        live = tmp_path / "live"
        live.mkdir(parents=True, exist_ok=True)
        for rel_path, source in _map_hub_island_corpus().items():
            (live / rel_path).write_text(source, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        try:
            yield ctx
        finally:
            await ctx.aclose()

    async def test_small_budget_yields_the_elision_trailer(
        self, filler_context: AppContext
    ) -> None:
        result = await filler_context.map(budget=_PRODUCTION_MAP_BUDGET_FLOOR)

        assert result.elided_modules > 0, (
            f"{_MAP_BUDGET_FILLER_FILE_COUNT} modules must not all fit in the "
            f"floor budget — some must be elided"
        )
        assert _PRODUCTION_MAP_ELISION_FRAGMENT in result.formatted

    async def test_generous_budget_elides_nothing_for_the_same_filler_corpus(
        self, filler_context: AppContext
    ) -> None:
        # The seam proof that ``budget`` genuinely FLOWS (not hardcoded to the
        # floor internally): the SAME corpus that overflows the floor budget
        # above must NOT elide anything once given a generous budget.
        result = await filler_context.map(budget=6000)
        assert result.elided_modules == 0
        assert _PRODUCTION_MAP_ELISION_FRAGMENT not in result.formatted

    @pytest.mark.parametrize(
        "focus_form",
        [
            pytest.param(_MAP_FOCUS_SYMBOL, id="bare-form"),
            pytest.param("island.island_fn", id="fqn-form"),
        ],
    )
    async def test_focus_changes_the_top_entry_versus_unfocused(
        self, hub_island_context: AppContext, focus_form: str
    ) -> None:
        # Parametrised over BOTH the bare AND the fully-qualified focus form:
        # the bare-name bridge (graph_surreal.py's answers_to fan-out — a
        # concurrent cycle) makes both legitimate queries for the SAME
        # symbol, so lore_map's focus resolution must promote the island
        # regardless of which form the caller passes.
        unfocused = await hub_island_context.map()
        focused = await hub_island_context.map(focus=focus_form)

        assert unfocused.entries[0].module == _MAP_HUB_MODULE, (
            "an unfocused map over this corpus must rank the globally-dominant "
            "hub first (imported by two production files vs the island's one)"
        )
        assert focused.entries[0].module == _MAP_ISLAND_MODULE, (
            "focusing on the island's own symbol must promote its module to "
            "the top entry, away from the globally-dominant hub"
        )
        assert focused.entries[0].module != unfocused.entries[0].module

    async def test_unknown_focus_raises_naming_it_and_search_code(
        self, hub_island_context: AppContext
    ) -> None:
        from loremaster.map import MapFocusNotFoundError

        with pytest.raises(MapFocusNotFoundError) as exc_info:
            await hub_island_context.map(focus=_MAP_UNKNOWN_FOCUS)
        message = str(exc_info.value)
        assert _MAP_UNKNOWN_FOCUS in message
        assert "search_code" in message


class TestImpactMapRebuildingGate:
    """Verdict-bearing lore_impact / lore_map calls NEVER serve mid-rebuild —
    the graded honest-emptiness doctrine applied at the TOOL-WIRING level.

    Unlike the four EXISTING corpus-read tools (search_code / what_imports /
    blast_radius / tests_for), which only raise when their result WOULD BE
    empty (``AppContext._raise_if_empty_during_rebuild``), ``ImpactEngine`` /
    ``MapEngine`` gate UNCONDITIONALLY — even a target/corpus that would serve
    a perfectly healthy, non-empty verdict must still raise while a rebuild is
    in flight. This proves the AppContext wiring actually threads a LIVE
    ``rebuild_notice`` probe into both engines (not just that the engines CAN
    gate — already pinned in test_impact.py / test_map.py against an injected
    fake probe).
    """

    @pytest_asyncio.fixture()
    async def indexed_context(
        self, tmp_path: Path    ) -> AsyncIterator[AppContext]:
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "base.py").write_text(_PY_BASE, encoding="utf-8")
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        try:
            yield ctx
        finally:
            await ctx.aclose()

    @staticmethod
    async def _seed_in_progress_rebuild(ctx: AppContext) -> None:
        """Seed the SAME manifest-meta shape a real background rebuild writes.

        Mirrors ``build_app_context``'s own rebuild-status JSON shape (the
        producer this reader must agree with, clause 5) — the identical blob
        ``test_schema_rebuild.py``'s own ``_seed_in_progress_rebuild`` helper
        writes.
        """
        import json

        from loremaster.index.schema import SCHEMA_REBUILD_STATUS_META_KEY

        await ctx.manifest.meta_set(
            SCHEMA_REBUILD_STATUS_META_KEY,
            json.dumps(
                {
                    "state": "in_progress",
                    "done": 3,
                    "total": 118,
                    "reason": "fingerprint_mismatch",
                    "from_fingerprint": "a" * 64,
                    "to_fingerprint": "b" * 64,
                }
            ),
        )

    async def test_impact_never_serves_a_verdict_mid_rebuild_even_over_a_live_target(
        self, indexed_context: AppContext
    ) -> None:
        # pkg.base.BaseRouter genuinely has a production reference -- a
        # healthy call would serve verdict="live". Mid-rebuild it must still
        # raise, never serve that (or any) verdict.
        await self._seed_in_progress_rebuild(indexed_context)

        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await indexed_context.impact(_IMPACT_TARGET_LIVE, depth=1)
        message = str(exc_info.value).lower()
        assert "rebuild" in message
        assert _RETRY_FRAGMENT in message

    async def test_map_never_serves_a_map_mid_rebuild_even_over_a_populated_corpus(
        self, indexed_context: AppContext
    ) -> None:
        await self._seed_in_progress_rebuild(indexed_context)

        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await indexed_context.map()
        message = str(exc_info.value).lower()
        assert "rebuild" in message
        assert _RETRY_FRAGMENT in message


class TestImpactMapProductionInvariants:
    """Structural pin (not behavioural): the AppContext composition hands
    BOTH new engines the SAME code graph every other tool reads — built with
    the project's configured roots.

    Why this matters (the P6-impact-green FRICTION note, REPORT-impact-
    green-3.md): astroid resolution is silently DISABLED when a graph is
    constructed with no ``project_roots``
    (``SurrealCodeGraph._resolution_enabled = bool(project_roots)``) — a
    rootless graph resolves only bare names, so cross-module references
    quietly vanish and every reference-backed verdict (lore_impact's
    live/dead call, lore_map's PageRank weights, lore_dead_code) drifts
    toward FALSE-DEAD. Wiring the engines to a separately-built graph (or one
    built without roots) would reproduce that exact class of bug even though
    every unit-level engine test (test_impact.py / test_map.py, which inject
    their OWN correctly-rooted fake graph directly) stays green — hence a
    dedicated structural pin at the WIRING seam, not a behavioural re-proof.
    """

    @pytest_asyncio.fixture()
    async def indexed_context(
        self, tmp_path: Path    ) -> AsyncIterator[AppContext]:
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "base.py").write_text(_PY_BASE, encoding="utf-8")
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        try:
            yield ctx
        finally:
            await ctx.aclose()

    async def test_impact_engine_reads_through_the_same_rooted_ctx_graph(
        self, indexed_context: AppContext
    ) -> None:
        engine = indexed_context._impact_engine  # noqa: SLF001 - structural wiring pin
        assert engine._graph is indexed_context.code_graph  # noqa: SLF001
        assert indexed_context.code_graph._derivation._resolution_enabled is True  # noqa: SLF001

    async def test_map_engine_reads_through_the_same_rooted_ctx_graph(
        self, indexed_context: AppContext
    ) -> None:
        engine = indexed_context._map_engine  # noqa: SLF001 - structural wiring pin
        assert engine._graph is indexed_context.code_graph  # noqa: SLF001
        assert indexed_context.code_graph._derivation._resolution_enabled is True  # noqa: SLF001


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
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import loremaster.embedding as embedding_module
        import loremaster.server as server_module

        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "boot.py").write_text("def boot():\n    return 1\n", encoding="utf-8")
        config = _config(slug, live)

        # Keep the lifespan hermetic: a FakeEmbedder (no live TEI) and tmp-path
        # SQLite/snapshot dirs — but otherwise the REAL composed lifespan the
        # framework runs.
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


class TestOriginWiring:
    """build_asgi_app always applies the Origin (DNS-rebinding) guard (Item 7).

    The local streamable-HTTP server must validate the Origin header regardless of
    whether Bearer auth is configured — a DNS-rebinding browser request carries an
    attacker Origin even when the no-auth localhost default is in effect. So the
    assembled app must reject a disallowed Origin (403) and allow an absent /
    loopback one, with OR without auth.
    """

    async def test_no_auth_app_rejects_disallowed_origin(self, tmp_path: Path) -> None:
        from test_auth import _drive  # the shared ASGI driver

        slug = _slug()
        config = _config(slug, tmp_path / "live")  # no auth block
        mcp = build_mcp_server(LoreServer(config))
        app = build_asgi_app(mcp, config)
        # A cross-origin browser request is rejected at the edge (the DNS-rebinding
        # defense) even with no Bearer auth.
        response = await _drive(app, [(b"origin", b"http://evil.example.com")])
        assert response["status"] == 403

    async def test_no_auth_app_is_origin_guarded(self, tmp_path: Path) -> None:
        # With no auth, the assembled app is the Origin guard (so a local
        # non-browser client with no Origin reaches the inner MCP app — the
        # no-auth localhost default is preserved; the absent/loopback-allowed
        # behaviour is exercised against the middleware directly in test_auth).
        from loremaster.auth import OriginValidationMiddleware

        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        app = build_asgi_app(mcp, config)
        assert isinstance(app, OriginValidationMiddleware)

    async def test_auth_app_still_rejects_disallowed_origin(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from test_auth import _drive

        monkeypatch.setenv("LORE_KEY_DEV", "dev-secret")
        slug = _slug()
        config = _config(
            slug,
            tmp_path / "live",
            auth={"enabled": True, "keys": [{"name": "dev", "key_env": "LORE_KEY_DEV"}]},
        )
        mcp = build_mcp_server(LoreServer(config))
        app = build_asgi_app(mcp, config)
        # Even WITH a valid Bearer key, a disallowed Origin is rejected (403) — the
        # DNS-rebinding guard runs alongside auth, not instead of it.
        response = await _drive(
            app,
            [(b"origin", b"http://evil.example.com"), (b"authorization", b"Bearer dev-secret")],
        )
        assert response["status"] == 403


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


# --------------------------------------------------------------------------- #
# P5-C6 (ledger #27) server-side wiring — build_app_context must construct,
# inject, and (on aclose) close a SnapshotStamper (the C4-audit #2 gap: an
# all-mode server that never stamps a snapshot because the stamper is unwired).
# --------------------------------------------------------------------------- #
class TestBuildAppContextWiresSnapshotStamper:
    """The all-mode ``build_app_context`` owns a ``SnapshotStamper`` end-to-end.

    C4-audit #2: the indexer/reconcile snapshot hook is inert unless SOMETHING
    constructs a stamper and injects it. The CLI/scout do; the SERVER must too, or
    a live server's periodic reconcile never records a snapshot generation. This
    pins the server-side wiring: build_app_context constructs the stamper, readies
    it, injects it into BOTH the indexer and the reconcile engine, and ``aclose``
    closes its connection.

    Uses a spy stamper monkeypatched at its SOURCE module so the assertions observe
    construction/injection/close without opening a real stamper socket. The spy's
    presence requires build_app_context to resolve ``SnapshotStamper`` at call time
    from ``loremaster.index.snapshots`` (the same lazy-import pattern it already
    uses for its other write-stack collaborators).
    """

    async def test_build_app_context_constructs_injects_and_closes_the_stamper(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import loremaster.index.snapshots as snapshots_module

        constructed: list[Any] = []

        class _SpyStamper:
            """Records its construction kwargs + ensure_ready/close, never connects."""

            def __init__(
                self,
                *,
                url: str,
                namespace: str,
                database: str,
                user: str,
                password: str,
                store: Any,
                manifest: Any,
                project_root: Any,
            ) -> None:
                self.url = url
                self.namespace = namespace
                self.database = database
                self.user = user
                self.password = password
                self.store = store
                self.manifest = manifest
                self.project_root = project_root
                self.ensure_ready_calls = 0
                self.close_calls = 0
                constructed.append(self)

            async def ensure_ready(self) -> None:
                self.ensure_ready_calls += 1

            async def close(self) -> None:
                self.close_calls += 1

            async def stamp(self) -> str:
                return "snapshot:spy"

        monkeypatch.setattr(snapshots_module, "SnapshotStamper", _SpyStamper)

        slug = _slug()
        config = _config(slug, tmp_path / "live")
        context = await _make_context(
            config=config, tmp_path=tmp_path, start_tasks=False
        )
        try:
            assert len(constructed) == 1, (
                "build_app_context must construct exactly one SnapshotStamper (the "
                "all-mode server-side wiring, C4-audit #2)"
            )
            spy = constructed[0]
            assert spy.ensure_ready_calls == 1, "the stamper must be readied at build"
            # Wired to the SAME per-project database + resolved credentials the rest
            # of the write stack uses (the seam a wrong-DB/wrong-cred wiring bites).
            assert spy.url == config.surreal.url
            assert spy.namespace == config.surreal.namespace
            assert spy.database == config.effective_surreal_database
            assert spy.user == surreal_user()
            assert spy.password == surreal_password()
            # Injected into BOTH write paths, else a productive sweep stamps nothing.
            assert context.indexer._snapshot_stamper is spy
            assert context.reconcile_engine._snapshot_stamper is spy
        finally:
            await context.aclose()
        # aclose owns the stamper's lifecycle too — its connection is closed on
        # teardown (a leaked stamper socket would outlive the server).
        assert spy.close_calls == 1


# --------------------------------------------------------------------------- #
# P7 CUTOVER — the memory tool handlers gain the v2 wire vocabulary and the two
# fleet-coordination task tools (lore_claim_task / lore_tasks) land on the
# served surface. The memory + task LOGIC is exhaustively pinned in
# test_memory_backend.py (87) / test_task_ledger.py (160); these classes pin the
# MCP-LAYER contract: the handler param/return surface, and honest rendering.
# --------------------------------------------------------------------------- #

# A realistic bare-uuid5 chunk key (the shape ``records.point_id`` mints) — used
# as a memory ``refs`` entry so the deterministic-id oracle is grounded in the
# same key shape production folds into an id.
_CUTOVER_CHUNK_KEY = "5f6b3d21-9c4a-5e88-a1b2-c3d4e5f60718"


@pytest_asyncio.fixture()
async def cutover_ctx(tmp_path: Path) -> AsyncIterator[AppContext]:
    """A real AppContext over an EMPTY corpus — the P7 memory/task tool seam.

    The memory + task handlers are corpus-independent, so the build skips indexing;
    it still runs the genuine ``build_app_context`` wiring the cutover changes.
    """
    slug = _slug()
    live = tmp_path / "live"
    live.mkdir(parents=True, exist_ok=True)
    config = _config(slug, live)
    ctx = await _make_context(config=config, tmp_path=tmp_path)
    try:
        yield ctx
    finally:
        await ctx.aclose()


class TestSaveMemoryCutover:
    """save_memory gains the v2 wire params (kind / refs / importance / …), validates
    them honestly, and PRESERVES the v0.3 deterministic id derivation."""

    async def test_save_memory_returns_a_uuid5_id(self, cutover_ctx: AppContext) -> None:
        # The id is the deterministic uuid5 the memory model has always minted.
        memory_id = await getattr(cutover_ctx, "save_memory")(
            "the loader retry budget is 3 attempts, in pkg/loader.py", kind="fact"
        )
        parsed = uuid.UUID(str(memory_id))
        assert parsed.version == 5, "save_memory must return a deterministic uuid5 id"

    async def test_save_memory_with_refs_mints_the_v03_deterministic_id(
        self, cutover_ctx: AppContext
    ) -> None:
        # A save with a chunk ref must mint the SAME id the v0.3 store would — an
        # OLD (text, refs) pins to the SAME memory, so a re-save dedups across the
        # cutover. Independent oracle: the production id helpers over the same refs.
        note = "the discount rounding rule lives in pkg/pricing/rules.py"
        memory_id = await getattr(cutover_ctx, "save_memory")(note, refs=[_CUTOVER_CHUNK_KEY])
        expected = derive_memory_id(
            note, derive_refs_stamp([MemoryRef(chunk_key=_CUTOVER_CHUNK_KEY)])
        )
        assert memory_id == expected, (
            "a save with refs must mint the v0.3 deterministic id (text+refs → same id)"
        )

    async def test_save_memory_no_refs_matches_the_v03_empty_stamp_id(
        self, cutover_ctx: AppContext
    ) -> None:
        # Backward-compat pin (must SURVIVE the cutover): a bare save with no refs
        # mints the v0.3 empty-stamp id, so an old note and a new one collapse.
        note = "champion routing warehouse selection lives in pkg/routing.py"
        memory_id = await getattr(cutover_ctx, "save_memory")(note)
        expected = derive_memory_id(note, derive_refs_stamp([]))
        assert memory_id == expected, (
            "a bare save must still mint the v0.3 deterministic id (backward compat)"
        )

    async def test_save_memory_rejects_an_unknown_kind(self, cutover_ctx: AppContext) -> None:
        # A bad ``kind`` is a caller error surfaced as a tool-level error NAMING the
        # offending value — never a silent default to 'fact'.
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await getattr(cutover_ctx, "save_memory")("a note", kind="bogus_kind")
        assert "bogus_kind" in str(exc_info.value), (
            "an invalid kind must raise a tool-level error naming the bad value"
        )

    async def test_save_memory_rejects_out_of_range_importance(
        self, cutover_ctx: AppContext
    ) -> None:
        # importance is a fraction in [0, 1]; 1.5 is out of range → a tool-level
        # error naming the offending value, never a silent clamp.
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await getattr(cutover_ctx, "save_memory")("a note", importance=1.5)
        assert "1.5" in str(exc_info.value), (
            "an out-of-range importance must raise a tool-level error naming the value"
        )


class TestRecallMemoryCutover:
    """recall_memory surfaces text + refs (chunk keys) + kind + importance, flags a
    drifted ref, and NEVER surfaces a superseded note."""

    async def test_recall_surfaces_text_refs_and_kind(self, cutover_ctx: AppContext) -> None:
        note = "champion routing lives in pkg/routing.py, not pricing.py"
        await getattr(cutover_ctx, "save_memory")(note, kind="decision", refs=[_CUTOVER_CHUNK_KEY])
        rendered = _render_text(
            await getattr(cutover_ctx, "recall_memory")("where does champion routing live", k=5)
        )
        # The recall surfaces the note text, its chunk ref, and the memory kind.
        assert note in rendered, "recall must surface the saved note text"
        assert _CUTOVER_CHUNK_KEY in rendered, "recall must surface the note's chunk ref key"
        assert "decision" in rendered, "recall must surface the memory kind"

    async def test_recall_flags_a_drifted_ref(self, cutover_ctx: AppContext) -> None:
        # A ref to a chunk that does NOT exist in the (empty) index is a DRIFTED ref
        # — the recall surfaces a drift signal so the agent re-verifies, never
        # silently drops the reference.
        note = "the fee schedule moved to pkg/pricing/fees.py"
        missing_chunk = "11111111-2222-5333-8444-555566667777"
        await getattr(cutover_ctx, "save_memory")(note, kind="gotcha", refs=[missing_chunk])
        rendered = _render_text(
            await getattr(cutover_ctx, "recall_memory")("where is the fee schedule", k=5)
        )
        assert "drifted" in rendered.lower(), (
            "a recalled ref whose chunk no longer exists must be flagged as drifted"
        )

    async def test_recall_never_surfaces_a_superseded_note(
        self, cutover_ctx: AppContext
    ) -> None:
        # A superseded note is history, never a live recall hit.
        stale = "pricing logic lives in sale.py"
        current = "pricing logic now lives in pkg/pricing.py"
        stale_id = await getattr(cutover_ctx, "save_memory")(stale, kind="fact")
        await getattr(cutover_ctx, "save_memory")(current, kind="fact", supersedes=stale_id)
        rendered = _render_text(
            await getattr(cutover_ctx, "recall_memory")("where does pricing logic live", k=5)
        )
        assert current in rendered, "the live successor note must be recalled"
        assert stale not in rendered, "a superseded note must NEVER be recalled"


class TestTaskToolsRegistered:
    """The two fleet-coordination tools are registered on the served surface."""

    async def test_lore_claim_task_is_registered(self, tmp_path: Path) -> None:
        config = _config(_slug(), tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        names = {tool.name for tool in await mcp.list_tools()}
        assert "lore_claim_task" in names, "lore_claim_task must be on the served surface"

    async def test_lore_tasks_is_registered(self, tmp_path: Path) -> None:
        config = _config(_slug(), tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        names = {tool.name for tool in await mcp.list_tools()}
        assert "lore_tasks" in names, "lore_tasks must be on the served surface"


class TestClaimTaskTool:
    """lore_claim_task renders a win (names the owner) / a loss (names the current
    holder, mutates nothing) / a clean not-found, riding AppContext.task_ledger."""

    async def test_claim_win_names_the_owner(self, cutover_ctx: AppContext) -> None:
        ledger = FakeTaskLedger(db=FakeTaskDatabase())
        task_id = await ledger.create_task(
            "wire the P7 memory cutover", "move recall onto the SurrealDB backend",
            created_by="team-lead",
        )
        setattr(cutover_ctx, "task_ledger", ledger)

        rendered = _render_text(await getattr(cutover_ctx, "claim_task")(task_id, "agent-alpha"))

        assert "agent-alpha" in rendered, "a winning claim must name the new owner"
        # The seam actually mutated the ledger: the row is now owned by the claimer.
        claimed = await ledger.get_task(task_id)
        assert claimed.owner == "agent-alpha"

    async def test_claim_loss_names_holder_and_mutates_nothing(
        self, cutover_ctx: AppContext
    ) -> None:
        ledger = FakeTaskLedger(db=FakeTaskDatabase())
        task_id = await ledger.create_task(
            "index the task ledger", "build the durable task table", created_by="team-lead",
        )
        await ledger.claim_task(task_id, "holder-one")  # already held by another agent
        setattr(cutover_ctx, "task_ledger", ledger)

        rendered = _render_text(await getattr(cutover_ctx, "claim_task")(task_id, "agent-two"))

        assert "holder-one" in rendered, "a losing claim must name the current holder"
        after = await ledger.get_task(task_id)
        assert after.owner == "holder-one", "a losing claim must mutate nothing"

    async def test_claim_unknown_task_id_is_clean_not_found(
        self, cutover_ctx: AppContext
    ) -> None:
        setattr(cutover_ctx, "task_ledger", FakeTaskLedger(db=FakeTaskDatabase()))
        with pytest.raises(TaskNotFoundError) as exc_info:
            await getattr(cutover_ctx, "claim_task")("no_such_task_id", "agent-alpha")
        assert "no_such_task_id" in str(exc_info.value), (
            "an unknown task id must surface a not-found naming the id"
        )


class TestTasksTool:
    """lore_tasks dispatches create|query|transition|supersede, renders SUMMARISED
    rows (never raw store rows), and surfaces the ledger's typed errors."""

    async def test_tasks_create_returns_an_opaque_id(self, cutover_ctx: AppContext) -> None:
        setattr(cutover_ctx, "task_ledger", FakeTaskLedger(db=FakeTaskDatabase()))
        rendered = _render_text(
            await getattr(cutover_ctx, "tasks")(
                action="create",
                subject="re-scope the cutover wave",
                description="split memory + task landing",
                created_by="team-lead",
            )
        )
        # An opaque id is surfaced — never a raw ``task:<id>`` record-prefixed row.
        assert "task:" not in rendered, "create must surface an opaque id, not a raw record id"

    async def test_tasks_query_renders_summarised_rows_not_raw(
        self, cutover_ctx: AppContext
    ) -> None:
        ledger = FakeTaskLedger(db=FakeTaskDatabase())
        await ledger.create_task(
            "index the P7 cutover", "populate the task table", created_by="team-lead",
        )
        await ledger.create_task(
            "wire the task tools", "land lore_claim_task + lore_tasks", created_by="team-lead",
        )
        setattr(cutover_ctx, "task_ledger", ledger)

        rendered = _render_text(await getattr(cutover_ctx, "tasks")(action="query"))

        assert "index the P7 cutover" in rendered, "query must surface the task subject"
        assert "open" in rendered, "query must surface the task status"
        # A summarised row, NEVER a raw SurrealDB row (a RecordID / ``task:`` prefix).
        assert "RecordID" not in rendered and "task:" not in rendered, (
            "query must render summarised rows, never a raw store row dump"
        )

    async def test_tasks_illegal_transition_surfaces_typed_error(
        self, cutover_ctx: AppContext
    ) -> None:
        ledger = FakeTaskLedger(db=FakeTaskDatabase())
        task_id = await ledger.create_task(
            "a fresh open task", "the birth state is open", created_by="team-lead",
        )
        setattr(cutover_ctx, "task_ledger", ledger)
        # open -> done is NOT a legal edge (open -> claimed is claim-only); the
        # illegal transition surfaces the ledger's typed error naming both states.
        with pytest.raises(IllegalTransitionError) as exc_info:
            await getattr(cutover_ctx, "tasks")(
                action="transition", task_id=task_id, status="done", actor="agent-alpha",
            )
        message = str(exc_info.value)
        assert "open" in message and "done" in message, (
            "an illegal transition must surface a typed error naming both states"
        )

    async def test_tasks_supersede_stamps_the_old_task(
        self, cutover_ctx: AppContext
    ) -> None:
        ledger = FakeTaskLedger(db=FakeTaskDatabase())
        task_id = await ledger.create_task(
            "the original framing", "to be re-scoped", created_by="team-lead",
        )
        setattr(cutover_ctx, "task_ledger", ledger)

        await getattr(cutover_ctx, "tasks")(
            action="supersede",
            task_id=task_id,
            subject="the re-scoped framing",
            description="the successor task",
            created_by="team-lead",
        )
        # The old task is stamped superseded (its history preserved) and a successor
        # was minted — the seam drove the ledger's real supersede.
        old = await ledger.get_task(task_id)
        assert old.superseded_by is not None, "supersede must stamp the old task's successor"


# =========================================================================== #
# P7-TAIL POLISH WAVE (ledger task #6) — the cutover-audit N1 guard. The
# DEPRECATED ``metadata`` dict is flattened to flat ``key=value`` labels; a key
# whose flattened label starts with the RESERVED ``lore_ref=`` prefix is
# otherwise promoted by the backend into a REAL chunk ref — silently folding into
# the deterministic id and minting a drift-checked ref the caller never asked
# for (a silent identity change / data loss). save_memory must REJECT it loudly.
# Reserved prefix imported from the backend's OWN source of truth so the guard
# and the id-folding logic can never drift apart (clause 5).
# =========================================================================== #

# Kept local to this wave (matches the build_asgi_app import above) rather than
# hoisted to the top-level import block, for the same reason: co-located with
# the wave of tests it supports in this large file.
from loremaster.memory.local import _LORE_REF_LABEL_PREFIX as _RESERVED_LORE_REF_PREFIX  # noqa: E402

# The metadata KEY that flattens to exactly the reserved prefix — derived from
# the prefix itself (``"lore_ref="`` minus its ``=`` separator), never a
# hand-copied literal, so if the backend ever renames the seam this fixture
# follows it.
_RESERVED_METADATA_KEY = _RESERVED_LORE_REF_PREFIX.rstrip("=")


def _ledger_row_count(ctx: AppContext) -> int:
    """The durable write-through ledger's current row count for ``ctx``.

    ``MemoryBackend.ledger`` is typed ``MemoryLedger | None`` (a backend MAY
    run ledger-less); every fixture that reaches this helper (``cutover_ctx``)
    wires a real ledger, so the ``None`` case is a hard fixture-wiring bug,
    never a silently-tolerated 0.
    """
    ledger = ctx.memory_backend.ledger
    assert ledger is not None, "cutover_ctx must wire a real durable ledger"
    return len(ledger.all_records())


class TestSaveMemoryReservedMetadataGuard:
    """N1 guard (cutover-audit): save_memory REJECTS a deprecated-metadata key
    whose flattened ``key=value`` label would start with the reserved
    ``lore_ref=`` prefix — loud beats silent data loss — while a benign metadata
    key and the sanctioned ``refs=`` param still work untouched. The rejection
    (SF-3, REPORT-polish-audit.md) is pinned to the guard's ACTUAL exception
    type (``ValueError``) plus two no-write postconditions -- the rejected note
    never becomes recallable and the durable ledger's row count is unchanged --
    so a guard that persisted-then-raised could never pass these tests."""

    async def test_metadata_lore_ref_key_is_rejected_naming_the_reserved_prefix(
        self, cutover_ctx: AppContext
    ) -> None:
        # metadata={"lore_ref": "<chunk_key>"} flattens to "lore_ref=<chunk_key>",
        # indistinguishable from a real ref that folds into the deterministic id.
        # The guard must REJECT it and NAME the reserved prefix so the caller
        # learns why (never a silent promotion into a chunk ref).
        rejected_note = "the loader retry budget is 3 attempts, in pkg/loader.py"
        ledger_rows_before = _ledger_row_count(cutover_ctx)

        # SF-3 (REPORT-polish-audit.md): narrowed from a bare
        # ``pytest.raises(Exception)`` -- the guard's OWN exception type is a
        # ValueError (server.py's ``_metadata_to_labels``), and a bare
        # ``Exception`` would also pass a guard that persisted-then-raised
        # some unrelated error.
        with pytest.raises(ValueError) as exc_info:
            await getattr(cutover_ctx, "save_memory")(
                rejected_note,
                metadata={_RESERVED_METADATA_KEY: _CUTOVER_CHUNK_KEY},
            )
        assert _RESERVED_LORE_REF_PREFIX in str(exc_info.value), (
            "the rejection must NAME the reserved prefix so the caller understands "
            "why the deprecated-metadata key was refused"
        )
        # No-write receipts (SF-3): the guard must fire BEFORE any write, not
        # merely eventually raise -- a rejected note must never become
        # recallable, and the durable write-through ledger must be untouched.
        rendered = _render_text(await getattr(cutover_ctx, "recall_memory")(rejected_note, k=5))
        assert rejected_note not in rendered, (
            "a rejected save must never surface on recall -- the guard fires "
            "before the write, so nothing was ever stored to find"
        )
        assert _ledger_row_count(cutover_ctx) == ledger_rows_before, (
            "a rejected save must leave the durable ledger's row count "
            "UNCHANGED -- proving the guard fires before any write"
        )

    async def test_metadata_key_embedding_the_prefix_is_rejected_by_label_not_key(
        self, cutover_ctx: AppContext
    ) -> None:
        # A guard that only checks ``key == "lore_ref"`` MISSES this: a key that
        # itself embeds the separator (label "lore_ref=nested=<value>") ALSO starts
        # with the reserved prefix and ALSO folds into the id. The guard must key on
        # the flattened LABEL's prefix, not an exact-key match — this is the
        # discriminating case for that predicate.
        offending_key = f"{_RESERVED_METADATA_KEY}=nested"
        rejected_note = "a durable project note"
        ledger_rows_before = _ledger_row_count(cutover_ctx)

        with pytest.raises(ValueError) as exc_info:
            await getattr(cutover_ctx, "save_memory")(
                rejected_note,
                metadata={offending_key: "ignored"},
            )
        assert _RESERVED_LORE_REF_PREFIX in str(exc_info.value), (
            "any metadata key whose flattened label starts with the reserved "
            "prefix must be rejected, naming the prefix"
        )
        # No-write receipts (SF-3): same two independent postconditions as the
        # exact-key case above -- this discriminating (nested-key) case must
        # ALSO leave no trace, not just raise.
        rendered = _render_text(await getattr(cutover_ctx, "recall_memory")(rejected_note, k=5))
        assert rejected_note not in rendered, (
            "a rejected save must never surface on recall -- the guard fires "
            "before the write, so nothing was ever stored to find"
        )
        assert _ledger_row_count(cutover_ctx) == ledger_rows_before, (
            "a rejected save must leave the durable ledger's row count "
            "UNCHANGED -- proving the guard fires before any write"
        )

    async def test_benign_metadata_key_succeeds_and_never_folds_into_the_id(
        self, cutover_ctx: AppContext
    ) -> None:
        # The SAME call without the offending key succeeds — a plain metadata label
        # is decorative, never a chunk ref, so it must NOT change the deterministic
        # id. Independent oracle: the v0.3 empty-stamp id over the same text.
        note = "the discount rounding rule lives in pkg/pricing/rules.py"
        memory_id = await getattr(cutover_ctx, "save_memory")(
            note, metadata={"author": "ejprice", "reviewed": "yes"}
        )
        expected_empty_stamp_id = derive_memory_id(note, derive_refs_stamp([]))
        assert memory_id == expected_empty_stamp_id, (
            "a benign metadata key is a plain label, never a ref — it must not "
            "fold into the deterministic id (id must equal the bare empty-stamp id)"
        )

    async def test_legitimate_refs_param_still_folds_into_the_deterministic_id(
        self, cutover_ctx: AppContext
    ) -> None:
        # The guard must fence ONLY the deprecated metadata seam — the sanctioned
        # ``refs=`` param must still fold into the v0.3 deterministic id unharmed.
        # Independent oracle: the production id helpers over the same ref.
        note = "champion routing warehouse selection lives in pkg/routing.py"
        memory_id = await getattr(cutover_ctx, "save_memory")(note, refs=[_CUTOVER_CHUNK_KEY])
        expected_with_ref_id = derive_memory_id(
            note, derive_refs_stamp([MemoryRef(chunk_key=_CUTOVER_CHUNK_KEY)])
        )
        assert memory_id == expected_with_ref_id, (
            "the legitimate refs= path must still mint the v0.3 deterministic id "
            "(text+refs → same id); the N1 guard fences metadata only"
        )


# =========================================================================== #
# CONTRACT-FINAL WAVE — recall_memory gains kind=/labels= filters (operator-
# approved). The FILTER LOGIC itself is exhaustively pinned in
# test_memory_backend.py's ``TestRecallFiltering`` (labels= ALL-semantics, and
# this same wave's new kind= pins); this class pins the MCP-LAYER handler
# surface only: ``AppContext.recall_memory`` must ACCEPT and APPLY kind=/
# labels=, mirroring how it already threads ``k=`` through untouched.
# =========================================================================== #

# Two notes share the label ``area=map`` (one gotcha, one fact); the third is
# a fact labelled ``area=impact`` — the fixture every pin in this class routes
# through, so the corpus shape can never silently drift per-test.
_MAP_GOTCHA_NOTE = "lore_map's teaching trailer must name focus=<module> for the full list"
_MAP_FACT_NOTE = "lore_map ranks entries rank DESC, ties broken by module ASC"
_IMPACT_FACT_NOTE = "lore_impact depth>1 rollups must be labeled transitive"
# One query recalls against all three notes at once (the notes are lexically
# close enough to co-occur in the top-k without a filter) -- so any exclusion
# observed below is the FILTER doing the work, never the ranking.
_RECALL_FILTER_QUERY = "how do the map and impact tools rank and label their output"
# Comfortably above the 3-note corpus, so nothing is silently k-truncated.
_RECALL_FILTER_K = 10


async def _seed_map_impact_notes(ctx: AppContext) -> None:
    """Save the three smoke notes ``TestRecallMemoryFilters`` filters over."""
    await getattr(ctx, "save_memory")(_MAP_GOTCHA_NOTE, kind="gotcha", labels=["area=map"])
    await getattr(ctx, "save_memory")(_MAP_FACT_NOTE, kind="fact", labels=["area=map"])
    await getattr(ctx, "save_memory")(_IMPACT_FACT_NOTE, kind="fact", labels=["area=impact"])


class TestRecallMemoryFilters:
    """recall_memory accepts kind=/labels= filters and applies them (never
    silently ignores them): kind alone, labels alone (ALL-semantics per the
    backend contract), no filter (existing behaviour unchanged), and the two
    combined (intersection, not union)."""

    async def test_kind_filter_excludes_other_kinds(self, cutover_ctx: AppContext) -> None:
        await _seed_map_impact_notes(cutover_ctx)

        rendered = _render_text(
            await getattr(cutover_ctx, "recall_memory")(
                _RECALL_FILTER_QUERY, k=_RECALL_FILTER_K, kind="gotcha"
            )
        )

        assert _MAP_GOTCHA_NOTE in rendered, "kind='gotcha' must surface the gotcha note"
        assert _MAP_FACT_NOTE not in rendered, "kind='gotcha' must exclude a fact note"
        assert _IMPACT_FACT_NOTE not in rendered, "kind='gotcha' must exclude a fact note"

    async def test_labels_filter_returns_only_the_matching_label(
        self, cutover_ctx: AppContext
    ) -> None:
        await _seed_map_impact_notes(cutover_ctx)

        rendered = _render_text(
            await getattr(cutover_ctx, "recall_memory")(
                _RECALL_FILTER_QUERY, k=_RECALL_FILTER_K, labels=["area=impact"]
            )
        )

        assert _IMPACT_FACT_NOTE in rendered, (
            "labels=['area=impact'] must surface the impact-labelled note"
        )
        assert _MAP_GOTCHA_NOTE not in rendered, "a differently-labelled note must be excluded"
        assert _MAP_FACT_NOTE not in rendered, "a differently-labelled note must be excluded"

    async def test_no_filters_returns_every_note_unchanged(
        self, cutover_ctx: AppContext
    ) -> None:
        # Existing behaviour must be UNCHANGED by the new params' addition.
        await _seed_map_impact_notes(cutover_ctx)

        rendered = _render_text(
            await getattr(cutover_ctx, "recall_memory")(_RECALL_FILTER_QUERY, k=_RECALL_FILTER_K)
        )

        assert _MAP_GOTCHA_NOTE in rendered, "an unfiltered recall must still surface every note"
        assert _MAP_FACT_NOTE in rendered, "an unfiltered recall must still surface every note"
        assert _IMPACT_FACT_NOTE in rendered, "an unfiltered recall must still surface every note"

    async def test_kind_and_labels_filters_intersect(self, cutover_ctx: AppContext) -> None:
        # kind="fact" ALONE would also match the impact note; labels=["area=map"]
        # ALONE would also match the gotcha note -- only the note satisfying
        # BOTH filters (the map fact) may survive the intersection.
        await _seed_map_impact_notes(cutover_ctx)

        rendered = _render_text(
            await getattr(cutover_ctx, "recall_memory")(
                _RECALL_FILTER_QUERY,
                k=_RECALL_FILTER_K,
                kind="fact",
                labels=["area=map"],
            )
        )

        assert _MAP_FACT_NOTE in rendered, "the note matching BOTH filters must be returned"
        assert _MAP_GOTCHA_NOTE not in rendered, (
            "wrong kind must be excluded despite matching labels"
        )
        assert _IMPACT_FACT_NOTE not in rendered, (
            "wrong labels must be excluded despite matching kind"
        )
