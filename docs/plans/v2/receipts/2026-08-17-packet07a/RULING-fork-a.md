# Operator ruling — packet 07a FORK A + two secondary decisions

Date: 2026-08-17. Ruled by: operator, via `lead-07a-1`, in response to `REPORT-contract-07a-1.md`
§3 (FORK A) and §5/§7 (decisions-needed 2/3). Graded-at: `995a358` (contract author's HEAD-at-report;
unchanged at ruling time).

## FORK A — RULED: A1 (adjudicate FIXED, defer the polish)

The #164/#250 "store bounce wedges forever, only a container restart heals it" premise does **not**
reproduce on HEAD — `contract-07a-1`'s 20-consecutive live full-bounce drill against spike-surreal
3.2.4 (`scripts/probe_store_recovery_07a.py`, transcript
`docs/plans/v2/receipts/2026-08-17-packet07a/probe-store-recovery-transcript.txt`) shows 20/20
self-heal on the next call after a full server restart. Root cause: packet 05a-ii's
`_SDK_AWAIT_BOUNDARY_ERRORS = (*_CONNECTION_ERRORS, KeyError)` already closed the hole that produced
the July wedge (the in-flight `KeyError` used to escape `run_query` without dropping the dead handle;
it is now caught and dropped like any transport fault).

**Ruled: A1.** Ship:
- The measurement + the committed 20-consecutive live drill as the packet's deploy-smoke instrument
  (satisfies the spec's literal "20-consecutive bounce-recovery, no container restart" ask).
- Resolve #164/#250 as **fixed-by-05a-ii**, with a named re-open trigger (below).
- **No new reconnect-and-retry code.** The Option A2 design (§3.1 of the contract report — a shared
  `ReconnectRetrySignal`, pre-send/idempotent-only, at-most-once-preserving) stays **designed but
  unwritten**.

**Named re-open trigger (measure-then-tune, per the deferral law):** packet 16 (#249's RSS
restart-policy). When store restarts become a *routine, scheduled* operation rather than an
occasional engine-upgrade event, the "1 sacrificed call per restart × every active consumer" cost
becomes real and measurable — re-open FORK A then, with fleet/production telemetry in hand, rather
than building A2 speculatively now against a currently-cosmetic gain that would partially reverse
`retry_on_conflict`'s at-most-once write-safety guarantee.

## #128 render wording — RULED: distinct contention line

A contended batch item's per-item failure line reads **`FAILED — store contention, safe to retry
this item`**, distinct from the domain trio's generic `FAILED — {reason}`. Rationale (Trust
Doctrine): contention is genuinely retryable — the connection is healthy, this row just lost a
write-write race — where a domain rejection (not-found / illegal-transition / bad value) is not. The
distinct wording tells the caller which failures are worth retrying without over- or under-claiming.

Contract action: tighten the 3 existing RED `#128` pins in `test_mcp_server.py` to assert this exact
line for the contention case (they currently assert the CONTINUE property + "a FAILED line, not an
ABORTED line" without pinning the suffix — now pin the suffix too).

## #127 tripwire pin — RULED: add the frozen-caller-set pin

Add the AST-scan pin asserting `scout.CommandSubscriber._ensure_connection`'s callers are exactly
`{run, process_pending_once}` — the corrected invariant (contract author found `process_pending_once`
is a 2nd in-code caller, test-only, zero production callers, so "sole PRODUCTION driver" is the
correct claim, not "sole caller"). A real 3rd (production) caller reddens it, giving #127's
re-open trigger ("any change that adds a second caller of `_ensure_connection`, or makes scout
construct its own socket") a mechanical tripwire instead of a prose-only bound. Do not add the
connect lock itself — an untested lock on a path with no concurrent production driver is exactly the
scope the original #127 decision declined; it stays latent.

## What does NOT change

- #126 verdict: RENEW (trigger not fired), with the rider that it must be re-adjudicated against the
  shipped 07a seam — moot under A1 since A1 makes no seam change, so the rider does not fire this
  packet.
- #250 healing-scope + #308 findings: settled as reported (§2 of `REPORT-contract-07a-1.md`) — no
  further action beyond resolving the findings at close-out.
- Store-reference §3 one-line clarification (contract report §8): flagged for the lead to apply
  (docs-only, outside the contract author's writable set this phase).
