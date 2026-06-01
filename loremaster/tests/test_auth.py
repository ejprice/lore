"""Contract tests for ``loremaster.auth`` — the pluggable Bearer-key auth layer.

Plan D9/D11/§A1.12: loremaster's auth is a PLUGGABLE request verifier. The
**API-key Bearer** backend ships now (it covers the near-term consumers — Claude
Code's static ``Authorization: Bearer`` header and the Messages-API MCP
connector's ``authorization_token``); an OAuth 2.1 + DCR backend is a documented
FUTURE plug-in behind the same seam. TLS is terminated upstream (D11), so the key
is the whole gate — there is no transport encryption here to lean on.

The contract these tests pin (a security boundary — exhaustive on the failure
modes):

The seam (``AuthVerifier``)
---------------------------
* An abstract :class:`AuthVerifier` with ``verify(token) -> str | None``: a valid
  token returns the IDENTITY (the named key's label, for audit); an invalid one
  returns ``None``. The async-friendly seam an OAuth/DCR backend can also satisfy.

The API-key backend (``ApiKeyVerifier``)
----------------------------------------
* **Valid key → its identity.** A configured key verifies and returns the NAME it
  was registered under (so a log line can attribute the request to a developer).
* **Unknown / empty / wrong key → ``None``.** A key not in the set, the empty
  string, or a near-miss never verifies.
* **Constant-time comparison.** The match uses :func:`hmac.compare_digest`, so a
  wrong key cannot be discovered by timing the rejection. (Asserted structurally
  — the verifier does not use a plain ``in`` / ``==`` on the secret.)
* **Rotation — add / remove with zero downtime.** Adding a new named key makes it
  verify immediately; removing one named key revokes JUST that identity and
  leaves the others verifying — the rotation contract (revoke one developer
  without disturbing the rest).
* **Two keys with the same VALUE are distinct identities by name** is out of
  scope (keys are unique secrets); a duplicate value resolves to one identity
  deterministically.

Building from config
--------------------
* ``build_api_key_verifier(auth_config)`` reads each key's VALUE from the env var
  it names (``key_env``) — never inlined — and registers it under the key's
  ``name``. A missing/empty env var for a configured key fails LOUD (a key that
  silently resolves to empty would create an un-closable hole).

The ASGI Bearer middleware
--------------------------
* A request with a valid ``Authorization: Bearer <key>`` passes through to the
  wrapped app (the MCP handler runs).
* A request with NO ``Authorization`` header, a non-Bearer scheme, or an unknown
  key is rejected with **HTTP 401** and a ``WWW-Authenticate: Bearer`` header —
  before the wrapped app is ever called.
* The middleware never logs the presented key value.

These run offline — the verifier is pure, and the middleware is exercised with a
minimal ASGI scope (a recording inner app), no network.
"""

from __future__ import annotations

import hmac
from collections.abc import MutableMapping
from typing import Any

import pytest
from loremaster.config import AuthConfig, AuthKey


