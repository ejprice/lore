"""Contract tests for ``loresigil.voyage_cloud.VoyageCloudEmbedder``.

The cloud backend targets ``api.voyageai.com`` and differs from TEI in wire shape:

* Request body: ``{"input": [...], "model": <model>, "input_type": "document"|"query",
  "output_dimension": 2048}``. ``embed_documents`` sends ``input_type="document"``;
  ``embed_query`` sends ``input_type="query"`` (asymmetric retrieval prompting).
* Response: ``{"data": [{"embedding": [...]}, ...]}`` (OpenAI-ish envelope), NOT a
  bare list — the parser must read ``data[].embedding``.
* Server-side auto-truncate is ON, so there is no client pre-split requirement
  (unlike TEI). But the ``isfinite`` quarantine and 429/5xx retry still apply.
* Bearer auth on every request.

All HTTP is an offline ``httpx.MockTransport``. The unit-norm / finiteness oracles
are independent (``math``), not the server's claims.
"""

from __future__ import annotations

import json
import math

import httpx
import pytest
from loresigil.base import Embedder, EmbedResult
from loresigil.voyage_cloud import VoyageCloudEmbedder

API_URL: str = "https://api.voyageai.com/v1/embeddings"
API_KEY: str = "voyage-test-key-cafebabe"
MODEL: str = "voyage-4-large"
CLOUD_DIM: int = 2048

SENTENCE: str = "Embeddings map text into a dense vector space for semantic search."


def _unit_vector(seed: float) -> list[float]:
    """Finite, L2-normalized CLOUD_DIM vector, built independently of the impl."""
    raw = [seed + index * 1e-6 for index in range(CLOUD_DIM)]
    norm = math.sqrt(sum(component * component for component in raw))
    return [component / norm for component in raw]


