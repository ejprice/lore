"""Contract tests for the Indexer's dispatch onto loresigil's contextualized
(document-grouped) embedding capability (v0.4, feat/contextualized-embedder).

``loresigil.base.Embedder`` now carries an optional capability:
``supports_contextualized`` (a bool property, ``False`` by default) and
``embed_document_chunks(docs: list[list[str]]) -> list[EmbedResult]`` (one
``EmbedResult`` per doc, chunk-aligned). ``loresigil.testing.FakeEmbedder``
ships both, deterministic and doc-context-sensitive.

The ONLY embed call site in the indexer is ``_index_chunks``
(``loremaster/loremaster/index/indexer.py:406``), which TODAY always calls the
flat ``self._embedder.embed_documents([... every chunk text ...])`` regardless
of what the embedder advertises. This file pins the contract that call site
must satisfy once it feature-detects the capability:

* ``supports_contextualized is True`` and the file yields chunks -> embed via
  ``embed_document_chunks`` with EXACTLY ONE doc = the file's
  ``embedding_text``s, in order (one file == one document, the doc-grouping
  semantics loresigil's contextualized backend needs).
* ``supports_contextualized is False`` -> the existing flat ``embed_documents``
  path, BYTE-IDENTICAL to today's behaviour (back-compat).
* The record/point-id construction is UNAFFECTED by which call path produced
  the vector -- "same records, same ids" regardless of dispatch.
* Failure semantics (a ``None`` or non-finite vector anywhere in the file's
  chunks marks the WHOLE file ``failed``, stores NOTHING new, retains any
  prior last-good points) apply identically on the grouped call site.
* On the success path, ``index.file.done``'s structured log carries
  ``usage_tokens`` (the ``EmbedResult.usage.total_tokens`` when the backend
  reports usage; ``None`` when it does not, mirroring TEI today).

These run against a REAL local Qdrant (``http://127.0.0.1:16333``, throwaway
``lore_test_*`` collections) and a REAL corpus, chunked for real through the
default lorescribe registry -- mirroring ``tests/test_indexer.py``'s own
harness conventions (real server, real chunker, a ``FakeEmbedder`` double for
the embedding step itself).

Expected RED state on current code (before the grouped dispatch exists):
every ``RecordingContextualizedEmbedder``/``NonFiniteContextualizedEmbedder``-
based test fails with an ``AssertionError`` raised from INSIDE
``embed_documents`` -- proof the indexer took the flat call path against a
double that has explicitly declared "the flat path must never be used here."
The usage-telemetry tests fail with ``AttributeError: 'LogRecord' object has
no attribute 'usage_tokens'`` (the field is not logged at all today). The
back-compat flat-path test is expected to already be GREEN (a regression
guard, not a new behaviour).
"""

from __future__ import annotations

import logging
import math
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer
from loremaster.index.manifest import STATE_FAILED, STATE_INDEXED, Manifest
from loremaster.server import LoreServer
from loremaster.store.qdrant import QdrantStore
from loresigil.base import Embedder, EmbedResult
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient

# Production dimensionality for the bulk fake (matches test_indexer.py's convention).
_DIM = 2048

_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"


# --------------------------------------------------------------------------- #
# Recording / instrumented embedder doubles
# --------------------------------------------------------------------------- #
class RecordingContextualizedEmbedder(FakeEmbedder):
    """A contextualized-capable fake that records every ``embed_document_chunks`` call.

    ``embed_documents`` (the FLAT call) is guarded to raise -- this is the
    RED-triggering assertion: today's indexer unconditionally calls the flat
    path, so any test using this double fails with THIS AssertionError until
    the indexer feature-detects ``supports_contextualized`` and dispatches to
    ``embed_document_chunks`` instead.
    """

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
    """A fake that advertises NO contextualized capability (back-compat pin).

    ``embed_document_chunks`` (the GROUPED call) is guarded to raise -- proves
    the indexer never calls the grouped method when the embedder cannot
    satisfy it. ``embed_documents`` calls are recorded (mirrors
    ``test_indexer.py``'s own ``RecordingEmbedder``).
    """

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
    """Poisons ONE named chunk's vector with NaN on the GROUPED call site.

    Mirrors ``test_indexer.py``'s ``NonFiniteEmbedder`` but targets
    ``embed_document_chunks`` specifically, so the ``isfinite`` guard is pinned
    for the grouped path too. ``embed_documents`` is guarded to raise (same
    RED-triggering convention as ``RecordingContextualizedEmbedder``).
    """

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
    """Strips usage telemetry from every result, mirroring TEI's ``usage=None`` today.

    ``TEIEmbedder`` never sets ``EmbedResult.usage`` (it stays the pydantic
    default, ``None``); ``FakeEmbedder`` ALWAYS reports usage. This double lets
    the "usage absent" half of the log-field contract be pinned against a
    realistic non-reporting backend shape, on top of an otherwise-standard
    (contextualized-capable) fake.
    """

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
    """Create parents and write ``text`` under ``base / rel_path`` (UTF-8)."""
    path = base / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# A real module the python_ast chunker splits into MULTIPLE chunks (imports +
