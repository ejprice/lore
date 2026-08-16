# REPORT-adversary-59b — contract-adversary PASS 2 grade of packet 59 (fastmcp 3.x migration)

brief-base v14 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4 — first thing)
- **Demanded vs. have:** `uv` (✓); network to `uv run --with 'fastmcp>=3.4,<4' --with uvicorn --with httpx`
  into the scratch copy (✓ authorized, D4 dep); `scripts/scratch_copy.sh` (✓ — provenance ASSERTED);
  lore tools (`ToolSearch "+lore"`, ✓); Read of the 3 contract files + design + `server.py` +
  both predecessor reports (✓); the TEST store `ws://127.0.0.1:18000` (✓ OPEN — real-store legs ran);
  WRITE to the scratch dir + this report (✓). **No blocker — the mission ran end to end** (partial +
  full reference builds, 6 wrong-build probes, full satisfiability run + ruff leg).
- **Model attestation (brief-carried, cannot self-read):** `claude-opus-4-8` (Opus 4.8), `opus48-worker` pin. ✓
- **Scratch provenance receipt:** `loremaster.__file__ =
  …/scratchpad/adversary-59b/refbuild/loremaster/loremaster/__init__.py` (INSIDE the scratch copy —
  scratch_copy.sh asserted it; I am NOT grading the original tree). fastmcp **3.4.7** synced.
- **Tool honesty:** lore_get_symbol / lore_read served the apparatus; one grep fallback (retired-name +
  constant occurrence scan over `server.py`) — a NON-SYMBOL textual seam (sanctioned case, CLAUDE.md
  dogfood §3b). No lore weakness → no finding filed.

## SUMMARY BLOCK
- state: **done** · VERDICT: **CONTRACT INSUFFICIENT** — narrow: ONE confirmed over-constraint
  (①-OC) needing an operator/lead RULING. **All 5 adversary-59 gaps ARE closed; NO wrong build
  survives; NO C-DEF.** This is a design-interface ruling gate, NOT an under-constraint hole.
- **P1 headline:** No wrong build survives the revised contract — I threw 6 distinct wrong builds
  (single-shot re-home, `Context→Any`, FG2 funnel-filter, `Context`-unfixed, routing-not-sharing,
  shield-drop) and EVERY ONE reddened the pin it should. Full contract vs a complete correct reference
  build (FP-07 helper wired, apparatus deleted, prose scrubbed) = **43 passed / 4 skipped**, holding
  after `ruff --fix`. The ONE finding is an OVER-constraint: the ① nameable-helper interface REJECTS a
  legitimate INLINE FP-07 re-home (3/4 retry pins RED, indistinguishable from the wrong single-shot).
- Graded: `ee4bced` · HEAD-at-report: `ee4bced` · **SAME** (coupling sites in `server.py` unchanged).
- deviations: (1) I built the reference in layered targeted patches (helper → middleware → build_mcp_server
  → apparatus-delete+scrub) rather than one monolith; each isolates exactly what its pin-group needs —
  legs run vs inferred are labelled throughout.
- Packages considered: **`fastmcp` 3.4.7 — replace** (façade + trace middleware); `mcp`
  **keep_with_trigger** (rides transitively; re-open at first off-fleet consumer). READ: installed 3.4.7
  signatures + live build/inject/funnel probes. Diff vs the contract's + adversary-59's P-PKG table:
  **no disagreement**.
