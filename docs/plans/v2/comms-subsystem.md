# comms-subsystem — Agent comms (SurrealDB-backed replacement for Claude Code native agent communication) (formerly PKT-28)
size: multi-session subsystem, phases C0–C5 (not a single-session packet like its siblings —
each phase is its own session) · wave C, resequenced ahead of packet 10 (operator 2026-07-11) ·
depends: PKT-06/C0 first, then each prior phase
law: DESIGN-LAW §8 (orchestration substrate, pull-only — L5 push bus stays rejected; operator's
approval sentence lives here), §5 (hot-row minting — write-once CAS stamps satisfy it), §1
(client render law — context density > call counts, counted elision), §12 (deploy checkpoint) ·
DEPLOY: yes (rebuild+recreate BOTH containers per phase that ships surface)

## Design source
`~/.claude/plans/one-of-claude-codes-nifty-garden.md` — FULL approved design (~567 lines incl.
the SurrealDB 3.1 capability appendix). This packet maps to it, condensed; read the plan for
schema DDL, the full await state machine, and the drill script — never re-transcribe it here.

## Mission
Claude Code's native agent comms lose messages silently by open bug
(anthropics/claude-code#50779: inbox injects only at `stop_reason=end_turn`; SendMessage
returns success unconditionally). Bakes durable store-and-forward **pull** comms into lore on
SurrealDB — new `lore_comms` tool (pin 14→15): registry, message graph with per-recipient
delivery state, versioned briefs with queryable acks, fleet view. Replaces the manual
mitigation stack (front-loaded briefs, brief-base.md, REPORT files, idle-gate). LIVE SELECT is
a contentless wake signal only, never a source of truth.

## Operator rulings (2026-07-11, session C2 — binding)
1. Scope: FULL subsystem (registry + message graph + delivery state + fleet + briefs).
2. New `lore_comms` tool — exact-set pin 14→15, deliberate.
3. `await`: BUILD IT — satisfies PKT-06's "L4 needs an operator ruling" clause.
4. Sequencing: comms next, ahead of packet 10; INDEX Log records the resequence.
5. Graph: lean in — `blocks` dependency edge; delivery + brief acks as stateful RELATE edges.
6. Append-only struck as a requirement — remaining immutability is a strikeable design choice.
7. Roster: Sonnet 5 builders except the C3 await/LIVE leg (Opus 4.8); cold audits Opus 4.8;
   lead Fable writes no code; drill teammates Sonnet 5. **(Lead AMENDED 2026-07-14, operator:
   OPUS leads packets 02–06 — INDEX roster; the lead-writes-no-code law is unchanged.)**
