# Task-coordination substrate — assign, reaping, and lifecycle↔liveness reconciliation

**Design doc.** Author: `fable-design-05b` (design sidecar). Date: 2026-08-11.
Grounded @HEAD `299e69a`. **DESIGN ONLY — no production code/tests; contract-adversary + build
come in a later packet.** The operator rules; this doc recommends and decides nothing.

> Provenance: task-side mechanisms verified @HEAD `299e69a` via `lore_get_symbol` / `lore_read` /
> `lore_verify` (cited inline, symbol names not line numbers per brief-base). comms-side
> (§1.3/§1.4) mapped by a read-only research scout, cited to its findings.
> Store law cited, never re-transcribed: `docs/reference/surrealdb-31-capabilities.md`.

---

## PART 1 — THE EXISTING MECHANISMS (verify-don't-assume)

### 1.1 Task lifecycle — states, edges, ownership
- **Six statuses** (`TaskStatus`, `tasks.py:122`): `open`, `claimed`, `in_progress`, `done`,
  `blocked`, `wontfix`. `TASK_STATUSES` is the closed domain; **`TERMINAL_STATUSES = {done, wontfix}`**
  (`tasks.py:142`) — the SAME set that "resolves" a blocker (one source of truth for the state
  machine and the `blocked=` partition).
