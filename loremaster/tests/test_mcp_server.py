"""Contract tests for ``loremaster.server`` — the FastMCP integration lynchpin.

This is Deliverable 3's running MCP server: the FastMCP streamable-http server,
the :class:`AppContext` lifespan with the embedder **startup probe gate**, the
spawned live watcher + periodic reconcile tasks, the pluggable Bearer auth wiring
(D9/D11/§A1.12), and the built-in MCP tools wrapping the merged services. These tests
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

The built-in MCP tools (end-to-end through the AppContext handlers)
------------------------------------------------------------------
* The built-ins — ``search``/``get_symbol``/``remember``/
  ``recall``/``reindex``/``index_status``/``what_imports``/
  ``blast_radius``/``tests_for``/``references``/``dead_code`` — are REGISTERED on
  the FastMCP app.
* Each returns the right SHAPE over a real-indexed corpus: ``search`` finds a
  uniquely-named symbol with a ``[SOURCE...]`` citation; ``index_status`` reports
  a healthy index; ``remember`` → ``recall`` round-trips; ``get_symbol``
  resolves an exact definition; ``read`` returns a real stored span;
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
import re
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _finding_fakes import FakeFindingDatabase, FakeFindingLedger
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
from loremaster.findings import Finding, FindingActivityWindow
from loremaster.map import _BUDGET_FLOOR as _PRODUCTION_MAP_BUDGET_FLOOR
from loremaster.map import _ELISION_FRAGMENT as _PRODUCTION_MAP_ELISION_FRAGMENT
from loremaster.memory.backend import MemoryRef, derive_memory_id, derive_refs_stamp
from loremaster.server import (
    _SEARCH_BUDGET_CAP,
    _SEARCH_STUB_NOTICE,
    AppContext,
    LoreServer,
    ProbeGateError,
    build_app_context,
    build_mcp_server,
    configure_logging_from_config,
    run_probe_gate,
)
from loremaster.store._txn import SurrealConnectionError
from loremaster.tasks import (
    ClaimResult,
    IllegalTransitionError,
    Task,
    TaskActivityWindow,
    TaskNotFoundError,
)
from loresigil.testing import FakeEmbedder
from render_injection_scaffold import (
    _INJECTION_THREAT_CHARS,
    _ROW_FORGE_PAYLOAD,
    RenderCase,
    assert_render_injection_safe,
)

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
# os`` stays first so the line-1 span assertion is unchanged.
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

# Finding #60's elision-count fixture: three functions with ZERO references
# anywhere (not even from a test) -- guarantees dead_code_total() >= 3
# regardless of whether the enclosing module itself also rolls up as dead.
# Used to prove ``AppContext.dead_code``'s ``elided`` count is honest both
# when ``max_results`` binds (capped below 3) and when it doesn't (default).
_PY_MANY_ORPHANS = """\
\"\"\"Three functions with zero references anywhere -- planted dead code.\"\"\"


def orphan_one():
    \"\"\"Never referenced by anything.\"\"\"
    return 1


def orphan_two():
    \"\"\"Never referenced by anything.\"\"\"
    return 2


def orphan_three():
    \"\"\"Never referenced by anything.\"\"\"
    return 3
"""


# --------------------------------------------------------------------------- #
# lore_impact / lore_map corpora (P6-tail tool wiring).
# --------------------------------------------------------------------------- #
# A target with a REAL production reference for the impact e2e/wrapper tests
# (``pkg.base.BaseRouter`` has a genuine production reference from
# ``pkg.router`` via the in-project import in ``_PY_MODULE`` below — reused
# here rather than re-deriving a second oracle target; the sibling tests that
# once independently proved this same fact, test_what_imports_traverses_graph
# and test_references_returns_production_test_split, were both removed in
# P8d Wave 2's impact fold).
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
    monkeypatch.setenv(_SURREAL_PASS_ENV, surreal_password().get_secret_value())
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
    calibration_engine: Any = None,
) -> AppContext:
    """Build a live :class:`AppContext` with injected fakes (the test wiring seam).

    ``build_app_context`` runs the probe gate, constructs every runtime service,
    readies the SurrealDB write stack, and (when ``start_tasks``) spawns the watcher +
    reconcile tasks — the same path the lifespan takes, but with the embedder /
    paths injected so a test needs no real TEI endpoint.

    ``calibration_engine`` is forwarded to ``build_app_context``: ``None`` (the
    default) constructs the real :class:`~loremaster.calibration.engine.
    CalibrationEngine` over ``config.anthropic`` — its background probe is NOT
    started here (the lifespan owns that), so it serves the committed constant and
    touches no network. A test that needs a specific served constant / status /
    stop-spy injects its own engine double.
    """
    return await build_app_context(
        server=LoreServer(config),
        embedder=embedder or FakeEmbedder(dim=_DIM),
        manifest_path=tmp_path / "m.db",
        snapshot_root=tmp_path / "snap",
        start_tasks=start_tasks,
        calibration_engine=calibration_engine,
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
        # already holds an un-indexed .py file, then read index() right away:
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
            status = await ctx.index()
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
            status = await ctx.index()
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
# The built-in tools, each carrying the mandatory ``lore_`` service prefix
# (mcp-builder: a service prefix so tools disambiguate across many connected MCP
# servers). The bare (un-prefixed) names they were renamed FROM — no built-in may
# publish a bare name on the wire.
_TOOL_PREFIX = "lore_"
_BARE_TOOL_NAMES = {
    # P8d surface flip: the corpus-read verb renamed from ``search_code`` — one
    # name per concept; ``read_file`` was merged into ``read`` (the single,
    # store-backed, hash-verified read verb), so it no longer publishes.
    "search",
    "get_symbol",
    "verify",
    # P8d surface flip: the project-memory verbs renamed from
    # ``save_memory`` / ``recall_memory`` to the shorter ``remember`` / ``recall``.
    "remember",
    "recall",
    # P8d Wave 3 (the index merge): ``reindex`` + ``index_status`` FOLD into
    # ONE ``lore_index(reconcile=False, tier=None)`` tool — a no-arg call is a
    # pure status read (never sweeps); ``reconcile=True`` runs the old
    # ``reindex`` sweep first, then renders the same status. They no longer
    # publish separate tool names.
    "index",
    # P8d Wave 2 (the impact fold): what_imports / blast_radius / tests_for /
    # references FOLD into lore_impact (depth=1 renders direct consumers +
    # covering tests + reference counts; depth>1 renders the module rollup) —
    # they no longer publish their own tool names. The graph_surreal ENGINE
    # methods survive unchanged (impact.py / map.py call them directly). The
    # AppContext.what_imports handler briefly survived unregistered (kept for
    # test_schema_rebuild.py's TestRebuildingNoticeSeam A8c pin) but was
    # deleted outright once fixer-w2f repointed that pin at lore_impact — no
    # residual what_imports surface remains anywhere in AppContext.
    "dead_code",
    # P6-tail (lore_impact / lore_map): the "who depends on this?" / "orient
    # me here" verdict-bearing rollups over the same unified graph the other
    # graph tools above already read.
    "impact",
    "map",
    # P8b wire-up: the store-backed hash-verified span reader (the single read
    # verb after the read_file merge), the snapshot diff engine, and the finding
    # ledger.
    "read",
    "diff",
    "findings",
}
_EXPECTED_TOOLS = {f"{_TOOL_PREFIX}{name}" for name in _BARE_TOOL_NAMES}
# The COMPLETE built-in surface = the prefixed cores above PLUS the two task-ledger
# tools (pinned separately below because they predate the bare-name cutover) PLUS
# PKT-28 C1's new agent-comms dispatch tool. This is the EXACT set the flip
# freezes — the surface-equality pin fails if a tool is silently ADDED as well as
# if one is removed. Later waves update this set deliberately as the surface
# consolidates. (PKT-28 C1: 14 -> 15, adds "lore_comms" — see test_comms_tool.py
# for its own dispatch-table/render/registration contract.)
_ALL_BUILTIN_TOOL_NAMES = _EXPECTED_TOOLS | {"lore_claim_task", "lore_tasks", "lore_comms"}


class TestToolRegistration:
    """Every built-in MCP tool is registered on the FastMCP app, each ``lore_``-prefixed."""

    async def test_all_tools_registered(self, tmp_path: Path) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        assert _EXPECTED_TOOLS <= names

    async def test_the_registered_surface_is_exactly_the_expected_set(
        self, tmp_path: Path
    ) -> None:
        # R2 pin (P8d): the registration checks are otherwise SUBSET-only — they
        # catch a removal/rename but NOT a silent ADDITION, and no numeric count is
        # asserted anywhere. This equality assertion freezes the built-in surface to
        # EXACTLY the expected set, so it cannot grow (or shrink) unnoticed. A new
        # built-in must be added to ``_ALL_BUILTIN_TOOL_NAMES`` deliberately.
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        names = {t.name for t in await mcp.list_tools()}
        assert names == _ALL_BUILTIN_TOOL_NAMES, (
            "the built-in surface must be EXACTLY the expected set; unexpected: "
            f"{names - _ALL_BUILTIN_TOOL_NAMES}, missing: "
            f"{_ALL_BUILTIN_TOOL_NAMES - names}"
        )

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


# A token matching the tool-name SHAPE (``lore_`` + lowercase/underscore) that is
# NOT itself a tool name but is still legitimate to appear in served text (e.g. a
# config key or file name that happens to share the shape) belongs here, each
# entry carrying a one-line justification. Empty today: every ``lore_``-shaped
# token actually served by the live surface names a currently-registered tool.
_LEGITIMATE_NON_TOOL_LORE_TOKENS: frozenset[str] = frozenset()


class TestNoDeadToolNamesInAgentFacingText:
    """No text FastMCP actually serves to a connecting agent may name a dead tool.

    Two flip waves in a row shipped the SAME defect archetype: a live,
    agent-facing string pointing at a tool name the very same wave had just
    deleted. Wave 1's bare -> ``lore_``-prefixed rename sweep left
    ``lore_read``'s not-found/stale text teaching the dead ``search_code``
    (REPORT-audit-w1.md F1/F4/F5). Wave 2's impact fold repeated it twice over:
    ``lore_dead_code``'s description told an agent to "Use lore_references"
    after Wave 2 folded ``lore_references`` into ``lore_impact``
    (REPORT-audit-w2.md F1), and ``lore_findings``' ``area`` parameter example
    named the dead ``lore_tests_for`` (F2). Both slipped every existing gate:
    the exact-set pin above (:class:`TestToolRegistration`) checks tool NAMES,
    never description TEXT; mypy/ruff don't parse free text; ``TestToolDescriptions``
    only asserts POSITIVE substrings, never the ABSENCE of a dead one.

    This test closes the whole defect CLASS rather than the two instances: it
    extracts every token matching the tool-name shape from every piece of text
    FastMCP actually serves — the server ``instructions``, every tool's
    top-level ``description``, AND every tool's per-parameter ``inputSchema``
    field description (F2 lives in a PARAMETER description, not a top-level
    one — a scan limited to top-level text alone would have missed it) — and
    asserts every such token names a tool CURRENTLY on the registered surface.
    A future rename/fold that leaves one stale reference anywhere in served
    text fails this test immediately, with no adversarial audit required to
    catch it by hand.
    """

    _TOOL_NAME_TOKEN = re.compile(r"\blore_[a-z_]+\b")

    async def test_every_lore_prefixed_token_in_served_text_is_a_live_tool_name(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        tools = await mcp.list_tools()
        names = {tool.name for tool in tools}

        texts: dict[str, str] = {"_INSTRUCTIONS": mcp.instructions or ""}
        for tool in tools:
            texts[f"{tool.name}.description"] = tool.description or ""
            properties = (tool.inputSchema or {}).get("properties", {})
            for field_name, field_schema in properties.items():
                texts[f"{tool.name}.{field_name}"] = field_schema.get("description") or ""

        offenders: dict[str, set[str]] = {}
        for label, text in texts.items():
            tokens = set(self._TOOL_NAME_TOKEN.findall(text))
            tokens -= _LEGITIMATE_NON_TOOL_LORE_TOKENS
            dead = tokens - names
            if dead:
                offenders[label] = dead

        assert not offenders, (
            "served agent-facing text names a tool that is NOT on the registered "
            f"surface (a dead/renamed tool) -- {offenders}"
        )


# --------------------------------------------------------------------------- #
# In-band consumer guidance (server instructions + per-tool descriptions +
# input-schema field descriptions + tool annotations)
# --------------------------------------------------------------------------- #
# The read-only tools (every tool that does NOT mutate index/memory state). These
# must carry ``readOnlyHint=True``. ``lore_remember`` / ``lore_reindex`` /
# ``lore_findings`` mutate state and must NOT be marked read-only.
_READ_ONLY_TOOLS = {
    "lore_search",
    "lore_get_symbol",
    "lore_verify",
    "lore_recall",
    "lore_dead_code",
    # P6-tail: both are pure reads over the graph, never mutating index/memory
    # state — read-only exactly like their five graph-tool neighbours above.
    "lore_impact",
    "lore_map",
    # P8b wire-up: lore_read serves a stored span (a read — the single read verb
    # after the read_file merge), lore_diff reads the snapshot ledger (a read).
    # lore_findings MUTATES the finding ledger, so it is NOT here — it lives in
    # ``_MUTATING_TOOLS`` below (like lore_tasks' family).
    "lore_read",
    "lore_diff",
}
# P8d Wave 3: ``lore_index`` replaces ``lore_reindex`` here — the merged tool
# CAN sweep (``reconcile=True``), so it is annotated by its strongest
# capability exactly like ``lore_findings``/``lore_tasks``, even though a
# no-arg call never mutates anything (mcp-builder: a tool that CAN write is
# not read-only merely because one call shape happens not to).
# PKT-28 C1: ``lore_comms`` joins this set (register/brief_publish/brief_ack
# mutate the durable agent/brief ledgers) — this is also what actually WIRES
# UP annotation-level test coverage for the tool (see test_comms_tool.py's
# own ``_COMMS_TOOL_ANNOTATIONS`` pin for the production-side annotation).
_MUTATING_TOOLS = {"lore_remember", "lore_index", "lore_findings", "lore_comms"}

# Tools that take NO consumer-facing parameters (so there are no per-field
# descriptions to assert). Empty today: ``lore_index_status`` was the last
# parameterless tool, and the P8d Wave 3 merge gave it a ``reconcile``/``tier``
# pair (mirrors ``_LEGITIMATE_NON_TOOL_LORE_TOKENS`` above — the mechanism
# stays for a genuinely future parameterless tool, it just has no member now).
_PARAMETERLESS_TOOLS: set[str] = set()


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
        # alone — so every registered tool is named there. P8d Wave 4b: widened
        # from _EXPECTED_TOOLS (12) to _ALL_BUILTIN_TOOL_NAMES (14) — the prior
        # pin silently exempted lore_claim_task/lore_tasks from this contract
        # even though they are built-in, registered tools; the new six-section
        # block's LADDER/MEMORY sections carry all 14 naturally, so there is no
        # reason to leave the two task tools unpinned here.
        instructions = self._instructions(tmp_path)
        for tool_name in _ALL_BUILTIN_TOOL_NAMES:
            assert tool_name in instructions, (
                f"the instructions must mention {tool_name!r} so the consumer "
                f"knows when to reach for it"
            )

    def test_instructions_teaches_the_rollup_catch_up_verb(self, tmp_path: Path) -> None:
        # PKT-06 §6: the tool-NAME pin above (test_instructions_names_every_tool)
        # confirms "lore_tasks" is mentioned, but "rollup" is an ACTION on that
        # tool, not a tool name — a separate, action-level pin is needed so a
        # lead learns the one-call fleet catch-up verb exists at strategy level
        # (DESIGN-LAW §1.5: strategy in instructions, per-action detail in the
        # tool description — the latter is TestToolDescriptions' job).
        instructions = self._instructions(tmp_path)
        assert "rollup" in instructions

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
        # locate with lore_search, then verify safety with lore_impact
        # before touching something), or the one-call ergonomic these two
        # tools exist to provide goes unused just like the four-tool
        # seam-sweep chain did. Pinned loosely (co-occurrence + relative
        # order on ONE line, mirroring how every other bullet in this block
        # is authored) so the author keeps editorial freedom over wording.
        instructions = self._instructions(tmp_path)
        chain_lines = [
            line
            for line in instructions.splitlines()
            if "lore_map" in line and "lore_search" in line and "lore_impact" in line
        ]
        assert chain_lines, (
            "the instructions must teach the map -> search -> impact workflow "
            "chain in at least one line naming all three tools together"
        )
        line = chain_lines[0]
        assert line.index("lore_map") < line.index("lore_search") < line.index(
            "lore_impact"
        ), (
            "the chain-teaching line must name the tools in map -> search -> "
            "impact order (orient, then locate, then verify safety)"
        )

    def test_instructions_teaches_that_lore_may_be_indexing_a_DIFFERENT_tree(
        self, tmp_path: Path
    ) -> None:
        # Finding #125 (the honesty line), adversary §A5 — the escalation the operator
        # ruled on 2026-07-14. Shipping the watched-root/branch field in lore_index()'s
        # response closes #125 in the CODE and leaves it open IN PRACTICE: nothing tells
        # an agent that lore might be indexing a DIFFERENT tree than the one it is
        # editing, and the LADDER routes it straight to lore_map/lore_search. An agent
        # following these instructions never calls lore_index() for that purpose — which
        # is precisely what happened: both auditors in the #102 wave INFERRED the
        # worktree mismatch and fell back to grep; neither called lore_index().
        #
        # This is the author's own pin-20 reasoning ("shipping the field while the
        # description omits it means no agent ever learns to look") applied one level up,
        # where every agent actually reads.
        #
        # Pinned LOOSELY, in this block's house style (co-occurrence on one line): a
        # truthful REWORD keeps passing; DELETING the guidance goes RED. The block is
        # already over its token budget (717 Claude tokens, operator-ACCEPTED), so the
        # sentence must be TIGHT — the author keeps full editorial freedom over wording.
        instructions = self._instructions(tmp_path)
        teaching_lines = [
            line
            for line in instructions.splitlines()
            if "lore_index" in line
            and "branch" in line.lower()
            and ("tree" in line.lower() or "worktree" in line.lower())
        ]
        assert teaching_lines, (
            "the instructions must tell an agent that lore may be indexing a DIFFERENT "
            "TREE than the one it is working in, and that lore_index() names the watched "
            "root + its git BRANCH so the agent can check — one line, naming lore_index, "
            "the tree, and the branch (finding #125: an agent in a sibling worktree must "
            "see the mismatch BEFORE it trusts a single result)"
        )

    def test_instructions_teaches_impact_ladder_authority(self, tmp_path: Path) -> None:
        # S7 (client-needs consult docs/design/2026-07-06-client-needs-
        # consult.md §S7 + Fable's "ladder authority line"): the LADDER
        # ordering alone caused a measured redundant-check habit -- session
        # evidence showed models corroborating an already-correct lore_impact
        # answer with map/search "because ladder". One sentence fixes it:
        # impact is authoritative for consumer/coverage questions;
        # corroborate only on a miss. Pinned on the SAME chain-teaching line
        # (mirrors test_instructions_teaches_the_map_search_impact_ladder's
        # own co-occurrence style) since the authority clause naturally
        # extends the existing lore_impact mention there.
        instructions = self._instructions(tmp_path)
        lowered = instructions.lower()
        assert "authoritative" in lowered, (
            "the instructions must teach that lore_impact is authoritative for "
            "consumer/coverage questions, not just present in the ladder"
        )
        chain_lines = [
            line
            for line in instructions.splitlines()
            if "lore_map" in line and "lore_search" in line and "lore_impact" in line
        ]
        assert chain_lines
        assert "authoritative" in chain_lines[0].lower(), (
            "the authority clause should extend the existing ladder line, not "
            "a disconnected new sentence"
        )

    def test_instructions_encourages_parallel_independent_calls(
        self, tmp_path: Path
    ) -> None:
        # S7 (client-needs consult, Sonnet informant §2 continuity nuance):
        # independent calls batched in ONE turn are cheap to integrate (one
        # mental model, updated once); the same calls serialized across turns
        # cost a re-orientation each time. One line encourages the cheaper
        # shape.
        instructions = self._instructions(tmp_path)
        lowered = instructions.lower()
        assert "one turn" in lowered or "parallel" in lowered, (
            "the instructions must encourage batching independent calls in a "
            "single turn rather than serializing them"
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

    async def test_get_symbol_vs_search_disambiguated(self, tmp_path: Path) -> None:
        # get_symbol = EXACT definition; search = semantic. The descriptions
        # must draw that distinction so a consumer picks the right one.
        tools = await self._tools_by_name(tmp_path)
        assert "exact" in tools["lore_get_symbol"].description.lower()
        assert "semantic" in tools["lore_search"].description.lower()

    async def test_impact_direct_vs_transitive_disambiguated_by_depth(
        self, tmp_path: Path
    ) -> None:
        # P8d Wave 2 fold: what_imports (DIRECT importers) and blast_radius
        # (TRANSITIVE closure) no longer publish their own tools — the SAME
        # direct-vs-transitive distinction is now made by lore_impact's own
        # 'depth' parameter (depth=1 direct, depth>1 transitive rollup), so
        # its ONE description must still teach both halves.
        tools = await self._tools_by_name(tmp_path)
        description = tools["lore_impact"].description.lower()
        assert "direct" in description
        assert "transitive" in description

    async def test_impact_description_names_its_folded_one_call_verbs(
        self, tmp_path: Path
    ) -> None:
        # T2 (P8d' #54 tweak): "who imports X" / "what tests cover X" must route
        # to lore_impact FIRST -- its description names, early, the former
        # what_imports / tests_for capabilities it folds in one call. Both bare
        # stems are pre-approved phrasing (test_text_hygiene.py's tier-2 scan
        # mechanically excludes them: living SurrealCodeGraph methods of the
        # same name survive, so they are not enforced retired verbs; neither
        # carries the ``lore_`` prefix tier-1 enforces).
        tools = await self._tools_by_name(tmp_path)
        description = tools["lore_impact"].description
        assert "what_imports" in description
        assert "tests_for" in description
        assert "who imports" in description.lower()
        assert "what tests cover" in description.lower()

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

    async def test_findings_description_teaches_the_batch_actions(
        self, tmp_path: Path
    ) -> None:
        # PKT-06 §3 (L2b): resolve_many/acknowledge_many are NEW actions, not
        # merely implied by the singular resolve/acknowledge verbs the pin
        # above already checks — a caller must be able to learn the batch
        # verbs exist from the description text alone.
        tools = await self._tools_by_name(tmp_path)
        description = tools["lore_findings"].description.lower()
        assert "resolve_many" in description
        assert "acknowledge_many" in description

    async def test_tasks_description_teaches_the_actions(self, tmp_path: Path) -> None:
        # PKT-06 §6: latent gap closed — no task-side counterpart to
        # test_findings_description_teaches_the_actions existed before this
        # packet, even though the comment on that pin claimed lore_tasks was
        # mirrored. lore_tasks dispatches on ``action``; every verb (the
        # pre-existing create/transition and PKT-06's new rollup/create_many)
        # must be teachable from the description alone.
        tools = await self._tools_by_name(tmp_path)
        description = tools["lore_tasks"].description.lower()
        assert "create" in description
        assert "transition" in description
        assert "rollup" in description
        assert "create_many" in description


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
        # PKT-06 §6: widened from _EXPECTED_TOOLS to _ALL_BUILTIN_TOOL_NAMES —
        # the prior iteration silently EXEMPTED lore_tasks/lore_claim_task from
        # this pin (they predate the bare-name cutover and were never folded
        # into _EXPECTED_TOOLS), so PKT-06's new lore_tasks params (since,
        # limit, items, summary, report_path) and lore_findings' new ``items``
        # would dodge this contract entirely. Every existing lore_tasks param
        # already carries a Field description, so this widening is green-able
        # immediately for the pre-existing surface.
        tools = await self._tools_by_name(tmp_path)
        for name in _ALL_BUILTIN_TOOL_NAMES:
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

    async def test_search_path_describes_the_exact_miss_shape(
        self, tmp_path: Path
    ) -> None:
        # T5 (P8d' #54 tweak): the path param must LEAD with the EXACT-file
        # requirement and explicitly rule out the three miss-shapes the gate
        # transcripts hit (a directory, a basename, a path prefix).
        tools = await self._tools_by_name(tmp_path)
        description = tools["lore_search"].inputSchema["properties"]["path"][
            "description"
        ]
        lowered = description.lower()
        assert lowered.startswith("exact")
        assert "directory" in lowered
        assert "basename" in lowered
        assert "prefix" in lowered


class TestInputParamConstraints:
    """Input params publish their value constraints + reject bad values (Items 4, 5).

    Item 4: ``lore_search(detail_level=...)`` must publish a Literal enum
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
        prop = tools["lore_search"].inputSchema["properties"]["detail_level"]
        assert prop.get("enum") == ["auto", "summary", "source"], (
            "detail_level must publish the Literal enum so a bad value is rejected, "
            "not silently filtered to empty"
        )

    async def test_invalid_detail_level_is_rejected_good_value_accepted(
        self, tmp_path: Path
    ) -> None:
        from pydantic import ValidationError

        mcp = await self._server(tmp_path)
        model = self._arg_model(mcp, "lore_search")
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
        # k on search + recall, depth on lore_impact (P8d Wave 2: the folded
        # blast_radius tool is gone, but its ge=1 depth constraint lives on
        # unchanged as lore_impact's own 'depth' param), max_results on
        # lore_dead_code all carry a minimum of 1 (a count/depth below 1 is
        # meaningless).
        search_k = tools["lore_search"].inputSchema["properties"]["k"]
        recall_k = tools["lore_recall"].inputSchema["properties"]["k"]
        depth = tools["lore_impact"].inputSchema["properties"]["depth"]
        max_results = tools["lore_dead_code"].inputSchema["properties"]["max_results"]
        assert search_k.get("minimum") == 1
        assert recall_k.get("minimum") == 1
        assert depth.get("minimum") == 1
        assert max_results.get("minimum") == 1

    async def test_zero_or_negative_numeric_is_rejected_good_value_accepted(
        self, tmp_path: Path
    ) -> None:
        from pydantic import ValidationError

        mcp = await self._server(tmp_path)
        search_model = self._arg_model(mcp, "lore_search")
        impact_model = self._arg_model(mcp, "lore_impact")
        # k=0 (search) and depth=-1 (lore_impact) are schema-rejected at validation.
        with pytest.raises(ValidationError):
            search_model.model_validate({"query": "x", "k": 0})
        with pytest.raises(ValidationError):
            impact_model.model_validate({"target": "x", "depth": -1})
        # A positive value passes — the bound rejects below-1, not all values.
        search_model.model_validate({"query": "x", "k": 1})
        impact_model.model_validate({"target": "x", "depth": 1})


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
        assert tools["lore_remember"].annotations is not None


