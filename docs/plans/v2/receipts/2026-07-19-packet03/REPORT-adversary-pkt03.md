# REPORT-adversary-pkt03 — CONTRACT ADVERSARY on the packet 03/03a message-graph contract

brief-base v4 read

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT** — 3 BLOCKERs, 5 lesser missing pins. The schema/DDL half is
  the strongest I have graded in this repo; the LEDGER SEMANTICS half has three holes.
- **P1 result — YES, wrong builds survive.** Eight plausible-wrong builds passed the ledger
  contract **57 passed / 0 failed**, indistinguishable from correct. Controls (W6/W7/W11) fail
  loudly, so the instrument discriminates.
- **BLOCKER-1** `awaiting_answer` ignores `message.question` entirely (keys on `grade`) — ruling
  9's whole mechanism is write-only. *(E6: the lead asked me to attack this. It does not hold.)*
- **BLOCKER-2** the fan-out silently DROPS a recipient when there are ≥3 — receipt intact, counts
  self-consistent. PR93's quantifier defect, verbatim.
- **BLOCKER-3** `directive_pending` counts the ELIDED REMAINDER, not directives — the fixture's
  arithmetic (5 signals + 2 directives, cap 5) makes the two numbers identical.
- **MAJOR-4** the dirty-store migration pin covers `to` — a table that **does not exist in
  production**. The three tables that DO (`briefed`/`refers`/`answers_to`, 101,479 rows) get
  offline string pins only. Measured: the narrowing write-poisons a heterogeneous row.
- Lesser: `set_status` monoculture · `asked_at` unpinned · message-`id` shape unpinned ·
  `ack(note=)` unpinned AND the design's `ack_note` column absent from the schema pins.
- **VERIFIED STRONG (mutation-proven, do not weaken):** `ENFORCED` (S1 → 6 RED), the relation
  policy flip (S2 → 4 RED), the `to` dirty-store pin, the four-way ack disambiguation, the
  peek/drain cap discipline, seam discovery (11 seams, live).
- Provenance: `loremaster.__file__ = /tmp/adv-pkt03/loremaster/loremaster/__init__.py` ·
  `git status --porcelain loremaster/loremaster/` **EMPTY** · §9.
- Receipt pointers: §1 P1 matrix · §2 quantifier table · §3 missing pins · §4 P2 perturbation ·
  §5 verified-strong · §6 P6/P6b sweeps · §7 residuals · §8 my own control failures · §9 receipts.

---

## §0. Provenance and method

```
$ ./scripts/scratch_copy.sh /tmp/adv-pkt03
scratch copy READY: /tmp/adv-pkt03
  loremaster  -> /tmp/adv-pkt03/loremaster/loremaster/__init__.py

$ cd /tmp/adv-pkt03 && uv run python -c "import loremaster, loremaster.messages as m; ..."
PROVENANCE loremaster.__file__ = /tmp/adv-pkt03/loremaster/loremaster/__init__.py
PROVENANCE messages.__file__   = /tmp/adv-pkt03/loremaster/loremaster/messages.py
```

I did **not** trust the author's `/tmp/pkt03-ref`; I made my own provenance-asserted copy of the
working tree and imported the reference production files into it. The six contract test files in
the scratch copy are **byte-identical** to the repo's (`diff -q` × 6, all SAME).

**What "the build" means here.** The author's reference `MessageLedger` store methods are stubs;
the executable semantics live in `_comms_fakes.FakeMessageLedger`, which the `[fake]` leg grades.
So the fake IS the reference implementation, and mutating it is the correct P1 instrument — it is
simultaneously P5 (can the double fail?). **It can**: W6/W7/W11 drive it RED.

**P0 baseline (the control that makes every result below meaningful):**
```
$ uv run pytest loremaster/tests/test_message_ledger.py -k "fake" -q -p no:randomly
57 passed, 5 skipped, 70 deselected in 0.39s
```

---

## §1. P1 — the wrong-build survival matrix

Every row is a real mutation of the reference build, with the **real** contract run against it.

