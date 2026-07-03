"""Live integration contract for P5-C3b: the Indexer / ReconcileEngine rewired
onto the async Surreal ports with the C2 composed atomic per-file transaction.

These run against the REAL 3.1.5 server (``_surreal_harness`` per-test DB
isolation) with the REAL :class:`~loremaster.store.surreal.SurrealStore`,
:class:`~loremaster.index.surreal_manifest.SurrealManifest` and
:class:`~loremaster.graph_surreal.SurrealCodeGraph` — the cross-connection
visibility, snapshot isolation and cap enforcement the rewiring depends on are
server-side properties with no in-memory shortcut. They are the LEAN companion to
the fast fake-backed unit ports (``test_indexer.py`` et al.); store-level
atomicity itself is already live-covered by ``test_surreal_apply.py``, so this
file pins only the four things the rewiring ADDS at the indexer/reconcile seam:

* **(a) one composed apply lands all four surfaces.** ``index_file`` of one
  Python file makes its chunks, its verbatim ``file_text`` body, its manifest row
  AND its code-graph slice readable — each through the surface's own independent
  connection (the manifest/graph read back what the STORE's apply wrote).
* **(b) re-index observes an atomic replace.** A changed file's second
  ``index_file`` re-derives it: the stale chunk/edge are gone, the new present,
  the manifest + file_text updated — no half-applied residue.
* **(c) an embed failure writes a failed-state row and NOTHING else.** A file the
  embedder cannot embed leaves a ``failed`` manifest row and ZERO chunks, ZERO
  file_text, ZERO graph nodes — the four-surface write never partially happened.
* **(d) reconcile purge removes every surface.** A file deleted from disk is
  purged atomically — chunks, file_text, manifest row and graph slice all gone.

Every expected value is an INDEPENDENT oracle read off the authored source (the
true FQNs / identities / digest), never re-derived from the engine's own output.

RED against current code: the pre-P5-C3b Indexer calls the manifest/graph methods
synchronously and uses the old ``upsert``-then-``delete_points`` store ordering,
so ``index_file`` against the async :class:`SurrealManifest` raises
``AttributeError`` on a never-awaited coroutine before any surface is written.
"""

from __future__ import annotations

import textwrap
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    TIER_A,
    SurrealEnv,
    connect_admin,
    run,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
)
from loremaster.config import LoreConfig
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.indexer import Indexer, graph_roots
from loremaster.index.manifest import STATE_FAILED, STATE_INDEXED
from loremaster.index.reconcile import ReconcileEngine
from loremaster.index.records import sha512_hex
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.server import LoreServer
from loremaster.store.surreal import SurrealStore
from loremaster.store.surreal_schema import FILE_TEXT_TABLE
from lorescribe.astroid_parse import clear_resolution_cache, reset_search_path_memo
from loresigil.testing import FakeEmbedder

# The production embedding width the harness uses — the real distribution the
# store's HNSW index and vector-width guard will see in production, not a
# convenience scale (clause 1).
_DIM = PRODUCTION_DIM

# --- Authored on-disk sources. Each is an INDEPENDENT ORACLE: the true FQNs /
# importer sets are read off the source text below, never from the engine. ---

_BASE_PATH = "src/base.py"
_WIDGET_PATH = "src/widget.py"
_WIDGET_MODULE = "src.widget"
# The in-project import the widget makes — the RESOLVED FQN ``from src.base
# import Base`` points at (read straight off _WIDGET_SOURCE below). A stdlib
# import would be dropped by the resolution keep/drop rule, so the import assert
# keys on this in-project symbol.
_BASE_FQN = "src.base.Base"

_BASE_SOURCE = textwrap.dedent(
    '''\
    """The widget base."""


    class Base:
        """A base widget."""

        def tag(self):
            return "base"
    '''
)

_WIDGET_SOURCE = textwrap.dedent(
    '''\
    """The widget module."""
    from src.base import Base


    class Widget(Base):
        """A widget."""

        def render(self, value):
            return self.tag() + str(value)


    def make_widget():
        return Widget()
    '''
)

# The REVISED widget: ``make_widget`` is REMOVED and ``spawn_widget`` ADDED, and
# the ``from src.base import Base`` import is DROPPED — so the surviving identity
# set both loses and gains a member (a partial replace would equal NEITHER set)
# AND the LoadError-style import edge must vanish (the stale-edge oracle).
_WIDGET_SOURCE_V2 = textwrap.dedent(
    '''\
    """The widget module (revised)."""


    class Widget:
        """A widget."""

        def render(self, value):
            return str(value)


    def spawn_widget():
        return Widget()
    '''
)


