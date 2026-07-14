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
Packet 02 deployed; task f86af162 claimed; `comms-subsystem.md` build-time probe list
(the C2 probe is this packet's); spike-surreal up.

## Exit
Full gates + cold audit + deploy BOTH + smoke: send→drain→ack round-trip on the live
wire incl. a broadcast and a hostile body staying fenced; INDEX row + Log.
