"""CONTRACT tests for P5-C6 (ledger #27): the ``loremaster.scout`` write-role daemon.

The scout is the SINGLE-WRITER process for a project's unified SurrealDB index: it
composes the FULL write stack (store / manifest / code-graph / snapshot-stamper /
indexer / reconcile-engine / live-watcher) from ``lore.yaml``, runs the eager
initial sweep + live watch + periodic reconcile, and services an out-of-band
``command`` table (LIVE-primary, poll-fallback) so an operator can nudge it. It is
deliberately SEPARATE from the read-side MCP server: importing the scout must NOT
drag in FastMCP (the daemon has no HTTP surface).

This file is written BLIND to any implementation — the module does not exist yet.
It DEFINES the interface:

* ``loremaster.scout.Scout`` — the driveable daemon (tests drive the class).
* ``loremaster.scout.CommandSubscriber`` — the LIVE-primary + poll-fallback +
  reconnect command reader (seams: ``live_select_statement`` /
  ``process_pending_once`` / ``run`` / ``stop``).
* ``loremaster.scout.UnknownCommandError`` — raised by ``Scout.handle_command`` on
  an unrecognised ``kind``.
* ``loremaster.scout.build_parser`` / ``main`` — the ``python -m loremaster.scout``
  argparse entrypoint (``--config`` + ``--snapshot-root``), with the ``__main__``
  guard as the LAST top-level statement (mirrors ``test_server_entrypoint``).

Adversarial pre-flight (every entry → a case, or a scoped-out note):

1. Wrong unit — the periodic reconcile interval is SECONDS (``reconcile_interval_s``),
   not milliseconds and not ``debounce_ms``. → ``TestScoutStartupSequence.
   test_periodic_reconcile_interval_is_the_config_value_in_seconds``.
2. LIVE WHERE with a BOUND PARAM (the SDK forbids params in a LIVE WHERE — a naive
   ``$status`` bind silently delivers NOTHING). → ``TestLiveSelectStatement`` +
   ``TestCommandSubscriberTransport.test_run_issues_filtered_live_select_without_a_status_param``.
3. Whole-table ``.live(table)`` instead of a filtered ``LIVE SELECT`` (re-fires on
   every done/failed transition → re-dispatch storm). → same as (2): ``.live()``
   must NOT be used.
4. NOT replayed on reconnect (the SDK orphans the live queue on a socket drop) →
   commands inserted during the gap must be recovered by POLL. →
   ``TestCommandSubscriberTransport.test_reconnect_recovers_a_command_inserted_during_the_gap``.
5. Double-processing on a LIVE+poll race. → same reconnect case pins each command
   dispatched EXACTLY once (idempotence by processed-count).
6. Degenerate empty command table (no pending) → no dispatch, no crash. →
   ``TestCommandDispatchAgainstRealSchema`` (a no-op ``process_pending_once``).
7. ``watcher.enabled=False`` sweep-only mode: the initial sweep + command channel
   still run; the live observer + periodic task do NOT. →
   ``TestScoutStartupSequence.test_sweep_only_mode_indexes_once_but_never_watches``.
8. Producer↔consumer seam: the ``command.status`` domain is exactly
   {pending, done, failed} (a schema ASSERT). The scout's status writes are pinned
   against the REAL engine so a stray ``'processing'``/``'complete'`` is caught. →
   ``TestCommandDispatchAgainstRealSchema`` (asserts the real status column, using
   the schema module's OWN status constants — clause 5).
9. Store DOWN at startup → a loud TYPED failure (not a hang), opened resources
   closed. → ``TestScoutHonestFailure``.
10. Store DROPS mid-run → the subscriber reconnects with BOUNDED backoff. →
    ``TestCommandSubscriberTransport.test_reconnect_*`` +
    ``test_bounded_backoff_between_reconnect_attempts``.
11. A handler exception must NOT kill the loop (the command is failed; the scout
    keeps serving). → ``TestCommandDispatchAgainstRealSchema.
    test_handler_exception_marks_failed_and_scout_survives``.
12. Snapshot wiring inert (C4-audit #2): the scout must inject the stamper into
    BOTH the indexer and the reconcile engine, else snapshots never stamp. →
    ``TestScoutCompositionRoot.test_from_config_wires_the_snapshot_stamper`` +
    the real-sweep ``TestScoutSweepStampsSnapshot``.
13. Command ordering vs the periodic sweep — a command sweep never RACES the
    periodic sweep (both serialize on the watcher's single-writer lock). →
    ``TestCommandDispatchPolicy.test_reconcile_command_serializes_on_the_writer_lock``.

Five-clause realism checklist is reported at the end of the CONTRACT hand-off.

Guarded-import RED strategy (mirrors ``test_indexer_snapshot_wiring``): the
``loremaster.scout`` module does not exist yet, so the import is guarded and the
symbols resolve to ``None``. Constructing ``Scout(...)`` / ``CommandSubscriber(...)``
then raises ``TypeError`` — a behavioural RED at fixture/act time, not a whole-file
collection error. The module-structure pins import inside the test body (a clean
per-test RED). Harness-backed cases run against the REAL 3.1.5 dev server via the
shared ``_surreal_harness`` per-test-DB isolation.
"""

from __future__ import annotations

import ast
import asyncio
import contextlib
import inspect
import logging
import signal
import subprocess
import sys
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from _surreal_harness import (
    PRODUCTION_DIM,
    TIER_A,
    SurrealEnv,
    connect_admin,
    run,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
    )
from loremaster.config import LoreConfig
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.indexer import Indexer, graph_roots
from loremaster.index.reconcile import ReconcileEngine, ReconcileSummary
from loremaster.index.snapshots import SnapshotStamper
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.index.watcher import LiveWatcher
from loremaster.server import LoreServer
from loremaster.store.surreal import SurrealConnectionError, SurrealStore

# The command table + its status DOMAIN, imported from the schema module — the
# SAME source of truth production writes against (clause 5). A hand-copied
# ``'done'`` literal could silently drift from the schema's ASSERT; importing the
# constant makes the drift impossible.
from loremaster.store.surreal_schema import (
    _COMMAND_STATUS_DONE,
    _COMMAND_STATUS_FAILED,
    _COMMAND_STATUS_PENDING,
    COMMAND_TABLE,
    SNAPSHOT_TABLE,
)
from loresigil.testing import FakeEmbedder

try:
    from loremaster.scout import (
        CommandSubscriber,
        Scout,
        UnknownCommandError,
        build_parser,
        main,
    )

    _SCOUT_API_AVAILABLE = True
except ImportError:  # pragma: no cover - pre-P5-C6 RED: the module does not exist
    _SCOUT_API_AVAILABLE = False
    CommandSubscriber = None  # type: ignore[assignment,misc]
    Scout = None  # type: ignore[assignment,misc]
    UnknownCommandError = None  # type: ignore[assignment,misc]
    build_parser = None  # type: ignore[assignment]
    main = None  # type: ignore[assignment]


_DIM = PRODUCTION_DIM

# The command ``kind`` the requirement names for "run a reconcile sweep now"
# (ledger #27, deliverable 4a). This is the CONTRACT's own definition of the
# command vocabulary, not a transcription of any implementation.
_RECONCILE_KIND = "reconcile"

