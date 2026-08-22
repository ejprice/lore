"""CONTRACT (contract-39-w23) — composition: FastMCP(auth=…) per posture (design §8 / §13 g5).

Pins the standalone-fastmcp COMPOSITION — that ``build_mcp_server`` accepts the injected
``http_client`` (discharging the ``pending_contracts.yaml`` ``_auth_fixtures.py`` bound) and wires
``FastMCP(auth=…)`` + installs ``ReadOnlyGuardMiddleware`` differently per posture.

⚠ SCOPE — HARNESS-LIGHT (no wire). These pins assemble the composed ``FastMCP`` in-process via
``build_mcp_server`` and inspect ``mcp.auth`` / ``mcp.middleware`` — they do NOT open an SDK client
session or run the lifespan, so no live store is needed. The WIRE-driven half — the RFC 9728
``.well-known`` served/absent, the 401 ``resource_metadata=``, the Origin-outermost 403, wrong
Host — is ``test_auth_composition_wire.py`` (the transport-posture pins), which needs the recut
``wire_session`` hosted harness (contract ESC-1) and is authored once that lands.

The composition SEAM the recut wire harness relies on: the ``LoreTokenVerifier`` is reachable via
the fastmcp-native ``mcp.auth`` (hosted: ``mcp.auth.token_verifier``; LAN: ``mcp.auth`` itself), so
a test can force a verdict there — REPLACING the stale ``mcp._token_verifier`` seam the pre-recut
``wire_session`` monkeypatches (``_auth_fixtures.py:772``).

CONTRACT-FIRST: the stub ``build_mcp_server`` accepts ``http_client`` but wires NO auth and installs
NO guard (that is builder GREEN work), so the wiring pins fail on a clean ``assert mcp.auth is not
None`` (never an ImportError / AttributeError).
"""

from __future__ import annotations

from pathlib import Path

# A distinctive object the composition must thread through as the verifier's http_client (a real
# ``httpx.AsyncClient`` in production; here any sentinel proves the seam accepts + carries it).
import httpx
import pytest
from _auth_fixtures import set_test_store_creds
from _recut_auth_fixtures import build_composed_mcp
from fastmcp.server.auth import RemoteAuthProvider, TokenVerifier
from loremaster.readonly_guard import ReadOnlyGuardMiddleware
from loremaster.token_verifier import LoreTokenVerifier


