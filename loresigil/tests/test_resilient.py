"""Contract tests for ``loresigil.resilient`` — the shared request wrapper.

Both embedders route every request through :class:`ResilientEmbedder`. Its job is
to turn a *fragile* single-shot "POST these texts, parse vectors" callable into a
resilient one that **never crashes and never silently stores garbage**:

* **429** (the TEI 64-concurrency guard) → exponential backoff + retry.
* **5xx / ConnectError / timeout** → exponential backoff + retry.
* **422 / over-length** → catch, **sub-split the offending input by tokens** and
  re-embed the pieces through the same path (a runtime backstop on top of the
  upstream ≤8192 pre-check). The sub-split must yield finite vectors covering the
  content, never a 422 bubbling out.
* **Non-finite vector** (NaN / inf from the model) → reject/quarantine. A
  non-finite component poisons cosine/argmax across *every* query, so it must
  come back as ``None`` (permanent failure for that input), never as a stored
  vector.
* **Permanent failure** after the retry budget is exhausted → ``None`` for that
  input, positionally.

The transport is a *mocked* ``httpx.MockTransport`` (offline, deterministic) — the
live ``TEI`` endpoint is reserved for the deploy healthcheck, not unit tests.
Backoff sleeps are injected so retries don't make the suite slow.

The independent oracle for "is this vector clean" is :func:`math.isfinite` applied
here in the test — never the implementation's own check.
"""

from __future__ import annotations

import logging
import math

import httpx
import pytest
from loresigil.resilient import ResilientEmbedder
from loresigil.tokens import VoyageTokenCounter

# The dotted logger name the resilient wrapper emits under (module ``__name__``).
RESILIENT_LOGGER = "loresigil.resilient"

# --- Real fixtures grounded in the voyage-4-nano tokenizer --------------------
# A 13-token warehouse-ops sentence (verified via VoyageTokenCounter offline).
SENTENCE: str = (
    "The quarterly safety report summarizes incident rates across all warehouse facilities. "
)
# unit*750 == 9001 tokens (verified) — genuinely OVER the 8192 cap, the case the
# 422 sub-split backstop exists for. Its two char-halves are 4501 tokens each
# (both under the cap), so a single bisection suffices.
OVER_LIMIT_TEXT: str = SENTENCE * 750
MAX_INPUT_TOKENS: int = 8192
EMBED_DIM: int = 2048

# A finite unit-ish vector and a poisoned one, built independently of the impl.
GOOD_VECTOR: list[float] = [0.1] * EMBED_DIM
NAN_VECTOR: list[float] = [float("nan")] + [0.1] * (EMBED_DIM - 1)
INF_VECTOR: list[float] = [float("inf")] + [0.1] * (EMBED_DIM - 1)


def _no_sleep_factory() -> tuple[list[float], object]:
    """Return (recorded_delays, sleep_fn) — captures backoff delays without waiting."""
    recorded: list[float] = []

    async def fake_sleep(delay: float) -> None:
        recorded.append(delay)

    return recorded, fake_sleep


def _make_resilient(
    request_fn: object,
    *,
    max_retries: int = 5,
) -> tuple[ResilientEmbedder, list[float]]:
    """Build a ResilientEmbedder over an injected request callable + fake sleep.

    ``request_fn`` is the backend-specific "POST texts -> list[vector]" coroutine
    function. It may raise ``httpx.HTTPStatusError`` (carrying a 429/422/5xx
    response) or ``httpx.ConnectError`` / ``httpx.TimeoutException``.
    """
    recorded_delays, fake_sleep = _no_sleep_factory()
    embedder = ResilientEmbedder(
        request_fn=request_fn,  # type: ignore[arg-type]
        token_counter=VoyageTokenCounter(),
        max_input_tokens=MAX_INPUT_TOKENS,
        max_retries=max_retries,
        sleep_fn=fake_sleep,  # type: ignore[arg-type]
    )
    return embedder, recorded_delays


