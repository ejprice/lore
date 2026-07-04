"""Contract tests for ``loremaster.index.reconcile`` — the startup + periodic sweep.

PORTED for P5-C3b: the :class:`~loremaster.index.reconcile.ReconcileEngine` is
rewired onto the async Surreal ports — its ``_purge_deletions`` composes ONE
atomic purge transaction per deleted file (store-delete + file_text-delete +
manifest-delete + graph-purge fragments through ``store.apply``) instead of the
old sequential ``store.delete_by_file`` + ``manifest.delete``. These tests keep
the SAME behavioural pins as the pre-port suite — only the fixtures change: the
real Qdrant + SQLite ``Manifest`` become the fast in-memory async fakes
(:mod:`_surreal_fakes`), store-side side-effect assertions are re-expressed over
the fake's recorded state, and every manifest read is ``await``ed.

The contract under test (unchanged):

* **Live-tier walk, content fast-path.** A first reconcile indexes every included
  file under a LIVE root; an immediate second reconcile of an unchanged tree
  re-embeds NOTHING.
* **Changed file → reindex.** Editing a file re-indexes exactly it.
* **Deleted file → purge.** A file gone from disk is purged from the store AND
  the manifest; a sibling tier's copy of the same path is untouched.
* **Resume non-indexed.** A ``failed``/``dirty`` row is re-attempted even when
  unchanged, and reaches ``indexed``.
* **Static-tier defer.** A matching version stamp SKIPS with ZERO walk/acquire;
  a changed stamp rebuilds it.
* **Summary.** ``reconcile()`` rolls up indexed/failed/skipped + rebuilt/skipped
  tiers plus the count of purged files.
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Any

import pytest
from _surreal_fakes import FakeSurrealTrio, fake_surreal_trio
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer, graph_roots
from loremaster.index.reconcile import ReconcileEngine
from loremaster.index.surreal_manifest import (
    STATE_DIRTY,
    STATE_FAILED,
    STATE_INDEXED,
)
from loremaster.server import LoreServer
from loremaster.source.local_directory import LocalDirectorySourceProvider
from loresigil.base import Embedder
from loresigil.testing import FakeEmbedder

_DIM = 2048
_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"


# --------------------------------------------------------------------------- #
# Recording / instrumented fakes
# --------------------------------------------------------------------------- #
class RecordingEmbedder(FakeEmbedder):
    """A :class:`FakeEmbedder` that records every ``embed_documents`` batch."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.embed_batches: list[list[str]] = []

    @property
    def supports_contextualized(self) -> bool:
        return False

    async def embed_documents(self, texts: list[str]) -> Any:
        self.embed_batches.append(list(texts))
        return await super().embed_documents(texts)

    @property
    def total_embedded(self) -> int:
        return sum(len(batch) for batch in self.embed_batches)


class ExplodingProvider:
    """A :class:`SourceProvider` whose ``acquire`` raises if ever called."""

    def __init__(self, tier: str) -> None:
        self.tier = tier
        self.acquired = False

    def acquire(self, tier: str, snapshot_root: Path) -> None:
        self.acquired = True
        raise AssertionError(f"acquire({tier!r}) must NOT run when the version stamp matches")


# --------------------------------------------------------------------------- #
# Corpus + config builders
# --------------------------------------------------------------------------- #
def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


_PY_MODULE = """\
import os

class Widget:
    \"\"\"A widget.\"\"\"

    def render(self, value):
        return os.linesep.join(str(value))


def make_widget():
    return Widget()
"""

_PY_MODULE_2 = """\
def champion_routing(week):
    \"\"\"Route the 36-week curve champion.\"\"\"
    return week * 2
"""


def _build_live_corpus(root: Path) -> None:
    _write(root / "src" / "widget.py", _PY_MODULE)
    _write(root / "src" / "routing.py", _PY_MODULE_2)
    _write(root / "README.md", "# Project\n\nSome docs.\n")
    _write(root / "src" / "bundle.min.js", "var x=1;")
    _write(root / "src" / "api_pb2.py", "def generated_proto_marker():\n    return 1\n")
    _write(root / ".git" / "config.py", "SECRET = 'do-not-index'\n")
    _write(root / ".venv" / "lib" / "vendored.py", "junk = 1\n")


def _build_static_source(root: Path) -> None:
    _write(root / "lib" / "core.py", _PY_MODULE)


def _config(
    *,
    slug: str,
    live_path: Path | None = None,
    static_source: Path | None = None,
    static_version: str = "1.0.0",
) -> LoreConfig:
    roots: list[dict[str, Any]] = []
    if live_path is not None:
        roots.append(
            {
                "tier": "custom",
                "watch": "live",
                "path": str(live_path),
                "include": ["**/*.py", "**/*.md"],
                "exclude": ["**/*.min.js"],
            }
        )
    if static_source is not None:
        roots.append(
            {
                "tier": "community",
                "watch": "static",
                "source": str(static_source),
                "version": static_version,
                "provider": "local_directory",
                "include": ["**/*.py"],
            }
        )
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": _TEI_BASE_URL,
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": _TEI_KEY_ENV,
            "tokenizer": "voyage-4-nano",
        },
        "roots": roots,
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": ["**/*.min.js", "**/*_pb2.py"],
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


