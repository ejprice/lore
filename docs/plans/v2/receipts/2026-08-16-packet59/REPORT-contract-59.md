# REPORT-contract-59 — tdd Phase-1 CONTRACT for packet 59 (fastmcp 3.x migration)

> ⚠ **CORRECTION (lead-59, 2026-08-16) — SUPERSEDED in part by `REPORT-contract-59b.md`.**
> The §0 "FIVE couplings #1" claim that unfixed `Context[...]` causes a **module-LOAD break**
> (`loremaster.server` fails to IMPORT) is **FALSE** (#107-class): `server.py` has
> `from __future__ import annotations` (PEP-563), so the import SUCCEEDS and the `TypeError`
> fires at **tool REGISTRATION** inside `build_mcp_server`. The discriminating fixture still
> catches it; only the wording was wrong. Corrected in `REPORT-contract-59b.md` + the contract
> docstrings. The adversary pass-1 record: `REPORT-adversary-59.md` finding ④.

brief-base v14 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4 — first thing)
- **Demanded vs. have:** the brief needs `uv` (present) + network to introspect `fastmcp>=3.4,<4`
  ephemerally (worked — ephemeral introspection is authorized, fastmcp is NOT yet a lore dep);
  the lore tools (loaded via `ToolSearch "+lore"`); write access to `loremaster/tests/` +
  `REPORT-contract-59.md` (all writable); and READ access to `server.py`/`auth.py`/the design/spike
  (all readable via lore + Read). **Nothing was un-satisfiable — the mission ran end to end.** No
  blocker.
- **One scope note (not a blocker):** two couplings the contract must PIN live in files OUTSIDE my
  writable set — the ~16 `Context[Any, AppContext, Any]` sites + `add_tool` call site in
  `server.py` (PRODUCTION), and `_auth_fixtures.py::stub_heavy_startup`. I do NOT edit them; I PIN
  their required outcomes and FLAG them for the build (§Couplings, decisions-needed).
- **Model attestation (brief-carried, I cannot self-read):** `claude-opus-4-8` (Opus 4.8), pinned
  via the `opus48-worker` definition. `$CLAUDE_CODE_SUBAGENT_MODEL=claude-opus-4-8` corroborates.
  Repo law: contract authors are Opus 4.8. ✓

