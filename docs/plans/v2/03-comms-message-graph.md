# 03 — Comms: message graph — THE DURABLE CORE (store + ledger) · formerly PKT-28 phase C2b
size ~0.35 wu (measured; see SPLIT) · wave C · depends: packet 02
law: read `comms-subsystem.md` FIRST + DESIGN-LAW §8/§5/§1 · design source:
~/.claude/plans/one-of-claude-codes-nifty-garden.md · **DEPLOY: NO — test+store only**

## SPLIT (operator-ruled 2026-07-19, on the contract author's measurement)
The contract was written IN FULL and then measured, per operator direction: **296 pins,
0.6–0.8 wu against a 0.25 sizing** — packet 02's miss, caught earlier. Split along the
contract's own pin groups:
- **03 (this file)** — schema/DDL + the `messages.py` ledger + concurrency + the retry-seam
  coverage + the relation-table flip. **TEST-ONLY, NO DEPLOY** (precedent: 02a).
- **03a** (`03a-comms-message-surface.md`) — tool dispatch + renders/promises; **DEPLOYS BOTH**
  and owns the live-wire smoke.
⚠ These numbers are a FLOOR: the contract-adversary had not run when they were measured, and
it reliably adds pins. Re-check before 03a starts.

## Mission
The durable core: store-and-forward messages with per-recipient delivery state, proven at
contention BEFORE any surface depends on them. Nothing user-visible ships here — and that is
the point: the mint, the atomic fan-out, the recipient guard and the write-once CAS all land
where their failure is a test failure, not a production one.

## Scope IN
- Schema slices: `message` node (id `ulid()`, `grade` signal|directive, bodies immutable
  after send — strikeable design choice) + `to` delivery edge (UNIQUE(in,out); write-once
  CAS stamps `seen_at`/`acked_at` — only the recipient stamps its own edges, zero hot-row
  contention).
- `message.seq` minted via native `DEFINE SEQUENCE` + `sequence::nextval("<name>")` —
  probe-settled, operator-confirmed (ledger task f86af162; not gapless, accepted).
