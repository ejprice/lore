"""REAL-uvicorn wire smoke for the packet-59 fastmcp migration — the ``migration_wire``
fixture the design §6.2 acceptance requires, and the ``@pytest.mark.wire`` assertions it
carries (contract ``test_fastmcp_migration.py`` SECTION F documents them; those pins are
un-runnable placeholders that ``pytest.skip`` until this fixture exists — this module IS
that fixture + its runnable assertions).

WHY A REAL UVICORN, NOT THE IN-MEMORY TRANSPORT (design §9-FG1, the migration's biggest
risk): the in-memory ``Client(mcp)`` transport NEVER runs the ASGI lifespan, so a build
where the lifespan silently fails to enter (session manager not initialised, heavy build
not hoisted) passes every in-memory test while the deployed container serves NOTHING. Only
a ``uvicorn`` server on a TCP port with ``lifespan="on"`` proves the running artifact. This
mirrors ``scripts/fastmcp_migration_spike.py`` (the GO spike) but drives the REAL
production composition — ``build_mcp_server`` → ``build_asgi_app`` — end to end.

The assertions (design §6.2, brief step 4):

* serves at the configured path — the C2 lifespan propagation did not silently fail (FG1);
* ``tools/list`` = the 15 built-ins + the registered extension tool (D6);
* ``serverInfo.version`` == ``_resolve_version()`` (D4 / FG4);
* a BUILT-IN and an EXTENSION tool call EACH land exactly one trace row in the store
  (B1 funnel-∀ / FG2 — the reach catch: the ``on_call_tool`` middleware fires on BOTH
  registration paths, read back from the REAL ``trace`` table);
* auth posture: a bad token → 401, a bad Origin → 403, a spoofed Host → 421, a legit
  proxied Host → 200 (C3/C3'/C4 + the ``allowed_hosts`` config rider, spike Item 3);
* the heavy build runs EXACTLY ONCE per process across concurrent sessions (C2 / #16/#19 —
  fastmcp's native ref-counted ``lifespan=``, the apparatus DELETE relies on this).

HERMETIC: a ``FakeEmbedder`` (no live TEI), the TEST SurrealDB store on a fresh throwaway
database (``ws://127.0.0.1:18000`` — ``:18500`` is PRODUCTION and is never a test target),
tmp-path SQLite/snapshot dirs, and the inert calibration counter — but otherwise the REAL
composed lifespan uvicorn runs.
"""

from __future__ import annotations

import asyncio
import contextlib
import socket
import threading
import time
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import httpx
import loremaster.embedding as embedding_module
import loremaster.server as server_module
import pytest
import pytest_asyncio
import uvicorn
from _extension_helpers import CounterExtension
from _surreal_harness import (
    PRODUCTION_DIM,
    connect_admin,
    drop_database,
    make_env,
    surreal_url,
    unique_database,
)
from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from loremaster.config import LoreConfig
from loremaster.server import (
    LoreServer,
    _resolve_version,
    build_asgi_app,
    build_mcp_server,
)
from loremaster.store.surreal import SurrealStore
from loresigil.testing import FakeEmbedder

# Every test here spins a REAL uvicorn — it is the deploy/gate lane, not the unit lane.
pytestmark = pytest.mark.wire

_DIM = PRODUCTION_DIM  # the voyage-4-nano production curve dim the probe gate matches.
_SURREAL_TEST_NAMESPACE = "lore_test"
# The Bearer key + its env ref (the config names the ENV, the value lives in the env).
_DEV_KEY = "wire-dev-secret-59"
_DEV_KEY_ENV = "LORE_KEY_DEV_WIRE59"
# A stand-in for the real nginx-ingress proxied Host, configured via the LORE_ALLOWED_HOSTS
# deploy knob (build_asgi_app's config rider) so a legit proxied Host is accepted (not 421).
_ALLOWED_PROXY_HOST = "lore.internal.example"
# The 15 built-in tools the migrated server must serve on the wire (design §1, unchanged).
_BUILTIN_TOOLS = frozenset(
    {
        "lore_search", "lore_get_symbol", "lore_verify", "lore_remember", "lore_recall",
        "lore_claim_task", "lore_tasks", "lore_comms", "lore_impact", "lore_map",
        "lore_read", "lore_dead_code", "lore_diff", "lore_index", "lore_findings",
    }
)


