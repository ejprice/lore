# Blast-radius: migrating lore off `mcp.server.fastmcp` → standalone `fastmcp` 3.x

**Read-only investigation.** No code/tests/config touched. Branch `feat/surreal-unification`
@ `562c9bd`; lore index fresh (sync 12 min, sweep 2.4 min, watching `/workspace` on this
branch). Confidence tags per claim: **[live]** = introspected the installed SDK or grepped the
tree; **[docs]/[pypi]** = the web-research pass (cited); **[inferred]** = reasoned, not measured.

---

## 0. The one correction that reframes everything

The brief calls `fastmcp` a *"DIFFERENT distribution … not the `mcp` SDK."* Half true, and the
half that's false matters: **`fastmcp` 3.x is a *wrapper over* the official `mcp` SDK v1, not a
replacement for it.** Its runtime deps (via `fastmcp-slim` 3.4.7) pin **`mcp<2.0,>=1.24.0`**
[pypi]. So a migration does **not remove `mcp`** — it *adds* `fastmcp` on top and keeps `mcp`
transitively for the wire-protocol types. Current `mcp` 1.27.2 satisfies fastmcp 3.x's pin, so
the two coexist. `fastmcp` 4.0b1 (beta) is the one built on `mcp` v2. [pypi/docs]

Net: the migration is **swap the server façade, keep the protocol substrate.**

---

## 1. Inventory of coupling points

### 1a. Production code — **ONE file: `loremaster/loremaster/server.py`**

Grepped every workspace member + `scripts/` for `from mcp`/`import mcp` [live]. **Only
`server.py` imports `mcp.*` in production.** `loresigil`, `lorescribe`, `lorerunes`, and
`loremaster/auth.py` are **100% mcp-free.** Three import lines, then a small set of use sites:

| # | Site (server.py) | SDK surface | Public? |
|---|---|---|---|
| P1 | L77 `from mcp.server.fastmcp import Context, FastMCP` | `FastMCP` class + `Context` injection type | **PUBLIC** |
| P2 | L78 `from mcp.server.lowlevel.server import request_ctx` | `request_ctx` ContextVar | **INTERNAL** (private module) |
| P3 | L79 `from mcp.types import ContentBlock, ToolAnnotations` | wire-protocol schema types | **PUBLIC** (protocol pkg) |
| P4 | L9916 `class TracingFastMCP(FastMCP)` overriding `call_tool` | subclass + override | PUBLIC method, but see P5 |
| P5 | L9923-25 dep on `_setup_handlers` binding the **bound** `self.call_tool` at construction | construction-time binding behavior | **INTERNAL behavior** |
| P6 | L10216 `TracingFastMCP(name=…, instructions=…, lifespan=…, host=…, port=…, streamable_http_path=…)` | constructor kwargs | **PUBLIC** (kwargs differ in fastmcp — see §2) |
| P7 | L10229 `mcp._mcp_server.version = _resolve_version()` | private attr `_mcp_server` | **INTERNAL** (`# type: ignore` nearby) |
| P8 | L10393 `mcp.tool(name=…, description=…, annotations=…)` (built-in registration) | decorator | **PUBLIC** |
| P9 | L12035 `mcp._tool_manager.get_tool(spec.name)` (extension-name collision guard) | private attr `_tool_manager` | **INTERNAL** (`# noqa: SLF001`) |
| P10 | L12047 `mcp.add_tool(wrapper, name=…, annotations=ToolAnnotations(…))` (extension registration) | method | **PUBLIC** |
| P11 | L12484 `mcp.streamable_http_app()` (the inner ASGI app) | method | **PUBLIC** (renamed in fastmcp — see §2) |
| P12 | L10314 `mcp.list_tools()` (referenced; used in `scripts/comms_consumer_eval.py`) | method | **PUBLIC** |
| P13 | L10006 `request_ctx.get()` → `.lifespan_context`, `.request.headers` (trace emitter) | request-context object shape | **INTERNAL** (rides P2) |
| P14 | 7× `ToolAnnotations(readOnlyHint=…, …)` posture constants (L10251-10292) + `Context` annotation injection in `_extension_tool_wrapper` (L12122) | protocol type + injection | **PUBLIC** |

