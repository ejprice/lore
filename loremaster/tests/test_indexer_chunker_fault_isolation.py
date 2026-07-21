"""Contract tests: per-file fault isolation for CHUNKER exceptions (live-bug driven).

PORTED for P5-C3b onto the async Surreal fakes (:mod:`_surreal_fakes`). The
behavioural pins are UNCHANGED — a chunker exception isolates the ONE poisoned
file (marked ``failed``, nothing stored) while the sweep completes and healthy
siblings index — only the fixtures change: the real Qdrant + SQLite manifest
become the fast in-memory async fakes, store-side assertions read the fake's
recorded state, and every manifest read is ``await``ed.

The bug (found deploying lore on the Odoo 15 tree): ``odoo/tests/dummy.xml`` ships
comment-only (``<!-- Should not be read by anyone -->``), the XML chunker raises
``ParseError``, and that propagated UNCAUGHT out of the indexer's chunk step,
killing the eager startup build. The isolation is pinned at every level the
exception can propagate through:

1. **Walk level** (``index_all`` / ``index_tier`` → ``_walk_and_index``): a
   chunker-raising file is committed ``failed`` (zero chunks, nothing stored), the
   sweep CONTINUES, siblings index, ``files_failed`` counts it, and the
   ``index.file.failed`` event carries a CHUNKER-distinguishable reason.
2. **Live-event level** (``index_file`` — the watcher's per-event path): the same
   raise returns a ``failed`` outcome instead of propagating.
3. **Re-attempt / recovery**: a later sweep re-attempts the failed file (stays
   ``failed`` while unchanged) and recovers it to ``indexed`` once parseable.

Adversarial corpus — four REAL invalid shapes through the REAL XML chunker.

The pre-port eager-startup class (``TestEagerStartupSurvivesUnparseableFile``,
which drove ``build_app_context`` — the SERVER lifespan wired with Qdrant/Kùzu)
is DROPPED here and reported to the team lead: ``build_app_context`` is
server-level and its Surreal migration is a SEPARATE concern from the
indexer/reconcile/watcher rewiring this task covers.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

import pytest
from _surreal_fakes import FakeSurrealTrio, fake_surreal_trio
from loremaster.config import LoreConfig
from loremaster.index.indexer import (
    _FAILED_EMBED_REASON,
    _FAILED_STORE_REASON,
    Indexer,
)
from loremaster.index.surreal_manifest import STATE_FAILED, STATE_INDEXED
from loremaster.server import LoreServer
from lorescribe.xml_generic import MAX_DEPTH
from loresigil.base import Embedder, EmbedResult
from loresigil.testing import FakeEmbedder

_DIM = 2048
_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"

# ---------------------------------------------------------------------------
# The poison fixtures — REAL invalid XML shapes.
# ---------------------------------------------------------------------------

# Byte-for-byte the content of the real /odoo/odoo/tests/dummy.xml.
_DUMMY_XML_CONTENT = "<!-- Should not be read by anyone -->\n"
_DUMMY_XML_PATH = "odoo/tests/dummy.xml"

_EMPTY_XML_PATH = "data/placeholder.xml"

_TRUNCATED_XML_PATH = "data/ir_rule_partial.xml"
_TRUNCATED_XML_CONTENT = '<odoo><data><record id="res_partner_rule"'

# An over-deep document past the chunker's recursion-DoS gate (the SHARED
# production constant), raising ValueError — a SECOND exception TYPE.
_OVERDEEP_XML_PATH = "data/generated_menu_tree.xml"
_OVERDEEP_DEPTH = MAX_DEPTH + 2
_OVERDEEP_XML_CONTENT = (
    "".join(f"<menu{i}>" for i in range(_OVERDEEP_DEPTH))
    + "x"
    + "".join(f"</menu{i}>" for i in reversed(range(_OVERDEEP_DEPTH)))
)

_POISON_FILES: dict[str, str] = {
    _DUMMY_XML_PATH: _DUMMY_XML_CONTENT,
    _EMPTY_XML_PATH: "",
    _TRUNCATED_XML_PATH: _TRUNCATED_XML_CONTENT,
    _OVERDEEP_XML_PATH: _OVERDEEP_XML_CONTENT,
}

# ---------------------------------------------------------------------------
# Healthy siblings.
# ---------------------------------------------------------------------------

_HEALTHY_PY_PATH = "models/sale_margin.py"
_HEALTHY_PY_CONTENT = '''\
"""Sale-order margin helpers."""


def order_margin(price_total, cost_total):
    """The absolute margin on one order."""
    return price_total - cost_total
'''

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
    """A :class:`FakeEmbedder` recording every embed call on EITHER path."""

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
        return len(self.flat_batches) + len(self.grouped_docs)


# --------------------------------------------------------------------------- #
# Corpus + config builders
# --------------------------------------------------------------------------- #
def _write(base: Path, rel_path: str, text: str) -> None:
    path = base / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _build_odoo_like_corpus(root: Path, *, poison: bool = True) -> None:
    for rel_path, content in _HEALTHY_FILES.items():
        _write(root, rel_path, content)
    if poison:
        for rel_path, content in _POISON_FILES.items():
            _write(root, rel_path, content)


def _config(*, slug: str, live_path: Path) -> LoreConfig:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
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
    return f"test_{uuid.uuid4().hex}"


def _make_indexer(
    *, config: LoreConfig, trio: FakeSurrealTrio, embedder: Embedder, snapshot_root: Path
) -> Indexer:
    server = LoreServer(config)
    return Indexer(
        store=trio.store,
        embedder=embedder,
        manifest=trio.manifest,
        registry=server.registry,
        source_providers=list(server.source_providers),
        config=config,
        snapshot_root=snapshot_root,
    )


# --------------------------------------------------------------------------- #
# 1. Walk-level isolation — the frames the production crash climbed
# --------------------------------------------------------------------------- #
class TestChunkerFaultIsolationInSweep:
    """A chunker raise fails ONE file; the sweep completes and siblings index."""

    async def test_sweep_over_poisoned_tree_completes_and_isolates_each_bad_file(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )

        # RED before 0a90687: the ParseError propagated out of index_all instead of returning.
        summary = await indexer.index_all()

        assert summary.files_failed == len(_POISON_FILES)
        assert summary.files_indexed == len(_HEALTHY_FILES)

        for rel_path in _POISON_FILES:
            row = await trio.manifest.get("custom", rel_path)
            assert row is not None, f"{rel_path} must have a committed manifest row"
            assert row.state == STATE_FAILED, f"{rel_path} must be failed"
            assert row.n_chunks == 0, f"{rel_path} must have zero chunks committed"

        for rel_path in _HEALTHY_FILES:
            row = await trio.manifest.get("custom", rel_path)
            assert row is not None and row.state == STATE_INDEXED

        # The store holds chunks ONLY for the healthy files.
        assert trio.store.stored_file_paths() == set(_HEALTHY_FILES)

    async def test_chunker_failed_file_never_reaches_the_embedder(self, tmp_path: Path) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        embedder = DualPathRecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )

        await indexer.index_all()

        # The chunk step precedes the embed step: only healthy files embed.
        assert embedder.files_embedded == len(_HEALTHY_FILES)

    async def test_chunker_failure_logs_a_chunker_distinguishable_reason(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )

        with caplog.at_level(logging.WARNING, logger="loremaster.index.indexer"):
            await indexer.index_all()

        failed_events = [r for r in caplog.records if r.message == "index.file.failed"]
        assert {r.file_path for r in failed_events} == set(_POISON_FILES)  # type: ignore[attr-defined]
        for record in failed_events:
            reason: str = record.reason  # type: ignore[attr-defined]
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
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root, poison=False)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )

        outcome = await indexer.index_file("custom", _DUMMY_XML_PATH, _DUMMY_XML_CONTENT)

        assert outcome.state == STATE_FAILED
        assert outcome.n_chunks == 0
        row = await trio.manifest.get("custom", _DUMMY_XML_PATH)
        assert row is not None and row.state == STATE_FAILED
        assert trio.store.stored_file_paths() == set()


# --------------------------------------------------------------------------- #
# 3. Re-attempt + recovery across sweeps
# --------------------------------------------------------------------------- #
class TestChunkerFailureReattemptAndRecovery:
    """Unchanged → stays failed without crashing; fixed → recovers to indexed."""

    async def test_second_sweep_over_unchanged_poison_completes_and_stays_failed(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        embedder = DualPathRecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap",
        )

        await indexer.index_all()
        embedded_after_first = embedder.files_embedded

        second = await indexer.index_all()

        assert second.files_failed == len(_POISON_FILES)
        assert second.files_skipped == len(_HEALTHY_FILES)
        assert embedder.files_embedded == embedded_after_first  # no embed churn
        for rel_path in _POISON_FILES:
            row = await trio.manifest.get("custom", rel_path)
            assert row is not None and row.state == STATE_FAILED

    async def test_failed_file_recovers_to_indexed_once_parseable(self, tmp_path: Path) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _build_odoo_like_corpus(root)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=FakeEmbedder(dim=_DIM), snapshot_root=tmp_path / "snap",
        )
        await indexer.index_all()
        row = await trio.manifest.get("custom", _DUMMY_XML_PATH)
        assert row is not None and row.state == STATE_FAILED  # precondition

        _write(root, _DUMMY_XML_PATH, _RECOVERED_XML_CONTENT)

        recovery = await indexer.index_all()

        row = await trio.manifest.get("custom", _DUMMY_XML_PATH)
        assert row is not None
        assert row.state == STATE_INDEXED
        assert row.n_chunks >= 1
        assert _DUMMY_XML_PATH in trio.store.stored_file_paths()
        assert recovery.files_failed == len(_POISON_FILES) - 1
