"""CONTRACT — the ASSEMBLED app: discovery, the 401 challenge, and the edge policy.

Design ``docs/design/2026-07-31-packet39-google-oauth.md`` §6 + §9 group 5. Every pin
here drives the app ``build_asgi_app`` actually returns, because **the MCP SDK's whole
auth branch is ``# pragma: no cover`` upstream** — a verifier-level unit test proves
nothing about what the composed Starlette app serves. Verified at the installed SDK
(``mcp`` 1.27.2): ``FastMCP.streamable_http_app`` guards its auth wiring, its
``RequireAuthMiddleware`` wrap and its ``.well-known`` route registration behind three
separate ``# pragma: no cover`` blocks.

Pins here do NOT run the ASGI lifespan; they exercise the routes and middleware that
answer before the streamable session manager is reached (discovery, 401, Origin).
The pins that need a LIVE session manager — api-key admission through ``/mcp``, the
Host/Origin enforcement inside the transport, and the F3 session-ownership property —
live in ``test_auth_identity_seam``, which runs the real lifespan.

------------------------------------------------------------------------------
THE WRONG BUILDS THESE PINS DISCRIMINATE AGAINST

* **F2 — a Bearer-gated discovery document.** The retired ``BearerAuthMiddleware``
  gated the WHOLE app, so ``/.well-known/oauth-protected-resource/mcp`` would 401.
  RFC 9728 §3.1 requires it to be anonymous; a 401 there means claude.ai's connector
  can never begin the flow. Design §8 row 7 adjudicates this a DELIBERATE DROP.
* **Discovery served in the wrong posture.** ``LAN_BEARER`` sets
  ``resource_server_url=None`` so the route is ABSENT — advertising an OAuth flow that
  does not exist is a discovery fiction a connecting agent will act on.
* **Origin no longer outermost.** Today Bearer is outermost. Design §6 inverts it so a
  cross-origin request is refused BEFORE any credential is parsed — a browser-borne
  attacker must not be able to make lore dial Google. The zero-outbound-call assertion
  is what makes that property real rather than an ordering claim.
* **A loopback-only ``TransportSecuritySettings``.** ⚠ MEASURED AT THE SDK: FastMCP
  AUTO-ENABLES DNS-rebinding protection whenever ``host`` is loopback, with
  ``allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"]``. lore binds ``127.0.0.1``
  in EVERY posture, so a build that leaves ``transport_security`` unset inherits that
  default — and every hosted request, which arrives through lore-caddy carrying
  ``Host: lore.firehawktransam.org``, is answered **421**. That build passes every
  loopback test in this suite and is 100% broken in production. The ``EdgePolicy``
  pins below are the instrument for it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from _auth_fixtures import (
    API_KEY_ENV_LAN_CLIENT,
    API_KEY_ENV_LOCAL_AGENT,
    API_KEY_VALUE_LAN_CLIENT,
    API_KEY_VALUE_LOCAL_AGENT,
    CLAUDE_AI_ORIGIN,
    CLAUDE_COM_ORIGIN,
    HOSTILE_ORIGIN,
    LOOPBACK_HOST,
    MCP_PATH,
    OPERATOR_EMAIL,
    PUBLIC_HOSTNAME,
    SERVER_PORT,
    WELL_KNOWN_PATH,
    TokeninfoSpy,
    base_config_payload,
    bearer,
    drive,
    google_access_token,
    hosted_auth_block,
    lan_bearer_auth_block,
    slug,
    write_roster,
)

# RFC 9728 §3.1's URL construction, derived independently of the SDK's helper:
# ``https://{netloc}/.well-known/oauth-protected-resource{resource path}``.
EXPECTED_METADATA_URL = f"https://{PUBLIC_HOSTNAME}{WELL_KNOWN_PATH}"

# The Host header a hosted request actually carries. lore-caddy reverse-proxies to
# 127.0.0.1:9202 while FORWARDING the original Host — so this, not the loopback bind,
# is what the SDK's transport-security layer sees in production.
HOSTED_HOST_HEADER = PUBLIC_HOSTNAME.encode("ascii")
LOOPBACK_HOST_HEADER = f"{LOOPBACK_HOST}:{SERVER_PORT}".encode("ascii")


@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Export the api-key env vars every posture fixture's ``keys`` block references."""
    monkeypatch.setenv(API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LOCAL_AGENT)
    monkeypatch.setenv(API_KEY_ENV_LAN_CLIENT, API_KEY_VALUE_LAN_CLIENT)


def _config(tmp_path: Path, auth_block: dict[str, Any] | None) -> Any:
    from loremaster.config import LoreConfig

    payload = base_config_payload(slug(), tmp_path / "live")
    if auth_block is not None:
        payload["auth"] = auth_block
    return LoreConfig.model_validate(payload)


def hosted_config(tmp_path: Path) -> Any:
    """A validated ``HOSTED_OAUTH`` config over a real one-principal roster."""
    roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
    return _config(tmp_path, hosted_auth_block(roster))


def lan_bearer_config(tmp_path: Path) -> Any:
    """A validated ``LAN_BEARER`` config (today's networked multi-dev deployment)."""
    return _config(tmp_path, lan_bearer_auth_block())


def loopback_config(tmp_path: Path) -> Any:
    """A validated ``LOOPBACK`` config — today's default, no auth block at all."""
    return _config(tmp_path, None)


def build_app(config: Any, *, http_client: Any = None) -> Any:
    """Build the production-composed ASGI app for ``config``.

    Args:
        config: The validated :class:`LoreConfig`.
        http_client: An optional injected ``httpx.AsyncClient`` for the verifier, so a
            pin can assert an outbound Google call did NOT happen.
    """
    from loremaster.server import LoreServer, build_asgi_app, build_mcp_server

    server = LoreServer(config)
    mcp = build_mcp_server(server, http_client=http_client)
    return build_asgi_app(mcp, config)


