brief-base v6 read

# REPORT — contract-r2 · packet 03a-2 final wave: R2 (design ruling) + S1/S3 (audit residuals)

*(Everything below MEASURED 2026-07-23 on this box, against commit `50d65a0` plus the two
files this report changes. Store: `spike-surreal ws://127.0.0.1:18000`; `:18500` NEVER touched.
Claims are dated where they are made, never "currently".)*

## SUMMARY BLOCK

- **State: done.** Contract is RED **only** on the two new R2 `[real]` legs — the builder's target.
  S1 and S3 are GREEN against the shipped code (no latent defect behind either).
- **Gate receipts.**
  `test_message_ledger.py -n auto -q` → **`2 failed, 178 passed, 12 skipped`** (baseline at
  `50d65a0` re-measured by me: **`176 passed, 12 skipped`**) ·
  `test_retry_seam.py -n auto -q` → **`503 passed, 1 warning`** ·
  `./scripts/typecheck.sh` → **`Found 36 errors in 3 files (checked 148 source files)`**, unchanged,
  ZERO in any production module · `uv run ruff check .` → **`All checks passed!`**
- **SATISFIABILITY RECEIPT (§3).** With the one-conjunct reference fix applied to
  `messages.py::MessageLedger.awaiting_answer`: **`180 passed, 12 skipped` — 0 failed**, plus
  ruff clean and typecheck still 36 (the harder leg: the reference build demands NO lint cleanup).
  **REVERTED and proven byte-exact:** `md5 d2aec8a1688ba63fc6916e62c432ff86` ==
  `git show 50d65a0:loremaster/loremaster/messages.py | md5sum`; `git status` shows `messages.py`
  unmodified.
- **Mutation-proof table (§4):** 4 wrong builds, each RED for the right reason, each restored
  byte-exact — oracle-conjunct-removed → both `[fake]` legs RED · R2 reference fix reverted →
  both `[real]` legs RED · peek-writes-`ack_note` → S1 RED **while every count-based drain pin
  in the file stayed GREEN** · note-written-per-edge-unscoped → S3 RED on the NEW assertion
  while the OLD one (`acked_at is None`) still passed.
- **No existing pin weakened.** Pin count **89 → 91** methods; collected **188 → 192**; `[real]`
  node ids **76 → 78**. Every deleted line is accounted for in §5 — **no assertion was loosened
  or deleted**; the one changed failure *message* sits on an unchanged assertion.
- **Oracle change turns NO existing pin red — MEASURED, not inferred (§6).** ⚠ And the designer's
  premise was incomplete: `_message_fakes.py` has **TWO** consumers, not one
  (`test_comms_tool.py` imports it too). That suite was measured at `50d65a0` and with my change:
  **`149 failed, 554 passed` BOTH times, identical.**
- **Decisions needed / flags (§7):** (1) a **new store-behaviour defect found while building a
  mutation** — `UPDATE <edge> … WHERE in IN $ids` **silently matches ZERO rows** on 3.2.1 while
  the identical `SELECT` matches; filed as **finding #175**, shipped code unaffected;
  (2) `_message_fakes.py`'s module docstring asserts a **false** blast-radius claim ("only
  `test_message_ledger.py` imports this file") — flagged, NOT edited (outside my one-conjunct
  writable scope).
- **Provenance:** no scratch copy. Every run imported
  `loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`
  and `messages.__file__ = …/loremaster/loremaster/messages.py` — the REAL tree. Every mutation
  used a `cp -a` CONTENT backup and was restored from content with md5 verification.
  **No git-state mutation of any kind** (no stash, no checkout, no reset — see §8).
- **Receipt pointers:** §1 what changed · §2 the R2 ruling as pinned · §3 satisfiability ·
  §4 mutation proofs · §5 counts + deletions · §6 no-existing-pin-red · §7 flags · §8 mutation
  safety · §9 tool honesty.

---

## 1. What changed (two files, exactly)

