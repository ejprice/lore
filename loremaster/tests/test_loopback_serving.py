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
"""

from __future__ import annotations

import _socket
import asyncio
import contextlib
import errno
import http.server
import socket
import threading
import time
from collections.abc import AsyncIterator, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import httpx
import pytest
from loremaster.testing.loopback import (
    DEFAULT_STARTUP_TIMEOUT_S,
    LOOPBACK_HOST,
    LoopbackPort,
    ServerBindError,
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
    """

    def __init__(
        self,
        identity: str,
        *,
        startup_delay_s: float = 0.0,
        startup_gate: threading.Event | None = None,
    ) -> None:
        self.identity = identity
        self.startup_delay_s = startup_delay_s
        self.startup_gate = startup_gate
        self.events: list[str] = []

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
                    self.events.append("shutdown")
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        elif scope["type"] == "http":
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
            # The budget that expired travels as data (the value is measure-then-tune — §E).
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
        # Existence + sanity only; the VALUE is measure-then-tune (#466 contract report, §E).
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
