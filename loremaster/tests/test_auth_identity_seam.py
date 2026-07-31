"""CONTRACT — F3: two principals, two sessions. Driven through the LIVE assembled app.

**This is the module packet 39 exists for.** Finding F3, verified by EXECUTION against
the installed SDK (``mcp`` 1.27.2), not by reasoning:

``mcp.server.streamable_http_manager.StreamableHTTPSessionManager._handle_stateful_request``
computes ``requestor = authorization_context(user)`` and compares it against
``self._session_owners[session_id]``; ``authorization_context`` returns exactly
``(client_id, claims["iss"], subject)``. odoo-code's verifier — the port this packet
starts from — returns ``AccessToken(token=…, client_id=<google client id>,
scopes=["email"])`` with **no ``subject`` and no ``claims``**. So for every Google user
the tuple is ``(<same client id>, None, None)``, the comparison is between two identical
values, and **the session binding is inert**: any allowlisted principal can resume any
other's MCP session by presenting their own valid token plus the victim's session id.

It is masked in odoo-code because Odoo re-checks ACLs on every downstream call.
**lore has no downstream check.** A verbatim port is green at every gate.

------------------------------------------------------------------------------
WHY THE PINS HERE RUN THE REAL LIFESPAN

The SDK's entire auth branch is ``# pragma: no cover`` upstream, and the ownership
comparison lives inside the session manager — reachable only once its task group is
running. A verifier-level assertion that two ``AccessToken``s differ (which
``test_google_token_verifier`` also makes) does NOT prove the SDK's comparison
discriminates: that depends on which FIELDS the SDK reads, and reading them is the
whole finding. So these pins create a real MCP session over the real composed app and
try to hijack it.

The heavy startup (probe gate → SurrealDB → watcher) is stubbed — it has its own
contract in ``test_eager_startup.py`` and the ``initialize`` handshake never touches the
lifespan context. **Everything in the auth and session path is production code.**

------------------------------------------------------------------------------
THE WRONG BUILDS THESE PINS DISCRIMINATE AGAINST

* The verbatim odoo-code port (no ``subject``, no ``claims``) — hijack SUCCEEDS.
* A build that populates ``subject`` from something constant (the client id, a literal,
  the configured resource URL) — hijack SUCCEEDS, and every unit-level "subject is not
  empty" assertion still passes.
* A build that populates ``claims`` but not ``subject`` — the tuple differs only if the
  two principals have different issuers, which they never do. Hijack SUCCEEDS.
* A build whose ``EdgePolicy`` never reaches ``TransportSecuritySettings`` — every pin
  in ``test_auth_composition`` passes and the first real hosted request is answered
  **421**, because FastMCP auto-enabled loopback-only Host validation.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from _auth_fixtures import (
    API_KEY_ENV_LAN_CLIENT,
    API_KEY_ENV_LOCAL_AGENT,
    API_KEY_VALUE_LAN_CLIENT,
    API_KEY_VALUE_LOCAL_AGENT,
    CLAUDE_AI_ORIGIN,
    LOOPBACK_HOST,
    MCP_PATH,
    MCP_POST_HEADERS,
    OPERATOR_EMAIL,
    OPERATOR_SUBJECT,
    PUBLIC_HOSTNAME,
    SECOND_PRINCIPAL_EMAIL,
    SECOND_PRINCIPAL_SUBJECT,
    SERVER_PORT,
    AsgiResponse,
    TokeninfoSpy,
    admitted_payload,
    base_config_payload,
    bearer,
    drive,
    google_access_token,
    hosted_auth_block,
    json_rpc_initialize,
    lan_bearer_auth_block,
    mcp_session_id,
    running_asgi_app,
    slug,
    stub_heavy_startup,
    write_roster,
)

# The Host header a hosted request actually carries: lore-caddy reverse-proxies to
# 127.0.0.1:9202 while FORWARDING the original Host, so this — not the loopback bind —
# is what the SDK's transport-security layer sees in production.
HOSTED_HOST = PUBLIC_HOSTNAME.encode("ascii")
LOOPBACK_HOST_HEADER = f"{LOOPBACK_HOST}:{SERVER_PORT}".encode("ascii")

# A Host an attacker would supply in a DNS-rebinding attempt.
REBINDING_HOST = b"lore.attacker.example"

# Every HTTP exchange here is bounded, so a transport that never closes its stream
# fails the pin loudly instead of wedging the suite.
EXCHANGE_TIMEOUT_S = 20.0

# The MCP session header, spelled once.
SESSION_HEADER = b"mcp-session-id"

def hosted_refusal_marker() -> str:
    """The substring proving the POSTURE GUARD produced a response, not the tool.

    Taken from the posture NAME on the enum rather than a hand-typed literal, so a
    rename cannot leave these pins silently matching nothing and going green — the
    dead-marker failure this repo has receipts for. Imported lazily because the
    contract is written before ``lorerunes`` exports the enum, and a module-level
    import would collapse every pin in this file into one collection error.
    """
    from lorerunes import Posture

    return str(Posture.HOSTED_OAUTH.name)


class _TwoPrincipalEdge:
    """The hosted app plus two live Google principals, each with their own token."""

    def __init__(self, tmp_path: Path) -> None:
        from loremaster.config import LoreConfig
        from loremaster.server import LoreServer, build_asgi_app, build_mcp_server

        roster = write_roster(
            tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL
        )
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = hosted_auth_block(roster)
        config = LoreConfig.model_validate(payload)

        self.operator_token = google_access_token("operator")
        self.colleague_token = google_access_token("colleague")
        self.spy = TokeninfoSpy(responder=self._respond)

        mcp = build_mcp_server(LoreServer(config), http_client=self.spy.client())
        # Deterministic single-shot bodies. The ownership comparison happens BEFORE any
        # body is produced, so the encoding is irrelevant to what is under contract —
        # but an SSE stream that stays open would turn a failure into a hang.
        mcp.settings.json_response = True
        stub_heavy_startup(mcp)
        self.app = build_asgi_app(mcp, config)

    def _respond(self, request: httpx.Request) -> httpx.Response:
        if self.operator_token.encode() in request.content:
            return httpx.Response(
                200, json=admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT)
            )
        if self.colleague_token.encode() in request.content:
            return httpx.Response(
                200,
                json=admitted_payload(
                    email=SECOND_PRINCIPAL_EMAIL, sub=SECOND_PRINCIPAL_SUBJECT
                ),
            )
        return httpx.Response(401)


async def open_session_and_call_tool(
    app: Any, *, token: str, tool_name: str, arguments: dict[str, Any] | None = None
) -> str:
    """Drive a REAL MCP session to `tools/call` and return the decoded response body.

    ⚠ THIS IS THE SEQUENCE THE CONTRACT WAS MISSING (adversary M1 / WB30). The hosted
    read-only guard was pinned only through the in-process ``mcp.call_tool(...)`` entry
    point — and ``FastMCP.__init__`` calls ``_setup_handlers``, which registers the BOUND
    ``self.call_tool`` with the lowlevel server. So a guard installed after construction
    as an instance attribute is live for a test and DEAD on the wire, with all 422 pins
    green. Only a real ``tools/call`` can tell the two apart.

    Args:
        app: The assembled ASGI app, with its lifespan already running.
        token: The Bearer credential to authenticate as.
        tool_name: The tool to dispatch.
        arguments: The tool arguments (default empty — the guard must refuse BEFORE
            argument validation, and an argument-validation error in the body is
            precisely how WB30 was caught).

    Returns:
        The decoded response body of the ``tools/call``.
    """
    opened = await post_mcp(app, token=token)
    assert opened.status == 200, (
        f"initialize failed ({opened.status}) — the wire pin cannot say anything about "
        f"dispatch if no session exists: {opened.body[:300]!r}"
    )
    session = mcp_session_id(opened)
    await post_mcp(
        app,
        token=token,
        session_id=session,
        body=b'{"jsonrpc":"2.0","method":"notifications/initialized"}',
    )
    called = await post_mcp(
        app,
        token=token,
        session_id=session,
        body=json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments or {}},
            }
        ).encode("utf-8"),
    )
    return called.body.decode("utf-8", "replace")


async def post_mcp(
    app: Any,
    *,
    token: str | None = None,
    session_id: str | None = None,
    host: bytes = HOSTED_HOST,
    origin: bytes | None = None,
    body: bytes | None = None,
) -> AsgiResponse:
    """POST one MCP request over the assembled app, with a hard timeout."""
    headers: list[tuple[bytes, bytes]] = [(b"host", host), *MCP_POST_HEADERS]
    if token is not None:
        headers.append(bearer(token))
    if session_id is not None:
        headers.append((SESSION_HEADER, session_id.encode("ascii")))
    if origin is not None:
        headers.append((b"origin", origin))
    return await asyncio.wait_for(
        drive(
            app,
            method="POST",
            path=MCP_PATH,
            headers=headers,
            body=body if body is not None else json_rpc_initialize(),
        ),
        timeout=EXCHANGE_TIMEOUT_S,
    )


@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Export the api-key env vars the hosted/LAN auth blocks reference."""
    monkeypatch.setenv(API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LOCAL_AGENT)
    monkeypatch.setenv(API_KEY_ENV_LAN_CLIENT, API_KEY_VALUE_LAN_CLIENT)


