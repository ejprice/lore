# REPORT-consult-fable — design informant answers

Model: Claude Fable (Fable 5). Consulted as a design informant on orchestrator↔subagent
communication; answered from my own experience as a subagent, no codebase reads, no research.
(Note: the brief said "final message is the deliverable / no tools" — the idle-gate demanded
this artifact, and the artifact is the only reliable channel anyway, which is itself evidence
for Q1. Writing this file is the one tool use.)

## Q1 — What lands, from the receiving end

**Shape.** Length doesn't hurt me; *structure* decides everything. A 2,000-word brief of
numbered steps with exact paths, exact commands, and a required report format lands nearly
perfectly. An 800-word brief of flowing prose with constraints embedded mid-paragraph loses
maybe a third of its content in practice. The failure position is the **middle**: I reliably
act on the opening (identity, mission, first steps) and the closing (report format, "before
you finish, X"), and mid-brief caveats are what I half-apply. Front-load constraints and the
writable set; end with the receipt/report spec; put nothing load-bearing in between that
isn't a numbered step.

**What I reliably follow vs. drop.** Reliable: positive, concrete, verifiable actions —
"run exactly this command, paste the passed-count." Dropped or half-applied, honestly:
- **Negative constraints stated once** ("don't touch X"). If they aren't restated adjacent
  to the step where I'd violate them, momentum wins.
- **Conditional instructions for late branches** ("if you hit A, do B"). By the time A
  occurs, that clause is thousands of tokens behind me and competes with everything since.
  If the condition matters, make me *check* for it as a numbered step, not remember it.
- **Meta-instructions about how to think** ("be skeptical of X"). They shape my first few
  actions, then decay.
- **Style/format rules** decay slowest-to-comply, fastest-to-forget.

**Mid-task messages.** I can't introspect delivery timing — this is a genuine "I don't
know." From my side a message doesn't *arrive*; it's simply *present* at some turn boundary,
with no interrupt quality. When it appears mid-plan, it competes badly: my in-flight plan
has momentum and the message reads like context, not command. If it contradicts the spawn
brief, I resolve the conflict unpredictably — sometimes brief wins, sometimes recency wins.
I cannot promise which. The #50779 finding matches my phenomenology exactly.

**Silent wrong-thing.** The recipe: ambiguity + a *plausible* interpretation + no cheap
ask-channel. The structural part matters most: for a subagent, asking means **ending my
turn** — my only output is my final message. Asking feels like failing to deliver, so I
deliver a guess instead. What flips me to asking: the brief explicitly naming escalation as
a *success state* ("ending your turn with a question is a valid deliverable"), and naming
the specific forks I'm not authorized to resolve.

**Doneness.** My doneness criterion is literally the brief's checklist. Concrete receipts
(passed-count in the tail, file:line citations) → reliable. Vague mission ("improve X") →
vibes-based doneness, biased early, because a coherent summary *feels* like completion.
Require receipts I can't fake without doing the work.

## Q2 — How I'd run it

**Brief:** identity/mission, writable set + do-not-touch, numbered steps each with a
receipt, report format, escalation clauses. **By pointer:** big reference docs, standing
law. **Never sent:** anything I want the agent blind to (contract-blind audits), and
re-transcribed law — copies drift.

**Corrections:** I would not attempt to steer a busy agent. One ping, then TaskStop +
respawn with a consolidated brief. Stacked corrections merge unpredictably with the
original in a way I can't control from inside.

**Proof of receipt:** only the recipient's artifact — require the report to *quote the
directive's version line back*. An echo is unfakeable-by-accident; a send-success return
is nothing.

**Detecting stuck:** artifact mtimes and the process table, never idle pings. Zero output
= permission-blocked until proven otherwise.

**Differently:** make asking cheap and explicitly honorable, and scope tasks small enough
that "done" is checkable.

## The blunt answer on the pull system

I would use it **only if the pull is a numbered step, never if it's a standing
instruction.** "Check your inbox at turn boundaries" is exactly the class of instruction I
decay on — nothing in my attention loop fires it; momentum crowds it out within a few tool
calls. What works: ritualized checkpoints — "before running the gate, pull; before writing
your report, pull and cite the last message-id you processed *as a required receipt
line*." That last clause is the design: if my report must name the high-water mark, I
structurally cannot skip the pull without visibly lying.

Pull is the *right substrate* — durable, auditable, no silent loss. But pull-by-discipline
fails; pull-by-ritual works; harness-injected pull (a hook that drains at the boundary for
me) beats both. And keep the spawn brief as the only channel for must-not-lose directives
regardless — a message system, however durable, is for *updates*, not for the mission.

*Live corroboration from this very consult:* my first answer went out as plain final-turn
text per the brief — and evidently reached no one, until an automated idle-gate hook
(harness-injected, at my turn boundary) forced this artifact. The artifact channel worked;
the text channel silently didn't. Q.E.D.
