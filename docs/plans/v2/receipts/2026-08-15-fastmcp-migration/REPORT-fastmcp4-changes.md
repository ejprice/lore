# REPORT — fastmcp4-scout: FastMCP 4.0 investigation

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done
- **Deviations:** report filename is `REPORT-fastmcp4-changes.md` (per spawn brief), not the idle-gate default `REPORT-fastmcp4-scout.md`; wrote a custom idle-gate contract declaring it (`/tmp/claude-idle-gate-lore/<session>-fastmcp4-scout.contract`).
- **Packages considered:** none — no mechanism specified (read-only research; I built/specified no code mechanism).
- **Reuse ledger:** none — introduced no new symbols.
- **Graded:** n/a — research report; renders no verdict on a code artifact.
- **Scope of all claims:** measured 2026-08-15 against **fastmcp 4.0.0b3** (released 2026-08-14) vs stable **3.4.7** (2026-08-10). 4.0 is BETA and moving weekly — every claim is provisional until a stable 4.0.0.
- **Biggest finding:** 4.0 is a **large** delta, not a small one — it is a full rebuild onto **MCP Python SDK v2** and the sessionless **2026-07-28** protocol (handshake/sessions gone, server-initiated sampling/roots/elicitation removed). It *strengthens* lore's "3.x now / 4.x later" sequencing.
- **Correction to a briefed assumption:** of the three extras flagged as "genuinely new 4.0 surface," only **`tasks`** is 4.0-native. **`code-mode`** shipped in **3.1.0** and **`apps`** in **3.0.0** — their extras merely persist in 4.0 metadata.
- **Coverage bound:** concrete release notes surfaced for **b1** (the big breaking release) and **b3** (latest); a1/a2/b2 confirmed to exist by date [pypi] but their individual notes were not separately retrievable (alpha/interim). The b1→b3 span carries the substance.
- **Receipt pointers:** §1 changed · §2 why · §3 new features (§3.1 code-mode / §3.2 apps / §3.3 tasks) · §4 mcp v2 + mcp-types · §5 timeline · §6 lore sequencing.

Confidence tags per claim: **[release-notes]** (GitHub/gofastmcp changelog + release themes) · **[docs]** (gofastmcp.com doc pages) · **[pypi]** (PyPI metadata/JSON) · **[inferred]** (my reasoning across sources).

---

## 1. What CHANGED in 4.0 relative to 3.x

The one-sentence version: **4.0 rebuilds FastMCP's engine on the official MCP Python SDK v2, and adopts the sessionless `2026-07-28` MCP protocol as the default.** Everything else in this section falls out of those two moves. [release-notes][docs]

### 1a. Dependency shifts (the hard, verifiable core) [pypi]
Measured from PyPI JSON, 2026-08-15:

| | `fastmcp-slim` **3.4.7** | `fastmcp-slim` **4.0.0b3** |
|---|---|---|
| official SDK pin | `mcp<2.0,>=1.24.0` | `mcp<3.0.0,>=2.0.0` (moved into the `mcp`/`server`/`client` extras) |
| protocol types | *(none — bundled in `mcp`)* | **`mcp-types<3.0.0,>=2.0.0` as a CORE requirement** |
| HTTP client | `httpx<1.0,>=0.28.1` | **`httpx2>=2.5.0`** |
| pydantic | `>=2.11.7` | `>=2.12.0` |
| starlette | (via extras) | `>=1.0.1` (in server/client extras) |

The shape of the split is itself a finding: in 4.0 the **slim core depends only on `mcp-types`** (pure wire shapes, no HTTP stack); the full `mcp` v2 SDK + `httpx2` + `starlette` moved *into* the `mcp`/`server`/`client` extras. That is the `mcp-types` split (§4) working as designed — a consumer that only needs types (a gateway/proxy) never pulls an HTTP stack. This **confirms and refines** the briefed fact ("4.0.0b3 pins mcp<3.0,>=2.0 AND mcp-types<3.0,>=2.0"): both pins are real, but `mcp-types` is core and `mcp` is extras-gated. [pypi]

