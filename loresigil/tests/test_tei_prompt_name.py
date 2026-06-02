"""Contract tests for TEI asymmetric prompt_name support (feat-tei-prompt-name).

GROUP A — new behavior (must FAIL red on current TEIEmbedder):
  A1. document_prompt_name carried into embed_documents POST body.
  A2. query_prompt_name carried into embed_query POST body.
  A3. probe() raises (does NOT swallow) when the endpoint 422s "prompt not found".
  A4. Factory EmbeddingConfig accepts and threads prompt name fields to TEIEmbedder.

GROUP B — regression guards (must STAY green now and after implementation):
  B1. VoyageCloudEmbedder wire contract: input_type present, prompt_name absent.
  B2. TEIEmbedder with no prompt names sends exactly {"inputs": [...]}, no prompt_name.

All HTTP is served by offline httpx.MockTransport — the live TEI box is never hit.

Adversarial pre-flight rationale (see checklist at module end):

  document-prompt-sent:   A1 — captures real POST body and asserts key presence.
  query-prompt-sent:       A2 — same via embed_query path.
  no-prompt-when-None:    B2 — exact body check; "prompt_name" key must be absent.
  bad-prompt-at-startup:  A3 — 422 from a "bogus" prompt_name; probe() must raise,
                               NOT swallow into None (the ResilientEmbedder 422 trap).
  cloud-unchanged:         B1 — captures cloud POST body; input_type present,
                               prompt_name completely absent.
  config-fields-accepted:  A4 — EmbeddingConfig(extra="forbid") must accept the new
                               fields; today it raises ValidationError on them.
  loremaster-plumbing:    (in test_embedding_prompt_name.py / test_config_prompt_name.py)
"""

from __future__ import annotations

import json
import math

import httpx
import pytest
from loresigil.factory import EmbeddingConfig, make_embedder
from loresigil.tei import TEIEmbedder
from loresigil.voyage_cloud import VoyageCloudEmbedder

# ---------------------------------------------------------------------------
# Shared constants — values taken from the verified live deployment config.
# ---------------------------------------------------------------------------

BASE_URL: str = "http://embedder.test:8080"
EMBED_ENDPOINT: str = "/embed"
API_KEY: str = "test-bearer-key-deadbeef"
TEI_DIM: int = 2048
TEI_MAX_INPUT_TOKENS: int = 8192

# The exact prompt names the live TEI endpoint has configured (from the spec).
DOCUMENT_PROMPT_NAME: str = "document"
QUERY_PROMPT_NAME: str = "query"

# Real semantically meaningful sentence (13 tokens, within cap).
SENTENCE: str = (
    "The quarterly safety report summarizes incident rates across all warehouse facilities."
)

# Voyage cloud constants (mirrors test_voyage_cloud.py).
CLOUD_API_URL: str = "https://api.voyageai.com/v1/embeddings"
CLOUD_API_KEY: str = "voyage-test-key-cafebabe"
CLOUD_MODEL: str = "voyage-4-large"
CLOUD_DIM: int = 2048

# Factory env var for tests.
_TEI_KEY_ENV: str = "LORE_TEI_PROMPT_TEST_KEY"
_TEI_KEY_VALUE: str = "tei-secret-prompt-tests"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _unit_vector(seed: float) -> list[float]:
    """Finite, L2-normalized TEI_DIM vector built independently of the impl."""
    raw = [seed + index * 1e-6 for index in range(TEI_DIM)]
    norm = math.sqrt(sum(component * component for component in raw))
    return [component / norm for component in raw]


class _TEIRecordingTransport:
    """httpx.MockTransport that records every request body (bare list response)."""

    def __init__(self) -> None:
        self.bodies: list[dict] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            self.bodies.append(body)
            inputs: list[str] = body["inputs"]
            vectors = [_unit_vector(float(i)) for i in range(len(inputs))]
            return httpx.Response(200, json=vectors)

        return httpx.MockTransport(handler)


class _CloudRecordingTransport:
    """httpx.MockTransport that records cloud request bodies (data-envelope response)."""

    def __init__(self) -> None:
        self.bodies: list[dict] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            self.bodies.append(body)
            inputs = body["input"]
            data = [{"embedding": _unit_vector(float(i))} for i in range(len(inputs))]
            return httpx.Response(200, json={"data": data})

        return httpx.MockTransport(handler)


