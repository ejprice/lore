"""The live inotify watcher — watchdog Observer, debounced, lock-serialized.

This is staleness angle (1) of Deliverable 3 (and the Watcher-concurrency / Q2
section): a continuous live watch over the LIVE roots that re-indexes a file
within ~a debounce window of an edit, so an anti-hallucination tool never serves
stale code for long after a change. It is built on the already-merged
:class:`~loremaster.index.indexer.Indexer` and the
:class:`~loremaster.index.reconcile.ReconcileEngine`.

The concurrency design (the Q2 contract, verified safe in the plan's risk
table):

* **Observer on its own OS thread.** A watchdog :class:`Observer` is scheduled on
  the LIVE roots ONLY, with ``exclude_dirs`` pruned at the SCHEDULING level — a
  ``.venv``/``.git``/worktree-copy subtree is never even watched (the perf rule +
  the "don't index worktrees" rule, one mechanism). STATIC roots are frozen and
  are never scheduled.
* **Thread → loop hand-off.** The observer thread never touches asyncio state
  directly. Its event handler calls :meth:`asyncio.AbstractEventLoop.call_soon_threadsafe`
  to marshal each event onto the loop thread, where it lands in a coalescing
  dict keyed by ``(tier, file_path)``.
* **Debounce + coalesce.** Rapid events for one path within ``debounce_ms``
  collapse to a single pending op (an editor's save storm, a formatter's
  rewrite). A per-key timer flushes the coalesced op onto a bounded
  :class:`asyncio.Queue` once the path goes quiet.
* **Single lock.** A drain worker pulls from the queue and runs
  :meth:`Indexer.index_file` (or a purge) under ONE :class:`asyncio.Lock`. The
  periodic reconcile sweep (:meth:`run_sweep`) acquires the SAME lock — so a live
  event and a sweep never run ``index_file`` concurrently, the single-writer
  guarantee the manifest relies on.

Atomic-save handling: editors save by writing a temp file then renaming it over
the target (``MOVED_TO``). :meth:`on_moved_path` reindexes the destination and
purges the source, so neither a stale source row nor a missing destination is
left behind.

Every collaborator is injected (indexer, manifest, store, config, loop,
reconcile_engine) so the watcher is unit-testable without a server: tests drive
the handler seams (:meth:`on_modified_path`/:meth:`on_deleted_path`/
:meth:`on_moved_path`) directly and call :meth:`drain` for deterministic
processing, while one test drives the REAL Observer over a ``tmp_path`` (inotify
over a real temp dir works on this box).
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver

from loremaster.config import WATCH_LIVE, RootConfig
from loremaster.index.paths import is_included, walked_dirs

if TYPE_CHECKING:
    from loremaster.config import LoreConfig
    from loremaster.graph import CodeGraph
    from loremaster.index.indexer import Indexer
    from loremaster.index.manifest import Manifest
    from loremaster.index.reconcile import ReconcileEngine, ReconcileSummary
    from loremaster.store.qdrant import QdrantStore

logger = logging.getLogger(__name__)

# Pending-op kinds the coalescing dict stores per (tier, file_path).
_OP_INDEX = "index"
_OP_PURGE = "purge"

# A generous bound on the in-flight queue. The coalescing dict already collapses
# a per-path storm to one entry, so this only needs to absorb many DISTINCT paths
# changing at once (a big checkout) before the periodic sweep backstop catches up.
_DEFAULT_QUEUE_MAXSIZE = 10_000


class _WatchdogHandler(FileSystemEventHandler):
    """Translates raw watchdog events into the watcher's handler-seam calls.

    Runs on the OBSERVER thread, so it does nothing but forward to the watcher's
    thread-safe seams (which marshal onto the loop). Directory events are ignored
    — only file changes matter for indexing.
    """

    def __init__(self, watcher: LiveWatcher) -> None:
        self._watcher = watcher

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._watcher.on_modified_path(self._as_str(event.src_path))

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._watcher.on_modified_path(self._as_str(event.src_path))

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._watcher.on_deleted_path(self._as_str(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._watcher.on_moved_path(
                src_abs=self._as_str(event.src_path),
                dest_abs=self._as_str(event.dest_path),
            )

    @staticmethod
    def _as_str(path: str | bytes) -> str:
        """Normalise a watchdog path (str or bytes) to ``str``."""
        return path.decode() if isinstance(path, bytes) else path


class LiveWatcher:
    """A watchdog Observer over the live roots, debounced and lock-serialized.

    Args:
        indexer: The :class:`~loremaster.index.indexer.Indexer` whose
            ``index_file`` performs the per-file pipeline.
        manifest: The SQLite :class:`~loremaster.index.manifest.Manifest`.
        store: The :class:`~loremaster.store.qdrant.QdrantStore` whose
            ``delete_by_file`` purges a deleted/moved-from file's points.
        config: The validated :class:`~loremaster.config.LoreConfig`; its live
            roots drive what is watched.
        loop: The asyncio loop the observer thread marshals events onto.
        reconcile_engine: The :class:`~loremaster.index.reconcile.ReconcileEngine`
            run by :meth:`run_sweep` under the SAME lock as live events.
        queue_maxsize: The bound on the in-flight work queue. Defaults to
            :data:`_DEFAULT_QUEUE_MAXSIZE`; overridable so a deploy can tune the
            bound and tests can exercise the ``QueueFull`` overflow backstop.
        code_graph: Optional :class:`~loremaster.graph.CodeGraph`. When supplied, a
            delete/move-from purge also removes the file's graph slice; ``None``
            disables graph purging (the index path's graph refresh is the
            indexer's concern).
    """

    def __init__(
        self,
        *,
        indexer: Indexer,
        manifest: Manifest,
        store: QdrantStore,
        config: LoreConfig,
        loop: asyncio.AbstractEventLoop,
        reconcile_engine: ReconcileEngine,
        queue_maxsize: int = _DEFAULT_QUEUE_MAXSIZE,
        code_graph: CodeGraph | None = None,
    ) -> None:
        self._indexer = indexer
        self._manifest = manifest
        self._store = store
        self._config = config
        self._loop = loop
        self._reconcile_engine = reconcile_engine
        # Optional code-graph: a delete/move-from purge removes the file's graph
        # slice too (so the graph never serves a symbol whose source is gone). The
        # index path's graph refresh rides through the injected indexer.
        self._code_graph = code_graph

        # The SINGLE writer lock: live events AND the periodic sweep both index
        # under it, so index_file never runs concurrently with itself.
        self._lock = asyncio.Lock()
        # Bounded in-flight queue of (tier, file_path) keys ready to process.
        self._queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue(
            maxsize=queue_maxsize
        )
        # The coalescing layer: (tier, file_path) -> the pending op for it. A
        # burst of events for one path mutates one entry instead of N queue items.
        self._pending: dict[tuple[str, str], _PendingOp] = {}
        # Per-key debounce timer handles, so a fresh event resets the window.
        self._timers: dict[tuple[str, str], asyncio.TimerHandle] = {}

        # ``Observer`` is a factory alias in watchdog; the instance type is
        # ``BaseObserver`` (what is valid as an annotation).
        self._observer: BaseObserver | None = None
        # The continuous background consumer (spun up by ``start``); ``None`` when
        # the watcher is driven purely on demand via ``drain`` (the test seam).
        self._worker: asyncio.Task[None] | None = None
        self._debounce_s = self._config.watcher.debounce_ms / 1000.0
        self._live_roots: list[RootConfig] = [
            root for root in self._config.effective_roots if root.watch == WATCH_LIVE
        ]

    # -- single-writer lock ------------------------------------------------- #

    @property
    def writer_lock(self) -> asyncio.Lock:
        """The SINGLE-writer lock live events AND the periodic sweep index under.

        Exposed so a same-process write path that must not race the watcher (the
        startup schema rebuild) can acquire the EXACT same lock — guaranteeing
        ``index_file`` / ``reconcile`` / ``rebuild_all`` are mutually exclusive.
        """
        return self._lock

    # -- scheduling --------------------------------------------------------- #

    def watched_paths(self) -> list[str]:
        """Return the directory paths the Observer is (or would be) scheduled on.

        Each LIVE root is walked with ``exclude_dirs`` pruned at the ``os.walk``
        level, and EVERY surviving directory is returned as its own NON-recursive
        watch. This is the scheduling-level prune the perf + worktree rules
        require: a ``.venv``/``.git``/worktree-copy subtree is never even handed
        to inotify (a recursive watch on the root would descend into it and melt
        the watcher on a 43k-file worktree copy — exactly what we forbid). STATIC
        roots are frozen and are absent entirely.
        """
        paths: list[str] = []
        for root in self._live_roots:
            assert root.path is not None  # validated by RootConfig
            base = Path(root.path)
            if not base.is_dir():
                continue
            # ``walked_dirs`` prunes ``exclude_dirs`` at the os.walk level, so a
            # ``.venv``/worktree-copy subtree is never yielded — never scheduled.
            paths.extend(walked_dirs(self._config, base))
        return paths

    async def start(self) -> None:
        """Schedule the Observer on the live roots' included dirs and begin watching.

        Each surviving directory (excluded subtrees pruned at the walk level —
        see :meth:`watched_paths`) is scheduled as a NON-recursive watch on the
        observer thread; events for out-of-scope files are additionally dropped
        at event time (:meth:`_resolve`). A background worker task continuously
        drains debounced ops from the queue under the single lock, so an edit is
        re-indexed autonomously. The deterministic :meth:`drain` seam remains for
        tests / explicit flushes.
        """
        observer = Observer()
        handler = _WatchdogHandler(self)
        watched = self.watched_paths()
        for path in watched:
            observer.schedule(handler, path, recursive=False)
        observer.start()
        self._observer = observer
        self._worker = self._loop.create_task(self._worker_loop())
        logger.info(
            "watcher.start",
            extra={"watched_dir_count": len(watched), "live_tiers": len(self._live_roots)},
        )

    async def stop(self) -> None:
        """Stop the Observer thread, the worker task, and any debounce timers."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        if self._worker is not None:
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass
            self._worker = None
        for timer in self._timers.values():
            timer.cancel()
        self._timers.clear()
        logger.info("watcher.stop")

    async def _worker_loop(self) -> None:
        """Continuously consume queued ops, each under the single lock.

        Blocks on the queue, then processes one op while holding the lock — so a
        live event and the periodic sweep are mutually exclusive. Re-acquiring the
        lock per op (rather than holding it across the ``get``) lets the sweep
        interleave between ops instead of being starved by a busy queue.
        """
        while True:
            key = await self._queue.get()
            try:
                async with self._lock:
                    op = self._pending.pop(key, None)
                    if op is not None:
                        await self._apply(key, op)
            finally:
                self._queue.task_done()

    # -- handler seams (called from the observer thread) -------------------- #

    def on_modified_path(self, abs_path: str) -> None:
        """Enqueue a reindex for an absolute path (create/modify seam).

        Thread-safe: marshals onto the loop via ``call_soon_threadsafe`` so the
        observer thread never touches asyncio state. A path outside every live
        root, or inside an excluded subtree / not matching the include globs, is
        dropped (resolves to ``None``).
        """
        resolved = self._resolve(abs_path)
        if resolved is None:
            return
        self._loop.call_soon_threadsafe(self._coalesce, resolved, _OP_INDEX, None)

    def on_deleted_path(self, abs_path: str) -> None:
        """Enqueue a purge for an absolute path (delete seam)."""
        resolved = self._resolve(abs_path)
        if resolved is None:
            return
        self._loop.call_soon_threadsafe(self._coalesce, resolved, _OP_PURGE, None)

    def on_moved_path(self, *, src_abs: str, dest_abs: str) -> None:
        """Enqueue an atomic-save move: purge the source, reindex the destination.

        Either endpoint may lie outside the watched/included set (a move into or
        out of an excluded subtree), so each is resolved and enqueued
        independently — an unresolved endpoint is simply skipped.
        """
        src = self._resolve(src_abs)
        if src is not None:
            self._loop.call_soon_threadsafe(self._coalesce, src, _OP_PURGE, None)
        dest = self._resolve(dest_abs)
        if dest is not None:
            self._loop.call_soon_threadsafe(self._coalesce, dest, _OP_INDEX, dest_abs)

    # -- coalesce + debounce (loop thread) ---------------------------------- #

    def _coalesce(
        self, key: tuple[str, str], op: str, abs_path: str | None
    ) -> None:
        """Record/replace the pending op for ``key`` and (re)arm its debounce timer.

        Runs on the loop thread. A fresh event for an already-pending key resets
        the debounce window (so a save storm flushes once, after the path goes
        quiet) and updates the op — a delete after a modify within the window
        wins as a purge, a modify after a delete wins as an index — last event
        reflects the file's final state.
        """
        tier, file_path = key
        logger.debug(
            "watcher.event.received", extra={"tier": tier, "file_path": file_path, "op": op}
        )
        self._pending[key] = _PendingOp(op=op, abs_path=abs_path)
        existing = self._timers.pop(key, None)
        if existing is not None:
            existing.cancel()
        self._timers[key] = self._loop.call_later(
            self._debounce_s, self._flush_key, key
        )

    def _flush_key(self, key: tuple[str, str]) -> None:
        """Debounce timer fired: move ``key``'s pending op onto the work queue.

        Runs on the loop thread. If the queue is full (a huge churn outpacing the
        worker), the event is dropped from the queue path rather than blocking the
        loop. Recovery does NOT come from the still-pending coalescing entry (the
        periodic reconcile does not consume ``_pending`` — it RE-WALKS the
        filesystem and diffs against the manifest, so it re-discovers the change
        independently); the dropped event is simply caught by that next sweep —
        the documented ``IN_Q_OVERFLOW`` backstop.
        """
        self._timers.pop(key, None)
        if key not in self._pending:
            return
        tier, file_path = key
        logger.debug(
            "watcher.debounce.flush",
            extra={"tier": tier, "file_path": file_path, "queue_depth": self._queue.qsize()},
        )
        try:
            self._queue.put_nowait(key)
        except asyncio.QueueFull:
            # Dropped from the queue path; the next periodic reconcile RE-WALKS the
            # filesystem and re-discovers this change (it does not read _pending).
            logger.warning(
                "watcher.in_q_overflow", extra={"tier": tier, "file_path": file_path}
            )
            return

    # -- drain worker (loop thread, under the single lock) ------------------ #

    async def drain(self) -> None:
        """Process every currently-pending and queued event to completion.

        Flushes any debounce timers still pending (so a test need not sleep out
        the window), then drains the queue, running each op under the single
        :class:`asyncio.Lock`. The lock is acquired ONCE around the whole drain so
        the worker holds the single-writer role for the batch — and so a
        concurrent :meth:`run_sweep` is forced to wait rather than interleave its
        own ``index_file`` calls.
        """
        # Let any ``call_soon_threadsafe``-scheduled ``_coalesce`` callbacks (from
        # the observer thread OR a direct seam call) run first, so their pending
        # ops + debounce timers exist before we flush them.
        await asyncio.sleep(0)
        self._flush_all_timers()
        async with self._lock:
            while not self._queue.empty():
                key = self._queue.get_nowait()
                op = self._pending.pop(key, None)
                if op is None:
                    continue
                await self._apply(key, op)

    def _flush_all_timers(self) -> None:
        """Cancel every armed debounce timer and queue its pending op now.

        Lets :meth:`drain` process a just-fired burst deterministically without
        waiting out the debounce window. Each still-pending key is pushed onto
        the queue exactly as its timer would have.
        """
        for key, timer in list(self._timers.items()):
            timer.cancel()
            self._timers.pop(key, None)
            if key in self._pending:
                try:
                    self._queue.put_nowait(key)
                except asyncio.QueueFull:
                    # Same drop semantics as ``_flush_key``: the next periodic
                    # reconcile re-walks the filesystem and re-discovers this
                    # change. Log the SAME ``watcher.in_q_overflow`` event so a
                    # burst-flush overflow is observable in Mezmo, not silent.
                    tier, file_path = key
                    logger.warning(
                        "watcher.in_q_overflow",
                        extra={"tier": tier, "file_path": file_path},
                    )
                    return

    async def _apply(self, key: tuple[str, str], op: _PendingOp) -> None:
        """Run one pending op (index or purge) for ``key``.

        Called only while the single lock is held. An index reads the current
        on-disk content and runs the full per-file pipeline; a purge removes the
        file's points and manifest row. A vanished file mid-index (raced with a
        delete) degrades to a purge rather than crashing.
        """
        tier, rel_path = key
        if op.op == _OP_PURGE:
            await self._purge(tier, rel_path)
            return
        # _OP_INDEX: read the live file and reindex it.
        abs_path = op.abs_path or self._abs_for(tier, rel_path)
        if abs_path is None or not Path(abs_path).is_file():
            # The file disappeared between the event and the drain — purge instead
            # of indexing a path that no longer exists.
            logger.info(
                "watcher.index.degraded_to_purge",
                extra={"tier": tier, "file_path": rel_path},
            )
            await self._purge(tier, rel_path)
            return
        source = Path(abs_path).read_text(encoding="utf-8")
        await self._indexer.index_file(tier, rel_path, source)

    async def _purge(self, tier: str, rel_path: str) -> None:
        """Purge a (tier, file) from Qdrant, the manifest, and the graph (tier-scoped)."""
        await self._store.delete_by_file(tier, rel_path)
        self._manifest.delete(tier, rel_path)
        # Keep the code-graph in lock-step: a deleted/moved-from file's symbols
        # must not linger in the graph (tier-scoped, so a sibling tier survives).
        if self._code_graph is not None:
            self._code_graph.delete_file_graph(tier, rel_path)

    # -- periodic sweep (under the SAME lock) ------------------------------- #

    async def run_sweep(self) -> ReconcileSummary:
        """Run the periodic reconcile sweep under the shared single-writer lock.

        Acquiring the SAME lock the drain uses is the whole concurrency contract:
        a live event being drained and this sweep can never both be inside
        ``index_file`` at once. The reconcile itself is the policy-aware
        :class:`~loremaster.index.reconcile.ReconcileEngine.reconcile`.

        Returns:
            The :class:`~loremaster.index.reconcile.ReconcileSummary` the sweep
            produced, so the startup path can log/report the initial sweep's
            counts without bypassing the lock.
        """
        async with self._lock:
            return await self._reconcile_engine.reconcile()

    # -- path resolution ---------------------------------------------------- #

    def _resolve(self, abs_path: str) -> tuple[str, str] | None:
        """Map an absolute event path to ``(tier, tier_relative_path)`` or ``None``.

        Returns ``None`` when the path is under no live root, inside an excluded
        directory, or does not match the root's include / passes an exclude glob —
        the event-time mirror of the indexer's walk-level prune, so the watcher
        and the reconcile sweep agree on exactly which files are in scope.
        """
        target = Path(abs_path)
        for root in self._live_roots:
            assert root.path is not None  # validated by RootConfig
            base = Path(root.path)
            try:
                rel = target.relative_to(base)
            except ValueError:
                continue
            rel_parts = rel.parts
            if any(part in set(self._config.exclude_dirs) for part in rel_parts[:-1]):
                return None  # inside a pruned subtree
            rel_posix = str(PurePosixPath(rel.as_posix()))
            # Shared scope predicate: watch scope == walk scope == reconcile scope.
            if not is_included(self._config, root, rel_posix):
                return None
            return (root.tier, rel_posix)
        return None

    def _abs_for(self, tier: str, rel_path: str) -> str | None:
        """Reconstruct the absolute path for a (tier, rel_path) under its live root."""
        for root in self._live_roots:
            if root.tier == tier and root.path is not None:
                return str(Path(root.path) / rel_path)
        return None


class _PendingOp:
    """One coalesced pending op for a (tier, file_path) key.

    Attributes:
        op: ``"index"`` or ``"purge"``.
        abs_path: The absolute source path for an index op when known (a move's
            destination carries it explicitly); ``None`` ⇒ reconstruct from the
            tier root.
    """

    __slots__ = ("op", "abs_path")

    def __init__(self, op: str, abs_path: str | None) -> None:
        self.op = op
        self.abs_path = abs_path
