brief-base v6 read

# REPORT — builder-r2 · packet 03a-2 · R2 (`sender != me`) + the two prose fixes

*(Everything below MEASURED 2026-07-23 on this box, at commit `50d65a0` plus the working-tree
contract from `REPORT-contract-r2.md`. Store: `spike-surreal ws://127.0.0.1:18000`;
`:18500` NEVER contacted. Claims are dated where made, never "currently".)*

## SUMMARY BLOCK

- **State: done.** All three jobs landed. Exit target hit exactly.
- **Gate receipts (all four, with passed-COUNTs).**
  - `uv run pytest loremaster/tests/test_message_ledger.py -n auto -q` → **`180 passed, 12 skipped`**,
    **0 failed** (RED baseline before my change, re-measured by me: `2 failed, 178 passed, 12 skipped`).
  - `uv run pytest loremaster/tests/test_retry_seam.py -n auto -q` → **`503 passed, 1 warning`**.
  - `./scripts/typecheck.sh` → **`Found 36 errors in 3 files (checked 148 source files)`** — unchanged,
    and **ZERO** in `messages.py` (grep count of `loremaster/messages.py` in mypy output = **0**).
  - `uv run ruff check .` → **`All checks passed!`**
- **Mutation proof (against MY build, §3).** Conjunct removed → **exactly 2 failed** — the two R2
  `[real]` legs, nothing else. Restored from `cp -a` content → **`180 passed, 12 skipped`**, file
  byte-exact (`md5 e7377ebb38ef2654dd7d1142f84fbbde` both sides). RED → GREEN → RED → GREEN.
- **Delivery positive control (ruling 7 intact).**
  `TestSendWritesTheNodeAndOneEdgePerRecipient::test_an_EXPLICIT_self_addressed_send_IS_delivered`
  → **2 passed** (`[real]` + `[fake]`) — **and it also passed UNDER the mutation**, so it is
  independent of the conjunct, not carried by it. Each new R2 pin additionally asserts its own
  self-note WAS delivered before asserting it is not an answer; both are green.
- **Derivation classes, full results.** `TestTheWaitingStateIsDerived` → **36 passed, 2 skipped**
  (154 deselected). `TestTheDerivedWaitingStateKnownBound` → **4 passed** (188 deselected).
  No regression in either.
- **Contract untouched — proven, not asserted.** `test_message_ledger.py` is byte-identical to the
  start state (`diff -q` vs my `cp -a` backup: identical; `md5 33b2237f7c898dbd32b5fb6509be5b92`).
  `FakeMessageLedger` untouched: my only edit to `_message_fakes.py` is the ONE module-docstring
  sentence (§2.3 shows that isolated diff).
- **Deviations (1).** Job 3's supplied replacement ends a sentence whose trailing relative clause
  (*", which is where contract-first wants it"*) modified the deleted noun *"the one new contract
  file"*. I dropped that dangling clause; keeping it would have left prose referring to nothing.
  Nothing else in that file changed. **§4.1 — lead may restore a reworded tail in one line.**
- **Decisions needed: none.** Three findings surfaced, none blocking (§4).
- **New PROBE receipt handed forward (§4.2):** `in.sender != $agent` where `in.sender` is ABSENT
  (a dangling `in`, #105's shape) → the row is **INCLUDED** (`NONE != agt:me` is **`True`** on
  3.2.1, probed with a positive control). So the conjunct changes behaviour for genuinely
  self-sent messages and for **nothing else** — no silent drop was introduced.
- **Provenance:** no scratch copy; every run imported the REAL tree —
  `loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`,
  `messages.__file__ = …/loremaster/loremaster/messages.py`. Mutation used a `cp -a` CONTENT
  backup, restored from content, md5-verified. **No git-state mutation** (no stash/checkout/reset/
  add/commit — only `git status`, `git diff`).
