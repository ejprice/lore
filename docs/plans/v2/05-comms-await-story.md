# 05 — Comms: await + story + hooks · formerly PKT-28 phase C3
size ~0.30 wu →split at kickoff if the folds push past 0.25 · wave C · depends: packet 04
law: read `comms-subsystem.md` FIRST + DESIGN-LAW §8/§5/§1 · **Opus 4.8 builder on the
await/LIVE leg (operator roster ruling)** · DEPLOY: yes (both)

## Mission
The wait-and-reconstruct half of the surface: bounded await, task-anchored story,
rollup extension, CLI, and the idle-gate hook rework.

## Scope IN
- `await`: snapshot-first bounded wait (drain SELECT → filtered LIVE-on-edge wake w/
  poll fallback, ≤55s, honest empty on timeout) — plan §"await semantics". Build-time
  probe: RELATE fires edge-table LIVE (empty-payload-safe by design); re-probe the
  socket-drop error shape on 3.1.5. Seven scout.py constraints + injection pin.
- `story`: task-anchored lineage in one call (created→blocks→claim→messages→brief
  versions→transitions→report_path).
- Rollup gains messages/fleet/skew sections (the C0 rollup extension).
- `comms_cli.py`.
- teammate-idle-gate v2, fail-open — **folds #121** (worktree-aware artifact check —
  today every agent briefed into a sibling worktree gets a false 'report missing' nudge)
  **and #149** (slotted 2026-07-22: the gate fires on COMPLIANT agents whose briefs
  legitimately owe no artifact — v2 must key on what the brief actually OWES, not a
  hardcoded REPORT-<name>.md expectation; a gate that punishes honest work gets ignored).
- **Folds #89**: lore_tasks single-task detail read (full description reachable via MCP).
- **INHERITED DEBT — 03b's R1, DEFERRED HERE BY OPERATOR RULING 2026-07-24, WITH THIS AS ITS
  NAMED DECISION POINT (a deferral without one is a can-kick — this line IS the mechanism).**
  **05 MUST re-adjudicate drain-row question visibility when it designs `await`/`story`.**
  THE HOLE: drain rows do NOT mark `question=true` messages — an inbox row that ASKS renders
  like any other, so a recipient cannot see at a glance which rows owe an answer. It is taught
  SENDER-side (03b S4.1's question line) and STATICALLY (03b S5's instructions paragraph), but
  never marked per-row on the recipient's own inbox.
  WHY IT WAS PRICED OUT OF 03b, not forgotten: the recipient-side marker needs `question` added
  to `InboxEntry` — an **ORACLE + model change**, and an oracle change is contract-author +
  adversary work by law (never a builder drive-by), whose satisfiability receipt must cover
  **BOTH** consumer suites (`test_message_ledger.py` AND `test_comms_tool.py` — the
  single-consumer premise was MEASURED FALSE; inherited delta row 6). And 05's await/story work
  re-shapes this teach anyway, so paying it in 03b would have been paying it twice.
  ⚠ **If 05 also declines it, that is a THIRD deferral of a known hole and it goes to the
  operator as a fork, not into another doc.** Design source: `03b-comms-surface-design-rulings.md`
  §Residuals item 1.

## Scope OUT
- Protocol/brief-base/drill (packet 06). C5 (checkpoint/respawn) stays deferred, no ruling.

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
Packet 04 deployed; `lore_findings` → #89, #121 open; LIVE-on-edge spike receipts from
the probe BEFORE building on it (documented poll fallback if it fails).

## Exit
Full gates + cold audit + deploy BOTH + smoke: an await wakes on a real send inside the
bound and empties honestly on timeout; `story` reconstructs a real task's arc; #89 +
#121 resolved; INDEX row + Log.
