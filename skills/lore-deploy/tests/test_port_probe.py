"""Tests for the lore-deploy MCP port-probe / wait-for-bind helpers.

Motivating incident: the ``lore-demand_intelligence`` container was "running"
and `status` reported healthy, but the MCP endpoint refused connections for
~4 minutes because loremaster's ASGI lifespan startup runs a boot-time
delta-reconcile BEFORE uvicorn binds the port. Neither `status` nor `start`
ever probed the live port — they only checked container state + the manifest
file. These tests cover the two new primitives that close that gap:

- ``lore_deploy._probe_mcp_port`` — a single point-in-time check of whether
  something is bound and speaking HTTP at (host, port, path). Any HTTP
  response (even non-2xx) counts as "accepting"; connection-refused/timeout
  means "not yet".
- ``lore_deploy._wait_for_bind`` — polls the probe until it succeeds or a
  budget elapses, calling an optional progress callback along the way.

Run with the skill idiom (the workspace venv — the stub servers come from the ONE
loopback helper, ``loremaster.testing.loopback``, finding #466):
``cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests``.
"""
from __future__ import annotations

import http.server
import sys
import threading
import time
from pathlib import Path

from loremaster.testing.loopback import LoopbackPort, serve_http

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import lore_deploy  # noqa: E402  (path must be extended before this import)


class _StubMCPHandler(http.server.BaseHTTPRequestHandler):
    """A minimal HTTP handler standing in for a real MCP server.

    Deliberately does NOT speak real MCP — the probe's contract is "is
    something bound and answering HTTP here", not "is this a valid MCP
    handshake", so any well-formed HTTP response must satisfy it.
    """

    def do_POST(self) -> None:  # noqa: N802 (stdlib override name)
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        body = b'{"jsonrpc": "2.0", "id": 0, "result": {}}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_str: str, *args: object) -> None:
        pass  # silence request logging during tests


def test_probe_reports_not_accepting_on_a_port_nothing_listens_on() -> None:
    """Connection-refused must read as NOT accepting, and return fast (no timeout wait)."""
    # A HELD, un-listened port (finding #466): refused like an unserved one, and no other
    # process can start serving it mid-test.
    with LoopbackPort() as unserved:
        started = time.monotonic()
        accepting = lore_deploy._probe_mcp_port(unserved.host, unserved.port, "/mcp", timeout_s=1.0)
        elapsed = time.monotonic() - started
    assert accepting is False
    assert elapsed < 2.0  # connection-refused is immediate, never the full timeout


def test_probe_reports_accepting_against_any_bound_http_listener() -> None:
    """A bound port answering ANY http response (not necessarily valid MCP) counts."""
    with serve_http(_StubMCPHandler) as served:
        accepting = lore_deploy._probe_mcp_port(served.host, served.port, "/mcp", timeout_s=2.0)
    assert accepting is True


def test_wait_for_bind_returns_promptly_once_a_listener_appears_mid_wait() -> None:
    """A listener appearing partway through the wait must be caught within ~1 poll tick."""
    listener_delay_s = 0.3
    wait_finished = threading.Event()

    # The port is HELD (refusing) from the start and served later on the SAME socket (finding
    # #466): the listener appears mid-wait with no window for another process to take the port.
    with LoopbackPort() as held:

        def _delayed_listen() -> None:
            time.sleep(listener_delay_s)
            with serve_http(_StubMCPHandler, port=held):
                wait_finished.wait(timeout=5.0)

        thread = threading.Thread(target=_delayed_listen, daemon=True)
        thread.start()
        try:
            started = time.monotonic()
            accepted = lore_deploy._wait_for_bind(
                held.host, held.port, "/mcp", timeout_s=5.0, poll_interval_s=0.05,
            )
            elapsed = time.monotonic() - started
        finally:
            wait_finished.set()
            thread.join(timeout=2.0)
    assert accepted is True
    assert elapsed < 3.0  # well under the 5s budget — caught soon after it appeared


def test_wait_for_bind_times_out_and_returns_false_when_nothing_ever_listens() -> None:
    """No listener ever appears → must return False (not raise) once the budget elapses."""
    with LoopbackPort() as unserved:
        accepted = lore_deploy._wait_for_bind(
            unserved.host, unserved.port, "/mcp", timeout_s=0.3, poll_interval_s=0.05,
        )
    assert accepted is False


def test_wait_for_bind_calls_on_progress_while_waiting() -> None:
    """The progress callback must fire at least once during a wait long enough to need one."""
    progress_calls: list[float] = []
    with LoopbackPort() as unserved:
        lore_deploy._wait_for_bind(
            unserved.host, unserved.port, "/mcp",
            timeout_s=0.5, poll_interval_s=0.05, progress_interval_s=0.1,
            on_progress=progress_calls.append,
        )
    assert len(progress_calls) >= 1
