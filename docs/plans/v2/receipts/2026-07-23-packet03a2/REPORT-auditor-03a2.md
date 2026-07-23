brief-base v6 read

> **ARCHIVE CORRECTION (lead, 2026-07-23).** This report's summary block gave the mypy error
> distribution as `test_comms_tool.py` 43 / `test_comms_promise_registry.py` 3 /
> `test_message_ledger.py` 2 — which sums to 48, beside its own CORRECT total of 36. The figure is
> corrected in place below (43 → 31, struck rather than overwritten). Re-derived twice: by
> `fixer-r1r8` (its §6 S4) and independently by the lead at `f04729c`
> (`./scripts/typecheck.sh | grep error: | cut -d: -f1 | sort | uniq -c` → 31 / 3 / 2 = 36).
> Every other number in this report was re-derived by the lead and held. The report's VERDICT
> (GO) and its residual table are unaffected.

# REPORT — auditor-03a2 · COLD REFUTE audit of packet 03a-2 (comms ledger: CONSUME path)

## SUMMARY BLOCK

- **VERDICT: GO** — the shipped `ack` / `awaiting_answer` in `loremaster/loremaster/messages.py`
  at `853a95b` are, on my own instruments, CORRECT. I could not construct a wrong-behaviour
  refutation of the code. **But the wave ships with ONE CONFIRMED FALSE GATE and two behaviours
  the contract cannot see — see RESIDUALS; R1 is not optional.**
- **My gate receipts** (re-run by me on the restored tree at `ac38246`, 2026-07-23):
  `test_message_ledger.py -n auto -q` → **`171 passed, 9 skipped in 7.05s`** ·
  `test_retry_seam.py -n auto -q` → **`503 passed, 1 warning in 8.11s`** ·
  `./scripts/typecheck.sh` → **`Found 36 errors in 3 files (checked 148 source files)`**,
  distribution ~~`test_comms_tool.py` 43~~ **31** / `test_comms_promise_registry.py` 3 /
  `test_message_ledger.py` 2 — **ZERO in `messages.py` or any production module** ·
  `uv run ruff check .` → **`All checks passed!`**
- **`[real]`-leg grading: 31 real-leg pins EXECUTE for 03a-2, SILENT SKIPS = 0.**
  `ack` 13 (`TestAckIsWriteOnce` 3 + `TestAckDisambiguates…` 9 + `TestConcurrentAcks…` 1),
  `awaiting_answer` 18 (`TestTheWaitingStateIsDerived` 16 + `TestTheDerivedWaitingStateKnownBound` 2).
  **All 9 skips in the file are `[fake]`-leg skips** (node-id verified, §2) — no `[real]` pin skipped.
- **Mutation proofs: 14 of 15 fired RED** (§3). The 15th did not — **R1 below**.
- **Concurrency, my own tally: 20/20 consecutive GREEN**, zero re-rolls (§4). Plus an independent
  8-way probe: exactly 1 winner, 1 distinct stamp, no `None` (§6 P9).
- **Sharing proof (ROUTING IS NOT SHARING): PROVEN, 6/6 legs with controls in both directions** (§5).
  Both new call sites' retry behaviour FOLLOWS the moved `_txn._RETRYABLE_CONFLICT_MARKER`, and
  STOPS retrying the old text once moved. No hand-rolled retry/backoff/jitter/conflict-string in
  `messages.py` (bare anchor-free grep, §5).
- **Provenance receipt:** every run above imported
  `loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`
  and `messages.__file__ = …/loremaster/loremaster/messages.py` — the REAL tree. No scratch copy
  was made; mutations were applied to the real (committed) tree with a `cp -a` content backup and
  restored byte-exact.
- **Tree restored:** `git status --porcelain` → only `?? REPORT-builder-03a2.md`;
  `md5sum` of `messages.py` == `git show ac38246:…` == `1d5e824b5c156ce61945d7d79695827c`.

### RESIDUALS — READ THIS TABLE, NOT JUST THE VERDICT

