# REPORT-fable-design-05a — the WAIT SURFACE, design guidance under the Consumer Law

brief-base v10 read
brief project v7 read

## Summary block
- **State:** done — five design questions answered, each a recommendation + its fork, never a decision.
- **Deviations:** none.
- **Packages considered:** none — no mechanism specified (this is a design doc; every mechanism named here is already-built lore code — `awaiting_answer`, `render_attributed`/fence, the `to`/`briefed`/`message` graph — so the packages question is the framing one level down: **ONE IMPLEMENTATION** — 05a reuses the shipped `awaiting_answer` derivation and the shipped injection-containment seam, it does not hand-roll a second copy of either. Called out per-question below.)
- **Graded:** read at `ee1d19a` · HEAD-at-report `ee1d19a` · SAME. (Q5 renders a design review of the plan's `await` semantics + DD-4; no verdict on a builder artifact. Ground-truth reads: `messages.py::drain`/`awaiting_answer`/`WaitingOnAnswer`/`InboxEntry`/`MessageDrainResult`, `server.py::_render_comms_fleet(_row)`/`_render_age`, all at `ee1d19a`.)
- **Decisions-needed (operator forks surfaced, none decided here):**
  1. Q1 fault line — which sub-packet DEPLOYS first (lowest-risk reads vs. coupled consume-path core).
  2. Q2 — USE (recommended) vs REMOVE the `awaiting_answer` mechanism.
  3. Q4 — #304 fix shape: age-the-declaration (recommended, +1 `agent` field) vs auto-clear (rejected here as false-not-waiting) vs derive-into-fleet (forbidden by DD-2.a).
  4. Q5(ii) — await's LIVE-WHERE inline key: agent-id-only (recommended) vs thread-in-LIVE-with-charset.
- **Receipt pointers:** Q1 §Q1 · Q2 §Q2 · Q3 §Q3 · Q4 §Q4 · Q5 §Q5 · cross-cutting coupling (Q2↔Q5) §Q5(iii) and §Cross-cutting.

Sources cited section-exactly, never re-transcribed: `docs/plans/v2/05-comms-await-story.md` (Scope IN; the SPLIT box), `docs/plans/v2/comms-subsystem.md` (tool-surface table + Honest limits), `docs/plans/v2/03b-deferred-design-rulings.md` (DD-2/DD-2.a/DD-2.b, DD-3.e, DD-4/DD-4.c/DD-4.d), `docs/reference/surrealdb-31-capabilities.md` (§10 LIVE SELECT, §8 hazard #819), `~/.claude/plans/one-of-claude-codes-nifty-garden.md` (§"await semantics", the tool table §213-225), findings #190/#195/#214/#304/#332, and code symbols named in the Graded line.

---

## Q1 — THE SPLIT: decompose 05a into bootable sub-packets ≤ ~0.25

**The fault line is the drain SELECT projection + `InboxEntry` model + the consume path.** Everything that reshapes that surface must land in ONE session (the lead's own coupling rule); everything that only READS existing state is independent. That yields three sub-packets.

### 05a-i — THE CONSUME PATH (the coupled core) · ~0.25 · DEPLOYS the message-path work
The one session that reshapes `drain`. Contents:
- **#190 oracle parity FIRST** — the entry gate. No message-path pin in this sub-packet is valid until `FakeMessageLedger` renders production's prose (finding #190: the D4 broadcast defect passed *because* the oracle diverged). It is an oracle + adversary change whose satisfiability receipt covers BOTH `test_message_ledger.py` AND `test_comms_tool.py` (inherited delta row 6, measured-false single-consumer premise). Build the parity INVARIANT (every oracle error type ⇒ same prose as production's), not a one-string edit — #190's own instruction.
- **`since=`/paging drain reshape serving SEEN rows (DD-4.c)** + **#183 (bound the pending read)** + **`stamped_seqs` truth-or-delete (DD-4/Q5 residual)** — ONE reshape of the drain read path. DD-4.c: `since=` MUST serve seen rows keyed by seq or D11 returns to the operator (`03b-deferred-design-rulings.md` §DD-4.c). #214 is the live receipt this rests on.
- **R1 per-row `question` marker on `InboxEntry`** — the ORACLE + model change (05 Scope IN §R1). NOTE (ground truth `ee1d19a`): `message.question` **already exists** (set by `set_status='input_required'`, read by `awaiting_answer`), so R1 is a **projection + model** change (add `question` to the drain SELECT and to `InboxEntry`), **not a schema change** — cheaper than the packet's "oracle + model change" framing implies, though still oracle-by-law.
- **DD-2.a waiting mechanism** — the `waiting:` line on `drain` AND `heartbeat` via ONE shared helper, prose DERIVED from typed `WaitingOnAnswer` (see Q2). The helper + the two verb wirings live here; `await`'s consumption is 05a-ii.

This is the only sub-packet touching `InboxEntry`/the drain SELECT — so the coupling rule ("without two sessions both reshaping drain") is satisfied by construction.

### 05a-ii — AWAIT (the heavy Opus-4.8 LIVE leg) · ~0.20 · depends on 05a-i
- `await`: snapshot-first (RE-USES 05a-i's reshaped drain SELECT, **read-only — it does not re-reshape it**), filtered LIVE-on-edge + poll fallback, honest empty on timeout, the LIVE-on-edge build probe, the injection pin (Q5(ii)), and **await's timeout render = the first consumer of DD-2.a's waiting state** (Q5(iii)).
- Because 05a-i has already reshaped drain, await consumes it read-only — no second reshape. This is why await is a SEPARATE session after 05a-i, not folded into it: folding pushes the size back to ~0.45; separating keeps each ≤0.25, and await's distinct risk profile (unproven LIVE-on-relation, Opus-4.8 roster) wants its own entry/exit.

### 05a-iii — READ COMPOSITIONS + FLEET HONESTY · ~0.15–0.20 · independent
- **`story`** (task-anchored lineage), **rollup extension** (messages/fleet/skew sections), **`comms_cli.py`** (read-only SELECTs; absent at `ee1d19a`, confirmed) — all read-only compositions over EXISTING edges.
- **#304 fleet badge + R4 fleet unread/unacked columns** (#332 re-homed both here) — fleet-render honesty (Q4).
- Touches NO drain SELECT reshape. Reads agent rows + to-edge counts + existing message/edge state. Can boot and deploy independently.

### Dependency graph + sequencing
```
05a-iii  (independent) ─────────────┐  ships backlog + #321 at LOWEST risk
05a-i    (gated only by #190) ──► 05a-ii (await)
```
- **05a-i and 05a-iii are mutually independent.** 05a-ii depends on 05a-i (needs the reshaped drain SELECT AND the DD-2.a waiting helper for its timeout render — see Q5(iii)).
- **Keep `story`/`rollup` rendering over EXISTING state** to preserve 05a-iii's independence. If rollup/story must surface the NEW waiting derivation, that part follows 05a-i — flag it, don't couple silently. `story` marks question/answer STRUCTURALLY from `message.question` (already exists), so it needs no DD-2.a dependency.

### Which sub-packet DEPLOYS
All three ship served surface, so each needs rebuild+recreate BOTH. The accumulated 04b-3/04b4/04b5 commit-only work (incl. #321) is already in the tree — **the FIRST 05a deploy of any sub-packet ships the entire backlog + #321 live.** #321-before-pkt-56 is wave D (far off), so nothing forces WHICH sub-packet carries it.

- **Recommended: 05a-iii deploys FIRST** to ship the backlog + #321 at the lowest blast radius (read-only compositions + an honesty-improving fleet render — the only served-surface *change* is #304's, and it improves honesty). This decouples "get #321/backlog live" from "the risky drain reshape."
- **Fork (operator):** if the operator wants the message-path surface live earliest, 05a-i deploys first instead — but that is the highest-risk-to-existing-consumers deploy (the drain render changes shape). Recommend against unless #321 urgency changes.
- **Deploy-count sub-fork:** 05a-i and 05a-ii MAY share ONE deploy (await's verb + the drain reshape ship together as one consumer-facing change) even though they are separate BUILD sub-packets — recommended, to minimize consumer-facing churn. 05a-iii deploys separately (its own, first).

### Each half's Leg-1 scope-diff + deploy risk
- **05a-i:** Leg-1 diffs to render — `since=` serves SEEN rows ≥ N (name: "already-seen; new unseen traffic still comes from a plain drain"); the `question` marker means "this MESSAGE asked you something," not "you owe an answer"; the `waiting:` line's four-conjunct meaning + out-of-band-answer known bound. **Deploy risk: moderate** — drain render changes for existing consumers; R1 is projection-only (no DDL). The #131/#139 "test env is a fiction" risk applies (run the in-image conformance). #190 parity is the gate: skip it and every message-path pin inherits D4's blindness.
- **05a-ii:** Leg-1 diff — await is snapshot-FIRST (returns immediately on already-pending unseen traffic; it is NOT "only-new"), ≤55s bound, honest-empty names the bound, LIVE is a contentless wake and never a source of truth. **Deploy risk: higher** — LIVE-on-relation is UNPROVEN in this SDK (build probe MANDATORY; poll fallback documented), the socket-drop error shape needs re-probing on the live engine (now 3.2.1, not 3.1.5), the inlined LIVE-WHERE literal is an injection surface (Q5(ii)). De-risked by the poll fallback (await works even if LIVE never fires). This is why it is the Opus-4.8 leg.
- **05a-iii:** Leg-1 diff — `story` names its SET (this task/thread's arc) and what it OMITS; #304's fleet badge honesty (Q4). **Deploy risk: LOWEST** — read-only over existing edges; the only served-surface change is the honesty-improving fleet render (+ possibly one `agent` field, Q4).

---

## Q2 — DD-2.a: USE vs REMOVE the `awaiting_answer` mechanism

**Recommendation: (a) USE it — give `awaiting_answer` its first production consumer.** The fork stated for the operator: (a) wire the waiting line (drain + heartbeat) + await's timeout render, per DD-2.a; (b) adjudicate the WHOLE mechanism for removal (method + `WaitingOnAnswer` + the `(sender, question)` index + the R3 narrowing).

### Consumer-Law reasoning
- **Does the asker seeing its own outstanding conversational debt earn trust? YES — strongly.** The subsystem exists because native comms lose messages silently. Today an agent that asked a question and got no answer has NO served surface telling it "you are still waiting on #S, thread T" — it must REMEMBER. That is exactly the "route around the tool" tax the Consumer Law forbids: an agent that can't SEE its own debt either re-asks (noise) or proceeds as if answered (the dangerous inference). The `waiting:` line converts a remember-to-check into a served FACT, aged off the real `asked_at` (`WaitingOnAnswer.asked_at` is the question's own `created_at`, never fabricated). This is the highest-value trust move in the packet.
- **Is a dead-but-indexed mechanism a liability? YES.** It is finding D7's exact complaint (`03b-deferred-design-rulings.md` §DD-2 Facts): a `(sender, question)` index and an R3 narrowing that NOTHING calls carry cost (schema surface, reader confusion) for zero value, and stand as a standing invitation for a future engineer to either wire it WRONG (the conflation below) or delete it and re-open R1. A live mechanism is cheaper to maintain than a dead one wearing a live index.
- **The mechanism is already BUILT, TESTED, and CORRECT** (`ee1d19a`): the four-conjunct derivation (delivered-to-me · on-thread · after · from-another-agent), the R2 self-note ruling, the known-bound pin for out-of-band answers. Removal throws away correct tested design AND blinds agents to their own debt — the anti-trust outcome. **ONE IMPLEMENTATION:** (a) reuses this derivation; it does not re-derive a waiting flag (the #104 law — prose derives from the typed `WaitingOnAnswer`).
- **(b) is only justified** if the operator judges the question-debt surface not worth ANY render real estate. The Consumer Law weighs hard against that, and the packet's own third-deferral clause means declining (a) is not a quiet option — it escalates as an operator fork regardless. So the honest choice is (a)-or-escalate, and (a) is the cheaper, trust-earning one.

### The discriminating pair that stops the wrong build (CONFIRMED)
The wrong build DD-2 forbids: wiring "waiting" to the STORED `input_required` status (the two-vocabulary conflation). At `ee1d19a` the two vocabularies are cleanly separated at the WRITE side, which is what makes the pair discriminate:
- STORED `agent.status = input_required` — set ONLY by `heartbeat status=input_required` (a self-declaration; `send set_status` deliberately does NOT touch the status row, r2 B2.5).
- DERIVED debt — `message.question=true AND sender=me` with no on-thread answer, read by `awaiting_answer`. Set by `send set_status='input_required'` (which sets the message column, not the agent status).

The pin pair (both fixtures REQUIRED; they use DIFFERENT values per the FIXTURES-MUST-DISCRIMINATE law):
1. Agent with stored `active` status + an unanswered question → **the waiting line RENDERS.** (A build reading `agent.status` MISSES this — false negative.)
2. Agent with stored `input_required` (via heartbeat) + NO outstanding question → **the waiting line does NOT render.** (A build reading `agent.status` FALSELY renders — false positive.)
A build keyed on stored status fails BOTH; a build keyed on the derived `awaiting_answer` passes BOTH. Confirmed as the DD-2.a-named pair.

### One cost to price (not a blocker)
The emit predicate `awaiting_answer(agent_id) is not None` costs TWO indexed reads per drain/heartbeat (the `(sender,question)` index + the R3-bounded deliveries read). DD-2.a accepts this as "the same order as the ~3 point reads B4.1 priced for skew-at-drain." Confirmed reasonable for drain/heartbeat (one per-agent derivation) — and it is exactly why **fleet must NOT** do it per row (N derivations = the N+1 DD-2.a bars; see Q4).

---

## Q3 — #195 HOME: is there a distinct injection-resistance surface affordance for 05a?

**Recommendation: the OBEDIENCE measurement settles WHOLLY as a 06 drill measurement. 05a's surface-affordance duty is NARROW and is CONTAINMENT REUSE, not a new instrument — plus one net-new structural-legibility gain in `story`.** 05a must SAY it declines the obedience-measurement (hands it to 06), not pass over it silently (finding #195's named-decision-point clause).

### Reasoning
- **Obedience is a CONSUMER-BEHAVIOR property, not a render property.** #195's gap is "nothing measures whether an agent OBEYS an instruction inside a body — legible ≠ inert." A render can make body content LEGIBLE-as-quoted (04b5's #321 `render_attributed`/fence already does: labels the fence, names its author, states nothing inside is a delivered message). A render CANNOT make an LLM INERT to an instruction it reads — that is measured by a drill that plants an in-body instruction and checks whether the agent acts on it. So the obedience instrument is 06's (the live multi-agent exercise is the natural home), exactly as the packet routes it.
- **05a's real duty is DON'T-REGRESS-04b5 on its new renders (ONE IMPLEMENTATION).** Every NEW 05a render that emits stored free text MUST route through the SAME shipped `render_attributed`/fence seam — it must not hand-roll a second containment nor emit a raw body outside the fence. The surfaces at risk:
  - **`story`** renders the task's MESSAGE ARC — bodies, refs, ack_notes. This is the biggest new free-text surface in 05a and the one most likely to leak a raw body. It MUST fence bodies, pinned with a HOSTILE fixture (the P8d / 03b rendered-free-text law: newlines + an output-format-shaped forgery line + backtick runs) — the same fixture class `drain` already carries.
  - **`await`'s timeout render** and the **`waiting:` line** derive from TYPED state (`WaitingOnAnswer`) — low injection surface; the only free text is the `thread` label, which is length-bounded (DD-3) and sanitised (`sanitise_line`). Safe by construction; no new affordance needed beyond the existing sanitiser.
  - **`since=` re-read** renders bodies exactly as `drain` does → inherits `drain`'s fence; pin it re-uses the same hostile fixture.
- **The one net-new legibility gain worth adding:** `story` marks question/answer messages STRUCTURALLY from `message.question` (which exists), so the LEAD reading "why is this stuck" reads intent from TYPED state, not from body prose — reducing the surface where a forged "I already answered you" body could mislead the reconstruction. This is a legibility gain (Leg-1-shaped), not an inertness one; it does not close #195, and 05a should not claim it does.

**Net:** 05a needs NO new injection instrument. It needs (1) every new render that emits stored free text to route through 04b5's fence with a hostile-fixture pin, and (2) the `story` structural question/answer marker. The obedience gap is explicitly handed to 06's drill, said out loud.

---

## Q4 — #304/#332: the latched fleet badge

**Recommendation: AGE-THE-DECLARATION — render the stored `input_required` self-declaration WITH the age since it was declared, so it is a dated FACT, not a live VERDICT.** This is #332's/S2's "serve a fact, not a latched verdict" principle one field over. It requires one new `agent` field (`status_set_at` or equivalent), stamped write-side only when the status VALUE changes.

Ground truth at `ee1d19a` (correcting #304's premise per #332): `_render_comms_fleet_row` renders `[{status} ⚠ STALE]` where `⚠ STALE` IS derived-at-render (from `heartbeat_age_s` via `_render_age`) — the weaker acceptable form, NOT retired. The remaining LATCH is the `{status}` cell itself: `agent.status = input_required` set via `heartbeat status=` never self-clears (it wins over the idle→active auto-flip), so the badge outlives the debt.

### Why age-the-declaration, and why the alternatives lose under the Consumer Law
- **The Consumer-Law problem:** a bare `[input_required]` reads as a VERDICT ("this agent needs input NOW") when it is a LATCH ("declared at some past point, never updated"). Under the hard trust definition, a consumer acting on `[input_required]` without checking can be wrong in a way the badge did not name (the debt was discharged 40m ago). Rendering the DECLARATION AGE beside the liveness age fixes exactly this: `- name [input_required 47m] hb 5s · …` — a FRESH `hb 5s` beside a STALE `47m` declaration is itself the signal that the badge is a latch. The consumer SEES the contradiction (active liveness + old self-declaration) instead of being told a verdict. This is #304's option (b) done right and S2's fact-not-verdict shape.
- **Auto-clear (reject).** "Clear the latch on some event" has no HONEST event: the stored status carries no thread, and the only available signal is the agent's own next action — but drain/heartbeat/ack mean ACTIVITY, not "the input arrived" (#304's body says this verbatim: "the drain that RECEIVED the answer" ≠ the answer). Making `input_required` not-win the next auto-flip would flip a genuinely-parked agent (heartbeating every 30s while waiting on an operator) to `active` — manufacturing a **false-not-waiting**, the INVISIBLE error direction ruling 9 refuses. Auto-clear is the WORST option here, not the cheapest.
- **Derive-and-reconcile into fleet (forbidden).** Replacing the stored badge with the derived `awaiting_answer` per row is (i) the N×2-query **N+1 DD-2.a explicitly bars** at the 200-row fleet cap, and (ii) the WRONG VOCABULARY: `awaiting_answer` is question-DEBT (an unanswered lore question), while `input_required` is a self-declaration an agent may set for reasons ORTHOGONAL to any lore question (waiting on an operator out-of-band, a human decision, a non-lore dependency). Conflating them is precisely the DD-2 hard-rule violation. Fleet keeps rendering the STORED self-declaration; the DERIVED debt surfaces on the agent's OWN drain/heartbeat waiting line (Q2), never in fleet.

### Mechanics + the discriminating pair
- **Write-side:** stamp `status_set_at` only when the new status ≠ the current stored status (else it always reads "0s"). Rides the existing agent UPDATE on heartbeat/register — no extra round-trip. Store law: `DEFINE FIELD OVERWRITE` for the field, `IF NOT EXISTS` semantics per `surrealdb-31-capabilities.md` §1.1 (cite, don't re-transcribe); it is an `option<datetime>` on `agent` — a store/schema change, so this rides 05a-iii's own contract+adversary, and the free-window / dirty-store reasoning must be checked against §1.4/§1.6 (existing agent rows get NONE → render falls back to "declared: unknown / since hb" — decide the NONE render explicitly).
- **Read-side:** the `status_set_at` rides the existing agent-row read — **NOT a per-row derived query**, so DD-2.a's N+1 objection does not apply (that objection is about deriving `awaiting_answer` per row; a stored timestamp is free).
- **Discriminating pair (wrong build = wiring fleet to `awaiting_answer`):**
  1. Agent declared `input_required` via heartbeat, NO outstanding lore question (waiting on an operator out-of-band) → fleet STILL shows `input_required` with its age. (An `awaiting_answer`-derived build shows NOTHING — false-not-waiting.)
  2. Agent with `active` status + an outstanding lore question → fleet shows `active`; the debt surfaces via the agent's own waiting line, not fleet. (A conflating build wrongly badges fleet.)

### Fork stated
Age-the-declaration (recommended, +1 `agent` field, honest) **vs** leave-stored-as-declared with no age (cheapest, but keeps the undated-verdict trust trap #304 filed) **vs** auto-clear (rejected — false-not-waiting) **vs** derive-into-fleet (rejected — DD-2.a N+1 + wrong vocabulary). ⚠ NOT MEASURED and worth a cheap check the builder owes (per #304's own tail): whether `last_note` and OTHER explicit statuses (`retired`, `idle`) latch the same way — if so, the age applies to the whole status cell, not just `input_required`.

---

## Q5 — AWAIT under the Consumer Law (review, not re-design)

The plan §"await semantics" (`one-of-claude-codes-nifty-garden.md` §227-242) + DD-4 own the mechanism. Sanity-check only.

### (i) Honest-empty-on-timeout render + its trust legs — SOUND, with three conditions
- **Leg-1 scope diff (what await ACTUALLY answers vs what the caller thinks).** The caller's mental model is "block until something NEW happens." The actual mechanism is snapshot-FIRST (step 1 runs the drain SELECT; pending traffic returns IMMEDIATELY) — so await answers *"is there UNSEEN traffic for me now, or within ≤55s?"*, NOT "wake me only on new arrivals." **Trap flagged:** a caller can get an instant non-empty return on OLD unseen rows and misread it as "something just arrived." The render should make the snapshot-first behavior legible (await is drain-with-a-wait, not only-new). The `≤55s` bound and the honest empty must be stated as FACTS (the time, the set), not disclaimers — "no new traffic after {N}s" names the bound; good.
- **The completeness bound is the poll floor, and the render must not over-claim.** LIVE is a contentless wake, never a source of truth; the drain SELECT at each wake/poll/timeout is authoritative. So await's honest claim is *"no unseen traffic AS OF my final snapshot at timeout"* — NOT a continuous guarantee. A message arriving in the last <5s before timeout is caught by the final re-read (the plan's step 3 re-runs the drain SELECT on any wake; ensure a FINAL snapshot at timeout, not just on wakes). State the bound as a fact.
- **Leg-2 forgery pin (the load-bearing one):** await's dependencies × {stale, empty, wrong-instance, partial}. The critical false-clear is **a dropped LIVE subscription serving a false EMPTY** — the SDK silently orphans `live_queues` on a socket drop (§10). The poll fallback + the final drain-SELECT snapshot is what prevents it. **REQUIRED forgery pin:** kill the socket mid-await with pending traffic present → assert await STILL returns that traffic via the poll path, does NOT serve a false-empty. This is the build-time probe's real acceptance criterion, not just "does LIVE fire."

### (ii) Injection safety of the mandatory inlined LIVE-WHERE literal (DD-3.e) — inline the AGENT-ID, never `thread`
- DD-3.e (`03b-deferred-design-rulings.md` §DD-3.e) is explicit: `thread` is a bound param EVERYWHERE today, has NO charset validation (length-bound only, because the taught `q:<topic>` convention contains `:` which `AGENT_NAME_PATTERN` forbids), and **await inlining `thread` into a LIVE WHERE is DD-3.e's NAMED re-open trigger** — "05's await design MUST consult this ruling before touching thread in a LIVE clause." I consulted it; the answer is:
- **Recommendation: await filters the LIVE on the AGENT-ID only — `WHERE out = agent:⟨uuid5-id⟩` — and NEVER inlines `thread`.** The agent-id is `uuid5(session:name)`: a hex/uuid literal derived from charset-ASSERTED name/session (the plan §230-232 says exactly this: "safe because ids derive from charset-ASSERTed name/session; pin this in tests"). It contains ZERO caller-controlled free text — it is a hash, injection-safe BY CONSTRUCTION. This SIDESTEPS DD-3.e's re-open trigger entirely: await never inlines `thread`, so the charset-then-inline obligation never arises and DD-3.e stays un-triggered.
- **If `await` takes a `thread?` param** (the plan shows `await(agent, thread?)`), apply the thread filter CLIENT-SIDE on the authoritative re-read (the drain SELECT / snapshot, where `thread` IS a bound param), NOT in the LIVE WHERE. The LIVE is a contentless wake with a DISCARDED payload — filtering it precisely on thread buys nothing operationally (a thread-mismatched wake just triggers a re-read that finds nothing new and re-waits), while inlining thread would open the exact injection door DD-3.e names. So: **LIVE WHERE = agent-id literal ONLY; thread filtering = client-side on the snapshot.**
- **Fork (operator), with a strong lean:** agent-id-only inline (recommended — sidesteps DD-3.e) vs thread-in-LIVE-WITH-charset-ASSERT (would REJECT the taught `q:<topic>` convention — self-defeating, and buys only wake-filtering precision on a discarded payload). Recommend agent-id-only firmly. The injection pin: assert the emitted LIVE statement inlines only the uuid5 id and carries no caller free text (the plan's "pin this in tests").

### (iii) The Consumer-Law trap in await's timeout render when the caller's OWN question is outstanding — REAL, and it couples to Q2
DD-2.a §3 makes await the natural first consumer of the waiting state. The trap:
- A bare honest-empty ("no new traffic after 25s") is TRUE but, when the caller has an OUTSTANDING question, it LICENSES the wrong action: the caller infers "nothing is happening, I can proceed" — while it is still owed an answer. Under the hard trust definition (§CLAUDE.md: trustworthy iff a consumer acting WITHOUT CHECKING cannot be wrong in a way the response did not name), **the bare empty FAILS** — it does not name the still-open debt, and the consumer is wrongly-unblocked in a way the response was silent about.
- **Fix (already designed):** await's timeout render consults `awaiting_answer(caller)` and, if non-None, appends the waiting state — the plan/DD-2.a shape *"timed out — still waiting on #{seq}, thread {thread}"* (derived from the typed `WaitingOnAnswer`, aged off the real `asked_at`). This NAMES the debt → the consumer cannot be wrongly-unblocked in a way the response didn't name → trust restored.

**Cross-cutting flag (Q2 ↔ Q5):** await's timeout-render trust DEPENDS on Q2 landing option (a). If the operator chooses (b) REMOVE the waiting mechanism, await's honest-empty becomes a Consumer-Law trap with NO fix — the bare empty cannot name a debt the system no longer tracks. So **choosing (b) does not just delete a dead mechanism; it REGRESSES await's timeout trust for the outstanding-question caller.** This tilts Q2 hard toward (a), and it is why DD-2.a's waiting helper (05a-i) must land BEFORE await (05a-ii) consumes it — consistent with the Q1 sequencing.

---

## Cross-cutting (one place, so nothing is buried)
1. **Q2(a) and Q5(iii) are coupled:** removing the waiting mechanism creates an un-fixable Consumer-Law trap in await. Recommend (a). Sequencing: DD-2.a helper (05a-i) before await (05a-ii).
2. **Two vocabularies, one rule, THREE surfaces:** stored `input_required` (self-declaration, fleet — Q4) vs derived `awaiting_answer` (question-debt, the agent's own waiting line — Q2) must never conflate. The SAME discriminating pair (stored-status ≠ derived-state) pins the wrong build on BOTH the fleet surface (Q4) and the waiting-line surface (Q2).
3. **ONE IMPLEMENTATION throughout:** 05a reuses `awaiting_answer` (Q2), reuses `render_attributed`/fence (Q3), reuses the drain SELECT read-only in await (Q1/Q5) — it hand-rolls no second copy of any of them.
4. **#190 oracle parity is the entry gate for the whole consume-path sub-packet (05a-i)** — no message-path pin is trustworthy until it lands. Build the INVARIANT, not a string edit.

_This doc proposes; the operator rules, the lead adjudicates. Standing by for follow-ups (SendMessage — I am an at-rest consultant)._

---

## Follow-up rulings (2026-08-06) — 05a-iii contract forks
The operator delegated ruling authority on design forks to the lead tonight; the lead relayed two. Grounded against `test_comms_fleet_grouping.py:111-126`, `config.py::SurrealConfig` (`:226`), `config.py::LoreConfig` (`:559`) at HEAD (`ee1d19a`, unchanged from my Graded base).

### RULING — FORK 1: #304 age scope = **(a) input_required-ONLY** (ratify the contract's pin)
This discharges the "NOT MEASURED" flag in my Q4; the contract author's measurement is CONFIRMED against ground truth.
- **Consumer-Law reason:** the #304 defect IS the latch — `input_required` is the one status that wins over the idle→active auto-flip, so it alone goes stale WHILE the agent works. Age-the-declaration earns trust by exposing the CONTRADICTION between fresh liveness (`hb 5s`) and a stale self-declaration (`input_required 47m`). `idle`/`active` carry NO such contradiction — a fresh heartbeat keeps them current — so aging them exposes nothing and renders `active 3s`, pure noise that violates the render-density law (client render law §1: context density > churn).
- **C-DEF trap avoided:** option (b) contradicts the GREEN pins `test_comms_fleet_grouping.py:124-126` (`assert "[idle]" in …` / `assert "[active]" in …` — bare brackets), trapping the builder between the new contract and a suite it may not edit, for ZERO trust gain. Confirmed by reading the pins.
- **Why not (c) latching-subset:** the safe set is a measured single member; (c) is (a) with generality for a set of one — YAGNI. **BUT the pin must be keyed on the PROPERTY, not left as a bare literal that a future latching status silently escapes** (the enumerate-the-forbidden trap). Ruling rider: the render conditional carries a comment naming the property (*"aged because it is the one status that wins over the auto-flip and can go stale while the agent works"*) + a **named re-open trigger: the day any status other than `input_required` is made to win over the auto-flip, the age-scope re-opens.** That is (a) built, with (c)'s door documented not built.

### RULING — FORK 2: comms_cli default = **(a) resolve via the server's OWN `SurrealConfig`, reused not cloned**
- **The reuse seam is real and named:** `SurrealConfig` (`config.py:226`) already resolves `url` / `namespace` / `database` (None → project-slug-derived via `LoreConfig.effective_surreal_database`) and creds by env-var NAME through `resolve_secret` (fails loud if unset, never inlined). comms_cli reads THIS off the project's `lore.yaml`; it does NOT hand-roll a second coordinate resolver (ONE IMPLEMENTATION — a cloned resolver is where a config change reaches the server and not the CLI).
- **The "tests → :18000, never :18500" law does NOT bar this — it binds TEST code, not production tooling.** The CLI is the idle-gate HOOK BRIDGE (`python -m loremaster.comms_cli pending --agent <name>`, design §Hook bridge): in a live session it must read the REAL fleet, which lives in production lore-surreal (:18500) — the same store the running server uses. `pending` is read-only (SELECTs only, contract-pinned), so production blast radius is nil.
- **Why not (b) require-explicit-no-default:** it forces the coordinate into the idle-gate SHELL wiring (settings.json / the hook script) — hardcoding :18500 in bash, where the AST guard cannot see it and where it now DUPLICATES the config value. That is strictly worse under ONE IMPLEMENTATION and the no-hardcoded-coordinate law, not safer.
- **Why not (c) env-var default:** env is an OVERRIDE layer (the explicit-arg path already covers it), not the default source; a third competing coordinate source is more divergence surface (and env is fragile under cron). Config is the default; explicit args/env override.
- **Riders (bound the only ways (a) could trip the safety law):** (1) the no-hardcoded-`:18500` AST guard STAYS — the coordinate is resolved, never literal. (2) **No CLI test exercises the config-DEFAULT path against a live production store** — default-resolution is tested by asserting it READS the config value (a fixture pointed at :18000, or a pure-resolution assertion), never by connecting to whatever the real `lore.yaml` names. Tests keep using the explicit `--url` override to :18000 (already pinned). (3) **Builder-verify:** `load_config` resolves the Anthropic key EAGERLY (`LoreConfig` docstring) and `anthropic:` is REQUIRED — a creds-free read-only CLI must not be blocked by a missing Anthropic key it never uses. If `load_config` hard-requires it, the CLI needs a surreal-block-only parse — that is a legitimate narrow hand-roll of the LOADING (the two-sided rule: the full loader doesn't fit a creds-free CLI), but the RESOLUTION logic (url/ns/db/secret) stays the shared `SurrealConfig`. Flag, not a redesign.

### Builder-latitude items — CONFIRMED, no objection
A3 question-marker glyph, rollup section content shapes, D8 NONE-render wording are fine to leave to the builder within their pinned properties. One nudge on D8: the NONE render (existing `agent` rows with no `status_set_at`) must be HONEST per Q4 — *"declared: unknown"* / age-since-hb, never a fabricated age — which is inside "pinned properties," just naming the trap.