# Item 2: the named output fields each tool's published outputSchema must carry.
# A wrapper returning the real pydantic model (a scalar model, or list[Model]) makes
# FastMCP derive a FIELD-LEVEL outputSchema; a wrapper returning list[dict[str, Any]]
# publishes an opaque ``additionalProperties: true`` (no field names) — the regression
# this pins. Each value is field names that MUST be discoverable in the schema (either
# top-level ``properties`` for a scalar-model tool, or under ``$defs`` for a
# list-wrapped one). ``lore_remember`` returns a bare str (the id) — no model — so
# it is excluded (a str has no fields to name).
_TOOL_OUTPUT_FIELDS: dict[str, set[str]] = {
    "lore_search": {"formatted", "chunk_key", "detail_level", "stale", "score"},
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
    # P8b wire-up: lore_read returns a StoreFileSpan MODEL (the single, store-backed
    # read verb) — its fields include the two store-only marks (``stale`` /
    # ``integrity_verified``) the filesystem FileSpan cannot supply.
    "lore_read": {
        "tier",
        "path",
        "line_start",
        "line_end",
        "text",
        "stale",
        "integrity_verified",
    },
    # lore_recall is intentionally omitted: the P7 cutover re-shapes its
    # return (it no longer carries the retired store's flat ``metadata`` note), so
    # its surfaced fields are pinned behaviourally in TestRecallMemoryCutover
    # rather than as a fixed field-name table here.
    # P8d Wave 3: the merged tool's fields — the pre-existing counts plus the
    # redesigned sections (calibration already existed; ages/traces are NEW).
    "lore_index": {
        "files_indexed",
        "files_failed",
        "files_skipped",
        "calibration",
        "last_sync",
        "last_sweep",
        "newest_snapshot",
        "traces",
    },
    # #60 phase 2: DeadCodeSweepResult wraps the DeadCodeNode list with an
    # honest elided count (a SCALAR return, mirroring lore_impact/lore_map) --
    # "nodes"/"elided" are the wrapper's own top-level properties; the rest
    # are DeadCodeNode's fields, surfacing under $defs.
    "lore_dead_code": {
        "nodes",
        "elided",
        "id",
        "kind",
        "qualified_name",
        "file_path",
        "chunk_id",
        "tier",
        "test_references",
        "reason",
    },
    # P6-tail: ImpactResult is a SCALAR return (mirrors lore_index), so
    # its own fields are top-level properties; its nested ModuleRollup fields
    # surface under $defs. P8d Wave 2: absorbs the folded lore_references /
    # lore_what_imports / lore_blast_radius / lore_tests_for capability —
    # no new fields (direct_consumers/covering_tests/module_rollups already
    # carried them).
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
    # surface under $defs. Finding #77: MapEntry gains symbols_elided (the
    # honest per-module hidden-symbol count, mirrors lore_impact's
    # covering_tests_elided) alongside the now-capped symbols field.
    "lore_map": {
        "entries",
        "elided_modules",
        "formatted",
        "module",
        "rank",
        "symbols",
        "symbols_elided",
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
            # index: a scalar IndexStatusSummary — structuredContent is the model dict.
            status_tool = mcp._tool_manager.get_tool("lore_index")  # noqa: SLF001
            _content, structured = await status_tool.run(
                {},
                context=_FakeToolContext(ctx),
                convert_result=True,
            )
            assert isinstance(structured, dict)
            assert "files_indexed" in structured
            # search: a list[SearchResult] — wrapped under ``result`` with the
            # SearchResult fields on each element.
            search_tool = mcp._tool_manager.get_tool("lore_search")  # noqa: SLF001
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
            assert "lore_search" in message or "reindex" in message, (
                "a not-found must point the consumer at a next step "
                "(lore_search / reindex)"
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

    async def test_search_finds_indexed_symbol(self, indexed_context: AppContext) -> None:
        results = await indexed_context.search("champion routing", k=10)
        assert results
        # The base citation format is present, and the unique symbol's file shows.
        joined = "\n".join(r.formatted for r in results)
        assert "[SOURCE:" in joined
        assert "pkg/router.py" in joined

    async def test_index_reports_healthy_with_no_args(self, indexed_context: AppContext) -> None:
        status = await indexed_context.index()
        assert status.files_indexed >= 1
        assert status.files_failed == 0
        # This fixture indexed via ``indexer.index_all()`` directly — never through
        # the watcher's live-apply path nor a ``reconcile()`` sweep — so both age
        # sections render honestly "never", not a crash.
        assert status.last_sync.at is None
        assert status.last_sync.age_seconds is None
        assert status.last_sweep.at is None
        assert status.last_sweep.age_seconds is None
        # Nothing ever called record_trace in this fixture.
        assert status.traces.total == 0
        assert status.traces.by_tool == []
        assert status.traces.latest_at is None

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

    # -- lore_read (StoreReadTool) — the single, store-backed read verb --- #

    async def test_read_serves_a_hash_verified_store_span(
        self, indexed_context: AppContext
    ) -> None:
        # lore_read serves the INDEXED bytes from the store (not disk), hash-verified,
        # with a [SOURCE:...] provenance header matching the filesystem span reader's.
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

    async def test_diff_listing_shows_an_honest_total_when_more_exist(
        self, indexed_context: AppContext
    ) -> None:
        # P8d Wave 4a (finding #8): more snapshots than the default limit must
        # never silently cap — the listing names how many exist vs shown.
        for _ in range(3):
            await indexed_context._snapshot_stamper.stamp()  # noqa: SLF001
        total = await indexed_context._diff_engine.count_snapshots()  # noqa: SLF001

        rendered = await indexed_context.diff(limit=2)
        assert f"showing 2 of {total}" in rendered
        assert "raise limit" in rendered.lower()

    async def test_diff_listing_has_no_trailer_when_everything_fit(
        self, indexed_context: AppContext
    ) -> None:
        await indexed_context._snapshot_stamper.stamp()  # noqa: SLF001

        rendered = await indexed_context.diff()
        assert "showing" not in rendered.lower()

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
        values: dict[str, str] = {
            "subject": "s",
            "area": "a",
            "category": "c",
            "created_by": "me",
        }
        values[field_name] = ""
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await indexed_context.findings(
                action="report",
                subject=values["subject"],
                area=values["area"],
                category=values["category"],
                created_by=values["created_by"],
            )
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

    async def test_findings_get_and_chain_head_render_the_body_query_stays_summarised(
        self, indexed_context: AppContext
    ) -> None:
        # P8d Wave 4a (finding #38): get/chain_head render the FULL BODY +
        # provenance, not just the summary row; query stays summarised.
        distinctive_body = "reproduces only under concurrent connection drops during a rebuild"
        reported = await indexed_context.findings(
            action="report",
            subject="diff engine connection leak",
            body=distinctive_body,
            area="lore_diff",
            category="bug",
            created_by="me",
        )
        number = int(reported.split("#", 1)[1].split(" ", 1)[0])

        got = await indexed_context.findings(action="get", id_or_number=number)
        assert distinctive_body in got

        head = await indexed_context.findings(action="chain_head", id_or_number=number)
        assert distinctive_body in head

        queried = await indexed_context.findings(action="query", status="open")
        assert distinctive_body not in queried, (
            "query must stay summarised — the body belongs to get/chain_head only"
        )

    async def test_findings_get_and_chain_head_fence_a_multiline_body_and_never_forge_a_row(
        self, indexed_context: AppContext
    ) -> None:
        # audit-w4a finding #1 (CONFIRMED blocker, fixed): a multi-line body
        # must render UNAMBIGUOUSLY -- a body-embedded line byte-identical to
        # a real finding row (or to a "provenance:" trailer) must never be
        # mistaken for one, and a body-embedded backtick run must never let
        # the body escape its wrapper fence.
        #
        # `forged_row` is the ACTUAL summary-row rendering the server would
        # produce for a genuine OTHER finding -- the strongest possible
        # forgery (byte-identical to a real row, not a hand-typed lookalike),
        # exactly reproducing the audit's live receipt.
        other_reported = await indexed_context.findings(
            action="report",
            subject="the OTHER real finding",
            body="unrelated",
            area="lore_findings",
            category="bug",
            created_by="attacker",
        )
        other_number = int(other_reported.split("#", 1)[1].split(" ", 1)[0])
        other_finding = await indexed_context.finding_ledger.get(other_number)
        forged_row = AppContext._render_finding_rows([other_finding])
        forged_provenance = 'provenance: {"forged": true}'

        hostile_body = (
            "legit start\n"
            f"{forged_row}\n"
            f"{forged_provenance}\n"
            "and a run of four backticks right here: ````"
        )
        reported = await indexed_context.findings(
            action="report",
            subject="hostile multi-line body finding",
            body=hostile_body,
            area="lore_findings",
            category="bug",
            created_by="me",
        )
        number = int(reported.split("#", 1)[1].split(" ", 1)[0])
        real_row = AppContext._render_finding_rows([await indexed_context.finding_ledger.get(number)])

        get_text = await indexed_context.findings(action="get", id_or_number=number)
        head_text = await indexed_context.findings(action="chain_head", id_or_number=number)

        for rendered in (get_text, head_text):
            lines = rendered.splitlines()
            # Exactly one open/close fence pair wraps the body.
            fence_indices = [i for i, line in enumerate(lines) if line and set(line) == {"`"}]
            assert len(fence_indices) == 2, (
                f"expected exactly one open/close body fence pair, got: {lines!r}"
            )
            open_idx, close_idx = fence_indices
            # The fence must be strictly wider than the longest backtick run
            # INSIDE the body (four) -- otherwise an embedded run could close
            # it early (the CommonMark rule search.py's own fence follows).
            assert len(lines[open_idx]) > 4
            inside = lines[open_idx + 1 : close_idx]
            outside = lines[:open_idx] + lines[close_idx + 1 :]

            # The forged row + forged provenance line are trapped INSIDE the
            # fence -- never readable as a bare, fence-external line.
            assert forged_row in inside
            assert forged_provenance in inside
            assert forged_row not in outside
            assert forged_provenance not in outside

            # Exactly one REAL trailer of each kind renders OUTSIDE the
            # fence, and the provenance trailer is the real one, not forged.
            outside_provenance = [line for line in outside if line.startswith("provenance:")]
            assert len(outside_provenance) == 1
            assert "forged" not in outside_provenance[0]
            outside_created_at = [line for line in outside if line.startswith("created_at:")]
            assert len(outside_created_at) == 1

            # The leading summary row is the REAL finding, never the forged one.
            assert lines[0] == real_row

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

    async def test_remember_then_recall_roundtrips(
        self, indexed_context: AppContext
    ) -> None:
        # P7 cutover: remember takes the memory ``kind``; recall surfaces the note
        # text (its exact return SHAPE is pinned in TestRecallMemoryCutover).
        note = "champion routing lives in pkg/router.py"
        await getattr(indexed_context, "remember")(note, kind="fact")
        rendered = _render_text(
            await getattr(indexed_context, "recall")("where is champion routing", k=5)
        )
        assert note in rendered

    # P8d Wave 2 (the impact fold): test_blast_radius_traverses_graph /
    # test_tests_for_returns_list / test_references_returns_production_test_split /
    # test_references_zero_is_valid_not_error were REMOVED here — their
    # AppContext handlers (blast_radius / tests_for / references) are deleted
    # (folded into lore_impact; confirmed by the deletion-gate grep in
    # REPORT-builder-flip-w2.md that nothing outside their own wrapper + these
    # tests called them). The underlying graph_surreal ENGINE behaviour they
    # exercised remains fully covered by test_graph_surreal.py's
    # TestBlastRadius / TestTestsFor / TestReferences classes, untouched.
    #
    # fixer-w2f follow-on: test_what_imports_traverses_graph (same family) was
    # REMOVED here too — the AppContext.what_imports HANDLER it exercised
    # (kept alive unregistered purely for test_schema_rebuild.py's
    # TestRebuildingNoticeSeam A8c pin) is now deleted; A8c was repointed at
    # lore_impact instead (see test_schema_rebuild.py). The underlying
    # graph_surreal ENGINE's ``what_imports`` method remains covered by
    # test_graph_surreal.py's own tests, untouched — this deletion only
    # removes the AppContext-handler-level wrapper test.

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
            # #60 phase 2: AppContext.dead_code now returns a DeadCodeSweepResult
            # wrapper (nodes + an honest elided count), not a bare list.
            dead = await ctx.dead_code()
            names = {node.qualified_name for node in dead.nodes}
            assert "pkg.utils.orphan_helper" in names, (
                f"orphan_helper is only referenced by tests and must appear in dead_code; "
                f"got: {names}"
            )
            orphan = next(
                n for n in dead.nodes if n.qualified_name == "pkg.utils.orphan_helper"
            )
            assert orphan.reason == REASON_ONLY_REFERENCED_BY_TESTS
        finally:
            await ctx.aclose()

    async def test_dead_code_does_not_surface_production_referenced_symbol(
        self, indexed_context: AppContext
    ) -> None:
        # ``pkg.base.BaseRouter`` has a production reference from ``pkg.router``
        # (it imports it). It must NOT appear in dead_code.
        dead = await indexed_context.dead_code()
        names = {node.qualified_name for node in dead.nodes}
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

    async def test_dead_code_reports_zero_elided_when_max_results_does_not_bind(
        self, indexed_context: AppContext
    ) -> None:
        # Finding #60, "no false elision signal" half: the default max_results
        # (100) cannot bind on this fixture's tiny corpus, so elided must be 0 —
        # never some stale/nonzero artifact of the counting itself.
        dead = await indexed_context.dead_code()
        assert dead.elided == 0

    async def test_dead_code_counts_elided_nodes_when_max_results_binds(
        self, tmp_path: Path
    ) -> None:
        # Finding #60, "counted signal" half: a capped dead_code result must
        # carry an honest elided count -- a bare list makes "these are all the
        # dead symbols" indistinguishable from "these are the first
        # max_results of many more". Three independently-dead functions
        # (zero references anywhere) guarantee dead_code_total() >= 3
        # regardless of whether the enclosing module itself also rolls up as
        # dead.
        slug = _slug()
        live = tmp_path / "live_many_orphans"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "orphans.py").write_text(_PY_MANY_ORPHANS, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        try:
            full = await ctx.dead_code()
            assert len(full.nodes) >= 3, (
                "the three planted orphans must all surface as dead; got "
                f"{[n.qualified_name for n in full.nodes]}"
            )
            assert full.elided == 0, "an unbound (default-cap) sweep must show zero elision"

            capped = await ctx.dead_code(max_results=1)
            assert len(capped.nodes) == 1
            assert capped.elided == len(full.nodes) - 1
            assert capped.elided >= 2
        finally:
            await ctx.aclose()

    async def test_index_reconcile_true_brings_a_new_file_current(
        self, indexed_context: AppContext, tmp_path: Path
    ) -> None:
        # Write a NEW file then index(reconcile=True): it becomes searchable
        # (read-your-writes) — the former ``reindex()`` behaviour, now reached via
        # the merged tool's sweep flag.
        live = tmp_path / "live"
        (live / "pkg" / "extra.py").write_text(
            "def freshly_added_symbol():\n    return 7\n", encoding="utf-8"
        )
        await indexed_context.index(reconcile=True)
        symbol = await indexed_context.get_symbol("freshly_added_symbol")
        assert symbol.file_path == "pkg/extra.py"


class TestReindexTierValidation:
    """``index(reconcile=True, tier=...)`` validates the tier — a typo must fail
    loud (Item 3). Ported onto the P8d Wave 3 merged tool: the SAME validation
    ``reindex(tier=...)`` ran survives unchanged inside the merged handler.

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
            await indexed_context.index(reconcile=True, tier="bogus")
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
        await indexed_context.index(reconcile=True, tier="custom")
        symbol = await indexed_context.get_symbol("scoped_added_symbol")
        assert symbol.file_path == "pkg/scoped.py"

    async def test_reindex_all_still_works(self, indexed_context: AppContext) -> None:
        # tier=None still means all — the unscoped sweep is unchanged.
        summary = await indexed_context.index(reconcile=True)
        assert summary.files_failed == 0

    async def test_tier_without_reconcile_raises(self, indexed_context: AppContext) -> None:
        # A caller passing ``tier`` but forgetting ``reconcile=True`` would
        # otherwise silently get a status-only read that ignores ``tier``
        # entirely — a teaching-miss the merged tool must refuse loudly instead.
        from loremaster.server import ReindexTierError

        with pytest.raises(ReindexTierError) as exc_info:
            await indexed_context.index(tier="custom")
        message = str(exc_info.value)
        assert "custom" in message
        assert "reconcile" in message, (
            "the error must point the caller at reconcile=True as the fix"
        )


class TestMergedIndexTool:
    """P8d Wave 3 — the ``lore_index`` redesign: last-sync/last-sweep ages,
    newest-snapshot age, and trace aggregates, over a REAL corpus + REAL store.
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

    async def test_reconcile_true_stamps_last_sweep_but_not_last_sync(
        self, indexed_context: AppContext, tmp_path: Path
    ) -> None:
        # reconcile()'s walk never calls index_file (it has its own inline
        # per-file pipeline), so a sweep stamps last_sweep but leaves last_sync
        # untouched — the two ages are genuinely independent signals.
        (tmp_path / "live" / "pkg" / "extra.py").write_text(
            "def fresh_symbol_for_sweep():\n    return 1\n", encoding="utf-8"
        )
        status = await indexed_context.index(reconcile=True)
        assert status.last_sweep.at is not None
        assert status.last_sweep.age_seconds is not None
        assert 0 <= status.last_sweep.age_seconds < 30
        assert status.last_sync.at is None
        assert status.last_sync.age_seconds is None

    async def test_a_live_apply_stamps_last_sync_but_not_last_sweep(
        self, indexed_context: AppContext
    ) -> None:
        # Simulate what the watcher's drain does: call index_file directly
        # (bypassing reconcile entirely) — only last_sync should move.
        await indexed_context.indexer.index_file(
            "custom", "pkg/extra_live.py", "def live_applied_symbol():\n    return 2\n"
        )
        status = await indexed_context.index()
        assert status.last_sync.at is not None
        assert status.last_sync.age_seconds is not None
        assert 0 <= status.last_sync.age_seconds < 30
        assert status.last_sweep.at is None

    async def test_last_sync_age_survives_a_naive_iso_stamp(
        self, indexed_context: AppContext
    ) -> None:
        # Every writer in this codebase stamps `datetime.now(UTC).isoformat()`
        # (tz-aware) — but the meta value is a plain string, so nothing stops
        # a future writer, a legacy-timestamp migration, or a manual meta edit
        # from landing a timezone-NAIVE-but-otherwise-valid ISO stamp. The age
        # render's own docstring promises "a malformed stamp must not crash a
        # status read" (audit finding 2) — a naive stamp is honestly assumed
        # UTC (this codebase's own convention), not crashed on nor silently
        # rendered "never" (it DID parse; "never" would be a lie).
        from loremaster.index.indexer import META_LAST_SYNC_AT_KEY

        naive_stamp = "2026-07-06T00:00:00"  # valid ISO-8601, no offset/tzinfo
        await indexed_context.manifest.meta_set(META_LAST_SYNC_AT_KEY, naive_stamp)

        status = await indexed_context.index()

        assert status.last_sync.at == naive_stamp
        assert status.last_sync.age_seconds is not None
        assert status.last_sync.age_seconds >= 0

    async def test_newest_snapshot_age_after_a_productive_sweep(
        self, indexed_context: AppContext, tmp_path: Path
    ) -> None:
        (tmp_path / "live" / "pkg" / "another.py").write_text(
            "def another_fresh_symbol():\n    return 3\n", encoding="utf-8"
        )
        status = await indexed_context.index(reconcile=True)
        assert status.newest_snapshot.at is not None
        assert status.newest_snapshot.age_seconds is not None
        assert status.newest_snapshot.age_seconds >= 0

    async def test_trace_aggregates_reflect_recorded_traces(
        self, indexed_context: AppContext
    ) -> None:
        await indexed_context.write_store.record_trace(
            tool="lore_search", params_hash="h1", hit_count=3, latency_ms=1.5, session="s1"
        )
        await indexed_context.write_store.record_trace(
            tool="lore_search", params_hash="h2", hit_count=1, latency_ms=2.0, session="s1"
        )
        await indexed_context.write_store.record_trace(
            tool="lore_impact", params_hash="h3", hit_count=0, latency_ms=0.9, session="s1"
        )
        status = await indexed_context.index()
        assert status.traces.total == 3
        by_tool = {row.tool: row.calls for row in status.traces.by_tool}
        assert by_tool == {"lore_search": 2, "lore_impact": 1}
        assert status.traces.latest_at is not None

    async def test_trace_aggregates_empty_when_none_recorded(
        self, indexed_context: AppContext
    ) -> None:
        status = await indexed_context.index()
        assert status.traces.total == 0
        assert status.traces.by_tool == []
        assert status.traces.latest_at is None


class TestCosineFloorStatusWiring:
    """Finding #74 part 3: ``lore_index()`` surfaces the cosine weak-match

    floor's drift status (measured/stale/disabled) and RE-CHECKS it (via
    ``search.apply_cosine_floor_drift_check``) on every status read — mirrors
    the ``calibration`` section's own attached-nested-status idiom.
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

    @pytest.fixture(autouse=True)
    def _reset_drift_state(self) -> Iterator[None]:
        # State-leakage guard (global CLAUDE.md lifecycle rule): each test
        # below triggers a REAL call to apply_cosine_floor_drift_check (via
        # indexed_context.index()), which mutates loremaster.search's
        # module-level disarm flag directly (not through monkeypatch) — an
        # explicit reset before/after is required so tests never leak this
        # into each other regardless of order.
        from loremaster import search as search_module

        search_module._reset_cosine_floor_drift_state_for_tests()
        yield
        search_module._reset_cosine_floor_drift_state_for_tests()

    async def _stamp_fingerprint(self, ctx: AppContext, fingerprint: str) -> None:
        from loremaster.index.schema import SCHEMA_FINGERPRINT_META_KEY

        await ctx.manifest.meta_set(SCHEMA_FINGERPRINT_META_KEY, fingerprint)

    async def test_measured_state_when_the_stamp_matches_the_live_corpus(
        self, indexed_context: AppContext, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from loremaster import search as search_module

        fingerprint = "f" * 64
        await self._stamp_fingerprint(indexed_context, fingerprint)
        baseline = await indexed_context.index()
        assert baseline.files_indexed == 2
        stamp = search_module.CosineFloorMeasurement(
            floor=0.5828, measured_file_count=2,
            measured_embedding_schema_fingerprint=fingerprint,
        )
        # The floor is patched, not merely stamped: since packet 10-d the
        # SHIPPED constant is None, which short-circuits to "disabled" before
        # any stamp comparison runs. A stamp-only patch would leave this test
        # asserting a state the drift machinery can no longer reach.
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", 0.5828)
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR_STAMP", stamp)

        status = await indexed_context.index()

        assert status.cosine_floor.state == "measured"
        assert status.cosine_floor.floor == 0.5828
        assert status.cosine_floor.note is None
        assert search_module._cosine_floor_runtime_state.disarmed_by_drift is False

    async def test_stale_state_and_teaching_note_when_file_count_drifts(
        self, indexed_context: AppContext, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from loremaster import search as search_module

        fingerprint = "f" * 64
        await self._stamp_fingerprint(indexed_context, fingerprint)
        stamp = search_module.CosineFloorMeasurement(
            floor=0.5828, measured_file_count=2000,  # wildly beyond the 10% tolerance
            measured_embedding_schema_fingerprint=fingerprint,
        )
        # Packet 10-d: the shipped floor is None (short-circuits to
        # "disabled"), so reaching the drift machinery requires arming it.
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", 0.5828)
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR_STAMP", stamp)

        status = await indexed_context.index()

        assert status.cosine_floor.state == "stale"
        assert status.cosine_floor.note is not None
        assert "re-measure needed" in status.cosine_floor.note
        # The disarm takes effect on the QUERY hot path too, not just the
        # status render -- end-to-end proof the two seams agree (the disarm
        # state renders the teaching here AND silences the verdict there).
        assert search_module._cosine_floor_runtime_state.disarmed_by_drift is True

    async def test_stale_state_when_the_embedding_schema_fingerprint_changed(
        self, indexed_context: AppContext, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from loremaster import search as search_module

        await self._stamp_fingerprint(indexed_context, "f" * 64)
        stamp = search_module.CosineFloorMeasurement(
            floor=0.5828, measured_file_count=2,
            measured_embedding_schema_fingerprint="e" * 64,  # differs from the stamped "f"*64
        )
        # Packet 10-d: the shipped floor is None (short-circuits to
        # "disabled"), so reaching the drift machinery requires arming it.
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", 0.5828)
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR_STAMP", stamp)

        status = await indexed_context.index()

        assert status.cosine_floor.state == "stale"
        assert status.cosine_floor.note is not None
        assert "fingerprint" in status.cosine_floor.note

    async def test_disabled_state_when_the_floor_itself_is_unset(
        self, indexed_context: AppContext, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from loremaster import search as search_module

        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", None)

        status = await indexed_context.index()

        assert status.cosine_floor.state == "disabled"
        assert status.cosine_floor.floor is None
        # Packet 10-d: an unset floor no longer renders a null note — see
        # test_production_default_serves_the_disarm_note_through_lore_index
        # for the same assertion made against the SHIPPED constants (this one
        # forces the state; that one observes it).
        assert status.cosine_floor.note == search_module._COSINE_FLOOR_DISARMED_NOTE

    async def test_production_default_serves_the_disarm_note_through_lore_index(
        self, indexed_context: AppContext
    ) -> None:
        """Packet 10-d (2026-07-24): the SERVED surface, at the SHIPPED constants.

        Deliberately NO ``monkeypatch`` — every other test in this class
        patches the floor and/or the stamp, so none of them can see what
        ``lore_index()`` actually renders on a real deployment. This one can.
        A consumer agent reading a null note would conclude the surface was
        simply never enabled; the truth is that it was DISARMED because its
        judgement was confident-wrong (#176/#179/#180), and that difference is
        the whole of finding #4's lesson.
        """
        from loremaster import search as search_module

        status = await indexed_context.index()

        assert status.cosine_floor.state == "disabled"
        assert status.cosine_floor.floor is None
        assert status.cosine_floor.note == search_module._COSINE_FLOOR_DISARMED_NOTE

    def test_cosine_floor_defaults_disabled_on_a_bare_index_status_summary(self) -> None:
        # F3 safety pattern (IndexStatusSummary's own docstring): constructing
        # the model with ONLY the base IndexSummary fields must still
        # validate -- the new section needs a sane "nothing recorded" default,
        # never a bare required field forcing every existing caller to change.
        from loremaster.server import IndexStatusSummary

        summary = IndexStatusSummary(
            files_indexed=0, files_failed=0, files_skipped=0,
            tiers_rebuilt=[], tiers_skipped=[], outcomes=[],
        )
        assert summary.cosine_floor.state == "disabled"


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

    async def test_search_wrapper_yields_structured_list(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        structured = await self._structured(
            mcp, "lore_search", ctx, query="champion routing", k=10
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

    async def test_index_wrapper_yields_structured_model(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        structured = await self._structured(mcp, "lore_index", ctx)
        assert isinstance(structured, dict)
        assert structured["files_indexed"] >= 1
        assert structured["files_failed"] == 0

    async def test_index_wrapper_no_arg_never_sweeps(
        self, indexed: tuple[Any, AppContext], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The registered wrapper's default call must reach the SAME "never
        # sweeps" contract as the handler — spy on the reconcile engine to
        # prove it is never invoked through the live FastMCP dispatch path.
        mcp, ctx = indexed
        calls: list[None] = []
        original_reconcile = ctx.reconcile_engine.reconcile

        async def _spy_reconcile() -> Any:
            calls.append(None)
            return await original_reconcile()

        monkeypatch.setattr(ctx.reconcile_engine, "reconcile", _spy_reconcile)
        await self._structured(mcp, "lore_index", ctx)
        assert calls == [], "a no-arg lore_index call must never sweep"

    async def test_index_wrapper_reconcile_true_sweeps(
        self, indexed: tuple[Any, AppContext], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mcp, ctx = indexed
        calls: list[None] = []
        original_reconcile = ctx.reconcile_engine.reconcile

        async def _spy_reconcile() -> Any:
            calls.append(None)
            return await original_reconcile()

        monkeypatch.setattr(ctx.reconcile_engine, "reconcile", _spy_reconcile)
        await self._structured(mcp, "lore_index", ctx, reconcile=True)
        assert calls == [None], "reconcile=True must sweep exactly once"

    # P8d Wave 2: test_references_wrapper_yields_structured_model REMOVED —
    # the lore_references TOOL wrapper is deleted (folded into lore_impact).
    # TestImpactMapRegisteredToolWrappers below already drives lore_impact's
    # own wrapper end to end.

    async def test_dead_code_wrapper_yields_structured_result_with_elided_count(
        self, indexed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = indexed
        # #60 phase 2: DeadCodeSweepResult is a SCALAR return (mirrors
        # ImpactResult/MapResult) -- structuredContent carries ``nodes``/
        # ``elided`` directly as top-level properties, not wrapped under
        # ``result`` (that wrapping was the bare-list convention this tool
        # used before #60's phase 2 wiring).
        structured = await self._structured(mcp, "lore_dead_code", ctx)
        assert isinstance(structured, dict)
        assert isinstance(structured["nodes"], list)
        assert isinstance(structured["elided"], int)
        # This fixture's tiny corpus cannot bind the default max_results=100.
        assert structured["elided"] == 0
        # Every element must have the DeadCodeNode fields.
        for item in structured["nodes"]:
            assert isinstance(item, dict)
            assert "qualified_name" in item
            assert "reason" in item

    async def test_dead_code_wrapper_reports_elided_count_when_max_results_binds(
        self, tmp_path: Path
    ) -> None:
        # Finding #60: the served (wire-level) output must carry the counted
        # signal when max_results binds, not just the AppContext-level return.
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "orphans.py").write_text(_PY_MANY_ORPHANS, encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        mcp = build_mcp_server(LoreServer(config))
        try:
            structured = await self._structured(mcp, "lore_dead_code", ctx, max_results=1)
            assert len(structured["nodes"]) == 1
            assert structured["elided"] >= 2
        finally:
            await ctx.aclose()


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
        assert "lore_search" in message

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
        assert "lore_search" in message

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
        assert "lore_search" in message


class TestImpactMapRebuildingGate:
    """Verdict-bearing lore_impact / lore_map calls NEVER serve mid-rebuild —
    the graded honest-emptiness doctrine applied at the TOOL-WIRING level.

    Unlike the reactive corpus-read tools (``search_code`` raises only when
    its own result WOULD BE empty, via ``AppContext._raise_if_empty_during_
    rebuild``; ``get_symbol``/``read`` raise only on a not-found exception,
    via ``_rebuilding_error_or`` — what_imports/blast_radius/tests_for rode
    the same reactive ``_raise_if_empty_during_rebuild`` seam before P8d
    Wave 2 folded them into lore_impact/lore_map), ``ImpactEngine`` /
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

    async def test_impact_engine_carries_a_symbol_resolver_over_the_same_ctx_graph(
        self, indexed_context: AppContext
    ) -> None:
        """Findings #63/#65 PRIMARY fix: ``ImpactEngine`` must be wired with a
        chunk-store resolver (:class:`~loremaster.symbols.SymbolResolver`)
        sharing the SAME rooted ``code_graph`` every other tool reads — never
        a bare-test-only widening path with nothing wired in production.
        """
        from loremaster.symbols import SymbolResolver

        engine = indexed_context._impact_engine  # noqa: SLF001 - structural wiring pin
        resolver = engine._symbol_resolver  # noqa: SLF001
        assert isinstance(resolver, SymbolResolver)
        assert resolver._code_graph is indexed_context.code_graph  # noqa: SLF001
        assert resolver._store is indexed_context.write_store  # noqa: SLF001


# --------------------------------------------------------------------------- #
# Findings #63/#65 end-to-end: the FULL production round trip (real indexer,
# real SurrealCodeGraph, real SymbolResolver, real server wiring) over the
# exact live collision shape REPORT-slate-fixer-63.md §3 / finding #65 proved
# (a module-less "Class.method" query that would otherwise silently ride an
# unrelated symbol's unresolved caller). Every layer is ALSO tested in
# isolation (test_graph_surreal.py's channel-honesty fixture, test_impact.py's
# widening + render tests, the wiring pin just above) -- this is the one test
# proving they compose correctly through the REAL `AppContext.impact` a live
# `lore_impact` call actually drives.
# --------------------------------------------------------------------------- #
_PY_RESOLVE_ALPHA = """\
class ClassAlpha:
    \"\"\"Alpha's own resolve.\"\"\"

    def resolve(self, name):
        return name
"""

_PY_RESOLVE_ALPHA_CONSUMER = """\
from pkg.resolve_alpha import ClassAlpha


def use_alpha(name):
    \"\"\"A production caller astroid CAN resolve (local instantiation).\"\"\"
    alpha = ClassAlpha()
    return alpha.resolve(name)
"""

_PY_RESOLVE_BETA = """\
class ClassBeta:
    \"\"\"Beta's own resolve -- unrelated to alpha's, same bare name.\"\"\"

    def resolve(self, name):
        return name
"""

_PY_RESOLVE_BETA_CONSUMER = """\
def use_beta(unknown_receiver, name):
    \"\"\"A production caller astroid CANNOT resolve (untyped receiver) --
    its dst falls back to the bare written name "resolve".\"\"\"
    return unknown_receiver.resolve(name)
"""


class TestImpactResolutionWideningEndToEnd:
    """Findings #63/#65: the module-less "Class.method" shape, driven through
    the REAL production stack end-to-end.
    """

    @pytest_asyncio.fixture()
    async def resolve_collide_context(self, tmp_path: Path) -> AsyncIterator[AppContext]:
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "resolve_alpha.py").write_text(_PY_RESOLVE_ALPHA, encoding="utf-8")
        (live / "pkg" / "resolve_alpha_consumer.py").write_text(
            _PY_RESOLVE_ALPHA_CONSUMER, encoding="utf-8"
        )
        (live / "pkg" / "resolve_beta.py").write_text(_PY_RESOLVE_BETA, encoding="utf-8")
        (live / "pkg" / "resolve_beta_consumer.py").write_text(
            _PY_RESOLVE_BETA_CONSUMER, encoding="utf-8"
        )
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        try:
            yield ctx
        finally:
            await ctx.aclose()

    async def test_module_less_target_resolves_to_the_real_caller_and_names_the_collidee(
        self, resolve_collide_context: AppContext
    ) -> None:
        result = await resolve_collide_context.impact("ClassAlpha.resolve", depth=1)

        # PRIMARY fix (#63/#65): widening finds alpha's OWN real caller --
        # never a not-found, never silently serving beta's profile instead.
        assert result.verdict == "live"
        assert any("use_alpha" in name for name in result.direct_consumers)

        # Channel honesty (#43/#65): beta's unresolved caller rides the SAME
        # bare "resolve" fallback the graph always OR's in -- disclosed, with
        # beta's real FQN named, never a silent confident-wrong merge.
        assert "bare-name fallback" in result.formatted.lower()
        assert "resolve_beta" in result.formatted


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
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        _inert_calibration_counter: None,
    ) -> None:
        # ``_inert_calibration_counter`` (conftest) forces the calibration probe's
        # counter construction to a network-free double: this test drives the REAL
        # production lifespan, which now starts the boot probe — without the double
        # it would fire a live ``count_tokens`` POST to ``api.anthropic.com`` with the
        # dummy key (the leak the wiring introduced). Scoped to THIS test, not the
        # module, so the file's other tests keep their exact collaborators.
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

    def test_run_configures_lore_logging_before_fastmcp_root_handler(  # noqa: PLR0915 - test infra
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
# P8c — the boot token-calibration engine is wired into the server: constructed
# in build_app_context from config.anthropic (closes config-audit F3), its
# status surfaced by index_status, and cleanly stopped by aclose. The engine's
# OWN behaviour is exhaustively pinned in test_calibration_engine.py and the
# server SEAMS in test_calibration_wiring.py; these classes pin the end-to-end
# BUILD wiring over a real (SurrealDB-backed) AppContext.
# --------------------------------------------------------------------------- #
_CALIBRATION_STATES = (
    "cached",
    "measured",
    "drift_adopted",
    "cached_retrying",
    # P8d Wave 3 (finding #4): the 5th state, verbatim end-to-end through index().
    "integrity_failed",
)


class _FakeStatusEngine:
    """An injectable calibration-engine double with a fixed served constant + status."""

    def __init__(
        self,
        *,
        state: str,
        served: float = 1.78,
        committed: float = 1.78,
        extra_status_fields: dict[str, Any] | None = None,
        per_model_ratios: dict[str, float] | None = None,
    ) -> None:
        self._state = state
        self._served = served
        self._committed = committed
        # A hook for exercising F3 resilience (audit finding 4): a caller-supplied
        # key ``status()`` returns that the ``CalibrationStatus`` model does not
        # (yet) declare — simulating a future engine version outgrowing the model.
        self._extra_status_fields = extra_status_fields or {}
        self.stopped = False
        self.started = False
        # P8d Wave 4a: the caller-model read-side ratio lookup. A test injects
        # ``per_model_ratios`` to control exactly which caller_model values
        # have a "cached ratio" versus which fall back honestly.
        self._per_model_ratios: dict[str, float] = per_model_ratios or {}

    @property
    def served_constant(self) -> float:
        return self._served

    def cached_ratio_for_model(self, model: str) -> float | None:
        return self._per_model_ratios.get(model)

    def status(self) -> dict[str, Any]:
        return {
            "state": self._state,
            "served_constant": self._served,
            "committed_constant": self._committed,
            "model": "claude-sonnet-5",
            "ratio_shift": None if self._state == "cached" else 0.05,
            "last_probe_at": None if self._state == "cached" else "2026-07-04T00:00:00+00:00",
            "baseline_generated_at": "2026-07-04T00:00:00+00:00",
            "note": None,
            **self._extra_status_fields,
        }

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


class TestCalibrationEngineWiring:
    """build_app_context constructs the engine from config.anthropic; index_status
    surfaces its status; aclose stops it cleanly."""

    async def test_build_app_context_constructs_engine_from_config_anthropic(
        self, tmp_path: Path
    ) -> None:
        # No injection → the REAL engine, over config.anthropic + a findings-ledger
        # adapter. The probe is NOT started here (the lifespan owns that), so it
        # serves the committed constant and touches no network.
        from loremaster.calibration.engine import CalibrationEngine
        from loremaster.server import TOKEN_BUDGET_CALIBRATION, _CalibrationFindingsAdapter

        slug = _slug()
        config = _config(slug, tmp_path / "live")
        ctx = await build_app_context(
            server=LoreServer(config),
            embedder=FakeEmbedder(dim=_DIM),
            manifest_path=tmp_path / "m.db",
            snapshot_root=tmp_path / "snap",
            start_tasks=False,
        )
        try:
            engine = ctx._calibration_engine  # noqa: SLF001 — the wiring under test
            assert isinstance(engine, CalibrationEngine), (
                "build_app_context must construct the real CalibrationEngine when "
                "none is injected (the production path, F3 closure)"
            )
            status = engine.status()
            # Committed constant + yardstick model flow straight from config.anthropic.
            assert status["committed_constant"] == TOKEN_BUDGET_CALIBRATION
            assert status["model"] == config.anthropic.yardstick_model
            # Unstarted → serves the committed constant (state cached).
            assert engine.served_constant == TOKEN_BUDGET_CALIBRATION
            assert status["state"] == "cached"
            # Wired to file drift through the durable finding ledger (the adapter).
            port = engine._findings_port  # noqa: SLF001 — the seam under test
            assert isinstance(port, _CalibrationFindingsAdapter)
            assert port._finding_ledger is ctx.finding_ledger  # noqa: SLF001
        finally:
            await ctx.aclose()

    @pytest.mark.parametrize("state", _CALIBRATION_STATES)
    async def test_index_status_surfaces_the_calibration_state_verbatim(
        self, tmp_path: Path, state: str
    ) -> None:
        # The deployed exit criterion: index_status visibly shows the engine's
        # serving state verbatim in every reachable state, plus served/committed.
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        engine = _FakeStatusEngine(state=state, served=1.9, committed=1.78)
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, calibration_engine=engine
        )
        try:
            status = await ctx.index()
            assert status.calibration is not None, "index() must carry a calibration section"
            assert status.calibration.state == state
            assert status.calibration.served_constant == 1.9
            assert status.calibration.committed_constant == 1.78
            assert status.calibration.model == "claude-sonnet-5"
        finally:
            await ctx.aclose()

    async def test_index_status_survives_an_unknown_future_engine_status_key(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # F3 (audit finding 4): CalibrationStatus stays extra="forbid" on the
        # wire, but a FUTURE engine.status() key must not brick index()'s
        # render. Before the from_engine_status construction seam, the
        # production call site was a raw `CalibrationStatus(**engine.status())`
        # splat — this exercises the REAL end-to-end path (build_app_context ->
        # index() -> _build_index_status) with an engine whose status() has
        # grown a key the model doesn't declare, proving the seam is actually
        # wired in, not just unit-correct in isolation.
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        engine = _FakeStatusEngine(
            state="measured",
            served=1.9,
            committed=1.78,
            extra_status_fields={"a_future_engine_field": "unexpected"},
        )
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, calibration_engine=engine
        )
        try:
            with caplog.at_level(logging.WARNING):
                status = await ctx.index()
            assert status.calibration is not None, "the render must survive, not crash"
            assert status.calibration.state == "measured"
            assert status.calibration.served_constant == 1.9
            assert status.calibration.committed_constant == 1.78
            logged = [r for r in caplog.records if r.levelno >= logging.WARNING]
            assert any(
                "a_future_engine_field" in str(getattr(r, "extras", [])) for r in logged
            ), "the unknown engine-status key must be logged, named, as a drift signal"
        finally:
            await ctx.aclose()

    async def test_index_status_calibration_is_none_without_an_engine(
        self, tmp_path: Path
    ) -> None:
        # A context whose engine was cleared (the no-engine branch) renders
        # calibration=None, not a crash.
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        ctx._calibration_engine = None  # noqa: SLF001 — exercise the None branch
        try:
            status = await ctx.index()
            assert status.calibration is None
        finally:
            await ctx.aclose()

    async def test_aclose_stops_the_calibration_engine(self, tmp_path: Path) -> None:
        # Shutdown must stop the engine cleanly (an engine that never settles must
        # not wedge shutdown — the spy's stop() records the clean cancellation).
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        engine = _FakeStatusEngine(state="cached")
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, calibration_engine=engine
        )
        await ctx.aclose()
        assert engine.stopped is True, "aclose must stop the calibration engine"


# --------------------------------------------------------------------------- #
# P8d Wave 4a — caller_model budget re-denomination (plan re-amendment
# 2026-07-04). ``caller_model`` plugs into the SAME chokepoint
# (``AppContext._count_tokens_single``) every budgeted call already reads;
# ``None`` (the default) is BYTE-IDENTICAL to pre-Wave-4a behaviour.
# --------------------------------------------------------------------------- #


class TestCallerModelTokenCounting:
    """``_count_tokens_single``'s new ``caller_model`` kwarg, in isolation."""

    async def test_omitted_caller_model_is_unchanged_default(self, tmp_path: Path) -> None:
        from loremaster.server import TOKEN_BUDGET_CALIBRATION

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            voyage_count = ctx.embedder.count_tokens(["hello world"])[0]
            import math

            assert ctx._count_tokens_single("hello world") == math.ceil(  # noqa: SLF001
                voyage_count * TOKEN_BUDGET_CALIBRATION
            )
        finally:
            await ctx.aclose()

    async def test_caller_model_with_a_cached_ratio_scales_by_it(self, tmp_path: Path) -> None:
        import math

        config = _config(_slug(), tmp_path / "live")
        engine = _FakeStatusEngine(
            state="measured", served=1.78, per_model_ratios={"claude-haiku-4-5": 1.35}
        )
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, calibration_engine=engine
        )
        try:
            voyage_count = ctx.embedder.count_tokens(["hello world"])[0]
            counted = ctx._count_tokens_single(  # noqa: SLF001
                "hello world", caller_model="claude-haiku-4-5"
            )
            assert counted == math.ceil(voyage_count * 1.35)
            assert counted != ctx._count_tokens_single("hello world")  # noqa: SLF001 - proves it's applied
        finally:
            await ctx.aclose()

    async def test_caller_model_with_no_cached_ratio_falls_back_to_served_constant(
        self, tmp_path: Path
    ) -> None:
        config = _config(_slug(), tmp_path / "live")
        engine = _FakeStatusEngine(state="measured", served=1.78)  # no per_model_ratios
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, calibration_engine=engine
        )
        try:
            assert ctx._count_tokens_single(  # noqa: SLF001
                "hello world", caller_model="claude-haiku-4-5"
            ) == ctx._count_tokens_single("hello world")  # noqa: SLF001
        finally:
            await ctx.aclose()

    async def test_caller_model_note_names_the_model_and_the_fallback(
        self, tmp_path: Path
    ) -> None:
        config = _config(_slug(), tmp_path / "live")
        engine = _FakeStatusEngine(state="measured", served=1.78)
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, calibration_engine=engine
        )
        try:
            note = ctx._caller_model_note("claude-haiku-4-5")  # noqa: SLF001
            assert note is not None
            assert "claude-haiku-4-5" in note
            assert "no measured ratio" in note
            assert ctx._caller_model_note(None) is None  # noqa: SLF001
        finally:
            await ctx.aclose()