### 1.1 `loremaster/tests/_message_fakes.py` — the ORACLE (R2, one conjunct)

`FakeMessageLedger.awaiting_answer`'s `answered` predicate gains a third clause:

```python
answered = any(
    candidate.thread == question.thread
    and candidate.seq > question.seq
    and candidate.sender_id != agent_id          # <-- R2's fourth conjunct
    for candidate in delivered_to_me
)
```

**Placed in the `answered` predicate, not in the `delivered_to_me` comprehension** — the design
ruling (§R2 implementation step 2) expressly permits either. I chose the predicate because
production applies it at the *deliveries SELECT*, and the fake's whole reason to exist is to be an
INDEPENDENT implementation that can still FAIL a wrong build; giving it the same structural shape
as production would make it a mirror rather than an oracle.

The docstring is rewritten from "any message DELIVERED TO this agent … created after the
question" (three conjuncts) to the FOUR, naming the fourth as *sent by ANOTHER AGENT* and citing
the ruling by path, with the ruling-7 reconciliation stated in place (a self-addressed send stays
fully deliverable; it simply cannot discharge its own sender's debt).

### 1.2 `loremaster/tests/test_message_ledger.py` — three pins

| # | pin | class | job |
|---|---|---|---|
| 1 | `test_an_explicitly_SELF_ADDRESSED_message_on_the_question_thread_is_NOT_an_answer` | `TestTheWaitingStateIsDerived` | **NEW** — R2, self-only leg |
| 2 | `test_a_self_addressed_message_with_ANOTHER_recipient_is_STILL_not_an_answer` | `TestTheWaitingStateIsDerived` | **NEW** — R2, mixed-recipient `[lead, me]` leg |
| 3 | `test_peek_serves_the_same_rows_but_stamps_none` | `TestPeekStampsNothing` | **STRENGTHENED** — S1, adopts `_WriteWatch` |
| 4 | `test_acking_another_agents_edge_leaves_that_edge_UNCHANGED` | `TestAckDisambiguatesTheFourWayEmptyReturn` | **STRENGTHENED** — S3, asserts the victim's `ack_note` |

Both new pins are placed immediately after
`test_a_message_the_ASKER_sends_on_its_own_thread_is_not_an_answer` — the pin whose fixture cannot
reach the door — so the next reader meets the gap and its closure together.

---

## 2. R2 as pinned — and what each pin actually discriminates

The ruling is `docs/plans/v2/03a-2-consume-path-design-rulings.md` §R2 (design-comms, binding).
I implemented it; I did not relitigate it, and I found **no ambiguity requiring escalation** —
the ruling names the conjunct, the two legs, the oracle edit, and the ruling-7 reconciliation
explicitly.

**Pin 1 (self-only).** Asker asks on `q:cap-boundary` (recipients `[lead]`), then sends on the
same thread with `recipients=[itself]`. Asserts, in order: the self-note **WAS delivered** (ruling
7 untouched — so the pin can only fail because it is not an ANSWER, never because delivery broke),
`awaiting_answer` is still not-None, and then — **positive control inside the fixture** — an
external `_answer` on the same thread DOES clear it.

> *What wrong build still passes this?* A build that never clears at all — killed by the in-fixture
> positive control (and by `test_an_answer_on_the_thread_clears_it_…`). A build keyed on **"am I
> the only recipient"** — **passes this pin with the defect fully intact**, which is exactly why
> pin 2 exists.

**Pin 2 (mixed recipients `[lead, me]`).** Same ask; the follow-up is sent by the asker to
`[lead, me]`. Delivered-to-me holds, another agent IS on the message, sender is still me.

> *What wrong build still passes this?* One keyed on the SENDER's *name* rather than identity, or
> one comparing `sender_id` to the wrong side. A build that filters "messages I sent" out of
> **deliveries entirely** (rather than out of the ANSWER predicate) passes both — but is killed by
> `test_an_EXPLICIT_self_addressed_send_IS_delivered` and by pin 1's own delivery assertion.
> **Value monoculture watched:** the two legs differ in the recipient SET (`[me]` vs `[lead, me]`),
> which is the only value the plausible wrong builds can branch on here; the sender is `fixer-b`
> in both because that IS the property (an asker ≠ lead is already the file's default, and the
> answering party in every other fixture is `SENDER_LEAD` — the two roles never collapse).

**Error direction, recorded in both docstrings:** without the conjunct the failure is a
self-memo silently discharging its own debt — **false-NOT-waiting, the invisible direction**;
with it, the residual is an agent that self-resolved still reading "waiting" — visible beside a
fresh `heartbeat_at`. That is ruling 9's asymmetry, third application, as the ruling states.

**The corroborating prose defect is real and I read it myself:** `MessageLedger.awaiting_answer`'s
shipped docstring already promises *"(a `to` edge to it — so the asker's own follow-up on its own
thread is not an answer)"* while the code performs no such check. R2 makes the prose true rather
than weakening it. **The builder must update that docstring from "all THREE conjuncts" to FOUR** —
a fix that leaves the prose at three would ship the same false-gate class one notch down.

