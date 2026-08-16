#!/usr/bin/env python3
"""Packet-59 migration spike — measure the 3 `[inferred]` §6.6 gates against a REAL wire.

Spec: docs/design/2026-08-15-fastmcp-3x-migration.md §6.6 (items 1/2/3), §5b-C2,
the §5b Origin-ordering caveat, §5b-C3', and §9 FG1 (the in-memory blind spot).

Each of the 3 items is a GO/NO-GO fork the migration build depends on. This harness
proves each over a REAL uvicorn server on a TCP port driven by a real fastmcp.Client
and raw httpx (NEVER the in-memory transport — the in-memory path skips the ASGI
lifespan, so it would prove nothing about item 1: §6.2 / FG1). Every item carries a
POSITIVE and a NEGATIVE control (CLAUDE.md: "a probe needs a control").

    Item 1 — lifespan-apparatus DELETE (§6.6-1 / §5b-C2):
        Prove fastmcp enters the user `lifespan=` EXACTLY ONCE PER PROCESS at ASGI
        startup, ref-counted teardown correct, in stateful (served) mode, AND that
        lore's bespoke Origin/Bearer ASGI wrappers delegate the lifespan scope so it
        actually runs. GO => the ~150-LOC guard/interceptor can be deleted.

    Item 2 — Origin-ordering (§6.6-2 / §5b caveat):
        Prove whether fastmcp's `host_origin_protection` runs BEFORE the TokenVerifier
        (the packet-39 §8 R9 "zero outbound Google call" property). GO => it runs first.

    Item 3 — host_origin_protection closes the Host/DNS-rebinding gap (§6.6-3 / §5b-C3'):
        Prove the enabled guard REJECTS a spoofed Host header — a check lore does not
        have today (`transport_security` unset). GO => a security benefit to bank.

Re-run (fastmcp is NOT a lore dependency yet — this is measurement only):
    uv run --with 'fastmcp>=3.4,<4' --with uvicorn --with httpx \
        python scripts/fastmcp_migration_spike.py

Measured 2026-08-15 against fastmcp 3.4.7 / mcp 1.29.0 (isolated venv). Nothing under
loremaster/ or the lore package tree is imported or touched.
"""
from __future__ import annotations

import asyncio
import contextlib
import socket
import threading
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, Iterator, MutableMapping
from typing import Any, TypedDict
from urllib.parse import urlsplit

import httpx
import uvicorn
from fastmcp import Client, FastMCP
from fastmcp.client.auth import BearerAuth
from fastmcp.exceptions import ToolError  # noqa: F401  (kept for parity w/ prod trace seam)
from fastmcp.server.auth.auth import AccessToken, TokenVerifier

# --------------------------------------------------------------------------- #
# ASGI wrappers — FAITHFUL reproductions of lore's bespoke middleware.
# The load-bearing clause is the non-HTTP (lifespan) PASS-THROUGH, verbatim from
# loremaster/loremaster/auth.py:
#   BearerAuthMiddleware.__call__      (auth.py:228-237, pass-through at :230-232)
#   OriginValidationMiddleware.__call__(auth.py:310-319, pass-through at :312-314)
# Both: `if scope.get("type") != "http": await self._app(scope, receive, send); return`
# That clause is item 1(b): the wrapper delegates the ASGI `lifespan` scope to the
# inner fastmcp http_app so the user lifespan actually runs at process startup.
# --------------------------------------------------------------------------- #
_Scope = MutableMapping[str, Any]
_Message = MutableMapping[str, Any]
_Receive = Callable[[], Awaitable[_Message]]
_Send = Callable[[_Message], Awaitable[None]]
_ASGIApp = Callable[[_Scope, _Receive, _Send], Awaitable[None]]

_HTTP = "http"
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


class OriginValidationMiddleware:
    """Faithful repro of lore's Origin allow-list wrapper (auth.py:272)."""

    def __init__(self, app: _ASGIApp, allowed_origins: Iterable[str] | None = None) -> None:
        self._app = app
        self._allowed_origins = frozenset(allowed_origins or ())

    async def __call__(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        if scope.get("type") != _HTTP:              # <-- lifespan pass-through (item 1b)
            await self._app(scope, receive, send)
            return
        origin = self._origin(scope)
        if not self._is_allowed(origin):
            await self._reject(send, 403, b"Forbidden: disallowed Origin")
            return
        await self._app(scope, receive, send)

    @staticmethod
    def _origin(scope: _Scope) -> str | None:
        headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
        for name, value in headers:
            if name.lower() == b"origin":
                return value.decode("latin-1")
        return None

    def _is_allowed(self, origin: str | None) -> bool:
        if not origin:
            return True
        if origin in self._allowed_origins:
            return True
        try:
            return urlsplit(origin).hostname in _LOOPBACK_HOSTS
        except ValueError:
            return False

    @staticmethod
    async def _reject(send: _Send, status: int, body: bytes) -> None:
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"text/plain; charset=utf-8")]})
        await send({"type": "http.response.body", "body": body})


