"""ONE race-free loopback listener, and a server start that NAMES its failure (finding #466).

The retired pattern bound ``127.0.0.1:0``, read the port, CLOSED the socket, then handed the
NUMBER to a server that bound it again — a window in which any other process could take the
port. Every helper here instead HOLDS the kernel-assigned socket for the whole context and
serves FROM it, so no specific (non-zero) port is ever bound.

Both servers are the packages' own, handed the held socket rather than re-implemented:
uvicorn's ``Server.run(sockets=[...])`` (it calls ``loop.create_server(sock=...)`` and never
binds) and the stdlib ``http.server.HTTPServer`` built with ``bind_and_activate=False`` and then
activated on the held socket.

Contract: ``loremaster/tests/test_loopback_serving.py`` and
``skills/lore-deploy/tests/test_loopback_home.py``.
"""

from __future__ import annotations

import contextlib
import http.server
import logging
import socketserver
import threading
import time
from collections.abc import Awaitable, Callable, Iterator
from dataclasses import dataclass
from socket import AF_INET, SOCK_STREAM
from socket import socket as TcpSocket  # noqa: N812 — distinguishes the type from the .socket attribute
from types import TracebackType
from typing import Literal

import uvicorn

LOOPBACK_HOST: str = "127.0.0.1"
"""The only host the helpers bind by default — loopback, never a routable interface."""

DEFAULT_STARTUP_TIMEOUT_S: float = 15.0
"""How long :func:`serve_asgi` waits for the server to report started before raising
:class:`ServerStartupTimeout`. The value is measure-then-tune (#466 contract report §E); callers
pass ``startup_timeout_s`` to override it without editing this module."""

KERNEL_ASSIGNED_PORT: int = 0
"""The port number that asks the kernel for an ephemeral port — the ONLY port ever bound here."""

_STARTUP_POLL_S: float = 0.02
"""How often the startup wait re-checks ``started`` / thread death. Small, so a crash is named
promptly rather than when the budget expires."""

_SHUTDOWN_JOIN_TIMEOUT_S: float = 5.0
"""How long exit waits for a STARTED server thread to finish its lifespan shutdown."""

_UVICORN_ERROR_LOGGER: str = "uvicorn.error"
"""The logger uvicorn reports lifespan failures on — the only place a lifespan crash's own text
goes (uvicorn ends the server thread NORMALLY after a failed startup; nothing is raised)."""

_UVICORN_LOG_LEVEL: str = "error"
"""Quiet uvicorn's info chatter; errors (the crash evidence) still flow."""

_UVICORN_LIFESPAN: Literal["on"] = "on"
"""Lifespan FORCED on (packet-59 FG1): an app that cannot speak lifespan fails loudly instead of
being served with its startup silently skipped (``"auto"``)."""

_NO_ERROR_LOGGED: str = "(the server thread logged no error)"
"""The crash detail when the thread ended without logging or raising anything."""

AsgiApplication = Callable[..., Awaitable[None]]
"""An ASGI 3 application: ``await app(scope, receive, send)``."""


class ServerStartError(RuntimeError):
    """A test server failed to start. Never raised directly — one leaf per cause.

    Attributes:
        host: The host the server was to be served on.
        port: The port the server was to be served on (``0`` if no port was ever assigned).
    """

    def __init__(self, message: str, *, host: str, port: int) -> None:
        """Record the failed address alongside the message.

        Args:
            message: Human-readable cause; must name ``host:port``.
            host: The host the server was to be served on.
            port: The port the server was to be served on.
        """
        super().__init__(message)
        self.host = host
        self.port = port


class ServerBindError(ServerStartError):
    """Cause 1 of 3: binding the listener socket itself failed.

    The underlying :class:`OSError` is chained as ``__cause__``; the message names the address
    and says it was a bind.
    """


class ServerStartupTimeout(ServerStartError):
    """Cause 2 of 3: the server thread is alive but did not report started within the budget.

    Attributes:
        startup_timeout_s: The budget that expired, in seconds.
    """

    def __init__(self, message: str, *, host: str, port: int, startup_timeout_s: float) -> None:
        """Record the failed address and the expired budget.

        Args:
            message: Human-readable cause; must name ``host:port`` and say it timed out.
            host: The host the server was to be served on.
            port: The port the server was to be served on.
            startup_timeout_s: The startup budget that expired, in seconds.
        """
        super().__init__(message, host=host, port=port)
        self.startup_timeout_s = startup_timeout_s


class ServerThreadCrashed(ServerStartError):
    """Cause 3 of 3: the server thread ended before it reported started.

    Raised promptly on thread death (not when the budget expires); the message carries the
    app's own error text (a raising lifespan, a ``lifespan.startup.failed``, or an app that
    cannot speak lifespan at all).
    """


@dataclass(frozen=True)
class ServedEndpoint:
    """Where a started test server is answering.

    Attributes:
        host: The served host.
        port: The served port — the held socket's port.
        base_url: ``http://{host}:{port}``.
    """

    host: str
    port: int
    base_url: str