- **Receipt pointers:** §1 store law · §2 what changed · §3 mutation proof + controls · §4 flags ·
  §5 sweeps · §6 mutation safety · §7 tool honesty · §8 unrelated failures.

---

## 1. Store law applied (not re-derived)

`docs/reference/surrealdb-31-capabilities.md` read FIRST, in full. What actually bound this change:

- **§1 (DDL/migration) is NOT in play** — I touched no DDL. The `OVERWRITE`/`IF NOT EXISTS`
  decision rule, #107, and the sequence/index clauses are all out of the blast radius of a
  `SELECT` predicate. Stated so the next reader does not have to re-derive that it was checked.
- **§2 (DML idioms)** is the section that governs: `$agent` is bound as a `RecordID` (§2's
  round-trip rule) and the comparison is `RecordID != RecordID`, so no stringification is
  introduced — §7's *"a bare `str` endpoint is rejected loudly"* hazard is avoided by construction.
- **§2's silent-degradation class** is what made me PROBE the absent-`sender` corner (§4.2) rather
  than reason about it: *"a missing SELECT projection reads `None`, not a `KeyError`"* — a
  traversal field that silently reads NONE inside a **WHERE** is the same shape one level over, and
  the shipped code did not previously depend on `in.*` in a predicate at all.
- **Finding #175 (the brief's landmine) is context, not a constraint here** — it is an `UPDATE`
  anomaly. I am editing a `SELECT`, and I reached for no `UPDATE` anywhere. Confirmed rather than
  assumed: the only statement I changed is the deliveries `SELECT`.
- **§5's *"a single green run never clears"*** is why every count below is quoted in full rather
  than reported as "green".

## 2. What changed (two files, three edits)

### 2.1 `messages.py::MessageLedger.awaiting_answer` — the R2 conjunct (Job 1)

The deliveries SELECT, split across two f-strings only because one line exceeds `line-length = 110`:

```python
f"SELECT in.thread AS thread, in.seq AS seq FROM {TO_RELATION} "
f"WHERE out = $agent AND in.sender != $agent",
```

Exactly the ruling's implementation step 1. **Minimal, as briefed:** the method is not
restructured, `ack` is untouched, no index is added, and the read stays **unbounded** — R3's
`in.thread IN $question_threads AND in.seq > $min_question_seq` is deliberately 03b's and is
**not** present here.

### 2.2 `messages.py::MessageLedger.awaiting_answer` — the docstring (Job 2)

*"all THREE conjuncts"* → **FOUR**, and — this is the part a literal three→four edit would have
missed — **the false attribution was moved, not merely renumbered.** The shipped prose hung the
claim *"so the asker's own follow-up on its own thread is not an answer"* off the **delivered-to-me**
conjunct. That parenthetical was false as written and would have stayed structurally false at four:
delivered-to-me does not produce that property; the **fourth** conjunct does. It now reads *"a reply
nobody addressed to you is not yours"* (what delivered-to-me actually buys) and the self-note claim
sits on `in.sender != $agent`, where the check lives.