def _free_port() -> int:
    """Grab an ephemeral loopback TCP port for a throwaway uvicorn."""
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


@contextlib.contextmanager
def _serve(app: Any, port: int) -> Iterator[str]:
    """Run ``app`` under uvicorn on ``127.0.0.1:port`` in a daemon thread.

    ``lifespan="on"`` FORCES the ASGI lifespan protocol — a server that cannot enter it
    fails loudly (the heavy build never completes → ``server.started`` never flips → a loud
    timeout) rather than silently skipping it (the FG1 guard). Yields the base URL; on exit
    drives a real shutdown so lifespan teardown runs.
    """
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", lifespan="on")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        for _ in range(600):  # up to 15s for the heavy build (probe gate + store + watcher)
            if server.started:
                break
            time.sleep(0.025)
        else:
            raise RuntimeError("uvicorn did not report started within 15s (heavy build failed?)")
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=20)


def _wire_config(database: str, live_path: Path) -> LoreConfig:
    """A production-shaped config bound to the TEST store, with auth ENABLED.

    An EXPLICIT ``database`` (not the slug default) so a reader store can be pointed at the
    SAME throwaway DB to read the trace rows the server wrote.
    """
    payload: dict[str, Any] = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": f"wire_{database}", "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "surreal": {
            "url": surreal_url(),
            "namespace": _SURREAL_TEST_NAMESPACE,
            "database": database,
            "user_env": "SURREAL_USER",
            "password_env": "SURREAL_PASS",
        },
        "roots": [
            {"tier": "custom", "watch": "live", "path": str(live_path), "include": ["**/*.py"]}
        ],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": False,  # no live inotify watcher in the harness (the build still runs)
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9233},
        "auth": {"enabled": True, "keys": [{"name": "dev", "key_env": _DEV_KEY_ENV}]},
    }
    return LoreConfig.model_validate(payload)