class BearerAuthMiddleware:
    """Faithful repro of lore's Bearer wrapper (auth.py:208). Verifier: token->identity."""

    def __init__(self, app: _ASGIApp, verify: Callable[[str], str | None]) -> None:
        self._app = app
        self._verify = verify

    async def __call__(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        if scope.get("type") != _HTTP:              # <-- lifespan pass-through (item 1b)
            await self._app(scope, receive, send)
            return
        token = self._bearer(scope)
        if token is None or self._verify(token) is None:
            await send({"type": "http.response.start", "status": 401,
                        "headers": [(b"www-authenticate", b'Bearer realm="loremaster"'),
                                    (b"content-type", b"text/plain; charset=utf-8")]})
            await send({"type": "http.response.body", "body": b"Unauthorized"})
            return
        await self._app(scope, receive, send)

    @staticmethod
    def _bearer(scope: _Scope) -> str | None:
        headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
        for name, value in headers:
            if name.lower() == b"authorization":
                decoded = value.decode("latin-1")
                if decoded.lower().startswith("bearer "):
                    return decoded[len("bearer "):]
                return None
        return None


class NaiveLifespanEatingMiddleware:
    """NEGATIVE control for item 1(b): a broken wrapper that INTERCEPTS the ASGI
    lifespan protocol and DOES NOT delegate it to the inner app. It satisfies
    uvicorn's `lifespan="on"` (responds startup/shutdown complete itself) but the
    inner fastmcp lifespan never runs -> the user lifespan body is never entered.
    This is the exact failure a faithful pass-through prevents."""

    def __init__(self, app: _ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        if scope.get("type") == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        else:
            await self._app(scope, receive, send)


# --------------------------------------------------------------------------- #
# uvicorn-on-a-TCP-port harness (REAL transport, never in-memory).
# --------------------------------------------------------------------------- #
def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = int(s.getsockname()[1])
    s.close()
    return port


@contextlib.contextmanager
def serve(app: _ASGIApp, port: int) -> Iterator[str]:
    """Run `app` under uvicorn on 127.0.0.1:port in a daemon thread. `lifespan="on"`
    FORCES the ASGI lifespan protocol (a server that cannot run it fails loudly rather
    than silently skipping it — the FG1 guard). Yields the base URL; on exit drives a
    real shutdown so lifespan teardown runs."""
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error",
                            lifespan="on")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        for _ in range(400):
            if server.started:
                break
            time.sleep(0.025)
        else:
            raise RuntimeError("uvicorn did not report started within 10s")
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=15)


async def _wire_session(url: str, tool: str, token: str | None = None) -> Any:
    """One FULL wire MCP session: connect -> initialize -> call `tool` -> close.
    Each `async with Client(...)` is a distinct wire session over streamable-HTTP."""
    auth = BearerAuth(token) if token else None
    endpoint = url if url.rstrip("/").endswith("/mcp") else f"{url.rstrip('/')}/mcp"
    async with Client(endpoint, auth=auth) as client:
        result = await client.call_tool(tool, {})
        return result.data


async def _concurrent_sessions(url: str, tool: str, n: int, token: str | None = None) -> list[Any]:
    """N distinct wire sessions opened CONCURRENTLY in one event loop — the real
    multi-client condition under which a per-session lifespan re-entry would show."""
    return await asyncio.gather(*[_wire_session(url, tool, token) for _ in range(n)])


# ============================================================================ #
# ITEM 1 — lifespan enters EXACTLY ONCE PER PROCESS, ref-counted teardown,
#          bespoke wrappers delegate the lifespan scope.  (§6.6-1 / §5b-C2)
# ============================================================================ #
class _Item1Counters(TypedDict):
    """Oracle counters for item 1 — heterogeneous values, so a precise TypedDict (not a
    ``dict[str, int | None]`` that would make ``+= 1`` and the str assignment both errors)."""

    enter: int
    exit: int
    boot_id: str | None


