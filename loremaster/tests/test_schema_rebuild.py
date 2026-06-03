"""Contract tests for the deterministic embedding-schema fingerprint + async rebuild.

These tests are GROUP A — they define the contract for a feature that does NOT
yet exist. Every test is expected to be RED (fail with AttributeError or
ImportError) until the implementation is written.

The contract under test:
    1. A pure fingerprint function (A1, A2) — deterministic, sensitive to
       embedding-schema fields, blind to unrelated fields.
    2. A pure rebuild-needed decision (A3) — stored-vs-current fingerprint logic.
    3. A force-rebuild operation (A4, A5) — re-embeds all tiers, stamps
       fingerprint ONLY after completion.
    4. index_status surfaces schema fields (A6) — fingerprint + rebuild status
       section visible to a caller during/after rebuild.
    5. Startup wiring (A7) — build_app_context spawns background rebuild when
       fingerprint mismatch; runs normal sync reconcile on a match.

Tests marked ``# offline`` need no Qdrant. Tests marked ``# real-Qdrant`` hit
http://127.0.0.1:16333 and require the QDRANT__SERVICE__API_KEY.

How to run:
    PP=<worktree>/loremaster:<worktree>/loresigil:<worktree>/lorescribe
    cd <worktree>/loremaster
    PYTHONPATH=$PP /home/ejprice/PycharmProjects/lore/.venv/bin/python \\
        -m pytest tests/test_schema_rebuild.py -q -p no:cacheprovider
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Production-canonical imports.  These deliberately reference symbols that do
# NOT yet exist so the suite is RED at collection time for the new module while
# remaining importable itself (lazy import pattern inside each test class).
#
# We import existing production symbols freely — they ground the fixtures in
# the real config/manifest/indexer conventions (clause 5: shared source of truth).
# ---------------------------------------------------------------------------
from loremaster.config import LoreConfig
from loremaster.index.manifest import Manifest
from loremaster.index.indexer import Indexer
from loremaster.server import AppContext, LoreServer, build_app_context
from loremaster.source.local_directory import LocalDirectorySourceProvider
from loremaster.store.qdrant import QdrantStore
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient

# ---------------------------------------------------------------------------
# Production-realistic constants (same values the existing test suite uses,
# derived from test_indexer.py/_config — clause 5: same source of truth).
# ---------------------------------------------------------------------------

# The production embedding dimensionality; all FakeEmbedder fixtures use this.
_DIM = 2048

# Production model identifier used by the real lore.yaml deployments.
_MODEL = "voyageai/voyage-4-nano"
_TOKENIZER = "voyage-4-nano"
_MAX_INPUT_TOKENS = 8192  # tokens, not characters
_TEI_BASE_URL = "http://tei.example:8080"
_TEI_ENDPOINT = "/embed"
_TEI_KEY_ENV = "LORE_TEI_KEY"

# The meta key prefix used for the embedding-schema fingerprint in the manifest.
# Shared constant so tests and impl converge on the same key name (clause 5).
SCHEMA_FINGERPRINT_META_KEY = "embedding_schema_fingerprint"

# The meta key used for the in-progress/done rebuild status blob.
SCHEMA_REBUILD_STATUS_META_KEY = "schema_rebuild_status"

# Expected EMBEDDING_SCHEMA_VERSION at the time this contract was written.
# If the implementation starts at a different integer, the test name will guide
# the implementer: the contract says "start at 1".
EXPECTED_SCHEMA_VERSION: int = 1


# ---------------------------------------------------------------------------
# Shared corpus + config builders (mirroring the production-realistic helpers
# from test_reconcile.py / test_indexer.py — clause 5: same builder style).
# ---------------------------------------------------------------------------

def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# A real Python module the python_ast chunker splits into multiple chunks.
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
    """Realistic live tree — same shape as the reconcile/indexer suites."""
    _write(root / "src" / "widget.py", _PY_MODULE)
    _write(root / "src" / "routing.py", _PY_MODULE_2)
    _write(root / "README.md", "# Project\n\nSome docs.\n")
    # Excluded glob — must NOT be indexed.
    _write(root / "src" / "bundle.min.js", "var x=1;")
    # Pruned dir — must never be descended.
    _write(root / ".git" / "config.py", "SECRET = 'do-not-index'\n")


def _slug() -> str:
    return f"test_{uuid.uuid4().hex}"


def _config(
    *,
    slug: str,
    live_path: Path,
    model: str = _MODEL,
    dim: int = _DIM,
    endpoint: str = _TEI_ENDPOINT,
    max_input_tokens: int = _MAX_INPUT_TOKENS,
    tokenizer: str = _TOKENIZER,
    truncate: bool = False,
    query_prompt_name: str | None = None,
    document_prompt_name: str | None = None,
    chunkers: dict[str, Any] | None = None,
    concurrency: int = 2,
    server_port: int = 9201,
    qdrant_url: str = "http://127.0.0.1:16333",
) -> LoreConfig:
    """Build a validated :class:`LoreConfig` grounded in production-realistic values.

    Parameters correspond 1-to-1 with the embedding-schema fingerprint fields so
    tests can vary exactly one field at a time (A2 sensitivity checks).
    Unrelated fields (concurrency, server_port, qdrant_url) are also parameterised
    so the insensitivity checks are explicit (A2 negative cases).
    """
    if chunkers is None:
        chunkers = {".py": {"chunker": "python_ast"}, ".md": {"chunker": "markdown"}}
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": _TEI_BASE_URL,
            "endpoint": endpoint,
            "model": model,
            "dim": dim,
            "truncate": truncate,
            "max_input_tokens": max_input_tokens,
            "max_batch_texts": 32,
            "concurrency": concurrency,       # NOT in fingerprint
            "connect_timeout_s": 5,
            "api_key_env": _TEI_KEY_ENV,
            "tokenizer": tokenizer,
        },
        "qdrant": {"url": qdrant_url, "api_key_env": "QDRANT__SERVICE__API_KEY"},
        "roots": [
            {
                "tier": "custom",
                "watch": "live",
                "path": str(live_path),
                "include": ["**/*.py", "**/*.md"],
                "exclude": ["**/*.min.js"],
            }
        ],
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": ["**/*.min.js"],
        "chunkers": chunkers,
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": server_port},
    }
    if query_prompt_name is not None:
        payload["embedding"]["query_prompt_name"] = query_prompt_name
    if document_prompt_name is not None:
        payload["embedding"]["document_prompt_name"] = document_prompt_name
    return LoreConfig.model_validate(payload)


# ---------------------------------------------------------------------------
# RecordingEmbedder — identical to test_reconcile.py / test_indexer.py so
# the rebuild assertion can prove actual re-embedding (clause 3: seam coverage).
# ---------------------------------------------------------------------------
class RecordingEmbedder(FakeEmbedder):
    """A :class:`FakeEmbedder` that records every ``embed_documents`` call.

    Used to prove that ``rebuild_all()`` ACTUALLY re-embeds chunks, not just
    shuffles manifest rows. The oracle is ``total_embedded`` after the rebuild
    vs. after the initial index.
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


# ---------------------------------------------------------------------------
# Qdrant fixture — exact-name teardown, same pattern as test_indexer.py
# (clause 5: reuse the production fixture convention).
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def store_factory() -> AsyncIterator[Any]:
    """Build QdrantStore instances with concurrency-safe exact-name teardown."""
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
    embedder: Any,
    manifest: Manifest,
    snapshot_root: Path,
) -> Indexer:
    """Wire an Indexer exactly as the CLI/server does (mirrors test_indexer.py)."""
    server = LoreServer(config)
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


# ===========================================================================
# A1 — Fingerprint determinism (offline)
# ===========================================================================
class TestFingerprintDeterminism:
    """``embedding_schema_fingerprint(config)`` is deterministic across calls.

    Two calls with the same config must return the identical hex string —
    regardless of call order, process restart, or dict iteration order.
    """

    def test_same_config_returns_identical_fingerprint_across_two_calls(
        self, tmp_path: Path
    ) -> None:
        """Arrange: build a config with production-realistic values.
        Act: call the fingerprint function twice.
        Assert: the results are identical (deterministic, not random).
        """
        # offline — no Qdrant needed
        from loremaster.index.schema import (  # type: ignore[import-not-found]
            EMBEDDING_SCHEMA_VERSION,
            embedding_schema_fingerprint,
        )

        config = _config(slug=_slug(), live_path=tmp_path / "live")
        first = embedding_schema_fingerprint(config)
        second = embedding_schema_fingerprint(config)

        assert first == second, (
            "fingerprint must be deterministic: same config → same hash across calls"
        )

    def test_fingerprint_is_a_64_char_hex_string(self, tmp_path: Path) -> None:
        """The fingerprint is a SHA-256 hex digest: exactly 64 lowercase hex chars."""
        # offline
        from loremaster.index.schema import (  # type: ignore[import-not-found]
            embedding_schema_fingerprint,
        )

        config = _config(slug=_slug(), live_path=tmp_path / "live")
        fp = embedding_schema_fingerprint(config)

        assert isinstance(fp, str), "fingerprint must be a str"
        assert len(fp) == 64, f"SHA-256 hex is 64 chars, got {len(fp)}"
        assert all(c in "0123456789abcdef" for c in fp), (
            "fingerprint must be lowercase hex (sha256)"
        )

    def test_embedding_schema_version_is_positive_integer(self) -> None:
        """EMBEDDING_SCHEMA_VERSION is a positive integer (spec says start at 1)."""
        # offline
        from loremaster.index.schema import (  # type: ignore[import-not-found]
            EMBEDDING_SCHEMA_VERSION,
        )

        assert isinstance(EMBEDDING_SCHEMA_VERSION, int)
        assert EMBEDDING_SCHEMA_VERSION >= 1, (
            f"spec says start at 1, got {EMBEDDING_SCHEMA_VERSION}"
        )
        # Pin to the contract value so a future bump is a deliberate, visible change.
        assert EMBEDDING_SCHEMA_VERSION == EXPECTED_SCHEMA_VERSION


