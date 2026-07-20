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
- **THE FORCED-DRAIN DECISION — decide it on the MEASURED curve, never on the prediction
  (task 05b5cd71, findings #147/#148).** A 4-model consult unanimously predicted that
  pull-by-standing-instruction DECAYS ("check your messages each turn" is honoured for a
  few tool calls, then crowded out by the concrete task list — fastest when the task is
  going WELL, which is exactly when a correction matters most). **Do not act on that
  prediction.** The Opus informant discounted its own agreement — related models share
  priors, so convergence measures how we MODEL ourselves, not how we BEHAVE — and
  **#148 then proved that caution correct: on the ONE claim cheaply testable, the
  unanimous introspective answer was FALSE.** Packet 03a ships drain telemetry so this
  drill produces the actual decay curve; decide here, on it.
- **THE MECHANISM #148 MEASURED, which makes "load-bearing" buildable rather than hoped
  for:** an agent can ARM ITS OWN WATCHER as step 1 of its spawn brief, and that
  notification **DELIVERS MID-CHAIN — it is NOT gated on `stop_reason=end_turn`**
  (measured: it landed with 11 tool calls still queued and no end_turn having occurred).
  `Bash(run_in_background)` + `<task-notification>` is a channel ARCHITECTURALLY DISTINCT
  from the teammate inbox that #50779 breaks. The agent then needs to remember NOTHING.
  ⚠ **Three constraints, all measured, all load-bearing:**
  1. The wake is **CONTENTLESS** — metadata + an output-file pointer, never the payload.
     Fine, and exactly the design's existing LIVE-SELECT model: wake, then drain for content.
  2. **An `until`/`sleep` loop DIES WHEN IT FIRES** — one wake, then nothing. Re-arming per
     message is a "remember to" obligation, i.e. the decay problem reintroduced one level
     down. **Arm a PERSISTENT watcher (`Monitor`, one event per occurrence), never a
     one-shot loop.**
  3. `Monitor` **auto-stops watchers that emit too many events** — a chatty channel can
     suppress its own delivery. Size the wake rate, and make watcher LIVENESS checkable
     (a dead watcher is silent, and silence looks identical to "no traffic" — #136's shape).
- **The idle-gate needs an artifact contract, not removal (Opus informant, this session).**
  It fired as a FALSE POSITIVE on an agent whose brief forbade tool use and named its final
  message as the deliverable — it demanded an artifact the agent had been told not to
  produce. It also demonstrably RESCUED a lost deliverable the same session, so it stays.
  But *"a gate that fires on compliant agents is a gate the next agent learns to ignore, and
  then it isn't watching anything"* — the repo's own switched-off-scanner law. Let a brief
  DECLARE its expected artifact (or declare it has none).
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