class TestDiscoveryDocumentIsAnonymousInHostedPosture:
    """RFC 9728 §3.1 (design §8 row 7, dropped-deliberately with pins)."""

    async def test_the_well_known_document_is_served_without_any_credential(
        self, tmp_path: Path
    ) -> None:
        # THE F2 PIN. Under the retired whole-app Bearer gate this is a 401 and the
        # claude.ai connector can never start the flow.
        response = await drive(
            build_app(hosted_config(tmp_path)), method="GET", path=WELL_KNOWN_PATH
        )
        assert response.status == 200, (
            f"the protected-resource metadata must be world-readable (RFC 9728 §3.1); "
            f"got {response.status}"
        )

    async def test_the_well_known_document_is_served_with_a_claude_ai_origin(
        self, tmp_path: Path
    ) -> None:
        # claude.ai's connector may or may not send Origin (design R6, M-1 unmeasured).
        # BOTH shapes must work, so both are pinned — a build that allows only the
        # absent-Origin shape breaks discovery for the one client that matters.
        response = await drive(
            build_app(hosted_config(tmp_path)),
            method="GET",
            path=WELL_KNOWN_PATH,
            headers=[(b"origin", CLAUDE_AI_ORIGIN.encode("ascii"))],
        )
        assert response.status == 200

    async def test_the_well_known_document_names_the_resource_and_the_issuer(
        self, tmp_path: Path
    ) -> None:
        # A 200 with an empty or wrong body is a discovery fiction. The expected values
        # come from the CONFIG the fixture declared and the issuer design §4 hardcodes.
        import json

        from _auth_fixtures import GOOGLE_ISSUER, RESOURCE_SERVER_URL

        response = await drive(
            build_app(hosted_config(tmp_path)), method="GET", path=WELL_KNOWN_PATH
        )
        document = json.loads(response.body)
        assert document["resource"].rstrip("/") == RESOURCE_SERVER_URL.rstrip("/")
        assert any(
            str(server).rstrip("/") == GOOGLE_ISSUER
            for server in document["authorization_servers"]
        ), f"the metadata must name Google as the authorization server; got {document}"

    async def test_the_well_known_document_is_absent_in_lan_bearer_posture(
        self, tmp_path: Path
    ) -> None:
        # Design §5: ``LAN_BEARER`` sets ``resource_server_url=None`` precisely so the
        # route is NOT registered. Serving discovery for an OAuth flow that does not
        # exist teaches a connecting agent a lie it will act on.
        response = await drive(
            build_app(lan_bearer_config(tmp_path)), method="GET", path=WELL_KNOWN_PATH
        )
        assert response.status == 404

    async def test_the_well_known_document_is_absent_in_loopback_posture(
        self, tmp_path: Path
    ) -> None:
        response = await drive(
            build_app(loopback_config(tmp_path)), method="GET", path=WELL_KNOWN_PATH
        )
        assert response.status == 404


class TestUnauthenticatedRequestsAreChallenged:
    """Design §8 rows 1, 6 and 8 — 401 before the wrapped app, with a usable challenge."""

    @pytest.mark.parametrize("posture", ["hosted", "lan_bearer"])
    async def test_an_unauthenticated_mcp_request_is_401(
        self, tmp_path: Path, posture: str
    ) -> None:
        config = hosted_config(tmp_path) if posture == "hosted" else lan_bearer_config(tmp_path)
        response = await drive(build_app(config), method="POST", path=MCP_PATH)
        assert response.status == 401

    async def test_the_401_advertises_the_bearer_scheme(self, tmp_path: Path) -> None:
        # Design §8 row 1: the SHAPE is superseded by the SDK's, but the property —
        # a challenge naming the scheme (RFC 7235) — is preserved.
        response = await drive(
            build_app(hosted_config(tmp_path)), method="POST", path=MCP_PATH
        )
        assert "bearer" in response.header("www-authenticate").lower()

    async def test_the_401_carries_a_resource_metadata_url_that_resolves(
        self, tmp_path: Path
    ) -> None:
        # RFC 9728 §5.1, and the branch the SDK marks ``# pragma: no cover``: without
        # ``resource_metadata=`` in the challenge, a compliant client has no way to
        # discover WHERE to authenticate, and the connector dead-ends at the 401.
        app = build_app(hosted_config(tmp_path))
        response = await drive(app, method="POST", path=MCP_PATH)
        challenge = response.header("www-authenticate")
        assert "resource_metadata=" in challenge, (
            f"the 401 challenge must carry resource_metadata= (RFC 9728 §5.1); got "
            f"{challenge!r}"
        )
        assert EXPECTED_METADATA_URL in challenge, (
            f"the advertised metadata URL must be {EXPECTED_METADATA_URL!r} — derived "
            f"from RFC 9728 §3.1's construction over the configured resource URL; got "
            f"{challenge!r}"
        )

        # And the URL it advertises must actually be served by this same app: a
        # challenge pointing at a 404 is worse than no challenge.
        followed = await drive(app, method="GET", path=WELL_KNOWN_PATH)
        assert followed.status == 200

    async def test_an_unknown_bearer_token_is_401_and_never_reaches_a_session(
        self, tmp_path: Path
    ) -> None:
        # Fail closed BEFORE the wrapped app (design §8 row 6). If this reached the
        # streamable app it would raise (no lifespan has run), so a 401 is also proof
        # the request stopped at the gate.
        spy = TokeninfoSpy(responder=lambda _request: _unauthorised())
        app = build_app(hosted_config(tmp_path), http_client=spy.client())
        response = await drive(
            app,
            method="POST",
            path=MCP_PATH,
            headers=[bearer(google_access_token("unknown"))],
        )
        assert response.status == 401

    @pytest.mark.parametrize("scheme", ["Bearer", "bearer", "BEARER", "BeArEr"])
    async def test_the_bearer_scheme_is_matched_case_insensitively(
        self, tmp_path: Path, scheme: str
    ) -> None:
        # Design §8 row 2 — RFC 7235 §2.1 makes the scheme case-insensitive, and the
        # retired middleware honoured that. The pin is on the ASSEMBLED app because the
        # SDK now owns the parse; if the SDK were case-SENSITIVE that is a FINDING to
        # surface, not a silent regression. All four casings must reach the verifier,
        # which is observable as an outbound tokeninfo attempt.
        spy = TokeninfoSpy(responder=lambda _request: _unauthorised())
        app = build_app(hosted_config(tmp_path), http_client=spy.client())
        response = await drive(
            app,
            method="POST",
            path=MCP_PATH,
            headers=[bearer(google_access_token("casing"), scheme=scheme)],
        )
        assert response.status == 401
        assert spy.call_count == 1, (
            f"the {scheme!r} scheme did not reach the token verifier ("
            f"{spy.call_count} outbound attempts) — RFC 7235 §2.1 makes the scheme "
            f"case-insensitive and the retired middleware honoured it"
        )

    async def test_a_non_bearer_scheme_is_401_without_an_outbound_call(
        self, tmp_path: Path
    ) -> None:
        # The CONTROL for the casing pin: ``Basic`` must NOT reach the verifier, so the
        # call-count assertion above is measuring scheme matching rather than "any
        # header reaches Google".
        spy = TokeninfoSpy(responder=lambda _request: _unauthorised())
        app = build_app(hosted_config(tmp_path), http_client=spy.client())
        response = await drive(
            app,
            method="POST",
            path=MCP_PATH,
            headers=[(b"authorization", b"Basic ZWpwcmljZTpodW50ZXIy")],
        )
        assert response.status == 401
        assert spy.call_count == 0

    async def test_a_non_ascii_token_is_a_clean_401_not_a_500(
        self, tmp_path: Path
    ) -> None:
        # Design §8 row 3. The header is decoded latin-1, so a non-ASCII token is
        # reachable; a str-mode ``compare_digest`` raises TypeError and the client gets
        # a 500 instead of the 401 contract.
        spy = TokeninfoSpy(responder=lambda _request: _unauthorised())
        app = build_app(hosted_config(tmp_path), http_client=spy.client())
        response = await drive(
            app,
            method="POST",
            path=MCP_PATH,
            headers=[(b"authorization", "Bearer ééé".encode("latin-1"))],
        )
        assert response.status == 401


