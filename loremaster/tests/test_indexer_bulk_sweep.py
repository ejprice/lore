"""Contract tests for ledger #14 PART 2: the indexer BULK-SWEEP batch mode.

This is the loremaster-side consumer of the loresigil Voyage Batch API
capability (``loresigil.voyage_batch`` + the batch methods on
``VoyageCloudEmbedder``/``VoyageContextEmbedder``/``FakeEmbedder`` — see
``loresigil/tests/test_voyage_batch.py``). It pins how a full ``Indexer``
sweep (``index_all`` / ``rebuild_all``) drives that capability: instead of
embedding one file at a time inline, a batch/auto-over-threshold sweep walks
+ chunks EVERY pending file first (pass 1, zero embeds), then submits the
WHOLE sweep's pending chunks as ONE asynchronous batch job (pass 2), polls it,
and applies each file's existing atomic composed transaction as results become
available. Per-file atomicity, the manifest-state checkpoint, and the
chunker/embed fault-isolation contract already pinned in ``test_indexer.py``
are UNCHANGED — only WHERE the vectors come from differs.

SCOPE: loremaster ONLY (the indexer). This file does NOT re-pin the batch
CAPABILITY itself (submit/poll/fetch semantics, JSONL shaping, resumability at
the embedder level, vector-parity) — that contract lives in
``loresigil/tests/test_voyage_batch.py``. This file pins ONLY what the sweep
adds at the indexer seam.

THE PINNED CONFIG SEAM (``loremaster.config``, see ``test_config.py``)
-------------------------------------------------------------------------
``EmbeddingConfig.batch: BatchConfig`` (OPTIONAL, defaulted — see
``test_config.py::TestEmbeddingBatchConfig`` for the full config contract):

    mode: Literal["realtime", "batch", "auto"] = "auto"
    chunk_count_threshold: PositiveInt = 1000
    poll_interval_s: float = <loresigil.voyage_batch.DEFAULT_POLL_INTERVAL_S>

THE PINNED SWEEP-DISPATCH DECISION
-------------------------------------------------------------------------
A sweep (``index_all`` / ``rebuild_all``) decides ONCE, before pass 1, whether
to run the two-pass batch flow or the pre-existing per-file realtime flow:

* ``mode == "realtime"`` -> ALWAYS the pre-existing per-file realtime flow,
  regardless of embedder capability or pending-chunk count.
* ``mode == "batch"`` -> the two-pass batch flow, PROVIDED
  ``embedder.supports_batch`` is ``True``; otherwise falls back to realtime
  for the WHOLE sweep with ONE loud WARNING log (never a silent downgrade —
  an operator who explicitly asked for batch on a TEI/local backend must see
  why they didn't get it).
* ``mode == "auto"`` (the default) -> the two-pass batch flow ONLY when BOTH
  ``embedder.supports_batch`` is ``True`` AND the sweep's total pending-chunk
  count (summed across every tier pass 1 would actually walk — i.e. AFTER
  the existing per-tier version-stamp / mtime+size fast-path skips, never a
  raw file count) exceeds ``chunk_count_threshold``; otherwise the pre-existing
  per-file realtime flow (no batch job for a small incremental sweep — the
  12h-worst-case latency is not worth it for a handful of changed files).

``Indexer.index_file`` (the single-file pipeline the LIVE WATCHER and
``embed_query`` use) is COMPLETELY UNCHANGED and stays realtime REGARDLESS of
``embedding.batch.mode`` — the two-pass flow only exists inside a WHOLE-SWEEP
walk (``index_all`` / ``rebuild_all``), never a single-file call (see
``TestWatcherSingleFileStaysRealtime``).

THE PINNED CRASH-RECOVERY / RESUMABILITY DESIGN
-------------------------------------------------------------------------
* BEFORE polling, the submitted job's id is persisted into the manifest meta
  store under ``loremaster.index.indexer.BULK_SWEEP_BATCH_JOB_META_KEY`` as
  ``json.dumps({"job_id": <str>, "kind": "flat"|"grouped"})`` — so a process
  that crashes between submit and apply leaves durable evidence of the
  in-flight job.
* A NEW sweep first checks this meta key: a live in-flight job id REATTACHES
  (polls + fetches the EXISTING job) instead of resubmitting a NEW one (no
  double-embed, no doubled provider bill). Pass 1 still re-walks/re-chunks on
  every sweep (cheap, no network) — the point ids/content hashes it derives
  are deterministic, so re-deriving them is safe and requires no separate
  per-file bookkeeping in the meta blob itself.
* On successful application of ALL of a job's results, the meta key is
  CLEARED (so a later sweep does not mistake a completed job for a live one).
* A WHOLE-JOB terminal failure (``BatchJobFailedError``) does NOT mark the
  affected files ``failed`` and does NOT abort the sweep. The meta key is
  CLEARED and the sweep FALLS BACK TO THE REALTIME PATH for exactly the files
  that job would have covered, logging ONE WARNING — throughput degrades
  (slower, synchronous re-embed) but the sweep still fully succeeds. This is
  a DELIBERATE pin overriding two rejected alternatives (marking the files
  failed; aborting the whole sweep loudly) per the ledger's own design
  discussion: "throughput degraded beats sweep lost."

SCOPED OUT of this cycle's test coverage (flagged for the team lead / a
follow-up ledger item, not silently dropped):

* Resumability across SEVERAL concurrent in-flight batch jobs (the >100K-line
  multi-job-split case) is NOT behaviourally tested end-to-end here — it would
  require either a real 100K+-chunk fixture (impractical for a unit test) or a
  4th injectable ``EmbeddingConfig.batch`` field (a per-job line cap) the
  ledger brief did not ask for. The MULTI-JOB-SPLIT dispatch itself (multiple
  ``submit_batch_documents``/``submit_batch_document_chunks`` calls for one
  sweep) IS pinned cheaply via ``TestBulkSweepMultiJobSplitting`` using a
  small file count against the REAL ``MAX_BATCH_INPUTS`` semantics is left to
  a follow-up; only the OBSERVABLE "one job covers the whole sweep" claim is
  pinned at production scale here.
* The exact on-disk/wire JSONL ``custom_id`` naming scheme the indexer assigns
  per chunk (flat arm) / per file (grouped arm) is DELIBERATELY NOT pinned —
  tests verify correctness by comparing STORED vectors against an
  independently-computed oracle (clause 2), never by asserting a specific id
  string shape, so the GREEN implementer keeps freedom over that internal
  bookkeeping.

RED STRATEGY
-------------------------------------------------------------------------
No new top-level symbol needs an ``ImportError``-style guard: every test
either (a) constructs a batch-capable recording ``FakeEmbedder`` subclass
whose new keyword arguments (``batch_jobs``/``batch_polls_before_terminal``/
``batch_should_fail`` — ledger #14 Part 1 companion, ``loresigil.testing``)
don't exist yet, raising ``TypeError`` at fixture-setup time (mirrors
``test_indexer_snapshot_wiring.py``'s identical precedent for a not-yet-wired
optional collaborator), or (b) calls the EXISTING ``Indexer.index_all()`` /
``index_file()`` with the EXISTING config shape and asserts on OBSERVABLE
dispatch behaviour that the current (pre-Part-2) code does not yet implement
(a clean assertion failure, never a collection error). ``loremaster.index.
indexer.BULK_SWEEP_BATCH_JOB_META_KEY`` is imported inside the ONE test body
that needs it (mirrors ``TestFactoryBatchCapabilitySurvivesConfig``'s
per-test-import idiom in ``test_voyage_batch.py``), so its absence fails only
that test, not this whole file's collection.

Fakes-first (per the task brief): every test below runs against the
in-memory async ``_surreal_fakes`` trio. ONE lean live-harness test
(``TestBulkSweepLiveHarnessHappyPath``) exercises the same two-pass flow
against the REAL SurrealDB dev server for the happy path only.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _surreal_fakes import FakeSurrealTrio, fake_surreal_trio
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer
from loremaster.index.surreal_manifest import STATE_FAILED, STATE_INDEXED
from loremaster.server import LoreServer
from loremaster.source.local_directory import LocalDirectorySourceProvider
from loresigil.testing import FakeEmbedder

# Real production embedding dimensionality — the scale the store's
# vector-width guard and HNSW index will see in production (clause 1), same
# convention as test_indexer.py.
_DIM = 2048

_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"


# --------------------------------------------------------------------------- #
# Recording batch-capable embedder fakes (mirrors test_indexer.py's
# RecordingEmbedder/NonFiniteEmbedder precedent, extended with the batch seam)
# --------------------------------------------------------------------------- #
class RecordingBatchFlatEmbedder(FakeEmbedder):
    """Flat (non-contextualized) arm — records every realtime AND batch-submit
    call so a test can prove pass 1 embeds NOTHING and pass 2 submits exactly
    ONE job (or however many the sweep's own splitting logic decides)."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.realtime_calls: list[list[str]] = []
        self.batch_submit_calls: list[tuple[list[str], list[str]]] = []

    @property
    def supports_contextualized(self) -> bool:
        return False

    async def embed_documents(self, texts: list[str]) -> Any:
        self.realtime_calls.append(list(texts))
        return await super().embed_documents(texts)

    async def submit_batch_documents(self, texts: list[str], ids: list[str]) -> str:
        self.batch_submit_calls.append((list(texts), list(ids)))
        return await super().submit_batch_documents(texts, ids)

    @property
    def total_realtime_embedded(self) -> int:
        return sum(len(batch) for batch in self.realtime_calls)


class RecordingBatchGroupedEmbedder(FakeEmbedder):
    """Grouped (contextualized) arm — one batch line PER FILE, mirroring the
    realtime ``embed_document_chunks`` dispatch's own one-doc-per-file rule."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.realtime_calls: list[list[list[str]]] = []
        self.batch_submit_calls: list[tuple[list[list[str]], list[str]]] = []

    async def embed_document_chunks(self, docs: list[list[str]]) -> Any:
        self.realtime_calls.append([list(doc) for doc in docs])
        return await super().embed_document_chunks(docs)

    async def submit_batch_document_chunks(
        self, docs: list[list[str]], ids: list[str]
    ) -> str:
        self.batch_submit_calls.append(([list(doc) for doc in docs], list(ids)))
        return await super().submit_batch_document_chunks(docs, ids)

    @property
    def total_realtime_embedded(self) -> int:
        return sum(len(doc) for batch in self.realtime_calls for doc in batch)


# --------------------------------------------------------------------------- #
# Corpus + config builders
# --------------------------------------------------------------------------- #
def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _module_source(name: str, variant: int) -> str:
    """A REAL, structurally-valid (if synthetic) Python module — distinct
    per ``name``/``variant`` so every file's chunks are content-distinguishable
    (never degenerate identical fixtures the chunker/embedder could
    coincidentally alias)."""
    return (
        f'"""Pricing helper module: {name}."""\n\n\n'
        f"def compute_{name}(quantity, unit_price):\n"
        f'    """Compute the extended price for {name} (schedule variant {variant}).\"\"\"\n'
        f"    return quantity * unit_price * {variant + 1}\n\n\n"
        f"def validate_{name}(quantity):\n"
        f'    """Reject a non-positive quantity for {name}."""\n'
        f"    if quantity <= 0:\n"
        f'        raise ValueError("quantity must be positive")\n'
        f"    return quantity\n"
    )