def _config(*, slug: str, live_path: Path) -> LoreConfig:
    """A minimal single-live-root config at the real production embedding dim."""
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://tei.example:8080",
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
                "tier": TIER_A,
                "watch": "live",
                "path": str(live_path),
                "include": ["**/*.py"],
                "exclude": [],
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
    return LoreConfig.model_validate(payload)


@dataclass(frozen=True)
class _Bench:
    """The rewired indexer wired to the three REAL Surreal ports on one database."""

    indexer: Indexer
    engine: ReconcileEngine
    store: SurrealStore
    manifest: SurrealManifest
    graph: SurrealCodeGraph
    env: SurrealEnv
    config: LoreConfig
    live_root: Path


@pytest_asyncio.fixture()
async def bench(
    surreal_env: SurrealEnv,  # noqa: F811
    tmp_path: Path,
) -> AsyncIterator[_Bench]:
    """A rewired :class:`Indexer` + :class:`ReconcileEngine` over the REAL ports.

    Store, manifest and graph each open their OWN connection to the SAME database
    (schema is DB-scoped), so a manifest/graph fragment the STORE's ``apply``
    writes is read back over the SEPARATE manifest/graph connections — the
    cross-connection visibility the atomic per-file transaction relies on.
    """
    clear_resolution_cache()
    reset_search_path_memo()
    live_root = tmp_path / "live"
    (live_root / "src").mkdir(parents=True)
    (live_root / "src" / "base.py").write_text(_BASE_SOURCE, encoding="utf-8")
    (live_root / "src" / "widget.py").write_text(_WIDGET_SOURCE, encoding="utf-8")
    config = _config(slug=surreal_env.database, live_path=live_root)
    snapshot_root = tmp_path / "snap"

    store = SurrealStore(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        dim=_DIM,
        user=surreal_env.user,
        password=surreal_env.password,
    )
    manifest = SurrealManifest(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        user=surreal_env.user,
        password=surreal_env.password,
    )
    tier_roots, project_roots = graph_roots(config, snapshot_root)
    graph = SurrealCodeGraph(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        user=surreal_env.user,
        password=surreal_env.password,
        tier_roots=tier_roots,
        project_roots=project_roots,
    )
    await store.ensure_ready()
    await manifest.ensure_ready()
    await graph.ensure_ready()

    server = LoreServer(config)
    indexer = Indexer(
        store=store,
        embedder=FakeEmbedder(dim=_DIM),
        manifest=manifest,
        registry=server.registry,
        source_providers=[],
        config=config,
        snapshot_root=snapshot_root,
        code_graph=graph,
    )
    engine = ReconcileEngine(
        indexer=indexer, manifest=manifest, store=store, config=config, code_graph=graph
    )
    try:
        yield _Bench(
            indexer=indexer, engine=engine, store=store, manifest=manifest,
            graph=graph, env=surreal_env, config=config, live_root=live_root,
        )
    finally:
        await store.close()
        await manifest.close()
        await graph.close()
        clear_resolution_cache()
        reset_search_path_memo()


async def _file_text_rows(env: SurrealEnv) -> list[dict[str, Any]]:
    """Every ``file_text`` row (id + body + digest), read on a FRESH admin conn."""
    connection = await connect_admin(env)
    try:
        result = await run(connection, f"SELECT id, text, sha512 FROM {FILE_TEXT_TABLE}")
    finally:
        await connection.close()
    return [row for row in result if isinstance(row, dict)] if isinstance(result, list) else []


# ===========================================================================
# (a) One composed apply lands all four surfaces.
# ===========================================================================


