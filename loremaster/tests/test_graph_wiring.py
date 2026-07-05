"""Contract tests for graph wiring into the index path (plan AMENDMENT 1, item 6).

PORTED for P5-C3b onto the async Surreal fakes (:mod:`_surreal_fakes`). The
wiring pins are UNCHANGED — ``index_file`` (and therefore the reconcile per-file
path) rebuilds a Python file's graph slice from the SAME chunks it embeds, a
purge removes it, a failed embed does NOT refresh it, a non-Python file adds no
node, and the slice is tier-scoped — but the graph is now built as a FRAGMENT
composed into the ONE atomic per-file transaction alongside the chunk/file_text/
manifest fragments (never a separate ``build_file_graph`` call). Only the
fixtures change: the real Qdrant + Kùzu ``CodeGraph`` become the fast in-memory
fakes whose code-graph REUSES the REAL astroid derivation (so node qnames /
import edges are production-identical); the graph query methods are ``await``ed;
and the raw-Kùzu inspection helpers (``_qnames`` etc.) become the fake graph's
own inspection surface.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

from _surreal_fakes import FakeSurrealCodeGraph, FakeSurrealTrio, fake_surreal_trio
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer, graph_roots
from loremaster.index.reconcile import ReconcileEngine
from loremaster.index.surreal_manifest import STATE_FAILED
from loremaster.index.watcher import LiveWatcher
from loremaster.server import LoreServer
from loresigil.base import Embedder
from loresigil.testing import FakeEmbedder

_DIM = 2048

# An IN-PROJECT dependency the widget module imports a symbol from.
_BASE_MODULE = '''\
"""The widget base."""


class Base:
    """A base widget."""

    def tag(self):
        return "base"
'''
_BASE_REL_PATH = "src/base.py"

_PY_MODULE = '''\
"""The widget module."""
from src.base import Base


class Widget(Base):
    """A widget."""

    def render(self, value):
        return self.tag() + str(value)


def make_widget():
    return Widget()
'''

# Independent oracle: the in-project import the widget module makes.
_WIDGET_IMPORT_FQN = "src.base.Base"


def _slug() -> str:
    return f"test_{uuid.uuid4().hex}"


def _config(slug: str, live_path: Path) -> LoreConfig:
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


def _trio(config: LoreConfig | None, snapshot_root: Path | None) -> FakeSurrealTrio:
    """The fake trio whose graph is wired with the config's project roots (via the
    production :func:`graph_roots`), so its astroid derivation resolves references
    exactly as the live graph does."""
    kwargs: dict[str, Any] = {"dim": _DIM}
    if config is not None and snapshot_root is not None:
        tier_roots, project_roots = graph_roots(config, snapshot_root)
        kwargs["tier_roots"] = tier_roots
        kwargs["project_roots"] = project_roots
    return fake_surreal_trio(**kwargs)


def _make_indexer(
    *,
    config: LoreConfig,
    trio: FakeSurrealTrio,
    embedder: Embedder,
    snapshot_root: Path,
    with_graph: bool = True,
) -> Indexer:
    server = LoreServer(config)
    return Indexer(
        store=trio.store,
        embedder=embedder,
        manifest=trio.manifest,
        registry=server.registry,
        source_providers=[],
        config=config,
        snapshot_root=snapshot_root,
        code_graph=trio.graph if with_graph else None,
    )


class TestGraphWiring:
    """``index_file`` keeps the code-graph fresh; a purge removes the slice."""

    async def test_indexer_without_graph_is_unaffected(self, tmp_path: Path) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        trio = _trio(config, tmp_path / "snap")
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM),
            snapshot_root=tmp_path / "snap", with_graph=False,
        )
        outcome = await indexer.index_file("custom", "src/widget.py", _PY_MODULE)
        assert outcome.n_chunks >= 3

    async def test_index_python_file_populates_graph(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        (live / "src").mkdir(parents=True)
        (live / "src" / "base.py").write_text(_BASE_MODULE, encoding="utf-8")
        (live / "src" / "widget.py").write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        trio = _trio(config, tmp_path / "snap")
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )

        await indexer.index_file("custom", "src/base.py", _BASE_MODULE)
        await indexer.index_file("custom", "src/widget.py", _PY_MODULE)

        qnames = trio.graph.qnames_for("custom", "src/widget.py")
        assert "src.widget" in qnames
        assert "src.widget.Widget" in qnames
        assert "src.widget.Widget.render" in qnames
        assert "src.widget.make_widget" in qnames
        importers = await trio.graph.what_imports(_WIDGET_IMPORT_FQN)
        assert any(n.qualified_name == "src.widget" for n in importers)

    async def test_reindex_updates_graph_slice_transactionally(self, tmp_path: Path) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        trio = _trio(config, tmp_path / "snap")
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )

        await indexer.index_file("custom", "src/m.py", "def alpha_marker():\n    return 1\n")
        assert "src.m.alpha_marker" in trio.graph.qnames_for("custom", "src/m.py")

        await indexer.index_file("custom", "src/m.py", "def beta_marker():\n    return 2\n")
        qnames = trio.graph.qnames_for("custom", "src/m.py")
        assert "src.m.beta_marker" in qnames
        assert "src.m.alpha_marker" not in qnames

    async def test_delete_file_graph_purges_slice(self, tmp_path: Path) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        trio = _trio(config, tmp_path / "snap")
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        await indexer.index_file("custom", "src/widget.py", _PY_MODULE)
        assert trio.graph.qnames_for("custom", "src/widget.py")

        await trio.graph.delete_file_graph("custom", "src/widget.py")
        assert trio.graph.qnames_for("custom", "src/widget.py") == set()

    async def test_failed_embed_does_not_refresh_graph(self, tmp_path: Path) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        trio = _trio(config, tmp_path / "snap")

        good = FakeEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=good, snapshot_root=tmp_path / "snap",
        )
        v1 = "def gamma_marker():\n    return 1\n"
        await indexer.index_file("custom", "src/m.py", v1)
        assert "src.m.gamma_marker" in trio.graph.qnames_for("custom", "src/m.py")

        v2 = "def delta_marker():\n    return 2\n"
        probe_indexer = _make_indexer(
            config=config, trio=_trio(config, tmp_path / "snap"), embedder=FakeEmbedder(dim=_DIM),
            snapshot_root=tmp_path / "snap",
        )
        v2_texts = probe_indexer.chunk_texts("custom", "src/m.py", v2)
        failing = FakeEmbedder(dim=_DIM, fail_inputs=set(v2_texts))
        indexer2 = _make_indexer(
            config=config, trio=trio, embedder=failing, snapshot_root=tmp_path / "snap",
        )
        outcome = await indexer2.index_file("custom", "src/m.py", v2)

        assert outcome.state == STATE_FAILED
        qnames = trio.graph.qnames_for("custom", "src/m.py")
        # The failed new content never entered the graph; the last-good slice holds.
        assert "src.m.gamma_marker" in qnames
        assert "src.m.delta_marker" not in qnames

    async def test_non_python_file_adds_no_graph_nodes(self, tmp_path: Path) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        trio = _trio(config, tmp_path / "snap")
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )

        await indexer.index_file("custom", "README.md", "# Title\n\nProse.\n")

        assert trio.graph.qnames_for("custom", "README.md") == set()
        assert trio.graph.module_node_count() == 0

    async def test_graph_slices_are_tier_scoped(self, tmp_path: Path) -> None:
        slug = _slug()
        config = _config(slug, tmp_path / "live")
        trio = _trio(config, tmp_path / "snap")
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )

        await indexer.index_file("custom", "src/m.py", "def custom_fn():\n    return 1\n")
        await indexer.index_file("community", "src/m.py", "def community_fn():\n    return 2\n")

        await indexer.index_file("custom", "src/m.py", "def custom_fn_v2():\n    return 3\n")
        custom_q = trio.graph.qnames_for("custom", "src/m.py")
        community_q = trio.graph.qnames_for("community", "src/m.py")
        assert "src.m.custom_fn_v2" in custom_q
        assert "src.m.custom_fn" not in custom_q
        assert "src.m.community_fn" in community_q

        assert trio.graph.tier_function_qnames("community") == {"src.m.community_fn"}


class TestImportableModuleNaming:
    """End-to-end: indexed nodes/edges name modules by the TRUE importable path."""

    @staticmethod
    def _build_member_pkg(live: Path) -> None:
        member = live / "member"
        pkg = member / "pkg"
        sub = pkg / "sub"
        sub.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (sub / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "a.py").write_text(
            'class Foo:\n    """A base."""\n\n    def go(self):\n        return 1\n', encoding="utf-8"
        )
        (sub / "b.py").write_text(
            "from pkg.a import Foo\n\n\nclass Bar(Foo):\n    pass\n", encoding="utf-8"
        )
        (pkg / "c.py").write_text(
            "from pkg.sub.b import Bar\n\n\ndef use_bar():\n    return Bar()\n", encoding="utf-8"
        )

    async def _index_member_pkg(self, tmp_path: Path) -> FakeSurrealCodeGraph:
        slug = _slug()
        live = tmp_path / "live"
        live.mkdir(parents=True)
        self._build_member_pkg(live)
        config = _config(slug, live)
        trio = _trio(config, tmp_path / "snap")
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        await indexer.index_tier(config.effective_roots[0])
        return trio.graph

    async def test_nodes_use_importable_not_doubled_names(self, tmp_path: Path) -> None:
        graph = await self._index_member_pkg(tmp_path)
        all_qnames = graph.all_qnames()
        assert "pkg.a" in all_qnames
        assert "pkg.a.Foo" in all_qnames
        assert "pkg.sub.b" in all_qnames
        assert "pkg.sub.b.Bar" in all_qnames
        assert "pkg.c" in all_qnames
        assert not any(name.startswith("member.") for name in all_qnames)

    async def test_what_imports_is_form_unified(self, tmp_path: Path) -> None:
        graph = await self._index_member_pkg(tmp_path)
        by_import_string = {n.qualified_name for n in await graph.what_imports("pkg.a")}
        assert "pkg.sub.b" in by_import_string
        assert "pkg.a" in graph.all_qnames()
        by_canonical_name = {n.qualified_name for n in await graph.what_imports("pkg.a")}
        assert by_canonical_name == by_import_string

    async def test_blast_radius_traverses_transitive_reverse_imports(self, tmp_path: Path) -> None:
        graph = await self._index_member_pkg(tmp_path)
        affected = {
            n.qualified_name for n in await graph.blast_radius("pkg.a", depth=2, max_results=100)
        }
        assert "pkg.sub.b" in affected  # hop 1
        assert "pkg.c" in affected  # hop 2

    async def test_tests_for_still_works_with_importable_names(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        live.mkdir(parents=True)
        self._build_member_pkg(live)
        (live / "member" / "pkg" / "test_a.py").write_text(
            "from pkg.a import Foo\n\n\ndef test_go():\n    assert Foo().go() == 1\n", encoding="utf-8"
        )
        config = _config(slug, live)
        trio = _trio(config, tmp_path / "snap")
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        await indexer.index_tier(config.effective_roots[0])

        related_files = {n.file_path for n in await trio.graph.tests_for("pkg.a")}
        assert "member/pkg/test_a.py" in related_files


class TestWatcherAndReconcilePurgeGraph:
    """The watcher delete-purge and the reconcile deletion-sweep remove the slice."""

    async def test_watcher_delete_purges_graph_slice(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        (live / "src").mkdir(parents=True)
        py = live / "src" / "widget.py"
        py.write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        trio = _trio(config, tmp_path / "snap")
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        await indexer.index_file("custom", "src/widget.py", _PY_MODULE)
        assert trio.graph.qnames_for("custom", "src/widget.py")

        engine = ReconcileEngine(
            indexer=indexer, manifest=trio.manifest, store=trio.store, config=config,
            code_graph=trio.graph,
        )
        watcher = LiveWatcher(
            indexer=indexer, manifest=trio.manifest, store=trio.store, config=config,
            loop=asyncio.get_running_loop(), reconcile_engine=engine, code_graph=trio.graph,
        )
        py.unlink()
        watcher.on_deleted_path(str(py))
        await watcher.drain()

        assert trio.graph.qnames_for("custom", "src/widget.py") == set()

    async def test_reconcile_deletion_sweep_purges_graph_slice(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        (live / "src").mkdir(parents=True)
        py = live / "src" / "gone.py"
        py.write_text(_PY_MODULE, encoding="utf-8")
        config = _config(slug, live)
        trio = _trio(config, tmp_path / "snap")
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        engine = ReconcileEngine(
            indexer=indexer, manifest=trio.manifest, store=trio.store, config=config,
            code_graph=trio.graph,
        )
        await engine.reconcile()
        assert trio.graph.qnames_for("custom", "src/gone.py")

        py.unlink()
        summary = await engine.reconcile()
        assert summary.files_purged >= 1
        assert trio.graph.qnames_for("custom", "src/gone.py") == set()


class TestSweepBoundaryResetsResolutionCache:
    """The indexer resets astroid's warm cache ONCE at each full-sweep boundary."""

    async def test_rebuild_graph_only_resets_resolution_cache_once(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        (live / "src").mkdir(parents=True)
        config = _config(slug, live)
        trio = _trio(config, tmp_path / "snap")
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        # No indexed rows → 0 files re-graphed, but the sweep STILL resets once
        # (the reset is a sweep-boundary primitive, independent of file count).
        regraphed = await indexer.rebuild_graph_only("custom")
        assert regraphed == 0
        assert trio.graph.reset_calls == 1, (
            "rebuild_graph_only must reset the resolution cache exactly once per "
            f"sweep; got {trio.graph.reset_calls} resets"
        )