def _build_corpus(root: Path, count: int, *, prefix: str = "module") -> list[str]:
    """Write ``count`` distinguishable Python files under ``root``; return
    their tier-relative paths (deterministic order)."""
    paths: list[str] = []
    for index in range(count):
        name = f"{prefix}_{index}"
        rel = f"src/{name}.py"
        _write(root / rel, _module_source(name, index))
        paths.append(rel)
    return paths


def _slug() -> str:
    return f"test_bulk_{uuid.uuid4().hex}"


def _config(
    *,
    slug: str,
    live_path: Path | None = None,
    static_source: Path | None = None,
    static_version: str = "1.0.0",
    batch: dict[str, Any] | None = None,
) -> LoreConfig:
    roots: list[dict[str, Any]] = []
    if live_path is not None:
        roots.append(
            {
                "tier": "custom",
                "watch": "live",
                "path": str(live_path),
                "include": ["**/*.py"],
                "exclude": [],
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
    embedding: dict[str, Any] = {
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
    }
    if batch is not None:
        embedding["batch"] = batch
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": embedding,
        "roots": roots,
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


def _trio(*, dim: int = _DIM) -> FakeSurrealTrio:
    return fake_surreal_trio(dim=dim)


def _make_indexer(
    *,
    config: LoreConfig,
    trio: FakeSurrealTrio,
    embedder: Any,
    snapshot_root: Path,
    providers: list[Any] | None = None,
) -> Indexer:
    """Wire an :class:`Indexer` onto the fake Surreal ports (mirrors
    test_indexer.py's identical helper — kept as a local copy per this
    codebase's per-file-duplication convention, see e.g.
    test_indexer_snapshot_wiring.py)."""
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
        snapshot_root=Path("/tmp/probe-bulk-sweep-unused"),
    )
    return probe.chunk_texts(tier, path, source)


def _stored_vectors_for_file(
    trio: FakeSurrealTrio, tier: str, file_path: str
) -> list[list[float]]:
    """Every vector actually stored for ``(tier, file_path)`` (order-agnostic
    oracle helper — the fake has no positional retrieval by chunk identity
    from outside the indexer, so correctness is checked as a SET, not a
    positional list)."""
    identities = trio.store.identities_for(tier, file_path)
    vectors: list[list[float]] = []
    for identity in identities:
        vector = trio.store.stored_vector_for(tier, file_path, identity)
        assert vector is not None
        vectors.append(vector)
    return vectors


async def _oracle_vectors_for_texts(texts: list[str], dim: int) -> list[list[float]]:
    """Independently-computed expected vectors: a FRESH, throwaway
    ``FakeEmbedder`` instance's own realtime call — never the batch
    implementation's own code path, and never the SAME instance under test
    (clause 2: the expected value comes from a source independent of the
    implementation)."""
    oracle = FakeEmbedder(dim=dim)
    result = await oracle.embed_documents(texts)
    return [vector for vector in result.vectors if vector is not None]


def _as_vector_set(vectors: list[list[float]]) -> set[tuple[float, ...]]:
    return {tuple(vector) for vector in vectors}


# --------------------------------------------------------------------------- #
# Dispatch decision: mode + threshold + capability gating
# --------------------------------------------------------------------------- #
class TestBulkSweepDispatchDecision:
    """``mode``/``chunk_count_threshold``/``supports_batch`` decide whether a
    sweep runs the two-pass batch flow or the pre-existing realtime flow."""

    async def test_mode_realtime_never_batches_even_with_a_batch_capable_embedder(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=3)
        config = _config(slug=slug, live_path=live, batch={"mode": "realtime"})
        trio = _trio()
        embedder = RecordingBatchFlatEmbedder(dim=_DIM, supports_batch=True)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        summary = await indexer.index_all()

        assert summary.files_indexed == len(paths)
        assert embedder.batch_submit_calls == []
        assert embedder.total_realtime_embedded > 0

    async def test_mode_auto_under_threshold_stays_realtime(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=2)
        # A threshold far above this tiny corpus's real chunk count.
        config = _config(
            slug=slug, live_path=live, batch={"mode": "auto", "chunk_count_threshold": 10_000}
        )
        trio = _trio()
        embedder = RecordingBatchFlatEmbedder(dim=_DIM, supports_batch=True)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        summary = await indexer.index_all()

        assert summary.files_indexed == len(paths)
        assert embedder.batch_submit_calls == []
        assert embedder.total_realtime_embedded > 0

    async def test_mode_auto_over_threshold_dispatches_batch(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=5)
        # A threshold small enough that 5 real chunked files trip it, without
        # needing a 1000+-file fixture (the REAL default is 1000 — this test
        # exercises the DECISION, not the production-scale default value,
        # which test_config.py already pins independently).
        config = _config(
            slug=slug, live_path=live, batch={"mode": "auto", "chunk_count_threshold": 3}
        )
        trio = _trio()
        embedder = RecordingBatchFlatEmbedder(dim=_DIM, supports_batch=True)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        summary = await indexer.index_all()

        assert summary.files_indexed == len(paths)
        assert embedder.total_realtime_embedded == 0
        assert len(embedder.batch_submit_calls) >= 1

    async def test_mode_batch_on_an_unsupported_backend_falls_back_to_realtime_with_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=2)
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        trio = _trio()
        # supports_batch defaults False — a TEI/local-backend stand-in.
        embedder = RecordingBatchFlatEmbedder(dim=_DIM)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        with caplog.at_level(logging.WARNING, logger="loremaster.index.indexer"):
            summary = await indexer.index_all()

        assert summary.files_indexed == len(paths)
        assert embedder.batch_submit_calls == []
        assert embedder.total_realtime_embedded > 0
        assert any(
            "batch" in record.message.lower() for record in caplog.records
        ), "expected a loud WARNING naming batch-mode unsupported, never a silent downgrade"

    async def test_a_skipped_static_tier_contributes_nothing_to_the_one_batch_job(
        self, tmp_path: Path
    ) -> None:
        # Cross-tier aggregation pin: a version-matched static tier is skipped
        # with ZERO walk (the pre-existing D5 fast-path); only the live tier's
        # genuinely-pending files must appear in the ONE submitted job.
        slug = _slug()
        live = tmp_path / "live"
        static_source = tmp_path / "community_src"
        live_paths = _build_corpus(live, count=2, prefix="live_module")
        _write(static_source / "lib" / "vendored.py", _module_source("vendored", 0))
        config = _config(
            slug=slug,
            live_path=live,
            static_source=static_source,
            static_version="1.0.0",
            batch={"mode": "batch"},
        )
        trio = _trio()
        embedder = RecordingBatchFlatEmbedder(dim=_DIM, supports_batch=True)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )
        # First sweep builds BOTH tiers (stamps the static tier's version).
        await indexer.index_all()
        embedder.batch_submit_calls.clear()

        # Second sweep: the static tier's version is UNCHANGED (fast-path
        # skip, zero walk); only the live tier is genuinely re-walked, but its
        # files are already `indexed` with a matching hash too, so nothing new
        # should even reach a batch submission this time.
        second_config = _config(
            slug=slug,
            live_path=live,
            static_source=static_source,
            static_version="1.0.0",
            batch={"mode": "batch"},
        )
        indexer2 = _make_indexer(
            config=second_config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )
        summary = await indexer2.index_all()

        assert summary.files_skipped == len(live_paths) + 1
        assert embedder.batch_submit_calls == []