def _unauthorised() -> Any:
    """A 401 tokeninfo reply (the only outcome the composition pins need)."""
    import httpx

    return httpx.Response(401)


class TestUnknownPathsAre404NotChallenged:
    """S1 — an ACCEPTED KNOWN BOUND (operator ruling, 2026-07-31), pinned so it stays deliberate.

    The retired ``BearerAuthMiddleware`` gated EVERY HTTP path, so an unauthenticated
    ``POST /anything`` was ``401``. The SDK wraps only the streamable route, so an
    unknown path is now ``404`` — which means an anonymous caller can enumerate which
    paths exist. Design §8 row 7 adjudicates the DISCOVERY path deliberately; it did not
    adjudicate the rest of the surface, so this was surfaced as spec-silent and the
    operator ACCEPTED it: the disclosure is a route list, not data, the two-route surface
    is already public in the design, and re-gating everything would break RFC 9728
    discovery all over again. Recorded as design §8 **row 15**, ``dropped-deliberately``
    (verified against the doc on disk — the ruling message said "row 14", but row 14 is the
    retired-``__all__`` row; citing it would have pointed a future reader at the wrong
    adjudication).

    The pin exists so a future engineer meets the bound DELIBERATELY. If a later change
    re-gates unknown paths (or narrows the surface), this reds and the change is a
    decision rather than an accident.
    """

    @pytest.mark.parametrize(
        "path",
        ["/", "/admin", "/metrics", "/.well-known/openid-configuration", "/mcp/internal"],
    )
    async def test_an_unknown_path_is_404_for_an_anonymous_caller(
        self, tmp_path: Path, path: str
    ) -> None:
        response = await drive(
            build_app(hosted_config(tmp_path)), method="GET", path=path
        )
        assert response.status == 404, (
            f"{path} answered {response.status}. If unknown paths are now CHALLENGED "
            f"again, that is a deliberate re-gating — update this pin and design §8 "
            f"row 15 together."
        )

    async def test_the_protected_route_is_still_challenged(self, tmp_path: Path) -> None:
        # THE CONTROL, and it is what stops the bound from widening: the 404 shape must
        # apply to paths that do not exist, never to the one that does. A build that
        # 404'd ``/mcp`` for an anonymous caller would pass every pin above while
        # silently un-gating nothing and confusing every client.
        response = await drive(
            build_app(hosted_config(tmp_path)), method="POST", path=MCP_PATH
        )
        assert response.status == 401