class LoopbackPort:
    """A socket already bound to ``host:0`` and HELD open for the whole context.

    Bound but NOT listening by default, so a connect is refused (a race-free "dead port": the
    port is unserved and nobody else can take it). :meth:`listen` makes it accept; exit closes
    it. A bind failure raises :class:`ServerBindError` no later than ``__enter__``.

    Attributes:
        host: The bound host.
        port: The kernel-assigned ephemeral port.
        socket: The held, bound socket.
        base_url: ``http://{host}:{port}``.
    """

    host: str
    port: int
    socket: TcpSocket
    base_url: str

    def __init__(self, host: str = LOOPBACK_HOST) -> None:
        """Bind a fresh TCP socket to ``host:0`` and keep it open.

        Args:
            host: The host to bind; defaults to :data:`LOOPBACK_HOST`.

        Raises:
            ServerBindError: If the bind fails; the :class:`OSError` is chained.
        """
        self.host = host
        self.socket = TcpSocket(AF_INET, SOCK_STREAM)
        try:
            self.socket.bind((host, KERNEL_ASSIGNED_PORT))
        except OSError as bind_error:
            self.socket.close()
            raise ServerBindError(
                f"bind of {host}:{KERNEL_ASSIGNED_PORT} failed: {bind_error}",
                host=host,
                port=KERNEL_ASSIGNED_PORT,
            ) from bind_error
        self.port = int(self.socket.getsockname()[1])
        self.base_url = f"http://{host}:{self.port}"

    def listen(self) -> None:
        """Start listening on the held socket so connects are accepted."""
        self.socket.listen()

    def close(self) -> None:
        """Close the held socket, releasing the port."""
        self.socket.close()

    def served_endpoint(self) -> ServedEndpoint:
        """The endpoint a server started FROM this held socket answers on."""
        return ServedEndpoint(host=self.host, port=self.port, base_url=self.base_url)

    def __enter__(self) -> LoopbackPort:
        """Enter the context, returning this held port."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the held socket on exit, whatever ended the context."""
        self.close()


def _held_port(port: LoopbackPort | None) -> contextlib.AbstractContextManager[LoopbackPort]:
    """The caller's held port unchanged (the caller closes it), or a fresh one this helper owns.

    Args:
        port: A caller-held port, or ``None`` to own a fresh :class:`LoopbackPort`.

    Returns:
        A context manager yielding the port to serve from.
    """
    if port is None:
        return LoopbackPort()
    return contextlib.nullcontext(port)


class _ThreadErrorCapture(logging.Handler):
    """Collect the ERROR records ONE thread logs — the server thread's crash evidence.

    Filtered by thread, because the uvicorn logger is process-global: concurrent servers each
    capture only their own failure text.
    """

    def __init__(self, thread: threading.Thread) -> None:
        """Watch ``thread``'s records.

        Args:
            thread: The server thread whose errors are evidence.
        """
        super().__init__(level=logging.ERROR)
        self._thread = thread
        self._lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Keep the formatted record (message + traceback) if the watched thread logged it."""
        if record.thread == self._thread.ident:
            self._lines.append(self.format(record))

    @property
    def text(self) -> str:
        """Everything captured, one record per line group."""
        return "\n".join(self._lines)


class _UvicornServerThread:
    """A real uvicorn serving ONE held socket from a daemon thread, with its failure evidence kept.

    ``log_config=None``: uvicorn's default ``dictConfig`` would reset the process-global
    ``uvicorn.error`` handlers on every construction, stripping a concurrent server's crash
    capture mid-start.
    """

    def __init__(self, app: AsgiApplication, held: LoopbackPort) -> None:
        """Build (but do not start) the server for ``app`` on ``held``'s socket.

        Args:
            app: The ASGI application to serve.
            held: The held port whose socket uvicorn serves from.
        """
        self._held = held
        self._address = f"{held.host}:{held.port}"
        config = uvicorn.Config(
            app, lifespan=_UVICORN_LIFESPAN, log_level=_UVICORN_LOG_LEVEL, log_config=None
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._run, name=f"serve_asgi {self._address}", daemon=True)
        self._capture = _ThreadErrorCapture(self._thread)
        self._crash: BaseException | None = None

    def _run(self) -> None:
        """Thread body: serve until told to exit, keeping any escaping exception as evidence."""
        try:
            self._server.run(sockets=[self._held.socket])
        except BaseException as crash:  # noqa: BLE001 — incl. uvicorn's SystemExit; reported by start()
            self._crash = crash

    def start(self, startup_timeout_s: float) -> None:
        """Start the thread and wait until uvicorn reports started.

        Args:
            startup_timeout_s: How long to wait for ``started``.

        Raises:
            ServerThreadCrashed: The thread ended first (the held socket is closed).
            ServerStartupTimeout: The budget expired with the thread alive (the held socket is
                closed).
        """
        logging.getLogger(_UVICORN_ERROR_LOGGER).addHandler(self._capture)
        self._thread.start()
        deadline = time.monotonic() + startup_timeout_s
        while not self._server.started:
            if not self._thread.is_alive():
                self._abandon()
                raise ServerThreadCrashed(
                    f"server thread for {self._address} ended before it reported started:\n"
                    f"{self._crash_detail()}",
                    host=self._held.host,
                    port=self._held.port,
                )
            remaining_s = deadline - time.monotonic()
            if remaining_s <= 0:
                self._abandon()
                raise ServerStartupTimeout(
                    f"server at {self._address} timed out: not started within {startup_timeout_s}s "
                    "(server thread still alive)",
                    host=self._held.host,
                    port=self._held.port,
                    startup_timeout_s=startup_timeout_s,
                )
            # A join returns the moment the thread dies, so a crash is named within one poll.
            self._thread.join(timeout=min(_STARTUP_POLL_S, remaining_s))

    def stop(self) -> None:
        """Drive a real lifespan shutdown and wait (bounded) for the thread to finish."""
        self._server.should_exit = True
        self._thread.join(timeout=_SHUTDOWN_JOIN_TIMEOUT_S)
        self._detach_capture()

    def _abandon(self) -> None:
        """Give up on a failed start: ask the thread to exit and release the held port NOW.

        Never joins — a stuck lifespan would hold the caller hostage; the thread is a daemon.
        """
        self._server.should_exit = True
        self._held.close()
        self._detach_capture()

    def _detach_capture(self) -> None:
        """Stop capturing this thread's records."""
        logging.getLogger(_UVICORN_ERROR_LOGGER).removeHandler(self._capture)

    def _crash_detail(self) -> str:
        """The app's own error text: logged records first, then any exception that escaped."""
        parts = [part for part in (self._capture.text, repr(self._crash) if self._crash else "") if part]
        return "\n".join(parts) or _NO_ERROR_LOGGED


