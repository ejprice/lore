# REPORT-contract-pkt03 — the packet 03 message-graph CONTRACT

brief-base v4 read

> ⚠ **READ THE THREE UPDATE SECTIONS AT THE END FIRST — `## UPDATE 5eb445b` → `## UPDATE post-adversary` → `## UPDATE collection-fix`, which supersede every count, sizing and escalation in this block.** Now **400 pins**; adversary verdict INSUFFICIENT is CLOSED (3 BLOCKERs + 1 MAJOR + 5 lesser + 5 residuals), all eight surviving wrong builds mutation-proven RED. **Packet 03 re-sized to 0.55 wu — past the split threshold; a second split is proposed.**
> E1–E5 are RESOLVED by the packet file's rulings 7–9 and Scope IN; E6 (the waiting-state
> MECHANISM) was ruled in my favour by the lead and is now pinned so the mechanism must be READ.
> Everything below is the original contract and remains accurate for what it describes.

- **state**: done-with-deviations
- **deviations**:
  1. I built a REFERENCE IMPLEMENTATION in a scratch copy (`/tmp/pkt03-ref`, via
     `./scripts/scratch_copy.sh`) to grade the contract's satisfiability. It caught **four real
     contract defects** before you ever saw the file (§4). The scratch copy is left in place for
     the adversary; the real production tree is byte-untouched (receipt §3).
  2. Two of the six pin groups (tool DISPATCH, ledger `[real]` leg) are RED-verified but
     **NOT satisfiability-graded** — grading them needs the server/store build itself. Said
     plainly in §4.3; they are the two lowest-machinery groups.
- **decisions-needed** (FIVE escalations — §6; none decided silently):
  E1 a design sentence and the shipped status machine CONTRADICT each other on whether draining
  un-parks a parked agent · E2 `set_status` on `send` is in the design table but not in Scope IN ·
  E3 ruling 7 covers BROADCAST self-delivery, not an EXPLICIT self-addressed send · E4 the
  recipient-existence check has two plausible homes and I pinned BOTH · E5 `AgentRefLike` would be
  copy #2 of a Protocol — a DESIGN decision the DRY law says to escalate, not write.
- **SIZING: 296 new pins. Honest build estimate 0.6–0.8 wu against a 0.25 sizing. I recommend a
  SPLIT (§5).**
- **receipt pointers**: §1 what/where · §2 sizing · §3 untouched-tree + RED · §4 satisfiability +
  the 4 caught defects · §5 the split proposal · §6 escalations · §7 frontier→pin map ·
  §8 known-bound answer · §9 things you did not ask about.

---

## 1. What I contracted, and where each group lives

| group | file | pins |
|---|---|---|
| schema / DDL (`message`, `to`, `DEFINE SEQUENCE`) | `test_comms_schema.py` (appended) | **29** |
| ledger send · drain · ack · concurrency · seam | `test_message_ledger.py` (**new**) | **94** |
| tool dispatch (specs, broadcast, strict-param) | `test_comms_tool.py` (appended) | **21** |
| renders — hostile-injection battery, 6 new labels × 21 threat chars | `test_comms_tool.py` | **147** |
| promise registry + executable proofs | `test_comms_promise_registry.py` | **5** |
| adversarial fake (`FakeMessageLedger`) | `_comms_fakes.py` (appended) | — |
| | | **296** |

The pinned public surface is written as a typed block in `test_message_ledger.py`'s module
docstring — that IS the contract, and I have not re-transcribed it here.

Three choices worth naming, all following existing law rather than inventing:

- **The ledger never imports `loremaster.agents`** (`briefs.py:79-89`). `send` takes an
  externally-resolved sender/recipient; the DISPATCHER resolves the roster — which is why
  rulings 1 and 7 are pinned in `test_comms_tool.py`, not in the ledger file.
