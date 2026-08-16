# REPORT-contract-59b — tdd Phase-1 contract REVISER for packet 59 (fastmcp 3.x migration)

brief-base v14 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4 — first thing)
- **Demanded vs. have:** `Read`/`Edit`/`Write` of the 3 contract files + `REPORT-contract-59b.md` (✓);
  lore tools (`ToolSearch "+lore"`, ✓ — used lore_get_symbol for the apparatus, plus Read/grep where
  noted); Read of the design + adversary/predecessor reports + `server.py` + `_extension_helpers` +
  `loresigil.backoff` (✓); `uv run --with 'fastmcp>=3.4,<4'` ephemeral introspection (✓ authorized, D4
  dep) to RE-VERIFY the fastmcp facts my new pins rest on; `ruff`/`ast.parse` (✓). **No blocker — the
  mission ran end to end.** RED still depends on the dep swap (unchanged from contract-59), so a green
  pytest run is not available; every new pin was verified STRUCTURALLY (ast+ruff) and its load-bearing
  mechanic verified EMPIRICALLY against installed fastmcp 3.4.7 (§EMPIRICAL RE-VERIFICATION).
- **Model attestation (brief-carried, cannot self-read):** `claude-opus-4-8` (Opus 4.8), `opus48-worker` pin. ✓
- **Tool-honesty:** one grep fallback used — the FP-07 call sites (`grep -n "FP-07\|backoff"` over
  server.py) — because it is a NON-SYMBOL textual seam (comment markers + a module-attribute usage,
  not a def), one of the three sanctioned grep cases (CLAUDE.md dogfood §3b). `lore_get_symbol` served
  the apparatus classes; the line-number drift (adversary cited migrated-build lines) is why I grepped
  the live sites. No `lore_findings` filed — the fallback is a sanctioned case, not a lore weakness.

## SUMMARY BLOCK
- state: **done — PAUSES for RE-ADVERSARY** (operator pre-approved this additive-delta; NOT operator review).
- deviations:
  1. **Residual (b) placed in `test_fastmcp_migration.py`, NOT by mutating `test_trace_telemetry.py`'s
     `_telemetry_prose_offenders`** (the adversary offered either). Reason: a retired-NAME sweep over
     live `server.py` reddens TODAY (the names are the live implementation), which would break
     `test_trace_telemetry.py`'s pass-today status; the migration file is uncollectable-until-swap and
     RED-until-migration by design, the correct lifecycle for a rename pin. `test_trace_telemetry.py`
     and `test_wire_discipline.py` are UNTOUCHED by me.
  2. **① wiring is a WIRE-GATE requirement + honest bound, not an in-memory pin.** The retry helper's
     BEHAVIOUR is a runnable unit CHECKED variable (4 pins); that the migrated LIFESPAN calls it is the
     §6.2 boot-retry leg — an in-memory lifespan drive needs the build-provided heavy-build stub seam
     (coupling #3), whose shape this contract does not assume. Stated at the class + §HONEST BOUNDS.
  3. **① imposes a design interface** (FP-07 re-homed as a nameable async retry helper). Contract
     author's right + DRY-justified (the retry is a POLICY = a function; it already IS a separate
     method today). One constant renames it. Flagged so the adversary/build can contest it.
- Packages considered: **`fastmcp` 3.4.7** — verdict **replace** (façade + trace middleware), UNCHANGED
  from contract-59 / adversary-59 (both `replace`; `mcp` `keep_with_trigger`). No NEW mechanism specified
  by this delta — the retry helper REUSES `loresigil.backoff` (existing shared policy). READ: installed
  3.4.7 signatures via ephemeral `uv run --with fastmcp` (§EMPIRICAL RE-VERIFICATION, pasted).
- Reuse ledger: **2 new test symbols, both dispositioned** (DRY ledger below) — `_FlakyBuild` (HAND-ROLLED,
  no prior heavy-build fake) + `_retired_name_hits` (HAND-ROLLED, a NEW predicate — retired NAMES, not
  the retired-PLAN phrases `_telemetry_prose_offenders` keys on; different predicate, not a clone). All
  other new helpers reuse existing seams (`_TraceRecorder`, `_make_trace_middleware`, `loresigil.backoff`).
- Graded: `ee4bced` · HEAD-at-report: `ee4bced` · **SAME** (the adversary graded `ee4bced`; the coupling
  sites in `server.py` are unchanged at my measurement HEAD).