| # | severity | what | evidence |
|---|---|---|---|
| **R1** | **FALSE GATE — contract defect, code is correct** | `TestTheWaitingStateIsDerived::test_the_derivation_writes_NOTHING` promises to catch *"a build that stamps an `agent` column (or any row)"* but asserts only `message`/`to` **ROW COUNTS**. A build whose `awaiting_answer` stamps **`agent.status = 'input_required'` — the exact stored state ruling 9 STRUCK** — passes the **ENTIRE `[real]` leg, 86 passed / 0 failed.** | §3.2, W1/W2/W3 all UNSEEN; **W4 positive control CAUGHT** the identical write shaped as a row CREATE, so the instrument demonstrably fires |
| **R2** | real, prose-vs-code | `awaiting_answer`'s docstring claims *"a `to` edge to it — so the asker's own follow-up on its own thread is not an answer"*. **FALSE when the follow-up is SELF-ADDRESSED**: the asker discharges its own debt. Reproduced live with a control. The **fake oracle does the same**, so NEITHER leg discriminates — this is a SPEC question, not a build divergence | §6 P3 / P3b |
| **R3** | perf, unbounded | **TWO TABLE SCANS on the hot comms path**, EXPLAIN-confirmed: `ack`'s `SELECT id, seq FROM message WHERE seq IN $seqs` and `awaiting_answer`'s `SELECT … FROM message WHERE question = true AND sender = $agent`. Both scan the whole `message` table, which grows forever. The other three statements ARE index-backed | §6 P8b |
| **R4** | unbounded read | `awaiting_answer`'s `SELECT … FROM to WHERE out = $agent` IS index-backed (`to_out_seen_at`) but is **unbounded**: it pulls EVERY delivery edge the agent has EVER received, then dereferences `in.thread`/`in.seq` per row, on every comms call | §6 P8b |
| **R5** | unpinned, correct | duplicate seq inside ONE batch → `['acked','already_acked','already_acked']`, one identical stamp, `acked_count=1/already=2`. Matches the docstring and the "two separate calls" claim. **No pin covers it** | §6 P1 |
| **R6** | unpinned, semantic | ONE answer on a thread carrying TWO questions discharges **BOTH**. Ordering IS respected (control: an answer between them leaves the later question outstanding). Defensible thread-level-debt semantics, but undecided by any pin | §6 P7 / P7b |
| **R7** | unpinned | `ack` does NOT stamp `seen_at`: an acked-but-undrained message stays **PENDING** in `drain` and counts toward `total_pending`. Plausibly intended (seen ≠ actioned); nothing decides it | §6 P5 |
| **R8** | latent | `_ack_entries` checks `not in stored_stamps` **BEFORE** `in won_stamps`, so a CAS **WINNER** whose follow-up-SELECT row went missing would be reported **`not_addressed`** — "you were never sent this" for a message you just acked. Only reachable if the edge vanishes between the two statements (hard agent delete → cascade, store ref §4). Latent today because agents are retired, never hard-deleted — the same latency clause as #105 | §7 |
| **R9** | prose | the module docstring's new SCOPE HISTORY says *"Receipts for both waves are archived under `docs/plans/v2/receipts/`"*. **03a-1's are** (`2026-07-23-packet03a1/`); **03a-2's is not** — it is `REPORT-builder-03a2.md`, untracked at the repo root. True only after the lead's close-out `git mv`. Also a bare-directory citation where repo law asks for a section-exact tracked path | §8 |
| **R10** | state-of-record | `docs/plans/v2/INDEX.md` still reads `@ b32839b` and `test_message_ledger.py` **140 passed / 31 failed** — three commits stale as of `ac38246`. Lead close-out item, flagged so it is not missed | §8 |

**Builder's four flags, adjudicated on my own evidence:** (1) duplicate seq — **non-issue, correct**, but unpinned (R5). (2) self-addressed follow-up — **REAL** (R2), and worse than the builder framed it: the *docstring* asserts the opposite. (3) two unindexed scans — **REAL**, EXPLAIN-confirmed (R3), plus a third unbounded read the builder did not flag (R4). (4) doc modified mid-run — **non-issue**, that was the lead's `ac38246`.

---

*(Everything below measured 2026-07-23 on this box against `spike-surreal ws://127.0.0.1:18000` — the
TEST store. `:18500` was never touched. Artifact under audit: commit `853a95b`, tree at `ac38246`.
Claims are dated at the point of measurement, not "currently".)*

## 1. Method

I read the diff and the contract and formed my own view BEFORE reading `REPORT-builder-03a2.md`.
Required reads done in order: `~/.claude/orchestration/brief-base.md` (v6),
`docs/reference/surrealdb-31-capabilities.md`, `docs/plans/v2/03a-2-comms-ledger-consume.md`.