- Reuse ledger: none — no repo symbols introduced (the scratch reference build is disposable; probes only).
- **Graded:** `test_fastmcp_migration.py` (47 collected), `test_trace_telemetry.py`, `test_wire_discipline.py`.
- decisions-needed for lead-59/operator:
  1. **① FP-07 interface (the reviser's flag, CONFIRMED genuine):** the nameable-helper pins reject a
     correct inline re-home. This is a DESIGN decision (a property-to-invent — how FP-07 re-homes) and
     per CLAUDE.md must be operator-ruled before a builder sees it. **My recommendation: ACCEPT the
     imposition** (keep the pins) — the retry is *already* a named unit today
     (`_EagerStartupLifespan._acquire_eager_lease_with_retry`), the nameable helper PRESERVES that
     testable unit across the migration (a DUAL virtue), and it is the ONLY way to get runnable FP-07
     coverage; an inline re-home dissolves the unit and loses it. Keep the contract's explicit
     "inline → escalate" note. This makes the verdict a ~5-minute ruling, not a rework.
- receipt POINTERS: §PHASE-A (① contest + ③ funnel + SECTION B) · §PHASE-B/C (② + SECTION A + ④ +
  full satisfiability) · §FINDINGS · §P1b · §P1c · §RESIDUALS · §PROBES (every command + count).

---

## VERDICT: CONTRACT INSUFFICIENT (narrow — one design-interface ruling gate)

**The revision SUCCEEDED on its primary axis.** Every one of adversary-59's five findings is closed
with a RUNNABLE, DISCRIMINATING pin — I built the exact wrong builds each was meant to catch and every
one now reddens (§FINDINGS, §PROBES). The full revised contract goes **0-failed against a known-correct
reference build** (43 passed / 4 skipped, after `ruff --fix` too) — **no NEW pin is RED on a correct
build, so NO C-DEF.** The 8-pin strong core still discriminates (spot-checked: B4 shield-drop).

**INSUFFICIENT rests on ONE finding, and it is an OVER-constraint, not an under-constraint hole:** the
① FP-07 pins force the build to expose a nameable module-level async helper `_eager_build_with_retry`,
and a CORRECT build that inlines the bounded retry in the `lifespan=` closure (a legitimate re-home)
FAILS 3 of the 4 retry pins — **indistinguishable from the WRONG single-shot re-home.** The reviser
FLAGGED this for me to contest (contract-59b deviation 3 + HONEST BOUNDS); I confirmed it is genuine.
Because it is a DESIGN decision baked into a pin without an operator ruling, it routes back for that
ruling (my recommendation: ACCEPT). Nothing else blocks; if the operator rules "keep the pins," the
contract is fully sufficient as written.

---

## PHASE A — ① FP-07 contest, ③ funnel, SECTION B (empirical; partial reference build)

Partial reference = scratch `server.py.orig` + an appended standalone FP-07 helper
`_eager_build_with_retry` + a faithful `ToolTraceMiddleware(Middleware)` re-home of
`TracingFastMCP.call_tool` + a module-level `_record_tool_trace` (M4 policy, reads `write_store` off
`fastmcp_context`). All commands + counts in §PROBES.

### ① FP-07 CONTEST — CONFIRMED OVER-CONSTRAINT (Finding ①-OC)
The contract pins FP-07 as a **nameable standalone async helper** `_eager_build_with_retry` (constant
`_EAGER_RETRY_HELPER_NAME`; `_eager_retry_helper()` fetches it at call time and asserts it exists). I
built BOTH references the brief asked for, and the tell-tale third:

| build | `_eager_build_with_retry` present? | the 4 `TestTheEagerHeavyBuildRetriesTransientFailures` pins |
|---|---|---|
| **correct, helper extracted** | yes | **4 passed** |
| **single-shot re-home (WRONG)** | no | **3 FAILED, 1 passed** (pin 3 reads the surviving constant) |
| **inline-correct re-home (RIGHT)** | no (retry inlined in the `lifespan=` closure) | **3 FAILED, 1 passed — byte-identical to the WRONG build** |

**The pins cannot tell a WRONG single-shot re-home from a CORRECT inline re-home** — both lack the
module-level symbol, both give the identical 3-RED / 1-GREEN. The three failing pins are
`…retried_then_the_build_comes_up`, `…fails_closed_after_the_budget`,
`…routes_through_the_shared_backoff_policy` (all fetch `_eager_retry_helper()`, which RAISES when the
symbol is absent); the survivor is `…budget_is_bounded_and_greater_than_one` (reads only the constant).

**C2 DUAL completeness (adversary-59 ①, verified):** the `_ProcessLifespanGuard` +
`_EagerStartupLifespan` DELETE removes SEVEN observable behaviours (P6b #15–21); the revised contract's
SECTION C header adjudicates **all seven** (I read each): #15 once-per-process → PRESERVE-property
(wire gate); #16 concurrent-reuse / #17 sequential-rebuild / #19 eager-hoist → DROP the bespoke
mechanism, PRESERVE the property (wire-gate legs, since fastmcp's in-memory transport skips the ASGI
lifespan — FG1 — so these genuinely cannot be in-process unit pins); #18 build-failure-not-cached →
DROP the per-lease mechanism, PRESERVE the transient-resilience VIRTUE via FP-07 #21 (fail-closed leg,
runnable); #20 http-scope-passthrough → DROP (no interceptor), covered by the §6.2 auth gate; #21
FP-07 → PRESERVE+PIN. No spec-silent item; no unadjudicated deletion. The one adjudication worth a
second look — #18's "next lease retries" virtue — shifts correctly from *next-session-retries* (the
retired SDK model) to *FP-07-retries-within-one-startup + next-PROCESS-retries-on-container-restart*
(the orchestrator's job); a defensible preserve, not a silent drop. **The DUAL is complete.** The
predecessor's ① "the DUAL is incomplete for C2" is thereby RESOLVED — the only residue is the ①-OC
interface question below.

**Assessment (the contest's answer):** the over-constraint is REAL but LOW-HARM and DEFENSIBLE.
- REAL: a correct inline re-home (bounded retry + shared backoff + fail-closed, inlined) is rejected.
- DEFENSIBLE: the retry is *already* a named unit today (`_acquire_eager_lease_with_retry`), so the
  nameable helper PRESERVES a testable unit the migration would otherwise dissolve — and it is the ONLY
  way to make FP-07's SEMANTICS a runnable CHECKED variable (the alternative, an in-memory lifespan
  drive, needs the coupling-#3 heavy-build stub seam this contract does not assume; without it FP-07 is
  back to being tested only by the §6.2 wire SKIP — the exact adversary-59 ① gap).
- LOW-HARM: the compliance path is trivial (extract the loop into a named async fn — which it is today).
- **BUT it is a DESIGN decision (property-to-invent) baked into a pin with no operator ruling → per
  CLAUDE.md it must be operator-ruled before a builder proceeds.** → routes back for that ruling.

### ③ funnel-∀ (adversary-59 ③) — CLOSED at a runnable level
- correct `ToolTraceMiddleware` → `test_both_registration_paths_land_exactly_one_trace_row_each` **passed**.
- WRONG BUILD (a middleware that records only tools "known at construction") → **FAILED**:
  `funnelled ['funnel_builtin_path_tool']` — the extension-path row missing, exact FG2 message. Caught.
- HONEST BOUND (matches contract-59b): fastmcp's middleware is server-wide, so the literal
  "reached-on-built-in-but-not-add_tool" shape is architecturally hard to realize; the pin discriminates
  a FILTERING middleware ("only trace our own tools"), a plausible-wrong build. It is a runnable CHECKED
  variable (was a `pytest.skip`), belt-and-braces beneath the §6.2 wire smoke. Reach is now checked.

### SECTION B strong core — RE-VALIDATED against the REAL re-homed middleware
The whole trace-funnel section against the appended `ToolTraceMiddleware`: **24 passed** (the only
non-pass, `…installs_exactly_one_trace_middleware`, uses `built_server` — needs the full
`build_mcp_server` migration, Phase B). B2/B3/B4/B5/B6/B7/B8/T3/T6 + funnel-∀ + the 4 retry pins all
GREEN on a correct build. Spot-check discrimination: dropping `anyio.CancelScope(shield=True)` →
`…AnyioLevelTriggeredCancellation::…still_writes_its_row` **FAILED** while the asyncio sibling
`…RecordsOkFalse` + the positive control stayed **PASSED** — B4's discriminating asymmetry is real on
the migrated middleware (not only on adversary-59's build).

---

## PHASE B/C — ② injection, SECTION A, E, D6, ④, + FULL SATISFIABILITY (full reference build)

Full reference = the partial build + `build_mcp_server` migrated (ctor `FastMCP(version=…,
middleware=[ToolTraceMiddleware()])`, native FP-07 lifespan, guard dropped) + all 17
`Context[Any, AppContext, Any]` → bare `Context` + `_register_extension_tools` adapted (sync local
collision set + `mcp.tool(name=…)(wrapper)`) + `_ProcessLifespanGuard`/`_EagerStartupLifespan`/
`TracingFastMCP` DELETED + `build_asgi_app` → `http_app(path=)` + all retired-name prose scrubbed
(residue check: `TracingFastMCP`/`request_ctx`/`streamable_http_app` = 0 / 0 / 0).

### ② context injection (adversary-59 ②) — CLOSED
- correct build (bare `context: Context`) → **10 passed** across SECTION A + ② + install + E + D6
  (all 15 built-ins register; `context` absent from every published schema).
- WRONG BUILD `Context→Any` (the coupling-#1 dodge) → SECTION A **4 passed** (imports + 15 register)
  but `test_no_builtin_tool_publishes_the_injected_context_param` **FAILED**, listing **all 15
  built-ins** leaking `'context'` into their input schema. ∀-over-15 + the non-vacuity control both
  real (the assert reached the leak leg, so `saw_a_real_client_param` was True).

### ④ correction — VERIFIED FACTUALLY (the #107 read-then-verify class)
WRONG BUILD `Context` left SUBSCRIPTED (`Context[Any, AppContext, Any]`) atop the migrated ctor:
- `import loremaster.server` **SUCCEEDS** ("IMPORT OK (PEP-563 strings, not evaluated at import)").
- `test_loremaster_server_imports_under_fastmcp` **PASSES** on the broken build (2 passed).
- the `built_server`-fixture pins **ERROR** with `TypeError: type 'Context' is not subscriptable` —
  fired at TOOL REGISTRATION inside `build_mcp_server`, NOT at module load.
So the contract's corrected wording ("a tool-REGISTRATION break, NOT a module-load break; the bare-import
pin PASSES; the fixture pins discriminate") is EMPIRICALLY TRUE. No false #107-class claim remains.

### ⑤ scope/gate — enumerated + documented (reach note in §P1c)
The module docstring documents the acceptance gate as FULL-SUITE / §6.1 in-image (not collect-only),
`_MIGRATION_AFFECTED_TEST_FILES` enumerates 11 files (categorised), and
`TestTheMigrationAffectedTestFilesAreEnumerated` is a non-shrink pin. Passes on the correct build.
Reach caveat (P1c): the worklist is a HAND-LIST — gutting it 11→4 still passes the non-shrink pin (low
severity — the worklist is advisory; the real gate is the *derived* full-suite run, which runs
everything, so a dropped worklist entry does not reduce the gate's coverage).

### SATISFIABILITY RECEIPT (contract-adversary hard rule)
```
# FULL revised contract vs the complete correct reference build (FP-07 helper wired):
$ pytest tests/test_fastmcp_migration.py            -> 43 passed, 4 skipped   (47 collected)
# after ruff --select F --fix loremaster/server.py (removed 1 orphaned import):
$ pytest tests/test_fastmcp_migration.py            -> 43 passed, 4 skipped
```
The 4 skips are the wire-lane placeholders (once-per-process, wire smoke, host-origin, auth). **NO pin
RED on a correct build — NO C-DEF.** Every NEW pin (① ×4, ② ×1, ③ ×1, ⑤ ×1, res(b) ×3) goes GREEN when
the corresponding correct code exists — confirmed including the ① helper pins (green iff the helper exists).

---

## FINDINGS

### ①-OC [design-interface OVER-CONSTRAINT — route to operator/lead for a RULING]
*The defect it would introduce:* a builder who re-homes FP-07 CORRECTLY but INLINE (bounded retry in the
`lifespan=` closure, no separate module-level helper) hits 3 RED pins that are indistinguishable from the
WRONG single-shot re-home — a correct build rejected, and a design choice (nameable-helper vs inline)
baked into a pin with no operator ruling.
*Reproduction:* §PHASE-A table + §PROBES (correct-helper 4-pass; no-helper 3-fail/1-pass).
*Resolution options:* (a) **ACCEPT** (my recommendation) — keep the pins; the retry is already a named
unit today and the helper preserves runnable FP-07 coverage; the contract already carries the
"inline → escalate" note, so the imposition is explicit. (b) RELAX to a structure-agnostic behavioural
pin — NOT cheap (needs the coupling-#3 stub seam the contract disclaims), and it re-opens the FP-07
gap if it degrades to the wire SKIP. Operator rules; I recommend (a).

**No MISSING pin (under-constraint) finding.** Every adversary-59 gap is closed and every wrong build I
built is caught. The list adversary-59 said the old contract "waved through" is now empty:

| adversary-59 wrong build | revised pin that catches it | my empirical result |
|---|---|---|
| single-shot lifespan re-home (drops FP-07) | `TestTheEagerHeavyBuildRetriesTransientFailures` (helper fetch) | **3/4 RED** — caught |
| `Context→Any` injection dodge | `TestContextIsInjectedNotPublishedInTheToolSchema` | **RED** (15 tools leak) — caught |
| extension not funnelled (FG2) | `TestTheTraceMiddlewareFunnelsBothRegistrationPaths` | **RED** (`['funnel_builtin_path_tool']`) — caught |
| ④ false "module-LOAD break" claim | (correction) bare-import PASSES; fixture pins ERROR at registration | wording now TRUE — verified |
| ⑤ collect-only gate blind to runtime breaks | full-suite doc + `_MIGRATION_AFFECTED_TEST_FILES` + non-shrink pin | present; reach note in §P1c |

---

## P1b — QUANTIFIER TABLE (the NEW load-bearing pins; the 8-pin core rows are in REPORT-adversary-59)

| invariant (new) | ∀ or GUARDED | door-build receipt |
|---|---|---|
| **② context injection** | ∀ over the 15 built-ins (+ non-vacuity: ≥1 real client param) | **door built:** `Context→Any` → all 15 leak `context` → RED. Correct (bare Context) → PASS. Discriminates. |
| **③ funnel-∀** | ∀ over {`@mcp.tool` built-in, `mcp.tool(name=…)(wrapper)` extension} | **door built:** filtering middleware → `funnelled ['funnel_builtin_path_tool']` → RED. Correct → both rows → PASS. |
| **① retry comes-up** | ∀ over {K<N fail-then-succeed, all-N fail} | **door built:** no helper (single-shot) → RED; correct helper → PASS (build.calls == 3 / == budget). |
| **① budget bounded** | ∀ (value bound `1 < N ≤ 20`) | reads production `_DEFAULT_EAGER_MAX_ATTEMPTS` (=5); GREEN on correct. This is the ONE ① leg a single-shot build still passes (constant survives) — the others carry the discrimination. |
| **① routing-is-sharing** | GUARDED→discriminating (mutation, per DRY #102/#207) | **door built:** hand-rolled `asyncio.sleep(base)` (bypasses `backoff.additive_jitter`) → `seen == []` → RED, other 3 green. Proves sharing by mutation. |
| **⑤ worklist non-shrink** | GUARDED (kinds + 2 named files present) | reach is a hand-list — see §P1c (gut 11→4 still passes). Low severity (advisory list; real gate = derived full-suite). |
| **res(b) rename-sweep** | ∀ over {`TracingFastMCP`, `request_ctx`, `streamable_http_app`} (parametrized) | correct (scrubbed source, residue 0/0/0) → GREEN; pre-scrub → RED-by-design. Control `test_the_sweep_itself_fires` proves it SEES a retired name and IGNORES the live `request_context`/`http_app`. |

Every "guarded" row carries a receipt. No guarded row hides a surviving wrong build.

## P1c — REACH TABLE (per instrument the revised contract introduces/relies on)

| instrument | reach set | DERIVED or hand-list? | coverage a checked variable? | effect or proxy? | one-source / mutation | verdict |
|---|---|---|---|---|---|---|
| ① `_eager_retry_helper()` fetch | the module symbol `_eager_build_with_retry` | DERIVED (getattr at call time) | yes (absent → RAISES → RED) | EFFECT (fetches + drives the real helper) | routing pin mutates the SHARED `backoff.additive_jitter` → RED (proven) | **SAFE (empirical)** — but see ①-OC: it certifies a NAMED-UNIT structure, rejecting a correct inline build |
| ② injection reach | the 15 registered built-in tools' `Tool.parameters` | DERIVED (`await list_tools()` → `get_tool(name)`, not a hand-list) | **yes** — ∀ over registered set + non-vacuity (empty-schema build can't pass mute) | EFFECT (reads the published schema fastmcp emits) | single guard; `Context→Any` mutation reddens all 15 | **SAFE (empirical)** |
| ③ funnel reach | {built-in path, `add_tool`-adapted extension path} | DERIVED (in-memory `Client` drives each real path) | **yes** — filtering middleware → RED | EFFECT (a real recorder row per path) | single middleware; mutation-proven | **SAFE (empirical)** — mechanism-level (server-wide funnel), belt-and-braces under §6.2 |
| ⑤ worklist `_MIGRATION_AFFECTED_TEST_FILES` | 11 named test files | **HAND-LIST** | **NO** — gut 11→4 still passes the non-shrink pin (proven) | reads the literal dict | n/a | **NOTE (empirical)** — low severity: the worklist is ADVISORY; the ACTUAL gate is the *derived* full-suite run (runs everything), so a dropped entry does not shrink real coverage. The "full-suite not collect-only" rule is DOCUMENTED (prose), enforced by the build's §6.6 gate config — a test file cannot pin its own runner mode. |
| res(b) rename-sweep | retired NAMES in `loremaster.server` source only | reach = 3 hand-named strings × ONE module | partial — the NAME set is a hand-list (`_RETIRED_MCP_NAMES`); scope is `server.py` only | EFFECT (scans `inspect.getsource(server)`) | its own +/- control fires | **SAFE-with-BOUND (empirical)** — a retired name surviving in ANOTHER module (auth.py, tests) is out of reach; acceptable (server.py is the served façade surface adversary-59 res(b) targeted), but a P1c bound worth naming. |

Legs run: EMPIRICAL for the ① fetch/routing, ② injection, ③ funnel, ⑤ worklist, B4 shield (all built +
run in scratch against real code). Construction-inspection for res(b)'s +/- control (read it; the
scrubbed-build GREEN leg is empirical).

---

## RESIDUALS (each with an individual verdict)

- **`wire` pytest marker still UNREGISTERED.** Verdict: real minor gap, CONFIRMED — collection emits
  `PytestUnknownMarkWarning: Unknown pytest.mark.wire` (×5). Harmless today (self-skips), would ERROR
  under `--strict-markers`. BUILD scope (pyproject `[tool.pytest.ini_options] markers`). Already flagged
  by contract-59b res(a); re-affirmed.
- **`TracingFastMCP` prose at `server.py:2475` + the migrated-mw docstring.** Verdict: BUILD obligation,
  now COVERED — the res(b) rename-sweep reddens on it, so the build MUST scrub it (my reference build
  did; residue 0). This closes the adversary-59 residual (the plan-prose scan could not see it).
- **res(b) sweep scope is `server.py`-only.** Verdict: acceptable bound, worth naming (P1c) — a retired
  name lingering in another module is out of reach. Not a blocker (server.py is the façade surface).
- **⑤ "full-suite not collect-only" is DOCUMENTED, not PINNED.** Verdict: inherent + acceptable — a test
  file cannot assert its own runner mode; enforcement lives in the build's §6.6 gate config. Exactly what
  adversary-59 ⑤ asked for (document + enumerate). Named so the build wires the full-suite gate deliberately.
- **`_read_trace_rows` real-store leg.** Verdict: SOUND — the real-store pins
  (`TestTheMigratedSeamLandsARealRow`) are in the 43-pass run against the live TEST store (18000), so the
  `store._query(SELECT … FROM trace)` shape + the `record_trace` signature-bind close the W30/W33 hole.

---

## PROBES — full record (commands + real output)

**Environment.** `scripts/scratch_copy.sh` copy at
`…/scratchpad/adversary-59b/refbuild` — provenance ASSERTED
(`loremaster.__file__ = …/refbuild/loremaster/loremaster/__init__.py`, INSIDE the copy). `fastmcp
3.4.7`, `uvicorn`, `httpx` synced ephemerally (D4 dep). TEST store `ws://127.0.0.1:18000` OPEN. The
reference builds are DISPOSABLE scratch; every command + count below re-derives them (the patchers are
short `python3 -` scripts embedded in the run log, applied to `server.py.orig` — a `scratch_copy.sh`
copy). Python 3.14.

```
# COLLECTION (unmigrated server + fastmcp installed):        47 tests collected   (+ PytestUnknownMarkWarning ×5 = residual: wire marker)

# ---- ① FP-07 CONTEST ----
# correct: standalone helper _eager_build_with_retry appended
pytest -k EagerHeavyBuildRetries                          -> 4 passed
# no standalone helper (models single-shot OR inline-correct — pins can't tell them apart)
  test_a_transient_failure_is_retried_then_the_build_comes_up      FAILED
  test_every_attempt_failing_fails_closed_after_the_budget         FAILED
  test_the_default_retry_budget_is_bounded_and_greater_than_one    PASSED   (constant-only leg)
  test_the_inter_attempt_sleep_routes_through_the_shared_backoff   FAILED
                                                           -> 3 failed, 1 passed
# routing-not-sharing: helper hand-rolls asyncio.sleep(base) (bypasses backoff.additive_jitter)
  test_the_inter_attempt_sleep_routes_through_the_shared_backoff   FAILED  (seen == [] != [2.0])
                                                           -> 1 failed, 3 passed

# ---- SECTION B (real re-homed ToolTraceMiddleware) ----
pytest -k "TraceMiddleware or FunnelRecords or OutcomeAlwaysWins or WriteFailure or EmissionDegrades
           or CancelledDispatch or AnyioLevel or IdentityIsDeclared or ParamsHash or FunnelsBoth
           or EagerHeavyBuildRetries or AffectedTestFiles"
                                                           -> 24 passed, 1 failed (…installs… needs full build)
# ③ funnel correct                                        -> 1 passed
# ③ funnel WRONG (filtering mw)                           -> FAILED: funnelled ['funnel_builtin_path_tool']
# B4 shield-drop spot-check
  test_a_scope_cancelled_dispatch_still_writes_its_row            FAILED  (no row)
  test_a_cancelled_dispatch_records_ok_false (asyncio sibling)    PASSED
  test_positive_control_the_same_scope_uncancelled…              PASSED
                                                           -> 1 failed, 3 passed

# ---- PHASE B (full build_mcp_server migration) ----
# correct (bare Context): SECTION A + ② + install + E + D6
pytest -k "MigratedServerImportsAndBuilds or ContextIsInjected or InstalledAtTheOneFunnel
           or CollisionsAreRefused or ExtensionToolsRegister"          -> 10 passed
# ② WRONG: context: Context -> context: Any (16 sites; 15 built-ins)
  SECTION A (imports + 15 register)                               4 passed
  test_no_builtin_tool_publishes_the_injected_context_param      FAILED
      -> tools ['lore_claim_task','lore_comms',…,'lore_verify'] (all 15) publish injected 'context'
                                                           -> 1 failed, 4 passed
# ④ WRONG: Context[Any, AppContext, Any] left subscripted (unfixed)
  import loremaster.server                                        IMPORT OK (PEP-563 strings)
  test_loremaster_server_imports_under_fastmcp                    PASSED
  test_mcp_still_importable_transitively                         PASSED
  test_build_mcp_server_constructs_a_fastmcp_instance            ERROR (TypeError: type 'Context' is not subscriptable, at registration)
  test_all_fifteen_builtin_tools_register                        ERROR (same)
                                                           -> 2 passed, 2 errors

# ---- PHASE C (apparatus DELETE + prose scrub) + FULL SATISFIABILITY ----
retired-name residue in server.py:  TracingFastMCP 0 · request_ctx 0 · streamable_http_app 0
pytest tests/test_fastmcp_migration.py                     -> 43 passed, 4 skipped   (47 collected)
ruff check --select F --fix loremaster/server.py           -> 1 fixed (orphaned import)
pytest tests/test_fastmcp_migration.py (after ruff)        -> 43 passed, 4 skipped

# ---- ⑤ worklist reach (perturbation, scratch COPY of the CONTRACT) ----
_MIGRATION_AFFECTED_TEST_FILES gutted 11 -> 4 (minimal kinds + 2 named files)
pytest -k TestTheMigrationAffectedTestFilesAreEnumerated    -> 1 passed   (hand-list reach; low severity)
(contract restored to pristine after the probe)
```

Every finding + wrong build above has a reproduction in this record. The scratch reference builds +
patchers are disposable; the lead need keep nothing — the commands re-derive them.
