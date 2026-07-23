# 03a-2 — Comms ledger: DRAIN / ACK + derived waiting state · sub-packet 2/2 of 03a
size ~0.18 wu · wave C · depends: **03a-1** (SEND path + foundations) · **DEPLOY: NO — test-only** ·
**CLOSES 03a**
law: read `03a-comms-message-ledger.md` (shared 03a reference) + `comms-subsystem.md` +
DESIGN-LAW §8/§5/§1 · **FIRST READ (repo store law):
`docs/reference/surrealdb-31-capabilities.md`** · task `96f9f3a0003049b8bd4cb44a35b3ddef`

## Mission
Build the CONSUME path (`drain`/`peek`, `ack`, `awaiting_answer`) onto the `messages.py` that 03a-1
committed, taking the WHOLE contract (all 180 pins) green. The `[real]`-tier leg is the largest
residual risk (adversary §7.8, ungraded until the module existed) — the cold audit grades it.

## Scope IN
- **`drain` / `peek`** — a windowed SELECT over my unstamped `to`-edges + a scoped CAS stamp of
  EXACTLY the served window (`peek` stamps nothing; elided rows stay unread — NO cursor arithmetic);
  `total_pending` / `directive_pending` computed over the WHOLE set, never the capped window;
  scoped to the caller (`AND out = $me`), with a cross-session negative.
- **`ack`** — a write-once CAS (`UPDATE … WHERE acked_at IS NONE AND out = $me`) + a disambiguating
  follow-up SELECT returning the four-way `AckOutcome`
  (`acked`/`already_acked`/`unknown_message`/`not_addressed`); a batch reports every seq's own fate;
  a note lands ONLY on the CAS-won edge; a NEGATIVE pin for the ownership rejection (invisible in the
  raw CAS return — the four-way ambiguity).
- **`awaiting_answer`** — the DERIVED waiting state (ruling 9): awaiting iff an unanswered question
  thread exists; `asked_at` IS the question's own `created_at` (no stored column); the derivation
  **WRITES NOTHING** (pinned structurally); the OLDEST unanswered question is reported; an answer on
  the SAME thread clears it with **no write to the agent**; the KNOWN BOUND (an out-of-band answer
  leaves the state waiting until relayed) is pinned with its re-open trigger.
- **ack-side concurrency ≥16-way (exactly one winner), 20 CONSECUTIVE green runs.** Both the
  drain-CAS and the ack-CAS MUST ride the shared `_txn.retry_on_conflict` driver — **prove by
  MUTATION** (move the shared marker; every caller's pin goes RED). Routing through the driver while
  classifying the conflict locally is a private copy wearing the shared name. The retry-seam
  enumerator drives every NEW SDK call site and fails CLOSED on an undriven one.

## Scope OUT
All of 03b (renders / dispatch / promise proofs / drain telemetry / deploy); packet 04
(`blocks`/fleet columns/`_comms_footer`); packet 05 (`await`/`story`/`since=`).

## Pin classes (03a-2's target — takes the whole 180 green)
`TestDrainStampsExactlyWhatItServed` · `TestPeekStampsNothing` · `TestDrainIsScopedToTheCaller` ·
`TestAckIsWriteOnce` · `TestAckDisambiguatesTheFourWayEmptyReturn` ·
`TestConcurrentAcksOfOneEdgeProduceExactlyOneWinner` · `TestTheWaitingStateIsDerived` ·
`TestTheDerivedWaitingStateKnownBound`.

## Entry check
03a-1 DONE + committed (send path green, the module skeleton + full type surface in place); the
drain/ack/waiting pins RED for the right reason (`NotImplementedError`, NOT an import error);
spike-surreal :18000 healthy; task `96f9f3a0` in play.

## Exit
ALL 180 pins green (whole contract) with a passed-COUNT; `scripts/typecheck.sh` per-file clean +
ruff + `test_retry_seam.py` green; **cold REFUTE audit GRADING THE `[real]` LEG** for the consume
path; one-concern commits at natural boundaries; **NO deploy** (03b ships the surface + deploys
both); INDEX row + Log + ledger row done. Concurrency 20 consecutive runs — a single green run never
clears it. On close, 03b (successor `618cd45d`) unblocks.
