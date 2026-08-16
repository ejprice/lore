"""Contract for packet 59 — migrate lore's MCP façade to standalone ``fastmcp`` 3.x.

**Spec (execute verbatim; a genuine gap is a STOP-and-flag, never an improvised
design decision):** ``docs/design/2026-08-15-fastmcp-3x-migration.md`` — §3 (the
coupling→migration map), §5 (the DUAL removed-behaviour inventory B1–B8 / C1–C5 /
D1–D7), §6 (acceptance gates), §9 (the FG1–FG8 false-green scenarios), §12 (bounds).
Cite its sections; never re-transcribe. The spike GO receipts this contract builds
on: ``docs/plans/v2/receipts/2026-08-15-fastmcp-migration/`` (once archived) and
``scripts/fastmcp_migration_spike.py``.

WHAT THIS PACKET IS (design §1)
------------------------------
A pure SUBSTRATE swap of lore's MCP server FAÇADE — from ``mcp.server.fastmcp.FastMCP``
to standalone ``fastmcp.FastMCP`` 3.x. The **served behaviour does not change**: same 15
tools, same wire protocol, same trace emission, same Origin/Bearer auth. Trust Leg 1 is
*"does the server behave identically after swapping the façade?"* — and any diff in wire
protocol / tool set / trace emission / auth posture is a **DEFECT**, not a feature. This
file is the DUAL: every deleted behaviour has a preserved discriminating pin or a ruled
DROP, so a build written for the fastmcp world cannot silently drop an old-world virtue
(design §9-FG5).

RED DEPENDS ON THE DEP SWAP (stated per the brief)
--------------------------------------------------
These pins import ``fastmcp``. ``fastmcp`` is NOT yet a lore dependency — the BUILD adds
``"fastmcp>=3.4,<4"`` to ``loremaster/pyproject.toml`` and ``uv sync``s (design §3
packaging, D4). Until then this module is UNCOLLECTABLE (import error), which is a
DIFFERENT state from RED; that is expected and is the build's first step. The unbuilt
LORE symbols (the trace middleware, the deleted apparatus) are reached at CALL time so a
pin fails for ITS OWN reason once fastmcp is present, never at collection.

THE MIGRATION ACCEPTANCE GATE IS THE FULL SUITE, NOT ``--collect-only`` (contract-59b ⑤)
----------------------------------------------------------------------------------------
The design §6.6 collection gate (``pytest --collect-only``, zero-new-delta vs #333) is
NECESSARY but NOT SUFFICIENT as the migration's acceptance instrument: it is BLIND to
RUNTIME breakages the migration causes. collect-only sees only a module-level ImportError
(e.g. ``test_eager_startup.py``'s ``from loremaster.server import _ProcessLifespanGuard``);
it CANNOT see a test whose BODY reaches ``mcp._tool_manager`` (renamed ``_local_provider``
→ AttributeError), a mock-patch of a deleted symbol, or a ``pytest.raises`` keyed on the
wrong ``ToolError`` class. The migration's acceptance gate MUST therefore be a FULL-SUITE
run (``pytest -n auto``) OR the §6.1 in-image conformance — never collect-only alone. The
files the migration breaks at RUNTIME (adversary-59 ⑤, measured on the reference build) are
enumerated in :data:`_MIGRATION_AFFECTED_TEST_FILES` and pinned as a build worklist by
:class:`TestTheMigrationAffectedTestFilesAreEnumerated` (SECTION H). The FIXING of those
files is the BUILD's job; this contract NAMES them so the build meets them deliberately and
pins that the full suite must pass post-migration.

§0 — EVERY fastmcp 3.x FACT BELOW WAS RE-VERIFIED against installed 3.4.7 source
-------------------------------------------------------------------------------
(introspection + an empirical wire probe, 2026-08-15; receipts pasted verbatim in
``REPORT-contract-59.md`` §"fastmcp 3.x verification"). The load-bearing ones:

* ``from fastmcp import FastMCP, Context`` · ``from fastmcp.exceptions import ToolError``
  (MRO ToolError→FastMCPError→Exception→BaseException).
* ``FastMCP.__init__`` takes ``version=`` / ``lifespan=`` / ``middleware=`` / ``auth=`` /
  ``on_duplicate=`` and **NO** ``host`` / ``port`` / ``streamable_http_path``.
* ``FastMCP.http_app(path=…, stateless_http=…, host_origin_protection=…, allowed_hosts=…,
  allowed_origins=…)`` — there is **no** ``streamable_http_app`` method (C1).
* ``mcp._tool_manager`` is **GONE** (renamed ``_local_provider``); public ``get_tool`` is
  ``async`` → ``await mcp.get_tool(name) is not None`` (P9 hard break).
* ``Middleware.on_call_tool(context: MiddlewareContext[CallToolRequestParams], call_next)
  -> ToolResult`` / ``on_list_tools`` — the funnel; ``mcp.middleware`` is a public list.
* ``MiddlewareContext`` fields: ``message`` (has ``.name`` / ``.arguments``) +
  ``fastmcp_context: Context | None``.
* Injection is ANNOTATION-based (a ``context: Context`` param is injected) — confirmed on
  the wire for BOTH a built-in and an ``add_tool``-registered extension tool (design §12,
  FG7). ``context.request_context.lifespan_context`` yields the lifespan value, so
  ``_app_context``'s BODY is unchanged (only the ``Context[...]`` annotation must change).

⚠ FIVE COUPLINGS THE DESIGN P-TABLE UNDER-SPECIFIES (measured; full detail in the report):
1. **``Context[Any, AppContext, Any]`` is NOT subscriptable in fastmcp** (``TypeError: type
   'Context' is not subscriptable``). All 15 built-ins + ``_app_context`` +
   ``_extension_tool_wrapper`` annotate it → a **tool-REGISTRATION break, NOT a module-load
   break** (contract-59b correction ④, adversary-59: #107-class read-then-verify). ``server.py``
   carries ``from __future__ import annotations`` (PEP-563), so EVERY annotation is a STRING that
   is never evaluated at import — ``import loremaster.server`` SUCCEEDS with the ``Context[...]``
   sites unfixed. The ``TypeError`` fires later, at TOOL REGISTRATION inside ``build_mcp_server``,
   where fastmcp/pydantic resolves the string annotation. So the bare-import smoke
   (``test_loremaster_server_imports_under_fastmcp``) PASSES on the broken build; the DISCRIMINATOR
   is the ``built_server``-fixture pins (``…constructs_a_fastmcp_instance`` /
   ``…fifteen_builtin_tools_register`` ERROR at the fixture). The build must change every
   ``Context[...]`` → ``Context``. Pinned by :class:`TestTheMigratedServerImportsAndBuilds`.
2. **``add_tool(self, tool)`` is single-arg** in fastmcp — ``mcp.add_tool(wrapper, name=…,
   description=…, annotations=…)`` (``_register_extension_tools``) breaks. Adapt via
   ``mcp.tool(name=…, description=…, annotations=…)(wrapper)`` (probed working). Pinned by
   the D6 extension-registration pins.
3. **``_auth_fixtures.stub_heavy_startup`` reaches ``mcp._lore_eager_guard._build``** — which
   the Item-1 lifespan DELETE removes; every ``wire_session`` pin breaks unless the build
   updates that SHARED harness (OUTSIDE this contract's writable set — FLAGGED).
4. **The P9 collision check is SYNC** (``_register_extension_tools`` is a sync function) while
   fastmcp's public ``get_tool`` is ASYNC — the build needs a sync path (a local
   registered-names set, keeping the ``_ALL_BUILTIN_TOOL_NAMES`` universe check).
5. **``_record_tool_trace`` is a METHOD on the deleted subclass** — M4 preserves the WRITE
   POLICY, but its home moves and its store/headers accessors change (design B5/B7).
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import inspect
import json
import logging
import re
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any, cast

import anyio
import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)

# fastmcp is present AFTER the build's D4 dep swap (module-level import = the expected
# uncollectable-until-swap state, per the header). mcp rides transitively (design §2/D4).
# ``Client`` is fastmcp's in-memory client — it RUNS the user ``lifespan=`` and dispatches
# through the installed middleware WITHOUT a uvicorn/TCP server (verified 2026-08-16 against
# installed 3.4.7; the funnel-∀ pin below rests on it — contract-59b ③, adversary-59 §PROBES).
from fastmcp import Client, Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext
from loremaster.config import LoreConfig
from loremaster.server import LoreServer, build_mcp_server
from loremaster.store.surreal import SurrealStore, SurrealStoreError
from mcp.types import CallToolRequestParams

# --------------------------------------------------------------------------- #
# The interface THIS CONTRACT DEFINES (the build must provide it; fetched at CALL
# time so a pin fails for its own reason, never at collection — see the header).
#
# The trace subclass ``TracingFastMCP`` is RETIRED (design M3); its ``call_tool``
# override becomes an ``on_call_tool`` middleware. I name that middleware class here —
# the build implements it in ``loremaster.server``, subclassing
# ``fastmcp.server.middleware.Middleware``, reusing the ``_record_tool_trace`` WRITE
# policy unchanged (design M4). If the build prefers a different class name, this ONE
# constant changes; nothing else in the file hardcodes it.
# --------------------------------------------------------------------------- #
_TRACE_MIDDLEWARE_NAME = "ToolTraceMiddleware"


def _trace_middleware_class() -> type[Middleware]:
    """The ``on_call_tool`` trace middleware the migration installs, fetched at call time."""
    server = importlib.import_module("loremaster.server")
    cls = getattr(server, _TRACE_MIDDLEWARE_NAME, None)
    assert cls is not None, (
        f"loremaster.server.{_TRACE_MIDDLEWARE_NAME} does not exist. Design M3 retires the "
        f"TracingFastMCP subclass and re-homes its call_tool override to an `on_call_tool` "
        f"middleware (a fastmcp.server.middleware.Middleware subclass) reusing "
        f"_record_tool_trace unchanged (M4). The spike PROVED middleware gates/observes on the "
        f"wire (§Q1); a `call_tool` override on a fastmcp subclass is untested and betting on it "
        f"is the design's central rejected option."
    )
    assert issubclass(cls, Middleware), (
        f"{_TRACE_MIDDLEWARE_NAME} must subclass fastmcp.server.middleware.Middleware so its "
        f"on_call_tool hook runs on the wire dispatch path (spike §Q1)."
    )
    # ``getattr`` returns Any; the asserts above prove it is a ``type[Middleware]`` at
    # runtime, but mypy cannot narrow Any through ``issubclass`` — cast (not an assertion
    # change: the runtime check is unchanged) so the declared return type holds (no-any-return).
    return cast(type[Middleware], cls)


def _make_trace_middleware() -> Middleware:
    """Construct the trace middleware (no-arg: it reads everything off the per-call context)."""
    return _trace_middleware_class()()


# --------------------------------------------------------------------------- #
# Config + app-context doubles.
# --------------------------------------------------------------------------- #
_DIM = 2048


def _config(slug: str, *, tools: list[str] | None = None) -> LoreConfig:
    """A minimal validated config: enough to BUILD a server, never to connect.

    ``tools`` (when given) becomes the ``tools.enabled`` allowlist, so a pin can DISABLE a
    built-in and prove its name is still reserved against an extension collision (packet 45).
    """
    payload: dict[str, Any] = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
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
        "surreal": {
            # The TEST store. :18500 is PRODUCTION and is never a test target.
            "url": "ws://127.0.0.1:18000/rpc",
            "namespace": "lore_test",
            "user_env": "SURREAL_USER",
            "password_env": "SURREAL_PASS",
        },
        "roots": [],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": False,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9233},
    }
    if tools is not None:
        payload["tools"] = {"enabled": tools}
    return LoreConfig.model_validate(payload)


class _TraceRecorder:
    """The ``AppContext.write_store`` stand-in — captures every emission ATTEMPT.

    Binds against the REAL ``SurrealStore.record_trace`` signature so the double can never
    accept what the real store would reject: a keyword the real store does not declare, or a
    required one the seam forgot, raises here exactly as it would there. That turns every
    double-backed pin into an end-to-end signature check by construction (the W30/W33 class),
    while a real-store leg (:class:`TestTheMigratedSeamLandsARealRow`) closes the value/type
    half ``Signature.bind`` cannot see.
    """

    _REAL_SIGNATURE = inspect.signature(SurrealStore.record_trace)

    def __init__(self, *, failure: BaseException | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._failure = failure

    async def record_trace(self, **fields: Any) -> None:
        self._REAL_SIGNATURE.bind(None, **fields)  # None stands in for the bound `self`
        self.calls.append(dict(fields))
        if self._failure is not None:
            raise self._failure


class _SuspendingTraceRecorder(_TraceRecorder):
    """A recorder that SUSPENDS before recording — the real store's own shape.

    ``SurrealStore.record_trace`` is a network round-trip and ALWAYS suspends; a cancellation
    is delivered at the next suspension point, so only a suspending emission can model the
    shield's job. A non-suspending double completes whether shielded or not — the exact blind
    cell that let an unshielded build pass green (design B4 / §9-FG3).
    """

    async def record_trace(self, **fields: Any) -> None:
        await asyncio.sleep(0)
        await super().record_trace(**fields)


def _app_context_double(recorder: Any) -> Any:
    """A fastmcp ``Context`` stand-in whose lifespan value carries ``write_store``.

    Exposes the AppContext via BOTH accessors the empirical probe proved yield the lifespan
    value under fastmcp — ``.request_context.lifespan_context`` AND ``.lifespan_context`` — so
    the pin does not couple to which one the build's middleware reads (both were measured to
    work; design B5, FG7). ``fastmcp_context`` on the MiddlewareContext is THIS object.
    """
    app_context = SimpleNamespace(write_store=recorder)
    request_context = SimpleNamespace(lifespan_context=app_context, request=None)
    return SimpleNamespace(
        lifespan_context=app_context,
        request_context=request_context,
    )


def _no_store_fastmcp_context() -> Any:
    """A ``Context`` whose lifespan value carries NO ``write_store`` (the B6 un-wired shape)."""
    app_context = SimpleNamespace()  # no write_store attribute -> AttributeError on access
    request_context = SimpleNamespace(lifespan_context=app_context, request=None)
    return SimpleNamespace(lifespan_context=app_context, request_context=request_context)


def _recorder_lifespan_factory(recorder: Any) -> Any:
    """Build a fastmcp ``lifespan=`` that yields an AppContext-shaped value with ``write_store``.

    fastmcp exposes whatever the lifespan yields at ``context.request_context.lifespan_context``
    (verified 2026-08-16 against installed 3.4.7) — exactly where the trace middleware reads
    ``write_store``. So an in-memory ``Client`` dispatch drives the REAL emission into ``recorder``
    with NO real SurrealDB and NO uvicorn. Used only by the funnel-∀ pin, to prove the middleware's
    REACH over both tool-registration paths. A closure (not module state) so each pin gets its own
    recorder with no cross-test leakage.
    """

    @asynccontextmanager
    async def _lifespan(_server: Any) -> Any:
        yield SimpleNamespace(write_store=recorder)

    return _lifespan


def _middleware_context(
    *, name: str, arguments: dict[str, Any], fastmcp_context: Any
) -> MiddlewareContext[Any]:
    """A real ``MiddlewareContext`` carrying a ``CallToolRequestParams`` message + a context."""
    return MiddlewareContext(
        message=CallToolRequestParams(name=name, arguments=arguments),
        fastmcp_context=fastmcp_context,
    )


class _SENTINEL_RESULT:
    """A unique object a ``call_next`` returns, so B2's "outcome wins" is an identity check."""