**Internal (private/unstable) reaches: P2, P5, P7, P9, P13.** Everything else is public.
Confirmed live against installed `mcp` 1.27.2 [live]: `streamable_http_app`, `call_tool`,
`list_tools`, `add_tool`, `tool`, `run` are public methods; `call_tool` **is** defined on
`FastMCP` (so the P4 subclass override is a real dispatch hook); `_setup_handlers`, `_mcp_server`,
`_tool_manager` are private; `request_ctx` is a `ContextVar` in the `lowlevel` module.

The `TracingFastMCP` docstring (L9919-9923) already names the migration target verbatim:
*"`mcp` exposes no middleware or hook API, and the standalone `fastmcp` package that does is a
server-wide dependency swap far beyond this change."* The developers know this is coming.

**Auth (`loremaster/auth.py`, 366 lines) — fully bespoke, zero SDK coupling** [live]:
`ApiKeyVerifier` (rotatable named Bearer keys, `hmac.compare_digest`), `BearerAuthMiddleware`
(401 fail-closed), `OriginValidationMiddleware` (DNS-rebinding/Origin allow-list, 403). Plain ASGI,
no Starlette import, no `mcp` import. Composed in `build_asgi_app` (L12455) as
`Origin(app)` or `Bearer(Origin(app))` wrapping `mcp.streamable_http_app()`. The module's own
docstring names **OAuth 2.1 + DCR as the documented FUTURE plug-in behind the same
`AuthVerifier` seam** — i.e. packet 39 (below).

### 1b. Test code — 11 files import `mcp.*` today (26 import lines) [live]

| Test file | SDK surface reached | Note |
|---|---|---|
| `test_trace_telemetry.py` | `FastMCP`, `ToolError`, `request_ctx`, `RequestContext`, `CallToolRequest/Params`, `TextContent` | pins the P4/P13 trace seam |
| `test_wire_discipline.py` | **AST-parses installed `FastMCP._setup_handlers`** | derives the handler set (P5) — see §2c |
| `test_hosted_readonly_posture.py` | `AccessToken`, `Tool`, `ToolManager`, `ToolError`, `ToolAnnotations` | **packet 39, pending** (see §1d) |
| `test_permission_resolver_seam.py` | `AccessToken`, `ToolError` | **packet 39, pending** |
| `test_auth_composition.py` | `AccessToken` | **packet 39, pending** |
| `test_google_token_verifier.py` | `AccessToken` | **packet 39, pending** |
| `_auth_fixtures.py` | `FastMCP`, `ClientSession`, `streamable_http_client`, `auth_context_var`, `AuthenticatedUser` | **packet 39** wire harness |
| `test_tool_allowlist.py` | `FastMCP`, `ToolError` | packet 45 (done) |
| `test_mcp_server.py` | `ToolError` | main server contract |
| `test_mutating_set_derivation.py` | `ToolAnnotations` | posture derivation |
| `test_refusal_observes_effect.py` | `ToolAnnotations` | packet 39 effect pin |
| `test_schema_rebuild.py` | `func_metadata._convert_to_content` (internal) | **already defensively `try/except/skip`-wrapped** against SDK layout drift |

### 1c. Packaging / deploy

- **`loremaster/pyproject.toml` L16:** `"mcp[cli]>=1.27"` — the single declared dep. Migration =
  add `"fastmcp<4"` (which re-pins `mcp<2.0,>=1.24`); keep/relax the `mcp` line or let it ride
  transitively. [live]
- **`uv.lock`:** `mcp` 1.27.2 present as a resolved dep (13 transitive deps incl. starlette,
  uvicorn, sse-starlette, pydantic, pyjwt). No `fastmcp` entry yet. Re-lock required. [live]
