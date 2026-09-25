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

- **2026-09-24 ~22:40 EDT — amendment 6 ADOPTED** (`3327770`, sidecar-63c-2; standing ruling: sidecar is the
  authority). MP-1/2/3 GATING (MP-1 = text-twin static ∀ pin with the honest-engineer threat model IN the
  instrument + SKIP-gate effect leg; MP-3 effect pin REPLACES the spelling pin) · MP-4/5 NON-GATING · R-3: the
  bound's VALUE is not normative, no ceiling pin · **STOP-rule invoked: r4 is the LAST pre-build contract round**;
  further identity-class doors after r4 become pinned KNOWN BOUNDS, never r5. §E flags that cap to the operator
  (told in the lead's turn summary, not escalated — within sidecar authority).
  - **BUILDER-BRIEF ITEM ADDED (6th):** `surreal_schema._IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern`
    imported from `lorerunes` (one line; `brief`'s ASSERT stays byte-identical until 63c-ii).
  - **Sidecar lore client is DOWN** (ECONNREFUSED since outage #2; server answers). Ledger #16005 is un-acked
    for that reason, not ignored. Until its session restarts, every sidecar directive's durable copy is a
    committed lead-report entry + native wake.
  - **Spawned `contract-63c-i-a-r4`** (opus55-worker; brief `scratchpad/brief-contract-63c-i-a-r4.md`): §W items
    1–6 in ONE commit, SAT full-suite-alone receipt incl. the two builder edits, memory + parallel-session guard.

- **2026-09-24 ~23:xx EDT — FORK-D (from `contract-63c-i-a-r4`) → SIDECAR TASK 7** (durable copy HERE; sidecar's lore
  client is down). Full fork text: `REPORT-contract-63c-i-a-r4.md` §FORKS → FORK-D (uncommitted, on disk; the
  reviser holds its commit for this ruling). Gist: amendment-6 STOP-rule §2's key text `[a-z0-9][a-z0-9_` also
  matches `config.SLUG_PATTERN = r"^[a-z0-9][a-z0-9_]*$"` (the project-SLUG rule — a different policy), so the
  literal pin reds a CORRECT build and SAT is impossible. Readings: (a) keep the key, allowlist the safe by
  evidence — exempt `SLUG_PATTERN` by (file, binding, EXACT text) plus an evidence leg that it decides a different
  language (rejects legal agent name `fixer-b`), re-open trigger in the pin [reviser's rec; built provisionally];
  (b) lengthen the key (no exemption, but a hyphen-dropping pasted twin escapes — narrower than ruled); (c) literal
  — edit `SLUG_PATTERN` (ungranted production edit to an unrelated policy). **Ask of the sidecar:** rule (a)/(b)/(c)
  or other; reply via a committed amendment-6 addendum (or amendment 7) + native micro-format to the lead.

- **FORK-D RULED + ADOPTED — amendment 7 (`3a2975c`):** reading (a) — keep the text-twin key; exempt
  `config.SLUG_PATTERN` by (file, binding, EXACT text) with a LIVE two-direction evidence leg (`fixer-b` agent ✓/slug ✗;
  65×`a` slug ✓/agent ✗) + a re-open trigger routing a converged language to lorerunes as ONE predicate; (b) rejected
  (narrows the honest-paste threat model), (c) rejected (ungranted edit to a different policy). Still GATING.
  Erratum recorded: amendment-6 swept with the full class text but pinned the prefix. Relayed to
  `contract-63c-i-a-r4` (native; durable = the committed amendment) — its provisional build is the ruling; commit.

- **2026-09-24 ~23:15 EDT — contract r4 DELIVERED (`e80a854`)**; reviser TaskStopped + ledger-retired. Summary block,
  §FORKS, candidate bounds and deviations read in full. Trailer-clean; touches only its writable set (+ the appended
  r3 correction note). SAT: full suite ALONE `-n 12` on its reference `11428 passed, 62 skipped, 3 xfailed`, 0 failed,
  incl. both builder edits; 10/10 wrong builds killed (X1, X2, X3, X3b-d, R5, FX1, TW, SLUGDRIFT); RED@HEAD 0 greens
  turned red, 7 new right-reason reds. **These are claims — the r4 adversary re-derives them.**
  - **DV-1** (a bare `--currency` ran pytest at `-n auto` concurrently with the agent's own lane) is a RECURRENCE of
    #466 whose root cause is the DEFAULT in `scripts/gates.yaml` (pytest leg hard-codes `-n auto`); annotated on #466
    (→ packet 09b). Every brief from here says: currency only as `--legs typecheck,ruff` or `--currency -- -n 12`.
  - **SIDECAR TASK 8 (durable copy HERE; its lore client is down):** rule (1) **FORK-E** — amendment-6 R-3 "the FULL
    count on a separate line": reviser picked reading (i) (count asserted independently of the id sample; no newline
    requirement) over (ii) (a `\n` in the refusal text); ruling needed only if (ii) was meant. (2) **KB-1…KB-5**
    (`REPORT-contract-63c-i-a-r4.md` §Candidate KNOWN BOUNDS): KB-1 hostile corpus lacks a DOTTED shape (one-entry
    close, grows corpus-parametrised pins) · KB-2 reworded/runtime-assembled class evades the text pin (threat-model
    boundary) · KB-3 reach excludes `scripts/` · KB-4 a docstring quoting the rule text reds the pin · KB-5 re-register
    parity covers only the three ruled sequences. For each: pinned KNOWN BOUND (and who writes the pin, given r4 was
    the last contract round) / accepted-unpinned with trigger / close. Reply: committed amendment 8 + native
    micro-format.
  - **Spawned `adversary-63c-i-a-r4`** (contract-adversary) on `39935f6..e80a854` in parallel with Task 8.

- **2026-09-24 ~23:35 EDT — amendment 8 (`2f16ac9`, sidecar Task 8) ADOPTED on every design ruling:** FORK-E reading (i)
  (erratum "line" → "assertion"; no new pin) · KB-1 CLOSE (`"fixer.b"` joins `_HOSTILE_IDENTIFIERS`) · KB-2 PINNED KNOWN
  BOUND (reworded-class NEGATIVE control + the KNOWN-BOUND message; #138 trigger) · KB-3 ACCEPTED reach parameter
  (docstring sentence) · KB-4 not a bound (failure text → "reference the constant, never quote its text") · KB-5 CLOSE
  (fourth parity row). Builder-brief rows reconfirmed (+ **item 7: `_REFUSAL_ID_SAMPLE_SIZE` docstring states WHY**).
  - **ONE PROCESS DEVIATION from amendment 8, by the lead, on standing operator law:** amendment 8 says r4a "needs no
    adversary round of its own". CLAUDE.md (operator, 2026-07-28): *"no contract revision skips the adversary because it
    is 'small'"* — its receipts are precisely a small fixture wave that went straight on. Process law is the operator's,
    not a design fork, so the sidecar's authority does not reach it. Resolution, right-sized: r4a is HELD until
    adversary-r4's verdict (so it absorbs the KB closes AND any SAME-CLASS bound pins r4 produces in ONE addendum), then
    a NARROW adversary delta grades only the r4a diff. The builder may still start on `e80a854` in parallel (amendment
    8: none of the rows changes what the builder builds); r4a + its delta must land before the cold audit.

- **2026-09-25 ~01:00 EDT — adversary r4 verdict: CONTRACT INSUFFICIENT — NEW-CLASS survivors, NO live production
  defect** (graded `e80a854`; `REPORT-adversary-63c-i-a-r4.md`, committed with this entry; summary, §6, §8 read in full).
  Adversary TaskStopped + ledger-retired (it survived one API-error turn via a single resume ping).
  - **Held:** r3 floor 5/5 KILLED (+ X3b-e); SAT reproduced independently `11428 passed, 62 skipped, 3 xfailed`, 0
    failed; RED@HEAD confirmed; built world 11 SELF-DESTRUCTs; author claims re-derived (R-8).
  - **8 full-suite survivors → missing pins:** **MP-R4-1 RS1** (NEW-CLASS, security-adjacent, rec. GATING) — the REAL
    writer re-stamps an already-stamped row from a DIFFERENT consistent pair (householded joiner takes ownership);
    mint-once is pinned ∀ rows, not ∀ callers; **amendment-8 KB-5's premise ("the real writer is pinned mint-once on
    it") is FALSE** · **MP-R4-4 FXg** (NEW-CLASS) — MP-3's effect pin removes the predicate at ONE binding; a guard
    importing from the submodule outlives its premise · **MP-R4-5 FXf** (DUAL loss of the deleted spelling pin's
    "presence reds" virtue; a guard with a private-regex fallback survives) · **MP-R4-3 G1** (SAME-CLASS, closable by a
    legal-at-cap witness `"a"*64`) · **MP-R4-6 FX2** (fake side of KB-5, already ruled r4a — row must carry the ABSOLUTE
    real-side expectation) · **MP-R4-7 PX2** (NEW-CLASS prose twin of the sample bound, rec. NON-GATING) · bounds TWR
    (KB-2) and G2 (KB-1, r4a kills). MP-R4-2 WITHDRAWN after the full-suite leg.
  - **Residuals needing a ruling:** R-1 (r3's MP-4 was a scoped-file-set artifact — packet 07's pin already observes the
    premise; r4's premise pin is redundant and weaker: delete or re-key) · R-2 (skip-gate header over-claims) · R-4
    (MP-2 failure text misdiagnoses a def-time capture).
  - **Routed: SIDECAR TASK 9** (durable copy HERE; its lore client is down): per amendment-6 §5, NEW-CLASS survivors are
    ruled before any round. Rule each MP-R4-* (close in the r4a addendum / pinned KNOWN BOUND / accept), R-1, R-2, R-4,
    and correct amendment-8 KB-5. Reply: amendment 9 committed + native micro-format. Then: ONE r4a addendum carrying
    amendment-8 + amendment-9 rows → NARROW adversary delta on r4a only → builder.

- **2026-09-25 — amendment 9 (`4640232`, sidecar Task 9) ADOPTED on every ruling.** RS1 pinned ∀ callers with the
  ABSOLUTE real-side expectation (GATING; amendment-8 KB-5's premise was false — erratum) · FX2 closes in the same
  parity row (absolute real side + `fake == real`) · G1 closed by a LEGAL witness corpus incl. `"a"*64` (+ R-2 header
  narrowed) · FXg: effect pin removes the predicate at EVERY `lorerunes*` binding · FXf: property-shaped presence pin
  RESTORED beside the effect pin (amendment-6 MP-3's deletion was a DUAL loss — erratum) · PX2 prose-twin leg
  (NON-GATING) · R-1: delete r4's redundant premise pin, FORK-A docstring cites packet 07's
  `test_this_slice_contains_neither_a_relation_table_nor_a_sequence` · R-4 failure text. No r5; STOP-rule holds.
  - **BUILDER-BRIEF ITEM 8:** the re-register docstring reads "a re-register does NOT re-stamp it — from ANY caller,
    including a different householded principal". Item 1 (guard deletion) is now concretely "import
    `lorerunes.is_legal_identifier` at module top" — the restored presence pin demands exactly that.
  - **ADVERSARY-BRIEF LINE (standing, every future adversary):** "a survivor is a CONTRACT survivor until the full suite
    is run on it" (adversary-r4 R-1: r3's MP-4 was a scoped-file-set artifact).
  - **Spawned `contract-63c-i-a-r4a`** (opus55-worker; brief `scratchpad/brief-contract-63c-i-a-r4a.md`): ONE addendum
    = amendment-9 §W rows 1–8 (⊇ amendment-8 §W); SAT full-suite-alone receipt incl. all builder edits; full-suite leg
    for every survivor claim; memory + parallel-session guard. Then: NARROW adversary delta on r4a only → builder.

- **2026-09-25 — FORK-MEM (from `contract-63c-i-a-r4a`, blocked 30 min at 24–25 GB available) → LEAD GRANT:** full-suite
  legs may launch at ≥23 GB. Conditions: one pytest at a time; a 12 GB kill-by-PID watchdog; a process-table check
  before each launch; stop on a watchdog fire, with no retry. Grounds (measured at grant): no other pytest on the box;
  memory held by spike-surreal ~16 GB, lore-surreal ~12 GB, four Odoo PG harnesses from other sessions, ~40 GB shared.
  A single `-n 12` full suite costs ~6–7 GB (today: 28→22, 33→26), so the expected low is ~17 GB; the 2026-09-24 OOM
  (#479) was from CONCURRENT suites. r4a otherwise reports its rows done: 14/14 builds killed, RED clean.

- **2026-09-25 ~05:00 EDT — contract r4a DELIVERED (`bf77fb9`)**; author TaskStopped + ledger-retired. Trailer-clean;
  touches only its writable set. Claims (the narrow adversary re-derives them): SAT full suite ALONE `-n 12` `11459
  passed, 62 skipped, 3 xfailed`, 0 failed, with all four builder edits (launched 24 GB, low 18 GB per the FORK-MEM
  grant; lead watcher independently saw the low at 18 GB); TWR (KB-2 bound) survives the full suite 11459/0 as intended;
  14/14 wrong builds killed (RS1 FX2 RS1FX2 G1 G2 FXg FXf FXf2 X3b X3d PX2 MP2DEF R5 R5b; RS1FX2 is the receipt that
  row 1 needed the absolute real side); RED@HEAD 0 r4-greens turned red, 13 new right-reason reds. Lore finding #481
  filed by it (a recalled memory teaches retired tool names).
  - **SIDECAR TASK 10 (durable copy HERE):** rule (1) **R-A** — the restored presence pin accepts a module-top import from
    `lorerunes` OR a submodule (reading ii, picked: reading i reds an honest submodule import); (2) **C-1…C-5**
    (`REPORT-contract-63c-i-a-r4a.md` §CANDIDATES): C-1 fold the two pre-existing legal lists into
    `_LEGAL_IDENTIFIER_WITNESSES` · **C-2 RS1's other axis — a re-register from a DIFFERENT KEEP re-stamping `scope`**
    (unobserved; construction only) · **C-3 RS1 pinned at the registry seam only; the end-to-end `lore_comms register`
    door for a householded joiner is undriven** (63c-i-b's serving/security scope?) · C-4 PX2 detector phrase-bound
    (stated bound) · C-5 shape/effect pin reach = one fake file. For each: close (and in which artifact — r4a is
    closed; the narrow delta is running), pinned bound, route to 63c-i-b, or accept. Reply: amendment 10 + native.
  - **Spawned `adversary-63c-i-a-r4a`** (contract-adversary): NARROW delta over `e80a854..bf77fb9` only.
  - **Builder-brief item 1 sharpened** (r4a): delete the fake's guard AND import `is_legal_identifier` at MODULE TOP.

- **2026-09-25 — amendment 10 (`5b94961`, sidecar Task 10) ADOPTED.** R-A reading (ii) accepted as built · C-4 accepted
  · nothing re-opens r4a if the narrow delta is SUFFICIENT.
  - **CARRY-FORWARD ITEMS (must appear in later briefs — this list IS their durable home):**
    - **→ 63c-i-b CONTRACT (C-3, GATING-class, security):** re-register is a SELF-write. On the re-register path an
      existing row with `owner_principal` ≠ NONE and ≠ caller → the identity-conflict teaching verbatim ("names are
      never reused; register a fresh name"), naming no owner, ZERO agent-table mutations, no capability. Ownerless
      rows (α/legacy) stay re-registerable by any householded principal until `migrate-governed` stamps them.
      Pin shape: end-to-end via `AppContext.comms` register (joiner → conflict, row byte-identical `SELECT *`, no
      capability; controls: owner re-register → `re_registered=True`; joiner FRESH name → created, owner = joiner)
      + the registry-seam twin. The security-auditor's #467 wire battery gains this row.
    - **→ 63c-i-b (C-2):** one registry-seam row — re-register from a DIFFERENT keep leaves `scope` untouched
      (unreachable through the tool by construction: keep keyed on `session:<s>` alone). Lands in r4b only if the
      delta forces one; else i-b.
    - **→ 63c-i-b (C-5):** widen the shape/effect pin reach beyond `_comms_fakes.py` when i-b adds test doubles.
    - **→ 63c-ii CONTRACT (C-1):** fold `_VALID_IDENTIFIERS` + `test_pattern_accepts_legal_names`'s list into
      `_LEGAL_IDENTIFIER_WITNESSES` by UNION.
  - **§E (operator-visible, told in the lead's summary):** C-3 adds a served DENIAL to `lore_comms register`; the base
    ruling §5 had reasoned only the non-householded case. Production at HEAD does not carry the door (no principals
    on agents in the running image); it opens with i-a's stamps and closes in i-b. Sidecar: not MAJOR.

- **2026-09-25 ~07:35 EDT — narrow adversary r4a verdict: CONTRACT INSUFFICIENT** (graded `bf77fb9`; report
  `REPORT-adversary-63c-i-a-r4a.md`; summary, §6, §8, VERDICT read in full). No LIVE production defect (MEDIUM). Held:
  floor 7/7 killed exactly; RS1FX2 proves the absolute parity leg; the premise-pin deletion is covered by packet 07 over
  the full suite; SAT reproduced independently `11459 passed`, 0 failed; RED@HEAD, currency and #461 CONFIRMED.
  **Six builds survive the FULL suite** (COMBO 11459/0). Three demand action:
  - **MP-A2 · SH1 — CONTRACT DEFECT (satisfiability):** row 5's phrase leg reds the CORRECT prose
    `(first {N} of {M} ids shown)` (it reads the total). MUST be fixed before any builder (strip the full count from the
    residue, or drop the `N … shown` alternative).
  - **MP-A3 · RS1srv — NEW-CLASS (new seam):** the tool (`_comms_register`, which the i-a builder EDITS) re-stamps
    ownership after a correct registry call; the rec. is an end-to-end DATA-INVARIANCE pin (green at HEAD and on a correct
    build; no served denial, so it does not cross into i-b) riding r4b; the refusal stays i-b (am-10 C-3).
  - **MP-A1 · FXh — SAME-CLASS:** a `try`-free guard with a non-silent private fallback falsifies the shape pin's "ANY
    spelling" and amendment-9's "any fallback" claims; close with clause (iii) (no call-time re-read of the predicate off
    a module object) or pin a KNOWN BOUND with both sentences narrowed.
  - Bounds, no pin demanded: G3 (trailing-separator/all-digit witnesses → am-10 C-1 union) · PX2w (docstring: birth-value
    leg is ∀ over DIGIT spellings only; also corrects am-10 C-4's sentence) · C2 RULED · TWR working.
  - **SIDECAR TASK 11 (durable copy HERE):** rule MP-A1/A2/A3 + G3/PX2w. AND the explicit STOP-rule question, because the
    lead sees the tell: RS1 moved registry → tool seam, FXf moved `try` → `try`-free — "is the reach receding one level
    deeper each round?" Rule the SHAPE of what follows: an r4b (which items, and does it get another narrow delta per the
    07-28 law, or is there a cheaper closure) vs pinned bounds vs routing to i-b. MP-A2 is non-negotiable (a correct build
    must pass). Reply: amendment 11 + native.
  - Adversary r4a TaskStopped (it had already ledger-retired itself). Its "no LIVE production defect" was MEDIUM (it could
    not read `:18500`); **lead corroboration by SOURCE, no store touched:** at `0f5f2dc` (the INDEX-recorded live image;
    the container carries no revision label, so the identity is the INDEX's) `loremaster/loremaster/agents.py` has 0
    occurrences of `owner_principal` / `session_keep_id` — the running code cannot stamp an agent owner, so the RS1/RS1srv
    takeover door does not exist in production. HIGH at the code level.

- **2026-09-25 — amendment 11 (`71b669f`, sidecar Task 11) ADOPTED.** STOP-rule answered YES: two families recede
  (fake-guard X3b→X3→FXg→FXf→FXh; ownership registry→tool) → r4b closes each at the OUTERMOST boundary: MP-A2 DELETE the
  PX2 phrase leg (SAT fix) · MP-A3 end-to-end ownership-INVARIANCE pin through `AppContext.comms(action="register")`
  (data only; refusal stays i-b) · MP-A1 fake-predicate ALLOWLIST (one module-top ImportFrom + bare-Name Calls only) +
  obfuscation KNOWN BOUND · G3 witnesses `a-`/`a_`/`00` · C-2 registry-seam row. C-5 widening WITHDRAWN (erratum).
  - **PRE-RULING (binds the lead):** r4b gets its narrow delta (07-28 law); any post-r4b survivor of the two families is
    recorded by the LEAD as a pinned KNOWN BOUND — **no r4c**; only satisfiability defects are fixed, verified by the delta
    author's own reference. §E flags this cap as operator-visible (told in the lead's summary).
  - **Carry-forward UPDATE:** C-2 now rides r4b (removed from the i-b list); C-5 withdrawn (removed from the i-b list).
    i-b keeps C-3 (served refusal + #467 battery row; covers R-6's metadata columns).
  - **Spawned `contract-63c-i-a-r4b`** (opus55-worker; brief `scratchpad/brief-contract-63c-i-a-r4b.md`).

- **2026-09-25 — FORK-R3 (from `contract-63c-i-a-r4b`) → SIDECAR TASK 12** (durable copy HERE). Full text:
  `REPORT-contract-63c-i-a-r4b.md` §FORK-R3 (on disk, uncommitted; rows 1/2/4/5 proceed, commit held). Amendment 11
  MP-A1 clause (2) "`Call` nodes whose func is the bare `Name`" is UNSATISFIABLE: the honest post-build fake (the
  builder's granted edit, "unchanged" per §W row 3) leaves `FakeAgentRegistry._shared_identifier_predicate` as
  `return is_legal_identifier` — a Load `Name`, not a `Call`; both independent references do this. Readings: **R-3a**
  (reviser's rec., built provisionally) — shape (2) = any LOAD-context bare `Name`; DENY `Attribute` of that attr, any
  string `Constant` equal to it (getattr/hasattr/vars/sys.modules/importlib), any other import/alias incl. `as`
  rebinding, `Name` in Store/Del, a parameter of that name, `global`/`nonlocal` — with the module-top import mandatory a
  Load Name can only reach THE object · **R-3b** (literal) — keep Call-only and change the builder's granted edit to
  collapse the helper (contradicts "unchanged"; builder brief grows). Ask: rule R-3a/R-3b/other; amendment 12 + native.

- **FORK-R3 RULED + ADOPTED — amendment 12 (`f2a3bdd`):** R-3a — clause (2) = a Load-context bare `Name`; the denied set is
  the finite GRAMMAR COMPLEMENT (Attribute, string Constant, alias/`as`, Store/Del incl. class-shadow + walrus, parameter,
  global/nonlocal) — still an allowlist. Both honest post-build shapes (bare-Name return; collapsed direct call) are GREEN
  negative controls. R-3b rejected (a scope change disguised as a SAT fix). Erratum on amendment 11 recorded. Relayed to
  `contract-63c-i-a-r4b` (native; durable = the committed amendment).
  - **BUILDER-BRIEF ITEM 9 (permissive, not a requirement):** "you MAY collapse `_shared_identifier_predicate` to a direct
    `is_legal_identifier(value)` call in REFACTOR". If left, the cold audit's residual table names the dead `None` branch
    for a post-build tidy (owner: the i-b contract author).

- **2026-09-25 ~08:00 EDT — FORK-MEM grant WIDENED (pre-emptive, to `contract-63c-i-a-r4b`):** the idle baseline fell to ~21 GB
  available (a 5th Odoo PG harness from another session appeared; lore-surreal grew 12.2 → 13.9 GB RSS). A full suite may
  launch at ≥20 GB with `-n 8` (counts are -n-independent) when <23 GB; watchdog, one-at-a-time and STOP-on-fire unchanged.
  r4b progress: REF 25 contract files `3002 passed, 19 skipped`, 0 failed — the SH1 prose now passes; 15 wrong builds remain.

## RESUME ANCHOR v3 (2026-09-25 ~08:10 EDT — compaction-ready; SUPERSEDES v1 at the top and v2 above)

**I am `lead-63c-2`** (Opus 5.5), lore_comms session `63c-20260924`, branch `feat/surreal-unification`, COMMIT-ONLY (no deploy
until pkt-65). Read `~/.claude/orchestration/lead-base.md` (v8) on resume. **Operator standing rulings:** (1) the design
sidecar is THE AUTHORITY on rulings/design forks — adopt, record in a committed artifact, never re-escalate; only MAJOR
scope/architecture goes to the operator (lore memory e4131fdc). (2) No AI-attribution trailers, ever. (3) PROCESS LAW is the
operator's, not the sidecar's (the lead kept a narrow adversary on r4a/r4b per CLAUDE.md 2026-07-28 — the sidecar agreed).

**Contract chain (63c-i-a):** r1 `0b8ce37` → r2 `88205a4` → r3a `11cbfb2` + r3b `39935f6` → r4 `e80a854` → r4a `bf77fb9` →
**r4b IN FLIGHT** (`contract-63c-i-a-r4b`, brief `scratchpad/brief-contract-63c-i-a-r4b.md`; worklist amendment-11 §W rows
1–5 as amended by amendment 12 row 3). Adversary reports: r1 `b46d3f2`, r2 `539ffae`, r3 `c22419d`, r4 `86379a4`, r4a `94c31f8`.
**Ruling chain:** base `699a6e9` · am-1 `c4728b1` · 2 `65ca279` · 3 `e6bedd1` · 4 `2c30150` · 5 `26511f0` · 6 `3327770` ·
7 `3a2975c` · 8 `2f16ac9` · 9 `4640232` · 10 `5b94961` · 11 `71b669f` · 12 `f2a3bdd` (all `docs/design/2026-09-2*-packet63c-*.md`).

**LIVE AGENTS (2):** `contract-63c-i-a-r4b` (running its 15 wrong builds, ~80 min from 07:53; REF 25 files `3002 passed`, 0
failed; commit held until done — FORK-R3 already ruled). `sidecar-63c-2` (fable51-worker, standing by; **its lore client is
DOWN** — every directive = a committed lead-report entry + native wake; it replies via committed amendment + native).
**Lead watcher:** `b3s4yhxrj` (r4b commit, 3h cap).

**NEXT, in order:**
1. r4b commits → read summary/forks/candidates → TaskStop + ledger-retire → commit log entry.
2. Spawn a NARROW adversary `adversary-63c-i-a-r4b` over `bf77fb9..<r4b sha>` (template: `scratchpad/brief-adversary-63c-i-a-r4a.md`),
   under amendment 11's **PRE-RULING: any post-r4b survivor of the two receding families (fake-guard; ownership) is recorded
   by the LEAD as a pinned KNOWN BOUND — NO r4c; only satisfiability defects are fixed** (verified by that adversary's own
   reference). A NEW-class survivor still goes to the sidecar first; a LIVE production defect overrides.
3. Spawn ONE Opus 5.5 builder (`opus55-worker`) for 63c-i-a with the **BUILDER-BRIEF ITEMS**: (1) delete the fake's guard AND
   import `lorerunes.is_legal_identifier` at MODULE TOP in `loremaster/tests/_comms_fakes.py` — its ONE granted test edit ·
   (2) delete BOTH `scripts/pending_contracts.yaml` 63c-i-a entries with the build (all 11 self-destruct) · (3) apply the
   notes in `test_agent_governance_63c_i_a.py`'s module docstring (MP-F pair, MP-C constant, A4-bis home body) · (4) fix
   the 2 production prose lines adversary-r2 §11 says the build falsifies · (5) D3: fold `_create_agent` onto
   `seed_agent_legacy` in REFACTOR · (6) `surreal_schema._IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern` from
   `lorerunes` · (7) `_REFUSAL_ID_SAMPLE_SIZE` docstring states WHY · (8) re-register docstring "does NOT re-stamp — from ANY
   caller, including a different householded principal" · (9) MAY collapse `_shared_identifier_predicate` to a direct call.
   + memory guard (below). Then COLD AUDIT (Opus REFUTE, full suite ALONE) → commit → INDEX Log "63c-i-a CLOSED".
4. Then 63c-i-b → 63c-ii → ONE security-auditor (Fable 5.1) → packet close (git mv reports to
   `docs/plans/v2/receipts/2026-09-24-packet63c/`, INDEX Log, lore_remember, STOP sidecar, `fleet` shows only me).

**CARRY-FORWARD (must appear in later briefs):** → **63c-i-b contract:** C-3 re-register is a SELF-write (owned row, owner ≠
caller → identity-conflict teaching, zero mutations, no capability; ownerless rows stay re-registerable until migrate) +
#467 battery row (amendment 10 C-3; covers R-6 metadata); the builder may leave `_shared_identifier_predicate`'s dead `None`
branch → i-b tidies. → **63c-ii contract:** C-1 fold legal lists into `_LEGAL_IDENTIFIER_WITNESSES` by union. **Every
adversary brief:** "a survivor is a CONTRACT survivor until the full suite runs on it."

**MEMORY / HOST (measured 2026-09-25):** idle available ~21 GB (other sessions' Odoo PG harnesses + lore-surreal 13.9 GB). Grant
in force: full suite ≥23 GB at `-n 12`, or ≥20 GB at `-n 8`; one pytest at a time; 12 GB kill-by-PID watchdog; STOP on fire.
Never a bare `pending_contract_gate.py --currency` (#466 `-n auto` default; annotated). Kill by PID, never `pkill -f`
(#228); no `git stash` in scratch.

**Other landmines:** lore-lore does not reconnect after a store restart (#478 → `podman restart lore-lore`, then operator
`/mcp reconnect`); grep/rg + the WORD are hook-blocked (#473). **Open non-63c items (operator-scheduled):** lore_tasks
f4e3b63f… (#474) · #478/#479/#480 · #355 (→ 11c) · #383 · #466 default fix (→ 09b) · #481 (retired names in a recalled memory).

### 2026-09-25 — contract r4b COMMITTED (`8b9eb6d`); author retired; narrow adversary spawned
- r4b (amendment-11 §W rows 1–5 + amendment-12 R-3a): SAT full suite ALONE `-n 12` **11486 passed / 62 skipped / 3 xfailed / 0 failed** (author's claim — re-derived by the adversary, not by me); killed FXh FXhS FXr RS1srv RS1srvS C2 C2fake G3 G3d PX2; survivors FXo · PX2w · TWR = pinned bounds (COMBO full suite 11486/0); RED@HEAD 0 turned, 5 right-reason reds, 22 new greens; ruff GREEN; currency typecheck RED_ADJUDICATED 20 (unchanged). No attribution trailer (checked).
- Author deviations read: idle-gate contract write DENIED by the auto-mode classifier (nil effect — hook default = report name); ~1.5 h lost waiting on a foreign pytest (`mobile-pricepaper-smoke`).
- §8 candidates R-1…R-8: none needs a ruling (R-1 → amendment 12 / i-b; R-4 → amendment-11 pre-ruling; R-2 stated SAT hazard, adversary asked to check reachability). R-6 (`lore_search` >120 s) filed as **finding #482**.
- contract-63c-i-a-r4b: TaskStop + ledger heartbeat `retired`.
- NEXT: `adversary-63c-i-a-r4b` (opus55-worker) over `bf77fb9..8b9eb6d`, graded under the amendment-11 PRE-RULING (fake-guard / ownership survivors → lead-recorded KNOWN BOUND; SAT defects FIXED; NEW-CLASS → sidecar; LIVE → operator). Its reference must include both helper shapes (uncollapsed + collapsed). Then the builder (9 BUILDER-BRIEF ITEMS, anchor v3).

### 2026-09-25 — adversary r4b: INSUFFICIENT on ONE SAT defect; 2 KNOWN BOUNDs recorded; Task 13 → sidecar
Report `REPORT-adversary-63c-i-a-r4b.md` (this commit). Independent SAT, BOTH helper shapes, full suite ALONE `-n 12`: uncollapsed `11486 passed / 62 skipped / 3 xfailed / 0 failed`, collapsed the same — amendment-12 "both shapes green" now full-suite measured. RED@HEAD 0/5/22 confirmed. Currency 20 → 11 SELF-DESTRUCT → GREEN. LIVE 0. Adversary retired (TaskStop + ledger).

**KNOWN BOUNDs recorded by the lead under the amendment-11 PRE-RULING (no r4c):**
- **KB-RS1srvT (ownership family).** The end-to-end invariance pin drives ONE argument shape (agent/session/role). A takeover conditioned on an optional register argument (model / spawned_by / task_id / cadence) survives it (adversary-r4b RS1srvT, full suite 11486/0). Threat model: the honest builder — no honest ownership rule keys on an optional descriptive argument. RE-OPEN TRIGGER: any branch in `_comms_register` / `AgentRegistry.register` that reads model / spawned_by / task_id / cadence on the re-register path. Closure if reopened: one extra joiner call with every optional argument set.
- **KB-FXt (fake-guard family).** The allowlist certifies every occurrence of the predicate's NAME in `_comms_fakes.py`. A second identity decision that never names it — an `except` handler around the CALL deciding with a private rule — survives (adversary-r4b FXt, full suite 11486/0). It is inert while the shared predicate cannot raise on `str`. Threat model: the honest builder. RE-OPEN TRIGGER: an `except` handler around an identity decision in any test double, or i-b's new test doubles (amendment-10 C-5 branch 2).
- Both texts need an IN-TREE home: "pinned" means the next engineer meets them in the test. Task 13 asks the sidecar to name it.

**F-2 SAT DEFECT — FIXED under the pre-ruling (fix pending the Task-13 ruling so ONE agent touches row 1 once).** Failing node: `test_agent_governance_63c_i_a.py::…::test_R_Q5_1_…[perturbed-bound]` with `_REFUSAL_ID_SAMPLE_SIZE = 15` + remainder prose `(first 3 of 18 ids shown, 15 more)`. The remainder 18−3 = 15 equals the birth value. Fix (adversary §F-2, proven in scratch: ref+fix 4 passed · PXrem15+fix 4 passed · PX2+fix 1 failed [perturbed-bound]):
`while trap_count in (birth_bound, birth_bound - legacy_count, birth_bound + id_bound):` and add `trap_count - id_bound` to `fixture_counts`.

**SIDECAR TASK 13 (NEW-CLASS, adversary-r4b §8) — sidecar-63c-2, please rule:**
1. **F-1 — served-prose ACCURACY (row 1).** PXlie — N = the constant — serves `(first 10 of 2 ids shown)` below the cap. That is a FALSE served count (CONSUMER LAW), and it survives the full suite. It is the r4b author's own reference form, and the pin's failure message (D5) teaches it. Builder item 6 has two readings: (a) N = `min(bound, M)`, or (b) N = the constant. Options: (i) a builder-brief sentence plus rewording D5 to `first {shown} of {count}`; or (ii) a pin running the digit leg in `below-cap` too, with D4's count guard mirrored there. Or a bound, with trigger "a served refusal stating a sample size larger than its count". The lead's note: this is a served count, so the trust doctrine leans away from a bound.
2. **G4 — legal-witness axis (row 4).** A SKIP gate narrowing on `--`/`__` survives the full suite. By the adversary's count it is the 4th adversary-found axis (cap · trailing separator · all-digit · doubled separator), so amendment-11's "FOURTH witness axis → derive the corpus" trigger FIRES. It is contestable if all-digit counts as sidecar-found. Rule: derive the corpus, grow the hand-list (`a--b`, `a__b`), or bound.
3. **Carrier.** Where do the KB-RS1srvT / KB-FXt texts live in-tree (pin docstrings in the row-2 / row-3 tests, written by the F-2 fix agent)? And does anything ruled in 1–2 ride that same fix agent (a contract r4b-fix under the pre-ruling, tests only; SAT verified by re-running the adversary's §1 runner), or does it go into the builder brief?
The lead then spawns ONE tests-only fix agent (name `contract-63c-i-a-r4b-fix`), with a narrow adversary only if the ruling adds a pin (2026-07-28 law), and then the builder.

### 2026-09-25 — amendment 13 (`fab659b`) ruled Task 13; fix agent spawned
- **F-1:** reading (a) — N = `len(shown)` = `min(bound, count)`. NOT a bound: a served count falls under the CONSUMER LAW. Pinned in all three populations; D5 reworded. **Builder item 6 now reads:** "N = the number of ids actually named, `min(_REFUSAL_ID_SAMPLE_SIZE, count)`".
- **G4:** the derive trigger FIRES on the merits → `hypothesis` `from_regex(AGENT_NAME_PATTERN, fullmatch=True)` oracle-equality legs at the SKIP gate, plus a hostile companion. The dev dep goes in pytest's group; the fix agent must PROVE the in-image conformance run installs that group (#131/#139 class).
- **KB-RS1srvT and KB-FXt: CLOSED, not carried** (they supersede the two bounds recorded at `60899bf`). RS1srvT → a second joiner call with every optional arg. FXt → the allowlist gains an `ast.Try` exclusion, plus the FXs docstring line.
- **Carrier rule for future bounds:** the bounded pin's docstring; the lead-report entry until then; never `pending_contracts.yaml`.
- **Carry-forward (adversary-r4b idle summary):** a shadowing star-import in the fake (FXs) is invisible to the row-3 allowlist and is killed only by the r3/r4 SHARING pins. Builder and cold-audit briefs must say that those pins are NOT deletable on the belief that the allowlist covers them. The fix agent writes the docstring line (item 5).
- NEXT: `contract-63c-i-a-r4b-fix` (§W items 1–5; brief in the scratchpad) → narrow adversary `adversary-63c-i-a-r4b-fix` under the amendment-11 pre-ruling → builder.

### 2026-09-25 — FORK F1-ADMIT (r4b-fix item 2) → sidecar as Task 14
Raised by `contract-63c-i-a-r4b-fix` in `REPORT-contract-63c-i-a-r4b-fix.md` §FORK F1-ADMIT (working tree, uncommitted — read it there). Items 1, 3, 4 and 5 and the dependency rider are proceeding. Item 2 is being built to reading (B), switchable.
- **Conflict:** amendment 13 §F-1's literal leg — residue integers ⊆ `{len(shown)}` — REDs every correct build that also states a remainder or legacy count:
  - `(first 2 of 2 ids shown, 0 more)` below-cap;
  - `16 more` at birth 15 perturbed-bound (post-F-2);
  - the r4b docstring's own `"3 legacy rows"`.
  The lead's brief required the birth-15 remainder variant to be SAT, because it is F-2's own scenario. So (A) is F-2's defect class reborn.
- **(B), author-recommended:** admitted = the fixture's TRUE counts per population, `{len(shown), count, count−len(shown), legacy_count, count+legacy_count}`, with the guard keeping `birth` out of that set wherever `birth ≠ len(shown)`. It still kills PXlie below-cap for birth > 2. It gives up a lie equal to a different TRUE count (e.g. `first 3 of 2` when legacy = 3) — the author calls that implausible.
- **Scope sub-question:** also run the leg in `above-cap`? (shown = bound = birth, so it cannot false-RED; the QUANTIFIER LAW argues ∀ populations.)

**SIDECAR TASK 14 — sidecar-63c-2, please rule:** (A) vs (B) (or another admitted set), and above-cap in or out. Deliver as a committed amendment 14.

### 2026-09-25 — amendment 14 (`e6441aa`) ruled Task 14: reading (B) + above-cap IN; relayed
- The admitted set = the fixture's TRUE counts per population, with the birth guard. The "lie equal to another true count" case is a stated bound (its text is in amendment 14, carried in the pin docstring). D5 and the builder sentence are unchanged.
- The sidecar's erratum on amendment 13's literal `{len(shown)}`: its third SAT-class pin defect in a row. Lesson recorded: enumerate the REQUIRED-green builds before writing an admitted shape.
- Relayed to `contract-63c-i-a-r4b-fix` by a durable `lore_comms` directive (thread `63c`, sender `lead-63c-2`) plus a native wake. Proof of receipt = its report citing `e6441aa`.

### 2026-09-25 — FORK F5-REACH (r4b-fix item 5) → sidecar as Task 15
Raised by `contract-63c-i-a-r4b-fix` in `REPORT-contract-63c-i-a-r4b-fix.md` §FORK F5-REACH (working tree, uncommitted; instrument `fxt_probe.py` in its §A).
- **Measured:** amendment-13's clause (iv), "the predicate `Name` is not inside any `ast.Try`", finds 0 violations on adversary-r4b's FXt built on the UNCOLLAPSED helper (U). There, the `try` wraps a local ALIAS returned by `_shared_identifier_predicate()`. It finds 1 violation on the collapsed shape (C). So KB-FXt is closed only on the shape the builder MAY skip (amendment 12). Following the alias = a binding tracker = the packet-01 v2 regression.
- **Options:**
  - (a) As ruled, plus a pinned KNOWN BOUND for FXt-on-U: a control asserting the scanner stays quiet, which goes RED when the gap is closed.
  - (b) AUTHOR-RECOMMENDED — an EFFECT leg: `patch_shared_object_everywhere` swaps THE shared predicate for a stub that RAISES a sentinel, and a fake `register` of a LEGAL identity must propagate it (no `except` may swallow the shared decision). Alias-blind and receiver-blind; kills FXt on both shapes and any variant that names nothing; both honest shapes stay green; one test function reusing the r3/r4 seam. It is an instrument beyond the ruled clause.
  - (c) Force the collapse (R-3b): already rejected by amendment 12.
- Clause (iv) is implemented as ruled meanwhile; its mutation proof is on shape C.

**SIDECAR TASK 15 — sidecar-63c-2, please rule:** (a) / (b) / other. Deliver as a committed amendment 15.

### 2026-09-25 — amendment 15 (`7f01787`) ruled Task 15: (b) the EFFECT leg; relayed
- Item 5 = a raising-stub effect leg through `patch_shared_object_everywhere`: a legal fake `register` must propagate the sentinel. It kills FXt on BOTH helper shapes and every nameless variant. The static allowlist and clause (iv) STAY as teaching twins ("static reach — the effect leg is the ∀"). **amendment-11's obfuscation KNOWN BOUND is CLOSED** (its control is re-labelled, and its bound message removed).
- Sidecar erratum on amendments 11 and 13: a runtime property was given static instruments twice. Askable form: "is the property I am pinning a fact about the CODE's shape, or about what the code DOES?"
- Relayed as `lore_comms` directive (thread `63c`, which re-carries amendment 14 too) plus a native wake. Proof of receipt = the r4b-fix report citing `7f01787` and `e6441aa`.
- **Builder/cold-audit carry-forward:** neither static twin nor the effect leg may be deleted on the belief that another covers it, and the same holds for the r3/r4 SHARING pins (FXs).

### 2026-09-25 — contract r4b-fix COMMITTED (`10a33ef`); author retired; narrow adversary spawned
- Items 1–5 pinned per amendments 13, 14 (B) and 15 (effect leg). SAT (author's claim): both helper shapes, full suite ALONE `-n 12`, `11496 passed / 62 skipped / 3 xfailed / 0 failed` each. 8 wrong builds killed exactly; no survivors. RED@HEAD 0 turned. `hypothesis` 6.168.1 is in `[dependency-groups] dev`, and the author says it is installed in-image by the Containerfile's `uv sync --locked --all-packages`. The `conftest.py` redirects the hypothesis home out of the tree (`database=None` measurably did not stop `.hypothesis/`). No attribution trailer (checked).
- ⚠ Currency typecheck `RED_ADJUDICATED` went 20 → 23: the adversary must account for it.
- Candidate doors (author §CANDIDATE DOORS), passed to the adversary: near-miss hostile generator; shared per-user hypothesis cache under concurrent sessions; failure-message ordering in perturbed-bound.
- Author self-retired on the ledger; TaskStop done.
- NEXT: `adversary-63c-i-a-r4b-fix` over `8b9eb6d..10a33ef`, under the amendment-11 pre-ruling → builder.

### 2026-09-25 — host memory diagnosis (`memdiag-1`, operator-requested; report `REPORT-memdiag-1.md`, this commit)
- **Causes, ranked:**
  1. pp-odoo harness Postgres pods at `shared_buffers=8GB` → pinned shmem: 23.7 GiB now, 55.6 at the 09-24 OOM, ~97 at the 09-14 mass-OOM.
  2. Both Surreal stores with no `Memory=`: 31.9 GiB combined; prod was the 09-24 OOM victim.
  3. Claude sessions: 9.4 GiB.
  ARC is NOT a cause (the operator's ruling, confirmed by atop).
- **Applied by the lead (R5):** the watchdog kill-line rises from 12 → **15 GiB with a ≤10 s poll** in every future spawn brief. Launch gates stay 23/20 GiB, one suite at a time. (The adversary running now keeps its 12 GiB line; it is not re-briefed mid-run.)
- **Operator decisions surfaced:** R1 harness `shared_buffers` 8→2 GB · R2 a Surreal quadlet `Memory=` cap / OOM priority, so spike dies before prod · R6 **EDAC: 154 corrected errors on one DIMM, 3 pages hwpoisoned — hardware check.** Other-session items: R3 harness pod TTL, R7 the mobile_pricepaper_smoke dart fleet cap, R8 stale agents/containers. R4 (recycle spike-surreal) is deferred until no suite is running.
- memdiag-1 is standing by.

### 2026-09-25 — adversary r4b-fix: INSUFFICIENT on ONE SAT defect (F-A1); 4 SAME-FAMILY bounds; Task 16 (G5, G6) → sidecar
Report `REPORT-adversary-63c-i-a-r4b-fix.md` (this commit). **Every author claim was CONFIRMED independently:**
- SAT on both shapes, full suite ALONE `-n 12`: `11496 passed / 62 skipped / 3 xfailed / 0 failed` each.
- All 8 kills; RED@HEAD to the id.
- typecheck 23 = 20 + 3 direct `lorerunes` reads (owned, 11/11 SELF-DESTRUCT).
- The `hypothesis` rider holds in-image and in scratch.
- The shared cache home is safe under 8-way cold / 4-way warm concurrency (MEASURED).

LIVE 0. Adversary retired (TaskStop + ledger).

- **F-A1 SAT (FIXED under the pre-ruling):** a correct refusal stating a TRUE count the admitted list omits (`already_migrated` / `backfilled` = 0, the ruling's own "ZERO stamped") is RED in `[above-cap]` and `[perturbed-bound]`. The 12-line fix is verbatim in the report's §8, and proven: every correct variant GREEN on both shapes; PXlie and PX2 still killed.
- **SAME-FAMILY → KNOWN BOUND (lead records; carrier = the bounded pin's docstring per amendment 13; texts + re-open triggers in the report's §8):** FXtVE, FXand, FXname (fake-guard); RS1combo (ownership). Also DELETE two docstring over-claims: "whatever the handler spells" and "REACHED and TRUSTED".
- **SIDECAR TASK 16 (NEW-CLASS, report §8) — sidecar-63c-2, please rule:**
  1. **G5:** the generated legal leg never SAMPLES lengths 28–64 (the 200 derandomized draws max at 27), so a SKIP-gate narrowing on 28–63-char names survives the full suite. The measured closure is one line: `hypothesis.target(float(len(attribution)), label="length")` → max 64, 30 draws at the cap. The two over-claiming prose lines ("in its sample space by construction", "every narrowing conjunct … named or not") need narrowing either way.
  2. **G6:** single-ASCII-punctuation WIDENINGS (`@`, `+`, `\t` → `-`) survive; sampling measurably cannot close them (0 hits in 200). The measured closure is exhaustive: ∀ ASCII `c`, the rejected one-edit neighbours are never looked up (≤384 in-memory spy calls). The consequence is read-budget-only (one extra registry read; no such identity can register). The adversary flags rigor-to-importance: close it simply, or bound it.
  3. Right-sizing: this is the 5th contract round on 63c-i-a (r4 → r4a → r4b → r4b-fix → now fix2). Confirm that the fix2 agent (F-A1 + 4 bound docstrings + over-claim deletions + whatever 1–2 add) needs a further narrow adversary ONLY if the ruling adds a pin (2026-07-28 law), and say whether G5/G6's closures are worth that.

### 2026-09-25 — amendment 16 (`fbd4c80`) ruled Task 16: fix2 closes G5 + G6 verbatim; NO sixth pre-build adversary (flagged to the operator)
- fix2 = F-A1 (verbatim) + G5 CLOSE (one `hypothesis.target(len)` line) + G6 CLOSE (exhaustive single-char leg, ≤384 spy calls) + the four SAME-FAMILY bound docstrings (with closure-if-reopened; RS1combo MOOT at i-b) + the two over-claim deletions. Then the BUILDER.
- **The 2026-07-28 law is READ, not waived (sidecar §E):** the closures were authored and graded by the adversary itself, so byte-equal landing carries its own independent grading, and any deviation re-triggers a narrow delta. **Lead guard:** the fix2 brief REQUIRES a mechanical byte-equality proof (`diff` of the pasted hunks vs the landed hunks, empty) and STOP-and-escalate on any deviation. Surfaced to the operator for override.
- Watchdog kill-line in the fix2 brief = 15 GiB at ≤10 s polling (memdiag R5).
- Test store re-budgeted by `surreal-memcap-2` (spike restarted 17:34: 2 GiB block cache + 14×128 MiB write buffers). fix2 waits for any smoke to clear.
- NEXT: `contract-63c-i-a-r4b-fix2` → builder (9 items; item 6 per amendment 13 F-1) → cold audit.

### 2026-09-25 — SurrealDB ENGINE memory budgets applied (operator directive; `surreal-memcap-2`, report in this commit)
- **Engine config only, no container/cgroup limits** (the operator corrected the first brief; surreal-memcap-1 was stopped before it touched anything).

  | store | block cache | write buffers | RocksDB limit | + HNSW default | ceiling | restarted |
  |---|---|---|---|---|---|---|
  | lore-surreal (prod) | 4.5 GiB | 26 × 128 MiB | 7.75 GiB | 0.25 GiB | 8 GiB | 17:20:53, NRestarts 0 |
  | spike-surreal (test) | 2 GiB | 14 × 128 MiB | 3.75 GiB | 0.25 GiB | 4 GiB | 17:34:14 |

  The totals are confirmed by the engine's boot-log "Memory manager" lines.
- lore MCP: transient "no close frame" errors during the prod restart, then self-healed. The lead verified `lore_index()` fresh (sync 46 s, branch head current).
- **NOT bounded (report §4, stated as facts):**
  - the transaction and definition caches (item-count caps, not bytes);
  - per-query and per-connection working memory, which a `-n 12` burst can push above the budget transiently;
  - RocksDB index/filter blocks, file handles and compaction threads outside the declared limit;
  - allocator-retained RSS.
  RE-OPEN TRIGGER: store RSS > 1.5× its ceiling.
- **Smoke-result correction by the lead:** the agent's "1 failed + 3 errors, unrelated pre-existing gap" in `test_comms_schema.py` was re-run by the lead (`1 failed, 215 passed, 3 errors`, reproduced). These are **63c-i-a contract reds for the RIGHT reason** (unbuilt world), not a store effect and not a pre-existing gap:
  - the ERRORs = `AgentRegistry.register()` has no `session_keep_id` kwarg yet;
  - the FAILED `[agent]` = the `agent` floor wants `scope`, which i-a adds.
  The builder closes both.
- surreal-memcap-2 retired.

### 2026-09-25 — DEV-1 (fix2: the verbatim hunks fail `ruff check`) → sidecar as Task 17
Raised by `contract-63c-i-a-r4b-fix2` in `REPORT-contract-63c-i-a-r4b-fix2.md` §DEVIATION (working tree, uncommitted). Items 1–3 land byte-equal (3 diffs EMPTY) but go RED on the manifested ruff gate: E501 ×4 (comment, f-string, docstring lines at 111–116 > 110) and I001 ×1 (`from hypothesis import target` ordering). The adversary's lint claim covered its reference builds, not its §4f/§4d scratch proposals.
- The proposed lint-clean form: a comment rewrap, an f-string split at a literal boundary (identical runtime string), ruff's own I001 fix, and a docstring rewrap. It is **proven AST-equivalent** (`ast_equiv.py`, with positive controls that DO detect a real edit). The author will re-run the adversary's drivers and the SAT runner on whatever lands.
- Options: (A) land the lint-clean form with no delta; (B) a narrow delta on the four rewraps; (C) `# noqa` — adds bytes and teaches a noqa for formatting, not recommended.
- **Lead recommendation: (A).** The intent of amendment 16's verbatim clause is that the GRADED PROGRAM lands unchanged. A machine-checked AST equivalence with controls is a stronger proof of that than byte-equality, and the behavioural grading is re-measured on the landed bytes anyway. **Condition:** the fix2 report must carry the `ast_equiv.py` receipts against the COMMITTED files, not only the scratch copies.

**SIDECAR TASK 17 — sidecar-63c-2, please rule:** (A) / (B) / (C). A short committed amendment 17 or an addendum line is enough.

### 2026-09-25 — amendment 17 ruled Task 17 (DEV-1): (A), relayed
- "Verbatim" = the graded PROGRAM: AST-equivalent under `ast_equiv.py`'s rule with positive controls. Byte-equality is sufficient, never necessary. Conditions: (1) ast_equiv receipts against the COMMITTED files; (2) the adversary's drivers + SAT runner re-run on the landed bytes. (B) and (C) are rejected. Sidecar erratum on amendment 16's "byte-equal" (it collided with the C-DEF law's "satisfiable AFTER the lint cleanups").
- Relayed as `lore_comms` directive (thread `63c`) plus a native wake. Proof of receipt = the fix2 report citing amendment 17 and carrying both receipts.

### 2026-09-25 — FINDING N-1 (fix2: G5's `target()` LOSES the Nmixed kill) → sidecar as Task 18
Raised by `contract-63c-i-a-r4b-fix2` in `REPORT-contract-63c-i-a-r4b-fix2.md` §FINDING N-1 (working tree; commit HELD; SAT/RED receipts continue). All 17 adversary drivers reproduce on the landed bytes, with declared = observed both ways.
- **The DUAL regression nobody ran:** amendment 16 / adversary §4f graded `target(len)` only against the untargeted leg's SURVIVORS. The author re-ran the builds the untargeted leg KILLED, with sets declared before the run: **Nmixed (a SKIP-gate narrowing on names containing both `-` and `_`) is now `638 passed`, LOST.** G4's kill held on the real seed but on a thinner margin.
  - Mechanism (a strategy replay): targeting spends the budget on length. Mixed-separator draws go 4 → 0, doubled 10 → 1, trailing 23 → 6.
  - Nmixed's full-suite leg is queued.
- **Severity:** a NARROWING — a legal agent's traffic-line lookup is silently SKIPPED, which is a SERVED-OUTPUT consequence (unlike G6's read-budget-only widening).
- **Options:** (a) record a bound; (b) keep an UNTARGETED TWIN of the generated leg beside the targeted one — **author-recommended**; (c) a named `"a-_b"` witness (one axis at a time, the enumeration shape).
- **Lead recommendation: (b), with NO further delta.** The twin is the r4b-fix generated leg that `adversary-63c-i-a-r4b-fix` already graded, restored byte/AST-equal under a second test id. So it is the previously graded program, not new ungraded code (the amendment-17 reading). It restores the pre-fix2 kill set by construction and keeps G5's gain. The fix2 report must prove the twin is AST-equal to the leg at `10a33ef` and show Nmixed RED on the full suite.

**SIDECAR TASK 18 — sidecar-63c-2, please rule:** (a) / (b) / (c), and whether (b) needs a delta.

### 2026-09-25 — amendment 18 ruled Task 18 (N-1): (b) untargeted twin, no delta; relayed
- An UNTARGETED TWIN of the generated leg (the r4b-fix leg at `10a33ef`, restored AST-equal, second test id) sits beside the targeted leg. Its docstring states why two samples exist. (a) is rejected: a served-output NARROWING is not boundable under the trust doctrine. (c) is rejected: enumeration.
- Conditions: (1) ast_equiv of the twin vs `10a33ef` with controls; (2) Nmixed RED on the FULL suite; (3) the regression table over BOTH legs, declared before the run. **Lead addition:** SAT on the FINAL bytes (with the twin), both shapes. The pre-twin SAT runs do not count.
- Sidecar erratum on amendment 16 G5: it graded on survivors only; the removed-behaviour leg was owed ("what did the OLD sample kill?"). **Lesson for the cold audit + i-b:** any change to a generator/sampling strategy is a delete/replace of coverage and carries a DUAL leg.
- Relayed as `lore_comms` directive (thread `63c`) plus a native wake.

### 2026-09-25 — contract r4b-fix2 COMMITTED (`9298183`) — the 63c-i-a CONTRACT IS FINAL; builder spawned
- fix2 = amendment 16 §W 1–5, plus amendment 17 (a lint-clean AST-equivalent landing) and amendment 18 (the untargeted twin). SAT on the FINAL bytes, both shapes, full suite ALONE `-n 12`: `11498 passed / 62 skipped / 3 xfailed / 0 failed`. Nmixed is RED on the full suite (twin only). All 17 adversary drivers are reproduced on the landed bytes. RED@HEAD: 0 turned red. 11/11 SELF-DESTRUCT on the built world. No attribution trailer (checked). The author is retired (it self-retired on the ledger; TaskStop done).
- **N-2 (carry-forward):** hypothesis seeds `derandomize` from the test function's SOURCE digest (name + docstring + body), so every derandomized leg's kill set is a property of its exact bytes. The twin's docstring carries the bound and a re-open trigger. The targeted leg and the hostile companion are candidates only (scope closed).
  - **Suggested hardening for i-b (lead, MEDIUM on the API details):** an explicit `@hypothesis.seed(...)` on each derandomized leg, so draws stop depending on names and docstrings.
  - The candidate door C-1 is in the fix2 report's §CAND.
- **Carry-forward for the cold audit + i-b:** any change to a sampling/generator strategy is a delete/replace of coverage, and it carries a DUAL leg ("what did the OLD sample kill?").
- NEXT: `builder-63c-i-a` (items 1–10 per anchor v3 as amended by amendments 13–18; brief in the scratchpad; NO commit and NO deploy — the cold audit comes first) → COLD AUDIT (Opus REFUTE, full suite ALONE) → lead commits → INDEX Log "63c-i-a CLOSED".

### 2026-09-25 — FORK-B1 (builder: the D3 fold's file was outside the writable set) — ruled by the LEAD: (A)
- This was a lead-brief defect, not a design fork: D3 is a ruled builder action, but `_create_agent` lives in `loremaster/tests/test_agent_owns_principal_schema.py`, which my writable set omitted.
- Granted for the D3 fold ONLY: delete `_create_agent`; route its 11 sites through `seed_agent_legacy(..., role="worker")` (behaviour-equivalent); nothing else in the file changes. Receipts required: the file diff, identical `--collect-only` ids before and after, green after the fold, and a DUAL row.
- **Cold-audit carry-forward:** check this test-file edit specifically.
- Relayed as `lore_comms` directive (thread `63c`) plus a native wake.
