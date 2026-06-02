#!/usr/bin/env python3
"""Idempotently merge a project's ``.mcp.json`` ``lore_<slug>`` server entry.

Claude Code reads a project's ``.mcp.json`` to discover its MCP servers. This
script adds (or updates) ONLY the ``mcpServers.lore_<slug>`` entry, preserving
every other server and every other top-level key byte-for-byte — so re-running
``setup``/``start`` never clobbers a hand-edited config or a sibling server.

Idempotent: if the entry already equals the desired value, the file is left
untouched (no rewrite, no churn) and the script reports ``unchanged``.

The entry points at the local HTTP server. By default (no ``--auth-key-env``) it is
**headerless** — the local no-auth server has no auth middleware, and a
``Bearer ${UNSET_VAR}`` would only imply an auth that isn't there and risk an
unresolvable env-var expansion in the client. When the deferred Bearer-key auth is
enabled, pass ``--auth-key-env`` and the entry carries a ``Bearer ${THAT_VAR}``
header (expanded by Claude Code from the environment). Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_EXIT_OK = 0
_EXIT_ERROR = 2


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the .mcp.json merge."""
    parser = argparse.ArgumentParser(
        prog="merge_mcp_json",
        description="Idempotently merge the lore_<slug> entry into a project .mcp.json.",
    )
    parser.add_argument(
        "--mcp-json", required=True, help="Path to the project's .mcp.json (created if absent)."
    )
    parser.add_argument("--slug", required=True, help="Project slug (the server is lore_<slug>).")
    parser.add_argument("--port", type=int, required=True, help="The server's host port.")
    parser.add_argument(
        "--path", default="/mcp", help="The server mount path (default: /mcp)."
    )
    parser.add_argument(
        "--auth-key-env",
        default=None,
        help=(
            "Env-var name holding the Bearer key (e.g. LORE_<SLUG>_KEY) when "
            "Bearer-key auth is enabled. Omit for the no-auth localhost default — "
            "then NO Authorization header is written."
        ),
    )
    return parser


def _desired_entry(port: int, mount_path: str, auth_key_env: str | None) -> dict[str, object]:
    """Build the desired ``lore_<slug>`` server entry.

    The local no-auth default (``auth_key_env is None``) emits a plain http entry
    with NO ``Authorization`` header — the server has no auth middleware, and a
    ``Bearer ${UNSET}`` would only mislead and risk an unresolvable env-var
    expansion in the client. When Bearer-key auth is enabled the caller passes the
    key's env-var name and the entry carries ``Bearer ${THAT_VAR}`` (expanded by
    Claude Code at connect time).
    """
    entry: dict[str, object] = {
        "type": "http",
        "url": f"http://127.0.0.1:{port}{mount_path}",
    }
    if auth_key_env:
        entry["headers"] = {"Authorization": f"Bearer ${{{auth_key_env}}}"}
    return entry


def main(argv: list[str] | None = None) -> int:
    """Merge (or no-op) the lore server entry into the project .mcp.json."""
    args = _build_parser().parse_args(argv)
    mcp_path = Path(args.mcp_json)
    server_name = f"lore_{args.slug}"
    desired = _desired_entry(args.port, args.path, args.auth_key_env)

    if mcp_path.exists():
        try:
            document = json.loads(mcp_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError) as error:
            print(f"merge_mcp_json: {mcp_path} is not valid JSON: {error}", file=sys.stderr)
            return _EXIT_ERROR
        if not isinstance(document, dict):
            print(f"merge_mcp_json: {mcp_path} top level is not an object.", file=sys.stderr)
            return _EXIT_ERROR
    else:
        document = {}

    servers = document.get("mcpServers")
    if not isinstance(servers, dict):
        servers = {}
        document["mcpServers"] = servers

    if servers.get(server_name) == desired:
        print(f"merge_mcp_json: {server_name} already present and current (unchanged).")
        return _EXIT_OK

    servers[server_name] = desired
    mcp_path.parent.mkdir(parents=True, exist_ok=True)
    # Trailing newline + 2-space indent: a clean, diff-friendly file.
    mcp_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"merge_mcp_json: wrote {server_name} → {desired['url']}")
    return _EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
