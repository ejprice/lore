"""Contract tests: per-file fault isolation for CHUNKER exceptions (live-bug driven).

The bug (found deploying lore on the Odoo 15 tree): ``odoo/tests/dummy.xml``
ships with the ENTIRE content ``<!-- Should not be read by anyone -->`` —
comment-only, no root element, deliberately invalid. The XML chunker's parse
raises (``xml.etree.ElementTree.ParseError`` wrapping expat's "no element
found"), and that exception propagates UNCAUGHT out of the indexer's chunk
step, killing the whole eager startup build: the container's three internal
retries all re-walk to the same file (a failed/absent manifest row is never
fast-path-skipped) and die the same way; the container exits.

The EMBED step already has exactly the right per-file isolation — a failed
embed marks the one file ``failed``, stores nothing for it, and lets siblings
continue (see ``_index_chunks`` and ``tests/test_indexer.py``'s
failure-isolation tests). This file pins the SAME isolation for the CHUNK
step, at every level the exception can propagate through:

1. **Walk level** (``index_all`` / ``index_tier`` → ``_walk_and_index`` — the
   exact frames the crash climbed): a file whose chunker raises is committed
   ``failed`` (zero chunks, nothing stored), the sweep CONTINUES, siblings
   index normally, and the summary's ``files_failed`` counts it. The
   ``index.file.failed`` event carries a CHUNKER-distinguishable reason
   (distinct from the embed and store reasons, naming the chunk step).
2. **Live-event level** (``index_file`` — the watcher's per-event path): the
   same raise returns a ``failed`` outcome instead of propagating, so the
   regression cannot re-enter via the event path.
3. **Re-attempt / recovery**: a subsequent sweep re-attempts the failed file
   (state stays ``failed`` while it is unchanged — no crash, no churn) and
   recovers it to ``indexed`` once the file becomes parseable.
4. **Eager-startup level** (``build_app_context(start_tasks=True)`` — where
   the crash ACTUALLY happened, via ``watcher.run_sweep`` →
   ``ReconcileEngine.reconcile``): the build completes (does not raise) over a
   tree containing such a file, and ``index_status`` reports the failure.

Adversarial corpus — four REAL invalid shapes through the REAL XML chunker
(no synthetic raising chunker, so the isolation is proven against genuine
exception types, plural):

* ``odoo/tests/dummy.xml`` — byte-for-byte the real Odoo 15 file
  (``<!-- Should not be read by anyone -->`` + newline): ParseError
  "no element found".
* an EMPTY ``.xml``: ParseError "no element found" at line 1.
* a TRUNCATED/garbage ``.xml`` (unclosed token): ParseError "unclosed token".
* an OVER-DEEP ``.xml`` (nested past ``lorescribe.xml_generic.MAX_DEPTH``):
  ``ValueError`` from the recursion-DoS gate — a SECOND exception type, so an
  implementation that only catches ParseError/ExpatError still fails here.

Expected RED on current code: the ParseError propagates out of
``index_file`` / ``index_tier`` / ``index_all`` / ``build_app_context`` — every
test in this file dies with the raised chunker exception (behavioral failure,
not a structural/collection error). That propagating exception IS the bug.

Harness conventions mirror ``tests/test_indexer.py``: REAL local Qdrant
(throwaway ``lore_test_*`` collections), a REAL corpus chunked through the
default lorescribe registry (XmlChunker is registered for ``.xml`` by
``LoreServer`` itself), and a FakeEmbedder-family double for the embed step.
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
from loremaster.index.indexer import (
    _FAILED_EMBED_REASON,
    _FAILED_STORE_REASON,
    Indexer,
)
from loremaster.index.manifest import STATE_FAILED, STATE_INDEXED, Manifest
from loremaster.server import LoreServer
from loremaster.store.qdrant import QdrantStore
from lorescribe.xml_generic import MAX_DEPTH
from loresigil.base import Embedder, EmbedResult
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient

# Production embedding dimensionality (matches the rest of the loremaster suite).
_DIM = 2048

_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"

# ---------------------------------------------------------------------------
# The poison fixtures — REAL invalid XML shapes.
# ---------------------------------------------------------------------------

# Byte-for-byte the content of the real /odoo/odoo/tests/dummy.xml (verified
# against the production Odoo 15 source tree): one comment line + newline, no
# root element. Deliberately invalid upstream ("Should not be read by anyone").
_DUMMY_XML_CONTENT = "<!-- Should not be read by anyone -->\n"

# The tier-relative path mirroring where the real file lives in the Odoo tree.
_DUMMY_XML_PATH = "odoo/tests/dummy.xml"

# An empty .xml file — "no element found" at line 1 (a real deploy shape:
# placeholder/touched-but-never-written data files).
_EMPTY_XML_PATH = "data/placeholder.xml"

# A truncated record file (unclosed token) — the shape a killed editor/rsync
# leaves behind.
_TRUNCATED_XML_PATH = "data/ir_rule_partial.xml"
_TRUNCATED_XML_CONTENT = '<odoo><data><record id="res_partner_rule"'

# An over-deep document: nests past the chunker's recursion-DoS gate
# (lorescribe.xml_generic.MAX_DEPTH — the SHARED production constant, never a
# hand-copied 256), raising ValueError — a second exception TYPE so the
# isolation is proven for "any exception", not just ParseError/ExpatError.
_OVERDEEP_XML_PATH = "data/generated_menu_tree.xml"
_OVERDEEP_DEPTH = MAX_DEPTH + 2
_OVERDEEP_XML_CONTENT = (
    "".join(f"<menu{i}>" for i in range(_OVERDEEP_DEPTH))
    + "x"
    + "".join(f"</menu{i}>" for i in reversed(range(_OVERDEEP_DEPTH)))
)

# The full set of poison files a corpus-level sweep must isolate.
_POISON_FILES: dict[str, str] = {
    _DUMMY_XML_PATH: _DUMMY_XML_CONTENT,
    _EMPTY_XML_PATH: "",
    _TRUNCATED_XML_PATH: _TRUNCATED_XML_CONTENT,
    _OVERDEEP_XML_PATH: _OVERDEEP_XML_CONTENT,
}

# ---------------------------------------------------------------------------
# Healthy siblings — prove the same sweep still indexes them normally.
# ---------------------------------------------------------------------------

_HEALTHY_PY_PATH = "models/sale_margin.py"
_HEALTHY_PY_CONTENT = '''\
"""Sale-order margin helpers."""


def order_margin(price_total, cost_total):
    """The absolute margin on one order."""
    return price_total - cost_total
'''

# A realistic, well-formed Odoo view file — proves the XML CHUNKER itself is
# healthy in this sweep (the failures are the documents' fault, not the
# chunker's), so isolation is not conflated with a broken chunker.
_HEALTHY_XML_PATH = "views/sale_margin_views.xml"
_HEALTHY_XML_CONTENT = """\
<odoo>
    <record id="view_sale_margin_tree" model="ir.ui.view">
        <field name="name">sale.order.margin.tree</field>
        <field name="model">sale.order</field>
    </record>
