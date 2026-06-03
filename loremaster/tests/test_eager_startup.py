"""CONTRACT tests for EAGER process-startup initialization of the lore MCP server.

These tests pin the *observable* behaviour of a not-yet-built composition seam:
loremaster must run its heavy startup (probe gate → initial reconcile →
schema-fingerprint self-heal → file watcher) **eagerly at ASGI/uvicorn process
startup** (the ``lifespan.startup`` event), BEFORE any MCP client session opens —
not lazily on the first session as it does today.

Why this is a behaviour change worth a contract
------------------------------------------------
Today ``build_mcp_server`` builds a closure-local
:class:`~loremaster.server._ProcessLifespanGuard` and a per-SESSION
``@asynccontextmanager`` lifespan that takes/releases a lease. FastMCP's
streamable-http session manager enters that per-session lifespan once per MCP
session, so a freshly (re)started container does NOTHING heavy until the FIRST
client connects. A container that has restarted but has no live client is a dead
index that *looks* up.

The fix composes an OUTER ASGI lifespan in :func:`~loremaster.server.build_asgi_app`
that, on ``lifespan.startup``: (a) enters the inner streamable app's own
session-manager lifespan (so the server still serves) AND (b) takes a
process-lifetime EAGER lease via the guard surfaced from ``build_mcp_server``
(so the heavy build runs ONCE, eagerly). On ``lifespan.shutdown`` it releases the
eager lease (→ teardown) and exits the inner lifespan. The Origin/Bearer wrapping
(Bearer outermost when auth enabled) is preserved unchanged.

The contract pinned (each invariant has an oracle independent of the impl)
-------------------------------------------------------------------------
1. **Eager build at process startup.** Driving ``lifespan.startup`` runs the
   guard's build factory BEFORE any HTTP/session — a spy build counter is == 1
   after startup with ZERO sessions opened.
2. **Exactly once per process.** Across the eager lease + N subsequent per-session
   leases, the build factory runs exactly ONCE (eager builds; sessions reuse).
3. **Inner session-manager lifespan still runs.** The composed lifespan must enter
   the inner app's ``lifespan_context`` — a regression that drops it must fail.
4. **Shutdown tears down**, and a FAILED eager build does not wedge: the failure
   propagates out of startup, nothing is cached, a later startup retries and can
   succeed (mirrors the guard's no-cache-on-failure).
5. **Additive.** ``build_mcp_server``'s single-FastMCP return signature is
   unchanged; the new guard handle is surfaced WITHOUT breaking existing callers.
6. **Origin/Bearer preserved.** The composed app still rejects a bad Origin and
   keeps Bearer outermost when auth is enabled.

Hermetic design
---------------
The startup-ordering / once-per-process / inner-lifespan / shutdown assertions are
driven against the COMPOSITION with a SUBSTITUTED spy guard + a fake inner app, so
no live Qdrant or TEI is needed and the ASSERTIONS do not mirror the production
build factory's internals (they observe a spy's call counts, an oracle the impl
cannot satisfy by accident). One end-to-end case drives the REAL composed app's
raw ASGI ``lifespan`` protocol with a FakeEmbedder + a real throwaway Qdrant +
tmp-path SQLite/snapshot dirs — mirroring the hermetic pattern in
``test_mcp_server.py::test_heavy_startup_runs_once_across_two_sessions`` — to pin
the real handoff (the producer↔consumer seam where ``build_mcp_server`` surfaces
the guard and ``build_asgi_app`` consumes it).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from loremaster.config import LoreConfig
from loremaster.server import (
    LoreServer,
    build_asgi_app,
    build_mcp_server,
)
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient

# The configured embedding dimensionality the FakeEmbedder must report so the
# startup probe gate (probe dim == config.dim) passes. Mirrors the value the rest
# of the loremaster suite uses (test_mcp_server / test_lifespan_framework: 2048),
# the real production curve dimensionality for the voyage-4-nano deploy — NOT a
# convenience value. Pinning it to the same constant keeps the probe-gate seam
# coherent with how the production config declares ``embedding.dim``.
_DIM = 2048

# The number of distinct MCP client sessions simulated AFTER eager startup in the
# once-per-process test. Two is the minimum that distinguishes "build once,
# reuse" from "build per session"; the existing heavy-startup test also uses 2.
_SIMULATED_SESSIONS_AFTER_EAGER = 2

# How many times the eager build factory must have run after a single
# process-startup + N session leases: EXACTLY ONCE (eager builds, sessions reuse).
_EXPECTED_BUILD_COUNT_PER_PROCESS = 1


def _slug() -> str:
    """A unique throwaway project slug per test (namespaces Qdrant collections)."""
    return f"test_{uuid.uuid4().hex}"


def _config(slug: str, live_path: Path, *, auth: dict[str, Any] | None = None) -> LoreConfig:
    """Build a validated :class:`LoreConfig` mirroring the production shape.

    Reuses the exact production-realistic config payload the rest of the
    loremaster suite uses (``test_mcp_server._config``): a TEI embedding backend
    at dim ``_DIM``, the real local throwaway Qdrant URL/key env, a single
    inotify-watched custom-tier root, and the 127.0.0.1 loopback server bind the
    Origin guard defends. ``auth`` threads an enabled Bearer block when given.
    """
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
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
        "qdrant": {"url": "http://127.0.0.1:16333", "api_key_env": "QDRANT__SERVICE__API_KEY"},
        "roots": [
            {"tier": "custom", "watch": "live", "path": str(live_path), "include": ["**/*.py"]}
        ],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9233},
    }
    if auth is not None:
        payload["auth"] = auth
    return LoreConfig.model_validate(payload)


# --------------------------------------------------------------------------- #
# Spy doubles for the hermetic composition tests
# --------------------------------------------------------------------------- #
class _SpyGuard:
    """A drop-in stand-in for :class:`_ProcessLifespanGuard` that COUNTS leases.

    ``build_asgi_app`` must take a process-lifetime eager lease against whatever
    guard ``build_mcp_server`` surfaced on the returned ``mcp`` object. This spy
    records every ``acquire`` / ``release`` so a test can assert the eager lease
    was taken at ``lifespan.startup`` and released at ``lifespan.shutdown`` — an
    oracle the production guard cannot satisfy by coincidence (the spy never
    builds a real AppContext; it just counts).

    The optional ``fail_acquire_times`` reproduces the guard's no-cache-on-failure
    contract: the first N acquires raise, then one succeeds — to prove a failed
    eager build propagates out of ``lifespan.startup`` and a later startup retries.
    """

    def __init__(self, *, fail_acquire_times: int = 0) -> None:
        self.acquire_calls = 0
        self.release_calls = 0
        self.live_leases = 0
        self._fail_acquire_times = fail_acquire_times
        self._sentinel_context = object()

    async def acquire(self) -> Any:
        self.acquire_calls += 1
        if self.acquire_calls <= self._fail_acquire_times:
            # Mirror the guard: a build failure is NOT cached — the lease that
            # raised did not increment the live count, so a later acquire retries.
            raise RuntimeError("eager build failed")
        self.live_leases += 1
        return self._sentinel_context

    async def release(self) -> None:
        self.release_calls += 1
        if self.live_leases > 0:
            self.live_leases -= 1


class _SpyInnerApp:
    """A fake inner ASGI app standing in for the streamable-http (Starlette) app.

    Records whether its session-manager lifespan was ENTERED and EXITED so a test
    can prove the composed outer lifespan still drives the inner one (invariant 3:
    a regression that forgets to enter the inner ``lifespan_context`` — and thus
    never starts the session manager / task group — must fail). HTTP scopes record
    their arrival so the Origin/Bearer wrapping can be exercised end-to-end if
    needed; lifespan scopes drive the startup/shutdown handshake.
    """

    def __init__(self) -> None:
        self.lifespan_entered = False
        self.lifespan_exited = False
        self.http_calls = 0

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope.get("type") == "lifespan":
            self.lifespan_entered = True
            message = await receive()
            assert message["type"] == "lifespan.startup"
            await send({"type": "lifespan.startup.complete"})
            message = await receive()
            assert message["type"] == "lifespan.shutdown"
            self.lifespan_exited = True
            await send({"type": "lifespan.shutdown.complete"})
            return
        self.http_calls += 1


async def _drive_lifespan(app: Any) -> dict[str, list[str]]:
    """Drive the raw ASGI ``lifespan`` protocol against ``app``: startup → shutdown.

    Feeds a ``lifespan.startup`` then a ``lifespan.shutdown`` message and records
    every reply the app sends (``...complete`` / ``...failed``). Returns the
    captured ``startup`` and ``shutdown`` reply-type lists. If startup fails, the
    app should send ``lifespan.startup.failed`` (and the driver stops before
    shutdown, mirroring how uvicorn handles a failed startup).
    """
    sent: list[dict[str, Any]] = []
    inbox: list[dict[str, Any]] = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    cursor = {"i": 0}

    async def receive() -> dict[str, Any]:
        message = inbox[cursor["i"]]
        cursor["i"] += 1
        return message

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    await app({"type": "lifespan"}, receive, send)
    return {"all": [m["type"] for m in sent]}


# --------------------------------------------------------------------------- #
# Invariant 5 (additive) — build_mcp_server signature + guard handle
# --------------------------------------------------------------------------- #
class TestBuildMcpServerSurfacesGuardAdditively:
    """``build_mcp_server`` still returns ONE FastMCP and surfaces the eager guard.

    Invariant 5: the ~25 existing call sites do ``mcp = build_mcp_server(...)`` and
    expect a single FastMCP back — the signature must NOT change. The eager guard
    is surfaced as an ATTRIBUTE on that returned object so ``build_asgi_app`` can
    read it. These tests pin the additive surface without forcing any existing
    test to change.
    """

    async def test_returns_a_single_object_not_a_tuple(self, tmp_path: Path) -> None:
        # The 25 existing call sites unpack nothing — a tuple return would break
        # every one. The contract: one object back, exactly as today.
        config = _config(_slug(), tmp_path / "live")
        result = build_mcp_server(LoreServer(config))
        assert not isinstance(result, tuple), (
            "build_mcp_server must keep its single-FastMCP return; surfacing the "
            "eager guard must be additive (an attribute), never a tuple return"
        )

    async def test_surfaces_the_eager_guard_handle_on_the_returned_server(
        self, tmp_path: Path
    ) -> None:
        # build_asgi_app needs a handle to the guard build_mcp_server constructed,
        # to take the eager process-lifetime lease. It must be reachable off the
        # returned object and be a real lease-able guard (acquire/release present),
        # so the composition can drive it. The exact attribute name is the impl's
        # choice; the contract is that SOME lease-able guard is surfaced.
        config = _config(_slug(), tmp_path / "live")
        mcp = build_mcp_server(LoreServer(config))
        guard = getattr(mcp, "_lore_eager_guard", None)
        assert guard is not None, (
            "build_mcp_server must surface its _ProcessLifespanGuard on the "
            "returned mcp (e.g. mcp._lore_eager_guard) so build_asgi_app can take "
            "the eager process-startup lease"
        )
        assert callable(getattr(guard, "acquire", None)), (
            "the surfaced eager guard must expose an async acquire() lease method"
        )
        assert callable(getattr(guard, "release", None)), (
            "the surfaced eager guard must expose an async release() lease method"
        )


# --------------------------------------------------------------------------- #
# Invariants 1-4 — the composed eager lifespan (hermetic, spy guard + inner app)
# --------------------------------------------------------------------------- #
class TestEagerLifespanComposition:
    """The OUTER ASGI lifespan ``build_asgi_app`` composes: eager build + inner run.

    Driven hermetically with a spy guard + a fake inner streamable app substituted
    onto the FastMCP object, so the assertions observe SPY call-counts (an oracle
    the production build factory cannot satisfy by accident) rather than mirroring
    the build's internals. Each test drives the raw ASGI ``lifespan`` protocol the
    way uvicorn does at process startup.
    """

    @staticmethod
    def _compose_with_spies(
        tmp_path: Path,
        *,
        guard: _SpyGuard,
        inner: _SpyInnerApp,
        auth: dict[str, Any] | None = None,
    ) -> Any:
        """Build the REAL composed ASGI app with the guard + inner app substituted.

        ``build_mcp_server`` surfaces the eager guard on the returned object and
        ``streamable_http_app`` yields the inner Starlette app; we replace both
        with spies so ``build_asgi_app`` composes its eager lifespan around the
        DOUBLES. This exercises the production composition wiring while keeping the
        assertions independent of the heavy build.
        """
        config = _config(_slug(), tmp_path / "live", auth=auth)
        mcp = build_mcp_server(LoreServer(config))
        # Substitute the eager guard the composition reads (the producer side of
        # the build_mcp_server → build_asgi_app seam) ...
        mcp._lore_eager_guard = guard  # type: ignore[attr-defined]
        # ... and the inner streamable app the composition must still drive.
        mcp.streamable_http_app = lambda: inner  # type: ignore[assignment]
        return build_asgi_app(mcp, config)

    async def test_startup_builds_eagerly_before_any_session(self, tmp_path: Path) -> None:
        # Invariant 1: driving lifespan.startup takes the eager lease (the heavy
        # build) with ZERO sessions/HTTP requests issued. A lazy-only server would
        # leave acquire_calls == 0 until the first session.
        guard = _SpyGuard()
        inner = _SpyInnerApp()
        app = self._compose_with_spies(tmp_path, guard=guard, inner=inner)

        # Drive ONLY the lifespan startup (no HTTP request, no MCP session).
        sent: list[dict[str, Any]] = []

        async def receive() -> dict[str, Any]:
            return {"type": "lifespan.startup"}

        async def send(message: dict[str, Any]) -> None:
            sent.append(message)
            # Stop the inner handshake after startup completes (we only assert the
            # eager build fired); raise to unwind the (already-entered) contexts.
            if message["type"] in ("lifespan.startup.complete", "lifespan.startup.failed"):
                raise _StopLifespan

        with pytest.raises(_StopLifespan):
            await app({"type": "lifespan"}, receive, send)

        assert guard.acquire_calls == 1, (
            f"the eager lease must be taken on lifespan.startup (got "
            f"{guard.acquire_calls} acquires); the heavy build must run at PROCESS "
            f"startup, before any MCP session opens"
        )
        assert inner.http_calls == 0, "no HTTP request was issued before the eager build"
        assert "lifespan.startup.complete" in [m["type"] for m in sent], (
            "a successful eager startup must report lifespan.startup.complete"
        )

    async def test_build_runs_exactly_once_across_eager_lease_plus_sessions(
        self, tmp_path: Path
    ) -> None:
        # Invariant 2: the eager lease builds; subsequent per-session leases REUSE.
        # Across the eager lease + N session leases the build factory runs ONCE.
        # We model this with the REAL guard's refcount semantics via a spy that
        # only the FIRST live lease would build — here, the production guard is the
        # real subject. Substitute the REAL guard with a build-counting factory.
        from loremaster.server import _ProcessLifespanGuard

        builds: list[int] = []

        class _Ctx:
            def __init__(self) -> None:
                self.closed = False

            async def aclose(self) -> None:
                self.closed = True

        class _Client:
            async def close(self) -> None:
                pass

        async def _factory() -> tuple[Any, Any]:
            builds.append(1)
            return _Ctx(), _Client()

        guard = _ProcessLifespanGuard(_factory)
        inner = _SpyInnerApp()
        app = self._compose_with_spies(tmp_path, guard=guard, inner=inner)

        # Eager startup takes the process-lifetime lease (build #1) and HOLDS it —
        # the eager lease is not released until process shutdown, so the AppContext
        # stays live for subsequent sessions to reuse.
        await _drive_eager_startup(app)
        assert len(builds) == _EXPECTED_BUILD_COUNT_PER_PROCESS, (
            "the eager startup must build the AppContext exactly once"
        )

        # N subsequent simulated MCP sessions each take + release a lease against
        # the SAME guard — they must REUSE the eager build, not rebuild.
        for _ in range(_SIMULATED_SESSIONS_AFTER_EAGER):
            await guard.acquire()
            await guard.release()

        assert len(builds) == _EXPECTED_BUILD_COUNT_PER_PROCESS, (
            f"the build factory ran {len(builds)}x across the eager lease + "
            f"{_SIMULATED_SESSIONS_AFTER_EAGER} sessions; it must run exactly once "
            f"per process (eager builds, sessions reuse)"
        )

    async def test_composed_lifespan_enters_inner_lifespan_AND_builds_eagerly(
        self, tmp_path: Path
    ) -> None:
        # Invariant 3: the composed outer lifespan must ENTER the inner streamable
        # app's lifespan (which starts the session-manager task group) AND take the
        # eager lease — on the SAME startup. Asserting the CONJUNCTION is what makes
        # this a real discriminator: today's build_asgi_app already forwards the
        # lifespan scope through the Origin middleware to the inner app (auth.py
        # passthrough), so inner.lifespan_entered alone is True even with NO eager
        # composition. The bug is that no eager lease is taken — so requiring BOTH
        # "inner entered" AND "eager build fired" goes RED today and only passes
        # once the composition does both (server both BUILDS eagerly and SERVES).
        guard = _SpyGuard()
        inner = _SpyInnerApp()
        app = self._compose_with_spies(tmp_path, guard=guard, inner=inner)

        await _drive_eager_startup(app)

        assert inner.lifespan_entered is True, (
            "the composed lifespan must enter the inner streamable app's "
            "session-manager lifespan (else the server builds but never serves)"
        )
        assert guard.acquire_calls == 1, (
            "the composed lifespan must ALSO take the eager lease on the same "
            "startup (else it serves but never builds eagerly) — both, not either"
        )

    async def test_shutdown_releases_the_eager_lease_and_exits_inner(
        self, tmp_path: Path
    ) -> None:
        # Invariant 4 (teardown): driving startup then shutdown releases the eager
        # lease (→ AppContext + client teardown) AND exits the inner lifespan. The
        # spy guard records the release; the spy inner records its exit.
        guard = _SpyGuard()
        inner = _SpyInnerApp()
        app = self._compose_with_spies(tmp_path, guard=guard, inner=inner)

        replies = await _drive_lifespan(app)

        assert guard.acquire_calls == 1 and guard.release_calls == 1, (
            f"shutdown must release the one eager lease (acquires="
            f"{guard.acquire_calls}, releases={guard.release_calls})"
        )
        assert guard.live_leases == 0, "the eager lease must be fully released at shutdown"
        assert inner.lifespan_exited is True, (
            "the composed lifespan must exit the inner streamable app's lifespan "
            "on shutdown (clean session-manager teardown)"
        )
        assert "lifespan.shutdown.complete" in replies["all"], (
            "a clean shutdown must report lifespan.shutdown.complete"
        )

    async def test_failed_eager_build_propagates_and_does_not_wedge(
        self, tmp_path: Path
    ) -> None:
        # Invariant 4 (no-cache-on-failure): a failed eager build must surface at
        # lifespan.startup (uvicorn aborts the process) and must NOT be cached — a
        # later startup retries and can succeed. Mirrors the guard's existing
        # no-cache-on-failure unit contract, lifted to the composition layer.
        guard = _SpyGuard(fail_acquire_times=1)
        inner = _SpyInnerApp()
        app = self._compose_with_spies(tmp_path, guard=guard, inner=inner)

        # First startup: the eager build raises. The failure must NOT be swallowed
        # — either it propagates out of the lifespan call, or the app reports
        # lifespan.startup.failed (uvicorn's signal to abort). Accept either.
        failed_signal = await _drive_startup_expecting_failure(app)
        assert failed_signal, (
            "a failed eager build must surface (raise out of startup or send "
            "lifespan.startup.failed) so uvicorn aborts — never a silent green "
            "startup over a dead context"
        )

        # Nothing was cached: the next startup over the SAME composition retries
        # the eager lease and now succeeds (the spy's second acquire passes). The
        # eager lease is HELD after this startup-only drive (no shutdown), so the
        # spy's live-lease count reflects the one process-lifetime lease.
        await _drive_eager_startup(app)
        assert guard.live_leases == 1, (
            "the retry startup must successfully take the eager lease — a failed "
            "build must not wedge the process into a permanently-broken state"
        )


# --------------------------------------------------------------------------- #
# Invariant 6 — Origin/Bearer security wrapping preserved by the composition
# --------------------------------------------------------------------------- #
class TestSecurityWrappingPreserved:
    """The eager-lifespan composition must not weaken the Origin/Bearer wrapping.

    Invariant 6: the Origin guard is always on; Bearer is outermost when auth is
    enabled. The composed app must still reject a disallowed Origin and keep the
    Bearer layer outermost — adding the eager lifespan must not bypass either.
    """

    async def test_composed_no_auth_app_still_rejects_a_bad_origin(
        self, tmp_path: Path
    ) -> None:
        # A cross-origin browser request (the DNS-rebinding vector) is rejected at
        # the edge even with the eager lifespan in front of the inner app, and even
        # with no Bearer auth configured.
        from test_auth import _drive

        config = _config(_slug(), tmp_path / "live")  # no auth block
        mcp = build_mcp_server(LoreServer(config))
        app = build_asgi_app(mcp, config)
        response = await _drive(app, [(b"origin", b"http://evil.example.com")])
        assert response["status"] == 403, (
            "the composed app must still reject a disallowed Origin (403) — the "
            "DNS-rebinding guard survives the eager-lifespan composition"
        )

    async def test_composed_auth_app_is_bearer_outermost(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # With auth enabled, Bearer must be the OUTERMOST layer — a keyless request
        # is rejected with 401 BEFORE the Origin guard or the eager-wrapped inner
        # app runs. (A disallowed-Origin-with-valid-key request is still 403, proven
        # in test_mcp_server::TestOriginWiring; here we pin Bearer outermost.)
        from loremaster.auth import BearerAuthMiddleware
        from test_auth import _drive

        monkeypatch.setenv("LORE_KEY_DEV", "dev-secret")
        config = _config(
            _slug(),
            tmp_path / "live",
            auth={"enabled": True, "keys": [{"name": "dev", "key_env": "LORE_KEY_DEV"}]},
        )
        mcp = build_mcp_server(LoreServer(config))
        app = build_asgi_app(mcp, config)
        assert isinstance(app, BearerAuthMiddleware), (
            "with auth enabled, the composed app's OUTERMOST layer must be the "
            "Bearer middleware (auth gates before Origin + the eager inner app)"
        )
        # A keyless request is rejected at the outermost Bearer layer (401), never
        # reaching the inner app — the eager composition does not open a hole.
        response = await _drive(app, [(b"origin", b"http://localhost")])
        assert response["status"] == 401, (
            "a keyless HTTP request must be rejected 401 at the outermost Bearer "
            "layer, even with a loopback (allowed) Origin"
        )


# --------------------------------------------------------------------------- #
# Invariant 1-4 end-to-end — the REAL composed app, real Qdrant, FakeEmbedder
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture()
async def qdrant() -> AsyncIterator[AsyncQdrantClient]:
    """A real local Qdrant client with exact-name (concurrency-safe) teardown.

    Mirrors ``test_mcp_server.qdrant``: build_app_context creates the project
    collection AND a ``<name>_memory`` sibling, so reap BOTH for every tracked
    name (never a bare-prefix sweep that could nuke a sibling worktree's run).
    """
    from conftest import QDRANT_URL, _qdrant_api_key

    client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
    created: list[str] = []
    client._lore_created = created  # type: ignore[attr-defined]
    try:
        yield client
    finally:
        for name in created:
            for candidate in (name, f"{name}_memory"):
                if await client.collection_exists(candidate):
                    await client.delete_collection(candidate)
        await client.close()


class TestEagerStartupEndToEnd:
    """One real-handoff case: drive the REAL composed app's ASGI lifespan.

    This exercises the actual ``build_mcp_server`` → ``build_asgi_app`` seam with
    the REAL production guard + build factory (not a spy), faking only what the
    rest of the suite fakes — the embedder (no live TEI) — against a REAL throwaway
    Qdrant + tmp-path SQLite/snapshot dirs. It proves the eager startup fires the
    heavy build at lifespan.startup over the real wiring (the seam where a unit /
    null / handle-name mismatch would actually bite), and that shutdown tears down.
    """

    async def test_real_composed_lifespan_builds_eagerly_then_tears_down(
        self,
        tmp_path: Path,
        qdrant: AsyncQdrantClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import loremaster.embedding as embedding_module
        import loremaster.index.watcher as watcher_module
        import loremaster.server as server_module
        from conftest import _qdrant_api_key

        # The real eager build constructs its own AsyncQdrantClient from the
        # config's api_key_env; export the throwaway server's key so it connects.
        monkeypatch.setenv("QDRANT__SERVICE__API_KEY", _qdrant_api_key())

        slug = _slug()
        live = tmp_path / "live"
        (live / "pkg").mkdir(parents=True)
        (live / "pkg" / "boot.py").write_text(
            "def boot():\n    return 1\n", encoding="utf-8"
        )
        config = _config(slug, live)
        # The eager build creates the project + _memory collections from the slug;
        # register both for the fixture's exact-name reap.
        qdrant._lore_created.append(f"lore_{slug}")  # type: ignore[attr-defined]
        qdrant._lore_created.append(f"lore_{slug}_memory")  # type: ignore[attr-defined]

        # Keep it hermetic: FakeEmbedder (no live TEI), tmp-path state/snapshot dirs
        # — but otherwise the REAL composed eager lifespan. make_embedder_from_config
        # is imported at build time, so patch it at its source.
        monkeypatch.setattr(
            embedding_module,
            "make_embedder_from_config",
            lambda _embedding_config: FakeEmbedder(dim=_DIM),
        )
        monkeypatch.setattr(server_module, "_DEFAULT_MANIFEST_DIR", tmp_path / "state")
        monkeypatch.setattr(server_module, "_DEFAULT_SNAPSHOT_ROOT", tmp_path / "snap")
        (tmp_path / "state").mkdir()

        # Spy on the heavy-startup primitives WITHOUT changing their behaviour —
        # the watcher start is the unambiguous signal that the heavy build ran.
        watcher_starts = 0
        real_watcher_start = watcher_module.LiveWatcher.start

        async def _counting_watcher_start(self: Any) -> None:
            nonlocal watcher_starts
            watcher_starts += 1
            await real_watcher_start(self)

        monkeypatch.setattr(
            watcher_module.LiveWatcher, "start", _counting_watcher_start
        )

        # Build the REAL composed ASGI app and drive its raw ASGI lifespan as
        # uvicorn does at process startup: startup → shutdown, with NO HTTP request
        # and NO MCP session in between.
        mcp = build_mcp_server(LoreServer(config))
        app = build_asgi_app(mcp, config)

        replies = await _drive_lifespan(app)

        # The heavy build ran EAGERLY at process startup (the watcher started) with
        # zero sessions opened — the whole point of the feature.
        assert watcher_starts == 1, (
            f"the live watcher started {watcher_starts}x; the heavy build must run "
            f"exactly once, EAGERLY at lifespan.startup, before any MCP session"
        )
        assert "lifespan.startup.complete" in replies["all"], (
            "the real composed app must complete its eager startup"
        )
        assert "lifespan.shutdown.complete" in replies["all"], (
            "the real composed app must complete its shutdown (eager lease "
            "released → AppContext + Qdrant client torn down)"
        )


# --------------------------------------------------------------------------- #
# Lifespan-driving helpers
# --------------------------------------------------------------------------- #
class _StopLifespan(Exception):
    """Sentinel raised from a test ``send`` to stop a lifespan mid-handshake."""


async def _drive_eager_startup(app: Any) -> None:
    """Drive ``lifespan.startup`` ONLY against ``app`` — the eager lease stays HELD.

    Models "the process has STARTED and is now running": uvicorn has driven
    ``lifespan.startup``, the eager process-lifetime lease has been acquired, and
    the process is up serving — with NO shutdown yet. This is the steady-running
    state, so the eager lease is HELD (never released here) and the inner
    session-manager lifespan stays entered.

    For tests whose assertions read spy state with the process still running —
    e.g. the once-per-process reuse case (the held eager lease keeps the
    AppContext live for subsequent sessions to reuse) and the failed-build retry
    case (the retry's acquired lease is still live). For the full startup→shutdown
    round-trip that asserts the lease is RELEASED at shutdown, use
    :func:`_drive_lifespan` directly instead.

    Drives a startup-only ASGI lifespan inline (it must NOT call
    :func:`_drive_lifespan`, which would send ``lifespan.shutdown`` and release the
    eager lease): a ``receive()`` that yields a single ``lifespan.startup``, a
    ``send()`` recorder, and one ``app`` invocation that returns once startup is
    acknowledged.
    """
    sent: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return {"type": "lifespan.startup"}

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)
        # The composed startup is complete (or failed) once it has acknowledged —
        # stop the handshake here, leaving the eager lease HELD and the inner
        # lifespan entered (the steady-running state), without sending shutdown.
        if message["type"] in ("lifespan.startup.complete", "lifespan.startup.failed"):
            raise _StopLifespan

    try:
        await app({"type": "lifespan"}, receive, send)
    except _StopLifespan:
        # Expected: we unwound the handshake right after startup acknowledged, so
        # the process is left in its steady-running state (eager lease held).
        pass


async def _drive_startup_expecting_failure(app: Any) -> bool:
    """Drive ``lifespan.startup`` and report whether the eager build FAILED.

    Returns ``True`` if the failure surfaced — either the app raised out of the
    lifespan call, or it sent ``lifespan.startup.failed`` (uvicorn's abort
    signal). Returns ``False`` if startup reported ``...complete`` (a silent green
    startup over a failed build — the bug this guards against).

    Feeds the full ``startup`` → ``shutdown`` message sequence (not an endless
    stream of ``startup``) so that a composition WITHOUT an eager build completes
    its passthrough cleanly and reports ``...complete`` → ``False`` (the RED today),
    rather than tripping an inner app's protocol assertion and looking like a
    failure for the wrong reason.
    """
    sent: list[dict[str, Any]] = []
    inbox: list[dict[str, Any]] = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    cursor = {"i": 0}

    async def receive() -> dict[str, Any]:
        message = inbox[min(cursor["i"], len(inbox) - 1)]
        cursor["i"] += 1
        return message

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    try:
        await app({"type": "lifespan"}, receive, send)
    except Exception:
        # The eager build raised out of the lifespan — a valid failure surface.
        return True
    reply_types = [m["type"] for m in sent]
    if "lifespan.startup.failed" in reply_types:
        return True
    # A "...complete" reply means the failure was swallowed — NOT a valid surface.
    return False


# --------------------------------------------------------------------------- #
# Security hardening — the startup.failed ASGI message must not leak exc detail
# --------------------------------------------------------------------------- #
# A recognizable sentinel that stands in for whatever secret-bearing detail a
# future eager-build exception string could carry. The leak vector the audit
# flagged is concrete: a config like ``qdrant.url: http://user:pass@host`` would
# put credentials into an httpx/qdrant HTTP-status exception's ``str()`` — and
# the current code copies ``str(exc)`` verbatim into the ASGI startup.failed
# message, which uvicorn logs UNREDACTED. This sentinel embeds both an obvious
# marker token AND a realistic ``user:pw@host`` credential shape so the test
# fails the moment ANY part of the raw exception text reaches the ASGI message.
_LEAK_SENTINEL = "SENTINEL-SECRET-abc123 http://leak_user:leak_pw@qdrant.internal:6333"

# The contract's independent oracle: the startup.failed message must be a FIXED,
# operator-safe phrase that is NOT a function of the exception. This is the
# *requirement*, not a transcription of the impl — the message is asserted to be
# a constant string the implementation may not yet emit (RED today). The fixed
# wording itself is the impl's choice; the contract pins (a) the sentinel is
# absent and (b) the message names the eager-build-startup failure generically.
_OPERATOR_SAFE_PHRASE_FRAGMENT = "startup"


class _LeakingSpyGuard(_SpyGuard):
    """A spy guard whose eager build raises an exception carrying a secret.

    Reuses the existing :class:`_SpyGuard` lease-counting machinery (so the
    composition's acquire/release sequencing is exercised exactly as in the other
    failure tests) but overrides ``acquire`` to raise a ``RuntimeError`` whose
    ``str()`` contains :data:`_LEAK_SENTINEL`. This reproduces the audit's leak
    vector: a real eager-build failure (e.g. a Qdrant connect error against a
    credentialed URL) whose exception string carries secret material the operator
    never wants copied into uvicorn's startup log.

    ``fail_acquire_times`` is honoured via the parent so the first acquire raises
    (the eager build fails) — but with the secret-bearing message, not the
    parent's fixed ``"eager build failed"`` literal.
    """

    async def acquire(self) -> Any:
        self.acquire_calls += 1
        if self.acquire_calls <= self._fail_acquire_times:
            raise RuntimeError(_LEAK_SENTINEL)
        self.live_leases += 1
        return self._sentinel_context


async def _drive_startup_capturing_failed_message(app: Any) -> str | None:
    """Drive ``lifespan.startup`` and RETURN the startup.failed ``message`` sent.

    Unlike :func:`_drive_startup_expecting_failure` (which discards the payload
    and returns only a bool), this captures the full reply stream and returns the
    string in the ``lifespan.startup.failed`` reply's ``message`` field — the
    exact bytes uvicorn would log. Returns ``None`` if the app raised out of the
    lifespan instead of sending a structured ``startup.failed`` (a different,
    also-non-leaking failure surface) or if no ``startup.failed`` was sent.

    Feeds the full startup -> shutdown sequence (mirroring
    :func:`_drive_startup_expecting_failure`) so a composition that completes its
    passthrough does not trip an inner protocol assertion for the wrong reason.
    """
    sent: list[dict[str, Any]] = []
    inbox: list[dict[str, Any]] = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    cursor = {"i": 0}

    async def receive() -> dict[str, Any]:
        message = inbox[min(cursor["i"], len(inbox) - 1)]
        cursor["i"] += 1
        return message

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    try:
        await app({"type": "lifespan"}, receive, send)
    except Exception:
        # The eager build raised out of the lifespan rather than sending a
        # structured startup.failed — no ASGI message string to inspect.
        return None
    for message in sent:
        if message["type"] == "lifespan.startup.failed":
            # uvicorn reads the "message" field for its startup-failure log line.
            return message.get("message")
    return None


class TestEagerBuildFailureMessageDoesNotLeakSecrets:
    """The startup.failed ASGI message is operator-safe; the detail goes to the log.

    Security hardening (from the security audit). uvicorn logs the ASGI
    ``lifespan.startup.failed`` ``message`` field UNREDACTED at process startup,
    so copying ``str(exc)`` into it is a latent secret-leak path: a credentialed
    ``qdrant.url`` (or any secret that surfaces in an HTTP-status exception) lands
    in the startup log. The contract:

    1. The ASGI startup.failed message must be a FIXED, operator-safe string that
       does NOT contain the exception's text (the independent oracle: a constant,
       never a function of ``exc``).
    2. The real failure detail must still reach operators — logged through
       loremaster's own ``logging.getLogger("loremaster.server")`` logger, which
       is the redaction-backstopped sink. The sentinel MAY appear there (its
       intended destination); it must NOT appear in the ASGI message.
    """

    async def test_failed_eager_build_message_is_operator_safe_and_logs_detail(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # Arrange: a composition whose eager build raises an exception carrying a
        # secret-bearing sentinel. Read the logger NAME from the module itself
        # (clause 5: shared source of truth, never a hand-copied literal) so the
        # caplog capture targets exactly the logger the impl logs through.
        import logging

        import loremaster.server as server_module

        lore_logger_name = server_module.logger.name  # "loremaster.server"

        guard = _LeakingSpyGuard(fail_acquire_times=1)
        inner = _SpyInnerApp()
        app = TestEagerLifespanComposition._compose_with_spies(
            tmp_path, guard=guard, inner=inner
        )

        # Act: drive lifespan.startup; the eager build fails. Capture BOTH the
        # ASGI startup.failed message bytes uvicorn would log AND any records the
        # loremaster logger emits on this path.
        with caplog.at_level(logging.ERROR, logger=lore_logger_name):
            failed_message = await _drive_startup_capturing_failed_message(app)

        # The failure must surface as a structured startup.failed (uvicorn's abort
        # signal) — that is the message whose contents this contract governs.
        assert failed_message is not None, (
            "a failed eager build must report a structured lifespan.startup.failed "
            "so uvicorn aborts (and so there is an operator-facing message to "
            "harden) — never raise an opaque error or silently complete"
        )

        # Assertion 1 (independent oracle): the ASGI message is a FIXED phrase, NOT
        # a copy of the exception. The sentinel — and specifically the credential
        # shape inside it — must be wholly absent. This goes RED against the
        # current impl, which sends str(exc) == _LEAK_SENTINEL verbatim.
        assert _LEAK_SENTINEL not in failed_message, (
            f"the startup.failed message uvicorn logs UNREDACTED must NOT carry the "
            f"exception text; it leaked the sentinel secret: {failed_message!r}"
        )
        # Belt-and-suspenders on the credential substring specifically (the part an
        # operator log must never contain), independent of the marker token.
        assert "leak_pw" not in failed_message and "leak_user" not in failed_message, (
            "the startup.failed message must not carry credentials from the "
            "exception (the qdrant.url user:pass leak vector the audit flagged)"
        )
        # ...and it must read as a fixed operator-safe phrase naming the failure,
        # not the empty string or an exc-derived value. (Substring, not equality:
        # the exact wording is the impl's choice; the constant-ness is the oracle.)
        assert _OPERATOR_SAFE_PHRASE_FRAGMENT in failed_message.lower(), (
            f"the startup.failed message must be a fixed, operator-safe phrase that "
            f"names the startup failure generically; got {failed_message!r}"
        )

        # Assertion 2: operators still get the real detail — a failure record was
        # logged through loremaster's redaction-backstopped logger on this path,
        # at ERROR (the level run_probe_gate/other startup-failure paths use). The
        # sentinel MAY appear in the captured record (its intended destination);
        # what matters is that SOME failure record was emitted on the eager-build
        # failure path so the detail is not simply discarded with the leak fix.
        eager_failure_records = [
            record
            for record in caplog.records
            if record.name == lore_logger_name and record.levelno >= logging.ERROR
        ]
        assert eager_failure_records, (
            "the eager-build failure detail must be logged through loremaster's "
            "own logger (the redaction-backstopped sink) at ERROR — so hardening "
            "the ASGI message does not blind operators to WHY startup failed"
        )