class TestSessionsAreBoundToTheCredentialThatCreatedThem:
    """F3 — the hijack, attempted against the real composed app."""

    async def test_a_listed_principal_can_open_a_session(self, tmp_path: Path) -> None:
        # POSITIVE CONTROL, and it is load-bearing: if no session is ever created, the
        # hijack pin below passes vacuously — a 404 for "session not found" is exactly
        # what a nonexistent session also returns.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            response = await post_mcp(edge.app, token=edge.operator_token)
            assert response.status == 200, (
                f"an allowlisted principal must be able to initialize a session; got "
                f"{response.status} body={response.body[:400]!r}"
            )
            assert mcp_session_id(response)

    async def test_the_owner_can_reuse_their_own_session(self, tmp_path: Path) -> None:
        # The SECOND control. Without it, a build that rejects EVERY session-carrying
        # request would pass the hijack pin — "session not found" for everyone.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            opened = await post_mcp(edge.app, token=edge.operator_token)
            session_id = mcp_session_id(opened)

            resumed = await post_mcp(
                edge.app,
                token=edge.operator_token,
                session_id=session_id,
                body=b'{"jsonrpc":"2.0","id":2,"method":"ping"}',
            )
            assert resumed.status != 404, (
                "the principal who CREATED the session must be able to use it; a 404 "
                "here means the ownership tuple is unstable across requests"
            )

    async def test_a_different_listed_principal_cannot_resume_the_session(
        self, tmp_path: Path
    ) -> None:
        # ⚠ THE PIN THIS PACKET EXISTS FOR. Both principals are on the roster, both hold
        # valid Google tokens minted through the SAME OAuth client — so ``client_id`` is
        # identical and only ``subject`` (and ``claims['iss']``) can distinguish them.
        # Under the verbatim odoo-code port both are ``None`` and this hijack SUCCEEDS.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            opened = await post_mcp(edge.app, token=edge.operator_token)
            victim_session = mcp_session_id(opened)

            hijack = await post_mcp(
                edge.app,
                token=edge.colleague_token,
                session_id=victim_session,
                body=b'{"jsonrpc":"2.0","id":3,"method":"ping"}',
            )
            assert hijack.status == 404, (
                f"a DIFFERENT allowlisted principal resumed another's MCP session "
                f"(status {hijack.status}). This is finding F3: the SDK derives "
                f"session ownership from (client_id, claims['iss'], subject), and a "
                f"verifier that leaves subject/claims unset makes every Google "
                f"principal identical. The SDK answers 404 'Session not found' when "
                f"the credential does not match."
            )

    async def test_an_api_key_principal_cannot_resume_a_google_session(
        self, tmp_path: Path
    ) -> None:
        # The cross-population case. An api-key principal has a different client_id
        # prefix AND a different subject, so this is the easy direction — which is
        # exactly why it is pinned: a build that distinguished ONLY the two populations
        # (and not two Google users) would pass it while failing the pin above.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            opened = await post_mcp(edge.app, token=edge.operator_token)
            victim_session = mcp_session_id(opened)

            hijack = await post_mcp(
                edge.app,
                token=API_KEY_VALUE_LOCAL_AGENT,
                session_id=victim_session,
                body=b'{"jsonrpc":"2.0","id":4,"method":"ping"}',
            )
            assert hijack.status == 404

    async def test_two_api_key_principals_do_not_share_a_session(
        self, tmp_path: Path
    ) -> None:
        # Value monoculture, at the api-key branch: two DIFFERENT named keys must be
        # two different principals. A build that minted ``client_id="api_key"`` with no
        # name (or a constant subject) collapses every local agent into one identity.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            opened = await post_mcp(edge.app, token=API_KEY_VALUE_LOCAL_AGENT)
            assert opened.status == 200
            session_id = mcp_session_id(opened)

            hijack = await post_mcp(
                edge.app,
                token=API_KEY_VALUE_LAN_CLIENT,
                session_id=session_id,
                body=b'{"jsonrpc":"2.0","id":5,"method":"ping"}',
            )
            assert hijack.status == 404, (
                "two distinct named api keys resolved to the same session owner"
            )

    async def test_an_unauthenticated_request_cannot_resume_a_session(
        self, tmp_path: Path
    ) -> None:
        # The gate must fire before the session lookup; a credential-free request with
        # a stolen session id must never be served.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            opened = await post_mcp(edge.app, token=edge.operator_token)
            victim_session = mcp_session_id(opened)

            anonymous = await post_mcp(
                edge.app,
                session_id=victim_session,
                body=b'{"jsonrpc":"2.0","id":6,"method":"ping"}',
            )
            assert anonymous.status == 401