| # | wrong build | result | verdict |
|---|---|---|---|
| **W1** | `awaiting_answer` keys on `grade=='directive'`, never reads `message.question` | **57 passed, 0 failed** | **SURVIVES — BLOCKER-1** |
| **W2** | `directive_pending = total_pending - len(window)` | **57 passed, 0 failed** | **SURVIVES — BLOCKER-3** |
| **W3** | `question = (set_status is not None)` | **57 passed, 0 failed** | **SURVIVES** |
| **W4** | `WaitingOnAnswer.asked_at = now()` instead of the question's `created_at` | **57 passed, 0 failed** | **SURVIVES** |
| **W5** | message id carries the table prefix (`message:01f…`) | **57 passed, 0 failed** | **SURVIVES** |
| **W8** | dedupe by `name` instead of by `id` | **57 passed, 0 failed** | **SURVIVES** |
| **W9** | fan-out drops the LAST recipient when >2 (receipt still reports all) | **57 passed, 0 failed** | **SURVIVES — BLOCKER-2** |
| **W10** | fan-out drops the id-sorted-last recipient when >2 | **57 passed, 0 failed** | **SURVIVES — BLOCKER-2** |
| W6 | drain stamps the WHOLE pending set (*control*) | 2 failed, 55 passed | correctly killed |
| W7 | `awaiting_answer` returns the NEWEST question (*control*) | 1 failed, 56 passed | correctly killed |
| W11 | fan-out writes NO edges at all (*control*) | 26 failed, 31 passed | correctly killed |
| S1 | drop `ENFORCED` from the `to` edge (*schema*) | 6 failed, 36 passed | correctly killed |
| S2 | relation table back on `IF NOT EXISTS` (*schema*) | 4 failed, 38 passed | correctly killed |

The three controls and both schema mutations prove the instrument sees breakage. Eight wrong
builds still walk through.

### BLOCKER-1 — ruling 9's mechanism is write-only (E6, as the lead suspected)

`TestSetStatusMarksTheQuestionItDoesNotStoreAState` pins that `message.question` is **set**
correctly. **Nothing pins that the derivation READS it.** Across the entire waiting-state section,
every `_ask()` is `grade=DIRECTIVE + set_status='input_required'` and every `_answer()` is
`grade=SIGNAL` — so `question` and `grade=='directive'` are **perfectly correlated in every
fixture**. All 12 `TestTheWaitingStateIsDerived` pins, both known-bound pins, and all three
`set_status` pins pass on a build that never reads the column.

This is the #94 shape the repo already paid for: *a contract pins a beautiful new symbol and never
requires the code to USE it.* It is also why the lead's E6 instruction was the right question —
the answer is that the mechanism is **not** pinned tightly enough.

### BLOCKER-2 — the ∀-recipient property is guarded by ONE cause

`TestSendValidatesEveryRecipientBeforeWritingAnyEdge` names the quantifier law in its docstring and
pins it **only through the door marked "recipient not registered"**. A recipient dropped in the
emission plumbing — supply fine, receipt intact, `recipient_count` and `recipient_names` fully
self-consistent — engages nothing.

The mechanism is a fixture gap: the only fixtures that FORCE an edge per recipient carry exactly
**two** recipients. The one three-recipient fixture,
`test_recipient_names_are_deterministic_not_argument_order`, asserts only the **names in the
receipt** and never that the edges were written. So `len(recipients) > 2` is an untested branch.

### BLOCKER-3 — arithmetic alignment (PR93's third axis)

`test_directive_pending_is_also_over_the_whole_set` uses 5 signals + 2 directives at cap 5. Then:

- directives in the whole set = **2**
- total − window = 7 − 5 = **2**

A build that counts *the rows you cannot see* reads 2 and passes. The pin's own failure message
promises it "must count DIRECTIVES rather than all messages" — and the assertion, at this fixture,
**cannot tell the difference**. (This is the assertion-vs-message gap the repo's P2 law names: the
message is the spec the author believed; the assertion is what the suite performs.) The test is
also the ONLY assertion of `directive_pending`'s value in the ledger contract.

Note the pin *does* correctly kill "computed over the capped window" (window holds 0 directives).
It is one specific wrong build it cannot see.

---

## §2. P1b — THE QUANTIFIER TABLE

