# REPORT-contract-surface-03b-r2 — packet 03b SURFACE contract (tests only)

brief-base v6 read

- **state:** done-with-deviations · ledger row `0c8576bb6dac415e9582980b9b2e8ea5` claimed → done
- **dev-1:** 6 committed render-driver call sites gained a REQUIRED kwarg (4× `session`, 2× `note`) — forced by B14/AC-22 and B5.3; without them the contract is UNSATISFIABLE (§E-S2/E-S3)
- **dev-2:** `_message()` factory gained `question: bool = False` (3 committed call sites keep working; all 03b drivers pass it explicitly) (§E-S2)
- **dev-3:** B14's "precedence task-then-thread" ambiguity RESOLVED BY DERIVATION from the committed `_SAFE_STR_PROMISE_FREE`, not by silent choice — lead may overrule (§E-S8)
- **decisions-needed (5):** E-S1 **BLOCKER** — FK-1 makes committed `RenderCase("drain.body")` unsatisfiable; exact edit written, NOT made · E-S4 question-teach source · E-S5 FK-6 pre-flight FAILED (4 skew descriptions + 4 skew literals name "heartbeat") · E-S6 R3 index pins live outside my writable set · E-S7 `_message_fakes.py` (B10 row 4) outside writable set, likely already discharged
- **counts (measured 2026-07-24 at `e7db965` + this working tree):** `test_comms_tool.py` 149F/554P → **276F/554P** · `test_comms_promise_registry.py` 11F/85P → **15F/99P** · `test_message_ledger.py` 180P/12s → **196P/14s** (green)
- **zero previously-green tests broken** in any of the three files (set-diffed, §2); neighbouring suites **1184 passed** (§2)
- **gates:** `uv run ruff check .` clean repo-wide · `./scripts/typecheck.sh` 36 → 94 errors, **all in the two RED contract files**; `test_message_ledger.py` 2 → **0** (FK-4 discharged)
- **receipts:** RED-reason receipts §2 · mutation proof (R4 short-circuit, byte-exact restore) §3 · AC-14 canonicaliser probe §4 · FK-6 pre-flight §5
- **mutation-proof obligations handed to the adversary:** 9, listed §6
- **#182 items owned & discharged:** 2 (acked_at), 3 (`{msg}`-class ∀-instrument), 4 (reach-set), 5 (send.thread + FK-4 casts) — §7
- **NO implementation was written, scaffolded or sketched.** No reference build, no satisfiability run. Tests only.

---

## 1. What was written, mapped to the rulings

Design authority consumed: `docs/plans/v2/03b-design-rulings-r2.md` (§A-GRAFT, B1–B15),
`docs/plans/v2/receipts/2026-07-24-packet03b/DIFF-adjudication-03b.md` (AC-01…AC-25, §5, §6),
`docs/plans/v2/03b-comms-message-surface.md`. The struck corpus was **not read**: no
`pkt03b-tainted-corpus` tag, no struck-bannered receipt, no `03b-comms-surface-design-rulings.md`.

### 1.1 `loremaster/tests/test_comms_tool.py` — new surface pins