class TestTheReadOnlyGuardFiresOnTheSERVEDPath:
    """M1 / WB30 — THE BLOCKER. The guard must run where production dispatches, not where a test does.

    ⚑ WHY THIS CLASS EXISTS, stated plainly because it is the sharpest lesson of the
    packet. Every one of the 55 pins in ``test_hosted_readonly_posture`` calls
    ``mcp.call_tool(...)`` directly. ``FastMCP.__init__`` calls ``_setup_handlers``,
    which registers the **bound** ``self.call_tool`` with the lowlevel server
    (SDK ``server/fastmcp/server.py``), so a guard installed after construction as an
    instance attribute — ``mcp.call_tool = _guarded`` — is live for those 55 pins and
    **completely dead on the wire**. The adversary built exactly that (WB30) and it
    passed all 422 pins while dispatching straight into ``lore_remember``.

    This is CLAUDE.md's own law, verbatim: *"a runtime gate is an invariant only over
    code it actually RUNS — so check coverage as a variable."* The contract checked the
    gate and never checked its REACH.

    The generalisable question, which is worth more than the pin: **"does this exercise
    the SERVED path, or a path only a test uses?"** The SDK's auth branch being
    ``# pragma: no cover`` upstream is the same warning from the other side.

    All three pins below drive a REAL session over the assembled app. The two controls
    are not optional: a build that refused EVERYTHING over the wire would pass the first
    pin alone.
    """

    async def test_a_hosted_principal_is_refused_a_mutating_tool_over_the_WIRE(
        self, tmp_path: Path
    ) -> None:
        # The pin WB30 survives. A real Google principal, admitted by the real verifier,
        # holding a real MCP session, calls a real mutating tool over the real transport.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            body = await open_session_and_call_tool(
                edge.app, token=edge.operator_token, tool_name="lore_remember"
            )
        assert hosted_refusal_marker() in body, (
            f"a hosted Google principal reached the MUTATING tool `lore_remember` over "
            f"the SERVED path. The read-only posture is decorative in production. "
            f"(WB30's tell is an argument-validation error in this body — that is the "
            f"tool itself answering, which means the guard never ran.) Body: {body[:500]!r}"
        )

    async def test_a_hosted_principal_is_NOT_refused_a_READ_tool_over_the_wire(
        self, tmp_path: Path
    ) -> None:
        # CONTROL 1. Without it, a build that refuses every wire dispatch passes the pin
        # above — and hosted principals, whose whole purpose is reading, get nothing.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            body = await open_session_and_call_tool(
                edge.app, token=edge.operator_token, tool_name="lore_search"
            )
        assert hosted_refusal_marker() not in body, (
            f"`lore_search` is read-only and must reach dispatch for a hosted principal; "
            f"it was refused by the posture guard. Body: {body[:500]!r}"
        )

    async def test_an_api_key_principal_is_NOT_refused_a_mutating_tool_over_the_wire(
        self, tmp_path: Path
    ) -> None:
        # CONTROL 2, on the other axis: design §1's mechanical verdict — "an api-key
        # principal can call mutating tools through the hosted port" — is INTENDED. A
        # guard that keyed on the posture rather than the principal's SCOPES would pass
        # both pins above and lock every local agent out of its own machine.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            body = await open_session_and_call_tool(
                edge.app, token=API_KEY_VALUE_LOCAL_AGENT, tool_name="lore_remember"
            )
        assert hosted_refusal_marker() not in body, (
            f"an api-key principal was refused a mutating tool over the wire; api keys "
            f"are the local/LAN trust anchor and retain the FULL surface. "
            f"Body: {body[:500]!r}"
        )


