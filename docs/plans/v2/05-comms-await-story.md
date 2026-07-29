# 05 — Comms: await + story + hooks · formerly PKT-28 phase C3
size ~0.30 wu →split at kickoff if the folds push past 0.25 · wave C · depends: packet 04
law: read `comms-subsystem.md` FIRST + DESIGN-LAW §8/§5/§1 · **Opus 4.8 builder on the
await/LIVE leg (operator roster ruling)** · DEPLOY: yes (both)

⚠ **SPLIT RULED BY THE 2026-07-29 SWEEP (operator sizing directive: packets KEEP the size
goal — they always run over).** This packet's accumulated load (core + two DD inheritances +
five routed findings + two verb folds) is far past the law. It boots as TWO sessions; this
file stays the shared reference until the kickoff mints the bootable halves (the 03a
precedent):
- **05a — the WAIT SURFACE (~0.30, re-size at its own kickoff; DEPLOYS):** await + story +
  rollup extension + `comms_cli.py`; DD-2.a (waiting mechanism) · DD-4.c (`since=` serves
  seen rows) · R1 drain-question visibility · #183 (bound the pending read) · #190 (oracle
  parity FIRST — before any message-path pin) · #214 (the live receipt).
- **05b — LEDGER VERBS + HOOKS (~0.20):** #89 (task detail read) · #174 (supersede carries
  `blocked_by`) · **#256** (an ANNOTATE edge for open/acknowledged findings — ack→ack is
  illegal, so a correction must mint a duplicate or mis-resolve; hit by three sweeps running)
  · **#262** (register accepts a task_id another agent holds, SILENTLY — two surfaces
  disagree and only one says so) · idle-gate v2 (#121/#149) · #195 home-settling (with 06).

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
- **INHERITED FROM 03b's DEFERRED-DESIGN RULINGS (2026-07-25) — TWO MORE NAMED DECISION POINTS.**
  Full designs: `docs/plans/v2/03b-deferred-design-rulings.md` (DD-2, DD-4); provenance: the
  contract-blind audit's D7/D11 (`receipts/2026-07-24-packet03b/`… see the 03b close-out).
  1. **DD-2.a — SERVE THE CONVERSATIONAL-DEBT STATE, OR ADJUDICATE IT FOR REMOVAL.** 03b's
     served instructions were found teaching a debt state machine with **zero production
     consumers**: `MessageLedger.awaiting_answer` and `WaitingOnAnswer` are called by nothing
     in `server.py`, and `set_status` deliberately does not touch the status row. 03b fixed the
     LIE (the prose now teaches only what is served); **05 owns the MECHANISM.** It is fully
     designed so 05 implements rather than invents: a `waiting:` line on drain + heartbeat
     through ONE shared helper (the B4.1 skew precedent — sharing PROVEN BY MUTATION, not
     inspection), emitted iff `awaiting_answer` is non-None, prose DERIVED from the typed
     `WaitingOnAnswer`; `await`'s timeout render is the natural first consumer; **fleet gets no
     per-row cell** (it is an N×2-query N+1). ⚠ The wrong build to stop: wiring "waiting" to the
     STORED `input_required` status — that conflates two vocabularies; kill it with a
     discriminating pair. **This clause WIDENS 05's R1 duty: use the mechanism, or adjudicate
     the WHOLE thing for removal (method + model + the `(sender, question)` index 03b already
     built for it). A third deferral is an operator fork, not another doc line.**
  2. **DD-4.c — `since=` MUST SERVE ALREADY-SEEN ROWS.** `drain` is at-most-once: it stamps
     `seen_at` BEFORE the render reaches the caller, and only unstamped rows are ever served
     again, so any failure between the stamp and the caller receiving bytes (transport drop,
     cancellation) loses those messages **with no recovery verb in the tool set**. 03b
     deliberately did NOT reshape drain (the reshape buys only the in-process leg, which is a
     code-defect leg, not the operational one) and instead pinned the loss window shut. **The
     rows are stamped, not destroyed — "permanent loss" is a property of the VERB SET, and
     05's `since=` is exactly the verb that closes it, but ONLY if it serves seen rows.** A
     `since=` that serves only unseen rows leaves the hole fully open. ⚠ **If 05 declines this
     requirement, D11 returns to the operator as a fork.** Exposure is MEASURED meanwhile:
     `ok=false` drain trace rows are the loss-rate upper bound 06 reads (DD-4.d).

- **ROUTED FROM 03b's CLOSE (findings sweep 2026-07-26 — the numbers behind the Log line):**
  - **#183** — drain's pending read is UNBOUNDED. Bound it inside the same reshape that
    builds `since=`/paging (this packet already reworks that read path).
  - **#190** — the message ORACLE's error prose diverges from production's, so NO surface
    pin can see production's wording (it is how the D4 broadcast defect passed
    certification). Before this packet pins any message-path render, re-establish
    oracle↔production parity — or pin the divergence as a bound with a named trigger.
    Otherwise 05's pins inherit the same blindness.
  - **#214** — DD-4.c's hazard REPRODUCED LIVE within an hour of being documented (a drain
    stamped, then the caller's parser raised; the message was destroyed with no recovery
    verb). The live receipt that the seen-rows `since=` requirement above is load-bearing.
  - **#195** — routed 05-OR-06, UNSETTLED: nothing measures whether an agent OBEYS an
    instruction embedded in a teammate's message body (the fence makes a forgery LEGIBLE,
    not INERT). **Settle the home at THIS packet's kickoff**: a drill-battery measurement
    belongs to 06; a surface affordance belongs here.
  - **#174** — rides the #89 lore_tasks fold: `supersede` silently DROPS `blocked_by`,
    minting a falsely-unblocked successor (it bit the 03b dependency rewire live —
    the Log's `618cd45d` retirement). Fix in the same verb pass.

## Scope OUT
- Protocol/brief-base/drill (packet 06). C5 (checkpoint/respawn) stays deferred, no ruling.

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
Packet 04 deployed; `lore_findings` → #89, #121 unresolved (+ #174/#183/#190/#214
acknowledged-here, #195 unsettled 05-or-06 — settle it now); LIVE-on-edge spike receipts
from the probe BEFORE building on it (documented poll fallback if it fails).

## Exit
Full gates + cold audit + deploy BOTH + smoke: an await wakes on a real send inside the
bound and empties honestly on timeout; `story` reconstructs a real task's arc; #89 +
#121 resolved; INDEX row + Log.
