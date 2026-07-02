"""``VoyageContextEmbedder`` — api.voyageai.com contextualized embeddings (voyage-context-4).

The v0.4 backend for the **contextualized** (document-grouped) Voyage endpoint.

Doc-grouping semantics: each entry of a ``docs`` argument is the ordered chunk
texts of exactly ONE source document (e.g. one indexed file) — chunks inside a
doc share context with each other; chunks belonging to different docs never do,
even when both docs travel in the same request.

Wire contract (S8-verified):

* ``POST https://api.voyageai.com/v1/contextualizedembeddings``
* Request body: ``{"inputs": [[chunk, ...], ...], "model": <model>,
  "input_type": "document"|"query", "output_dimension": <dim>}`` with a bearer
  token. ``embed_document_chunks`` tags ``input_type="document"``;
  ``embed_query`` sends ONE single-chunk doc tagged ``"query"``.
* Response: ``data[i].data[j].embedding`` — per-chunk vectors positionally
  aligned with ``inputs[i][j]``; extra ``index`` echoes are tolerated, never
  required. ``usage.total_tokens`` is present and is this backend's ONLY
  source of truth for billed tokens (never re-derived from the client's own
  tokenizer — the provider's billing meter is not guaranteed to agree with it).
* Degrade, never crash: per-doc failures come back as aligned all-``None``
  results without poisoning sibling docs; a doc over the model's context
  window is a loud per-doc failure, never a silent truncation or split.

The retry/backoff and finiteness-quarantine machinery is IMPORTED, not just
conventionally mirrored, from :mod:`loresigil.resilient`
(:func:`~loresigil.resilient.is_retryable_status`,
:func:`~loresigil.resilient.compute_backoff_delay`,
:func:`~loresigil.resilient.quarantine_vector`) — but the orchestration around
it is hand-rolled here, deliberately NOT :class:`~loresigil.resilient.ResilientEmbedder`.
That class is built to salvage as many FLAT texts as possible by falling back
to per-text requests when a batch fails, which is exactly the behaviour this
backend must NOT exhibit: splitting one document's chunks into separate
per-chunk requests would silently change what "context" each chunk was
embedded with (ResilientEmbedder has no notion of a chunk belonging to a doc
in the first place — its atom is a bare text). Instead, a failed combined
request falls back to one request PER DOCUMENT (never per chunk), fanned out
with the shared :func:`~loresigil.batching.run_in_windows` bounded-concurrency
runner — per-DOCUMENT atomicity, not per-text salvage.

The backoff sleep is injectable (``sleep_fn`` constructor keyword, default
``asyncio.sleep``) — the exact seam convention of
:class:`~loresigil.resilient.ResilientEmbedder`, whose ``SleepFn`` alias is
imported here rather than redefined. A retryable failure on the FINAL
attempt never pays a parting sleep: sleeping is only ever a bridge BETWEEN
attempts, so the retry loop below checks whether it is on its last attempt
before deciding to sleep.

Usage/telemetry seam (v0.4 follow-up cycle): this backend ALWAYS reports
usage (never ``None``) — ``usage.total_tokens`` is read from each
successfully-parsed 200 response body, summed across every request the call
made ("billed" != "succeeded": a request whose vectors are later quarantined
was still billed; an unreadable 200 or a 400 contributes 0). A combined
request that covers several docs at once bills once for the whole request;
:meth:`_split_usage_by_doc` attributes that one bill across its docs
(weighted by this backend's own token counter, purely as a distribution
knob — never as the SOURCE of the total, which always comes off the wire) so
that summing every doc's usage reproduces exactly what was served.

Conservation across re-resolution: when a doc's shape does not map inside a
combined response, that doc falls back to its own dedicated request(s) — but
the combined request's ATTRIBUTED share for that doc (see
:meth:`_split_usage_by_doc`) was still genuinely billed; it must not be
discarded just because the doc's embedding ultimately came from elsewhere.
The redistribution scheme is deliberately the simplest one that conserves
the grand total (Σ per-doc usage over the returned results == Σ every
successfully-parsed 200's wire total for the call, no matter how many
requests it took or whether a doc was re-resolved): :meth:`_embed_docs` folds
each unresolved doc's abandoned share directly onto whatever its own
dedicated fallback eventually reports, via :meth:`_fold_abandoned_usage`.
Spreading the abandoned share across the OTHER docs of the combined request
instead would be equally conservation-correct but is not what this
implementation does — folding it back onto the doc it was actually billed
for keeps the accounting local to that doc's own resolution path.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from loresigil.base import Embedder, EmbedResult, EmbedUsage
from loresigil.batching import run_in_windows
from loresigil.resilient import SleepFn, compute_backoff_delay, is_retryable_status, quarantine_vector
from loresigil.tokens import VoyageTokenCounter
from loresigil.voyage_http import build_bearer_client

logger = logging.getLogger(__name__)

DEFAULT_API_URL: str = "https://api.voyageai.com/v1/contextualizedembeddings"
DEFAULT_MODEL: str = "voyage-context-4"
DEFAULT_DIM: int = 2048
DEFAULT_CONCURRENCY: int = 4
DEFAULT_NAME_PREFIX: str = "voyage-context:"

# voyage-context-4's documented per-DOCUMENT context window (tokens). A doc
# whose chunks exceed it in total cannot be contextualized as requested.
DEFAULT_MAX_INPUT_TOKENS: int = 32_000

# Maximum attempts (initial + retries) for a transient (429/5xx/transport)
# request, mirroring ResilientEmbedder's default retry budget.
DEFAULT_MAX_RETRIES: int = 5
_PROBE_SENTINEL: str = "probe"

_INPUT_TYPE_DOCUMENT: str = "document"
_INPUT_TYPE_QUERY: str = "query"

# A request that billed nothing (permanent failure, unreadable body) reports
# this — a reporting backend distinguishes "billed zero" from "not reported"
# (the latter is EmbedResult.usage is None, never used by this backend).
_ZERO_TOKENS: int = 0

# Every doc gets at least this much weight when attributing a combined
# request's bill across its docs, so an all-empty doc still receives a
# (deterministic, if tiny) proportional share rather than dividing by zero.
_MIN_USAGE_WEIGHT: int = 1


@dataclass(frozen=True)
class _ContextBatchResponse:
    """One successfully-parsed contextualized response, ready for the caller.

    Attributes:
        vectors: ``data[i][j]`` — one vector per chunk per doc, positionally
            aligned with the request's ``docs``.
        usage_total_tokens: The wire's ``usage.total_tokens`` for this ONE
            request (0 if the response body carried no readable usage object).
    """

    vectors: list[list[list[float]]]
    usage_total_tokens: int


class VoyageContextEmbedder(Embedder):
    """Embedder backed by the hosted Voyage AI contextualized-embeddings API."""

    def __init__(
        self,
        api_key: str,
        api_url: str = DEFAULT_API_URL,
        model: str = DEFAULT_MODEL,
        output_dimension: int = DEFAULT_DIM,
        concurrency: int = DEFAULT_CONCURRENCY,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep_fn: SleepFn | None = None,
    ) -> None:
        """Configure the contextualized cloud embedder.

        Args:
            api_key: Bearer token sent on every request (arrives resolved; the
                env-var seam is the factory's responsibility).
            api_url: Full contextualized-embeddings endpoint URL.
            model: Voyage contextualized model name.
            output_dimension: The single Matryoshka dimensionality knob —
                sent in the request body, reflected by :attr:`dim`.
            concurrency: In-flight request pool size for the per-document
                fallback fan-out.
            transport: Optional httpx transport (offline ``MockTransport`` in
                tests).
            sleep_fn: Awaitable sleep used for backoff; defaults to
                ``asyncio.sleep`` (injected in tests so retries don't block
                the suite) — the exact seam convention of
                :class:`~loresigil.resilient.ResilientEmbedder`.
        """
        self._api_url = api_url
        self._model = model
        self._output_dimension = output_dimension
        self._concurrency = concurrency
        self._max_retries = DEFAULT_MAX_RETRIES
        self._token_counter = VoyageTokenCounter()
        self._sleep_fn: SleepFn = sleep_fn or asyncio.sleep
        # The bearer token is baked into the shared client builder; it is not
        # retained on this instance (needless secret surface).
        self._client = build_bearer_client(api_key, transport)

    @property
    def name(self) -> str:
        """Stable model identifier (names the configured model)."""
        return f"{DEFAULT_NAME_PREFIX}{self._model}"

    @property
    def dim(self) -> int:
        """Embedding dimensionality — follows the configured ``output_dimension``."""
        return self._output_dimension

    @property
    def max_input_tokens(self) -> int:
        """Per-DOCUMENT token window; an over-window doc fails loud per-doc."""
        return DEFAULT_MAX_INPUT_TOKENS

    @property
    def normalized(self) -> bool:
        """Voyage contextualized vectors are L2-normalized."""
        return True

    @property
    def supports_contextualized(self) -> bool:
        """This backend's reason to exist — advertises the contextualized seam."""
        return True

    async def embed_document_chunks(self, docs: list[list[str]]) -> list[EmbedResult]:
        """Embed each doc's grouped chunks (``input_type="document"``).

        Args:
            docs: One entry per document, each the ordered chunk texts.

        Returns:
            One input-aligned :class:`EmbedResult` per doc; ``None`` marks a
            permanently-failed chunk. One doc's failure never poisons siblings.
            Each result's ``usage`` conserves the call's served-and-parsed
            totals (see module docstring).
        """
        return await self._embed_docs(docs, _INPUT_TYPE_DOCUMENT)

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        """Embed a flat batch of documents into an input-aligned result.

        Each text is treated as its own independent, single-chunk document
        (no shared context between texts) — the contextualized endpoint has
        no ungrouped shape, so this is the closest faithful mapping.
        """
        if not texts:
            return EmbedResult(
                vectors=[], dim=self._output_dimension, usage=EmbedUsage(total_tokens=_ZERO_TOKENS)
            )
        doc_results = await self._embed_docs([[text] for text in texts], _INPUT_TYPE_DOCUMENT)
        vectors: list[list[float] | None] = [result.vectors[0] for result in doc_results]
        # This backend always reports on every doc_result; sum them into the
        # ONE aggregate bill for the whole flat call.
        total_tokens = sum(
            result.usage.total_tokens for result in doc_results if result.usage is not None
        )
        return EmbedResult(
            vectors=vectors,
            dim=self._output_dimension,
            usage=EmbedUsage(total_tokens=total_tokens),
        )

    async def embed_query(self, text: str) -> list[float]:
        """Embed one query as a single-chunk doc (``input_type="query"``).

        Raises:
            RuntimeError: If the query could not be embedded (permanent failure).
        """
        results = await self._embed_docs([[text]], _INPUT_TYPE_QUERY)
        vector = results[0].vectors[0]
        if vector is None:
            raise RuntimeError(f"failed to embed query: {text[:80]!r}")
        return vector

    async def probe(self) -> int:
        """Embed a sentinel and return the observed embedding dimension.

        Bypasses the retry/fallback machinery entirely (one direct attempt) so
        an unreachable endpoint fails immediately rather than after a retry
        budget of exponential-backoff sleeps.

        Raises:
            Exception: If the endpoint is unreachable (propagated so the
                startup gate refuses to start).
        """
        response = await self._post([[_PROBE_SENTINEL]], _INPUT_TYPE_QUERY)
        if not response.vectors or not response.vectors[0]:
            raise RuntimeError("probe: endpoint returned no embedding for the sentinel")
        return len(response.vectors[0][0])

    def count_tokens(self, texts: list[str]) -> list[int]:
        """Return exact, input-aligned token counts via the pinned tokenizer."""
        return self._token_counter.count_tokens(texts)

    async def _embed_docs(self, docs: list[list[str]], input_type: str) -> list[EmbedResult]:
        """Embed ``docs`` together in one request, falling back per-doc on failure.

        Reads linearly as two passes: try everything together first (cheap,
        one request), then resolve whatever that pass could not settle one
        document at a time (never poisoning a doc's siblings).

        Args:
            docs: One entry per document, each the ordered chunk texts.
            input_type: ``"document"`` or ``"query"``, forwarded verbatim.

        Returns:
            One input-aligned :class:`EmbedResult` per doc, each carrying its
            own ``usage`` (never ``None`` — this backend always reports). A
            doc re-resolved by its own dedicated fallback carries BOTH its
            dedicated request's bill AND its abandoned share of the earlier
            combined request's bill (see the module docstring's conservation
            note and :meth:`_fold_abandoned_usage`), so no billed token from
            any parsed 200 the call made is ever dropped.
        """
        if not docs:
            return []

        resolved_by_index: dict[int, EmbedResult] = {}
        abandoned_usage_by_index = await self._resolve_combined_batch(
            docs, input_type, resolved_by_index
        )

        if abandoned_usage_by_index:
            unresolved_indices = list(abandoned_usage_by_index.keys())

            async def resolve_doc_at_index(index: int) -> EmbedResult:
                result = await self._embed_single_doc(docs[index], input_type)
                return self._fold_abandoned_usage(result, abandoned_usage_by_index[index])

            per_doc_results = await run_in_windows(
                unresolved_indices, resolve_doc_at_index, concurrency=self._concurrency
            )
            for index, result in zip(unresolved_indices, per_doc_results, strict=True):
                resolved_by_index[index] = result

        return [resolved_by_index[index] for index in range(len(docs))]

    async def _resolve_combined_batch(
        self,
        docs: list[list[str]],
        input_type: str,
        resolved_by_index: dict[int, EmbedResult],
    ) -> dict[int, int]:
        """Attempt one request for every doc at once; report what it could not settle.

        Args:
            docs: One entry per document, each the ordered chunk texts.
            input_type: ``"document"`` or ``"query"``, forwarded verbatim.
            resolved_by_index: Mutated in place — filled with one
                :class:`EmbedResult` per doc the combined request could
                shape-validate, its ``usage`` its attributed share (see
                :meth:`_split_usage_by_doc`) of this ONE request's bill.

        Returns:
            A mapping from doc index to its ABANDONED usage share, one entry
            per doc still needing per-doc fallback resolution: every doc
            index (each mapped to a 0 share — a request that never parsed
            never attributed anything) if the combined request failed
            outright, or just the doc(s) whose OWN chunk count disagreed with
            what came back (each mapped to that doc's
            :meth:`_split_usage_by_doc` share of THIS request's total — it
            was genuinely billed even though this doc's shape was unusable
            here, so the share travels with the doc for
            :meth:`_embed_docs` to fold onto its dedicated fallback rather
            than being silently dropped).
        """
        response = await self._request_with_retry(docs, input_type)
        if response is None:
            # Nothing usable came back: no per-doc share was ever
            # attributable, so every doc falls back with zero abandoned
            # usage (an unparsed/rejected request billed nothing countable).
            # (_post guarantees a parsed response has one vector list per
            # requested doc, so a non-None response never mismatches here.)
            return {index: _ZERO_TOKENS for index in range(len(docs))}

        usage_shares = self._split_usage_by_doc(docs, response.usage_total_tokens)
        abandoned_usage_by_index: dict[int, int] = {}
        for index, (chunks, chunk_vectors, usage_share) in enumerate(
            zip(docs, response.vectors, usage_shares, strict=True)
        ):
            if len(chunk_vectors) == len(chunks):
                resolved_by_index[index] = self._quarantine_doc(chunk_vectors, chunks, usage_share)
            else:
                abandoned_usage_by_index[index] = usage_share
        return abandoned_usage_by_index

    @staticmethod
    def _fold_abandoned_usage(result: EmbedResult, abandoned_tokens: int) -> EmbedResult:
        """Add a doc's abandoned combined-request share onto its fallback result.

        This is the ONE accumulation point for the conservation contract
        described in the module docstring: a doc that needed its own
        dedicated request still owes whatever an earlier combined request
        billed for it before that combined response turned out unusable for
        this doc.

        Args:
            result: The :class:`EmbedResult` produced by the doc's dedicated
                fallback resolution (this backend always reports, so
                ``result.usage`` is never ``None`` in practice).
            abandoned_tokens: The doc's attributed share (see
                :meth:`_split_usage_by_doc`) of an earlier combined request
                whose shape did not map for this doc — 0 when the earlier
                combined request billed nothing at all (e.g. it failed
                outright before ever reaching a parsed 200).

        Returns:
            ``result`` unchanged when there is nothing to fold in (the
            common case), else a copy whose ``usage.total_tokens`` includes
            the abandoned share.
        """
        if abandoned_tokens == _ZERO_TOKENS or result.usage is None:
            return result
        return result.model_copy(
            update={
                "usage": EmbedUsage(total_tokens=result.usage.total_tokens + abandoned_tokens)
            }
        )

    async def _embed_single_doc(self, chunks: list[str], input_type: str) -> EmbedResult:
        """Resolve exactly one document on its own request; never split further.

        Args:
            chunks: The ordered chunk texts of the one document being resolved.
            input_type: ``"document"`` or ``"query"``, forwarded verbatim.

        Returns:
            An input-aligned :class:`EmbedResult`; aligned all-``None`` if this
            document's own isolated request still could not be satisfied (e.g.
            it exceeds the context window, or the batch is unsatisfiable as
            sent) — the chunks are never sub-split into separate requests,
            which would silently change what context each chunk was embedded
            with. A DEDICATED single-doc request needs no attribution split:
            its ``usage`` is the exact wire total of that one request (0 if
            the request never billed at all).
        """
        response = await self._request_with_retry([chunks], input_type)
        if response is None:
            return EmbedResult(
                vectors=[None] * len(chunks),
                dim=self._output_dimension,
                usage=EmbedUsage(total_tokens=_ZERO_TOKENS),
            )
        if len(response.vectors) == 1 and len(response.vectors[0]) == len(chunks):
            return self._quarantine_doc(response.vectors[0], chunks, response.usage_total_tokens)
        # A parsed 200 whose chunk mapping is unusable is still billed —
        # "billed" != "succeeded" applies here exactly as it does to a
        # quarantined (NaN) vector.
        return EmbedResult(
            vectors=[None] * len(chunks),
            dim=self._output_dimension,
            usage=EmbedUsage(total_tokens=response.usage_total_tokens),
        )

    def _quarantine_doc(
        self, chunk_vectors: list[list[float]], chunks: list[str], usage_total_tokens: int
    ) -> EmbedResult:
        """Quarantine each chunk vector to ``None`` if wrong-shape or non-finite.

        Args:
            chunk_vectors: The wire vectors, one per chunk, positionally aligned.
            chunks: The chunk texts (used only for the result's length/order).
            usage_total_tokens: The token bill attributed to this doc — already
                resolved by the caller (either an exact per-request total, or
                this doc's share of a combined request's total).

        Returns:
            An :class:`EmbedResult` whose ``dim`` is the CONFIGURED
            ``output_dimension`` (never a lying wire length); ``usage`` is
            billed regardless of any per-chunk quarantine (billed != succeeded).
        """
        vectors: list[list[float] | None] = [
            self._quarantine_vector(vector) for vector in chunk_vectors
        ]
        return EmbedResult(
            vectors=vectors,
            dim=self._output_dimension,
            usage=EmbedUsage(total_tokens=usage_total_tokens),
        )

    def _quarantine_vector(self, vector: list[float]) -> list[float] | None:
        """Return ``vector`` only if it is the configured dimension and all-finite.

        Delegates to the module-level :func:`~loresigil.resilient.quarantine_vector`
        (shared with ``ResilientEmbedder._quarantine``): a wrong-dimension vector
        would be stored under a lying ``dim`` and a non-finite component would
        poison cosine similarity/argmax downstream.
        """
        return quarantine_vector(vector, self._output_dimension)

    def _split_usage_by_doc(self, docs: list[list[str]], total_tokens: int) -> list[int]:
        """Attribute one combined request's billed total across its docs.

        The provider bills PER REQUEST, not per doc — this split is
        attribution, not measurement (the contract pins only that summing
        every doc's usage reproduces the served total). Weighted by each
        doc's own token count via this backend's OWN tokenizer, used here
        purely as an internal weighting knob — NEVER as the source of the
        total itself, which always comes off the wire — so a bigger document
        is attributed a proportionally bigger share. The largest-remainder
        method distributes any integer-division leftover so the shares sum
        to EXACTLY ``total_tokens``, never drifting from what was billed.

        Args:
            docs: The documents that traveled together in the combined request.
            total_tokens: That ONE request's wire-reported ``usage.total_tokens``.

        Returns:
            One attributed share per doc, positionally aligned with ``docs``,
            summing to exactly ``total_tokens``.
        """
        if not docs:
            return []
        weights = [max(_MIN_USAGE_WEIGHT, sum(self.count_tokens(chunks))) for chunks in docs]
        total_weight = sum(weights)
        scaled = [total_tokens * weight for weight in weights]
        shares = [value // total_weight for value in scaled]
        remainders = [value % total_weight for value in scaled]
        leftover = total_tokens - sum(shares)
        # Hand the leftover, one token at a time, to the docs with the
        # largest remainder — the standard largest-remainder rounding fix,
        # so Σ shares == total_tokens exactly regardless of how it divides.
        for index in sorted(range(len(docs)), key=lambda i: remainders[i], reverse=True)[:leftover]:
            shares[index] += 1
        return shares

    async def _request_with_retry(
        self, docs: list[list[str]], input_type: str
    ) -> _ContextBatchResponse | None:
        """Send one contextualized request, retrying transient failures.

        Args:
            docs: One entry per document, each the ordered chunk texts.
            input_type: ``"document"`` or ``"query"``, forwarded verbatim.

        Returns:
            The parsed response (vectors + this request's billed total), or
            ``None`` if the request could not be satisfied (permanent
            failure, malformed response, or the retry budget was exhausted —
            all of which bill nothing countable).
        """
        last_status: int | None = None
        for attempt in range(self._max_retries):
            # Sleeping is only ever a bridge BETWEEN attempts: a retryable
            # failure discovered on the LAST attempt must return immediately,
            # never pay a parting backoff sleep it will not get to use.
            is_final_attempt = attempt == self._max_retries - 1
            try:
                return await self._post(docs, input_type)
            except httpx.HTTPStatusError as error:
                status = error.response.status_code
                if is_retryable_status(status):
                    last_status = status
                    if is_final_attempt:
                        break
                    await self._backoff(attempt, status=status, n_docs=len(docs))
                    continue
                # Any other 4xx (including the documented over-window 400) is
                # permanent for this request.
                logger.error(
                    "voyage_context.permanent_failure",
                    extra={"status": status, "n_docs": len(docs)},
                )
                return None
            except (httpx.ConnectError, httpx.TimeoutException):
                if is_final_attempt:
                    break
                await self._backoff(attempt, status=None, n_docs=len(docs))
                continue
            except (ValueError, KeyError, TypeError):
                # A 2xx with a malformed/garbage body (JSONDecodeError is a
                # ValueError; a wrong envelope or doc-count mismatch is a
                # KeyError/ValueError) is a permanent failure for this request.
                logger.error(
                    "voyage_context.permanent_failure",
                    extra={"status": last_status, "n_docs": len(docs)},
                )
                return None
        logger.error(
            "voyage_context.permanent_failure",
            extra={"status": last_status, "n_docs": len(docs)},
        )
        return None

    async def _post(self, docs: list[list[str]], input_type: str) -> _ContextBatchResponse:
        """POST one contextualized request and parse the response positionally.

        Args:
            docs: One entry per document, each the ordered chunk texts.
            input_type: ``"document"`` or ``"query"``.

        Returns:
            The parsed vectors (``data[i][j]``, positionally aligned with
            ``docs``; the API's ``index`` echoes are tolerated but never
            consulted) plus this request's billed ``usage.total_tokens``
            (0 if the body carried no readable usage object).

        Raises:
            httpx.HTTPStatusError: On a non-2xx response.
            ValueError: If the response body is not JSON, or the returned doc
                count disagrees with the request (unsafe to positionally map).
            KeyError: If the response envelope is missing expected keys.
        """
        response = await self._client.post(
            self._api_url,
            json={
                "inputs": docs,
                "model": self._model,
                "input_type": input_type,
                "output_dimension": self._output_dimension,
                # lore's chunks are canonical (domain-specific, identity-bearing);
                # the provider must never re-split them — pinned off explicitly so
                # a server-side default flip can't change what a "chunk" is.
                "enable_auto_chunking": False,
            },
        )
        response.raise_for_status()
        body = response.json()
        data = body["data"]
        if len(data) != len(docs):
            # A short/long doc list would otherwise be mapped positionally to
            # the WRONG document (corpus poisoning) — reject outright.
            raise ValueError(f"contextualized response doc count {len(data)} != requested {len(docs)}")
        vectors = [[entry["embedding"] for entry in doc_entry["data"]] for doc_entry in data]
        return _ContextBatchResponse(
            vectors=vectors, usage_total_tokens=self._extract_usage_total(body)
        )

    @staticmethod
    def _extract_usage_total(body: dict[str, Any]) -> int:
        """Read ``usage.total_tokens`` off a successfully-parsed response body.

        Missing or malformed usage in an otherwise-valid body degrades to 0
        tokens billed for THIS request — never fabricated from the client's
        own tokenizer. The wire is the only source of truth for what was
        actually billed; the mock provider's billing meter deliberately
        differs from the client tokenizer precisely to catch that mistake.

        Args:
            body: The parsed JSON response body.

        Returns:
            The integer ``usage.total_tokens``, or 0 if absent/malformed.
        """
        usage = body.get("usage")
        if isinstance(usage, dict):
            total = usage.get("total_tokens")
            if isinstance(total, int):
                return total
        return _ZERO_TOKENS

    async def _backoff(self, attempt: int, *, status: int | None, n_docs: int) -> None:
        """Log the retry, then sleep for an exponentially growing, capped delay.

        Args:
            attempt: The zero-based attempt index that just failed.
            status: The HTTP status that triggered the retry (429/5xx), or
                ``None`` for a transport error.
            n_docs: The number of documents in the failed request (a count
                only, never the documents themselves).
        """
        delay = compute_backoff_delay(attempt)
        logger.warning(
            "voyage_context.retry.backoff",
            extra={"status": status, "attempt": attempt, "delay_s": delay, "n_docs": n_docs},
        )
        await self._sleep_fn(delay)
