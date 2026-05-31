"""Security contract tests for the UNTRUSTED-RESPONSE surface of the embedders.

A length/dimension mismatch between request and response is correctness-critical:
the stitch loop maps ``vectors[i]`` back to ``texts[i]``, so a short/long/permuted
response would silently bind the WRONG vector to the WRONG chunk (corpus poisoning),
or crash the batch (violating the never-crash contract). These tests pin the
defensive guards that turn a malformed/garbage 2xx response into an aligned, safe
``None`` rather than corruption or a crash.

All transport is an offline ``httpx.MockTransport`` / an injected ``request_fn`` —
the live endpoint is never touched. The oracles (length equality, ``isfinite``,
dimension) are computed independently in the test, not read from the impl.
"""

from __future__ import annotations

import math

import httpx
from loresigil.resilient import ResilientEmbedder, mean_pool
from loresigil.tokens import VoyageTokenCounter

EMBED_DIM: int = 2048
SENTENCE: str = (
    "The quarterly safety report summarizes incident rates across all warehouse facilities. "
)
GOOD_VECTOR: list[float] = [0.1] * EMBED_DIM
# A vector of the WRONG dimension — structurally finite but the wrong shape.
WRONG_DIM_VECTOR: list[float] = [0.1] * (EMBED_DIM - 1)


async def _never_sleep(delay: float) -> None:
    """Backoff sleep that returns immediately (keeps the suite fast)."""


def _make_resilient(request_fn: object, *, max_retries: int = 3) -> ResilientEmbedder:
    """Build a ResilientEmbedder over an injected request callable, dim-aware."""
    return ResilientEmbedder(
        request_fn=request_fn,  # type: ignore[arg-type]
        token_counter=VoyageTokenCounter(),
        max_input_tokens=8192,
        dim=EMBED_DIM,
        max_retries=max_retries,
        sleep_fn=_never_sleep,
    )


class TestResponseLengthMismatch:
    """A response whose length != the request length must never corrupt alignment."""

    async def test_short_response_does_not_crash_and_returns_aligned_none(self) -> None:
        # Endpoint returns FEWER vectors than inputs (2 for 3). The old stitch loop
        # would IndexError / mis-map; the wrapper must instead detect the mismatch
        # and fall back to per-input resolution. Because the per-input requests ALSO
        # short-return here (still wrong count for a 1-text batch -> 0 vectors), each
        # input ends up a safe, aligned None. Crucially: no crash, length preserved.
        async def request_fn(texts: list[str]) -> list[list[float]]:
            # Always return one fewer than asked (a truncating/buggy server).
            return [GOOD_VECTOR for _ in texts[:-1]]

        embedder = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE, SENTENCE + "B", SENTENCE + "C"])
        # Never raises; output is exactly aligned to the 3 inputs.
        assert len(vectors) == 3
        # A length-mismatched batch is unsafe to map, so every input degrades to None
        # rather than a possibly-wrong vector.
        assert vectors == [None, None, None]

    async def test_long_response_is_rejected_not_silently_passed(self) -> None:
        # Endpoint returns MORE vectors than inputs (a permuted/padded response).
        # Silently slicing would bind arbitrary vectors to chunks -> poisoning.
        async def request_fn(texts: list[str]) -> list[list[float]]:
            return [GOOD_VECTOR for _ in texts] + [GOOD_VECTOR, GOOD_VECTOR]

        embedder = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE, SENTENCE + "B"])
        # Mismatch detected: aligned to the 2 inputs, both safely None (not the
        # extra/garbage vectors silently passed through).
        assert len(vectors) == 2
        assert vectors == [None, None]

    async def test_exact_length_response_passes_through(self) -> None:
        # Control: a correctly-sized response is accepted verbatim.
        async def request_fn(texts: list[str]) -> list[list[float]]:
            return [GOOD_VECTOR for _ in texts]

        embedder = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE, SENTENCE + "B"])
        assert vectors == [GOOD_VECTOR, GOOD_VECTOR]


class TestResponseDimensionValidation:
    """A vector of the wrong dimension is quarantined, never stored with a lying dim."""

    async def test_wrong_dimension_vector_is_quarantined(self) -> None:
        async def request_fn(texts: list[str]) -> list[list[float]]:
            return [WRONG_DIM_VECTOR for _ in texts]

        embedder = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE])
        # Wrong shape -> None (a 2047-d vector must not be returned as if it were
        # 2048-d; downstream cosine/index would silently break or mis-rank).
        assert vectors == [None]

    async def test_correct_dimension_vector_passes(self) -> None:
        async def request_fn(texts: list[str]) -> list[list[float]]:
            return [GOOD_VECTOR for _ in texts]

        embedder = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE])
        assert vectors == [GOOD_VECTOR]
        assert len(vectors[0]) == EMBED_DIM  # type: ignore[arg-type]


class TestMeanPoolDoesNotCorruptOnMixedDims:
    """``mean_pool`` must not emit a corrupt vector from inconsistently-sized pieces."""

    def test_mixed_dimension_pieces_yield_none(self) -> None:
        # If two piece vectors disagree on dimension, summing them component-wise
        # would either crash or silently drop tail components -> a corrupt vector.
        # The pool must refuse and return None instead.
        pieces = [[0.1] * EMBED_DIM, [0.1] * (EMBED_DIM - 5)]
        assert mean_pool(pieces) is None

    def test_consistent_dimension_pieces_pool_to_unit_vector(self) -> None:
        # Control: same-dim pieces pool to one finite, unit-norm vector.
        pieces = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
        pooled = mean_pool(pieces)
        assert pooled is not None
        assert len(pooled) == 3
        # Independent oracle: math.hypot, not the impl's normalization.
        assert math.isclose(math.hypot(*pooled), 1.0, abs_tol=1e-9)


class TestMalformedJsonDegradesToNone:
    """A 2xx body that doesn't parse / lacks the expected shape degrades to None."""

    async def test_value_error_from_request_fn_is_permanent_none(self) -> None:
        # Simulates JSONDecodeError (a ValueError subclass) on a 200 garbage body.
        async def request_fn(texts: list[str]) -> list[list[float]]:
            raise ValueError("Expecting value: line 1 column 1 (char 0)")

        embedder = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE])
        assert vectors == [None]

    async def test_key_error_from_request_fn_is_permanent_none(self) -> None:
        # Simulates a wrong envelope: response.json()["data"] missing.
        async def request_fn(texts: list[str]) -> list[list[float]]:
            raise KeyError("data")

        embedder = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE])
        assert vectors == [None]

    async def test_type_error_from_request_fn_is_permanent_none(self) -> None:
        # Simulates indexing a non-subscriptable body (e.g. data is null).
        async def request_fn(texts: list[str]) -> list[list[float]]:
            raise TypeError("'NoneType' object is not subscriptable")

        embedder = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE])
        assert vectors == [None]


class TestTransportErrorsStillPropagateAndRetry:
    """The new ValueError/KeyError catch must NOT swallow httpx transport retries."""

    async def test_connect_error_still_retried_then_succeeds(self) -> None:
        # Guard against the malformed-body catch being too broad and eating the
        # retryable transport-error path.
        calls = 0

        async def request_fn(texts: list[str]) -> list[list[float]]:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise httpx.ConnectError("connection refused")
            return [GOOD_VECTOR for _ in texts]

        embedder = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE])
        assert calls == 2
        assert vectors == [GOOD_VECTOR]
