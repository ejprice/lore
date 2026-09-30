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

### 2026-09-25 — 63c-i-a BUILT (uncommitted; `REPORT-builder-63c-i-a.md`); flags ruled; prose fixes; cold audit next
- **Builder's claims (the cold audit re-derives them):**
  - Full suite ALONE `-n 12`: `11498 passed / 62 skipped / 3 xfailed / 0 failed`.
  - 250/250 RED@HEAD → green; 0 of 2767 HEAD-greens turned.
  - ruff, typecheck and currency GREEN, with both yaml entries deleted.
  - Two real-tree mutation proofs HELD.
  - D3 folded inside the FORK-B1 grant. Item 10 (collapse) declined, as permitted.
  - Backup patch md5 `113d0143…`.
  - Friction filed: #483 (`lore_index(reconcile=True)` client abort at 300 s).
- **Flags:**
  - **F-1** (stale fake docstring/comment) and **F-3** (`scripts/probe_governed_63c.py`, falsified by the build) — FIXED in this wave by `prosefix-63c-i-a` (prose only; brief requires the allowlist, effect-leg and sharing pins green, and a refreshed backup). The builder had self-retired on the ledger, so it was TaskStopped (it had not acted) and the work went to a fresh agent.
  - **F-2** → **63c-i-b contract carry-forward:** `test_comms_schema.py::_create_agent` (9 sites) is a third raw-CREATE clone. Fold onto `seed_agent_legacy` unless its raw writes are deliberate dirty-store rows.
  - **F-4** (a scoped-but-ownerless raw row makes the message migrate refuse forever, loudly; MP-F-named) → no action. Noted for i-b.
  - **F-5** (the `agents.py` module docstring API block refreshed) → accepted.
- NEXT: prosefix → COLD AUDIT (Opus REFUTE: re-run gates, full suite ALONE, probes; the FORK-B1 test edit checked specifically) ∥ a CONTRACT-BLIND diff reader (report-only; D3 is a delete/replace) → lead commits → INDEX Log.

### 2026-09-25 — prose fixes F-1/F-3 applied (`REPORT-prosefix-63c-i-a.md`); cold audit spawned
- Prose-only, AST-proven. Scoped pins (allowlist, effect leg, sharing, generated legs) at `-n 8`: `639 passed / 0 failed`. The final-bytes backup patch md5 is `5ed71294a7c72627e7398218b74cc11c`.
- Deviations ACCEPTED by the lead:
  - **D-1:** a dangling inline comment that the granted docstring rewrite orphaned was reworded, and "guarded" was dropped.
  - **D-2 (b):** a second comment carrying the "NO scope column" claim was corrected; printed output strings were deliberately left, and are dated by the new header.
- prosefix retired. `blindreader-63c-i-a` (contract-blind, no tests) is running; `coldaudit-63c-i-a` spawned over the final working tree.

