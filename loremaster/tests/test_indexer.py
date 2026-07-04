"""Contract tests for ``loremaster.index.indexer`` — the batch indexer centerpiece.

PORTED for P5-C3b: the :class:`~loremaster.index.indexer.Indexer` is rewired off
the sync SQLite-manifest + upsert-then-purge Qdrant store onto the **async**
Surreal ports with the C2 composed atomic per-file transaction. These tests keep
the SAME behavioural pins as the pre-port suite — only the fixtures change: the
real Qdrant + SQLite ``Manifest`` are replaced by the fast in-memory async fakes
(:mod:`_surreal_fakes`) that mirror :class:`~loremaster.store.surreal.
SurrealStore` / :class:`~loremaster.index.surreal_manifest.SurrealManifest` /
:class:`~loremaster.graph_surreal.SurrealCodeGraph`. Store-side side-effect
assertions (``store.search(...)``) are re-expressed over the fake's recorded
state (``identities_for`` / ``stored_file_paths`` / ``count``), and every
manifest read is now ``await``ed.

The contract under test (unchanged from the pre-port pins):

* **Per-file pipeline** ``index_file(tier, path, source)``: chunk via
  ``registry.dispatch_file``; embed; ``chunk_to_record(tier=…)``; then — the
  P5-C3b change — build the chunk + ``file_text`` + manifest (+ graph for ``.py``)
  fragments and apply them as ONE atomic transaction via ``store.apply``.
* **Fast-path.** An unchanged file (content hash matches an ``indexed`` row) is
  skipped with ZERO embeds (an embedder that records every call proves it).
* **Selective per-tier rebuild** uses ``delete_by_tier`` so a sibling tier is
  untouched.
* **Resilience.** An embed failure / non-finite vector marks the file ``failed``
  in a SMALL separate manifest-only write, stores NO chunks/file_text/graph, and
  lets the other files continue.
* **NEW decisions pinned here** (P5-C3b): an oversized ``file_text`` body indexes
  WITHOUT the file_text fragment (chunks/manifest/graph still land, state stays
  ``indexed``); a file whose composed transaction would overflow the store's hard
  statement cap is isolated ``failed`` (one bad file never kills the sweep).

Two pre-port classes are DROPPED as unportable and reported to the team lead:
``TestStoreFailureIsolation`` (a Qdrant-transport 500/429 + store-retry-budget
contract with NO analogue on the retry-less self-healing Surreal store — its
spiritual replacement is ``TestCapOverflowFailedState`` below) and
``TestRealTeiSmoke`` (a real-Qdrant + real-TEI smoke). ``TestCli`` (pure argparse)
is kept unchanged.
"""

from __future__ import annotations

import logging
import math
import uuid
from pathlib import Path
from typing import Any

import pytest
from _surreal_fakes import (
    PRODUCER_CHUNK,
    PRODUCER_FILE_TEXT,
    PRODUCER_MANIFEST,
    FakeSurrealTrio,
    fake_surreal_trio,
)
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer, graph_roots
from loremaster.index.surreal_manifest import STATE_FAILED, STATE_INDEXED
from loremaster.server import LoreServer
from loremaster.source.local_directory import LocalDirectorySourceProvider
from loresigil.base import Embedder
from loresigil.testing import FakeEmbedder

# Real production embedding dimensionality (the scale the store's vector-width
# guard and HNSW index will see in production — clause 1).
_DIM = 2048

_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"


# --------------------------------------------------------------------------- #
# Recording / instrumented embedder fakes (embedder side — mocks sanctioned)
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