**Tool honesty (brief-base §4).** The lore MCP tools were loaded in ONE `ToolSearch` call as
briefed. I then **did not use them** — every question this audit asked was one of the three cases
the repo's dogfood protocol reserves for grep/direct read: (a) exhaustiveness sweeps for retired
prose (`NotImplementedError` stub language) where an anchored/semantic search systematically misses
the un-anchored prose mention, (b) non-symbol textual seams (SurrealQL statement strings, EXPLAIN
plans, DDL field specs), (c) live runtime behaviour, which no index can answer. **Saying so out
loud, per §4.** No friction is owed — this is the protocol working, not routed around.

**Mutation safety.** No scratch copy. `cp -a` content backup at
`/tmp/…/messages.py.orig` (md5 `1d5e824b…`), every mutation applied to the real tree and restored
from CONTENT with an md5 assertion in the harness itself. Final tree byte-identical to
`git show ac38246:loremaster/loremaster/messages.py`.

## 2. `[real]`-leg grading — the number that matters

The `[fake]` legs passed before this wave existed and prove nothing about it.

```
$ uv run pytest loremaster/tests/test_message_ledger.py -p no:randomly --collect-only -q  ->  180 tests collected
   TestAckIsWriteOnce                        3 fake / 3 real
   TestAckDisambiguatesTheFourWayEmptyReturn 9 fake / 9 real
   TestConcurrentAcksOfOneEdge…              1 fake / 1 real
   TestTheWaitingStateIsDerived             16 fake / 16 real
   TestTheDerivedWaitingStateKnownBound      2 fake / 2 real
   => 03a-2 [real]-leg pins EXECUTED: 13 (ack) + 18 (awaiting) = 31
```

All 9 skips carry `[fake]` in their node id (verified with `-v`, not with the reason text):

```
…::test_the_receipt_COUNT_equals_the_edges_actually_written[fake-1..4]   SKIPPED
…::TestSendValidatesEveryRecipient…::test_a_rejected_send_leaves_no_message_row_at_all[fake]
…::TestSendValidatesEveryRecipient…::test_no_dangling_edge_survives_a_send[fake]
…::TestAckIsWriteOnce::test_the_guard_is_what_does_the_work[fake]
…::TestTheDdlSliceIsAppliedByEnsureReady::test_ensure_ready_creates_the_message_and_to_tables[fake]
…::TestTheWaitingStateIsDerived::test_the_derivation_writes_NOTHING[fake]
```

**SILENT SKIPS ON THE `[real]` LEG: 0.** The brief's arithmetic note is confirmed: 171 + 9 = the
180 pin total; "180 passed" is impossible and its absence is not a miss.

## 3. Mutation proofs

Harness: apply mutation to the real tree → run the named `[real]`-leg pins → restore from content.

### 3.1 Wave 1 — 15 mutations, 14 fired RED

| # | mutation | verdict | tail |
|---|---|---|---|
| M1 | drop `acked_at IS NONE` from the CAS | **RED** | 2 failed |
| M2 | drop `out = $agent` from the CAS | **RED** | 1 failed |
| M3 | note escapes the guard (second unguarded `UPDATE … SET ack_note`) | **RED** | 1 failed |
| M4 | `unknown_message` → `already_acked` | **RED** | 2 failed |
| M5 | `not_addressed` → `already_acked` | **RED** | 2 failed |
| M6 | losers report a FRESH stamp instead of the STORED one | **RED** | 1 failed |
| M7 | walk the STORE's result set, not the REQUEST (quantifier law) | **RED** | 1 failed |
| M8 | `question = true` → `grade = 'directive'` | **RED** | 2 failed |
| M9 | drop `sender = $agent` | **RED** | 1 failed |
| M10 | answer conjunct: drop DELIVERED-TO-ME | **RED** | 1 failed |
| M11 | answer conjunct: drop SAME-THREAD | **RED** | 1 failed |
| M12 | answer conjunct: `> question_seq` → `!= question_seq` (order-blind) | **RED** | 1 failed |
| M13 | report the NEWEST unanswered question, not the OLDEST | **RED** | 1 failed |
| M14 | `asked_at` fabricated at read time | **RED** | 1 failed |
| **M15** | **the derivation WRITES (stamps `to.seen_at` on the way past)** | **GREEN — PIN DID NOT FIRE** | 1 passed |