**S1 (pin 3).** The message *"peek stamped something"* was unqualified over a single
caller-scoped count. The `[real]` leg now wraps the peek in `_WriteWatch` — **the existing
instrument, reused, not re-implemented** (ONE IMPLEMENTATION) — with the same allowlist-the-safe
classification and the same anti-vacuity guard (`assert watch.reads` before trusting
`watch.writes == []`). The count assertion STAYS (it is backend-agnostic, so the `[fake]` leg
still discriminates a fake that stamps under peek) and its message is now honest: *"a peek stamped
the CALLER's OWN edges"*. The instrument's positive control is the existing
`test_the_write_watch_SEES_a_real_write`; the verb's own control is the existing
`test_a_non_peek_drain_after_a_peek_still_stamps`.

> *What wrong build still passes this?* One whose peek writes through a connection never obtained
> via `_ensure_connection`, or whose write is BOTH `SELECT`-shaped and content-neutral — the
> instrument's own documented bounds (`_WriteWatch` docstring; `REPORT-fixer-r1r8.md` §6 S6). I did
> **not** add the `_database_snapshot` content leg here: a peek is a hot-path read and the snapshot
> costs a full `INFO FOR DB` + per-table scan, and unlike the derivation pin the peek has a
> second, independent store-reading control right below it. **That is a judgement the lead may
> overrule in one line** (`before/after = await _database_snapshot(...)` around the same block).

**S3 (pin 4).** ⚠ **The fixture had to be changed or the new assertion would be decoration:** with
`note=None` there is nothing to leak and `ack_note is None` holds for every build. The ack now
carries `note="fixer-b only: gate re-run, 5551/0"` — deliberately NOT the string
`test_ack_note_lands_on_the_edge_the_CAS_WON` uses (value monoculture) — the victim's `ack_note`
is asserted `None`, and the acker's OWN note is asserted to have landed as the positive control.

> *What wrong build still passes this?* One that leaks the note only to an edge belonging to a
> THIRD agent not in the fixture (not reachable — the fan-out here is exactly two), or one that
> leaks it only across DIFFERENT messages (a different property, covered by
> `test_a_note_never_reaches_an_ALREADY_acked_edge` + `test_not_addressed_to_me`). Without the
> positive control, a build that discards every note would pass — which is why the control is in
> the same fixture rather than argued from a sibling pin.

---

## 3. SATISFIABILITY RECEIPT (the C-DEF class) — 0 failed against a known-correct build

The reference fix, applied by me to `messages.py::MessageLedger.awaiting_answer` — one conjunct,
exactly as the ruling's implementation step 1 specifies:

```python
f"SELECT in.thread AS thread, in.seq AS seq FROM {TO_RELATION} "
f"WHERE out = $agent AND in.sender != $agent",
```

