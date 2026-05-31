"""The policy-aware reconcile engine — startup + periodic staleness sweep.

This is staleness angles (2) and (3) of Deliverable 3 (and AMENDMENT 1 D5): the
sweep that brings the Qdrant index current with the filesystem on startup and on
a timer. The timer sweep is the backstop that catches inotify events the watcher
dropped (a ``git checkout`` burst → ``IN_Q_OVERFLOW``, or downtime while the
container was stopped). It is built entirely on the already-merged
:class:`~loremaster.index.indexer.Indexer` and
:class:`~loremaster.index.manifest.Manifest`.

What reconcile owns on top of :meth:`Indexer.index_all`:

* **The same per-policy walk.** :meth:`Indexer.index_tier` already does the right
  thing per tier — a LIVE tier is walked with the manifest mtime+size fast-path
  (unchanged ``indexed`` file → zero embeds) and any non-``indexed`` file
  (``failed``/``dirty``/``embedding`` from a crash mid-embed) is re-attempted
  because :meth:`Manifest.needs_reindex` returns ``True`` for it; a STATIC tier
  is freshness-gated on its version stamp (matching stamp → SKIP with zero walk
  and zero acquisition; changed/absent → acquire + rebuild + re-stamp). Reconcile
  does NOT re-implement any of that — it delegates, so the policy lives in one
  place.
* **Purge of deleted files (the part ``index_all`` cannot do).** A walk only
  visits files that still exist, so a file present in the manifest but GONE from
  disk is invisible to ``index_tier``. Reconcile closes that gap: for every LIVE
  tier it diffs the manifest's rows against the files the walk actually saw and
  purges the difference — ``store.delete_by_file(tier, path)`` (tier-scoped, so a
  sibling tier's copy of the same path survives) followed by
  ``manifest.delete(tier, path)``. STATIC tiers are excluded from the purge pass:
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
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from loremaster.config import WATCH_LIVE
from loremaster.index.indexer import IndexSummary
from loremaster.index.paths import is_included, walked_dirs

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from loremaster.config import LoreConfig, RootConfig
    from loremaster.graph import CodeGraph
    from loremaster.index.indexer import Indexer, IndexOutcome
    from loremaster.index.manifest import Manifest
    from loremaster.store.qdrant import QdrantStore


class ReconcileSummary(IndexSummary):
    """An :class:`IndexSummary` extended with the count of purged files.

    Attributes:
        files_purged: Files present in the manifest but gone from disk that this
            sweep purged from Qdrant and the manifest (a live-tier-only count;
            static tiers are not diffed for deletions).
    """

    files_purged: int


class ReconcileEngine:
    """Bring the index current with the filesystem, one root at a time.

    Dependency-injected so the server wires the real collaborators and tests pass
    a :class:`FakeEmbedder`-backed indexer, a temp-file manifest, a throwaway
    Qdrant collection, and a real ``tmp_path`` corpus.

    Args:
        indexer: The :class:`~loremaster.index.indexer.Indexer` that owns the
            per-tier walk + per-file pipeline. Reconcile delegates all indexing
            to it and only adds the deletion-purge pass.
        manifest: The SQLite :class:`~loremaster.index.manifest.Manifest` — the
            authority diffed against the disk to find deletions.
        store: The :class:`~loremaster.store.qdrant.QdrantStore` whose
            ``delete_by_file`` purges a deleted file's points.
        config: The validated :class:`~loremaster.config.LoreConfig`; its roots
            drive the sweep.
    """

    def __init__(
        self,
        *,
        indexer: Indexer,
        manifest: Manifest,
        store: QdrantStore,
        config: LoreConfig,
        code_graph: CodeGraph | None = None,
    ) -> None:
        self._indexer = indexer
        self._manifest = manifest
        self._store = store
        self._config = config
        # Optional code-graph: when present, the deletion sweep also purges a
        # vanished file's graph slice (kept as fresh as the vector index). The
        # per-file re-index path already refreshes the graph through the indexer.
        self._code_graph = code_graph

    async def reconcile(self) -> ReconcileSummary:
        """Walk every root per its policy, purge deletions, return a summary.

        For each configured root: delegate to :meth:`Indexer.index_tier` (live →
        walk + fast-path + resume non-indexed; static → version-stamp defer).
        Then, for every LIVE tier, purge the files the manifest still holds but
        that no longer exist on disk (the part the walk structurally cannot do).

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
        return result

    async def _purge_deletions(self) -> int:
        """Purge live-tier manifest rows whose file is gone from disk.

        Returns:
            The number of (tier, file) rows purged from Qdrant and the manifest.
        """
        purged = 0
        for root in self._config.effective_roots:
            if root.watch != WATCH_LIVE:
                continue
            assert root.path is not None  # validated by RootConfig
            base = Path(root.path)
            on_disk = self._included_files_on_disk(root, base)
            for row in self._manifest.files_for_tier(root.tier):
                if row.file_path not in on_disk:
                    logger.debug(
                        "reconcile.purge",
                        extra={"tier": root.tier, "file_path": row.file_path},
                    )
                    await self._store.delete_by_file(root.tier, row.file_path)
                    self._manifest.delete(root.tier, row.file_path)
                    # Purge the deleted file's graph slice too (tier-scoped), so the
                    # graph never outlives the source it was derived from.
                    if self._code_graph is not None:
                        self._code_graph.delete_file_graph(root.tier, row.file_path)
                    purged += 1
        return purged

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
