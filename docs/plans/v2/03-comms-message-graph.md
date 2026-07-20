# 03 — Comms: message graph (send/drain/ack) · formerly PKT-28 phase C2b
size ~0.25 wu · wave C · depends: packet 02
law: read `comms-subsystem.md` FIRST + DESIGN-LAW §8/§5/§1 · design source:
~/.claude/plans/one-of-claude-codes-nifty-garden.md · DEPLOY: yes (both)

## Mission
The message graph core: durable store-and-forward messages with per-recipient delivery
state, the actual replacement for Claude Code's lossy SendMessage.

## Scope IN
- Schema slices: `message` node (id `ulid()`, `grade` signal|directive, bodies immutable
  after send — strikeable design choice) + `to` delivery edge (UNIQUE(in,out); write-once
  CAS stamps `seen_at`/`acked_at` — only the recipient stamps its own edges, zero hot-row
  contention).
- `message.seq` minted via native `DEFINE SEQUENCE` + `sequence::nextval("<name>")` —
  probe-settled, operator-confirmed (ledger task f86af162; not gapless, accepted).
- `messages.py` ledger module (tasks.py blueprint): send txn (node + to-edge fan-out;
  `to=[]` ⇒ broadcast active registry; unregistered recipient = teaching error),
  drain (numbered render; stamps exactly what's rendered; `peek` skips; `ACK REQUIRED`
  trailer), ack (write-once CAS).
- Hostile render fixtures MANDATORY (message bodies are stored free text: newlines +
  row-shaped forgery + backtick runs).
- Concurrency pins at ≥8-way, 20-consecutive-green law; the UNIQUE-on-edge cascade probe
  (RELATE → delete endpoint → re-RELATE) runs in this packet.

## Scope OUT
- `blocks` mirroring, fleet columns, `_comms_footer` (packet 04); await/story (05).

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
7. **LEAD: a broadcast does NOT deliver to its own sender.**

## Exit
Full gates + cold audit + deploy BOTH + smoke: send→drain→ack round-trip on the live
wire incl. a broadcast and a hostile body staying fenced; INDEX row + Log.
