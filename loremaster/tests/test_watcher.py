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
* **RESTORED (ledger #33 — test-restoration audit)** — the REAL-inotify
  end-to-end tests that drive an actual watchdog ``Observer`` over ``tmp_path``
  were dropped by the P5-C3b port (a fresh-context audit found none of the
  ported tests call ``watcher.start()``): ``TestLiveModify``, the real-timer
  burst-coalescing count (``TestDebounce``), the start/stop lifecycle-log test
  (``TestWatcherLifecycleLogging``), the recursive-watch nested-indexing +
  excluded-subtree event-scope regression guards
  (``TestRecursiveWatchStillIndexesNestedFile`` /
  ``TestRecursiveWatchStillFiltersExcludedSubtree``), and the watch-SCHEDULING
  scope tests that inspect the running Observer's OWN inotify watch set —
  ground truth, not the pure/tautological ``watcher.watched_paths()`` computation
  already covered by ``TestSchedulingPruning`` (``TestWatchScopeExcludesNoisySubtrees``
  / ``TestRuntimeNewDirWatchScope``). These are restored here onto the SAME async
  Surreal fakes the rest of this file uses (store/manifest assertions read
  ``trio.store``/``trio.manifest`` — the fakes are orthogonal to the real
  watchdog Observer under test) rather than the old real-Qdrant + SQLite
  fixtures, keeping the file's fixture story single. Two items the audit
  explicitly flagged as intentionally NOT restored live in OTHER files, not
  here: ``TestStoreFailureIsolation`` (``test_indexer.py`` — superseded, no
  retry layer by design) and the two search oracles (P6 scope).
* **RESTORED (P6 read-path cutover, 8ae67ab)** — the two search-oracle tests
  commit 53db748 explicitly deferred: ``TestLiveModify.
  test_modify_event_content_becomes_searchable_via_search_code`` and
  ``TestDelete.test_delete_event_content_no_longer_searchable_via_search_code``.
  Archaeology note: in the PRE-PORT file (``git show df5431e~1``), the
  ``store.search([0.0] * _DIM, k=500)`` calls at old lines 313/470/742/781 were
  ALWAYS a raw broad scan against the real backend (Qdrant), never a call
  through a query-time ranking/formatting pipeline — no such pipeline existed
  before P6. The C3 port's ``_has_identity``/``stored_file_paths()`` fake-state
  reads are an equally-faithful port of THAT raw-scan shape (they already cover
  the debounce-coalesce purge and atomic-move purge assertions). What was
  genuinely deferred — and is restored here as NEW coverage, not a literal
  reinstatement — is a round trip through the REAL :class:`~loremaster.search.
  SearchPipeline`: now that it reads the SAME ``FakeSurrealStore`` the indexer
  writes through in this file's fixtures, these two tests prove new content is
  retrievable via ``search_code`` after a live modify, and a deleted file's
  content is NOT (honest emptiness, never stale serving) after a live delete —
  the flagship presence/absence duo the module docstring's headline contract
  bullets ("new content searchable" / "purges the file") describe.
"""

from __future__ import annotations

import asyncio
import inspect as _inspect_for_overflow_guard
import logging
import os
import struct as _struct_for_overflow_guard
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from _surreal_fakes import FakeSurrealTrio, fake_surreal_trio
from loremaster.config import LoreConfig
from loremaster.extension import ExtensionContext
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.indexer import Indexer, IndexOutcome
from loremaster.index.reconcile import ReconcileEngine
from loremaster.index.surreal_manifest import STATE_INDEXED, SurrealManifest
from loremaster.index.watcher import LiveWatcher, _OverflowAwareInotify
from loremaster.search import SearchPipeline, SearchResult
from loremaster.server import LoreServer
from loremaster.store.surreal import SurrealStore
from loresigil.base import Embedder
from loresigil.testing import FakeEmbedder
from watchdog.observers.inotify_c import Inotify as _WatchdogInotify
from watchdog.observers.inotify_c import InotifyConstants as _WatchdogInotifyConstants

_DIM = 2048
_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"

_DEBOUNCE_MS = 120
_SETTLE_TIMEOUT_S = 8.0

# Comfortably above the tiny live corpus's total chunk count (1-2 files) in the
# two P6 search-oracle tests below, so a single ``hybrid_search`` call can
# always retrieve every candidate — mirrors the pre-port fixture's generous
# k=500 (see the module docstring's archaeology note) scaled down for this
# file's much smaller corpus.
_SEARCH_K = 20


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


# A live root whose excluded subtree (``__pycache__``) is DEEP and WIDE, so the
# per-dir recursive watch would install MANY watches there (the production
# explosion in miniature). The in-scope tree stays small, so the post-fix watch
# count is a small, bounded set a test can pin exactly.
_EXCLUDED_NESTED_SUBDIRS: tuple[str, ...] = (
    f"pkg/{_EXCLUDED_DIR_NAME}",
    f"pkg/{_EXCLUDED_DIR_NAME}/nested_a",
    f"pkg/{_EXCLUDED_DIR_NAME}/nested_a/deeper",
    f"pkg/{_EXCLUDED_DIR_NAME}/nested_b",
    f"services/{_EXCLUDED_DIR_NAME}",
    f"services/{_EXCLUDED_DIR_NAME}/cache_inner",
)


def _build_corpus_with_big_excluded_subtree(root: Path) -> None:
    """A wide INCLUDED tree plus a wide EXCLUDED (``__pycache__``) subtree.

    Mirrors the production failure mode in miniature: the excluded tree holds a
    real file per dir so the dir physically exists and a naive recursive watch
    (or an unpruned ``os.walk``) would descend it absent the exclude_dirs prune.
    """
    _build_wide_live_corpus(root)
    for rel in _EXCLUDED_NESTED_SUBDIRS:
        _write(root / rel / "artifact.pyc.py", "def excluded_artifact():\n    return 1\n")


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


def _make_search_pipeline(
    *, config: LoreConfig, trio: FakeSurrealTrio, embedder: Embedder
) -> SearchPipeline:
    """Wire a v2 :class:`SearchPipeline` directly over ``trio`` (the P6 read path).

    Inlined here rather than imported from ``test_search.py`` — this suite does
    not cross-import test helpers across modules. Builds a BARE :class:`LoreServer`
    (no extension hooks) plus a runtime :class:`ExtensionContext` over the SAME
    (fake) store/manifest the watcher/indexer just wrote through, so
    ``search_code`` performs a genuine end-to-end READ of what the live event
    committed — never a peek at the fake's internal ``db.chunks`` dict.
    """
    server = LoreServer(config)
    extension_context = ExtensionContext(
        store=trio.store,
        embedder=embedder,
        config=config,
        count_tokens=embedder.count_tokens,
        manifest=trio.manifest,
    )
    return SearchPipeline(
        store=cast(SurrealStore, trio.store),
        embedder=embedder,
        server=server,
        manifest=cast(SurrealManifest, trio.manifest),
        config=config,
        extension_context=extension_context,
        code_graph=cast(SurrealCodeGraph, trio.graph),
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


async def _wait_for(predicate: Callable[[], bool], timeout_s: float = _SETTLE_TIMEOUT_S) -> bool:
    """Poll a SYNC predicate until it is true or ``timeout_s`` elapses.

    The real-Observer end-to-end tests below drive an actual watchdog thread,
    which marshals events onto the loop asynchronously — a test must poll rather
    than assume synchronous delivery. The fakes' state (``trio.store.db.chunks``,
    the running Observer's own inotify watch set) is read synchronously, so a
    single sync-predicate poller covers both the store-identity and the
    inotify-watch-set oracles. Always evaluates one final time after the
    deadline so a check that becomes true exactly at the boundary is not lost.
    """
    deadline = asyncio.get_running_loop().time() + timeout_s
    while asyncio.get_running_loop().time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.05)
    return bool(predicate())


async def _wait_for_search_result(
    pipeline: SearchPipeline,
    query: str,
    predicate: Callable[[list[SearchResult]], bool],
    *,
    timeout_s: float = _SETTLE_TIMEOUT_S,
) -> list[SearchResult]:
    """Poll ``pipeline.search_code(query)`` until ``predicate(results)`` holds.

    The ORACLE polled here is ``search_code`` itself — the real query-time read
    path (embed → hybrid_search → augment/rerank → format) — never a peek at
    the fake's internal state; this is what makes the two P6 search-oracle
    tests below a genuine round-trip guard rather than a restatement of
    ``_has_identity``. The real-Observer tests can't assume synchronous
    delivery (inotify events are marshalled onto the loop from a background
    thread via ``call_soon_threadsafe``), hence the bounded poll. Always
    evaluates one final time after the deadline so a transition landing
    exactly at the boundary is not lost (mirrors :func:`_wait_for`).
    """
    deadline = asyncio.get_running_loop().time() + timeout_s
    results: list[SearchResult] = await pipeline.search_code(query, k=_SEARCH_K)
    while not predicate(results):
        if asyncio.get_running_loop().time() >= deadline:
            return results
        await asyncio.sleep(0.05)
        results = await pipeline.search_code(query, k=_SEARCH_K)
    return results


def _inotify_watched_dirs(watcher: LiveWatcher) -> set[Path]:
    """The set of directories the watcher's RUNNING observer holds inotify watches for.

    Reaches through the (single, recursive) emitter → its ``InotifyBuffer`` →
    the backing ``Inotify`` instance's ``_wd_for_path`` map (path bytes → watch
    descriptor) — the GROUND TRUTH of which directories actually consumed a
    kernel inotify watch, as opposed to ``watcher.watched_paths()`` (a pure,
    config-derived computation of what the watcher INTENDS to schedule).
    Requires the observer to have been started (so ``on_thread_start`` opened
    the inotify instance); poll-wait on a non-empty result before asserting.
    """
    observer = watcher._observer
    assert observer is not None, "observer not started"
    watched: set[Path] = set()
    for emitter in observer.emitters:
        inotify_buffer = getattr(emitter, "_inotify", None)
        if inotify_buffer is None:
            continue
        inotify = getattr(inotify_buffer, "_inotify", None)
        if inotify is None:
            continue
        for path_bytes in inotify._wd_for_path:
            watched.add(Path(os.fsdecode(path_bytes)).resolve())
    return watched


# --------------------------------------------------------------------------- #
# Real-inotify MODIFY → index (RESTORED — ledger #33; real watchdog Observer)
# --------------------------------------------------------------------------- #
class TestLiveModify:
    """A real file write under a live root is re-indexed via the Observer."""

    async def test_modify_event_reindexes_file(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        # Seed the index so we are testing an UPDATE, not a first build.
        await indexer.index_file(
            "custom", "src/routing.py",
            (live / "src" / "routing.py").read_text(encoding="utf-8"),
        )
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)
        await watcher.start()
        try:
            # Write a NEW uniquely-named symbol to the watched file.
            (live / "src" / "routing.py").write_text(
                "def watcher_marker_abc(week):\n    return week\n", encoding="utf-8"
            )
            # The real Observer should pick up the write and reindex the file.
            assert await _wait_for(
                lambda: _has_identity(trio, "src/routing.py", "watcher_marker_abc")
            )
        finally:
            await watcher.stop()

    async def test_modify_event_content_becomes_searchable_via_search_code(
        self, tmp_path: Path
    ) -> None:
        """P6 search-oracle restoration (see module docstring archaeology note).

        Proves the FULL watcher -> indexer -> store -> :class:`SearchPipeline`
        round trip the P6 read-path cutover (8ae67ab) makes closable: a real
        inotify write's new content is retrievable through ``search_code`` —
        not merely present in the fake's internal chunk dict (that narrower
        claim is already pinned by ``test_modify_event_reindexes_file`` above).
        """
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        embedder = FakeEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        # Seed the index so we are testing an UPDATE, not a first build.
        await indexer.index_file(
            "custom", "src/routing.py",
            (live / "src" / "routing.py").read_text(encoding="utf-8"),
        )
        pipeline = _make_search_pipeline(config=config, trio=trio, embedder=embedder)
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)
        await watcher.start()
        try:
            # Write a NEW uniquely-named symbol to the watched file.
            marker = "watcher_marker_search_e2e"
            (live / "src" / "routing.py").write_text(
                f"def {marker}(week):\n    return week\n", encoding="utf-8"
            )
            results = await _wait_for_search_result(
                pipeline, marker, lambda rs: any(marker in r.formatted for r in rs),
            )
            assert any(marker in r.formatted for r in results), (
                f"search_code never surfaced {marker!r} after the real-inotify "
                f"modify settled — results: {[r.formatted for r in results]}"
            )
        finally:
            await watcher.stop()


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
# Debounce coalescing count under the REAL Observer/timer
# (RESTORED — ledger #33; distinct from TestDebounceCoalesce's seam-driven
# last-event-wins pair above — this proves N RAPID REAL writes collapse to a
# single index_file call via the real debounce timer, not a hand-fired seam).
# --------------------------------------------------------------------------- #
class TestDebounce:
    """N rapid events for one path collapse to a single ``index_file`` call."""

    async def test_burst_coalesces_to_single_index(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live, debounce_ms=_DEBOUNCE_MS)
        trio = _trio()
        inner = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        indexer = RecordingIndexer(inner)
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)
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
            assert await _wait_for(
                lambda: _has_identity(trio, "src/routing.py", "burst_marker_9")
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


# --------------------------------------------------------------------------- #
# Lifecycle logging: start / stop (RESTORED — ledger #33)
# --------------------------------------------------------------------------- #
class TestWatcherLifecycleLogging:
    """``start``/``stop`` emit structured lifecycle events (caplog-asserted)."""

    async def test_start_and_stop_emit_lifecycle_events(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)
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

    async def test_delete_event_content_no_longer_searchable_via_search_code(
        self, tmp_path: Path
    ) -> None:
        """P6 search-oracle restoration (see module docstring archaeology note).

        The dual of ``test_modify_event_content_becomes_searchable_via_search_code``:
        proves a REAL inotify delete makes the file's content UNRETRIEVABLE
        through ``search_code`` — honest emptiness, never a stale hit for
        content that no longer exists on disk. Driven through the real
        watchdog Observer (a physical ``unlink()``), not the seam call
        ``on_deleted_path`` above — this is the read-side, full-loop guard;
        ``test_delete_event_purges_file`` above already pins the write-side
        (fake-state) purge via the deterministic seam.
        """
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        embedder = FakeEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        seed_source = (live / "src" / "routing.py").read_text(encoding="utf-8")
        await indexer.index_file("custom", "src/routing.py", seed_source)
        pipeline = _make_search_pipeline(config=config, trio=trio, embedder=embedder)

        # Baseline: the seeded content IS searchable BEFORE the delete — proves
        # the post-delete absence below is a real transition, not a query that
        # was always going to return nothing (a vacuous pass).
        marker = "champion_routing"
        baseline = await pipeline.search_code(marker, k=_SEARCH_K)
        assert any(marker in r.formatted for r in baseline), (
            "the search oracle must find the seeded content BEFORE deleting it, "
            "otherwise 'not found after delete' would be a vacuous pass"
        )

        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)
        await watcher.start()
        try:
            (live / "src" / "routing.py").unlink()
            # The real Observer's DELETE event purges the file end-to-end.
            results = await _wait_for_search_result(
                pipeline, marker, lambda rs: not any(marker in r.formatted for r in rs),
            )
            assert not any(marker in r.formatted for r in results), (
                f"search_code still surfaced {marker!r} after the real-inotify "
                f"delete settled — stale serving: {[r.formatted for r in results]}"
            )
        finally:
            await watcher.stop()


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
# (2) Live indexing still works under the recursive watch (nested INCLUDED dir)
# (RESTORED — ledger #33; real watchdog Observer)
# --------------------------------------------------------------------------- #
class TestRecursiveWatchStillIndexesNestedFile:
    """An edit to a file in a NESTED included subdir is still detected + indexed.

    Proves the move to ONE recursive watch per root did not break the live path:
    a real write deep under the root (``services/routing/module.py``) is picked
    up by the single recursive Observer and re-indexed through ``index_file`` —
    new content searchable.
    """

    async def test_nested_modify_event_reindexes_file(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_wide_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        nested_rel = "services/routing/module.py"
        # Seed the index so this is an UPDATE under the recursive watch.
        await indexer.index_file(
            "custom", nested_rel, (live / nested_rel).read_text(encoding="utf-8"),
        )
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)
        await watcher.start()
        try:
            # Write a NEW uniquely-named symbol DEEP in the nested subtree — the
            # recursive watch must still observe it.
            (live / nested_rel).write_text(
                "def nested_recursive_marker(week):\n    return week\n",
                encoding="utf-8",
            )
            assert await _wait_for(
                lambda: _has_identity(trio, nested_rel, "nested_recursive_marker")
            )
        finally:
            await watcher.stop()


# --------------------------------------------------------------------------- #
# (3) Excluded subtree STILL filtered at EVENT time (regression guard)
# (RESTORED — ledger #33; seam-driven, matching the original fixture faithfully)
# --------------------------------------------------------------------------- #
class TestRecursiveWatchStillFiltersExcludedSubtree:
    """An edit under an EXCLUDED dir is NOT indexed, though now physically watched.

    The recursive-watch scaling fix moves pruning from SCHEDULE time (per-dir,
    excluded dirs never scheduled) to EVENT time only (one recursive watch
    physically observes the excluded subtree, and ``_resolve`` must drop its
    events). This is the regression guard for that move: a write under the
    configured ``exclude_dirs`` entry ``__pycache__`` — which the recursive
    watch DOES see — must still yield ZERO index work. The excluded dir name is
    read from the SAME config field production prunes against, not a
    hand-copied literal.
    """

    async def test_event_under_recursively_watched_excluded_dir_does_no_index(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_wide_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        # The excluded subtree must be one the config actually prunes (shared
        # source of truth), and one the recursive watch would see.
        assert _EXCLUDED_DIR_NAME in config.exclude_dirs
        trio = _trio()
        inner = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        indexer = RecordingIndexer(inner)
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)

        # A modify event for a file inside the recursively-watched EXCLUDED
        # subtree (``pkg/__pycache__/...``). Driven through the handler seam so
        # the contract is deterministic and independent of host inotify headroom.
        excluded_abs = live / "pkg" / _EXCLUDED_DIR_NAME / "module.cpython-314.pyc.py"
        watcher.on_modified_path(str(excluded_abs))
        await watcher.drain()

        # The event-time ``_resolve`` drop filtered it: zero index work, no row.
        assert indexer.index_calls == []
        assert (
            await trio.manifest.get(
                "custom", f"pkg/{_EXCLUDED_DIR_NAME}/module.cpython-314.pyc.py"
            )
            is None
        )

    async def test_nested_included_event_still_indexes_proving_filter_is_selective(
        self, tmp_path: Path
    ) -> None:
        """Control: a sibling INCLUDED nested file DOES index — the filter is
        selective, not a blanket drop of everything under the recursive watch."""
        slug = _slug()
        live = tmp_path / "live"
        _build_wide_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        inner = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        indexer = RecordingIndexer(inner)
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)

        included_rel = "pkg/sub_a/deep/module.py"
        watcher.on_modified_path(str(live / included_rel))
        await watcher.drain()

        # The included nested file WAS indexed (so the exclusion above is a real
        # event-time filter decision, not a corpus artifact).
        assert ("custom", included_rel) in indexer.index_calls
        row = await trio.manifest.get("custom", included_rel)
        assert row is not None and row.state == STATE_INDEXED


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


# --------------------------------------------------------------------------- #
# Watch-SCHEDULING scope excludes noisy subtrees (RESTORED — ledger #33)
# --------------------------------------------------------------------------- #
class TestWatchScopeExcludesNoisySubtrees:
    """The recursive watch installs inotify watches for IN-SCOPE dirs ONLY.

    The core idle-CPU assertion: an excluded directory subtree
    (``exclude_dirs``) gets NO inotify watch, so a tree with a large excluded
    subtree installs only the few real source-dir watches — not one per dir
    across the whole tree. Inspected against the RUNNING observer's backing
    ``Inotify._wd_for_path`` (the ground truth of consumed kernel watches) via
    :func:`_inotify_watched_dirs` — NOT the pure/tautological
    ``watcher.watched_paths()`` already covered by ``TestSchedulingPruning``.
    """

    async def test_excluded_subtree_dirs_get_no_inotify_watch(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_corpus_with_big_excluded_subtree(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)
        await watcher.start()
        try:
            # The setup walk runs on the emitter thread; wait until at least the
            # root watch is installed before inspecting the watch set.
            assert await _wait_for(lambda: live.resolve() in _inotify_watched_dirs(watcher))
            watched = _inotify_watched_dirs(watcher)

            # Every IN-SCOPE directory is watched (root + each included subdir).
            assert live.resolve() in watched
            for rel in _NESTED_INCLUDED_SUBDIRS:
                assert (live / rel).resolve() in watched, (
                    f"in-scope dir {rel!r} lost its watch"
                )

            # NO directory inside an EXCLUDED subtree is watched — neither the
            # ``__pycache__`` dir itself nor any nested dir under it.
            for rel in _EXCLUDED_NESTED_SUBDIRS:
                assert (live / rel).resolve() not in watched, (
                    f"excluded dir {rel!r} consumed an inotify watch — the watch "
                    f"scope did not prune exclude_dirs"
                )

            # The watch count is bounded by the IN-SCOPE dir count (root + the
            # included subdirs), NOT the total dir count (which includes the wide
            # excluded subtree).
            in_scope_dir_count = 1 + len(_NESTED_INCLUDED_SUBDIRS)
            assert len(watched) == in_scope_dir_count, (
                f"watcher holds {len(watched)} inotify watches for "
                f"{in_scope_dir_count} in-scope dirs — excluded subtrees were "
                f"watched too"
            )
        finally:
            await watcher.stop()

    async def test_included_modify_still_indexes_under_pruned_watch(self, tmp_path: Path) -> None:
        """Functional preservation: an edit to an in-scope file is still indexed.

        Pruning excluded subtrees from the watch set must not cost any IN-SCOPE
        coverage — a real write to a nested included file is still observed by
        the (now exclusion-pruned) recursive watch and re-indexed via
        ``index_file``, new content searchable.
        """
        slug = _slug()
        live = tmp_path / "live"
        _build_corpus_with_big_excluded_subtree(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        nested_rel = "pkg/sub_a/deep/module.py"
        await indexer.index_file(
            "custom", nested_rel, (live / nested_rel).read_text(encoding="utf-8"),
        )
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)
        await watcher.start()
        try:
            (live / nested_rel).write_text(
                "def pruned_watch_still_indexes(week):\n    return week\n",
                encoding="utf-8",
            )
            assert await _wait_for(
                lambda: _has_identity(trio, nested_rel, "pruned_watch_still_indexes")
            )
        finally:
            await watcher.stop()


# --------------------------------------------------------------------------- #
# Runtime new-dir watch scope (RESTORED — ledger #33)
# --------------------------------------------------------------------------- #
class TestRuntimeNewDirWatchScope:
    """A NEW in-scope subdir is watched; a NEW excluded subdir is NOT.

    The second watch-add path (runtime, not setup): watchdog adds a watch for
    each newly-created directory under a recursive watch. The fix must apply the
    SAME ``exclude_dirs`` prune there — a new in-scope subdir gets a watch (and
    its files deliver events + index), a new excluded subdir gets NONE (so a
    fresh ``__pycache__`` created at runtime never re-introduces the watch
    explosion the setup prune removed).
    """

    async def test_new_in_scope_subdir_is_watched_and_indexes(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_wide_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)
        await watcher.start()
        try:
            assert await _wait_for(lambda: live.resolve() in _inotify_watched_dirs(watcher))
            # Create a brand-new INCLUDED subdir at runtime, then a file in it.
            new_dir = live / "services" / "fresh_runtime_pkg"
            new_dir.mkdir(parents=True)
            new_file = new_dir / "module.py"
            new_file.write_text(
                "def runtime_new_dir_marker():\n    return 1\n", encoding="utf-8"
            )
            # The new dir got its own watch AND the file event indexed.
            assert await _wait_for(
                lambda: _has_identity(
                    trio, "services/fresh_runtime_pkg/module.py", "runtime_new_dir_marker",
                )
            )
            assert new_dir.resolve() in _inotify_watched_dirs(watcher)
        finally:
            await watcher.stop()

    async def test_new_excluded_subdir_gets_no_watch(self, tmp_path: Path) -> None:
        """A runtime-created EXCLUDED subdir is never watched.

        Creating a ``__pycache__`` at runtime (the common case: the first import
        materialises it) must NOT install a watch — otherwise the setup-time
        prune is undone the moment the interpreter writes a bytecode cache.
        """
        slug = _slug()
        live = tmp_path / "live"
        _build_wide_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        watcher = _make_watcher(config=config, indexer=indexer, trio=trio)
        await watcher.start()
        try:
            assert await _wait_for(lambda: live.resolve() in _inotify_watched_dirs(watcher))
            watched_before = _inotify_watched_dirs(watcher)
            # Create a brand-new EXCLUDED subdir at runtime + a nested dir in it.
            new_excluded = live / "services" / _EXCLUDED_DIR_NAME
            (new_excluded / "inner").mkdir(parents=True)
            (new_excluded / "artifact.pyc.py").write_text(
                "def runtime_excluded_marker():\n    return 1\n", encoding="utf-8"
            )
            # Give the observer time to (not) react to the new dir.
            await asyncio.sleep(0.3)
            watched_after = _inotify_watched_dirs(watcher)

            # Neither the new excluded dir nor its nested child is ever watched.
            assert new_excluded.resolve() not in watched_after, (
                "a runtime-created excluded dir consumed an inotify watch"
            )
            assert (new_excluded / "inner").resolve() not in watched_after
            # And the watch set did not grow beyond what was there before (no
            # excluded dir watches were added).
            assert watched_after == watched_before
        finally:
            await watcher.stop()


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

        # Every repeat FIRED the callback — the only guard against a
        # "fires once then latches off across repeated overflows" regression
        # (detection has no latch by design; restored after being dropped as
        # collateral in the 8ab017c oracle-restoration hunk).
        assert spy.fired == iterations
