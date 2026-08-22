"""Harness-light composed-``mcp`` builder for the wave-2/3 COMPOSITION-UNIT pins.

Reuses the ONE shared config-block builders in ``_auth_fixtures`` (``hosted_auth_block`` —
recut to the standalone-fastmcp shape 2026-08-22 — and ``lan_bearer_auth_block``) plus
``base_config_payload``; it does NOT clone them (no fork — the lead's ESC-1 constraint). The only
thing here is :func:`build_composed_mcp`, a HARNESS-LIGHT sibling of ``wire_session``: it drives
the real ``build_mcp_server`` (so the per-posture ``FastMCP(auth=…)`` wiring + guard install are
exercised) but opens NO SDK client session and runs NO lifespan, so the composition-unit pins
(``test_auth_composition_recut.py``) can inspect ``mcp.auth`` / ``mcp.middleware`` without a live
store. The full wire (#295 EFFECT, .well-known) is ``wire_session`` (``_auth_fixtures``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from _auth_fixtures import (
    base_config_payload,
    hosted_auth_block,
    lan_bearer_auth_block,
    slug,
    surreal_block_for_test_store,
)


def recut_config(tmp_path: Path, *, posture: str) -> Any:
    """Build a recut ``LoreConfig`` for ``posture`` (``hosted`` / ``lan_bearer`` / ``loopback``).

    ``base_config_payload`` binds the loopback host (``127.0.0.1``) — correct for both LOOPBACK
    and HOSTED_OAUTH (which requires a loopback bind, "the proxy comes to us", design §6). For the
    auth-enabled postures, ``config.surreal`` is pointed at the test store so the CORRECT build's
    composed ``LoreTokenVerifier`` resolves its store creds (which ``set_test_store_creds`` sets —
    the pins' autouse fixture) WITHOUT externally-set env (adversary-39-w23 #1 / C-DEF). The store
    is never CONNECTED here (build_mcp_server construction is lazy), so no DB is reaped.
    """
    from _surreal_harness import PRODUCTION_DIM, make_env, unique_database  # noqa: PLC0415
    from loremaster.config import LoreConfig  # noqa: PLC0415

    payload = base_config_payload(slug(), tmp_path / "live")
    if posture == "hosted":
        payload["auth"] = hosted_auth_block()
    elif posture == "lan_bearer":
        payload["auth"] = lan_bearer_auth_block()
    elif posture != "loopback":  # pragma: no cover - guards the caller
        raise AssertionError(f"unknown posture {posture!r}")
    if posture != "loopback":
        payload["surreal"] = surreal_block_for_test_store(
            make_env(database=unique_database(), dim=PRODUCTION_DIM)
        )
    return LoreConfig.model_validate(payload)


def build_composed_mcp(tmp_path: Path, *, posture: str, http_client: Any = None) -> Any:
    """Assemble the composed ``FastMCP`` in-process for ``posture`` — HARNESS-LIGHT (no wire).

    Drives the REAL ``build_mcp_server`` (so the per-posture ``FastMCP(auth=…)`` wiring + the
    ``ReadOnlyGuardMiddleware`` install are exercised) but does NOT open an SDK client session or
    run the lifespan, so no live store/socket is needed — the pins inspect ``mcp.auth`` /
    ``mcp.middleware`` only. The full wire is ``wire_session`` (contract ESC-1 recut).
    """
    from loremaster.server import LoreServer, build_mcp_server  # noqa: PLC0415

    config = recut_config(tmp_path, posture=posture)
    server = LoreServer(config)
    if posture == "hosted":
        return build_mcp_server(server, http_client=http_client)
    return build_mcp_server(server)
