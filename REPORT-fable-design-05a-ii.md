# REPORT-fable-design-05a-ii — the `await` verb, contract-ready requirements + forks

brief-base v11 read
brief project v7 read

## Summary block
- **State:** done — the await design is RECONSTRUCTABLE from the surviving sources; requirements derived with section-exact citations. Two genuine gaps flagged as OPERATOR FORKS (neither is invented here).
- **Deviations:** none. (Writable set honoured: this report only.)
- **Capability check:** all tools present; lore index reachable; the now-deleted plan file `~/.claude/plans/one-of-claude-codes-nifty-garden.md` is confirmed GONE — every claim below traces to a SURVIVING source (the two archived reports, the two packet docs, the store reference, the shipped code), never to the missing plan except where my own PRIOR report transcribed a plan fact, which I mark as such.
- **Packages considered:** none — no mechanism specified. `await` REUSES shipped lore code (the `CommandSubscriber` LIVE-primary/poll-fallback shape, the reshaped `drain` SELECT, `awaiting_answer`/`WaitingOnAnswer`, the `render_attributed`/fence seam); it hand-rolls no second copy of any (ONE IMPLEMENTATION). The SDK (`surrealdb` 2.0.0) is `keep` — it is the project SDK, its LIVE + socket-drop behaviour already probed (`REPORT-probe-await-05a-1.md`).
- **Graded:** design review — no builder artifact graded. Ground-truth reads (all at HEAD `83dba44`, branch `feat/surreal-unification`): `messages.py::{drain, awaiting_answer, WaitingOnAnswer, InboxEntry, MessageDrainResult}`, `scout.py::CommandSubscriber` (`live_select_statement`/`run`/`_serve`/`_consume_live`/`process_pending_once`), store ref §10 + §3, DD-3.e.
- **Decisions-needed (operator forks — surfaced, none decided here):**
  1. **F1 — does `await` STAMP or NOT?** Blocking-drain (stamps seen) vs blocking-peek (stamps nothing, caller drains for real). STRONG lean: **NOT-stamp (peek+wait)** — stamping puts await on the DD-4.c/#214 loss path and contradicts the forgery pin. Contract-blocking: the return shape and the pins differ.
  2. **F2 — the ≤55s bound: fixed constant vs caller param.** Lean: **fixed named constant, no timeout param** (the plan's recorded signature was `await(agent, thread?)` — no timeout arg; 55 sits under the ~60s tool-call ceiling). Reconstructable-with-caveat (rests on my prior's transcription of the deleted plan).
  3. **F3 (re-affirm, not new)** — Q5(ii) LIVE-WHERE key = **agent-id only, never `thread`** (DD-3.e). Now EMPIRICALLY backed by the probe; recommend ratifying.
- **Receipt pointers:** the 6 contract requirements §A.1–A.6 · Q5(ii) re-affirm §B · Opus-4.8 leg §C · consolidated forks §Forks · contract-author pin list §Pins.