class _RecordingTransport:
    """httpx.MockTransport that records bodies and serves a ``{"data":[...]}`` envelope."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.bodies: list[dict[str, object]] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            body = json.loads(request.content.decode())
            self.bodies.append(body)
            inputs = body["input"]
            # OpenAI-ish envelope: data[].embedding.
            data = [{"embedding": _unit_vector(float(i))} for i in range(len(inputs))]
            return httpx.Response(200, json={"data": data})

        return httpx.MockTransport(handler)


def _make_embedder(transport: httpx.MockTransport) -> VoyageCloudEmbedder:
    return VoyageCloudEmbedder(
        api_url=API_URL,
        api_key=API_KEY,
        model=MODEL,
        dim=CLOUD_DIM,
        output_dimension=CLOUD_DIM,
        concurrency=2,
        transport=transport,
    )


class TestVoyageCloudAttributes:
    """Reports voyage-4-large parameters and is a real Embedder."""

    def test_is_an_embedder(self) -> None:
        recorder = _RecordingTransport()
        assert isinstance(_make_embedder(recorder.transport()), Embedder)

    def test_reports_parameters(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        assert embedder.dim == CLOUD_DIM
        assert embedder.normalized is True
        assert isinstance(embedder.name, str) and embedder.name


class TestVoyageCloudRequestShape:
    """Body carries input/model/input_type/output_dimension; bearer auth set."""

    async def test_document_path_sends_input_type_document(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        await embedder.embed_documents([SENTENCE])
        body = recorder.bodies[0]
        assert isinstance(body["input"], list)
        assert body["model"] == MODEL
        assert body["input_type"] == "document"
        assert body["output_dimension"] == CLOUD_DIM

    async def test_query_path_sends_input_type_query(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        await embedder.embed_query(SENTENCE)
        body = recorder.bodies[0]
        # Asymmetric prompting: a query is tagged "query", not "document".
        assert body["input_type"] == "query"

    async def test_sends_bearer_authorization(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        await embedder.embed_documents([SENTENCE])
        assert recorder.requests[0].headers.get("authorization") == f"Bearer {API_KEY}"


class TestVoyageCloudResponseParsing:
    """Parses ``data[].embedding`` (not a bare list) and aligns to inputs."""

    async def test_parses_data_embedding_envelope(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        result = await embedder.embed_documents([SENTENCE, SENTENCE + " More."])
        assert isinstance(result, EmbedResult)
        assert result.dim == CLOUD_DIM
        assert len(result.vectors) == 2
        for vector in result.vectors:
            assert vector is not None
            assert len(vector) == CLOUD_DIM
            assert math.hypot(*vector) == pytest.approx(1.0, abs=1e-6)

    async def test_embed_query_returns_single_vector(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        vector = await embedder.embed_query(SENTENCE)
        assert len(vector) == CLOUD_DIM


class TestVoyageCloudResilientNonFinite:
    """A non-finite vector from the cloud is quarantined to None."""

    async def test_nan_is_quarantined(self) -> None:
        nan_vector = [float("nan")] + [0.1] * (CLOUD_DIM - 1)

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            data = [{"embedding": nan_vector} for _ in body["input"]]
            # allow_nan=True reproduces the literal ``NaN`` token a real server can
            # emit; the stdlib encoder rejects NaN by default.
            payload = json.dumps({"data": data}, allow_nan=True)
            return httpx.Response(
                200, content=payload.encode(), headers={"content-type": "application/json"}
            )

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([SENTENCE])
        assert result.vectors == [None]


class TestVoyageCloudRetryAndProbe:
    """429 is retried; probe returns the observed dim or raises when unreachable."""

    async def test_429_then_200_succeeds(self) -> None:
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                return httpx.Response(429, json={"error": "rate limited"})
            body = json.loads(request.content.decode())
            data = [{"embedding": _unit_vector(0.0)} for _ in body["input"]]
            return httpx.Response(200, json={"data": data})

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([SENTENCE])
        assert calls == 2  # retried
        assert result.vectors[0] is not None

    async def test_probe_returns_observed_dim(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        assert await embedder.probe() == CLOUD_DIM

    async def test_probe_raises_when_unreachable(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("voyage unreachable")

        embedder = _make_embedder(httpx.MockTransport(handler))
        with pytest.raises(Exception):
            await embedder.probe()


class TestVoyageCloudUntrustedResponseSurface:
    """A short / long / malformed / wrong-envelope 2xx body degrades to aligned None."""

    async def test_short_response_does_not_crash_returns_aligned_none(self) -> None:
        # data[] shorter than input[] -> mis-mapping / IndexError risk. Must align.
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            inputs = body["input"]
            data = [{"embedding": _unit_vector(float(i))} for i in range(max(0, len(inputs) - 1))]
            return httpx.Response(200, json={"data": data})

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([SENTENCE, SENTENCE + " B", SENTENCE + " C"])
        assert len(result.vectors) == 3
        assert result.vectors == [None, None, None]

    async def test_long_response_is_rejected(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            inputs = body["input"]
            data = [{"embedding": _unit_vector(float(i))} for i in range(len(inputs) + 2)]
            return httpx.Response(200, json={"data": data})

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([SENTENCE, SENTENCE + " B"])
        assert len(result.vectors) == 2
        assert result.vectors == [None, None]

    async def test_wrong_dimension_vector_is_quarantined(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            short = [0.1] * (CLOUD_DIM - 1)
            data = [{"embedding": short} for _ in body["input"]]
            return httpx.Response(200, json={"data": data})

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([SENTENCE])
        assert result.vectors == [None]
        assert result.dim == CLOUD_DIM

    async def test_missing_data_envelope_degrades_to_none(self) -> None:
        # A 2xx body lacking the "data" key would KeyError in the parser; the
        # embedder must degrade to None, not crash.
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"unexpected": "shape"})

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([SENTENCE])
        assert result.vectors == [None]

    async def test_malformed_json_body_degrades_to_none(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, content=b"upstream timeout", headers={"content-type": "text/plain"}
            )

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([SENTENCE])
        assert result.vectors == [None]
