# 57 — Task-coordination substrate: `assign`, task-release `reap`, ownership↔liveness surface
size ~0.25 wu (→split at kickoff if the forks price it ≥0.30) · wave C/L · depends: 05b (✅ DONE),
**and 63c CLOSED** (contract may not start before — see Entry check) · DEPLOY: rides the next joint
image (packet 65 cutover) unless the operator rules a standalone recreate
lead: Opus + **design author who ATTACKS ITS OWN DESIGN, or the Fable design sidecar**
FIRST READ (store law — MANDATORY): `docs/reference/surrealdb-31-capabilities.md` (§1.1/§1.4 new
`option<>` field on a populated table; §2 THROW-on-zero-rows CAS; §4 plain-table reads, no traversal)
Design of record: `docs/plans/v2/design/2026-08-11-task-coordination-substrate.md` Part 1–2 + FORKS
(Addendum A-262 is DONE in 05b; Addendum A-174 is packet 58, not this one)
Governance read: `docs/design/2026-09-13-packet63c-remainder-ruling.md` §0 (Q1 visible set) + §2.3
⚠ **DESIGN PACKET under roster law** — the ownership↔liveness surface and the `reap` semantics are
properties to INVENT, not specs to implement. It never reaches a builder as "work out the general form".
Forks 2 / 3 / 4 / 6 (design doc § FORKS) are ruled by the operator AT KICKOFF, plus the new forks below.

