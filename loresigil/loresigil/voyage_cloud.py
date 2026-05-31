"""``VoyageCloudEmbedder`` — api.voyageai.com (voyage-4-large).

Ported from the odoo-code donor's request/retry shape, re-expressed against the
shared :class:`~loresigil.resilient.ResilientEmbedder`. The cloud wire contract:

* Request body: ``{"input": [...], "model": <model>, "input_type":
  "document"|"query", "output_dimension": 2048}`` with a bearer token.
  ``embed_documents`` tags ``input_type="document"``; ``embed_query`` tags
  ``"query"`` (asymmetric retrieval prompting).
* Response: ``{"data": [{"embedding": [...]}, ...]}`` — the parser reads
  ``data[].embedding`` (NOT a bare list, unlike TEI).
* The server auto-truncates over-length inputs, so there is no client pre-split
  requirement; the ``isfinite`` quarantine and 429/5xx retry still apply.
"""

from __future__ import annotations

import httpx

from loresigil.base import Embedder, EmbedResult
from loresigil.batching import build_batches, run_in_windows
from loresigil.resilient import RequestFn, ResilientEmbedder
from loresigil.tokens import VoyageTokenCounter

DEFAULT_API_URL: str = "https://api.voyageai.com/v1/embeddings"
DEFAULT_MODEL: str = "voyage-4-large"
DEFAULT_DIM: int = 2048
DEFAULT_CONCURRENCY: int = 4
DEFAULT_NAME_PREFIX: str = "voyage-cloud:"

# voyage-4 model context; the cloud auto-truncates over this, so it is reported
# for the Embedder contract but not enforced client-side.
DEFAULT_MAX_INPUT_TOKENS: int = 32_000
# Voyage's documented per-request batch ceiling.
_MAX_BATCH_TEXTS: int = 128
_REQUEST_TIMEOUT_S: float = 120.0
_PROBE_SENTINEL: str = "probe"

_INPUT_TYPE_DOCUMENT: str = "document"
_INPUT_TYPE_QUERY: str = "query"


class VoyageCloudEmbedder(Embedder):
    """Embedder backed by the hosted Voyage AI embeddings API."""

    def __init__(
        self,
        api_key: str,
        api_url: str = DEFAULT_API_URL,
        model: str = DEFAULT_MODEL,
        dim: int = DEFAULT_DIM,
        output_dimension: int = DEFAULT_DIM,
        concurrency: int = DEFAULT_CONCURRENCY,
        max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Configure the cloud embedder.

        Args:
            api_key: Bearer token sent on every request.
            api_url: Full embeddings endpoint URL.
            model: Voyage model name.
            dim: Embedding dimensionality (must match ``output_dimension``).
            output_dimension: ``output_dimension`` sent in the request body.
            concurrency: In-flight request pool size.
            max_input_tokens: Reported per-input cap (cloud auto-truncates over it).
            transport: Optional httpx transport (offline ``MockTransport`` in tests).
        """
        self._api_url = api_url
        self._model = model
        self._dim = dim
        self._output_dimension = output_dimension
        self._concurrency = concurrency
        self._max_input_tokens = max_input_tokens
        self._name = f"{DEFAULT_NAME_PREFIX}{model}"
        self._token_counter = VoyageTokenCounter()
        # The bearer token is baked into the client headers below; it is not
        # retained on the instance (needless secret surface).
        self._client = httpx.AsyncClient(
            timeout=_REQUEST_TIMEOUT_S,
            transport=transport,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        # Document and query paths use the same resilience but a different
        # input_type, so each gets its own request function.
        self._document_resilient = ResilientEmbedder(
            request_fn=self._make_request_fn(_INPUT_TYPE_DOCUMENT),
            token_counter=self._token_counter,
            max_input_tokens=max_input_tokens,
            dim=dim,
        )
        self._query_resilient = ResilientEmbedder(
            request_fn=self._make_request_fn(_INPUT_TYPE_QUERY),
            token_counter=self._token_counter,
            max_input_tokens=max_input_tokens,
            dim=dim,
        )

    @property
    def name(self) -> str:
        """Stable model identifier."""
        return self._name

    @property
    def dim(self) -> int:
        """Embedding dimensionality."""
        return self._dim

    @property
    def max_input_tokens(self) -> int:
        """Reported per-input cap (the cloud auto-truncates over it)."""
        return self._max_input_tokens

    @property
    def normalized(self) -> bool:
        """Voyage cloud vectors are L2-normalized."""
        return True

    def _make_request_fn(self, input_type: str) -> RequestFn:
        """Build a request coroutine that tags the body with ``input_type``."""

        async def request_fn(texts: list[str]) -> list[list[float]]:
            response = await self._client.post(
                self._api_url,
                json={
                    "input": texts,
                    "model": self._model,
                    "input_type": input_type,
                    "output_dimension": self._output_dimension,
                },
            )
            response.raise_for_status()
            data = response.json()["data"]
            return [item["embedding"] for item in data]

        return request_fn

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        """Embed documents (``input_type="document"``) into an aligned result."""
        if not texts:
            return EmbedResult(vectors=[], dim=self._dim)
        vectors = await self._embed_batched(texts, self._document_resilient)
        return EmbedResult(vectors=vectors, dim=self._dim)

    async def _embed_batched(
        self, texts: list[str], resilient: ResilientEmbedder
    ) -> list[list[float] | None]:
        """Token-aware-batch ``texts`` and embed each batch through ``resilient``."""
        token_counts = self._token_counter.count_tokens(texts)
        batches = build_batches(
            token_counts,
            max_tokens=self._max_input_tokens * _MAX_BATCH_TEXTS,
            max_texts=_MAX_BATCH_TEXTS,
        )

        async def embed_batch(index_batch: list[int]) -> list[list[float] | None]:
            batch_texts = [texts[index] for index in index_batch]
            return await resilient.embed_texts(batch_texts)

        batch_results = await run_in_windows(batches, embed_batch, concurrency=self._concurrency)

        vectors: list[list[float] | None] = [None] * len(texts)
        for index_batch, batch_vectors in zip(batches, batch_results, strict=True):
            for position, original_index in enumerate(index_batch):
                vectors[original_index] = batch_vectors[position]
        return vectors

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query (``input_type="query"``) into one vector.

        Raises:
            RuntimeError: If the query could not be embedded.
        """
        vectors = await self._embed_batched([text], self._query_resilient)
        vector = vectors[0]
        if vector is None:
            raise RuntimeError(f"failed to embed query: {text[:80]!r}")
        return vector

    async def probe(self) -> int:
        """Embed a sentinel and return the observed embedding dimension.

        Raises:
            Exception: If the endpoint is unreachable or returns an empty/malformed
                response (propagated so the startup gate refuses to start).
        """
        request_fn = self._make_request_fn(_INPUT_TYPE_QUERY)
        vectors = await request_fn([_PROBE_SENTINEL])
        if not vectors:
            raise RuntimeError("probe: endpoint returned no embedding for the sentinel")
        return len(vectors[0])

    def count_tokens(self, texts: list[str]) -> list[int]:
        """Return exact, input-aligned token counts via the pinned tokenizer."""
        return self._token_counter.count_tokens(texts)