class NonFiniteEmbedder(FakeEmbedder):
    """A fake that returns a NaN-poisoned vector for a named text."""

    def __init__(self, *, nan_texts: set[str], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._nan_texts = nan_texts

    @property
    def supports_contextualized(self) -> bool:
        return False

    async def embed_documents(self, texts: list[str]) -> Any:
        result = await super().embed_documents(texts)
        poisoned: list[list[float] | None] = []
        for text, vector in zip(texts, result.vectors, strict=True):
            if text in self._nan_texts and vector is not None:
                bad = list(vector)
                bad[0] = math.nan
                poisoned.append(bad)
            else:
                poisoned.append(vector)
        result.vectors = poisoned
        return result


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
        "exclude_globs": ["**/*.min.js"],
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
# Fake-trio wiring (replaces the real Qdrant store_factory + SQLite Manifest)
# --------------------------------------------------------------------------- #
def _trio(
    *,
    dim: int = _DIM,
    config: LoreConfig | None = None,
    snapshot_root: Path | None = None,
    with_graph: bool = False,
    file_text_max_bytes: int | None = None,
    txn_statement_hard_cap: int | None = None,
) -> FakeSurrealTrio:
    """Build the store + manifest + graph fakes over one shared database.

    When ``with_graph`` is set the graph fake is wired with the config's project
    roots (via the production :func:`graph_roots`), so its astroid derivation
    resolves references exactly as the live graph does.
    """
    kwargs: dict[str, Any] = {"dim": dim}
    if with_graph and config is not None and snapshot_root is not None:
        tier_roots, project_roots = graph_roots(config, snapshot_root)
        kwargs["tier_roots"] = tier_roots
        kwargs["project_roots"] = project_roots
    if file_text_max_bytes is not None:
        kwargs["file_text_max_bytes"] = file_text_max_bytes
    if txn_statement_hard_cap is not None:
        kwargs["txn_statement_hard_cap"] = txn_statement_hard_cap
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
    """Wire an :class:`Indexer` onto the fake Surreal ports (mirrors the CLI wiring)."""
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


def _probe_texts(config: LoreConfig, tier: str, path: str, source: str) -> list[str]:
    """The chunk texts a file produces (a throwaway indexer; pure — no I/O)."""
    server = LoreServer(config)
    probe = Indexer(
        store=fake_surreal_trio(dim=_DIM).store,
        embedder=FakeEmbedder(dim=_DIM),
        manifest=fake_surreal_trio(dim=_DIM).manifest,
        registry=server.registry,
        source_providers=[],
        config=config,
        snapshot_root=Path("/tmp/probe-unused"),
    )
    return probe.chunk_texts(tier, path, source)


# --------------------------------------------------------------------------- #
# index_file — the per-file pipeline
# --------------------------------------------------------------------------- #
class TestIndexFile:
    """``index_file`` chunks → embeds → records → applies ONE composed transaction."""

    async def test_indexes_a_real_python_file_end_to_end(self, tmp_path: Path) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM),
            snapshot_root=tmp_path / "snap",
        )

        source = (root / "src" / "widget.py").read_text(encoding="utf-8")
        outcome = await indexer.index_file("custom", "src/widget.py", source)

        # The real chunker splits this module into >1 chunk (imports/class/etc.).
        assert outcome.state == STATE_INDEXED
        assert outcome.n_chunks >= 3
        # The manifest row is committed in the indexed state with the chunk count.
        row = await trio.manifest.get("custom", "src/widget.py")
        assert row is not None
        assert row.state == STATE_INDEXED
        assert row.n_chunks == outcome.n_chunks
        assert len(row.chunk_ids) == outcome.n_chunks
        # The chunks actually landed on the store, tagged with the tier + file.
        assert await trio.store.count("custom") == outcome.n_chunks
        assert "src/widget.py" in trio.store.stored_file_paths()
        # One SINGLE composed apply spanned exactly the chunk + file_text + manifest
        # producers (no graph fragment — this indexer has no code_graph wired).
        assert len(trio.store.applied_transactions) == 1
        producers = {f.producer for f in trio.store.applied_transactions[0]}
        assert producers == {PRODUCER_CHUNK, PRODUCER_FILE_TEXT, PRODUCER_MANIFEST}
        # The verbatim body landed under the file_text surface too.
        body = trio.store.file_text_of("custom", "src/widget.py")
        assert body is not None and body["text"] == source

    async def test_reindex_unchanged_file_hits_fast_path_zero_embeds(self, tmp_path: Path) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = _trio()
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        source = (root / "src" / "widget.py").read_text(encoding="utf-8")

        await indexer.index_file("custom", "src/widget.py", source)
        embedded_after_first = embedder.total_embedded
        assert embedded_after_first >= 3

        # Re-index the SAME unchanged file: the content-hash fast-path must skip it.
        second = await indexer.index_file("custom", "src/widget.py", source)
        assert second.state == "skipped"
        assert embedder.total_embedded == embedded_after_first

    async def test_embedder_failure_marks_file_failed_and_stores_no_vectors(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = _trio()
        source = (root / "src" / "widget.py").read_text(encoding="utf-8")
        texts = _probe_texts(config, "custom", "src/widget.py", source)
        assert texts

        embedder = FakeEmbedder(dim=_DIM, fail_inputs=set(texts))
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        outcome = await indexer.index_file("custom", "src/widget.py", source)

        assert outcome.state == STATE_FAILED
        row = await trio.manifest.get("custom", "src/widget.py")
        assert row is not None and row.state == STATE_FAILED
        # No chunks for this file landed on the store; no composed apply happened.
        assert "src/widget.py" not in trio.store.stored_file_paths()
        assert trio.store.applied_transactions == []
        # The file_text was never written either (the failure is manifest-only).
        assert trio.store.file_text_of("custom", "src/widget.py") is None

    async def test_nonfinite_vector_is_never_stored(self, tmp_path: Path) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = _trio()
        source = (root / "src" / "widget.py").read_text(encoding="utf-8")
        texts = _probe_texts(config, "custom", "src/widget.py", source)

        # Poison one chunk's vector with NaN. The isfinite guard refuses the WHOLE
        # file (no partial store of finite siblings alongside a NaN sibling).
        embedder = NonFiniteEmbedder(dim=_DIM, nan_texts={texts[0]})
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        outcome = await indexer.index_file("custom", "src/widget.py", source)

        assert outcome.state == STATE_FAILED
        assert "src/widget.py" not in trio.store.stored_file_paths()

    async def test_update_upserts_new_before_purging_stale_no_gap(self, tmp_path: Path) -> None:
        """End-state of an update: NEW content present, stale purged (atomically)."""
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM),
            snapshot_root=tmp_path / "snap",
        )

        await indexer.index_file("custom", "src/m.py", "def alpha_marker():\n    return 1\n")
        assert "alpha_marker" in trio.store.identities_for("custom", "src/m.py")

        # Index v2: a DIFFERENT function. The new chunk present, the stale purged.
        await indexer.index_file("custom", "src/m.py", "def beta_marker():\n    return 2\n")
        identities_v2 = trio.store.identities_for("custom", "src/m.py")
        assert "beta_marker" in identities_v2
        assert "alpha_marker" not in identities_v2  # stale purged in the same apply

    async def test_failed_reindex_retains_prior_good_points(self, tmp_path: Path) -> None:
        """A re-index whose embeds all FAIL keeps the file's PRIOR good chunks intact
        and marks the file failed — it never purges the last-good content."""
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = _trio()

        good = FakeEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=good, snapshot_root=tmp_path / "snap",
        )
        v1 = "def gamma_marker():\n    return 1\n"
        first = await indexer.index_file("custom", "src/m.py", v1)
        assert first.state != STATE_FAILED
        assert "gamma_marker" in trio.store.identities_for("custom", "src/m.py")

        # v2: CHANGED content, embedder fails ALL its chunks.
        v2 = "def delta_marker():\n    return 2\n"
        v2_texts = _probe_texts(config, "custom", "src/m.py", v2)
        failing = FakeEmbedder(dim=_DIM, fail_inputs=set(v2_texts))
        indexer2 = _make_indexer(
            config=config, trio=trio, embedder=failing, snapshot_root=tmp_path / "snap",
        )
        outcome = await indexer2.index_file("custom", "src/m.py", v2)

        assert outcome.state == STATE_FAILED
        row = await trio.manifest.get("custom", "src/m.py")
        assert row is not None and row.state == STATE_FAILED
        ids = trio.store.identities_for("custom", "src/m.py")
        assert "gamma_marker" in ids, "last-good chunks must survive a failed re-index"
        assert "delta_marker" not in ids, "the failed new content must never be stored"

    async def test_file_edited_to_zero_chunks_purges_prior_points(self, tmp_path: Path) -> None:
        """A file whose new content yields NO chunks must not orphan its prior points."""
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM),
            snapshot_root=tmp_path / "snap",
        )

        await indexer.index_file("custom", "src/m.py", "def keep_me():\n    return 1\n")
        assert "src/m.py" in trio.store.stored_file_paths()

        # Edit to content the python_ast chunker yields zero chunks for.
        await indexer.index_file("custom", "src/m.py", "# no symbols here\n")
        assert "src/m.py" not in trio.store.stored_file_paths()
        # The manifest row reflects zero chunks, still indexed.
        row = await trio.manifest.get("custom", "src/m.py")
        assert row is not None and row.state == STATE_INDEXED and row.n_chunks == 0

    async def test_unknown_extension_yields_zero_chunks_skipped(self, tmp_path: Path) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = _trio()
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        outcome = await indexer.index_file("custom", "data.bin", "binary-ish junk")
        assert outcome.n_chunks == 0
        assert embedder.total_embedded == 0


