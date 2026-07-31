"""CONTRACT — ``loremaster.auth`` after packet 39: the SDK owns the gate, we own identity.

Packet 39 (design ``docs/design/2026-07-31-packet39-google-oauth.md``) DELETES the
hand-rolled ``BearerAuthMiddleware`` and the ``AuthVerifier`` ABC and adopts the MCP
SDK's ``TokenVerifier`` protocol (design §4, packages-considered §14: **replace**).
This module is the rewrite of the pre-packet contract, and it carries three jobs:

1. **The PRESERVED behaviours**, each citing the design §8 inventory row that demands
   it — never "the old code did it".
2. **The RETIRED surface**, pinned as absent so a half-finished deletion cannot ship
   with the hand-roll still importable (and still wired) beside the SDK.
3. **The CONFIG boundary** — the new ``google`` block, the deleted
   ``tls_terminated_upstream`` flag and its migration message, and the fail-closed
   validation R5/R7/R12 demand.

The Google branch, the caches, the roster runtime, the assembled-app composition, the
identity seam and the hosted read-only posture live in their own modules
(``test_google_token_verifier``, ``test_allowlist_roster``, ``test_auth_composition``,
``test_auth_identity_seam``, ``test_hosted_readonly_posture``,
``test_permission_resolver_seam``) — this one stays the module about ``auth.py``'s own
surface.

⚠ ``_drive`` AND ``_RecordingApp`` ARE PUBLIC-BY-USE. ``test_eager_startup.py`` and
``test_mcp_server.py`` import ``_drive`` from here (four call sites at packet-39 time).
They are kept with their exact existing shape. Design §8's removed-behaviour inventory
lists ``test_auth.py`` as a CONSUMER of the deleted symbols but does not record that it
is also a PROVIDER to three sibling modules — noted in the contract report as an
inventory gap.
"""

from __future__ import annotations

import hmac
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

import pytest
from _auth_fixtures import (
    API_KEY_ENV_LAN_CLIENT,
    API_KEY_ENV_LOCAL_AGENT,
    API_KEY_NAME_LAN_CLIENT,
    API_KEY_NAME_LOCAL_AGENT,
    API_KEY_VALUE_LAN_CLIENT,
    API_KEY_VALUE_LOCAL_AGENT,
    GOOGLE_CLIENT_ID,
    OPERATOR_EMAIL,
    RESOURCE_SERVER_URL,
    base_config_payload,
    hosted_auth_block,
    slug,
    write_roster,
)
from loremaster.config import AuthConfig, AuthKey, LoreConfig
from pydantic import SecretStr, ValidationError

# The names design §4 keeps, and the names it deletes. Both lists are the CONTRACT;
# the deletion half is what stops a build shipping the hand-roll beside the SDK.
KEPT_AUTH_EXPORTS = (
    "ApiKeyVerifier",
    "OriginValidationMiddleware",
    "build_api_key_verifier",
)
RETIRED_AUTH_NAMES = (
    "BearerAuthMiddleware",
    "AuthVerifier",
)
RETIRED_AUTH_CONFIG_FIELD = "tls_terminated_upstream"


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


