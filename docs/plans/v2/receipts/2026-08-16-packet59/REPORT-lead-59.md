# REPORT-lead-59 — packet 59 build (fastmcp 3.x migration)

lead-base v6 read
brief project v7 read

## SUMMARY BLOCK
- state: **DONE — packet 59 SHIPPED + live-verified.** Migration committed `130fa16`; image `a8daccf`
  (`:latest`, rollback anchor `pre-59-rollback`); lore-lore RECREATED on it (LORE_ALLOWED_HOSTS=*,
  LORE_VERSION=130fa16), **live wire smoke PASSED** (lore_index round-trips; git_ref 130fa16; trace
  middleware recording; no 421). in-image conformance PASSED (provenance clean; all migration+wire pins
  green in-artifact; +37 image-vs-host = benign source-scan/host-tooling artifacts, comm-diff verified).
- Verdicts acted on: spike `ee4bced`→HEAD SAME · adversary pass1/pass2 `ee4bced`→SAME · coldaudit/
  security/blindread graded working-tree over `ee4bced`→SAME. **No STALE acted on.**
- Directives: 0 ledger / 3 wake (sidecar: F2/F3 forks · ①-OC fork · this) / 0 prose-duplicated.
- Rulings: **all in committed artifacts / 0 body-only** — D1–D4 (`aad58e8`); ①-OC ACCEPT (lore decision
  `33f708fe` + commit `130fa16` msg); hardening rulings (lore decision `30e56ac8` + `130fa16`).
- Agents: **13 spawned / 13 ledger-retired / 0 left-running** (fable-sidecar-59[+59b], spike-59, sweep-59,
  contract-59[+59b], adversary-59[+59b], builder-59[+59b], coldaudit-59, security-59, blindread-59).
  ⚠ discovered a PRE-EXISTING cross-packet orphan `builder-harden-47a` (packet 47a, already committed/done) —
  out of pkt59 scope; flagged to operator, not reaped.
- Uncommitted at stop: **0** (migration `130fa16`; conformance fix `24c1863`; reports archived; INDEX logged).
- Findings filed: #381 (F1 transport_session, FIXED) · #382 (conformance harness: thread-explosion false-green
  FIXED `24c1863`, +2 harness gaps open) · #383 (index 5000-stmt cap: test_comms_tool.py un-indexable, open).
  Resolved: #184 (03b's swap-bound, discharged by 59). Deviations: none material (all audit findings closed or filed).