- **`Containerfile`:** bakes deps via `RUN uv sync --locked --all-packages` (L94) — **no explicit
  `COPY`/pip of `mcp`, no `EXPECTED_MEMBERS`/conformance guard naming `mcp`.** `mcp`/`fastmcp` ride
  the lockfile; the conformance provenance guard names only the 4 workspace *members*. So the image
  change is: re-lock, rebuild. Mechanical. [live]
- **`scripts/`:** `comms_consumer_eval.py` consumes `build_mcp_server(...)` + `mcp.list_tools()`
  (production API, survives). `lore_tool_name_currency.py` speaks the **wire** protocol
  (`mcp-session-id` header) — protocol-level, SDK-agnostic, survives. No script reaches SDK
  internals. [live]

### 1d. ⚠ The pending surface that dominates the decision — **packet 39 (hosted-security)**

`scripts/pending_contracts.yaml` + `docs/plans/v2/INDEX.md` reveal that the deepest SDK-auth
couplings **do not exist in production yet** — they are a written-but-unbuilt contract [live]:

- The hosted read-only **`ToolManager` subclass**, the **`LoreTokenVerifier`** (an
  `mcp.server.auth.provider.TokenVerifier` returning `AccessToken`), `GoogleOAuthConfig`,
  `resolve_posture`, `HostedToolRefusedError`, `PermissionFilteredToolError`, `lorerunes.Posture`
  — **none exist in the tree** (grepped; empty). They are symbols packet 39's build *will create*.
- The 11 packet-39 test files above are **committed RED and adjudicated** in
  `pending_contracts.yaml` (`id: packet-39-pending-build`) — a ruled, owned red bound, not a defect.
- Packet 39 has a **480-pin contract, four adversary passes, and the build was never started —
  deliberately.** All four failed on **one root cause** (INDEX L245, verbatim):
  > *"`_setup_handlers` binds at construction ⇒ post-construction installs are live in-process,
  > DEAD ON THE WIRE"* — WB30 (`call_tool`) → WB48 (guard after body) → WB93 (instance attr on
  > `list_tools`) → WB100 (**class** attr, flaky-green 5/10).

That is *exactly* the SDK limitation (P5) that fastmcp's middleware API is built to remove.
Packet 39 is queued in wave D (deps 45 ✅, 48, 49 open; current work is 47a). **Today's
production has no `ToolManager` subclass and no SDK auth-provider usage** — those are the future
this migration would land in front of.

---

## 2. Per-coupling portability verdict → `fastmcp` 3.x

Method: web-research pass over `pypi.org/pypi/fastmcp` + `fastmcp-slim` JSON and gofastmcp.com
docs [pypi/docs], corroborated against the installed `mcp` 1.27.2 baseline [live].

### 2a. Auth composition — **KEEP BESPOKE (mostly)** ✅/⚠

- **Bearer half → clean public target.** fastmcp ships `TokenVerifier`/`JWTVerifier`/
  `StaticTokenVerifier` and full `OAuthProvider`/`OAuthProxy`/`RemoteAuthProvider` +
  Google/GitHub/WorkOS providers, wired via the `FastMCP(auth=…)` ctor kwarg. lore's pluggable
  `AuthVerifier` seam could wrap a `TokenVerifier`, or packet 39's `LoreTokenVerifier` could
  target fastmcp's `TokenVerifier` instead of the SDK's. [docs]
- **Origin / DNS-rebinding half → NO documented fastmcp replacement.** fastmcp's auth is
  *identity* (token/OAuth), not *transport-origin* hardening; there is no surfaced
  `TransportSecuritySettings` equivalent on its auth docs [docs, negative]. **But lore already
  hand-rolls `OriginValidationMiddleware` as plain ASGI**, wrapping the app — it wraps `http_app()`
  identically to how it wraps `streamable_http_app()` today. **So this stays bespoke at zero
  migration cost** (it never touched the SDK). Verdict: **not a blocker; no work.**