Every one of the brief's required attack points fired: the `IS NONE` guard (M1), the `out = $me`
ownership scope (M2), the note's write-once behaviour (M1+M3), `question` vs `grade` (M8), each of
the three answer conjuncts (M10/M11/M12), oldest-vs-newest (M13), `asked_at` read-back vs
fabrication (M14), and the four-way classification (M4/M5/M6/M7). **Positive control:** the
unmutated tree is 171 passed / 0 failed, so every RED above is attributable to the mutation.

### 3.2 Wave 2 — R1, the false gate, with its positive control

M15 raised the question: does `test_the_derivation_writes_NOTHING` see a WRITE, or only a ROW COUNT?
Its helpers are `_message_row_count` / `_edge_row_count`, both `SELECT count() … GROUP ALL`. I
injected four writes into `awaiting_answer` and ran the **WHOLE `[real]` leg** for each:

| leg | injected write | result |
|---|---|---|
| W1 | `UPDATE agent SET status = 'input_required' WHERE id = $agent` — **ruling 9's STRUCK stored state, verbatim** | **UNSEEN — 86 passed, 0 failed** |
| W2 | `UPDATE agent SET last_note = 'awaiting'` | **UNSEEN — 86 passed, 0 failed** |
| W3 | `UPDATE to SET seen_at = $now WHERE out = $agent` (silently marks the whole inbox seen) | **UNSEEN — 86 passed, 0 failed** |
| W4 | **POSITIVE CONTROL** — `CREATE message CONTENT …` (a NEW row, so the count moves) | **CAUGHT** — `FAILED …::test_the_derivation_writes_NOTHING[real]` |

W4 proves the pin fires; W1–W3 are therefore genuine negatives, not a blind instrument.
`agent.status = 'input_required'` is a legal value of the schema's own closed status vocabulary
(`_AGENT_STATUSES`), so W1 is not a contrived shape — it is precisely the build ruling 9 exists
to forbid, and the contract waves it through.

This is the repo's own **"A FAILURE MESSAGE THAT PROMISES A CHECK THE ASSERTION DOES NOT PERFORM
IS A FALSE GATE"** class (CLAUDE.md, P2 2026-07-14). The message is the spec its author believed;
the assertion is what the suite performs; the gap is the wrong build's door. **The shipped code is
correct — it writes nothing.** What is defective is the pin protecting the wave's load-bearing
structural property. The contract is IMMUTABLE for this wave (committed RED at `efef2b3`), so this
is an operator call: strengthen the pin (assert the AGENT ROW's own before/after content, or count
writes at the `_query` seam rather than counting rows) in 03b or as a follow-up packet, and pin the
class per repo law.

## 4. Concurrency — my own tally

`TestConcurrentAcksOfOneEdgeProduceExactlyOneWinner::test_sixteen_ackers_of_one_edge`, `[real]` leg,
20 fresh consecutive invocations (each mints its own database):

```
run 1..20: 1 passed, 1 deselected  (0.88s – 1.07s)
=> 20/20 GREEN, ZERO failures, ZERO re-rolls
```

Corroborated independently at 8-way outside pytest (§6 P9): `acked` × 1, `already_acked` × 7,
**1 distinct stamp, no `None`**.

## 5. Sharing proof — ROUTING IS NOT SHARING

**Static leg.** Bare, anchor-free grep over `messages.py` for `retr|conflict|can be retried|sleep|
jitter|backoff`: every hit is a docstring or a delegation comment. **No hand-rolled retry loop, no
backoff, no jitter, no conflict-string comparison exists in the module.** `_query` is a pure
delegation to `run_query`.

**Runtime leg — the one that actually discriminates.** A build where every seam routes through the
driver but matches the conflict locally once scored 839/0. So I drove both NEW call sites against a
scripted connection and MOVED `_txn._RETRYABLE_CONFLICT_MARKER`:

| leg | marker | error text | required | observed |
|---|---|---|---|---|
| L1 (positive control) | unmoved | live `"…can be retried"` | RETRY | `attempts=3`, completed ✅ |
| L2 | moved → `AUDIT-MARKER-MOVED` | new text | RETRY | `attempts=3`, completed ✅ |
| L3 (negative control) | moved | OLD live text | **NOT** retry | `attempts=1`, `SurrealStoreError` ✅ |

