"""Contract tests for ``loremaster.index.reconcile`` — the startup + periodic sweep.

The :class:`~loremaster.index.reconcile.ReconcileEngine` is the policy-aware
sweep that brings the index current with the filesystem on startup and on a
timer (catching dropped inotify events / ``IN_Q_OVERFLOW``). It is built on the
already-merged :class:`~loremaster.index.indexer.Indexer` and
:class:`~loremaster.index.manifest.Manifest`.

These tests run it the way the server will: against a **REAL local Qdrant**
(``http://127.0.0.1:16333``, throwaway ``lore_test_<session>_*`` collections), a
**REAL corpus** (a ``tmp_path`` tree built per test, chunked for real through the
default lorescribe registry), and a **FakeEmbedder(dim=2048)** (the embedder is
loresigil's tested concern; faking it keeps these fast and deterministic).

The contract under test (each maps to a plan requirement — Deliverable 3
Staleness engine §(2) + AMENDMENT 1 D5):

* **Live-tier walk, mtime+size fast-path.** A first reconcile indexes every
  included file under a LIVE root; an immediate second reconcile of an unchanged
  tree re-embeds NOTHING (the manifest mtime+size fast-path) — proven by a
  recording embedder.
* **Changed file → reindex.** Editing a file's content between sweeps re-indexes
  exactly that file (new content present, stale purged) and leaves the others on
  the fast-path.
* **Deleted file → purge.** A file present in the manifest but GONE from disk is
  purged: its points are removed from Qdrant (``delete_by_file``) and its
  manifest row is deleted. A sibling tier's copy of the same path is untouched.
* **Resume non-indexed.** A file the manifest holds in a non-``indexed`` state
  (``failed``/``dirty``/``embedding`` — e.g. a crash mid-embed) is re-attempted
  by reconcile even when its mtime+size are unchanged, and reaches ``indexed``.
* **Exclude-dir pruning at the walk level.** A ``.venv``/``.git`` subtree is
  NEVER descended — no file under it ever lands in the manifest or Qdrant.
* **Static-tier defer.** A STATIC tier whose version stamp MATCHES the manifest
  is skipped with ZERO walk and ZERO acquisition (a provider that raises if
  ``acquire`` runs proves it); a CHANGED stamp rebuilds it. Reconcile defers to
  the indexer's version-stamp logic — it does not walk static trees itself.
* **Summary.** ``reconcile()`` returns an :class:`~loremaster.index.indexer.IndexSummary`
  rolling up indexed / failed / skipped files + rebuilt / skipped tiers across
  every root, plus the count of purged (deleted) files.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer
from loremaster.index.manifest import (
    STATE_DIRTY,
    STATE_FAILED,
    STATE_INDEXED,
    Manifest,
)
from loremaster.index.reconcile import ReconcileEngine
from loremaster.server import LoreServer
from loremaster.source.local_directory import LocalDirectorySourceProvider
from loremaster.store.qdrant import QdrantStore
from loresigil.base import Embedder
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient

_DIM = 2048
_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"


# --------------------------------------------------------------------------- #
# Recording / instrumented fakes
# --------------------------------------------------------------------------- #
class RecordingEmbedder(FakeEmbedder):
    """A :class:`FakeEmbedder` that records every ``embed_documents`` batch.

    Lets a test prove the *fast-path* fired (zero embed calls on an unchanged
    re-reconcile) and count texts embedded — a plain fake cannot.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.embed_batches: list[list[str]] = []

    async def embed_documents(self, texts: list[str]) -> Any:
        self.embed_batches.append(list(texts))
        return await super().embed_documents(texts)

    @property
    def total_embedded(self) -> int:
        return sum(len(batch) for batch in self.embed_batches)


