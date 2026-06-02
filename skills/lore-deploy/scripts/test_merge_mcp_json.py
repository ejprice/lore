"""Regression tests for the .mcp.json merge — auth header must be OPT-IN.

The local default lore deploy is no-auth (localhost mode); a `.mcp.json` for it
must NOT carry an `Authorization` header (a `Bearer ${UNSET_VAR}` both implies an
auth that isn't there and risks an unresolvable env-var expansion in the client).
The header is correct ONLY when Bearer-key auth is enabled, requested explicitly
via `--auth-key-env`.
"""

from __future__ import annotations

import json
from pathlib import Path

import merge_mcp_json


def test_no_auth_default_emits_no_header(tmp_path: Path) -> None:
    """Default (no --auth-key-env) → a headerless http entry (no-auth localhost)."""
    mcp = tmp_path / ".mcp.json"
    merge_mcp_json.main(
        ["--mcp-json", str(mcp), "--slug", "demo", "--port", "9201", "--path", "/mcp"]
    )
    entry = json.loads(mcp.read_text(encoding="utf-8"))["mcpServers"]["lore_demo"]
    assert entry["type"] == "http"
    assert entry["url"] == "http://127.0.0.1:9201/mcp"
    assert "headers" not in entry, "a no-auth deploy must not emit an Authorization header"


def test_auth_key_env_emits_bearer_header(tmp_path: Path) -> None:
    """With --auth-key-env, the entry carries Bearer ${THAT_VAR} (opt-in auth)."""
    mcp = tmp_path / ".mcp.json"
    merge_mcp_json.main(
        ["--mcp-json", str(mcp), "--slug", "demo", "--port", "9201",
         "--auth-key-env", "LORE_DEMO_KEY"]
    )
    entry = json.loads(mcp.read_text(encoding="utf-8"))["mcpServers"]["lore_demo"]
    assert entry["headers"]["Authorization"] == "Bearer ${LORE_DEMO_KEY}"


def test_merge_preserves_sibling_servers(tmp_path: Path) -> None:
    """Merging the lore entry never clobbers another server already present."""
    mcp = tmp_path / ".mcp.json"
    mcp.write_text(
        json.dumps({"mcpServers": {"other": {"type": "http", "url": "http://x/y"}}}),
        encoding="utf-8",
    )
    merge_mcp_json.main(["--mcp-json", str(mcp), "--slug", "demo", "--port", "9201"])
    servers = json.loads(mcp.read_text(encoding="utf-8"))["mcpServers"]
    assert servers["other"] == {"type": "http", "url": "http://x/y"}
    assert servers["lore_demo"]["url"] == "http://127.0.0.1:9201/mcp"