</odoo>
"""

_HEALTHY_FILES: dict[str, str] = {
    _HEALTHY_PY_PATH: _HEALTHY_PY_CONTENT,
    _HEALTHY_XML_PATH: _HEALTHY_XML_CONTENT,
}

# The VALID replacement content the recovery test rewrites dummy.xml to — a
# realistic minimal record document (what an operator shipping a fixed data
# file would actually write).
_RECOVERED_XML_CONTENT = """\
<odoo>
    <record id="dummy_marker" model="ir.model.data">
        <field name="name">dummy_marker</field>
    </record>
</odoo>
"""


# --------------------------------------------------------------------------- #
# Recording embedder double (path-agnostic: counts BOTH embed call flavours)
# --------------------------------------------------------------------------- #
class DualPathRecordingEmbedder(FakeEmbedder):
    """A :class:`FakeEmbedder` recording every embed call on EITHER path.

    The chunk step runs BEFORE the embed step, so a chunker-failed file must
    produce ZERO embed activity. This double counts files embedded through the
    flat call (one ``embed_documents`` per file) AND the grouped call (one doc
    per file inside ``embed_document_chunks``), so the zero-embed oracle holds
    no matter which dispatch path the indexer takes for this embedder.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.flat_batches: list[list[str]] = []
        self.grouped_docs: list[list[str]] = []

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        self.flat_batches.append(list(texts))
        return await super().embed_documents(texts)

    async def embed_document_chunks(self, docs: list[list[str]]) -> list[EmbedResult]:
        self.grouped_docs.extend([list(doc) for doc in docs])
        return await super().embed_document_chunks(docs)

    @property
    def files_embedded(self) -> int:
        """Total embed units seen: flat batches + grouped docs (one per file)."""
        return len(self.flat_batches) + len(self.grouped_docs)