async def _drive_on_call_tool(
    middleware: Middleware,
    *,
    name: str,
    arguments: dict[str, Any],
    fastmcp_context: Any,
    call_next: Any,
) -> Any:
    """Drive the migrated funnel: ``middleware.on_call_tool(ctx, call_next)``.

    This is the middleware equivalent of the retired ``FastMCP.call_tool`` dispatch. It is a
    UNIT drive of the seam's own logic (ok-latch, shield, failure posture, identity harvest);
    the wire-level funnel/coverage lives in the §6.1/§6.2 gates below.
    """
    context = _middleware_context(name=name, arguments=arguments, fastmcp_context=fastmcp_context)
    return await middleware.on_call_tool(context, call_next)


async def _registered_tool_names(mcp: Any) -> set[str]:
    """The registered tool names, read the fastmcp way (``await mcp.list_tools()``)."""
    return {tool.name for tool in await mcp.list_tools()}


def _tool_input_properties(tool: Any) -> dict[str, Any]:
    """The tool's published input-schema ``properties`` (fastmcp ``Tool.parameters``).

    ``Tool.parameters`` is the JSON schema fastmcp publishes as ``inputSchema`` on the wire —
    verified against installed 3.4.7 (2026-08-16): ``{'additionalProperties', 'properties',
    'required', 'type'}``, and the injected ``context: Context`` param is EXCLUDED from
    ``properties`` (a ``context: Any`` param is NOT). Read here (not over the wire) so the ②
    injection pin needs no uvicorn and no lifespan.
    """
    parameters = getattr(tool, "parameters", None)
    assert isinstance(parameters, dict), (
        f"the fastmcp Tool for {getattr(tool, 'name', tool)!r} exposes no dict `parameters` "
        f"(got {type(parameters).__name__}); the input-schema accessor changed — re-verify "
        f"against the installed fastmcp before trusting this pin."
    )
    properties = parameters.get("properties", {})
    return properties if isinstance(properties, dict) else {}


def _injected_context_param_name() -> str:
    """The param name fastmcp injects the request :class:`Context` on — production's convention.

    Read from ``loremaster.server._RESERVED_TOOL_PARAM`` (the name a ToolSpec handler may not
    re-declare precisely BECAUSE it collides with the injected context), so this pin tracks the
    production constant rather than hard-coding ``"context"`` (tdd-contract clause 5: obtain the
    convention from the same source of truth as production). Fetched at CALL time (never at
    import) so a build that renamed it fails for its own reason, never at collection.
    """
    server = importlib.import_module("loremaster.server")
    return getattr(server, "_RESERVED_TOOL_PARAM", "context")