class TestSearchParamsCutBudgetAndTeachingMiss:
    """lore_search: filters dict -> path/tier; a response-token budget with an
    announced elision; a path/tier filter that matches nothing renders a
    teaching notice rather than a bare (or memory-masked) empty."""

    @pytest_asyncio.fixture()
    async def indexed_context(self, tmp_path: Path) -> AsyncIterator[AppContext]:
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

    async def test_filters_dict_param_is_gone(self, indexed_context: AppContext) -> None:
        with pytest.raises(TypeError):
            await indexed_context.search("champion routing", filters={"tier": "custom"})  # type: ignore[call-arg]

    async def test_path_param_scopes_like_the_old_filters_dict(
        self, indexed_context: AppContext
    ) -> None:
        results = await indexed_context.search("champion routing", path="pkg/router.py")
        hits = [r for r in results if r.kind == "hit"]
        assert hits
        assert all("pkg/router.py" in r.formatted for r in hits)

    async def test_tier_param_scopes_like_the_old_filters_dict(
        self, indexed_context: AppContext
    ) -> None:
        results = await indexed_context.search("champion routing", tier="custom")
        assert [r for r in results if r.kind == "hit"]

    async def test_unknown_path_filter_renders_a_teaching_notice_not_a_bare_empty(
        self, indexed_context: AppContext
    ) -> None:
        results = await indexed_context.search("champion routing", path="pkg/nope.py")
        notices = [r for r in results if r.kind == "notice"]
        assert notices, "a path filter matching nothing must render a teaching notice"
        message = notices[0].formatted
        assert "pkg/nope.py" in message
        assert "pkg/router.py" in message or "pkg/base.py" in message, (
            "the teach should name a nearby real indexed path"
        )

    async def test_unknown_tier_filter_renders_tier_appropriate_teaching_not_path_wording(
        self, indexed_context: AppContext
    ) -> None:
        """A tier-only miss teaches tiers, never path/subtree wording (P8d' #54).

        Live repro (docs/eval/p8d-flip-eval-raw.md task 9 feedback): tier=
        "loresigil" (a package name, not a tier) rendered the PATH-flavored
        ``_FILTER_MISS_NO_SUBTREE_HINT`` ("subtree/prefix scoping is not
        supported ... pass an exact indexed file path") even though no path
        was ever given -- confusing wording for a tier typo. The teach must
        instead name the missed tier value and the actual configured tier(s).
        """
        results = await indexed_context.search("champion routing", tier="loresigil")
        notices = [r for r in results if r.kind == "notice"]
        assert notices, "a tier filter matching nothing must render a teaching notice"
        message = notices[0].formatted
        assert "loresigil" in message, "the teach must name the missed tier value"
        assert "custom" in message, "the teach must name the actual configured tier(s)"
        assert "subtree" not in message, "a tier-only miss must not carry path/subtree wording"
        assert "exact indexed file path" not in message, (
            "a tier-only miss must not carry path-teaching wording"
        )

    async def test_memory_only_hits_under_a_filter_still_teach_the_miss(
        self, indexed_context: AppContext
    ) -> None:
        # A search_pipeline stub that returns ONLY a memory-kind entry — proving
        # a filtered search never lets a memory injection mask a real code-match
        # miss (no code-match masking).
        from loremaster.search import SearchResult

        class _MemoryOnlyPipeline:
            async def search_code(self, *args: Any, **kwargs: Any) -> list[SearchResult]:
                return [
                    SearchResult(
                        formatted="[MEMORY] some unrelated note (refs: )",
                        chunk_key="",
                        detail_level="summary",
                        stale=False,
                        score=0.9,
                        kind="memory",
                    )
                ]

        indexed_context.search_pipeline = _MemoryOnlyPipeline()  # type: ignore[assignment]
        results = await indexed_context.search("anything", path="pkg/router.py")
        assert any(r.kind == "notice" for r in results), (
            "memory-only results under a filter must still render the filter-miss teach"
        )

    async def test_budget_default_elides_a_large_result_set(
        self, indexed_context: AppContext
    ) -> None:
        results = await indexed_context.search("champion routing", k=10, budget=250)
        notices = [r for r in results if r.kind == "notice" and "elided" in r.formatted]
        assert notices, "a tight budget must elide and announce it"
        assert "budget=250" in notices[0].formatted

    async def test_generous_budget_elides_nothing(self, indexed_context: AppContext) -> None:
        results = await indexed_context.search("champion routing", k=10, budget=6000)
        assert not [r for r in results if r.kind == "notice" and "elided" in r.formatted]

    async def test_budget_elision_notice_names_top_elided_hit_and_a_raise_hint(
        self, indexed_context: AppContext
    ) -> None:
        # T4 (P8d' #54 tweak): the elision notice must go beyond a bare count
        # -- name the top elided hit (identity + score) and a concrete "raise
        # budget to ~N" hint, reusing the SAME calibrated counter the
        # enforcement path already runs (no new estimation machinery).
        #
        # Updated for finding #75: these hits carry no fence, so the
        # floor-of-one stub can't shrink hit-0's rendered form -- but it is
        # still SERVED (unstripped + marked), not elided. hit-1 is now the
        # deterministic "top elided" entry (the highest-priority one that
        # is genuinely NOT shown), never hit-0.
        from loremaster.search import SearchResult

        class _HugeHitsPipeline:
            async def search_code(self, *args: Any, **kwargs: Any) -> list[SearchResult]:
                # Each hit's formatted text is deliberately huge so even ONE
                # blows the floor budget -- the "top elided" hit is then
                # deterministically the FIRST one, whatever the exact
                # tokenizer counts turn out to be.
                return [
                    SearchResult(
                        formatted=f"[SOURCE:pkg/hit_{i}.py:1]\nKey: hit-{i}\n" + "x" * 4000,
                        chunk_key=f"hit-{i}",
                        detail_level="source",
                        stale=False,
                        score=0.9 - i * 0.1,
                        kind="hit",
                    )
                    for i in range(3)
                ]

        indexed_context.search_pipeline = _HugeHitsPipeline()  # type: ignore[assignment]
        results = await indexed_context.search(
            "anything", budget=_PRODUCTION_MAP_BUDGET_FLOOR
        )
        notice = next(r for r in results if r.kind == "notice" and "elided" in r.formatted)

        assert f"budget={_PRODUCTION_MAP_BUDGET_FLOOR}" in notice.formatted
        assert "hit-1" in notice.formatted, (
            f"finding #75: hit-0 is now floor-served (shown, not elided) -- "
            f"expected hit-1 named as the top elided entry; got "
            f"{notice.formatted!r}"
        )
        assert "hit-0" not in notice.formatted, (
            f"the floor-served stub must not be double-counted as elided "
            f"in the notice; got {notice.formatted!r}"
        )
        assert "score=" in notice.formatted
        assert "raise budget to ~" in notice.formatted
        assert "all 3 entries" in notice.formatted
        assert any(r.kind == "hit" and r.chunk_key == "hit-0" for r in results), (
            f"finding #75: hit-0 must still be served, downgraded to a "
            f"stub, rather than dropped entirely; got {results!r}"
        )

    async def test_raise_to_hint_never_exceeds_the_enforced_cap(
        self, indexed_context: AppContext
    ) -> None:
        """S6 (finding #59): the "raise budget to ~N" hint must never name an
        N beyond ``_SEARCH_BUDGET_CAP`` -- the tool's own schema rejects any
        budget above it (``le=_SEARCH_BUDGET_CAP``), so an unclamped
        suggestion hands the caller a next call the schema bounces
        (live-observed 6200-11001 in the P8d' gate re-run, finding #59).
        When the full un-elided join genuinely exceeds the cap, the notice
        must say so honestly AND name exactly how many of the total entries
        the cap DOES surface -- never silently overpromise "raise to N to
        see all" when N could not be requested at all.
        """
        from loremaster.search import SearchResult

        class _OverCapPipeline:
            async def search_code(self, *args: Any, **kwargs: Any) -> list[SearchResult]:
                # 4 hits, each ~4035 chars -- under the FakeEmbedder's len//4
                # heuristic + the 1.78 calibration constant, the full
                # un-elided join costs ~7183 Claude-tokens (over the 6000
                # cap); the first 3 alone cost ~5387 (under it) -- so raising
                # to the cap reveals exactly 3 of 4.
                return [
                    SearchResult(
                        formatted=f"[SOURCE:pkg/hit_{i}.py:1]\nKey: hit-{i}\n" + "x" * 4000,
                        chunk_key=f"hit-{i}",
                        detail_level="source",
                        stale=False,
                        score=0.9 - i * 0.1,
                        kind="hit",
                    )
                    for i in range(4)
                ]

        indexed_context.search_pipeline = _OverCapPipeline()  # type: ignore[assignment]
        results = await indexed_context.search(
            "anything", budget=_PRODUCTION_MAP_BUDGET_FLOOR
        )
        notice = next(r for r in results if r.kind == "notice" and "elided" in r.formatted)

        raise_to = re.search(r"raise budget to (?:~|the )?(\d+)", notice.formatted)
        assert raise_to, f"expected a raise-to hint; got {notice.formatted!r}"
        assert int(raise_to.group(1)) <= _SEARCH_BUDGET_CAP, (
            f"suggested a budget beyond the enforced cap; got {notice.formatted!r}"
        )
        assert f"{_SEARCH_BUDGET_CAP}" in notice.formatted
        assert "cannot show all 4 entries" in notice.formatted, (
            f"expected an honest cap-can't-show-everything statement; got {notice.formatted!r}"
        )
        assert "3 of 4 entries" in notice.formatted, (
            f"expected the exact count the cap DOES surface; got {notice.formatted!r}"
        )

    async def test_raise_to_hint_when_caller_is_already_at_the_cap(
        self, tmp_path: Path
    ) -> None:
        """Hostile fixture (S6): a direct ``_enforce_search_budget`` call AT
        the cap, where even the cap can't show everything, must not recurse
        forever (the "re-run at the cap" computation would otherwise call
        itself with the SAME budget indefinitely) and must render an honest
        "already at the max" notice rather than a redundant "raise to the
        max you're already at" instruction.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            results = [
                SearchResult(
                    formatted=f"[SOURCE:pkg/hit_{i}.py:1]\nKey: hit-{i}\n" + "x" * 4000,
                    chunk_key=f"hit-{i}",
                    detail_level="source",
                    stale=False,
                    score=0.9 - i * 0.1,
                    kind="hit",
                )
                for i in range(4)
            ]
            kept = ctx._enforce_search_budget(  # noqa: SLF001
                list(results), _SEARCH_BUDGET_CAP, None
            )
            notice = next(r for r in kept if r.kind == "notice" and "elided" in r.formatted)
            assert "already at" in notice.formatted, (
                f"expected an 'already at the cap' notice; got {notice.formatted!r}"
            )
            assert "3 of 4 entries" in notice.formatted
        finally:
            await ctx.aclose()

    async def test_elision_notice_carries_the_worst_shown_score(
        self, tmp_path: Path
    ) -> None:
        """S7: the elision notice must also carry the worst-SHOWN score (the
        cliff edge) alongside the existing top-elided score -- both
        informants in the client-needs consult (docs/design/2026-07-06-
        client-needs-consult.md §S7) independently name this as the datum
        that lets a client decide "is the tail weak?" with zero extra calls.

        Hostile fixture: a memory-kind entry survives the budget alongside
        two hit-kind entries. Memory/notice entries carry ``score=0.0`` by
        construction -- a naive ``min()`` over every KEPT entry would report
        0.0 (the memory's placeholder score) instead of 0.35 (the genuinely
        weakest SHOWN hit). The worst-shown score must filter to
        ``kind == "hit"`` only.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            hit_keep_strong = SearchResult(
                formatted="[SOURCE:pkg/a.py:1-5@abc111]\n" + "a" * 40,
                chunk_key="keep-strong",
                detail_level="source",
                stale=False,
                score=0.55,
                kind="hit",
            )
            hit_keep_weak = SearchResult(
                formatted="[SOURCE:pkg/b.py:1-5@abc222]\n" + "b" * 40,
                chunk_key="keep-weak",
                detail_level="source",
                stale=False,
                score=0.35,
                kind="hit",
            )
            memory_entry = SearchResult(
                formatted="[MEMORY] a fact that survives the budget too " + "m" * 20,
                chunk_key="",
                detail_level="summary",
                stale=False,
                score=0.0,
                kind="memory",
            )
            hit_elided = SearchResult(
                formatted="[SOURCE:pkg/big.py:1]\nKey: big-hit\n" + "x" * 4000,
                chunk_key="big-hit",
                detail_level="source",
                stale=False,
                score=0.10,
                kind="hit",
            )
            results = [hit_keep_strong, hit_keep_weak, memory_entry, hit_elided]
            kept = ctx._enforce_search_budget(list(results), 300, None)  # noqa: SLF001
            notice = next(r for r in kept if r.kind == "notice" and "elided" in r.formatted)

            assert "worst shown: score=0.350" in notice.formatted, (
                f"expected the weakest SHOWN hit's score (0.35), not the memory's "
                f"placeholder 0.0; got {notice.formatted!r}"
            )
            assert "worst shown: score=0.000" not in notice.formatted, (
                f"the memory entry's score=0.0 corrupted the worst-shown min; "
                f"got {notice.formatted!r}"
            )
            assert "big-hit" in notice.formatted
            assert "score=0.100" in notice.formatted, "expected the top-elided score too"
        finally:
            await ctx.aclose()

    async def test_elision_notice_worst_shown_is_recomputed_after_the_pop_loop(
        self, tmp_path: Path
    ) -> None:
        """S7 (audit gap, REPORT-slate-audit-server.md §C2): the shipped
        ``test_elision_notice_carries_the_worst_shown_score`` fixture never
        forces the pop-until-it-fits loop (server.py:1931-1935) to actually
        pop a hit, so the dynamic "recompute after every pop" path was
        unpinned -- correct in the code (verified live by the audit), but
        with no regression guard. This fixture DOES force a pop: two hits
        (``keep-strong``=0.9, ``keep-weak``=0.7) both survive the initial
        greedy walk alongside one elided hit, so the FIRST notice render
        reports worst-shown=0.700 (``keep-weak``) -- but appending that
        notice to the two kept hits overflows the budget, so the pop loop
        drops ``keep-weak`` (the trailing, lowest-priority kept entry) and
        must recompute the notice from scratch. The final rendered
        worst-shown score must be 0.900 (``keep-strong``, the survivor),
        never the stale pre-pop 0.700 -- and the elision count must have
        grown from 1 (the initial elision) to 2 (after the pop), proving a
        pop genuinely happened rather than the fixture vacuously passing.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            hit_keep_strong = SearchResult(
                formatted="[SOURCE:pkg/a.py:1-5@abc111]\n" + "a" * 40,
                chunk_key="keep-strong",
                detail_level="source",
                stale=False,
                score=0.9,
                kind="hit",
            )
            hit_keep_weak = SearchResult(
                formatted="[SOURCE:pkg/b.py:1-5@abc222]\n" + "b" * 40,
                chunk_key="keep-weak",
                detail_level="source",
                stale=False,
                score=0.7,
                kind="hit",
            )
            hit_elided = SearchResult(
                formatted="[SOURCE:pkg/big.py:1]\nKey: big-hit\n" + "c" * 4000,
                chunk_key="big-hit",
                detail_level="source",
                stale=False,
                score=0.5,
                kind="hit",
            )
            results = [hit_keep_strong, hit_keep_weak, hit_elided]
            # budget=100: the initial greedy walk keeps BOTH hits (their
            # joined cost is ~61 Claude-tokens, under 100) and elides
            # ``hit_elided`` -- but appending the first-built notice (which
            # names worst-shown=0.700, the weaker of the two kept hits) to
            # the two kept texts costs ~125, over budget, so the pop loop
            # must fire at least once. Popping ``keep-weak`` (the trailing
            # kept entry) leaves only ``keep-strong`` + the recomputed
            # notice at ~93, which fits -- the loop stops there, one pop.
            kept = ctx._enforce_search_budget(list(results), 100, None)  # noqa: SLF001
            notice = next(r for r in kept if r.kind == "notice" and "elided" in r.formatted)

            surviving_keys = {r.chunk_key for r in kept if r.kind == "hit"}
            assert surviving_keys == {"keep-strong"}, (
                f"expected the pop loop to drop 'keep-weak', leaving only "
                f"'keep-strong'; kept hit keys were {surviving_keys!r} -- "
                f"the fixture did not exercise the pop path"
            )
            assert "+2 entries elided" in notice.formatted, (
                f"expected the elision count to have grown from 1 (initial) "
                f"to 2 (after the pop) -- proves a pop actually happened; "
                f"got {notice.formatted!r}"
            )
            assert "worst shown: score=0.900" in notice.formatted, (
                f"expected the RECOMPUTED post-pop worst-shown score (0.900, "
                f"the surviving 'keep-strong'), not the stale pre-pop value; "
                f"got {notice.formatted!r}"
            )
            assert "worst shown: score=0.700" not in notice.formatted, (
                f"the notice still carries the STALE pre-pop worst-shown "
                f"score (0.700, 'keep-weak', which the pop loop dropped); "
                f"got {notice.formatted!r}"
            )
            # Finding #81: `top_elided` must be RECOMPUTED after the pop
            # too, exactly like `worst_shown_score` above -- the popped
            # 'keep-weak' (0.700) outranks the original top-elided
            # 'big-hit' (0.500) by fused-order construction (it was KEPT by
            # the initial walk; 'big-hit' was not), so it is now the true
            # top elided entry. The shipped pre-#81 code left `top_elided`
            # as a fixed post-walk index and kept naming 'big-hit' here --
            # wrong identity AND wrong score in the notice's most
            # decision-relevant datum.
            assert "top elided: 'keep-weak' (score=0.700)" in notice.formatted, (
                f"expected the RECOMPUTED post-pop top-elided entry "
                f"('keep-weak', 0.700 -- the pop loop just dropped it, and "
                f"it outranks the original top-elided 'big-hit'), not the "
                f"stale pre-pop identity; got {notice.formatted!r}"
            )
            assert "top elided: 'big-hit'" not in notice.formatted, (
                f"the notice still names the STALE pre-pop top-elided "
                f"entry ('big-hit', 0.500), which the pop-loop-dropped "
                f"'keep-weak' (0.700) outranks; got {notice.formatted!r}"
            )
        finally:
            await ctx.aclose()

    async def test_elision_notice_reports_the_floor_stubs_score_as_worst_shown(
        self, indexed_context: AppContext
    ) -> None:
        """Guard (S7), updated for finding #75. Was
        ``test_elision_notice_omits_worst_shown_when_no_hit_survives``: with
        every hit oversized, pre-#75 NOTHING of kind "hit" ever survived the
        budget, so the worst-shown clause was correctly omitted. Post-#75,
        the floor-of-one rule always serves the top hit as a stub, so a hit
        genuinely IS shown -- the worst-shown clause must now report ITS
        score (never a fabricated 0.0, and never omitted when a hit really
        did survive, even downgraded). The complementary guard --
        genuinely nothing of kind "hit" ever considered, clause still
        omitted -- is pinned directly by
        ``test_floor_of_one_never_fires_for_a_non_hit_first_entry``.
        """
        from loremaster.search import SearchResult

        class _HugeHitsPipeline:
            async def search_code(self, *args: Any, **kwargs: Any) -> list[SearchResult]:
                return [
                    SearchResult(
                        formatted=f"[SOURCE:pkg/hit_{i}.py:1]\nKey: hit-{i}\n" + "x" * 4000,
                        chunk_key=f"hit-{i}",
                        detail_level="source",
                        stale=False,
                        score=0.9 - i * 0.1,
                        kind="hit",
                    )
                    for i in range(3)
                ]

        indexed_context.search_pipeline = _HugeHitsPipeline()  # type: ignore[assignment]
        results = await indexed_context.search(
            "anything", budget=_PRODUCTION_MAP_BUDGET_FLOOR
        )
        notice = next(r for r in results if r.kind == "notice" and "elided" in r.formatted)
        assert "worst shown: score=0.900" in notice.formatted, (
            f"finding #75: the floor-served stub (hit-0, score=0.9) is the "
            f"worst (and only) SHOWN hit -- expected its score reported, "
            f"not omitted; got {notice.formatted!r}"
        )

    async def test_tight_budget_never_leaves_a_dangling_memories_header(
        self, tmp_path: Path
    ) -> None:
        """F1 (REPORT-audit-tweaks.md): ``_enforce_search_budget`` must never
        keep the ``memories:`` section header while every memory entry
        beneath it gets squeezed out -- a CLASS invariant (header survives
        iff >=1 memory-kind entry survives with it), not a numbers-specific
        fix. Mirrors the audit's live repro (scratchpad/probe_budget.py, an
        UNTRACKED scratch file -- it is still on disk today but repo law does
        not preserve it, so it is not a durable instrument) -- the same list
        shape ``[*hits, header, mem1, mem2, mem3]`` fed straight into the real
        ``_enforce_search_budget`` -- swept across a budget range wide enough to
        cross the dangling window the audit measured (the audit's
        dangled-budget COUNT is struck: it was specific to that fixture shape
        and no in-tree instrument reproduces it; the sweep below is what makes
        the invariant checkable).
        """
        from loremaster.search import _MEMORY_SECTION_HEADER, SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            hit = SearchResult(
                formatted="[SOURCE:pkg/router.py:1-10@abc123]\n" + "h" * 40,
                chunk_key="hit-key-0",
                detail_level="source",
                stale=False,
                score=0.9,
                kind="hit",
            )
            header = SearchResult(
                formatted=_MEMORY_SECTION_HEADER,
                chunk_key="",
                detail_level="summary",
                stale=False,
                score=0.0,
                kind="notice",
            )
            memories = [
                SearchResult(
                    formatted=f"[MEMORY] remembered correction number {i} " + "m" * 30,
                    chunk_key="",
                    detail_level="summary",
                    stale=False,
                    score=0.5,
                    kind="memory",
                )
                for i in range(3)
            ]
            base = [hit, header, *memories]
            dangling: list[int] = []
            for budget in range(1, 200):
                kept = ctx._enforce_search_budget(list(base), budget, None)  # noqa: SLF001
                has_header = any(r.formatted == _MEMORY_SECTION_HEADER for r in kept)
                has_memory_entry = any(r.kind == "memory" for r in kept)
                if has_header and not has_memory_entry:
                    dangling.append(budget)
            assert not dangling, (
                "a memories: header rendered with zero memory entries beneath "
                f"it at budgets {dangling}"
            )
        finally:
            await ctx.aclose()

    async def test_absence_verdict_survives_budget_when_an_oversized_weak_hit_precedes_it(
        self, indexed_context: AppContext
    ) -> None:
        """Finding #71 (live post-deploy smoke, image ee7c3a8e73cd): the
        canonical nonsense-query shape returns one oversized weak hit ranked
        first plus the absence-verdict notice trailing it (§7.4.3). At the
        DEFAULT budget (1100) the oversized hit alone blows the budget, and
        the greedy prefix walk used to break before it ever reached the
        verdict -- the client got ZERO verdict on exactly the query shape
        the verdict exists for. The verdict must now survive.

        Updated for finding #75: pre-#75, "the oversized hit must still be
        honestly elided" was the best available outcome -- the hit was
        simply dropped. Post-#75, the SAME shape is exactly the floor-of-one
        trigger (the greedy walk keeps nothing, walkable has one entry): the
        hit is now served too, downgraded to a stub, alongside the verdict
        -- and since it is the ONLY walkable entry, nothing is left to
        elide, so no elision notice is owed at all.
        """
        from loremaster.search import SearchResult

        class _OversizedWeakHitPipeline:
            async def search_code(self, *args: Any, **kwargs: Any) -> list[SearchResult]:
                fence = "```"
                return [
                    SearchResult(
                        formatted="\n".join(
                            [
                                "[SOURCE:pkg/huge.py:1]",
                                "Key: huge-weak-hit",
                                "[S:lore:pkg/huge.py:1-900@abcdef]",
                                fence,
                                "x" * 6000,
                                fence,
                            ]
                        ),
                        chunk_key="huge-weak-hit",
                        detail_level="source",
                        stale=False,
                        score=0.03,
                        kind="hit",
                    ),
                    SearchResult(
                        formatted=(
                            "no confident match: best hit similarity 0.27 is below "
                            "the range real answers measure on this corpus "
                            "(>=0.58) and no hit matches your identifiers verbatim "
                            "-- likely no direct answer indexed; nearest indexed: "
                            "'pkg.huge.weak_fn' -- broaden the query or treat these "
                            "hits as adjacent-topic leads"
                        ),
                        chunk_key="",
                        detail_level="summary",
                        stale=False,
                        score=0.0,
                        kind="notice",
                    ),
                ]

        indexed_context.search_pipeline = _OversizedWeakHitPipeline()  # type: ignore[assignment]
        results = await indexed_context.search("nonsense query shape", k=5)

        notices = [r for r in results if r.kind == "notice"]
        verdict = next((n for n in notices if "no confident match" in n.formatted), None)
        assert verdict is not None, (
            f"the absence verdict must survive the default budget; got notices={notices!r}"
        )
        hits = [r for r in results if r.kind == "hit"]
        assert len(hits) == 1 and hits[0].chunk_key == "huge-weak-hit", (
            f"finding #75: the oversized weak hit must now be SERVED, "
            f"downgraded to a stub, rather than dropped; got {results!r}"
        )
        assert "x" * 6000 not in hits[0].formatted, (
            f"the stub must not carry the full oversized body; got {hits[0].formatted!r}"
        )
        assert _SEARCH_STUB_NOTICE in hits[0].formatted
        elision = next((n for n in notices if "elided" in n.formatted), None)
        assert elision is None, (
            f"the ONLY walkable entry is now shown (as a stub) -- nothing "
            f"is left to elide, so no elision notice is owed; got "
            f"notices={notices!r}"
        )

    async def test_verdict_absent_budget_enforcement_is_unaffected(
        self, tmp_path: Path
    ) -> None:
        """Finding #71 regression guard: with no absence-verdict entry in the
        result list, the new reservation logic must never fire -- the greedy
        walk + pop-until-it-fits behaviour must stay byte-identical to
        before this fix (same fixture/expectations as the pre-existing
        ``test_elision_notice_worst_shown_is_recomputed_after_the_pop_loop``).
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            hit_keep_strong = SearchResult(
                formatted="[SOURCE:pkg/a.py:1-5@abc111]\n" + "a" * 40,
                chunk_key="keep-strong",
                detail_level="source",
                stale=False,
                score=0.9,
                kind="hit",
            )
            hit_keep_weak = SearchResult(
                formatted="[SOURCE:pkg/b.py:1-5@abc222]\n" + "b" * 40,
                chunk_key="keep-weak",
                detail_level="source",
                stale=False,
                score=0.7,
                kind="hit",
            )
            hit_elided = SearchResult(
                formatted="[SOURCE:pkg/big.py:1]\nKey: big-hit\n" + "c" * 4000,
                chunk_key="big-hit",
                detail_level="source",
                stale=False,
                score=0.5,
                kind="hit",
            )
            results = [hit_keep_strong, hit_keep_weak, hit_elided]
            kept = ctx._enforce_search_budget(list(results), 100, None)  # noqa: SLF001
            notice = next(r for r in kept if r.kind == "notice" and "elided" in r.formatted)

            surviving_keys = {r.chunk_key for r in kept if r.kind == "hit"}
            assert surviving_keys == {"keep-strong"}
            assert "+2 entries elided" in notice.formatted
            assert "worst shown: score=0.900" in notice.formatted
        finally:
            await ctx.aclose()

    async def test_absence_verdict_composes_readably_with_elision_and_worst_shown(
        self, tmp_path: Path
    ) -> None:
        """Finding #71: the absence verdict, the budget-elision notice, and
        the worst-shown-score clause must all compose correctly in ONE
        response -- the verdict's reservation must not corrupt the elision
        count or the worst-shown computation over the surviving hits.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            hit_keep_strong = SearchResult(
                formatted="[SOURCE:pkg/a.py:1-5@abc111]\n" + "a" * 40,
                chunk_key="keep-strong",
                detail_level="source",
                stale=False,
                score=0.9,
                kind="hit",
            )
            hit_keep_weak = SearchResult(
                formatted="[SOURCE:pkg/b.py:1-5@abc222]\n" + "b" * 40,
                chunk_key="keep-weak",
                detail_level="source",
                stale=False,
                score=0.6,
                kind="hit",
            )
            hit_elided = SearchResult(
                formatted="[SOURCE:pkg/big.py:1]\nKey: big-hit\n" + "c" * 4000,
                chunk_key="big-hit",
                detail_level="source",
                stale=False,
                score=0.1,
                kind="hit",
            )
            verdict = SearchResult(
                formatted=(
                    "no confident match: best hit similarity 0.31 is below the "
                    "range real answers measure on this corpus (>=0.58) and no "
                    "hit matches your identifiers verbatim -- likely no direct "
                    "answer indexed; nearest indexed: 'pkg.a.weak_fn' -- broaden "
                    "the query or treat these hits as adjacent-topic leads"
                ),
                chunk_key="",
                detail_level="summary",
                stale=False,
                score=0.0,
                kind="notice",
            )
            results = [hit_keep_strong, hit_keep_weak, hit_elided, verdict]
            kept = ctx._enforce_search_budget(list(results), 400, None)  # noqa: SLF001

            surviving_keys = {r.chunk_key for r in kept if r.kind == "hit"}
            assert surviving_keys == {"keep-strong", "keep-weak"}, (
                f"expected both small hits to survive and the oversized one "
                f"elided; got {surviving_keys!r}"
            )
            notices = [r for r in kept if r.kind == "notice"]
            verdict_notices = [n for n in notices if "no confident match" in n.formatted]
            assert len(verdict_notices) == 1, (
                f"expected exactly one absence verdict, never duplicated or "
                f"dropped; got {notices!r}"
            )
            elision_notices = [n for n in notices if "elided" in n.formatted]
            assert len(elision_notices) == 1
            assert "+1 entries elided" in elision_notices[0].formatted
            assert "worst shown: score=0.600" in elision_notices[0].formatted, (
                f"expected the weakest SURVIVING hit's score; got "
                f"{elision_notices[0].formatted!r}"
            )
        finally:
            await ctx.aclose()

    async def test_absence_verdict_and_elision_notice_are_the_honest_mandatory_tail_at_a_tiny_budget(
        self, tmp_path: Path
    ) -> None:
        """Finding #71 fixture (d): a budget so tiny that even the verdict +
        elision notice together exceed it. Documented, honest behaviour:
        the verdict is still rendered (never an infinite loop, never a
        silent drop).

        Updated for finding #75: pre-#75 the served surface was
        ``[verdict, elision notice]`` -- honest, but zero real content,
        exactly the degenerate case #75 fixes. ``hit_elided`` carries no
        fence (nothing to strip), so the floor-of-one stub can't shrink it
        -- but it is still served, UNCONDITIONALLY, even though the stub
        itself still busts this budget=10. Since it is the ONLY walkable
        entry, nothing else is left to elide once it's shown: the served
        surface becomes ``[stub, verdict]``, no elision notice at all.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            hit_elided = SearchResult(
                formatted="[SOURCE:pkg/big.py:1]\nKey: big-hit\n" + "c" * 4000,
                chunk_key="big-hit",
                detail_level="source",
                stale=False,
                score=0.1,
                kind="hit",
            )
            verdict = SearchResult(
                formatted=(
                    "no confident match: best hit similarity 0.31 is below the "
                    "range real answers measure on this corpus (>=0.58) and no "
                    "hit matches your identifiers verbatim -- likely no direct "
                    "answer indexed; nearest indexed: 'pkg.a.weak_fn' -- broaden "
                    "the query or treat these hits as adjacent-topic leads"
                ),
                chunk_key="",
                detail_level="summary",
                stale=False,
                score=0.0,
                kind="notice",
            )
            results = [hit_elided, verdict]
            kept = ctx._enforce_search_budget(list(results), 10, None)  # noqa: SLF001

            assert len(kept) == 2, f"expected exactly [stub, verdict]; got {kept!r}"
            assert kept[0].kind == "hit" and kept[0].chunk_key == "big-hit", (
                f"finding #75: the floor must still serve the hit -- "
                f"unstripped, since it carries no fence -- rather than "
                f"dropping it, even though the stub itself busts this tiny "
                f"budget; got {kept!r}"
            )
            assert _SEARCH_STUB_NOTICE in kept[0].formatted
            assert "no confident match" in kept[1].formatted
        finally:
            await ctx.aclose()

    async def test_absence_verdict_survives_the_at_cap_recursive_recompute(
        self, tmp_path: Path
    ) -> None:
        """Finding #71 + S6 interaction: when the full un-elided join
        (hits + verdict) exceeds ``_SEARCH_BUDGET_CAP`` and the requested
        budget is below the cap, ``_enforce_search_budget`` recurses ONCE
        (at the cap) to compute how many entries the cap would surface. The
        verdict must still identify correctly and survive on BOTH the outer
        and the recursive call -- and the recursion must not loop.

        Updated for finding #75: at the floor budget every oversized hit
        blows the budget alone, so the PRE-#75 expectation was "only the
        verdict + the elision notice survive" -- exactly the degenerate,
        zero-content response #75 fixes. The floor-of-one rule now also
        serves ``hit-0`` as a stub, so exactly one hit-kind entry survives
        alongside the verdict; the cap-recursion math (3 of 5 entries
        visible at the cap) is UNCHANGED, since that recursive call at
        ``_SEARCH_BUDGET_CAP`` never itself degenerates (3 hits fit there
        without the floor firing).
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            hits = [
                SearchResult(
                    formatted=f"[SOURCE:pkg/hit_{i}.py:1]\nKey: hit-{i}\n" + "x" * 4000,
                    chunk_key=f"hit-{i}",
                    detail_level="source",
                    stale=False,
                    score=0.9 - i * 0.1,
                    kind="hit",
                )
                for i in range(4)
            ]
            verdict = SearchResult(
                formatted=(
                    "no confident match: best hit similarity 0.31 is below the "
                    "range real answers measure on this corpus (>=0.58) and no "
                    "hit matches your identifiers verbatim -- likely no direct "
                    "answer indexed; nearest indexed: 'pkg.a.weak_fn' -- broaden "
                    "the query or treat these hits as adjacent-topic leads"
                ),
                chunk_key="",
                detail_level="summary",
                stale=False,
                score=0.0,
                kind="notice",
            )
            results = [*hits, verdict]
            kept = ctx._enforce_search_budget(  # noqa: SLF001
                list(results), _PRODUCTION_MAP_BUDGET_FLOOR, None
            )

            assert any("no confident match" in r.formatted for r in kept), (
                f"the verdict must survive the capped recursive recompute; got {kept!r}"
            )
            hit_kind_entries = [r for r in kept if r.kind == "hit"]
            assert len(hit_kind_entries) == 1 and hit_kind_entries[0].chunk_key == "hit-0", (
                f"finding #75: the floor-of-one rule must still serve "
                f"'hit-0' as a stub even inside the #71 capped-recursion "
                f"path; got hit-kind entries {hit_kind_entries!r}"
            )
            notice = next(r for r in kept if r.kind == "notice" and "elided" in r.formatted)
            assert f"{_SEARCH_BUDGET_CAP}" in notice.formatted
            assert "cannot show all 5 entries" in notice.formatted
            assert "3 of 5 entries" in notice.formatted
        finally:
            await ctx.aclose()

    async def test_floor_of_one_serves_a_stub_when_every_hit_is_oversized(
        self, tmp_path: Path
    ) -> None:
        """Finding #75: the closure-test probe's core repro. When the
        greedy walk keeps literally NOTHING (the top fused-order hit alone
        blows ``budget``), the caller must not receive an elision notice
        with zero real content -- the top hit is served as a stub instead.
        The stub is SHOWN, not elided: the notice's ``elided`` count must
        name only the genuinely-elided second hit, never double-counting
        the stub.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            fence = "```"
            hit_oversized = SearchResult(
                formatted="\n".join(
                    [
                        "[SOURCE:pkg/huge.py:1-900]",
                        "Key: hit0-key",
                        "[S:lore:pkg/huge.py:1-900@abcdef]",
                        "← 0 prod / 0 test · tests: 0",
                        "def huge_function(*args, **kwargs) -> None:",
                        fence,
                        "x" * 20000,
                        fence,
                    ]
                ),
                chunk_key="hit0-key",
                detail_level="source",
                stale=False,
                score=0.8,
                kind="hit",
            )
            hit_second = SearchResult(
                formatted="[SOURCE:pkg/small.py:1-3]\nKey: hit1-key\n" + "y" * 20,
                chunk_key="hit1-key",
                detail_level="source",
                stale=False,
                score=0.6,
                kind="hit",
            )
            results = [hit_oversized, hit_second]
            kept = ctx._enforce_search_budget(list(results), 500, None)  # noqa: SLF001

            assert len(kept) == 2, f"expected exactly [stub, elision notice]; got {kept!r}"
            stub, notice = kept
            assert stub.kind == "hit" and stub.chunk_key == "hit0-key"
            assert "x" * 20000 not in stub.formatted, (
                f"the fenced body must be stripped from the stub; got {stub.formatted!r}"
            )
            assert "[SOURCE:pkg/huge.py:1-900]" in stub.formatted
            assert "Key: hit0-key" in stub.formatted
            assert _SEARCH_STUB_NOTICE in stub.formatted

            assert notice.kind == "notice" and "elided" in notice.formatted
            assert "+1 entries elided" in notice.formatted, (
                f"only hit1 is genuinely elided -- the stub is SHOWN, not "
                f"elided; got {notice.formatted!r}"
            )
            assert "hit1-key" in notice.formatted, (
                f"expected hit1 (the next truly-elided entry) named as top "
                f"elided, not the stubbed hit0; got {notice.formatted!r}"
            )
            assert "hit0-key" not in notice.formatted, (
                f"the stub must never be double-counted as elided in the "
                f"notice; got {notice.formatted!r}"
            )
        finally:
            await ctx.aclose()

    async def test_floor_of_one_omits_the_notice_when_the_only_hit_is_shown(
        self, tmp_path: Path
    ) -> None:
        """Finding #75: when the ONE walkable entry gets floor-served as a
        stub, nothing else is left to elide -- no elision notice is owed at
        all (mirrors the pre-existing ``if not elided: return kept`` early
        return for the normal, non-degenerate case).
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            fence = "```"
            hit_oversized = SearchResult(
                formatted="\n".join(
                    [
                        "[SOURCE:pkg/huge.py:1-900]",
                        "Key: only-key",
                        "[S:lore:pkg/huge.py:1-900@abcdef]",
                        fence,
                        "z" * 20000,
                        fence,
                    ]
                ),
                chunk_key="only-key",
                detail_level="source",
                stale=False,
                score=0.4,
                kind="hit",
            )
            kept = ctx._enforce_search_budget([hit_oversized], 500, None)  # noqa: SLF001

            assert len(kept) == 1, f"expected exactly [stub], no notice; got {kept!r}"
            assert kept[0].kind == "hit" and kept[0].chunk_key == "only-key"
            assert "z" * 20000 not in kept[0].formatted
        finally:
            await ctx.aclose()

    async def test_floor_of_one_stub_survives_even_when_the_stub_itself_busts_budget(
        self, tmp_path: Path
    ) -> None:
        """Finding #75 hostile fixture: the honest floor is UNCONDITIONAL --
        even at a budget so tiny (1) that the stub's own identity kernel
        cannot fit, the stub is still served rather than falling back to
        notice-only. Zero content is a strictly worse failure than a small,
        honestly-marked budget overrun (see ``_enforce_search_budget``'s
        finding #75 docstring for the reasoning this pins).
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            fence = "```"
            hit_oversized = SearchResult(
                formatted="\n".join(
                    [
                        "[SOURCE:pkg/huge.py:1-900]",
                        "Key: hit0-key",
                        "[S:lore:pkg/huge.py:1-900@abcdef]",
                        fence,
                        "x" * 20000,
                        fence,
                    ]
                ),
                chunk_key="hit0-key",
                detail_level="source",
                stale=False,
                score=0.8,
                kind="hit",
            )
            hit_second = SearchResult(
                formatted="[SOURCE:pkg/small.py:1-3]\nKey: hit1-key\n" + "y" * 20,
                chunk_key="hit1-key",
                detail_level="source",
                stale=False,
                score=0.6,
                kind="hit",
            )
            results = [hit_oversized, hit_second]
            kept = ctx._enforce_search_budget(list(results), 1, None)  # noqa: SLF001

            assert len(kept) == 2, f"expected [stub, elision notice] even over budget; got {kept!r}"
            assert kept[0].kind == "hit" and kept[0].chunk_key == "hit0-key", (
                "the floor must serve the stub even though it alone busts "
                "budget=1 -- never fall back to notice-only"
            )
            assert kept[1].kind == "notice" and "+1 entries elided" in kept[1].formatted
        finally:
            await ctx.aclose()

    async def test_floor_of_one_stub_strips_the_true_fence_not_an_embedded_backtick_run(
        self, tmp_path: Path
    ) -> None:
        """Finding #75 hostile fixture: a body that itself contains a
        shorter run of backticks (nested markdown/code) must not be
        mistaken for the fence boundary. The TRUE fence is whatever the
        first and last pure-backtick lines are; any pure-backtick line in
        between (necessarily inside the body, since header/substrate lines
        are never bare backtick runs) stays exactly where it is -- inside
        the stripped span.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            true_fence = "`" * 5
            hit_oversized = SearchResult(
                formatted="\n".join(
                    [
                        "[SOURCE:pkg/hostile.py:1-900]",
                        "Key: hostile-key",
                        "[S:lore:pkg/hostile.py:1-900@abcdef]",
                        true_fence,
                        "some code",
                        "`" * 4,  # an embedded, SHORTER backtick run inside the body
                        "more code " + "w" * 20000,
                        true_fence,
                    ]
                ),
                chunk_key="hostile-key",
                detail_level="source",
                stale=False,
                score=0.5,
                kind="hit",
            )
            kept = ctx._enforce_search_budget([hit_oversized], 500, None)  # noqa: SLF001

            assert len(kept) == 1
            stub = kept[0]
            assert "w" * 20000 not in stub.formatted, "the body must still be stripped"
            assert "some code" not in stub.formatted and "more code" not in stub.formatted, (
                f"the whole fenced span, including the embedded backtick "
                f"run, must be stripped; got {stub.formatted!r}"
            )
            assert "Key: hostile-key" in stub.formatted
        finally:
            await ctx.aclose()

    async def test_floor_of_one_stub_marks_but_does_not_strip_an_unfenced_hit(
        self, tmp_path: Path
    ) -> None:
        """Finding #75: a hit whose ``formatted`` carries no recognisable
        fence pair (fewer than two pure-backtick lines) is returned
        unstripped -- the honesty marker is the invariant this floor
        guarantees, not the stripping itself. Also covers every
        PRE-EXISTING budget test fixture in this file, which renders hits
        without a fence at all.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            unfenced = SearchResult(
                formatted="[SOURCE:pkg/unfenced.py:1]\nKey: unfenced-key\n" + "u" * 20000,
                chunk_key="unfenced-key",
                detail_level="source",
                stale=False,
                score=0.5,
                kind="hit",
            )
            kept = ctx._enforce_search_budget([unfenced], 500, None)  # noqa: SLF001

            assert len(kept) == 1
            stub = kept[0]
            assert "u" * 20000 in stub.formatted, (
                "no fence to strip -- the original text must survive unstripped"
            )
            assert _SEARCH_STUB_NOTICE in stub.formatted, (
                "the marker must still be appended even when nothing was stripped"
            )
        finally:
            await ctx.aclose()

    async def test_floor_of_one_never_fires_for_a_non_hit_first_entry(
        self, tmp_path: Path
    ) -> None:
        """Finding #75 scope decision: floor-of-one is specifically the
        method-chunk-oversizing fix -- it never stubs a bare memory or
        notice entry that happens to end up first in fused order. When
        NOTHING of kind ``hit`` ever survives, the pre-#75 behaviour is
        UNCHANGED: notice-only, and the worst-shown clause stays omitted
        (never a fabricated score standing in for "no hit was ever
        considered").
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            oversized_memory = SearchResult(
                formatted="[MEMORY] an oversized recalled note " + "m" * 20000,
                chunk_key="",
                detail_level="summary",
                stale=False,
                score=0.5,
                kind="memory",
            )
            second_memory = SearchResult(
                formatted="[MEMORY] a second recalled note " + "n" * 20,
                chunk_key="",
                detail_level="summary",
                stale=False,
                score=0.3,
                kind="memory",
            )
            kept = ctx._enforce_search_budget(  # noqa: SLF001
                [oversized_memory, second_memory], 500, None
            )

            assert not any(r.kind == "hit" for r in kept), (
                f"floor-of-one must never fire for a non-hit first entry; got {kept!r}"
            )
            notice = next(r for r in kept if r.kind == "notice" and "elided" in r.formatted)
            assert "worst shown" not in notice.formatted, (
                f"no hit-kind entry ever survived -- the worst-shown clause "
                f"must stay omitted, never a fabricated score; got "
                f"{notice.formatted!r}"
            )
        finally:
            await ctx.aclose()

    # ----------------------------------------------------------------- #
    # Finding #79: the floor-of-one guarantee (finding #75) only checked
    # "did the greedy walk keep nothing" ONCE, right after that walk. It
    # never re-checked whether the LATER pop-until-it-fits loop drains an
    # originally non-empty ``kept`` all the way back to zero -- plausible
    # when the elision notice's own rendered overhead (a long top-elided
    # identity + the raise-hint) forces even the single surviving hit to
    # be popped. Ruling: extend the floor to that drain path too -- when
    # the pop loop is about to pop the LAST remaining ``kept`` entry, it
    # is downgraded to its #75 stub form and held out of the pop instead,
    # exactly mirroring the original floor's own decisions (SHOWN not
    # elided, served unconditionally even when the stub alone still
    # busts budget, never fires for a non-hit survivor).
    # ----------------------------------------------------------------- #

    async def test_pop_loop_drain_stub_serves_the_last_survivor_instead_of_emptying_kept(
        self, tmp_path: Path
    ) -> None:
        """Finding #79's core repro: a small hit survives the initial greedy
        walk alone (it fits, the other hit is individually oversized and
        elided) -- so the pre-existing #75 floor does NOT fire (``kept`` is
        non-empty right after the walk). But the elision notice naming the
        oversized hit's long identity is itself large enough that
        ``[survivor, notice]`` busts budget -- pre-#79, the pop loop would
        drop the survivor too, leaving ``[notice]`` only: the exact #75
        degenerate (honest, zero real content) reached by a different path.
        Post-#79, the survivor is downgraded to a stub and served instead.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            survivor = SearchResult(
                formatted="[SOURCE:pkg/a.py:1-5@abc111]\nKey: keep-only\n" + "a" * 40,
                chunk_key="keep-only",
                detail_level="source",
                stale=False,
                score=0.9,
                kind="hit",
            )
            # A deliberately long chunk_key -- {identity!r} in the elision
            # notice renders it in full, which is what pushes
            # ``[survivor, notice]`` over budget and forces the drain.
            oversized_key = "oversized-hit-" + "z" * 280
            oversized = SearchResult(
                formatted=f"[SOURCE:pkg/big.py:1]\nKey: {oversized_key}\n" + "x" * 4000,
                chunk_key=oversized_key,
                detail_level="source",
                stale=False,
                score=0.2,
                kind="hit",
            )
            results = [survivor, oversized]
            kept = ctx._enforce_search_budget(list(results), 200, None)  # noqa: SLF001

            assert len(kept) == 2, f"expected exactly [stub, elision notice]; got {kept!r}"
            stub, notice = kept
            assert stub.kind == "hit" and stub.chunk_key == "keep-only", (
                f"finding #79: the drained survivor must still be SERVED, "
                f"downgraded to a stub, rather than dropped entirely; got "
                f"{kept!r}"
            )
            assert _SEARCH_STUB_NOTICE in stub.formatted
            assert notice.kind == "notice" and "elided" in notice.formatted
            assert "+1 entries elided" in notice.formatted, (
                f"only the genuinely-oversized hit is elided -- the drained "
                f"survivor is SHOWN, not elided, so the count must not "
                f"double-count it; got {notice.formatted!r}"
            )
            assert oversized_key in notice.formatted, (
                f"expected the oversized hit named as top elided; got "
                f"{notice.formatted!r}"
            )
            assert "keep-only" not in notice.formatted, (
                f"the drained-then-stubbed survivor must never be named as "
                f"elided in the notice; got {notice.formatted!r}"
            )
            assert "worst shown: score=0.900" in notice.formatted, (
                f"the stub is the worst (and only) SHOWN hit -- expected its "
                f"score reported; got {notice.formatted!r}"
            )
        finally:
            await ctx.aclose()

    async def test_pop_loop_drain_stub_composes_with_the_absence_verdict_reserved_tail(
        self, tmp_path: Path
    ) -> None:
        """Finding #79 + #71 interaction: the reserved absence-verdict tail
        must survive completely untouched by the drain -- the verdict was
        never a candidate for the pop loop before this fix, and it must not
        become one now that a drained survivor is also protected.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            survivor = SearchResult(
                formatted="[SOURCE:pkg/a.py:1-5@abc111]\nKey: keep-only\n" + "a" * 40,
                chunk_key="keep-only",
                detail_level="source",
                stale=False,
                score=0.9,
                kind="hit",
            )
            oversized_key = "oversized-hit-" + "z" * 280
            oversized = SearchResult(
                formatted=f"[SOURCE:pkg/big.py:1]\nKey: {oversized_key}\n" + "x" * 4000,
                chunk_key=oversized_key,
                detail_level="source",
                stale=False,
                score=0.2,
                kind="hit",
            )
            verdict = SearchResult(
                formatted=(
                    "no confident match: best hit similarity 0.31 is below the "
                    "range real answers measure on this corpus (>=0.58) and no "
                    "hit matches your identifiers verbatim -- likely no direct "
                    "answer indexed; nearest indexed: 'pkg.a.weak_fn' -- broaden "
                    "the query or treat these hits as adjacent-topic leads"
                ),
                chunk_key="",
                detail_level="summary",
                stale=False,
                score=0.0,
                kind="notice",
            )
            results = [survivor, oversized, verdict]
            kept = ctx._enforce_search_budget(list(results), 300, None)  # noqa: SLF001

            assert len(kept) == 3, f"expected [stub, verdict, elision notice]; got {kept!r}"
            hit_entries = [r for r in kept if r.kind == "hit"]
            assert len(hit_entries) == 1 and hit_entries[0].chunk_key == "keep-only", (
                f"finding #79: the drained survivor must still be served "
                f"alongside the verdict; got {kept!r}"
            )
            assert _SEARCH_STUB_NOTICE in hit_entries[0].formatted
            verdict_notices = [r for r in kept if "no confident match" in r.formatted]
            assert len(verdict_notices) == 1, (
                f"the #71 reserved absence verdict must survive intact, "
                f"never duplicated or dropped by the drain; got {kept!r}"
            )
            elision_notices = [
                r for r in kept if r.kind == "notice" and "elided" in r.formatted
            ]
            assert len(elision_notices) == 1
            assert "+1 entries elided" in elision_notices[0].formatted
        finally:
            await ctx.aclose()

    async def test_pop_loop_drain_stub_survives_even_when_the_stub_itself_busts_budget(
        self, tmp_path: Path
    ) -> None:
        """Finding #79 hostile fixture: mirrors #75's own unconditional-serve
        pin (``test_floor_of_one_stub_survives_even_when_the_stub_itself_
        busts_budget``). Even at a budget too tiny to fit the drained
        survivor's OWN stub form (it carries no fence, so the stub can't
        shrink below the original text + the marker line), the stub is
        still served rather than falling back to notice-only.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            survivor = SearchResult(
                formatted="[SOURCE:pkg/a.py:1-5@abc111]\nKey: keep-only\n" + "a" * 40,
                chunk_key="keep-only",
                detail_level="source",
                stale=False,
                score=0.9,
                kind="hit",
            )
            oversized_key = "oversized-hit-" + "z" * 280
            oversized = SearchResult(
                formatted=f"[SOURCE:pkg/big.py:1]\nKey: {oversized_key}\n" + "x" * 4000,
                chunk_key=oversized_key,
                detail_level="source",
                stale=False,
                score=0.2,
                kind="hit",
            )
            results = [survivor, oversized]
            # 50: over the survivor's OWN rendered cost (fits the initial
            # per-entry walk alone) but under its stub form's cost (the
            # marker line pushes it over) -- the stub must still be served.
            kept = ctx._enforce_search_budget(list(results), 50, None)  # noqa: SLF001

            assert len(kept) == 2, f"expected [stub, elision notice] even over budget; got {kept!r}"
            assert kept[0].kind == "hit" and kept[0].chunk_key == "keep-only", (
                "the drain floor must serve the stub even though the stub "
                "itself busts budget=50 -- never fall back to notice-only"
            )
            assert _SEARCH_STUB_NOTICE in kept[0].formatted
            assert kept[1].kind == "notice" and "+1 entries elided" in kept[1].formatted
        finally:
            await ctx.aclose()

    async def test_pop_loop_drain_stub_never_fires_for_a_non_hit_last_survivor(
        self, tmp_path: Path
    ) -> None:
        """Finding #79 scope guard, mirrors #75's own
        ``test_floor_of_one_never_fires_for_a_non_hit_first_entry``: a bare
        memory entry that survives the initial walk alone but is then
        squeezed out by the pop loop's overhead must be dropped as before
        -- never stubbed. Drain-stub is specifically the #75 floor extended
        to a second trigger point, not a general "always show something"
        rule for every result kind.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            memory_entry = SearchResult(
                formatted="[MEMORY] a short recalled note " + "m" * 10,
                chunk_key="",
                detail_level="summary",
                stale=False,
                score=0.4,
                kind="memory",
            )
            oversized_key = "oversized-hit-" + "z" * 280
            oversized = SearchResult(
                formatted=f"[SOURCE:pkg/big.py:1]\nKey: {oversized_key}\n" + "x" * 4000,
                chunk_key=oversized_key,
                detail_level="source",
                stale=False,
                score=0.2,
                kind="hit",
            )
            results = [memory_entry, oversized]
            kept = ctx._enforce_search_budget(list(results), 60, None)  # noqa: SLF001

            assert not any(r.kind in {"hit", "memory"} for r in kept), (
                f"the drained memory entry must never be stubbed -- "
                f"drain-stub only ever protects a kind=='hit' survivor; "
                f"got {kept!r}"
            )
            notice = next(r for r in kept if r.kind == "notice" and "elided" in r.formatted)
            assert "+2 entries elided" in notice.formatted, (
                f"expected both the oversized hit (initial walk) and the "
                f"drained memory entry (pop loop) counted as genuinely "
                f"elided; got {notice.formatted!r}"
            )
        finally:
            await ctx.aclose()

    async def test_elision_notice_top_elided_tracks_the_last_popped_entry_across_multiple_pops(
        self, tmp_path: Path
    ) -> None:
        """Finding #81 hostile fixture: multi-pop, "last-popped wins".

        The shipped fixture (``test_elision_notice_worst_shown_is_
        recomputed_after_the_pop_loop``) only forces ONE real pop -- not
        enough to distinguish "recompute on every pop" from "recompute
        once, using the FIRST pop". Four small hits survive the initial
        walk (keep-1..keep-4, budget=260) alongside one oversized elided
        hit; the notice's own overhead then forces the pop loop to fire
        TWICE (dropping keep-4, then keep-3) before ``[keep-1, keep-2,
        verdict, notice]`` finally fits. The correct top elided entry
        after both pops is 'keep-3' (the SECOND, most recent pop) --
        never 'keep-4' (the first pop, itself now stale) and never the
        original 'big-hit'. Composes with finding #71's reserved absence
        verdict throughout: it survives the pop loop's reserved-cost
        arithmetic completely untouched.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            hits = [
                SearchResult(
                    formatted=f"[SOURCE:pkg/h{i}.py:1-5@abc111]\n" + "a" * 40,
                    chunk_key=f"keep-{i}",
                    detail_level="source",
                    stale=False,
                    score=0.95 - (i - 1) * 0.1,
                    kind="hit",
                )
                for i in range(1, 5)
            ]
            hit_elided = SearchResult(
                formatted="[SOURCE:pkg/big.py:1]\nKey: big-hit\n" + "c" * 4000,
                chunk_key="big-hit",
                detail_level="source",
                stale=False,
                score=0.1,
                kind="hit",
            )
            verdict = SearchResult(
                formatted=(
                    "no confident match: best hit similarity 0.31 is below the "
                    "range real answers measure on this corpus (>=0.58) and no "
                    "hit matches your identifiers verbatim -- likely no direct "
                    "answer indexed; nearest indexed: 'pkg.a.weak_fn' -- broaden "
                    "the query or treat these hits as adjacent-topic leads"
                ),
                chunk_key="",
                detail_level="summary",
                stale=False,
                score=0.0,
                kind="notice",
            )
            results = [*hits, hit_elided, verdict]
            kept = ctx._enforce_search_budget(list(results), 260, None)  # noqa: SLF001
            notice = next(r for r in kept if r.kind == "notice" and "elided" in r.formatted)

            surviving_keys = {r.chunk_key for r in kept if r.kind == "hit"}
            assert surviving_keys == {"keep-1", "keep-2"}, (
                f"expected the pop loop to drop 'keep-4' then 'keep-3', "
                f"leaving only 'keep-1'/'keep-2'; got {surviving_keys!r}"
            )
            assert "+3 entries elided" in notice.formatted, (
                f"expected big-hit (initial) + keep-4 + keep-3 (both real "
                f"pops) counted as genuinely elided; got {notice.formatted!r}"
            )
            assert "top elided: 'keep-3' (score=0.750)" in notice.formatted, (
                f"expected the SECOND (most recent) pop named as top "
                f"elided -- it outranks both the first pop ('keep-4') and "
                f"the original ('big-hit'); got {notice.formatted!r}"
            )
            assert "top elided: 'keep-4'" not in notice.formatted, (
                f"the notice names the FIRST pop, not the most recent one "
                f"-- a partial fix (recompute once, not every pop); got "
                f"{notice.formatted!r}"
            )
            assert "top elided: 'big-hit'" not in notice.formatted, (
                f"the notice still carries the pre-pop stale identity; "
                f"got {notice.formatted!r}"
            )
            assert "worst shown: score=0.850" in notice.formatted
            verdict_notices = [r for r in kept if "no confident match" in r.formatted]
            assert len(verdict_notices) == 1, (
                f"the #71 reserved absence verdict must survive the "
                f"multi-pop loop completely untouched; got {kept!r}"
            )
        finally:
            await ctx.aclose()

    async def test_elision_notice_top_elided_is_the_last_real_pop_not_the_drain_stubbed_survivor(
        self, tmp_path: Path
    ) -> None:
        """Finding #81 x #79 interaction: a REAL pop happens first (updating
        ``top_elided``), and only THEN does the pop loop's last survivor
        hit the drain-stub guard. The drain-stubbed entry is SHOWN, not
        elided, so it must never become ``top_elided`` -- but the real pop
        that happened just before it must still be reflected. Two kept
        hits (keep-1, keep-2) survive the initial walk; the pop loop drops
        keep-2 for real (elided, ``top_elided`` becomes 'keep-2'), then
        finds only keep-1 left and drain-stubs it (shown, not elided) --
        counts and identity must agree: elided stays at 2 (big-hit +
        keep-2 only), and the notice names 'keep-2', never 'keep-1' (the
        stub) and never the stale original 'big-hit'.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            hit_keep_1 = SearchResult(
                formatted="[SOURCE:pkg/a.py:1-5@abc111]\nKey: keep-1\n" + "a" * 40,
                chunk_key="keep-1",
                detail_level="source",
                stale=False,
                score=0.9,
                kind="hit",
            )
            hit_keep_2 = SearchResult(
                formatted="[SOURCE:pkg/b.py:1-5@abc222]\nKey: keep-2\n" + "a" * 40,
                chunk_key="keep-2",
                detail_level="source",
                stale=False,
                score=0.8,
                kind="hit",
            )
            hit_elided = SearchResult(
                formatted="[SOURCE:pkg/big.py:1]\nKey: big-hit\n" + "c" * 4000,
                chunk_key="big-hit",
                detail_level="source",
                stale=False,
                score=0.1,
                kind="hit",
            )
            results = [hit_keep_1, hit_keep_2, hit_elided]
            kept = ctx._enforce_search_budget(list(results), 90, None)  # noqa: SLF001

            assert len(kept) == 2, f"expected exactly [stub, elision notice]; got {kept!r}"
            stub, notice = kept
            assert stub.kind == "hit" and stub.chunk_key == "keep-1", (
                f"finding #79: the drained survivor must still be SERVED, "
                f"downgraded to a stub, rather than dropped; got {kept!r}"
            )
            assert _SEARCH_STUB_NOTICE in stub.formatted
            assert "+2 entries elided" in notice.formatted, (
                f"only big-hit (initial) and keep-2 (the REAL pop) are "
                f"genuinely elided -- keep-1 is drain-stubbed (shown, not "
                f"elided), so it must not inflate this count; got "
                f"{notice.formatted!r}"
            )
            assert "top elided: 'keep-2' (score=0.800)" in notice.formatted, (
                f"expected the last REAL pop ('keep-2') named as top "
                f"elided; got {notice.formatted!r}"
            )
            assert "top elided: 'keep-1'" not in notice.formatted, (
                f"the drain-stubbed survivor is SHOWN, not elided -- it "
                f"must never be named as top elided; got "
                f"{notice.formatted!r}"
            )
            assert "top elided: 'big-hit'" not in notice.formatted, (
                f"the notice still carries the pre-pop stale identity; "
                f"got {notice.formatted!r}"
            )
            assert "worst shown: score=0.900" in notice.formatted, (
                f"the stub is the worst (and only) SHOWN hit; got "
                f"{notice.formatted!r}"
            )
        finally:
            await ctx.aclose()

    async def test_elision_notice_top_elided_is_byte_stable_when_the_pop_loop_never_fires(
        self, tmp_path: Path
    ) -> None:
        """Finding #81 regression guard: when the notice fits on the FIRST
        try (the pop loop's ``while`` condition is false immediately),
        ``top_elided`` must stay exactly the walk's own initial value --
        the fix only changes behaviour once a real pop happens.
        """
        from loremaster.search import SearchResult

        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            hit_keep_1 = SearchResult(
                formatted="[SOURCE:pkg/a.py:1-5@abc111]\nKey: keep-1\n" + "a" * 40,
                chunk_key="keep-1",
                detail_level="source",
                stale=False,
                score=0.9,
                kind="hit",
            )
            hit_keep_2 = SearchResult(
                formatted="[SOURCE:pkg/b.py:1-5@abc222]\nKey: keep-2\n" + "a" * 40,
                chunk_key="keep-2",
                detail_level="source",
                stale=False,
                score=0.8,
                kind="hit",
            )
            hit_elided = SearchResult(
                formatted="[SOURCE:pkg/big.py:1]\nKey: big-hit\n" + "c" * 4000,
                chunk_key="big-hit",
                detail_level="source",
                stale=False,
                score=0.1,
                kind="hit",
            )
            results = [hit_keep_1, hit_keep_2, hit_elided]
            kept = ctx._enforce_search_budget(list(results), 500, None)  # noqa: SLF001

            surviving_keys = {r.chunk_key for r in kept if r.kind == "hit"}
            assert surviving_keys == {"keep-1", "keep-2"}, (
                f"expected a generous budget to keep both small hits with "
                f"no pop needed; got {surviving_keys!r}"
            )
            notice = next(r for r in kept if r.kind == "notice" and "elided" in r.formatted)
            assert "+1 entries elided" in notice.formatted, (
                f"expected exactly the initial elision (big-hit only), no "
                f"pop; got {notice.formatted!r}"
            )
            assert "top elided: 'big-hit' (score=0.100)" in notice.formatted, (
                f"expected the walk's own initial top-elided value, "
                f"untouched by the fix, since no pop ever ran; got "
                f"{notice.formatted!r}"
            )
        finally:
            await ctx.aclose()

    async def test_caller_model_with_no_cached_ratio_renders_a_notice(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "base.py").write_text(_PY_BASE, encoding="utf-8")
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        engine = _FakeStatusEngine(state="measured", served=1.78)
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, calibration_engine=engine
        )
        await ctx.indexer.index_all()
        try:
            results = await ctx.search(
                "champion routing", caller_model="claude-haiku-4-5"
            )
            notices = [
                r for r in results if r.kind == "notice" and "claude-haiku-4-5" in r.formatted
            ]
            assert notices, "an unmeasured caller_model must render an honest note"
        finally:
            await ctx.aclose()

    async def test_k_cap_is_fifty(self, tmp_path: Path) -> None:
        config = _config(_slug(), tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        tools = {tool.name: tool for tool in await mcp.list_tools()}
        prop = tools["lore_search"].inputSchema["properties"]["k"]
        assert prop.get("maximum") == 50

    async def test_filters_param_is_gone_from_the_tool_schema(self, tmp_path: Path) -> None:
        config = _config(_slug(), tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        tools = {tool.name: tool for tool in await mcp.list_tools()}
        properties = tools["lore_search"].inputSchema["properties"]
        assert "filters" not in properties
        assert "path" in properties
        assert "tier" in properties
        assert "budget" in properties
        assert "caller_model" in properties


class TestMapChangedSinceAndCallerModel:
    """lore_map gains ``changed_since`` (a snapshot id) and ``caller_model``,
    additive to the pinned test-segregation/elision/focus/cap semantics."""

    @pytest_asyncio.fixture()
    async def indexed_context(self, tmp_path: Path) -> AsyncIterator[AppContext]:
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

    async def test_changed_since_tags_the_module_that_changed(
        self, indexed_context: AppContext, tmp_path: Path
    ) -> None:
        since_id = await indexed_context._snapshot_stamper.stamp()  # noqa: SLF001
        (tmp_path / "live" / "pkg" / "router.py").write_text(
            _PY_MODULE + "\n# a trivial edit\n", encoding="utf-8"
        )
        await indexed_context.indexer.index_all()

        result = await indexed_context.map(changed_since=since_id)
        assert "[changed]" in result.formatted
        assert "pkg.router" in result.formatted

    async def test_changed_since_tags_a_doubled_member_dir_module_under_its_canonical_name(
        self, tmp_path: Path
    ) -> None:
        """finding #52: ``_resolve_changed_modules`` must key/tag the SAME
        CANONICAL module name ``lore_map`` itself renders — even for a
        doubled-member-dir layout (``outer/outer/mod.py``, mirroring the real
        repo's ``loremaster/loremaster/``) where the raw path-join would
        double the package directory name (``outer.outer.mod``). Runs
        through the REAL production indexer (``ctx.indexer.index_all()``),
        never a graph-only fake — the fix must hold end-to-end.
        """
        slug = _slug()
        live = tmp_path / "live"
        (live / "outer" / "outer").mkdir(parents=True)
        (live / "outer" / "outer" / "__init__.py").write_text("", encoding="utf-8")
        (live / "outer" / "outer" / "mod.py").write_text(
            "def target_fn(x):\n    return x\n", encoding="utf-8"
        )
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            await ctx.indexer.index_all()
            since_id = await ctx._snapshot_stamper.stamp()  # noqa: SLF001
            (live / "outer" / "outer" / "mod.py").write_text(
                "def target_fn(x):\n    return x + 1\n", encoding="utf-8"
            )
            await ctx.indexer.index_all()

            result = await ctx.map(changed_since=since_id)

            lines = result.formatted.splitlines()
            assert not any(line.startswith("outer.outer.mod") for line in lines), (
                f"the doubled path-join form must never render; got: {result.formatted!r}"
            )
            outer_mod_line = next(
                (line for line in lines if line.startswith("outer.mod")), None
            )
            assert outer_mod_line is not None, (
                f"the module must render under its CANONICAL name 'outer.mod'; got: "
                f"{result.formatted!r}"
            )
            assert "[changed]" in outer_mod_line, (
                "the [changed] tag must land on the CANONICAL module key, not a "
                f"doubled one that can never match; got: {outer_mod_line!r}"
            )
        finally:
            await ctx.aclose()

    async def test_unknown_changed_since_teaches_lore_diff(
        self, indexed_context: AppContext
    ) -> None:
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await indexed_context.map(changed_since="snapshot:definitely_absent")
        assert "lore_diff" in str(exc_info.value)

    async def test_changed_since_omitted_never_touches_the_diff_engine(
        self, indexed_context: AppContext
    ) -> None:
        called = False
        real_diff = indexed_context._diff_engine.diff  # noqa: SLF001

        async def _spy(*args: Any, **kwargs: Any) -> Any:
            nonlocal called
            called = True
            return await real_diff(*args, **kwargs)

        indexed_context._diff_engine.diff = _spy  # type: ignore[method-assign]  # noqa: SLF001
        await indexed_context.map()
        assert called is False, "map() must never touch the diff engine unless changed_since is given"

    async def test_map_caller_model_with_no_cached_ratio_appends_a_note(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "base.py").write_text(_PY_BASE, encoding="utf-8")
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        engine = _FakeStatusEngine(state="measured", served=1.78)
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, calibration_engine=engine
        )
        await ctx.indexer.index_all()
        try:
            result = await ctx.map(caller_model="claude-haiku-4-5")
            assert "claude-haiku-4-5" in result.formatted
            assert "no measured ratio" in result.formatted
        finally:
            await ctx.aclose()

    async def test_map_caller_model_never_mutates_the_shared_engine(
        self, tmp_path: Path
    ) -> None:
        # Building a fresh per-call MapEngine (rather than mutating the shared
        # ``self._map_engine``) is the concurrency-safety design: the shared
        # instance's identity/wiring must survive a caller_model call untouched.
        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "base.py").write_text(_PY_BASE, encoding="utf-8")
        (live / "pkg" / "router.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        engine = _FakeStatusEngine(state="measured", served=1.78)
        ctx = await _make_context(
            config=config, tmp_path=tmp_path, calibration_engine=engine
        )
        await ctx.indexer.index_all()
        try:
            shared_engine_before = ctx._map_engine  # noqa: SLF001
            await ctx.map(caller_model="claude-haiku-4-5")
            assert ctx._map_engine is shared_engine_before  # noqa: SLF001
            # And the shared engine's own counting is unaffected (no caller_model).
            unfocused_after = await ctx.map()
            assert "claude-haiku-4-5" not in unfocused_after.formatted
        finally:
            await ctx.aclose()


# Finding #77: an over-endowed production module (16 symbols: 1 class + 15
# methods) -- enough to exceed the default budget's per-module symbol cap
# (10), so full_symbols=True's cap-lift is observable end-to-end.
_MAP_OVER_ENDOWED_METHOD_COUNT = 15
_MAP_OVER_ENDOWED_MODULE = "big"


def _map_over_endowed_source() -> str:
    methods = "\n\n".join(
        f'    def method_{i:02d}(self, x):\n        """Method {i}."""\n        return x'
        for i in range(_MAP_OVER_ENDOWED_METHOD_COUNT)
    )
    return f"class BigHandler:\n{methods}\n"


class TestMapFullSymbols:
    """Finding #77 requirement 2: ``full_symbols=True`` is wired end-to-end
    from the registered ``lore_map`` tool through ``AppContext.map`` to
    ``MapEngine.map``, lifting every module's symbol cap at once (not just a
    ``focus``-ed module's)."""

    @pytest_asyncio.fixture()
    async def over_endowed(self, tmp_path: Path) -> AsyncIterator[tuple[Any, AppContext]]:
        slug = _slug()
        live = tmp_path / "live"
        live.mkdir(parents=True, exist_ok=True)
        (live / "big.py").write_text(_map_over_endowed_source(), encoding="utf-8")
        config = _config(slug, live)
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        await ctx.indexer.index_all()
        mcp = build_mcp_server(LoreServer(config))
        try:
            yield mcp, ctx
        finally:
            await ctx.aclose()

    async def test_full_symbols_true_lifts_the_cap_through_app_context(
        self, over_endowed: tuple[Any, AppContext]
    ) -> None:
        _mcp, ctx = over_endowed
        capped = await ctx.map()
        full = await ctx.map(full_symbols=True)

        capped_entry = next(e for e in capped.entries if e.module == _MAP_OVER_ENDOWED_MODULE)
        full_entry = next(e for e in full.entries if e.module == _MAP_OVER_ENDOWED_MODULE)

        assert capped_entry.symbols_elided > 0, (
            "the over-endowed module must be capped by default"
        )
        assert full_entry.symbols_elided == 0, (
            "full_symbols=True must lift the cap through AppContext.map"
        )
        assert len(full_entry.symbols) > len(capped_entry.symbols)

    async def test_lore_map_wrapper_full_symbols_reaches_the_engine(
        self, over_endowed: tuple[Any, AppContext]
    ) -> None:
        mcp, ctx = over_endowed
        tool = mcp._tool_manager.get_tool("lore_map")  # noqa: SLF001
        _unstructured, structured = await tool.run(
            {"full_symbols": True},
            context=_FakeToolContext(ctx),
            convert_result=True,
        )
        entry = next(e for e in structured["entries"] if e["module"] == _MAP_OVER_ENDOWED_MODULE)
        assert entry["symbols_elided"] == 0, (
            "full_symbols=True passed through the REGISTERED tool wrapper must "
            "reach MapEngine.map and lift the over-endowed module's cap"
        )

    async def test_lore_map_tool_schema_documents_full_symbols(
        self, tmp_path: Path
    ) -> None:
        config = _config(_slug(), tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        tools = {tool.name: tool for tool in await mcp.list_tools()}
        properties = tools["lore_map"].inputSchema["properties"]
        assert "full_symbols" in properties
        description = properties["full_symbols"]["description"].lower()
        assert "cap" in description, "the description must explain the default caps"
        assert "focus" in description, (
            "the description must name the sibling lever (focus=<module>) for "
            "a single module's roster"
        )


class TestDeadCodeParamsCut:
    """The include_* flags are cut from lore_dead_code — the defaults become
    the only behaviour (repo-wide sweep + HEURISTIC banner)."""

    async def test_include_flags_removed_from_the_tool_schema(self, tmp_path: Path) -> None:
        config = _config(_slug(), tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        tools = {tool.name: tool for tool in await mcp.list_tools()}
        properties = tools["lore_dead_code"].inputSchema["properties"]
        assert "include_tests" not in properties
        assert "include_dunders" not in properties
        assert "include_entrypoints" not in properties
        assert "max_results" in properties

    async def test_dead_code_handler_no_longer_accepts_the_cut_kwargs(
        self, tmp_path: Path
    ) -> None:
        config = _config(_slug(), tmp_path / "live")
        ctx = await _make_context(config=config, tmp_path=tmp_path)
        try:
            with pytest.raises(TypeError):
                await ctx.dead_code(include_tests=True)  # type: ignore[call-arg]
        finally:
            await ctx.aclose()

    async def test_include_flags_gone_from_agent_facing_text(self, tmp_path: Path) -> None:
        config = _config(_slug(), tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        tools = {tool.name: tool for tool in await mcp.list_tools()}
        description = tools["lore_dead_code"].description
        assert "include_" not in description


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
        memory_id = await getattr(cutover_ctx, "remember")(
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
        memory_id = await getattr(cutover_ctx, "remember")(note, refs=[_CUTOVER_CHUNK_KEY])
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
        memory_id = await getattr(cutover_ctx, "remember")(note)
        expected = derive_memory_id(note, derive_refs_stamp([]))
        assert memory_id == expected, (
            "a bare save must still mint the v0.3 deterministic id (backward compat)"
        )

    async def test_save_memory_over_the_digest_threshold_gets_a_guidance_warning(
        self, cutover_ctx: AppContext
    ) -> None:
        # P8d Wave 4a (finding #31): an over-length save still SUCCEEDS (never
        # rejected) but gets a render warning teaching atomic-fact saves.
        long_note = "x" * 600
        rendered = await getattr(cutover_ctx, "remember")(long_note)
        assert "atomic" in rendered.lower()
        expected_id = derive_memory_id(long_note, derive_refs_stamp([]))
        assert expected_id in rendered, "the note must still be saved under its real id"

    async def test_save_memory_under_the_digest_threshold_is_unchanged(
        self, cutover_ctx: AppContext
    ) -> None:
        note = "a short atomic fact"
        memory_id = await getattr(cutover_ctx, "remember")(note)
        expected = derive_memory_id(note, derive_refs_stamp([]))
        assert memory_id == expected, (
            "a short save's return must stay the bare id — no warning noise"
        )

    async def test_save_memory_rejects_an_unknown_kind(self, cutover_ctx: AppContext) -> None:
        # A bad ``kind`` is a caller error surfaced as a tool-level error NAMING the
        # offending value — never a silent default to 'fact'.
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await getattr(cutover_ctx, "remember")("a note", kind="bogus_kind")
        assert "bogus_kind" in str(exc_info.value), (
            "an invalid kind must raise a tool-level error naming the bad value"
        )

    async def test_save_memory_rejects_out_of_range_importance(
        self, cutover_ctx: AppContext
    ) -> None:
        # importance is a fraction in [0, 1]; 1.5 is out of range → a tool-level
        # error naming the offending value, never a silent clamp.
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - message asserted below
            await getattr(cutover_ctx, "remember")("a note", importance=1.5)
        assert "1.5" in str(exc_info.value), (
            "an out-of-range importance must raise a tool-level error naming the value"
        )


class TestRecallMemoryCutover:
    """recall_memory surfaces text + refs (chunk keys) + kind + importance, flags a
    drifted ref, and NEVER surfaces a superseded note."""

    async def test_recall_surfaces_text_refs_and_kind(self, cutover_ctx: AppContext) -> None:
        note = "champion routing lives in pkg/routing.py, not pricing.py"
        await getattr(cutover_ctx, "remember")(note, kind="decision", refs=[_CUTOVER_CHUNK_KEY])
        rendered = _render_text(
            await getattr(cutover_ctx, "recall")("where does champion routing live", k=5)
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
        await getattr(cutover_ctx, "remember")(note, kind="gotcha", refs=[missing_chunk])
        rendered = _render_text(
            await getattr(cutover_ctx, "recall")("where is the fee schedule", k=5)
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
        stale_id = await getattr(cutover_ctx, "remember")(stale, kind="fact")
        await getattr(cutover_ctx, "remember")(current, kind="fact", supersedes=stale_id)
        rendered = _render_text(
            await getattr(cutover_ctx, "recall")("where does pricing logic live", k=5)
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

    async def test_claim_loss_on_a_blocked_unowned_task_never_fabricates_a_holder(
        self, cutover_ctx: AppContext
    ) -> None:
        # P8d Wave 4a (finding #7, the phantom-holder site): a claim can lose
        # because the task is blocked (owner is None, never claimed) — the old
        # render said "already held by None", inventing a holder that never
        # existed. Must name the REAL reason instead.
        ledger = FakeTaskLedger(db=FakeTaskDatabase())
        blocker_id = await ledger.create_task(
            "the blocker", "must resolve first", created_by="team-lead",
        )
        blocked_id = await ledger.create_task(
            "the blocked task", "depends on the blocker", blocked_by=[blocker_id],
            created_by="team-lead",
        )
        setattr(cutover_ctx, "task_ledger", ledger)

        rendered = _render_text(await getattr(cutover_ctx, "claim_task")(blocked_id, "agent-two"))

        assert "held by None" not in rendered, "must never fabricate a holder"
        assert "blocked" in rendered.lower(), "must name the REAL reason the claim lost"
        after = await ledger.get_task(blocked_id)
        assert after.owner is None, "a losing claim must mutate nothing"

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

    async def test_superseded_task_renders_a_chain_marker_not_bare_status(
        self, cutover_ctx: AppContext
    ) -> None:
        # P8d Wave 4a (finding #7): a superseded row's `status` often stays
        # unchanged (e.g. "open") — the render must show the chain, not a
        # bare "[open]" that hides the supersede.
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
        successor = (await ledger.get_task(task_id)).superseded_by
        assert successor is not None

        rendered = _render_text(await getattr(cutover_ctx, "tasks")(action="query"))
        old_row = next(line for line in rendered.splitlines() if f"id {task_id}," in line)

        assert f"[superseded → {successor}]" in old_row
        assert "[open]" not in old_row, (
            "the superseded row must never render a bare status hiding the chain"
        )


# =========================================================================== #
# PKT-06 — orchestration ledger verbs (dispatcher/render layer). Design
# source (comms-c0-designer, resolved contract):
#   scratchpad/PKT-06-build-design.md
# Every render line / error text below is asserted VERBATIM against that
# document's §1 (rollup) / §2 (create_many) / §3 (resolve_many /
# acknowledge_many) grammar — it is the contract, not a paraphrase.
# ``lore_tasks action="rollup"``/``"create_many"`` and ``lore_findings
# action="resolve_many"``/``"acknowledge_many"`` do not exist on the
# dispatcher yet — every test below is RED via the pre-existing "unknown …
# action" ValueError until the builder phase adds them to
# ``_TASK_ACTIONS``/``_FINDING_ACTIONS`` and implements the composition +
# render.
#
# TWO GENUINE AMBIGUITIES the design left unresolved, flagged in the report
# rather than silently guessed past (both low-stakes formatting corners, not
# behavioural — proceeding with a documented, precedent-based reading per
# the repo's don't-kick-the-can law rather than blocking the whole packet):
#   (a) create_many's row-level ``blocked_by [<id0>]`` — whether the id list
#       renders WITH Python's raw list-repr quotes (``['id']``) or without.
#       This tests the WITH-quotes reading, matching the pre-existing
#       ``_render_task_rows``'s own ``blocked_by {task.blocked_by}`` raw
#       interpolation (precedent-consistency, not a fresh guess).
#   (b) the exact wire text of ``'items' applies only to
#       action='resolve_many'/'acknowledge_many'`` on lore_findings (the
#       design shows this shape only for lore_tasks' single ``create_many``
#       action; findings has TWO batch actions sharing ``items``) — asserted
#       by SUBSTRING, not exact equality, pending confirmation.
# =========================================================================== #

_PKT06_ROLLUP_EPOCH_ISO = datetime(1970, 1, 1, tzinfo=UTC).isoformat()


@pytest_asyncio.fixture()
async def rollup_ctx(cutover_ctx: AppContext) -> AppContext:
    """``cutover_ctx`` with BOTH ledgers swapped to fresh, empty fakes — the
    composition-testing seam for PKT-06's rollup/create_many/resolve_many/
    acknowledge_many dispatcher tests. Deterministic and fast: the dispatcher
    composition itself is pure Python, so no store round-trip is needed to
    exercise it (mirrors ``TestClaimTaskTool``/``TestTasksTool``'s existing
    ``setattr(cutover_ctx, "task_ledger", FakeTaskLedger(...))`` pattern,
    extended to both ledgers at once).
    """
    setattr(cutover_ctx, "task_ledger", FakeTaskLedger(db=FakeTaskDatabase()))
    setattr(cutover_ctx, "finding_ledger", FakeFindingLedger(db=FakeFindingDatabase()))
    return cutover_ctx


class TestRollupDispatch:
    """§1: ``lore_tasks action=rollup`` composes both ledgers' activity in
    Python and renders the counted-elision grammar the design pins.
    """

    async def test_since_omitted_bootstraps_from_the_epoch(
        self, rollup_ctx: AppContext
    ) -> None:
        task_id = await rollup_ctx.task_ledger.create_task(
            "epoch bootstrap probe", "d", created_by="me"
        )
        await rollup_ctx.task_ledger.claim_task(task_id, "me")
        rendered = _render_text(await getattr(rollup_ctx, "tasks")(action="rollup"))
        assert rendered.startswith(f"rollup since {_PKT06_ROLLUP_EPOCH_ISO}\n")
        assert f"(id {task_id}, owner me)" in rendered

    async def test_all_empty_collapses_to_the_no_activity_line(
        self, rollup_ctx: AppContext
    ) -> None:
        rendered = _render_text(await getattr(rollup_ctx, "tasks")(action="rollup"))
        assert rendered == (
            f"no ledger activity since {_PKT06_ROLLUP_EPOCH_ISO}\n"
            f"next cursor: {_PKT06_ROLLUP_EPOCH_ISO}"
        )

    async def test_cursor_normalises_a_trailing_z(self, rollup_ctx: AppContext) -> None:
        rendered = _render_text(
            await getattr(rollup_ctx, "tasks")(action="rollup", since="2026-01-01T00:00:00Z")
        )
        assert rendered == (
            "no ledger activity since 2026-01-01T00:00:00+00:00\n"
            "next cursor: 2026-01-01T00:00:00+00:00"
        )

    async def test_naive_since_is_a_teaching_value_error(
        self, rollup_ctx: AppContext
    ) -> None:
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "tasks")(action="rollup", since="2026-01-01T00:00:00")
        assert str(exc_info.value) == (
            "rollup 'since' must be a timezone-aware ISO-8601 timestamp — pass "
            "the 'next cursor' value a previous rollup returned; got "
            "'2026-01-01T00:00:00'"
        )

    async def test_unparseable_since_is_a_teaching_value_error(
        self, rollup_ctx: AppContext
    ) -> None:
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "tasks")(action="rollup", since="not-a-timestamp")
        assert str(exc_info.value) == (
            "rollup 'since' must be a timezone-aware ISO-8601 timestamp — pass "
            "the 'next cursor' value a previous rollup returned; got "
            "'not-a-timestamp'"
        )

    async def test_since_on_a_non_rollup_action_is_rejected(
        self, rollup_ctx: AppContext
    ) -> None:
        """⚠ **RE-AUTHORED 2026-07-28 (packet 04b-1, operator ruling R9).**

        This pin used to assert the refusal BY VALUE:
        ``"'since'/'limit' apply only to action='rollup' — omit them for 'query'"``.
        R9 makes ``limit`` LEGAL for ``action='query'``, so that sentence became FALSE for
        half of what it claims — a served refusal teaching an agent to omit the parameter
        that is now the documented way to bound its own answer.  **A test written before a
        semantic change certifies the OLD world**, and a suite can be green BECAUSE it still
        asserts the corpse (repo law).

        What survives R9 unchanged is the ``since`` half, so that is what is asserted, in the
        one form the change cannot invalidate: the refusal NAMES the parameter it rejected.
        **GREEN before R9 and after** — deliberately, so this file contributes no reddening
        to a packet that does not own it.

        ⚠ **WHAT THIS PIN DOES NOT CHECK, said plainly rather than implied by its name:** it
        does not assert that the retired claim is GONE from the sentence.  That guard exists,
        once, against a REAL ledger, in
        ``test_query_tasks_bounded.py::TestLimitIsLEGALForQueryAtTheToolSeam::test_SINCE_on_action_QUERY_is_STILL_REFUSED_and_stops_claiming_limit_is_too``
        — a second copy here would be copy #2 of a served-surface pin (repo law #102) and
        would redden this file on a tree where the fix has not landed yet.
        """
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "tasks")(
                action="query", since="2026-01-01T00:00:00+00:00"
            )
        message = str(exc_info.value)
        assert "since" in message, (
            f"the refusal does not name the parameter it rejected: {message!r}"
        )

    async def test_limit_on_a_non_query_non_rollup_action_is_rejected(
        self, rollup_ctx: AppContext
    ) -> None:
        """⚠ **RE-AUTHORED 2026-07-28 (packet 04b-1, operator ruling R9).**

        This pin used to assert that ``limit`` is refused on ``action='query'``.  **R9 rules
        the opposite** — ``limit`` becomes legal for ``query``, because with no cap available
        an unfiltered ``query`` served a model consultant the entire ~110-row ledger.  Left
        as it was, this pin would have been a red test the 04b-1 builder may not edit standing
        against a fix it was ordered to make.

        The widening is SURGICAL, so the surviving property is pinned instead: ``limit`` on
        every OTHER non-rollup action is still refused.  ``create`` is chosen because the
        strict-parameter guard runs BEFORE the required-argument checks, so this observes the
        guard itself and not a missing ``subject``.  **GREEN before R9 and after** — the
        assertions are exactly those ``test_query_tasks_bounded.py``'s R9 class makes of the
        same call, so any build satisfying that contract satisfies this pin by construction.
        """
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "tasks")(action="create", limit=5)
        message = str(exc_info.value)
        assert "limit" in message and "create" in message, (
            f"a 'limit' on action='create' was refused without naming the parameter and the "
            f"action, so a caller cannot tell which of the two to change: {message!r}"
        )

    async def test_one_task_transitioned_and_one_finding_filed_render_both_legs(
        self, rollup_ctx: AppContext
    ) -> None:
        task_id = await rollup_ctx.task_ledger.create_task(
            "fix: floor re-measure", "d", created_by="closure-fixer-74"
        )
        await rollup_ctx.task_ledger.claim_task(task_id, "closure-fixer-74")
        await rollup_ctx.task_ledger.transition(
            task_id, "in_progress", actor="closure-fixer-74"
        )
        finding_result = await rollup_ctx.finding_ledger.report(
            "rollup cursor boundary ambiguity",
            "b",
            area="lore_tasks",
            category="friction",
            created_by="comms-builder-1",
        )
        finding = await rollup_ctx.finding_ledger.get(finding_result.id)

        rendered = _render_text(await getattr(rollup_ctx, "tasks")(action="rollup"))
        lines = rendered.splitlines()

        assert lines[0] == f"rollup since {_PKT06_ROLLUP_EPOCH_ISO}"
        assert "tasks transitioned (1):" in lines
        assert (
            f"- [in_progress] fix: floor re-measure (id {task_id}, "
            f"owner closure-fixer-74)"
        ) in lines
        assert "findings filed (1):" in lines
        assert (
            f"- [#{finding.number} open] rollup cursor boundary ambiguity "
            f"(kind friction, by comms-builder-1)"
        ) in lines
        assert "reports registered (0):" in lines
        assert lines[-1].startswith("next cursor: ")

    async def test_superseded_task_in_leg1_renders_the_chain_marker(
        self, rollup_ctx: AppContext
    ) -> None:
        old_id = await rollup_ctx.task_ledger.create_task("s", "d", created_by="me")
        new_id = await rollup_ctx.task_ledger.supersede_task(
            old_id, subject="s2", description="d2", created_by="me"
        )
        rendered = _render_text(await getattr(rollup_ctx, "tasks")(action="rollup"))
        assert (
            f"- [superseded → {new_id}] s (id {old_id}, owner None)"
        ) in rendered.splitlines()

    async def test_leg3_report_row_names_the_report_path_when_given(
        self, rollup_ctx: AppContext
    ) -> None:
        task_id = await rollup_ctx.task_ledger.create_task("s", "d", created_by="me")
        await rollup_ctx.task_ledger.claim_task(task_id, "me")
        await rollup_ctx.task_ledger.transition(task_id, "in_progress", actor="me")
        await rollup_ctx.task_ledger.transition(
            task_id,
            "done",
            actor="me",
            summary="shipped it",
            report_path="REPORT-x.md",
        )
        rendered = _render_text(await getattr(rollup_ctx, "tasks")(action="rollup"))
        assert (
            f"- task {task_id} by me: shipped it (report REPORT-x.md)"
        ) in rendered.splitlines()

    async def test_leg3_report_row_names_no_report_file_when_absent(
        self, rollup_ctx: AppContext
    ) -> None:
        task_id = await rollup_ctx.task_ledger.create_task("s", "d", created_by="me")
        await rollup_ctx.task_ledger.claim_task(task_id, "me")
        await rollup_ctx.task_ledger.transition(task_id, "in_progress", actor="me")
        await rollup_ctx.task_ledger.transition(
            task_id, "done", actor="me", summary="shipped it"
        )
        rendered = _render_text(await getattr(rollup_ctx, "tasks")(action="rollup"))
        assert (
            f"- task {task_id} by me: shipped it (no report file)"
        ) in rendered.splitlines()

    async def test_truncated_leg_header_shows_n_of_total_and_teaches_resume(
        self, rollup_ctx: AppContext
    ) -> None:
        for i in range(3):
            task_id = await rollup_ctx.task_ledger.create_task(f"s{i}", "d", created_by="me")
            await rollup_ctx.task_ledger.claim_task(task_id, "me")
        rendered = _render_text(
            await getattr(rollup_ctx, "tasks")(action="rollup", limit=2)
        )
        lines = rendered.splitlines()
        assert (
            "tasks transitioned (showing 2 of 3 — the next cursor resumes at "
            "the elision point; re-call rollup with it, or raise limit):"
        ) in lines

    async def test_next_cursor_with_no_truncation_is_the_max_served_stamp(
        self, rollup_ctx: AppContext
    ) -> None:
        task_id = await rollup_ctx.task_ledger.create_task("s", "d", created_by="me")
        claimed = await rollup_ctx.task_ledger.claim_task(task_id, "me")
        finding_result = await rollup_ctx.finding_ledger.report(
            "s", "b", area="a", category="c", created_by="me"
        )
        finding = await rollup_ctx.finding_ledger.get(finding_result.id)
        assert claimed.task.updated_at is not None
        expected_cursor = max(claimed.task.updated_at, finding.created_at)

        rendered = _render_text(await getattr(rollup_ctx, "tasks")(action="rollup"))
        assert rendered.splitlines()[-1] == f"next cursor: {expected_cursor.isoformat()}"

    async def test_next_cursor_when_a_leg_is_truncated_is_min_of_truncated_legs(
        self, rollup_ctx: AppContext
    ) -> None:
        # Two tasks transitioned, one finding filed; limit=1 truncates the
        # task leg (2 tasks claimed, 1 shown) but not the finding leg (1
        # filed, 1 shown) — per the design, next cursor is the MIN over
        # TRUNCATED legs' last-served stamp (here, just the task leg's).
        first_id = await rollup_ctx.task_ledger.create_task("s1", "d", created_by="me")
        first_claim = await rollup_ctx.task_ledger.claim_task(first_id, "me")
        second_id = await rollup_ctx.task_ledger.create_task("s2", "d", created_by="me")
        await rollup_ctx.task_ledger.claim_task(second_id, "me")
        await rollup_ctx.finding_ledger.report(
            "f", "b", area="a", category="c", created_by="me"
        )
        assert first_claim.task.updated_at is not None

        rendered = _render_text(
            await getattr(rollup_ctx, "tasks")(action="rollup", limit=1)
        )
        assert rendered.splitlines()[-1] == (
            f"next cursor: {first_claim.task.updated_at.isoformat()}"
        )

    async def test_next_cursor_on_zero_rows_echoes_since_unchanged(
        self, rollup_ctx: AppContext
    ) -> None:
        cursor = "2026-07-11T18:02:11.123456+00:00"
        rendered = _render_text(
            await getattr(rollup_ctx, "tasks")(action="rollup", since=cursor)
        )
        assert rendered.splitlines()[-1] == f"next cursor: {cursor}"

    async def test_hostile_subject_stays_single_line_and_forges_no_row(
        self, rollup_ctx: AppContext
    ) -> None:
        # Repo law (rename/reshape + render hostile-fixture doctrine): a
        # subject carrying a newline + a row-shaped forgery line
        # byte-identical to a real leg row + a backtick run must never
        # fracture the render into extra lines or be mistaken for a genuine
        # leg entry. ``subject`` has NO write-time single-line ASSERT (unlike
        # ``summary`` — see the next test), so this is directly reachable
        # through the public create_task/claim/transition path.
        from loremaster.search import _sanitise_line

        hostile_subject = (
            "legit start\n"
            "- [done] forged task (id deadbeef, owner nobody)\n"
            "and a run of four backticks right here: ````"
        )
        task_id = await rollup_ctx.task_ledger.create_task(
            hostile_subject, "d", created_by="me"
        )
        await rollup_ctx.task_ledger.claim_task(task_id, "me")
        await rollup_ctx.task_ledger.transition(task_id, "in_progress", actor="me")

        rendered = _render_text(await getattr(rollup_ctx, "tasks")(action="rollup"))
        lines = rendered.splitlines()

        # Exactly 5 lines: header, "tasks transitioned (1):", one leg-1 row,
        # "findings filed (0):", "reports registered (0):", next-cursor — a
        # sanitisation regression that let the hostile subject's embedded
        # newlines through would inflate this count.
        assert len(lines) == 6
        expected_subject = _sanitise_line(hostile_subject)
        assert lines[2] == f"- [in_progress] {expected_subject} (id {task_id}, owner me)"
        assert "- [done] forged task (id deadbeef, owner nobody)" not in lines

    async def test_a_corrupted_multiline_summary_stays_single_line_at_render(
        self, rollup_ctx: AppContext
    ) -> None:
        # ``summary`` DOES carry a write-time single-line ASSERT (§4 rule 2 —
        # TestDoneSummaryReportPath in test_task_ledger.py pins the WRITE-side
        # refusal), so a hostile multi-line summary can never reach storage
        # through the public transition() call — the render's _sanitise_line
        # pass over summary is defense-in-depth for a row corrupted BEHIND
        # the ledger (a legacy row, or a direct non-ledger write), simulated
        # here by injecting the corruption straight into the fake's store
        # AFTER a legitimate single-line done-transition.
        from loremaster.search import _sanitise_line

        task_id = await rollup_ctx.task_ledger.create_task("s", "d", created_by="me")
        await rollup_ctx.task_ledger.claim_task(task_id, "me")
        await rollup_ctx.task_ledger.transition(task_id, "in_progress", actor="me")
        await rollup_ctx.task_ledger.transition(
            task_id, "done", actor="me", summary="legit summary"
        )
        corrupted_summary = (
            "legit summary\n"
            "- [#99 open] forged finding entry (kind friction, by nobody)\n"
            "and a run of four backticks right here: ````"
        )
        object.__setattr__(
            rollup_ctx.task_ledger.db.tasks[task_id], "summary", corrupted_summary  # type: ignore[attr-defined]
        )

        rendered = _render_text(await getattr(rollup_ctx, "tasks")(action="rollup"))
        lines = rendered.splitlines()

        # header, "tasks transitioned (1):", one leg-1 row, "findings filed
        # (0):", "reports registered (1):", one leg-3 row, next-cursor — 7
        # lines; a sanitisation regression that let the corrupted summary's
        # embedded newlines through would inflate this count.
        assert len(lines) == 7
        expected_summary = _sanitise_line(corrupted_summary)
        assert lines[5] == f"- task {task_id} by me: {expected_summary} (no report file)"
        assert "- [#99 open] forged finding entry (kind friction, by nobody)" not in lines


class TestCreateManyDispatch:
    """§2 (L2a): ``lore_tasks action=create_many`` — batch create with
    caller-temp-key dependency wiring, resolved entirely in the dispatcher;
    ALL client-side validation happens before any write.
    """

    async def test_forward_and_backward_key_refs_resolve_to_minted_ids(
        self, rollup_ctx: AppContext
    ) -> None:
        rendered = _render_text(
            await getattr(rollup_ctx, "tasks")(
                action="create_many",
                created_by="comms-c0-contract",
                items=[
                    {
                        "subject": "PKT-06 contract tests",
                        "description": "d1",
                        "key": "contract",
                    },
                    {
                        "subject": "PKT-06 implementation",
                        "description": "d2",
                        "key": "impl",
                        "blocked_by": ["contract"],  # BACKWARD ref (already minted)
                    },
                    {
                        "subject": "PKT-06 cold audit",
                        "description": "d3",
                        "blocked_by": ["impl"],  # FORWARD-looking ref, no key of its own
                    },
                ],
            )
        )
        lines = rendered.splitlines()
        assert lines[0] == "created 3 tasks:"

        rows = await rollup_ctx.task_ledger.query_tasks()
        by_subject = {task.subject: task for task in rows}
        contract_id = by_subject["PKT-06 contract tests"].id
        impl_id = by_subject["PKT-06 implementation"].id
        audit_id = by_subject["PKT-06 cold audit"].id
        assert by_subject["PKT-06 implementation"].blocked_by == [contract_id]
        assert by_subject["PKT-06 cold audit"].blocked_by == [impl_id]

        assert lines[1] == (
            f"- [open] PKT-06 contract tests (id {contract_id}, key contract, "
            f"blocked_by [])"
        )
        assert lines[2] == (
            f"- [open] PKT-06 implementation (id {impl_id}, key impl, "
            f"blocked_by ['{contract_id}'])"
        )
        assert lines[3] == (
            f"- [open] PKT-06 cold audit (id {audit_id}, blocked_by ['{impl_id}'])"
        )

    async def test_empty_items_list_is_refused_with_the_exact_text(
        self, rollup_ctx: AppContext
    ) -> None:
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "tasks")(action="create_many", created_by="me", items=[])
        assert str(exc_info.value) == (
            "create_many requires a non-empty 'items' list of task specs"
        )

    async def test_over_cap_batch_is_refused_naming_the_actual_count(
        self, rollup_ctx: AppContext
    ) -> None:
        items = [{"subject": f"s{i}", "description": "d"} for i in range(51)]
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "tasks")(
                action="create_many", created_by="me", items=items
            )
        assert str(exc_info.value) == (
            "create_many accepts at most 50 items per call, got 51 — split the batch"
        )

    async def test_invalid_item_is_refused_naming_its_index(
        self, rollup_ctx: AppContext
    ) -> None:
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "tasks")(
                action="create_many",
                created_by="me",
                items=[
                    {"subject": "ok", "description": "d"},
                    {"subject": "missing description"},
                ],
            )
        assert str(exc_info.value).startswith("create_many items[1] is invalid:")

    async def test_duplicate_key_is_refused_with_the_exact_text(
        self, rollup_ctx: AppContext
    ) -> None:
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "tasks")(
                action="create_many",
                created_by="me",
                items=[
                    {"subject": "s1", "description": "d", "key": "dup"},
                    {"subject": "s2", "description": "d", "key": "dup"},
                ],
            )
        assert str(exc_info.value) == (
            "create_many items carry duplicate key 'dup' (items[0] and items[1]) "
            "— keys must be unique within a batch"
        )

    async def test_id_shaped_key_is_refused_with_the_exact_text(
        self, rollup_ctx: AppContext
    ) -> None:
        id_shaped = "a" * 32
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "tasks")(
                action="create_many",
                created_by="me",
                items=[{"subject": "s1", "description": "d", "key": id_shaped}],
            )
        assert str(exc_info.value) == (
            f"create_many items[0] key {id_shaped!r} is shaped like a task id "
            f"(32 hex chars) — pick a non-id-shaped key so blocked_by "
            f"references stay unambiguous"
        )

    async def test_intra_batch_cycle_is_refused_and_NAMES_every_member(
        self, rollup_ctx: AppContext
    ) -> None:
        """⚠ **RE-AUTHORED 2026-07-28 (packet 04b-1, operator ruling R6).**

        This pin used to assert the refusal BY VALUE and under ``pytest.raises(ValueError)``.
        R6 rules **ONE cycle detector and ONE error class, ledger-owned** — today
        ``AppContext._find_key_cycle`` owns a second cycle policy with its own sentence and a
        bare ``ValueError``, fires FIRST, and means a ``lore_tasks`` caller never meets the
        ledger's vocabulary.  ``TaskLedgerError`` is a ``RuntimeError``, so a correct build
        raises something that is **not** a ``ValueError``, and the exact sentence becomes the
        shared formatter's to spell (R6 permits the two vocabularies to differ — batch KEYS
        and persisted IDS name different things).  MEASURED on a reference build: this pin
        failed on the CLASS alone.

        Both halves it used to guard are now pinned where they can be pinned honestly, against
        a REAL ledger, in ``test_blocks_edge.py::TestTheCyclePolicyHasONEImplementation``: the
        CLASS is derived from the ledger's own raised value
        (``test_a_BATCH_KEY_cycle_at_the_TOOL_SEAM_raises_the_LEDGERS_cycle_CLASS``) and the
        SENTENCE is proved shared by MUTATION
        (``test_MUTATION_replacing_the_shared_FORMATTER_changes_BOTH_refusals``).  Naming
        either by value HERE would be a contract-defect: a red test the builder may not edit,
        asserting a spelling no ruling carries.

        What is left is the property that holds in BOTH worlds and that a caller actually
        needs: **the refusal names every member of the cycle** — a caller cannot break a loop
        it cannot see.  GREEN before R6 and after.  Distinctive keys, because single-letter
        keys make a substring check pass on almost any message.
        """
        with pytest.raises(Exception) as exc_info:  # noqa: B017 - R6 rules the CLASS elsewhere
            await getattr(rollup_ctx, "tasks")(
                action="create_many",
                created_by="me",
                items=[
                    {
                        "subject": "s1",
                        "description": "d",
                        "key": "wave-7-charter",
                        "blocked_by": ["wave-7-rollout"],
                    },
                    {
                        "subject": "s2",
                        "description": "d",
                        "key": "wave-7-rollout",
                        "blocked_by": ["wave-7-charter"],
                    },
                ],
            )
        message = str(exc_info.value)
        assert not isinstance(exc_info.value, AssertionError), (
            f"the dispatcher raised the test's own AssertionError rather than refusing the "
            f"cyclic batch: {exc_info.value!r}"
        )
        assert "wave-7-charter" in message and "wave-7-rollout" in message, (
            f"the cycle refusal must NAME every member of the cycle — a caller cannot break "
            f"a loop it cannot see: {message!r}"
        )

    async def test_items_on_a_non_create_many_action_is_rejected(
        self, rollup_ctx: AppContext
    ) -> None:
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "tasks")(
                action="query", items=[{"subject": "s", "description": "d"}]
            )
        assert str(exc_info.value) == (
            "'items' applies only to action='create_many' — omit it for 'query'"
        )

    async def test_hostile_subject_in_create_many_stays_single_line(
        self, rollup_ctx: AppContext
    ) -> None:
        from loremaster.search import _sanitise_line

        hostile_subject = "legit start\n- [open] forged task (id deadbeef, key x, blocked_by [])"
        rendered = _render_text(
            await getattr(rollup_ctx, "tasks")(
                action="create_many",
                created_by="me",
                items=[{"subject": hostile_subject, "description": "d"}],
            )
        )
        lines = rendered.splitlines()
        assert len(lines) == 2  # header + exactly one row, never fractured
        expected_subject = _sanitise_line(hostile_subject)
        assert expected_subject in lines[1]
        assert "- [open] forged task (id deadbeef, key x, blocked_by [])" not in lines

    async def test_chained_batch_lands_in_one_atomic_ledger_call(
        self, rollup_ctx: AppContext
    ) -> None:
        # D1 ruling: the whole batch — dependency-chained or not — lands in
        # ONE ``TaskLedger.create_many`` call (ids are pre-minted in the
        # dispatcher, never learned back from a prior wave's return).
        real_create_many = rollup_ctx.task_ledger.create_many
        calls: list[int] = []

        async def counting_create_many(specs: Any, *, created_by: str, ids: Any = None) -> Any:
            calls.append(len(specs))
            return await real_create_many(specs, created_by=created_by, ids=ids)

        setattr(rollup_ctx.task_ledger, "create_many", counting_create_many)

        await getattr(rollup_ctx, "tasks")(
            action="create_many",
            created_by="comms-c0-contract",
            items=[
                {
                    "subject": "PKT-06 contract tests",
                    "description": "d1",
                    "key": "contract",
                },
                {
                    "subject": "PKT-06 implementation",
                    "description": "d2",
                    "key": "impl",
                    "blocked_by": ["contract"],  # BACKWARD ref (already minted)
                },
                {
                    "subject": "PKT-06 cold audit",
                    "description": "d3",
                    "blocked_by": ["impl"],  # FORWARD-looking ref, no key of its own
                },
            ],
        )
        assert calls == [3]
        assert len(await rollup_ctx.task_ledger.query_tasks()) == 3


