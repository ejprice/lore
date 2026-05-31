"""The batch :class:`Indexer` — config → source → chunk → embed → records → store.

This is the integration centerpiece (plan AMENDMENT 1 / D5–D7). A standalone,
dependency-injected, OOP indexer that builds and refreshes a project's Qdrant
index, one tier at a time. It is consumed two ways:

* the deploy/CI **CLI** (:mod:`loremaster.index.cli`) wires the real
  :class:`~loremaster.store.qdrant.QdrantStore`, a real
  :class:`loresigil.base.Embedder` (via ``make_embedder``), the SQLite
  :class:`~loremaster.index.manifest.Manifest`, the composed
  :class:`~lorescribe.registry.ChunkerRegistry`, and the per-static-tier
  :class:`~loremaster.source.local_directory.LocalDirectorySourceProvider`s, then
  runs it;
* the future watcher reuses :meth:`Indexer.index_file` for one-file incremental
  updates.

The invariants this module owns (each pinned by ``tests/test_indexer.py``):

**Per-tier freshness (D5).** A STATIC tier compares ``config.version`` against
the tier's stamp in the manifest ``meta``. CHANGED/absent → ``acquire`` the
snapshot via the tier's provider, then rebuild (selectively, via
``delete_by_tier``) and re-stamp. MATCH → SKIP with **zero filesystem walk**. A
LIVE tier does a full walk + per-file index every run (the watcher handles
incremental later, out of scope here).

**Per-file pipeline (`index_file`).** Honour the manifest mtime+size fast-path
(unchanged ``indexed`` file → skip, zero embeds). Otherwise chunk via
``registry.dispatch_file`` with a real :class:`~lorescribe.models.ChunkContext`
(the embedder's token counter + ``max_input_tokens`` injected); embed the chunk
texts; build records via ``chunk_to_record(..., tier=tier)``; **upsert the NEW
points BEFORE purging the stale ones** for that ``(tier, file)`` (dedupe by
deterministic point-id) so a concurrent reader never sees a gap; commit the
manifest row transactionally (``state='indexed'``).

**Resilience.** A permanently-failed embed (a ``None`` vector) OR a non-finite
vector (an ``isfinite`` guard — one NaN poisons cosine/argmax across every
query) marks the file ``failed``, stores **no** vectors for it, and lets the
other files continue; the failure is surfaced in the returned
:class:`IndexSummary`.

**Selective rebuild.** Rebuilding one tier uses ``delete_by_tier`` so sibling
tiers are untouched (the C1 primitive).
"""

from __future__ import annotations

import logging
import math
import os
import time
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

import httpx
from lorescribe.models import Chunk, ChunkContext
from pydantic import BaseModel, ConfigDict
from qdrant_client.common.client_exceptions import ResourceExhaustedResponse
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from loremaster.config import WATCH_LIVE, WATCH_STATIC, LoreConfig, RootConfig
from loremaster.index.manifest import (
    STATE_FAILED,
    STATE_INDEXED,
    FileRow,
    Manifest,
)
from loremaster.index.paths import is_included, walked_dirs
from loremaster.index.records import chunk_to_record, sha512_hex
from loremaster.source.snapshot import SnapshotLayout

if TYPE_CHECKING:
    from collections.abc import Sequence

    from lorescribe.registry import ChunkerRegistry
    from loresigil.base import Embedder

    from loremaster.extension import SourceProvider
    from loremaster.graph import CodeGraph
    from loremaster.store.qdrant import QdrantStore

# The Python source suffix whose files contribute to the code-graph. Non-Python
# files are NOT given a graph slice (the graph is a Python AST structure only),
# so a markdown/sql/xml file never synthesises a spurious module node.
_PYTHON_SUFFIX = ".py"

# Per-file lifecycle outcomes the indexer reports. ``skipped`` is the fast-path
# (unchanged file, zero embeds) — distinct from ``indexed`` (freshly embedded)
# and ``failed`` (embedder/finite-guard rejection).
STATE_SKIPPED = "skipped"

# The manifest ``meta`` key prefix that stamps a static tier's built version.
_TIER_VERSION_META_PREFIX = "tier_version:"


logger = logging.getLogger(__name__)

