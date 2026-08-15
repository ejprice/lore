# Packet 59 design — migrate lore's MCP server off `mcp.server.fastmcp` → standalone `fastmcp` 3.x

**Author:** migration-author (Opus 4.8), 2026-08-15, at branch `feat/surreal-unification`
HEAD `41287c5` (`lore_index()` git_ref `41287c5bf…`, index fresh: sync/sweep ~8 min).
**Authority:** this is a PACKET DESIGN doc (roster law — a design packet). It rules the forks
that the receipts + spike + standing law DETERMINE, and ESCALATES the genuine operator/lead
forks (deploy posture, exact slot) as decisions-needed. It does NOT implement — the build is a
later tdd cycle (contract → contract-adversary → build → cold audit). Per the Opus-author rule,
§9 adversarially attacks this design before it ships.
**Inputs (durable receipts — cited section-exactly, never re-transcribed):**
- `lore_recall("fastmcp migration")` — the 2026-08-15 DECISION memory (target, coupling, next
  step) + the MEASURED spike memory (lead-verified GO). Ground truth; this doc builds on them.
- `docs/plans/v2/receipts/2026-08-15-fastmcp-migration/REPORT-fastmcp-blastradius.md` — coupling
  inventory (§1), per-coupling portability verdicts (§2), `mcp` 2.0 confirmation (§3), effort/risk
  (§4), and packet-39 session/auth forward-compat (§7).
- `…/REPORT-fastmcp-spike.md` — the VERIFIED GO spike (Q1 wire-gating, Q2 list-hiding, Q3 principal
  seam × 4 legs, §Verdict, §API-notes, §Instruments).
- `…/REPORT-fastmcp4-changes.md` — 4.0 is the LATER, larger step (§1, §6); NOT this packet's target.
- `REPORT-handroll-inventory.md` (lead-verified 2026-08-15; at repo root pending archive to
  `receipts/2026-08-15-fastmcp-migration/`) — the EXHAUSTIVE hand-roll inventory dispositioning every
  lore hand-roll around `mcp` (REPLACE / DELETE / STAYS-BESPOKE, ranked by cost-of-keeping). §3/§5/§6.6
  below are REVISED to fold it in (a revision pass over the first draft; the biggest change is §5b —
  the lifespan apparatus is now a ~150 LOC DELETE, not a PRESERVE).
- Live-read coupling sites at HEAD `41287c5` (grounded, not inherited from possibly-drifted line
  numbers): `TracingFastMCP` (server.py:9959), `TracingFastMCP.call_tool` (:10002),
  `_record_tool_trace` (:10032), `build_mcp_server` (:10156), `build_asgi_app` (:12498),
  `_EagerStartupLifespan` (:12256).
- `docs/design/2026-07-31-packet39-google-oauth.md` (§0 rulings R13–R16, §7, §17) — the packet
  this migration must precede; §7 of the blast-radius report judges it forward-compatible.

**Scope of all claims:** measured/read 2026-08-15 at HEAD `41287c5`. `fastmcp` API facts are from
the receipts (spike read fastmcp 3.4.7 installed source; blast-radius did a pypi/docs pass) — every
one is re-verified at CONTRACT time by reading the installed 3.x source, never coded from this doc.

---

## 0. Ruling summary