8. SurrealDB 3.1 audit adopted (Opus scout): DEFINE SEQUENCE replaces a hand-rolled counter;
   UNIQUE-on-edge unbanned (≥3.1.0, #7061 fixed); recursive traversal idiom for `blocks`;
   DEFINE EVENT + CHANGEFEED considered-and-deferred.

## Data model (condensed — see plan §"Data model" for DDL)
Schema slices in `surreal_schema.py`, house pattern (`_X_FIELD_SPECS` → `generate_x_ddl()`,
IF NOT EXISTS, SCHEMAFULL).

Nodes: `agent` fleet registry, id `uuid5(session:name)` (idempotent re-register, respawns
never reuse a name), `name`/`session` charset-ASSERTed (injection guard — SDK ignores bound
`$params` in LIVE WHERE, identifiers get inlined). `message` one node per body regardless of
recipient count, `seq` minted via native DEFINE SEQUENCE + `sequence::next()` (not gapless,
accepted), id `ulid()`, `grade` signal|directive; **design choice, strikeable: bodies immutable
after send**. `brief` versioned standing instruction, UNIQUE(name, version), publish = max+1
insert.

Edges (TYPE RELATION SCHEMAFULL — state lives ON the edge): `to` delivery edge
`message->to->agent`, UNIQUE(in,out) (legal ≥3.1.0, #7061 fixed), **write-once CAS stamps**
(`seen_at`/`acked_at`, `UPDATE … WHERE … IS NONE`) — only the recipient stamps its own edges,
zero hot-row contention (§5); "unread" = my unstamped to-edges. `briefed` brief-ack edge
`agent->briefed->brief`, UNIQUE(in,out) idempotent re-ack; "unbriefed" = active agent with no
edge to the head version. `blocks` task DAG `task->blocks->task`, mirrored from
`task.blocked_by` in existing write txns, invariant test pins edge≡blocked_by + acyclicity
(3.1.5 fixed cyclic node-drops); transitive reads use the recursive idiom
(`@.{1..n}->blocks->task`, always TIMEOUT) for critical-path chains and fleet's orphan-impact
line.

Messages-as-pure-edges and semantic-verb edge tables were both considered and rejected — plan
§"Design choices recorded" has the reasoning if this resurfaces.

## Tool surface — `lore_comms` (pin 14 → 15)
New ledger modules cloning the `tasks.py` blueprint: `agents.py`, `messages.py`, `briefs.py`.
Every action carries `agent=` and touches its heartbeat.

| action | purpose |
|---|---|
| `register` | mint/reuse agent row; returns 'project' brief + unread/unacked counts; auto-acks brief |
| `heartbeat` | liveness ping; returns unread count + brief-skew notice |
| `send` | txn: message node + to-edge fan-out (`to=[]` ⇒ broadcast active registry); unregistered recipient = teaching error |
| `drain` | numbered render of my unstamped to-edges; stamps exactly what's rendered (`peek` skips); `ACK REQUIRED` trailer |
| `ack` | write-once CAS stamp of acked_at |
| `await` | snapshot-first bounded wait (drain SELECT → filtered LIVE-on-edge wake w/ poll fallback, ≤55s, honest empty on timeout) — plan §"await semantics" |
| `brief_get`/`brief_publish`/`brief_ack` | read head w/ briefed coverage / publish max+1 / explicit mid-phase ack |
| `fleet` | per-agent status/heartbeat-age/unread/unacked/brief-skew/orphan-impact |
| `story` | task-anchored lineage in one call: created→blocks→claim→messages→brief versions→transitions→report_path |

Nudge footer: `lore_tasks`/`lore_claim_task`/`lore_findings` mutations append one line when
traffic pends (`_comms_footer`). PKT-06 rollup gains messages/fleet/skew sections (built C3).

## Phases (TDD contract-first; lead writes no code; cold REFUTE audit before every phase commit)
**Renumbered 2026-07-14: each remaining phase is its own step packet — this doc is their
shared reference; the step files carry scope/entry/exit and CITE this doc, never re-transcribe it.**
- **C0** — DONE (was PKT-06): rollup, create_many, resolve_many/acknowledge_many, mandatory
  done-summary+report_path. Row f38f3b96.
- **C1** — DONE + DEPLOYED: registry + briefs (agent/brief/briefed slices, agents.py/briefs.py,
  register/heartbeat/brief_*/fleet, all four structural pins updated 14→15).
- **C2a** — **DONE + DEPLOYED 2026-07-19** (`02-comms-render-architecture.md`): #104 step-0
  (STANDING_BRIEF role via ONE accessor, renders take TYPED applicability, `_brief()`
  monoculture default removed) + #103 (heartbeat generalized to subscribed-name skew, three
  name-conditioned §9.4 tails, fleet cell `brief`→`project`) + #100 + #101. Image
  **ae0e78d9a504**, both containers; d3c899f→05a8bb2; cold-audit GO + F1 fixed; live-wire
  smoke PASS. All four findings RESOLVED. Row c2009c94.
- **02a** — **DONE 2026-07-19, TEST-ONLY / no deploy** (`02a-comms-promise-instrument-hardening.md`;
  split off C2a by the operator): §9.7 mechanized as 16 executable emit/no-emit proofs with
  `registered ⟺ proven` a CHECKED invariant, and the `safe_str` residual closed then
  GENERALIZED to deny-by-default (an unknown AST shape FAILS LOUD). a2e9a70→ceac2d0;
  production byte-identical throughout. 3 bounds pinned; #143 ledgered. Row 5807c930.
- **C2b** → `03-comms-message-graph.md` (message/to schema, seq, send/drain/ack).
- **C2c** → `04-comms-blocks-footer.md` (blocks edge, fleet columns, footer, #105).
- **C3** → `05-comms-await-story.md` (await, story, rollup sections, CLI, idle-gate v2).
- **C4** → `06-comms-protocol-drill.md` (brief-base v3, hooks, THE DRILL below).
- **C5** — deferred, no ruling yet: checkpoint/respawn workflow; per-agent auth rides packet 39.

Roster: **OPUS END TO END** — Opus contract authors · OPUS BUILDERS · Opus contract-adversary ·
Opus cold audits · **Opus leads** (operator, 2026-07-14; **Sonnet is RETIRED from the builder
slot** — this line previously read "Sonnet 5 builders on C0–C2/C4" and was stale). Fable =
design sidecar / escalation valve only; INDEX carries the triggers. And the half that binds the
LEAD: **a DESIGN problem never reaches a builder** — a property to INVENT escalates to the
operator or goes to an Opus author who must adversarially attack its own design.

## Build-time probes (run in the phase that first depends on each)
C1 — `sequence::next()` vs `sequence::nextval()` real name + first-boot seeding smoke. C2 —
UNIQUE-on-edge cascade probe (RELATE → delete endpoint → re-RELATE). C3 — RELATE fires
edge-table LIVE (empty-payload-safe by design); re-probe the socket-drop error shape on 3.1.5.

## Entry check
Kickoff-only, before C1: INDEX row + Log line recording the resequence; DESIGN-LAW §8 gets the
operator's clarifying sentence + append-only-struck note; PKT-06 candidates section notes the
L4/ack rulings landed here; commit the scout's capability reference as
`docs/reference/surrealdb-31-capabilities.md` + `lore_remember` pointer; update the stale
UNIQUE-on-edge ban in memory `surreal-31-docs-audit-adjustments.md`. Each phase: read this
packet + the plan sections it names + DESIGN-LAW §8/§5/§1; mint/claim a ledger row.

## Exit
Per phase: `scripts/typecheck.sh` zero errors incl. tests + `ruff check .` clean + scoped
suites green with passed-COUNT in the tail; cold REFUTE audit before commit; deploy = rebuild +
recreate BOTH (never restart) for any phase shipping tool surface; tests at spike-surreal
:18000, NEVER :18500; INDEX row/Log per phase. **C4's live drill is the subsystem's acceptance
gate**: lead + 2 subagents coordinate solely through lore (SendMessage only as contentless
wake-nudge, verified by transcript grep) through register→brief_publish→create_many-with-
blocks→claim→mid-work brief bump+directive→drain shows skew→parked question→kill→orphan
surfaces in fleet→release→`story` reconstructs the arc. Receipts: SELECT dumps of
brief/briefed/message/to-edge state, one rollup + one story render verbatim, zero-content-
SendMessage grep, both REPORT files.

## Honest limits (accepted by design — plan §"Honest limits" has the full list)
Fixes LOSS not LATENCY (an agent calling no tools until end_turn stays unreachable till then).
Protocol discipline is unenforceable server-side — spawn-stub + footer nudges + idle-gate raise
the floor, not a guarantee. Identity is honor-system until packet 39; charset ASSERT is an
injection guard, not auth. Broadcasts don't reach agents registered after the send. LIVE SELECT
on a relation table is unproven in this SDK — spiked in C3 with a documented poll fallback.