### 2026-09-25 — contract-blind diff reader: 0 BLOCKER, 1 MAJOR (F-2), 5 MINOR (served prose), 5 NOTE; Task 19 → sidecar
Report `REPORT-blindreader-63c-i-a.md` (this commit; the withheld set was honoured; it read finding #470, disclosed). Reader retired.
- **BR-F-2 MAJOR (conditional):** the build redefines "un-migrated agent" as `scope IS NONE` and adds the owned-but-unscoped precondition refusal to the AGENT leg. The UNCHANGED MESSAGE leg's agent-first guard still keys on `owner_principal IS NONE` (via `_owner_count`). So on a store where `--table agent` refuses as multi-principal, `--table message` PROCEEDS and stamps foreign owners into the project keep. #470 quotes ruling §6 item 6 as "refuses ALL tables". Untested.
- **Served-prose MINORs (CONSUMER LAW):**
  - BR-F-1: the refusal's diagnosis "multi-principal or half-applied store" is false for operator-owned unscoped rows (pkt-62→63b images).
  - BR-F-4: "nothing was written" is false on the credentialed tool path — the session keep is minted and the keeper claimed before a blank-role/identity refusal.
  - BR-F-8: the new `lorerunes/identifiers.py` docstring re-teaches the WHERE-inlining injection threat model that #219 refuted.
  - BR-F-5: the `_owner_count` docstring is stale.
  - BR-F-9: the identity-refusal gloss is restated, not derived, and omits the 64-char cap.

**SIDECAR TASK 19 — sidecar-63c-2, please rule:**
1. **D-1:** is "the precondition refuses ALL tables on a foreign-owned agent" (ruling §6 item 6, per #470) in 63c-i-a's scope? If yes, BR-F-2 is a build defect: the message leg's guard must share the agent leg's migrated predicate + precondition (ONE implementation), with a contract pin. If no, name the wave.
2. **D-2:** the BR-F-4 fix locus — refuse a blank role / invalid identity in the handler BEFORE the keep mint (behaviour), or narrow the prose (text)?
3. Do the prose MINORs (F-1, F-5, F-8, F-9) ride a same-wave fix (a builder fix pass + contract pins where a pin is owed, e.g. the gloss deriving the cap) or a named later wave?
The cold audit is running in parallel; the lead will merge its findings with this ruling into ONE fix wave.

### 2026-09-25 — COLD AUDIT: NO-GO (`REPORT-coldaudit-63c-i-a.md`, in `84af63f`); build CHECKPOINT-committed; amendment-19 fix wave spawned
- **Blocking (both MAJOR, confirmed BY CONSTRUCTION with controls, and matching the blind reader independently):**
  - CA-A = BR-F-2: the message leg proceeds over a store the agent leg refuses.
  - CA-B = BR-F-4: a blank-role credentialed register mints and claims the keep, then serves "nothing was written".
- **Added:** CA-1 (#484), the raw stored-record-id render in the refusal → §W item 4.
- **HELD** (no rework): full suite 11498/0; ruff/typecheck/currency GREEN; production-IMAGE dirty-store cutover 34/34 with C0/C1 controls; the ONE-IMPLEMENTATION identifier decision (3 mutation proofs); refusal-count honesty; 8-way×20 concurrency + control; the D3 fold; the DDL verbs.
- **Residuals read:**
  - R-3 → §W 4. R-4 (the "`refused=True` writes nothing" wording) → builder-only item.
  - R-5 = F-2 → i-b (already carried). R-6 → 63c-ii deletes the pair.
  - R-7: a driver label, unreachable in prod. R-8: operator-owned population empty in prod — holds. R-9: auditor misprediction, recorded.
- **Build CHECKPOINT-COMMITTED at `84af63f`** — lead decision, flagged to the operator. The audited tree = patch md5 `5ed71294…` (re-verified before commit). The commit message states NO-GO and names the defects. **Why:** the fix-wave contract edits test files that carried uncommitted builder hunks. A path-scoped commit would have swept them in unaudited, and the commit-at-boundaries law says the tree must never be the only copy. **The wave is NOT closed:** the INDEX "63c-i-a CLOSED" line waits for a re-audit GO.
- Cold auditor retired.
- NEXT: `contract-63c-i-a-a19` (§W 1–5 + CA-1; RED at `84af63f` for the right reason; SAT reference) → NARROW adversary (warranted per amendment 19) → builder fix (+ builder-only items F-8, F-5, F-7, R-4) → cold-audit re-run → lead commit → INDEX.

### 2026-09-25 — contract a19 COMMITTED (`77d9146`); narrow adversary spawned; Task 20 (three readings) → sidecar
- a19 pins amendment 19 §W 1–5 plus CA-1. The author's claims, which the adversary re-derives:
  - 29 RED at `84af63f`, each on its defect;
  - SAT full suite ALONE `-n 12` on a lint-clean reference: `11529 passed / 62 skipped / 3 xfailed / 0 failed`;
  - 13 mutation proofs HELD;
  - no yaml entry needed.
  No attribution trailer (checked). Author retired.
- **SIDECAR TASK 20 — sidecar-63c-2, please confirm or overrule the author's three readings (`REPORT-contract-63c-i-a-a19.md` §8):**
  1. An operator-only owned-but-unscoped store is still REFUSED at i-a; its diagnosis names the operator and E3, never "multi-principal"; the pin carries a bound note for E3's trigger.
  2. The principal-naming bound = `_REFUSAL_ID_SAMPLE_SIZE`.
  3. The shared function is `_agent_migration_preconditions(store)`; only its name and the StoreHandle argument are pinned.
  Also §8.4 (a stated bound): which refusal wins when an owned-but-unscoped store also has an unresolvable operator is unpinned.
  The adversary grades the contract as committed and reports any wrong build that survives only under one reading.
- NEXT: `adversary-63c-i-a-a19` over `84af63f..77d9146` → builder fix → cold-audit re-run.

### 2026-09-25 — Task 20 ADDENDUM (a19 author's candidate doors, `REPORT-contract-63c-i-a-a19.md` §9) — sidecar-63c-2, please also rule:
5. **CD-1:** the message backfill's own `WHERE owner_principal IS NONE` has the same TOCTOU shape F-3 closed for agents, and stays owner-keyed while the agent side moved to scope. The author flags it for 63c-ii. **Lead view:** it is the SAME class in the SAME wave, and amendment 19's own rule — "the wave that changes a predicate's meaning sweeps its consumers" — argues for fixing it at i-a, alongside item 1's message-guard re-key. In i-a or ii? If i-a, it rides a small a19 addendum before the builder (the adversary is already grading; one pin).
6. **CD-2:** for an unsupported/typo'd `--table` on a multi-principal store, the §2.1 teaching is now served before "not supported". Acceptable, or should the table validity be checked first?
(CD-3, the order-guard refusal wording: the builder keeps it derived. CD-4 = F-2, already i-b.)

### 2026-09-25 — amendment 20 (`a212c06` + its §Addendum) ruled Task 20
- §8.1 CONFIRMED. §8.2 CONFIRMED + RIDER: the principal count is READ from `_REFUSAL_ID_SAMPLE_SIZE`, asserting exactly `min(bound, distinct owners)` under the SAME perturbation leg (patch to 3, >3 foreign owners → 3 named). §8.3 CONFIRMED. §8.4 RULED: both conditions → the refusal names BOTH (unresolvable-operator remedy first; owners UNCLASSIFIED); one byte-inert fixture.
- **§Addendum — CD-1 IN i-a:** the message backfill becomes `WHERE scope IS NONE AND owner_principal IS NONE`; message counts go via the shared preconditions function, parametrised by table; golden updated. RIDER: a ∀-tables pin — every governed leg's golden WHERE contains `scope IS NONE`. **CD-2:** table validity FIRST — an unsupported table on a multi-principal store → "not supported", ZERO store reads (spy), byte-inert; control: a supported table → the §2.1 refusal.
- **Lead sequencing:** ONE addendum contract `contract-63c-i-a-a19a` carries amendment 20's riders + CD-1 + CD-2 + any MISSING PINS from the running `adversary-63c-i-a-a19` (awaiting its verdict so one agent touches the contract once). Grading per the sidecar: the cold-audit re-run (or the adversary's receipt). Then the builder fix.
- **Note:** the sidecar ALSO committed `docs/design/2026-09-25-packet63c-amendment-21.md` — same CD-1/CD-2 content, standalone, **superseding** amendment 20's §Addendum (`d53527f`). This is a duplicate the lead's second wake caused; the content is identical. The a19a brief cites amendment 21 as authoritative for CD-1/CD-2, and amendment 20 for §8.1–§8.4.

### 2026-09-25 — adversary a19: INSUFFICIENT (5 MISSING PINS, 0 SAT); LIVE defect #485; unrelated red #486; Task 22 → sidecar
Report `REPORT-adversary-63c-i-a-a19.md` (this commit). SAT CONFIRMED on an INDEPENDENT reference (`11529 passed / 0 failed`); 29 RED at `84af63f` confirmed; no yaml entry needed, confirmed. Adversary retired.
- **MISSING PINS → the a19a addendum (verbatim kills in its §3 / §A):**
  - MP-1 / MP-2 ROUTING-IS-NOT-SHARING: both sharing proofs are one-directional, so a private copy beside the shared function survives → K1/K2 (the reverse redirect).
  - MP-3 ORDER: D-2 says "before the mint", but the pins see only "no keep remains", so mint-then-undo passes → K3 (a `get_or_create_keyed` call spy).
  - MP-4 SERVED PROSE: the re-keyed order guard serves a scope count under the "NONE-owner" noun → PD2 as a pin.
  - MP-5: the F-9 gloss returning in a later clause → a skeleton golden.
  - READING-DEPENDENT WB7b → covered by amendment 20 R1.
- **LIVE-PRODUCTION-DEFECT #485 (flagged loudly; outside §W).** A credentialed register refused by ANY registry rule after the keep mint (role/spawned_by write-once conflict, RetiredAgentError, the provenance pair) keeps the minted `session:<s>` keep with the caller as keeper, then DENIES a third party (SF-63-1). Reproduced at pristine `84af63f` bytes AND on a correct D-2 fix. This is D-2's class stated over one member (blank role) — the QUANTIFIER LAW; the sidecar's own recorded lesson.
  - "Live" = at branch HEAD. The deployed image predates it, and deploy is pkt-65. Not measured by the lead.
- **#486:** an unrelated red, once in 3 full-suite runs (the adversary's §4.2) — surfaced to the operator.
- **SIDECAR TASK 22 — sidecar-63c-2, please rule:**
  1. **#485:** in i-a? **Lead recommends YES** — same class, same wave. Shape per the adversary: the handler validates everything the registry can refuse without a write BEFORE the mint, and row-dependent refusals (conflict/retired) read the row before the mint OR the mint + agent write share one transaction. It needs a ∀-registry-refusals pin, the set DERIVED from the registry's refusal classes, not a hand-list.
  2. **F-1:** amendment 21 CD-2 ("validity first") vs a19's four `∀[brief]` pins. Adversary recommends Reading A: "valid" = the GOVERNED set {agent, memory, message, brief}; only non-governed names get the zero-read "not supported".
  3. **F-2:** a message from an ownerless-but-scoped sender is stamped owner NONE. Is that intended, or must the order guard / message leg require the sender to be OWNED?
  4. **F-3:** the verb-level refusal zeroes `scanned` / `already_migrated` in its receipt. Rule it.

### 2026-09-25 — amendment 22 (`ecc3f57`) ruled Task 22; a19a addendum contract spawned
- **#485 in i-a:** ONE registry `preflight` (which `register` calls first); handler order preflight → mint → register; created-only compensation for the race (a named bound); the ∀-refusal-classes pin DERIVED from `AgentRegistryError` subclasses, with coverage as a CHECKED variable.
- **F-1:** Reading A (valid = the GOVERNED set; amendment 21 CD-2 corrected; the `∀[brief]` pins stand).
- **F-2:** both half-pairs are refused at verb level; post-migrate there is no NONE-owner message; the D-1 control is re-keyed (sidecar erratum).
- **F-3:** refusal receipts serve `None` plus the precondition's own counts.
- MP-1..5 = the adversary's kills. #486 stays the operator's.
- `contract-63c-i-a-a19a` spawned with amendments 20 (R1/R2), 21 (CD-1/CD-2) and 22 (§W 1–6). The #486 instruction: an intermittent red is never counted as green — re-run and report both runs.
- NEXT: a19a → narrow adversary → builder fix (+ the builder-only items F-8, F-5, F-7, R-4, and the memory-without-agent-table note) → cold-audit re-run.

### 2026-09-26 — a19a forks FK-1/FK-2/FK-3 (`REPORT-contract-63c-i-a-a19a.md` §F, working tree) → sidecar as Task 23
The author continues on unaffected items.
- **FK-1 (BLOCKING the #485 pin):** amendment 22 §1's ∀-refusal-classes clause is unsatisfiable. `agents.py` defines 6 concrete `AgentRegistryError` subclasses, and `register`'s call tree raises only 3 of them plus the base (`Unknown`/`Ambiguous`/`IllegalAgentStatus` are unreachable from register). The base's A3 mixed-pair refusal is unreachable through `comms(register)` BY CONSTRUCTION (the handler derives the pair from one principal).
  - Author's Reading A: the derived set = the classes RAISED in `AgentRegistry.register`'s AST call closure (plus the base), coverage checked BOTH ways. The base is covered at registry level (the existing amendment-4 MP-B pins), and its comms-unreachability is a stated bound with a re-open trigger.
- **FK-2 (BLOCKING one F-2 pin):** the post-migrate invariant "no stamped message has a NONE owner" is FALSE for a GHOST sender — a legacy message whose `sender` link names no agent row (record links are not existence-checked). Probed at HEAD: stamped `owner_principal` NONE + the project scope; the owner-keyed WHERE re-stamps it on run 2.
  - Author's Reading A: pin the invariant ∀ populations reachable under the ruled mechanism, and SURFACE the ghost sender as a door.
  - **Lead note:** the ghost sender is a real served-state question — a NONE-owner message in the project scope. It needs a behaviour ruling: refuse the message leg on a dangling sender, or skip-and-report, or accept a named bound, and say whether that is i-a or later. A door with no decision is a can-kick.
- **FK-3 (non-blocking; author picked):** F-1's pointer to "the production constant the five-set resolver pin cross-checks" does not exist, and the derived node set EXCLUDES `brief`. The author's pick is behaviour-wins: valid = {agent, memory, message, brief}. CD-2's invalid probes are derived as the schema tables minus those four, plus a typo. Please confirm.

**SIDECAR TASK 23 — sidecar-63c-2, please rule FK-1, FK-2 (including the ghost sender's behaviour + wave) and FK-3.**

### 2026-09-26 — amendment 23 ruled Task 23 (FK-1..FK-4); relayed to a19a
- **FK-1:** Reading A — the classes raised in `register`'s AST call closure BEFORE the first write, ∪ base; coverage both ways. Exclusions: the post-write "vanished" guards, and the A3 pair (covered at registry level by the amendment-4 MP-B pins; bound + trigger). Sidecar erratum: it had derived reach from the MODULE's class list instead of the FUNCTION's raise set.
- **FK-2:** RULED in i-a. A ghost/dangling sender = the message half-pair → the message leg's shared precondition REFUSES (count + bounded ids, byte-inert, "dangling sender"). Skip-and-report and stamp-to-operator are rejected. The population is expected empty in prod (agents are never deleted). The invariant then holds ∀, ghost included.
- **FK-3** confirmed (valid = the four governed tables incl. brief); **FK-4** confirmed.
- Relayed as `lore_comms` directive (thread `63c`) plus a native wake.

### 2026-09-26 — contract a19a COMMITTED (`16d2d82`); narrow adversary spawned
- The author's claims (re-derived by the adversary):
  - 63 new pins; RED at `84af63f` = 80 (52 new on-defect + a19's 28);
  - SAT full suite ALONE `-n 12`, lint-clean reference: `11592 passed / 62 skipped / 3 xfailed / 0 failed`;
  - 23 mutation proofs HELD; P1c 4 held + 1 under-declared.
  No attribution trailer (checked). The author is retired.
- The author's own contract defect was caught by its SAT run #1: `FakeAgentRegistry` lacked `preflight` (86 reds), so it gained `preflight` plus a mirror pin, in the test tree.
- **Builder contract (D-2):**
  - the handler calls `preflight` BY NAME on the wired registry, with keywords `session`, `role`, `spawned_by`, `owner_principal_id` (no `session_keep_id` before the mint);
  - `get_or_create_keyed` is called by name;
  - the dangling-sender check lives in `principals._agent_migration_preconditions`.
- **§10 candidate doors (9):** the adversary is asked to PROBE and classify #2 (owned-but-unscoped MESSAGE rows — never stamped, yet counted forever; MEDIUM, reasoned only), #4 (compensation masking), #1 (the both-half-pairs diagnosis) and #3 (leg-level refusals still serving zeros). #6/#7 (test-hygiene invariants) → candidates for later.
- NEXT: `adversary-63c-i-a-a19a` over `77d9146..16d2d82` → builder fix → cold-audit re-run.

### 2026-09-26 — adversary a19a: INSUFFICIENT (7 MISSING PINS, 3 NEW DOORS, FK-a); Task 24 → sidecar WITH the STOP-rule question
Report `REPORT-adversary-63c-i-a-a19a.md` (this commit). Verified:
- SAT CONFIRMED on an independent build (`11592/62/3/0`); RED@`84af63f` 80 honest.
- ALL 5 a19 survivors plus #485's PQ1 KILLED.
- 12 wrong builds survive the FULL suite (two composites). #486 did not recur in 3 runs.
Adversary retired.

**Missing pins:**
- **MP-A (REACH, headline):** the ∀-refusal-classes pin (amendment 23's AST raise-closure derivation) fails OPEN on this package's own factory-raise idiom (`raise self._x_refusal(...)`), and counts CLASSES, not raise SITES, so a new post-mint refusal arrives unpinned (N3b, N17). The adversary's cure: fail closed plus per-site coverage, OR the RUNTIME property (KP13) armed around every driven `comms(register)`. **This is the instrument lesson's seventh defeat** — a reach keyed on code SHAPE — and the runtime form is the one CLAUDE.md prescribes as the end of the recession.
- MP-B: created-vs-found is never raced against a concurrent winner (N5).
- MP-C: the race path's refusal text is unpinned (N7).
- MP-D: ONE-IMPLEMENTATION is proven for the blank role only; existing-row decisions can be privately copied in the registry or the handler (N13, N14).
- MP-E: the two new id samples are never perturbed (N11, N12).
- MP-F (under FK-a reading A): leg-level refusals serve an unmeasured `0` (L3).
- MP-G: a failed keep mint degrades to an ownerless register — an old virtue with no pin (N6).

**New doors:**
- #1: which diagnoses a both-half-pairs refusal carries.
- #2 (PROBED, a real non-convergence): an owned-but-unscoped MESSAGE row is never stamped, `report_unmigrated` = 1 forever, `refused=False`.
- #4b: a failed compensation leaves a keep behind with only a log line.

**FK-a:** do the F-3 None receipts cover leg-level refusals? The adversary picks A (yes). FK-b and FK-c are picked, in its §7.

**STOP-RULE (lead, per CLAUDE.md's reach attack):** this fix wave is now on its 3rd contract round (a19 → a19a → next), after ~10 rounds on 63c-i-a overall. MP-A is a receding reach. **Lead recommendation:** close MP-A with the RUNTIME property only (KP13 — observes what `register` actually raises, which ends the recession by construction) rather than another static derivation. Land MP-B…MP-G + the door rulings as ONE final addendum (a19b), ALREADY graded by this adversary's green-on-reference kill probes (§A.3), in the verbatim/AST-equal manner of amendments 16–17. Then the builder. **No further adversary round unless a19b deviates from the graded probes.**

**SIDECAR TASK 24 — sidecar-63c-2, please rule:**
1. MP-A's form: runtime KP13 vs fail-closed static.
2. The three doors #1, #2, #4b — behaviour and wave.
3. FK-a.
4. The lead's STOP-rule proposal: a19b = the adversary's graded kill probes landed AST-equal, no further adversary unless it deviates.
The operator has been told and may override the right-sizing.

### 2026-09-26 — amendment 24 (`301f9b1`) ruled Task 24 — STOP-RULE CLOSE ACCEPTED; a19b (LAST contract round) spawned
- **MP-A:** RUNTIME (KP13). The spy is armed around every driven `comms(register)`, and the covered-call count is a CHECKED variable. `_ClosureWalk` is DELETED. Fixtures stay as drivers. Bound: an undriven new refusal (#137's shape), with a trigger.
- **Doors, all in i-a:**
  - #1: one refusal names BOTH half-pairs.
  - #2: message half-pairs are refused, and `backfilled` = the rows actually stamped.
  - #4b: the teaching survives, plus an appended remedy line naming the left-behind keep (N8 rejected).
- FK-a / FK-b: reading A. FK-c: moot. MP-B..G = the adversary's kill probes.
- **Grading:** a19b lands the adversary's green-on-reference probes AST-equal (receipts against the committed files). The two NEW-behaviour rows (#2's refusal leg, #4b) are graded by the cold-audit re-run. NO further adversary unless a19b changes a probe's assertion. Then builder → cold audit.
- **Operator-visible (§E), surfaced to the operator and NOT acted on by the lead:** the sidecar recommends adding a SEVENTH row to CLAUDE.md's instrument-lesson table — "runtime-refusal reach · keyed on the raise SHAPE in an AST walk · defeated by the package's own factory-raise idiom and by a new raise site of a covered class". CLAUDE.md is the operator's file; the lead does not edit it at a peer's request.

---
## RESUME ANCHOR v4 (2026-09-26, compaction point) — supersedes v3
**Identity:** lead of packet 63c (wave 63c-i-a), branch `feat/surreal-unification`. Ledger name `lead-63c-2` (session `63c-20260924`). Standing rulings: forks/rulings → the sidecar (`sidecar-63c-2`, Fable, long-running, lore client DOWN — directives go as a committed lead-report entry + a native SendMessage wake); only major scope/architecture → the operator. Consumer law + trust doctrine. The lead writes no code.

**State of 63c-i-a:**
- The contract chain is closed through r4b-fix2 (`9298183`), then build → checkpoint.
- **The BUILD is checkpoint-committed at `84af63f`** (cold audit NO-GO: CA-A/BR-F-2, CA-B/BR-F-4, CA-1 #484). The checkpoint commit was a lead decision, flagged to the operator, not yet ruled on.
- **Fix wave (amendments 19–24):**
  - contract a19 `77d9146` → adversary a19 (INSUFFICIENT);
  - a19a `16d2d82` → adversary a19a (INSUFFICIENT, `58f73b4`);
  - **amendment 24 `301f9b1` = STOP-RULE CLOSE ACCEPTED** — a19b is the LAST contract round.
- **IN FLIGHT: `contract-63c-i-a-a19b`** (brief `scratchpad/brief-contract-63c-i-a-a19b.md`). Watcher `bi9zklo7l` (6 h cap) watches for `REPORT-contract-63c-i-a-a19b.md` to be committed. a19b lands the adversary-a19a kill probes AST-equal:
  - MP-A as a RUNTIME KP13 spy, with the covered-call count checked and `_ClosureWalk` deleted;
  - MP-B..G = KP1/KP4/KP5-6/KP2-3/KP7/KP14;
  - door #1 (a both-half-pairs refusal);
  - door #2 (the message half-pair refused; `backfilled` = stamped rows);
  - door #4b (an appended remedy line);
  - FK-a/FK-b reading A.
  If an adaptation CHANGES a probe's assertion, a new adversary is required; otherwise NONE.

**NEXT (in order):**
1. a19b commits → check: no attribution trailer, the AST-equal receipts vs the committed files, the SAT full suite ALONE `-n 12` at 0 failed, both helper shapes. TaskStop it; retire it on the ledger; log it.
2. Spawn the **builder fix** (opus55-worker, a fresh name such as `builder-63c-i-a-fix`) on top of `84af63f`: amendments 19–24 as pinned by a19 + a19a + a19b. Also the builder-only items: F-8 (the lorerunes/agents.py threat-model prose → #219's rationale), F-5 (the `_owner_count` docstring), the F-7 DUAL line, R-4 (the "a `refused=True` writes nothing" wording). Carry the a19a D-2 builder constraints:
   - the handler calls `preflight` BY NAME, with keywords `session`, `role`, `spawned_by`, `owner_principal_id`, and no `session_keep_id` before the mint;
   - `get_or_create_keyed` is called by name;
   - the dangling-sender check lives in `principals._agent_migration_preconditions`;
   - the memory table still migrates on a store with no agent table;
   - plus a19b's BUILDER CONSTRAINTS section.
   No commit, no deploy; back up the patch (use the `git diff --no-index` trick to include new files).
3. **Cold-audit re-run** (Opus REFUTE, full suite ALONE, dirty-store probe with controls) — it also grades a19b's two new-behaviour rows (#2's refusal leg, #4b's remedy line) — plus a contract-blind diff reader.
4. GO → the lead commits → INDEX Log "63c-i-a CLOSED".
5. Then 63c-i-b, carrying:
   - C-3 + #467;
   - F-2/CA-3 = the third raw-CREATE clone in `test_comms_schema.py`;
   - the dead `None` branch;
   - N-2 hypothesis `@seed` hardening;
   - fix2 CAND C-1;
   - "a sampling-strategy change carries a DUAL leg";
   - "derive reach from the thing whose behaviour you pin".
6. Then 63c-ii (C-1 union; the brief leg inherits the scope-keyed WHERE) → security auditor → packet close (git mv reports to `docs/plans/v2/receipts/2026-09-24-packet63c/`, INDEX, lore_remember, stop the sidecar).

**OPERATOR DECISIONS PENDING:**
- (a) the stop-rule close (amendment 24): stand, or a 6th adversary;
- (b) add the 7th row to CLAUDE.md's instrument-lesson table (the text is in amendment 24 §E — the lead does NOT edit CLAUDE.md at a peer's request);
- (c) **#486** — an unrelated intermittent red (`test_memory_replay_fidelity_63b_ib.py::…test_a_cross_owner_replay_close_is_skipped_with_a_warning`, an un-retried "Resource busy" = a call site bypassing the retry seam; possibly the new 4 GiB spike budget — GUESS);
- (d) the checkpoint-commit-of-a-NO-GO-build decision (`84af63f`);
- (e) memdiag R1 (harness PG `shared_buffers` 8→2 GB) and R6 (**EDAC: a degrading DIMM**).

**Host / memory (2026-09-25):**
- SurrealDB ENGINE budgets were applied (operator directive; engine env only, no cgroup): prod lore-surreal 8 GiB (4.5 GiB cache + 26×128 MiB write buffers + 0.25 GiB HNSW); spike 4 GiB (2 GiB + 14×128 MiB + 0.25 GiB). Receipts are in `REPORT-surreal-memcap-2.md`.
- Memory causes (`REPORT-memdiag-1.md`): the harness PG pods' pinned shmem; the Surreal stores. ARC is NOT a cause.
- Grants: `-n 12` ≥23 GB, `-n 8` ≥20 GB; watchdog kill-line **15 GiB, ≤10 s poll**; one pytest at a time; never a bare `--currency`; kill by PID.

**Landmines:**
- Agents self-retire on the ledger, so lore_comms directives to them then FAIL: use a fresh agent for follow-ups.
- The builder's backup patch must include untracked files.
- Stale idle notifications from stopped agents get zero tool calls.
- The `feat/surreal-unification` tree has only `REPORT-sidecar-63c.md` untracked (archive at packet close).

**Findings filed this session:** #482 (lore_search >120 s), #483 (reconcile client abort at 300 s), #484 (CA-1), #485 (register mint side effect — being fixed), #486 (the unrelated red).

**Live agents to KEEP:** `sidecar-63c-2`, `contract-63c-i-a-a19b`. Everything else is retired.

### 2026-09-26 — FORK FK-a19b-1 (a19b door #2 "both halves" vs the standing CD-1 pin) → sidecar as Task 25
Raised in `REPORT-contract-63c-i-a-a19b.md` §F (working tree). The author continues on all other items, landing half (i) + the D2 leg now.
- **Reading A** (literal, "symmetric with agents"): refuse BOTH (i) owned-but-unscoped and (ii) scoped-but-ownerless message rows. This CONTRADICTS amendment 21 CD-1's pin `test_fixwave_a19a_63c_i_a.py::…::test_a_scoped_but_ownerless_message_is_never_restamped_and_counts_as_migrated`, which requires (ii) to proceed (`refused=False`), so that pin must be re-keyed (DUAL; its "never restamped" virtue survives as byte-inertness). No writer produces (ii) (measured from `_comms_send`), so the population is expected empty.
- **Reading B:** only (i) is a message half-pair.
- The author picks A.
- Also flagged: the D2 pin has no graded adversary probe (SP2 was print-only), so it is AUTHORED here and graded by the cold audit.

**SIDECAR TASK 25 — sidecar-63c-2: rule A vs B (and the CD-1 pin re-key if A).** Relay the ruling to `contract-63c-i-a-a19b` via the lead. NOTE: the lead is compacting — the anchor-v4 successor must relay amendment 25 to a19b (a lore_comms directive + a native wake; fall back to a fresh agent if a19b has self-retired).

### 2026-09-26 — amendment 25 ruled Task 25 (FK-a19b-1 = Reading A); RELAYED to a19b before compaction
- BOTH message half-pairs are refused in ONE refusal (each half gets its own count + bounded ids; byte-inert).
- The CD-1 pin is re-keyed by DUAL: byte-inertness survives, and "counts as migrated" is dropped.
- CD-1's scope-keyed WHERE stays (defence at the write).
- Reading B is rejected. The D2 pin is authored and cold-audit graded.
- Sidecar erratum: amendments 21 and 24 gave one population opposite verdicts.
- Relayed as `lore_comms` directive (thread `63c`, sender `lead-63c-2`) plus a native wake. **The anchor-v4 "first action after compaction" relay is DONE.** Proof of receipt = the a19b report citing amendment 25.

### 2026-09-26 — OPERATOR RULINGS: 64 fork F0 + INDEX pool 30 (recorded in INDEX)
- **F0 = design + contract AHEAD of 63c.** `sidecar-64` (a new Fable, separate from `sidecar-63c-2` so 63c queries never queue behind 64) rules 64's kickoff forks F1–F9 (+ #417). Then the 64b (findings) contract → adversary, NEW test files only. Edits to 63c-shared files are held as a written integration patch; SAT re-runs on the final 63c base. Every 64 build stays serial after 63c. Pytest stays single-lane — 63c's runs have priority.
- **Pool 30 = 58 FIRST.** 64a (tasks) waits on 58. **58 has no lead yet** — surfaced to the operator.
- Brief: scratchpad `brief-sidecar-64.md`.

### 2026-09-26 — 64 kickoff rulings committed (`e5fa7f9`, sidecar-64); OPERATOR RULINGS on OF-1/3/4, OF-2 pending
- **OF-1 = (A):** tasks default to the PROJECT keep. `scope=principal-private` is an explicit, PDP-validated request. 64a is unblocked on this axis; it still waits on 58.
- **OF-4 = ACCEPT, pinned:** the global finding `number` count-leak bound carries into a hosted 65, with the served sentence and a re-open trigger (§10).
- **OF-3 = OPERATOR DIRECTIVE (neither offered option), verbatim intent:** principal/owner deletion takes a REQUIRED choice of `--delete-obj` | `--archive-obj` | `--change-owner <target>`. **The designer decides how archive works.** Archived objects are RETAINED but HIDDEN unless specifically requested. This replaces the sidecar's §10.7-Z orphaning (64d). Relayed to sidecar-64 as **Task 2** (amendment doc): the verb shape, archive semantics (store representation, read-filter default, the "show archived" request surface, served counts/labels per the trust doctrine), per-table behaviour, the #404 and #488 interaction, 64d sizing, riders.
- **OF-2 = operator asked for more info** — explained, answer pending. The 64b contract waits on OF-2, because F5 changes findings' `created_by`/`actor` args.

### 2026-09-26 — a19b COMMITTED (`9353445`), VERIFIED, RETIRED; SIDECAR TASK 26 (R-3)
- **Verified by the lead:**
  - no attribution trailer;
  - amendment 25 (`027a3a3`) cited: half (ii) refused, the CD-1 pin re-keyed by DUAL;
  - **AST receipt RE-RUN by the lead on HEAD:** blob `9a93e8d5`, 14/14 AST-EQUAL, 7/7 positive controls DIFFERENT; instrument md5 `b471475c…` matches the report's §A.3;
  - claimed: RED@`84af63f` 80 failed / 16 passed; SAT full suite alone `-n 12` 11625 passed / 62 skipped / 3 xfailed / 0 failed, lint-clean; mutation 33/33 HELD;
  - §10 BUILDER CONSTRAINTS present (9 items).
- **For the cold audit to grade:** D-1 (KP12 not landed; argued as the pinned #137 bound) and D-2 (KP5/KP6 red via AttributeError; verbatim wins). The process-table disclosure (a peer's pytest was live at the first RED run) is noted.
- a19b TaskStopped; ledger heartbeat set to `retired`.
- **SIDECAR TASK 26 — sidecar-63c-2, residual R-3:** a store holding BOTH a door-#2 message half-pair AND a dangling sender is unruled. a19b's reference names both in ONE refusal; nothing pins it. Rule: one refusal naming both (and in what order), or precedence? Is a pin required, or is it graded by the cold audit? The builder spawns after this ruling so the brief carries it. FYI, no action: sidecar-64 flagged #488 (amendment 25's half (ii) vs 64's owner-deletion wave). The operator re-shaped that wave (OF-3: `--delete-obj`/`--archive-obj`/`--change-owner`); sidecar-64 designs it and may ask you.

### 2026-09-26 — amendment 26 (`0ca5bdb`) + 64 amendment 1 (`6797d63`, report `98c5314`) landed; OPERATOR OF-2 = RETIRE AT 65
- **Amendment 26 (R-3):** ONE refusal naming BOTH, in check order (dangling senders first, then half-pairs); each counted and bounded; byte-inert. The builder builds it now; the pin goes to i-b via the cold audit's residual.
- **64 amendment 1 (OF-3):** `lore-adm delete` takes a REQUIRED `--delete-obj | --archive-obj | --change-owner <agent@session>`; archive = a 4th governed column `archived_at` + a `NotArchived` PDP node; `include_archived`; #404 closes, #488 moot; 64d ≈0.20–0.25, split into 64d-i archive / 64d-ii delete.
- **OF-2 = RETIRE AT 65 (operator, overriding the sidecar's recommendation):** `created_by`/`actor`/`owner` on `lore_tasks`/`lore_findings`/`lore_claim_task` become foreign-param refusals at the 65 cutover, together with `capability=` required. Relayed to sidecar-64 as **Task 3**: revise F5/§6 + riders + the §14 inventory, and say which 64 wave lands the refusal (nothing deploys before 65).
- All four sidecar commits checked: no attribution.
- Builder fix spawning: `builder-63c-i-a-fix`, brief in scratchpad `brief-builder-63c-i-a-fix.md`.

### 2026-09-26 — findings routed; inbox drained
- **#487 → 63c-i-b carry list.** The enforced 63b message-family verbs (send/drain/ack/await/story) leave `_GOVERNED_VERBS_PENDING_ROUTING` with `@observes_routing` markers. The #420 pin gains the REVERSE direction: an enforced verb, or a marked one, that is still pending goes RED. 64's contract carries the reverse pin regardless. Annotated on the finding.
- **#488 → moot under 64 amendment 1** (OF-3 produces no orphan state; amendment 25 stands). Kept open until 64d-ii closes. Annotated.
- `lore_comms` inbox drained: 30 historical pointers, no new action.

### 2026-09-26 — OPERATOR: packet 58 runs AHEAD in parallel (same shape as 64's F0)
- The operator asked for agents on 58 in parallel. Applied as for 64: DESIGN + CONTRACT + ADVERSARY now. The BUILD is serial in the shared tree, slotted after the 63c-i-a commit and before the 63c-i-b build: 58 is ~0.20 and `tasks.py`-centred, disjoint from 63c. Any 63c-shared edit (e.g. #130's claim-loss render, if it lives in `server.py`) is held as a written integration patch.
- 58's forks: F-1 hub cap, F-2 terminal dependents, F-4 extraction owner vs 57. F-3 is moot, because 58 lands before 64. Routed to **sidecar-64 as Task 4**, queued after Task 3; sidecar-64 already holds the `tasks.py` context from its pool-30 read.
- **Pytest lane priority** (lead call; single lane per #466): 63c, then 58, then 64b. The 58/64b agents wait up to 90 min, not 30, before reporting `blocked`.

### 2026-09-26 — OPERATOR DECISIONS (a)–(e) + 64 amendment 2 landed
- **(a) The amendment-24 STOP-rule close is ACCEPTED:** a19b is the last contract round, and the cold audit grades the new behaviour.
- **(b) CLAUDE.md gains the 7th instrument-lesson row** (this commit): runtime-refusal reach · keyed on the raise SHAPE in an AST walk · defeated by the factory-raise idiom and by a new raise site of a covered class. Counts updated (seven defeats; a hidden constant is now the "eighth" waiting). The global `~/.claude/CLAUDE.md` "six instruments" wording is NOT touched (not asked).
- **(c) #486 → investigate, read-only now.** Agent `investigate-486`: trace the un-retried "Resource busy"; no fixes, no full suite.
- **(d) FYI given:** the NO-GO checkpoint `84af63f` sits on the branch under the fix wave. No objection raised.
- **(e) Harness Postgres = operator handles it separately.** Memory pressure is relaxed. **BACK TO FAST PYTEST:** every NEW brief uses `-n auto`, one pytest session at a time (#466 ports). The 15 GB PID watchdog stays; the 23/20 GB launch floors are dropped. The in-flight builder keeps `-n 12` (not steered mid-run). MEMORY.md landmine line updated.
- **64 amendment 2** (`2ea52fe`, report `a761b71`): OF-2 retire-at-65 designed; §12 confirmed for the 64b author. **64b contract author spawning.** The lane order stays 63c, then 58, then 64b.
- The memory stick (EDAC DIMM) is dropped per operator.

### 2026-09-26 — 58 kickoff rulings landed (`c8d3241`, sidecar-64 Task 4); contract-58 spawned
- F-1: refuse-and-teach at a DERIVED cap (cap−1/cap/cap+1 pinned). F-2: rewire ∀ dependents, incl. terminal. F-4: 58 extracts, 57 consumes (AST one-producer pin). The shell shape = the seam 64a governs. #130 (a) the claimable partition; (c) already present. Held patch = the `server.py` supersede render + `SupersedeResult`. Commit is attribution-clean.
- #489 (cross-ledger guarded-append unification) is ledgered with a trigger ("the third ledger"), pinned per module. It is NOT built.
- `contract-58` spawned (brief `brief-contract-58.md`; new test files + DUAL-commented task-ledger test edits; lane priority 63c, then 58, then 64b).
- **Operator question pending:** fix #466 (fixed wire-test ports) now to unlock parallel pytest, or leave it in 09b.

### 2026-09-26 — 64b split ruled; amendment 3 (`aea2a9d`); probe-64 spawned; #466 under /tdd-light
- contract-64b priced 64b at ≈0.33–0.40. The lead ruled the §12 split TRIGGERED (64b-i = substrate + writes + migrate first; 64b-ii = reads later) and that the author owns SAT (directive #17027).
- Amendment 3 (sidecar-64 Task 5): D-1b = Reading A (64b-i flips 7 writes + `set_scope`; reads stay False with a foreign-param teaching on `capability=` until 64b-ii). D-3 = a committed `scripts/restore_prod_dump.py`, built now by one-shot **probe-64**; the S2 leg is marker-gated on its receipt. Relayed as directive #17029 + wake. Attribution-clean.
- **#466 (operator: "Fix #466 now using /tdd-light"):** Phase-0 discovery CORRECTED the premise. No fixed port; the defects are a bind-0→close→rebind race (4 hand-rolled `_free_port` copies) plus startup timeout and EADDRINUSE being indistinguishable. Annotated on #466. Phase 1: `contract-466` (tdd-light-contract). Deviation from the skill: RED/GREEN are scoped runs plus a concurrent-pair acceptance driver, not the full suite, because the shared tree carries 63c's in-flight reds.

### 2026-09-26 — build delivered; audits + 58 adversary spawned; #486 diagnosed
- **builder-63c-i-a-fix DONE** (not committed). Full suite alone `-n 12` 11625 passed / 62 skipped / 3 xfailed / 0 failed; RED@HEAD 108 → all green, 0 regressions. The lead VERIFIED the working tree == its patch (md5 `b23f3e43…`, 6 production files, zero test edits). Open items: FORK-1 (the agent leg's `backfilled` is still a pre-count), FORK-2, DV-2 (#4b compensation inlined) → **sidecar-63c-2 Task 27**. #490 filed (lore_search timeout). TaskStopped.
- **coldaudit-63c-i-a-2 + blindreader-63c-i-a-2 spawned.** The audit grades HEAD + patch `b23f3e43` in a scratch copy reset to HEAD (the peers' contract-ahead reds excluded). It grades the ungraded new behaviour (door #2, D2, #4b, am-26, a19b D-1/D-2, DV-2), and runs a REAL dirty-store probe via `scripts/restore_prod_dump.py` on the 08-03 prod dump. It has lane priority.
- **contract-58 DONE `5a43aeb`:** RED@HEAD 68; 14/14 mutation HELD; SAT "set-equal to the HEAD baseline"; absorbed 58 amendment 1 (`f4e96b4`). Disclosed a `pkill -f` process slip (its own shell only). §DECISIONS (a)/(b) → **sidecar-64 Task 7**. TaskStopped. **adversary-58 spawned.** Its SAT base = HEAD + the 63c patch + §HELD, and it must prove §HELD applies over 63c's `server.py`.
- **probe-64 DONE `80409f4`:** `scripts/restore_prod_dump.py`, 16 tests + a 13/13 self-test. The first measurement of the real legacy population (08-03 dump): finding 324 · task 116 · agent 95 · memory 177 · message 316 · brief 26, all `scope IS NONE`. D1/D2 → sidecar-64 Task 7. ⚠ FLAG for the operator: the `lore_test` namespace on spike holds ~3,900 databases (suite residue). TaskStopped.
- **investigate-486 DONE `081782e`:** a test-harness escape (`_surreal_harness.run` bypasses `_run_under_store_retry_seam`); the contender is engine index compaction; 24 exposed writes in 8 files. **Operator: fix via /tdd-light after the #466 cycle.** TaskStopped.
- **58 amendment 1 `f4e96b4`** (sidecar-64 Task 6): FORK-A = A1, FORK-C = R1 closed in-txn + R2 healed at boot. #491 filed.

### 2026-09-26 — #466 tdd-light Phase 1 reviewed + committed (`37de0a7`); Phase 2 stub; D-SAT ruled
- **contract-466 reviewed by the lead** (tdd-light: no approval pause). The helper home `loremaster.testing.loopback` is ACCEPTED (lorerunes is stdlib-only; one home serves both trees, and the skill-idiom import is proven). Spike = ROUTE. Guard = AST now, runtime at the trigger. 27/27 on the reference; 11 wrong builds all RED; the guard's RED@HEAD = exactly the 4 declared files. Committed `37de0a7`. **Operator decisions surfaced:** #492 (lore-deploy `_free_port` has the same race in PRODUCTION, exempted in the guard with a trigger) and §E (the `-n auto` gate leg; 15 s startup timeout = measure-then-tune). #493 filed (lore_search filter-miss). contract-466 TaskStopped (tmux pane limit hit). **stub-466 (tdd-stub) spawned.**
- **Directive #17038 → coldaudit-63c-i-a-2 + adversary-58:** HEAD carries contract-ahead reds from 58 (`5a43aeb`) and #466 (`37de0a7`), so grade as a diff vs a HEAD baseline.
- **contract-64b D-SAT RULED (i)** (directive #17037): the author converts the 115 corpse tests (builders never edit tests), with DUAL verdicts. test_mcp_server/test_comms_footer edits land in its commit and are listed in §HELD re-verification.
- sidecar-64 **Task 8**: add probe-64's measured `POST /import` facts to the store reference §6.

### 2026-09-26 — sidecar rulings: 63c amendment 27; 58 amendment 2; 64 amendment 4; store-ref §6.7 (all attribution-clean)
- **63c am-27 (`40c188d`, Task 27):**
  - FORK-1 = Reading B: `backfilled` = rows stamped ∀ legs, pinned by a ∀-legs byte-diff over `_migrate_legs`.
  - FORK-2: the message leg's ORDER → dangling → half-pairs serve ONE refusal in check order; the verb-level §2.1 refusal keeps precedence.
  - DV-2 ACCEPTABLE (one policy at one site); i-b extracts `_release_the_minted_session_keep` + a `_RENDER_OUT` entry.
  - Each lands in the cold audit's fix pass if one opens, else as 63c-i-b's first rows. The patch under audit is untouched.
- **58 am-2 (`e0760fd`, Task 7a):** `owner=` serves a held superseded row, decorated; `status=`/`blocked=False` exclude it. The boot heal CHUNKS at the derived cap and never refuses. → directive #17041 to adversary-58: grade the contract against it; missing am-2 pins are expected MISSING-PIN findings.
- **64 am-4 (`17b7101`, Task 7b):** D1 hand-list ratified as a checked variable (decay/growth pins); D2 required/ABSENT ratified with derived provenance; S2 floor = task 116 / finding 324. Erratum on am-3's symbol citation. → directive #17042 to contract-64b; the driver changes are BUILDER items.
- **Store reference §6.7 (`aa1d3d6`, Task 8):** the `POST /import` vendor-vs-3.2.4 facts, with provenance from probe-64 (the sidecar's own re-probe was permission-denied at the secrets read).
- In flight: the test-DB cleanup agent (operator-approved: stale `lore_test` DBs, dead-pid only). **Operator question pending: admin-chosen port for lore-deploy (#492).**

### 2026-09-26 — blindreader-63c-i-a-2 DONE (`8e7aa2b`): 1 BLOCKER + 2 MAJOR → sidecar Task 28 (design escalation)
- **F-1 BLOCKER:** the created-only race compensation deletes a keep the concurrent same-principal WINNER found and scoped to, stranding it permanently. Derived by reading; NOT yet executed.
- **F-2 MAJOR:** preflight-before-SF-63-1 leaks agent existence, retirement, role and spawner to a foreign principal.
- **F-3 MAJOR** = builder FORK-1 (already ruled, am-27).
- This is the second fix wave on one gate → escalated the DESIGN to sidecar-63c-2 as **Task 28** (amendment 28: confirm/refute + a construction recipe + remedies + operator need). The cold audit continues independently; no fix is briefed until the audit verdict and am-28 both land.

### 2026-09-26 — OPERATOR RULING #492: the port is admin/agent-picked and defined in config
- The lore server port is picked by the admin (or by an agent via the lore-deploy skill) and defined in lore.yaml `server.port`. It is never auto-picked (MCP connections would break). Fix queued as a **tdd-light cycle after #466 → #486**: `setup` requires an explicit port when scaffolding (teaching refusal otherwise); `_free_port` is deleted; a pre-flight free-check runs on the PUBLISH address; SKILL.md teaches it; the #466 guard exemption is removed. Annotated on #492.
- Blindreader addendum (the race fixture blind to F-1; F-4 silent-proceed; F-5..F-7 MINORs) sent to sidecar-63c-2 for amendment 28.
- **tdd-light queue (serial, operator):** #466 (at stub) → #486 (harness `run()` via the retry seam) → #492 (admin-picked port).

### 2026-09-26 — amendment 28 (`eb75f57` + addendum `17c52b7`): F-1/F-2 CONFIRMED, design changed; test-DB cleanup; #492 CLI option
- **Am-28 (Task 28, second-fix-wave trigger):**
  - F-1 → NO race compensation: delete the branch + `minted_by_this_call`; KP1 re-keyed to the winner's live scope; door-#4b pins DUAL-deleted.
  - F-2 → a read-only gate BEFORE preflight, mint after, the post-mint re-check kept.
  - Addendum A1–A5: the race pin re-keyed to a same-principal winner; F-4 fails CLOSED on a wrong-shape INFO FOR DB; F-5 moot; F-6 docstring derived + measured counts served; F-7 sender-side WHERE guard.
  - **Process:** a contract delta (the 2 recipe pins + DUAL deletions + A1–A5; the lead also folds am-27's FORK-1/2 pins and am-26's pin, which are cheap and in the same area) → a NARROW adversary delta → the builder fix pass → the cold-audit re-run. Briefed AFTER coldaudit-63c-i-a-2's verdict so its findings join the same pass.
  - §E: `delete_keep`'s orphaning → packet 64 (sidecar-64 Task 9: confirm 64 am-1 covers `lore-adm delete-keep`).
  - Attribution-clean.
- **Test-DB cleanup (operator-approved):** dropped 1873 dead-pid `test_<pid>_<hex>` DBs (3984 → ~2111), 0 failures, :18000 only. **FOUND a growing leak:** ~2077 `test_<uuid>` DBs with no pid → **operator: fold into the #486 tdd-light cycle** (trace the minting site, route it through `unique_database()`, add a guard, reap when no pytest runs). The probe DBs (probe07a_/probe_await_/pc_/probe_smoke/x1_) → operator: DROP (cleanup agent resumed).
- **#492 addendum (operator):** add a `--port` CLI option as well; lore.yaml stays the source of truth MCP wiring reads (annotated).

### 2026-09-26 — lane ruling (lore-scoped); cold-audit prod-dump restore permission-DENIED → operator
- A foreign project (`mobile-pricepaper-smoke`) runs pytest continuously, so a box-wide lane never clears. coldaudit's waiter also self-matched its own wrapper (#228; adversary-58's catch). **Ruled (directive #17046):** the single-pytest rule is LORE-scoped (one lore pytest at a time; detect by executable + lore path, never args text). Order: coldaudit, then adversary-58, then contract-64b. The 15 GB watchdog stays; a full suite runs at -n 12 while a foreign pytest is live.
- **The coldaudit FOCUS 5 prod-dump restore was DENIED by the auto-mode permission classifier ("Modify Shared Resources").** Not retried, not routed around; surfaced to the operator. The staged commands are in REPORT-coldaudit-63c-i-a-2.md §5.
- Cleanup: 36 probe DBs dropped (2095 → 2059). The `test_<uuid>` leak (~2050) is left for the #486 cycle.

### 2026-09-26 — 64 amendment 5 (`9fd34d3`, sidecar-64 Task 9): standalone delete-keep orphaning REFUTED as covered → ruled into 64d-ii
- 64 am-1 covered only principal deletion. `lore-adm delete-keep` orphans keep-scoped rows at HEAD (no production exposure: the keep substrate is commit-only until the 65 cutover). Ruled into 64d-ii: the same REQUIRED choice `--delete-obj | --archive-obj | --change-scope` (the keep analogue of the operator's OF-3 `--change-owner`); ONE `dispose_population` engine for both verbs; a refuse-when-populated guard on `KeepStore.delete_keep`. #488 annotated. Attribution-clean.
- contract-64b directive #17047: the `_governed_contract.py` fold is §HELD-only; no §13 shared file in its commit.
- Operator pending: the coldaudit prod-dump restore permission (allow rule / operator-run / skip).

### 2026-09-26 — adversary-58: CONTRACT INSUFFICIENT; 7 HEAD reds from OUR scripts
- **adversary-58 (report at root, uncommitted per its brief):**
  - 13 wrong builds survive (14 MISSING PIN · 3 SAT DEFECT · 6 NEW DOOR). Worst: WB1 (a real store fault served as the R1 "retry" teaching), WB2 (a K-ignoring cap → a bare compose error), WB6/PR17 (the heal FAILS THE BOOT), WB7 (#130 under LIMIT).
  - **58 am-2's chunk sizing is itself defective** (rows vs statements → never converges; its own pin passes the defective build).
  - SAT on the right base (HEAD + 63c patch + §HELD + its build): 22F/11743P. 3 reds are 58-attributable (incl. the missing `_GUARDED_CAS_DOORS` row `tasks.py::claim_task`). §HELD applies clean over 63c (hunks disjoint; re-check after 64b edits test_mcp_server.py).
  - Disclosed: its SAT runs used `-n auto` before draining #17046.
  - → **sidecar-64 Task 10** (58 am-3: am-2 defect, fail-open vs FAILS_LOUD sweep, D12 order, MP14/MP8/MP5), then a **contract-58-r2** revision. adversary-58 TaskStopped.
- **7 unrelated HEAD reds are OURS, missed by scoped-only runs:**
  - `scripts/restore_prod_dump.py` (probe-64, `80409f4`) breaks 5 secret-seam invariants + the anchored-pattern seam → **fix-restore-seams** spawned (fix the script, not the invariants).
  - `scripts/concurrent_wire_acceptance.py` (#466, `37de0a7`) breaks the anchored-pattern seam → folded into the #466 GREEN phase.
  - Lesson: a committed script needs the repo-wide invariant tests, not just its own.
- **Pre-existing, surfaced:** `scripts/esc1_write_path_cycle_closure.py` exits 1 at HEAD since #174 (`[boundary-5] successor is born with NO dependencies`) and breaks post-58 typecheck. Owner: 58's build (the exact edit is in contract-58 §FLAGS 1).

### 2026-09-26 — 58 am-3 (`7266c1b`) ruled adversary-58's items; contract-58-r2 spawned; #466 at GREEN
- **58 am-3 (sidecar-64 Task 10, none MAJOR):** (1) erratum: heal chunks sized by their own composed count via ONE shared counter; (2) store faults LOUD (FAILS_LOUD sweep unedited), only domain rejections isolated, order backfill → heal; (3) claim loss = typed `claim_lost` at DEBUG; (4) refuse only cycles through X'; (5) phantom head skipped + recorded; SD1–SD3 (`claim_task` joins `_GUARDED_CAS_DOORS`). Attribution-clean.
- **contract-58-r2 spawned:** MP1–MP18, SD1–SD3, am-2/am-3, AST-equal probes, SAT with every red adjudicated, §HELD re-derived over the 63c patch.
- **#466:** Phase 3 RED verified by the lead (32/32 NotImplementedError; 0 structural). Stubs committed `fe45d1a`. **impl-466 (Phase 4 GREEN)** spawned: helper via uvicorn `sockets=` + HTTPServer, `include_testpaths`, the 4 copies switched + deleted, and the `concurrent_wire_acceptance.py` seam red.
- **fix-restore-seams** (the 5+1 seam reds from `restore_prod_dump.py`) running.

### 2026-09-26 — coldaudit-63c-i-a-2 NO-GO (`8ae642f`); checkpoint `169925f`; fix pass started
- **NO-GO, and it converges with blindreader-2 + am-28 by EXECUTION:**
  - F-2 BLOCKER: the created-only compensation strands concurrent same-session agents (8-way: 2/20, 8/20, 11/20 rounds; HEAD 0/20).
  - F-1 MAJOR: preflight-before-SF-63-1 leaks role/spawned_by/retired to a foreign principal.
  - F-3/F-4 = am-27. F-8 pin gap (door-#2 count swap). F-5/F-7/F-9 moot under am-28.
  - Confirmed: 108 fixed / 0 regressions; ruff GREEN; mutations A–D HELD (preflight and preconditions each ONE decision).
  - FOCUS 5 (the real prod-dump restore) permission-DENIED → operator-pending.
- **F-6 (HEAD, not this patch):** the close-out currency gate is RED_ORPHANED, with 31 unowned reds: 7 from `restore_prod_dump.py` (fix-restore-seams running) + 24 of packet 58's committed contract reds not in `pending_contracts.yaml`. **Process gap: a contract-ahead commit must own every pytest red it introduces.** Directive #17055 → contract-58-r2 + contract-64b.
- **Checkpoint:** the audited build committed as `169925f` (md5 == `b23f3e43`; NO-GO labelled, as `84af63f` was).
- **Fix pass:** contract-63c-i-a-a28 spawned (am-27 FORK-1/2; am-28 §F-1 no compensation with the RS-2 8-way pin, §F-2 read-only gate first with the RS-3 pin, addendum A1/A2/A4/A5; the am-26 RS-1 pin; F-8; currency ownership). Next: the NARROW adversary delta on the F-1/F-2/race pins → the builder fix → the cold-audit re-run.
- sidecar-63c-2 **Task 29**: RS-5 (a raw TxnDomainRejectionError for a same-role concurrent loser, pre-existing) + an F-8 fold FYI.
- **Lane order:** contract-63c-i-a-a28, then contract-58-r2, then contract-64b (impl-466 small scoped runs allowed).

### 2026-09-26 — #466 GREEN committed (`6566ba6`); Phase 5 spawned; forks routed
- **impl-466 GREEN, lead-VERIFIED:** #466 contract + test_migration_wire `72 passed`; skill suite `120 passed`. No assertion lines changed in the switched test files (the D4 `dead_port` params are signature-only). ruff clean. Committed `6566ba6` (7 files + report). Remaining reds NOT #466's: restore_prod_dump anchored seam (fix-restore-seams running) + the 64b untracked whole-tree clones → directive #17057 to contract-64b. **refactor-466 (tdd-refactorer, model opus)** spawned for review → refactor → the 20× concurrent-pair acceptance.
- **contract-58-r2 FORK-1:** am-3 SD3 (`claim_task` into `_GUARDED_CAS_DOORS`) contradicts am-3 decision 3 (a typed catch = not a door) → **sidecar-64 Task 11**; the author proceeds on reading A.
- contract-64b disclosed a lane breach (an orphaned pytest child after it killed only the wrapper), recorded in its report §0 D-e. Lesson: kill the process TREE.

### 2026-09-26 — am-29 (RS-5 fixed now; F-8 folded) → a28; 58 am-4 (SD3 erratum) → r2; fix-restore-seams 6/7
- **63c am-29 (`a92d33e`):** RS-5 = a CONSUMER-LAW defect, FIXED in this pass (CREATE's unique-id rejection caught by CLASS → the existing re-register path; P5 8-way pin, 20 greens + sequential), riding the narrow delta. F-8: per-clause count attribution. → directive #17059 to contract-63c-i-a-a28.
- **58 am-4:** Reading A (SD3 was the sidecar's erratum; a typed catch is not a door; the enumerator widens as r2's item). → directive #17060 to contract-58-r2.
- **fix-restore-seams `441f3b0`:** 6/7 seam reds GREEN (httpx.BasicAuth, python-dotenv removed from the script, 5 `.fullmatch` sites); script 16/16, self-test 13/13. The last red needs an `UNWRAP_ALLOWLIST` ruling (fills the 5..7 bound's ceiling). FORK A: creds from the harness, not the stores' env file (which carries prod secrets); lead leans ratify. → **sidecar-64 Task 12**.

### 2026-09-26 — am-30 (`c622254`): FK-a28-1 = Reading B (typed counts)
- The measured precondition counts become TYPED fields: `MigrateGovernedResult.preconditions: MigratePreconditionCounts | None` (six `int | None` fields; None = not measured). The reason text is DERIVED by ONE describe function from the fields; pins are parametrised over `model_fields`. Relayed as directive #17062 (my wake message misquoted it as #17061; the agent drains the thread, and proof = its ack of #17062). Attribution-clean: c622254 / a92d33e / fd6497d.

### 2026-09-26 — 64 am-6 (`c8147d9`) applied; the restore-script seam reds are CLEARED
- Am-6: (1) the `build_auth_headers` UNWRAP_ALLOWLIST entry is ratified as evidence-backed (lift trigger = the 2nd SurrealDB-HTTP consumer, e.g. 65's export driver; the 5..7 bound is at its ceiling, stated in the comment); (2) FORK A3 ratified (harness creds; the prod env file is never read); (3) the `EnvironmentFile=` half dropped, ports check kept + renamed.
- Applied by a one-shot agent; **the lead VERIFIED in full** (non-audited): diff read, the seam set + script tests `177 passed`, self-test 13/13 (agent receipt), ruff clean. Committed. All 7 restore/driver seam reds from `80409f4`/`37de0a7` are now green.
- Surfaced: `ruff format --check` flags pre-existing wrapping in test_secret_typing.py L206–230 (not new).

### 2026-09-26 — contract-64b: rebased on 63c's build; red ownership via TYPE_CHECKING blocks (flag for adversary-64b)
- §HELD rebased onto `441f3b0`. The `principals.py` conflict was resolved onto 63c's machinery (its half-pair refusal routes through 63c's ONE refusal + id-sample helpers, not copies). Runner kills now take the whole process tree.
- **FLAG for adversary-64b's brief:** to own its pytest reds, 64b adds `if TYPE_CHECKING:` blocks naming the unbuilt symbols. This manufactures 15 owned typecheck errors (`packet-64b-i-contract` entry), because the gate cannot register a type-clean file (#461). The adversary must check (a) whether the pytest-leg reds actually render RED_ADJUDICATED under the full `--currency`, or only the typecheck leg; (b) whether this is honest ownership or gate-gaming; (c) whether #461's gap needs a real fix (a pytest-keyed adjudication) instead of a per-contract workaround.

### 2026-09-26 — 58 am-5 (`67bf2cc`, sidecar-64 Task 13): r2 FORK-2 — Reading A (builder constrained to fit the enumerator) REJECTED
- Ruled C+B: (C) RUNTIME injection ∀ derived shell callers is the ∀, with coverage checked both ways; (B) the static index re-keyed to the caught CLASS (bare/tuple excepts; re-read irrelevant), cross-checked with (C). Sidecar erratum on its am-4. The lead flagged A as the 7th instrument-lesson row (a reach keyed on code SHAPE); the ruling agrees.
- Relayed as a STOP directive #17065 + a wake (the wake misquoted it as #17066; the agent drains the thread; proof = its ack of #17065).

### 2026-09-26 — #466 ACCEPTED 20/20; single-lane rule LIFTED; #466 delta d1
- **refactor-466 (tdd-refactorer, opus):** R1–R5 behaviour-preserving, lead-VERIFIED (#466 set `72 passed`, skill `120 passed`, ruff clean), committed `e6e17d8`. **Acceptance: 20/20 concurrent-pair rounds (14/14 ×2 each; rounds 1–7 alongside a28's -n 8); 0 ServerStartupTimeout in 480 starts; startup p50 3.06 s / max 4.24 s vs the 15 s budget** → the measure-then-tune decision point is RESOLVED: keep 15 s. **Deletion reconciliation (lead):** #466's deleted symbols ⊆ the contract inventory (`_delayed_listen` moved, not deleted). #496 filed (lore_search store error).
- **Single-lane rule LIFTED** (directive #17068): concurrent lore pytest sessions allowed; a full suite capped at -n 12 while another lore suite is live (RAM); 15 GB watchdog with process-tree kill. MEMORY.md landmine updated.
- **#466 delta** (tdd-light routes contract/behaviour findings back to Phase 1): **contract-466-d1** pins F1 (BaseException cleanup), F2 (a silent shutdown-join overrun → loud), C1 (a `_CONTRACT_FILES` dead-entry pin), C2 (the uvloop premise), C3 (aiohttp listener namespace; consider deriving it), F12 (driver process-tree kill on timeout).
- contract-58-r2 told: its `test_reanchor_58_r2_rulings.py` trips the whole-tree-clone invariant.
- Next in the tdd-light queue after #466 closes: #486 (harness `run()` via the retry seam + the `test_<uuid>` DB leak), then #492 (admin-picked port + `--port`).

### 2026-09-26 — #466 delta contract d1 reviewed; lead rulings (a)–(e); stub urgent
- contract-466-d1: pins F1/F2/C1/C2/C3/F12 (insertions only; declared RED == observed; reference passes; 17/17 wrong builds caught). C1/C2 are mutation-proven (they cannot be RED today by nature).
- ⚠ The uncommitted delta makes test_loopback_serving.py a COLLECTION error (`ImportError: DEFAULT_SHUTDOWN_TIMEOUT_S`) in the shared tree until the F2 stub lands → stub spawned immediately; contract + stub commit back to back.
- **Lead rulings (right-sized, test-infra):**
  - (a) F2 = raise on a clean exit + a note on a failing exit (loud; never masks the test's own failure).
  - (b) KEEP the derived-reach C3b (allowlist-the-safe; +4.5–8 s accepted).
  - (c) pytest-asyncio `unused_tcp_port*` ruled IN (a bind-close door; pin its absence in the test trees).
  - (d) the `serve_http` stuck-handler teardown is bounded + loud NOW (F2's class).
  - (e) F2 budget = measure-then-tune: the implementer measures 20 real wire-lifespan teardowns; budget = max(5 s, 3 × p99).

### 2026-09-26 — #466 d1: contract `a9ed80e` + stubs `a124c5a` + GREEN `ef0fcda` (lead-verified); Phase 5 + pins c/d
- Stubs: RED 9/80, all behavioural, == declared; collection verified by the lead (80 collected).
- impl-466-d1 GREEN: lead-VERIFIED `94 passed`, no assertion edits, ruff clean. One `_loud_teardown` serves serve_asgi + serve_http (ruling d; mutation-proven by the implementer). **Ruling e measured: real wire teardown p99 0.197 s (n=24 serial + 24 concurrent) → the 5 s budget is kept.**
- Gap: rulings (c) `unused_tcp_port` and (d) the serve_http bound post-dated the contract, so there are no pins. **refactor-466-d1** does Phase 5 AND authors both pins, each mutation-proven RED (a documented test-after deviation).
- impl-466-d1 extras: it fixed a driver bug (Py 3.14 `TimeoutExpired.stdout` is bytes, so the timeout tail was always empty). #499 filed. **Process caveat:** a "withheld" report appendix was reachable via lore_search (lore indexes REPORT-*.md). The implementer saw Appendix-B lines after its own fix; its version differs. Lesson: withholding an artifact from an agent does not hold while lore indexes it (keep withheld references out of the tree, e.g. in the scratchpad).
- Added to refactor-466-d1: a `serve_http(shutdown_timeout_s=)` param for pin (d), and `expected_passed()` routed through the same process-group kill (the F12 class).

### 2026-09-26 — #466 d1 Phase 5 committed (`8d42c27`); RIGHT-SIZED close via close-466
- refactor-466-d1: pins c (a DERIVED plugin-fixture allowlist; any unclassified plugin fixture is refused — lead CONFIRMED over a name-keyed deny-list) + d (serve_http loud teardown via the shared `_loud_teardown`), 9/9 mutations held; lead-VERIFIED `110 passed`, no removed assertions, ruff clean. #500 filed.
- Its R1 (MEDIUM): the teardown join leaks the capture handler on a BaseException (F1's class, other side). My add-ons arrived after it finished (the serve_http param; `expected_passed()` group-kill).
- **Right-size (operator memory "right-size rigor to importance"):** #466 is test infra, and each audit round has found a smaller tail. The lead ENDS the contract→audit→delta loop here: **close-466** does R1 + the serve_http param + `expected_passed` group-kill + the T1–T4 smells in ONE test-first pass, then a final 20-round acceptance. The lead verifies directly; no further audit round. After that, #466 closes and #486 starts.

### 2026-09-26 — contract-63c-i-a-a28 COMMITTED (`d334042`); narrow adversary spawned
- RED@`169925f` 45 (right-reason); SAT: ref 207F vs baseline 252F, 0 ref-only, all 45 a28 reds green on the reference, 0 63c-attributable; 18/18 wrong builds killed (one exposed a one-direction am-30 pin → reverse check added); 8-way race strands 4/20 and 6/20 rounds on the checkpoint, 20 greens on the reference; a28 currency orphans 0 (the 6 orphans are 58-r2's untracked cas_runtime file); Reading B (am-30) applied. Attribution-clean. Found: `count() … GROUP ALL` over no rows returns `[{'count': 0}]` on 3.2.4, so `_scope_count`'s docstring is stale (builder item).
- **adversary-63c-i-a-a28 (NARROW, per am-28 §Process)** spawned on the F-1/F-2/RS-5 pins + DUAL deletions, starting from the author's §13 list.
- FK-a28-3/-4 (non-blocking; pins agnostic) → sidecar-63c-2 **Task 31**.
- Stale refactor-466-d1 idle (its decisions were already handled: close-466 covers R1 + the serve_http param; c confirmed).
- **Am-31 (FK-a28-3/-4):** two typed fields (`distinct_owner_principals`, `owner_classification` enum); a verb-level `--table message` refusal OMITS the unmeasured message counts. Relayed to adversary-63c-i-a-a28 as directive #17070 (the wake misquoted it as #17071; lead habit fix: send the wake only AFTER reading the directive's returned seq, never in the same batch). The contract's "exactly six fields" pin now conflicts → the post-adversary contract fold.

### 2026-09-26 — contract-58-r2 COMMITTED (`c42eeaf`); adversary-58-r2 spawned; sequencing ruled
- r2: MP1–MP18 + SD1–SD3 + am-2..5 landed; 24/25 adversary probes AST-EQUAL (PR18 re-keyed per the am-3 erratum); 49 wrong builds, 0 survive; SAT on plain HEAD + §HELD + reference `2 failed, 11859 passed` (both a ruling-vs-pin conflict, resolved by §HELD part 3); `--currency` PASS. Reading A fully undone before the commit. The lead checked its `pending_contracts.yaml` hunk: ONLY the packet-58 entry changed. Attribution-clean. #494 and #497 (RETURN inside a txn → store ref) filed.
- **Sequencing (F-r2-2), lead-ruled:** 58's §HELD `test_retry_seam` re-key lands FIRST (58 builds before 64, pool 30); 64b re-derives G2 on top via a patch script → directive #17072 (the wake quoted the correct seq).
- FORK-3 (ERROR vs WARNING for an ASSERT rollback; does am-3 §3's WARNING reach 63's governed-conflict THROW) + FORK-4 (`[A,A,X]` dedupe) → **sidecar-64 Task 14** (58 am-6).
- **adversary-58-r2** (delta) spawned: prior-survivor kills, new wrong builds vs (C)/(B)/the packer, the AST receipt re-run, SAT on plain HEAD + §HELD + its own reference.
- r2 detail: when 64b merges its two findings functions, 58's runtime-injection test's two findings entries go stale → they fail LOUDLY by name at 64b's integration (the builder re-keys them). Logged, not directive-stacked. #497 (a RETURN inside a txn ends it early + commits) → sidecar-64 **Task 15** (store-ref entry).
- **58 am-6 (`dcf6b0f`, Task 14):** FORK-3 = ONE prefix-marker tier table in `_txn` (claim_lost DEBUG; governed_conflict/cas_lost/reanchor_straggler/heal_chunk WARNING, reaching 63's governed conflict; engine refusals/contention-exhausted/unrecognised ERROR); FORK-4 = whole-column distinct `[A,A,X]`→`[A,X']`, E11 changed-deliberately. → directive #17074 to adversary-58-r2 (wake sent AFTER the seq returned). Attribution-clean.

## RESUME ANCHOR v5 (2026-09-26 ~16:05 EDT — compaction point) — supersedes v4
Lead `lead-63c-2`, session `63c-20260924`, branch `feat/surreal-unification`. Sidecars: **sidecar-63c-2** (63c rulings) and **sidecar-64** (64 + 58 rulings; Task 15 queued = #497 into the store ref). Directives = a `lore_comms` directive (thread `63c`) + a native wake SENT AFTER the directive's seq returns (habit fix). Rulings/forks → sidecars; only MAJOR scope/architecture → the operator.

**Standing operator rulings this session:** F0 (design + contract ahead of 63c; builds serial) · pool 30 = 58 before 64 · OF-1 project keep · OF-2 retire the identity args at 65 · OF-3 required `--delete-obj|--archive-obj|--change-owner` (keeps: `--change-scope`, 64 am-5) · OF-4 accept the number bound · #492 port admin/agent-picked in lore.yaml + a `--port` CLI · the #466 fix → **single-lane pytest rule LIFTED** (concurrent lore sessions OK; full suite `-n 12` while another is live; 15 GB watchdog, process-TREE kill) · (a) STOP-close accepted · (b) CLAUDE.md 7th instrument row (done `6a09954`) · (c) #486 → tdd-light · (e) fast pytest · test-DB cleanup done (1873 + 36 dropped; the `test_<uuid>` leak → the #486 cycle).

**IN FLIGHT (they message on done):**
- **63c-i-a:** checkpoint `169925f` (fix-wave build, cold audit NO-GO, `REPORT-coldaudit-63c-i-a-2.md`). Fix-pass contract **a28 `d334042`** (am-27/28/29/30). **adversary-63c-i-a-a28** grading (NARROW; also told of am-31 `4a8ea02` → the "exactly six fields" pin conflicts). NEXT: a contract fold (am-31 + adversary missing pins) → a builder fix (fresh name) → the cold-audit re-run + a contract-blind reader → commit on GO → INDEX "63c-i-a CLOSED". Then 63c-i-b (carry: C-3, #467, #487 reverse #420 pin, F-2/CA-3, am-27 DV-2 helper extraction if still relevant, RS-6, the `_scope_count` docstring, N-2) → 63c-ii → security-auditor.
- **58:** contract r2 **`c42eeaf`** (0/49 survive). **adversary-58-r2** grading (told of am-6 `dcf6b0f`). NEXT: a fold of any missing pins → the 58 build AFTER the 63c-i-a commit (§HELD incl. the test_retry_seam re-key lands FIRST, before 64b's G2; esc1 script fix is a builder item).
- **64b-i:** **contract-64b** finishing receipts, then ONE commit (§HELD 24 files, patch scripts for the a19 + test_retry_seam files). NEXT: **adversary-64b** — its brief MUST include the flag: the TYPE_CHECKING red-ownership trick (#461); prove the pytest-leg reds render RED_ADJUDICATED. Build after 63c.
- **#466 (tdd-light):** contract `37de0a7` · stubs `fe45d1a` · GREEN `6566ba6` · refactor `e6e17d8` (acceptance 20/20; 15 s timeout kept) · delta d1 `a9ed80e`/`a124c5a`/`ef0fcda` (teardown p99 0.197 s → 5 s kept) · Phase 5 + pins c/d `8d42c27`. **close-466** doing the final right-sized pass (R1 teardown handler leak, `serve_http(shutdown_timeout_s=)`, `expected_passed` group-kill, T1–T4 smells, a final 20-round acceptance). The lead verifies + commits → #466 CLOSED.
- **tdd-light queue after #466:** **#486** (route `_surreal_harness.run()` through `_run_under_store_retry_seam` + a raw opt-out; the 4 conflict-marker files; + the `test_<uuid>` DB leak: trace the minting site, route it through `unique_database()`, add a guard, reap) → **#492** (admin-picked port: `setup` requires an explicit port / `--port`, lore.yaml is the source of truth, delete `_free_port`, publish-address pre-check, SKILL.md, remove the #466 guard exemption).

**OPERATOR-PENDING:** coldaudit FOCUS 5 — the real 08-03 prod-dump restore into :18000 was permission-DENIED ("Modify Shared Resources"). Options: (1) an allow rule for `uv run python scripts/restore_prod_dump.py *` (only on operator instruction), (2) the operator runs it via `!`, (3) skip this round. The staged commands are in `REPORT-coldaudit-63c-i-a-2.md` §5.

**Lessons logged this session:** a contract-ahead commit must own every pytest red (currency F-6) · committed scripts need the repo-wide invariant tests, not just their own · kill the process TREE · withheld artifacts leak via lore_search (keep them out of the tree) · quote a directive seq only after it returns · right-size: end audit→delta loops when tails shrink (close-466).
- (post-anchor) sidecar-64 **Task 15 DONE:** #497 (a RETURN inside a txn ends it early + commits the earlier statements) landed in the store ref (`cbc9fe0`, §3 bullet + a §6.2 silence row; re-probed with LET/THROW controls); #497 resolved. **#501 filed:** `compose` should refuse a top-level RETURN fragment; owner = the 58 builder (add to 58's BUILDER CONSTRAINTS at the 58 build). sidecar-64 has no queued tasks.

### 2026-09-26 — #466 closing pass committed (b94a627); #466 HELD OPEN on #503
- close-466 delivered: R1 fix (teardown detach in `finally`, RED 4/4 → GREEN), one process-group runner with a class AST pin, T1–T4, serve_http budget threading proven by mutation, acceptance 20/20.
- **Lead verification (no cold audit, so a full re-verify):** read the diff; ruff clean; `typecheck.sh` 0 errors in the 5 touched files (the 44+1 elsewhere are other packets' uncommitted contract-ahead files); the brief set re-run gave **2 failed / 112 passed / 10 errors**. Every red was `ServerStartupTimeout … 15.0s` in `test_migration_wire.py` (untouched by the pass), under 5 concurrent lore suites plus mypy at load 77. The file alone gave **14 passed in 124 s**. The loopback, guard and driver files were green in both runs.
- Committed 5 files + `REPORT-close-466.md`. contract-64b's `pending_contracts.yaml` ownership hunk was left UNSTAGED; it is theirs.
- **#503 filed:** the lane lift's rated concurrency is unstated. "-n 12 with another suite live" caps workers, not sessions. Needs measure-then-rule: the migration_wire start distribution at 1/2/5 sessions, then a per-caller budget and/or a fleet cap. Measurement waits for the adversaries' SAT runs to finish, so it doesn't contaminate them. Signal #17076 tells in-flight graders how to adjudicate that shape.
- Open from close-466, still to rule: (a) a generated interrupt-injection sweep over loopback's blocking waits vs a ledgered bound (rec: ledger; trigger = a 4th blocking wait or a 2nd kind of process-global state); refactor R4 (a raising `stop()` in the failing branch replaces the body's exception) and R6 (the aiohttp deny-list misses `SockSite`/`AppRunner`) are still open. At #466 close: archive the 8 #466 reports into `docs/plans/v2/receipts/2026-09-26-466/` and repoint the 3 in-code `REPORT-*466*` cites; add a superseded note to `REPORT-refactor-466-d1.md` §Pins-d.
- Lead self-error: a `pgrep -f` kill of the currency gate matched my own shell (#228 class); the gate tree is confirmed dead. The currency gate spawns `-n auto` internally, which breaks the `-n 12` cap when the fleet is busy. That is noted for #503.

### 2026-09-26 — operator rulings on close-466's leftovers; measure-503 spawned
- Operator: "Yes to your recommendations".
  - (a) interrupt-sweep → LEDGERED as finding **#504** (bound; re-open = a 4th blocking wait or a 2nd kind of process-global state).
  - **R4 → FIX NOW**, one tdd-light cycle together with the #503 budget fix (the property: a failing body's exception is never REPLACED by any teardown failure; the `stop()` raise becomes a note).
  - R6 → KNOWN BOUND, finding **#505** (re-open = the first test-tree import of aiohttp, mechanised by the derived reach).
- **measure-503** (opus55-worker) spawned: brief `scratchpad/brief-measure-503.md`. It measures migration_wire start latency at 1/2/5 single-process copies (ceiling = 5; no full suite), a phase breakdown, and a DERIVED budget recommendation, and answers whether `--currency` spawns at `-n auto`. Next: its report → rule the budget → tdd-light #503 + R4 → #466 CLOSED (archive the 8 reports, repoint cites) → tdd-light #486 → #492.
- Box memory at 20:4x: MemAvailable **11.5 GB of 125.7** (below the 15 GB watchdog floor). The holder is an Odoo test DB restore (`ppt-apps15-test-a36b`, another project). contract-64b's mutation chain (M5–M22) is gated on 32 GB free. Surfaced to the operator.

### 2026-09-26 — a28 adversary: INSUFFICIENT (4441b9d) → sidecar #17081; measure-503 committed (388c604)
- adversary-63c-i-a-a28: **11/18 wrong builds pass the contract; 6 pass the full suite** (union W2+W3c+W19+W7+W15b+W18 = a red set identical to the reference). MP-1 HIGH (W19: a gate keyed on "the caller sees no keep" re-opens F-2; every a28 foreign probe principal was keepless) · MP-2/3 MEDIUM (RS-5 catch-all recursion W7; text-keyed / transport-swallowing classifiers; a second re-register copy) · MP-4/5 LOW (the spy's 3-method hand-list; compensation on another refusal class). Three CLASSES C1/C2/C3; K9 is already generated. Forks: FK-ADV-1 (a typed `AlreadyExistsError` in the ONE driver vs a broad catch plus re-read), FK-ADV-2 (am-31 vs am-30, the message-leg agent fields). SAT: 0 reference-only reds, the same 45 fixed.
- **Second strike on F-2's property** (a foreign principal learns nothing) → routed as the PROPERTY C2 with a derived spy reach, not as instance W19. Sidecar directive **#17081** (am-32) plus a native wake. Next: am-32 → contract fold a28b (fresh author: am-31 + MP-1..5 by class + rulings) → narrow adversary delta (mandatory) → builder fix over 169925f → cold audit plus a blind reader.
- **Loop cost (the 2026-09-26 rule):** a28's contract↔adversary loop is at 1 round. Packet 63c-i-a overall: contract a19/a19a/a19b → build → cold audit NO-GO → a28 → this INSUFFICIENT.
- DV-5 (watchdog reading): the adversary ran its full suites under a per-tree 15 GB RSS kill plus a 4 GB host floor, because foreign tenants held the host at 11–27 GB free and the MemAvailable<15 GB reading SIGTERMed its baseline. That is an operator question: what does "15 GB PID watchdog" mean?

### 2026-09-26 — am-32 ruled (51fd508); operator rulings; a28b + tdd-light #503 spawned
- sidecar-63c-2 am-32: FK-ADV-1 = B (typed `TxnRecordExistsError` in `_txn.py`, both raise sites; RS-5 + keeps catch the class, R-6), FK-ADV-2 = A (`None` iff the read was gated off; am-31 erratum), C1–C3 with the K-probes AST-equal, the am-31 fold by annotation, R-1..R-6. The sidecar's own lore client is ECONNREFUSED (native works); the lead's lore is healthy.
- **Operator (AskUserQuestion):** #503 "All 4 recs"; watchdog "Memory pressure has been fixed" (the MemAvailable<15 GB reading stands); the am-32 typed driver error ALLOWED; both am-32 widenings KEPT.
- Spawned **contract-63c-i-a-a28b** (brief `scratchpad/brief-contract-63c-i-a-a28b.md`) → then the mandatory narrow adversary delta.
- Spawned **contract-503** (tdd-light Phase 1; Phase 0 = `scratchpad/phase0-503.md`: a per-caller 60 s budget, R4's never-replace-the-body-exception class over both helpers, and a currency-gate worker policy reusing `other_pytest_sessions`).

### 2026-09-26 — tdd-light #503 cycle status; the 58↔63c scanner-key collision → sidecar-64 Task 16
- #503 cycle: contract (46 pins) → stub → RED (lead: 30F/196P, sum 226) → GREEN 226/0 → audit (0 behaviour defects; routed §1a forwarded -n, §1b own-pid, F8) → delta contract d1 (+50; lead rulings D1-F1=B, D1-F2 refuse-before-spawn, D1-F3 typed error; helper keep_with_trigger) → GREEN 276/0 → re-audit d1 (the survivor killed; §1a refused; a false served claim about --maxprocesses fixed) → **STOP-rule close** (3 rounds on one surface, each sibling one level deeper): contract-503-d2 adds the D-2 rider pin (never "MANIFEST ERROR") plus pin-the-miss for D-1 and --maxprocesses; the remaining bounds are ledgered as **#508**. The green build's content is backed up at `scratchpad/backup-503-green/`.
- **Cross-packet collision** (contract-63c-i-a-a28b F-2, #17085): 63c am-32 §1.3(f) vs 58 am-5 §2(B) both re-key `test_retry_seam._discover_guarded_cas_handlers`. Proposed merge = 58's hierarchy key, with the 63c doors moved to `_TYPED_CAS_CATCHES`; the derived key also found an unlisted door `floor_calibration/store.py::record_measurement`. F-1: under 58 am-6 a keeps lost race (engine identity-taken) logs at ERROR. → **sidecar-64 Task 16** (native; asked for 58 am-7, cited by both packets). sidecar-63c-2 checks the ruling against am-32/33.
- Findings filed: #506 (the detector matches argv text), #507 (scripts/ not in lore's graph, by refactor-503), #508 (the #503 worker-policy bounds).

### 2026-09-26 — #503 COMMITTED (f21a885) + CLAUDE.md (e53b837); 58 r2 INSUFFICIENT (821be62) → sidecar-64 Task 17
- #503: lead verification — 8-file gate 305/0, skills 120, ruff clean, typecheck 0 in the touched files, the diff read (R4 catches Exception only; one worker-flag recogniser; the policy -n rendered last). CLAUDE.md gains the fleet cap line; its only reader, test_gate_currency, passes 21/21. A wider run over the CLAUDE.md-mentioning files: 92 reds, all in-flight contract-ahead (58: 61, owned; test_mcp_server 28, 64b uncommitted; test_retry_seam 3, a28b uncommitted). archive-466 is archiving the 17 #466/#503 reports and repointing cites.
- **adversary-58-r2: r2 INSUFFICIENT** — prior survivors all killed; SAT 0 attributable (45 = 63c-i-a owned). New: N3/F1 HIGH (a per-row-priced heal packer: every boot fails at ≥1250 two-blocker stragglers) = the **THIRD strike on the heal-chunk property** → routed as a PROPERTY with a generated sweep. P-PKG: `more_itertools.constrained_batches` IS the packer → **lead ruling: use it, declare more-itertools a direct dependency** (am-3's "no library" is an erratum). F2/F3/F4/F10/F11 missing pins; F5/F8 correct builds rejected (scanner literalism) vs N20 (helper escape) → reach question; F6–F8 covered by am-7. → **sidecar-64 Task 17** (58 am-8).
- **Loop cost:** 58 contract↔adversary is at round 3 (r1 → r2 → r3 next). 63c-i-a a28 at round 1 (a28b folding).

### 2026-09-26 — #466 + #503 RESOLVED; 64b contract committed (d8ea4ba) → adversary-64b; 58 am-8 (03cb6d0) → contract-58-r3; 64b forks → sidecar-64 Task 18
- archive-466: 17 reports → `docs/plans/v2/receipts/2026-09-26-466-503/`, 31 cites repointed (15b844b + 162450b). Lead-verified: 0 bare cites outside the archive and the lead log; the 6 edited test files 249 passed + test_gate_currency 21; ruff clean; the 13 "close-466 R1" prose mentions are agent NAMES, not addresses → left (the archive law). Findings **#466, #503 RESOLVED**.
- contract-64b DONE: d8ea4ba (RED@HEAD 119, all owned; --currency PASS; 19/19 mutations; §HELD 4 parts / 24 files). Forks FK-1..9 → **sidecar-64 Task 18** (FK-7 spec-silent: the server-side calibration drift writer has no Subject). **adversary-64b** spawned (brief `scratchpad/brief-adversary-64b.md`; attacks the TYPE_CHECKING-ownership shape FIRST).
- sidecar-64 **58 am-8** (03cb6d0): constrained_batches ratified; CONVERGENCE property with a generated shape sweep; F5/F8/N20 → driver-seam fault injection with call-graph-derived coverage (not a receding reach); F3 any logger; F4 skip the whole row; esc1 → the builder. A 4th instance re-opens the RULING. **contract-58-r3** spawned (brief `scratchpad/brief-contract-58-r3.md`).
- In flight: contract-63c-i-a-a28b (am-32/33 + 58 am-7), adversary-64b, contract-58-r3, sidecar-64 Task 18. Next lead-side: tdd-light #486, then #492.

### 2026-09-27 — a28b committed (e039c64) → adversary-63c-i-a-a28b; 64b INSUFFICIENT (0f69efa); rulings routed
- **contract-63c-i-a-a28b DONE** e039c64: RED@169925f 106; 20/20 mutations killed; RS-2/RS-5 20× consecutive; SAT 0 reference-only / 63c-attributable 0; currency orphans 0 (the a28 entry updated). Forks FK-a28b-2/3/4, F-5, and the owner of am-7's one-scanner-function pin → **sidecar-63c-2 Task 35**. #509 filed (mutation_proof.py does not restore on kill). **adversary-63c-i-a-a28b** spawned (narrow delta; brief `scratchpad/brief-adversary-63c-i-a-a28b.md`; #509 content-backup landmine included).
- **adversary-64b: 64b-i contract INSUFFICIENT** (0f69efa): 10 wrong builds + the reference survive (9 combined pass the full suite node-identical); 4 SAT defects on HEAD+§HELD (a stale base e6e17d8 → collisions with the 58-r2/63c-a28 contracts); the FK-9 TYPE_CHECKING blocks certify names, not signatures. 3 rulings needed (double agent-row read vs am-7's "one"; admin set_scope accepts any string; authorize-before-edge-validation) → **sidecar-64 Task 19 part A** (64 am-8). sidecar-64 **64 am-7** (6e42ed1) had ruled FK-1..8 (FK-7 → `report_system` + a `calibration-drift` exempt; FK-1 → `subject=` everywhere, title renamed at the seam); finding #510 (a memory existence oracle by text hash).
- contract-58-r3: 6 forks → **sidecar-64 Task 19 part B** (coordinate FK-r3-1 with 63c-2's FK-a28b-4 ruling). Continues on its picks.
- **Loop costs:** 63c-i-a contract round 2 (a28 → a28b); 58 round 3; 64b-i round 1 → r2.

### 2026-09-27 — 63c am-34 (178d236) ruled a28b's forks; operator: F-5 FIX NOW
- sidecar-63c-2 am-34: FK-a28b-4 = TWO exact sets NOW in 63c-i-a (supersedes 58 am-7's "one set first"; 58's §HELD delta shrinks to the claim_task entry + the union completeness pin + the runtime↔static cross-check + the tier re-key) → relayed to contract-58-r3 (#17094 + native). FK-a28b-2 = a fifth member "empty" + a model validator; FK-a28b-3 = total_principals/admin_principals become fields; the one-scanner pin is owned by 63c-i-a.
- **Operator (AskUserQuestion): F-5 "Fix now in 63c-i-a"** (defined_tables / table_defined + a one-read pin), as am-34 ruled.
- adversary-63c-i-a-a28b told (#17095) to list am-34 as §AM34 fold items, not to grade them. Next: its verdict → ONE fold a28c (am-34 + its missing pins) → a narrow adversary delta → the builder fix over 169925f.

## RESUME ANCHOR v6 (2026-09-27, lead-63c-2, session 63c-20260924) — AUTHORITATIVE; supersedes v5
**CLOSED this span:** #466 (b94a627, acceptance 20/20) · #503 + R4 (f21a885; per-caller 60 s budget; the currency gate renders `-n {workers}` last and refuses a forwarded -n) · CLAUDE.md fleet-cap line (e53b837) · reports archived at docs/plans/v2/receipts/2026-09-26-466-503/ (15b844b). Findings resolved: #466, #503. Bounds ledgered: #504 (loopback interrupt sweep), #505 (aiohttp deny-list), #506 (the detector matches argv text — design ruling needed if a false refusal blocks work), #508 (worker-policy bounds). Other new: #507 (scripts/ not in lore's graph), #509 (mutation_proof.py does not restore on kill — brief every mutation agent to cp -a + cmp), #510 (memory existence oracle by text hash).
**IN FLIGHT (all report by native micro-format):**
- **adversary-63c-i-a-a28b** — a narrow delta on contract a28b `e039c64` (brief `scratchpad/brief-adversary-63c-i-a-a28b.md`); told (#17095) to list am-34 as §AM34 fold items. NEXT: verdict → spawn ONE fold **contract-63c-i-a-a28c** = am-34 (178d236: two scanner sets now; the "empty" member + validator; total/admin_principals fields; the **F-5 FIX, operator-ruled**; the one-scanner pin owned by 63c-i-a) + its missing pins → a narrow adversary delta → the builder fix over checkpoint **169925f** → cold audit + contract-blind reader → commit on GO → INDEX "63c-i-a CLOSED" → 63c-i-b.
- **contract-58-r3** — folding 58 am-7 (01565f9) + am-8 (03cb6d0: `constrained_batches(strict=True)`, the convergence shape sweep, driver-seam CAS injection, F3 any logger, esc1 → the builder) + #17094 (am-34 shrinks its §HELD scanner delta). Brief `scratchpad/brief-contract-58-r3.md`. NEXT: commit → a narrow adversary delta. 58 is at contract round 3; a 4th instance of a routed property re-opens the RULING.
- **contract-486** — tdd-light Phase 1 (operator kept tdd-light despite the retries trigger). Phase 0 `scratchpad/phase0-486.md`: `_surreal_harness.run` routes through `_run_under_store_retry_seam` + an explicit raw door; the §Raw-door table (4 candidate files; test_retry_seam.py is owned by 63c, so its sites go in §HELD); the AST reach pin; the test-DB leak (every DB via `unique_database()` + reaped). NEXT: review forks → stub → lead RED run → implement → refactor(opus) → lead verify + commit. Then **tdd-light #492** (setup requires an explicit port / `--port`; lore.yaml is the source of truth; delete `_free_port`; a publish-address pre-check; SKILL.md; remove the #466 guard exemption).
- **sidecar-64 Task 19** (native only; its cross-session lore_comms fails): PART A = the 64b adversary rulings (a double agent-row read vs 64 am-7's "one"; admin set_scope accepts any string; authorize-before-edge-validation; the SAT base = post-63c/58 HEAD; FK-9 → a signature-checking form) → 64 am-8, then spawn **contract-64b-r2** (base: contract d8ea4ba + REPORT-adversary-64b.md 0f69efa + 64 am-7 6e42ed1 + am-8). PART B = the 58-r3 forks FK-r3-1..6 → 58 am-9 → relay to contract-58-r3.
- sidecar-63c-2: standing by (its lore client is ECONNREFUSED; use native only). sidecar-64: standing by after Task 19.
**Build order (pool 30):** 63c-i-a build → 58 build (§HELD incl. the scanner delta, #501, esc1, the more-itertools dependency) → 64b-i build. Every build serial.
**Loop costs to report at every INSUFFICIENT:** 63c-i-a contract round 2 (a28→a28b→a28c next); 58 round 3; 64b-i round 1 → r2.
**Standing:** the lead writes no code; verify in full any commit made without a cold audit; no attribution trailers; directives = lore_comms + a native wake after the seq returns (sidecar-64 and sidecar-63c-2 = native only); concurrent pytest OK (`-n 12` when another is live; the 15 GB host-MemAvailable watchdog stands, operator); never forward `-n` to the gates; end turns with the #486 line until #486 is fixed.

### post-anchor (v6) — sidecar-64 Task 19 delivered; contract-64b-r2 spawned
- **64 am-8** (53563e7): R8 = one agent read at the seam (am-7 erratum); admin set_scope = any ROW via a scope domain ∀ writers; authorize-before-edge; the r2 SAT base ruled; FK-9 → the typed-call form; survivor classes named. → **contract-64b-r2** SPAWNED (brief `scratchpad/brief-contract-64b-r2.md`). NEXT: its commit → a narrow adversary delta.
- **58 am-9** (4cb8ce9): all six r3 picks confirmed (claim_task unlisted — am-4/am-7 erratum; whole-tree swallow rule; F-r3-1 → r4; F-r3-3 → pytest-timeout); aligned with 63c am-34. → relayed to contract-58-r3 (#17098 + native).
- sidecar-64: standing by (Task 19 done).

### post-anchor (v6) — 58 am-10 (FK-r3-7) relayed; contract-486 done → stub; operator rulings D1–D4 + #512
- **58 am-10** (5b72471, sidecar-64 Task 20): property = exhausted contention is never a FALSE CLEAR; FATE classifier (PASSTHROUGH / TRANSLATE-to-FAULT_CLASSES-`from` derived; NAMED-ISOLATION registered, exact both ways); Reading (i); none of the 7 swallows a defect; cross-packet home `test_exhaustion_fates.py` landed by 58's build; am-9 §3 erratum. Relayed → contract-58-r3 (#17099 directive + native wake). Findings **#512** (17 `_ensure_connection` clones) · **#513** (indexer single failed-reason; pinned bound).
- **contract-486 DONE** (report uncommitted; content backup `scratchpad/backup-486-contract/`; test files sha256 6b150fbc… / c731fc98… match the report). tdd-light Phase 1 review PASS (☐s reasoned; pre-flight all covered/scoped; inventory adjudicated; spec-silent none). → **stub-486** spawned (tdd-stub; `_RUN_STATEMENT_LABEL`, `_MINTED_DATABASES`, `reap_minted_databases` only).
- **Rulings:** D1 (lead) — NO raw door (0/812 sites observe a raw conflict; allowlist-the-safe). **Operator:** D2 — killed-session orphans are handled by PERIODIC wipes of strays, "not a big deal": no cross-pid reaper, no pid-namespace token; #486 ships same-process session-end reap only, with the killed-session bound stated in the harness docstring. D3 — leave `scripts/` alone (no lint extension; 07a unchanged). D4 — AFTER #486 lands, an age-guarded (>24 h) drop of `test_*` DBs on the TEST store :18000 only, with counts before/after (this is also D2's periodic-wipe remedy). **#512** — queued as tdd-light AFTER #492.
- Fix queue: #486 (stub → lead RED → implement → refactor opus → lead verify + commit → D4 wipe) → #492 → #512.
- **58 contract r3 COMMITTED** 7130508 (trailer-clean; RED@HEAD 80; SAT 0 attributable; am-9/am-10/am-34 folded; `test_exhaustion_fates.py` green at HEAD, 74 sites, 8 pinned UNLOGGED holes). → **adversary-58-r3** spawned (brief `scratchpad/brief-adversary-58-r3.md`). Routing: FK-r3-4's 3 undriven rows (agents.register, keeps.get_or_create_keyed, record_measurement) → **63c a28c fold** (CAS_SEAM_DRIVERS); BC-r3-8 timeout number = lead, set in the 58 builder brief from the measured slowest test; am-10 §2 vs §4 (non-fault chained translate) → **sidecar-64 Task 21**.
- **#486 Phase 2 STUB** done (stub-486: 14 behavioral reds, structural 0, 80/80 pre-existing green). **Phase 3 RED (lead):** `pending_contract_gate.py --currency` at 7294b3f → pytest orphans = 14 in #486's two files (== the stub's 14) + 58 in 64b-r2's UNCOMMITTED WIP; typecheck/ruff orphans all 64b-r2 WIP; **58 = 0 orphans** (answers 58-r3's headroom request). PASS. ⚠ Lead slip: my watchdog wrapper set `S=` inside a backgrounded `&&` chain again, so the watchdog was blind this run; the gate's log was intact. Rule: assign variables in their own statement before `&`. → **implement-486** spawned (tdd-implementer, model opus per lore builder law; brief `scratchpad/brief-implement-486.md`; test_mcp_server §HELD waits on 64b-r2's commit).
- **Operator rulings (queue):** the 8 UNLOGGED holes incl. `watcher.read_events` (`return []` at DEBUG, a false clear) → ONE tdd-light AFTER #512. The test smells (38 `pytest.raises(Exception)` around `run`; 4 `_count` helpers turning store errors into 0) → a tdd-light AFTER the holes. **Fix queue: #486 → #492 → #512 → holes → test smells.**
- **58 am-11** (0ed6705, sidecar-64 Task 21): am-10 §2 governs. A translate is adjudicated by class ADMISSION to FAULT_CLASSES; `raises-chained` retired; only unchained raises register (with a reason). Inverts 5 r3 pins → relayed to **adversary-58-r3** mid-grade (#17103 + wake) as §AM11 items for r4.
- **64 am-9** (743373e, sidecar-64 Task 22): FK-r2-1..8 ruled (identity budget keyed by table; scope ASSERT withdrawn, 63a §4.1 stands; UNOWNED-LEGACY keyed on the SET clause; golden = composed txn text, A5 rejected; new `packet-64b-i-closeout` bound for the alias pin). → contract-64b-r2 (#17105 + wake). **Operator FK-r2-8: DELETE `scripts/c3_harness_repair.py`** in 64b §HELD with a DUAL row citing the archived copy → #17106 + wake.
- **adversary-63c-i-a-a28b: INSUFFICIENT** (52c7522). 5 wrong builds pass all 924 (B1, B13, S7/S8, B15) + MP-3 (ruling-level); predecessor 10/10 KILLED; SAT confirmed independently (63c-attributable 0). **THIRD strikes:** F-2's gate (→ am-32 §4 C2) and the RS-5 classifier (→ am-33 §(a); P-PKG: type R-txn via `surrealdb.errors.parse_query_error`). Per fix-the-class rule 5, the RULINGS re-open → **sidecar-63c-2** tasked (native): am-35, with the STOP-rule question put explicitly. The a28c fold waits on am-35 (and still carries am-34 + F-5 + FK-r3-4's 3 CAS drivers). **Loop cost: 63c-i-a contract = 13 revisions** (r1…a28b); this round ≈ 2 h adversary wall-clock + 37 contract runs + 2 full suites. #514 (staged-index sweep hazard): 0 staged at cb2357b.

### OPERATOR DIRECTIVE (2026-09-27) — WIND DOWN TO A CLEAN STOP, then pause for a restart
"Once each segment you're currently working on closes out, including audits and follow-up rounds, don't start a next segment." Segments in flight and their close-out point (NOTHING new starts after each):
1. **#486 (tdd-light):** implement-486 → refactor+audit (opus) → lead verify + commit → the D4 age-guarded wipe of the test store (ruled part of #486). STOP. Do NOT start #492 / #512 / holes / test smells.
2. **63c-i-a contract loop:** am-35 (sidecar-63c-2) → the a28c fold → its adversary delta → further rounds until SUFFICIENT (or the operator accepts pinned bounds). STOP before the 63c-i-a BUILD.
3. **58 contract loop:** adversary-58-r3 → r4 fold (am-11 + findings) → adversary delta → until SUFFICIENT. STOP before the 58 build.
4. **64b-i contract loop:** contract-64b-r2 (+ sidecar-64 Task 23: FK-r2-10/11) → adversary delta → until SUFFICIENT. STOP before the 64b-i build.
At the stop: archive the root REPORT-*.md, write RESUME ANCHOR v7, INDEX Log line, stand the sidecars down.
- **63c am-35** (d463dba, sidecar-63c-2): the third strikes re-ruled. STOP-rule applied: neither property is receding (C2's domain is finite: the relation-set powerset × mint orders; RS-5 was under-specified and is now fully specified, typed on both paths via `parse_query_error`). **a28c is the LAST contract round for both, by rule; a 4th strike → a pinned bound.** Scanner keyed per handler, the F-4 scope restored (D6). → **contract-63c-i-a-a28c** SPAWNED (brief `scratchpad/brief-contract-63c-i-a-a28c.md`; carries am-34 incl. F-5, am-35 §W, MP-1/2/4/5, and FK-r3-4's 3 CAS_SEAM_DRIVERS; collisions: 58 §HELD part 2, 64b-r2, the #486 WIP). Owed by sidecar-63c-2: the FK-r2-2 F5 universal-leg concurrence (pinged).

### OPERATOR DIRECTIVE — CORRECTED (2026-09-27; SUPERSEDES the wind-down table above)
"No, I mean finish out completely #486, 63c-i-a, 58 and 64b-i. Don't start anything past those." Each finishes FULLY, then STOP:
1. **#486:** implement → refactor+audit (opus) → lead verify + commit → the D4 age-guarded wipe.
2. **63c-i-a:** a28c (last round) → adversary delta → builder fix over 169925f → cold audit + contract-blind reader → commit on GO → INDEX "63c-i-a CLOSED". Do NOT start 63c-i-b.
3. **58:** r3 adversary → r4 fold → adversary delta → build (§HELD incl. the scanner delta, esc1, the more-itertools + pytest-timeout deps, BC-r3-8's timeout value) → cold audit → commit.
4. **64b-i:** r2 → adversary delta → build → cold audit → commit. Do NOT start 64b-ii / 64a / 64c.
Build order stays serial: 63c-i-a → 58 → 64b-i. NOT started: #492, #512, the holes, the test smells, 63c-i-b, 64a, 64b-ii, 64c, 65. At the stop: archive reports, RESUME ANCHOR v7, INDEX Log line, sidecars stood down.
- **64 am-10** (46340ef, sidecar-64 Task 23): FK-r2-10 NO closeout bound. **BINDING ON THE 64b-i BUILD BRIEF: the alias rewrite is a sequenced close-out step inside the build wave (builder commit → close-out commit → currency → cold audit).** FK-r2-11: the disposition comes from the SET clause alone; LEGACY_MAPPINGS materialisation filed as #515 → sidecar-63c-2 (not in the 4 segments unless it becomes a 63c-i-a fork). Relayed → contract-64b-r2 (directive + wake). sidecar-63c-2: confidence MEDIUM on the governed-marker anchoring (engine THROW wrapping unmeasured) → **rider for the 63c-i-a builder: a live read of the THROW wrapping.** Still owed: the FK-r2-2 concurrence.
- **FK-r2-2 concurrence** (63c am-35 §6 @ a68f652, sidecar-63c-2): the universal scope-in-DOMAIN leg is an F5 L2b leg over `effect.row_deltas[*].after`, ∀ governed tables; the 64-side wrapper is REFUSED (copy #2). 4 riders (effect-only; DOMAIN = shape predicate + existence read inside the observer lock; None not the leg's, no allowlist; both-direction controls incl. a missing keep; 63c populations first). → contract-64b-r2 (#17110 + wake).
- **#486 GREEN** (implement-486, report uncommitted): green outside HELD, 0 new reds. Rulings: D-a (store unreachable at session end → loud INTERNALERROR) ACCEPTED as built; D-b bounds ACCEPTED (stated in docstring); HELD hunks 1+3 (a consumer-side drain of test_comms_wiring's list) REJECTED → a PRODUCER-side fix in `test_comms_wiring._open_context` (fix-the-class); HELD hunk 2 (the one-line `_slug` → `unique_database()`, behaviour-neutral at HEAD) RE-ROUTED into contract-64b-r2's commit (#17112 + wake). implement-486 at rest until 64b-r2 commits → final full suite → Phase 5 refactor (opus).
- **HAZARD:** #486's WIP in the main tree poisons scratch copies (~628 provenance errors in test_mcp_server). Directive #17113 to adversary-58-r3 + contract-63c-i-a-a28c (and #17112 to 64b-r2): reset copies to HEAD content, re-adjudicate. Annotated on **#514** (the class: scratch_copy asserts the tree's identity, not that it equals HEAD).
- **63c am-36** (547f63d, sidecar-63c-2): FK-a28c-1 (an echoed "can be retried" / cascade phrase steers the retry decision; 2 s retries then TxnContentionExhaustedError) = the SAME class as MP-3 on the two upstream text readers → ruled INTO a28c as am-35 §2's completion (typed TransactionConflict/NotExecuted, one parse, text markers deleted, an exact-set pin over `_txn`'s text readers). **Overrides the letter of am-35 §0**, flagged §E (bound alternative = pin-the-miss; the 2 s misclassification ships). Lead: agree (honest-agent surface, typed fix measured, finite domain, no added round). Operator may pull before a28c commits. FK-2..8 ruled. → a28c (#17117 + wake). FK-6 → a one-line 58-r3 change for 58-r4.

## RESUME ANCHOR v7 (2026-09-29, lead-63c-2, session 63c-20260924) — AUTHORITATIVE; supersedes v6 and every post-anchor entry
**OPERATOR, latest:** "add the cap rule. Then we compact. Then you may resume the ONE packet that the contract was in flight for and finish it." The other segments stay PAUSED until the operator says. (The operator's earlier "finish #486, 63c-i-a, 58, 64b-i completely" is NARROWED by this to one packet.)
**NEW TEST POLICY (CLAUDE.md §Quality gates "TEST SCOPE", 402ec29 + 122778d) — binding on every brief:**
- targeted scope per run (changed tests + `lore_impact` covering tests + the AST pin files), `-n 8` max;
- the FULL suite once per packet (the cold audit, `-n 12`), one fleet-wide at a time; never `-n auto`;
- the currency gate at packet close-out only;
- a pytest tree >16 GiB is a defect;
- every agent pytest run under `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`, and mutation/reference runs add `pytest-timeout`;
- the test store is not a landfill.
Global tdd / tdd-light / tdd-implementer now defer to the project's test scope. Operator correction in lore memory (4ff30183): memory pressure is OURS, never ZFS ARC.
**MEASURED (2026-09-29):**
- **The 69.5 GB process:** OOM-killed at 2026-09-27 05:37Z, ONE python process, from an agent shell, unreported.
- **The profile:** a MemoryMax-capped memray profile of all 31 new contract files at HEAD peaked at 0.61 GiB each (`scratchpad/memprof/summary.tsv`), so the runaway was a looping wrong or reference build.
- **The collection floor:** 674 MiB per process (13,062 tests).
- **The stores:** spike-surreal RESTARTED by the lead (it was stopped and wiped by the operator; 31 MB on disk), now 1.28 GiB. Prod lore-surreal is 5.86 GiB flat (block cache 4.5 GB + write buffers up to 26×128 MB).
- **The sampler:** a 24 h prod RSS sampler runs in the background → `scratchpad/prod_surreal_rss.tsv`. The operator saw >20 GiB; not reproduced yet.
- **Orphaned containers:** 13 `github-mcp-server` stdio containers, one per Claude session. Not a memory cause.
**SEGMENT STATE:**
- **#486 (tdd-light):**
  - contract / stub / RED / GREEN done, UNCOMMITTED in the main tree (_surreal_harness.py, conftest.py, ~25 test files incl. `test_comms_wiring._open_context`, now self-reaping). The `_slug` line landed via 64b-r2's cb220ee.
  - NEXT: Phase 5 refactor+audit (opus, targeted scope) → lead verify (targeted) + commit → the D4 age-guarded wipe.
  - ⚠ Until it is committed, its WIP poisons scratch copies (#514; `git reset --hard HEAD && git clean -fd` in copies).
- **63c-i-a:**
  - contract **a28c COMMITTED 7017b54** (the LAST round by am-35/am-36 rule; a further instance = a pinned bound).
  - 4 open decisions in its SUMMARY: FK-a28c-9 (Validation-kind text), F-15, F-11 (a pre-existing txn parse error → connection error), and the 58-r4 items.
  - NEXT: a narrow adversary delta → builder over 169925f (rider: a live read of the engine THROW wrapping; the `_failed_statements` shape change) → cold audit (the one full suite) + contract-blind reader → commit → INDEX "63c-i-a CLOSED".
- **58:**
  - contract r3 7130508, adversary-58-r3 **INSUFFICIENT** (706a1bf): 7 wrong builds.
  - F-B = the 4th CAS-population instance → RE-OPEN am-9 FK-r3-5 (sidecar-64). F-A: the tuple-catch blind spot hides 12 sites (3 in `store/lease.py`: exhaustion → "did not win"; the lease owner rules).
  - NEXT: sidecar-64 re-ruling → r4 fold (am-11's 5 items + findings + a28c's 58 items + FK-6) → adversary delta → build → cold audit → commit.
- **64b-i:**
  - contract r2 **COMMITTED cb220ee** (SAT 0 attributable, 32/32 mutations, currency PASS on 7017b54).
  - Routing items (ledger #17120): BC-r2-13 (G12 waits on 58's Q-DRIVEN pin); BC-r2-9 = am-10's close-out step in the build brief; G2 must be regenerated after a28c (test_retry_seam rewritten).
  - NEXT: a narrow adversary delta → build → close-out step → cold audit → commit.
**WHICH PACKET TO RESUME:** the operator's "the one packet that the contract was in flight for" is AMBIGUOUS. At the pause, a28c (63c-i-a) and 64b-r2 (64b-i) both had contracts in flight; both have since committed. ASK the operator before spawning anything. Recommendation: **63c-i-a** (first in the serial build order; a28c is the last round by rule; 58 and 64b-i build after it).
**AGENTS:** alive, idle, standing by: **sidecar-63c-2** (native only; its lore_comms is ECONNREFUSED) and **sidecar-64** (native only). All one-shot agents were STOPPED 2026-09-29.
**LOOP COSTS:** 63c-i-a contract = 14 revisions (a28c last); 58 = r3, INSUFFICIENT; 64b-i = r2.
**Standing:**
- the lead writes no code; verify in full any commit made without a cold audit (targeted scope);
- no attribution trailers;
- directives = lore_comms + a native wake; the sidecars are native-only;
- never forward `-n` to the gates;
- end turns with the #486 line until #486 is committed;
- kill by PID only; no worktrees, no git stash; assign shell variables before any `&`.

### POST-ANCHOR v7 — resume (2026-09-29, operator: "Resume 63c-i-a and 64b-i"; 58 + #486 stay PAUSED)
- **adversary-63c-i-a-a28c** SPAWNED on `7017b54`: the FINAL delta. It is past the round cap, so its output is a triage-bucket ROUTING table (`SUFFICIENT-FOR-BUILD` | `REOPEN(<new properties>)`); a 4th C2 or RS-5 instance = a pinned bound. Brief: `scratchpad/brief-adversary-63c-i-a-a28c.md`.
- **adversary-64b-r2** SPAWNED on `cb220ee`: the ONE re-grade, with the same routing output plus a BUILD-ORDER feasibility section (which pins and §HELD parts need 58's build; is a 58-free 64b-i build satisfiable under BC-r2-13). Brief: `scratchpad/brief-adversary-64b-r2.md`.
- Both briefs carry:
  - the NEW TEST SCOPE (targeted SAT only; no full suite; no currency run);
  - the MemoryMax=16G cap + `uv run --with pytest-timeout --timeout=300` (not yet a dependency; 58's §HELD adds it);
  - an admission gate (MemAvailable ≥ 20 GiB; the host shows ~30 GiB available);
  - the #486-WIP copy reset (`git reset --hard HEAD && git clean -fd`);
  - a 90-min deadline.
- **sidecar-63c-2** (native): asked to rule FK-a28c-9 / F-15 / F-11 as am-37, each as a builder requirement, a pinned bound or a residual (a28c is the last round). The 58-r4 items are parked with 58.
- **⚠ OPERATOR FORK OPEN:** 64 am-8 ruled 64b-i's SAT base as post-63c-i-a AND post-58, and 58 is paused. adversary-64b-r2's BUILD-ORDER section will give receipts for whether a 58-free 64b-i build (BC-r2-13 in-place) is satisfiable.
- **63c am-37** (`7a40aaa`, sidecar-63c-2) — a28c's three decisions. NOTHING reopens the contract.
  - FK-a28c-9: Reading A confirmed. `_TEXT_DECIDED_KINDS` = a measured allowlist over `KIND_TO_CLASS`; this is an am-36 erratum. The adversary confirms the live Validation cell.
  - F-15: an ACCEPTED RESIDUAL, closed by registry retirement → RED_ORPHANED at close-out. Riders:
    1. the cold audit reads the exact-set pins' MEMBER diff, not their colour;
    2. **the LEAD reads every 58 / 64b-i / #486 commit in this window for a new `except` over `_txn` classes (binding on me);**
    3. the re-open trigger is a second 63c-i-a fix wave.
    The class is filed as **#517**; the gate owner decides at the 63c close-out.
  - F-11: IN the i-a build. ONE ladder helper, shared by `_attempt` and `_txn_query_raw`, keeps the connection on domain kinds with a hygienic message → a **63c-i-a BUILDER CONSTRAINT**, with an audit receipt both ways plus the sharing mutation. The derived-domain ladder pin goes to the next `_txn` contract.
  - §E is operator-visible: F-11 could take ONE targeted pin now with no re-grade. The sidecar declined it: not security-relevant, and the cold audit's receipt covers it.
- Drained 5 ledger signals (#17115–#17120). All are pre-compaction and already handled.
- **adversary-64b-r2 DONE** (`bd017ee`): **SUFFICIENT-FOR-BUILD.** All 10 predecessor survivors and the r1 reference are KILLED; 0 NEW PROPERTY. Targeted SAT: 59 files / 5177 collected.
  - **F-1** (the identity-budget counter's reach: `FROM ONLY` / `$rid`) → a BUILDER requirement at `_resolve_identity` / `resolve_subject_and_agent`.
  - **F-2** (a registry re-read on the deny path, by a caller-supplied name; security-relevant) → **ONE targeted pin, no re-grade (lead decision).**
  - **F-3** (MP-13's param domain is hand-listed = a 2nd WB23 instance; am-8 §6 re-opens the ruling) → sidecar-64 (native), as 64 am-11.
  - **F-4 build order:** a 58-free build is NOT satisfiable from the shipped §HELD. G2 fails loud on a28c's `test_retry_seam.py` (it needs re-deriving either way). A2 already carries the moved drivers. BC-r2-13's fallback has no artifact (it needs an A2′ plus in-place, identity-bearing rewrites of 58's two finding drivers).
  - Residuals F-5..F-9 accepted. Lore friction filed: #518 (`lore_impact` covering tests capped at 15), #519 (a reconcile that never returns).
  - → **OPERATOR FORK: resume 58 before 64b-i, or commission the fallback artifact.**
- **OPERATOR (2026-09-29): "Resume 58 first (Recommended)".** 64b-i builds on its shipped §HELD after 63c-i-a AND 58. G2 is still re-derived after a28c. The build order stays serial: 63c-i-a → 58 → 64b-i. 58 resumes with sidecar-64's re-ruling of am-9 FK-r3-5 (the 4th CAS-population instance). That goes to sidecar-64 once it answers F-3 (it is busy now, and the brief-base inbox rule applies).
- **adversary-63c-i-a-a28c DONE** (`68a1011`): **SUFFICIENT-FOR-BUILD.** 0 NEW PROPERTY; the predecessor 7/7 KILLED; 18/19 wrong builds killed. Targeted SAT: 63c-attributable 0 CONFIRMED (REF-ONLY 35 = §HELD D-9 harness, 0 once applied).
  - **F-1** (WB-H: the cascade picked by an anchored compiled-pattern `.match`; the 4th RS-5 instance, a pinned bound by ruling) → a BUILDER requirement at `_txn._domain_root_cause` (a typed NotExecuted constant) + the cold audit runs KF. No pin now; KF rides am-37 row 4.
  - **F-2** (KG: `_text_testers_in`'s spellings are hand-listed; the 2nd strike on that instrument) → an accepted residual, riding am-37 row 4.
  - R-3: lore's index lags HEAD by docs-only commits. Noted.
  - sidecar-63c-2 was told (FYI).
- **builder-63c-i-a-a28c SPAWNED** (opus55-worker, 2 h 30 min). Brief: `scratchpad/brief-builder-63c-i-a-a28c.md`.
  - It builds in a HEAD-reset scratch copy (it never touches the main tree, with its #486 WIP and a28c's registry residue) and hands back a patch; it does not commit.
  - It carries am-27..37 (am-37 §1's allowlist supersedes a28c's "Internal only"), F-11's one ladder helper, F-1, the live THROW-wrapping read and the `_failed_statements` consumer migration.
  - Its test runs are targeted and capped.
- **Correction #17124 → builder-63c-i-a-a28c** (directive + native ping): apply a28c §A.8 `held_harness.patch` (D-9) in its copy before the baseline. Without it, 35 unexplained reds in test_surreal_harness.py (adversary-a28c §SAT). ⚠ COMMIT HAZARD: #486's WIP owns that file in the main tree, so the lead must stage the D-9 hunk with `git apply --cached` at the 63c-i-a commit, never `git add` the file.
- **64 am-11** (`994c454`, sidecar-64): F-3 is NOT a new property; the ruling itself was the defect. Errata:
  - kickoff §8 F7: params/required move into `GovernedVerbSpec`'s base;
  - am-8 §6: the domain = `inspect.signature(AppContext.findings)` × `_FINDING_ACTIONS`.

  Consequences:
  - `_refuse_foreign_params` = a 64b-i BUILD requirement.
  - ONE generated pin, no re-grade, in the same commit as F-2's.
  - **An inverted pin:** `test_mcp_server.py::_derived_strict_to_action_matrix` (#319) reds on a correct build and needs a spec-dict leg → assigned to the **64b pin pass** (F-2 + F-3 + G2 + the #319 leg), which runs after 58 lands (G2 needs 58's §HELD).
  - Finding **#520** (comms' `values` hand-list; `_comms_foreign_param_error` owner derivation) is the OPERATOR's scope.
- **58 RESUMED → sidecar-64 Task 25 (58 am-12):**
  - re-open FK-r3-5 (F-B) and rule F-A (incl. the 3 lease sites);
  - bucket the r3 findings under the cap (default: no r4 re-grade unless a NEW property);
  - the r4 fold list: am-11 ×5, a28c's 58 items, the `_run_guarded` cas_seam red;
  - r4's base and start time relative to 63c-i-a's commit.
- adversary-a28c's "KF as a contract test?" → NO (the lead's decision above; it rides am-37 row 4). Its lore index lag (1d3cf98 vs bd017ee, docs-only) → noted, not filed (a docs-only delta).
- **63c am-37 §4** (`e455823`, sidecar-63c-2): CONCURS with the F-1/F-2 routing. Row 4's shape is fixed: the derived-domain ladder pin + GARBAGE-TEXT-CORRECT-KIND cells (effect-level, spelling-blind), never a wider tester spelling list.
- **58 am-12** (`5419448`, sidecar-64 Task 25): NEW PROPERTY 0 → **r4 = FOLD, NO delta grade.** The 58 build's cold audit re-runs adversary-58-r3's 7 wrong builds as its mutation set.
  - FK-r3-5 is re-ruled AT THE STATE: `statements_after == 0` + the same instance, with reach = the FIRED ledger == the domain, both ways.
  - F-A: the resolver fails CLOSED. The lease ×4 = named-isolation rows. inbox_awaiter/scout ×8 → `UNLOGGED_SITES` + finding **#521**.
  - The `_run_guarded` cas_seam red is **64b-i's** (it joins `packet-64b-i-contract`'s files).
  - **Lead scope call: the `error_class` ×4 log extra in `store/lease.py` IS carried by 58's build** (the rider is part of the ruling; it adds work and drops none; flagged to the operator).
- **contract-58-r4 SPAWNED** (opus55-worker, 90 min, on HEAD; brief `scratchpad/brief-contract-58-r4.md`). It carries the targeted scope + the cap, the #486-WIP boundary, registry hunk-staging, and ONE named re-base step when 63c-i-a commits.
- **builder-63c-i-a-a28c FK-B1 (a mid-run ping):** F-11's ONE ladder helper broke 2 pre-F-11 structural pins (source-text / lexical-except), and the builder "repaired" them with PROSE naming the ladder (no test edits).
  - **Lead: NOT accepted yet.** A structural pin that a comment or docstring can satisfy is a false gate (a pin that passes for the wrong reason).
  - The **cold audit brief will carry an explicit check:** for each of the two pins, does it pass by CODE or by PROSE? Mutation: delete the prose and keep the code, and the pin must stay green if the code is right. Also: is the prose true?
  - The pins' AST re-key → am-37 §W row 4 (the next `_txn` contract) either way.
  - Also pending from the builder: D-4 (the empty-text root-cause skip dropped; spec-silent) and D-5 (the `Cancelled` cascade kind is outside `_CASCADE_KIND`). → sidecar-63c-2 once the report is final.
- **builder-63c-i-a-a28c DONE** (`3e0553f`). Patch `956e4136` on `bbf6a0c` (8 files: 6 production + the §HELD harness hunk + the registry block deletion; verified: md5, and no loremaster/lorerunes/scripts delta `bbf6a0c`→`3e0553f`).
  - Declared set 67 files: 398 RED→GREEN, 0 GREEN→RED; the remaining reds are 58/64b-owned. 20/20 concurrency. F-11 live both ways. KF 2/2.
  - **FK-B1 → Reading A ACCEPTED** (am-37 §3 refuses copy #2). Pin 1 (`test_surreal_store` source-text) is now PROSE-satisfied, a known false gate. The cold audit proves the ONE mapping by mutation, and its AST re-key → am-37 §W row 4. Pin 2 is a prose-currency pin by design, so the audit checks the prose is TRUE.
  - D-4/D-5 → sidecar-63c-2 (am-37 §5).
- **coldaudit-63c-i-a-3 + blindreader-63c-i-a-3 SPAWNED** (2 h / 90 min). The audit's ONE full suite = `pending_contract_gate.py --currency -- --maxprocesses=12` under the 16G cap: the packet's single full suite, with per-red adjudication; `--maxprocesses` works around #508's `auto`. The audit also does a real dirty-store restore.
- **63c am-37 §5** (`ac60acd`, sidecar-63c-2).
  - D-4 is ACCEPTED (am-36: text is evidence, not a selector input; the empty-text shape is unmeasured, and the bound is stated).
  - **D-5 = a BUILDER REQUIREMENT BEFORE COMMIT:** `_CASCADE_KINDS = frozenset({QueryDetailKind.NOT_EXECUTED, QueryDetailKind.CANCELLED})` (`TIMED_OUT` adjudicated substantive). NotExecuted-only serves a FALSE root cause in the degenerate all-cascade list. The rename is free (no pin names it); the `QueryDetailKind` completeness pin → row 4.
  - FK-B1 A: concurred.
  - → **The post-audit FIX ROUND carries D-5** + any cold-audit / blind-reader findings, then a 30-min re-check. The builder and the two adversaries are STOPPED (done).
- **blindreader-63c-i-a-3 DONE** (`cdf840d`; stopped): 0 BLOCKER · 2 MAJOR · 7 MINOR · 7 NOTE. The typed `_txn` holds LIVE on 3.2.4 and FIXES two old echo misclassifications (F-A governed-by-substring, F-B "can be retried" echo).
  - **M-1:** the store reference §3/§6 item 3/#111 still teach the text marker, "no typed alternative" (the required-first-read is now false).
  - **M-2:** `table_defined` defaults True, so refusals over-claim.
  - MINORs: F-4/F-5 stale docstrings · F-8 an RPC conflict doesn't update `last_conflict` · F-9 the mixed-owner count includes the operator (a label/set mismatch) · F-10 silent un-migrated message rows · F-12 bare SurrealStoreError → a traceback instead of exit 1 · F-13 register's unbounded recursion + raw re-raise.
  - F-6 == D-5 (derived independently).
  - → **sidecar-63c-2 triage (am-37 §6)**. The default is ONE post-audit fix round carrying D-5 + all of these (M-1 edits docs/reference in this wave).
- **63c am-37 §6** (`ea87b3c`, sidecar-63c-2): the blind-reader-3 triage, each item pin-checked with a STOP condition.
  - **FIX-IN-ROUND:** M-1 (the store reference corrected per the enumerated facts), M-2 (`table_defined` has no default; it is derived once and is None iff INFO was not read), F-4/F-5, F-8 (reset `last_conflict` per attempt), F-9 (am-34 §2 form: one integer, as the total), F-10 (a measured `unsound_sender_messages` field + a derived sentence), F-12 (a base-class catch + one fail-closed `_scope_count`), + §5 D-5.
  - **RESIDUAL:** F-13 (as ruled am-32; wrapping REFUSED, since it reddens a28b's `_CAUSE_CLASS` exact set), F-14, F-16, and the fixture drift → row 4.
  - The F-8 label rider → contract-58-r4 (#17128-ish directive; durable).
  - The blind reader's untested `store.transaction.rejected` / connection-kept path: covered live by the audit's F-11 receipt, and its pin is in row 4 (the next `_txn` contract).
- **contract-58-r4 DONE** (`4d864c9`; stopped). The am-12 fold landed, tests only. SAT 0 r4-attributable (REF 661F/6176P vs BASE 850F/5933P). 10/10 mutations held. `--verify-registry` OK.
  - **Collision flag:** REF-ONLY 36 = 63c's generated sweeps over 58's reference `_txn` classes. They must go GREEN once 63c-i-a lands, a STOP check at r4 §RE-BASE.
  - `test_task_ledger.py` ×10: red only on HEAD+§HELD part 1, green on the reference.
  - Finding #522 (lore_impact renders `store.lease` dead).
  - **Open → sidecar-64 (58 am-13):** FK-r4-1 (6 admissions removed, exact-both-ways) · F-F NOT DONE (evidence by import) · the 63c am-37 F-8 label rider, NOT folded despite #17128. Each lands as a 58 build requirement, a bound or a residual; the contract is closed.
- **58 am-13** (`9e5d9b3`, sidecar-64 Task 26):
  - (1) FK-r4-1 (A) CONFIRMED: the admissions are exact BOTH ways, and the six stay deleted (erratum: am-11's "8+2" was un-derived). The 58 cold audit re-derives `translate_targets() == FAULT_CLASS_NAMES`.
  - (2) F-F is a BOUND; its owner = the 64b pin pass (the by-import rewrite, once for all eight). 58's cold audit records `evidence_probe.py` as an ACCEPTED RESIDUAL.
  - (3) The F-8 rider = a **58 BUILD requirement**: the txn path passes label/url to `retry_on_conflict` and raises its signal `from` a typed cause carrier (not a SurrealStoreError subclass). The §10 exemption is deleted (STOP check: a28c's allowlist pin). Verified by a generated per-call-site check (5 sites, reach checked). It composes with 63c am-37 §6 F-8's reset.
  - → **64b pin pass scope now:** F-2 pin + F-3 generated pin + G2 re-derivation + the #319 spec-dict leg + F-F by-import rewrite.
- **coldaudit-63c-i-a-3 DONE** (`535677a`; stopped): **NO-GO for patch 956e4136 as-is.**
  - The CORE HOLDS, with controls:
    - currency (the packet's ONE full suite, capped, `--maxprocesses=12`) PASS, 0 RED_ORPHANED;
    - 20/20 concurrency;
    - F-11 live both ways (connection kept; transport control drops);
    - KF + 19 garbage-text-correct-kind cells;
    - FK-B1: the mapping is behaviourally guarded (bypass → 52 reds) and pin 1 is prose-only (→ row 4);
    - the prior NO-GO's defects are fixed for the right reason.
  - 4 MAJOR:
    - F-C1/F-C2/F-C3 = am-37 §5 D-5, §6 M-2, F-9 (independent);
    - **F-C11 (NEW): §5's `in _CASCADE_KINDS` spelling reddens a28c's text-reader exact-set pin; `==` passes** → sidecar-63c-2 am-37 §7 BEFORE the fix round.
  - 7 MINOR: the new F-C4/F-C7/F-C8/F-C9/F-C10 → §7.
  - Commit mechanics: the patch conflicts with #486's WIP in the registry yaml; it applies clean with `--cached` (lead, at commit).
  - **R-1: FOCUS 7 (the real prod-dump restore, the #107 class) was DENIED by the permission layer ("Modify Shared Resources"), the 2nd audit in a row** → OPERATOR decision: grant it or run it. The auditor also had a plain source read in its own scratch copy denied.
- **63c am-37 §7** (`6ade684`, sidecar-63c-2):
  - F-C11: §5's `in` spelling was the erratum. The ruling is the SDK's own `QueryError.is_not_executed or is_cancelled` (no compare, no set; the tester pin is met, not dodged).
  - F-C7, F-C8(+F-14), F-C9: FIX-IN-ROUND.
  - F-C4: BOUND → #34's sanitiser owner. F-C10: BOUND.
  - No contract edit.
- **OPERATOR:** "You run the restore (Recommended)". The operator runs `restore_prod_dump.py` and hands over `LORE_PROD_DUMP_DB=<name>`. The fix-round re-check runs `migrate_governed` against it and reaps it.
- **builder-63c-i-a-fix2 SPAWNED** (opus55-worker, 90 min; brief `scratchpad/brief-builder-63c-i-a-fix2.md`). It works on patch 956e4136 in a scratch copy and carries am-37 §5-as-§7 + §6's 8 + §7's 3, M-1 included (it edits the store reference). Targeted scope: the packet's ONE full suite already ran in coldaudit-3.
- **Operator restore DONE (2026-09-30 00:11Z):** `LORE_PROD_DUMP_DB=test_dump_20260930T001125Z_a072e4789558446bb05abce309b4a4fb` (ns `lore_test`, :18000). The governed slice declared == readback on every table: agent 95 · message 316 · memory 177 · brief 26 · finding 324 · task 116 · to 337 · briefed 123 (all pre-63 shape, scope NONE == rows). principal / keep / member_of / audit / blocks / principal_key are ABSENT (the dump predates them), so the re-check must bootstrap the operator principal + project keep as a fresh deploy would. → Given to the fix-round re-check auditor, which reaps it with `--reap`.
- **builder-63c-i-a-fix2 DONE** (`1b219f9`; stopped). 8/9 am-37 items FIXED. 0 GREEN→RED over 72 files. Item 1 live (degenerate → LAST; a base-predicate control → the false Cancelled root). Full patch `01fd0471`, delta `54e6b613` (the delta touches the store reference + governed/keeps/principals/_txn, no tests).
  - **F-12(a) STOP:** the base-class catch reddens `test_exhaustion_fates` (a new catch site over TxnContentionExhaustedError). Its remedy is a REGISTERED_FATES row in 58's `_exhaustion_fates.py` → sidecar-63c-2 (am-37 §8: row vs passthrough) + sidecar-64 (does 58's fates law accept it).
  - The other decisions → am-37 §8: F-a (the F-10 sentence on stderr, exit 0) and the §DRY GROUP ALL reader duplication (two policies).
- **⚠ 58 r4 (`4d864c9`) LEFT TWO DEFECTS** that go RED_ORPHANED once 63c-i-a's registry entry is deleted, so they BLOCK the 63c commit (measured by fix2 on HEAD + the audited patch; r4 committed AFTER coldaudit-3's run):
  - (1) typecheck `RED_ORPHANED 2` (`type[FindingLedger]._run_guarded`): am-12 §4 item 3's "one path in two rows is legal" is FALSE for the typecheck matcher;
  - (2) 63c's one-scanner pin finds ZERO walkers after r4's `_catch_sites.py` edit.
  → sidecar-64 (58 am-14). The exact test-side edits land via a small contract-author-class fix-up BEFORE the 63c commit, together with F-12(a)'s row.
- **LEAD LESSON (mine):** the r4 brief forbade ALL currency runs. `--currency --legs typecheck,ruff` runs NO pytest and is exactly what would have caught (1) per round. The TEST SCOPE policy forbids the pytest leg only; future briefs allow the non-pytest legs. → Proposed to the operator as a CLAUDE.md clarification.
- **63c am-37 §8** (`bcb7bc2`, sidecar-63c-2):
  - F-12(a) → **OPTION A** (the base-class catch + a REGISTERED_FATES `cli-exit` row; the site's owner owns the row, per the U-27 precedent; the passthrough is REFUSED as a door).
  - F-a: stderr + exit 0 CONFIRMED, with a rider: the stdout receipt line carries `unsound_sender_messages` as a typed count.
  - §DRY: the GROUP ALL count reader = FIVE copies (findings, messages, diff, `governed._scope_count`, `principals._group_all_count`). ONE policy (empty → 0; wrong shape → SurrealStoreError) as `governed.group_all_count`. **63c's two copies collapse NOW**; findings/messages/diff → 64b, decided at the 63c close-out.
  - Walker-pin re-keys route through sidecar-63c-2.
- **The next wave (after sidecar-64's 58 am-14):** fix-round-3 = a production builder (the F-12(a) catch, the stdout typed count, the `group_all_count` consolidation) + a test-side fix-up (the fates row, r4's two orphan defects per am-14). Both are built on patch 01fd0471, then the re-check audit (targeted + the restored prod slice `test_dump_20260930T001125Z_…`).
- **58 am-14** (`a9be2c4`, sidecar-64 Task 27): r4 wrote NO second walker.
  - (1) The typecheck orphans' ONE place = the gate's matcher (`Registry.entry_for` is first-match on the typecheck leg, while pytest unions): `entries_for(path)`, admitted iff ANY entry admits it, with a 2-test TDD in `scripts/test_pending_contract_gate.py`. The registry is unchanged; am-12 §4.3 has an erratum.
  - (2) The one-scanner pin's `_RESOLVER_NAMES` hand-list lost the ONE walker. Its derivation becomes transitive through calls (63c-owned → sidecar-63c-2 concurrence requested).
  - (3) The F-12(a) `cli-exit` row is ACCEPTED (riders: `catches=` == `ast.unparse` of the production tuple; one commit).
  - Sequencing: am-14 §4.
- **Plan (lead):**
  - fixup-tests-63c-i-a (tests only: am-14 §1 tests RED, §2 re-key, §3 row) → builder-63c-i-a-fix3 (production: the gate matcher, the F-12(a) catch, am-37 §8's typed stdout count + the `group_all_count` consolidation) → a re-check audit (targeted + the restored prod slice) → the 63c-i-a commit.
  - The gate-matcher fix rides the 63c commit set as its own commit (one concern each).
- **63c am-37 §9** (`731a84f`): CONCURS with 58 am-14 §2, plus ONE rider: resolve Import/ImportFrom aliases before the call closure, +1 control. It accepts 58's two F-12(a) row riders.
- **fixup-tests-63c-i-a SPAWNED** (opus55-worker, 60 min; brief `scratchpad/brief-fixup-tests-63c-i-a.md`): tests only, on the fix2 patch in scratch; the patches are handed back, not committed.
- **fixup-tests-63c-i-a DONE** (`755e3a4`; stopped). The 3 ruled test edits landed in scratch (§1 RED on first-match for the right reason; §2 re-key GREEN 4/4 + the §9 alias rider; §3 row RED until the catch lands). Mutation proofs held. Full patch `2c88b1a9` (fix2 + tests), tests-only delta `88c52be2`.
  - D-1: a sibling of am-14 §1 in the per-entry unsymboled self-destruct leg (latent; fails loud). **Lead: FIX-THE-CLASS now** — every per-path lookup goes through the ONE `entries_for`, and the re-check audit constructs the case.
- **builder-63c-i-a-fix3 SPAWNED** (60 min): the gate matcher (+D-1), the F-12(a) catch, the am-37 §8 typed stdout count, and the `governed.group_all_count` consolidation (sharing proven by mutation). REQUIRED: currency `--legs typecheck,ruff` RED_ORPHANED 0.
- **builder-63c-i-a-fix3 DONE** (`63c5c71`; kept AT REST for a possible delta).
  - Results: 4 items; 0 GREEN→RED; 2 RED→GREEN (the fix-up's intended reds); **currency typecheck/ruff RED_ORPHANED 0** (83 residuals, all owned); ruff clean.
  - Delivered: `entries_for` is the ONE per-path lookup (`entry_for` deleted; the D-1 sibling fixed, probe-proven, NO pin). The F-12(a) tuple is exact. The stdout receipt carries `unsound_sender_messages` when measured. `governed.group_all_count` has its sharing proven by mutation.
  - Full patch `5a1d411c` (fix2 + tests + fix3) on `fb95d1f`, delta `abbb0edd`.
  - **Flag F-1:** am-37 §8.3's "five readers" is an UNDERCOUNT. There are ≥6 more tolerant GROUP ALL readers; **2 are FAIL-OPEN**: the principal-delete `owned_count` (the SF-63-5 guard bypassed on a malformed answer) and the unmigrated-rows boot alarm (silent). → sidecar-63c-2 am-37 §10 (lead default: fix (a) now; rule boot fail-vs-log for (b); the rest → the 64b §DRY step).
  - F-2 (None-render) and the D-1 pin → a residual for the next gate contract.
- **63c am-37 §10** (`cfaf793`):
  - (a) `owned_count` is FIXED NOW, fail-closed via `group_all_count` (a malformed count refuses the delete).
  - (b) The boot alarm: a malformed count takes the SAME fate as a rejected count query, never a boot fail. If that fate is silent today, it becomes a logged ERROR with exc_info.
  - F-2: render `unsound_sender_messages=None` explicitly (the #131 unrendered-field shape).
  - D-1 pin: the fix-up OR a residual. **Lead: RESIDUAL**, owner = the next gate-touching contract (latent, fails loud; a test-author round is not worth it).
  - Sidecar erratum: §8.3's "FIVE" was un-derived (≥11); the rest of the sweep → the 64b §DRY step.
- The §10 delta was sent to builder-63c-i-a-fix3 NATIVELY; it resumes from its transcript, with a 40-min deadline. (lore_comms refused: the agent had retired its registration. Retirement is terminal.) Proof of receipt = its report's §10. If none appears → respawn `builder-63c-i-a-fix4`.

## RESUME ANCHOR v8 (2026-09-30 ~01:55Z, lead-63c-2, session 63c-20260924) — AUTHORITATIVE; supersedes v7
**OPERATOR scope:** "Resume 63c-i-a and 64b-i", then "Resume 58 first (Recommended)".
- **Build order:** 63c-i-a → 58 → 64b-i, serial.
- **#486 stays PAUSED:** its WIP is uncommitted in the main tree.
- **Not started:** #492, #512, the holes, the test smells, 63c-i-b, 64a, 64b-ii, 64c, 65.

**TEST POLICY (CLAUDE.md TEST SCOPE):**
- targeted runs only; `-n 8`; every run under `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout … --timeout=300`;
- admission gate: MemAvailable ≥ 20 GiB;
- scratch copies via `scratch_copy.sh`, then `git reset --hard HEAD && git clean -fd`;
- ONE full suite per packet = the cold audit, run as `pending_contract_gate.py --currency -- --maxprocesses=12`, capped;
- ⚠ briefs ALLOW `--currency --legs typecheck,ruff` (no pytest); forbidding it let r4 ship orphans (lore memory 8c7a11fb).

**63c-i-a (IN FLIGHT, near commit):**
- **Patch chain** (all in scratch; nothing production is committed):
  - builder `956e4136`;
  - fix2 `01fd0471` (`…/f503eb3c…/scratchpad/builder-63c-i-a-fix2.patch`);
  - test fix-up full `2c88b1a9` (`…/c4f63f4e…/scratchpad/fixup-tests-63c-i-a.full.patch`; tests-only delta `88c52be2`);
  - fix3 full `5a1d411c` (`…/5e3e72cf…/scratchpad/builder-63c-i-a-fix3.full.patch`, on `fb95d1f`).
- **NOW:** builder-63c-i-a-fix3 is applying the **am-37 §10 delta** (`cfaf793`), deadline ~02:25Z; it was sent natively, and its lore_comms registration is retired:
  - (a) `owned_count` fail-closed via `governed.group_all_count`;
  - (b) the boot alarm: a malformed count = a rejected-count fate, never a boot fail; a logged ERROR if silent today;
  - (c) the receipt renders `unsound_sender_messages=None` explicitly.
  - Proof of receipt = a §10 section in `REPORT-builder-63c-i-a-fix3.md` + a NEW full-patch md5. If none appears, respawn `builder-63c-i-a-fix4` with that delta.
- **NEXT: a re-check audit** (`coldaudit-63c-i-a-4`, ~45 min) on HEAD + fix3's NEW full patch:
  - the targeted set (fix3's 74 files) + currency `--legs typecheck,ruff` RED_ORPHANED 0;
  - verify every am-37 §5–§10 item, the am-14 edits, and D-1 by construction;
  - **the REAL DIRTY STORE:** the operator restored `LORE_PROD_DUMP_DB=test_dump_20260930T001125Z_a072e4789558446bb05abce309b4a4fb` (ns `lore_test`, :18000; agent 95 / message 316 / memory 177 / brief 26 / finding 324 / task 116, all pre-63 scope NONE; principal/keep/member_of ABSENT). The audit bootstraps an operator principal + project keep as a fresh deploy would, runs `migrate_governed` for every `--table`, compares each served count to a direct SELECT, checks `unsound_sender_messages`, then `restore_prod_dump.py --reap <name>` and proves it gone.
  - No full suite unless a production delta outside the targeted derivation appears (the packet's ONE full suite ran in coldaudit-3, `535677a`: PASS, 0 orphaned).
- **COMMIT MECHANICS (lead), on GO:**
  - the main tree has #486 WIP (incl. `test_surreal_harness.py`, the registry yaml). Use `git apply --cached <final full patch>` on HEAD (NEVER `git add` those files), then also apply the production + scripts + docs files to the working tree;
  - one concern per commit is preferred: (i) the gate matcher (`scripts/pending_contract_gate.py` + `scripts/test_pending_contract_gate.py`); (ii) the 63c-i-a build (production + tests + the §HELD harness hunk + the registry block deletion + the store reference) — or one commit if they are entangled;
  - no attribution trailers;
  - then the INDEX Log line "63c-i-a CLOSED", and archive the REPORT-*.md files for 63c-i-a into `docs/plans/v2/receipts/2026-09-30-63c-i-a/` via git mv.
- **Residuals to list at close-out:**
  - the D-1 gate pin → the next gate contract;
  - am-37 §W row 4 (the derived ladder pin, KF, the garbage-text cells, the FK-B1 pin-1 AST re-key, the QueryDetailKind completeness, the fixture drift);
  - F-C4 → #34;
  - F-C10, F-13, F-14, F-16;
  - the ≥6 tolerant GROUP ALL readers + findings/messages/diff → the 64b §DRY step;
  - #517;
  - F-B1 pin 1 is decoration until row 4.

**58 (NEXT after the 63c commit):**
- contract r4 is COMMITTED `4d864c9` (the am-12 fold; NO re-grade by rule).
- Rulings: am-12 `5419448`, am-13 `9e5d9b3` (FK-r4-1 confirmed; F-F = a bound → the 64b pin pass; the F-8 label rider = a 58 BUILD requirement), am-14 `a9be2c4`.
- **Build brief must carry:**
  - the r4 §RE-BASE step first (`git apply --check` §HELD parts 1/3 on the new HEAD; re-run the targeted set; ⚠ **the 36 REF-ONLY reds (63c sweeps over 58's `_txn` classes) must go GREEN, else STOP**);
  - r4 §BUILDER CONSTRAINTS (incl. `more-itertools` + `pytest-timeout` deps, the lease `error_class` ×4 = lead scope call, esc1, the §1 FIRED-ledger instrument);
  - am-13 (3) (txn-path label/url + a typed cause carrier, generated over the 5 `retry_on_conflict(` sites);
  - the cold audit re-runs adversary-58-r3's 7 wrong builds as its mutation set + re-derives `translate_targets() == FAULT_CLASS_NAMES`;
  - F-F → an accepted residual.

**64b-i (after 58):**
- contract r2 `cb220ee`; adversary-64b-r2 `bd017ee` SUFFICIENT-FOR-BUILD.
- **The 64b pin pass (tests, before the build):**
  - F-2's targeted pin;
  - F-3's generated pin (am-11 `994c454`);
  - G2 re-derivation over a28c's `test_retry_seam.py`;
  - the #319 `_derived_strict_to_action_matrix` spec-dict leg;
  - F-F's by-import `_exhaustion_fates` rewrite;
  - the registry re-key `lore_findings::<verbs>` (am-12 §4.3).
- **Build requirements:**
  - F-1 (`_resolve_identity` budget);
  - `_refuse_foreign_params`;
  - BC-r2-9 close-out step (am-10);
  - fix2 F-b: any 64b leg constructing `MigrateGovernedResult` passes `table_defined=` and `unsound_sender_messages=`;
  - the 64b §DRY GROUP ALL sweep (findings/messages/diff + the ≥6).
- Finding #520 (comms `values` hand-list) = the OPERATOR's scope, unanswered.

**AGENTS alive:**
- sidecar-63c-2 (native only; its lore is ECONNREFUSED) and sidecar-64 (native), both idle;
- builder-63c-i-a-fix3 (working on §10).
- All others are STOPPED. Never reuse names: used names include adversary-63c-i-a-a28c, adversary-64b-r2, builder-63c-i-a-a28c, builder-63c-i-a-fix2, builder-63c-i-a-fix3, fixup-tests-63c-i-a, coldaudit-63c-i-a-3, blindreader-63c-i-a-3, contract-58-r4.

**OPEN OPERATOR ITEMS:**
- (1) May the lead add the CLAUDE.md TEST SCOPE clarification ("only the currency gate's pytest leg is close-out-only; `--legs typecheck,ruff` is allowed per round")?
- (2) Finding #520 scheduling.

**Live background:** the prod RSS sampler (b0nin9fbc, → `scratchpad/prod_surreal_rss.tsv`); prod lore-surreal holds ~6.2 GiB, and the >20 GiB is not reproduced. The prod dump DB above lives on :18000 until reaped.

**Standing:**
- the lead writes no code;
- no attribution trailers;
- kill by PID only; no worktrees, no stash; assign variables before `&`;
- never forward `-n`;
- never :18500; never the production TEI;
- never attribute host memory to ZFS ARC;
- end turns with the #486 line.

## POST-ANCHOR v8 — operator rulings (2026-09-30)
- **CLAUDE.md TEST SCOPE clarification: GRANTED and landed (`baa313c`).** `--currency --legs typecheck,ruff` runs no pytest and is allowed every round; only a bare `--currency` (its pytest leg) is close-out-only.
- **#520: fold part 1 into the 64b-i BUILD (operator).** 64b-i build brief requirement:
  - `AppContext.comms` derives its supplied-param set from `inspect.signature` (computed once at import); the hand-written `values` list is DELETED;
  - comms routes through the ONE `_refuse_foreign_params`, which then has three callers;
  - sharing is proved by MUTATION, and every caller's pins must go red;
  - part 2 (`actions=` plus the owner-assert rider) is already am-11 §3.3.
  - Resolve #520 at the 64b-i commit. Finding annotated.
- **fix3 §10 DONE (8abf1e2, 5005371).** New full patch `builder-63c-i-a-fix3.r2.full.patch` md5 `f5897681430ad5e7c5d719dab12815bd` (lead-verified on disk; `git apply --check --cached` OK at 5005371); delta r2 `4516d9b1…`. Scratch `…/5e3e72cf-a647-4837-966a-5e40d72da932/scratchpad/`.
  - Runs: 74+1 files, base 5926/341 → build 5928/339; RED→GREEN 2; GREEN→RED 0; remaining reds owned (64b-i 272 / 58 60 / both 7).
  - The 4-caller sharing mutation held; RED_ORPHANED 0.
  - **OPEN, waiting on the operator:** FLAG R2-1. `lore-adm delete`'s `_dispatch` does not catch `SurrealStoreError`, so a store fault prints a traceback (the delete is still refused). CLASS: every lore-adm verb's store fault → stderr + exit 1.
    - Options put to the operator: (1) fold it into 63c-i-a before the re-check audit, via a sidecar ruling + a fates row + a generated pin + a builder (recommended); (2) its own commit right after 63c-i-a.
    - The re-check audit is held until the operator picks.
- **R2-1: operator ruled FOLD into 63c-i-a before the re-check (~02:15Z).**
  - Sequence: sidecar-63c-2 am-37 §11 ruling (requested natively; deadline ~02:45Z) → a test-side agent (`fixup-tests-63c-i-a-2`: fates row + any generated pin) → `builder-63c-i-a-fix4` (the one chokepoint, on the r2 patch `f5897681…`) → `coldaudit-63c-i-a-4`.
  - Unused names reserved: fixup-tests-63c-i-a-2, builder-63c-i-a-fix4, coldaudit-63c-i-a-4.
- **am-37 §11 ruled (`1708a4c`).**
  - One handler at `_dispatch` with the 5-class tuple; the 3 verb dispatchers lose their excepts; FR-2 D1 re-ruled.
  - fates: 2 rows → 1 (`principals.py::_dispatch`).
  - A generated pin ∀ `build_parser()` verb × an `ensure_ready` injection.
  - It is a new CASE of a pinned property, so there is no contract round (rule 5).
- `fixup-tests-63c-i-a-2` spawned about 02:30Z (45 min; base r2 `f5897681…`). Next: `builder-63c-i-a-fix4`.
- **fixup-tests-63c-i-a-2 DONE (`774a0f7`).** Full patch `85a4d2e175a974633d60a81e8020d060` and delta `c216df30…`, both lead-verified on disk; apply-check OK.
  - The generated pin fails 15/17 on fix3 r2 for the right reason and passes 17/17 on the reference build.
  - The mutation proof held; no STOP fired.
  - R2 (its own mutation proof): accepted.
- **Two agents running in parallel (~02:30Z), on disjoint files:**
  - (i) `fixup-tests-63c-i-a-2` ROUND 2, resumed natively. F-1 is a verification first: derive KeepStore's write boundaries and name each one's wrap pin, with a mutation on `add_household`. If a boundary has no pin, that is a guard §11 removed: STOP, and it goes to the sidecar. Then the F-1..F-3 docstrings as a docstrings-only delta.
  - (ii) `builder-63c-i-a-fix4` spawned: the §11 production edit in `principals.py` only, on 85a4d2e1.
  - Composition for the audit: fix4 full + the docstrings delta (disjoint files).
- **fixup2 ROUND 2 DONE (`b2affe3`).**
  - No STOP: all 7 derived KeepStore write boundaries are wrap-pinned, and the `add_household_member` mutation held (5/5 declared).
  - 9 stale D1 docstrings were fixed; AST-equal modulo docstrings; failed set unchanged.
  - Docstrings delta `afa519cf7c4eca5241a060ca80cbc367`, full2 `e915b90f7f58712e164608a7fc8d2002`, both lead-verified; full2 apply-check OK.
  - ⚠ One run was admitted at 18 GiB (<20 gate): self-reported, cgroup-capped, no kill. Surfaced to the operator.
  - R2-F1: the coverage population is "references the wrap", not "writes", so a new unwrapped write is invisible, and §11 removed the incidental CLI traceback signal. Lead lift: ∀ store a lore-adm verb reaches. Sent to sidecar-63c-2 for am-37 §12 (~02:40Z, 20 min).
- **am-37 §12 ruled (`4e3a96c`).** The lift is right, and the class is FALSE today: 4 unwrapped write boundaries (`PrincipalStore.set_status`/`set_expires`/`delete`, `PrincipalKeyStore.revoke`).
  - It rides this fold: 4 one-line wraps + a derived per-store pin; the routed-set expectation is re-keyed to derived writes ∪ declared read-wrappers.
  - Order: the test side first (RED on exactly the 4), then the wraps.
  - The fixup2 ROUND 3 test side was sent natively (~02:35Z, 40 min). fix4 (busy, §11) is NOT steered; the wraps go to a new builder `builder-63c-i-a-fix5` on top of fix4 full + docstrings + r3 tests.
  - The operator was told the fold grew by §12.
- **builder-63c-i-a-fix4 DONE (`413775d`).**
  - Delta `fd70c6e9d4fff15e605660666a60a737` (principals.py only) and full `b10c6d7e2590a08a6b79273c27d86a3d`, both lead-verified on disk.
  - Runs: 0 GREEN→RED, 16 RED→GREEN (15 verbs + fates both-ways), 9 owned pkt-58 reds; no STOP; composition with docstrings `afa519cf` = 64 passed.
  - Audit items: R-1 (close-before-print ordering) and R-2 (factory faults are now laundered); neither is pinned.
  - NEXT: when fixup2 ROUND 3 lands, `builder-63c-i-a-fix5` builds the §12 wraps on full2 `e915b90f` + fix4 delta `fd70c6e9` + the r3 delta.
- **fixup2 ROUND 3 DONE (`def8d51`).**
  - The §12 pin is RED on exactly the 4 boundaries (37 declared = 37 observed) and GREEN on the reference wraps.
  - The create-wrap mutation held 6/6; STOP 1 and STOP 3 are clear.
  - r3 delta `c377c11ecf04697f6098da1780ca8ade` (the test file only) and full3 `299467bad167496a1e3bbc3c96b8a034`, both lead-verified.
  - Lead check: full3 + fix4 delta `fd70c6e9` compose at def8d51.
  - Ruling on its builder note: the `delete` wrap is whole-body from `get_by_email` (reading B).
- `builder-63c-i-a-fix5` spawned about 02:45Z (40 min): the 4 wraps in principals.py + principal_keys.py, on full3 + fix4 delta. Its full patch is the FINAL 63c-i-a patch.
- The re-check audit `coldaudit-63c-i-a-4` follows. Audit items so far: R-1, R-2 (fix4 §5).
- **builder-63c-i-a-fix5 DONE (`5089146`).**
  - FINAL 63c-i-a patch `…/e1f81771-6cf2-4679-b6f7-c87b1afe1196/scratchpad/builder-63c-i-a-fix5.full.patch`, md5 `5f2d7c4366d469e5c2a34d53aa235d6e` (18 files; lead-verified; `apply --check --cached` OK at 5089146). Delta `4e3024e7…`.
  - Runs: 0 GREEN→RED; exactly the 20 declared RED→GREEN; 36 owned reds (58 ×9, 64b-i ×27, the latter in `test_findings_classes_64b.py`).
- **COMMIT HAZARD (lead-checked).** The final patch conflicts with the main tree's working copy ONLY on `scripts/pending_contracts.yaml`; `test_surreal_harness.py` applies over the WIP cleanly.
  - The yaml WIP is ONE hunk, entirely inside the `packet-63c-i-a-a28-contract` entry: a stale, uncommitted a28c edit to 63c's own entry, with no #486 content. The final patch DELETES that entry (it self-destructs with the build).
  - At commit: `cp -a` the working yaml to the scratchpad, then `git apply --cached` the final patch, apply the patch to the working tree excluding the yaml, and set the working yaml to the new HEAD blob. #486's other WIP files are untouched.
- **Spawned about 02:55Z, in parallel:** `coldaudit-63c-i-a-4` (90 min; checks 1–8, incl. mutations (a)–(d), R-1/R-2, the real dirty store + reap — if the reap is denied, it goes to the operator) and `blindreader-63c-i-a-4` (45 min; contract-blind, production diff a28c→final).
- **blindreader-63c-i-a-4 DONE (`da24013`).** 0 BLOCKER / 0 MAJOR / 9 MINOR / 7 NIT; no fault prints success. Independence is slightly weakened: a sweep printed ~20 withheld amendment lines, which it says it did not use.
  - Preliminary lead triage (final triage waits for coldaudit-63c-i-a-4):
    - **Fix-now candidates (pinned classes, 63c's own files):**
      - F-1: delete's key-cascade count is fail-open; same class as §10.1(a) → `group_all_count`.
      - F-6/F-7: one fail-closed wrong-shape policy. `_rows_stamped` raises `TypeError` post-commit, which tracebacks; `_governed_select` drops non-dict rows that feed a refusal guard.
      - F-5: a post-commit fault reads "nothing was decided".
      - F-4: relabel `unsound_sender_messages` (Leg-1 scope diff).
      - Prose: F-2, F-10, F-14, F-15 (stale STUB/help).
    - **Audit cross-checks:** F-11 (the gate's unsymboled-count leg is per-entry — is D-1 incomplete?), F-12 (the text-ladder unique label).
    - **Pre-existing, surface:** F-13 ("already exists" on any store error).
    - **Residuals:** F-8 (= R-1), F-16.
    - **Operator decisions:** F-3 (print the wrapped fault's cause), F-9 (distinct exit codes for retryable vs refused).
- **coldaudit-63c-i-a-4: GO (`8026854`)** for the final patch `5f2d7c43`.
  - Prior NO-GO items: all closed or named residuals. Rulings verified by construction. Mutations (a)–(d) fire.
  - Targeted run: 101 files, 340 failed / 7205 passed, owners 64b-i 272 / 58 61 / both 7 / ORPHAN 0; the 63c pin files have 0 reds.
  - REAL DIRTY STORE: after the boot DDL, every served count = a direct SELECT (agent 95, memory 177, message 316, `unsound_sender_messages=0`), idempotent on re-run; the dump was REAPED and proven absent.
  - R-1 acceptable, with a MINOR residual; R-2 acceptable.
- **New findings, not introduced by the patch:**
  - D-1 MAJOR: the dump name is refused by `SurrealConfig.database` → packet 64.
  - D-2 MAJOR: migrate on a pre-boot schema is an opaque "unspecified rejection".
  - D-3 MAJOR: "see the server log" points at nothing in lore-adm; `engine_error` is dropped.
  - N-1/N-2/N-3 prose.
- **Combined triage with blindreader-4 (lifted to classes):**
  - A. The lore-adm error line teaches the cause (D-3 + F-3; this also makes D-2's engine detail visible). ONE chokepoint: the §11 handler.
  - B. Fail-closed counts/shapes: F-1 (delete `cascaded`), F-6 (`_rows_stamped` `TypeError` post-commit), F-7 (`_governed_select` drops non-dict rows feeding a refusal).
  - C. Honest prose/labels: F-4 relabel, F-5, N-1/N-2(=F-10)/N-3, F-2, F-14, F-15 help.
  - D. D-2 teaching precondition (or a 65 runbook line).
  - Residuals: R-1, F-8, F-9 (exit codes; recommend defer), F-11 (gate false RED, fails loud), F-12, F-13, F-16, §W row 4, the GROUP ALL sweep → 64b.
- **Lead receipt re-run (random pick):** `test_principals_cli.py` + `test_engine_rejection_seam.py` on 5f2d7c43, in background task bn87g2ha2 (held at the 20 GiB gate: an odoo pg restore in another session had 15.7 GiB free).
- **Lead receipt re-run: `test_principals_cli.py` + `test_engine_rejection_seam.py` on 5f2d7c43 → 192 passed, 0 failed** (= the audit's 85 + 107). Admitted at 20.8 GiB, cgroup-capped.
- **OPERATOR RULINGS (2026-09-30 ~03:35Z):**
  - FOLD classes A–D into 63c-i-a BEFORE the commit.
  - F-9 (exit codes): DEFERRED; trigger: the first script or agent flow that needs to retry lore-adm.
  - D-1: routed to packet 64 as finding **#526**; trigger: the next S2 / 65 dress rehearsal through lore-adm.
- am-37 §13 requested from sidecar-63c-2 (30 min).
  - Sequence: §13 → test side (fixup-tests-63c-i-a-2 round 4, or a fresh agent) → `builder-63c-i-a-fix6` → the delta re-check `coldaudit-63c-i-a-5` + `blindreader-63c-i-a-5`.
  - Base: the final patch 5f2d7c43.
- **Correction (lead):** the operator rulings and the am-37 §13 request are timestamped "~03:35Z" above; the true time is **~14:35Z on 2026-09-30** (the operator's answer arrived later; the lead did not re-read the clock). The same wrong stamp is in the annotations on #523/#524/#525.
- Findings: coldaudit-4 had already filed D-3/D-2/D-1 as **#523 / #524 / #525**; the lead's #526 duplicated #525 and is closed as wontfix.
  - #525 carries the packet-64 routing.
  - #523 (class A) and #524 (class D) are annotated FOLDED, to be resolved at the 63c-i-a commit.

## RESUME ANCHOR v9 (2026-09-30 ~14:45Z) — AUTHORITATIVE; supersedes v8
**Operator scope (unchanged):** serial order 63c-i-a → 58 → 64b-i. #486 is PAUSED; its WIP is in the main tree. Not started: #492, #512, holes, test smells, 63c-i-b, 64a, 64b-ii, 64c, 65.

**63c-i-a state: the audited patch is GO; the operator ordered classes A–D FOLDED IN BEFORE the commit.**
- AUDITED FINAL PATCH (GO, coldaudit-63c-i-a-4 `8026854`): `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/e1f81771-6cf2-4679-b6f7-c87b1afe1196/scratchpad/builder-63c-i-a-fix5.full.patch`, md5 `5f2d7c4366d469e5c2a34d53aa235d6e`, 18 files. Lead receipt re-run: 192/0. `apply --check --cached` OK.
- Chain inside it:
  - fix2;
  - the fix-up tests;
  - fix3 r2 (am-37 §8–§10, am-14 entries_for);
  - fixup2 R1 (§11 tests, `85a4d2e1`), R2 (D1 docstrings, `afa519cf`) and R3 (§12 pin, full3 `299467ba`);
  - fix4 (§11 handler, delta `fd70c6e9`);
  - fix5 (§12 four wraps, delta `4e3024e7`).
- **NOW:** sidecar-63c-2 is writing **am-37 §13** (A–D; requested ~14:35Z; watcher `b51y9v4j9`, 50 min). The four classes:
  - A: the lore-adm error line teaches the cause (#523 + blind F-3);
  - B: fail-closed counts/shapes (blind F-1 delete `cascaded`, F-6 `_rows_stamped`, F-7 `_governed_select`);
  - C: honest labels/prose (F-4 relabel, F-5, N-1/N-2/N-3, F-2, F-14, F-15);
  - D: pre-boot schema teaching precondition (#524).
- **NEXT, in order:**
  1. Verify §13 is committed and read it IN FULL.
  2. Test side: resume `fixup-tests-63c-i-a-2` as ROUND 4 (native SendMessage; it is at rest, its context holds the whole test chain). Base = `5f2d7c43`. It delivers an r4 delta + a full4 patch, RED receipts declared-then-diffed, a reference GREEN, and mutation proofs; memory wait-loop ≥20 GiB before EVERY run.
  3. `builder-63c-i-a-fix6` (a fresh spawn; brief shaped like fix4/fix5): the production for A–D on full4. The final patch = its full.
  4. In parallel: `coldaudit-63c-i-a-5` (a delta re-check: §13 by construction + mutations + targeted run + the dirty-store probe for D/A using a NEW `restore_prod_dump.py` restore, since the old dump is reaped; D-1/#525 means loader-swap as in audit-4 §A.2; if the restore or reap is permission-denied → the operator runs it) and `blindreader-63c-i-a-5` (contract-blind, diff 5f2d7c43 → final).
  5. On GO: the lead verifies md5 + one random receipt re-run, then COMMITS.
- **COMMIT MECHANICS (lead-checked):**
  - `cp -a scripts/pending_contracts.yaml` to the scratchpad first. Its working-tree hunk is a stale uncommitted a28c edit inside the `packet-63c-i-a-a28-contract` entry (NOT #486 content), which the patch deletes.
  - `git apply --cached --include=scripts/pending_contract_gate.py --include=scripts/test_pending_contract_gate.py` → commit (i) "gate matcher entries_for"; then `git apply --cached` the rest → commit (ii) "63c-i-a build".
  - Working tree: `git apply --exclude=scripts/pending_contracts.yaml <final>` (every other file applies over the WIP, incl. `test_surreal_harness.py`), then write `git show HEAD:scripts/pending_contracts.yaml` over the working yaml.
  - NEVER `git add` #486's WIP files. No attribution trailers.
  - Then: resolve #523/#524 and #520? (no — #520 resolves at 64b-i); an INDEX Log "63c-i-a CLOSED"; `git mv` every 63c REPORT-*.md to `docs/plans/v2/receipts/2026-09-30-63c-i-a/`; the close-out lists the residuals (below) + F-9 + #525.
- **Residuals to list at close-out:**
  - R-1 (a teardown fault masks the outcome);
  - F-8, F-9 (exit codes, operator-DEFERRED; trigger: the first retrying caller), F-11 (gate unsymboled-count false RED, fails loud), F-12, F-13, F-16;
  - §W row 4;
  - the GROUP ALL sweep → 64b;
  - (c) suite bound; gate `--legs` UX;
  - D-4 → 63c-ii; F-C4 → #34.

**Operator rulings this session (all recorded above):**
- CLAUDE.md TEST SCOPE clarified (`baa313c`).
- #520 part 1 folded into the 64b-i build.
- R2-1 folded (§11), and §12 (4 wraps) rode the fold.
- A–D folded before commit; F-9 deferred; D-1 → packet 64 (#525).

**Findings:**
- #523 (A) and #524 (D) are annotated FOLDED → resolve at the commit.
- #525 → packet 64. #526 is a dup (wontfix). #520 → the 64b-i build.

**Queue after 63c-i-a:**
- **58:** the §RE-BASE step first (the 36 REF-ONLY reds must go GREEN, else STOP); r4 BUILDER CONSTRAINTS; am-13 (3); a cold audit incl. the 7 adversary-58-r3 wrong builds + `translate_targets() == FAULT_CLASS_NAMES` (see anchor v8).
- **64b-i:** the pin pass (F-2, F-3, G2, the #319 leg, F-F, the registry re-key), then the build (F-1, `_refuse_foreign_params` with THREE callers incl. comms per #520, BC-r2-9, `table_defined=`, §DRY incl. the GROUP ALL sweep), then a cold audit + commit.

**Live agents:**
- sidecar-63c-2 (fable, busy on §13);
- sidecar-64 (fable, idle; keep for 58/64b-i);
- fixup-tests-63c-i-a-2 (opus, at rest; reuse for round 4).

All others are stopped.

**Used names (never reuse):**
- adversary-63c-i-a-a28c, adversary-64b-r2, builder-63c-i-a-a28c;
- builder-63c-i-a-fix2, -fix3, -fix4, -fix5;
- fixup-tests-63c-i-a, fixup-tests-63c-i-a-2;
- coldaudit-63c-i-a-3, -4; blindreader-63c-i-a-3, -4;
- contract-58-r4.

Reserved next: builder-63c-i-a-fix6, coldaudit-63c-i-a-5, blindreader-63c-i-a-5.

**Background:**
- `b51y9v4j9`: the §13 watcher.
- `b0nin9fbc`: the prod lore-surreal RSS sampler (24h, `scratchpad/prod_surreal_rss.tsv`).

**Memory note:** host MemAvailable swings 15–30 GiB (odoo pg restores in other sessions). The ≥20 GiB admission gate is a wait-loop, never a bypass.
- **am-37 §13 RULED (`ce2b4bd`, read in full by the lead).**
  - A: `main()` installs a stderr WARNING handler rendering `engine_error`/`error_class` (the hint becomes true), and the §11 line appends the `__cause__` chain. F-13 is FOLDED via A (neutral contexts).
  - B: ONE wrong-shape policy, `governed.rows_of` + `group_all_count`, with an AST allowlist; F-1/F-6/F-7/`_as_rows`/F-5 routed.
  - C: the field and receipt KEY rename to `messages_left_unmigrated`; the derived `--table` help; `report-unmigrated` validated via the one validator before I/O; prose.
  - D: one `INFO FOR TABLE` after the DB gate; columns derived from each leg's UPDATE text; a verb-level teaching refusal; generated REMOVE-FIELD dirty-store pins; coldaudit-4 §7.3 is the acceptance receipt.
- ROUND 4 (the test side of A–D) was sent to fixup-tests-63c-i-a-2 at ~14:50Z (60 min), base 5f2d7c43, new scratch `fixup4`. NEXT: builder-63c-i-a-fix6 on full4.
- **~15:10Z: fixup2 ROUND 4 is BLOCKED on the memory admission gate** (MemAvailable 15.4 GiB for 10+ min). No fleet pytest is live.
  - Held by: another session's odoo harness postgres `ppt-apps15-test-px2g` (idle connections, 2+ GiB each), prod surreal :18500 9.1G, test surreal :18000 5.4G, qdrant 2.8G.
  - Class A pins are written (206 collected); B and D are delegated to 2 sub-workers, C is being authored.
  - The lead did NOT relax the gate. It told the agent to SERIALIZE all worker pytest runs behind one queue, and escalated to the operator (free memory, e.g. stop the idle harness, or wait).
- **~15:15Z: memory is at 14 GiB. The lead EXTENDED fixup2 round 4's deadline** (the blocker is external). It must commit a PARTIAL ROUND 4 (patches + md5s + currency) as soon as B merges, keep the gated serialized queue armed, and fill in the receipts when memory admits. The gate is not relaxed; the operator has been asked (stop the idle harness / wait / lower the floor).
- **fixup2 ROUND 4 PARTIAL (`04a4149`).**
  - All A–D pins are authored; patches: r4 delta `346e746d6fbb3bdd1ca105a47036d59e`, full4 `ff70ecb2e9ef38fb934f22a310bfb11d` (lead-verified; full4 apply-check OK at 04a4149).
  - Currency typecheck 83 unchanged, ruff GREEN, RED_ORPHANED 0.
  - The A+C base run was exact (119/119 declared). The reference and mutation runs are queued, serialized behind one flock, and memory is back at 13.8 GiB.
  - The worker decisions were sent to sidecar-63c-2 as am-37 §13.1:
    - B-D1: FAIL-OPEN — `_table_exists` reads a non-dict INFO as "table absent", so delete skips the SF-63-5 owned-row guard. A third INFO-map helper is proposed.
    - B-D2: `authorize_guarded` coerces a wrong-shaped pre-read → `rows_of`.
    - D-fork: backtick spans.
    - D store facts → docs/reference?
    - D flag: a mutated-SET pin?
  - Process note: sub-b killed flock PID 3797612, believing it was its own waiter. Serialization held (process-table check + a single holder), but it is recorded.
- **am-37 §13.1 RULED (`d6cdd0b`).**
  - B-D1 (a): `governed.map_of` is the THIRD allowlisted shape helper; `_table_exists` (FAIL-OPEN guard) is fixed, the `_agent_migration_preconditions` clone is deleted, and D's INFO FOR TABLE read goes through it.
  - B-D2: `authorize_guarded` routes through `rows_of`.
  - D-fork: one backtick span per column.
  - D store facts go INTO `docs/reference/surrealdb-31-capabilities.md` in this commit, with the probe in the builder report.
  - The one-derivation pin is REQUIRED.
- The test-side edits (round 4b) were sent to fixup-tests-63c-i-a-2 (~15:35Z): allowlist → 3, xfails → plain pins, a delete non-dict-INFO pin, F5 DUAL re-key, the span form, the one-derivation pin; re-cut the patches; the final ROUND 4 replaces the partial.
- NEXT: builder-63c-i-a-fix6 on the final full4 (§13 + §13.1 production + the reference-doc facts).
- **fixup2 ROUND 4 FINAL (`bf1236a`).**
  - §13 A–D + §13.1 test side. 209 declared RED = observed on fix5 (+34 pre-owned 64b-i); GREEN on the combined reference; 5/5 mutations held (M-A2 v2 caught its own blind spot, re-keyed, v3 held); every run serialized through one flock gate.
  - r4 delta `ab711142bf1204cfe7395e4038bc9b88`, full4 `7ab76f3611bedf69eddc4df943cbbc67` (lead-verified; full4 apply-check OK at bf1236a). The delta touches 4 test files only; `_surreal_harness.py` is NOT touched.
- `builder-63c-i-a-fix6` spawned (~16:35Z; 100 min excluding memory-gate waits) on full4: §13 A–D + §13.1 production + the store-reference facts. It is NOT given the throwaway reference patches.
- Then `coldaudit-63c-i-a-5` + `blindreader-63c-i-a-5`. The audit re-runs the dirty-store acceptance for D and A (a NEW restore; #525 loader-swap).
- **The prod lore-surreal RSS sampler finished** (b0nin9fbc: 288 samples, 2026-09-29 17:08Z → 09-30 17:03Z, one PID 87802, no restart).
  - RSS went 5.84 → a plateau of ~8.9–9.6 GiB from ~21:00Z, peaked at 10.84 GiB at 02:53Z, and ended at 4.64 GiB (a 4.50 low at 16:48Z).
  - No monotonic growth; memory is released.
  - Host MemAvailable low: 11.8 GiB at 16:08Z. That pressure is from other sessions' workloads (odoo harness postgres, both surreal stores, qdrant), not from lore pytest.
  - Raw data: `scratchpad/prod_surreal_rss.tsv`.
- **builder-63c-i-a-fix6 DONE-with-deviations (`c8c3435`).**
  - Full `3132f699d5e0330c09efbbc58c0c3d0f` (20 file diffs) and delta `bfd73d83a9f073892c795f73df140f51`, both lead-verified; full apply-check OK at c8c3435.
  - Runs: 0 GREEN→RED; the 209 declared are accounted for (200 R→G, 8 param churn, 1 owned by 58); 268 owned reds + 1 UNOWNED red at base (FLAG-1).
- **Lead triage:**
  - FORK-1 (D gate is leg-first, B) → sidecar §13.2.
  - FORK-2 (`PrincipalKeyStore._as_rows` → `rows_of`, so `verify` raises on a wrong shape) → ACCEPT; the audit checks the served MCP auth result (denied, no leak).
  - FLAG-1 (am34_5 resolver pin red: round 4's D file uses eval+Expression) → round 5 test side.
  - The `_rows_stamped` default `noun` (a production default for a test's arity probe, the F-16 smell) → round 5 rewrites the probe, then the builder removes the default.
  - FLAG-3 (`governed.py` module docstring STUB) → the builder fixes it with the default removal.
  - FLAG-2 (currency `--legs` FAIL line) → the existing residual "gate --legs UX".
  - FLAG-4 (raw newlines in stderr cause lines) → residual; trigger: any MCP-served render of these lines.
- Sent: §13.2 to sidecar-63c-2; ROUND 5 to fixup-tests-63c-i-a-2 (base 3132f699). NEXT: resume builder-63c-i-a-fix6 (FLAG-3 + remove the default) → coldaudit-63c-i-a-5 + blindreader-63c-i-a-5.
- Close-out residual added: the six foreign tolerant `_as_rows` clones (agents, briefs, diff, findings, messages, tasks) → 64b §DRY, with the GROUP ALL sweep (trigger: the 64b §DRY step). Noted: §13 C closed a statement-interpolation path in `report-unmigrated --table` (it is now validated before I/O).
- **am-37 §13.2 RULED (`5f39564`): FORK-1 reading B ACCEPTED.**
  - "Verb-level" means no leg read/write runs before the gate. Serving the verb-level refusal first is harmless by construction, and the §7.3 acceptance holds.
  - Riders:
    - (a) the fix6 resume states the ordering bound in the leg docstring;
    - (b) coldaudit-63c-i-a-5 also runs `--table message` on the PRE-BOOT dump and records both teachings' order (receipts, not defects).
  - The fix6 resume list is now: FLAG-3 (the `governed.py` module docstring), remove the `_rows_stamped` default `noun` (after round 5), and the §13.2 leg-docstring bound.
- **fixup2 ROUND 5 DONE (`7a1dac4`).**
  - The D file's eval resolver is replaced by an ast literal reader; am34_5 is GREEN; targeted 1004/0; the D mutation held.
  - The arity probe goes through `Any` (default removable: typecheck 83 unchanged).
  - r5 delta `5ef35641295e40cc8e143f647fe2784e` (2 test files), lead-verified; it composes over the fix6 full at 7a1dac4.
- `builder-63c-i-a-fix6` RESUMED (~18:05Z, 40 min): apply r5; remove the `_rows_stamped` default; the FLAG-3 module docstring; the §13.2 leg-docstring bound; a targeted run (0 unowned reds); re-cut the FINAL patch. Then coldaudit-63c-i-a-5 + blindreader-63c-i-a-5.
