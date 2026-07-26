"""Contract tests for ``loresigil.voyage_context.VoyageContextEmbedder``.

New v0.4 backend for the **contextualized** (document-grouped) Voyage endpoint.
Wire ground truth is spike S8 (live-verified 2026-07-02 against the real API):

* ``POST https://api.voyageai.com/v1/contextualizedembeddings``
* Request body: ``{"inputs": [[chunk, ...], ...], "model": "voyage-context-4",
  "input_type": "document"|"query", "output_dimension": 2048|1024|512|256}``.
  ``embed_document_chunks`` sends ``input_type="document"``; ``embed_query``
  sends ONE single-chunk doc with ``input_type="query"``.
* Response: ``data[i].data[j].embedding`` — per-chunk vectors aligned 1:1 and
  positionally with ``inputs[i][j]``; ``usage.total_tokens`` is present. The
  fixture envelope here mirrors that shape (plus the API's ``index`` echoes,
  which a positional parser must tolerate, never require).
* ``enable_auto_chunking`` (live probe s8b, 2026-07-02): omitted and ``false``
  both return exactly 1:1 per-chunk vectors with identical usage; ``true`` is
  REJECTED 400 for multi-chunk inputs ("auto-chunking expects one string per
  document"). lore ALWAYS sends its own pre-chunked chunks, so EVERY request
  body — grouped, per-doc fallback, flat, query, and probe — carries
  ``"enable_auto_chunking": false`` explicitly: a provider-side default flip
  must never silently re-chunk our chunks.

Behavioural conventions are inherited from the existing loresigil embedders
(``voyage_cloud.py`` + ``resilient.py`` + ``base.py``), applied per document:

* One :class:`~loresigil.base.EmbedResult` per input doc, ``vectors`` aligned
  1:1 with that doc's chunks; ``None`` marks a permanent failure. Degrade,
  never crash; one doc's failure must not poison sibling docs.
* Wrong-dimension and non-finite (NaN/inf) vectors are quarantined to ``None``.
* 429/5xx/transport errors are retried with backoff; 400 is permanent.
* The flat ``embed_documents`` path (base-contract callers that do not group)
  embeds each text as its own single-chunk document with
  ``input_type="document"`` and unwraps the per-doc results back to ONE flat,
  input-aligned vector list; per-text permanent failure is ``None`` at that
  slot only. The empty list short-circuits without touching the network.
* The backoff sleep is injectable (``sleep_fn`` constructor keyword, default
  ``asyncio.sleep`` — the exact seam convention of ``ResilientEmbedder``) and
  draws from the shared ``compute_backoff_delay`` full-jitter window (#207); a
  failed FINAL attempt never pays a parting sleep (sleeping is only a bridge
  BETWEEN attempts).
* A doc whose chunk-group total exceeds the 32k window is split into
  OVERLAPPING sub-window requests (OPERATOR DECISION 2026-07-02, superseding
  the original fail-loud pin; live driver: odoo/fields.py-scale files, 4128
  lines). Each chunk's canonical vector comes from exactly ONE window — one
  where it has bilateral context unless it is a file-edge chunk; boundary
  chunks also travel in the adjacent window as context-only padding whose
  returned vectors are DISCARDED. Every request stays under the window
  budget; nothing is ever silently truncated; a normal-size doc's behaviour
  is byte-identical to before (single request, no windowing). Per-doc results
  carry ``windowed=True`` provenance so the indexer/render layer can mark
  ``(windowed context)`` rather than presenting partial context as whole-file
  context. Exact window packing (greedy vs balanced) is implementation
  freedom — only these observables are pinned.

Explicitly SCOPED OUT of this contract (flagged for operator review):

* Surfacing ``usage.total_tokens`` for cost accounting — the existing pattern
  has no seam for it (``voyage_cloud`` parses only ``data[].embedding``;
  ``EmbedResult`` is ``extra="forbid"``). The fixtures still carry realistic
  usage objects so the parser must at least tolerate them.
* A zero-chunk inner doc (``[[]]``) — real-API behaviour was not verified by S8.
* Per-request doc-count batching limits — not part of the S8 ground truth.
* A dedicated timeout-retry case — timeouts share the 429/5xx retry path of the
  shared ``ResilientEmbedder`` (pinned in ``test_resilient.py``); the seam is
  exercised here via 429-then-200.

All HTTP is an offline ``httpx.MockTransport``. Expected vectors are recomputed
in the test from the same pure helper the mock server used (independent of the
implementation); token sizing uses the pinned production tokenizer.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from typing import Any

import httpx
import pytest
from _contextualized_fixtures import DOC_POLICY, DOC_RUNBOOK, DOC_SINGLE
from loresigil.base import Embedder, EmbedResult, EmbedUsage
from loresigil.resilient import BACKOFF_BASE_S, BACKOFF_CAP_S, SleepFn
from loresigil.tokens import VoyageTokenCounter
from loresigil.voyage_context import (
    DEFAULT_API_URL,
    DEFAULT_DIM,
    DEFAULT_MAX_INPUT_TOKENS,
    DEFAULT_MODEL,
    VoyageContextEmbedder,
)

# S8-verified endpoint/model parameters (spec ground truth, independent of the
# implementation — the defaults test pins the module constants against these).
API_URL: str = "https://api.voyageai.com/v1/contextualizedembeddings"
API_KEY: str = "voyage-test-key-0ddba11"
MODEL: str = "voyage-context-4"
CONTEXT_DIM: int = 2048
# A documented reduced Matryoshka dimension (2048|1024|512|256) — used to prove
# output_dimension is honored, not hardcoded.
REDUCED_DIM: int = 1024
# voyage-context-4's documented per-document context window (tokens).
DOC_TOKEN_WINDOW: int = 32_000

# DOC_RUNBOOK / DOC_POLICY / DOC_SINGLE (imported above) are the grouped
# chunks of ONE source document each, exactly what a RAG indexer sends to a
# contextualized embedder — shared with ``test_testing_contextualized.py``
# via ``_contextualized_fixtures`` (same fixture, exercised against two
# different backends).
QUERY_TEXT: str = "How long do I have to file a chargeback dispute?"

# Flat (ungrouped) texts for the base-contract ``embed_documents`` path —
# standalone chunk-sized prose, drawn from the shared realistic documents.
FLAT_TEXTS: list[str] = [DOC_POLICY[0], DOC_RUNBOOK[1], DOC_SINGLE[0]]

# Sentence used to synthesize an over-window document (sized with the pinned
# production tokenizer inside the fixture builder, never guessed).
OVERSIZE_SENTENCE: str = (
    "Chargeback disputes must be filed within sixty days of the statement closing date. "
)
_WINDOWED_REPEATS_PER_CHUNK: int = 250
_WINDOWED_CHUNK_COUNT: int = 12

# Norm tolerance for the independent unit-norm sanity bound (math.hypot).
NORM_TOLERANCE: float = 1e-6

# Wall-clock ceiling for a retried call, as defence in depth behind the RECORDING
# of the injected sleep (the recording is what actually proves the fake seam was
# used; a non-empty ``recorded_delays`` cannot happen unless the injected callable
# ran).
#
# ⚠ This budget is NO LONGER a proof on its own, and the comment that used to claim
# it was has been removed rather than left to rot (#207). It previously argued "the
# smallest REAL backoff delay is compute_backoff_delay(0) == 1s, so finishing under
# 0.5s cannot have slept for real". Under the full jitter of #207 that delay is
# DRAWN from [0, 1.0), so a real sleep can legitimately return in a millisecond and
# finish well inside this budget. The inference died with the deterministic ladder;
# the assertion is kept only as a cheap regression bound on wall-clock, not as
# evidence about which sleep ran.
FAKE_SLEEP_WALL_BUDGET_S: float = 0.5


def _unit_vector_for_text(text: str, dim: int) -> list[float]:
    """Deterministic, text-distinguishing, L2-normalized ``dim`` vector.

    Built from a SHA-256 seed of ``text`` so the mock server and the test can
    independently compute the SAME vector for a chunk — which makes every
    alignment assertion a content check (a transposed/reordered/flattened
    mapping cannot pass), without ever consulting the implementation.
    """
    digest = hashlib.sha256(text.encode()).digest()
    seed = int.from_bytes(digest[:8], "big") / float(1 << 64)  # [0, 1)
    raw = [seed + 1.0 + index * 1e-6 for index in range(dim)]
    norm = math.sqrt(sum(component * component for component in raw))
    return [component / norm for component in raw]


def _heuristic_tokens(text: str) -> int:
    """~4 chars/token prose heuristic for realistic ``usage.total_tokens`` fixtures."""
    return max(1, len(text) // 4) if text else 0


def _context_payload(inputs: list[list[str]], dim: int) -> dict[str, Any]:
    """Build the S8-verified response envelope for ``inputs``.

    Shape: ``data[i].data[j].embedding`` positionally aligned with
    ``inputs[i][j]``, plus ``index`` echoes at both levels (the parser must be
    positional per S8 and tolerate the extra keys) and ``usage.total_tokens``.
    """
    data: list[dict[str, Any]] = []
    total_tokens = 0
    for doc_index, chunks in enumerate(inputs):
        entries = [
            {"index": chunk_index, "embedding": _unit_vector_for_text(chunk, dim)}
            for chunk_index, chunk in enumerate(chunks)
        ]
        data.append({"index": doc_index, "data": entries})
        total_tokens += sum(_heuristic_tokens(chunk) for chunk in chunks)
    return {"data": data, "usage": {"total_tokens": total_tokens}}


class _ContextRecordingTransport:
    """Records request bodies and serves the S8-shaped contextualized envelope."""

    def __init__(self, dim: int = CONTEXT_DIM) -> None:
        self.dim = dim
        self.requests: list[httpx.Request] = []
        self.bodies: list[dict[str, Any]] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            body: dict[str, Any] = json.loads(request.content.decode())
            self.bodies.append(body)
            return httpx.Response(200, json=_context_payload(body["inputs"], self.dim))

        return httpx.MockTransport(handler)


def _make_embedder(
    transport: httpx.MockTransport,
    output_dimension: int = CONTEXT_DIM,
) -> VoyageContextEmbedder:
    """Construct the embedder under test — this call IS the constructor contract.

    ``output_dimension`` is the single dimensionality knob (``dim`` reflects it);
    the api key arrives resolved (env-var resolution is the factory's seam,
    pinned in ``test_factory_voyage_context.py``).
    """
    return VoyageContextEmbedder(
        api_key=API_KEY,
        api_url=API_URL,
        model=MODEL,
        output_dimension=output_dimension,
        concurrency=2,
        transport=transport,
    )


def _make_embedder_with_sleep(
    transport: httpx.MockTransport,
    sleep_fn: SleepFn,
) -> VoyageContextEmbedder:
    """Constructor contract for the injectable backoff-sleep seam.

    ``sleep_fn`` is a keyword with the exact convention of
    ``ResilientEmbedder`` (``SleepFn = Callable[[float], Awaitable[None]]``,
    default ``asyncio.sleep``) so retry tests are fast and deterministic
    instead of paying real backoff sleeps.
    """
    return VoyageContextEmbedder(
        api_key=API_KEY,
        api_url=API_URL,
        model=MODEL,
        output_dimension=CONTEXT_DIM,
        concurrency=2,
        transport=transport,
        sleep_fn=sleep_fn,
    )


def _assert_doc_result_matches(result: EmbedResult, chunks: list[str], dim: int) -> None:
    """Assert one per-doc result is aligned 1:1 with ``chunks`` by CONTENT.

    The expected vector for each chunk is recomputed independently from the
    chunk text, so any transposition, reordering, flattening, or off-by-one in
    the doc/chunk mapping fails here.
    """
    assert isinstance(result, EmbedResult)
    assert result.dim == dim
    assert len(result.vectors) == len(chunks)
    for vector, chunk in zip(result.vectors, chunks, strict=True):
        assert vector is not None
        assert vector == _unit_vector_for_text(chunk, dim)
        # Independent magnitude sanity bound: a stored embedding is unit-norm.
        assert math.hypot(*vector) == pytest.approx(1.0, abs=NORM_TOLERANCE)


class TestVoyageContextAttributes:
    """Reports voyage-context-4 parameters and advertises the capability."""

    def test_is_an_embedder(self) -> None:
        recorder = _ContextRecordingTransport()
        assert isinstance(_make_embedder(recorder.transport()), Embedder)

    def test_supports_contextualized_is_true(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        assert embedder.supports_contextualized is True

    def test_reports_parameters(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        assert embedder.dim == CONTEXT_DIM
        assert embedder.normalized is True
        # The name must identify the model so operators can tell backends apart.
        assert MODEL in embedder.name
        # Default per-document window: the documented 32k context.
        assert embedder.max_input_tokens == DOC_TOKEN_WINDOW

    def test_module_defaults_match_the_verified_api(self) -> None:
        # Pins the module constants against the S8 spec values (independent
        # ground truth), so every other test may use the constants safely.
        assert DEFAULT_API_URL == API_URL
        assert DEFAULT_MODEL == MODEL
        assert DEFAULT_DIM == CONTEXT_DIM
        assert DEFAULT_MAX_INPUT_TOKENS == DOC_TOKEN_WINDOW

    def test_dim_reflects_configured_output_dimension(self) -> None:
        recorder = _ContextRecordingTransport(dim=REDUCED_DIM)
        embedder = _make_embedder(recorder.transport(), output_dimension=REDUCED_DIM)
        # dim is not a hardcoded 2048 — it follows the Matryoshka knob.
        assert embedder.dim == REDUCED_DIM


class TestVoyageContextRequestShape:
    """Body carries inputs/model/input_type/output_dimension; bearer auth set."""

    async def test_document_path_sends_grouped_inputs(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        await embedder.embed_document_chunks([DOC_RUNBOOK, DOC_POLICY])
        body = recorder.bodies[0]
        # The grouping IS the feature: chunks arrive nested per doc, verbatim.
        assert body["inputs"] == [DOC_RUNBOOK, DOC_POLICY]
        assert body["model"] == MODEL
        assert body["input_type"] == "document"
        assert body["output_dimension"] == CONTEXT_DIM
        # Our chunks are FINAL: the provider must never re-chunk them
        # (.get(): an absent key is an AssertionError, not a KeyError).
        assert body.get("enable_auto_chunking") is False

    async def test_query_path_sends_single_chunk_doc_with_input_type_query(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        await embedder.embed_query(QUERY_TEXT)
        body = recorder.bodies[0]
        # S8: the query side is ONE single-chunk doc, asymmetric input_type.
        assert body["inputs"] == [[QUERY_TEXT]]
        assert body["input_type"] == "query"
        assert body["model"] == MODEL
        assert body["output_dimension"] == CONTEXT_DIM
        assert body.get("enable_auto_chunking") is False

    async def test_sends_bearer_authorization(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        await embedder.embed_document_chunks([DOC_SINGLE])
        assert recorder.requests[0].headers.get("authorization") == f"Bearer {API_KEY}"

    async def test_every_request_disables_auto_chunking_explicitly(self) -> None:
        # Live probe s8b: enable_auto_chunking=true is a 400 on multi-chunk
        # inputs, and the omitted-param behaviour is only the provider's
        # CURRENT default. lore's chunks are final, so EVERY body on EVERY
        # path — the combined grouped request, each per-doc fallback request,
        # the flat path, the query path, and probe's sentinel POST — must pin
        # the switch off explicitly rather than lean on a default that can
        # flip server-side.
        poison_chunk = DOC_RUNBOOK[0]
        bodies: list[dict[str, Any]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            bodies.append(body)
            inputs: list[list[str]] = body["inputs"]
            if any(poison_chunk in chunk for doc in inputs for chunk in doc):
                # Forces the per-doc fallback so its request bodies are seen too.
                return httpx.Response(400, json={"detail": "invalid input"})
            return httpx.Response(200, json=_context_payload(inputs, CONTEXT_DIM))

        embedder = _make_embedder(httpx.MockTransport(handler))
        await embedder.embed_document_chunks([DOC_POLICY, DOC_RUNBOOK])
        await embedder.embed_documents([DOC_SINGLE[0]])
        await embedder.embed_query(QUERY_TEXT)
        await embedder.probe()
        # combined + (>=2) per-doc fallback + flat + query + probe.
        assert len(bodies) >= 5
        for body in bodies:
            assert body.get("enable_auto_chunking") is False

    async def test_reduced_output_dimension_flows_to_request_body(self) -> None:
        recorder = _ContextRecordingTransport(dim=REDUCED_DIM)
        embedder = _make_embedder(recorder.transport(), output_dimension=REDUCED_DIM)
        result = await embedder.embed_document_chunks([DOC_SINGLE])
        assert recorder.bodies[0]["output_dimension"] == REDUCED_DIM
        assert recorder.bodies[0].get("enable_auto_chunking") is False
        # And the matching 1024-length wire vectors are ACCEPTED, not quarantined.
        _assert_doc_result_matches(result[0], DOC_SINGLE, REDUCED_DIM)


class TestVoyageContextAlignment:
    """Per-doc, per-chunk 1:1 positional alignment — verified by vector content."""

    async def test_vectors_align_per_doc_per_chunk(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        docs = [DOC_SINGLE, DOC_RUNBOOK, DOC_POLICY]  # varying sizes: 1, 3, 2
        results = await embedder.embed_document_chunks(docs)
        assert len(results) == len(docs)
        for result, chunks in zip(results, docs, strict=True):
            _assert_doc_result_matches(result, chunks, CONTEXT_DIM)

    async def test_single_chunk_doc_round_trips(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        results = await embedder.embed_document_chunks([DOC_SINGLE])
        assert len(results) == 1
        _assert_doc_result_matches(results[0], DOC_SINGLE, CONTEXT_DIM)

    async def test_empty_docs_list_returns_empty_list_without_network(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        results = await embedder.embed_document_chunks([])
        assert results == []
        # Mirror of embed_documents([]): an empty batch never hits the wire.
        assert recorder.requests == []

    async def test_empty_string_chunk_keeps_alignment(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        doc_with_gap = [DOC_POLICY[0], "", DOC_POLICY[1]]
        results = await embedder.embed_document_chunks([doc_with_gap])
        vectors = results[0].vectors
        # Alignment is the contract: three slots, no shift, no drop. The empty
        # chunk's slot carries whatever the server returned for it (here a
        # vector; a permanent failure would be None) — never a displaced sibling.
        assert len(vectors) == 3
        assert vectors[0] == _unit_vector_for_text(doc_with_gap[0], CONTEXT_DIM)
        assert vectors[2] == _unit_vector_for_text(doc_with_gap[2], CONTEXT_DIM)


class TestVoyageContextFlatDocuments:
    """The base-contract flat ``embed_documents`` path: one single-chunk doc per text.

    Callers that do not group (the base ``Embedder`` contract) still get
    document-quality vectors: each text travels as its own single-chunk
    document with ``input_type="document"``, and the per-doc results unwrap
    back to ONE flat vector list aligned 1:1 with the input texts. Only the
    observable alignment is pinned — N single-chunk docs may legitimately
    travel in one combined request, so batching topology is NOT asserted.
    """

    async def test_empty_texts_return_empty_result_without_network(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        result = await embedder.embed_documents([])
        assert isinstance(result, EmbedResult)
        assert result.vectors == []
        assert result.dim == CONTEXT_DIM
        # The empty batch short-circuits: zero HTTP requests.
        assert recorder.requests == []

    async def test_texts_embed_as_single_chunk_documents_aligned_by_content(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        result = await embedder.embed_documents(FLAT_TEXTS)
        # Flat, input-aligned unwrap — verified by CONTENT via the hash oracle,
        # so a doc-level nesting leak or reorder cannot pass.
        assert result.dim == CONTEXT_DIM
        assert len(result.vectors) == len(FLAT_TEXTS)
        for vector, flat_text in zip(result.vectors, FLAT_TEXTS, strict=True):
            assert vector is not None
            assert vector == _unit_vector_for_text(flat_text, CONTEXT_DIM)
            assert math.hypot(*vector) == pytest.approx(1.0, abs=NORM_TOLERANCE)
        # Wire shape: every text crossed the seam as its own SINGLE-CHUNK doc
        # tagged "document" (batch composition deliberately unpinned).
        sent_docs = [doc for body in recorder.bodies for doc in body["inputs"]]
        assert sorted(sent_docs) == sorted([[flat_text] for flat_text in FLAT_TEXTS])
        for body in recorder.bodies:
            assert body["input_type"] == "document"
            assert body.get("enable_auto_chunking") is False

    async def test_one_failing_text_degrades_to_none_at_its_slot_only(self) -> None:
        poison_text = FLAT_TEXTS[1]  # middle slot — catches off-by-one remaps

        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            inputs: list[list[str]] = body["inputs"]
            if any(poison_text in chunk for doc in inputs for chunk in doc):
                return httpx.Response(400, json={"detail": "invalid input"})
            return httpx.Response(200, json=_context_payload(inputs, CONTEXT_DIM))

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents(FLAT_TEXTS)
        # Permanent failure is None AT ITS SLOT; flat siblings are unaffected.
        assert result.vectors[1] is None
        assert result.vectors[0] == _unit_vector_for_text(FLAT_TEXTS[0], CONTEXT_DIM)
        assert result.vectors[2] == _unit_vector_for_text(FLAT_TEXTS[2], CONTEXT_DIM)


class TestVoyageContextQuarantine:
    """Wrong-shape and non-finite wire vectors are quarantined to ``None``."""

    async def test_wrong_dimension_vectors_are_quarantined(self) -> None:
        # Server "honors" output_dimension=2048 with 2047-length vectors: every
        # slot must be None — a wrong-shape vector under a lying dim poisons
        # the vector index.
        recorder = _ContextRecordingTransport(dim=CONTEXT_DIM - 1)
        embedder = _make_embedder(recorder.transport())
        results = await embedder.embed_document_chunks([DOC_POLICY])
        assert results[0].vectors == [None, None]
        # The declared result dim stays the CONFIGURED one, never the liar's.
        assert results[0].dim == CONTEXT_DIM

    async def test_nan_chunk_is_quarantined_without_poisoning_doc_siblings(self) -> None:
        nan_target = DOC_POLICY[0]
        nan_vector = [float("nan")] + [0.1] * (CONTEXT_DIM - 1)

        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            data: list[dict[str, Any]] = []
            for doc_index, chunks in enumerate(body["inputs"]):
                entries = [
                    {
                        "index": chunk_index,
                        "embedding": (
                            nan_vector
                            if chunk == nan_target
                            else _unit_vector_for_text(chunk, CONTEXT_DIM)
                        ),
                    }
                    for chunk_index, chunk in enumerate(chunks)
                ]
                data.append({"index": doc_index, "data": entries})
            # allow_nan=True reproduces the literal ``NaN`` token a real server
            # can emit; the stdlib encoder rejects NaN by default.
            payload = json.dumps({"data": data, "usage": {"total_tokens": 64}}, allow_nan=True)
            return httpx.Response(
                200, content=payload.encode(), headers={"content-type": "application/json"}
            )

        embedder = _make_embedder(httpx.MockTransport(handler))
        results = await embedder.embed_document_chunks([DOC_POLICY])
        # The NaN chunk is None AT ITS SLOT; its doc-sibling keeps a real vector.
        assert results[0].vectors[0] is None
        assert results[0].vectors[1] == _unit_vector_for_text(DOC_POLICY[1], CONTEXT_DIM)


class TestVoyageContextFailureIsolation:
    """One doc's failure never poisons sibling docs; transient errors retry."""

    async def test_permanently_failing_doc_does_not_poison_siblings(self) -> None:
        poison_chunk = DOC_RUNBOOK[0]

        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            inputs: list[list[str]] = body["inputs"]
            if any(poison_chunk in chunk for doc in inputs for chunk in doc):
                # Permanent (400): the batch is unsatisfiable as sent, so the
                # embedder must fall back to per-doc resolution.
                return httpx.Response(400, json={"detail": "invalid input"})
            return httpx.Response(200, json=_context_payload(inputs, CONTEXT_DIM))

        embedder = _make_embedder(httpx.MockTransport(handler))
        docs = [DOC_POLICY, DOC_RUNBOOK, DOC_SINGLE]  # poison in the MIDDLE
        results = await embedder.embed_document_chunks(docs)
        assert len(results) == 3
        _assert_doc_result_matches(results[0], DOC_POLICY, CONTEXT_DIM)
        # The poisoned doc degrades to aligned all-None — and ONLY that doc.
        assert results[1].vectors == [None, None, None]
        _assert_doc_result_matches(results[2], DOC_SINGLE, CONTEXT_DIM)

    async def test_429_then_success_is_retried(self) -> None:
        calls = 0
        recorded_delays: list[float] = []

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                return httpx.Response(429, json={"error": "rate limited"})
            body: dict[str, Any] = json.loads(request.content.decode())
            return httpx.Response(200, json=_context_payload(body["inputs"], CONTEXT_DIM))

        async def recording_sleep(delay: float) -> None:
            recorded_delays.append(delay)

        embedder = _make_embedder_with_sleep(httpx.MockTransport(handler), recording_sleep)
        started = time.monotonic()
        results = await embedder.embed_document_chunks([DOC_POLICY])
        elapsed = time.monotonic() - started
        assert calls == 2  # (a) retried, not surfaced as a failure
        _assert_doc_result_matches(results[0], DOC_POLICY, CONTEXT_DIM)
        # (b) exactly one backoff, drawn from the SHARED policy's attempt-0 window.
        #
        # This used to read ``recorded_delays == [compute_backoff_delay(0)]``. That
        # assertion certified the OLD world: it could only hold while the backoff was
        # DETERMINISTIC, because it compares the recorded sleep against a second,
        # independent call to the same function. Under the full jitter of finding #207
        # those are two independent draws and the equality is false by construction —
        # the pin was, in effect, asserting the absence of jitter.
        #
        # What survives the change is the property that was actually meant: exactly one
        # backoff occurred, and it came from attempt 0's window ``[0, BACKOFF_BASE_S)``.
        # Strict growth and decorrelation are pinned where they belong, against the
        # shared policy itself, in loresigil/tests/test_backoff.py.
        assert len(recorded_delays) == 1
        assert 0.0 <= recorded_delays[0] <= BACKOFF_BASE_S
        # (c) the injected seam means this test no longer pays a real sleep.
        assert elapsed < FAKE_SLEEP_WALL_BUDGET_S

    async def test_no_sleep_after_final_failed_attempt(self) -> None:
        # Sleeping is only ever a bridge BETWEEN attempts. A sleep after the
        # LAST attempt's failure is pure wasted latency (up to the 16s rung)
        # paid by every permanently-failing batch right before giving up.
        events: list[tuple[str, float]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            events.append(("request", 0.0))
            return httpx.Response(429, json={"error": "rate limited"})

        async def recording_sleep(delay: float) -> None:
            events.append(("sleep", delay))

        embedder = _make_embedder_with_sleep(httpx.MockTransport(handler), recording_sleep)
        results = await embedder.embed_document_chunks([DOC_SINGLE])
        # Budget exhausted -> the aligned permanent-failure convention.
        assert results[0].vectors == [None]
        request_count = sum(1 for kind, _ in events if kind == "request")
        sleep_count = sum(1 for kind, _ in events if kind == "sleep")
        assert request_count >= 2  # the retry ladder actually ran
        # Strictly fewer sleeps than attempts, topology-agnostic: a
        # sleep-after-every-failure loop would make the two counts equal
        # regardless of how many retry sequences ran.
        assert sleep_count < request_count
        # And the final act before giving up is an ATTEMPT, never a sleep.
        assert events[-1][0] == "request"
        # Every delay honors the shared backoff cap (sanity bound).
        assert all(delay <= BACKOFF_CAP_S for kind, delay in events if kind == "sleep")

    async def test_missing_data_envelope_degrades_to_aligned_none(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"unexpected": "shape"})

        embedder = _make_embedder(httpx.MockTransport(handler))
        results = await embedder.embed_document_chunks([DOC_POLICY, DOC_SINGLE])
        # Degrade, never crash: per-doc results stay aligned with all-None slots.
        assert [result.vectors for result in results] == [[None, None], [None]]

    async def test_malformed_non_json_body_degrades_to_aligned_none(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, content=b"upstream timeout", headers={"content-type": "text/plain"}
            )

        embedder = _make_embedder(httpx.MockTransport(handler))
        results = await embedder.embed_document_chunks([DOC_SINGLE])
        assert [result.vectors for result in results] == [[None]]

    async def test_response_missing_a_doc_is_rejected_not_mismapped(self) -> None:
        # data[] persistently one doc SHORT of inputs[]: mapping it would bind
        # doc B's vectors to doc A (corpus poisoning). Reject to aligned None.
        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            inputs: list[list[str]] = body["inputs"]
            return httpx.Response(200, json=_context_payload(inputs[:-1], CONTEXT_DIM))

        embedder = _make_embedder(httpx.MockTransport(handler))
        results = await embedder.embed_document_chunks([DOC_POLICY, DOC_SINGLE])
        assert [result.vectors for result in results] == [[None, None], [None]]

    async def test_chunk_count_mismatch_within_doc_rejected_without_poisoning(self) -> None:
        # ONE doc's entry persistently drops a chunk vector: that doc is
        # unmappable (all-None); the well-formed sibling doc still resolves.
        short_marker = DOC_RUNBOOK[0]

        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            inputs: list[list[str]] = body["inputs"]
            payload = _context_payload(inputs, CONTEXT_DIM)
            for position, doc in enumerate(inputs):
                if any(short_marker in chunk for chunk in doc):
                    payload["data"][position]["data"] = payload["data"][position]["data"][:-1]
            return httpx.Response(200, json=payload)

        embedder = _make_embedder(httpx.MockTransport(handler))
        results = await embedder.embed_document_chunks([DOC_RUNBOOK, DOC_POLICY])
        assert results[0].vectors == [None, None, None]
        _assert_doc_result_matches(results[1], DOC_POLICY, CONTEXT_DIM)


