brief-base v6 read

# REPORT — builder-03a2 · packet 03a-2 (comms ledger: CONSUME path)

## SUMMARY BLOCK

- **state: done-with-flags** — `ack` + `awaiting_answer` implemented in
  `loremaster/loremaster/messages.py`; the WHOLE 03a contract is green.
- **Gate 1** `uv run pytest loremaster/tests/test_message_ledger.py -n auto -q` →
  **`171 passed, 9 skipped in 6.96s`** (RED baseline before this wave: `31 failed, 140 passed,
  9 skipped`). ⚠ **The brief's stated exit "180 passed / 0 failed / 9 skipped" is
  arithmetically impossible** — 140+31+9 = **180 PINS TOTAL**, so a fully green run is
  171 passed + 9 skipped. Nothing is missing; the brief conflated pins-total with passed-count.
- **Gate 2** `test_retry_seam.py -n auto -q` → **`503 passed, 1 warning`** (pre-existing
  `coroutine '_empty_subscription' was never awaited` warning, not mine).
- **Gate 3** `./scripts/typecheck.sh` → **`Found 36 errors in 3 files (checked 148 source files)`**
  — IDENTICAL to the lead-measured baseline; **0 errors in `messages.py`**, 0 in any production file.
- **Gate 4** `uv run ruff check .` → **`All checks passed!`**
- **Proof A — 16-way ack concurrency, 20/20 GREEN** on the final tree (§Proof A; loop command
  pasted). Zero failures, zero re-rolls.
- **Proof B — mutation proof, `SHARING PROVEN 10/10 legs`** (§Proof B): both new call sites
  FOLLOW the moved shared conflict marker and draw from the shared backoff; paired controls
  in both directions.
- **Proof C — my own build mutation-proven, 10/10 mutations caught RED** (§Proof C), with a
  green control leg and a byte-exact content restore (md5 equal, `read_text()` equal).
- **decisions-needed:** (1) duplicate seq inside ONE ack batch is UNPINNED — I matched the fake;
  (2) an explicitly SELF-ADDRESSED follow-up clears the asker's own debt (fake does this too);
  (3) two unindexed table scans; (4) a plan doc was modified in the tree by someone else
  mid-run. All in §Flags.
