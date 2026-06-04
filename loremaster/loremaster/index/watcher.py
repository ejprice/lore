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
  the LIVE roots ONLY, with ONE RECURSIVE watch per root (so a root with N nested
  dirs costs ONE inotify *instance* — one ``inotify_init`` fd — not N, which is
  what would exhaust ``fs.inotify.max_user_instances`` on a wide tree). STATIC
  roots are frozen and are never scheduled. Excluded subtrees (``.venv`` /
  ``.git`` / worktree copies) are no longer pruned at SCHEDULE time — the
  recursive watch physically observes them — so the event-time :meth:`_resolve`
  drop is the single mechanism that keeps their edits out of the index.
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
  periodic reconcile sweep (:meth:`run_sweep`) AND the kernel-overflow handler
  (:meth:`on_kernel_overflow`) acquire the SAME lock — so a live event, a sweep,
  and an overflow-driven reconcile never run ``index_file`` concurrently, the
  single-writer guarantee the manifest relies on.

Atomic-save handling: editors save by writing a temp file then renaming it over
the target (``MOVED_TO``). :meth:`on_moved_path` reindexes the destination and
purges the source, so neither a stale source row nor a missing destination is
left behind.

Kernel-queue overflow: a wide simultaneous burst can overflow the kernel's own
inotify event queue, which the kernel surfaces as a sentinel event with
``wd == -1`` and ``mask & IN_Q_OVERFLOW``. watchdog 6.0.0 SILENTLY DROPS that
sentinel (``Inotify.read_events`` does ``if wd == -1: continue``), so it never
reaches a handler — meaning files whose events were lost would stay stale until
the next periodic sweep. :class:`_OverflowAwareInotify` scans the raw event
buffer ITSELF (no mutation of watchdog's process-global parser) and routes the
sentinel to :meth:`on_kernel_overflow`, which triggers an IMMEDIATE tier
reconcile (recovery in seconds, not only at the periodic interval). The wiring is
best-effort and degrades gracefully: any change in watchdog's internals can only
cost the immediate signal, never crash the watcher — the periodic reconcile
remains the ultimate backstop.

Every collaborator is injected (indexer, manifest, store, config, loop,
reconcile_engine) so the watcher is unit-testable without a server: tests drive
the handler seams (:meth:`on_modified_path`/:meth:`on_deleted_path`/
:meth:`on_moved_path`) directly and call :meth:`drain` for deterministic
processing, while one test drives the REAL Observer over a ``tmp_path`` (inotify
over a real temp dir works on this box).
"""

from __future__ import annotations

import asyncio
import contextlib
import errno
import logging
import os
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers.api import BaseObserver, ObservedWatch
from watchdog.observers.inotify import InotifyEmitter, InotifyObserver
from watchdog.observers.inotify_buffer import InotifyBuffer
from watchdog.observers.inotify_c import (
    DEFAULT_EVENT_BUFFER_SIZE,
    Inotify,
    InotifyConstants,
    InotifyEvent,
)

from loremaster.config import WATCH_LIVE, RootConfig
from loremaster.index.paths import is_included

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

# The kernel's inotify-queue-overflow sentinel is a synthetic event delivered with
# NO watch descriptor (``wd == -1``) and the ``IN_Q_OVERFLOW`` bit set when the
# kernel's own event queue overflowed and events were dropped. watchdog discards
# it on the ``wd == -1`` check; :class:`_OverflowAwareInotify` re-surfaces it.
_NO_WATCH_DESCRIPTOR = -1


class _OverflowAwareInotify(Inotify):
    """An :class:`Inotify` that re-surfaces the kernel ``IN_Q_OVERFLOW`` sentinel.

    watchdog 6.0.0 drops the kernel's overflow sentinel in
    :meth:`Inotify.read_events` (``if wd == -1: continue``), so a dropped-burst
    signal never reaches any handler. This subclass reads the raw event buffer
    itself, scans it for the ``wd == -1`` / ``IN_Q_OVERFLOW`` entry via the PURE
    :meth:`scan_buffer_for_overflow` detector (firing the injected ``on_overflow``
    callback on a hit), and then translates the normal events by calling the
    pristine static ``Inotify._parse_event_buffer`` DIRECTLY — never swapping or
    otherwise mutating watchdog's process-global parser (the W1/W2 defect a prior
    swap-based implementation introduced).

    Robustness: the whole read path is guarded so any change in watchdog's
    internals (a renamed field, a different buffer shape) can only cost the
    immediate overflow signal, never crash the observer thread. The periodic
    reconcile sweep remains the ultimate backstop, so a missed signal degrades to
    "recovered at the next interval" rather than "watcher dies".
    """

    def __init__(
        self,
        path: bytes,
        *,
        recursive: bool = False,
        event_mask: int | None = None,
        on_overflow: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(path, recursive=recursive, event_mask=event_mask)
        self._on_overflow = on_overflow

    def scan_buffer_for_overflow(self, event_buffer: bytes) -> bool:
        """Detect the kernel ``IN_Q_OVERFLOW`` sentinel in a raw event buffer.

        PURE detector — takes the raw bytes watchdog read off the inotify fd and
        parses them with the pristine static ``Inotify._parse_event_buffer``
        (called via the class, NOT swapped), looking for the kernel's overflow
        sentinel: a ``wd == -1`` entry with the ``IN_Q_OVERFLOW`` mask bit. On a
        hit it fires the injected overflow callback (which marshals an immediate
        tier reconcile onto the loop) and returns ``True``; otherwise it touches
        nothing and returns ``False``. It mutates NO global state, so it is safe
        to call from any number of concurrent buffer threads.

        Args:
            event_buffer: The raw ``inotify_event`` byte buffer read off the fd.

        Returns:
            ``True`` iff the kernel overflow sentinel was present (and the
            callback was fired); ``False`` otherwise.
        """
        for wd, mask, _cookie, _name in Inotify._parse_event_buffer(event_buffer):
            if wd == _NO_WATCH_DESCRIPTOR and (mask & InotifyConstants.IN_Q_OVERFLOW):
                if self._on_overflow is not None:
                    self._on_overflow()
                return True
        return False

    def read_events(
        self, *, event_buffer_size: int = DEFAULT_EVENT_BUFFER_SIZE
    ) -> list[InotifyEvent]:
        """Read events, surfacing a dropped kernel-overflow sentinel.

        Reads the raw buffer off the inotify fd ourselves (the parent reads it
        too, but discards the ``wd == -1`` overflow sentinel before any handler
        sees it), scans it for the overflow sentinel via the pure
        :meth:`scan_buffer_for_overflow` detector, then translates the normal
        events exactly as watchdog 6.0.0's own ``Inotify.read_events`` does —
        calling the pristine static ``Inotify._parse_event_buffer`` DIRECTLY (no
        swap, no global mutation). lore re-indexes on any event and the periodic
        reconcile backstops, so exact ``IN_MOVED`` cookie-pairing is not critical;
        normal create/modify/delete delivery is preserved.

        Guarded end-to-end: a watchdog-internals mismatch degrades to an empty
        batch (the periodic reconcile recovers), never crashes the observer
        thread.
        """
        try:
            event_buffer = self._read_raw_buffer(event_buffer_size=event_buffer_size)
            if event_buffer is None:
                return []
            # Surface the kernel overflow sentinel the parent would silently drop.
            self.scan_buffer_for_overflow(event_buffer)
            return self._translate_buffer(event_buffer)
        except OSError:
            # A bad fd / interrupted read is the parent's own contract (it returns
            # ``[]`` on EBADF); re-raise nothing that would kill the thread.
            raise
        except Exception:  # pragma: no cover - defensive: never kill the thread
            logger.debug("watcher.read_events.degraded", exc_info=True)
            return []

    def _read_raw_buffer(self, *, event_buffer_size: int) -> bytes | None:
        """Read one raw inotify event buffer off the fd (mirrors the parent).

        Returns the raw bytes, or ``None`` when the instance has been closed (the
        parent returns ``[]`` in that case). Mirrors watchdog 6.0.0's
        ``Inotify.read_events`` read loop, including the ``EINTR`` retry and the
        ``EBADF`` short-circuit on a closed fd.
        """
        event_buffer = b""
        while True:
            try:
                with self._lock:
                    if self._closed:
                        return None
                    self._is_reading = True
                if self._check_inotify_fd():
                    event_buffer = os.read(self._inotify_fd, event_buffer_size)
                with self._lock:
                    self._is_reading = False
                    # ``_closed`` may flip on another thread (``close()``) during
                    # the unlocked ``os.read`` above, so re-check under the lock —
                    # exactly as watchdog's own ``read_events`` does. mypy narrows
                    # ``_closed`` to False from the earlier guard and can't model
                    # the cross-thread mutation, hence the unreachable ignore.
                    if self._closed:
                        self._close_resources()  # type: ignore[unreachable]
                        return None
            except OSError as exc:
                if exc.errno == errno.EINTR:
                    continue
                if exc.errno == errno.EBADF:
                    return None
                raise
            break
        return event_buffer

    def _translate_buffer(self, event_buffer: bytes) -> list[InotifyEvent]:
        """Translate a raw event buffer into ``InotifyEvent`` objects.

        A faithful port of watchdog 6.0.0's ``Inotify.read_events`` post-parse
        loop: it skips the ``wd == -1`` sentinel (already surfaced by
        :meth:`scan_buffer_for_overflow`), maintains the move-from bookkeeping and
        the recursive watch-descriptor maps, cleans up ignored watches, and
        simulates events for newly-created subdirectories under a recursive watch.
        It calls the pristine static ``Inotify._parse_event_buffer`` DIRECTLY — no
        swap of watchdog's process-global parser.
        """
        with self._lock:
            event_list: list[InotifyEvent] = []
            for wd, mask, cookie, name in Inotify._parse_event_buffer(event_buffer):
                if wd == _NO_WATCH_DESCRIPTOR:
                    # The overflow sentinel (already surfaced above) and any other
                    # watch-less kernel event — exactly the parent's skip.
                    continue
                wd_path = self._path_for_wd[wd]
                # Avoid a trailing slash for a watch-self event (empty name).
                src_path = os.path.join(wd_path, name) if name else wd_path
                inotify_event = InotifyEvent(wd, mask, cookie, name, src_path)

                if inotify_event.is_moved_from:
                    self.remember_move_from_event(inotify_event)
                elif inotify_event.is_moved_to:
                    move_src_path = self.source_for_move(inotify_event)
                    if move_src_path in self._wd_for_path:
                        moved_wd = self._wd_for_path[move_src_path]
                        del self._wd_for_path[move_src_path]
                        self._wd_for_path[inotify_event.src_path] = moved_wd
                        self._path_for_wd[moved_wd] = inotify_event.src_path
                        if self.is_recursive:
                            for _path in self._wd_for_path.copy():
                                if _path.startswith(move_src_path + os.path.sep.encode()):
                                    moved_wd = self._wd_for_path.pop(_path)
                                    _move_to_path = _path.replace(
                                        move_src_path, inotify_event.src_path
                                    )
                                    self._wd_for_path[_move_to_path] = moved_wd
                                    self._path_for_wd[moved_wd] = _move_to_path
                    src_path = os.path.join(wd_path, name)
                    inotify_event = InotifyEvent(wd, mask, cookie, name, src_path)

                if inotify_event.is_ignored:
                    # Clean up book-keeping for deleted watches.
                    path = self._path_for_wd.pop(wd)
                    if self._wd_for_path[path] == wd:
                        del self._wd_for_path[path]

                event_list.append(inotify_event)

                if (
                    self.is_recursive
                    and inotify_event.is_directory
                    and inotify_event.is_create
                ):
                    # A new directory under a recursive watch needs its own watch
                    # plus simulated create events for anything already inside it.
                    try:
                        self._add_watch(inotify_event.src_path, self._event_mask)
                    except OSError:
                        continue
                    event_list.extend(self._simulate_sub_creates(inotify_event.src_path))

        return event_list

    def _simulate_sub_creates(self, src_path: bytes) -> list[InotifyEvent]:
        """Simulate create events for a newly-created recursive subtree.

        Mirrors watchdog's ``_recursive_simulate``: a freshly-created directory
        may already contain files/subdirs whose own kernel events were never
        delivered, so synthesise ``IN_CREATE`` events (and add watches for the
        subdirs) to keep the recursive watch complete.
        """
        events: list[InotifyEvent] = []
        for root, dirnames, filenames in os.walk(src_path):
            for dirname in dirnames:
                with contextlib.suppress(OSError):
                    full_path = os.path.join(root, dirname)
                    wd_dir = self._add_watch(full_path, self._event_mask)
                    events.append(
                        InotifyEvent(
                            wd_dir,
                            InotifyConstants.IN_CREATE | InotifyConstants.IN_ISDIR,
                            0,
                            dirname,
                            full_path,
                        )
                    )
            for filename in filenames:
                full_path = os.path.join(root, filename)
                wd_parent_dir = self._wd_for_path[os.path.dirname(full_path)]
                events.append(
                    InotifyEvent(
                        wd_parent_dir,
                        InotifyConstants.IN_CREATE,
                        0,
                        filename,
                        full_path,
                    )
                )
        return events


class _OverflowAwareInotifyBuffer(InotifyBuffer):
    """An :class:`InotifyBuffer` whose backing inotify surfaces kernel overflow.

    ``InotifyBuffer.__init__`` hard-codes ``Inotify(...)``; this subclass swaps in
    :class:`_OverflowAwareInotify` so the dropped ``IN_Q_OVERFLOW`` sentinel is
    re-surfaced and routed to the watcher's overflow handler.
    """

    def __init__(
        self,
        path: bytes,
        *,
        recursive: bool = False,
        event_mask: int | None = None,
        on_overflow: Callable[[], None] | None = None,
    ) -> None:
        # Mirror ``InotifyBuffer.__init__`` but build the overflow-aware Inotify.
        # ``BaseThread.__init__`` (the grandparent) sets up the thread machinery;
        # call it directly to skip the parent's hard-coded ``Inotify`` build, then
        # start the buffer thread exactly as the parent does.
        from watchdog.utils.delayed_queue import DelayedQueue

        super(InotifyBuffer, self).__init__()
        self._queue = DelayedQueue[
            "InotifyEvent | tuple[InotifyEvent, InotifyEvent]"
        ](self.delay)
        self._inotify = _OverflowAwareInotify(
            path,
            recursive=recursive,
            event_mask=event_mask,
            on_overflow=on_overflow,
        )
        self.start()


class _OverflowAwareInotifyEmitter(InotifyEmitter):
    """An :class:`InotifyEmitter` that builds an overflow-aware inotify buffer.

    ``InotifyEmitter.on_thread_start`` hard-codes ``InotifyBuffer(...)``; this
    override swaps in :class:`_OverflowAwareInotifyBuffer` and threads the
    overflow callback through to the kernel-sentinel detection. The callback is
    attached by :class:`_OverflowAwareObserver` at schedule time.
    """

    #: Set by the observer before the emitter thread starts; ``None`` ⇒ no hook.
    on_overflow: Callable[[], None] | None = None

    def on_thread_start(self) -> None:
        """Open the overflow-aware inotify buffer on the emitter thread."""
        path = os.fsencode(self.watch.path)
        event_mask = self.get_event_mask_from_filter()
        self._inotify = _OverflowAwareInotifyBuffer(
            path,
            recursive=self.watch.is_recursive,
            event_mask=event_mask,
            on_overflow=self.on_overflow,
        )


class _OverflowAwareObserver(InotifyObserver):
    """An :class:`InotifyObserver` whose emitters re-surface kernel overflow.

    Uses :class:`_OverflowAwareInotifyEmitter` so a kernel ``IN_Q_OVERFLOW``
    sentinel is routed to the injected ``on_overflow`` callback (which marshals
    :meth:`LiveWatcher.on_kernel_overflow` onto the asyncio loop) instead of
    being silently dropped.
    """

    def __init__(self, on_overflow: Callable[[], None] | None = None) -> None:
        # Bypass ``InotifyObserver.__init__`` (which fixes the emitter class) and
        # register our overflow-aware emitter class with the base observer.
        BaseObserver.__init__(self, _OverflowAwareInotifyEmitter)
        self._on_overflow = on_overflow

    def schedule(
        self,
        event_handler: FileSystemEventHandler,
        path: str,
        *,
        recursive: bool = False,
        event_filter: list[type[FileSystemEvent]] | None = None,
    ) -> ObservedWatch:
        """Schedule a watch, attaching the overflow callback to its emitter."""
        watch = super().schedule(
            event_handler, path, recursive=recursive, event_filter=event_filter
        )
        # Attach the overflow hook to the freshly-created emitter for this watch
        # so its inotify buffer surfaces the kernel sentinel.
        emitter = self._emitter_for_watch.get(watch)
        if isinstance(emitter, _OverflowAwareInotifyEmitter):
            emitter.on_overflow = self._on_overflow
        return watch


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
            run by :meth:`run_sweep` AND :meth:`on_kernel_overflow` under the SAME
            lock as live events.
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
        """Return the root paths the Observer is (or would be) scheduled on.

        Each LIVE root is scheduled as ONE RECURSIVE watch on its root path, so a
        root with N nested dirs costs ONE inotify *instance* (not N). The
        ``exclude_dirs`` subtrees (``.venv`` / ``.git`` / worktree copies) are no
        longer pruned here — the recursive watch physically observes them — so the
        event-time :meth:`_resolve` drop is what keeps their edits out of the
        index. STATIC roots are frozen and are absent entirely.
        """
        paths: list[str] = []
        for root in self._live_roots:
            assert root.path is not None  # validated by RootConfig
            base = Path(root.path)
            if not base.is_dir():
                continue
            # ONE recursive watch per live root (the scalability fix): the root
            # path itself, not every nested directory under it.
            paths.append(str(base))
        return paths

    def build_observer(self) -> BaseObserver:
        """Construct (but do NOT start) the Observer scheduled on the live roots.

        Schedules exactly ONE RECURSIVE watch per LIVE root, so the observer holds
        ONE inotify *instance* per root regardless of how many nested directories
        it contains (the per-dir strategy opened one instance per dir and exhausted
        ``fs.inotify.max_user_instances`` on a wide tree). Returns the observer
        WITHOUT calling ``start()`` — no inotify fd is opened until the caller
        starts it — so the emitter count (one per root) can be inspected with zero
        kernel resources consumed. PURE: it touches only the config-derived live
        roots, never the injected indexer / store / reconcile engine.
        """
        observer = self._make_observer()
        handler = _WatchdogHandler(self)
        for path in self.watched_paths():
            # One recursive watch per root: the single inotify instance covers
            # every nested subdir via cheap per-dir inotify *watches*.
            observer.schedule(handler, path, recursive=True)
        return observer

    def _make_observer(self) -> BaseObserver:
        """Build the overflow-aware Observer, wiring the kernel-overflow callback.

        The callback runs on the OBSERVER thread, so it marshals onto the asyncio
        loop. An overflow signal can affect any watched root, so every live tier
        is reconciled (the immediate recovery the periodic sweep would otherwise
        defer to its interval).
        """
        return _OverflowAwareObserver(on_overflow=self._schedule_overflow_reconcile)

    def _schedule_overflow_reconcile(self) -> None:
        """Marshal a kernel-overflow-driven reconcile onto the loop (thread-safe).

        Invoked on the OBSERVER thread by :class:`_OverflowAwareInotify`. Each live
        tier may have lost events in the kernel-queue overflow, so each is
        reconciled via the single-writer :meth:`on_kernel_overflow` handler.
        """
        for root in self._live_roots:
            # Marshal onto the loop, then spawn the reconcile task there — a
            # named per-tier launcher (not an inline lambda) keeps the closed-over
            # tier explicit and the task creation on the loop thread.
            self._loop.call_soon_threadsafe(self._launch_overflow_reconcile, root.tier)

    def _launch_overflow_reconcile(self, tier: str) -> None:
        """Spawn the single-writer overflow reconcile for ``tier`` on the loop.

        Runs on the loop thread (scheduled by :meth:`_schedule_overflow_reconcile`
        via ``call_soon_threadsafe``), so creating the task here is safe.
        """
        self._loop.create_task(self.on_kernel_overflow(tier))

    async def start(self) -> None:
        """Schedule the Observer on the live roots and begin watching.

        Each LIVE root is scheduled as ONE RECURSIVE watch (see
        :meth:`build_observer`); events for out-of-scope files (excluded subtrees,
        non-included globs) are dropped at event time (:meth:`_resolve`). A
        background worker task continuously drains debounced ops from the queue
        under the single lock, so an edit is re-indexed autonomously. The
        deterministic :meth:`drain` seam remains for tests / explicit flushes.
        """
        observer = self.build_observer()
        observer.start()
        self._observer = observer
        self._worker = self._loop.create_task(self._worker_loop())
        logger.info(
            "watcher.start",
            extra={
                # One recursive watch per live root ⇒ the scheduled-watch count IS
                # the live-root count; both reported for operational visibility.
                "watched_dir_count": len(self.watched_paths()),
                "live_tiers": len(self._live_roots),
            },
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

    async def on_kernel_overflow(self, tier: str) -> None:
        """Reconcile a tier IMMEDIATELY in response to a kernel inotify overflow.

        A wide simultaneous burst can overflow the kernel's own inotify event
        queue; the kernel signals ``IN_Q_OVERFLOW`` and DROPS the lost events, so
        the files they targeted would stay stale until the next periodic sweep.
        This handler runs an IMMEDIATE reconcile of the affected tier (recovery in
        seconds), re-walking the filesystem to re-discover every change the
        dropped burst would have carried.

        It acquires the SAME single-writer lock the drain and the periodic sweep
        use, so the overflow-driven reconcile can never race a concurrent
        ``index_file``. The ``tier`` identifies which live tier overflowed; the
        engine's ``reconcile`` re-diffs the tree against the manifest.

        Args:
            tier: The live tier whose kernel inotify queue overflowed.
        """
        logger.warning("watcher.kernel_overflow", extra={"tier": tier})
        async with self._lock:
            await self._reconcile_engine.reconcile()

    # -- path resolution ---------------------------------------------------- #

    def _resolve(self, abs_path: str) -> tuple[str, str] | None:
        """Map an absolute event path to ``(tier, tier_relative_path)`` or ``None``.

        Returns ``None`` when the path is under no live root, inside an excluded
        directory, or does not match the root's include / passes an exclude glob —
        the event-time mirror of the indexer's walk-level prune, so the watcher
        and the reconcile sweep agree on exactly which files are in scope. With
        the recursive-watch fix the observer now PHYSICALLY sees excluded subtrees
        (they are no longer pruned at schedule time), so this event-time drop is
        the single mechanism keeping their edits out of the index.
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