def _status_error(status_code: int) -> httpx.HTTPStatusError:
    """Build an httpx.HTTPStatusError carrying a response with ``status_code``."""
    request = httpx.Request("POST", "http://embedder.test/embed")
    response = httpx.Response(status_code, request=request, text="error body")
    return httpx.HTTPStatusError("err", request=request, response=response)


class TestRetriesOn429:
    """A 429 (concurrency guard) is retried with backoff, then succeeds."""

    async def test_429_then_200_is_retried_and_succeeds(self) -> None:
        # Adversarial: first call raises 429, second returns a clean vector. The
        # wrapper must back off and retry — not surface the 429, not drop the input.
        calls = 0

        async def request_fn(texts: list[str]) -> list[list[float]]:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise _status_error(429)
            return [GOOD_VECTOR for _ in texts]

        embedder, delays = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE])

        assert calls == 2  # retried exactly once
        assert len(vectors) == 1
        assert vectors[0] == GOOD_VECTOR
        assert len(delays) == 1 and delays[0] > 0  # backed off before retry


class TestRetriesOn5xxAndTransport:
    """5xx, ConnectError and timeout all back off and retry."""

    async def test_503_then_200_is_retried(self) -> None:
        calls = 0

        async def request_fn(texts: list[str]) -> list[list[float]]:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise _status_error(503)
            return [GOOD_VECTOR for _ in texts]

        embedder, delays = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE])
        assert calls == 2
        assert vectors == [GOOD_VECTOR]
        assert len(delays) == 1

    async def test_connect_error_then_200_is_retried(self) -> None:
        calls = 0

        async def request_fn(texts: list[str]) -> list[list[float]]:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise httpx.ConnectError("connection refused")
            return [GOOD_VECTOR for _ in texts]

        embedder, _ = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE])
        assert calls == 2
        assert vectors == [GOOD_VECTOR]

    async def test_backoff_is_exponential(self) -> None:
        # Three transient failures then success -> delays must be non-decreasing
        # and strictly grow (exponential), so a burst can't hammer the box.
        calls = 0

        async def request_fn(texts: list[str]) -> list[list[float]]:
            nonlocal calls
            calls += 1
            if calls <= 3:
                raise _status_error(429)
            return [GOOD_VECTOR for _ in texts]

        embedder, delays = _make_resilient(request_fn)
        await embedder.embed_texts([SENTENCE])
        assert len(delays) == 3
        # Exponential: each delay strictly larger than the previous.
        assert delays[0] < delays[1] < delays[2]


class TestPermanentFailureYieldsNone:
    """Exhausting the retry budget marks the input as a permanent ``None``."""

    async def test_persistent_5xx_returns_none_aligned(self) -> None:
        async def request_fn(texts: list[str]) -> list[list[float]]:
            raise _status_error(500)

        embedder, _ = _make_resilient(request_fn, max_retries=3)
        vectors = await embedder.embed_texts([SENTENCE])
        # Never crashes; the input comes back as a permanent failure (None),
        # positionally aligned (one input -> one None).
        assert vectors == [None]


class TestNonFiniteIsQuarantined:
    """A NaN/inf vector is rejected and never surfaced as a stored vector."""

    async def test_nan_vector_becomes_none(self) -> None:
        # The endpoint returns a structurally valid response whose vector contains
        # a NaN. The independent oracle (math.isfinite) says it's poison; the
        # wrapper MUST quarantine it to None, never return it.
        async def request_fn(texts: list[str]) -> list[list[float]]:
            return [NAN_VECTOR for _ in texts]

        embedder, _ = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE])
        assert vectors == [None]
        # Defense in depth: whatever came back must contain no non-finite floats.
        for vector in vectors:
            if vector is not None:
                assert all(math.isfinite(component) for component in vector)

    async def test_inf_vector_becomes_none(self) -> None:
        async def request_fn(texts: list[str]) -> list[list[float]]:
            return [INF_VECTOR for _ in texts]

        embedder, _ = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE])
        assert vectors == [None]

    async def test_finite_vectors_pass_through_unchanged(self) -> None:
        # Control: a clean vector is returned verbatim, proving the guard does not
        # mangle good data.
        async def request_fn(texts: list[str]) -> list[list[float]]:
            return [GOOD_VECTOR for _ in texts]

        embedder, _ = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([SENTENCE])
        assert vectors == [GOOD_VECTOR]