- **`superseded` is NOT a status.** It is an orthogonal flag: `Task.superseded_by: str | None`
  (`tasks.py`, the `Task` model). Supersession stamps `superseded_by`; it never changes `status`
  (verified — see §1.2 and the #174/#356 note in §2C).
- **11 legal edges** (`LEGAL_TRANSITIONS`, `tasks.py:149`): `claimed→in_progress`,
  `in_progress→done`, `open→blocked`, `claimed→blocked`, `in_progress→blocked`, `blocked→open`,
  `blocked→in_progress`, `open→wontfix`, `claimed→wontfix`, `in_progress→wontfix`,
  `blocked→wontfix`. Consequences that matter for this design:
  - `open→claimed` is reachable **only** through `claim_task`, never `transition`.
  - **The only edge that RELEASES a claim (clears `owner`/`claimed_at`) is `→open`, and it exists
    ONLY from `blocked` (`blocked→open`).** There is **no `claimed→open` or `in_progress→open`
    unclaim edge.** An owner who wants to give a claimed task back must route `claimed→blocked→open`
    or `…→wontfix`. (`TaskLedger.transition` sets `release = (status == open)` and clears
    owner/claimed_at only on that edge.)
  - Terminal statuses (`done`/`wontfix`) have **no out-edges**. A `superseded_by`-stamped row
    **refuses ALL transitions** (`transition` validates `superseded_by` before the edge check).
- **Ownership + the claim CAS** (`TaskLedger.claim_task` + `_claim_fragment`, `tasks.py:1455`/`:1516`):
  a single `BEGIN…COMMIT` guarded compare-and-set —
  `UPDATE … SET owner=$owner, status='claimed', claimed_at=time::now(), updated_at=time::now()
  WHERE status='open' AND owner IS NONE AND superseded_by IS NONE
  AND array::len(array::distinct(blocked_by)) = array::len($resolved_terminal_blockers)`.
  The winner is read back from **`owner` identity alone** ("`owner` is written only by this CAS, so
  it is unforgeable"); a loss writes NOTHING and returns `ClaimResult(claimed=False)`, never an
  exception. **`owner: str | None`** and `claimed_at` are the ownership fields; `updated_at` is
  stamped on claim/transition/supersede — **a TASK-activity signal, NOT the owner's liveness.**

### 1.2 What happens to a claimed/in_progress row when its owner DIES or forgets to close — CONFIRMED: nothing
- A claimed/in_progress row keeps `owner` set, `status` non-terminal, `superseded_by` None. It is
  **invisible to `claim_task`** (the `owner IS NONE` guard fails) and **nothing reconciles it against
  the owner's liveness** — no TTL, no auto-release, no reap verb exists. It sits claimed forever.
- The render confirms the invisibility. `AppContext._render_task_rows` (`server.py:4613`) shows
  `- [<status-marker>] <subject> (id <id>, owner <owner>, blocked_by […])`. A superseded row gets
  `[superseded → <successor>]` (finding #7 — because supersede stamps only `superseded_by`, a bare
  `[open]` hid the chain; this is the ONE liveness-ish marker and it is about *supersession*, not
  owner-death). **A stuck claimed-by-a-dead-agent row is byte-indistinguishable from a live claim:**
  `[claimed]` + `owner <name>`, no staleness signal.

### 1.3 comms agent-liveness — registry, heartbeat, derived STALE, fleet, retirement
> Mapped by a read-only research scout @HEAD `299e69a`. Subsystem: `loremaster/agents.py`
> (`AgentRegistry`), `store/surreal_schema.py` (DDL), `server.py` (`lore_comms` handlers + render),
> `config.py` (threshold).
- **Registry model** (`agents.py`, `Agent` model, `extra="forbid"`): a **plain SCHEMAFULL `agent`
  table** (`AGENT_TABLE`, `surreal_schema.py`), NOT an edge. Row id is
  **`uuid5("lore://agent/{session}/{name}").hex`** (`AgentRegistry._agent_id`) — this is what makes
  re-register idempotent; `(session,name)` uniqueness rides the id. Fields: `id · name · session ·
  role · model? · status(Literal[active|idle|input_required|retired]) · spawned_by? · task_id? ·
  checkpoint? · last_note? · registered_at · heartbeat_at · status_set_at?`. **`heartbeat_at`** is the
  liveness timestamp (touched EVERY action); `status_set_at` (#304) is when the status VALUE last
  changed (not every heartbeat).
- **register/heartbeat** (`AgentRegistry.register`/`touch`; dispatch `server.py`): register is
  idempotent by the uuid5 id; `role`/`spawned_by` write-once, `model`/`task_id` mutable, status
  resets to `active` **unless retired**. EVERY registration-requiring action calls `touch(...)` first;
  only `action=heartbeat` forwards the caller's `status`/`note`. `touch` stamps `heartbeat_at=now`; an
  `idle` agent with no explicit status **auto-flips to `active`**. `AGENT_STATUSES =
  {active,idle,input_required,retired}` with a `LEGAL_AGENT_TRANSITIONS` matrix. (`set_status` on
  `send` is a DIFFERENT thing — it marks a message a question, does NOT change the status row.)
- **DERIVED liveness — ONE threshold, ONE marker.** `DEFAULT_COMMS_STALE_HEARTBEAT_S = 600` (10 min;
  `config.py`, as `CommsConfig.stale_heartbeat_s`). `_comms_fleet` computes
  `heartbeat_age = int((now − heartbeat_at).total_seconds())` (one `now`), and
  `_render_comms_fleet_row` renders `[<status> ⚠ STALE]` **iff `age > stale_after_s`** — never stored.
  **⚠ `"orphaned"` is NOT a rendered marker and there is NO orphaned threshold** — it exists only as a
  REJECTED input value (`touch(status="orphaned")` teaches "derived from heartbeat age, never set") and
  a docstring analogy. The tool-doc phrase "'orphaned'/'STALE' are DERIVED … never legal here" is about
  the *input-rejection* contract; in the actual render **only STALE materialises, at >600s.**
- **fleet render** (`_comms_fleet` → `_render_comms_fleet_row`): `- {name} [{status}(+⚠ STALE)] hb
  {age} · role … · model … · task {task_id[:8]}… · {brief} · note: …`. It DOES render the agent's
  self-declared **`task_id`** (truncated, via `render_attributed` — #348, unconstrained free text).
  True counts come from `roster().status_counts` (row-unlimited), not the display-capped window
  (cap 200).
- **retirement**: `touch(status="retired")` — legal from active/idle/input_required, **terminal** (no
  out-edges; register/touch on a retired row → `RetiredAgentError`; respawns MUST use a fresh name).
  **Fleet shows retired agents ONLY as a `+K retired` count, never a row.**
- **store-law facts** (designer-relevant): SCHEMAFULL, `DEFINE FIELD OVERWRITE`; `heartbeat_at` is a
  required `datetime`; `status_set_at`/`model`/`task_id`/`last_note` are `option<…>` (#304 — a new
  field on the production-populated table MUST be `option<>`); `status` carries an `ASSERT $value IN
  [...]`; first register is `CREATE … CONTENT`, re-register/touch are `UPDATE … SET`; the session
  filter binds as **`$flt_session`, never `$session`** (protected name). Two non-unique indexes:
  `(session,status)` and **`name` alone** (← supports owner→registry name lookup, §2B).

### 1.4 THE SEAM — reconciliation between task ownership and agent liveness: CONFIRMED NONE
- **Task side (verified):** `query`/`_render_task_rows` render `owner <name>` and the `[status]`
  marker but **never** the owner's liveness. A claimed row whose owner is retired/STALE renders
  exactly like a fresh live claim.
- **comms side (scout-confirmed):** `agents.py` has ZERO task-ownership references (every
  `TaskLedger`/`owner`/`claim` mention is a docstring analogy). **`register(task_id=…)` stores it
  VERBATIM with no validation and no claim** — `agent.task_id` is a display label, not a foreign key.
  `_comms_fleet` never reads the task table. The ONE comms handler that reads the task ledger is
  `_comms_story` (task-anchored: `get_task(anchor)`, renders `task.owner`), but it never cross-checks
  `task.owner` against a registry row, nor validates `agent.task_id` against a real task. **No join
  exists between `agent.task_id` and `task.owner`.**
- **Verdict:** the two ledgers are **fully decoupled.** `query` shows a stuck owner with no staleness;
  `fleet` shows the agent's *self-declared* `task_id` (unvalidated, and the WRONG direction — it is
  agent→task self-report, not task.owner→liveness) and a `STALE`/`retired` state with no indication it
  holds a stuck task. This absent seam is the root of the reaping gap (§2B) and compounds #262 (§2A).

---

## PART 2 — THE DESIGN

### (A) ASSIGN — the root of #262

**The problem.** There is no way to DIRECT a row to a named agent — only first-come `claim_task`.
So a lead who wants agent X to do task T reaches for **claim-to-reserve**, which is self-defeating:
the claim CAS sets `owner` (to the lead, or to X-before-X-has-taken-it), and a claimed row can no
longer be claimed (the `owner IS NONE` guard fails). #262's measured instance: the lead held T
(`owner=lead-pkt04b`, driven to `in_progress`); the intended agent's `lore_claim_task` then failed
"already held by lead-pkt04b", while `register(task_id=T)` had cheerfully accepted the association —
**two surfaces disagreeing, only one saying so.**

**The design — an `assignee` field DISTINCT from `owner`, plus an `assign` verb.**
- **`assignee: option<string>`** — a NEW task field naming the *intended* agent, set by an
  assigner (lead), advisory, **orthogonal to `owner`.** `owner` stays **claim-only** (the CAS's
  unforgeable invariant — conflating "reserve" into `owner` is exactly #262's mistake; do not
  pollute it). Store law: a new field on a populated table is **`option<>`** and uses
  **`DEFINE FIELD OVERWRITE`** (`surrealdb-…-capabilities.md` §1.1 + §1.4 — a required field poisons
  every existing row and a `DEFAULT` does NOT rescue it; #107/#131's lesson).
- **`assign(task_id, assignee, assigner)`** — sets `assignee` via the guarded THROW-on-zero-rows CAS
  shell already used by `_transition_fragment`/`_claim_fragment` (ONE IMPLEMENTATION — reuse the
  shell, don't clone; §2 store law: a silent UPDATE no-op is the enemy, so THROW on zero rows).
  Legal on an **unowned** row (`open`/`blocked`); **refuse-and-teach** on a claimed/in_progress/
  terminal/superseded row ("task is `<status>`/owned by X — cannot assign"). Re-assign on an
  already-assigned open row is fine (advisory).
- **The `assign` verb REMOVES the reason leads pre-claim.** The lead ASSIGNS T (`assignee=agent`,
  `owner` still None, T stays `open` and claimable); the intended agent CLAIMS T normally
  (`owner=agent`). The #262 stranding cannot arise because the lead never claims T.

**The #262 register-notice WORDING fork — resolved (this is what 05b's #262 fix is held on).**
Two readings of `register.task_id` ("the fleet task id this agent is currently working"):
- **Reading 1 — ADVISORY ASSOCIATION (RECOMMENDED).** `register.task_id` is a display association,
  not a claim. A helper may legitimately be associated with an owner's task. So register should
  **never refuse** (it must stay idempotent + cheap) but must **DISCLOSE** on a mismatch — the same
  honest-notice shape `heartbeat` already uses for brief-skew:
  *"note: task X is held by lead-pkt04b (in_progress); registering the association anyway."*
- **Reading 2 — OWNERSHIP a lead should not pre-hold.** `register.task_id` implies the agent
  owns/claims T, so accepting a held T is a misassignment and the notice should imply something is
  wrong.
- **Recommendation: Reading 1.** It keeps register cheap/idempotent, admits the legitimate helper
  case, and — crucially — the **`assign` verb makes the underlying workflow correct** (leads assign,
  agents claim), so the residual register case is genuinely just an association worth disclosing, not
  a misassignment to police. Pair it with the protocol rule **"leads never CLAIM rows destined for
  agents — they ASSIGN them,"** which is now *meaningful* because `assign` exists.

**05b's #262 fix (the piece it is held on): ship the Reading-1 honest notice** — resolve
`register.task_id` against the task ledger during register and disclose the mismatch: **held by a
different agent** → "note: task X is held by Y (status); registering the association anyway";
**names no task** → "note: task X not found; registering the association anyway." Disclose, never
refuse (register stays cheap/idempotent). ⚠ Note this is the FIRST comms→task read in the register
path (today register touches only the `agent` table; only `_comms_story` reads the task ledger, §1.4)
— so 05b's #262 fix is the **minimal first instance of the reconciliation seam**, and the full
reconciliation (§2B) is the coordination packet. This is a register read + a notice line, the size
05b already owns; the **`assign` verb/field is NOT 05b** (new field + new verb + DDL — see Packet
homes).

**Pins a contract author must cover (A):** `owner` is still written ONLY by the claim CAS (assign
never touches it — mutation-prove they are separate fields); `assign` refuses-and-teaches on an
owned/terminal/superseded row (discriminating fixtures per status); `assignee` is `option<>` and a
legacy row with no `assignee` reads cleanly (§1.4 / `SELECT *` omits a NONE column → `.get`); the
register disclosure fires iff the resolved task's holder ≠ the registering agent (discriminating
pair: self-held → no notice, other-held → notice, unheld → no notice); the assign path and the
register-resolve path route through the shared row-existence policy (`reject_unknown_rows`), not a
clone.

**Fork left for the operator (A):** `assign` ENFORCEMENT — **soft/advisory** (RECOMMENDED: claim CAS
unchanged; anyone may claim an assigned-open row; a non-assignee claim is DISCLOSED, not refused —
the trust-consistent choice) vs **hard/reserved** (claim CAS gains `AND (assignee IS NONE OR
assignee = $owner)` so only the assignee may claim). Hard-assign is rejected as the default because
it *manufactures a new strand*: an assigned row whose assignee never appears becomes unclaimable by
anyone — the forgot-to-claim failure mode made worse.

### (B) REAPING / lifecycle — reconcile stuck rows against owner liveness

Two failure modes, both currently invisible (§1.2/§1.4):
- **forgot-to-claim** (work done with no ownership record): the row stays `open`/unclaimed. **`assign`
  makes this a FIRST-CLASS VISIBLE STATE** — `assignee` set, `owner` None, assigned-long-ago =
  "assigned to X, never picked up." No reap needed (still claimable); the surface just nudges X.
- **forgot-to-close / died** (stuck `claimed`/`in_progress` forever): owner set, non-terminal,
  not superseded. **The common one.** Needs the liveness reconciliation below.

**The surface (the missing seam, built minimally).** A **task-anchored** `query`/`rollup` enrichment
that, for each OWNED task, resolves `owner → registry` and renders the owner's **last-seen age +
derived state: `active`/`idle`/`⚠ STALE`(>600s)/`retired`** — REUSING the comms derivation: the
`age > CommsConfig.stale_heartbeat_s` predicate currently inlined in `_render_comms_fleet_row`
(§1.3). **Extract that predicate to ONE shared home and call it; do NOT clone the 600s constant** —
prove sharing by mutation (perturb `stale_heartbeat_s` → the fleet pin AND the task-surface pin both
move). There is **no "orphaned" state to render** (§1.3) — the derived set is exactly `{active, idle,
STALE, retired}`. This is two plain-table reads (`task` + `agent`), **not a graph traversal** (§4
store law: a traversal never uses a secondary index; read plain tables). Trust (Consumer Law): if the
owner cannot be resolved in the registry, render *"owner X — not found in registry"*, never a false
"alive" — a false clear on a dead owner is the fatal case. (Task-anchored, not fleet-anchored, because
the fleet's existing `task_id` column is the agent's unvalidated self-report in the wrong direction,
§1.4.)

**The auto-release policy — OPERATOR FORK, with a recommendation.**
- (i) **never auto-release** — surface + a manual `reap` verb only;
- (ii) **auto-release on `retired` only** — an explicit, unambiguous terminal agent state;
- (iii) **auto-release on derived STALE** — **REJECTED**: STALE ≠ dead, and the 600s threshold makes
  this concrete. The benign "waiting-on-own-wake" mode (an agent backgrounding a long gate run — a
  full `pytest` can exceed 10 min — and idling until its watcher fires) does NOT touch `heartbeat_at`
  while it waits, so it renders `⚠ STALE` at 600s though it is perfectly healthy (CLAUDE.md,
  validated). Auto-releasing it YANKS live work — the false positive that trains the fleet to switch
  the reaper off ("a gate that fires on honest work gets switched off").
- **Recommendation: (i)+(ii)** — always surface; a **manual `reap` verb** for the STALE case;
  auto-release ONLY on explicit `retired`. Never auto-release on derived STALE.

**The `reap` verb.** `reap(task_id, actor)` releases a stuck row to `open`, clearing
`owner`/`claimed_at` and appending a reap event. It REUSES the guarded-CAS shell
(`_transition_fragment`/`_claim_fragment`), **guarded on `WHERE owner = $expected_owner AND status IN
(claimed, in_progress, blocked)`** so it can NEVER reap a row whose owner already changed (the agent
came back and advanced it, or someone re-claimed) — a THROW-on-zero-rows CAS, never a silent no-op.
**Fork:** a dedicated `reap` verb (RECOMMENDED — semantically distinct forced release, provenance
names the reaper, keeps the normal state machine's "no unclaim edge" property intact) vs adding
`claimed→open`/`in_progress→open` to `LEGAL_TRANSITIONS` (a general unclaim edge — broader blast
radius on the state machine).

**Modelling wrinkle to flag (owner→registry resolution).** `owner` is a caller-supplied bare string
(`claim_task(task_id, owner)`; #262's was `"lead-pkt04b"`). The registry id is
`uuid5("lore://agent/{session}/{name}")` — keyed on the `(session, name)` PAIR — and the registry has
a **non-unique `name`-alone index** (§1.3), so a by-name lookup is supported but may return several
rows (same name across sessions). So reconciling `owner → registry` is **best-effort by name** and may
be ambiguous. **Fork:** (a) reconcile via the `name` index, DISCLOSING ambiguity ("N registry rows
match owner X — most-recent heartbeat shown") vs (b) tighten `claim_task` to record the claimant's
registry-resolvable identity (`session`+`name`, or the uuid5 id, so the join is exact). Recommend
(a) for the first cut (no claim-path change) with (b) as the named re-open trigger (the first
workflow that needs an unambiguous join).

**Pins a contract author must cover (B):** the liveness enrichment calls the SHARED STALE derivation
(mutate the threshold → the task-surface pin AND the fleet pin both move); an unresolvable owner
renders "not found", never "alive" (trust discriminator); `reap` is owner-guarded (a reap whose
`expected_owner` ≠ the row's current owner THROWs / no-ops-loudly — discriminating fixture: owner
changed between surface-read and reap → refused, nothing released); `reap` clears owner/claimed_at
and lands the row `open`+claimable (round-trip pin); auto-release (if adopted) fires ONLY on
`retired`, never STALE (discriminating pair).

### (C) #356 — superseding a blocker strands its dependents

**Grounded restatement (correcting the finding's mechanism phrasing).** #356 says "supersede sets the
superseded task's status to `superseded`." **There is no `superseded` status** (§1.1). The real,
verified mechanism: `_supersede_fragment` stamps only `superseded_by`/`updated_at`/provenance and
**leaves `status` unchanged** — typically non-terminal (`open`/`claimed`/`in_progress`/`blocked`).
`TaskLedger._is_blocked` (`tasks.py:2564`) resolves a blocker iff its **`status ∈ {done, wontfix}`**
and **ignores `superseded_by` entirely.** So a task Y blocked_by X, where X is superseded (→ X') and
X's status is non-terminal, has `_is_blocked(Y) == True` **forever** — Y is unclaimable and nothing
says why. (The claim CAS agrees: its `resolved-blockers` count uses the same terminal set.)

**Does the lifecycle/reaping design subsume it? NO — recommend a SEPARATE fix.** #356 is a
**supersede ↔ blocks-DAG reconciliation** defect (a stale BLOCKER pointer), whereas §2B is an
**ownership ↔ liveness reconciliation** (a stale OWNER pointer). Same shape ("a pointer to something
no longer in the expected state") but different domains and machinery. #356's home is with **#174**
— the two are the same root ("supersede was built as an editorial reframe and never reconciled with
the 04b-1 blocks-edge/reachability machinery," #356's own words): #174 = the superseded task's OWN
`blocked_by` dropped; #356 = the OTHER DAG direction, tasks blocked_BY it.

**Recommended fix shape (design territory — operator rules; candidate shapes, one rejected):**
- **(a) dependent-rewire on supersede** — on `X → X'`, find X's dependents and rewire each
  `Y.blocked_by [X→X']` transactionally. **Mechanically feasible:** `TaskLedger.direct_dependents`
  (`tasks.py:1384`, `blocked_by CONTAINS $id`) already finds them; the rewire reuses `_relate_fragment`
  (re-mirror the `blocks` edge onto X') and `_refuse_a_cycle` (the rewire can close a cycle — must
  re-check). Semantically correct (the work continues in X') but a bigger transaction touching N
  dependents.
- **(b) refuse-and-teach if X has dependents** — supersede REFUSES loudly ("task X has dependents
  [Y,Z]; rewire them first"), so the strand can never be silent. Cheap, safe; changes supersede
  semantics for a currently-"working" flow.
- **(c) treat `superseded` as terminal in `_is_blocked`** — **REJECTED**: X' may be unfinished, so
  this would PREMATURELY UNBLOCK Y.
- **Recommendation: (b) as the immediate FLOOR** (rides #174's verb pass — cheap, makes the strand
  impossible-and-loud), with **(a) as the eventual richer capability** if superseding depended-on
  tasks becomes routine. **Not** subsumed by §2B; fix it in the supersede/#174 unit.

---

## PACKET HOMES (recommended)
- **05b (now):** the #262 register-notice — Reading-1 advisory-association honest disclosure. Small,
  register-wording only; the piece 05b's #262 fix is held on.
- **NEW coordination packet (substantial; own contract→adversary→build):** the `assign` verb +
  `assignee` field (DDL) + the ownership↔liveness reconciliation surface (`query`/`fleet` enrichment
  reusing the STALE derivation) + the `reap` verb + the auto-reap-on-`retired` policy.
- **#174 verb pass (05b's verb half or a dedicated blocks-consistency pass):** + **#356 refuse-and-
  teach floor** rides here (supersede ↔ blocks-DAG reconciliation). #356 dependent-rewire = a later
  richer capability.
- **Packet 28a:** the report-graph (#163 ⊃ #160) — **named only, not designed here** (next section).

## THE REPORT-GRAPH SEAM — NAMED, NOT DESIGNED (→ packet 28a)
A `report` node (28a Deliverable 2's document-graph, #163 ⊃ #160) **edged `report→task` and
`report→agent`** would make close-out inconsistencies DETECTABLE — a `done` task whose `report_path`
names a report that never landed/archived; an agent that filed reports but left tasks stuck-claimed.
That reconciliation is the **report-graph's territory (packet 28a)**, not this design's. The
ownership↔liveness seam in §2B is the minimal precursor that needs no doc-graph. **Recommend it stays
28a**; do not pull it forward. (Store law §4 governs any such edge: bound-RecordID endpoints,
`OVERWRITE` + typed `IN`/`OUT` + `ENFORCED`, dangling-edge hazard #105.)

## STORE-LAW + ONE-IMPLEMENTATION COMPLIANCE (summary)
- **`assignee` field:** `DEFINE FIELD OVERWRITE assignee ON task TYPE option<string>` — §1.1
  (`OVERWRITE` for fields) + §1.4 (new field on a populated table MUST be `option<>`; a `DEFAULT`
  does not rescue existing rows). A migration pin (old DDL → row → new DDL → row survives + new field
  reads None) per §1.6.
- **`assign`/`reap` writes:** REUSE the guarded THROW-on-zero-rows CAS shell
  (`_transition_fragment`/`_claim_fragment`) — §2 (a silent UPDATE no-op is the enemy). **No new
  EDGE for assign/reap** — a FIELD suffices, and §4's dangling-edge hazard argues against a RELATE
  when a field does the job (same logic as the annotate-vs-edge call).
- **Liveness reconciliation:** two plain-table SELECTs (`task` + `agent`), NOT a graph traversal
  (§4). REUSE the comms STALE derivation (`age > CommsConfig.stale_heartbeat_s`, extracted from
  `_render_comms_fleet_row`) — call it, never clone the 600s threshold; prove sharing by mutation.
  There is no "orphaned" render to reuse (§1.3).
- **#356 rewire (if adopted):** REUSE `direct_dependents` + `_relate_fragment` + `_refuse_a_cycle` —
  no new blocks-DAG machinery.

## FORKS FOR THE OPERATOR (consolidated)
1. **#262 `register.task_id` wording** — advisory-association (RECOMMENDED) vs ownership-implied.
   *Blocks 05b's #262 fix.*
2. **`assign` enforcement** — soft/advisory (RECOMMENDED) vs hard/reserved claim guard.
3. **`owner → registry` resolution** — best-effort name-match with disclosed ambiguity (RECOMMENDED
   first cut) vs tighten `claim_task` to record a registry-resolvable identity (named re-open trigger).
4. **Auto-release policy** — surface + manual `reap` only, plus auto-release ONLY on `retired`
   (RECOMMENDED) vs auto-release on derived STALE (REJECTED).
5. **#356 fix** — refuse-and-teach FLOOR (RECOMMENDED) vs dependent-rewire (richer, later) vs
   treat-superseded-terminal (REJECTED); and whether it rides #174 or a dedicated blocks-consistency
   pass.
6. **`reap` mechanism** — dedicated owner-guarded verb (RECOMMENDED) vs adding unclaim edges to
   `LEGAL_TRANSITIONS`.

---

## ADDENDUM (operator-directed, 2026-08-11) — two refinements to the #174/#262 fixes
> Grounded @HEAD **`c0071cd`** (2 commits past this doc's `299e69a` base: **#256 annotate** and
> **#149 idle-gate v2 have since LANDED** — my Q1/Q2 designs were built). Refines §2C (#356) and
> §2A (#262).

### A-174 — RE-ANCHOR-WITH-NOTE vs the refuse-and-teach floor (#356)
The operator's alternative to §2C's refuse-and-teach floor: on `supersede(X→X')`, **RE-ANCHOR each
dependent Y** (`blocked_by` contains X) to `blocked_by X'`, **and APPEND a provenance NOTE on each
rewired Y** recording the re-anchor (X→X', because X was superseded). This is §2C option (a)
(dependent-rewire) + a provenance audit-note.

**Recommendation: RE-ANCHOR-WITH-NOTE is the SUPERIOR fix — it is what the operator wants and what the
domain means** (the work moved to X'; dependents should follow it, not die on a superseded X). It
**actually fixes** the strand; refuse-and-teach only prevents it silently-becoming-silent while
**blocking a currently-working flow** (you could no longer supersede any depended-on task). Keep
refuse-and-teach only as an **interim floor IF re-anchor is deferred** — the two are alternatives, not
both; shipping re-anchor makes refuse-and-teach unnecessary (the strand cannot occur).

- **Feasibility + exact reuse seams (all verified @HEAD):** `direct_dependents(X)` (`tasks.py:1384`)
  finds every Y; for each Y, rewire `blocked_by` (replace X→X' in the array) + re-mirror the blocks edge
  (**DELETE** Y's `blocker=X` edge, **RELATE** `X'->blocks->Y` via `_relate_fragment`); run
  **`_refuse_a_cycle`** over the rewired graph because a rewire **can CLOSE a cycle** (if X' is
  transitively blocked_by Y, then Y→X'→…→Y) — refuse-and-roll-back if so.
- **Atomicity (load-bearing):** stamp-X-superseded + CREATE-X' + rewire-all-N-dependents + N notes ride
  **ONE `BEGIN…COMMIT`** — a partial rewire that strands SOME dependents is worse than none. ⚠ **Txn size
  scales with dependent count** (~1 + ~3N statements): a *hub* task with many dependents superseded is a
  large transaction (contention/timeout). Named bound + fork: bound/batch the rewire vs accept it
  (dependents are usually few). Skipping already-terminal dependents (a done Y ignores its `blocked_by`)
  is a legal minor optimization.
- **THE NOTE MECHANISM — tasks DO have the append target, and there is a ONE-IMPLEMENTATION decision.**
  The task side already appends to `provenance.events` server-side (`_supersede_fragment` /
  `_transition_fragment` both do `provenance.events += [$event]`), so a per-dependent note event
  `{actor, action:"dependency_reanchored", from:X, to:X', at}` is fully store-idiomatic. **BUT:** the
  guarded-append shell is **NOT shared** the way findings' now is. Verified @HEAD: **findings extracted
  `FindingLedger._guarded_append_fragment`** (`findings.py:1116`, optional `status_target`/`expected_from`
  — `_transition_fragment` + `annotate` route through it, #256's ONE-IMPLEMENTATION mission), while the
  **task side hand-rolls THREE** (`_transition_fragment` `tasks.py:1711`, `_supersede_fragment`
  `tasks.py:1965`, `_claim_fragment`), and **`lorerunes` holds no store shell.** So:
  - **The re-anchor MUST NOT hand-roll a fourth clone.** Extract a **task-side `_guarded_append_fragment`**
    (mirroring findings') that `_transition_fragment`, the supersede stamp, and the new re-anchor all
    route through — prove-by-mutation (perturb the shared append clause → transition + re-anchor pins
    both redden). Do this WITHIN #356's blast radius.
  - **The cross-module unification** (findings + tasks share ONE guarded-append) is a genuine DRY trigger
    (the policy — *server-side append + THROW-on-zero-rows, no silent no-op, no clobber* — now provably
    lives in 2 modules) but is a SEPARATE, bigger decision. ⚠ **Likely home is `loremaster.store`, NOT
    `lorerunes`** — the shell is a SurrealQL-`TxnFragment` builder (references table names, `store._txn`
    types), whereas `lorerunes` is stdlib-only and holds PREDICATES, not store-SQL builders (CLAUDE.md
    lorerunes §0). **Escalate this as its own DRY item; do NOT bolt the cross-module lift onto #356.**
- **SCOPE — bigger than #174's verb pass; its own item.** #174 (the *successor's* `blocked_by`
  inherit/override) is cheap and stays in the verb pass. Re-anchor-with-note (the *dependents'*
  `blocked_by`) is a multi-row atomic rewire + cycle re-check + per-row notes + a guarded-append
  extraction — **it warrants its own contract → adversary → build cycle.** Recommend: land #174 in the
  verb pass now; do **#356 re-anchor-with-note as its own item** (riding with #174 only if that pass has
  room), NOT a #174 drive-by (the design-problem-reaching-a-builder rule).

### A-262 — the LIVENESS-ENRICHED register notice (fork 1 ruled Reading 1)
Reading 1 (advisory-association, disclose-not-refuse) is ruled. The operator adds: per Consumer Law the
consumer is an AGENT, so the notice must not just NAME the holder — it must give an ACTIONABLE picture
(a LIVE conflict vs a STALE/retired/dead holder). So `register` resolves BOTH ledgers and renders the
holder's liveness.

**The minimal notice (recommended shape):**
1. Resolve `task_id` against the TASK ledger (`self.task_ledger.get_task` — the seam `_comms_story`
   already uses; no new plumbing) → the task's `owner` Y + status.
2. If Y ≠ the registering agent and Y is not None: resolve Y against the AGENT registry (by the
   non-unique `name` index; most-recent-heartbeat wins on ambiguity — inherits §2B fork 3) → Y's status +
   `heartbeat_at` → derive liveness with the **SHARED STALE predicate** (`age > stale_heartbeat_s`; §1.3).
3. Render, e.g.:
   - live: `note: task X is held by Y (in_progress; active) — registering the association anyway.`
   - degraded: `note: task X is held by Y (in_progress; ⚠ STALE, last seen 21m ago) — registering the association anyway.`
   - retired: `note: task X is held by Y (in_progress; retired) — registering the association anyway.`
   - **unresolvable holder (TRUST): `note: task X is held by Y (in_progress; Y not found in registry) — registering the association anyway.`** NEVER a false "alive."
   - no such task: `note: task X not found — registering the association anyway.`
   Never refuse (Reading 1).
- **SCOPE BOUND — #262 builds ONLY the notice-enrichment.** A single-row `get_task` + a single-row
  registry resolve + the shared STALE predicate + the render, IN the register path. It does **NOT** build
  the query/fleet liveness enrichment, the `reap` verb, the `assign` verb/field, or the auto-release
  policy — those are the coordination packet (§2A/§2B). #262 is the **first, minimal instance of the
  owner→registry reconciliation seam**; the coordination packet generalizes it.
- **ONE-IMPLEMENTATION — #262 forces the STALE-predicate extraction (2nd consumer).** The `age >
  stale_heartbeat_s` predicate is inline in `_render_comms_fleet_row` today (§1.3) — not callable. #262 is
  the FIRST new consumer, so #262 **extracts it to one shared home** and the fleet render + (later) the
  coordination query-enrichment all route through it. Prove-by-mutation (perturb the 600s constant → the
  fleet pin AND the register-notice pin both move). Do NOT clone the constant.
