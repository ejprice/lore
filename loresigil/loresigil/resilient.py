"""Resilient request wrapper shared by every concrete embedder.

:class:`ResilientEmbedder` turns a fragile single-shot "POST these texts, parse
vectors" callable into one that **never crashes and never stores garbage**. Every
backend (TEI, cloud) injects its own ``request_fn`` — the part that knows the wire
shape — and gets the same resilience contract for free:

* **429** (the TEI 64-concurrency DOS guard) → exponential backoff + retry.
* **5xx / ConnectError / timeout** → exponential backoff + retry.
* **422 / over-length** → catch, **sub-split** the offending input(s) by tokens
  (each piece ≤ ``max_input_tokens``), re-embed the pieces through the same path,
  and mean-pool a piece set back into one vector for the original input. This is a
  runtime backstop on top of the upstream ≤8192 pre-check (measured to fire on
  0/8239 real chunks, but must exist).
* **Non-finite vector** (NaN / inf) → quarantine to ``None``. One non-finite
  component poisons cosine/argmax across every query, so it is never surfaced as a
  stored vector.
* **Permanent failure** after the retry budget is exhausted → ``None`` for that
  input, positionally aligned.

The transport itself lives in the backend's ``request_fn``; the retry sleep is
injectable so tests stay fast and deterministic.
"""

from __future__ import annotations

import asyncio
import logging
import math
from collections.abc import Awaitable, Callable

import httpx

from loresigil.tokens import VoyageTokenCounter

logger = logging.getLogger(__name__)

# A coroutine that POSTs a batch of texts and returns one vector per text, or
# raises httpx.HTTPStatusError / ConnectError / TimeoutException on failure.
RequestFn = Callable[[list[str]], Awaitable[list[list[float]]]]
SleepFn = Callable[[float], Awaitable[None]]

# Exponential-backoff base: delay before retry N is ``BACKOFF_BASE ** N`` seconds,
# capped at BACKOFF_CAP_S so a long outage doesn't produce absurd sleeps.
BACKOFF_BASE_S: float = 1.0
BACKOFF_GROWTH: float = 2.0
BACKOFF_CAP_S: float = 30.0

# HTTP statuses with dedicated handling (everything else 4xx is treated as
# permanent; 5xx is retried).
HTTP_TOO_MANY_REQUESTS: int = 429
HTTP_UNPROCESSABLE_ENTITY: int = 422
HTTP_BAD_REQUEST: int = 400
HTTP_SERVER_ERROR_FLOOR: int = 500

# When sub-splitting an over-length input, halve it by character count until each
# piece's token count fits the cap. This factor bounds the recursion depth.
_SUBSPLIT_FACTOR: int = 2


def split_to_fit(text: str, token_counter: VoyageTokenCounter, max_input_tokens: int) -> list[str]:
    """Recursively bisect ``text`` until every piece is ≤ ``max_input_tokens``.

    Shared by the resilient 422 backstop and the TEI client-side pre-split so both
    use one splitting policy.

    Args:
        text: The text to split.
        token_counter: Exact tokenizer used to size pieces.
        max_input_tokens: Hard per-input token cap.

    Returns:
        Non-empty pieces whose concatenation is ``text``, each within the cap.
    """
    if token_counter.count(text) <= max_input_tokens or len(text) <= 1:
        return [text]
    midpoint = len(text) // _SUBSPLIT_FACTOR
    left = split_to_fit(text[:midpoint], token_counter, max_input_tokens)
    right = split_to_fit(text[midpoint:], token_counter, max_input_tokens)
    return left + right


def mean_pool(vectors: list[list[float]]) -> list[float] | None:
    """Mean-pool piece vectors into one L2-normalized vector.

    Mean-pooling mirrors the model's own pooling so the combined vector represents
    the whole input; re-normalizing keeps it a unit vector for cosine similarity.

    Args:
        vectors: The per-piece vectors to combine (all the same dimension).

    Returns:
        One L2-normalized vector, or ``None`` if the input is empty, the pieces
        disagree on dimension (pooling mixed dims would silently corrupt or truncate
        the result), or the pooled vector is degenerate (zero norm).
    """
    if not vectors:
        return None
    dim = len(vectors[0])
    # Defense in depth: refuse inconsistently-sized pieces rather than emit a
    # corrupt vector (component-wise sum would drop/zero the mismatched tail).
    if any(len(vector) != dim for vector in vectors):
        return None
    summed = [0.0] * dim
    for vector in vectors:
        for index, component in enumerate(vector):
            summed[index] += component
    count = len(vectors)
    mean = [component / count for component in summed]
    norm = math.sqrt(sum(component * component for component in mean))
    if norm == 0.0:
        return None
    return [component / norm for component in mean]


