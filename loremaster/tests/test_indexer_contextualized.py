"""Contract tests for the Indexer's dispatch onto loresigil's contextualized
(document-grouped) embedding capability (v0.4).

PORTED for P5-C3b onto the async Surreal fakes (:mod:`_surreal_fakes`). The
embed-dispatch behavioural pins are UNCHANGED — a ``supports_contextualized``
embedder gets ONE doc = the file's chunk texts in order via
``embed_document_chunks``; a non-capable one keeps the flat ``embed_documents``
path; point-id / chunk-count continuity is dispatch-agnostic; a None/non-finite
vector anywhere fails the WHOLE file; ``index.file.done`` carries
``usage_tokens`` — only the fixtures change: the real Qdrant + SQLite manifest
become the fakes, manifest reads are ``await``ed, and the one vector-correctness
assertion (which relied on Qdrant cosine search) is re-expressed as an EXACT
comparison against the vector the store actually persisted (the fake has no HNSW
search, and exact equality is a strictly tighter oracle than cosine ≈ 1.0).
"""

from __future__ import annotations

import logging
import math
import uuid
from pathlib import Path
from typing import Any

import pytest
from _surreal_fakes import FakeSurrealTrio, fake_surreal_trio
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer
from loremaster.index.surreal_manifest import STATE_FAILED, STATE_INDEXED
from loremaster.server import LoreServer
from loresigil.base import Embedder, EmbedResult
from loresigil.testing import FakeEmbedder

_DIM = 2048
_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"


# --------------------------------------------------------------------------- #
# Recording / instrumented embedder doubles
# --------------------------------------------------------------------------- #
class RecordingContextualizedEmbedder(FakeEmbedder):
    """A contextualized-capable fake that records every ``embed_document_chunks`` call."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.doc_calls: list[list[list[str]]] = []

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        raise AssertionError(
            "embed_documents (flat) was called on a supports_contextualized=True "
            "embedder; the indexer must dispatch to embed_document_chunks instead"
        )

    async def embed_document_chunks(self, docs: list[list[str]]) -> list[EmbedResult]:
        self.doc_calls.append([list(doc) for doc in docs])
        return await super().embed_document_chunks(docs)


class NonContextualizedEmbedder(FakeEmbedder):
    """A fake that advertises NO contextualized capability (back-compat pin)."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.embed_batches: list[list[str]] = []

    @property
    def supports_contextualized(self) -> bool:
        return False

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        self.embed_batches.append(list(texts))
        return await super().embed_documents(texts)

    async def embed_document_chunks(self, docs: list[list[str]]) -> list[EmbedResult]:
        raise AssertionError(
            "embed_document_chunks (grouped) was called on a "
            "supports_contextualized=False embedder; the indexer must use the "
            "flat embed_documents path for backward compatibility"
        )


