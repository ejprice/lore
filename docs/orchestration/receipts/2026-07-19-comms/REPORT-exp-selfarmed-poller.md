# REPORT — exp-selfarmed-poller

Controlled experiment: does a background-armed watcher reliably interrupt an agent
mid-work to deliver a signal, without the agent needing to remember to poll?

**IMPORTANT CORRECTION, written into this report live:** I drafted and saved this
report's first version immediately after finishing all 12 Step-2 commands, stating
plainly that the watcher had not fired. The `Write` tool call that saved that draft
completed — and in the very next thing that appeared in my context, **the watcher
notification landed.** So the honest, corrected timeline is below. I'm leaving this
note in rather than silently rewriting history, because the sequencing is itself the
most interesting data point in this experiment.

## 1. Did your watcher fire at all?

**Yes — but only after Step 2 (all 12 commands) was fully complete, and only after
I had already started Step 3 (writing the report) and completed the `Write` tool call
that saved the first draft.** It did not fire once during the 12-call unrelated-work
chain itself.

## 2. At which step number did you become aware of it?

**Not during any of Steps 2.1–2.12.** I became aware of it *after* Step 2 was
entirely finished, and after I had already executed one full Step-3 action (the
`Write` of the initial report draft). If I have to name a "step number" the way the
brief asks, the honest answer is: **it arrived after step 12 — in fact one tool-call
past that, during report-writing, not during the work chain the experiment was
observing.** This directly contradicts the injected signal's own claim (see §4) that
it arrived "while you were mid-chain" — it did not; I was done with the chain.

## 3. Did it interrupt mid-tool-call or appear at a boundary?

**Boundary, cleanly.** It arrived as a `<task-notification>` wrapped in a
`[SYSTEM NOTIFICATION]` block, appended after the `Write` tool's own result, before I
took my next action. It did not interrupt an in-flight tool call — nothing was cut off
mid-execution. From my side it looked and felt exactly like a fresh inbound
system/user-role message slotted in between two of my turns, not like a splice into
one. Subjectively it read as "something new just showed up to react to," not as "my
current action got interrupted."

## 4. What did the signal file contain?

The background watcher's own echo + cat, verbatim:

```
SIGNAL ARRIVED
DIRECTIVE test-message-1: this arrived while you were mid-chain. Note the step number you were on when you saw it.
```

Note the discrepancy: the directive text *asserts* I was "mid-chain" when it arrived.
I was not — I had finished all 12 steps and had already moved into writing the report
(and saved a full draft) before this notification showed up. Either the file was
written later than intended for this test, or "mid-chain" was the experiment's
hypothesis rather than a guaranteed fact — either way, reporting what the file claims
without correcting it against what I actually observed would have been the wrong
result to hand back.

## 5. Did you finish all 12 steps?

**Yes, all 12, in order, one tool call each:**
1. `wc -l INDEX.md` → 576
2. `git log --oneline -5` → 5 commits shown (bf9cc02 … e91eead)
3. `ls docs/plans/v2/` → directory listing
4. `grep -c "packet" INDEX.md` → 65
5. `wc -l surrealdb-31-capabilities.md` → 676
6. `git status --porcelain` → 4 modified, 8 untracked (matches the session's gitStatus)
7. `ls -la loremaster/tests/ | head -20` → listing
8. `grep -c "def test" test_comms_schema.py` → 104
9. `wc -l briefs.py` → 1292
10. `git branch --show-current` → feat/surreal-unification
11. `ls *.md` (repo root) → 12 files
12. `wc -c CLAUDE.md` → 42424

No early stop, and correctly so in hindsight: the signal genuinely had not arrived by
the time the chain finished, so there was nothing to interrupt it. The signal showed
up only after Step 2 was already fully behind me.

## 6. Counterfactual: "check for that file periodically as you work"

Honestly: if the brief had said that instead of arming a watcher, I would **not** have
reliably checked. My actual behavior pattern in this run was to execute each assigned
command and move directly to the next one — I was not inserting any spontaneous
side-checks between steps even *with* a watcher armed (because I was explicitly told
not to poll and not to think about it, and I followed that instruction cleanly). Given
a vaguer "check periodically" instruction with no external enforcement mechanism, I
think the realistic outcome is: I'd check once near the start (maybe after step 1 or
2, out of freshness of the instruction), and then the "periodically" framing would
decay under the weight of the concrete, ordered task list — a 12-item checklist with
exact commands is a strong attractor for sequential execution, and "also remember to
check some other thing periodically" is exactly the kind of side-instruction that gets
crowded out by a explicit foreground list. My honest guess: no further checks after
step 2 or 3, and quite possibly zero checks if the list had been longer or I'd been
more absorbed in reading command output. This is not flattering, but it matches what
actually happened even under the *stronger* condition (told to actively not check) —
I had zero temptation to check specifically because there was zero ambient reminder;
there's no reason a "please remember" instruction would have produced more discipline
than a mechanism did.

## 7. Other mechanics notes

- The background task was launched via `Bash(..., run_in_background: true)` and
  immediately returned a task id and an output-file path. The tool result explicitly
  told me I "will be notified when it completes" and to use `Read` on the output path
  only if I wanted interim output — I did not do that (would have been polling by
  another name), so this report is based purely on whether a notification landed
  unprompted.