| # | Fork | Ruling / disposition |
|---|------|------|
| M1 | Target version | **`fastmcp>=3.4,<4`** (current 3.4.7). NOT 4.0 beta (§8). *(decision memory)* |
| M2 | Keep or drop `mcp`? | **KEEP, now TRANSITIVE (D4)** — fastmcp 3.x WRAPS mcp v1 (`fastmcp-slim` pins `mcp<2.0,>=1.24`); `mcp.types` imports do NOT move; `mcp` rides via fastmcp rather than a direct dep (§11-D4). *(blast-radius §0, §2d)* |
| M3 | Trace seam under fastmcp | **Re-home `TracingFastMCP.call_tool` → an `on_call_tool` middleware** (spike-proven on the wire); RETIRE the subclass + its `_setup_handlers` dependency. Strong rule; risk in §5a/§9. |
| M4 | Trace WRITE logic | **REUSE `_record_tool_trace` unchanged** — only the FUNNEL (subclass method → middleware hook) changes. ONE-IMPLEMENTATION (§10). |
| M5 | Read-only enforcement (packet 39) | **NOT built here.** This packet delivers the SUBSTRATE (`on_call_tool`/`on_list_tools` middleware + the surviving principal seam); §7 states the sequencing dependency 39 inherits. |
| M6 | Acceptance instrument | **The in-image conformance run (packet 01a) + a REAL uvicorn wire smoke are REQUIRED gates** — this is #131/#139 territory: only the running artifact proves the cake (§6). |
| M7 | Two unmeasured bounds (spike) | **CARRIED as named bounds this packet does NOT close** (real OAuth tokeninfo POST; long-lived token-refresh) — they are packet 39's to close (§6.4). |
| M8 | Deploy posture | **RULED (operator 2026-08-15): STANDALONE** rebuild+recreate + the in-image gate (§6.1), so the substrate swap is proven in isolation, not co-mingled with 39 (§11-D1). |
| M9 | Slot in wave D | **RULED (operator 2026-08-15): BUILD NOW, ahead of the wave-D queue** — packet 59 is the IMMEDIATE NEXT BUILD (§11-D2). Table position (before 39) still records the hard sequencing constraint. |
| M10 | Packet 39 INDEX `Depends on` cell | **FLAGGED, not edited** (§11-D3) — 39's row is outside this packet's writable set; its `Depends on` should gain `59`. |
| M11 | The process-lifespan apparatus (`_ProcessLifespanGuard`+`_EagerStartupLifespan`, ~150 LOC) | **DELETE — `[inferred]`, spike-gated (§6.6-1).** fastmcp's once-per-process ref-counted `lifespan=` obviates it; the heavy build moves into `lifespan=`. A NO-GO on the spike ⇒ KEEP. *(hand-roll inventory #8/#9, §5b-C2 — this REVISES the first draft's PRESERVE)* |
| M12 | `transport_security` UNSET today (zero framework Host/DNS-rebinding validation) | **CLOSE IT — migration BENEFIT.** Enable fastmcp `host_origin_protection`; ⚠ its ordering vs the TokenVerifier is spike-gated (§6.6-2), and the bespoke outermost Origin layer may stay for that one property. *(inventory #3, §5b-C3′)* |
| M13 | Finding #184 (03b's "swap far beyond this change" bound) | **RESOLVED — trigger (b) fired** (packet 39 = the 2nd non-telemetry `call_tool` consumer; #102 shared-substrate law). Lead-annotated #184 → 59 (§7 provenance). |

**Genuine forks escalated to the operator/lead: §11. Bounds I could not measure: §12.**

---

## 1. What this packet IS and is NOT

**IS:** a pure SUBSTRATE swap of lore's MCP server façade — from the official `mcp` SDK's bundled
`FastMCP` (`from mcp.server.fastmcp import FastMCP`) to the standalone `fastmcp` 3.x package. The
**served behaviour does not change**: the same 15 tools, the same wire protocol, the same trace
emission, the same Origin/Bearer auth behaviour. The packet's whole "question" (Trust Leg 1) is
*"does the server behave identically after swapping the façade?"* — and its acceptance PROVES that
on the running artifact.

**Production surface is one file** (`loremaster/loremaster/server.py`, 3 import lines + a small use
set). `loresigil`, `lorescribe`, `lorerunes`, `loremaster/auth.py` are 100% mcp-free
*(blast-radius §1a)*.

**IS NOT:**
- **NOT the 4.0 migration** — 4.0 rebuilds onto `mcp` SDK v2 + the sessionless 2026-07-28 protocol;
  a separate, later step (§8). *(4.0-scout §1, §6)*
- **NOT packet 39** — no auth, no OAuth, no read-only enforcement is BUILT here. This packet only
  makes the middleware substrate 39 will author its enforcement on exist and be proven (§7).
- **NOT a behaviour change to the served surface.** Any diff in the wire protocol, tool set, trace
  emission, or auth posture is a DEFECT, not a feature — the DUAL removed-behaviour inventory (§5)
  and the acceptance gates (§6) exist to catch exactly that.

---

## 2. The one correction that frames the whole packet

The name "different distribution" is half-right and the wrong half matters: **`fastmcp` 3.x is a
WRAPPER OVER the official `mcp` SDK v1, not a replacement.** `fastmcp-slim` 3.4.7 pins
`mcp<2.0,>=1.24.0`; the installed `mcp` 1.27.2 satisfies it. So the migration **adds `fastmcp` on
top and keeps `mcp` transitively for the wire-protocol types** — it is *swap the server façade, keep
the protocol substrate*. *(blast-radius §0.)* Consequence: `from mcp.types import ContentBlock,
ToolAnnotations` stays byte-identical (§5, D-line C0); only the server FAÇADE class and a handful of
accessors move.

---

## 3. Coupling → migration map

Every production coupling point, its portability verdict, and the migration action. Sites cited by
SYMBOL (line numbers drift). `P#` ids are the blast-radius report's §1a inventory rows; verdicts are
its §2 (re-verify each against installed 3.x source at contract time).

| P# | Site (`server.py`) | today (`mcp` SDK) | migration action | risk |
|----|------|------|------|------|
| P1 | import in `server.py` head | `from mcp.server.fastmcp import Context, FastMCP` | `from fastmcp import Context, FastMCP` | mechanical |
| P3/P14 | protocol types | `from mcp.types import ContentBlock, ToolAnnotations` | **UNCHANGED** — fastmcp re-uses `mcp.types` | none *(§2d)* |
| — | `ToolError` (tests) | `mcp.server.fastmcp.exceptions.ToolError` | `fastmcp.exceptions.ToolError` (~4 test files) | mechanical |
| P4/P5 | `class TracingFastMCP(FastMCP)` + `call_tool` override; relies on `_setup_handlers` construction-time binding | subclass on wire by construction | **RE-ARCHITECT → `on_call_tool` middleware** (§5a); the `_setup_handlers` dependency DISSOLVES | **moderate — highest logic risk** |
| P6 | `TracingFastMCP(name=, instructions=, lifespan=, host=, port=, streamable_http_path=)` | ctor kwargs | `name/instructions/lifespan/version` → fastmcp ctor; `streamable_http_path` → `http_app(path=)`; `host/port` → confirm read from `config.server` at the uvicorn call site, NOT off the mcp object (§5c-D2) | moderate |
| P7 | `mcp._mcp_server.version = _resolve_version()` | private-attr reach | **`FastMCP(version=_resolve_version())` ctor kwarg** — resolved at construction (env-baked-after-import still honoured) | mechanical, pinned (§5c-D4) |
| P2/P13 | `from mcp.server.lowlevel.server import request_ctx` → `request_ctx.get()` in `_record_tool_trace`; `.lifespan_context`, `.request.headers` | private ContextVar + request shape | **inside the middleware, use `MiddlewareContext.fastmcp_context` directly** (no ContextVar); the AppContext + headers accessors are re-verified against installed 3.x source (§5a-B5/B7). fastmcp fallback for nested code: `fastmcp.server.dependencies.get_context()` / `get_http_request()` | **moderate — accessor shape must be verified** |
| P8/P10 | `mcp.tool(...)` (built-ins) + `mcp.add_tool(wrapper, ...)` (extensions) in `_register_tools` | decorator + method | **API-compatible** — verify signatures at contract; PIN ∀ registered tool callable + funnelled (§5a-B1) | low, pinned |
| P9 | `mcp._tool_manager.get_tool(spec.name)` (extension collision guard) | private-attr reach | **REPLACE — HARD BREAK, loud=good.** `mcp._tool_manager` DOES NOT EXIST in fastmcp 3.x (renamed `_local_provider`), so leaving it fails LOUDLY at migration rather than silently. Target the PUBLIC `await mcp.get_tool(name) is not None`, or fastmcp-native `FastMCP(on_duplicate="error")` *(inventory #5, `[src]`)* | low (loud break) |
| P11 | `mcp.streamable_http_app()` in `build_asgi_app` (+ `_ProcessLifespanGuard`/`_EagerStartupLifespan` around it) | deprecated ASGI factory + ~150 LOC lifespan apparatus | **`mcp.http_app(path=config.server.path)`; the lifespan apparatus DELETEs** — fastmcp's once-per-process ref-counted `lifespan=` obviates it (§5b-C2, spike-gated §6.6) | **moderate — highest WIRE risk** |
| P12 | `mcp.list_tools()` (referenced; `scripts/comms_consumer_eval.py`) | public method | API-compatible; verify | low |
| — | `OriginValidationMiddleware`, `BearerAuthMiddleware` (`auth.py`, bespoke ASGI) | plain ASGI wrap | **UNCHANGED** — never touched the SDK; wraps `http_app()` identically *(blast-radius §2a)* | none |

**Genuinely blocked: nothing.** Every surface has a public or bespoke path *(blast-radius §4)*.

**Packaging** *(blast-radius §1c; D4 RULED)*: `loremaster/pyproject.toml` — **REPLACE `"mcp[cli]>=1.27"`
with `"fastmcp>=3.4,<4"`**; `mcp` then rides TRANSITIVELY via `fastmcp-slim`'s `mcp<2.0,>=1.24.0` pin
(D4 caveats: (a) the transitive pin is BARE `mcp` — NO `[cli]` extra; (b) `mcp.types` becomes an
undeclared direct import, operator-accepted — §11-D4).
⚠ **The dependency is the FULL `fastmcp` umbrella, NOT `fastmcp-slim` directly.** Since 3.3 the code
lives in `fastmcp-slim`, and `fastmcp` = `fastmcp-slim[client,server]` + opt-in extras. lore needs NO
extras — the `anthropic`/`openai`/`gemini`/`azure` extras are LLM SDKs; `apps`/`code-mode`/`tasks` are
features lore does not use — so plain `fastmcp` is correct; add `fastmcp[tasks]` etc. ONLY if a future
feature needs it. (Stated so no future reader re-raises "slim or umbrella?".)
Then `uv lock`; rebuild image (`uv sync --locked --all-packages` unchanged; the Containerfile has NO
`EXPECTED_MEMBERS`/COPY naming `mcp`, so no conformance-guard edit — VERIFY at kickoff, per the
store/registration discipline). Scripts (`comms_consumer_eval.py`, `lore_tool_name_currency.py`) use
production API / the wire protocol only — SDK-agnostic, survive.

---

## 4. Test-surface impact (11 files import `mcp.*` today — blast-radius §1b)

Two test modules are RE-AUTHORED (not ported), because the migration changes their PREMISE — this is
the rename/reshape "tests written before a semantic change certify the OLD world" hazard; grep the
test tree for retired names at kickoff:
- **`test_wire_discipline.py`** — AST-parses the installed SDK's `FastMCP._setup_handlers` to enforce
  "no posture assertion calls a handler in-process". Its root cause (construction-time binding) is
  GONE once enforcement is middleware; **rewrite around the middleware dispatch contract, or delete
  with an explicit superseded-header** if 39 re-authors it *(blast-radius §2c; packet-39 §7.3 CANNOT-carry-#2)*.
- **`test_trace_telemetry.py`** — pins the `TracingFastMCP.call_tool`/`_record_tool_trace` seam
  (`ok`-latch, cancellation, the funnel). **Re-author onto the middleware** — every behaviour in §5a
  keeps a discriminating pin; the cancellation + `ok`-latch pins MUST survive (they are the
  false-green catch in §9-FG3).

`ToolError`-import swaps: ~4 files. `mcp.types` imports (`ToolAnnotations`, `ContentBlock`):
UNCHANGED across all test files. Packet-39's 11 pending-contract test files (committed RED, adjudicated
`packet-39-pending-build`) are 39's to re-cut per §7 — NOT this packet's (but they must still COLLECT:
§11-D4).

**Test-helper reuse (inventory #14):** `tests/_auth_fixtures.py::running_asgi_app` hand-rolls an ASGI
lifespan runner (~30 lines) → **`asgi-lifespan` `LifespanManager`** (packet 39 §14 already ruled this
replace; the dep is in the `dev` group). "Never maintain both." This is the in-process lifespan runner
for tests that don't spin a full uvicorn; the §6.2 wire smoke uses REAL uvicorn (which drives the ASGI
lifespan for real — the FG1 catch), so the two are complementary, not duplicative.

---

## 5. The two re-architectures + DUAL removed-behaviour inventory

The DUAL law: a diff that deletes/replaces code ships with a removed-behaviour inventory, each item
adjudicated. Both swaps below delete real, load-bearing behaviour. Adjudication key:
**PRESERVE+PIN** (mechanism cited) / **DROP** (reason) / **OLD-BUG** (not re-pinned) /
**SPEC-SILENT→operator**.

### 5a. `TracingFastMCP.call_tool` subclass → `on_call_tool` middleware

**Why the swap and not "keep the subclass":** the subclass is live-on-wire ONLY because
`mcp.server.fastmcp`'s `_setup_handlers` registers the *bound* `self.call_tool` at construction
(memory: "FastMCP binds its protocol handlers at CONSTRUCTION"). fastmcp is a DIFFERENT class with a
DIFFERENT dispatch; **betting a `call_tool` override survives the swap is untested**, whereas the
spike MEASURED that `on_call_tool` middleware refuses/observes on the wire *(spike §Q1)*. So the
package now DOES do the job (middleware) that it did not when `TracingFastMCP` was written — the
docstring's own "the standalone `fastmcp` package … is a server-wide dependency swap far beyond this
change" is exactly the swap this packet makes.

Removed-behaviour inventory (source: `TracingFastMCP` + `call_tool` + `_record_tool_trace`, read live
at HEAD `41287c5`):

| # | Behaviour today | adjudication | pin that discriminates |
|---|------|------|------|
| B1 | ONE trace row per dispatch, on the WIRE path **by construction**, covering built-in + extension-registered + later-registered tools (one funnel) | **PRESERVE+PIN** — middleware runs on the wire *(spike §Q1)*; but funnel-coverage is now a REACH variable, not "by construction" | wire smoke calls a **built-in AND an extension tool**, asserts BOTH produce exactly one trace row (§9-FG2) |
| B2 | Tool outcome ALWAYS wins; a trace-write failure is `logger.exception("trace.emit.failed")` and NEVER surfaces to the caller | **PRESERVE+PIN** — same try/finally around `call_next` | inject a trace-write failure; assert the tool result still returns + the log line emitted (hostile fixture) |
| B3 | `ok` starts False, latched True ONLY after dispatch returns; NO `except` arm ⇒ `CancelledError` (BaseException) leaves `ok=False` | **PRESERVE+PIN** — the latch is the numerator's integrity | a cancelled dispatch records `ok=False`, never True (§9-FG3) |
| B4 | Emission sits in `finally`, **`anyio.CancelScope(shield=True)` + `anyio.fail_after(_TRACE_EMIT_TIMEOUT_SECONDS)`** — writes the row even under level-triggered anyio cancellation, but can never hang a dying request | **PRESERVE+PIN VERBATIM** — the request is still under MCP's anyio cancel scope inside middleware, so the shield is still required | under cancellation the row is still written AND emission cannot exceed the timeout bound |
| B5 | `request_ctx.get()` → `LookupError` ⇒ DEBUG + return (in-process / no-transport: no store to write through) | **PRESERVE+PIN, mechanism CHANGES** — middleware reads `MiddlewareContext.fastmcp_context` directly (no ContextVar); the "no reachable write store ⇒ no-op" invariant holds. ⚠ exact accessor for the lifespan AppContext verified against installed 3.x source at contract | a middleware call with no reachable write store is a silent no-op (not a crash), + the un-wired branch still WARNs (B6) |
| B6 | `_trace_write_store` `AttributeError` ⇒ WARNING + return (emission un-wired — loud) | **PRESERVE** — `_record_tool_trace` reused unchanged (M4) | the existing un-wired WARNING pin, re-pointed |
| B7 | declared identity from `arguments` (str values only, `_TRACE_DECLARED_KEYS`); transport correlator from `request.headers` — MEASURED, never declared | **PRESERVE+PIN, mechanism CHANGES** — headers via the fastmcp request accessor (`get_http_request().headers` or the middleware context); verify at contract | identity recorded only for str args; a non-str arg mints no identity |
| B8 | latency measured around `super().call_tool` | **PRESERVE** — measured around `call_next` | latency present + bounded |

**M4 discipline:** `_record_tool_trace` is REUSED (the trace WRITE policy — identity rules, ordinal
mint, correlator, failure posture — stays ONE function). Only its CALLER changes from a bound method
to a middleware hook. Prove sharing by construction: the middleware calls `_record_tool_trace`; no
second emission path is written.

### 5b. `mcp.streamable_http_app()` → `mcp.http_app(path=…)`, and the lifespan-apparatus DELETE

⚠ **REVISED after the lead-verified hand-roll inventory (`REPORT-handroll-inventory.md` §1 rows
#7/#8/#9, §2 rank 1, §3).** My first draft adjudicated `_EagerStartupLifespan` PRESERVE+PIN; the
inventory OVERTURNS that — `_ProcessLifespanGuard` + `_EagerStartupLifespan` are a ~150 LOC DELETE
(the inventory's single highest-value removal), because they exist SOLELY to paper over the mcp SDK's
per-session lifespan re-entry, which fastmcp's once-per-process ref-counted lifespan dissolves. The
payoff is `[inferred]` (source-read, not measured), so it is a SPIKE-VALIDATION gate (§6.6), not a
foregone deletion.

Removed-behaviour inventory (source: `build_asgi_app`, `_EagerStartupLifespan`, `_ProcessLifespanGuard`,
read live at HEAD `41287c5`; verdicts corroborated by the inventory's `[src]` reads of fastmcp 3.4.7):

| # | Behaviour today | adjudication | pin / gate |
|---|------|------|------|
| C1 | `inner = mcp.streamable_http_app()` mounted at `streamable_http_path` (ctor P6) | **REPLACE** — `mcp.http_app(path=config.server.path)` (streamable is the default transport) | wire smoke connects at the configured path and serves |
| C2 | `_ProcessLifespanGuard` (server.py:9853) refcounts a per-process lease so the heavy startup is idempotent (the mcp SDK enters the user lifespan ONCE PER SESSION, so a 2nd session would else spawn a 2nd watcher/reconcile) **+** `_EagerStartupLifespan` (:12256) hoists the build to ASGI process startup + carries FP-07 bounded-retry | **DELETE ~150 LOC — `[inferred]` → §6.6 SPIKE-VALIDATION.** fastmcp runs the user `lifespan=` ONCE PER PROCESS (ref-counted `_lifespan_ref_count`/`_lifespan_manager`), even stateful — obviating BOTH: put the heavy build directly in `lifespan=`; FP-07 bounded-retry re-homes INSIDE it. Accidental complexity on the serving hot path; ⚠ silent-failure mode today: a drifted lease spawns a 2nd watcher → manifest contention, no error. **PRESERVE the PROPERTY** ("heavy build runs once per process, eagerly at startup"), not the mechanism | §6.6 gate: prove (a) fastmcp enters `lifespan=` exactly once/process at ASGI startup, ref-counted teardown correct, in the served (stateful) mode; (b) the bespoke Origin/Bearer ASGI wrappers delegate the lifespan scope to fastmcp's `http_app` so it actually runs. **NO-GO ⇒ KEEP the guard/interceptor** (fall back to this draft's PRESERVE branch) |
| C3 | `OriginValidationMiddleware(app)` — bespoke Origin allow-list (absent-Origin allowed, loopback, fail-closed on bad IPv6), ALWAYS on | **PRESERVE (bespoke)** — never touched the SDK; wraps `http_app()` identically *(blast-radius §2a; inventory #3)* — but SEE the BENEFIT (C3′) and the ordering caveat below | bad-Origin → 403; absent-Origin allowed (in-image auth suite) |
| C3′ | **⚠ `transport_security` is UNSET today** ⇒ lore has ZERO framework Host/DNS-rebinding validation right now (a SILENT security gap; inventory #3, lead-verified: zero hits) | **MIGRATION BENEFIT** — enable fastmcp `http_app(host_origin_protection=…, allowed_hosts=…, allowed_origins=…)`: it validates Host + Origin + DNS-rebinding, closing the gap for free. ⚠ default is opt-in (`False`) → the migration MUST enable it | with `host_origin_protection` on, a spoofed `Host` header is rejected — a check that does not exist today (§6.6-3) |
| C4 | `BearerAuthMiddleware(app, …)` outermost when `auth.enabled` | **PRESERVE for THIS packet** (bespoke; packet 39 REPLACEs it onto fastmcp's `TokenVerifier` — inventory #2 / §7) — wrap order `Bearer(Origin(app))` unchanged | bad token → 401; order preserved (in-image auth suite) |
| C5 | Transport MODE (stateful today; local session-based) | **PRESERVE+PIN EXPLICITLY** — set the mode to match today's behaviour; do NOT inherit a possibly-different fastmcp default. 39 flips to `stateless_http=True` later *(spike §Q3 leg D proved both)* | the served mode matches the pre-migration mode (§9-FG8) |

⚠ **Origin-ORDERING caveat (inventory §3, carried forward — do NOT drop):** packet 39 §8 R9 keeps a
bespoke Origin layer OUTERMOST deliberately, so a cross-origin browser attacker is rejected BEFORE
credential parse (the "zero outbound Google call" property). fastmcp's `host_origin_protection` lives
in the http-app builder; whether it runs BEFORE the `TokenVerifier` is unverified `[inferred]`. **§6.6
gate:** if fastmcp's guard runs AFTER auth, the outermost bespoke Origin layer STAYS for that ONE
ordering property only — everything else in C3/C3′ still adopts fastmcp's protection.

### 5c. `build_mcp_server` constructor (P6/P7)

| # | Behaviour today | adjudication | pin |
|---|------|------|------|
| D1 | ctor `name` / `instructions` / `lifespan` | **PRESERVE** — fastmcp ctor kwargs; `lifespan(server: FastMCP)` shape matches | server boots; instructions served |
| D2 | ctor `host` / `port` | **VERIFY+REPOINT** — fastmcp ctor takes neither; lore serves via its own `uvicorn.Config`, so host/port must be read from `config.server.host/port` at the uvicorn call site, not off the mcp object. Confirm the uvicorn caller already reads config *(blast-radius §2f)* | uvicorn binds the configured host/port |
| D3 | ctor `streamable_http_path` | **MOVE → `http_app(path=)`** (C1) | (C1) |
| D4 | `mcp._mcp_server.version = _resolve_version()` (P7) | **PRESERVE → `FastMCP(version=_resolve_version())` ctor kwarg** — construction-time resolve retained | wire smoke reads `serverInfo.version == _resolve_version()`, not the SDK's (§9-FG4) |
| D5 | `mcp._lore_eager_guard = guard` instance attr; `getattr(mcp, "_lore_eager_guard", None)` in `build_asgi_app` | **DELETE with the guard (§5b-C2)** — the attr exists ONLY to surface the lease to `build_asgi_app`; on the DELETE branch there is no guard/interceptor, so the attr and its getattr both go. (If §6.6 forces the KEEP branch, this PRESERVEs) | DELETE branch: no `_lore_eager_guard` reference remains |
| D6 | `_register_tools(mcp, server)` registers 15 built-ins + extension tools | **PRESERVE+PIN** — `mcp.tool`/`add_tool` API-compatible | all 15 built-in + every extension tool register + are callable on the wire |
| D7 | "the ONE construction site MUST be the tracing subclass" pin | **REWRITE** — no subclass; the pin becomes "the ONE construction site MUST install the trace middleware" (a plain FastMCP with no middleware traces nothing) | mutation: remove the middleware install → the trace-count pin goes RED |

---

## 6. Acceptance gates (what the build must prove)

The standing gates apply (scoped pytest `-n auto` + `scripts/typecheck.sh` + `ruff` + the
`--currency` gate manifest + a cold REFUTE audit). ON TOP, this packet REQUIRES:

### 6.1 The in-image conformance run (packet 01a instrument) — REQUIRED
This is #131/#139 territory: the migration is proven ONLY by the running artifact. Run the suite IN
the deployed image (ephemeral container from the SAME image, tests mounted, `loremaster.__file__`
ASSERTED into site-packages so it grades the ARTIFACT, not the mount — finding #139). *A green suite
on the dev host says the recipe is right; only the image proves the cake — and the whole risk of a
substrate swap (fastmcp resolved, lifespan entered, session manager initialised) lives in the gap
between them.*

### 6.2 A REAL uvicorn wire smoke — REQUIRED (the spike's transport shape)
Not the in-memory transport. A `uvicorn` server on a TCP port, a real MCP client, asserting on the
wire:
- **serves at all** (C2 lifespan propagation didn't silently fail — the FG1 catch);
- **the full tool set** — `tools/list` returns the 15 built-ins + extension tools;
- **trace emission** — a **built-in AND an extension tool** call each produce exactly one trace row
  (B1 funnel coverage — the FG2 catch), read back via the store / `lore_index()` traces section.
  ⚠ The production extension registry ships EMPTY (`EXTENSION_REGISTRY = {}` — packet 46, dark until
  54), so the extension-tool leg MUST register the **packet-47a fake-domain fixture** to have an
  extension tool to funnel; a config with zero extensions cannot exercise FG2;
- **`serverInfo.version`** == `_resolve_version()` (D4 — the FG4 catch);
- **auth posture** — with `auth.enabled`: bad token → 401, bad Origin → 403 (C4/C5).

### 6.3 Cancellation + failure-posture pins — REQUIRED (re-authored, not deleted)
`test_trace_telemetry.py` re-authored onto the middleware; the `ok`-latch (B3), the shielded/bounded
`finally` (B4), and the trace-failure-never-surfaces (B2) pins MUST survive and still discriminate
(mutation-proven). Deleting them is the FG3 false-green.

### 6.4 The two spike bounds — PINNED as bounds this packet does NOT close (PIN-THE-MISS)
The spike's own named unmeasured bounds *(spike §Q3 rider, §Verdict H2)*. Neither is closed by this
migration; both are packet 39's. Carry each as a documented bound with a re-open trigger:
1. **Real OAuth verification path (tokeninfo POST)** — the spike used a static `TokenVerifier`
   stand-in, proving the SEAM/plumbing, not Google-OAuth verification. **Re-open: packet 39's build.**
2. **Long-lived token-refresh** — the spike used a single short-lived non-refreshing token; the raw
   SDK contextvar can go stale after refresh on a long-lived session. **Mitigation for 39 (spike
   rider):** prefer `fastmcp.server.dependencies.get_access_token()` (request-scope-first, a hardened
   superset). **Re-open: 39's hosted principal using refreshable tokens on long-lived sessions.**

### 6.5 Satisfiability + DUAL
- The contract ships a satisfiability receipt (0-failed against the adversary's reference build,
  including AFTER the lint the swap demands — orphaned-import deletion).
- The removed-behaviour inventory (§5) is the DUAL: every deleted behaviour has a preserved pin or a
  ruled DROP. The contract-adversary attacks it (P6b deleted-code enumeration; the quantifier attack
  on B1's funnel-∀).

### 6.6 Spike-validation gates (INFERRED payoffs — prove BEFORE the build commits)
The existing spike already PROVED (measured, lead-verified — spike §Verdict): middleware gates on the
wire, `on_list_tools` hides, the principal seam survives stateful+stateless. The items below are
`[inferred]` from the hand-roll inventory (source-reads of fastmcp 3.4.7, NOT measured against this
deployment) and MUST be measured in a migration spike — an extension of the existing spike harness,
run at the START of the build — before the build relies on them. They are NOT in the proven set;
each is a real FORK, not a foregone conclusion:
1. **The lifespan-apparatus DELETE (§5b-C2; inventory #8/#9).** Prove fastmcp enters the user
   `lifespan=` EXACTLY ONCE PER PROCESS at ASGI startup, with ref-counted teardown, in the served
   (stateful) mode — AND that the bespoke Origin/Bearer ASGI wrappers delegate the lifespan scope to
   fastmcp's `http_app`. **GO ⇒ delete ~150 LOC** (`_ProcessLifespanGuard` + `_EagerStartupLifespan` +
   the `_lore_eager_guard` attr), heavy build → `lifespan=`, FP-07 retry re-homed inside it. **NO-GO ⇒
   KEEP the guard/interceptor** (the §5b-C2 PRESERVE branch).
2. **The Origin-ORDERING property (§5b caveat; inventory §3).** Prove whether `host_origin_protection`
   runs BEFORE the `TokenVerifier`. If AFTER, keep the bespoke Origin layer OUTERMOST for the
   packet-39 §8 R9 "zero outbound Google call" property; everything else adopts fastmcp's protection.
3. **`host_origin_protection` closes the today-open Host/DNS-rebinding gap (§5b-C3′; inventory #3).**
   Prove the enabled setting actually rejects a spoofed `Host` header — a check lore does NOT have
   today (`transport_security` is unset). This is a security BENEFIT to bank, not just a swap.

---

## 7. Packet-39 sequencing dependency (proposal — not editing 39)

**Provenance — why this migration is now SANCTIONED (finding #184, lead-annotated → 59).** The fastmcp
swap was previously REFUSED for packet 03b (which wired trace emission at the `call_tool` seam):
`TracingFastMCP`'s own docstring calls it *"a server-wide dependency swap far beyond this change"*, and
#184 pinned that refusal with a re-open trigger. **Re-open trigger (b) = a SECOND non-telemetry
consumer of the `call_tool` seam.** Packet 39's read-only ENFORCEMENT is exactly that second consumer —
and the #102 ONE-IMPLEMENTATION law then requires the seam be a SHARED middleware substrate (trace +
enforcement on ONE `on_call_tool`, not two hand-rolled overrides). So the trigger has fired: the
migration is sanctioned, and 03b's "far beyond this change" bound is discharged BY this packet. The
lead annotated #184 → 59 in the ledger.

**This packet MUST sequence BEFORE packet 39 builds.** Rationale, from the receipts: 39's central
blocker across FOUR adversary passes was one root cause — `_setup_handlers` binds handlers at
construction, so post-construction installs are live in-process but DEAD ON THE WIRE (WB30→WB100).
The spike MEASURED that fastmcp `on_call_tool` middleware GATES on the wire (refuses before the body)
and `on_list_tools` HIDES a tool from `tools/list` on the wire *(spike §Q1/§Q2)* — i.e. this
migration DELIVERS the substrate that dissolves 39's blocker. Building 39 on `mcp.server.fastmcp`
internals first and migrating after would redo the `ToolManager`-subclass / `_setup_handlers` work
*(blast-radius §5-Q1, §7.5: "building either now = building it twice")*.

**What 39 inherits from this packet** (blast-radius §7.3, §7.5 — 39 re-cuts, this packet does NOT
build it): author 39's read-only enforcement on **`on_call_tool` (refuse-before-body) +
`on_list_tools` (hide from `tools/list`)** middleware — the two-hook requirement (a port of only
`on_call_tool` silently drops the VISIBILITY half). **KEEP** 39's per-request
`AuthContext`/`PermissionResolver` identity model (already per-request/stateless-substance,
forward-compatible). **DROP** the scoped `ToolManager` subclass + the R16 `_setup_handlers` AST pins
+ `test_wire_discipline.py` (their referent is gone). **RE-EXPRESS** the F3 session-resumption pin as
a per-request identity-isolation pin. **CARRY** the derived-∀-EFFECT pin (observe `call_next`/`run`
never entered on refusal) — and note middleware REINTRODUCES placement as a free variable (the WB48
class), so that pin is now load-bearing, not redundant *(blast-radius §7.3 CANNOT-carry-#1)*.

**Single highest-risk assumption 39 must validate** *(blast-radius §7.5)*: every 39 refusal reads ONE
seam — the principal via `get_access_token()`. The spike proved BOTH the SDK contextvar seam AND
`fastmcp.server.dependencies.get_access_token()` yield the principal from inside `on_call_tool`,
stateful and stateless *(spike §Q3 legs B/D)* — so the seam is PORTABLE, not must-be-rewired. Adopt
the fastmcp accessor (hardened superset) to also close the token-refresh bound (§6.4-2).

This packet does NOT edit `docs/design/2026-07-31-packet39-google-oauth.md`; the above is a proposal
39's build inherits. **§11-D3 RULED:** 39's INDEX `Depends on` gains `59` — the LEAD makes that
one-cell edit on commit.

---

## 8. The 4.0-later note (a future packet + its re-open trigger)

fastmcp 4.0 is NOT this packet's target and NOT a near-term step *(4.0-scout §1, §6)*: it is a full
rebuild onto `mcp` SDK v2 + the sessionless 2026-07-28 protocol (handshake/sessions gone,
server-initiated sampling/roots/elicitation removed), currently a weekly-moving BETA (latest 4.0.0b3,
2026-08-14; no RC). Adopting 3.x now does NOT strand lore — 3.4.7 shipped four days AFTER 4.0.0b3, the
3.x line is actively maintained *(4.0-scout §5, §6)*.

**Mint a future packet: "fastmcp 4.x / mcp v2 migration"** (design-first), sequenced in wave S or
later. **Re-open trigger (compound):** the FIRST off-fleet / hosted consumer of lore (the same
trigger the CLAUDE.md pre-production clause names), OR lore specifically wanting a 4.0-only feature
(protocol-level background tasks SEP-2663, or stateless `UserSession` state) *(4.0-scout §6)*. Note
for that later packet: lore uses NO server→client back-channel (no `ctx.sample`/`elicit`/roots —
grepped) *(blast-radius §7.4)*, so its 4.x surface is mostly renames + httpx2/error-code/`mode="auto"`
shifts — a documented migration, not a reverse-engineering exercise.

---

## 9. Adversarial self-attack — what would ship this packet FALSE-GREEN?

Per the Opus-author rule, I attacked my own design. Each is a wrong build that passes a naive gate,
with the pin that catches it (all folded into §6).

- **FG1 — the in-memory-transport blind spot (the #131/#139 class, the biggest risk).** Tests that
  drive the server via the in-memory transport NEVER run the ASGI lifespan (§5b-C2) — whether the
  lifespan is entered by the deleted interceptor (KEEP branch) or by fastmcp's native once-per-process
  `lifespan=` (DELETE branch), an in-memory test skips it — so "session-manager-not-initialised" (the
  server serves NOTHING in the container) passes the whole suite green. This is doubly load-bearing now
  that §5b-C2 DELETEs the eager interceptor and RELIES on fastmcp's lifespan actually running. **Catch:**
  §6.1 in-image conformance + §6.2 REAL uvicorn wire smoke + the §6.6-1 gate. A migration that proves
  itself only on in-memory transport has proven nothing about the deployed artifact.
- **FG2 — funnel-coverage silently narrows.** The subclass funnelled EVERY tool "by construction";
  `on_call_tool` middleware coverage is now a REACH variable. If it fires for built-ins but not for
  `add_tool`-registered extension tools, extension calls produce no trace rows — invisible unless a
  test calls an extension tool over the wire. **Catch:** §6.2 traces BOTH a built-in and an extension
  tool. (The instrument-lesson reach attack: coverage is a CHECKED variable, not a hidden constant.)
- **FG3 — the cancellation/`ok`-latch is dropped in the rewrite.** A cancelled dispatch recorded as
  `ok=True` corrupts the numerator the instrument exists to produce; a lost shield hangs a dying
  request. Invisible because no test cancels mid-dispatch. **Catch:** §6.3 — the cancellation +
  `ok`-latch pins are re-authored (NOT deleted) and mutation-proven.
- **FG4 — `serverInfo.version` silently reverts to the SDK's** if `version=` is misspelled/ignored.
  Invisible because no in-memory test reads serverInfo over the wire. **Catch:** §6.2 reads it.
- **FG5 — the DUAL trap: the contract is written for the fastmcp world and nothing checks the old
  world's virtues survived.** This is the packet's central risk-of-process. **Catch:** §5 removed-
  behaviour inventory + the contract-adversary's deleted-code enumeration; every behaviour has a
  discriminating pin or a ruled DROP.
- **FG6 — "Origin/Bearer unchanged" assumed, not proven.** The `Bearer(Origin(app))` order must hold
  after `http_app`. **Catch:** §6.2 in-image auth suite (401/403), composition-order pin.
- **FG7 — the P2/P13 accessor-shape guess is wrong.** `MiddlewareContext.fastmcp_context` /
  `get_http_request()` may surface the AppContext/headers differently than `request_ctx.get()`. If
  the trace emitter reads the wrong shape it silently no-ops (B5/B6/B7). **Catch:** §6.2 asserts real
  trace rows with correct identity/correlator; and the contract VERIFIES the accessor against
  installed 3.x source before pinning (never from this doc — §0 scope).
- **FG8 — the transport mode silently changes** (fastmcp `http_app` default vs today's stateful). A
  stateless default would change session semantics under the local deploy. **Catch:** §5b-C6 sets the
  mode explicitly + pins it matches pre-migration.

**The receding-reach STOP-rule (CLAUDE.md instrument lesson):** if a contract-adversary round on the
funnel-∀ (B1/FG2) just relocates the coverage gap one registration-path deeper each round, accept a
pinned bound with a named re-open trigger rather than spiralling — this substrate has a small,
enumerable registration-path set (`tool` + `add_tool`), so a ∀ over both is the achievable safe-set.

---

## 10. Packages & DRY

**Packages considered:** `fastmcp` (`>=3.4,<4`) — verdict **replace** the façade class (`mcp.server.fastmcp.FastMCP`
→ `fastmcp.FastMCP`) and **keep** `mcp` for protocol types (`fastmcp` re-uses `mcp.types`; `fastmcp-slim`
pins `mcp<2.0`). Read: the spike read fastmcp 3.4.7 installed source (`inspect.getsource`); the
contract re-reads at build. This IS the packages-over-hand-rolling rule working: `TracingFastMCP`
hand-rolled a trace funnel BECAUSE `mcp` exposed no middleware; `fastmcp` now DOES, so the bespoke
subclass retires (M3). **DRY:** the trace WRITE policy stays ONE function (`_record_tool_trace`,
REUSED — M4); no second emission path. The `on_call_tool` trace middleware is a NEW reusable symbol —
the build's DRY ledger must show the lore search proving no existing trace-middleware exists (there is
none today; `TracingFastMCP` is the sole trace seam) and that `_record_tool_trace` is reused, not
re-implemented.

---

## 11. Decisions — RULED (operator, 2026-08-15)

All four forks below were escalated in the first draft and are now RULED. The build implements the
rulings; it does not re-open them.

- **D1 — Deploy posture. RULED: STANDALONE.** This packet DEPLOYS (rebuild+recreate + the in-image
  gate §6.1), not commit-only. The substrate swap is the surface most likely to break subtly on the
  wire (lifespan, session manager, transport mode); proving it in isolation — not co-mingled with 39's
  auth diff — is the #131/#139-safe path, and pre-production status pre-authorizes the deploy. Cost:
  one rebuild+recreate (budget the #355 re-embed risk — a docs-heavy commit crosses the drift
  threshold; a code-only migration commit likely does not, but verify via the served surface without
  waiting).
- **D2 — Slot. RULED: BUILD NOW, ahead of the wave-D queue** — packet 59 is the IMMEDIATE NEXT BUILD.
  (This satisfies and exceeds the draft recommendation to land before 54; the packet is independent —
  touches only `server.py` + deps.) The INDEX row status marks it immediate-next-build; its table
  position (before 39) records the hard sequencing constraint.
- **D3 — Packet 39's INDEX `Depends on` cell. RULED: YES, it gains `59`** (`45, 48, 49` → `45, 48, 49,
  59`). The LEAD makes that one-cell edit on commit (39's row is outside this packet's writable set).
- **D4 — `mcp` dependency. RULED: `mcp` rides TRANSITIVELY** ("let it ride") — REPLACE
  `"mcp[cli]>=1.27"` with `"fastmcp>=3.4,<4"`; `mcp` arrives via `fastmcp-slim`'s `mcp<2.0,>=1.24.0`
  pin, undeclared directly (§3 packaging). Two BUILD-TIME verification caveats the build MUST
  discharge:
  - **(a) the transitive pin is BARE `mcp` (NO `[cli]` extra).** CONFIRM lore imports nothing needing
    mcp's `[cli]` deps (grep prod imports for `mcp.cli` / `mcp.server.fastmcp.cli` / any CLI helper);
    if anything is reached, re-add `"mcp[cli]"` explicitly.
  - **(b) `mcp.types` is now an UNDECLARED direct import** (lore imports `ContentBlock`/`ToolAnnotations`
    directly while `mcp` is only transitive) — **operator-ACCEPTED**; noted so a future dependency
    audit does not re-raise it.
  - The 11 packet-39 pending-contract test files import `mcp.server.fastmcp` / `mcp.server.auth.*`
    (blast-radius §1b) — committed-RED, adjudicated `packet-39-pending-build`. They still COLLECT
    because `mcp` is still INSTALLED (transitively). **Run the FULL collection once to confirm
    zero-new-delta vs #333** (a ruled-RED must not become an ImportError).

---

## 12. Bounds of this design (what I did NOT measure)

- **The exact fastmcp 3.x accessor shapes** (P2/P13 AppContext + headers under middleware; P9 tool
  registry; **P14 `Context` INJECTION** — a tool wrapper param annotated `Context` gets the context
  injected: `_extension_tool_wrapper` relies on this, and fastmcp 3.x's injection mechanism must be
  confirmed still annotation-based, not `Depends()`-based as in 4.0) are from the receipts' pypi/docs
  pass + the spike's middleware read, NOT a fresh introspection at THIS HEAD. The contract MUST read
  installed 3.x source before pinning (§0 scope, FG7). I assert the SEAM exists (spike-measured); I do
  not assert the exact attribute path.
- **The `_EagerStartupLifespan` ↔ `http_app()` lifespan wiring** (C2) is reasoned from both docstrings,
  not built. It is the highest wire-risk item; the build proves it via §6.2, not this doc.
- **The two spike bounds (§6.4)** are UNMEASURED by design — carried, not closed.
- **Size/split** — I estimate ~0.25–0.30 wu (one file + two re-authored test modules + middleware +
  re-lock + image + two gates). If it measures ≥0.30 at kickoff, split per the sizing law (e.g. façade
  swap + trace-middleware as 59; the deploy + in-image gate as 59a). The lead sizes at kickoff.

---

## 13. INDEX row

The packet-59 row is ADDED LIVE to `docs/plans/v2/INDEX.md`'s Sequence + status table, placed just
before packet 39 (the hard sequencing constraint), and updated in place with the D1–D4 rulings
(STANDALONE deploy · IMMEDIATE NEXT BUILD · `mcp` transitive · 39's `Depends on` gains `59`, lead
edits 39's row on commit). `INDEX.md` is the canonical location; this section does not duplicate the
row text, to avoid drift.

_All facts read/measured 2026-08-15 at HEAD `41287c5`. fastmcp API details re-verify against
installed 3.x source at contract time (§0)._
