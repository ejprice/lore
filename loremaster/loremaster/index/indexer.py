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
texts; build records via ``chunk_to_record(..., tier=tier)``; then commit the
chunk-replace + verbatim ``file_text`` body + manifest row (+ the Python code-graph
slice for a ``.py`` file) as ONE atomic composed ``SurrealStore.apply`` transaction
— **atomicity, not an upsert-before-purge ordering**, is what keeps a concurrent
reader from ever observing a half-applied file, so the stale points/edges vanish in
the SAME commit the new ones land in (``state='indexed'``).

**Resilience.** A chunker exception (any ``Exception`` the registry's chunker
raises — a malformed-document ``ParseError``, a recursion-DoS ``ValueError``,
etc.), a permanently-failed embed (a ``None`` vector), OR a non-finite vector
(an ``isfinite`` guard — one NaN poisons cosine/argmax across every query)
marks the file ``failed``, stores **no** vectors for it, and lets the other
files continue — the file never reaches the embedder; the failure is surfaced
in the returned :class:`IndexSummary`.

**Selective rebuild.** Rebuilding one tier uses ``delete_by_tier`` so sibling
tiers are untouched (the C1 primitive).
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any

from lorescribe.models import Chunk, ChunkContext
from pydantic import BaseModel, ConfigDict

from loremaster.config import WATCH_LIVE, WATCH_STATIC, LoreConfig, RootConfig
from loremaster.index.manifest import (
    STATE_FAILED,
    STATE_INDEXED,
    FileRow,
)
from loremaster.index.paths import is_included, walked_dirs
from loremaster.index.records import Record, chunk_to_record, sha512_hex
from loremaster.index.schema import (
    SCHEMA_FINGERPRINT_META_KEY,
    SCHEMA_REBUILD_STATUS_META_KEY,
)
from loremaster.source.snapshot import SnapshotLayout
from loremaster.store.surreal import SurrealStoreError

if TYPE_CHECKING:
    from lorescribe.registry import ChunkerRegistry
    from loresigil.base import Embedder, EmbedResult

    from loremaster.extension import SourceProvider

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

# The schema-rebuild status state values written into the
# ``schema_rebuild_status`` meta blob as ``rebuild_all`` progresses. ``done`` is
# stamped ONLY after every tier completes successfully (the crash-safety contract).
_REBUILD_STATE_IN_PROGRESS = "in_progress"
_REBUILD_STATE_DONE = "done"
# The terminal FAILED state written when a background rebuild's underlying work
# raises (FP-11). It replaces the otherwise-stuck ``in_progress`` so a dead
# rebuild is reported as failed rather than a phantom perpetual in-progress; the
# fingerprint is NOT stamped on failure, so the next startup re-triggers.
_REBUILD_STATE_FAILED = "failed"

# The reason recorded in the rebuild-status blob when the rebuild is driven by a
# fingerprint mismatch (the only trigger today). Named so the server (the other
# producer) and any consumer agree on the literal.
_REBUILD_REASON_FINGERPRINT_MISMATCH = "fingerprint_mismatch"


logger = logging.getLogger(__name__)


def graph_roots(
    config: LoreConfig, snapshot_root: Path
) -> tuple[dict[str, str], list[str]]:
    """Derive the ``(tier_roots, project_roots)`` the code-graph resolves against.

    The SINGLE source of truth for wiring astroid resolution into a
    :class:`~loremaster.graph.CodeGraph` at its construction sites (the CLI and the
    server lifespan), so both build the same roots and the indexer's per-file
    ``base`` resolution (:meth:`Indexer._tier_base`) and the graph's resolution
    agree on where each tier's files live.

    * ``tier_roots`` maps every effective tier to its on-disk base — a LIVE root's
      declared ``path``, a STATIC tier's snapshot materialisation dir (the same
      directory the indexer probed for the importable-name derivation).
    * ``project_roots`` is the set of bases astroid adds to its search path and
      uses to classify a reference in-project vs external. ALL tier bases are
      included (a static vendored tree is still "in project" for its own internal
      references; an import that resolves outside every base is the external noise
      the keep/drop rule drops).

    Args:
        config: The validated project configuration (its ``effective_roots`` drive
            the mapping — explicit roots or the synthesised single-tree root).
        snapshot_root: The static-tier snapshot root (the base for static tiers'
            materialisation dirs).

    Returns:
        A ``(tier_roots, project_roots)`` pair ready to pass to ``CodeGraph``.
    """
    layout = SnapshotLayout(snapshot_root)
    tier_roots: dict[str, str] = {}
    for root in config.effective_roots:
        if root.watch == WATCH_LIVE and root.path is not None:
            tier_roots[root.tier] = str(Path(root.path))
        else:
            tier_roots[root.tier] = str(layout.materialization_dir(root.tier))
    # De-duplicate the bases (two tiers can share a root) while preserving order.
    project_roots = list(dict.fromkeys(tier_roots.values()))
    return tier_roots, project_roots


# The reason string attached to an ``index.file.failed`` event. Kept generic (no
# source text or vector data) — a permanently-failed/non-finite embed is the only
# failure path here, so naming it is enough for an operator to triage.
_FAILED_EMBED_REASON = "embed_failed_or_non_finite"

# The reason attached to ``index.file.failed`` when the composed per-file STORE
# transaction is REFUSED — a typed :class:`~loremaster.store.surreal.SurrealStoreError`
# from ``compose``/``apply`` (the hard statement-count cap overflow of a
# pathologically chunk-heavy file, or a server-side rollback). The atomic apply
# replaces the old upsert-then-purge ordering, so there is no partial residue: THIS
# one file is isolated ``failed`` and the sweep continues, exactly like the chunker
# fault-isolation contract one step earlier in the pipeline.
_FAILED_STORE_REASON = "store_op_failed_after_retries"