# ===========================================================================
# A2 — Fingerprint sensitivity (offline)
# ===========================================================================
class TestFingerprintSensitivity:
    """The fingerprint changes on schema-relevant fields; is stable on unrelated ones.

    Schema-relevant (must flip): backend, model, dim, endpoint, max_input_tokens,
    tokenizer, truncate, query_prompt_name, document_prompt_name, chunkers.

    Unrelated (must NOT flip): concurrency, server.port, qdrant.url.

    One test per variation so a single regression failure points to the exact field.
    """

    def _base_fp(self, tmp_path: Path) -> str:
        """Baseline fingerprint from the production-canonical config."""
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        return embedding_schema_fingerprint(
            _config(slug="baseline", live_path=tmp_path / "live")
        )

    # -- schema-relevant fields: each MUST change the fingerprint ---------------

    def test_model_change_flips_fingerprint(self, tmp_path: Path) -> None:
        """model field is in fingerprint scope."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)
        # Use a different model that would have a different embedding space.
        changed = embedding_schema_fingerprint(
            _config(slug="changed", live_path=tmp_path / "live", model="voyageai/voyage-3")
        )
        assert changed != baseline, "changing model must flip the fingerprint"

    def test_dim_change_flips_fingerprint(self, tmp_path: Path) -> None:
        """dim field is in fingerprint scope."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)
        # 1024 is a real production dim for smaller models.
        changed = embedding_schema_fingerprint(
            _config(slug="changed", live_path=tmp_path / "live", dim=1024)
        )
        assert changed != baseline, "changing dim must flip the fingerprint"

    def test_query_prompt_name_change_flips_fingerprint(self, tmp_path: Path) -> None:
        """query_prompt_name field is in fingerprint scope."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)  # query_prompt_name=None
        changed = embedding_schema_fingerprint(
            _config(
                slug="changed",
                live_path=tmp_path / "live",
                query_prompt_name="query",
            )
        )
        assert changed != baseline, "adding query_prompt_name must flip the fingerprint"

    def test_document_prompt_name_change_flips_fingerprint(self, tmp_path: Path) -> None:
        """document_prompt_name field is in fingerprint scope."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)  # document_prompt_name=None
        changed = embedding_schema_fingerprint(
            _config(
                slug="changed",
                live_path=tmp_path / "live",
                document_prompt_name="passage",
            )
        )
        assert changed != baseline, "adding document_prompt_name must flip the fingerprint"

    def test_tokenizer_change_flips_fingerprint(self, tmp_path: Path) -> None:
        """tokenizer field is in fingerprint scope (determines chunk boundaries)."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)
        changed = embedding_schema_fingerprint(
            _config(
                slug="changed",
                live_path=tmp_path / "live",
                tokenizer="cl100k_base",  # a real alternative tokenizer
            )
        )
        assert changed != baseline, "changing tokenizer must flip the fingerprint"

    def test_max_input_tokens_change_flips_fingerprint(self, tmp_path: Path) -> None:
        """max_input_tokens field is in fingerprint scope (affects chunk size)."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)
        # 4096 is a realistic alternative cap (some models support only half the max).
        changed = embedding_schema_fingerprint(
            _config(
                slug="changed",
                live_path=tmp_path / "live",
                max_input_tokens=4096,
            )
        )
        assert changed != baseline, "changing max_input_tokens must flip the fingerprint"

    def test_truncate_change_flips_fingerprint(self, tmp_path: Path) -> None:
        """truncate field is in fingerprint scope (changes over-limit behaviour)."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)  # truncate=False (production default)
        changed = embedding_schema_fingerprint(
            _config(slug="changed", live_path=tmp_path / "live", truncate=True)
        )
        assert changed != baseline, "changing truncate must flip the fingerprint"

    def test_endpoint_change_flips_fingerprint(self, tmp_path: Path) -> None:
        """endpoint field is in fingerprint scope (different endpoint → different model)."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)
        changed = embedding_schema_fingerprint(
            _config(
                slug="changed",
                live_path=tmp_path / "live",
                endpoint="/embed-en-q",
            )
        )
        assert changed != baseline, "changing endpoint must flip the fingerprint"

    def test_chunkers_change_flips_fingerprint(self, tmp_path: Path) -> None:
        """chunkers mapping is in fingerprint scope (different chunker → different boundaries)."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)
        # Remove the markdown chunker — a realistic config variation.
        changed = embedding_schema_fingerprint(
            _config(
                slug="changed",
                live_path=tmp_path / "live",
                chunkers={".py": {"chunker": "python_ast"}},
            )
        )
        assert changed != baseline, "changing chunkers must flip the fingerprint"

    def test_chunker_type_change_within_extension_flips_fingerprint(
        self, tmp_path: Path
    ) -> None:
        """Changing the chunker value for an existing extension flips the fingerprint."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)
        # Switch .py from python_ast to a hypothetical plain-text chunker.
        changed = embedding_schema_fingerprint(
            _config(
                slug="changed",
                live_path=tmp_path / "live",
                chunkers={
                    ".py": {"chunker": "plain_text"},
                    ".md": {"chunker": "markdown"},
                },
            )
        )
        assert changed != baseline, "changing a chunker type must flip the fingerprint"

    # -- unrelated fields: must NOT change the fingerprint ---------------------

    def test_concurrency_change_does_not_flip_fingerprint(self, tmp_path: Path) -> None:
        """concurrency is a runtime-only field; it does NOT affect stored vectors."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)
        # concurrency=8 vs. baseline=2 — purely a throughput knob.
        unchanged = embedding_schema_fingerprint(
            _config(slug="unchanged", live_path=tmp_path / "live", concurrency=8)
        )
        assert unchanged == baseline, (
            "changing concurrency must NOT flip the fingerprint "
            "(it does not affect stored vectors or chunk boundaries)"
        )

    def test_server_port_change_does_not_flip_fingerprint(self, tmp_path: Path) -> None:
        """server.port is purely a network binding; it does NOT affect stored vectors."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)
        unchanged = embedding_schema_fingerprint(
            _config(slug="unchanged", live_path=tmp_path / "live", server_port=9999)
        )
        assert unchanged == baseline, (
            "changing server.port must NOT flip the fingerprint"
        )

    def test_qdrant_url_change_does_not_flip_fingerprint(self, tmp_path: Path) -> None:
        """qdrant.url is a connection detail; it does NOT affect the embedding schema."""
        # offline
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        baseline = self._base_fp(tmp_path)
        unchanged = embedding_schema_fingerprint(
            _config(
                slug="unchanged",
                live_path=tmp_path / "live",
                qdrant_url="http://10.0.0.1:6333",
            )
        )
        assert unchanged == baseline, (
            "changing qdrant.url must NOT flip the fingerprint"
        )


# ===========================================================================
# A3 — Rebuild-needed decision (offline)
# ===========================================================================
class TestRebuildNeededDecision:
    """``rebuild_needed(stored, current) -> bool`` — pure three-case logic.

    Contract:
        * (None, X)  → True  (provenance unknown → fail safe toward correctness)
        * (X, X)     → False (fingerprints match → no rebuild)
        * (X, Y)     → True  (fingerprints differ → rebuild)

    The function is pure; no Qdrant, no filesystem.
    """

    def test_none_stored_means_rebuild_needed(self) -> None:
        """stored=None → rebuild (provenance unknown, fail safe)."""
        # offline
        from loremaster.index.schema import rebuild_needed  # type: ignore[import-not-found]

        # Use a realistic hex string (same length as an actual fingerprint).
        current_fp = "a" * 64
        assert rebuild_needed(stored=None, current=current_fp) is True

    def test_matching_fingerprints_means_no_rebuild(self) -> None:
        """stored == current → no rebuild needed."""
        # offline
        from loremaster.index.schema import rebuild_needed  # type: ignore[import-not-found]

        same_fp = "b" * 64  # realistic 64-char hex string
        assert rebuild_needed(stored=same_fp, current=same_fp) is False

    def test_differing_fingerprints_means_rebuild_needed(self) -> None:
        """stored != current → rebuild needed."""
        # offline
        from loremaster.index.schema import rebuild_needed  # type: ignore[import-not-found]

        old_fp = "a" * 64
        new_fp = "b" * 64
        assert rebuild_needed(stored=old_fp, current=new_fp) is True