# The reason string attached to an ``index.file.failed`` event. Kept generic (no
# source text or vector data) — a permanently-failed/non-finite embed is the only
# failure path here, so naming it is enough for an operator to triage.
_FAILED_EMBED_REASON = "embed_failed_or_non_finite"

# The reason attached to ``index.file.failed`` when the Qdrant STORE op (upsert /
# stale-purge) failed past the store's own transient-retry budget for THIS file.
# This is the cold-index crash class: a persistent 500 must isolate the one file,
# not propagate and kill the whole batch index.
_FAILED_STORE_REASON = "store_op_failed_after_retries"

# Store-side failures the per-file pipeline ISOLATES (mark the file failed and
# continue) when they persist past :class:`QdrantStore`'s own retry budget. These
# mirror the store's transient classification (a transient that never cleared) plus
# a permanent 4xx — either way, ONE file's store error must not crash the index.
# Narrowly scoped to Qdrant/transport errors so a genuine programming bug (a
# ``TypeError`` etc.) still surfaces loudly rather than being silently swallowed.
# ``ResourceExhaustedResponse`` (a ``QdrantException``, NOT an
# ``UnexpectedResponse``) is the 429+``Retry-After`` overload class — a persistent
# overload of ONE file must isolate it, exactly like a persistent 500.
_STORE_FAILURE_ERRORS: tuple[type[BaseException], ...] = (
    UnexpectedResponse,
    ResourceExhaustedResponse,
    ResponseHandlingException,
    httpx.HTTPError,
)


def _tier_version_meta_key(tier: str) -> str:
    """The manifest ``meta`` key holding ``tier``'s built version stamp."""
    return f"{_TIER_VERSION_META_PREFIX}{tier}"


class IndexOutcome(BaseModel):
    """The result of indexing a single file.

    Attributes:
        tier: The tier the file belongs to.
        file_path: The tier-relative file path.
        state: ``indexed`` (freshly embedded), ``skipped`` (fast-path,
            unchanged), or ``failed`` (an embed/finite-guard rejection).
        n_chunks: The number of chunks the file produced (0 for an unclaimed
            extension).
    """

    model_config = ConfigDict(extra="forbid")

    tier: str
    file_path: str
    state: str
    n_chunks: int


class IndexSummary(BaseModel):
    """A roll-up of an indexing run (also the ``index_status`` shape).

    Attributes:
        files_indexed: Files freshly embedded and committed ``indexed``.
        files_failed: Files marked ``failed`` (embed/finite-guard rejection).
        files_skipped: Files the fast-path skipped (unchanged, zero embeds).
        tiers_rebuilt: Static tiers whose version changed and were rebuilt, plus
            every live tier walked this run.
        tiers_skipped: Static tiers whose version matched the manifest stamp and
            were skipped with zero walk.
        outcomes: The per-file outcomes (empty for ``index_status``, which is a
            manifest roll-up).
    """

    model_config = ConfigDict(extra="forbid")

    files_indexed: int
    files_failed: int
    files_skipped: int
    tiers_rebuilt: list[str]
    tiers_skipped: list[str]
    outcomes: list[IndexOutcome]


