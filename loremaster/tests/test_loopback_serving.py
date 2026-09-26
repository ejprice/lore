"""Contract (finding #466) — ONE race-free loopback listener + a server-start that NAMES its failure.

Session ``297217bd`` (lead-63c-2), tdd-light. Author: ``contract-466`` (contract author — TESTS ONLY;
the helper module does not exist when this file is written).

WHAT #466 ACTUALLY IS (premise corrected by Phase-0 read, finding #466 annotation 2026-09-26)
------------------------------------------------------------------------------------------------
No test binds a FIXED port. Four hand-rolled copies of one policy (``test_migration_wire._free_port``,
lore-deploy ``test_port_probe._free_port`` / ``test_workspace_probe``'s stub + ``_dead_port``,
``scripts/fastmcp_migration_spike._free_port``) bind ``127.0.0.1:0``, read the port, CLOSE the socket,
then hand the NUMBER to a server that binds it again. Between the close and the rebind any other process
on the box — a second pytest session is the measured case — may take the port. And uvicorn 0.48.0 runs
the lifespan startup BEFORE ``create_server``, so a rebind ``EADDRINUSE`` (``sys.exit(1)`` inside the
server thread) and a slow heavy build both surface as the same ``RuntimeError("uvicorn did not report
started within 15s")``: the failure cannot say which it was.

THE CONTRACT (the names below ARE the interface; the module is ``loremaster.testing.loopback``)
------------------------------------------------------------------------------------------------
* ``LoopbackPort(host=LOOPBACK_HOST)`` — a context manager holding a socket ALREADY BOUND to
  ``host:0`` and KEPT OPEN for the whole context. ``.host`` / ``.port`` / ``.socket`` / ``.base_url``.
  Bound-but-NOT-listening by default, so a connect is REFUSED (the race-free ``_dead_port``: the port is
  unserved AND nobody else can take it). ``.listen()`` makes it accept. Exit closes it.
* ``serve_asgi(app, *, port=None, startup_timeout_s=DEFAULT_STARTUP_TIMEOUT_S)`` — runs ``app`` under a
  REAL uvicorn in a thread, FROM the pre-bound socket (uvicorn ``sockets=``), lifespan FORCED on. Yields a
  served endpoint (``.host`` / ``.port`` / ``.base_url``). Exit drives a real shutdown.
* ``serve_http(handler_class, *, port=None)`` — the same for a stdlib ``http.server`` handler.
* ``ServerStartError(RuntimeError)`` with three DISTINCT leaves, one per cause:
  ``ServerBindError`` (the bind itself failed; the ``OSError`` chained as ``__cause__``) ·
  ``ServerStartupTimeout`` (the server thread is alive but never reported started in the budget;
  carries ``.host`` / ``.port`` / ``.startup_timeout_s``) · ``ServerThreadCrashed`` (the server thread
  ended before reporting started — a raising lifespan, a ``lifespan.startup.failed``, an app with no
  lifespan; carries ``.host`` / ``.port`` and the app's own error text in its message).

HOW EACH CAUSE IS CONSTRUCTED (every one probed on this box 2026-09-26, Linux 6.18, before writing):
* bind — ``192.0.2.1`` is RFC 5737 TEST-NET-1 (documentation-only, never a local address): ``bind`` →
  ``EADDRNOTAVAIL`` (errno 99). Binding ``:0`` on loopback cannot otherwise be made to fail on demand.
* timeout — a lifespan that blocks on an ``Event`` the test only releases in teardown.
* crash — a lifespan that RAISES (plain ASGI), a real Starlette lifespan that raises (fastmcp's app IS a
  Starlette app — the production door), and an app that cannot speak lifespan at all (packet-59 FG1).

⚠ Present-tense dating: "the helper does not exist" / "RED" is dated to HEAD ``1206233``. A reader
retrieving this after the build must re-derive.

DELTA d1 (author ``contract-466-d1``; the Phase-5 audit's findings, REPORT-refactor-466.md §1/§2)
------------------------------------------------------------------------------------------------
* **F1** — an UNEXPECTED ``BaseException`` in the startup wait (KeyboardInterrupt, a pytest-timeout
  signal-method exception) propagates UNCHANGED, and the abandoned start leaves nothing behind: no
  logging handler attached anywhere, and no server thread left serving the held socket. Injected
  receiver-blind — a ``SIGALRM`` handler raising in the main thread mid-wait, the exact door
  pytest-timeout's signal method uses — so the pin does not depend on HOW the helper waits.
* **F2** — a lifespan SHUTDOWN that overruns its budget is LOUD (trust doctrine): a clean ``with`` exit
  raises ``ServerShutdownTimeout`` naming ``host:port`` (budget: ``serve_asgi(shutdown_timeout_s=…)``,
  default ``DEFAULT_SHUTDOWN_TIMEOUT_S``); a body ALREADY raising keeps its own exception (never masked)
  and carries the overrun as a PEP 678 note naming ``host:port``.
* **C2** — the bind spy's premise (asyncio binds through the Python ``socket.socket.bind``) is PINNED,
  not assumed: uvloop is absent and the served app runs on a stdlib asyncio loop.
RED dating for d1: every d1 pin is dated to ``43b8d16`` (== ``e6e17d8`` for the helper); see
REPORT-contract-466-d1.md for the declared RED set and its reasons.
"""

from __future__ import annotations

import _socket
import asyncio
import contextlib
import errno
import http.server
import importlib.util
import inspect
import logging
import signal
import socket
import threading
import time
import typing
from collections.abc import AsyncIterator, Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import loremaster.testing.loopback as loopback_module
import pytest
from loremaster.testing.loopback import (
    DEFAULT_SHUTDOWN_TIMEOUT_S,
    DEFAULT_STARTUP_TIMEOUT_S,
    LOOPBACK_HOST,
    LoopbackPort,
    ServedEndpoint,
    ServerBindError,
    ServerShutdownTimeout,
    ServerStartError,
    ServerStartupTimeout,
    ServerThreadCrashed,
    serve_asgi,
    serve_http,
)

# RFC 5737 TEST-NET-1: reserved for documentation, never assigned to a local interface, so ``bind``
# fails with EADDRNOTAVAIL (probed: errno 99 "Cannot assign requested address", 2026-09-26).
UNASSIGNABLE_HOST = "192.0.2.1"
# The kernel's ephemeral range — the SAME source of truth the kernel uses to pick a ``:0`` port.
_EPHEMERAL_RANGE_FILE = Path("/proc/sys/net/ipv4/ip_local_port_range")
# A distinctive cause string a crashing lifespan raises; the named error must carry it verbatim.
CRASH_SENTINEL = "store unreachable: wire-lifespan-crash-sentinel-466"
# A crash must be NAMED as soon as the thread dies — far below the startup budget it is given. A build
# that only notices a crash when the timeout expires would take CRASH_TEST_STARTUP_BUDGET_S here.
CRASH_TEST_STARTUP_BUDGET_S = 60.0
CRASH_DETECTION_BOUND_S = 5.0
# The timeout leg: a deliberately short budget, and how long the helper may take BEYOND it to give up
# on a stuck thread (it must not block for the old code's 20 s join before raising).
SHORT_STARTUP_BUDGET_S = 1.0
TIMEOUT_GIVE_UP_GRACE_S = 10.0
# A slow-but-within-budget startup (the timeout's positive control).
SLOW_STARTUP_S = 0.5
GENEROUS_STARTUP_BUDGET_S = 10.0
# Repo law (CLAUDE.md "concurrency DEGREE (≥8-way, never 2-way)").
CONCURRENT_SERVERS = 8
CONCURRENT_PORTS = 16
# How long a released port may take to start refusing (a closed listening socket refuses at once).
RELEASE_BOUND_S = 2.0
HTTP_TIMEOUT_S = 5.0
HTTP_OK = 200
# d1/F1: when the injected interrupt lands — well after the server thread started (startup takes ms) and
# well inside the startup budget (CRASH_TEST_STARTUP_BUDGET_S), so it can only land IN the wait.
INTERRUPT_AFTER_S = 0.3
# d1/F1: how long an abandoned server thread may take to END once its blocked lifespan is released.
THREAD_END_BOUND_S = 5.0
# d1/F2: a deliberately short shutdown budget, and how long beyond it the helper may take to give up.
# SHORT + GRACE must stay BELOW DEFAULT_SHUTDOWN_TIMEOUT_S, or a build that ignores the passed budget and
# joins for the default passes the elapsed bound (pinned in the test, not left to arithmetic luck).
SHORT_SHUTDOWN_BUDGET_S = 0.5
SHUTDOWN_GIVE_UP_GRACE_S = 2.0
# d1/F2 positive control: a slow-but-within-budget shutdown must NOT raise.
SLOW_SHUTDOWN_S = 0.3
# A shutdown budget far above any in-budget teardown (and above INTERRUPT_AFTER_S, asserted where it
# matters) — its OWN constant, so retuning a startup budget never silently retunes a shutdown control
# (close-466 T2; this control used GENEROUS_STARTUP_BUDGET_S before).
GENEROUS_SHUTDOWN_BUDGET_S = 10.0
# d1/F2: the sentinel a failing ``with`` body raises — it must survive the overrun unmasked.
BODY_FAILURE_SENTINEL = "the test's own assertion failed — d1-body-sentinel-466"
# d1/ruling (d): how long a STUCK serve_http request handler blocks before giving up on its own. Far above
# DEFAULT_SHUTDOWN_TIMEOUT_S + SHUTDOWN_GIVE_UP_GRACE_S (asserted in the test), so a build whose exit waits
# for the handler instead of the budget is caught by elapsed time — and bounded, so that wrong build makes
# the test RED rather than hanging the session.
STUCK_HANDLER_BOUND_S = 30.0
# d1/ruling (d): a complete request, so BaseHTTPRequestHandler reaches do_GET (where the handler sticks).
STUCK_HANDLER_REQUEST = b"GET / HTTP/1.0\r\n\r\n"
# d1/ruling (d): serve_http's exit window with a stuck handler under the PASSED short budget — not early
# (the budget was given), not stuck (the handler was not waited for). SHORT + GRACE stays below the default
# (asserted in the test), so a build that ignores serve_http's ``shutdown_timeout_s`` is caught.
_STUCK_EXIT_WINDOW_LOW_S = SHORT_SHUTDOWN_BUDGET_S * 0.9
_STUCK_EXIT_WINDOW_HIGH_S = SHORT_SHUTDOWN_BUDGET_S + SHUTDOWN_GIVE_UP_GRACE_S


