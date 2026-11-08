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

Round 4 (MP3, the index-transaction leg): :meth:`StoreBounceProxy.hold_reply_to_large_request` arms a
one-shot hold keyed on the REQUEST instead of on time: once one socket has carried at least ``min_bytes``
client-to-server since arming, the NEXT server-to-client chunk on THAT socket is held. A file's index
write is one request of megabytes (the per-row vectors), so this holds the reply to exactly that request
on a connection whose other traffic is small — it keys on SIZE, never on the request's text, so it works
whatever the WebSocket compression or the SDK's encoding. Unlike the time-based hold it is FRAME-AWARE:
while it is active the server-to-client stream is parsed into WebSocket frames and only DATA frames are held
— CONTROL frames (the pong to the SDK's keepalive ping, ``ping_interval=30`` / ``ping_timeout=10``) pass
straight through, as they do from a real engine that is slow to answer a query. Holding the whole TCP stream
instead starves the pong and the SDK closes the socket ~10 s after its next ping (measured 2026-11-07: a
32 s whole-stream hold on a connection opened at boot ended "WebSocket connection closed before a response
was received"). ASSUMPTION, stated: the hold starts at a server frame boundary — true when it triggers, since
the server is idle while the client is still sending the large request.

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
import socket
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from loremaster.testing.loopback import LoopbackPort

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
    # Client-to-server bytes since a large-request hold was armed, and whether this pipe's next reply is held.
    sent_since_armed: int = 0
    hold_next_reply: float | None = None
    # Frame-aware hold state (server-to-client): unparsed bytes, held data frames, whether holding.
    frame_buffer: bytearray = field(default_factory=bytearray)
    held_frames: list[bytes] = field(default_factory=list)
    holding_frames: bool = False


@dataclass
class StoreBounceProxy:
    """A TCP proxy to ``upstream_url``'s host:port that can play a store restart (module docstring)."""

    upstream_url: str
    accepted_total: int = 0
    severed_total: int = 0
    held_total: int = 0
    # Bytes forwarded client-to-store, all sockets (a pin can tell "sent nothing" from "sent, not held").
    to_store_bytes: int = 0
    _hold_seconds: float | None = None
    _large_request_hold: tuple[int, float] | None = None
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
        """Listen on an ephemeral loopback port, served FROM a held :class:`LoopbackPort` (#466)."""
        held = LoopbackPort(_LISTEN_HOST)
        try:
            await self._listen_held(held)
        except BaseException:
            held.close()
            raise

    async def come_up(self) -> None:
        """Listen again on the SAME port (the store is back)."""
        if self._server is not None:
            return
        await self._relisten_same_port()

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

    def hold_reply_to_large_request(self, *, min_bytes: int, seconds: float) -> None:
        """Arm a one-shot hold on the reply to the next request of >= ``min_bytes`` (module docstring)."""
        for pipe in self._pipes:
            pipe.sent_since_armed = 0
        self._large_request_hold = (min_bytes, seconds)

    async def close(self) -> None:
        """Teardown: go down for good."""
        await self.go_down(SeverMode.ABORT)

    async def _listen_held(self, held: LoopbackPort) -> None:
        """Serve FROM ``held``'s already-bound socket: ``start_server`` is handed the socket, never a number,
        so it binds nothing and no other session can take the port between bind and listen (#466).

        The served socket gets ``SO_REUSEADDR`` (``start_server`` sets it only in host/port mode): the
        sockets this listener accepts inherit it, and :meth:`_relisten_same_port` can re-bind the port only
        while every accepted socket still lingering on it carries it too (measured R43: without it,
        ``come_up`` after a ``go_down`` in EITHER sever mode raised ``EADDRINUSE``). From here the server
        owns the socket and closes it in :meth:`go_down`. The #466 scan still sees the ``start_server`` VERB
        here, so this function carries its own ``_EXEMPT_SITES`` row.
        """
        held.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server = await asyncio.start_server(self._handle, sock=held.socket)
        self._port = held.port

    async def _relisten_same_port(self) -> None:
        """Re-bind the port NUMBER :meth:`start` was given, after :meth:`go_down` closed the listener.

        A bounce must come back on the address its clients already hold, so this is #466's
        close-then-re-bind shape on purpose, exempted with its evidence and re-open trigger
        (``_EXEMPT_SITES`` in ``test_no_raw_listener_in_test_trees.py``). A collision is ``EADDRINUSE``
        raised LOUDLY by ``start_server``, never a listener on a different port.
        """
        self._server = await asyncio.start_server(self._handle, _LISTEN_HOST, self._port, reuse_address=True)

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
                if writer is pipe.upstream_writer:
                    self._note_sent(pipe, len(chunk))
                if writer is pipe.client_writer and pipe.hold_next_reply is not None:
                    self._start_frame_hold(pipe)
                if writer is pipe.client_writer and pipe.holding_frames:
                    pipe.frame_buffer.extend(chunk)
                    self._route_frames(pipe)
                    await writer.drain()
                    continue
                if writer is pipe.client_writer and pipe.frame_buffer:
                    chunk = bytes(pipe.frame_buffer) + chunk  # a partial frame left when the hold ended
                    pipe.frame_buffer.clear()
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

    def _note_sent(self, pipe: _Pipe, size: int) -> None:
        """Count client-to-store bytes; trigger an armed large-request hold on the pipe that crosses it."""
        self.to_store_bytes += size
        if self._large_request_hold is None:
            return
        pipe.sent_since_armed += size
        min_bytes, held_seconds = self._large_request_hold
        if pipe.sent_since_armed >= min_bytes:
            self._large_request_hold = None
            pipe.hold_next_reply = held_seconds

    def _start_frame_hold(self, pipe: _Pipe) -> None:
        """Begin holding this pipe's server DATA frames; release them ``hold_next_reply`` seconds from now."""
        seconds, pipe.hold_next_reply = pipe.hold_next_reply or 0.0, None
        self.held_total += 1
        pipe.holding_frames = True
        pipe.frame_buffer.clear()
        asyncio.get_running_loop().call_later(seconds, self._release_frames, pipe)

    @staticmethod
    def _frame_length(buffer: bytearray) -> int | None:
        """The byte length of the complete server WebSocket frame at the head of ``buffer`` (servers never
        mask), or ``None`` while it is incomplete."""
        if len(buffer) < 2:
            return None
        length, header = buffer[1] & 0x7F, 2
        if length == 126:
            if len(buffer) < 4:
                return None
            length, header = int.from_bytes(buffer[2:4], "big"), 4
        elif length == 127:
            if len(buffer) < 10:
                return None
            length, header = int.from_bytes(buffer[2:10], "big"), 10
        total = header + length
        return total if len(buffer) >= total else None

    def _route_frames(self, pipe: _Pipe) -> None:
        """While holding: forward every complete CONTROL frame now, keep every complete DATA frame back."""
        while (size := self._frame_length(pipe.frame_buffer)) is not None:
            frame = bytes(pipe.frame_buffer[:size])
            del pipe.frame_buffer[:size]
            if frame[0] & 0x08:
                pipe.client_writer.write(frame)
            else:
                pipe.held_frames.append(frame)

    @staticmethod
    def _release_frames(pipe: _Pipe) -> None:
        """The hold is over: forward the held data frames in order; later bytes forward as they arrive."""
        pipe.holding_frames = False
        if pipe.client_writer.is_closing():
            return
        for frame in pipe.held_frames:
            pipe.client_writer.write(frame)
        pipe.held_frames.clear()
        if pipe.frame_buffer:
            pipe.client_writer.write(bytes(pipe.frame_buffer))
            pipe.frame_buffer.clear()

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