# ===========================================================================
# A4 — Force rebuild re-embeds all tiers (real Qdrant)
# ===========================================================================
class TestForceRebuildReembeds:
    """``Indexer.rebuild_all()`` (or equivalent) re-embeds every tier from scratch.

    Contract:
        * After a successful initial index, calling rebuild_all() causes EVERY
          file to be re-embedded (proven by RecordingEmbedder.total_embedded
          increasing beyond the baseline by the number of chunks in the corpus).
        * The points are still present in Qdrant after the rebuild (not wiped).
        * The current fingerprint is stamped into the manifest meta AFTER
          completion (the stamp is the evidence the rebuild ran).
    """

    async def test_rebuild_all_reembeds_all_files_and_stamps_fingerprint(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """Arrange: index a live corpus with RecordingEmbedder.
        Act: call rebuild_all() with a fresh RecordingEmbedder.
        Assert: new embedder's total_embedded >= baseline; points present; stamp set.
        """
        # real-Qdrant
        from loremaster.index.schema import (  # type: ignore[import-not-found]
            embedding_schema_fingerprint,
        )

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))

        # Step 1: initial index (baseline embeds).
        initial_embedder = RecordingEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=initial_embedder,
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        await indexer.index_all()
        baseline_embedded = initial_embedder.total_embedded
        # Sanity: the real corpus produced at least 3 chunks (multiple files).
        assert baseline_embedded >= 3, (
            f"baseline_embedded={baseline_embedded} — corpus too small to test rebuild"
        )

        # Step 2: rebuild_all() with a FRESH RecordingEmbedder (zero prior state).
        rebuild_embedder = RecordingEmbedder(dim=_DIM)
        rebuild_indexer = _make_indexer(
            config=config, store=store, embedder=rebuild_embedder,
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        await rebuild_indexer.rebuild_all(  # type: ignore[attr-defined]
            fingerprint=embedding_schema_fingerprint(config)
        )

        # The rebuild actually re-embedded (not a no-op fast-path skip).
        assert rebuild_embedder.total_embedded >= baseline_embedded, (
            f"rebuild_all must re-embed at least as many chunks as the initial index "
            f"(got {rebuild_embedder.total_embedded}, expected >= {baseline_embedded})"
        )

        # Points are still present in Qdrant (rebuild doesn't leave the index empty).
        hits = await store.search([0.0] * _DIM, k=500)
        landed_paths = {
            h.payload["file_path"] for h in hits if h.payload is not None
        }
        assert "src/widget.py" in landed_paths, (
            "widget.py must be present in Qdrant after rebuild_all"
        )
        assert "src/routing.py" in landed_paths, (
            "routing.py must be present in Qdrant after rebuild_all"
        )

        # The fingerprint is stamped into the manifest meta.
        stored_fp = manifest.meta_get(SCHEMA_FINGERPRINT_META_KEY)
        expected_fp = embedding_schema_fingerprint(config)
        assert stored_fp == expected_fp, (
            f"rebuild_all must stamp the current fingerprint into manifest meta "
            f"under key '{SCHEMA_FINGERPRINT_META_KEY}'"
        )

        # Sanity bound: the fingerprint is a 64-char hex string (clause 4).
        assert stored_fp is not None and len(stored_fp) == 64


# ===========================================================================
# A5 — Fingerprint stamped ONLY after completion (offline + real-Qdrant)
# ===========================================================================
class TestFingerprintStampedOnlyAfterCompletion:
    """The embedding-schema fingerprint is NOT stamped before rebuild_all completes.

    Crash-safety contract:
        * Before rebuild_all() runs, the stamp is absent (or holds the old value).
        * After rebuild_all() completes successfully, the stamp equals the current fp.
        * A rebuild that raises mid-way leaves the stamp unchanged so the NEXT
          startup re-triggers the rebuild (fail safe).

    The mid-raise case is tested with a controlled synthetic failure: an embedder
    that raises on the second file, so the first file's new vectors are written
    but the stamp is NOT set (the stamp comes after all files succeed).
    """

    def test_stamp_absent_before_rebuild_all_is_called(
        self, tmp_path: Path
    ) -> None:
        """A fresh manifest has no fingerprint stamp — trivially correct."""
        # offline
        manifest = Manifest(str(tmp_path / "m.db"))
        stored = manifest.meta_get(SCHEMA_FINGERPRINT_META_KEY)
        assert stored is None, (
            "a fresh manifest must have no fingerprint stamp before any rebuild"
        )

    async def test_stamp_set_after_successful_rebuild_all(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """rebuild_all() sets the stamp on success — the completion evidence."""
        # real-Qdrant
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

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

        # The stamp is absent before the rebuild.
        assert manifest.meta_get(SCHEMA_FINGERPRINT_META_KEY) is None

        current_fp = embedding_schema_fingerprint(config)
        await indexer.rebuild_all(fingerprint=current_fp)  # type: ignore[attr-defined]

        # The stamp is set after completion.
        assert manifest.meta_get(SCHEMA_FINGERPRINT_META_KEY) == current_fp

    async def test_stamp_not_set_when_rebuild_all_raises_midway(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """If rebuild_all() raises, the old/absent stamp survives so the next start re-triggers.

        We simulate this by planting a previously-stamped OLD fingerprint, then
        running rebuild_all() with an embedder whose second batch raises. The
        stamp must still hold the OLD value (not the new one) so the restart
        logic detects a mismatch and tries again.
        """
        # real-Qdrant
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))

        # Plant an "old" fingerprint as if a prior schema was in place.
        old_fp = "0" * 64  # a realistic-length but distinct hex fingerprint
        manifest.meta_set(SCHEMA_FINGERPRINT_META_KEY, old_fp)

        current_fp = embedding_schema_fingerprint(config)
        assert current_fp != old_fp, "test setup: current and old must differ"

        # An embedder that raises on the first embed call — guarantees the rebuild
        # fails before stamping (which happens only after ALL files succeed).
        class BombEmbedder(FakeEmbedder):
            async def embed_documents(self, texts: list[str]) -> Any:
                raise RuntimeError("simulated mid-rebuild embedder failure")

        bomb_indexer = _make_indexer(
            config=config, store=store, embedder=BombEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )

        with pytest.raises(Exception):  # any exception from the failing embedder
            await bomb_indexer.rebuild_all(fingerprint=current_fp)  # type: ignore[attr-defined]

        # The stamp must still hold the OLD fingerprint (not the new one).
        after_raise = manifest.meta_get(SCHEMA_FINGERPRINT_META_KEY)
        assert after_raise == old_fp, (
            f"a failed rebuild must NOT update the fingerprint stamp "
            f"(got {after_raise!r}, expected {old_fp!r})"
        )


# ===========================================================================
# A6 — index_status reports schema fields (offline / manifest-level)
# ===========================================================================
class TestIndexStatusReportsSchemaFields:
    """``AppContext.index_status()`` surfaces the embedding schema fingerprint
    and a schema-rebuild status section.

    The contract specifies the OUTPUT SHAPE — we construct the manifest state
    that would exist during/after a rebuild, then assert the tool's return
    value includes the required fields. This is a seam test: we pre-populate
    the manifest meta keys that the (not-yet-built) implementation will read,
    and verify the tool surfaces them correctly.

    Required output fields:
        embedding_schema.fingerprint: str (the hex hash)
        embedding_schema.version: int (the EMBEDDING_SCHEMA_VERSION constant)
        schema_rebuild.state: "idle" | "in_progress" | "done"
        schema_rebuild.done: int (files completed so far)
        schema_rebuild.total: int (total files to re-embed)
        schema_rebuild.reason: str (why rebuild was triggered)
        schema_rebuild.from_fingerprint: str | None
        schema_rebuild.to_fingerprint: str | None
    """

    async def test_index_status_includes_embedding_schema_fingerprint(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """With a fingerprint stamped in the manifest, index_status includes it."""
        # real-Qdrant (needs AppContext.index_status() which needs the store)
        from loremaster.index.schema import (  # type: ignore[import-not-found]
            EMBEDDING_SCHEMA_VERSION,
            embedding_schema_fingerprint,
        )
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)

        # Build the full AppContext (same seam test_mcp_server.py uses).
        qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        try:
            current_fp = embedding_schema_fingerprint(config)
            # Pre-stamp the fingerprint as if a rebuild completed.
            manifest_path = tmp_path / "m.db"
            manifest = Manifest(str(manifest_path))
            manifest.meta_set(SCHEMA_FINGERPRINT_META_KEY, current_fp)
            manifest.close()

            # Register the collection for teardown.
            created_collections = [f"lore_{slug}", f"lore_{slug}_memory"]

            app_ctx = await build_app_context(
                server=LoreServer(config),
                embedder=FakeEmbedder(dim=_DIM),
                qdrant_client=qdrant_client,
                manifest_path=manifest_path,
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=False,
            )

            status = await app_ctx.index_status()

            # The status must carry the embedding_schema section.
            assert hasattr(status, "embedding_schema"), (
                "index_status() result must have an 'embedding_schema' attribute"
            )
            assert status.embedding_schema.fingerprint == current_fp  # type: ignore[union-attr]
            assert status.embedding_schema.version == EMBEDDING_SCHEMA_VERSION  # type: ignore[union-attr]

        finally:
            for name in created_collections:
                if await qdrant_client.collection_exists(name):
                    await qdrant_client.delete_collection(name)
            await qdrant_client.close()

    async def test_index_status_includes_schema_rebuild_status_when_in_progress(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """With an in_progress rebuild status in the manifest, index_status surfaces it."""
        # real-Qdrant
        import json

        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)

        old_fp = "1" * 64
        current_fp = embedding_schema_fingerprint(config)

        # Pre-populate the rebuild status as if a background rebuild started.
        manifest_path = tmp_path / "m.db"
        manifest = Manifest(str(manifest_path))
        rebuild_status_payload = json.dumps({
            "state": "in_progress",
            "done": 2,
            "total": 5,
            "reason": "fingerprint_mismatch",
            "from_fingerprint": old_fp,
            "to_fingerprint": current_fp,
        })
        manifest.meta_set(SCHEMA_REBUILD_STATUS_META_KEY, rebuild_status_payload)
        manifest.close()

        qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        created_collections = [f"lore_{slug}", f"lore_{slug}_memory"]
        try:
            app_ctx = await build_app_context(
                server=LoreServer(config),
                embedder=FakeEmbedder(dim=_DIM),
                qdrant_client=qdrant_client,
                manifest_path=manifest_path,
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=False,
            )

            status = await app_ctx.index_status()

            assert hasattr(status, "schema_rebuild"), (
                "index_status() result must have a 'schema_rebuild' attribute"
            )
            rebuild = status.schema_rebuild  # type: ignore[union-attr]
            assert rebuild.state == "in_progress"
            assert rebuild.done == 2
            assert rebuild.total == 5
            assert rebuild.reason == "fingerprint_mismatch"
            assert rebuild.from_fingerprint == old_fp
            assert rebuild.to_fingerprint == current_fp

            # Sanity bound: done and total are non-negative, done <= total (clause 4).
            assert 0 <= rebuild.done <= rebuild.total

        finally:
            for name in created_collections:
                if await qdrant_client.collection_exists(name):
                    await qdrant_client.delete_collection(name)
            await qdrant_client.close()

    async def test_index_status_schema_rebuild_idle_when_no_status_in_manifest(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """With no rebuild status in manifest, schema_rebuild.state is 'idle'."""
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)

        qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        created_collections = [f"lore_{slug}", f"lore_{slug}_memory"]
        try:
            app_ctx = await build_app_context(
                server=LoreServer(config),
                embedder=FakeEmbedder(dim=_DIM),
                qdrant_client=qdrant_client,
                manifest_path=tmp_path / "m.db",
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=False,
            )

            status = await app_ctx.index_status()

            assert hasattr(status, "schema_rebuild"), (
                "index_status() result must have a 'schema_rebuild' attribute"
            )
            assert status.schema_rebuild.state == "idle"  # type: ignore[union-attr]

        finally:
            for name in created_collections:
                if await qdrant_client.collection_exists(name):
                    await qdrant_client.delete_collection(name)
            await qdrant_client.close()


# ===========================================================================
# A7 — Startup decision: spawn vs. sync reconcile (seam test)
# ===========================================================================
class TestStartupDecision:
    """build_app_context spawns background rebuild on fingerprint mismatch;
    runs normal sync reconcile on a fingerprint match.

    Design rationale for the seam:
        The background coroutine is named ``_run_schema_rebuild`` and must be
        spawned via ``asyncio.create_task()``. We assert the DECISION (status
        flips to in_progress, task is created) rather than waiting out a full
        re-embed — the full embed is covered by A4; here we prove the startup
        WIRING fires the right branch.

        We test via ``build_app_context`` with ``start_tasks=False`` so we get
        the watcher-free path, but the fingerprint decision must still run before
        the initial reconcile. The background rebuild task is accessible via
        ``AppContext.schema_rebuild_task`` (the contract name we define).
    """

    async def test_fingerprint_mismatch_spawns_background_rebuild_task(
        self, tmp_path: Path
    ) -> None:
        """Arrange: manifest has an OLD fingerprint != current config fingerprint.
        Act: build_app_context (start_tasks=False).
        Assert: AppContext.schema_rebuild_task is NOT None (a task was created),
                schema_rebuild status in manifest is 'in_progress'.
        """
        # real-Qdrant (needs collection creation)
        import json

        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)

        # Plant a DIFFERENT old fingerprint into the manifest.
        manifest_path = tmp_path / "m.db"
        manifest = Manifest(str(manifest_path))
        old_fp = "c" * 64  # 64-char hex, distinct from the current fp
        manifest.meta_set(SCHEMA_FINGERPRINT_META_KEY, old_fp)
        current_fp = embedding_schema_fingerprint(config)
        # Make sure our planted old_fp actually differs (sanity).
        assert old_fp != current_fp
        manifest.close()

        qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        created_collections = [f"lore_{slug}", f"lore_{slug}_memory"]
        try:
            app_ctx = await build_app_context(
                server=LoreServer(config),
                embedder=FakeEmbedder(dim=_DIM),
                qdrant_client=qdrant_client,
                manifest_path=manifest_path,
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=False,
            )

            # The startup must have SPAWNED a background rebuild task.
            assert hasattr(app_ctx, "schema_rebuild_task"), (
                "AppContext must expose 'schema_rebuild_task' so callers can "
                "verify the spawn happened"
            )
            assert app_ctx.schema_rebuild_task is not None, (  # type: ignore[union-attr]
                "build_app_context must create a background rebuild task when "
                "the stored fingerprint differs from the current one"
            )
            assert isinstance(app_ctx.schema_rebuild_task, asyncio.Task), (  # type: ignore[union-attr]
                "schema_rebuild_task must be an asyncio.Task (created via create_task)"
            )

            # The manifest status must have flipped to in_progress (set BEFORE
            # the background task runs, so the server can report it immediately).
            reread = Manifest(str(manifest_path))
            raw_status = reread.meta_get(SCHEMA_REBUILD_STATUS_META_KEY)
            assert raw_status is not None, (
                "manifest must hold a schema_rebuild_status meta key after startup "
                "detects a fingerprint mismatch"
            )
            status_blob = json.loads(raw_status)
            assert status_blob["state"] == "in_progress", (
                f"schema_rebuild_status.state must be 'in_progress' immediately after "
                f"build_app_context spawns the rebuild; got {status_blob['state']!r}"
            )
            assert status_blob.get("from_fingerprint") == old_fp
            assert status_blob.get("to_fingerprint") == current_fp

            # Cancel the task so it doesn't run past the test boundary.
            app_ctx.schema_rebuild_task.cancel()  # type: ignore[union-attr]
            try:
                await app_ctx.schema_rebuild_task  # type: ignore[union-attr]
            except (asyncio.CancelledError, Exception):
                pass

        finally:
            for name in created_collections:
                if await qdrant_client.collection_exists(name):
                    await qdrant_client.delete_collection(name)
            await qdrant_client.close()

    async def test_matching_fingerprint_does_not_spawn_rebuild_task(
        self, tmp_path: Path
    ) -> None:
        """Arrange: manifest fingerprint == current config fingerprint.
        Act: build_app_context (start_tasks=False).
        Assert: schema_rebuild_task is None (no rebuild spawned).
        """
        # real-Qdrant
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)

        # Pre-stamp the CURRENT fingerprint (matching — no rebuild needed).
        manifest_path = tmp_path / "m.db"
        manifest = Manifest(str(manifest_path))
        current_fp = embedding_schema_fingerprint(config)
        manifest.meta_set(SCHEMA_FINGERPRINT_META_KEY, current_fp)
        manifest.close()

        qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        created_collections = [f"lore_{slug}", f"lore_{slug}_memory"]
        try:
            app_ctx = await build_app_context(
                server=LoreServer(config),
                embedder=FakeEmbedder(dim=_DIM),
                qdrant_client=qdrant_client,
                manifest_path=manifest_path,
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=False,
            )

            # Matching fingerprint → no background rebuild task.
            schema_rebuild_task = getattr(app_ctx, "schema_rebuild_task", None)
            assert schema_rebuild_task is None, (
                "build_app_context must NOT spawn a rebuild task when the "
                "fingerprint matches (no rebuild needed)"
            )

        finally:
            for name in created_collections:
                if await qdrant_client.collection_exists(name):
                    await qdrant_client.delete_collection(name)
            await qdrant_client.close()

    async def test_missing_stored_fingerprint_spawns_rebuild_task(
        self, tmp_path: Path
    ) -> None:
        """Arrange: manifest has NO fingerprint (fresh deploy or legacy index).
        Act: build_app_context (start_tasks=False).
        Assert: schema_rebuild_task is created (None stored → rebuild, fail safe).
        """
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        # manifest_path is a fresh file — no fingerprint stamped.

        qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        created_collections = [f"lore_{slug}", f"lore_{slug}_memory"]
        try:
            app_ctx = await build_app_context(
                server=LoreServer(config),
                embedder=FakeEmbedder(dim=_DIM),
                qdrant_client=qdrant_client,
                manifest_path=tmp_path / "m.db",
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=False,
            )

            assert hasattr(app_ctx, "schema_rebuild_task"), (
                "AppContext must expose 'schema_rebuild_task'"
            )
            assert app_ctx.schema_rebuild_task is not None, (  # type: ignore[union-attr]
                "a missing fingerprint must trigger a background rebuild task "
                "(provenance unknown → fail safe toward correctness)"
            )

            # Cancel the task so it doesn't run past the test boundary.
            app_ctx.schema_rebuild_task.cancel()  # type: ignore[union-attr]
            try:
                await app_ctx.schema_rebuild_task  # type: ignore[union-attr]
            except (asyncio.CancelledError, Exception):
                pass

        finally:
            for name in created_collections:
                if await qdrant_client.collection_exists(name):
                    await qdrant_client.delete_collection(name)
            await qdrant_client.close()

    async def test_prod_path_missing_fp_over_populated_index_rebuilds_not_silent_stamp(
        self, tmp_path: Path
    ) -> None:
        """Fix #1: missing fingerprint over a NON-EMPTY index must REBUILD, not silent-stamp.

        The prod path (``start_tasks=True``) runs the initial delta sweep, which
        FAST-PATH-SKIPS unchanged files (no re-embed). For a legacy / pre-feature
        index — populated manifest rows + Qdrant points, but NO fingerprint stamp
        (unknown provenance) — the sweep re-embeds nothing, so the stored vectors
        are NOT proven to be the current schema. Stamping the current fingerprint
        after that no-op sweep would MASK a needed rebuild (the bug). The fail-safe:
        provenance-unknown over a non-empty index → trigger a rebuild.

        Arrange: index a real corpus (manifest rows + store points), then DELETE
                 the fingerprint meta key to simulate the legacy/unknown-provenance
                 index.
        Act: build_app_context(start_tasks=True) — the PROD path with the sweep +
             stamp logic.
        Assert: a rebuild IS triggered (a schema_rebuild_task spawned OR the
                rebuild status flips to in_progress) AND the feature did NOT
                silently stamp-without-rebuilding (if no task was spawned, the
                fingerprint must remain unstamped — a populated-unstamped index is
                never treated as current).
        """
        # real-Qdrant
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"

        qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        created_collections = [f"lore_{slug}", f"lore_{slug}_memory"]
        app_ctx: Any = None
        try:
            # Step 1: build the index for real (start_tasks=False) so the manifest
            # has indexed rows and Qdrant has points — a POPULATED index.
            seed_ctx = await build_app_context(
                server=LoreServer(config),
                embedder=FakeEmbedder(dim=_DIM),
                qdrant_client=qdrant_client,
                manifest_path=manifest_path,
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=False,
            )
            # Settle and tear down anything the first build spawned; the first build
            # over a fresh manifest spawns a rebuild (missing fp), which we drain so
            # it does not interfere — we then DELETE the stamp to simulate a legacy
            # index whose provenance is unknown.
            await seed_ctx.reindex(None)  # bring everything current under the lock
            seed_status = await seed_ctx.index_status()
            assert seed_status.files_indexed >= 1, (
                "the seed build must populate the manifest with indexed rows"
            )
            await seed_ctx.aclose()

            # Step 2: REMOVE the fingerprint stamp entirely → legacy / pre-feature
            # index whose provenance is unknown (manifest rows + points present, no
            # stamp). meta_set cannot delete, so drop the row via the manifest's real
            # SQLite ``meta`` table (k TEXT PK) — grounding the fixture in the actual
            # DB the production code reads, not a hand-faked stand-in.
            manifest = Manifest(str(manifest_path))
            with manifest._connection:  # type: ignore[attr-defined]
                manifest._connection.execute(  # type: ignore[attr-defined]
                    "DELETE FROM meta WHERE k = ?", (SCHEMA_FINGERPRINT_META_KEY,)
                )
            stored_before = manifest.meta_get(SCHEMA_FINGERPRINT_META_KEY)
            indexed_rows = len(manifest.all_files())
            manifest.close()
            current_fp = embedding_schema_fingerprint(config)
            # The index is genuinely populated (rows present) but unstamped — the
            # exact legacy/unknown-provenance shape the fail-safe must catch.
            assert stored_before is None, (
                "test setup: the fingerprint stamp must be ABSENT (legacy index)"
            )
            assert indexed_rows >= 1, (
                "test setup: the manifest must still hold the indexed rows (a "
                "populated index), so the delta sweep will fast-path-skip them"
            )

            # Step 3: the PROD path — start_tasks=True runs the initial sweep + the
            # stamp logic + the rebuild decision.
            app_ctx = await build_app_context(
                server=LoreServer(config),
                embedder=FakeEmbedder(dim=_DIM),
                qdrant_client=qdrant_client,
                manifest_path=manifest_path,
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=True,
            )

            # A rebuild must have been triggered: either a task was spawned, or the
            # manifest's rebuild status flipped to in_progress.
            rebuild_task = getattr(app_ctx, "schema_rebuild_task", None)
            reread = Manifest(str(manifest_path))
            raw_status = reread.meta_get(SCHEMA_REBUILD_STATUS_META_KEY)
            stored_fp_after = reread.meta_get(SCHEMA_FINGERPRINT_META_KEY)
            reread.close()
            status_in_progress = False
            if raw_status is not None:
                import json as _json
                try:
                    status_in_progress = _json.loads(raw_status).get("state") == "in_progress"
                except (ValueError, TypeError):
                    status_in_progress = False

            assert rebuild_task is not None or status_in_progress, (
                "a populated-but-unstamped (unknown-provenance) index over the PROD "
                "path must TRIGGER a rebuild — either a schema_rebuild_task is "
                "spawned or the rebuild status flips to in_progress; got "
                f"task={rebuild_task!r}, status_raw={raw_status!r}"
            )

            # CRUCIAL fail-safe: the feature must NOT have silently stamped the
            # CURRENT fingerprint without a rebuild. If no rebuild task was spawned,
            # the stamp must NOT have been set to the current fingerprint (that would
            # mark the un-re-embedded index as 'current' and mask the bug).
            if rebuild_task is None:
                assert stored_fp_after != current_fp, (
                    "a populated-unstamped index must NOT be silently stamped with the "
                    "current fingerprint without a rebuild — that masks a needed "
                    f"re-embed; stamp after startup was {stored_fp_after!r}"
                )

        finally:
            if app_ctx is not None:
                await app_ctx.aclose()
            for name in created_collections:
                if await qdrant_client.collection_exists(name):
                    await qdrant_client.delete_collection(name)
            await qdrant_client.close()

    async def test_prod_path_empty_index_missing_fp_may_stamp_without_separate_rebuild(
        self, tmp_path: Path
    ) -> None:
        """Fix #1 companion: an EMPTY index + missing fp + start_tasks=True may stamp.

        The desirable optimisation the fail-safe must NOT break: a TRULY EMPTY
        index (fresh deploy — no manifest rows, no points) whose initial sweep
        BUILDS everything under the current schema is genuinely current afterwards,
        so stamping the fingerprint after that sweep — with no separate redundant
        background rebuild — is acceptable. This pins that the non-empty fail-safe
        does not regress the empty-index path into a redundant rebuild.

        Arrange: a live root with NO files (empty corpus) and a fresh manifest.
        Act: build_app_context(start_tasks=True).
        Assert: after startup the index is current — the fingerprint IS stamped to
                the current value, and there is no lingering non-terminal rebuild
                (no separate rebuild task left in progress).
        """
        # real-Qdrant
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        live.mkdir(parents=True, exist_ok=True)  # empty live root — no files to index
        config = _config(slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"  # fresh: no fingerprint, no rows

        qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        created_collections = [f"lore_{slug}", f"lore_{slug}_memory"]
        app_ctx: Any = None
        try:
            app_ctx = await build_app_context(
                server=LoreServer(config),
                embedder=FakeEmbedder(dim=_DIM),
                qdrant_client=qdrant_client,
                manifest_path=manifest_path,
                graph_path=tmp_path / "graph.db",
                snapshot_root=tmp_path / "snap",
                start_tasks=True,
            )

            # Settle any spawned task so a clean terminal state is observable.
            rebuild_task = getattr(app_ctx, "schema_rebuild_task", None)
            if rebuild_task is not None:
                try:
                    await rebuild_task
                except Exception:
                    pass

            current_fp = embedding_schema_fingerprint(config)
            reread = Manifest(str(manifest_path))
            stored_fp_after = reread.meta_get(SCHEMA_FINGERPRINT_META_KEY)
            reread.close()

            # An empty index built by the initial sweep is current → the fingerprint
            # is stamped to the current value (whether via the post-sweep stamp or a
            # rebuild that completed). The optimisation is allowed to skip a separate
            # redundant rebuild; either way the END STATE is a current stamp.
            assert stored_fp_after == current_fp, (
                "an empty index built by the initial sweep is genuinely current → "
                "its fingerprint must end stamped to the current value; got "
                f"{stored_fp_after!r}"
            )

        finally:
            if app_ctx is not None:
                await app_ctx.aclose()
            for name in created_collections:
                if await qdrant_client.collection_exists(name):
                    await qdrant_client.delete_collection(name)
            await qdrant_client.close()


# ===========================================================================
# A8 — Empty-reply-during-rebuild notice (the "don't mislead with []" rule)
# ===========================================================================
#
# Shared-seam contract (the helper the implementer wires into ALL SIX corpus
# read tools — search_code, get_symbol, what_imports, blast_radius, tests_for,
# read_file):
#
#     loremaster.index.schema.rebuilding_notice(manifest) -> str | None
#
# Returns a human-readable message (mentioning that the store is REBUILDING and
# the progress, e.g. "done/total") when the manifest's schema_rebuild state is
# "in_progress"; returns None when idle/done. Each read tool calls it ONLY when
# its substantive result would be empty, and surfaces the message in the
# agent-visible reply instead of a bare empty list.
#
# The contract pins OBSERVABLE behavior — the agent-visible text must say the
# store is rebuilding + carry progress. It does NOT mandate the structured shape
# (a notice field vs. a sentinel object vs. text injected into the reply). To
# stay implementation-agnostic while still asserting the observable, the tests
# below assert on the *rendered text* of the reply: a notice message is present
# in the reply's string projection when empty+in_progress, and ABSENT when
# empty+idle. The progress numbers (done/total) planted in the manifest must
# appear in that text.
#
# Scope: corpus-index read tools only. recall_memory / save_memory are OUT of
# scope — the memory collection is a SEPARATE Qdrant collection (``_memory``
# suffix) that the schema rebuild never purges, so a memory read during a
# corpus rebuild is genuinely complete and must NOT carry a rebuilding notice.
# (No A8 case asserts on memory tools by design — scoped out here.)

# The progress numbers planted in the in-progress rebuild status. Named
# constants (not magic literals) so the assertion that the reply MENTIONS the
# progress reads against the same source the manifest was seeded with (clause 5).
_REBUILD_DONE = 3
_REBUILD_TOTAL = 11

# A server-side payload filter that matches NO indexed point, used to force an
# empty search_code result DETERMINISTICALLY. A semantic search with a
# FakeEmbedder has no relevance threshold — it returns the top-k nearest points
# even for a nonsense query — so "query a junk term" does NOT yield an empty
# list. A filter on a file_path that exists nowhere in the corpus DOES (the
# server returns zero candidates regardless of the vector), which is the real
# "substantive result is empty" condition this seam guards.
_NO_MATCH_FILTER: dict[str, str] = {"file_path": "no/such/file/ever_indexed.py"}


def _seed_in_progress_rebuild(manifest_path: Path, *, from_fp: str, to_fp: str) -> None:
    """Seed the manifest meta with an in_progress schema-rebuild status.

    Mirrors exactly the JSON blob ``build_app_context`` writes when it spawns a
    background rebuild (A6/A7), so the read-tool seam sees the same shape it will
    in production (clause 5: same source of truth as the producer).
    """
    import json

    manifest = Manifest(str(manifest_path))
    manifest.meta_set(
        SCHEMA_REBUILD_STATUS_META_KEY,
        json.dumps(
            {
                "state": "in_progress",
                "done": _REBUILD_DONE,
                "total": _REBUILD_TOTAL,
                "reason": "fingerprint_mismatch",
                "from_fingerprint": from_fp,
                "to_fingerprint": to_fp,
            }
        ),
    )
    manifest.close()


def _mentions_rebuilding(text: str) -> bool:
    """True iff ``text`` tells the agent the store is rebuilding (case-insensitive)."""
    lowered = text.lower()
    return "rebuild" in lowered or "re-embed" in lowered or "reindex" in lowered


@pytest_asyncio.fixture()
async def app_context_factory(tmp_path: Path) -> AsyncIterator[Any]:
    """Build a live AppContext over an indexed corpus, with exact-name teardown.

    Yields a builder ``(config, manifest_path) -> AppContext`` so each test can
    seed the manifest (in_progress vs. idle) BEFORE the context is built and the
    read seam reads it. Indexes a real corpus first so the corpus tools have a
    populated graph/store — the EMPTY result then comes from querying a
    nonexistent term/target, not from an unindexed project.
    """
    from conftest import QDRANT_URL, _qdrant_api_key

    qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
    created_collections: list[str] = []

    async def _build(config: LoreConfig, manifest_path: Path) -> Any:
        slug = config.project.slug
        created_collections.extend([f"lore_{slug}", f"lore_{slug}_memory"])
        return await build_app_context(
            server=LoreServer(config),
            embedder=FakeEmbedder(dim=_DIM),
            qdrant_client=qdrant_client,
            manifest_path=manifest_path,
            graph_path=tmp_path / "graph.db",
            snapshot_root=tmp_path / "snap",
            start_tasks=False,
        )

    try:
        yield _build
    finally:
        for name in created_collections:
            if await qdrant_client.collection_exists(name):
                await qdrant_client.delete_collection(name)
        await qdrant_client.close()


class TestRebuildingNoticeSeam:
    """Empty corpus-read result + in_progress rebuild → agent-VISIBLE rebuilding error.

    Pins the shared seam ``rebuilding_notice(manifest)`` AND the SERIALIZATION-ROBUST
    way every corpus read tool surfaces it. When a tool's substantive result would
    be EMPTY and a schema rebuild is in progress, the tool RAISES an error whose
    message says the store is rebuilding AND carries progress (done/total) — NOT a
    bare empty list. Raising is the agent-visible contract because an exception
    propagates through the MCP SDK as a ``ToolError`` the agent SEES; a custom
    attribute on a returned list (e.g. a ``_NoticeList.schema_rebuild_notice``) is
    DROPPED by ``convert_result`` on the wire (the result serialises to a bare
    ``[]``), so the agent would never see it — that earlier shape was an
    in-process illusion. ``get_symbol`` / ``read_file`` already raise on not-found;
    the four list-returning tools (search_code / what_imports / blast_radius /
    tests_for) must raise too, uniformly.

    When NOT rebuilding, an empty result stays a plain empty list (no raise, no
    notice) — the false-positive guard.
    """

    async def test_rebuilding_notice_helper_returns_message_when_in_progress(
        self, tmp_path: Path
    ) -> None:
        """A8 seam: ``rebuilding_notice(manifest)`` returns a progress message in_progress.

        The pure-helper contract the six tools share — proven directly so a
        regression localises to the helper, not to each tool.
        """
        # offline — pure manifest read
        from loremaster.index.schema import rebuilding_notice  # type: ignore[import-not-found]

        manifest_path = tmp_path / "m.db"
        _seed_in_progress_rebuild(
            manifest_path, from_fp="a" * 64, to_fp="b" * 64
        )
        manifest = Manifest(str(manifest_path))

        notice = rebuilding_notice(manifest)

        assert notice is not None, (
            "rebuilding_notice must return a message when schema_rebuild is in_progress"
        )
        assert _mentions_rebuilding(notice), (
            f"the notice must tell the agent the store is rebuilding; got {notice!r}"
        )
        # The progress (done/total) must be conveyed so the agent knows to retry.
        assert str(_REBUILD_DONE) in notice and str(_REBUILD_TOTAL) in notice, (
            f"the notice must carry progress {_REBUILD_DONE}/{_REBUILD_TOTAL}; got {notice!r}"
        )

    async def test_rebuilding_notice_helper_returns_none_when_idle(
        self, tmp_path: Path
    ) -> None:
        """A8 seam: ``rebuilding_notice(manifest)`` returns None when NOT rebuilding."""
        # offline — fresh manifest, no rebuild status → idle
        from loremaster.index.schema import rebuilding_notice  # type: ignore[import-not-found]

        manifest = Manifest(str(tmp_path / "m.db"))
        assert rebuilding_notice(manifest) is None, (
            "rebuilding_notice must return None when no rebuild is in progress "
            "(so an idle empty result stays a plain empty result)"
        )

    async def test_a8a_search_code_empty_in_progress_raises_rebuilding_error(
        self, tmp_path: Path, app_context_factory: Any
    ) -> None:
        """A8a: search_code empty + in_progress → RAISES with rebuilding + progress.

        Arrange: index a real corpus; seed an in_progress rebuild in the manifest.
        Act: search with a server-side filter that matches no point (a true empty
             result that is independent of the embedder's lack of a threshold).
        Assert: the call RAISES, and the raised message mentions rebuilding AND
                carries the progress numbers (done/total). We assert on the
                EXCEPTION (serialization-robust: a ToolError IS agent-visible),
                NOT on a pre-serialization attribute of a returned object.
        """
        # real-Qdrant
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"

        app_ctx = await app_context_factory(config, manifest_path)
        # Index the corpus so the EMPTY result is "no match for this filter", not
        # "empty store". reindex(None) brings every tier current under the lock.
        await app_ctx.reindex(None)

        # Seed an in_progress rebuild AFTER the index so the read seam reads it.
        current_fp = embedding_schema_fingerprint(config)
        _seed_in_progress_rebuild(manifest_path, from_fp="9" * 64, to_fp=current_fp)

        # A server-side filter matching no indexed point forces a TRUE empty result
        # regardless of the embedder (a junk query term still returns top-k under a
        # FakeEmbedder — see _NO_MATCH_FILTER). Empty + in_progress must RAISE.
        with pytest.raises(Exception) as excinfo:  # noqa: PT011 - message asserted below
            await app_ctx.search_code(
                "champion routing widget", k=5, filters=dict(_NO_MATCH_FILTER)
            )

        message = str(excinfo.value)
        assert _mentions_rebuilding(message), (
            "an empty search_code DURING a rebuild must RAISE an error telling the "
            f"agent the store is rebuilding (so it retries); got message {message!r}"
        )
        # The progress must ride in the agent-visible message (the wire-survivable
        # surface), so the agent knows there is in-flight work and to retry.
        assert str(_REBUILD_TOTAL) in message, (
            f"the rebuilding error must carry progress (total={_REBUILD_TOTAL}); "
            f"got message {message!r}"
        )

    async def test_a8a_search_code_rebuilding_error_survives_mcp_serialization(
        self, tmp_path: Path, app_context_factory: Any
    ) -> None:
        """A8a (wire proof): the rebuilding signal survives MCP result conversion.

        The audit's finding was that a returned ``_NoticeList.schema_rebuild_notice``
        attribute is DROPPED by the MCP SDK's ``convert_result`` (the result
        serialises to a bare ``[]``), so the agent never sees the notice. This test
        drives the failure path through that same conversion the way the audit did
        and asserts the rebuilding signal is STILL agent-visible — which only holds
        if the tool RAISES (an exception is converted to an agent-visible error),
        not if it returns a notice-carrying list.

        Skips cleanly if the installed MCP SDK does not expose a ``convert_result``
        helper, so it never makes the suite brittle against an SDK refactor — the
        raise-based assertion in the sibling test is the primary contract.
        """
        # real-Qdrant
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        try:
            from mcp.server.fastmcp.utilities.func_metadata import (  # type: ignore[import-not-found]
                _convert_to_content as convert_result,
            )
        except Exception:  # pragma: no cover - SDK layout differs
            try:
                from mcp.server.fastmcp.server import (  # type: ignore[import-not-found]
                    _convert_to_content as convert_result,
                )
            except Exception:
                pytest.skip("MCP SDK convert_result helper not importable in this layout")

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"

        app_ctx = await app_context_factory(config, manifest_path)
        await app_ctx.reindex(None)
        current_fp = embedding_schema_fingerprint(config)
        _seed_in_progress_rebuild(manifest_path, from_fp="9" * 64, to_fp=current_fp)

        # Drive the tool exactly as the MCP wrapper would, then push whatever the
        # tool produces through the SDK's result conversion. The rebuilding signal
        # must be present in the converted, agent-visible payload.
        agent_visible_text = ""
        try:
            results = await app_ctx.search_code(
                "champion routing widget", k=5, filters=dict(_NO_MATCH_FILTER)
            )
            # The tool RETURNED (did not raise). Convert it the way the SDK does and
            # read what actually reaches the agent — a bare [] drops any attribute.
            converted = convert_result(results)
            agent_visible_text = repr(converted)
        except Exception as exc:
            # The tool RAISED. An MCP ToolError carries the message to the agent,
            # so the exception text IS the agent-visible payload.
            agent_visible_text = str(exc)

        assert _mentions_rebuilding(agent_visible_text), (
            "the rebuilding signal must survive MCP serialization and reach the "
            "agent (a returned _NoticeList attribute is dropped by convert_result — "
            f"a bare [] reaches the agent); agent-visible payload was "
            f"{agent_visible_text!r}"
        )
        assert str(_REBUILD_TOTAL) in agent_visible_text, (
            "the agent-visible payload must carry the rebuild progress "
            f"(total={_REBUILD_TOTAL}); payload was {agent_visible_text!r}"
        )

    async def test_a8b_search_code_empty_idle_is_plain_empty_no_raise(
        self, tmp_path: Path, app_context_factory: Any
    ) -> None:
        """A8b: search_code empty + NO rebuild → plain empty list, NO raise, NO notice.

        The false-positive guard: when the store is idle (or the rebuild is done),
        an empty result is a TRUE 'no matches' and must stay a plain empty list —
        never raised, never dressed up as rebuild-in-progress.
        """
        # real-Qdrant
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"

        app_ctx = await app_context_factory(config, manifest_path)
        await app_ctx.reindex(None)
        # NO rebuild status seeded → schema_rebuild.state is idle.

        # Same deterministic-empty trick as A8a: a server-side filter matching no
        # indexed point yields a TRUE empty result regardless of the embedder.
        results = await app_ctx.search_code(
            "champion routing widget", k=5, filters=dict(_NO_MATCH_FILTER)
        )

        # The substantive result is empty (true no-match: the filter excludes all)
        # and the call did NOT raise.
        assert len(results) == 0, (
            "the no-match file_path filter excludes every point → empty result"
        )
        assert not _mentions_rebuilding(repr(results)), (
            "an empty search_code when NOT rebuilding must stay a plain empty list "
            f"with NO rebuilding text; result repr was {results!r}"
        )

    async def test_a8c_what_imports_empty_in_progress_raises_rebuilding_error(
        self, tmp_path: Path, app_context_factory: Any
    ) -> None:
        """A8c: a SECOND list tool (what_imports) honours the SAME raise-based seam.

        Proves the rebuilding contract is a shared seam wired into more than one
        list-returning tool — not a one-off in search_code. An empty what_imports
        (nobody imports a nonexistent target) DURING a rebuild must RAISE with the
        rebuilding + progress message, exactly like search_code.
        """
        # real-Qdrant
        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"

        app_ctx = await app_context_factory(config, manifest_path)
        await app_ctx.reindex(None)

        current_fp = embedding_schema_fingerprint(config)
        _seed_in_progress_rebuild(manifest_path, from_fp="8" * 64, to_fp=current_fp)

        # A target nobody imports → empty reverse-import set → must RAISE in_progress.
        with pytest.raises(Exception) as excinfo:  # noqa: PT011 - message asserted below
            await app_ctx.what_imports("no.such.module.ever_imported")

        message = str(excinfo.value)
        assert _mentions_rebuilding(message), (
            "an empty what_imports DURING a rebuild must RAISE the SAME rebuilding "
            f"error as search_code (shared seam); got message {message!r}"
        )
        assert str(_REBUILD_TOTAL) in message, (
            f"the rebuilding error must carry progress (total={_REBUILD_TOTAL}); "
            f"got message {message!r}"
        )

    async def test_a8c_what_imports_empty_idle_is_plain_empty_no_raise(
        self, tmp_path: Path, app_context_factory: Any
    ) -> None:
        """A8c negative: what_imports empty + idle → plain empty list, NO raise.

        The same false-positive guard as A8b, for the second tool — confirms the
        shared seam is gated on in_progress for what_imports too.
        """
        # real-Qdrant
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = _config(slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"

        app_ctx = await app_context_factory(config, manifest_path)
        await app_ctx.reindex(None)
        # NO rebuild status → idle.

        importers = await app_ctx.what_imports("no.such.module.ever_imported")

        assert len(importers) == 0, "nobody imports the nonexistent target → empty"
        assert not _mentions_rebuilding(repr(importers)), (
            "an empty what_imports when NOT rebuilding must stay a plain empty list "
            f"with NO rebuilding text; result repr was {importers!r}"
        )


# ===========================================================================
# A9 — rebuild_all advances done LIVE during the rebuild (real Qdrant)
# ===========================================================================

# The number of files the extended corpus contains (3 from _build_live_corpus +
# 1 added below = 4). Named so the assertion that 0 < v < total is a strict
# interior check against the SAME value used to build the corpus, not a
# magic literal. Total must be >= 4 so there is always a strictly interior
# value between the first and last embed call.
_EXTENDED_CORPUS_TOTAL: int = 4


def _build_extended_corpus(root: Path) -> None:
    """Extend _build_live_corpus with one extra .py file for a total of 4 indexable files.

    _build_live_corpus gives widget.py, routing.py, README.md (3 indexable files).
    Adding helpers.py gives 4 — enough that an observer during the rebuild sees
    done values strictly between 0 and 4, i.e. 0 < v < total is always satisfiable
    even if one embed call processes two files (batching headroom).

    The excluded bundle.min.js and .git/config.py are still present (they must
    NOT be counted) — the total is 4 indexable files, matching _EXTENDED_CORPUS_TOTAL.
    """
    _build_live_corpus(root)
    # A fourth real Python module to push total to 4.  The content is a
    # production-plausible utility module — not foo/bar/x=1 (clause 1).
    _write(
        root / "src" / "helpers.py",
        """\
def format_week_range(start: int, end: int) -> str:
    \"\"\"Format a week range for display in a 36-week planning report.\"\"\"
    return f"W{start:02d}–W{end:02d}"
""",
    )


class ProgressSpyEmbedder(FakeEmbedder):
    """A :class:`FakeEmbedder` that snapshots ``schema_rebuild_status.done`` from
    the manifest at the MOMENT each ``embed_documents`` call begins.

    The spy reads the manifest meta key BEFORE delegating to the real embed so
    the recorded value reflects what ``rebuild_all`` has written at the time
    the embed call fires — not what it writes afterward.  This makes it
    impossible for a post-call write to fabricate a "live progress" illusion.

    Under the BUG: ``_walk_and_index`` is fully awaited and returns the complete
    outcomes list; the ``for outcome in await ...`` loop (and its
    ``_write_rebuild_status`` calls) only run after ALL embeds finish.  So every
    embed call sees ``done == 0`` from the manifest → ``max(recorded) == 0``.

    Under the FIX: ``_write_rebuild_status`` is called per-file inside the walk
    (before the next file's embed), so the spy on file N sees ``done == N-1``
    (files that completed before this call).  At least one call sees a value
    strictly between 0 and total, proving mid-rebuild progress.

    The oracle is derived from the specification ("done must advance per file"),
    NOT from reading rebuild_all's implementation — the spy does not import or
    inspect rebuild_all internals.
    """

    def __init__(self, manifest: Manifest, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # The manifest the spy reads ``done`` from — the SAME instance rebuild_all
        # writes to, so this is the real production seam (clause 3: seam coverage).
        self._spy_manifest = manifest
        # Ordered list of ``done`` values observed at the START of each embed call.
        # One entry per embed_documents call (each file produces one call via
        # _index_chunks → embed_documents).
        self.observed_done_values: list[int] = []

    async def embed_documents(self, texts: list[str]) -> Any:
        """Record the current manifest done counter, then delegate."""
        import json as _json

        raw = self._spy_manifest.meta_get(SCHEMA_REBUILD_STATUS_META_KEY)
        if raw is not None:
            try:
                blob = _json.loads(raw)
                observed_done = int(blob.get("done", 0))
            except (ValueError, TypeError, KeyError):
                observed_done = 0
        else:
            # Status not yet written — done is effectively 0.
            observed_done = 0

        self.observed_done_values.append(observed_done)
        return await super().embed_documents(texts)


class TestRebuildProgressAdvancesLive:
    """``rebuild_all`` must update ``schema_rebuild_status.done`` LIVE — advancing
    the counter after EACH file is indexed, not only after ALL files complete.

    Contract (from the spec, independent of implementation):
        * An observer reading ``schema_rebuild_status.done`` from the manifest
          partway through a rebuild must see a value strictly between 0 and total
          — not 0 the whole time then total at the very end.
        * Formally: the sequence of ``done`` values seen at the START of successive
          embed calls must be non-decreasing AND contain at least one value
          ``v`` with ``0 < v < total``.
        * Completion contract (unchanged): after ``rebuild_all`` returns,
          ``schema_rebuild_status.state == "done"`` and ``done == total``.

    Why this test FAILS on current code:
        ``_walk_and_index`` is a regular ``async def`` returning ``list[IndexOutcome]``.
        The expression ``for outcome in await self._walk_and_index(root, base)``
        fully awaits the coroutine (embedding ALL files) and THEN iterates the
        returned list.  The per-file ``_write_rebuild_status`` calls in the loop
        body only execute after every embed has finished, so ``done`` is 0
        throughout the entire (minutes-long) re-embed phase.  The spy sees
        ``done == 0`` on every embed call → ``max(observed_done_values) == 0``
        → the assertion ``max(recorded) > 0`` fails.
    """

    async def test_done_counter_advances_before_rebuild_completes(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """Arrange: index a 4-file corpus with a ProgressSpyEmbedder.
        Act: call rebuild_all() — the spy records done from the manifest at
             each embed_documents call.
        Assert:
            1. Observed done values are non-decreasing (no resets).
            2. At least one observed value is strictly between 0 and total
               (proves mid-rebuild progress — not an all-zero-then-jump).
            3. After rebuild_all: state == "done", done == total (completion
               correct, crash-safety invariant untouched).
        """
        # real-Qdrant
        import json as _json

        from loremaster.index.schema import embedding_schema_fingerprint  # type: ignore[import-not-found]

        slug = _slug()
        live = tmp_path / "live"
        _build_extended_corpus(live)
        config = _config(slug=slug, live_path=live)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))

        # Sanity: verify the corpus actually has the expected total so a
        # miscounted corpus silently invalidates the oracle.
        # We count by doing an initial index and reading the manifest — the same
        # authoritative source rebuild_all uses (clause 5: same source of truth).
        seed_embedder = FakeEmbedder(dim=_DIM)
        seed_indexer = _make_indexer(
            config=config, store=store, embedder=seed_embedder,
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )
        await seed_indexer.index_all()
        # All 4 indexable files must have been indexed on the initial pass.
        initial_indexed = sum(
            1 for row in manifest.all_files() if row.state == "indexed"
        )
        assert initial_indexed == _EXTENDED_CORPUS_TOTAL, (
            f"corpus setup error: expected {_EXTENDED_CORPUS_TOTAL} indexed files, "
            f"got {initial_indexed} — _build_extended_corpus or _EXTENDED_CORPUS_TOTAL "
            f"is inconsistent"
        )

        # Now wire the spy embedder into a FRESH indexer for the rebuild.
        # The spy and rebuild_all share the SAME manifest instance — the real seam.
        spy = ProgressSpyEmbedder(manifest=manifest, dim=_DIM)
        rebuild_indexer = _make_indexer(
            config=config, store=store, embedder=spy,
            manifest=manifest, snapshot_root=tmp_path / "snap",
        )

        # ACT: rebuild_all purges all manifest rows + vectors, then re-embeds every
        # file.  The spy records done at the start of each embed_documents call.
        fingerprint = embedding_schema_fingerprint(config)
        await rebuild_indexer.rebuild_all(fingerprint=fingerprint)  # type: ignore[attr-defined]

        # -----------------------------------------------------------------------
        # ASSERT 1: the spy must have been called (> 0 embed calls) — proves the
        # rebuild actually ran and was observable, not vacuously empty.
        # -----------------------------------------------------------------------
        assert len(spy.observed_done_values) > 0, (
            "rebuild_all must call embed_documents at least once — "
            "the spy must have recorded observations (corpus has 4 files)"
        )

        # Sanity bound on observation count: at most one call per file (clause 4).
        # A batching implementation might call embed_documents fewer times than
        # files (multiple files per batch), but never MORE than files.
        assert len(spy.observed_done_values) <= _EXTENDED_CORPUS_TOTAL, (
            f"embed_documents was called {len(spy.observed_done_values)} times — "
            f"more than the {_EXTENDED_CORPUS_TOTAL} files in the corpus (impossible)"
        )

        # -----------------------------------------------------------------------
        # ASSERT 2: the observed sequence is non-decreasing.
        # (A live counter that resets mid-rebuild would indicate a different bug.)
        # -----------------------------------------------------------------------
        for index in range(1, len(spy.observed_done_values)):
            assert spy.observed_done_values[index] >= spy.observed_done_values[index - 1], (
                f"observed done values must be non-decreasing; "
                f"sequence {spy.observed_done_values} has a decrease at index {index}"
            )

        # -----------------------------------------------------------------------
        # ASSERT 3 (PRIMARY — the one that FAILS on current code):
        # At least one observed done value is strictly between 0 and total.
        # This is the precise contract: "done must advance DURING the rebuild."
        #
        # Under the bug: every embed call sees done==0 (the counter is written
        # AFTER _walk_and_index returns the full list) → no value in (0, total)
        # exists → this assertion fails.
        #
        # Under the fix: _write_rebuild_status is called per-file inside the walk
        # so by the time the N-th file's embed_documents fires, N-1 files' status
        # writes have already landed → at least one call sees done >= 1 < total.
        #
        # Robustness against batching: if the implementation processes multiple
        # files per embed_documents call, the spy still records the done value at
        # the START of that call.  As long as ANY per-file status write precedes
        # a subsequent embed call, the condition holds.  We do NOT require a
        # strictly-increasing value per call (batching may keep it flat for a
        # group), only that the overall sequence reaches a strictly interior value.
        # -----------------------------------------------------------------------
        observed_max_before_last = max(spy.observed_done_values[:-1]) if len(spy.observed_done_values) > 1 else spy.observed_done_values[0]
        # The primary discriminator: a value strictly between 0 and total was seen.
        has_interior_progress = any(
            0 < value < _EXTENDED_CORPUS_TOTAL
            for value in spy.observed_done_values
        )
        assert has_interior_progress, (
            f"rebuild_all must advance schema_rebuild_status.done LIVE — "
            f"at least one embed_documents call must observe done in "
            f"(0, {_EXTENDED_CORPUS_TOTAL}) exclusive, but observed values were "
            f"{spy.observed_done_values!r} (all-zero means done is only written "
            f"AFTER _walk_and_index returns the full list — the bug)"
        )

        # -----------------------------------------------------------------------
        # ASSERT 4: completion state is correct (crash-safety contract untouched).
        # Final state after rebuild_all: state == "done" AND done == total.
        # -----------------------------------------------------------------------
        raw_final = manifest.meta_get(SCHEMA_REBUILD_STATUS_META_KEY)
        assert raw_final is not None, (
            "schema_rebuild_status meta key must be present after rebuild_all completes"
        )
        final_blob = _json.loads(raw_final)
        assert final_blob["state"] == "done", (
            f"schema_rebuild_status.state must be 'done' after successful rebuild_all; "
            f"got {final_blob['state']!r}"
        )
        # done must equal the count of indexed files — not the pre-counted total,
        # which could differ if files were skipped or failed.  We read done and
        # total from the BLOB so this is an exact-match assertion on the produced
        # state, not a restatement of _EXTENDED_CORPUS_TOTAL (independent oracle).
        assert final_blob["done"] == final_blob["total"], (
            f"schema_rebuild_status.done must equal total at completion; "
            f"blob={final_blob!r}"
        )
        # Sanity bound: done and total are non-negative and done >= initial_indexed
        # (we re-embedded at least as many files as the initial index had — clause 4).
        assert final_blob["done"] >= 1, (
            f"done must be positive after a real rebuild; blob={final_blob!r}"
        )
        assert final_blob["total"] >= 1, (
            f"total must be positive for a non-empty corpus; blob={final_blob!r}"
        )
        # The fingerprint stamp must be set after success (crash-safety: written
        # only on completion, not during).
        stored_fp = manifest.meta_get(SCHEMA_FINGERPRINT_META_KEY)
        assert stored_fp == fingerprint, (
            f"the fingerprint must be stamped into the manifest after a successful "
            f"rebuild_all; stored={stored_fp!r}, expected={fingerprint!r}"
        )