# --------------------------------------------------------------------------------------------- #
# Raw-socket probes. ``_attempt_raw_bind`` is the ONE raw bind in this file: the guard
# (test_no_raw_listener_in_test_trees.py) exempts exactly this (file, function) site, because the
# helper's own contract must build a squatter to prove the port is HELD.
# --------------------------------------------------------------------------------------------- #
def _attempt_raw_bind(host: str, port: int) -> int | None:
    """Try to bind ``host:port`` on a fresh socket; return the errno on failure, ``None`` on success."""
    squatter = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        squatter.bind((host, port))
    except OSError as bind_error:
        return bind_error.errno
    finally:
        squatter.close()
    return None


def _connect_is_refused(host: str, port: int) -> bool:
    """True iff a TCP connect to ``host:port`` is actively REFUSED (not accepted, not timed out)."""
    try:
        connection = socket.create_connection((host, port), timeout=RELEASE_BOUND_S)
    except ConnectionRefusedError:
        return True
    connection.close()
    return False


def _becomes_refused(host: str, port: int) -> bool:
    """Poll until ``host:port`` refuses, within :data:`RELEASE_BOUND_S`."""
    deadline = time.monotonic() + RELEASE_BOUND_S
    while time.monotonic() < deadline:
        if _connect_is_refused(host, port):
            return True
        time.sleep(0.05)
    return False


def _is_released(host: str, port: int) -> bool:
    """True iff ``host:port`` can be bound again — the held socket is CLOSED, not merely un-listened.

    Used only where the server never listened (startup timeout / crash): there a leaked-but-unlistened
    socket REFUSES connects exactly like a released one, so "refused" cannot tell them apart (a
    wrong build that leaks the socket on timeout passed a refusal check — contract-466 wrong build
    ``w6``). Not used after a real serve: server-side TIME_WAIT can legitimately block a rebind there.
    """
    return _attempt_raw_bind(host, port) is None


def _get(base_url: str) -> httpx.Response:
    """A plain GET that ignores any proxy env (``trust_env=False``) — the loopback is the target."""
    with httpx.Client(trust_env=False, timeout=HTTP_TIMEOUT_S) as client:
        return client.get(f"{base_url}/")


@contextlib.contextmanager
def _spy_on_every_bind(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[Any]]:
    """Record the address of EVERY ``socket.socket.bind`` in this process while the block runs.

    Receiver-blind: it sees a bind from the helper, from asyncio's ``create_server`` (host/port mode)
    and from ``socketserver`` alike — so "no specific-port bind happened" is an OUTCOME over every
    caller, not a claim about one code path. uvloop is NOT installed in this venv (probed 2026-09-26),
    so asyncio binds go through the Python method this spy replaces.
    """
    addresses: list[Any] = []

    def _recording_bind(self: socket.socket, address: Any) -> None:
        addresses.append(address)
        _socket.socket.bind(self, address)

    monkeypatch.setattr(socket.socket, "bind", _recording_bind)
    yield addresses


def _ephemeral_range() -> tuple[int, int]:
    low, high = _EPHEMERAL_RANGE_FILE.read_text(encoding="utf-8").split()
    return int(low), int(high)


# --------------------------------------------------------------------------------------------- #
# ASGI fixtures — tiny, but served by the REAL uvicorn over a REAL TCP socket.
# --------------------------------------------------------------------------------------------- #
class _RecordingApp:
    """A lifespan-speaking ASGI app that answers every HTTP request with its own ``identity``.

    ``startup_gate`` (optional) blocks lifespan startup until set — the never-completes fixture.
    ``startup_delay_s`` delays startup completion — the slow-but-in-budget fixture.
    ``events`` records ``startup`` / ``shutdown`` so a test can prove teardown ran.
    (d1) ``shutdown_gate`` / ``shutdown_delay_s`` are the same two shapes for lifespan SHUTDOWN — the
    hanging-teardown fixture (a store/watcher close that never returns) and its in-budget control.
    (d1) ``loop_classes`` records the event-loop class every HTTP request was served on (C2's premise).
    Every d1 addition defaults to "absent", so the fixtures the original pins build are unchanged.
    """

    def __init__(
        self,
        identity: str,
        *,
        startup_delay_s: float = 0.0,
        startup_gate: threading.Event | None = None,
        shutdown_delay_s: float = 0.0,
        shutdown_gate: threading.Event | None = None,
    ) -> None:
        self.identity = identity
        self.startup_delay_s = startup_delay_s
        self.startup_gate = startup_gate
        self.shutdown_delay_s = shutdown_delay_s
        self.shutdown_gate = shutdown_gate
        self.events: list[str] = []
        self.loop_classes: list[type] = []

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    if self.startup_gate is not None:
                        while not self.startup_gate.is_set():
                            await asyncio.sleep(0.05)
                    if self.startup_delay_s:
                        await asyncio.sleep(self.startup_delay_s)
                    self.events.append("startup")
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    if self.shutdown_gate is not None:
                        while not self.shutdown_gate.is_set():
                            await asyncio.sleep(0.05)
                    if self.shutdown_delay_s:
                        await asyncio.sleep(self.shutdown_delay_s)
                    self.events.append("shutdown")
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        elif scope["type"] == "http":
            self.loop_classes.append(type(asyncio.get_running_loop()))
            body = self.identity.encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": HTTP_OK,
                    "headers": [
                        (b"content-type", b"text/plain"),
                        (b"content-length", str(len(body)).encode("ascii")),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})


async def _raising_lifespan_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
    """Plain-ASGI app whose lifespan startup RAISES — the heavy build failing (store down)."""
    if scope["type"] == "lifespan":
        message = await receive()
        assert message["type"] == "lifespan.startup"
        raise RuntimeError(CRASH_SENTINEL)


async def _http_only_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
    """An app that cannot speak lifespan at all — packet-59 FG1: with lifespan FORCED on this must fail
    LOUDLY, never be served with its startup silently skipped."""
    if scope["type"] != "http":
        raise RuntimeError(f"no lifespan support ({CRASH_SENTINEL})")


def _starlette_app_with_failing_lifespan() -> Any:
    """A REAL Starlette app whose lifespan raises — fastmcp's ``http_app`` is a Starlette app, so this is
    the production door: Starlette sends ``lifespan.startup.failed`` (traceback text) AND re-raises."""
    from starlette.applications import Starlette  # noqa: PLC0415

    @contextlib.asynccontextmanager
    async def _failing_lifespan(_app: Any) -> AsyncIterator[None]:
        if _app is not None:  # always true — keeps the ``yield`` below reachable for mypy
            raise RuntimeError(CRASH_SENTINEL)
        yield

    return Starlette(routes=[], lifespan=_failing_lifespan)