class TestOverLengthSubSplitBackstop:
    """A 422/over-length input is sub-split by tokens and re-embedded."""

    async def test_422_triggers_subsplit_into_finite_pieces(self) -> None:
        # The endpoint rejects any batch containing the over-limit text with a 422.
        # Once that text is split into ≤8192-token pieces, the same endpoint
        # accepts them. The wrapper must: catch the 422, sub-split by tokens,
        # re-embed the pieces (each now finite), and return ONE finite vector for
        # the original input (the pieces recombined / first-piece policy — the
        # contract is: a finite vector, never a None, never a surfaced 422).
        counter = VoyageTokenCounter()
        assert counter.count(OVER_LIMIT_TEXT) > MAX_INPUT_TOKENS  # genuinely over

        seen_batches: list[list[str]] = []

        async def request_fn(texts: list[str]) -> list[list[float]]:
            seen_batches.append(list(texts))
            # Reject if ANY text exceeds the cap (mirrors TEI --auto-truncate false).
            if any(counter.count(text) > MAX_INPUT_TOKENS for text in texts):
                raise _status_error(422)
            return [GOOD_VECTOR for _ in texts]

        embedder, _ = _make_resilient(request_fn)
        vectors = await embedder.embed_texts([OVER_LIMIT_TEXT])

        # One input in -> one vector out, finite (the content was covered, not dropped).
        assert len(vectors) == 1
        assert vectors[0] is not None
        assert all(math.isfinite(component) for component in vectors[0])
        # The wrapper actually re-sent SMALLER pieces (proof it sub-split, didn't
        # just retry the same over-length payload): at least one later batch
        # contained only texts that individually fit the cap.
        assert any(
            batch and all(counter.count(text) <= MAX_INPUT_TOKENS for text in batch)
            for batch in seen_batches[1:]
        )

    async def test_subsplit_pieces_each_within_token_cap(self) -> None:
        # Every piece the wrapper ultimately sends after a 422 must individually be
        # ≤ the cap — otherwise the split didn't actually solve the over-length.
        counter = VoyageTokenCounter()
        accepted_texts: list[str] = []

        async def request_fn(texts: list[str]) -> list[list[float]]:
            if any(counter.count(text) > MAX_INPUT_TOKENS for text in texts):
                raise _status_error(422)
            accepted_texts.extend(texts)
            return [GOOD_VECTOR for _ in texts]

        embedder, _ = _make_resilient(request_fn)
        await embedder.embed_texts([OVER_LIMIT_TEXT])

        assert accepted_texts  # something was eventually accepted
        for text in accepted_texts:
            assert counter.count(text) <= MAX_INPUT_TOKENS


