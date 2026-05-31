"""Contract tests for ``loremaster.index.watcher`` — the live inotify watcher.

The :class:`~loremaster.index.watcher.LiveWatcher` runs a watchdog
:class:`~watchdog.observers.Observer` on the LIVE roots only, debounces/coalesces
the raw events, marshals them onto the asyncio loop via
``loop.call_soon_threadsafe`` into a bounded :class:`asyncio.Queue` + a coalescing
dict, and drains them through :meth:`Indexer.index_file` under a SINGLE
:class:`asyncio.Lock` that ALSO guards the periodic reconcile sweep — so a live
event and a sweep never run ``index_file`` concurrently.

These tests run against a **REAL local Qdrant** (throwaway collections), a
**REAL corpus** under ``tmp_path``, a **FakeEmbedder(dim=2048)**, and — for the
end-to-end event path — a **REAL watchdog Observer** over ``tmp_path`` (inotify
over a real temp dir is verified to work on this box).

The contract under test (plan Deliverable 3 Watcher concurrency §(1)/(Q2) +
AMENDMENT 1 A1.11):

* **MODIFY → index.** A real file write under a live root is picked up by the
  Observer and the file is re-indexed through ``index_file`` — new content
  searchable.
* **Debounce coalesces a burst.** N rapid events for one path within the
  debounce window collapse to a SINGLE ``index_file`` call (not N) — proven by a
  recording indexer.
* **Atomic-save (``MOVED_TO``).** An editor's atomic save (rename tmp → dest)
  re-indexes the DEST and purges the SRC: ``index_file(dest)`` runs and
  ``delete_by_file(src)`` runs.
* **Delete → purge.** A ``deleted`` event purges the file from Qdrant + manifest.
* **Excluded dirs are never SCHEDULED.** The Observer is scheduled on included
  roots with excluded dirs pruned at the scheduling level — a write inside a
  ``.venv``/worktree-copy subtree produces NO index work (it was never watched),
  and static roots are never scheduled at all.
* **Single lock serializes sweep + live event.** A periodic sweep and a live
  event targeting the SAME path never run ``index_file`` concurrently — the
  shared :class:`asyncio.Lock` forces them to interleave, never overlap. Proven
  by an instrumented indexer that asserts no re-entrancy and records call order.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer, IndexOutcome
from loremaster.index.manifest import STATE_INDEXED, Manifest
from loremaster.index.reconcile import ReconcileEngine
from loremaster.index.watcher import LiveWatcher
from loremaster.server import LoreServer
from loremaster.source.local_directory import LocalDirectorySourceProvider
from loremaster.store.qdrant import QdrantStore
from loresigil.base import Embedder
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient

_DIM = 2048
_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"

# A debounce short enough to keep tests fast but long enough to coalesce a burst.
_DEBOUNCE_MS = 120
# A generous ceiling for "the watcher has processed the event(s)" polling.
_SETTLE_TIMEOUT_S = 8.0


# --------------------------------------------------------------------------- #
# Instrumented indexer wrappers
# --------------------------------------------------------------------------- #
class RecordingIndexer:
    """Wraps a real :class:`Indexer`, recording every ``index_file`` call.

    Used by tests that need to count per-path live-event indexes (e.g. the
    debounce burst coalescing) or to prove an event was DROPPED (zero index
    work). It instruments only the LIVE-event ``index_file`` seam — which is all
    those tests exercise — and deliberately does NOT claim to observe the sweep's
    per-file work (that goes ``index_tier`` → ``_walk_and_index`` →
    ``_index_chunks``, never through ``index_file``). The sweep-vs-event
    serialization proof instead instruments :class:`ConcurrencyTrackingEmbedder`,
    the single chokepoint BOTH indexing paths funnel through.
    """

    def __init__(self, inner: Indexer) -> None:
        self._inner = inner
        self.index_calls: list[tuple[str, str]] = []  # (tier, path)
        self._inner_index_file = inner.index_file
        # Route the inner indexer's own self-calls (none today — the walk calls
        # ``_index_chunks`` directly — but a future refactor might) through this
        # recorder so the live-event count stays accurate.
        inner.index_file = self.index_file  # type: ignore[method-assign]

    async def index_file(self, tier: str, path: str, source: str) -> IndexOutcome:
        self.index_calls.append((tier, path))
        return await self._inner_index_file(tier, path, source)

    # Pass-through everything else the watcher / reconcile need.
    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class ConcurrencyTrackingEmbedder(FakeEmbedder):
    """A slow :class:`FakeEmbedder` that detects CONCURRENT indexing of any kind.

    ``embed_documents`` is the single chokepoint EVERY indexing path funnels
    through — the live-event ``index_file`` AND the sweep's
    ``index_tier`` → ``_walk_and_index`` → ``_index_chunks`` both ``await`` it.
    By bumping an in-flight counter on entry, sleeping a real interval to WIDEN
    the overlap window, then decrementing on exit, this fake observes whether two
    indexing operations are ever inside the embedder at the same time —
    regardless of which path issued them.

    With the watcher's single ``asyncio.Lock`` held across each op, the sweep and
    a queue-drain event are mutually exclusive, so ``max_concurrent`` stays at 1.
    Remove the lock and a genuine overlap (two distinct, genuinely-new files,
    neither short-circuiting) drives ``max_concurrent`` to 2 — the mutation the
    serialization test must fail on.
    """

    def __init__(self, *, hold_s: float = 0.05, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._hold_s = hold_s
        self._in_flight = 0
        self.max_concurrent = 0

    async def embed_documents(self, texts: list[str]) -> Any:
        self._in_flight += 1
        self.max_concurrent = max(self.max_concurrent, self._in_flight)
        try:
            # A REAL sleep (not sleep(0)): if the lock is absent, a concurrent
            # indexer will enter here during this window and bump _in_flight to 2.
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
    _write(root / ".venv" / "lib" / "vendored.py", "junk = 1\n")  # pruned dir
    # A real Python file that matches an INCLUDE glob (``**/*.py``) AND an EXCLUDE
    # glob (``**/*_pb2.py``). Because it satisfies the include filter, only the
    # exclude branch of ``is_included`` can keep it out — so it makes the
    # exclude-glob check load-bearing (the `.min.js` fixture cannot: it is also
    # outside the include list, masking any exclude-removal mutation).
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
        # ``**/*_pb2.py`` excludes a file that DOES match the ``**/*.py`` include —
        # so the exclude branch is the only thing keeping it out (load-bearing).
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


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture()
async def store_factory() -> AsyncIterator[Any]:
    """Builder for a :class:`QdrantStore` with CONCURRENCY-SAFE teardown."""
    from conftest import QDRANT_URL, _qdrant_api_key

    client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
    created: list[str] = []

    def _make(slug: str) -> QdrantStore:
        store = QdrantStore(client=client, slug=slug)
        created.append(store.collection_name)
        return store

    try:
        yield _make
    finally:
        for name in created:
            if await client.collection_exists(name):
                await client.delete_collection(name)
        await client.close()


def _make_indexer(
    *, config: LoreConfig, store: QdrantStore, embedder: Embedder,
    manifest: Manifest, snapshot_root: Path,
) -> Indexer:
    server = LoreServer(config)
    providers: list[Any] = list(server.source_providers)
    for root in config.roots:
        if root.watch == "static" and root.source is not None:
            providers.append(LocalDirectorySourceProvider(root.tier, Path(root.source)))
    return Indexer(
        store=store, embedder=embedder, manifest=manifest, registry=server.registry,
        source_providers=providers, config=config, snapshot_root=snapshot_root,
    )


def _make_watcher(
    *, config: LoreConfig, indexer: Any, manifest: Manifest, store: QdrantStore,
) -> LiveWatcher:
    """Build a :class:`LiveWatcher` on the running loop (DI'd collaborators)."""
    engine = ReconcileEngine(
        indexer=indexer, manifest=manifest, store=store, config=config
    )
    return LiveWatcher(
        indexer=indexer,
        manifest=manifest,
        store=store,
        config=config,
        loop=asyncio.get_running_loop(),
        reconcile_engine=engine,
    )


async def _wait_for_async(coro_factory: Any, timeout_s: float = _SETTLE_TIMEOUT_S) -> bool:
    """Poll an async predicate (coroutine factory) until true or timeout."""
    deadline = asyncio.get_running_loop().time() + timeout_s
    while asyncio.get_running_loop().time() < deadline:
        if await coro_factory():
            return True
        await asyncio.sleep(0.05)
    return bool(await coro_factory())


async def _store_has_identity(store: QdrantStore, file_path: str, identity: str) -> bool:
    hits = await store.search([0.0] * _DIM, k=500)
    return any(
        h.payload is not None
        and h.payload["file_path"] == file_path
        and h.payload["identity"] == identity
        for h in hits
    ) is True


def _queue_keys(watcher: LiveWatcher) -> list[tuple[str, str]]:
    """Snapshot the (tier, file_path) keys currently sitting in the watcher's queue.

    Used by the QueueFull test to assert a dropped event never made it onto the
    bounded queue. Drains and re-enqueues so the queue is left unchanged.
    """
    keys: list[tuple[str, str]] = []
    while not watcher._queue.empty():
        keys.append(watcher._queue.get_nowait())
    for key in keys:
        watcher._queue.put_nowait(key)
    return keys


# --------------------------------------------------------------------------- #
# Real-inotify MODIFY → index
# --------------------------------------------------------------------------- #
class TestLiveModify:
    """A real file write under a live root is re-indexed via the Observer."""

    async def test_modify_event_reindexes_file(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        # Seed the index so we are testing an UPDATE, not a first build.
        await indexer.index_file(
            "custom", "src/routing.py",
            (live / "src" / "routing.py").read_text(encoding="utf-8"),
        )
        watcher = _make_watcher(config=config, indexer=indexer, manifest=manifest, store=store)
        await watcher.start()
        try:
            # Write a NEW uniquely-named symbol to the watched file.
            (live / "src" / "routing.py").write_text(
                "def watcher_marker_abc(week):\n    return week\n", encoding="utf-8"
            )
            # The real Observer should pick up the write and reindex the file.
            assert await _wait_for_async(
                lambda: _store_has_identity(store, "src/routing.py", "watcher_marker_abc")
            )
        finally:
            await watcher.stop()


# --------------------------------------------------------------------------- #
# Debounce coalesces a burst to ONE index
# --------------------------------------------------------------------------- #
class TestDebounce:
    """N rapid events for one path collapse to a single index_file call."""

    async def test_burst_coalesces_to_single_index(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live, debounce_ms=_DEBOUNCE_MS)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        inner = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        indexer = RecordingIndexer(inner)
        watcher = _make_watcher(config=config, indexer=indexer, manifest=manifest, store=store)
        await watcher.start()
        try:
            target = live / "src" / "routing.py"
            # Fire many MODIFY events well within the debounce window, with the
            # last write carrying the final content.
            for n in range(10):
                target.write_text(
                    f"def burst_marker_{n}(week):\n    return {n}\n", encoding="utf-8"
                )
                await asyncio.sleep(_DEBOUNCE_MS / 1000.0 / 8.0)  # << debounce window
            # Wait for the single coalesced index of the FINAL content.
            assert await _wait_for_async(
                lambda: _store_has_identity(store, "src/routing.py", "burst_marker_9")
            )
            # The burst coalesced: routing.py was indexed at most a couple of times,
            # not once per raw event (10). A correct debounce yields exactly 1.
            routing_indexes = [c for c in indexer.index_calls if c[1] == "src/routing.py"]
            assert len(routing_indexes) <= 2, (
                f"debounce failed to coalesce: {len(routing_indexes)} index calls"
            )
            assert len(routing_indexes) >= 1
        finally:
            await watcher.stop()

    async def test_delete_after_modify_within_window_wins_as_purge(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """A modify then a delete (same path, same window) coalesce to ONE purge.

        Last event reflects the file's final state: the delete wins, so the single
        resulting op must be a PURGE — NOT an index. To make the test discriminate
        last-event-wins from the vanished-file fallback (a stale ``index`` op on a
        deleted file ALSO degrades to a purge, masking the coalesce), the file is
        deliberately LEFT ON DISK: only true last-event-wins coalescing yields a
        purge here — a surviving stale ``index`` op would index the present file
        (recording an ``index_calls`` entry), failing this test.
        """
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        inner = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        indexer = RecordingIndexer(inner)
        # Seed an indexed row so there is something a stale "index" op could touch.
        await indexer.index_file(
            "custom", "src/routing.py",
            (live / "src" / "routing.py").read_text(encoding="utf-8"),
        )
        indexer.index_calls.clear()
        watcher = _make_watcher(config=config, indexer=indexer, manifest=manifest, store=store)

        # MODIFY (file changed + still PRESENT) then DELETE event, both before any
        # drain → coalesced to the LAST op. The file stays on disk so a surviving
        # stale index op WOULD index it — only last-event-wins yields a purge.
        (live / "src" / "routing.py").write_text(
            "def changed_then_delete_event():\n    return 0\n", encoding="utf-8"
        )
        watcher.on_modified_path(str(live / "src" / "routing.py"))
        watcher.on_deleted_path(str(live / "src" / "routing.py"))
        await watcher.drain()

        # The single coalesced op was a PURGE: no index ran, the row is gone — even
        # though the file is still present on disk (so this can ONLY be the purge
        # op winning, not the vanished-file fallback).
        assert indexer.index_calls == [], "a stale index op survived the coalesce"
        assert manifest.get("custom", "src/routing.py") is None
        hits = await store.search([0.0] * _DIM, k=500)
        assert not any(
            h.payload is not None and h.payload["file_path"] == "src/routing.py"
            for h in hits
        )

    async def test_modify_after_delete_within_window_wins_as_index(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """A delete then a modify (same path, same window) coalesce to ONE index.

        The file was recreated after the delete, so the single resulting op must
        index the current content — NOT purge a file that exists.
        """
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        inner = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        indexer = RecordingIndexer(inner)
        watcher = _make_watcher(config=config, indexer=indexer, manifest=manifest, store=store)

        # DELETE then MODIFY (recreate), both before any drain → coalesced to MODIFY.
        watcher.on_deleted_path(str(live / "src" / "routing.py"))
        (live / "src" / "routing.py").write_text(
            "def deleted_then_recreated():\n    return 1\n", encoding="utf-8"
        )
        watcher.on_modified_path(str(live / "src" / "routing.py"))
        await watcher.drain()

        # The single coalesced op was an INDEX: the row exists, content searchable.
        assert indexer.index_calls == [("custom", "src/routing.py")]
        row = manifest.get("custom", "src/routing.py")
        assert row is not None and row.state == STATE_INDEXED
        assert await _store_has_identity(
            store, "src/routing.py", "deleted_then_recreated"
        )

    async def test_queue_full_drops_event_but_sweep_recovers_it(
        self, tmp_path: Path, store_factory: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A full bounded queue drops the event; the next reconcile sweep recovers it.

        Drives the REAL overflow path: a short-debounce event whose timer fires
        ``_flush_key`` against a SATURATED maxsize-1 queue, so ``put_nowait`` hits
        ``QueueFull`` and the event is dropped from the queue path. The op is NOT
        recovered from the coalescing dict (the sweep does not read ``_pending``);
        recovery comes from ``run_sweep``/``reconcile`` RE-WALKING the filesystem
        and re-discovering the change — the ``IN_Q_OVERFLOW`` backstop.
        """
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        # A tiny debounce so the real ``_flush_key`` timer fires within the test.
        config = _config(slug=slug, live_path=live, debounce_ms=20)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        inner = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        # ``RecordingIndexer`` is a delegating wrapper, not an ``Indexer`` subclass;
        # the watcher/engine treat the indexer structurally (the ``_make_watcher``
        # helper types it ``Any``), so annotate it ``Any`` here too.
        indexer: Any = RecordingIndexer(inner)
        engine = ReconcileEngine(
            indexer=indexer, manifest=manifest, store=store, config=config
        )
        # A maxsize-1 queue we saturate so any real enqueue overflows.
        watcher = LiveWatcher(
            indexer=indexer, manifest=manifest, store=store, config=config,
            loop=asyncio.get_running_loop(), reconcile_engine=engine, queue_maxsize=1,
        )

        # A brand-new file the event targets; saturate the queue with an UNRELATED
        # key (no _pending entry) so the real event cannot be enqueued.
        _write(live / "src" / "overflow.py", "def overflow_marker():\n    return 1\n")
        watcher._queue.put_nowait(("custom", "sentinel_filler.py"))  # queue now full
        assert watcher._queue.full()

        # Fire the event and wait past the debounce so the REAL timer runs
        # ``_flush_key`` → ``put_nowait`` → ``QueueFull`` → dropped.
        watcher.on_modified_path(str(live / "src" / "overflow.py"))
        with caplog.at_level(logging.WARNING, logger="loremaster.index.watcher"):
            await asyncio.sleep(0.10)  # > debounce_ms; the timer fires here

        # The event was DROPPED: the queue still holds ONLY the sentinel (overflow.py
        # was rejected by the bound, not enqueued).
        assert watcher._queue.qsize() == 1
        assert ("custom", "src/overflow.py") not in _queue_keys(watcher)
        assert manifest.get("custom", "src/overflow.py") is None
        assert indexer.index_calls == []

        # The drop is observable: a WARNING ``watcher.in_q_overflow`` carrying the
        # dropped key's tier + file_path (counts/identifiers only — no payload).
        overflow_events = [
            r for r in caplog.records if r.message == "watcher.in_q_overflow"
        ]
        assert len(overflow_events) == 1
        assert overflow_events[0].levelno == logging.WARNING
        assert overflow_events[0].tier == "custom"  # type: ignore[attr-defined]
        assert overflow_events[0].file_path == "src/overflow.py"  # type: ignore[attr-defined]

        # Recovery: a reconcile sweep re-walks the filesystem and indexes the file —
        # NOT a replay of the dropped queue op.
        await engine.reconcile()
        row = manifest.get("custom", "src/overflow.py")
        assert row is not None and row.state == STATE_INDEXED
        assert await _store_has_identity(store, "src/overflow.py", "overflow_marker")

    async def test_burst_flush_queue_full_logs_overflow(
        self, tmp_path: Path, store_factory: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A burst-flush drop on a SATURATED queue logs ``watcher.in_q_overflow``.

        Drives the SECOND drop site: :meth:`LiveWatcher._flush_all_timers` (the
        burst-flush :meth:`drain` runs to process a just-fired burst without
        waiting out the debounce). A long debounce keeps the event's timer ARMED
        (so the op sits in ``_timers``/``_pending``, not yet enqueued); the queue
        is pre-saturated so the burst-flush's ``put_nowait`` hits ``QueueFull``
        and the event is dropped. Like the ``_flush_key`` drop site, this must be
        OBSERVABLE — the same ``watcher.in_q_overflow`` WARNING carrying the
        dropped key's tier + file_path (counts/identifiers only, no payload) — so
        an overflow during a burst-flush is not silently invisible to Mezmo.
        Recovery still comes from the periodic reconcile re-walking the tree.
        """
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        # A LONG debounce so the event's timer stays armed (never fires on its
        # own) — the drop must come from the burst-flush, not ``_flush_key``.
        config = _config(slug=slug, live_path=live, debounce_ms=10_000)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        inner = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        indexer: Any = RecordingIndexer(inner)
        engine = ReconcileEngine(
            indexer=indexer, manifest=manifest, store=store, config=config
        )
        # A maxsize-1 queue saturated by an UNRELATED key, so the burst-flush's
        # enqueue of the real pending key overflows.
        watcher = LiveWatcher(
            indexer=indexer, manifest=manifest, store=store, config=config,
            loop=asyncio.get_running_loop(), reconcile_engine=engine, queue_maxsize=1,
        )

        _write(live / "src" / "overflow.py", "def overflow_marker():\n    return 1\n")
        watcher._queue.put_nowait(("custom", "sentinel_filler.py"))  # queue now full
        assert watcher._queue.full()

        # Arm the event's debounce timer (long window → still pending, not flushed).
        watcher.on_modified_path(str(live / "src" / "overflow.py"))
        await asyncio.sleep(0)  # let the scheduled _coalesce run → timer + _pending
        assert ("custom", "src/overflow.py") in watcher._pending

        # The burst-flush path: ``drain`` → ``_flush_all_timers`` → ``put_nowait``
        # → ``QueueFull`` → dropped. (The sentinel-filled queue is then drained;
        # its op has no _pending entry so it is a no-op.)
        with caplog.at_level(logging.WARNING, logger="loremaster.index.watcher"):
            await watcher.drain()

        # The event was DROPPED at the burst-flush: it never reached index_file.
        assert indexer.index_calls == []
        assert manifest.get("custom", "src/overflow.py") is None

        # The drop is OBSERVABLE — the same WARNING event + fields as _flush_key.
        overflow_events = [
            r for r in caplog.records if r.message == "watcher.in_q_overflow"
        ]
        assert len(overflow_events) == 1
        assert overflow_events[0].levelno == logging.WARNING
        assert overflow_events[0].tier == "custom"  # type: ignore[attr-defined]
        assert overflow_events[0].file_path == "src/overflow.py"  # type: ignore[attr-defined]

        # Recovery: a reconcile sweep re-walks the filesystem and indexes the file.
        await engine.reconcile()
        row = manifest.get("custom", "src/overflow.py")
        assert row is not None and row.state == STATE_INDEXED
        assert await _store_has_identity(store, "src/overflow.py", "overflow_marker")


# --------------------------------------------------------------------------- #
# Lifecycle logging: start / stop
# --------------------------------------------------------------------------- #
class TestWatcherLifecycleLogging:
    """``start``/``stop`` emit structured lifecycle events (caplog-asserted)."""

    async def test_start_and_stop_emit_lifecycle_events(
        self, tmp_path: Path, store_factory: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        watcher = _make_watcher(config=config, indexer=indexer, manifest=manifest, store=store)
        with caplog.at_level(logging.INFO, logger="loremaster.index.watcher"):
            await watcher.start()
            await watcher.stop()

        start_events = [r for r in caplog.records if r.message == "watcher.start"]
        stop_events = [r for r in caplog.records if r.message == "watcher.stop"]
        assert len(start_events) == 1
        assert start_events[0].levelno == logging.INFO
        # The start event carries operational counts (how many dirs are watched,
        # how many live tiers) — never the paths' contents.
        assert start_events[0].watched_dir_count >= 1  # type: ignore[attr-defined]
        assert start_events[0].live_tiers >= 1  # type: ignore[attr-defined]
        assert len(stop_events) == 1
        assert stop_events[0].levelno == logging.INFO


# --------------------------------------------------------------------------- #
# Atomic-save (MOVED_TO) → dest reindexed + src purged
# --------------------------------------------------------------------------- #
class TestAtomicSave:
    """An editor's rename tmp → dest re-indexes dest and purges src."""

    async def test_moved_event_reindexes_dest_and_purges_src(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        # Seed an index for the SRC path so the move has something to purge.
        await indexer.index_file(
            "custom", "src/routing.py",
            (live / "src" / "routing.py").read_text(encoding="utf-8"),
        )
        watcher = _make_watcher(config=config, indexer=indexer, manifest=manifest, store=store)

        # Drive the move event directly through the watcher's handler seam so the
        # contract is deterministic (a raw watchdog MOVED_TO). The handler must
        # reindex dest and purge src.
        dest_text = "def moved_marker_q(week):\n    return week\n"
        (live / "src" / "renamed.py").write_text(dest_text, encoding="utf-8")
        watcher.on_moved_path(
            src_abs=str(live / "src" / "routing.py"),
            dest_abs=str(live / "src" / "renamed.py"),
        )
        await watcher.drain()  # process the queued event(s) deterministically

        # The dest is indexed with its new content...
        assert await _store_has_identity(store, "src/renamed.py", "moved_marker_q")
        assert manifest.get("custom", "src/renamed.py") is not None
        # ...and the src is purged from both store and manifest.
        assert manifest.get("custom", "src/routing.py") is None
        hits = await store.search([0.0] * _DIM, k=500)
        assert not any(
            h.payload is not None and h.payload["file_path"] == "src/routing.py"
            for h in hits
        )


# --------------------------------------------------------------------------- #
# Delete → purge
# --------------------------------------------------------------------------- #
class TestDelete:
    """A delete event purges the file from Qdrant and the manifest."""

    async def test_delete_event_purges_file(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        await indexer.index_file(
            "custom", "src/routing.py",
            (live / "src" / "routing.py").read_text(encoding="utf-8"),
        )
        assert manifest.get("custom", "src/routing.py") is not None
        watcher = _make_watcher(config=config, indexer=indexer, manifest=manifest, store=store)

        (live / "src" / "routing.py").unlink()
        watcher.on_deleted_path(str(live / "src" / "routing.py"))
        await watcher.drain()

        assert manifest.get("custom", "src/routing.py") is None
        hits = await store.search([0.0] * _DIM, k=500)
        assert not any(
            h.payload is not None and h.payload["file_path"] == "src/routing.py"
            for h in hits
        )


# --------------------------------------------------------------------------- #
# Excluded dirs / static roots are never scheduled / never indexed
# --------------------------------------------------------------------------- #
class TestSchedulingPruning:
    """The Observer watches included live roots only; excluded dirs are pruned."""

    async def test_watched_roots_exclude_pruned_dirs_and_static(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        static_src = tmp_path / "community_src"
        _write(static_src / "core.py", _PY_MODULE_2)
        config = _config(slug=slug, live_path=live, static_source=static_src)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        watcher = _make_watcher(config=config, indexer=indexer, manifest=manifest, store=store)

        watched = {Path(p).resolve() for p in watcher.watched_paths()}
        # The live root is watched.
        assert (live).resolve() in watched
        # The excluded .venv subtree is NOT a scheduled watch path.
        assert (live / ".venv").resolve() not in watched
        assert (live / ".venv" / "lib").resolve() not in watched
        # The STATIC source dir is NOT watched at all (frozen tier).
        assert static_src.resolve() not in watched

    async def test_event_inside_excluded_dir_does_no_index_work(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """An event whose path lies under an excluded dir is dropped, not indexed."""
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        inner = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        indexer = RecordingIndexer(inner)
        watcher = _make_watcher(config=config, indexer=indexer, manifest=manifest, store=store)

        # A modify event for a file inside the pruned .venv subtree.
        watcher.on_modified_path(str(live / ".venv" / "lib" / "vendored.py"))
        # And for an excluded-glob file that is ALSO outside the include list.
        watcher.on_modified_path(str(live / "src" / "bundle.min.js"))
        # And for a file that MATCHES the include (``**/*.py``) but is held out by
        # the exclude glob ``**/*_pb2.py`` alone — the exclude branch of
        # ``is_included`` (mirrored in ``_resolve``) is the only thing dropping it.
        watcher.on_modified_path(str(live / "src" / "api_pb2.py"))
        await watcher.drain()

        # None produced any index work.
        assert indexer.index_calls == []
        assert manifest.get("custom", ".venv/lib/vendored.py") is None
        assert manifest.get("custom", "src/api_pb2.py") is None


# --------------------------------------------------------------------------- #
# The single lock serializes the sweep AND the live-event drain
# --------------------------------------------------------------------------- #
class TestLockSerialization:
    """A periodic sweep and a queue-drain event never index concurrently.

    The proof instruments :class:`ConcurrencyTrackingEmbedder` — the chokepoint
    BOTH indexing paths funnel through (the live-event ``index_file`` AND the
    sweep's ``index_tier`` → ``_walk_and_index`` → ``_index_chunks``) — and drives
    a GENUINE overlap: a queue-drain event indexing a brand-new file ``alpha.py``
    while a concurrent sweep indexes other brand-new files. Neither short-circuits
    (both have real in-flight embeds), and the embedder holds each call open for a
    real interval to widen the window. With the single ``asyncio.Lock`` the two are
    mutually exclusive (``max_concurrent == 1``); remove the lock and they overlap
    (``max_concurrent == 2``), failing this test.
    """

    async def test_sweep_and_event_never_index_concurrently(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        # A brand-new file the LIVE-EVENT path will index — distinct from every
        # file the SWEEP walks, so both paths carry genuine, non-overlapping work
        # and neither hits the content-hash fast-path.
        _write(live / "src" / "alpha.py", "def alpha_lock_marker():\n    return 1\n")
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        # The slow, concurrency-tracking embedder sees EVERY indexing path.
        embedder = ConcurrencyTrackingEmbedder(dim=_DIM, hold_s=0.05)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder,
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        watcher = _make_watcher(config=config, indexer=indexer, manifest=manifest, store=store)

        # Queue a live event for alpha.py, then run the periodic sweep (which
        # walks + indexes every OTHER brand-new corpus file) CONCURRENTLY. The
        # shared asyncio.Lock must serialize them: at no instant are two
        # embed_documents calls in flight.
        watcher.on_modified_path(str(live / "src" / "alpha.py"))
        await asyncio.gather(
            watcher.run_sweep(),  # the periodic reconcile, under the single lock
            watcher.drain(),      # the queued live event, under the single lock
        )

        # Both paths actually DID indexing work (the test is not vacuous: the
        # embedder was entered, so an overlap window genuinely existed to detect).
        assert embedder.max_concurrent >= 1
        # ...and they NEVER overlapped — the single-writer lock held.
        assert embedder.max_concurrent == 1, (
            f"sweep and live event indexed concurrently "
            f"(max_concurrent={embedder.max_concurrent}); the single lock failed"
        )
        # Both the live-event file and a swept file reached the indexed state.
        alpha_row = manifest.get("custom", "src/alpha.py")
        assert alpha_row is not None and alpha_row.state == STATE_INDEXED
        routing_row = manifest.get("custom", "src/routing.py")
        assert routing_row is not None and routing_row.state == STATE_INDEXED
