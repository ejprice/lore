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
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from _extension_helpers import FakeExtension, register_in_discovery
from _surreal_fakes import (
    FakeSurrealCodeGraph,
    FakeSurrealManifest,
    FakeSurrealStore,
    fake_surreal_trio,
)
from loremaster.config import LoreConfig
from loremaster.extension import DEFAULT_KEY_VERSION, Extension, ExtensionContext
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.manifest import STATE_DIRTY, STATE_EMBEDDING, STATE_INDEXED
from loremaster.index.records import chunk_to_record, point_id, sha512_hex
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.memory.backend import MemorySource, RecalledMemory, RecalledRef
from loremaster.search import SearchPipeline, SearchResult
from loremaster.server import LoreServer
from loremaster.store.candidate import Candidate
from loremaster.store.surreal import SurrealConnectionError, SurrealStore
from lorescribe.models import Chunk, ChunkContext
from loresigil.testing import FakeEmbedder

from loremaster import search as search_module

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
_NOTICE_KIND = "notice"
# T3 (P8d' #54 tweak): raised 2 -> 3, alongside the trailing-block reorder.
_MEMORY_INJECTION_CAP = 3
# T3: the section-label row segregating the trailing memories: block.
_MEMORY_SECTION_HEADER = "memories:"

# item 13 (S3, finding #61) — a non-auto detail_level can legitimately zero
# every code hit while injected memories still render unconditionally
# ("code-shaped query returned only memories, zero code hits, silently" —
# client-needs-consult §S3, live-reproduced). The marker is this module's own
# CONTRACT (not imported from the implementation).
_DETAIL_MISS_MARKER = "[DETAIL MISS]"

# item 10 (audit followup): bidi override/isolate/mark + zero-width + line-break
# chars OUTSIDE the C0/C1 control range the shipped sanitiser collapses — a
# hostile file_path/identity/memory text can smuggle these to visually rewrite
# (bidi), hide (zero-width), or fracture (line/paragraph separator) a rendered
# citation/memory line. One char from each distinct Unicode sub-range so the
# fix must be a genuine RANGE match, not a single-codepoint patch: BIDI
# override (U+202A-202E) + isolate (U+2066-2069) + mark (U+200E-200F);
# ZERO-WIDTH space (U+200B) + no-break space/BOM (U+FEFF); LINE/PARAGRAPH
# SEPARATOR (U+2028-2029) — the residual closed out after the initial audit.
# Sibling zero-widths flagged by that audit as backlog (efa5da7's commit
# message) and now closed out: ZWNJ (U+200C), ZWJ (U+200D), and WORD JOINER
# (U+2060) — all zero-width formatting chars that can hide characters inside
# a rendered field just like U+200B/U+FEFF above.
_BIDI_ZERO_WIDTH_AND_SEPARATOR_CHARS = (
    "\u202e",  # RIGHT-TO-LEFT OVERRIDE (bidi override sub-range)
    "\u2066",  # LEFT-TO-RIGHT ISOLATE (bidi isolate sub-range)
    "\u200e",  # LEFT-TO-RIGHT MARK (bidi mark sub-range)
    "\u200f",  # RIGHT-TO-LEFT MARK (bidi mark sub-range)
    "\u200b",  # ZERO WIDTH SPACE
    "\ufeff",  # ZERO WIDTH NO-BREAK SPACE / BOM
    "\u2028",  # LINE SEPARATOR
    "\u2029",  # PARAGRAPH SEPARATOR
    "\u200c",  # ZERO WIDTH NON-JOINER (ZWNJ)
    "\u200d",  # ZERO WIDTH JOINER (ZWJ)
    "\u2060",  # WORD JOINER
)


# item 12 (S4b, docs/design/2026-07-06-weak-match-discrimination.md) — RETIRES
# S4's fused-RRF-score floor (a rank-fusion CODE, structurally incapable of
# discriminating nonsense from real queries — §1.2) in favour of a PRE-FUSION
# cosine substrate + gated absence verdict. ADOPTED 2026-07-06 (search.py's
# own comment above ``_COSINE_SUBSTRATE_ENABLED`` carries the measured
# receipts). PARTLY DISARMED 2026-07-24 (packet 10-d): production ships the
# SUBSTRATE lit and the weak-match FLOOR at ``None``, so the per-hit
# judgement and the aggregate verdict are both dark pending per-instance
# calibration (#176/#179/#180). Most classes below ``monkeypatch`` their own
# floor to keep the LIT machinery under regression coverage for 11-ii; the
# SHIPPED state is pinned — patch-free, which is the point — by
# ``TestWeakMatchDisarmedAtTheProductionDefault``. The gate constants are
# never re-declared here; the whole POINT is that the module owns them.
_WEAK_MATCH_MARKER = "weak match"
_ABSENCE_VERDICT_MARKER = "no confident match"


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
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
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


def _backend_recalled(
    *,
    text: str,
    chunk_keys: list[str],
    score: float,
    kind: str = "fact",
    importance: float = 0.5,
) -> RecalledMemory:
    """Build a backend-vocabulary :class:`RecalledMemory` for the pipeline seam.

    The P7 cutover moves the pipeline's memory dependency onto the
    :class:`~loremaster.memory.backend.MemoryBackend` protocol, whose ``recall``
    returns :class:`~loremaster.memory.backend.RecalledMemory` value objects
    (``refs`` are versioned, drift-annotated
    :class:`~loremaster.memory.backend.RecalledRef`\\ s) — a richer shape than the
    retired store's flat note. The pipeline reads only ``.text`` / ``.score`` /
    ``.refs[].chunk_key`` off each, so this helper fills the remaining required
    wire fields with realistic, well-formed values (id via the same uuid5 shape
    production mints; a live, experiential ``operator`` source).
    """
    now = datetime.now(UTC)
    return RecalledMemory(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"memory:{text}:{','.join(chunk_keys)}")),
        text=text,
        score=score,
        kind=kind,
        importance=importance,
        refs=[
            RecalledRef(chunk_key=key, key_version=DEFAULT_KEY_VERSION, drifted=False)
            for key in chunk_keys
        ],
        source=MemorySource(kind="operator"),
        valid_from=now,
        created_at=now,
    )


