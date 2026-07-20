# 04 — Comms: blocks edge + fleet columns + footer · formerly PKT-28 phase C2c
size ~0.20 wu · wave C · depends: packet 03
law: read `comms-subsystem.md` FIRST + DESIGN-LAW §8/§5/§1 · DEPLOY: yes (both)

## Mission
Close the C2 surface: the task-DAG `blocks` edge, the fleet view's message columns, the
pending-traffic nudge footer, and the dangling-edge hardening.

## Scope IN
- `blocks` task DAG edge (`task->blocks->task`), mirrored from `task.blocked_by` inside
  the existing write txns; invariant tests pin edge≡blocked_by + acyclicity; transitive
  reads use the recursive idiom (`@.{1..n}->blocks->task`, always TIMEOUT).
- Fleet unread/directive columns (per-agent unread + unacked-directive counts — computed
  over the WHOLE set their label claims, per the spec's counting law).
- `_comms_footer`: lore_tasks/lore_claim_task/lore_findings mutations append one line
  when traffic pends.
- **#105** — RELATE does not validate its endpoints: guard every edge-writing verb so a
  bogus agent_id is a teaching error, never a dangling read-receipt.
  ⚠ **THE EXPOSURE WENT LIVE IN PACKET 03 — THIS IS NO LONGER LATENT WORK** (operator-ruled
  2026-07-19: *"we're the only consumer, and we're local"* — deferred DELIBERATELY, with the
  risk accepted, NOT because it is still theoretical).
  **What packet 03's kickoff probe measured** (`REPORT-probe-pkt03-store.md` PROBE 1, and now
  reference §4): the engine validates **NEITHER `in` NOR `out`** — the recorded `in`-only half
  was the *safe* half. Packet 03's `send` takes recipient NAMES from a caller, so the
  caller-supplied side is `out`. A bogus recipient writes a permanent edge, and
  `SELECT ->to->agent` lists the ghost as a **first-class recipient** while the agent table
  shows it never existed. A reader can only tell by projecting a field / `FETCH`ing and
  checking for `None`.
  **What packet 03 shipped as mitigation**: its own scoped "unregistered recipient = teaching
  error" app-level check on `send`, plus a typed `TYPE RELATION IN message OUT agent` (which
  catches only wrong-**table** endpoints, never a non-existent record of the right table).
  **What is therefore STILL OWED HERE**: the structural half — the guard must cover EVERY
  edge-writing verb, not just `send`; `BriefLedger.publish(agent_id=...)` still takes a BARE
  STRING; and the covering pins must use a **negative fixture** (an identity that does not
  exist must be REJECTED), since a fixture where every endpoint is registered cannot
  discriminate. Widen #105's own text from "latent — we never hard-delete" when resolving it.

## Scope OUT
- await/story/rollup/hooks (packet 05); protocol + drill (06).

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
Packet 03 deployed; `lore_findings` → #105 open; the edge≡blocked_by invariant's
fixture set includes a CYCLE attempt (3.1.5 fixed cyclic node-drops — pin it).

## Exit
Full gates + cold audit + deploy BOTH + smoke: a blocked task chain renders its
critical path; a bogus-recipient publish/send teaches instead of dangling; #105
resolved; INDEX row + Log.