### 1b. Removed / renamed server & client surfaces [docs — v3→v4 upgrade guide]
- **Server-initiated back-channels REMOVED entirely:** `ctx.sample()`, `ctx.sample_step()`, `ctx.list_roots()` are gone; `FastMCP(sampling_handler=...)` and `sampling_handler_behavior=` removed. Rationale: the modern sessionless protocol has no server→client request channel. [docs][release-notes]
- **`ctx.elicit()` narrowed:** now requires `response_type=` (e.g. `ctx.elicit("Confirm?", response_type=bool)`), and **works only on handshake-era connections (≤2025-11-25); it RAISES on the modern `2026-07-28` protocol.** [docs]
- **Method renames:** `FastMCP.as_proxy(sub)` → `create_proxy(sub)`; `import_server(sub)` → `mount(sub)` (note: *different semantics* — mount is live); `mount(prefix="x")` → `mount(namespace="x")`. [docs]
- **Tool decorator changes:** `serializer=` removed → return a `ToolResult`; `exclude_args=` removed → use `Depends()` injection; object-mode decorators and `FASTMCP_DECORATOR_MODE` removed. [docs][release-notes]
- **`McpError` construction changed:** `McpError(code=-32000, message="text")` — the old `McpError(ErrorData(...))` raises `TypeError` under SDK v2. [docs]
- **Import relocations:** `fastmcp.server.proxy` → `fastmcp.server.providers.proxy`; `fastmcp.server.openapi` → `FastMCP` + `OpenAPIProvider`; component shims (`fastmcp.tools.tool`, `fastmcp.resources.resource`, `fastmcp.prompts.prompt`) removed → import from the direct modules; `TaskConfig` → `fastmcp.utilities.tasks`; `CurrentDocket`/`CurrentWorker` → `fastmcp_tasks.dependencies`. All 3.x/3.0 deprecated module shims and dead parameters dropped. [docs][release-notes]
- **Removed transport params:** `StreamableHttpTransport(sse_read_timeout=...)`. [docs]

### 1c. Behavioral shifts [docs][release-notes]
- **`fastmcp.Client` now defaults to `mode="auto"`** — it negotiates the modern sessionless era by default. This **breaks clients/servers relying on `on_initialize`, session state, or `ctx.elicit()`**. [docs]
- **Protocol-era negotiation is the default** ("Negotiate the best mutual protocol era by default") — one deployment serves both handshake-era (≤2025-11-25) and modern (2026-07-28) clients. [release-notes]
- **Middleware scope widened:** middleware now runs for *every inbound message*, including notifications and previously-filtered failed requests. [release-notes]
- **Templated-resource path-traversal screening is now on by default** — extracted parameter values are checked for `..`, absolute paths, and null bytes *before your handler runs*. [docs][release-notes]
- **Spec-correct error codes:** one SERVER span per request; resource-not-found now returns `-32602` (was `-32002`). [docs][release-notes]
- **Proxies** no longer validate backend results or mutate shared transports. [release-notes]
- **httpx2 TLS behavior differs:** validates via `truststore` against the OS trust store, not bundled certs — deployments may need `SSL_CERT_FILE`/`SSL_CERT_DIR`. [docs]
- **Env floors:** pydantic ≥2.12; docs also cite FastAPI ≥0.133.0 / Starlette ≥1.0.1 (Starlette floor confirmed in PyPI extras; the explicit FastAPI floor is a docs claim, not present in `fastmcp-slim` core pins). [docs][pypi]

---

## 2. WHY 4.0 exists (the maintainers' stated rationale)

The rationale is explicit and consistent across sources — 4.0 is **not a feature bump, it is a foundation swap driven by an upstream protocol/SDK change**:

