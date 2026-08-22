"""CONTRACT — ``loremaster.auth`` KEPT surface (packet 39 RE-CUT, wave 1).

⚠ SCOPE (as of 2026-08-22, wave-1 close-out by contract-39-w1b). This module pins the
KEPT surface of ``loremaster/auth.py`` under the packet-39 re-cut (design
``docs/design/2026-08-21-packet39-recut-oauth.md`` §9): the ``ApiKeyVerifier`` rotation /
timing-safety semantics, ``build_api_key_verifier``, ``OriginValidationMiddleware``, the
still-exported KEPT names, and the cross-module ``_drive`` / ``_RecordingApp`` helpers
(imported by ``test_eager_startup`` / ``test_mcp_server``).

⚠ WHAT IS NOT HERE, AND WHY. The re-cut's REMOVALS — dropping ``BearerAuthMiddleware`` and
the ``AuthVerifier`` ABC (design §9: dropped-and-replaced by ``FastMCP(auth=…)``) and
retiring the ``tls_terminated_upstream`` config flag — land in WAVE 3 (the standalone-fastmcp
composition, design §2/§8). Per the DUAL law (removed-behaviour pins are written WHEN the
removal lands, not before), the absence pins for those symbols and the config-migration guard
were REMOVED from this wave-1 contract by contract-39-w1b and are RE-CUT at wave 3 — see the
wave-3 re-cut finding filed alongside this trim. Until then those symbols still exist in
``auth.py`` by design, so pinning their absence here would be a premature (perpetually RED)
forward pin — which is exactly what the currency gate flagged RED_ORPHANED.

The E1 trim (contract-39-w1) that preceded this close-out retired the 2026-07-31 SDK-FastMCP
pins: ``LoreTokenVerifier`` now lives in ``loremaster/token_verifier.py`` (pinned by
``test_token_verifier.py``); ``GoogleOAuthConfig`` / the flat-file roster are superseded by the
48/49 principal substrate (re-cut design §2/§9). The sibling modules named by the E1 trim
(``test_google_token_verifier`` / ``test_allowlist_roster`` / ``test_auth_composition`` /
``test_auth_identity_seam`` / ``test_hosted_readonly_posture`` /
``test_permission_resolver_seam``) are ARCHIVED at
``docs/plans/v2/receipts/2026-08-21-packet39-recut/``.

⚠ ``_drive`` AND ``_RecordingApp`` ARE PUBLIC-BY-USE. ``test_eager_startup.py`` and
``test_mcp_server.py`` import ``_drive`` from here. They are kept with their exact existing
shape — their signature and return shape are a cross-module contract, do not reshape them.
"""

from __future__ import annotations

import hmac
from collections.abc import MutableMapping
from typing import Any

import pytest
from _auth_fixtures import (
    API_KEY_ENV_LAN_CLIENT,
    API_KEY_ENV_LOCAL_AGENT,
    API_KEY_NAME_LAN_CLIENT,
    API_KEY_NAME_LOCAL_AGENT,
    API_KEY_VALUE_LAN_CLIENT,
    API_KEY_VALUE_LOCAL_AGENT,
)
from loremaster.config import AuthConfig, AuthKey
from pydantic import SecretStr

# The names design §9 keeps exported from ``loremaster.auth``. (The names it DELETES —
# ``BearerAuthMiddleware`` / ``AuthVerifier`` — and the retired ``tls_terminated_upstream``
# config flag are RE-CUT as absence pins at WAVE 3, when the removal actually lands; see the
# module docstring and the wave-3 re-cut finding.)
KEPT_AUTH_EXPORTS = (
    "ApiKeyVerifier",
    "OriginValidationMiddleware",
    "build_api_key_verifier",
)


class _RecordingApp:
    """A minimal ASGI app that records whether it was called (the protected resource)."""

    def __init__(self) -> None:
        self.called = False

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        self.called = True
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