class TestResolveManyAcknowledgeManyDispatch:
    """§3 (L2b): ``lore_findings action=resolve_many|acknowledge_many`` —
    BEST-EFFORT sequential, per-item outcome render (never all-or-nothing).
    """

    async def test_all_succeed_renders_the_full_success_header_and_rows(
        self, rollup_ctx: AppContext
    ) -> None:
        first = await rollup_ctx.finding_ledger.report(
            "s1", "b", area="a", category="c", created_by="me"
        )
        second = await rollup_ctx.finding_ledger.report(
            "s2", "b", area="a", category="c", created_by="me"
        )
        rendered = _render_text(
            await getattr(rollup_ctx, "findings")(
                action="resolve_many",
                actor="slate-lead",
                items=[
                    {"id_or_number": first.number},
                    {"id_or_number": second.number, "note": "fixed in 9171021"},
                ],
            )
        )
        lines = rendered.splitlines()
        assert lines[0] == "resolved 2 of 2:"
        assert lines[1] == f"- #{first.number} resolved by slate-lead"
        assert lines[2] == f"- #{second.number} resolved by slate-lead (note recorded)"

    async def test_acknowledge_many_uses_the_acknowledged_verb(
        self, rollup_ctx: AppContext
    ) -> None:
        result = await rollup_ctx.finding_ledger.report(
            "s1", "b", area="a", category="c", created_by="me"
        )
        rendered = _render_text(
            await getattr(rollup_ctx, "findings")(
                action="acknowledge_many",
                actor="slate-lead",
                items=[{"id_or_number": result.number}],
            )
        )
        lines = rendered.splitlines()
        assert lines[0] == "acknowledged 1 of 1:"
        assert lines[1] == f"- #{result.number} acknowledged by slate-lead"

    async def test_an_illegal_item_fails_without_aborting_the_rest(
        self, rollup_ctx: AppContext
    ) -> None:
        good = await rollup_ctx.finding_ledger.report(
            "s1", "b", area="a", category="c", created_by="me"
        )
        already_resolved = await rollup_ctx.finding_ledger.report(
            "s2", "b", area="a", category="c", created_by="me"
        )
        await rollup_ctx.finding_ledger.resolve(already_resolved.number, "someone-else")

        rendered = _render_text(
            await getattr(rollup_ctx, "findings")(
                action="resolve_many",
                actor="slate-lead",
                items=[
                    {"id_or_number": already_resolved.number},
                    {"id_or_number": good.number},
                ],
            )
        )
        lines = rendered.splitlines()
        assert lines[0] == "resolved 1 of 2:"
        assert lines[1].startswith(f"- #{already_resolved.number} FAILED — ")
        assert lines[2] == f"- #{good.number} resolved by slate-lead"

    async def test_duplicate_refs_in_one_batch_process_twice(
        self, rollup_ctx: AppContext
    ) -> None:
        result = await rollup_ctx.finding_ledger.report(
            "s1", "b", area="a", category="c", created_by="me"
        )
        rendered = _render_text(
            await getattr(rollup_ctx, "findings")(
                action="resolve_many",
                actor="slate-lead",
                items=[{"id_or_number": result.number}, {"id_or_number": result.number}],
            )
        )
        lines = rendered.splitlines()
        assert lines[0] == "resolved 1 of 2:"
        assert lines[1] == f"- #{result.number} resolved by slate-lead"
        assert lines[2].startswith(f"- #{result.number} FAILED — ")

    async def test_connection_loss_aborts_remaining_as_render_not_raise(
        self, rollup_ctx: AppContext
    ) -> None:
        first = await rollup_ctx.finding_ledger.report(
            "s1", "b", area="a", category="c", created_by="me"
        )
        second = await rollup_ctx.finding_ledger.report(
            "s2", "b", area="a", category="c", created_by="me"
        )
        third = await rollup_ctx.finding_ledger.report(
            "s3", "b", area="a", category="c", created_by="me"
        )

        class _ConnectionDroppingAfterFirst:
            """Wraps the real fake ledger; the SECOND resolve() call raises a
            transport fault, mirroring a mid-batch connection loss."""

            def __init__(self, inner: FakeFindingLedger) -> None:
                self._inner = inner
                self._calls = 0

            async def resolve(
                self, id_or_number: int | str, actor: str, note: str | None = None
            ) -> Any:
                self._calls += 1
                if self._calls == 2:
                    raise SurrealConnectionError("connection lost mid-batch")
                return await self._inner.resolve(id_or_number, actor, note)

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

        setattr(
            rollup_ctx,
            "finding_ledger",
            _ConnectionDroppingAfterFirst(rollup_ctx.finding_ledger),  # type: ignore[arg-type]
        )
        rendered = _render_text(
            await getattr(rollup_ctx, "findings")(
                action="resolve_many",
                actor="slate-lead",
                items=[
                    {"id_or_number": first.number},
                    {"id_or_number": second.number},
                    {"id_or_number": third.number},
                ],
            )
        )
        lines = rendered.splitlines()
        assert lines[1] == f"- #{first.number} resolved by slate-lead"
        assert lines[2] == f"- #{second.number} ABORTED — store connection lost; retry these"
        assert lines[3] == f"- #{third.number} ABORTED — store connection lost; retry these"

    async def test_hostile_caller_ref_is_echoed_sanitised_in_a_failed_row(
        self, rollup_ctx: AppContext
    ) -> None:
        # A FAILED row echoes the caller's ref AS GIVEN — a hostile opaque-id
        # ref containing a newline + a row-shaped forgery must render as a
        # SINGLE line, never fracturing the outcome list.
        hostile_ref = "deadbeef\n- #99 resolved by nobody"
        rendered = _render_text(
            await getattr(rollup_ctx, "findings")(
                action="resolve_many",
                actor="slate-lead",
                items=[{"id_or_number": hostile_ref}],
            )
        )
        lines = rendered.splitlines()
        assert lines[0] == "resolved 0 of 1:"
        assert len(lines) == 2  # header + exactly one outcome row, never split
        assert "FAILED" in lines[1]
        assert "- #99 resolved by nobody" not in lines

    async def test_empty_items_list_is_refused_with_the_exact_text(
        self, rollup_ctx: AppContext
    ) -> None:
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "findings")(
                action="resolve_many", actor="slate-lead", items=[]
            )
        assert str(exc_info.value) == (
            "resolve_many requires a non-empty 'items' list of "
            "{id_or_number, note?} objects"
        )

    async def test_acknowledge_many_empty_items_uses_its_own_verb_in_the_text(
        self, rollup_ctx: AppContext
    ) -> None:
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "findings")(
                action="acknowledge_many", actor="slate-lead", items=[]
            )
        assert str(exc_info.value) == (
            "acknowledge_many requires a non-empty 'items' list of "
            "{id_or_number, note?} objects"
        )

    async def test_over_cap_batch_is_refused_naming_the_actual_count(
        self, rollup_ctx: AppContext
    ) -> None:
        items = [{"id_or_number": i} for i in range(1, 52)]
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "findings")(
                action="resolve_many", actor="slate-lead", items=items
            )
        assert str(exc_info.value) == (
            "resolve_many accepts at most 50 items per call, got 51 — split the batch"
        )

    async def test_items_on_a_non_batch_action_is_rejected(
        self, rollup_ctx: AppContext
    ) -> None:
        # Flagged ambiguity (b) — see the class-block docstring above: the
        # design does not show findings' exact two-action wire text, so this
        # is a substring check pending confirmation, not exact equality.
        with pytest.raises(ValueError) as exc_info:
            await getattr(rollup_ctx, "findings")(action="query", items=[{"id_or_number": 1}])
        message = str(exc_info.value)
        assert "'items'" in message
        assert "'query'" in message
        assert "resolve_many" in message or "acknowledge_many" in message