class TestVoyageContextQuery:
    """``embed_query`` returns one vector or raises loud on permanent failure."""

    async def test_embed_query_returns_single_vector(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        vector = await embedder.embed_query(QUERY_TEXT)
        assert vector == _unit_vector_for_text(QUERY_TEXT, CONTEXT_DIM)
        assert math.hypot(*vector) == pytest.approx(1.0, abs=NORM_TOLERANCE)

    async def test_embed_query_raises_runtime_error_on_permanent_failure(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"detail": "invalid input"})

        embedder = _make_embedder(httpx.MockTransport(handler))
        # A query has no None-slot to degrade into — the caller needs an answer
        # or an error. Mirror of VoyageCloudEmbedder.embed_query's contract.
        with pytest.raises(RuntimeError):
            await embedder.embed_query(QUERY_TEXT)


class TestVoyageContextProbe:
    """``probe`` reports the live dimension or raises when unreachable."""

    async def test_probe_returns_observed_dim(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        assert await embedder.probe() == CONTEXT_DIM

    async def test_probe_raises_when_unreachable(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("voyage unreachable")

        embedder = _make_embedder(httpx.MockTransport(handler))
        # Propagates so the startup gate refuses to start (no silent retry loop).
        with pytest.raises(Exception):
            await embedder.probe()


def _window_vector(chunk: str, window_chunks: list[str], dim: int) -> list[float]:
    """Deterministic vector for ``chunk`` AS EMBEDDED WITHIN ``window_chunks``.

    Contextualized embeddings depend on the whole window — the realistic mock
    must too, otherwise a chunk's vector would be identical in every window
    and the tests could not observe WHICH window a canonical vector came from.
    """
    window_digest = hashlib.sha256("\x1e".join(window_chunks).encode()).hexdigest()
    return _unit_vector_for_text(f"{chunk}\x1f{window_digest}", dim)


def _build_over_window_chunks(token_counter: VoyageTokenCounter) -> list[str]:
    """Distinct, realistic source-file sections totalling > the 32k window.

    Sized with the PRODUCTION tokenizer and self-checked: the doc must exceed
    the window (forcing >= 2 sub-windows) while each chunk stays small enough
    to sit interior to a window with padding on both sides.
    """
    chunks = [
        f"Section {index:02d}: ORM field descriptor registry, part {index}. "
        + OVERSIZE_SENTENCE * _WINDOWED_REPEATS_PER_CHUNK
        for index in range(_WINDOWED_CHUNK_COUNT)
    ]
    counts = token_counter.count_tokens(chunks)
    assert sum(counts) > DOC_TOKEN_WINDOW, "fixture must exceed the 32k window"
    assert max(counts) <= DOC_TOKEN_WINDOW // 4, "chunks must fit interior to a window"
    return chunks


class _WindowingTransport:
    """Context-sensitive mock provider enforcing the real per-doc window budget.

    * Serves ``_window_vector`` per chunk (a vector depends on its whole
      window) so canonical-window identification is observable.
    * 400s any request carrying a doc over the token window (real API
      behaviour — silent truncation or over-budget windows cannot pass).
    * Optionally 400s any window containing an exact poison chunk, to fail
      ONE window while its neighbours stay healthy.
    * Records every doc entry seen/served and every served bill.
    """

    def __init__(
        self,
        token_counter: VoyageTokenCounter,
        fail_windows_containing: str | None = None,
    ) -> None:
        self._token_counter = token_counter
        self._fail_marker = fail_windows_containing
        self.bodies: list[dict[str, Any]] = []
        self.all_request_docs: list[list[str]] = []  # every doc entry SENT (incl. 400s)
        self.window_docs: list[list[str]] = []  # every doc entry served 200
        self.served_totals: list[int] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            self.bodies.append(body)
            inputs: list[list[str]] = body["inputs"]
            self.all_request_docs.extend(inputs)
            for doc in inputs:
                if sum(self._token_counter.count_tokens(doc)) > DOC_TOKEN_WINDOW:
                    return httpx.Response(400, json={"detail": "context window exceeded"})
            if self._fail_marker is not None and any(
                chunk == self._fail_marker for doc in inputs for chunk in doc
            ):
                return httpx.Response(400, json={"detail": "injected window failure"})
            total = sum(_heuristic_tokens(chunk) for doc in inputs for chunk in doc)
            data: list[dict[str, Any]] = [
                {
                    "index": doc_index,
                    "data": [
                        {
                            "index": chunk_index,
                            "embedding": _window_vector(chunk, doc, CONTEXT_DIM),
                        }
                        for chunk_index, chunk in enumerate(doc)
                    ],
                }
                for doc_index, doc in enumerate(inputs)
            ]
            self.window_docs.extend(inputs)
            self.served_totals.append(total)
            return httpx.Response(200, json={"data": data, "usage": {"total_tokens": total}})

        return httpx.MockTransport(handler)


def _find_canonical_window(
    chunk: str, vector: list[float], window_docs: list[list[str]]
) -> list[str]:
    """Return the served window whose context explains ``vector`` for ``chunk``.

    Fails the test if no served window explains the vector — i.e. the vector
    was fabricated, misaligned, or synthesized outside any real request.
    """
    for window in window_docs:
        if chunk in window and vector == _window_vector(chunk, window, CONTEXT_DIM):
            return window
    raise AssertionError(f"no served window explains the vector for chunk {chunk[:48]!r}")


class TestVoyageContextWindowedOversizeDoc:
    """OPERATOR AMENDMENT 2026-07-02: oversize docs split into OVERLAPPING windows.

    Supersedes the retired fail-loud pin (all-``None``). In the operator's
    words: "If we have to split, then we split, but let's use an algorithm
    that preserves as much context as possible for the chunks we're embedding.
    We can have overlap in the split document." Only observables are pinned —
    the packing algorithm (greedy vs balanced) is implementation freedom.
    """

    async def test_oversize_doc_gets_aligned_vectors_via_overlapping_windows(self) -> None:
        token_counter = VoyageTokenCounter()
        oversize_doc = _build_over_window_chunks(token_counter)
        recorder = _WindowingTransport(token_counter)
        embedder = _make_embedder(recorder.transport())

        results = await embedder.embed_document_chunks([oversize_doc])
        vectors = results[0].vectors

        # (a) 1:1 alignment: every chunk gets exactly one canonical vector.
        assert len(vectors) == len(oversize_doc)
        canonical_windows: list[list[str]] = []
        for chunk, vector in zip(oversize_doc, vectors, strict=True):
            assert vector is not None
            canonical_windows.append(_find_canonical_window(chunk, vector, recorder.window_docs))

        # (b) every request (even rejected ones) stayed under the budget.
        for sent_doc in recorder.all_request_docs:
            assert sum(token_counter.count_tokens(sent_doc)) <= DOC_TOKEN_WINDOW

        # It really was windowed: >= 2 distinct sub-window requests.
        assert len({tuple(window) for window in recorder.window_docs}) >= 2

        # (c) overlap: some chunk text travelled in more than one window.
        assert any(
            sum(1 for window in recorder.window_docs if chunk in window) >= 2
            for chunk in oversize_doc
        )

        # (d) maximal bilateral context: an interior FILE chunk is never
        # canonical at a window edge — edge slots are context-padding whose
        # vectors are discarded. Only the file's own first/last chunk may sit
        # at a window edge.
        last = len(oversize_doc) - 1
        for position, (chunk, window) in enumerate(
            zip(oversize_doc, canonical_windows, strict=True)
        ):
            if 0 < position < last:
                index_in_window = window.index(chunk)
                assert 0 < index_in_window < len(window) - 1, (
                    f"chunk {position} is canonical at the edge of its window"
                )

        # (3) provenance: the split is visible to the indexer/render layer.
        assert results[0].windowed is True

    async def test_normal_size_doc_is_untouched_by_windowing(self) -> None:
        # (e) byte-identical behaviour for docs within the window: ONE request,
        # the doc verbatim, no padding copies, no windowed marker.
        token_counter = VoyageTokenCounter()
        recorder = _WindowingTransport(token_counter)
        embedder = _make_embedder(recorder.transport())

        results = await embedder.embed_document_chunks([DOC_RUNBOOK])

        assert len(recorder.bodies) == 1
        assert recorder.bodies[0]["inputs"] == [DOC_RUNBOOK]
        for chunk, vector in zip(DOC_RUNBOOK, results[0].vectors, strict=True):
            # The whole doc IS the window — context-sensitive oracle agrees.
            assert vector == _window_vector(chunk, DOC_RUNBOOK, CONTEXT_DIM)
        assert results[0].windowed is False

    async def test_failed_window_nones_only_its_canonical_chunks(self) -> None:
        token_counter = VoyageTokenCounter()
        oversize_doc = _build_over_window_chunks(token_counter)
        # Fail every window carrying the FILE-FIRST chunk: file-edge chunks
        # appear in exactly one window (no left neighbour to pad into), so
        # exactly the first window fails while its right neighbour is healthy.
        recorder = _WindowingTransport(token_counter, fail_windows_containing=oversize_doc[0])
        embedder = _make_embedder(recorder.transport())

        results = await embedder.embed_document_chunks([oversize_doc])
        vectors = results[0].vectors
        assert len(vectors) == len(oversize_doc)

        none_indices = [index for index, vector in enumerate(vectors) if vector is None]
        # The failed window costs its canonical chunks…
        assert none_indices, "the failed window's canonical chunks must be None"
        # …which are a CONTIGUOUS PREFIX (windows span contiguous chunk runs
        # and the failed window is the first)…
        assert none_indices == list(range(len(none_indices)))
        # …and its neighbours are NOT poisoned: the rest carry real vectors
        # explained by healthy served windows.
        assert len(none_indices) < len(oversize_doc)
        for position in range(len(none_indices), len(oversize_doc)):
            vector = vectors[position]
            assert vector is not None
            _find_canonical_window(oversize_doc[position], vector, recorder.window_docs)

        # Context-padding copies do NOT rescue: the seam-adjacent canonical
        # chunk of the failed window also travelled (as padding) in a healthy
        # window — it must STILL be None, its padding vector discarded.
        last_none_chunk = oversize_doc[none_indices[-1]]
        healthy_chunk_texts = {chunk for window in recorder.window_docs for chunk in window}
        assert last_none_chunk in healthy_chunk_texts
        assert vectors[none_indices[-1]] is None

        # A partially-failed split is STILL windowed provenance.
        assert results[0].windowed is True

    async def test_windowed_usage_conserves_every_window_bill(self) -> None:
        # Conservation extends across windows: overlap chunks genuinely bill
        # twice, and that honest measurement must all land in the doc's usage.
        token_counter = VoyageTokenCounter()
        oversize_doc = _build_over_window_chunks(token_counter)
        recorder = _WindowingTransport(token_counter)
        embedder = _make_embedder(recorder.transport())

        results = await embedder.embed_document_chunks([oversize_doc])

        assert len(recorder.served_totals) >= 2  # it really paid per window
        assert results[0].usage == EmbedUsage(total_tokens=sum(recorder.served_totals))


class TestVoyageContextTokenCounting:
    """``count_tokens`` delegates to the pinned production tokenizer."""

    def test_count_tokens_matches_pinned_voyage_tokenizer(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        texts = [*DOC_RUNBOOK, "", QUERY_TEXT]
        # Same source of truth as production sizing decisions — the exact
        # tokenizer, not a drifting heuristic copy.
        assert embedder.count_tokens(texts) == VoyageTokenCounter().count_tokens(texts)