## ①-OC RULED: ACCEPT (operator, 2026-08-16) → CONTRACT SUFFICIENT
Operator ruled ACCEPT — keep the named-helper FP-07 pins. FP-07 re-homes as a NAMED module-level
`_eager_build_with_retry` (NOT inline); the pin forbids a regression from today's named
`_acquire_eager_lease_with_retry` into an anonymous closure, and is the only runnable unit-level check
for FP-07 + the #102 routing-is-sharing mutation proof. Deliberate C-DEF exception (a correct-inline build
reddens 3 pins), legitimate per the routing-is-sharing invariant; explicit "inline→escalate" note +
re-open trigger (coupling-#3 lifespan-stub supports unit-level fault-driven retry → revisit). Durable:
`lore_recall("fastmcp migration")` (decision 33f708fe). Contract v2 is SUFFICIENT as-is — no further cycle.

## BUILD launched (builder-59, Opus 4.8) — task `4bf2d7d8…`
GREEN phase. Implementation guide = REPORT-adversary-59b §PHASE-B (the adversary's CORRECT reference
migration, 43/4). Steps: D4 dep swap → RED → migrate server.py (imports incl. prod ToolError; ~16
Context[...]→Context; TracingFastMCP→ToolTraceMiddleware, _record_tool_trace REUSED M4; ctor version=/
middleware=; DELETE apparatus, FP-07 named-helper re-home; P9 sync guard; add_tool→mcp.tool()(wrapper);
http_app(path=)+host_origin_protection+allowed_hosts; scrub prose) → fix ~8-10 test files +
_auth_fixtures.stub_heavy_startup → build migration_wire fixture (unskip §6.2) → register wire marker →
FULL-SUITE green + typecheck + ruff + --currency + zero-new-delta collection. Gate FULL-SUITE, not
collect-only. Then: cold audit (fresh Opus 4.8) → standalone deploy (in-image #139 + real uvicorn wire smoke).
Deploy is pre-authorized (pre-production status). Next operator report: post-cold-audit.

## BUILD DONE-with-deviations (builder-59, Opus 4.8) — 2026-08-16, `REPORT-builder-59.md`
Migration built + self-proven. **4462 deletions / 1235 insertions across 20 files.** `_ProcessLifespanGuard`
/`_EagerStartupLifespan`/`TracingFastMCP`/`_lore_eager_guard` GONE; `_eager_build_with_retry` (EXTENDED,
routes shared backoff) + `ToolTraceMiddleware` (calls REUSED `_record_tool_trace`) + `http_app`+
`host_origin_protection` in. Contract `test_fastmcp_migration.py` 43/4; wire fixture `test_migration_wire.py`
8/8 real uvicorn; 2 mutation proofs RED-on-mutation/restored. **ZERO-NEW-DELTA proven rigorously** (migrated
459f/9837p vs `git-stash` HEAD baseline 448f/9907p → `comm -23` = exactly 11 new nodes; 9 FIXED, 2 LEFT in
pending-39; tree restored byte-exact). Build PRESERVED at `scratchpad/pkt59-build-backup/` (6880-line patch +
2 untracked). NOT committed (cold-audit-before-commit; lands as the GREEN commit after GO).
⚠ My earlier "ToolError is a prod swap in server.py" refinement was WRONG — builder verified server.py has
only 2 PROSE mentions, no import (I grepped a string without confirming an import; the design's "(tests)"
label was right). Lesson logged.

### Builder FLAGS to adjudicate (post-audit):
1. **2 residual NEW failures in pending-39 files** (`test_auth_composition`/`test_auth_identity_seam` reach
   `mcp.settings` in their test code; green@HEAD, broke on the swap). LEFT per writable-set — they still
   COLLECT (D4 met); packet 39 re-authors. Fix is trivial (`mcp.settings.auth`→`mcp.auth`) IF we grant scope.
   Lean: LEAVE (pending-39, collect OK) — surface to operator per flag-failures rule.
2. **--currency gate RED — none is builder's code:** the spike script `scripts/fastmcp_migration_spike.py`
   19 mypy (LATENT at HEAD; the dep swap made mypy analyse it against real fastmcp → surfaced) — **MY
   committed instrument, I must fix/register**; contract `test_fastmcp_migration.py:163` no-any-return (needs
   a `cast` — contract touch-up); 4 pre-existing pytest orphans (RED at HEAD, other owners).
3. **`allowed_hosts` = env knob `LORE_ALLOWED_HOSTS`**, not a `ServerConfig` field — the DEPLOY must set it
   for the nginx-ingress topology or prod 421s. (security-59 assessing fail-open/closed default.)
4. **⚠ DROPPED secret-non-leak boot behaviour** (DUAL gap): deleted `_EagerStartupLifespan` used a FIXED
   phrase on boot failure (never `str(exc)`) so a credentialed `surreal.url` couldn't leak into uvicorn's
   boot log; `_eager_build_with_retry` re-raises → potential unredacted leak on total boot failure. Builder
   recommends ACCEPT-with-trigger → **security-59 rules; likely operator-surfaced.**
5. P9: no `on_duplicate="error"` backstop (sync universe check is the discriminating mechanism; redundant
   backstop risks a boot failure on an unproven legit dup). ACCEPT — deliberate.

## PHASE-7 AUDIT launched (2026-08-16) — Opus 4.8 ×3, parallel
- coldaudit-59 (task `7f8d4eae…`): re-run all gates + REPRODUCE zero-new-delta (scratch-copy baseline, not
  real-tree stash) + diff read + deletion reconciliation + flags. GO/NO-GO.
- security-59 (task `bba680ee…`): host_origin_protection/allowed_hosts + auth composition + FLAG-4 ruling.
- blindread-59 (task `010f7363…`): contract-blind diff read (PR93) — dropped behaviour the contract can't see.
Agents: builder-59 retired. ACTIVE: coldaudit-59, security-59, blindread-59, fable-sidecar-59b. Next report:
audit verdicts (GO ⇒ commit + standalone deploy; NO-GO ⇒ route findings back).

## PHASE-7 RESULTS (2 of 3 done; coldaudit-59 running) — VERDICT: NO-GO → FIX-WAVE
- **security-59: GO** (`REPORT-security-59.md`) — no HIGH/CRITICAL; fail-safe posture correct; **flag-4
  ACCEPT-with-trigger SOUND (LOW)**. 2 LOW hardenings (F1 reject userinfo in surreal.url; F2 validate
  LORE_ALLOWED_HOSTS + reject literal `*`). security-59 retired.
- **blindread-59: found the defect the pipeline missed** (`REPORT-blindread-59.md`, blindness intact —
  the PR93 lesson, live). Retired.
  - **F1 [HIGH, lead-CONFIRMED] → MUST FIX.** Migrated trace middleware `get_http_headers().get("mcp-session-id")`
    is ALWAYS None — fastmcp strips `mcp-session-id` (dependencies.py:447). `transport_session` written NULL
    every row (silent telemetry regression) + the docstring LIES ("measured"). Finding #381. FIX:
    `get_http_headers(include={"mcp-session-id"})`; fix docstring; **CONTRACT GAP** — add a wire pin that a
    real HTTP session records transport_session non-None. ⚠ Partly MY brief's error (I named get_http_headers).
  - **F2 [MED]** — the boot-failure redaction dropped BOTH halves (the redacted operator diagnostic
    `logger.error(exc_info=)` AND the fixed-message re-raise). Fix: restore both in `_eager_build_with_retry`
    exhaustion. Resolves flag-4/F2 at the source.
  - **F3 [LOW-MED]** — new `_record_tool_trace` derefs `fastmcp_context.request_context.lifespan_context`
    but `.request_context` can be None → loud `trace.emit.failed` where base logged quiet DEBUG. Guard it.
  - **F4 [LOW]** collision guard narrowed to loop-local set (safe: 1 call site, 2 paths). **F5 [LOW]** stale
    `mcp.server.fastmcp` prose at server.py:1005-1013 (scrub). **F6 [NOTE]** host_origin_protection new 421
    surface (intentional; deploy must set LORE_ALLOWED_HOSTS). Central assumption (once-per-process) —
    spike already proved it; in-image gate re-confirms.
- **coldaudit-59: GO-with-R1** (`REPORT-coldaudit-59.md`). Retired. Zero-new-delta REPRODUCED independently
  (migrated 450 / baseline 448 failed → Δ = the 2 adjudicated pending-39 nodes); B1-B8 preserved (diff read);
  FP-07-routing + B4-shield mutation proofs RE-VERIFIED against the delivered tree; migration_wire 8/8.
  RED_ORPHANED=4 (all pre-existing at HEAD). NEW findings:
  - **R1 [MODERATE, builder-missed] → MUST FIX.** C5/FG8 transport MODE: `http_app()` sets no
    `stateless_http=` → inherits fastmcp's default (stateful today, but overridable by `FASTMCP_STATELESS_HTTP`);
    AND no GREEN pin asserts the mode (the §6.2 mode pin at `test_fastmcp_migration.py:1598` is a skip;
    `test_migration_wire.py` omits the session-id/mode assert). Benign today, fragile forward — the exact FG8
    C5 exists to close. FIX: `stateless_http=False` explicit + a session-id-minted wire assert.
  - **N1 [note]** — builder's cited "restored byte-exact" server.py md5 (`89eb7e9`) matches NEITHER the
    delivered tree (`0a84eb31`) NOR HEAD — receipt mis-transcribed or a post-receipt edit. coldaudit correctly
    re-verified the DELIVERED tree independently (didn't trust the receipt). Not a code break; a receipt-integrity flag.
  - Corroborates flag-4 (real DUAL gap; ACCEPT-with-trigger reasonable). ⚠ coldaudit marked B7-correlator
    "✓ no crash" — but that is blindread-F1 (the value is always None); no-crash ✓ ≠ correct-value. Complementary lenses.

## CONSOLIDATED VERDICT: NO-GO for commit → FIX-WAVE (then re-verify) — 2026-08-16
**Must-fix before commit:**
1. **blindread-F1 [HIGH]** — `get_http_headers(include={"mcp-session-id"})` (restore transport_session) + fix
   docstring + a wire pin asserting transport_session recorded non-None over a real HTTP session (contract gap).
2. **coldaudit-R1 [MOD]** — `stateless_http=False` explicit in `http_app()` + a session-id-minted/stateful wire pin (contract gap).
   (F1 + R1 are both wire-pin gaps → close in `test_migration_wire.py` AND un-skip the contract §6.2 pins by wiring the fixture.)
3. **blindread-F2 [MED]** — restore BOTH redaction halves in `_eager_build_with_retry` exhaustion (redacted
   `logger.error(exc_info=)` via lore's sink + a fixed-message re-raise). Supersedes flag-4.
**Should-fix (same wave, cheap):** blindread-F3 (guard `request_context` None deref) · blindread-F5 (scrub stale
`mcp.server.fastmcp` prose server.py:1005-1013) · currency cleanup (spike script's 19 mypy = MY committed
instrument; contract:163 `cast`).
**Ledger/accept (no fix):** F4 (collision-guard narrowing — safe in practice) · N1 · flag-4 (ACCEPT, superseded by F2) · F6.
**HARDENING DECISIONS → operator** (security LOWs; adopt-in-59 vs defer-to-39): security-F1 (reject `user:pass@`
in surreal.url) · security-F2 (validate LORE_ALLOWED_HOSTS + reject literal `*`) · LORE_ALLOWED_HOSTS as a
validated ServerConfig field (bigger, config-schema).
**Plan:** ONE fix-wave builder (builder-59b, Opus 4.8) does the code fixes + the 2 wire pins + approved
hardenings; then a FOCUSED re-verify (re-run wire suite + currency + changed suites + confirm zero-new-delta
unchanged + a targeted re-read/re-blindread of the F1/F2/R1 hunks). All 3 auditors retired; ACTIVE: fable-sidecar-59b only.

## OPERATOR HARDENING RULINGS (2026-08-16) + FIX-WAVE LAUNCHED
Rulings (`lore_recall("fastmcp migration")` decision 30e56ac8): **ADOPT security-F1** (reject `user:pass@`
in surreal.url) · **KEEP wildcard** — do NOT reject `LORE_ALLOWED_HOSTS=*`; operator wants allow-all-Host as
a supported config ("we want wild card access") → fix-wave PINS `*`=allow-all as deliberate (default stays
protective) · **NO** ServerConfig-field promotion (keep env knob). RE-OPEN: first off-fleet consumer.
**builder-59b launched** (task `249cee72…`) — 8 items: F1/R1/F2 (must-fix) + F3/F5/currency (cheap) +
security-F1 (adopt) + wildcard pin. ACTIVE: builder-59b + fable-sidecar-59b.
⚠ **DEPLOY landmine (MEMORY.md):** lore-lore has a HAND-ROLLED /source mount, NOT restart-durable — the
standalone deploy is a MANUAL rebuild+recreate, NOT `lore-deploy start` (until #165/#166). + set
`LORE_ALLOWED_HOSTS` per the wildcard ruling at deploy. Capture `podman inspect` CreateCommand before rm.

### FIX-WAVE plan (after coldaudit-59): builder-59b (suffixed)
Fix F1 (code+docstring) + a CONTRACT touch-up (transport_session wire pin — contract reviser) · F2 (restore
both redaction halves) · F3 (guard request_context) · F5 (scrub prose) · the currency cleanup (the spike
script's 19 mypy = MY committed instrument; contract:163 cast). Then re-verify (targeted re-audit incl. a
re-blindread of the F1/F2 hunks). HARDENING DECISIONS to consolidate for the operator: security F1 (reject
userinfo), F2 (validate LORE_ALLOWED_HOSTS + reject `*`), F4 (ledger the collision narrowing), F6/allowed_hosts
deploy config. flag-4 = ACCEPT (security-ruled) but F2's redaction restore supersedes it anyway.

## RE-ADVERSARY PASS 2 — INSUFFICIENT (narrow) — 2026-08-16, `REPORT-adversary-59b.md`
Empirical (partial + full reference builds, 6 wrong-build probes). **②③④⑤ all CLOSED** (each wrong build
now reddens; ④ #107-class wording verified TRUE — import succeeds, TypeError at registration; C2 DUAL
verified complete #15–21). **Satisfiability: 43 passed / 4 skipped on a correct reference build (FP-07
helper wired), no NEW pin RED → NO C-DEF.** Strong 8-pin core still discriminates (B4 shield spot-check).
- **ONE finding — ①-OC [design-interface OVER-constraint, needs operator ruling]:** the ① pins force a
  NAMEABLE module-level `_eager_build_with_retry`; a CORRECT inline re-home (retry in the `lifespan=`
  closure) fails 3/4 retry pins, byte-identical to the WRONG single-shot. Reviser flagged it; adversary
  confirmed + recommends **ACCEPT** (retry is already a named unit today; the helper is the ONLY runnable
  unit-level FP-07 check incl. routing-is-sharing; relaxing needs the coupling-#3 stub seam or degrades
  to the §6.2 wire SKIP → re-opens the gap). If operator rules ACCEPT → contract SUFFICIENT as-is → BUILD.
  → sidecar consulting (SendMessage); then operator ruling. ⑤ reach note: `_MIGRATION_AFFECTED_TEST_FILES`
  is a HAND-LIST (low severity — the real gate is the derived full-suite run).
- Contract v2 (`REPORT-contract-59b.md`): ① FP-07 retry pins + C2 DUAL complete · ② Context-injection
  in-memory pin · ③ funnel-∀ in-memory pin · ④ #107-class claim corrected (REPORT-contract-59 annotated) ·
  ⑤ full-suite gate + `_MIGRATION_AFFECTED_TEST_FILES` (11) + non-shrink pin. Flagged to re-adversary:
  ① imposes a named-retry-helper interface (contest over-constraint). Re-adversary task `7e3068e2…`.
- Uncommitted at stop: `REPORT-*.md` (this report + spike/sweep/fable readiness) — reports, archive at close-out.
- decisions-needed: none blocking (operator pre-approved the contract; see directives).

## Operator directives (2026-08-15, mid-build) — durable
1. **Reap only DONE agents (window pressure).** spike-59, sweep-59 TaskStopped + comms-retired.
   ⚠ CORRECTION (operator): the **Fable sidecar is NOT reapable — it is a STANDING consultant for the
   WHOLE packet, consulted for every fork/design decision.** It was errantly reaped and re-spawned as
   **fable-sidecar-59b** (suffixed per no-name-reuse). Do not reap it until packet close-out.
2. **Contract is PRE-APPROVED — skip the operator-review pause; on contract-59 done, go STRAIGHT to
   the contract-adversary.** The lead verifies the contract is complete (satisfiability, DUAL
   adjudication, ∀-table). **Design forks (P9 collision policy, test_wire_discipline rewrite-vs-delete,
   Origin defense-in-depth keep, sizing/split) are CONSULTED WITH fable-sidecar-59b** (framing +
   recommendation) — the lead does NOT decide design solo. Genuine property-to-INVENT forks still
   escalate to the operator; the sidecar frames, the operator rules. Only the routine review pause is waived.

## Launch (2026-08-15, HEAD `faa68b2`, session pkt59)
Operator ruled at kickoff: **launch the build now** + **run the deferred 7-file doctrine sweep in parallel**.
Index current (root `/workspace` @ `feat/surreal-unification` `faa68b2`; last sweep ~5m; no session edits → no reconcile).

Fleet task ledger (`lore_tasks`):
- spike  `8af4c2888cdf48078cc5f8eaf5d94ae0` — §6.6 migration spike (prereq of contract) → owner spike-59
- sweep  `2b171dca467845a4b77befcff2a8f6ff` — deferred doctrine sweep → owner sweep-59
- contract `f137cc86e9d44a57bb1c72fc482cd695` — CONTRACT (blocked_by spike)

Roster: Opus 4.8 end-to-end via `opus48-worker` (the confirmed fresh-context 4.8 subagent; no per-call
model override). Fable sidecar = `general-purpose` + `model: fable` (kickoff §4: general-purpose, never a fork).

## Lead ground-truth (read-only, pre-contract) — 2026-08-15 @ `faa68b2`
- **D4-a CLEAR:** `grep` of `loremaster/loremaster/` finds NO `mcp.cli` / `mcp.server.fastmcp.cli`
  imports → the bare transitive `mcp` (no `[cli]` extra) covers prod. (Grep is honest here: non-symbol
  textual seam — dogfood protocol case b.)
- **D4 Containerfile NO-EDIT:** `Containerfile` COPYs the 4 workspace members + `pyproject`/`uv.lock`;
  `mcp` appears only in comment lines (14/85/187). No `EXPECTED_MEMBERS`/`COPY` names `mcp`; `fastmcp`
  is an external dep, not a workspace member, so `conformance_provenance.py::EXPECTED_MEMBERS` and
  `registration_sites.py` are unaffected. (Cosmetic: Containerfile comment line 14/85 lists `mcp` among
  drift-prone deps — after swap `fastmcp` is the new top-level; comment refresh optional, not a gate.)
- **Coupling symbols CURRENT at HEAD** (design read at `41287c5`; symbols exist at `faa68b2`, lines drifted):
  `_ProcessLifespanGuard:9853`, `TracingFastMCP:9959`, `call_tool:10002`, `_record_tool_trace:10032`,
  `build_mcp_server:10156`, `_mcp_server.version:10272`, `_lore_eager_guard:10278`,
  `_tool_manager.get_tool:12078` (P9 hard-break), `_EagerStartupLifespan:12256`, `build_asgi_app:12498`,
  `streamable_http_app:12527`, `_lore_eager_guard` getattr:12533.
- **11 test files import `mcp.*`** (matches blast-radius §1b): `_auth_fixtures`, `test_auth_composition`,
  `test_google_token_verifier`, `test_hosted_readonly_posture`, `test_mcp_server`,
  `test_mutating_set_derivation`, `test_permission_resolver_seam`, `test_refusal_observes_effect`,
  `test_schema_rebuild`, `test_tool_allowlist`, `test_trace_telemetry`. (The packet-39 committed-RED set
  is inside this list — the contract must NOT re-author those; only `test_trace_telemetry` + the AST
  `test_wire_discipline` are 59's per design §4.)
- **REFINEMENT to the design coupling table:** `ToolError` appears in **`server.py` (PRODUCTION)** +
  6 test files (`test_hosted_readonly_posture`, `test_mcp_server`, `test_permission_resolver_seam`,
  `test_schema_rebuild`, `test_tool_allowlist`, `test_trace_telemetry`). The design's P-table labeled
  `ToolError` "(tests)" and estimated "~4 test files" — actual is server.py (prod) + 6 tests = 7 sites.
  **The `ToolError` import swap is a production change in `server.py`, not test-only.** The contract owns it.

## Sidecar readiness (fable-sidecar-59, warm 2026-08-15) — 6 pre-framed forks to consult
Recorded for pull at the right phase (do NOT double-drive it; it idles between questions):
- F1 lifespan-DELETE spike instrument + a hidden 3rd option → **spike-59 settling now (§6.6-1)**
- F2 FG1 needs a positive "build ran" observable → **spike-59 settling now (§6.6-1 oracle)**
- F3 trace-funnel ∀ safe-set — is `{tool, add_tool}` complete in fastmcp 3.x? → **spike/contract (FG2/§9 reach)**
- F4 wire-discipline DELETE-vs-rewrite + P9 collision-policy → **consult at CONTRACT time**
- F5 split-vs-D1-STANDALONE tension → **consult at CONTRACT/sizing time (§12 sizing law)**
- F6 #355 re-embed downtime → **consult at DEPLOY time (D1 §11)**

## Deferred doctrine sweep — DONE + APPLIED (2026-08-15)
sweep-59 (Opus 4.8) delivered `REPORT-sweep-59.md`: 2 contradictions · 3 inconsistencies · 2 gaps ·
staleness clean. Operator ruled: **apply all 7 + the I2 structural fix.** Applied:
- **C1** package-scout verdict tokens → shared closed set (`replace/replace_with_adapter/keep_with_trigger/bespoke`) + summary-table gloss.
- **C2** escalate-valence reconciled: brief-base §6 "escalation resolves into the shared home"; lore lorerunes bullet names brief-base §6 as its resolution.
- **I1** docs-only read insufficient for a `bespoke` verdict — caveat added to brief-base §1, tdd-contract, package-scout (the #107 law).
- **I2** ROUTING-IS-NOT-SHARING restored to global CLAUDE.md ONE-IMPLEMENTATION; **+ structural fix** — lore CLAUDE.md copy now POINTS at global + keeps only lore-specific #102/#120 receipts (kills the drift that lost the clause).
- **I3** tenacity jitter-class caveat (global CLAUDE.md).
- **G1** `EXTENDED <sym>` DRY-ledger disposition (brief-base §6).
- **G2** delete-the-twin check on an acted-on `replace` (lead-base commit check).
Commit: **`1f8229f`** (in-repo `CLAUDE.md`). 6 edits to untracked `~/.claude/*` (global standing law,
not version-controlled). Verified: no residual old package-scout tokens; diff coherent. sweep-59 retired.
sweep task `2b171dca…` done. `REPORT-sweep-59.md` to be archived at close-out.

## spike-59 (critical path) — running, all-GO per heartbeat (report not yet delivered)
Heartbeat note 2026-08-15: "4 identical runs, all 3 items GO. Item3 body=Misdirected Request(421).
No server.py/auth.py drift 41287c5..faa68b2." Report + `scripts/fastmcp_migration_spike.py` on disk.

## spike-59 — DONE + LEAD-VERIFIED (2026-08-15) — ALL 3 GATES GO
`REPORT-spike-59.md` read; harness read (honest: real uvicorn/TCP, pos+neg control per item, oracle
counters, correct verdict predicates). **Lead re-ran the harness independently — all 3 GO reproduced**
(even on py3.14 vs the spike's py3.12; fastmcp 3.4.7 / mcp 1.29.0). The Item-1 `RuntimeError` in output
is the negative control firing as designed (naive middleware eats lifespan → loud fail → caught).
- **Item 1 GO** — fastmcp enters `lifespan=` exactly once/process (enter==1 across 4 seq + 4 concurrent
  wire sessions, all boot-1; exit==1; pos-control 2nd lifecycle→boot-2; neg-control naive→delta 0).
  ⇒ pin the **~150-LOC `_ProcessLifespanGuard`+`_EagerStartupLifespan`+`_lore_eager_guard` DELETE**;
  heavy build → `lifespan=`, FP-07 retry re-homed inside. BONUS: mis-wired lifespan fails LOUD at first
  WIRE request (not silent) — a safety net, NOT a substitute for §6.1/§6.2.
- **Item 2 GO** — `host_origin_protection` runs BEFORE the `TokenVerifier` (bad Origin+valid token →
  403, verify_token_calls==0; source: `HostOriginGuardMiddleware` inserted at index 0, auth at route
  endpoint). ⇒ R9 "zero-outbound" ordering satisfied NATIVELY; no bespoke-outermost fallback required.
- **Item 3 GO** — enabled guard rejects spoofed Host (421); OFF accepts (today's gap). ⇒ bank the
  Host/DNS-rebinding rejection.
- **⚠ BUILD-TIME CONFIG RIDER (carry to contract + deploy, NOT a fork):** `host_origin_protection`
  default is **OFF**; the migration MUST pass `host_origin_protection=True`/`"auto"` AND set
  `allowed_hosts` for lore's real topology (TLS terminated upstream by nginx-ingress, `auth.py:13`) or
  it 421s legit prod traffic. Acceptance (§6.1/§6.2) MUST assert a legit proxied Host passes.
Harness committed `ee4bced`. spike-59 retired. Task `8af4c2…` done. `REPORT-spike-59.md` → archive at close-out.

## CONTRACT phase — launching contract-59 (Opus 4.8); PAUSES for operator review
Design doc is the work order; spike GO results + config rider + lead ground-truth (ToolError-in-prod,
D4-a clear, Containerfile no-edit) folded into the brief. Contract author re-verifies all fastmcp 3.x
API facts against installed source (§0 scope) before pinning. Genuine design choices (P9 collision
policy, test_wire_discipline rewrite-vs-delete) surface as decisions-needed for operator review.

## CONTRACT DONE + verified (contract-59, Opus 4.8) — 2026-08-15
`REPORT-contract-59.md`: 36 pins in `test_fastmcp_migration.py` + re-authored `test_trace_telemetry.py`
(funnel excised → File 1; M4 write-policy kept) + `test_wire_discipline.py` tombstone. Full package
survey, adversarial pre-flight, ∀-vs-GUARDED table, DUAL adjudication (every B/C/D → verdict), realism
checklist, DRY ledger. **Lead re-measured: ruff clean + all 3 compile** (SAME as its claim). Committed?
NO — in working tree for the adversary; commit as RED baseline WITH the dep swap when the contract is
final (test_fastmcp_migration.py is uncollectable-until-swap; committing it now would redden collection).
- **§0 re-verify caught 5 couplings the design P-table omitted** — biggest: `Context[Any,AppContext,Any]`
  is NOT subscriptable in fastmcp → ~16 `server.py` sites are a module-LOAD break (bare `Context`);
  `add_tool` is single-arg (adapt via `mcp.tool(...)(wrapper)`); `_auth_fixtures.stub_heavy_startup`
  reaches the DELETED `_lore_eager_guard` (build must supply a new stub hook); P9 check is sync vs
  fastmcp's async `get_tool`; `_record_tool_trace` home moves (write policy preserved). All build-scope.
- Probe scripts left at /tmp (disposable) — NOT committed: the 5 couplings are captured as contract
  PINS and the probe output is pasted verbatim in the contract report (brief-base §1 satisfied).

## ADVERSARY launched (adversary-59, Opus 4.8) — grading before build; PRE-APPROVED cycle
Task `c17a144a…`. Attack targets: funnel-∀ reach (built-in vs add_tool), P9 disabled-name leg,
B4 anyio shield, `_read_trace_rows`/`_query` shape; P6b two-stage deleted-code enum; satisfiability
receipt vs a reference build. SUFFICIENT → build. INSUFFICIENT → fresh reviser (contract-59b).

## ADVERSARY PASS 1 — INSUFFICIENT (strong core, 5 actionable gaps) — 2026-08-15, `REPORT-adversary-59.md`
Empirical: full reference build (`scratch_copy.sh` + AST patcher, provenance asserted), contract vs it =
**32 passed / 4 skipped, no C-DEF** (holds after ruff --fix); 8 wrong-build probes ALL caught (B4 shield,
P9 disabled-name, D6, D7, B7×2, T6, Context-registration). `_read_trace_rows`/`_query` = SOUND (real-store
legs landed a row). Gaps routed to the reviser (task `9ca1d6f2…`):
- **① [HIGH] FP-07 bounded-retry** deleted with the apparatus, no pin + no ruled-DROP (DUAL incomplete for
  C2); fastmcp `lifespan=` doesn't retry → single-shot re-home passes every pin, drops boot resilience.
- **② [MOD] Context injection** — SECTION A pins registration not injection; `Context→Any` dodge passes all
  4 SECTION-A pins but leaks `context` into every tool's inputSchema. In-memory Client pin fixes it.
- **③ [MOD] funnel-∀** over {built-in, add_tool ext} is a SKIP; adversary proved it works in-memory → make
  it a runnable checked variable.
- **④ [correction, #107-class] "module-LOAD break" claim is FALSE** — `server.py` has `from __future__
  import annotations` (PEP-563), so import SUCCEEDS; the TypeError fires at tool REGISTRATION. Defect still
  caught (fixture ERRORs); only the CLAIM/docstrings are wrong (+ REPORT-contract-59 §0 — lead annotates).
- **⑤ [scope] ~8–10 test files touched, not 2** (`_tool_manager`→`_local_provider`, mock-patched deleted
  symbols); §6.6 collect-only gate is BLIND to the runtime breaks → gate must be full-suite/in-image +
  enumerate the files. **Effort ~4× the design's test-surface estimate — surfaced to operator (heads-up).**
Re-adversary task `7e3068e2…` (blocked by the revision). adversary-59 reaped/retired.

## Design forks → sidecar (fable-sidecar-59b, SendMessage 2026-08-15)
Sent for framing (do not decide solo): (1) LF-A Origin defense-in-depth keep-both-vs-dedup (SPEC-SILENT
per §5b — may be a genuine operator ruling); (2) P9 policy (contract recommends public/sync + universe
check); (3) test_wire_discipline fate (contract recommends tombstone). None block the adversary.

### Fork RESOLUTIONS (fable-sidecar-59b, REPORT-fable-sidecar-59b.md §Q1) — 2026-08-16
- **F2 P9 — SETTLED (→ build).** CONCUR contract-59: `_ALL_BUILTIN_TOOL_NAMES` universe check +
  public/sync raise-before-register (live guard RAISES ValueError; fastmcp default is silent
  warn-and-keep, so `on_duplicate="error"` ALONE misses the disabled-built-in-name reservation).
  Nuance to fold into the build brief: ALSO set `on_duplicate="error"` as a reach-robust backstop over
  ALL registration paths — NOT a replacement, and VERIFY no legitimate duplicate exists first.
- **F3 wire-discipline — SETTLED (tombstone).** CONCUR: the wire-liveness virtue is PRESERVED by this
  packet's FG2/D7, so no coverage gap. Build/finalization TOUCH-UP: the tombstone header must name
  (a) premise-dissolved, (b) FG2/D7 re-expression, (c) packet-39 handoff — verify test_wire_discipline.py.
- **F1 Origin dedup — DEFERRED to packet 39, measure-then-tune (NOT put to operator yet).** Reframed as
  a MEASUREMENT: does fastmcp `host_origin_protection` reproduce bespoke semantics on
  {absent-Origin-allowed, loopback, bad-IPv6-fail-closed}? Spike already settled absent-Origin (fastmcp
  ALLOWS it, MATCHES bespoke — so KEEP is NOT forced); loopback + bad-IPv6 UNMEASURED. **Packet 59 keeps
  BOTH (design C3 PRESERVE bespoke Origin + C3′ ADD fastmcp Host protection) — the safe, non-blocking
  default.** DECISION POINT (packet 39, where the auth/Origin layer is reworked): measure the two
  remaining semantics; if equivalent → operator/pkt39 rules (sidecar leans DROP the bespoke Origin — one
  allow-list not two that silently diverge); if divergent → KEEP bespoke. Surface to operator WITH the
  measurement. Contract pins OUTCOMES either way (bad Origin→403, spoofed Host→421, absent allowed).