class TestApiKeyPrincipalsStillWorkInHostedPosture:
    """Design §5's operational consequence: in HOSTED_OAUTH the SDK gates EVERYONE."""

    async def test_a_named_api_key_can_open_a_session_through_the_hosted_gate(
        self, tmp_path: Path
    ) -> None:
        # The atomic-cutover rider: local agents authenticate with an API key once the
        # posture flips. If this failed, every local session on this box would 401 the
        # moment lore-lore is switched to HOSTED_OAUTH.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            response = await post_mcp(
                edge.app, token=API_KEY_VALUE_LOCAL_AGENT, host=LOOPBACK_HOST_HEADER
            )
            assert response.status == 200, (
                f"an api-key principal must still authenticate in HOSTED_OAUTH (design "
                f"§5's atomic cutover); got {response.status}"
            )

    async def test_an_unknown_api_key_is_refused(self, tmp_path: Path) -> None:
        # The CONTROL: the gate must still be a gate.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            response = await post_mcp(
                edge.app,
                token="lk_00000000000000000000000000000000",
                host=LOOPBACK_HOST_HEADER,
            )
            assert response.status == 401


class TestHostAndOriginAreEnforcedInsideTheTransport:
    """R9's behavioural leg — the layer ``test_auth_composition`` cannot reach."""

    async def test_the_public_hostname_is_accepted(self, tmp_path: Path) -> None:
        # ⚠ THE PIN FOR THE 421 TRAP. FastMCP auto-enables DNS-rebinding protection for
        # a loopback bind with ``allowed_hosts=["127.0.0.1:*", "localhost:*",
        # "[::1]:*"]``. lore binds loopback in EVERY posture, so a build that leaves
        # ``transport_security`` unset answers 421 to every request lore-caddy forwards
        # — 100% broken in production, invisible to every loopback test.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            response = await post_mcp(
                edge.app, token=edge.operator_token, host=HOSTED_HOST
            )
            assert response.status == 200, (
                f"a request carrying the PUBLIC Host header (what lore-caddy forwards) "
                f"was answered {response.status}. A 421 here means the derived "
                f"EdgePolicy never reached TransportSecuritySettings and FastMCP's "
                f"loopback-only auto-default is in force."
            )

    async def test_the_loopback_host_is_still_accepted(self, tmp_path: Path) -> None:
        # The CONTROL: widening for the public hostname must not drop loopback, or a
        # local agent on 127.0.0.1:9202 gets a 421.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            response = await post_mcp(
                edge.app, token=edge.operator_token, host=LOOPBACK_HOST_HEADER
            )
            assert response.status == 200

    async def test_an_attacker_host_is_refused(self, tmp_path: Path) -> None:
        # The gate must still be a gate: a DNS-rebinding Host is 421 (the SDK's ruled
        # status for an invalid Host).
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            response = await post_mcp(
                edge.app, token=edge.operator_token, host=REBINDING_HOST
            )
            assert response.status == 421, (
                f"a rebinding Host must be refused 421 by the SDK's transport-security "
                f"layer; got {response.status}"
            )

    async def test_the_claude_origin_passes_BOTH_origin_layers(
        self, tmp_path: Path
    ) -> None:
        # R9's ONE-DERIVATION property, stated behaviourally. lore's outer middleware
        # and the SDK's transport both check Origin. A build that adds the claude
        # origins to only ONE of them passes every composition pin and 403s the real
        # connector the moment a session is created — at the layer no unit test reaches.
        edge = _TwoPrincipalEdge(tmp_path)
        async with running_asgi_app(edge.app):
            response = await post_mcp(
                edge.app,
                token=edge.operator_token,
                origin=CLAUDE_AI_ORIGIN.encode("ascii"),
            )
            assert response.status == 200, (
                f"Origin {CLAUDE_AI_ORIGIN} passed the outer guard but was refused "
                f"({response.status}) inside the transport — the two Origin policies "
                f"have diverged, which is exactly what one shared derivation prevents"
            )


