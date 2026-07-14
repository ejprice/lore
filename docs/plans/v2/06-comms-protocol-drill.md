# 06 — Comms: protocol + THE DRILL (acceptance gate) · formerly PKT-28 phase C4
size ~0.25 wu · wave C, LAST · depends: packet 05
law: read `comms-subsystem.md` FIRST (its Exit section specifies the drill verbatim) +
DESIGN-LAW §8 · DEPLOY: receipts (no new tool surface expected)

## Mission
Make the fleet actually use it: the protocol rewrite plus the live multi-agent drill
that is the SUBSYSTEM'S acceptance gate. After this packet, the manual mitigation stack
(front-loaded-brief-only law, REPORT files as sole channel, idle-gate v1) retires per plan.

## Scope IN
- brief-base v3: register-first, drain points, directive-ack duty, SendMessage =
  contentless wake-nudge ONLY.
- Spawn-prompt template + UserPromptSubmit/PostToolUse hooks (drop PostToolUse if
  unsupported).
- **THE DRILL** (from `comms-subsystem.md` Exit): lead + 2 subagents coordinate solely
  through lore — register → brief_publish → create_many-with-blocks → claim → mid-work
  brief bump + directive → drain shows skew → parked question → kill → orphan surfaces
  in fleet → release → `story` reconstructs the arc. Receipts: SELECT dumps of
  brief/briefed/message/to-edge state, one rollup + one story render verbatim,
  zero-content-SendMessage transcript grep, both REPORT files.
- Receipts doc committed.

## Scope OUT
- C5 (checkpoint/respawn workflow) — deferred, no ruling; per-agent auth rides packet 39.

## Entry check
Packets 02–05 deployed; hooks pipe-tested headless before registration (all branches —
repo orchestration law).

## Exit
Drill receipts committed; protocol docs (brief-base v3) versioned; any defect found →
red-first fix + finding; INDEX row + Log. **Wave C closes here.**