| gate, reference build | result |
|---|---|
| `uv run pytest loremaster/tests/test_message_ledger.py -n auto -q` | **`180 passed, 12 skipped`** — **0 failed** |
| `uv run ruff check .` | `All checks passed!` |
| `./scripts/typecheck.sh` | `Found 36 errors in 3 files` — unchanged |

**The harder leg is satisfied trivially and I checked it rather than assuming:** the reference fix
orphans no import and triggers no lint demand, so there is no post-cleanup state in which the
contract stops being satisfiable.

**A FREE `[real]`-LEG RECEIPT FOR R3, worth handing the builder:** the design flagged
(`§R3(2)`, residual 4) that a traversal-field WHERE on an edge table (`in.*`) *"must be proven by
the `[real]` leg; if the engine rejects the shape, the FALLBACK is today's unbounded read"*.
**It is proven: `WHERE out = $agent AND in.sender != $agent` executes and DISCRIMINATES on
spike-surreal 3.2.1.** And the proof is two-sided rather than a single green run — had the clause
matched nothing, `test_an_answer_on_the_thread_clears_it_…` would have gone RED; had it matched
everything, the two new pins would have. Both directions held simultaneously. That settles the
`in.sender` half of R3's traversal-WHERE question; it does **not** settle `in.thread IN $threads`
or `in.seq > $min`, which are still the builder's to prove.

**Reverted, byte-exact:** `md5sum loremaster/loremaster/messages.py` →
`d2aec8a1688ba63fc6916e62c432ff86`, identical to
`git show 50d65a0:loremaster/loremaster/messages.py | md5sum`. `git status --porcelain` lists only
my two test files. **No edit remains in `messages.py`.**

---

## 4. MUTATION PROOFS — every new/strengthened pin demonstrated failing, for the right reason