# class + method + function) — mirrors test_indexer.py's own multi-chunk
# fixture shape, with distinct domain-realistic content (freight surcharges).
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

# A real module the python_ast chunker splits into exactly ONE chunk (a single
# bare top-level function, no imports/class/docstring to add siblings).
_SINGLE_CHUNK_MODULE = """\
def peak_season_multiplier(week):
    return 1.0 if week < 40 else 1.35
"""


def _oversize_module() -> str:
    """A real module with ONE function whose body clearly exceeds a small token cap.

    40 genuine per-leg dict-construction statements (mirrors the realistic
    "many real statements, not a repeated no-op" oversize fixture pattern used
    in ``lorescribe/tests/test_python_ast.py``), so under a small
    ``max_input_tokens`` this single AST unit is sub-split by the chunker into
    several ``sub_ordinal``-stamped pieces — the "oversize sub-split chunks
    still travel as ONE doc" edge case.
    """
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
    """A minimal, valid single-live-root :class:`LoreConfig` (TEI-shaped embedding
    block — the embedder actually injected into the Indexer is always a test
    double, so only the config's SHAPE, not its embedding backend, matters here).
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
    """Builder for a :class:`QdrantStore`, with concurrency-safe exact-name teardown.

    Mirrors ``test_indexer.py``'s own ``store_factory`` fixture (own client,
    deletes ONLY the exact collections THIS test created).
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