Sources cited section-exactly, never re-transcribed:
`docs/plans/v2/05-comms-await-story.md` (Scope IN await bullet; DD-2.a; DD-4.c; #214/#190/#183/#195 routes; Exit),
`docs/plans/v2/comms-subsystem.md` (:75 await row; :177–182 Honest limits),
`docs/plans/v2/receipts/2026-08-08-packet05aiii/REPORT-fable-design-05a.md` (§Q1 05a-ii def; §Q5(i)/(ii)/(iii); §Cross-cutting — MY MAIN PRIOR),
`docs/plans/v2/receipts/2026-08-09-packet05ai/REPORT-probe-await-05a-1.md` (PROBE 1 VERDICT FIRES; PROBE 2 KeyError shape; filtered-WHERE discriminates),
`docs/reference/surrealdb-31-capabilities.md` (§10 LIVE SELECT; §3 socket-drop ~:420–427; §10 record-ids ~:902–904),
`docs/plans/v2/03b-deferred-design-rulings.md` (§DD-3.e :306–315),
and the code symbols in the Graded line.

---

## A. The await contract — reconstructable, with two flagged gaps

**Verdict: RECONSTRUCTABLE.** The mechanism is fully specified by (i) the surviving one-liners
in `05-…await-story.md` Scope IN and `comms-subsystem.md:75`, (ii) my prior design doc's §Q5
(the Consumer-Law review, which is the real design), (iii) the shipped `CommandSubscriber` as the
reference shape await mirrors, and (iv) the live probe that upgraded LIVE-on-edge from assumption
to verified. The DELETED plan file adds nothing these don't carry, with exactly two exceptions,
both flagged as forks (F1 stamp-semantics, F2 the ≤55s param-vs-constant) — neither is invented.

### A.1 — The state-machine step sequence

Six steps. Steps 1 and 4 are the two the sources call out as load-bearing and easy to get wrong.

1. **SNAPSHOT-FIRST drain SELECT (read-only).** On entry, run the drain read for `agent_id`
   (the 05a-i-reshaped `drain` SELECT/projection — `messages.py::MessageLedger.drain`). If it
   yields unseen traffic, **RETURN IMMEDIATELY** — no wait. This is the *"drain-with-a-wait, not
   only-new"* property: a caller with already-pending unseen rows gets them at once
   (`comms-subsystem.md:75` "snapshot-first"; prior §Q5(i) — the flagged trap is a caller
   misreading an instant return of OLD rows as "something just arrived", which the render must
   defeat, §A.4). ⚠ Whether this SELECT *stamps* is **FORK F1** (§Forks).
2. **ESTABLISH filtered LIVE-on-edge (best-effort).** If the snapshot is empty, establish
   `LIVE SELECT * FROM to WHERE out = agent:<uuid5-id-literal>` — the recipient's agent-id
   INLINED as a literal (agent-id ONLY, never `thread` — §B), exactly as
   `scout.py::CommandSubscriber.live_select_statement` inlines its status literal (store §10:
   params are IGNORED in a LIVE WHERE). Establishment is best-effort: a failure falls to
   poll-only, it never aborts await (mirror `CommandSubscriber._serve`, where a dead socket on
   establish propagates to the reconnect ladder, and the poll loop alone carries the load). The
   probe CONFIRMED this fires: `REPORT-probe-await-05a-1.md` PROBE 1 VERDICT — filtered
   `WHERE out = agent:a1` FIRES on `RELATE` and DISCRIMINATES (Phase C: `out=agent:a2` did NOT
   fire it).
3. **WAIT with poll fallback, within the ≤55s budget.** Race three futures: (a) a LIVE
   notification (a **contentless wake** — store §10: "never a source of truth"), (b) a poll tick
   every `poll_interval_s`, (c) the ≤55s deadline. On ANY wake or poll tick, **re-run the drain
   SELECT** (authoritative) — if it now shows unseen traffic, RETURN. LIVE only *triggers* a
   re-read; it never supplies the answer (mirror `_serve`'s poll loop + `_consume_live`, which
   drains-pending on each notification and swallows a subscription drop). The poll floor ALONE
   must satisfy the completeness bound — a build that only works because LIVE fired is broken
   (store §10: "poll fallback is MANDATORY"; probe "poll-fallback implication").
4. **FINAL snapshot at timeout — LOAD-BEARING.** When the ≤55s deadline fires with nothing seen
   yet, run **one more drain SELECT** (the final snapshot) BEFORE rendering empty. A message that
   landed in the last poll-gap is caught here. The honest claim is *"no unseen traffic AS OF my
   final snapshot at timeout"* — a point-in-time fact, NOT a continuous guarantee (prior §Q5(i):
   "ensure a FINAL snapshot at timeout, not just on wakes"). **A build that renders empty off the
   last WAKE's stale read instead of a fresh final snapshot is the wrong build this step exists to
   stop.**
5. **HONEST RENDER.** Non-empty → the drain-shaped render (fenced bodies, §A.4). Empty → the
   honest-empty naming the bound as a FACT, PLUS the `awaiting_answer(caller)` waiting-line when
   the caller's own question is outstanding (§A.4).
6. **TEARDOWN.** KILL the live subscription and release the connection, swallowing an
   already-dead-socket failure by catching `(*_CONNECTION_ERRORS, KeyError)` at the SDK-await
   boundary — exactly as `CommandSubscriber._safe_kill`/`_safe_close` do (probe PROBE 2: the
   in-flight socket-drop shape is `KeyError(request-uuid)`, next call `ConnectionClosedError`;
   store §3 ~:420–427).

### A.2 — The tool signature

`action=await`, `agent=<name>` (REQUIRED, resolved to the caller's `agent_id` in the caller's
session, exactly like every other `lore_comms` action), and an **optional `thread?`** label. This
matches the plan's recorded signature `await(agent, thread?)` (transcribed in my prior §Q5(ii) —
the plan file is now gone, so this rests on that archived transcription; the `thread?` param is
also consistent with drain's own `thread`-labelled model).