class TestApiKeyVerifier:
    """The API-key Bearer backend validates a token against the named-key set."""

    def test_valid_key_returns_its_identity(self) -> None:
        from loremaster.auth import ApiKeyVerifier

        verifier = ApiKeyVerifier({"alice": "key-aaa", "bob": "key-bbb"})
        assert verifier.verify("key-aaa") == "alice"
        assert verifier.verify("key-bbb") == "bob"

    def test_unknown_key_returns_none(self) -> None:
        from loremaster.auth import ApiKeyVerifier

        verifier = ApiKeyVerifier({"alice": "key-aaa"})
        assert verifier.verify("key-zzz") is None

    def test_empty_token_returns_none(self) -> None:
        from loremaster.auth import ApiKeyVerifier

        verifier = ApiKeyVerifier({"alice": "key-aaa"})
        assert verifier.verify("") is None

    def test_near_miss_key_returns_none(self) -> None:
        # A one-character-off key must not verify (no prefix/substring match).
        from loremaster.auth import ApiKeyVerifier

        verifier = ApiKeyVerifier({"alice": "key-aaa"})
        assert verifier.verify("key-aa") is None
        assert verifier.verify("key-aaaa") is None

    def test_uses_constant_time_comparison(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Timing-safe compare is load-bearing for a secret check. Prove the
        # verifier routes its comparison through hmac.compare_digest (a plain
        # ``==`` / dict lookup on the secret would be timing-leaky). We spy on
        # compare_digest and assert it was consulted for the match.
        from loremaster import auth

        calls: list[tuple[str, str]] = []
        real = hmac.compare_digest

        def _spy(a: Any, b: Any) -> bool:
            calls.append((a, b))
            return real(a, b)

        monkeypatch.setattr(auth.hmac, "compare_digest", _spy)
        verifier = auth.ApiKeyVerifier({"alice": "key-aaa"})
        verifier.verify("key-aaa")
        assert calls, "the verifier must compare via hmac.compare_digest (timing-safe)"

    def test_empty_configured_key_value_is_rejected_at_construction(self) -> None:
        # Defense in depth: a key configured with an EMPTY value is an un-closable
        # hole (it would authenticate an empty token), so the verifier refuses to
        # even hold one — construction fails loud. build_api_key_verifier already
        # rejects empty env values; a directly-constructed verifier is safe too.
        from loremaster.auth import ApiKeyVerifier

        with pytest.raises(ValueError, match="(?i)empty"):
            ApiKeyVerifier({"ghost": ""})

    def test_empty_token_never_authenticates(self) -> None:
        # And an empty PRESENTED token is rejected up front, regardless of keys.
        from loremaster.auth import ApiKeyVerifier

        verifier = ApiKeyVerifier({"alice": "key-aaa"})
        assert verifier.verify("") is None

    def test_add_empty_key_value_is_rejected(self) -> None:
        from loremaster.auth import ApiKeyVerifier

        verifier = ApiKeyVerifier({"alice": "key-aaa"})
        with pytest.raises(ValueError, match="(?i)empty"):
            verifier.add_key("ghost", "")
        # alice still works; no empty hole was opened.
        assert verifier.verify("key-aaa") == "alice"

    def test_rotation_add_key_verifies_immediately(self) -> None:
        from loremaster.auth import ApiKeyVerifier

        verifier = ApiKeyVerifier({"alice": "key-aaa"})
        assert verifier.verify("key-ccc") is None
        verifier.add_key("carol", "key-ccc")
        assert verifier.verify("key-ccc") == "carol"

    def test_rotation_remove_key_revokes_only_that_identity(self) -> None:
        from loremaster.auth import ApiKeyVerifier

        verifier = ApiKeyVerifier({"alice": "key-aaa", "bob": "key-bbb"})
        verifier.remove_key("alice")
        # alice is revoked; bob is undisturbed (rotate one identity, not all).
        assert verifier.verify("key-aaa") is None
        assert verifier.verify("key-bbb") == "bob"


class TestBuildApiKeyVerifierFromConfig:
    """``build_api_key_verifier`` resolves each key's value from its env var."""

    def test_reads_key_values_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from loremaster.auth import build_api_key_verifier

        monkeypatch.setenv("LORE_KEY_ALICE", "secret-alice")
        monkeypatch.setenv("LORE_KEY_BOB", "secret-bob")
        config = AuthConfig(
            enabled=True,
            keys=[
                AuthKey(name="alice", key_env="LORE_KEY_ALICE"),
                AuthKey(name="bob", key_env="LORE_KEY_BOB"),
            ],
        )
        verifier = build_api_key_verifier(config)
        assert verifier.verify("secret-alice") == "alice"
        assert verifier.verify("secret-bob") == "bob"

    def test_missing_env_for_a_configured_key_fails_loud(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A configured key whose env var is unset must raise — never resolve to
        # an empty value that would be an un-closable hole.
        from loremaster.auth import build_api_key_verifier

        monkeypatch.delenv("LORE_KEY_MISSING", raising=False)
        config = AuthConfig(
            enabled=True, keys=[AuthKey(name="ghost", key_env="LORE_KEY_MISSING")]
        )
        with pytest.raises(KeyError):
            build_api_key_verifier(config)


class _RecordingApp:
    """A minimal ASGI app that records whether it was called (the protected resource)."""

    def __init__(self) -> None:
        self.called = False

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        self.called = True
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


async def _drive(app: Any, headers: list[tuple[bytes, bytes]]) -> dict[str, Any]:
    """Drive an ASGI app once over a synthetic HTTP scope; capture the response."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/mcp",
        "headers": headers,
    }
    sent: list[MutableMapping[str, Any]] = []

    async def receive() -> MutableMapping[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: MutableMapping[str, Any]) -> None:
        sent.append(message)

    await app(scope, receive, send)
    start = next(m for m in sent if m["type"] == "http.response.start")
    return {"status": start["status"], "headers": dict(start.get("headers", []))}


class TestBearerAuthMiddleware:
    """The ASGI middleware gates every request on a valid Bearer key (D9/D11)."""

    @pytest.mark.asyncio
    async def test_valid_bearer_passes_through(self) -> None:
        from loremaster.auth import ApiKeyVerifier, BearerAuthMiddleware

        inner = _RecordingApp()
        app = BearerAuthMiddleware(inner, ApiKeyVerifier({"alice": "key-aaa"}))
        response = await _drive(app, [(b"authorization", b"Bearer key-aaa")])
        assert response["status"] == 200
        assert inner.called is True

    @pytest.mark.asyncio
    async def test_missing_authorization_header_is_401(self) -> None:
        from loremaster.auth import ApiKeyVerifier, BearerAuthMiddleware

        inner = _RecordingApp()
        app = BearerAuthMiddleware(inner, ApiKeyVerifier({"alice": "key-aaa"}))
        response = await _drive(app, [])
        assert response["status"] == 401
        # The inner protected app must NEVER run for an unauthenticated request.
        assert inner.called is False
        # A 401 advertises the scheme (RFC 7235).
        assert b"bearer" in response["headers"].get(b"www-authenticate", b"").lower()

    @pytest.mark.asyncio
    async def test_unknown_key_is_401(self) -> None:
        from loremaster.auth import ApiKeyVerifier, BearerAuthMiddleware

        inner = _RecordingApp()
        app = BearerAuthMiddleware(inner, ApiKeyVerifier({"alice": "key-aaa"}))
        response = await _drive(app, [(b"authorization", b"Bearer key-wrong")])
        assert response["status"] == 401
        assert inner.called is False

    @pytest.mark.asyncio
    async def test_non_bearer_scheme_is_401(self) -> None:
        # A Basic-auth header (or any non-Bearer scheme) is rejected — the
        # middleware is Bearer-only.
        from loremaster.auth import ApiKeyVerifier, BearerAuthMiddleware

        inner = _RecordingApp()
        app = BearerAuthMiddleware(inner, ApiKeyVerifier({"alice": "key-aaa"}))
        response = await _drive(app, [(b"authorization", b"Basic key-aaa")])
        assert response["status"] == 401
        assert inner.called is False

    @pytest.mark.asyncio
    async def test_non_ascii_bearer_token_is_401_not_500(self) -> None:
        # Fix #2 (LOW): a non-ASCII presented token must yield a clean 401 (the
        # inner app never reached), NOT a 500. ``hmac.compare_digest`` RAISES
        # TypeError on a non-ASCII ``str``, so the verify must compare on bytes —
        # otherwise the exception propagates out of the middleware → uvicorn 500.
        from loremaster.auth import ApiKeyVerifier, BearerAuthMiddleware

        inner = _RecordingApp()
        app = BearerAuthMiddleware(inner, ApiKeyVerifier({"alice": "key-aaa"}))
        # ``ééé`` (U+00E9 ×3) encoded latin-1 in the header, as the middleware
        # decodes it: a non-ASCII str token reaches verify().
        non_ascii = "ééé".encode("latin-1")
        response = await _drive(app, [(b"authorization", b"Bearer " + non_ascii)])
        assert response["status"] == 401
        assert inner.called is False

    def test_verify_non_ascii_token_returns_none_not_raises(self) -> None:
        # The verifier itself must tolerate a non-ASCII token (compare on bytes):
        # a clean ``None``, never a TypeError from str-mode compare_digest.
        from loremaster.auth import ApiKeyVerifier

        verifier = ApiKeyVerifier({"alice": "key-aaa"})
        assert verifier.verify("ééé") is None

    @pytest.mark.asyncio
    async def test_non_http_scope_passes_through_untouched(self) -> None:
        # A lifespan scope (ASGI startup/shutdown) is not an HTTP request and must
        # pass straight through — the middleware only gates HTTP.
        from loremaster.auth import ApiKeyVerifier, BearerAuthMiddleware

        seen: list[str] = []

        async def _lifespan_app(scope: Any, receive: Any, send: Any) -> None:
            seen.append(scope["type"])

        app = BearerAuthMiddleware(_lifespan_app, ApiKeyVerifier({"alice": "key-aaa"}))

        async def receive() -> MutableMapping[str, Any]:
            return {"type": "lifespan.startup"}

        async def send(message: MutableMapping[str, Any]) -> None:
            pass

        await app({"type": "lifespan"}, receive, send)
        assert seen == ["lifespan"]


class TestOriginValidationMiddleware:
    """Origin allow-list (DNS-rebinding defense) for the local streamable-HTTP mode.

    The mcp-builder standard calls for Origin-header validation on local
    streamable-HTTP servers (a browser tricked by DNS rebinding into POSTing to
    127.0.0.1 carries an attacker Origin; a non-browser client like Claude Code
    carries none). The middleware ALLOWS a request with no Origin (legitimate local
    clients) or a loopback / configured Origin, and REJECTS any other Origin with
    403 — before the wrapped app runs — without breaking the no-auth localhost
    default.
    """

    @pytest.mark.asyncio
    async def test_absent_origin_is_allowed(self) -> None:
        # A non-browser local client (Claude Code, curl) sends no Origin — it must
        # pass through, so the no-auth localhost default is not broken.
        from loremaster.auth import OriginValidationMiddleware

        inner = _RecordingApp()
        app = OriginValidationMiddleware(inner)
        response = await _drive(app, [])
        assert response["status"] == 200
        assert inner.called is True

    @pytest.mark.asyncio
    async def test_loopback_origin_is_allowed(self) -> None:
        from loremaster.auth import OriginValidationMiddleware

        inner = _RecordingApp()
        app = OriginValidationMiddleware(inner)
        for origin in (
            b"http://localhost",
            b"http://localhost:9233",
            b"http://127.0.0.1:9233",
            b"https://127.0.0.1",
            b"http://[::1]:9233",
        ):
            inner.called = False
            response = await _drive(app, [(b"origin", origin)])
            assert response["status"] == 200, f"loopback origin {origin!r} must pass"
            assert inner.called is True

    @pytest.mark.asyncio
    async def test_disallowed_origin_is_403(self) -> None:
        # A cross-origin browser request (the DNS-rebinding attack vector) is
        # rejected with 403 and the inner app never runs.
        from loremaster.auth import OriginValidationMiddleware

        inner = _RecordingApp()
        app = OriginValidationMiddleware(inner)
        response = await _drive(app, [(b"origin", b"http://evil.example.com")])
        assert response["status"] == 403
        assert inner.called is False

    @pytest.mark.asyncio
    async def test_configured_extra_origin_is_allowed(self) -> None:
        # An explicitly-allowed extra origin (a trusted web UI host) passes, while
        # an un-listed one is still rejected.
        from loremaster.auth import OriginValidationMiddleware

        inner = _RecordingApp()
        app = OriginValidationMiddleware(inner, allowed_origins=["https://lore.internal"])
        ok = await _drive(app, [(b"origin", b"https://lore.internal")])
        assert ok["status"] == 200
        inner.called = False
        bad = await _drive(app, [(b"origin", b"https://other.internal")])
        assert bad["status"] == 403
        assert inner.called is False

    @pytest.mark.asyncio
    async def test_non_http_scope_passes_through_untouched(self) -> None:
        from loremaster.auth import OriginValidationMiddleware

        seen: list[str] = []

        async def _lifespan_app(scope: Any, receive: Any, send: Any) -> None:
            seen.append(scope["type"])

        app = OriginValidationMiddleware(_lifespan_app)

        async def receive() -> MutableMapping[str, Any]:
            return {"type": "lifespan.startup"}

        async def send(message: MutableMapping[str, Any]) -> None:
            pass

        await app({"type": "lifespan"}, receive, send)
        assert seen == ["lifespan"]
