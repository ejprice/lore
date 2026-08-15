"""The policy-aware reconcile engine — startup + periodic staleness sweep.

This is staleness angles (2) and (3) of Deliverable 3 (and AMENDMENT 1 D5): the
sweep that brings the SurrealDB index current with the filesystem on startup and
on a timer. The timer sweep is the backstop that catches inotify events the watcher
dropped (a ``git checkout`` burst → ``IN_Q_OVERFLOW``, or downtime while the
container was stopped). It is built entirely on the already-merged
:class:`~loremaster.index.indexer.Indexer` and
:class:`~loremaster.index.surreal_manifest.SurrealManifest`.

What reconcile owns on top of :meth:`Indexer.index_all`:

* **The same per-policy walk.** :meth:`Indexer.index_tier` already does the right
  thing per tier — a LIVE tier is walked with the manifest mtime+size fast-path
  (unchanged ``indexed`` file → zero embeds) and any non-``indexed`` file
  (``failed``/``dirty``/``embedding`` from a crash mid-embed) is re-attempted
  because :meth:`SurrealManifest.needs_reindex` returns ``True`` for it; a STATIC tier
  is freshness-gated on its version stamp (matching stamp → SKIP with zero walk
  and zero acquisition; changed/absent → acquire + rebuild + re-stamp). Reconcile
  does NOT re-implement any of that — it delegates, so the policy lives in one
  place.
* **Purge of deleted files (the part ``index_all`` cannot do).** A walk only
  visits files that still exist, so a file present in the manifest but GONE from
  disk is invisible to ``index_tier``. Reconcile closes that gap: for every LIVE
  tier it diffs the manifest's rows against the files the walk actually saw and
  purges the difference in ONE composed atomic transaction — the store chunk-delete
  + ``file_text`` delete + manifest-row delete (+ the graph slice), tier-scoped so a
  sibling tier's copy of the same path survives. STATIC tiers are excluded from the
  purge pass:
  a matching-stamp static tier is intentionally not walked, so "the walk didn't
  see it" carries no information about deletion there — a static tier's contents
  change only through a version-stamp rebuild, which already purges via
  ``delete_by_tier``.

:meth:`reconcile` returns a :class:`ReconcileSummary` — the indexer's
:class:`~loremaster.index.indexer.IndexSummary` plus the count of purged files —
the freshness surface the server's ``index_status`` and the deploy healthcheck
read.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any

# Seam-12 (ingest): a RUNTIME module import so ``_purge_file`` reaches
# ``claiming_extension`` through the LIVE module — a test monkeypatching
# ``loremaster.extension.claiming_extension`` binds here too (CF8, ONE
# IMPLEMENTATION prove-by-mutation).
import loremaster.extension as extension_module
from loremaster.config import WATCH_LIVE
from loremaster.index.indexer import META_LAST_SWEEP_AT_KEY, IndexSummary
from loremaster.index.paths import is_included, walked_dirs

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from loremaster.config import LoreConfig, RootConfig
    from loremaster.extension import Extension
    from loremaster.index.indexer import Indexer, IndexOutcome


class ReconcileSummary(IndexSummary):
    """An :class:`IndexSummary` extended with the count of purged files.

    Attributes:
        files_purged: Files present in the manifest but gone from disk that this
            sweep purged from the store and the manifest (a live-tier-only count;
            static tiers are not diffed for deletions).
    """

    files_purged: int


class ReconcileEngine:
    """Bring the index current with the filesystem, one root at a time.

    Dependency-injected so the server wires the real collaborators and tests pass
    a :class:`FakeEmbedder`-backed indexer, the fast in-memory async fakes
    mirroring the Surreal store/manifest (:mod:`_surreal_fakes`), and a real
    ``tmp_path`` corpus.

    Args:
        indexer: The :class:`~loremaster.index.indexer.Indexer` that owns the
            per-tier walk + per-file pipeline. Reconcile delegates all indexing
            to it and only adds the deletion-purge pass.
        manifest: The async :class:`~loremaster.index.surreal_manifest.SurrealManifest`
            — the authority diffed against the disk to find deletions.
        store: The async :class:`~loremaster.store.surreal.SurrealStore` whose
            composed ``apply`` purges a deleted file's every surface atomically.
        config: The validated :class:`~loremaster.config.LoreConfig`; its roots
            drive the sweep.
        snapshot_stamper: Optional :class:`~loremaster.index.snapshots.
            SnapshotStamper` (the capability layer, mirrors ``code_graph``).
            When wired, :meth:`reconcile` stamps a new snapshot on a
            FULLY-successful, genuinely-productive sweep; absent, reconcile
            behaves exactly as before (backward compatible).
    """

    def __init__(
        self,
        *,
        indexer: Indexer,
        manifest: Any,
        store: Any,
        config: LoreConfig,
        code_graph: Any = None,
        snapshot_stamper: Any = None,
        extensions: Sequence[Extension] = (),
    ) -> None:
        self._indexer = indexer
        self._manifest = manifest
        self._store = store
        self._config = config
        # Optional code-graph: when present, the deletion sweep also purges a
        # vanished file's graph slice (kept as fresh as the vector index). The
        # per-file re-index path already refreshes the graph through the indexer.
        self._code_graph = code_graph
        # Seam-12 (CF7/DG1): the registered extensions, so ``_purge_file`` can
        # compose a claimed file's ``entity_purge_fragment`` alongside the graph
        # purge (the code_graph precedent). STUB (packet 47a contract): accepted
        # + stored (default ``()``); the purge wiring is BUILDER logic → P14 RED.
        self._extensions: tuple[Extension, ...] = tuple(extensions)
        # Optional snapshot stamper (P5-C4, mirrors ``code_graph``). When
        # present, a fully-successful, genuinely productive sweep stamps a new
        # ``snapshot`` generation marker; absent, reconcile behaves exactly as
        # before (backward compatible).
        self._snapshot_stamper = snapshot_stamper

    async def reconcile(self, *, purge_traces: bool = False) -> ReconcileSummary:
        """Walk every root per its policy, purge deletions, return a summary.

        ``purge_traces`` (packet 06b contract stub, DD-1.c / E1=Reading Y): the
        gate that keeps the trace-retention GC OFF the awaited initial startup
        sweep and ON the periodic reconcile tick. The PERIODIC caller passes
        ``True``; every other caller (the initial startup sweep, the
        ``IN_Q_OVERFLOW`` recovery, a forced ``lore_index(reconcile=True)``, a
        ``reconcile`` command) leaves it default so a first-activation purge over
        months of rows can never block boot. The BUILDER adds the gated purge
        body (pinned RED by ``test_reconcile.py::TestReconcilePurgesTraceRetention``);
        the parameter lands here only so the contract type-checks (mypy zero-new).

        For each configured root: delegate to :meth:`Indexer.index_tier` (live →
        walk + fast-path + resume non-indexed; static → version-stamp defer).
        Then, for every LIVE tier, purge the files the manifest still holds but
        that no longer exist on disk (the part the walk structurally cannot do).
        On a FULLY-successful, genuinely-productive sweep, stamps a new
        snapshot generation (see :meth:`_maybe_stamp_snapshot`) — mirrors
        :meth:`~loremaster.index.indexer.Indexer._maybe_stamp_snapshot`'s gate.

        Returns:
            The :class:`ReconcileSummary` rolling up every root's per-file
            outcomes and tier dispositions plus the purged-file count.
        """
        started_ns = time.monotonic_ns()
        all_outcomes: list[IndexOutcome] = []
        rebuilt: list[str] = []
        skipped_tiers: list[str] = []
        for root in self._config.effective_roots:
            summary = await self._indexer.index_tier(root)
            all_outcomes.extend(summary.outcomes)
            rebuilt.extend(summary.tiers_rebuilt)
            skipped_tiers.extend(summary.tiers_skipped)

        files_purged = await self._purge_deletions()

        result = ReconcileSummary(
            files_indexed=sum(1 for o in all_outcomes if o.state == "indexed"),
            files_failed=sum(1 for o in all_outcomes if o.state == "failed"),
            files_skipped=sum(1 for o in all_outcomes if o.state == "skipped"),
            tiers_rebuilt=rebuilt,
            tiers_skipped=skipped_tiers,
            outcomes=all_outcomes,
            files_purged=files_purged,
        )
        # The liveness heartbeat: always at INFO (on at the default level) so a
        # quiet sweep still proves reconcile ran. Counts only — never file content.
        logger.info(
            "reconcile.summary",
            extra={
                "files_indexed": result.files_indexed,
                "files_failed": result.files_failed,
                "files_skipped": result.files_skipped,
                "files_purged": result.files_purged,
                "tiers_rebuilt": result.tiers_rebuilt,
                "tiers_skipped": result.tiers_skipped,
                "duration_ms": (time.monotonic_ns() - started_ns) / 1_000_000,
            },
        )
        # Seam-12 phase 2 (CF5/DG3): re-resolve cross-file edges through the
        # indexer's ONE shared resolver — the SAME method index_all / rebuild_all
        # route through (ONE IMPLEMENTATION, prove-by-mutation). Gated on a
        # PRODUCTIVE sweep (a file was actually indexed) so a no-op reconcile tick
        # does NOT re-resolve every edge each interval (CF5c / cost, not correctness).
        await self._indexer._resolve_all_extension_edges(
            productive=result.files_indexed > 0
        )
        await self._maybe_stamp_snapshot(result)
        # P8d Wave 3: stamp the sweep-liveness fact UNCONDITIONALLY — "did the
        # sweep mechanism last run", not "did it change anything" or "did it
        # fully succeed" (those are separate facts the render can already read
        # off files_failed/files_indexed/files_purged). Mirrors index_file's
        # META_LAST_SYNC_AT_KEY stamp on the per-file live-apply side.
        await self._manifest.meta_set(META_LAST_SWEEP_AT_KEY, datetime.now(UTC).isoformat())
        # Trace-retention GC (packet 06b, DD-1.c / #193), GATED to the PERIODIC
        # tick only (E1=Reading Y): the awaited initial startup sweep leaves
        # ``purge_traces`` default False so a first-activation purge over months of
        # rows can never block boot. The batched drain rides the store's ONE _txn
        # retry driver; the cutoff derives from config retention (a CHECKED
        # variable, not a hidden 90 — pinned in TestReconcilePurgesTraceRetention).
        if purge_traces:
            trace_cutoff = datetime.now(UTC) - timedelta(
                days=self._config.telemetry.trace_retention_days
            )
            await self._store.purge_traces_before(cutoff=trace_cutoff)
        return result

    async def _maybe_stamp_snapshot(self, summary: ReconcileSummary) -> None:
        """Stamp a new snapshot generation iff this sweep fully succeeded AND
        changed something — by indexing OR by purging (P5-C4, ledger #25; gate
        widened by the C4 audit's bug #1).

        A DELETION is a generation change too: a purge-only sweep (zero files
        indexed, zero failed, but a file genuinely vanished from disk) must
        still stamp — otherwise the newest snapshot keeps listing a file that
        no longer exists on disk. This is why the gate here is WIDER than
        :meth:`~loremaster.index.indexer.Indexer._maybe_stamp_snapshot`'s:
        ``IndexSummary`` (the walk-only result that method reads) has no
        ``files_purged`` equivalent to widen with — only reconcile's own
        deletion pass produces one. Both methods agree on the other half of
        the gate: a sweep containing even one failed file stamps NOTHING,
        regardless of how much else it indexed or purged. A no-op
        :attr:`_snapshot_stamper` (the default) makes this a silent no-op.

        ``stamp()`` itself is BEST-EFFORT from this caller's perspective (P5-C4
        audit hardening #3b): any exception it raises is caught, logged loudly
        (``snapshot.stamp_failed``), and never propagates — an advisory
        snapshot hiccup must never turn an otherwise-successful sweep into a
        reported failure.

        Args:
            summary: The just-completed sweep's :class:`ReconcileSummary`.
        """
        if self._snapshot_stamper is None:
            return
        if summary.files_failed != 0:
            return
        if summary.files_indexed <= 0 and summary.files_purged <= 0:
            return
        try:
            await self._snapshot_stamper.stamp()
        except Exception:
            # Advisory only: the sweep itself already fully succeeded (the
            # gate above already checked files_failed == 0) — a snapshot
            # hiccup must never be reported as a sweep failure.
            logger.warning(
                "snapshot.stamp_failed",
                exc_info=True,
                extra={
                    "files_indexed": summary.files_indexed,
                    "files_purged": summary.files_purged,
                },
            )

    async def _purge_deletions(self) -> int:
        """Purge live-tier manifest rows whose file is gone from disk.

        Each deletion is a SINGLE composed atomic transaction (see
        :meth:`_purge_file`) spanning the store chunks + ``file_text`` body +
        manifest row (+ the graph slice), so a vanished file's surfaces are removed
        all-or-nothing — a reader never observes a file half-purged.

        Returns:
            The number of (tier, file) rows purged from the store and the manifest.
        """
        purged = 0
        for root in self._config.effective_roots:
            if root.watch != WATCH_LIVE:
                continue
            assert root.path is not None  # validated by RootConfig
            base = Path(root.path)
            on_disk = self._included_files_on_disk(root, base)
            for row in await self._manifest.files_for_tier(root.tier):
                if row.file_path not in on_disk:
                    logger.debug(
                        "reconcile.purge",
                        extra={"tier": root.tier, "file_path": row.file_path},
                    )
                    await self._purge_file(root.tier, row.file_path)
                    purged += 1
        return purged

    async def _purge_file(self, tier: str, file_path: str) -> None:
        """Purge one vanished file's surfaces in ONE composed atomic transaction.

        Composes the store chunk-delete + ``file_text`` delete + manifest-row delete
        (+ the tier-scoped code-graph slice purge when a graph is wired) into a single
        :meth:`SurrealStore.apply` — tier- and file-scoped, so a sibling tier's copy
        of the same path (C1) survives and a reader never sees the file half-removed.

        Args:
            tier: The tier the deleted file belonged to.
            file_path: The tier-relative path that vanished from disk.
        """
        fragments: list[Any] = [
            self._store.delete_file_fragment(tier, file_path),
            self._store.file_text_delete_fragment(tier, file_path),
            self._manifest.delete_fragment(tier, file_path),
        ]
        # Purge the deleted file's graph slice too (tier-scoped), so the graph never
        # outlives the source it was derived from.
        if self._code_graph is not None:
            fragments.append(self._code_graph.purge_file_fragment(tier, file_path))
        # Seam-12 (CF7): a claimed file's entity NODES purge in the SAME apply (its
        # edges cascade — store §2/§4). The claiming extension is reached via THIS
        # engine's OWN ``extensions=`` param (the code_graph precedent), through the
        # shared ``claiming_extension`` helper (CF8 / ONE IMPLEMENTATION).
        claimant = extension_module.claiming_extension(self._extensions, tier, file_path)
        if claimant is not None:
            entity_purge = claimant.entity_purge_fragment(tier, file_path)
            if entity_purge is not None:
                fragments.append(entity_purge)
        await self._store.apply(fragments)

    def _included_files_on_disk(self, root: RootConfig, base: Path) -> set[str]:
        """Return the tier-relative included paths that currently exist under ``base``.

        Walks ``base`` exactly as the indexer's walk does — via the shared
        :func:`~loremaster.index.paths.walked_dirs` (``exclude_dirs`` pruned at
        the ``os.walk`` level so a pruned subtree is never descended) and the
        shared :func:`~loremaster.index.paths.is_included` glob test — so the set
        is precisely the paths the walk would have visited. Any manifest row NOT
        in this set is a deletion (or a now-excluded file) to purge.
        """
        present: set[str] = set()
        for dirpath in walked_dirs(self._config, base):
            for entry in Path(dirpath).iterdir():
                if not entry.is_file():
                    continue
                rel = str(PurePosixPath(entry.relative_to(base).as_posix()))
                if is_included(self._config, root, rel):
                    present.add(rel)
        return present