def item1() -> dict[str, Any]:  # noqa: PLR0915 - measurement harness: 3 lifecycles + controls inline
    print("\n" + "=" * 72)
    print("ITEM 1 — lifespan once-per-process + ref-counted teardown + wrapper delegation")
    print("=" * 72)

    # Oracle counters mutated ONLY by the user lifespan body.
    counters: _Item1Counters = {"enter": 0, "exit": 0, "boot_id": None}
    boot_seq = {"n": 0}

    @contextlib.asynccontextmanager
    async def heavy_lifespan(server: FastMCP) -> AsyncIterator[dict[str, str | None]]:
        # This stands in for lore's ~150-LOC eager heavy build (watcher/reconcile).
        counters["enter"] += 1
        boot_seq["n"] += 1
        counters["boot_id"] = f"boot-{boot_seq['n']}"
        try:
            yield {"boot_id": counters["boot_id"]}
        finally:
            counters["exit"] += 1

    def build_app(wrapper: str) -> tuple[_ASGIApp, Any]:
        mcp = FastMCP(name="spike59-item1", version="59.0.0", lifespan=heavy_lifespan)

        @mcp.tool
        def boot_probe() -> str:
            """Return the boot id set by the (once-per-process) lifespan body."""
            return counters["boot_id"] or "NO-LIFESPAN-RAN"

        inner = mcp.http_app(path="/mcp", stateless_http=False)  # SERVED/stateful mode
        if wrapper == "faithful":
            # Production stack: Bearer(Origin(http_app)) — both delegate lifespan.
            app: _ASGIApp = OriginValidationMiddleware(inner)
            app = BearerAuthMiddleware(app, verify=lambda t: "dev" if t == "tok-1" else None)
            return app, inner.lifespan
        if wrapper == "naive":
            return NaiveLifespanEatingMiddleware(inner), inner.lifespan
        raise ValueError(wrapper)

    out: dict[str, Any] = {}

    # --- Lifecycle 1: faithful wrappers, N wire sessions, ONE process ---------
    port = _free_port()
    app, _ = build_app("faithful")
    n_sessions = 4
    boot_ids: list[str] = []
    with serve(app, port) as url:
        eager_enter = counters["enter"]      # measured BEFORE any request
        for _ in range(n_sessions):          # sequential wire sessions
            boot_ids.append(asyncio.run(_wire_session(url, "boot_probe", token="tok-1")))
        enter_after_sessions = counters["enter"]
        # CONCURRENT wire sessions — the real multi-client condition for the ref-count.
        concurrent_boot_ids = asyncio.run(_concurrent_sessions(url, "boot_probe", 4, token="tok-1"))
        enter_after_concurrent = counters["enter"]
    exit_after_shutdown = counters["exit"]
    print(f"[faithful/lifecycle-1] eager enter (pre-request) : {eager_enter}")
    print(f"[faithful/lifecycle-1] {n_sessions} SEQUENTIAL wire sessions boot_ids : {boot_ids}")
    print(f"[faithful/lifecycle-1] enter after sequential : {enter_after_sessions}")
    print(f"[faithful/lifecycle-1] 4 CONCURRENT wire sessions boot_ids : {concurrent_boot_ids}")
    print(f"[faithful/lifecycle-1] enter after concurrent : {enter_after_concurrent}")
    print(f"[faithful/lifecycle-1] exit count after shutdown : {exit_after_shutdown}")
    out["eager_enter"] = eager_enter
    out["enter_after_sessions"] = enter_after_sessions
    out["enter_after_concurrent"] = enter_after_concurrent
    out["distinct_boot_ids"] = sorted(set(boot_ids) | set(concurrent_boot_ids))
    out["exit_after_shutdown"] = exit_after_shutdown

    # --- Lifecycle 2 (POSITIVE CONTROL: the counter WOULD move on re-fire) ----
    port2 = _free_port()
    app2, _ = build_app("faithful")
    with serve(app2, port2) as url:
        boot2 = asyncio.run(_wire_session(url, "boot_probe", token="tok-1"))
    print(f"[faithful/lifecycle-2] enter after a 2nd process lifecycle : {counters['enter']}"
          f"  boot_id={boot2}  (control: instrument is LIVE, not stuck)")
    out["enter_after_lifecycle2"] = counters["enter"]
    out["lifecycle2_boot_id"] = boot2

    # --- NEGATIVE CONTROL: naive wrapper drops the lifespan scope -------------
    enter_before_naive = counters["enter"]
    port3 = _free_port()
    app3, _ = build_app("naive")
    naive_boot = None
    with serve(app3, port3) as url:
        with contextlib.suppress(Exception):
            naive_boot = asyncio.run(_wire_session(url, "boot_probe", token="tok-1"))
    print(f"[naive/neg-control] enter before={enter_before_naive} after={counters['enter']} "
          f"(delta {counters['enter'] - enter_before_naive}); tool saw boot_id={naive_boot!r}")
    out["naive_enter_delta"] = counters["enter"] - enter_before_naive
    out["naive_tool_boot_id"] = naive_boot

    # --- Verdict ---------------------------------------------------------------
    go = (
        out["eager_enter"] == 1
        and out["enter_after_sessions"] == 1               # once per process across N sequential
        and out["enter_after_concurrent"] == 1             # still once under CONCURRENT sessions
        and out["distinct_boot_ids"] == ["boot-1"]         # one lifespan served all sessions
        and out["exit_after_shutdown"] == 1                # ref-counted teardown correct
        and out["enter_after_lifecycle2"] == 2             # control: counter moves on re-fire
        and out["naive_enter_delta"] == 0                  # neg: no delegation => no lifespan
    )
    out["verdict"] = "GO" if go else "NO-GO"
    print(f"\nITEM 1 VERDICT: {out['verdict']}")
    return out