- **`thread?` filtering is CLIENT-SIDE on the authoritative snapshot re-read, NEVER in the LIVE
  WHERE** (prior §Q5(ii); §B below). The LIVE is a contentless wake with a DISCARDED payload —
  filtering it precisely on thread buys nothing (a thread-mismatched wake just triggers a re-read
  that finds nothing new and re-waits), while inlining `thread` would open DD-3.e's named
  injection door. So: LIVE WHERE = agent-id literal only; thread narrowing = a predicate on the
  drain SELECT result (where `thread` IS a bound param, as `drain` already treats it).
- **The ≤55s bound is a FIXED named constant, not a caller param** — **FORK F2** (§Forks). No
  `timeout=` argument.

### A.3 — The ≤55s budget mechanics

- **"Snapshot-first returns immediately on pending unseen traffic"** = step 1 short-circuits the
  whole wait; the ≤55s clock governs ONLY the wait phase (steps 2–4). A caller who already has
  unseen traffic never waits at all.
- **The budget is spent on the WAIT, not on the work.** Within ≤55s: LIVE-primary (a wake
  re-drains at once, so the common case returns in well under the budget) + poll-fallback (ticks
  guarantee progress even if LIVE never fires) + the final snapshot at the deadline.
- **`poll_interval_s` is builder-latitude WITHIN a named property:** *the poll ticks plus the
  final snapshot together must guarantee that any message present at the deadline is returned, not
  missed.* A single poll near the deadline is too thin — recommend a cadence giving several polls
  inside the window (the reference `CommandSubscriber` polls on a fixed `poll_interval_s` in an
  unbounded loop; await bounds the same loop by the ≤55s deadline). Not a fork; name the property
  so the contract pins it rather than pinning a magic number.
- **55, not 60:** the constant sits under the MCP tool-call timeout ceiling so the tool returns a
  render rather than being killed mid-wait. Pin it as a named constant with that rationale in a
  comment (the value is builder-latitude within "strictly under the tool-call timeout"; the
  PROPERTY is what the pin guards, per the enumerate-the-safe-set law).

### A.4 — The honest-empty timeout render (+ snapshot-first legibility + the waiting line)

Three requirements, all from prior §Q5(i)/(iii):

- **Snapshot-first legibility.** The render must make await legible as *drain-with-a-wait, not
  only-new* — a non-empty return may be OLD unseen rows, and the caller must not misread it as
  "just arrived." (Leg-1 scope-diff: the caller's mental model is "block until something NEW"; the
  actual answer is "is there UNSEEN traffic for me now, or within ≤55s?")
- **The bound as a FACT, never a disclaimer.** Empty render names the time and the set:
  *"no unseen traffic for <agent> as of <final-snapshot time>, waited <N>s"* — a bound is the set +
  the predicate + the time (CLAUDE.md trust definition), not *"results may be incomplete."*
- **The waiting line — the Consumer-Law fix (couples to Q2/DD-2.a).** On timeout, await consults
  `messages.py::MessageLedger.awaiting_answer(caller)`; if non-None, it APPENDS the waiting state
  DERIVED from the typed `WaitingOnAnswer` (`thread`, `question_seq`, aged off the real
  `asked_at` — NEVER fabricated), e.g. *"…still waiting on #<seq>, thread <thread> (asked 12m
  ago)"*. WHY load-bearing: a bare honest-empty is TRUE but LICENSES the wrong action when the
  caller has an outstanding question — it infers "nothing's happening, I can proceed" while still
  owed an answer. Under the hard trust definition (a consumer acting without checking cannot be
  wrong in a way the response did not name), the bare empty FAILS; naming the debt restores trust
  (prior §Q5(iii)).
- **Fenced bodies on the non-empty render.** await's non-empty output renders stored free text
  (bodies/refs, via `InboxEntry`) and MUST route through the SAME shipped `render_attributed`/fence
  seam `drain` uses — it hand-rolls no second containment (prior §Q3, ONE IMPLEMENTATION). Its
  test carries the P8d/03b HOSTILE fixture (newlines + an output-format-shaped forgery line +
  backtick runs) — single-line fixtures are how these defects stay green. (If F1 = peek, the
  bodies still render, so this holds regardless of F1.)