class TestResilientLogging:
    """Structured-logging events on the resilience seams (caplog-asserted).

    The events ride a static event string + ``extra={...}`` — variable data
    (status/attempt/delay/n_texts) is in ``extra``, never interpolated into the
    message. No secret, header, or response object is ever logged; only counts
    and statuses.
    """

    async def test_429_emits_retry_backoff_event(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        calls = 0

        async def request_fn(texts: list[str]) -> list[list[float]]:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise _status_error(429)
            return [GOOD_VECTOR for _ in texts]

        embedder, _ = _make_resilient(request_fn)
        with caplog.at_level(logging.WARNING, logger=RESILIENT_LOGGER):
            await embedder.embed_texts([SENTENCE])

        events = [r for r in caplog.records if r.message == "embed.retry.backoff"]
        assert len(events) == 1
        record = events[0]
        assert record.levelno == logging.WARNING
        assert record.status == 429  # type: ignore[attr-defined]
        assert record.attempt == 0  # type: ignore[attr-defined]  # first attempt, 0-based
        assert record.delay_s > 0  # type: ignore[attr-defined]
        assert record.n_texts == 1  # type: ignore[attr-defined]

    async def test_5xx_emits_retry_backoff_event_with_status(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        calls = 0

        async def request_fn(texts: list[str]) -> list[list[float]]:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise _status_error(503)
            return [GOOD_VECTOR for _ in texts]

        embedder, _ = _make_resilient(request_fn)
        with caplog.at_level(logging.WARNING, logger=RESILIENT_LOGGER):
            await embedder.embed_texts([SENTENCE])
        events = [r for r in caplog.records if r.message == "embed.retry.backoff"]
        assert events and events[0].status == 503  # type: ignore[attr-defined]

    async def test_422_emits_over_length_subsplit_event(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        counter = VoyageTokenCounter()

        async def request_fn(texts: list[str]) -> list[list[float]]:
            if any(counter.count(text) > MAX_INPUT_TOKENS for text in texts):
                raise _status_error(422)
            return [GOOD_VECTOR for _ in texts]

        embedder, _ = _make_resilient(request_fn)
        with caplog.at_level(logging.INFO, logger=RESILIENT_LOGGER):
            await embedder.embed_texts([OVER_LIMIT_TEXT])

        events = [r for r in caplog.records if r.message == "embed.over_length.subsplit"]
        assert events, "a 422 over-length batch must log embed.over_length.subsplit"
        assert events[0].levelno == logging.INFO
        assert events[0].n_texts == 1  # type: ignore[attr-defined]

    async def test_retry_exhaustion_emits_permanent_failure_event(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        async def request_fn(texts: list[str]) -> list[list[float]]:
            raise _status_error(500)

        embedder, _ = _make_resilient(request_fn, max_retries=3)
        with caplog.at_level(logging.ERROR, logger=RESILIENT_LOGGER):
            await embedder.embed_texts([SENTENCE])

        events = [r for r in caplog.records if r.message == "embed.permanent_failure"]
        assert events, "exhausting retries must log embed.permanent_failure at ERROR"
        record = events[0]
        assert record.levelno == logging.ERROR
        assert record.status == 500  # type: ignore[attr-defined]
        assert record.n_texts == 1  # type: ignore[attr-defined]

    async def test_no_secret_or_response_object_in_resilient_logs(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        # The secret rule: a log call must carry only counts/statuses — never the
        # httpx response object (which holds headers/body). Assert no record's
        # extra carries an httpx.Response and the rendered lines stay scalar.
        async def request_fn(texts: list[str]) -> list[list[float]]:
            raise _status_error(503)

        embedder, _ = _make_resilient(request_fn, max_retries=2)
        with caplog.at_level(logging.DEBUG, logger=RESILIENT_LOGGER):
            await embedder.embed_texts([SENTENCE])
        for record in caplog.records:
            for value in record.__dict__.values():
                assert not isinstance(value, (httpx.Response, httpx.Request))


class TestBatchAlignmentWithMixedOutcomes:
    """A batch with a poison input keeps the other inputs' good vectors aligned."""

    async def test_one_nan_does_not_taint_its_neighbours(self) -> None:
        # Inputs [A, B, C]; the endpoint returns a NaN ONLY for the middle one.
        # Result must be [good, None, good] — alignment preserved, poison isolated.
        async def request_fn(texts: list[str]) -> list[list[float]]:
            output: list[list[float]] = []
            for text in texts:
                output.append(NAN_VECTOR if text == "B" else GOOD_VECTOR)
            return output

        embedder, _ = _make_resilient(request_fn)
        vectors = await embedder.embed_texts(["A", "B", "C"])
        assert len(vectors) == 3
        assert vectors[0] == GOOD_VECTOR
        assert vectors[1] is None
        assert vectors[2] == GOOD_VECTOR