class _MigrationWire:
    """The wire harness handed to a test: a running server + the probes SECTION F needs."""

    _INIT_BODY = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "migration-wire-probe", "version": "0"},
        },
    }

    def __init__(self, *, base_url: str, path: str, env: Any, build_calls: dict[str, int]) -> None:
        self.base_url = base_url
        self.path = path
        self._env = env
        self.build_calls = build_calls  # {"n": <heavy-build invocations>} — once-per-process

    @property
    def endpoint(self) -> str:
        """The full MCP endpoint URL (base + mount path)."""
        return f"{self.base_url.rstrip('/')}{self.path}"

    @contextlib.asynccontextmanager
    async def client(self, *, token: str | None = _DEV_KEY) -> AsyncIterator[Any]:
        """A connected fastmcp streamable-HTTP client (one wire session).

        Authenticated with the dev Bearer key by default; pass ``token=None`` for none.
        """
        auth = BearerAuth(token) if token else None
        async with Client(self.endpoint, auth=auth) as client:
            yield client

    async def server_info(self) -> Any:
        """The ``initialize`` result's ``serverInfo`` (carries the served version)."""
        async with self.client() as client:
            init_result = client.initialize_result
        return init_result.serverInfo

    async def post(
        self, *, host: str | None = None, origin: str | None = None, token: str | None = _DEV_KEY
    ) -> httpx.Response:
        """Raw ``initialize`` POST for header-spoof probes (Host/Origin/token → status code)."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        if host is not None:
            headers["Host"] = host
        if origin is not None:
            headers["Origin"] = origin
        async with httpx.AsyncClient() as http_client:
            return await http_client.post(self.endpoint, json=self._INIT_BODY, headers=headers)

    async def trace_rows(self) -> list[dict[str, Any]]:
        """Every row in the server's REAL ``trace`` table, read back from the same DB.

        A separate reader store on the SAME (namespace, database) the server wrote through —
        so the funnel's real-row legs (B1/FG2) read what the ``on_call_tool`` middleware
        actually landed, not a double.
        """
        store = SurrealStore(
            url=self._env.url,
            namespace=self._env.namespace,
            database=self._env.database,
            dim=self._env.dim,
            user=self._env.user,
            password=self._env.password,
        )
        try:
            projection = "tool, ok, ordinal, ts, transport_session"
            result = await store._query(f"SELECT {projection} FROM trace")  # noqa: SLF001
            return list(result or [])
        finally:
            await store.close()

    async def raw_session_tool_call(
        self, tool: str, *, arguments: dict[str, Any] | None = None
    ) -> str:
        """Run a FULL stateful wire session over raw httpx; return the minted mcp-session-id.

        initialize (capture the minted ``mcp-session-id`` response header) →
        ``notifications/initialized`` → ``tools/call``. The tools/call request carries the
        ``mcp-session-id`` header, so the server's trace write records ``transport_session``
        == that id (F1). Returns the session id so the caller can assert equality against the
        trace row. Raw httpx (not the fastmcp ``Client``) so the session id is observable.
        """
        base = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {_DEV_KEY}",
        }
        async with httpx.AsyncClient() as http_client:
            init = await http_client.post(
                self.endpoint, json=self._INIT_BODY, headers=base, timeout=30
            )
            session_id: str | None = init.headers.get("mcp-session-id")
            assert session_id, (
                f"initialize minted NO mcp-session-id header (status {init.status_code}); the "
                f"served mode is not stateful. Body: {init.text[:200]!r}"
            )
            session_headers = {
                **base,
                "mcp-session-id": session_id,
                "mcp-protocol-version": "2025-06-18",
            }
            await http_client.post(
                self.endpoint,
                json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                headers=session_headers,
                timeout=30,
            )
            await http_client.post(
                self.endpoint,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": tool, "arguments": arguments or {}},
                },
                headers=session_headers,
                timeout=30,
            )
        return session_id


@contextlib.asynccontextmanager
async def _serve_migration_wire(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, allowed_hosts_env: str | None
) -> AsyncIterator[_MigrationWire]:
    """Serve the REAL migrated composition over uvicorn with a chosen ``LORE_ALLOWED_HOSTS``.

    ``allowed_hosts_env``: the ``LORE_ALLOWED_HOSTS`` value to set, or ``None`` to leave it
    UNSET (the default-protective posture). The ``migration_wire`` fixture drives this with the
    proxied-host rider; the item-8 host tests drive it with ``'*'`` (allow-all) / ``None``.

    Callers MUST also depend on the ``_inert_calibration_counter`` fixture (the fixture below
    does) so the real lifespan cannot fire a live ``count_tokens`` POST with the dummy key.
    """
    database = unique_database()
    env = make_env(database=database, dim=_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()

    # The REAL test-store credentials (the same ones connect_admin above just used), named
    # by the config's user_env/password_env — the heavy build actually CONNECTS, so these
    # must be the working creds, not a "root"/"root" placeholder.
    monkeypatch.setenv("SURREAL_USER", env.user)
    monkeypatch.setenv("SURREAL_PASS", env.password.get_secret_value())
    monkeypatch.setenv(_DEV_KEY_ENV, _DEV_KEY)
    # The config rider: name the proxied Host(s) host_origin_protection accepts. ``None``
    # leaves it UNSET so _resolve_allowed_hosts returns just the bind host (the DEFAULT
    # protective posture — item 8's "unset still 421s a spoofed Host" leg).
    if allowed_hosts_env is None:
        monkeypatch.delenv("LORE_ALLOWED_HOSTS", raising=False)
    else:
        monkeypatch.setenv("LORE_ALLOWED_HOSTS", allowed_hosts_env)
    # Hermetic heavy build: a FakeEmbedder (no live TEI) + tmp SQLite/snapshot dirs. The
    # lifespan does ``from loremaster.embedding import make_embedder_from_config`` at call
    # time, so patch it at its source module.
    monkeypatch.setattr(
        embedding_module, "make_embedder_from_config", lambda _config: FakeEmbedder(dim=_DIM)
    )
    (tmp_path / "state").mkdir(exist_ok=True)
    monkeypatch.setattr(server_module, "_DEFAULT_MANIFEST_DIR", tmp_path / "state")
    monkeypatch.setattr(server_module, "_DEFAULT_SNAPSHOT_ROOT", tmp_path / "snap")

    # Once-per-process oracle: count heavy-build invocations by spying the probe gate (the
    # first heavy-startup primitive). The uvicorn thread shares this process + module object,
    # so a patch set here (before serving) is visible inside the lifespan, and the counter
    # dict is read back after the sessions run.
    build_calls = {"n": 0}
    real_probe_gate = server_module.run_probe_gate

    async def _counting_probe_gate(**kwargs: Any) -> int:
        build_calls["n"] += 1
        return await real_probe_gate(**kwargs)

    monkeypatch.setattr(server_module, "run_probe_gate", _counting_probe_gate)

    live = tmp_path / "live"
    (live / "pkg").mkdir(parents=True, exist_ok=True)
    (live / "pkg" / "module.py").write_text(
        "def wire_probe_function():\n    return 1\n", encoding="utf-8"
    )
    config = _wire_config(database, live)
    server = LoreServer(config).register_extension(CounterExtension())
    mcp = build_mcp_server(server)
    app = build_asgi_app(mcp, config)
    port = _free_port()
    try:
        with _serve(app, port):
            yield _MigrationWire(
                base_url=f"http://127.0.0.1:{port}",
                path=config.server.path,
                env=env,
                build_calls=build_calls,
            )
    finally:
        await drop_database(env)


@pytest_asyncio.fixture()
async def migration_wire(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _inert_calibration_counter: None
) -> AsyncIterator[_MigrationWire]:
    """Serve the REAL migrated composition over uvicorn and yield the wire harness.

    Uses the proxied-host allowlist rider (``_ALLOWED_PROXY_HOST``); ``_inert_calibration_
    counter`` (conftest) neutralises the boot calibration probe.
    """
    async with _serve_migration_wire(
        tmp_path, monkeypatch, allowed_hosts_env=_ALLOWED_PROXY_HOST
    ) as wire:
        yield wire


class TestTheWireSmokeServesTheFullSurface:
    """§6.2 / FG1 / FG4 / D6: the running artifact serves the full surface + honest version."""

    async def test_tools_list_serves_the_builtins_and_the_extension_tool(
        self, migration_wire: _MigrationWire
    ) -> None:
        async with migration_wire.client() as client:
            registered = {tool.name for tool in await client.list_tools()}
        assert _BUILTIN_TOOLS <= registered, (
            f"the wire tools/list is missing built-ins {sorted(_BUILTIN_TOOLS - registered)} — "
            f"the lifespan did not serve the full surface (FG1) or a Context[...] site broke "
            f"registration. Served: {sorted(registered)}"
        )
        assert "bump_counter" in registered, (
            "the extension tool `bump_counter` is absent from the wire tools/list — the "
            "add_tool→mcp.tool adaptation (coupling #2 / D6) did not reach the served surface."
        )

    async def test_serverinfo_version_is_lores_resolved_version(
        self, migration_wire: _MigrationWire
    ) -> None:
        server_info = await migration_wire.server_info()
        assert server_info.version == _resolve_version(), (
            f"serverInfo.version is {server_info.version!r}, expected lore's "
            f"{_resolve_version()!r} (D4/FG4) — the ctor `version=` kwarg was dropped, so the "
            f"server silently advertises fastmcp's own version."
        )


class TestBothRegistrationPathsLandARealTraceRow:
    """B1 funnel-∀ / FG2: a BUILT-IN and an EXTENSION call EACH land exactly one trace row.

    The ``on_call_tool`` middleware's coverage is a REACH variable (not "by construction"
    like the retired subclass), so this reads BOTH paths back from the REAL ``trace`` table.
    """

    async def test_a_builtin_and_an_extension_call_each_land_one_trace_row(
        self, migration_wire: _MigrationWire
    ) -> None:
        async with migration_wire.client() as client:
            await client.call_tool("lore_index", {})  # a built-in (@mcp.tool path)
            await client.call_tool("bump_counter", {})  # an extension (add_tool adaptation)

        # The trace write sits in a shielded `finally` (async), so it may land just after
        # the call returns — poll briefly for both rows rather than reading once and racing.
        traced: list[str] = []
        for _ in range(40):
            rows = await migration_wire.trace_rows()
            traced = sorted(str(row["tool"]) for row in rows)
            if {"bump_counter", "lore_index"} <= set(traced):
                break
            await asyncio.sleep(0.05)
        assert "lore_index" in traced, (
            f"the built-in call landed NO trace row (funnel not reached on the @mcp.tool path); "
            f"traced={traced}"
        )
        assert "bump_counter" in traced, (
            f"the extension call landed NO trace row — the on_call_tool middleware does not "
            f"reach the add_tool-adapted extension path (design §9-FG2); traced={traced}"
        )


class TestTheHostOriginProtectionIsEnabledAndConfigured:
    """§5b-C3' / Item 3 / the config rider: spoofed Host → 421, legit proxied Host → not-421."""

    async def test_a_spoofed_host_is_rejected_421(self, migration_wire: _MigrationWire) -> None:
        # Good token + no Origin so the request REACHES fastmcp's host guard; a spoofed Host
        # is not in DEFAULT_HOSTS/allowed_hosts → 421 (a check lore did NOT have pre-migration).
        response = await migration_wire.post(host="evil.example")
        assert response.status_code == 421, (
            f"a spoofed Host was accepted (status {response.status_code}) — "
            f"host_origin_protection is not enabled (default is OFF; the migration must pass "
            f"host_origin_protection=True). Body: {response.text[:200]!r}"
        )

    async def test_a_legit_proxied_host_is_accepted(self, migration_wire: _MigrationWire) -> None:
        # The config rider: the proxied Host is named via LORE_ALLOWED_HOSTS, so it must NOT
        # 421 — else the enabled guard 421s legitimate production traffic (TLS terminated
        # upstream by nginx-ingress, so the Host lore sees is the proxied name).
        response = await migration_wire.post(host=_ALLOWED_PROXY_HOST)
        assert response.status_code != 421, (
            f"a legit proxied Host ({_ALLOWED_PROXY_HOST}) was 421'd — allowed_hosts is not "
            f"configured for the real topology, so the enabled guard rejects prod traffic "
            f"(the config rider). Body: {response.text[:200]!r}"
        )


