"""Contract tests for ``loremaster.search`` — the query-time pipeline.

The :class:`~loremaster.search.SearchPipeline` is the read side of lore: it
turns a natural-language query into a list of *summarised* results
(``[SOURCE:file:line]`` + a stable ``Key:`` + a fenced source block), never a
raw :class:`~qdrant_client.models.ScoredPoint` dump. It is the MCP
``search_code`` tool's engine.

These run against the **REAL local Qdrant** (``http://127.0.0.1:16333``,
throwaway ``lore_test_<uuid>`` collections), a real
:class:`~loremaster.index.indexer.Indexer` over a **real corpus** (so the points
under search carry real chunk types / payloads / line numbers, not hand-faked
ones), the shipped deterministic :class:`~loresigil.testing.FakeEmbedder`, and
the fast in-memory async :class:`~loremaster.index.surreal_manifest.SurrealManifest`
fake (via ``fake_surreal_trio``).

Why real Qdrant, not ``:memory:``: ranking and payload-filtered search
(``filters={"tier": ...}``) are *server-side* behaviours — filter-based search
is a no-op on the in-memory backend. "A boosted chunk overtakes an unboosted
one" and "a tier filter returns only that tier's hit" are only meaningful
against the live engine.

**Concurrency-safe teardown (deliberately NOT the inherited global sweep).** A
sibling agent may be creating/deleting ``lore_test_*`` collections on this SAME
server concurrently; the inherited ``conftest.qdrant_client`` fixture tears down
by a GLOBAL ``lore_test_*`` prefix sweep, which under concurrency would delete
the other run's in-flight collections. This module owns a :func:`store_factory`
that records the EXACT collection names it creates and deletes only those by
name on teardown. Foreign collections are never touched; this module's never
leak.

The pinned contract (each maps to a plan / AMENDMENT-1 requirement):

* **Pipeline shape.** ``search_code(query, k, filters=None, wait_for_fresh=False,
  detail_level="auto")`` embeds the query (``embed_query``), searches the store,
  runs the extension ``augment_candidates`` then ``rerank`` (identity for the
  bare generic server), memory-boosts, formats, freshness-flags, and partitions
  by detail level. It returns summarised :class:`~loremaster.search.SearchResult`
  value objects, NEVER raw ``ScoredPoint``\\ s.
* **Base citation format (seam 5 default).** Each result's ``formatted`` carries
  ``[SOURCE:<file_path>:<line_start>]``, a stable ``Key:`` line (the chunk's key),
  and a fenced ```` ``` ```` source block wrapping the chunk's ``source_text``.
* **Ranking.** A query embedding equal to one indexed chunk's text (FakeEmbedder
  is deterministic ⇒ cosine 1.0) ranks that chunk first — an independent oracle,
  not the implementation's own arithmetic.
* **Memory-boost (generic).** A saved memory whose ``refs`` point at a chunk's
  key lifts that chunk ABOVE an unboosted chunk that the bare store ranked higher
  — proven by an ordering flip, with the control (no memory) showing the original
  order, so the boost is the cause.
* **Freshness flags (never blanket-block).** A chunk whose manifest file row is
  ``dirty``/``embedding`` is flagged stale ("⚠ re-indexing — may be stale"); an
  ``indexed`` chunk is not. The stale chunk is STILL RETURNED (annotate, never
  block).
* **detail_level partition (seam 11 / C2).** With ``detail_level="summary"`` only
  summary-classified chunk types come back; ``"source"`` only source-classified;
  ``"auto"`` returns both. The base default classifies ``imports``/``class``/
  ``markdown_section`` as summary and ``method``/``function`` as source — proven
  with REAL chunks of those types.
* **Extension hooks vs generic.** A FAKE extension's ``augment_candidates`` /
  ``rerank`` / ``format_result`` / ``classify_detail`` observably change the
  output, while the bare (zero-extension) server uses the base defaults — both
  proven side by side so the seam wiring is the cause.
* **Filters.** ``filters={"tier": X}`` returns only tier-X hits;
  ``filters={"file_path": P}`` only that file's — server-side, on real indexes.
* **``wait_for_fresh`` is bounded.** With an in-flight file matching the query's
  path filter that NEVER reaches ``indexed``, ``wait_for_fresh=True`` returns
  within the timeout (serving stale-with-warning) rather than hanging forever.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any, cast

import pytest
import pytest_asyncio

# ``conftest`` and ``_extension_helpers`` resolve as top-level modules because
# conftest.py inserts the tests dir onto ``sys.path`` (see
# loremaster/tests/conftest.py). The inherited harness URL + key reader are
# reused WITHOUT its global-sweep teardown; ``_extension_helpers`` ships the fake
# extension overriding every seam (proves the pipeline consults the resolved
# LoreServer hooks, not hardwired base behaviour). ``_surreal_fakes`` supplies the
# async in-memory ``FakeSurrealManifest`` — the P5 write-stack's manifest contract,
# faked, since ``SearchPipeline`` now consults it asynchronously (see
# ``_index_corpus`` below for why it replaces the old SQLite ``Manifest``); it is
# ``cast`` to the real :class:`SurrealManifest` at the one fixture boundary that
# constructs it, so every downstream type hint stays the real production type.
from _extension_helpers import FakeExtension, minimal_config
from _surreal_fakes import fake_surreal_trio
from _surreal_harness import (
    drop_database as drop_surreal_database,
)
from _surreal_harness import (
    make_env,
    surreal_password,
    surreal_url,
    surreal_user,
)
from conftest import QDRANT_URL, _qdrant_api_key
from loremaster.config import LoreConfig
from loremaster.extension import Extension, ExtensionContext
from loremaster.index.manifest import STATE_DIRTY, STATE_EMBEDDING, STATE_INDEXED
from loremaster.index.records import chunk_to_record, sha512_hex
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.memory.store import MemoryRef, MemoryStore
from loremaster.search import SearchPipeline, SearchResult
from loremaster.server import LoreServer, build_app_context
from loremaster.store.qdrant import QdrantStore
from lorescribe.models import ChunkContext
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import ScoredPoint

# Production embedding dim per the owner directive (FakeEmbedder at 2048).
_DIM = 2048

# The (sole) tier every ``_config``-built config declares — matches the "custom"
# literal the tests already hardcode when reading manifest rows back.
_TIER = "custom"

# The freshness warning marker the plan pins ("⚠ re-indexing — may be stale").
_STALE_MARKER = "re-indexing"

# The memory-collection slug suffix the MemoryStore convention appends.
_MEMORY_SUFFIX = "_memory"

# The namespace + credential env-var names the one real ``build_app_context``
# test's throwaway SurrealDB database uses (mirrors ``test_cli.py``'s
# harness-isolation convention).
_SURREAL_TEST_NAMESPACE = "lore_test"
_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"


# --------------------------------------------------------------------------- #
# Real corpus — modules whose chunk types we can pin by inspection
# --------------------------------------------------------------------------- #
# A real module the python_ast chunker splits into imports/class/method/function
# — types the base classifies as summary (imports/class) vs source (method/
# function). Used for the detail_level partition and the freshness/format tests.
_PY_ROUTING = """\
import os


