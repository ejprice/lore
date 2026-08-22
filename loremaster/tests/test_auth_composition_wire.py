"""CONTRACT (contract-39-w23) — transport-posture pins on the assembled wire (design §13 g5).

The TRANSPORT half of the composition: what the assembled ASGI app does to ANONYMOUS requests
(``.well-known``, an unauthenticated ``POST /mcp``, a hostile ``Origin``, a wrong ``Host``).
These drive the RAW ASGI app via :func:`_auth_fixtures.drive` (no SDK session, no principal), so
they are behaviourally RED against the STUB composition (the pre-recut ``build_asgi_app`` still
ships ``BearerAuthMiddleware``, which 401s every anonymous request and serves no RFC 9728
metadata) and GREEN once the builder's composition lands (``FastMCP(auth=RemoteAuthProvider)``
serves ``.well-known`` anonymously + a 401 with ``resource_metadata=``, and
``OriginValidationMiddleware`` is outermost).

⚠ The enforcement (#295 EFFECT) pins that need an authenticated hosted principal on a drivable
SDK session are in ``test_readonly_guard.py`` (they need the composition's ``FastMCP(auth=…)`` to
authenticate a bearer, which is builder GREEN work — see that file + REPORT §Deferred-wire-pins).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest
from _auth_fixtures import (
    HOSTILE_ORIGIN,
    LOOPBACK_HOST,
    MCP_PATH,
    MCP_POST_HEADERS,
    WELL_KNOWN_PATH,
    TokeninfoSpy,
    base_config_payload,
    drive,
    hosted_auth_block,
    json_rpc_initialize,
    running_asgi_app,
    set_test_store_creds,
    slug,
    stub_heavy_startup,
    surreal_block_for_test_store,
)

# The always-allowed bind host (``_resolve_allowed_hosts`` allows config.server.host = the
# loopback bind), so a valid-Host anonymous drive needs no LORE_ALLOWED_HOSTS.
_BIND_HOST_HEADER = (b"host", LOOPBACK_HOST.encode("ascii"))


@pytest.fixture(autouse=True)
def _thread_test_store_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Thread the SurrealDB test-store creds so the CORRECT composition resolves the verifier's
    store creds (config.surreal → resolve_secret) WITHOUT externally-set env (adversary-39-w23 #1).
    The transport pins never CONNECT the store (anonymous requests), but the composed verifier is
    CONSTRUCTED at build time, resolving creds — so they must be present.
    """
    set_test_store_creds(monkeypatch)


def _hosted_app(tmp_path: Path, *, spy: TokeninfoSpy | None = None) -> Any:
    """Assemble the composed HOSTED ASGI app in-process (recut config; no store admission).

    The anonymous transport pins never ADMIT a principal (the store is never dialed), but the
    composed verifier is CONSTRUCTED from ``config.surreal`` at build time — so it is pointed at
    the test store with creds the autouse fixture sets, keeping the CORRECT build satisfiable
    WITHOUT externally-set env (adversary-39-w23 #1). When ``spy`` is given it is the verifier's
    injected ``http_client`` (so a pin can assert ZERO outbound provider calls).
    """
    from _surreal_harness import PRODUCTION_DIM, make_env, unique_database  # noqa: PLC0415
    from loremaster.config import LoreConfig  # noqa: PLC0415
    from loremaster.server import LoreServer, build_asgi_app, build_mcp_server  # noqa: PLC0415

    payload = base_config_payload(slug(), tmp_path / "live")
    payload["auth"] = hosted_auth_block()
    payload["surreal"] = surreal_block_for_test_store(
        make_env(database=unique_database(), dim=PRODUCTION_DIM)
    )
    config = LoreConfig.model_validate(payload)
    server = LoreServer(config)
    mcp = build_mcp_server(server, http_client=(spy.client() if spy is not None else None))
    stub_heavy_startup(mcp)
    return build_asgi_app(mcp, config)