class TestRetiredAuthSurfaceIsGone:
    """The hand-roll is DELETED, not merely unused (design §8 rows 9 and 13).

    A build that adds ``LoreTokenVerifier`` while leaving ``BearerAuthMiddleware``
    importable passes every behavioural pin in this contract — and leaves a second,
    divergent gate one import away from being re-wired by the next engineer who finds
    it. That is the ONE-IMPLEMENTATION failure, pre-installed.
    """

    @pytest.mark.parametrize("name", RETIRED_AUTH_NAMES)
    def test_the_retired_name_is_not_importable_from_loremaster_auth(self, name: str) -> None:
        import loremaster.auth as auth_module

        assert not hasattr(auth_module, name), (
            f"{name} is deleted by packet 39 (design §8). It is still an attribute of "
            f"loremaster.auth — a second gate beside the SDK's."
        )

    @pytest.mark.parametrize("name", RETIRED_AUTH_NAMES)
    def test_the_retired_name_is_not_exported(self, name: str) -> None:
        import loremaster.auth as auth_module

        assert name not in auth_module.__all__

    @pytest.mark.parametrize("name", KEPT_AUTH_EXPORTS)
    def test_the_kept_names_are_still_exported(self, name: str) -> None:
        # The CONTROL for the pins above: a build that emptied ``__all__`` entirely
        # would satisfy every absence assertion. The kept surface must still be there.
        import loremaster.auth as auth_module

        assert name in auth_module.__all__, f"{name} is KEPT by design §8 and must stay exported"

    def test_the_new_token_verifier_is_exported(self) -> None:
        import loremaster.auth as auth_module

        assert "LoreTokenVerifier" in auth_module.__all__

    def test_the_verifier_satisfies_the_sdk_token_verifier_protocol(self) -> None:
        # The whole point of the replacement: our verifier must be the thing the SDK
        # accepts, not a look-alike. ``TokenVerifier`` is a runtime-uncheckable
        # Protocol, so the pin is on the ONE method the SDK calls, with the right
        # async-ness — a sync ``verify_token`` would be awaited and blow up only
        # inside the SDK's uncovered branch.
        import inspect

        from loremaster.auth import LoreTokenVerifier

        verify = LoreTokenVerifier.verify_token
        assert inspect.iscoroutinefunction(verify), (
            "the SDK awaits verify_token; the retired seam's sync verify(token) -> "
            "str|None is dropped (design §8 row 9)"
        )
        parameters = list(inspect.signature(verify).parameters)
        assert parameters[:2] == ["self", "token"]


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


