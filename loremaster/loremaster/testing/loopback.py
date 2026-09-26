"""ONE race-free loopback listener, and a server start that NAMES its failure (finding #466).

The retired pattern bound ``127.0.0.1:0``, read the port, CLOSED the socket, then handed the
NUMBER to a server that bound it again — a window in which any other process could take the
port. Every helper here instead HOLDS the kernel-assigned socket for the whole context and
serves FROM it, so no specific (non-zero) port is ever bound.

Contract: ``loremaster/tests/test_loopback_serving.py`` and
``skills/lore-deploy/tests/test_loopback_home.py``.
"""

from __future__ import annotations

import contextlib
import socketserver
from collections.abc import Awaitable, Callable, Iterator
from dataclasses import dataclass
from socket import socket as TcpSocket  # noqa: N812 — distinguishes the type from the .socket attribute
from types import TracebackType

LOOPBACK_HOST: str = "127.0.0.1"
"""The only host the helpers bind by default — loopback, never a routable interface."""

DEFAULT_STARTUP_TIMEOUT_S: float = 15.0
"""How long :func:`serve_asgi` waits for the server to report started before raising
:class:`ServerStartupTimeout`. The value is measure-then-tune (#466 contract report §E); callers
pass ``startup_timeout_s`` to override it without editing this module."""

_NOT_IMPLEMENTED_MESSAGE: str = "Not yet implemented"

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
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)

    def listen(self) -> None:
        """Start listening on the held socket so connects are accepted."""
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)

    def close(self) -> None:
        """Close the held socket, releasing the port."""
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)

    def __enter__(self) -> LoopbackPort:
        """Enter the context, returning this held port."""
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the held socket on exit, whatever ended the context."""
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)


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
    raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)


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
    raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)


__all__ = [
    "DEFAULT_STARTUP_TIMEOUT_S",
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
