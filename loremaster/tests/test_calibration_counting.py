"""Tests for :mod:`loremaster.calibration.counting`.

The load-bearing test is the WIRE-SHAPE PARITY check: the async counter must issue
a byte-identical ``count_tokens`` request to the survey's reference
``ClaudeTokenCounter`` (``scripts/token_survey.py``) so counts stay comparable to the
generation-anchored baseline forever. The remaining tests cover the retry contract,
the success path, key acquisition, and client-ownership lifecycle.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

# The survey module is the SHAPE REFERENCE. It lives in ``scripts/`` (not a package),
# so make that directory importable — mirrors ``scripts/test_token_survey.py``.
_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import token_survey as ts  # type: ignore[import-not-found]  # noqa: E402  (scripts/ is not a package)
from loremaster.calibration import counting  # noqa: E402

# httpx adds these to every outgoing request itself (host/content-length are derived from
# the URL and body; connection/accept/accept-encoding/user-agent are httpx client defaults) —
# they are transport plumbing, not part of the application-level request shape being pinned
# for parity, so they're excluded from the full-header-set comparison below.
_TRANSPORT_INJECTED_HEADERS = frozenset(
    {"host", "content-length", "connection", "accept", "accept-encoding", "user-agent"}
)


def _recording_transport(recorded: list[httpx.Request], response: httpx.Response) -> httpx.MockTransport:
    """A MockTransport that records each request and returns ``response``."""

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        return response

    return httpx.MockTransport(handler)


class TestConstantsParity:
    def test_endpoint_version_key_env_match_survey(self) -> None:
        assert counting.ANTHROPIC_COUNT_TOKENS_URL == ts.ANTHROPIC_COUNT_TOKENS_URL
        assert counting.ANTHROPIC_VERSION == ts.ANTHROPIC_VERSION
        assert counting.ANTHROPIC_API_KEY_ENV == ts.ANTHROPIC_API_KEY_ENV
        assert counting.DEFAULT_ENV_FILE == ts.DEFAULT_ENV_FILE


class TestRequestShapeParity:
    async def test_wire_shape_is_byte_identical_to_survey_counter(self) -> None:
        text = "def add(a, b):\n    return a + b  # dense\n"
        api_key = "sk-parity-fixture"
        model = "claude-sonnet-5"

        sync_recorded: list[httpx.Request] = []
        sync_client = httpx.Client(
            transport=_recording_transport(sync_recorded, httpx.Response(200, json={"input_tokens": 11}))
        )
        survey_counter = ts.ClaudeTokenCounter(api_key, model=model, client=sync_client)
        survey_counter.count(text)
        survey_counter.close()

        async_recorded: list[httpx.Request] = []
        async_client = httpx.AsyncClient(
            transport=_recording_transport(async_recorded, httpx.Response(200, json={"input_tokens": 11}))
        )
        async_counter = counting.AsyncClaudeTokenCounter(
            SecretStr(api_key), model=model, client=async_client
        )
        await async_counter.count(text)
        await async_counter.aclose()

        survey_request = sync_recorded[0]
        async_request = async_recorded[0]

        # Method + URL identical, and equal to the pinned endpoint constant.
        assert async_request.method == survey_request.method == "POST"
        assert str(async_request.url) == str(survey_request.url) == counting.ANTHROPIC_COUNT_TOKENS_URL
        # Body wrapping byte-for-byte identical, and equal to the expected shape.
        assert async_request.content == survey_request.content
        assert json.loads(async_request.content) == {
            "model": model,
            "messages": [{"role": "user", "content": text}],
        }
        # The three explicit auth/version headers identical.
        for header in ("x-api-key", "anthropic-version", "content-type"):
            assert async_request.headers[header] == survey_request.headers[header]
        assert async_request.headers["anthropic-version"] == counting.ANTHROPIC_VERSION
        # Full application-level header-KEY-SET parity: a future one-sided header (e.g.
        # anthropic-beta added to only one counter) must fail here, not just the three
        # named headers above.
        survey_header_keys = {k.lower() for k in survey_request.headers.keys()} - _TRANSPORT_INJECTED_HEADERS
        async_header_keys = {k.lower() for k in async_request.headers.keys()} - _TRANSPORT_INJECTED_HEADERS
        assert survey_header_keys.symmetric_difference(async_header_keys) == set()
        for header in survey_header_keys:
            assert async_request.headers[header] == survey_request.headers[header]


class TestCountBehavior:
    async def test_count_returns_input_tokens(self) -> None:
        recorded: list[httpx.Request] = []
        client = httpx.AsyncClient(
            transport=_recording_transport(recorded, httpx.Response(200, json={"input_tokens": 123}))
        )
        counter = counting.AsyncClaudeTokenCounter(SecretStr("k"), client=client)
        assert await counter.count("hello") == 123
        await counter.aclose()

    async def test_default_model_is_current_generation_anchor(self) -> None:
        counter = counting.AsyncClaudeTokenCounter(SecretStr("k"))
        assert counter.model == counting.DEFAULT_MODEL == "claude-sonnet-5"
        await counter.aclose()


class TestRetryContract:
    async def test_retries_on_429_then_succeeds(self) -> None:
        attempts: list[int] = []
        slept: list[float] = []

        def handler(request: httpx.Request) -> httpx.Response:
            attempts.append(1)
            if len(attempts) < 3:
                return httpx.Response(429, json={})
            return httpx.Response(200, json={"input_tokens": 42})

        async def fake_sleep(delay: float) -> None:
            slept.append(delay)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        counter = counting.AsyncClaudeTokenCounter(SecretStr("k"), client=client, sleep=fake_sleep)
        assert await counter.count("hi") == 42
        assert len(attempts) == 3
        assert len(slept) == 2  # slept before each of the two retries
        await counter.aclose()

    async def test_retry_after_header_is_honoured(self) -> None:
        slept: list[float] = []
        attempts: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            attempts.append(1)
            if len(attempts) == 1:
                return httpx.Response(429, headers={"retry-after": "7"}, json={})
            return httpx.Response(200, json={"input_tokens": 5})

        async def fake_sleep(delay: float) -> None:
            slept.append(delay)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        counter = counting.AsyncClaudeTokenCounter(SecretStr("k"), client=client, sleep=fake_sleep)
        await counter.count("hi")
        assert slept == [7.0]
        await counter.aclose()

    async def test_non_retryable_4xx_raises_immediately(self) -> None:
        attempts: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            attempts.append(1)
            return httpx.Response(400, text="bad request")

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        counter = counting.AsyncClaudeTokenCounter(SecretStr("k"), client=client)
        with pytest.raises(RuntimeError):
            await counter.count("hi")
        assert len(attempts) == 1  # no retry on a non-429 4xx
        await counter.aclose()

    async def test_non_retryable_4xx_raises_typed_terminal_error(self) -> None:
        """A permanent 4xx (bad key / 400) raises the TYPED terminal error so a caller can
        tell it apart from retry-exhaustion — while staying a ``RuntimeError`` subclass so
        the counter's documented ``RuntimeError`` contract is unbroken."""
        assert issubclass(counting.TerminalCountError, RuntimeError)

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, text="invalid x-api-key")

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        counter = counting.AsyncClaudeTokenCounter(SecretStr("k"), client=client)
        with pytest.raises(counting.TerminalCountError):
            await counter.count("hi")
        await counter.aclose()

    async def test_exhausted_retries_raises_plain_not_terminal(self) -> None:
        """Retry-exhaustion (429/5xx forever) is NOT a terminal error — it raises a plain
        ``RuntimeError`` that is *not* a ``TerminalCountError``, so the engine keeps retrying
        it as a transient outage instead of disabling the probe."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={})

        async def fake_sleep(delay: float) -> None:
            return None

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        counter = counting.AsyncClaudeTokenCounter(
            SecretStr("k"), client=client, max_retries=2, sleep=fake_sleep
        )
        with pytest.raises(RuntimeError) as exc_info:
            await counter.count("hi")
        assert not isinstance(exc_info.value, counting.TerminalCountError)
        await counter.aclose()

    async def test_exhausting_retries_raises(self) -> None:
        attempts: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            attempts.append(1)
            return httpx.Response(503, json={})

        async def fake_sleep(delay: float) -> None:
            return None

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        counter = counting.AsyncClaudeTokenCounter(
            SecretStr("k"), client=client, max_retries=3, sleep=fake_sleep
        )
        with pytest.raises(RuntimeError):
            await counter.count("hi")
        assert len(attempts) == 3
        await counter.aclose()


class TestApiKeyAcquisition:
    def test_prefers_exported_env(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv(counting.ANTHROPIC_API_KEY_ENV, "from-env")
        env_file = tmp_path / ".env"
        env_file.write_text(f"{counting.ANTHROPIC_API_KEY_ENV}=from-file\n", encoding="utf-8")
        # Unwrapped DELIBERATELY: ``load_api_key`` returns a ``SecretStr`` (#211),
        # so a bare ``==`` against the value would be False — which is the point.
        assert counting.load_api_key(env_file).get_secret_value() == "from-env"

    def test_parses_env_file_when_unset(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.delenv(counting.ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text(f'{counting.ANTHROPIC_API_KEY_ENV}="from-file"\n', encoding="utf-8")
        assert counting.load_api_key(env_file).get_secret_value() == "from-file"

    def test_raises_when_key_absent_everywhere(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.delenv(counting.ANTHROPIC_API_KEY_ENV, raising=False)
        with pytest.raises(RuntimeError):
            counting.load_api_key(tmp_path / "does-not-exist.env")


class TestClientOwnershipLifecycle:
    async def test_owned_client_is_closed_on_aclose(self) -> None:
        counter = counting.AsyncClaudeTokenCounter(SecretStr("k"))  # constructs & owns its client
        internal_client = counter._client
        await counter.aclose()
        assert internal_client.is_closed

    async def test_injected_client_is_not_closed_by_counter(self) -> None:
        client = httpx.AsyncClient(
            transport=_recording_transport([], httpx.Response(200, json={"input_tokens": 1}))
        )
        counter = counting.AsyncClaudeTokenCounter(SecretStr("k"), client=client)
        await counter.aclose()
        assert not client.is_closed  # the injector still owns it
        await client.aclose()

    async def test_works_as_async_context_manager(self) -> None:
        client = httpx.AsyncClient(
            transport=_recording_transport([], httpx.Response(200, json={"input_tokens": 9}))
        )
        async with counting.AsyncClaudeTokenCounter(SecretStr("k"), client=client) as counter:
            assert await counter.count("x") == 9
        assert not client.is_closed
        await client.aclose()