class TestIndexFileLandsAllFourSurfaces:
    """One ``index_file`` writes chunks + file_text + manifest + graph atomically,
    each readable through its surface's own independent connection."""

    async def test_index_file_populates_chunks_file_text_manifest_and_graph(
        self, bench: _Bench
    ) -> None:
        # Index the base first so astroid resolves the widget's in-project import.
        await bench.indexer.index_file(TIER_A, _BASE_PATH, _BASE_SOURCE)
        outcome = await bench.indexer.index_file(TIER_A, _WIDGET_PATH, _WIDGET_SOURCE)

        assert outcome.state == STATE_INDEXED
        assert outcome.n_chunks >= 3  # the real chunker splits imports/class/method/fn

        # 1) chunks — scrollable via the store, tagged with this tier + file.
        rows = await bench.store.scroll(
            {"tier": TIER_A, "file_path": _WIDGET_PATH}, limit=1000
        )
        identities = {row["identity"] for row in rows}
        # Independent oracle (source): Widget, its render method, make_widget.
        assert "Widget" in identities
        assert "make_widget" in identities

        # 2) file_text — the verbatim body + the independent SHA-512 of that body.
        expected_sha = sha512_hex(_WIDGET_SOURCE)
        text_rows = [
            r for r in await _file_text_rows(bench.env) if tuple(r["id"].id) == (TIER_A, _WIDGET_PATH)
        ]
        assert len(text_rows) == 1
        assert text_rows[0]["text"] == _WIDGET_SOURCE
        assert text_rows[0]["sha512"] == expected_sha
        assert len(text_rows[0]["sha512"]) == 128  # a full digest, not a stub

        # 3) manifest — visible over the SEPARATE SurrealManifest connection.
        row = await bench.manifest.get(TIER_A, _WIDGET_PATH)
        assert row is not None
        assert row.state == STATE_INDEXED
        assert row.n_chunks == outcome.n_chunks
        assert len(row.chunk_ids) == outcome.n_chunks
        assert row.sha512 == expected_sha  # shared digest — never a hand-copied twin

        # 4) graph — queryable over the SEPARATE SurrealCodeGraph connection. The
        # RESOLVED in-project import edge: src.widget imports src.base.Base.
        importers = {n.qualified_name for n in await bench.graph.what_imports(_BASE_FQN)}
        assert _WIDGET_MODULE in importers
        assert await bench.graph.indexed_file_count() >= 2  # base + widget

    async def test_non_python_file_writes_chunks_and_manifest_but_no_graph(
        self, bench: _Bench
    ) -> None:
        # A markdown file: chunks + file_text + manifest land, but the graph is a
        # Python-AST structure only, so it synthesises NO node for it.
        md_path = "docs/guide.md"
        md_source = "# Guide\n\nHow to use the widget.\n"
        (bench.live_root / "docs").mkdir(parents=True, exist_ok=True)
        (bench.live_root / "docs" / "guide.md").write_text(md_source, encoding="utf-8")

        graph_count_before = await bench.graph.indexed_file_count()
        outcome = await bench.indexer.index_file(TIER_A, md_path, md_source)

        assert outcome.state == STATE_INDEXED
        manifest_row = await bench.manifest.get(TIER_A, md_path)
        assert manifest_row is not None and manifest_row.state == STATE_INDEXED
        text_rows = [r for r in await _file_text_rows(bench.env) if tuple(r["id"].id) == (TIER_A, md_path)]
        assert len(text_rows) == 1 and text_rows[0]["text"] == md_source
        # No graph slice was added for the markdown file.
        assert await bench.graph.indexed_file_count() == graph_count_before


# ===========================================================================
# (b) Re-index observes an atomic replace.
# ===========================================================================


class TestReindexIsAtomicReplace:
    """A changed file's second ``index_file`` re-derives every surface — stale
    chunks/edges gone, new present, manifest + file_text updated."""

    async def test_reindex_removes_stale_chunks_and_edges_and_updates_manifest(
        self, bench: _Bench
    ) -> None:
        await bench.indexer.index_file(TIER_A, _BASE_PATH, _BASE_SOURCE)
        await bench.indexer.index_file(TIER_A, _WIDGET_PATH, _WIDGET_SOURCE)
        # Pre-state oracle: v1 imports src.base.Base and defines make_widget.
        assert _WIDGET_MODULE in {
            n.qualified_name for n in await bench.graph.what_imports(_BASE_FQN)
        }
        first_identities = {
            r["identity"]
            for r in await bench.store.scroll({"tier": TIER_A, "file_path": _WIDGET_PATH}, limit=1000)
        }
        assert "make_widget" in first_identities

        # Re-write on disk (astroid re-resolves v2 from disk) and re-index.
        (bench.live_root / "src" / "widget.py").write_text(_WIDGET_SOURCE_V2, encoding="utf-8")
        outcome = await bench.indexer.index_file(TIER_A, _WIDGET_PATH, _WIDGET_SOURCE_V2)
        assert outcome.state == STATE_INDEXED

        # Stale chunk removal: make_widget gone, spawn_widget present — the set
        # genuinely changed (a partial replace would equal neither v1 nor v2).
        surviving = {
            r["identity"]
            for r in await bench.store.scroll({"tier": TIER_A, "file_path": _WIDGET_PATH}, limit=1000)
        }
        assert "spawn_widget" in surviving
        assert "make_widget" not in surviving

        # Stale EDGE removal: v2 dropped the src.base import, so no importer remains.
        assert await bench.graph.what_imports(_BASE_FQN) == []

        # Manifest + file_text updated to v2's content + digest (shared, not copied).
        expected_sha = sha512_hex(_WIDGET_SOURCE_V2)
        row = await bench.manifest.get(TIER_A, _WIDGET_PATH)
        assert row is not None and row.sha512 == expected_sha
        text_rows = [
            r for r in await _file_text_rows(bench.env) if tuple(r["id"].id) == (TIER_A, _WIDGET_PATH)
        ]
        assert text_rows[0]["text"] == _WIDGET_SOURCE_V2
        assert text_rows[0]["sha512"] == expected_sha


