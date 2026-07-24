> ⚠ **STRUCK AS AUTHORITY 2026-07-24** (operator; finding #181; reset commit 0941aab): an independent adversary run, but briefed by the struck orchestrator and grading a corpus that changed after its verdict — stale, not authority. Its empirical wrong-build receipts may serve as LEADS in the blind-diff step only. Corpus at tag `pkt03b-tainted-corpus`.

brief-base v6 read

# REPORT-adversary-surface-03b — contract adversary, packet 03b served surface

**Graded at:** repo `feat/surreal-unification` HEAD `45cc161`, clean, 2026-07-24.
**Contract graded:** `test_comms_tool.py` · `test_comms_promise_registry.py` · `test_message_ledger.py`.
**Spec:** `docs/plans/v2/03b-comms-surface-design-rulings.md` §S1–S5/§S8 + delta rows A–E;
`docs/plans/v2/03a-2-consume-path-design-rulings.md` rows 1–11.
**All probes ran OUTSIDE the repo**, in `/home/ejprice/scratch/adv03b` (built by
`scripts/scratch_copy.sh`). No repo file was edited except this report.

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT.**
- **PROVENANCE:** `loremaster.__file__ = /home/ejprice/scratch/adv03b/loremaster/loremaster/__init__.py` (scratch, not home).
- **SATISFIABILITY CONTROL: PASSES.** My reference build of S4.1/S4.2/S4.3/S5 goes **1092 passed / 0 failed / 12 skipped** on first run — the contract is satisfiable and its RED is honest (242 failed / 850 passed baseline, all from genuinely-absent production symbols).
- **P1 RESULT: 32 of 41 wrong builds SURVIVED the contract with 0 failures.** Every survivor carries a served-surface diff as its positive control.
- **THE SINGLE MOST DANGEROUS SURVIVOR — the NO-OP FIX, twice:** `_render_comms_send` and `_render_comms_ack` can be built PERFECTLY and **never called by their handlers**. `AppContext.comms(action="send"/"ack")` returning a hardcoded `"no unread messages"` passes **1092/1092**. The drain has a wiring pin; send and ack have none.
- **MISSING PINS: 2 BLOCKER · 9 CRITICAL · 8 MAJOR · 6 MINOR** (§3, each with the test to write and the defect it catches).
- **S4.3 (the ack render) is behaviourally UNPINNED end to end** — group order, request order, the receipt's own counts, and acked-vs-already-acked can all be wrong (W10–W15b).
- **S5's ruled-verbatim paragraph is pinned on 2 substrings out of ~7 claims.** Serving "bodies cap at **20000** chars", or INVERTING peek/grade/broadcast semantics, passes 1092/1092 (W16–W19).
- **P1b quantifier table: §2.** 39 invariants classified; **19 are guarded-by-fixture or unreachable**, each with a surviving door-build receipt.
- **P2 perturbation: 5 perturbed pins, each GREEN on the correct build and RED on exactly its target wrong build** (§4) — the pairs the fixture-discrimination law demands.
- **ESCALATION, outside my three files: the repo is RED at HEAD `45cc161`.** `test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts` fails (docstring says 35 importers, 36 exist) — broken by the 03b wave's own `a774c8f`. Also: design-doc Residual 8's "36→0 mypy" is **58**, and 6 of them are NOT paid by building S4/S5. §6.

---

## 1 — Method and its controls (P0)

| leg | receipt |
|---|---|
| scratch provenance | `scripts/scratch_copy.sh /home/ejprice/scratch/adv03b` → `loremaster -> /home/ejprice/scratch/adv03b/loremaster/loremaster/__init__.py` (asserted by the tool, printed above) |
| RED baseline reproduced | `242 failed, 850 passed, 12 skipped` — matches the lead's stated figure exactly |
| RED honesty (P7) | failure reasons classified: 108 `AttributeError … no attribute '_render_comms_drain'`, 78 `… '_render_comms_send'`, 22 `… '_render_comms_ack'`, 8+7+1 `TypeError: comms() got an unexpected keyword argument 'grade'/'to'/'peek'`, 3+1+1 `KeyError: 'send'/'drain'/'ack'`, 1 `ValueError: unknown comms action 'ack'`, 2 `AssertionError: … exactly ONE 'COMMS:' paragraph`. **Zero import/path errors; 850 tests still ran** — the RED is for the right reason. |
| satisfiability (C-DEF law) | reference build → `1092 passed, 12 skipped` in one run, no iteration on the contract |
| satisfiability after lint | `uv run ruff check loremaster/` → **All checks passed** on the reference build |
| probe can SEE (positive control) | every "SURVIVED" verdict is paired with a **served-surface diff** from `refbuild/observe.py`, which drives the real renders AND the real dispatcher. Two mutations that showed **no diff** (`W3` at first, `W14` at first) were **discarded and rebuilt** rather than reported. |
| probe passed for the WRONG reason (caught, self-reported) | `W2` and `W15` were "caught" — but by the **static safe_str literal classifier**, because my mutation introduced a NEW string literal (`sanitise_line("everyone")`), not by any behavioural pin. Re-run as `W2b`/`W2c`/`W15b` **without** new literals: **all three SURVIVED.** This is exactly the "rejected on a parse error, not the ASSERT" class; reporting it because it changes the verdict on those rows. |
| fakes can FAIL (P5) | 4 mutations of `_message_fakes.FakeMessageLedger` → RED every time: ignore `peek` (3 failed), ignore `limit` (7), never mark `question` (16), never stamp an ack (10). **The fakes are not decoration.** ⚠ But all 16 `question` failures are in `test_message_ledger.py` and **zero in the surface contract** — the surface never checks that `question` reaches the render through the dispatcher (→ W29). |

Reference build, mutation driver, observation harness and result logs live at
`/home/ejprice/scratch/adv03b/refbuild/` (scratch — deliberately not a citable address;
every claim below is reproducible from the recipe in this report).

---

## 2 — P1b THE QUANTIFIER TABLE

`∀` = the invariant is pinned over the transform's inputs. `GUARDED` = pinned only where a
fixture value, a monoculture, or an unreachable branch keeps the bad outcome away. **Every
GUARDED row carries a door-build receipt: either a surviving wrong build (a finding) or the
pin that killed the door.**

### S4.1 — send

| # | invariant | class | receipt |
|---|---|---|---|
| I1 | the receipt's `{seq}`/`{grade}` slots are the message's | **GUARDED** (no pin reads them) | **W22 SURVIVED** (`seq+1`), **W23 SURVIVED** (grade slot fed `message.session`) |
| I2 | recipient list capped at `_COVERAGE_NAMES_CAP`, true remainder | ∀ over cap−/at/over, derived from the constant | door `W44` (show 1 name) **CAUGHT** by both cap pins ✅ |
| I2b | …and it shows the FIRST cap names | **GUARDED** (pin counts, never identifies) | **W42 SURVIVED** (tail slice `[-cap:]`) |
| I3 | the broadcast receipt variant | **UNREACHABLE** — every call site passes `broadcast=False` | **W3, W2b, W2c, W33 all SURVIVED** |
| I4 | directive trailer IFF `grade == 'directive'` | ∀ over the question×grade 2×2 | door `W20` (wrong seq in trailer) **CAUGHT** by the proof marker ✅ |
| I5 | question teach IFF `message.question` | ∀ **at the render**; **GUARDED at the dispatcher** | **W29 SURVIVED** — `set_status` dropped in `_comms_send` ⇒ no production message is ever a question |
| I6 | the question line names the MESSAGE's thread | ∀ (thread ≠ session fixture, both directions) | no door found ✅ |

### S4.2 — drain

| # | invariant | class | receipt |
|---|---|---|---|
| I7 | header variant = peek vs stamping | ∀ | door `W21` (flag inverted) **CAUGHT** (4 pins) ✅ |
| I8 | the header's `{shown}`/`{total}` are honest | **GUARDED — no pin reads either number** | **W4 SURVIVED** (`drained 2 of 2` while 7 pend), **W5 SURVIVED** (same on peek) |
| I9 | the context cell: precedence, singularity, `thread != session` | ∀ — the strongest family in the contract (pair pin, literal-vs-argument pin, task-on-session-thread pin) | doors `W24`/`W30` **CAUGHT** ✅ |
| I9b | the row's `{grade}`/`{sender}` slots | **GUARDED** (no pin reads them) | **W24b SURVIVED** (grade↔sender swapped: `#61 [lead] signal→you:`) |
| I10 | rows render in the ledger's order | **GUARDED** (pins locate rows by seq, never by position) | **W25 SURVIVED** (rows reversed) |
| I11 | the refs row variant | **UNREACHABLE** — no fixture in the tree sets `refs` non-empty | **W7 SURVIVED** (refs dropped entirely) |
| I12 | ACK REQUIRED IFF ≥1 served **unacked directive** | `acked_at` half ∀ (amendment R3); **grade half GUARDED** — every trailer fixture is directive-only or a lone signal | **W41 SURVIVED**: demand list is grade-blind (lists an unacked SIGNAL alongside the directive) |
| I13 | …and its taught command is runnable | **GUARDED** — the proof marker stops at `ACK REQUIRED: #71` | **W6 SURVIVED**: `ACK REQUIRED: #71, #72 — lore_comms action=ack seqs=[]` |
| I14 | ALREADY ACKED IFF ≥1 served acked row, only those | ∀ (grade varied: signal + directive; partition pin) | door `W26` (list every row) **CAUGHT** ✅ |
| I15 | elision `next_limit == more`, not `shown+more` | ∀ within the branch (5 vs 7 vs 2 all separated) | no door found ✅ |
| I16 | peek serves no trailers / no elision | ∀, each with its own positive control | no door found ✅ |
| I17 | block order header · rows · trailers · elision | **UNPINNED** | **W8 SURVIVED** (trailers + elision above the rows) |
| I18 | empty ⇒ `no unread messages` | ∀ via the convergence test | ✅ |
| I19 | window = caller's `limit`, else `comms.drain_limit` | config half ∀; **caller half GUARDED** — no dispatcher call ever passes `limit=` | **W9 SURVIVED** (caller's `limit` deleted) |