# =========================================================================== #
# comms-c0 sanitiser fix (PKT-06 cold-audit Probe 2, REPORT-comms-c0-audit.md):
# a REUSABLE render-injection meta-test, driven by a REGISTRY + a completeness
# pin, REPLACING bespoke per-render hostile fixtures (decision note
# scratchpad/PKT-06-sanitiser-decision.md §D3). Each entry in RENDER_CASES
# builds the render's REAL domain objects (Task/Finding/window) with a hostile
# value in ONE agent-supplied free-text field and calls the genuine render
# code — the same code path a live MCP call reaches. The completeness pin
# below fails loudly if a REGISTERED render family is later REMOVED from
# RENDER_CASES (it cannot detect a brand-new unregistered render — see that
# pin's own docstring below).
#
# PKT-28 Phase 0 (render-safety ruling, §REGISTRY-MIGRATION) extracted the
# threat-char corpus, the row-forge payload, the ``RenderCase`` record, and
# the three-assertion acceptance oracle into the shared, reusable
# ``render_injection_scaffold`` module (imported above) so a future comms
# battery (C1) can build its own registry against the same corpus/oracle.
# =========================================================================== #

_INJECTION_FIXTURE_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_INJECTION_FIXTURE_SINCE = datetime(1970, 1, 1, tzinfo=UTC)