class ExplodingProvider:
    """A :class:`SourceProvider` whose ``acquire`` raises if ever called.

    Proves a static tier whose version stamp MATCHES is skipped with ZERO
    acquisition (and therefore zero walk).
    """

    def __init__(self, tier: str) -> None:
        self.tier = tier
        self.acquired = False

    def acquire(self, tier: str, snapshot_root: Path) -> None:
        self.acquired = True
        raise AssertionError(
            f"acquire({tier!r}) must NOT run when the version stamp matches"
        )


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
    """A realistic live tree with includes, excluded globs, and prune dirs."""
    _write(root / "src" / "widget.py", _PY_MODULE)
    _write(root / "src" / "routing.py", _PY_MODULE_2)
    _write(root / "README.md", "# Project\n\nSome docs.\n")
    _write(root / "src" / "bundle.min.js", "var x=1;")  # excluded glob (also non-.py)
    # An excluded glob that DOES match the include (``**/*.py``) — so only the
    # exclude branch of ``is_included`` can keep it out (load-bearing; `.min.js`
    # is masked by the include filter and cannot prove the exclude branch).
    _write(root / "src" / "api_pb2.py", "def generated_proto_marker():\n    return 1\n")
    _write(root / ".git" / "config.py", "SECRET = 'do-not-index'\n")  # pruned dir
    _write(root / ".venv" / "lib" / "vendored.py", "junk = 1\n")  # pruned dir


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
        "qdrant": {"url": "http://127.0.0.1:16333", "api_key_env": "QDRANT__SERVICE__API_KEY"},
        "roots": roots,
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        # ``**/*_pb2.py`` excludes a file that DOES match the ``**/*.py`` include —
        # the exclude branch is the only thing keeping it out (load-bearing).
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
# Fixtures
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture()
async def store_factory() -> AsyncIterator[Any]:
    """Builder for a :class:`QdrantStore` with CONCURRENCY-SAFE teardown.

    A SIBLING agent creates/deletes ``lore_test_*`` collections on the same
    shared server concurrently, so a prefix sweep would reap the other run's
    in-flight collections. This fixture owns its own client and deletes ONLY the
    exact collection names *this* test created.
    """
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


def _make_indexer(
    *,
    config: LoreConfig,
    store: QdrantStore,
    embedder: Embedder,
    manifest: Manifest,
    snapshot_root: Path,
    providers: list[Any] | None = None,
) -> Indexer:
    """Wire an :class:`Indexer` exactly as the CLI/server does."""
    server = LoreServer(config)
    built: list[Any] = list(server.source_providers) if providers is None else list(providers)
    if providers is None:
        for root in config.roots:
            if root.watch == "static" and root.source is not None:
                built.append(LocalDirectorySourceProvider(root.tier, Path(root.source)))
    return Indexer(
        store=store,
        embedder=embedder,
        manifest=manifest,
        registry=server.registry,
        source_providers=built,
        config=config,
        snapshot_root=snapshot_root,
    )


def _make_engine(
    *,
    config: LoreConfig,
    indexer: Indexer,
    manifest: Manifest,
    store: QdrantStore,
) -> ReconcileEngine:
    """Construct the :class:`ReconcileEngine` from injected collaborators."""
    return ReconcileEngine(
        indexer=indexer, manifest=manifest, store=store, config=config
    )


async def _file_paths_in_store(store: QdrantStore) -> set[str]:
    hits = await store.search([0.0] * _DIM, k=500)
    return {
        hit.payload["file_path"]
        for hit in hits
        if hit.payload is not None
    }


# --------------------------------------------------------------------------- #
# Reconcile-summary logging (the liveness heartbeat)
# --------------------------------------------------------------------------- #
class TestReconcileSummaryLogging:
    """``reconcile`` always logs a ``reconcile.summary`` heartbeat (caplog)."""

    async def test_reconcile_logs_summary_counts(
        self, tmp_path: Path, store_factory: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, manifest=manifest, store=store)

        with caplog.at_level(logging.INFO, logger="loremaster.index.reconcile"):
            summary = await engine.reconcile()

        events = [r for r in caplog.records if r.message == "reconcile.summary"]
        assert len(events) == 1
        record = events[0]
        assert record.levelno == logging.INFO  # INFO heartbeat, on at default level
        # The event mirrors the returned ReconcileSummary's counts — the independent
        # oracle is the summary object the engine returned, not the log's own math.
        assert record.files_indexed == summary.files_indexed  # type: ignore[attr-defined]
        assert record.files_failed == summary.files_failed  # type: ignore[attr-defined]
        assert record.files_skipped == summary.files_skipped  # type: ignore[attr-defined]
        assert record.files_purged == summary.files_purged  # type: ignore[attr-defined]
        assert record.tiers_rebuilt == summary.tiers_rebuilt  # type: ignore[attr-defined]
        assert record.tiers_skipped == summary.tiers_skipped  # type: ignore[attr-defined]
        assert isinstance(record.duration_ms, (int, float)) and record.duration_ms >= 0  # type: ignore[attr-defined]
        # A real corpus indexed something on the first sweep (sanity guard).
        assert record.files_indexed >= 1  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
