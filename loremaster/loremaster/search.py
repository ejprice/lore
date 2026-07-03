"""The query-time search pipeline — the engine behind the ``search_code`` tool.

:class:`SearchPipeline` is the read side of lore. It is OOP and fully
dependency-injected (the unified SurrealDB store, the embedder, the composed
:class:`~loremaster.server.LoreServer` that resolves the extension hooks, the
manifest, the code graph, an optional
:class:`~loremaster.memory.store.MemoryStore`, an optional config-gated reranker
seam, and the config), so a test wires the in-memory
:func:`~_surreal_fakes.fake_surreal_trio` + a :class:`~loresigil.testing.FakeEmbedder`
while the live server wires the deployed SurrealDB / embedder resources.

**P6 read-path cutover (plan §6).** The pipeline reads from the unified store's
:meth:`~loremaster.store.surreal.SurrealStore.hybrid_search` (an HNSW vector arm
⊕ a BM25 FULLTEXT arm fused with Reciprocal Rank Fusion), which returns
backend-neutral :class:`~loremaster.store.candidate.Candidate`\\ s (``key`` = bare
uuid5, ``score`` = RRF-scale < 1.0, ``payload`` = the flattened canonical chunk
fields incl. the chunker's ``signature``) — never a ``qdrant_client``
``ScoredPoint``. The read result is a list of summarised :class:`SearchResult`
value objects, never a raw candidate dump (the Anthropic token-efficiency rule).

The v2 pipeline for one ``search_code(query, k, filters, wait_for_fresh,
detail_level)`` call:

1. **(bounded) ``wait_for_fresh``** — when set, poll the manifest for the
   in-flight files matching the query's ``path``/``file_path`` filter until they
   reach ``indexed`` OR a hard timeout elapses. ALWAYS bounded: on timeout the
   search proceeds and serves the stale content *with a warning* — it never hangs
   (the embedder can be slow or down).
2. **Embed the query** via :meth:`~loresigil.base.Embedder.embed_query` for the
   HNSW arm; the RAW query text is forwarded UNCHANGED for the BM25 arm (dropping
   it, or sending the vector/prompt text, is the classic seam bug this closes).
3. **Hybrid search** — ``store.hybrid_search(query_vector, query_text, k,
   filters)`` returns the RRF-fused :class:`Candidate`\\ s, optionally
   payload-filtered (tier / file_path) server-side. A down store RAISES here
   (never a silent ``[]``); the public ``path`` alias is translated to the
   canonical ``file_path`` before the query.
4. **Extension search-pipeline hook (seam 4 / C3)** — ``augment_candidates`` (an
   extension may inject extra candidates) THEN ``rerank`` (an extension may
   reorder/rescore). Both are the identity for the bare generic server.
5. **Memory (generic)** — recall project memory once, then (a) *boost*: any
   candidate a recalled memory references is lifted by :data:`_MEMORY_BOOST` (an
   RRF-scale-aware constant, so a remembered correction reliably overtakes an
   unboosted hit) and the candidates re-sorted; and (b) *inject*: the ≤
   :data:`_MEMORY_INJECTION_CAP` top-scored recalled memories are rendered as
   VISIBLE, provenance-stamped entries that LEAD the result list — distinct from
   the silent boost, and NEVER masquerading as source citations. No memory store
   ⇒ both are inert.
6. **Config-gated reranker seam (item 9)** — when ``search.reranker`` is
   configured AND a reranker seam object is injected, the candidates pass through
   it AFTER RRF fusion and BEFORE formatting. Config, not the mere presence of the
   seam object, is the gate.
7. **Format (seam 5) + graph enrichment + freshness** — the extension
   ``format_result`` wins if it claims the result; otherwise the base default
   citation: ``[SOURCE:<file>:<line>]`` + a stable ``Key:`` line + the v2 short
   citation ``[S:<tier>:<path>:<start>-<end>@<hash6>]`` + a fenced source block.
   A function/method hit (non-``None`` ``signature``) additionally carries its
   ref-join line (``← N prod / M test · tests: K`` from the code graph) + its
   signature — enrichment is CAPPED at :data:`_ENRICHMENT_CAP` graph joins (the
   top hits by score), and a graph that raises mid-enrichment still returns the
   hit, annotated with :data:`_ENRICHMENT_UNAVAILABLE`. Each in-flight
   (``dirty``/``embedding``) chunk is flagged stale (annotate, NEVER block). All
   non-fenced rendered fields (identities / paths / memory lines) are
   render-sanitised so control chars / newlines cannot break a citation line or
   escape a fence.
8. **detail_level partition (seam 11 / C2)** — ``"summary"`` keeps only
   summary-classified hits, ``"source"`` only source-classified, ``"auto"`` keeps
   both. Injected memory entries are NOT partitioned — they always lead.

The return is a list of summarised :class:`SearchResult` value objects.
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import TYPE_CHECKING, Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict

from loremaster.extension import DetailLevel, ExtensionContext
from loremaster.index.manifest import STATE_INDEXED
from loremaster.store.candidate import Candidate

if TYPE_CHECKING:
    from loresigil.base import Embedder

    from loremaster.config import LoreConfig
    from loremaster.graph_surreal import SurrealCodeGraph
    from loremaster.index.surreal_manifest import SurrealManifest
    from loremaster.memory.store import MemoryStore, RecalledMemory
    from loremaster.server import LoreServer
    from loremaster.store.surreal import SurrealStore

# The detail-level selector the caller passes; ``"auto"`` keeps every level.
DetailSelector = Literal["auto", "summary", "source"]
_DETAIL_AUTO = "auto"

# The discriminator on every :class:`SearchResult`: a real code hit vs a visible,
# provenance-stamped injected memory line (item 5). The two must be tellable apart
# so an agent never mistakes response-level guidance for a cited source span.
ResultKind = Literal["hit", "memory"]
HIT_KIND: ResultKind = "hit"
MEMORY_KIND: ResultKind = "memory"

# The per-chunk freshness warning (plan: "⚠ re-indexing — may be stale"). A
# returned chunk whose file is in-flight is flagged with this — never blocked.
STALE_WARNING = "⚠ re-indexing — may be stale"

# Payload keys the base format / freshness / classification / enrichment read.
# They match the keys ``records.chunk_to_record`` stamps into every point payload.
_PAYLOAD_FILE_PATH = "file_path"
_PAYLOAD_TIER = "tier"
_PAYLOAD_LINE_START = "line_start"
_PAYLOAD_LINE_END = "line_end"
_PAYLOAD_CHUNK_TYPE = "chunk_type"
_PAYLOAD_SOURCE_TEXT = "source_text"
_PAYLOAD_CONTENT_HASH = "content_hash"
_PAYLOAD_IDENTITY = "identity"
# The chunker stamps ``signature`` (a rendered ``(params) -> ret`` string) on
# function/method chunks and ``None`` on everything else — so a non-``None`` str
# here is exactly "this hit is a callable worth a graph ref-join" (item 7).
_PAYLOAD_SIGNATURE = "signature"

# The filter keys that scope the in-flight wait to a path. ``file_path`` is the
# stored payload key; ``path`` is the friendlier alias a caller may pass.
_FILTER_FILE_PATH_KEYS = ("file_path", "path")

# How much a memory reference lifts a matching candidate's score (item 4). The
# store's fused RRF scores are strictly < 1.0 (rank-1/rank-1 tops out well below
# it — see :class:`~loremaster.store.candidate.Candidate`), so a boost of one full
# unit guarantees a referenced hit overtakes ANY unreferenced one regardless of
# the raw fused ordering, while a stable sort preserves the relative order among
# equally-boosted candidates. (Re-grounded on the RRF scale — the pre-P6 value was
# sized for a cosine gap, an order of magnitude the fused score never reaches.)
_MEMORY_BOOST = 1.0

# item 5: at most this many recalled memories are injected as visible entries,
# highest-score first — a deterministic cap so a noisy recall can never flood the
# response with guidance lines.
_MEMORY_INJECTION_CAP = 2

# item 5: the provenance marker that stamps an injected memory line (so it is
# tellable apart from a real citation) and the (overview) detail level such an
# entry carries — memory guidance is response-level, never a source body.
_MEMORY_MARKER = "[MEMORY]"
_MEMORY_DETAIL_LEVEL: DetailLevel = "summary"

# item 6: the v2 short-citation grammar. Full form
# ``[S:<tier>:<file_path>:<line_start>-<line_end>@<hash6>]``; ``hash6`` is the
# first six hex of the chunk's file content hash. Coexists with the kept
# ``[SOURCE:file:line]`` grammar — it does NOT replace or shorten ``chunk_key``.
_SHORT_CITATION_PREFIX = "[S:"
_SHORT_HASH_LEN = 6

# item 7: the per-hit graph ref-join line ``← N prod / M test · tests: K`` — N/M
# from ``graph.references`` (production/test split), K from ``graph.tests_for``.
_ENRICHMENT_ARROW = "←"  # "←"
_ENRICHMENT_MIDDOT = "·"  # "·"
# item 7: the maximum number of hits enriched per response (a bounded graph-join
# fan-out). A wide result set never issues one graph round-trip per hit — only the
# top ``_ENRICHMENT_CAP`` by score are joined.
_ENRICHMENT_CAP = 10
# item 7: the explicit marker annotating a hit whose enrichment could not be
# computed (the graph raised mid-enrichment) — annotate the hit, never blanket-fail.
_ENRICHMENT_UNAVAILABLE = "⚠ enrichment unavailable"  # "⚠ enrichment unavailable"

# item 10: the CommonMark backtick fence character, and the standard minimum fence
# width. The wrapper fence must be a backtick run LONGER than any run inside the
# source (so a ``` embedded in the source cannot close the fence early), bounded
# below by the three-backtick CommonMark minimum.
_FENCE_CHAR = "`"
_MIN_FENCE_WIDTH = 3

# item 10: the render-sanitiser's control-char class — C0 controls (incl. TAB,
# LF, CR, the ANSI/OSC introducer ESC ``\x1b`` and its BEL terminator ``\x07``),
# DEL, and the C1 controls. A run of these collapses to a single space so a hostile
# identity/path stays one logical line and cannot smuggle terminal-framing or a
# fake second citation into a rendered field.
_CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x1f\x7f-\x9f]+")
# item 10: matches a run of consecutive backticks, for sizing the wrapper fence.
_BACKTICK_RUN_PATTERN = re.compile(r"`+")

# Default bound on the in-flight wait, in seconds. Always finite — the wait can
# never hang (the embedder may be slow or down).
_DEFAULT_WAIT_TIMEOUT_S = 10.0

# Poll interval for the bounded in-flight wait.
_WAIT_POLL_INTERVAL_S = 0.05


def _sanitise_line(text: str) -> str:
    """Collapse control chars / newlines in a NON-fenced rendered field (item 10).

    Any run of control characters (:data:`_CONTROL_CHAR_PATTERN` — C0/C1 controls,
    DEL, incl. an ANSI/OSC ``ESC`` introducer and a newline) becomes a single
    space, and leading/trailing whitespace is stripped, so the field renders as a
    single logical line that cannot break the citation line it sits on or escape a
    fence. Source *bodies* are NOT run through this — they stay verbatim inside a
    backtick fence.
    """
    return _CONTROL_CHAR_PATTERN.sub(" ", text).strip()


def _max_backtick_run(text: str) -> int:
    """The length of the longest run of consecutive backticks anywhere in ``text``."""
    return max((len(run) for run in _BACKTICK_RUN_PATTERN.findall(text)), default=0)


def _refjoin_line(production_references: int, test_references: int, covering_tests: int) -> str:
    """Render the item-7 ref-join line ``← N prod / M test · tests: K``.

    The counts are forwarded verbatim from the code graph (``references`` split
    production/test, ``tests_for`` covering-node count); this is the single place
    the exact ref-join grammar is composed.
    """
    return (
        f"{_ENRICHMENT_ARROW} {production_references} prod / {test_references} test "
        f"{_ENRICHMENT_MIDDOT} tests: {covering_tests}"
    )


class _Reranker(Protocol):
    """The config-gated cross-encoder reranker seam (item 9) — interface only.

    P6 ships no live reranker client; the pipeline calls this seam ONLY when
    ``config.search.reranker`` is set, passing the RRF-fused candidates through
    after fusion and before formatting.
    """

    async def rerank(
        self, query: str, candidates: list[Candidate], ctx: ExtensionContext
    ) -> list[Candidate]:
        """Re-score/reorder ``candidates`` for ``query`` and return them."""
        ...


class SearchResult(BaseModel):
    """A summarised search result — a formatted citation or an injected memory line.

    Attributes:
        formatted: The rendered block — for a ``hit``, the base
            ``[SOURCE:file:line]`` + ``Key:`` + short ``[S:…]`` citation + fenced
            source (or an extension's custom format), plus any graph ref-join /
            signature / stale warning; for a ``memory`` entry, the sanitised,
            provenance-stamped memory line.
        chunk_key: The result's stable key — the extension semantic key if one
            claims it, else the structural bare-uuid5 point id; empty for an
            injected memory entry (a memory is not a cited chunk).
        detail_level: The chunk's classified detail level (``summary``/``source``).
        stale: Whether the chunk's file is in-flight (``dirty``/``embedding``) in
            the manifest at query time (always ``False`` for a memory entry).
        score: The (possibly memory-boosted) fusion score, or the memory's recall
            score for a ``memory`` entry.
        kind: ``"hit"`` (a real code citation) or ``"memory"`` (an injected,
            provenance-stamped project-memory line) — see :data:`ResultKind`.
    """

    model_config = ConfigDict(extra="forbid")

    formatted: str
    chunk_key: str
    detail_level: DetailLevel
    stale: bool
    score: float
    kind: ResultKind = HIT_KIND


class SearchPipeline:
    """The query-time pipeline behind ``search_code`` (dependency-injected, OOP).

    Args:
        store: The unified :class:`~loremaster.store.surreal.SurrealStore` — the
            read path is its ``hybrid_search`` (HNSW ⊕ BM25 via RRF).
        embedder: The active :class:`~loresigil.base.Embedder` (query side).
        server: The composed :class:`~loremaster.server.LoreServer`, which
            resolves the extension hooks (``augment_candidates``/``rerank``/
            ``format_result``/``chunk_key``/``classify_detail``) — identity/base
            for a bare server.
        manifest: The :class:`~loremaster.index.surreal_manifest.SurrealManifest`,
            the authority on per-(tier, file) freshness.
        config: The validated :class:`~loremaster.config.LoreConfig` — its
            ``search.reranker`` block gates the reranker seam (item 9).
        extension_context: The RUNTIME :class:`~loremaster.extension.ExtensionContext`
            handed to every context-taking search seam (4/5/6/11). It carries the
            REAL shared services — the live embedder, the manifest, and the
            embedder's working ``count_tokens`` — so an extension's search hooks
            see functional resources, NOT the composition-time placeholder the
            server's :meth:`~loremaster.server.LoreServer.extension_context`
            returns. The owner (``build_app_context``) constructs it over the live
            services and shares the SAME object with the startup hooks, so seam-9
            ``state`` set at startup is visible to the search seams.
        code_graph: The :class:`~loremaster.graph_surreal.SurrealCodeGraph` the
            per-hit ref-join enrichment (item 7) joins against.
        memory_store: Optional :class:`~loremaster.memory.store.MemoryStore` for
            the memory boost + visible injection; ``None`` disables both (the
            generic, no-memory deploy).
        reranker: Optional config-gated cross-encoder reranker seam (item 9);
            called ONLY when ``config.search.reranker`` is set.
    """

    def __init__(
        self,
        *,
        store: SurrealStore,
        embedder: Embedder,
        server: LoreServer,
        manifest: SurrealManifest,
        config: LoreConfig,
        extension_context: ExtensionContext,
        code_graph: SurrealCodeGraph,
        memory_store: MemoryStore | None = None,
        reranker: _Reranker | None = None,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._server = server
        self._manifest = manifest
        self._config = config
        self._extension_context = extension_context
        self._code_graph = code_graph
        self._memory_store = memory_store
        self._reranker = reranker

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
                ``{"file_path": ...}``), applied server-side in BOTH fused arms.
                The public alias ``"path"`` is translated to the canonical
                ``"file_path"`` payload key before the store query.
            wait_for_fresh: When ``True``, bounded-wait for in-flight files
                matching the query's path filter to reach ``indexed`` before
                searching; on timeout, serve stale-with-warning (never hang).
            detail_level: ``"auto"`` (both), ``"summary"``, or ``"source"`` — the
                detail-level partition applied to the code hits (injected memory
                entries always lead and are never partitioned).
            wait_timeout_s: The hard ceiling on the ``wait_for_fresh`` poll.

        Returns:
            The summarised :class:`SearchResult` list — injected memory entries
            first, then the ranked, formatted code hits — never a raw
            :class:`~loremaster.store.candidate.Candidate` dump.
        """
        ctx = self._extension_context

        # Step 1: bounded read-your-writes wait (never hangs).
        if wait_for_fresh:
            await self._wait_for_fresh(filters, wait_timeout_s)

        # Steps 2 + 3: embed for the vector arm, forward the RAW text for the BM25
        # arm, and fetch the RRF-fused candidates (a down store RAISES here).
        vector = await self._embedder.embed_query(query)
        candidates = await self._store.hybrid_search(
            query_vector=vector,
            query_text=query,
            k=k,
            filters=self._normalize_filters(filters),
        )

        # Step 4 (seam 4 / C3): extension candidate-augmentation then rerank
        # (identity for the bare generic server).
        candidates = self._server.augment_candidates(query, candidates, ctx)
        candidates = self._server.rerank(candidates, ctx)

        # Step 5: recall project memory ONCE, then boost referenced candidates and
        # (below, after formatting) inject the visible memory entries.
        recalled = await self._recall_memory(query)
        candidates = self._apply_memory_boost(candidates, recalled, ctx)

        # Step 6 (item 9): config-gated reranker seam (post-RRF, pre-format).
        candidates = await self._maybe_rerank(query, candidates, ctx)

        # Step 7: format each candidate (base/extension citation + capped graph
        # enrichment + freshness flag).
        enrichment_targets = self._select_enrichment_targets(candidates)
        hits = [
            await self._to_result(candidate, ctx, enrich=candidate.key in enrichment_targets)
            for candidate in candidates
        ]

        # Step 8: partition the HITS by detail level, then prepend the visible
        # memory entries (they lead the response and are never partitioned).
        partitioned_hits = self._partition_by_detail(hits, detail_level)
        memory_entries = self._inject_memories(recalled)
        return [*memory_entries, *partitioned_hits]

    # -- filter normalisation ---------------------------------------------------

    @staticmethod
    def _normalize_filters(
        filters: dict[str, str] | None,
    ) -> dict[str, str] | None:
        """Translate the public ``path`` alias to the canonical ``file_path`` key.

        The store's filter allow-list uses dict keys verbatim as payload field
        names, and no chunk carries a ``path`` field — only ``file_path``. This
        helper returns a new dict with the alias translated so callers can use
        either spelling without silently matching nothing.

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

    # -- step 1: bounded read-your-writes wait ------------------------------

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
            if await self._all_rows_indexed_for_path(file_path):
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

    async def _all_rows_indexed_for_path(self, file_path: str) -> bool:
        """True iff every manifest row for ``file_path`` (any tier) is ``indexed``.

        A path may exist under multiple tiers (C1); a wait is satisfied only when
        no copy is still in-flight. An absent path (no rows) is vacuously settled.
        """
        rows = [row for row in await self._manifest.all_files() if row.file_path == file_path]
        return all(row.state == STATE_INDEXED for row in rows)

    # -- step 5: memory recall / boost / visible injection ------------------

    async def _recall_memory(self, query: str) -> list[RecalledMemory]:
        """Recall project memory for ``query`` once (``[]`` with no memory store).

        A single recall drives BOTH the silent score-boost and the visible
        injection, so the two never double-query the memory collection.
        """
        if self._memory_store is None:
            return []
        return list(await self._memory_store.recall_memory(query))

    def _apply_memory_boost(
        self,
        candidates: list[Candidate],
        recalled: list[RecalledMemory],
        ctx: ExtensionContext,
    ) -> list[Candidate]:
        """Boost candidates a recalled memory references, then re-sort by score.

        Collects the chunk-keys the recalled memories reference; any candidate
        whose key is in that set has its score lifted by :data:`_MEMORY_BOOST`
        (enough — on the RRF scale — to overtake an unboosted chunk the store
        ranked higher) and the candidates are re-sorted descending. The lift uses
        :meth:`~loremaster.store.candidate.Candidate.model_copy` so the boost never
        mutates the store's returned candidate. Empty recall ⇒ unchanged.
        """
        referenced_keys = {ref.chunk_key for memory in recalled for ref in memory.refs}
        if not referenced_keys:
            return candidates

        boosted: list[Candidate] = []
        for candidate in candidates:
            if self._chunk_key(candidate, ctx) in referenced_keys:
                # model_copy so the boost never mutates the store's returned candidate.
                boosted.append(
                    candidate.model_copy(update={"score": candidate.score + _MEMORY_BOOST})
                )
            else:
                boosted.append(candidate)
        # Stable sort: equally-boosted candidates keep their incoming relative order.
        boosted.sort(key=lambda candidate: candidate.score, reverse=True)
        return boosted

    def _inject_memories(self, recalled: list[RecalledMemory]) -> list[SearchResult]:
        """Render the ≤ cap top-scored recalled memories as visible entries (item 5).

        The injected entries LEAD the result list, are provenance-stamped (so they
        never masquerade as a source citation), and are capped at
        :data:`_MEMORY_INJECTION_CAP` by descending score. Empty recall ⇒ nothing.
        """
        if not recalled:
            return []
        top = sorted(recalled, key=lambda memory: memory.score, reverse=True)
        return [self._memory_result(memory) for memory in top[:_MEMORY_INJECTION_CAP]]

    @staticmethod
    def _memory_result(memory: RecalledMemory) -> SearchResult:
        """Build one provenance-stamped, sanitised memory :class:`SearchResult`.

        The line carries the :data:`_MEMORY_MARKER`, the memory text, and its refs'
        keys — and is render-sanitised to a single logical line (item 10) so a
        hostile memory text cannot smuggle framing or a fake extra result. It
        deliberately carries NEITHER citation grammar, so it is never mistaken for
        a cited source span.
        """
        ref_keys = ", ".join(ref.chunk_key for ref in memory.refs)
        line = _sanitise_line(f"{_MEMORY_MARKER} {memory.text} (refs: {ref_keys})")
        return SearchResult(
            formatted=line,
            chunk_key="",  # a memory is provenance, not a cited chunk
            detail_level=_MEMORY_DETAIL_LEVEL,
            stale=False,
            score=memory.score,
            kind=MEMORY_KIND,
        )

    # -- step 6: config-gated reranker seam ---------------------------------

    async def _maybe_rerank(
        self, query: str, candidates: list[Candidate], ctx: ExtensionContext
    ) -> list[Candidate]:
        """Route candidates through the reranker seam iff CONFIG enables it (item 9).

        The gate is ``config.search.reranker`` — NOT the mere presence of the
        injected seam object. With the reranker unconfigured the seam is provably
        never called (an injected reranker double stays inert).
        """
        if self._config.search.reranker is None or self._reranker is None:
            return candidates
        return await self._reranker.rerank(query, candidates, ctx)

    # -- step 7: per-hit graph enrichment (capped) --------------------------

    @staticmethod
    def _select_enrichment_targets(candidates: list[Candidate]) -> set[str]:
        """The keys of the hits to graph-enrich — the top ``_ENRICHMENT_CAP`` by score.

        Only a function/method hit (a non-``None`` string ``signature``) is a
        candidate for a ref-join; of those, the top :data:`_ENRICHMENT_CAP` by
        score are selected so a wide result set never fans out one graph
        round-trip per hit. Ties break on ascending key (deterministic).
        """
        symbol_hits = [
            candidate
            for candidate in candidates
            if isinstance(candidate.payload.get(_PAYLOAD_SIGNATURE), str)
        ]
        ranked = sorted(symbol_hits, key=lambda candidate: (-candidate.score, candidate.key))
        return {candidate.key for candidate in ranked[:_ENRICHMENT_CAP]}

    async def _enrichment_lines(self, payload: dict[str, Any]) -> list[str]:
        """The ref-join + signature lines for one symbol hit (item 7), fail-soft.

        Joins the code graph on the chunk's ``identity``: ``references`` gives the
        production/test split, ``tests_for`` the covering-test count. A graph that
        raises mid-enrichment yields the single :data:`_ENRICHMENT_UNAVAILABLE`
        marker line instead of dropping the hit or failing the whole search.
        """
        symbol = str(payload.get(_PAYLOAD_IDENTITY, ""))
        signature = payload.get(_PAYLOAD_SIGNATURE)
        try:
            summary = await self._code_graph.references(symbol)
            covering = await self._code_graph.tests_for(symbol)
        except Exception:
            # Annotate, never blanket-fail: the hit is still cited, its enrichment
            # explicitly marked unavailable (a mid-enrichment graph outage).
            return [_sanitise_line(_ENRICHMENT_UNAVAILABLE)]
        refjoin = _refjoin_line(
            summary.production_references, summary.test_references, len(covering)
        )
        return [_sanitise_line(refjoin), _sanitise_line(str(signature))]

    # -- step 7: per-result formatting --------------------------------------

    async def _to_result(
        self, candidate: Candidate, ctx: ExtensionContext, *, enrich: bool
    ) -> SearchResult:
        """Format one candidate, enrich it, flag freshness, classify its detail."""
        payload = candidate.payload
        key = self._chunk_key(candidate, ctx)
        stale = await self._is_stale(payload)
        detail = self._server.classify_detail(payload.get(_PAYLOAD_CHUNK_TYPE, "")) or "source"

        enrichment_lines = await self._enrichment_lines(payload) if enrich else []

        # Seam 5: an extension's custom format wins; otherwise the base citation
        # (which folds the enrichment lines in BEFORE its fenced source block).
        core = self._server.format_result(candidate, ctx)
        if core is None:
            formatted = self._base_format(payload, key, enrichment_lines)
        else:
            formatted = core
            if enrichment_lines:
                formatted = f"{formatted}\n" + "\n".join(enrichment_lines)
        if stale:
            formatted = f"{formatted}\n{STALE_WARNING}"

        return SearchResult(
            formatted=formatted,
            chunk_key=key,
            detail_level=detail,
            stale=stale,
            score=candidate.score,
            kind=HIT_KIND,
        )

    def _chunk_key(self, candidate: Candidate, ctx: ExtensionContext) -> str:
        """The result's stable key — the extension semantic key, else the point id.

        Seam 6: an extension may supply a versioned semantic key for a payload;
        when none claims it, the candidate's bare-uuid5 key (``records.point_id``)
        is the key. Carried on every result so a caller can cite it and a memory
        ref can match it. This stays the FULL stable key — the short ``[S:…]``
        citation never shortens or replaces it (item 6).
        """
        key = self._server.chunk_key(candidate.payload, ctx)
        return key if key is not None else candidate.key

    @staticmethod
    def _fence_width(source_text: str) -> int:
        """The backtick-fence width for ``source_text`` (item 10, CommonMark rule).

        Longer than any backtick run inside the source (so an embedded ``` cannot
        close the fence early), bounded below by the three-backtick minimum.
        """
        return max(_MIN_FENCE_WIDTH, _max_backtick_run(source_text) + 1)

    def _base_format(
        self, payload: dict[str, Any], key: str, enrichment_lines: list[str]
    ) -> str:
        """The base default citation (item 6): kept ``[SOURCE:]`` + ``Key:`` + fence,
        plus the added v2 short ``[S:…]`` citation and any graph enrichment.

        The path/identity-carrying lines are render-sanitised (item 10) so a
        hostile ``file_path`` cannot break a citation line; the source body is
        wrapped VERBATIM in a backtick fence sized to survive an embedded run.
        """
        file_path = str(payload.get(_PAYLOAD_FILE_PATH, ""))
        tier = str(payload.get(_PAYLOAD_TIER, ""))
        line_start = payload.get(_PAYLOAD_LINE_START, 0)
        line_end = payload.get(_PAYLOAD_LINE_END, line_start)
        content_hash = str(payload.get(_PAYLOAD_CONTENT_HASH, ""))
        source_text = payload.get(_PAYLOAD_SOURCE_TEXT, "") or ""
        hash6 = content_hash[:_SHORT_HASH_LEN]

        # Non-fenced rendered fields — each sanitised to a single logical line.
        lines = [
            _sanitise_line(f"[SOURCE:{file_path}:{line_start}]"),
            _sanitise_line(f"Key: {key}"),
            _sanitise_line(
                f"{_SHORT_CITATION_PREFIX}{tier}:{file_path}:{line_start}-{line_end}@{hash6}]"
            ),
            *enrichment_lines,
        ]
        # The source body: verbatim, wrapped in a fence longer than any run inside.
        fence = _FENCE_CHAR * self._fence_width(source_text)
        lines.extend((fence, source_text, fence))
        return "\n".join(lines)

    async def _is_stale(self, payload: dict[str, Any]) -> bool:
        """True iff the chunk's manifest file row is in-flight (not ``indexed``).

        The manifest — not the store — is the freshness authority. A row absent
        from the manifest is treated as settled (nothing in-flight to warn about).
        """
        tier = payload.get(_PAYLOAD_TIER, "")
        file_path = payload.get(_PAYLOAD_FILE_PATH, "")
        row = await self._manifest.get(tier, file_path)
        if row is None:
            return False
        return row.state != STATE_INDEXED

    # -- step 8: detail-level partition -------------------------------------

    @staticmethod
    def _partition_by_detail(
        hits: list[SearchResult], detail_level: str
    ) -> list[SearchResult]:
        """Keep only the code hits matching the requested detail level (``auto`` = all).

        Applied to the code hits only; injected memory entries are prepended after
        this and are never partitioned (they are response-level guidance).
        """
        if detail_level == _DETAIL_AUTO:
            return hits
        return [hit for hit in hits if hit.detail_level == detail_level]