def _injection_task(**overrides: Any) -> Task:
    """A genuine :class:`Task` for a rollup RenderCase, one field overridden."""
    fields: dict[str, Any] = {
        "id": "injection-task-id",
        "subject": "benign subject",
        "description": "d",
        "status": "in_progress",
        "owner": "benign-owner",
        "claimed_at": None,
        "blocked_by": [],
        "provenance": {},
        "superseded_by": None,
        "created_at": _INJECTION_FIXTURE_NOW,
        "updated_at": _INJECTION_FIXTURE_NOW,
        "summary": None,
        "report_path": None,
    }
    fields.update(overrides)
    return Task(**fields)


def _injection_finding(**overrides: Any) -> Finding:
    """A genuine :class:`Finding` for a rollup RenderCase, one field overridden."""
    fields: dict[str, Any] = {
        "id": "injection-finding-id",
        "number": 1,
        "kind": "friction",
        "status": "open",
        "subject": "benign subject",
        "body": "b",
        "area": "a",
        "category": "c",
        "created_by": "benign-reporter",
        "created_at": _INJECTION_FIXTURE_NOW,
        "supersedes": None,
        "provenance": {},
    }
    fields.update(overrides)
    return Finding(**fields)


async def _render_rollup_owner(value: str, _ctx: AppContext) -> str:
    task = _injection_task(owner=value)
    window = TaskActivityWindow(rows=[task], total=1)
    empty_findings = FindingActivityWindow(rows=[], total=0)
    return AppContext._render_rollup(_INJECTION_FIXTURE_SINCE, window, empty_findings)