class TestTheAuthPostureIsUnchanged:
    """§5b-C4 / FG6: bad token → 401, bad Origin → 403 (the bespoke wrappers, unchanged)."""

    async def test_a_bad_token_is_rejected_401(self, migration_wire: _MigrationWire) -> None:
        response = await migration_wire.post(token="not-the-dev-key")
        assert response.status_code == 401, (
            f"a bad Bearer token was not rejected 401 (status {response.status_code}) — the "
            f"bespoke BearerAuthMiddleware posture changed under the http_app swap."
        )

    async def test_a_bad_origin_is_rejected_403(self, migration_wire: _MigrationWire) -> None:
        # Good token so the request passes Bearer and reaches the Origin guard; a non-loopback
        # non-configured Origin → 403 (the bespoke OriginValidationMiddleware, kept — C3/F1).
        response = await migration_wire.post(origin="http://evil.example")
        assert response.status_code == 403, (
            f"a bad Origin was not rejected 403 (status {response.status_code}) — the bespoke "
            f"Origin (DNS-rebinding) guard was lost or reordered under the http_app swap."
        )


class TestTheHeavyBuildRunsOncePerProcess:
    """§5b-C2 / #16 / #19: fastmcp enters the ``lifespan=`` ONCE PER PROCESS across sessions.

    The ~150-LOC apparatus DELETE relies on this native behaviour. If a per-session re-entry
    crept back, the heavy build (probe gate) would run once per session — the build_calls
    counter would exceed 1 across the concurrent + sequential sessions this drives.
    """

    async def test_the_heavy_build_runs_once_across_concurrent_and_sequential_sessions(
        self, migration_wire: _MigrationWire
    ) -> None:
        async def _one_session() -> set[str]:
            async with migration_wire.client() as client:
                return {tool.name for tool in await client.list_tools()}

        # 4 CONCURRENT wire sessions (the real multi-client condition a per-session re-entry
        # would show), then 2 more SEQUENTIAL — the heavy build must still have run once.
        concurrent = await asyncio.gather(*[_one_session() for _ in range(4)])
        for _ in range(2):
            await _one_session()

        assert all(_BUILTIN_TOOLS <= names for names in concurrent), (
            "a concurrent session saw a partial tool surface — the shared build was not reused."
        )
        assert migration_wire.build_calls["n"] == 1, (
            f"the heavy build (probe gate) ran {migration_wire.build_calls['n']}x across 4 "
            f"concurrent + 2 sequential sessions; fastmcp's ref-counted lifespan must enter it "
            f"exactly ONCE per PROCESS (design §5b-C2 — the apparatus DELETE relies on it)."
        )


