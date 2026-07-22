# 03b — Comms: the message SURFACE (send/drain/ack on `lore_comms`) · split from 03
size ~0.3 wu (measured; FLOOR — see 03's SPLIT note) **→split at kickoff (sizing law: ≥0.30)** · wave C · depends: **packet 03a** (which depends on 03)
law: read `comms-subsystem.md` FIRST + DESIGN-LAW §8/§5/§1/§15 · design source:
~/.claude/plans/one-of-claude-codes-nifty-garden.md · **DEPLOY: yes (BOTH containers)**

## Why this packet exists
Split from packet 03 at kickoff (operator-ruled 2026-07-19) on the contract author's
measurement: the contract was written IN FULL and then sized — **296 pins, 0.6–0.8 wu
against a 0.25 sizing**. Packet 03 took the durable core (test-only); this takes the
served surface and owns the deploy. **The contract is ONE file covering both** — pin
groups are labelled, not forked.

## Mission
Put the message graph on the wire: three new `lore_comms` actions over the `MessageLedger`
packet 03 proved at contention, with renders that satisfy the promise instruments packets
02/02a shipped. This is the packet where an agent can finally be sent something durably.

## Scope IN
- `send` / `drain` / `ack` actions on `lore_comms`: dispatcher wiring, param validation,
  the heartbeat touch (inherited — one site, `spec.requires_registration`), the four
  tool-level structural pins, and the served INSTRUCTIONS block.
- All renders — send confirmation, the numbered drain list with its counted elision, the
  `ACK REQUIRED` trailer, ack confirmation. **They live in `server.py` under the existing
  `_render_comms*`/`_comms_*` prefix (packet 03 ruling 5): three of the five render
  scanners are keyed on that PATH and that NAME PREFIX (#145), so a render anywhere else
  is invisible to the promise registry and stays green.**
- Promise-registry entries + `PromiseProof` emit/no-emit proofs + non-cross-satisfied
  markers for every new template literal. `ACK REQUIRED` reads as a mechanism promise on
  its face and needs all three. ⚠ Check `test_comms_promise_registry.py:2088-2115`'s
  KNOWN BOUND first — a bare `{...}` drain template plausibly pulls its re-open trigger,
  and the bound must close BEFORE that classification, not after.
- Hostile render fixtures MANDATORY (bodies are stored free text written by other agents:
  newlines + a row-shaped forgery line + backtick runs). Single-line-only fixtures are the
  documented way this defect class stays green.
- **DRAIN TELEMETRY — REQUIRED, and it is not optional decoration (task 05b5cd71, #147).**
  Every drain records the calling agent and a monotonic call ordinal, so drain frequency
  is derivable against turn index from day one. RATIONALE: a 4-model consult unanimously
  predicted that pull-based comms DECAY (an agent has no background attention; a standing
  "check your messages" obligation decays within a few tool calls, fastest when the task
  is going well). The Opus informant then discounted that unanimity — three related models
  share priors, so agreement measures how we MODEL ourselves, not how we BEHAVE — and named
  the real instrument: log every pull against turn index and look for decay. **Packet 06
  must decide forced-drain on that CURVE, not on the prediction.** If the telemetry is not
  built here, the measurement cannot happen and 06 ships on opinion.
  ⚠ FIRST: `lore_index` currently serves `traces.total = 0` after heavy tool use (#147) —
  diagnose whether the trace path records at all BEFORE designing this against it.

## Scope OUT
- Everything packet 03 owns (schema, `messages.py`, concurrency, the relation-table flip).
- `blocks` mirroring, fleet message columns, `_comms_footer` (04); await/story/`since=` (05);
  brief-base v3 + hooks + THE DRILL (06).
- **The forced-drain mechanism itself is packet 06's** — this packet ships the telemetry that
  lets 06 decide it, and must NOT pre-empt that decision.

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this packet
reads the store; cite it, never re-transcribe.
Packet 03 DONE (schema + `MessageLedger` green at ≥8-way, 20 consecutive); the contract's
surface pin groups RED for the right reason at HEAD; spike-surreal up; the render scanners'
current reach confirmed (#145 — if renders have moved out of `server.py` since, STOP).
**COVERAGE-PREMISE CHECK (INDEX law, 2026-07-19):** this packet's scope excludes render
hygiene on the grounds that packets 02/02a's instruments cover it. **PROBE THAT AT KICKOFF** —
one receipt showing a new `_render_comms*` helper in `server.py` is actually seen by the
promise scan. 02a's own scope rested on an untested coverage premise and gave a real hole a
formal alibi.
**#143 adjudication (slotted 2026-07-22):** the sibling-branch marker mechanization ("a
marker must not survive a SIBLING-BRANCH render of the same helper") — adjudicate whether
the committed contract's promise-proof pins already deliver it for the new templates; if
not, pin it here or record the bound with a re-open trigger. It sits beside the
`test_comms_promise_registry.py:2088-2115` KNOWN BOUND this packet already checks.

## Exit
Full gates + cold REFUTE audit + **contract-adversary on the surface pin groups** (DESIGN-LAW
§15) + deploy BOTH (rebuild + recreate, never restart) + live-wire smoke: a
`send → drain → ack` round-trip on the real store including a broadcast to all non-retired
agents and a hostile body staying inside its fence. INDEX row + Log + ledger rows done.
