# Agent comms — MEASURED, 2026-07-19/20

**Successor to `2026-07-04-agent-comms-failures-research.md`.** That document established, from
evidence and the upstream bug tracker, that Claude Code's push delivery to BUSY subagents is broken
by open defect anthropics/claude-code#50779 — the inbox injects only at `stop_reason=end_turn`, and
`SendMessage` returns success unconditionally, so loss is silent. It produced the mitigation stack
this repo runs on (front-loaded briefs, durable pull channels, artifact-as-receipt) and the design
for the comms subsystem (packets 02–06).

**This document is what happened when the same questions were MEASURED instead of reasoned about.**
Two of its three headline results contradict what careful, well-motivated reasoning had concluded —
including reasoning in this repo's own reference documentation.

Raw receipts: `receipts/2026-07-19-comms/`.

---

## Why it exists (operator questions, in order)

1. *"What would be the most efficient and reliable way to communicate with your agents?"*
2. *"Spawn an agent of each latest model and ask them the same — and if THEY were the orchestrator,
   how would THEY communicate?"*
3. *"Is it possible to have an agent start a pull or polling loop as part of its initial brief? Why
   rely on 'memory'?"*
4. *"Are you going to ignore the opus agent's advice to measure decay? Or does your plan not need it
   because you've found a way to ensure decay is irrelevant?"*

Question 3 produced the measurement. Question 4 stopped a consult from being shipped as a finding.

---

## Part 1 — the four-model consult (Haiku · Sonnet 5 · Opus · Fable)

**Method.** Four agents, **identical prompts**, told to answer from their own experience as
subagents and explicitly NOT to read the codebase — so the answers are introspective reports, not
summaries of our design. They were asked to push back if they thought pull-based comms was simply
wrong. Deliberate design: same question, different models, **diff the answers rather than blend
them**.

**Delivery note, which is itself a result: three of four answers did not arrive by the channel the
brief specified.** The brief said "your final message IS the deliverable". Fable's answer reached
nobody until this repo's idle-gate hook forced it to write a file. Haiku's never arrived at all —
over twenty minutes after a `SendMessage` returning `success: true`. **The orchestrator committed
the exact failure mode he was consulting about, while consulting about it.** See "Instrument
defects" below; the Opus informant's diagnosis of it is sharper than the one originally recorded.

### What they converged on

- **Mid-task messages have no interrupt quality.** Sonnet: *"I have no felt experience of noticing
  something arrive mid-tool-chain… I only see something when it's already sitting in context before
  my next turn starts."* Fable: *"no interrupt quality — they lose to in-flight momentum."*
  ⚠ **This claim was later FALSIFIED by measurement for the background-task channel** (Part 2).
- **Pull is the right substrate and the wrong discipline.** Sonnet: durability fixes "silently
  dropped" but relocates the failure to *"silently never checked"* unless the check is wired into
  the loop mechanically. Fable: *"pull-by-standing-instruction WILL decay within a few tool calls."*
- **Where instructions die.** Fable: the **MIDDLE** of a brief — opening and closing land. Sonnet:
  anything *"stated once early and never reinforced near the point of relevance."* Both: negative
  constraints stated once decay; positive concrete steps with receipts are followed.
- **Why they silently do the wrong thing.** Opus: *"Ambiguity resolves itself invisibly — I pick a
  reading and the pick doesn't feel like a decision, so there's nothing to escalate about."* And:
  *"Generic 'ask if unsure' does nothing — I'm never subjectively unsure at the moment I choose."*
  The fix both named: **name the specific forks in advance, and make escalation a SUCCESS state.**
- **How they decide they are done.** Opus: *"I'm done when I've produced the SHAPE you asked for,
  not when the work is correct… Executable done-conditions I verify; prose done-conditions I
  self-assess, and my self-assessment is generous."*
- **Opus's three tiers**, adopted: standing law → the **spawn brief** (only guaranteed-read
  channel) · must-not-lose but not urgent → the **durable pull store, welded into the workflow** ·
  must-act-now → **TaskStop and respawn**, because no message shape reliably preempts an agent
  mid-chain and *"building one on top of a channel that can't interrupt is designing around a wish."*
