# Hand-roll inventory: what fastmcp 3.x REPLACES / DELETES vs what STAYS BESPOKE

**Read-only.** No code/tests/config touched. Branch `feat/surreal-unification` @ `562c9bd`; lore
index fresh (watching `/workspace` on this branch). Companion to
`docs/plans/v2/receipts/2026-08-15-fastmcp-migration/REPORT-fastmcp-blastradius.md` (the coupling
map + §7 packet-39 forward-compat) — this operationalizes *"frameworks over hand-rolling"* for the
migration: every place lore hand-rolls something *around* the `mcp` package that fastmcp 3.x
subsumes, dispositioned and ranked by **what keeping it COSTS**.

**Confidence tags:** `[src]` = read from fastmcp v3.4.7 source (`PrefectHQ/fastmcp`, path
`fastmcp_slim/fastmcp/…`) or introspected from installed `mcp` 1.27.2 · `[docs]` = gofastmcp.com ·
`[contract]` = packet-39 design/§8/§14 (`docs/design/2026-07-31-packet39-google-oauth.md`) ·
`[inferred]`.

**Method / grep disclosure (dogfood honesty):** consumer sets via `lore_impact`
(`build_mcp_server` = 1 prod / 101 test refs; only `server.py` imports `mcp` in prod). The
*exhaustive* sweep for hand-rolled ASGI/middleware/lifespan/protocol machinery is a **cross-cutting,
non-symbol textual seam** — lore's graph is function-granular and cannot answer "every hand-rolled
control around the framework" — so I used **`grep` for the exhaustiveness pass** (bare patterns:
`class .*Middleware`, `_ASGIApp`, `uvicorn\.`, `http\.response`, `TextContent\(`, `_convert`,
`event_store`, `stateless`, `streamable_http_app`, …). This is the sanctioned grep case #3
(cross-cutting map); no lore-tool defect — `lore_findings` not filed.

---

## 1. Dispositioned inventory (all instances)

Disposition ∈ **REPLACE** (fastmcp has a public equivalent) · **DELETE** (the hand-roll exists only
to work around an mcp-internal coupling that fastmcp dissolves) · **STAYS BESPOKE** (fastmcp has no
adequate equivalent). ⚠ = **silent breakage** (no error/log if it drifts or the SDK shifts).

