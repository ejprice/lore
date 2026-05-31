"""``TEIEmbedder`` — self-hosted Text Embeddings Inference for voyage-4-nano.

Implements the verified TEI native contract:

* ``POST {base_url}{endpoint}`` with body ``{"inputs": [text, ...]}`` and a bearer
  token. **No** ``truncate`` field is sent: the server runs ``--auto-truncate
  false``, so an over-length input is a hard 422, never silently truncated.
* The response is a **bare** ``[[float × 2048], ...]`` of L2-normalized vectors.
* ``dim == 2048``, ``max_input_tokens == 8192``, ``normalized is True``.

Resilience is delegated to :class:`~loresigil.resilient.ResilientEmbedder` (429
backoff, 422 sub-split backstop, ``isfinite`` quarantine). Over-length inputs are
**pre-split client-side** against the exact pinned tokenizer so the whole text is
never sent to a 422 — the 422 path is only the runtime backstop. Requests are run
through a bounded in-flight pool of 2 (the measured optimum).
"""

from __future__ import annotations

import logging

import httpx

from loresigil.base import Embedder, EmbedResult
from loresigil.batching import build_batches, run_in_windows
from loresigil.resilient import ResilientEmbedder, mean_pool, split_to_fit
from loresigil.tokens import VoyageTokenCounter

logger = logging.getLogger(__name__)

DEFAULT_DIM: int = 2048
DEFAULT_MAX_INPUT_TOKENS: int = 8192
DEFAULT_ENDPOINT: str = "/embed"
DEFAULT_CONCURRENCY: int = 2
DEFAULT_NAME: str = "tei:voyageai/voyage-4-nano"

# TEI per-request input cap (max_client_batch_size); over it the server 413s.
_MAX_BATCH_TEXTS: int = 32
# Generous HTTP timeout: a near-limit 8k-token input can cost ~14 s on the box.
_REQUEST_TIMEOUT_S: float = 120.0
# A tiny sentinel used by probe() to observe the live embedding dimension.
_PROBE_SENTINEL: str = "probe"