class Indexer:
    """Build/refresh a project's Qdrant index, tier by tier (dependency-injected).

    Every collaborator is injected so tests pass a :class:`FakeEmbedder`, a real
    Qdrant client (throwaway collection), a temp-file manifest, and real files,
    while the CLI wires the real deployment resources.

    Args:
        store: The :class:`~loremaster.store.qdrant.QdrantStore`.
        embedder: The active :class:`loresigil.base.Embedder`.
        manifest: The SQLite :class:`~loremaster.index.manifest.Manifest`.
        registry: The composed :class:`~lorescribe.registry.ChunkerRegistry`.
        source_providers: The :class:`SourceProvider`s, one per static tier
            (matched to a tier by the provider's ``tier`` attribute).
        config: The validated :class:`~loremaster.config.LoreConfig`.
        snapshot_root: The on-disk root static tiers are materialised under and
            served from (bind-mounted ``:ro`` at ``/source`` in the live server).
    """

    def __init__(
        self,
        *,
        store: QdrantStore,
        embedder: Embedder,
        manifest: Manifest,
        registry: ChunkerRegistry,
        source_providers: Sequence[SourceProvider],
        config: LoreConfig,
        snapshot_root: Path,
        code_graph: CodeGraph | None = None,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._manifest = manifest
        self._registry = registry
        self._providers_by_tier: dict[str, SourceProvider] = {
            provider.tier: provider for provider in source_providers
        }
        self._config = config
        self._snapshot_layout = SnapshotLayout(snapshot_root)
        # Optional code-graph (the capability layer). When present, a successful
        # per-file index rebuilds that file's Python graph slice; absent, the
        # indexer behaves exactly as before (backward compatible).
        self._code_graph = code_graph

    # -- token-counter adapter ---------------------------------------------

    def _chunk_context(self, file_path: str) -> ChunkContext:
        """Build a :class:`ChunkContext` with the embedder's token counter injected.

        The embedder counts a *batch* (``list[str] -> list[int]``) but a
        ``ChunkContext`` wants a single-string counter (``str -> int``), so the
        batch counter is adapted to one element. The embedder's
        ``max_input_tokens`` is the hard cap chunkers gate against.
        """
        embedder = self._embedder

        def count_one(text: str) -> int:
            return embedder.count_tokens([text])[0]

        return ChunkContext(
            slug=self._config.project.slug,
            file_path=file_path,
            count_tokens=count_one,
            max_input_tokens=embedder.max_input_tokens,
        )

    def chunk_texts(self, tier: str, path: str, source: str) -> list[str]:
        """Return the embed texts a file produces (the chunker's output, no embed).

        A read-only helper (used by tests and the future watcher) that runs only
        the chunking half of the pipeline. ``tier`` is accepted for signature
        symmetry with :meth:`index_file`; chunking itself is tier-agnostic.

        Args:
            tier: The tier the file belongs to (unused by chunking; kept for
                signature parity).
            path: The tier-relative file path selecting the chunker.
            source: The file's full text.

        Returns:
            The ``embedding_text`` of each produced chunk, in order.
        """
        chunks = self._chunk(path, source)
        return [chunk.embedding_text for chunk in chunks]

    def _chunk(self, path: str, source: str) -> list[Chunk]:
        """Dispatch ``source`` through the registry with a real ``ChunkContext``."""
        return self._registry.dispatch_file(path, source, self._chunk_context(path))

    # -- per-file pipeline --------------------------------------------------

    async def index_file(self, tier: str, path: str, source: str) -> IndexOutcome:
        """Index one file: chunk → embed → records → upsert-new-before-purge → commit.

        Honours the manifest mtime+size fast-path is the *caller's* job for an
        on-disk walk; here ``source`` is supplied directly, so freshness is keyed
        on the content hash: an ``indexed`` row whose ``sha512`` already matches
        this source is skipped with zero embeds. (The walk in :meth:`index_tier`
        applies the cheaper mtime+size fast-path *before* reading the file, so an
        unchanged file is never even read.)

        Args:
            tier: The tier the file belongs to.
            path: The tier-relative file path.
            source: The file's full text.

        Returns:
            The :class:`IndexOutcome` (``indexed`` / ``skipped`` / ``failed``).
        """
        content_hash = sha512_hex(source)
        existing = self._manifest.get(tier, path)
        if (
            existing is not None
            and existing.state == STATE_INDEXED
            and existing.sha512 == content_hash
        ):
            return IndexOutcome(
                tier=tier, file_path=path, state=STATE_SKIPPED, n_chunks=existing.n_chunks
            )

        chunks = self._chunk(path, source)
        return await self._index_chunks(
            tier=tier, path=path, content_hash=content_hash,
            chunks=chunks, mtime_ns=0, size=len(source.encode("utf-8")),
        )

    async def _index_chunks(
        self,
        *,
        tier: str,
        path: str,
        content_hash: str,
        chunks: list[Chunk],
        mtime_ns: int,
        size: int,
    ) -> IndexOutcome:
        """Embed ``chunks``, upsert-new-before-purge, and commit the manifest row.

        An unclaimed file (no chunks) is committed as a zero-chunk ``indexed``
        row (so a directory walk never re-reads it) with no embed. Otherwise the
        chunk texts are embedded; if ANY vector is missing (``None`` —
        permanent failure) or non-finite (the ``isfinite`` guard), the whole
        file is marked ``failed`` and NO vectors are stored — never a partial or
        poisoned set. On success the new points are upserted, THEN the stale
        point ids (the prior row's ids no longer produced) are purged, then the
        manifest row is replaced transactionally as ``indexed``.
        """
        started_ns = time.monotonic_ns()
        records = [
            chunk_to_record(
                chunk,
                slug=self._config.project.slug,
                tier=tier,
                file_path=path,
                content_hash=content_hash,
                mtime_ns=mtime_ns,
            )
            for chunk in chunks
        ]
        new_ids = [record.point_id for record in records]
        prior = self._manifest.get(tier, path)
        prior_ids = prior.chunk_ids if prior is not None else []

        if records:
            result = await self._embedder.embed_documents(
                [record.embedding_text for record in records]
            )
            vectors = result.vectors
            if not self._all_vectors_usable(vectors):
                # Embedder failure / non-finite: mark failed, store NOTHING new,
                # leave any prior points in place (last-good retained). Continue.
                return self._mark_file_failed(
                    tier=tier, path=path, content_hash=content_hash, mtime_ns=mtime_ns,
                    size=size, prior=prior, prior_ids=prior_ids,
                    reason=_FAILED_EMBED_REASON,
                )

        # The Qdrant store ops (upsert NEW, then purge stale). Each already retries
        # a TRANSIENT failure internally (Layer 1); if one STILL fails for THIS
        # file past that budget, isolate it — mark the file failed, retain its
        # last-good points + manifest metadata, and let the OTHER files keep
        # indexing. A raw 500 escaping here is exactly the cold-index crash this
        # guards against. A non-store error (a real bug) is NOT caught — it
        # propagates loudly. Upsert and purge share one guard so a failure in
        # either leaves a consistent (failed, last-good-retained) state.
        try:
            if records:
                # Upsert NEW before purging stale: a concurrent reader sees the new
                # content (deterministic ids dedupe an unchanged chunk in place);
                # only then (below) are the genuinely stale ids removed.
                pairs = list(zip(records, [v for v in vectors if v is not None], strict=True))
                await self._store.upsert(pairs)

            # Purge stale ids (prior − new) AFTER any new points are upserted. This
            # runs even when ``records`` is empty (a file edited to yield no
            # chunks), so its prior points are never orphaned in the store. With
            # new records, the just-upserted ids are excluded (set difference).
            stale_ids = [pid for pid in prior_ids if pid not in set(new_ids)]
            await self._store.delete_points(stale_ids)
        except _STORE_FAILURE_ERRORS:
            logger.warning(
                "index.file.store_failed",
                extra={"tier": tier, "file_path": path, "reason": _FAILED_STORE_REASON},
                exc_info=True,
            )
            return self._mark_file_failed(
                tier=tier, path=path, content_hash=content_hash, mtime_ns=mtime_ns,
                size=size, prior=prior, prior_ids=prior_ids,
                reason=_FAILED_STORE_REASON,
            )

        # Transactional manifest commit (atomic delete-old + insert-new row).
        self._manifest.replace(
            tier=tier, file_path=path, sha512=content_hash, mtime_ns=mtime_ns,
            size=size, n_chunks=len(records), chunk_ids=new_ids, state=STATE_INDEXED,
        )
        # Keep the code-graph slice as fresh as the vector index: rebuild this
        # file's Python graph slice from the SAME chunks (transactional delete +
        # rebuild inside the graph). Only runs on the SUCCESS path — a failed
        # embed returned earlier, so the graph never diverges from what is indexed
        # (last-good graph retained alongside last-good vectors).
        self._refresh_graph(tier, path, chunks)
        duration_ms = (time.monotonic_ns() - started_ns) / 1_000_000
        logger.info(
            "index.file.done",
            extra={
                "tier": tier, "file_path": path, "n_chunks": len(records),
                "state": STATE_INDEXED, "duration_ms": duration_ms,
            },
        )
        return IndexOutcome(
            tier=tier, file_path=path, state=STATE_INDEXED, n_chunks=len(records)
        )

    def _mark_file_failed(
        self,
        *,
        tier: str,
        path: str,
        content_hash: str,
        mtime_ns: int,
        size: int,
        prior: FileRow | None,
        prior_ids: list[str],
        reason: str,
    ) -> IndexOutcome:
        """Mark ``(tier, path)`` ``failed`` (retaining last-good), and report it.

        The single failure-isolation path shared by an unusable embed and a
        persistent store error. NO new vectors are stored; any PRIOR points and
        the prior chunk metadata are retained (last-good), the manifest row is
        committed as ``failed``, an ``index.file.failed`` event is logged, and a
        ``failed`` :class:`IndexOutcome` is returned so the caller's tier/all
        loop continues with the other files instead of propagating the error.

        Args:
            tier: The tier the file belongs to.
            path: The tier-relative file path.
            content_hash: The new content's hash (recorded so a later identical
                re-index can still fast-path-skip a since-recovered file).
            mtime_ns: The file mtime in nanoseconds (0 for a direct-source index).
            size: The file size in bytes.
            prior: The prior manifest row, if any (its chunk count is retained).
            prior_ids: The prior point ids (retained — last-good points survive).
            reason: A generic, leak-free reason string for the failure event.

        Returns:
            A ``failed`` :class:`IndexOutcome` (``n_chunks=0`` — nothing stored).
        """
        self._manifest.upsert(
            tier=tier, file_path=path, sha512=content_hash, mtime_ns=mtime_ns,
            size=size, n_chunks=prior.n_chunks if prior else 0,
            chunk_ids=prior_ids, state=STATE_FAILED,
        )
        logger.warning(
            "index.file.failed",
            extra={"tier": tier, "file_path": path, "reason": reason},
        )
        return IndexOutcome(tier=tier, file_path=path, state=STATE_FAILED, n_chunks=0)

    def _refresh_graph(self, tier: str, path: str, chunks: list[Chunk]) -> None:
        """Rebuild ``(tier, path)``'s Python graph slice from ``chunks`` (if wired).

        A no-op when no :class:`~loremaster.graph.CodeGraph` is injected (backward
        compatible) or when ``path`` is not a Python file (the graph is a Python
        AST structure only — a markdown/sql/xml file must not synthesise a
        spurious module node). The graph's own ``build_file_graph`` is the
        transactional, tier-scoped delete+rebuild primitive, so a re-index updates
        only this file's slice and a removed symbol leaves no orphan edge.

        The module qualified-name passed to the graph is the TRUE importable
        dotted path, derived from the tier's on-disk package layout (the indexer
        owns the filesystem ``base`` the tier-relative ``path`` is relative to, so
        it — not the filesystem-agnostic graph — resolves the package root). This
        is what unifies node names with the ``imports``-edge ``dst`` strings: a
        workspace-member file ``loremaster/loremaster/config.py`` becomes the
        importable ``loremaster.config``, not the doubled
        ``loremaster.loremaster.config``.
        """
        if self._code_graph is None:
            return
        if not path.endswith(_PYTHON_SUFFIX):
            return
        module_name = self._importable_module_name(tier, path)
        self._code_graph.build_file_graph(tier, path, chunks, module_name=module_name)

    def _importable_module_name(self, tier: str, path: str) -> str | None:
        """Resolve the TRUE importable dotted module name for ``(tier, path)``.

        Locates the tier's on-disk ``base`` (the live root's ``path`` or the
        static tier's snapshot materialisation dir) and asks the graph's
        package-root detector for the importable name. Returns ``None`` when the
        tier's base is unknown (e.g. a tier with no registered root), letting
        ``build_file_graph`` fall back to its pure path-join — so the wiring stays
        robust even for a tier the config does not describe.

        Args:
            tier: The tier the file belongs to.
            path: The tier-relative POSIX file path.

        Returns:
            The importable dotted module name, or ``None`` to defer to the
            graph's path-join fallback.
        """
        from loremaster.graph import CodeGraph

        base = self._tier_base(tier)
        if base is None:
            return None
        return CodeGraph.importable_module_name(base, path)

    def _tier_base(self, tier: str) -> Path | None:
        """The on-disk root a tier's tier-relative file paths are relative to.

        A LIVE root's ``base`` is its declared ``path``; a STATIC tier's is its
        snapshot materialisation dir (the single source of truth). Mirrors the
        base resolution in :meth:`_index_live_tier` / :meth:`_index_static_tier`
        so the package-root probe walks the SAME directory the file was indexed
        from. ``None`` for a tier with no matching effective root.

        Args:
            tier: The tier to locate the base for.

        Returns:
            The tier's on-disk base directory, or ``None`` if unknown.
        """
        for root in self._config.effective_roots:
            if root.tier != tier:
                continue
            if root.watch == WATCH_LIVE and root.path is not None:
                return Path(root.path)
            return self._snapshot_layout.materialization_dir(tier)
        return None

    @staticmethod
    def _all_vectors_usable(vectors: list[list[float] | None]) -> bool:
        """True iff every vector is present (not ``None``) and fully finite.

        A ``None`` is a permanently-failed input; a non-finite component
        (NaN/inf) poisons cosine/argmax across every query. Either condition
        fails the whole file — defensive hygiene retained post-fp32.
        """
        for vector in vectors:
            if vector is None:
                return False
            if not all(math.isfinite(component) for component in vector):
                return False
        return True

    # -- per-tier orchestration --------------------------------------------

    async def index_tier(self, root: RootConfig) -> IndexSummary:
        """Index one tier per its freshness policy (D5).

        A LIVE tier is walked + indexed in full. A STATIC tier is freshness-gated
        on its version stamp: a matching stamp SKIPS the tier with zero walk; a
        changed/absent stamp acquires the snapshot, selectively rebuilds the tier
        (``delete_by_tier`` so siblings are untouched), and re-stamps.

        Args:
            root: The tier's :class:`~loremaster.config.RootConfig`.

        Returns:
            The :class:`IndexSummary` for this tier.
        """
        logger.debug("index.tier.start", extra={"tier": root.tier, "watch": root.watch})
        if root.watch == WATCH_LIVE:
            return await self._index_live_tier(root)
        return await self._index_static_tier(root)

    async def _index_live_tier(self, root: RootConfig) -> IndexSummary:
        """Walk a live root's included files and index each (mtime+size fast-path)."""
        assert root.path is not None  # validated by RootConfig
        base = Path(root.path)
        logger.debug("index.tier.rebuild", extra={"tier": root.tier, "watch": WATCH_LIVE})
        outcomes = await self._walk_and_index(root, base)
        return self._summarize(outcomes, rebuilt=[root.tier], skipped_tiers=[])

    async def _index_static_tier(self, root: RootConfig) -> IndexSummary:
        """Freshness-gate a static tier; acquire + rebuild + re-stamp on change."""
        assert root.version is not None  # validated by RootConfig
        if self.tier_version_stamp(root.tier) == root.version:
            # MATCH → skip with ZERO walk and zero acquisition.
            logger.info("index.tier.skip", extra={"tier": root.tier})
            return self._summarize([], rebuilt=[], skipped_tiers=[root.tier])

        # CHANGED/absent → acquire the snapshot via the tier's provider, then
        # selectively rebuild (purge only this tier) and walk the materialised
        # snapshot, finally re-stamping the built version.
        provider = self._providers_by_tier.get(root.tier)
        if provider is None:
            raise KeyError(
                f"static tier {root.tier!r} has no registered SourceProvider"
            )
        logger.info("index.tier.rebuild", extra={"tier": root.tier, "watch": WATCH_STATIC})
        provider.acquire(root.tier, self._snapshot_layout.snapshot_root)
        await self._store.delete_by_tier(root.tier)
        for stale in self._manifest.files_for_tier(root.tier):
            self._manifest.delete(root.tier, stale.file_path)

        base = self._snapshot_layout.materialization_dir(root.tier)
        outcomes = await self._walk_and_index(root, base)
        self.set_tier_version_stamp(root.tier, root.version)
        return self._summarize(outcomes, rebuilt=[root.tier], skipped_tiers=[])

    async def _walk_and_index(self, root: RootConfig, base: Path) -> list[IndexOutcome]:
        """Walk ``base`` (pruning excluded dirs), index each included file.

        Applies the manifest mtime+size fast-path *before* reading a file — an
        unchanged ``indexed`` file is skipped without a read or an embed. A
        file's stored ``file_path`` is POSIX-relative to ``base`` (the tier's
        walk root), so it is tier-relative and resolvable by the snapshot layout.
        """
        outcomes: list[IndexOutcome] = []
        for dirpath in walked_dirs(self._config, base):
            # ``walked_dirs`` prunes ``exclude_dirs`` at the os.walk level (the
            # .git/.venv/worktree-copy rule + the perf rule, one mechanism).
            for filename in sorted(os.listdir(dirpath)):
                abs_path = Path(dirpath) / filename
                if not abs_path.is_file():
                    continue
                rel = str(PurePosixPath(abs_path.relative_to(base).as_posix()))
                if not is_included(self._config, root, rel):
                    continue
                stat = abs_path.stat()
                if not self._manifest.needs_reindex(
                    root.tier, rel, stat.st_mtime_ns, stat.st_size
                ):
                    outcomes.append(
                        IndexOutcome(
                            tier=root.tier, file_path=rel, state=STATE_SKIPPED,
                            n_chunks=self._chunk_count(root.tier, rel),
                        )
                    )
                    continue
                source = abs_path.read_text(encoding="utf-8")
                content_hash = sha512_hex(source)
                chunks = self._chunk(rel, source)
                outcome = await self._index_chunks(
                    tier=root.tier, path=rel, content_hash=content_hash,
                    chunks=chunks, mtime_ns=stat.st_mtime_ns, size=stat.st_size,
                )
                outcomes.append(outcome)
        return outcomes

    def _chunk_count(self, tier: str, path: str) -> int:
        """The committed chunk count for a fast-path-skipped file (manifest read)."""
        row = self._manifest.get(tier, path)
        return row.n_chunks if row is not None else 0

    # -- whole-project orchestration ---------------------------------------

    async def index_all(self) -> IndexSummary:
        """Index every effective root, accumulating into one :class:`IndexSummary`.

        Iterates :attr:`LoreConfig.effective_roots`, not the raw ``roots`` list,
        so a single-tree config (top-level ``include`` globs and NO ``roots:``)
        indexes its synthesised default live root instead of silently indexing
        nothing.
        """
        outcomes: list[IndexOutcome] = []
        rebuilt: list[str] = []
        skipped_tiers: list[str] = []
        for root in self._config.effective_roots:
            summary = await self.index_tier(root)
            outcomes.extend(summary.outcomes)
            rebuilt.extend(summary.tiers_rebuilt)
            skipped_tiers.extend(summary.tiers_skipped)
        return self._summarize(outcomes, rebuilt=rebuilt, skipped_tiers=skipped_tiers)

    def index_status(self) -> IndexSummary:
        """Return a freshness roll-up read PURELY from the manifest (zero embeds).

        Counts each file row by state across every tier — the cheap health
        surface the deploy healthcheck polls. ``outcomes`` is empty (this is a
        roll-up, not a per-file run) and the tier lists are empty (no run
        happened); the counts reflect the manifest's current state.

        Returns:
            An :class:`IndexSummary` whose counts come from the manifest.
        """
        indexed = failed = 0
        for row in self._manifest.all_files():
            if row.state == STATE_INDEXED:
                indexed += 1
            elif row.state == STATE_FAILED:
                failed += 1
        return IndexSummary(
            files_indexed=indexed, files_failed=failed, files_skipped=0,
            tiers_rebuilt=[], tiers_skipped=[], outcomes=[],
        )

    @staticmethod
    def _summarize(
        outcomes: list[IndexOutcome], *, rebuilt: list[str], skipped_tiers: list[str]
    ) -> IndexSummary:
        """Roll per-file outcomes + tier dispositions into an :class:`IndexSummary`."""
        return IndexSummary(
            files_indexed=sum(1 for o in outcomes if o.state == STATE_INDEXED),
            files_failed=sum(1 for o in outcomes if o.state == STATE_FAILED),
            files_skipped=sum(1 for o in outcomes if o.state == STATE_SKIPPED),
            tiers_rebuilt=rebuilt,
            tiers_skipped=skipped_tiers,
            outcomes=outcomes,
        )

    # -- version stamps (D5) -----------------------------------------------

    def tier_version_stamp(self, tier: str) -> str | None:
        """Return the built version stamp for ``tier`` from the manifest ``meta``."""
        return self._manifest.meta_get(_tier_version_meta_key(tier))

    def set_tier_version_stamp(self, tier: str, version: str) -> None:
        """Stamp ``tier``'s built version into the manifest ``meta``."""
        self._manifest.meta_set(_tier_version_meta_key(tier), version)