# --------------------------------------------------------------------------- #
# Grouped dispatch shape
# --------------------------------------------------------------------------- #
class TestGroupedDispatchShape:
    """``supports_contextualized`` feature-detection drives which embed call fires."""

    async def test_contextualized_embedder_receives_one_doc_with_all_file_chunks_in_order(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = RecordingContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")
        probe_texts = indexer.chunk_texts("custom", "src/lanes.py", source)
        assert len(probe_texts) >= 3  # genuinely a multi-chunk file

        outcome = await indexer.index_file("custom", "src/lanes.py", source)

        assert outcome.state == STATE_INDEXED
        assert len(embedder.doc_calls) == 1
        assert embedder.doc_calls[0] == [probe_texts]  # ONE doc = the file's chunks, in order

    async def test_non_contextualized_embedder_still_uses_flat_embed_documents_call(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """Back-compat pin: expected GREEN today (a regression guard, not new behaviour)."""
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = NonContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")
        probe_texts = indexer.chunk_texts("custom", "src/lanes.py", source)

        outcome = await indexer.index_file("custom", "src/lanes.py", source)

        assert outcome.state == STATE_INDEXED
        assert len(embedder.embed_batches) == 1
        assert embedder.embed_batches[0] == probe_texts

    async def test_single_chunk_file_still_dispatches_through_grouped_call_as_one_doc_one_chunk(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/season.py", _SINGLE_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = RecordingContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        source = (root / "src" / "season.py").read_text(encoding="utf-8")
        probe_texts = indexer.chunk_texts("custom", "src/season.py", source)
        assert len(probe_texts) == 1  # precondition: genuinely a single-chunk file

        outcome = await indexer.index_file("custom", "src/season.py", source)

        assert outcome.state == STATE_INDEXED
        assert len(embedder.doc_calls) == 1
        assert embedder.doc_calls[0] == [probe_texts]

    async def test_oversize_subsplit_chunks_of_one_file_travel_as_a_single_doc(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/legs.py", _oversize_module())
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        # A small max_input_tokens forces the single oversize function to be
        # sub-split by the real python_ast chunker into several sub_ordinal pieces.
        embedder = RecordingContextualizedEmbedder(dim=_DIM, max_input_tokens=150)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        source = (root / "src" / "legs.py").read_text(encoding="utf-8")
        probe_texts = indexer.chunk_texts("custom", "src/legs.py", source)
        assert len(probe_texts) >= 3  # the oversize function genuinely sub-splits

        outcome = await indexer.index_file("custom", "src/legs.py", source)

        assert outcome.state == STATE_INDEXED
        assert len(embedder.doc_calls) == 1  # ALL sub-split pieces travel as ONE doc
        assert embedder.doc_calls[0] == [probe_texts]
        assert outcome.n_chunks == len(probe_texts)

    async def test_zero_chunk_file_triggers_no_embed_call_on_either_path(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        root.mkdir(parents=True, exist_ok=True)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = RecordingContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        # An extension the registry does not claim -> zero chunks. Calling
        # index_file directly (bypassing walk-level include filtering) mirrors
        # test_indexer.py's own "unknown extension" convention.
        outcome = await indexer.index_file("custom", "data.bin", "binary-ish junk")

        assert outcome.n_chunks == 0
        assert outcome.state == STATE_INDEXED
        # Reaching this line without the guarded AssertionError already proves
        # embed_documents was never called either; doc_calls empty proves the
        # grouped call was never invoked.
        assert embedder.doc_calls == []


# --------------------------------------------------------------------------- #
# Record / point-id continuity across the two dispatch paths
# --------------------------------------------------------------------------- #
class TestGroupedPathRecordContinuity:
    """Record construction (point ids, tier, file_path) is unaffected by which
    embed call path produced the vector — "same records, same ids"."""

    async def test_grouped_and_flat_paths_produce_identical_point_ids_and_chunk_count(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")

        # The point id is uuid5(slug:tier:file_path:...) (records.py) — the
        # PROJECT slug must be held CONSTANT across both runs so the ids are
        # actually comparable; the Qdrant COLLECTION each run lands in (a
        # separate concern, via store_factory) is free to differ so the two
        # runs never collide with each other.
        project_slug = "freight-lane-fixture"
        flat_config = _config(slug=project_slug, live_path=root)
        flat_store = store_factory(_slug())
        await flat_store.ensure_collection(_DIM)
        flat_manifest = Manifest(str(tmp_path / "flat.db"))
        flat_embedder = NonContextualizedEmbedder(dim=_DIM)
        flat_indexer = _make_indexer(
            config=flat_config, store=flat_store, embedder=flat_embedder,
            manifest=flat_manifest, snapshot_root=tmp_path / "flat_snap",
        )
        flat_outcome = await flat_indexer.index_file("custom", "src/lanes.py", source)

        grouped_config = _config(slug=project_slug, live_path=root)
        grouped_store = store_factory(_slug())
        await grouped_store.ensure_collection(_DIM)
        grouped_manifest = Manifest(str(tmp_path / "grouped.db"))
        # A RECORDING contextualized-capable double (not a plain FakeEmbedder):
        # forces this run through the GROUPED call site (raises on the flat
        # one), so the test is RED against today's code -- proving the
        # dispatch actually happened, not just that ids are trivially
        # embed-method-agnostic.
        grouped_embedder = RecordingContextualizedEmbedder(dim=_DIM)
        grouped_indexer = _make_indexer(
            config=grouped_config, store=grouped_store, embedder=grouped_embedder,
            manifest=grouped_manifest, snapshot_root=tmp_path / "grouped_snap",
        )
        grouped_outcome = await grouped_indexer.index_file("custom", "src/lanes.py", source)

        assert flat_outcome.state == STATE_INDEXED
        assert grouped_outcome.state == STATE_INDEXED
        assert len(grouped_embedder.doc_calls) == 1  # the GROUPED call site was used
        assert grouped_outcome.n_chunks == flat_outcome.n_chunks

        flat_row = flat_manifest.get("custom", "src/lanes.py")
        grouped_row = grouped_manifest.get("custom", "src/lanes.py")
        assert flat_row is not None and grouped_row is not None
        assert sorted(grouped_row.chunk_ids) == sorted(flat_row.chunk_ids)


# --------------------------------------------------------------------------- #
# Grouped-path vector correctness (proves genuine context flowed into storage)
# --------------------------------------------------------------------------- #
class TestGroupedPathVectorCorrectness:
    """The vector actually stored is the context-sensitive one, not a flat one."""

    async def test_grouped_path_stores_the_context_sensitive_vector_not_a_flat_one(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = FakeEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")

        outcome = await indexer.index_file("custom", "src/lanes.py", source)
        assert outcome.state == STATE_INDEXED

        texts = indexer.chunk_texts("custom", "src/lanes.py", source)
        assert len(texts) >= 2

        # Independent oracle: call the embedder's OWN public grouped method
        # directly (bypassing the indexer entirely) with the SAME doc grouping,
        # to learn what the file's first chunk's context-sensitive vector
        # should be — NOT a value re-derived from the indexer's own formula.
        expected = await embedder.embed_document_chunks([texts])
        expected_vector = expected[0].vectors[0]
        assert expected_vector is not None

        hits = await store.search(
            expected_vector, k=1, filters={"tier": "custom", "file_path": "src/lanes.py"}
        )
        assert hits
        # Cosine similarity of a normalized vector against itself is exactly
        # 1.0 — near-1.0 here is essentially unfalsifiable except by an actual
        # stored-vector match (two independent hash-derived unit vectors in a
        # 2048-dim space have near-zero expected cosine similarity).
        assert hits[0].score == pytest.approx(1.0, abs=1e-6)

        # And prove genuine context-sensitivity: the FLAT embedding of the
        # SAME lone text is a documented-different vector, so querying with it
        # must NOT be an exact match to what actually got stored.
        flat_result = await embedder.embed_documents([texts[0]])
        flat_vector = flat_result.vectors[0]
        assert flat_vector is not None
        flat_hits = await store.search(
            flat_vector, k=1, filters={"tier": "custom", "file_path": "src/lanes.py"}
        )
        assert flat_hits
        assert flat_hits[0].score < 0.99


# --------------------------------------------------------------------------- #
# Failure semantics on the grouped call site
# --------------------------------------------------------------------------- #
class TestGroupedFailureSemantics:
    """A None/non-finite vector ANYWHERE in the doc's EmbedResult fails the WHOLE file."""

    async def test_none_vector_in_grouped_result_marks_file_failed_and_stores_nothing(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))

        probe = FakeEmbedder(dim=_DIM)
        probe_indexer = _make_indexer(
            config=config, store=store, embedder=probe,
            manifest=Manifest(str(tmp_path / "p.db")), snapshot_root=tmp_path / "snap0",
        )
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")
        texts = probe_indexer.chunk_texts("custom", "src/lanes.py", source)
        assert len(texts) >= 2

        # fail_inputs applies PER CHUNK inside embed_document_chunks too (a
        # FakeEmbedder built-in) — one failing chunk inside a multi-chunk doc.
        embedder = RecordingContextualizedEmbedder(dim=_DIM, fail_inputs={texts[0]})
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        outcome = await indexer.index_file("custom", "src/lanes.py", source)

        assert outcome.state == STATE_FAILED
        assert len(embedder.doc_calls) == 1  # the grouped call site WAS used
        row = manifest.get("custom", "src/lanes.py")
        assert row is not None and row.state == STATE_FAILED
        hits = await store.search([0.0] * _DIM, k=100)
        assert not any(
            hit.payload is not None and hit.payload["file_path"] == "src/lanes.py"
            for hit in hits
        )

    async def test_nonfinite_vector_in_grouped_result_is_never_stored(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))

        probe = FakeEmbedder(dim=_DIM)
        probe_indexer = _make_indexer(
            config=config, store=store, embedder=probe,
            manifest=Manifest(str(tmp_path / "p.db")), snapshot_root=tmp_path / "snap0",
        )
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")
        texts = probe_indexer.chunk_texts("custom", "src/lanes.py", source)

        embedder = NonFiniteContextualizedEmbedder(dim=_DIM, nan_texts={texts[0]})
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        outcome = await indexer.index_file("custom", "src/lanes.py", source)

        assert outcome.state == STATE_FAILED
        hits = await store.search([0.0] * _DIM, k=100)
        for hit in hits:
            assert hit.payload is not None
            assert hit.payload["file_path"] != "src/lanes.py"

    async def test_failed_grouped_reindex_retains_prior_good_points(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        root.mkdir(parents=True, exist_ok=True)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))

        good = RecordingContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=good, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        v1 = "def epsilon_marker():\n    return 1\n"
        first = await indexer.index_file("custom", "src/m.py", v1)
        assert first.state != STATE_FAILED
        assert len(good.doc_calls) == 1  # v1 also went through the grouped call

        hits_v1 = await store.search([0.0] * _DIM, k=100)
        ids_v1 = {
            h.payload["identity"]
            for h in hits_v1
            if h.payload is not None and h.payload["file_path"] == "src/m.py"
        }
        assert "epsilon_marker" in ids_v1

        v2 = "def zeta_marker():\n    return 2\n"
        probe = FakeEmbedder(dim=_DIM)
        probe_indexer = _make_indexer(
            config=config, store=store, embedder=probe,
            manifest=Manifest(str(tmp_path / "p.db")), snapshot_root=tmp_path / "snap0",
        )
        v2_texts = probe_indexer.chunk_texts("custom", "src/m.py", v2)
        failing = RecordingContextualizedEmbedder(dim=_DIM, fail_inputs=set(v2_texts))
        indexer2 = _make_indexer(
            config=config, store=store, embedder=failing, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        outcome = await indexer2.index_file("custom", "src/m.py", v2)

        assert outcome.state == STATE_FAILED
        row = manifest.get("custom", "src/m.py")
        assert row is not None and row.state == STATE_FAILED
        hits_v2 = await store.search([0.0] * _DIM, k=100)
        ids_v2 = {
            h.payload["identity"]
            for h in hits_v2
            if h.payload is not None and h.payload["file_path"] == "src/m.py"
        }
        assert "epsilon_marker" in ids_v2, "last-good vectors must survive a failed grouped re-index"
        assert "zeta_marker" not in ids_v2, "the failed new content must never be stored"


# --------------------------------------------------------------------------- #
# Usage telemetry in the success log
# --------------------------------------------------------------------------- #
class TestUsageTelemetryLogging:
    """``index.file.done`` carries ``usage_tokens`` when the embed result reports usage."""

    async def test_success_log_includes_usage_tokens_when_grouped_embed_result_reports_usage(
        self, tmp_path: Path, store_factory: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = RecordingContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")
        texts = indexer.chunk_texts("custom", "src/lanes.py", source)
        # Independent oracle: the embedder's OWN public count_tokens method,
        # not the log call's own internal arithmetic.
        expected_usage_tokens = sum(embedder.count_tokens(texts))

        with caplog.at_level(logging.INFO, logger="loremaster.index.indexer"):
            outcome = await indexer.index_file("custom", "src/lanes.py", source)
        assert outcome.state == STATE_INDEXED
        assert len(embedder.doc_calls) == 1  # confirms the GROUPED result is what's logged

        events = [r for r in caplog.records if r.message == "index.file.done"]
        assert len(events) == 1
        assert events[0].usage_tokens == expected_usage_tokens  # type: ignore[attr-defined]

    async def test_success_log_includes_usage_tokens_when_flat_embed_result_reports_usage(
        self, tmp_path: Path, store_factory: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = NonContextualizedEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")
        texts = indexer.chunk_texts("custom", "src/lanes.py", source)
        expected_usage_tokens = sum(embedder.count_tokens(texts))

        with caplog.at_level(logging.INFO, logger="loremaster.index.indexer"):
            outcome = await indexer.index_file("custom", "src/lanes.py", source)
        assert outcome.state == STATE_INDEXED
        assert len(embedder.embed_batches) == 1  # confirms the FLAT result is what's logged

        events = [r for r in caplog.records if r.message == "index.file.done"]
        assert len(events) == 1
        assert events[0].usage_tokens == expected_usage_tokens  # type: ignore[attr-defined]

    async def test_success_log_usage_tokens_is_none_when_embedder_reports_no_usage(
        self, tmp_path: Path, store_factory: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        root = tmp_path / "live"
        _write(root, "src/lanes.py", _MULTI_CHUNK_MODULE)
        config = _config(slug=slug, live_path=root)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        embedder = NoUsageEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, store=store, embedder=embedder, manifest=manifest,
            snapshot_root=tmp_path / "snap",
        )
        source = (root / "src" / "lanes.py").read_text(encoding="utf-8")

        with caplog.at_level(logging.INFO, logger="loremaster.index.indexer"):
            outcome = await indexer.index_file("custom", "src/lanes.py", source)
        assert outcome.state == STATE_INDEXED

        events = [r for r in caplog.records if r.message == "index.file.done"]
        assert len(events) == 1
        assert events[0].usage_tokens is None  # type: ignore[attr-defined]