# A distinctive, prime interval so the seconds-vs-milliseconds bug is unmissable:
# a fixture reading ``debounce_ms`` (1500) or converting to ms (137_000) fails the
# equality, only the correct SECONDS value (137) passes.
_RECONCILE_INTERVAL_S = 137

_PRICING_SOURCE = "def compute_margin(cost, price):\n    return price - cost\n"


# --------------------------------------------------------------------------- #
# Config builder (production-shaped; the harness dev server when ``env`` given)
# --------------------------------------------------------------------------- #
def _config(
    *,
    slug: str,
    live_path: Path,
    watcher_enabled: bool = True,
    reconcile_interval_s: int = _RECONCILE_INTERVAL_S,
    env: SurrealEnv | None = None,
) -> LoreConfig:
    """A single-live-root config at the production embedding dim.

    ``env`` threads the harness dev-server URL + per-test database when a real
    stack is built; omitted, the SurrealConfig defaults apply (fine for the
    construction-only / fake-collaborator tests that never open a socket).
    """
    surreal_block: dict[str, Any] = {"user_env": "SURREAL_USER", "password_env": "SURREAL_PASS"}
    if env is not None:
        surreal_block = {
            "url": env.url,
            "namespace": env.namespace,
            "database": env.database,
            "user_env": "SURREAL_USER",
            "password_env": "SURREAL_PASS",
        }
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://tei.example:8080",
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
        "surreal": surreal_block,
        "roots": [
            {
                "tier": TIER_A,
                "watch": "live",
                "path": str(live_path),
                "include": ["**/*.py"],
                "exclude": [],
            }
        ],
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": watcher_enabled,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": reconcile_interval_s,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9202},
    }
    return LoreConfig.model_validate(payload)


def _empty_reconcile_summary(*, files_indexed: int = 0) -> ReconcileSummary:
    """A well-formed zero-ish summary a fake ``run_sweep`` returns."""
    return ReconcileSummary(
        files_indexed=files_indexed,
        files_failed=0,
        files_skipped=0,
        tiers_rebuilt=[],
        tiers_skipped=[],
        outcomes=[],
        files_purged=0,
    )


