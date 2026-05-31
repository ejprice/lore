"""Contract tests for graph wiring into the index path (plan AMENDMENT 1, item 6).

The capability-layer :class:`~loremaster.graph.CodeGraph` left its *wiring into
the index path* deferred: the graph module builds/deletes one file's slice
transactionally, but nothing was calling it on an index or a delete. This feature
wires it: :meth:`Indexer.index_file` (and therefore the reconcile per-file path,
which delegates to ``index_file``) rebuilds the indexed file's graph slice from
the SAME chunks it embeds, and a purge (delete / move-from) removes the slice —
so the code-graph stays as fresh as the vector index, on both live-watch and
reconcile.

The contract pinned here (each capable of failing on the unwired implementation):

* **Optional graph (backward compatible).** An :class:`Indexer` constructed WITH
  NO ``code_graph`` behaves exactly as before (the existing indexer tests must
  stay green). The wiring is opt-in.
* **Index a Python file → its nodes appear.** Indexing a real Python module
  through ``index_file`` populates the graph: the module node plus the symbols
  the python_ast chunker emits (a class, its method, a top-level function) are
  queryable (``blast_radius`` / ``what_imports`` reach them).
* **Re-index updates the slice transactionally.** Editing the file so a symbol is
  removed and a new one added rebuilds ONLY that file's slice — the gone symbol's
  node disappears, the new one appears, with no orphan edge left behind (the
  delete+rebuild is the graph module's transactional primitive).
* **Delete purges the slice.** Removing a file's graph (the purge path the
  watcher drives on a delete/move-from) leaves none of its nodes.
* **A failed embed does NOT refresh the graph stale.** When the embedder fails a
  file (state ``failed``, no vectors stored), the graph slice is NOT rebuilt from
  the new (unembeddable) content — the graph must not diverge from what is
  actually indexed. (Last-good graph retained, mirroring last-good vectors.)
* **A non-Python file contributes no graph nodes.** A README.md indexed through
  the same path must not synthesise a spurious ``module`` node — the graph is a
  Python AST structure only.
* **Tier scoping (C1).** Two tiers' copies of one path keep independent graph
  slices — rebuilding one tier's file does not touch the other's nodes.

Real Qdrant (throwaway collections), a real :class:`CodeGraph` (a tmp_path SQLite
file), a real ``tmp_path`` corpus chunked through the default registry, and a
:class:`FakeEmbedder` — the same harness shape as ``test_indexer.py``.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest_asyncio
from loremaster.config import LoreConfig
from loremaster.graph import KIND_FUNCTION, KIND_MODULE, CodeGraph
from loremaster.index.indexer import Indexer
from loremaster.index.manifest import STATE_FAILED, Manifest
from loremaster.index.reconcile import ReconcileEngine
from loremaster.index.watcher import LiveWatcher
from loremaster.server import LoreServer
from loremaster.store.qdrant import QdrantStore
from loresigil.base import Embedder
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient

_DIM = 2048

# A real Python module the python_ast chunker splits into imports + class +
# method + a top-level function — enough symbols to populate a real graph slice.
_PY_MODULE = """\
import os

class Widget:
    \"\"\"A widget.\"\"\"

    def render(self, value):
        return os.linesep.join(str(value))


def make_widget():
    return Widget()