class TestOriginIsOutermost:
    """Design §6 + §8 row 13 — the REWRITTEN pin (never silently deleted)."""

    async def test_the_composed_app_is_not_wrapped_in_the_retired_bearer_middleware(
        self, tmp_path: Path
    ) -> None:
        # The old pin asserted ``isinstance(app, BearerAuthMiddleware)``. The name is
        # gone; the property that replaces it is that the OUTERMOST layer is the Origin
        # guard, in EVERY posture — so the ordering cannot silently invert back.
        from loremaster.auth import OriginValidationMiddleware

        for config in (
            hosted_config(tmp_path),
            lan_bearer_config(tmp_path),
            loopback_config(tmp_path),
        ):
            app = build_app(config)
            assert isinstance(app, OriginValidationMiddleware), (
                f"the composed app's OUTERMOST layer must be the Origin guard so a "
                f"cross-origin request is refused before any credential is parsed; "
                f"got {type(app).__name__}"
            )

    async def test_a_hostile_origin_is_403_with_ZERO_outbound_google_calls(
        self, tmp_path: Path
    ) -> None:
        # THE ARGUED IMPROVEMENT, made measurable. With Bearer outermost, a
        # browser-borne attacker's request would be token-parsed FIRST — so a hostile
        # page could make lore dial Google once per request, from lore's own IP, with
        # an attacker-chosen token. Origin-outermost makes that impossible, and the
        # spy's call count is the proof rather than the layer ordering.
        spy = TokeninfoSpy(responder=lambda _request: _unauthorised())
        app = build_app(hosted_config(tmp_path), http_client=spy.client())
        response = await drive(
            app,
            method="POST",
            path=MCP_PATH,
            headers=[
                (b"origin", HOSTILE_ORIGIN.encode("ascii")),
                bearer(google_access_token("attacker")),
            ],
        )
        assert response.status == 403
        assert spy.call_count == 0, (
            f"a disallowed Origin made {spy.call_count} outbound Google call(s). "
            f"Origin must be refused BEFORE any credential is parsed, or a hostile "
            f"page can drive traffic to Google from lore's IP with a token it chose."
        )

    @pytest.mark.parametrize("origin", [CLAUDE_AI_ORIGIN, CLAUDE_COM_ORIGIN])
    async def test_the_hosted_default_origins_are_allowed(
        self, tmp_path: Path, origin: str
    ) -> None:
        # Design R6: in ``HOSTED_OAUTH`` the effective allow-set gains
        # ``https://claude.ai`` and ``https://claude.com`` from a module CONSTANT — not
        # from anyone's yaml. Both are pinned because M-1 (does claude.ai send Origin,
        # and which value) is UNMEASURED; the design is correct under both outcomes and
        # so is this pin.
        spy = TokeninfoSpy(responder=lambda _request: _unauthorised())
        app = build_app(hosted_config(tmp_path), http_client=spy.client())
        response = await drive(
            app,
            method="POST",
            path=MCP_PATH,
            headers=[
                (b"origin", origin.encode("ascii")),
                bearer(google_access_token("claude")),
            ],
        )
        assert response.status == 401, (
            f"{origin} must pass the Origin guard and be judged on its CREDENTIAL "
            f"(401), not refused at the edge (403)"
        )
        assert spy.call_count == 1

    async def test_the_hosted_default_origins_are_NOT_allowed_in_lan_bearer_posture(
        self, tmp_path: Path
    ) -> None:
        # The union is applied in the POSTURE derivation, not baked into the middleware
        # for everyone. A LAN deployment has no business trusting claude.ai's origin.
        app = build_app(lan_bearer_config(tmp_path))
        response = await drive(
            app,
            method="POST",
            path=MCP_PATH,
            headers=[(b"origin", CLAUDE_AI_ORIGIN.encode("ascii"))],
        )
        assert response.status == 403

    async def test_an_absent_origin_is_allowed_in_hosted_posture(
        self, tmp_path: Path
    ) -> None:
        # Design R6: absent-Origin stays ALLOWED — a server-side proxy (which is what
        # claude.ai most plausibly is) sends none, and so does every non-browser client.
        spy = TokeninfoSpy(responder=lambda _request: _unauthorised())
        app = build_app(hosted_config(tmp_path), http_client=spy.client())
        response = await drive(
            app,
            method="POST",
            path=MCP_PATH,
            headers=[bearer(google_access_token("no-origin"))],
        )
        assert response.status == 401
        assert spy.call_count == 1

    async def test_the_discovery_route_is_also_origin_guarded(
        self, tmp_path: Path
    ) -> None:
        # Origin is outermost, so it covers discovery too. A hostile origin must not be
        # able to read the metadata document from a victim's browser session — and,
        # more importantly, the guard must not have been narrowed to ``/mcp`` only.
        response = await drive(
            build_app(hosted_config(tmp_path)),
            method="GET",
            path=WELL_KNOWN_PATH,
            headers=[(b"origin", HOSTILE_ORIGIN.encode("ascii"))],
        )
        assert response.status == 403