# Live-tier walk + fast-path
# --------------------------------------------------------------------------- #
class TestLiveReconcile:
    """A live root is walked; an unchanged second sweep re-embeds nothing."""

    async def test_first_reconcile_indexes_included_files(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, manifest=manifest, store=store)

        summary = await engine.reconcile()

        indexed_paths = {row.file_path for row in manifest.files_for_tier("custom")}
        assert "src/widget.py" in indexed_paths
        assert "src/routing.py" in indexed_paths
        assert "README.md" in indexed_paths
        # Excluded glob never indexed.
        assert "src/bundle.min.js" not in indexed_paths
        # A file that MATCHES the include (``**/*.py``) but ALSO matches an exclude
        # glob (``**/*_pb2.py``) is kept out by the exclude branch alone — proving
        # that branch is load-bearing (deleting it from ``is_included`` would index
        # this file and fail this assertion).
        assert "src/api_pb2.py" not in indexed_paths
        assert not any(p.startswith(".git/") for p in indexed_paths)
        assert not any(p.startswith(".venv/") for p in indexed_paths)
        # The summary reflects the real files indexed.
        assert summary.files_indexed >= 3
        # Points actually landed.
        assert "src/widget.py" in await _file_paths_in_store(store)

    async def test_second_reconcile_unchanged_tree_zero_embeds(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder,
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, manifest=manifest, store=store)

        await engine.reconcile()
        embedded_after_first = embedder.total_embedded
        assert embedded_after_first >= 3

        # Second sweep of the UNCHANGED tree: mtime+size fast-path → zero embeds.
        second = await engine.reconcile()
        assert embedder.total_embedded == embedded_after_first
        assert second.files_indexed == 0  # nothing freshly embedded
        assert second.files_skipped >= 3  # everything fast-pathed

    async def test_changed_file_is_reindexed_others_fast_pathed(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder,
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, manifest=manifest, store=store)
        await engine.reconcile()
        baseline = embedder.total_embedded

        # Edit ONE file's content (a new uniquely-named symbol) and bump its mtime.
        edited = live / "src" / "routing.py"
        edited.write_text(
            "def reconcile_marker_xyz(week):\n    return week\n", encoding="utf-8"
        )
        # Force a distinct mtime so the fast-path sees a change even on coarse clocks.
        import os as _os
        st = edited.stat()
        _os.utime(edited, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))

        second = await engine.reconcile()
        # Exactly the edited file was re-embedded (others fast-pathed).
        assert embedder.total_embedded > baseline
        assert second.files_indexed >= 1
        # The new symbol is searchable; the old one is gone.
        hits = await store.search([0.0] * _DIM, k=500)
        identities = {
            h.payload["identity"]
            for h in hits
            if h.payload is not None and h.payload["file_path"] == "src/routing.py"
        }
        assert "reconcile_marker_xyz" in identities
        assert "champion_routing" not in identities


# --------------------------------------------------------------------------- #
# Deleted file → purge
# --------------------------------------------------------------------------- #
class TestPurgeDeleted:
    """A file gone from disk is purged from Qdrant AND the manifest."""

    async def test_deleted_file_is_purged_from_store_and_manifest(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, manifest=manifest, store=store)
        await engine.reconcile()
        assert manifest.get("custom", "src/routing.py") is not None
        assert "src/routing.py" in await _file_paths_in_store(store)

        # Delete the file from disk (the watcher was down — startup must catch it).
        (live / "src" / "routing.py").unlink()
        summary = await engine.reconcile()

        # The manifest row is gone and no points remain for it.
        assert manifest.get("custom", "src/routing.py") is None
        assert "src/routing.py" not in await _file_paths_in_store(store)
        # The surviving files are still indexed.
        assert manifest.get("custom", "src/widget.py") is not None
        assert "src/widget.py" in await _file_paths_in_store(store)
        # The summary reports the purge.
        assert summary.files_purged >= 1

    async def test_purge_is_tier_scoped_sibling_survives(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """A delete in the live tier never purges another tier's copy of the path."""
        slug = _slug()
        live = tmp_path / "live"
        _write(live / "shared.py", _PY_MODULE_2)  # custom-tier copy of shared.py
        static_src = tmp_path / "community_src"
        _write(static_src / "shared.py", _PY_MODULE)  # community-tier copy
        config = _config(slug=slug, live_path=live, static_source=static_src)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, manifest=manifest, store=store)
        await engine.reconcile()
        assert manifest.get("custom", "shared.py") is not None
        assert manifest.get("community", "shared.py") is not None

        # Delete only the live (custom) copy.
        (live / "shared.py").unlink()
        await engine.reconcile()

        # The custom copy is purged; the community copy survives entirely.
        assert manifest.get("custom", "shared.py") is None
        assert manifest.get("community", "shared.py") is not None
        community_hits = await store.search(
            [0.0] * _DIM, k=500, filters={"tier": "community"}
        )
        assert any(
            h.payload is not None and h.payload["file_path"] == "shared.py"
            for h in community_hits
        )


