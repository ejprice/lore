# REPORT-lead-63c — packet 63c wave (comms remainder: brief_* + agent roster as governed)

`lead-base v6 read` · **resumed 2026-09-24: `lead-base v8 read`**
`brief project v7 read`

**Lead:** lead-63c (Opus 4.8) · session `63c-20260913` · branch `feat/surreal-unification`
**Packet:** 63c — the LAST wave of packet 63 (govern comms + memory). COMMIT-ONLY (deploys at the
pkt-65 joint cutover). Do NOT start packet 64.
**Base:** HEAD `bb9ac1e` (local strictly AHEAD of origin `c658781` by 35 unpushed 63b commits —
verified `git fetch`; no stale base, nothing to rebase, no missed upstream conventions).
**Design authority:** `docs/design/2026-08-28-packet63-retrofit-rulings.md` (§1.1 63c contents,
§2.1 migration per table, §4.1 DDL emitter, §6 §9 target, §7 SF-63-2, §9 riders, §10.9 F5).
Plus the 63c-specific sidecar ruling (this wave) as the binding design for the open forks.

**HARD TRIGGER:** 63c MUST precede the pkt-65 hosted cutover (63-rulings §1.1). #467 is the headline
security debt.

---

## SUMMARY BLOCK (lead-base v6 — filled at close)

| field | value |
|---|---|
| `Verdicts acted on:` | (pending) |
| `Directives:` | (pending) |
| `Rulings:` | (pending) |
| `Agents:` | (pending) |
| `Uncommitted at stop:` | (pending) |

---

## RESUME ANCHOR (compaction-ready — read this + the wave log to reconstruct state)

**I am `lead-63c`** (Opus 4.8, session `63c-20260913`), orchestrating packet 63c (comms remainder). HEAD
`bb9ac1e`, branch `feat/surreal-unification`, COMMIT-ONLY (no deploy until pkt-65). 63b COMPLETE.

**Binding design:** `docs/design/2026-09-13-packet63c-remainder-ruling.md` (sidecar-63c, `699a6e9`) — accepted
in full. Split RULED **Option 2**: 63c-i-a (agent data) → 63c-i-b (serving/security) → 63c-ii (brief) → ONE
security-auditor at 63c close. Each sub-wave: contract→adversary(+sidecar fidelity read)→build→cold-audit→commit.