class TestEdgePolicyIsOneDerivationFeedingBothLayers:
    """R9 — two enforcement points, ONE derivation, so they cannot disagree by memory."""

    def test_the_composed_server_uses_the_derived_transport_security_settings(
        self, tmp_path: Path
    ) -> None:
        # The equality pin design R9's rider names. A build that computes an EdgePolicy
        # for the Origin middleware and leaves ``transport_security`` at FastMCP's
        # loopback auto-default passes every Origin pin above and 421s every hosted
        # request in production.
        from loremaster.auth import derive_edge_policy
        from loremaster.config import resolve_posture
        from loremaster.server import LoreServer, build_mcp_server

        config = hosted_config(tmp_path)
        mcp = build_mcp_server(LoreServer(config))
        policy = derive_edge_policy(config, resolve_posture(config))
        assert mcp.settings.transport_security == policy.to_transport_security(), (
            "the composed FastMCP's transport_security must BE the EdgePolicy's "
            "output — two independently-written settings objects are two policies "
            "that must agree by memory"
        )

    def test_the_hosted_edge_policy_allows_the_public_hostname(
        self, tmp_path: Path
    ) -> None:
        # ⚠ THE PRODUCTION-BREAKING DEFAULT. lore binds 127.0.0.1 in every posture, so
        # FastMCP auto-enables DNS-rebinding protection with loopback-only
        # ``allowed_hosts``. Hosted requests arrive through lore-caddy carrying
        # ``Host: lore.firehawktransam.org`` and are answered 421. The derived policy
        # must include the resource URL's netloc.
        from loremaster.auth import derive_edge_policy
        from loremaster.config import resolve_posture

        config = hosted_config(tmp_path)
        policy = derive_edge_policy(config, resolve_posture(config))
        # ⚠ BOTH FORMS ARE REQUIRED, and the reason is a measured SDK fact neither the
        # contract's nor the adversary's first survey carried. ``_validate_host`` tries
        # an EXACT match, then wildcards via ``host.startswith(base + ":")`` — so an
        # entry of ``"h:*"`` matches ONLY a Host that carries a colon. A reverse proxy
        # forwarding port 443 sends a PORT-LESS ``Host: lore.firehawktransam.org``,
        # which a `:*`-only policy answers 421. A bare-only policy conversely 421s any
        # explicit-port request. Emit both or one shape of real traffic breaks.
        assert PUBLIC_HOSTNAME in policy.allowed_hosts, (
            f"the hosted edge policy must allow the BARE public hostname "
            f"{PUBLIC_HOSTNAME!r} — the SDK's wildcard form requires a colon in the "
            f"presented Host, so a port-less Host (what a proxy forwards for :443) is "
            f"421ed by a `:*`-only policy. allowed_hosts was {sorted(policy.allowed_hosts)}"
        )
        assert f"{PUBLIC_HOSTNAME}:*" in policy.allowed_hosts, (
            f"the hosted edge policy must ALSO allow the explicit-port form "
            f"{PUBLIC_HOSTNAME}:* ; allowed_hosts was {sorted(policy.allowed_hosts)}"
        )

    def test_the_hosted_edge_policy_still_allows_the_loopback_bind(
        self, tmp_path: Path
    ) -> None:
        # The CONTROL: widening for the public hostname must not drop loopback, or a
        # local agent hitting 127.0.0.1:9202 with an api key gets a 421.
        from loremaster.auth import derive_edge_policy
        from loremaster.config import resolve_posture

        config = hosted_config(tmp_path)
        policy = derive_edge_policy(config, resolve_posture(config))
        assert any(host.split(":")[0] == LOOPBACK_HOST for host in policy.allowed_hosts), (
            f"loopback must stay allowed; allowed_hosts was {sorted(policy.allowed_hosts)}"
        )

    def test_the_hosted_edge_policy_carries_the_claude_origins(
        self, tmp_path: Path
    ) -> None:
        # The same ONE derivation feeds the SDK's Origin check, which runs INSIDE the
        # transport. A build that adds the claude origins only to the outer middleware
        # passes every pin in ``TestOriginIsOutermost`` and 403s at the inner layer the
        # moment a real session is created.
        from loremaster.auth import derive_edge_policy
        from loremaster.config import resolve_posture

        config = hosted_config(tmp_path)
        policy = derive_edge_policy(config, resolve_posture(config))
        assert CLAUDE_AI_ORIGIN in policy.allowed_origins
        assert CLAUDE_COM_ORIGIN in policy.allowed_origins

    def test_the_lan_bearer_edge_policy_does_not_carry_the_claude_origins(
        self, tmp_path: Path
    ) -> None:
        from loremaster.auth import derive_edge_policy
        from loremaster.config import resolve_posture

        config = lan_bearer_config(tmp_path)
        policy = derive_edge_policy(config, resolve_posture(config))
        assert CLAUDE_AI_ORIGIN not in policy.allowed_origins
        assert CLAUDE_COM_ORIGIN not in policy.allowed_origins

    def test_dns_rebinding_protection_is_enabled_in_every_non_loopback_posture(
        self, tmp_path: Path
    ) -> None:
        # Design R9: leaving ``transport_security`` unset repeats #206's shape inside
        # the packet that cites it. Host validation is the half lore's hand-rolled
        # middleware never covered.
        from loremaster.auth import derive_edge_policy
        from loremaster.config import resolve_posture

        for config in (hosted_config(tmp_path), lan_bearer_config(tmp_path)):
            settings = derive_edge_policy(config, resolve_posture(config)).to_transport_security()
            assert settings.enable_dns_rebinding_protection is True
            assert settings.allowed_hosts, "an empty allowed_hosts denies every request"

    def test_a_lan_bearer_deployment_on_a_real_lan_address_is_not_421ed(
        self, tmp_path: Path
    ) -> None:
        # M4 / WB28. ⚑ A PARAMETER-VALUE MONOCULTURE IN THIS CONTRACT'S OWN FIXTURES:
        # every EdgePolicy pin above binds 127.0.0.1, so a policy that hardcodes the
        # loopback forms and ignores ``config.server.host`` passes all of them. Design §5
        # rules LAN_BEARER legal on a NON-loopback bind — ``lorerunes``'
        # ``test_todays_enabled_api_key_config_is_lan_bearer`` asserts exactly that — and
        # with rebinding protection ON, every LAN request carries
        # ``Host: 192.168.64.100:9202`` and is answered 421. That is the W7 trap, one
        # posture over, on the deployment shape that exists TODAY.
        from loremaster.auth import derive_edge_policy
        from loremaster.config import LoreConfig, resolve_posture

        lan_host = "192.168.64.100"
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = lan_host
        payload["auth"] = lan_bearer_auth_block()
        config = LoreConfig.model_validate(payload)
        policy = derive_edge_policy(config, resolve_posture(config))
        assert any(entry.split(":")[0] == lan_host for entry in policy.allowed_hosts), (
            f"the derived edge policy must allow the CONFIGURED bind host {lan_host!r}; "
            f"allowed_hosts was {sorted(policy.allowed_hosts)}"
        )

    @pytest.mark.parametrize("lan_host", ["192.168.64.100", "10.0.0.7", "0.0.0.0"])
    def test_the_configured_bind_host_is_allowed_whatever_it_is(
        self, tmp_path: Path, lan_host: str
    ) -> None:
        # The same property over THREE distinct values, because one value is how a
        # monoculture starts. A build that special-cased the one address in the pin above
        # would pass it and fail here.
        from loremaster.auth import derive_edge_policy
        from loremaster.config import LoreConfig, resolve_posture

        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = lan_host
        payload["auth"] = lan_bearer_auth_block()
        config = LoreConfig.model_validate(payload)
        policy = derive_edge_policy(config, resolve_posture(config))
        assert any(entry.split(":")[0] == lan_host for entry in policy.allowed_hosts)

    def test_the_loopback_posture_does_not_allow_the_claude_origins(
        self, tmp_path: Path
    ) -> None:
        # M8 / WB35. LOOPBACK installs NO auth at all. Trusting ``https://claude.ai``
        # there means a page served from that origin can reach an unauthenticated local
        # lore through the browser. Every other posture's origin set is asserted; this
        # one never was.
        from loremaster.auth import derive_edge_policy
        from loremaster.config import LoreConfig, resolve_posture

        config = LoreConfig.model_validate(base_config_payload(slug(), tmp_path / "live"))
        policy = derive_edge_policy(config, resolve_posture(config))
        assert CLAUDE_AI_ORIGIN not in policy.allowed_origins, (
            "the LOOPBACK posture must not trust claude.ai's origin — it installs no "
            "auth, so an allowed cross-origin is an unauthenticated door"
        )
        assert CLAUDE_COM_ORIGIN not in policy.allowed_origins

    def test_the_lan_bearer_auth_settings_require_the_read_scope_too(
        self, tmp_path: Path
    ) -> None:
        # N6 / WB55 — the previous wave's M9 pinned ``required_scopes`` for HOSTED_OAUTH
        # only, so the same deletion one posture over went unseen. Behaviourally inert
        # today (every minted token carries lore:read) and a silently removed
        # defence-in-depth layer the day any branch mints a scopeless token. The property
        # is "every GATED posture", not "the posture I was thinking about".
        from loremaster.server import LoreServer, build_mcp_server

        from lorerunes import SCOPE_READ

        mcp = build_mcp_server(LoreServer(lan_bearer_config(tmp_path)))
        assert mcp.settings.auth is not None
        assert mcp.settings.auth.required_scopes == [SCOPE_READ]

    def test_the_hosted_auth_settings_require_the_read_scope(self, tmp_path: Path) -> None:
        # M9 / WB45. Design §6 names the value. With ``required_scopes=[]`` the SDK's
        # RequireAuthMiddleware enforces nothing — behaviourally identical TODAY (every
        # minted token carries lore:read) and a silently deleted defence-in-depth layer
        # the day any verifier branch mints a scopeless token.
        from loremaster.server import LoreServer, build_mcp_server

        from lorerunes import SCOPE_READ

        mcp = build_mcp_server(LoreServer(hosted_config(tmp_path)))
        assert mcp.settings.auth is not None
        assert mcp.settings.auth.required_scopes == [SCOPE_READ]

    def test_the_edge_policy_is_hashable_and_frozen(self, tmp_path: Path) -> None:
        # It is shared by two layers; a mutable policy is a policy one layer can edit
        # out from under the other — the ONE-IMPLEMENTATION failure with extra steps.
        from loremaster.auth import derive_edge_policy
        from loremaster.config import resolve_posture

        config = hosted_config(tmp_path)
        policy = derive_edge_policy(config, resolve_posture(config))
        assert hash(policy) == hash(derive_edge_policy(config, resolve_posture(config)))
        with pytest.raises((AttributeError, TypeError)):
            setattr(policy, "allowed_hosts", frozenset())