class TEIEmbedder(Embedder):
    """Embedder backed by a self-hosted TEI endpoint serving voyage-4-nano."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        endpoint: str = DEFAULT_ENDPOINT,
        dim: int = DEFAULT_DIM,
        max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS,
        concurrency: int = DEFAULT_CONCURRENCY,
        transport: httpx.AsyncBaseTransport | None = None,
        name: str = DEFAULT_NAME,
    ) -> None:
        """Configure the TEI embedder.

        Args:
            base_url: Scheme+host(+port) of the TEI server.
            api_key: Bearer token sent on every request.
            endpoint: Path of the native embed endpoint (default ``/embed``).
            dim: Embedding dimensionality the model produces.
            max_input_tokens: Hard per-input token cap the server enforces.
            concurrency: In-flight request pool size (measured optimum: 2).
            transport: Optional httpx transport (an offline ``MockTransport`` in
                tests); when ``None`` a real networked client is built.
            name: Stable model identifier.
        """
        self._base_url = base_url
        self._endpoint = endpoint
        self._dim = dim
        self._max_input_tokens = max_input_tokens
        self._concurrency = concurrency
        self._name = name
        self._token_counter = VoyageTokenCounter()
        # The bearer token is baked into the client headers below; it is not
        # retained on the instance (needless secret surface).
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=_REQUEST_TIMEOUT_S,
            transport=transport,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        self._resilient = ResilientEmbedder(
            request_fn=self._post_embed,
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
        """Hard per-input token cap (over it the server returns 422)."""
        return self._max_input_tokens

    @property
    def normalized(self) -> bool:
        """voyage-4-nano vectors are L2-normalized."""
        return True

    async def _post_embed(self, texts: list[str]) -> list[list[float]]:
        """POST ``{"inputs": texts}`` to the native endpoint and parse the bare list.

        Args:
            texts: The batch of texts to embed.

        Returns:
            One vector per input (a bare ``[[...]]`` response).

        Raises:
            httpx.HTTPStatusError: On a non-2xx status (handled by the resilient
                wrapper: 429/5xx retried, 422 sub-split).
        """
        response = await self._client.post(self._endpoint, json={"inputs": texts})
        response.raise_for_status()
        vectors: list[list[float]] = response.json()
        return vectors

    def _presplit(self, texts: list[str]) -> tuple[list[str], list[int]]:
        """Pre-split any over-length input so the whole text is never sent.

        Args:
            texts: The original inputs.

        Returns:
            A tuple ``(pieces, owners)`` where ``pieces`` is the flat list of
            within-cap texts to send and ``owners[k]`` is the index of the original
            input that ``pieces[k]`` belongs to.
        """
        pieces: list[str] = []
        owners: list[int] = []
        for original_index, text in enumerate(texts):
            for piece in split_to_fit(text, self._token_counter, self._max_input_tokens):
                pieces.append(piece)
                owners.append(original_index)
        return pieces, owners

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        """Embed a batch of documents into an input-aligned :class:`EmbedResult`.

        Over-length inputs are pre-split, all pieces are token-aware-batched and
        embedded through the resilient pool, then pieces are mean-pooled back to one
        vector per original input.
        """
        if not texts:
            return EmbedResult(vectors=[], dim=self._dim)

        pieces, owners = self._presplit(texts)
        piece_vectors = await self._embed_pieces(pieces)

        # Reassemble: gather each original input's piece vectors, mean-pool them.
        grouped: list[list[list[float]]] = [[] for _ in texts]
        failed: list[bool] = [False] * len(texts)
        for piece_index, vector in enumerate(piece_vectors):
            owner = owners[piece_index]
            if vector is None:
                failed[owner] = True
            else:
                grouped[owner].append(vector)

        vectors: list[list[float] | None] = []
        for original_index in range(len(texts)):
            if failed[original_index] or not grouped[original_index]:
                vectors.append(None)
            else:
                vectors.append(mean_pool(grouped[original_index]))
        return EmbedResult(vectors=vectors, dim=self._dim)

    async def _embed_pieces(self, pieces: list[str]) -> list[list[float] | None]:
        """Token-aware-batch ``pieces`` and embed each batch through the resilient pool."""
        token_counts = self._token_counter.count_tokens(pieces)
        batches = build_batches(
            token_counts,
            max_tokens=self._max_input_tokens * _MAX_BATCH_TEXTS,
            max_texts=_MAX_BATCH_TEXTS,
        )

        async def embed_batch(index_batch: list[int]) -> list[list[float] | None]:
            batch_texts = [pieces[index] for index in index_batch]
            return await self._resilient.embed_texts(batch_texts)

        batch_results = await run_in_windows(batches, embed_batch, concurrency=self._concurrency)

        # Stitch batch results back into piece order.
        piece_vectors: list[list[float] | None] = [None] * len(pieces)
        for index_batch, batch_vectors in zip(batches, batch_results, strict=True):
            for position, original_index in enumerate(index_batch):
                piece_vectors[original_index] = batch_vectors[position]
        return piece_vectors

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string into one vector.

        Raises:
            RuntimeError: If the query could not be embedded (the query path has no
                ``None`` sentinel — a failed query is an error the caller must see).
        """
        result = await self.embed_documents([text])
        vector = result.vectors[0]
        if vector is None:
            raise RuntimeError(f"failed to embed query: {text[:80]!r}")
        return vector

    async def probe(self) -> int:
        """Embed a sentinel and return the observed embedding dimension.

        Returns:
            The dimensionality of the vector the live endpoint returns.

        Raises:
            Exception: If the endpoint is unreachable (the transport error
                propagates so the startup gate refuses to start) or returns an
                empty/malformed response (no vector to observe a dimension from).
        """
        try:
            vectors = await self._post_embed([_PROBE_SENTINEL])
        except Exception:
            # The endpoint is unreachable (transport error) or refused; the gate
            # turns this into a refuse-to-start. Log a count-free ERROR event (no
            # URL, header, or response object — the bearer must never leak).
            logger.error("embed.probe.unreachable")
            raise
        if not vectors:
            logger.error("embed.probe.unreachable")
            raise RuntimeError("probe: endpoint returned no embedding for the sentinel")
        observed_dim = len(vectors[0])
        logger.info("embed.probe.ok", extra={"observed_dim": observed_dim})
        return observed_dim

    def count_tokens(self, texts: list[str]) -> list[int]:
        """Return exact, input-aligned token counts via the pinned tokenizer."""
        return self._token_counter.count_tokens(texts)