### 2b. Read-only enforcement — **SUPPORTED PUBLIC HOOK replaces the subclass** ✅ (high value)

fastmcp exposes a first-class **Middleware API**: `mcp.add_middleware(M())` with an
**`on_call_tool`** hook receiving `MiddlewareContext` (`.message.name`, `.message.arguments`,
`.fastmcp_context`) + `call_next`. It can inspect/reject **before** dispatch (raise `ToolError`)
and wrap the result **after** [docs]. This cleanly replaces **both** jobs of the P4 `call_tool`
override:
1. **Trace-per-dispatch** (the `TracingFastMCP` seam) → an `on_call_tool` middleware wrapping
   `call_next` — supported, no subclass.
2. **Per-tool read-only gating** (packet 39) → an `on_call_tool` middleware inspecting
   `message.name` against the mutating partition.

⚠ **[inferred, strong]** This is very likely the mechanism that **unblocks packet 39's
dead-on-the-wire problem**: middleware is a *supported wire hook*, registered before serving,
so it is on the dispatch path by construction — dissolving the WB30→WB100 spiral that killed four
adversary passes. This is the single most consequential finding, but it is an inference from the
docs, **not a measured spike** — it needs a proof-of-concept before being trusted.

### 2c. The `_setup_handlers` wire-discipline pin — **REWRITTEN, not ported** ⚠

`test_wire_discipline.py` AST-parses the installed SDK's `FastMCP._setup_handlers` to derive the
handler set and enforce "no posture assertion calls a handler in-process." Under fastmcp:
- The concern's *root cause* (construction-time binding forcing in-process guards) **goes away**
  once enforcement is middleware (2b) — the "dead on the wire" failure mode is no longer
  reachable, so the pin's premise changes.
- fastmcp's `FastMCP` may or may not expose a `_setup_handlers` internal to parse [inferred,
  unknown]. **The test becomes meaningless-as-written and must be re-authored** around the
  middleware dispatch contract, not the low-level handler binding. Effort: rewrite one test module.
  This is coupled to packet 39's own WB-series pins.

### 2d. `mcp.types.*` (`ToolAnnotations`, `ContentBlock`) — **NO CHANGE** ✅

fastmcp does **not** re-export protocol types; they still come from `from mcp.types import
ToolAnnotations` / `ContentBlock` (fastmcp depends on `mcp` precisely for these) [docs, live].
**These import lines (P3, P14, and the `ToolAnnotations` test imports) stay byte-identical.**
Only `ToolError` moves: `mcp.server.fastmcp.exceptions.ToolError` → `fastmcp.exceptions.ToolError`
(a mechanical swap in ~4 test files). [docs]

### 2e. The two internal reaches — **BOTH get supported public replacements** ✅

- **P2/P13 `request_ctx`** → `from fastmcp.server.dependencies import get_context` →
  `get_context()` (works in nested/helper code like the trace emitter), plus `get_http_request()`
  for raw ASGI headers. Supported. [docs]
- **P7 `mcp._mcp_server.version`** → the **`FastMCP(version=…)` constructor kwarg.** Supported. [docs]
- **P9 `mcp._tool_manager.get_tool`** → **[unknown]** the research pass did not confirm a public
  tool-lookup/registry accessor on fastmcp's server. Needs a doc/introspection check during the
  spike; likely a public `get_tool`/registry exists, but treat as unverified.

### 2f. Server façade + ASGI — **moderate mechanical rework** ⚠

- `FastMCP` from `fastmcp` (not `mcp.server.fastmcp`); ctor takes `name`/`instructions`/`lifespan`/
  `version`/`auth`/`middleware`/`tools` [docs].