async def _drive(app: Any, headers: list[tuple[bytes, bytes]]) -> dict[str, Any]:
    """Drive an ASGI app once over a synthetic HTTP scope; capture the response.

    KEPT VERBATIM: ``test_eager_startup.py`` and ``test_mcp_server.py`` import this
    helper. Its signature and return shape are a cross-module contract.
    """
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


class TestKeptAuthSurfaceIsExported:
    """Design §9 keeps ``ApiKeyVerifier`` / ``OriginValidationMiddleware`` /
    ``build_api_key_verifier`` exported from ``loremaster.auth`` — pin that they stay in
    ``__all__`` so a rewrite that empties or reshapes the module's public surface reddens
    here.

    (The absence pins for the DELETED hand-roll — ``BearerAuthMiddleware`` / ``AuthVerifier``
    — are RE-CUT at WAVE 3 when the deletion actually lands, not before; see the module
    docstring and the wave-3 re-cut finding. Until then those symbols still exist in
    ``auth.py`` by design.)
    """

    @pytest.mark.parametrize("name", KEPT_AUTH_EXPORTS)
    def test_the_kept_names_are_still_exported(self, name: str) -> None:
        # A build that emptied ``__all__`` entirely, or dropped one kept name in a rewrite,
        # reddens here. The kept surface must stay exported.
        import loremaster.auth as auth_module

        assert name in auth_module.__all__, f"{name} is KEPT by design §9 and must stay exported"

    # RETIRED (E1a, contract-39-w1): ``test_the_new_token_verifier_is_exported`` and
    # ``test_the_verifier_satisfies_the_sdk_token_verifier_protocol`` asserted
    # ``LoreTokenVerifier`` was exported from ``loremaster.auth`` (the 2026-07-31 SDK model).
    # The re-cut moved ``LoreTokenVerifier`` to ``loremaster/token_verifier.py``; its
    # fastmcp-TokenVerifier signature + behaviour are pinned by ``test_token_verifier.py``.