@contextlib.contextmanager
def serve_asgi(
    app: AsgiApplication,
    *,
    port: LoopbackPort | None = None,
    startup_timeout_s: float = DEFAULT_STARTUP_TIMEOUT_S,
) -> Iterator[ServedEndpoint]:
    """Serve ``app`` under a real uvicorn in a thread, FROM a pre-bound socket.

    The server is handed the held socket (never a port number) and runs with lifespan forced on.
    Exit drives a real lifespan shutdown and releases the port.

    Args:
        app: The ASGI application to serve.
        port: A held port to serve from; if ``None`` a fresh :class:`LoopbackPort` is owned and
            closed by this helper.
        startup_timeout_s: How long to wait for the server to report started.

    Yields:
        The served endpoint.

    Raises:
        ServerBindError: If binding a fresh port fails.
        ServerStartupTimeout: If the thread is alive but not started within the budget; the held
            port is released at the raise.
        ServerThreadCrashed: If the server thread ends before reporting started; raised promptly,
            carrying the app's own error text, with the held port released.
    """
    with _held_port(port) as held:
        server_thread = _UvicornServerThread(app, held)
        server_thread.start(startup_timeout_s)
        try:
            yield held.served_endpoint()
        finally:
            server_thread.stop()


@contextlib.contextmanager
def serve_http(
    handler_class: type[socketserver.BaseRequestHandler],
    *,
    port: LoopbackPort | None = None,
) -> Iterator[ServedEndpoint]:
    """Serve a stdlib ``http.server`` handler in a thread, FROM a pre-bound socket.

    Args:
        handler_class: The request handler class to serve.
        port: A held port to serve from; if ``None`` a fresh :class:`LoopbackPort` is owned and
            closed by this helper.

    Yields:
        The served endpoint.

    Raises:
        ServerBindError: If binding a fresh port fails.
    """
    with _held_port(port) as held:
        # bind_and_activate=False: the server constructs an UNBOUND socket of its own, which is
        # swapped for the held one before activation — the stdlib never binds a port number.
        server = http.server.HTTPServer((held.host, held.port), handler_class, bind_and_activate=False)
        server.socket.close()
        server.socket = held.socket
        # What HTTPServer.server_bind would have recorded, had it bound.
        server.server_name = held.host
        server.server_port = held.port
        server.server_activate()
        thread = threading.Thread(
            target=server.serve_forever, name=f"serve_http {held.base_url}", daemon=True
        )
        thread.start()
        try:
            yield held.served_endpoint()
        finally:
            server.shutdown()
            thread.join(timeout=_SHUTDOWN_JOIN_TIMEOUT_S)


__all__ = [
    "DEFAULT_STARTUP_TIMEOUT_S",
    "KERNEL_ASSIGNED_PORT",
    "LOOPBACK_HOST",
    "AsgiApplication",
    "LoopbackPort",
    "ServedEndpoint",
    "ServerBindError",
    "ServerStartError",
    "ServerStartupTimeout",
    "ServerThreadCrashed",
    "serve_asgi",
    "serve_http",
]