@pytest.fixture(autouse=True)
def _thread_test_store_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Thread the SurrealDB test-store creds so the CORRECT composition resolves the verifier's
    store creds (config.surreal → resolve_secret) WITHOUT externally-set env (adversary-39-w23 #1).
    Auth-enabled postures point config.surreal at the test store (recut_config); loopback ignores it.
    """
    set_test_store_creds(monkeypatch)


class TestBuildMcpServerAcceptsHttpClient:
    def test_the_injected_http_client_param_exists(self, tmp_path: Path) -> None:
        # DISCHARGES the pending bound (_auth_fixtures.py referenced build_mcp_server(http_client=)
        # since packet 59). GREEN-now guard: build_composed_mcp(hosted, http_client=…) must not
        # TypeError. WRONG BUILD: a build_mcp_server that dropped the param (reintroduces the
        # pending mypy error + breaks the hosted wire harness).
        client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _r: httpx.Response(200)))
        try:
            mcp = build_composed_mcp(tmp_path, posture="hosted", http_client=client)
        finally:
            pass
        assert mcp is not None


class TestHostedOAuthComposition:
    """HOSTED_OAUTH → ``FastMCP(auth=RemoteAuthProvider(LoreTokenVerifier, authorization_servers=…))``
    + the read-only guard installed (design §8)."""

    def test_hosted_wires_the_lore_token_verifier_as_the_fastmcp_auth(
        self, tmp_path: Path
    ) -> None:
        # The verifier must be REACHABLE via the fastmcp-native auth seam (so the wire harness can
        # force verdicts there). WRONG BUILD: a build that passes no auth= (mcp.auth is None) — the
        # stub — or wires a non-lore verifier.
        client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _r: httpx.Response(200)))
        mcp = build_composed_mcp(tmp_path, posture="hosted", http_client=client)
        assert mcp.auth is not None, "HOSTED_OAUTH must wire FastMCP(auth=…), not leave it None"
        verifier = getattr(mcp.auth, "token_verifier", mcp.auth)
        assert isinstance(verifier, LoreTokenVerifier), (
            "the hosted auth provider must wrap the lore resource-server verifier"
        )

    def test_hosted_auth_is_a_remote_auth_provider_advertising_authorization_servers(
        self, tmp_path: Path
    ) -> None:
        # A RemoteAuthProvider is what serves the RFC 9728 .well-known protected-resource metadata
        # (advertising the authorization server(s)). WRONG BUILD: wiring the bare LoreTokenVerifier
        # as auth= (which gates /mcp but serves NO .well-known — the LAN_BEARER shape) in a hosted
        # deploy, so claude.ai's connector cannot discover the authorization server.
        client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _r: httpx.Response(200)))
        mcp = build_composed_mcp(tmp_path, posture="hosted", http_client=client)
        assert mcp.auth is not None
        assert isinstance(mcp.auth, RemoteAuthProvider), (
            "HOSTED_OAUTH must advertise its authorization server(s) via RemoteAuthProvider "
            "(the .well-known advertiser), not a bare TokenVerifier"
        )

    def test_hosted_installs_the_read_only_guard_middleware(self, tmp_path: Path) -> None:
        # The #295 enforcement guard must be INSTALLED in the middleware chain for the hosted
        # deploy. WRONG BUILD: composing hosted auth without the guard — every hosted principal
        # would reach the mutating tools (the read-only-hosted banner violated).
        client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _r: httpx.Response(200)))
        mcp = build_composed_mcp(tmp_path, posture="hosted", http_client=client)
        assert any(isinstance(m, ReadOnlyGuardMiddleware) for m in mcp.middleware), (
            "ReadOnlyGuardMiddleware must be installed in the hosted middleware chain"
        )


class TestLanBearerComposition:
    def test_lan_bearer_wires_a_bare_token_verifier_not_a_remote_auth_provider(
        self, tmp_path: Path
    ) -> None:
        # LAN_BEARER gates /mcp with the api-key branch but serves NO .well-known (there is no
        # authorization server to advertise). So auth is the bare LoreTokenVerifier (a
        # TokenVerifier), NOT a RemoteAuthProvider. WRONG BUILD: leaving auth None (no gate on the
        # LAN), or wiring a RemoteAuthProvider (advertising a .well-known that does not apply).
        mcp = build_composed_mcp(tmp_path, posture="lan_bearer")
        assert mcp.auth is not None, "LAN_BEARER must gate /mcp with the api-key verifier"
        assert isinstance(mcp.auth, TokenVerifier), (
            "LAN_BEARER auth must be the bare LoreTokenVerifier (a TokenVerifier)"
        )
        assert not isinstance(mcp.auth, RemoteAuthProvider), (
            "LAN_BEARER must NOT advertise a .well-known (no RemoteAuthProvider)"
        )
        assert isinstance(mcp.auth, LoreTokenVerifier), "the LAN verifier is the lore verifier"


class TestLoopbackComposition:
    def test_loopback_installs_no_auth_provider(self, tmp_path: Path) -> None:
        # GREEN-now guard (RED on over-wiring): the unchanged local single-user mode installs NO
        # auth. WRONG BUILD: wiring an auth provider on loopback would break every local session
        # (they carry no bearer).
        mcp = build_composed_mcp(tmp_path, posture="loopback")
        assert mcp.auth is None, "LOOPBACK is the no-auth local mode — no auth provider"
