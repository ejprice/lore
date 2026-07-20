# Receipts — agent comms measurement, 2026-07-19/20

Raw agent reports behind `../../2026-07-19-agent-comms-measurement.md`. Preserved here because
repo law deletes every root-level `REPORT-*.md` before an image build, and these are RESEARCH
records rather than packet scratch.

| file | what |
|---|---|
| `REPORT-consult-fable.md` | Fable design-informant answer (Q1 receiving end, Q2 as orchestrator) |
| `REPORT-consult-opus.md` | Opus informant + the POSTSCRIPT that discounted the consult's own convergence and named the decay measurement |
| `REPORT-exp-selfarmed-poller.md` | Run 1 — **CONFOUNDED, do not cite its null**; chain ended before the signal existed |
| `REPORT-exp-selfarmed-poller-2.md` | Run 2 — pre-placed signal; delivered before step 2 with 11 calls queued, no `end_turn` |
| `REPORT-exp-selfarmed-poller-3.md` | Run 3 — timed watcher; delivered after step 13 of 15, deep in chain |

## Two answers are MISSING, and their absence is itself data

- **consult-sonnet** delivered by teammate message only and wrote no file — its content survives
  solely in the session transcript and in the quotations in the parent document. Recovered by luck
  of the channel, not by design.
- **consult-haiku NEVER DELIVERED.** A `SendMessage` asking it to write its answer to a file
  returned `success: true` and produced nothing, twenty-plus minutes on. Its answer is lost.

Both losses have the same cause, and it is the orchestrator's: the spawn brief said *"your final
message IS the deliverable"* — a brief with **no durable address in it**. The fix is not "make
agents write files"; it is **make the deliverable's address part of the brief**. That this happened
during a consult ABOUT losing messages is the session's most transferable finding.
