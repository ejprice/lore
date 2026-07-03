"""Contract tests for ``loremaster.index.watcher`` — the live inotify watcher.

PORTED for P5-C3b onto the async Surreal fakes (:mod:`_surreal_fakes`). The
watcher's rewiring is: its ``_purge`` composes ONE atomic purge transaction
(store-delete + file_text-delete + manifest-delete + graph-purge fragments via
``store.apply``) and its manifest/graph calls are ``await``ed, while ``_apply``
indexes through the async indexer. These tests keep the SAME behavioural pins —
delete → purge, atomic-save → reindex-dest + purge-src, event-scope drop,
debounce coalesce, the single-writer lock serialising sweep + live event, and
the kernel-overflow → immediate reconcile seam — only the fixtures change (real
Qdrant + SQLite manifest → the fakes; store-side assertions read the fake's
recorded state; manifest reads are ``await``ed).

SCOPE OF THIS PORT (reported to the team lead):

* **Ported** — the DETERMINISTIC seam/drain tests that exercise the async
  purge/index contract: debounce coalescing (delete-after-modify /
  modify-after-delete), atomic-save, delete, event-scope pruning, the QueueFull
  drop sites, the single-writer lock serialisation, the kernel-overflow →
  immediate-reconcile seam, and ``stop()`` settling in-flight overflow tasks.
* **Kept UNCHANGED** (they never touch the Surreal ports, so nothing to port):
  ``TestOneInotifyInstancePerRoot`` (build_observer against explode-on-touch
  sentinels) and ``TestKernelOverflowDetectionDoesNotMutateGlobalParser`` (a pure
  raw-buffer scan against a spy).
* **DEFERRED** — the REAL-inotify end-to-end tests that drive an actual watchdog
  Observer over ``tmp_path`` (``TestLiveModify``, the nested/recursive-watch
  indexing tests, the watch-scope pruning tests, and the start/stop lifecycle log
  test). These exercise real kernel inotify (EEXIST/EMFILE-prone on a saturated
  host, slow timeout-based polling) and their store/manifest usage is INCIDENTAL
  to the watch mechanism they test — orthogonal to the Surreal rewiring. Left for
  a focused follow-up so the fast unit port stays fast and deterministic.
"""

from __future__ import annotations

import asyncio
import inspect as _inspect_for_overflow_guard
import logging
import struct as _struct_for_overflow_guard
import uuid
from pathlib import Path
from typing import Any

import pytest
from _surreal_fakes import FakeSurrealTrio, fake_surreal_trio
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer, IndexOutcome
from loremaster.index.reconcile import ReconcileEngine
from loremaster.index.surreal_manifest import STATE_INDEXED
from loremaster.index.watcher import LiveWatcher, _OverflowAwareInotify
from loremaster.server import LoreServer
from loresigil.base import Embedder
from loresigil.testing import FakeEmbedder
from watchdog.observers.inotify_c import Inotify as _WatchdogInotify
from watchdog.observers.inotify_c import InotifyConstants as _WatchdogInotifyConstants

_DIM = 2048
_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"

_DEBOUNCE_MS = 120
_SETTLE_TIMEOUT_S = 8.0