class TestTheBootRefusalReachesTheThingThatActuallyBoots:
    """M2 + M3 — the adversary's verdict, in one sentence: *pinned at the seam where it was
    reasoned about, not at the seam where it is enforced.*

    R11/R12 say ``HOSTED_OAUTH`` REFUSES TO BOOT unless the roster loads with at least one
    valid entry, and design R4 says lore must never itself listen off loopback. The
    original contract pinned both on ``resolve_posture`` — **a function that is not what
    boots**. Two wrong builds walked straight through:

    * **WB34** — ``build_mcp_server`` catches ``PostureConfigError`` and degrades to
      ``LOOPBACK``. An incoherent config, or a roster that will not load, then yields a
      server with **NO auth wired at all**; if lore-caddy is already pointed at it, that is
      an unauthenticated, internet-facing lore. Ask the repo's own question: *"if step N
      silently no-opped, would step N+1 still print something that reads as success?"*
      Here step N+1 prints a perfectly healthy server.
    * **WB33** — ``resolve_posture`` hardcodes ``host_is_loopback=True``. ``lorerunes``
      pins ``derive_posture(host_is_loopback=False)`` → refusal, but **nothing pinned the
      MAPPING** from ``config.server.host`` to that boolean, and every loremaster fixture
      binds ``127.0.0.1``.
    """

    def test_build_mcp_server_refuses_a_hosted_config_whose_roster_will_not_load(
        self, tmp_path: Path
    ) -> None:
        from loremaster.config import LoreConfig, PostureConfigError
        from loremaster.server import LoreServer, build_mcp_server

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = hosted_auth_block(roster)
        config = LoreConfig.model_validate(payload)
        roster.unlink()
        with pytest.raises(PostureConfigError):
            build_mcp_server(LoreServer(config))

    def test_build_asgi_app_refuses_it_too(self, tmp_path: Path) -> None:
        # The OTHER boot entry point. ``build_asgi_app`` is what uvicorn actually calls,
        # and a refusal that exists in only one of the two is a door.
        from loremaster.config import LoreConfig, PostureConfigError
        from loremaster.server import LoreServer, build_asgi_app, build_mcp_server

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = hosted_auth_block(roster)
        config = LoreConfig.model_validate(payload)
        mcp = build_mcp_server(LoreServer(config))
        roster.unlink()
        with pytest.raises(PostureConfigError):
            build_asgi_app(mcp, config)

    def test_a_healthy_hosted_config_still_builds(self, tmp_path: Path) -> None:
        # THE CONTROL: the refusal must not be a blanket one, or every pin above passes
        # on a build that refuses to boot at all.
        from loremaster.server import LoreServer, build_asgi_app, build_mcp_server

        config = hosted_config(tmp_path)
        mcp = build_mcp_server(LoreServer(config))
        assert mcp is not None
        assert build_asgi_app(mcp, config) is not None

    @pytest.mark.parametrize("host", ["0.0.0.0", "192.168.64.100", "::"])
    def test_a_hosted_config_on_a_NON_loopback_bind_refuses_to_boot(
        self, tmp_path: Path, host: str
    ) -> None:
        # M3 at the resolution seam. Design R4 / investigation M-2: a wide bind is
        # "instant whole-LAN exposure" — lore stays on loopback and the proxy comes to it.
        from loremaster.config import LoreConfig, PostureConfigError, resolve_posture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = host
        payload["auth"] = hosted_auth_block(roster)
        with pytest.raises(PostureConfigError):
            resolve_posture(LoreConfig.model_validate(payload))

    @pytest.mark.parametrize("host", ["0.0.0.0", "192.168.64.100", "::"])
    def test_build_mcp_server_also_refuses_a_non_loopback_hosted_bind(
        self, tmp_path: Path, host: str
    ) -> None:
        # M3 at the ENFORCEMENT seam — the whole lesson of this class. A build that maps
        # the host correctly inside ``resolve_posture`` but never calls it from the boot
        # path is WB34 and WB33 combined.
        from loremaster.config import LoreConfig, PostureConfigError
        from loremaster.server import LoreServer, build_mcp_server

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = host
        payload["auth"] = hosted_auth_block(roster)
        with pytest.raises(PostureConfigError):
            build_mcp_server(LoreServer(LoreConfig.model_validate(payload)))

    @pytest.mark.parametrize(
        "host",
        ["lore.firehawktransam.org", "lore-internal", "example.com", "", "not a host"],
    )
    def test_a_bind_host_the_mapping_does_not_RECOGNISE_refuses_to_boot(
        self, tmp_path: Path, host: str
    ) -> None:
        # N4 / WB51 / R15 — ⚑ THE UNKNOWN BRANCH, which the previous wave left free.
        # That wave widened this pin from one host to six, and every one of the six is a
        # value any classifier is CERTAIN to recognise: three canonical loopback
        # spellings, three canonical non-loopback addresses. Nothing pinned what happens
        # to a host the mapping does not recognise — and the natural implementation has
        # exactly that branch, because ``localhost`` is not an IP literal and
        # ``ipaddress.ip_address`` raises on it. A build whose ``except ValueError`` arm
        # returns True passed all six and booted HOSTED_OAUTH with lore bound to a
        # HOSTNAME that resolves to a LAN or public address — design R4 /
        # investigation M-2's "instant whole-LAN exposure", one spelling over from the
        # value the previous wave fixed.
        #
        # ⚑ THE GENERALISABLE SHAPE, worth more than the pin: when a contract pins only
        # values a classifier is certain to recognise, the UNKNOWN branch is unpinned —
        # and the unknown branch is exactly where the fail-open/fail-closed default
        # lives. R15 rules it CLOSED: True iff literal ``localhost`` or an IP whose
        # ``.is_loopback`` holds; anything unparseable is False, never True on exception.
        # ``""`` is included deliberately — it is uvicorn's all-interfaces spelling.
        from loremaster.config import LoreConfig, PostureConfigError, resolve_posture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = host
        payload["auth"] = hosted_auth_block(roster)
        with pytest.raises(PostureConfigError):
            resolve_posture(LoreConfig.model_validate(payload))

    @pytest.mark.parametrize("host", ["LOCALHOST", "LocalHost"])
    def test_a_loopback_spelling_in_a_DIFFERENT_CASE_still_resolves(
        self, tmp_path: Path, host: str
    ) -> None:
        # R15 says "the literal ``localhost`` (lowercased)". A yaml carrying ``LOCALHOST``
        # is an honest config, and refusing it would be the gate insulting honest code —
        # which is how a gate gets switched off. The CONTROL against over-tightening the
        # fix for WB51.
        from loremaster.config import LoreConfig, resolve_posture

        from lorerunes import Posture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = host
        payload["auth"] = hosted_auth_block(roster)
        assert resolve_posture(LoreConfig.model_validate(payload)) is Posture.HOSTED_OAUTH

    def test_the_container_entry_point_propagates_the_refusal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # N8 / WB54 — THE THIRD BOOT SITE. ``build_mcp_server`` and ``build_asgi_app`` are
        # pinned above; what the CONTAINER actually runs is
        # ``CMD ["python","-m","loremaster.server"]`` → ``main()`` → ``LoreServer.run()``,
        # which no pin touched. A try/except there that degrades to a no-auth config
        # serves an unauthenticated internet-facing lore with every other pin green.
        # uvicorn is stubbed to a class that FAILS if it is ever constructed, so the
        # assertion is "serving was never reached" rather than "an exception happened".
        import uvicorn
        from loremaster.config import LoreConfig, PostureConfigError
        from loremaster.server import LoreServer

        served: list[Any] = []

        class _NeverServes:
            def __init__(self, config: Any) -> None:
                served.append(config)

            def run(self) -> None:
                raise AssertionError("uvicorn must never be reached for a refused config")

        monkeypatch.setattr(uvicorn, "Server", _NeverServes)
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = hosted_auth_block(roster)
        config = LoreConfig.model_validate(payload)
        roster.unlink()

        with pytest.raises(PostureConfigError):
            LoreServer(config).run()
        assert not served, "a refused config must never reach uvicorn at all"

    @pytest.mark.parametrize(
        "host",
        ["127.0.0.1", "127.0.0.2", "127.0.1.1", "127.255.255.254", "::1", "localhost"],
    )
    def test_the_loopback_PREDICATE_holds_across_the_whole_127_8_grid(
        self, tmp_path: Path, host: str
    ) -> None:
        # ⚑ R15 SHARPENED BY WB71 — PIN THE PREDICATE, NEVER ITS SPELLINGS. A build that
        # spelled ``host_is_loopback`` as a LITERAL SET — ``{localhost, 127.0.0.1, ::1}``
        # — passed every host pin the previous wave wrote and then REFUSED TO BOOT on
        # ``127.0.0.2``, which is loopback. The whole of 127/8 is loopback, and the
        # implementation must delegate to ``ipaddress.ip_address(...).is_loopback`` rather
        # than enumerate.
        #
        # Ask: *"would a hand-list of every loopback spelling I tested still pass this?"*
        # If yes, the grid is too small. This grid is chosen so no plausible literal set
        # survives it.
        from loremaster.config import LoreConfig, resolve_posture

        from lorerunes import Posture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = host
        payload["auth"] = hosted_auth_block(roster)
        assert resolve_posture(LoreConfig.model_validate(payload)) is Posture.HOSTED_OAUTH

    @pytest.mark.parametrize(
        "host", ["10.0.0.1", "192.168.64.100", "0.0.0.0", "128.0.0.1", "126.255.255.255"]
    )
    def test_the_loopback_PREDICATE_rejects_addresses_just_outside_127_8(
        self, tmp_path: Path, host: str
    ) -> None:
        # The negative half of the same grid, including the two addresses immediately
        # either side of 127/8 — a predicate implemented as a sloppy prefix match
        # (``host.startswith("127")``) or an off-by-one range check dies here.
        from loremaster.config import LoreConfig, PostureConfigError, resolve_posture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = host
        payload["auth"] = hosted_auth_block(roster)
        with pytest.raises(PostureConfigError):
            resolve_posture(LoreConfig.model_validate(payload))

    @pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
    def test_every_loopback_SPELLING_still_resolves_to_hosted_oauth(
        self, tmp_path: Path, host: str
    ) -> None:
        # THE CONTROL, and the other half of the monoculture: three spellings of the same
        # bind. A build recognising only the literal "127.0.0.1" refuses a legitimate
        # ``localhost`` or IPv6-loopback deployment at boot — a self-inflicted outage
        # that the refusal pins above would never catch.
        from loremaster.config import LoreConfig, resolve_posture

        from lorerunes import Posture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = host
        payload["auth"] = hosted_auth_block(roster)
        assert resolve_posture(LoreConfig.model_validate(payload)) is Posture.HOSTED_OAUTH