# --------------------------------------------------------------------------- #
# Fixtures — a real trace store, so the funnel's real-row legs (W30/W33) can read back.
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture()
async def trace_store() -> Any:
    """A ready real :class:`SurrealStore` on a fresh throwaway database (TEST store only)."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    store = SurrealStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        dim=env.dim,
        user=env.user,
        password=env.password,
    )
    await store.ensure_ready()
    try:
        yield store
    finally:
        await store.close()
        await drop_database(env)


@pytest.fixture()
def built_server(monkeypatch: pytest.MonkeyPatch) -> Any:
    """A REAL server built through production ``build_mcp_server`` (registration only).

    ``build_mcp_server`` registers tools synchronously; nothing connects until the lifespan
    runs. If the ``Context[Any, AppContext, Any]`` sites broke tool REGISTRATION (coupling #1 —
    the ``TypeError`` fires HERE, inside ``build_mcp_server``, NOT at import, because
    ``server.py`` has ``from __future__ import annotations``; see the header ④), or the ctor
    kwargs are wrong (design D2), THIS fixture raises — every dependent pin then fails loudly.
    """
    monkeypatch.setenv("SURREAL_USER", "root")
    monkeypatch.setenv("SURREAL_PASS", "root")
    return build_mcp_server(LoreServer(_config("migration_probe")))


# =========================================================================== #
# SECTION A — the migration LOADS and BUILDS (coupling #1: Context subscript break)
# =========================================================================== #
class TestTheMigratedServerImportsAndBuilds:
    """The whole surface must survive the ``mcp.server.fastmcp`` → ``fastmcp`` swap.

    THE WRONG BUILD (measured, coupling #1): the swap changes only the 3 import lines and the
    façade class, leaving all 15 built-ins annotated ``context: Context[Any, AppContext, Any]``.
    fastmcp's ``Context`` is NOT subscriptable (``TypeError: type 'Context' is not
    subscriptable``).

    ⚠ CORRECTION (contract-59b ④, adversary-59; the #107 read-then-verify class): this is a
    tool-REGISTRATION break, NOT a module-load break. ``server.py`` carries
    ``from __future__ import annotations`` (PEP-563) → every annotation is a STRING that is
    never evaluated at import, so ``import loremaster.server`` SUCCEEDS with the ``Context[...]``
    sites unfixed. The ``TypeError`` fires later, when fastmcp/pydantic resolves the string
    annotation at TOOL REGISTRATION inside ``build_mcp_server``. Consequence for these pins:
    the bare-import smoke below PASSES on the broken build (it is a valid façade-identity smoke,
    NOT the coupling-#1 discriminator); the DISCRIMINATION lives entirely in the
    ``built_server``-fixture pins (``…constructs_a_fastmcp_instance`` /
    ``…fifteen_builtin_tools_register``), which ERROR at the fixture on the broken build. This
    pin is the first gate: the module imports, the server builds, the façade is fastmcp's, and
    all 15 built-ins register.
    """

    def test_loremaster_server_imports_under_fastmcp(self) -> None:
        # ⚠ NOT the coupling-#1 discriminator (see the class docstring ④): PEP-563 future-
        # annotations mean import SUCCEEDS even with the Context[...] sites unfixed. This is a
        # façade-IDENTITY smoke — it proves the swap reached `from fastmcp import FastMCP` — and
        # it PASSES on the Context-unfixed build. The registration break is caught by the
        # built_server-fixture pins below.
        server = importlib.import_module("loremaster.server")
        # The façade is now standalone fastmcp, not the mcp SDK's bundled one.
        assert server.FastMCP.__module__.startswith("fastmcp"), (
            f"loremaster.server.FastMCP resolves to {server.FastMCP.__module__} — the migration "
            f"must import `from fastmcp import FastMCP` (design P1), not mcp.server.fastmcp."
        )

    def test_build_mcp_server_constructs_a_fastmcp_instance(self, built_server: Any) -> None:
        assert isinstance(built_server, FastMCP), (
            f"build_mcp_server returned a {type(built_server).__name__}; the ONE construction "
            f"site must build a standalone fastmcp.FastMCP (design §5c-D1)."
        )

    async def test_all_fifteen_builtin_tools_register(self, built_server: Any) -> None:
        registered = await _registered_tool_names(built_server)
        # NON-VACUITY (a build registering nothing would pass a subset check).
        assert registered, "the built server registered NO tools — Context[...] likely broke load"
        expected = {
            "lore_search", "lore_get_symbol", "lore_verify", "lore_remember", "lore_recall",
            "lore_claim_task", "lore_tasks", "lore_comms", "lore_impact", "lore_map",
            "lore_read", "lore_dead_code", "lore_diff", "lore_index", "lore_findings",
        }
        assert expected <= registered, (
            f"missing built-in tools after the migration: {sorted(expected - registered)}. "
            f"A tool whose `context: Context[...]` annotation broke import, or whose registration "
            f"changed, silently vanishes from the served surface."
        )

    def test_mcp_still_importable_transitively(self) -> None:
        # D4: `mcp` rides transitively via fastmcp-slim; `mcp.types` stays a direct import and
        # the 11 packet-39 pending files still COLLECT (design §6.6 / §11-D4). If a build
        # dropped mcp entirely, this smoke — and that whole collection gate — goes red.
        importlib.import_module("mcp.types")
        importlib.import_module("mcp.server.fastmcp")


class TestContextIsInjectedNotPublishedInTheToolSchema:
    """P14 / coupling #1: the ``context: Context`` param is INJECTED — it may not be published.

    THE WRONG BUILD (measured, adversary-59 ② — the gap SECTION A does not close): a build that
    dodges the coupling-#1 ``TypeError`` by WEAKENING the annotation (``context: Context`` →
    ``context: Any``, or dropping it) passes EVERY SECTION A pin — the module imports and all 15
    tools REGISTER — but silently breaks INJECTION. fastmcp injects a parameter as the request
    :class:`Context` ONLY when it is annotated ``Context``; weaken that and fastmcp treats
    ``context`` as an ordinary client argument, so it LEAKS into every tool's published
    ``inputSchema.properties`` as a REQUIRED arg the consumer cannot supply (adversary probe:
    ``weak: props=['context','q']`` vs ``good: props=['q']``) — every tool is then unusable on
    the wire. SECTION A pins REGISTRATION; this pins INJECTION, the property the ``Context→Any``
    dodge destroys. Runs against ``built_server`` via ``get_tool``/``list_tools`` — NO uvicorn,
    NO lifespan (the schema is read from the registered Tool object; verified 2026-08-16).
    """

    async def test_no_builtin_tool_publishes_the_injected_context_param(
        self, built_server: Any
    ) -> None:
        injected = _injected_context_param_name()
        leaked: list[str] = []
        saw_a_real_client_param = False
        for name in await _registered_tool_names(built_server):
            tool = await built_server.get_tool(name)
            properties = _tool_input_properties(tool)
            if injected in properties:
                leaked.append(name)
            if properties:  # NON-VACUITY: at least one tool exposes real client args, so a
                saw_a_real_client_param = True  # build publishing empty schemas cannot pass mute.
        assert saw_a_real_client_param, (
            "no built-in tool published ANY input property — the schema read is vacuous, so "
            f"'{injected} is absent' proves nothing (a build that published empty schemas, or a "
            "broken accessor, would pass this pin without demonstrating injection works)."
        )
        assert not leaked, (
            f"tools {sorted(leaked)} publish the injected {injected!r} parameter in their input "
            f"schema — the `context: Context` annotation was weakened to `Any`/dropped (the "
            f"coupling-#1 dodge), so fastmcp stopped injecting it and it leaked to the wire as a "
            f"required client argument. Every such tool is unusable (a consumer cannot supply "
            f"{injected!r}). The fix is a BARE `context: Context`, never `Any` (adversary-59 ②)."
        )


# =========================================================================== #
# SECTION B — the trace FUNNEL re-homed onto on_call_tool middleware (design §5a: B1–B8)
# =========================================================================== #
class TestTheTraceMiddlewareIsInstalledAtTheOneFunnel:
    """B1 / D7: the trace middleware is installed at the ONE construction site.

    THE WRONG BUILD (design D7 / §9-FG1): a middleware that exists, is unit-tested, and is
    never installed — ``build_mcp_server`` constructs a plain FastMCP with no trace middleware.
    That build passes every direct-drive emission pin while the served trace count stays 0
    forever (#147's shape). The one-line mutation (drop the install) must go RED here.

    ⚠ ``mcp.middleware`` already contains a built-in ``DereferenceRefsMiddleware``, so this
    counts INSTANCES of the trace class, never ``len(...) == 1``.
    """

    def test_build_mcp_server_installs_exactly_one_trace_middleware(self, built_server: Any) -> None:
        cls = _trace_middleware_class()
        installed = [mw for mw in built_server.middleware if isinstance(mw, cls)]
        assert len(installed) == 1, (
            f"the built server carries {len(installed)} {_TRACE_MIDDLEWARE_NAME} instances, "
            f"expected exactly 1. Zero = nothing is traced (a plain FastMCP); more than one = "
            f"every dispatch is double-counted, corrupting the decay denominator packet 06 reads. "
            f"Installed middleware: {[type(mw).__name__ for mw in built_server.middleware]}"
        )


class TestTheMigratedFunnelRecordsOneRowPerDispatch:
    """B1 (unit): the middleware writes exactly ONE trace row per dispatch, ∀ outcomes.

    Drives ``on_call_tool`` directly (the retired ``FastMCP.call_tool`` override's replacement).
    Coverage-∀ across registration paths (built-in vs extension) is the WIRE gate below
    (§6.2 / FG2), because middleware reach is now a variable, not "by construction".
    """

    async def test_a_returning_dispatch_records_exactly_one_row(self) -> None:
        recorder = _TraceRecorder()

        async def _ok(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        result = await _drive_on_call_tool(
            _make_trace_middleware(),
            name="lore_search",
            arguments={"query": "champion routing"},
            fastmcp_context=_app_context_double(recorder),
            call_next=_ok,
        )
        assert result is _SENTINEL_RESULT, (
            "B2: the tool's OUTCOME always wins — the middleware must return call_next's result "
            "UNCHANGED, never a rewrapped or telemetry-derived value."
        )
        assert len(recorder.calls) == 1, (
            f"a dispatch wrote {len(recorder.calls)} rows, expected exactly 1. Zero = this "
            f"registration path is not funnelled; more than one = a double-counted denominator."
        )
        assert recorder.calls[0]["tool"] == "lore_search", (
            f"the row records tool={recorder.calls[0].get('tool')!r} — the funnel must record the "
            f"DISPATCHED name, not a constant."
        )
        assert recorder.calls[0]["ok"] is True, (
            "B3 latch: a dispatch that RETURNED records ok=True."
        )


class TestTheTraceMiddlewareFunnelsBothRegistrationPaths:
    """B1 funnel-∀ / FG2 (adversary-59 ③): the middleware is REACHED on BOTH registration paths.

    THE WRONG BUILD (design §9-FG2): the retired ``TracingFastMCP`` subclass funnelled EVERY tool
    'by construction'; an ``on_call_tool`` middleware's coverage is now a REACH VARIABLE. A build
    whose middleware fires for ``@mcp.tool`` built-ins but NOT for ``add_tool``-registered
    extension tools produces zero trace rows for extension calls — invisible to every direct-drive
    pin above (they exercise only the built-in shape). D6 pins that extensions REGISTER and D7
    that the middleware is INSTALLED exactly once; THIS pin makes the FUNNEL a CHECKED VARIABLE
    over BOTH registration paths (the instrument-lesson reach requirement) at a RUNNABLE level.

    HOW (verified feasible in-memory 2026-08-16; adversary-59 §PROBES): an in-memory ``Client``
    RUNS the user ``lifespan=`` and dispatches through the installed middleware, so a lifespan
    yielding a recorder-backed AppContext lets the REAL trace middleware land one row per dispatch
    with NO uvicorn/SurrealDB. It registers one tool the ``@mcp.tool`` (built-in) way AND one the
    ``mcp.tool(name=…)(wrapper)`` way — the EXACT adaptation the migration uses for extension
    tools (coupling #2 / design D6) — then asserts BOTH are funnelled. The §6.2 real-uvicorn wire
    smoke keeps the full ``build_mcp_server`` + ``register_extension(CounterExtension)`` path as
    the deploy-lane belt-and-braces (design §6.2); this is the runnable CHECKED variable beneath it.
    """

    _BUILTIN_PATH_TOOL = "funnel_builtin_path_tool"
    _EXTENSION_PATH_TOOL = "funnel_extension_path_tool"

    def _server_with_both_registration_paths(self, recorder: _TraceRecorder) -> FastMCP:
        """Build a probe server: the real trace middleware + one tool per registration path."""
        mcp = FastMCP(
            name="funnel_probe",
            version="funnel-1",
            lifespan=_recorder_lifespan_factory(recorder),
            middleware=[_make_trace_middleware()],
        )

        # Path 1 — the BUILT-IN registration path: `@mcp.tool` (as `_register_tools` uses for the
        # 15 built-ins). A `context: Context` param is injected, matching every real built-in.
        @mcp.tool(name=self._BUILTIN_PATH_TOOL)
        async def _builtin_path_tool(query: str, context: Context) -> str:
            return "builtin path ok"

        # Path 2 — the EXTENSION registration path: `mcp.tool(name=…)(wrapper)`, the single-arg
        # `add_tool` adaptation coupling #2 requires (`_register_extension_tools`). Same shape as
        # the migration's `_extension_tool_wrapper`: a `context: Context` param + declared args.
        async def _extension_path_wrapper(count: int, context: Context) -> str:
            return "extension path ok"

        mcp.tool(name=self._EXTENSION_PATH_TOOL, description="extension-path probe tool")(
            _extension_path_wrapper
        )
        return mcp

    async def test_both_registration_paths_land_exactly_one_trace_row_each(self) -> None:
        recorder = _TraceRecorder()
        mcp = self._server_with_both_registration_paths(recorder)
        expected_tools = {self._BUILTIN_PATH_TOOL, self._EXTENSION_PATH_TOOL}
        async with Client(mcp) as client:
            registered = {tool.name for tool in await client.list_tools()}
            assert expected_tools <= registered, (
                f"the probe registered {sorted(registered)}; both registration paths must produce "
                f"a live tool before the funnel can be tested (missing "
                f"{sorted(expected_tools - registered)})."
            )
            # Drive ONE dispatch down EACH registration path through the in-memory Client, so the
            # installed middleware runs on the real wire dispatch path for both.
            await client.call_tool(self._BUILTIN_PATH_TOOL, {"query": "funnel-builtin"})
            await client.call_tool(self._EXTENSION_PATH_TOOL, {"count": 7})
        traced = sorted(row["tool"] for row in recorder.calls)
        assert traced == sorted(expected_tools), (
            f"the trace middleware funnelled {traced}, expected exactly one row for EACH "
            f"registration path ({sorted(expected_tools)}). A middleware reached on the @mcp.tool "
            f"built-in path but NOT the add_tool-adapted extension path (mcp.tool(name=…)(wrapper)) "
            f"lands the built-in row only — extension calls silently go untraced (design §9-FG2). "
            f"Funnel coverage is a CHECKED variable over BOTH paths, never a hidden constant."
        )


class TestTheToolsOutcomeAlwaysWins:
    """B2: the tool's result and its error both survive the emission (design §5a-B2)."""

    async def test_a_raising_dispatch_surfaces_the_error_and_records_ok_false(self) -> None:
        recorder = _TraceRecorder()
        boom = ToolError("synthetic tool exploded on purpose")

        async def _raise(_ctx: Any) -> Any:
            raise boom

        with pytest.raises(ToolError) as raised:
            await _drive_on_call_tool(
                _make_trace_middleware(),
                name="lore_remember",
                arguments={},
                fastmcp_context=_app_context_double(recorder),
                call_next=_raise,
            )
        assert "exploded on purpose" in str(raised.value), (
            "the tool's own error must surface UNCHANGED — the emission may never swallow, "
            "rewrite, or replace it."
        )
        assert len(recorder.calls) == 1, (
            "a raising dispatch wrote no trace row. The write sits in `finally` precisely so the "
            "error leg records: an errored call still advances the DENOMINATOR packet 06 reads."
        )
        assert recorder.calls[0]["ok"] is False, (
            f"an ERRORED dispatch recorded ok={recorder.calls[0].get('ok')!r}. Ruled semantics "
            f"(B3): True iff the dispatch RETURNED a result — False on any raise, cancellation "
            f"included."
        )
        assert recorder.calls[0]["tool"] == "lore_remember"

    async def test_the_recorded_latency_is_present_and_bounded(self) -> None:
        # B8: latency measured AROUND call_next. Kills a build reporting 0, or SECONDS, or
        # measuring after the emission. The CONSTANT killer is the two-duration pin below.
        recorder = _TraceRecorder()

        async def _slow(_ctx: Any) -> Any:
            await asyncio.sleep(0.05)
            return _SENTINEL_RESULT

        await _drive_on_call_tool(
            _make_trace_middleware(),
            name="lore_search",
            arguments={"query": "x"},
            fastmcp_context=_app_context_double(recorder),
            call_next=_slow,
        )
        latency_ms = recorder.calls[0]["latency_ms"]
        assert isinstance(latency_ms, float | int) and not isinstance(latency_ms, bool)
        assert latency_ms >= 50.0 - 5.0, (
            f"recorded latency {latency_ms}ms is below the tool's own 50ms sleep — the "
            f"measurement does not span the tool call."
        )

    async def test_two_durations_record_different_latencies(self) -> None:
        # B8: a CONSTANT latency dies here at ANY fixture value — a difference cannot be a
        # constant. This is fixture-INDEPENDENT by construction.
        recorder = _TraceRecorder()

        async def _fast(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        async def _slow(_ctx: Any) -> Any:
            await asyncio.sleep(0.05)
            return _SENTINEL_RESULT

        mw = _make_trace_middleware()
        fc = _app_context_double(recorder)
        await _drive_on_call_tool(mw, name="a", arguments={}, fastmcp_context=fc, call_next=_fast)
        await _drive_on_call_tool(mw, name="b", arguments={}, fastmcp_context=fc, call_next=_slow)
        assert len(recorder.calls) == 2
        fast_ms, slow_ms = (float(row["latency_ms"]) for row in recorder.calls)
        assert slow_ms - fast_ms >= 0.05 * 1000 * 0.5, (
            f"slow={slow_ms}ms fast={fast_ms}ms — a constant (or a value measured outside the "
            f"tool call) cannot produce a difference; a real measurement cannot avoid one."
        )

    async def test_the_seam_never_mints_the_ordinal_itself(self) -> None:
        # T3 / M4: the ordinal is minted SERVER-SIDE inside the write. A client-side mint is a
        # third mint policy (#102's clone) and races under concurrency.
        recorder = _TraceRecorder()

        async def _ok(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        await _drive_on_call_tool(
            _make_trace_middleware(),
            name="lore_search", arguments={"query": "x"},
            fastmcp_context=_app_context_double(recorder), call_next=_ok,
        )
        assert "ordinal" not in recorder.calls[0], (
            f"the emission passed ordinal={recorder.calls[0].get('ordinal')!r} to the store — the "
            f"ordinal is minted inside the write transaction, never client-side."
        )


class TestATraceWriteFailureNeverTouchesTheCall:
    """B2: a trace-write failure is LOUD in the log and INVISIBLE to the caller (§5a-B2).

    The DESIGN-LAW §14 carve-out: a trace row is telemetry ABOUT a call — failing the call to
    save its telemetry would couple the entire served tool surface to an observability row.
    """

    async def test_a_failing_store_leaves_a_successful_result_intact(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        broken = _TraceRecorder(failure=SurrealStoreError("trace store is down"))

        async def _ok(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        with caplog.at_level(logging.ERROR, logger="loremaster.server"):
            result = await _drive_on_call_tool(
                _make_trace_middleware(),
                name="lore_search", arguments={"query": "survives"},
                fastmcp_context=_app_context_double(broken), call_next=_ok,
            )
        assert result is _SENTINEL_RESULT, (
            "a trace-write failure converted a successful tool call into something else."
        )
        assert broken.calls, "the emission never even attempted the write"
        loud = [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert loud, (
            "a trace-write failure was swallowed silently. It must be LOUD where it can be — the "
            "server log — or a flatlined traces section is #147 with nothing to diagnose from."
        )
        assert any(record.exc_info is not None for record in loud), (
            "the loud log must carry the exception (a `logger.exception`-shaped event)."
        )
        assert any(
            re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z0-9_]+)+", record.message) for record in loud
        ), (
            "the failure event must be a STRUCTURED dotted event name (house idiom: "
            "`logger.exception('trace.emit.failed', extra={...})`), never an interpolated sentence."
        )

    async def test_the_positive_control_a_healthy_store_writes(self) -> None:
        # Without this, "the call succeeded while the store was broken" is trivially true of a
        # build with NO telemetry at all (AC-13).
        healthy = _TraceRecorder()

        async def _ok(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        await _drive_on_call_tool(
            _make_trace_middleware(),
            name="lore_search", arguments={"query": "x"},
            fastmcp_context=_app_context_double(healthy), call_next=_ok,
        )
        assert len(healthy.calls) == 1, (
            "the healthy-store control wrote nothing, so the broken-store leg proves nothing."
        )

    async def test_a_failing_store_on_a_failing_tool_surfaces_the_tools_error(self) -> None:
        # Both halves fail: the TOOL's error reaches the caller, never the store's.
        broken = _TraceRecorder(failure=SurrealStoreError("trace store is down"))

        async def _raise(_ctx: Any) -> Any:
            raise ToolError("the tool's own error")

        with pytest.raises(ToolError) as raised:
            await _drive_on_call_tool(
                _make_trace_middleware(),
                name="lore_remember", arguments={},
                fastmcp_context=_app_context_double(broken), call_next=_raise,
            )
        assert "the tool's own error" in str(raised.value)
        assert "trace store is down" not in str(raised.value), (
            "the store's failure displaced the tool's own error in the caller's diagnosis."
        )


class TestTheEmissionDegradesWhenNoStoreIsReachable:
    """B5 / B6: mechanism CHANGES (no more ``request_ctx.get()``), the invariant holds.

    B5: a call with NO reachable write store is a silent no-op (DEBUG), never a crash — the
    tool is still served (telemetry is never a gate on the surface).
    B6: an un-wired store (the AppContext exists but carries no ``write_store``) is LOUD
    (WARNING) — that is the un-wired-emission signal, not an expected shape.
    """

    async def test_no_reachable_store_is_a_silent_no_op_not_a_crash(self) -> None:
        # fastmcp_context is None (the non-request / no-session shape). The design's B5 branch:
        # "no reachable write store -> no-op". The dispatch must still return the tool's result.
        async def _ok(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        result = await _drive_on_call_tool(
            _make_trace_middleware(),
            name="lore_search", arguments={"query": "contextless"},
            fastmcp_context=None, call_next=_ok,
        )
        assert result is _SENTINEL_RESULT, (
            "a dispatch with no reachable store must still SERVE the tool — an emission that "
            "reads the context outside its own guard takes the tool down with it (design B5)."
        )

    async def test_an_un_wired_store_warns_loudly(self, caplog: pytest.LogCaptureFixture) -> None:
        async def _ok(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        with caplog.at_level(logging.WARNING, logger="loremaster.server"):
            result = await _drive_on_call_tool(
                _make_trace_middleware(),
                name="lore_search", arguments={"query": "unwired"},
                fastmcp_context=_no_store_fastmcp_context(), call_next=_ok,
            )
        assert result is _SENTINEL_RESULT
        warned = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert warned, (
            "an un-wired store (AppContext present but no write_store) must WARN loudly (B6) — "
            "unlike the no-store B5 branch (DEBUG), this means the emission is un-wired and every "
            "trace would otherwise vanish with every gate green (design §5a-B6, #131's shape)."
        )


class TestTheCancelledDispatchIsRecordedOkFalse:
    """B3 (the ok-latch) + the asyncio-cancel KNOWN BOUND (design §5a-B3 / §9-FG3).

    ⚠ KNOWN BOUND, carried from the retired seam: this pin uses ``asyncio.Task.cancel`` which is
    EDGE-triggered (delivered once, at the interrupted await), so a later await in ``finally``
    runs normally and a non-suspending recorder completes shielded-or-not. It genuinely proves
    the write is in ``finally`` and the latch leaves ok=False — but it CANNOT see the shield's
    job. The DISCRIMINATING shield pin is
    :class:`TestTheEmissionSurvivesAnyioLevelTriggeredCancellation`.
    RE-OPEN TRIGGER: if the recorder gains a suspension point or the emission's placement
    changes, re-derive this bound.
    """

    async def test_a_cancelled_dispatch_records_ok_false(self) -> None:
        recorder = _TraceRecorder()
        mw = _make_trace_middleware()
        fc = _app_context_double(recorder)

        async def _block(_ctx: Any) -> Any:
            await asyncio.sleep(30.0)
            return _SENTINEL_RESULT

        task = asyncio.create_task(
            _drive_on_call_tool(mw, name="lore_search", arguments={}, fastmcp_context=fc, call_next=_block)
        )
        await asyncio.sleep(0.05)
        assert not task.done(), "the blocking dispatch finished before it could be cancelled"
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert len(recorder.calls) == 1, (
            "a CANCELLED dispatch wrote no trace row — the write belongs in `finally` so the "
            "timed-out population (exactly what ok=False measures) is not lost."
        )
        assert recorder.calls[0]["ok"] is False, (
            f"the cancelled dispatch recorded ok={recorder.calls[0].get('ok')!r}. The success "
            f"latch starts False and is set True only after call_next RETURNS, with NO except "
            f"arm — so CancelledError (a BaseException an `except Exception` misses) leaves it "
            f"False. True here means a timed-out drain counts as one the agent performed."
        )


class TestTheEmissionSurvivesAnyioLevelTriggeredCancellation:
    """B4: the ``finally`` write is SHIELDED + BOUNDED — the discriminating cancellation pin.

    MCP cancels a request through an anyio cancel scope (LEVEL-triggered): once cancelled every
    subsequent await inside the scope raises, ``finally`` included. An unshielded emission that
    SUSPENDS writes NO row for exactly the population ok=False exists to measure.

    MUTATION-PROOF OBLIGATION (the build/adversary must demonstrate): remove
    ``anyio.CancelScope(shield=True)`` from the emission -> this leg goes RED (no row) while the
    asyncio-cancel sibling stays GREEN. That asymmetry IS the finding (design §6.3).
    """

    async def test_a_scope_cancelled_dispatch_still_writes_its_row(self) -> None:
        recorder = _SuspendingTraceRecorder()
        mw = _make_trace_middleware()
        fc = _app_context_double(recorder)

        async def _block(_ctx: Any) -> Any:
            await asyncio.sleep(30.0)
            return _SENTINEL_RESULT

        with anyio.move_on_after(0.05):
            await _drive_on_call_tool(
                mw, name="lore_search", arguments={}, fastmcp_context=fc, call_next=_block
            )
        assert len(recorder.calls) == 1, (
            "a dispatch cancelled through an ANYIO cancel scope wrote no trace row. anyio scopes "
            "are level-triggered, so the `finally`'s own await raises too — the emission must be "
            "SHIELDED (design B4), or the timed-out population is silently absent."
        )
        assert recorder.calls[0]["ok"] is False

    async def test_positive_control_the_same_scope_uncancelled_records_ok_true(self) -> None:
        # Without this, a build that always wrote ok=False — or a probe that never cancelled —
        # would satisfy the leg above.
        recorder = _SuspendingTraceRecorder()

        async def _ok(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        with anyio.move_on_after(30.0):
            result = await _drive_on_call_tool(
                _make_trace_middleware(), name="lore_search", arguments={},
                fastmcp_context=_app_context_double(recorder), call_next=_ok,
            )
        assert result is _SENTINEL_RESULT
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["ok"] is True

    def test_the_shielded_write_is_bounded(self) -> None:
        # B4: the shield must not hold a dying request open forever. The bound is DERIVED and
        # must sit above the store's own conflict-retry deadline (a healthy contended write must
        # not be cut short). This constant is UNCHANGED by the migration (M4) — pinned so a
        # re-home that drops the bound is caught.
        from loremaster.server import _TRACE_EMIT_TIMEOUT_SECONDS
        from loremaster.store._txn import _TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS

        assert _TRACE_EMIT_TIMEOUT_SECONDS > _TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS, (
            "the emission's timeout is at or below the retry driver's deadline — a contended "
            "healthy trace write is cut short and lost."
        )
        assert _TRACE_EMIT_TIMEOUT_SECONDS <= 30, (
            "an unbounded-in-practice shield holds a cancelled request open by its own telemetry."
        )


class TestIdentityIsDeclaredNeverGuessed:
    """B7: declared identity is harvested from ``context.message.arguments``, str-only, no guess.

    Mechanism CHANGES (arguments now come off ``context.message``, not a positional param), the
    rule is UNCHANGED (design §5a-B7). Values below deliberately differ from any other pin's, so
    a build keyed on one value set cannot satisfy them all (fixture monoculture killer).
    """

    _AGENT = "auditor-q"
    _SESSION = "wave9"
    _ACTION = "drain"

    async def test_all_declared_string_keys_are_recorded(self) -> None:
        recorder = _TraceRecorder()

        async def _ok(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        await _drive_on_call_tool(
            _make_trace_middleware(),
            name="lore_comms",
            arguments={"agent": self._AGENT, "session": self._SESSION, "action": self._ACTION},
            fastmcp_context=_app_context_double(recorder), call_next=_ok,
        )
        row = recorder.calls[0]
        assert row["agent"] == self._AGENT
        assert row["session"] == self._SESSION
        assert row["action"] == self._ACTION

    async def test_a_partial_declaration_is_recorded_partially(self) -> None:
        # The all-or-nothing killer: `agent` declared, `session`/`action` absent. A build that
        # harvests the three keys all-or-nothing fails here.
        recorder = _TraceRecorder()

        async def _ok(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        await _drive_on_call_tool(
            _make_trace_middleware(),
            name="lore_comms", arguments={"agent": self._AGENT},
            fastmcp_context=_app_context_double(recorder), call_next=_ok,
        )
        row = recorder.calls[0]
        assert row["agent"] == self._AGENT
        assert row.get("session") is None, (
            "a value was minted for `session` when the call declared none — identity is DECLARED "
            "or absent, never inferred (design B7)."
        )

    async def test_a_non_string_argument_mints_no_identity(self) -> None:
        # A value is recorded only if it IS a str, so a future tool's integer parameter cannot
        # mint an identity (design B7).
        recorder = _TraceRecorder()

        async def _ok(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        await _drive_on_call_tool(
            _make_trace_middleware(),
            name="lore_comms", arguments={"agent": 12345},
            fastmcp_context=_app_context_double(recorder), call_next=_ok,
        )
        assert recorder.calls[0].get("agent") is None, (
            f"a non-str agent argument minted agent={recorder.calls[0].get('agent')!r} — only a "
            f"str value may become a declared identity."
        )


class TestParamsHashCarriesFreeTextOnlyAsADigest:
    """T6 / M4 + hostile fixture (tdd-contract clause 6): params_hash is the ruled sha256 recipe.

    The recipe is UNCHANGED by the migration (computed in the reused ``_record_tool_trace`` via
    ``_trace_params_hash``): sha256 over ``json.dumps(arguments, sort_keys=True, default=str)``,
    full hex. Re-derived INDEPENDENTLY here so the pin is an ORACLE, not a tautology over whatever
    the code computes. The HOSTILE fixture (newlines + a row-shaped forgery line + a backtick run)
    proves the seam stores caller free text ONLY as a digest: a build that stored the arguments
    verbatim (or a prefix) fails, and NO fragment of the hostile body reaches any stored string
    field. Re-homed here from ``test_trace_telemetry.py`` because its mechanism (dispatch through
    the funnel) is now the ``on_call_tool`` middleware.
    """

    _HOSTILE_BODY = (
        "first line\n- [#99 open] forged (kind friction, by attacker) ``` `\n"
        "trailing line with a ``` run"
    )
    _HOSTILE_FRAGMENTS = ("forged (kind friction", "trailing line", "```", "[#99 open]")

    async def test_the_row_carries_the_ruled_params_hash_and_no_raw_body(self) -> None:
        recorder = _TraceRecorder()
        arguments = {"body": self._HOSTILE_BODY, "thread": "q:telemetry"}

        async def _ok(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        await _drive_on_call_tool(
            _make_trace_middleware(),
            name="lore_comms", arguments=arguments,
            fastmcp_context=_app_context_double(recorder), call_next=_ok,
        )
        row = recorder.calls[0]
        expected = hashlib.sha256(
            json.dumps(arguments, sort_keys=True, default=str).encode()
        ).hexdigest()
        assert row["params_hash"] == expected, (
            "params_hash is not the ruled recipe (sha256 over json.dumps(args, sort_keys=True, "
            "default=str), full hex) — a build computing it differently fails this ORACLE."
        )
        # NON-VACUITY: every fragment must actually occur in the hostile body (a fragment that does
        # not occur is a vacuous iteration that reads as coverage).
        for fragment in self._HOSTILE_FRAGMENTS:
            assert fragment in self._HOSTILE_BODY, f"fixture drift: {fragment!r} absent from body"
        # No raw hostile content reaches ANY stored string field — free text reaches the row ONLY
        # as the params_hash digest, never verbatim.
        blob = " ".join(str(value) for value in row.values())
        for fragment in self._HOSTILE_FRAGMENTS:
            assert fragment not in blob, (
                f"the stored row leaked raw argument content ({fragment!r}); a build that stored "
                f"the arguments verbatim or as a prefix is the row-forgery hazard this kills."
            )


class TestTheMigratedSeamLandsARealRow:
    """B1 (real store): the W30/W33 class — the seam's kwargs must be ones the ENGINE accepts.

    Every other funnel pin points the emission at a DOUBLE that accepts ``**fields``. This one
    drives ``on_call_tool`` with a REAL :class:`SurrealStore` behind the fastmcp_context, so an
    emission passing a keyword the real ``record_trace`` rejects RAISES (and the failure-posture
    swallow logs it) instead of silently "working" — the exact hole where "traces.total stays 0
    forever" hid (design §5a-B1, #147).
    """

    async def test_a_successful_dispatch_lands_one_real_row(self, trace_store: SurrealStore) -> None:
        async def _ok(_ctx: Any) -> Any:
            return _SENTINEL_RESULT

        await _drive_on_call_tool(
            _make_trace_middleware(),
            name="lore_search", arguments={"query": "end-to-end"},
            fastmcp_context=_app_context_double(trace_store), call_next=_ok,
        )
        rows = await _read_trace_rows(trace_store)
        assert len(rows) == 1, (
            f"the dispatch wrote {len(rows)} rows to the REAL trace table, expected 1. Zero means "
            f"the store REJECTED the emission's call and the failure-posture swallow hid it — the "
            f"whole tool surface keeps working while telemetry is dead (#147). Check the server "
            f"log for `record_trace() got an unexpected keyword argument …`."
        )
        row = rows[0]
        assert row["tool"] == "lore_search"
        assert row["ok"] is True
        assert isinstance(row["ordinal"], int) and not isinstance(row["ordinal"], bool), (
            f"the real row carries ordinal={row['ordinal']!r} — the store-side mint did not run."
        )

    async def test_a_raising_dispatch_also_lands_one_real_row(self, trace_store: SurrealStore) -> None:
        async def _raise(_ctx: Any) -> Any:
            raise ToolError("boom")

        with pytest.raises(ToolError):
            await _drive_on_call_tool(
                _make_trace_middleware(),
                name="lore_remember", arguments={},
                fastmcp_context=_app_context_double(trace_store), call_next=_raise,
            )
        rows = await _read_trace_rows(trace_store)
        assert len(rows) == 1, (
            "the ERROR leg wrote no row to the REAL store — the failure path's kwargs must be "
            "acceptable to the store too; a mismatch there is swallowed exactly like the success "
            "path's, and errored calls are part of packet 06's denominator."
        )
        assert rows[0]["ok"] is False


async def _read_trace_rows(store: SurrealStore) -> list[dict[str, Any]]:
    """Read every trace row back with an explicit projection (an unset option<> reads None)."""
    projection = (
        "tool", "params_hash", "hit_count", "latency_ms", "session", "agent", "action",
        "transport_session", "ordinal", "ok", "ts",
    )
    statement = f"SELECT {', '.join(projection)} FROM trace"
    result = await store._query(statement)  # noqa: SLF001 - the store's own query seam (test-only read)
    return list(result or [])


# =========================================================================== #
# SECTION C — the lifespan-apparatus DELETE + once-per-process property + FP-07
# bounded-retry re-home (design §5b-C2 / M11 / Item 1 / §9-FG1; adversary-59 ①)
# =========================================================================== #
#
# THE C2 DUAL, COMPLETED (contract-59b ①, adversary-59: the DELETE of
# ``_ProcessLifespanGuard`` + ``_EagerStartupLifespan`` removes SEVEN observable behaviours —
# adversary P6b Stage-1 #15–21 — and the predecessor contract pinned only #15. Each is
# adjudicated here; the full table is in REPORT-contract-59b.md §"C2 DUAL"):
#
#   #15 once-per-process         PRESERVE the PROPERTY (fastmcp-native ref-counted lifespan;
#                                Item 1 GO). Pin: the once-per-process wire gate below.
#   #16 concurrent-reuse         DROP the bespoke asyncio-lock lease; PRESERVE as the CONCURRENT
#                                observation of #15 (ref-counting shares one build across
#                                concurrent sessions — spike Item 1 GO, 4 concurrent). Pin: the
#                                once-per-process wire gate's CONCURRENT leg (enumerated below).
#   #17 sequential-rebuild       DROP the mcp-SDK-specific "tear down at ref-zero mid-process,
#                                rebuild on the next session" mechanism — its referent (the SDK's
#                                per-SESSION lifespan re-entry) is GONE; fastmcp holds the build
#                                for the PROCESS lifetime. The SURVIVING virtue ("the build is not
#                                torn down between client sessions") is native + pinned by the
#                                once-per-process wire gate's SEQUENTIAL leg (enter stays 1).
#   #18 build-failure-not-cached DROP the per-lease "not cached → next lease retries" mechanism
#                                (no per-session "next lease" exists under a process-lifetime
#                                lifespan). The transient-resilience VIRTUE is PRESERVED via FP-07
#                                (#21) re-homed INSIDE the lifespan; the fail-closed leg is pinned
#                                by ``TestTheEagerHeavyBuildRetriesTransientFailures`` below.
#   #19 eager hoist              DROP the bespoke ASGI-lifespan interceptor; PRESERVE the property
#                                (heavy build runs at PROCESS startup, not first-client-connect)
#                                — native to fastmcp's ``http_app()`` ASGI lifespan; pinned by the
#                                once-per-process wire gate (entered at startup, before any call).
#   #20 http-scope passthrough   DROP — with the interceptor deleted there is no scope-delegation
#                                to preserve; the Origin/Bearer wrappers wrap ``http_app()``
#                                directly (design C3/C4). Covered by the §6.2 auth-composition wire
#                                gate (bad token→401, bad Origin→403 prove the http scope routes).
#   #21 FP-07 bounded-retry      PRESERVE+PIN (design §5b-C2 rider: "FP-07 re-homes INSIDE" the
#                                native lifespan). Pinned by the retry-helper class below
#                                (TestTheEagerHeavyBuildRetriesTransientFailures) + the §6.2 wire
#                                gate's boot-retry leg (wiring).
#
# The retry policy is the ONE the workspace shares (``loresigil.backoff``); the retry LOOP is a
# nameable async helper the lifespan calls (contract's chosen interface — the retry is a POLICY,
# so it is a FUNCTION per DRY/#102, and it already IS a separate method today,
# ``_EagerStartupLifespan._acquire_eager_lease_with_retry``). ONE constant names it.

#: The nameable async FP-07 bounded-retry helper the migrated lifespan calls. Today the retry
#: loop is ``_EagerStartupLifespan._acquire_eager_lease_with_retry``; the DELETE re-homes it as a
#: standalone async helper on ``loremaster.server``. Required signature (the contract's interface):
#: ``async def <helper>(build, *, max_attempts, backoff_base_s) -> T`` — call ``build`` (an async,
#: no-arg callable that runs the heavy build), return its result on the first success, retry up to
#: ``max_attempts`` total attempts sleeping ``loresigil.backoff.additive_jitter(backoff_base_s)``
#: between attempts (only while another attempt remains), and re-raise the last exception after the
#: budget is exhausted (fail-closed). If the build prefers another name, change ONLY this constant.
_EAGER_RETRY_HELPER_NAME = "_eager_build_with_retry"

#: The name of the PRODUCTION default retry-budget constant (> 1 = bounded, never single-shot).
#: Today ``_DEFAULT_EAGER_MAX_ATTEMPTS = 5``; the re-home keeps a module constant. One name here.
_EAGER_MAX_ATTEMPTS_CONST_NAME = "_DEFAULT_EAGER_MAX_ATTEMPTS"


def _eager_retry_helper() -> Any:
    """Fetch the FP-07 bounded-retry helper at CALL time (fails for its own reason, not collection).

    THE WRONG BUILD this fetch catches (adversary-59 ①): a "single-shot lifespan re-home" that
    runs the heavy build ONCE in fastmcp's ``lifespan=`` with NO bounded retry — a transient boot
    SurrealDB/TEI blip then aborts the container on first failure (FP-07 is the resilience the
    ~150-LOC apparatus DELETE must NOT drop, design §5b-C2). Such a build has no bounded-retry
    helper, so this fetch RAISES — reddening every leg below.
    """
    server = importlib.import_module("loremaster.server")
    helper = getattr(server, _EAGER_RETRY_HELPER_NAME, None)
    assert helper is not None, (
        f"loremaster.server.{_EAGER_RETRY_HELPER_NAME} does not exist. Design §5b-C2 DELETEs the "
        f"~150-LOC lifespan apparatus and re-homes FP-07 bounded-retry-with-backoff INSIDE the "
        f"native fastmcp `lifespan=` — as a nameable async helper the lifespan calls (the retry is "
        f"a POLICY, so a FUNCTION per DRY/#102; it is already a separate method today, "
        f"`_EagerStartupLifespan._acquire_eager_lease_with_retry`). A single-shot re-home that "
        f"drops the retry passes every OTHER migration pin (adversary-59 ①). Required signature: "
        f"`async def {_EAGER_RETRY_HELPER_NAME}(build, *, max_attempts, backoff_base_s) -> T`. If "
        f"you named it differently, change only `_EAGER_RETRY_HELPER_NAME` in this file."
    )
    assert inspect.iscoroutinefunction(helper), (
        f"loremaster.server.{_EAGER_RETRY_HELPER_NAME} must be an async function (it awaits the "
        f"heavy build and sleeps between attempts)."
    )
    return helper


def _eager_default_max_attempts() -> int:
    """The production default retry budget (> 1 = bounded, not single-shot), fetched at call time."""
    server = importlib.import_module("loremaster.server")
    value = getattr(server, _EAGER_MAX_ATTEMPTS_CONST_NAME, None)
    assert isinstance(value, int) and not isinstance(value, bool), (
        f"loremaster.server.{_EAGER_MAX_ATTEMPTS_CONST_NAME} must survive the migration as an int "
        f"(the FP-07 bounded default). Design §5b-C2 re-homes FP-07 inside the lifespan; its budget "
        f"is still a named production constant. If renamed, change only "
        f"`_EAGER_MAX_ATTEMPTS_CONST_NAME` in this file."
    )
    return value


class TestTheHeavyBuildRunsOncePerProcessEagerly:
    """M11 / C2 / Item-1: the ~150-LOC lifespan apparatus is DELETED, the PROPERTY preserved.

    The DUAL adjudication (design §5b-C2): DELETE ``_ProcessLifespanGuard`` +
    ``_EagerStartupLifespan`` + ``_lore_eager_guard`` (their referent — the mcp SDK's
    per-SESSION lifespan re-entry — is gone under fastmcp's once-per-PROCESS ref-counted
    ``lifespan=``). PRESERVE the PROPERTY: "the heavy build runs ONCE per process, eagerly at
    startup." The spike MEASURED once-per-process (Item 1 GO: enter==1 across 4 seq + 4
    concurrent wire sessions). This pins the PROPERTY, which is what the DELETE relies on.

    ⚠ This is the highest-wire-risk item (design §12). The strongest proof is the §6.1 in-image
    conformance + §6.2 REAL-uvicorn smoke gates below (only the running artifact proves the
    lifespan actually entered). This pin is the in-process property check; it does not replace
    those gates.
    """

    @pytest.mark.wire
    async def test_the_lifespan_yields_the_app_context_exactly_once_per_process(self) -> None:
        # The once-per-process property is a fastmcp NATIVE behaviour the spike already MEASURED
        # (Item 1 GO: enter==1 across 4 sequential + 4 concurrent wire sessions, on a REAL
        # uvicorn/TCP server) — the in-memory transport skips the ASGI lifespan (FG1) and cannot
        # see it, so this cannot be an in-process unit pin. It is carried as a `wire`-lane gate:
        # the build's §6.2 real-uvicorn smoke MUST assert the heavy build (a lifespan that
        # increments a module counter) runs exactly once across multiple sessions on one process.
        #
        # ⚠ CONTRACT-59b ① — this ONE wire gate carries FOUR C2 DUAL legs (adversary-59 P6b
        # #16/#17/#19/#21 wiring), because they are all observations of the SAME native lifespan on
        # a real server. The build's §6.2 real-uvicorn smoke MUST assert ALL of:
        #   • EAGER-AT-STARTUP (#19): the module counter reads 1 BEFORE the first client call
        #     (the build runs at ASGI process startup, not first-client-connect);
        #   • CONCURRENT-REUSE (#16): 4 concurrent wire sessions still read enter==1 (one build
        #     shared, no second probe/watcher — the ref-count shares it);
        #   • SEQUENTIAL-SURVIVAL (#17): across 4 sequential sessions the counter STAYS 1 (the
        #     build is NOT torn down and rebuilt between client sessions — process-lifetime);
        #   • FP-07 BOOT-RETRY WIRING (#21): a heavy build that FAILS once then succeeds still
        #     brings the container up (the lifespan routes the build through the bounded-retry
        #     helper — the in-memory unit legs in TestTheEagerHeavyBuildRetriesTransientFailures
        #     pin the helper's BEHAVIOUR; only the running artifact proves the lifespan CALLS it).
        pytest.skip(
            "REQUIRES the real-uvicorn once-per-process leg (design §6.6-1 / spike Item 1). The "
            "heavy build runs in fastmcp's ref-counted `lifespan=`; a counter must read 1 (a) "
            "before the first call (eager, #19), (b) across 4 concurrent sessions (reuse, #16), "
            "and (c) across 4 sequential sessions (survival, #17); AND a fail-then-succeed heavy "
            "build must still bring the container up (FP-07 wiring, #21). In-memory transport skips "
            "the ASGI lifespan (FG1), so this belongs in the wire gate, reusing "
            "scripts/fastmcp_migration_spike.py."
        )

    def test_the_deleted_apparatus_is_gone(self) -> None:
        # PIN-THE-DELETE (design M11): the ~150-LOC apparatus is removed. These go RED the day
        # someone re-adds a hand-rolled per-session guard — carrying the message that fastmcp's
        # once-per-process lifespan makes it dead weight (Item 1 GO). If §6.6-1 had come back
        # NO-GO the design KEEPS the guard; then this pin is deleted deliberately with a note.
        server = importlib.import_module("loremaster.server")
        for retired in ("_ProcessLifespanGuard", "_EagerStartupLifespan"):
            assert not hasattr(server, retired), (
                f"loremaster.server.{retired} still exists. Design M11/C2 DELETEs the "
                f"per-session lifespan apparatus — fastmcp enters the user `lifespan=` once per "
                f"PROCESS (Item 1 GO, ref-counted `_lifespan_manager`), so the guard is dead "
                f"weight on the serving hot path. (If the spike had gone NO-GO, delete this pin "
                f"deliberately and say so.)"
            )


class _FlakyBuild:
    """An async no-arg heavy-build stand-in: raises ``fail_times`` transient errors, then succeeds.

    Models the eager heavy build (probe gate → SurrealDB write stack → watcher) as the FP-07 retry
    helper sees it: a no-arg async callable that either raises a transient dependency error or
    returns the built context. Counts its calls so a pin can assert the EXACT attempt count (a
    single-shot re-home attempts once; a correct bounded retry attempts failures + 1).
    """

    def __init__(self, *, fail_times: int, result: Any) -> None:
        self._fail_times = fail_times
        self._result = result
        self.calls = 0

    async def __call__(self) -> Any:
        self.calls += 1
        if self.calls <= self._fail_times:
            raise SurrealStoreError(f"transient boot blip #{self.calls}")
        return self._result


class TestTheEagerHeavyBuildRetriesTransientFailures:
    """FP-07 (#21 / design §5b-C2 rider / adversary-59 ①): the eager heavy build is RETRIED.

    THE WRONG BUILD (measured, adversary-59 ①): a "single-shot lifespan re-home" runs the heavy
    build ONCE in fastmcp's native ``lifespan=`` with NO bounded retry. fastmcp's ``lifespan=``
    does NOT retry a failed build, so a transient boot SurrealDB/TEI blip aborts the container on
    the first failure — the exact resilience the ~150-LOC apparatus DELETE must NOT drop (design
    §5b-C2: "FP-07 re-homes INSIDE" the native lifespan). That build passes every OTHER migration
    pin, because the only apparatus pin the predecessor carried is a `pytest.skip`. These are the
    runnable behavioural CHECKED variable for FP-07's retry SEMANTICS, driving the bounded-retry
    helper directly with a fail-then-succeed / always-fail heavy build.

    ⚠ HONEST BOUND (the wiring leg): these pin the helper's BEHAVIOUR. That the migrated LIFESPAN
    actually ROUTES the heavy build through this helper (not an orphaned helper beside a single-shot
    lifespan — the D7 "defined-but-not-installed" shape) is the §6.2 wire gate's FP-07 boot-retry
    leg (a fail-then-succeed heavy build over real uvicorn → container comes up): an in-memory
    lifespan drive would need the heavy-build stub seam coupling #3 introduces (build-provided;
    this contract does not assume its shape). So: helper behaviour = runnable here; lifespan wiring
    = the wire gate. Both are required (adversary-59 ①).
    """

    async def test_a_transient_failure_is_retried_then_the_build_comes_up(self) -> None:
        helper = _eager_retry_helper()
        sentinel = object()
        build = _FlakyBuild(fail_times=2, result=sentinel)
        result = await helper(build, max_attempts=5, backoff_base_s=0.0)
        assert result is sentinel, (
            "the bounded retry did not return the heavy build's result after a transient failure — "
            "a single-shot re-home aborts on the first blip instead of retrying (FP-07, #21)."
        )
        assert build.calls == 3, (
            f"the heavy build ran {build.calls} time(s); a 2-failure-then-success build must be "
            f"attempted EXACTLY 3 times (2 transient failures + 1 success)."
        )

    async def test_every_attempt_failing_fails_closed_after_the_budget(self) -> None:
        helper = _eager_retry_helper()
        build = _FlakyBuild(fail_times=99, result=object())  # never succeeds within the budget
        with pytest.raises(SurrealStoreError):
            await helper(build, max_attempts=3, backoff_base_s=0.0)
        assert build.calls == 3, (
            f"the heavy build ran {build.calls} time(s); a budget of 3 must attempt EXACTLY 3 then "
            f"re-raise (fail-CLOSED) — never loop unbounded (uvicorn must be able to abort a "
            f"genuinely-down dependency), never stop before the budget is spent."
        )

    async def test_the_default_retry_budget_is_bounded_and_greater_than_one(self) -> None:
        budget = _eager_default_max_attempts()
        assert budget > 1, (
            f"the production eager-build retry budget is {budget}; it must be > 1 so the default is "
            f"BOUNDED retry, not single-shot — a single-shot default IS the FP-07 drop this section "
            f"exists to catch (adversary-59 ①)."
        )
        assert budget <= 20, (
            f"the retry budget is {budget}; a huge budget approximates an unbounded loop that stops "
            f"uvicorn ever aborting a down dependency (FP-07 must fail closed after the budget)."
        )

    async def test_the_inter_attempt_sleep_routes_through_the_shared_backoff_policy(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ROUTING-IS-SHARING (DRY / #207 / #102): the retry must sleep via the ONE workspace
        # backoff policy (loresigil.backoff.additive_jitter, late-bound via the MODULE attribute),
        # never a hand-rolled sleep. Monkeypatch the SHARED policy and prove the retry actually
        # calls it — a private copy (or a `from ... import additive_jitter` bound at import time)
        # would NOT fire, which is precisely the failure mode #102 exists to end.
        from loresigil import backoff

        seen: list[float] = []

        def _spy(base_s: float, **_kw: Any) -> float:
            seen.append(base_s)
            return 0.0  # no real sleep in the test

        monkeypatch.setattr(backoff, "additive_jitter", _spy)
        helper = _eager_retry_helper()
        build = _FlakyBuild(fail_times=1, result=object())
        await helper(build, max_attempts=3, backoff_base_s=2.0)
        assert seen == [2.0], (
            f"the retry's inter-attempt sleep called loresigil.backoff.additive_jitter {seen}, "
            f"expected exactly one call with the base (2.0) after the single failure. A retry that "
            f"hand-rolls its own sleep, or imports the jitter function by value (defeating the "
            f"late binding the backoff module is deliberately built for), does NOT route through "
            f"the shared policy — and patching the shared attribute then would not fire, exactly "
            f"as this asserts (#207/#102)."
        )


# =========================================================================== #
# SECTION D — serverInfo.version (design D4 / §9-FG4), via a wire read.
# The version pin requires reading serverInfo over the wire; see §6.2 gate below.
# =========================================================================== #
class TestTheServedVersionIsLoresResolvedVersion:
    """D4 / FG4: ``serverInfo.version`` is lore's ``_resolve_version()``, not the SDK's default.

    Under the mcp SDK the build reached ``mcp._mcp_server.version`` (a private attr). Under
    fastmcp it is the ctor kwarg ``FastMCP(version=_resolve_version())`` — CONFIRMED
    (empirical probe: serverInfo.version == the ctor value). A build that drops the kwarg
    silently reverts to fastmcp's own version, invisible unless a test reads serverInfo over the
    WIRE (no in-memory test reads it). Pinned by the §6.2 wire smoke below (this class documents
    the requirement; the assertion lives in the wire gate).
    """

    def test_resolve_version_is_construction_time(self) -> None:
        # A cheap structural half: _resolve_version() honours an env baked after import (the
        # container bakes LORE_VERSION), so it must be resolved at CONSTRUCTION, not import.
        from loremaster.server import _resolve_version

        assert callable(_resolve_version), "the version resolver must survive the migration (D4)."


# =========================================================================== #
# SECTION E — the P9 name-collision guard on the NEW registry (design §3-P9)
# =========================================================================== #
class TestExtensionToolNameCollisionsAreRefused:
    """P9: an extension tool may never silently shadow a built-in or a sibling extension tool.

    ``mcp._tool_manager`` is GONE in fastmcp (renamed ``_local_provider``; §0). The current
    guard's ``mcp._tool_manager.get_tool(...)`` is a HARD BREAK (loud=good). The migration keeps
    the guard against a PUBLIC/sync path AND keeps the ``_ALL_BUILTIN_TOOL_NAMES`` universe
    check — because that check reserves a DISABLED built-in's name too (packet 45, L2-4), which
    ``on_duplicate='error'`` ALONE cannot do (it only sees REGISTERED tools). Two legs:
    """

    def test_collision_with_a_registered_builtin_is_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # An extension tool named `lore_search` collides with an ENABLED built-in -> ValueError
        # at build time, never a silent shadow on the served surface. Explicit registration
        # (the test_extension.py / test_tool_allowlist.py idiom), so the collision is exercised
        # without needing a discovery config block.
        from _extension_helpers import CollidingExtension

        monkeypatch.setenv("SURREAL_USER", "root")
        monkeypatch.setenv("SURREAL_PASS", "root")
        server = LoreServer(_config("collision_builtin")).register_extension(CollidingExtension())
        with pytest.raises(ValueError, match=r"collide|shadow|reserved"):
            build_mcp_server(server)

    def test_collision_with_a_DISABLED_builtin_name_is_still_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # THE DISCRIMINATING LEG (design §3-P9 / packet 45 L2-4): `lore_search` is DISABLED by
        # the allowlist, so it is NOT registered on mcp — yet its name stays RESERVED. A build
        # that switched to `on_duplicate='error'` ALONE (no universe check) passes the leg above
        # and FAILS here, because on_duplicate only sees REGISTERED tools. This is the wrong
        # build the design's public-`get_tool`-plus-universe-check recommendation kills.
        from _extension_helpers import CollidingExtension

        monkeypatch.setenv("SURREAL_USER", "root")
        monkeypatch.setenv("SURREAL_PASS", "root")
        enabled_without_search = [
            "lore_get_symbol", "lore_verify", "lore_remember", "lore_recall", "lore_claim_task",
            "lore_tasks", "lore_comms", "lore_impact", "lore_map", "lore_read", "lore_dead_code",
            "lore_diff", "lore_index", "lore_findings",
        ]
        server = LoreServer(
            _config("collision_disabled", tools=enabled_without_search)
        ).register_extension(CollidingExtension())
        with pytest.raises(ValueError, match=r"collide|shadow|reserved|universe"):
            build_mcp_server(server)


class TestExtensionToolsRegisterAndAreCallable:
    """D6 (coupling #2): the ``add_tool`` single-arg change must not drop extension tools.

    ``add_tool(self, tool)`` is single-arg in fastmcp — the current
    ``mcp.add_tool(wrapper, name=…, description=…, annotations=…)`` breaks. The build adapts
    (``mcp.tool(name=…, description=…, annotations=…)(wrapper)`` is probed-working). The OUTCOME
    this pins: a real extension registers under its ToolSpec name, is visible on the surface,
    and carries the honest ``readOnlyHint=False`` posture (R14).
    """

    async def test_a_real_extension_tool_registers_under_its_spec_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from _extension_helpers import CounterExtension

        monkeypatch.setenv("SURREAL_USER", "root")
        monkeypatch.setenv("SURREAL_PASS", "root")
        server = LoreServer(_config("ext_register")).register_extension(CounterExtension())
        mcp = build_mcp_server(server)
        registered = await _registered_tool_names(mcp)
        assert "bump_counter" in registered, (
            "the extension tool `bump_counter` did not register — the `add_tool(wrapper, name=…)` "
            "call site must be adapted to fastmcp's single-arg `add_tool`/`mcp.tool(...)` (design "
            "coupling: add_tool signature change)."
        )

    async def test_the_extension_tool_carries_read_only_hint_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # R14: an extension tool may MUTATE, so it publishes an explicit readOnlyHint=False,
        # never None (which would leave the consumer guessing). The adaptation must preserve it.
        from _extension_helpers import CounterExtension

        monkeypatch.setenv("SURREAL_USER", "root")
        monkeypatch.setenv("SURREAL_PASS", "root")
        server = LoreServer(_config("ext_hint")).register_extension(CounterExtension())
        mcp = build_mcp_server(server)
        tool = await mcp.get_tool("bump_counter")
        annotations = getattr(tool, "annotations", None)
        assert annotations is not None and getattr(annotations, "readOnlyHint", None) is False, (
            "the extension tool must publish readOnlyHint=False (R14) — the add_tool adaptation "
            "dropped the ToolAnnotations."
        )


# =========================================================================== #
# SECTION F — the WIRE + HOST-ORIGIN + AUTH gates (design §6.1 / §6.2 / §5b-C3/C3'/C4/C5).
#
# These REQUIRE a running server. Per design §6.2 (and the FG1 in-memory-transport blind spot)
# the STRONGEST form is a REAL uvicorn TCP server + a real MCP client — realised as the §6.1
# in-image conformance run (the packet-01a instrument, finding #139) and a real-uvicorn smoke
# reusing `scripts/fastmcp_migration_spike.py`. This file specifies the wire fixture the build
# provides; the pins below are the discriminating assertions those gates MUST carry.
#
# The `migration_wire` fixture contract (build/adversary implements it): yield an object with
#   .base_url            -> str (a real TCP http URL the server is bound to)
#   .client()            -> an async ctx mgr yielding a connected fastmcp/mcp client
#   .raw_request(headers, host=…, origin=…) -> an httpx response for header-spoof probes
#   .server_info()       -> the initialize result's serverInfo
# with `host_origin_protection` ENABLED and `allowed_hosts` set for the bind (the config rider).
# =========================================================================== #
@pytest.mark.wire
class TestTheWireSmokeServesTheFullSurface:
    """§6.2 / FG1 / FG2 / FG4: the running artifact serves — the migration's central proof.

    A migration that proves itself only on in-memory transport has proven nothing about the
    deployed artifact (FG1). This REQUIRES the `migration_wire` fixture (a REAL uvicorn TCP
    server + real client, per §6.2). Marked `wire` so it runs in the deploy/gate lane, not the
    default unit lane. The build MUST make every assertion below pass:

    * serves at the configured path (C2 lifespan propagation did not silently fail — FG1);
    * tools/list returns the 15 built-ins + every registered extension tool (D6);
    * a BUILT-IN and an EXTENSION tool call EACH produce exactly one trace row, read back from
      the store (B1 funnel ∀ — the FG2 reach catch; register the CounterExtension so an
      extension tool EXISTS, since the prod registry ships empty);
    * serverInfo.version == _resolve_version() (D4 / FG4);
    * the served transport mode matches pre-migration (stateful: a mcp-session-id is minted —
      C5 / FG8).
    """

    async def test_wire_smoke_is_specified_not_yet_runnable(self) -> None:
        pytest.skip(
            "REQUIRES the `migration_wire` real-uvicorn fixture (design §6.2 / §6.1 in-image "
            "conformance, packet-01a instrument). The build implements it reusing "
            "scripts/fastmcp_migration_spike.py; the assertions it must carry are in this class's "
            "docstring. Kept as an explicit, un-satisfiable placeholder rather than a silently "
            "absent gate (a guard nobody runs is a hope with a filename)."
        )


@pytest.mark.wire
class TestTheHostOriginProtectionIsEnabledAndConfigured:
    """§5b-C3' / Item 3 / the config RIDER: enable host_origin_protection, configure allowed_hosts.

    The spike MEASURED (Item 3 GO): ENABLED -> a spoofed Host is 421; OFF -> accepted (today's
    gap). And the default is OFF (`http_host_origin_protection == False`), so the migration MUST
    explicitly pass `host_origin_protection=True`/"auto" AND set `allowed_hosts` for lore's real
    proxied topology (TLS terminated upstream by nginx-ingress) — an unconfigured allowlist 421s
    LEGIT production traffic. Every assertion below is REQUIRED (design §6.6-3, spike rider):

    * a spoofed `Host` header is REJECTED (421) — a check lore does NOT have today;
    * a LEGIT proxied `Host` is ACCEPTED (not 421) — the config rider (else prod 421s);
    * a bad `Origin` is REJECTED (403); an ABSENT Origin is ALLOWED (C3 preserved);
    * ordering (Item 2): with a VALID token, a spoofed Host/bad Origin is rejected BEFORE the
      TokenVerifier runs (the "zero outbound Google call" property packet 39 inherits).
    """

    async def test_host_origin_protection_is_specified_not_yet_runnable(self) -> None:
        pytest.skip(
            "REQUIRES the `migration_wire` fixture with host_origin_protection ENABLED and "
            "allowed_hosts configured for the bind (design §6.2 / §6.6-3). Assertions in the "
            "docstring. A legit proxied Host MUST pass (the config rider) or the gate itself 421s "
            "prod traffic."
        )


@pytest.mark.wire
class TestTheAuthPostureAndCompositionOrderAreUnchanged:
    """§5b-C4 / FG6: bad token -> 401, bad Origin -> 403; the Bearer(Origin(app)) order holds.

    The bespoke Origin + Bearer ASGI wrappers never touched the SDK; they wrap `http_app()`
    identically (design C3/C4). A build that reordered them, or lost a layer, changes the auth
    posture. REQUIRED (in-image auth suite): with auth enabled, a bad token -> 401 and a bad
    Origin -> 403, and the composition order is preserved.
    """

    async def test_auth_posture_is_specified_not_yet_runnable(self) -> None:
        pytest.skip(
            "REQUIRES the `migration_wire` fixture with an enabled auth block (design §6.2). "
            "Assertions in the docstring. Reuse `_auth_fixtures.wire_session` — but note the "
            "build MUST first update `_auth_fixtures.stub_heavy_startup`, which reaches the "
            "DELETED `mcp._lore_eager_guard._build` (coupling #3, outside this contract's writable "
            "set)."
        )


# =========================================================================== #
# SECTION G — PIN-THE-MISS: bounds this packet does NOT close (design §6.4).
# =========================================================================== #
class TestTheTwoSpikeBoundsAreCarriedNotClosed:
    """§6.4: the two unmeasured spike bounds are packet 39's, not this migration's.

    Neither is closed here; each is carried with a NAMED re-open trigger (PIN-THE-MISS):
    1. the REAL OAuth verification path (Google tokeninfo POST) — the spike used a static
       TokenVerifier stand-in, proving the SEAM, not Google-OAuth verification.
       RE-OPEN: packet 39's build.
    2. long-lived token-refresh — the spike used a single short-lived non-refreshing token; the
       raw SDK contextvar can go stale after refresh on a long-lived session. Mitigation for 39:
       prefer `fastmcp.server.dependencies.get_access_token()` (request-scope-first). RE-OPEN:
       39's hosted principal using refreshable tokens on long-lived sessions.

    This packet's surface touches NEITHER, so there is nothing to assert against — the bounds
    are documented here (and in the report) so a later engineer meets them DELIBERATELY, and are
    the contract's explicit hand-off to packet 39.
    """

    def test_this_packet_does_not_build_oauth_or_token_refresh(self) -> None:
        # A guard against SCOPE CREEP: if a future edit adds a real Google verifier or a
        # token-refresh path to THIS packet's surface, this bound is being closed here and the
        # PIN-THE-MISS note above must be revisited. Documented, not enforced (there is no packet-
        # 59 symbol to bind against); the enforcement lives in packet 39's contract.
        assert True, "carried bound — see the docstring's re-open triggers (design §6.4)"


# =========================================================================== #
# SECTION H — the migration's TEST-SURFACE impact: full-suite gate + affected-file
# enumeration (adversary-59 ⑤). The collect-only gate is blind to RUNTIME breaks.
# =========================================================================== #
#
# The FIXING of these files is the BUILD's job; this contract NAMES them (a durable worklist)
# and documents that the migration's acceptance gate is a FULL-SUITE run, not collect-only.
# Each entry: file -> (break kind, the retired symbol/behaviour it reaches). Measured by
# adversary-59 on the reference build (§⑤). "COLLECT-VISIBLE" = a module-level ImportError the
# §6.6 collect-only gate SEES; "RUNTIME" = collects fine, RED only under the full suite / in-image
# (the class collect-only is BLIND to); "TOOLERROR" = a `pytest.raises(ToolError)` keyed on the
# mcp SDK's ToolError, which won't catch `fastmcp.exceptions.ToolError`; "SOFT-CORPSE" = passes on
# the migrated build via a retired reach, teaching a retired mechanism in its docstring.
_MIGRATION_AFFECTED_TEST_FILES: dict[str, tuple[str, str]] = {
    "test_eager_startup.py": ("COLLECT-VISIBLE", "imports _ProcessLifespanGuard (deleted, §5b-C2)"),
    "test_mcp_server.py": ("RUNTIME+TOOLERROR", "in-method import of _ProcessLifespanGuard; ToolError"),
    "test_extension.py": ("RUNTIME", "reaches mcp._tool_manager (renamed _local_provider, P9)"),
    "test_task_read_surface.py": ("RUNTIME", "reaches mcp._tool_manager (renamed _local_provider, P9)"),
    "test_hosted_readonly_posture.py": ("RUNTIME+TOOLERROR", "reaches mcp._tool_manager; ToolError"),
    "test_auth_composition.py": ("RUNTIME", "reaches mcp._tool_manager (renamed _local_provider, P9)"),
    "test_backoff_seam.py": ("RUNTIME", "mock-patches _EagerStartupLifespan._acquire_eager_lease_with_retry"),
    "test_tool_allowlist.py": ("TOOLERROR", "imports mcp.server.fastmcp.exceptions.ToolError"),
    "test_permission_resolver_seam.py": ("TOOLERROR", "imports mcp.server.fastmcp.exceptions.ToolError"),
    "test_server_version.py": ("SOFT-CORPSE", "green via retired mcp._mcp_server.version; teaches it"),
    "_auth_fixtures.py": ("RUNTIME", "stub_heavy_startup reaches deleted mcp._lore_eager_guard._build"),
}


class TestTheMigrationAffectedTestFilesAreEnumerated:
    """§6.6 / adversary-59 ⑤: the migration's RUNTIME test-surface impact is a durable worklist.

    THE WRONG GATE (measured, adversary-59 ⑤): the design §6.6 gate is ``pytest --collect-only``
    (zero-new-delta vs #333). collect-only is BLIND to the migration's RUNTIME breakages — it sees
    only a module-level ImportError (``test_eager_startup.py``), and MISSES every test whose BODY
    reaches ``mcp._tool_manager`` (→ ``_local_provider`` AttributeError), mock-patches a deleted
    symbol, or ``pytest.raises`` the wrong ``ToolError``. On the reference build collect-only saw
    1 of ~8+ breakages. So the migration acceptance gate MUST be a FULL-SUITE run
    (``pytest -n auto``) OR the §6.1 in-image conformance — NOT collect-only alone (module
    docstring). This class does NOT fix those files (build scope); it makes the enumeration a
    durable, citable worklist so the build meets each one DELIBERATELY, and asserts the worklist
    still carries the classes collect-only cannot see (so a future edit cannot quietly gut it).
    """

    def test_the_worklist_names_the_runtime_and_soft_corpse_classes(self) -> None:
        kinds = {kind for kind, _reach in _MIGRATION_AFFECTED_TEST_FILES.values()}
        # The whole point of ⑤: the worklist must carry breakage classes collect-only is BLIND to.
        assert any(kind.startswith("RUNTIME") for kind in kinds), (
            "the affected-file worklist names no RUNTIME breakage — the class collect-only cannot "
            "see (adversary-59 ⑤). A worklist that lost these has lost the reason it exists."
        )
        assert "SOFT-CORPSE" in kinds, (
            "the worklist dropped the SOFT-CORPSE class (test_server_version.py passes on the "
            "migrated build via the retired mcp._mcp_server.version reach while its docstring "
            "teaches that retired mechanism — a green suite hiding a corpse)."
        )
        assert any(kind.startswith("TOOLERROR") or "TOOLERROR" in kind for kind in kinds), (
            "the worklist dropped the ToolError-import mismatch class (~4 files import the mcp SDK "
            "ToolError; a pytest.raises won't catch fastmcp.exceptions.ToolError)."
        )
        # NON-VACUITY: the two most load-bearing runtime breaks are named explicitly, so the
        # worklist cannot shrink to a token single entry and still pass.
        assert "test_eager_startup.py" in _MIGRATION_AFFECTED_TEST_FILES
        assert "test_extension.py" in _MIGRATION_AFFECTED_TEST_FILES


# =========================================================================== #
# SECTION I — rename-sweep: no retired mcp/trace NAME survives in production source
# (adversary-59 residual (b); the P8d natural-language-surface failure class).
# =========================================================================== #
#: The mcp-SDK/trace symbol NAMES this migration RETIRES. Post-migration NONE may survive in
#: ``loremaster.server`` — not in code (the migration deletes/replaces the references) and not in
#: PROSE (a docstring/comment teaching a retired name is the P8d "natural-language surface no gate
#: checks" defect; adversary-59 found a stale ``TracingFastMCP`` at server.py:2475 that the
#: telemetry-PLAN prose scan cannot see because it keys on retired PLAN PHRASES, not NAMES).
#: BARE, anchor-free substrings (the CLAUDE.md rename-sweep idiom — prose carries no structural
#: anchors). Each is specific enough not to be a substring of a live name: "request_ctx" is NOT a
#: substring of fastmcp's "request_context"; "streamable_http_app" is distinct from "http_app".
_RETIRED_MCP_NAMES: tuple[str, ...] = (
    "TracingFastMCP",
    "request_ctx",
    "streamable_http_app",
)


def _retired_name_hits(source: str, name: str) -> list[tuple[int, str]]:
    """Every ``(line_number, line)`` in ``source`` containing ``name`` (case-insensitive)."""
    needle = name.lower()
    return [
        (lineno, line.strip())
        for lineno, line in enumerate(source.splitlines(), start=1)
        if needle in line.lower()
    ]


class TestNoRetiredMcpNameSurvivesInProductionSource:
    """Residual (b): after the migration, no retired mcp/trace NAME survives in ``server.py``.

    Complements ``test_the_deleted_apparatus_is_gone`` (which checks the SYMBOLS are absent as
    module attributes) by covering NAMES in both CODE and PROSE — the surface the telemetry-PLAN
    prose scan in test_trace_telemetry.py misses (it keys on retired PLAN phrases, not NAMES). The
    threat model is the honest author who leaves a stale docstring/comment teaching a retired name
    (adversary-59 residual (b): a lingering ``TracingFastMCP`` reference). BARE substring patterns
    (rename-sweep idiom); every residual hit is reported with its file:line so a build can give each
    a verdict, per the P8d "no wholesale 'all remaining hits are X'" rule.

    ⚠ RED UNTIL THE MIGRATION LANDS (by construction): pre-migration ``server.py`` defines/uses all
    three names live, so this reddens today — the correct lifecycle for a rename pin (it goes green
    only once the migration removes the last reference). If a mention is DELIBERATE historical prose
    the build wants to keep, reword it to not NAME the retired symbol, or narrow ``_RETIRED_MCP_NAMES``
    with a documented reason — never silence the sweep wholesale.
    """

    @pytest.mark.parametrize("retired_name", _RETIRED_MCP_NAMES)
    def test_the_retired_name_is_absent_from_server_source(self, retired_name: str) -> None:
        server = importlib.import_module("loremaster.server")
        source = inspect.getsource(server)
        hits = _retired_name_hits(source, retired_name)
        assert not hits, (
            f"loremaster.server still names the retired symbol {retired_name!r} in "
            f"{len(hits)} place(s) (code or prose):\n"
            + "\n".join(f"  · server.py:{lineno}: {line[:120]}" for lineno, line in hits)
            + f"\n\nThe migration RETIRES {retired_name!r} (TracingFastMCP→on_call_tool middleware "
            "M3; request_ctx→MiddlewareContext.fastmcp_context B5; streamable_http_app→http_app "
            "C1). Every live reference must be removed and every docstring/comment teaching the "
            "name reworded — a stale name in served/production prose is the P8d defect class no "
            "other gate checks. Give each hit above a verdict; do not silence this sweep wholesale."
        )

    def test_the_sweep_itself_fires(self) -> None:
        # THE CONTROL (a probe needs a control — PKT-28 C1): the sweep must SEE a retired name and
        # IGNORE a live one, on samples built here, so a broken walk cannot pass vacuously.
        assert _retired_name_hits("x = TracingFastMCP()  # retired\n", "TracingFastMCP"), (
            "the sweep did not flag a line that plainly contains the retired name — it cannot see "
            "what it certifies."
        )
        # DISCRIMINATION: the live fastmcp accessor `request_context` must NOT trip the
        # `request_ctx` pattern (else the sweep reddens correct post-migration code and gets
        # switched off).
        assert not _retired_name_hits(
            "ctx = context.request_context.lifespan_context\n", "request_ctx"
        ), (
            "the sweep flagged the LIVE fastmcp `request_context` accessor as the retired "
            "`request_ctx` — a false positive on correct migrated code would earn this sweep a "
            "`# noqa` and stop it guarding anything."
        )
        # And `http_app` (the live replacement) must NOT trip `streamable_http_app`.
        assert not _retired_name_hits("inner = mcp.http_app(path=path)\n", "streamable_http_app")
