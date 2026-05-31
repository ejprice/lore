"""Contract tests for ``loremaster.index.indexer`` — the batch indexer centerpiece.

The :class:`~loremaster.index.indexer.Indexer` ties config → source → chunk →
embed → records → upsert → manifest together. These tests run it the way the
deploy CLI will: against a **REAL local Qdrant** (``http://127.0.0.1:16333``,
throwaway ``lore_test_<uuid>`` collections), a **REAL corpus** (a ``tmp_path``
tree built per test, chunked for real through the default lorescribe registry),
and a **FakeEmbedder(dim=2048)** for the bulk (the embedder is loresigil's
tested concern — faking it keeps these fast and deterministic).

Why real Qdrant, not ``:memory:``: ``upsert-before-purge`` and
``delete_by_tier`` are *server-side* behaviours — filter-based deletes and
payload indexes are no-ops in the in-memory backend. Proving "a concurrent
reader never sees a gap" and "rebuilding one tier leaves the sibling intact"
is only meaningful against the live engine.

The contract under test (each maps to a plan requirement):

* **Per-tier freshness (D5).** A STATIC tier compares ``config.version`` to the
  tier's stamp in the manifest ``meta``: CHANGED/absent → ``acquire`` via the
  provider then rebuild + re-stamp; MATCH → SKIP with ZERO filesystem walk
  (proven by a sentinel that would raise if the walk ran). A LIVE tier does a
  full walk + index every run.
* **Per-file pipeline** ``index_file(tier, path, source)``: chunk via
  ``registry.dispatch_file`` with a real ``ChunkContext`` (the embedder's token
  counter + ``max_input_tokens`` injected); embed; ``chunk_to_record(tier=…)``;
  **upsert NEW chunks BEFORE purging stale** ones for that (tier, file) — a
  mid-update scroll sees the new content, never a gap; transactional manifest
  update (state ``indexed``, sha512, mtime_ns, size, n_chunks, chunk_ids).
* **Fast-path.** An unchanged file (mtime+size match an ``indexed`` row) is
  skipped with ZERO embeds (proven by an embedder that records every call).
* **Selective per-tier rebuild** uses ``delete_by_tier`` so a sibling tier is
  untouched (real Qdrant).
* **Resilience.** An embedder failure for a file → that file is marked
  ``failed`` in the manifest, NO vectors are stored for it (never zero/NaN — an
  ``isfinite`` guard), and other files still index; the failure is surfaced via
  the ``index_status``-style summary the indexer returns.
* **Include/exclude.** Per-root globs select files; excluded dirs are pruned at
  walk time (``.git`` etc. never descended).

Optional ONE real-TEI end-to-end smoke (a tiny real corpus, ``http://
tei.example:8080``) runs only if ``/health`` is 200; it SKIPs
cleanly otherwise so it never makes the suite flaky.
"""

from __future__ import annotations

import logging
import math
import os
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx
import pytest
import pytest_asyncio
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer
from loremaster.index.manifest import (
    STATE_FAILED,
    STATE_INDEXED,
    Manifest,
)
from loremaster.server import LoreServer
from loremaster.source.local_directory import LocalDirectorySourceProvider
from loremaster.source.snapshot import SnapshotLayout
from loremaster.store.qdrant import QdrantStore
from loresigil.base import Embedder
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient
from qdrant_client.common.client_exceptions import ResourceExhaustedResponse
from qdrant_client.http.exceptions import UnexpectedResponse

# Real embedder dimensionality for the bulk fake (the production dim).
_DIM = 2048

# The optional real-TEI endpoint and its health probe.
_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"


