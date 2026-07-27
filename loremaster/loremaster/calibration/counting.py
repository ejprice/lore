"""Async Claude token counter — wire-shape-pinned to ``scripts/token_survey.py``.

The ``count_tokens`` REQUEST SHAPE — endpoint URL, ``anthropic-version`` header, and the
message wrapping of the counted text — is IDENTICAL to
:class:`token_survey.ClaudeTokenCounter` (``scripts/token_survey.py``, the READ-ONLY shape
reference). That parity keeps every count comparable to the generation-anchored
``baseline.json`` forever, and is pinned by
``loremaster/tests/test_calibration_counting.py::TestRequestShapeParity`` — which fires
this counter and the survey's through a shared ``httpx.MockTransport`` and asserts: the
request body is byte-identical; the URL and method are identical; and the full
application-level header set (every header minus httpx's own transport-injected ones,
e.g. ``host``, ``content-length``) is identical in both keys and values.

This module does NOT import from ``scripts/`` (not a package); it replicates the shape and
the constants, and the parity test is what guarantees they stay in lock-step.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

import httpx
from pydantic import SecretStr

# ``resolve_secret`` is imported into THIS module's namespace (not called through
# ``config.resolve_secret``) so ``load_api_key`` binds the shared resolver at
# ``counting.resolve_secret`` — the one attribute a caller, or a mutation pin,
# can substitute to prove the routing is real.
from loremaster.config import resolve_secret
from loresigil import backoff

#: Anthropic token-counting endpoint (billed free; no completion generated).
ANTHROPIC_COUNT_TOKENS_URL: str = "https://api.anthropic.com/v1/messages/count_tokens"
ANTHROPIC_VERSION: str = "2023-06-01"
ANTHROPIC_API_KEY_ENV: str = "ANTHROPIC_API_KEY"
#: The generation anchor — count_tokens is byte-identical across the current model
#: generation (sonnet-5 / opus-4-8 / fable-5), so the baseline is generated once here.
DEFAULT_MODEL: str = "claude-sonnet-5"
#: The operator-authorised env file the key is sourced from when not already exported.
DEFAULT_ENV_FILE: Path = Path.home() / "docker" / "mcp" / ".env"

MAX_RETRIES: int = 6
RETRY_BASE_DELAY_S: float = 1.0
RETRY_MAX_DELAY_S: float = 30.0
_HTTP_CLIENT_TIMEOUT_S: float = 60.0
_HTTP_SERVER_ERROR_FLOOR: int = 500
_HTTP_TOO_MANY_REQUESTS: int = 429
_HTTP_OK: int = 200
_ERROR_BODY_SNIPPET: int = 200

#: An async sleep hook — injectable so retry backoff is instant (and deterministic)
#: under test without patching the global :func:`asyncio.sleep`.
AsyncSleep = Callable[[float], Awaitable[None]]


class TerminalCountError(RuntimeError):
    """A permanent, non-retryable ``count_tokens`` failure (a 4xx other than 429).

    Raised on a bad API key / malformed request (401 / 400 / …): retrying cannot heal it,
    so it is a distinct type a caller can catch to STOP instead of treating the failure as
    a transient outage. It subclasses :class:`RuntimeError` so the counter's documented
    ``RuntimeError`` contract still holds — retry-exhaustion stays a *plain* ``RuntimeError``
    (retryable), and only this typed subclass signals the terminal case.
    """


def build_auth_headers(credential: SecretStr) -> dict[str, str]:
    """Build the authenticated ``count_tokens`` request headers (ruling R26).

    **THE TYPED SEAM, and the type IS the instrument.** Three earlier gates all
    keyed on parameter NAMES (``api_key``/``password``, a ``.get_secret_value()``
    call, an ``"api_key" in parameters`` sweep) and a class holding a bare ``str``
    under some other name walked past all three. The name set is unbounded; the
    TYPE is not — so a bare ``str`` reaching an outgoing auth header is a mypy
    error at every call site regardless of what the caller called its variable,
    and an ``AttributeError`` at runtime if one is forced through anyway.

    It returns the FULL header set for the request rather than the auth header
    alone, because the auth header is not separable in practice: a caller that
    merged a seam-built ``x-api-key`` into a locally-built dict would be building
    outgoing headers outside the seam again, which is the shape being closed.
    Returning the whole set also keeps the wire shape of the two counters
    (this one and ``scripts/token_survey.ClaudeTokenCounter``, which imports this
    function) identical BY CONSTRUCTION rather than by the parity test noticing
    later.

    ⚠ **The unwrapped value must not outlive the returned mapping.** Under ruling
    R19's shape B the result is built per request, handed straight to
    ``httpx``, and never stored on an instance — see
    :meth:`AsyncClaudeTokenCounter.count`.

    Args:
        credential: The Anthropic API key, still wrapped.

    Returns:
        The request headers, with the credential's real bytes in ``x-api-key``.
    """
    return {
        "x-api-key": credential.get_secret_value(),
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }


def load_api_key(env_file: Path = DEFAULT_ENV_FILE) -> SecretStr:
    """Resolve the Anthropic API key from the environment or the operator env file.

    A THIN CALLER of the shared resolver, not a lookup of its own (ruling R2). It
    owns exactly two decisions: that this path opts into the operator ``.env``
    workflow — the ONLY call site in the workspace permitted to pass an
    ``env_file`` (ruling R3, so a stray ``.env`` can never become a *server*
    credential source) — and that the failure is reported as a ``RuntimeError``
    naming BOTH the variable and the file, because the shared resolver's
    ``KeyError`` names only the variable and the operator has to be able to fix
    the environment and the file in one step. That translation mirrors
    :func:`loremaster.config.load_config`, which turns the same ``KeyError`` into
    a ``ValueError`` naming the yaml field.

    ``scripts/token_survey.py`` imports this function rather than owning a twin:
    the two used to be byte-divergent copies of one parser (inventory C10), and
    two functions that merely agree today are two functions that diverge tomorrow.

    The key is never logged, printed, or copied.

    Args:
        env_file: The operator ``.env`` consulted when the environment does not
            already export the key.

    Returns:
        The resolved key, wrapped.

    Raises:
        RuntimeError: If no usable key can be found in either source.
    """
    try:
        return resolve_secret(ANTHROPIC_API_KEY_ENV, env_file)
    except KeyError as error:
        raise RuntimeError(
            f"{ANTHROPIC_API_KEY_ENV} not set and not found in {env_file}"
        ) from error


class AsyncClaudeTokenCounter:
    """Counts Claude tokens for a text via the Anthropic ``count_tokens`` endpoint.

    The async analogue of :class:`token_survey.ClaudeTokenCounter`. Retries on 429/5xx
    with exponential backoff, honouring a ``Retry-After`` header when present; other 4xx
    are not retryable and raise. A caller-supplied client is never closed by this counter
    (the injector owns it); a client this counter creates is closed by :meth:`aclose`.
    """

    def __init__(
        self,
        api_key: SecretStr,
        *,
        model: str = DEFAULT_MODEL,
        client: httpx.AsyncClient | None = None,
        max_retries: int = MAX_RETRIES,
        sleep: AsyncSleep | None = None,
    ) -> None:
        self._model = model
        self._max_retries = max_retries
        # SHAPE B, MANDATED BY RULING R19: no auth headers are built here at all —
        # the credential stays WRAPPED on the instance and the headers are built
        # per request in :meth:`count`.
        #
        # The alternative (bake the headers into the client at construction) has
        # TWO arms — an owned client and an injected one — and a build that fixed
        # only one produced a failure set byte-identical to the correct build while
        # leaving every production caller unauthenticated. That is #107's shape:
        # green everywhere, 100% broken in production. One code path has no arm to
        # forget. It also means this counter never rewrites the headers of a client
        # its caller owns.
        self._api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=_HTTP_CLIENT_TIMEOUT_S)
        self._sleep: AsyncSleep = sleep or asyncio.sleep

    @property
    def model(self) -> str:
        return self._model

    def _payload(self, text: str) -> dict[str, object]:
        """The exact request body wrapping — the single seam kept in lock-step with the
        survey counter (``{"model": ..., "messages": [{"role": "user", "content": text}]}``)."""
        return {"model": self._model, "messages": [{"role": "user", "content": text}]}

    async def count(self, text: str) -> int:
        """Return the Claude ``input_tokens`` for ``text``.

        Raises:
            TerminalCountError: On a non-retryable response (a 4xx other than 429) — a
                permanent condition retrying cannot heal.
            RuntimeError: If the endpoint keeps failing past ``max_retries`` (retry
                exhaustion — a plain ``RuntimeError``, distinct from the terminal case).
        """
        payload = self._payload(text)
        last_error = ""
        for attempt in range(self._max_retries):
            try:
                response = await self._client.post(
                    ANTHROPIC_COUNT_TOKENS_URL,
                    headers=build_auth_headers(self._api_key),
                    json=payload,
                )
            except httpx.HTTPError as exc:
                last_error = f"transport:{type(exc).__name__}"
                await self._sleep_backoff(attempt, None)
                continue
            status = response.status_code
            if status == _HTTP_OK:
                return int(response.json()["input_tokens"])
            if status == _HTTP_TOO_MANY_REQUESTS or status >= _HTTP_SERVER_ERROR_FLOOR:
                last_error = f"http:{status}"
                await self._sleep_backoff(attempt, response.headers.get("retry-after"))
                continue
            raise TerminalCountError(
                f"count_tokens failed ({response.status_code}): {response.text[:_ERROR_BODY_SNIPPET]}"
            )
        raise RuntimeError(f"count_tokens exhausted retries ({last_error})")

    async def _sleep_backoff(self, attempt: int, retry_after: str | None) -> None:
        """Sleep before a retry, honouring ``Retry-After`` when the server sets it.

        The exponential path draws from the shared full-jitter policy
        (:func:`loresigil.backoff.jittered_backoff_delay`, finding #207): a rate-limit
        429 is by definition something many concurrent counters hit at once, and a
        deterministic ladder would send every one of them back at the same instant.

        The ``Retry-After`` path is jittered too (#207 D2), but **ADDITIVELY** — every
        rate-limited client is handed the SAME ``Retry-After`` by the server, so that
        path is more perfectly lockstepped than the exponential ladder ever was. The
        jitter is added on top of the capped value and never subtracts
        (:func:`loresigil.backoff.additive_jitter`): retrying sooner than a rate
        limiter instructed is a worse bug than the herd it would fix.

        ⚠ The pre-existing ``min(…, RETRY_MAX_DELAY_S)`` cap is UNCHANGED and can still
        sleep less than a large ``Retry-After`` asks (a `Retry-After: 120` yields ~30 s).
        That conflict predates this change and is finding **#223** — it is deliberately
        NOT settled here, and the additive jitter must not be read as having settled it.
        """
        if retry_after is not None:
            try:
                capped = min(float(retry_after), RETRY_MAX_DELAY_S)
            except ValueError:
                pass
            else:
                await self._sleep(backoff.additive_jitter(capped))
                return
        await self._sleep(
            backoff.jittered_backoff_delay(
                attempt, base_s=RETRY_BASE_DELAY_S, cap_s=RETRY_MAX_DELAY_S
            )
        )

    async def aclose(self) -> None:
        """Close the underlying client only if this counter created it."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncClaudeTokenCounter:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