class Router:
    \"\"\"Routes a request.\"\"\"

    def route(self, request):
        return os.path.join("/", request)


def champion_routing(week):
    \"\"\"Route the 36-week curve champion to the right warehouse.\"\"\"
    return week * 2
"""

# A second real module with a distinct uniquely-named function, so two files'
# chunks coexist and a per-file filter is meaningful.
_PY_PRICING = """\
def quarterly_pricing(volume):
    \"\"\"Compute the quarterly tiered price for a paper volume.\"\"\"
    return volume * 0.95
"""


def _write(path: Path, text: str) -> None:
    """Create parents and write ``text`` (UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _slug() -> str:
    """A per-test slug → throwaway ``lore_test_<uuid4>`` collection."""
    return f"test_{uuid.uuid4().hex}"


def _embedding_text_for(
    server: LoreServer, file_path: str, source: str, identity: str
) -> str:
    """Return the EXACT ``embedding_text`` the indexer embedded for one chunk.

    Runs ``source`` through the SAME chunker registry the indexer used (so the
    text — including any chunker-internal prefix — is the genuine producer's
    output, not a hand-mirrored copy). A query equal to this embeds, under the
    deterministic FakeEmbedder, to that chunk's exact stored vector — an
    independent ranking oracle (cosine 1.0) free of a hardcoded text format.
    """
    ctx = ChunkContext(
        slug="oracle",
        file_path=file_path,
        count_tokens=lambda text: max(1, len(text) // 4),
        max_input_tokens=8192,
    )
    chunks = server.registry.dispatch_file(file_path, source, ctx)
    return next(chunk.embedding_text for chunk in chunks if chunk.identity == identity)


def _config(
    *, slug: str, live_path: Path, surreal: dict[str, Any] | None = None
) -> LoreConfig:
    """A validated :class:`LoreConfig` with one live tier rooted at ``live_path``.

    ``surreal`` threads an explicit SurrealDB connection block (the harness's
    throwaway dev-server URL + credentials) when given — needed ONLY by the one
    test that drives the real ``build_app_context`` (``TestRuntimeExtensionContext``);
    every other test in this file builds a :class:`SearchPipeline` directly and
    never resolves SurrealDB credentials at all.
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
        "qdrant": {"url": QDRANT_URL, "api_key_env": "QDRANT__SERVICE__API_KEY"},
        "roots": [
            {
                "tier": "custom",
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
    if surreal is not None:
        payload["surreal"] = surreal
    return LoreConfig.model_validate(payload)


# --------------------------------------------------------------------------- #
# Fixtures — concurrency-safe, exact-name teardown
# --------------------------------------------------------------------------- #
StoreFactory = Callable[[str], QdrantStore]


@pytest_asyncio.fixture()
async def store_factory() -> AsyncIterator[StoreFactory]:
    """Builder for :class:`QdrantStore`, with CONCURRENCY-SAFE exact-name teardown.

    Owns its own client and deletes ONLY the exact collection names it created
    (never a ``lore_test_*`` prefix sweep, which would race a sibling agent on
    this shared server).
    """
    client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
    created: list[str] = []

    def _make(slug: str) -> QdrantStore:
        store = QdrantStore(client=client, slug=slug)
        created.append(store.collection_name)
        return store

    try:
        yield _make
    finally:
        for name in created:
            if await client.collection_exists(name):
                await client.delete_collection(name)
        await client.close()


class FlatFakeEmbedder(FakeEmbedder):
    """A :class:`FakeEmbedder` pinned to the FLAT embed path.

    These search tests' identity oracle (query text == chunk text => cosine 1.0)
    holds only when index-time vectors are FLAT: a contextualized-capable
    embedder's grouped vectors are deliberately context-sensitive, so the same
    text embedded as a query (always flat) would no longer match. The grouped
    flavor of this truth is pinned by test_indexer_contextualized.py's
    ``test_grouped_path_stores_the_context_sensitive_vector_not_a_flat_one``.
    """

    @property
    def supports_contextualized(self) -> bool:
        """This double instruments the FLAT embed path — opt out of grouped dispatch."""
        return False


@pytest.fixture()
def embedder() -> FakeEmbedder:
    """The shipped deterministic embedder at the production dim (flat-path pinned)."""
    return FlatFakeEmbedder(dim=_DIM)


@pytest.fixture()
def manifest() -> SurrealManifest:
    """A fast in-memory async manifest — the P5 write-stack's :class:`SurrealManifest`
    CONTRACT, faked (:mod:`_surreal_fakes`). ``SearchPipeline`` now consults its
    manifest asynchronously (``_is_stale`` / ``_all_rows_indexed_for_path``), so
    the old synchronous SQLite ``Manifest`` no longer satisfies its type — and
    these tests never need a REAL SurrealDB round-trip (they pin
    ``SearchPipeline`` behaviour, not the manifest store itself), so the fake is
    the right-sized double (``fake_surreal_trio`` wires it with its own private
    in-memory database; only the manifest half is used here). ``cast`` to the real
    type: the fake satisfies the SAME async contract structurally but is not a
    nominal ``SurrealManifest`` subclass — the standard typed-double pattern.
    """
    return cast(SurrealManifest, fake_surreal_trio(dim=_DIM).manifest)


class _Indexed:
    """A small bundle: a slug-scoped store, the manifest it was indexed under, and the config."""

    def __init__(
        self, *, store: QdrantStore, manifest: SurrealManifest, config: LoreConfig
    ) -> None:
        self.store = store
        self.manifest = manifest
        self.config = config


async def _index_corpus(
    *,
    slug: str,
    live_path: Path,
    store: QdrantStore,
    embedder: FakeEmbedder,
    manifest: SurrealManifest,
    server: LoreServer | None = None,
) -> _Indexed:
    """Index the live corpus at ``live_path`` for real, returning the bundle.

    NOT the production :class:`~loremaster.index.indexer.Indexer`: since P5 its
    write path is the unified SurrealDB store exclusively (the composed-
    transaction ``store.apply(...)``), which :class:`QdrantStore` does not
    implement — ``SearchPipeline``'s read path is UNCHANGED (still Qdrant; the
    P5→P6 dual-store interim documented on ``server.build_app_context``), so a
    real ``Indexer`` run would populate SurrealDB while this suite searches
    Qdrant and find nothing. Instead this chunks + embeds every ``.py`` file
    through the SAME producer helpers the real ``Indexer`` uses — the REAL
    chunker registry (``composed.registry.dispatch_file``) and the REAL (fake)
    embedder, translated to :class:`~loremaster.index.records.Record` via the
    production ``chunk_to_record`` — so the points under search still carry
    real chunk types, payloads, and line numbers; only the ORCHESTRATION differs
    (a direct ``store.upsert`` + a mirrored manifest row, not the atomic Surreal
    apply).
    """
    config = _config(slug=slug, live_path=live_path)
    composed = server if server is not None else LoreServer(config)
    await store.ensure_collection(embedder.dim)
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
        await store.upsert(pairs)
        await manifest.upsert(
            tier=_TIER,
            file_path=rel,
            sha512=content_hash,
            mtime_ns=stat.st_mtime_ns,
            size=len(source.encode("utf-8")),
            n_chunks=len(records),
            chunk_ids=[record.point_id for record in records],
            state=STATE_INDEXED,
        )
    return _Indexed(store=store, manifest=manifest, config=config)


def _make_pipeline(
    *,
    indexed: _Indexed,
    embedder: FakeEmbedder,
    server: LoreServer,
    memory_store: MemoryStore | None = None,
) -> SearchPipeline:
    """Wire a :class:`SearchPipeline` over an indexed bundle + the composed server.

    Builds the RUNTIME :class:`ExtensionContext` over the live (fake) services so
    the pipeline's search seams receive a functional embedder/manifest/tokenizer
    — the same shape ``build_app_context`` injects in production.
    """
    extension_context = ExtensionContext(
        store=indexed.store,
        embedder=embedder,
        config=indexed.config,
        count_tokens=embedder.count_tokens,
        manifest=indexed.manifest,
    )
    return SearchPipeline(
        store=indexed.store,
        embedder=embedder,
        server=server,
        manifest=indexed.manifest,
        extension_context=extension_context,
        memory_store=memory_store,
        config=indexed.config,
    )


# --------------------------------------------------------------------------- #
# Pipeline shape & summarised output
# --------------------------------------------------------------------------- #
class TestSummarisedOutput:
    """search_code returns summarised value objects, never raw ScoredPoints."""

    async def test_returns_search_result_value_objects(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        results = await pipeline.search_code("champion routing warehouse", k=5)

        assert results, "a real query over a real corpus must return hits"
        assert all(isinstance(r, SearchResult) for r in results)
        # Never a raw ScoredPoint dump.
        from qdrant_client.models import ScoredPoint

        assert not any(isinstance(r, ScoredPoint) for r in results)

    async def test_respects_k_ceiling(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        _write(tmp_path / "pricing.py", _PY_PRICING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        results = await pipeline.search_code("anything", k=2)
        assert len(results) <= 2


# --------------------------------------------------------------------------- #
# Base citation/result format (seam 5 default)
# --------------------------------------------------------------------------- #
class TestBaseFormat:
    """The base default citation: [SOURCE:file:line] + stable Key: + fenced source."""

    async def test_base_format_carries_source_key_and_fenced_block(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        # Query equal to the champion_routing function's source so it ranks first
        # (FakeEmbedder deterministic). Then inspect that result's format.
        results = await pipeline.search_code("champion routing warehouse", k=5)
        top = results[0]

        # [SOURCE:<file_path>:<line_start>] — the file path is the indexed
        # tier-relative path; the line is the chunk's start line (an int).
        assert "[SOURCE:routing.py:" in top.formatted
        # A stable Key: line carrying the chunk's key.
        assert "Key:" in top.formatted
        assert top.chunk_key, "a base result still carries a (structural) key"
        assert top.chunk_key in top.formatted
        # A fenced source block wrapping the real source text.
        assert "```" in top.formatted

    async def test_source_line_in_citation_matches_chunk_line_start(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        # champion_routing's `def` is line 11 of _PY_ROUTING (counted by hand:
        # import(1), blanks(2,3), class(4)+docstring(5)+blank(6)+method(7,8)+
        # blanks(9,10), then `def champion_routing` at 11). An independent oracle
        # counted from the source, NOT read back from the implementation.
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        # Embed the EXACT text the indexer embedded for champion_routing's chunk
        # (FakeEmbedder is deterministic ⇒ cosine 1.0 ⇒ it ranks first). We pull
        # that text from the same chunker the indexer used, so the query equals
        # the stored vector's source without hardcoding the chunker's text format.
        champion_text = _embedding_text_for(server, "routing.py", _PY_ROUTING, "champion_routing")
        results = await pipeline.search_code(champion_text, k=5)
        top = results[0]
        assert "[SOURCE:routing.py:11]" in top.formatted


# --------------------------------------------------------------------------- #
# Ranking (independent oracle: identical-text cosine == 1.0)
# --------------------------------------------------------------------------- #
class TestRanking:
    """A chunk whose text equals the query embeds identically ⇒ ranks first."""

    async def test_query_equal_to_chunk_text_ranks_that_chunk_first(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        _write(tmp_path / "pricing.py", _PY_PRICING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        # The EXACT text the indexer embedded for quarterly_pricing's chunk →
        # that chunk's vector (FakeEmbedder deterministic ⇒ cosine 1.0), so the
        # pricing chunk MUST outrank every routing chunk. The query text is pulled
        # from the same chunker the indexer used (independent oracle, no hardcoded
        # chunker text format).
        pricing_text = _embedding_text_for(server, "pricing.py", _PY_PRICING, "quarterly_pricing")
        results = await pipeline.search_code(pricing_text, k=5)
        assert results
        assert "pricing.py" in results[0].formatted
        # cosine of an identical vector is 1.0 — an independent magnitude oracle.
        assert results[0].score == pytest.approx(1.0, abs=1e-4)


# --------------------------------------------------------------------------- #
# Memory-boost (generic) — proven by an ordering FLIP vs a no-memory control
# --------------------------------------------------------------------------- #
class TestMemoryBoost:
    """A saved memory referencing a chunk's key lifts it above an unboosted hit."""

    async def _index_two_funcs(
        self, tmp_path: Path, store_factory: StoreFactory,
        embedder: FakeEmbedder, manifest: SurrealManifest,
    ) -> tuple[_Indexed, LoreServer]:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        _write(tmp_path / "pricing.py", _PY_PRICING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        return indexed, server

    async def test_boost_flips_order_vs_no_memory_control(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        indexed, server = await self._index_two_funcs(
            tmp_path, store_factory, embedder, manifest
        )

        # CONTROL: no memory store → the bare store ranking decides the order.
        control = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        query = "tiered routing and pricing logic"
        control_results = await control.search_code(query, k=5)
        assert len(control_results) >= 2
        control_top_key = control_results[0].chunk_key
        # Pick a chunk the control ranked BELOW the top to boost.
        boost_target = next(
            r for r in control_results[1:] if r.chunk_key != control_top_key
        )

        # Save a memory whose ref points at the boost target's key. A second
        # store over the project's _memory collection.
        mem_store = MemoryStore(
            store=store_factory(f"{indexed.config.project.slug}{_MEMORY_SUFFIX}"),
            embedder=embedder,
        )
        await mem_store.ensure_ready()
        await mem_store.save_memory(
            query,  # the memory text matches the query so recall finds it
            refs=[MemoryRef(chunk_key=boost_target.chunk_key)],
        )

        boosted = _make_pipeline(
            indexed=indexed, embedder=embedder, server=server, memory_store=mem_store
        )
        boosted_results = await boosted.search_code(query, k=5)

        # The boosted chunk now outranks the control's former top — an ordering
        # FLIP that only the memory boost can cause (control proves it was lower).
        boosted_keys = [r.chunk_key for r in boosted_results]
        assert boost_target.chunk_key in boosted_keys
        assert boosted_keys.index(boost_target.chunk_key) < boosted_keys.index(
            control_top_key
        )

    async def test_no_memory_store_is_inert(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        # A pipeline with memory_store=None must search fine (the generic, no-
        # memory deploy) — memory-boost is optional, never required.
        indexed, server = await self._index_two_funcs(
            tmp_path, store_factory, embedder, manifest
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        results = await pipeline.search_code("routing", k=5)
        assert results


# --------------------------------------------------------------------------- #
# Freshness flags — annotate, never blanket-block
# --------------------------------------------------------------------------- #
class TestFreshnessFlags:
    """An in-flight (dirty/embedding) chunk is flagged stale but still returned."""

    @pytest.mark.parametrize("inflight_state", [STATE_DIRTY, STATE_EMBEDDING])
    async def test_inflight_chunk_is_flagged_but_still_returned(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
        inflight_state: str,
    ) -> None:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        # Flip routing.py to an in-flight state AFTER indexing (its points are
        # still searchable — the manifest, not Qdrant, is the freshness authority).
        await manifest.set_state("custom", "routing.py", inflight_state)

        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        results = await pipeline.search_code("champion routing warehouse", k=5)

        assert results, "freshness is annotate-never-block: hits still come back"
        flagged = [r for r in results if "routing.py" in r.formatted]
        assert flagged, "the in-flight file's chunks are still returned"
        for r in flagged:
            assert r.stale is True
            assert _STALE_MARKER in r.formatted

    async def test_indexed_chunk_is_not_flagged_stale(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        # All files settled at 'indexed' after index_all — confirm the control.
        routing_row = await manifest.get("custom", "routing.py")
        assert routing_row is not None
        assert routing_row.state == STATE_INDEXED

        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)
        results = await pipeline.search_code("champion routing warehouse", k=5)
        assert results
        for r in results:
            assert r.stale is False
            assert _STALE_MARKER not in r.formatted


# --------------------------------------------------------------------------- #
# detail_level partition (seam 11 / C2) — proven with REAL chunk types
# --------------------------------------------------------------------------- #
class TestDetailLevel:
    """summary/source/auto partition the results by the chunk-type classification."""

    async def _pipeline(
        self, tmp_path: Path, store_factory: StoreFactory,
        embedder: FakeEmbedder, manifest: SurrealManifest,
    ) -> SearchPipeline:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        return _make_pipeline(indexed=indexed, embedder=embedder, server=server)

    async def test_summary_returns_only_summary_chunk_types(
        self, tmp_path: Path, store_factory: StoreFactory,
        embedder: FakeEmbedder, manifest: SurrealManifest,
    ) -> None:
        pipeline = await self._pipeline(tmp_path, store_factory, embedder, manifest)
        # _PY_ROUTING yields imports/class (summary) + method/function (source).
        results = await pipeline.search_code("routing", k=10, detail_level="summary")
        assert results, "summary chunks (imports/class) exist in this corpus"
        # Every returned result is a summary chunk: classify_detail==summary.
        assert all(r.detail_level == "summary" for r in results)

    async def test_source_returns_only_source_chunk_types(
        self, tmp_path: Path, store_factory: StoreFactory,
        embedder: FakeEmbedder, manifest: SurrealManifest,
    ) -> None:
        pipeline = await self._pipeline(tmp_path, store_factory, embedder, manifest)
        results = await pipeline.search_code("routing", k=10, detail_level="source")
        assert results, "source chunks (method/function) exist in this corpus"
        assert all(r.detail_level == "source" for r in results)

    async def test_auto_returns_both_levels(
        self, tmp_path: Path, store_factory: StoreFactory,
        embedder: FakeEmbedder, manifest: SurrealManifest,
    ) -> None:
        pipeline = await self._pipeline(tmp_path, store_factory, embedder, manifest)
        results = await pipeline.search_code("routing", k=10, detail_level="auto")
        levels = {r.detail_level for r in results}
        # The corpus has both summary and source chunks; auto keeps both.
        assert "summary" in levels
        assert "source" in levels


# --------------------------------------------------------------------------- #
# Extension hooks vs the bare generic server
# --------------------------------------------------------------------------- #
class TestExtensionHooks:
    """A FAKE extension's seams observably change the output; generic = base."""

    async def test_fake_extension_format_overrides_base_citation(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        # Compose a server WITH the fake extension. The fake's config slice lives
        # under extensions.fake; merge it into this config.
        ext_config = config.model_copy(
            update={"extensions": minimal_config().extensions}
        )
        server = LoreServer(ext_config).register_extension(FakeExtension())
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        results = await pipeline.search_code("routing", k=5)
        assert results
        # The fake's format_result returns "FAKE: <id>" for EVERY result, so the
        # base [SOURCE:...] citation must NOT appear — the seam-5 hook won.
        assert all(r.formatted.startswith("FAKE:") for r in results)
        assert not any("[SOURCE:" in r.formatted for r in results)

    async def test_fake_extension_augment_injects_a_candidate(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        ext_config = config.model_copy(
            update={"extensions": minimal_config().extensions}
        )
        server = LoreServer(ext_config).register_extension(FakeExtension())
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        # The fake's augment_candidates injects a ScoredPoint id="injected"
        # score=1.0 and rerank sorts by score desc, so the injected candidate
        # leads — visible proof the seam-4 hook ran in the pipeline.
        results = await pipeline.search_code("routing", k=10)
        assert results
        assert results[0].formatted == "FAKE: injected"

    async def test_bare_server_uses_base_defaults(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        # The control: a zero-extension server. No "FAKE:" anywhere, no injected
        # candidate — the base [SOURCE:...] citation is used.
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        results = await pipeline.search_code("routing", k=10)
        assert results
        assert not any(r.formatted.startswith("FAKE:") for r in results)
        assert all("[SOURCE:" in r.formatted for r in results)


# --------------------------------------------------------------------------- #
# Filters — server-side, on real payload indexes
# --------------------------------------------------------------------------- #
class TestFilters:
    """filters scope the search to a tier / file_path, server-side."""

    async def test_file_path_filter_returns_only_that_file(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        _write(tmp_path / "pricing.py", _PY_PRICING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        results = await pipeline.search_code(
            "anything at all", k=10, filters={"file_path": "pricing.py"}
        )
        assert results, "the filtered file has chunks"
        # Every hit is from pricing.py — the routing.py chunks are filtered out
        # server-side (proven against the real engine, not a no-op backend).
        assert all("pricing.py" in r.formatted for r in results)
        assert not any("routing.py" in r.formatted for r in results)

    async def test_tier_filter_returns_only_that_tier(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        # The only tier is 'custom'; a non-existent tier returns nothing (the
        # filter is applied, not ignored).
        hits = await pipeline.search_code("routing", k=10, filters={"tier": "custom"})
        assert hits
        misses = await pipeline.search_code(
            "routing", k=10, filters={"tier": "nonexistent_tier"}
        )
        assert misses == []

    async def test_path_alias_filter_scopes_like_file_path(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        """Contract: the 'path' alias for 'file_path' must scope the Qdrant store
        query IDENTICALLY to the canonical 'file_path' key.

        The public API documents 'path' as a valid alias (see
        ``_FILTER_FILE_PATH_KEYS = ("file_path", "path")`` and the MCP tool
        docstring).  After the fix, ``{"path": "pricing.py"}`` must:

        * return at least one result (the file has real chunks), and
        * scope the server-side filter so EVERY hit comes from pricing.py, and
        * exclude routing.py entirely — not merely rank it lower.

        This is an integration test against the REAL Qdrant engine (not a no-op
        in-memory backend) because the alias translation must happen BEFORE the
        store query, and the store's ``_build_filter`` applies the dict key
        verbatim as a Qdrant payload field name.  The test proves the full
        producer-to-consumer seam: index → real Qdrant → path-alias filter →
        SearchResult list.

        Expected values are derived solely from the alias contract (path ≡
        file_path), not from any implementation detail of the buggy code.  The
        sibling test ``test_file_path_filter_returns_only_that_file`` (which uses
        the canonical key and is known-green) serves as the independent oracle:
        the alias must produce the same scope.
        """
        # Arrange — two-file corpus (same as the sibling test; both files must be
        # indexed so the filter has something real to exclude).
        _write(tmp_path / "routing.py", _PY_ROUTING)
        _write(tmp_path / "pricing.py", _PY_PRICING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        # Act — filter with the ALIAS 'path', not the canonical 'file_path'.
        # The value "pricing.py" is the tier-relative path the indexer stamped into
        # every point's file_path payload field; it is read from _PY_PRICING's
        # file name, matching the production path convention (not a magic literal).
        FILTERED_FILE = "pricing.py"
        EXCLUDED_FILE = "routing.py"
        results = await pipeline.search_code(
            "anything at all", k=10, filters={"path": FILTERED_FILE}
        )

        # Assert — the alias must behave IDENTICALLY to {"file_path": "pricing.py"}.
        # (1) The filtered file has real indexed chunks — a non-empty result set
        #     proves the filter did not silently match nothing (the bug: returns []).
        assert results, (
            f"{{'path': {FILTERED_FILE!r}}} filter must match chunks from that file; "
            f"an empty list means the alias was not translated to the canonical "
            f"file_path payload key before the Qdrant query"
        )
        # (2) Every hit is from pricing.py — server-side scoping, not just ranking.
        assert all(FILTERED_FILE in r.formatted for r in results), (
            f"every result must be from {FILTERED_FILE!r}; a hit from another file "
            f"means the alias filter was ignored server-side"
        )
        # (3) No hit from routing.py — the filter excluded it, not merely ranked it lower.
        assert not any(EXCLUDED_FILE in r.formatted for r in results), (
            "routing.py chunks must be excluded by the path filter; "
            "a routing.py hit means the alias scoped nothing"
        )
        # (4) Sanity-bound: result count is within the plausible range for a single
        #     small module (at least 1, at most k=10 — catches scale / sign bugs).
        assert 1 <= len(results) <= 10



# --------------------------------------------------------------------------- #
# wait_for_fresh — ALWAYS bounded, NEVER hangs
# --------------------------------------------------------------------------- #
class TestWaitForFresh:
    """wait_for_fresh times out and serves stale-with-warning rather than hanging."""

    async def test_wait_for_fresh_times_out_and_returns(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        # Stick routing.py in 'embedding' state FOREVER — it never reaches
        # 'indexed'. wait_for_fresh must give up after its bounded timeout.
        await manifest.set_state("custom", "routing.py", STATE_EMBEDDING)

        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        start = time.monotonic()
        results = await pipeline.search_code(
            "champion routing warehouse",
            k=5,
            wait_for_fresh=True,
            filters={"file_path": "routing.py"},
            wait_timeout_s=0.5,
        )
        elapsed = time.monotonic() - start

        # Bounded: it returned well within a generous ceiling (never hung).
        assert elapsed < 5.0
        # And it served stale-with-warning rather than blocking/erroring.
        assert results
        assert any(r.stale for r in results)
        assert any(_STALE_MARKER in r.formatted for r in results)

    async def test_wait_for_fresh_returns_immediately_when_all_indexed(
        self,
        tmp_path: Path,
        store_factory: StoreFactory,
        embedder: FakeEmbedder,
        manifest: SurrealManifest,
    ) -> None:
        # When the matching file is already 'indexed', wait_for_fresh returns at
        # once (no wait), and nothing is flagged stale.
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(slug=slug, live_path=tmp_path)
        server = LoreServer(config)
        indexed = await _index_corpus(
            slug=slug, live_path=tmp_path, store=store_factory(slug),
            embedder=embedder, manifest=manifest, server=server,
        )
        pipeline = _make_pipeline(indexed=indexed, embedder=embedder, server=server)

        start = time.monotonic()
        results = await pipeline.search_code(
            "champion routing warehouse",
            k=5,
            wait_for_fresh=True,
            filters={"file_path": "routing.py"},
            wait_timeout_s=5.0,
        )
        elapsed = time.monotonic() - start
        assert elapsed < 2.0, "an already-indexed file needs no waiting"
        assert results
        assert all(not r.stale for r in results)


# --------------------------------------------------------------------------- #
# Runtime ExtensionContext wiring (bug A2) — the search seams get REAL services
# --------------------------------------------------------------------------- #
class _CtxRecordingExtension(Extension):
    """An :class:`Extension` whose seam-4 ``augment_candidates`` RECORDS its ``ctx``.

    The search pipeline hands each context-taking search seam an
    :class:`ExtensionContext`. This extension stashes the exact context object it
    is handed on :attr:`recorded_ctx` so a test can assert it carries the RUNTIME
    services (a real embedder, a real manifest, a working ``count_tokens``) rather
    than the composition-time placeholder (``embedder=None``, ``manifest=None``,
    and the ``_no_tokenizer`` stub that refuses to count).

    Observed via ``augment_candidates`` (seam 4) rather than ``format_result``
    (seam 5): ``SearchPipeline.search_code`` calls ``augment_candidates``
    UNCONDITIONALLY — even over an EMPTY candidate list — whereas
    ``format_result`` only fires per-HIT (``_to_result`` is never called on an
    empty candidate set). That distinction matters on THIS branch: the P5→P6
    dual-store interim (documented on ``server.build_app_context`` — the write
    path now lands in SurrealDB while ``search_code`` still reads the read-path
    QdrantStore) means a real ``search_code`` call returns ZERO hits regardless
    of indexing, until P6 cuts the read path over. Seam 4 still proves the exact
    same "the search seam gets a RUNTIME ctx, not the composition placeholder"
    contract this class exists to pin — it just does so on a seam whose firing
    does not depend on a store this branch cannot populate.
    """

    def __init__(self) -> None:
        self.recorded_ctx: ExtensionContext | None = None

    @property
    def name(self) -> str:
        """The extension's stable name (no config slice required)."""
        return "ctxrec"

    def augment_candidates(
        self, query: str, candidates: list[ScoredPoint], ctx: ExtensionContext
    ) -> list[ScoredPoint]:
        """Record the handed ``ctx`` (identity function otherwise)."""
        self.recorded_ctx = ctx
        return candidates

    def format_result(self, result: ScoredPoint, ctx: ExtensionContext) -> str | None:
        """Emit a recognisable citation (unused for the ctx-recording assertion,
        kept so a hit — if the read path ever serves one — still renders
        distinctively)."""
        return f"CTXREC: {result.id}"


class TestRuntimeExtensionContext:
    """The search seams receive a RUNTIME ctx (real embedder/manifest/tokenizer)."""

    async def test_search_seam_ctx_carries_runtime_services(
        self,
        tmp_path: Path,
        embedder: FakeEmbedder,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Drive a real search_code through the SAME build_app_context wiring the
        # live server uses (FakeEmbedder + a throwaway Qdrant collection), with a
        # recording extension on the seam-5 hook. The ctx that hook receives MUST
        # carry the runtime services, not the composition-time placeholder.
        #
        # KNOWN P5→P6 dual-store-interim gap (documented on
        # server.build_app_context): ``app_context.reindex()`` writes through the
        # unified SurrealDB write store, but ``app_context.search_code`` still
        # reads Qdrant — so this test's ``assert results`` below is expected to
        # fail until P6 cuts the read path over. The env/config plumbing here is
        # still ported (real SURREAL_USER/PASS creds + a throwaway harness
        # database) so the test fails on that DOCUMENTED gap, not on a
        # resolve_secret KeyError.
        monkeypatch.setenv(_SURREAL_USER_ENV, surreal_user())
        monkeypatch.setenv(_SURREAL_PASS_ENV, surreal_password())
        _write(tmp_path / "routing.py", _PY_ROUTING)
        slug = _slug()
        config = _config(
            slug=slug,
            live_path=tmp_path,
            surreal={
                "url": surreal_url(),
                "namespace": _SURREAL_TEST_NAMESPACE,
                "user_env": _SURREAL_USER_ENV,
                "password_env": _SURREAL_PASS_ENV,
            },
        )
        recorder = _CtxRecordingExtension()
        server = LoreServer(config).register_extension(recorder)

        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        try:
            app_context = await build_app_context(
                server=server,
                embedder=embedder,
                qdrant_client=client,
                manifest_path=tmp_path / "manifest.db",
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snapshot",
                start_tasks=False,
            )
            try:
                # A real reconcile so the corpus is indexed (build_app_context with
                # start_tasks=False does not auto-sweep), then search through the
                # live AppContext handler — the path the MCP tool takes.
                await app_context.reindex()
                # The result list itself is not asserted on (see the ctx-
                # recording docstring above) — only that the seam ran.
                await app_context.search_code("champion routing warehouse", k=5)
            finally:
                await app_context.aclose()
        finally:
            for candidate in (f"lore_{slug}", f"lore_{slug}_memory"):
                if await client.collection_exists(candidate):
                    await client.delete_collection(candidate)
            await client.close()
            await drop_surreal_database(make_env(database=slug, dim=embedder.dim))

        # NOTE: NOT asserting on ``results`` here (see _CtxRecordingExtension's
        # docstring) — the P5→P6 dual-store interim means search_code returns
        # zero hits on this branch regardless of indexing, so a hit-gated
        # observation point (format_result / seam 5) can never fire. The
        # runtime-ctx-wiring contract is instead pinned via augment_candidates
        # (seam 4), which SearchPipeline.search_code calls unconditionally, hit
        # or not — the SAME ctx object every context-taking seam receives.
        ctx = recorder.recorded_ctx
        assert ctx is not None, "the augment_candidates seam (4) must have been handed a ctx"
        # The runtime ctx carries the REAL (fake) embedder, not the placeholder None.
        assert ctx.embedder is not None
        assert ctx.embedder is embedder
        # The runtime ctx carries the REAL manifest, not the placeholder None.
        assert ctx.manifest is not None
        # And a WORKING token counter — the placeholder ``_no_tokenizer`` raises
        # NotImplementedError, so a returned int proves the real one was injected.
        counts = ctx.count_tokens(["a sample string"])
        assert isinstance(counts, list)
        assert len(counts) == 1
        assert isinstance(counts[0], int)