# --------------------------------------------------------------------------- #
# NEW P5-C3b decisions: oversize file_text skip + cap-overflow failed-state
# --------------------------------------------------------------------------- #
class TestOversizeFileTextSkip:
    """A file whose body exceeds the store's ``file_text`` byte cap indexes WITHOUT
    the file_text fragment — chunks / manifest / graph still land, state stays
    ``indexed``, a warning logs. The cap is READ from the store (clause-5 single
    source of truth), so a small file crossing a small cap exercises the decision
    cheaply."""

    async def test_oversize_body_indexes_without_file_text_but_keeps_chunks_and_manifest(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        # A tiny file_text cap so a normal small module crosses it (the store is
        # the single source of truth the indexer's pre-check reads).
        trio = _trio(file_text_max_bytes=32)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM),
            snapshot_root=tmp_path / "snap",
        )
        source = _PY_MODULE  # well over 32 bytes
        assert len(source.encode("utf-8")) > trio.store.file_text_max_bytes

        with caplog.at_level(logging.WARNING, logger="loremaster.index.indexer"):
            outcome = await indexer.index_file("custom", "src/widget.py", source)

        # The file indexed (NOT failed) with its chunks + manifest row …
        assert outcome.state == STATE_INDEXED
        assert outcome.n_chunks >= 3
        row = await trio.manifest.get("custom", "src/widget.py")
        assert row is not None and row.state == STATE_INDEXED and row.n_chunks == outcome.n_chunks
        assert "src/widget.py" in trio.store.stored_file_paths()
        # … but the oversized file_text body was SKIPPED (not written, not crashed).
        assert trio.store.file_text_of("custom", "src/widget.py") is None
        # The composed apply carried NO file_text fragment.
        producers = {f.producer for f in trio.store.applied_transactions[-1]}
        assert PRODUCER_FILE_TEXT not in producers
        assert PRODUCER_CHUNK in producers and PRODUCER_MANIFEST in producers
        # A warning names the skip (no source text leaked).
        assert any(
            "file_text" in record.getMessage() or "file_text" in str(getattr(record, "reason", ""))
            for record in caplog.records
            if record.levelno == logging.WARNING
        )