# ============================================================================ #
# ITEM 2 — does host_origin_protection run BEFORE the TokenVerifier?  (§6.6-2)
# ============================================================================ #
def item2() -> dict[str, Any]:
    print("\n" + "=" * 72)
    print("ITEM 2 — Origin/Host guard ordering vs the TokenVerifier (zero-outbound property)")
    print("=" * 72)

    verify_calls = {"n": 0}

    class CountingVerifier(TokenVerifier):
        def __init__(self, token: str, client_id: str, scopes: list[str]) -> None:
            super().__init__()
            self._token, self._client_id, self._scopes = token, client_id, scopes

        async def verify_token(self, token: str) -> AccessToken | None:
            # In real packet-39 OAuth, the OUTBOUND Google tokeninfo POST happens HERE.
            verify_calls["n"] += 1
            if token == self._token:
                return AccessToken(token=token, client_id=self._client_id, scopes=self._scopes)
            return None

    port = _free_port()
    mcp = FastMCP(name="spike59-item2", version="59.0.0",
                  auth=CountingVerifier("good-token", "principal-xyz", ["read"]))

    @mcp.tool
    def ping() -> str:
        return "pong"

    # Strict host/origin protection ON; Host allowlist includes our real bind so a
    # legitimate request passes the Host check and reaches the auth layer.
    app = mcp.http_app(path="/mcp", stateless_http=False, host_origin_protection=True,
                       allowed_hosts=[f"127.0.0.1:{port}", "127.0.0.1"])

    init_body = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "probe", "version": "0"}},
    }
    base_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer good-token",   # VALID token throughout item 2
    }

    def post(extra_headers: dict[str, str]) -> httpx.Response:
        with httpx.Client() as c:
            return c.post(f"http://127.0.0.1:{port}/mcp", json=init_body,
                          headers={**base_headers, **extra_headers}, timeout=10)

    out: dict[str, Any] = {}
    with serve(app, port):
        # PROBE: bad Origin + VALID token. If the guard is outermost, the request is
        # rejected (403) BEFORE the verifier is ever consulted (verify_calls stays 0).
        verify_calls["n"] = 0
        r_bad_origin = post({"Origin": "http://evil.example"})
        bad_origin_status = r_bad_origin.status_code
        bad_origin_body = r_bad_origin.text.strip()[:60]
        bad_origin_verify = verify_calls["n"]
        print(f"[probe]     bad Origin + valid token -> status={bad_origin_status} "
              f"body={bad_origin_body!r} verify_token_calls={bad_origin_verify}  (zero => guard ran first)")
        out["bad_origin_body"] = bad_origin_body

        # POSITIVE CONTROL: loopback Origin (allowed) + VALID token. Origin passes,
        # so the request reaches auth and the verifier IS consulted (>=1) — proves the
        # counter is live (a 0 in the probe is meaningful, not a stuck instrument).
        verify_calls["n"] = 0
        r_ok = post({"Origin": f"http://127.0.0.1:{port}"})
        ok_status = r_ok.status_code
        ok_verify = verify_calls["n"]
        print(f"[pos-ctrl]  good Origin + valid token -> status={ok_status} "
              f"verify_token_calls={ok_verify}  (>=1 => verifier reachable & live)")

        # NEG CONTROL (auth reached & rejects): good Origin + BAD token -> 401.
        verify_calls["n"] = 0
        r_badtok = post({"Origin": f"http://127.0.0.1:{port}",
                         "Authorization": "Bearer WRONG"})
        badtok_status = r_badtok.status_code
        badtok_verify = verify_calls["n"]
        print(f"[neg-ctrl]  good Origin + BAD token  -> status={badtok_status} "
              f"verify_token_calls={badtok_verify}  (401 => auth is the inner gate)")

    out.update(bad_origin_status=bad_origin_status, bad_origin_verify=bad_origin_verify,
               ok_status=ok_status, ok_verify=ok_verify,
               badtok_status=badtok_status, badtok_verify=badtok_verify)

    go = (bad_origin_status == 403 and bad_origin_verify == 0     # guard first, zero outbound
          and ok_verify >= 1                                     # verifier live when origin ok
          and badtok_status == 401)                              # auth is the inner gate
    out["verdict"] = "GO" if go else "NO-GO"
    out["ordering"] = ("guard-BEFORE-verifier" if bad_origin_verify == 0 and bad_origin_status == 403
                       else "verifier-before-or-with-guard")
    print(f"\nITEM 2 VERDICT: {out['verdict']}  ({out['ordering']})")
    return out