def _slug() -> str:
    return f"test_{uuid.uuid4().hex}"


# --------------------------------------------------------------------------- #
# Fake-trio wiring
# --------------------------------------------------------------------------- #
def _trio(*, config: LoreConfig | None = None, snapshot_root: Path | None = None,
          with_graph: bool = False) -> FakeSurrealTrio:
    kwargs: dict[str, Any] = {"dim": _DIM}
    if with_graph and config is not None and snapshot_root is not None:
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
    providers: list[Any] | None = None,
    with_graph: bool = False,
) -> Indexer:
    server = LoreServer(config)
    built: list[Any] = list(server.source_providers) if providers is None else list(providers)
    if providers is None:
        for root in config.roots:
            if root.watch == "static" and root.source is not None:
                built.append(LocalDirectorySourceProvider(root.tier, Path(root.source)))
    return Indexer(
        store=trio.store,
        embedder=embedder,
        manifest=trio.manifest,
        registry=server.registry,
        source_providers=built,
        config=config,
        snapshot_root=snapshot_root,
        code_graph=trio.graph if with_graph else None,
    )


def _make_engine(
    *, config: LoreConfig, indexer: Indexer, trio: FakeSurrealTrio, with_graph: bool = False
) -> ReconcileEngine:
    return ReconcileEngine(
        indexer=indexer,
        manifest=trio.manifest,
        store=trio.store,
        config=config,
        code_graph=trio.graph if with_graph else None,
    )


# --------------------------------------------------------------------------- #
# Reconcile-summary logging (the liveness heartbeat)
# --------------------------------------------------------------------------- #
class TestReconcileSummaryLogging:
    """``reconcile`` always logs a ``reconcile.summary`` heartbeat (caplog)."""

    async def test_reconcile_logs_summary_counts(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, trio=trio)

        with caplog.at_level(logging.INFO, logger="loremaster.index.reconcile"):
            summary = await engine.reconcile()

        events = [r for r in caplog.records if r.message == "reconcile.summary"]
        assert len(events) == 1
        record = events[0]
        assert record.levelno == logging.INFO
        assert record.files_indexed == summary.files_indexed  # type: ignore[attr-defined]
        assert record.files_failed == summary.files_failed  # type: ignore[attr-defined]
        assert record.files_skipped == summary.files_skipped  # type: ignore[attr-defined]
        assert record.files_purged == summary.files_purged  # type: ignore[attr-defined]
        assert record.tiers_rebuilt == summary.tiers_rebuilt  # type: ignore[attr-defined]
        assert record.tiers_skipped == summary.tiers_skipped  # type: ignore[attr-defined]
        assert isinstance(record.duration_ms, (int, float)) and record.duration_ms >= 0  # type: ignore[attr-defined]
        assert record.files_indexed >= 1  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
# Live-tier walk + fast-path
# --------------------------------------------------------------------------- #
class TestLiveReconcile:
    """A live root is walked; an unchanged second sweep re-embeds nothing."""

    async def test_first_reconcile_indexes_included_files(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, trio=trio)

        summary = await engine.reconcile()

        indexed_paths = {row.file_path for row in await trio.manifest.files_for_tier("custom")}
        assert "src/widget.py" in indexed_paths
        assert "src/routing.py" in indexed_paths
        assert "README.md" in indexed_paths
        assert "src/bundle.min.js" not in indexed_paths
        assert "src/api_pb2.py" not in indexed_paths
        assert not any(p.startswith(".git/") for p in indexed_paths)
        assert not any(p.startswith(".venv/") for p in indexed_paths)
        assert summary.files_indexed >= 3
        assert "src/widget.py" in trio.store.stored_file_paths()

    async def test_second_reconcile_unchanged_tree_zero_embeds(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, trio=trio)

        await engine.reconcile()
        embedded_after_first = embedder.total_embedded
        assert embedded_after_first >= 3

        second = await engine.reconcile()
        assert embedder.total_embedded == embedded_after_first
        assert second.files_indexed == 0
        assert second.files_skipped >= 3

    async def test_changed_file_is_reindexed_others_fast_pathed(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, trio=trio)
        await engine.reconcile()
        baseline = embedder.total_embedded

        edited = live / "src" / "routing.py"
        edited.write_text("def reconcile_marker_xyz(week):\n    return week\n", encoding="utf-8")
        st = edited.stat()
        os.utime(edited, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))

        second = await engine.reconcile()
        assert embedder.total_embedded > baseline
        assert second.files_indexed >= 1
        identities = trio.store.identities_for("custom", "src/routing.py")
        assert "reconcile_marker_xyz" in identities
        assert "champion_routing" not in identities


