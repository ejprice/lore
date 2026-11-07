"""A store BOUNCE without touching the store: an in-process TCP proxy in front of the TEST store.

Packet SDK3 (``docs/plans/v2/sdk3-python-sdk-3-migration.md`` §3 "Contract index"). Finding #576 is
about what a long-lived connection sees after the store restarts. Restarting the shared TEST store
(``:18000``) would take every concurrent test session down with it, and production (``:18500``) is
off limits, so the contract restarts nothing. Instead every connection under test reaches the TEST
store through this proxy, and the proxy plays the restart as the CLIENT sees it:

* :meth:`StoreBounceProxy.go_down` stops listening (a new connect is REFUSED, exactly as against a
  stopped container) and severs every live socket. The upstream half closes too, so the engine
  drops that session, just as a restarted engine has no memory of it.
* :meth:`StoreBounceProxy.come_up` listens again on the SAME port, so a client that reconnects to
  the address it was built with reaches the store again.

Two sever shapes, because a real restart can produce either and the SDK classifies them apart:

* :attr:`SeverMode.ABORT` drops the TCP connection with no WebSocket close frame — the #576 text
  ("no close frame received or sent").
* :attr:`SeverMode.CLOSE_FRAME` first writes a server close frame with no status code (``0x88 0x00``),
  the shape ``podman restart`` produced when measured on 3.3.5 (research doc §D-4: SDK 2.0 saw
  ``ConnectionClosedOK: received 1005 (no status received)``). Only safe on an IDLE socket: a frame
  written in the middle of a forwarded server frame would corrupt it, so the racing-call pins use
  :attr:`SeverMode.ABORT`.

A SLOW STORE, without a slow statement (round 3, operator ruling R5 rider 3):
:meth:`StoreBounceProxy.hold_next_response` arms a one-shot hold — the NEXT server-to-client chunk on
any socket is held back ``seconds`` before it is forwarded (and everything after it on that socket
queues behind it, so frame order is preserved). The
engine finished long ago; the CLIENT simply sees its reply arrive ``seconds`` late. That is how the
long-operation pins make a startup DDL "take" longer than the default request timeout without depending
on how long any real DDL takes on this box.

The proxy also COUNTS, so a pin can prove its own premise (a positive control): how many sockets it
accepted, how many it severed, and how many are live now. A recovery pin that never saw its
connections cut would pass for the wrong reason.

BOUND, stated: this is a client-side model of a restart. It does not reproduce what a restarted
ENGINE loses beyond the session (nothing else matters to these pins: the database persists across a
real restart too), and it does not model a half-open socket whose peer vanished without a FIN/RST
(that is what the SDK 3.0 keepalive ping exists for, and it is out of these pins' reach).
"""

from __future__ import annotations

import asyncio
import contextlib
import enum
from dataclasses import dataclass, field
from urllib.parse import urlsplit

# A server WebSocket close frame (FIN + opcode 0x8) with an empty payload: "no status code".
_CLOSE_FRAME_NO_STATUS = b"\x88\x00"

# How long teardown waits for a severed pipe's copy tasks and the listener to finish.
_TEARDOWN_TIMEOUT_SECONDS = 5.0

# The read size of one forwarding hop.
_FORWARD_CHUNK_BYTES = 65536

# The loopback interface the proxy listens on.
_LISTEN_HOST = "127.0.0.1"


class SeverMode(enum.Enum):
    """How :meth:`StoreBounceProxy.go_down` cuts a live socket (see the module docstring)."""

    ABORT = "abort"
    CLOSE_FRAME = "close_frame"


@dataclass
class _Pipe:
    """One proxied client socket and its upstream twin."""

    client_writer: asyncio.StreamWriter
    upstream_writer: asyncio.StreamWriter
    tasks: list[asyncio.Task[None]] = field(default_factory=list)