class TestTheTransportSessionCorrelatorIsCaptured:
    """F1 / finding #381: a traced HTTP tool call records ``transport_session`` == the
    session's ``mcp-session-id``.

    ``get_http_headers()`` STRIPS ``mcp-session-id`` by default (it is in the exclude set —
    verified in installed fastmcp ``server/dependencies.py``), so a bare ``.get()`` nulls the
    correlator on EVERY row; the write must pass ``include={'mcp-session-id'}``. This reads the
    REAL trace row back over a real stateful session and asserts equality — RED before the fix
    (transport_session is None ≠ the session id), GREEN after.
    """

    async def test_a_traced_call_records_the_mcp_session_id_as_transport_session(
        self, migration_wire: _MigrationWire
    ) -> None:
        session_id = await migration_wire.raw_session_tool_call("lore_index")
        found_row = False
        correlator: Any = None
        for _ in range(40):
            rows = await migration_wire.trace_rows()
            for row in rows:
                if str(row["tool"]) == "lore_index":
                    found_row = True
                    correlator = row.get("transport_session")
            if found_row and correlator is not None:
                break
            await asyncio.sleep(0.05)
        # Distinguish the two RED causes: a broken handshake/funnel (no row at all) from the
        # F1 regression (row present, correlator None). Only the latter is what this pins.
        assert found_row, (
            "the raw wire tool call landed NO trace row for lore_index — the handshake or the "
            "on_call_tool funnel is broken (distinct from the correlator being None)."
        )
        assert correlator == session_id, (
            f"trace transport_session={correlator!r} != the session's mcp-session-id="
            f"{session_id!r}. get_http_headers() strips mcp-session-id by default (F1 / #381); "
            f"the write must call get_http_headers(include={{'mcp-session-id'}})."
        )


