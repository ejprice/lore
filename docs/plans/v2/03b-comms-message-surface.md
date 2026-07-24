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
**SECOND READ (binding, added at 03a-2's close): `03a-2-consume-path-design-rulings.md`** — six
design rulings and a consolidated delta table, several of which are THIS packet's work. See
§"Inherited from 03a-2" below; a 03b that does not open that doc will re-author pins that already
exist and will miss the index window.

**Predecessor state, MEASURED at `bd524f0` (2026-07-23) — do NOT expect a green tree at start:**
- Packet **03** (store) DONE `df59f76`; **03a-1** (send + drain) DONE `2d1f75d`→`13da377`;
  **03a-2** (ack + derived waiting) DONE `853a95b`→`f04729c`. **03a is CLOSED.**
- `test_message_ledger.py` → **180 passed / 0 failed / 12 skipped** (all skips `[fake]`-leg).
- `test_retry_seam.py` → **503 passed**. `MessageLedger` is discovered by the seam enumerator and
  every SDK call site rides the shared driver — **keep it that way; the gate fails CLOSED.**
- ⚠ **`test_comms_tool.py` → 149 failed / 554 passed**, and `test_comms_promise_registry.py` also
  RED. **That is THIS packet's contract.** Measured identical before and after 03a-2's changes.
- `./scripts/typecheck.sh` → **36 errors (31/3/2), ALL in the two RED contract test files above,
  zero in any production module.** The 2026-07-23 operator ruling defers **global mypy-zero to the
  END of 03b** — this packet is where that debt is paid.
- spike-surreal `:18000` up (`:18500` is PRODUCTION); the render scanners' current reach confirmed
  (#145 — if renders have moved out of `server.py` since, STOP).

**⚠ FINDING #175, read BEFORE writing any edge write:** `UPDATE <edge> … WHERE in IN $ids` **silently
matches ZERO rows** on 3.2.1 — no error — while the identical `SELECT` predicate matches; adding an
`out = $x` conjunct makes it work. Mechanism UNVERIFIED. Shipped code is safe (every such UPDATE
carries `out = $agent`), but any message-scoped edge write (a retract/redact verb, a `to`-edge GC
sweep) will report success and do nothing.

### Inherited from 03a-2 (design-ruled; delta table rows 1–11)
1. **Both `message` indexes, BEFORE this packet's deploy, as their own one-concern commit** —
   `(seq)` and `(sender, question)`. The window argument is decisive and expires here: production
   carries **zero** `message` rows until 03b deploys, so the index build is free **exactly once**.
   `IF NOT EXISTS` per store reference §1.1. `seq` is **PLAIN, not UNIQUE** (a strikeable divergence
   from the approved design, with a named re-open trigger).
2. **Bound `awaiting_answer`'s deliveries SELECT** by the question threads / min-seq (a
   semantics-identical superset), with an EXPLAIN receipt settling whether `(out, seen_at)` covers
   the `out` prefix, plus 20-consecutive re-runs of the send + ack concurrency pins after the
   schema change.
3. **New pins:** duplicate-seq in one batch (incl. a non-adjacent `[s1,s2,s1]` variant) ·
   thread-level debt in BOTH directions · read-order + the zero-questions short-circuit, with the
   KNOWN BOUND docstring and its re-open trigger.
   ⚠ **NOT the self-addressed pins — those SHIPPED in 03a-2** (`f04729c`); do not re-author them.
4. **BINDING RENDER LAW:** ack-nudges key on `acked_at`, **never** `seen_at` (an acked directive
   must never re-nag; the two-counter footer is the confirmed required shape); queue counts key on
   `seen_at` and say **"unread"**, never "unactioned", and must agree with what `drain` then serves.
5. **Teaching clauses in the served render** (the consumer is an LLM; the render is where it learns
   the contract): `already_acked` on a duplicate occurrence, and the waiting line's clearing rule.
   Separate debts belong on separate threads — taught STATICALLY in the instructions block, not by
   a send-time thread scan.
6. **Any future ORACLE change** (`_message_fakes.py`) is a contract-author + adversary edit, never a
   builder drive-by — and its satisfiability receipt must cover **BOTH** consumer suites
   (`test_message_ledger.py` AND `test_comms_tool.py`; the single-consumer premise was measured false).
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