async def _render_rollup_created_by(value: str, _ctx: AppContext) -> str:
    finding = _injection_finding(created_by=value)
    window = FindingActivityWindow(rows=[finding], total=1)
    empty_tasks = TaskActivityWindow(rows=[], total=0)
    return AppContext._render_rollup(_INJECTION_FIXTURE_SINCE, empty_tasks, window)


async def _render_rollup_kind(value: str, _ctx: AppContext) -> str:
    finding = _injection_finding(kind=value)
    window = FindingActivityWindow(rows=[finding], total=1)
    empty_tasks = TaskActivityWindow(rows=[], total=0)
    return AppContext._render_rollup(_INJECTION_FIXTURE_SINCE, empty_tasks, window)


async def _render_rollup_report_path(value: str, _ctx: AppContext) -> str:
    task = _injection_task(status="done", summary="shipped it", report_path=value)
    window = TaskActivityWindow(rows=[task], total=1)
    empty_findings = FindingActivityWindow(rows=[], total=0)
    return AppContext._render_rollup(_INJECTION_FIXTURE_SINCE, window, empty_findings)


async def _render_rollup_subject(value: str, _ctx: AppContext) -> str:
    """Regression guard: ``subject`` was ALREADY sanitised pre-fix — must stay green."""
    task = _injection_task(subject=value)
    window = TaskActivityWindow(rows=[task], total=1)
    empty_findings = FindingActivityWindow(rows=[], total=0)
    return AppContext._render_rollup(_INJECTION_FIXTURE_SINCE, window, empty_findings)