- **All renders live in `server.py` under the `_render_comms*` prefix** (ruling 5 / #145).
- **Renders take TYPED applicability they branch on** (#104): `_render_comms_send(..., broadcast:
  bool)`, `_render_comms_drain(..., peeked)` — never a name comparison.

---

## 2. STEP 7 — sizing, measured after the contract was complete

**296 pins. Build estimate: 0.6–0.8 wu.** The packet was sized 0.25 before discovery. Packet 02
was sized 0.20 and measured 3–4×; this is the same shape of miss, caught earlier.

What the number is made of:

1. **`messages.py` is a new ledger module** (`briefs.py`, its closest analogue, is 1292 lines for a
   structurally *simpler* shape — one node + one edge, no fan-out, no display cap, no per-recipient
   state machine). Its `send` composes mint + CREATE + N×`RELATE` in ONE transaction with
   variable-arity params (the `tasks.py:248` format-string param idiom), plus an
   all-recipients-exist precheck; `drain` is a windowed SELECT plus a scoped CAS stamp of exactly
   the served rows; `ack` is a CAS plus a disambiguating follow-up SELECT producing four typed
   outcomes.
2. **Two mechanisms with NO precedent in this tree** (recon §C.6, flag 8): `DEFINE SEQUENCE` /
   `sequence::nextval` and `ulid()` ids. Probe-settled, but nothing to clone.
3. **A new DDL helper.** Ruling 3 mandates `TYPE RELATION IN message OUT agent`; the house
   `_define_relation_table` **cannot emit `IN`/`OUT` at all** (§9 F1). That helper must be
   extended — a shared-seam change, not a local one.
4. **Nine touch points in `server.py`** per recon §E.2, times three actions, plus ~6 new params on
   BOTH `AppContext.comms` and the MCP wrapper, plus a new `comms.drain_limit` config key.
5. **The concurrency law adds wall-clock, not just code**: ≥8-way and 16-way live races, and
   "a single green run NEVER clears a concurrency test — require 20 consecutive" has **no
   mechanical enforcement** (recon flag 7). That is builder discipline measured in runs.

---

## 3. RED verification at clean HEAD

**Production tree untouched:**

```
$ git status --porcelain loremaster/loremaster/
(empty)
```

`uv run ruff check` on all five touched test files: **All checks passed!**

Every changed path is under `loremaster/tests/`:
`_comms_fakes.py`, `test_comms_promise_registry.py`, `test_comms_schema.py`,
`test_comms_tool.py`, `test_message_ledger.py` (new).

**Every file is RED at collection, each for its own intended reason** — no import typos, no
fixture bugs (proved independently in §4, where 1004 tests collect cleanly and 699 of them PASS
against a reference build):

```
test_message_ledger              ModuleNotFoundError: No module named 'loremaster.messages'
test_comms_schema                ImportError: cannot import name 'MESSAGE_SEQUENCE_NAME' from
                                 'loremaster.store.surreal_schema'
test_comms_tool                  ModuleNotFoundError: No module named 'loremaster.messages'
test_comms_promise_registry      ModuleNotFoundError: No module named 'loremaster.messages'
test_brief_ledger                ModuleNotFoundError: No module named 'loremaster.messages'
test_agent_registry              ModuleNotFoundError: No module named 'loremaster.messages'
test_comms_render_architecture   ModuleNotFoundError: No module named 'loremaster.messages'
test_comms_fleet_grouping        ModuleNotFoundError: No module named 'loremaster.messages'
```

⚠ **BLAST RADIUS, stated plainly (§9 F5):** the last four files were GREEN at HEAD and are now RED
**collaterally**, because `_comms_fakes.py` gained a module-level `loremaster.messages` import.
This is the same shape `test_brief_ledger.py` had in its own contract phase, and it clears the
instant a STUB `messages.py` lands — but it means **the builder must land the stub FIRST**, before
it can run any comms suite. I kept the message fake in `_comms_fakes.py` (subsystem-per-file, the
repo's convention) rather than minting `_message_fakes.py`; splitting would cut the collateral from
8 files to 3. **Your call — I did not decide it silently.**

**Guard-rail tests that must stay GREEN at HEAD:** none of the four collateral files can be run at
HEAD to demonstrate that, which is itself the cost above. Their green-ness is instead demonstrated
in the reference build (§4): `test_comms_promise_registry.py` scores **96/0** and the full
`test_comms_tool.py` render battery **508/0**, both including every pre-existing pin.

---

## 4. Satisfiability — the reference build, and the four defects it caught

Per the C-DEF law ("a contract ships with a satisfiability receipt"), I built a reference
implementation in an isolated scratch copy and graded the contract against it.

**Provenance receipt (#140):**
```
$ ./scripts/scratch_copy.sh /tmp/pkt03-ref
scratch copy READY: /tmp/pkt03-ref
  loremaster  -> /tmp/pkt03-ref/loremaster/loremaster/__init__.py
```
The copy imports its OWN `loremaster`, not this checkout's.

### 4.1 What the reference build contains
A real `messages.py` (value objects, constants, error tree, `MessageLedger` with the standard
five-kwarg ctor and an `async def _query` riding `run_query`); a real `generate_message_ddl()`
schema slice; and the three real `_render_comms_send`/`_drain`/`_ack` renders in `server.py`. The
ledger's STORE methods are stubs on purpose — `FakeMessageLedger` is the known-correct build the
semantics are graded against, which is exactly what the `[fake]` leg is for.

### 4.2 Results — 699 pins pass against a correct build

| group | result |
|---|---|
| ledger semantics (`[fake]` leg) | **40 passed, 4 skipped, 0 failed** |
| vocabularies · seam discovery · ctor shape | **26 passed, 0 failed** |
| schema DDL — offline + LIVE against spike-surreal | **29 passed, 0 failed** |
| promise registry (incl. all pre-existing pins) | **96 passed, 0 failed** |
| render hostile-injection battery (incl. pre-existing) | **508 passed, 0 failed** |

The 4 skips are the deliberately REAL-backend-only observations (raw row counts, the
dangling-endpoint scan, the unguarded-write control).

### 4.3 What is NOT graded, said plainly
- **Tool DISPATCH (21 pins)** — needs `_COMMS_ACTIONS` entries, three handlers, and the MCP
  wrapper params. One pin, `test_every_action_has_at_least_one_registered_case`, currently fails
  precisely because `_COMMS_ACTIONS` still holds six actions. These are the plainest pins in the
  contract (a dict of frozensets, plus calls through the existing dispatcher).
- **Ledger `[real]` leg (47 pins)** — needs the real store implementation. Its SEMANTICS are
  graded via the `[fake]` leg; what is ungraded is store fidelity, and the schema group above
  already exercises the DDL live.

### 4.4 The four defects the receipt caught — all mine, all before you saw them

1. **`session` is a PROTECTED param name even at a `RELATE ... SET`.** My schema helper bound
   `$session` and every live edge test failed with *"'session' is a protected variable and cannot
   be set"*. The store reference's §2 rule is stated in terms of `CONTENT`; `RELATE` has no
   `CONTENT` form, so the rule there is **rename the PARAM** (the COLUMN stays `session`). Fixed;
   the constraint is now a comment in the helper so the builder inherits it. **Reference-doc
   addition candidate (§9 F2).**
2. **My own endpoint-typing pin was too weak to catch its own hazard.** It asserted
   `"TYPE RELATION" in statement`. The reference build used the house `_define_relation_table`
   helper — which emits a bare `TYPE RELATION` — and **passed the offline pin while failing the
   live coercion pin.** A build reusing the existing helper unchanged would have shipped the
   `TYPE ANY`-equivalent guard. The pin now demands `TYPE RELATION IN message OUT agent` verbatim,
   with probe 5d's reasoning attached.
3. **Two `safe_str` literals were unclassified** (`'#{}'`, and the drain row's context cell). The
   deny-by-default `safe_str` channel caught them. Classified in `_SAFE_STR_PROMISE_FREE` with
   reasons — so the builder does not have to invent that classification mid-build and get it wrong.
4. **I wrote a duplicate instrument.** My `TestNoRegisteredLiteralIsORPHANED` reimplemented
   `TestEveryCommsRenderLiteralIsClassified::test_no_dead_registry_entries`, which already existed.
   Deleted. A DRY violation inside a contract that pins the DRY law — caught only because the
   reference run showed the existing pin failing on my entries first.

---

## 5. STEP 7 — the SPLIT I recommend (you rule; I recommend)

**03a — the durable core. TEST + STORE only, NO deploy.**
Groups: schema/DDL (29) + ledger send/drain/ack/concurrency/seam (94) + the fake. ≈ 0.35 wu.
Exit: full gates, cold audit, ≥8-way and 16-way races green 20 consecutive, `[real]`+`[fake]`
parity. **What it buys despite shipping nothing user-visible:** the mint, the atomic fan-out, the
recipient-existence guard and the write-once CAS are all proven at contention BEFORE any surface
depends on them — and the two unprecedented mechanisms (`DEFINE SEQUENCE`, `ulid()`) land where
their failure is a test failure, not a production one. The slice is applied by `ensure_ready()`, so
the tables and the sequence reach the store on the next deploy of any packet. Exact precedent:
packet 02a shipped test-only, no deploy, and was the right call.

**03b — the surface. DEPLOYS BOTH.**
Groups: tool dispatch (21) + renders/promises (152). ≈ 0.3 wu. Depends on 03a.
Exit: the packet's own stated exit — live-wire `send→drain→ack` round-trip including a broadcast
and a hostile body staying fenced.

If you prefer one packet, my estimate stands at 0.6–0.8 wu and the risk is a builder running out of
context between the ledger and the surface, with the tree uncommitted.

---

## 6. ESCALATIONS — five forks I did NOT decide

**E1 — does draining un-park a parked agent? A DESIGN SENTENCE AND SHIPPED CODE CONTRADICT.**
The approved design (garden plan, `drain` row) says *"drain by a parked agent flips it back to
active"*. The shipped status machine says the opposite: `AgentRegistry.touch` auto-flips only
`idle → active`, and `input_required` **NEVER** auto-flips (`agents.py:753-759`, mirrored in
`_comms_fakes.py`). Ruling 1's own reasoning cuts against the design sentence — a parked agent is
parked *because it asked a question*, and un-parking it on a drain would erase the signal that it
is waiting. **I pinned neither.** My recommendation: keep the shipped law (`input_required` never
auto-flips) and strike the design sentence. This is the eighth ambiguity you asked me to surface.

**E2 — `set_status` on `send`.** The design's tool table gives `send` a `set_status?` param
(*"`set_status=input_required` parks the sender — one-call operator question"*). Packet 03's
Scope IN does not name it. I did NOT pin it and did NOT add it to `send`'s param set. Fix now or
defer to packet 05 with the await work? Your call.

**E3 — an EXPLICIT self-addressed send.** Ruling 7 says *a broadcast* does not deliver to its own
sender. It is silent on `to=["lead"]` sent by `lead` (a deliberate self-note, or a typo). I pinned
only the unambiguous half — that a send whose recipient list omits the sender leaves the sender's
inbox empty — and said so in the test's own docstring.

**E4 — where the recipient-existence check lives; I pinned BOTH layers.** Ruling 2 routes the
teaching error through the SERVER's existing `_comms_enrich_unknown_agent`. Probe consequence #1
says the check is *"a REQUIRED, PINNED INVARIANT of the new module"*. Those are different layers.
I pinned the dispatcher (names the bad recipient AND the live roster) **and** the ledger (a
`SELECT` over `agent` by id before any `RELATE`, all-or-nothing) — defense in depth, and the
dispatcher pin accepts either error type. If you want ONE home, say which; the ledger-side pin is
the one probe 1 makes non-negotiable, so I would keep that one and thin the other.

**E5 — `AgentRefLike` would be copy #2 of a Protocol.** `briefs.py:224` defines `id`+`name`;
`messages.py` needs the identical shape. Structural typing makes them interchangeable, and a
Protocol is closer to trivia than to policy — but the DRY law says **duplication is a DESIGN
decision: escalate it, never quietly write copy #2.** My recommendation: promote it to a small
shared module both import. I contracted `messages.AgentRefLike` (so the contract is executable
either way) and am raising the design question here rather than settling it.

---

## 7. STEP 4 — every wrong build, mapped to the pin that kills it

| # | wrong build | pin |
|---|---|---|
| 1 | broadcast over `status=='active'` only | `TestBroadcastFanOut::test_broadcast_reaches_active_idle_and_parked` — fixture carries active + idle + input_required + retired |
| 2 | broadcast includes retired | `…::test_broadcast_excludes_retired_agents` |
| 3 | broadcast leaks across sessions | `…::test_broadcast_never_crosses_sessions` (+ ledger `test_a_cross_session_agent_sees_nothing`) |
| 4 | broadcast self-delivers | `…::test_broadcast_does_not_deliver_to_its_own_sender` |
| — | *(all four individually right, one wrong in aggregate)* | `…::test_the_exact_broadcast_set` |
| — | broadcast resolved through `fleet()` (a display window) | `…::test_broadcast_is_not_bounded_by_the_fleet_display_limit` — 30 agents vs a 20-row cap |
| — | `to=` ignored entirely, always broadcasts | `…::test_an_explicit_recipient_list_is_not_a_broadcast` (monoculture break) |
| 5 | drain returns another agent's messages | `test_fan_out_reaches_every_recipient_and_only_them`, `test_two_recipients_drain_independently` |
| **6** | **drain stamps MORE than it served** | `TestDrainStampsExactlyWhatItServed` — **every fixture is N > cap** |
| 7 | `peek=true` stamps anyway | `TestPeekStampsNothing` (+ its non-peek POSITIVE CONTROL) |
| 8 | counts computed over the capped window | `test_counts_are_computed_over_the_WHOLE_set…`, `test_directive_pending_is_also_over_the_whole_set` |
| 9 | `ACK REQUIRED` lists non-directives / omits them / lists all | `PromiseProof("ACK REQUIRED: …")` — NO-EMIT leg is a **signal row**, not an empty drain, so an emits-for-every-row build fails |
| 10 | ack stamps ANOTHER agent's edge | `test_acking_another_agents_edge_leaves_that_edge_UNCHANGED` — positive assertion on the victim's row |
| 11 | the CAS is not write-once | `test_a_second_ack_never_overwrites_the_first_stamp` — sleeps so `time::now()` demonstrably advances (a DIFFERENT second value) |
| — | write-once is a property of edge rows, not of the guard | `test_the_guard_is_what_does_the_work` — unguarded UPDATE **does** overwrite (probe 4 leg C control) |
| 12 | the four-way empty return passed through undifferentiated | `TestAckDisambiguatesTheFourWayEmptyReturn` — three survivors pinned **separately**, plus a mixed batch forcing all four fates in ONE call |
| 13 | `seq` minted read-max-then-CREATE | `TestConcurrentSendsMintDistinctSeqs` at 8- and 16-way, **separate ledger instances on separate connections** |
| — | mints correctly then loses rows | `test_every_concurrent_send_is_readable_by_its_recipient` |
| 14 | a consumer breaks on a seq GAP | `test_a_gap_breaks_nothing` — burns a number via `sequence::nextval`, asserts counts come from ROWS |
| 15 | hand-rolled conflict matching (routing ≠ sharing) | **inherited automatically**: `TestTheLedgerIsDiscoverableByTheSeamEnumerator` guarantees `MessageLedger` enters `_QUERY_SEAMS`, which parametrises ~19 existing retry/marker/**mutation** pins over it |
| 16 | partial fan-out (N−1 edges + one failure) | `test_a_mixed_batch_is_all_or_nothing`, `test_a_rejected_send_leaves_no_message_row_at_all`, `test_no_dangling_edge_survives_a_send` |
| 17 | duplicate recipient → LOUD `UNIQUE` ERR | `test_a_repeated_recipient_is_deduped_before_the_relate_loop` + the schema's own duplicate/different-pair control pair |
| 18 | unregistered recipient dropped, or a dangling edge | `TestSendValidatesEveryRecipientBeforeWritingAnyEdge` (fixture uses a name that does not exist) + `TestUnregisteredRecipientIsTheEXISTINGTeachingError` (asserts the roster clause, i.e. the EXISTING helper) |
| 19 | body truncated instead of rejected; blank accepted | `TestSendValidatesTheBody` — incl. an at-cap POSITIVE control and a delivery check after the reject |
| 20 | `thread` defaults to something else | `test_thread_defaults_to_the_session` + `test_an_explicit_thread_is_kept` (monoculture break) |
| 21 | parked sender un-parked by drain | **NOT PINNED — escalation E1** |

**The quantifier law** is carried by two ∀ pins, each with all fates FORCED by fixture:
`TestSendValidatesEveryRecipientBeforeWritingAnyEdge` (every recipient delivered-or-reported) and
`test_a_mixed_batch_reports_every_seqs_own_fate` (every requested seq accounted for, in order).

**Not killed:** only #21 (escalated). Everything else has a discriminating fixture.

---

## 8. STEP 5.4 — the pinned KNOWN BOUND: does the drain render pull its re-open trigger?

**NO — and I checked before designing the render, not after.**

The bound (`test_comms_promise_registry.py:2088-2115`) fires the day anyone classifies a **bare,
placeholder-only** template (`"{msg}"`, `"{line}"`) as promise-free, because that is what would
make a value-carried promise invisible. My drain row template is:

```
"#{seq} [{grade}] {sender}→you{context}: {body}"
```

It carries structural literal text (`#`, ` [`, `] `, `→you`, `: `), so it is **not** a
placeholder-only template, and **I added no placeholder-only template to `_PROMISE_FREE`.**
Verified rather than reasoned: the bound test PASSES in the reference build (§4.2, promise registry
96/0). The bound stays closed and stays honest.

---

## 9. Things I found that you did not ask about

**F1 — `_define_relation_table` cannot express ruling 3, and NO edge table in this repo is typed
today.** The helper emits `DEFINE TABLE IF NOT EXISTS {name} TYPE RELATION SCHEMAFULL` — no
`IN`/`OUT`. Ruling 3 mandates `IN message OUT agent`, so the helper must be **extended** (per ONE
IMPLEMENTATION — not forked into a second helper). The wider fact: `briefed`, `refers` and
`answers_to` are all bare `TYPE RELATION`, so **the only endpoint validation the engine offers is
currently unused everywhere in this codebase.** Packet 04 owns #105; this is adjacent and cheap.

**F2 — reference-doc addition (measured live this session).** §2's protected-name rule is written
in terms of `CONTENT` writes. `RELATE` has no `CONTENT` form, and a `RELATE ... SET session =
$session` is rejected with *"'session' is a protected variable and cannot be set"*. The rule for
`RELATE` is: **the COLUMN may be `session`; the PARAM must not be.** Worth a line in §2 or §7 —
the production fan-out will hit this on its first run.

**F3 — the `generate_ddl()` registration gap gets a third instance** (recon §C.2 / flag 1).
`message`/`to` follow the comms precedent (own generator, applied by `MessageLedger.ensure_ready()`)
and so will sit outside both `EXPECTED_TABLES` and `test_comms_schema.py:632`'s subset pin, like
`finding_counter` and `brief_counter` already do. My contract asserts the tables via
`ensure_ready()` + `INFO FOR DB` rather than via those frozensets, which **sidesteps** the gap for
packet 03 but does not close it. Closing it means making those pins `==` rather than `<=`, which is
a change to two existing files and outside my writable set.

**F4 — `_MIN_KNOWN_SEAMS = 10` is a floor, not an equality pin** (recon flag 6) — confirmed by
reading it. A new ledger raising the true count to 11 passes. My
`TestTheLedgerIsDiscoverableByTheSeamEnumerator` is what actually notices if `MessageLedger` falls
out; the floor would not.

**F5 — the collateral blast radius** (four previously-green files) — §3, with the mitigation and
the alternative I did not take.

**F6 — a process receipt worth keeping.** The satisfiability run caught **four** defects, and the
two most valuable were ones I could not have seen by reading my own tests: a pin that passed for
the wrong reason (#2, weak endpoint assertion) and an instrument I duplicated without knowing it
existed (#4). Both are the contract-adversary's native question, answered one stage early and for
the cost of one scratch build. `/tmp/pkt03-ref` is left in place so the adversary can start from a
working reference rather than rebuild one.

**F7 — no lore-tool fallback to declare.** I used `lore_search`/`lore_get_symbol` only for
definition lookups where the name was already known; the rest of this task was reading named files
at known paths, plus live probes. No structure question was answered by grep-instead-of-lore, so
there is no friction to file.

---

# UPDATE 5eb445b

Re-read `docs/plans/v2/03-comms-message-graph.md` at HEAD `5eb445b`, plus the two probe reports it
newly cites (`REPORT-probe-enforced-clause.md`, `REPORT-audit-edge-preflight.md`) and the reconciled
§4 of the store reference. My model of the task matches the packet file; nothing below is a guess.

**Headline: 296 → 347 pins (+51). Sizing 0.6–0.8 → 0.7–0.9 wu total.** And the extension caught
**two PRE-EXISTING pins that certify the OLD world** — either one would have gone RED on a correct
build and trapped the builder between a test it may not edit and the new policy.

## Items 1–7 — the pins added or changed

**1. SPLIT labelling (contract kept WHOLE).**
Banner in `test_message_ledger.py`'s module docstring (`PACKET 03 (the durable core — TEST-ONLY, no
deploy)`), a matching banner over the packet-03 section of `test_comms_schema.py`, and a
`PACKET 03a` banner over the dispatcher section of `test_comms_tool.py` naming the other file too.
Selectors, verified:

```
# packet 03 — the durable core (TEST-ONLY, no deploy)
uv run pytest loremaster/tests/test_message_ledger.py \
              loremaster/tests/test_comms_schema.py \
              loremaster/tests/test_surreal_schema.py -n auto

# packet 03a — the surface (deploys both)
uv run pytest loremaster/tests/test_comms_tool.py \
              loremaster/tests/test_comms_promise_registry.py -n auto
```

⚠ FLAG: a proper pytest MARKER would be better than file selectors, but `pyproject.toml` has no
`markers =` list and adding one is outside my writable set. Say the word and I will specify the
exact stanza.

**2. `ENFORCED` on the `to` edge.** Rewrote `TestMessageDdlOffline::
test_defines_the_to_edge_as_a_typed_relation_table` to assert the statement BYTE-EXACT
(`DEFINE TABLE OVERWRITE to TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL`), with a
per-clause comment naming the measured failure each one prevents. New live class
**`TestEnforcedIsLiveOnTheDeliveryEdge`** (6 pins): a real-pair POSITIVE CONTROL *first*, ghost-`out`
rejected, ghost-`in` rejected, no dangling row survives a rejected RELATE, **`INSERT RELATION` closed**
(the door no app check can reach), and a control proving that rejection is the CLAUSE not the VERB.
Ruling 8 honoured — the ledger-side check is untouched and still pinned.

**3. Relation-table policy flip + the dirty-store migration pin.**
New **`TestRelationTablePolicyFlip`** (3): `briefed` declares its endpoint tables, `briefed` uses
`OVERWRITE`, and a ∀ pin over **four** generators (`agent`/`brief`/`message`/`graph`) asserting every
emitted relation table is typed AND `OVERWRITE` — quantified, not a hand-list, so a relation table
added tomorrow is covered the day it is written.
New **`TestRelationFlipAgainstAnExistingStore`** (4), the §1.6 shape: a BASELINE proving the old world
really is unguarded, then apply-OLD → write-row → apply-NEW asserting the guard is LIVE via **two
independent instruments** (the stored definition changed; a ghost is now refused), the old row
SURVIVES intact, and re-application does not drift. **Graded live: the `OVERWRITE` migration does land
on a dirty store.**

**4. `set_status` on `send` — IN.** Ledger: new class
**`TestSetStatusMarksTheQuestionItDoesNotStoreAState`** (3) — it marks the message, the ordinary send
is NOT a question (parameter-monoculture break), and a question still delivers normally (a build
treating it as a status-only side channel loses the question). Dispatcher:
`TestNewActionSpecs::test_send_params_and_required` now expects `set_status` in `send`'s param set.

**5. `AgentRefLike` — ONE shared home.** New **`TestAgentRefLikeHasONEHome`** (2): `briefs.AgentRefLike
is messages.AgentRefLike` (the SAME object), and `__module__` is neither ledger — pinned structurally,
so the contract does not dictate the filename, only that there is exactly one. Reference build
confirms it is satisfiable (`loremaster.comms_refs`).

**6. Explicit self-addressed send ALLOWED.** New
`test_an_EXPLICIT_self_addressed_send_IS_delivered`. Kept the existing
`test_a_sender_never_receives_its_own_message` and rewrote its docstring from "escalation E3 open" to
ruling 7's two clauses. **The pair is the point:** the new pin is what stops a build from "satisfying"
no-self-broadcast by filtering the sender out of EVERY list — which would pass the old pin alone while
silently discarding a legal message.

**7. Ruling 9 — the DERIVED waiting state.** The largest addition.
**`TestTheWaitingStateIsDerived`** (12): baseline no-question control · unanswered question makes the
asker waiting · an answer clears it **with no write to the agent between the two assertions** · an
answer on a DIFFERENT thread does not clear it · a message the ASKER sends on its own thread is not an
answer (else an agent answers itself) · a message PREDATING the question is not an answer · another
agent's question never makes me wait · the OLDEST unanswered question is reported · answering one of
two leaves the other · **the derivation writes NOTHING** (row counts unchanged over repeated reads —
the structural pin that a build has not reintroduced stored state) · **draining does NOT change it**
(the struck design sentence, pinned dead) · and its POSITIVE CONTROL, that draining *the answer* does
clear it (so the pin above cannot pass by being stuck at "waiting" forever).
**`TestTheDerivedWaitingStateKnownBound`** (2), per the pin-the-miss law: the out-of-band answer leaves
the state waiting, carrying its RE-OPEN TRIGGER in the docstring (*the day a relay path can write to
the thread — an operator CLI posting through the ledger, or packet 05's `await`/`story` gaining a relay
verb — close this bound and delete the pin*), plus an executable demonstration that relaying clears it.

⚠ **ESCALATION E6 (new, mechanism not semantics).** Ruling 9 gives the SEMANTICS ("a question thread
with no answer on it") but not the MECHANISM. I chose the smallest surface consistent with it — a
`message.question: bool DEFAULT false` column set when `send` carries `set_status='input_required'`, so
the derivation reads `message` + `to` only and adds NO `agent` column. That is a design choice I am
surfacing, not settling: a third `grade` value or a thread-kind table would also satisfy the ruling.

## New totals and sizing, per group

| group | packet | pins (was → now) |
|---|---|---|
| schema/DDL — message, `to`, sequence, ENFORCED, relation flip, dirty-store migration | **03** | 29 → **42** |
| ledger — send/drain/ack/concurrency/seam/`set_status`/waiting-derivation/shared-Protocol | **03** | 94 → **132** |
| `test_surreal_schema.py` guard-kind pin (widened, +1 generator registered) | **03** | — → **1 changed** |
| tool dispatch | 03a | 21 → **21** (1 changed) |
| render hostile battery | 03a | 147 → **147** |
| promise registry + proofs | 03a | 5 → **5** |
| | | **296 → 347** |

**Sizing: packet 03 ≈ 0.45 wu · packet 03a ≈ 0.3 wu · total 0.7–0.9 wu.** Packet 03 absorbed
everything the update added: ruling 9 is a new stored column *plus* a new derivation query *plus* its
own KNOWN BOUND; the relation flip touches four generators, two pre-existing pins and a migration path;
`ENFORCED` and the shared-Protocol module are small but real. Still a FLOOR — the contract-adversary has
not run.

## Contradictions with my own earlier work — all resolved in the open, none overwritten silently

| # | what | resolution |
|---|---|---|
| 1 | My `test_every_field_uses_the_overwrite_guard_and_every_object_uses_if_not_exists` asserted `IF NOT EXISTS` for **every** `DEFINE TABLE` — item 2 makes that wrong for edges | SUPERSEDED in place, split per object KIND, with a comment saying so and naming the failure each branch prevents. Not deleted. |
| 2 | My `to`-edge pin demanded only `TYPE RELATION IN…OUT…` | tightened to the byte-exact statement incl. `OVERWRITE` + `ENFORCED` |
| 3 | My self-send pin's docstring said E3 was an open escalation | rewritten to ruling 7's two clauses; the pin itself still holds and is now half of a discriminating pair |
| 4 | My dirty-store pin read `INFO FOR TABLE` for the stored definition | **my instrument was wrong** — `INFO FOR TABLE` carries fields/indexes only; the table's own DEFINE lives in `INFO FOR DB.tables`. It failed on a CORRECT build until fixed. A probe needs its instrument checked too. |

## ⚠ TWO PRE-EXISTING PINS CERTIFIED THE OLD WORLD — found by grep, not by luck

Repo law: *"tests written before a semantic change certify the OLD world; on any rename, grep the test
tree for assertions pinning retired strings."* I ran that sweep and it paid twice. Either one would
have gone RED on a correct build — packet 02's C-DEF class verbatim.

1. **`test_comms_schema.py::TestBriefedDdlOffline::test_table_is_a_schemafull_relation`** asserted the
   byte-exact retired literal `DEFINE TABLE IF NOT EXISTS briefed TYPE RELATION SCHEMAFULL`. Rewritten
   to assert only what it always MEANT (briefed is a SCHEMAFULL relation table); the typing and
   `OVERWRITE` assertions moved to `TestRelationTablePolicyFlip`.
2. **`test_surreal_schema.py::TestFieldDdlConvergesOnAnExistingStore::
   test_every_define_statement_carries_the_guard_its_kind_requires`** — the ∀ #107 guard pin — ruled
   that **every** `DEFINE TABLE` must be `IF NOT EXISTS`, i.e. it actively certified the silent-no-op
   as correct for edges. Widened: `TABLE (RELATION)` is now its own kind requiring `OVERWRITE`,
   `SEQUENCE` added (a bare `DEFINE SEQUENCE` raises on re-apply → boot crash), the failure message
   rewritten, and **`generate_message_ddl` registered in its generator dict** — a new generator sitting
   outside that dict is the registration gap the class exists to close.

## Receipts

**Satisfiability re-graded against the extended reference build** (`/tmp/pkt03-ref`, provenance-asserted):

```
test_comms_schema + test_comms_promise_registry + test_surreal_schema
  + test_graph_surreal + test_brief_ledger ..................... 623 passed, 0 failed
ledger [fake] + statics + render battery ...... 570 passed, 5 skipped, 1 failed
```
The single failure is `test_every_action_has_at_least_one_registered_case`, RED because
`_COMMS_ACTIONS` still holds six actions — the packet-03a dispatch group, which remains ungraded by
design (§4.3). **`test_graph_surreal.py` and `test_brief_ledger.py` are green THROUGH the relation
flip**, so its blast radius on existing suites is exactly the two pins above and no more.

**RED at clean HEAD, each for its own reason:**
```
test_message_ledger          ModuleNotFoundError: No module named 'loremaster.messages'
test_comms_schema            ImportError: cannot import name 'MESSAGE_SEQUENCE_NAME' …
test_comms_tool              ModuleNotFoundError: No module named 'loremaster.messages'
test_comms_promise_registry  ModuleNotFoundError: No module named 'loremaster.messages'
test_surreal_schema          ImportError: cannot import name 'generate_message_ddl' …
```
`test_surreal_schema.py` joins the collateral list (§3) — now **9** files RED at HEAD, cleared by the
stub. `uv run ruff check loremaster/tests/`: **All checks passed!**

```
$ git status --porcelain loremaster/loremaster/
(empty)
```

## One thing in the packet file itself

⚠ The **Exit** section still reads *"Full gates + cold audit + **deploy BOTH + smoke**: send→drain→ack
round-trip on the live wire…"* while the header says **`DEPLOY: NO — test+store only`** and the SPLIT
gives the live-wire smoke to 03a. The Exit block looks un-edited from before the split. Flagging, not
assuming — packet 03's real exit is presumably gates + cold audit + INDEX row, with the deploy and the
smoke moving to 03a.

---

# UPDATE post-adversary

Read `REPORT-adversary-pkt03.md` in full, §7 residuals included. **All 3 BLOCKERs, the MAJOR, all 5
lesser and 5 of the 10 residuals are closed.** Nothing in its §5 verified-strong list was weakened —
every change is additive or a fixture-value change; no assertion was relaxed.

**The proof, not the claim:** every one of the eight wrong builds that passed **57 / 0** now goes
RED, each mutation applied to the reference fake with the real contract run against it, and the
correct-build control green after every restore.

| adversary's wrong build | before | now | the pin that kills it |
|---|---|---|---|
| **W1** `awaiting_answer` keys on `grade`, never reads `question` | 57✓ 0✗ | **3 RED** | `test_a_SIGNAL_grade_question_DOES_make_the_sender_waiting` · `test_a_DIRECTIVE_sent_without_set_status_does_NOT_make_the_sender_waiting` · `test_asked_at_IS_the_questions_own_created_at` |
| **W2** `directive_pending` = elided remainder | 57✓ 0✗ | **2 RED** | `test_directive_pending_is_also_over_the_whole_set` · `test_directive_pending_counts_directives_INSIDE_the_window_too` |
| **W9** fan-out drops the LAST recipient when >2 | 57✓ 0✗ | **2 RED** | `test_EVERY_recipient_actually_RECEIVES_the_message[3]` and `[4]` |
| **W10** drops the id-sorted-last when >2 | 57✓ 0✗ | **RED** | same pin (it is quantified over arity, not spot-checked at 3) |
| **W3** `question = (set_status is not None)` | 57✓ 0✗ | **2 RED** | `test_a_DIFFERENT_set_status_value_does_NOT_mark_a_question[idle]`/`[active]` |
| **W4** `asked_at` fabricated at read time | 57✓ 0✗ | **1 RED** | `test_asked_at_IS_the_questions_own_created_at` |
| **W5** message id carries the table prefix | 57✓ 0✗ | **1 RED** | `test_the_message_id_is_BARE_with_no_table_prefix` |
| **W8** dedupe by `name` instead of `id` | 57✓ 0✗ | **1 RED** | `test_dedupe_keys_on_IDENTITY_not_display_name` |
| **M8** `note` accepted and silently discarded | not built | **2 RED** | `test_ack_note_lands_on_the_edge_the_CAS_WON` · `test_a_note_never_reaches_an_ALREADY_acked_edge` |
| **S3** the flip lands on `to` but NOT on the production tables (**MAJOR-4**) | 3 offline RED only | **7 RED** | + `test_the_flip_LANDS_on_an_existing_untyped_relation_table[briefed\|refers\|answers_to]` · `test_a_HETEROGENEOUS_row_is_write_poisoned_not_dropped` |

Correct-build control after every restore: **77 passed, 9 skipped, 0 failed.**

## How each was closed

**B1 — the mechanism is now forced to be READ.** The root cause was a fixture correlation, not a
missing assertion: `_ask()` hardcoded `grade=DIRECTIVE` and `_answer()` hardcoded `SIGNAL`, so
`question` and `grade=='directive'` were identical in every fixture in the section. Both helpers now
take `grade` as a PARAMETER, and three pins break the correlation in all three directions — a SIGNAL
question parks, an ordinary DIRECTIVE does not, and a DIRECTIVE-graded *answer* still clears. The
contract block now states the orthogonality explicitly so the next reader cannot re-couple them.

**B2 — the ∀ is now evaluated where the branch fires.** `test_EVERY_recipient_actually_RECEIVES_the_message`
is parametrized over recipient COUNT `[1,2,3,4]` — quantified over arity rather than spot-checked at
three, so a wrong build cannot happen to be correct at the one value tested. It asserts the
**inboxes**, not the receipt, with the reason in the failure message: *the receipt agreeing with
itself is not delivery*. Its raw-store sibling `test_the_receipt_COUNT_equals_the_edges_actually_written`
counts edges straight off the `to` table, so a build with a matching broken drain cannot satisfy both.

**B3 — the arithmetic no longer aligns.** 5 signals + 2 directives at cap 5 made directives (2) and
the elided remainder (7−5=2) identical. Now 6 + 2 at cap 5: elided 3 ≠ directives 2 ≠ window
directives 0 — three distinct numbers, so the assertion can finally perform what its message
promised. A `fixture guard` assertion pins the arithmetic itself, so a future edit cannot silently
re-align it. Its complement puts the directives INSIDE the window, killing an elision-scoped count.

**MAJOR-4 — the instrument is now aimed at the tables that exist.** New
`TestTheFlipAgainstTheTablesThatACTUALLYEXISTInProduction`: the flip LANDS on `briefed`/`refers`/
`answers_to` (parametrized, each starting from the OLD untyped definition with a BASELINE assertion
that it really was untyped), plus the narrowing's documented hazard — a heterogeneous row is
**write-poisoned, readable, never dropped** — with a homogeneous CONTROL whose only difference is
the endpoint's table. That control is deliberate: the adversary's own first write-poisoning probe
failed on both arms for two different reasons (its §8.2), and attribution is unsound without it. It
also makes the pre-flight audit's verdict *actionable* — production's rows are all the control's
shape, and that shape migrates cleanly.

**Lesser + residuals.** M5 `set_status` second value (parametrized `idle`/`active`) · M6 `asked_at`
provenance · M7 bare-id + `message_id` round-trip · M8 `ack_note` (three pins: it lands on the edge
the CAS **won**, an ack with no note leaves it unset, and a second ack cannot smuggle a new note
through the write-once door) · **7.2** concurrent seqs all exceed the pre-race maximum (monotonic,
which survives legal gaps where "consecutive" cannot) · **7.3** `drain(limit=1)` and `ack(seqs=[])`
· **7.4** the wrong-table endpoint is now an **existing** record, so `ENFORCED` cannot reject it
before typing is consulted · **7.5** a send in `wave9` breaks the session monoculture.

## Where I disagree, or diverged

1. **M8 is not a spec gap.** The adversary surfaced it as *"may be a genuine spec gap rather than a
   contract miss"*. It is not: `ack | agent, seqs[], note?` and the `to` edge's `ack_note?` column
   are both in the approved design (`one-of-claude-codes-nifty-garden.md` §Data model / §Tool
   surface). The contract simply had no pin. Closed as a contract miss, and I added the write-once
   clause the design does not state but the CAS law implies — flagging that one as my inference.
2. **7.1 (racer lifetimes) — I closed it rather than only escalating.** The adversary was right that
   single-op racers match BOTH precedents it was pointed at, and right to escalate the repo-wide
   pattern. But repeated-ops-per-racer was cheap here, so I took the monotonicity half now
   (residual 7.2's pin) and leave the *lifetime-overlap* question for the operator as a repo-wide
   ruling. I am not claiming 7.1 fully closed — only that packet 03 no longer depends on it for the
   ORDERING property.
3. **7.8 (`[real]` leg ungraded) stands, and I agree it is the largest residual risk.** Neither of
   us can close it without building the real store implementation. It is the strongest argument for
   packet 03 shipping test-only with a cold audit before 03a starts.
4. **Nothing else disputed.** The eight surviving builds were real and my fixtures were the cause in
   every case.

## New totals and re-sizing

| group | packet | pins (was → now) |
|---|---|---|
| schema/DDL incl. MAJOR-4's three production tables | **03** | 42 → **47** |
| ledger — send/drain/ack/concurrency/derivation/`ack_note`/boundaries | **03** | 132 → **180** |
| `test_surreal_schema.py` guard-kind pin (widened) | **03** | 1 changed |
| tool dispatch | 03a | 21 |
| render hostile battery | 03a | 147 |
| promise registry + proofs | 03a | 5 |
| | | **347 → 400** |

**Re-sized: packet 03 ≈ 0.55 wu · packet 03a ≈ 0.3 wu.**

⚠ **You asked me to say so if this pushes packet 03 past the split threshold. IT DOES — 0.55 is
well beyond 0.30, and it was already over at 0.45.** My recommendation, and the seam I would cut on:

> **03 = the STORE.** Schema/DDL, the relation-table policy flip, `ENFORCED`, all three
> dirty-store migration pins, and the guard-kind pin. **47 pins + 1 changed, ≈ 0.2 wu.** It is a
> clean seam: it touches only `surreal_schema.py`, it has no dependency on `messages.py` existing,
> and it is the only part of packet 03 that changes behaviour for code **already in production**
> (101,479 live edge rows) — which is exactly the work that deserves its own cold audit rather than
> riding along behind a new module.
>
> **03b = the LEDGER.** `messages.py`, the shared `AgentRefLike` module, and all 180 ledger pins.
> **≈ 0.35 wu.** Depends on 03.
>
> Then **03a = the surface**, unchanged at ≈ 0.3 wu.

The alternative — keeping the store and ledger together at 0.55 — is defensible if you would rather
not pay two more audit cycles, but the relation flip against live production tables is the piece I
would least like to see land inside a large wave.

## Receipts

```
$ git status --porcelain loremaster/loremaster/
(empty)

$ uv run ruff check loremaster/tests/
All checks passed!
```

Satisfiability, re-graded in the provenance-asserted scratch copy after every change:
```
test_comms_schema + test_comms_promise_registry + test_surreal_schema
  + test_graph_surreal + test_brief_ledger ................ 628 passed, 0 failed
test_message_ledger [fake] + statics ......... 77 passed, 9 skipped, 0 failed
test_comms_tool render injection battery ..... 505 passed, 1 failed
```
The single remaining failure is `test_every_action_has_at_least_one_registered_case` — RED because
`_COMMS_ACTIONS` still holds six actions. That is the packet-03a dispatch group, ungraded by design.

**RED at clean HEAD, each for its own reason** (unchanged, 9 files; the three that carry new imports
shown):
```
test_message_ledger   ModuleNotFoundError: No module named 'loremaster.messages'
test_comms_schema     ImportError: cannot import name 'MESSAGE_SEQUENCE_NAME' …
test_surreal_schema   ImportError: cannot import name 'generate_message_ddl' …
```

**One regression I caused and caught:** adding `ack_note` to `InboxEntry` broke the fixture builders
in `test_comms_tool.py` and `test_comms_promise_registry.py` (64 render-battery pins RED on a
*correct* build). Fixed; both back to 505/1 and 96/0. Recording it because it is the same class the
adversary found in me twice — a pin red for a reason that is not its subject.

---

# UPDATE collection-fix

**You are right, the defect is mine, and it is worse than you measured.** Reproduced at clean HEAD
before touching anything:

```
$ uv run pytest --collect-only -q
4472 tests collected, 9 errors in 2.89s
Interrupted: 9 errors during collection
```

**NINE files, not six.** `_comms_fakes.py` took down six via the shared-module import you named — and
I had ALSO put not-yet-existing symbols into the module-level import blocks of two PRE-EXISTING
schema suites (`test_comms_schema.py` → `MESSAGE_SEQUENCE_NAME`/`MESSAGE_TABLE`/`TO_RELATION`/
`generate_message_ddl`; `test_surreal_schema.py` → `generate_message_ddl`), killing ~480 more
pre-existing pins the same way. Same defect, second and third instance, in files nobody had flagged.
I am recording that rather than fixing only what was named.

## The fix — one rule, applied uniformly

**A module-level import must be HEAD-safe. Anything that needs a not-yet-built symbol is imported at
CALL time, inside the function that uses it.**

1. **`_message_fakes.py` (NEW)** — the message fake moved out of `_comms_fakes.py` entirely, which is
   reverted to its HEAD content. This is your preferred fix and the right one: only
   `test_message_ledger.py` imports the new module, so the regression is **structurally impossible**
   rather than merely remembered. Its docstring carries the whole incident — why the file exists, the
   RED-vs-UNCOLLECTABLE distinction, and the #133 reason neither grader could see it.
2. **`test_message_ledger.py`, `test_comms_schema.py`, `test_comms_tool.py`, `test_surreal_schema.py`**
   — `_msg()` / `_msg_fakes()` / `_schema()` call-time accessors replace the eager imports. Each
   carries the same comment block naming the defect. PLC0415 is an ignored house idiom here, so this
   is sanctioned style, not a workaround.
3. `test_comms_promise_registry.py` needed no change — its packet-03 helpers already used call-time
   imports; it was collateral damage from `_comms_fakes.py` alone.

Two import-time traps caught on the way, both worth knowing: **default parameter values are evaluated
at import** (`grade: str = _msg().MESSAGE_GRADE_SIGNAL` re-broke collection — now `None` with the
default resolved in the body), and a **class-body constant** does the same (`_OLD_DDL` → a
`_old_ddl()` staticmethod).

## Receipts

**1. Full collection at clean HEAD — ZERO errors, well above baseline:**
```
$ uv run pytest --collect-only -q
6079 tests collected in 3.25s
```
No error line, no `Interrupted`. Baseline 5694 → **6079 collected (+385)**. Note the two numbers are
not the same kind: 5694 was a PASSED count and 6079 is a COLLECTED count, so the honest reading is
"every previously-collected test is collected again, plus this contract's pins" — which the per-suite
run below demonstrates directly.

**The four suites that had nothing to do with packet 03, green again at clean HEAD:**
```
test_brief_ledger                120 passed in 5.65s
test_agent_registry              150 passed in 6.41s
test_comms_fleet_grouping         28 passed in 1.66s
test_comms_render_architecture    26 passed in 1.72s
```

**2. The contract is still RED for its OWN reason — and it is now RED rather than UNCOLLECTABLE:**
```
$ uv run pytest loremaster/tests/test_message_ledger.py -q
14 failed, 166 errors in 12.65s
E  ModuleNotFoundError: No module named 'loremaster.messages'
```
180 pins COLLECT and then fail on their own assertion path naming the module they need. The fix did
not make anything satisfiable — the mutation matrix below is the proof.

**3. Production tree:**
```
$ git status --porcelain loremaster/loremaster/
(empty)

$ uv run ruff check loremaster/tests/
All checks passed!
```

**4. YES — the satisfiability runs needed re-doing, and I re-did all of them.** The seam moved
(`_comms_fakes.py` → `_message_fakes.py`) and ~30 call sites changed shape, so nothing carried over.
Re-run in the provenance-asserted scratch copy against the reference build:

```
test_message_ledger [fake] + statics ............ 85 passed, 9 skipped, 0 failed
test_comms_schema + test_comms_promise_registry . 317 passed, 0 failed
+ test_surreal_schema + test_graph_surreal
  + test_brief_ledger + test_comms_tool ......... 1308 passed, 23 failed
                                                  (all 23 in test_comms_tool.py)
test_comms_tool render injection battery ........ 505 passed, 1 failed
```
The only failures are in `test_comms_tool.py` — the packet-03a dispatch group, ungraded by design
because the reference build has no `_COMMS_ACTIONS` entries. **Zero failures in any other file.**

**All eight mutation kills re-proven against the moved seam** (mutations now applied to
`_message_fakes.py`), correct-build control green after restore:
```
W1 3 RED · W2 2 RED · W3 2 RED · W4 1 RED · W5 1 RED · W8 1 RED · W9 2 RED · M8 2 RED
CTRL (correct build)  77 passed, 9 skipped, 0 failed
```

## The checklist line, added — and the half I would add to it

Yours, adopted verbatim: **a contract that touches a SHARED test-support module must be
collection-checked at CLEAN HEAD, not only in a scratch copy holding the reference build.**

The half I would add, because it is what made my instance bigger than yours: **it is not only shared
modules.** Two of my three instances were plain pre-existing TEST files whose module-level import
block I appended a not-yet-existing symbol to. The generalisable rule is about the IMPORT, not the
file's role:

> **Any module-level import of a symbol the contract is about to create makes its whole file
> uncollectable at HEAD. Run `pytest --collect-only -q` at clean HEAD and require ZERO errors —
> that single command catches every instance, shared module or not, and takes three seconds.**

It is now the first thing I will run after writing a contract, before the satisfiability build —
because the satisfiability build is precisely the environment in which this defect cannot be seen.
