brief-base v6 read

# 03a-2 consume-path design rulings — duplicate-seq acks, self-answers, hot-path reads, snapshot atomicity

**Authority:** design-comms (long-running comms design authority, operator-delegated 2026-07-23 —
design decisions in this subsystem escalate here, not to the operator). These four are RULINGS the
packet lead implements and pins, not options.
**Read at:** working tree `ac38246` (03a-2 landed at `853a95b`), 2026-07-23.
**Addendum 2026-07-23 (same day):** R5/R6 appended on the lead's follow-up — two more
undecided-by-any-pin semantics surfaced by the cold audit (§6 P7/P7b and P5) after the original
brief was written. Same class as R1: shipped behaviour that a refactor could silently flip.
**Sources (cited, not re-derived):** the approved design
`~/.claude/plans/one-of-claude-codes-nifty-garden.md` · `docs/plans/v2/comms-subsystem.md` ·
`docs/plans/v2/03-comms-message-graph.md` §Kickoff rulings (ruling 9) · DESIGN-LAW §1/§5/§8/§15 ·
`docs/reference/surrealdb-31-capabilities.md` §1.1/§1.5/§3/§4/§5 · the artifact
`loremaster/loremaster/messages.py` + oracle `loremaster/tests/_message_fakes.py` + contract
`loremaster/tests/test_message_ledger.py` (IMMUTABLE — new pins land via 03b's contract) ·
`REPORT-builder-03a2.md` §Flags.
**Operator inputs needed: NONE.** All four are ruled within delegated authority. (R3 delegates one
*measurement* to the 03b builder under a stated decision rule — that is not a design delegation.)

**The consumer, restated once because every ruling leans on it:** `lore_comms` is consumed by LLM
agents coordinating a fleet. An LLM consumer (a) assembles inputs from rendered text, so benign
input slips (a repeated seq) are certain to occur; (b) acts on the CURRENT render and re-derives
constantly, so transient staleness is cheap; (c) cannot see an INVISIBLE error at all — per
ruling 9, false-waiting beside a fresh heartbeat is self-announcing, false-NOT-waiting is the
lost-message class this subsystem exists to kill; (d) pays for errors in context and round-trips
(DESIGN-LAW §1: attention is the cost, call count is not), so a teaching reject is only justified
when the ledger cannot act safely.

---

## R1 — duplicate seq inside ONE ack batch: first-wins / rest-`already_acked`. Pin it in 03b.

**RULING.** `ack(agent_id=X, seqs=[5, 5])` reports `["acked", "already_acked"]` with
`acked_count == 1`, `already_acked_count == 1`, both entries carrying the SAME `acked_at` — the
shipped behaviour (option a), now made law. Options (b) request-dedupe and (c) reject are REFUSED.

**Reasoning (consuming agent's PoV).**
- The likely producer of `[5, 5]` is an LLM transcribing seqs from a rendered inbox (a seq listed
  in both the body render and the `ACK REQUIRED` trailer). This input WILL occur; it has an
  obviously correct interpretation and zero store hazard, so a reject (c) converts a harmless slip
  into a failed call + retry round-trip — pure attention tax, and it teaches the consumer to fear
  `ack`. Rejects are for inputs the ledger cannot act on safely (ghost recipient, empty body); this
  is not one.
- Dedupe-the-request (b) breaks the quantifier law the contract already pins
  (`test_a_mixed_batch_reports_every_seqs_own_fate`: every REQUESTED seq gets its own entry, in
  request order). An LLM matching entries back to its request positionally would misalign — silent
  positional loss, DESIGN-LAW §1.4's cardinal class.
- (a) has the one algebraic property worth pinning: **a batch reads exactly as the sequential
  composition of singleton acks** — `ack([5,5])` ≡ `ack([5]); ack([5])`. It is also what the
  designated oracle (`FakeMessageLedger.ack`, per-seq loop) already does, and it is the only option
  under which one CAS has one winner — "two winners for one edge" (`acked_count == 2`) would be a
  false statement about the store, the exact shape the write-once section forbids.
- Honesty check on the second entry's label: `already_acked` cannot distinguish "you listed it
  twice" from "acked in an earlier call". At the LEDGER surface that is fine — the consumer's
  correct next action ("this seq is settled, nothing further owed") is identical under both
  readings, and the stamp value tells the truth either way. (03b's RENDER may annotate duplicates
  if it wishes; not required, not ruled.)

**Cost.** Zero implementation (shipped build conforms). One pin in 03b's contract.

**Instrument (03b contract, both `[fake]` and `[real]` legs).**
```python
async def test_a_seq_repeated_inside_ONE_batch_reads_as_the_sequential_composition(...):
    """RULING R1 (03a-2-consume-path-design-rulings.md): first occurrence wins the
    CAS, every later occurrence reads already_acked with the SAME stored stamp —
    a batch is exactly the fold of its singleton acks. Guards the naive set-based
    build that reports two winners for one edge."""
    [seq] = await _send_n(message_ledger, 1, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
    result = await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[seq, seq])
    assert [e.outcome for e in result.entries] == ["acked", "already_acked"]
    assert result.acked_count == 1
    assert result.already_acked_count == 1
    assert result.entries[0].acked_at == result.entries[1].acked_at
```
Plus one non-adjacent variant (`seqs=[s1, s2, s1]`) asserting entry order equals request order —
the adjacent-duplicate-only fixture would let a "dedupe adjacent pairs" build pass.

---

## R2 — a self-addressed follow-up must NOT clear the asker's own debt. Add the fourth conjunct.

**RULING.** An ANSWER requires FOUR conjuncts: delivered-to-me · on the question's thread · created
after it (`seq`) · **`sender != me`**. The shipped behaviour (an explicit self-addressed send on
the question's own thread clears the waiting state) is a DEFECT relative to the contract's own
pinned intent, reachable only through a fixture-monoculture gap. Fix in 03b before any agent can
call the surface.

**Reasoning (consuming agent's PoV).**
- **What the state MEANS to its consumers** (fleet render, lead, footer): "this agent needs INPUT."
  Input is by definition external. A self-note is information, but it is not input — an agent that
  has sent itself a memo has, by construction, received nothing from outside. The load-bearing
  invariant is: *the signal must not clear without an external message arriving on the thread.*
- **The error-direction asymmetry ruling 9 rests on decides it.** Without the conjunct, the failure
  mode is an ACCIDENTAL clear: questions ride ordinary work threads (`set_status='input_required'`
  on any send; threads default to session and to `task:<id>` conventions — a dedicated `q:` thread
  is a fixture idiom, not the field reality), and self-notes are an explicitly blessed pattern
  (03 kickoff ruling 7: explicit self-address IS delivered). A self-memo landing on the same
  thread as an open question silently reads as its answer → **false-NOT-waiting, the invisible
  direction** — the one failure ruling 9 refuses to accept. With the conjunct, the failure mode is
  an agent that self-resolved staying "waiting" → visible beside a fresh heartbeat, remediable.
  Same asymmetry, same verdict, third application.
- **The contract already asserts the property; the fixture just can't reach the gap.** The pin is
  NAMED `test_a_message_the_ASKER_sends_on_its_own_thread_is_not_an_answer` — unconditionally —
  and its docstring says "an answer is a message DELIVERED TO the asker" as the *mechanism* for
  that property. The fixture sends to the lead only, so delivered-to-me happens to enforce it; the
  explicit-self-address path (pinned deliverable by
  `test_an_EXPLICIT_self_addressed_send_IS_delivered`) walks around the mechanism while the
  property's name stays green. This is the repo's fixture-monoculture defect class verbatim: the
  message is the spec the author believed, the assertion is the check the suite performs.
- **Corroborating natural-language defect, live in the tree today:** the shipped
  `MessageLedger.awaiting_answer` docstring states *"DELIVERED TO this agent (a `to` edge to it —
  so the asker's own follow-up on its own thread is not an answer)"*. That parenthetical is FALSE
  for a self-addressed follow-up under the shipped code — served prose promising a check the code
  does not perform (the P2 false-gate class). R2 makes the prose true instead of weakening it.
- **Reconciliation with ruling 7 (self-notes are legitimate):** unchanged. Self-addressed sends
  remain deliverable, drainable, ackable. They simply do not count as answers to your OWN question.
- **The consequence, accepted and named:** with `sender != me` there is NO self-service clearing of
  a question. An asker that resolved its own question (or received the answer out-of-band directly)
  clears the state only when SOME OTHER party sends it an on-thread message — in practice the
  lead's one-line on-thread ack, which is protocol-POSITIVE: it both clears the debt and puts the
  resolution into the durable record (the existing KNOWN-BOUND escape pin,
  `test_the_bound_closes_the_moment_the_answer_IS_relayed`, already models exactly this shape).
  This folds into ruling 9's existing out-of-band KNOWN BOUND; it does not need a bound of its own.
  Residual for packet 05, non-binding: if a question-withdrawal verb is ever wanted, it is a NEW
  design question for this authority — do not re-admit self-answering as its cheap substitute.

**Cost.** One conjunct in one WHERE clause + one line in the fake + one new pin + a docstring that
becomes true. No existing pin goes RED: every answer fixture in the committed contract uses
`SENDER_LEAD` as sender (verified against `_answer` and every `TestTheWaitingStateIsDerived`
fixture at `ac38246`), so the change is invisible to all 180 pins.

**Implementation (exact, for the builder brief).**
1. `messages.py::MessageLedger.awaiting_answer` — the deliveries SELECT gains one conjunct:
   `... FROM to WHERE out = $agent AND in.sender != $agent` (`$agent` is already bound as a
   `RecordID`; `in.sender` is the same type). Docstring: "all THREE conjuncts" → FOUR, with the
   fourth stated as *from another agent — a self-note is information, never input*.
2. `_message_fakes.py::FakeMessageLedger.awaiting_answer` — the `delivered_to_me` comprehension (or
   the `answered` predicate) gains `candidate.sender_id != agent_id`. ⚠ This is an ORACLE change —
   a contract-phase edit made by 03b's contract author and graded by the contract-adversary
   (DESIGN-LAW §15), never a builder drive-by.
3. New pin (03b contract, both legs):
   `test_an_explicitly_SELF_ADDRESSED_message_on_the_question_thread_is_NOT_an_answer` — asker
   asks on thread T (recipients `[lead]`); asker then sends on thread T with
   `recipients=[_ref(AGENT_FIXER_B)]` (and a second leg with `[lead, me]` — the mixed-recipient
   variant, so a "self-only sends are special" build cannot pass); `awaiting_answer` is still
   not-None. Positive control is the adjacent existing pin (a lead answer clears it).

---

## R3 — hot-path reads: land BOTH message indexes inside 03b (the free window), bound the
deliveries read, refuse the window-bound and the stored pointer.

**RULING**, in four parts:

**(1) Two indexes land in 03b, before its deploy, as their own one-concern commit.**
`surreal_schema.py::_message_statements` gains:
- `_plain_index(MESSAGE_TABLE, f"{MESSAGE_TABLE}_seq", ("seq",))` — serves `ack`'s
  `_resolve_message_ids` (`WHERE seq IN $seqs`).
- `_plain_index(MESSAGE_TABLE, f"{MESSAGE_TABLE}_sender_question", ("sender", "question"))` —
  serves the questions read (`WHERE question = true AND sender = $agent`; sender-first is the
  selective prefix).
Both `IF NOT EXISTS` per store reference §1.1 (INDEX row — `OVERWRITE` on an index is the
boot-crash direction; the guard-kind pin `TestFieldDdlConvergesOnAnExistingStore` accepts these
automatically since `_plain_index` emits the required guard).

**Why NOW is the deliberate packet the builder's flag asked for — the window argument, derived:**
a NEW index on a POPULATED table BUILDS, blocking, at the first `ensure_ready` that carries it
(§1.5 vendor quote: "indexes all existing records… blocks until fully built"). But production has
**zero `message`/`to` rows today and will until 03b deploys**: packets 03/03a-1/03a-2 are all
TEST-ONLY (their packet headers), the deployed image predates `messages.py`, and — decisively —
this DDL is applied only by `MessageLedger.ensure_ready`, which nothing in the deployed server
instantiates until 03b's dispatcher exists. So indexes shipped WITH 03b build over an empty table
for free; the same two lines shipped in any later packet cost a blocking build over months of
accumulated rows at every deployed store's next boot. The cheap window closes at 03b's deploy,
permanently. (Lead: the 03b deploy smoke will confirm the empty-table premise for free; do not
probe `:18500` before then.)

**(2) Bound the deliveries read — semantics-identical, rows bounded.** Even perfectly indexed,
`SELECT in.thread, in.seq FROM to WHERE out = $agent` returns EVERY delivery ever made to the
agent, forever, and filters client-side — the result set itself grows with lifetime volume. Since
the questions read runs first (and must — see R4), the deliveries read can be bounded by what the
derivation can actually use:
```
SELECT in.thread AS thread, in.seq AS seq FROM to
WHERE out = $agent
  AND in.sender != $agent            -- R2's conjunct
  AND in.thread IN $question_threads -- threads of MY question rows (small by construction)
  AND in.seq > $min_question_seq     -- min over my questions' seqs; any relevant answer exceeds it
```
This is a superset of every candidate answer for every question (any answer to Qk needs
`seq > Qk.seq ≥ min`), so the client-side per-question check is unchanged and all 180 pins plus
R2's new pin remain the semantic instrument. ⚠ Traversal-field WHERE clauses (`in.*`) on an edge
table must be proven by the `[real]` leg; if the engine rejects the shape, the FALLBACK is
today's unbounded-but-indexed read with client-side filtering — a performance regression only,
never a semantics fork, and the builder says which shape shipped.

**(3) REFUSED: any time/seq bound on how far back the derivation looks.** An unanswered question
aging out of the derivation window is a debt that silently vanishes — false-NOT-waiting, the
invisible direction. That is a semantics change wearing an optimization's clothes; ruling 9's
asymmetry forbids it regardless of scale.

**(4) REFUSED: the stored open-question pointer.** Ruling 9 struck stored waiting state for
reasons (lost updates, forgot-to-clear, agent-discipline dependence) that are all still true;
the brief asks "what changed" — the answer is NOTHING. The scale concern is fully answered by
indexes + the bounded read without storing anything. Do not re-litigate absent a new fact.

**Costs.** Two DDL lines + two schema pins + the bounded-SELECT edit riding the same 03b builder
wave as R2 (same function, one review). Index-presence pins follow `test_comms_schema.py`'s
existing `_index_statements` idiom (the packet-03 pins are per-property, not exact-set — verified
at `ac38246` — so nothing existing goes RED).

**Receipts required (03b exit):**
- Schema pins: `message_seq` and `message_sender_question` indexes present, non-UNIQUE,
  `IF NOT EXISTS` (the guard-kind pin covers the guard automatically).
- **Concurrency re-certification:** an index adds an index-write to every send transaction, and
  the 320/320 zero-conflict send measurement (store reference §5) predates it — so the existing
  send-concurrency AND 16-way ack pins re-run at the 20-consecutive discipline AFTER the schema
  change. A single green run never clears a concurrency test (repo law).
- **One `EXPLAIN` receipt** against spike-surreal for the bounded deliveries SELECT and for
  `drain`'s SELECT, settling whether the `(out, seen_at)` composite serves an `out`-only /
  `out`+traversal-filter lookup. The builder's "covered by the out prefix" claim is asserted, not
  probed — planner behaviour is exactly the class the reference says to verify (§"READ THE
  DEPENDENCY'S DOCS — THEN VERIFY"). Decision rule: prefix served ⇒ done; not served ⇒ add
  `_plain_index(TO_RELATION, f"{TO_RELATION}_out", ("out",))` in the SAME commit (same free
  window). This is a measurement under a stated rule, not a design delegation.

**Deliberate divergence from the approved design, recorded (strikeable):** the design's data-model
section says `seq` (int, **UNIQUE**); the shipped schema has no unique index and R3 lands a PLAIN
one. Reason: `sequence::nextval` distinctness is a vendor-documented guarantee, probed at 3200/3200
distinct (store reference §5), and the mint is the ONLY write path to `message` — while a UNIQUE
index adds unmeasured conflict surface to every concurrent send for a backstop against a write
path that does not exist. Note that `ack._resolve_message_ids` silently last-wins if seq were ever
duplicated, so this divergence carries a **named re-open trigger**: the day ANY second write path
to `message` exists (an import/migration tool, a relay verb writing rows directly), flip to
`_unique_index` behind a fresh 20-run send-concurrency receipt.

---

## R4 — two reads, not one snapshot: ACCEPT as a KNOWN BOUND, pin it (order + bound + trigger),
and REFUSE the transaction. Also: the flag's direction analysis is backwards — corrected here.

**RULING.** `awaiting_answer` stays two (with R3's bounding, up to three) plain reads. No
`execute_transaction`. The bound is pinned per PIN-THE-MISS with the corrected analysis below, a
named re-open trigger, and the named cheap remedy so the trigger-day engineer neither reinvents it
nor reaches for the transaction.

**First, the correction (surfaced per the everything-you-notice law).** Builder flag #5 and the
question's framing say an answer landing between the questions SELECT and the deliveries SELECT
"makes the call report a just-settled debt as waiting". **That is the wrong direction.** With the
shipped order (questions first, deliveries second), deliveries can only be a SUPERSET of what
existed at the questions read — an answer landing in the window is SEEN by read 2 and makes the
result FRESHER, not staler. The real skew anomaly is the opposite corner: the agent's own
concurrent NEW ask in the window, combined with an in-window answer settling all its OLD
questions, yields one call returning `None` while a (milliseconds-old) debt exists — a one-cycle
**false-NOT-waiting**, provably non-linearizable (asked-then-answered interleavings exist where
`None` was true at no instant of the call). Derived 2026-07-23 from read order + monotonic data;
the pin's docstring must carry THIS analysis, not the flag's, or the next engineer "fixes" the
wrong hazard.

**Why accept it anyway (consuming agent's PoV).**
- The corner requires the watched agent itself to ask a new question inside the millisecond window
  of another caller's derivation, AND all its prior questions to settle in the same window. The
  miss lasts exactly one read cycle; every consumer named (fleet render, footer, heartbeat line)
  re-derives continuously and acts on renders, never on a single point read.
- No consumer can even OBSERVE the anomaly as distinct from irreducible staleness: any render is
  stale by transit time; a "correct" atomic snapshot taken at the call's start would report the
  same `None`. The marginal truth an atomic read buys is zero for every consumer that exists.
- The "fix" is not even known to be one: SurrealDB's read-isolation semantics inside a transaction
  are UNVERIFIED in this repo (the store reference has no section on it — noted as a gap in
  §Residuals). Wrapping two SELECTs in `BEGIN/COMMIT` and CLAIMING snapshot semantics without a
  probe is the #107 doc-trust failure shape; buying the probe + a transaction on every derivation
  call (fleet × agents × renders) purchases nothing observable.

**Instrument (03b contract).**
1. **Read-order + short-circuit pin** (scripted-connection, `test_retry_seam`-style): assert the
   questions SELECT (`FROM message`) is issued BEFORE the deliveries SELECT (`FROM to`), and that
   with ZERO question rows NO deliveries SELECT is issued at all (the early return — the common
   fleet case is one cheap indexed read). The order is load-bearing twice over: it is what makes
   the dominant error direction fresh-or-visible (a swapped order re-derives a different anomaly
   profile), and R3's bounding derives its `$question_threads`/`$min_question_seq` params FROM the
   questions read — deliveries-first cannot bound. The executable claims (order, short-circuit)
   are executed; the race-window claim is a derivation from them, stated in the docstring as such.
2. **KNOWN BOUND docstring** on that pin, `TestTheDerivedWaitingStateKnownBound`-style: the
   corrected anomaly (one-cycle false-`None` under the agent's own concurrent ask), why accepted
   (unobservable beside irreducible render staleness; consumers re-derive), and:
   **RE-OPEN TRIGGER:** the day `awaiting_answer`'s result becomes load-bearing for a ONE-SHOT
   irreversible action — an auto-release, a gate, packet 05's `await` returning on it — the
   staleness window becomes a correctness input and the bound must be closed. **The named remedy
   for that day is NOT a transaction:** it is the conditional third read — when the derivation
   concludes `None` with question rows present (the only path the corner inhabits), re-read
   questions once and evaluate any new ask against the already-fetched deliveries; every residual
   error then collapses into visible false-waiting, engine-probe-free. (If a transaction is ever
   preferred instead, the engine's transactional read-isolation must be probed and pinned FIRST.)

**Cost.** Zero production change now. One scripted-connection pin + docstring.

---

## R5 — one answer discharges the THREAD's whole debt: KEEP it, name it honestly, pin it
both ways, teach the batching consequence. (Cold audit §6 P7/P7b.)

**RULING.** The shipped semantics stand: **the unit of derived debt is the THREAD, not the
question.** An agent is awaiting iff its LAST on-thread question has no later qualifying delivery;
one answer discharges every earlier question on that thread, and (the audit's own control) an
answer landing BETWEEN two asks leaves the later question outstanding. Per-question FIFO matching
is REFUSED; an answers-to reference column is REFUSED. 03b pins both faces of the shipped
behaviour and ships one static teaching line.

**Reasoning (consuming agent's PoV).**
- **The discharge predicate is content-blind BY DESIGN** (ruling 9's coarseness: ANY later
  on-thread delivery-to-me counts — the existing pins already accept that unrelated on-thread
  chatter discharges a question). A per-question 1:1 matching discipline layered on a content-blind
  predicate is precision theater: it would assert "the Kth reply answers the Kth question" — a
  fiction the data cannot support, since the Kth delivery may be chatter. The thread is the honest
  granularity of what this mechanism can actually know.
- **The normal fleet exchange decides the error direction.** An agent that batches two questions
  onto one thread gets ONE comprehensive reply — that is how an LLM lead actually answers a
  backlog. Under per-question matching, the state stays "waiting" after a comprehensive reply and
  **never self-corrects** (no second reply is coming), and the LEAD has no signal telling it which
  debt it supposedly still owes — a persistent false-waiting with no holder of the recovery
  information. Under thread-debt, the failure mode is a PARTIAL reply clearing both — but the
  recovery information sits with exactly the right party: the ASKER read the reply, knows which
  question went unaddressed, and a RE-ASK (a new `set_status='input_required'` send on the thread)
  re-establishes the debt mechanically. Errs recoverable-by-the-informed-party vs. errs
  unrecoverable-by-anyone: thread-debt wins.
- The lead's asymmetry note is acknowledged and priced: thread-debt does err toward NOT-waiting on
  a partial reply. The mitigation is not mechanism but PROTOCOL, expressible today with zero code:
  **separate debts belong on separate threads** (the `q:<topic>` idiom the contract's own fixtures
  use). Distinct threads are already pinned as independent debts
  (`test_answering_only_ONE_of_two_questions_leaves_the_other_outstanding` — two threads).
- **Composition checks (the lead's flagged interactions):** R3's bounding is unaffected
  (`thread IN $threads AND seq > min` remains a superset of every candidate discharge). R2's
  `sender != me` PROTECTS R5: an asker's own second question (or self-addressed bump) on the
  thread can never discharge the first — only external traffic moves the debt.

**Cost.** Zero implementation (shipped build and oracle already agree). Two pins + one line of
instruction text.

**Instrument (03b).**
1. Pin (both legs): two questions, SAME thread, one later answer → `awaiting_answer` is `None` —
   docstring naming the semantics (*"a thread carries ONE conversational debt; a reply discharges
   the thread — separate debts take separate threads"*) so the next reader meets the choice
   deliberately.
2. Pin (both legs, the audit's control, currently live-reproduced but unpinned): ask Q1 → answer →
   ask Q2, same thread → waiting on Q2 (ordering respected; discharge is never retroactive).
3. **Static teaching, not a hot-path check:** the `lore_comms` instructions block (which 03b's
   instructions pin already forces to teach the tool) carries the one-thread-one-debt rule and the
   re-ask recovery. REFUSED: a send-time "this thread already carries your open question" warning —
   it would put a question-scan on every `send`, a hot-path cost for a teaching job the
   instructions block does statically for free.

---

## R6 — `ack` does NOT stamp `seen_at`: KEEP the stamps independent; the fix the consumer
needs is a RENDER-LAYER law, and the committed contract already forecloses the alternative.
(Cold audit §6 P5.)

**RULING.** `seen_at` and `acked_at` remain independent write-once facts: **seen = served by a
stamping drain; acked = actioned by the recipient. Neither implies the other in the STORE;
implications belong to renders.** "Ack also stamps seen" is REFUSED. The consumer-visible
consequence (an acked-but-never-drained message still counts as pending) is ruled coherent,
transient, and in the SAFE direction — and it is governed by a binding render law on 03b/04 below.

**Reasoning (consuming agent's PoV).**
- **The committed contract already pins the shipped behaviour — inadvertently but mechanically.**
  Verified at `ac38246`: `test_ack_note_lands_on_the_edge_the_CAS_WON`,
  `test_an_ack_with_NO_note_leaves_it_unset`, and `test_a_note_never_reaches_an_ALREADY_acked_edge`
  all ack a never-drained message and then read the edge back via `drain(peek=True)`,
  indexing `entries[0]` — which is only served while the edge is unseen. "Ack stamps seen" turns
  all three RED. Flipping it therefore means re-opening a cold-audited IMMUTABLE contract for a
  corner-case cosmetic gain (plus an engine-syntax probe for a conditional SET). Refused on that
  ground alone — and the semantics ground below says the contract's accident is also correct.
- **The two stamps answer two different questions, and both consumers exist.** `seen_at` is the
  queue stamp — it drives *what the next drain serves* ("drain stamps exactly what it rendered";
  elided rows stay unread — the design's whole no-cursor mechanism). `acked_at` is the
  accountability stamp — it drives the must-not-lose directive tracking. Collapsing them makes the
  queue lie about what it served: an ack from a `peek` (look-don't-consume, the deliberate
  affordance) would silently consume.
- **The anomaly is bounded and self-healing in the designed flow.** The designed path is
  drain (stamps seen) → ack: no anomaly at all. The anomaly path is peek→ack (or out-of-band seq
  knowledge): the message is served ONCE more by the next stamping drain — rendered WITH its
  `acked_at`, i.e. the agent sees its own ack confirmed, which is informative, not a nag — and
  then converges. The only persistent case is an agent that acks from peeks and never drains,
  whose unread count over-reports until its first drain.
- **Over-notification is the SAFE direction for a delivery subsystem.** Under-notification is the
  loss class this subsystem exists to kill; a transiently inflated unread count is noise, not
  loss. The cry-wolf risk is real but lives entirely in RENDERS — so the law lands there:

**THE RENDER LAW (binding on 03b's drain telemetry and packet 04's `_comms_footer` contracts):**
1. **Ack-nudges key on `acked_at`, NEVER on `seen_at`.** "1 directive unacked" counts directive
   edges with no `acked_at`; an acked directive never re-nags regardless of seen state. The
   design's two-counter footer (`2 unread · 1 directive unacked`) is hereby CONFIRMED as the
   required shape — a footer collapsing both into one "pending" number recreates the cry-wolf
   this ruling exists to prevent.
2. **Queue counts key on `seen_at` and SAY "unread", never "unactioned".** `total_pending` /
   `directive_pending` describe what a drain will serve — and they must AGREE with what drain then
   serves (a count excluding what the very next drain renders is the silent-inconsistency class).
3. Served entries carry `acked_at` (they already do — `InboxEntry.acked_at`), so a re-served
   acked message is self-explanatory in the render.

**Cost.** Zero production change. Two pins + the render-law clauses in 03b/04's contracts.

**Instrument.**
1. Pin (03b, both legs): ack a never-drained message → the next NON-peek drain still serves it,
   the entry carries the ack's `acked_at`, it is counted in `total_pending`, and that drain stamps
   `seen_at` (convergence). Docstring carries the trade (*"seen = served, acked = actioned — the
   store records facts, renders own implications"*) and the RE-OPEN TRIGGER: **if fleet telemetry
   ever shows agents systematically acking from peeks and drowning in stale unread nudges, revisit
   at the RENDER layer first (de-emphasise acked entries in unread renders); the store-level
   seen-on-ack flip is last resort and requires re-opening the three contract pins named above —
   deliberately, with this ruling cited.**
2. The render law lands as contract clauses in 03b (drain telemetry render) and 04 (footer) —
   their contract authors cite this section; the adversary grades the footer fixtures against
   clause 1 specifically (an acked-directive fixture that still nags must go RED).

---

## Residuals & contradictions noticed (everything surfaced; the lead owns disposition)

1. **Live natural-language defect in `messages.py`:** `awaiting_answer`'s docstring parenthetical
   *"so the asker's own follow-up on its own thread is not an answer"* is FALSE under the shipped
   code for self-addressed follow-ups (green at every gate — the P2 false-gate class). R2's change
   makes it true; until R2 lands, the prose overclaims. Covered by R2; named so it cannot be lost
   if 03b re-scopes.
2. **Builder flag #5's direction analysis is backwards** — corrected in R4. Do not transcribe the
   flag's wording into any pin.
3. **Approved design vs shipped schema:** design says `message.seq` UNIQUE; store has no index at
   all; R3 rules a PLAIN index with a strikeable divergence note + re-open trigger (above).
4. **`(out, seen_at)`-covers-`out`-prefix is builder-asserted, un-probed** — closed by R3's
   EXPLAIN receipt + decision rule.
5. **Cross-session thread-string collision** (e.g. `dm:lead+fixer-b` recurring across sessions):
   the answer conjuncts carry no session equality, but agent ids are `uuid5(session:name)` —
   delivery targeting is session-bound by id construction, so a cross-session delivery to a
   session-dead asker is structurally unreachable today. No conjunct added (it would also break
   nothing-that-exists while complicating deliberately cross-session `task:<id>` threads). Recorded
   so the premise is visible: **it holds only while recipient resolution is roster-scoped** — if a
   future verb ever addresses agents across sessions, re-open here.
6. **Builder flag #4** (a plan doc changed mid-run): observed as commit `ac38246` (the retired-03b
   task-id fix, finding #174). Resolved; nothing owed.
7. **Store-reference gap:** no section on transactional READ isolation / snapshot semantics. Not
   needed by any current ruling (R4 refuses the transaction), but the gap is what makes the
   transaction non-cheap; whoever first needs it files the probe into the reference, not a brief.
8. **Render note for 03b, non-binding:** `already_acked` on a duplicate occurrence (R1) and the
   waiting line's clearing rule (R2: "cleared by any teammate's on-thread reply delivered to you")
   are both worth one teaching clause in the served render — the consumer is an LLM; the render is
   where it learns the contract.

## Consolidated implementation delta (for the lead's 03b builder brief)

| # | file | change | ruling |
|---|---|---|---|
| 1 | `loremaster/loremaster/messages.py::awaiting_answer` | deliveries SELECT gains `AND in.sender != $agent`; docstring three→four conjuncts | R2 |
| 2 | same SELECT | gains `AND in.thread IN $question_threads AND in.seq > $min_question_seq` (params from the questions read); `[real]`-leg proven, unbounded-indexed fallback documented if the engine rejects traversal-WHERE | R3 |
| 3 | `loremaster/loremaster/store/surreal_schema.py::_message_statements` | + `_plain_index(MESSAGE_TABLE, "message_seq", ("seq",))` + `_plain_index(MESSAGE_TABLE, "message_sender_question", ("sender", "question"))` — own one-concern commit, BEFORE 03b's deploy | R3 |
| 4 | `loremaster/tests/_message_fakes.py::FakeMessageLedger.awaiting_answer` | + `sender_id != agent_id` in the answer predicate — ORACLE change: contract author + adversary, never a builder drive-by | R2 |
| 5 | 03b contract | new pins: R1 duplicate-batch (+ non-adjacent variant) · R2 self-addressed-not-an-answer (incl. mixed-recipient leg) · R3 two index-presence pins · R4 read-order + short-circuit pin with KNOWN BOUND docstring + trigger | all |
| 6 | 03b exit receipts | 20-consecutive re-runs of send + ack concurrency pins post-index · EXPLAIN receipt for the `to` reads (+ decision rule for a `to_out` index) | R3 |
| 7 | — | no change: `ack` duplicate handling (ruled correct) · no derivation window bound · no stored pointer · no transaction | R1/R3/R4 |
| 8 | 03b contract | new pins: R5 same-thread one-answer-discharges-all + the answer-BETWEEN control · R6 acked-but-undrained is served once more (with `acked_at`), counted, then converges | R5/R6 |
| 9 | 03b instructions block | one-thread-one-debt teaching + re-ask recovery (static text; send-time thread-scan REFUSED) | R5 |
| 10 | 03b + 04 contracts | THE RENDER LAW: ack-nudges key on `acked_at` never `seen_at`; queue counts key on `seen_at` and say "unread"; counts agree with what drain serves; two-counter footer confirmed required | R6 |
| 11 | — | no change: stamps stay independent (three committed pins mechanically require it — verified) · per-question FIFO matching refused · answers-to column refused | R5/R6 |

## Tool honesty

Every file read directly (paths supplied by the spawn brief — no structure search needed). Greps
were used for test-name/pin sweeps and DDL-statement location (non-symbol textual seams — the
honest-grep category); `lore_impact`'s consumer-set answer was consumed from the builder's report
receipt, not re-run. No lore friction encountered; nothing filed.
