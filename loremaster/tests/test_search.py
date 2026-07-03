"""Contract tests for ``loremaster.search`` — the P6 query-time pipeline (v2).

The :class:`~loremaster.search.SearchPipeline` is the read side of lore: it turns
a natural-language query into a list of *summarised* :class:`SearchResult` value
objects, never a raw backend hit. It is the MCP ``search_code`` tool's engine.

**P6 read-path cutover (plan §6).** The pipeline reads from the unified SurrealDB
store's ``hybrid_search`` (HNSW ⊕ BM25 fused with Reciprocal Rank Fusion), which
returns backend-neutral :class:`~loremaster.store.candidate.Candidate`\\ s
(``key`` = bare uuid5, ``score`` = RRF-scale < 1.0, ``payload`` = the FLATTENED
canonical chunk fields incl. the chunker's ``signature``, ``origin`` = ``"fused"``)
— never a ``qdrant_client`` ``ScoredPoint``. These run against the audited
in-memory :func:`~_surreal_fakes.fake_surreal_trio` (store + manifest + graph
sharing one database), the shipped deterministic
:class:`~loresigil.testing.FakeEmbedder`, and — for the memory features — a small
recall double; NO live Qdrant/SurrealDB server is required.

The pinned P6 contract (each maps to plan §6):

* **Store cutover (item 1).** ``search_code`` calls ``store.hybrid_search`` with
  BOTH the query VECTOR (embedded) AND the raw query TEXT (the BM25 arm needs it),
  producing :class:`SearchResult`\\ s, never a ``Candidate``/``ScoredPoint`` dump.
  Filters (tier / file_path / the ``path`` alias) survive verbatim.
* **Honest failure (item 2).** A down store RAISES out of ``search_code`` (never a
  silent ``[]``); an embedder failure propagates (never swallowed).
* **Memory-boost re-grounded on RRF scale (item 4).** A memory-referenced hit
  overtakes an unreferenced higher-RRF-scored one (proven by an ordering flip vs a
  no-memory control), and equally-boosted hits keep a stable order. No memory
  store ⇒ inert.
* **Visible memory injection (item 5, NEW).** ≤2 query-matching memories are
  injected as VISIBLE, provenance-stamped result entries (distinct from the silent
  score-boost) — the memory text + a provenance marker + its refs' keys — that do
  NOT masquerade as source citations.
* **Citation grammar + short keys (item 6).** The base format KEEPS
  ``[SOURCE:file:line]`` + ``Key:`` + fenced source AND ADDS the v2 citation
  ``[S:tier:path:start-end@hash6]``; ``chunk_key`` stays the full stable bare uuid5.
* **Per-hit graph enrichment (item 7).** Each function/method hit carries
  ``← N prod / M test · tests: K`` (from the code graph) plus its ``signature``;
  enrichment is capped (≤10 graph joins per response, top-10 by score); a graph
  that raises mid-enrichment still returns the hit, annotated with an explicit
  marker.
* **Per-result staleness stays visible (item 8).** An in-flight (dirty/embedding)
  chunk is flagged stale but still returned; ``wait_for_fresh`` is bounded.
* **Config-gated reranker seam (item 9).** ``search.reranker`` null (default) ⇒ the
  reranker seam is provably NOT called; configured ⇒ candidates pass through it
  post-RRF, pre-format.
* **Render-sanitiser (item 10).** Control chars / framing in non-fenced fields
  (identities / paths / memory lines) are collapsed so they cannot break the
  citation line or escape a fence.
* **Detail levels (item 11).** The ``auto``/``summary``/``source`` partition
  survives.
* **Extension hooks (item 3).** The seam hooks operate on ``Candidate``.
"""

from __future__ import annotations

import re
import time
import uuid
from pathlib import Path
from typing import Any, cast

import pytest
from _extension_helpers import FakeExtension, minimal_config
from _surreal_fakes import (
    FakeSurrealCodeGraph,
    FakeSurrealManifest,
    FakeSurrealStore,
    fake_surreal_trio,
)
from loremaster.config import LoreConfig
from loremaster.extension import Extension, ExtensionContext
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.manifest import STATE_DIRTY, STATE_EMBEDDING, STATE_INDEXED
from loremaster.index.records import chunk_to_record, point_id, sha512_hex
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.memory.store import MemoryRef, RecalledMemory
from loremaster.search import SearchPipeline, SearchResult
from loremaster.server import LoreServer
from loremaster.store.candidate import Candidate
from loremaster.store.surreal import SurrealConnectionError, SurrealStore
from lorescribe.models import Chunk, ChunkContext
from loresigil.testing import FakeEmbedder

# Production embedding dim per the owner directive (FakeEmbedder at 2048).
_DIM = 2048

# The (sole) tier every ``_config``-built config declares.
_TIER = "custom"

# The freshness warning marker the plan pins ("⚠ re-indexing — may be stale").
_STALE_MARKER = "re-indexing"

# --------------------------------------------------------------------------- #
# Contract constants THIS module DEFINES (the interface the pipeline must meet).
# These are the shapes/caps/markers the CONTRACT decides for items 5/6/7/10 —
# not values reverse-engineered from any implementation. Reported for review.
# --------------------------------------------------------------------------- #

# item 6: the v2 short-citation grammar prefix. Full form:
# ``[S:<tier>:<file_path>:<line_start>-<line_end>@<hash6>]`` (hash6 = first 6 hex
# of the chunk's content_hash). Coexists with the kept ``[SOURCE:file:line]``.
_SHORT_CITATION_PREFIX = "[S:"

# item 7: the per-hit graph ref-join line, rendered on a function/method hit as
# ``← N prod / M test · tests: K`` (N/M = production/test reference counts from
# ``graph.references``; K = covering-test-node count from ``graph.tests_for``).
_ENRICHMENT_ARROW = "←"  # "←"
_ENRICHMENT_MIDDOT = "·"  # "·"
# item 7: the maximum number of hits enriched per response (dead-reckoning's cap);
# a k=20 response issues at most this many graph joins (top-10 by score).
_ENRICHMENT_CAP = 10
# item 7: the explicit marker annotating a hit whose enrichment could not be
# computed (the graph raised mid-enrichment) — annotate, never blanket-fail.
_ENRICHMENT_UNAVAILABLE = "⚠ enrichment unavailable"  # "⚠ enrichment unavailable"

# item 5: the provenance marker distinguishing an injected memory line from a real
# source citation; the injected result's ``kind`` discriminator; the injection cap.
_MEMORY_MARKER = "[MEMORY]"
_MEMORY_KIND = "memory"
_HIT_KIND = "hit"
_MEMORY_INJECTION_CAP = 2


def _refjoin_line(n_prod: int, n_test: int, n_tests: int) -> str:
    """The exact ref-join enrichment substring for the given graph counts (item 7).

    The format is the CONTRACT (``← N prod / M test · tests: K``); the *values*
    are supplied by an independent oracle (a hand-known corpus + the audited fake
    graph's own ``references``/``tests_for``), so this is a faithful-forwarding
    check, not a restatement of the pipeline's own arithmetic.
    """
    return f"{_ENRICHMENT_ARROW} {n_prod} prod / {n_test} test {_ENRICHMENT_MIDDOT} tests: {n_tests}"


