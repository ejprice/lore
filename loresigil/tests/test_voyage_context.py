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
  follows the shared ``compute_backoff_delay`` ladder; a failed FINAL attempt
  never pays a parting sleep (sleeping is only a bridge BETWEEN attempts).
* A doc whose total tokens exceed the model's documented 32k context window is
  a loud per-doc failure (all-``None`` chunks) — NEVER silent truncation and
  NEVER a silent split into multiple context windows (splitting would silently
  change what "context" each chunk was embedded with).

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
from loresigil.base import Embedder, EmbedResult
from loresigil.resilient import BACKOFF_CAP_S, SleepFn, compute_backoff_delay
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
_OVERSIZE_REPEATS_PER_CHUNK: int = 500
_OVERSIZE_CHUNK_COUNT: int = 6

# Norm tolerance for the independent unit-norm sanity bound (math.hypot).
NORM_TOLERANCE: float = 1e-6

# Wall-clock ceiling proving an injected fake sleep really replaced the real
# one: the smallest REAL backoff delay is compute_backoff_delay(0) == 1s, so a
# retried call finishing well under this budget cannot have slept for real.
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
        # (b) the one backoff delay follows the SHARED canonical ladder — the
        # same compute_backoff_delay both retry loops document using.
        assert recorded_delays == [compute_backoff_delay(0)]
        assert 0 < recorded_delays[0] <= BACKOFF_CAP_S  # independent sanity bound
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


class TestVoyageContextOversizeDoc:
    """A doc over the 32k context window fails loud per-doc — never truncated.

    The codebase convention (``batching.py`` docstring): clamping over-length
    input is never batching's job, and silent truncation is forbidden. A doc
    that cannot fit ONE context window cannot be contextualized as requested,
    so its chunks degrade to the aligned all-``None`` permanent-failure
    convention while sibling docs are unaffected. Silent window-splitting is
    deliberately NOT accepted either — it would change what "context" each
    chunk was embedded with. (If the operator prefers split-and-stitch, amend
    at contract review.)
    """

    async def test_doc_over_token_window_degrades_loud_not_truncated(self) -> None:
        token_counter = VoyageTokenCounter()
        oversize_chunk = OVERSIZE_SENTENCE * _OVERSIZE_REPEATS_PER_CHUNK
        oversize_doc = [oversize_chunk] * _OVERSIZE_CHUNK_COUNT
        total_tokens = sum(token_counter.count_tokens(oversize_doc))
        # Fixture self-check with the PRODUCTION tokenizer (same source of
        # truth the embedder uses) — the doc genuinely exceeds the window.
        assert total_tokens > DOC_TOKEN_WINDOW

        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            inputs: list[list[str]] = body["inputs"]
            for doc in inputs:
                if sum(token_counter.count_tokens(doc)) > DOC_TOKEN_WINDOW:
                    # Emulates the real API: an over-window doc is a 400 —
                    # so if the client silently TRUNCATED the doc to fit, the
                    # mock would answer 200 with vectors and the all-None
                    # assertion below would catch the truncation.
                    return httpx.Response(400, json={"detail": "context window exceeded"})
            return httpx.Response(200, json=_context_payload(inputs, CONTEXT_DIM))

        embedder = _make_embedder(httpx.MockTransport(handler))
        results = await embedder.embed_document_chunks([oversize_doc, DOC_POLICY])
        # The over-window doc: aligned all-None (loud per-doc failure).
        assert results[0].vectors == [None] * _OVERSIZE_CHUNK_COUNT
        # The sibling doc is untouched by its neighbour's size.
        _assert_doc_result_matches(results[1], DOC_POLICY, CONTEXT_DIM)


class TestVoyageContextTokenCounting:
    """``count_tokens`` delegates to the pinned production tokenizer."""

    def test_count_tokens_matches_pinned_voyage_tokenizer(self) -> None:
        recorder = _ContextRecordingTransport()
        embedder = _make_embedder(recorder.transport())
        texts = [*DOC_RUNBOOK, "", QUERY_TEXT]
        # Same source of truth as production sizing decisions — the exact
        # tokenizer, not a drifting heuristic copy.
        assert embedder.count_tokens(texts) == VoyageTokenCounter().count_tokens(texts)
