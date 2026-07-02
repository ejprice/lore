"""Contract tests for the token-usage / cost-telemetry seam on ``EmbedResult``.

v0.4 follow-up cycle (operator-approved): surface the provider-billed token
count so downstream cost accounting (future loremaster work) can meter
embedding spend. The seam:

* ``EmbedUsage`` — a new, small pydantic model in ``loresigil.base``:
  ``total_tokens: int`` (>= 0, ``extra="forbid"``). A sub-model rather than a
  bare ``total_tokens: int | None`` field because (a) it mirrors the S8 wire
  object (``usage.total_tokens``) so future provider fields extend ``EmbedUsage``
  without another ``EmbedResult`` migration, (b) validation (non-negative,
  strict) lives on the value object, and (c) ``usage: EmbedUsage | None``
  reads unambiguously as "telemetry absent", where a bare ``None`` int could
  be misread as zero.
* ``EmbedResult.usage: EmbedUsage | None = None`` — OPTIONAL with default
  ``None`` so every existing constructor call remains valid unchanged.

Pinned semantics:

* ``usage.total_tokens`` = the sum of provider-reported ``usage.total_tokens``
  over the successfully PARSED 200 responses that produced this result
  ("billed" ≠ "succeeded": a quarantined vector's request was still billed).
* ``usage is None`` = the backend does not report usage at all (TEI's wire has
  no usage object; the voyage-cloud backend deliberately does not read it this
  cycle). ``None`` is NOT zero: a reporting backend with nothing billed says
  ``EmbedUsage(total_tokens=0)``.
* ``VoyageContextEmbedder`` ALWAYS reports (never ``None``): exact totals per
  call for ``embed_documents``; for ``embed_document_chunks`` the per-doc
  values must CONSERVE the call total (Σ per-doc == Σ served-and-parsed 200
  totals), with exact per-doc attribution when a doc was resolved by its own
  dedicated request(s) (the per-doc fallback). How a COMBINED request's total
  is split across its docs is deliberately unpinned beyond conservation — the
  provider bills per request, so any per-doc split of a shared request is
  attribution, not measurement.
* The mock provider's billing meter is a ~4 chars/token heuristic — deliberately
  DIFFERENT from the client's exact tokenizer, so an implementation that
  fabricates usage from its own ``count_tokens`` (instead of reading the wire)
  cannot conserve the served totals and fails here.

Explicitly SCOPED OUT this cycle (flagged for the operator):

* ``embed_query`` usage — its return type is a bare ``list[float]`` (base ABC),
  so there is no envelope to carry usage; surfacing query-side cost needs a
  richer return type or a side-channel (follow-up contract if wanted).
* POPULATING usage in ``VoyageCloudEmbedder`` (its wire DOES carry usage — the
  fixture serves it realistically, and this contract pins that the backend
  does not read it yet) and in ``TEIEmbedder`` (its wire has none to read).
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from _contextualized_fixtures import DOC_POLICY, DOC_RUNBOOK, DOC_SINGLE
from loresigil.base import EmbedResult, EmbedUsage
from loresigil.tei import TEIEmbedder
from loresigil.testing import FakeEmbedder
from loresigil.voyage_cloud import VoyageCloudEmbedder
from loresigil.voyage_context import VoyageContextEmbedder
from pydantic import ValidationError

# ── Contextualized backend parameters (S8-verified, as pinned in
#    test_voyage_context.py) ───────────────────────────────────────────────────
CONTEXT_API_URL: str = "https://api.voyageai.com/v1/contextualizedembeddings"
CONTEXT_MODEL: str = "voyage-context-4"
CONTEXT_DIM: int = 2048
API_KEY: str = "voyage-test-key-0ddba11"

# ── Sibling backend parameters (mirroring their own contract suites'
#    construction sites — unchanged constructor shapes is part of THIS pin) ────
CLOUD_API_URL: str = "https://api.voyageai.com/v1/embeddings"
CLOUD_MODEL: str = "voyage-4-large"
CLOUD_DIM: int = 2048
TEI_BASE_URL: str = "http://embedder.test:8080"
TEI_ENDPOINT: str = "/embed"
TEI_DIM: int = 2048
TEI_MAX_INPUT_TOKENS: int = 8192

# Flat (ungrouped) realistic texts for the base-contract embed_documents path.
FLAT_TEXTS: list[str] = [DOC_POLICY[0], DOC_RUNBOOK[1], DOC_SINGLE[0]]

# A plausible single-request bill for a small indexing batch (non-round on
# purpose — no magic value the implementation could echo back by accident).
SAMPLE_BILLED_TOKENS: int = 487


def _tokens_billed(inputs: list[list[str]]) -> int:
    """The MOCK PROVIDER's billing meter for one request (~4 chars/token).

    This is the server-side ground truth the fixtures serve in
    ``usage.total_tokens``. It intentionally differs from the client's exact
    tokenizer: an implementation must READ the wire value, not re-derive it.
    """
    return sum(max(1, len(chunk) // 4) if chunk else 0 for doc in inputs for chunk in doc)


def _unit_vector(seed: float, dim: int) -> list[float]:
    """A finite, L2-normalized ``dim`` vector, independent of any implementation."""
    raw = [seed + 1.0 + index * 1e-6 for index in range(dim)]
    norm = sum(component * component for component in raw) ** 0.5
    return [component / norm for component in raw]


def _context_envelope(inputs: list[list[str]], dim: int, total_tokens: int) -> dict[str, Any]:
    """The S8-verified contextualized response: data[i].data[j].embedding + usage."""
    data: list[dict[str, Any]] = []
    for doc_index, chunks in enumerate(inputs):
        entries = [
            {"index": chunk_index, "embedding": _unit_vector(float(chunk_index), dim)}
            for chunk_index, _chunk in enumerate(chunks)
        ]
        data.append({"index": doc_index, "data": entries})
    return {"data": data, "usage": {"total_tokens": total_tokens}}


class _UsageContextTransport:
    """Serves the contextualized envelope and RECORDS what it billed per request."""

    def __init__(self, dim: int = CONTEXT_DIM) -> None:
        self.dim = dim
        self.served_inputs: list[list[list[str]]] = []
        self.served_totals: list[int] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            inputs: list[list[str]] = body["inputs"]
            total = _tokens_billed(inputs)
            self.served_inputs.append(inputs)
            self.served_totals.append(total)
            return httpx.Response(200, json=_context_envelope(inputs, self.dim, total))

        return httpx.MockTransport(handler)


def _make_context_embedder(transport: httpx.MockTransport) -> VoyageContextEmbedder:
    return VoyageContextEmbedder(
        api_key=API_KEY,
        api_url=CONTEXT_API_URL,
        model=CONTEXT_MODEL,
        output_dimension=CONTEXT_DIM,
        concurrency=2,
        transport=transport,
    )


class TestEmbedUsageModel:
    """``EmbedUsage`` is a strict, non-negative token-count value object."""

    def test_holds_total_tokens(self) -> None:
        usage = EmbedUsage(total_tokens=SAMPLE_BILLED_TOKENS)
        assert usage.total_tokens == SAMPLE_BILLED_TOKENS

    def test_zero_tokens_is_valid_and_distinct_from_absent(self) -> None:
        # A reporting backend that billed nothing says 0 — which must never be
        # conflated with "does not report" (None on EmbedResult.usage).
        usage = EmbedUsage(total_tokens=0)
        assert usage.total_tokens == 0
        assert usage is not None

    def test_rejects_negative_tokens(self) -> None:
        # A negative bill is always an upstream bug — fail loud, never store.
        with pytest.raises(ValidationError):
            EmbedUsage(total_tokens=-1)

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            EmbedUsage(total_tokens=SAMPLE_BILLED_TOKENS, cost_usd=0.01)  # type: ignore[call-arg]

    def test_requires_total_tokens(self) -> None:
        with pytest.raises(ValidationError):
            EmbedUsage()  # type: ignore[call-arg]


class TestEmbedResultUsageField:
    """``EmbedResult.usage`` is optional, defaults ``None``, back-compatible."""

    def test_existing_constructor_shape_still_valid_defaults_none(self) -> None:
        # THE back-compat pin: the exact pre-seam constructor call keeps
        # working, and the new field silently defaults to "not reported".
        result = EmbedResult(vectors=[[0.0] * 8], dim=8)
        assert result.usage is None

    def test_carries_usage_when_provided(self) -> None:
        usage = EmbedUsage(total_tokens=SAMPLE_BILLED_TOKENS)
        result = EmbedResult(vectors=[[0.0] * 8], dim=8, usage=usage)
        assert result.usage == EmbedUsage(total_tokens=SAMPLE_BILLED_TOKENS)

    def test_still_rejects_extra_fields(self) -> None:
        # Guard: widening the model must not loosen extra="forbid".
        with pytest.raises(ValidationError):
            EmbedResult(vectors=[], dim=8, tokens=SAMPLE_BILLED_TOKENS)  # type: ignore[call-arg]


class TestVoyageContextUsageFlatPath:
    """``embed_documents`` reports the exact wire-served bill for the call."""

    async def test_usage_equals_served_total(self) -> None:
        recorder = _UsageContextTransport()
        embedder = _make_context_embedder(recorder.transport())
        result = await embedder.embed_documents(FLAT_TEXTS)
        # The bill is what the PROVIDER said across all 200s of this call —
        # readable only from the wire (the mock's meter differs from the
        # client tokenizer by construction).
        assert result.usage == EmbedUsage(total_tokens=sum(recorder.served_totals))
        assert result.usage is not None  # (narrows the Optional for the bound below)
        assert result.usage.total_tokens > 0  # sanity: real text bills tokens

    async def test_empty_call_reports_zero_not_none(self) -> None:
        recorder = _UsageContextTransport()
        embedder = _make_context_embedder(recorder.transport())
        result = await embedder.embed_documents([])
        # Zero requests -> the bill is KNOWABLY zero; a reporting backend says
        # 0, never None (None is reserved for non-reporting backends).
        assert result.usage == EmbedUsage(total_tokens=0)
        assert recorder.served_totals == []

    async def test_unreadable_200_contributes_zero(self) -> None:
        # A 2xx whose body cannot be parsed reports nothing COUNTABLE: usage
        # sums over parsed 200s only, so a fully-degraded call reports 0.
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, content=b"upstream timeout", headers={"content-type": "text/plain"}
            )

        embedder = _make_context_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([FLAT_TEXTS[0]])
        assert result.vectors == [None]
        assert result.usage == EmbedUsage(total_tokens=0)

    async def test_missing_usage_key_contributes_zero(self) -> None:
        # Provider drift: a perfectly valid 200 whose envelope simply lacks
        # the usage object. Embeddings must flow; the uncountable response
        # contributes 0 — and the backend still REPORTS (0), it does not
        # degrade to a non-reporting None.
        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            inputs: list[list[str]] = body["inputs"]
            payload = _context_envelope(inputs, CONTEXT_DIM, 0)
            del payload["usage"]
            return httpx.Response(200, json=payload)

        embedder = _make_context_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([FLAT_TEXTS[0]])
        assert result.vectors[0] is not None  # the embedding parse is unaffected
        assert result.usage == EmbedUsage(total_tokens=0)


class TestVoyageContextUsageGroupedPath:
    """``embed_document_chunks`` conserves the served bill across per-doc results."""

    async def test_per_doc_usage_conserves_served_totals(self) -> None:
        recorder = _UsageContextTransport()
        embedder = _make_context_embedder(recorder.transport())
        results = await embedder.embed_document_chunks([DOC_RUNBOOK, DOC_POLICY])
        # The contextualized backend ALWAYS reports (possibly 0) — never None.
        assert all(result.usage is not None for result in results)
        # Conservation: summing per-doc usage reproduces exactly what the
        # provider billed — no double counting, no dropped tokens. This is the
        # contract downstream cost accounting sums against.
        summed = sum(result.usage.total_tokens for result in results if result.usage is not None)
        assert summed == sum(recorder.served_totals)

    async def test_fallback_attributes_usage_exactly_per_doc(self) -> None:
        poison_chunk = DOC_RUNBOOK[0]
        served_inputs: list[list[list[str]]] = []
        served_totals: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            inputs: list[list[str]] = body["inputs"]
            if any(poison_chunk in chunk for doc in inputs for chunk in doc):
                # 400 errors BEFORE billing: nothing served, nothing recorded.
                return httpx.Response(400, json={"detail": "invalid input"})
            total = _tokens_billed(inputs)
            served_inputs.append(inputs)
            served_totals.append(total)
            return httpx.Response(200, json=_context_envelope(inputs, CONTEXT_DIM, total))

        embedder = _make_context_embedder(httpx.MockTransport(handler))
        docs = [DOC_POLICY, DOC_RUNBOOK, DOC_SINGLE]  # poison in the MIDDLE
        results = await embedder.embed_document_chunks(docs)

        # The 400ed doc billed nothing: a reporting backend says exactly 0.
        assert results[1].usage == EmbedUsage(total_tokens=0)
        # Docs resolved by their OWN dedicated request(s) get exact
        # measurement, not attribution: their usage is the served total of the
        # single-doc 200 request(s) that produced them.
        single_doc_totals = {
            inputs[0][0]: total
            for inputs, total in zip(served_inputs, served_totals, strict=True)
            if len(inputs) == 1
        }
        assert results[0].usage == EmbedUsage(total_tokens=single_doc_totals[DOC_POLICY[0]])
        assert results[2].usage == EmbedUsage(total_tokens=single_doc_totals[DOC_SINGLE[0]])
        # And the call-level conservation still holds.
        summed = sum(result.usage.total_tokens for result in results if result.usage is not None)
        assert summed == sum(served_totals)

    async def test_billed_tokens_counted_even_when_vectors_quarantined(self) -> None:
        # "Billed" is not "succeeded": a parsed 200 whose vectors are later
        # quarantined (NaN) was still paid for — its usage MUST be counted.
        nan_vector = [float("nan")] + [0.1] * (CONTEXT_DIM - 1)
        billed = _tokens_billed([DOC_POLICY])

        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            inputs: list[list[str]] = body["inputs"]
            data = [
                {
                    "index": doc_index,
                    "data": [
                        {"index": chunk_index, "embedding": nan_vector}
                        for chunk_index, _chunk in enumerate(chunks)
                    ],
                }
                for doc_index, chunks in enumerate(inputs)
            ]
            payload = json.dumps(
                {"data": data, "usage": {"total_tokens": billed}}, allow_nan=True
            )
            return httpx.Response(
                200, content=payload.encode(), headers={"content-type": "application/json"}
            )

        embedder = _make_context_embedder(httpx.MockTransport(handler))
        results = await embedder.embed_document_chunks([DOC_POLICY])
        assert results[0].vectors == [None, None]  # quarantined…
        assert results[0].usage == EmbedUsage(total_tokens=billed)  # …but billed

    async def test_partial_mismatch_fallback_conserves_grand_total(self) -> None:
        # A combined 200 for docs A,B,C is doc-count-correct but doc B's inner
        # chunk count is short -> B alone is unmappable there and gets rescued
        # by its own dedicated fallback request (a clean 200 with its own
        # bill). BOTH parsed 200s were really billed ("billed != succeeded"),
        # so the per-doc usages must conserve the GRAND total: the combined
        # request's FULL bill plus the fallback's. Silently discarding B's
        # abandoned share of the combined bill under-counts real spend. How
        # that share is redistributed (folded into B, or spread over A/C) is
        # deliberately unpinned — only conservation is the contract.
        mismatch_marker = DOC_RUNBOOK[0]
        served_totals: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            inputs: list[list[str]] = body["inputs"]
            total = _tokens_billed(inputs)
            served_totals.append(total)
            payload = _context_envelope(inputs, CONTEXT_DIM, total)
            if len(inputs) > 1:
                # Only the COMBINED request mutilates B; B's dedicated
                # fallback request is served clean, with its own usage.
                for position, doc in enumerate(inputs):
                    if any(mismatch_marker in chunk for chunk in doc):
                        payload["data"][position]["data"] = payload["data"][position]["data"][:-1]
            return httpx.Response(200, json=payload)

        embedder = _make_context_embedder(httpx.MockTransport(handler))
        docs = [DOC_POLICY, DOC_RUNBOOK, DOC_SINGLE]  # B (the mismatch) in the MIDDLE
        results = await embedder.embed_document_chunks(docs)
        # The fallback rescued B: every doc ends fully embedded.
        for result, chunks in zip(results, docs, strict=True):
            assert len(result.vectors) == len(chunks)
            assert all(vector is not None for vector in result.vectors)
        # Both the combined 200 and (at least) B's dedicated 200 were served.
        assert len(served_totals) >= 2
        # Conservation of the grand total across ALL parsed 200s of the call.
        assert all(result.usage is not None for result in results)
        summed = sum(result.usage.total_tokens for result in results if result.usage is not None)
        assert summed == sum(served_totals)

    async def test_dedicated_fallback_mismatch_bills_despite_all_none(self) -> None:
        # EVERY response (combined and dedicated fallback alike) is
        # chunk-count-short: the doc is never mappable and ends all-None —
        # but each parsed 200 along the way was still billed, and every one
        # of those bills is counted.
        served_totals: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            inputs: list[list[str]] = body["inputs"]
            total = _tokens_billed(inputs)
            served_totals.append(total)
            payload = _context_envelope(inputs, CONTEXT_DIM, total)
            payload["data"][0]["data"] = payload["data"][0]["data"][:-1]
            return httpx.Response(200, json=payload)

        embedder = _make_context_embedder(httpx.MockTransport(handler))
        results = await embedder.embed_document_chunks([DOC_POLICY])
        assert results[0].vectors == [None, None]  # never mappable…
        assert len(served_totals) >= 1
        # …but "billed != succeeded": every parsed 200's bill is counted.
        assert results[0].usage == EmbedUsage(total_tokens=sum(served_totals))


class TestNonReportingBackendsDefaultNone:
    """Cloud + TEI results carry ``usage is None`` — population is a later cycle.

    Their construction sites are byte-for-byte the shapes their own contract
    suites use: proving the new field costs existing backends NO code change.
    """

    async def test_voyage_cloud_usage_is_none_even_though_wire_carries_it(self) -> None:
        # The REAL /v1/embeddings response includes usage.total_tokens — the
        # fixture serves it faithfully. This cycle deliberately does not read
        # it: None keeps the backend honest ("not reported") rather than
        # half-populated.
        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            texts: list[str] = body["input"]
            data = [{"embedding": _unit_vector(float(i), CLOUD_DIM)} for i in range(len(texts))]
            usage_total = _tokens_billed([[text] for text in texts])
            return httpx.Response(200, json={"data": data, "usage": {"total_tokens": usage_total}})

        embedder = VoyageCloudEmbedder(
            api_url=CLOUD_API_URL,
            api_key=API_KEY,
            model=CLOUD_MODEL,
            dim=CLOUD_DIM,
            output_dimension=CLOUD_DIM,
            concurrency=2,
            transport=httpx.MockTransport(handler),
        )
        result = await embedder.embed_documents([FLAT_TEXTS[0]])
        assert isinstance(result, EmbedResult)
        assert result.vectors[0] is not None  # embedding path unaffected
        assert result.usage is None

    async def test_tei_usage_is_none(self) -> None:
        # TEI's bare-list wire carries NO usage object at all — None is the
        # only honest value it can ever report.
        def handler(request: httpx.Request) -> httpx.Response:
            body: dict[str, Any] = json.loads(request.content.decode())
            inputs: list[str] = body["inputs"]
            vectors = [_unit_vector(float(i), TEI_DIM) for i in range(len(inputs))]
            return httpx.Response(200, json=vectors)

        embedder = TEIEmbedder(
            base_url=TEI_BASE_URL,
            endpoint=TEI_ENDPOINT,
            api_key=API_KEY,
            dim=TEI_DIM,
            max_input_tokens=TEI_MAX_INPUT_TOKENS,
            concurrency=2,
            transport=httpx.MockTransport(handler),
        )
        result = await embedder.embed_documents([FLAT_TEXTS[0]])
        assert isinstance(result, EmbedResult)
        assert result.vectors[0] is not None
        assert result.usage is None


class TestFakeEmbedderUsage:
    """The shipped fake reports deterministic usage: its own count_tokens sums."""

    async def test_flat_usage_is_count_tokens_sum(self) -> None:
        embedder = FakeEmbedder()
        result = await embedder.embed_documents(FLAT_TEXTS)
        # The fake's bill is its own public count_tokens — the one shared
        # source of truth a downstream cost test can recompute against.
        expected_total = sum(embedder.count_tokens(FLAT_TEXTS))
        assert result.usage == EmbedUsage(total_tokens=expected_total)

    async def test_usage_is_deterministic_across_instances(self) -> None:
        first = await FakeEmbedder().embed_documents(FLAT_TEXTS)
        second = await FakeEmbedder().embed_documents(FLAT_TEXTS)
        assert first.usage == second.usage
        assert first.usage is not None

    async def test_failed_inputs_still_billed(self) -> None:
        # Post-billing failure semantics (like a real quarantined vector): a
        # fail_inputs text still counts toward the deterministic bill.
        embedder = FakeEmbedder(fail_inputs={FLAT_TEXTS[1]})
        result = await embedder.embed_documents(FLAT_TEXTS)
        assert result.vectors[1] is None
        expected_total = sum(embedder.count_tokens(FLAT_TEXTS))
        assert result.usage == EmbedUsage(total_tokens=expected_total)

    async def test_grouped_usage_is_exact_per_doc(self) -> None:
        # Offline, the fake CAN measure per doc — so it must: each per-doc
        # result bills exactly that doc's chunks (conservation follows).
        embedder = FakeEmbedder()
        docs = [DOC_RUNBOOK, DOC_POLICY]
        results = await embedder.embed_document_chunks(docs)
        for result, chunks in zip(results, docs, strict=True):
            assert result.usage == EmbedUsage(total_tokens=sum(embedder.count_tokens(chunks)))

    async def test_empty_call_reports_zero_not_none(self) -> None:
        embedder = FakeEmbedder()
        result = await embedder.embed_documents([])
        # The fake always reports; an empty batch bills exactly zero.
        assert result.usage == EmbedUsage(total_tokens=0)