class NonFiniteContextualizedEmbedder(FakeEmbedder):
    """Poisons ONE named chunk's vector with NaN on the GROUPED call site."""

    def __init__(self, *, nan_texts: set[str], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._nan_texts = nan_texts

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        raise AssertionError(
            "embed_documents (flat) was called on a supports_contextualized=True "
            "embedder while pinning the GROUPED isfinite guard"
        )

    async def embed_document_chunks(self, docs: list[list[str]]) -> list[EmbedResult]:
        results = await super().embed_document_chunks(docs)
        for chunks, result in zip(docs, results, strict=True):
            poisoned: list[list[float] | None] = []
            for text, vector in zip(chunks, result.vectors, strict=True):
                if text in self._nan_texts and vector is not None:
                    bad = list(vector)
                    bad[0] = math.nan
                    poisoned.append(bad)
                else:
                    poisoned.append(vector)
            result.vectors = poisoned
        return results


class NoUsageEmbedder(FakeEmbedder):
    """Strips usage telemetry from every result, mirroring TEI's ``usage=None`` today."""

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        result = await super().embed_documents(texts)
        result.usage = None
        return result

    async def embed_document_chunks(self, docs: list[list[str]]) -> list[EmbedResult]:
        results = await super().embed_document_chunks(docs)
        for result in results:
            result.usage = None
        return results


# --------------------------------------------------------------------------- #
# Corpus fixtures — real, realistic Python source (chunked for real)
# --------------------------------------------------------------------------- #
def _write(base: Path, rel_path: str, text: str) -> None:
    path = base / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


_MULTI_CHUNK_MODULE = '''\
"""Freight-lane surcharge helpers."""

import math


class LaneSurcharge:
    """Computes a fuel surcharge for one freight lane."""

    def __init__(self, base_rate):
        self.base_rate = base_rate

    def apply(self, distance_km):
        return self.base_rate * math.log1p(distance_km)


def blended_rate(lanes):
    """Average the surcharge across several lanes."""
    return sum(lane.base_rate for lane in lanes) / len(lanes)
'''

_SINGLE_CHUNK_MODULE = """\
def peak_season_multiplier(week):
    return 1.0 if week < 40 else 1.35
"""


def _oversize_module() -> str:
    body = "\n".join(
        f'    leg_{i} = {{"origin": origin, "destination": destination, '
        f'"distance_km": distance_km + {i}, "surcharge": distance_km * 0.0{i % 9 + 1}}}'
        for i in range(40)
    )
    return (
        "def aggregate_lane_legs(origin, destination, distance_km):\n"
        '    """Aggregate synthetic per-leg surcharge rows for one lane."""\n'
        f"{body}\n"
        "    return leg_0\n"
    )


def _config(*, slug: str, live_path: Path) -> LoreConfig:
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
        "roots": [
            {
                "tier": "custom",
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
        source_providers=[],
        config=config,
        snapshot_root=snapshot_root,
    )


def _stored_vectors(trio: FakeSurrealTrio, tier: str, file_path: str) -> set[tuple[float, ...]]:
    """The exact vectors the store persisted for ``(tier, file_path)`` (test oracle)."""
    return {
        tuple(chunk.vector)
        for chunk in trio.store.db.chunks.values()
        if chunk.tier == tier and chunk.file_path == file_path
    }


# --------------------------------------------------------------------------- #
# Grouped dispatch shape
# --------------------------------------------------------------------------- #
class TestGroupedDispatchShape:
    """``supports_contextualized`` feature-detection drives which embed call fires."""

    async def test_contextualized_embedder_receives_one_doc_with_all_file_chunks_in_order(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        embedder = RecordingContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap")
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")
        probe_texts = indexer.chunk_texts("custom", "src/lanes.py", source)
        assert len(probe_texts) >= 3

        outcome = await indexer.index_file("custom", "src/lanes.py", source)

        assert outcome.state == STATE_INDEXED
        assert len(embedder.doc_calls) == 1
        assert embedder.doc_calls[0] == [probe_texts]

    async def test_non_contextualized_embedder_still_uses_flat_embed_documents_call(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        embedder = NonContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap")
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")
        probe_texts = indexer.chunk_texts("custom", "src/lanes.py", source)

        outcome = await indexer.index_file("custom", "src/lanes.py", source)

        assert outcome.state == STATE_INDEXED
        assert len(embedder.embed_batches) == 1
        assert embedder.embed_batches[0] == probe_texts

    async def test_single_chunk_file_still_dispatches_through_grouped_call_as_one_doc_one_chunk(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/season.py", _SINGLE_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        embedder = RecordingContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap")
        source = (root / "src" / "season.py").read_text(encoding="utf-8")
        probe_texts = indexer.chunk_texts("custom", "src/season.py", source)
        assert len(probe_texts) == 1

        outcome = await indexer.index_file("custom", "src/season.py", source)

        assert outcome.state == STATE_INDEXED
        assert len(embedder.doc_calls) == 1
        assert embedder.doc_calls[0] == [probe_texts]

    async def test_oversize_subsplit_chunks_of_one_file_travel_as_a_single_doc(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/legs.py", _oversize_module())
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        embedder = RecordingContextualizedEmbedder(dim=_DIM, max_input_tokens=150)
        indexer = _make_indexer(config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap")
        source = (root / "src" / "legs.py").read_text(encoding="utf-8")
        probe_texts = indexer.chunk_texts("custom", "src/legs.py", source)
        assert len(probe_texts) >= 3

        outcome = await indexer.index_file("custom", "src/legs.py", source)

        assert outcome.state == STATE_INDEXED
        assert len(embedder.doc_calls) == 1
        assert embedder.doc_calls[0] == [probe_texts]
        assert outcome.n_chunks == len(probe_texts)

    async def test_zero_chunk_file_triggers_no_embed_call_on_either_path(self, tmp_path: Path) -> None:
        slug = _slug()
        root = tmp_path / "live"
        root.mkdir(parents=True, exist_ok=True)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        embedder = RecordingContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap")

        outcome = await indexer.index_file("custom", "data.bin", "binary-ish junk")

        assert outcome.n_chunks == 0
        assert outcome.state == STATE_INDEXED
        assert embedder.doc_calls == []


# --------------------------------------------------------------------------- #
# Record / point-id continuity across the two dispatch paths
# --------------------------------------------------------------------------- #
class TestGroupedPathRecordContinuity:
    """Record construction is unaffected by which embed call path produced the vector."""

    async def test_grouped_and_flat_paths_produce_identical_point_ids_and_chunk_count(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")

        # The point id is uuid5(slug:tier:file_path:…) — hold the PROJECT slug
        # constant across both runs so the ids are actually comparable.
        project_slug = "freight_lane_fixture"
        flat_config = _config(slug=project_slug, live_path=root)
        flat_trio = fake_surreal_trio(dim=_DIM)
        flat_indexer = _make_indexer(
            config=flat_config, trio=flat_trio, embedder=NonContextualizedEmbedder(dim=_DIM),
            snapshot_root=tmp_path / "flat_snap",
        )
        flat_outcome = await flat_indexer.index_file("custom", "src/lanes.py", source)

        grouped_config = _config(slug=project_slug, live_path=root)
        grouped_trio = fake_surreal_trio(dim=_DIM)
        grouped_embedder = RecordingContextualizedEmbedder(dim=_DIM)
        grouped_indexer = _make_indexer(
            config=grouped_config, trio=grouped_trio, embedder=grouped_embedder,
            snapshot_root=tmp_path / "grouped_snap",
        )
        grouped_outcome = await grouped_indexer.index_file("custom", "src/lanes.py", source)

        assert flat_outcome.state == STATE_INDEXED
        assert grouped_outcome.state == STATE_INDEXED
        assert len(grouped_embedder.doc_calls) == 1
        assert grouped_outcome.n_chunks == flat_outcome.n_chunks

        flat_row = await flat_trio.manifest.get("custom", "src/lanes.py")
        grouped_row = await grouped_trio.manifest.get("custom", "src/lanes.py")
        assert flat_row is not None and grouped_row is not None
        assert sorted(grouped_row.chunk_ids) == sorted(flat_row.chunk_ids)


# --------------------------------------------------------------------------- #
# Grouped-path vector correctness (proves genuine context flowed into storage)
# --------------------------------------------------------------------------- #
class TestGroupedPathVectorCorrectness:
    """The vector actually stored is the context-sensitive one, not a flat one."""

    async def test_grouped_path_stores_the_context_sensitive_vector_not_a_flat_one(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        embedder = FakeEmbedder(dim=_DIM)
        indexer = _make_indexer(config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap")
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")

        outcome = await indexer.index_file("custom", "src/lanes.py", source)
        assert outcome.state == STATE_INDEXED

        texts = indexer.chunk_texts("custom", "src/lanes.py", source)
        assert len(texts) >= 2

        # Independent oracle: the embedder's OWN public grouped method with the
        # SAME doc grouping — the context-sensitive vectors that SHOULD be stored.
        expected = await embedder.embed_document_chunks([texts])
        context_vectors = {tuple(v) for v in expected[0].vectors if v is not None}
        stored = _stored_vectors(trio, "custom", "src/lanes.py")
        # The store persisted EXACTLY the context-sensitive vectors (a strictly
        # tighter oracle than cosine ≈ 1.0 — the fake has no HNSW search).
        assert stored == context_vectors

        # And the FLAT embedding of the SAME lone first text is a documented-
        # different vector, so it is NOT among what was stored (genuine context).
        flat = await embedder.embed_documents([texts[0]])
        flat_vector = flat.vectors[0]
        assert flat_vector is not None
        assert tuple(flat_vector) not in stored


# --------------------------------------------------------------------------- #
# Failure semantics on the grouped call site
# --------------------------------------------------------------------------- #
class TestGroupedFailureSemantics:
    """A None/non-finite vector ANYWHERE in the doc's EmbedResult fails the WHOLE file."""

    async def test_none_vector_in_grouped_result_marks_file_failed_and_stores_nothing(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)

        probe_indexer = _make_indexer(
            config=config, trio=fake_surreal_trio(dim=_DIM), embedder=FakeEmbedder(dim=_DIM),
            snapshot_root=tmp_path / "snap0",
        )
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")
        texts = probe_indexer.chunk_texts("custom", "src/lanes.py", source)
        assert len(texts) >= 2

        embedder = RecordingContextualizedEmbedder(dim=_DIM, fail_inputs={texts[0]})
        indexer = _make_indexer(config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap")
        outcome = await indexer.index_file("custom", "src/lanes.py", source)

        assert outcome.state == STATE_FAILED
        assert len(embedder.doc_calls) == 1
        row = await trio.manifest.get("custom", "src/lanes.py")
        assert row is not None and row.state == STATE_FAILED
        assert "src/lanes.py" not in trio.store.stored_file_paths()

    async def test_nonfinite_vector_in_grouped_result_is_never_stored(self, tmp_path: Path) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)

        probe_indexer = _make_indexer(
            config=config, trio=fake_surreal_trio(dim=_DIM), embedder=FakeEmbedder(dim=_DIM),
            snapshot_root=tmp_path / "snap0",
        )
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")
        texts = probe_indexer.chunk_texts("custom", "src/lanes.py", source)

        embedder = NonFiniteContextualizedEmbedder(dim=_DIM, nan_texts={texts[0]})
        indexer = _make_indexer(config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap")
        outcome = await indexer.index_file("custom", "src/lanes.py", source)

        assert outcome.state == STATE_FAILED
        assert "src/lanes.py" not in trio.store.stored_file_paths()

    async def test_failed_grouped_reindex_retains_prior_good_points(self, tmp_path: Path) -> None:
        slug = _slug()
        root = tmp_path / "live"
        root.mkdir(parents=True, exist_ok=True)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)

        good = RecordingContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(config=config, trio=trio, embedder=good, snapshot_root=tmp_path / "snap")
        v1 = "def epsilon_marker():\n    return 1\n"
        first = await indexer.index_file("custom", "src/m.py", v1)
        assert first.state != STATE_FAILED
        assert len(good.doc_calls) == 1
        assert "epsilon_marker" in trio.store.identities_for("custom", "src/m.py")

        v2 = "def zeta_marker():\n    return 2\n"
        probe_indexer = _make_indexer(
            config=config, trio=fake_surreal_trio(dim=_DIM), embedder=FakeEmbedder(dim=_DIM),
            snapshot_root=tmp_path / "snap0",
        )
        v2_texts = probe_indexer.chunk_texts("custom", "src/m.py", v2)
        failing = RecordingContextualizedEmbedder(dim=_DIM, fail_inputs=set(v2_texts))
        indexer2 = _make_indexer(config=config, trio=trio, embedder=failing, snapshot_root=tmp_path / "snap")
        outcome = await indexer2.index_file("custom", "src/m.py", v2)

        assert outcome.state == STATE_FAILED
        row = await trio.manifest.get("custom", "src/m.py")
        assert row is not None and row.state == STATE_FAILED
        ids = trio.store.identities_for("custom", "src/m.py")
        assert "epsilon_marker" in ids, "last-good vectors must survive a failed grouped re-index"
        assert "zeta_marker" not in ids, "the failed new content must never be stored"


# --------------------------------------------------------------------------- #
# Usage telemetry in the success log
# --------------------------------------------------------------------------- #
class TestUsageTelemetryLogging:
    """``index.file.done`` carries ``usage_tokens`` when the embed result reports usage."""

    async def test_success_log_includes_usage_tokens_when_grouped_embed_result_reports_usage(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        embedder = RecordingContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap")
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")
        texts = indexer.chunk_texts("custom", "src/lanes.py", source)
        expected_usage_tokens = sum(embedder.count_tokens(texts))

        with caplog.at_level(logging.INFO, logger="loremaster.index.indexer"):
            outcome = await indexer.index_file("custom", "src/lanes.py", source)
        assert outcome.state == STATE_INDEXED
        assert len(embedder.doc_calls) == 1

        events = [r for r in caplog.records if r.message == "index.file.done"]
        assert len(events) == 1
        assert events[0].usage_tokens == expected_usage_tokens  # type: ignore[attr-defined]

    async def test_success_log_includes_usage_tokens_when_flat_embed_result_reports_usage(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        embedder = NonContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap")
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")
        texts = indexer.chunk_texts("custom", "src/lanes.py", source)
        expected_usage_tokens = sum(embedder.count_tokens(texts))

        with caplog.at_level(logging.INFO, logger="loremaster.index.indexer"):
            outcome = await indexer.index_file("custom", "src/lanes.py", source)
        assert outcome.state == STATE_INDEXED
        assert len(embedder.embed_batches) == 1

        events = [r for r in caplog.records if r.message == "index.file.done"]
        assert len(events) == 1
        assert events[0].usage_tokens == expected_usage_tokens  # type: ignore[attr-defined]

    async def test_success_log_usage_tokens_is_none_when_embedder_reports_no_usage(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        trio = fake_surreal_trio(dim=_DIM)
        embedder = NoUsageEmbedder(dim=_DIM)
        indexer = _make_indexer(config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap")
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")

        with caplog.at_level(logging.INFO, logger="loremaster.index.indexer"):
            outcome = await indexer.index_file("custom", "src/lanes.py", source)
        assert outcome.state == STATE_INDEXED

        events = [r for r in caplog.records if r.message == "index.file.done"]
        assert len(events) == 1
        assert events[0].usage_tokens is None  # type: ignore[attr-defined]
