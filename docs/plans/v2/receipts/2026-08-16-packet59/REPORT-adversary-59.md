# REPORT-adversary-59 — contract-adversary grade of packet 59 (fastmcp 3.x migration)

brief-base v14 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4 — first thing)
- **Demanded vs. have:** `uv` (✓), network to install `fastmcp>=3.4,<4` ephemerally into a scratch
  copy (✓ authorized — packet D4 dep), lore tools (✓ `ToolSearch "+lore"`), Read of the 3 contract
  files + design + `server.py` (✓), `scripts/scratch_copy.sh` (✓), the TEST store
  `ws://127.0.0.1:18000` (✓ port open — real-store legs ran), WRITE to scratch + this report (✓).
  **No blocker.** The mission ran end to end: a full reference build + 8 wrong-build probes.
- **Model attestation (brief-carried, cannot self-read):** `claude-opus-4-8` (Opus 4.8), `opus48-worker` pin. ✓
- **P6b FIDELITY DEVIATION (disclosed):** the brief ordered the deleted-code enumeration BEFORE
  opening design §5, but the brief ALSO named §5 an INPUT and I read the whole design doc (which
  contains §5) in one Read. So my P6b Stage-1 was NOT frame-blind. Mitigation: Stage-1 was derived
  strictly from live `server.py` source (`lore_get_symbol`, cited) and I diffed against §5 regardless.
  Honest bound: a frame-blind pass might have found more.

## SUMMARY BLOCK
- state: **done** · VERDICT: **CONTRACT INSUFFICIENT** (a STRONG core with SPECIFIC, actionable gaps — not a weak contract)
- deviations: (1) P6b Stage-1 was not frame-blind (I read design §5 as a required input first — mitigated by source-grounding, §capability check). (2) The wire-lane pins (4 skips) could not be executed against a real uvicorn fixture (does not exist) — assessed by construction + an in-memory-Client stand-in for the funnel-∀ leg.
- Reuse ledger: none — no repo symbols introduced (the reference build is a disposable scratch copy, not a deliverable; probes only).
- **P1 headline:** No wrong build survived the contract's IN-SCOPE core — 8 distinct wrong builds all
  reddened the pin they should, and a full reference build gives **32 passed / 4 skipped** (before AND
  after ruff --fix; no C-DEF). BUT four wrong "builds"/omissions ARE waved through: (i) a `Context→Any`
  injection-dodge passes all of SECTION A; (ii) a single-shot lifespan re-home drops FP-07 bounded-retry
  with no pin; (iii) funnel-∀ over extension tools is checked only by a SKIP; (iv) the §6.6 collect-only
  gate is blind to ~7 runtime test breakages the migration causes.
- Graded: `ee4bced` · HEAD-at-report: `ee4bced` · **SAME**.
- Packages considered: `fastmcp` 3.4.7 — **replace** (façade + trace middleware); `mcp` **keep_with_trigger**
  (rides transitively; re-open at first off-fleet consumer / mcp-v2). READ: installed 3.4.7 signatures +
  live wire/injection probes (pasted §PROBES). Diff vs the contract's P-PKG table: **no disagreement** —
  its `replace`/`keep_with_trigger` verdicts reproduce.
- **Missing pins (ranked):** ①FP-07 bounded-retry re-home (DUAL incomplete for C2) · ②Context-injection-survives
  (SECTION A pins registration, not injection) · ③in-memory funnel-∀ (feasible without uvicorn). **Required
  corrections:** ④coupling-#1 "module-LOAD break" claim is FALSE (#107-class) · ⑤§6.6 collect-only gate blind
  to runtime breakages — needs full-suite + affected-file enumeration.
- decisions-needed for lead-59/operator: the test-surface impact is ~8–10 files, not the design's "2
  re-authored + ~4 ToolError" — this ~4× under-count changes the build's effort estimate and needs a scope call.
- receipt POINTERS: §SATISFIABILITY (reference build) · §WRONG-BUILDS (8 probes) · §P1b quantifier table ·
  §P1c reach table · §P6b diff · §PROBES (commands+output). Reference build = a scratch copy (disposable);
  the patcher + all commands are pasted so every claim re-runs.