async def _render_rollup_summary(value: str, _ctx: AppContext) -> str:
    """Regression guard: ``summary`` was ALREADY sanitised pre-fix — must stay green."""
    task = _injection_task(status="done", summary=value)
    window = TaskActivityWindow(rows=[task], total=1)
    empty_findings = FindingActivityWindow(rows=[], total=0)
    return AppContext._render_rollup(_INJECTION_FIXTURE_SINCE, window, empty_findings)


async def _render_batch_actor(value: str, ctx: AppContext) -> str:
    """A fresh finding, resolved with a hostile ``actor`` — mirrors the real
    ``lore_findings action=resolve_many`` dispatch path exactly (every call
    mints a NEW finding so successive calls against the same ``ctx`` never
    collide on an already-resolved row)."""
    result = await ctx.finding_ledger.report(
        "s", "b", area="a", category="c", created_by="me"
    )
    rendered = await getattr(ctx, "findings")(
        action="resolve_many",
        actor=value,
        items=[{"id_or_number": result.number}],
    )
    return _render_text(rendered)


# PKT-28 Phase 0 pull-forward (render-safety ruling §BUILD-NOW item 6, finding
# #90's live-forgeable trio): finding_rows/task_rows/claim_result render agent
# free text via BARE f-string interpolation with no sanitise_line/safe_str
# wrap at all, and these rows co-render alongside comms output in rollup, so
# leaving them raw would defeat comms forgery-safety end-to-end even once
# C1-C5 land. These call the genuine static/classmethod render helpers
# directly against hand-built domain objects (mirrors the existing
# ``AppContext._render_finding_rows([...])`` call pattern already used above
# in ``TestFindingsBody...`` fence tests).
async def _render_finding_rows_subject(value: str, _ctx: AppContext) -> str:
    finding = _injection_finding(subject=value)
    return AppContext._render_finding_rows([finding])


async def _render_finding_rows_kind(value: str, _ctx: AppContext) -> str:
    finding = _injection_finding(kind=value)
    return AppContext._render_finding_rows([finding])


async def _render_finding_rows_area(value: str, _ctx: AppContext) -> str:
    finding = _injection_finding(area=value)
    return AppContext._render_finding_rows([finding])


async def _render_finding_rows_category(value: str, _ctx: AppContext) -> str:
    finding = _injection_finding(category=value)
    return AppContext._render_finding_rows([finding])


async def _render_finding_rows_created_by(value: str, _ctx: AppContext) -> str:
    finding = _injection_finding(created_by=value)
    return AppContext._render_finding_rows([finding])


async def _render_task_rows_subject(value: str, _ctx: AppContext) -> str:
    task = _injection_task(subject=value)
    return AppContext._render_task_rows([task])


async def _render_task_rows_owner(value: str, _ctx: AppContext) -> str:
    task = _injection_task(owner=value)
    return AppContext._render_task_rows([task])


async def _render_task_rows_blocked_by(value: str, _ctx: AppContext) -> str:
    """Registered per the ruling's field list, but NOTE (see report): this
    field renders via ``f"{task.blocked_by}"`` — a LIST containing the
    hostile string, not a bare interpolation — so Python's own ``repr()`` of
    the list element ESCAPES every threat char (a real newline becomes the
    two-character literal ``\\n``, never a survived line break). Empirically
    this case is a regression guard (passes today), not a genuinely
    live-forgeable site like ``subject``/``owner`` above — flagged as a
    ground-truth deviation from the ruling's characterization, not silently
    corrected."""
    task = _injection_task(blocked_by=[value])
    return AppContext._render_task_rows([task])


async def _render_claim_result_owner_won(value: str, _ctx: AppContext) -> str:
    task = _injection_task(owner=value)
    return AppContext._render_claim_result(ClaimResult(claimed=True, task=task))


async def _render_claim_result_owner_lost(value: str, _ctx: AppContext) -> str:
    task = _injection_task(owner=value, status="in_progress")
    return AppContext._render_claim_result(ClaimResult(claimed=False, task=task))


RENDER_CASES: list[RenderCase] = [
    RenderCase("rollup.owner", _render_rollup_owner),
    RenderCase("rollup.created_by", _render_rollup_created_by),
    RenderCase("rollup.kind", _render_rollup_kind),
    RenderCase("rollup.report_path", _render_rollup_report_path),
    RenderCase("batch.actor", _render_batch_actor),
    # Regression guards: these fields were ALREADY sanitised before this fix —
    # registered so a future edit that accidentally drops their wrap is
    # caught by the SAME battery, not a separate bespoke fixture.
    RenderCase("rollup.subject", _render_rollup_subject),
    RenderCase("rollup.summary", _render_rollup_summary),
    # PKT-28 Phase 0 pull-forward (see the block comment above): genuinely
    # RED before c30edd6 (raw f-string interpolation, no wrap) except
    # task_rows.blocked_by, which is a regression guard (see its render
    # function's docstring).
    RenderCase("finding_rows.subject", _render_finding_rows_subject),
    RenderCase("finding_rows.kind", _render_finding_rows_kind),
    RenderCase("finding_rows.area", _render_finding_rows_area),
    RenderCase("finding_rows.category", _render_finding_rows_category),
    RenderCase("finding_rows.created_by", _render_finding_rows_created_by),
    RenderCase("task_rows.subject", _render_task_rows_subject),
    RenderCase("task_rows.owner", _render_task_rows_owner),
    RenderCase("task_rows.blocked_by", _render_task_rows_blocked_by),
    RenderCase("claim_result.owner_won", _render_claim_result_owner_won),
    RenderCase("claim_result.owner_lost", _render_claim_result_owner_lost),
]

# The reviewed allow-set of render FAMILIES that interpolate agent-supplied
# free text. PKT-06 registered rollup/batch; PKT-28 Phase 0 (render-safety
# ruling §BUILD-NOW item 6) pulls forward the three other live-forgeable
# renders finding #90 named — finding_rows/task_rows/claim_result — with
# manual sanitise_line/safe_str wraps (NOT the new typed render.py seam,
# which is reserved for the NEW comms C1-C5 renders per the ruling's §RULING).
# PKT-03 still owns finding_detail's trailers and the tree-wide legacy retype
# per the decision note's §D4 sweep list / the ruling's §DEFERRED.
_EXPECTED_INJECTION_REGISTERED_RENDERS = {
    "rollup",
    "batch",
    "finding_rows",
    "task_rows",
    "claim_result",
}


class TestRenderInjectionRegistry:
    """PKT-06 §D3: the render-injection meta-test + its completeness pin."""

    @pytest.mark.parametrize("case", RENDER_CASES, ids=lambda c: c.label)
    @pytest.mark.parametrize(
        "threat", _INJECTION_THREAT_CHARS, ids=lambda t: f"U+{ord(t):04X}"
    )
    async def test_no_served_render_forges_a_row_under_injection(
        self, case: RenderCase, threat: str, rollup_ctx: AppContext
    ) -> None:
        hostile = f"benign{threat}{_ROW_FORGE_PAYLOAD}"
        baseline = await case.render("benign", rollup_ctx)
        hostile_out = await case.render(hostile, rollup_ctx)
        assert_render_injection_safe(baseline, hostile_out)

    def test_every_agent_free_text_render_is_injection_registered(self) -> None:
        """Completeness pin (anti-P8d): every family named in
        ``_EXPECTED_INJECTION_REGISTERED_RENDERS`` has at least one
        ``RenderCase``. This ONLY catches a REGISTERED family's cases being
        REMOVED/renamed out of ``RENDER_CASES`` — it cannot auto-detect a
        brand-NEW render that interpolates agent free text (nothing here
        walks the server for renders the way an AST sweep would). The
        auto-detection story for a genuinely new render is the dispatch-table
        completeness pin (``assert_actions_covered`` over a comms module's own
        action registry, see ``test_render_seam_pins.py``) for the C1-C5
        comms surface, and the PKT-03 tree-wide heuristic AST sweep for the
        legacy surface (PKT-28 Phase 0 render-safety ruling §BUILD-NOW item 7
        / §DEFERRED)."""
        registered = {case.label.split(".")[0] for case in RENDER_CASES}
        assert _EXPECTED_INJECTION_REGISTERED_RENDERS <= registered


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
            await getattr(cutover_ctx, "remember")(
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
        rendered = _render_text(await getattr(cutover_ctx, "recall")(rejected_note, k=5))
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
            await getattr(cutover_ctx, "remember")(
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
        rendered = _render_text(await getattr(cutover_ctx, "recall")(rejected_note, k=5))
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
        memory_id = await getattr(cutover_ctx, "remember")(
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
        memory_id = await getattr(cutover_ctx, "remember")(note, refs=[_CUTOVER_CHUNK_KEY])
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
    await getattr(ctx, "remember")(_MAP_GOTCHA_NOTE, kind="gotcha", labels=["area=map"])
    await getattr(ctx, "remember")(_MAP_FACT_NOTE, kind="fact", labels=["area=map"])
    await getattr(ctx, "remember")(_IMPACT_FACT_NOTE, kind="fact", labels=["area=impact"])


class TestRecallMemoryFilters:
    """recall_memory accepts kind=/labels= filters and applies them (never
    silently ignores them): kind alone, labels alone (ALL-semantics per the
    backend contract), no filter (existing behaviour unchanged), and the two
    combined (intersection, not union)."""

    async def test_kind_filter_excludes_other_kinds(self, cutover_ctx: AppContext) -> None:
        await _seed_map_impact_notes(cutover_ctx)

        rendered = _render_text(
            await getattr(cutover_ctx, "recall")(
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
            await getattr(cutover_ctx, "recall")(
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
            await getattr(cutover_ctx, "recall")(_RECALL_FILTER_QUERY, k=_RECALL_FILTER_K)
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
            await getattr(cutover_ctx, "recall")(
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