- ⚠ `host`/`port`/`streamable_http_path` are **not** fastmcp ctor kwargs [inferred] — path moves to
  `http_app(path=…)`, host/port to `run(...)`. lore serves via its own `uvicorn.Config(build_asgi_app(...))`
  (not `mcp.run()`), so host/port are lore-owned already; the `streamable_http_path` ctor kwarg (P6)
  moves to the `http_app(path=config.server.path)` call. One site.
- **`mcp.streamable_http_app()` → `mcp.http_app(path=…)`** (streamable is the default transport;
  the old name is deprecated). ⚠ Must propagate the fastmcp app's **lifespan** to lore's ASGI
  composition or the session manager won't init — lore already threads a custom
  `_EagerStartupLifespan` here, so this needs care but the seam exists. One site (`build_asgi_app`).

---

## 3. Does official `mcp` 2.0 rename `FastMCP` → `MCPServer`? — **YES, confirmed** ✅

`mcp` **2.0.0 released on PyPI 2026-07-28** [pypi]. It renames **`FastMCP` → `MCPServer` with NO
alias** — the old path is *removed*, not deprecated: `mcp.server.fastmcp.*` → `mcp.server.mcpserver.*`;
`get_context()` removed; lowlevel `request_context` removed; `McpError`→`MCPError`;
`ctx.fastmcp`→`ctx.mcp_server`; `mcp.types` becomes a permanent alias for a split-out `mcp_types`.
[docs: py.sdk.modelcontextprotocol.io/migration + GitHub v2.0.0 release notes]

**Consequence for the "stay official, do nothing" path:** it is *not* churn-free. lore is pinned
`>=1.27` (installed 1.27.2), unaffected today — but a future bump to `mcp` 2.0 is a **harder** break
than adopting fastmcp: it breaks **both** internal reaches (P2 `request_context` removed, P7
`_mcp_server` path renamed) *and* the P1 import, with no compatibility layer. fastmcp 3.x, by
contrast, keeps you on `mcp` v1 and cushions all of it. (fastmcp 4.0b1 is the eventual bridge onto
`mcp` v2.)

---

## 4. Effort & risk ranking

| Bucket | Touchpoints | Items |
|---|---|---|
| **Mechanical rename/config** | ~10 sites | pyproject dep swap + re-lock + image rebuild (uv sync unchanged); `from mcp.server.fastmcp import FastMCP, Context` → `from fastmcp import …` (P1 + test files); `ToolError` import swap (~4 tests); **`mcp.types` imports UNCHANGED** (P3/P14); `mcp.tool`/`add_tool`/`list_tools` API-compatible. |
| **Moderate rework** | ~6 sites | `streamable_http_app()`→`http_app(path=)` + lifespan propagation (P11, `build_asgi_app`); `streamable_http_path` ctor→`http_app` (P6); `mcp._mcp_server.version`→`FastMCP(version=)` (P7); `request_ctx.get()`→`get_context()`/`get_http_request()` (P2/P13, trace emitter); `TracingFastMCP.call_tool` override → `on_call_tool` middleware (P4/P5 — a supported re-architecture, arguably an upgrade); confirm public replacement for `mcp._tool_manager.get_tool` (P9). |
| **Bespoke re-engineering** | 0 net | Origin/DNS-rebinding middleware has no fastmcp built-in — **but already bespoke, so no work.** `test_wire_discipline.py` re-authored around middleware (§2c) — 1 test module, entangled with packet 39. |
| **Genuinely blocked** | 0 | Nothing is blocked. Every surface has a public or bespoke path. |