**PIPELINE STATE (as of this anchor):**
- ✅ probe-63c (`109da9c`), sidecar ruling (`699a6e9`), findings #469/#470/#471 filed, #468 confirmed.
- ✅ **63c-i-a RED contract** — `contract-63c-i` delivered, commit `0b8ce37` (VERIFIED clean, no trailer; 8 files
  test-only + F5 substrate ADD-only + DUAL surgery on test_comms_schema/wiring). RED verified 38 failed/19 passed
  (`-n 12`, author's measure — adversary re-grades). currency FAILs BY DESIGN (a pytest RED contract's reds are
  structurally RED_ORPHANED — the registry adjudicates only mypy bounds; builder greens at wave close). Report
  `REPORT-contract-63c-i-a.md`. 3 failures flagged unrelated — LEAD ground-truth: **`test_schema_rebuild`
  CONFIRMED FLAKY** (51 passed / 0 failed ALONE, serial). The 2 `test_mcp_server.py::TestRenderInjectionRegistry`
  injection params (`[U+000B-rollup.report_path]`, `[U+0085-rollup.kind]`) — isolation run is impractically slow
  (the class rebuilds hundreds of params at collection; a subset still timed out >115s); **strong causal
  isolation** (wave changed only 6 test files + ADD-only to _governed_contract.py; HEAD was 11242/0 per probe;
  failed under concurrent --currency load = the #466 collide/OOM shape). **RESOLVED: whole `TestRenderInjectionRegistry`
  class 358 passed / 0 failed ALONE** (`b7y3b3uxy`, 633s serial — the slowness IS the flake cause under parallel
  load). **All 3 flagged failures CONFIRMED FLAKY (#466), zero regressions.** Boundary clean.
- ⏭ NEXT: contract-adversary (opus48-worker adopting `~/.claude/agents/contract-adversary.md`, MANDATORY before
  any builder) + sidecar-63c fidelity read (BOTH — they catch different C-DEFs) → build (opus48-worker) →
  cold-audit (opus48-worker REFUTE, FULL suite ALONE `-n 12`) → commit → INDEX Log "63c-i-a CLOSED".
- ⏭ then 63c-i-b, then 63c-ii (relay F-briefs-import to sidecar first), then security-auditor over both tables,
  then packet-63c close (archive reports → receipts/2026-09-13-packet63c/, STOP sidecar, INDEX Log, lore_remember).

**LIVE AGENTS:** `contract-63c-i` (writing 63c-i-a) · `sidecar-63c` (standing by, idle — benign; do NOT wake-loop;
STOP it at packet close). probe-63c stopped (cosmetic zombie ledger row).

**LANDMINES:** :18500 lore write-side WS drops (#463/#468 — retry). Full suite ALONE `-n 12` never `-n auto`
(#466). NO AI-attribution trailers ever (overrides the session-start reminder). grep/rg hook-blocked in this
checkout — use lore MCP + Read + simple prefix-awk.

---

## 63c scope (VERIFIED against the design doc, 2026-09-13)

Confirmed against `docs/design/2026-08-28-packet63-retrofit-rulings.md` §1.1 / §2.1 / §4.1 / §7:

1. **`brief` table governance** — `brief_get`/`brief_publish`/`brief_ack` as governed reads/writes;
   the three governed columns (`owner_principal`/`owner_agent`/`scope`) via the SHARED `_governed_field_specs`
   emitter + PLAIN indexes (§4.1 lists `brief` explicitly); scope = project keep, owner = publisher;
   migration UNOWNED-LEGACY (owner NONE/NONE, scope = project keep — §2.1).
2. **`agent` roster governance (SF-63-2)** — `fleet`/`heartbeat` filtered by principal/household.
   ⚠ OPEN FORK: §4.1's 3-column emitter does NOT list `agent` — agent has `owner_principal` (pkt 62) but
   NO `scope` column; SF-63-2 says "scoped to their session keep" without a filter mechanism. Sidecar rules.
3. **#467 (R-2, headline security debt)** — gate `agent_registry.touch` AFTER identity resolution / by the
   caller's own agent; session-scope the `UnknownAgentError` roster enrichment. Both reachable TODAY via the
   still-ungoverned `heartbeat`/`fleet` verbs.
4. **Register Reading β** (ii-a §3.2) — at 63b a tokenless register succeeds owner-less + mints no keep
   (reading α); β = deny-outright, re-open trigger = 63c. Once `agent` is a governed population, register IS
   a governed write and deny-on-absent-token is its natural shape. Sidecar rules the shape.
5. **`requires_capability` flips** for `heartbeat`/`brief_*`/`fleet` (RED_ADJUDICATED(owner=63c) at HEAD) +
   the #420 verb-routing coverage legs wired.
6. **DD-3.c class check** (this session's hypothesis, to PROBE): `agent` is UPDATE-hot (heartbeat + the
   owner_principal backfill UPDATE); the `brief` scope-backfill is a one-shot whole-window UPDATE. Any field
   ASSERT on either table a whole-window UPDATE re-validates (store-ref §1.4) is a loaded gun. Apply the ii-b
   DROP/KEEP discriminator per ASSERT: DROP if it merely duplicates an app cap and fails in a direction the
   reader would not; KEEP if its violation set ≡ the reader's own rejection set (ii-b R19 `grade` precedent).

## Pipeline (per the brief)
probe → sidecar rulings → contract (Opus) → contract-adversary (MANDATORY) + sidecar fidelity read →
[reviser] → build (Opus) → cold-audit (Opus REFUTE, FULL suite ALONE `-n 12`) → commit → dedicated
security-auditor wave (§9, F3: ≥2 principals × ≥2 agents, disjoint households; #467 + roster/liveness/brief
is its headline; 63c-gates-65 instrument). One build wave if the contract prices ≤0.30; split brief-side /
agent-side at that seam otherwise.

---

## Wave log

- **2026-09-13 — orientation complete.** git fetch (local ahead 35 commits, no rebase). Read lead-base v6,
  CLAUDE.md (auto), store-ref (pending targeted read at DDL time), design doc §1–§10.9, ii-a §3.2 (register β),
  ii-b §2–§4 + §12 (DD-3.c precedent), INDEX Log tail (63b COMPLETE at bb9ac1e), #467, packet-63 design recall.
  Registered on comms (session 63c-20260913, 3 retries — #463 WS instability). Report skeleton written.
- **2026-09-13 — probe-63c CLOSED (Opus 4.8, one-shot).** Commit `109da9c` (probe script + 1 test_secret_typing
  allowlist entry + report; VERIFIED clean, no AI trailers, author EJ Price). Gates GREEN (ruff/typecheck/
  currency PASS, pytest 11242 passed/0 failed, probe exit 0). Facts A–F in `REPORT-probe-63c.md`. Lead
  spot-VERIFIED the load-bearing facts: the commit; the agent/brief ASSERT enumeration read directly against
  `surreal_schema.py` (`_AGENT_FIELD_SPECS` :523, `_BRIEF_FIELD_SPECS` :644). **Key verified finding:** the
  ASSERT-bearing columns (agent name/session/role/status; brief name/body/created_by) are the ORIGINAL PKT-28
  C1 birth-time columns; EVERY post-birth column (status_set_at, declared_cadence, owner_principal, capability_*)
  is `option<>` NO-ASSERT per store-ref §1.4 → **no legacy row can violate the birth-time ASSERTs**, so the
  DD-3.c hazard for the CURRENT migration is nil (unlike ii-b's `to.ack_note`); the risk is a FUTURE post-birth
  ASSERT/required column + the all-or-nothing backfill. → likely ruling KEEP + a forward P2 pin (sidecar's call).
  Forks confirmed for the sidecar: (Q1) agent has no scope column → pkt-61 scope filter TableScans, owner_principal=
  IndexScans, session= IndexScans (D2 fleet mechanism); (Q5) report_unmigrated is scope-keyed, unfit for agent.
  #467 sites: touch-before-deny server.py:6216; roster leak _comms_enrich_unknown_agent server.py:6649. Probe
  process TaskStopped (ledger row = cosmetic zombie, no cross-agent retire verb). Comms: 2 probe signals drained
  (no ack owed). ⚠ Discrepancy to reconcile: report §FRICTION says "#468 filed" but the probe signal says it
  couldn't file to lore_findings — check whether #468 exists before double-filing the :18500-drop friction.
- **2026-09-13 — sidecar-63c spawned** (Fable general-purpose, NOT a fork, long-running). Front-loaded with all
  6 forks (Q1 agent read-filter mechanism · Q2 register β · Q3 DD-3.c per-ASSERT + forward pin · Q4 #467 shapes ·
  Q5 agent report_unmigrated · Q6 wave shape + requires_capability flips), the verified probe facts, and the
  design-authority + ii-a/ii-b precedent pointers. Ruling doc → `docs/design/2026-09-13-packet63c-remainder-ruling.md`.
- **2026-09-13 — sidecar RULING committed `699a6e9`** (VERIFIED clean, no AI trailers). Lead read the doc in
  full + graded it against the design authority + probe facts. **BINDING rulings + LEAD DECISIONS (accepted):**
  - **Q1 = (c)** — `agent` gets the SAME 3 governed columns + 2 indexes via the ONE emitter (retire pkt-62's
    hand-rolled owner_principal twin). The sidecar explicitly resolved §4.1 (omits agent — a SIDECAR ruling)
    vs §7 SF-63-2 (operator-CONFIRMED, names a scope) toward the operator's letter (Reading B). ACCEPTED: a
    HOW within confirmed scope, resolving toward the operator's own SF-63-2, and store changes to lore's own
    code are pre-authorized (proceed-then-report). Alternatives (a)/(b) each break single-brain or the comms
    model. Reported to the operator for transparency; not gated.
  - **Q2 = β** — a register resolving NO principal DENIES (correctness, not taste: α post-63c lets the cutover
    backfill fabricate an owner one verb later). Keys on the transport PRINCIPAL token, not `capability=`.
  - **Q3 = KEEP agent.status (reader-aligned Literal) · DROP+MOVE 5 (name/session/role + brief name/created_by
    → the ONE writer's app-cap, retiring the 2nd regex spelling) · DROP brief.body (dup of #257 floor).**
    ACCEPTED the MOVE (sidecar's rec; KEEP-ALL fallback available if the contract prices MOVE out). Birth-time
    fact confirmed → current migration safe; forward P2[agent]/[brief] pin carries the DD-3.c bound.
  - **Q4 = identity-first dispatcher** — resolve Subject FIRST, read own row by id, check agent=/session=
    against it, THEN touch by id, THEN dispatch. Closes #467-1 by ORDER (denied call = zero agent mutations);
    collapses 5 handler copies to ONE site. Roster leak: agent= is a self-check, never a lookup key → ghost≡foreign.
  - **Q5 dissolves under Q1** (agent gains scope; `scope IS NONE` is the ∀-table unmigrated predicate); the
    agent migrate = ONE 3-column statement + the §2.1 ROW-precondition (which Q5 IMPLEMENTS — it was missing).
  - **Q6 / L1 = TWO waves, agent-first** (63c-i agent population; 63c-ii brief population) + ONE security-auditor
    at 63c close over both. ACCEPTED. **L2** = land β + its 58-site corpse in 63c-i as ONE reconciliation
    (ii-a D1 precedent). ACCEPTED. requires_capability flips land per verb WITH the enforcing handler.
  - **Operator escalations from the sidecar: none.** Three findings to file (L3-a/b/c). Spec-silent items: none.
- **2026-09-13 — findings #469/#470/#471 FILED** (L3-a regex twin / L3-b migrate row-precondition unimplemented /
  L3-c fleet session= prose). #468 (probe's :18500-drop friction) confirmed already filed. Sidecar informed of
  accepts (#13003). contract-63c-i spawned (Opus 4.8, RED contract to the ruling).
- **2026-09-13 — contract-63c-i RETURNED, BLOCKED on the split decision (success-state escalation, #13004).**
  Priced 63c-i at ~55–70 pins + the 58-site β corpse + F5 substrate additions ≈ 2/3 of packet 63c — OVER the
  0.30 split gate (recon COMPLETE, 63c-i-a data-layer design locked in scratch; nothing written yet). Fork:
  **Option 1** = one 63c-i contract; **Option 2 (author's rec)** = sub-split on the data/serving seam —
  **63c-i-a agent DATA layer** (Q1 DDL/emitter, register stamps, Q3 drops+MOVE, P2[agent]+P-A2, Q5 migrate,
  DD-3.c dirty legs, F5 seeders) then **63c-i-b SERVING/SECURITY layer** (∀-reader read_filter wiring + 8
  consumers, EXPLAIN-A, Q2 β + 58-corpse, Q4 #467, flips), i-b depends on i-a. Mirrors the 63b ii-a/ii-b
  write/read split. Two flags raised: F-regex-twin ordering (the `_IDENTIFIER_CHARSET_PATTERN` deletion is
  63c-ii-gated — refines #469); F-briefs-import discrepancy (ruling §4.2's "briefs.py imports from agents" is
  FALSE per briefs.py's docstring — a 63c-ii predicate-source issue, relay to sidecar then). ⏸ PAUSED per
  operator (2026-09-13) at the agent-return boundary; operator RESUMED.
- **2026-09-13 — SPLIT RULED: Option 2 (lead call L1; operator resumed with no override → lead recommendation).**
  63c-i sub-splits into **63c-i-a (agent DATA layer)** → **63c-i-b (serving/security)**, i-b depends on i-a,
  each its own contract→adversary→build→cold-audit; ONE security-auditor at 63c close over both. Mirrors 63b
  ii-a/ii-b. 63c-i-a scope: Q1 DDL/emitter (W1-1) · register stamps (owner_principal/owner_agent=self/scope=
  session keep) · Q3 agent drops + register MOVE (name/session via AGENT_NAME_PATTERN, role via is_blank,
  teaching, pre-I/O) + agent DDL name/session/role ASSERT→"" · P2[agent]+P-A2 · Q5 agent migrate R-Q5-1..3
  (incl. the §2.1 row-precondition, #470) · DD-3.c dirty legs (Leg A/B/heartbeat/P-A3) · lift seed_agent_legacy/
  _governed + agent GovernedTableCase into the F5 home. NO dispatcher/read-filter/β (those are 63c-i-b).
  Flag F-regex-twin ACCEPTED: `_IDENTIFIER_CHARSET_PATTERN` DELETION is 63c-ii-gated (brief.name is its last
  consumer) — 63c-i-a only moves agent's register off it + sets agent's DDL ASSERT to ""; no deletion, no
  single-hit sweep yet. Flag F-briefs-import DEFERRED to 63c-ii (relay to sidecar: ruling §4.2's "briefs.py
  imports from agents" is false per its docstring — settle the brief.name MOVE predicate source then).
  Contract author unblocked via ledger directive + native wake.
- **2026-09-24 — RESUMED (new session, lead Opus 5.5).** `lead-base v8 read`; brief-base now v16. git fetch:
  local ahead of origin 39, behind 0 (no rebase). HEAD `f04916d` (operator commit: project agent overrides pin
  claude-opus-5-5; `fable51-worker` for the sidecar; security-auditor pinned Fable 5.1) — touches only
  `.claude/agents/`, so the 63c-i-a contract graded at `0b8ce37` is not STALE. Prior-session agents
  (`contract-63c-i`, `sidecar-63c`) are dead with the old session → respawn with suffixed names. lore-lore was
  mid-reindex at session start (MCP :9202 refused); watcher armed. NEXT unchanged: adversary + sidecar
  fidelity read on 63c-i-a.
- **2026-09-24 — baseline @ `f04916d`.** ruff clean; typecheck OK on all members. Contract RED re-measured
  (`pytest -n 12` over the 5 touched test files): **38 failed / 433 passed** — the 38 reproduces the author's
  count exactly (19 test_agent_registry · 10 test_agent_governance_63c_i_a · 8 test_agent_owns_principal_schema
  · 1 test_comms_schema); all reds are in contract-touched files. Waiting on lore MCP (reindexing).
- **2026-09-24 09:18 — lore NOT serving after 66 min.** lore-lore (up since 08:12, 0 restarts) is doing a
  cold full reindex; since 13:12Z every TEI embed call to the remote embedder times out (`embed.retry.backoff`,
  status null, ~2 min/attempt, attempts 0→3). :9202 never bound. Remote-embedder probe denied by the session
  permission classifier → escalated to operator. Watcher re-armed (60 min). Wave work gated on lore per
  operator instruction.
- **2026-09-24 10:19 — embedder recovered; lore still cold-reindexing (507 `lore`-tier files done, ~250/h over
  the last hour).** One file FAILED to store: `loremaster/tests/test_comms_tool.py`
  (`store_op_failed_after_retries`, 12:55Z — #463/#468 WS-drop class) → the index will be missing it until a
  reconcile; FILE a finding + `lore_index(reconcile=True)` once lore serves. Also to file: a cold reindex
  blocking MCP serve for 2h+ (eager boot) vs the documented ~150s. Watcher re-armed (3h).
- **2026-09-24 12:00 — lore SERVING (:9202, after ~3h48m cold reindex).** This session's MCP client failed at
  startup and does not auto-reconnect → lore tools absent here; operator asked to `/mcp` reconnect. Spawn briefs
  drafted (session scratchpad): `sidecar-63c-2` (fable51-worker, long-running; Task 1 = 63c-i-a fidelity read;
  consumer law front-loaded) and `adversary-63c-i-a` (contract-adversary, Opus 5.5). Spawn on reconnect.
- **2026-09-24 ~16:10Z — /mcp reconnected; lore live at HEAD `f04916d` (3772 indexed / 1 failed = #338/#383
  permanent >5000-stmt file; no reconcile — it cannot fix that file and #434 says a full sweep times out).**
  Registered `lead-63c-2` (comms session `63c-20260924`). Annotated #355 with the ~3h48m cold-boot recurrence +
  the #383→#355 trigger HYPOTHESIS (no new finding — dedup). SPAWNED (parallel, independent — enumerations
  diffed by the lead, never shared): `sidecar-63c-2` (fable51-worker, long-running; Task 1 = 63c-i-a ruling-
  fidelity read; consumer law front-loaded) + `adversary-63c-i-a` (contract-adversary, Opus 5.5). Briefs:
  session scratchpad `brief-sidecar-63c-2.md` / `brief-adversary-63c-i-a.md`.
- **2026-09-24 ~16:14Z — cold-boot outage logged DURABLY (operator directive).** Commit `d0c9946`:
  `docs/plans/v2/receipts/2026-09-24-lore-cold-boot/` = full `podman logs --timestamps lore-lore` (1314 lines,
  secret-scanned: 0 hits) + README timeline. #355 annotated with the path. NEW **#472** (uncertainty,
  trust_false_clear): `embed.permanent_failure` (32 texts, 13:20:31Z) mid-file, yet `test_mcp_server.py`
  reported `indexed` 471 chunks with no `index.file.failed` — possible silent chunk loss; UNMEASURED.
  Surfaced to operator: investigate now vs. ledger (outside 63c scope → operator's call).
- **2026-09-24 ~16:25Z — sidecar-63c-2 Task 1 ACTED ON.** Verdict line: `0b8ce37 -> d0c9946 -> SAME`
  (merge-base ancestor ✓; intervening commits touch only `.claude/agents/` + `docs/plans/v2/receipts/`).
  Report `043f960`; ruling amendment 1 `c4728b1` (E1 Leg A three-not-four · E2 heartbeat control = frozen-DDL
  store rejection via real `touch` · E3 R-Q5-1 KNOWN BOUND). Fidelity: 5 GAP / 5 GAP-minor / 2 ORPHANED /
  0 CONTRADICTS. **OPERATOR RULING (2026-09-24): the design sidecar is THE AUTHORITY on design forks —
  "Follow what the sidecar wants."** Applied: **D1 = (a)** F5 write-attribution rows (§2.2 rows 1–3) owned by
  **63c-i-b**, named in its contract brief · **D2 = (a)** R-Q5-1 precondition unchanged, pinned KNOWN BOUND +
  trigger "a pkt-62-through-63b image deployed before the 63c cutover" (amendment E3) · **D3 = yes** fold
  `test_agent_owns_principal_schema.py::_create_agent` onto `seed_agent_legacy` in the i-a build's REFACTOR
  step. ORPHANED #14 (wiring schema-applied proof rests on brief leg only) → carried to 63c-ii's brief.
  **#472: operator ordered a READ-ONLY investigation now** → `investigate-472` spawned (Opus 5.5).
  Pending: `adversary-63c-i-a` report; then ONE contract-reviser wave folding adversary missing-pins + sidecar
  GAPs (#1,2,4–8,10) + E1/E2/E3 + D2/D3 → re-adversary delta pass (contract→adversary law, no skip) → build.
- **2026-09-24 ~16:55Z — adversary-63c-i-a ACTED ON.** Verdict line: `0b8ce37 -> f89a1ae -> SAME` (no test/prod
  symbol moved). **INSUFFICIENT + UNSATISFIABLE:** 11 surviving wrong builds (kill-pins proven RED-on-wrong /
  GREEN-on-ref) · correct ref build full suite ALONE `-n 12` = **8 failed / 11254 passed**, all 8 contract
  defects (missed corpse `TestAgentRoleNonEmptyAssert` x4 · heartbeat leg seeds wrong id -> `UnknownAgentError`
  on every build, RED for the WRONG reason · 2 exact population-set pins · `TestMigrateAgentOwner` old world).
  Author's 38/433 RED reproduced. Report committed `b46d3f2`; process TaskStopped + ledger-retired. Its fork (1)
  = D1 (ruled). Forks (2) MP-10 `briefed` population · (3) MP-12 register scope-kwarg vs forbidden-name pin ·
  (4) R5 owner=>scope -> **routed to sidecar-63c-2** (directive #15002 + wake), plus a GAP/missing-pin conflict
  diff so the reviser gets ONE worklist. Filed by adversary: #473 (text-search hook blocks scratch copies too).
- **2026-09-24 ~17:15Z — sidecar Task 2 ADOPTED (amendment 2, `65ca279`).** A1 `briefed` governed from i-a
  (resolver ImportFrom leg; its F5 case owed by 63c-ii) · A2 registry seam `session_keep_id`, forbidden-name pin
  re-keyed to the safe set, fakes mirror, unconditional pass · A3 register refuses an inconsistent owner/scope
  pair pre-I/O · A4 `lorerunes.is_legal_identifier` (fullmatch decision) + `AGENT_NAME_PATTERN` moves to
  lorerunes; pre-answers F-briefs-import. §E flagged A4 as operator-visible; lead judged it NOT major
  architecture (it is the CLAUDE.md-designated `lorerunes` home applied verbatim) → adopted, operator informed.
  §D = ONE 15-item worklist. **Spawned `contract-63c-i-a-r2`** (opus55-worker) to revise 0b8ce37 against §D, with
  a required full-suite satisfiability receipt. NEXT: re-adversary delta pass on r2 (no skip) → build.
- **2026-09-24 ~17:45Z — investigate-472 CLOSED: #472 BENIGN (resolved).** batch-scope `embed.permanent_failure`
  → unlogged per-text fallback; 471/471 vectors correct; tier-wide no false clear. Report + README resolutions
  committed `41b9e21`. ⚠ **DEVIATION (surfaced to operator):** its Run 1 full-rate re-embed 429'd PRODUCTION TEI
  17:27:55–17:36:26Z (one file 7s→76.7s; zero file failures; killed) + a transient script write to the lore-lore
  container /tmp. Follow-ups: #474 filed (misleading batch event name) · #383 annotated (re-embeds 505 chunks
  every sweep) · #355 CORRECTED (my count-leg hypothesis refuted; trigger still unknown) · lore memory: TEI
  capacity gotcha. Process TaskStopped; ledger row already self-retired. Drained #15000/#15001/#15003 (signals,
  already acted on).
- **2026-09-24 ~18:05Z — contract r2 DELIVERED `88205a4`** (report inside; 0 attribution lines). Author claims:
  15/15 §D pinned · SAT 11292 passed / 0 failed full suite ALONE `-n 12` on ref · RED@HEAD 70/70 + 78 missing-seam
  fallout · 22/22 wrong builds PROOF HELD. Deviations D-1 (13 test files' owner-only register fixtures re-keyed —
  A3/A2 corpses) · D-2 (footer pin retargeted) · D-3/F-1 (E2 control DDL order). Process TaskStopped; ledger
  self-retired. Forks F-1/F-2/F-3 → sidecar (directive #15005 + wake). **Spawned `adversary-63c-i-a-r2`**
  (contract-adversary, Opus 5.5) — delta pass, re-derive every claim, independent ref build (contract→adversary law).
  Operator todo: lore_tasks f4e3b63f… (log the re-embed fallback outcome; #474).
- **2026-09-24 ~18:30Z — sidecar Task 3 ADOPTED (amendment 3, `e6bedd1`).** F-1 reading (b) confirmed (+E2-bis
  wording fix) · F-2 fake mirrors `is_blank` + `is_legal_identifier` via the shared predicates (r3-NON-GATING) ·
  F-3 fold THREE name-keyed `_patch_everywhere` copies → the shared instrument (r3-NON-GATING) · F-4(b)
  column-wise 2-of-3 wrong build IS constructible → r3 item 1 = mutation run, **GATING iff a pin is missing** ·
  F-5 bound accepted. **Sequencing:** r3 HELD until `adversary-63c-i-a-r2` reports (it scratch-copies the
  checkout; r3 edits would contaminate its copies). Then r3 (item 1 first) + fold any r2-adversary findings;
  builder may start after item 1 is clean, in parallel with r3 items 2–3 (disjoint files), one adversary delta
  covers 2–3 before cold audit. Noted operator commit `5e3e5a4` (INDEX plan review, another session): its "live
  image 0f5f2dc" CONSISTENT with E3 (0f5f2dc 2026-08-17 predates pkt-62 66b5fa4; image created 2026-08-18 00:03Z).
- **2026-09-24 ~16:15 EDT — adversary-63c-i-a-r2 ACTED ON.** Verdict line: `88205a4 -> 91c6f5c -> SAME` (no
  production/test path moved; the adversary's `git diff --stat` over code roots is EMPTY). **INSUFFICIENT:** 7 new
  wrong builds survive (N1, N1c, N2, N3, N4/N4h, N5, N10); N1c+N2+N3+N5+N10 TOGETHER pass the WHOLE tree
  11292/0. **BLOCKERS: MP-A** (`_is_comms_charset_legal`, the SKIP-policy consumer of the identity decision, is
  unpinned AND ORPHANED — in no sub-wave's A4 consumer list) · **MP-D** (population resolver reach is a spelling
  hand-list, not a checked variable — derive from the emitted DDL). Also MP-B/C/E/F/G. Prior 11/11 KILLED;
  independent SAT 11292/0; RED@HEAD reproduced exactly (148/2345); WB-2of3 (amendment-3 F-4) PROOF HELD → r3
  item 1 is NOT gating. DUAL diff independent = author's. Process TaskStopped (ledger retire pending lore).
- **LEAD DIRECTIVE TO sidecar-63c-2 — TASK 4 (durable copy HERE; lore ledger is DOWN, see next entry):** rule the
  r2 adversary's decisions in a committed amendment-4: **NF-1** (A4 consumer set includes `_is_comms_charset_legal`;
  adversary recs yes) · **NF-2** (may a legacy hostile-named agent re-register after the MOVE; recs no) ·
  **MP-D's fix shape** (resolver reach derived from emitted DDL) · **MP-G ordering** (fix the shared patch helper's
  aliased-import false-RED + lying message BEFORE amendment-3 F-3's fold). THEN publish ONE consolidated **r3
  worklist** = amendment-3 §A items 2–3 + adversary-r2 §6 MP-A..MP-G, each tagged GATING / NON-GATING. Evidence:
  `REPORT-adversary-63c-i-a-r2.md` (committed with this entry). Deliver: doc + native micro-format wake.
- **2026-09-24 16:12 EDT — lore OUTAGE #2: host global OOM.** Kernel OOM-killer (invoked by `python`) killed
  lore-surreal's `surreal` (anon-rss ~20 GB) at 15:19:54; systemd restarted it at 15:19:56 (exit 137, restart
  counter 1). **lore-lore never re-established its store WS** → every lore call "no close frame" for 52 min (the
  adversary lost ledger access mid-run: its R-1). At OOM: surreal ×2 ≈30.5 GB anon, python ×52 ≈13.3 GB, odoo ≈4.5 GB;
  `/tmp` is tmpfs (RAM-backed) at 18 GB, 17 GB of it `/tmp/claude-1000` (Claude Code task files, all sessions).
  Receipts: `docs/plans/v2/receipts/2026-09-24-lore-store-oom/` (kernel OOM dump, surreal restart journal, lore-lore
  log since 15:15). Action (pre-authorized production op): `podman restart lore-lore` at 16:12:32 (CreateCommand
  captured first; restart keeps the hand-rolled mounts). Watcher armed. Findings to file when lore serves: lore-lore
  does not reconnect after a store restart (R-1; cf. #330 "self-healed" in Aug) · host OOM kills the prod store
  (oom_score_adj 200 makes surreal the preferred victim).
- **2026-09-24 16:16 EDT — lore-lore back in 240s after the restart (delta boot, NOT a #355 full rebuild):**
  `reconcile.summary files_indexed 2, files_failed 1 (#383), files_skipped 1233, tiers_rebuilt ["lore"]` —
  a 3rd receipt that the `tiers_rebuilt` label does NOT mean "purged" (for #355). This session's MCP client
  dropped on the restart → operator `/mcp` reconnect needed before filing: R-1 (no reconnect after a store
  restart), host-OOM-kills-prod-store, and the adversary-r2 ledger retire.
- **2026-09-24 ~16:30 EDT — sidecar Task 4 ADOPTED (amendment 4, `2c30150`).** NF-1 YES (A4-bis:
  `_is_comms_charset_legal` is the server's ONE decision home) · NF-2 NO · MP-D fix = emitted-DDL derivation, fail
  closed · MP-G identity-alone before the F-3 fold · §W = ONE 11-item r3 worklist (1–6 GATING, 7–10 NON-GATING,
  11 PROSE). §E (item 7 supersedes 63b §1.9 item 2's MECHANISM, intent preserved) judged not major → adopted.
  **LEAD ORCHESTRATION CALL:** r3a+r3b run SEQUENTIALLY in ONE reviser (two commits), not in parallel as the
  sidecar suggested — no worktrees in this repo, so parallel test-writers in one checkout would contaminate each
  other's full-suite runs and the adversary's scratch copies. **Spawned `contract-63c-i-a-r3`** (opus55-worker).
  Memory guard in its brief: ≤1 full suite at a time, don't launch under ~30 GB available (host at 25 GB available
  now: Shmem 58 GB, only 18 GB of it tmpfs `/tmp` — the rest likely Postgres shared_buffers across the Odoo
  harness pods; surfaced to the operator). Lead to file on reconnect: `ALL_DDL_GENERATORS` misses lease +
  floor_calibration (amendment-4 finding), plus the outage-#2 findings.
- **2026-09-24 ~18:05 EDT — contract r3a COMMITTED `11cbfb2`** (items 1–6, GATING). r3b (items 7–11) done +
  lane-proven but UNCOMMITTED, held on forks (patch saved by the author at its scratchpad `r3b_snapshot/r3b.patch`).
  **Operator-directed memory cleanup:** deleted 162,173 files older than 7 days (17.3 GB, none open per lsof) under
  `/tmp/claude-1000` (tmpfs); /tmp 18 GB → 1.4 GB; host available 19 GB → 35 GB (clears the reviser's 30 GB gate).
- **LEAD DIRECTIVE TO sidecar-63c-2 — TASK 5 (durable copy HERE; this session's lore MCP is still disconnected):**
  rule the r3 author's forks, `REPORT-contract-63c-i-a-r3.md` §FORKS (uncommitted, at repo root — read it in place):
  **FORK-A** (item 7 ⊇-pin direction: amendment-4's literal text vs its parenthetical point opposite ways; the
  parenthetical reading is RED on a correct build = unsatisfiable; author recs (c) PIN-THE-MISS — assert the known
  gap is EXACTLY {generate_lease_ddl, generate_floor_calibration_ddl}) · **FORK-C** (item 8: amendment-3 F-2's
  "unguarded call-time import adds no HEAD reds" is FALSE — measured 55→287 reds over the 11 `_comms_fakes`
  consumers, 232 HEAD-green tests turn RED; author recs a GUARDED read under which the mirror legs stay visibly RED)
  · **FORK-B** (ratify: author lifted the generator-discovery helper into `_enforced_relations_scaffold.py` and
  folded two pre-existing private copies — `test_ddl_write_target_coverage_124.py`, `test_principal_keys_schema.py`
  — outside the named worklist; also found `_logging_fixtures._rebind_everywhere` was a pre-existing identity-keyed
  twin and shared its loop). Deliver a committed amendment-5 + native micro-format wake.
- **2026-09-24 ~19:00 EDT — sidecar Task 5 ADOPTED (amendment 5, `26511f0`).** FORK-A (c) PIN-THE-MISS ratified ·
  FORK-B RATIFIED + ONE rider (lifted `emit_schema_ddl` must pass `dim` whenever PRESENT, as both old copies did;
  name the `isfunction` bound) · FORK-C (b) guarded identity leg ratified + riders (narrow `except ImportError`
  helper; CONDITIONAL pin — symbol exists ⇒ no guard in `_comms_fakes` source; **BUILDER BRIEF MUST GRANT the one
  test-tree guard-line deletion in REFACTOR**). All NON-GATING. The r3 author watches for the amendment file itself.
  Operator reconnected lore (`/mcp reconnect all`). Filed **#478** (lore-lore never reconnects after a store restart)
  · **#479** (host OOM kills the prod store first; oom_score_adj 200) · **#480** (`ALL_DDL_GENERATORS` misses
  lease + floor_calibration; pinned by r3b item 7). #355 annotated (3rd receipt: the `tiers_rebuilt` label does not
  mean purged; plan-review routed #355 to packet 11c). `adversary-63c-i-a-r2` ledger-retired. Drained
  #15004/#15008/#16000–#16002 (signals, all already acted on).
- **2026-09-24 ~19:20 EDT — contract r3 DELIVERED:** r3a `11cbfb2` + r3b `39935f6` (0 attribution lines each;
  report committed in `39935f6`). Author claims SAT **11405 passed / 0 failed** full suite ALONE `-n 12` on ref
  (36 GB available); HEAD reds all new pins, zero HEAD-greens turned red; forks A/B/C RULED + amendment-5 riders
  applied (dim-whenever-present restored + pinned, D17). **BUILDER-BRIEF ITEMS (carry verbatim):** (1) the builder
  may delete the fake's `except ImportError` guard in `_comms_fakes.py` in REFACTOR — its ONE granted test-tree
  edit (conditional pin reds until it does); (2) delete both `scripts/pending_contracts.yaml` entries (`…-r2`,
  `…-r3`) with the build — all 11 self-destruct on the built world; (3) builder notes in
  `test_agent_governance_63c_i_a.py`'s module docstring (MP-F pair, MP-C constant, A4-bis home body); (4) the two
  production prose lines the build falsifies (adversary-r2 §11); (5) D3: fold `_create_agent` onto
  `seed_agent_legacy` in REFACTOR. Finding #477 filed by the author (lore_impact covering-test noise). Process
  TaskStopped (ledger self-retired). **Spawned `adversary-63c-i-a-r3`** — delta pass over `88205a4..39935f6`,
  prior-7 kill table + new-instrument attacks + independent SAT, memory-guarded.

---

## RESUME ANCHOR v2 (2026-09-24 ~20:25 EDT — compaction-ready; supersedes the v1 anchor at the top)

**I am `lead-63c-2`** (Opus 5.5), lore_comms session `63c-20260924`, branch `feat/surreal-unification`,
COMMIT-ONLY (no deploy until pkt-65). Read `~/.claude/orchestration/lead-base.md` (v8) on resume.
**Operator standing rulings (this session):** (1) the design sidecar is THE AUTHORITY on rulings + design forks —
adopt its call, record it in a committed artifact, never re-escalate; only MAJOR scope / MAJOR architecture go to
the operator (lore memory e4131fdc). (2) No AI-attribution trailers, ever.

**Pipeline state (63c-i-a, agent DATA layer):**
- Contract chain: r1 `0b8ce37` → r2 `88205a4` → **r3a `11cbfb2` + r3b `39935f6`** (current contract).
- Ruling chain: base `699a6e9` + amendments 1 `c4728b1` · 2 `65ca279` · 3 `e6bedd1` · 4 `2c30150` (§W worklist) ·
  5 `26511f0` (FORK-A/B/C). All in `docs/design/2026-09-*-packet63c-*.md`.
- ~~RUNNING: `adversary-63c-i-a-r3`~~ → **DONE 2026-09-24 ~22:10 EDT: INSUFFICIENT** (see the wave-log entry at the
  END of this file — "adversary r3 verdict"). Current step: sidecar Task 6 (rule MP-1…MP-5 + R-3), then reviser r4.
- **STANDING BY:** `sidecar-63c-2` (fable51-worker, long-running for the whole packet; idle is benign; never
  wake-loop; STOP it + ledger-retire at 63c close). Queued for 63c-ii: F-briefs-import is pre-answered by A4
  (`briefs.py` imports `lorerunes.is_legal_identifier`).
- **NEXT on the adversary verdict:** SUFFICIENT → verify graded sha (`git merge-base --is-ancestor 39935f6 HEAD`),
  TaskStop + ledger-retire it, commit its report, spawn ONE Opus 5.5 builder (`opus55-worker`) for 63c-i-a carrying
  the **BUILDER-BRIEF ITEMS** in the 19:20 wave-log entry above (guard deletion in `_comms_fakes.py` = its ONE
  granted test edit; delete both `pending_contracts.yaml` entries; module-docstring notes; the 2 production prose
  lines from adversary-r2 §11; D3 `_create_agent` fold) + memory guard (≤1 full suite, ≥30 GB available, `-n 12`
  ALONE) → cold audit (Opus REFUTE, full suite ALONE) → commit → INDEX Log "63c-i-a CLOSED".
  INSUFFICIENT → route forks to the sidecar (ledger directive + wake), then a reviser r4 → adversary delta.
- Then 63c-i-b (serving/security: read_filter, EXPLAIN-A, β + corpse, #467 dispatcher, flips, F5 write labels per
  D1) → 63c-ii (brief; F14 wiring schema-applied proof) → ONE security-auditor (Fable 5.1) over both tables →
  packet close (archive reports to `docs/plans/v2/receipts/2026-09-24-packet63c/` with git mv, INDEX Log,
  lore_remember, STOP sidecar, verify `fleet` shows only me).

**Retired agents (process stopped + ledger retired):** adversary-63c-i-a, investigate-472, contract-63c-i-a-r2,
adversary-63c-i-a-r2, contract-63c-i-a-r3.

**Landmines learned today:**
- lore-lore does NOT reconnect after lore-surreal restarts (#478); the fix is `podman restart lore-lore` (~4 min
  delta boot; keeps its hand-rolled mounts; never `lore-deploy start`). After any lore-lore restart, the operator
  must `/mcp reconnect` this session.
- Host OOM killed the prod store (#479). Memory guard in every brief: ≤1 full suite at a time, don't launch
  under ~30 GB available. /tmp is tmpfs; `/tmp/claude-1000` was cleaned (operator-directed, files >7d).
- TEI capacity ≈ 64 concurrent texts, and one indexer fills it; never full-rate-embed ad hoc (lore memory).
- grep/rg are hook-blocked here AND in scratch copies (#473); even the WORD in a command string trips the hook.
- lore_comms directives fail while lore is down → the durable fallback is a committed lead-report entry + a
  native wake (used for sidecar Tasks 4–5).

**Open non-63c items (operator-scheduled):** lore_tasks f4e3b63f… (log the re-embed fallback outcome; #474) ·
#478/#479/#480 · #355 (→ packet 11c; trigger of the ~4h full rebuild still unknown) · #383 cost amplifier.

## Wave log (cont., after RESUME ANCHOR v2)

- **2026-09-24 ~22:10 EDT — adversary r3 verdict: CONTRACT INSUFFICIENT** (graded `39935f6`; report
  `REPORT-adversary-63c-i-a-r3.md`, committed with this entry). Summary block + §6 MISSING PINS + §8 residuals
  read IN FULL (the read-the-residuals law).
  - **Floor held:** 7/7 adversary-r2 survivors KILLED on their declared pins. **SAT reproduced independently:**
    full suite ALONE `-n 12` on the adversary's own reference = `11405 passed, 62 skipped, 3 xfailed`, 0 failed
    (= author's count); ruff clean after cleanups; built world = exactly 11 SELF-DESTRUCTs. **RED@HEAD:** 0
    HEAD-greens turned red; 77 new reds, all right-reason. DUAL: no virtue lost by any fold.
  - **5 NEW survivors, each with a kill-pin GREEN on ref / RED on its build:** MP-1 (X1 — `_comms_traffic_line`'s
    SKIP gate hand-rolls the identifier decision; routing-is-not-sharing one call site up; rec. GATING) · MP-2
    (X2 — `[:10]` literal twin of `_REFUSAL_ID_SAMPLE_SIZE`; the bound is read, never perturbed; rec. GATING) ·
    MP-3 (X3 — FORK-C guard pin checks a spelling; `except Exception:` passes; rec. GATING-adjacent) · MP-4 (R5 —
    FORK-A bound's PREMISE "no unswept emitter emits a relation" is unobserved; rec. NON-GATING) · MP-5 (FX1 — parity
    matrix covers first-register only; fake re-register unmirrored; rec. NON-GATING).
  - **Fork R-3:** is `_REFUSAL_ID_SAMPLE_SIZE = 10` normative? (adversary: any positive bound + sanity ceiling ≤ 20).
  - **Prose:** MP-P1 (`test_ddl_write_target_coverage_124.py::_emit` docstring false after amendment-5's `dim`
    rider) · R-1 (author's "36 parity rows" is 34) · R-2 (author's `r3b_files.txt` run set unpasted).
  - Convergence across rounds: wrong-build survivors 11 → 7 → 5, every prior survivor killed. The STOP-rule
    question ("is the reach receding one level deeper each round?") goes to the sidecar with the classification
    ask — MP-1 is the same class one call site up, which is exactly the tell to rule on, not re-brief.
  - Actions: `adversary-63c-i-a-r3` TaskStopped + ledger-retired; fallback watcher stopped. **Routed to
    `sidecar-63c-2` as Task 6** (ledger directive on thread `63c` + native wake): rule MP-1…MP-5 class (GATING /
    NON-GATING / pinned KNOWN BOUND), R-3, and whether r4 takes all five or the STOP-rule applies to any.
  - **Environment note:** operator re-scope `2fd3351` / `26ff7bb` keeps 63c on the critical path (63c → 64 → 65;
    11c is a hard dependency of 65) and starts 17 + 19 + 65-P1 design + 24 in PARALLEL sessions. Every r4+ brief
    carries: `ps` check for other pytest before any full suite, `git add` own paths only.