class TestHostedTransportPosture:
    async def test_wellknown_is_served_200_and_anonymous(self, tmp_path: Path) -> None:
        # RFC 9728: the protected-resource metadata is world-readable (no bearer). WRONG BUILD /
        # STUB: BearerAuthMiddleware gates ALL paths (→ 401), or no RemoteAuthProvider serves the
        # route (→ 404). GREEN when a RemoteAuthProvider serves it anonymously.
        app = _hosted_app(tmp_path)
        async with running_asgi_app(app):
            response = await drive(app, method="GET", path=WELL_KNOWN_PATH, headers=[_BIND_HOST_HEADER])
        assert response.status == 200, (
            f".well-known must be 200 and anonymous in HOSTED_OAUTH (RFC 9728); got "
            f"{response.status} — a BearerAuthMiddleware-gated or unrouted build fails here"
        )

    async def test_unauthenticated_post_401_carries_resource_metadata(self, tmp_path: Path) -> None:
        # An unauthenticated POST /mcp → 401 whose WWW-Authenticate carries ``resource_metadata=``
        # (RFC 9728 — points the client at .well-known). WRONG BUILD / STUB: the hand-rolled
        # BearerAuthMiddleware 401 is ``Bearer realm="loremaster"`` with NO resource_metadata.
        app = _hosted_app(tmp_path)
        async with running_asgi_app(app):
            response = await drive(
                app,
                method="POST",
                path=MCP_PATH,
                headers=[_BIND_HOST_HEADER, *MCP_POST_HEADERS],
                body=json_rpc_initialize(),
            )
        assert response.status == 401, f"an unauthenticated POST /mcp must be 401; got {response.status}"
        challenge = response.header("www-authenticate")
        assert "resource_metadata" in challenge.lower(), (
            "the 401 must carry a resource_metadata= pointer (RFC 9728); the hand-rolled "
            f"BearerAuthMiddleware challenge does not. www-authenticate={challenge!r}"
        )

    async def test_disallowed_origin_is_403_with_zero_outbound_provider_calls(
        self, tmp_path: Path
    ) -> None:
        # A hostile Origin → 403 (OriginValidationMiddleware OUTERMOST — design §6/R6) with ZERO
        # outbound provider calls (rejected BEFORE any credential parse / tokeninfo call). WRONG
        # BUILD / STUB: BearerAuthMiddleware wraps OUTSIDE OriginValidationMiddleware, so a
        # no-bearer request is 401 (credential-first), not 403 (Origin-first).
        spy = TokeninfoSpy(responder=lambda _r: httpx.Response(401))
        app = _hosted_app(tmp_path, spy=spy)
        async with running_asgi_app(app):
            response = await drive(
                app,
                method="POST",
                path=MCP_PATH,
                headers=[_BIND_HOST_HEADER, (b"origin", HOSTILE_ORIGIN.encode("ascii")), *MCP_POST_HEADERS],
                body=json_rpc_initialize(),
            )
        assert response.status == 403, (
            f"a disallowed Origin must be 403 (Origin OUTERMOST), not {response.status}; a "
            f"BearerAuthMiddleware-outermost build 401s a no-bearer request first"
        )
        assert spy.call_count == 0, (
            f"a disallowed Origin must be rejected with ZERO outbound provider calls "
            f"(Origin before any credential/tokeninfo work); spy saw {spy.call_count}"
        )

    async def test_wrong_host_is_refused(self, tmp_path: Path) -> None:
        # A non-allowlisted Host → refused by fastmcp's native host_origin_protection
        # (DNS-rebinding defence; server.py build_asgi_app host_origin_protection=True). This is a
        # GREEN-now guard: the property already holds via the current http_app config — it reddens
        # if a build turns host_origin_protection off. WRONG BUILD: a wrong Host served (2xx).
        app = _hosted_app(tmp_path)
        async with running_asgi_app(app):
            response = await drive(
                app,
                method="POST",
                path=MCP_PATH,
                headers=[(b"host", b"evil.attacker.example"), *MCP_POST_HEADERS],
                body=json_rpc_initialize(),
            )
        assert response.status >= 400, (
            f"a wrong Host must be refused (host_origin_protection), not served; got {response.status}"
        )


class TestLanBearerTransportPosture:
    async def test_wellknown_is_absent_in_lan_bearer(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # LAN_BEARER advertises NO authorization server, so there is no .well-known route → 404.
        # (The api-key branch gates /mcp; it serves no RFC 9728 metadata.) The pre-recut
        # build_asgi_app wraps BearerAuthMiddleware over the LAN config, so the key env vars must
        # resolve for the app to assemble; set them for the drive. WRONG BUILD: a LAN deploy that
        # advertises a .well-known (200) it cannot honour.
        from _auth_fixtures import (  # noqa: PLC0415
            API_KEY_ENV_LAN_CLIENT,
            API_KEY_ENV_LOCAL_AGENT,
            API_KEY_VALUE_LAN_CLIENT,
            API_KEY_VALUE_LOCAL_AGENT,
            lan_bearer_auth_block,
        )
        from _surreal_harness import PRODUCTION_DIM, make_env, unique_database  # noqa: PLC0415
        from loremaster.config import LoreConfig  # noqa: PLC0415
        from loremaster.server import LoreServer, build_asgi_app, build_mcp_server  # noqa: PLC0415

        monkeypatch.setenv(API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LOCAL_AGENT)
        monkeypatch.setenv(API_KEY_ENV_LAN_CLIENT, API_KEY_VALUE_LAN_CLIENT)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = lan_bearer_auth_block()
        # LAN's verifier (FastMCP(auth=LoreTokenVerifier) at GREEN) builds its stores from
        # config.surreal too, so point it at the test store (creds via the autouse fixture).
        payload["surreal"] = surreal_block_for_test_store(
            make_env(database=unique_database(), dim=PRODUCTION_DIM)
        )
        config = LoreConfig.model_validate(payload)
        mcp = build_mcp_server(LoreServer(config))
        stub_heavy_startup(mcp)
        app = build_asgi_app(mcp, config)
        async with running_asgi_app(app):
            response = await drive(app, method="GET", path=WELL_KNOWN_PATH, headers=[_BIND_HOST_HEADER])
        assert response.status == 404, (
            f"LAN_BEARER must not serve a .well-known (no authorization server to advertise); "
            f"got {response.status}"
        )
