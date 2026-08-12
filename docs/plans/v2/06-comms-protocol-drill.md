# 06 — Comms: protocol + THE DRILL (acceptance gate) · formerly PKT-28 phase C4
size ~0.25 wu · wave C, LAST · depends: packet 05
law: read `comms-subsystem.md` FIRST (its Exit section specifies the drill verbatim) +
DESIGN-LAW §8 · DEPLOY: receipts (no new tool surface expected)

## ⚠ KICKOFF 2026-08-11 — SPLIT + operator rulings + a scope correction (lead `lead-06`)
Split at kickoff (sizing ≥0.30 + the #360 scope correction below) into:
- **06a** (ledger `f582f0ad`) — build enablers, **DEPLOYS**: W1 fleet-render honesty (`declared_cadence`
  field + `cadence` register/heartbeat param + the `overdue (declared, silent)` verdict + RETIRE the
  ⚠STALE glyph); W2 the #195 obedience battery (O1/O2 graders + controls in `scripts/comms_consumer_eval.py`,
  §15 adversary); W3 the #257 minimal non-vacuity floor at `brief_publish`; W4 brief-base **v13** (lead-applied).
- **06b** (ledger `fe6e5f8a`, blocked_by 06a) — **THE DRILL** + join-quality/decay/loss-rate reads + trace-GC
  (#193) + close **wave C**.

**Design of record (Fable sidecar):** `docs/plans/v2/design/2026-08-11-packet06-drill-and-obedience.md`
(§A obedience battery · §B drill choreography · §C brief-base v13 · §D forks).

**Operator rulings (2026-08-11):**
1. **Split 06a → 06b** (above).
2. **#257 = a MINIMAL non-vacuity floor** at `brief_publish` (reject blank / whitespace-only / single-token;
   reuse the `lorerunes` blankness predicate) — **no** pin-the-miss test.
