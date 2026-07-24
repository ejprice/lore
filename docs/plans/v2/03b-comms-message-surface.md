# 03b — Comms: the message SURFACE (send/drain/ack on `lore_comms`) · split from 03
size ~0.3 wu (measured; FLOOR — see 03's SPLIT note) **→split at kickoff (sizing law: ≥0.30)** · wave C · depends: **packet 03a** (which depends on 03)
law: read `comms-subsystem.md` FIRST + DESIGN-LAW §8/§5/§1/§15 · design source:
~/.claude/plans/one-of-claude-codes-nifty-garden.md · **DEPLOY: yes (BOTH containers)**

## ⚠ TAKEOVER + CONTRACT-PHASE RESET (operator, 2026-07-24)
The 03b contract phase run between `0223291` and `6bfe820` is **STRUCK** (finding #181): its
contract authors built their own reference implementations, then wrote the tests, and no
adversary re-graded either fix wave — nothing decided by that orchestrator retains authority.
Test tree reset at commit `0941aab` (verified byte-equivalent to the trusted 03a-2 close);
the struck corpus is preserved at tag `pkt03b-tainted-corpus` as raw material for a blind-diff
completeness check ONLY; its reports carry struck-banners in `receipts/2026-07-24-packet03b/`.
**What survives: direct operator rulings only** — the 2026-07-24 scope widening (03b traces
EVERY tool call, not drains only: a drain-only ordinal is a numerator with no denominator),
the R1→packet-05 deferral, and the committed-contract immutability law. Every section below
recording struck-session substance (amendments 1–10, the adversary-wave rulings, the D-items,
S-references) is HISTORY, not instruction. The fresh design authority is
`03b-design-rulings-r2.md` (blind re-derivation) once adjudicated; the trusted baseline
contract is the packet-03-era RED restored by the reset (149F/554P + 11F/85P).

### Clean-phase leads from the struck record (re-derive, never inherit)
The struck session's empirical findings are LEADS, not authority. The consolidated
checklist (9 clusters, 27 items, one-line receipts) is the POST-SUPERSESSION ADDENDUM in
design-comms-03b-r2's report (committed at root; archives to
`receipts/2026-07-24-packet03b/` at close-out) — the diff-adjudication and the fresh
adversary grade against it. **Five items are BLOCKERS (finding #182): the reset RESTORED
measured-defective committed pins** — each must be independently re-derived, and fixed only
under fresh operator authorization, BEFORE any builder is briefed:
1. the drain/fleet elision marker that rewards the wrong drain arithmetic (struck receipt:
   correct build → 2F, wrong arithmetic → 2P);
2. the `ACK REQUIRED` emit/no-emit proofs' `acked_at` monoculture;
3. the value-carried-bound pin asserting `"{msg}"`-only against a docstring banning the class;
4. the promise-scan reach-set omitting the three new render helpers + no `send.thread`
   injection case in the battery;
5. the two `test_message_ledger.py` mypy errors (`_ask`/`_answer`) that building the surface
   cannot pay.
Also lead-ruled dispositions (operator may override): WB9/E3-class conclusions from the
struck adversary wave are struck SUBSTANCE (recovery path = the hazard checklist at the
diff step, from fresh probes); the two struck-session store-reference additions (`7f23223`)
are re-probe-on-contact; `record_trace`'s production docstring is a known prose corpse
(teaches fire-and-forget) — no derivation may read it as intent.

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
  ✅ **DONE at kickoff 2026-07-24** — receipt `receipts/2026-07-24-packet03b/REPORT-scout-147-traces.md`
  (`6e175fd`); #147 → `acknowledged`. `SurrealStore.record_trace` EXISTS and is CORRECT but is
  **NEVER CALLED** — zero prod call sites in source AND in the deployed artifact; the missing seam
  is `FastMCP.call_tool` (`mcp` 1.27.2 has **no middleware API**). The READ side is FINE, proven by
  POSITIVE CONTROL (3 rows written through the real `record_trace` on TEST `:18000`, returned
  correctly by the real `trace_aggregates`). Production `:18500`, read-only: `trace` DEFINED,
  `count() = 0`.
- **SCOPE WIDENED — OPERATOR RULING 2026-07-24: 03b traces EVERY TOOL CALL, not drains only.**
  RATIONALE (the scout's load-bearing finding): a drain-only ordinal is **a numerator with no
  denominator**. Decay is an *absence* of drains across increasing turns, and an absence writes no
  rows — so drain ordinals `[1,2,3]` are equally consistent with "3 drains in 5 tool calls" (no
  decay) and "3 drains in 300" (total decay). As originally specced, this packet's telemetry
  **could not answer the question it exists to answer**, and 06 would still ship on opinion.
  Therefore 03b additionally owns:
  1. Wiring the emission at the `FastMCP.call_tool` seam — **subclass + override**, delegating to
     `super()` (the package does not do this job, so the hand-roll is the packages rule working as
     intended: minimal surface, maximal verifiability). The `fastmcp` standalone migration is a
     far larger trade → its own ledger item, met deliberately, NOT folded in here.
  2. Extending `_TRACE_FIELD_SPECS` with `option<>` agent/ordinal columns — **`DEFINE FIELD
     OVERWRITE`** per store reference §1.1 (this is the #107 trap exactly; `IF NOT EXISTS` is a
     silent no-op on an existing field). Columns MUST be `option<…>` so a non-drain trace may omit
     them. Production holds zero `trace` rows, so §1.4's back-fill hazard is nil.
  3. The ordinal rides the **existing** sequence mechanism (`_define_sequence`, `DEFINE SEQUENCE IF
     NOT EXISTS`) — a hand-rolled `trace_counter` hot row would be a third mint policy competing
     with `finding_counter`/`brief_counter` (the #102 clone defect). Do NOT overload
     `trace.session` with the agent name; a distinct `option<string> agent` is the honest shape.
  4. **THE AGENT-IDENTITY PROBLEM IS A DESIGN QUESTION, NOT A BUILDER TASK.** Only `lore_comms`
     carries an `agent` param; `lore_search`/`lore_read`/etc. carry none, and the SDK `Context`
     exposes no plain session-id string. Deriving a stable per-agent key and joining it to the
     `lore_comms register` identity is a property to INVENT → it goes to the Fable design sidecar
     BEFORE any contract is written (CLAUDE.md: a design problem never reaches a builder).
  5. **SHIP THE INSTRUMENT WITH THE FIX** — a pin that dispatches through the real server seam and
     asserts a `trace` row lands, mutation-proven, enumerating tool names as a **checked coverage
     variable** rather than asserting one hardcoded name. Without it the next refactor silently
     un-wires the emission and `traces.total` returns to 0 with every gate green — #147's own shape.

## OPERATOR AUTHORIZATION 2026-07-24 — six amendments to COMMITTED contract files
The committed contract is immutable without an explicit operator ruling (precedent `42eeedc`).
**All six below are AUTHORIZED. Every one is STRENGTHEN-ONLY — no assertion may be weakened — and
every one lands only after a MUTATION PROOF (break the production code, watch the pin go RED,
restore). The contract-adversary's P2 fixture-perturbation confirms the fix wave.**
1. **R3 — a LIVE FALSE GATE.** The committed `ACK REQUIRED` emit/no-emit fixtures never set
   `acked_at` on a directive, so they are an **`acked_at` monoculture**: a build keying the trailer
   on `grade == directive` ALONE, ignoring `acked_at IS None`, **passes the committed proofs**. Add
   the discriminating pin. (Parameter-value monoculture, the class this repo has now paid for four
   times — a fixture that cannot distinguish the correct build from a plausible wrong one is
   decoration.)
2. **R5 — a SECOND live false gate.** The value-carried bound's pin asserts `"{msg}"`-ONLY while its
   own docstring bans the whole class. A failure message promising a check the assertion does not
   perform is a false gate (P2, 2026-07-14). Closed by S3's placeholder-only ∀-ban pin.
3. **R6** — the reach-pin `expected` set omits the three new helpers (S1 instrument item 2).
4. **R7** — `send.thread` has no injection RenderCase in the committed battery; mandatory once
   S4.1's question line puts `thread` into the send render for the first time.
5. **+6. The two mypy errors in `test_message_ledger.py`** — 03a's GREEN, CLOSED contract.
   ⚠ **Residual 8 of the design doc is WRONG on exactly these two.** It says global mypy-zero is
   "structural… building S4's surface pays them". That holds for **34** of the 36 (forward refs to
   `_render_comms_*` / `comms(...)` kwargs). It does NOT hold for these 2, which are
   `Returning Any from function declared to return "int"` in the `_ask` / `_answer` HELPERS
   (`ledger: Any`). **Building the surface will not pay them.** They need this authorized fix, or
   03b misses the global mypy-zero it owns.

### Amendments 7–9 — AUTHORIZED 2026-07-24 (found BY the contract wave, same standing terms)
7. **D1 — THE COMMITTED CONTRACT REWARDED THE WRONG BUILD.** `_PROOF_LIST`'s fleet-elision marker
   `"— re-run with limit=5"` is a value-bearing but **line-INCOMPLETE** marker. Under S4.2's ruled and
   CORRECT drain arithmetic (`next_limit = more`), the drain fixture renders
   `+5 more unread — re-run with limit=5` — **containing the fleet marker verbatim** — so the
   cross-satisfaction pin fires. **MEASURED against a reference build:** correct arithmetic → **2 failed**;
   fleet's `shown + more` (the dishonest re-ask) → **2 passed**. A builder implementing S4.2 correctly was
   PUNISHED and one cloning fleet's arithmetic REWARDED. This is the "spec/contract prescribes the bug"
   class (PKT-28 C1 §5.1) live in the committed contract, invisible only because `_render_comms_drain`
   does not exist yet. **FIX = the ROOT CAUSE:** promote the marker to the full rendered line
   (`+3 more — re-run with limit=5`). Renumbering the drain fixture was REJECTED — it conceals the weak
   marker and the collision returns the next time two fixtures' arithmetic aligns.
8. **D5 — the default that CAUSED R3.** `_p03_entry`'s `acked_at=None` default is what made the committed
   proofs an `acked_at` monoculture. Amendment 3 added the discriminating pin; this removes the cause.
   Four call sites gain `acked_at=None` explicitly. (Repo law already bans defaulting a branched-on
   parameter — this is that law applied to the fixture that proved it.)
9. **D6 — the `test_message_ledger.py` freeze is WIDENED** so 03b owns inherited 03a-2 delta row 8's
   `[fake]`/`[real]` LEDGER legs for R5/R6, which were otherwise UNOWNED. The dispatcher-level R6
   convergence pin STAYS (it is the surface-layer claim, mutation-proven); the ledger legs are the layer
   beneath it, not a replacement. The freeze widens for row 8's legs ONLY; a tenth edit still stops.

### D2 / D3 — RULED BY THE DESIGN SIDECAR 2026-07-24 (both were defects in its OWN rulings)
- **D2 → READING A.** `_render_comms_drain` gains a **REQUIRED `session: str`** kwarg (house shape,
  matching `_render_comms_send`). S4.2 had stated a signature that made its own branch 3 unreachable.
  **Reading B REFUSED with reasons, and the reason binds the builder:** most fleet traffic rides the
  session-default thread, so under B the subsystem's highest-volume render carries a ` (thread wave7)`
  cell on EVERY row — teaching nothing, and **destroying the signal S5's teaching leans on** (a thread
  label means "a deliberate conversation" ONLY if default-thread rows stay bare).
  ⚠ **The kwarg is REQUIRED, never defaulted** — a defaulted branch-comparand lets any call site
  silently make the branch unreachable again (the fixture-monoculture hazard, at the SIGNATURE layer).
  **Required pin: the discriminating pair** — same fixture; entry on the default thread renders NO
  thread cell, entry on a non-default thread renders one. The battery's `drain.thread` case stays valid
  (hostile values ≠ `"wave7"`, so the cell renders and sanitisation is still exercised).
  → **AMENDMENT 10** (mechanical: five committed drivers gain `session="wave7"`).
- **D3 → CONFIRMED, with a LARGER concession than the escalation claimed.** The sidecar executed the
  check before conceding: its prescribed `_has_literal_text` form was a false gate in **BOTH** directions
  — RED on the correct build (`_PROMISE_FREE`'s `" "` separator) **AND BLIND TO THE VERY CLASS THE BOUND
  BANS**, because `_has_literal_text("{msg}")` returns **True** (named-field characters read as literal
  text), so the assert would have waved `"{msg}"` straight through even where satisfiable.
  **A doubly-broken instrument, prescribed by a design doc, caught only by the contract author's
  satisfiability receipt against a correct build.** `_is_placeholder_only` (≥1 format field, nothing but
  whitespace outside the fields) is the ruled form: bans exactly the docstring's class, admits `" "` and
  `"#{}"` with **no exemption list to rot**, and the `" "`-discrimination positive control pins it.

### ADVERSARY WAVE — telemetry contract graded INSUFFICIENT (2026-07-24)
**Eleven wrong builds survived the frozen telemetry contract at 41 passed / 0 failed.** Receipt:
`REPORT-adversary-telemetry-03b.md` (`0921157`). Two findings changed rulings:
- **WB9 — S7's self-attack table had an UNENFORCED row.** `caller = str(id(session))` passes EVERY
  S7 pin (alnum, stable within a session, distinct while two sessions COEXIST) and collapses **400
  sequential non-overlapping sessions into 17 distinct keys (383 collisions)** — CPython recycles
  `id()`. **The pinned quantifier was "distinct while coexisting"; the needed property is "distinct
  ∀ TIME."** A self-attack row promising a property of the MECHANISM while the pins bound only
  BEHAVIOUR is the false-gate class, inside the design's own instrument.
  → **RULED:** the caller key must derive from a source that **CANNOT RECYCLE** (fresh process
  randomness / a monotonic mint) — never object identity, an address, or any recycled value. MP3's
  two halves (uniqueness-across-lifetimes + no-retention-of-finished-sessions) **INTERLOCK**: a
  retaining dict passes uniqueness but fails retention; weak retention forces recycling, so an
  identity key then fails uniqueness. Either alone is escapable; the pair is not.
- **E3 STANDS — but its ground 3 was "pure hope", and the adversary was right.** "The schema rejects
  future mint-less writers" could never be self-enforcing, because **the schema is code a builder can
  edit.** MEASURED incentive to undo the ruling: `seq int` (correct) → contract 41/41 + **7 committed
  pins RED**; `seq option<int>` (wrong) → contract 41/41 + **2 RED**. → **FIX (in scope): a contract
  pin asserting `seq` is `TYPE int` NOT `option<int>`, mutation-proven** — the flip becomes
  1-RED-in-contract and the five-test incentive dies.

### OPERATOR SCOPE GRANT 2026-07-24 — SEVEN amendments in FOUR suites OUTSIDE 03b
`test_surreal_schema.py` · `test_surreal_store.py` · `test_surreal_fakes.py` · `test_mcp_server.py`.
Strengthen-only, each mutation-proven.
- **2 ordinary corpses** (old-world `hit_count TYPE int`; the exact 7-name `record_trace` signature).
- **4 `TestTraceRoundTrip` pins** doing raw `CREATE trace` with no mint → amend to supply `seq`.
  **These are writers omitting the mint — the class `seq int` exists to reject. THE GUARD WORKING IS
  NOT THE GUARD FAILING.**
- **The flagship #107 dirty-store migration pin — AMEND TO SHARPEN, NEVER TO WEAKEN.** It keeps
  everything it asserts today (old-shaped row survives the new DDL, still readable) and GAINS the
  §1.4 truth: the old row is UPDATE-poisoned (the accepted append-only-shielded bound with its named
  trigger) and new writes must mint. **Why this beats `option<int>`, verbatim from the ruling:** *a
  dirty-store migration pin that surfaces a dirty-store consequence LOUDLY is the pin doing its job.
  The alternative would green that pin by making the schema SILENT — seq-less rows admissible
  forever, from any writer — and the flagship invariant would be certifying a hole as health.*
  ⚠ If it cannot be amended without weakening, the wave STOPS.
- **MP9 RULED — nothing to build:** `trace.session` records **what the CALL DECLARED, never what the
  server inferred** (populated iff the call carried the fleet session; NONE = the call declared
  nothing). Deriving it for generic rows is REFUSED — it resurrects the S7-refused caller→identity
  map through a column and makes one field an unmarked mixture of declared facts and guesses.

### STANDING AUTHORIZATION — operator, 2026-07-24
**Further amendments to committed contract files need NO individual ruling when ALL THREE hold:**
(a) **required by a design ruling** from the sidecar, (b) **MECHANICAL** — preserves every existing
rendered value and changes NO assertion, and (c) **MUTATION-PROVEN before landing.** Each is reported in
the packet close-out, not round-tripped. **Anything that is a judgement call, a WEAKENING, or a newly
found defect still goes to the operator individually** — the grant covers mechanical consequences of
rulings, never the rulings themselves.

## Scope OUT
- Everything packet 03 owns (schema, `messages.py`, concurrency, the relation-table flip).
- **R1 — drain-row `question=true` markers: DEFERRED TO PACKET 05 by operator ruling 2026-07-24**,
  with 05's Scope IN carrying the named decision point (a deferral without one is a can-kick).
  Priced, not narrowed: the marker needs `question` on `InboxEntry` — an ORACLE + model change with
  two-suite blast radius — for a teach 05's await/story work re-shapes anyway. The clearing rule is
  still taught SENDER-side (S4.1) and STATICALLY (S5); only the per-row recipient marker waits.
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
- `./scripts/typecheck.sh` → **36 errors (31/3/2), zero in any production module.** The 2026-07-23
  operator ruling defers **global mypy-zero to the END of 03b** — this packet is where that debt is
  paid.
  ⚠ **CORRECTED 2026-07-24 (lead re-measured at kickoff; the inherited half-claim was FALSE).** This
  line and the INDEX both said the 36 were *"ALL in the two RED contract test files"*. The
  `zero in production` half is TRUE and re-confirmed; the other half is NOT. The split is
  `test_comms_tool.py` **31** · `test_comms_promise_registry.py` **3** · **`test_message_ledger.py` 2**
  — and that third file is packet 03a's **GREEN, CLOSED** contract (180 passed / 0 failed), not a RED
  03b file. Both are `Returning Any from function declared to return "int"` in the `_ask` / `_answer`
  test HELPERS (they take `ledger: Any`), not in any pin. **Consequence: reaching global mypy-zero
  requires editing a COMMITTED CONTRACT FILE from a closed packet** — the class of edit that needed
  explicit operator authorization at `42eeedc`. Get that authorization before touching it; do not let
  a builder treat it as a drive-by.
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
