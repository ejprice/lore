"""Contract tests for ``loresigil.tei.TEIEmbedder`` — self-hosted voyage-4-nano.

The verified TEI contract:

* ``POST {base_url}{endpoint}`` with body ``{"inputs": [text, ...]}`` — NO
  ``truncate`` field (the server runs ``--auto-truncate false``; over-length is a
  hard 422, never silently truncated).
* Bearer auth on every request (``Authorization: Bearer <key>``).
* Response is a **bare** ``[[float×2048], ...]`` (not wrapped in ``{"data": ...}``)
  — L2-normalized unit vectors.
* ``dim == 2048``, ``max_input_tokens == 8192``, ``normalized is True``.
* Over-8192-token inputs are **pre-split client-side** (the ≤8192 pre-check) so
  the whole text is NEVER sent — the 422 sub-split in ``resilient`` is only the
  backstop.
* ``probe()`` embeds a sentinel and returns the observed dimension; it raises if
  the endpoint is unreachable.

All HTTP is served by an offline ``httpx.MockTransport`` — the live ``TEI``
box is reserved for the deploy healthcheck. Token counting uses the real pinned
tokenizer (offline). The unit-norm oracle is an independent ``math.hypot`` here,
not the server's claim.
"""

from __future__ import annotations

import json
import logging
import math

import httpx
import pytest
from loresigil.base import Embedder, EmbedResult
from loresigil.tei import TEIEmbedder
from loresigil.tokens import VoyageTokenCounter

# The dotted logger name the TEI embedder emits under (module ``__name__``).
TEI_LOGGER = "loresigil.tei"

BASE_URL: str = "http://embedder.test:8080"
EMBED_ENDPOINT: str = "/embed"
API_KEY: str = "test-bearer-key-deadbeef"
TEI_DIM: int = 2048
TEI_MAX_INPUT_TOKENS: int = 8192

# Real warehouse-ops prose; 13 tokens per sentence (verified offline).
SENTENCE: str = (
    "The quarterly safety report summarizes incident rates across all warehouse facilities. "
)
# unit*750 == 9001 tokens > 8192 (verified) — must be pre-split, never sent whole.
OVER_LIMIT_TEXT: str = SENTENCE * 750


def _unit_vector(seed: float) -> list[float]:
    """Build a finite, L2-normalized 2048-d vector (independent of the impl).

    A constant vector normalized to unit length — its norm is exactly 1.0 by
    construction, so the test's norm assertion is a real check on parsing, not a
    tautology against the server.
    """
    raw = [seed + index * 1e-6 for index in range(TEI_DIM)]
    norm = math.sqrt(sum(component * component for component in raw))
    return [component / norm for component in raw]