- decisions-needed / FLAGS (for lead-59):
  1. **④ REPORT-contract-59 §0 "FIVE couplings #1" carries the SAME false "module-LOAD break" claim** →
     annotate it (lead's call — do not edit that report; the archived report should get a one-line
     superseded/corrected header). Design §5/§3-P4/§0 also frame it as a load break — the lead/build
     should annotate on kickoff (the FIX is code-side: the discriminating fixture already catches it).
  2. **Residual (a): the `wire` pytest marker is UNREGISTERED** → BUILD scope (pyproject). Exact edit in
     §FLAGS. Harmless today (the 5 `@pytest.mark.wire` tests self-`skip`), would ERROR under
     `--strict-markers`.
  3. **① design interface** (nameable retry helper) — the build implements to it; if it prefers to inline
     FP-07 in the lifespan, the interface pins bounce it (contract's right). Flag for the adversary to contest.
- receipt POINTERS: §DELTA (each revision + adversary finding) · §C2 DUAL (the completed #15–21 table) ·
  §∀-vs-GUARDED (new pins) · §EMPIRICAL RE-VERIFICATION (fastmcp probes + output) · §HONEST BOUNDS ·
  §FLAGS · §REALISM. Contract file: `loremaster/tests/test_fastmcp_migration.py` (45 pins / +9 vs 36,
  +5 test classes; strong core untouched).

---

## DELTA — each revision, citing the adversary finding (the work order)

| # | adversary finding | what I added / changed | where | RUNNABLE? |
|---|---|---|---|---|
| ① | [HIGH] FP-07 bounded-retry PRESERVE+PIN + complete the C2 DUAL | New `TestTheEagerHeavyBuildRetriesTransientFailures` (4 behavioural unit pins on the retry helper) + `_eager_retry_helper()`/`_eager_default_max_attempts()` fetch-at-call-time + `_FlakyBuild`; strengthened the once-per-process wire gate to carry the #16/#17/#19/#21-wiring legs; COMPLETED the C2 DUAL (#15–21, §C2 DUAL) | SECTION C | unit pins RUNNABLE (RED-until-build: helper absent); wiring = §6.2 wire gate |
| ② | [MOD] Context INJECTION pin (SECTION A pinned registration, not injection) | New `TestContextIsInjectedNotPublishedInTheToolSchema` — `get_tool(name).parameters["properties"]` excludes the injected `context` param, ∀ 15 built-ins + non-vacuity control | SECTION A | **RUNNABLE, no uvicorn/lifespan** (verified against 3.4.7) |
| ③ | [MOD] funnel-∀ in-memory pin (was a `pytest.skip`) | New `TestTheTraceMiddlewareFunnelsBothRegistrationPaths` — in-memory `Client` drives ONE dispatch down the `@mcp.tool` built-in path AND the `mcp.tool(name=…)(wrapper)` extension path through the REAL trace middleware; asserts exactly one recorder row PER path | SECTION B | **RUNNABLE in-memory** (verified feasible against 3.4.7; RED-until-build: real middleware absent) |
| ④ | [correction, #107-class] the "module-LOAD break" claim is FALSE (PEP-563) | Corrected the module docstring "FIVE COUPLINGS #1", the `TestTheMigratedServerImportsAndBuilds` docstring, the `test_loremaster_server_imports_under_fastmcp` comment, and the `built_server` fixture docstring — it is a tool-REGISTRATION break; the bare-import pin PASSES on the broken build; the fixture pins discriminate. Kept the discriminating fixture (only the CLAIM was wrong). | module docstring + SECTION A | n/a (wording) |
| ⑤ | [scope/gate] full-suite gate + enumerate affected files | Module-docstring rule (acceptance gate is FULL-SUITE / §6.1 in-image, NOT collect-only) + `_MIGRATION_AFFECTED_TEST_FILES` (11 entries, categorised) + `TestTheMigrationAffectedTestFilesAreEnumerated` (worklist non-shrink pin) | module docstring + SECTION H | RUNNABLE (pure-data worklist assertions) |
| res(b) | trace-prose scan misses retired NAMES (`TracingFastMCP`@2475/`request_ctx`/`streamable_http_app`) | New `TestNoRetiredMcpNameSurvivesInProductionSource` (rename-sweep, bare substrings, per-hit file:line report) + its firing/discrimination control | SECTION I | RUNNABLE (RED-until-migration by design); control verified in isolation |
| res(a) | `wire` marker unregistered | FLAGGED (pyproject = build scope; exact edit in §FLAGS) — NOT edited | — | n/a |
| CORE | 8 confirmed pins must stay intact | UNTOUCHED — verified present (grep count 8); I only ADDED classes + fixed docstrings, changed no core assertion | — | — |

---

## C2 DUAL — COMPLETED (adversary-59 ① "the DUAL must be complete for C2")

The `_ProcessLifespanGuard` + `_EagerStartupLifespan` DELETE removes SEVEN observable behaviours
(adversary P6b Stage-1 #15–21, source-grounded from the guard/lifespan docstrings, cited by symbol).
The predecessor contract adjudicated only #15. Each below now has a verdict + instrument (the full table
is also inlined in the SECTION C header comment so it travels with the code):

| # | behaviour (source: guard/eager docstrings, server.py) | verdict | instrument |
|---|---|---|---|
| #15 | heavy build runs once per process | **PRESERVE the PROPERTY** (fastmcp-native ref-counted `lifespan=`; Item 1 GO) | once-per-process wire gate (pre-existing skip, now enumerated) |
| #16 | concurrent leases REUSE one build (no 2nd probe/watcher) | **DROP** bespoke asyncio-lock lease; **PRESERVE** as the CONCURRENT observation of #15 (ref-count shares one build; spike 4-concurrent GO) | wire gate CONCURRENT leg (added to the skip's required-legs list) |
| #17 | sequential drop-to-zero → later session REBUILDS | **DROP** the mcp-SDK-specific mechanism — its referent (per-SESSION lifespan re-entry) is GONE; fastmcp holds the build for the PROCESS lifetime. **Surviving virtue** (build not torn down between sessions) native | wire gate SEQUENTIAL-SURVIVAL leg (enter stays 1 across sessions) |
| #18 | a build FAILURE is not cached; next lease retries | **DROP** the per-lease "next lease retries" mechanism (no per-session "next lease" under a process-lifetime lifespan); **transient-resilience VIRTUE PRESERVED via FP-07 (#21)** re-homed inside the lifespan | fail-closed leg of `TestTheEagerHeavyBuildRetriesTransientFailures` |
| #19 | heavy build HOISTED to process/ASGI startup (not first-connect) | **DROP** the bespoke interceptor; **PRESERVE the property** (native to `http_app()` ASGI lifespan) | wire gate EAGER-AT-STARTUP leg (counter reads 1 before first call) |
| #20 | only the `lifespan` scope intercepted; `http` delegated | **DROP** — no interceptor, so no scope-delegation to preserve; Origin/Bearer wrap `http_app()` directly (C3/C4) | §6.2 auth-composition wire gate (401/403 prove the http scope routes) |
| #21 | **FP-07 bounded retry-with-backoff for the eager build** | **PRESERVE+PIN** (design §5b-C2 rider: "FP-07 re-homes INSIDE") | `TestTheEagerHeavyBuildRetriesTransientFailures` (4 unit pins) + §6.2 boot-retry leg (wiring) |

**No spec-silent item, no operator ruling required** — every drop is a mechanism whose referent the
migration removes, with the surviving virtue preserved and pinned. FP-07 (#21) is the one PRESERVE the
predecessor missed; it is the boot-resilience the ~150-LOC DELETE must not silently drop.

---

## ∀-vs-GUARDED table (the NEW load-bearing pins — the strong core's rows are in REPORT-contract-59)

| invariant (new) | property it pins | ∀ or GUARDED | fixture forcing each fate | wrong build it kills |
|---|---|---|---|---|
| ② context injection | the injected `context` param is NEVER published in a tool's input schema | ∀ over the 15 built-ins (+ non-vacuity: ≥1 real client param seen) | `get_tool(name).parameters["properties"]` for every registered tool | the `Context→Any`/dropped-annotation dodge (registration passes; `context` leaks to the wire — adversary probe `['context','q']` vs `['q']`) |
| ③ funnel-∀ | the trace middleware is REACHED on BOTH registration paths | ∀ over {`@mcp.tool` built-in, `mcp.tool(name=…)(wrapper)` extension} | in-memory `Client` calls one tool per path; exactly one recorder row EACH | a middleware reached on the built-in path but not the `add_tool` extension path (FG2) → built-in row only |
| ① retry comes-up | a transient boot failure is RETRIED, then the build comes up | ∀ over {K<N fail-then-succeed, all-N fail} (both fates forced) | `_FlakyBuild(fail_times=2)`→returns; `_FlakyBuild(fail_times=99)`→raises after budget | a single-shot re-home (no retry): helper absent → RED; or an early-stop / unbounded loop |
| ① budget bounded | the default retry budget is bounded and > 1 | ∀ (value bound: `1 < budget ≤ 20`) | fetch the production `_DEFAULT_EAGER_MAX_ATTEMPTS` | a single-shot default (N==1) or an unbounded-in-practice N |
| ① routing-is-sharing | the inter-attempt sleep routes through the SHARED `loresigil.backoff` | ∀ (mutation) | monkeypatch `backoff.additive_jitter`, assert it fired with the base | a hand-rolled sleep / a `from…import` value-bound copy (late binding defeated) — #102/#207 |
| ⑤ worklist | the affected-file worklist keeps the collect-only-BLIND classes | ∀ over kinds {RUNTIME, SOFT-CORPSE, TOOLERROR present} | assert each class present + 2 named files | a future edit gutting the worklist to a token entry |
| res(b) rename-sweep | no retired mcp/trace NAME survives in `server.py` | ∀ over {`TracingFastMCP`, `request_ctx`, `streamable_http_app`} (parametrized) | scan `inspect.getsource(server)` per name | a stale name in code OR prose (e.g. the `TracingFastMCP`@2475 the plan-scan misses) |

**Two GUARDED→discriminating notes:** ① routing-is-sharing is GUARDED (needs the monkeypatch to engage)
but is the ONLY way to prove sharing (mutation, per DRY law) — a hand-rolled sleep passes every other
① leg; res(b) carries a firing+discrimination CONTROL (`test_the_sweep_itself_fires`) so a broken walk
cannot pass vacuously, and the control proves it IGNORES the live `request_context`/`http_app` (no
false-positive that would earn the sweep a `# noqa`).

---

## EMPIRICAL RE-VERIFICATION (read-then-verify — the fastmcp facts the NEW pins rest on)

Per the #107 law, every dependency fact a new pin rests on was RE-VERIFIED against installed
`fastmcp` 3.4.7 (ephemeral `uv run --with 'fastmcp>=3.4,<4'`), not coded from the design or the
adversary report. The load-bearing confirmations (commands + output, 2026-08-16):

- **② `Tool.parameters` is the input JSON schema; the injected `context` is EXCLUDED.**
  `get_tool("lore_search").parameters` → `{'additionalProperties','properties','required','type'}`;
  `parameters['properties']` → `['query']` (a `context: Context` param is absent) — `get_tool`/
  `list_tools` work WITHOUT a lifespan. So the ② pin needs no uvicorn/store.
- **③ an in-memory `Client` RUNS the user `lifespan=` and funnels BOTH registration paths.**
  Built `FastMCP(lifespan=<yields SimpleNamespace(write_store=recorder)>, middleware=[TraceMW()])`,
  registered a `@mcp.tool` built-in AND an `mcp.tool(name=…)(wrapper)` extension, drove
  `Client(mcp).call_tool(...)` for each → recorder rows `[{'tool':'builtin_tool'},{'tool':'bump_counter'}]`.
  The middleware reached the app_context via `context.fastmcp_context.request_context.lifespan_context`
  — the SAME accessor the SECTION B `_app_context_double` models, so the REAL middleware works with my
  lifespan shape.
- **③ `@mcp.tool(name=…)` parametrized-decorator form works** (registers under the override name) —
  the built-in path in the pin.
- **FP-07 apparatus (source, live at `ee4bced`):** `_EagerStartupLifespan._acquire_eager_lease_with_retry`
  loops `self._guard.acquire()` up to `_DEFAULT_EAGER_MAX_ATTEMPTS` (=5, > 1 = bounded), sleeping
  `backoff.additive_jitter(self._backoff_base_s)` (=2.0) between attempts, re-raising the last exception
  after the budget (fail-closed). `loresigil.backoff.additive_jitter` is the shared full/additive-jitter
  policy (tenacity-backed; imported as a MODULE for late binding — #102/#207). These are the behaviours
  the ① unit pins encode; the retry LOOP is already a separate method today, so re-homing it as a
  nameable helper is consistent, not novel.
- **rename-sweep discrimination** (isolated Python): `_retired_name_hits` sees `TracingFastMCP`, and does
  NOT match the live `request_context` on the `request_ctx` pattern, nor `http_app` on
  `streamable_http_app`.

---

## HONEST BOUNDS (stated so the adversary/build meet them deliberately)

- **① WIRING is not an in-memory pin.** The 4 unit pins prove the retry HELPER's behaviour; they do NOT
  prove the migrated LIFESPAN actually CALLS it (the D7 "defined-but-not-installed" shape). That wiring
  is the §6.2 wire gate's FP-07 boot-retry leg (a fail-then-succeed heavy build over real uvicorn →
  container comes up). An in-memory lifespan drive would need the build-provided heavy-build stub seam
  (coupling #3 — `stub_heavy_startup` must be re-homed off the deleted `_lore_eager_guard`); this
  contract does not assume that seam's shape. **Residual risk if the adversary disagrees:** an orphan
  correct helper beside a single-shot lifespan passes the unit pins; only the wire gate closes it.
- **③ is MECHANISM-level, not full-path.** It proves fastmcp's server-wide middleware funnels BOTH
  registration MECHANISMS (`@mcp.tool` + the `add_tool` adaptation) — the FG2 "does the middleware reach
  add_tool tools?" question, as a CHECKED variable at a runnable level. It does NOT drive
  `build_mcp_server` + `register_extension(CounterExtension)` end-to-end (that needs a real store/embedder
  or the stub seam). The full-path funnel-∀ is the §6.2 wire smoke (a built-in AND `bump_counter` each
  land a real trace row) — kept as the deploy-lane belt-and-braces, exactly as adversary-59 ③ asked.
- **① imposes a design interface** (a nameable async retry helper the lifespan calls). This is the
  contract author's right AND DRY-justified, but it IS a constraint on the build's structure. If the
  build has a strong reason to inline FP-07 in the lifespan, that is an escalation, not a silent bounce.

---

## FLAGS (build/lead — outside my writable set)

- **④ `REPORT-contract-59.md` §0 "FIVE couplings #1" + the design (§0/§3-P4/§5b/§9-FG-none)** frame
  coupling #1 as a "module-LOAD break / fails to IMPORT". That is FALSE (PEP-563 future-annotations →
  import succeeds; the `TypeError` fires at tool registration). The contract wording is now corrected;
  the archived predecessor report and the design should get a one-line corrected/superseded annotation
  on kickoff (LEAD — do not edit the report retroactively without a header; the design is the build's
  work order). The CODE fix is unaffected (the discriminating fixture already catches it).
- **res(a) the `wire` pytest marker is UNREGISTERED (pyproject — BUILD scope).** Exact edit:
  in `loremaster/pyproject.toml` `[tool.pytest.ini_options]`, add a `markers` entry, e.g.
  `markers = ["wire: requires a real uvicorn/TCP server (deploy/gate lane), self-skips in the unit lane"]`.
  Harmless today (the 5 `@pytest.mark.wire` tests self-`skip`), would ERROR under `--strict-markers`.
- **coupling #3 (`_auth_fixtures.stub_heavy_startup` reaches the deleted `mcp._lore_eager_guard._build`)**
  — already flagged by contract-59; re-affirmed here because the ① wiring leg + the §6.2 auth gate both
  depend on the build re-homing that stub off the deleted guard. It is on `_MIGRATION_AFFECTED_TEST_FILES`.

---

## REALISM & INDEPENDENCE (the NEW pins — per tdd-contract)

1. **Production-realistic inputs** ☑ — real tool names (`lore_search`, the `@mcp.tool` decorator + the
   `mcp.tool(name=…)(wrapper)` adaptation that IS the migration's extension path), the real
   `SurrealStore.record_trace`-bound `_TraceRecorder`, the real `loresigil.backoff` shared policy, the
   production `_DEFAULT_EAGER_MAX_ATTEMPTS` (read, not transcribed).
2. **Independent expected values** ☑ — ② asserts `context` ABSENT (the fastmcp injection contract,
   verified against installed source, not the impl's formula); ①'s attempt counts (3 for 2-fail; N for
   all-fail) are derived from the FP-07 spec, not the code; the routing pin asserts the SHARED policy
   fired (mutation), not a value the code computes.
3. **Seam / boundary coverage** ☑ — ③ exercises the REAL registration→middleware→store seam via an
   in-memory Client (both paths); ① exercises the build-callable→retry-helper→shared-backoff seam.
4. **Magnitude / sanity bound** ☐ not applicable — pure protocol/wire + retry-count logic (no derived
   numeric output); the budget bound (`1 < N ≤ 20`) is the relevant sanity guard.
5. **Shared domain conventions** ☑ — ② reads the injected-param name from `server._RESERVED_TOOL_PARAM`
   (not a magic `"context"`); ① reads `loresigil.backoff` + the production budget constant; ③ reuses the
   `_TraceRecorder` bound to the real `record_trace` signature.
6. **Hostile fixtures for rendered stored text** ☑ (unchanged) — `TestParamsHashCarriesFreeTextOnlyAsADigest`
   (strong core, untouched); the new pins do not render stored free text.
7. **Input accounting (totality)** ☐ not applicable — no new collection transform; the funnel-∀ (every
   registration path traces) is the nearest totality property and is now a CHECKED variable (③).

---

## DRY ledger (brief-base §6 — one row per NEW reusable symbol)

| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_FlakyBuild` | `lore_search "fail then succeed test double retry"` (intent); scanned `_auth_fixtures`/`_extension_helpers` for a heavy-build fake | `_StubAppContext` (a no-op, not fail-injecting); no fail-then-succeed heavy-build double exists | **HAND-ROLLED** — a call-counting fail-then-succeed async callable; no prior double injects transient failures |
| `_retired_name_hits` + `TestNoRetiredMcpNameSurvivesInProductionSource` | compared with `test_trace_telemetry._telemetry_prose_offenders` | that scan keys on retired-PLAN PHRASES scoped by telemetry token; it CANNOT see retired NAMES (adversary res(b)) | **HAND-ROLLED** — a DIFFERENT predicate (retired NAMES, whole-source, bare substring). Not a clone of policy; the two guard different classes. (Noted: a future consolidation could share a token-walker, but the predicates differ.) |
| `_eager_retry_helper` / `_eager_default_max_attempts` / `_injected_context_param_name` / `_tool_input_properties` / `_recorder_lifespan_factory` | — | fetch/read helpers over EXISTING seams (`loremaster.server` symbols, fastmcp `Tool.parameters`, a lifespan factory) | **REUSED-seam accessors** — no new policy; each fetches at CALL time so a pin fails for its own reason, never at collection (the file's stated idiom) |
| (REUSED, no new symbol) | — | `_TraceRecorder`, `_make_trace_middleware`, `_trace_middleware_class`, `loresigil.backoff`, `SurrealStoreError`, `built_server` fixture | **REUSED** — cited in the new pins |

*No PRODUCTION symbol introduced (contract writes tests only). ①'s retry helper is a BUILD deliverable
the contract NAMES via one constant; the tests REUSE `loresigil.backoff` and assert the build routes
through it (never re-implement it).*

---

## RED depends on the dep swap (carried from contract-59, unchanged)

`test_fastmcp_migration.py` imports `fastmcp` at module level → UNCOLLECTABLE until the BUILD's D4 dep
swap (`"fastmcp>=3.4,<4"` + `uv sync`), a DIFFERENT state from RED. After the swap, the new pins reach
unbuilt LORE symbols (the trace middleware, the retry helper) at CALL time, so each fails for ITS OWN
reason, never at collection. res(b)'s rename-sweep is RED-until-migration BY DESIGN (the retired names
are live in `server.py` today). Structural verification I ran: `ast.parse` OK · `ruff check` **All checks
passed** · strong core present (grep count 8) · the pure-Python NEW logic (rename-sweep control,
worklist assertions, `_FlakyBuild` counts) verified in isolation · every fastmcp mechanic the new pins
rest on verified against installed 3.4.7 (§EMPIRICAL RE-VERIFICATION).

---

## Bottom line for the RE-ADVERSARY

This is an ADDITIVE delta: +9 pins (② injection, ③ funnel-∀, ① ×4 retry, ⑤ worklist, res(b) ×2),
the C2 DUAL completed (#15–21), the ④ false-claim corrected, the ⑤ full-suite gate documented, and the
8-pin strong core UNTOUCHED. Attack surface for the re-adversary: (a) is ①'s retry-helper interface too
prescriptive, and does the wire-gate wiring leg genuinely close the orphan-helper gap? (b) does ③'s
mechanism-level pin miss a wrong build that registers extensions OFF the server-wide funnel (the full
path is the §6.2 smoke)? (c) is res(b)'s rename-sweep going to false-positive on legitimate historical
prose (threat-model tradeoff)? (d) does ②'s `Tool.parameters` read hold for every built-in (all 15
verified to register; the schema accessor verified on `lore_search`). PAUSES here for the re-adversary,
NOT operator review (operator pre-approved this additive delta).