# --------------------------------------------------------------------------- #
# The two-pass flow itself — flat arm
# --------------------------------------------------------------------------- #
class TestBulkSweepTwoPassFlatArm:
    """Pass 1 walks+chunks everything with ZERO embeds; pass 2 submits ONE
    batch job for the WHOLE sweep and applies each file's result."""

    async def test_pass_one_never_embeds_pass_two_submits_one_job_for_the_sweep(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=4)
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        trio = _trio()
        embedder = RecordingBatchFlatEmbedder(dim=_DIM, supports_batch=True)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        summary = await indexer.index_all()

        assert summary.files_indexed == len(paths)
        assert summary.files_failed == 0
        assert embedder.total_realtime_embedded == 0
        assert len(embedder.batch_submit_calls) == 1

        submitted_texts, submitted_ids = embedder.batch_submit_calls[0]
        assert len(submitted_ids) == len(set(submitted_ids)), "custom ids must be unique"
        expected_texts: list[str] = []
        for rel in paths:
            source = (live / rel).read_text(encoding="utf-8")
            expected_texts.extend(_probe_texts(config, "custom", rel, source))
        assert sorted(submitted_texts) == sorted(expected_texts)

    async def test_stored_vectors_match_an_independent_oracle_per_file(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=3)
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        trio = _trio()
        embedder = RecordingBatchFlatEmbedder(dim=_DIM, supports_batch=True)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        await indexer.index_all()

        for rel in paths:
            source = (live / rel).read_text(encoding="utf-8")
            texts = _probe_texts(config, "custom", rel, source)
            row = await trio.manifest.get("custom", rel)
            assert row is not None and row.state == STATE_INDEXED
            assert row.n_chunks == len(texts)
            stored = _as_vector_set(_stored_vectors_for_file(trio, "custom", rel))
            expected = _as_vector_set(await _oracle_vectors_for_texts(texts, _DIM))
            assert stored == expected

    async def test_usage_conserves_the_sweep_served_total(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=3)
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        trio = _trio()
        embedder = RecordingBatchFlatEmbedder(dim=_DIM, supports_batch=True)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        await indexer.index_all()

        # Independent derivation: FakeEmbedder's OWN public count_tokens, the
        # SAME source of truth its usage billing uses, recomputed here over
        # every file's actual chunk texts rather than re-read from the sweep.
        oracle = FakeEmbedder(dim=_DIM)
        expected_total = 0
        for rel in paths:
            source = (live / rel).read_text(encoding="utf-8")
            texts = _probe_texts(config, "custom", rel, source)
            expected_total += sum(oracle.count_tokens(texts))
        assert expected_total > 0

        submitted_texts, _ids = embedder.batch_submit_calls[0]
        # The submitted batch's own bill (recomputed independently) must match
        # what pass 1's collected texts actually total.
        assert sum(oracle.count_tokens(submitted_texts)) == expected_total