# --------------------------------------------------------------------------- #
# Recording / instrumented fakes (extension/embedder side — mocks sanctioned)
# --------------------------------------------------------------------------- #
class RecordingEmbedder(FakeEmbedder):
    """A :class:`FakeEmbedder` that records every ``embed_documents`` batch.

    Lets a test assert the *fast-path* fired (zero embed calls on an unchanged
    re-index) and count how many texts were embedded — behaviour a plain fake
    cannot prove.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.embed_batches: list[list[str]] = []

    async def embed_documents(self, texts: list[str]) -> Any:
        self.embed_batches.append(list(texts))
        return await super().embed_documents(texts)

    @property
    def total_embedded(self) -> int:
        """Total number of texts embedded across all batches."""
        return sum(len(batch) for batch in self.embed_batches)


class NonFiniteEmbedder(FakeEmbedder):
    """A fake that returns a NaN-poisoned vector for a named text.

    Exercises the ``isfinite`` guard: a vector containing ``NaN``/``inf`` must
    never be stored (one NaN poisons cosine/argmax across every query), and the
    file must be marked ``failed`` exactly as a ``None`` (permanent-failure)
    return is.
    """

    def __init__(self, *, nan_texts: set[str], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._nan_texts = nan_texts

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
    """A :class:`SourceProvider` whose ``acquire`` raises if ever called.

    Proves a static tier whose version MATCHES the manifest stamp is skipped
    with ZERO acquisition (and therefore zero walk) — calling this provider is
    the failure signal.
    """

    def __init__(self, tier: str) -> None:
        self.tier = tier
        self.acquired = False

    def acquire(self, tier: str, snapshot_root: Path) -> None:
        self.acquired = True
        raise AssertionError(
            f"acquire({tier!r}) must NOT run when the version stamp matches"
        )


def _server_error_500() -> BaseException:
    """The original cold-index crash signature: a 500 ``UnexpectedResponse``."""
    return UnexpectedResponse(
        status_code=500,
        reason_phrase="Internal Server Error",
        content=b"Service internal error: task panicked",
        headers=httpx.Headers(),
    )


def _resource_exhausted_429() -> BaseException:
    """A 429+``Retry-After`` overload signal: ``ResourceExhaustedResponse``.

    qdrant-client 1.18.0 raises this (a ``QdrantException``, NOT an
    ``UnexpectedResponse``) for a 429 carrying a ``Retry-After`` header — the
    failure class that, before the fix, slipped past BOTH resilience layers.
    """
    return ResourceExhaustedResponse("rate limited", retry_after_s=1)


class _FailingForOneFileClient:
    """An ``AsyncQdrantClient`` proxy whose ``upsert`` fails FOREVER for ONE file.

    Wraps a REAL client and forwards every call EXCEPT an ``upsert`` whose points
    carry ``failing_file`` in their payload — that one raises ``error_factory()``
    on EVERY call (a persistent server-side error that never clears). All OTHER
    files' upserts pass through to the real server, so they index for real.
    Failing at the CLIENT layer (not above the store) means the store's own
    Layer-1 retry/backoff runs and is exhausted — so this one double exercises
    BOTH layers end-to-end: the store retries+backs off, gives up, and the
    indexer isolates the file. ``error_factory`` is injectable so a test can pin
    either the 500 (the original crash) or the 429+Retry-After overload class.
    """

    def __init__(
        self,
        inner: AsyncQdrantClient,
        *,
        failing_file: str,
        error_factory: Any = _server_error_500,
    ) -> None:
        self._inner = inner
        self._failing_file = failing_file
        self._error_factory = error_factory
        self.failed_upsert_attempts = 0

    async def upsert(self, **kwargs: Any) -> Any:
        points = kwargs.get("points") or []
        if any((point.payload or {}).get("file_path") == self._failing_file for point in points):
            self.failed_upsert_attempts += 1
            raise self._error_factory()
        return await self._inner.upsert(**kwargs)

    def __getattr__(self, name: str) -> Any:
        # Forward every other client method (collection_exists, create_collection,
        # delete, query_points, scroll, get_collection, …) to the real client.
        return getattr(self._inner, name)


# --------------------------------------------------------------------------- #
# Corpus + config builders
# --------------------------------------------------------------------------- #
def _write(path: Path, text: str) -> None:
    """Create parents and write ``text`` to ``path`` (UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# A small, real Python module that the real python_ast chunker splits into
# multiple chunks (imports + class + method + function). Used as live-tier
# corpus content — chunked for real, not stubbed.
_PY_MODULE = """\
import os

class Widget:
    \"\"\"A widget.\"\"\"

    def render(self, value):
        return os.linesep.join(str(value))


def make_widget():
    return Widget()
"""

# A second real module with a uniquely-named function, so a search can find it.
_PY_MODULE_2 = """\
def champion_routing(week):
    \"\"\"Route the 36-week curve champion.\"\"\"
    return week * 2
"""


def _build_live_corpus(root: Path) -> None:
    """Build a realistic live-tier tree with includes, excludes and prune dirs."""
    _write(root / "src" / "widget.py", _PY_MODULE)
    _write(root / "src" / "routing.py", _PY_MODULE_2)
    _write(root / "README.md", "# Project\n\nSome docs.\n")
    # An excluded-glob file (compiled artifact) that must NOT be indexed.
    _write(root / "src" / "bundle.min.js", "var x=1;")
    # A file inside an excluded DIR that must never be descended.
    _write(root / ".git" / "config.py", "SECRET = 'do-not-index'\n")
    _write(root / ".venv" / "lib" / "vendored.py", "junk = 1\n")


def _build_static_source(root: Path) -> None:
    """Build a small static-tier source tree the provider materialises."""
    _write(root / "lib" / "core.py", _PY_MODULE)


def _config(
    *,
    slug: str,
    live_path: Path | None = None,
    static_source: Path | None = None,
    static_version: str = "1.0.0",
) -> LoreConfig:
    """Build a validated :class:`LoreConfig` with optional live + static roots."""
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
    """A per-test slug → throwaway ``lore_test_<uuid4>`` collection."""
    return f"test_{uuid.uuid4().hex}"


def _count_text(text: str) -> int:
    """A heuristic single-string token count for the injected ChunkContext."""
    return max(1, len(text) // 4)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture()
async def store_factory() -> AsyncIterator[Any]:
    """Builder for a :class:`QdrantStore`, with CONCURRENCY-SAFE teardown.

    A SIBLING agent creates/deletes ``lore_test_*`` collections on the same
    shared server concurrently with this run, so the inherited ``qdrant_client``
    fixture's GLOBAL ``lore_test_*`` sweep would reap the other run's in-flight
    collections (and vice-versa) — non-deterministic failures. This fixture owns
    its OWN client and deletes ONLY the exact collection names *this* test
    created (tracked below), never a prefix sweep — so two runs never step on
    each other.
    """
    # Reuse the conftest key reader (process env → dotenv) without its sweep.
    from conftest import QDRANT_URL, _qdrant_api_key

    client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
    created: list[str] = []

    def _make(slug: str) -> QdrantStore:
        store = QdrantStore(client=client, slug=slug)
        created.append(store.collection_name)  # track for exact-name teardown
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
) -> Indexer:
    """Wire an :class:`Indexer` exactly as the CLI does (composed registry/providers)."""
    server = LoreServer(config)
    # Built-in provider per static root (the generic wiring the CLI performs).
    providers: list[Any] = list(server.source_providers)
    for root in config.roots:
        if root.watch == "static" and root.source is not None:
            providers.append(LocalDirectorySourceProvider(root.tier, Path(root.source)))
    return Indexer(
        store=store,
        embedder=embedder,
        manifest=manifest,
        registry=server.registry,
        source_providers=providers,
        config=config,
        snapshot_root=snapshot_root,
    )


# --------------------------------------------------------------------------- #
# index_file — the per-file pipeline
# --------------------------------------------------------------------------- #
class TestIndexFile:
    """``index_file`` chunks → embeds → records → upserts → commits the manifest."""

    async def test_indexes_a_real_python_file_end_to_end(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = FakeEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )

        source = (root / "src" / "widget.py").read_text(encoding="utf-8")
        outcome = await indexer.index_file("custom", "src/widget.py", source)

        # The real chunker splits this module into >1 chunk (imports/class/etc.).
        assert outcome.state == STATE_INDEXED
        assert outcome.n_chunks >= 3
        # The manifest row is committed in the indexed state with the chunk count.
        row = manifest.get("custom", "src/widget.py")
        assert row is not None
        assert row.state == STATE_INDEXED
        assert row.n_chunks == outcome.n_chunks
        assert len(row.chunk_ids) == outcome.n_chunks
        # The points actually landed on the real server, tagged with the tier.
        count = await store.search([0.0] * _DIM, k=100)
        assert count  # something was upserted
        assert all(
            hit.payload is not None and hit.payload["tier"] == "custom" for hit in count
        )

    async def test_reindex_unchanged_file_hits_fast_path_zero_embeds(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        source = (root / "src" / "widget.py").read_text(encoding="utf-8")

        await indexer.index_file("custom", "src/widget.py", source)
        embedded_after_first = embedder.total_embedded
        assert embedded_after_first >= 3

        # Re-index the SAME unchanged file: the mtime+size fast-path must skip it
        # with ZERO further embeds.
        second = await indexer.index_file("custom", "src/widget.py", source)
        assert second.state == "skipped"
        assert embedder.total_embedded == embedded_after_first

    async def test_embedder_failure_marks_file_failed_and_stores_no_vectors(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))

        # Determine the real chunk texts this file produces, then fail ALL of them.
        probe = FakeEmbedder(dim=_DIM)
        probe_indexer = _make_indexer(
            config=config, store=store, embedder=probe, manifest=Manifest(str(tmp_path / "p.db")),
            snapshot_root=tmp_path / "snap0",
        )
        source = (root / "src" / "widget.py").read_text(encoding="utf-8")
        texts = probe_indexer.chunk_texts("custom", "src/widget.py", source)
        assert texts  # the file does produce chunks

        embedder = FakeEmbedder(dim=_DIM, fail_inputs=set(texts))
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        outcome = await indexer.index_file("custom", "src/widget.py", source)

        assert outcome.state == STATE_FAILED
        row = manifest.get("custom", "src/widget.py")
        assert row is not None
        assert row.state == STATE_FAILED
        # No vectors for this file landed on the server.
        hits = await store.search([0.0] * _DIM, k=100)
        assert not any(
            hit.payload is not None and hit.payload["file_path"] == "src/widget.py"
            for hit in hits
        )

    async def test_nonfinite_vector_is_never_stored(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        source = (root / "src" / "widget.py").read_text(encoding="utf-8")

        probe = FakeEmbedder(dim=_DIM)
        probe_indexer = _make_indexer(
            config=config, store=store, embedder=probe, manifest=Manifest(str(tmp_path / "p.db")),
            snapshot_root=tmp_path / "snap0",
        )
        texts = probe_indexer.chunk_texts("custom", "src/widget.py", source)

        # Poison one chunk's vector with NaN. The isfinite guard must refuse the
        # whole file (no partial store of finite siblings alongside a NaN sibling
        # would be safe — the file is failed) — no points for it land.
        embedder = NonFiniteEmbedder(dim=_DIM, nan_texts={texts[0]})
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        outcome = await indexer.index_file("custom", "src/widget.py", source)

        assert outcome.state == STATE_FAILED
        hits = await store.search([0.0] * _DIM, k=100)
        # Crucially: NO NaN vector poisoned the collection.
        for hit in hits:
            assert hit.payload is not None
            assert hit.payload["file_path"] != "src/widget.py"

    async def test_update_upserts_new_before_purging_stale_no_gap(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """End-state of an update: NEW content present, stale purged.

        Note: being synchronous, this asserts the END state, not a mid-flight gap. Gap-freedom
        is guaranteed BY CONSTRUCTION in ``index_file`` — it upserts the new points BEFORE
        purging the stale ones, so a concurrent reader sees at worst brief duplicates, never a
        missing section. This test pins that the upsert-then-purge end result is correct.
        """
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = FakeEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )

        # Index v1 of a file with a uniquely-named function.
        v1 = "def alpha_marker():\n    return 1\n"
        await indexer.index_file("custom", "src/m.py", v1)
        hits_v1 = await store.search([0.0] * _DIM, k=100)
        identities_v1 = {
            h.payload["identity"]
            for h in hits_v1
            if h.payload is not None and h.payload["file_path"] == "src/m.py"
        }
        assert "alpha_marker" in identities_v1

        # Index v2: a DIFFERENT function. The new chunk must be present, and the
        # stale one purged — at no point is the file's content absent (the upsert
        # of new precedes the purge of stale).
        v2 = "def beta_marker():\n    return 2\n"
        await indexer.index_file("custom", "src/m.py", v2)
        hits_v2 = await store.search([0.0] * _DIM, k=100)
        identities_v2 = {
            h.payload["identity"]
            for h in hits_v2
            if h.payload is not None and h.payload["file_path"] == "src/m.py"
        }
        assert "beta_marker" in identities_v2
        assert "alpha_marker" not in identities_v2  # stale purged

    async def test_failed_reindex_retains_prior_good_points(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """Degradation/recovery (owner rule): a re-index whose embeds all FAIL keeps the
        file's PRIOR good vectors intact and marks the file failed — it does not purge the
        last-good content (upsert-of-new precedes purge-of-stale, so a failure before the
        upsert purges nothing). The file recovers on a later successful re-index.
        """
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))

        # v1 indexes cleanly → a good, queryable point.
        good = FakeEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=good, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        v1 = "def gamma_marker():\n    return 1\n"
        first = await indexer.index_file("custom", "src/m.py", v1)
        assert first.state != STATE_FAILED
        hits_v1 = await store.search([0.0] * _DIM, k=100)
        ids_v1 = {
            h.payload["identity"]
            for h in hits_v1
            if h.payload is not None and h.payload["file_path"] == "src/m.py"
        }
        assert "gamma_marker" in ids_v1

        # v2: CHANGED content (not fast-path-skipped), embedder fails ALL its chunks.
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
            snapshot_root=tmp_path / "snap",
        )
        outcome = await indexer2.index_file("custom", "src/m.py", v2)

        # The file is failed, the NEW content was never stored, and the PRIOR good point
        # survives (last-good retained, not purged).
        assert outcome.state == STATE_FAILED
        row = manifest.get("custom", "src/m.py")
        assert row is not None and row.state == STATE_FAILED
        hits_v2 = await store.search([0.0] * _DIM, k=100)
        ids_v2 = {
            h.payload["identity"]
            for h in hits_v2
            if h.payload is not None and h.payload["file_path"] == "src/m.py"
        }
        assert "gamma_marker" in ids_v2, "last-good vectors must survive a failed re-index"
        assert "delta_marker" not in ids_v2, "the failed new content must never be stored"

    async def test_file_edited_to_zero_chunks_purges_prior_points(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """A file whose new content yields NO chunks must not orphan its prior points."""
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM), manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )

        await indexer.index_file("custom", "src/m.py", "def keep_me():\n    return 1\n")
        before = await store.search([0.0] * _DIM, k=100)
        assert any(
            h.payload is not None and h.payload["file_path"] == "src/m.py" for h in before
        )

        # Edit to content the python_ast chunker yields zero chunks for (a bare
        # comment). The prior point must be purged, not left orphaned.
        await indexer.index_file("custom", "src/m.py", "# no symbols here\n")
        after = await store.search([0.0] * _DIM, k=100)
        assert not any(
            h.payload is not None and h.payload["file_path"] == "src/m.py" for h in after
        )
        # The manifest row reflects zero chunks, still indexed.
        row = manifest.get("custom", "src/m.py")
        assert row is not None and row.state == STATE_INDEXED and row.n_chunks == 0

    async def test_unknown_extension_yields_zero_chunks_skipped(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        # A file the registry does not claim → no chunks, no embeds, no points.
        outcome = await indexer.index_file("custom", "data.bin", "binary-ish junk")
        assert outcome.n_chunks == 0
        assert embedder.total_embedded == 0


# --------------------------------------------------------------------------- #
# Per-file pipeline logging
# --------------------------------------------------------------------------- #
class TestIndexerLogging:
    """``index_file`` emits structured per-file events (caplog-asserted).

    Variable data (tier/file_path/n_chunks/state/duration_ms/reason) rides in
    ``extra``; the event string is static. No source text or embedder object is
    ever logged.
    """

    async def test_successful_index_logs_file_done_with_fields(
        self, tmp_path: Path, store_factory: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM), manifest=manifest,
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
        # A non-negative duration is recorded (an int/float ms count).
        assert isinstance(record.duration_ms, (int, float))  # type: ignore[attr-defined]
        assert record.duration_ms >= 0  # type: ignore[attr-defined]

    async def test_failed_embed_logs_file_failed_with_reason(
        self, tmp_path: Path, store_factory: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_live_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))

        probe = FakeEmbedder(dim=_DIM)
        probe_indexer = _make_indexer(
            config=config, store=store, embedder=probe, manifest=Manifest(str(tmp_path / "p.db")),
            snapshot_root=tmp_path / "snap0",
        )
        source = (root / "src" / "widget.py").read_text(encoding="utf-8")
        texts = probe_indexer.chunk_texts("custom", "src/widget.py", source)
        embedder = FakeEmbedder(dim=_DIM, fail_inputs=set(texts))
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        with caplog.at_level(logging.WARNING, logger="loremaster.index.indexer"):
            await indexer.index_file("custom", "src/widget.py", source)

        events = [r for r in caplog.records if r.message == "index.file.failed"]
        assert len(events) == 1
        record = events[0]
        assert record.levelno == logging.WARNING
        assert record.tier == "custom"  # type: ignore[attr-defined]
        assert record.file_path == "src/widget.py"  # type: ignore[attr-defined]
        # A non-empty reason string explains the failure (no source text leaked).
        assert isinstance(record.reason, str) and record.reason  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