class TestCapOverflowFailedState:
    """A file whose composed transaction would overflow the store's hard statement
    cap is isolated ``failed`` (the typed store error is caught and routed to
    ``_mark_file_failed``) — one pathologically chunk-heavy file never kills the
    sweep, and a normal sibling still indexes."""

    async def test_overflowing_file_is_isolated_failed_and_sibling_indexes(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        # A statement cap tuned to SEPARATE a multi-chunk file from a minimal
        # one: the minimal apply is 1 chunk-DELETE + 1 file_text + 2 manifest =
        # 4 statements, while the 4-chunk widget module composes 5 chunk + 1
        # file_text + 2 manifest = 8 — so cap 6 fails the widget and passes the
        # tiny sibling. The cap is the store's own guard, read from the store
        # (clause 5), never a value the indexer hardcodes.
        trio = _trio(txn_statement_hard_cap=6)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM),
            snapshot_root=tmp_path / "snap",
        )

        # The multi-chunk widget module overflows the tiny cap → isolated failed.
        widget_source = (root / "src" / "widget.py").read_text(encoding="utf-8")
        with caplog.at_level(logging.WARNING, logger="loremaster.index.indexer"):
            heavy = await indexer.index_file("custom", "src/widget.py", widget_source)

        assert heavy.state == STATE_FAILED
        row = await trio.manifest.get("custom", "src/widget.py")
        assert row is not None and row.state == STATE_FAILED
        # NOTHING partially persisted (the whole composed txn was refused at build).
        assert "src/widget.py" not in trio.store.stored_file_paths()
        assert trio.store.file_text_of("custom", "src/widget.py") is None
        # The cap-overflow is loud (a warning was logged, no crash escaped).
        assert any(record.levelno == logging.WARNING for record in caplog.records)

        # A single-chunk sibling stays UNDER the cap and indexes normally — one bad
        # file did not kill the sweep.
        tiny = await indexer.index_file("custom", "src/tiny.py", "x = 1\n")
        assert tiny.state == STATE_INDEXED