Identical 3/3 for `ack` and for `awaiting_answer` → **6/6, SHARING PROVEN.** L3 is what makes L2
meaningful: the behaviour genuinely FOLLOWS the marker rather than retrying everything.

**⚠ My own instrument lied first, and only the positive control exposed it.** The initial run
reported `SHARING NOT PROVEN` — every leg `attempts=1`, `raised TypeError`. The cause was my fake
raising `QueryError(text)` when the SDK signature is `QueryError(kind, message, code=0,
details=None)`. Had I written only the negative legs, I would have filed a false NO-GO. Recording it
because it is this repo's §"A PROBE NEEDS A CONTROL" law paying for itself inside the audit that
cites it.

## 6. My own frontier — live probes against the real store

Both probe scripts printed `messages.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/
loremaster/messages.py` before running.

- **P1 duplicate seq in ONE batch** → `['acked','already_acked','already_acked']`, all three stamps
  byte-identical, `acked_count=1 already_acked_count=2`. Matches the docstring exactly. **Unpinned** (R5).
- **P2 batch scale** — 62 requested (60 real + 2 forged) → 62 entries, **order preserved**,
  histogram `{acked: 60, unknown_message: 2}`. `seqs=[]` short-circuits before any query. The
  0 / 1 / large / duplicate axis is clean.
- **P3 SELF-ADDRESSED follow-up (R2).** asker asks on `t:self` → waiting ✅ (control). Asker then
  sends a follow-up on `t:self` addressed to `[itself, lead]` → **waiting becomes False: the asker
  ANSWERED ITSELF.** **P3b control:** the identical follow-up NOT self-addressed leaves the debt
  standing. The `[fake]` oracle implements the same rule, so no leg can see it — this is a SPEC
  fork, but the docstring's parenthetical states the opposite outcome as fact.
- **P4** a self-addressed QUESTION does **not** answer itself (its own edge carries `seq ==
  question_seq`, and the conjunct is strict `>`). Correct.
- **P5** `ack` does not touch `seen_at`; the acked message is still served by `drain(peek=True)` and
  still counted in `total_pending`, carrying its `acked_at` + `ack_note` (R7).
- **P6** no empty-`thread` rows are reachable through `send` (thread defaults to `session`), so the
  `str(... or "")` normalisation in the derivation is unreachable today.
- **P7 / P7b** ONE answer on a thread carrying TWO questions clears **both**; an answer landing
  BETWEEN two questions leaves the later one outstanding (`waiting = q4`) — ordering is respected,
  the discharge is thread-scoped (R6).
- **P8b EXPLAIN — every statement the two methods issue:**

  | statement | plan |
  |---|---|
  | `ack` #1 `SELECT id, seq FROM message WHERE seq IN $seqs` | **TableScan** ⚠ |
  | `ack` #2 CAS `UPDATE to … WHERE acked_at IS NONE AND out AND in IN` | IndexScan(`to_in_out`) |
  | `ack` #3 readback `SELECT in.id, acked_at FROM to WHERE out AND in IN` | IndexScan(`to_in_out`) |
  | `awaiting` Q1 `SELECT … FROM message WHERE question = true AND sender = $a` | **TableScan** ⚠ |
  | `awaiting` Q2 `SELECT in.thread, in.seq FROM to WHERE out = $a` | IndexScan(`to_out_seen_at`), **unbounded** |

  The `message` table carries **no** index on `seq` and none on `(question, sender)` —
  `_MESSAGE_FIELD_SPECS` declares fields only, and the sole indexes in the slice are `to`'s
  `UNIQUE(in,out)` and `(out, seen_at)`. R3/R4.
- **P9** 8-way concurrent `ack` outside pytest: 1 × `acked`, 7 × `already_acked`, **1 distinct
  stamp, no `None`**.

## 7. Code reading — what I attacked and could NOT break

- **The four-way disambiguation is sound.** `unknown_message` is separated BEFORE the CAS by a
  seq→id resolution, so a forged seq cannot read back as an idempotent re-ack (M4 RED). The
  follow-up SELECT drops only the `acked_at IS NONE` conjunct, so it is a strict superset of the
  CAS's matched set — `not_addressed` and `already_acked` are cleanly separated (M5 RED).