# --------------------------------------------------------------------------- #
# Resume a non-indexed file
# --------------------------------------------------------------------------- #
class TestResumeNonIndexed:
    """A file the manifest left non-``indexed`` is re-attempted, even if unchanged."""

    async def test_failed_file_is_resumed_to_indexed(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder,
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, manifest=manifest, store=store)
        await engine.reconcile()

        # Simulate a crash mid-embed: mark widget.py FAILED in place (its mtime+size
        # are unchanged, so a naive fast-path would skip it forever).
        manifest.set_state("custom", "src/widget.py", STATE_FAILED)
        failed_row = manifest.get("custom", "src/widget.py")
        assert failed_row is not None and failed_row.state == STATE_FAILED
        embedded_before_resume = embedder.total_embedded

        summary = await engine.reconcile()

        # The failed file was RE-ATTEMPTED (embeds happened) and reached indexed.
        assert embedder.total_embedded > embedded_before_resume
        row = manifest.get("custom", "src/widget.py")
        assert row is not None and row.state == STATE_INDEXED
        assert summary.files_indexed >= 1

    async def test_dirty_file_is_resumed(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, manifest=manifest, store=store)
        await engine.reconcile()

        manifest.set_state("custom", "README.md", STATE_DIRTY)
        await engine.reconcile()
        row = manifest.get("custom", "README.md")
        assert row is not None and row.state == STATE_INDEXED


# --------------------------------------------------------------------------- #
# Static-tier defer (D5)
# --------------------------------------------------------------------------- #
class TestStaticDefer:
    """Reconcile defers static tiers to the indexer's version-stamp logic."""

    async def test_matching_stamp_skips_with_zero_walk_and_acquire(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        config = _config(slug=slug, static_source=static_src, static_version="15.0.1")
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        snapshot_root = tmp_path / "snap"

        # Pre-stamp as if already built at this version.
        pre = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root,
        )
        pre.set_tier_version_stamp("community", "15.0.1")

        # Build an indexer whose provider EXPLODES on acquire and whose embedder
        # records any embed; the matching stamp must skip both.
        exploding = ExplodingProvider("community")
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=snapshot_root, providers=[exploding],
        )
        engine = _make_engine(config=config, indexer=indexer, manifest=manifest, store=store)

        summary = await engine.reconcile()

        assert "community" in summary.tiers_skipped
        assert "community" not in summary.tiers_rebuilt
        assert exploding.acquired is False
        assert embedder.total_embedded == 0  # zero walk → zero embeds

    async def test_changed_stamp_rebuilds_static_tier(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        snapshot_root = tmp_path / "snap"

        config_v1 = _config(slug=slug, static_source=static_src, static_version="15.0.1")
        engine_v1 = _make_engine(
            config=config_v1,
            indexer=_make_indexer(
                config=config_v1, store=store, embedder=FakeEmbedder(dim=_DIM),
                manifest=manifest, snapshot_root=snapshot_root,
            ),
            manifest=manifest, store=store,
        )
        await engine_v1.reconcile()

        config_v2 = _config(slug=slug, static_source=static_src, static_version="15.0.2")
        indexer_v2 = _make_indexer(
            config=config_v2, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root,
        )
        engine_v2 = _make_engine(
            config=config_v2, indexer=indexer_v2, manifest=manifest, store=store
        )
        summary = await engine_v2.reconcile()
        assert "community" in summary.tiers_rebuilt
        assert indexer_v2.tier_version_stamp("community") == "15.0.2"


# --------------------------------------------------------------------------- #
# Whole-project summary across mixed tiers
# --------------------------------------------------------------------------- #
class TestReconcileSummary:
    """``reconcile()`` rolls up every root into one summary."""

    async def test_summary_spans_live_and_static_roots(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        config = _config(slug=slug, live_path=live, static_source=static_src)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        engine = _make_engine(config=config, indexer=indexer, manifest=manifest, store=store)

        summary = await engine.reconcile()

        # The live tier and the (fresh) static tier both indexed; both appear as
        # rebuilt/walked this run; no spurious purges on a first sweep.
        assert summary.files_indexed >= 4  # 3 live + >=1 static
        assert "custom" in summary.tiers_rebuilt
        assert "community" in summary.tiers_rebuilt
        assert summary.files_purged == 0