# --------------------------------------------------------------------------- #
# Per-file pipeline logging
# --------------------------------------------------------------------------- #
class TestIndexerLogging:
    """``index_file`` emits structured per-file events (caplog-asserted)."""

    async def test_successful_index_logs_file_done_with_fields(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM),
            snapshot_root=tmp_path / "snap",
        )
        source = (root / "src" / "widget.py").read_text(encoding="utf-8")
        with caplog.at_level(logging.INFO, logger="loremaster.index.indexer"):
            outcome = await indexer.index_file("custom", "src/widget.py", source)

        events = [r for r in caplog.records if r.message == "index.file.done"]
        assert len(events) == 1
        record = events[0]
        assert record.levelno == logging.INFO
        assert record.tier == "custom"  # type: ignore[attr-defined]
        assert record.file_path == "src/widget.py"  # type: ignore[attr-defined]
        assert record.n_chunks == outcome.n_chunks  # type: ignore[attr-defined]
        assert record.state == STATE_INDEXED  # type: ignore[attr-defined]
        assert isinstance(record.duration_ms, (int, float))  # type: ignore[attr-defined]
        assert record.duration_ms >= 0  # type: ignore[attr-defined]

    async def test_failed_embed_logs_file_failed_with_reason(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = _trio()
        source = (root / "src" / "widget.py").read_text(encoding="utf-8")
        texts = _probe_texts(config, "custom", "src/widget.py", source)
        embedder = FakeEmbedder(dim=_DIM, fail_inputs=set(texts))
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        with caplog.at_level(logging.WARNING, logger="loremaster.index.indexer"):
            await indexer.index_file("custom", "src/widget.py", source)

        events = [r for r in caplog.records if r.message == "index.file.failed"]
        assert len(events) == 1
        record = events[0]
        assert record.levelno == logging.WARNING
        assert record.tier == "custom"  # type: ignore[attr-defined]
        assert record.file_path == "src/widget.py"  # type: ignore[attr-defined]
        assert isinstance(record.reason, str) and record.reason  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
# Per-tier freshness (D5)
# --------------------------------------------------------------------------- #
class TestStaticTierFreshness:
    """Static-tier version-stamp: CHANGED → rebuild + re-stamp; MATCH → skip-no-walk."""

    async def test_absent_stamp_acquires_and_builds_then_stamps(self, tmp_path: Path) -> None:
        from loremaster.source.snapshot import SnapshotLayout

        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        config = _config(slug=slug, static_source=static_src, static_version="15.0.1")
        trio = _trio()
        snapshot_root = tmp_path / "snap"
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=snapshot_root,
        )

        root = next(r for r in config.roots if r.tier == "community")
        summary = await indexer.index_tier(root)

        assert "community" in summary.tiers_rebuilt
        assert summary.files_indexed >= 1
        materialized = SnapshotLayout(snapshot_root).materialization_dir("community")
        assert (materialized / "lib" / "core.py").exists()
        assert await indexer.tier_version_stamp("community") == "15.0.1"
        # Chunks landed under the community tier on the store.
        assert await trio.store.count("community") >= 1

    async def test_matching_stamp_skips_with_zero_walk(self, tmp_path: Path) -> None:
        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        config = _config(slug=slug, static_source=static_src, static_version="15.0.1")
        trio = _trio()
        snapshot_root = tmp_path / "snap"

        # Pre-stamp the manifest as if this exact version was already built.
        indexer0 = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=snapshot_root,
        )
        await indexer0.set_tier_version_stamp("community", "15.0.1")

        exploding = ExplodingProvider("community")
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=snapshot_root,
            providers=[exploding],
        )
        root = next(r for r in config.roots if r.tier == "community")
        summary = await indexer.index_tier(root)

        assert "community" in summary.tiers_skipped
        assert "community" not in summary.tiers_rebuilt
        assert exploding.acquired is False
        assert embedder.total_embedded == 0

    async def test_changed_stamp_rebuilds_and_restamps(self, tmp_path: Path) -> None:
        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        trio = _trio()
        snapshot_root = tmp_path / "snap"

        config_v1 = _config(slug=slug, static_source=static_src, static_version="15.0.1")
        indexer_v1 = _make_indexer(
            config=config_v1, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=snapshot_root,
        )
        await indexer_v1.index_tier(next(r for r in config_v1.roots if r.tier == "community"))
        assert await indexer_v1.tier_version_stamp("community") == "15.0.1"

        config_v2 = _config(slug=slug, static_source=static_src, static_version="15.0.2")
        indexer_v2 = _make_indexer(
            config=config_v2, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=snapshot_root,
        )
        summary = await indexer_v2.index_tier(
            next(r for r in config_v2.roots if r.tier == "community")
        )
        assert "community" in summary.tiers_rebuilt
        assert await indexer_v2.tier_version_stamp("community") == "15.0.2"