- **Release theme, b1 (2026-07-28), "Fourgone Conclusion":** *"FastMCP 4 makes stateful MCP applications work on the sessionless `2026-07-28` protocol while one deployment continues serving handshake-era clients. Tools can ask follow-up questions across requests, preserve authenticated user state, and move long-running work into background tasks without sticky sessions."* [release-notes]
- **The upstream cause:** the MCP `2026-07-28` protocol revision **eliminates the connection handshake and session model**. *"A 2026-07-28 client does not open a connection, negotiate, and then talk. Every request carries its protocol version, client info, and client capabilities in `_meta`."* Server-initiated requests vanish. [docs — mcp SDK whats-new]
- **The v3→v4 upgrade guide frames it as SDK-driven:** the v4 rebuild "aligns FastMCP with the MCP Python SDK v2," whose two fundamental shifts are moving protocol types into standalone `mcp_types` and renaming all fields camelCase→snake_case. [docs]
- **The major-version bump is warranted** because supporting a sessionless protocol requires removing the server→client back-channel (sampling, roots, server-initiated elicitation) that many 3.x servers relied on — an unavoidable breaking change, hence a major version. [inferred, from 1b + the theme]
- **b3 theme, "Fast Fourward" (2026-08-14):** moving v4 toward general availability (hardening, security bumps, compatibility fixes) — i.e. the *why* of b3 specifically is stabilization, not new scope. [release-notes]

Bottom line on WHY: **4.0 is the downstream consequence of MCP SDK v2 + the 2026-07-28 sessionless spec.** FastMCP could not adopt the new protocol without a breaking rebuild, so it took the major version to also clean out 3.x deprecations. [inferred]

---

## 3. NEW features the 4.0 line introduces