class ResilientEmbedder:
    """Wrap a backend ``request_fn`` with retry, sub-split, and finiteness guards."""

    def __init__(
        self,
        request_fn: RequestFn,
        token_counter: VoyageTokenCounter,
        max_input_tokens: int,
        dim: int | None = None,
        max_retries: int = 5,
        sleep_fn: SleepFn | None = None,
    ) -> None:
        """Configure the resilient wrapper.

        Args:
            request_fn: Backend coroutine that POSTs texts and parses vectors.
            token_counter: Exact tokenizer used to size sub-split pieces.
            max_input_tokens: Hard per-input token cap the endpoint enforces.
            dim: Expected embedding dimension. When set, a returned vector whose
                length differs is quarantined (a wrong-shape vector must never be
                stored under a lying ``dim``). When ``None``, only finiteness is
                checked.
            max_retries: Maximum attempts for a transient (429/5xx/transport) batch.
            sleep_fn: Awaitable sleep used for backoff; defaults to ``asyncio.sleep``
                (injected in tests so retries don't block the suite).
        """
        self._request_fn = request_fn
        self._token_counter = token_counter
        self._max_input_tokens = max_input_tokens
        self._dim = dim
        self._max_retries = max_retries
        self._sleep_fn: SleepFn = sleep_fn or asyncio.sleep

    async def embed_texts(self, texts: list[str]) -> list[list[float] | None]:
        """Embed ``texts`` resiliently, returning one entry per input (``None`` on failure).

        Args:
            texts: The texts to embed (already token-pre-checked upstream; this
                method is the runtime backstop if the pre-check ever diverges).

        Returns:
            A list aligned 1:1 with ``texts``: a finite vector, or ``None`` for a
            permanently-failed or quarantined input.
        """
        if not texts:
            return []
        raw_vectors = await self._request_with_retry(texts)
        if raw_vectors is None:
            # The whole batch permanently failed (exhausted retries or hit the
            # over-length backstop). Resolve each input individually so a single
            # over-length input doesn't sink its batch-mates.
            return await self._resolve_individually(texts)
        # Apply the finiteness quarantine to each returned vector.
        return [self._quarantine(vector) for vector in raw_vectors]

    async def _request_with_retry(self, texts: list[str]) -> list[list[float]] | None:
        """Send ``texts`` once, retrying transient failures with exponential backoff.

        Returns:
            The raw per-input vectors, or ``None`` if the batch could not be
            satisfied (permanent failure, or an over-length 422 that needs the
            per-input sub-split path).
        """
        n_texts = len(texts)
        # The last transient status seen, surfaced in the exhaustion event so an
        # operator knows WHAT was failing (a 429 storm vs a 5xx outage vs a
        # transport drop). ``None`` for a transport error (no HTTP status).
        last_status: int | None = None
        for attempt in range(self._max_retries):
            try:
                result = await self._request_fn(texts)
            except httpx.HTTPStatusError as error:
                status = error.response.status_code
                if status == HTTP_UNPROCESSABLE_ENTITY:
                    # Over-length: not retryable as-is; the caller sub-splits.
                    # Log only the count — never the offending text or the response.
                    logger.info(
                        "embed.over_length.subsplit", extra={"status": status, "n_texts": n_texts}
                    )
                    return None
                if status == HTTP_BAD_REQUEST:
                    # Malformed/unembeddable batch: permanent for this batch.
                    logger.error(
                        "embed.permanent_failure", extra={"status": status, "n_texts": n_texts}
                    )
                    return None
                if status == HTTP_TOO_MANY_REQUESTS or status >= HTTP_SERVER_ERROR_FLOOR:
                    last_status = status
                    await self._backoff(attempt, status=status, n_texts=n_texts)
                    continue
                # Any other 4xx is permanent.
                logger.error(
                    "embed.permanent_failure", extra={"status": status, "n_texts": n_texts}
                )
                return None
            except (httpx.ConnectError, httpx.TimeoutException):
                await self._backoff(attempt, status=None, n_texts=n_texts)
                continue
            except (ValueError, KeyError, TypeError):
                # A 2xx with a malformed/garbage body (JSONDecodeError is a
                # ValueError; a wrong envelope is a KeyError/TypeError) is treated
                # as a permanent batch failure — degrade to None, never crash.
                logger.error(
                    "embed.permanent_failure", extra={"status": last_status, "n_texts": n_texts}
                )
                return None
            # Untrusted-response guard: a response whose length disagrees with the
            # request is unsafe to map (short -> IndexError/mis-map; long/permuted
            # -> wrong vector bound to wrong chunk == corpus poisoning). Reject it
            # so the caller falls back to aligned per-input resolution.
            if len(result) != len(texts):
                logger.error(
                    "embed.permanent_failure", extra={"status": last_status, "n_texts": n_texts}
                )
                return None
            return result
        # Retry budget exhausted.
        logger.error("embed.permanent_failure", extra={"status": last_status, "n_texts": n_texts})
        return None

    async def _resolve_individually(self, texts: list[str]) -> list[list[float] | None]:
        """Resolve each input on its own — sub-splitting any that is over-length.

        Used when a batch came back unsatisfiable. An input within the token cap is
        embedded directly (one more isolated attempt); an over-length input is
        sub-split into ≤cap pieces, each embedded, and mean-pooled back to one
        vector.
        """
        resolved: list[list[float] | None] = []
        for text in texts:
            if self._token_counter.count(text) > self._max_input_tokens:
                resolved.append(await self._embed_over_length(text))
            else:
                resolved.append(await self._embed_single(text))
        return resolved

    async def _embed_single(self, text: str) -> list[float] | None:
        """Embed one within-cap text, returning its quarantined vector or ``None``."""
        raw_vectors = await self._request_with_retry([text])
        if not raw_vectors:
            return None
        return self._quarantine(raw_vectors[0])

    async def _embed_over_length(self, text: str) -> list[float] | None:
        """Sub-split an over-length text by tokens, embed pieces, mean-pool to one vector.

        Args:
            text: An input whose token count exceeds ``max_input_tokens``.

        Returns:
            One finite, re-normalized vector covering the content, or ``None`` if
            any piece permanently failed.
        """
        pieces = split_to_fit(text, self._token_counter, self._max_input_tokens)
        piece_vectors: list[list[float]] = []
        for piece in pieces:
            vector = await self._embed_single(piece)
            if vector is None:
                # A piece failed -> the whole input is a permanent failure.
                return None
            piece_vectors.append(vector)
        return mean_pool(piece_vectors)

    def _quarantine(self, vector: list[float]) -> list[float] | None:
        """Return ``vector`` only if it is the right shape and all-finite; else ``None``.

        Two ways an untrusted vector poisons the corpus, both rejected here:

        * Non-finite component (NaN/inf) — poisons cosine similarity and argmax
          across every query.
        * Wrong dimension — would be stored under a lying ``dim`` and silently break
          (or mis-rank) the vector index; ``mean_pool`` would also corrupt on mixed
          dims. Enforced only when an expected ``dim`` was configured.
        """
        if self._dim is not None and len(vector) != self._dim:
            return None
        if all(math.isfinite(component) for component in vector):
            return vector
        return None

    async def _backoff(self, attempt: int, *, status: int | None, n_texts: int) -> None:
        """Log the retry, then sleep for an exponentially growing, capped delay.

        Args:
            attempt: The zero-based attempt index that just failed (drives the
                exponential delay and is surfaced in the event).
            status: The HTTP status that triggered the retry (429/5xx), or
                ``None`` for a transport error (ConnectError/timeout).
            n_texts: The batch size — a count only, never the texts themselves.
        """
        delay = min(BACKOFF_BASE_S * (BACKOFF_GROWTH**attempt), BACKOFF_CAP_S)
        logger.warning(
            "embed.retry.backoff",
            extra={"status": status, "attempt": attempt, "delay_s": delay, "n_texts": n_texts},
        )
        await self._sleep_fn(delay)