| # | `file::symbol` | Hand-rolls | Disp. | fastmcp 3.x replacement / reason | Conf. |
|---|---|---|---|---|---|
| 1 | `server.py::TracingFastMCP.call_tool` (subclass of `FastMCP`) | ⚠ per-dispatch trace row via a `call_tool` OVERRIDE — its own docstring: *"`mcp` exposes no middleware or hook API, and the standalone `fastmcp` package that does is a … swap far beyond this change"* | **REPLACE** | `Middleware.on_call_tool` hook via `mcp.add_middleware(…)` — wrap `call_next`, record the row. Supported, no subclass, no `_setup_handlers` coupling | `[docs]`/`[src]` |
| 2 | `auth.py::BearerAuthMiddleware` + `auth.py::AuthVerifier` (ABC) | hand-rolled ASGI Bearer gate (401 fail-closed, `WWW-Authenticate`) + pluggable verifier seam | **REPLACE** | `FastMCP(auth=…)` + a `TokenVerifier` subclass. Packet 39 §8 item 9 / §14 already rules these **deleted** (against the SDK's `token_verifier=`); under fastmcp the target is fastmcp's `TokenVerifier` | `[contract]`/`[docs]` |
| 3 | `auth.py::OriginValidationMiddleware` **+ the unset `transport_security`** | Origin allow-list (absent-Origin allowed, loopback, fail-closed on bad IPv6) — AND lore sets NO `transport_security`, so ⚠ **no Host/DNS-rebinding validation at all today** | **REPLACE** | fastmcp `http_app(host_origin_protection=…, allowed_hosts=…, allowed_origins=…)` (env `FASTMCP_HTTP_*`) — validates Host + browser Origin, DNS-rebinding defense, wildcards. ⚠ default is `False` (opt-in). Caveat below | `[src]` |
| 4 | `server.py` `build_mcp_server`: `mcp._mcp_server.version = _resolve_version()` | version set via a **private attr** (`# type: ignore`) | **REPLACE** | `FastMCP(version="…")` constructor kwarg | `[src]`/`[docs]` |
| 5 | `server.py` `_register_extension_tools`: `mcp._tool_manager.get_tool(spec.name)` | ⚠ duplicate-tool-name guard via **private attr** (`# noqa: SLF001`) | **REPLACE** | public `await mcp.get_tool(name) is not None`, or fastmcp-native `FastMCP(on_duplicate="error")`. NB `_tool_manager` **does not exist in fastmcp 3.x** (renamed `_local_provider`) → hard break if not migrated | `[src]` |
| 6 | `server.py` `_record_tool_trace`: `request_ctx.get()` (from `mcp.server.lowlevel.server`) + `.request.headers`/`.lifespan_context` | request-context access via a **private lowlevel module** ContextVar | **REPLACE** | `from fastmcp.server.dependencies import get_context` → `get_context()` (+ `get_http_request()` for raw headers) — supported outside a tool fn | `[docs]` |
| 7 | `server.py` `build_asgi_app`: `mcp.streamable_http_app()` | inner ASGI app via the **deprecated** method name | **REPLACE** | `mcp.http_app(path=config.server.path)` (streamable is the default transport) | `[docs]` |
| 8 | `server.py::_ProcessLifespanGuard` | ⚠ refcounted per-process **lease** making heavy startup idempotent, because *"the session manager calls [the lifespan] once per MCP SESSION"* — spawns a 2nd watcher/reconcile otherwise | **DELETE** | fastmcp runs the user `lifespan=` **ONCE PER PROCESS** (ref-counted `_lifespan_ref_count`/`_lifespan_manager`), even in stateful mode — the entire guard is unnecessary; put the heavy build in `lifespan=` | `[src]` |
| 9 | `server.py::_EagerStartupLifespan` | ASGI lifespan-interceptor to drive the build EAGERLY at process startup + FP-07 bounded-retry | **DELETE** (mostly) | Obviated by #8 — pass `lifespan=` directly (fastmcp enters it at process startup). FP-07 bounded-retry re-homes *inside* that lifespan; the interceptor/lease-wiring is deleted | `[src]`/`[inferred]` |
| 10 | `auth.py::ApiKeyVerifier` | constant-time (`hmac.compare_digest`) rotatable named-key set, `SecretStr` holding (#211), all-keys-no-early-out | **STAYS BESPOKE** | fastmcp's `StaticTokenVerifier` is a **plaintext, non-constant-time dev helper** (`self.tokens.get(token)`; docstring: *"Never use this in production"*). Keep the class; wrap it as a custom `TokenVerifier`. (Packet 39 §8 item 11: "preserved-with-pin") | `[src]`/`[contract]` |
| 11 | `server.py::_extension_tool_wrapper` | introspects a `ToolSpec` handler signature to build a typed wrapper so FastMCP derives the input schema; refuses `*args`/`**kwargs`/positional-only | **STAYS BESPOKE** (reducible) | fastmcp auto-introspects type hints (`tools/function_parsing.py`) — the schema-building is redundant, but the runtime `ToolSpec`→typed-signature bridge + param-kind policy remain lore's. Can lean on `Tool.from_function`; core need stays | `[src]`/`[inferred]` |
| — | **Contract-only (packet 39, UNBUILT)** | | | | |
| 12 | pkt39 scoped `ToolManager` subclass (R13) of `mcp.server.fastmcp.tools.tool_manager.ToolManager` — hosted read-only enforcement | per-principal `get_tool`/`list_tools` filtering by `readOnlyHint`, engineered around the SDK's `ToolManager.call_tool` data-dependency | **REPLACE** | fastmcp `on_call_tool` **+ `on_list_tools`** middleware (visibility + gating). Building the subclass now = building against `ToolManager` internals that **don't exist in fastmcp 3.x** = building twice (prior report §7) | `[docs]`/`[inferred]` |
| 13 | pkt39 R16 `_setup_handlers` AST pins (`test_wire_discipline.py`) | AST-parses the SDK's `FastMCP._setup_handlers` to police "post-construction attr shadowing = dead-on-wire" | **DELETE** | The coupling they police (construction-time bound-handler binding) dissolves once enforcement is middleware — the pins have no referent. Delete/rewrite, not port | `[inferred]` |
| 14 | `tests/_auth_fixtures.py::running_asgi_app` (~30 lines) | hand-rolled ASGI **lifespan** runner for tests | **REPLACE** | `asgi-lifespan` `LifespanManager(app, startup_timeout=…, shutdown_timeout=…)` — packet 39 §14 already rules this replace (dep added to `dev` group); *"Never maintain both"* | `[contract]` |

**Not hand-rolls (checked, negative — lore does NOT hand-roll these; the SDK/FastMCP owns them):**
JSON-RPC framing, `CallToolResult`/`isError`, `TextContent`/`ContentBlock` construction, SSE/event
store, session-id management. Grep for `JSONRPC|isError|TextContent\(|_convert|event_store|
StreamingResponse` found only the protocol-typed `call_tool` return annotation and a test-only,
already-`try/except`-guarded `_convert_to_content` import. `mcp-session-id` is *read* as a trace
correlator, not managed. So there is no protocol-serialization hand-roll to migrate. `[src]`

---

## 2. Ranked shortlist — by COST OF KEEPING (highest first)

Cost = ongoing maintenance burden + divergence risk (coupling to mcp internals that shift) + blast
radius of a wrong choice + **silent-breakage** (no error when it drifts).

1. **#8+#9 — `_ProcessLifespanGuard` + `_EagerStartupLifespan` → DELETE.** *Highest cost.* Two whole
   classes (~150+ LOC: refcounted leases, an asyncio lock, an ASGI lifespan interceptor) that exist
   **solely** to paper over the mcp SDK's per-session lifespan re-entry — pure accidental complexity
   on the critical serving path, coupled to SDK dispatch internals
   (`_handle_stateful_request`→`run_server`→`lifespan`). fastmcp's ref-counted once-per-process
   lifespan makes ALL of it free. ⚠ **Silent:** a drifted lease spawns a second watcher →
   manifest contention, no error.

2. **#2+#3 — auth composition (`BearerAuthMiddleware`/`AuthVerifier` → REPLACE; Origin/`transport_security`
   → REPLACE).** *High + security + already in flight.* A hand-rolled ASGI security boundary is the
   textbook "frameworks over hand-rolling" target (upstream is better-tested, maintained). **Packet 39
   is about to rebuild this** — so the decision is *build it against fastmcp's `TokenVerifier`/`auth=`
   now, not the SDK's, to avoid building it twice.* ⚠ **Silent security gap TODAY:** lore sets no
   `transport_security`, so it has zero framework Host/DNS-rebinding validation — fastmcp's
   `host_origin_protection` closes it for free.

3. **#1 — `TracingFastMCP.call_tool` override → `on_call_tool` middleware.** *High, ⚠ silent-by-construction.*
   The docstring itself warns a plain `FastMCP` *"traces nothing while every emission pin still
   passes, served count stays 0 forever with every gate green"* — the trace seam breaks with **no
   signal**. The subclass couples to `_setup_handlers` binding the bound method; middleware is the
   supported, decoupled seam AND the same hook packet 39's enforcement needs (share it).

4. **#12 — packet-39 read-only enforcement (scoped `ToolManager` subclass) → `on_call_tool`+`on_list_tools`
   middleware.** *High strategic.* Unbuilt; if built against `ToolManager`/`_tool_manager` internals
   (which **don't exist in fastmcp 3.x**) it is thrown away at migration. Re-cut onto middleware
   *before* building (prior report §7). This is the item most likely to be **built twice** if the
   migration and packet 39 are sequenced wrong.

5. **#13 — `_setup_handlers` wire-discipline AST pins → DELETE.** *Medium.* Machinery + a contract-level
   AST invariant that exists only to police the dead-on-wire class; once enforcement is middleware the
   whole apparatus is dead weight. Deleting it removes a standing coupling to the SDK's private
   `_setup_handlers` source shape (which the pin literally `inspect.getsource`-parses).

6. **#5, #4, #6 — private-attr reaches (`_tool_manager.get_tool`, `_mcp_server.version`, `request_ctx`)
   → REPLACE.** *Medium.* Each is a `# noqa`/`# type: ignore` reach into mcp internals with a clean
   public fastmcp replacement. Two are **hard breaks** at migration (`_tool_manager`→`_local_provider`;
   lowlevel `request_ctx` gone), which is *good* (loud, not silent). ⚠ #5 is silent if the private
   attr merely changes shape: the collision guard would stop guarding with no error.

7. **#7, #14 — `streamable_http_app()`→`http_app()`; `running_asgi_app`→`asgi-lifespan`.** *Low.*
   Mechanical rename + a test-helper swap packet 39 already ruled.

8. **#10, #11 — `ApiKeyVerifier`, `_extension_tool_wrapper` → STAYS BESPOKE.** *Low / no action.*
   fastmcp has no adequate equivalent (constant-time verifier; dynamic-from-spec tool bridge). Keep,
   wrapping into the framework's seams.

**Single highest-value replacement:** **#8/#9 — deleting the process-lifespan apparatus** (biggest
accidental-complexity removal, on the serving hot path, with a silent-failure mode), closely followed
by routing packet 39's *soon-to-be-built* auth (#2/#3) and enforcement (#12) onto fastmcp's
`TokenVerifier`/middleware so they are authored once.

## 3. One caveat carried forward (do not drop)

**#3 Origin ordering:** packet 39 §8 R9 keeps a bespoke Origin layer **outermost** deliberately — so
a cross-origin browser attacker is rejected *before* credential parse (the "zero outbound Google
call" property). fastmcp's `host_origin_protection` lives in the http-app builder; whether it runs
*before* the `TokenVerifier` is **unverified `[inferred]`**. If fastmcp's guard runs after auth, the
outermost Origin layer stays bespoke *for that one ordering property only* — everything else in #3
still REPLACEs. Validate ordering in the migration spike.