Genuinely-new 4.0 surface (from b1's "New Features" + b3 enhancements) [release-notes]:
- **Migration to MCP Python SDK v2** — the new engine (see §4).
- **Stateless session state** — `UserSession` / `SessionId`: preserve authenticated user state *without* sticky sessions, on the sessionless protocol.
- **Background tasks** via the `io.modelcontextprotocol/tasks` extension (SEP-2663) — see §3.3.
- **Guard-mode multi-round-trip (MRTR) tools** (SEP-2322) — tools can ask follow-up questions across requests; client-side MRTR driver + response cache.
- **FastMCP-native server extension API** (SEP-2133) — `mcp.add_extension(...)`.
- **Server-side identity assertion** (SEP-990 ID-JAG) — enterprise identity.
- **Server-level cache hints** (SEP-2549) + `KeyValueResponseCacheStore` for distributed client response caching; client response cache.
- **Gateway/auth features:** routable transport headers for gateways (SEP-2243); scope step-up challenges for incremental authorization (SEP-2350); OAuth `application_type` honored in DCR (SEP-837); machine-to-machine client auth; `require_roles` auth check; `Auth0MCPProvider`; forward-ported Hugging Face auth; (b3) Prefect Horizon auth client.
- **Client protocol mode negotiation** + telemetry off-switch + `mcp.protocol.version` span attribute + argument-completion request support.

### 3.1 code-mode — **NOT new in 4.0** (pre-existing 3.1 feature)
- **Introduced FastMCP 3.1.0** (version badge on the docs page; blog "Stop Calling Tools, Start Writing Code (Mode)"). [docs]
- **What it is:** an *experimental* transform that lets an LLM **write Python to orchestrate tools in a sandbox** instead of calling each tool directly. Solves two token-scaling problems: (1) loading every tool's schema into context upfront, and (2) every tool call being a context-window round-trip where intermediate results burn tokens. The LLM sees discovery-tool docstrings as descriptions. [docs]
- **The `code-mode` extra** in 4.0.0b3 pulls `pydantic-monty==0.0.18` (the sandboxed Python evaluator). [pypi]
- **4.0 relevance:** the extra persists; I found no evidence code-mode is *reworked* in 4.0. Its presence in 4.0 extras is continuity, not new scope. [inferred]

### 3.2 apps — **NOT new in 4.0** (pre-existing 3.0 feature)
- **Introduced FastMCP 3.0.0** (version badge on `gofastmcp.com/apps/overview`). [docs]
- **What it is:** tools that **return an interactive UI instead of text** — a chart, table, form, or dashboard rendered inside the conversation with working sort/search/tooltips/state. Builds on the **MCP Apps extension** and uses **Prefab** to describe UIs in Python. [docs]
- **The `apps` extra** pulls `prefab-ui>=0.18.0`. [pypi]
- **4.0 relevance:** apps predates 4.0; 4.0's changelog only touches apps peripherally (app-visibility enforcement, late-bound app tool names surviving composition). Continuity, not new scope. [release-notes][inferred]

### 3.3 tasks — **the one genuinely 4.0-native item of the three**
- **Introduced FastMCP 4.0.0** (version badge on the tasks docs page). [docs]
- **What it is:** protocol-level **background tasks** — a task-enabled tool returns a task ID immediately; the client polls for status and retrieves results when ready. Coordinated *through the MCP protocol itself*, not application-level concurrency — enabling long-running work with **no sticky session**. [docs]
- **Spec basis:** the MCP background-tasks extension `io.modelcontextprotocol/tasks`, **SEP-2663**. [docs][release-notes]
- **The `tasks` extra** installs the `fastmcp-tasks` package, providing `TasksExtension` (registered via `mcp.add_extension(TasksExtension())`, required for `task=True` tools) and dependencies `CurrentDocket`/`CurrentWorker` (in `fastmcp_tasks.dependencies`). [docs]
- ⚠ **Caveat / possible predecessor:** one source noted "FastMCP 2.14 began adopting the MCP 2025-11-25 spec, headlined by protocol-native background tasks." So an *earlier* tasks notion may have existed under the older spec; the **4.0 tasks feature is the `io.modelcontextprotocol/tasks` / SEP-2663 implementation** specifically. Treat "tasks brand-new in 4.0" as *true for this extension/SEP*, with the older-spec ancestor flagged. [release-notes][inferred]

---

## 4. `mcp` 2.0 + `mcp-types` split, explained

From the official MCP Python SDK v2.0.0 release + "What's new in v2" [docs]:

- **The split:** protocol types now live in their own distribution, **`mcp-types`**, which *"depends on nothing but pydantic and typing-extensions, so a gateway, a proxy, or a code generator can consume MCP's wire shapes without installing an HTTP stack."* [docs]
- **Backward-compatible re-export:** `mcp` depends on `mcp-types` at an exact version and re-exposes it, so existing code keeps writing `import mcp.types as types` / `from mcp.types import Tool` — *"a permanent alias, every name the same object."* Per-version wire packages are private (`mcp_types._v*`); `mcp.types` is a permanent alias for `mcp_types`. [docs]
- **snake_case attributes:** every Python attribute is now snake_case (`result.is_error`, `tool.input_schema`, `listing.next_cursor`). **The JSON on the wire stays camelCase** — only the Python attribute spelling changed. [docs]
- **2026-07-28 protocol / sessionless:** no handshake, no session; every request self-describes in `_meta`; server-initiated requests removed. One 2.x server serves every earlier revision too. `pip install mcp` now installs 2.x. [docs]
- **httpx2:** the SDK's HTTP client is now `httpx2` (TLS via OS truststore). [docs]
- ⚠ **Possible naming conflation to watch:** the SDK "what's new" also states *"`FastMCP` renamed to `MCPServer`"*. This refers to the **official SDK's own bundled** `mcp.server.fastmcp.FastMCP` class, **not** the standalone `fastmcp` (gofastmcp) package, which keeps the `FastMCP` name. Don't read this as the gofastmcp package renaming its main class. [inferred]

**Why this matters for the 4.0 story:** the `mcp-types` split is *why* `fastmcp-slim` 4.0 can put only `mcp-types` in its core and gate the heavy `mcp` SDK behind extras (§1a) — a real, verifiable architecture improvement, not just a version churn. [inferred][pypi]

---

## 5. Stability / timeline read

- **Cadence** [pypi]: 4.0.0a1 (Jul 21) → a2 (Jul 24) → b1 (Jul 28) → b2 (Aug 7) → b3 (Aug 14). Roughly weekly.
- **No stable 4.0.0 and no RC yet** as of 2026-08-15. Latest is **b3**, a beta. Latest *stable* remains **3.4.7** (Aug 10) — note 3.x is **still actively released in parallel** with the 4.0 betas, i.e. 3.x is maintained, not abandoned. [pypi]
- **b3 theme is "toward GA"** (hardening, security bumps: cryptography 50.0.0, GoogleTokenVerifier audience pinning; compat fixes: Python 3.14 partial hints, `StatefulProxyClient` reconnection). Reads as late-beta stabilization, not new-scope churn. [release-notes]
- **Provisional surfaces flagged by the maintainers themselves:** code-mode is explicitly *experimental* ("discovery tools and parameters may evolve"). The SDK v2 protocol (`2026-07-28`) is itself very recent — the SDK betas were the "2026-07-28 RC" betas — so the whole 4.0 substrate is young. [docs]
- **Risk read:** adopting b3 now means tracking a weekly-moving beta on top of a months-old protocol spec; API details (import paths, defaults like `mode="auto"`) are still settling. [inferred]

---

## 6. Effect on lore's "3.x now / 4.x later" sequencing (short)

The research **strengthens** the "3.x now, 4.x later" plan; it does not weaken it. [inferred, grounded in §1–§5]

- **4.0 is a LARGE delta, not a small one.** It is a full engine swap (SDK v1→v2), a protocol change (handshake/sessions → sessionless 2026-07-28), and a removal of the entire server→client back-channel (sampling, roots, server-side elicitation). That is exactly the kind of foundation change worth *not* riding while it's a weekly beta.
- **3.x is not a dead end being obsoleted out from under you.** 3.4.7 shipped (Aug 10) *four days before* 4.0.0b3 — the 3.x line is actively maintained alongside the 4.0 betas. Adopting 3.x now does not strand lore. [pypi]
- **The 4.x-later step is well-cushioned by an official migration path:** there is a published v3→v4 upgrade guide with concrete before/after for every breaking change (§1b). A later hop is a documented migration, not a reverse-engineering exercise.
- **Nothing lore would build on 3.x is *removed* wholesale in 4.0** — the primitives (tools/resources/prompts, `FastMCP`, `Client`) survive; what changes is *how* stateful/interactive/back-channel patterns work. If lore's usage stays to plain tools/resources over HTTP, the 4.x migration surface is mostly renames + the httpx2/error-code/`mode="auto"` shifts. If lore ever wants `ctx.sample()`/`ctx.elicit()`/roots, note those are **gone or era-gated in 4.0** — design against that now. [inferred]
- **One thing that could pull 4.x forward:** if lore specifically wants **protocol-level background tasks** (SEP-2663, §3.3) or **stateless user session state**, those are 4.0-only. But `code-mode` (3.1) and `apps` (3.0) — two of the three extras the brief flagged — are **already available on the 3.x line**, so they are *not* reasons to jump to 4.0 early. [docs][pypi]

---

## Sources
- gofastmcp.com/changelog · gofastmcp.com/apps/overview · gofastmcp.com/servers/tasks · gofastmcp.com/servers/transforms/code-mode · gofastmcp v3→v4 upgrade guide (`docs/getting-started/upgrading/from-fastmcp-3.mdx`)
- GitHub PrefectHQ/fastmcp `docs/changelog.mdx` (v4.0.0b1 "Fourgone Conclusion", v4.0.0b3 "Fast Fourward")
- PyPI JSON: `fastmcp-slim` 4.0.0b3 and 3.4.7 (dependency pins + extras)
- MCP Python SDK v2.0.0 release + py.sdk.modelcontextprotocol.io "What's new in v2" (mcp-types split, snake_case, 2026-07-28 protocol, httpx2)

_All facts measured 2026-08-15 against fastmcp 4.0.0b3 (a moving beta) — re-verify before relying on any specific API detail._