def _make_tei_embedder(
    transport: httpx.MockTransport,
    document_prompt_name: str | None = None,
    query_prompt_name: str | None = None,
) -> TEIEmbedder:
    """Construct a TEIEmbedder with optional prompt names, backed by an offline transport."""
    return TEIEmbedder(
        base_url=BASE_URL,
        endpoint=EMBED_ENDPOINT,
        api_key=API_KEY,
        dim=TEI_DIM,
        max_input_tokens=TEI_MAX_INPUT_TOKENS,
        concurrency=2,
        transport=transport,
        document_prompt_name=document_prompt_name,
        query_prompt_name=query_prompt_name,
    )


def _make_cloud_embedder(transport: httpx.MockTransport) -> VoyageCloudEmbedder:
    """Construct a VoyageCloudEmbedder backed by an offline transport."""
    return VoyageCloudEmbedder(
        api_url=CLOUD_API_URL,
        api_key=CLOUD_API_KEY,
        model=CLOUD_MODEL,
        dim=CLOUD_DIM,
        output_dimension=CLOUD_DIM,
        concurrency=2,
        transport=transport,
    )


# ---------------------------------------------------------------------------
# GROUP A: New behavior — MUST FAIL RED on current code
# ---------------------------------------------------------------------------


class TestTEIDocumentPromptName:
    """A1 — embed_documents posts prompt_name="document" when configured.

    This is a GROUP A new-behavior test. It MUST fail red on the current
    TEIEmbedder because the constructor does not accept document_prompt_name and
    _post_embed never includes prompt_name in its body.
    """

    async def test_document_prompt_name_appears_in_post_body(self) -> None:
        """embed_documents POSTs prompt_name matching the configured document prompt."""
        # Arrange: embedder configured with the live endpoint's document prompt.
        recorder = _TEIRecordingTransport()
        embedder = _make_tei_embedder(
            recorder.transport(),
            document_prompt_name=DOCUMENT_PROMPT_NAME,
        )

        # Act: embed a realistic document text.
        await embedder.embed_documents([SENTENCE])

        # Assert: the captured POST body includes prompt_name with the configured value.
        assert recorder.bodies, "no POST request was sent"
        body = recorder.bodies[0]
        # The TEI /embed endpoint uses prompt_name to select the asymmetric prompt.
        assert "prompt_name" in body, (
            f"expected 'prompt_name' key in POST body; got keys: {list(body.keys())}"
        )
        assert body["prompt_name"] == DOCUMENT_PROMPT_NAME

    async def test_document_prompt_name_does_not_affect_inputs_key(self) -> None:
        """The inputs list is still sent alongside the prompt_name."""
        recorder = _TEIRecordingTransport()
        embedder = _make_tei_embedder(
            recorder.transport(),
            document_prompt_name=DOCUMENT_PROMPT_NAME,
        )
        await embedder.embed_documents([SENTENCE])
        body = recorder.bodies[0]
        assert isinstance(body["inputs"], list)
        assert body["inputs"] == [SENTENCE]


class TestTEIQueryPromptName:
    """A2 — embed_query posts prompt_name="query" when configured.

    GROUP A new-behavior test: must fail red on current code.
    """

    async def test_query_prompt_name_appears_in_post_body(self) -> None:
        """embed_query POSTs prompt_name matching the configured query prompt."""
        recorder = _TEIRecordingTransport()
        embedder = _make_tei_embedder(
            recorder.transport(),
            query_prompt_name=QUERY_PROMPT_NAME,
        )

        await embedder.embed_query(SENTENCE)

        assert recorder.bodies, "no POST request was sent"
        body = recorder.bodies[0]
        assert "prompt_name" in body, (
            f"expected 'prompt_name' key in embed_query POST body; got: {list(body.keys())}"
        )
        assert body["prompt_name"] == QUERY_PROMPT_NAME

    async def test_query_prompt_name_differs_from_document_prompt_name(self) -> None:
        """When both prompt names are configured, each path sends its own value.

        This verifies the asymmetry: embedding a document and embedding a query
        each use their distinct server-side prompt, which is the whole point of
        the feature.
        """
        recorder = _TEIRecordingTransport()
        embedder = _make_tei_embedder(
            recorder.transport(),
            document_prompt_name=DOCUMENT_PROMPT_NAME,
            query_prompt_name=QUERY_PROMPT_NAME,
        )

        # Embed one document and one query; both paths hit the same mock.
        await embedder.embed_documents([SENTENCE])
        await embedder.embed_query(SENTENCE)

        assert len(recorder.bodies) >= 2, "expected at least two POST requests"
        doc_body = recorder.bodies[0]
        query_body = recorder.bodies[1]

        # Document path uses DOCUMENT_PROMPT_NAME; query path uses QUERY_PROMPT_NAME.
        assert doc_body["prompt_name"] == DOCUMENT_PROMPT_NAME
        assert query_body["prompt_name"] == QUERY_PROMPT_NAME
        # They must be distinct values — same prompt defeats the whole purpose.
        assert doc_body["prompt_name"] != query_body["prompt_name"]