# --------------------------------------------------------------------------- #
# Real corpora — modules whose chunk types / references we can pin by inspection.
# --------------------------------------------------------------------------- #
# A real module the python_ast chunker splits into imports/class/method/function —
# types the base classifies as summary (imports/class) vs source (method/function).
_PY_ROUTING = """\
import os


class Router:
    \"\"\"Routes a request.\"\"\"

    def route(self, request):
        return os.path.join("/", request)


def champion_routing(week):
    \"\"\"Route the 36-week curve champion warehouse.\"\"\"
    return week * 2
"""

# A second real module with a distinct uniquely-named function, so two files'
# chunks coexist and a per-file filter is meaningful.
_PY_PRICING = """\
def quarterly_pricing(volume):
    \"\"\"Compute the quarterly tiered price for a paper volume.\"\"\"
    return volume * 0.95
"""

# --- enrichment corpus: a target with a KNOWN production + test reference profile
# (modelled on test_graph_surreal's REFLIB — a symbol called from prod AND a test).
_REFLIB_SOURCE = """\
def champion_routing(week):
    \"\"\"Route the 36-week curve champion warehouse.\"\"\"
    return week * 2
"""

_CONSUMER_SOURCE = """\
from reflib import champion_routing


def dispatch(week):
    \"\"\"A production caller of champion_routing.\"\"\"
    return champion_routing(week)
"""

_TEST_REFLIB_SOURCE = """\
from reflib import champion_routing


def test_champion_routing():
    assert champion_routing(1) == 2
"""

# The unique bare symbol name the enrichment join keys on (globally unique across
# the enrichment corpus, so a bare-name OR fqn join both resolve it).
_ENRICHMENT_SYMBOL = "champion_routing"