# ============================================================================================= #
# A — the listener: bound to :0, KEPT OPEN, never a close→rebind.
# ============================================================================================= #
class TestLoopbackPortHoldsItsPort:
    """``LoopbackPort`` hands out a kernel-assigned port and HOLDS it for the whole context — the
    property whose absence is #466 (bind :0 → close → someone else takes it → rebind fails)."""

    def test_the_port_is_a_kernel_assigned_ephemeral_port(self) -> None:
        # Magnitude/sanity: a real ``:0`` bind lands in the kernel's ephemeral range. A build that hands
        # back a hardcoded/config port (9233) or 0 fails here.
        with LoopbackPort() as held:
            assert held.host == LOOPBACK_HOST
            assert isinstance(held.port, int)
            if _EPHEMERAL_RANGE_FILE.exists():
                low, high = _ephemeral_range()
                assert low <= held.port <= high, (
                    f"port {held.port} is outside the kernel ephemeral range [{low}, {high}] — it was "
                    "not assigned by a :0 bind"
                )
            else:  # pragma: no cover — non-Linux
                assert held.port > 0

    def test_the_port_stays_held_while_the_context_is_open(self) -> None:
        # THE #466 PROPERTY. A squatter binding the same port must be refused for as long as the context
        # is open; a build that closes after reading the port (the four retired copies) lets it through.
        with LoopbackPort() as held:
            squatter_errno = _attempt_raw_bind(held.host, held.port)
            assert squatter_errno == errno.EADDRINUSE, (
                f"another socket could bind {held.host}:{held.port} while the LoopbackPort was open "
                f"(errno {squatter_errno}) — the port is NOT held; the close→rebind race is still open"
            )
            assert held.socket.fileno() != -1, "the held socket was closed inside its own context"
            assert held.socket.getsockname()[1] == held.port

    def test_an_unlistened_port_refuses_connections_fast(self) -> None:
        # The race-free ``_dead_port``: bound (so nobody else can serve it) but not listening (so a
        # connect is REFUSED, not queued). A build that listens by default would ACCEPT here.
        with LoopbackPort() as held:
            started = time.monotonic()
            assert _connect_is_refused(held.host, held.port), (
                "a connect to a fresh (un-listened) LoopbackPort was not refused — it must model an "
                "unserved endpoint until .listen() or a server takes it"
            )
            assert time.monotonic() - started < RELEASE_BOUND_S  # refused, not a timeout

    def test_listen_makes_the_port_accept_connections(self) -> None:
        # Positive control for the refusal above: the SAME port accepts once listened.
        with LoopbackPort() as held:
            held.listen()
            assert not _connect_is_refused(held.host, held.port), (
                ".listen() did not make the held port accept connections"
            )

    def test_exit_closes_the_socket_and_releases_the_port(self) -> None:
        # Lifecycle: the resource dies with its context — no leaked fd, no port held past the test.
        with LoopbackPort() as held:
            held.listen()
            port = held.port
            sock = held.socket
        assert sock.fileno() == -1, "the LoopbackPort socket survived its context (leaked fd)"
        assert _becomes_refused(LOOPBACK_HOST, port), f"port {port} still accepts after exit"

    def test_base_url_names_the_host_and_the_held_port(self) -> None:
        # The wire harness builds every request URL from this; a mismatch is a silent mis-target.
        with LoopbackPort() as held:
            assert held.base_url == f"http://{LOOPBACK_HOST}:{held.port}"

    def test_concurrently_held_ports_are_pairwise_distinct(self) -> None:
        # ≥8-way (repo law): distinctness is what the kernel guarantees ONLY while every socket is held.
        barrier = threading.Barrier(CONCURRENT_PORTS)

        def _hold_and_report() -> int:
            with LoopbackPort() as held:
                barrier.wait(timeout=HTTP_TIMEOUT_S)  # all held at the same instant
                port: int = held.port
                barrier.wait(timeout=HTTP_TIMEOUT_S)
                return port

        with ThreadPoolExecutor(max_workers=CONCURRENT_PORTS) as pool:
            ports = list(pool.map(lambda _index: _hold_and_report(), range(CONCURRENT_PORTS)))
        assert len(set(ports)) == CONCURRENT_PORTS, f"concurrently held ports collided: {sorted(ports)}"

    def test_it_never_binds_a_specific_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # The OUTCOME form of "no close→rebind window": every bind in the process targets port 0. A
        # build that picks a number and binds it again (any spelling) records a non-zero bind here.
        with _spy_on_every_bind(monkeypatch) as addresses, LoopbackPort() as held:
            held.listen()
        assert addresses, "no bind was observed — the spy saw nothing, so it certifies nothing"
        specific = [address for address in addresses if address[1] != 0]
        assert specific == [], f"a bind to a SPECIFIC port happened (the rebind window): {specific}"


class TestBindFailureIsNamed:
    """Cause 1 of 3 — the bind itself failed. Named as ``ServerBindError``, with the address and the OS
    error, never folded into a generic ``RuntimeError``."""

    def test_an_unassignable_host_raises_server_bind_error_naming_the_host(self) -> None:
        with pytest.raises(ServerBindError) as excinfo, LoopbackPort(host=UNASSIGNABLE_HOST):
            pytest.fail("entered a LoopbackPort bound to a non-local address")
        error = excinfo.value
        assert type(error) is ServerBindError
        assert UNASSIGNABLE_HOST in str(error), f"the bind error does not name the address: {error}"
        assert "bind" in str(error).lower(), f"the bind error does not say it was a bind: {error}"
        cause = error.__cause__
        assert isinstance(cause, OSError), f"the OS error is not chained as __cause__: {cause!r}"
        assert cause.errno == errno.EADDRNOTAVAIL

    def test_positive_control_the_loopback_host_binds(self) -> None:
        # Without this, "raises on 192.0.2.1" could be a helper that raises on EVERY host.
        with LoopbackPort(host=LOOPBACK_HOST) as held:
            assert held.port > 0