class _FakeMemoryBackend:
    """A minimal, backend-shaped recall double for the pipeline's memory seam (P7).

    The pipeline now consumes the :class:`~loremaster.memory.backend.MemoryBackend`
    protocol: it calls ``recall(query, *, k=...)`` and reads
    :class:`~loremaster.memory.backend.RecalledMemory` value objects. This double
    returns a fixed, score-ordered list so the memory-boost (item 4) and visible
    injection (item 5) behaviours stay deterministic without a live
    embedder/SurrealDB. (The full backend contract is pinned in
    ``test_memory_backend.py``; here only the pipeline's CONSUMPTION of the seam —
    that it calls ``recall`` and honours the returned refs/score/text — matters.)
    """

    def __init__(self, recalled: list[RecalledMemory]) -> None:
        self._recalled = recalled
        self.recall_calls = 0

    async def recall(self, query: str, *, k: int = 5) -> list[RecalledMemory]:
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

        # k bounds the number of store HITS returned (no memory store ⇒ no
        # extra visible-memory entries). item 12b's aggregate weak-match
        # notice is metadata ABOUT the hits, not itself a store hit, so it is
        # excluded from the k-ceiling count (same non-inflation rule as a
        # memory entry) -- checked separately below.
        results = await pipeline.search_code("anything", k=2)
        hits = [r for r in results if r.kind == _HIT_KIND]
        assert len(hits) <= 2
        assert all(r.kind in (_HIT_KIND, _NOTICE_KIND) for r in results)


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
        memory_store = _FakeMemoryBackend(
            [
                _backend_recalled(
                    text="the pricing/routing correction",
                    chunk_keys=[boost_target.chunk_key],
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
        memory_store = _FakeMemoryBackend(
            [
                _backend_recalled(
                    text="boost both leaders",
                    chunk_keys=list(top_two),
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
        # No memory store ⇒ no boost AND no injected memory entries (item
        # 12b's aggregate weak-match notice is unrelated to memory injection
        # and may legitimately co-occur, so only MEMORY_KIND is ruled out here).
        assert not any(r.kind == _MEMORY_KIND for r in results)


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
            memory_store=_FakeMemoryBackend(recalled),
        )

    async def test_matching_memory_injected_as_visible_provenance_line(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        ref_key = "11111111-1111-5111-8111-111111111111"
        memory_text = "champion_routing lives in routing.py, not pricing.py"
        pipeline = await self._pipeline_with_memories(
            tmp_path, embedder,
            [_backend_recalled(text=memory_text, chunk_keys=[ref_key], score=0.9)],
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
            [_backend_recalled(
                text="a project convention note",
                chunk_keys=["22222222-2222-5222-8222-222222222222"],
                score=0.9,
            )],
        )
        results = await pipeline.search_code("champion routing warehouse", k=5)
        memory_entries = [r for r in results if r.kind == _MEMORY_KIND]
        assert memory_entries
        for entry in memory_entries:
            assert "[SOURCE:" not in entry.formatted
            assert _SHORT_CITATION_PREFIX not in entry.formatted

    async def test_injection_capped_at_three_by_score(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # Four matching memories recalled; only the THREE highest-scored are
        # injected (a deterministic cap, raised 2 -> 3 by T3), in
        # descending-score order.
        recalled = [
            _backend_recalled(text="mem-high", chunk_keys=["a" * 32], score=0.95),
            _backend_recalled(text="mem-mid", chunk_keys=["b" * 32], score=0.80),
            _backend_recalled(text="mem-low", chunk_keys=["c" * 32], score=0.60),
            _backend_recalled(text="mem-lowest", chunk_keys=["e" * 32], score=0.50),
        ]
        pipeline = await self._pipeline_with_memories(tmp_path, embedder, recalled)

        results = await pipeline.search_code("champion routing warehouse", k=5)
        memory_texts = [r.formatted for r in results if r.kind == _MEMORY_KIND]

        assert len(memory_texts) == _MEMORY_INJECTION_CAP
        # The top-3 by score, in order; the lowest-score memory is dropped.
        assert "mem-high" in memory_texts[0]
        assert "mem-mid" in memory_texts[1]
        assert "mem-low" in memory_texts[2] and "mem-lowest" not in memory_texts[2]
        assert all("mem-lowest" not in text for text in memory_texts)

    async def test_injected_memories_render_after_hits_behind_a_memories_header(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # T3 contract decision (P8d' #54, reversing the earlier lead-first
        # design): memory noise crowded out code hits under a tight budget
        # (feedback: "initial searches returned memory entries"). The ranked
        # code hits now render FIRST; injected memories are segregated behind
        # a trailing ``memories:`` header so they never masquerade as part of
        # the code-hit list.
        pipeline = await self._pipeline_with_memories(
            tmp_path, embedder,
            [_backend_recalled(
                text="a trailing note",
                chunk_keys=["d" * 32], score=0.9,
            )],
        )
        results = await pipeline.search_code("champion routing warehouse", k=5)
        kinds = [r.kind for r in results]

        assert _HIT_KIND in kinds, "the code hits must still be present"
        last_hit_index = max(i for i, kind in enumerate(kinds) if kind == _HIT_KIND)
        header_index = next(
            i for i, r in enumerate(results) if r.formatted == _MEMORY_SECTION_HEADER
        )
        memory_index = next(i for i, kind in enumerate(kinds) if kind == _MEMORY_KIND)

        assert last_hit_index < header_index, "every hit must precede the memories: header"
        assert header_index < memory_index, "the header must lead the memory entries"

    async def test_memory_cap_elision_is_announced(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # T3: memory hits beyond the (raised) cap are not silently dropped --
        # a counted notice announces how many matching memories were not shown.
        recalled = [
            _backend_recalled(text="mem-1", chunk_keys=["1" * 32], score=0.95),
            _backend_recalled(text="mem-2", chunk_keys=["2" * 32], score=0.90),
            _backend_recalled(text="mem-3", chunk_keys=["3" * 32], score=0.85),
            _backend_recalled(text="mem-4", chunk_keys=["4" * 32], score=0.80),
        ]
        pipeline = await self._pipeline_with_memories(tmp_path, embedder, recalled)

        results = await pipeline.search_code("champion routing warehouse", k=5)
        notices = [r for r in results if r.kind == _NOTICE_KIND]

        assert notices, "a memory recall exceeding the injection cap must announce it"
        assert any("+1" in n.formatted for n in notices), (
            f"expected the elided count (+1, one memory beyond the cap of "
            f"{_MEMORY_INJECTION_CAP}) named in a notice; got {notices!r}"
        )

    async def test_no_memory_store_injects_nothing(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        results = await pipeline.search_code("champion routing warehouse", k=5)
        assert results
        assert not any(r.kind == _MEMORY_KIND for r in results)
        assert not any(r.formatted == _MEMORY_SECTION_HEADER for r in results), (
            "no memories: header without a memory store"
        )


class _DenyingMemoryBackend:
    """A memory backend whose ``recall`` DENIES with :class:`~loremaster.governed.GovernedDenied`
    — the FORK-D1 fixture (packet 63a-ii). Since the 63a retrofit memory is governed, and
    ``search_code``'s enrichment recall carries NO caller ``Subject`` until 63b, the boost recall
    is refused. ``recall_calls`` records that the pipeline still ATTEMPTED the boost (so the notice
    is the deny doing the work, never a store that was never called)."""

    def __init__(self) -> None:
        self.recall_calls = 0

    async def recall(self, query: str, *, k: int = 5) -> list[RecalledMemory]:
        from loremaster.governed import GovernedDenied

        self.recall_calls += 1
        raise GovernedDenied("identity-less recall of the fleet's governed memory (test)")


class TestMemoryBoostWithheldNotice:
    """FORK-D1 (design §10.7-Y): a DENIED memory boost is NAMED in the render — one derived line, a
    Leg-1 fact — never a silent ``[]`` (the #131 shape). The code search still succeeds (a governed
    memory boost is an enrichment, never a hard dependency of code search)."""

    async def test_a_denied_boost_is_named_in_the_render(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        from loremaster.search import _MEMORY_WITHHELD_NOTICE

        indexed, server = await _index_single(tmp_path, embedder)
        denying = _DenyingMemoryBackend()
        pipeline = _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, memory_store=denying
        )
        results = await pipeline.search_code("champion routing warehouse", k=5)
        # The boost was ATTEMPTED (so the notice reflects a real deny, not a never-called store)...
        assert denying.recall_calls == 1, "search_code must still attempt the memory boost"
        # ...the code search still SUCCEEDED (the boost degrades, never fails the search)...
        assert any(r.kind == _HIT_KIND for r in results), "a denied boost must not fail code search"
        # ...and the withheld boost is NAMED in exactly ONE render line (a fact, never a silent []).
        withheld = [
            r for r in results if r.kind == _NOTICE_KIND and _MEMORY_WITHHELD_NOTICE in r.formatted
        ]
        notices = [r.formatted for r in results if r.kind == _NOTICE_KIND]
        assert len(withheld) == 1, (
            f"a denied memory boost must be NAMED in ONE render line "
            f"({_MEMORY_WITHHELD_NOTICE!r}); a silent [] is the #131 shape. notices={notices}"
        )
        # Nothing was recalled, so there is no memories: block — the notice is the only memory signal.
        assert not any(r.kind == _MEMORY_KIND for r in results)

    async def test_a_healthy_empty_recall_names_no_withheld_boost(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # POSITIVE CONTROL: a memory store that returns [] WITHOUT denying shows NO withheld notice
        # — so the notice above is the DENY doing the work, never a line that always fires on an
        # empty boost (a fixture that could not distinguish deny from empty would be decoration).
        from loremaster.search import _MEMORY_WITHHELD_NOTICE

        indexed, server = await _index_single(tmp_path, embedder)
        pipeline = _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, memory_store=_FakeMemoryBackend([])
        )
        results = await pipeline.search_code("champion routing warehouse", k=5)
        assert any(r.kind == _HIT_KIND for r in results)
        assert not any(
            _MEMORY_WITHHELD_NOTICE in r.formatted for r in results if r.kind == _NOTICE_KIND
        ), "a healthy empty recall must NOT emit the withheld-boost notice (positive control)"


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

    @pytest.mark.parametrize("line_break_char", ("\u2028", "\u2029"))
    async def test_line_and_paragraph_separator_cannot_split_the_short_citation(
        self, tmp_path: Path, embedder: FakeEmbedder, line_break_char: str
    ) -> None:
        # U+2028 LINE SEPARATOR / U+2029 PARAGRAPH SEPARATOR are genuine line
        # breaks to a bidi-aware terminal or a browser-rendered UI even though
        # they are neither "\n" nor a C0/C1 control — a hostile file_path must
        # not use one to fracture the single-line [S:...] citation into two
        # (which would let injected text pose as a second citation), the same
        # invariant the plain-newline injection test above pins for "\n".
        hostile = self._hostile_payload(
            file_path=f"pkg/evil.py{line_break_char}Injected: fake line"
        )
        result = await self._search_one_hostile_chunk(tmp_path, embedder, hostile)
        start = result.formatted.index(_SHORT_CITATION_PREFIX)
        end = result.formatted.index("]", start)
        citation = result.formatted[start : end + 1]
        assert line_break_char not in citation, (
            "the [S:...] citation must stay a single line"
        )
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
        memory_store = _FakeMemoryBackend(
            [_backend_recalled(
                text="note with \x1b]0;evil\x07 and a\nnewline",
                chunk_keys=["e" * 32], score=0.9,
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

    @pytest.mark.parametrize("hostile_char", _BIDI_ZERO_WIDTH_AND_SEPARATOR_CHARS)
    async def test_bidi_and_zero_width_collapsed_in_citation_lines(
        self, tmp_path: Path, embedder: FakeEmbedder, hostile_char: str
    ) -> None:
        # A bidi override/isolate/mark can visually rewrite a rendered citation
        # line in a bidi-aware terminal/UI, a zero-width char can hide characters
        # inside it, and a line/paragraph separator can fracture it — none of
        # these is a C0/C1 control, so the shipped sanitiser (which only
        # collapses \x00-\x1f/\x7f-\x9f) lets them through untouched.
        hostile = self._hostile_payload(file_path=f"pkg/ev{hostile_char}il.py")
        result = await self._search_one_hostile_chunk(tmp_path, embedder, hostile)
        assert hostile_char not in result.formatted

    async def test_zero_width_no_break_space_stripped_from_memory_line(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # The memory-line path is a non-fenced field too: U+FEFF (ZERO WIDTH
        # NO-BREAK SPACE / BOM) smuggled into memory text must not survive into
        # the visible injected line.
        indexed, server = await _index_single(tmp_path, embedder)
        memory_store = _FakeMemoryBackend(
            [_backend_recalled(
                text="note with a \ufeffhidden marker",
                chunk_keys=["f" * 32], score=0.9,
            )]
        )
        pipeline = _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, memory_store=memory_store
        )
        results = await pipeline.search_code("champion routing warehouse", k=5)
        memory_entries = [r for r in results if r.kind == _MEMORY_KIND]
        assert memory_entries
        assert "\ufeff" not in memory_entries[0].formatted

    async def test_fenced_source_keeps_bidi_and_zero_width_verbatim(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # The fenced source block is CONTENT, not framing: a bidi override, a
        # zero-width space, a bidi mark, a line/paragraph separator, ZWNJ/ZWJ,
        # and WORD JOINER embedded in source_text are all preserved verbatim
        # inside the fence — the extended sanitiser range must not overreach
        # into the fenced body.
        source = "def f():\n    return '\u202e\u200b\u200e\u200f\u2028\u2029\u200c\u200d\u2060 evil'\n"
        hostile = self._hostile_payload(chunk_type="function", source_text=source, signature="()")
        result = await self._search_one_hostile_chunk(tmp_path, embedder, hostile)
        assert source in result.formatted


# --------------------------------------------------------------------------- #
# item 12 (S4) — weak-match banding: per-hit flag + aggregate all-weak notice
# --------------------------------------------------------------------------- #
class _FixedCandidatesStore(FakeSurrealStore):
    """A store double whose ``hybrid_search`` returns a FIXED candidate list.

    Lets a weak-match test pin an EXACT ``candidate.vector_cosine`` directly
    (relative to :data:`_COSINE_WEAK_MATCH_FLOOR`) instead of reverse-
    engineering the real RRF fusion / HNSW cosine math to land a value on a
    specific side of a floor. (S4's retired ``_SEARCH_SCORE_FLOOR`` cross-ref
    corrected — S4b audit finding #4: the store now pins ``vector_cosine``,
    not the retired fused ``score``.)
    """

    def __init__(self, *, dim: int, db: Any, candidates: list[Candidate]) -> None:
        super().__init__(dim=dim, db=db)
        self._candidates = candidates

    async def hybrid_search(
        self,
        *,
        query_vector: list[float],
        query_text: str,
        k: int,
        filters: dict[str, str] | None = None,
    ) -> list[Candidate]:
        return list(self._candidates[:k])


def _score_candidate(
    key: str,
    score: float,
    *,
    file_path: str = "pkg/mod.py",
    chunk_type: str = "function",
    vector_cosine: float | None = None,
    identity: str = "some_function",
    ident_text: str = "some_function",
) -> Candidate:
    """A well-formed candidate at an exact, caller-chosen score and chunk type.

    ``chunk_type="function"`` (the default) classifies ``"source"``;
    ``chunk_type="imports"`` classifies ``"summary"`` (see
    ``LoreServer._base_classify_detail``'s ``_BASE_SUMMARY_CHUNK_TYPES``).
    ``signature=None`` keeps the candidate out of graph enrichment (item 7) so
    these tests need no code-graph double. ``vector_cosine`` (S4b, docs/design/
    2026-07-06-weak-match-discrimination.md) is the ``_FixedCandidatesStore``
    cosine knob — ``None`` (the default) exercises the "no substrate data"
    path; a caller-chosen float pins an exact cosine for the weak-match /
    absence-verdict machinery without reverse-engineering real HNSW math.
    ``ident_text`` backs the verbatim-identifier-anchor carve-out (D3).
    """
    return Candidate(
        key=key,
        score=score,
        payload={
            "tier": _TIER,
            "file_path": file_path,
            "identity": identity,
            "chunk_type": chunk_type,
            "line_start": 1,
            "line_end": 2,
            "content_hash": "0" * 128,
            "source_text": "def some_function():\n    pass\n",
            "signature": None,
            "ident_text": ident_text,
        },
        origin="fused",
        vector_cosine=vector_cosine,
    )


class TestCosineWeakMatchDark:
    """The dark code path still works when EXPLICITLY forced dark.

    These tests keep the EXPLICIT forcing under coverage: an operator (or a
    packet) setting ``_COSINE_SUBSTRATE_ENABLED=False`` /
    ``_COSINE_WEAK_MATCH_FLOOR=None`` must get zero substrate line, zero
    per-hit flag and zero aggregate verdict, regardless of how low a
    candidate's ``vector_cosine`` is.

    History, because the monkeypatching here reads oddly without it: dark was
    the production default pre-adoption (this class then patched nothing);
    the 2026-07-06 survey re-run lit both gates, at which point the patches
    were added; packet 10-d (2026-07-24) then darkened the FLOOR again on
    every instance — so the floor patches below now re-assert what the module
    already ships, while the ``_COSINE_SUBSTRATE_ENABLED=False`` patch still
    forces a genuinely non-default state. What the SHIPPED constants do is
    pinned patch-free by ``TestWeakMatchDisarmedAtTheProductionDefault``;
    this class must never be read as evidence about them.
    """

    async def _pipeline(
        self, tmp_path: Path, embedder: FakeEmbedder, candidates: list[Candidate]
    ) -> SearchPipeline:
        indexed, server = await _index_single(tmp_path, embedder, files={})
        store = _FixedCandidatesStore(dim=embedder.dim, db=indexed.db, candidates=candidates)
        return _make_pipeline(indexed=indexed, embedder=embedder, server=server, store=store)

    async def test_no_substrate_line_regardless_of_cosine(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_SUBSTRATE_ENABLED", False)
        candidate = _score_candidate("k1", 0.03, vector_cosine=0.9)
        pipeline = await self._pipeline(tmp_path, embedder, [candidate])

        results = await pipeline.search_code("anything", k=5)

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert "sim " not in hits[0].formatted

    async def test_no_weak_flag_regardless_of_how_low_the_cosine_is(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", None)
        near_zero_cosine = _score_candidate("k1", 0.03, vector_cosine=-1.0)
        pipeline = await self._pipeline(tmp_path, embedder, [near_zero_cosine])

        results = await pipeline.search_code("anything", k=5)

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert _WEAK_MATCH_MARKER not in hits[0].formatted

    async def test_no_absence_verdict_even_when_every_hit_is_weak_cosine(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", None)
        weak_a = _score_candidate("k1", 0.03, vector_cosine=-1.0, file_path="pkg/a.py")
        weak_b = _score_candidate("k2", 0.02, vector_cosine=-1.0, file_path="pkg/b.py")
        pipeline = await self._pipeline(tmp_path, embedder, [weak_a, weak_b])

        results = await pipeline.search_code("anything", k=5)

        notices = [r for r in results if r.kind == _NOTICE_KIND]
        assert not any(_ABSENCE_VERDICT_MARKER in n.formatted for n in notices)


class TestCosineSubstrateLit:
    """With ``_COSINE_SUBSTRATE_ENABLED`` measured on (D1), every hit with a

    captured cosine renders the compact always-on magnitude; a hit with no
    cosine (an older store / test double) renders nothing extra.
    """

    async def _pipeline(
        self, tmp_path: Path, embedder: FakeEmbedder, candidates: list[Candidate]
    ) -> SearchPipeline:
        indexed, server = await _index_single(tmp_path, embedder, files={})
        store = _FixedCandidatesStore(dim=embedder.dim, db=indexed.db, candidates=candidates)
        return _make_pipeline(indexed=indexed, embedder=embedder, server=server, store=store)

    async def test_renders_the_compact_magnitude_when_cosine_is_present(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_SUBSTRATE_ENABLED", True)
        candidate = _score_candidate("k1", 0.03, vector_cosine=0.87)
        pipeline = await self._pipeline(tmp_path, embedder, [candidate])

        results = await pipeline.search_code("anything", k=5)

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert "sim 0.87" in hits[0].formatted

    async def test_renders_nothing_extra_when_cosine_is_absent(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_SUBSTRATE_ENABLED", True)
        candidate = _score_candidate("k1", 0.03, vector_cosine=None)
        pipeline = await self._pipeline(tmp_path, embedder, [candidate])

        results = await pipeline.search_code("anything", k=5)

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert "sim " not in hits[0].formatted


class TestCosineWeakMatchLit:
    """With ``_COSINE_WEAK_MATCH_FLOOR`` measured (D2), a per-hit weak flag

    fires unconditionally below the floor — no verbatim-anchor carve-out
    here; that carve-out gates the AGGREGATE verdict only (D3).
    """

    _FLOOR = 0.5

    async def _pipeline(
        self,
        tmp_path: Path,
        embedder: FakeEmbedder,
        candidates: list[Candidate],
        *,
        memory_store: Any | None = None,
    ) -> SearchPipeline:
        indexed, server = await _index_single(tmp_path, embedder, files={})
        store = _FixedCandidatesStore(dim=embedder.dim, db=indexed.db, candidates=candidates)
        return _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, store=store,
            memory_store=memory_store,
        )

    async def test_cosine_below_floor_is_flagged(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        weak = _score_candidate("k1", 0.03, vector_cosine=self._FLOOR - 0.01)
        pipeline = await self._pipeline(tmp_path, embedder, [weak])

        results = await pipeline.search_code("anything", k=5)

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert _WEAK_MATCH_MARKER in hits[0].formatted

    async def test_cosine_above_floor_is_not_flagged(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        confident = _score_candidate("k1", 0.03, vector_cosine=self._FLOOR + 0.01)
        pipeline = await self._pipeline(tmp_path, embedder, [confident])

        results = await pipeline.search_code("anything", k=5)

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert _WEAK_MATCH_MARKER not in hits[0].formatted

    async def test_cosine_exactly_at_the_floor_is_not_flagged(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Boundary: the floor itself reads as confident (strict less-than),
        # mirroring S4's own retired convention.
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        at_floor = _score_candidate("k1", 0.03, vector_cosine=self._FLOOR)
        pipeline = await self._pipeline(tmp_path, embedder, [at_floor])

        results = await pipeline.search_code("anything", k=5)

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert _WEAK_MATCH_MARKER not in hits[0].formatted

    async def test_missing_cosine_is_never_flagged(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        no_cosine = _score_candidate("k1", 0.03, vector_cosine=None)
        pipeline = await self._pipeline(tmp_path, embedder, [no_cosine])

        results = await pipeline.search_code("anything", k=5)

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert _WEAK_MATCH_MARKER not in hits[0].formatted

    async def test_memory_and_notice_entries_are_never_banded(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A recalled memory can carry ANY score and a notice entry always
        # carries score=0.0 — neither may ever be mistaken for a weak CODE
        # hit (only kind=="hit" passes through the per-hit check).
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        weak = _score_candidate("k1", 0.03, vector_cosine=self._FLOOR - 0.01)
        memory_store = _FakeMemoryBackend(
            [_backend_recalled(text="a low-score memory", chunk_keys=[], score=0.0001)]
        )
        pipeline = await self._pipeline(tmp_path, embedder, [weak], memory_store=memory_store)

        results = await pipeline.search_code("anything", k=5)

        memory_entries = [r for r in results if r.kind == _MEMORY_KIND]
        notice_entries = [r for r in results if r.kind == _NOTICE_KIND]
        assert memory_entries, "the recalled memory must still be injected"
        assert not any(_WEAK_MATCH_MARKER in r.formatted for r in memory_entries)
        header = next(r for r in notice_entries if r.formatted == _MEMORY_SECTION_HEADER)
        assert _WEAK_MATCH_MARKER not in header.formatted


class TestCosineAbsenceVerdictLit:
    """With ``_COSINE_WEAK_MATCH_FLOOR`` measured (D2), the aggregate absence

    verdict fires iff the MAX cosine among shown hits is below the floor AND
    no shown hit carries a verbatim-identifier anchor (D3).
    """

    _FLOOR = 0.5

    async def _pipeline(
        self,
        tmp_path: Path,
        embedder: FakeEmbedder,
        candidates: list[Candidate],
        *,
        memory_store: Any | None = None,
    ) -> SearchPipeline:
        indexed, server = await _index_single(tmp_path, embedder, files={})
        store = _FixedCandidatesStore(dim=embedder.dim, db=indexed.db, candidates=candidates)
        return _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, store=store,
            memory_store=memory_store,
        )

    async def test_all_weak_hits_carry_the_absence_verdict(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        weak_a = _score_candidate(
            "k1", 0.03, vector_cosine=self._FLOOR - 0.01, file_path="pkg/a.py",
            identity="pkg.a.weak_fn", ident_text="weak_fn",
        )
        weak_b = _score_candidate(
            "k2", 0.02, vector_cosine=self._FLOOR - 0.2, file_path="pkg/b.py",
            identity="pkg.b.other_fn", ident_text="other_fn",
        )
        pipeline = await self._pipeline(tmp_path, embedder, [weak_a, weak_b])

        results = await pipeline.search_code("something unrelated", k=5)

        notices = [r for r in results if r.kind == _NOTICE_KIND]
        notice = next((n for n in notices if _ABSENCE_VERDICT_MARKER in n.formatted), None)
        assert notice is not None, f"expected an absence verdict; got notices={notices!r}"
        # weak_a is BOTH the fused-order top hit AND the max-cosine pair here
        # (0.49 > 0.30) -- the coincidental case where the two identities
        # happen to agree. See the finding #76 tests below in this class for
        # the case where they diverge.
        assert "pkg.a.weak_fn" in notice.formatted

    async def test_nearest_indexed_names_the_max_cosine_pair_not_the_top_fused_pair(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Finding #76 (live repro, tester-sonnet): the fused-order TOP hit is
        NOT always the max-cosine candidate. Pre-fix, ``nearest`` was
        hardcoded to ``code_pairs[0]`` (the top-fused hit) while
        ``best_cosine`` was independently ``max(cosines)`` over every
        candidate -- so the rendered sentence bound a similarity number to
        the WRONG identity whenever the two diverged. Here the true
        max-cosine candidate sits at fused positions 2 and 3 (behind two
        weaker-cosine hits ranked ahead of it by RRF) -- the exact shape of
        the finding's live repro, where the max-cosine candidate was very
        likely one of the 12 hits budget-elided server-side and never shown.
        This test lives at the pipeline layer (pre-budget, per search.py's
        own step-9 placement) -- server-side budget elision of the named
        candidate is a separate, already-covered concern (finding #71
        machinery, test_mcp_server.py's TestSearchParamsCutBudgetAndTeachingMiss,
        decoupled from this function by the stable marker constant).
        """
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        top_fused = _score_candidate(
            "k1", 0.04, vector_cosine=self._FLOOR - 0.30, file_path="pkg/a.py",
            identity="pkg.a.top_fused_fn", ident_text="top_fused_fn",
        )
        second = _score_candidate(
            "k2", 0.03, vector_cosine=self._FLOOR - 0.20, file_path="pkg/b.py",
            identity="pkg.b.second_fn", ident_text="second_fn",
        )
        max_cosine_but_low_fused_rank = _score_candidate(
            "k3", 0.02, vector_cosine=self._FLOOR - 0.01, file_path="pkg/c.py",
            identity="pkg.c.max_cosine_fn", ident_text="max_cosine_fn",
        )
        fourth = _score_candidate(
            "k4", 0.01, vector_cosine=self._FLOOR - 0.10, file_path="pkg/d.py",
            identity="pkg.d.fourth_fn", ident_text="fourth_fn",
        )
        pipeline = await self._pipeline(
            tmp_path, embedder,
            [top_fused, second, max_cosine_but_low_fused_rank, fourth],
        )

        results = await pipeline.search_code("something unrelated", k=5)

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert len(hits) == 4
        # Composition: every individual hit still carries its OWN per-hit
        # weak-match flag (item 12b), independent of the aggregate verdict.
        assert all(_WEAK_MATCH_MARKER in hit.formatted for hit in hits)

        notices = [r for r in results if r.kind == _NOTICE_KIND]
        notice = next((n for n in notices if _ABSENCE_VERDICT_MARKER in n.formatted), None)
        assert notice is not None, f"expected an absence verdict; got notices={notices!r}"
        # The rendered similarity number and the rendered identity must
        # describe the SAME candidate -- the one that actually holds the
        # maximum cosine (0.49, "pkg.c.max_cosine_fn") -- never the
        # fused-order top hit's identity ("pkg.a.top_fused_fn", cosine 0.20).
        assert "0.49" in notice.formatted
        assert "pkg.c.max_cosine_fn" in notice.formatted
        assert "pkg.a.top_fused_fn" not in notice.formatted, (
            "the notice must not name the fused-order top hit's identity "
            "when a different candidate actually produced best_cosine"
        )

    async def test_coincidental_match_notice_is_byte_identical_to_the_template(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When the fused-order top hit IS the max-cosine pair (no divergence
        to resolve), the rendered notice must be byte-for-byte what the
        module's own template produces for that single candidate -- proving
        the finding #76 fix changes WHICH candidate is selected, never the
        render's shape, in the case that was already correct pre-fix.
        """
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        top_fused_and_max_cosine = _score_candidate(
            "k1", 0.04, vector_cosine=self._FLOOR - 0.01, file_path="pkg/a.py",
            identity="pkg.a.weak_fn", ident_text="weak_fn",
        )
        weaker = _score_candidate(
            "k2", 0.03, vector_cosine=self._FLOOR - 0.20, file_path="pkg/b.py",
            identity="pkg.b.other_fn", ident_text="other_fn",
        )
        pipeline = await self._pipeline(
            tmp_path, embedder, [top_fused_and_max_cosine, weaker]
        )

        results = await pipeline.search_code("something unrelated", k=5)

        notices = [r for r in results if r.kind == _NOTICE_KIND]
        notice = next((n for n in notices if _ABSENCE_VERDICT_MARKER in n.formatted), None)
        assert notice is not None

        expected = search_module._COSINE_ABSENCE_VERDICT_TEMPLATE.format(
            best_cosine=self._FLOOR - 0.01, floor=self._FLOOR, nearest="pkg.a.weak_fn"
        )
        assert notice.formatted == expected

    async def test_mixed_weak_and_confident_hits_no_absence_verdict(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        weak = _score_candidate("k1", 0.03, vector_cosine=self._FLOOR - 0.01, file_path="pkg/a.py")
        confident = _score_candidate(
            "k2", 0.02, vector_cosine=self._FLOOR + 0.1, file_path="pkg/b.py"
        )
        pipeline = await self._pipeline(tmp_path, embedder, [confident, weak])

        results = await pipeline.search_code("anything", k=5)

        notices = [r for r in results if r.kind == _NOTICE_KIND]
        assert not any(_ABSENCE_VERDICT_MARKER in n.formatted for n in notices)

    async def test_verbatim_identifier_anchor_suppresses_the_verdict(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # D3: even with every shown hit weak-cosine, an exact identifier
        # lookup (the query pastes a symbol name verbatim) must NOT be told
        # "no confident match" — that would be a confident-wrong channel
        # aimed at the client's most confident queries.
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        weak = _score_candidate(
            "k1", 0.03, vector_cosine=self._FLOOR - 0.01,
            identity="pkg.OriginValidationMiddleware",
            ident_text="OriginValidationMiddleware",
        )
        pipeline = await self._pipeline(tmp_path, embedder, [weak])

        results = await pipeline.search_code("find OriginValidationMiddleware please", k=5)

        notices = [r for r in results if r.kind == _NOTICE_KIND]
        assert not any(_ABSENCE_VERDICT_MARKER in n.formatted for n in notices)

    async def test_memory_entries_never_feed_the_absence_verdict(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        weak = _score_candidate("k1", 0.03, vector_cosine=self._FLOOR - 0.01)
        memory_store = _FakeMemoryBackend(
            [_backend_recalled(text="a memory that looks confident", chunk_keys=[], score=0.99)]
        )
        pipeline = await self._pipeline(tmp_path, embedder, [weak], memory_store=memory_store)

        results = await pipeline.search_code("anything", k=5)

        # The verdict still fires off the (weak) code hit alone — a
        # high-scored MEMORY entry must never be mistaken for a confident
        # code hit and suppress it.
        notices = [r for r in results if r.kind == _NOTICE_KIND]
        assert any(_ABSENCE_VERDICT_MARKER in n.formatted for n in notices)

    async def test_no_hits_produces_no_absence_verdict(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        pipeline = await self._pipeline(tmp_path, embedder, [])

        results = await pipeline.search_code("anything", k=5)

        assert results == []

    async def test_hostile_identity_in_nearest_indexed_is_sanitised(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # S4b audit finding #6/#5 (REPORT-slate-audit-searchstore.md): "nearest
        # indexed" renders a STORED identity verbatim (D3's Opus addition) —
        # repo law: any NEW render of stored free text needs a hostile
        # fixture (newlines forging a second line, a row-shaped table
        # forgery, backtick runs), not just a claim that ``_sanitise_line``
        # (search.py:418) already covers it. Positively asserts the
        # SANITISED (collapsed-to-a-single-space) form, not merely the
        # absence of raw control bytes — Python's ``!r`` template formatting
        # already escapes raw control/format characters on its own (verified
        # empirically), so a bare "control byte absent" assertion would pass
        # even with ``_sanitise_line`` deleted; asserting the collapsed text
        # only holds when the sanitiser actually ran.
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        hostile_identity = "evil_fn\x1bmiddle\n|forged|row|\n```fenced```"
        weak = _score_candidate(
            "k1", 0.03, vector_cosine=self._FLOOR - 0.01,
            identity=hostile_identity, ident_text="evil_fn",
        )
        pipeline = await self._pipeline(tmp_path, embedder, [weak])

        results = await pipeline.search_code("something unrelated", k=5)

        notices = [r for r in results if r.kind == _NOTICE_KIND]
        notice = next((n for n in notices if _ABSENCE_VERDICT_MARKER in n.formatted), None)
        assert notice is not None
        assert len(notice.formatted.splitlines()) == 1, (
            "the hostile identity must not forge an extra line in the notice"
        )
        assert "evil_fn middle |forged|row| ```fenced```" in notice.formatted
        # Would appear if the raw hostile bytes reached ``!r`` unsanitised
        # (repr's OWN escaping renders a real ESC/LF as this visible text).
        assert "\\x1b" not in notice.formatted
        assert "\\n" not in notice.formatted

    async def test_bare_word_overlap_no_longer_suppresses_the_verdict(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # D3 fix (docs/design/2026-07-06-weak-match-discrimination.md §7.2 D3,
        # search_score_survey_summary.md 2026-07-06): "client" is a bare
        # English word, not a pasted identifier -- it must not suppress the
        # verdict just because it happens to overlap a real identifier's
        # derived ident_text (identity "Client" + file stem "client" from
        # ``pkg/client.py``, exactly how ``SurrealStore._derive_ident_text``
        # would build it). Measured defect: 9/15 nonsense queries anchored
        # via exactly this bare-word-overlap pattern before this fix.
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        weak = _score_candidate(
            "k1", 0.03, vector_cosine=self._FLOOR - 0.01,
            file_path="pkg/client.py", identity="Client", ident_text="Client client",
        )
        pipeline = await self._pipeline(tmp_path, embedder, [weak])

        results = await pipeline.search_code(
            "rate limiting middleware per client IP address", k=5
        )

        notices = [r for r in results if r.kind == _NOTICE_KIND]
        assert any(_ABSENCE_VERDICT_MARKER in n.formatted for n in notices)


class TestIdentifierShapedQueryTokens:
    """D3 fix: query-side token admissibility for the verbatim-identifier
    anchor. Measured defect (search_score_survey run, 2026-07-06,
    search_score_survey_summary.md): 9/15 nonsense queries anchored via a
    bare common-English word before this fix, capping nonsense catch at 40%
    against D2's 60% adoption bar.
    """

    def test_underscore_bearing_token_is_shaped(self) -> None:
        assert "action_confirm" in search_module._identifier_shaped_query_tokens(
            "find action_confirm please"
        )

    def test_dotted_chain_segments_are_shaped_even_without_underscore_or_case_change(
        self,
    ) -> None:
        tokens = search_module._identifier_shaped_query_tokens("requests.get")
        assert {"requests", "get"} <= tokens

    def test_camel_case_token_is_shaped(self) -> None:
        tokens = search_module._identifier_shaped_query_tokens(
            "find OriginValidationMiddleware please"
        )
        assert "originvalidationmiddleware" in tokens

    def test_bare_common_english_words_are_never_shaped(self) -> None:
        tokens = search_module._identifier_shaped_query_tokens(
            "rate limiting middleware per client IP address"
        )
        assert tokens == frozenset()

    def test_all_caps_acronym_alone_is_not_shaped(self) -> None:
        # "HVAC" carries no lowercase-to-uppercase transition -- a plain
        # acronym, not a code-identifier signature.
        assert search_module._identifier_shaped_query_tokens("HVAC scheduling") == frozenset()

    def test_a_single_leading_capital_is_not_shaped(self) -> None:
        # "Kubernetes" is Title-Case, not camelCase -- one capital at
        # position 0 is not an "internal" case change.
        assert search_module._identifier_shaped_query_tokens("Kubernetes ingress") == frozenset()

    def test_single_letter_dotted_segments_do_not_qualify(self) -> None:
        # "e.g." must not be treated as a dotted identifier chain.
        assert search_module._identifier_shaped_query_tokens("see e.g. the docs") == frozenset()

    def test_measured_nonsense_queries_never_yield_a_shaped_token(self) -> None:
        # The exact 9 nonsense queries that anchored under the un-gated rule
        # (search_score_survey_summary.md, 2026-07-06) -- none may contribute
        # a shaped token under the fix.
        nonsense_queries_that_used_to_anchor = (
            "quantum blockchain kubernetes ingress rate limiter for photo uploads",
            "rate limiting middleware per client IP address",
            "GPU-accelerated video transcoding pipeline for livestream ingestion",
            "OAuth2 device-code flow for a smart refrigerator's firmware updater",
            "distributed consensus protocol for a fleet of autonomous drones",
            "cryptocurrency mining pool payout reconciliation ledger",
            "airline seat upgrade bidding auction settlement engine",
            "smart thermostat HVAC scheduling machine learning model",
            "podcast transcript closed-caption timing alignment tool",
        )
        for query in nonsense_queries_that_used_to_anchor:
            assert search_module._identifier_shaped_query_tokens(query) == frozenset(), query


class TestHasWholeQueryIdentityMatch:
    def test_fires_on_a_substantial_verbatim_whole_query_match(self) -> None:
        assert search_module._has_whole_query_identity_match(
            "Summary > Fix — DISCLOSE-AND-SERVE",
            "summary > fix — disclose-and-serve some_doc",
        ) is True

    def test_does_not_fire_below_the_minimum_length(self) -> None:
        assert search_module._has_whole_query_identity_match("fix it", "fix it now") is False

    def test_does_not_fire_on_a_partial_match(self) -> None:
        assert search_module._has_whole_query_identity_match(
            "a long enough english sentence with no identifier in it at all",
            "some_function",
        ) is False


class TestHasVerbatimIdentifierAnchor:
    def test_true_when_a_shaped_query_token_is_a_whole_token_in_ident_text(self) -> None:
        assert search_module._has_verbatim_identifier_anchor(
            "find action_confirm please", "PurchaseOrder action_confirm"
        ) is True

    def test_false_on_whole_token_boundary_not_a_substring_scan(self) -> None:
        # "is_a" (shaped, underscore-bearing) must not spuriously match
        # inside the LONGER glued token "this_is_a_test" -- a token-SET
        # intersection, never a raw substring scan.
        assert search_module._has_verbatim_identifier_anchor(
            "check is_a value", "this_is_a_test"
        ) is False

    def test_bare_common_english_overlap_no_longer_anchors(self) -> None:
        assert search_module._has_verbatim_identifier_anchor(
            "rate limiting middleware per client IP address", "Client client"
        ) is False

    def test_dotted_class_method_paste_anchors(self) -> None:
        # The exact TestScoutMainGuard paste this fix must anchor -- an
        # honest ``_derive_ident_text``-shaped fixture (identity + bare_name
        # + file_stem, space-joined).
        assert search_module._has_verbatim_identifier_anchor(
            "TestScoutMainGuard.test_main_guard_is_last_top_level_statement",
            "TestScoutMainGuard.test_main_guard_is_last_top_level_statement "
            "test_main_guard_is_last_top_level_statement test_scout",
        ) is True

    def test_camel_case_paste_anchors(self) -> None:
        assert search_module._has_verbatim_identifier_anchor(
            "find OriginValidationMiddleware please", "OriginValidationMiddleware"
        ) is True

    def test_whole_query_fallback_anchors_a_non_code_identity_paste(self) -> None:
        assert search_module._has_verbatim_identifier_anchor(
            "Summary > Fix — DISCLOSE-AND-SERVE",
            "summary > fix — disclose-and-serve some_doc",
        ) is True

    def test_empty_query_never_anchors(self) -> None:
        assert search_module._has_verbatim_identifier_anchor("   ", "anything") is False


class TestCosineAbsencePredicate:
    """The D2/D3 aggregate-verdict firing rule, extracted as its own pure
    function (S4b audit finding #1, REPORT-slate-audit-searchstore.md
    §Concern 6) so ``scripts/search_score_survey.py``'s Phase C floor
    selection can IMPORT this exact predicate — never re-derive a
    paraphrase that can silently drift from what production actually runs.
    """

    def test_fires_when_below_floor_and_no_anchor(self) -> None:
        assert search_module._cosine_absence_predicate(0.3, 0.5, False) is True

    def test_does_not_fire_at_or_above_the_floor(self) -> None:
        assert search_module._cosine_absence_predicate(0.5, 0.5, False) is False
        assert search_module._cosine_absence_predicate(0.6, 0.5, False) is False

    def test_does_not_fire_when_a_verbatim_anchor_is_present_even_below_floor(
        self,
    ) -> None:
        assert search_module._cosine_absence_predicate(0.1, 0.5, True) is False


class TestCosineFloorDriftCheck:
    """Pure :func:`~loremaster.search._cosine_floor_drift_note` tests -- no

    pipeline, no store, no I/O. Finding #74 part 3: the floor is stamped with
    the corpus snapshot it was measured against (indexed-file count +
    embedding-schema fingerprint, which folds in ``config.chunkers`` -- see
    :func:`~loremaster.index.schema.embedding_schema_fingerprint`) and a
    later drift beyond a defined bar must be DETECTED here before anything
    downstream can disarm on it.
    """

    _STAMP = search_module.CosineFloorMeasurement(
        floor=0.5828,
        measured_file_count=200,
        measured_embedding_schema_fingerprint="a" * 64,
    )

    def test_no_drift_when_file_count_and_fingerprint_match_exactly(self) -> None:
        assert search_module._cosine_floor_drift_note(self._STAMP, 200, "a" * 64) is None

    def test_no_drift_within_the_file_count_tolerance_band(self) -> None:
        # +9%/-9% (under the 10% bar) on both sides.
        assert search_module._cosine_floor_drift_note(self._STAMP, 218, "a" * 64) is None
        assert search_module._cosine_floor_drift_note(self._STAMP, 182, "a" * 64) is None

    def test_drift_when_file_count_exceeds_the_tolerance_band(self) -> None:
        # +11.5%/-11.5% (over the 10% bar), both directions.
        for current in (223, 177):
            note = search_module._cosine_floor_drift_note(self._STAMP, current, "a" * 64)
            assert note is not None
            assert "file count" in note

    def test_drift_on_any_embedding_schema_fingerprint_change(self) -> None:
        # An exact-match gate -- even a single differing character
        # disqualifies, unlike the percentage-tolerant file count (a
        # chunker/embedding-config change already forces a full re-embed
        # elsewhere; ANY difference here means the corpus almost certainly
        # moved under the floor).
        note = search_module._cosine_floor_drift_note(self._STAMP, 200, "b" * 64)
        assert note is not None
        assert "fingerprint" in note

    def test_fingerprint_drift_is_checked_before_file_count(self) -> None:
        # Both signals drifted at once -- the reason names the fingerprint
        # (checked first), a single clear cause rather than a confusing
        # double reason.
        note = search_module._cosine_floor_drift_note(self._STAMP, 999999, "b" * 64)
        assert note is not None
        assert "fingerprint" in note

    def test_non_positive_stamped_file_count_is_treated_as_unconditional_drift(
        self,
    ) -> None:
        # Defensive, mirrors CalibrationEngine._apply_measurement's own
        # non-positive-baseline guard: never divide by zero, never silently
        # treat a degenerate stamp as still valid.
        degenerate_stamp = search_module.CosineFloorMeasurement(
            floor=0.5828, measured_file_count=0, measured_embedding_schema_fingerprint="a" * 64
        )
        note = search_module._cosine_floor_drift_note(degenerate_stamp, 10, "a" * 64)
        assert note is not None


class TestApplyCosineFloorDriftCheck:
    """:func:`~loremaster.search.apply_cosine_floor_drift_check` -- the

    stateful half: (re)sets the runtime disarm flag and returns a status
    snapshot. Called by ``AppContext._build_index_status`` on every
    ``lore_index()`` read (test_mcp_server.py covers that wiring); these
    tests exercise the function directly.
    """

    @pytest.fixture(autouse=True)
    def _reset_drift_state(self) -> Any:
        # State-leakage guard (global CLAUDE.md lifecycle rule): the disarm
        # flag is module-level mutable state consulted on the query hot path
        # -- a test that disarms it must never leak that into the next test,
        # regardless of test order or a failure mid-test.
        search_module._reset_cosine_floor_drift_state_for_tests()
        yield
        search_module._reset_cosine_floor_drift_state_for_tests()

    def test_measured_state_when_the_stamp_still_holds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        stamp = search_module.CosineFloorMeasurement(
            floor=0.5828, measured_file_count=200,
            measured_embedding_schema_fingerprint="a" * 64,
        )
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", 0.5828)
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR_STAMP", stamp)

        status = search_module.apply_cosine_floor_drift_check(
            current_file_count=200, current_embedding_schema_fingerprint="a" * 64
        )

        assert status.state == "measured"
        assert status.note is None
        assert search_module._cosine_floor_runtime_state.disarmed_by_drift is False

    def test_stale_state_and_disarm_when_file_count_drifts(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        stamp = search_module.CosineFloorMeasurement(
            floor=0.5828, measured_file_count=200,
            measured_embedding_schema_fingerprint="a" * 64,
        )
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", 0.5828)
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR_STAMP", stamp)

        status = search_module.apply_cosine_floor_drift_check(
            current_file_count=999, current_embedding_schema_fingerprint="a" * 64
        )

        assert status.state == "stale"
        assert status.note is not None
        assert "re-measure needed" in status.note
        assert search_module._cosine_floor_runtime_state.disarmed_by_drift is True

    def test_disabled_state_when_the_floor_itself_is_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", None)

        status = search_module.apply_cosine_floor_drift_check(
            current_file_count=1, current_embedding_schema_fingerprint=""
        )

        assert status.state == "disabled"
        assert status.floor is None
        # Packet 10-d: the disabled branch stopped serving a null note —
        # disabled-by-config and disarmed-pending-calibration are different
        # conditions and must not share a rendering (finding #4). The note's
        # CONTENT is pinned by
        # TestWeakMatchDisarmedAtTheProductionDefault; here it only has to be
        # the module's one string rather than an ad-hoc second copy.
        assert status.note == search_module._COSINE_FLOOR_DISARMED_NOTE
        assert search_module._cosine_floor_runtime_state.disarmed_by_drift is False

    def test_recomputes_fresh_every_call_not_a_one_way_latch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Lifecycle degrade-then-recover test (global CLAUDE.md): a stamp

        comparison is cheap and deterministic (no network, unlike
        CalibrationEngine's retry/cache machinery), so "last observed" must
        be exactly the current truth -- degrading then recovering the
        underlying signal re-arms the verdict; it must never stay stuck
        disabled the way a network-probe cache legitimately might.
        """
        stamp = search_module.CosineFloorMeasurement(
            floor=0.5828, measured_file_count=200,
            measured_embedding_schema_fingerprint="a" * 64,
        )
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", 0.5828)
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR_STAMP", stamp)

        # Degrade: file count drifts far beyond tolerance -> disarmed.
        degraded = search_module.apply_cosine_floor_drift_check(
            current_file_count=999, current_embedding_schema_fingerprint="a" * 64
        )
        assert degraded.state == "stale"
        assert search_module._cosine_floor_runtime_state.disarmed_by_drift is True

        # Recover: a later status read observes the count back in tolerance
        # (e.g. the extra files were transient) -> re-armed, never stuck.
        recovered = search_module.apply_cosine_floor_drift_check(
            current_file_count=200, current_embedding_schema_fingerprint="a" * 64
        )
        assert recovered.state == "measured"
        assert search_module._cosine_floor_runtime_state.disarmed_by_drift is False


class TestCosineAbsenceVerdictDisarmedByDrift:
    """The disarm flag suppresses the AGGREGATE absence verdict end-to-end --

    the split finding #74 part 3 demands: the disarm state renders the
    TEACHING (``lore_index``'s status -- test_mcp_server.py covers that),
    never the verdict itself (this class, at the pipeline layer).
    """

    _FLOOR = 0.5

    async def _pipeline(
        self, tmp_path: Path, embedder: FakeEmbedder, candidates: list[Candidate]
    ) -> SearchPipeline:
        indexed, server = await _index_single(tmp_path, embedder, files={})
        store = _FixedCandidatesStore(dim=embedder.dim, db=indexed.db, candidates=candidates)
        return _make_pipeline(indexed=indexed, embedder=embedder, server=server, store=store)

    @pytest.fixture(autouse=True)
    def _reset_drift_state(self) -> Any:
        search_module._reset_cosine_floor_drift_state_for_tests()
        yield
        search_module._reset_cosine_floor_drift_state_for_tests()

    async def test_hostile_fixture_no_verdict_while_disarmed_even_though_every_condition_for_it_holds(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Every condition the (undisarmed) verdict needs is present: a hit
        # below the floor, no verbatim anchor -- this is the EXACT fixture
        # TestCosineAbsenceVerdictLit.test_all_weak_hits_carry_the_absence_verdict
        # uses to PROVE the verdict fires. Disarming must suppress it anyway
        # -- the disarm state renders the TEACHING, not the verdict.
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        monkeypatch.setattr(search_module._cosine_floor_runtime_state, "disarmed_by_drift", True)
        weak = _score_candidate(
            "k1", 0.03, vector_cosine=self._FLOOR - 0.01, file_path="pkg/a.py",
            identity="pkg.a.weak_fn", ident_text="weak_fn",
        )
        pipeline = await self._pipeline(tmp_path, embedder, [weak])

        results = await pipeline.search_code("something unrelated", k=5)

        notices = [r for r in results if r.kind == _NOTICE_KIND]
        assert not any(_ABSENCE_VERDICT_MARKER in n.formatted for n in notices), (
            "a disarmed (stale) floor must render NO absence claim at all -- "
            "under-claim is cheap, a confidently-wrong absence claim is not"
        )
        # The per-hit weak-match flag is a SEPARATE, lower-stakes claim
        # (finding #74 part 3 explicitly scopes the disarm to the AGGREGATE
        # verdict only -- see the informant false-flag-asymmetry receipts in
        # docs/design/2026-07-06-weak-match-discrimination.md §4/§5) -- it
        # still fires normally while the aggregate verdict is disarmed.
        hits = [r for r in results if r.kind == _HIT_KIND]
        assert any(_WEAK_MATCH_MARKER in hit.formatted for hit in hits)

    async def test_armed_by_default_the_same_fixture_still_fires(
        self, tmp_path: Path, embedder: FakeEmbedder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Control: WITHOUT disarming, the identical fixture fires -- proves
        # the suppression above is caused by the disarm flag, not some other
        # accidental difference in the fixture.
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", self._FLOOR)
        monkeypatch.setattr(search_module._cosine_floor_runtime_state, "disarmed_by_drift", False)
        weak = _score_candidate(
            "k1", 0.03, vector_cosine=self._FLOOR - 0.01, file_path="pkg/a.py",
            identity="pkg.a.weak_fn", ident_text="weak_fn",
        )
        pipeline = await self._pipeline(tmp_path, embedder, [weak])

        results = await pipeline.search_code("something unrelated", k=5)

        notices = [r for r in results if r.kind == _NOTICE_KIND]
        assert any(_ABSENCE_VERDICT_MARKER in n.formatted for n in notices)


class TestWeakMatchDisarmedAtTheProductionDefault:
    """Packet 10-d (2026-07-24): the weak-match CONFIDENCE surfaces are dark at

    the PRODUCTION DEFAULT — deliberately NO ``monkeypatch`` of
    ``_COSINE_WEAK_MATCH_FLOOR`` anywhere in this class, because the shipped
    value of that constant IS the thing under test. Every OTHER cosine class
    in this file patches its own floor, so a flip of the production constant
    is invisible to all of them; this class is the only pin that sees it.

    Ruled by ``docs/design/2026-07-24-floor-calibration.md`` Addendum E1 and
    executed by ``docs/plans/v2/10-d-weak-match-disarm.md``. The judgement was
    confident-wrong three source-verified ways: it compares live cosines
    against a floor measured in a retired embedding space (#176), ships an
    unmeasured constant to every foreign instance (#179), and applies a
    best-of-response floor to every individual hit (#180).

    What must stay ON is pinned here just as hard as what goes dark: the
    per-hit cosine SUBSTRATE line is claim-free and D1-gated, so darkening it
    too would be over-correcting, and the stamp constant is 11-i's provenance.
    """

    async def _pipeline(
        self, tmp_path: Path, embedder: FakeEmbedder, candidates: list[Candidate]
    ) -> SearchPipeline:
        indexed, server = await _index_single(tmp_path, embedder, files={})
        store = _FixedCandidatesStore(dim=embedder.dim, db=indexed.db, candidates=candidates)
        return _make_pipeline(indexed=indexed, embedder=embedder, server=server, store=store)

    @pytest.fixture(autouse=True)
    def _reset_drift_state(self) -> Any:
        search_module._reset_cosine_floor_drift_state_for_tests()
        yield
        search_module._reset_cosine_floor_drift_state_for_tests()

    def test_the_shipped_floor_is_none(self) -> None:
        assert search_module._COSINE_WEAK_MATCH_FLOOR is None, (
            "packet 10-d: the shipped floor is the DISARMED state (None) until "
            "11-ii arms it from the instance's own measurement"
        )

    def test_the_measurement_stamp_survives_the_disarm(self) -> None:
        # Scope IN, explicitly: the stamp is 11-i's provenance for what 0.50649
        # was, and 11-ii owns its retirement. A build that "cleaned up" the
        # stamp alongside the floor has destroyed the historical record.
        stamp = search_module._COSINE_WEAK_MATCH_FLOOR_STAMP
        assert stamp is not None
        assert stamp.floor == 0.50649
        assert stamp.measured_file_count == 214

    async def test_no_per_hit_weak_flag_however_low_the_cosine(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        far_below_any_floor = _score_candidate("k1", 0.03, vector_cosine=0.05)
        pipeline = await self._pipeline(tmp_path, embedder, [far_below_any_floor])

        results = await pipeline.search_code("anything", k=5)

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert _WEAK_MATCH_MARKER not in hits[0].formatted

    async def test_the_substrate_line_still_renders(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # The disarm must not over-correct: a raw magnitude with no judgement
        # attached is not a confident-wrong claim, and it is the ONLY thing
        # left for a reader to weigh the hit by. Same fixture as the weak-flag
        # pin above, so the two together discriminate "surface disarmed" from
        # "cosine machinery removed".
        far_below_any_floor = _score_candidate("k1", 0.03, vector_cosine=0.05)
        pipeline = await self._pipeline(tmp_path, embedder, [far_below_any_floor])

        results = await pipeline.search_code("anything", k=5)

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert "sim 0.05" in hits[0].formatted

    async def test_no_aggregate_absence_verdict_even_when_every_condition_holds(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # The exact fixture shape TestCosineAbsenceVerdictLit uses to PROVE the
        # verdict fires (all hits weak, no verbatim identifier anchor) — with
        # the shipped floor it must produce no claim at all.
        weak_a = _score_candidate(
            "k1", 0.03, vector_cosine=0.05, file_path="pkg/a.py",
            identity="pkg.a.weak_fn", ident_text="weak_fn",
        )
        weak_b = _score_candidate(
            "k2", 0.02, vector_cosine=0.04, file_path="pkg/b.py",
            identity="pkg.b.other_fn", ident_text="other_fn",
        )
        pipeline = await self._pipeline(tmp_path, embedder, [weak_a, weak_b])

        results = await pipeline.search_code("something unrelated", k=5)

        notices = [r for r in results if r.kind == _NOTICE_KIND]
        assert not any(_ABSENCE_VERDICT_MARKER in n.formatted for n in notices)

    def test_the_disabled_state_serves_the_disarm_note_not_a_null(self) -> None:
        # Finding #4's lesson: disabled-BY-CONFIG and disarmed-PENDING-
        # CALIBRATION are different conditions and must not share a rendering.
        # A null note renders as "this surface was simply never turned on",
        # which is a different (and, today, false) fact about the instance.
        status = search_module.apply_cosine_floor_drift_check(
            current_file_count=214, current_embedding_schema_fingerprint="a" * 64
        )

        assert status.state == "disabled"
        assert status.floor is None
        assert status.note == search_module._COSINE_FLOOR_DISARMED_NOTE

    def test_the_disarm_note_admits_the_condition_and_names_the_next_move(self) -> None:
        # §C5 family (a) shape: the failure is admitted loudly, the findings
        # that caused it are citable, the packets that resolve it are named,
        # and what STILL serves is stated so a reader does not conclude the
        # whole cosine surface went away. A bland "disabled" string passes
        # every other pin in this class and fails this one.
        note = search_module._COSINE_FLOOR_DISARMED_NOTE
        assert "disarmed" in note
        for citation in ("#83", "#176", "#179", "#180", "11-i", "11-ii"):
            assert citation in note, f"the disarm note must cite {citation}"
        assert "substrate remains served" in note

    def test_the_disarm_note_is_not_the_drift_note(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Positive control for the pin above: with a REAL floor restored, the
        # same function's stale branch must still serve its own re-measure
        # note. Proves the disarm note landed on the disabled branch
        # specifically, not on every branch (a build that returned the disarm
        # string unconditionally would pass the disabled-state pin alone).
        stamp = search_module.CosineFloorMeasurement(
            floor=0.5828, measured_file_count=200,
            measured_embedding_schema_fingerprint="a" * 64,
        )
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR", 0.5828)
        monkeypatch.setattr(search_module, "_COSINE_WEAK_MATCH_FLOOR_STAMP", stamp)

        stale = search_module.apply_cosine_floor_drift_check(
            current_file_count=999, current_embedding_schema_fingerprint="a" * 64
        )

        assert stale.state == "stale"
        assert stale.note is not None
        assert "re-measure needed" in stale.note
        assert stale.note != search_module._COSINE_FLOOR_DISARMED_NOTE


class TestRetiredFusedFloorIsGone:
    """S4's fused-score-floor mechanism is fully retired — a corpse pin

    (repo law: an audit-caught defect class becomes an invariant test, and a
    known-non-discriminating flag left live implies interpretive authority it
    doesn't have).
    """

    def test_the_retired_constants_no_longer_exist(self) -> None:
        for name in (
            "_SEARCH_SCORE_FLOOR",
            "_WEAK_MATCH_WARNING_TEMPLATE",
            "_ALL_HITS_WEAK_TEMPLATE",
        ):
            assert not hasattr(search_module, name), f"{name} should have been retired"

    def test_the_retired_functions_no_longer_exist(self) -> None:
        for name in ("_weak_match_warning", "_all_hits_weak_notice"):
            assert not hasattr(search_module, name), f"{name} should have been retired"

    def test_the_retired_pipeline_method_no_longer_exists(self) -> None:
        assert not hasattr(search_module.SearchPipeline, "_all_weak_notice")


# --------------------------------------------------------------------------- #
# item 13 (S3, finding #61) — a non-auto detail_level miss never renders
# memories-only silently
# --------------------------------------------------------------------------- #
class TestDetailLevelMissNotice:
    """A ``detail_level`` filter that zeroes every code hit gets an explicit,

    teaching NOTICE_KIND entry — never a silent memories-only response. The
    S4b cosine weak-match/absence-verdict machinery (unrelated to this
    notice) never fires here regardless of the production gate constants:
    every candidate in this class is built via ``_score_candidate(...)``
    with no ``vector_cosine=`` override, so it defaults to ``None`` — the
    substrate/flag/verdict checks all gate on ``candidate.vector_cosine is
    not None`` and short-circuit before ever consulting the enabled flag or
    the floor.
    """

    _CONFIDENT_SCORE = 0.5

    async def _pipeline(
        self,
        tmp_path: Path,
        embedder: FakeEmbedder,
        candidates: list[Candidate],
        *,
        memory_store: Any | None = None,
    ) -> SearchPipeline:
        indexed, server = await _index_single(tmp_path, embedder, files={})
        store = _FixedCandidatesStore(dim=embedder.dim, db=indexed.db, candidates=candidates)
        return _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, store=store,
            memory_store=memory_store,
        )

    async def test_all_hits_filtered_out_by_detail_level_produces_a_notice(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # Every candidate classifies "source" (chunk_type="function"); asking
        # for "summary" zeroes partitioned_hits even though hits were found.
        source_only = _score_candidate("k1", self._CONFIDENT_SCORE, chunk_type="function")
        pipeline = await self._pipeline(tmp_path, embedder, [source_only])

        results = await pipeline.search_code("anything", k=5, detail_level="summary")

        assert not any(r.kind == _HIT_KIND for r in results), "the filter must still zero the hits"
        notices = [r for r in results if r.kind == _NOTICE_KIND]
        assert any(_DETAIL_MISS_MARKER in n.formatted for n in notices), (
            f"expected a detail-level-miss notice; got notices={notices!r}"
        )

    async def test_auto_detail_level_never_produces_the_notice(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        source_only = _score_candidate("k1", self._CONFIDENT_SCORE, chunk_type="function")
        pipeline = await self._pipeline(tmp_path, embedder, [source_only])

        results = await pipeline.search_code("anything", k=5, detail_level="auto")

        assert any(r.kind == _HIT_KIND for r in results), "auto never filters"
        assert not any(_DETAIL_MISS_MARKER in r.formatted for r in results)

    async def test_partial_match_produces_no_notice(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # A mix of summary- and source-classified hits: requesting "summary"
        # still yields a hit, so there is nothing to explain.
        summary_hit = _score_candidate(
            "k1", self._CONFIDENT_SCORE, file_path="pkg/a.py", chunk_type="imports"
        )
        source_hit = _score_candidate(
            "k2", self._CONFIDENT_SCORE, file_path="pkg/b.py", chunk_type="function"
        )
        pipeline = await self._pipeline(tmp_path, embedder, [summary_hit, source_hit])

        results = await pipeline.search_code("anything", k=5, detail_level="summary")

        hits = [r for r in results if r.kind == _HIT_KIND]
        assert len(hits) == 1
        assert not any(_DETAIL_MISS_MARKER in r.formatted for r in results)

    async def test_genuinely_empty_hits_produces_no_detail_miss_notice(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # Zero candidates at all: nothing was "zeroed BY the filter" -- this
        # is a different (unrelated) empty-result case, not S3's defect.
        pipeline = await self._pipeline(tmp_path, embedder, [], memory_store=None)

        results = await pipeline.search_code("anything", k=5, detail_level="summary")

        assert not any(_DETAIL_MISS_MARKER in r.formatted for r in results)

    async def test_notice_coexists_with_the_trailing_memories_block(
        self, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        # The exact defect shape: a code-intent query with memories recalled
        # AND a detail_level miss must show BOTH the notice and the memory
        # block -- never memories-only with no explanation.
        source_only = _score_candidate("k1", self._CONFIDENT_SCORE, chunk_type="function")
        memory_store = _FakeMemoryBackend(
            [_backend_recalled(text="a relevant memory", chunk_keys=[], score=0.9)]
        )
        pipeline = await self._pipeline(
            tmp_path, embedder, [source_only], memory_store=memory_store
        )

        results = await pipeline.search_code("anything", k=5, detail_level="summary")

        assert not any(r.kind == _HIT_KIND for r in results)
        assert any(_DETAIL_MISS_MARKER in r.formatted for r in results if r.kind == _NOTICE_KIND)
        assert any(r.kind == _MEMORY_KIND for r in results), "the memory block must still render"


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
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, embedder: FakeEmbedder
    ) -> SearchPipeline:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        base_config = _config(slug=slug, live_path=tmp_path)
        # Packet 46: compose the fake via LIVE DISCOVERY (the production path) —
        # inject the registry and carry the matching slice, then let
        # ``LoreServer(...)`` discover it, rather than a manual ``register_extension``
        # (which now needs the slice discovery would have supplied).
        register_in_discovery(monkeypatch, {"fake": FakeExtension})
        ext_config = base_config.model_copy(
            update={"extensions": {"fake": {"flavour": "vanilla"}}}
        )
        server = LoreServer(ext_config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, embedder=embedder, server=server
        )
        return _make_pipeline(indexed=indexed, embedder=embedder, server=server)

    async def test_fake_extension_format_overrides_base_citation(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        pipeline = await self._extension_pipeline(monkeypatch, tmp_path, embedder)
        results = await pipeline.search_code("routing", k=5)
        hits = [r for r in results if r.kind == _HIT_KIND]
        assert hits
        # The fake's format_result returns "FAKE: <key>" for every hit ⇒ the base
        # [SOURCE:...] citation must NOT appear (the seam-5 hook won).
        assert all(r.formatted.startswith("FAKE:") for r in hits)
        assert not any("[SOURCE:" in r.formatted for r in hits)

    async def test_fake_extension_augment_injects_a_candidate(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, embedder: FakeEmbedder
    ) -> None:
        pipeline = await self._extension_pipeline(monkeypatch, tmp_path, embedder)
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