| # | pin | mutation | verdict + the assertion that fired |
|---|---|---|---|
| **M1** | R2 pins, `[fake]` legs | delete `and candidate.sender_id != agent_id` from the oracle | **RED ×2** — *"the asker's own self-addressed follow-up … cleared its own debt"* / *"a self-SENT message that merely CC'd another agent cleared the sender's own debt"*. Restored, md5 `6ef51f55c62781171c8397cf2ead3958`. ⚠ In the same run `test_an_EXPLICIT_self_addressed_send_IS_delivered` stayed **GREEN both legs** — ruling 7 demonstrably independent. |
| **M2** | R2 pins, `[real]` legs | the shipped code IS the wrong build (no conjunct) → RED; reference fix applied → GREEN; reverted → RED again | **RED → GREEN → RED**, §3 |
| **M3** | S1 | inject into `drain`: `if peek and window: UPDATE to SET ack_note = 'peeked' WHERE out = $agent` | **RED** — *"a PEEK issued 1 statement(s) that are not allowlisted reads: [\"UPDATE to SET ack_note = 'peeked' WHERE out = $agent\"]"*. **The whole-file run under this mutation had exactly 3 failures** (this pin's `[real]` leg + the two R2 legs) — i.e. **every count-based drain/peek pin in the file stayed GREEN**, which is the empirical proof that the assertion S1 replaced could not see this write. |
| **M4** | S3 | make `ack` resolve the message's edges and write the note per-edge, unscoped by `out` | **RED** — *"fixer-b's ack NOTE landed on audit-c's edge ('fixer-b only: gate re-run, 5551/0') — the stamp is scoped by ownership but the note is not"*. **The `acked_at is None` assertion above it PASSED**, so the pin as it stood at `50d65a0` would have been GREEN on this build. |

All four restored from `cp -a` CONTENT backups and md5-verified (§8).

**⚠ A FAILED MUTATION ATTEMPT, REPORTED BECAUSE IT FOUND SOMETHING.** M4's *first two* forms wrote
the note with `UPDATE to SET ack_note = $note WHERE [acked_at IS NONE AND] in IN $message_ids` —
and the pin stayed **GREEN**, because that statement **silently matched zero rows**. I did not
shrug that off as a bad mutation; I probed it (§7.1). It is a real engine anomaly, and the episode
is its own small lesson: *a mutation that fails to turn a pin red is either a weak pin or a wrong
belief about the system — and you cannot tell which without probing.*

---

## 5. Counts, and every deleted line accounted for

| | at `50d65a0` | now | delta |
|---|---|---|---|
| `test_` methods in `test_message_ledger.py` | **89** | **91** | +2 |
| collected (both legs) | 188 | **192** | +4 |
| `[real]` node ids | 76 | **78** | +2 |
| `[fake]` node ids | 76 | **78** | +2 |
| `-n auto -q` result | `176 passed, 12 skipped` | **`2 failed, 178 passed, 12 skipped`** | +2 passed (the new `[fake]` legs), +2 failed (the new `[real]` legs — the builder's target) |

Arithmetic: 2 new methods × 2 params = 4 collected; the 2 `[fake]` legs pass (oracle fixed), the 2
`[real]` legs fail (production unfixed). 178 + 12 + 2 = 192. ✅ Skips unchanged at 12 — **the new
pins deliberately run on BOTH backends** (no `_is_real` skip), because the R2 property is
semantic, not store-observational.

**Deletions, exhaustively** (`git diff -- loremaster/tests/ | grep '^-'`), eight lines total:

| deleted | fate |
|---|---|
| 4 docstring lines in the fake ("An ANSWER is any message DELIVERED TO…") | **replaced by the four-conjunct docstring** — prose, not an assertion |
| `candidate.thread == … and candidate.seq > …` (the predicate line) | **replaced by the same two conjuncts plus a third** — strictly stronger |
| the one-line peek `drain(...)` call | **reformatted** into the real/fake branch — same call, same arguments |
| `assert again.total_pending == _OVER_CAP, "peek stamped something"` | **the ASSERTION IS UNCHANGED**; only the failure MESSAGE changed, from an unqualified promise to what it actually checks |
| `acked = await message_ledger.ack(agent_id=…, seqs=[seq])` | **replaced by the same call carrying `note=`** — required to make the new assertion non-vacuous (§2, S3) |

**No assertion was loosened. No assertion was deleted. No test was deleted.** Three repeated
full-file runs gave `2 failed, 178 passed, 12 skipped` each time (`pytest-randomly` is not
installed in this venv, so collection order is deterministic — saying so rather than implying I
varied it).

---

## 6. The oracle change turns NO existing pin red — measured on BOTH consumers

- `test_message_ledger.py`: at `50d65a0`, `176 passed, 12 skipped`. Now, the ONLY failures are the
  two pins that did not exist before. Every previously-passing node still passes.
- **⚠ The designer's premise was that this file has one consumer. It has two.**
  `grep -rn "_message_fakes" --include=*.py loremaster/` returns `test_comms_tool.py:127` as well
  as `test_message_ledger.py:163`. So "verified against `_answer` and every
  `TestTheWaitingStateIsDerived` fixture" was a necessary but INCOMPLETE check.
  I measured the second consumer both ways, restoring the two files to their `50d65a0` content
  (`git show … > file`, a working-tree write — **not** a git-state operation) and back:

  | `test_comms_tool.py -n auto -q` | result |
  |---|---|
  | at `50d65a0` (my files reverted by content) | `149 failed, 554 passed` |
  | with my oracle + pins | `149 failed, 554 passed` |

  **Identical.** Those 149 are the pre-existing packet-03b RED contract, not my change. Files
  restored and md5-verified afterwards (§8).
- I also re-read every `awaiting_answer` fixture in the file myself rather than trusting the
  ruling's note: `_answer`'s sender is `SENDER_LEAD` unconditionally, and the only other message
  ever delivered to a waiting asker comes from `SENDER_LEAD`. The asker is `AGENT_FIXER_B` in
  every case (`_ask`'s default; the one explicit `asker=` passes `AGENT_FIXER_B` too). Sender and
  waiter never coincide in any pre-existing fixture — **which is precisely the monoculture that
  hid the defect.**

---

## 7. FLAGS — everything I noticed (I do not decide scope)

### 7.1 NEW STORE DEFECT — `UPDATE <edge> … WHERE in IN $ids` is a SILENT NO-OP. Filed as **finding #175**.

[PROBED 2026-07-23, spike-surreal `ws://127.0.0.1:18000`, surrealdb-3.2.1] One `message` row, two
`message->to->agent` edges. `$message_ids` = the one message's `RecordID`, in a list.

| statement | matched |
|---|---|
| `UPDATE to SET ack_note='A' WHERE in IN $message_ids` | **0 — silent no-op, no error** |
| `UPDATE to SET ack_note='B' WHERE meta::id(in) IN $bare` | 2 |
| `UPDATE to SET ack_note='C' WHERE in = $one` | 2 |
| `UPDATE to SET ack_note='D' WHERE out = $agent AND in IN $message_ids` | 1 |
| `UPDATE to SET ack_note='E' WHERE true` | 2 *(control)* |
| **`SELECT out FROM to WHERE in IN $message_ids`** *(same predicate, different verb)* | **2** |

The control legs matter: the predicate is correct, the rows are reachable, the binding is right,
and the instrument can see writes — only the `UPDATE … WHERE in IN $list` **form** declines to
match, silently. Mechanism **UNVERIFIED**; the hypothesis I did *not* probe is an index-backed
iterator over `to_in_out` `UNIQUE(in, out)` mishandling an `IN`-list on the leading column
(consistent with the 3.2 release-note COUNT fix in store reference §0 — itself unverified by us).
**Do not repeat the hypothesis as fact.**

**Shipped code is NOT affected** (checked at `50d65a0`): every `in IN $message_ids` UPDATE in
`messages.py` also carries `out = $agent` — the ack CAS and drain's stamp — i.e. the working row.
**The hazard is future code**: any edge-maintenance write scoped by message alone (a retract, a
redact, a GC sweep, "mark every delivery of message X") will report success and do nothing.
**Recommended disposition (lead's call):** re-probe with the UNIQUE index dropped to confirm or
refute the mechanism, then land the confirmed fact in
`docs/reference/surrealdb-31-capabilities.md` §2 (DML idioms) beside the existing
`UPDATE`-of-an-edge-endpoint silent no-op, and §6.6 (claims for which we are the only source).

### 7.2 `_message_fakes.py`'s module docstring makes a FALSE claim — flagged, not edited

Its header states: *"Living in its own module makes the regression STRUCTURALLY IMPOSSIBLE rather
than merely remembered: **only `test_message_ledger.py` imports this file**, so the blast radius of
the not-yet-existing module is the one new contract file."* **False at `50d65a0`** —
`test_comms_tool.py:127` imports it too (lazily, in a `_msg_fakes()`-style call-time helper, which
is why the uncollectable-module regression it describes is still averted; the *structural*
argument is what has decayed, not the safety).

This is the repo's own natural-language-surface class: prose asserting a property no gate checks,
in the very file whose docstring exists to teach that class. **I did not fix it** — my writable
scope in this file is the ONE oracle conjunct (brief), and a docstring rewrite is a separate
concern. The exact edit I would make: replace *"only `test_message_ledger.py` imports this file,
so the blast radius … is the one new contract file"* with *"its consumers are exactly the packet-03
contract files (`test_message_ledger.py`, `test_comms_tool.py`) — never the shared
`_comms_fakes.py` seam, so a not-yet-existing `loremaster.messages` can never take an unrelated
suite down with it."*

### 7.3 The builder must fix the production docstring too (R2's other half)

`MessageLedger.awaiting_answer`'s docstring says *"all THREE conjuncts"* and already promises the
fourth's effect parenthetically. The ruling's implementation step 1 requires both the WHERE clause
AND the docstring. **Nothing in my contract can catch a docstring that stays at three** — no gate
checks served prose. Naming it here so it cannot be lost.

### 7.4 S2 confirmed out of scope, untouched

`TestDrainStampsExactlyWhatItServed::test_over_cap_drain_serves_the_cap_and_stamps_only_the_cap`
is unchanged, per the brief. I re-read its sibling
`test_the_elided_remainder_is_still_unread_on_the_next_drain` and confirm it does read the store
back, so the CLASS is covered even though that pin's message over-promises.

### 7.5 Unrelated failing tests

`test_comms_tool.py` fails **149** tests at `50d65a0` and with my change alike (§6) — the
packet-03b RED contract, not touched by this wave. Flagged rather than buried.

---

## 8. Mutation safety

- Tree COMMITTED at `50d65a0`. **No git-state mutation of any kind**: no `stash`, no
  `checkout --`, no `reset`, no `add`, no commit. The only git invocations were reads
  (`git show`, `git status`, `git diff`, `git log`).
- **No scratch copy** (`scripts/scratch_copy.sh` not needed — nothing ran outside the real tree).
  Every run's provenance printed and checked:
  `loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`,
  `messages.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/messages.py`.
- Every mutation ran against a `cp -a` CONTENT backup at `/tmp/contract-r2-backup/`, restored
  **from content**, md5-verified after each leg:

  | file | md5 now | matches |
  |---|---|---|
  | `loremaster/loremaster/messages.py` | `d2aec8a1688ba63fc6916e62c432ff86` | `git show 50d65a0:…` ✅ (untouched at HEAD) |
  | `loremaster/tests/_message_fakes.py` | `6ef51f55c62781171c8397cf2ead3958` | my intended one-conjunct + docstring change |
  | `loremaster/tests/test_message_ledger.py` | `33b2237f7c898dbd32b5fb6509be5b92` | my intended three-pin change |

- Final `git status --porcelain`: only `M loremaster/tests/_message_fakes.py`,
  `M loremaster/tests/test_message_ledger.py`, plus the four pre-existing untracked `REPORT-*.md`
  and this report. **No commits, no deploy, `:18500` never contacted.**

---

## 9. Tool honesty (brief-base §4, CLAUDE.md dogfood protocol)

lore's tools were loaded in ONE `ToolSearch` call as briefed, and used **freshness-first**:
`lore_index()` confirmed the watched root is `/workspace` on `feat/surreal-unification` at
`50d65a0` — my own tree, last sweep 10 minutes old and *before* any edit of mine — so graph
answers were trustworthy for the pre-edit consumer question. `lore_impact` was then run on both
`MessageLedger.awaiting_answer` and `FakeMessageLedger.awaiting_answer`.

**I fell back to grep, and here is why — it caught something the graph did not.** Both `impact`
calls returned the SAME profile (0 prod / 18 test refs) with an explicit self-reported caveat:
*"this profile rode the bare-name fallback channel — it may be a UNION with … not this symbol's
exact profile alone."* An honest caveat, and it means neither answer could settle "who imports
`_message_fakes`". A bare `grep -rn "_message_fakes"` did — and found the **second consumer**
(`test_comms_tool.py`) that the design ruling's own verification had missed (§6). This is the
dogfood protocol's case (b)/(a): a non-symbol textual seam (a lazy call-time `import _message_fakes`
inside a helper function) and an exhaustiveness question where missing one site would have shipped
an unmeasured claim. **No friction filed** — the tool named its own bound and I honoured it; that
is the protocol working, not routed around.

Store law: `docs/reference/surrealdb-31-capabilities.md` read FIRST (§0–§7 of the served page).
No DDL is touched, so §1.1's clause rule is not in play. §2's silent-degradation class is what made
me probe rather than shrug at the non-landing mutation (§4/§7.1); §4's `RELATE`/edge semantics are
why the `to` edge's `in`/`out` shapes were probed with a `SELECT` control; §5's *"a single green
run never clears"* is why the reference-build receipt is quoted with its full counts rather than
"green". One new store fact was measured and filed as **finding #175** rather than left in a
report only the lead reads.

I filed no task-ledger row (my brief named none — brief-base §5).