# --------------------------------------------------------------------------- #
# Corpus + config builders (mirroring test_indexer.py conventions)
# --------------------------------------------------------------------------- #
def _write(base: Path, rel_path: str, text: str) -> None:
    """Create parents and write ``text`` under ``base / rel_path`` (UTF-8)."""
    path = base / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _build_odoo_like_corpus(root: Path, *, poison: bool = True) -> None:
    """Build the live-tier tree: healthy .py/.xml siblings + the poison files."""
    for rel_path, content in _HEALTHY_FILES.items():
        _write(root, rel_path, content)
    if poison:
        for rel_path, content in _POISON_FILES.items():
            _write(root, rel_path, content)


def _config(*, slug: str, live_path: Path) -> LoreConfig:
    """A validated single-live-root :class:`LoreConfig` including ``**/*.xml``.

    Mirrors the Odoo-deploy shape that surfaced the bug: python AND xml files
    in one live tier. The XML chunker is registered for ``.xml`` by
    ``LoreServer`` itself (the default registry), so no chunker override is
    needed — exactly as in the failing deployment.
    """
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
        "roots": [
            {
                "tier": "custom",
                "watch": "live",
                "path": str(live_path),
                "include": ["**/*.py", "**/*.xml"],
                "exclude": [],
            }
        ],
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}, ".xml": {"chunker": "xml"}},
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
    """A per-test slug -> throwaway ``lore_test_<uuid4>`` collection."""
    return f"test_{uuid.uuid4().hex}"


def _make_indexer(
    *,
    config: LoreConfig,
    store: QdrantStore,
    embedder: Embedder,
    manifest: Manifest,
    snapshot_root: Path,
) -> Indexer:
    """Wire an :class:`Indexer` exactly as the CLI does (mirrors test_indexer.py)."""
    server = LoreServer(config)
    return Indexer(
        store=store,
        embedder=embedder,
        manifest=manifest,
        registry=server.registry,
        source_providers=list(server.source_providers),
        config=config,
        snapshot_root=snapshot_root,
    )


@pytest_asyncio.fixture()
async def store_factory() -> AsyncIterator[Any]:
    """Builder for a :class:`QdrantStore` with concurrency-safe exact-name teardown."""
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


async def _stored_file_paths(store: QdrantStore) -> set[str]:
    """Every distinct payload ``file_path`` currently stored — the store oracle."""
    hits = await store.search([0.0] * _DIM, k=200)
    return {
        hit.payload["file_path"]
        for hit in hits
        if hit.payload is not None and "file_path" in hit.payload
    }