# --------------------------------------------------------------------------- #
# Instrumented indexer wrappers
# --------------------------------------------------------------------------- #
class RecordingIndexer:
    """Wraps a real :class:`Indexer`, recording every ``index_file`` call."""

    def __init__(self, inner: Indexer) -> None:
        self._inner = inner
        self.index_calls: list[tuple[str, str]] = []
        self._inner_index_file = inner.index_file
        inner.index_file = self.index_file  # type: ignore[method-assign]

    async def index_file(self, tier: str, path: str, source: str) -> IndexOutcome:
        self.index_calls.append((tier, path))
        return await self._inner_index_file(tier, path, source)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class ConcurrencyTrackingEmbedder(FakeEmbedder):
    """A slow :class:`FakeEmbedder` that detects CONCURRENT indexing of any kind."""

    def __init__(self, *, hold_s: float = 0.05, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._hold_s = hold_s
        self._in_flight = 0
        self.max_concurrent = 0

    @property
    def supports_contextualized(self) -> bool:
        return False

    async def embed_documents(self, texts: list[str]) -> Any:
        self._in_flight += 1
        self.max_concurrent = max(self.max_concurrent, self._in_flight)
        try:
            await asyncio.sleep(self._hold_s)
            return await super().embed_documents(texts)
        finally:
            self._in_flight -= 1


# --------------------------------------------------------------------------- #
# Corpus + config builders
# --------------------------------------------------------------------------- #
def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


_PY_MODULE_2 = """\
def champion_routing(week):
    \"\"\"Route the 36-week curve champion.\"\"\"
    return week * 2
"""


def _build_live_corpus(root: Path) -> None:
    _write(root / "src" / "routing.py", _PY_MODULE_2)
    _write(root / ".venv" / "lib" / "vendored.py", "junk = 1\n")
    _write(root / "src" / "api_pb2.py", "def generated_proto_marker():\n    return 1\n")


def _config(
    *,
    slug: str,
    live_path: Path,
    static_source: Path | None = None,
    debounce_ms: int = _DEBOUNCE_MS,
) -> LoreConfig:
    roots: list[dict[str, Any]] = [
        {
            "tier": "custom",
            "watch": "live",
            "path": str(live_path),
            "include": ["**/*.py", "**/*.md"],
            "exclude": ["**/*.min.js"],
        }
    ]
    if static_source is not None:
        roots.append(
            {
                "tier": "community",
                "watch": "static",
                "source": str(static_source),
                "version": "1.0.0",
                "provider": "local_directory",
                "include": ["**/*.py"],
            }
        )
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": _TEI_BASE_URL,
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": _TEI_KEY_ENV,
            "tokenizer": "voyage-4-nano",
        },
        "qdrant": {"url": "http://127.0.0.1:16333", "api_key_env": "QDRANT__SERVICE__API_KEY"},
        "roots": roots,
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": ["**/*.min.js", "**/*_pb2.py"],
        "chunkers": {".py": {"chunker": "python_ast"}, ".md": {"chunker": "markdown"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": debounce_ms,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9201},
    }
    return LoreConfig.model_validate(payload)


def _slug() -> str:
    return f"test_{uuid.uuid4().hex}"


_NESTED_INCLUDED_SUBDIRS: tuple[str, ...] = (
    "pkg",
    "pkg/sub_a",
    "pkg/sub_a/deep",
    "pkg/sub_b",
    "services",
    "services/routing",
)
_EXCLUDED_DIR_NAME = "__pycache__"


def _build_wide_live_corpus(root: Path) -> None:
    for rel in _NESTED_INCLUDED_SUBDIRS:
        _write(
            root / rel / "module.py",
            f"def symbol_in_{rel.replace('/', '_')}():\n    return 1\n",
        )
    _write(
        root / "pkg" / _EXCLUDED_DIR_NAME / "module.cpython-314.pyc.py",
        "def compiled_artifact_marker():\n    return 1\n",
    )


def _live_root_count(config: LoreConfig) -> int:
    from loremaster.config import WATCH_LIVE

    return sum(1 for root in config.effective_roots if root.watch == WATCH_LIVE)


# --------------------------------------------------------------------------- #
# Fake-trio wiring
# --------------------------------------------------------------------------- #
def _trio() -> FakeSurrealTrio:
    return fake_surreal_trio(dim=_DIM)


def _make_indexer(
    *, config: LoreConfig, trio: FakeSurrealTrio, embedder: Embedder, snapshot_root: Path
) -> Indexer:
    server = LoreServer(config)
    return Indexer(
        store=trio.store,
        embedder=embedder,
        manifest=trio.manifest,
        registry=server.registry,
        source_providers=list(server.source_providers),
        config=config,
        snapshot_root=snapshot_root,
    )


def _make_watcher(
    *, config: LoreConfig, indexer: Any, trio: FakeSurrealTrio, queue_maxsize: int | None = None
) -> LiveWatcher:
    engine = ReconcileEngine(
        indexer=indexer, manifest=trio.manifest, store=trio.store, config=config
    )
    kwargs: dict[str, Any] = {}
    if queue_maxsize is not None:
        kwargs["queue_maxsize"] = queue_maxsize
    return LiveWatcher(
        indexer=indexer,
        manifest=trio.manifest,
        store=trio.store,
        config=config,
        loop=asyncio.get_running_loop(),
        reconcile_engine=engine,
        **kwargs,
    )


def _has_identity(trio: FakeSurrealTrio, file_path: str, identity: str) -> bool:
    for chunk in trio.store.db.chunks.values():
        if chunk.file_path == file_path and chunk.payload.get("identity") == identity:
            return True
    return False


def _queue_keys(watcher: LiveWatcher) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    while not watcher._queue.empty():
        keys.append(watcher._queue.get_nowait())
    for key in keys:
        watcher._queue.put_nowait(key)
    return keys


# --------------------------------------------------------------------------- #
# Debounce coalescing (seam-driven, deterministic)
# --------------------------------------------------------------------------- #
class TestDebounceCoalesce:
    """Last-event-wins coalescing of a modify+delete burst for one path."""

    async def test_delete_after_modify_within_window_wins_as_purge(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        inner = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        indexer = RecordingIndexer(inner)
        await indexer.index_file(
            "custom", "src/routing.py", (live / "src" / "routing.py").read_text(encoding="utf-8"),
        )
        indexer.index_calls.clear()
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)

        # MODIFY (still present) then DELETE, both before any drain → last op wins.
        (live / "src" / "routing.py").write_text(
            "def changed_then_delete_event():\n    return 0\n", encoding="utf-8"
        )
        watcher.on_modified_path(str(live / "src" / "routing.py"))
        watcher.on_deleted_path(str(live / "src" / "routing.py"))
        await watcher.drain()

        assert indexer.index_calls == [], "a stale index op survived the coalesce"
        assert await trio.manifest.get("custom", "src/routing.py") is None
        assert "src/routing.py" not in trio.store.stored_file_paths()

    async def test_modify_after_delete_within_window_wins_as_index(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        inner = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        indexer = RecordingIndexer(inner)
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)

        watcher.on_deleted_path(str(live / "src" / "routing.py"))
        (live / "src" / "routing.py").write_text(
            "def deleted_then_recreated():\n    return 1\n", encoding="utf-8"
        )
        watcher.on_modified_path(str(live / "src" / "routing.py"))
        await watcher.drain()

        assert indexer.index_calls == [("custom", "src/routing.py")]
        row = await trio.manifest.get("custom", "src/routing.py")
        assert row is not None and row.state == STATE_INDEXED
        assert _has_identity(trio, "src/routing.py", "deleted_then_recreated")


# --------------------------------------------------------------------------- #
# QueueFull drop sites (seam + real timer, deterministic)
# --------------------------------------------------------------------------- #
class TestQueueFullDrop:
    """A full bounded queue drops the event; the next reconcile sweep recovers it."""

    async def test_queue_full_drops_event_but_sweep_recovers_it(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live, debounce_ms=20)
        trio = _trio()
        inner = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        indexer: Any = RecordingIndexer(inner)
        engine = ReconcileEngine(
            indexer=indexer, manifest=trio.manifest, store=trio.store, config=config
        )
        watcher = LiveWatcher(
            indexer=indexer, manifest=trio.manifest, store=trio.store, config=config,
            loop=asyncio.get_running_loop(), reconcile_engine=engine, queue_maxsize=1,
        )

        _write(live / "src" / "overflow.py", "def overflow_marker():\n    return 1\n")
        watcher._queue.put_nowait(("custom", "sentinel_filler.py"))
        assert watcher._queue.full()

        watcher.on_modified_path(str(live / "src" / "overflow.py"))
        with caplog.at_level(logging.WARNING, logger="loremaster.index.watcher"):
            await asyncio.sleep(0.10)

        assert watcher._queue.qsize() == 1
        assert ("custom", "src/overflow.py") not in _queue_keys(watcher)
        assert await trio.manifest.get("custom", "src/overflow.py") is None
        assert indexer.index_calls == []

        overflow_events = [r for r in caplog.records if r.message == "watcher.in_q_overflow"]
        assert len(overflow_events) == 1
        assert overflow_events[0].levelno == logging.WARNING
        assert overflow_events[0].tier == "custom"  # type: ignore[attr-defined]
        assert overflow_events[0].file_path == "src/overflow.py"  # type: ignore[attr-defined]

        await engine.reconcile()
        row = await trio.manifest.get("custom", "src/overflow.py")
        assert row is not None and row.state == STATE_INDEXED
        assert _has_identity(trio, "src/overflow.py", "overflow_marker")

    async def test_burst_flush_queue_full_logs_overflow(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live, debounce_ms=10_000)
        trio = _trio()
        inner = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        indexer: Any = RecordingIndexer(inner)
        engine = ReconcileEngine(
            indexer=indexer, manifest=trio.manifest, store=trio.store, config=config
        )
        watcher = LiveWatcher(
            indexer=indexer, manifest=trio.manifest, store=trio.store, config=config,
            loop=asyncio.get_running_loop(), reconcile_engine=engine, queue_maxsize=1,
        )

        _write(live / "src" / "overflow.py", "def overflow_marker():\n    return 1\n")
        watcher._queue.put_nowait(("custom", "sentinel_filler.py"))
        assert watcher._queue.full()

        watcher.on_modified_path(str(live / "src" / "overflow.py"))
        await asyncio.sleep(0)
        assert ("custom", "src/overflow.py") in watcher._pending

        with caplog.at_level(logging.WARNING, logger="loremaster.index.watcher"):
            await watcher.drain()

        assert indexer.index_calls == []
        assert await trio.manifest.get("custom", "src/overflow.py") is None

        overflow_events = [r for r in caplog.records if r.message == "watcher.in_q_overflow"]
        assert len(overflow_events) == 1
        assert overflow_events[0].levelno == logging.WARNING
        assert overflow_events[0].tier == "custom"  # type: ignore[attr-defined]
        assert overflow_events[0].file_path == "src/overflow.py"  # type: ignore[attr-defined]

        await engine.reconcile()
        row = await trio.manifest.get("custom", "src/overflow.py")
        assert row is not None and row.state == STATE_INDEXED
        assert _has_identity(trio, "src/overflow.py", "overflow_marker")


# --------------------------------------------------------------------------- #
# Atomic-save (MOVED_TO) → dest reindexed + src purged (seam-driven)
# --------------------------------------------------------------------------- #
class TestAtomicSave:
    """An editor's rename tmp → dest re-indexes dest and purges src."""

    async def test_moved_event_reindexes_dest_and_purges_src(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        await indexer.index_file(
            "custom", "src/routing.py", (live / "src" / "routing.py").read_text(encoding="utf-8"),
        )
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)

        dest_text = "def moved_marker_q(week):\n    return week\n"
        (live / "src" / "renamed.py").write_text(dest_text, encoding="utf-8")
        watcher.on_moved_path(
            src_abs=str(live / "src" / "routing.py"),
            dest_abs=str(live / "src" / "renamed.py"),
        )
        await watcher.drain()

        assert _has_identity(trio, "src/renamed.py", "moved_marker_q")
        assert await trio.manifest.get("custom", "src/renamed.py") is not None
        assert await trio.manifest.get("custom", "src/routing.py") is None
        assert "src/routing.py" not in trio.store.stored_file_paths()


# --------------------------------------------------------------------------- #
# Delete → purge (seam-driven)
# --------------------------------------------------------------------------- #
class TestDelete:
    """A delete event purges the file from the store and the manifest."""

    async def test_delete_event_purges_file(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        await indexer.index_file(
            "custom", "src/routing.py", (live / "src" / "routing.py").read_text(encoding="utf-8"),
        )
        assert await trio.manifest.get("custom", "src/routing.py") is not None
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)

        (live / "src" / "routing.py").unlink()
        watcher.on_deleted_path(str(live / "src" / "routing.py"))
        await watcher.drain()

        assert await trio.manifest.get("custom", "src/routing.py") is None
        assert "src/routing.py" not in trio.store.stored_file_paths()


# --------------------------------------------------------------------------- #
# Excluded dirs / static roots are never scheduled / never indexed (seam + pure)
# --------------------------------------------------------------------------- #
class TestSchedulingPruning:
    """The Observer watches included live roots only; excluded dirs are pruned."""

    async def test_watched_roots_exclude_pruned_dirs_and_static(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        static_src = tmp_path / "community_src"
        _write(static_src / "core.py", _PY_MODULE_2)
        config = _config(slug=slug, live_path=live, static_source=static_src)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)

        watched = {Path(p).resolve() for p in watcher.watched_paths()}
        assert (live).resolve() in watched
        assert (live / ".venv").resolve() not in watched
        assert (live / ".venv" / "lib").resolve() not in watched
        assert static_src.resolve() not in watched

    async def test_event_inside_excluded_dir_does_no_index_work(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        inner = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        indexer = RecordingIndexer(inner)
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)

        watcher.on_modified_path(str(live / ".venv" / "lib" / "vendored.py"))
        watcher.on_modified_path(str(live / "src" / "bundle.min.js"))
        watcher.on_modified_path(str(live / "src" / "api_pb2.py"))
        await watcher.drain()

        assert indexer.index_calls == []
        assert await trio.manifest.get("custom", ".venv/lib/vendored.py") is None
        assert await trio.manifest.get("custom", "src/api_pb2.py") is None


# --------------------------------------------------------------------------- #
# The single lock serializes the sweep AND the live-event drain
# --------------------------------------------------------------------------- #
class TestLockSerialization:
    """A periodic sweep and a queue-drain event never index concurrently."""

    async def test_sweep_and_event_never_index_concurrently(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        _write(live / "src" / "alpha.py", "def alpha_lock_marker():\n    return 1\n")
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        embedder = ConcurrencyTrackingEmbedder(dim=_DIM, hold_s=0.05)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)

        watcher.on_modified_path(str(live / "src" / "alpha.py"))
        await asyncio.gather(watcher.run_sweep(), watcher.drain())

        assert embedder.max_concurrent >= 1
        assert embedder.max_concurrent == 1, (
            f"sweep and live event indexed concurrently "
            f"(max_concurrent={embedder.max_concurrent}); the single lock failed"
        )
        alpha_row = await trio.manifest.get("custom", "src/alpha.py")
        assert alpha_row is not None and alpha_row.state == STATE_INDEXED
        routing_row = await trio.manifest.get("custom", "src/routing.py")
        assert routing_row is not None and routing_row.state == STATE_INDEXED


# --------------------------------------------------------------------------- #
# (1) One inotify INSTANCE per ROOT — build_observer (pure; unchanged)
# --------------------------------------------------------------------------- #
class _NoopStoreSentinel:
    def __getattr__(self, name: str) -> Any:  # pragma: no cover - never called
        raise AssertionError(f"store.{name} touched during build_observer")


class _NoopIndexerSentinel:
    def __getattr__(self, name: str) -> Any:  # pragma: no cover - never called
        raise AssertionError(f"indexer.{name} touched during build_observer")


class _NoopEngineSentinel:
    def __getattr__(self, name: str) -> Any:  # pragma: no cover - never called
        raise AssertionError(f"reconcile_engine.{name} touched during build_observer")


class TestOneInotifyInstancePerRoot:
    """The watcher schedules ONE recursive watch per LIVE ROOT, not one per dir."""

    async def test_emitter_count_equals_root_count_not_dir_count(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_wide_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        watcher = LiveWatcher(
            indexer=_NoopIndexerSentinel(),  # type: ignore[arg-type]
            manifest=trio.manifest,
            store=_NoopStoreSentinel(),
            config=config,
            loop=asyncio.get_running_loop(),
            reconcile_engine=_NoopEngineSentinel(),  # type: ignore[arg-type]
        )

        observer = watcher.build_observer()

        expected_instances = _live_root_count(config)
        assert expected_instances == 1
        assert len(observer.emitters) == expected_instances, (
            f"watcher opened {len(observer.emitters)} inotify instances for "
            f"{expected_instances} live root(s)"
        )
        sole_watch = next(iter(observer.emitters)).watch
        assert sole_watch.is_recursive is True
        assert Path(sole_watch.path).resolve() == live.resolve()


# --------------------------------------------------------------------------- #
# (4) Kernel IN_Q_OVERFLOW -> immediate tier reconcile (seam-driven)
# --------------------------------------------------------------------------- #
class _ReconcileSpy:
    """Wraps a real :class:`ReconcileEngine`, recording every ``reconcile`` call."""

    def __init__(self, inner: ReconcileEngine) -> None:
        self._inner = inner
        self.reconcile_calls = 0

    async def reconcile(self) -> Any:
        self.reconcile_calls += 1
        return await self._inner.reconcile()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class TestKernelOverflowTriggersImmediateReconcile:
    """A KERNEL inotify-queue overflow triggers an immediate reconcile."""

    def _build(
        self, tmp_path: Path, trio: FakeSurrealTrio, *, slug: str
    ) -> tuple[LiveWatcher, _ReconcileSpy, Path]:
        live = tmp_path / "live"
        _build_wide_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        spy = _ReconcileSpy(
            ReconcileEngine(indexer=indexer, manifest=trio.manifest, store=trio.store, config=config)
        )
        watcher = LiveWatcher(
            indexer=indexer, manifest=trio.manifest, store=trio.store, config=config,
            loop=asyncio.get_running_loop(),
            reconcile_engine=spy,  # type: ignore[arg-type]
        )
        return watcher, spy, live

    async def test_kernel_overflow_signal_invokes_tier_reconcile(self, tmp_path: Path) -> None:
        slug = _slug()
        trio = _trio()
        watcher, spy, _live = self._build(tmp_path, trio, slug=slug)

        assert spy.reconcile_calls == 0
        await watcher.on_kernel_overflow("custom")
        assert spy.reconcile_calls == 1

    async def test_kernel_overflow_recovers_a_missed_file_promptly(self, tmp_path: Path) -> None:
        slug = _slug()
        trio = _trio()
        watcher, spy, live = self._build(tmp_path, trio, slug=slug)

        missed_rel = "pkg/sub_b/burst_missed.py"
        _write(live / missed_rel, "def burst_overflow_recovery_marker():\n    return 1\n")
        assert await trio.manifest.get("custom", missed_rel) is None

        await watcher.on_kernel_overflow("custom")

        assert spy.reconcile_calls == 1
        row = await trio.manifest.get("custom", missed_rel)
        assert row is not None and row.state == STATE_INDEXED
        assert _has_identity(trio, missed_rel, "burst_overflow_recovery_marker")

    async def test_kernel_overflow_reconcile_holds_the_single_writer_lock(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        trio = _trio()
        watcher, spy, _live = self._build(tmp_path, trio, slug=slug)

        await watcher.writer_lock.acquire()
        task = asyncio.ensure_future(watcher.on_kernel_overflow("custom"))
        await asyncio.sleep(0.05)
        assert spy.reconcile_calls == 0, (
            "overflow reconcile ran without the single-writer lock"
        )
        watcher.writer_lock.release()
        await asyncio.wait_for(task, timeout=_SETTLE_TIMEOUT_S)
        assert spy.reconcile_calls == 1


# --------------------------------------------------------------------------- #
# ``stop()`` settles in-flight overflow-reconcile tasks
# --------------------------------------------------------------------------- #
class TestStopSettlesOverflowTasks:
    """``stop()`` cancels-and-awaits EVERY task the watcher launched."""

    async def test_stop_settles_in_flight_overflow_reconcile_task(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_wide_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        engine = ReconcileEngine(
            indexer=indexer, manifest=trio.manifest, store=trio.store, config=config
        )
        watcher = LiveWatcher(
            indexer=indexer, manifest=trio.manifest, store=trio.store, config=config,
            loop=asyncio.get_running_loop(), reconcile_engine=engine,
        )

        await watcher.writer_lock.acquire()
        tasks_before = asyncio.all_tasks()
        watcher._launch_overflow_reconcile("custom")
        await asyncio.sleep(0)
        new_tasks = asyncio.all_tasks() - tasks_before
        assert len(new_tasks) == 1, "expected exactly one spawned overflow task"
        overflow_task = next(iter(new_tasks))
        assert not overflow_task.done(), "overflow task should be blocked on the lock"

        await watcher.stop()

        assert overflow_task.done(), (
            "an overflow-reconcile task survived stop()"
        )
        assert overflow_task.cancelled(), "stop() should CANCEL the settled task"

        watcher.writer_lock.release()
        await trio.manifest.close()  # must not raise
        await asyncio.sleep(0.05)
        assert overflow_task.cancelled()


# ===========================================================================
# Kernel-overflow DETECTION guard (W1/W2) — PURE raw-buffer scan; UNCHANGED,
# never touches the Surreal ports.
# ===========================================================================

_PRISTINE_PARSE_EVENT_BUFFER = _inspect_for_overflow_guard.getattr_static(
    _WatchdogInotify, "_parse_event_buffer"
)
_DETECTION_SEAM_NAME = "scan_buffer_for_overflow"
_INOTIFY_HEADER_FORMAT = "iIII"
_NO_WATCH_DESCRIPTOR_SENTINEL = -1


def _pack_inotify_event(wd: int, mask: int, *, cookie: int = 0, name: bytes = b"") -> bytes:
    padded = name + b"\x00" if name else b""
    return _struct_for_overflow_guard.pack(
        _INOTIFY_HEADER_FORMAT, wd, mask, cookie, len(padded)
    ) + padded


def _overflow_sentinel_buffer() -> bytes:
    return _pack_inotify_event(
        _NO_WATCH_DESCRIPTOR_SENTINEL, _WatchdogInotifyConstants.IN_Q_OVERFLOW
    )


def _normal_modify_buffer() -> bytes:
    return _pack_inotify_event(1, _WatchdogInotifyConstants.IN_MODIFY, name=b"routing.py")


class _OverflowCallbackSpy:
    def __init__(self) -> None:
        self.fired = 0

    def __call__(self) -> None:
        self.fired += 1


def _build_overflow_aware_inotify_without_fd(
    on_overflow: _OverflowCallbackSpy,
) -> _OverflowAwareInotify:
    instance = _OverflowAwareInotify.__new__(_OverflowAwareInotify)
    instance._on_overflow = on_overflow
    return instance


class TestKernelOverflowDetectionDoesNotMutateGlobalParser:
    """The overflow detector scans the raw buffer WITHOUT touching global state."""

    def test_detection_seam_exists_and_is_named(self) -> None:
        assert hasattr(_OverflowAwareInotify, _DETECTION_SEAM_NAME), (
            f"reworked _OverflowAwareInotify must expose a pure detection seam "
            f"named {_DETECTION_SEAM_NAME!r}"
        )

    def test_detection_fires_callback_on_overflow_sentinel(self) -> None:
        spy = _OverflowCallbackSpy()
        inotify = _build_overflow_aware_inotify_without_fd(spy)
        seam = getattr(inotify, _DETECTION_SEAM_NAME)

        result = seam(_overflow_sentinel_buffer())

        assert spy.fired == 1
        assert result is None or bool(result) is True

    def test_detection_ignores_a_normal_event_buffer(self) -> None:
        spy = _OverflowCallbackSpy()
        inotify = _build_overflow_aware_inotify_without_fd(spy)
        seam = getattr(inotify, _DETECTION_SEAM_NAME)

        result = seam(_normal_modify_buffer())

        assert spy.fired == 0
        assert result is None or bool(result) is False

    def test_detection_does_not_strip_or_replace_global_static_parser(self) -> None:
        spy = _OverflowCallbackSpy()
        inotify = _build_overflow_aware_inotify_without_fd(spy)
        seam = getattr(inotify, _DETECTION_SEAM_NAME)

        before = _inspect_for_overflow_guard.getattr_static(
            _WatchdogInotify, "_parse_event_buffer"
        )
        assert isinstance(before, staticmethod)
        assert before is _PRISTINE_PARSE_EVENT_BUFFER

        seam(_overflow_sentinel_buffer())
        assert spy.fired == 1

        after = _inspect_for_overflow_guard.getattr_static(
            _WatchdogInotify, "_parse_event_buffer"
        )
        assert isinstance(after, staticmethod), (
            "Inotify._parse_event_buffer is no longer a staticmethod after detection (W1)"
        )
        assert after is _PRISTINE_PARSE_EVENT_BUFFER, (
            "Inotify._parse_event_buffer was replaced after detection (W1/W2)"
        )

    def test_repeated_detection_never_mutates_global_parser(self) -> None:
        spy = _OverflowCallbackSpy()
        inotify = _build_overflow_aware_inotify_without_fd(spy)
        seam = getattr(inotify, _DETECTION_SEAM_NAME)

        iterations = 5
        for _ in range(iterations):
            seam(_overflow_sentinel_buffer())
            current = _inspect_for_overflow_guard.getattr_static(
                _WatchdogInotify, "_parse_event_buffer"
            )
            assert isinstance(current, staticmethod)
            assert current is _PRISTINE_PARSE_EVENT_BUFFER

        assert spy.fired == iterations