class TestTheServedTransportModeIsExplicitlyStateful:
    """R1 / design §5b-C5 / FG8: ``build_asgi_app`` sets the transport mode EXPLICITLY
    (stateful), never inheriting fastmcp's env-overridable ``settings.stateless_http`` default.
    """

    def test_build_asgi_app_passes_stateless_http_false_explicitly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # UNIT (the DISCRIMINATING pin for the code change): spy the http_app kwargs. Reddens
        # if stateless_http is dropped (inherits fastmcp.settings.stateless_http, an
        # env-overridable default — C5/FG8) or set True. No server needed.
        monkeypatch.setenv(_DEV_KEY_ENV, _DEV_KEY)  # so the Bearer wrap can build its verifier
        captured: dict[str, Any] = {}

        class _SpyMcp:
            def http_app(self, **kwargs: Any) -> Any:
                captured.update(kwargs)

                async def _app(scope: Any, receive: Any, send: Any) -> None:  # ASGI stub
                    return None

                return _app

        config = _wire_config("spy_db", Path("."))
        build_asgi_app(_SpyMcp(), config)
        assert captured.get("stateless_http") is False, (
            f"build_asgi_app did not pass stateless_http=False explicitly (got "
            f"{captured.get('stateless_http')!r}); the served mode would INHERIT "
            f"fastmcp.settings.stateless_http, an env-overridable default (C5/FG8)."
        )

    async def test_a_stateful_session_mints_an_mcp_session_id_header(
        self, migration_wire: _MigrationWire
    ) -> None:
        # WIRE regression guard (the coldaudit R1 / §6.2 mode assertion): a real initialize
        # mints an mcp-session-id response header in stateful mode. Reddens if the served mode
        # ever flips to stateless.
        response = await migration_wire.post()
        assert response.status_code == 200, (
            f"a clean initialize POST returned {response.status_code}, not 200 — cannot observe "
            f"the session-id mint. Body: {response.text[:200]!r}"
        )
        assert response.headers.get("mcp-session-id"), (
            "the stateful initialize minted NO mcp-session-id response header — the served mode "
            f"is stateless (C5/FG8). Response header keys: {sorted(response.headers.keys())}"
        )