# ============================================================================================= #
# B — serve FROM the held socket; every start failure names its cause.
# ============================================================================================= #
class TestServeAsgiServesFromThePreBoundSocket:
    """``serve_asgi`` runs a REAL uvicorn on the held socket — the same socket, still open, no rebind."""

    def test_a_healthy_app_serves_a_request_at_base_url(self) -> None:
        app = _RecordingApp("healthy-466")
        with serve_asgi(app) as served:
            response = _get(served.base_url)
        assert response.status_code == HTTP_OK
        assert response.text == "healthy-466"
        assert served.base_url == f"http://{served.host}:{served.port}"
        assert served.host == LOOPBACK_HOST

    def test_a_passed_port_is_the_one_served_and_stays_open_while_serving(self) -> None:
        # The seam: the served port IS the held socket's port, and that socket is still open (a build
        # that reads held.port, closes, and hands the number to uvicorn fails the fileno leg).
        app = _RecordingApp("passed-port-466")
        with LoopbackPort() as held, serve_asgi(app, port=held) as served:
            assert served.port == held.port
            assert held.socket.fileno() != -1, "the held socket was closed so uvicorn could rebind it"
            assert _get(served.base_url).text == "passed-port-466"

    def test_no_bind_to_a_specific_port_happens_during_the_whole_serve(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Quantified over EVERY bind in the process (uvicorn's own create_server included): a build that
        # passes ``port=<number>`` to uvicorn.Config makes asyncio bind that number → recorded here.
        app = _RecordingApp("spied-466")
        with _spy_on_every_bind(monkeypatch) as addresses, serve_asgi(app) as served:
            assert _get(served.base_url).status_code == HTTP_OK
        assert addresses, "no bind observed during serve_asgi — the spy certifies nothing"
        assert [address for address in addresses if address[1] != 0] == [], (
            f"serve_asgi bound a SPECIFIC port (the close→rebind window #466 names): {addresses}"
        )

    def test_exit_drives_a_real_lifespan_shutdown(self) -> None:
        # Teardown runs (the wire harness depends on lifespan teardown closing the store/watchers).
        app = _RecordingApp("shutdown-466")
        with serve_asgi(app):
            assert app.events == ["startup"]
        assert app.events == ["startup", "shutdown"], f"lifespan shutdown did not run: {app.events}"

    def test_exit_releases_the_port(self) -> None:
        app = _RecordingApp("release-466")
        with serve_asgi(app) as served:
            port = served.port
        assert _becomes_refused(LOOPBACK_HOST, port), f"port {port} still accepts after serve_asgi exit"

    def test_a_slow_but_in_budget_startup_is_served_not_timed_out(self) -> None:
        # Positive control for the timeout leg: a startup inside the budget must NOT raise.
        app = _RecordingApp("slow-466", startup_delay_s=SLOW_STARTUP_S)
        with serve_asgi(app, startup_timeout_s=GENEROUS_STARTUP_BUDGET_S) as served:
            assert _get(served.base_url).text == "slow-466"

    def test_concurrent_servers_each_serve_their_own_identity(self) -> None:
        # ≥8-way in ONE process: every server answers on its own port with its own identity — no
        # cross-wiring, no collision, all up at the same instant.
        barrier = threading.Barrier(CONCURRENT_SERVERS)

        def _serve_and_fetch(index: int) -> tuple[int, str, str]:
            identity = f"server-{index}-466"
            with serve_asgi(_RecordingApp(identity)) as served:
                barrier.wait(timeout=GENEROUS_STARTUP_BUDGET_S)
                body = _get(served.base_url).text
                barrier.wait(timeout=GENEROUS_STARTUP_BUDGET_S)
                return served.port, identity, body

        with ThreadPoolExecutor(max_workers=CONCURRENT_SERVERS) as pool:
            results = list(pool.map(_serve_and_fetch, range(CONCURRENT_SERVERS)))
        assert len({port for port, _identity, _body in results}) == CONCURRENT_SERVERS
        mismatched = [(identity, body) for _port, identity, body in results if identity != body]
        assert mismatched == [], f"a server answered with another server's identity: {mismatched}"


class TestStartupFailureNamesItsCause:
    """Cause 2 (timeout) and cause 3 (thread crash) — each its own leaf, each carrying what happened,
    and a crash named PROMPTLY (on thread death), not when the budget runs out."""

    def test_the_three_causes_are_distinct_leaves_of_server_start_error(self) -> None:
        leaves = (ServerBindError, ServerStartupTimeout, ServerThreadCrashed)
        assert issubclass(ServerStartError, RuntimeError)
        for leaf in leaves:
            assert issubclass(leaf, ServerStartError)
            others = [other for other in leaves if other is not leaf]
            assert not any(issubclass(leaf, other) for other in others), (
                f"{leaf.__name__} subclasses another cause — an `except` for one would catch the other"
            )

    def test_a_lifespan_that_never_completes_raises_startup_timeout(self) -> None:
        gate = threading.Event()
        app = _RecordingApp("never-466", startup_gate=gate)
        started = time.monotonic()
        try:
            with pytest.raises(ServerStartupTimeout) as excinfo:
                with serve_asgi(app, startup_timeout_s=SHORT_STARTUP_BUDGET_S):
                    pytest.fail("a server whose lifespan never completed was reported started")
            elapsed = time.monotonic() - started
            error = excinfo.value
            assert type(error) is ServerStartupTimeout
            # Not early (it waited the budget) and not stuck (it did not join the stuck thread for ~20 s).
            assert SHORT_STARTUP_BUDGET_S * 0.9 <= elapsed <= SHORT_STARTUP_BUDGET_S + TIMEOUT_GIVE_UP_GRACE_S
            message = str(error)
            assert f"{error.host}:{error.port}" in message, (
                f"the timeout does not name the address: {message}"
            )
            assert "timed out" in message.lower() or "timeout" in message.lower(), message
            # The budget that expired travels as data (here the test's own short budget; the DEFAULT's value
            # is operator-ruled since 2026-09-26, lore #503 — no longer measure-then-tune).
            assert error.startup_timeout_s == SHORT_STARTUP_BUDGET_S
            # Lifecycle: the held socket is released at the raise, not whenever the stuck thread ends.
            assert _is_released(error.host, error.port), (
                f"{error.host}:{error.port} is still HELD after the startup timeout — the socket leaked"
            )
        finally:
            gate.set()  # let the stuck lifespan finish so the daemon thread can end

    def test_a_raising_lifespan_is_a_thread_crash_named_promptly_with_its_cause(self) -> None:
        started = time.monotonic()
        with pytest.raises(ServerThreadCrashed) as excinfo:
            with serve_asgi(_raising_lifespan_app, startup_timeout_s=CRASH_TEST_STARTUP_BUDGET_S):
                pytest.fail("a server whose lifespan raised was reported started")
        elapsed = time.monotonic() - started
        error = excinfo.value
        assert type(error) is ServerThreadCrashed
        assert elapsed < CRASH_DETECTION_BOUND_S, (
            f"the crash was named after {elapsed:.1f}s — it must be detected on thread death, not by "
            f"waiting out the {CRASH_TEST_STARTUP_BUDGET_S}s budget"
        )
        assert CRASH_SENTINEL in str(error), f"the crash does not carry the lifespan's own error: {error}"
        assert f"{error.host}:{error.port}" in str(error)
        assert _is_released(error.host, error.port), "the port is still HELD after the crash (socket leaked)"

    def test_a_starlette_lifespan_failure_is_a_thread_crash_with_its_cause(self) -> None:
        # The PRODUCTION door (fastmcp's app is Starlette): startup.failed + re-raise, not a bare raise.
        started = time.monotonic()
        with pytest.raises(ServerThreadCrashed) as excinfo:
            with serve_asgi(
                _starlette_app_with_failing_lifespan(), startup_timeout_s=CRASH_TEST_STARTUP_BUDGET_S
            ):
                pytest.fail("a Starlette app whose lifespan raised was reported started")
        assert time.monotonic() - started < CRASH_DETECTION_BOUND_S
        assert CRASH_SENTINEL in str(excinfo.value), f"cause lost: {excinfo.value}"

    def test_an_app_that_cannot_speak_lifespan_fails_loudly(self) -> None:
        # Packet-59 FG1: lifespan is FORCED on, so an app without lifespan support is a crash — never a
        # server that comes up with its startup silently skipped (what lifespan="auto" would do).
        started = time.monotonic()
        with pytest.raises(ServerThreadCrashed):
            with serve_asgi(_http_only_app, startup_timeout_s=CRASH_TEST_STARTUP_BUDGET_S):
                pytest.fail("an app with no lifespan support was served — FG1's loud-failure guard is gone")
        assert time.monotonic() - started < CRASH_DETECTION_BOUND_S

    def test_the_default_budget_is_a_positive_finite_number(self) -> None:
        # Existence + sanity only here. The VALUE is operator-ruled (2026-09-26, lore #503) and pinned exactly
        # by test_migration_wire_budget_503 (…the_default_startup_budget_stays_at_the_ruled_value); it was
        # measure-then-tune (#466 contract report, §E) before that ruling.
        assert isinstance(DEFAULT_STARTUP_TIMEOUT_S, float | int)
        assert 0 < DEFAULT_STARTUP_TIMEOUT_S < float("inf")


# ============================================================================================= #
# A (stdlib half) — serve_http from the held socket (the lore-deploy stub servers).
# ============================================================================================= #
class _StubHandler(http.server.BaseHTTPRequestHandler):
    """Answers any GET/POST with a fixed JSON-RPC body — the lore-deploy stub-MCP shape."""

    body = b'{"jsonrpc": "2.0", "id": 0, "result": {}}'

    def _answer(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        if length:
            self.rfile.read(length)
        self.send_response(HTTP_OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(self.body)))
        self.end_headers()
        self.wfile.write(self.body)

    def do_GET(self) -> None:  # noqa: N802 — stdlib override name
        self._answer()

    def do_POST(self) -> None:  # noqa: N802 — stdlib override name
        self._answer()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 — stdlib signature
        return


class TestServeHttp:
    """``serve_http`` serves a stdlib handler from the held socket — same no-rebind property."""

    def test_serves_the_handler_at_base_url(self) -> None:
        with serve_http(_StubHandler) as served:
            response = _get(served.base_url)
        assert response.status_code == HTTP_OK
        assert response.content == _StubHandler.body
        assert served.base_url == f"http://{LOOPBACK_HOST}:{served.port}"

    def test_a_held_port_refuses_until_served_then_accepts(self) -> None:
        # The lore-deploy "listener appears mid-wait" shape, race-free: the port is HELD (refusing) the
        # whole time, then served on the SAME socket — no window where a stranger can take it.
        with LoopbackPort() as held:
            assert _connect_is_refused(held.host, held.port)
            with serve_http(_StubHandler, port=held) as served:
                assert served.port == held.port
                assert _get(served.base_url).status_code == HTTP_OK

    def test_exit_releases_the_port(self) -> None:
        with serve_http(_StubHandler) as served:
            port = served.port
        assert _becomes_refused(LOOPBACK_HOST, port), f"port {port} still accepts after serve_http exit"

    def test_no_bind_to_a_specific_port_happens(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # ``http.server.HTTPServer((host, port), ...)`` binds the number (bind_and_activate=True): the
        # retired lore-deploy shape. Serving from the held socket binds only :0.
        with _spy_on_every_bind(monkeypatch) as addresses, serve_http(_StubHandler) as served:
            assert _get(served.base_url).status_code == HTTP_OK
        assert addresses, "no bind observed during serve_http — the spy certifies nothing"
        assert [address for address in addresses if address[1] != 0] == [], addresses


# ============================================================================================= #
# DELTA d1 — probes. Each is receiver-blind: it observes an OUTCOME over the whole process, never
# a named attribute of the helper, so the pins survive any correct restructuring of the helper.
# ============================================================================================= #
class _InjectedInterrupt(BaseException):
    """An exception that is NOT an ``Exception`` — the shape of pytest-timeout's signal-method failure
    (``pytest.fail`` → ``Failed``, a ``BaseException``) and of ``KeyboardInterrupt``. A cleanup written
    as ``except Exception`` does not see it; that is the wrong build this type exists to catch."""


class _BodyFailure(Exception):
    """A test body's own failure raised inside ``serve_asgi`` — F2's must-not-be-masked exception."""


@contextlib.contextmanager
def _interrupt_main_thread_after(
    delay_s: float, make_error: type[BaseException]
) -> Iterator[list[BaseException]]:
    """Raise ``make_error()`` in the MAIN thread ``delay_s`` from now, from a ``SIGALRM`` handler.

    This is the real door F1 names: pytest-timeout's signal method and Ctrl-C both raise from a signal
    handler at whatever bytecode the main thread is executing — here, the helper's startup wait,
    whatever primitive that wait uses (a join, an ``Event.wait``, a ``sleep``: all are interruptible on
    POSIX). Yields the list the raised instance is recorded in, so the caller can prove it FIRED and
    that the propagated exception is that very object. The timer and the previous handler are restored
    however the block ends.
    """
    with _main_thread_interrupt(make_error) as (raised, arm):
        arm(delay_s)
        yield raised


@contextlib.contextmanager
def _main_thread_interrupt(
    make_error: type[BaseException],
) -> Iterator[tuple[list[BaseException], Callable[[float], None]]]:
    """Install a ``SIGALRM`` handler raising ``make_error()`` in the MAIN thread, NOT yet scheduled.

    Yields ``(raised, arm)``: ``arm(delay_s)`` schedules the one interrupt ``delay_s`` from THAT call, so a
    caller can aim it at a later phase of the helper (the teardown join, close-466 R1) rather than at the
    moment the block opens. The timer and the previous handler are restored however the block ends.
    """
    assert threading.current_thread() is threading.main_thread(), (
        "signal injection needs the MAIN thread (signal.signal raises elsewhere) — the probe cannot run "
        "here, so the pin would certify nothing"
    )
    raised: list[BaseException] = []

    def _raise(_signum: int, _frame: object) -> None:
        error = make_error()
        raised.append(error)
        raise error

    def _arm(delay_s: float) -> None:
        signal.setitimer(signal.ITIMER_REAL, delay_s)

    previous = signal.signal(signal.SIGALRM, _raise)
    try:
        yield raised, _arm
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _attached_logging_handlers() -> dict[str, tuple[logging.Handler, ...]]:
    """Every logger in the process that has handlers → those handlers (root included).

    Receiver-blind: a helper that leaks a handler onto ANY logger (``uvicorn.error`` today, whatever it
    uses tomorrow) changes this snapshot.
    """
    loggers: dict[str, logging.Logger] = {"<root>": logging.getLogger()}
    for name, candidate in list(logging.Logger.manager.loggerDict.items()):
        if isinstance(candidate, logging.Logger):
            loggers[name] = candidate
    return {name: tuple(logger.handlers) for name, logger in loggers.items() if logger.handlers}


def _threads_still_alive_after(started_before: set[threading.Thread], bound_s: float) -> list[str]:
    """Poll up to ``bound_s`` for every thread NOT in ``started_before`` to end; return the survivors'
    names (empty = every thread the block started has ended). Receiver-blind: it needs no handle on the
    helper's thread."""
    deadline = time.monotonic() + bound_s
    while True:
        survivors = [
            thread.name
            for thread in threading.enumerate()
            if thread not in started_before and thread.is_alive()
        ]
        if not survivors or time.monotonic() >= deadline:
            return survivors
        time.sleep(0.05)


# ============================================================================================= #
# d1/F1 — an unexpected BaseException in the startup wait: propagated unchanged, nothing left behind.
# ============================================================================================= #
_UNEXPECTED_INTERRUPTS = [
    pytest.param(_InjectedInterrupt, id="pytest-timeout-shaped-BaseException"),
    pytest.param(KeyboardInterrupt, id="KeyboardInterrupt"),
]


class TestAnInterruptedStartupLeavesNothingBehind:
    """F1 (REPORT-refactor-466.md §1): the helper cleans up on its two NAMED start failures; this pins
    the same outcome for ANY exception that interrupts the startup wait. The lifespan is held blocked
    (never completes) so the interrupt can only land IN the wait; it is released afterwards so an
    abandoned thread CAN end."""

    @pytest.mark.parametrize("interrupt", _UNEXPECTED_INTERRUPTS)
    def test_the_interrupt_propagates_unchanged_and_no_logging_handler_is_left_attached(
        self, interrupt: type[BaseException]
    ) -> None:
        gate = threading.Event()
        app = _RecordingApp("interrupted-466", startup_gate=gate)
        handlers_before = _attached_logging_handlers()
        threads_before = set(threading.enumerate())
        try:
            with _interrupt_main_thread_after(INTERRUPT_AFTER_S, interrupt) as raised:
                with pytest.raises(interrupt) as excinfo:
                    with serve_asgi(app, startup_timeout_s=CRASH_TEST_STARTUP_BUDGET_S):
                        pytest.fail("a server whose lifespan never completed was reported started")
            # Non-vacuity: the injection FIRED exactly once, and what came out is THAT object — not a
            # ServerStartError wrapping it, not a re-raised copy, not a later cleanup error.
            assert len(raised) == 1, f"the interrupt fired {len(raised)} times — the probe is broken"
            assert excinfo.value is raised[0], (
                f"the helper replaced the interrupt with {excinfo.value!r} — it must propagate UNCHANGED"
            )
            # The process-global logging state is exactly what it was: an abandoned start that leaves a
            # handler attached captures (and holds) every later uvicorn error in the process.
            assert _attached_logging_handlers() == handlers_before, (
                "the interrupted start left a logging handler attached — cleanup ran only on the named "
                f"failures: before={handlers_before} after={_attached_logging_handlers()}"
            )
        finally:
            gate.set()
        survivors = _threads_still_alive_after(threads_before, THREAD_END_BOUND_S)
        assert survivors == [], f"the abandoned server thread(s) never ended: {survivors}"

    @pytest.mark.parametrize("interrupt", _UNEXPECTED_INTERRUPTS)
    def test_a_passed_port_is_not_served_after_the_interrupted_start(
        self, interrupt: type[BaseException]
    ) -> None:
        # The sharp form of F1: the CALLER still holds the port, so nothing else closes the socket. A
        # build that does not abandon the start leaves uvicorn running on it — once the lifespan is
        # released it SERVES the caller's socket forever from a thread nobody can stop.
        gate = threading.Event()
        app = _RecordingApp("interrupted-passed-466", startup_gate=gate)
        handlers_before = _attached_logging_handlers()
        threads_before = set(threading.enumerate())
        with LoopbackPort() as held:
            try:
                with _interrupt_main_thread_after(INTERRUPT_AFTER_S, interrupt) as raised:
                    with pytest.raises(interrupt) as excinfo:
                        with serve_asgi(app, port=held, startup_timeout_s=CRASH_TEST_STARTUP_BUDGET_S):
                            pytest.fail("a server whose lifespan never completed was reported started")
                assert len(raised) == 1 and excinfo.value is raised[0]
            finally:
                gate.set()
            survivors = _threads_still_alive_after(threads_before, THREAD_END_BOUND_S)
            assert survivors == [], (
                f"the interrupted start left server thread(s) running on the caller's held port: {survivors}"
            )
            assert _connect_is_refused(held.host, held.port), (
                f"{held.host}:{held.port} ACCEPTS connections after the interrupted start — a server came "
                "up on the caller's socket that nobody started"
            )
        assert _attached_logging_handlers() == handlers_before


# ============================================================================================= #
# d1/F2 — a lifespan shutdown that overruns its budget is LOUD, never silent, never masking.
# ============================================================================================= #
class TestAShutdownOverrunIsLoud:
    """F2 (REPORT-refactor-466.md §1, trust doctrine "failures are LOUD"): exit used to join the server
    thread for a fixed budget and return whether or not it finished — a lifespan teardown that hangs
    (the store / watcher close in the wire harness) passed as a GREEN test. The decision (d1 report §F2):
    a clean exit RAISES ``ServerShutdownTimeout``; an exit already carrying the body's exception keeps
    that exception (the test's own failure is the headline) and adds the overrun as a note."""

    def test_the_shutdown_error_is_its_own_runtime_error_not_a_start_failure(self) -> None:
        # An ``except ServerStartError`` (a start-retry) must never swallow a teardown overrun.
        assert issubclass(ServerShutdownTimeout, RuntimeError)
        assert not issubclass(ServerShutdownTimeout, ServerStartError)
        # Existence + sanity only; the shutdown VALUE is still measure-then-tune (the startup DEFAULT, by
        # contrast, is operator-ruled since 2026-09-26, lore #503).
        assert isinstance(DEFAULT_SHUTDOWN_TIMEOUT_S, float | int)
        assert 0 < DEFAULT_SHUTDOWN_TIMEOUT_S < float("inf")

    def test_a_clean_exit_whose_shutdown_hangs_raises_naming_the_address(self) -> None:
        # Fixture discrimination (arithmetic alignment, CLAUDE.md FIXTURES MUST DISCRIMINATE): the upper
        # elapsed bound must exclude a build that joins for the DEFAULT instead of the passed budget.
        assert SHORT_SHUTDOWN_BUDGET_S + SHUTDOWN_GIVE_UP_GRACE_S < DEFAULT_SHUTDOWN_TIMEOUT_S, (
            "lower SHORT_SHUTDOWN_BUDGET_S / SHUTDOWN_GIVE_UP_GRACE_S: with the default this low, a build "
            "that ignores shutdown_timeout_s is indistinguishable by elapsed time"
        )
        gate = threading.Event()
        app = _RecordingApp("hanging-teardown-466", shutdown_gate=gate)
        handlers_before = _attached_logging_handlers()
        try:
            with pytest.raises(ServerShutdownTimeout) as excinfo:
                with serve_asgi(app, shutdown_timeout_s=SHORT_SHUTDOWN_BUDGET_S) as served:
                    assert _get(served.base_url).status_code == HTTP_OK
                    exit_started = time.monotonic()
            elapsed = time.monotonic() - exit_started
            error = excinfo.value
            assert type(error) is ServerShutdownTimeout
            assert (error.host, error.port) == (served.host, served.port)
            message = str(error)
            assert f"{served.host}:{served.port}" in message, (
                f"the overrun does not name the address: {message}"
            )
            assert "shutdown" in message.lower(), f"the overrun does not say it was the shutdown: {message}"
            # The budget that expired travels as data (like ServerStartupTimeout.startup_timeout_s).
            assert error.shutdown_timeout_s == SHORT_SHUTDOWN_BUDGET_S
            # Not early (it gave the teardown its budget) and not stuck (it did not wait for the hang).
            assert (
                SHORT_SHUTDOWN_BUDGET_S * 0.9 <= elapsed <= SHORT_SHUTDOWN_BUDGET_S + SHUTDOWN_GIVE_UP_GRACE_S
            ), f"exit took {elapsed:.2f}s against a {SHORT_SHUTDOWN_BUDGET_S}s budget"
            # Lifecycle still completes around the raise: nothing left attached, the port released.
            assert _attached_logging_handlers() == handlers_before
            assert _becomes_refused(served.host, served.port), "the port still accepts after the overrun"
        finally:
            gate.set()
        # The hang WAS the teardown: once released it completes (asynchronously — the lifespan polls the
        # gate every 50 ms, so wait for it rather than read the list at the instant of release).
        deadline = time.monotonic() + THREAD_END_BOUND_S
        while app.events != ["startup", "shutdown"] and time.monotonic() < deadline:
            time.sleep(0.05)
        assert app.events == ["startup", "shutdown"], app.events

    def test_a_failing_body_keeps_its_own_exception_and_carries_the_overrun_as_a_note(self) -> None:
        # Never mask: the test's own failure is what the reader must see first. The overrun still travels
        # WITH it (PEP 678 ``add_note`` — rendered by pytest under the traceback), naming the address.
        gate = threading.Event()
        app = _RecordingApp("hanging-teardown-failing-body-466", shutdown_gate=gate)
        body_failure = _BodyFailure(BODY_FAILURE_SENTINEL)
        handlers_before = _attached_logging_handlers()
        try:
            with pytest.raises(_BodyFailure) as excinfo:
                with serve_asgi(app, shutdown_timeout_s=SHORT_SHUTDOWN_BUDGET_S) as served:
                    exit_started = time.monotonic()
                    raise body_failure
            elapsed = time.monotonic() - exit_started
            assert excinfo.value is body_failure, (
                f"the body's own exception was replaced by {excinfo.value!r} — the overrun MASKED it"
            )
            notes = "\n".join(getattr(body_failure, "__notes__", []))
            assert f"{served.host}:{served.port}" in notes and "shutdown" in notes.lower(), (
                f"the overrun is SILENT on the failing path — no note naming the address: {notes!r}"
            )
            # Both bounds (close-466 T1): a build that skips the wait on the FAILING path only (checks
            # ``is_alive()`` at once, notes, returns) was bounded only above; and the lifecycle completes on
            # this path too, not just on the clean one.
            assert (
                SHORT_SHUTDOWN_BUDGET_S * 0.9 <= elapsed <= SHORT_SHUTDOWN_BUDGET_S + SHUTDOWN_GIVE_UP_GRACE_S
            ), f"exit took {elapsed:.2f}s against a {SHORT_SHUTDOWN_BUDGET_S}s budget"
            assert _attached_logging_handlers() == handlers_before
            assert _becomes_refused(served.host, served.port), "the port still accepts after the overrun"
        finally:
            gate.set()

    def test_positive_control_a_slow_in_budget_shutdown_does_not_raise(self) -> None:
        # Without this, "raises on overrun" could be a helper that raises on EVERY exit.
        app = _RecordingApp("slow-teardown-466", shutdown_delay_s=SLOW_SHUTDOWN_S)
        with serve_asgi(app, shutdown_timeout_s=GENEROUS_SHUTDOWN_BUDGET_S) as served:
            assert _get(served.base_url).status_code == HTTP_OK
        assert app.events == ["startup", "shutdown"], app.events

    def test_positive_control_a_failing_body_with_a_prompt_shutdown_gets_no_note(self) -> None:
        # The note is evidence of an overrun, not decoration on every failure.
        body_failure = _BodyFailure(BODY_FAILURE_SENTINEL)
        with pytest.raises(_BodyFailure):
            with serve_asgi(_RecordingApp("prompt-teardown-466")):
                raise body_failure
        assert getattr(body_failure, "__notes__", []) == []


# ============================================================================================= #
# close-466 R1 — F1's class on the TEARDOWN side: an unexpected BaseException in the shutdown join.
# ============================================================================================= #
class TestAnInterruptedTeardownLeavesNothingBehind:
    """R1 (REPORT-refactor-466-d1.md §Step 1): F1 made an interrupted START clean up; an interrupt landing in
    the teardown JOIN (Ctrl-C, pytest-timeout's signal method — the same door) propagated out of the exit
    with the ``uvicorn.error`` capture handler still attached for the life of the process. The lifespan
    shutdown is held blocked so the interrupt can only land IN the join; it is released afterwards so the
    server thread CAN end."""

    @pytest.mark.parametrize("interrupt", _UNEXPECTED_INTERRUPTS)
    @pytest.mark.parametrize("port_ownership", ["owned", "passed"])
    def test_the_interrupt_propagates_unchanged_and_nothing_is_left_behind(
        self, interrupt: type[BaseException], port_ownership: str
    ) -> None:
        # Discrimination: the interrupt must fire well INSIDE the budget, or it would land after an overrun
        # (a different path) and the pin would test that instead.
        assert INTERRUPT_AFTER_S < GENEROUS_SHUTDOWN_BUDGET_S / 2
        gate = threading.Event()
        app = _RecordingApp(f"interrupted-teardown-{port_ownership}-466", shutdown_gate=gate)
        handlers_before = _attached_logging_handlers()
        threads_before = set(threading.enumerate())
        with contextlib.ExitStack() as stack:
            held = stack.enter_context(LoopbackPort()) if port_ownership == "passed" else None
            try:
                with _main_thread_interrupt(interrupt) as (raised, arm):
                    with pytest.raises(interrupt) as excinfo:
                        with serve_asgi(
                            app, port=held, shutdown_timeout_s=GENEROUS_SHUTDOWN_BUDGET_S
                        ) as served:
                            assert _get(served.base_url).status_code == HTTP_OK
                            # Armed as the LAST act of the body: it can only land once exit is under way.
                            arm(INTERRUPT_AFTER_S)
                            exit_started = time.monotonic()
                    elapsed = time.monotonic() - exit_started
                    # Non-vacuity: it fired once, what came out is THAT object, and it landed IN the teardown
                    # wait — the exit waited for it, and the (blocked) lifespan shutdown had not completed.
                    assert len(raised) == 1, f"the interrupt fired {len(raised)} times — the probe is broken"
                    assert excinfo.value is raised[0], (
                        f"the exit replaced the interrupt with {excinfo.value!r} — it must propagate "
                        "UNCHANGED"
                    )
                    assert INTERRUPT_AFTER_S * 0.9 <= elapsed < GENEROUS_SHUTDOWN_BUDGET_S, elapsed
                    assert app.events == ["startup"], app.events
                # The process-global logging state is exactly what it was.
                assert _attached_logging_handlers() == handlers_before, (
                    "the interrupted teardown left a logging handler attached — the capture was detached "
                    "only after an UNINTERRUPTED join: "
                    f"before={handlers_before} after={_attached_logging_handlers()}"
                )
            finally:
                gate.set()
            survivors = _threads_still_alive_after(threads_before, THREAD_END_BOUND_S)
            assert survivors == [], f"the interrupted teardown left server thread(s) running: {survivors}"
            assert _becomes_refused(served.host, served.port), (
                f"{served.host}:{served.port} ({port_ownership} port) still accepts after the interrupted "
                "teardown"
            )


# ============================================================================================= #
# d1/ruling (d) — serve_http's teardown with a STUCK handler is bounded and LOUD, exactly like serve_asgi's.
# Lead-directed pin, authored in Phase 5 AFTER the build (documented deviation from test-first: the ruling
# post-dated the contract). Proven able to fail by mutation — REPORT-refactor-466-d1.md §Pins-d.
# DUAL (budget): first authored against serve_http's ONLY budget, the real 5 s default (spent twice per run);
# since serve_http gained ``shutdown_timeout_s`` (8d42c27) the two overrun pins pass SHORT_SHUTDOWN_BUDGET_S.
# Assertions unchanged — only the budget argument moved, and the window/discrimination constants with it.
# That the budget is THREADED (not the default) is proven by mutation: REPORT-close-466.md §Item 2.
# ============================================================================================= #
def _stuck_handler_class() -> tuple[
    type[http.server.BaseHTTPRequestHandler], threading.Event, threading.Event
]:
    """A fresh handler class whose ``do_GET`` announces it ENTERED, then blocks until RELEASED.

    Returns ``(handler_class, entered, released)``. The block is bounded by ``STUCK_HANDLER_BOUND_S`` so a
    wrong build that waits for the handler finishes (RED) instead of hanging. It writes no response: the
    client is closed in teardown, and a write racing that close would only add a broken-pipe traceback.
    """
    entered = threading.Event()
    released = threading.Event()

    class _StuckHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 — stdlib override name
            entered.set()
            released.wait(STUCK_HANDLER_BOUND_S)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002 — stdlib signature
            return

    return _StuckHandler, entered, released


def _stick_a_request(served_host: str, served_port: int, entered: threading.Event) -> socket.socket:
    """Send one complete request and wait until the handler is INSIDE it; return the open client."""
    client = socket.create_connection((served_host, served_port), timeout=HTTP_TIMEOUT_S)
    client.sendall(STUCK_HANDLER_REQUEST)
    assert entered.wait(HTTP_TIMEOUT_S), (
        "the stuck handler was never entered — the teardown below would not be stuck, so the pin would "
        "certify nothing"
    )
    return client


class TestServeHttpShutdownOverrunIsLoud:
    """Ruling (d): ``HTTPServer.shutdown()`` waits, with NO timeout, for ``serve_forever`` — and a stuck
    request handler runs inside that loop, so the old exit HUNG. Now the exit is bounded by
    ``serve_http(shutdown_timeout_s=…)`` (default ``DEFAULT_SHUTDOWN_TIMEOUT_S`` — parity with serve_asgi)
    and the overrun is LOUD by the SAME policy as serve_asgi's (``TestAShutdownOverrunIsLoud``): a clean
    exit raises ``ServerShutdownTimeout`` naming ``host:port``; a body already raising keeps its own
    exception and carries the overrun as a note."""

    def test_a_clean_exit_with_a_stuck_handler_raises_naming_the_address(self) -> None:
        # Fixture discrimination: the handler must outlive the window, or a build that simply waits for the
        # handler would ALSO finish inside it; and the window must end before the DEFAULT, or a build that
        # ignores the passed budget would too.
        assert _STUCK_EXIT_WINDOW_HIGH_S < DEFAULT_SHUTDOWN_TIMEOUT_S < STUCK_HANDLER_BOUND_S
        handler_class, entered, released = _stuck_handler_class()
        threads_before = set(threading.enumerate())
        client: socket.socket | None = None
        try:
            with pytest.raises(ServerShutdownTimeout) as excinfo:
                with serve_http(handler_class, shutdown_timeout_s=SHORT_SHUTDOWN_BUDGET_S) as served:
                    client = _stick_a_request(served.host, served.port, entered)
                    exit_started = time.monotonic()
            elapsed = time.monotonic() - exit_started
            error = excinfo.value
            assert type(error) is ServerShutdownTimeout
            assert (error.host, error.port) == (served.host, served.port)
            message = str(error)
            assert f"{served.host}:{served.port}" in message, (
                f"the overrun does not name the address: {message}"
            )
            assert "shutdown" in message.lower(), f"the overrun does not say it was the shutdown: {message}"
            assert error.shutdown_timeout_s == SHORT_SHUTDOWN_BUDGET_S
            # Not early (the handler was given the budget) and not stuck (exit did not wait for the handler).
            assert _STUCK_EXIT_WINDOW_LOW_S <= elapsed <= _STUCK_EXIT_WINDOW_HIGH_S, (
                f"exit took {elapsed:.2f}s against a {SHORT_SHUTDOWN_BUDGET_S}s budget"
            )
            assert _becomes_refused(served.host, served.port), (
                "the owned port still accepts after the overrun"
            )
        finally:
            released.set()
            if client is not None:
                client.close()
        # Once the handler returns, the serving thread (and the shutdown request's thread) must end.
        survivors = _threads_still_alive_after(threads_before, THREAD_END_BOUND_S)
        assert survivors == [], f"serve_http left thread(s) running after the released handler: {survivors}"

    def test_a_failing_body_keeps_its_own_exception_and_carries_the_overrun_as_a_note(self) -> None:
        handler_class, entered, released = _stuck_handler_class()
        body_failure = _BodyFailure(BODY_FAILURE_SENTINEL)
        client: socket.socket | None = None
        try:
            with pytest.raises(_BodyFailure) as excinfo:
                with serve_http(handler_class, shutdown_timeout_s=SHORT_SHUTDOWN_BUDGET_S) as served:
                    client = _stick_a_request(served.host, served.port, entered)
                    exit_started = time.monotonic()
                    raise body_failure
            elapsed = time.monotonic() - exit_started
            assert excinfo.value is body_failure, (
                f"the body's own exception was replaced by {excinfo.value!r} — the overrun MASKED it"
            )
            notes = "\n".join(getattr(body_failure, "__notes__", []))
            assert f"{served.host}:{served.port}" in notes and "shutdown" in notes.lower(), (
                f"the overrun is SILENT on the failing path — no note naming the address: {notes!r}"
            )
            # Both bounds, on THIS path too: a build that skips the wait when the body failed is not bounded
            # below, and one that waits for the handler is not bounded above.
            assert _STUCK_EXIT_WINDOW_LOW_S <= elapsed <= _STUCK_EXIT_WINDOW_HIGH_S, (
                f"exit took {elapsed:.2f}s against a {SHORT_SHUTDOWN_BUDGET_S}s budget"
            )
        finally:
            released.set()
            if client is not None:
                client.close()

    def test_both_helpers_default_to_the_same_shutdown_budget(self) -> None:
        # Parity: serve_http's budget is a parameter with the SAME default as serve_asgi's, so the two helpers
        # cannot drift apart on the default the overrun policy runs with.
        defaults = {
            helper.__name__: inspect.signature(helper).parameters["shutdown_timeout_s"].default
            for helper in (serve_asgi, serve_http)
        }
        assert defaults == {
            "serve_asgi": DEFAULT_SHUTDOWN_TIMEOUT_S,
            "serve_http": DEFAULT_SHUTDOWN_TIMEOUT_S,
        }

    def test_positive_control_a_failing_body_with_a_prompt_handler_gets_no_note(self) -> None:
        # The note is evidence of an overrun, not decoration on every failure (and a clean prompt exit not
        # raising is already every TestServeHttp pin).
        body_failure = _BodyFailure(BODY_FAILURE_SENTINEL)
        with pytest.raises(_BodyFailure):
            with serve_http(_StubHandler) as served:
                assert _get(served.base_url).status_code == HTTP_OK
                raise body_failure
        assert getattr(body_failure, "__notes__", []) == []


# ============================================================================================= #
# d1/C2 — the bind spy's premise, PINNED (it used to be a docstring sentence).
# ============================================================================================= #
class TestTheBindSpyPremiseHolds:
    """C2 (REPORT-refactor-466.md §2): ``_spy_on_every_bind`` sees a bind only if it goes through the
    Python ``socket.socket.bind`` — true for asyncio's ``create_server``, UNVERIFIED for uvloop (which
    binds in libuv). uvicorn's default ``loop="auto"`` would switch to uvloop the day it is installed
    (``uvicorn[standard]`` pulls it in), silently blinding every no-specific-port pin.

    Decision (d1 report §C2): PIN THE PREMISE rather than force ``loop="asyncio"`` in the helper —
    production ``LoreServer`` runs uvicorn on the default ``"auto"`` loop, so forcing asyncio in the test
    helper would make the wire harness test a loop production would no longer run (THE TEST ENVIRONMENT
    IS A FICTION, #131). The day this reddens, decide deliberately: verify the spy under uvloop, or force
    the loop in BOTH places."""

    _REOPEN = (
        "RE-OPEN (#466 C2): uvloop is now importable. uvicorn's loop='auto' will serve on it, and "
        "`_spy_on_every_bind` may no longer see uvicorn's binds (libuv binds in C), so the "
        "no-specific-port pins can pass BLIND. Verify the spy under uvloop, or force loop='asyncio' in "
        "BOTH loremaster.testing.loopback and LoreServer — then update this pin and say so."
    )

    def test_uvloop_is_not_installed(self) -> None:
        assert importlib.util.find_spec("uvloop") is None, self._REOPEN

    def test_the_served_app_runs_on_a_stdlib_asyncio_loop(self) -> None:
        # The premise stated behaviourally, so any door to a non-stdlib loop (an extra, a policy, a
        # plugin) reddens it — not only the one ``find_spec`` can see.
        app = _RecordingApp("loop-premise-466")
        with serve_asgi(app) as served:
            assert _get(served.base_url).status_code == HTTP_OK
        assert app.loop_classes, "no request was recorded — the premise probe saw nothing"
        foreign = [cls for cls in app.loop_classes if cls.__module__.split(".")[0] != "asyncio"]
        assert foreign == [], f"{self._REOPEN}\nserved on: {foreign}"


# ============================================================================================= #
# #503 R4 (refactor-466-d1 R4, operator: "fix now") — author ``contract-503``, session ``297217bd``.
#
# CLASS (the lifted property): a failing ``with`` body's exception is NEVER REPLACED by ANY teardown
# failure of ANY serving helper. The teardown problem rides that exception as a PEP 678 note naming
# ``host:port``. The domain is the product of three sets, each GENERATED, never hand-listed:
#   * the helpers — every public context manager in ``loopback.__all__`` that yields a
#     ``ServedEndpoint`` (derived from the type hints; ``test_every_serving_helper_has_a_teardown_rig``
#     reddens when a new one appears without a rig);
#   * the body failures — an ``Exception`` and a non-``Exception`` ``BaseException`` (pytest's own
#     ``Failed`` / pytest-timeout's signal failure are the latter, so "a failing test" spans both);
#   * the teardown failures — the COMPLETE outcome set of ``stop(budget) -> bool`` other than success:
#     it returns ``False`` (an OVERRUN, already loud since d1) or it RAISES (R4's hole: the measured
#     door is ``_stop_http_server``'s ``Thread.start()`` → ``RuntimeError: can't start new thread``).
# The raise is injected receiver-blind — a ``SIGALRM`` handler raising an ``Exception`` inside the
# teardown wait — so the pin never depends on WHICH call inside ``stop`` fails.
#
# RED dating: the ``raise`` rows are RED at HEAD ``884ca63`` (the stop error REPLACES the body's, which
# survives only as ``__context__``); the ``overrun`` rows and both controls are GREEN at ``884ca63``.
# ============================================================================================= #
# The text a raising teardown carries — distinctive, so the note must carry the teardown's OWN words.
TEARDOWN_FAILURE_SENTINEL = "can't start new thread — r4-teardown-sentinel-503"


class _TeardownFailure(RuntimeError):
    """What a helper's ``stop`` raises in R4's world (``RuntimeError``, like thread exhaustion)."""

    def __init__(self) -> None:
        super().__init__(TEARDOWN_FAILURE_SENTINEL)


@dataclass
class _TeardownRig:
    """One serving helper, set up so that its exit's teardown wait BLOCKS until :meth:`release`.

    ``serving`` is the helper's context manager, already given the budget the row needs; ``engage``
    runs INSIDE the body and makes the teardown block (it proves the server is serving first);
    ``release`` un-blocks it so every thread can end; ``still_blocked`` is read right after the exit
    and must be ``True`` — proof the injected failure landed IN the teardown, not after it.
    """

    serving: contextlib.AbstractContextManager[ServedEndpoint]
    engage: Callable[[ServedEndpoint], None]
    release: Callable[[], None]
    still_blocked: Callable[[], bool]


def _serve_asgi_rig(shutdown_timeout_s: float) -> _TeardownRig:
    """serve_asgi, whose lifespan SHUTDOWN is held on a gate (a store close that never returns)."""
    gate = threading.Event()
    app = _RecordingApp(f"r4-teardown-asgi-{shutdown_timeout_s}-503", shutdown_gate=gate)

    def _engage(served: ServedEndpoint) -> None:
        assert _get(served.base_url).status_code == HTTP_OK

    return _TeardownRig(
        serving=serve_asgi(app, shutdown_timeout_s=shutdown_timeout_s),
        engage=_engage,
        release=gate.set,
        still_blocked=lambda: app.events == ["startup"],
    )


def _serve_http_rig(shutdown_timeout_s: float) -> _TeardownRig:
    """serve_http, with one request STUCK inside its handler (so ``serve_forever`` cannot return)."""
    handler_class, entered, released = _stuck_handler_class()
    clients: list[socket.socket] = []

    def _engage(served: ServedEndpoint) -> None:
        clients.append(_stick_a_request(served.host, served.port, entered))

    def _release() -> None:
        released.set()
        for client in clients:
            client.close()

    return _TeardownRig(
        serving=serve_http(handler_class, shutdown_timeout_s=shutdown_timeout_s),
        engage=_engage,
        release=_release,
        still_blocked=lambda: entered.is_set() and not released.is_set(),
    )


# Keyed by the helper's __name__; completeness is asserted against the module, not trusted.
_TEARDOWN_RIGS: dict[str, Callable[[float], _TeardownRig]] = {
    "serve_asgi": _serve_asgi_rig,
    "serve_http": _serve_http_rig,
}


def _serving_helpers_of_the_module() -> set[str]:
    """Every public helper in ``loopback.__all__`` that is a context manager yielding a ServedEndpoint.

    DERIVED from the type hints, not from a name prefix: whatever the next helper is called, if it
    yields a served endpoint it exits through a teardown, and R4's class covers it.
    """
    helpers: set[str] = set()
    for name in loopback_module.__all__:
        candidate = getattr(loopback_module, name)
        if not inspect.isfunction(candidate):
            continue
        return_hint = typing.get_type_hints(candidate).get("return")
        if ServedEndpoint in typing.get_args(return_hint):
            helpers.add(name)
    return helpers


@dataclass(frozen=True)
class _TeardownFailureKind:
    """One non-success outcome of ``stop``: the budget the rig runs with, whether a raise is injected
    into the teardown wait, the exit window, and the words the note must carry."""

    shutdown_timeout_s: float
    injects_a_raise: bool
    exit_window_s: tuple[float, float]
    note_must_name: tuple[str, ...]


_TEARDOWN_FAILURE_KINDS: dict[str, _TeardownFailureKind] = {
    # stop RAISES: the injection lands INTERRUPT_AFTER_S into a GENEROUS wait, so exit ends near
    # INTERRUPT_AFTER_S — long before the budget (a build that waits out the budget is caught above).
    "raise": _TeardownFailureKind(
        shutdown_timeout_s=GENEROUS_SHUTDOWN_BUDGET_S,
        injects_a_raise=True,
        exit_window_s=(INTERRUPT_AFTER_S * 0.9, GENEROUS_SHUTDOWN_BUDGET_S / 2),
        note_must_name=(_TeardownFailure.__name__, TEARDOWN_FAILURE_SENTINEL),
    ),
    # stop returns False: the short budget expires with the teardown still blocked.
    "overrun": _TeardownFailureKind(
        shutdown_timeout_s=SHORT_SHUTDOWN_BUDGET_S,
        injects_a_raise=False,
        exit_window_s=(SHORT_SHUTDOWN_BUDGET_S * 0.9, SHORT_SHUTDOWN_BUDGET_S + SHUTDOWN_GIVE_UP_GRACE_S),
        note_must_name=("shutdown",),
    ),
}

_BODY_FAILURE_TYPES = [
    pytest.param(_BodyFailure, id="body-raises-Exception"),
    pytest.param(_InjectedInterrupt, id="body-raises-BaseException"),
]


class TestAFailingBodyIsNeverReplacedByItsTeardown:
    """R4 (REPORT-refactor-466-d1.md R4): ``_loud_teardown`` calls ``stop`` bare in its failing-body
    branch, so a ``stop`` that RAISES replaces the test's own failure — the headline becomes a teardown
    error and the real failure survives only as ``__context__``. The d1 overrun policy already said
    "never mask"; this generalises it from one teardown failure (an overrun) to every one."""

    def test_every_serving_helper_has_a_teardown_rig(self) -> None:
        # Completeness: the generated sweep below is only a sweep if its domain is the module's.
        derived = _serving_helpers_of_the_module()
        assert derived, "the derivation found no serving helper — the probe is broken"
        assert derived == set(_TEARDOWN_RIGS), (
            f"loopback exports serving helper(s) {sorted(derived - set(_TEARDOWN_RIGS))} with no teardown "
            f"rig (or rigs {sorted(set(_TEARDOWN_RIGS) - derived)} for helpers that no longer exist) — R4's "
            "class covers EVERY helper that exits through a teardown; add a rig, do not narrow the domain"
        )

    @pytest.mark.parametrize("teardown_failure", sorted(_TEARDOWN_FAILURE_KINDS))
    @pytest.mark.parametrize("body_failure_type", _BODY_FAILURE_TYPES)
    @pytest.mark.parametrize("helper_name", sorted(_TEARDOWN_RIGS))
    def test_the_body_exception_survives_and_the_teardown_failure_rides_as_a_note(
        self, helper_name: str, body_failure_type: type[BaseException], teardown_failure: str
    ) -> None:
        kind = _TEARDOWN_FAILURE_KINDS[teardown_failure]
        rig = _TEARDOWN_RIGS[helper_name](kind.shutdown_timeout_s)
        body_failure = body_failure_type(BODY_FAILURE_SENTINEL)
        handlers_before = _attached_logging_handlers()
        threads_before = set(threading.enumerate())
        try:
            # The timer is armed only on the "raise" rows; an unarmed timer never fires.
            with _main_thread_interrupt(_TeardownFailure) as (raised, arm):
                # BaseException, not body_failure_type: a REPLACED exception must fail this test with an
                # assertion naming the replacement, not escape pytest.raises as a stray error.
                with pytest.raises(BaseException) as excinfo:
                    with rig.serving as served:
                        rig.engage(served)
                        if kind.injects_a_raise:
                            # The LAST act of the body: it can only land once exit is under way.
                            arm(INTERRUPT_AFTER_S)
                        exit_started = time.monotonic()
                        raise body_failure
                elapsed = time.monotonic() - exit_started
                teardown_was_blocked = rig.still_blocked()
            # Non-vacuity: the injection fired exactly when it should, IN the teardown wait.
            assert len(raised) == (1 if kind.injects_a_raise else 0), (
                f"the teardown injection fired {len(raised)} times — the probe is broken"
            )
            assert teardown_was_blocked, (
                "the teardown was not blocked at exit — the failure did not land IN it"
            )
            low_s, high_s = kind.exit_window_s
            assert low_s <= elapsed <= high_s, f"exit took {elapsed:.2f}s; expected [{low_s}, {high_s}]"
            # THE CLASS: the test's own failure is the headline, whatever the teardown did.
            assert excinfo.value is body_failure, (
                f"{helper_name}'s teardown REPLACED the body's own {body_failure_type.__name__} with "
                f"{excinfo.value!r} — a failing test must report ITS failure; the teardown's rides as a note"
            )
            notes = "\n".join(getattr(body_failure, "__notes__", []))
            address = f"{served.host}:{served.port}"
            assert address in notes, f"the teardown failure is SILENT — no note naming {address}: {notes!r}"
            for fragment in kind.note_must_name:
                assert fragment.lower() in notes.lower(), (
                    f"the note does not carry the teardown failure's own evidence {fragment!r}: {notes!r}"
                )
            # Nothing process-global leaks on this path either (R1's outcome, on R4's path).
            assert _attached_logging_handlers() == handlers_before, (
                f"a logging handler was left attached: before={handlers_before} "
                f"after={_attached_logging_handlers()}"
            )
            assert _becomes_refused(served.host, served.port), f"{address} still accepts after the exit"
        finally:
            rig.release()
        survivors = _threads_still_alive_after(threads_before, THREAD_END_BOUND_S)
        assert survivors == [], f"{helper_name} left thread(s) running once released: {survivors}"

    @pytest.mark.parametrize("helper_name", sorted(_TEARDOWN_RIGS))
    def test_control_a_clean_body_whose_teardown_raises_propagates_that_error(self, helper_name: str) -> None:
        # Ruling (Phase 0 item 2): with NO body error to preserve, the stop error IS the failure, and it
        # must surface unchanged — the R4 fix must not swallow or re-wrap it. Without this, "notes the
        # teardown failure" could be a build that notes it and then drops it on a clean exit.
        rig = _TEARDOWN_RIGS[helper_name](GENEROUS_SHUTDOWN_BUDGET_S)
        try:
            with _main_thread_interrupt(_TeardownFailure) as (raised, arm):
                with pytest.raises(BaseException) as excinfo:
                    with rig.serving as served:
                        rig.engage(served)
                        arm(INTERRUPT_AFTER_S)
            assert len(raised) == 1, f"the teardown injection fired {len(raised)} times — the probe is broken"
            assert excinfo.value is raised[0], (
                f"a clean exit whose teardown raised surfaced {excinfo.value!r} instead of the "
                f"teardown's own {raised[0]!r} — with no body failure, the teardown failure IS the headline"
            )
        finally:
            rig.release()

    @pytest.mark.parametrize("interrupt", _UNEXPECTED_INTERRUPTS)
    @pytest.mark.parametrize("helper_name", sorted(_TEARDOWN_RIGS))
    def test_an_interrupt_in_the_teardown_of_a_failing_body_still_propagates(
        self, helper_name: str, interrupt: type[BaseException]
    ) -> None:
        # R1's contract must not regress (Phase 0 item 2): Ctrl-C / pytest-timeout landing in the teardown
        # wait propagate UNCHANGED — also when the body is already failing. The wrong build this catches
        # wraps ``stop`` in ``except BaseException`` and notes EVERYTHING, swallowing the interrupt.
        # ⚠ SPEC-SILENT, author's reading (READING A) — see REPORT-contract-503.md §Forks F1: the ruling
        # names "an overrun OR a raise" as teardown FAILURES, and an interrupt as the user's control flow.
        # The body's failure stays reachable on the interrupt's ``__context__`` (pytest prints the chain).
        rig = _TEARDOWN_RIGS[helper_name](GENEROUS_SHUTDOWN_BUDGET_S)
        body_failure = _BodyFailure(BODY_FAILURE_SENTINEL)
        handlers_before = _attached_logging_handlers()
        try:
            with _main_thread_interrupt(interrupt) as (raised, arm):
                with pytest.raises(BaseException) as excinfo:
                    with rig.serving as served:
                        rig.engage(served)
                        arm(INTERRUPT_AFTER_S)
                        raise body_failure
            assert len(raised) == 1, f"the interrupt fired {len(raised)} times — the probe is broken"
            assert excinfo.value is raised[0], (
                f"{helper_name}'s teardown swallowed the {interrupt.__name__} (surfaced {excinfo.value!r}) — "
                "an interrupt is not a teardown failure to note; it must propagate unchanged"
            )
            assert excinfo.value.__context__ is body_failure, (
                "the body's own failure is no longer reachable from the interrupt's traceback chain"
            )
            assert _attached_logging_handlers() == handlers_before
        finally:
            rig.release()
