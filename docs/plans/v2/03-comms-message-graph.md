# 03 — Comms: the STORE (schema, relation-table policy, ENFORCED) · formerly PKT-28 phase C2b

> **DONE 2026-07-23. TEST-ONLY, nothing deployed** (the prod-touching relation-table flip against
> the live edge rows lands at 03b's deploy). Commits `df59f76` (schema) → `10d8de4` (receipts) →
> `905b35e` (INDEX); scoped 304/0, blast 432/0; cold-audit **GO**; #146 accepted with a named
> re-open trigger. Receipts: `docs/plans/v2/receipts/2026-07-23-packet03-store/`.
> *(Banner added at 03a-2's close-out — this packet finished without one while its siblings had
> theirs, which made a DONE packet read as open.)*
size ~0.2 wu (measured post-adversary) · wave C · depends: packet 02
law: read `comms-subsystem.md` FIRST + DESIGN-LAW §8/§5/§1 · design source:
~/.claude/plans/one-of-claude-codes-nifty-garden.md · **DEPLOY: NO — test+store only**

## SPLIT — TWICE (operator-ruled 2026-07-19; second cut lead-ruled on the same instrument)
The contract was written IN FULL, then measured, then adversary-graded, then re-measured — each
time by the contract author, never estimated by the lead.

| stage | measurement |
|---|---|
| packet as written | 0.25 wu (before discovery) |
| contract complete | **296 pins · 0.6–0.8 wu** → operator ruled SPLIT (core / surface) |
| + operator rulings folded in | **347 pins · 0.7–0.9 wu** |
| + adversary blockers closed | **400 pins · packet-03-half alone 0.55 wu** |

0.55 is well past the 0.30 split threshold, so the core was cut again along the author's
recommended seam:
- **03 (this file) — the STORE.** Schema/DDL, the relation-table policy flip, `ENFORCED`, all
  three dirty-store migration pins, the guard-kind pin. **47 pins + 1 changed, ≈0.2 wu.**
  Touches ONLY `surreal_schema.py`; no dependency on `messages.py` existing.
  **Why it is its own packet:** it is the ONLY part of this work that changes behaviour for code
  ALREADY IN PRODUCTION — 101,479 live edge rows across `briefed`/`refers`/`answers_to`. That
  deserves its own cold audit rather than riding behind a new module inside a large wave.
- **03a — the LEDGER** (`03a-comms-message-ledger.md`): `messages.py`, the shared `AgentRefLike`
  module, 180 ledger pins. ≈0.35 wu. Depends on this packet.
- **03b — the SURFACE** (`03b-comms-message-surface.md`): dispatch + renders + promises, DEPLOYS
  BOTH. ≈0.3 wu. Depends on 03a.

**The contract is ONE file across all three** — pin groups are labelled, not forked. Selectors are
in `REPORT-contract-pkt03.md` §UPDATE 5eb445b.

⚠ **The `[real]`-tier ledger leg is UNGRADED and is the largest residual risk** (adversary §7.8,
author concurring): neither could close it without building the real store. It is the reason 03 and
03a ship TEST-ONLY with a cold audit each, before 03b deploys anything.

## Mission
The STORE half: every schema change this subsystem needs, including the one that touches tables
already carrying production data. Nothing user-visible ships here, and no new module is written —
`messages.py` is packet 03a. What lands here is the ground the ledger stands on, proven against a
DIRTY store rather than the virgin one every test fixture mints.

## Scope IN
- **Schema slices**: `message` node (id `ulid()`, `grade` signal|directive, `seq`, `question`,
  `asked_at`; bodies immutable after send — strikeable design choice) + the `to` delivery edge
  (`seen_at`/`acked_at`/`ack_note` as `option<>` so `IS NONE` is the CAS guard; UNIQUE(in,out)).
- **`message.seq` via native `DEFINE SEQUENCE IF NOT EXISTS` + `sequence::nextval("<name>")`** —
  probe-settled, operator-confirmed (ledger task f86af162). A bare `DEFINE SEQUENCE` RAISES on
  re-apply → boot crash; no variant resets the counter; the BATCH/START residual is **#146**.
  Gaps are REAL, so `seq` is an ORDERING key — never a count, never a gapless handle.
- **`ENFORCED` on the `to` edge** (operator-ruled; probed `REPORT-probe-enforced-clause.md`):
  `DEFINE TABLE OVERWRITE to TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL`.
  A BACKSTOP, not a replacement for 03a's app-level recipient check — it reports ONE bad recipient
  per attempt as untyped prose AFTER the write is attempted, and cannot see ghosts already stored.
  It IS the only thing that closes the `INSERT RELATION` door, which no app check can reach.
- **RELATION-TABLE POLICY FLIP — the production-touching work, and the reason this is its own
  packet.** `_define_relation_table` moves to `DEFINE TABLE OVERWRITE` and gains real `IN`/`OUT`
  params; **it emits NEITHER today**, so `briefed`/`refers`/`answers_to` carry no endpoint typing
  at all. ⚠ `IF NOT EXISTS` is a MEASURED silent no-op for a changed relation clause (#107's
  shape) — a flip that ships unchanged returns OK, passes every virgin-DB test, and leaves
  production exactly as untyped as today.
- **DIRTY-STORE MIGRATION PINS AGAINST THE TABLES THAT ACTUALLY EXIST.** The §1.6
  `TestSchemaMigrationAgainstAnExistingStore` shape — apply OLD DDL → write a row → apply NEW DDL
  → assert the guard is LIVE **and** the old row survived — parametrized over
  `briefed`/`refers`/`answers_to`, each starting from a BASELINE proving it really was untyped.
  Plus the narrowing's documented hazard: a heterogeneous row is **write-poisoned, readable, never
  dropped**, with a homogeneous CONTROL (the adversary's own first probe failed on both arms for
  two different reasons — attribution is unsound without it).
  **Pre-flight audit is DONE** (`REPORT-audit-edge-preflight.md`): all 101,479 live edge rows are
  endpoint-homogeneous, zero would be poisoned, zero ghosts. The DATA is safe; the MECHANISM is
  the risk.
- **The guard-kind pin widened** (`test_surreal_schema.py`): `TABLE (RELATION)` becomes its own
  kind requiring `OVERWRITE`, and `SEQUENCE` is added. ⚠ This pin previously asserted that EVERY
  `DEFINE TABLE` must be `IF NOT EXISTS` — i.e. **the instrument built to prevent #107 actively
  certified the silent-no-op as correct for edges.** It would have gone RED on a correct build.

## Scope OUT
- `messages.py` / `MessageLedger`, `send`/`drain`/`ack`, `set_status`, the shared `AgentRefLike`
  module, the derived waiting state, all concurrency pins, the retry-seam driving body →
  **packet 03a (the ledger)**.
- Tool dispatch, renders, promise proofs, hostile render fixtures, deploy, live-wire smoke →
  **packet 03b (the surface)**.
- `blocks` mirroring, fleet columns, `_comms_footer` (04); await/story/`since=` (05).

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
**⚠ THE ENGINE IS NOW 3.2.1 (migrated 2026-07-22, reference §0)** — this contract was
probe-settled on 3.1.5. The migration receipts cover: identical suite behaviour, #107
re-probed, SDK unchanged. NOT covered: two `[VENDOR]` release-note claims touching THIS
packet's seams — the **duplicate edge record ID fix (#349)** (bears on `UNIQUE(in,out)`
dedupe behaviour) and the **cold-start `Session not found` router-race fix (#308)**.
Re-probe each on 3.2.1 where a pin leans on it; un-re-probed 3.1.5 facts keep their
provenance labels (reference law).
**#146 adjudication (slotted 2026-07-22):** verify the dirty-store migration pins cover a
changed `DEFINE SEQUENCE` BATCH/START on an existing store (the #107 shape for sequences)
— pin it, or record the accepted residual with a named re-open trigger. No silent gap.
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
**TEST + STORE ONLY — NO DEPLOY** (header law; the stale send→drain→ack/deploy exit that
previously sat here belonged to the pre-split packet — send/drain/ack are 03a/03b).
Scoped gates green with passed-COUNTs (the 47 store pins + the dirty-store migration pins
+ the `[real]` tier) + `scripts/typecheck.sh` + ruff + **cold audit** (production-touching
relation flip) → one-concern commits at natural boundaries → INDEX row + Log + ledger
rows; 03a unblocked.