# --------------------------------------------------------------------------- #
# The two-pass flow itself — grouped (contextualized) arm
# --------------------------------------------------------------------------- #
class TestBulkSweepTwoPassGroupedArm:
    """The grouped arm submits ONE LINE PER FILE (mirrors the realtime
    embed_document_chunks dispatch's one-doc-per-file rule)."""

    async def test_one_batch_line_per_file(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=3)
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        trio = _trio()
        embedder = RecordingBatchGroupedEmbedder(dim=_DIM, supports_batch=True)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        summary = await indexer.index_all()

        assert summary.files_indexed == len(paths)
        assert embedder.total_realtime_embedded == 0
        assert len(embedder.batch_submit_calls) == 1
        submitted_docs, submitted_ids = embedder.batch_submit_calls[0]
        assert len(submitted_docs) == len(paths)
        assert len(submitted_ids) == len(set(submitted_ids))

        expected_docs = []
        for rel in paths:
            source = (live / rel).read_text(encoding="utf-8")
            expected_docs.append(_probe_texts(config, "custom", rel, source))
        # Order-independent: each file's chunk-text list must appear exactly
        # once among the submitted docs.
        assert sorted(submitted_docs) == sorted(expected_docs)

    async def test_stored_vectors_are_context_sensitive_like_realtime(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=2)
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        trio = _trio()
        embedder = RecordingBatchGroupedEmbedder(dim=_DIM, supports_batch=True)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        await indexer.index_all()

        oracle = FakeEmbedder(dim=_DIM)
        docs = [
            _probe_texts(config, "custom", rel, (live / rel).read_text(encoding="utf-8"))
            for rel in paths
        ]
        expected_results = await oracle.embed_document_chunks(docs)
        for rel, expected in zip(paths, expected_results, strict=True):
            stored = _as_vector_set(_stored_vectors_for_file(trio, "custom", rel))
            expected_set = _as_vector_set(
                [vector for vector in expected.vectors if vector is not None]
            )
            assert stored == expected_set