**Single highest-risk item: the packet 39 entanglement (§1d).** A 480-pin auth contract is written
and *stuck* against `mcp.server.fastmcp` internals (`_setup_handlers` dead-on-wire, a `ToolManager`
subclass, `AccessToken`/`TokenVerifier`). The migration changes the substrate that contract targets.
This is simultaneously the **biggest risk** (redo/rewrite 480 pins if migrated after 39 builds, or
mid-flight if migrated during) **and the biggest opportunity** (fastmcp middleware very likely
*unblocks* 39's construction-time-binding blocker — §2b). Timing this migration relative to packet
39 is the whole decision.

---

## 5. Open questions / decisions for the operator

1. **Sequence vs packet 39 (the load-bearing call).** Migrate to fastmcp 3.x **before** packet 39
   builds — so 39's enforcement is authored against fastmcp's `on_call_tool` middleware (likely
   dissolving its dead-on-the-wire blocker) — or ship 39 on SDK internals first and migrate later
   (paying to redo the `ToolManager`-subclass / `_setup_handlers` work)? Recommendation: **before**,
   but gated on a spike (Q2).
2. **Prove the middleware-unblocks-39 hypothesis first.** §2b is [inferred], not measured. A ~half-day
   spike — a fastmcp `on_call_tool` middleware that refuses a mutating tool *on the wire* — would
   confirm it before any commitment. Worth authorizing?
3. **Read-only enforcement mechanism, long-term.** Adopt fastmcp Middleware as the supported home for
   *both* the trace seam and packet 39 gating (retire the `TracingFastMCP` subclass), or keep the
   subclass for tracing and add middleware only for gating? (Recommend: consolidate on middleware.)
4. **Auth: wrap or replace the `AuthVerifier` seam?** Keep lore's pluggable seam and have
   `LoreTokenVerifier` target *fastmcp's* `TokenVerifier` (vs the SDK's), or adopt fastmcp's
   Google/OAuth providers directly? Origin/DNS-rebinding middleware stays bespoke either way.
5. **`mcp` 2.0 stance.** Confirmed hard break with no alias (§3). Is the intent fastmcp 3.x (stay on
   `mcp` v1, cushioned) now, with fastmcp 4.x / `mcp` v2 as a later, separately-planned step?

---

## One-line lean

**Migrate to `fastmcp` 3.x, and do it *before* packet 39 builds** — the production surface is a
single file with only 5 private reaches, all of which gain supported public replacements; the
middleware API cleanly replaces the `call_tool` subclass and very likely dissolves packet 39's
dead-on-the-wire blocker; `mcp.types` imports don't move; and it keeps you on `mcp` v1 while
deferring the harder no-alias `mcp` 2.0 break — but gate the commitment on a one-day
`on_call_tool` spike, because the packet-39-unblock is inferred, not yet measured.

---

## §7 — Packet 39 session/auth-state forward-compatibility

Judges packet 39's SESSION-STATE and AUTH-STATE assumptions against (a) the fastmcp 3.x
`on_call_tool` middleware migration (§2b) and (b) the eventual 4.x **sessionless** 2026-07-28
protocol (no handshake, no session, per-request identity in `_meta`, no server→client
back-channel). Source: `docs/design/2026-07-31-packet39-google-oauth.md` (design, **not yet
built** — the symbols live only in the pending-contract tests). Confidence: *contract-says* /
*code-says* / *inferred* / *spec-silent*.

### 7.1 — Session state (Q1): NO lore-owned connection-scoped state

- **Enforcement reads the principal PER-CALL, not per-connection.** §7-R13: `build_mcp_server`
  installs a posture-scoped `ToolManager` subclass whose `get_tool`/`list_tools` filter *"when
  the ambient principal (via `get_access_token()`) lacks `lore:write`."* The scope is decided at
  each lookup from the ambient auth context, not cached on a session object. *(contract-says,
  §7 "Enforcement (R13)")*
- **Permission resolution is per-dispatch.** The `AuthContext`/`PermissionResolver` seam (B4) is
  *"Derived at tool dispatch from `mcp.server.auth.middleware.auth_context.get_access_token()`."*
  *(contract-says, §4 "Extension seam")*
- **The token cache is content-keyed and process-global, not per-connection** — SHA-512 of the
  token is the only cache key (§4). A revoked principal rides their own entry's TTL regardless of
  connection. So no per-connection cache exists to lose. *(contract-says, §4)*
