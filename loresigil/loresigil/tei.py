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

Asymmetric prompting: when ``query_prompt_name`` or ``document_prompt_name`` are
configured, the corresponding ``"prompt_name"`` key is added to the POST body.
When both are ``None`` (the default), the body is exactly ``{"inputs": [...]}``
— byte-identical to the pre-feature behavior.
"""

from __future__ import annotations

import logging

import httpx

from loresigil.base import Embedder, EmbedResult
from loresigil.batching import build_batches, run_in_windows
from loresigil.resilient import RequestFn, ResilientEmbedder, mean_pool, split_to_fit
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
        query_prompt_name: str | None = None,
        document_prompt_name: str | None = None,
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
            query_prompt_name: When set, the ``"prompt_name"`` key is added to
                the POST body for ``embed_query`` calls and ``probe()`` validation.
                When ``None`` (default), no ``"prompt_name"`` key is sent.
            document_prompt_name: When set, the ``"prompt_name"`` key is added
                to the POST body for ``embed_documents`` calls. When ``None``
                (default), no ``"prompt_name"`` key is sent.
        """
        self._base_url = base_url
        self._endpoint = endpoint
        self._dim = dim
        self._max_input_tokens = max_input_tokens
        self._concurrency = concurrency
        self._name = name
        self._query_prompt_name = query_prompt_name
        self._document_prompt_name = document_prompt_name
        self._token_counter = VoyageTokenCounter()
        # The bearer token is baked into the client headers below; it is not
        # retained on the instance (needless secret surface).
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=_REQUEST_TIMEOUT_S,
            transport=transport,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        # Document and query paths use the same resilience strategy but different
        # prompt names, so each gets its own request function — mirroring the
        # VoyageCloudEmbedder._make_request_fn pattern exactly.
        self._document_resilient = ResilientEmbedder(
            request_fn=self._make_request_fn(document_prompt_name),
            token_counter=self._token_counter,
            max_input_tokens=max_input_tokens,
            dim=dim,
        )
        self._query_resilient = ResilientEmbedder(
            request_fn=self._make_request_fn(query_prompt_name),
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

    def _make_request_fn(self, prompt_name: str | None) -> RequestFn:
        """Build a request coroutine that optionally tags the body with ``prompt_name``.

        When ``prompt_name`` is not None, the returned coroutine adds
        ``"prompt_name": <value>`` to the JSON body alongside ``"inputs"``.
        When ``prompt_name`` is None, the body is exactly ``{"inputs": [...]}``,
        preserving byte-identical backward compatibility.

        Args:
            prompt_name: The TEI prompt name to include, or ``None`` to omit it.

        Returns:
            A coroutine suitable for use as a ``RequestFn`` in a
            :class:`~loresigil.resilient.ResilientEmbedder`.
        """

        async def request_fn(texts: list[str]) -> list[list[float]]:
            """POST the embed request; optionally include prompt_name."""
            body: dict[str, list[str] | str] = {"inputs": texts}
            # Only include prompt_name when explicitly configured — a None value
            # must NEVER appear as a key in the body (not even as null), since
            # TEI would reject it as an unknown/null prompt name.
            if prompt_name is not None:
                body["prompt_name"] = prompt_name
            response = await self._client.post(self._endpoint, json=body)
            response.raise_for_status()
            vectors: list[list[float]] = response.json()
            return vectors

        return request_fn

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

    async def _embed_with(
        self, texts: list[str], resilient: ResilientEmbedder
    ) -> EmbedResult:
        """Pre-split, batch-embed via ``resilient``, and mean-pool back to one vector per input.

        This is the shared pipeline used by both ``embed_documents`` and
        ``embed_query``, parameterized on the resilient wrapper so each path
        uses its own prompt-name-carrying request function.

        Args:
            texts: The original inputs (may be over-length; pre-split handles them).
            resilient: The :class:`~loresigil.resilient.ResilientEmbedder` to use
                for the actual HTTP call (document or query variant).

        Returns:
            An :class:`EmbedResult` aligned 1:1 with ``texts``.
        """
        if not texts:
            return EmbedResult(vectors=[], dim=self._dim)

        pieces, owners = self._presplit(texts)
        piece_vectors = await self._embed_pieces(pieces, resilient)

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

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        """Embed a batch of documents into an input-aligned :class:`EmbedResult`.

        Over-length inputs are pre-split, all pieces are token-aware-batched and
        embedded through the resilient pool, then pieces are mean-pooled back to one
        vector per original input. Uses the document resilient wrapper (which carries
        ``document_prompt_name`` when configured).
        """
        return await self._embed_with(texts, self._document_resilient)

    async def _embed_pieces(
        self, pieces: list[str], resilient: ResilientEmbedder
    ) -> list[list[float] | None]:
        """Token-aware-batch ``pieces`` and embed each batch through ``resilient``.

        Args:
            pieces: The flat list of within-cap texts to embed.
            resilient: The resilient wrapper to use for each batch call.

        Returns:
            One vector (or ``None``) per piece, positionally aligned.
        """
        token_counts = self._token_counter.count_tokens(pieces)
        batches = build_batches(
            token_counts,
            max_tokens=self._max_input_tokens * _MAX_BATCH_TEXTS,
            max_texts=_MAX_BATCH_TEXTS,
        )

        async def embed_batch(index_batch: list[int]) -> list[list[float] | None]:
            """Embed one token-aware batch through the resilient wrapper."""
            batch_texts = [pieces[index] for index in index_batch]
            return await resilient.embed_texts(batch_texts)

        batch_results = await run_in_windows(batches, embed_batch, concurrency=self._concurrency)

        # Stitch batch results back into piece order.
        piece_vectors: list[list[float] | None] = [None] * len(pieces)
        for index_batch, batch_vectors in zip(batches, batch_results, strict=True):
            for position, original_index in enumerate(index_batch):
                piece_vectors[original_index] = batch_vectors[position]
        return piece_vectors

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string into one vector.

        Uses the query resilient wrapper (which carries ``query_prompt_name`` when
        configured).

        Raises:
            RuntimeError: If the query could not be embedded (the query path has no
                ``None`` sentinel — a failed query is an error the caller must see).
        """
        result = await self._embed_with([text], self._query_resilient)
        vector = result.vectors[0]
        if vector is None:
            raise RuntimeError(f"failed to embed query: {text[:80]!r}")
        return vector

    async def probe(self) -> int:
        """Embed a sentinel and return the observed embedding dimension.

        Validates configured prompt names at startup by calling the endpoint
        DIRECTLY (bypassing the ResilientEmbedder, whose 422→sub-split handling
        would otherwise silently null the corpus on a bad prompt). A 422 or any
        non-2xx propagates so the startup gate refuses to start.

        Returns:
            The dimensionality of the vector the live endpoint returns.

        Raises:
            Exception: If the endpoint is unreachable (transport error propagates
                so the startup gate refuses to start), returns an empty/malformed
                response, or rejects a configured prompt name with a non-2xx.
        """
        # Collect the distinct prompt names to validate (None is skipped).
        # We validate the query_prompt_name (or a plain no-prompt call if none
        # are configured) and use that call to observe the dimension.
        prompt_names_to_validate: set[str] = set()
        if self._query_prompt_name is not None:
            prompt_names_to_validate.add(self._query_prompt_name)
        if self._document_prompt_name is not None:
            prompt_names_to_validate.add(self._document_prompt_name)

        observed_dim: int | None = None

        if prompt_names_to_validate:
            # Validate each distinct configured prompt name directly (not through
            # the resilient wrapper, which would swallow 422s as over-length signals).
            for prompt_name in prompt_names_to_validate:
                try:
                    vectors = await self._make_request_fn(prompt_name)([_PROBE_SENTINEL])
                except Exception:
                    logger.error("embed.probe.unreachable")
                    raise
                if not vectors:
                    logger.error("embed.probe.unreachable")
                    raise RuntimeError(
                        f"probe: endpoint returned no embedding for sentinel with prompt {prompt_name!r}"
                    )
                # Capture dimension from the first successful probe response.
                if observed_dim is None:
                    observed_dim = len(vectors[0])
        else:
            # No prompts configured: plain probe call to observe dimension.
            try:
                vectors = await self._make_request_fn(None)([_PROBE_SENTINEL])
            except Exception:
                logger.error("embed.probe.unreachable")
                raise
            if not vectors:
                logger.error("embed.probe.unreachable")
                raise RuntimeError("probe: endpoint returned no embedding for the sentinel")
            observed_dim = len(vectors[0])

        # Every branch above either sets observed_dim from a successful probe or
        # raises, so it is provably non-None here; assert it to satisfy the type
        # checker without a blanket ``# type: ignore``.
        assert observed_dim is not None
        logger.info("embed.probe.ok", extra={"observed_dim": observed_dim})
        return observed_dim

    def count_tokens(self, texts: list[str]) -> list[int]:
        """Return exact, input-aligned token counts via the pinned tokenizer."""
        return self._token_counter.count_tokens(texts)