# --------------------------------------------------------------------------- #
# 1. Walk-level isolation — the frames the production crash climbed
# --------------------------------------------------------------------------- #
class TestChunkerFaultIsolationInSweep:
    """A chunker raise fails ONE file; the sweep completes and siblings index."""

    async def test_sweep_over_poisoned_tree_completes_and_isolates_each_bad_file(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM), manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )

        # RED today: the ParseError from dummy.xml propagates out of index_all
        # and this await raises instead of returning a summary.
        summary = await indexer.index_all()

        # The sweep COMPLETED and counted each poison file as failed, exactly.
        assert summary.files_failed == len(_POISON_FILES)
        assert summary.files_indexed == len(_HEALTHY_FILES)

        # Every poison file: manifest row failed, zero chunks committed.
        for rel_path in _POISON_FILES:
            row = manifest.get("custom", rel_path)
            assert row is not None, f"{rel_path} must have a committed manifest row"
            assert row.state == STATE_FAILED, f"{rel_path} must be failed"
            assert row.n_chunks == 0, f"{rel_path} must have zero chunks committed"

        # Every healthy sibling: indexed normally in the SAME sweep.
        for rel_path in _HEALTHY_FILES:
            row = manifest.get("custom", rel_path)
            assert row is not None and row.state == STATE_INDEXED

        # The store holds points ONLY for the healthy files — nothing for any
        # poison file (zero chunks stored is a store-level fact, not just a
        # manifest-level count).
        stored = await _stored_file_paths(store)
        assert stored == set(_HEALTHY_FILES)

    async def test_chunker_failed_file_never_reaches_the_embedder(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = DualPathRecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )

        await indexer.index_all()

        # The chunk step precedes the embed step: only the healthy files may
        # produce embed activity (one embed unit per file, either path).
        assert embedder.files_embedded == len(_HEALTHY_FILES)

    async def test_chunker_failure_logs_a_chunker_distinguishable_reason(
        self, tmp_path: Path, store_factory: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM), manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )

        with caplog.at_level(logging.WARNING, logger="loremaster.index.indexer"):
            await indexer.index_all()

        failed_events = [r for r in caplog.records if r.message == "index.file.failed"]
        # One failure event per poison file, each carrying the poisoned path.
        assert {r.file_path for r in failed_events} == set(_POISON_FILES)  # type: ignore[attr-defined]
        for record in failed_events:
            reason: str = record.reason  # type: ignore[attr-defined]
            # A chunker failure must be TRIAGEABLE as a chunker failure: the
            # reason is non-empty, names the chunk step, and is distinct from
            # the embed and store reasons (the existing shared constants — the
            # single source of truth, never hand-copied literals).
            assert isinstance(reason, str) and reason
            assert "chunk" in reason
            assert reason != _FAILED_EMBED_REASON
            assert reason != _FAILED_STORE_REASON


# --------------------------------------------------------------------------- #
# 2. Live-event-level isolation — index_file (the watcher's per-event path)
# --------------------------------------------------------------------------- #
class TestChunkerFaultIsolationOnIndexFile:
    """``index_file`` returns a ``failed`` outcome instead of propagating."""

    async def test_index_file_on_comment_only_xml_returns_failed_outcome(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root, poison=False)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM), manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )

        # RED today: xml.etree.ElementTree.ParseError propagates out of this
        # call (the watcher's live-event path would crash the drain worker).
        outcome = await indexer.index_file("custom", _DUMMY_XML_PATH, _DUMMY_XML_CONTENT)

        assert outcome.state == STATE_FAILED
        assert outcome.n_chunks == 0
        row = manifest.get("custom", _DUMMY_XML_PATH)
        assert row is not None and row.state == STATE_FAILED
        assert await _stored_file_paths(store) == set()