# --------------------------------------------------------------------------- #
# Fault isolation carried through the two-pass flow
# --------------------------------------------------------------------------- #
class TestBulkSweepChunkerFaultIsolationInPassOne:
    """A chunker exception during pass 1's walk isolates THAT ONE file
    ``failed`` immediately — it never reaches pass 2's batch submission, and
    every OTHER file still gets embedded via the sweep's one batch job."""

    async def test_unparseable_file_is_isolated_without_poisoning_the_batch(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=2)
        # CONTRACT FIX (team-lead, ground-truth verified): the real python_ast
        # chunker does NOT raise on syntactically-broken Python — it degrades
        # to a windowed whole-file chunk by design, so a broken .py legitimately
        # INDEXES (identically to the realtime path). The genuinely chunker-
        # raising input is the established fault-isolation corpus's comment-only
        # XML (the real Odoo dummy.xml shape, which the REAL XML chunker raises
        # on — see test_indexer_chunker_fault_isolation.py).
        _write(live / "src" / "broken.xml", "<!-- Should not be read by anyone -->\n")
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        config = config.model_copy(deep=True)
        config.include.append("**/*.xml")
        config.roots[0].include.append("**/*.xml")
        config.chunkers[".xml"] = {**config.chunkers[".py"], "chunker": "xml_generic"}
        trio = _trio()
        embedder = RecordingBatchFlatEmbedder(dim=_DIM, supports_batch=True)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        summary = await indexer.index_all()

        assert summary.files_indexed == len(paths)
        assert summary.files_failed == 1
        broken_row = await trio.manifest.get("custom", "src/broken.xml")
        assert broken_row is not None and broken_row.state == STATE_FAILED
        # The broken file's (nonexistent) chunk texts never leaked into the
        # ONE batch submission the healthy files still got.
        assert len(embedder.batch_submit_calls) == 1