- **`on_initialize` / handshake hooks: packet 39 hangs NOTHING on them.** Grep of the design and
  of production `server.py`/`extension.py`/`auth.py` for `on_initialize`/`initialize`/handshake
  returns nothing enforcement-related. *(code-says + spec-silent — the design never mentions the
  handshake as a state anchor, which is itself the finding: it does not depend on one.)*
- **The only session-scoped object in the model is the SDK's own** `authorization_context`
  ("derives session identity from `client_id` + `claims["iss"]` + `subject`"). That is **borrowed
  from `mcp.server.auth`, not built by lore.** *(contract-says, §4)*

### 7.2 — Auth identity (Q2): resolved PER-REQUEST (stateless substance)

The Bearer token is on every HTTP request; `LoreTokenVerifier.verify_token` runs per request
(with the SHA-512 cache), mints an `AccessToken`, and the SDK's bearer middleware sets the ambient
`get_access_token()` contextvar per request — which the scoped lookup reads at dispatch. So
identity is **effectively per-request.** *(contract-says, §4 + §7)*

The one place it *reads* as per-connection is the **F3 pin: "a session created by X cannot be
resumed by Y"** (§4 "Identity minting"). That is an assertion about the SDK's session-binding
property, **not evidence lore requires sessions** — the underlying invariant is per-principal
identity isolation, which the SDK happens to express through session binding today. Packet 39
adopts the SDK's session model wholesale (it *deletes* the bespoke `BearerAuthMiddleware`/
`AuthVerifier` and *adopts* `TokenVerifier`/`AuthSettings`/`RequireAuthMiddleware`/
`authorization_context`, §4 + §14). The design even hedges: `AuthSettings(resource_server_url=
None)` *"suppresses `.well-known` — no discovery fiction **while sessions still bind**"* (§5 table)
— explicit awareness that session-binding is a current-protocol fact, not a lore invariant.
*(contract-says.)*

### 7.3 — Enforcement move to `on_call_tool` middleware (Q3): substance PRESERVED, two structural pins do NOT carry

Relocating enforcement from the scoped `ToolManager` onto fastmcp middleware preserves every
*behavioural* packet-39 assumption — **but must use TWO hooks, because packet 39 filters
visibility as well as invocation:**