Every invariant classified ∀-over-inputs vs guarded-by-known-failure-mode. Every guarded row
carries a receipt: either a surviving wrong build (finding) or the door-build that was killed.

| # | invariant | class | receipt |
|---|---|---|---|
| 1 | every recipient gets a delivery edge | **GUARDED** (cause: unregistered) | **W9/W10 survive → BLOCKER-2** |
| 2 | a rejected send leaves no row/edge | **GUARDED** (cause: unregistered) | door-build W11 killed (26 RED); other causes untested |
| 3 | body blank / oversize / at-cap | ∀ over body inputs, all fates forced | at-cap positive control present |
| 4 | grade is a closed domain | ∀ | offline + live ASSERT, both grades |
| 5 | one edge per DISTINCT recipient | **GUARDED** (identity = id in every fixture) | **W8 survives** (dedupe-by-name) |
| 6 | `thread` default vs explicit | ∀ (two values) | monoculture broken by the author |
| 7 | a message is a question iff asked as one | **GUARDED** (one `set_status` value) | **W3 survives** |
| 8 | broadcast excludes sender / explicit self-send delivers | ∀ (the pair) | both halves pinned |
| 9 | drain stamps exactly the served window | ∀ over N>cap | W6 killed (2 RED) |
| 10 | `total_pending` over the WHOLE set | ∀ | fixture N=8 > cap 5 |
| 11 | `directive_pending` counts DIRECTIVES | **GUARDED** (fixture arithmetic) | **W2 survives → BLOCKER-3** |
| 12 | peek stamps nothing | ∀ + positive control | non-peek control mutates |
| 13 | oldest-first ordering | ∀ | adversarial fake supplies wrong order |
| 14 | drain scoped to the caller | ∀ | 2 agents on 1 message |
| 15 | ack CAS is write-once | ∀ + unguarded-UPDATE control | control proves the GUARD does the work |
| 16 | every requested seq gets its own fate | ∀, all 4 fates forced in ONE call | **model example — do not weaken** |
| 17 | ack scoped by ownership | ∀ + positive victim assertion | |
| 18 | `ack(note=)` persisted | **UNPINNED** | never exercised; no `ack_note` column pinned |
| 19 | `asked_at` provenance | **UNPINNED** | **W4 survives** |
| 20 | message `id` is a bare ulid | **UNPINNED** | **W5 survives** |
| 21 | concurrent sends mint distinct seqs | ∀ over degree (8, 16) | racer lifetimes do NOT overlap (§7.1) |
| 22 | seq gaps break nothing | ∀ | gap forced by burning a number |
| 23 | concurrent sends all readable | ∀ | independent reader connection |
| 24 | exactly one ack winner at 16-way | ∀ over degree | single op per racer (§7.1) |
| 25 | waiting iff unanswered question thread | **GUARDED** (question⇔directive correlated) | **W1 survives → BLOCKER-1** |
| 26 | the derivation writes NOTHING | ∀ | row counts over repeated reads |
| 27 | drain does not clear the state | ∀ + positive control | control rules out stuck-at-waiting |
| 28 | `ENFORCED` rejects both ghost endpoints | ∀ + positive control first | **S1 → 6 RED** |
| 29 | every relation table typed + OVERWRITE | ∀ over 4 generators | **S2 → 4 RED** |
| 30 | the flip LANDS on a dirty store | **GUARDED — wrong table** | covers `to` only → **MAJOR-4** |
| 31 | sequence INE, idempotent, never rewinds | ∀ | live re-apply |
| 32 | UNIQUE(in,out) + different-recipient control | ∀ | negative control present |
| 33 | seam discoverable by the enumerator | ∀ | verified live: 11 seams, floor 10 |

---

## §3. MISSING PINS — the test that should exist + the defect it catches

**M1 (BLOCKER).** `test_a_DIRECTIVE_sent_without_set_status_does_NOT_make_the_sender_waiting`
and `test_a_SIGNAL_grade_question_DOES_make_the_sender_waiting`.
*Catches:* a derivation keyed on `grade` that never reads `message.question` — ruling 9's
mechanism present in the schema and dead in the code.
**Pair proven:** both RED on W1 (assertion failures, quoted §9.2); both GREEN on correct build.