- **receipt pointers:** §Proof A / §Proof B / §Proof C / §Gates / §Flags below. NO commit, NO
  deploy, NO test edits. Ledger `96f9f3a0…` driven `claimed → in_progress` (left there for the
  lead's cold audit, per brief).

---

*(Everything below measured 2026-07-23 on this box, against `spike-surreal ws://127.0.0.1:18000`
— the TEST store; `:18500` was never touched. Working tree at parent commit `2dc077d`.)*

## What changed

ONE file, `loremaster/loremaster/messages.py` (+270/−23):

| symbol | what |
|---|---|
| `_ACK_OUTCOME_ACKED` / `_ALREADY_ACKED` / `_UNKNOWN_MESSAGE` / `_NOT_ADDRESSED` | the four outcome values as constants, each **annotated `AckOutcome`** so a drift from the closed Literal is a TYPE ERROR at the declaration, not a served string nobody can match on |
| `MessageLedger.ack` | the write-once CAS + four-way disambiguation (was `NotImplementedError`) |
| `MessageLedger._resolve_message_ids` | seq → bare message id, ONE set-based read |
| `MessageLedger._stamps_by_message` | index edge rows by message id, carrying `acked_at`; shared by the CAS return and the follow-up SELECT |
| `MessageLedger._ack_entries` | the quantifier-law walk: every REQUESTED seq gets its own fate, in request order |
| `MessageLedger.awaiting_answer` | ruling 9's read-time derivation (was `NotImplementedError`) |
| module docstring | the §SCOPE paragraph claiming both methods "land here as `NotImplementedError` stubs" was **stale prose the moment I landed them** — rewritten as scope HISTORY. (Repo law: natural-language surfaces whose consistency with code no gate checks are where green-at-gate defects cluster.) |

Nothing else in the repo was edited. No test file, no schema, no DDL, no deploy, no commit.

### `ack` — three set-based statements, never a per-seq loop

1. `SELECT id, seq FROM message WHERE seq IN $seqs` — separates **`unknown_message`** BEFORE the
   CAS, so a forged seq can never read back as an idempotent re-ack.
2. `UPDATE to SET acked_at = $acked_at, ack_note = $ack_note WHERE acked_at IS NONE AND out = $agent
   AND in IN $message_ids` — the guard does the work; because `SET` never reaches an unmatched row,
   **write-once covers the NOTE as well as the stamp** for free. Its returned rows are the CAS
   WINNERS, carrying the value actually stored.
3. `SELECT in.id AS message_id, acked_at FROM to WHERE out = $agent AND in IN $message_ids` —
   separates **`not_addressed`** (no edge) from **`already_acked`** (an edge whose stamp someone
   else's — or an earlier call's — CAS won), and supplies the **STORED** stamp to every loser, so
   all 16 racers observe one identical `acked_at`.

The fourth ambiguous condition (never-ran-due-to-conflict) is killed by `_query` → `run_query` →
`retry_on_conflict`, proven by mutation in §Proof B — **not by inspection**.

`seqs=[]` short-circuits with zero queries and an honest empty result.

### `awaiting_answer` — derived, writes nothing

Two reads, no write:
`SELECT thread, seq, created_at FROM message WHERE question = true AND sender = $agent`
(the column, **never `grade`** — they are orthogonal), then
`SELECT in.thread AS thread, in.seq AS seq FROM to WHERE out = $agent`.
A question is answered iff some **delivered-to-me** message shares its **thread** and has a
**greater `seq`** — all three conjuncts separately mutation-proven below. Oldest unanswered wins;
`asked_at` is the question row's own `created_at`, read back.

**Why `seq` and not `created_at` for "after".** `seq` is the engine-minted monotonic ordering key;
`created_at` is stamped in Python by the sending ledger, so under concurrent senders on separate
connections two `created_at`s can invert relative to `seq`. `seq` is the ordering authority and is
what `_message_fakes.FakeMessageLedger.awaiting_answer` (my oracle) uses. Stated because it is a
choice, not an inevitability.

## Gates

```
$ uv run pytest loremaster/tests/test_message_ledger.py -n auto -q
171 passed, 9 skipped in 6.96s

$ uv run pytest loremaster/tests/test_retry_seam.py -n auto -q
503 passed, 1 warning in 8.07s

$ uv run ruff check .
All checks passed!

$ ./scripts/typecheck.sh
Found 36 errors in 3 files (checked 148 source files)
typecheck: loremaster FAILED
   -> grouped: 31 test_comms_tool.py · 3 test_comms_promise_registry.py · 2 test_message_ledger.py
   -> loremaster/loremaster/**: ZERO. messages.py: ZERO.
   -> identical to the lead-measured baseline; the 36 are the forward-reference errors the
      operator ruling defers to 03b's end.
```

RED→GREEN receipt: the same Gate-1 command before any edit returned
`31 failed, 140 passed, 9 skipped in 8.29s` — the 13 `ack` + 18 `awaiting_answer` `[real]`-leg pins,
failing at the two `NotImplementedError` stubs.

Per brief-base §3 I did **not** run the full repo suite (the brief named the scoped set). I
therefore make **no claim** about repo-wide failures outside these two files.

## Proof A — 16-way ack concurrency, 20 consecutive runs

```bash
green=0; fail=0
for i in $(seq 1 20); do
  if timeout 300 uv run pytest \
      "loremaster/tests/test_message_ledger.py::TestConcurrentAcksOfOneEdgeProduceExactlyOneWinner::test_sixteen_ackers_of_one_edge" \
      -q -p no:randomly 2>&1 | tail -1 | grep -q "^2 passed"; then green=$((green+1));
  else fail=$((fail+1)); echo "RUN $i FAILED"; fi
done; echo "TALLY: green=$green fail=$fail / 20"
```
```
FINAL-TREE TALLY: green=20 fail=0 / 20
```
`2 passed` per run = the `[real]` and `[fake]` legs. One run's tail, verbatim, so the grep is not
taken on faith:
```
..                                                                       [100%]
2 passed in 0.91s
```
Run TWICE at 20/20: once on the first green build, and again on the FINAL tree after a typing
cleanup (`dict[str, datetime | Any]` → `dict[str, datetime | None]`). **Zero failures, zero
re-rolls** — no run was discarded.

## Proof B — the two new call sites SHARE the retry driver (mutation, not inspection)

Probe: move the ONE shared conflict marker (`_txn._RETRYABLE_CONFLICT_MARKER`) and the ONE shared
backoff (`_txn._txn_conflict_backoff_seconds`), then watch whether `ack`'s CAS `UPDATE` and
`awaiting_answer`'s questions `SELECT` move with them. Marker vocabulary is QUOTED from the repo's
own seam pins (`test_retry_seam.py::_MUTATED_MARKER` / `_LIVE_CONFLICT_TEXT`), not invented.
A scripted connection fails the ONE target statement twice, then succeeds.

```
PROVENANCE: loremaster.messages.__file__   = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/messages.py
PROVENANCE: loremaster.store._txn.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/store/_txn.py
shared marker (unmutated) = 'can be retried'

--- ack ---
  [PASS] A control: marker INTACT + live conflict -> retries         target_calls=3 raised=-                 retried=True
  [PASS] B MUTATION: marker MOVED + live conflict -> must NOT retry  target_calls=1 raised=SurrealStoreError retried=False
  [PASS] C MUTATION: marker MOVED + moved conflict -> must retry     target_calls=3 raised=-                 retried=True
  [PASS] D neg control: marker INTACT + ASSERT violation -> no retry target_calls=1 raised=SurrealStoreError retried=False
  [PASS] E jitter: draws from the SHARED backoff                     target_calls=3 draws=[1, 2]

--- awaiting_answer ---   (same five legs, same results)
  [PASS] A  target_calls=3 raised=-  · [PASS] B  target_calls=1 raised=SurrealStoreError
  [PASS] C  target_calls=3 raised=-  · [PASS] D  target_calls=1 raised=SurrealStoreError
  [PASS] E  draws=[1, 2]

VERDICT: SHARING PROVEN — 10/10 legs as expected
```

**Why each leg is load-bearing.** A private conflict matcher on the literal `"can be retried"`
passes A and D and **fails B** (it would keep retrying words the shared authority no longer calls a
conflict) **and C** (it would not recognise the moved words). A private backoff passes A–D and
records **zero** draws in E. D is the negative control: an ASSERT violation is refused
immediately, so the probe is not "everything retries". A is the positive control in the unmutated
world, proving the harness can SEE a retry at all.

**HONEST LIMIT:** this proves the two new call sites consult the shared marker and the shared
backoff. It does not (and cannot) make text-keyed conflict detection robust to a real engine
rewording — the repo's own seam contract states that bound, and finding #111 records why a typed
check is not yet available.

The probe ran as a standalone script; it edits no repo file and needs no scratch copy (it
monkeypatches `_txn` in-process), so #140's three poison modes do not apply — but the two
`PROVENANCE:` lines above are printed as the tree receipt regardless. Full source is inlined in
§Appendix so it is reproducible without a `/tmp` address (repo law: never cite a `/tmp` path).

## Proof C — my own build, mutation-proven against the contract

Break the production code one anchor at a time; the NAMED pin must go RED. Content backup taken
FIRST with `shutil.copy2` (an md5 list is a detector, not a backup — 2026-07-14 near-miss);
restore is from CONTENT; byte-exactness proved after.

```
content backup md5 2e881b07cf96e0312b1e9a32299ff09a
[CONTROL] unmutated build, all target pins: rc=0 :: 24 passed in 3.11s
[RED ✓] drop the write-once guard (acked_at IS NONE)                       2 failed, 2 passed
[RED ✓] drop the ownership scope (out = $me) from the CAS                  1 failed, 1 passed
[RED ✓] not_addressed branch made unreachable                              1 failed, 1 passed
[RED ✓] quantifier law: silently drop a seq with no fate                    1 failed, 1 passed
[RED ✓] derive from `grade` instead of `question` (the #94 shape)          2 failed, 2 passed
[RED ✓] report the NEWEST unanswered question instead of the oldest        1 failed, 1 passed
[RED ✓] drop the AFTER-the-question conjunct                               1 failed, 1 passed
[RED ✓] drop the ON-THE-THREAD conjunct                                    1 failed, 1 passed
[RED ✓] answer = any message on the thread (asker can answer ITSELF)       1 failed, 1 passed
[RED ✓] fabricate asked_at at READ time                                    1 failed, 1 passed

restored md5 == pristine: True     byte-exact restore: True
VERDICT: 10/10 mutations caught by the contract
```
The `N failed, N passed` shape is the `[real]` leg going RED while the (unmutated) `[fake]` leg
stays green — i.e. the pin discriminates on the backend I changed, exactly as intended.
The `[CONTROL]` line is the leg that stops this from being a probe that fires for the wrong
reason: the same 24 pins are green on the unmutated build.

## Flags — everything I noticed (the operator owns scope; I only escalate)

1. **UNPINNED: a seq repeated inside ONE ack batch.** The contract never exercises
   `seqs=[5, 5]`. `_message_fakes.FakeMessageLedger.ack` loops per-seq, so its first occurrence
   wins and the rest read `already_acked`. A naive set-based build would report **`acked` twice**
   — two winners for one CAS. I matched the fake (a `claimed` set in `_ack_entries`), because the
   fake is the designated oracle and "two winners" is the shape the whole section exists to
   forbid. **This is a real contract gap, not a preference**: nothing pins it, so a future
   refactor can silently flip it. Suggested pin for 03b/the cold audit:
   `ack(seqs=[s, s])` → `["acked", "already_acked"]`, `acked_count == 1`.
2. **UNPINNED and design-relevant: an explicitly SELF-ADDRESSED follow-up clears the asker's own
   debt.** `test_a_message_the_ASKER_sends_on_its_own_thread_is_not_an_answer` sends to
   `SENDER_LEAD`, so nothing is delivered to the asker and the pin passes. If the asker names
   ITSELF as a recipient on the question's thread, that message IS "delivered to me, on the
   thread, after the question" — so both my build and the fake treat it as an answer. The
   contract's `test_an_EXPLICIT_self_addressed_send_IS_delivered` shows self-addressing is legal,
   so this is reachable. It is arguably wrong (an agent can clear its own debt), and arguably
   right (a self-note is information). **Operator/03b call — I implemented the fake's behaviour
   and did not invent a fourth conjunct.**
3. **Two unindexed table scans I could not fix (schema is outside my writable set).**
   `SELECT id, seq FROM message WHERE seq IN $seqs` (ack) and
   `SELECT … FROM message WHERE question = true AND sender = $agent` (awaiting_answer) have no
   supporting index — `_MESSAGE_FIELD_SPECS` declares none, and `generate_message_ddl` emits
   indexes only on the `to` edge. The `to`-side reads ARE covered by the `(out, seen_at)`
   composite's `out` prefix. At current volumes this is invisible; at production message volume
   `awaiting_answer` is on the hot comms path. **The edit I would make** (if granted the schema):
   add `_plain_index(MESSAGE_TABLE, "message_seq_idx", ("seq",))` and
   `_plain_index(MESSAGE_TABLE, "message_sender_question", ("sender", "question"))` to
   `_message_statements`. Note store reference §1.1: index DDL stays `IF NOT EXISTS`, and a NEW
   index on a POPULATED table BUILDS — so this belongs in a deliberate packet, not a drive-by.
4. **A plan doc changed in the working tree during my run, and it is not mine.**
   `git status` shows `M docs/plans/v2/03a-2-comms-ledger-consume.md` — a rewrite of the closing
   line's task id (`618cd45d` → `b7f89c12`, citing finding #174). I did not touch it and left it
   alone. Raised because I was told the tree was clean at spawn: another writer is live in this
   checkout, which matters for whoever stages the commit.
5. **`awaiting_answer`'s two reads are not one snapshot.** An answer landing between the questions
   SELECT and the deliveries SELECT can make the call report "waiting" for a debt just settled.
   Self-correcting on the next read, and it errs in the direction ruling 9's KNOWN BOUND already
   declares SAFE (a false-waiting is visible beside a fresh `heartbeat_at`; a false-not-waiting is
   invisible). Flagged, not fixed — fixing it means one `execute_transaction`, which buys a
   snapshot at the cost of a transaction on a pure read path. **Operator call.**
6. **The brief's exit arithmetic** — see the summary block. `180` is the PIN TOTAL (140+31+9), not
   a passed-count; a green run is `171 passed, 9 skipped`. If the lead's cold audit greps for
   "180 passed" it will find nothing and read that as a miss.

## Tool honesty

lore was first choice and answered the consumer-set question: `lore_impact` on
`MessageLedger.awaiting_answer` → **0 production references / 18 test references**, `direct_consumers: []`
(with its own bare-name-fallback caveat, and the standing astroid-bounds caveat). I **cross-checked
with grep** — an exhaustiveness question where one missed site matters, which repo law names as an
honest grep case — and the only `.ack(` hits in production are `server.py`'s `brief_ledger.ack`, a
different ledger. Both instruments agree: **nothing outside the contract consumes these two methods
today**, which is what makes 03a-2 test-only and 03b the surface that ships them.

Grep was also used for the non-symbol textual sweeps (the stale "`NotImplementedError` stubs"
docstring prose, the schema field specs) — textual seams the graph does not model.
No lore friction encountered, so nothing filed.

## Appendix — the Proof-B probe, inlined

Reproduce with `uv run python -` from the repo root (it imports the installed `loremaster`, prints
its own provenance, and exits non-zero if any leg misbehaves). Abridged to the mechanism; the four
`leg(...)` invocations per method are A/B/C/D as tabulated above.

```python
import loremaster.store._txn as txn_module
from loremaster.messages import MessageLedger
from surrealdb.errors import ErrorKind, InternalError, QueryError

LIVE = "Transaction conflict: Resource busy. This transaction can be retried"
MOVED_MARKER = "the writer may take another turn"          # test_retry_seam.py::_MUTATED_MARKER
MOVED = f"Row is presently occupied; {MOVED_MARKER}"

# a connection that fails ONE target statement `failures` times, then answers by shape
class ScriptedConnection:
    def __init__(self, target, error, failures): ...
    async def query(self, statement, params=None):
        if self.target in statement and (self.target_calls := self.target_calls + 1) <= self.failures:
            raise self.error
        return self._rows(statement)          # canned rows per statement prefix

# ONE leg: optionally MOVE the shared marker, run the method, observe retry-or-raise
original = txn_module._RETRYABLE_CONFLICT_MARKER
txn_module._RETRYABLE_CONFLICT_MARKER = MOVED_MARKER        # THE MUTATION
...  await ledger.ack(agent_id=..., seqs=[1], note="probe")
txn_module._RETRYABLE_CONFLICT_MARKER = original

# leg E: the SHARED backoff — a private jitter records ZERO draws
txn_module._txn_conflict_backoff_seconds = lambda n: (draws.append(n), 0.0)[1]
```

Targets: `ACK_TARGET = "UPDATE to SET acked_at"` (the CAS) and
`WAIT_TARGET = "SELECT thread, seq, created_at FROM message"` (the derivation's first read).
Assertion per leg: `retried == expected_retry`, and every non-retrying leg must raise
`SurrealStoreError` specifically — a leg that raised something else fails even with the right
retry count, so "did not retry" cannot pass for the wrong reason.
