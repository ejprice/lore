"""The query-time search pipeline — the engine behind the ``search_code`` tool.

:class:`SearchPipeline` is the read side of lore. It is OOP and fully
dependency-injected (store, embedder, the composed :class:`~loremaster.server.LoreServer`
that resolves the extension hooks, the manifest, an optional
:class:`~loremaster.memory.store.MemoryStore`, and the config), so a test wires a
:class:`~loresigil.testing.FakeEmbedder` + a throwaway Qdrant collection while the
later FastMCP server wires the live deployment resources.

The pipeline (plan AMENDMENT 1, Deliverable 3 + §A1.3 seams 4/5/11 + the
read-your-writes / in-flight-freshness contract) for one
``search_code(query, k, filters, wait_for_fresh, detail_level)`` call:

1. **Embed the query** via :meth:`~loresigil.base.Embedder.embed_query`. (The
   query-vs-document asymmetric prompt the model recommends is the *embedder's*
   concern, encapsulated behind ``embed_query`` — the pipeline does not prepend a
   prefix itself.)
2. **(bounded) ``wait_for_fresh``** — when set, poll the manifest for the
   in-flight files matching the query's ``path``/``file_path`` filter until they
   reach ``indexed`` OR a hard timeout elapses. ALWAYS bounded: on timeout the
   search proceeds and serves the stale content *with a warning* — it never hangs
   (the embedder can be slow or down).
3. **Search the store** — ``store.search(vector, k, filters)`` returns the
   nearest candidate :class:`~qdrant_client.models.ScoredPoint`\\ s, optionally
   payload-filtered (tier / file_path) server-side.
4. **Extension search-pipeline hook (seam 4 / C3)** — ``augment_candidates`` (an
   extension may inject extra candidates) THEN ``rerank`` (an extension may
   reorder/rescore). Both are the identity for the bare generic server.
5. **Memory-boost (generic)** — recall project memory for the query; any
   candidate whose chunk-key is referenced by a recalled memory is boosted (its
   score lifted) and the candidates re-sorted, so a remembered correction lifts
   the right chunk above an unboosted one. A pipeline with no memory store skips
   this step.
6. **Format (seam 5)** — the extension ``format_result`` wins if it claims the
   result; otherwise the base default citation: ``[SOURCE:<file>:<line>]`` + a
   stable ``Key:`` line (the chunk key) + a fenced source block.
7. **Freshness flags** — each result whose manifest file row is ``dirty`` or
   ``embedding`` is flagged stale (the warning marker is appended to its
   ``formatted`` text); ``indexed`` chunks are never flagged. Annotate, NEVER
   blanket-block.
8. **detail_level partition (seam 11 / C2)** — ``"summary"`` keeps only
   summary-classified chunk types, ``"source"`` only source-classified,
   ``"auto"`` keeps both. The classification is the extension's ``classify_detail``
   else the base default (signatures/imports/headings ⇒ summary; bodies ⇒ source).

The return is a list of summarised :class:`SearchResult` value objects — the
filtered/formatted citations — NEVER a raw ``ScoredPoint`` dump (the Anthropic
MCP token-efficiency rule).
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict
from qdrant_client.models import ScoredPoint

from loremaster.extension import DetailLevel, ExtensionContext
from loremaster.index.manifest import STATE_INDEXED

if TYPE_CHECKING:
    from loresigil.base import Embedder

    from loremaster.config import LoreConfig
    from loremaster.index.manifest import Manifest
    from loremaster.memory.store import MemoryStore
    from loremaster.server import LoreServer
    from loremaster.store.qdrant import QdrantStore

# The detail-level selector the caller passes; ``"auto"`` keeps every level.
DetailSelector = Literal["auto", "summary", "source"]
_DETAIL_AUTO = "auto"

# The per-chunk freshness warning (plan: "⚠ re-indexing — may be stale"). A
# returned chunk whose file is in-flight is flagged with this — never blocked.
STALE_WARNING = "⚠ re-indexing — may be stale"

# Payload keys the base format / freshness / classification read. They match the
# keys ``records.chunk_to_record`` stamps into every point payload.
_PAYLOAD_FILE_PATH = "file_path"
_PAYLOAD_TIER = "tier"
_PAYLOAD_LINE_START = "line_start"
_PAYLOAD_CHUNK_TYPE = "chunk_type"
_PAYLOAD_SOURCE_TEXT = "source_text"

# The filter keys that scope the in-flight wait to a path. ``file_path`` is the
# stored payload key; ``path`` is the friendlier alias a caller may pass.
_FILTER_FILE_PATH_KEYS = ("file_path", "path")

# How much a memory reference lifts a matching candidate's score. Larger than any
# cosine gap (cosine is in [-1, 1]) so a referenced chunk reliably overtakes an
# unreferenced one regardless of the raw store ordering, while preserving the
# relative order among equally-boosted candidates.
_MEMORY_BOOST = 10.0

# Default bound on the in-flight wait, in seconds. Always finite — the wait can
# never hang (the embedder may be slow or down).
_DEFAULT_WAIT_TIMEOUT_S = 10.0

# Poll interval for the bounded in-flight wait.
_WAIT_POLL_INTERVAL_S = 0.05


class SearchResult(BaseModel):
    """A summarised search result — the filtered citation, never a raw point.

    Attributes:
        formatted: The rendered citation block — the base
            ``[SOURCE:file:line]`` + ``Key:`` + fenced source, or an extension's
            custom format; carries the stale warning appended when in-flight.
        chunk_key: The result's stable key (the extension semantic key if one
            claims it, else the structural point id) — also embedded in
            ``formatted`` so a caller can cite it.
        detail_level: The chunk's classified detail level (``summary``/``source``).
        stale: Whether the chunk's file is in-flight (``dirty``/``embedding``) in
            the manifest at query time.
        score: The (possibly memory-boosted) similarity score.
    """

    model_config = ConfigDict(extra="forbid")

    formatted: str
    chunk_key: str
    detail_level: DetailLevel
    stale: bool
    score: float


class SearchPipeline:
    """The query-time pipeline behind ``search_code`` (dependency-injected, OOP).

    Args:
        store: The :class:`~loremaster.store.qdrant.QdrantStore` to search.
        embedder: The active :class:`~loresigil.base.Embedder` (query side).
        server: The composed :class:`~loremaster.server.LoreServer`, which
            resolves the extension hooks (``augment_candidates``/``rerank``/
            ``format_result``/``classify_detail``) — identity/base for a bare
            server.
        manifest: The SQLite :class:`~loremaster.index.manifest.Manifest`, the
            authority on per-(tier, file) freshness.
        config: The validated :class:`~loremaster.config.LoreConfig`.
        extension_context: The RUNTIME :class:`~loremaster.extension.ExtensionContext`
            handed to every context-taking search seam (4/5/6/11). It carries the
            REAL shared services — the live embedder, the manifest, and the
            embedder's working ``count_tokens`` — so an extension's search hooks
            see functional resources, NOT the composition-time placeholder
            (``embedder=None``/``manifest=None``/non-counting tokenizer) that
            :meth:`~loremaster.server.LoreServer.extension_context` returns. The
            owner (``build_app_context``) constructs it over the live services and
            shares the SAME object with the startup hooks, so seam-9 ``state`` set
            at startup is visible to the search seams.
        memory_store: Optional :class:`~loremaster.memory.store.MemoryStore` for
            the memory-boost step; ``None`` disables it (the generic, no-memory
            deploy).
    """

    def __init__(
        self,
        *,
        store: QdrantStore,
        embedder: Embedder,
        server: LoreServer,
        manifest: Manifest,
        config: LoreConfig,
        extension_context: ExtensionContext,
        memory_store: MemoryStore | None = None,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._server = server
        self._manifest = manifest
        self._config = config
        self._extension_context = extension_context
        self._memory_store = memory_store

    async def search_code(
        self,
        query: str,
        k: int,
        filters: dict[str, str] | None = None,
        *,
        wait_for_fresh: bool = False,
        detail_level: str = _DETAIL_AUTO,
        wait_timeout_s: float = _DEFAULT_WAIT_TIMEOUT_S,
    ) -> list[SearchResult]:
        """Run the full query-time pipeline and return summarised results.

        Args:
            query: The natural-language search query.
            k: The maximum number of candidates to retrieve from the store.
            filters: Optional payload keyword filters (e.g. ``{"tier": ...}`` or
                ``{"file_path": ...}``), applied server-side.  The public alias
                ``"path"`` is accepted and translated to the canonical
                ``"file_path"`` payload key before the store query.
            wait_for_fresh: When ``True``, bounded-wait for in-flight files
                matching the query's path filter to reach ``indexed`` before
                searching; on timeout, serve stale-with-warning (never hang).
            detail_level: ``"auto"`` (both), ``"summary"``, or ``"source"`` — the
                detail-level partition applied to the formatted results.
            wait_timeout_s: The hard ceiling on the ``wait_for_fresh`` poll.

        Returns:
            The summarised :class:`SearchResult` list (filtered + formatted),
            never a raw :class:`~qdrant_client.models.ScoredPoint` dump.
        """
        ctx = self._extension_context

        if wait_for_fresh:
            await self._wait_for_fresh(filters, wait_timeout_s)

        vector = await self._embedder.embed_query(query)
        # Translate the public ``path`` alias to the canonical ``file_path``
        # payload key BEFORE the store query so Qdrant's _build_filter sees the
        # real field name (no point has a ``path`` payload field).
        candidates = await self._store.search(vector, k, self._normalize_filters(filters))

        # Seam 4 (C3): extension candidate-augmentation then rerank (identity for
        # the bare generic server).
        candidates = self._server.augment_candidates(query, candidates, ctx)
        candidates = self._server.rerank(candidates, ctx)

        # Memory-boost (generic) — lift candidates a recalled memory references.
        candidates = await self._apply_memory_boost(query, candidates, ctx)

        results = [self._to_result(point, ctx) for point in candidates]
        return self._partition_by_detail(results, detail_level)

    # -- filter normalisation ---------------------------------------------------

    @staticmethod
    def _normalize_filters(
        filters: dict[str, str] | None,
    ) -> dict[str, str] | None:
        """Translate the public ``path`` alias to the canonical ``file_path`` key.

        The store's ``_build_filter`` uses dict keys verbatim as Qdrant payload
        field names, and no point carries a ``path`` field — only ``file_path``.
        This helper returns a new dict with the alias translated so callers can
        use either spelling without silently matching nothing.

        Precedence: if BOTH ``path`` and ``file_path`` are present the explicit
        canonical ``file_path`` wins and the alias is dropped. All other keys
        (e.g. ``tier``) pass through untouched. A ``None`` or empty dict is
        returned unchanged.

        The canonical target is :data:`_PAYLOAD_FILE_PATH` — the field name
        ``records.chunk_to_record`` actually stamps into every point — so the
        translation is decoupled from the ORDER of :data:`_FILTER_FILE_PATH_KEYS`
        (reordering that tuple, e.g. to surface ``path`` first, cannot silently
        reintroduce the bug). The alias set is every recognised path-filter key
        except the canonical one, keeping a single constant authoritative for
        both the wait-scoping path (``_path_filter``) and this store-query path.
        """
        if not filters:
            return filters

        # The canonical payload field (what the indexer stamps); everything else
        # in the recognised path-filter key set is an alias.  Aliases never reach
        # the store — only the canonical field name does.
        canonical = _PAYLOAD_FILE_PATH
        aliases = {key for key in _FILTER_FILE_PATH_KEYS if key != canonical}

        # Fast path: nothing to do when no alias key is present.
        if not aliases.intersection(filters):
            return filters

        normalised: dict[str, str] = {}
        for key, value in filters.items():
            if key in aliases:
                # Translate alias → canonical, but only when the caller did NOT
                # also supply the canonical key explicitly (canonical wins).
                if canonical not in filters:
                    normalised[canonical] = value
                # else: drop the alias — the explicit canonical key takes precedence.
            else:
                normalised[key] = value
        return normalised

    # -- step 2: bounded read-your-writes wait ------------------------------

    async def _wait_for_fresh(
        self, filters: dict[str, str] | None, timeout_s: float
    ) -> None:
        """Bounded-wait for the path-filtered in-flight files to reach ``indexed``.

        Polls the manifest for the file(s) named by the query's
        ``file_path``/``path`` filter until every such row is ``indexed`` OR the
        timeout elapses, whichever comes first. ALWAYS returns within
        ``timeout_s`` — a file that never settles (slow/down embedder) is served
        stale-with-warning rather than hanging the search. With no path filter
        there is no single file to wait on, so this returns at once (the freshness
        flags still annotate any in-flight chunk that surfaces).
        """
        file_path = self._path_filter(filters)
        if file_path is None:
            return
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self._all_rows_indexed_for_path(file_path):
                return
            await asyncio.sleep(_WAIT_POLL_INTERVAL_S)

    @staticmethod
    def _path_filter(filters: dict[str, str] | None) -> str | None:
        """Extract the path the wait should scope to from the filters, or ``None``."""
        if not filters:
            return None
        for key in _FILTER_FILE_PATH_KEYS:
            if key in filters:
                return filters[key]
        return None

    def _all_rows_indexed_for_path(self, file_path: str) -> bool:
        """True iff every manifest row for ``file_path`` (any tier) is ``indexed``.

        A path may exist under multiple tiers (C1); a wait is satisfied only when
        no copy is still in-flight. An absent path (no rows) is vacuously settled.
        """
        rows = [row for row in self._manifest.all_files() if row.file_path == file_path]
        return all(row.state == STATE_INDEXED for row in rows)

    # -- step 5: memory-boost -----------------------------------------------

    async def _apply_memory_boost(
        self, query: str, candidates: list[ScoredPoint], ctx: ExtensionContext
    ) -> list[ScoredPoint]:
        """Boost candidates a recalled memory references, then re-sort by score.

        Recalls project memory for ``query``; collects the set of chunk-keys those
        memories reference; any candidate whose key is in that set has its score
        lifted by :data:`_MEMORY_BOOST` (enough to overtake an unboosted chunk the
        bare store ranked higher) and the candidates are re-sorted descending. A
        pipeline with no memory store returns the candidates unchanged.
        """
        if self._memory_store is None:
            return candidates
        recalled = await self._memory_store.recall_memory(query)
        referenced_keys = {
            ref.chunk_key for memory in recalled for ref in memory.refs
        }
        if not referenced_keys:
            return candidates

        boosted: list[ScoredPoint] = []
        for point in candidates:
            if self._chunk_key(point, ctx) in referenced_keys:
                # model_copy so the boost never mutates the store's returned point.
                boosted.append(point.model_copy(update={"score": point.score + _MEMORY_BOOST}))
            else:
                boosted.append(point)
        boosted.sort(key=lambda p: p.score, reverse=True)
        return boosted

    # -- steps 6 + 7 + key: per-result formatting ---------------------------

    def _to_result(self, point: ScoredPoint, ctx: ExtensionContext) -> SearchResult:
        """Format one candidate, flag freshness, and classify its detail level."""
        payload = point.payload or {}
        key = self._chunk_key(point, ctx)
        stale = self._is_stale(payload)
        detail = self._server.classify_detail(payload.get(_PAYLOAD_CHUNK_TYPE, "")) or "source"

        formatted = self._server.format_result(point, ctx)
        if formatted is None:
            formatted = self._base_format(payload, key)
        if stale:
            formatted = f"{formatted}\n{STALE_WARNING}"

        return SearchResult(
            formatted=formatted,
            chunk_key=key,
            detail_level=detail,
            stale=stale,
            score=point.score,
        )

    def _chunk_key(self, point: ScoredPoint, ctx: ExtensionContext) -> str:
        """The result's stable key — the extension semantic key, else the point id.

        Seam 6: an extension may supply a versioned semantic key for a payload;
        when none claims it, the structural point id (``records.point_id``) is the
        key. Carried on every result so a caller can cite it and a memory ref can
        match it.
        """
        payload = point.payload or {}
        key = self._server.chunk_key(payload, ctx)
        return key if key is not None else str(point.id)

    @staticmethod
    def _base_format(payload: dict[str, Any], key: str) -> str:
        """The base default citation: ``[SOURCE:file:line]`` + ``Key:`` + fenced source.

        The single base citation when no extension claims seam 5. The file path and
        line come from the stored payload (the indexer stamps them); the fenced
        block wraps the chunk's verbatim ``source_text``.
        """
        file_path = payload.get(_PAYLOAD_FILE_PATH, "")
        line_start = payload.get(_PAYLOAD_LINE_START, 0)
        source_text = payload.get(_PAYLOAD_SOURCE_TEXT, "")
        return (
            f"[SOURCE:{file_path}:{line_start}]\n"
            f"Key: {key}\n"
            f"```\n{source_text}\n```"
        )

    def _is_stale(self, payload: dict[str, Any]) -> bool:
        """True iff the chunk's manifest file row is in-flight (not ``indexed``).

        The manifest — not Qdrant — is the freshness authority. A row absent from
        the manifest is treated as settled (nothing in-flight to warn about).
        """
        tier = payload.get(_PAYLOAD_TIER, "")
        file_path = payload.get(_PAYLOAD_FILE_PATH, "")
        row = self._manifest.get(tier, file_path)
        if row is None:
            return False
        return row.state != STATE_INDEXED

    # -- step 8: detail-level partition -------------------------------------

    @staticmethod
    def _partition_by_detail(
        results: list[SearchResult], detail_level: str
    ) -> list[SearchResult]:
        """Keep only the results matching the requested detail level (``auto`` = all)."""
        if detail_level == _DETAIL_AUTO:
            return results
        return [r for r in results if r.detail_level == detail_level]