⚠ **Cross-cutting dependency (from prior §Cross-cutting + Q1 sequencing):** the timeout waiting
line CONSUMES 05a-i's DD-2.a helper. If the operator ever chose to REMOVE the waiting mechanism
(Q2 fork (b)), await's honest-empty becomes an un-fixable Consumer-Law trap — it cannot name a
debt the system no longer tracks. This is why 05a-i (the DD-2.a helper) MUST land before 05a-ii
consumes it, and why removing the mechanism REGRESSES await, not just deletes dead code.

### A.5 — The injection pin (DD-3.e / Q5(ii))

- **LIVE WHERE inlines ONLY `out = agent:<uuid5-id>`; NEVER `thread`.** The agent-id is
  `uuid5(session:name)` — a hash of charset-ASSERTed `name`/`session` (`comms-subsystem.md`
  Data model). It carries ZERO caller free text → injection-safe BY CONSTRUCTION. This SIDESTEPS
  DD-3.e's named re-open trigger entirely (await never inlines `thread`, so the
  charset-then-inline obligation never arises; DD-3.e :306–315).
- **Pin (property, not literal):** assert the EMITTED LIVE statement string inlines only a value
  matching the uuid5/record-id shape and contains NO caller-supplied substring (no `thread`, no
  body text). This is the plan's *"pin this in tests"* obligation my prior §Q5(ii) records.