## SUMMARY BLOCK
- state: **done — PAUSES for operator review, then contract-adversary** (no stub/build).
- deviations:
  - `test_trace_telemetry.py` re-authored by SURGICAL EXCISION (funnel pins → File 1), not rewrite —
    verified by ast.parse + ruff + orphan-grep (can't green-run: RED depends on the dep swap).
  - The §6.2 wire pins + the once-per-process pin are **specified-not-runnable** placeholders
    (require a build-provided real-uvicorn `migration_wire` fixture, per design §6.2/FG1) — kept as
    explicit skips, never silently absent.
- Packages considered: **`fastmcp` (`>=3.4,<4`, introspected 3.4.7)** — verdict **replace** the
  façade (`mcp.server.fastmcp.FastMCP` → `fastmcp.FastMCP`) / **keep `mcp` transitive** for
  `mcp.types` (fastmcp-slim pins `mcp<2.0`). Full survey table below. READ: installed 3.4.7 source
  via `inspect` + an empirical wire probe (both pasted verbatim in §Instruments).
- Reuse ledger: **11 new test symbols, all dispositioned** (DRY ledger below) — a re-homed
  `_TraceRecorder` (MOVED, not cloned), new middleware-drive harness (HAND-ROLLED, no prior
  middleware seam existed), REUSED `_extension_helpers` (`CollidingExtension`/`CounterExtension`) +
  `_surreal_harness`.
- Graded (the fastmcp-fact measurements this contract rests on): `ee4bced` · HEAD-at-report:
  `ee4bced` · **SAME**. (Design authored at `41287c5`; only docs + the spike harness `scripts/`
  committed `41287c5..ee4bced` — no `server.py`/`auth.py`/`pyproject` drift, so the coupling sites
  are unchanged at my measurement HEAD.)
- decisions-needed (surfaced for the OPERATOR review — do NOT self-resolve, per tdd law):
  1. **P9 collision policy** — recommend PUBLIC/sync registry check + KEEP the universe check;
     `on_duplicate="error"` ALONE is insufficient (misses the disabled-built-in-name reservation).
  2. **`test_wire_discipline.py` fate** — recommend delete-with-superseded-header (implemented as a
     tombstone); alternative is an immediate rewrite (premature — 39's posture modules don't exist).
  3. **5 under-specified couplings** the design P-table omits (esp. the `Context[...]` module-load
     break + `stub_heavy_startup` reaching the deleted guard) — build scope items to confirm.
- receipt POINTERS:
  - Contract files: `loremaster/tests/test_fastmcp_migration.py` (NEW, 36 pins),
    `test_trace_telemetry.py` (re-authored 3455→1524), `test_wire_discipline.py` (tombstone).
  - fastmcp verification: §"fastmcp 3.x verification" + §Instruments (probe + verbatim output).
  - The DUAL adjudication + ∀-vs-GUARDED + realism checklist: §tables below.

---

## The two contract files' shape (what pins what)

**`test_fastmcp_migration.py` (NEW) — the migration contract, 36 pins / 19 classes:**
- SECTION A — the migration LOADS + BUILDS (catches the `Context[...]` module-load break; all 15
  built-ins register; `mcp` stays importable transitively).
- SECTION B — the trace FUNNEL re-homed onto an `on_call_tool` middleware (design §5a B1–B8): the
  middleware is installed at the ONE site (D7 + mutation obligation); one row per dispatch; outcome
  always wins (B2); latency present/bounded + constant-killer (B8); ordinal never client-minted;
  failure-swallow + loud structured log (B2); degrade-with-no-store no-op (B5) + un-wired WARN (B6);
  ok-latch on cancellation (B3, asyncio KNOWN BOUND) + the discriminating anyio-scope shield pin
  (B4) + bounded; declared-identity str-only / all-or-nothing / non-str (B7); the params-hash ruled
  recipe + hostile-body-only-as-digest (T6 + tdd clause 6); the real-store W30/W33 land-a-row legs.
- SECTION C — the lifespan-apparatus DELETE + once-per-process property (C2/M11/Item-1): the
  `_ProcessLifespanGuard`/`_EagerStartupLifespan` PIN-THE-DELETE; the once-per-process wire gate.
- SECTION D — serverInfo.version = `_resolve_version()` (D4/FG4).
- SECTION E — the P9 name-collision guard (both legs: registered built-in AND **disabled**-built-in
  name); D6 extension registers + `readOnlyHint=False` (the `add_tool` adaptation).
- SECTION F — the WIRE + host_origin_protection + auth gates (§6.1/§6.2/§5b — specified as the
  `migration_wire` real-uvicorn fixture the build provides; assertions in each class docstring).
- SECTION G — PIN-THE-MISS: the two spike bounds carried, not closed (§6.4).

**`test_trace_telemetry.py` (re-authored) — the trace-store WRITE POLICY (M4-UNCHANGED):** the
funnel pins were EXCISED (re-homed to File 1); what stays is the `trace` table schema delta + dirty
migration (T2/T2.1), the native sequence + store-side ordinal (T3), the `record_trace` signature
(T8), the windowed aggregate + per-tool cap (DD-1.b), the monotonicity/index-parser controls, and
the no-prod-prose-teaches-the-retired-plan scan. The retired MCP imports (`mcp.server.fastmcp`,
`request_ctx`, `RequestContext`, the funnel `mcp.types` set) were removed by the excision (ruff
--fix); the stale module docstring was rewritten; 21 orphaned funnel constants removed.

**`test_wire_discipline.py` (re-authored) — SUPERSEDED-HEADER TOMBSTONE:** its `_setup_handlers`
construction-binding premise dissolves under fastmcp middleware (design §4/§7); packet 39
re-expresses the wire-only discipline over the middleware substrate. Retains one anti-regression pin
(TracingFastMCP stays retired) + a documented hand-off placeholder.

---

## fastmcp 3.x verification (§0 SCOPE RULE — EVERY fact re-verified against installed 3.4.7 source)

Method (per the #107 read-then-verify law): each fact was READ from installed 3.4.7 source
(`inspect.getsource`/`inspect.signature`) AND confirmed empirically with an in-process wire probe.
Full receipts pasted verbatim in §Instruments. The load-bearing confirmations:

| fact (design ref) | verified result |
|---|---|
| `from fastmcp import FastMCP, Context` · `from fastmcp.exceptions import ToolError` (P1) | ✓ `fastmcp.server.server.FastMCP`, `fastmcp.server.context.Context`; ToolError MRO → FastMCPError → Exception → BaseException |
| `FastMCP.__init__` kwargs (P6/P7/D1/D4) | ✓ takes `version=`/`lifespan=`/`middleware=`/`auth=`/`on_duplicate=`; **NO** `host`/`port`/`streamable_http_path` |
| `FastMCP.http_app(path, stateless_http, host_origin_protection, allowed_hosts, allowed_origins)` (C1) | ✓ **no** `streamable_http_app` method exists (`hasattr → False`) |
| `mcp._tool_manager` GONE → `_local_provider` (P9) | ✓ `hasattr _tool_manager → False`, `_local_provider → True`; public `get_tool` is **async** → `await mcp.get_tool(name) is not None` |
| `on_duplicate` ctor param (P9 native) | ✓ present, `DuplicateBehavior \| None`, default None |
| `Middleware.on_call_tool` / `on_list_tools` hooks (P4/P5) | ✓ `on_call_tool(ctx: MiddlewareContext[CallToolRequestParams], call_next) -> ToolResult`; `mcp.middleware` is a public list (already carries a built-in `DereferenceRefsMiddleware`) |
| `MiddlewareContext` shape (P2/P13) | ✓ `message` (has `.name`/`.arguments`) + `fastmcp_context: Context \| None` |
| **P14 Context injection** | ✓ ANNOTATION-based — a `context: Context` param is injected; confirmed on the WIRE for a built-in AND an `add_tool` extension tool |
| lifespan accessor (B5, `_app_context`) | ✓ `context.request_context.lifespan_context` yields the lifespan value → `_app_context`'s BODY is unchanged; middleware reaches it via `context.fastmcp_context.request_context.lifespan_context` (both accessors measured) |
| headers/token (B7/§6.4) | ✓ `fastmcp.server.dependencies.get_http_headers()` / `get_access_token()` present |
| serverInfo.version (D4) | ✓ `serverInfo.version` == the ctor `version=` (measured over the wire) |
| host_origin_protection default (Item 3 rider) | ✓ default OFF (`settings.http_host_origin_protection == False`, `create_streamable_http_app` param default `False`) |

### ⚠ FIVE couplings the design P-table UNDER-SPECIFIES (measured — the highest-value findings)
1. **`Context[Any, AppContext, Any]` is NOT subscriptable in fastmcp** — `TypeError: type 'Context'
   is not subscriptable`. All **15 built-ins** + `_app_context` + `_extension_tool_wrapper` annotate
   it, so `loremaster.server` **fails to IMPORT** — a module-LOAD break the design's mechanical
   P-table (only import lines + the façade class) does not cover. The build MUST change every
   `Context[...]` → bare `Context`. **PROD change, ~16 sites.** Pinned by
   `TestTheMigratedServerImportsAndBuilds` (build succeeds + all 15 register).
2. **`add_tool(self, tool)` is single-arg** in fastmcp — `_register_extension_tools`'s
   `mcp.add_tool(wrapper, name=…, description=…, annotations=ToolAnnotations(readOnlyHint=False))`
   breaks (TypeError). Adapt via `mcp.tool(name=…, description=…, annotations=…)(wrapper)` (probed
   working). Pinned by the D6 extension-registration pins (outcome: registers + `readOnlyHint=False`).
3. **`_auth_fixtures.stub_heavy_startup` reaches `mcp._lore_eager_guard._build`** — which the Item-1
   lifespan DELETE removes. Every `wire_session`-based pin (incl. the 11 packet-39 pending files and
   the posture suite) breaks unless the build updates this SHARED harness. **OUTSIDE my writable
   set — FLAGGED for the build.** (The build's Item-1 DELETE must supply a new stub-the-lifespan hook.)
4. **The P9 collision check is SYNC** — `_register_extension_tools` is a `def` (sync); fastmcp's
   public `get_tool` is `async`. The build needs a sync path (a local registered-names set) and MUST
   keep the `_ALL_BUILTIN_TOOL_NAMES` universe check (see decision 1).
5. **`_record_tool_trace` is a METHOD on the deleted `TracingFastMCP`** (`self._record_tool_trace`).
   M4 preserves the WRITE POLICY (identity rules, ordinal mint, correlator, failure posture), but its
   HOME moves (to the middleware or module-level) and its store/headers accessors change
   (`request_ctx.get()` → `context.fastmcp_context…`; `request.headers` → `get_http_headers()`), as
   design B5/B7 flag. The contract pins the write-policy OUTPUT (params_hash recipe, str-only
   identity, ok latch), not the home.

*Good news (no design change needed):* `_app_context`'s **body** (`context.request_context
.lifespan_context`) works unchanged under fastmcp — only its `Context[...]` annotation must change.

---

## PACKAGE SURVEY (tdd-contract required output)

| mechanism | libraries evaluated (name + version) | what I READ | verdict |
|---|---|---|---|
| MCP server façade | `fastmcp` 3.4.7 vs `mcp.server.fastmcp` (`mcp` 1.27.2 live / 1.29.0 fresh-resolve) | installed 3.4.7 `FastMCP.__init__`/`http_app`/`get_tool` signatures + the empirical wire probe | **replace** the façade class (`fastmcp.FastMCP`); the bespoke `TracingFastMCP` subclass retires because fastmcp NOW exposes middleware (the exact gap `TracingFastMCP` hand-rolled around) |
| wire-protocol types | `mcp.types` (transitive via `fastmcp-slim`'s `mcp<2.0,>=1.24`) | design §2/§3 + fastmcp-slim pin; `mcp.types` imports byte-identical | **keep_with_trigger** — re-open when the first off-fleet consumer or fastmcp 4.x/mcp-v2 lands (§8) |
| trace funnel | fastmcp `Middleware.on_call_tool` vs the retired `FastMCP.call_tool` subclass override | `inspect.getsource(Middleware.on_call_tool)` + the wire probe (middleware fires for built-in AND extension) | **replace** — the subclass is bespoke machinery the package now provides (M3); the WRITE policy (`_record_tool_trace`) is **kept** unchanged (M4) |
| ASGI lifespan (tests) | `asgi_lifespan.LifespanManager` (already in `dev`) via `_auth_fixtures.running_asgi_app` | `_auth_fixtures.py:550` (already a package, not hand-rolled) | **keep** — reuse the existing `running_asgi_app`; do NOT hand-roll a lifespan runner |
| lifespan once-per-process | fastmcp native `_lifespan_manager` ref-count vs the bespoke `_ProcessLifespanGuard` | `inspect.getsource(FastMCP._lifespan_manager)` (spike §Source) + Item-1 GO | **replace** — fastmcp's ref-counted `lifespan=` obviates the ~150-LOC guard (M11/C2) |
| Host/DNS-rebinding guard | fastmcp `host_origin_protection` (`HostOriginGuardMiddleware`) — `transport_security` is UNSET today | `inspect.getsource(HostOriginGuardMiddleware.__call__)` + Item-3 GO (spoofed Host→421) | **replace/adopt** (a security BENEFIT the migration banks; C3′) |

*The contract specifies NO numeric mechanism (this is a substrate swap, not a computation), so the
realism clause 4 magnitude-bound is "not applicable, pure protocol/wire logic".*

---

## Adversarial pre-flight (every realistic breaker → covered or scoped-out)

| breaker | covered by |
|---|---|
| module-LOAD break (`Context[...]` subscript) — everything downstream assumes the module imported | `TestTheMigratedServerImportsAndBuilds` (build succeeds + 15 register) — the FIRST gate |
| funnel silently narrows (fires for built-ins, not `add_tool` extensions) — FG2 | wire smoke traces a built-in AND an extension tool (Section F) + D6 registers an extension |
| in-memory transport blind spot (server serves nothing in the container) — FG1 | §6.1 in-image conformance + §6.2 real-uvicorn `migration_wire` (skips are explicit) |
| cancelled dispatch recorded `ok=True` (corrupts the numerator) — FG3 | ok-latch pin (asyncio KNOWN BOUND) + the anyio-scope shield pin + positive control |
| shield dropped → dying request hangs, or timed-out population lost | the anyio-scope pin (mutation obligation: drop shield → RED) + the bounded-timeout constant pin |
| trace-write failure surfaces to the caller (couples the tool surface to telemetry) — B2 | failure-swallow pin + loud-structured-log + positive control (healthy store writes) |
| accessor-shape guess wrong (silent no-op) — FG7 | accessor VERIFIED against installed source; the real-store W30/W33 land-a-row legs assert a real row |
| version reverts to the SDK's — FG4 | §6.2 reads serverInfo.version over the wire == `_resolve_version()` |
| Origin/Bearer order changed, or a layer lost — FG6 | §6.2 auth gate (bad token→401, bad Origin→403, order) |
| transport mode silently stateless — FG8 | §6.2 asserts an mcp-session-id is minted (stateful) |
| `on_duplicate='error'` misses the disabled-built-in-name reservation (packet-45 hole) | the DISCRIMINATING P9 leg (disabled built-in name still refused) |
| params_hash stores raw free text (row forgery) | the hostile-body pin (newlines + forgery line + backtick run; no fragment in the row) |
| `_query`/store-shape mismatch in the real-row read-back | `_read_trace_rows` is a best-effort read — **build-verify item** (align with the kept `_trace_rows`) |

Every entry is a case or a scoped-out note. No realistic breaker is un-enumerated.

---

## ∀-vs-GUARDED table (every load-bearing invariant + the wrong build it kills)

| invariant | property it pins | ∀ or GUARDED | fixture forcing each fate | wrong build it kills |
|---|---|---|---|---|
| B1 one-row-per-dispatch | funnel emits exactly one row | ∀ over outcome (return/raise) unit; ∀ over registration-path (built-in/extension) = WIRE gate | returning + raising `call_next`; wire built-in + extension | per-wrapper emission that misses `add_tool` tools; a plain FastMCP (no middleware) |
| B2 outcome-wins + swallow | tool result/error survives; write-fail invisible+loud | ∀ (success + raise + broken-store) | `_ok`/`_raise` call_next; `_TraceRecorder(failure=…)` + positive control | a build that fails the call on a trace-write error, or swallows silently |
| B3 ok-latch | ok True iff dispatch RETURNED | ∀ over 3 fates | return→True, raise→False, cancel→False | `except Exception` clearing an ok=True flag (CancelledError walks past) |
| B4 shield | write survives level-triggered cancel, bounded | GUARDED→discriminating: needs a SUSPENDING recorder + anyio scope | `_SuspendingTraceRecorder` + `move_on_after` + positive control | an unshielded emission (loses the timed-out population); an unbounded shield |
| B5/B6 degrade | no-store no-op vs un-wired WARN | ∀ over 2 states | `fastmcp_context=None` (B5) vs no-`write_store` (B6) | an emission that crashes the tool when the store is unreachable; a silent un-wired emission |
| B7 identity | recorded only for str, per-key | ∀ over 3 fates | all-3-str, agent-only, int-agent | a build harvesting keys all-or-nothing, or minting an identity from a non-str |
| B8 latency | around call_next, real | GUARDED (bracket) + ∀ (difference) | slow call_next + two-durations-differ | a constant latency (killed by the difference pin at any fixture value) |
| T6 params_hash | ruled sha256 recipe; free text as digest only | ∀ (oracle + hostile) | hostile body; independent recipe | a build storing args verbatim/prefixed, or a different digest recipe |
| P9 collision | refuse registered AND disabled-name | ∀ over 2 legs | enabled `lore_search` + DISABLED `lore_search` | `on_duplicate='error'` alone (passes leg 1, fails leg 2) |
| Context-import | module loads + 15 register | ∀ over the 15 | set-membership over the 15 built-ins | the `Context[...]` subscript break (module fails to import) |
| D7 install | trace middleware at the ONE site | count == 1 (not len==1; a built-in mw already exists) | isinstance count over `mcp.middleware` | a build that defines but never installs the middleware |

Every GUARDED row is either promoted to ∀ or names the discriminating sibling (B4's anyio pin,
B8's difference pin).

---

## §5 DUAL removed-behaviour inventory — adjudication (every B/C/D item → verdict)

| # | behaviour | verdict | pin (or ruling) |
|---|---|---|---|
| B1 | one trace row per dispatch, funnel ∀ | PRESERVE+PIN | `TestTheMigratedFunnelRecordsOneRowPerDispatch` + wire ∀ (Section F) |
| B2 | outcome wins; trace-fail invisible+loud | PRESERVE+PIN | `TestTheToolsOutcomeAlwaysWins` + `TestATraceWriteFailureNeverTouchesTheCall` |
| B3 | ok latch (no except arm) | PRESERVE+PIN | `TestTheCancelledDispatchIsRecordedOkFalse` (ok-latch legs) |
| B4 | shielded + bounded `finally` | PRESERVE+PIN (VERBATIM mechanism) | `TestTheEmissionSurvivesAnyioLevelTriggeredCancellation` (+ mutation obligation + bound) |
| B5 | no reachable store ⇒ no-op | PRESERVE+PIN (mechanism CHANGES) | `TestTheEmissionDegradesWhenNoStoreIsReachable::…no_op` |
| B6 | un-wired store ⇒ WARNING | PRESERVE+PIN | `…::an_un_wired_store_warns_loudly` |
| B7 | declared str-only identity + correlator | PRESERVE+PIN (mechanism CHANGES) | `TestIdentityIsDeclaredNeverGuessed` (+ correlator = wire) |
| B8 | latency around dispatch | PRESERVE+PIN | `TestTheToolsOutcomeAlwaysWins::…latency` + difference pin |
| C1 | `streamable_http_app()` at path | REPLACE | `http_app(path=…)`; wire smoke serves at the path (Section F) |
| C2 | process-lifespan guard + eager | **DELETE ~150 LOC** (Item-1 GO), property preserved | `TestTheHeavyBuildRunsOncePerProcessEagerly` (deleted-apparatus-gone + once-per-process wire gate) |
| C3 | bespoke Origin guard | PRESERVE (bespoke) | wire host-origin gate (bad Origin→403, absent allowed) |
| C3′ | `host_origin_protection` (Host/DNS-rebinding) | **MIGRATION BENEFIT** (Item-3 GO) | wire gate: spoofed Host→421 ON, accepted OFF, legit proxied Host→200 (the config rider) |
| C4 | Bearer outermost when auth.enabled | PRESERVE (39 replaces later) | wire auth gate (bad token→401, order) |
| C5 | stateful transport mode | PRESERVE+PIN EXPLICITLY | wire gate asserts an mcp-session-id is minted (FG8) |
| D1 | name/instructions/lifespan ctor | PRESERVE | build succeeds (Section A) |
| D2 | host/port | VERIFY+REPOINT (uvicorn call site) | build succeeds proves the ctor rejects host/port; uvicorn bind = wire smoke |
| D3 | streamable_http_path → http_app(path=) | MOVE | (C1) |
| D4 | version ctor kwarg | PRESERVE | `TestTheServedVersionIsLoresResolvedVersion` + wire read |
| D5 | `_lore_eager_guard` attr | DELETE with the guard | `test_the_deleted_apparatus_is_gone` (guard classes) |
| D6 | register 15 built-ins + extension tools | PRESERVE+PIN | `TestTheMigratedServerImportsAndBuilds` + `TestExtensionToolsRegisterAndAreCallable` |
| D7 | ONE construction site = the tracing seam | REWRITE (now "installs the middleware") | `TestTheTraceMiddlewareIsInstalledAtTheOneFunnel` (+ mutation obligation) |

### DELIBERATE DROPs (verdict 2 — retired, with reason)
- `TracingFastMCP` subclass + `call_tool` override → the package now provides middleware (M3); re-homed.
- `_ProcessLifespanGuard` + `_EagerStartupLifespan` + `_lore_eager_guard` → fastmcp's once-per-process
  `lifespan=` obviates them (M11/C2, Item-1 GO); the DELETE also retires the guard's **silent-failure
  mode** (a drifted lease spawning a 2nd watcher) — an OLD-BUG, NOT re-pinned.
- `request_ctx` ContextVar access → replaced by `context.fastmcp_context` (B5).
- `streamable_http_app()` → `http_app(path=…)` (C1). `mcp._tool_manager.get_tool` → public/sync (P9).
  `mcp._mcp_server.version` private reach → ctor `version=` (D4).
- `test_trace_telemetry.py`'s funnel pins → re-homed to `test_fastmcp_migration.py`.
- `test_wire_discipline.py`'s `_setup_handlers`-derived invariant → tombstoned; 39 re-expresses.

### OLD-BUG / KNOWN-LIMITATION (verdict 3 — NOT re-pinned)
- `transport_security` UNSET (the Host/DNS-rebinding gap) → an old LIMITATION the migration CLOSES
  (C3′/Item-3); not re-pinned as a bug — the Item-3 gate pins the FIX.
- The `_ProcessLifespanGuard` drifted-lease silent 2nd watcher → accidental complexity removed by the
  DELETE; not re-pinned.

### SPEC-SILENT — operator ruling required (verdict 4)
- **Whether to KEEP a defense-in-depth bespoke Origin layer** now that fastmcp's `host_origin_protection`
  runs BEFORE the verifier natively (Item-2 GO). The design §5b caveat explicitly defers this ("a
  keep-for-defense-in-depth choice is a separate design call"). The spike proves it is NOT structurally
  REQUIRED for the R9 ordering. The design C3 currently PRESERVES the bespoke Origin (for the Origin
  allow-list); C3′ ADDS fastmcp's (for Host). Whether both coexist or the bespoke Origin dedups once
  fastmcp does Origin too is a design call → **surface to operator / packet 39.** (My wire gate pins
  the OUTCOMES — bad Origin→403, spoofed Host→421 — under either arrangement.)

---

## The realism-&-independence checklist (each item, per tdd-contract)

1. **Production-realistic inputs** ☑ — real tool names (`lore_search`/`lore_comms`), the real
   `SurrealStore.record_trace` signature (bound), the real `_extension_helpers` Extensions, a real
   TEST store (`ws://127.0.0.1:18000`), a hostile free-text body with a row-shaped forgery line.
2. **Independent expected values** ☑ — params_hash re-derived from the ruled recipe (oracle, not the
   impl's formula); the 15-tool set enumerated from the served surface; `_resolve_version()` compared
   to the wire, not to itself.
3. **Seam / boundary coverage** ☑ — the real seam under test is the MIDDLEWARE→store handoff; the
   W30/W33 legs drive a REAL store so a bad kwarg RAISES (not swallowed by a `**fields` double); the
   `MiddlewareContext.fastmcp_context.request_context.lifespan_context` accessor is the verified seam.
4. **Magnitude / sanity bound** ☐ not applicable — pure protocol/wire logic (no derived numeric
   output); latency has a >= sleep bound + a difference bound (the constant-killer), which is the
   relevant sanity guard.
5. **Shared domain conventions** ☑ — the `record_trace` signature is READ from the production class
   (not transcribed); the timeout bound is compared against `_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS`
   (the shared retry deadline); the 15-tool set is the served surface, not a magic list.
6. **Hostile fixtures for rendered stored text** ☑ — `TestParamsHashCarriesFreeTextOnlyAsADigest`
   (newlines + a forgery line + a backtick run; asserts NO fragment reaches any stored field).
7. **Input accounting (totality)** ☐ not applicable — the middleware transforms ONE dispatch at a
   time, not a caller-supplied collection; the funnel-∀ (every registered tool traces) is the
   nearest totality property and is a CHECKED variable (set-equality over the served surface + the
   wire built-in/extension legs).

---

## DRY ledger (brief-base §6 — one row per new reusable symbol)

| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_TraceRecorder` (File 1) | it MOVED from `test_trace_telemetry.py` (deleted there) | the signature-binding write_store double | **EXTENDED/MOVED** — re-homed with the funnel; NOT a clone (original deleted) |
| `_SuspendingTraceRecorder` | moved with `_TraceRecorder` | the suspending variant for the shield pin | MOVED |
| `_config` (File 1) | `lore_search "minimal LoreConfig test fixture builder"` → `_extension_helpers.minimal_config`, `_auth_fixtures.base_config_payload`, `test_trace_telemetry._config` | multiple local config builders exist by design | **HAND-ROLLED** — fixture DATA, not shared policy (the codebase's sanctioned pattern; each suite has a local one) |
| `_trace_middleware_class` / `_make_trace_middleware` / `_drive_on_call_tool` / `_middleware_context` / `_app_context_double` / `_no_store_fastmcp_context` / `_registered_tool_names` / `_read_trace_rows` / `_SENTINEL_RESULT` | `lore_search "on_call_tool middleware test harness fastmcp"` → none (the funnel was subclass-based) | no prior middleware-drive harness | **HAND-ROLLED** — new seam (the retired `_tracing_subclass`/`_request_context`/`_dispatch` were subclass/ContextVar-based); `_read_trace_rows` flagged as a build-verify item (align with the kept `_trace_rows`) |
| (REUSED, no new symbol) | — | `_extension_helpers.CollidingExtension`/`CounterExtension`/`register_extension`; `_surreal_harness.*`; `_auth_fixtures.running_asgi_app`/`wire_session` | **REUSED** — cited in the pins |

*No PRODUCTION symbol introduced (contract writes tests only). The trace WRITE policy
(`_record_tool_trace`, `_trace_params_hash`) is REUSED by the build unchanged (M4) — the contract
tests its OUTPUT, never re-implements it.*

---

## decisions-needed (surfaced for the OPERATOR review — spec ambiguity is a defect, not my call)

1. **P9 collision policy** (design-named fork). RECOMMEND: keep the guard against a PUBLIC/sync
   registry path (a local registered-names set, since `_register_extension_tools` is sync and
   fastmcp's `get_tool` is async) AND keep the `_ALL_BUILTIN_TOOL_NAMES` universe check.
   `on_duplicate="error"` ALONE is INSUFFICIENT — it only sees REGISTERED tools, so it cannot reserve
   a DISABLED built-in's name (packet-45 L2-4). The contract pins BOTH legs; the build picks the sync
   mechanism. → operator confirms.
2. **`test_wire_discipline.py` fate** (design-named fork). RECOMMEND: delete-with-superseded-header
   (implemented as a tombstone) — its `_setup_handlers` referent is gone and packet 39 re-expresses
   the wire-only discipline over the middleware substrate (design §7). Alternative: an immediate
   rewrite — premature (39's posture modules don't exist). → operator confirms.
3. **The 5 under-specified couplings** (§0). Two need explicit build-scope confirmation because they
   touch files OUTSIDE this contract's writable set: (a) the ~16 `Context[...]` sites + the `add_tool`
   call site in `server.py` (PROD); (b) `_auth_fixtures.stub_heavy_startup`'s reach into the deleted
   `_lore_eager_guard`. → confirm the build owns these.
4. **The `migration_wire` fixture** — the §6.2 wire pins + the once-per-process pin are
   specified-not-runnable placeholders (explicit skips) until the build provides a real-uvicorn TCP
   fixture (reusing `scripts/fastmcp_migration_spike.py`, per design §6.2/FG1). This is the ONE part
   of the contract that is specified rather than directly runnable. → confirm the build implements it.
5. **The trace middleware class NAME** (`ToolTraceMiddleware`) — I decided the interface (contract
   author's right); one constant `_TRACE_MIDDLEWARE_NAME` changes it if the build prefers another. →
   FYI, not a fork.

---

## RED depends on the dep swap (per the brief)

These pins import `fastmcp`, which is NOT yet a lore dependency. The BUILD's first step (design §3/D4)
is to add `"fastmcp>=3.4,<4"` to `loremaster/pyproject.toml` and `uv sync`. Until then
`test_fastmcp_migration.py` is UNCOLLECTABLE (import error) — a DIFFERENT state from RED, and the
expected pre-build state. `test_trace_telemetry.py` (re-authored) COLLECTS today (its imports resolve
transitively) and its write-policy pins stay green; the funnel pins that would have RED-for-the-wrong-
reason after the migration were EXCISED, not left. `test_wire_discipline.py` COLLECTS + passes today
(the tombstone pin checks `TracingFastMCP` is absent — true today, and after the migration).

**§6.6 collection gate (the build runs it):** after the dep swap, `pytest --collect-only` must show
zero-new-delta vs #333 — the 11 packet-39 pending files still COLLECT (mcp transitive). A ruled-RED
must not become an ImportError. (`test_fastmcp_migration.py` is NEW and its uncollectable-until-swap
state is expected, not a #333 regression.)

## Verification receipts (what I actually ran — structural, since green-run needs the dep swap)
- `test_fastmcp_migration.py`: `ast.parse` OK · `ruff check` **All checks passed** · 36 pins / 19
  classes / 1246 lines.
- `test_trace_telemetry.py`: `ast.parse` OK · `ruff check` **All checks passed** · re-authored
  3455→1524; excision verified by orphan-grep (no kept pin references a deleted symbol — the only
  residual mentions of `TracingFastMCP`/`request_ctx` are in the rewritten docstring documenting the
  retirement) + no non-Test orphaned symbol remains.
- `test_wire_discipline.py`: `ast.parse` OK · `ruff check` **All checks passed** · tombstone.
- Backup of the pre-excision `test_trace_telemetry.py` at `/tmp/test_trace_telemetry.py.bak-pre-excise`
  (content backup per the mutation-backup law; the file is git-tracked, so a git restore is also
  available — I did NOT mutate git state).

---

## Instruments (brief-base §1 — the load-bearing verification survives)

The §0 facts + the 5 couplings rest on two ephemeral scripts (at `/tmp/fastmcp_introspect_59.py` and
`/tmp/fastmcp_probe_59.py`; disposable). **RECOMMENDATION: the lead commits both to `scripts/`**
alongside `scripts/fastmcp_migration_spike.py`. The load-bearing probe + its verbatim output are
pasted here so the claim survives even if the scripts do not:

### The wire probe (the source that settled the 5 couplings + the accessor confirmations)
```python
# /tmp/fastmcp_probe_59.py — run: uv run --with 'fastmcp>=3.4,<4' --with uvicorn --with httpx python …
# 1. Context[...] subscript:  Context[object, object, object]  -> TypeError
# 2/3. built-in tool: @mcp.tool async def builtin_probe(context: Context, marker: str)  (annotation-injection)
#      returns context.request_context.lifespan_context.marker  and  context.lifespan_context.marker
# 4.  extension tool: a signature-built wrapper (context: Context, **kwargs) registered via
#      mcp.tool(name=…, description=…, annotations=ToolAnnotations(readOnlyHint=False))(wrapper)  [Path A OK]
# 5.  middleware ProbeMW.on_call_tool reads context.message.name/.arguments and
#      context.fastmcp_context.request_context.lifespan_context
# 6.  in-memory Client(mcp) runs the lifespan; 7. serverInfo.version == ctor version=
```

### Verbatim probe output (the receipt)
```
fastmcp 3.4.7
=== 1. Context[...] subscript ===
Context[a,b,c] FAILS -> TypeError("type 'Context' is not subscriptable")
Context[a] FAILS -> TypeError("type 'Context' is not subscriptable")
=== 4. add_tool signature adaptation ===
Path A mcp.tool(name=,description=,annotations=)(wrapper) OK -> function
=== 5. does mcp.call_tool run middleware? (current test's entry point) ===
mcp.call_tool returned: ToolResult(... text='builtin ok marker=direct via_request_ctx=<err
  AttributeError("\'NoneType\' object has no attribute \'lifespan_context\'")> via_direct=NO_MARKER')
middleware.seen after direct call_tool: [{'name': 'builtin_probe', 'arguments': {'marker': 'direct'},
  'ok': True, 'lifespan_via_request_ctx': '<err ...NoneType...>', 'lifespan_via_direct': {}}]
=== 6. in-memory Client (runs lifespan + full dispatch + middleware) ===
tools/list names: ['builtin_probe', 'ext_probe']
builtin call result: builtin ok marker=wire via_request_ctx=APPCTX_SENTINEL via_direct=APPCTX_SENTINEL
ext call result:     ext ok via_request_ctx=APPCTX_SENTINEL kwargs={'body': 'hello'}
middleware.seen after in-memory client calls:
   {'name': 'builtin_probe', 'arguments': {'marker': 'wire'}, 'ok': True,
    'lifespan_via_request_ctx': 'APPCTX_SENTINEL', 'lifespan_via_direct': 'APPCTX_SENTINEL'}
   {'name': 'ext_probe', 'arguments': {'body': 'hello'}, 'ok': True,
    'lifespan_via_request_ctx': 'APPCTX_SENTINEL', 'lifespan_via_direct': 'APPCTX_SENTINEL'}
=== 7. serverInfo.version over in-memory client ===
serverInfo.version: 1.2.3-probe
```
Reading it: (1) `Context[...]` breaks module load; (5/6) middleware sees `message.name`/`.arguments`
and reaches the AppContext via `fastmcp_context.request_context.lifespan_context` — but ONLY when a
SESSION has run the lifespan (direct `mcp.call_tool` gives `request_context=None`, so unit pins drive
`on_call_tool` directly with a store-backed double); (4) the `add_tool` adaptation works; (7)
serverInfo.version = the ctor kwarg.

*(The full introspection dump — `FastMCP.__init__`/`http_app` signatures, `_tool_manager` absence,
`create_streamable_http_app` ordering, HostOriginGuardMiddleware 421/403 bodies, settings defaults —
is at `/tmp/fastmcp_introspect_59.out`, 20 KB; its load-bearing rows are tabulated in §"fastmcp 3.x
verification" above.)*

---

## Bottom line for the CONTRACT-ADVERSARY + BUILD

The migration contract is complete and PAUSES here. The adversary should attack: (a) the funnel-∀
reach (does a wrong build funnel built-ins but not `add_tool` extensions? — the wire gate must run,
not skip, on a reference build); (b) the P9 disabled-name leg (build the `on_duplicate='error'`-alone
wrong build and confirm it FAILS leg 2); (c) the B4 shield (build the unshielded emission and confirm
the anyio-scope pin reddens while the asyncio pin stays green); (d) the `_read_trace_rows`/`_query`
shape (the one hand-rolled read that needs alignment). The build's FIRST step is the dep swap +
the ~16 `Context[...]` → `Context` edits (else nothing collects), and it must supply the
`migration_wire` real-uvicorn fixture + update `_auth_fixtures.stub_heavy_startup` for the deleted
guard.