---

## VERDICT: CONTRACT INSUFFICIENT

The contract's **in-scope core is strong** — I could not break the trace-middleware re-home, the P9
guard, the identity/params-hash policy, or the D6/D7 registration/install pins; every wrong build I
threw at them reddened correctly, and the whole contract goes 0-failed against a known-correct
reference build. **INSUFFICIENT rests on concrete, feasible missing pins** (below), not on the core.
Sending it back costs one revision; shipping it as-is ships a silently-dropped boot-resilience
behavior (FP-07) and a plausible wrong-fix (`Context→Any`) that no runnable pin catches.

---

## P1 — WRONG BUILDS (empirical; reference build in scratch, real contract run against it)

Reference build: `scripts/scratch_copy.sh` copy at
`…/scratchpad/adversary-59/refbuild` (provenance ASSERTED — `loremaster.__file__` inside the copy),
`fastmcp>=3.4,<4` synced (3.4.7), then the migration applied by an AST patcher (pasted §PROBES). It
imports cleanly and gives the **SATISFIABILITY receipt: 32 passed / 4 skipped** (the 4 skips = the
wire-lane placeholders), holding **after `ruff --fix`** removed the two orphaned imports the swap
demands. The re-authored `test_trace_telemetry.py` + `test_wire_discipline.py`: **49 passed / 1 skip**
on the migrated build. **No pin is RED on a correct build — no C-DEF.**