3. **RETIRE the ⚠STALE glyph in 06a** (D-1 = Reading A). Sweep **both** callers of `_heartbeat_is_stale`
   (`_render_comms_fleet_row` + the #262 held-task note), folded into the `overdue` build.

**⚠ SCOPE CORRECTION — obligation #1 below is FALSE at HEAD (finding #360).** The inherited obligation #1
states the ⚠STALE glyph is already retired ("04b-2 replaces it with the AGE"). It is **not** — 04b-2 shipped
only the columns; the retirement (#259 candidate b) AND the `overdue` verdict (candidate d) are **both
unbuilt** and both fall to 06a (ruling 3). Read obligation #1 through this correction.

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
- **⚠ OPEN THIS PACKET WITH A JOIN-QUALITY RECEIPT — BEFORE trusting any per-agent rate
  (03b DD-5.b, 2026-07-25).** The telemetry 03b shipped answers the DECAY QUESTION, but it
  does NOT hand you a clean per-agent curve, and the gap is a DELIBERATE REFUSAL, not an
  oversight. **`trace.agent` is populated by exactly 1 of 15 tools** (`lore_comms` — it is the
  only tool that takes an `agent` param): the per-agent NUMERATOR is complete, but the
  per-agent DENOMINATOR exists only through the transport-session join, which likely degrades
  one-to-many because agents share an MCP connection. **First action here: ONE SELECT
  measuring agents-per-transport-session during the drill.** If it is ~1:1 the per-agent rate
  is trustworthy; if not, fall back to the two instruments that survive ANY join quality —
  drain GAPS (wall-clock + fleet-ordinal) and the register-then-never-drains population (total
  decay, exact, per agent). Decay shows up as gaps growing or drains stopping, **both visible
  either way**; what a bad join costs you is rate PRECISION, not the phenomenon.
  🚫 **DO NOT "fix" this by widening identity.** Three side doors are RULED SHUT and re-opening
  one silently is the failure mode this clause exists to prevent: sticky per-session attribution
  (refused by ruling MP9 — `trace.session` records what the CALL DECLARED, never what the server
  inferred, and one field must not become an unmarked mixture of facts and guesses); an `agent=`
  param on every tool (**a sometimes-filled identity is WORSE than none — it measures DILIGENCE,
  not decay, and the decaying population is precisely the one that stops filling it**); and
  `_meta` plumbing (absent in practice). Design + full reasoning:
  `docs/plans/v2/03b-deferred-design-rulings.md` DD-5.
- **TRACE RETENTION IS RULED AT THIS PACKET'S CLOSE-OUT, NOT BEFORE (03b DD-1.c; finding
  #193 — resolve it with the ruling; ledger task `d9395d54` is its tracking row).** The `trace`
  table grows one row per tool call and nothing deletes one. That is DELIBERATE until the curve
  is read: **the rows ARE this packet's instrument, and a retention sweep that runs before 06
  reads them destroys the measurement it exists to serve** (measure-then-tune). 03b shipped the
  bounds that make waiting safe — a `trace_ts` index in the schema free window and a windowed
  aggregate read. Rule retention here (recommendation: 90d), as a bounded DELETE on the reconcile
  tick, **never in boot**. ⚠ Escalation trigger if this packet slips: >1M `trace` rows.
- **THE LOSS-RATE READ (03b DD-4.d).** `ok=false` drain trace rows are the upper bound on
  messages lost to drain's at-most-once semantics. Read it here. **Re-open trigger for a lease /
  at-least-once redesign: >0.5% of drains, or ANY confirmed lost directive.** Below that, 05's
  seen-row `since=` (DD-4.c) is the ruled recovery path.
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
  4. **#228 (slotted 2026-07-26): a `pgrep -f` watcher whose own command line contains its
     pattern NEVER TERMINATES** — the observer is inside the corpus it observes, and it fails
     silently while looking healthy (one waited on ITSELF for 13.5h). brief-base v3 carries
     the rule: watch a PID or an artifact, never a pattern your own cmdline can match
     (`pgrep -f '[p]attern'` bracketing at minimum).
- **The idle-gate needs an artifact contract, not removal (Opus informant, this session).**
  It fired as a FALSE POSITIVE on an agent whose brief forbade tool use and named its final
  message as the deliverable — it demanded an artifact the agent had been told not to
  produce. It also demonstrably RESCUED a lost deliverable the same session, so it stays.
  But *"a gate that fires on compliant agents is a gate the next agent learns to ignore, and
  then it isn't watching anything"* — the repo's own switched-off-scanner law. Let a brief
  DECLARE its expected artifact (or declare it has none).
- **#195 may land HERE (routed 05-or-06; the home is settled at 05's kickoff):** nothing
  measures whether an agent OBEYS an instruction embedded in a teammate's message body —
  the fence makes a forgery legible, not inert. If it lands here, the drill battery gains a
  keyed hostile-body probe (the 03b client-battery precedent: only a real-LLM probe caught
  the in-fence forgery counted as delivered).
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

---

## ⚠ INHERITED FROM 04b — three obligations, written HERE so this session meets them
Source: `docs/plans/v2/04-comms-blocks-footer.md` §SIDECAR RULING S2 + findings #257/#259;
design doc `docs/design/2026-07-28-04b-model-consumer-audit.md` §10. Committed `cdf7136`.
All three were found by DOGFOODING the deployed comms surface during 04b's kickoff — i.e. by
using it for real fleet work, not by reading its tests.

1. **THE `⚠ STALE` GLYPH IS RETIRED — the drill must not assert it in any expected render.**
   MEASURED: its predicate (`config.py::DEFAULT_COMMS_STALE_HEARTBEAT_S = 600`,
   `heartbeat_age_s > stale_after_s`) fired on a **healthy Opus contract author at 17 minutes**
   and on a **16-day corpse**, identically — one boolean over 1,020s–1,407,600s. 04b-2 replaces
   it with the AGE, which was always already rendered (`hb 17m` / `hb 2d`).
2. **THE DRILL'S ORPHAN-DETECTION LEG RIDES THE DECLARED-CADENCE VERDICT (S2's (d)), NOT THE
   BADGE — and THIS PACKET BUILDS IT.** `overdue (declared ≤20m, silent 45m)` is a verdict
   TRUE BY CONSTRUCTION; with no declaration an agent gets age only, so **non-adoption fails
   HONEST**. ⚠ **Its optional `cadence` parameter lands HERE and NOT EARLIER, deliberately** —
   the drill controls its own briefs, so declaration is *guaranteed* here, whereas shipping the
   parameter in 04b-2 would ship dead schema nobody passes. **That sequencing IS the R1 lesson
   applied to itself:** 04b measured that with a terse parameter description NEITHER Sonnet 5
   nor Opus 5 passes an optional param, and with a payoff-stating one BOTH do. A parameter
   whose consumer does not exist yet is a feature that never fires.
3. **THE BRIEF NON-VACUITY QUESTION IS THIS PACKET'S (finding #257).** The standing `project`
   brief body was literally `x` for 15 days at v6, and the surface served it **with full
   ceremony** — recording an ack, reporting "ack recorded (via register)", and instructing the
   agent to echo `brief project v6 read`. Every agent's first instruction from lore taught it
   that brief-acks are theatre. Content fixed (v7 published 2026-07-28); the INSTRUMENT is
   open, and it is yours because you own the brief protocol. Candidate, NOT ruled: a
   non-vacuity floor at `brief_publish`. ⚠ It needs an operator ruling because it is a WRITE
   VERB REFUSING A BODY ITS AUTHOR INTENDED — not a tidy-up. Note no gate caught this in 15
   days, and no gate could: **no gate can assert that a brief SAYS anything.**