@dataclass
class StoreBounceProxy:
    """A TCP proxy to ``upstream_url``'s host:port that can play a store restart (module docstring)."""

    upstream_url: str
    accepted_total: int = 0
    severed_total: int = 0
    held_total: int = 0
    _hold_seconds: float | None = None
    _port: int = 0
    _server: asyncio.base_events.Server | None = None
    _pipes: list[_Pipe] = field(default_factory=list)

    @property
    def upstream_host_port(self) -> tuple[str, int]:
        """The TEST store's host and port, read from its RPC URL."""
        parts = urlsplit(self.upstream_url)
        if parts.hostname is None or parts.port is None:
            raise ValueError(f"cannot proxy {self.upstream_url!r}: it names no host:port")
        return parts.hostname, parts.port

    @property
    def url(self) -> str:
        """The RPC URL a client uses to reach the store THROUGH the proxy."""
        if not self._port:
            raise RuntimeError("the proxy has not been started")
        parts = urlsplit(self.upstream_url)
        return f"{parts.scheme}://{_LISTEN_HOST}:{self._port}{parts.path}"

    @property
    def live_pipes(self) -> int:
        """Proxied sockets currently open (not yet severed or closed by either end)."""
        return sum(1 for pipe in self._pipes if not pipe.client_writer.is_closing())

    @property
    def is_up(self) -> bool:
        """Whether the proxy is accepting connections."""
        return self._server is not None

    async def start(self) -> None:
        """Listen on an ephemeral loopback port."""
        await self._listen(port=0)

    async def come_up(self) -> None:
        """Listen again on the SAME port (the store is back)."""
        if self._server is not None:
            return
        await self._listen(port=self._port)

    async def go_down(self, mode: SeverMode = SeverMode.ABORT) -> int:
        """Stop listening and sever every live socket; returns how many were severed."""
        server, self._server = self._server, None
        if server is not None:
            server.close()
        severed = 0
        for pipe in self._pipes:
            if pipe.client_writer.is_closing():
                continue
            severed += 1
            self._sever(pipe, mode)
        self.severed_total += severed
        await self._reap_pipes()
        if server is not None:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(server.wait_closed(), _TEARDOWN_TIMEOUT_SECONDS)
        return severed

    async def bounce(self, *, down_seconds: float, mode: SeverMode = SeverMode.ABORT) -> int:
        """Go down, stay down ``down_seconds``, come back up; returns how many sockets were severed."""
        severed = await self.go_down(mode)
        await asyncio.sleep(down_seconds)
        await self.come_up()
        return severed

    def hold_next_response(self, seconds: float) -> None:
        """Arm a one-shot hold: the next server-to-client chunk waits ``seconds`` (module docstring)."""
        self._hold_seconds = seconds

    async def close(self) -> None:
        """Teardown: go down for good."""
        await self.go_down(SeverMode.ABORT)

    async def _listen(self, *, port: int) -> None:
        self._server = await asyncio.start_server(self._handle, _LISTEN_HOST, port, reuse_address=True)
        self._port = self._server.sockets[0].getsockname()[1]

    async def _handle(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter) -> None:
        host, port = self.upstream_host_port
        try:
            upstream_reader, upstream_writer = await asyncio.open_connection(host, port)
        except OSError:
            client_writer.transport.abort()
            return
        self.accepted_total += 1
        pipe = _Pipe(client_writer=client_writer, upstream_writer=upstream_writer)
        pipe.tasks = [
            asyncio.create_task(self._forward(client_reader, upstream_writer, pipe)),
            asyncio.create_task(self._forward(upstream_reader, client_writer, pipe)),
        ]
        self._pipes.append(pipe)

    async def _forward(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, pipe: _Pipe) -> None:
        """Copy one direction until either end goes away, then close both ends."""
        try:
            while True:
                chunk = await reader.read(_FORWARD_CHUNK_BYTES)
                if not chunk:
                    break
                if writer is pipe.client_writer and self._hold_seconds is not None:
                    seconds, self._hold_seconds = self._hold_seconds, None
                    self.held_total += 1
                    await asyncio.sleep(seconds)
                writer.write(chunk)
                await writer.drain()
        except OSError, asyncio.IncompleteReadError:
            pass
        finally:
            for end in (pipe.client_writer, pipe.upstream_writer):
                if not end.is_closing():
                    end.close()

    @staticmethod
    def _sever(pipe: _Pipe, mode: SeverMode) -> None:
        if mode is SeverMode.CLOSE_FRAME:
            pipe.client_writer.write(_CLOSE_FRAME_NO_STATUS)
            pipe.client_writer.close()
        else:
            pipe.client_writer.transport.abort()
        pipe.upstream_writer.transport.abort()

    async def _reap_pipes(self) -> None:
        """Wait for severed pipes' copy tasks to finish; drop closed pipes from the live list."""
        pending = [task for pipe in self._pipes for task in pipe.tasks if not task.done()]
        if pending:
            await asyncio.wait(pending, timeout=_TEARDOWN_TIMEOUT_SECONDS)
        self._pipes = [pipe for pipe in self._pipes if not pipe.client_writer.is_closing()]