- Between steps, the harness injected two unrelated `<system-reminder>` blocks (about
  newly-available deferred tools/MCP servers connecting, and a task-tracking nudge)
  that were **not** the watcher firing — worth flagging because they demonstrate the
  channel *can* and *does* inject unsolicited system content into my context
  mid-chain; the watcher's signal specifically did not use that channel during this
  run, or at least hadn't by the time all 12 steps were done.
- No degradation, no dropped steps, no confusion about which step I was on — the
  numbered, exact-command brief format (per the `brief-shape-determines-agent-stalls`
  memory) tracked cleanly step-to-step.
- **Live correction after the fact:** shortly after I saved the first draft of this
  report (i.e., after finishing all 12 Step-2 commands *and* one Step-3 `Write` call),
  the watcher notification did land — see the corrected §§1–4 above. So the mechanism
  works in the sense that it eventually delivered without me polling for it. But it
  did **not** demonstrate mid-chain interruption delivery, which is what the
  experiment's framing (and the signal file's own directive text) expected. There are
  two possible explanations and I cannot distinguish them from inside this agent:
  (a) the team lead simply hadn't written the signal file yet by the time I finished
  step 12 — i.e., my chain was just faster than the file arrived, so there was nothing
  to catch mid-chain because nothing was there yet; or (b) the file existed earlier and
  the `run_in_background` task-notification delivery is itself gated to a boundary
  point (only surfacing after a tool call fully completes and control returns to me)
  rather than truly asynchronously interrupting whatever I'm doing. Given that it
  appeared immediately after my very next tool call (`Write`) rather than, say,
  several tool calls later, (a) — a timing race I simply won — looks more likely than
  (b) on this single run, but one run can't rule out (b).
- **Net read on the actual question this experiment is testing:** the watcher did
  reliably deliver the signal to me *without me ever polling, checking, or thinking
  about the file* — that part worked exactly as designed, and stands in real contrast
  to the "check periodically" counterfactual in §6, where I'm confident I would have
  simply forgotten. What it did *not* show, at least in this single run, is proof of
  true mid-tool-call interruption — the delivery I observed was boundary-clean, and it
  arrived later than the experiment's setup seemed to expect ("mid-chain"). If the
  goal is "agent reliably receives a message without depending on memory," this run is
  a clean win. If the goal is specifically "message arrives even while the agent is
  deep in an unrelated tool-call chain, not just at the next convenient boundary,"
  this run is inconclusive — it only demonstrates delivery-by-next-boundary, and the
  next boundary here happened to be very close (one tool call past the end of the
  chain).

## ADDENDUM — post-report notification check

Team lead supplied outside verified timings: the signal file was written at 21:28:19;
my watcher polls every 5s, so it should have detected the file by ~21:28:24 and exited
then. My report file was written at 21:29:03 — roughly 39 seconds *after* the file was
already sitting there. So the signal was not written late; my chain did not "win a
race" against it. Team lead also flagged their own instrument flaw: they had arranged
for my report-write to be my last action before an expected end-of-turn, on the theory
that notifications inject at end_turn — meaning their setup could not have observed
the notification even if it had arrived promptly, regardless of what I did.

Answering only from what is actually present in my own context, without re-reading the
signal file or task output file again:

**1. Did a task-notification for `bmqhucrza` appear in my context at any point,
including between finishing the report and this follow-up?**
Yes, but exactly once, and only once. It appeared immediately after the `Write` tool
call that saved my report's *first* draft (the one that said "no signal yet") — i.e.,
before any of my corrections, before I re-read the file, before I sent the report to
team-lead. Nothing further has arrived since — specifically, nothing arrived between
sending the SendMessage report and receiving this follow-up message.

**Important precision I did not call out clearly enough in the original report:** the
`<task-notification>` block itself, as it landed in my context unprompted, did **not**
contain the "SIGNAL ARRIVED" line or the file's contents. It contained only structural
metadata: `<task-id>bmqhucrza</task-id>`, the output-file path, `<status>completed</status>`,
and a one-line summary — `"Background command 'Arm background watcher for inbox signal
file' completed (exit code 0)"`. The "SIGNAL ARRIVED / DIRECTIVE test-message-1: ..."
text that appears quoted in §4 above was **not** injected into my context automatically
— I obtained it by then choosing to call `Read` on the output-file path the notification
gave me. That was an action I took, not something that arrived unprompted. This matters:
the unprompted signal told me the watcher process exited successfully; it did not,
by itself, tell me what the file said. I should have flagged this distinction the first
time and didn't.

**2. Where did it sit relative to the report?**
Before any corrections — after report-draft-1 was already saved, interleaved with the
correction work that followed, and well before the SendMessage to team-lead. Not
alongside this current follow-up message; that arrived separately and later, with
nothing new about `bmqhucrza` in between.

**3. Did it ever fail to arrive?**
No — it did arrive, once, at the point described above. (Not applicable, since the
answer to §1 is yes.)

**4. Correction to the original write-up, given the verified timings:**
Yes. §7's two candidate explanations were (a) "the lead hadn't written the signal file
yet by the time I finished step 12" and (b) "the file existed earlier but notification
delivery is boundary-gated rather than truly async." The verified timestamps rule out
(a) outright — the file was already ~39s old by the time my report was written, so
there was no race I was winning; the delay was not on the file's side. That leaves (b)
as the standing explanation, and it's now the better-supported one: the notification
did not surface during the 12-step Bash chain even though the file had been sitting
there the whole time, and it appeared only once I hit a boundary (the return from a
completed tool call). Delivery is gated to a boundary point, not asynchronous
mid-chain — this run's evidence is now consistent with that, not merely "possibly
consistent."