# --------------------------------------------------------------------------- #
# 3. Re-attempt + recovery across sweeps
# --------------------------------------------------------------------------- #
class TestChunkerFailureReattemptAndRecovery:
    """Unchanged → stays failed without crashing; fixed → recovers to indexed."""

    async def test_second_sweep_over_unchanged_poison_completes_and_stays_failed(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = DualPathRecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )

        await indexer.index_all()
        embedded_after_first = embedder.files_embedded

        # The container's retry loop is exactly this: sweep again, unchanged
        # tree. It must complete again (no crash), the poison files are
        # RE-ATTEMPTED (a failed row is never fast-path-skipped) and stay
        # failed, and the healthy siblings ride the fast-path (zero re-embeds
        # — no churn).
        second = await indexer.index_all()

        assert second.files_failed == len(_POISON_FILES)
        assert second.files_skipped == len(_HEALTHY_FILES)
        assert embedder.files_embedded == embedded_after_first  # no embed churn
        for rel_path in _POISON_FILES:
            row = manifest.get("custom", rel_path)
            assert row is not None and row.state == STATE_FAILED

    async def test_failed_file_recovers_to_indexed_once_parseable(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM), manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        await indexer.index_all()
        row = manifest.get("custom", _DUMMY_XML_PATH)
        assert row is not None and row.state == STATE_FAILED  # precondition

        # The operator ships a FIXED, parseable file at the same path.
        _write(root, _DUMMY_XML_PATH, _RECOVERED_XML_CONTENT)

        recovery = await indexer.index_all()

        # The recovered file is indexed this sweep; its points now exist.
        row = manifest.get("custom", _DUMMY_XML_PATH)
        assert row is not None
        assert row.state == STATE_INDEXED
        assert row.n_chunks >= 1
        assert _DUMMY_XML_PATH in await _stored_file_paths(store)
        # The other poison files are still isolated failures, not crashes.
        assert recovery.files_failed == len(_POISON_FILES) - 1


# --------------------------------------------------------------------------- #
# 4. Eager-startup level — where the container actually died
# --------------------------------------------------------------------------- #
class TestEagerStartupSurvivesUnparseableFile:
    """``build_app_context(start_tasks=True)`` completes over a poisoned tree.

    This is the level the production crash happened at: the eager lifespan's
    initial sweep (``watcher.run_sweep`` → ``ReconcileEngine.reconcile`` →
    ``indexer.index_tier``) hit dummy.xml and the ParseError climbed all the
    way out of ``build_app_context``, killing startup — three container
    retries, same file, container exit. Pinning here (not just at
    ``_index_chunks``' level) means the regression cannot re-enter via a
    different call site on the startup/reconcile path.
    """

    @pytest_asyncio.fixture()
    async def qdrant(self) -> AsyncIterator[Any]:
        """A real Qdrant client; deletes exactly the collections this test created.

        ``build_app_context`` creates BOTH the project collection and its
        ``_memory`` sibling, so teardown reaps both (mirrors
        test_extension.py's qdrant fixture).
        """
        from conftest import QDRANT_URL, _qdrant_api_key

        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        created: list[str] = []
        client._lore_created = created  # type: ignore[attr-defined]
        try:
            yield client
        finally:
            for name in created:
                if await client.collection_exists(name):
                    await client.delete_collection(name)
            await client.close()

    async def test_eager_startup_build_completes_and_reports_the_failure(
        self, tmp_path: Path, qdrant: Any
    ) -> None:
        from loremaster.server import build_app_context

        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root)
        config = _config(slug=slug, live_path=root)
        server = LoreServer(config)
        qdrant._lore_created.append(f"lore_{slug}")
        qdrant._lore_created.append(f"lore_{slug}_memory")

        # RED today: the ParseError from dummy.xml propagates out of the
        # initial sweep inside build_app_context and this await raises —
        # exactly the production container-exit signature.
        app_context = await build_app_context(
            server=server,
            embedder=FakeEmbedder(dim=_DIM),
            qdrant_client=qdrant,
            manifest_path=tmp_path / "m.db",
            graph_path=tmp_path / "graph.db",
            snapshot_root=tmp_path / "snap",
            start_tasks=True,
        )
        try:
            # The build survived AND is honest about the poison: the status
            # roll-up counts every poison file failed and every healthy file
            # indexed — a live server over a poisoned tree, not a dead container.
            status = app_context.indexer.index_status()
            assert status.files_failed == len(_POISON_FILES)
            assert status.files_indexed >= len(_HEALTHY_FILES)
        finally:
            await app_context.aclose()