# The reason attached to ``index.file.failed`` when the CHUNK step (the
# registry's ``dispatch_file``) raises. Deliberately broad at the catch site —
# any ``Exception`` a chunker raises (a malformed-document ``ParseError``, a
# recursion-DoS ``ValueError`` from ``lorescribe.xml_generic``'s depth gate,
# or any other chunker-specific failure) isolates the ONE file rather than
# propagating out of the walk / ``index_file`` and killing the whole sweep —
# the same isolation the embed and store steps already have, extended to the
# step that precedes them (a chunker-failed file never reaches the embedder).
_FAILED_CHUNK_REASON = "chunk_failed"


def _tier_version_meta_key(tier: str) -> str:
    """The manifest ``meta`` key holding ``tier``'s built version stamp."""
    return f"{_TIER_VERSION_META_PREFIX}{tier}"


class IndexOutcome(BaseModel):
    """The result of indexing a single file.

    Attributes:
        tier: The tier the file belongs to.
        file_path: The tier-relative file path.
        state: ``indexed`` (freshly embedded), ``skipped`` (fast-path,
            unchanged), or ``failed`` (a chunker exception, an embed/finite-guard
            rejection, or a persistent store error).
        n_chunks: The number of chunks the file produced (0 for an unclaimed
            extension).
    """

    model_config = ConfigDict(extra="forbid")

    tier: str
    file_path: str
    state: str
    n_chunks: int



class EmbeddingSchemaStatus(BaseModel):
    """The embedding-schema fingerprint and epoch surfaced by ``index_status``.

    Attributes:
        fingerprint: The SHA-256 hex digest of the current embedding-schema
            fields, or ``None`` when no fingerprint has been stamped yet.
        version: The :data:`~loremaster.index.schema.EMBEDDING_SCHEMA_VERSION`
            epoch constant in effect when the status was read.
    """

    model_config = ConfigDict(extra="forbid")

    fingerprint: str | None = None
    version: int = 1


class SchemaRebuildStatus(BaseModel):
    """The in-progress / idle schema-rebuild status surfaced by ``index_status``.

    Attributes:
        state: ``"idle"``, ``"in_progress"``, or ``"done"``.
        done: Files re-embedded so far (0 when idle or not yet started).
        total: Total files to re-embed (0 when idle).
        reason: Why the rebuild was triggered (empty string when idle).
        from_fingerprint: The fingerprint being replaced, or ``None``.
        to_fingerprint: The target fingerprint, or ``None``.
    """

    model_config = ConfigDict(extra="forbid")

    state: str = "idle"
    done: int = 0
    total: int = 0
    reason: str = ""
    from_fingerprint: str | None = None
    to_fingerprint: str | None = None

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
    embedding_schema: EmbeddingSchemaStatus | None = None
    schema_rebuild: SchemaRebuildStatus | None = None