"""


@pytest_asyncio.fixture()
async def store_factory() -> AsyncIterator[Any]:
    """Builder for a :class:`QdrantStore` with exact-name (concurrency-safe) teardown."""
    from conftest import QDRANT_URL, _qdrant_api_key

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


def _slug() -> str:
    return f"test_{uuid.uuid4().hex}"


def _config(slug: str, live_path: Path) -> LoreConfig:
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
                "tier": "custom",
                "watch": "live",
                "path": str(live_path),
                "include": ["**/*.py", "**/*.md"],
            }
        ],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}, ".md": {"chunker": "markdown"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9201},
    }
    return LoreConfig.model_validate(payload)


def _make_indexer(
    *,
    config: LoreConfig,
    store: QdrantStore,
    embedder: Embedder,
    manifest: Manifest,
    snapshot_root: Path,
    code_graph: CodeGraph | None = None,
) -> Indexer:
    """Wire an :class:`Indexer`, optionally with a :class:`CodeGraph` (the new seam)."""
    server = LoreServer(config)
    return Indexer(
        store=store,
        embedder=embedder,
        manifest=manifest,
        registry=server.registry,
        source_providers=[],
        config=config,
        snapshot_root=snapshot_root,
        code_graph=code_graph,
    )


def _qnames(graph: CodeGraph, tier: str, file_path: str) -> set[str]:
    """Return the set of qualified names the graph holds for ``(tier, file_path)``."""
    rows = graph.connection.execute(
        "SELECT qualified_name FROM nodes WHERE tier = ? AND file_path = ?",
        (tier, file_path),
    ).fetchall()
    return {row["qualified_name"] for row in rows}


class TestGraphWiring:
    """``index_file`` keeps the code-graph fresh; a purge removes the slice."""

    async def test_indexer_without_graph_is_unaffected(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        # Backward compatibility: an Indexer with NO code_graph indexes a file
        # exactly as before — no graph dependency, no crash.
        slug = _slug()
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        config = _config(slug, tmp_path / "live")
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap", code_graph=None,
        )
        outcome = await indexer.index_file("custom", "src/widget.py", _PY_MODULE)
        assert outcome.n_chunks >= 3

    async def test_index_python_file_populates_graph(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        config = _config(slug, tmp_path / "live")
        manifest = Manifest(str(tmp_path / "m.db"))
        graph = CodeGraph(str(tmp_path / "graph.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap", code_graph=graph,
        )

        await indexer.index_file("custom", "src/widget.py", _PY_MODULE)

        qnames = _qnames(graph, "custom", "src/widget.py")
        # module → src.widget; class Widget; its method render; function make_widget.
        assert "src.widget" in qnames
        assert "src.widget.Widget" in qnames
        assert "src.widget.Widget.render" in qnames
        assert "src.widget.make_widget" in qnames
        # The query layer reaches the wired-in symbols.
        importers = graph.what_imports("os")
        assert any(n.qualified_name == "src.widget" for n in importers)

    async def test_reindex_updates_graph_slice_transactionally(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        config = _config(slug, tmp_path / "live")
        manifest = Manifest(str(tmp_path / "m.db"))
        graph = CodeGraph(str(tmp_path / "graph.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap", code_graph=graph,
        )

        await indexer.index_file("custom", "src/m.py", "def alpha_marker():\n    return 1\n")
        assert "src.m.alpha_marker" in _qnames(graph, "custom", "src/m.py")

        # Re-index with a DIFFERENT function: the old node is gone, the new present,
        # no orphan from the prior build.
        await indexer.index_file("custom", "src/m.py", "def beta_marker():\n    return 2\n")
        qnames = _qnames(graph, "custom", "src/m.py")
        assert "src.m.beta_marker" in qnames
        assert "src.m.alpha_marker" not in qnames

    async def test_delete_file_graph_purges_slice(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        # The purge path the watcher drives on a delete/move-from must remove the
        # file's graph slice (the graph module's delete primitive, now reachable).
        slug = _slug()
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        config = _config(slug, tmp_path / "live")
        manifest = Manifest(str(tmp_path / "m.db"))
        graph = CodeGraph(str(tmp_path / "graph.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap", code_graph=graph,
        )
        await indexer.index_file("custom", "src/widget.py", _PY_MODULE)
        assert _qnames(graph, "custom", "src/widget.py")

        graph.delete_file_graph("custom", "src/widget.py")
        assert _qnames(graph, "custom", "src/widget.py") == set()

    async def test_failed_embed_does_not_refresh_graph(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        # A re-index whose embeds all FAIL keeps the prior graph slice (last-good),
        # NOT the new unembeddable content — the graph must not diverge from what
        # is actually indexed.
        slug = _slug()
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        config = _config(slug, tmp_path / "live")
        manifest = Manifest(str(tmp_path / "m.db"))
        graph = CodeGraph(str(tmp_path / "graph.db"))

        # v1 indexes clean → a graph slice with gamma_marker.
        good = FakeEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=good, manifest=manifest,
            snapshot_root=tmp_path / "snap", code_graph=graph,
        )
        v1 = "def gamma_marker():\n    return 1\n"
        await indexer.index_file("custom", "src/m.py", v1)
        assert "src.m.gamma_marker" in _qnames(graph, "custom", "src/m.py")

        # v2 changed content, embedder fails ALL its chunks → state failed.
        v2 = "def delta_marker():\n    return 2\n"
        probe = FakeEmbedder(dim=_DIM)
        probe_indexer = _make_indexer(
            config=config, store=store, embedder=probe,
            manifest=Manifest(str(tmp_path / "p.db")), snapshot_root=tmp_path / "snap0",
        )
        v2_texts = probe_indexer.chunk_texts("custom", "src/m.py", v2)
        failing = FakeEmbedder(dim=_DIM, fail_inputs=set(v2_texts))
        indexer2 = _make_indexer(
            config=config, store=store, embedder=failing, manifest=manifest,
            snapshot_root=tmp_path / "snap", code_graph=graph,
        )
        outcome = await indexer2.index_file("custom", "src/m.py", v2)

        assert outcome.state == STATE_FAILED
        qnames = _qnames(graph, "custom", "src/m.py")
        # The failed new content never entered the graph; the last-good slice holds.
        assert "src.m.gamma_marker" in qnames
        assert "src.m.delta_marker" not in qnames

    async def test_non_python_file_adds_no_graph_nodes(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        # A markdown file indexed through the same path must not synthesise a
        # spurious module node — the graph is a Python AST structure only.
        slug = _slug()
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        config = _config(slug, tmp_path / "live")
        manifest = Manifest(str(tmp_path / "m.db"))
        graph = CodeGraph(str(tmp_path / "graph.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap", code_graph=graph,
        )

        await indexer.index_file("custom", "README.md", "# Title\n\nProse.\n")

        # No nodes for the markdown file (no module node synthesised).
        assert _qnames(graph, "custom", "README.md") == set()
        # And globally there is no node at all for it.
        all_nodes = graph.connection.execute(
            "SELECT COUNT(*) AS c FROM nodes WHERE kind = ?", (KIND_MODULE,)
        ).fetchone()
        assert all_nodes["c"] == 0

    async def test_graph_slices_are_tier_scoped(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        # Two tiers' copies of one path keep independent graph slices: rebuilding
        # one tier's file must not touch the other tier's nodes (C1).
        slug = _slug()
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        config = _config(slug, tmp_path / "live")
        manifest = Manifest(str(tmp_path / "m.db"))
        graph = CodeGraph(str(tmp_path / "graph.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap", code_graph=graph,
        )

        await indexer.index_file("custom", "src/m.py", "def custom_fn():\n    return 1\n")
        await indexer.index_file("community", "src/m.py", "def community_fn():\n    return 2\n")

        # Rebuild the custom copy; the community slice is untouched.
        await indexer.index_file("custom", "src/m.py", "def custom_fn_v2():\n    return 3\n")
        custom_q = _qnames(graph, "custom", "src/m.py")
        community_q = _qnames(graph, "community", "src/m.py")
        assert "src.m.custom_fn_v2" in custom_q
        assert "src.m.custom_fn" not in custom_q
        assert "src.m.community_fn" in community_q  # sibling tier intact

        # The function nodes are scoped to their tiers — no cross-contamination.
        community_funcs = {
            n.qualified_name
            for n in [graph._row_to_node(r) for r in graph.connection.execute(  # noqa: SLF001
                "SELECT * FROM nodes WHERE tier = ? AND kind = ?", ("community", KIND_FUNCTION)
            ).fetchall()]
        }
        assert community_funcs == {"src.m.community_fn"}


class TestImportableModuleNaming:
    """End-to-end: indexed nodes/edges name modules by the TRUE importable path.

    Drives a synthetic fixture package on disk through a full ``index_tier`` walk
    (the production ingestion seam that owns the tier filesystem ``base``), shaped
    as a WORKSPACE-MEMBER layout — a leading ``member/`` dir with NO ``__init__.py``
    wrapping the real package ``pkg`` — exactly the split-brain trigger:
    ``member/pkg/a.py`` is importable as ``pkg.a`` but the buggy full-path join
    named it ``member.pkg.a`` (doubled), which never matched the import-edge
    ``dst`` strings (``pkg.a``).

    The regressions pinned here (each fails on the doubled-form implementation):

    * node qualified-names are the importable form (``pkg.a``, ``pkg.a.Foo``,
      ``pkg.sub.b``, ``pkg.sub.b.Bar``) — NOT ``member.pkg.*``;
    * ``what_imports("pkg.a")`` returns ``pkg.sub.b`` AND querying the module by
      its OWN canonical node name returns the SAME consumers (form-unification —
      the silent false-negative the bug caused);
    * ``blast_radius("pkg.a", depth=2)`` reaches BOTH ``pkg.sub.b`` (hop 1) AND
      ``pkg.c`` (hop 2, imports b which imports a) — transitive reverse-import
      now traverses because hop-1 importers come back in the form that re-matches
      import-edge ``dst`` strings.
    """

    @staticmethod
    def _build_member_pkg(live: Path) -> None:
        """Lay the workspace-member fixture package under ``live`` (the tier root).

        ``live/member/`` has NO ``__init__.py`` (the workspace-member dir, wrongly
        doubled by the bug); ``live/member/pkg/`` is the real importable package
        top. ``pkg.a`` defines ``Foo``; ``pkg.sub.b`` imports ``Foo`` and defines
        ``Bar(Foo)``; ``pkg.c`` imports ``Bar`` (the second reverse-import hop).
        """
        member = live / "member"
        pkg = member / "pkg"
        sub = pkg / "sub"
        sub.mkdir(parents=True)
        # member/ is deliberately NOT a package (no __init__.py) — the doubled seg.
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (sub / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "a.py").write_text(
            'class Foo:\n    """A base."""\n\n    def go(self):\n        return 1\n',
            encoding="utf-8",
        )
        (sub / "b.py").write_text(
            "from pkg.a import Foo\n\n\nclass Bar(Foo):\n    pass\n",
            encoding="utf-8",
        )
        (pkg / "c.py").write_text(
            "from pkg.sub.b import Bar\n\n\ndef use_bar():\n    return Bar()\n",
            encoding="utf-8",
        )

    async def _index_member_pkg(
        self, tmp_path: Path, store_factory: Any
    ) -> CodeGraph:
        """Index the member-pkg fixture through a real ``index_tier`` walk."""
        slug = _slug()
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        live = tmp_path / "live"
        live.mkdir(parents=True)
        self._build_member_pkg(live)
        config = _config(slug, live)
        manifest = Manifest(str(tmp_path / "m.db"))
        graph = CodeGraph(str(tmp_path / "graph.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap", code_graph=graph,
        )
        # Walk the live tier (the only root in _config): every .py file is chunked,
        # embedded, and graph-sliced through the production path that owns ``base``.
        await indexer.index_tier(config.effective_roots[0])
        return graph

    async def test_nodes_use_importable_not_doubled_names(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        graph = await self._index_member_pkg(tmp_path, store_factory)
        all_qnames = {
            row["qualified_name"]
            for row in graph.connection.execute(
                "SELECT qualified_name FROM nodes"
            ).fetchall()
        }
        # The TRUE importable names are present …
        assert "pkg.a" in all_qnames
        assert "pkg.a.Foo" in all_qnames
        assert "pkg.sub.b" in all_qnames
        assert "pkg.sub.b.Bar" in all_qnames
        assert "pkg.c" in all_qnames
        # … and the DOUBLED workspace-member form is NOWHERE.
        assert not any(name.startswith("member.") for name in all_qnames)

    async def test_what_imports_is_form_unified(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        graph = await self._index_member_pkg(tmp_path, store_factory)
        # b.py does ``from pkg.a import Foo`` → pkg.sub.b imports pkg.a.
        by_import_string = {n.qualified_name for n in graph.what_imports("pkg.a")}
        assert "pkg.sub.b" in by_import_string
        # Querying pkg.a by its OWN canonical NODE name returns the SAME consumers
        # (the form-unification: the bug made this a silent empty false-negative,
        # because the node was named ``member.pkg.a`` and never matched ``pkg.a``).
        node = graph.connection.execute(
            "SELECT qualified_name FROM nodes WHERE kind = ? AND qualified_name = ?",
            (KIND_MODULE, "pkg.a"),
        ).fetchone()
        assert node is not None  # the canonical node IS named pkg.a
        by_canonical_name = {n.qualified_name for n in graph.what_imports(node["qualified_name"])}
        assert by_canonical_name == by_import_string

    async def test_blast_radius_traverses_transitive_reverse_imports(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        graph = await self._index_member_pkg(tmp_path, store_factory)
        # c imports b; b imports a. The blast radius of pkg.a (who breaks if a
        # changes) must reach b (hop 1) AND c (hop 2) — transitive reverse-import.
        affected = {
            n.qualified_name
            for n in graph.blast_radius("pkg.a", depth=2, max_results=100)
        }
        assert "pkg.sub.b" in affected  # hop 1: imports pkg.a
        assert "pkg.c" in affected  # hop 2: imports pkg.sub.b which imports pkg.a

    async def test_tests_for_still_works_with_importable_names(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        # tests_for must keep working under the corrected naming: a test-glob file
        # importing the module under test is a test for it.
        slug = _slug()
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        live = tmp_path / "live"
        live.mkdir(parents=True)
        self._build_member_pkg(live)
        # A test file (test-glob path) under the same package importing pkg.a.
        (live / "member" / "pkg" / "test_a.py").write_text(
            "from pkg.a import Foo\n\n\ndef test_go():\n    assert Foo().go() == 1\n",
            encoding="utf-8",
        )
        config = _config(slug, live)
        manifest = Manifest(str(tmp_path / "m.db"))
        graph = CodeGraph(str(tmp_path / "graph.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap", code_graph=graph,
        )
        await indexer.index_tier(config.effective_roots[0])

        related_files = {n.file_path for n in graph.tests_for("pkg.a")}
        assert "member/pkg/test_a.py" in related_files


class TestWatcherAndReconcilePurgeGraph:
    """The watcher delete-purge and the reconcile deletion-sweep remove the slice."""

    async def test_watcher_delete_purges_graph_slice(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        # A watcher delete event (the live-watch purge path) must remove the
        # deleted file's graph slice, not just its vector points — else the graph
        # would serve a symbol whose source is gone (an anti-hallucination defect).
        slug = _slug()
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        live = tmp_path / "live"
        (live / "src").mkdir(parents=True)
        py = live / "src" / "widget.py"
        py.write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        manifest = Manifest(str(tmp_path / "m.db"))
        graph = CodeGraph(str(tmp_path / "graph.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap", code_graph=graph,
        )
        await indexer.index_file("custom", "src/widget.py", _PY_MODULE)
        assert _qnames(graph, "custom", "src/widget.py")

        engine = ReconcileEngine(
            indexer=indexer, manifest=manifest, store=store, config=config, code_graph=graph
        )
        watcher = LiveWatcher(
            indexer=indexer, manifest=manifest, store=store, config=config,
            loop=asyncio.get_running_loop(), reconcile_engine=engine, code_graph=graph,
        )
        # Delete the file on disk, then drive the delete seam + drain the queue.
        py.unlink()
        watcher.on_deleted_path(str(py))
        await watcher.drain()

        assert _qnames(graph, "custom", "src/widget.py") == set()

    async def test_reconcile_deletion_sweep_purges_graph_slice(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        # The reconcile deletion sweep (startup/periodic backstop) purges the graph
        # slice of a file that vanished from disk while the watcher was down.
        slug = _slug()
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        live = tmp_path / "live"
        (live / "src").mkdir(parents=True)
        py = live / "src" / "gone.py"
        py.write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        manifest = Manifest(str(tmp_path / "m.db"))
        graph = CodeGraph(str(tmp_path / "graph.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap", code_graph=graph,
        )
        # First reconcile indexes the on-disk file → graph slice present.
        engine = ReconcileEngine(
            indexer=indexer, manifest=manifest, store=store, config=config, code_graph=graph
        )
        await engine.reconcile()
        assert _qnames(graph, "custom", "src/gone.py")

        # Delete the file; the next reconcile's deletion sweep must purge its slice.
        py.unlink()
        summary = await engine.reconcile()
        assert summary.files_purged >= 1
        assert _qnames(graph, "custom", "src/gone.py") == set()