- `messages.py` ledger module (tasks.py blueprint): send txn (node + to-edge fan-out;
  `to=[]` ⇒ broadcast **all non-retired** agents; unregistered recipient = teaching error),
  drain (stamps exactly what's rendered; `peek` skips), ack (write-once CAS).
- **`set_status` on `send`** (operator-ruled 2026-07-19, pulled in from the design's tool
  table): a sender may park itself in the same call — the one-call operator question.
- **`ENFORCED` on the `to` edge** (operator-ruled 2026-07-19; probed
  `REPORT-probe-enforced-clause.md`): ship it as
  `DEFINE TABLE OVERWRITE to TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL`.
  It is a BACKSTOP, **not** a replacement for the app-level recipient check — it reports one
  bad recipient per attempt as untyped prose AFTER the write is attempted, it cannot see
  ghosts already stored, and it is the only thing that closes the `INSERT RELATION` door
  (which no app check on `send` can reach).
- **RELATION-TABLE POLICY FLIP** (operator-ruled 2026-07-19, scope EXPANSION): flip
  `_define_relation_table` to `DEFINE TABLE OVERWRITE` and give it real `IN`/`OUT` parameters
  — **it emits neither today**, so `briefed`/`refers`/`answers_to` currently carry NO endpoint
  typing at all. ⚠ `IF NOT EXISTS` is a measured SILENT NO-OP for a changed relation clause
  (#107's shape, invisible to every virgin-DB test). REQUIRED with it: a **pre-flight audit of
  existing rows** (typing a populated edge WRITE-POISONS any row whose endpoint is of a
  forbidden table — `REPORT-audit-edge-preflight.md`) and a **dirty-store migration pin** in
  the §1.6 `TestSchemaMigrationAgainstAnExistingStore` shape: apply OLD DDL → write a row →
  apply NEW DDL → assert the guard is LIVE **and** the old row survived. A virgin-DB fixture
  proves nothing here, by construction.
- **`AgentRefLike` is promoted to ONE shared module both `briefs.py` and `messages.py` import**
  (operator-ruled 2026-07-19, DRY law: duplication is a design decision, never a quiet copy #2).
- Concurrency pins at ≥8-way with SEPARATE ledger instances (N coroutines on one socket do not
  contend); 20-consecutive-green law — note it has NO mechanical enforcement, it is builder
  discipline measured in runs.

## Scope OUT
- Tool dispatch, all renders, promise-registry entries, hostile render fixtures, deploy and
  live-wire smoke → **packet 03a**.
- `blocks` mirroring, fleet columns, `_comms_footer` (packet 04); await/story (05).
- `drain`'s `since=` (packet 05, lead-ruled).

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
Packet 02 deployed; task f86af162 claimed; `comms-subsystem.md` build-time probe list
(the C2 probe is this packet's); spike-surreal up.

## Kickoff rulings (2026-07-19 — operator unless marked LEAD; probes: `REPORT-probe-pkt03-store.md`)
1. **Broadcast (`to=[]`) = ALL NON-RETIRED agents** (active + idle + input_required), never
   `status=='active'` alone. An idle or parked agent silently missing a broadcast is message
   LOSS — the failure this subsystem exists to remove — and a parked agent MUST receive
   messages, since that is how its answer arrives. Precedent: #99 made the same correction to
   the fleet label. Fixtures must include a retired agent (excluded) AND an idle/parked one
   (included), or they cannot discriminate.
2. **#105 (dangling edges) STAYS IN PACKET 04** — deferred deliberately, risk accepted
   (*"we're the only consumer, and we're local"*). Packet 03 still builds its OWN scoped
   `unregistered recipient = teaching error` (already in Scope IN) and routes it through the
   existing `_comms_enrich_unknown_agent` helper rather than minting a second one. Packet 03
   does NOT add #105's structural schema guard. Packet 04's file carries the widened exposure.
3. **Store facts settled by this packet's own probes** (cite reference, do not re-derive):
   `DEFINE SEQUENCE **IF NOT EXISTS**` (a bare DEFINE RAISES → boot crash on re-apply; no
   variant resets the counter; BATCH/START residual = **#146**) · `sequence::nextval("<name>")`
   (`sequence::next` is a PARSE ERROR) · seq gaps are REAL, so `seq` is an ORDERING key, never
   a count or a gapless handle · `UNIQUE(in,out)` on `to` is SAFE (the #7061 cascade hazard is
   settled ABSENT) but makes a duplicate recipient a LOUD ERR → **dedupe before the RELATE
   loop** · `DEFINE TABLE to TYPE RELATION IN message OUT agent` is MANDATORY before first
   write · bind endpoints as `RecordID`, never `str`; `RELATE $m.id->…` is a PARSE ERROR, so
   bind the id into the `LET`.
4. **The CAS stamp's empty return is FOUR-WAY AMBIGUOUS** (already-stamped / no-such-edge /
   not-yours / never-ran-due-to-conflict). Resolve it INSIDE the module — kill the fourth with
   the shared retry driver, disambiguate the rest with a follow-up SELECT, return a TYPED
   outcome. Pin the three survivors SEPARATELY, and scope every stamp by ownership
   (`AND out = $me`) with a NEGATIVE pin: a test that only exercises "already stamped" passes a
   build that silently accepts forged edge ids.
5. **LEAD: all new renders live in `server.py` with the existing `_render_comms*`/`_comms_*`
   prefix.** Three of the five render scanners are hardcoded to that path AND that name prefix
   (**#145**) — a render in `messages.py`, or under another name, is invisible to the promise
   registry and stays GREEN. Following the 19-function precedent keeps every scanner effective.
   The general fix is DESIGN work and does not go to a builder.
6. **LEAD: `drain`'s `since=` (re-reading already-seen history) is DEFERRED to packet 05** — it
   is not named in this packet's Scope IN, and it is closer to `story`. Nothing depends on it yet.
7. **LEAD: a broadcast does NOT deliver to its own sender.** An EXPLICIT self-addressed send
   (`to=[me]`) IS allowed — deliberate self-notes are legitimate and ruling 7 covers broadcast only.
8. **LEAD: the recipient-existence check is pinned at BOTH layers** — the ledger check (a SELECT
   over `agent` before any RELATE, all-or-nothing) is non-negotiable per probe 1; the dispatcher
   check produces the teaching error naming every bad recipient plus the live roster. Defence in
   depth; neither is redundant (`ENFORCED` is a third, engine-level layer — see Scope IN).
9. **LEAD: the WAITING state is DERIVED, never stored — and nothing "un-parks" an agent.**
   RESOLVES a direct contradiction between the approved design (*"drain by a parked agent flips it
   back to active"*) and shipped code (`agents.py:753-759`: `touch` auto-flips ONLY `idle→active`;
   `input_required` never auto-flips). **Both are struck.** An agent is awaiting-input **iff it has
   a question thread with no answer on it** — computed at render time, exactly as `orphaned` is
   already derived from `heartbeat_at` and deliberately excluded from the stored status domain.
   **Why neither original branch survives** (evidence, not preference):
   - *Drain un-parks* clears the signal on NO INFORMATION. When an agent drains and its answer is
     not there, "the answer hasn't come" and "the answer was lost" are the SAME observation — so
     the drain teaches nothing, and clearing on it destroys the one signal that says a debt is
     outstanding. False-unblocked is invisible; false-blocked is visible beside a fresh
     `heartbeat_at`. The asymmetry is the whole argument.
   - *Explicit un-park only* depends on an agent REMEMBERING — and the 4-model consult
     (`REPORT-consult-{sonnet,fable,opus}.md`) is unanimous from the receiving end: an agent has NO
     background attention and does only what is in its current instruction path; a standing
     obligation decays within a few tool calls. A state whose correctness depends on agent
     discipline is not a state, it is a hope.
   - Derivation needs neither. Nothing to remember, nothing to stamp, no lost update.
   ⚠ **Named limitation:** an answer arriving OUT-OF-BAND (an operator replying in a terminal, not
   through `lore_comms`) never lands on the thread, so the derived state stays "waiting" until
   someone relays it in. Accepted and recorded rather than discovered later.
   ⚠ This adds a `question thread` notion to the `agent`/`message` slices — the contract author must
   price it; it is the one ruling here that ADDS pins.

## Exit
Full gates + cold audit + deploy BOTH + smoke: send→drain→ack round-trip on the live
wire incl. a broadcast and a hostile body staying fenced; INDEX row + Log.