**M2 (BLOCKER).** `test_a_three_recipient_send_reaches_ALL_THREE` (+ a real-backend
`test_the_receipt_COUNT_equals_the_edges_actually_written`).
*Catches:* a recipient silently dropped by the fan-out for any cause other than non-registration.
**Pair proven:** RED on W9, GREEN on correct.

**M3 (BLOCKER).** `test_directive_pending_when_directives_are_NOT_the_elided_remainder`
(6 signals + 2 directives at cap 5: elided 3 ≠ directives 2) and
`test_directive_pending_counts_directives_INSIDE_the_window_too`.
*Catches:* `directive_pending` computed as elided-count or window-count.
**Pair proven:** both RED on W2, both GREEN on correct.

**M4 (MAJOR).** A dirty-store migration pin in the `TestRelationFlipAgainstAnExistingStore` shape
for **`briefed` / `refers` / `answers_to`** — including a row whose endpoint is of a
now-forbidden table, asserting the DOCUMENTED outcome (readable, **write-poisoned**), so the
hazard is pinned rather than resting on a one-time audit.
*Catches:* the flip failing to land, or poisoning rows, on the tables that actually exist in
production. See §6.2 for the measurement.

**M5.** `set_status` exercised with a SECOND value (e.g. `'idle'`/`'active'`) asserting
`question is False`. *Catches:* `question = set_status is not None` (**W3**). Repo law: *if the
code can branch on a value, at least one pin must use a DIFFERENT value.*

**M6.** Assert `WaitingOnAnswer.asked_at == <the question's created_at>`.
*Catches:* **W4** — `asked_at` fabricated at read time. The field is in the pinned contract block
and is asserted nowhere.

**M7.** Assert `message.id` has no table prefix and that `InboxEntry.message_id` round-trips it.
*Catches:* **W5**. The contract's own docstring says "bare ulid (no table prefix)"; nothing
executes that claim, and packet 03a's renders will consume it.

**M8.** Exercise `ack(note=...)` and pin where it lands — plus the design's `ack_note` column on
the `to` edge (`~/.claude/plans/one-of-claude-codes-nifty-garden.md:121`, `:219`), which the
schema field pins do not cover. *Catches:* a build that accepts `note` and silently discards it.
⚠ **This may be a genuine spec gap rather than a contract miss — surfacing, not deciding.**

---

## §4. P2 — perturbation, with correct-build control legs

Perturbations were made in **scratch copies**, never in the repo.

```
BLOCKER-3 perturbation (directive_pending)
  LEG 1  perturbed pins vs WRONG build W2      -> 2 failed, 6 deselected
         (assert 3 == 2   <- read the elided remainder)
  LEG 2  perturbed pins vs CORRECT build       -> 2 passed, 6 deselected

BLOCKER-2 perturbation (three-recipient fan-out)
  LEG 1  missing pins vs WRONG build W9        -> 1 failed, 1 skipped
  LEG 2  missing pins vs CORRECT build         -> 1 passed, 1 skipped

BLOCKER-1 (question column)
  LEG 1  missing pins vs WRONG build W1        -> 2 failed
  LEG 2  missing pins vs CORRECT build         -> 2 passed
```

Both legs on every perturbation. Without leg 2 these would be botched expected values, not
findings (§8 records the run where exactly that happened to me).

**Fixture-discrimination verdicts, individually:**

| fixture | discriminates? |
|---|---|
| `_OVER_CAP = 8` vs `_DRAIN_CAP = 5` | **YES** — genuinely > cap; kills W6. The best fixture in the file. |
| 5 signals + 2 directives (directive_pending) | **NO** — arithmetic-aligned; blinds W2. **M3** |
| 2-recipient fan-out fixtures | **YES** at N=2 |
| 3-recipient fixture (`recipient_names` sort) | **NO** — asserts names only, never edges. **M2** |
| `_ask`/`_answer` helpers | **NO** — `question` ⇔ `grade` correlated in every call. **M1** |
| `set_status='input_required'` (every call site) | **NO** — single value. **M5** |
| grade / peek / thread | **YES** — two values each, deliberately |
| 4 identities incl. cross-session wave9 | **YES** — kills session-scoped drain |
| ack mixed batch (all 4 fates, one call) | **YES** — exemplary |
| `_old_world()` dirty store (`to`) | **YES** for `to`; **absent** for the production tables. **M4** |