# ============================================================================ #
# ITEM 3 — enabled host_origin_protection REJECTS a spoofed Host header. (§6.6-3)
# ============================================================================ #
def item3() -> dict[str, Any]:
    print("\n" + "=" * 72)
    print("ITEM 3 — host_origin_protection rejects a spoofed Host (DNS-rebinding gap)")
    print("=" * 72)

    def build(protection: bool) -> Any:
        mcp = FastMCP(name="spike59-item3", version="59.0.0")

        @mcp.tool
        def ping() -> str:
            return "pong"

        return mcp.http_app(path="/mcp", stateless_http=False,
                            host_origin_protection=protection)

    init_body = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "probe", "version": "0"}},
    }
    accept = {"Content-Type": "application/json",
              "Accept": "application/json, text/event-stream"}

    def post(port: int, host_header: str | None) -> httpx.Response:
        headers = dict(accept)
        if host_header is not None:
            headers["Host"] = host_header
        with httpx.Client() as c:
            return c.post(f"http://127.0.0.1:{port}/mcp", json=init_body,
                          headers=headers, timeout=10)

    out: dict[str, Any] = {}

    # --- Protection ON (the migration BENEFIT) --------------------------------
    port_on = _free_port()
    with serve(build(True), port_on):
        r_spoof_on = post(port_on, "evil.example")                     # PROBE
        spoof_on, spoof_on_body = r_spoof_on.status_code, r_spoof_on.text.strip()[:40]
        legit_on = post(port_on, f"127.0.0.1:{port_on}").status_code   # POS CONTROL
    print(f"[protection=ON ] spoofed Host 'evil.example' -> status={spoof_on} "
          f"body={spoof_on_body!r}  (421 => REJECTED)")
    print(f"[protection=ON ] legit   Host '127.0.0.1:{port_on}' -> status={legit_on}  "
          f"(not 421 => guard lets legit through)")

    # --- Protection OFF (today's pre-migration state — the NEGATIVE CONTROL) ---
    port_off = _free_port()
    with serve(build(False), port_off):
        spoof_off = post(port_off, "evil.example").status_code
    print(f"[protection=OFF] spoofed Host 'evil.example' -> status={spoof_off}  "
          f"(not 421 => ACCEPTED, the gap that exists today)")

    out.update(spoof_on=spoof_on, spoof_on_body=spoof_on_body, legit_on=legit_on, spoof_off=spoof_off)
    go = (spoof_on == 421 and legit_on != 421 and spoof_off != 421)
    out["verdict"] = "GO" if go else "NO-GO"
    print(f"\nITEM 3 VERDICT: {out['verdict']}")
    return out


def main() -> None:
    import importlib.metadata as md

    import fastmcp
    print(f"fastmcp=={fastmcp.__version__}  mcp=={md.version('mcp')}  "
          f"starlette=={md.version('starlette')}  uvicorn=={md.version('uvicorn')}  "
          f"httpx=={md.version('httpx')}")
    r1 = item1()
    r2 = item2()
    r3 = item3()
    print("\n" + "#" * 72)
    print("SUMMARY")
    print("#" * 72)
    print(f"ITEM 1 (lifespan once-per-process / delete guard) : {r1['verdict']}")
    print(f"ITEM 2 (guard before TokenVerifier)               : {r2['verdict']}  ({r2['ordering']})")
    print(f"ITEM 3 (spoofed Host rejected when enabled)       : {r3['verdict']}")


if __name__ == "__main__":
    main()