# --------------------------------------------------------------------------- #
# Selective per-tier rebuild — sibling tier untouched
# --------------------------------------------------------------------------- #
class TestSelectiveRebuild:
    """Rebuilding one tier purges only it; the sibling tier's points survive."""

    async def test_rebuild_one_tier_leaves_sibling_intact(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        trio = _trio()
        snapshot_root = tmp_path / "snap"

        config_v1 = _config(slug=slug, live_path=live, static_source=static_src, static_version="1")
        indexer_v1 = _make_indexer(
            config=config_v1, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=snapshot_root,
        )
        await indexer_v1.index_all()

        live_ids_before = trio.store.point_ids_for("custom")
        assert live_ids_before

        config_v2 = _config(slug=slug, live_path=live, static_source=static_src, static_version="2")
        indexer_v2 = _make_indexer(
            config=config_v2, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=snapshot_root,
        )
        summary = await indexer_v2.index_all()
        assert "community" in summary.tiers_rebuilt

        # The custom-tier points are exactly as before (delete_by_tier touched only
        # community; the live tier re-walked unchanged content → same point ids).
        assert trio.store.point_ids_for("custom") == live_ids_before
        assert trio.store.point_ids_for("community")  # community still has points


# --------------------------------------------------------------------------- #
# index_all / index_status — the summary surface + include/exclude
# --------------------------------------------------------------------------- #
def _single_tree_config(*, slug: str, project_root: Path) -> LoreConfig:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": str(project_root)},
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
        "include": ["**/*.py", "**/*.md"],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": ["**/*.min.js"],
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


class TestSingleTreeRootsSynthesis:
    """A config with NO ``roots:`` + top-level ``include`` globs still indexes."""

    async def test_index_all_with_empty_roots_indexes_top_level_include(self, tmp_path: Path) -> None:
        slug = _slug()
        project_root = tmp_path / "tree"
        _build_live_corpus(project_root)
        config = _single_tree_config(slug=slug, project_root=project_root)
        assert config.roots == []
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )

        summary = await indexer.index_all()

        assert summary.files_indexed > 0
        indexed_paths = {o.file_path for o in summary.outcomes if o.state == STATE_INDEXED}
        assert "src/widget.py" in indexed_paths
        assert "src/routing.py" in indexed_paths
        assert "README.md" in indexed_paths
        assert "src/bundle.min.js" not in indexed_paths
        assert not any(p.startswith(".git/") for p in indexed_paths)
        assert not any(p.startswith(".venv/") for p in indexed_paths)


class TestIndexAllAndStatus:
    """``index_all`` walks live tiers + freshness-gates static; ``index_status`` reports."""

    async def test_include_exclude_pruning(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        await indexer.index_all()

        indexed_paths = {row.file_path for row in await trio.manifest.files_for_tier("custom")}
        assert "src/widget.py" in indexed_paths
        assert "src/routing.py" in indexed_paths
        assert "README.md" in indexed_paths
        assert "src/bundle.min.js" not in indexed_paths
        assert not any(p.startswith(".git/") for p in indexed_paths)
        assert not any(p.startswith(".venv/") for p in indexed_paths)

    async def test_index_status_summarizes_indexed_and_failed(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()

        routing_src = (live / "src" / "routing.py").read_text(encoding="utf-8")
        fail_texts = set(_probe_texts(config, "custom", "src/routing.py", routing_src))
        embedder = FakeEmbedder(dim=_DIM, fail_inputs=fail_texts)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        await indexer.index_all()

        status = await indexer.index_status()
        assert status.files_failed >= 1
        assert status.files_indexed >= 1
        routing_row = await trio.manifest.get("custom", "src/routing.py")
        assert routing_row is not None and routing_row.state == STATE_FAILED
        widget_row = await trio.manifest.get("custom", "src/widget.py")
        assert widget_row is not None and widget_row.state == STATE_INDEXED

    async def test_index_status_reads_manifest_without_embedding(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        trio = _trio()
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )
        await indexer.index_all()
        embedded_after_build = embedder.total_embedded

        status = await indexer.index_status()
        assert status.files_indexed >= 1
        assert embedder.total_embedded == embedded_after_build


# --------------------------------------------------------------------------- #
# CLI surface — argparse, stdlib only (unchanged; orthogonal to the Surreal port)
# --------------------------------------------------------------------------- #
class TestCli:
    """The thin ``index`` CLI parses args (stdlib argparse) and exposes a parser."""

    def test_cli_parser_accepts_config_and_tier(self) -> None:
        from loremaster.index.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--config", "/tmp/lore.yaml", "--tier", "community"])
        assert args.config == "/tmp/lore.yaml"
        assert args.tier == "community"

    def test_cli_parser_defaults_tier_to_none(self) -> None:
        from loremaster.index.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--config", "/tmp/lore.yaml"])
        assert args.tier is None