async def _wait_until(predicate: Callable[[], bool], *, timeout: float = 2.0) -> None:
    """Poll ``predicate`` until true or ``timeout`` seconds elapse (else assert)."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError(f"condition not met within {timeout}s")


# =========================================================================== #
# Fakes for the composition / startup / shutdown / dispatch pins
# =========================================================================== #
class _FakeReadyClosable:
    """A store/manifest/graph/stamper stand-in recording ready/close + order."""

    def __init__(
        self, *, name: str, order: list[Any], ensure_ready_error: BaseException | None = None
    ) -> None:
        self.name = name
        self._order = order
        self._error = ensure_ready_error
        self.ensure_ready_calls = 0
        self.close_calls = 0

    async def ensure_ready(self) -> None:
        self.ensure_ready_calls += 1
        self._order.append(("ready", self.name))
        if self._error is not None:
            raise self._error

    async def close(self) -> None:
        self.close_calls += 1
        self._order.append(("close", self.name))


class _FakeWatcher:
    """A LiveWatcher stand-in whose ``run_sweep`` really holds a single-writer lock."""

    def __init__(self, *, order: list[Any] | None = None) -> None:
        self._order = order if order is not None else []
        self.writer_lock = asyncio.Lock()
        self.run_sweep_calls = 0
        self.start_calls = 0
        self.stop_calls = 0

    async def run_sweep(self) -> ReconcileSummary:
        async with self.writer_lock:
            self.run_sweep_calls += 1
            self._order.append(("sweep",))
            return _empty_reconcile_summary()

    async def start(self) -> None:
        self.start_calls += 1
        self._order.append(("watcher_start",))

    async def stop(self) -> None:
        self.stop_calls += 1
        self._order.append(("watcher_stop",))


class _FailingWatcher:
    """A watcher whose ``run_sweep`` always raises — pins handler-exception → failed."""

    def __init__(self) -> None:
        self.writer_lock = asyncio.Lock()

    async def run_sweep(self) -> ReconcileSummary:
        raise RuntimeError("reconcile sweep exploded")

    async def start(self) -> None:  # pragma: no cover - not reached in these tests
        pass

    async def stop(self) -> None:
        pass


class _FakeCommandSubscriber:
    """A subscriber stand-in whose ``run`` parks until cancelled; records start/stop."""

    def __init__(self) -> None:
        self.run_calls = 0
        self.stop_calls = 0

    async def run(self) -> None:
        self.run_calls += 1
        await asyncio.Event().wait()  # park forever (cancelled at teardown)

    async def stop(self) -> None:
        self.stop_calls += 1


class _RecordingSleep:
    """A ``sleep`` seam that records each delay then parks (until cancelled).

    Lets the periodic-reconcile loop's FIRST awaited interval be inspected without
    the loop spinning — the parked ``wait`` is cancelled when the scout stops.
    """

    def __init__(self) -> None:
        self.delays: list[float] = []
        self._gate = asyncio.Event()

    async def __call__(self, delay: float) -> None:
        self.delays.append(delay)
        await self._gate.wait()


def _fake_scout(
    *,
    config: LoreConfig,
    order: list[Any],
    store: _FakeReadyClosable | None = None,
    manifest: _FakeReadyClosable | None = None,
    graph: _FakeReadyClosable | None = None,
    stamper: _FakeReadyClosable | None = None,
    watcher: Any = None,
    subscriber: _FakeCommandSubscriber | None = None,
    sleep: _RecordingSleep | None = None,
) -> Any:
    """Construct a ``Scout`` wired entirely to in-memory fakes (no sockets)."""
    return Scout(
        config=config,
        store=store or _FakeReadyClosable(name="store", order=order),
        manifest=manifest or _FakeReadyClosable(name="manifest", order=order),
        code_graph=graph or _FakeReadyClosable(name="graph", order=order),
        snapshot_stamper=stamper or _FakeReadyClosable(name="stamper", order=order),
        indexer=object(),
        reconcile_engine=object(),
        watcher=watcher or _FakeWatcher(order=order),
        command_subscriber=subscriber or _FakeCommandSubscriber(),
        sleep=sleep or _RecordingSleep(),
    )


# =========================================================================== #
# 1) Module structure + entrypoint (import/main-guard pins ONLY)
# =========================================================================== #
class TestScoutModuleIsFastMcpFree:
    """Importing the write-role daemon must NOT drag in the FastMCP read server."""

    def test_importing_scout_does_not_import_fastmcp(self) -> None:
        # A FRESH interpreter (not this polluted test process, which imports the
        # server) so the assertion reflects ONLY loremaster.scout's import graph.
        # The scout is a write daemon with no HTTP surface — pulling FastMCP would
        # load an entire unused server stack into every scout process.
        code = (
            "import sys\n"
            "import loremaster.scout\n"
            "bad = sorted(m for m in sys.modules if 'fastmcp' in m.lower())\n"
            "assert not bad, f'scout import pulled in FastMCP: {bad}'\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        )
        assert result.returncode == 0, (
            f"importing loremaster.scout must not import FastMCP (rc="
            f"{result.returncode}):\n{result.stderr}"
        )


class TestScoutMainGuard:
    """The ``__main__`` guard is the LAST top-level statement (def-after-guard bug)."""

    @staticmethod
    def _is_main_guard(node: ast.stmt) -> bool:
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
            return False
        left = node.test.left
        return isinstance(left, ast.Name) and left.id == "__name__"

    def test_main_guard_is_last_top_level_statement(self) -> None:
        import loremaster.scout  # imported here so absence is a per-test RED

        source = Path(loremaster.scout.__file__).read_text(encoding="utf-8")
        body = ast.parse(source).body
        guard_positions = [i for i, node in enumerate(body) if self._is_main_guard(node)]
        assert guard_positions, "scout.py has no `if __name__ == '__main__'` guard"
        assert guard_positions[-1] == len(body) - 1, (
            "the `__main__` guard must be the LAST top-level statement in scout.py; "
            "a def/binding after it never executes under `python -m loremaster.scout`"
        )


class TestScoutArgparse:
    """``build_parser`` exposes ``--config`` (required) and ``--snapshot-root``."""

    def test_parses_config_and_snapshot_root(self) -> None:
        args = build_parser().parse_args(
            ["--config", "/etc/lore/lore.yaml", "--snapshot-root", "/data/snap"]
        )
        assert args.config == "/etc/lore/lore.yaml"
        assert args.snapshot_root == "/data/snap"

    def test_snapshot_root_defaults_to_none_when_omitted(self) -> None:
        args = build_parser().parse_args(["--config", "/etc/lore/lore.yaml"])
        # Omitted ⇒ None (the impl substitutes its default snapshot root later).
        assert args.snapshot_root is None

    def test_config_is_required(self) -> None:
        # A missing --config is a hard, loud argparse error (SystemExit), never a
        # silent run against an implicit config.
        with pytest.raises(SystemExit):
            build_parser().parse_args([])

    def test_main_is_callable(self) -> None:
        # The asyncio entrypoint exists and is callable (its behaviour is pinned via
        # the driveable Scout class, per the brief — this is just the surface pin).
        assert callable(main)


# =========================================================================== #
# 2) Startup sequence (fakes)
# =========================================================================== #
class TestScoutStartupSequence:
    """``Scout.start`` readies the stack, runs the eager sweep, then goes live."""

    async def test_ensure_ready_runs_on_all_four_backends_before_the_initial_sweep(
        self, tmp_path: Path
    ) -> None:
        order: list[Any] = []
        store = _FakeReadyClosable(name="store", order=order)
        manifest = _FakeReadyClosable(name="manifest", order=order)
        graph = _FakeReadyClosable(name="graph", order=order)
        stamper = _FakeReadyClosable(name="stamper", order=order)
        watcher = _FakeWatcher(order=order)
        config = _config(slug="s", live_path=tmp_path / "live")
        scout = _fake_scout(
            config=config, order=order, store=store, manifest=manifest,
            graph=graph, stamper=stamper, watcher=watcher,
        )
        try:
            await scout.start()
            for _ in range(5):
                await asyncio.sleep(0)
            # All four write backends were readied ...
            assert store.ensure_ready_calls == 1
            assert manifest.ensure_ready_calls == 1
            assert graph.ensure_ready_calls == 1
            assert stamper.ensure_ready_calls == 1
            # ... and EVERY ready happened before the first sweep (a sweep against
            # an un-readied store would query a schemaless database).
            first_sweep = order.index(("sweep",))
            ready_positions = [i for i, ev in enumerate(order) if ev[0] == "ready"]
            assert ready_positions and max(ready_positions) < first_sweep
        finally:
            await scout.stop()
            await scout.aclose()

    async def test_initial_sweep_runs_eagerly_at_startup(self, tmp_path: Path) -> None:
        order: list[Any] = []
        watcher = _FakeWatcher(order=order)
        scout = _fake_scout(
            config=_config(slug="s", live_path=tmp_path / "live"), order=order, watcher=watcher
        )
        try:
            await scout.start()
            # A fresh start after offline edits must delta-index NOW (via the
            # single-writer run_sweep), not wait out the periodic interval.
            assert watcher.run_sweep_calls == 1
        finally:
            await scout.stop()
            await scout.aclose()

    async def test_live_watch_and_command_channel_start_when_enabled(
        self, tmp_path: Path
    ) -> None:
        order: list[Any] = []
        watcher = _FakeWatcher(order=order)
        subscriber = _FakeCommandSubscriber()
        scout = _fake_scout(
            config=_config(slug="s", live_path=tmp_path / "live", watcher_enabled=True),
            order=order, watcher=watcher, subscriber=subscriber,
        )
        try:
            await scout.start()
            await _wait_until(lambda: subscriber.run_calls == 1)
            assert watcher.start_calls == 1  # live inotify observer up
            assert subscriber.run_calls == 1  # command channel up
        finally:
            await scout.stop()
            await scout.aclose()

    async def test_periodic_reconcile_interval_is_the_config_value_in_seconds(
        self, tmp_path: Path
    ) -> None:
        # The killer unit bug: the periodic loop must sleep reconcile_interval_s
        # SECONDS — not debounce_ms (1500), not a ms conversion (137_000).
        order: list[Any] = []
        sleep = _RecordingSleep()
        scout = _fake_scout(
            config=_config(
                slug="s", live_path=tmp_path / "live", watcher_enabled=True,
                reconcile_interval_s=_RECONCILE_INTERVAL_S,
            ),
            order=order, sleep=sleep,
        )
        try:
            await scout.start()
            await _wait_until(lambda: bool(sleep.delays))
            assert sleep.delays[0] == _RECONCILE_INTERVAL_S, (
                f"the periodic reconcile must sleep the config interval in SECONDS "
                f"({_RECONCILE_INTERVAL_S}); got {sleep.delays[0]!r} — a ms/seconds "
                f"or debounce_ms confusion"
            )
        finally:
            await scout.stop()
            await scout.aclose()

    async def test_sweep_only_mode_indexes_once_but_never_watches(
        self, tmp_path: Path
    ) -> None:
        # ``watcher: {enabled: false}`` = static, non-live-watched: the corpus is
        # still indexed once at startup and the command channel still serves, but
        # there is NO live observer and NO periodic reconcile task (the bug that
        # kept a disabled-watcher corpus permanently un-indexed stays dead).
        order: list[Any] = []
        watcher = _FakeWatcher(order=order)
        subscriber = _FakeCommandSubscriber()
        sleep = _RecordingSleep()
        scout = _fake_scout(
            config=_config(slug="s", live_path=tmp_path / "live", watcher_enabled=False),
            order=order, watcher=watcher, subscriber=subscriber, sleep=sleep,
        )
        try:
            await scout.start()
            await _wait_until(lambda: subscriber.run_calls == 1)
            for _ in range(5):
                await asyncio.sleep(0)
            assert watcher.run_sweep_calls == 1  # initial sweep STILL ran
            assert subscriber.run_calls == 1  # command channel STILL up
            assert watcher.start_calls == 0  # NO live observer
            assert sleep.delays == []  # NO periodic reconcile loop
        finally:
            await scout.stop()
            await scout.aclose()


# =========================================================================== #
# 3) Clean shutdown (fakes)
# =========================================================================== #
class TestScoutShutdown:
    """``stop`` settles background work; ``aclose`` closes every connection."""

    async def test_stop_stops_watcher_and_command_channel(self, tmp_path: Path) -> None:
        order: list[Any] = []
        watcher = _FakeWatcher(order=order)
        subscriber = _FakeCommandSubscriber()
        scout = _fake_scout(
            config=_config(slug="s", live_path=tmp_path / "live"),
            order=order, watcher=watcher, subscriber=subscriber,
        )
        await scout.start()
        await _wait_until(lambda: subscriber.run_calls == 1)
        await scout.stop()
        assert watcher.stop_calls == 1  # observer + spawned tasks settled (#16)
        assert subscriber.stop_calls == 1  # command subscriber cancelled
        await scout.aclose()

    async def test_aclose_closes_all_four_write_connections(self, tmp_path: Path) -> None:
        order: list[Any] = []
        store = _FakeReadyClosable(name="store", order=order)
        manifest = _FakeReadyClosable(name="manifest", order=order)
        graph = _FakeReadyClosable(name="graph", order=order)
        stamper = _FakeReadyClosable(name="stamper", order=order)
        scout = _fake_scout(
            config=_config(slug="s", live_path=tmp_path / "live"), order=order,
            store=store, manifest=manifest, graph=graph, stamper=stamper,
        )
        await scout.start()
        await scout.stop()
        await scout.aclose()
        assert store.close_calls == 1
        assert manifest.close_calls == 1
        assert graph.close_calls == 1
        assert stamper.close_calls == 1

    async def test_run_installs_sigterm_and_sigint_handlers_and_a_signal_shuts_down(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ``run`` is the process lifecycle ``main`` wraps: start → await a
        # shutdown signal → stop + aclose. Spy on the loop's signal registration
        # (an oracle independent of the impl) and prove ``request_shutdown``
        # unblocks the run so a SIGTERM/SIGINT tears the daemon down cleanly.
        order: list[Any] = []
        store = _FakeReadyClosable(name="store", order=order)
        watcher = _FakeWatcher(order=order)
        subscriber = _FakeCommandSubscriber()
        scout = _fake_scout(
            config=_config(slug="s", live_path=tmp_path / "live"), order=order,
            store=store, watcher=watcher, subscriber=subscriber,
        )
        loop = asyncio.get_running_loop()
        registered: set[int] = set()
        monkeypatch.setattr(
            loop, "add_signal_handler",
            lambda sig, *a, **k: registered.add(int(sig)),
        )
        monkeypatch.setattr(loop, "remove_signal_handler", lambda sig: True)

        run_task = asyncio.create_task(scout.run())
        try:
            await _wait_until(lambda: subscriber.run_calls == 1)
            assert {int(signal.SIGTERM), int(signal.SIGINT)} <= registered, (
                "run() must install a clean shutdown on BOTH SIGTERM and SIGINT"
            )
            scout.request_shutdown()
            await asyncio.wait_for(run_task, timeout=3)
            # The signal drove a full teardown: watcher stopped, connections closed.
            assert watcher.stop_calls == 1
            assert store.close_calls == 1
        finally:
            if not run_task.done():
                run_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await run_task


# =========================================================================== #
# 4) Honest failure (fakes)
# =========================================================================== #
class TestScoutHonestFailure:
    """A down store at startup is a loud, TYPED exit — never a hang."""

    async def test_start_propagates_a_typed_connection_error_and_indexes_nothing(
        self, tmp_path: Path
    ) -> None:
        order: list[Any] = []
        watcher = _FakeWatcher(order=order)
        subscriber = _FakeCommandSubscriber()
        store = _FakeReadyClosable(
            name="store", order=order,
            ensure_ready_error=SurrealConnectionError("SurrealDB unreachable"),
        )
        scout = _fake_scout(
            config=_config(slug="s", live_path=tmp_path / "live"), order=order,
            store=store, watcher=watcher, subscriber=subscriber,
        )
        # A down store surfaces the SAME typed error the store raises — not a hang,
        # not a bare Exception the operator cannot classify.
        with pytest.raises(SurrealConnectionError):
            await scout.start()
        assert watcher.run_sweep_calls == 0  # never reached the sweep
        assert subscriber.run_calls == 0  # never opened the command channel

    async def test_a_mid_startup_ready_failure_closes_the_resources_already_opened(
        self, tmp_path: Path
    ) -> None:
        order: list[Any] = []
        store = _FakeReadyClosable(name="store", order=order)  # readies OK
        manifest = _FakeReadyClosable(
            name="manifest", order=order,
            ensure_ready_error=SurrealConnectionError("manifest socket refused"),
        )
        scout = _fake_scout(
            config=_config(slug="s", live_path=tmp_path / "live"), order=order,
            store=store, manifest=manifest,
        )
        with pytest.raises(SurrealConnectionError):
            await scout.start()
        # The store opened before the manifest failed — it MUST be closed on the
        # way out, so a failed startup leaks no live connection.
        assert store.close_calls == 1


# =========================================================================== #
# 5) Command dispatch POLICY (fakes)
# =========================================================================== #
class TestCommandDispatchPolicy:
    """``Scout.handle_command`` maps a kind → action under the writer lock."""

    async def test_reconcile_command_runs_a_sweep(self, tmp_path: Path) -> None:
        order: list[Any] = []
        watcher = _FakeWatcher(order=order)
        scout = _fake_scout(
            config=_config(slug="s", live_path=tmp_path / "live"), order=order, watcher=watcher
        )
        await scout.handle_command({"kind": _RECONCILE_KIND, "payload": {}})
        assert watcher.run_sweep_calls == 1  # 'reconcile' → a real reconcile sweep

    async def test_unknown_kind_raises_and_names_the_kind(self, tmp_path: Path) -> None:
        scout = _fake_scout(
            config=_config(slug="s", live_path=tmp_path / "live"), order=[]
        )
        with pytest.raises(UnknownCommandError) as excinfo:
            await scout.handle_command({"kind": "defrobnicate", "payload": {}})
        # The error must NAME the offending kind so an operator can debug it.
        assert "defrobnicate" in str(excinfo.value)

    async def test_reconcile_command_serializes_on_the_writer_lock(
        self, tmp_path: Path
    ) -> None:
        # A command sweep must never RACE the periodic sweep: both take the
        # watcher's single-writer lock. Hold the lock, fire the command, and prove
        # the sweep is BLOCKED until the lock frees.
        order: list[Any] = []
        watcher = _FakeWatcher(order=order)
        scout = _fake_scout(
            config=_config(slug="s", live_path=tmp_path / "live"), order=order, watcher=watcher
        )
        await watcher.writer_lock.acquire()
        task = asyncio.create_task(
            scout.handle_command({"kind": _RECONCILE_KIND, "payload": {}})
        )
        try:
            for _ in range(5):
                await asyncio.sleep(0)
            assert watcher.run_sweep_calls == 0  # blocked behind the held lock
            watcher.writer_lock.release()
            await asyncio.wait_for(task, timeout=2)
            assert watcher.run_sweep_calls == 1  # proceeded once the lock freed
        finally:
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task


# =========================================================================== #
# 6) CommandSubscriber transport (fake connection: LIVE / poll / reconnect)
# =========================================================================== #
class _FakeCommandConnection:
    """A method-level fake WS connection modelling the ``command`` table.

    Records every ``query(statement, params)`` call. ``pending`` is a shared
    id→row map: a SELECT returns its rows; a stamp UPDATE naming an id removes it
    (models the pending→done/failed transition, which is what makes a re-poll
    idempotent). ``die_on_subscribe`` makes LIVE unavailable (poll must carry the
    load); ``dead`` makes the whole socket raise (models a mid-run drop).
    """

    def __init__(
        self,
        *,
        pending: dict[str, dict[str, Any]] | None = None,
        live_uuid: str = "live-uuid-1",
        die_on_subscribe: bool = False,
        dead: bool = False,
    ) -> None:
        self.pending = pending if pending is not None else {}
        self.queries: list[tuple[str, dict[str, Any]]] = []
        self.live_calls: list[Any] = []
        self.killed: list[Any] = []
        self.closed = False
        self._live_uuid = live_uuid
        self._die_on_subscribe = die_on_subscribe
        self._dead = dead

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}
        self.queries.append((statement, dict(params)))
        if self._dead:
            raise ConnectionResetError("fake socket is dead")
        upper = statement.strip().upper()
        if upper.startswith("LIVE SELECT"):
            return self._live_uuid
        if upper.startswith("SELECT"):
            return list(self.pending.values())
        if upper.startswith(("UPDATE", "DELETE")):
            blob = statement + repr(params)
            for key in list(self.pending):
                if key in blob:
                    self.pending.pop(key, None)
            return []
        return []

    async def live(self, table: Any, *args: Any, **kwargs: Any) -> Any:
        # Whole-table LIVE — the subscriber must NOT use this (it re-fires on every
        # done/failed transition). Recorded so a test can assert it stays unused.
        self.live_calls.append(table)
        return self._live_uuid

    async def subscribe_live(self, query_uuid: Any) -> AsyncIterator[dict[str, Any]]:
        if self._die_on_subscribe or self._dead:
            raise ConnectionResetError("fake live subscription unavailable")
        return
        # The dead yield is the standard empty-async-generator marker; mypy's
        # warn_unreachable flags it by design.
        yield {}  # type: ignore[unreachable]  # pragma: no cover

    async def kill(self, query_uuid: Any) -> None:
        self.killed.append(query_uuid)

    async def close(self) -> None:
        self.closed = True


class _Connector:
    """An async connect factory returning a scripted sequence of connections.

    An entry that is a ``BaseException`` is RAISED on that connect attempt (models
    a failed reconnect for the bounded-backoff pin); the last entry repeats.
    """

    def __init__(self, sequence: list[Any]) -> None:
        self._sequence = list(sequence)
        self.calls = 0

    async def __call__(self) -> Any:
        self.calls += 1
        item = self._sequence[min(self.calls - 1, len(self._sequence) - 1)]
        if isinstance(item, BaseException):
            raise item
        return item


class _RecordingImmediateSleep:
    """A ``sleep`` seam that records each delay and returns at once (yields once)."""

    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, delay: float) -> None:
        self.delays.append(delay)
        await asyncio.sleep(0)


_MAX_BACKOFF_S = 0.05


def _make_subscriber(
    *,
    connect: Any,
    handler: Callable[[dict[str, Any]], Awaitable[None]],
    sleep: Any,
) -> Any:
    """Construct a ``CommandSubscriber`` with a fast poll cadence + tiny backoff."""
    return CommandSubscriber(
        connect=connect,
        handler=handler,
        poll_interval_s=0.01,
        sleep=sleep,
        backoff_base_s=0.01,
        max_backoff_s=_MAX_BACKOFF_S,
    )


async def _run_briefly(subscriber: Any, *, until: Callable[[], bool], timeout: float = 2.0) -> None:
    """Run ``subscriber.run()`` as a task until ``until`` holds, then stop it."""
    task = asyncio.create_task(subscriber.run())
    try:
        await _wait_until(until, timeout=timeout)
    finally:
        await subscriber.stop()
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


class TestLiveSelectStatement:
    """The filtered LIVE SELECT inlines the status LITERAL (the SDK forbids a param)."""

    def test_live_select_filters_pending_with_an_inlined_literal(self) -> None:
        subscriber = _make_subscriber(
            connect=_Connector([_FakeCommandConnection()]),
            handler=lambda row: _noop(),
            sleep=_RecordingImmediateSleep(),
        )
        statement = subscriber.live_select_statement()
        upper = statement.upper()
        assert upper.startswith("LIVE SELECT"), "must be a filtered LIVE SELECT"
        assert COMMAND_TABLE in statement, "must target the command table"
        # The status filter is an INLINED literal — a bound ``$param`` in a LIVE
        # WHERE is silently ignored by the engine (delivers nothing). Use the
        # schema's OWN status constant (clause 5), never a hand-copied 'pending'.
        assert f"status = '{_COMMAND_STATUS_PENDING}'" in statement
        where_clause = statement[upper.index("WHERE"):]
        assert "$" not in where_clause, (
            "a LIVE WHERE must carry NO bound param (the SDK ignores params in a "
            "LIVE query); inline the pending literal instead"
        )


class TestCommandSubscriberTransport:
    """LIVE-primary, poll-fallback, and reconnect against a fake WS connection."""

    async def test_run_issues_filtered_live_select_without_a_status_param(self) -> None:
        connection = _FakeCommandConnection()
        subscriber = _make_subscriber(
            connect=_Connector([connection]),
            handler=lambda row: _noop(),
            sleep=_RecordingImmediateSleep(),
        )
        await _run_briefly(
            subscriber,
            until=lambda: any(
                q[0].upper().startswith("LIVE SELECT") for q in connection.queries
            ),
        )
        live_queries = [q for q in connection.queries if q[0].upper().startswith("LIVE SELECT")]
        assert live_queries, "the subscriber must establish a filtered LIVE SELECT"
        _statement, params = live_queries[0]
        assert "status" not in params, "the LIVE status filter must be inlined, not bound"
        assert connection.live_calls == [], (
            "the subscriber must use a FILTERED `LIVE SELECT ... WHERE status = "
            "'pending'`, never the whole-table `.live(table)` (which re-fires on "
            "every done/failed transition)"
        )

    async def test_poll_fallback_processes_pending_when_live_is_unavailable(self) -> None:
        # LIVE is best-effort; when the subscription is unavailable the poll
        # fallback must STILL process pending commands within the poll interval.
        row = {"id": "command:poll1", "kind": _RECONCILE_KIND, "payload": {}, "status": "pending"}
        connection = _FakeCommandConnection(
            pending={"command:poll1": row}, die_on_subscribe=True
        )
        dispatched: list[str] = []

        async def handler(command_row: dict[str, Any]) -> None:
            dispatched.append(str(command_row["id"]))

        subscriber = _make_subscriber(
            connect=_Connector([connection]), handler=handler, sleep=_RecordingImmediateSleep()
        )
        await _run_briefly(subscriber, until=lambda: bool(dispatched))
        assert dispatched == ["command:poll1"], (
            "with LIVE unavailable, the POLL fallback must still dispatch the "
            "pending command (the SDK never replays a dropped live queue)"
        )

    async def test_reconnect_recovers_a_command_inserted_during_the_gap(self) -> None:
        # A mid-run socket drop: connection #1 is dead (every call raises), then a
        # command is inserted during the gap and connection #2 recovers it. Each
        # command is dispatched EXACTLY once (no loss, no double — idempotence by
        # processed-count, structural to re-reading pending).
        gap_command = {
            "id": "command:gap", "kind": _RECONCILE_KIND, "payload": {}, "status": "pending",
        }
        dead = _FakeCommandConnection(dead=True)
        recovered = _FakeCommandConnection(
            pending={"command:gap": gap_command}, die_on_subscribe=True
        )
        connector = _Connector([dead, recovered])
        dispatched: list[str] = []

        async def handler(command_row: dict[str, Any]) -> None:
            dispatched.append(str(command_row["id"]))

        subscriber = _make_subscriber(
            connect=connector, handler=handler, sleep=_RecordingImmediateSleep()
        )
        # Give the loop time to poll again after the gap command is stamped out, to
        # prove it is NOT re-dispatched.
        await _run_briefly(
            subscriber,
            until=lambda: dispatched.count("command:gap") == 1 and connector.calls >= 2,
        )
        for _ in range(10):
            await asyncio.sleep(0)
        assert connector.calls >= 2, "the subscriber must RECONNECT after a socket drop"
        assert dispatched.count("command:gap") == 1, (
            "the gap command must be recovered EXACTLY once — never lost, never "
            "double-processed"
        )

    async def test_bounded_backoff_between_reconnect_attempts(self) -> None:
        # Two failed reconnects then success: the subscriber backs off between
        # attempts (bounded by max_backoff) and RECOVERS — a brief store outage
        # does not permanently wedge the command channel.
        good = _FakeCommandConnection(die_on_subscribe=True)
        connector = _Connector(
            [ConnectionResetError("boom-1"), ConnectionResetError("boom-2"), good]
        )
        sleep = _RecordingImmediateSleep()
        subscriber = _make_subscriber(
            connect=connector, handler=lambda row: _noop(), sleep=sleep
        )
        await _run_briefly(subscriber, until=lambda: connector.calls >= 3)
        assert connector.calls >= 3, "the subscriber must RETRY a failing reconnect"
        assert sleep.delays, "reconnect must back off (a recorded sleep) between attempts"
        assert all(0 <= delay <= _MAX_BACKOFF_S for delay in sleep.delays), (
            f"every backoff/poll delay must be bounded by max_backoff "
            f"({_MAX_BACKOFF_S}s); got {sleep.delays!r} — an unbounded backoff "
            f"would delay recovery indefinitely"
        )


class _LiveTriggeredConnection(_FakeCommandConnection):
    """A fake connection whose live subscription yields on an explicit trigger.

    ``subscribe_live`` blocks on ``notify_event`` before its first (and only)
    notification, then parks forever — so a test controls PRECISELY when the
    live route fires, independent of the poll loop's own cadence.
    """

    def __init__(
        self, *, pending: dict[str, dict[str, Any]] | None = None, live_uuid: str = "live-uuid-1"
    ) -> None:
        super().__init__(pending=pending, live_uuid=live_uuid)
        self.notify_event = asyncio.Event()

    async def subscribe_live(self, query_uuid: Any) -> AsyncIterator[dict[str, Any]]:
        await self.notify_event.wait()
        yield {"action": "CREATE"}
        # Park forever after the one notification (a fresh, never-set Event) so
        # the generator never raises StopAsyncIteration mid-test.
        await asyncio.Event().wait()


class _ParkingSleep:
    """A sleep seam that records each requested delay, then parks (never returns).

    Pairing a HUGE ``poll_interval_s`` with a sleep that never resolves proves
    the poll loop can fire its drain only ONCE (the eager pre-sleep pass) for
    the lifetime of the test — any dispatch observed AFTER that pass could only
    have come from the live-notification path, never a second poll.
    """

    def __init__(self) -> None:
        self.delays: list[float] = []
        self._gate = asyncio.Event()

    async def __call__(self, delay: float) -> None:
        self.delays.append(delay)
        await self._gate.wait()


# Deliberately enormous — large enough that the poll loop could not plausibly
# sleep it out within any test's timeout, so only LIVE can explain a dispatch
# observed after the eager first drain.
_HUGE_POLL_INTERVAL_S = 10_000.0


class TestLiveNotificationDelivery:
    """A LIVE notification drains pending WITHOUT waiting a poll interval."""

    async def test_live_notification_triggers_a_drain_without_a_poll_interval(
        self,
    ) -> None:
        connection = _LiveTriggeredConnection(pending={})
        dispatched: list[str] = []

        async def handler(command_row: dict[str, Any]) -> None:
            dispatched.append(str(command_row["id"]))

        sleep = _ParkingSleep()
        subscriber = CommandSubscriber(
            connect=_Connector([connection]),
            handler=handler,
            poll_interval_s=_HUGE_POLL_INTERVAL_S,
            sleep=sleep,
            backoff_base_s=0.01,
            max_backoff_s=_MAX_BACKOFF_S,
        )
        task = asyncio.create_task(subscriber.run())
        try:
            # Wait for the poll loop's ONE eager pre-sleep drain to finish and the
            # huge-interval sleep to begin (it never returns) — proving the poll
            # loop cannot fire again for the rest of this test.
            await _wait_until(lambda: bool(sleep.delays))
            assert sleep.delays == [_HUGE_POLL_INTERVAL_S]
            assert dispatched == [], "nothing was pending on the eager first drain"

            # NOW the command appears + the live notification fires — the ONLY
            # route left that can possibly trigger a drain.
            row = {
                "id": "command:live1", "kind": _RECONCILE_KIND, "payload": {},
                "status": "pending",
            }
            connection.pending["command:live1"] = row
            connection.notify_event.set()

            await _wait_until(lambda: bool(dispatched))
            assert dispatched == ["command:live1"], (
                "a live notification must trigger an immediate drain — never "
                "waiting out the poll interval"
            )
        finally:
            await subscriber.stop()
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task


async def _noop() -> None:
    return None


# =========================================================================== #
# 7) Real-harness: composition root + snapshot stamping + command status
# =========================================================================== #
@dataclass
class _ScoutBench:
    """A REAL scout write stack over a throwaway harness database."""

    scout: Any
    store: SurrealStore
    manifest: SurrealManifest
    code_graph: SurrealCodeGraph
    stamper: SnapshotStamper
    indexer: Indexer
    reconcile_engine: ReconcileEngine
    watcher: LiveWatcher
    config: LoreConfig
    env: SurrealEnv
    live_root: Path


async def _build_scout_bench(
    env: SurrealEnv, tmp_path: Path, *, watcher_enabled: bool = True
) -> _ScoutBench:
    """Hand-build the full real write stack and inject it into a ``Scout``.

    Mirrors the composition ``Scout.from_config`` performs, but with the harness's
    root credentials wired directly (no env plumbing) so the command/snapshot
    status transitions can be pinned against the REAL 3.1.5 engine.
    """
    live_root = tmp_path / "live"
    live_root.mkdir(parents=True, exist_ok=True)
    config = _config(slug=env.database, live_path=live_root, watcher_enabled=watcher_enabled, env=env)

    store = SurrealStore(
        url=env.url, namespace=env.namespace, database=env.database, dim=_DIM,
        user=env.user, password=env.password,
    )
    manifest = SurrealManifest(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
    )
    tier_roots, project_roots = graph_roots(config, tmp_path / "snap")
    code_graph = SurrealCodeGraph(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
        tier_roots=tier_roots, project_roots=project_roots,
    )
    stamper = SnapshotStamper(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
        store=store, manifest=manifest, project_root=tmp_path,
    )
    server = LoreServer(config)  # test-side registry source (FastMCP import is fine here)
    indexer = Indexer(
        store=store, embedder=FakeEmbedder(dim=_DIM), manifest=manifest,
        registry=server.registry, source_providers=[], config=config,
        snapshot_root=tmp_path / "snap", code_graph=code_graph, snapshot_stamper=stamper,
    )
    reconcile_engine = ReconcileEngine(
        indexer=indexer, manifest=manifest, store=store, config=config,
        code_graph=code_graph, snapshot_stamper=stamper,
    )
    watcher = LiveWatcher(
        indexer=indexer, manifest=manifest, store=store, config=config,
        loop=asyncio.get_running_loop(), reconcile_engine=reconcile_engine, code_graph=code_graph,
    )
    # Construct the Scout FIRST (this is where the pre-implementation RED fires),
    # then ready the backends.
    scout = Scout(
        config=config, store=store, manifest=manifest, code_graph=code_graph,
        snapshot_stamper=stamper, indexer=indexer, reconcile_engine=reconcile_engine,
        watcher=watcher, command_subscriber=_FakeCommandSubscriber(),
    )
    await store.ensure_ready()
    await manifest.ensure_ready()
    await code_graph.ensure_ready()
    await stamper.ensure_ready()
    return _ScoutBench(
        scout=scout, store=store, manifest=manifest, code_graph=code_graph, stamper=stamper,
        indexer=indexer, reconcile_engine=reconcile_engine, watcher=watcher,
        config=config, env=env, live_root=live_root,
    )


async def _close_scout_bench(bench: _ScoutBench) -> None:
    await bench.stamper.close()
    await bench.code_graph.close()
    await bench.manifest.close()
    await bench.store.close()


async def _insert_command(env: SurrealEnv, *, kind: str, payload: dict[str, Any] | None = None) -> Any:
    """CREATE one ``command`` row (status defaults to pending); return its id."""
    connection = await connect_admin(env)
    try:
        result = await run(
            connection,
            f"CREATE {COMMAND_TABLE} CONTENT $content",
            {"content": {"kind": kind, "payload": payload or {}}},
        )
        rows = [r for r in result if isinstance(r, dict)] if isinstance(result, list) else []
        return rows[0]["id"]
    finally:
        await connection.close()


async def _command_row(env: SurrealEnv, command_id: Any) -> dict[str, Any] | None:
    connection = await connect_admin(env)
    try:
        result = await run(
            connection, f"SELECT * FROM {COMMAND_TABLE} WHERE id = $id", {"id": command_id}
        )
        rows = [r for r in result if isinstance(r, dict)] if isinstance(result, list) else []
        return rows[0] if rows else None
    finally:
        await connection.close()


async def _snapshot_rows(env: SurrealEnv) -> list[dict[str, Any]]:
    connection = await connect_admin(env)
    try:
        result = await run(connection, f"SELECT * FROM {SNAPSHOT_TABLE}")
    finally:
        await connection.close()
    return [r for r in result if isinstance(r, dict)] if isinstance(result, list) else []


class TestScoutCompositionRoot:
    """``Scout.from_config`` composes the full stack — and wires the stamper (C4-#2)."""

    async def test_from_config_wires_the_snapshot_stamper(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Construction-only (no sockets — from_config must NOT do I/O; readiness is
        # start()'s job): the C4-audit #2 wiring is that the ONE stamper the scout
        # built is injected into BOTH the indexer AND the reconcile engine — else a
        # fully-successful sweep stamps NO snapshot (silent). Injection is read via
        # the Indexer/ReconcileEngine's OWN ``_snapshot_stamper`` slot (the same
        # private collaborator field the server-side wiring pin inspects). Tolerant
        # of a sync OR async from_config (the running loop the watcher needs is
        # present either way inside this async test).
        monkeypatch.setenv("SURREAL_USER", "root")
        monkeypatch.setenv("SURREAL_PASS", "secret")
        config = _config(slug="wire", live_path=tmp_path / "live")
        built = Scout.from_config(
            config, snapshot_root=tmp_path / "snap", embedder=FakeEmbedder(dim=_DIM)
        )
        scout = await built if inspect.isawaitable(built) else built
        injected_into_indexer = scout.indexer._snapshot_stamper
        injected_into_reconcile = scout.reconcile_engine._snapshot_stamper
        assert injected_into_indexer is not None, (
            "from_config must construct a SnapshotStamper and inject it into the "
            "indexer (else index_all stamps nothing)"
        )
        assert injected_into_reconcile is not None, (
            "the stamper must also be injected into the reconcile engine (else a "
            "reconcile sweep stamps nothing)"
        )
        assert injected_into_indexer is injected_into_reconcile, (
            "the indexer and reconcile engine must share the SAME stamper instance"
        )


class TestScoutSweepStampsSnapshot:
    """The scout's sweep seam stamps a snapshot on a fully-successful sweep."""

    async def test_scout_sweep_stamps_a_snapshot_reflecting_the_indexed_files(
        self, surreal_env: SurrealEnv, tmp_path: Path  # noqa: F811 - imported fixture
    ) -> None:
        bench = await _build_scout_bench(surreal_env, tmp_path)
        try:
            (bench.live_root / "src").mkdir(parents=True, exist_ok=True)
            (bench.live_root / "src" / "pricing.py").write_text(_PRICING_SOURCE, encoding="utf-8")
            # The scout's own sweep seam (the watcher.run_sweep the initial sweep +
            # the reconcile command both drive) — a productive sweep stamps exactly
            # one snapshot generation.
            summary = await bench.watcher.run_sweep()
            assert summary.files_failed == 0
            assert summary.files_indexed >= 1
            rows = await _snapshot_rows(surreal_env)
            assert len(rows) == 1
            assert rows[0]["files_total"] == summary.files_indexed
        finally:
            await _close_scout_bench(bench)


class TestCommandDispatchAgainstRealSchema:
    """Command status transitions pinned against the REAL {pending,done,failed} domain."""

    async def test_reconcile_command_is_marked_done_with_processed_at(
        self, surreal_env: SurrealEnv, tmp_path: Path  # noqa: F811 - imported fixture
    ) -> None:
        bench = await _build_scout_bench(surreal_env, tmp_path)
        subscriber = CommandSubscriber(
            connect=lambda: connect_admin(surreal_env),
            handler=bench.scout.handle_command,
            poll_interval_s=0.05,
        )
        try:
            command_id = await _insert_command(surreal_env, kind=_RECONCILE_KIND)
            processed = await subscriber.process_pending_once()
            assert processed == 1  # exactly the one pending command
            row = await _command_row(surreal_env, command_id)
            assert row is not None
            # Status uses the schema's OWN 'done' constant (clause 5); a stray
            # 'complete'/'processing' would be rejected by the ASSERT and fail here.
            assert row["status"] == _COMMAND_STATUS_DONE
            assert row.get("processed_at") is not None
        finally:
            await subscriber.stop()
            await _close_scout_bench(bench)

    async def test_empty_command_table_is_a_no_op_drain(
        self, surreal_env: SurrealEnv, tmp_path: Path  # noqa: F811 - imported fixture
    ) -> None:
        bench = await _build_scout_bench(surreal_env, tmp_path)
        subscriber = CommandSubscriber(
            connect=lambda: connect_admin(surreal_env),
            handler=bench.scout.handle_command,
            poll_interval_s=0.05,
        )
        try:
            # A degenerate empty queue: nothing pending → nothing processed, no crash.
            assert await subscriber.process_pending_once() == 0
        finally:
            await subscriber.stop()
            await _close_scout_bench(bench)

    async def test_unknown_kind_is_marked_failed_and_scout_survives(
        self, surreal_env: SurrealEnv, tmp_path: Path  # noqa: F811 - imported fixture
    ) -> None:
        bench = await _build_scout_bench(surreal_env, tmp_path)
        subscriber = CommandSubscriber(
            connect=lambda: connect_admin(surreal_env),
            handler=bench.scout.handle_command,
            poll_interval_s=0.05,
        )
        try:
            bad_id = await _insert_command(surreal_env, kind="defrobnicate")
            await subscriber.process_pending_once()
            bad_row = await _command_row(surreal_env, bad_id)
            assert bad_row is not None
            assert bad_row["status"] == _COMMAND_STATUS_FAILED
            assert bad_row.get("error"), "a failed command must record an error message"
            assert "defrobnicate" in str(bad_row["error"])
            # The scout is STILL alive: a subsequent valid command is processed.
            good_id = await _insert_command(surreal_env, kind=_RECONCILE_KIND)
            await subscriber.process_pending_once()
            good_row = await _command_row(surreal_env, good_id)
            assert good_row is not None
            assert good_row["status"] == _COMMAND_STATUS_DONE
        finally:
            await subscriber.stop()
            await _close_scout_bench(bench)

    async def test_handler_exception_marks_failed_and_scout_survives(
        self, surreal_env: SurrealEnv, tmp_path: Path,  # noqa: F811 - imported fixture
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        bench = await _build_scout_bench(surreal_env, tmp_path)
        # A reconcile whose sweep raises MID-flight (not a bad kind — a genuine
        # handler failure): the command is marked failed, the loop keeps serving.
        async def _boom() -> ReconcileSummary:
            raise RuntimeError("reconcile blew up mid-sweep")

        monkeypatch.setattr(bench.reconcile_engine, "reconcile", _boom)
        subscriber = CommandSubscriber(
            connect=lambda: connect_admin(surreal_env),
            handler=bench.scout.handle_command,
            poll_interval_s=0.05,
        )
        try:
            command_id = await _insert_command(surreal_env, kind=_RECONCILE_KIND)
            await subscriber.process_pending_once()
            row = await _command_row(surreal_env, command_id)
            assert row is not None
            assert row["status"] == _COMMAND_STATUS_FAILED
            assert row.get("error"), "a handler exception must be recorded as the error"
        finally:
            await subscriber.stop()
            await _close_scout_bench(bench)

    async def test_marking_an_already_done_command_claims_nothing_and_does_not_error(
        self, surreal_env: SurrealEnv, tmp_path: Path,  # noqa: F811 - imported fixture
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        # C6-audit hardening #1: the status MARK is a conditional CAS claim
        # (``WHERE status = 'pending' RETURN BEFORE``) — two scout instances
        # racing the SAME command must never both succeed. A duplicate mark
        # attempt against an already-terminal row (modelling a second instance
        # finishing a beat late) must claim NOTHING, log loudly, and never raise
        # or corrupt the already-done row.
        bench = await _build_scout_bench(surreal_env, tmp_path)
        subscriber = CommandSubscriber(
            connect=lambda: connect_admin(surreal_env),
            handler=bench.scout.handle_command,
            poll_interval_s=0.05,
        )
        try:
            command_id = await _insert_command(surreal_env, kind=_RECONCILE_KIND)
            processed = await subscriber.process_pending_once()
            assert processed == 1
            row = await _command_row(surreal_env, command_id)
            assert row is not None and row["status"] == _COMMAND_STATUS_DONE
            first_processed_at = row["processed_at"]

            connection = await connect_admin(surreal_env)
            try:
                with caplog.at_level(logging.INFO, logger="loremaster.scout"):
                    # A second mark attempt against the now-terminal row — the
                    # CAS claim must match nothing (status is no longer pending).
                    await subscriber._mark(  # noqa: SLF001 - the seam under test
                        connection, command_id, _COMMAND_STATUS_DONE
                    )
            finally:
                await connection.close()

            duplicate_events = [
                r for r in caplog.records if r.message == "command.duplicate_completion"
            ]
            assert duplicate_events, "a duplicate mark must log command.duplicate_completion"
            assert duplicate_events[0].levelno == logging.INFO

            # The already-terminal row is untouched by the duplicate attempt —
            # no corruption (same processed_at), and no exception propagated.
            row_after = await _command_row(surreal_env, command_id)
            assert row_after is not None
            assert row_after["status"] == _COMMAND_STATUS_DONE
            assert row_after["processed_at"] == first_processed_at
        finally:
            await subscriber.stop()
            await _close_scout_bench(bench)


class TestCommandChannelLivePrimaryEndToEnd:
    """A RUNNING subscriber processes an out-of-band command end-to-end."""

    async def test_running_subscriber_processes_an_inserted_pending_command(
        self, surreal_env: SurrealEnv, tmp_path: Path  # noqa: F811 - imported fixture
    ) -> None:
        bench = await _build_scout_bench(surreal_env, tmp_path)
        subscriber = CommandSubscriber(
            connect=lambda: connect_admin(surreal_env),
            handler=bench.scout.handle_command,
            poll_interval_s=0.1,  # a short poll backstop keeps the test robust
        )
        run_task = asyncio.create_task(subscriber.run())
        try:
            command_id = await _insert_command(surreal_env, kind=_RECONCILE_KIND)

            async def _is_done() -> bool:
                row = await _command_row(surreal_env, command_id)
                return row is not None and row["status"] == _COMMAND_STATUS_DONE

            deadline = asyncio.get_event_loop().time() + 6.0
            while asyncio.get_event_loop().time() < deadline:
                if await _is_done():
                    break
                await asyncio.sleep(0.1)
            row = await _command_row(surreal_env, command_id)
            assert row is not None and row["status"] == _COMMAND_STATUS_DONE, (
                "a running command subscriber must process an inserted pending "
                "command (LIVE-primary, poll-backstopped) end-to-end"
            )
        finally:
            await subscriber.stop()
            if not run_task.done():
                run_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await run_task
            await _close_scout_bench(bench)