- **Opus on receipts:** *"Proof of receipt = an artifact I produced that could only exist if I'd read
  it. Not an acknowledgment — I'll acknowledge anything… my saying 'got it' proves slightly less than
  nothing, because it's the cheapest token I can emit."* And the cheap early instrument for catching
  an agent confidently doing the wrong thing: **make it post its plan and its interpretation of the
  ambiguous clause BEFORE the work**, not after.

### ⚠ The caveat that saved the session, from the Opus informant

> *"We are three instances of closely-related models answering the same question about the same
> architecture; correlated priors produce correlated answers. The convergence is evidence that the
> claim is the natural inference from how we model ourselves — it is not three independent
> measurements of how we actually behave."*

It named the instrument instead: **log every pull call against turn index across a long task and see
whether the frequency decays.** *"If it does, we were right for the right reason. If it doesn't, we
were all confabulating the same story, and you'd never have learned that from asking us again."*

**This was correct, and Part 2 proves it.**

---

## Part 3 — the measurements (three runs)

**Question:** can an agent ARM ITS OWN pull at spawn, so receiving does not depend on memory — and
does that escape the `end_turn` constraint?

| run | method | result |
|---|---|---|
| 1 | signal dropped 45s after spawn; 12-call chain | **CONFOUNDED — do not cite.** The chain finished before the signal existed. Delivered at the first available boundary. |
| 2 | signal PRE-PLACED before spawn; watcher fires <2s; 12-call chain | Notification arrived **attached to the arming call's own result** — before step 2, with **11 calls still queued and no `end_turn`** |
| 3 | **timed** watcher (`sleep 40`), fire moment guaranteed; 15-call chain | Notification arrived **after step 13 of 15**, promptly, deep in the chain |

### Result 1 — delivery is NOT gated on `end_turn`, for this channel

Replicated across runs 2 and 3. A mechanism gated on end-of-turn could not have delivered in either.
**`Bash(run_in_background)` + `<task-notification>` is ARCHITECTURALLY DISTINCT from the teammate
inbox that #50779 breaks.** This does not refute that bug — it identifies a path around it, and it
makes the Opus informant's "load-bearing, not mandatory" shape actually buildable: **the agent
remembers nothing.**

### Result 2 — the wake is CONTENTLESS

Both runs: task-id, tool-use-id, output-file path, `status: completed`, a generic summary. **Never
the watcher's own stdout.** The payload requires a follow-up read.
**This is exactly the model the comms design already specifies for LIVE SELECT — a contentless wake,
never a source of truth.** The design's shape was right; only the delivery mechanism changes.

### Result 3 — THE INTROSPECTION WAS WRONG, 0 for 2

Both measured agents, independently, and the second explicitly warned not to simply agree with the
first: the notification is *"unmistakably a discrete, freshly-injected event"*, tagged and bounded,
*"structurally distinct from the preceding tool-result pattern"*. Run 2: *"I do not corroborate the
prior informant's report."*

**Two consult informants said the opposite from introspection. On the one claim that was cheaply
testable, the unanimous introspective answer was FALSE.**

> **THE STANDING LESSON: a model consult is a source of HYPOTHESES, not findings. Test the cheaply
> testable ones before acting on any of them — and weight the untestable remainder by how the
> testable ones scored.** Here they scored 0 for 2.

**Consequence, carried into packet 06:** the consult's central claim — that pull-by-standing-
instruction decays — remains **UNMEASURED**. It must NOT be treated as established. Task
`05b5cd71` carries the real measurement with its decision point; packet 03a ships the drain
telemetry that makes it producible.

### ⚠ Traps in the mechanism (all measured)

1. **An `until`/`sleep` loop DIES WHEN IT FIRES.** One wake, then silence. Re-arming per message is a
   "remember to" obligation — *the decay problem reintroduced one level down*. **Arm a PERSISTENT
   watcher (`Monitor`, one event per occurrence), never a one-shot loop.**
2. **`Monitor` auto-stops watchers that emit too many events** — a chatty channel can suppress its own
   delivery.