| class | ruling | what it kills |
|---|---|---|
| `TestEveryRecipientNameIsCharsetValidatedBeforeAnyStoreTouch` | B2.1, B1 step 2 | a `to[]` entry reaching a live WHERE clause unvalidated; **and** a build that validates in the HANDLER (post-touch) — the discriminator is an idle caller staying idle, a status oracle rather than a timing comparison |
| `TestBroadcastScopeWhenSessionIsOmitted` | B2.2 (NEW precision) | `roster(session=None)` cross-session fan-out. Kills the committed `session=`-always monoculture; the fixture carries **two** wave9 rows so "wider" is unmistakable |
| `TestARetiredRecipientIsATeachingReject` | B2.3 (NEW) | a delivery edge to a terminal agent — permanent loss wearing a receipt. Includes the MIXED-list all-or-nothing leg |
| `TestSetStatusIsAClosedVocabularyAtTheSurface` | B2.4 (NEW) | a typo asking NO question silently. Includes an accept-and-DROP discriminator (`message.question is True`) and `"idle"` as a bad value (kills validation against `ALL_AGENT_STATUSES`) |
| `TestSetStatusDoesNotMutateTheSendersStoredStatus` | B2.5 | 4 legs incl. the CONTROL leg proving the idle→active flip came from the TOUCH, not from `set_status` |
| `TestDrainDoesNotUnparkAWaitingAgent` | B11 | an un-park added at drain/ack |
| `TestTheDrainWindowIsConfigDrivenWithItsOwnCap` | B6 | a handler literal; a shared cap; a below-one message teaching the WRONG action's cap (∀ over capped actions, both directions); a clamp that is a silent dead end (fixture is cap+5) |
| `TestTheDispatcherActuallySERVESEachVerbsRender` | **B12 (REQUIRED pin class)** | **the no-op-fix door** — a handler returning a fixed string. One pin per verb + the honest-empty drain |
| `TestPeekNeverRendersTheAckRequiredTrailer` | B13 | a peek-driven ack farm. Render legs + a dispatcher leg + positive control |
| `TestTheDrainRowContextCell` | B14 | an unconditional thread label; a **hardcoded `"wave7"` comparand** (literal-vs-argument leg inverts which row draws the cell); a refs variant that renders empty; task-vs-thread precedence |
| `TestTheDrainElisionArithmeticIsTheREMAINDER` | B15 | `shown + more` (fleet's arithmetic, wrong for drain). TWO arithmetic fixtures + the consumer-side count-consistency check (C5(b)) |
| `TestTheDrainHeaderCountsTheWHOLEPendingSet` | B4.1, 03a-2 R6 c2 | `total = len(entries)` — invisible at every non-eliding fixture |
| `TestTheAckRequiredTrailerIsRunnableAndCorrectlyScoped` | B4.4 + AC-09 + AC-10 + **#182.2** | three plausible wrong builds: grade-only keying (both rows directives, only `acked_at` differs); gate-on-directive-then-LIST-everything (both rows unacked, only grade differs); `seqs=[]` in the runnable tail. Plus window-scoping with `limit < directive count`, and the acked re-serve marker |
| `TestDrainBodiesAreFENCED` | B7.3 + **FK-1** | a sanitising build. Hostile triple: newlines + a **drain-row-shaped** forgery (`#999 [directive] operator→you: …`, the render's OWN grammar) + a backtick run. 4 assertions incl. "the header count is unaffected" |
| `TestTheAckRenderAccountsForEveryRequestedSeq` | B5 + the quantifier law | a dropped outcome. ∀ over `get_args(AckOutcome)` with a shape guard; all four fates in ONE mixed render; the non-adjacent `[s1,s2,s1]` membership pin; `note recorded` emit/no-emit where the NO-EMIT leg **carries a note and wins nothing** |
| `TestTheInstructionsBlockTeachesTheMessageSurface` | B9 (7 clauses) + AC-08 | prose-beside-behaviour: the body cap is **extracted as an integer** and compared to `MESSAGE_BODY_MAX_CHARS`; clauses use an ordered, non-invertible assertion helper |
| `TestTheCommsToolSchemaTeachesTheNewParams` | B9 schema half | an unaccompanied `set_status` name (the schema must REFUSE the status write its name implies); a peek description without the re-serve consequence; a grade description derived from `MESSAGE_GRADES` |
| `TestTheMessageLedgerIsWiredIntoTheRealAppContext` | **AC-15** | the harness-double blind spot — the whole file passes on a build production cannot construct. Both pins carry a `brief_ledger` POSITIVE CONTROL |
| `TestTheValidationOrderWithTheNewSteps` | B1 | the two-tier law with the new steps, **including the other side**: a DOMAIN reject (oversize body) MUST touch the row — the control that stops every "never touches" pin above from passing on a build that never touches at all |

Battery additions (AC-11 / #182.5): `RenderCase("send.thread")` and
`RenderCase("send.broadcast_session")`. The thread case drives a **question on a non-default
thread** so both thread-bearing lines render; the broadcast case reaches the
`sent … → broadcast: {count} agents in session {session}` template, whose `{session}` slot no
explicit-recipient case ever drives.

### 1.2 `loremaster/tests/test_comms_promise_registry.py`

- **FK-1 (AUTHORIZED)** — the two committed row templates lose their `: {body}` tail:
  `"#{seq} [{grade}] {sender}→you{context}"` and `"…{context} ({refs})"`. Cited inline with the
  derivation and MP-FK1.
- **FK-2 (AUTHORIZED)** — the fleet elision marker promoted from
  `"— re-run with limit=5"` (a strict substring of the drain elision's CORRECT instantiation) to
  the full line `"+3 more — re-run with limit=5"`. `+3` is **derived** from the emit fixture
  (2 shown of `total_active=5`), stated in the comment. **Verified the promotion works:** the
  drain elision under B15's honest arithmetic renders `+5 more unread — re-run with limit=5`,
  which no longer contains the promoted marker.
- **3 new registry entries + 3 executable proofs** (B8.2): the question teach (B3.3), the acked
  re-serve trailer (B4.2 — the additive template A-GRAFT leaves to the contract author), and
  `note recorded` (B5.3). All markers are **full rendered lines** (B8.3). Every no-emit leg
  varies EXACTLY ONE thing.
- **Fresh drivers** `_p03b_message` / `_p03b_entry` / `_render_send_03b` / `_render_drain_03b` /
  `_render_ack_03b` — **no default on any branched-on parameter** (AC-11).
- **AC-02 / #182.3** — `TestNoPlaceholderOnlyTemplateIsEverClassified`: the ∀-ban in the ruled
  `_is_placeholder_only` form (≥1 format field AND nothing but whitespace outside), using
  `string.Formatter`'s own parser. Non-vacuity guard, 5 caught shapes, 6 admitted controls, and
  a receipt proving the NAIVE alternative is broken in **both** directions
  (`_has_literal_text("{msg}") is True`, `_has_literal_text(" ") is False`). Threat model stated
  in the docstring. **Green today, RED the day someone classifies one.**
- **AC-03 / #182.4** — `TestThePromiseScanReachesThe03bRenderHelpers`: the additive subset pin,
  plus a MECHANISM pin proving the committed reach pin is a FLOOR (`expected - observed`) that
  structurally cannot demand a name it does not carry — so a future reader does not delete the
  addition as a duplicate.

### 1.3 `loremaster/tests/test_message_ledger.py` — authorized legs only

Every addition cites its ruling inline. **Not re-authored (AC-25, confirmed by survey):** R2's
two self-addressed pins already exist at this baseline.

| class | ruling | note |
|---|---|---|
| *(FK-4)* `_ask` / `_answer` | B10 / AC-04, FK-4 | `cast(int, result.message.seq)` ×2. `cast` was already imported. **Discharges the file's 2 mypy errors → 0.** |
| `TestADuplicateSeqInOneBatchReportsPerOCCURRENCE` | B10 row 5 / R1 | The only committed duplicate test reaches this shape through a **hostile edge-deletion fixture** and skips on `[fake]`. The ordinary path — an agent re-pasting an ACK REQUIRED trailer — was unpinned on both legs. Adjacent + **non-adjacent** `[s1,s2,s1]`. |
| `TestTheDerivationReadsQuestionsFIRSTAndShortCircuits` | B10 row 5 / R4 | Reuses `_WriteWatch` (ONE IMPLEMENTATION, not a cloned recorder) ⇒ `[real]`-only, like its two committed consumers. Non-vacuity guards on both. **Mutation-proven, §3.** |
| `TestOneAnswerDischargesITSWHOLETHREAD` | B10 row 8 / R5 | Every committed multi-question fixture uses **two different threads**, so thread-discharge and question-discharge were indistinguishable. Includes the ask→answer→ask control (discharge is not retroactive). |
| `TestAnAckedButUNDRAINEDMessageIsServedONCEMore` | B10 row 8 / R6 | The ledger layer beneath B4.2's marker and B4.4's `acked_at` keying. Serve + stamp carried + counted; **converges** (not an infinite re-serve); and a peek does not consume the one re-serve. |

---

## 2. RED/GREEN receipts

Set-diffed failing-test names before vs after, per file. **`comm -23 before after` is EMPTY for
both RED files** — no previously-green test was broken.

```
test_comms_tool.py                149 failed, 554 passed  ->  276 failed, 554 passed
test_comms_promise_registry.py     11 failed,  85 passed  ->   15 failed,  99 passed
test_message_ledger.py            180 passed, 12 skipped  ->  196 passed, 14 skipped
```

Passed counts are **identical** in the two RED files (554 → 554, and 85 → 99 where all 14 new
passes are the AC-02/AC-03 invariants). The +2 ledger skips are the two R4 `[fake]` legs.

**RED-for-the-right-reason**, sampled across the new groups:

```
E  AttributeError: type object 'AppContext' has no attribute '_render_comms_send'
E  AttributeError: type object 'AppContext' has no attribute '_render_comms_drain'
E  AttributeError: type object 'AppContext' has no attribute '_render_comms_ack'
E  AssertionError: the promise scan observed NO render template literal from these 03b
   helpers: ['_render_comms_ack', '_render_comms_drain', '_render_comms_send']
```
plus `TypeError: comms() got an unexpected keyword argument 'to'/'grade'/'peek'/'seqs'`
at the dispatcher pins. **No import error, no fixture error, no collection error** — the file
still collects cleanly (830 tests). Every new production symbol is reached through a call-time
accessor (`_server()`, `_config_module()`, `_msg()`) precisely so one missing name cannot turn
the contract into 700 collection errors.

**One vacuous pass found and fixed by me:** `test_nothing_is_delivered_when_ONE_of_several_
recipients_is_retired` initially passed, because `pytest.raises(Exception)` caught the
`TypeError` about the unaccepted `to=` kwarg. It now asserts the raise NAMES `retired-e`.
(The committed contract uses the same broad idiom in two places; left untouched.)

**Neighbouring suites, after all edits:** `test_render_seam_pins.py`, `test_mcp_server.py`,
`test_comms_render_architecture.py`, `test_comms_schema.py`, `test_agent_registry.py`,
`test_brief_ledger.py` → **1184 passed**, 0 failed.

**Gates:** `uv run ruff check .` → *All checks passed!* (repo-wide).
`./scripts/typecheck.sh` → 94 errors in **2 files**, both RED contract files
(`test_comms_tool.py` 122 lines of the tally, `test_comms_promise_registry.py` 6), every one a
forward reference to the unbuilt surface. `test_message_ledger.py` went **2 → 0**. Baseline was
36; the packet defers global mypy-zero to the END of 03b, and 92 of the 94 clear when the
builder lands the symbols.

---

## 3. Mutation proof I ran (the only one in my remit)

The ledger legs are **GREEN by design** — B10 rows 5/8 say the PINS are owed, not the code. A
green pin is worthless unless it discriminates, so the least-obvious one was mutation-proven
against the REAL tree with a `cp -a` content backup (repo law: an MD5 list is a detector, not a
backup — I kept both).

```
cp -a loremaster/loremaster/messages.py /tmp/messages.py.backup ; md5sum > /tmp/messages.md5
# remove `if not question_rows: return None` from MessageLedger.awaiting_answer
FAILED …TestTheDerivationReadsQuestionsFIRSTAndShortCircuits::
       test_zero_questions_never_issues_the_deliveries_query[real]
1 failed, 1 passed, 2 skipped
# restore
loremaster/loremaster/messages.py: OK          <- md5sum -c, byte-exact
2 passed, 2 skipped
```

No scratch copy was used, so the #140 provenance hazard does not apply: the mutation was made
in, and restored to, the real checkout.

---

## 4. AC-14 discharged — the trailer assembly shape, derived once

Probed 2026-07-24 by running the committed canonicaliser's OWN scanners
(`_scan_safe_str_source_unclassifiable`, `_scan_render_literals_source`,
`_scan_safe_str_source`) over three synthetic assembly shapes. Result recorded in the
`TestTheAckRequiredTrailerIsRunnableAndCorrectlyScoped` docstring, so the builder buys the
wall-hit zero times:

| shape | canonicaliser verdict |
|---|---|
| list comprehension inside `render_join` | **not denied** |
| generator expression | **not denied** |
| pre-bound local list | **not denied** |

What the builder WILL trip is CLASSIFICATION, twice, and both are avoidable: the `render_join`
separator is scanned as a template literal, so the csv list must join on `", "` (already
`_PROMISE_FREE`; a bare `","` is unclassified) — which also produces the friendlier
`seqs=[71, 72]`; and the seq sigil must be `"#{}"` (already `_SAFE_STR_PROMISE_FREE`).

---

## 5. FK-6 pre-flight — **FAILED**, recorded not fixed

The brief's pre-flight: *verify the skew literals' registry descriptions/predicates are
action-agnostic before reuse.* They are not.

**Four registry DESCRIPTIONS name `heartbeat` as the emitting action** (all in
`_PROMISE_REGISTRY`, keyed on the four `skew…` literals): *"heartbeat skew surfacing — tail
1/2…"*, *"…tail 1/2, unscoped variant"*, and two *"heartbeat surfacing for ackers + brief_get
name= for unbriefed…"*. Under FK-6 the same literals are emitted by **drain** as well, so each
description's claim about which action emits it becomes incomplete.

**And a second, larger finding the pre-flight did not ask about:** the four skew LITERALS
themselves carry `surfaces at their next heartbeat` / `ackers see it at next heartbeat`. B4.1
ruled deliberately against editing them ("the publish render's promise becomes an UNDER-claim,
which is nearly free, DESIGN-LAW §1.3"). **That ruling predates the trust doctrine.** The C5(c)
honesty probe grades *"what a render TEACHES must match what the tool measurably then does"* —
and an agent reading `surfaces at their next heartbeat` **inside a drain response** is being
told about a different verb than the one it just called. Under-claiming to a human is cheap;
to an LLM consumer learning the protocol from served text it is a teaching mismatch on the
exact axis the battery scores.

**Disposition question for the lead (I did not edit either):** the brief says *"record it in
your report for the sibling's FK-3 batch"* — but FK-3's batch is `test_surreal_schema.py` /
`test_surreal_fakes.py`, and **these live in MY file**. Options: (a) description-only edits here
under the standing authorization (mechanical, changes no assertion); (b) fold into FK-3 as
written; (c) additionally re-open B4.1's literal ruling against C5(c). My recommendation: (a)
for the four descriptions, and (c) escalated to the operator as a trust-doctrine question,
priced at one authorized amendment to a registered literal + its proofs.

---

## 6. Named mutation-proof obligations for the CONTRACT-ADVERSARY

I wrote no reference build; each obligation states the break and the pin that must redden.

| id | break the production code like this | must go RED |
|---|---|---|
| **MP-FK1a** | render the body INLINE in the row template again | `test_no_dead_registry_entries` **and** `TestDrainBodiesAreFENCED` |
| **MP-FK1b** | `sanitise_line` the body instead of `render_fenced` | `TestDrainBodiesAreFENCED::test_the_body_round_trips_BYTE_VERBATIM` + the fence-width leg |
| **MP-FK2** | fleet's remainder → `total`, or its `next_limit` → `shown+more` | the fleet elision `PromiseProof` EMIT leg |
| **MP-B12** (×3) | delete the `_render_comms_send` / `_drain` / `_ack` call from its handler, return a constant | exactly that verb's pin in `TestTheDispatcherActuallySERVESEachVerbsRender` — **and nothing else in the file** |
| **MP-B33** | make the question teach unconditional; **or** gate it on `grade == 'directive'` | the question-teach proof's NO-EMIT leg (its no-emit fixture IS a directive, so grade-gating cannot pass) |
| **MP-B42** | key the acked re-serve marker on `seen_at`/`stamped_seqs` instead of `acked_at` | that proof's NO-EMIT leg |
| **MP-B53** | drop the `acked_count > 0` conjunct from `note recorded` | that proof's NO-EMIT leg |
| **MP-B14** | compare the row's thread against a hardcoded `"wave7"`; **or** ignore `session` | `test_the_comparand_is_the_ARGUMENT_not_a_hardcoded_literal` |
| **MP-B15** | drain's `next_limit` → `shown + more` | both `TestTheDrainElisionArithmeticIsTheREMAINDER` arithmetic pins |

Already proven by me (§3): the R4 short-circuit.

**Fixture discrimination — "what WRONG build still passes?", answered per group.** The
non-obvious ones: B4.4's two fixtures hold rows differing in *exactly one* axis each
(`acked_at` with grade held constant; grade with `acked_at` held constant), so neither conjunct
can be satisfied by the other's fixture. B14's pair lives in **one render** — two separate
renders cannot distinguish "suppresses the default" from "renders what it was given". B15 uses
**two** arithmetic fixtures with pairwise-distinct values. B5's note pin's NO-EMIT leg
**carries a note**, so `note is not None` alone does not pass it. B6's clamp fixture is cap+5,
so "clamped" and "served everything" differ. The AC-15 pins both carry a `brief_ledger`
positive control. `_assert_ordered` exists because a bare substring pin admits an INVERTED
rewrite ("a peek DOES mark them seen" contains every word a naive pin looks for).

---

## 7. Finding #182 — my four items

| # | item | disposition |
|---|---|---|
| 2 | ACK REQUIRED `acked_at` monoculture | **discharged** — `test_an_ACKED_directive_never_re_nags` (both rows directives, only the stamp differs) + fresh drivers with **no** `acked_at` default |
| 3 | `"{msg}"` under-enforcing pin | **discharged** — the ∀-ban in `_is_placeholder_only` form, with the `" "` positive control and the both-directions receipt against the naive alternative. The committed bound pin is untouched. |
| 4 | reach-set gap | **discharged** — additive subset pin + the mechanism pin proving the committed one is a floor |
| 5 | `send.thread` injection case + 2 ledger mypy | **discharged** — `RenderCase("send.thread")` (plus `send.broadcast_session`) and the two FK-4 casts (`test_message_ledger.py` mypy 2 → 0) |

#182.1 (the weak fleet marker) is the operator's FK-2 and is landed above.

---

## 8. Escalations

### E-S1 — **BLOCKER.** FK-1 makes a COMMITTED battery case unsatisfiable. Not fixed by me.

`C1_RENDER_CASES` contains `RenderCase("drain.body", _render_drain_body)`. Its oracle,
`assert_render_injection_safe`, asserts (1) `hostile_out.count("\n") == baseline.count("\n")`,
(2) no surviving `Cc/Cf/Zl/Zp` char anywhere, (3) the forged row never appears as its own line.
**A fenced body violates all three by construction** — `render_fenced` is verbatim and
newline-preserving. There is no build satisfying both FK-1 and this case; B4 explicitly
forecloses the escape hatch ("Ruled UNIFORM: no inline-if-single-line variant"), and even a
conditional-fencing build would fence the hostile value (it contains `\n`).

The committed contract already documents the resolution mechanism for exactly this collision —
`_FENCE_CASE_LABELS` + `TestFencedBodyIntegrity`, whose own comment says the two are *"mutually
exclusive requirements, not a gap in this test file."*

**The exact edit I would make** (three lines, plus one prose retirement):
1. delete `RenderCase("drain.body", _render_drain_body),` from `C1_RENDER_CASES`;
2. add `"drain.body"` to `_FENCE_CASE_LABELS`;
3. the replacement coverage **is already written and additive** —
   `TestDrainBodiesAreFENCED` — so no second wave is needed;
4. **AC-19 prose corpse:** the committed comment above the packet-03 fixtures says *"A drain
   row is a SINGLE line … so the body is sanitised into it rather than fenced — which is
   exactly why the injection battery, not the fence-integrity class, is its oracle."* That is
   FALSE the moment FK-1 lands and must be retired in the same edit.

**Why I did not make it:** removing a case from the battery **changes which assertions run**, so
it falls outside the STANDING AUTHORIZATION's clause (b) ("MECHANICAL — preserves every existing
rendered value and changes NO assertion"), and FK-1's authorization enumerates only *"the two
row-template registry amendments"*. `drain`'s per-ACTION battery coverage survives the removal
(`drain.sender`, `drain.thread` remain), so `assert_actions_covered` and
`test_every_action_has_at_least_one_registered_case` stay green.

⚠ Until this is ruled, the contract is **21 parametrized cases RED on a correct build** — the
C-DEF class the repo names ("trapping the builder between ruff and a test it may not edit"). It
should be settled before any builder is briefed.

### E-S2 — `_render_comms_drain` gains a REQUIRED `session` kwarg (deviation, made)

B14/AC-22 rules `session` REQUIRED (it is the `{context}` cell's comparand; a defaulted
comparand lets any call site silently kill the branch — the fixture-default law at the signature
layer). **Re-derived call-site count at `e7db965`: 4** — `_render_drain_body`,
`_render_drain_sender`, `_render_drain_thread` (test_comms_tool.py) and `_render_drain`
(test_comms_promise_registry.py). *(The struck record's "five committed drivers" is not
reproducible; I did not read it — the lead quoted the count in the packet file's HISTORY
section. Re-derive before trusting either number.)*

All four now pass `session="wave7"`. Because `_inbox_entry`/`_p03_entry` hardcode
`thread="wave7"`, every committed case renders the same shape it would have pre-B14 (the thread
half of the cell is suppressed when `thread == session`), and `drain.thread` stays a valid
injection case — its hostile values are never `"wave7"`, so the cell renders and its
sanitisation is still exercised. **Reading: this is a mechanical consequence of a design ruling
under the STANDING AUTHORIZATION.** The alternative reading — that it needs its own operator
ruling because the authorization speaks of "the sidecar" — is the lead's to settle. Without it
the contract is unsatisfiable, which is why I made the edit rather than deferring it.

### E-S3 — `_render_comms_ack` gains a REQUIRED `note` kwarg (deviation, made)

B5.3's `note recorded` line emits IFF the call carried a note AND `acked_count > 0`.
`MessageAckResult` carries no note (verified), so the value must reach the render. 2 committed
call sites gained `note=None`. Same authorization question as E-S2. The alternative — rendering
the line from the HANDLER — splits one render across two places and contradicts B5's
`_render_comms_ack(result)` shape.

### E-S4 — the question teach derives from `Message.question`, not a new render parameter

Two readings that produce different code:
- **(A, what I pinned):** B3.3's teach keys on the TYPED `result.message.question`, which
  `messages.py::send` already sets from `set_status == 'input_required'`.
  `_render_comms_send`'s committed signature is **unchanged** (3 call sites untouched).
- **(B):** B3's literal ruled signature `_render_comms_send(…, question, thread_differs)` — a
  new parameter, which must then be either defaulted (violating AC-11's law on branched-on
  params) or required (breaking 2 more committed drivers).

I pinned (A): it is the repo's own derived-prose law ("renders take typed applicability, never
a name they compare"), it needs no further committed edits, and the B3 wording is explicitly
superseded by §A-GRAFT at the wording layer. **Both the dispatcher-level and render-level pins
I wrote hold under (A); under (B) the promise-registry driver `_render_send_03b` needs one
line changed.** Flagged rather than assumed.

### E-S5 — FK-6 pre-flight failed; see §5 for the finding and the three options.

### E-S6 — R3's index-presence pins are outside my writable set

Survey-confirmed: **neither `message` index exists**, and no test pins either. The live
`generate_message_ddl()` emits `DEFINE SEQUENCE … message_seq`,
`DEFINE INDEX … to_in_out UNIQUE`, `DEFINE INDEX … to_out_seen_at` — `MESSAGE_TABLE` has
**zero** indexes. The presence pins belong in **`test_comms_schema.py`** (which owns the
`_index_statements(ddl, table, fields_pattern=…)` idiom), not in any file I own. Index pins are
per-property, not exact-set, so adding two indexes turns nothing RED.

**Exact edit I would make** — two tests in `test_comms_schema.py` mirroring
`test_a_drain_index_on_out_and_seen_at_exists`, with `fields_pattern=r"seq"` and
`r"sender,\s*question"` on `MESSAGE_TABLE`, asserting `IF NOT EXISTS` and that `seq` is
**PLAIN, not UNIQUE** (a strikeable divergence with a named re-open trigger, per the packet).

⚠ **Hazard surfaced (not mine to rule):** the inherited ruling names the new index `message_seq`
— the *identical string* to `MESSAGE_SEQUENCE_NAME = "message_seq"`, the `DEFINE SEQUENCE`.
Different object kinds, so the engine accepts it and the sequence pin still passes (it filters
on `startswith("DEFINE SEQUENCE")`), but two schema objects sharing one name is a debugging
trap. `message_seq_idx` avoids it. **And the free window closes at this packet's deploy** —
production holds zero `message` rows exactly once.

### E-S7 — `_message_fakes.py` (B10 row 4) is outside my writable set

B10 row 4 assigns "fake oracle gains R2's conjunct" to the 03b contract author. **I read it: the
conjunct is already there** — `FakeMessageLedger.awaiting_answer`'s docstring states all four
conjuncts including "sent by ANOTHER AGENT (ruling R2)", and the R2 pins pass on the `[fake]`
leg (my R5/R6 additions pass on both legs). Row 4 appears already discharged; confirming it is
one grep the lead can run. I made no edit.

### E-S8 — B14's "precedence task-then-thread" — resolved by derivation, lead may overrule

The phrase admits two readings that produce different code: (a) the task **replaces** the thread
label in the single cell; (b) both render, task first. I did **not** choose silently — I
derived it from the committed, immutable `_SAFE_STR_PROMISE_FREE`, which carries exactly two
literals for one `{context}` slot: `" (thread {})"` described as *"the thread variant"* and
`" (task {})"` described as *"the task-anchored variant"*. Two mutually-described **variants**
of one cell is a choice, not a concatenation; a both-render build would need a third literal
the committed set does not contain, and `test_every_comms_render_literal_is_classified` would
go RED on it. I pinned (a), with that derivation in the test's docstring.

*(This same discovery is why the `{context}` cell renders parenthesised — ` (thread q:gate)` —
rather than the ` · thread x` shape the superseded B4.2 wording used. Worth knowing before
reading any render pin here.)*

---

## 9. Residuals noticed (not mine to fix; surfaced per standing law)

1. **`test_drain_defaults_to_the_configured_limit_not_a_hardcoded_one` reads
   `rendered.count("#") >= 5`.** Under FK-1's fenced bodies a body containing `#` inflates that
   count. Its bodies are `message {i}` (no `#`) and its grade is `signal` (no trailer), so it
   stays green — recorded so nobody "fixes" it into weakness and nobody feeds it hash-bearing
   bodies without re-reading it. (r2 §F.5 predicted this; it holds under the FENCE arm.)
2. **`pytest.raises(Exception)` appears twice in the committed contract**
   (`test_nothing_is_delivered_when_one_recipient_is_unknown`,
   `test_an_oversize_body_is_a_teaching_reject_at_the_surface`). Both can pass for an unrelated
   reason while `to=`/`body=` are unaccepted kwargs. The second is saved by its `"refs" in
   str(...)` assertion; the first is saved by its store assertions. Left untouched (committed),
   but the class is real — I hit it in my own first draft (§2).
3. **`test_the_derivation_writes_NOTHING` and my two R4 pins are `[real]`-only** because
   `_WriteWatch` shadows a real connection seam. The `[fake]` legs of the R4 ordering property
   are therefore unguarded. Closing that needs a statement seam on `FakeMessageLedger` — a fake
   oracle change, i.e. contract-author + adversary work, not a builder drive-by. Ledger row
   candidate.
4. **`_INSTRUCTIONS` currently names six comms actions**; B9 adds three. `test_mcp_server.py::
   TestServerInstructions`'s committed substring pins are additive-compatible (verified: 1184
   passed after my edits), so no amendment there is needed — but its pins will not DEMAND the
   new clauses. That is why B9's clause pins live in `test_comms_tool.py` (my writable set) as
   a new class rather than as edits to `test_mcp_server.py`.
5. **The committed `_p03_entry` / `_inbox_entry` factories still default `acked_at` and
   hardcode `thread`.** I did not change them (committed; and AC-11 binds *fresh* drivers). Every
   03b pin uses the fresh no-default factories instead. If the lead wants the cause removed as
   well as the symptom, that is a separate authorized amendment.

---

## 10. Tool honesty

lore's indexed tools were used for task-ledger coordination (`lore_claim_task`, `lore_tasks`).
**Code-structure work was done by direct Read/Grep, and I say so as required:** every question I
had was of the three kinds the dogfood protocol keeps with grep — exhaustive call-site
enumeration where one missed site breaks a signature (the `_render_comms_*` driver sweep, §E-S2,
where a miss compiles-but-fails), non-symbol textual seams (registry template LITERALS, registry
DESCRIPTIONS, `_INSTRUCTIONS` prose, `_SAFE_STR_PROMISE_FREE` keys — none of which are symbols),
and a cross-cutting map (which committed pins exist for R1–R6, delegated to a survey subagent).
No lore weakness was routed around, so no friction row is owed.

---

# APPENDIX A — E-S5(c) (wording amendment): PROCESSED, **DECLINED IN PART**, escalated

*Appended 2026-07-24 by contract-surface-03b-r2, after the lead's re-ping reported this
item unactioned. It was NOT unactioned: it was investigated, measured, and declined, and the
chat reply carrying that verdict was lost. The report is the record — this appendix is that
verdict, in its durable place. Standing lesson, mine: a verdict that lives only in a
SendMessage is a verdict that did not happen (brief-base §1, §5).*

## A.1 The ruling, verified — not taken on relay

`git log` → `aa25e79 docs(03b): design rulings — E-S5(c) AMEND under the trust doctrine;
E-S4/E-S8 confirmed`, and `03b-design-rulings-r2.md` §G row E-S5(c) carries the mechanical
replacement spec verbatim as relayed. **The ruling is real and I do not contest it.** B4.1's
"under-claim is nearly free" genuinely predates the trust doctrine, and a skew line naming
`heartbeat` inside a DRAIN response genuinely teaches the wrong verb to the exact reader C5(c)
protects. If it were mine to land, I would land it.

## A.2 Why it was not applied: 3 of the 5 files are outside my writable set, one is production

The ruling's spec is priced at "4 literals + 4 descriptions". A **bare, anchor-free sweep**
(`grep -rn "next heartbeat"` — no prefix anchor, no call-paren anchor, per the rename-sweep law)
finds the wording at **47 sites across 5 files**:

| file | sites | writable by me? |
|---|---|---|
| `loremaster/loremaster/server.py` | **4** — the SHIPPED literals, the source of truth | **NO — production** |
| `loremaster/tests/test_comms_promise_registry.py` | 13 (4 registry keys · 4 proof `literal=` · 4 `marker=` · 1 comment of mine) | yes |
| `loremaster/tests/test_comms_tool.py` | 19 (~17 exact-string assertions on COMMITTED render pins · 1 regex · 1 docstring) | yes, but those pins are committed and the relay does not name them |
| `loremaster/tests/test_comms_render_architecture.py` | **10** (`_TAIL_SURFACES` / `_TAIL_ACKERS` constants + 5 assertions) | **NO** |
| `loremaster/tests/test_comms_wiring.py` | **1** | **NO** |

## A.3 Measured, not asserted — and there is NO coherent partial application

**Direction 1 — amend production only** (temporary mutation, `cp -a` content backup, restored
byte-exact; `md5sum -c` → `loremaster/loremaster/server.py: OK`):

```
test_comms_render_architecture.py + test_comms_wiring.py   5 failed, 49 passed
test_comms_tool.py            255 failed, 554 passed  ->  258 failed, 551 passed
```
→ **5 tests RED in two files I may not touch**, plus 3 committed pins in a file I may only
add to.

**Direction 2 — amend my registry keys only.** Decisive receipt, measured at this tree:

```
PASSED  TestEveryCommsRenderLiteralIsClassified::test_every_comms_render_literal_is_classified
FAILED  TestEveryCommsRenderLiteralIsClassified::test_no_dead_registry_entries   (already RED at baseline)
```
`test_every_comms_render_literal_is_classified` is **GREEN today**. Changing the four registry
keys while `server.py` still emits the old strings turns it **RED** — production would be
emitting four UNCLASSIFIED literals — and adds four more dead entries behind an already-red
`test_no_dead_registry_entries`, where the new breakage is invisible. That is a regression I
would be introducing, and it destroys the one property this whole wave has been holding:
**zero previously-green tests broken.**

Both directions leave the tree incoherent. Applying the relay as scoped would have produced a
tree whose gates report the damage as "expected RED".

## A.4 The mis-pricing is MINE, and it is the law-in-the-law shape again

§5 of this report priced E-S5(c) at *"one authorized amendment to a registered literal + its
proofs."* That figure came from counting the sites **in my own files** and reporting it as the
cost of the change — two populations conflated into one count. The ruling then inherited my
number. **Re-derive from the sweep in A.2, never from §5.** This is the `_query`
ten-vs-eleven shape from CLAUDE.md §102, committed inside the wave whose report quotes that
law — the third recorded instance, and the second by an agent who had just written the rule
down.

## A.5 Recommendation (the lead/operator rules; I changed nothing)

A **one-concern commit of its own**, spanning production + 4 test suites, landing BEFORE the
adversary phase so the adversary grades the final wording. Two shapes:

1. **Expand this agent's writable set** to `test_comms_render_architecture.py`,
   `test_comms_wiring.py` and `server.py`'s 4 literals — cheapest, the site map is loaded and
   the mutation/restore discipline is already exercised twice this session. Requires one
   ruling: that amending 4 SHIPPED served strings is not barred by my "tests only" law. I read
   that law as scoped to the *unbuilt* surface, but the reading is not mine to settle.
2. **A dedicated agent** briefed with A.2's site map.

**And do not duplicate the wording a 48th time.** 47 hardcoded copies of one served sentence is
the "pattern to clone" defect (CLAUDE.md §ONE IMPLEMENTATION). `test_comms_render_architecture.py`
already has the right shape — the `_TAIL_SURFACES` / `_TAIL_ACKERS` constants — and extending
that seam discharges the ruling's own re-open trigger STRUCTURALLY: at a third surfacing verb
you change one constant, not fifty strings.

## A.6 Answers to the three questions asked

- **(a) fresh tails** — unchanged from the E-S1/E-S5(a) wave, because no E-S5(c) edit was made:
  `test_comms_tool.py` **255F/554P** (809 collected) · `test_comms_promise_registry.py`
  **15F/99P** (114) · `test_message_ledger.py` **196P/14s** (210) · `uv run ruff check .` →
  *All checks passed!* · `./scripts/typecheck.sh` → *Found 92 errors in 2 files*.
- **(b) description-wording option** — **neither**. Reconciling descriptions to wording the
  literals do not yet carry would assert a string production never emits. My E-S5(a)
  descriptions already name BOTH verbs (*"emitted by EVERY action that serves the shared skew
  block (heartbeat and, per FK-6, drain)"*), which satisfies the ruled property ("names every
  verb that measurably surfaces it") — so under option 1 of the spec they need no further
  edit, and I have left them exactly as authorized under E-S5(a).
- **(c) proofs moved in step** — **no**, and they could not have: the proofs' markers are
  instantiations of the literals, and the literals cannot move without the four out-of-scope
  files moving with them.

**Item 3 of the relay (the line-142 comment → re-open trigger) is deliberately NOT applied
either**: that comment currently records the TRUE state of the tree (the literals are
untouched). Replacing it with a re-open trigger for an amendment that has not landed would
leave the file asserting in prose that work was done which was not — the precise defect class
this packet exists to kill. It lands with the amendment, in the same commit, not before it.

---

# FIX WAVE — response to the adversary re-grade (`bb8d106`)

*Appended 2026-07-24 by contract-surface-03b-r2. The re-grade is rigorous and fair; where it
and I disagreed I checked, and it was right every time. Its four-way adjudication cleared 50
of 53 red-on-reference pins as its own reference's legitimate variance — that discipline is
what makes the remaining 3 trustworthy.*

## F.1 Fresh tails

```
test_comms_tool.py                 255F/554P  ->  275 failed, 556 passed   (831 collected)
test_comms_promise_registry.py      15F/ 99P  ->   15 failed, 101 passed   (116 collected)
test_message_ledger.py             196P/14s   ->  196 passed, 14 skipped   (210 collected)

uv run ruff check .        All checks passed!
./scripts/typecheck.sh     Found 108 errors in 2 files  (was 92; the delta is new forward
                           references from this wave's pins — still only the two RED files)
neighbours                 943 passed, 3 failed
```
The 3 neighbour failures are `test_comms_schema.py`'s message-index pins, committed by the
telemetry sibling at `bb64324` — that is **my escalation E-S6 being picked up**, RED pending
builder work. Not caused by this wave (`git diff` on that file is empty for me).

**Passed counts went UP in both RED files (554→556, 99→101) and the ledger held at 196** — so
no previously-green test broke. The 4 new passes are invariants by design, each with a stated
control: the D5 clone pin + its positive control, the inversion denylist, and the ack-outcome
fixture's discrimination guard.

## F.2 The three PIN DEFECTS — the contract was UNSATISFIABLE

**§3.B3 — the inverted header-count gate.** `test_the_header_count_is_UNAFFECTED_by_a_hostile_body`
scanned the WHOLE render while its own message promised *"outside its fence"*, and its fixture
body deliberately carries a row-shaped line the sibling pin REQUIRES to survive verbatim. It
**reddened the FK-1 build the operator ruled and greened the two builds FK-1 forbids.** Fixed
by computing `outside` exactly as the sibling does — extracted to a shared
`_outside_the_fence` helper so the two cannot drift apart again (the private copy is what let
them diverge).

Neither this fix nor the next can be verified against this tree — the renders do not exist,
which is the point of a RED contract — so I proved it at the level of my own helper, **both
directions**, on a synthetic render of the exact shape a correct FK-1 build emits:

```
OLD (whole render): 2 rows -> assert ==1  FAILS   <- the inverted gate, reproduced
NEW (outside only): 1 rows -> assert ==1  PASSES  <- the correct build now passes
NEW on the INLINE build (what FK-1 forbids): FAILS at the fence-boundary guard -> REJECTED
```
So the sign flip is corrected **and** the pin still rejects the forbidden build.

**§3.B4 — the question-teach proof reddened a committed marker.** `_render_send_03b` minted
`seq=41`, which is `_p03_message`'s default, so a correct build necessarily co-emitted the
committed marker `"recipients must ack: … seqs=[41]"`. Moved to `seq=42`. The
`grade="directive"` choice on both legs is load-bearing (it is what kills a grade-gating
build, MP-B33) and is kept. Verified no new collision: seq 42 appears in exactly one driver
and in no marker.

Chosen over declaring a `_MARKER_CO_EMISSION_EXEMPTIONS` pair deliberately — an exemption
permanently blinds the meta-test to that pair, while a distinct fixture value costs nothing.
**Exemptions are for STRUCTURAL co-emission; this was a fixture collision.**

## F.3 The six BLOCKERS

| § | fix |
|---|---|
| **3.B1** FK-6 pinned by nothing | `TestDrainServesTheSharedBriefSkewBlock` — five pins through the REAL dispatcher: drain serves the catch-up line for an agent behind head · heartbeat and drain serve the **identical** line for the same state (the sharing half) · a current agent gets none (emit/no-emit) · **P11**: brief ledger down ⇒ drain FAILS LOUD (§B4.1's ruled posture; a silent messages-without-skew fallback is the degradation DESIGN-LAW §1.4 refuses) · positive control that the same drain succeeds live |
| **3.B2** D5 routing-is-not-sharing | `TestEveryPromiseLiteralHasExactlyONEEmittingFunction` — **a served promise literal is emitted from exactly ONE function.** A private clone must duplicate the `render_line` call to exist, so it lands here whatever it is named. **Name-free on purpose**: naming a helper is the enumerate-the-forbidden mistake (the six-defeats table); this keys on the property. Measured before writing it: **zero** registry literals have >1 emitter today, so it is green now and RED on the first clone. Scoped to `_PROMISE_REGISTRY` because the join separators legitimately ARE multi-emitted — duplicating trivia is cheap, duplicating POLICY is what this forbids. Carries a positive control proving the scan CAN see a two-function literal |
| **3.B3 / 3.B4** | §F.2 |
| **3.B5** invertible teaching | **The INSTRUMENT was replaced, not the pins patched.** `_assert_ordered` claimed to be "the cheapest non-invertible strengthening"; measured false — an entirely inverted instructions block passed 9/9 and two inverted schema descriptions passed 11/11. Now: `_assert_teaches` (PRIMARY — the ruled sentence verbatim, non-invertible by construction) · `_assert_never_claims` (SECONDARY — the 12 phrases the adversary actually served; explicitly *not* the definition of correctness, since enumerating the forbidden is the losing shape) · `_assert_ordered` KEPT with an honest docstring and word-boundary matching, for shape only. The ruled sentences live in `_RULED_INSTRUCTION_CLAUSES` / `_RULED_BODY_CAP_SENTENCE` — stated once so every pin derives from one source. **AC-08's integer extraction is kept AND repaired**: it survived *"the 2000 char figure is advisory"*, so the cap sentence is now pinned whole with the constant interpolated |
| **3.B6** ack mapping | `TestEachRequestedSeqLandsInTheLineItsOwnOutcomeNames` — four DISTINCT seqs, one render, **group-exact** membership per outcome (`_seqs_named_in(<that group's line>) == [that seq]`). Plus **P6**: `acked_count` / `len(entries)` / `already_acked_count` pairwise distinct (2/5/1) |

## F.4 CRITICAL + MAJOR missing pins

**P7** `TestAnExplicitRecipientResolvesInTheCALLERSSessionOnly` — the adversary's own
discriminating fixture (same name in two sessions, the caller's copy RETIRED so a bare-name
lookup resolves to the *other* session and silently succeeds), plus the positive control that
the name IS reachable in its own session. WB8 delivered across sessions and reported success.
**P8/P9** `TestTheSendReceiptCapsAndCountsHonestly` — N derived from `_COVERAGE_NAMES_CAP`
(never the literal 5): over-cap shows exactly the cap + the counted remainder; under-cap names
everyone and shows no remainder (emit/no-emit for the committed capped variant); broadcast
counts the WHOLE delivered set. **P10** `TestTheDrainRefsCellIsCappedAndCounted` — refs are
uncapped at the ledger, so an uncapped render is an unbounded dump in the highest-volume
surface. **P12** the drain elision proof's marker promoted from the value-free
`"more unread — re-run with limit="` to the full line `"+5 more unread — re-run with limit=5"`;
checked it is not a substring of the FK-2 fleet marker, and vice versa. **P13**
`TestARejectedRecipientCharsetNamesWHICHRecipient` — five recipients, one bad; the innocent
four must NOT be echoed (actionable denial). **P15** `TestTheQuestionTeachReachesTheReader
ThroughTheDispatcher` — closes the fake-honesty loop end-to-end, so the surface contract
observes the `question` field it teaches from.

## F.5 A defect of MINE the adversary did not catch

Writing the FK-6 pin, I scanned which functions actually emit the four `skew (session …)`
literals. **They are emitted by `_render_comms_brief_publish`, not by heartbeat.** My E-S5(a)
description edits had rewritten all four to say *"emitted by EVERY action that serves the
shared skew block (heartbeat and, per FK-6, drain)"* — **wrong**: those lines are
brief_publish's publisher-side SUMMARY, and what "heartbeat or drain" names is where the
promise is REDEEMED, not who emits it. I had corrected an emitter claim into a different
wrong emitter claim. All four now distinguish the two: *"EMITTED BY brief_publish … what it
PROMISES is that the behind agents will see the catch-up at their next heartbeat or drain."*

This is the same shape as A.4 and as the §102 law: a claim about a population, written without
deriving the population. The derivation took one scan I could have run before writing the
first version.

## F.6 Claim corrections (§6)

- **MP-FK2 arm 2 was VACUOUS** — for fleet, `shown + more ≡ total` by construction, so
  "`next_limit → shown+more`" cannot redden anything. A receipt taken on arm 2 alone would
  have been a false proof. **MP-FK2 now has ONE arm** (remainder → `total`, confirmed 6 RED);
  the drain-side arithmetic is carried by MP-B15 and the new MP-P12.
- **MP-B12's "and nothing else in the file" was an OVER-CLAIM.** Measured: send → 2 RED
  (1 in-file), drain → 7 RED (6 in-file), ack → 3 RED (2 in-file). The mechanism is confirmed;
  the exclusivity clause is withdrawn. It should have read *"that verb's pin is among the
  reddened, and it is the only pin that names that verb's render"*.

## F.7 Updated mutation-proof obligations for the re-grade

| id | break | must go RED |
|---|---|---|
| MP-FK1a/b | inline body · `sanitise_line` the body | as before — **and** the header-count pin must now STAY red (it previously flipped green; that flip was the §3.B3 defect) |
| MP-FK2 | fleet remainder → `total` | the fleet elision proof (arm 2 withdrawn as vacuous) |
| MP-P12 | drain `next_limit` → `shown+more` | the drain elision proof's EMIT leg **and** both B15 arithmetic pins |
| MP-B12 ×3 | delete each render call | that verb's render pin (exclusivity clause withdrawn) |
| MP-B33 · MP-B42 · MP-B53 · MP-B14 · MP-B15 | as before | as before — all CONFIRMED at 8/9 |
| **MP-FK6** | `_comms_drain` never assembles/passes the skew block (WB1) | `TestDrainServesTheSharedBriefSkewBlock` (≥3 legs) |
| **MP-D5** | drain hand-rolls a private skew clone (WB18) | `TestEveryPromiseLiteralHasExactlyONEEmittingFunction`, naming both functions — **and** the identical-line pin |
| **MP-B5c** | brief ledger raises during a drain | the fail-loud pin; a build that swallows it and serves messages-without-skew must go RED |
| **MP-B6c** | swap the acked / already-acked groups (WB33) | all four group-exact pins |
| **MP-B5d** | serve any inverted teaching sentence (WB30/WB31b) | the sentence pins first, the denylist second |

## F.8 §8 residuals + §9 corpse — individual verdicts

1. **`_p03_entry` defaults `acked_at`** — agreed with the adversary: acceptable, hazard closed
   by the fresh no-default factories. **No action**, recorded so nobody "fixes" it by weakening.
2. **Value-free elision marker** — **FIXED** (P12, above).
3. **WB16 (ack render dedupes + re-sorts) survives** — **ESCALATED, not fixed.** B5.2 ruled
   request order; §A-GRAFT re-expressed R1 as MEMBERSHIP and retired the ordering clause. Two
   readings, different code. The adversary would pick (A) membership-only; so would I, and it
   is what the contract implements. **This is a ruling, not mine to make** — pinning ordering
   would contradict A-GRAFT, and pinning membership-only forecloses B5.2's letter.
4. **B3.2 send thread cell** — **UNTOUCHED** per the lead's instruction; with the design owner.
5. **`AppContext.comms` fails `ruff PLR0912` under the ruled validation order** —
   **ESCALATED, not pinned.** The adversary is right that this is a real, unanticipated builder
   cost. But "invent the extraction seam" is a **property to INVENT, not a spec to implement**
   — CLAUDE.md routes that to the operator or an Opus author who attacks its own design, never
   to a builder, and equally never to a contract author inventing it in a pin. Pinning a shape
   I designed would be exactly the failure the roster law names. **Recommend**: the design
   owner names the seam (or grants the `noqa` with a reason), then it becomes one cheap AST pin.
6. **Drain reads the brief ledger ⇒ drain fails when briefs fail** — **FIXED** (P11).
7. **`MessageLedger` is never closed** — **FLAGGED, outside my writable set.** The `aclose`
   pins live in `test_comms_wiring.py` (`TestAcloseClosesBothNewConnections` area). Exact edit:
   one pin mirroring `test_aclose_closes_the_agent_registry_connection` for
   `message_ledger`. Real resource-leak hole; one line for whoever owns that file.
8. **The cross-test `_SKEW_SURFACING_TEACH` import** — correct and load-bearing. **No action**;
   the adversary's note is right that a future reader may misread it as a smell.
9. **The struck adversary's `test_surreal_harness.py` escalation** — outside my writable set
   and outside my graded five. **FLAGGED for the lead** to confirm it was fixed, not assumed.

**§9 corpse — `docs/design/2026-07-12-pkt28-c1-semantics.md`, 8 live sites.** Real corpse: it
is the doc a future reader consults for §9.4's tail wording and it now contradicts production.
**Outside my writable set** (docs). Exact edit: one supersession line under its §9.4 pointing
at ruling E-S5(c) and `03b-design-rulings-r2.md` §G — not a rewrite of the 8 sites, since the
doc is a historical spec and rewriting it would erase what C1 actually shipped.
`docs/plans/v2/02-comms-render-architecture.md:26` is historical (records #103's finding, does
not prescribe) — a pointer would be cheap; flagged, not blocking.

## F.9 What I could not verify, stated plainly

The §F.2 fixes and every new pin are RED on this tree for the right reason (`AttributeError`
naming a missing render, `TypeError` naming an unaccepted kwarg — sampled and pasted above).
**I cannot show them green, because I may not build the surface.** The B3 fix is proven both
directions synthetically; the B4 fix is proven by collision analysis. Everything else is the
adversary's to certify against its reference — that split is the point.

---

# APPENDIX B — B3.2 ruled (Reading A): contract stands as built

*Appended 2026-07-24 by contract-surface-03b-r2, after the lead relayed the ruling. Verified
in the tree, not taken on relay: `f537051 docs(03b): B3.2 ruled — Reading A, no thread cell on
the send receipt; clause struck in place`, with B3 item 2 struck in place and the §G row
carrying the derivation.*

**Outcome: no pin changes owed.** The contract already implements Reading A — I never authored
a send thread-cell template or a pin demanding one. The question teach derives from the typed
`Message.question` (E-S4), and B3.3's additive teach template is the one place a thread reaches
the send render. The classification pin reddening an additive-template build is now the RULED
behaviour, so the adversary's Reading-B reference dying on it is the instrument working, not a
contract defect.

**One prose corpse retired, found by a bare sweep of my own files** (`grep -n "thread cell|
thread-bearing|B3.2"`, 4 hits, each verdicted individually):

| site | verdict |
|---|---|
| `_render_send_thread` docstring — *"B3.2/B3.3 put `thread` into the send render (the thread cell, and the question teach)"* and *"BOTH thread-bearing lines render"* | **CORPSE — retired.** False the moment B3.2 was struck. Rewritten to name the question teach as the ONLY thread-bearing line, with the retired sentence quoted so the change is met deliberately |
| same docstring, the QUESTION fixture choice | **upgraded from incidental to LOAD-BEARING** — under Reading A a non-question fixture would drive this injection case against a render that never touches `thread`, so the hostile value would exercise nothing. Now stated as the reason |
| `test_comms_tool.py:3770` — *"same-thread rows draw no thread cell"* | **not a corpse** — that is the DRAIN row's `{context}` cell (B14), which Reading A does not touch |
| `TestTheDrainRowContextCell` (whole class) | **unaffected** — B14 governs the drain row; B3.2 governed the send receipt. What survives of B3.2 is the suppression PRINCIPLE, which B14 already applies |

Gates after the edit (docstring-only, no assertion changed): `test_comms_tool.py`
**275 failed, 556 passed**; `test_comms_promise_registry.py` **15 failed, 101 passed**;
`test_message_ledger.py` **196 passed, 14 skipped**; `uv run ruff check .` → *All checks
passed!* — identical to §F.1, as a prose-only edit must be.