- ⚠ **RESIDUAL BUILD-PROBE (cheap, flag to the builder): the record-id LITERAL syntax for a
  hyphenated uuid5.** The probe verified `agent:a1` (trivially safe). A uuid5 string
  (`d3b07384-d9a0-…`) inlined BARE as `agent:d3b07384-…` is a PARSE hazard — the hyphens read as
  subtraction (store §10 record-ids ~:902–904: the id's string component has quoting rules). The
  builder must inline the id in the correct record-id literal form (backtick or angle-bracket
  quoted) and the build probe must confirm it PARSES *and* still discriminates on a uuid5-shaped
  id. Injection-safety is unaffected (the id is charset-guarded); this is purely "does it parse."
  Fold it into the mandatory LIVE-on-edge build probe.

### A.6 — The load-bearing forgery pin (the real acceptance of the build probe)

**Socket-drop mid-await with pending traffic present → await STILL returns that traffic via the
poll path; it does NOT serve a false-empty.** (prior §Q5(i) Leg-2.) The SDK silently orphans
`live_queues` on a socket drop (store §10), and an in-flight op raises `KeyError(request-uuid)`
(probe PROBE 2). So await's wait phase must catch `(*_CONNECTION_ERRORS, KeyError)` at the
SDK-await boundary and, on a drop, **reconnect (bounded, within the remaining budget) and
re-drain** — mirroring `CommandSubscriber.run`'s reconnect ladder
(`(*_CONNECTION_ERRORS, KeyError, TxnContentionExhaustedError)`) — so the final snapshot runs on a
LIVE socket. Only a genuinely-empty final snapshot renders empty.

Acceptance for the build probe is therefore NOT merely "does LIVE fire" (PROBE 1 already settled
that YES). It is TWO legs:
- **Leg A (poll-only):** disable/ignore the LIVE leg entirely; assert await still returns pending
  traffic within the budget (proves the mandatory fallback carries the load alone).
- **Leg B (forgery):** with pending traffic present, drop the socket mid-wait; assert await
  reconnects, re-drains, and returns that traffic — NO false-empty. This is DD-4.c/#214's loss
  hazard re-tested on the await path, and it is the probe's real acceptance criterion.

Positive control (per the probe-with-a-control law): the SAME harness must show await returning
EMPTY when there is genuinely no traffic and no drop — else Leg B could pass by always-returning.

---

## B. Q5(ii) ruling — RE-AFFIRM: LIVE-WHERE key = agent-id only

**Confirmed, now with empirical backing.** Inline the recipient's `agent:<uuid5-id>` literal
ONLY; never inline `thread`.

- **Injection safety by construction** (the argument, unchanged from prior §Q5(ii)): the agent-id
  is a uuid5 hash of charset-ASSERTed `name`/`session` — no caller free text ever reaches the
  inlined LIVE WHERE. `thread` by contrast has NO charset validation (DD-3.e :306–315, length-bound
  only, because the taught `q:<topic>` convention contains `:` which `AGENT_NAME_PATTERN` forbids),
  so inlining `thread` is precisely DD-3.e's named re-open trigger. Agent-id-only leaves DD-3.e
  un-triggered.
- **Now empirically supported** (this is the new evidence the prior didn't have): the probe
  showed the filtered form FIRES and DISCRIMINATES correctly — `WHERE out = agent:a1` fired on a
  matching `RELATE` and stayed SILENT for `out = agent:a2` (`REPORT-probe-await-05a-1.md` PROBE 1,
  Phases B/C). So agent-id filtering is not just safe, it WORKS — the wake is scoped to the
  recipient, no whole-table re-dispatch storm.
- **The case for thread-in-LIVE, stated and rejected:** it would require charset-ASSERTing
  `thread`, which REJECTS the packet's own taught `q:<topic>` convention — self-defeating — and
  buys only wake-filtering precision on a payload that is DISCARDED anyway (a thread-mismatched
  wake just costs one extra re-read). All cost, ~no benefit.

**Recommendation to the operator: ratify agent-id-only.** Thread narrowing, if `await(agent,
thread?)` is offered, is a client-side predicate on the authoritative snapshot (§A.2), where
`thread` is a bound param and injection-safe.

---

## C. The Opus-4.8 LIVE receipt leg

- **What the acceptance IS** (`05-comms-await-story.md` Exit + #214): *an await WAKES on a REAL
  `send` inside the ≤55s bound, and EMPTIES HONESTLY on timeout.* Concretely, a live two-party
  exercise against the deployed image: agent X calls `await`; agent Y `send`s within the bound;
  X's await returns the traffic (the LIVE-or-poll wake fired) — and a separate await with no
  inbound `send` returns the honest-empty naming the bound. #214 is the live loss-hazard receipt
  this rests on (DD-4.c reproduced within an hour of being documented), so the await leg must
  demonstrate the NON-loss on the live engine, not just in-process.
- **This is a DEPLOY-gated, live-store acceptance** — it is the "the running artifact proves the
  cake, the green suite only proves the recipe" instrument (CLAUDE.md "THE TEST ENVIRONMENT IS A
  FICTION"): the in-process pins prove the state machine; only a real send across a real socket to
  the deployed container proves await wakes. Run it against spike-surreal :18000 for the build
  probe, and as the deploy smoke against the recreated container.
- **Roster is an OPERATOR item, not a design decision I make** (flag): this leg wants a
  fresh-context Opus-4.8 builder (`comms-subsystem.md` roster ruling 7 as amended;
  `05-…await-story.md:3–4` "Opus 4.8 builder on the await/LIVE leg"). The spawn mechanism exists —
  the `opus48-worker` agent type is pinned to `claude-opus-4-8` via its frontmatter (spawn it
  WITHOUT a per-invocation `model` override so the pin wins). Naming the actual agent + wiring is
  the lead's/operator's call; I only note the mechanism is available and the roster ruling stands.

---

## Forks (consolidated — surfaced, none decided here)

### F1 — Does `await` STAMP the traffic it serves? (contract-blocking)
Two readings that produce DIFFERENT code and DIFFERENT pins (brief-base §2 — flag both, recommend):
- **(a) Blocking-drain (stamps seen).** await IS a drain-that-waits: on wake it serves AND stamps
  `seen_at`, returning `stamped_seqs` like `drain`.
- **(b) Blocking-peek (stamps nothing).** await is a snapshot-first PEEK + wait: it surfaces
  unseen traffic (or waits, or times out) but stamps NOTHING; the caller consumes+stamps via a
  subsequent `drain`. (`drain(peek=True)` is the existing read-only shape it would mirror.)

**STRONG lean: (b) NOT-stamp.** Reasons: (i) stamping puts await squarely on the DD-4.c/#214
at-most-once LOSS path — a drop between await's stamp and the caller receiving bytes destroys
those rows with only `since=` to recover them, doubling the exposure surface 05a-i just pinned
shut; (ii) it CONTRADICTS the A.6 forgery pin — you cannot both "return pending traffic on a
socket drop" and "have already stamped it seen"; (iii) NOT-stamp makes await idempotent and safe
to retry, which is the whole point of a wait primitive. The surviving sources say "drain SELECT"
(the SELECT, read-only) and never state stamping either way — so this is a genuine gap, not an
invention. **Operator ruling needed before the contract fixes the return shape.** If (a) is
chosen despite the lean, the contract MUST extend the `since=` recovery to cover await's stamps
and A.6 must be re-stated (await can only promise non-loss up to its own stamp).

### F2 — The ≤55s bound: fixed constant vs caller `timeout=` param
- **Lean: fixed named constant, NO `timeout=` param.** The plan's recorded signature (prior
  §Q5(ii)) was `await(agent, thread?)` — no timeout arg; a caller-set timeout above the ~60s
  tool-call ceiling would get the tool killed mid-wait, defeating the honest-empty. An idle agent
  waiting the full budget is fine (it returns early on a real wake).
- **Caveat (why it's a fork, not a settled fact):** the param-vs-constant decision and the exact
  value 55 rest on my PRIOR report's transcription of the now-DELETED plan file — reconstructable,
  but not independently re-derivable. If the operator wants a caller-tunable wait, it must be
  CLAMPED to ≤55s (never exceed the ceiling). Recommend fixed constant.

### F3 — Q5(ii) LIVE-WHERE key (re-affirm, not new)
Agent-id-only (recommended, now probe-backed) vs thread-in-LIVE-with-charset (rejected —
self-defeating, ~zero benefit). §B. Recommend ratifying agent-id-only.

---

## Pins — the contract author's checklist (derived above; here in one place)

1. **Snapshot-first short-circuit** — a caller with pending unseen traffic returns IMMEDIATELY,
   no wait (fixture: pending row present at entry → sub-budget return). Discriminates against a
   "only-new / always-waits" build. (§A.1 step 1)
2. **Final-snapshot-at-timeout** — a message injected AFTER the last wake but BEFORE the deadline
   is RETURNED, not missed. Discriminates against a build that renders empty off a stale last-wake
   read. (§A.1 step 4 — load-bearing)
3. **Poll-only completeness (probe Leg A)** — with LIVE disabled, await still returns pending
   traffic within the budget. Discriminates against a LIVE-dependent build. (§A.6)
4. **Forgery / socket-drop non-loss (probe Leg B)** — drop the socket mid-wait with traffic
   present → await reconnects, re-drains, returns it; NO false-empty. Positive control: genuine
   empty renders empty. (§A.6 — the real acceptance criterion)
5. **Injection — emitted-LIVE-statement pin** — the LIVE WHERE inlines only a uuid5/record-id
   literal, no `thread`, no caller substring; property-keyed, not a bare literal. Plus the
   record-id-literal PARSE build-probe for a hyphenated uuid5. (§A.5 / §B)
6. **Honest-empty-as-fact** — empty render names time + set, never a disclaimer. (§A.4)
7. **Waiting-line on outstanding debt** — timeout render consumes `awaiting_answer(caller)` and
   appends the typed `WaitingOnAnswer` aged off real `asked_at`; discriminating pair: caller WITH
   an outstanding question sees the waiting line, caller WITHOUT does not. Depends on 05a-i's
   DD-2.a helper landing first. (§A.4)
8. **Fenced bodies + hostile fixture** — non-empty render routes stored free text through the
   shipped `render_attributed`/fence seam; test carries newlines + a forgery line + backtick runs.
   (§A.4 / prior §Q3)
9. **F1-dependent return-shape pin** — once the operator rules F1: (b) → `stamped_seqs` empty and
   an idempotency pin (two awaits over the same traffic both return it); (a) → `since=` extended to
   await's stamps. (§Forks F1)

_This doc proposes; the operator rules, the lead adjudicates. Standing by for follow-ups._

---

## Follow-up rulings 05a-ii (2026-08-10) — the contract author's three seam forks

The Opus-4.8 contract author (`REPORT-contract-05a-ii.md`, 26 RED pins, 35/35 satisfiability +
8 mutation proofs) ratified my F1=PEEK and F2=fixed-constant, then raised three questions about
the Python SEAM that HOSTS the wait-machine — my design-of-record specified await's BEHAVIOR
(§A.1–A.6) but not its structure. **All three settle from HOUSE PRECEDENT (`CommandSubscriber`)
+ standing law (Consumer Law, ONE IMPLEMENTATION, #104 typed-applicability). NONE is
operator-level** — they need no scope/feature decision, only a structure ruling the lead may
ratify (ruling authority delegated to the lead per the 05a-iii precedent). Tight rulings so the
contract-adversary pass is unblocked:

### R-1 — Wait-machine home: STANDALONE primitive, not a `MessageLedger` method (lead-adjudicable)

**Ruling: host the wait-machine in a STANDALONE primitive (e.g. `InboxAwaiter`), constructed with
the injectable `connect` factory — NOT as `MessageLedger.await_inbox`.** The ledger stays the
data-access authority; the awaiter CALLS it.

- **House precedent is unambiguous and already made this exact separation:**
  `scout.py::CommandSubscriber` is the project's LIVE + poll + reconnect wait/dispatch machine, and
  it is a **standalone class constructed with an injected `connect` factory** — NOT a method on any
  ledger. await is the same KIND of thing (transport-driven, reconnecting, its own connection
  lifecycle), bounded instead of infinite. Same concern → same home shape.
- **The injectable `connect=None` on `await_inbox` is itself the tell.** `MessageLedger` ALREADY
  owns a connection (its `_query` seam); a ledger method needing a SEPARATE injected `connect`
  factory is transport orchestration wearing a data-access method's clothes. That parameter is
  precisely `CommandSubscriber.__init__(connect=...)` — it wants to be a constructor arg on its
  own object, not a bolt-on to a ledger method that then carries two connection concepts (the
  ledger's `_query` connection for drain SELECTs + the awaiter's dedicated LIVE connection).
- **Concern boundary:** `MessageLedger` = request/response rows-and-edges (drain/send/ack/
  awaiting_answer). A LIVE-subscription + poll + reconnect + budget-clock loop is a different
  concern; parking it on the ledger blurs the boundary the codebase already keeps in scout.py.
- **Clean collaboration (concrete):** `InboxAwaiter` takes the `MessageLedger` (or just its
  `drain` callable) + a `connect` factory; it owns snapshot-first `drain(peek=True)`, LIVE
  establish, poll re-drain, reconnect, budget clock, final snapshot; returns a `MessageDrainResult`
  (peek). The **server `_comms_await` handler CONSTRUCTS it, calls it, and owns the RENDER** —
  including the timeout waiting-line via `ledger.awaiting_answer(caller)` (§A.4). The awaiter need
  not even know about `awaiting_answer`; the waiting-line is a render concern that lives with the
  other `_render_comms_*` helpers in server.py. (Reject the "server handler ORCHESTRATES the loop"
  option — that blurs the server's dispatch/render concern the same way; the handler CONSTRUCTS and
  CALLS, it does not BE the loop.)
- **Cost is low** (the observable pins are seam-agnostic — only the entry point the ~13
  wait-machine pins call moves) and **testability improves** (inject `connect`/`sleep`/`now` on a
  purpose-built class, the CommandSubscriber idiom, instead of bloating a ledger method signature
  with transport seams).
- **Classification: DESIGN recommendation, LEAD-adjudicable — not an operator fork.** Internal
  module structure is design/lead territory; house precedent settles it. The `MessageLedger`-method
  form is not *wrong*, just off-pattern — if the lead judges the (small) churn not worth it, it can
  stand, but I lean firmly to the standalone primitive.

### R-2 — ONE IMPLEMENTATION vs `CommandSubscriber`: share the ERROR-CLASSIFICATION POLICY only; the loop structure is legitimately distinct (mandatory share + mutation pin)

**Ruling: await is a legitimately DISTINCT STRUCTURE (bounded one-shot ≠ infinite dispatcher) — do
NOT extract a shared wait-machine helper. It MUST share exactly ONE thing: the
error-classification policy, referenced from a single symbol, PROVEN BY MUTATION.**

- **What is POLICY (must agree) vs STRUCTURE (may differ):**
  - **POLICY — the connection-error set.** Both must reconnect on the same exceptions. The shared
    atom is `loremaster.store._txn._CONNECTION_ERRORS` (already a shared constant — `CommandSubscriber`
    references it) PLUS the documented rule *"add `KeyError` at the SDK-await boundary"* (store §3:
    "Classify `KeyError` tightly, at the SDK-await boundary only"; probe PROBE 2 re-confirmed the
    shape on 3.2.4). **Discharge: extract `_SDK_AWAIT_BOUNDARY_ERRORS = (*_CONNECTION_ERRORS,
    KeyError)` in `store._txn`, and have BOTH await AND at least one `CommandSubscriber` catch site
    (`_safe_close`/`_safe_kill`) reference it.** Today scout.py writes `(*_CONNECTION_ERRORS,
    KeyError)` inline at several sites — so this DRYs scout's own clones too.
  - **STRUCTURE — the loop.** `CommandSubscriber.run()` is an infinite reconnect loop;
    await is a bounded one-shot. A shared `run()`-shaped helper would force one structure onto two
    genuinely different lifecycles — that is over-abstraction, not sharing. The filtered-LIVE
    statement builders are ALSO legitimately different (`WHERE status='pending'` vs
    `WHERE out=agent:<id>`); their shared element is the store-LAW idiom "inline the literal, never
    a bound param" (§A.5 injection pin), not a shareable function.
- **`TxnContentionExhaustedError` nuance (builder latitude, recommend YES):** `run()` ALSO unions
  `TxnContentionExhaustedError` at its reconnect ladder (finding #108) but NOT at teardown. await's
  drain SELECTs already retry via the shared `retry_on_conflict` driver; recommend await treat an
  exhaustion as a transient and re-poll within budget (mirror `run()`), i.e. its reconnect-path
  set = `(*_SDK_AWAIT_BOUNDARY_ERRORS, TxnContentionExhaustedError)`, teardown set =
  `_SDK_AWAIT_BOUNDARY_ERRORS`. This composition is builder latitude; the SHARED constant is not.
- **MANDATORY PIN (per ONE IMPLEMENTATION — routing is not sharing):** a prove-sharing-by-mutation
  pin — mutate `_SDK_AWAIT_BOUNDARY_ERRORS` (e.g. drop `KeyError`) and assert a pin in BOTH await's
  suite AND `CommandSubscriber`'s suite reddens. A caller that merely re-writes the same tuple inline
  is a private copy wearing the shared name; only the mutation pin distinguishes share from clone.
- **Classification: MANDATORY ONE-IMPLEMENTATION mechanic — builder/lead latitude on the seam NAME
  and the small scout.py touch (a scope call for the lead), but the share + mutation pin is
  required, not optional. Not operator-level.**

### R-3 — await's non-empty render MUST NOT reuse the peek-teach verbatim: it teaches a false affordance (mandatory Consumer-Law fix + pin)

**Ruling: the shared `_render_comms_drain(peeked=True)` footer is NOT acceptable for await as-is —
it teaches "re-run WITHOUT peek=true to mark them seen," an instruction await CANNOT honor (await
has no `peek` param). await's non-empty render MUST teach its REAL consume path: consume via
`action=drain`.** This is a served-surface TRUST violation, not wording latitude.

- **Why mandatory, not latitude:** a served surface teaching a follow-up action that does not exist
  on the tool is the #104/#131 class — served English contradicting served behavior, with no
  mechanical guard. Under the hard trust definition, a consumer acting on "re-run without peek=true"
  is wrong in a way the response induced. The contract left "the wording as open latitude," but the
  wording carries a mandatory PROPERTY it did not pin: it must name the true consume action and must
  NOT teach the nonexistent await-peek re-run.
- **Fix, ONE-IMPLEMENTATION-compatible (#104 — renders take TYPED applicability, not a name they
  compare):** REUSE the fence + row rendering (the injection-critical part — §A.4 hostile-fixture
  pin still applies) and vary ONLY the taught follow-up via typed input. Concretely, the footer's
  consume-instruction becomes a typed applicability the caller supplies (drain-peek → "re-run
  without peek=true"; await → "consume via `action=drain`"), rather than a `peeked: bool` that
  hardcodes the drain wording. Do NOT hand-roll a second full render (that forks the fence); do NOT
  emit the drain footer verbatim.
- **MANDATORY PIN:** a render pin asserting await's non-empty output (a) does NOT contain the
  "peek=true" re-run instruction and (b) DOES name `action=drain` as the consume path — plus the
  existing fence + verbatim-body round-trip pins. Discriminating fixture: a build that reuses the
  drain footer verbatim FAILS (a).
- **Classification: MANDATORY Consumer-Law/trust fix — exact wording is builder latitude WITHIN the
  pinned property (names `action=drain`, never the peek re-run). Not operator-level.**

**Net for the adversary:** R-1 moves the ~13 wait-machine pins' entry point to a standalone
`InboxAwaiter` (seam-agnostic, cheap); R-2 adds one shared error constant + a cross-suite mutation
pin; R-3 adds one render pin (correct consume-teach) and a typed-applicability footer. None blocks
on the operator; all three are ratifiable by the lead now.

_Standing by for follow-ups._