3. **A dead watcher is SILENT, and silence is indistinguishable from "no traffic"** — finding #136's
   shape (a guard that cannot substantiate its own verdict). Watcher liveness must be CHECKABLE.
4. Measured on **sonnet only**; nothing here speaks to SendMessage/inbox delivery, still broken.

---

## Instrument defects — disclosed, because they are the most transferable part

**The orchestrator's, all four:**
1. Asked for deliverables **as a final message**, i.e. with no durable address — then could not
   retrieve them. The Opus informant's diagnosis is better than the original one: *"my answer WAS
   produced, in full, on time, correctly. What failed was that the channel didn't persist it… The fix
   is not 'make agents write files'; it's **make the deliverable's address part of the brief**."*
2. Built run 1 so the report was the agent's **last act before `end_turn`** — an experiment that
   could not observe its own outcome.
3. Dropped run 1's signal **after** the chain had ended, then briefly reported that null as a finding
   before timestamps corrected it.
4. Read a report file **while an agent was still writing it**, concluded it was truncated, and spawned
   a duplicate agent. **File contents are not a completion signal.**

**The agents' own, each caught by a control the brief demanded:**
- The endpoint probe's first run would have concluded *"RELATE rejects bad ids"* — **the exact
  opposite of the truth** — had the positive control been omitted; the control revealed its endpoints
  were bound as strings.
- The migration probe's controls fired on the UNIQUE index rather than the clause under test.
- The production audit's first edge-detector tested for the *presence* of an `in`/`out` key, but a
  schemaless SELECT returns absent keys as `None` — it flagged a node table as an edge and **only a
  crash revealed the bug**.
- The contract author's dirty-store pin read `INFO FOR TABLE`, which carries fields and indexes but
  not the table's own definition — **it failed on a CORRECT build until fixed**.

> Five instrument defects across one session, every one caught by a control or a crash rather than by
> review. **"A probe needs a control" is not a nicety — it is the only thing that caught any of these.**

**And the one that generalises furthest:** the orchestrator committed the failure mode *while
consulting about it*. Opus: *"That's not embarrassing, it's the most informative data point in this
whole exchange. It means the failure is not caused by ignorance… knowing a failure class does not
prevent an instance of it."* This repo's CLAUDE.md already carries a section titled
**A DIAGNOSIS IS NOT AN INSTRUMENT**. This is another entry in it.

---

## Design consequences (where each lands)

| finding | destination |
|---|---|
| Self-armed persistent watcher = the wake mechanism; agent remembers nothing | **packet 06** (brief-base v3 + hooks) · **packet 05** (comms_cli/await) |
| Wake is contentless → wake, then drain for payload | validates existing design; **packet 06** |
| Three traps (one-shot death · Monitor auto-stop · silent dead watcher) | **packet 06** |
| Pull-decay is UNMEASURED — decide on the curve | task **05b5cd71**, decided at **packet 06** kickoff by the operator |
| Drain telemetry required at build time so the curve is producible | **packet 03a** (in its Scope IN) |
| Trace substrate serves total=0 — the natural home may not record | finding **#147**, diagnose BEFORE 03a designs telemetry |
| Idle gate needs an ARTIFACT CONTRACT, not removal | **packet 06** + finding (below) |
| Brief-design findings (middle-of-brief decay · escalation as success state · executable done-conditions · plan-before-work receipt) | **brief-base v5** — the reusable half |

**The line worth keeping, from the Opus informant, and the acceptance test for packet 06:**

> *"Do not ship the comms system with a brief clause telling agents to use it. Ship it with the pull
> welded to the work, and then the clause is unnecessary — which is the only proof that you built an
> instrument instead of writing a law."*

---

## Open questions

- Does pull-by-standing-instruction actually decay? **UNMEASURED** (task `05b5cd71`).
- Does the trace path record anything? **UNDIAGNOSED** (#147; three candidate causes, do not
  one-read-diagnose).
- Does the background-notification channel behave the same across models? Measured on sonnet only.
- Does a `Monitor`-style persistent watcher deliver mid-chain the way a one-shot does? Untested —
  and it is the shape packet 06 would actually ship.