---

## §5. Where the contract is genuinely strong (do not weaken these)

I tried to break these and could not. Receipts, not adjectives:

1. **`ENFORCED` on the delivery edge.** Dropping the clause turns 6 pins RED, including the
   positive control ordering that probe 1's own first run got backwards. Landmine 8 answered:
   **no**, a build cannot pass by declaring the table without `ENFORCED` — a right-table
   nonexistent record is accepted by typing alone, and `test_a_ghost_OUT_endpoint_is_REJECTED`
   fires. The `INSERT RELATION` door pin plus its verb-not-clause control is exactly right.
2. **The `to` dirty-store migration pin.** Landmine 9 answered: it applies OLD DDL → writes a row
   → applies NEW DDL, and asserts the guard live via **two independent instruments** plus row
   survival. Flipping the clause back to `IF NOT EXISTS` (S2) turns it RED. It would NOT pass on a
   build that never migrates. The author's own instrument correction (`INFO FOR TABLE` →
   `INFO FOR DB.tables`) is recorded honestly in the test.
3. **The four-way ack disambiguation.** All four fates forced in ONE call with an ordered
   per-seq accounting assertion. This is the ∀-property done correctly and should be the model
   for M2.
4. **Peek/stamp discipline** — every fixture N > cap, and the positive control proving a non-peek
   drain mutates through the same path.
5. **The write-once CAS control** (`test_the_guard_is_what_does_the_work`) — proves write-once is
   a property of the GUARD, not of edge rows. Exactly the probe-needs-a-control law.
6. **Landmine 5 (routing ≠ sharing) — VERIFIED, not relayed.** `_QUERY_SEAMS` parametrises **19**
   pin sites in `test_retry_seam.py` — derived, not eyeballed:
   `grep -c '@pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)' → 19`, which
   corroborates the author's "~19" claim exactly. I confirmed live that `MessageLedger` is discovered:
   `SEAMS discovered: 11 [... 'MessageLedger' ...] | floor = 10`. The mutation pins are inherited
   automatically, as claimed.
7. **Landmine 6 (runtime-guard reach) — does not bite.** `_all_sdk_call_sites()` returns **9**
   sites, all in `store/_txn.py` and `scout.py`. A `messages.py` following the `briefs.py` pattern
   (`bootstrap_session` + `run_query` + `execute_transaction`) adds **zero**: `SDK call sites
   inside messages.py: []`. If a builder hand-rolls one instead, the guard goes RED as
   "unobserved" — which is the correct outcome. No contract pin needed.

---

## §6. P6 / P6b sweeps

### 6.1 Corpse sweep — run from the GREP, not from the author's hand-list

Bare, anchor-free patterns per repo law. **Every hit gets an individual verdict.**

`TYPE RELATION` outside the contract file — 2 hits:
- `test_surreal_schema.py:462` — the widened guard-kind pin; **already rewritten by the contract**. Not a corpse.
- `test_graph_surreal.py:622` — asserts `"RELATION" in <stored ddl>`. Substring-tolerant, survives the flip. **Verified GREEN**, not a corpse.

`DEFINE TABLE IF NOT EXISTS` assertions — 19 hits, verdicts:
- `test_comms_schema.py:409, 489, 1524` (agent/brief/brief_counter) — **NODE** tables, correctly stay INE. Not corpses.
- `test_comms_schema.py:537` — inside the rewritten docstring quoting the retired literal. Prose. Not a corpse.
- `test_comms_schema.py:1579` — the new `message` NODE table. Correct.
- `test_comms_schema.py:1930, 1956, 2126, 2140, 2147` — the contract's own new code/comments/old-world fixture. Correct by construction.
- `test_surreal_schema.py:1534, 1548, 1549, 1740` — finding/finding_counter NODE tables. Not corpses.
- `test_diff.py:989, 995` — snapshot NODE tables. Not corpses.
- `test_retry_seam.py:2324, 2512, 3198, 4775` — throwaway harness tables. Not corpses.