**Provenance:** minted 2026-08-11 at 05b close-out (operator ruling). Findings re-routed here by the
plan review of 2026-09-24 (#352 #357 #363 #372 #412 — each `acknowledged` with a `→ packet 57` note).

## Mission
Leads ASSIGN, agents CLAIM (dissolves #262's root); a claimed row whose owner is dead is VISIBLE as
such on a task-anchored read; a stuck row can be RELEASED by an owner-guarded verb; auto-release fires
on explicit `retired` ONLY, never on a derived liveness verdict.

## What exists today (read 2026-09-24 at `d237ad7` — cite symbols, not lines)
- `loremaster/loremaster/tasks.py`: six statuses (`TaskStatus`), `TERMINAL_STATUSES = {done, wontfix}`,
  11-edge `LEGAL_TRANSITIONS` — **no `claimed→open` / `in_progress→open` unclaim edge, no out-edge from
  `done`** (the #357 strand). Claim CAS = `TaskLedger._claim_fragment` (guards `status=open AND owner IS
  NONE AND superseded_by IS NONE AND <blockers terminal>`). `TaskLedger._is_blocked` = terminal-only.
  No `assignee` field, no `assign`/`reap` verb (verified: absent from the served `lore_tasks` action list).
- The shared liveness predicate is **`AppContext._heartbeat_is_stale` in `server.py`** (NOT
  `agents.py`), extracted by #262. ⚠ **#360 RETIRED the `⚠ STALE` glyph**: the fleet row now renders an
  `overdue (declared …, silent …)` verdict off the agent's declared `cadence`, and `lore_impact` shows
  ONE production consumer of `_heartbeat_is_stale` today (`_render_holder_liveness_notice`, which gates
  "last seen Nm ago" on it). The design doc's `{active, idle, ⚠ STALE, retired}` render set is
  therefore **stale vocabulary** — see Fork F-A. The overdue predicate's symbol home: UNVERIFIED.
- `agents.py` `AgentRegistry`: `retired` is terminal (`RetiredAgentError` on re-register); retire =
  `lore_comms action=heartbeat status=retired`; there is **no agent hard-delete path** (the #412 premise).
- 63c (in flight at this writing — a peer session holds uncommitted 63c work) governs the `agent`
  table: `owner_principal`/`owner_agent`/`scope` columns, register reading β, and every roster reader
  through the member `read_filter` (ruling §0 Q1 visible set).

## Scope IN
1. **`assign(task_id, assignee, assigner)`** + **`assignee: option<string>`** field, DISTINCT from
   claim-only `owner` (design §2A). `DEFINE FIELD OVERWRITE … option<string>` + a dirty-store
   migration pin (old DDL → row → new DDL → row survives, `assignee` reads None). Reuses the guarded
   THROW-on-zero-rows shell — **after packet 58 extracts the task-side guarded-append shell, route
   through it; if 57 lands first, 57 extracts it and 58 consumes it (one extraction, never two)**.
2. **Task-release verb** (design calls it `reap`): owner-guarded CAS
   `WHERE owner = $expected_owner AND status IN (claimed, in_progress, blocked)` → `open`, clears
   `owner`/`claimed_at`, appends an event naming the releaser. THROWs on zero rows.
3. **Ownership↔liveness surface**: a task-anchored `query`/`rollup` enrichment resolving
   `owner → registry` (two plain-table reads, no traversal) and rendering last-seen age + derived
   liveness through the SHARED predicate(s) — never a cloned threshold; unresolvable owner renders
   "not found in registry", never "alive" (the fatal false clear). **Reads the registry through
   63c's governed `read_filter`** — an owner the caller may not see must render byte-identically to
   one that is absent (63c ruling §0 Q4b: ghost-vs-foreign unrepresentable), and that bound is
   STATED in the render (Leg 1).
4. **Auto-release on `retired` only** (design fork 4 recommendation) — never on overdue/stale.
5. The findings below, each resolved/bounded with a receipt.

## Scope OUT (surface to operator if encountered)
- #356 supersede re-anchor (packet 58). The report-graph seam (packet 28a). The governed retrofit of
  `task` itself (packet 64 — see hazard below). Any change to 63c's agent DDL or read filter.

## FINDINGS OWNED (IN / bound / fork — one line each)
- **#352** — IN: the retire response teaches that retiring the row does NOT stop the process
  (TaskStop). Superseded in substance by #372; resolve both together.
- **#372** — IN: retire result + fleet render teach `TaskStop(<name>)`; codify reap order (TaskStop
  FIRST, then comms-retire) in lead-base — ⚠ lead-base is outside the repo: FLAG the edit to the
  operator, never write it from a packet.
- **#357** — FORK F-C: a guarded `done→in_progress` reopen edge vs a supersede-with-reopen vs the
  protocol rule "phase agents never close the workstream row — the lead does". Not buildable before ruled.
- **#363** — FORK F-B: phantom agent rows. The design's "never auto-act on a derived liveness verdict"
  rule was written for TASK release; #363 asks for AGENT-row auto-retire on TTL. Same principle or not?
- **#412** — ENTRY GATE: decide agent-`reap` = retire-status (no cascade; #412 stays moot) vs
  hard-delete (fires #412's trigger: a cascade-disposition pass over EVERY `record<agent>` link —
  `audit.actor_agent`, `message.sender`, `to`/`briefed` edges — BEFORE building). Recommend
  retire-status; if ruled, add #412's optional assumption-guard pin (reds if an agent hard-delete
  method appears).

## FORKS (questions — operator rules at kickoff; the recommendation is the design doc's unless noted)
- **F-A (NEW) — which liveness does the task surface render?** The design's STALE (600s,
  `_heartbeat_is_stale`) or #360's per-agent `overdue` (declared cadence), or both? #360 retired
  STALE on the fleet for a reason; re-introducing it on the task surface re-opens that argument.
  Rec: render `overdue` when a cadence is declared, else bare age — no verdict glyph (matches #360).
- **F-B (NEW) — the word "reap" means two things.** The design's `reap` RELEASES A TASK ROW; #352/
  #363/#372/#412 use it for retiring/killing an AGENT. Name them apart (e.g. `release` for tasks)
  before the contract, or the served prose teaches a conflation. Rec: split the names.
- **F-C (NEW) — #357 reopen shape** (above).
- Design fork 2 (assign soft vs hard) · 3 (owner→registry name-match with disclosed ambiguity vs
  recording a registry-resolvable claimant — ⚠ under 63c the registry id is session-scoped AND
  governed, which may force (b)) · 4 (auto-release policy) · 6 (dedicated verb vs unclaim edges).

## Hazards
- **File overlap with packet 64** (governed retrofit of tasks + findings: owner+scope on `task`,
  PDP routing). 64 changes the SAME `tasks.py` write paths 57 adds verbs to, and `assign`/release
  are writes 64 must govern. Sequence 57 AFTER 64, or 57's contract carries 64's governance legs;
  the operator rules the order at kickoff. UNVERIFIED: whether 64 has started (INDEX: PLANNED).
- **`owner` is caller-supplied free text** (`claim_task(task_id, owner)`), while 63c makes agent
  identity principal-bound — a name match is not an identity match (design fork 3).

## Entry check (RELATIVE facts only)
1. INDEX row 63 shows 63c CLOSED (both waves), and HEAD contains its close-out commit.
2. `lore_verify AppContext._heartbeat_is_stale` confirmed; `lore_impact` names its consumers (re-derive —
   do not trust this file's "one").
3. `lore_tasks` served action list still has no `assign`/`reap`/`release` action.
4. `lore_findings` #352 #357 #363 #372 #412 not resolved.
5. Premise probe (INDEX protocol, scope-boundary rule): confirm no agent hard-delete path exists
   (`lore_search`/`lore_impact` on `AgentRegistry`) — #412's "moot" rests on it.
6. Suite green at HEAD; `pending_contract_gate.py --currency` 0 RED_ORPHANED.

## Exit
Ruled design doc (forks F-A/F-B/F-C + 2/3/4/6 recorded) → **contract → contract-adversary
(MANDATORY) → build → cold REFUTE audit → commit**. Gates: scoped pytest + full suite ALONE `-n 12`
(never `-n auto`, #466) + `scripts/typecheck.sh` + `uv run ruff check .` +
`uv run python scripts/pending_contract_gate.py --currency` 0 RED_ORPHANED. Required pins: `owner`
written ONLY by the claim CAS (mutation-proven separate from `assignee`); release refused when owner
changed between read and release (discriminating fixture); shared-predicate mutation moves BOTH the
fleet/notice pin AND the task-surface pin; unresolvable AND foreign-scoped owner render identically
and never "alive"; auto-release fires on `retired`, not on overdue (discriminating pair). Findings
resolved with receipts; INDEX row + Log.