# Per-tier freshness (D5)
# --------------------------------------------------------------------------- #
class TestStaticTierFreshness:
    """Static-tier version-stamp: CHANGED → rebuild + re-stamp; MATCH → skip-no-walk."""

    async def test_absent_stamp_acquires_and_builds_then_stamps(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        config = _config(slug=slug, static_source=static_src, static_version="15.0.1")
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = FakeEmbedder(dim=_DIM)
        snapshot_root = tmp_path / "snap"
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=snapshot_root,
        )

        root = next(r for r in config.roots if r.tier == "community")
        summary = await indexer.index_tier(root)

        assert "community" in summary.tiers_rebuilt
        assert summary.files_indexed >= 1
        # The provider materialised the snapshot AND the version is stamped.
        materialized = SnapshotLayout(snapshot_root).materialization_dir("community")
        assert (materialized / "lib" / "core.py").exists()
        assert indexer.tier_version_stamp("community") == "15.0.1"
        # Points landed under the community tier on the real server.
        hits = await store.search([0.0] * _DIM, k=100)
        assert any(h.payload is not None and h.payload["tier"] == "community" for h in hits)

    async def test_matching_stamp_skips_with_zero_walk(
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

        # Pre-stamp the manifest as if this exact version was already built.
        indexer0 = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root,
        )
        indexer0.set_tier_version_stamp("community", "15.0.1")

        # Now build an indexer whose provider EXPLODES if acquire is called, and
        # whose embedder would record any embed. A matching stamp must skip both.
        exploding = ExplodingProvider("community")
        embedder = RecordingEmbedder(dim=_DIM)
        server = LoreServer(config)
        indexer = Indexer(
            store=store,
            embedder=embedder,
            manifest=manifest,
            registry=server.registry,
            source_providers=[exploding],
            config=config,
            snapshot_root=snapshot_root,
        )
        root = next(r for r in config.roots if r.tier == "community")
        summary = await indexer.index_tier(root)

        assert "community" in summary.tiers_skipped
        assert "community" not in summary.tiers_rebuilt
        assert exploding.acquired is False  # acquire never ran
        assert embedder.total_embedded == 0  # zero walk → zero embeds

    async def test_changed_stamp_rebuilds_and_restamps(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        snapshot_root = tmp_path / "snap"

        # Build at v1.
        config_v1 = _config(slug=slug, static_source=static_src, static_version="15.0.1")
        indexer_v1 = _make_indexer(
            config=config_v1, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root,
        )
        await indexer_v1.index_tier(next(r for r in config_v1.roots if r.tier == "community"))
        assert indexer_v1.tier_version_stamp("community") == "15.0.1"

        # Bump the version → must rebuild and re-stamp.
        config_v2 = _config(slug=slug, static_source=static_src, static_version="15.0.2")
        indexer_v2 = _make_indexer(
            config=config_v2, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root,
        )
        summary = await indexer_v2.index_tier(
            next(r for r in config_v2.roots if r.tier == "community")
        )
        assert "community" in summary.tiers_rebuilt
        assert indexer_v2.tier_version_stamp("community") == "15.0.2"


# --------------------------------------------------------------------------- #
# Selective per-tier rebuild — sibling tier untouched (real Qdrant)
# --------------------------------------------------------------------------- #
class TestSelectiveRebuild:
    """Rebuilding one tier purges only it; the sibling tier's points survive."""

    async def test_rebuild_one_tier_leaves_sibling_intact(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        snapshot_root = tmp_path / "snap"

        # Initial full build of BOTH tiers at community v1.
        config_v1 = _config(
            slug=slug, live_path=live, static_source=static_src, static_version="1"
        )
        indexer_v1 = _make_indexer(
            config=config_v1, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root,
        )
        await indexer_v1.index_all()

        live_before = await store.search([0.0] * _DIM, k=200, filters={"tier": "custom"})
        live_ids_before = {h.id for h in live_before}
        assert live_ids_before

        # Bump ONLY the community version → community rebuilds, custom untouched.
        config_v2 = _config(
            slug=slug, live_path=live, static_source=static_src, static_version="2"
        )
        indexer_v2 = _make_indexer(
            config=config_v2, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root,
        )
        summary = await indexer_v2.index_all()
        assert "community" in summary.tiers_rebuilt

        # The custom-tier points are exactly as before (delete_by_tier touched
        # only community). The live tier is re-walked but its content is unchanged
        # so the SAME deterministic point ids persist.
        live_after = await store.search([0.0] * _DIM, k=200, filters={"tier": "custom"})
        assert {h.id for h in live_after} == live_ids_before
        # Community still has its points after the rebuild.
        community_after = await store.search([0.0] * _DIM, k=200, filters={"tier": "community"})
        assert community_after


# --------------------------------------------------------------------------- #
# index_all / index_status — the summary surface + include/exclude
# --------------------------------------------------------------------------- #
def _single_tree_config(*, slug: str, project_root: Path) -> LoreConfig:
    """Build a single-tree config: top-level ``include`` globs and NO ``roots:``.

    This is the documented Deliverable-3 style. ``roots`` is omitted entirely so
    the indexer must fall back to the synthesised default live root rooted at
    ``project.root`` — exercising the single-tree footgun fix.
    """
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
        "qdrant": {"url": "http://127.0.0.1:16333", "api_key_env": "QDRANT__SERVICE__API_KEY"},
        # NO "roots" key at all — the single-tree footgun shape.
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

    async def test_index_all_with_empty_roots_indexes_top_level_include(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        # The footgun: roots=[] + top-level include must index the matching files,
        # NOT silently index nothing. Before the fix index_all iterates config.roots
        # (empty) and indexes zero files.
        slug = _slug()
        project_root = tmp_path / "tree"
        _build_live_corpus(project_root)
        config = _single_tree_config(slug=slug, project_root=project_root)
        assert config.roots == []  # the single-tree shape: no explicit roots
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )

        summary = await indexer.index_all()

        # Files were actually indexed (not silently zero).
        assert summary.files_indexed > 0
        indexed_paths = {o.file_path for o in summary.outcomes if o.state == STATE_INDEXED}
        assert "src/widget.py" in indexed_paths
        assert "src/routing.py" in indexed_paths
        assert "README.md" in indexed_paths
        # Project-level exclude_dirs / exclude_globs still apply to the synthesised root.
        assert "src/bundle.min.js" not in indexed_paths
        assert not any(p.startswith(".git/") for p in indexed_paths)
        assert not any(p.startswith(".venv/") for p in indexed_paths)


class TestIndexAllAndStatus:
    """``index_all`` walks live tiers + freshness-gates static; ``index_status`` reports."""

    async def test_include_exclude_pruning(
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
        await indexer.index_all()

        indexed_paths = {row.file_path for row in manifest.files_for_tier("custom")}
        # Included real files are indexed.
        assert "src/widget.py" in indexed_paths
        assert "src/routing.py" in indexed_paths
        assert "README.md" in indexed_paths
        # The excluded-glob file is NOT indexed.
        assert "src/bundle.min.js" not in indexed_paths
        # No file from an excluded DIR was ever descended.
        assert not any(p.startswith(".git/") for p in indexed_paths)
        assert not any(p.startswith(".venv/") for p in indexed_paths)

    async def test_index_status_summarizes_indexed_and_failed(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))

        # Fail exactly the chunks of routing.py; widget.py + README index fine.
        probe = FakeEmbedder(dim=_DIM)
        probe_indexer = _make_indexer(
            config=config, store=store, embedder=probe,
            manifest=Manifest(str(tmp_path / "p.db")), snapshot_root=tmp_path / "snap0",
        )
        routing_src = (live / "src" / "routing.py").read_text(encoding="utf-8")
        fail_texts = set(probe_indexer.chunk_texts("custom", "src/routing.py", routing_src))

        embedder = FakeEmbedder(dim=_DIM, fail_inputs=fail_texts)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        await indexer.index_all()

        status = indexer.index_status()
        # At least one file failed (routing.py) and at least one indexed.
        assert status.files_failed >= 1
        assert status.files_indexed >= 1
        # The failed file is recorded as failed in the manifest.
        routing_row = manifest.get("custom", "src/routing.py")
        assert routing_row is not None and routing_row.state == STATE_FAILED
        # An unrelated file still indexed successfully.
        widget_row = manifest.get("custom", "src/widget.py")
        assert widget_row is not None and widget_row.state == STATE_INDEXED

    async def test_index_status_reads_manifest_without_embedding(
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
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        await indexer.index_all()
        embedded_after_build = embedder.total_embedded

        # index_status() is a pure manifest read — zero further embeds.
        status = indexer.index_status()
        assert status.files_indexed >= 1
        assert embedder.total_embedded == embedded_after_build


# --------------------------------------------------------------------------- #
# Per-file STORE-failure isolation (the cold-index crash regression)
# --------------------------------------------------------------------------- #
class TestStoreFailureIsolation:
    """A persistent Qdrant error for ONE file must isolate it, not crash the index.

    The actual failure this fixes: a ~731-file cold index crashed two-thirds in
    on an UNCAUGHT Qdrant 500 during a per-file ``upsert``. The embedder had
    resilient retry; the store did not. After the fix, a store error that
    persists past the store's own retry budget for ONE file marks THAT file
    ``failed`` and lets ``index_all`` complete-with-failures — the other files
    still reach ``indexed`` and NO exception escapes. Both Qdrant overload
    signatures are covered: the original 500 ``UnexpectedResponse`` and the
    429+``Retry-After`` ``ResourceExhaustedResponse`` (a ``QdrantException`` that
    is NOT an ``UnexpectedResponse`` — the class that slipped past both layers).
    """

    async def _assert_one_file_isolated(
        self,
        *,
        tmp_path: Path,
        store_factory: Any,
        error_factory: Any,
    ) -> None:
        """Drive ``index_all`` with one file's ``upsert`` raising ``error_factory()``
        on every attempt; assert BOTH layers (store retry + indexer isolation) ran
        and the index completed-with-failures with no exception escaping.
        """
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        # A real store creates the collection + holds the real client; ``inner`` is
        # used only to verify what actually landed on the server. The indexer's
        # store shares that real collection but routes through a client whose
        # ``upsert`` raises a persistent error for routing.py only.
        inner = store_factory(slug)
        await inner.ensure_collection(_DIM)
        failing_client = _FailingForOneFileClient(
            inner._client, failing_file="src/routing.py", error_factory=error_factory
        )
        recorded: list[float] = []

        async def fake_sleep(delay: float) -> None:
            recorded.append(delay)

        # Same collection (slug), but a fast bounded retry over the failing client.
        store = QdrantStore(
            client=failing_client,  # type: ignore[arg-type]
            slug=slug,
            max_retries=3,
            sleep_fn=fake_sleep,
        )
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )

        # The whole-project index must COMPLETE — no store exception escapes.
        summary = await indexer.index_all()

        # Layer 1 ran: the store retried the transient error (bounded by
        # max_retries) and backed off before giving up.
        assert failing_client.failed_upsert_attempts == 3  # exactly the retry cap
        assert recorded, "the store's transient retry must have backed off before failing"
        # Layer 2 ran: the bad file is isolated as failed; the others reached indexed.
        assert summary.files_failed >= 1
        assert summary.files_indexed >= 1
        routing_row = manifest.get("custom", "src/routing.py")
        assert routing_row is not None and routing_row.state == STATE_FAILED
        widget_row = manifest.get("custom", "src/widget.py")
        assert widget_row is not None and widget_row.state == STATE_INDEXED
        readme_row = manifest.get("custom", "README.md")
        assert readme_row is not None and readme_row.state == STATE_INDEXED
        # The surviving files' vectors actually landed on the real server.
        hits = await inner.search([0.0] * _DIM, k=200)
        landed = {h.payload["file_path"] for h in hits if h.payload is not None}
        assert "src/widget.py" in landed
        assert "src/routing.py" not in landed  # the failed file stored nothing

    async def test_persistent_500_for_one_file_isolates_it(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        # The original cold-index crash class: a persistent 500 UnexpectedResponse.
        await self._assert_one_file_isolated(
            tmp_path=tmp_path, store_factory=store_factory,
            error_factory=_server_error_500,
        )

    async def test_persistent_429_retry_after_for_one_file_isolates_it(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        # The overload class that slipped past BOTH layers before the fix: a 429
        # with Retry-After → ResourceExhaustedResponse (NOT an UnexpectedResponse).
        # It must be retried by the store AND isolated by the indexer, exactly like
        # the 500 — an overloaded Qdrant must never crash the whole batch index.
        await self._assert_one_file_isolated(
            tmp_path=tmp_path, store_factory=store_factory,
            error_factory=_resource_exhausted_429,
        )


# --------------------------------------------------------------------------- #
# CLI surface — argparse, stdlib only
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

    def test_cli_parser_accepts_graph_and_defaults_to_none(self) -> None:
        # The --graph arg mirrors --manifest: explicit path honoured, else None
        # (the CLI then defaults it alongside the manifest as <slug>.graph.db).
        from loremaster.index.cli import build_parser

        parser = build_parser()
        assert parser.parse_args(["--config", "/tmp/lore.yaml"]).graph is None
        explicit = parser.parse_args(
            ["--config", "/tmp/lore.yaml", "--graph", "/tmp/lore.graph.db"]
        )
        assert explicit.graph == "/tmp/lore.graph.db"


# --------------------------------------------------------------------------- #
# Optional ONE real-TEI end-to-end smoke (skips cleanly if /health != 200)
# --------------------------------------------------------------------------- #
def _tei_healthy() -> bool:
    """Return True iff the real TEI ``/health`` returns 200 within a short timeout."""
    if not os.environ.get(_TEI_KEY_ENV):
        return False
    try:
        response = httpx.get(f"{_TEI_BASE_URL}/health", timeout=4.0)
    except httpx.HTTPError:
        return False
    return response.status_code == 200


@pytest.mark.skipif(not _tei_healthy(), reason="real TEI endpoint /health != 200 or no key")
class TestRealTeiSmoke:
    """One tiny real-corpus end-to-end against the live TEI embedder (dim 2048)."""

    async def test_indexes_a_tiny_corpus_through_real_tei(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        from loresigil.factory import EmbeddingConfig, make_embedder

        slug = _slug()
        live = tmp_path / "live"
        _write(live / "tiny.py", _PY_MODULE_2)  # a few small chunks only
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = make_embedder(
            EmbeddingConfig(
                backend="tei",
                base_url=_TEI_BASE_URL,
                endpoint="/embed",
                api_key_env=_TEI_KEY_ENV,
                dim=_DIM,
                max_input_tokens=8192,
            )
        )
        observed = await embedder.probe()
        assert observed == _DIM
        await store.ensure_collection(_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        summary = await indexer.index_all()
        assert summary.files_indexed >= 1
        assert summary.files_failed == 0
        # Real 2048-dim vectors landed and are searchable.
        hits = await store.search(await embedder.embed_query("champion routing"), k=5)
        assert hits