**Independent re-run of the blast radius** (I did not relay the author's number):
```
$ uv run pytest loremaster/tests/test_graph_surreal.py loremaster/tests/test_surreal_schema.py -q
191 passed in 107.59s
```
No corpse survives the flip in those suites. The author's two catches
(`TestBriefedDdlOffline::test_table_is_a_schemafull_relation`, the ∀ guard-kind pin) are real and
correctly handled; my independent sweep found **no third**.

### 6.2 P6b — behaviour being REPLACED: `_define_relation_table`

Enumerated from source FIRST (`surreal_schema.py:620-627`), before reading
`REPORT-audit-edge-preflight.md`:

1. emits `DEFINE TABLE IF NOT EXISTS {name} TYPE RELATION SCHEMAFULL`
2. `IF NOT EXISTS` ⇒ idempotent AND **never migrates** a changed clause (silent no-op)
3. **no `IN`/`OUT`** ⇒ accepts an endpoint of ANY table — a permissive guard, and *the absence of
   an override is a behaviour*
4. `SCHEMAFULL` ⇒ undeclared top-level keys raise
5. single-parameter signature ⇒ all three callers pass a name only
6. no `ENFORCED` ⇒ accepts NONEXISTENT endpoints

Diffed against the inventory: items 2, 3 and 6 are the deliberate changes and are adjudicated in
the packet file. **Item 3 is where the diff bites, and it is a NARROWING on populated tables.**
Store reference §1.4 predicts schema converges but data does not. **Measured live, with a control
(§9.4):**

```
CONTROL  legal endpoint (aa->bb)   : readable=True  UPDATE OK      -> survives writable
PROBE    forbidden endpoint (aa->cc): readable=True  UPDATE RAISED -> WRITE-POISONED
         Couldn't coerce value for field `out`: Expected `record<bb>` but found `cc:r1`
```

So the hazard is real and behaves exactly as §1.4 documents. The pre-flight audit says production
is homogeneous — but **that audit is a claim about data at a point in time, and the contract holds
no executable pin over it.** The contract's ONE dirty-store instrument is pointed at `to`, a table
that does not exist in production, where `IF NOT EXISTS` would have worked anyway. **The
instrument is aimed at the case that cannot hurt and away from the three that can.** → **M4**.

---

## §7. Residuals — every item with an individual verdict

**7.1 Concurrency racer lifetimes do not overlap.** `_race` and `test_sixteen_ackers_of_one_edge`
give each racer exactly ONE operation. Repo law (§5) demands "racer LIFETIMES overlap (repeated
operations per racer); a start-line barrier synchronises Python, not the wire." **Verdict:
genuine gap, but the contract matches BOTH precedents the brief named** — `test_findings.py:477`
and `test_brief_ledger.py:285` are also single-op. This is a repo-wide pattern, not this author's
lapse. Escalating rather than charging it to packet 03; the operator should decide whether the law
or the precedents change.

**7.2 Concurrency pins assert DISTINCT, never MONOTONIC.** The findings/briefs precedents assert
*consecutive*; here gaps are legal so that is unavailable. A build minting a random or
timestamp-derived `seq` passes at 8- and 16-way. **Verdict:** low risk (the specified mechanism is
`sequence::nextval`), worth one cheap pin that concurrent seqs are all > the pre-race maximum.

**7.3 `drain(limit=0)` and `drain(limit=1)` never exercised; `ack(seqs=[])` never exercised.**
The repo's own 0/1/cap−1/cap/cap+1 discipline is only half-served — cap and cap+1 are excellent,
0 and 1 are absent. **Verdict:** minor missing boundary pins.

**7.4 `test_the_typed_relation_rejects_a_wrong_TABLE_endpoint` passes for a possibly-wrong
reason.** Its fixture uses `RecordID(BRIEF_TABLE, "not-an-agent")` — a record that does not exist,
so `ENFORCED` rejects it before endpoint typing is consulted. The test is named for TYPE coercion.
**Verdict:** currently harmless (the byte-exact statement pin subsumes it), but it would silently
stop testing its own subject if that pin were ever relaxed. Use an EXISTING record of the wrong
table.