def _write(path: Path, text: str) -> None:
    """Create parents and write ``text`` (UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _slug() -> str:
    """A per-test slug (point ids fold it in, so keep it unique)."""
    return f"test_{uuid.uuid4().hex}"


def _config(
    *,
    slug: str,
    live_path: Path,
    reranker: dict[str, Any] | None = None,
) -> LoreConfig:
    """A validated :class:`LoreConfig` with one live tier rooted at ``live_path``.

    ``reranker`` threads the P6 ``search.reranker: {url, model}`` block (item 9);
    ``None`` (the default) leaves it unset, so the config carries no reranker and
    the pipeline must provably NOT call the reranker seam.
    """
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "qdrant": {"url": "http://127.0.0.1:16333", "api_key_env": "QDRANT__SERVICE__API_KEY"},
        "roots": [
            {
                "tier": _TIER,
                "watch": "live",
                "path": str(live_path),
                "include": ["**/*.py"],
            }
        ],
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9201},
    }
    if reranker is not None:
        # item 9: the config-gated reranker seam (SearchConfig). Present ⇒ the
        # pipeline routes candidates through the seam post-RRF, pre-format.
        payload["search"] = {"reranker": reranker}
    return LoreConfig.model_validate(payload)


# --------------------------------------------------------------------------- #
# Producer-grounded oracles — the query text / line span / signature the REAL
# chunker emits (so a fixture value is the genuine producer's output, never a
# hand-mirrored copy).
# --------------------------------------------------------------------------- #
def _chunk_for(server: LoreServer, file_path: str, source: str, identity: str) -> Chunk:
    """Return the REAL chunk the indexer's chunker emits for ``identity``.

    Runs ``source`` through the SAME chunker registry the indexer uses, so the
    line span / signature / embedding_text read off it are the genuine producer's
    output — an independent oracle, not a hand-mirrored copy.
    """
    ctx = ChunkContext(
        slug="oracle",
        file_path=file_path,
        count_tokens=lambda text: max(1, len(text) // 4),
        max_input_tokens=8192,
    )
    chunks = server.registry.dispatch_file(file_path, source, ctx)
    return next(chunk for chunk in chunks if chunk.identity == identity)


def _embedding_text_for(
    server: LoreServer, file_path: str, source: str, identity: str
) -> str:
    """The EXACT ``embedding_text`` the indexer embedded for one chunk (rank oracle).

    A query equal to this embeds — under the deterministic FakeEmbedder — to that
    chunk's stored vector (cosine 1.0), an independent ranking oracle free of a
    hardcoded chunker text format.
    """
    return _chunk_for(server, file_path, source, identity).embedding_text


def _expected_point_id(slug: str, file_path: str, chunk: Chunk) -> str:
    """The bare uuid5 point id the indexer mints for ``chunk`` (chunk_key oracle).

    Computed via the production :func:`~loremaster.index.records.point_id` over the
    chunk's own natural key — the SAME derivation ``chunk_to_record`` uses — so it
    is independent of the pipeline's own key handling.
    """
    return point_id(slug, _TIER, file_path, chunk.chunk_type, chunk.identity, chunk.sub_ordinal)


def _expected_short_citation(file_path: str, source: str, chunk: Chunk) -> str:
    """The exact ``[S:tier:path:start-end@hash6]`` citation for ``chunk`` (item 6).

    ``hash6`` is the first 6 hex of the file's SHA-512, computed HERE from the raw
    source via the production :func:`~loremaster.index.records.sha512_hex` — an
    independent oracle, never read back from the pipeline's formatted output.
    """
    hash6 = sha512_hex(source)[:6]
    return (
        f"{_SHORT_CITATION_PREFIX}{_TIER}:{file_path}:"
        f"{chunk.line_start}-{chunk.line_end}@{hash6}]"
    )


def _max_backtick_run(text: str) -> int:
    """The longest run of consecutive backticks anywhere in ``text``."""
    runs = re.findall(r"`+", text)
    return max((len(run) for run in runs), default=0)


# --------------------------------------------------------------------------- #
# Test doubles (all faithful to the seam they stand in for).
# --------------------------------------------------------------------------- #
class FlatFakeEmbedder(FakeEmbedder):
    """A :class:`FakeEmbedder` pinned to the FLAT embed path.

    The identity oracle (query text == chunk text ⇒ cosine 1.0) holds only when
    index-time vectors are FLAT; a contextualized embedder's grouped vectors are
    deliberately context-sensitive.
    """

    @property
    def supports_contextualized(self) -> bool:
        """Instrument the FLAT embed path — opt out of grouped dispatch."""
        return False


class _FailingEmbedder(FlatFakeEmbedder):
    """A :class:`FakeEmbedder` whose query embed permanently raises (item 2)."""

    class EmbedderDown(RuntimeError):
        """The distinct error this double raises from ``embed_query``."""

    async def embed_query(self, text: str) -> list[float]:
        """Raise instead of embedding — the pipeline must NOT swallow this."""
        raise self.EmbedderDown("embedder backend is down")


class _RecordingSurrealStore(FakeSurrealStore):
    """A :class:`FakeSurrealStore` that records its last ``hybrid_search`` call.

    Proves the producer→consumer seam (item 1): the pipeline forwards BOTH the
    embedded query VECTOR and the RAW query TEXT (the BM25 arm's input) into the
    store. It still delegates to the real fused search, so results are genuine.
    """

    def __init__(self, *, dim: int, db: Any) -> None:
        super().__init__(dim=dim, db=db)
        self.last_query_text: str | None = None
        self.last_query_vector: list[float] | None = None
        self.last_k: int | None = None
        self.hybrid_search_calls = 0

    async def hybrid_search(
        self,
        *,
        query_vector: list[float],
        query_text: str,
        k: int,
        filters: dict[str, str] | None = None,
    ) -> list[Candidate]:
        self.last_query_text = query_text
        self.last_query_vector = list(query_vector)
        self.last_k = k
        self.hybrid_search_calls += 1
        return await super().hybrid_search(
            query_vector=query_vector, query_text=query_text, k=k, filters=filters
        )


class _FakeMemoryStore:
    """A minimal recall double standing in for the pipeline's ``memory_store`` seam.

    The pipeline consumes ``recall_memory(query) -> list[RecalledMemory]``; this
    returns a fixed, score-ordered list so the memory-boost (item 4) and visible
    injection (item 5) behaviours are deterministic without a live embedder/Qdrant.
    (MemoryStore internals are P7 — explicitly out of scope for this cycle.)
    """

    def __init__(self, recalled: list[RecalledMemory]) -> None:
        self._recalled = recalled
        self.recall_calls = 0

    async def recall_memory(self, query: str, k: int = 5) -> list[RecalledMemory]:
        self.recall_calls += 1
        return list(self._recalled[:k])


class _RecordingReranker:
    """A recording stand-in for the config-gated cross-encoder reranker seam (item 9).

    Records whether it was called and the candidates it received (post-RRF,
    pre-format), returning them unchanged. No live reranker in P6 — the seam
    interface only.
    """

    def __init__(self) -> None:
        self.calls = 0
        self.received: list[Candidate] | None = None

    async def rerank(
        self, query: str, candidates: list[Candidate], ctx: ExtensionContext
    ) -> list[Candidate]:
        self.calls += 1
        self.received = list(candidates)
        return candidates


class _CountingCodeGraph(FakeSurrealCodeGraph):
    """A :class:`FakeSurrealCodeGraph` counting enrichment lookups (item 7 cap)."""

    def __init__(self, *, db: Any, tier_roots: Any, project_roots: Any) -> None:
        super().__init__(db=db, tier_roots=tier_roots, project_roots=project_roots)
        self.reference_lookups = 0

    async def references(self, name: str) -> Any:
        self.reference_lookups += 1
        return await super().references(name)


class _RaisingCodeGraph(FakeSurrealCodeGraph):
    """A :class:`FakeSurrealCodeGraph` whose enrichment queries raise (item 7)."""

    async def references(self, name: str) -> Any:
        raise SurrealConnectionError("code graph socket dropped mid-enrichment")

    async def tests_for(self, symbol_or_file: str) -> Any:
        raise SurrealConnectionError("code graph socket dropped mid-enrichment")


class _CtxRecordingExtension(Extension):
    """An :class:`Extension` whose seam-4 ``augment_candidates`` records its ``ctx``.

    ``augment_candidates`` fires UNCONDITIONALLY (even over an empty candidate
    list), so it is the reliable observation point for "the search seam receives a
    RUNTIME context carrying the real services", independent of whether any hit is
    served. P6: it now receives ``list[Candidate]``.
    """

    def __init__(self) -> None:
        self.recorded_ctx: ExtensionContext | None = None

    @property
    def name(self) -> str:
        return "ctxrec"

    def augment_candidates(
        self, query: str, candidates: list[Candidate], ctx: ExtensionContext
    ) -> list[Candidate]:
        self.recorded_ctx = ctx
        return candidates


# --------------------------------------------------------------------------- #
# Indexing + pipeline wiring over the shared fake trio.
# --------------------------------------------------------------------------- #
class _Indexed:
    """A bundle: the fake trio (store/manifest/graph over one db) + the config."""

    def __init__(
        self,
        *,
        store: FakeSurrealStore,
        # The truthful fixture type — _make_pipeline casts it to the pipeline's
        # SurrealManifest-typed param at the one construction seam.
        manifest: FakeSurrealManifest,
        graph: FakeSurrealCodeGraph,
        config: LoreConfig,
        db: Any,
    ) -> None:
        self.store = store
        self.manifest = manifest
        self.graph = graph
        self.config = config
        self.db = db


async def _index_corpus(
    *,
    slug: str,
    live_path: Path,
    embedder: FakeEmbedder,
    server: LoreServer | None = None,
    reranker: dict[str, Any] | None = None,
) -> _Indexed:
    """Index every ``*.py`` under ``live_path`` into a fresh fake trio.

    Chunks + embeds every file through the SAME producer helpers the real Indexer
    uses (the real chunker registry + the real (fake) embedder + the production
    ``chunk_to_record``), then writes each file's chunks to the store, its manifest
    row, AND its derived code-graph slice — so the points under search carry real
    chunk types / payloads / line spans and the graph carries real reference edges
    (the tier/project roots point astroid at the on-disk corpus for resolution).
    """
    config = _config(slug=slug, live_path=live_path, reranker=reranker)
    composed = server if server is not None else LoreServer(config)
    trio = fake_surreal_trio(
        dim=embedder.dim,
        tier_roots={_TIER: str(live_path)},
        project_roots=[str(live_path)],
    )
    for path in sorted(live_path.rglob("*.py")):
        rel = str(path.relative_to(live_path).as_posix())
        source = path.read_text(encoding="utf-8")
        content_hash = sha512_hex(source)
        stat = path.stat()
        ctx = ChunkContext(
            slug=slug,
            file_path=rel,
            count_tokens=lambda text: embedder.count_tokens([text])[0],
            max_input_tokens=embedder.max_input_tokens,
        )
        chunks = composed.registry.dispatch_file(rel, source, ctx)
        records = [
            chunk_to_record(
                chunk, slug=slug, tier=_TIER, file_path=rel,
                content_hash=content_hash, mtime_ns=stat.st_mtime_ns,
            )
            for chunk in chunks
        ]
        vectors: list[list[float] | None] = []
        if records:
            result = await embedder.embed_documents([r.embedding_text for r in records])
            vectors = result.vectors
        pairs = [
            (record, vector)
            for record, vector in zip(records, vectors, strict=True)
            if vector is not None
        ]
        await trio.store.upsert(pairs)
        await trio.manifest.upsert(
            tier=_TIER, file_path=rel, sha512=content_hash, mtime_ns=stat.st_mtime_ns,
            size=len(source.encode("utf-8")), n_chunks=len(records),
            chunk_ids=[record.point_id for record in records], state=STATE_INDEXED,
        )
        await trio.graph.build_file_graph(_TIER, rel, chunks)
    return _Indexed(
        store=trio.store, manifest=trio.manifest, graph=trio.graph, config=config, db=trio.db
    )


def _make_pipeline(
    *,
    indexed: _Indexed,
    embedder: FakeEmbedder,
    server: LoreServer,
    memory_store: Any | None = None,
    reranker: Any | None = None,
    store: FakeSurrealStore | None = None,
    code_graph: FakeSurrealCodeGraph | None = None,
) -> SearchPipeline:
    """Wire a v2 :class:`SearchPipeline` over an indexed bundle + composed server.

    Builds the RUNTIME :class:`ExtensionContext` over the live (fake) services so
    the pipeline's search seams receive a functional embedder/manifest/tokenizer.
    ``code_graph`` (item 7) is a required v2 dependency; ``reranker`` (item 9) is
    the optional config-gated seam.
    """
    the_store = store if store is not None else indexed.store
    the_graph = code_graph if code_graph is not None else indexed.graph
    extension_context = ExtensionContext(
        store=the_store,
        embedder=embedder,
        config=indexed.config,
        count_tokens=embedder.count_tokens,
        manifest=indexed.manifest,
    )
    return SearchPipeline(
        store=cast(SurrealStore, the_store),
        embedder=embedder,
        server=server,
        manifest=cast(SurrealManifest, indexed.manifest),
        config=indexed.config,
        extension_context=extension_context,
        code_graph=cast(SurrealCodeGraph, the_graph),
        memory_store=memory_store,
        reranker=reranker,
    )


@pytest.fixture()
def embedder() -> FakeEmbedder:
    """The shipped deterministic embedder at the production dim (flat-path pinned)."""
    return FlatFakeEmbedder(dim=_DIM)


async def _index_single(
    tmp_path: Path, embedder: FakeEmbedder, *, files: dict[str, str] | None = None
) -> tuple[_Indexed, LoreServer]:
    """Index a small corpus (``routing.py`` by default) and return (indexed, server)."""
    corpus = files if files is not None else {"routing.py": _PY_ROUTING}
    for name, text in corpus.items():
        _write(tmp_path / name, text)
    slug = _slug()
    config = _config(slug=slug, live_path=tmp_path)
    server = LoreServer(config)
    indexed = await _index_corpus(
        slug=slug, live_path=tmp_path, embedder=embedder, server=server
    )
    return indexed, server


# --------------------------------------------------------------------------- #
# item 1 — store cutover (hybrid_search: vector + text; Candidate → SearchResult)
# --------------------------------------------------------------------------- #
class TestStoreCutover:
    """search_code reads from hybrid_search and returns summarised value objects."""

    async def test_forwards_query_vector_and_raw_text_to_hybrid_search(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # The producer→consumer seam: the pipeline embeds the query for the vector
        # arm but MUST forward the RAW query text for the BM25 arm — dropping it (or
        # sending the vector/prompt text) is the classic seam bug this pins.
        indexed, server = await _index_single(tmp_path, embedder)
        recording = _RecordingSurrealStore(dim=embedder.dim, db=indexed.db)
        pipeline = _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, store=recording
        )

        query = "champion routing warehouse"
        await pipeline.search_code(query, k=5)

        assert recording.hybrid_search_calls == 1
        # The BM25 arm's input is the caller's RAW query text, verbatim.
        assert recording.last_query_text == query
        # The vector arm's input is the embedded query (deterministic ⇒ equal).
        assert recording.last_query_vector == await embedder.embed_query(query)

    async def test_returns_search_result_value_objects_never_candidates(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        results = await pipeline.search_code("champion routing warehouse", k=5)

        assert results, "a real query over a real corpus must return hits"
        assert all(isinstance(r, SearchResult) for r in results)
        # Never a raw backend hit dump (the Anthropic token-efficiency rule).
        assert not any(isinstance(r, Candidate) for r in results)

    async def test_respects_k_ceiling(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(
            tmp_path, embedder, files={"routing.py": _PY_ROUTING, "pricing.py": _PY_PRICING}
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        # k bounds the number of store hits returned (no memory store ⇒ no
        # extra visible-memory entries, so total == hits).
        results = await pipeline.search_code("anything", k=2)
        assert len(results) <= 2


# --------------------------------------------------------------------------- #
# item 2 — honest failure (down store RAISES; embedder failure propagates)
# --------------------------------------------------------------------------- #
class TestHonestFailure:
    """A down store raises out of search_code; an embedder failure propagates."""

    async def test_down_store_raises_never_returns_empty(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        # Arm the store to simulate a downed connection on the next read; the
        # pipeline must surface it LOUDLY (a silent [] would hide an outage).
        indexed.store.arm_connection_failure()
        with pytest.raises(SurrealConnectionError):
            await pipeline.search_code("champion routing warehouse", k=5)

    async def test_embedder_failure_propagates(
        self, tmp_path: Path
    ) -> None:
        failing = _FailingEmbedder(dim=_DIM)
        # Index with a WORKING embedder, then search with the failing one so the
        # failure is isolated to the query-embed step.
        working = FlatFakeEmbedder(dim=_DIM)
        indexed, server = await _index_single(tmp_path, working)
        pipeline = _make_pipeline(indexed=indexed, embedder=failing, server=server)

        with pytest.raises(_FailingEmbedder.EmbedderDown):
            await pipeline.search_code("champion routing warehouse", k=5)


# --------------------------------------------------------------------------- #
# item 6 — citation grammar (kept [SOURCE:] + Key: + fence, added [S:...]) + keys
# --------------------------------------------------------------------------- #
class TestCitationGrammar:
    """The base citation keeps its v1 grammar AND gains the v2 short citation."""

    async def test_base_format_keeps_source_key_and_fenced_block(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        # A query equal to champion_routing's embedding_text ranks it first.
        query = _embedding_text_for(server, "routing.py", _PY_ROUTING, "champion_routing")
        results = await pipeline.search_code(query, k=5)
        top = results[0]

        assert "[SOURCE:routing.py:" in top.formatted
        assert "Key:" in top.formatted
        assert top.chunk_key and top.chunk_key in top.formatted
        assert "```" in top.formatted

    async def test_source_line_matches_chunk_line_start(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # champion_routing's ``def`` is line 11 of _PY_ROUTING (import(1), blanks,
        # class(4)+docstring(5)+blank(6)+method(7,8)+blanks(9,10), def at 11) — an
        # oracle counted from the source, not read back from the implementation.
        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        query = _embedding_text_for(server, "routing.py", _PY_ROUTING, "champion_routing")
        top = (await pipeline.search_code(query, k=5))[0]
        assert "[SOURCE:routing.py:11]" in top.formatted

    async def test_v2_short_citation_composed_from_payload_fields(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # item 6: ``[S:tier:path:start-end@hash6]`` — every component sourced from
        # the payload (tier/path/line span) + the file's real SHA-512 (first 6 hex).
        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        query = _embedding_text_for(server, "routing.py", _PY_ROUTING, "champion_routing")
        top = (await pipeline.search_code(query, k=5))[0]

        chunk = _chunk_for(server, "routing.py", _PY_ROUTING, "champion_routing")
        expected = _expected_short_citation("routing.py", _PY_ROUTING, chunk)
        # The exact short citation the CONTRACT specifies, e.g.
        # ``[S:custom:routing.py:11-13@<hash6>]``.
        assert expected in top.formatted

    async def test_both_citation_grammars_coexist(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        query = _embedding_text_for(server, "routing.py", _PY_ROUTING, "champion_routing")
        top = (await pipeline.search_code(query, k=5))[0]

        # The acceptance-pinned v1 citation survives alongside the added v2 short one.
        assert "[SOURCE:" in top.formatted
        assert _SHORT_CITATION_PREFIX in top.formatted

    async def test_chunk_key_is_the_full_stable_bare_uuid5(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # item 6: chunk_key REMAINS the full stable key (memory refs match on it);
        # the added short citation must not shorten or replace it.
        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        query = _embedding_text_for(server, "routing.py", _PY_ROUTING, "champion_routing")
        top = (await pipeline.search_code(query, k=5))[0]

        chunk = _chunk_for(server, "routing.py", _PY_ROUTING, "champion_routing")
        expected_key = _expected_point_id(indexed.config.project.slug, "routing.py", chunk)
        assert top.chunk_key == expected_key
        # A canonical uuid5 string (36 chars), never a truncated hash6.
        assert uuid.UUID(top.chunk_key)


# --------------------------------------------------------------------------- #
# item 1/4 — ranking (RRF-scale) + magnitude sanity bound on the derived score
# --------------------------------------------------------------------------- #
class TestRanking:
    """A chunk whose text equals the query ranks first; its score is RRF-scale."""

    async def test_query_equal_to_chunk_text_ranks_it_first_at_rrf_scale(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(
            tmp_path, embedder, files={"routing.py": _PY_ROUTING, "pricing.py": _PY_PRICING}
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        # The EXACT text embedded for quarterly_pricing → its stored vector (cosine
        # 1.0), so the pricing chunk MUST outrank every routing chunk. Independent
        # oracle: the query is the producer's own embedding_text.
        pricing_text = _embedding_text_for(server, "pricing.py", _PY_PRICING, "quarterly_pricing")
        results = await pipeline.search_code(pricing_text, k=5)

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert hits
        assert "pricing.py" in hits[0].formatted
        # Magnitude/sanity bound (clause 4): a fused RRF score is strictly positive
        # and well under 1.0 (unlike a raw cosine, which would be ~1.0). Catches an
        # order-of-magnitude regression to raw cosine or an un-fused arm.
        assert 0.0 < hits[0].score < 1.0


# --------------------------------------------------------------------------- #
# item 4 — memory-boost re-grounded on RRF scale (behaviour, not the constant)
# --------------------------------------------------------------------------- #
class TestMemoryBoost:
    """A memory-referenced hit overtakes an unreferenced higher-RRF-scored one."""

    async def _two_file_pipeline(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> tuple[_Indexed, LoreServer]:
        return await _index_single(
            tmp_path, embedder, files={"routing.py": _PY_ROUTING, "pricing.py": _PY_PRICING}
        )

    async def test_boost_flips_order_vs_no_memory_control(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await self._two_file_pipeline(tmp_path, embedder)
        query = "tiered routing and pricing logic"

        # CONTROL: no memory store ⇒ the bare RRF ranking decides the hit order.
        control = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        control_hits = [r for r in await control.search_code(query, k=5) if r.kind == _HIT_KIND]
        assert len(control_hits) >= 2
        control_top_key = control_hits[0].chunk_key
        boost_target = next(r for r in control_hits[1:] if r.chunk_key != control_top_key)

        # A recalled memory referencing the lower-ranked hit's key must lift it.
        memory_store = _FakeMemoryStore(
            [
                RecalledMemory(
                    text="the pricing/routing correction",
                    refs=[MemoryRef(chunk_key=boost_target.chunk_key)],
                    score=0.9,
                )
            ]
        )
        boosted = _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, memory_store=memory_store
        )
        boosted_hits = [r for r in await boosted.search_code(query, k=5) if r.kind == _HIT_KIND]
        boosted_keys = [r.chunk_key for r in boosted_hits]

        # An ordering FLIP that only the boost can cause (the control proves the
        # target was ranked BELOW the former top) — behaviour, not the constant.
        assert boost_target.chunk_key in boosted_keys
        assert boosted_keys.index(boost_target.chunk_key) < boosted_keys.index(control_top_key)

    async def test_stable_order_among_equally_boosted_hits(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await self._two_file_pipeline(tmp_path, embedder)
        query = "tiered routing and pricing logic"

        control = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        control_hits = [r for r in await control.search_code(query, k=10) if r.kind == _HIT_KIND]
        assert len(control_hits) >= 2
        # Boost the top TWO hits equally; their RELATIVE order must be preserved.
        top_two = [control_hits[0].chunk_key, control_hits[1].chunk_key]
        memory_store = _FakeMemoryStore(
            [
                RecalledMemory(
                    text="boost both leaders",
                    refs=[MemoryRef(chunk_key=k) for k in top_two],
                    score=0.9,
                )
            ]
        )
        boosted = _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, memory_store=memory_store
        )
        boosted_keys = [
            r.chunk_key for r in await boosted.search_code(query, k=10) if r.kind == _HIT_KIND
        ]
        # Both stay at the head and keep their control order (stable among equals).
        assert boosted_keys.index(top_two[0]) < boosted_keys.index(top_two[1])

    async def test_no_memory_store_is_inert(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await self._two_file_pipeline(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        results = await pipeline.search_code("routing", k=5)
        assert results
        # No memory store ⇒ no boost AND no injected memory entries.
        assert all(r.kind == _HIT_KIND for r in results)


# --------------------------------------------------------------------------- #
# item 5 — visible, provenance-stamped memory injection (NEW)
# --------------------------------------------------------------------------- #
class TestVisibleMemoryInjection:
    """≤2 query-matching memories render as visible provenance lines, distinct
    from the silent boost and NOT masquerading as source citations."""

    async def _pipeline_with_memories(
        self, tmp_path: Path, embedder: FakeEmbedder, recalled: list[RecalledMemory]
    ) -> SearchPipeline:
        indexed, server = await _index_single(tmp_path, embedder)
        return _make_pipeline(
            indexed=indexed, embedder=embedder, server=server,
            memory_store=_FakeMemoryStore(recalled),
        )

    async def test_matching_memory_injected_as_visible_provenance_line(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        ref_key = "11111111-1111-5111-8111-111111111111"
        memory_text = "champion_routing lives in routing.py, not pricing.py"
        pipeline = await self._pipeline_with_memories(
            tmp_path, embedder,
            [RecalledMemory(text=memory_text, refs=[MemoryRef(chunk_key=ref_key)], score=0.9)],
        )

        results = await pipeline.search_code("champion routing warehouse", k=5)
        memory_entries = [r for r in results if r.kind == _MEMORY_KIND]

        assert len(memory_entries) == 1
        line = memory_entries[0].formatted
        # The line carries the provenance marker + the memory text + its ref key.
        assert _MEMORY_MARKER in line
        assert memory_text in line
        assert ref_key in line

    async def test_injected_line_is_not_a_source_citation(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # The visible memory line must be DISTINGUISHABLE from a real code hit — it
        # must not carry either citation grammar, or an agent could mistake project
        # guidance for a cited source span.
        pipeline = await self._pipeline_with_memories(
            tmp_path, embedder,
            [RecalledMemory(
                text="a project convention note",
                refs=[MemoryRef(chunk_key="22222222-2222-5222-8222-222222222222")],
                score=0.9,
            )],
        )
        results = await pipeline.search_code("champion routing warehouse", k=5)
        memory_entries = [r for r in results if r.kind == _MEMORY_KIND]
        assert memory_entries
        for entry in memory_entries:
            assert "[SOURCE:" not in entry.formatted
            assert _SHORT_CITATION_PREFIX not in entry.formatted

    async def test_injection_capped_at_two_by_score(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # Three matching memories recalled; only the TWO highest-scored are injected
        # (a deterministic cap), in descending-score order.
        recalled = [
            RecalledMemory(text="mem-high", refs=[MemoryRef(chunk_key="a" * 32)], score=0.95),
            RecalledMemory(text="mem-mid", refs=[MemoryRef(chunk_key="b" * 32)], score=0.80),
            RecalledMemory(text="mem-low", refs=[MemoryRef(chunk_key="c" * 32)], score=0.50),
        ]
        pipeline = await self._pipeline_with_memories(tmp_path, embedder, recalled)

        results = await pipeline.search_code("champion routing warehouse", k=5)
        memory_texts = [r.formatted for r in results if r.kind == _MEMORY_KIND]

        assert len(memory_texts) == _MEMORY_INJECTION_CAP
        # The top-2 by score, in order; the low-score memory is dropped.
        assert "mem-high" in memory_texts[0]
        assert "mem-mid" in memory_texts[1]
        assert all("mem-low" not in text for text in memory_texts)

    async def test_injected_memories_render_before_hits(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # Contract decision: injected memories lead the result list (response-level
        # guidance surfaces first), then the ranked code hits follow.
        pipeline = await self._pipeline_with_memories(
            tmp_path, embedder,
            [RecalledMemory(
                text="a leading note",
                refs=[MemoryRef(chunk_key="d" * 32)], score=0.9,
            )],
        )
        results = await pipeline.search_code("champion routing warehouse", k=5)
        assert results[0].kind == _MEMORY_KIND
        assert any(r.kind == _HIT_KIND for r in results), "the code hits still follow"

    async def test_no_memory_store_injects_nothing(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        results = await pipeline.search_code("champion routing warehouse", k=5)
        assert results
        assert not any(r.kind == _MEMORY_KIND for r in results)


# --------------------------------------------------------------------------- #
# item 7 — per-hit graph enrichment (ref-joins v1.0 + signature + cap + failure)
# --------------------------------------------------------------------------- #
class TestGraphEnrichment:
    """A function/method hit carries its ref-joins + signature; enrichment is
    bounded and fails-soft."""

    async def _enrichment_corpus(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> tuple[_Indexed, LoreServer, str]:
        """Index the reflib corpus; return (indexed, server, champion_routing key)."""
        files = {
            "reflib.py": _REFLIB_SOURCE,
            "consumer.py": _CONSUMER_SOURCE,
            "tests/test_reflib.py": _TEST_REFLIB_SOURCE,
        }
        indexed, server = await _index_single(tmp_path, embedder, files=files)
        chunk = _chunk_for(server, "reflib.py", _REFLIB_SOURCE, _ENRICHMENT_SYMBOL)
        key = _expected_point_id(indexed.config.project.slug, "reflib.py", chunk)
        return indexed, server, key

    async def test_function_hit_carries_refjoins_and_signature(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server, target_key = await self._enrichment_corpus(tmp_path, embedder)

        # Independent oracle: the audited fake graph's OWN reference/test counts for
        # the target. The corpus is built so these are non-zero (a production caller
        # + a test caller) — a non-empty driver table, so an "enrichment silently
        # inert on an empty graph" bug cannot hide as 0/0.
        summary = await indexed.graph.references(_ENRICHMENT_SYMBOL)
        covering = await indexed.graph.tests_for(_ENRICHMENT_SYMBOL)
        assert summary.production_references >= 1
        assert summary.test_references >= 1
        expected_refjoin = _refjoin_line(
            summary.production_references, summary.test_references, len(covering)
        )

        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        results = await pipeline.search_code("champion routing warehouse", k=10)
        target = next(r for r in results if r.chunk_key == target_key)

        # The pipeline must JOIN the graph with the right key and render the counts
        # verbatim — a wrong join key would yield 0/0 and fail this substring.
        assert expected_refjoin in target.formatted
        # And the chunker-stamped signature rides along (an independent oracle read
        # off the producer's metadata, e.g. "(week)").
        signature = _chunk_for(server, "reflib.py", _REFLIB_SOURCE, _ENRICHMENT_SYMBOL).metadata[
            "signature"
        ]
        assert signature is not None and signature in target.formatted

    async def test_non_symbol_hit_has_no_ref_join_line(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # Enrichment is for function/method hits only. A class-header chunk (signature
        # None) carries neither the ref-join arrow nor a signature line.
        indexed, server = await _index_single(tmp_path, embedder)
        class_chunk = _chunk_for(server, "routing.py", _PY_ROUTING, "Router")
        class_key = _expected_point_id(indexed.config.project.slug, "routing.py", class_chunk)

        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        results = await pipeline.search_code("Router routes a request", k=10)
        class_result = next((r for r in results if r.chunk_key == class_key), None)
        assert class_result is not None, "the class header chunk is retrievable"
        assert _ENRICHMENT_ARROW not in class_result.formatted

    async def test_enrichment_is_capped_for_a_large_response(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # A module of many functions: a k=20 response must issue at most
        # _ENRICHMENT_CAP graph joins (top-10 by score enriched), so enrichment can
        # never fan out one graph round-trip per hit on a wide result set.
        handlers = "\n\n\n".join(
            f'def routing_handler_{i}(week):\n'
            f'    """Route handler {i}."""\n'
            f'    return week + {i}'
            for i in range(25)
        )
        indexed, server = await _index_single(
            tmp_path, embedder, files={"handlers.py": handlers}
        )
        counting = _CountingCodeGraph(
            db=indexed.db, tier_roots={_TIER: str(tmp_path)}, project_roots=[str(tmp_path)]
        )
        pipeline = _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, code_graph=counting
        )

        results = await pipeline.search_code("routing handler", k=20)
        hits = [r for r in results if r.kind == _HIT_KIND]
        enriched = [r for r in hits if _ENRICHMENT_ARROW in r.formatted]

        assert len(hits) > _ENRICHMENT_CAP, "the corpus yields more hits than the cap"
        # At most the cap is enriched, and the graph is joined at most cap times.
        assert len(enriched) <= _ENRICHMENT_CAP
        assert counting.reference_lookups <= _ENRICHMENT_CAP

    async def test_graph_raising_mid_enrichment_still_returns_the_hit(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # A graph that fails mid-enrichment must NOT drop the hit or blanket-fail the
        # search — the hit is returned, its enrichment omitted and explicitly marked.
        indexed, server, target_key = await self._enrichment_corpus(tmp_path, embedder)
        raising = _RaisingCodeGraph(
            db=indexed.db, tier_roots={_TIER: str(tmp_path)}, project_roots=[str(tmp_path)]
        )
        pipeline = _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, code_graph=raising
        )

        results = await pipeline.search_code("champion routing warehouse", k=10)
        target = next(r for r in results if r.chunk_key == target_key)

        # Still cited (the search succeeded), but enrichment annotated as unavailable.
        assert "[SOURCE:" in target.formatted
        assert _ENRICHMENT_ARROW not in target.formatted
        assert _ENRICHMENT_UNAVAILABLE in target.formatted


# --------------------------------------------------------------------------- #
# item 8 — freshness flags (annotate, never blanket-block) + bounded wait
# --------------------------------------------------------------------------- #
class TestFreshnessFlags:
    """An in-flight (dirty/embedding) chunk is flagged stale but still returned."""

    @pytest.mark.parametrize("inflight_state", [STATE_DIRTY, STATE_EMBEDDING])
    async def test_inflight_chunk_is_flagged_but_still_returned(
        self, tmp_path: Path, embedder: FakeEmbedder, inflight_state: str
    ) -> None:
        indexed, server = await _index_single(tmp_path, embedder)
        # Flip routing.py to an in-flight state AFTER indexing (its chunks are still
        # searchable — the manifest, not the store, is the freshness authority).
        await indexed.manifest.set_state(_TIER, "routing.py", inflight_state)

        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        results = await pipeline.search_code("champion routing warehouse", k=5)

        assert results, "freshness is annotate-never-block: hits still come back"
        flagged = [r for r in results if r.kind == _HIT_KIND and "routing.py" in r.formatted]
        assert flagged, "the in-flight file's chunks are still returned"
        for r in flagged:
            assert r.stale is True
            assert _STALE_MARKER in r.formatted

    async def test_indexed_chunk_is_not_flagged_stale(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(tmp_path, embedder)
        routing_row = await indexed.manifest.get(_TIER, "routing.py")
        assert routing_row is not None and routing_row.state == STATE_INDEXED

        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        results = await pipeline.search_code("champion routing warehouse", k=5)
        assert results
        for r in (r for r in results if r.kind == _HIT_KIND):
            assert r.stale is False
            assert _STALE_MARKER not in r.formatted


class TestWaitForFresh:
    """wait_for_fresh times out and serves stale-with-warning rather than hanging."""

    async def test_wait_for_fresh_times_out_and_returns(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(tmp_path, embedder)
        # routing.py stuck in 'embedding' forever — wait_for_fresh must give up.
        await indexed.manifest.set_state(_TIER, "routing.py", STATE_EMBEDDING)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        start = time.monotonic()
        results = await pipeline.search_code(
            "champion routing warehouse", k=5,
            wait_for_fresh=True, filters={"file_path": "routing.py"}, wait_timeout_s=0.5,
        )
        elapsed = time.monotonic() - start

        assert elapsed < 5.0, "bounded — it returned well within a generous ceiling"
        assert results
        assert any(r.stale for r in results if r.kind == _HIT_KIND)
        assert any(_STALE_MARKER in r.formatted for r in results if r.kind == _HIT_KIND)

    async def test_wait_for_fresh_returns_immediately_when_all_indexed(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        start = time.monotonic()
        results = await pipeline.search_code(
            "champion routing warehouse", k=5,
            wait_for_fresh=True, filters={"file_path": "routing.py"}, wait_timeout_s=5.0,
        )
        elapsed = time.monotonic() - start
        assert elapsed < 2.0, "an already-indexed file needs no waiting"
        assert results
        assert all(not r.stale for r in results if r.kind == _HIT_KIND)


# --------------------------------------------------------------------------- #
# item 9 — config-gated reranker seam (default OFF, provably not called)
# --------------------------------------------------------------------------- #
class TestConfigGatedReranker:
    """search.reranker null ⇒ seam not called; configured ⇒ candidates pass through."""

    async def test_reranker_default_off_is_not_called(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # A normal config carries no reranker; even with a reranker double injected,
        # the pipeline must NOT call it (the config, not mere presence, is the gate).
        indexed, server = await _index_single(tmp_path, embedder)
        reranker = _RecordingReranker()
        pipeline = _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, reranker=reranker
        )
        await pipeline.search_code("champion routing warehouse", k=5)
        assert reranker.calls == 0

    async def test_configured_reranker_receives_candidates_post_rrf(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # With search.reranker configured, candidates pass through the seam AFTER
        # the store's RRF fusion and BEFORE formatting — the seam sees Candidates.
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        reranker_cfg = {"url": "http://reranker.internal:8080/rerank", "model": "bge-reranker-v2"}
        server = LoreServer(_config(slug=slug, live_path=tmp_path, reranker=reranker_cfg))
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, embedder=embedder, server=server,
            reranker=reranker_cfg,
        )
        reranker = _RecordingReranker()
        pipeline = _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, reranker=reranker
        )

        results = await pipeline.search_code("champion routing warehouse", k=5)
        assert reranker.calls == 1
        assert reranker.received is not None and reranker.received, "it received the RRF candidates"
        assert all(isinstance(c, Candidate) for c in reranker.received)
        # Formatting still ran (the seam is a pass-through in the pipeline path).
        assert any(r.kind == _HIT_KIND for r in results)


# --------------------------------------------------------------------------- #
# item 10 — render-sanitiser (control chars / framing in non-fenced fields)
# --------------------------------------------------------------------------- #
class TestRenderSanitiser:
    """Control chars / framing in non-fenced fields cannot break a citation or fence."""

    async def _search_one_hostile_chunk(
        self, tmp_path: Path, embedder: FakeEmbedder, payload: dict[str, Any]
    ) -> SearchResult:
        """Upsert ONE crafted (imports-type, no enrichment) chunk and return its hit."""
        indexed, server = await _index_single(tmp_path, embedder, files={})
        from loremaster.index.records import Record

        vector = await embedder.embed_query("seed")
        record = Record(point_id=str(uuid.uuid4()), embedding_text="seed", payload=payload)
        await indexed.store.upsert([(record, vector)])
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        results = await pipeline.search_code("seed", k=5)
        assert results, "the single crafted chunk is retrievable"
        return results[0]

    @staticmethod
    def _hostile_payload(**overrides: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "tier": _TIER,
            "file_path": "pkg/normal.py",
            "identity": "normal",
            "chunk_type": "imports",  # non-symbol ⇒ no graph enrichment needed
            "line_start": 1,
            "line_end": 1,
            "content_hash": "abcdef0123456789" * 8,  # 128 hex chars
            "source_text": "import os\n",
            "signature": None,
        }
        payload.update(overrides)
        return payload

    async def test_ansi_escape_collapsed_in_citation_lines(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # An ANSI escape smuggled into file_path must not survive into the rendered
        # citation lines (it could rewrite a terminal or hide text).
        hostile = self._hostile_payload(file_path="pkg/ev\x1b]0;pwn\x07il.py")
        result = await self._search_one_hostile_chunk(tmp_path, embedder, hostile)
        assert "\x1b" not in result.formatted

    async def test_newline_injection_cannot_split_the_short_citation(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # A newline in file_path must not break the single-line [S:...] citation into
        # two lines (which would let injected text pose as a second citation).
        hostile = self._hostile_payload(file_path="pkg/evil.py\nInjected: fake line")
        result = await self._search_one_hostile_chunk(tmp_path, embedder, hostile)
        start = result.formatted.index(_SHORT_CITATION_PREFIX)
        end = result.formatted.index("]", start)
        citation = result.formatted[start : end + 1]
        assert "\n" not in citation, "the [S:...] citation must stay a single line"

    async def test_backtick_fence_breakout_stays_fenced(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # A ``` run inside source_text must not close the wrapper fence early; the
        # wrapper must open with a backtick run LONGER than any run in the source
        # (the CommonMark nesting rule).
        source = "def f():\n    return '```'\n```\nnot really a close\n"
        hostile = self._hostile_payload(chunk_type="function", source_text=source, signature="()")
        result = await self._search_one_hostile_chunk(tmp_path, embedder, hostile)
        # The source is present verbatim, wrapped in a fence longer than its own runs.
        assert source in result.formatted
        fence_lines = [
            line for line in result.formatted.splitlines() if set(line) == {"`"}
        ]
        assert fence_lines, "a bare backtick fence line must delimit the source block"
        assert max(len(line) for line in fence_lines) > _max_backtick_run(source)

    async def test_hostile_memory_line_is_sanitised(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # The memory-line path is a non-fenced field too: a memory whose text carries
        # an ANSI escape / newline must not smuggle framing into the output.
        indexed, server = await _index_single(tmp_path, embedder)
        memory_store = _FakeMemoryStore(
            [RecalledMemory(
                text="note with \x1b]0;evil\x07 and a\nnewline",
                refs=[MemoryRef(chunk_key="e" * 32)], score=0.9,
            )]
        )
        pipeline = _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, memory_store=memory_store
        )
        results = await pipeline.search_code("champion routing warehouse", k=5)
        memory_entries = [r for r in results if r.kind == _MEMORY_KIND]
        assert memory_entries
        line = memory_entries[0].formatted
        assert "\x1b" not in line
        # The injected memory renders as a single logical line (no embedded newline
        # splitting it into a fake extra result).
        assert "\n" not in line


# --------------------------------------------------------------------------- #
# item 11 — detail_level partition (auto / summary / source) survives
# --------------------------------------------------------------------------- #
class TestDetailLevel:
    """summary/source/auto partition the hits by chunk-type classification."""

    async def _pipeline(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> SearchPipeline:
        indexed, server = await _index_single(tmp_path, embedder)
        return _make_pipeline(indexed=indexed, embedder=embedder, server=server)

    async def test_summary_returns_only_summary_chunk_types(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        pipeline = await self._pipeline(tmp_path, embedder)
        # _PY_ROUTING yields imports/class (summary) + method/function (source).
        results = await pipeline.search_code("routing", k=10, detail_level="summary")
        hits = [r for r in results if r.kind == _HIT_KIND]
        assert hits, "summary chunks (imports/class) exist in this corpus"
        assert all(r.detail_level == "summary" for r in hits)

    async def test_source_returns_only_source_chunk_types(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        pipeline = await self._pipeline(tmp_path, embedder)
        results = await pipeline.search_code("routing", k=10, detail_level="source")
        hits = [r for r in results if r.kind == _HIT_KIND]
        assert hits, "source chunks (method/function) exist in this corpus"
        assert all(r.detail_level == "source" for r in hits)

    async def test_auto_returns_both_levels(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        pipeline = await self._pipeline(tmp_path, embedder)
        results = await pipeline.search_code("routing", k=10, detail_level="auto")
        levels = {r.detail_level for r in results if r.kind == _HIT_KIND}
        assert "summary" in levels
        assert "source" in levels


# --------------------------------------------------------------------------- #
# item 3 — extension hooks operate on Candidate; bare server = base defaults
# --------------------------------------------------------------------------- #
class TestExtensionHooks:
    """A FAKE extension's Candidate seams observably change output; generic = base."""

    async def _extension_pipeline(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> SearchPipeline:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        base_config = _config(slug=slug, live_path=tmp_path)
        # Merge the fake extension's config slice into this config.
        ext_config = base_config.model_copy(update={"extensions": minimal_config().extensions})
        server = LoreServer(ext_config).register_extension(FakeExtension())
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, embedder=embedder, server=server
        )
        return _make_pipeline(indexed=indexed, embedder=embedder, server=server)

    async def test_fake_extension_format_overrides_base_citation(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        pipeline = await self._extension_pipeline(tmp_path, embedder)
        results = await pipeline.search_code("routing", k=5)
        hits = [r for r in results if r.kind == _HIT_KIND]
        assert hits
        # The fake's format_result returns "FAKE: <key>" for every hit ⇒ the base
        # [SOURCE:...] citation must NOT appear (the seam-5 hook won).
        assert all(r.formatted.startswith("FAKE:") for r in hits)
        assert not any("[SOURCE:" in r.formatted for r in hits)

    async def test_fake_extension_augment_injects_a_candidate(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        pipeline = await self._extension_pipeline(tmp_path, embedder)
        # The fake's augment_candidates injects a Candidate keyed "injected" score
        # 1.0 and rerank sorts by score desc ⇒ the injected candidate leads the hits.
        results = await pipeline.search_code("routing", k=10)
        hits = [r for r in results if r.kind == _HIT_KIND]
        assert hits
        assert hits[0].formatted == "FAKE: injected"

    async def test_bare_server_uses_base_defaults(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        results = await pipeline.search_code("routing", k=10)
        hits = [r for r in results if r.kind == _HIT_KIND]
        assert hits
        assert not any(r.formatted.startswith("FAKE:") for r in hits)
        assert all("[SOURCE:" in r.formatted for r in hits)


# --------------------------------------------------------------------------- #
# item 1 — filters scope the search server-side (tier / file_path / path alias)
# --------------------------------------------------------------------------- #
class TestFilters:
    """filters scope the search to a tier / file_path, in the store's fused arms."""

    async def _two_files(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> tuple[_Indexed, LoreServer]:
        return await _index_single(
            tmp_path, embedder, files={"routing.py": _PY_ROUTING, "pricing.py": _PY_PRICING}
        )

    async def test_file_path_filter_returns_only_that_file(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await self._two_files(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        results = await pipeline.search_code(
            "anything at all", k=10, filters={"file_path": "pricing.py"}
        )
        hits = [r for r in results if r.kind == _HIT_KIND]
        assert hits, "the filtered file has chunks"
        assert all("pricing.py" in r.formatted for r in hits)
        assert not any("routing.py" in r.formatted for r in hits)

    async def test_tier_filter_returns_only_that_tier(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        hits = await pipeline.search_code("routing", k=10, filters={"tier": _TIER})
        assert [r for r in hits if r.kind == _HIT_KIND]
        # A non-existent tier scopes to nothing (the filter is applied, not ignored).
        misses = await pipeline.search_code("routing", k=10, filters={"tier": "nonexistent_tier"})
        assert [r for r in misses if r.kind == _HIT_KIND] == []

    async def test_path_alias_scopes_like_file_path(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # The public 'path' alias must translate to the canonical 'file_path' key
        # BEFORE the store query (the store's filter allow-list rejects 'path'), so
        # {"path": "pricing.py"} scopes identically to {"file_path": "pricing.py"}.
        indexed, server = await self._two_files(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        results = await pipeline.search_code(
            "anything at all", k=10, filters={"path": "pricing.py"}
        )
        hits = [r for r in results if r.kind == _HIT_KIND]
        assert hits, "the 'path' alias must translate to file_path and match chunks"
        assert all("pricing.py" in r.formatted for r in hits)
        assert not any("routing.py" in r.formatted for r in hits)
        assert 1 <= len(hits) <= 10  # sanity bound: catches a scale/sign regression


# --------------------------------------------------------------------------- #
# Runtime ExtensionContext wiring — the search seams get REAL services
# --------------------------------------------------------------------------- #
class TestRuntimeExtensionContext:
    """The search seams receive a RUNTIME ctx (real embedder/manifest/tokenizer).

    Pinned at the PIPELINE level (not via ``build_app_context`` — that server
    integration belongs to the server-wiring cycle). ``augment_candidates`` fires
    unconditionally, so it is the reliable observation point for the runtime ctx.
    """

    async def test_search_seam_ctx_carries_runtime_services(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        recorder = _CtxRecordingExtension()
        server = LoreServer(config).register_extension(recorder)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, embedder=embedder, server=server
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        await pipeline.search_code("champion routing warehouse", k=5)

        ctx = recorder.recorded_ctx
        assert ctx is not None, "the augment_candidates seam (4) must have been handed a ctx"
        # The runtime ctx carries the REAL (fake) embedder, not a None placeholder.
        assert ctx.embedder is embedder
        # And the REAL manifest + a WORKING token counter (the placeholder raises).
        assert ctx.manifest is not None
        counts = ctx.count_tokens(["a sample string"])
        assert isinstance(counts, list) and len(counts) == 1 and isinstance(counts[0], int)