class _RecordingTransport:
    """Wrap an httpx.MockTransport handler, recording every request body seen."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.bodies: list[dict[str, object]] = []
        self.inputs_seen: list[list[str]] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            body = json.loads(request.content.decode())
            self.bodies.append(body)
            inputs: list[str] = body["inputs"]
            self.inputs_seen.append(inputs)
            # Bare [[...]] response, one unit vector per input.
            vectors = [_unit_vector(float(index)) for index in range(len(inputs))]
            return httpx.Response(200, json=vectors)

        return httpx.MockTransport(handler)


def _make_embedder(transport: httpx.MockTransport) -> TEIEmbedder:
    """Construct a TEIEmbedder backed by an offline mock transport."""
    return TEIEmbedder(
        base_url=BASE_URL,
        endpoint=EMBED_ENDPOINT,
        api_key=API_KEY,
        dim=TEI_DIM,
        max_input_tokens=TEI_MAX_INPUT_TOKENS,
        concurrency=2,
        transport=transport,
    )


class TestTEIEmbedderAttributes:
    """The embedder reports the verified voyage-4-nano model parameters."""

    def test_is_an_embedder(self) -> None:
        recorder = _RecordingTransport()
        assert isinstance(_make_embedder(recorder.transport()), Embedder)

    def test_reports_verified_parameters(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        assert embedder.dim == TEI_DIM
        assert embedder.max_input_tokens == TEI_MAX_INPUT_TOKENS
        assert embedder.normalized is True
        assert isinstance(embedder.name, str) and embedder.name


class TestTEIRequestShape:
    """The native /embed body is exactly ``{"inputs": [...]}`` — no truncate flag."""

    async def test_body_uses_inputs_key_and_no_truncate(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        await embedder.embed_documents([SENTENCE])
        assert recorder.bodies, "no request was sent"
        body = recorder.bodies[0]
        # Native TEI contract: "inputs" is a list; "truncate" must be ABSENT
        # because the server runs --auto-truncate false (sending truncate:true
        # would silently corrupt embeddings).
        assert isinstance(body["inputs"], list)
        assert "truncate" not in body

    async def test_sends_bearer_authorization(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        await embedder.embed_documents([SENTENCE])
        auth = recorder.requests[0].headers.get("authorization")
        assert auth == f"Bearer {API_KEY}"

    async def test_targets_configured_embed_endpoint(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        await embedder.embed_documents([SENTENCE])
        assert str(recorder.requests[0].url) == f"{BASE_URL}{EMBED_ENDPOINT}"


class TestTEIResponseParsing:
    """A bare ``[[...]]`` of dim-2048 unit vectors is parsed and aligned."""

    async def test_parses_bare_list_of_lists(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        result = await embedder.embed_documents([SENTENCE, SENTENCE + "Extra."])
        assert isinstance(result, EmbedResult)
        assert result.dim == TEI_DIM
        assert len(result.vectors) == 2
        for vector in result.vectors:
            assert vector is not None
            assert len(vector) == TEI_DIM

    async def test_returned_vectors_are_unit_norm(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        result = await embedder.embed_documents([SENTENCE])
        vector = result.vectors[0]
        assert vector is not None
        # Independent oracle: math.hypot, not the server's normalization claim.
        assert math.hypot(*vector) == pytest.approx(1.0, abs=1e-6)

    async def test_embed_query_returns_single_vector(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        vector = await embedder.embed_query(SENTENCE)
        assert len(vector) == TEI_DIM
        assert math.hypot(*vector) == pytest.approx(1.0, abs=1e-6)


class TestTEIPreSplitsOverLengthInputs:
    """An over-8192-token input is split client-side; the whole text is never sent."""

    async def test_over_limit_input_is_never_sent_whole(self) -> None:
        counter = VoyageTokenCounter()
        assert counter.count(OVER_LIMIT_TEXT) > TEI_MAX_INPUT_TOKENS  # genuinely over

        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        result = await embedder.embed_documents([OVER_LIMIT_TEXT])

        # Pre-check guarantee: every individual input the server ever received was
        # within the cap — the raw 9001-token text was split before sending.
        for inputs in recorder.inputs_seen:
            for sent_text in inputs:
                assert counter.count(sent_text) <= TEI_MAX_INPUT_TOKENS
        # And the one input still yields one finite vector (content not dropped).
        assert len(result.vectors) == 1
        assert result.vectors[0] is not None
        assert all(math.isfinite(component) for component in result.vectors[0])


class TestTEIProbe:
    """``probe()`` embeds a sentinel and returns the observed dimension."""

    async def test_probe_returns_observed_dim(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        assert await embedder.probe() == TEI_DIM

    async def test_probe_raises_when_unreachable(self) -> None:
        # An unreachable endpoint -> ConnectError from the transport -> probe must
        # raise (the startup gate refuses to start on this).
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("TEI unreachable")

        embedder = _make_embedder(httpx.MockTransport(handler))
        with pytest.raises(Exception):
            await embedder.probe()

    async def test_probe_ok_logs_observed_dim(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        with caplog.at_level(logging.INFO, logger=TEI_LOGGER):
            await embedder.probe()
        events = [r for r in caplog.records if r.message == "embed.probe.ok"]
        assert len(events) == 1
        assert events[0].levelno == logging.INFO
        assert events[0].observed_dim == TEI_DIM  # type: ignore[attr-defined]

    async def test_probe_unreachable_logs_error_event(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("TEI unreachable")

        embedder = _make_embedder(httpx.MockTransport(handler))
        with caplog.at_level(logging.ERROR, logger=TEI_LOGGER):
            with pytest.raises(Exception):
                await embedder.probe()
        events = [r for r in caplog.records if r.message == "embed.probe.unreachable"]
        assert events, "an unreachable probe must log embed.probe.unreachable at ERROR"
        assert events[0].levelno == logging.ERROR

    async def test_probe_logs_carry_no_secret(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        # The bearer token (API_KEY) must never appear in any probe log line.
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        with caplog.at_level(logging.DEBUG, logger=TEI_LOGGER):
            await embedder.probe()
        for record in caplog.records:
            assert API_KEY not in record.getMessage()
            for value in record.__dict__.values():
                assert not (isinstance(value, str) and API_KEY in value)


class TestTEICountTokens:
    """``count_tokens`` delegates to the exact pinned tokenizer (offline)."""

    def test_count_tokens_matches_pinned_tokenizer(self) -> None:
        recorder = _RecordingTransport()
        embedder = _make_embedder(recorder.transport())
        counter = VoyageTokenCounter()
        texts = [SENTENCE, "Hello world.", ""]
        # Independent oracle: the standalone counter on the same pinned tokenizer.
        assert embedder.count_tokens(texts) == counter.count_tokens(texts)


class TestTEIResilientNonFinite:
    """A non-finite vector from the endpoint is quarantined to None, never stored."""

    async def test_nan_from_endpoint_is_quarantined(self) -> None:
        nan_vector = [float("nan")] + [0.1] * (TEI_DIM - 1)

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            # Real TEI emits a literal ``NaN`` JSON token; the stdlib encoder
            # rejects NaN by default, so serialize with allow_nan=True to faithfully
            # reproduce the on-wire bytes the client must cope with.
            payload = json.dumps([nan_vector for _ in body["inputs"]], allow_nan=True)
            return httpx.Response(
                200, content=payload.encode(), headers={"content-type": "application/json"}
            )

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([SENTENCE])
        # Poison must never be surfaced as a stored vector.
        assert result.vectors == [None]


class TestTEIUntrustedResponseSurface:
    """A short / long / malformed 2xx body degrades to aligned None, never corrupts."""

    async def test_short_response_does_not_crash_returns_aligned_none(self) -> None:
        # Server returns FEWER vectors than inputs. The old stitch loop would
        # IndexError (crash) or mis-map; the embedder must return a result aligned
        # to the inputs with safe Nones and no exception.
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            inputs = body["inputs"]
            # One fewer vector than asked for.
            vectors = [_unit_vector(float(i)) for i in range(max(0, len(inputs) - 1))]
            return httpx.Response(200, json=vectors)

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([SENTENCE, SENTENCE + "B", SENTENCE + "C"])
        assert len(result.vectors) == 3  # aligned to inputs, no crash
        assert result.vectors == [None, None, None]

    async def test_long_response_is_rejected_not_silently_mapped(self) -> None:
        # Server returns MORE vectors than inputs (permuted/padded). Silently
        # mapping would bind arbitrary vectors to the wrong chunks.
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            inputs = body["inputs"]
            vectors = [_unit_vector(float(i)) for i in range(len(inputs) + 2)]
            return httpx.Response(200, json=vectors)

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([SENTENCE, SENTENCE + "B"])
        assert len(result.vectors) == 2
        assert result.vectors == [None, None]

    async def test_wrong_dimension_vector_is_quarantined(self) -> None:
        # A finite but wrong-dimension vector must not be stored under a lying dim.
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            short = [0.1] * (TEI_DIM - 1)
            return httpx.Response(200, json=[short for _ in body["inputs"]])

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([SENTENCE])
        assert result.vectors == [None]
        assert result.dim == TEI_DIM  # the declared dim stays truthful

    async def test_malformed_json_body_degrades_to_none(self) -> None:
        # A 2xx with a non-JSON body would raise JSONDecodeError in parsing; the
        # embedder must degrade to None, not crash the batch.
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, content=b"<html>gateway error</html>", headers={"content-type": "text/html"}
            )

        embedder = _make_embedder(httpx.MockTransport(handler))
        result = await embedder.embed_documents([SENTENCE])
        assert result.vectors == [None]