- **Write-once covers the note structurally**, not by a second guard: `SET` never reaches an
  unmatched row. M3 (adding an unguarded note write) fires the pin, so the property is attributable
  to the guard and not to luck.
- **The quantifier law holds**: `_ack_entries` walks `requested`, and `claimed` makes the
  first occurrence of a duplicate the winner. M7 RED.
- **Losers report the STORED stamp** (M6 RED), which is what makes the 16-way "one stamp" assertion
  meaningful.
- **Store-law compliance** (`docs/reference/surrealdb-31-capabilities.md`): no DDL is touched by
  this wave, so §1.1's `OVERWRITE`/`IF NOT EXISTS` rule is not in play. §3 is respected — every new
  statement is SINGLE-statement through `_query`, never a multi-statement `query()`. §5's ONE-driver
  rule is satisfied and proven by mutation (§5). §2's silent-`None`-projection trap is handled
  explicitly by `_stamps_by_message(require_stamp=True)` for CAS winners.
- **The one ordering wrinkle I found is R8**: `_ack_entries` tests `not in stored_stamps`
  (→ `not_addressed`) BEFORE `in won_stamps` (→ `acked`). A winner missing from the readback is
  therefore mislabelled `not_addressed` rather than `acked`. Unreachable without an edge
  disappearing between two statements on one connection. Filed as latent, same clause as #105.
- **Unexpected CAS return shapes**: a returned row with no `in` is silently `continue`d (would
  downgrade a win, see R8); a returned row with a missing/garbage `acked_at` raises
  `SurrealStoreError` via `_require_aware_utc` rather than swallowing a `None`. The loud direction
  is the right one.

## 8. Served prose

Bare, anchor-free sweep for retired stub language (`NotImplementedError`, "land here as",
"not implemented in 03a-1", "is packet 03a-2", "stays RED") across `*.py` and `*.md`. Every residual
hit, with an individual verdict — no wholesale classification:

| hit | verdict |
|---|---|
| `loresigil/loresigil/base.py` ×6, `loresigil/tests/test_voyage_batch.py:1467` | unrelated subsystem — non-issue |
| `docs/plans/v2/03a-1-comms-ledger-send.md:48,69` | historical packet spec, past state — correct as written |
| `docs/plans/v2/03a-2-comms-ledger-consume.md:17,49` | this packet's own entry-check description — correct as written |
| `docs/plans/v2/receipts/2026-07-23-packet03a1/*` ×2 | archived receipts, dated — correct |
| `docs/plans/v2/INDEX.md:45,834` | Log/state-of-record; :45 is now stale (R10) |
| `docs/plans/v2/INDEX.md:807` | Log entry, past-tense — correct |
| `REPORT-builder-03a2.md` ×5 | the builder's own report describing what it replaced — correct |
| `messages.py` | **zero** — the stale SCOPE paragraph was correctly rewritten |

Two prose problems remain, both in `messages.py`:
- **R2** — `awaiting_answer`'s *"so the asker's own follow-up on its own thread is not an answer"*
  is falsified by P3.
- **R9** — the SCOPE HISTORY's *"Receipts for both waves are archived under
  `docs/plans/v2/receipts/`"* is true for 03a-1 (`2026-07-23-packet03a1/`) and NOT YET true for
  03a-2, whose report is untracked at the repo root. It becomes true at the lead's close-out
  `git mv`; until then the module ships a claim about the tree that the tree does not support.

And **R10**, outside the wave's file but sitting in the tree now: `INDEX.md`'s state-of-record still
reads `@ b32839b` with `test_message_ledger.py` at 140 passed / 31 failed — three commits behind
`ac38246`, where it is 171 / 0.

## 9. What I tried and did NOT find

For completeness, since a clean audit that lists its attacks is worth more than one that lists none:
no defect was found in — the empty-batch short circuit; batch ordering at scale; the
`acked_count`/`already_acked_count` arithmetic under duplicates; the `AckOutcome` constants (all four
are annotated and no raw outcome literal survives in `_ack_entries`); `asked_at` timezone coercion;
the `question`/`grade` orthogonality in both directions; `sender` scoping; another agent's question
never parking me; the KNOWN BOUND pins and their re-open trigger; the retry-seam enumerator's reach
(29 `MessageLedger` legs collected in `test_retry_seam.py`); `mypy`/`ruff` cleanliness of the new
code; and the module's continued non-import of `loremaster.agents` (the deliberate decoupling holds).