class TestApiKeyVerifierIsPreservedVerbatim:
    """Design §8 rows 3, 10 and 11 — kept, and pinned at the semantics that made it sound.

    None of these is justified by "the old code did it": each is the D9 rotation /
    timing-safety contract the threat model in design §1 still relies on for the
    api-key principals, who retain the FULL tool surface.
    """

    def _verifier(self) -> Any:
        from loremaster.auth import ApiKeyVerifier

        return ApiKeyVerifier(
            {
                API_KEY_NAME_LOCAL_AGENT: SecretStr(API_KEY_VALUE_LOCAL_AGENT),
                API_KEY_NAME_LAN_CLIENT: SecretStr(API_KEY_VALUE_LAN_CLIENT),
            }
        )

    def test_each_valid_key_returns_its_own_identity(self) -> None:
        # TWO distinct key names, deliberately: a build that returns a constant
        # identity passes a one-key fixture and collapses every principal into one.
        verifier = self._verifier()
        assert verifier.verify(API_KEY_VALUE_LOCAL_AGENT) == API_KEY_NAME_LOCAL_AGENT
        assert verifier.verify(API_KEY_VALUE_LAN_CLIENT) == API_KEY_NAME_LAN_CLIENT

    def test_unknown_key_returns_none(self) -> None:
        assert self._verifier().verify("lk_0000000000000000000000000000000") is None

    def test_empty_token_returns_none(self) -> None:
        assert self._verifier().verify("") is None

    def test_near_miss_key_returns_none(self) -> None:
        # No prefix / substring match: one character short and one character long.
        verifier = self._verifier()
        assert verifier.verify(API_KEY_VALUE_LOCAL_AGENT[:-1]) is None
        assert verifier.verify(API_KEY_VALUE_LOCAL_AGENT + "a") is None

    def test_uses_constant_time_comparison(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Timing-safety is load-bearing for a secret check. Spy on compare_digest and
        # assert the verifier routed through it — a dict lookup or ``==`` is leaky.
        from loremaster import auth

        calls: list[tuple[Any, Any]] = []
        real = hmac.compare_digest

        def _spy(a: Any, b: Any) -> bool:
            calls.append((a, b))
            return bool(real(a, b))

        monkeypatch.setattr(auth.hmac, "compare_digest", _spy)
        verifier = auth.ApiKeyVerifier({API_KEY_NAME_LOCAL_AGENT: SecretStr(API_KEY_VALUE_LOCAL_AGENT)})
        verifier.verify(API_KEY_VALUE_LOCAL_AGENT)
        assert calls, "the verifier must compare via hmac.compare_digest (timing-safe)"

    def test_all_keys_are_checked_with_no_early_out(self) -> None:
        # The timing must not depend on WHICH key matched: with two keys configured, a
        # match on the FIRST must still consult the second. An early ``return`` on the
        # first hit reintroduces the timing oracle the constant-time compare removed.
        from loremaster import auth

        verifier = auth.ApiKeyVerifier(
            {
                API_KEY_NAME_LOCAL_AGENT: SecretStr(API_KEY_VALUE_LOCAL_AGENT),
                API_KEY_NAME_LAN_CLIENT: SecretStr(API_KEY_VALUE_LAN_CLIENT),
            }
        )
        comparisons: list[Any] = []
        real = hmac.compare_digest

        with pytest.MonkeyPatch.context() as patch:

            def _spy(a: Any, b: Any) -> bool:
                comparisons.append(b)
                return bool(real(a, b))

            patch.setattr(auth.hmac, "compare_digest", _spy)
            assert verifier.verify(API_KEY_VALUE_LOCAL_AGENT) == API_KEY_NAME_LOCAL_AGENT
        assert len(comparisons) == 2, (
            f"a two-key verifier must perform 2 comparisons even when the first "
            f"matches; performed {len(comparisons)}"
        )

    def test_empty_configured_key_value_is_rejected_at_construction(self) -> None:
        from loremaster.auth import ApiKeyVerifier

        with pytest.raises(ValueError, match="(?i)empty"):
            ApiKeyVerifier({"ghost": SecretStr("")})

    def test_add_empty_key_value_is_rejected_and_leaves_the_set_intact(self) -> None:
        from loremaster.auth import ApiKeyVerifier

        verifier = ApiKeyVerifier({API_KEY_NAME_LOCAL_AGENT: SecretStr(API_KEY_VALUE_LOCAL_AGENT)})
        with pytest.raises(ValueError, match="(?i)empty"):
            verifier.add_key("ghost", SecretStr(""))
        assert verifier.verify(API_KEY_VALUE_LOCAL_AGENT) == API_KEY_NAME_LOCAL_AGENT

    def test_rotation_add_key_verifies_immediately(self) -> None:
        from loremaster.auth import ApiKeyVerifier

        verifier = ApiKeyVerifier({API_KEY_NAME_LOCAL_AGENT: SecretStr(API_KEY_VALUE_LOCAL_AGENT)})
        assert verifier.verify(API_KEY_VALUE_LAN_CLIENT) is None
        verifier.add_key(API_KEY_NAME_LAN_CLIENT, SecretStr(API_KEY_VALUE_LAN_CLIENT))
        assert verifier.verify(API_KEY_VALUE_LAN_CLIENT) == API_KEY_NAME_LAN_CLIENT

    def test_rotation_remove_key_revokes_only_that_identity(self) -> None:
        verifier = self._verifier()
        verifier.remove_key(API_KEY_NAME_LOCAL_AGENT)
        assert verifier.verify(API_KEY_VALUE_LOCAL_AGENT) is None
        assert verifier.verify(API_KEY_VALUE_LAN_CLIENT) == API_KEY_NAME_LAN_CLIENT

    def test_non_ascii_token_returns_none_not_typeerror(self) -> None:
        # Design §8 row 3. The header is decoded latin-1 upstream, so a non-ASCII str
        # token IS reachable, and ``hmac.compare_digest`` RAISES TypeError on one.
        # A str-mode compare turns the 401 contract into a 500.
        assert self._verifier().verify("ééé") is None

    def test_the_key_set_is_copied_at_construction(self) -> None:
        # A later mutation of the caller's dict must not change the live key set —
        # otherwise a config reload could silently widen the gate.
        from loremaster.auth import ApiKeyVerifier

        caller_owned = {API_KEY_NAME_LOCAL_AGENT: SecretStr(API_KEY_VALUE_LOCAL_AGENT)}
        verifier = ApiKeyVerifier(caller_owned)
        caller_owned[API_KEY_NAME_LAN_CLIENT] = SecretStr(API_KEY_VALUE_LAN_CLIENT)
        assert verifier.verify(API_KEY_VALUE_LAN_CLIENT) is None


class TestBuildApiKeyVerifierFromConfig:
    """Design §8 row 10 — a key whose env var is unset/empty fails LOUD at startup."""

    def test_reads_key_values_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from loremaster.auth import build_api_key_verifier

        monkeypatch.setenv(API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LOCAL_AGENT)
        monkeypatch.setenv(API_KEY_ENV_LAN_CLIENT, API_KEY_VALUE_LAN_CLIENT)
        config = AuthConfig(
            enabled=True,
            keys=[
                AuthKey(name=API_KEY_NAME_LOCAL_AGENT, key_env=API_KEY_ENV_LOCAL_AGENT),
                AuthKey(name=API_KEY_NAME_LAN_CLIENT, key_env=API_KEY_ENV_LAN_CLIENT),
            ],
        )
        verifier = build_api_key_verifier(config)
        assert verifier.verify(API_KEY_VALUE_LOCAL_AGENT) == API_KEY_NAME_LOCAL_AGENT
        assert verifier.verify(API_KEY_VALUE_LAN_CLIENT) == API_KEY_NAME_LAN_CLIENT

    def test_missing_env_for_a_configured_key_fails_loud(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from loremaster.auth import build_api_key_verifier

        monkeypatch.delenv("LORE_KEY_MISSING", raising=False)
        config = AuthConfig(
            enabled=True, keys=[AuthKey(name="ghost", key_env="LORE_KEY_MISSING")]
        )
        with pytest.raises(KeyError):
            build_api_key_verifier(config)

    def test_whitespace_only_env_value_fails_loud(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ``resolve_secret`` routes blankness through ``lorerunes.is_blank``, whose
        # whole reason to exist is that a single space has length 1. A key resolving
        # to " " would authenticate a " " token — an un-closable hole.
        from loremaster.auth import build_api_key_verifier

        monkeypatch.setenv("LORE_KEY_BLANK", "   ")
        config = AuthConfig(enabled=True, keys=[AuthKey(name="ghost", key_env="LORE_KEY_BLANK")])
        with pytest.raises(KeyError):
            build_api_key_verifier(config)


class TestOriginValidationMiddlewareIsPreserved:
    """Design §8 rows 4 and 13 — kept in ``auth.py``, and now the OUTERMOST layer.

    The middleware's own policy is unchanged; what changes is its POSITION (design §6:
    Origin-outermost rejects cross-origin BEFORE any credential is parsed, so a
    browser-borne attacker cannot force an outbound Google call). The position pin
    lives in ``test_auth_composition``; the policy pins live here.
    """

    async def test_absent_origin_is_allowed(self) -> None:
        from loremaster.auth import OriginValidationMiddleware

        inner = _RecordingApp()
        response = await _drive(OriginValidationMiddleware(inner), [])
        assert response["status"] == 200
        assert inner.called is True

    async def test_loopback_origins_are_allowed(self) -> None:
        from loremaster.auth import OriginValidationMiddleware

        inner = _RecordingApp()
        app = OriginValidationMiddleware(inner)
        for origin in (
            b"http://localhost",
            b"http://localhost:9202",
            b"http://127.0.0.1:9202",
            b"https://127.0.0.1",
            b"http://[::1]:9202",
        ):
            inner.called = False
            response = await _drive(app, [(b"origin", origin)])
            assert response["status"] == 200, f"loopback origin {origin!r} must pass"
            assert inner.called is True

    async def test_disallowed_origin_is_403_before_the_inner_app(self) -> None:
        from loremaster.auth import OriginValidationMiddleware

        inner = _RecordingApp()
        response = await _drive(
            OriginValidationMiddleware(inner), [(b"origin", b"http://evil.example.com")]
        )
        assert response["status"] == 403
        assert inner.called is False

    async def test_configured_extra_origin_is_allowed_and_others_are_not(self) -> None:
        from loremaster.auth import OriginValidationMiddleware

        inner = _RecordingApp()
        app = OriginValidationMiddleware(inner, allowed_origins=["https://claude.ai"])
        ok = await _drive(app, [(b"origin", b"https://claude.ai")])
        assert ok["status"] == 200
        inner.called = False
        bad = await _drive(app, [(b"origin", b"https://claude.ai.evil.example")])
        assert bad["status"] == 403
        assert inner.called is False

    async def test_spoofed_loopback_origins_are_disallowed(self) -> None:
        from loremaster.auth import OriginValidationMiddleware

        inner = _RecordingApp()
        app = OriginValidationMiddleware(inner)
        for origin in (
            b"http://localhost.evil.com",
            b"http://127.0.0.1.evil.com",
            b"http://localhost@evil.com",
            b"http://localhost:1234@evil.com",
            b"http://localhost.",
        ):
            inner.called = False
            response = await _drive(app, [(b"origin", origin)])
            assert response["status"] == 403, f"spoofed origin {origin!r} must be 403"
            assert inner.called is False

    async def test_malformed_bracketed_ipv6_origin_is_403_not_500(self) -> None:
        from loremaster.auth import OriginValidationMiddleware

        inner = _RecordingApp()
        app = OriginValidationMiddleware(inner)
        for origin in (b"http://[::1]@evil.com", b"http://[::1].evil.com"):
            inner.called = False
            response = await _drive(app, [(b"origin", origin)])
            assert response["status"] == 403, (
                f"malformed origin {origin!r} must fail closed to 403, not crash"
            )
            assert inner.called is False

    async def test_non_http_scope_passes_through_untouched(self) -> None:
        # Design §8 row 4: the ASGI lifespan is not an HTTP request. A middleware that
        # gated it would break process startup outright.
        from loremaster.auth import OriginValidationMiddleware

        seen: list[str] = []

        async def _lifespan_app(scope: Any, receive: Any, send: Any) -> None:
            seen.append(scope["type"])

        app = OriginValidationMiddleware(_lifespan_app)

        async def receive() -> MutableMapping[str, Any]:
            return {"type": "lifespan.startup"}

        async def send(message: MutableMapping[str, Any]) -> None:
            return None

        await app({"type": "lifespan"}, receive, send)
        assert seen == ["lifespan"]


# RETIRED (wave-1 close-out, contract-39-w1b): TestAuthConfigRetiresTlsTerminatedUpstream
# pinned the ``tls_terminated_upstream`` config flag as DELETED — a not-a-field / fails-to-load
# / message-names-field-and-fix trio plus a clean-config positive control. The re-cut assigns
# that retirement to WAVE 3 (the standalone-fastmcp config surface, design §9), so the flag is
# still a live ``AuthConfig`` field today and those pins were perpetually RED (RED_ORPHANED at
# the currency gate). Per the DUAL law they are RE-CUT at wave 3 when the removal lands — see
# the wave-3 re-cut finding filed by contract-39-w1b.

# RETIRED (E1a, contract-39-w1): TestGoogleOAuthConfigFailsClosed +
# TestLoreConfigCrossChecksTheResourcePath tested GoogleOAuthConfig / resource_server_url /
# the flat-file roster — the 2026-07-31 SDK-FastMCP + R12-roster model, superseded by the
# standalone-fastmcp resource-server design (LoreTokenVerifier in token_verifier.py + the
# 48/49 principal substrate; re-cut design §2/§9). The re-cut's config surface
# (OAuthProviderConfig / AuthConfig / base_url https-only) is wave-3's contract.