class TestAuthConfigRetiresTlsTerminatedUpstream:
    """Design §8 row 12 — the dead flag is deleted, and the migration is DIAGNOSED.

    ``extra="forbid"`` alone produces "Extra inputs are not permitted", which tells an
    operator nothing about what to do. The row demands the failure MESSAGE name the
    field AND the fix, because an external ``lore.yaml`` still carrying the flag stops
    loading the moment this ships.
    """

    def test_the_retired_field_is_not_a_model_field(self) -> None:
        assert RETIRED_AUTH_CONFIG_FIELD not in AuthConfig.model_fields

    def test_a_config_still_carrying_the_retired_flag_fails_to_load(self) -> None:
        with pytest.raises(ValidationError):
            AuthConfig.model_validate({"enabled": True, RETIRED_AUTH_CONFIG_FIELD: True})

    def test_the_failure_names_the_retired_field_and_the_fix(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            AuthConfig.model_validate({"enabled": True, RETIRED_AUTH_CONFIG_FIELD: True})
        message = str(excinfo.value)
        assert RETIRED_AUTH_CONFIG_FIELD in message, (
            "the operator must be told WHICH key to delete; a bare 'extra inputs are "
            "not permitted' sends them reading the whole schema"
        )
        assert "remove" in message.lower() or "delete" in message.lower(), (
            f"the message must state the FIX (delete the key), not merely that the "
            f"config is invalid. Message was: {message}"
        )

    def test_a_config_without_the_retired_flag_loads(self) -> None:
        # POSITIVE CONTROL: the migration guard must not reject a clean config.
        assert AuthConfig.model_validate({"enabled": False}).enabled is False


class TestGoogleOAuthConfigFailsClosed:
    """R5 / R7 / R12 config leg — an unconstructible config is a hole that cannot open."""

    def _google_block(self, roster_path: Path, **overrides: Any) -> dict[str, Any]:
        block: dict[str, Any] = {
            "client_id": GOOGLE_CLIENT_ID,
            "resource_server_url": RESOURCE_SERVER_URL,
            "allowed_emails_file": str(roster_path),
        }
        block.update(overrides)
        return block

    def test_a_complete_google_block_validates(self, tmp_path: Path) -> None:
        # POSITIVE CONTROL for every refusal below.
        from loremaster.config import GoogleOAuthConfig

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        google = GoogleOAuthConfig.model_validate(self._google_block(roster))
        assert google.client_id == GOOGLE_CLIENT_ID
        assert google.allowed_emails_file == str(roster)

    @pytest.mark.parametrize("blank", ["", " ", "\t", "\n", "     "])
    def test_a_blank_client_id_is_unconstructible(self, tmp_path: Path, blank: str) -> None:
        # R5's rider. Every blank SHAPE, not just "": a single space has length 1, so
        # a ``min_length=1`` guard accepts it — which is exactly why ``lorerunes.
        # is_blank`` exists and why this is parametrised.
        from loremaster.config import GoogleOAuthConfig

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        with pytest.raises(ValidationError):
            GoogleOAuthConfig.model_validate(self._google_block(roster, client_id=blank))

    def test_a_missing_client_id_is_unconstructible(self, tmp_path: Path) -> None:
        # R5: required, no default. A defaulted client_id would make the ``aud`` check
        # compare against a placeholder — i.e. accept nothing, or worse, accept
        # whatever the placeholder happens to be.
        from loremaster.config import GoogleOAuthConfig

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        block = self._google_block(roster)
        del block["client_id"]
        with pytest.raises(ValidationError):
            GoogleOAuthConfig.model_validate(block)

    @pytest.mark.parametrize("blank", ["", " ", "\t"])
    def test_a_blank_roster_path_is_unconstructible(self, tmp_path: Path, blank: str) -> None:
        # R12: ``lore.yaml`` carries ONLY the path. A blank path would resolve to the
        # process cwd or to nothing — either way the roster silently never loads, and
        # a build that then "degrades gracefully" is the F4 fail-open.
        from loremaster.config import GoogleOAuthConfig

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        with pytest.raises(ValidationError):
            GoogleOAuthConfig.model_validate(
                self._google_block(roster, allowed_emails_file=blank)
            )

    @pytest.mark.parametrize(
        "url",
        [
            "http://lore.firehawktransam.org/mcp",
            "ftp://lore.firehawktransam.org/mcp",
            "lore.firehawktransam.org/mcp",
            "",
        ],
    )
    def test_a_non_https_resource_server_url_is_unconstructible(
        self, tmp_path: Path, url: str
    ) -> None:
        # Design §8 row 12: the retired ``tls_terminated_upstream`` flag's INTENT
        # becomes this validator. The resource identifier is published to every client
        # in the ``.well-known`` document and echoed in the 401 challenge; an ``http``
        # value would advertise a downgrade to the whole world.
        from loremaster.config import GoogleOAuthConfig

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        with pytest.raises(ValidationError):
            GoogleOAuthConfig.model_validate(
                self._google_block(roster, resource_server_url=url)
            )

    def test_the_google_block_forbids_unknown_keys(self, tmp_path: Path) -> None:
        # ``extra="forbid"`` on the wire, per the repo's standing config law: a typo
        # like ``allowed_email_file`` must fail loud rather than leave the real field
        # at a default nobody chose.
        from loremaster.config import GoogleOAuthConfig

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        with pytest.raises(ValidationError):
            GoogleOAuthConfig.model_validate(
                self._google_block(roster, allowed_email_file=str(roster))
            )


class TestLoreConfigCrossChecksTheResourcePath:
    """The resource URL's PATH must equal ``server.path`` (design §5).

    This is a producer↔consumer seam with a silent failure mode: the SDK derives the
    ``.well-known`` route from ``resource_server_url``'s path and the streamable route
    from ``server.path``. If they disagree, the published metadata advertises a
    resource identifier that does not exist — clients 404 on discovery and the
    connector never completes, with nothing in the logs saying why.
    """

    def _config_payload(self, tmp_path: Path, resource_server_url: str) -> dict[str, Any]:
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        block = hosted_auth_block(roster)
        block["google"]["resource_server_url"] = resource_server_url
        payload["auth"] = block
        return payload

    def test_matching_paths_validate(self, tmp_path: Path) -> None:
        # POSITIVE CONTROL — ``/mcp`` on both sides is the production shape.
        config = LoreConfig.model_validate(self._config_payload(tmp_path, RESOURCE_SERVER_URL))
        assert config.auth is not None

    def test_a_mismatched_path_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(
                self._config_payload(tmp_path, "https://lore.firehawktransam.org/rag")
            )

    def test_a_resource_url_with_no_path_is_refused(self, tmp_path: Path) -> None:
        # RFC 9728 §3.1's URL construction inserts the well-known segment between host
        # and resource path; an empty path silently produces a DIFFERENT route than
        # the one lore-caddy is configured to forward.
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(
                self._config_payload(tmp_path, "https://lore.firehawktransam.org")
            )