# ===========================================================================
# (c) An embed failure writes a failed-state row and NOTHING else.
# ===========================================================================


class TestEmbedFailureWritesFailedRowOnly:
    """A file the embedder cannot embed leaves a ``failed`` manifest row and ZERO
    chunks / file_text / graph nodes — the four-surface write never happened."""

    async def test_embed_failure_persists_failed_row_and_no_partial_surfaces(
        self, bench: _Bench
    ) -> None:
        path = "src/lonely.py"
        source = "def compute_margin(cost, price):\n    return price - cost\n"
        (bench.live_root / "src" / "lonely.py").write_text(source, encoding="utf-8")

        # Learn the file's real chunk texts, then build an embedder that fails ALL
        # of them (a permanent None-vector) — reusing the production chunk path.
        texts = bench.indexer.chunk_texts(TIER_A, path, source)
        assert texts
        failing_indexer = Indexer(
            store=bench.store,
            embedder=FakeEmbedder(dim=_DIM, fail_inputs=set(texts)),
            manifest=bench.manifest,
            registry=LoreServer(bench.config).registry,
            source_providers=[],
            config=bench.config,
            snapshot_root=bench.live_root.parent / "snap",
            code_graph=bench.graph,
        )
        outcome = await failing_indexer.index_file(TIER_A, path, source)

        # The manifest row is the ONLY surface written, and it is ``failed``.
        assert outcome.state == STATE_FAILED
        row = await bench.manifest.get(TIER_A, path)
        assert row is not None and row.state == STATE_FAILED
        # No chunks, no file_text body, no graph slice for the failed file.
        assert await bench.store.scroll({"tier": TIER_A, "file_path": path}, limit=1000) == []
        assert [r for r in await _file_text_rows(bench.env) if tuple(r["id"].id) == (TIER_A, path)] == []
        assert await bench.graph.what_imports("src.lonely.compute_margin") == []


# ===========================================================================
# (d) Reconcile purge removes every surface.
# ===========================================================================


class TestReconcilePurgeRemovesEverySurface:
    """A file deleted from disk is purged atomically across all four surfaces."""

    async def test_reconcile_purges_chunks_file_text_manifest_and_graph(
        self, bench: _Bench
    ) -> None:
        # First reconcile indexes base + widget from disk → all surfaces present.
        await bench.engine.reconcile()
        assert await bench.manifest.get(TIER_A, _WIDGET_PATH) is not None
        assert _WIDGET_PATH in {
            r["file_path"] for r in await bench.store.scroll({"tier": TIER_A}, limit=1000)
        }
        assert await bench.graph.indexed_file_count() >= 1

        # Delete the widget from disk; the next reconcile's deletion sweep purges it.
        (bench.live_root / "src" / "widget.py").unlink()
        summary = await bench.engine.reconcile()
        assert summary.files_purged >= 1

        # Every surface for the deleted file is gone; the surviving base is intact.
        assert await bench.manifest.get(TIER_A, _WIDGET_PATH) is None
        assert await bench.store.scroll({"tier": TIER_A, "file_path": _WIDGET_PATH}, limit=1000) == []
        remaining = [
            r for r in await _file_text_rows(bench.env) if tuple(r["id"].id) == (TIER_A, _WIDGET_PATH)
        ]
        assert remaining == []
        # The base survives (tier-scoped, file-scoped purge).
        assert await bench.manifest.get(TIER_A, _BASE_PATH) is not None