### S4.3 — ack

| # | invariant | class | receipt |
|---|---|---|---|
| I20 | four group lines in FIXED order | **UNPINNED** | **W13 SURVIVED** (order reversed) |
| I21 | seqs in REQUEST order, not re-sorted | **UNPINNED** | **W14 SURVIVED** (`#9, #3` → `#3, #9`) |
| I22 | `acked {acked} of {requested}` are the true counts | **UNPINNED** | **W11 SURVIVED** (`acked 0 of 0: #5`) |
| I23 | already-acked is a DISTINCT group from acked | **UNPINNED** | **W12 SURVIVED** (folded: `acked 1 of 4: #5, #4`) |
| I24 | "no delivery to `{name}`" names the CALLER | **GUARDED** — the only driver hands the render `agent_name` directly | **W15b SURVIVED** (handler passes `agent_row.session`: *"…no delivery to wave7"*) |
| I25 | unknown-seq teach IFF ≥1 unknown seq | ∀ (no-emit leg is the NEIGHBOURING cause, not a success) | ✅ |
| I26 | the handler CALLS `_render_comms_ack` at all | **UNPINNED** | **W10 SURVIVED — BLOCKER** |
| I27 | `note=` reaches the ledger | **UNPINNED** | **W27 SURVIVED** (note dropped; edge stores `None`) |