class TestTheAllowedHostsWildcardAndDefault:
    """Item 8 (operator-ruled 2026-08-16, decision 30e56ac8): ``LORE_ALLOWED_HOSTS='*'`` is an
    explicit opt-in ALLOW-ALL (an arbitrary/spoofed Host is served, not 421); with the env
    UNSET the default posture stays PROTECTIVE (a spoofed Host is 421). Default = protective,
    ``'*'`` = deliberate allow-all. (The operator DECLINED both promoting the knob to a
    ServerConfig field and rejecting ``'*'`` — security-59 F2 overruled.)
    """

    async def test_a_wildcard_allows_an_arbitrary_spoofed_host(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        _inert_calibration_counter: None,
    ) -> None:
        async with _serve_migration_wire(
            tmp_path, monkeypatch, allowed_hosts_env="*"
        ) as wire:
            response = await wire.post(host="evil.example")
        assert response.status_code != 421, (
            f"LORE_ALLOWED_HOSTS='*' did not allow an arbitrary Host (status "
            f"{response.status_code}) — '*' must be an explicit allow-all (fastmcp "
            f"_host_matches treats '*' as match-all). Body: {response.text[:200]!r}"
        )

    async def test_an_unset_allowlist_still_rejects_a_spoofed_host_421(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        _inert_calibration_counter: None,
    ) -> None:
        async with _serve_migration_wire(
            tmp_path, monkeypatch, allowed_hosts_env=None
        ) as wire:
            response = await wire.post(host="evil.example")
        assert response.status_code == 421, (
            f"with LORE_ALLOWED_HOSTS UNSET a spoofed Host was NOT 421'd (status "
            f"{response.status_code}) — the DEFAULT posture must stay PROTECTIVE (host "
            f"validation on via host_origin_protection=True). Body: {response.text[:200]!r}"
        )


class TestTraceEmitGuardsANoneRequestContext:
    """F3: ``_record_tool_trace`` guards a None ``request_context`` (fastmcp types it
    ``RequestContext | None``) with the SAME quiet DEBUG no-op as a None context — never a loud
    ``trace.emit.failed`` from dereferencing ``None.lifespan_context``.

    A pure UNIT pin (no server/store); it lives here because the middleware/context scaffolding
    it would otherwise reuse is in the restricted contract file.
    """

    async def test_a_none_request_context_is_a_quiet_debug_no_op(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from types import SimpleNamespace

        debug_events: list[str] = []
        monkeypatch.setattr(
            server_module.logger,
            "debug",
            lambda event, *args, **kwargs: debug_events.append(str(event)),
        )
        # A non-None context whose request_context is None (the F3 shape). Without the guard
        # this raises AttributeError on None.lifespan_context BEFORE any debug log.
        fastmcp_context = SimpleNamespace(request_context=None)
        await server_module._record_tool_trace(  # noqa: SLF001
            fastmcp_context=fastmcp_context,
            tool="lore_index",
            arguments={},
            latency_ms=1.0,
            ok=True,
        )
        assert "trace.emit.no_request_context" in debug_events, (
            "a None request_context did not take the quiet DEBUG no-op path (F3) — it either "
            "crashed on None.lifespan_context or logged a loud trace.emit.failed."
        )