# --------------------------------------------------------------------------- #
# Deleted file → purge
# --------------------------------------------------------------------------- #
class TestPurgeDeleted:
    """A file gone from disk is purged from the store AND the manifest."""

    async def test_deleted_file_is_purged_from_store_and_manifest(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, trio=trio)
        await engine.reconcile()
        assert await trio.manifest.get("custom", "src/routing.py") is not None
        assert "src/routing.py" in trio.store.stored_file_paths()

        (live / "src" / "routing.py").unlink()
        summary = await engine.reconcile()

        assert await trio.manifest.get("custom", "src/routing.py") is None
        assert "src/routing.py" not in trio.store.stored_file_paths()
        assert await trio.manifest.get("custom", "src/widget.py") is not None
        assert "src/widget.py" in trio.store.stored_file_paths()
        assert summary.files_purged >= 1

    async def test_purge_is_tier_scoped_sibling_survives(self, tmp_path: Path) -> None:
        """A delete in the live tier never purges another tier's copy of the path."""
        slug = _slug()
        live = tmp_path / "live"
        _write(live / "shared.py", _PY_MODULE_2)
        static_src = tmp_path / "community_src"
        _write(static_src / "shared.py", _PY_MODULE)
        config = _config(slug=slug, live_path=live, static_source=static_src)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, trio=trio)
        await engine.reconcile()
        assert await trio.manifest.get("custom", "shared.py") is not None
        assert await trio.manifest.get("community", "shared.py") is not None

        (live / "shared.py").unlink()
        await engine.reconcile()

        # The custom copy is purged; the community copy survives entirely.
        assert await trio.manifest.get("custom", "shared.py") is None
        assert await trio.manifest.get("community", "shared.py") is not None
        assert trio.store.identities_for("custom", "shared.py") == set()
        assert trio.store.identities_for("community", "shared.py")  # sibling intact


# --------------------------------------------------------------------------- #
# Resume a non-indexed file
# --------------------------------------------------------------------------- #
class TestResumeNonIndexed:
    """A file the manifest left non-``indexed`` is re-attempted, even if unchanged."""

    async def test_failed_file_is_resumed_to_indexed(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, trio=trio)
        await engine.reconcile()

        await trio.manifest.set_state("custom", "src/widget.py", STATE_FAILED)
        failed_row = await trio.manifest.get("custom", "src/widget.py")
        assert failed_row is not None and failed_row.state == STATE_FAILED
        embedded_before_resume = embedder.total_embedded

        summary = await engine.reconcile()

        assert embedder.total_embedded > embedded_before_resume
        row = await trio.manifest.get("custom", "src/widget.py")
        assert row is not None and row.state == STATE_INDEXED
        assert summary.files_indexed >= 1

    async def test_dirty_file_is_resumed(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, trio=trio)
        await engine.reconcile()

        await trio.manifest.set_state("custom", "README.md", STATE_DIRTY)
        await engine.reconcile()
        row = await trio.manifest.get("custom", "README.md")
        assert row is not None and row.state == STATE_INDEXED


# --------------------------------------------------------------------------- #
# Static-tier defer (D5)
# --------------------------------------------------------------------------- #
class TestStaticDefer:
    """Reconcile defers static tiers to the indexer's version-stamp logic."""

    async def test_matching_stamp_skips_with_zero_walk_and_acquire(self, tmp_path: Path) -> None:
        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        config = _config(slug=slug, static_source=static_src, static_version="15.0.1")
        trio = _trio()
        snapshot_root = tmp_path / "snap"

        pre = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=snapshot_root,
        )
        await pre.set_tier_version_stamp("community", "15.0.1")

        exploding = ExplodingProvider("community")
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=snapshot_root,
            providers=[exploding],
        )
        engine = _make_engine(config=config, indexer=indexer, trio=trio)

        summary = await engine.reconcile()

        assert "community" in summary.tiers_skipped
        assert "community" not in summary.tiers_rebuilt
        assert exploding.acquired is False
        assert embedder.total_embedded == 0

    async def test_changed_stamp_rebuilds_static_tier(self, tmp_path: Path) -> None:
        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        trio = _trio()
        snapshot_root = tmp_path / "snap"

        config_v1 = _config(slug=slug, static_source=static_src, static_version="15.0.1")
        engine_v1 = _make_engine(
            config=config_v1,
            indexer=_make_indexer(
                config=config_v1, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=snapshot_root,
            ),
            trio=trio,
        )
        await engine_v1.reconcile()

        config_v2 = _config(slug=slug, static_source=static_src, static_version="15.0.2")
        indexer_v2 = _make_indexer(
            config=config_v2, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=snapshot_root,
        )
        engine_v2 = _make_engine(config=config_v2, indexer=indexer_v2, trio=trio)
        summary = await engine_v2.reconcile()
        assert "community" in summary.tiers_rebuilt
        assert await indexer_v2.tier_version_stamp("community") == "15.0.2"


# --------------------------------------------------------------------------- #
# Whole-project summary across mixed tiers
# --------------------------------------------------------------------------- #
class TestReconcileSummary:
    """``reconcile()`` rolls up every root into one summary."""

    async def test_summary_spans_live_and_static_roots(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        config = _config(slug=slug, live_path=live, static_source=static_src)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, trio=trio)

        summary = await engine.reconcile()

        assert summary.files_indexed >= 4
        assert "custom" in summary.tiers_rebuilt
        assert "community" in summary.tiers_rebuilt
        assert summary.files_purged == 0