class Indexer:
    """Build/refresh a project's Qdrant index, tier by tier (dependency-injected).

    Every collaborator is injected so tests pass a :class:`FakeEmbedder`, a real
    Qdrant client (throwaway collection), a temp-file manifest, and real files,
    while the CLI wires the real deployment resources.

    Args:
        store: The async :class:`~loremaster.store.surreal.SurrealStore` — its
            composed-transaction ``apply`` plus the pure chunk / ``file_text``
            fragment builders back the atomic per-file update.
        embedder: The active :class:`loresigil.base.Embedder`.
        manifest: The async :class:`~loremaster.index.surreal_manifest.SurrealManifest`.
        registry: The composed :class:`~lorescribe.registry.ChunkerRegistry`.
        source_providers: The :class:`SourceProvider`s, one per static tier
            (matched to a tier by the provider's ``tier`` attribute).
        config: The validated :class:`~loremaster.config.LoreConfig`.
        snapshot_root: The on-disk root static tiers are materialised under and
            served from (bind-mounted ``:ro`` at ``/source`` in the live server).
        snapshot_stamper: Optional :class:`~loremaster.index.snapshots.
            SnapshotStamper` (the capability layer, mirrors ``code_graph``).
            When wired, :meth:`index_all` and :meth:`rebuild_all` stamp a new
            snapshot on a FULLY-successful, genuinely-productive sweep (see
            :meth:`_maybe_stamp_snapshot`); absent, the indexer behaves exactly
            as before (backward compatible).
    """

    def __init__(
        self,
        *,
        store: Any,
        embedder: Embedder,
        manifest: Any,
        registry: ChunkerRegistry,
        source_providers: Sequence[SourceProvider],
        config: LoreConfig,
        snapshot_root: Path,
        code_graph: Any = None,
        snapshot_stamper: Any = None,
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
        # Optional snapshot stamper (P5-C4, the versioning capability layer,
        # mirrors ``code_graph``). When present, a fully-successful, genuinely
        # productive sweep (``index_all`` / ``rebuild_all``) stamps a new
        # ``snapshot`` generation marker; absent, the indexer behaves exactly
        # as before (backward compatible).
        self._snapshot_stamper = snapshot_stamper

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

        A chunker exception (ANY ``Exception`` the registry raises — a malformed
        document's ``ParseError``, a recursion-DoS ``ValueError``, etc.) is
        isolated to this ONE file: it is marked ``failed`` and this method
        returns that outcome instead of propagating, so the watcher's live-event
        drain never crashes on a single poisoned file.

        Args:
            tier: The tier the file belongs to.
            path: The tier-relative file path.
            source: The file's full text.

        Returns:
            The :class:`IndexOutcome` (``indexed`` / ``skipped`` / ``failed``).
        """
        content_hash = sha512_hex(source)
        existing = await self._manifest.get(tier, path)
        if (
            existing is not None
            and existing.state == STATE_INDEXED
            and existing.sha512 == content_hash
        ):
            return IndexOutcome(
                tier=tier, file_path=path, state=STATE_SKIPPED, n_chunks=existing.n_chunks
            )

        size = len(source.encode("utf-8"))
        try:
            chunks = self._chunk(path, source)
        except Exception:
            # ANY chunker exception (ParseError, a recursion-DoS ValueError,
            # etc.) isolates THIS file instead of propagating out of the
            # watcher's live-event path — mirrors the embed/store isolation
            # below, one step earlier.
            return await self._handle_chunk_failure(
                tier=tier, path=path, content_hash=content_hash, mtime_ns=0, size=size,
            )
        return await self._index_chunks(
            tier=tier, path=path, content_hash=content_hash, source=source,
            chunks=chunks, mtime_ns=0, size=size,
        )

    async def _index_chunks(
        self,
        *,
        tier: str,
        path: str,
        content_hash: str,
        source: str,
        chunks: list[Chunk],
        mtime_ns: int,
        size: int,
    ) -> IndexOutcome:
        """Embed ``chunks``, then commit chunks + ``file_text`` + manifest (+ graph)
        as ONE atomic composed transaction.

        An unclaimed file (no chunks) is committed as a zero-chunk ``indexed`` row
        (so a directory walk never re-reads it) — its chunk fragment is a bare
        DELETE that purges any prior points, so an edit down to zero chunks never
        orphans them. Otherwise the chunk texts are embedded via
        :meth:`_embed_records`, which feature-detects
        ``self._embedder.supports_contextualized`` to pick the call site: a
        contextualized-capable embedder gets the WHOLE file's chunks as one grouped
        document (``embed_document_chunks``); every other embedder keeps the flat
        ``embed_documents`` call. If ANY vector is missing (``None`` — permanent
        failure) or non-finite (the ``isfinite`` guard), the whole file is marked
        ``failed`` in a SMALL separate manifest-only write and NO surface is touched
        — the prior points/graph are retained (last-good).

        On the success path the chunk-replace, ``file_text`` body, manifest row and
        (for a ``.py`` file with a wired graph) code-graph slice are composed into
        ONE :meth:`SurrealStore.apply` transaction, so a concurrent reader never
        observes a half-applied file and the stale chunks/edges vanish in the SAME
        commit the new ones land in. An oversized ``file_text`` body (over the
        store's :attr:`file_text_max_bytes` cap) is indexed WITHOUT the file_text
        fragment (a single WARNING; chunks/manifest/graph still land ``indexed``). A
        composed transaction that would overflow the store's hard statement cap is
        refused LOUDLY by ``apply`` (a typed :class:`SurrealStoreError`) and isolated
        ``failed`` — one pathological file never kills the sweep.
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
        prior = await self._manifest.get(tier, path)
        prior_ids = prior.chunk_ids if prior is not None else []

        usage_tokens: int | None = None
        vectors: list[list[float] | None] = []
        if records:
            result = await self._embed_records(records)
            vectors = result.vectors
            if not self._all_vectors_usable(vectors):
                # Embedder failure / non-finite: mark failed in a SMALL separate
                # manifest-only write, store NOTHING new, leave any prior points +
                # graph in place (last-good retained). The sweep continues.
                return await self._mark_file_failed(
                    tier=tier, path=path, content_hash=content_hash, mtime_ns=mtime_ns,
                    size=size, prior=prior, prior_ids=prior_ids,
                    reason=_FAILED_EMBED_REASON,
                )
            usage_tokens = result.usage.total_tokens if result.usage is not None else None

        # The composed atomic per-file transaction (clause 1): chunk-replace +
        # ``file_text`` body + manifest row (+ graph slice for a wired ``.py``),
        # applied ALL-OR-NOTHING through ONE ``store.apply``. Atomicity replaces the
        # old upsert-new-before-purge ordering — a concurrent reader observes only
        # the complete pre- or post-replace state, so the stale points/edges are
        # purged in the SAME commit the new ones land in. A composed transaction the
        # store refuses (its hard statement-count cap overflowed — a pathologically
        # chunk-heavy file) raises a typed :class:`SurrealStoreError` at BUILD time,
        # before anything persists; catch it, isolate THIS file ``failed`` (last-good
        # retained), and let the OTHER files keep indexing (clause 5).
        try:
            fragments = self._compose_file_fragments(
                tier=tier, path=path, source=source, content_hash=content_hash,
                records=records, vectors=vectors, new_ids=new_ids,
                mtime_ns=mtime_ns, size=size, chunks=chunks,
            )
            await self._store.apply(fragments)
        except SurrealStoreError:
            logger.warning(
                "index.file.store_failed",
                extra={"tier": tier, "file_path": path, "reason": _FAILED_STORE_REASON},
                exc_info=True,
            )
            return await self._mark_file_failed(
                tier=tier, path=path, content_hash=content_hash, mtime_ns=mtime_ns,
                size=size, prior=prior, prior_ids=prior_ids,
                reason=_FAILED_STORE_REASON,
            )

        duration_ms = (time.monotonic_ns() - started_ns) / 1_000_000
        logger.info(
            "index.file.done",
            extra={
                "tier": tier, "file_path": path, "n_chunks": len(records),
                "state": STATE_INDEXED, "duration_ms": duration_ms,
                "usage_tokens": usage_tokens,
            },
        )
        return IndexOutcome(
            tier=tier, file_path=path, state=STATE_INDEXED, n_chunks=len(records)
        )

    def _compose_file_fragments(
        self,
        *,
        tier: str,
        path: str,
        source: str,
        content_hash: str,
        records: list[Record],
        vectors: list[list[float] | None],
        new_ids: list[str],
        mtime_ns: int,
        size: int,
        chunks: list[Chunk],
    ) -> list[Any]:
        """Build the ordered producer fragments for one file's atomic apply.

        Spans the four producers the per-file transaction covers: the chunk-replace
        (a DELETE + one UPSERT per record — empty ``records`` composes a bare DELETE
        that purges any prior points), the ``file_text`` body (SKIPPED when it
        exceeds the store's cap — see :meth:`_file_text_within_cap`), the manifest
        row (committed ``indexed``), and — only for a ``.py`` file with a wired graph
        — the code-graph slice. The chunk vectors are paired with their records
        positionally; the embed guard upstream already proved every vector present.

        Returns:
            The fragment list ready to hand to :meth:`SurrealStore.apply`, ordered
            chunk → file_text → manifest → graph.
        """
        pairs = list(zip(records, [v for v in vectors if v is not None], strict=True))
        fragments: list[Any] = [self._store.replace_file_fragment(tier, path, pairs)]
        if self._file_text_within_cap(tier, path, source):
            fragments.append(self._store.file_text_fragment(tier, path, source, content_hash))
        fragments.append(
            self._manifest.replace_fragment(
                tier=tier, file_path=path, sha512=content_hash, mtime_ns=mtime_ns,
                size=size, n_chunks=len(records), chunk_ids=new_ids, state=STATE_INDEXED,
            )
        )
        graph_fragment = self._graph_fragment(tier, path, chunks)
        if graph_fragment is not None:
            fragments.append(graph_fragment)
        return fragments

    def _file_text_within_cap(self, tier: str, path: str, source: str) -> bool:
        """Whether ``source``'s UTF-8 byte size is within the store's file_text cap.

        The clause-4 pre-check: the per-body byte ceiling is READ from the store
        (:attr:`SurrealStore.file_text_max_bytes` — the single source of truth, never
        a hand-copied literal), so an oversized body is skipped BEFORE the fragment
        is built rather than crashing the composed apply. A skip logs one WARNING
        naming the file + byte sizes (never the source text) and drops only the
        ``file_text`` fragment — the chunks, manifest row and graph slice still land
        ``indexed``.

        Returns:
            ``True`` to include the ``file_text`` fragment; ``False`` to skip it.
        """
        body_bytes = len(source.encode("utf-8"))
        cap: int = self._store.file_text_max_bytes
        if body_bytes > cap:
            logger.warning(
                "index.file.file_text_skipped",
                extra={
                    "tier": tier, "file_path": path,
                    "reason": "file_text_body_exceeds_cap",
                    "body_bytes": body_bytes, "cap_bytes": cap,
                },
            )
            return False
        return True

    def _graph_fragment(self, tier: str, path: str, chunks: list[Chunk]) -> Any:
        """Build ``(tier, path)``'s code-graph fragment for the composed apply, or None.

        ``None`` when no :class:`~loremaster.graph_surreal.SurrealCodeGraph` is wired
        (backward compatible) or when ``path`` is not a Python file (the graph is a
        Python-AST structure only — a markdown/sql/xml file must never synthesise a
        spurious module node). Otherwise the graph's PURE
        ``build_file_graph_fragment`` derives the slice (astroid at BUILD time) and
        returns its purge+upsert+relate fragment, which rides the SAME per-file
        transaction as the chunk/file_text/manifest fragments — so the graph slice is
        as fresh, and as atomic, as the vector index. The module qualified-name is
        the TRUE importable dotted path (see :meth:`_importable_module_name`),
        unifying a node's name with the ``imports``-edge ``dst`` strings.
        """
        if self._code_graph is None:
            return None
        if not path.endswith(_PYTHON_SUFFIX):
            return None
        module_name = self._importable_module_name(tier, path)
        return self._code_graph.build_file_graph_fragment(
            tier, path, chunks, module_name=module_name
        )

    async def _embed_records(self, records: Sequence[Record]) -> EmbedResult:
        """Embed ``records``' texts, dispatching on the embedder's grouping capability.

        A ``supports_contextualized`` embedder (e.g. voyage-context) gets the
        file's chunk texts as EXACTLY ONE document — one file == one document,
        the doc-grouping semantics the contextualized backend needs to produce
        context-sensitive vectors — via ``embed_document_chunks``, and this
        returns that single doc's :class:`~loresigil.base.EmbedResult`. Every
        other embedder uses the pre-existing flat ``embed_documents`` call,
        unchanged (back-compat, byte-identical to before this dispatch existed).

        Args:
            records: The file's chunk records, in order.

        Returns:
            The :class:`~loresigil.base.EmbedResult` for this file's chunks,
            positionally aligned with ``records`` either way.
        """
        texts = [record.embedding_text for record in records]
        if self._embedder.supports_contextualized:
            doc_results = await self._embedder.embed_document_chunks([texts])
            return doc_results[0]
        return await self._embedder.embed_documents(texts)

    async def _mark_file_failed(
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
        await self._manifest.upsert(
            tier=tier, file_path=path, sha512=content_hash, mtime_ns=mtime_ns,
            size=size, n_chunks=prior.n_chunks if prior else 0,
            chunk_ids=prior_ids, state=STATE_FAILED,
        )
        logger.warning(
            "index.file.failed",
            extra={"tier": tier, "file_path": path, "reason": reason},
        )
        return IndexOutcome(tier=tier, file_path=path, state=STATE_FAILED, n_chunks=0)

    async def _handle_chunk_failure(
        self, *, tier: str, path: str, content_hash: str, mtime_ns: int, size: int
    ) -> IndexOutcome:
        """Isolate a chunker exception: mark ``(tier, path)`` ``failed`` and report it.

        Called from the ``except Exception`` clause around each ``self._chunk``
        call site (:meth:`index_file`, :meth:`_walk_and_index`) — the ONLY
        broadly-caught exception class in this module, deliberately so: the
        registry's chunkers raise a variety of types for a genuinely invalid
        document (``xml.etree.ElementTree.ParseError`` for malformed/empty/
        truncated XML, ``ValueError`` from ``lorescribe.xml_generic``'s
        recursion-DoS depth gate, etc.), and every one of them must isolate the
        ONE poisoned file rather than climb out of a sweep or a live watcher
        event. The file never reaches the embedder. Delegates the actual
        failure-commit to :meth:`_mark_file_failed` (the single failure-isolation
        path shared by the chunk, embed, and store steps), first logging the
        live traceback (``exc_info=True`` — valid here because this is always
        called from within the triggering ``except`` block) for triage.

        Args:
            tier: The tier the file belongs to.
            path: The tier-relative file path.
            content_hash: The new content's hash (recorded so a later identical
                re-index can still fast-path-skip a since-recovered file).
            mtime_ns: The file mtime in nanoseconds (0 for a direct-source index).
            size: The file size in bytes.

        Returns:
            A ``failed`` :class:`IndexOutcome` (``n_chunks=0`` — nothing stored).
        """
        prior = await self._manifest.get(tier, path)
        prior_ids = prior.chunk_ids if prior is not None else []
        logger.warning(
            "index.file.chunk_failed",
            extra={"tier": tier, "file_path": path, "reason": _FAILED_CHUNK_REASON},
            exc_info=True,
        )
        return await self._mark_file_failed(
            tier=tier, path=path, content_hash=content_hash, mtime_ns=mtime_ns,
            size=size, prior=prior, prior_ids=prior_ids, reason=_FAILED_CHUNK_REASON,
        )

    async def _refresh_graph(self, tier: str, path: str, chunks: list[Chunk]) -> None:
        """Rebuild ``(tier, path)``'s Python graph slice STANDALONE (graph-only heal).

        The atomic per-file index composes the graph as a FRAGMENT in the ONE
        per-file transaction (see :meth:`_graph_fragment`); this STANDALONE path is
        used ONLY by :meth:`rebuild_graph_only`, which re-derives a tier's graph
        slices from disk WITHOUT touching the healthy vector collection (no embed,
        no composed apply). A no-op when no
        :class:`~loremaster.graph_surreal.SurrealCodeGraph` is injected or when
        ``path`` is not a Python file. The graph's own ``build_file_graph`` is the
        transactional, tier-scoped delete+rebuild primitive.

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
        await self._code_graph.build_file_graph(tier, path, chunks, module_name=module_name)

    def _reset_graph_resolution_cache(self) -> None:
        """Bound astroid's resolution cache at a full-sweep boundary (if graph wired).

        The graph keeps astroid's dependency cache WARM across the files of a sweep
        (each in-project dependency is parsed ~once per sweep, not once per file —
        the cold-build speed win). That cache is process-global, so to stop it
        growing without limit across a long-lived server it is reset ONCE per full
        sweep, at the start of :meth:`rebuild_all` / :meth:`rebuild_graph_only`.
        A no-op when no graph is wired.
        """
        if self._code_graph is None:
            return
        self._code_graph.reset_resolution_cache()

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

    def _snapshot_materialized(self, tier: str) -> bool:
        """True iff a static tier's snapshot materialisation dir is present + non-empty.

        The fast-skip guard for :meth:`_index_static_tier` (FP-05): a matching
        version stamp may short-circuit the tier ONLY when the snapshot it vouches
        for is still on disk and actually holds files. A dir that is absent (a lost
        volume) OR present-but-empty (a remounted-empty volume) serves no file —
        ``read_file`` misses for every path — so both are treated as un-materialised
        and force a re-acquire.

        Args:
            tier: The static tier to check.

        Returns:
            ``True`` when the materialisation dir exists and contains at least one
            entry; ``False`` when it is absent or empty.
        """
        materialization_dir = self._snapshot_layout.materialization_dir(tier)
        if not materialization_dir.is_dir():
            return False
        # ``any(iterdir())`` is True for a dir with at least one entry; an empty dir
        # is as broken as an absent one for serving, so it fails the guard too.
        return any(materialization_dir.iterdir())

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
        # The version-stamp skip is an optimisation that ASSUMES the snapshot the
        # stamp vouches for is still materialised. Three-way logic on a MATCHING
        # stamp (FP-05):
        #   * snapshot present + non-empty            → SKIP (the fast-path; the
        #     served files are intact, regardless of manifest rows).
        #   * snapshot absent/empty + tier HAS rows   → RE-ACQUIRE (the genuine
        #     "built then lost the snapshot volume" case — the manifest/state dir
        #     survived so indexed rows are still there, but the served files are
        #     physically gone; re-materialise them).
        #   * snapshot absent/empty + ZERO tier rows  → SKIP (a degenerate stamp-
        #     only state — a version was stamped but nothing was ever built, so
        #     there is nothing to serve and nothing to re-acquire).
        # A stamp is only legitimately written after a real build (which produces
        # both manifest rows AND a materialised snapshot), so "stamp + rows but no
        # snapshot" is the lost-volume signature and "stamp + no rows" is the
        # never-built signature.
        if await self.tier_version_stamp(root.tier) == root.version and (
            self._snapshot_materialized(root.tier)
            or await self._manifest.indexed_file_count(tier=root.tier) == 0
        ):
            # MATCH + (present snapshot OR nothing ever built) → skip with ZERO
            # walk and zero acquisition.
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
        for stale in await self._manifest.files_for_tier(root.tier):
            await self._manifest.delete(root.tier, stale.file_path)

        base = self._snapshot_layout.materialization_dir(root.tier)
        outcomes = await self._walk_and_index(root, base)
        await self.set_tier_version_stamp(root.tier, root.version)
        return self._summarize(outcomes, rebuilt=[root.tier], skipped_tiers=[])

    async def _walk_and_index(
        self,
        root: RootConfig,
        base: Path,
        on_file_indexed: Callable[[IndexOutcome], Awaitable[None]] | None = None,
    ) -> list[IndexOutcome]:
        """Walk ``base`` (pruning excluded dirs), index each included file.

        Applies the manifest mtime+size fast-path *before* reading a file — an
        unchanged ``indexed`` file is skipped without a read or an embed. A
        file's stored ``file_path`` is POSIX-relative to ``base`` (the tier's
        walk root), so it is tier-relative and resolvable by the snapshot layout.

        Args:
            root: The :class:`RootConfig` for this tier.
            base: The filesystem root to walk (tier's materialisation dir).
            on_file_indexed: Optional per-file callback invoked IMMEDIATELY after
                each file is ACTUALLY indexed (i.e. after
                :meth:`_index_chunks` returns its :class:`IndexOutcome`).
                Skipped/fast-path files do NOT trigger this callback — only real
                embeds do.  Defaults to ``None`` (no-op) so existing callers
                (:meth:`_index_live_tier`, :meth:`_index_static_tier`) are
                unaffected.
        """
        # A full-tier walk is a SWEEP: start it from a clean astroid resolution
        # cache (then keep the cache warm across this tier's files so each in-project
        # dependency is parsed ~once per sweep, not once per file). This is the one
        # walk primitive every full index path funnels through — live, static, and
        # the per-tier loop of ``rebuild_all`` — so resetting here bounds the warm
        # cache at exactly each tier-sweep boundary.
        self._reset_graph_resolution_cache()
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
                if not await self._manifest.needs_reindex(
                    root.tier, rel, stat.st_mtime_ns, stat.st_size
                ):
                    outcomes.append(
                        IndexOutcome(
                            tier=root.tier, file_path=rel, state=STATE_SKIPPED,
                            n_chunks=await self._chunk_count(root.tier, rel),
                        )
                    )
                    continue
                source = abs_path.read_text(encoding="utf-8")
                content_hash = sha512_hex(source)
                try:
                    chunks = self._chunk(rel, source)
                except Exception:
                    # ANY chunker exception isolates THIS file (the walk-level
                    # frames the production crash climbed) instead of killing
                    # the whole sweep — mirrors the embed/store isolation one
                    # step later in the pipeline.
                    outcome = await self._handle_chunk_failure(
                        tier=root.tier, path=rel, content_hash=content_hash,
                        mtime_ns=stat.st_mtime_ns, size=stat.st_size,
                    )
                else:
                    outcome = await self._index_chunks(
                        tier=root.tier, path=rel, content_hash=content_hash, source=source,
                        chunks=chunks, mtime_ns=stat.st_mtime_ns, size=stat.st_size,
                    )
                outcomes.append(outcome)
                # Notify the caller that this file has been indexed.  Called AFTER
                # _index_chunks so the outcome is final before the callback fires.
                # Skipped files intentionally do NOT trigger this (fast-path means
                # no new embedding occurred — nothing to report as live progress).
                if on_file_indexed is not None:
                    await on_file_indexed(outcome)
        return outcomes

    async def _chunk_count(self, tier: str, path: str) -> int:
        """The committed chunk count for a fast-path-skipped file (manifest read)."""
        row = await self._manifest.get(tier, path)
        if row is None:
            return 0
        n_chunks: int = row.n_chunks
        return n_chunks

    # -- whole-project orchestration ---------------------------------------

    async def index_all(self) -> IndexSummary:
        """Index every effective root, accumulating into one :class:`IndexSummary`.

        Iterates :attr:`LoreConfig.effective_roots`, not the raw ``roots`` list,
        so a single-tree config (top-level ``include`` globs and NO ``roots:``)
        indexes its synthesised default live root instead of silently indexing
        nothing. On a FULLY-successful, genuinely-productive sweep, stamps a
        new snapshot generation (see :meth:`_maybe_stamp_snapshot`).
        """
        outcomes: list[IndexOutcome] = []
        rebuilt: list[str] = []
        skipped_tiers: list[str] = []
        for root in self._config.effective_roots:
            summary = await self.index_tier(root)
            outcomes.extend(summary.outcomes)
            rebuilt.extend(summary.tiers_rebuilt)
            skipped_tiers.extend(summary.tiers_skipped)
        result = self._summarize(outcomes, rebuilt=rebuilt, skipped_tiers=skipped_tiers)
        await self._maybe_stamp_snapshot(result)
        return result

    async def _maybe_stamp_snapshot(self, summary: IndexSummary) -> None:
        """Stamp a new snapshot generation iff this sweep fully succeeded AND did
        something (P5-C4, ledger #25).

        The shared stamp-on-full-success gate :meth:`index_all` and
        :meth:`rebuild_all` both apply: a no-op sweep (every file fast-path
        skipped, zero changes) must NOT create a heartbeat snapshot, and a
        sweep containing even one failed file must stamp NOTHING — not even a
        partial snapshot for the files that DID succeed. A no-op
        :attr:`_snapshot_stamper` (the default) makes this a silent no-op,
        matching the ``code_graph``-style optional-collaborator pattern.

        Args:
            summary: The just-completed sweep's :class:`IndexSummary`.
        """
        if self._snapshot_stamper is None:
            return
        if summary.files_failed != 0 or summary.files_indexed <= 0:
            return
        await self._snapshot_stamper.stamp()


    async def rebuild_all(self, fingerprint: str) -> IndexSummary:
        """Re-embed EVERY tier from scratch and stamp the fingerprint on completion.

        Mirrors :meth:`_index_static_tier`'s purge+rewalk, but UNCONDITIONALLY for
        every effective root (live included): each tier's vectors and manifest
        rows are deleted, so the subsequent walk's ``needs_reindex`` fast-path can
        never short-circuit — every file is genuinely re-embedded (no skip).

        Crash-safety contract: the fingerprint is stamped into the manifest meta
        ONLY after ALL tiers complete successfully.  A mid-rebuild failure
        propagates WITHOUT stamping, so the next startup still detects the
        mismatch and re-triggers the rebuild (fail safe toward correctness).

        As the rebuild progresses it keeps the ``schema_rebuild_status`` meta blob
        current (``state=in_progress``, ``done``/``total`` file counts) so a
        concurrent ``index_status`` / :func:`~loremaster.index.schema.rebuilding_notice`
        reflects live progress; the state flips to ``done`` only on success.

        This method does NOT acquire any writer lock — locking is the caller's job
        (the startup ``_run_schema_rebuild`` holds the watcher's single-writer lock
        for the whole rebuild so it never races the watcher / periodic reconcile).

        A wired :attr:`_snapshot_stamper` also stamps a new snapshot generation
        on a fully-successful, genuinely-productive rebuild (see
        :meth:`_maybe_stamp_snapshot`).

        Args:
            fingerprint: The SHA-256 hex digest of the current embedding schema
                (produced by :func:`~loremaster.index.schema.embedding_schema_fingerprint`).
                Stamped into the manifest only after all tiers complete.

        Returns:
            The :class:`IndexSummary` for the full rebuild run.
        """
        roots = list(self._config.effective_roots)
        # Note: the per-tier walk (``_walk_and_index``) resets the resolution cache
        # at each tier-sweep boundary, so ``rebuild_all`` needs no extra reset here.
        # Total files to re-embed, counted up-front so the in-progress status
        # carries a meaningful progress denominator from the first update. The
        # purge below clears the manifest rows, so the count is taken before any
        # deletion (it walks the on-disk trees, independent of manifest state).
        total = sum(self._count_included_files(root) for root in roots)
        await self._write_rebuild_status(
            state=_REBUILD_STATE_IN_PROGRESS, done=0, total=total,
            fingerprint=fingerprint,
        )

        outcomes: list[IndexOutcome] = []
        rebuilt: list[str] = []
        done = 0

        async def _on_file_indexed(outcome: IndexOutcome) -> None:
            """Increment the done counter and write the in-progress status per file.

            Invoked by ``_walk_and_index`` IMMEDIATELY after each file's
            ``_index_chunks`` call completes — so ``done`` advances DURING the
            walk, not after all files finish.  This is the fix for the bug where
            ``done`` stayed 0 until ``_walk_and_index`` returned the full list.
            """
            nonlocal done
            done += 1
            # Live progress so index_status / rebuilding_notice reflect the
            # rebuild as it advances (the stamp is withheld until the end).
            await self._write_rebuild_status(
                state=_REBUILD_STATE_IN_PROGRESS, done=done, total=total,
                fingerprint=fingerprint,
            )

        for root in roots:
            # Purge this tier's vectors + manifest rows so the walk re-embeds every
            # file (the deleted rows make ``needs_reindex`` return True — no skip).
            # A static tier's snapshot is acquired first (mirrors _index_static_tier)
            # so its materialisation dir exists for the walk.
            self._acquire_static_snapshot(root)
            await self._store.delete_by_tier(root.tier)
            for stale in await self._manifest.files_for_tier(root.tier):
                await self._manifest.delete(root.tier, stale.file_path)

            base = self._tier_base(root.tier)
            assert base is not None  # every effective root resolves a base
            outcomes.extend(
                await self._walk_and_index(root, base, on_file_indexed=_on_file_indexed)
            )
            rebuilt.append(root.tier)

        # ALL tiers succeeded → stamp the fingerprint and flip the status to done.
        # Order matters: the fingerprint is the durable completion evidence; the
        # status blob is the human/agent-facing roll-up.
        await self._manifest.meta_set(SCHEMA_FINGERPRINT_META_KEY, fingerprint)
        await self._write_rebuild_status(
            state=_REBUILD_STATE_DONE, done=done, total=total, fingerprint=fingerprint,
        )
        result = self._summarize(outcomes, rebuilt=rebuilt, skipped_tiers=[])
        await self._maybe_stamp_snapshot(result)
        return result

    async def stamp_schema_fingerprint(self, fingerprint: str) -> None:
        """Stamp the embedding-schema fingerprint + mark the rebuild status done.

        The empty-index fast path the startup task takes instead of a full
        :meth:`rebuild_all`: an index with no stored vectors has nothing stale to
        re-embed, so the only work is to record that the index is now current under
        ``fingerprint``. Writes the same ``schema_rebuild_status`` ``done`` blob a
        completed rebuild leaves (no ``in_progress`` phase), so a concurrent read
        never observes a phantom rebuild for an empty index.

        Args:
            fingerprint: The current embedding-schema fingerprint to stamp.
        """
        await self._manifest.meta_set(SCHEMA_FINGERPRINT_META_KEY, fingerprint)
        await self._write_rebuild_status(
            state=_REBUILD_STATE_DONE, done=0, total=0, fingerprint=fingerprint,
        )

    async def rebuild_graph_only(self, tier: str) -> int:
        """Re-graph a tier's indexed ``.py`` files WITHOUT touching the vectors (FP-04 follow-up).

        The graph-only heal primitive: when a tier's code graph was lost but its
        vector collection is intact (the LIVE point count still agrees with the
        manifest), the graph can be rebuilt from the on-disk source ALONE — no
        re-embed, no upsert, no ``delete_by_tier`` purge of the healthy collection.
        For each INDEXED file in the tier this reads the source, ``_chunk`` it, and
        ``_refresh_graph`` it. Only ``.py`` files contribute graph nodes
        (``_refresh_graph`` no-ops every non-Python path), so a re-chunk of the whole
        tier rebuilds exactly the graph slice a full re-embed would have — at a
        fraction of the cost, since the embedding step is skipped entirely.

        Args:
            tier: The tier whose graph slice to rebuild from its indexed files.

        Returns:
            The number of graph-eligible (``.py``) indexed files re-graphed — the
            count the graph's own ``indexed_file_count`` returns after the heal.
        """
        base = self._tier_base(tier)
        if base is None:
            # A tier with no resolvable on-disk base has nothing to re-graph (no
            # source to read); nothing was lost that this primitive can restore.
            return 0
        # Sweep boundary: re-graphing a whole tier is a full sweep, so start from a
        # clean astroid cache and let it stay warm across this tier's files.
        self._reset_graph_resolution_cache()
        regraphed = 0
        for row in await self._manifest.files_for_tier(tier):
            # Only INDEXED rows represent files whose graph slice should exist; a
            # pending/failed row has no committed content to re-graph.
            if row.state != STATE_INDEXED:
                continue
            # Only Python files produce graph nodes — skip the rest so the returned
            # count matches the graph's indexed-file count (the test's oracle), and
            # so a docs file is never read needlessly.
            if not row.file_path.endswith(_PYTHON_SUFFIX):
                continue
            source = (base / row.file_path).read_text(encoding="utf-8")
            chunks = self._chunk(row.file_path, source)
            # _refresh_graph is the transactional, tier-scoped delete+rebuild of this
            # file's slice — NO embed, NO upsert, NO delete_by_tier.
            await self._refresh_graph(tier, row.file_path, chunks)
            regraphed += 1
        return regraphed

    def _acquire_static_snapshot(self, root: RootConfig) -> None:
        """Materialise a STATIC tier's snapshot before the rebuild walk (no-op for live).

        Mirrors the acquire step of :meth:`_index_static_tier` so the tier's
        materialisation dir exists for :meth:`_walk_and_index`. A live tier walks
        its on-disk path directly and needs no acquisition.

        Args:
            root: The tier's :class:`~loremaster.config.RootConfig`.
        """
        if root.watch == WATCH_LIVE:
            return
        provider = self._providers_by_tier.get(root.tier)
        if provider is None:
            raise KeyError(
                f"static tier {root.tier!r} has no registered SourceProvider"
            )
        provider.acquire(root.tier, self._snapshot_layout.snapshot_root)

    def count_files_to_rebuild(self) -> int:
        """Total files a full rebuild would re-embed across every effective root.

        The progress denominator the startup wiring stamps into the in-progress
        rebuild status BEFORE the background rebuild begins, so an immediate
        ``index_status`` reports a meaningful ``done``/``total``. Reuses the same
        per-tier walk + include predicates :meth:`rebuild_all` re-embeds against.

        Returns:
            The number of included files under every effective root.
        """
        return sum(
            self._count_included_files(root) for root in self._config.effective_roots
        )

    def _count_included_files(self, root: RootConfig) -> int:
        """Count the files a tier's walk would index (the rebuild progress denominator).

        Walks the tier's base with the SAME prune + include predicates
        :meth:`_walk_and_index` uses, so the count matches what the rebuild
        actually re-embeds. A static tier whose snapshot is not yet materialised
        contributes 0 (its files are counted once the snapshot is acquired during
        the rebuild loop — a conservative denominator, never an over-count).

        Args:
            root: The tier's :class:`~loremaster.config.RootConfig`.

        Returns:
            The number of included files under the tier's base.
        """
        base = self._tier_base(root.tier)
        if base is None or not base.exists():
            return 0
        count = 0
        for dirpath in walked_dirs(self._config, base):
            for filename in sorted(os.listdir(dirpath)):
                abs_path = Path(dirpath) / filename
                if not abs_path.is_file():
                    continue
                rel = str(PurePosixPath(abs_path.relative_to(base).as_posix()))
                if is_included(self._config, root, rel):
                    count += 1
        return count

    async def _write_rebuild_status(
        self, *, state: str, done: int, total: int, fingerprint: str
    ) -> None:
        """Write the ``schema_rebuild_status`` meta blob (the live progress surface).

        The blob shape matches exactly what ``build_app_context`` seeds and what
        ``index_status`` / :func:`~loremaster.index.schema.rebuilding_notice` read
        (clause 5: one source of truth). ``from_fingerprint`` is read back from the
        currently-stamped fingerprint so the blob always names what is being
        replaced; ``to_fingerprint`` is the target ``fingerprint``.

        Args:
            state: ``in_progress`` while running, ``done`` once complete.
            done: Files re-embedded so far.
            total: Total files to re-embed.
            fingerprint: The target fingerprint being rebuilt toward.
        """
        from_fingerprint = await self._manifest.meta_get(SCHEMA_FINGERPRINT_META_KEY)
        await self._manifest.meta_set(
            SCHEMA_REBUILD_STATUS_META_KEY,
            json.dumps(
                {
                    "state": state,
                    "done": done,
                    "total": total,
                    "reason": _REBUILD_REASON_FINGERPRINT_MISMATCH,
                    "from_fingerprint": from_fingerprint,
                    "to_fingerprint": fingerprint,
                }
            ),
        )

    async def mark_rebuild_failed(self, fingerprint: str) -> None:
        """Settle the rebuild-status meta to ``failed`` after the rebuild's work raised (FP-11).

        Called by the background rebuild task when ``rebuild_all`` (or the empty-
        index stamp) raises. Rewrites the ``schema_rebuild_status`` blob to the
        terminal :data:`_REBUILD_STATE_FAILED` state so ``index_status`` /
        ``lore_index_status`` surface a dead rebuild instead of a perpetual
        ``in_progress``. The current ``done``/``total`` progress is preserved from
        the existing blob (best effort) so the failed surface keeps a meaningful
        denominator; absent/malformed progress falls back to zero.

        Crash-safety is UNCHANGED: this writes ONLY the status blob and never the
        fingerprint stamp, so the next startup still detects the mismatch and
        re-triggers the rebuild.

        Args:
            fingerprint: The target fingerprint the failed rebuild was building
                toward (recorded as ``to_fingerprint`` in the status blob).
        """
        # Preserve whatever progress the in-progress phase reached so the failed
        # surface keeps a meaningful done/total; a missing/malformed blob → zeros.
        done = 0
        total = 0
        raw_status = await self._manifest.meta_get(SCHEMA_REBUILD_STATUS_META_KEY)
        if raw_status is not None:
            try:
                prior = json.loads(raw_status)
                if isinstance(prior, dict):
                    done = int(prior.get("done", 0))
                    total = int(prior.get("total", 0))
            except (ValueError, TypeError):
                done = 0
                total = 0
        await self._write_rebuild_status(
            state=_REBUILD_STATE_FAILED, done=done, total=total, fingerprint=fingerprint,
        )

    async def index_status(self) -> IndexSummary:
        """Return a freshness roll-up read PURELY from the manifest (zero embeds).

        Counts each file row by state across every tier — the cheap health
        surface the deploy healthcheck polls. ``outcomes`` is empty (this is a
        roll-up, not a per-file run) and the tier lists are empty (no run
        happened); the counts reflect the manifest's current state.

        Returns:
            An :class:`IndexSummary` whose counts come from the manifest.
        """
        indexed = failed = 0
        for row in await self._manifest.all_files():
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

    async def tier_version_stamp(self, tier: str) -> str | None:
        """Return the built version stamp for ``tier`` from the manifest ``meta``."""
        stamp: str | None = await self._manifest.meta_get(_tier_version_meta_key(tier))
        return stamp

    async def set_tier_version_stamp(self, tier: str, version: str) -> None:
        """Stamp ``tier``'s built version into the manifest ``meta``."""
        await self._manifest.meta_set(_tier_version_meta_key(tier), version)