# --------------------------------------------------------------------------- #
# Per-line (per-item) batch failure -> _mark_file_failed, end to end
# --------------------------------------------------------------------------- #
class TestBulkSweepPerLineFailureMapsToFailedFile:
    """A batch job whose results include a permanently-failed item for one
    file's chunks marks THAT file ``failed`` (the existing None-vector
    convention, routed end-to-end through a sweep) without poisoning siblings."""

    async def test_a_permanently_failed_chunk_fails_only_its_own_file(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=3)
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        trio = _trio()
        failing_source = (live / paths[1]).read_text(encoding="utf-8")
        failing_texts = set(_probe_texts(config, "custom", paths[1], failing_source))
        embedder = RecordingBatchFlatEmbedder(
            dim=_DIM, supports_batch=True, fail_inputs=failing_texts
        )
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        summary = await indexer.index_all()

        assert summary.files_failed == 1
        assert summary.files_indexed == len(paths) - 1
        failed_row = await trio.manifest.get("custom", paths[1])
        assert failed_row is not None and failed_row.state == STATE_FAILED
        # Siblings unaffected — still indexed with correct vectors.
        for rel in (paths[0], paths[2]):
            row = await trio.manifest.get("custom", rel)
            assert row is not None and row.state == STATE_INDEXED