class TestTEIProbeValidatesPromptName:
    """A3 — probe() raises when the configured prompt_name is rejected (HTTP 422).

    HAZARD (from spec): ResilientEmbedder treats 422 as an over-length signal and
    silently sub-splits, which would null the entire corpus if the 422 is actually
    "unknown prompt". The fix: probe() must call the embedding endpoint directly
    (bypassing the resilient wrapper) with the configured prompt_name, so a bad
    prompt surfaces at startup rather than silently corrupting every embedding.

    GROUP A new-behavior test: must fail red on current code.
    """

    async def test_probe_raises_on_422_unknown_prompt(self) -> None:
        """probe() must raise when the endpoint returns 422 for an unknown prompt.

        The endpoint's 422 body mirrors the actual TEI error format for an
        unrecognised prompt_name value.
        """
        # The real TEI 422 body when an unknown prompt is sent.
        tei_422_body = {
            "error": (
                "Prompt 'bogus' not found. Available prompts: [\"query\", \"document\"]"
            ),
            "error_type": "Validation",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            # Only 422 if a bad prompt_name is sent; otherwise 200.
            if body.get("prompt_name") == "bogus":
                return httpx.Response(422, json=tei_422_body)
            vectors = [_unit_vector(0.0) for _ in body["inputs"]]
            return httpx.Response(200, json=vectors)

        embedder = _make_tei_embedder(
            httpx.MockTransport(handler),
            query_prompt_name="bogus",
        )

        # probe() must NOT return silently — it must raise so the startup gate
        # refuses to start rather than silently nulling the entire corpus.
        with pytest.raises(Exception) as exc_info:
            await embedder.probe()

        # The exception must not be the "prompt not found" swallowed into None;
        # it must propagate up so the caller (startup gate) sees it.
        # We allow any exception subtype — RuntimeError, HTTPStatusError, etc.
        assert exc_info.value is not None

    async def test_probe_with_valid_prompt_name_does_not_raise(self) -> None:
        """probe() with a valid prompt_name succeeds normally."""
        recorder = _TEIRecordingTransport()
        embedder = _make_tei_embedder(
            recorder.transport(),
            query_prompt_name=QUERY_PROMPT_NAME,
        )
        # Must not raise — the prompt name is recognised by the endpoint.
        dim = await embedder.probe()
        assert dim == TEI_DIM

    async def test_probe_sends_configured_prompt_name_to_endpoint(self) -> None:
        """probe() calls the endpoint with the configured query_prompt_name.

        This is the seam-level check: the live probe path (not the resilient
        wrapper path) must carry the prompt_name so that a bad prompt is caught
        at startup, not swallowed silently.
        """
        recorder = _TEIRecordingTransport()
        embedder = _make_tei_embedder(
            recorder.transport(),
            query_prompt_name=QUERY_PROMPT_NAME,
        )
        await embedder.probe()
        # probe() must have fired at least one request with the query prompt name.
        probe_bodies = recorder.bodies
        assert probe_bodies, "probe() sent no request"
        # At least one probe request carries the configured prompt name.
        prompt_names_sent = [b.get("prompt_name") for b in probe_bodies]
        assert QUERY_PROMPT_NAME in prompt_names_sent, (
            f"probe() did not send query_prompt_name={QUERY_PROMPT_NAME!r}; "
            f"prompt_names seen: {prompt_names_sent}"
        )


class TestFactoryPromptNameWiring:
    """A4 — EmbeddingConfig accepts prompt name fields and they reach TEIEmbedder.

    GROUP A new-behavior test: EmbeddingConfig has extra="forbid", so today
    passing query_prompt_name / document_prompt_name raises ValidationError.
    After the feature, it must accept them and the factory must thread them
    through to the TEIEmbedder constructor.
    """

    @pytest.fixture(autouse=True)
    def _set_tei_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(_TEI_KEY_ENV, _TEI_KEY_VALUE)

    def test_embedding_config_accepts_query_prompt_name(self) -> None:
        """EmbeddingConfig(extra='forbid') must accept query_prompt_name without error."""
        # Today this raises pydantic.ValidationError because the field is unknown.
        config = EmbeddingConfig(
            backend="tei",
            base_url="http://tei.example:8080",
            endpoint="/embed",
            dim=TEI_DIM,
            max_input_tokens=TEI_MAX_INPUT_TOKENS,
            api_key_env=_TEI_KEY_ENV,
            query_prompt_name=QUERY_PROMPT_NAME,  # type: ignore[call-arg]
        )
        assert config.query_prompt_name == QUERY_PROMPT_NAME  # type: ignore[attr-defined]

    def test_embedding_config_accepts_document_prompt_name(self) -> None:
        """EmbeddingConfig(extra='forbid') must accept document_prompt_name without error."""
        config = EmbeddingConfig(
            backend="tei",
            base_url="http://tei.example:8080",
            endpoint="/embed",
            dim=TEI_DIM,
            max_input_tokens=TEI_MAX_INPUT_TOKENS,
            api_key_env=_TEI_KEY_ENV,
            document_prompt_name=DOCUMENT_PROMPT_NAME,  # type: ignore[call-arg]
        )
        assert config.document_prompt_name == DOCUMENT_PROMPT_NAME  # type: ignore[attr-defined]

    def test_embedding_config_prompt_names_default_to_none(self) -> None:
        """Both prompt name fields default to None (backward-compatible opt-in)."""
        config = EmbeddingConfig(
            backend="tei",
            base_url="http://tei.example:8080",
            api_key_env=_TEI_KEY_ENV,
        )
        # None means "don't send prompt_name" — preserving the current no-prompt behavior.
        assert config.query_prompt_name is None  # type: ignore[attr-defined]
        assert config.document_prompt_name is None  # type: ignore[attr-defined]

    async def test_factory_threads_prompt_names_to_tei_embedder(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """make_embedder carries prompt names from config into the TEIEmbedder.

        Verified by recording the actual POST body the constructed embedder sends
        — not by introspecting constructor arguments (which would be a white-box
        tautology).
        """
        recorder = _TEIRecordingTransport()
        # Patch httpx.AsyncClient so the factory-built embedder uses the recorder.
        # We do this by constructing via factory then replacing _client.
        config = EmbeddingConfig(
            backend="tei",
            base_url=BASE_URL,
            endpoint=EMBED_ENDPOINT,
            dim=TEI_DIM,
            max_input_tokens=TEI_MAX_INPUT_TOKENS,
            api_key_env=_TEI_KEY_ENV,
            query_prompt_name=QUERY_PROMPT_NAME,  # type: ignore[call-arg]
            document_prompt_name=DOCUMENT_PROMPT_NAME,  # type: ignore[call-arg]
        )
        embedder = make_embedder(config)
        assert isinstance(embedder, TEIEmbedder)

        # Wire in the recording transport so no network is hit.
        embedder._client = httpx.AsyncClient(
            base_url=BASE_URL,
            transport=recorder.transport(),
            headers={"Authorization": f"Bearer {_TEI_KEY_VALUE}"},
        )

        # Embed a document and verify the prompt_name flows through.
        await embedder.embed_documents([SENTENCE])
        assert recorder.bodies, "no POST was sent after factory construction"
        body = recorder.bodies[0]
        assert body.get("prompt_name") == DOCUMENT_PROMPT_NAME, (
            f"factory-built embedder did not send document_prompt_name; body: {body}"
        )


# ---------------------------------------------------------------------------
# GROUP B: Regression guards — MUST PASS NOW and stay green after the feature
# ---------------------------------------------------------------------------


class TestVoyageCloudUnchangedGuard:
    """B1 — REGRESSION GUARD: VoyageCloudEmbedder wire contract is unchanged.

    The Voyage cloud embedder uses input_type for asymmetry and MUST NOT gain a
    prompt_name field. This test pins the exact wire shape so any accidental
    modification of voyage_cloud.py causes immediate, visible failure.
    """

    async def test_document_path_sends_input_type_document_and_no_prompt_name(
        self,
    ) -> None:
        """embed_documents sends input_type='document' and NO prompt_name key."""
        recorder = _CloudRecordingTransport()
        embedder = _make_cloud_embedder(recorder.transport())

        await embedder.embed_documents([SENTENCE])

        assert recorder.bodies, "no POST request was sent"
        body = recorder.bodies[0]
        # Cloud asymmetry uses input_type, not prompt_name.
        assert body["input_type"] == "document", (
            f"expected input_type='document'; got {body.get('input_type')!r}"
        )
        # The cloud path must NEVER send prompt_name — that is TEI-only.
        assert "prompt_name" not in body, (
            f"VoyageCloudEmbedder sent unexpected 'prompt_name' key: {body['prompt_name']!r}"
        )

    async def test_query_path_sends_input_type_query_and_no_prompt_name(
        self,
    ) -> None:
        """embed_query sends input_type='query' and NO prompt_name key."""
        recorder = _CloudRecordingTransport()
        embedder = _make_cloud_embedder(recorder.transport())

        await embedder.embed_query(SENTENCE)

        assert recorder.bodies, "no POST request was sent"
        body = recorder.bodies[0]
        assert body["input_type"] == "query", (
            f"expected input_type='query'; got {body.get('input_type')!r}"
        )
        assert "prompt_name" not in body, (
            f"VoyageCloudEmbedder sent unexpected 'prompt_name' key: {body['prompt_name']!r}"
        )

    async def test_cloud_body_contains_model_and_output_dimension(self) -> None:
        """Full cloud wire shape: input, model, input_type, output_dimension all present."""
        recorder = _CloudRecordingTransport()
        embedder = _make_cloud_embedder(recorder.transport())

        await embedder.embed_documents([SENTENCE])

        body = recorder.bodies[0]
        # Pin the full set of keys the cloud API requires.
        assert "input" in body
        assert "model" in body
        assert "output_dimension" in body
        assert body["output_dimension"] == CLOUD_DIM
        # Guard: no TEI-specific keys have leaked into the cloud shape.
        assert "inputs" not in body  # TEI uses "inputs"; cloud uses "input"
        assert "prompt_name" not in body


class TestTEIBackwardCompatGuard:
    """B2 — REGRESSION GUARD: TEIEmbedder with no prompt names is byte-identical to today.

    When query_prompt_name and document_prompt_name are both None (the default),
    the POST body must be exactly {"inputs": [...]} — no prompt_name key at all.
    This pins the opt-in contract: the feature is a no-op unless explicitly
    configured.
    """

    async def test_embed_documents_without_prompt_names_sends_exact_inputs_only(
        self,
    ) -> None:
        """No-prompt-config embed_documents body is exactly {'inputs': [...]}."""
        recorder = _TEIRecordingTransport()
        # Construct with NO prompt names — the default None values.
        embedder = TEIEmbedder(
            base_url=BASE_URL,
            endpoint=EMBED_ENDPOINT,
            api_key=API_KEY,
            dim=TEI_DIM,
            max_input_tokens=TEI_MAX_INPUT_TOKENS,
            concurrency=2,
            transport=recorder.transport(),
        )

        await embedder.embed_documents([SENTENCE])

        assert recorder.bodies, "no POST request was sent"
        body = recorder.bodies[0]

        # Exact body: only "inputs", nothing else. Any extra key is a regression.
        assert set(body.keys()) == {"inputs"}, (
            f"expected body keys {{\"inputs\"}} only; got {set(body.keys())}"
        )
        assert body["inputs"] == [SENTENCE]
        # The prompt_name key must be completely absent — not None, not empty string.
        assert "prompt_name" not in body

    async def test_embed_query_without_prompt_names_sends_exact_inputs_only(
        self,
    ) -> None:
        """No-prompt-config embed_query body is exactly {'inputs': ['<text>']}."""
        recorder = _TEIRecordingTransport()
        embedder = TEIEmbedder(
            base_url=BASE_URL,
            endpoint=EMBED_ENDPOINT,
            api_key=API_KEY,
            dim=TEI_DIM,
            max_input_tokens=TEI_MAX_INPUT_TOKENS,
            concurrency=2,
            transport=recorder.transport(),
        )

        await embedder.embed_query(SENTENCE)

        assert recorder.bodies, "no POST request was sent"
        body = recorder.bodies[0]
        assert set(body.keys()) == {"inputs"}, (
            f"expected body keys {{\"inputs\"}} only; got {set(body.keys())}"
        )
        assert "prompt_name" not in body