**7.5 `session` monoculture in `send`.** Every send in the ledger contract is `SESSION_WAVE7`;
`SESSION_WAVE9` is only ever a *registration* session. The edge's `session` column and
`message.session` are therefore written with one value throughout. **Verdict:** low risk, but it
is the same monoculture shape that cost this repo a blocker before.

**7.6 Packet-file contradiction (author already flagged; I confirm it).**
`03-comms-message-graph.md` header says `DEPLOY: NO — test+store only` while its **Exit** section
still demands "deploy BOTH + smoke … live wire". The SPLIT gives the smoke to 03a. **Verdict:**
real editing residual in the plan file; needs a lead ruling, not a builder guess.

**7.7 `_MIN_KNOWN_SEAMS = 10` is a floor and the true count is now 11.** Confirmed live. The
contract's `TestTheLedgerIsDiscoverableByTheSeamEnumerator` is what actually notices a drop-out, so
the floor's weakness is covered. **Verdict:** no action; the author's F4 read is correct.

**7.8 The `[real]` leg (47 pins) remains ungraded for satisfiability.** The author said so
plainly, and I confirm I could not close it either without building the real store implementation.
**Verdict:** the largest residual RISK in this contract. The schema group IS graded live (42
passed, reproduced by me), so the DDL half is covered; what is unproven is that the real ledger's
store methods can satisfy the semantics the fake defines.

**7.9 Satisfiability re-graded by me, independently.**
```
$ uv run pytest loremaster/tests/test_comms_schema.py -k "Message or Enforced or RelationFlip or RelationTablePolicy"
42 passed, 174 deselected in 5.05s
```
Matches the author's "29 → 42" claim. **Verdict:** claim verified.

**7.10 RED honesty at HEAD — reproduced.**
```
$ uv run pytest test_message_ledger.py test_comms_schema.py test_surreal_schema.py -q
ImportError: cannot import name 'generate_message_ddl' from 'loremaster.store.surreal_schema'
ERROR test_message_ledger.py / test_comms_schema.py / test_surreal_schema.py
3 errors in 0.32s
```
RED for the RIGHT reason — genuinely-absent production symbols, not an import typo or a bad path.
**Verdict:** honest.

---

## §8. My own control failures (disclosed)

Two probes of mine failed for the wrong reason before I trusted any result — the exact hazard the
role exists to guard against:

1. My first BLOCKER-2 pair proof showed RED on both legs. Cause: **`NameError: AGENT_SCOUT_D is
   not defined`** — a missing import in my scratch file, not the assertion. Had I reported leg 1
   alone I would have filed a finding on a broken probe. Fixed; the re-run gives a clean
   RED/GREEN pair.
2. My first write-poisoning probe showed poisoning on BOTH the heterogeneous row and the
   homogeneous control — but the control failed on a **missing `resolved` field** in my
   hand-built old world, a different cause. The attribution was unsound until I rebuilt the probe
   with a single isolated variable (§9.4).

3. My first draft of §5.6 stated `_QUERY_SEAMS` parametrises "31" pin sites — a number I read off
   a **truncated** `grep | head -40` listing rather than deriving. The derived count is **19**
   (`grep -c`), which happens to corroborate the author's "~19" claim I was checking. An
   un-derived count inside a report about un-derived counts; caught on self-review and corrected
   in place.

All three are recorded because a probe that passes for the wrong reason is worth exactly as much
as a pin that cannot fail.

---

## §9. Raw receipts

### 9.1 Repo untouched
```
$ git status --porcelain loremaster/loremaster/
(empty)
$ ls loremaster/tests/test_adv_missing_pins.py
ls: cannot access ...: No such file or directory     # all probes live in /tmp/adv-pkt03
```

### 9.2 BLOCKER-1 pair
```
LEG 1 (wrong build W1):
E  AssertionError: a SIGNAL-graded question did not park its sender — the derivation
   reads `grade` instead of `question`
E  assert (None is not None)
FAILED ...::test_a_DIRECTIVE_sent_without_set_status_does_NOT_make_the_sender_waiting[fake]
FAILED ...::test_a_SIGNAL_grade_question_DOES_make_the_sender_waiting[fake]
2 failed, 2 deselected in 0.15s

LEG 2 (correct build):   2 passed, 2 deselected in 0.13s
```