# --------------------------------------------------------------------------- #
# Crash recovery / resumability
# --------------------------------------------------------------------------- #
class TestBulkSweepCrashRecoveryResumability:
    """A job id persisted to the manifest meta store BEFORE polling lets a
    brand-new sweep REATTACH instead of resubmitting (no double-embed)."""

    async def test_job_id_is_persisted_to_manifest_meta_before_polling_completes(
        self, tmp_path: Path
    ) -> None:
        from loremaster.index.indexer import BULK_SWEEP_BATCH_JOB_META_KEY

        slug = _slug()
        live = tmp_path / "live"
        _build_corpus(live, count=2)
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        trio = _trio()
        # A job that never reaches a terminal status within this test's
        # lifetime (a very high poll count) proves the meta key is written
        # BEFORE the poll loop resolves, not merely as a post-hoc side effect
        # of a successful apply.
        embedder = RecordingBatchFlatEmbedder(
            dim=_DIM, supports_batch=True, batch_polls_before_terminal=10_000
        )
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        task = asyncio.ensure_future(indexer.index_all())
        try:
            # Yield control long enough for pass 2's submit + first poll to
            # run, but not long enough for 10_000 polls to resolve.
            for _ in range(5):
                await asyncio.sleep(0)
            raw = await trio.manifest.meta_get(BULK_SWEEP_BATCH_JOB_META_KEY)
            assert raw is not None
            job_descriptor = json.loads(raw)
            assert job_descriptor["job_id"]
            assert job_descriptor["kind"] in {"flat", "grouped"}
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    async def test_a_new_sweep_reattaches_to_a_live_job_instead_of_resubmitting(
        self, tmp_path: Path
    ) -> None:
        from loremaster.index.indexer import BULK_SWEEP_BATCH_JOB_META_KEY

        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=3)
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        trio = _trio()
        shared_jobs: dict[str, Any] = {}
        embedder = RecordingBatchFlatEmbedder(
            dim=_DIM, supports_batch=True, batch_jobs=shared_jobs
        )

        # Simulate "sweep #1 submitted the job and crashed before applying":
        # drive the REAL pass 1 + submit on a throwaway indexer, then discard
        # it (the "crash"), persisting the job id exactly as the real sweep
        # would BEFORE polling — without ever applying results. The submission
        # carries the REAL deterministic point ids: the re-attach guarantee is
        # precisely that a resumed pass 1 re-derives those same ids and looks
        # results up BY id (phase-audit blocker fix), never by position — a
        # synthetic-id simulation would test nothing real.
        crashed_indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )
        crashed_pending, _, _, _ = await crashed_indexer._collect_sweep_pending(
            is_rebuild=False
        )
        crashed_job_id = await crashed_indexer._submit_batch_job(crashed_pending, "flat")
        await trio.manifest.meta_set(
            BULK_SWEEP_BATCH_JOB_META_KEY,
            json.dumps({"job_id": crashed_job_id, "kind": "flat"}),
        )
        submissions_before_resume = len(embedder.batch_submit_calls)

        # A BRAND NEW Indexer (simulating a fresh process), sharing only the
        # manifest/store (trio) and an embedder wired to the SAME batch_jobs
        # store (standing in for the real Voyage account) — never any
        # in-memory pass-1 state from the "crashed" sweep above.
        resumed_indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )
        summary = await resumed_indexer.index_all()

        assert summary.files_indexed == len(paths)
        assert len(embedder.batch_submit_calls) == submissions_before_resume, (
            "a live in-flight job must be REATTACHED, never resubmitted"
        )
        # The meta key is cleared once the reattached job's results are fully
        # applied — a THIRD sweep must not think a completed job is live.
        assert await trio.manifest.meta_get(BULK_SWEEP_BATCH_JOB_META_KEY) is None


# --------------------------------------------------------------------------- #
# Whole-job failure -> realtime fallback (the pinned decision)
# --------------------------------------------------------------------------- #
class TestBulkSweepJobFailureFallsBackToRealtime:
    """A WHOLE batch job's terminal failure falls back to realtime re-embed
    for the affected files (never marks them ``failed``, never aborts the
    sweep) — "throughput degraded beats sweep lost", logged as ONE WARNING."""

    async def test_whole_job_failure_reembeds_realtime_and_still_succeeds(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        from loremaster.index.indexer import BULK_SWEEP_BATCH_JOB_META_KEY

        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=3)
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        trio = _trio()
        embedder = RecordingBatchFlatEmbedder(
            dim=_DIM, supports_batch=True, batch_should_fail=True
        )
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        with caplog.at_level(logging.WARNING, logger="loremaster.index.indexer"):
            summary = await indexer.index_all()

        # The sweep still fully succeeds — no files marked failed, no
        # exception propagated.
        assert summary.files_indexed == len(paths)
        assert summary.files_failed == 0
        for rel in paths:
            row = await trio.manifest.get("custom", rel)
            assert row is not None and row.state == STATE_INDEXED
        # The realtime fallback actually ran (the affected texts were
        # re-embedded synchronously).
        assert embedder.total_realtime_embedded > 0
        # The meta key must not be left pointing at a dead job.
        assert await trio.manifest.meta_get(BULK_SWEEP_BATCH_JOB_META_KEY) is None
        assert any(
            "batch" in record.message.lower() and record.levelno == logging.WARNING
            for record in caplog.records
        )

        # Correctness is preserved through the fallback too.
        for rel in paths:
            source = (live / rel).read_text(encoding="utf-8")
            texts = _probe_texts(config, "custom", rel, source)
            stored = _as_vector_set(_stored_vectors_for_file(trio, "custom", rel))
            expected = _as_vector_set(await _oracle_vectors_for_texts(texts, _DIM))
            assert stored == expected


# --------------------------------------------------------------------------- #
# Watcher / single-file path stays realtime regardless of mode
# --------------------------------------------------------------------------- #
class TestWatcherSingleFileStaysRealtime:
    """``index_file`` (the live watcher's + reconcile's single-file primitive)
    is UNCHANGED by the batch config — it always uses the realtime path."""

    async def test_index_file_never_batches_even_in_batch_mode(self, tmp_path: Path) -> None:
        slug = _slug()
        live = tmp_path / "live"
        _build_corpus(live, count=1)
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        trio = _trio()
        embedder = RecordingBatchFlatEmbedder(dim=_DIM, supports_batch=True)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )
        source = (live / "src" / "module_0.py").read_text(encoding="utf-8")

        outcome = await indexer.index_file("custom", "src/module_0.py", source)

        assert outcome.state == STATE_INDEXED
        assert embedder.batch_submit_calls == []
        assert embedder.total_realtime_embedded > 0


