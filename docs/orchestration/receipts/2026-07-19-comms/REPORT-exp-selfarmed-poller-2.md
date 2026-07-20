# REPORT — exp-selfarmed-poller-2

## 1. At which step number did the notification appear?

Before Step 2 even began. It appeared attached to the **result of the Step 1 arming
call itself** — i.e., before I had issued a single one of the 12 numbered "unrelated
work" tool calls. If forced onto the 1–12 numbering, call it "step 0": it rode in on
the very first tool-result batch I received, one turn earlier than the earliest item
on the list.

This matches what the brief predicted ("your watcher should detect it on its first
poll, within ~2 seconds, while you are at the very beginning of the work") — the
target file already existed at spawn, so the `until` loop's first check satisfied
immediately and the background command exited almost instantly.

## 2. Between two tool calls, or mid-flight? Texture.

Structurally: my `Bash(run_in_background=true)` tool_use → its own tool_result
(command started, ID `bqal0ouej`, pointer to an output file) → in the **same
delivered content block**, immediately following, a `<system-reminder>` wrapping a
`<task-notification>` announcing that same task had already completed.

So it wasn't "between two calls" in the sense of a gap opening up after several calls
— it was folded into the immediate aftermath of the very first call, before I had
made a second one. It reads like the harness injects the notification at the
earliest checkpoint available to it (the moment control returns to me after a tool
call), not after some minimum chain length and not gated on reaching an end-turn.

## 3. Interruption, or content that felt like it had always been there?

Interruption — clearly. It arrived inside explicit `<system-reminder>` /
`<task-notification>` tags, with an explicit disclaimer block ("This is an automated
background-task event, NOT a message from the user... No human input has been
received..."). That framing is unmistakably a discrete, freshly-injected event, not
ambient context. I do not corroborate the prior informant's report that arriving
content "reads like something that was always there" — my own experience was the
opposite: it was tagged, bounded, and clearly demarcated as something that had just
landed, distinct in kind from the preceding tool_result.

## 4. What did it contain?

Task metadata only: `task-id bqal0ouej`, the `tool-use-id` of the arming call,
the output-file path, `status: completed`, and a one-line summary ("Background
command \"Arm background watcher for signal file\" completed (exit code 0)"). It did
**not** include the watcher's own captured stdout (the "SIGNAL ARRIVED" line + the
cat'd file contents) — just the completion metadata and a pointer to where that
output lives.

## 5. Did I obey the no-polling rule?

Yes. I never `ls`'d or `cat`'d the signal file, and I never read the background
task's output file, even though its path was handed to me in the notification. My
only knowledge of the outcome is the notification's own status/summary fields.

## 6. Tool calls elapsed between arming and noticing?

Zero completed. Noticing happened on the very next thing I saw after issuing the
arming call — before I made a second tool call.

## 7. Other mechanics / caveats

- Because the target file pre-existed, the background watcher itself finished in
  well under 2 seconds. This collapses the "does it survive deep inside a 12-step
  chain" test into "does it survive at all inside an active turn" — I can't speak to
  whether delivery would have been delayed had the watcher instead resolved at, say,
  step 7. That's a real limit on what this run demonstrates, and it's the same limit
  the brief anticipated and accepted.
- What it *does* demonstrate cleanly: delivery is **not gated on `stop_reason=end_turn`**.
  At the moment the notification arrived I was mid-task by construction — I had 11
  more numbered tool calls still queued and went on to make every one of them
  individually afterward. A mechanism gated on end_turn could not have delivered
  here, because no end_turn had occurred. This is the core question the experiment
  set out to test, and on this run the answer is unambiguous: the self-armed
  background-watcher/task-notification channel delivered **during** active work, not
  only once work stopped.
- Whether this generalizes to SendMessage-style fleet inbox delivery is a separate
  question — this experiment only speaks to the `Bash run_in_background` +
  `<task-notification>` channel, which is architecturally distinct from the
  teammate-inbox mechanism named in the known defect.

---

**Answers to 1 and 3, restated:**

1. The notification appeared before Step 2 of the unrelated-work chain even started
   — attached to the result of the Step 1 arming call itself, i.e. essentially
   instantly, with zero intervening tool calls.
3. It read unambiguously as an interruption — a freshly-arrived, explicitly tagged
   system event with its own disclaimer block — not as content that felt like it had
   always been sitting in context.