### 9.3 BLOCKER-3 pair
```
LEG 1 (wrong build W2):
E  assert 3 == 2
   where 3 = MessageDrainResult(..., total_pending=8, directive_pending=3, ...)
2 failed, 6 deselected in 0.16s

LEG 2 (correct build):   2 passed, 6 deselected in 0.13s
```

### 9.4 P6b write-poisoning probe (single isolated variable, with control)
```
OLD: DEFINE TABLE IF NOT EXISTS advedge TYPE RELATION SCHEMAFULL
NEW: DEFINE TABLE OVERWRITE     advedge TYPE RELATION IN aa OUT bb SCHEMAFULL

CONTROL  legal endpoint (aa->bb)   : readable=True  UPDATE OK      -> survives writable
PROBE    forbidden endpoint (aa->cc): readable=True  UPDATE RAISED -> WRITE-POISONED
  InternalError: Couldn't coerce value for field `out` of `advedge:...`:
                 Expected `record<bb>` but found `cc:r1`
```

### 9.5 Seam / SDK call-site reach
```
SEAMS discovered: 11 ['AgentRegistry','BriefLedger','DiffEngine','FindingLedger',
  'LocalMemoryBackend','MessageLedger','SnapshotStamper','SurrealCodeGraph',
  'SurrealManifest','SurrealStore','TaskLedger']
MessageLedger discovered: True | _MIN_KNOWN_SEAMS floor = 10
SDK call sites total: 9   (all in store/_txn.py + scout.py)
SDK call sites inside messages.py: []
```

### 9.6 Schema mutation kills
```
S1 drop ENFORCED            -> 6 failed, 36 passed
   test_defines_the_to_edge_as_a_typed_relation_table, test_a_ghost_OUT_endpoint_is_REJECTED,
   test_a_ghost_IN_endpoint_is_REJECTED, test_no_dangling_edge_survives_a_rejected_relate,
   test_ENFORCED_closes_the_INSERT_RELATION_door,
   test_the_guard_is_LIVE_after_applying_the_new_ddl_to_a_dirty_store

S2 relation table -> IF NOT EXISTS -> 4 failed, 38 passed
   test_defines_the_to_edge_as_a_typed_relation_table,
   test_every_field_uses_the_overwrite_guard_and_every_object_uses_if_not_exists,
   test_every_relation_table_in_every_comms_generator_is_typed,
   test_the_guard_is_LIVE_after_applying_the_new_ddl_to_a_dirty_store
```

### 9.7 Tool honesty
No lore-tool fallback to declare beyond this line: I used **grep** for the §6.1 corpse sweep and
for the `directive_pending` / `asked_at` / `note` assertion sweeps. Per repo law that is the
honest instrument for cases (a) and (b) — rename/retired-literal exhaustiveness and non-symbol
textual seams — and I am saying so rather than routing around it silently. Structure questions
(seam discovery, SDK call sites) were answered by executing the repo's own enumerators, which is
stronger than either grep or the index. No friction to file.

---

# VERDICT: **CONTRACT INSUFFICIENT**

Three BLOCKERs (M1, M2, M3), one MAJOR (M4), four lesser missing pins (M5–M8), each with a named
test to write and a named defect it catches. Eight wrong builds pass the contract 57/0 today.

This is **not** a weak contract — the schema, ENFORCED, migration and ack-disambiguation groups
are among the strongest instruments in this repo, and I have shown by mutation that they hold. The
holes are concentrated in exactly the three places the repo's own history predicts: a **mechanism
pinned as written but never as read** (#94's shape), a **∀ property conditioned on the debugged
cause** (PR93's shape), and a **fixture whose arithmetic hides the branch** (PR93's third axis).
The contract author named all three laws in the docstrings and was caught by all three anyway —
which is precisely why this phase exists and is not a criticism of the work.

M1–M3 cost roughly one function each to write. They were expensive only to think of.