### S5 — the served instructions

| # | invariant | class | receipt |
|---|---|---|---|
| I28 | every `action=` token names a real action | ∀, derived from the dispatch tables | ✅ strong |
| I29 | the COMMS paragraph teaches only comms verbs | ∀ | ✅ |
| I30 | it teaches send/drain/ack | pinned (set containment) | ✅ |
| I31/I32 | thread-debt + self-answer clauses present | substring-pinned | ✅ |
| I33 | **every other ruled claim** — body cap, grade semantics, `to=[]`, peek semantics, re-ask recovery | **UNPINNED** | **W16, W17, W18, W19 all SURVIVED** |

### Cross-cutting (dispatcher ⇄ render ⇄ ledger)

| # | invariant | class | receipt |
|---|---|---|---|
| I34 | the dispatcher hands the drain render the right session | ∀ (wiring pin + literal-vs-argument pin) | door `W30` **CAUGHT** ✅ — the model for what the other two verbs need |
| I35 | the handlers CALL their renders | drain ✅ pinned; **send/ack UNPINNED** | **W1 + W10 SURVIVED — BLOCKER ×2** |
| I36 | send forwards `task_id`/`refs`/`set_status` | **UNPINNED** (`thread` is pinned, via I34's fixture) | **W28 SURVIVED**, **W29 SURVIVED** |
| I37 | recipient resolution is scoped to the caller's session | broadcast-vs-fleet ∀ (`W40` **CAUGHT**); **scope SOURCE GUARDED** — all 13 sends pass `session=` | **W32 SURVIVED**: with `session` omitted (legal), a broadcast crosses into `wave9` |
| I38 | `to=[]` ⇒ broadcast (S5 teaches it verbatim) | **UNPINNED** — no call site passes `to=[]` | **W31 SURVIVED**: `to=[]` raises `EmptyRecipientSetError` |
| I39 | hostile-input sanitisation | ∀ over the corpus for `send.recipients/sender/thread`, `drain.body/sender/thread`, `ack.name`, with two non-vacuity classes | ✅ strong. Residual: no RenderCase for `drain.task_id` or `drain.refs` (§5 R4) |

**Score: 20 ∀ · 19 GUARDED/UNREACHABLE/UNPINNED, every one of the 19 with a surviving door-build.**

---

## 3 — MISSING PINS (each: the test to write · the defect it catches)

### BLOCKER

**B1 — `TestDrainAndAckAtTheDispatcher::test_the_SEND_dispatcher_serves_the_SEND_RENDER`.**
Send through the real dispatcher (`to=["fixer-b"]`, `grade="directive"`,
`set_status="input_required"`, `thread="q:cap"`) and assert the returned text carries the
receipt line, the ack trailer AND the question line.
*Catches:* **W1** — `_render_comms_send` built perfectly and **never called**. Survives
1092/1092 today.
```
--- DISPATCHER send (reference) ---            --- W1 ---
sent #1 [directive] → fixer-b                  no unread messages
recipients must ack: lore_comms action=ack seqs=[1]
awaiting an answer on thread 'q:cap' — …
```
This is the #94 shape verbatim: *"every pin tested a new method nothing required the code to
CALL."* The drain has `test_the_dispatcher_HANDS_THE_RENDER_A_SESSION_and_it_is_the_right_one`;
send and ack have no equivalent.

**B2 — `TestDrainAndAckAtTheDispatcher::test_the_ACK_dispatcher_serves_the_ACK_RENDER`.**
Ack a real seq, then ack it again together with an unknown seq; assert
`acked 1 of 1: #1`, then `already acked: #1 — no new stamp` **and** the unknown-seq teach.
*Catches:* **W10** (render never called), and en route **W11/W12/W13/W14/W15b**.

### CRITICAL

**C1 — `TestRenderCommsDrainShape::test_the_header_names_the_TRUE_pending_total`.**
Assert the first line is exactly `drained 2 of 7 pending` on the existing 2-shown/7-pending
fixture, and `peeked 2 of 7 pending…` on its peek twin.
*Catches:* **W4/W5** — `drained 2 of 2 pending` while five messages wait. The peek variant is
worse: S4.2 lets a peek skip the elision line **because** "its header already discloses
`shown of total`" — a lying header removes the only disclosure a peek has.
(Perturbation proven in §4: GREEN on reference, RED on W4/W5.)

**C2 — `TestRenderCommsDrainShape::test_an_unacked_SIGNAL_is_not_demanded`.**
One unacked signal + one unacked directive in one drain; the demand names the directive only.
*Catches:* **W41.** Amendment R3 closed the `acked_at` monoculture on this trailer and left the
**grade** monoculture untouched — every ACK-REQUIRED fixture in the tree is directive-only or
a lone signal. Residual 3 of the design doc predicted the adversary would "confirm the fix
wave"; the fix closed one axis of a two-axis predicate.

**C3 — `TestRenderCommsDrainShape::test_the_ACK_REQUIRED_command_is_RUNNABLE`.**
Split the trailer at `action=ack ` and assert the taught command names every demanded seq.
*Catches:* **W6** — `ACK REQUIRED: #71, #72 — lore_comms action=ack seqs=[]`. The registered
promise's own predicate says "ack runs for any delivery edge addressed to the caller"; §9.7's
litmus is *"if the reader ran the taught command WITH ITS DEFAULTS, would the promised thing
happen?"* With `seqs=[]` it does not. The proof marker `"ACK REQUIRED: #71"` stops one
character before the part that has to be true.

**C4 — `TestRenderCommsSendShape::test_a_BROADCAST_receipt_names_the_true_fan_out_and_the_session`.**
Drive `_render_comms_send(..., broadcast=True, session="wave7")` with 3 recipients and a
non-session thread; assert `sent #41 [signal] → broadcast: 3 agents in session wave7`.
*Catches:* **W2b** (`…broadcast: 1 agents…`), **W2c** (`…in session q:cap`), **W3** (handler
hardcodes `broadcast=False`). **`broadcast=True` is a parameter-value MONOCULTURE: not one
call site in the contract sets it** — the repo's own #96 law, on a boolean.

**C5 — `TestRenderCommsSendShape::test_the_question_teach_survives_a_BROADCAST`.**
Same call with `question=True`.
*Catches:* **W33** — an agent that asks the whole fleet is never told how its debt clears.

**C6 — `TestDrainAndAckAtTheDispatcher::test_send_forwards_set_status_task_id_and_refs`.**
Send with all three set; assert the question line appears in the send render AND the next
drain row shows `(task T-9)` and `(REPORT-x.md)`.
*Catches:* **W28** and **W29.** W29 is the sharper one: with `set_status` dropped, **no
message in production is ever a question**, so S4.1's whole question-teach line — the packet's
headline addition — is unreachable through the real path while its render-level 2×2 stays
green. The P5 fake-mutation receipt makes this exact: breaking `question` in the fake reddens
**16 tests, all of them in `test_message_ledger.py`, none in the surface contract.**

**C7 — `TestTheServedInstructionsTeachCommsMechanismsThatEXIST::test_the_body_cap_is_DERIVED_from_the_constant`.**
Assert `f"cap at {MESSAGE_BODY_MAX_CHARS} chars"` (or a regex-extracted integer equal to it)
appears in the COMMS paragraph.
*Catches:* **W16** — the served text says **20000** while the ledger rejects at 2000. This is
`CLAUDE.md`'s #104 clause verbatim: *"prose that describes behaviour must be DERIVED from the
behaviour, not re-stated beside it"* — and the number is right there as an importable constant.

**C8 — `…::test_the_grade_and_peek_semantics_taught_are_the_ones_IMPLEMENTED`.**
Assert the ordered claims: `"grade=signal is fire-and-forget"` before
`"grade=directive demands an ack"`; `"stamps what it serves as seen"` and
`"peek=true looks without stamping"`.
*Catches:* **W17** (peek inverted — teaches an agent that a plain drain does not stamp, i.e.
to re-read the same inbox forever) and **W19** (grade inverted). S5 rules this paragraph
**VERBATIM**; the contract pins 2 substrings of ~7 claims, so five ruled claims may be freely
rewritten. A whole-paragraph byte-exact pin against a module-level ruled constant would close
C7+C8+W18 in one line.

**C9 — `TestBroadcastFanOut::test_a_broadcast_with_session_OMITTED_stays_in_the_callers_session`.**
Register `lead`+`fixer-b` in `wave7` and `outsider` in `wave9`; broadcast **without**
`session=`; assert `outsider` receives nothing.
*Catches:* **W32.** `session` is optional on every non-register action, and all 13 sends in the
contract pass it — a build scoping the roster by the nullable parameter delivers `wave7`'s
traffic into `wave9`. Measured: recipients `['fixer-b']` → `['fixer-b', 'outsider']`.

### MAJOR

**M1 — `test_to_EMPTY_LIST_is_a_broadcast`** (dispatcher, `to=[]`). *Catches* **W31**: `to=[]`
raises `EmptyRecipientSetError` while the served instructions teach it as the broadcast form.
`to=[]` appears in this contract **only inside a docstring**.

**M2 — `test_the_drain_serves_its_rows_in_LEDGER_order`** (assert `#61` before `#62` by index,
not by presence). *Catches* **W25**.

**M3 — `test_every_served_row_renders_ABOVE_the_first_trailer`.** *Catches* **W8** (S4.2's
ruled composition). Perturbation proven in §4.

**M4 — `test_a_row_with_REFS_renders_them`** — the refs variant is live only as a *static*
literal (`test_no_dead_registry_entries`); nothing renders it. *Catches* **W7**.

**M5 — `test_the_row_names_the_GRADE_and_the_SENDER_in_the_right_slots`** (one fixture where
grade and sender are not confusable). *Catches* **W24b**.

**M6 — `test_drain_honours_an_EXPLICIT_limit_at_the_dispatcher`** (`action="drain", limit=1`
with 3 pending). *Catches* **W9**; `limit` is a declared `drain` param that no test exercises.

**M7 — `test_the_send_receipt_names_the_MESSAGES_seq_and_grade`.** *Catches* **W22/W23** — and
the seq matters twice over, since the directive trailer tells recipients to ack it.

**M8 — `test_ack_forwards_the_NOTE`** (assert the note lands on the winning edge). *Catches*
**W27.** S4.3 records "note= is accepted and stored … recorded as deliberate, not forgotten" —
storage is asserted nowhere at the surface.

### MINOR

**m1** `test_the_capped_recipient_list_shows_the_FIRST_names` — *catches* **W42** (tail slice).
**m2** `TestC1RenderInjectionBattery` has no `drain.task_id` / `drain.refs` RenderCase; both are
caller-controlled free text entering a row. The `SafeLine`/`safe_str` seam makes an
unsanitised build hard to write, so this is defence-in-depth, not a live hole — but the
battery's completeness pin is per-ACTION, so it cannot notice.
**m3** `test_description_names_every_action` passes for `"ack"` **vacuously** — `"ack"` is a
substring of `"brief_ack"`, already in the shipped description. Only `send`/`drain` are real
checks. Use word boundaries or `action='ack'`.
**m4** `_render_comms_drain`'s `agent_name` **and** `limit` are consumed by no ruled line
(`next_limit = more`; no drain line names the reader). The ruled signature obliges a builder to
accept two parameters it must not use. Either a line is missing from S4.2 or the signature is
wider than the ruling — an escalation, not something I should settle.
**m5** `TestRenderCommsSendShape` uses `_drain_line_containing` — a helper whose name, message
and docstring are all about drains. Cosmetic, but its failure message will mislead.
**m6** `test_the_recipient_list_shares_ONE_display_cap…` computes `shown` by substring
membership; with `agent-00 … agent-06` no two names are substrings of each other today, but a
fixture rename (`agent-1`, `agent-11`) would silently double-count. Prefer exact split.

---

## 4 — P2 fixture-discrimination: perturbations WITH their correct-build control

Five perturbed copies of committed pins, in the scratch tree only
(`loremaster/tests/test_ADVERSARY_perturbations.py`, deleted after use). **Both legs shown, as
required — without the control leg a perturbation may just be botched expected values.**

```
LEG 1 (control) — perturbed pins on the CORRECT reference build:
    5 passed in 0.60s

LEG 2 (discrimination) — the same 5 pins on each wrong build:
  W41_ack_demand_is_grade_blind      -> 1 failed, 4 passed   (P2a only)
  W4_drain_header_total_is_shown     -> 1 failed, 4 passed   (P2b stamping only)
  W5_peek_header_total_is_shown      -> 1 failed, 4 passed   (P2b peek only)
  W6_ack_required_command_is_empty   -> 1 failed, 4 passed   (P2c only)
  W8_block_order_inverted            -> 1 failed, 4 passed   (P2d only)
```

Each perturbed pin fires on **exactly** its target and stays green on the other four — so the
discrimination is the perturbation's, not a blanket sensitivity.

**Fixture-discrimination verdicts, individually:**

| fixture / pin | verdict |
|---|---|
| `test_the_ack_demand_lists_ONLY_the_UNACKED_directives` (71 directive + 82 acked directive) | **cannot discriminate on GRADE** — both rows are directives. Perturbation: make one an unacked signal ⇒ RED on W41, GREEN on reference. |
| `test_the_elision_re_ask_is_the_REMAINDER…` (2 shown / 7 pending, limit 2) | **discriminates the elision**; **blind to the header** it never reads. Perturbation: assert the header ⇒ RED on W4, GREEN on reference. *(Note: `next_limit = more` and `total − limit` are indistinguishable here, but they are indistinguishable in reality too — `shown == limit` whenever an elision exists. Not a finding.)* |
| ACK-REQUIRED promise proof, marker `"ACK REQUIRED: #71"` | **stops before the taught command.** Perturbation: assert the command ⇒ RED on W6. |
| `TestRenderCommsDrainShape` context-cell family | **strongest family in the contract.** The pair pin + the `session="wave9"` monoculture killer + the task-on-session-thread pin defeated every door I built. No perturbation weakened it. |
| every `_render_comms_send(...)` call site (`broadcast=False`, 100%) | **boolean MONOCULTURE** — the whole broadcast branch is untested. W3/W2b/W2c/W33. |
| every dispatcher `send` call (`session="wave7"`, 13/13) | **value monoculture** — masks W32's cross-session leak. |
| `_inbox_entry(refs=…)` / `_message(refs=…)` | **never called with refs** anywhere in the tree ⇒ the refs row variant is unreachable (W7). |
| `_ack_result()`'s default (`outcome="acked"`) | **dead fixture code** — the only ack-render driver in `test_comms_tool.py` passes explicit `not_addressed` entries. Symptom of S4.3 being unpinned. |
| small-N (`len()` ≡ `sum()`) | checked and **NOT present** in this surface: `acked {acked} of {requested}` is the only count pair, and it is unpinned outright (W11) rather than pinned at a degenerate N. |
| arithmetic alignment | checked: the elision fixture separates `more`(5) / `shown+more`(7) / `limit`(2) cleanly, and both cap fixtures derive from `_COVERAGE_NAMES_CAP`. **No alignment hazard found.** |

---

## 5 — P6 corpse sweep · P6b removed-behaviour · residuals (individual verdicts)

**P6 (corpses — assertions still pinning retired behaviour).** 03b is **additive**: it widens
`_COMMS_ACTIONS` 6→9, adds three renders, and appends a paragraph to `_INSTRUCTIONS` (S5
explicitly keeps the MEMORY paragraph's `lore_comms` sentence). Sweep result, with the receipt:
**the full suite against my reference build shows ZERO failures in any pre-existing suite** —
`36 failed, 6343 passed, 15 skipped, 3 xfailed` where **all 36 are `test_trace_telemetry.py`**
(the S6v2 telemetry contract, deliberately RED and outside my three files). Individually
checked and **clean**: `TestCommsActionsTable::_EXPECTED_ACTIONS` already carries all nine
verbs; `test_description_names_every_action` derives from the table; `test_mcp_server.py`'s
instructions pins do not fix the paragraph count. **No corpse found.**

**P6b (orphaned virtues of deleted/replaced code).** **Not applicable, stated rather than
assumed:** 03b deletes and replaces nothing. I enumerated the diff surface from source first —
`_COMMS_ACTIONS` (widened, no entry removed), `_INSTRUCTIONS` (appended, no paragraph
rewritten), `CommsConfig` (field added), `AppContext.__init__` (parameter added). The design
doc's own retirements (S6v2's `comms_calls` counter, v1's drain-render telemetry notice) are
retirements of **never-built v1 design items**, not of shipped code, so there is no
removed-behaviour inventory to diff against. If the lead believes a Phase 0 inventory exists
for 03b, it was not named in my brief and I did not find one.

**Residuals, each with its own verdict:**

- **R1 — `test_surreal_harness.py` is RED at HEAD `45cc161`, in the pristine repo.**
  `TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts`:
  *"the harness docstring says 35 test files import it; 36 actually do."* The 36th is
  `test_trace_telemetry.py`, added by **`a774c8f` ("test(03b): the all-tools trace telemetry
  contract")** — the 03b wave broke a committed derived-count pin and it went unnoticed because
  the wave runs only the three comms files. **Verdict: live defect, escalate.** One-line fix in
  `_surreal_harness.py`'s docstring (35 → 36); the pin is doing exactly its job.
- **R2 — design-doc Residual 8's mypy number is wrong and its scope claim is false.** It says
  "Global mypy-zero (36→0) is structural: the errors are the RED contract's forward refs to
  `_render_comms_*`/`comms(...)` kwargs; building S4's surface pays them." Measured at HEAD:
  **58 errors in 3 files**, and **6 of them are `test_trace_telemetry.py`'s
  `record_trace(caller=…)`**, which S4/S5 does **not** pay — after my full reference build,
  `scripts/typecheck.sh` still reports `Found 6 errors in 1 file`. **Verdict: an inherited
  number that was not re-derived; the S4/S5 builder will not reach mypy-zero and must be told
  so, or the two builds must land together.**
- **R3 — the `[real]` legs of inherited delta row 8** are flagged by the contract author as
  belonging in `test_message_ledger.py` (frozen). **Verdict: agreed, unresolved, still owed.**
- **R4 — injection battery coverage is per-ACTION, not per-FIELD.** `drain.task_id` and
  `drain.refs` are caller-controlled free text with no RenderCase (§3 m2). **Verdict: minor —
  the `SafeLine` type discipline makes an unsanitised build awkward to write, but the
  completeness pin cannot see the gap and says so nowhere.**
- **R5 — `_render_comms_drain`'s `agent_name`/`limit` are dead parameters** under the ruled
  shapes (§3 m4). **Verdict: escalate to the design sidecar — this is a spec question (is a
  line missing, or is the signature wide?), not a builder's call.**
- **R6 — the two "caught for the wrong reason" probes are a warning about the static
  classifiers.** `_SAFE_STR_PROMISE_FREE` / `_PROMISE_FREE` catch a *new literal*, never a
  *wrong value*. Every mutation I wrote that reused existing literals sailed through them.
  **Verdict: not a defect — but the promise registry must not be counted as behavioural
  coverage, and several of the survivors above would look "covered" if it were.**
- **R7 — `test_registered_iff_proven` + `test_no_dead_registry_entries` are STATIC liveness
  only.** `already acked: {seqs} — no new stamp`, `acked {acked} of {requested}: {seqs}`,
  `not addressed to you: …`, `sent … → broadcast: …`, and the refs row variant are all "live"
  purely because the literal appears in `server.py`. **Verdict: this is why W7/W10/W12/W13
  survive — the promise-free set has no emit proof, by design. Flagging so the gap is
  deliberate rather than assumed.**
- **R8 — no probe touched production `:18500`.** All runs used the scratch tree's fakes and
  `ws://127.0.0.1:18000` per the test config. **Verdict: clean.**
- **R9 — the spec moved under me, mid-grade (disclosed, not silently absorbed).** The repo was
  clean at spawn; at write-up `git status` showed `docs/plans/v2/03b-comms-surface-design-rulings.md`
  **modified by another agent** (+53/−1). Hunks: `@@ -460 +460,21 @@` (S7's caller-key mint —
  a "WB9 CORRECTION" conceding the attack table's no-collision row was unenforced prose) and
  `@@ -539,0 +560,32 @@` (an E3 revisit). **Both are S6v2/S7 TELEMETRY territory; §S1–S5 and
  §S8's D2/D3/D10 — everything I graded — are byte-unchanged.** My verdict therefore stands
  against the spec as briefed. **Verdict: no impact on this grade; flagged because a spec that
  changes during its own adversary pass is a coordination hazard, and because I did not and
  will not touch that file.**

---

## 6 — Reproduction recipe

```bash
./scripts/scratch_copy.sh /abs/scratch/adv03b            # asserts provenance, prints it
# 1. RED baseline               -> 242 failed, 850 passed, 12 skipped
# 2. build S4.1/S4.2/S4.3/S5 per the design rulings (renders + 3 handlers +
#    _COMMS_ACTIONS entries + comms() kwargs + tool params + CommsConfig.drain_limit
#    + AppContext.message_ledger + the S5 paragraph verbatim)
# 3. satisfiability             -> 1092 passed, 12 skipped, 0 failed
# 4. per mutation: patch, run the three files, diff the served surface vs reference
uv run pytest -n auto -q loremaster/tests/test_comms_tool.py \
    loremaster/tests/test_comms_promise_registry.py loremaster/tests/test_message_ledger.py
```

Mutation W-numbers in this report map 1:1 to entries in the scratch driver; each is a single
`(old, new)` replacement against the reference `server.py`, so any of them is reconstructible
from the description alone.

---

## VERDICT: **CONTRACT INSUFFICIENT**

The contract's context-cell family (S4.2 branch 3, amendment 10 / D2) and its peek/elision
rules are genuinely excellent — I built five doors at them and every one was killed, and the
`session="wave9"` monoculture killer is the best pin in the file. The `acked_at` discrimination
that amendment R3 added is real. The injection battery with its two non-vacuity classes is
real. The satisfiability receipt held on the first run, which is rarer than it sounds.

But **32 of 41 wrong builds pass it with zero failures**, and two of them are the no-op fix:
a builder can ship `_render_comms_send` and `_render_comms_ack` exactly as ruled and **wire
neither of them up**. The pattern under almost every survivor is the same one the drain got
right and the other two verbs did not — *the contract pins the RENDER as a function and the
LEDGER as a module, and pins the seam between them for exactly one verb.* Add B1/B2 and the
nine CRITICAL pins and most of the rest of the list closes with them.
