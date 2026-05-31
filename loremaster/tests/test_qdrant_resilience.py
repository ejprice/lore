"""Contract tests for ``QdrantStore`` transient-failure resilience (Layer 1).

A long cold-index crashed on an UNCAUGHT Qdrant 500 (``UnexpectedResponse``)
two-thirds of the way through. The embedder already has resilient retry/backoff
(:mod:`loresigil.resilient`); the store did NOT — so a single transient Qdrant
hiccup killed the whole batch. This module pins the store-level fix: every
network op retries a TRANSIENT failure with capped exponential backoff up to a
cap, then raises; a PERMANENT (4xx) failure fails fast and is never retried.

These are UNIT tests over a FAKE client (a stub exposing exactly the
``AsyncQdrantClient`` methods :class:`QdrantStore` calls) — NO real Qdrant. The
fake lets a test script a precise failure sequence (raise N times, then succeed)
and assert the retry COUNT and that backoff actually slept, deterministically and
offline. The backoff ``sleep_fn`` is injected so the suite never really sleeps.

Transient (retried): ``UnexpectedResponse`` with a 5xx status, ``httpx``
transport errors (``ConnectError`` / ``ReadTimeout`` / ``PoolTimeout`` /
``TimeoutException``), and ``ResponseHandlingException``. Permanent (fail-fast):
``UnexpectedResponse`` with a 4xx status (bad request / dim mismatch).

The independent oracle is the count of attempts the fake observed and the
recorded backoff delays — never the implementation's own bookkeeping.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest
from loremaster.index.records import Record
from loremaster.store.qdrant import QdrantStore
from qdrant_client.common.client_exceptions import ResourceExhaustedResponse
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

_DIM = 8
_SLUG = "resilience"


def _unexpected_response(status_code: int) -> UnexpectedResponse:
    """Build an ``UnexpectedResponse`` carrying ``status_code`` (the Qdrant 5xx/4xx shape)."""
    return UnexpectedResponse(
        status_code=status_code,
        reason_phrase="error",
        content=b"task panicked",
        headers=httpx.Headers(),
    )


def _record() -> Record:
    """A minimal valid :class:`Record` for an upsert pair."""
    return Record(
        point_id="00000000-0000-0000-0000-000000000001",
        embedding_text="text",
        payload={"tier": "custom", "file_path": "a.py", "content_hash": "h", "chunk_type": "x"},
    )


class _ScriptedClient:
    """A fake ``AsyncQdrantClient`` whose ``upsert`` follows a scripted error plan.

    ``errors`` is a list of exceptions (or ``None`` for success) consumed one per
    call: the first call raises ``errors[0]``, the second ``errors[1]``, and so
    on; once exhausted (or on a ``None`` entry) the call succeeds. ``calls``
    records how many times ``upsert`` was actually invoked — the independent
    retry-count oracle.
    """

    def __init__(self, errors: list[BaseException | None]) -> None:
        self._errors = list(errors)
        self.calls = 0

    async def upsert(self, **_kwargs: Any) -> None:
        self.calls += 1
        if self._errors:
            error = self._errors.pop(0)
            if error is not None:
                raise error
        return None


def _record_sleep() -> tuple[list[float], Any]:
    """Return ``(recorded_delays, sleep_fn)`` — captures backoff delays without waiting."""
    recorded: list[float] = []

    async def fake_sleep(delay: float) -> None:
        recorded.append(delay)

    return recorded, fake_sleep


def _store(client: Any, *, max_retries: int = 5) -> tuple[QdrantStore, list[float]]:
    """Build a :class:`QdrantStore` over a fake client + an injected no-wait sleep."""
    recorded, fake_sleep = _record_sleep()
    store = QdrantStore(client=client, slug=_SLUG, max_retries=max_retries, sleep_fn=fake_sleep)
    return store, recorded


class TestTransientRetry:
    """A transient (5xx / transport) failure is retried with backoff, then succeeds."""

    async def test_500_then_success_is_retried_and_backs_off(self) -> None:
        # Adversarial: the real crash signature — one 500 UnexpectedResponse, then
        # the op succeeds. The store must retry (NOT surface the 500) and the
        # backoff sleep must have fired before the retry.
        client = _ScriptedClient([_unexpected_response(500), None])
        store, delays = _store(client)
        await store.upsert([(_record(), [0.1] * _DIM)])
        assert client.calls == 2  # retried exactly once
        assert len(delays) == 1 and delays[0] > 0  # backed off before the retry

    async def test_connect_error_then_success_is_retried(self) -> None:
        client = _ScriptedClient([httpx.ConnectError("connection refused"), None])
        store, delays = _store(client)
        await store.upsert([(_record(), [0.1] * _DIM)])
        assert client.calls == 2
        assert len(delays) == 1

    async def test_read_timeout_then_success_is_retried(self) -> None:
        client = _ScriptedClient([httpx.ReadTimeout("read timed out"), None])
        store, delays = _store(client)
        await store.upsert([(_record(), [0.1] * _DIM)])
        assert client.calls == 2

    async def test_response_handling_exception_then_success_is_retried(self) -> None:
        client = _ScriptedClient(
            [ResponseHandlingException(httpx.ConnectError("boom")), None]
        )
        store, delays = _store(client)
        await store.upsert([(_record(), [0.1] * _DIM)])
        assert client.calls == 2

    async def test_backoff_is_exponential(self) -> None:
        # Three transient failures then success → delays strictly grow, so a burst
        # can't hammer the server.
        client = _ScriptedClient(
            [_unexpected_response(503), _unexpected_response(503), _unexpected_response(503), None]
        )
        store, delays = _store(client)
        await store.upsert([(_record(), [0.1] * _DIM)])
        assert client.calls == 4
        assert len(delays) == 3
        assert delays[0] < delays[1] < delays[2]


class TestResourceExhausted429:
    """A 429+``Retry-After`` raises ``ResourceExhaustedResponse`` — a transient.

    qdrant-client 1.18.0 raises ``ResourceExhaustedResponse`` (a ``QdrantException``,
    NOT an ``UnexpectedResponse``) for a 429 that carries a ``Retry-After`` header
    — the textbook "server overloaded, back off" signal. It MUST be retried (it is
    the most explicitly-transient failure there is), and when it persists past the
    cap it must re-raise — bounded, like every other transient. A 429 WITHOUT a
    ``Retry-After`` is already a 4xx ``UnexpectedResponse`` (handled by fail-fast).
    """

    async def test_429_retry_after_then_success_is_retried(self) -> None:
        # Adversarial: the overload signature this feature exists to survive. One
        # ResourceExhaustedResponse, then success → the store must RETRY it, not
        # surface it and crash the index.
        client = _ScriptedClient(
            [ResourceExhaustedResponse("rate limited", retry_after_s=3), None]
        )
        store, delays = _store(client)
        await store.upsert([(_record(), [0.1] * _DIM)])
        assert client.calls == 2  # retried exactly once (transient)
        assert len(delays) == 1 and delays[0] > 0  # backed off before the retry

    async def test_429_honors_server_retry_after_for_the_backoff_delay(self) -> None:
        # The server told us EXACTLY how long to wait (retry_after_s). The backoff
        # must honor that value, not the computed exponential delay — otherwise we
        # retry sooner than the server permitted and get rate-limited again.
        # attempt-0 computed backoff would be 1.0s; the server says 7s, so a 7.0s
        # delay proves the server value won (and is distinguishable from computed).
        client = _ScriptedClient(
            [ResourceExhaustedResponse("rate limited", retry_after_s=7), None]
        )
        store, delays = _store(client)
        await store.upsert([(_record(), [0.1] * _DIM)])
        assert delays == [7.0]

    async def test_persistent_429_raises_after_cap_bounded(self) -> None:
        # A persistent overload must NOT loop forever: attempt exactly max_retries,
        # then re-raise the ResourceExhaustedResponse.
        client = _ScriptedClient(
            [ResourceExhaustedResponse("rate limited", retry_after_s=1)] * 100
        )
        store, delays = _store(client, max_retries=4)
        with pytest.raises(ResourceExhaustedResponse):
            await store.upsert([(_record(), [0.1] * _DIM)])
        assert client.calls == 4  # bounded by the cap, not infinite
        assert len(delays) == 3  # one fewer sleep than attempts


class TestPermanentFailFast:
    """A permanent (4xx) failure is raised immediately and NEVER retried."""

    async def test_400_is_not_retried(self) -> None:
        # A 4xx (bad request / dim mismatch) is permanent: fail fast, zero retries,
        # zero backoff sleeps.
        client = _ScriptedClient([_unexpected_response(400), None])
        store, delays = _store(client)
        with pytest.raises(UnexpectedResponse) as excinfo:
            await store.upsert([(_record(), [0.1] * _DIM)])
        assert excinfo.value.status_code == 400
        assert client.calls == 1  # NOT retried
        assert delays == []  # no backoff at all

    async def test_404_is_not_retried(self) -> None:
        client = _ScriptedClient([_unexpected_response(404), None])
        store, delays = _store(client)
        with pytest.raises(UnexpectedResponse):
            await store.upsert([(_record(), [0.1] * _DIM)])
        assert client.calls == 1
        assert delays == []


class TestRetryExhaustion:
    """A transient error that PERSISTS past the cap raises (bounded, no infinite loop)."""

    async def test_persistent_500_raises_after_cap_bounded(self) -> None:
        # The op fails transiently forever. The wrapper must NOT loop forever: it
        # attempts exactly ``max_retries`` times then re-raises the last error.
        client = _ScriptedClient([_unexpected_response(500)] * 100)
        store, delays = _store(client, max_retries=4)
        with pytest.raises(UnexpectedResponse) as excinfo:
            await store.upsert([(_record(), [0.1] * _DIM)])
        assert excinfo.value.status_code == 500
        assert client.calls == 4  # bounded by the cap, not infinite
        # One fewer backoff than attempts (no sleep after the final, failing try).
        assert len(delays) == 3