class TestLoopbackPostureServesWithoutCredentials:
    """The existing single-user deployment must not acquire a gate it never had."""

    def _loopback_app(self, tmp_path: Path) -> Any:
        from loremaster.config import LoreConfig
        from loremaster.server import LoreServer, build_asgi_app, build_mcp_server

        config = LoreConfig.model_validate(base_config_payload(slug(), tmp_path / "live"))
        mcp = build_mcp_server(LoreServer(config))
        mcp.settings.json_response = True
        stub_heavy_startup(mcp)
        return build_asgi_app(mcp, config)

    async def test_an_unauthenticated_initialize_succeeds(self, tmp_path: Path) -> None:
        app = self._loopback_app(tmp_path)
        async with running_asgi_app(app):
            response = await post_mcp(app, host=LOOPBACK_HOST_HEADER)
            assert response.status == 200, (
                f"the LOOPBACK posture must serve a credential-free request; got "
                f"{response.status}. A local single-user deploy that suddenly 401s is "
                f"a self-inflicted outage."
            )


class TestLanBearerPostureStillGatesOnApiKeys:
    """Today's networked deployment keeps working, and keeps its full surface."""

    def _lan_app(self, tmp_path: Path) -> Any:
        from loremaster.config import LoreConfig
        from loremaster.server import LoreServer, build_asgi_app, build_mcp_server

        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = lan_bearer_auth_block()
        config = LoreConfig.model_validate(payload)
        mcp = build_mcp_server(LoreServer(config))
        mcp.settings.json_response = True
        stub_heavy_startup(mcp)
        return build_asgi_app(mcp, config)

    async def test_a_valid_api_key_opens_a_session(self, tmp_path: Path) -> None:
        app = self._lan_app(tmp_path)
        async with running_asgi_app(app):
            response = await post_mcp(
                app, token=API_KEY_VALUE_LAN_CLIENT, host=LOOPBACK_HOST_HEADER
            )
            assert response.status == 200

    async def test_an_unauthenticated_request_is_401(self, tmp_path: Path) -> None:
        app = self._lan_app(tmp_path)
        async with running_asgi_app(app):
            response = await post_mcp(app, host=LOOPBACK_HOST_HEADER)
            assert response.status == 401

    async def test_a_google_token_is_not_accepted_in_lan_bearer_posture(
        self, tmp_path: Path
    ) -> None:
        # There is no Google branch to reach: no ``google`` block means no client id to
        # check ``aud`` against, and a build that "helpfully" fell back to a default
        # would accept tokens from an OAuth client nobody configured.
        app = self._lan_app(tmp_path)
        async with running_asgi_app(app):
            response = await post_mcp(
                app, token=google_access_token("wrong-posture"), host=LOOPBACK_HOST_HEADER
            )
            assert response.status == 401
