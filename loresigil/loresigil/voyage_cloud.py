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
from loresigil.resilient import RequestFn, ResilientEmbedder, SleepFn
from loresigil.tokens import VoyageTokenCounter
from loresigil.voyage_batch import (
    DEFAULT_BATCHES_API_URL,
    DEFAULT_FILES_API_URL,
    DEFAULT_POLL_INTERVAL_S,
    VoyageBatchClient,
    encode_batch_jsonl,
    parse_batch_failed_ids,
    parse_batch_output_lines,
)
from loresigil.voyage_http import build_bearer_client

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
_PROBE_SENTINEL: str = "probe"

_INPUT_TYPE_DOCUMENT: str = "document"
_INPUT_TYPE_QUERY: str = "query"

# The Batch API's ``endpoint`` field targets a path, not a full URL (the guide's
# own create-batch example body: ``{"endpoint": "/v1/embeddings", ...}``).
_BATCH_ENDPOINT_PATH: str = "/v1/embeddings"


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
        files_api_url: str = DEFAULT_FILES_API_URL,
        batches_api_url: str = DEFAULT_BATCHES_API_URL,
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
            files_api_url: Full Batch Files API base URL.
            batches_api_url: Full Batches API base URL.
        """
        self._api_url = api_url
        self._model = model
        self._dim = dim
        self._output_dimension = output_dimension
        self._concurrency = concurrency
        self._max_input_tokens = max_input_tokens
        self._name = f"{DEFAULT_NAME_PREFIX}{model}"
        self._token_counter = VoyageTokenCounter()
        # The bearer token is baked into the shared client builder; it is not
        # retained on this instance (needless secret surface).
        self._client = build_bearer_client(api_key, transport)
        # The Batch API shares this same bearer-authenticated client — see
        # loresigil.voyage_batch's module docstring for the shared plumbing.
        self._batch_client = VoyageBatchClient(self._client, files_api_url, batches_api_url)
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

    @property
    def supports_batch(self) -> bool:
        """Advertises the asynchronous Batch API capability (Files + Batches)."""
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

    async def submit_batch_documents(self, texts: list[str], ids: list[str]) -> str:
        """Submit an asynchronous batch job embedding ``texts``.

        One JSONL line per text (design decision: one input unit per line),
        each tagged with its caller-supplied ``custom_id`` so
        :meth:`fetch_batch_results` can return results keyed by that same id
        regardless of the provider's output-line order.

        Args:
            texts: Documents to embed, ``input_type="document"``.
            ids: Caller-supplied stable ids, 1:1 with ``texts``.

        Returns:
            The provider-assigned batch job id.

        Raises:
            ValueError: Empty batch or an ``ids``/``texts`` length mismatch
                (before any network call — the JSONL is built first).
            DuplicateBatchIdError: A repeated id (before any network call).
        """
        bodies = [{"input": [text]} for text in texts]
        jsonl_bytes = encode_batch_jsonl(ids, bodies)
        input_file_id = await self._batch_client.upload_input_file(jsonl_bytes)
        request_params = {
            "model": self._model,
            "input_type": _INPUT_TYPE_DOCUMENT,
            "output_dimension": self._output_dimension,
        }
        return await self._batch_client.create_batch(_BATCH_ENDPOINT_PATH, input_file_id, request_params)

    async def get_batch_status(self, job_id: str) -> str:
        """Return a submitted batch job's current lifecycle status."""
        return await self._batch_client.get_status(job_id)

    async def await_batch_completion(
        self,
        job_id: str,
        *,
        poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
        sleep_fn: SleepFn | None = None,
        deadline_s: float | None = None,
    ) -> str:
        """Poll a batch job until it reaches a terminal status.

        Args:
            job_id: The batch job id.
            poll_interval_s: Delay between polls; sleeps only BETWEEN polls.
            sleep_fn: Awaitable sleep used between polls; defaults to
                ``asyncio.sleep`` (injected in tests so polling doesn't block
                the suite).
            deadline_s: Optional logical-clock deadline; raises
                :class:`TimeoutError` naming the job id if exceeded before a
                terminal status (a real batch job may legally take the full
                12h completion window).

        Returns:
            The terminal status (always ``STATUS_COMPLETED``).

        Raises:
            TimeoutError: The deadline elapsed before a terminal status.
            BatchJobFailedError: If the terminal status is not ``"completed"``,
                naming the job id and folding its ``errors`` payload.
        """
        return await self._batch_client.await_completion(
            job_id, poll_interval_s=poll_interval_s, sleep_fn=sleep_fn, deadline_s=deadline_s
        )

    async def fetch_batch_results(self, job_id: str) -> dict[str, list[float] | None]:
        """Fetch a completed batch job's results, keyed by caller-supplied id.

        A caller only needs ``job_id`` (persisted externally) to call this —
        never the original in-memory ``ids``/``texts`` — which is what makes
        batch submission resumable across a process restart.

        Args:
            job_id: The batch job id.

        Returns:
            A mapping from each submitted id to its embedding vector, or
            ``None`` for an id the batch job's error file names as a
            permanent per-item failure (or a malformed output line the
            provider emitted) — the same sentinel convention
            :class:`~loresigil.base.EmbedResult` already uses.

        Raises:
            RuntimeError: If the job has not yet reached a terminal status.
            BatchJobFailedError: If the job's terminal status is not
                ``"completed"``, naming the job id.
        """
        output_bytes, error_bytes = await self._batch_client.fetch_result_files(job_id)
        results: dict[str, list[float] | None] = {}
        if output_bytes is not None:
            for custom_id, body in parse_batch_output_lines(output_bytes).items():
                # A malformed output line surfaces as None (the same sentinel a
                # per-item error-file failure uses), never a crash nor a drop.
                results[custom_id] = None if body is None else body["data"][0]["embedding"]
        if error_bytes is not None:
            for custom_id in parse_batch_failed_ids(error_bytes):
                results[custom_id] = None
        return results