| # | wrong build (mutation of the reference) | pin that should catch it | result | verdict |
|---|---|---|---|---|
| (c) B4 | drop `anyio.CancelScope(shield=True)` from the emission | `…SurvivesAnyioLevelTriggeredCancellation::…still_writes_its_row` | **RED**, while the asyncio sibling `…RecordedOkFalse` stays GREEN + the bounded-constant pin GREEN | **caught — discriminating asymmetry real** |
| (b) P9 | reserve only the ENABLED/registered surface, not `_ALL_BUILTIN_TOOL_NAMES` (the `on_duplicate='error'` semantic) | `…CollisionsAreRefused::…DISABLED_builtin_name_is_still_refused` | leg1 (enabled) GREEN, **leg2 (disabled) RED** | **caught — the disabled-name leg is the discriminator** |
| D6 | keep the old single-arg `mcp.add_tool(wrapper, name=…)` (coupling #2) | `TestExtensionToolsRegisterAndAreCallable` (both) | **RED (both)** | **caught** |
| D7 | define `ToolTraceMiddleware` but never install it | `…TraceMiddlewareIsInstalledAtTheOneFunnel` | **RED** | **caught** |
| B7-a | drop the `isinstance(str)` filter | `…IsDeclaredNeverGuessed::…non_string_argument_mints_no_identity` | **RED** (other two GREEN) | **caught** |
| B7-b | all-or-nothing identity harvest | `…IsDeclaredNeverGuessed::…partial_declaration_is_recorded_partially` | **RED** (other two GREEN) | **caught** |
| T6 | store `params_hash` as raw `json.dumps` (no sha256) | `…ParamsHashCarriesFreeTextOnlyAsADigest` | **RED** (oracle mismatch + hostile-body leak) | **caught** |
| #1 | leave ALL 17 `Context[Any, AppContext, Any]` unfixed | `TestTheMigratedServerImportsAndBuilds` | **ERROR** at the `built_server` fixture (TypeError at REGISTRATION) — but the bare-import pin PASSES | **caught by the fixture; see FINDING ④** |

**WAVED THROUGH (the findings):**

| wrong build | which pins it passes | escapes because |
|---|---|---|
| **`Context→Any`** (dodge the subscript by weakening the annotation) | **ALL 4 SECTION A pins PASS** | SECTION A pins *registration*, not *injection*; the annotation-based context injection breaks (`context` leaks into every tool's client schema — measured) — only the SKIPPED wire smoke would catch it → **FINDING ②** |
| **single-shot lifespan re-home** (heavy build in `lifespan=` with no bounded retry) | every migration pin (only `…OncePerProcessEagerly` is relevant and it is a `pytest.skip`) | FP-07 bounded-retry (`loresigil.backoff`, ruff-orphaned by the delete) is deleted with the apparatus; no pin, no ruled-DROP → **FINDING ①** |
| **extension tools bypass the trace middleware** | D6 + D7 pass (register + install); no runnable pin dispatches an extension tool through the middleware | funnel-∀ is deferred entirely to the SKIPPED `TestTheWireSmokeServesTheFullSurface` → **FINDING ③** |

---

## MISSING PINS (each = the test that should exist + the defect it catches)

**① [HIGH] FP-07 bounded-retry (+ apparatus behaviors) DELETED with no re-pin and no ruled-DROP — the DUAL is incomplete for C2.**
The `_ProcessLifespanGuard`/`_EagerStartupLifespan` DELETE removes five observable behaviors (P6b
Stage-1 #15–21). Only *once-per-process* is adjudicated (design §5b-C2) and even that is a `pytest.skip`
(wire gate, unbuilt). **FP-07 bounded-retry-with-backoff is a preservation RIDER in the design** ("FP-07
re-homes INSIDE" the native lifespan, §5b-C2) with **no instrument** — and fastmcp's native `lifespan=`
does NOT retry a failed build. Ruff proves it: deleting `_EagerStartupLifespan` orphans
`from loresigil import backoff` (server.py:238), the retry primitive (used at server.py:11961 "FP-07 —
bounded retry-with-backoff for the eager heavy build"). Its existing test `test_backoff_seam.py` breaks
at the migration.
- *Test that should exist:* a pin that the migrated lifespan wraps the heavy build in the bounded-retry
  primitive (structural: it references `backoff`/N>1), OR a behavioral pin injecting a fail-then-succeed
  build and asserting the container comes up. *Or* an explicit ruled-DROP for each of {concurrent-reuse,
  sequential-rebuild, build-failure-not-cached, FP-07 retry} with a reason (per the DUAL / "rider is part
  of the ruling").
- *Defect it catches:* a builder re-homes the heavy build into `lifespan=` as single-shot; a transient
  boot-time SurrealDB/TEI blip aborts the container on first failure instead of retrying — passing every
  migration pin.

**② [MODERATE] SECTION A does not pin that `Context` INJECTION survives — the `Context→Any` wrong-fix passes.**
Measured: a build that "fixes" the subscript TypeError by weakening `context: Context` → `context: Any`
passes all 4 SECTION A pins (module loads, 15 tools register) but breaks injection — `context` appears
in every tool's published input schema as a required arg (probe: `weak: props=['context','q']` vs
`good: props=['q']`), so the tools are unusable on the wire.
- *Test that should exist:* an in-memory `Client` pin (NO uvicorn) that lists a built-in tool through a
  server from `build_mcp_server` and asserts `context` is NOT in its `inputSchema.properties`.
- *Defect it catches:* the annotation weakened to `Any`/removed (a plausible way to dodge coupling #1) —
  registration succeeds, injection is dead, every tool demands an un-suppliable `context`.

**③ [MODERATE] funnel-∀ over {built-in, add_tool extension} is checked only by a SKIP, though an in-memory pin is feasible.**
Measured: fastmcp middleware funnels BOTH a built-in-style tool AND an `add_tool`-adapted extension via
an in-memory `Client` (probe §PROBES). So the FG2 catch does NOT need real uvicorn. Currently funnel-∀
coverage is NOT a checked variable at any runnable level — `TestTheWireSmokeServesTheFullSurface` is a
`pytest.skip`. (Residual risk is indirectly covered by D6 + D7 + fastmcp's server-wide middleware
semantics; this pin makes the reach a checked variable per the instrument-lesson.)
- *Test that should exist:* register `CounterExtension`, drive an in-memory `Client` call to the extension
  tool, assert the trace middleware observed it (or a trace row landed via a store double).
- *Defect it catches:* an extension tool that registers but is not funnelled (belt-and-braces vs D6/D7).

---

## REQUIRED CORRECTIONS (not missing pins — the defect is caught, but the contract is WRONG/weak)

**④ [MODERATE — #107 class] The coupling-#1 claim "module-LOAD break / `loremaster.server` fails to IMPORT" is FACTUALLY FALSE.**
`server.py:39` has `from __future__ import annotations` → all annotations are PEP-563 STRINGS, never
evaluated at import. Measured: with all 17 `Context[...]` left unfixed, `import loremaster.server`
**succeeds**; the `TypeError: type 'Context' is not subscriptable` fires at **tool registration** inside
`build_mcp_server` (fastmcp/pydantic resolves the string annotation there). `test_loremaster_server_imports_under_fastmcp`
**PASSES on the broken build**; the discrimination lives entirely in the `built_server`-fixture pins
(`…constructs_a_fastmcp_instance` / `…fifteen_builtin_tools_register` ERROR). This is precisely the
#107 class — a dependency-behavior claim (the author's `Context[object,object,object]` REPL probe
evaluated EAGERLY because a REPL has no `from __future__ import annotations`; the file does, so the eager
result does not transfer). Correct the claim in the contract docstrings, design §5/§0, and REPORT-contract-59
"FIVE couplings #1": the break is a **tool-registration** break inside `build_mcp_server`, not a module-load
break; the bare-import pin does not catch it.

**⑤ [HIGH — scope/gate] The migration's test-surface impact is ~8–10 files (not "2 re-authored + ~4 ToolError"), and the §6.6 collect-only gate is blind to most of it.**
P6 corpse sweep (test tree, bare patterns) + empirical runs on the reference build:
- **collection ERROR (the §6.6 collect-only gate SEES this one):** `test_eager_startup.py` — module-level
  `from loremaster.server import _ProcessLifespanGuard` → ImportError (987 others still collect).
- **RUNTIME break (COLLECT fine → INVISIBLE to collect-only; RED only under the full suite / in-image):**
  `test_extension.py`, `test_task_read_surface.py`, `test_hosted_readonly_posture.py`,
  `test_auth_composition.py` all reach `mcp._tool_manager…` (renamed `_local_provider` → AttributeError,
  confirmed `hasattr(FastMCP(),"_tool_manager")==False`); `test_backoff_seam.py` mock-patches
  `_EagerStartupLifespan._acquire_eager_lease_with_retry` (gone); `test_mcp_server.py` in-method-imports
  `_ProcessLifespanGuard` (gone).
- **ToolError-import mismatch (~4 files):** `test_tool_allowlist.py`, `test_hosted_readonly_posture.py`,
  `test_mcp_server.py`, `test_permission_resolver_seam.py` import `mcp.server.fastmcp.exceptions.ToolError`
  — a `pytest.raises(ToolError)` won't catch `fastmcp.exceptions.ToolError`.
- **SOFT CORPSE:** `test_server_version.py` **passes** on the migrated build (fastmcp still exposes
  `mcp._mcp_server.version`, carrying the ctor value) — but its docstring teaches the retired private-attr
  mechanism; it is green because it still asserts the corpse.
- The design §4 named only `test_wire_discipline` + `test_trace_telemetry` re-authored + "~4 ToolError".
  RECOMMEND: (a) the migration gate is a **full-suite** run (or the §6.1 in-image conformance) — NOT
  collect-only; (b) ENUMERATE the affected files in the design so the build meets them deliberately;
  (c) `_tool_manager` (→ `_local_provider`) is the highest-count runtime break — grep for it.

---

## RESIDUALS (each with an individual verdict)

- **`wire` marker unregistered + not deselected by config.** Verdict: real minor gap. The 5
  `@pytest.mark.wire` tests self-skip (`pytest.skip`) so they are harmless today, but the marker routes
  nothing to a deploy lane and would ERROR under `--strict-markers`. Register it in `[tool.pytest.ini_options] markers`.
- **Stale prose `TracingFastMCP` in server.py:2475** (a docstring reference). Verdict: real, build-side.
  The `test_trace_telemetry.py` prose-scan (`_telemetry_prose_offenders`) keys on RETIRED-PLAN phrases
  ("fire-and-forget", …), NOT retired NAMES — so it does not catch a lingering `TracingFastMCP`/`request_ctx`/
  `streamable_http_app` mention. The rename-sweep at kickoff must cover it.
- **`_read_trace_rows`/`_query` shape (target d).** Verdict: SOUND. The real-store legs
  (`TestTheMigratedSeamLandsARealRow`) landed and read back a real row on the reference build — the
  `store._query(SELECT … FROM trace)` shape is correct; the `_TraceRecorder` signature-bind + the real
  store together close the W30/W33 hole.
- **`_app_context` / `_extension_tool_wrapper._tool` `Context[...]` annotations.** Verdict: harmless dead
  strings — `_app_context` is never introspected; `_extension_tool_wrapper` overrides `__signature__`/
  `__annotations__` with a bare `Context`. Not a defect, but they are the sites a `Context→Any` "fix" (②)
  would also touch.

---

## P1b — QUANTIFIER TABLE (every load-bearing invariant, ∀-vs-guarded, with a door-build receipt)

| invariant | ∀ or GUARDED | door-build receipt (surviving wrong build OR the pin that killed it) |
|---|---|---|
| B1 one-row-per-dispatch | ∀ over outcome (return/raise) | satisfiability: `…RecordsOneRowPerDispatch` + `…OutcomeAlwaysWins::…raising…` GREEN on correct; the raise leg's `len(calls)==1` forces the finally-write |
| B2 outcome-wins + swallow + loud log | ∀ (success/raise/broken-store) | satisfiability: `TestATraceWriteFailureNeverTouchesTheCall` (3 legs + positive control) GREEN; the log leg keys on a structured dotted event |
| B3 ok-latch | ∀ over 3 fates | shield-drop probe: the asyncio-cancel leg stayed GREEN (latch intact) while the anyio leg reddened — the latch and the shield are independently pinned |
| **B4 shield** | GUARDED→discriminating | **door built:** shield dropped → `…still_writes_its_row` RED, asyncio sibling GREEN. Discriminates. |
| B5/B6 degrade | ∀ over 2 states | satisfiability: `fastmcp_context=None` no-op + `_no_store_fastmcp_context()` WARN both GREEN on correct |
| **B7 identity** | ∀ over 3 fates | **two doors built:** drop str-filter → `non_string` RED; all-or-nothing → `partial` RED. Both legs discriminate. |
| B8 latency | GUARDED (bracket) + ∀ (difference) | satisfiability: `…latency_is_present_and_bounded` + `…two_durations_record_different_latencies` GREEN; the difference pin is fixture-independent |
| **T6 params_hash** | ∀ (oracle + hostile) | **door built:** store verbatim → RED (oracle mismatch + hostile-body leak). Independent oracle, not a tautology. |
| **P9 collision** | ∀ over 2 legs | **door built:** enabled-not-universe → leg2 RED, leg1 GREEN. The disabled-name leg is the discriminator. |
| **D6 register** | ∀ over the extension surface | **door built:** old single-arg add_tool → both D6 pins RED |
| **D7 install** | count==1 (not len==1) | **door built:** drop `middleware=[…]` → RED |
| **Context-import** | ∀ over the 15 built-ins | **door built:** unfixed → `built_server` fixture ERRORS (registration). ⚠ ∀ is over REGISTRATION, NOT injection — the `Context→Any` build passes (FINDING ②) |
| **funnel-∀ {built-in, extension}** | GUARDED — deferred to a SKIP | **NOT a checked variable at runnable level** (FINDING ③); the wire pin is `pytest.skip`. Reach is fastmcp's server-wide middleware (probe-confirmed) but no lore pin observes it |

## P1c — REACH TABLE (per instrument the contract introduces/relies on)

| instrument | reach set | DERIVED or hand-list? | coverage a checked variable? | effect or proxy? | one-source / mutation | verdict |
|---|---|---|---|---|---|---|
| ToolTraceMiddleware install (D7) | the ONE construction site's middleware list | DERIVED (isinstance count over `built_server.middleware`) | yes (count==1; 0 and >1 both fail) | EFFECT (reads the installed list) | mutation-proven (drop install → RED) | **SAFE (empirical)** |
| P9 collision universe | `_ALL_BUILTIN_TOOL_NAMES` ∪ local registered set | DERIVED (the built-in registry) | **yes** — the disabled-name leg reddens the enabled-only build | EFFECT (build raises ValueError) | single guard; mutation-proven (leg2) | **SAFE (empirical)** |
| trace-prose sweep (`_telemetry_prose_offenders`) | 3 whole modules, every comment+string | DERIVED (not a docstring hand-list) — has its own +/- control (`test_the_sweep_itself_fires`) | yes (control fires) | EFFECT | single | **SAFE** — but its phrase-list is retired-PLAN only; it does NOT catch retired NAMES (residual) |
| SECTION A module-load gate | the 15 built-ins registering | registration is checked; **injection is NOT** | **NO for injection** | proves registration, not the served schema | — | **GAP (FINDING ②)** |
| funnel-∀ reach | {built-in, add_tool extension} | reach is fastmcp's (DERIVED) but **unobserved by any runnable pin** | **NO** (deferred to a skip) | — | — | **GAP (FINDING ③)** |
| §6.6 collection gate | collect-time import errors only | — | catches 1 of ~8 breakages | **PROXY** — collect-only cannot see runtime `_tool_manager`/mock-patch breaks | — | **INADEQUATE (FINDING ⑤)** |

Legs run: EMPIRICAL for D7, P9, module-load, funnel-∀ reach, §6.6 (all built + run in scratch). Construction-inspection for the prose sweep (read its controls).

---

## P6b — DELETED-CODE DIFF (my source enumeration vs design §5)

Stage-1 (from live `server.py`, cited by symbol) enumerated 27 behaviors across the deleted/rewritten
seams (full list retained below). Stage-2 diff vs §5 B1–B8/C1–C5/D1–D7: **§5 covers B1–B13 and the
mechanical C/D rows faithfully.** The behaviors §5 UNDER-covers (→ findings above):
- **FP-07 bounded-retry re-home (Stage-1 #21):** §5b-C2 names it as re-homed but the contract pins
  nothing → **FINDING ①**.
- **concurrent-reuse / sequential-rebuild / build-failure-not-cached (Stage-1 #16–18):** §5b-C2 collapses
  all apparatus behavior to the single "once per process" property (a skip pin); the other three are
  dropped without an explicit per-item DROP ruling → part of **FINDING ①** (DUAL completeness).
- Everything else maps to a §5 row + a discriminating contract pin (verified empirically above).

### P6b Stage-1 (retained, source-grounded)
call_tool→middleware: (1) one row/dispatch (2) latency around dispatch (3) ok-latch no-except (4) result
unchanged (5) write in finally (6) shield (7) bounded (8) except-Exception swallow+loud. _record_tool_trace:
(9) no-request-context→DEBUG no-op (10) no write_store→WARN (11) str-only declared identity (12) measured
correlator (13) no client ordinal (14) bounded identity. apparatus DELETE: (15) once-per-process (16)
concurrent-reuse (17) sequential-rebuild (18) build-failure-not-cached (19) eager hoist (20) http-scope
passthrough (21) FP-07 bounded-retry. rewrites: (22) per-session logging (23) allowlist validate (24)
version ctor (25) P9 universe+registered (26) add_tool+readOnlyHint=False (27) Origin always / Bearer outermost.

---

## PROBES — full record (commands + real output)

**Environment.** Reference build in a `scratch_copy.sh` copy (provenance ASSERTED:
`loremaster.__file__` inside the copy). `fastmcp>=3.4,<4` → 3.4.7 synced (D4 dep swap:
`"mcp[cli]>=1.27"` → `"fastmcp>=3.4,<4"`; `mcp` rides transitively — `import mcp.types` /
`mcp.server.fastmcp` both OK). Python 3.14. The AST patcher and every mutation are pasted below so
each claim re-runs; the scratch tree itself is disposable.

**fastmcp §0 facts re-verified (all match the contract):** `Context[a,b,c]` → `TypeError: type
'Context' is not subscriptable`; `FastMCP.__module__ == fastmcp.server.server`; ctor has
`version`/`middleware`/`on_duplicate`, NO host/port/streamable_http_path; `_tool_manager` GONE,
`_local_provider` present; `get_tool` is async; `http_app(path, stateless_http, host_origin_protection,
allowed_hosts, allowed_origins)`, no `streamable_http_app`; `add_tool(tool)` single-arg;
`on_call_tool(context, call_next) -> ToolResult`.

**Reference migration (AST patcher).** Swapped the 3 head imports (`from fastmcp import Context,
FastMCP`; added `Middleware, MiddlewareContext`; dropped `request_ctx`), replaced `Context[Any,
AppContext, Any]`→`Context` at all 17 sites, replaced `TracingFastMCP` with `ToolTraceMiddleware(Middleware)`
+ a module-level `_record_tool_trace(fastmcp_context, …)` (design M4 write policy, accessor re-homed to
`context.fastmcp_context.request_context.lifespan_context`), rewrote `build_mcp_server` (native
`lifespan=`, `version=`, `middleware=[ToolTraceMiddleware()]`, guard deleted), `_register_extension_tools`
(sync universe+local collision, `mcp.tool(name=…)(wrapper)` adaptation), `build_asgi_app`
(`http_app(path=)`), and DELETED `_ProcessLifespanGuard` + `_EagerStartupLifespan`. Full patcher script
lives at the scratch path `…/scratchpad/adversary-59/patch_refbuild.py` (re-runnable; pasted intent above).

```
# SATISFIABILITY (correct reference build)
$ pytest tests/test_fastmcp_migration.py -q
32 passed, 4 skipped, 4 warnings
# after `ruff check --select F --fix server.py` (removed unused ContentBlock + loresigil.backoff):
32 passed, 4 skipped
# re-authored files on the migrated build:
$ pytest tests/test_trace_telemetry.py tests/test_wire_discipline.py -q
49 passed, 1 skipped

# (c) shield drop
FAILED …SurvivesAnyioLevelTriggeredCancellation::test_a_scope_cancelled_dispatch_still_writes_its_row
PASSED …TestTheCancelledDispatchIsRecordedOkFalse::test_a_cancelled_dispatch_records_ok_false   (asyncio sibling stays green)
PASSED …SurvivesAnyioLevelTriggeredCancellation::test_the_shielded_write_is_bounded

# (b) P9 reserve-enabled-not-universe
PASSED …CollisionsAreRefused::test_collision_with_a_registered_builtin_is_refused
FAILED …CollisionsAreRefused::test_collision_with_a_DISABLED_builtin_name_is_still_refused

# D6 old single-arg add_tool → 2 failed ; D7 no install → 1 failed
# B7 drop str-filter → non_string RED ; all-or-nothing → partial RED ; T6 verbatim → params_hash RED

# coupling #1 — leave all 17 Context[...] unfixed:
IMPORT OK (PEP 563 strings, no eval)
PASSED …test_loremaster_server_imports_under_fastmcp
PASSED …test_mcp_still_importable_transitively
ERROR  …test_build_mcp_server_constructs_a_fastmcp_instance   (TypeError at registration)
ERROR  …test_all_fifteen_builtin_tools_register

# Context->Any injection-dodge — passes ALL of SECTION A:
4 passed
# injection probe: good(context: Context) -> client props=['q'] ; weak(context: Any) -> client props=['context','q']

# funnel-∀ probe (in-memory Client, NO uvicorn):
registered: ['builtin_style', 'ext_bump']
middleware fired for: [('builtin_style', True), ('ext_bump', True)]   -> funnel-∀ over {built-in, add_tool extension} = True

# corpse sweep + collection on affected files (migrated build):
ImportError: cannot import name '_ProcessLifespanGuard'  -> ERROR tests/test_eager_startup.py
987 tests collected, 1 error            (collect-only sees ONLY test_eager_startup.py)
test_server_version.py -> 11 passed     (SOFT CORPSE: green via the retired _mcp_server.version reach)
hasattr(FastMCP(), "_tool_manager") == False   (every mcp._tool_manager.* test body → runtime AttributeError)
```

Every finding above has a reproduction in this record. The scratch reference build + patcher are
disposable (a scratch dir, not a git worktree); the lead need keep nothing — the commands re-derive it.