Added, per the ruling: a paragraph citing `docs/plans/v2/03a-2-consume-path-design-rulings.md` §R2
by tracked path, naming the error direction (false-NOT-waiting, the invisible one), and stating the
**ruling-7 reconciliation** in place — a self-addressed send stays deliverable/drainable/ackable and
cites the pin that proves it. The existing KNOWN-BOUND paragraph gained R2's accepted consequence
(no self-service clearing; some OTHER party's on-thread reply is what clears it), folded into that
bound rather than given one of its own — as §R2 directs.

### 2.3 `_message_fakes.py` — the ONE false module-docstring sentence (Job 3)

Contract-r2 §7.2's pre-authored replacement, applied. My whole edit to that file, isolated against
my start-state backup (i.e. excluding the contract author's oracle work already in the tree):

```diff
 Living in its own module makes the regression STRUCTURALLY IMPOSSIBLE rather
-than merely remembered: only ``test_message_ledger.py`` imports this file, so
-the blast radius of the not-yet-existing module is the one new contract file,
-which is where contract-first wants it.
+than merely remembered: its consumers are exactly the packet-03 contract files
+(``test_message_ledger.py``, ``test_comms_tool.py``) — never the shared
+``_comms_fakes.py`` seam, so a not-yet-existing ``loremaster.messages`` can never
+take an unrelated suite down with it.
```

Rendered in the file's own rst `` `` `` idiom rather than §7.2's markdown backticks (brief-base §7,
match the surrounding style). `FakeMessageLedger` and every behaviour: untouched.

## 3. Mutation proof, and the controls that make it mean something

| leg | build | result |
|---|---|---|
| RED (start state) | shipped code, no conjunct | **`2 failed, 178 passed, 12 skipped`** — the 2 are the R2 `[real]` legs |
| GREEN | + my conjunct | **`180 passed, 12 skipped`, 0 failed** |
| **MUTATION** | my build with `AND in.sender != $agent` deleted | **`2 failed, 178 passed, 12 skipped`** — `…SELF_ADDRESSED…is_NOT_an_answer[real]` + `…with_ANOTHER_recipient_is_STILL_not_an_answer[real]`, **and nothing else** |
| RESTORE | `cp -a` from content backup | **`180 passed, 12 skipped`**, `md5 e7377ebb38ef2654dd7d1142f84fbbde` — byte-exact |

**The mutation is specific, not just red:** exactly the two pins the conjunct exists to satisfy
went red, and all 178 other nodes stayed green — so the conjunct is not silently carrying some
other assertion, and it did not break the query.

**Positive control — the query still WORKS and delivery still happens.** A conjunct that broke the
deliveries SELECT would also produce green R2 pins (nothing would ever look like an answer), so
"the two pins passed" is not sufficient on its own. Three independent controls, all green:

1. `test_an_EXPLICIT_self_addressed_send_IS_delivered[real]` **and** `[fake]` → **2 passed**.
   Also **passed under the mutation** — it does not depend on the conjunct in either direction.
2. **Inside each new pin's own fixture**, before the waiting assertion: the self-note's `seq` is
   asserted present in the sender's own `drain(peek=True)` inbox. A build where the self-addressed
   message stopped being delivered fails there, not on the waiting state.
3. **In pin 1's fixture, after it:** an external `_answer` on the same thread **DOES** clear the
   state (`awaiting_answer(...) is None`). So the predicate still matches real answers — the
   conjunct narrows the SENDER, it did not disable the clause.

**Derivation classes, in full (no regression):** `TestTheWaitingStateIsDerived` → **36 passed,
2 skipped**; `TestTheDerivedWaitingStateKnownBound` → **4 passed**.

## 4. Flags — everything I noticed (I do not decide scope)

### 4.1 DEVIATION: one dangling clause dropped in Job 3

§7.2's replacement text ends its own sentence, but the original continued *", which is where
contract-first wants it"* — a relative clause whose antecedent (*"the one new contract file"*) the
replacement deletes. I dropped it rather than leave prose pointing at a removed noun. Disclosed
because the brief called §7.2 "exact text": everything §7.2 supplied is present verbatim (modulo rst
backticks); the deletion is the trailing clause only. If the lead wants the sentiment kept, the
one-line restoration is `… down with it — which is where contract-first wants the blast radius.`

### 4.2 NEW PROBE RECEIPT — the absent-`sender` corner of the new predicate. Direction: unchanged.

The shipped code previously used `in.*` only in the **projection**; my change makes the derivation
depend on a traversal field inside a **WHERE**. Store reference §2 warns that a missing projection
degrades silently to `None`, so I did not assume the three-valued behaviour — I probed it.

[PROBED 2026-07-23, spike-surreal `ws://127.0.0.1:18000`, surrealdb-3.2.1, throwaway DB dropped
after; `:18500` never touched] Three `msg->lnk->agt:me` edges: `seq=1` sender = **me**, `seq=2`
sender = **another agent**, `seq=3` **no `sender` column at all** (a dangling/absent `in.sender`,
finding #105's shape).

| statement | matched |
|---|---|
| `SELECT in.seq AS seq FROM lnk WHERE out = $agent AND in.sender != $agent` | **`[2, 3]`** |
| `SELECT in.seq AS seq FROM lnk WHERE out = $agent` *(control — instrument sees all rows)* | `[1, 2, 3]` |
| `RETURN [ NONE != agt:me, (SELECT VALUE sender FROM msg:m_null)[0] ]` | `[True, None]` |

**Reading:** the self-sent row (1) is excluded — R2 working. The other-sender row (2) is kept.
The **absent-sender row (3) is KEPT**, because `NONE != agt:me` evaluates to **`True`**, not to
NONE/false. The raw leg's second element confirms the fixture really did reach the door (that
message's `sender` is genuinely `None`), and the control proves the query is not simply matching
everything. **So the conjunct's behavioural delta is confined to genuinely self-sent messages — it
introduces no silent row-drop, in either error direction.** Worth a line in store reference §2 /
§6.6 (we are the only source) at the lead's discretion; I did not edit that file — outside my
writable set. I did **not** file a finding: this is a benign confirmation, not friction.

### 4.3 `awaiting_answer` has ZERO production consumers today

`lore_impact` verdict: `dead (heuristic)`, **0 prod / 20 test references**, `direct_consumers: []`
— corroborated by a bare grep (§7): outside `messages.py` itself and the two contract files,
`awaiting_answer` appears nowhere in `loremaster/`. Expected (03b wires the dispatcher), and it is
the reason this docstring fix is cheap NOW: **the prose I corrected is currently read by no served
surface, so the false-gate class moves next to 03b's `lore_comms` instructions block** — which is
where the ruling's R5/R6 teaching clauses also land. Flagging so 03b's contract author knows the
served-English risk transfers with the wiring, not that anything is broken today.

### 4.4 The R3 traversal-WHERE question is now half-settled, with a two-sided receipt

Corroborating `REPORT-contract-r2.md` §3 from a second instrument: `WHERE out = $agent AND
in.sender != $agent` **executes and DISCRIMINATES** on spike-surreal 3.2.1 — proven two-sided in one
run (the two new pins require it to exclude; `test_an_answer_on_the_thread_clears_it_…` requires it
to still include), plus §4.2's direct probe. This settles only the `in.sender` half of §R3(2);
`in.thread IN $question_threads` and `in.seq > $min_question_seq` remain **unproven** and are 03b's
to demonstrate on the `[real]` leg, with the documented unbounded-indexed fallback.

## 5. Sweeps — the retired prose is gone, and nothing else taught it

Per repo law (rename/reshape sweeps use BARE, anchor-free patterns; no "all remaining hits are X").

- `grep -rn "THREE conjunct\|three conjunct"` across `*.py` + `*.md`, `.venv` excluded — **5 hits,
  each with an individual verdict**: `REPORT-builder-03a2.md:80` (historical record of the pre-R2
  build — correct as history) · `REPORT-contract-r2.md:76,133,337` (the three places contract-r2
  *instructs* this fix — correct as instruction) · `docs/plans/v2/03a-2-consume-path-design-rulings.md:137`
  (the ruling's own implementation step — correct as instruction). **Zero in `loremaster/`.** The
  retired claim survives in no production or test surface.
- Bare `grep -rn "conjunct"` across the same set: the only `loremaster/` hits outside my two files
  are `test_message_ledger.py` (the new pins' own prose, which already says FOUR), an unrelated
  `acked_at IS NONE` conjunct comment at `test_message_ledger.py:1433`, and three hits in
  `store/surreal.py` / `memory/local.py` about FULLTEXT `@@` **conjunctive matching** — a different
  word sense, not this rule.
- **Is any docstring pinned by a test?** `grep -rn "__doc__" loremaster/tests/` → the `__doc__`-reading
  pins cover `shellout`, `DiffEngine._live_state`, `_surreal_harness`, and `retry_on_conflict`.
  **None reads `awaiting_answer.__doc__`** — consistent with the brief's warning that nothing in the
  contract can fail on this docstring.
- Neighbouring prose checked for the same false claim: `messages.py`'s module docstring (`:44–51`)
  and the `WaitingOnAnswer` class docstring both mention the derivation but state **no conjunct
  rule**, so neither went stale. Verified by reading, not assumed.

## 6. Mutation safety

- Tree at `50d65a0` + the contract's two working-tree files. **No git-state mutation of any kind**:
  no `stash`, `checkout --`, `reset`, `add`, or commit. Only `git status` / `git diff` (reads).
- **No scratch copy** — `scripts/scratch_copy.sh` not needed, nothing ran outside the real tree.
  Provenance printed and checked before the first gate run:
  `loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` ·
  `messages.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/messages.py`.
- Before editing: `cp -a` CONTENT backup of all three files. Before mutating: a second `cp -a`
  CONTENT backup of the **fixed** `messages.py`. Restored **from content**, md5-verified after.

| file | md5 (final) | state |
|---|---|---|
| `loremaster/loremaster/messages.py` | `e7377ebb38ef2654dd7d1142f84fbbde` | my conjunct + docstring; identical to the pre-mutation fixed build |
| `loremaster/tests/_message_fakes.py` | `1ef5a020228979fb7d301411d217efed` | contract author's oracle + my ONE docstring sentence |
| `loremaster/tests/test_message_ledger.py` | `33b2237f7c898dbd32b5fb6509be5b92` | **unchanged from start** (`diff -q` identical) |

`git status --porcelain`: the three `M` files above plus the pre-existing untracked `REPORT-*.md`
and this report. **No commits, no deploy, `:18500` never contacted.**

## 7. Tool honesty (brief-base §4, CLAUDE.md dogfood protocol)

lore's tools were loaded in ONE `ToolSearch` call as briefed. `lore_get_symbol` on
`loremaster.messages.MessageLedger.awaiting_answer` gave the authoritative definition (used to read
the method before the file, per investigation order). `lore_impact` answered the consumer question
(§4.3) — **and self-reported its bound**: *"this profile rode the bare-name fallback channel — it
may be a UNION with `FakeMessageLedger.awaiting_answer`'s own references"*, plus the standing
astroid caveat.

**I fell back to grep, deliberately, and say so:** (a) the §5 prose sweeps are the honest-grep
category — retired natural-language claims carry no symbol anchor, so no graph query can find them;
(b) I cross-checked `lore_impact`'s 0-prod-consumer answer with a bare `grep -rn "awaiting_answer"`
because the tool had named its own union caveat and §4.3 is an **exhaustiveness** claim. The grep
agreed. **No friction filed** — the tool declared its bound and I honoured it; that is the protocol
working, not routed around.

The absent-`sender` question (§4.2) was **probed**, not searched: it is a three-valued-logic
behaviour of a traversal field inside a WHERE, which the store reference does not cover and which
sits in §6.6's "we are the only source" territory. Docs-first was still respected — the reference
was read in full FIRST, and the probe carried a positive control precisely because §4's own
`ENFORCED` episode records a probe run without one reporting the opposite of the truth.

No task-ledger row: my brief named none (brief-base §5).

## 8. Unrelated failing tests

`loremaster/tests/test_comms_tool.py -n auto -q` → **`149 failed, 554 passed`**, measured by me
**after** my change. That is byte-identical to the brief's stated before-state (`149` both sides),
so my `_message_fakes.py` docstring edit — the only way this wave could reach that suite — changed
nothing there. Those 149 are packet 03b's committed RED contract. **Not touched, not "fixed."**

There are 149 failing tests unrelated to our present scope. Do you want to examine them more
closely?