# --------------------------------------------------------------------------- #
# rebuild_all gets the same two-pass treatment
# --------------------------------------------------------------------------- #
class TestRebuildAllBulkSweepBatching:
    """``rebuild_all`` (the full re-embed path) follows the IDENTICAL
    two-pass dispatch as ``index_all`` — this is a thin extension pin, not a
    full duplicate of every index_all scenario above."""

    async def test_rebuild_all_dispatches_through_one_batch_job_too(
        self, tmp_path: Path
    ) -> None:
        slug = _slug()
        live = tmp_path / "live"
        paths = _build_corpus(live, count=3)
        config = _config(slug=slug, live_path=live, batch={"mode": "batch"})
        trio = _trio()
        embedder = RecordingBatchFlatEmbedder(dim=_DIM, supports_batch=True)
        indexer = _make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        summary = await indexer.rebuild_all("f" * 64)

        assert summary.files_indexed == len(paths)
        assert embedder.total_realtime_embedded == 0
        assert len(embedder.batch_submit_calls) == 1


# --------------------------------------------------------------------------- #
# ONE lean live integration test (real SurrealDB dev server) — happy path
# --------------------------------------------------------------------------- #
try:
    from _surreal_harness import (
        PRODUCTION_DIM,
        TIER_A,
        SurrealEnv,
        surreal_env,  # noqa: F401 - re-exported pytest fixture
    )
    from loremaster.index.surreal_manifest import SurrealManifest
    from loremaster.store.surreal import SurrealStore

    _HARNESS_AVAILABLE = True
except ImportError:  # pragma: no cover - harness module always present in this repo
    _HARNESS_AVAILABLE = False


if _HARNESS_AVAILABLE:

    def _harness_config(*, slug: str, live_path: Path) -> LoreConfig:
        payload: dict[str, Any] = {
            "schema_version": 1,
            "project": {"slug": slug, "root": "."},
            "embedding": {
                "backend": "tei",
                "base_url": _TEI_BASE_URL,
                "endpoint": "/embed",
                "model": "voyageai/voyage-4-nano",
                "dim": PRODUCTION_DIM,
                "truncate": False,
                "max_input_tokens": 8192,
                "max_batch_texts": 32,
                "concurrency": 2,
                "connect_timeout_s": 5,
                "api_key_env": _TEI_KEY_ENV,
                "tokenizer": "voyage-4-nano",
                "batch": {"mode": "batch"},
            },
            "roots": [
                {
                    "tier": TIER_A,
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

    class TestBulkSweepLiveHarnessHappyPath:
        """The two-pass batch flow against the REAL SurrealDB dev server (not
        just the in-memory fakes) — the ONE lean live-integration companion
        the task brief calls for. FakeEmbedder still stands in for the
        network Voyage call (this pins the store/manifest seam, not a real
        Voyage account)."""

        @pytest_asyncio.fixture()
        async def bench(
            self, surreal_env: SurrealEnv, tmp_path: Path
        ) -> AsyncIterator[tuple[Indexer, SurrealManifest, LoreConfig, Path]]:
            live_root = tmp_path / "live"
            paths = _build_corpus(live_root, count=3)
            config = _harness_config(slug=surreal_env.database, live_path=live_root)
            snapshot_root = tmp_path / "snap"

            store = SurrealStore(
                url=surreal_env.url, namespace=surreal_env.namespace,
                database=surreal_env.database, dim=PRODUCTION_DIM,
                user=surreal_env.user, password=surreal_env.password,
            )
            manifest = SurrealManifest(
                url=surreal_env.url, namespace=surreal_env.namespace,
                database=surreal_env.database, user=surreal_env.user,
                password=surreal_env.password,
            )
            await store.ensure_ready()
            await manifest.ensure_ready()

            server = LoreServer(config)
            embedder = RecordingBatchFlatEmbedder(dim=PRODUCTION_DIM, supports_batch=True)
            indexer = Indexer(
                store=store, embedder=embedder, manifest=manifest,
                registry=server.registry, source_providers=[], config=config,
                snapshot_root=snapshot_root,
            )
            try:
                yield indexer, manifest, config, live_root
                del paths  # (kept for readability at the call site below)
            finally:
                await store.close()
                await manifest.close()

        async def test_two_pass_batch_sweep_lands_on_the_real_store_and_manifest(
            self,
            bench: tuple[Indexer, SurrealManifest, LoreConfig, Path],
        ) -> None:
            indexer, manifest, config, live_root = bench
            summary = await indexer.index_all()

            assert summary.files_failed == 0
            assert summary.files_indexed >= 1
            for rel in ("src/module_0.py", "src/module_1.py", "src/module_2.py"):
                row = await manifest.get(TIER_A, rel)
                assert row is not None
                assert row.state == STATE_INDEXED
                assert row.n_chunks > 0