- **`on_call_tool`** carries the refusal-before-body guarantee (refuse before `call_next` ⇒ body
  never runs), and **`on_list_tools`** carries the R13/WB93 requirement that a hosted principal's
  `tools/list` on the wire omits the mutating tools (9 not 15). Both hooks exist in fastmcp. *A
  migration that ports only `on_call_tool` silently drops the visibility half* — flagged. *(§2b +
  research; inferred that on_list_tools maps R13's list filter.)*
- **Preserved:** per-call ambient-principal read, fail-closed (unclassified tool born refused),
  loopback-unfiltered (no token ⇒ full surface), the derived-∀-EFFECT pin (observe `run`/`call_next`
  never entered), the `AuthContext`/`PermissionResolver` seam, scope constants in `lorerunes`.
- **CANNOT carry #1 — R13's "placement is not a builder variable" guarantee.** R13's whole safety
  argument is that the SDK's `ToolManager.call_tool` is `tool = get_tool(name); … await
  tool.run()`, so *"the callable EXISTS only as the lookup's return value"* — a builder physically
  cannot place the guard after the body. **Middleware REINTRODUCES placement as a free variable**
  (you *can* wrongly put the check after `call_next` — the exact WB48 defect). It is not a fatal
  loss because packet 39's derived-EFFECT pin catches mis-placement, but the migration re-exposes
  the class the scoped-lookup was engineered to make unrepresentable. *(inferred, high confidence.)*
- **CANNOT carry #2 — R16's `_setup_handlers` AST structural pins become meaningless.** They exist
  only to detect "post-construction instance attribute shadowing a bound handler = dead on the
  wire." Middleware IS the supported wire hook, so that failure mode is unreachable and the pins
  have no referent. This is a *simplification*, not a loss — but the R16 pins, the
  `all_registered_tools()` friction accessor, and `test_wire_discipline.py` are all deleted/rewritten,
  not ported. *(inferred, high confidence.)*

### 7.4 — Sessionless (4.x) break-test (Q4): narrow, and concentrated in BORROWED SDK machinery

- **Server→client back-channel (elicit / sampling / roots): NOT USED — zero break.** No
  `ctx.elicit()`/`create_message`/`list_roots`/sampling anywhere in the design or production code
  (the `roots:` hits are config source-tiers, unrelated to MCP protocol roots). lore's tools are
  pure client→server request/response. *(code-says, confirmed by grep.)*
- **`on_initialize` / handshake: NOT depended on — zero break.** (7.1). *(spec-silent → finding:
  no dependency.)*
- **BREAKS as written — the F3 "session X ≠ resumable by Y" pin** and the SDK's
  `authorization_context` "session identity" derivation. Sessionless has no session to create or
  resume; identity arrives per-request in `_meta`. The *requirement* (identity isolation) survives;
  the *expression* (session-resumption) must be re-authored as a per-request identity-isolation
  pin. *(contract-says the pin; inferred that it breaks under sessionless.)*
- **BREAKS by substrate — the entire `mcp.server.auth.*` adoption.** `TokenVerifier`,
  `AuthSettings`, `RequireAuthMiddleware`, `authorization_context`, `get_access_token` are the
  v1-SDK, session-shaped auth stack packet 39 plans to *adopt wholesale*. Under fastmcp they map to
  fastmcp's auth; under sessionless `mcp` v2 they change shape (v2 removes `get_context()` and
  lowlevel `request_context`, §3/§F). The per-request token *verification logic* (tokeninfo POST,
  caches, scope minting) is portable; the *plumbing it plugs into* is not. *(contract-says +
  research.)*

### 7.5 — NET verdict (Q5)

**Packet 39's auth-identity model is already per-request/stateless and forward-compatible — it
does NOT need a ground-up sessionless redesign.** It hangs no lore state on the connection
lifecycle, uses no back-channel, and depends on no handshake. What it *does* have is (i) an
ENFORCEMENT MECHANISM (scoped `ToolManager` subclass + R13 data-dependency argument + R16
`_setup_handlers` AST pins) precision-engineered against the mcp-v1-SDK's construction-time handler
binding — the exact substrate both fastmcp middleware AND sessionless dissolve — and (ii) an auth
*plumbing* choice (adopt `mcp.server.auth.*`) that is v1-and-session-shaped. Building either now =
building it twice.

**Recommendation (one-line lean):** Do NOT rebuild packet 39's auth-identity model (it is already
per-request), but **re-cut its ENFORCEMENT onto fastmcp `on_call_tool`+`on_list_tools` middleware
and re-target the token verifier at fastmcp's `TokenVerifier` BEFORE building — keeping the
`AuthContext`/`PermissionResolver` seam and the derived-EFFECT pin, dropping the scoped-ToolManager
subclass + the R16 `_setup_handlers` pins, and re-expressing the F3 session-resumption pin as
per-request identity isolation** — so the enforcement is authored once, on a substrate that
survives both the fastmcp migration and the sessionless protocol.

**Single highest-risk assumption:** every packet-39 refusal reads ONE seam — the SDK's ambient
`mcp.server.auth.middleware.auth_context.get_access_token()` contextvar, populated per-request by
the SDK's bearer middleware. If fastmcp (and later sessionless `_meta`) surfaces the principal
through a *different* mechanism (`MiddlewareContext.fastmcp_context` / fastmcp's own auth
dependency / a per-request `_meta` field) rather than that exact contextvar, the single seam the
entire enforcement, contract, and four-pass adversary record hang on must be rewired — and that
rewire is invisible to every existing packet-39 pin, which all assume the SDK contextvar is the
identity source. *(inferred; this is the seam to validate in the §5-Q2 spike.)*