class TestNoInstanceAttributeShadowsABoundHandler:
    """R16 part 1 — the STRUCTURAL half that kills the wire-dead-shadowing CLASS.

    ``FastMCP.__init__`` calls ``_setup_handlers``, which registers the **bound** method
    with the low-level server. So ``mcp.<handler> = something`` after construction is live
    for every in-process caller and **DEAD ON THE WIRE**. Three wrong builds used exactly
    that, on three different handlers, in three consecutive waves — WB30 (`call_tool`),
    WB48 (dispatch order on the same route), WB93 (`list_tools`). Each fix pinned the door
    that had just been opened; this pins the CLASS.

    ⚠ THE HANDLER SET IS DERIVED FROM THE INSTALLED SDK, NEVER HAND-LISTED. A hand-list is
    the next name-list — the artifact this repo has the most receipts against (six
    instruments, six defeats) — and it would miss the eighth handler an SDK upgrade binds.

    **Coverage, stated honestly rather than over-claimed:** this catches attribute
    SHADOWING of bound handlers, which is the dead-on-wire class. It does not need to
    catch wire-LIVE replacements — a swapped ``_tool_manager`` (caught by the
    scoped-manager identity pin), a rewritten low-level handler table (wire-visible, so
    the wire pins catch it), or a subclass override (the sanctioned spelling, wire-live by
    construction).
    """

    def test_no_derived_handler_name_is_shadowed_on_the_composed_server(
        self, tmp_path: Path
    ) -> None:
        from _auth_fixtures import sdk_bound_handler_names
        from loremaster.server import LoreServer, build_mcp_server

        mcp = build_mcp_server(LoreServer(hosted_config(tmp_path)))
        shadowed = sorted(name for name in sdk_bound_handler_names() if name in vars(mcp))
        assert not shadowed, (
            f"instance attributes shadow bound handlers: {shadowed}. "
            f"``_setup_handlers`` registered the BOUND originals at construction, so these "
            f"overrides are live in process and DEAD ON THE WIRE — the WB30/WB48/WB93 "
            f"class. The sanctioned spelling is a SUBCLASS override (wire-live by "
            f"construction) or the scoped ToolManager."
        )

    @pytest.mark.parametrize("posture", ["hosted", "lan_bearer", "loopback"])
    def test_no_shadowing_in_any_posture(self, tmp_path: Path, posture: str) -> None:
        # ∀ postures — a filter installed only for the hosted branch is exactly the shape
        # WB93 took, and a single-posture pin would not see it.
        from _auth_fixtures import sdk_bound_handler_names
        from loremaster.server import LoreServer, build_mcp_server

        config = {
            "hosted": hosted_config,
            "lan_bearer": lan_bearer_config,
            "loopback": loopback_config,
        }[posture](tmp_path)
        mcp = build_mcp_server(LoreServer(config))
        assert not [name for name in sdk_bound_handler_names() if name in vars(mcp)]

    def test_the_derivation_sees_the_routes_that_have_receipts(self) -> None:
        # The instrument's own honesty check: if the AST parse of ``_setup_handlers``
        # drifts and returns a smaller set, the pins above go quietly vacuous rather than
        # red. Both routes with a wrong-build receipt against them must be in the set.
        from _auth_fixtures import sdk_bound_handler_names

        handlers = sdk_bound_handler_names()
        assert {"call_tool", "list_tools"} <= handlers, (
            f"the SDK handler derivation lost a route with a WRONG-BUILD receipt against "
            f"it; got {sorted(handlers)}"
        )


class TestLoopbackPostureIsUnchanged:
    """The existing single-user deployment must not acquire a gate it never had."""

    async def test_no_auth_settings_are_configured(self, tmp_path: Path) -> None:
        from loremaster.server import LoreServer, build_mcp_server

        mcp = build_mcp_server(LoreServer(loopback_config(tmp_path)))
        assert mcp.settings.auth is None, (
            "the LOOPBACK posture installs NO auth — a local single-user deploy that "
            "suddenly 401s is a self-inflicted outage"
        )

    async def test_no_token_verifier_is_wired(self, tmp_path: Path) -> None:
        # The other half: FastMCP raises if a token_verifier is supplied without auth
        # settings, so this cannot be inferred from the pin above. A LOOPBACK build
        # that wires a verifier would gate the local deploy on Google being reachable.
        from loremaster.server import LoreServer, build_mcp_server

        mcp = build_mcp_server(LoreServer(loopback_config(tmp_path)))
        assert getattr(mcp, "_token_verifier", None) is None

    # The behavioural half — an unauthenticated ``initialize`` actually SUCCEEDS in the
    # LOOPBACK posture — needs a running session manager and lives in
    # ``test_auth_identity_seam::TestLoopbackPostureServesWithoutCredentials``.
