"""Contract (finding #466) — the ONE loopback helper is reachable from the lore-deploy test idiom.

Author: ``contract-466`` (TESTS ONLY). The helper's full contract lives in
``loremaster/tests/test_loopback_serving.py``; this file proves only the claim the HOME decision rests
on: ``loremaster.testing.loopback`` imports and works under the skill's own run idiom
(``cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests``) as well as from the
workspace ``testpaths`` run — so the lore-deploy stubs need no second copy of the policy.

It also exercises the real seam this tree cares about: ``lore_deploy._probe_mcp_port`` against a port
the helper SERVES (accepting) and a port the helper HOLDS un-listened (refused, race-free — the
``_dead_port`` semantics without the close that lets another process take the port).

⚠ Dated to HEAD ``1206233``: the module does not exist yet, so this file is RED (import error until the
stub lands, behavioural after).
"""

from __future__ import annotations

import http.server
import sys
import time
from pathlib import Path

from loremaster.testing import loopback
from loremaster.testing.loopback import LoopbackPort, serve_http

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import lore_deploy  # noqa: E402 — the scripts dir must be on sys.path first (sibling-test idiom)

_MCP_PATH = "/mcp"
_PROBE_TIMEOUT_S = 2.0
# connection-refused is immediate; anything near the probe timeout means it waited instead.
_REFUSAL_BOUND_S = 1.0


class _StubMCPHandler(http.server.BaseHTTPRequestHandler):
    """Any well-formed HTTP answer satisfies the probe (its contract is "bound and speaking HTTP")."""

    def do_POST(self) -> None:  # noqa: N802 — stdlib override name
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        body = b'{"jsonrpc": "2.0", "id": 0, "result": {}}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 — stdlib signature
        return


def test_the_helper_is_the_installed_workspace_member_not_a_namespace_shell() -> None:
    # #140's third poison mode: a member imported as an empty namespace package has __file__ None and
    # loads no code. Assert the helper is a real module inside the loremaster PACKAGE root.
    module_file = loopback.__file__
    assert module_file is not None, "loremaster.testing.loopback imported as an empty namespace shell"
    assert Path(module_file).resolve().parts[-3:] == ("loremaster", "testing", "loopback.py"), module_file


def test_the_probe_accepts_a_port_the_helper_serves() -> None:
    with serve_http(_StubMCPHandler) as served:
        accepting = lore_deploy._probe_mcp_port(
            served.host, served.port, _MCP_PATH, timeout_s=_PROBE_TIMEOUT_S
        )
    assert accepting is True


def test_the_probe_refuses_a_held_unlistened_port_fast() -> None:
    with LoopbackPort() as held:
        started = time.monotonic()
        accepting = lore_deploy._probe_mcp_port(held.host, held.port, _MCP_PATH, timeout_s=_PROBE_TIMEOUT_S)
        elapsed = time.monotonic() - started
    assert accepting is False
    assert elapsed < _REFUSAL_BOUND_S, (
        f"refusal took {elapsed:.2f}s — the probe waited instead of being refused"
    )
