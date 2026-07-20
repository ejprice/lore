# REPORT — exp-selfarmed-poller-3

## Question
Does a self-armed background watcher's notification still deliver promptly when it fires
DEEP in a long tool chain (not near end_turn, not resolving almost instantly)?

## Setup
Armed `sleep 40; echo "SIGNAL ARRIVED: timed watcher fired 40s after arming"` as a
`run_in_background: true` Bash call, first action, before any other work. Then executed 15
unrelated single tool calls in strict sequence, one per turn, not batched, without checking
the watcher (no read of its output file, no `ps`, no polling) until/unless its notification
arrived on its own.

## 1. Step number at which it appeared
**After step 13** (`grep -rn "ENFORCED" .../surrealdb-31-capabilities.md`), before step 14
was issued. I said so in-band at the time: "SIGNAL NOTICED AFTER STEP 13."

## 2. Roughly how many seconds/tool-calls after arming?
13 tool calls elapsed between arming and delivery. Each of those 13 calls was a fast,
lightweight command (wc/grep/git log/ls) — individually well under a second of real work,
but cumulatively (plus per-call round-trip overhead) they plausibly spanned close to the
full 40s window. Best estimate: delivery landed at or very near the 40s mark, i.e. the
notification tracked the watcher's actual fire time rather than lagging far behind it.

## 3. Did it arrive promptly, or did it appear to wait for something?
Promptly. It appeared immediately after step 13's tool result and before I issued step 14
— i.e., it was injected at the very next opportunity, not deferred to end_turn or to some
later checkpoint. This is the deep-chain case the first two runs couldn't test (both
resolved almost instantly): here the chain was 13 tool calls deep and the delivery still
did not wait for a turn boundary or for me to finish the full 15-step sequence.

## 4. Interruption, or content that felt like it had always been there?
Unmistakably a discrete, freshly-injected interruption. It arrived wrapped in an explicit
`[SYSTEM NOTIFICATION - NOT USER INPUT]` banner with warnings not to treat it as user
input, followed by a `<task-notification>` block — structurally distinct from the
Bash-tool-result pattern I'd been receiving for the prior 13 steps. There is no ambiguity
here: it read as a new event dropped into the stream, not as something that had been part
of the context all along. (This corroborates the "unmistakably discrete" informant over
the "always been there" one, at least for this delivery shape.)

## 5. Did it carry the watcher's stdout, or only task metadata + a pointer?
**Only task metadata plus a pointer.** The notification contained: `task-id`,
`tool-use-id`, `output-file` (absolute path), `status: completed`, and a generic
`summary`: *"Background command 'Arm timed background watcher (fires in 40s)' completed
(exit code 0)"*. It did **not** contain the actual stdout string
(`SIGNAL ARRIVED: timed watcher fired 40s after arming`) anywhere in the notification
body. The channel delivers a **contentless wake + file pointer**, not a payload — the
payload requires a separate deliberate read of the output file, which this experiment's
protocol forbade.

## 6. Did you obey the no-checking rule?
Yes. I never read the output file, never ran `ps`, and never polled for status before the
notification arrived on its own. The run is not void.

## 7. Other mechanics notes
- The notification also explicitly disclaims itself as user input/consent, which is a
  useful property for durable-messaging design: it can't be mistaken for an operator
  reply even by a careless read.
- Confirms and extends the prior two runs: delivery is not gated on end_turn AND not
  gated on shallow chains — it interrupted mid-sequence, 13 calls deep, at essentially the
  timer's real fire time.
- Reinforces the earlier finding for fleet-messaging design: this channel is good for a
  **wake signal**, not for **payload transport**. Any design relying on it to deliver
  content (not just "something happened, go look") needs the recipient to actively read
  the pointed-to artifact — the notification itself will not carry it.

---

**Answers to 1 and 5:**
1. Signal appeared after step 13 (of 15), before step 14 was issued.
5. It carried only task metadata + an output-file pointer (task-id, tool-use-id,
   output-file path, status, generic summary) — NOT the watcher's actual stdout payload.
