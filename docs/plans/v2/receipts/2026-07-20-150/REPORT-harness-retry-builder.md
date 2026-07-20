# REPORT — harness-retry-builder (finding #150)

brief-base v5 read

## SUMMARY BLOCK

- **state:** done-with-deviations
- **deviations:**
  - Removed two now-unused module-level imports from the harness (`asyncio`,
    `surrealdb.errors.SurrealError`) — ruff F401 forced it. A NARROWING of the module-level
    import set, never a widening; RULING 1's guarantee is intact and now AST-pinned.
  - Added a 4th pin class beyond the brief's P1–P8 (`TestTheHarnessDeclaresNoRetryPolicyOfItsOwn`)
    asserting the three deleted policy constants stay deleted + an AST pin on RULING 1.
- **decisions-needed:**
  1. `connect_admin` / `drop_database` can now raise `TxnContentionExhaustedError` where they
     previously raised the engine's `QueryError`. Adjudicated **preserved-with-pin** but it IS a
     caller-visible type change across 21 test files — see §2 B3/B7. No consumer catches either
     type (verified, §2), so nothing broke; flagging because it is a public shape change.
  2. Teardown debuggability **does regress** — `retry_on_conflict` raises without `from`, so the
     engine's original text leaves the exception. I judged it acceptable and did NOT touch
     `_txn.py`. Your call whether it stays. §2 B4.
  3. `signin()` remains unretried at BOTH sites. It was not one of your three, and it is not
     conflict-class, but it is a bare `await` in the same two functions. §5 E1.
  4. A historical receipts doc still describes the deleted constants as live. Outside my
     writable set. §5 E2.
- **receipt pointers:**
  - removed-behaviour inventory + adjudication → §2
  - gate tails (every command, with passed-COUNTs) → §3
  - mutation-proof transcript (3 seam mutations + 1 wrong-build) → §4
  - escalations / out-of-scope observations → §5
  - commits `6be78d6` (RED) · `0734d78` (fix); `git status --short` = `?? scratchpad/` only → §3.6

---

## 1. What changed

Two commits, three files, **zero production changes** in the final diff.

```
loremaster/tests/_surreal_harness.py     | 159 +++++----
loremaster/tests/test_retry_seam.py      |  86 ++---
loremaster/tests/test_surreal_harness.py | 540 ++++++++++++++++++++++++++++---
3 files changed, 618 insertions(+), 167 deletions(-)
```

**Site 1 — `connect_admin` (`_surreal_harness.py:232`).** The three bare, unretried `await`s
(`DEFINE NAMESPACE` / `use()` / `DEFINE DATABASE`) are replaced by one call to
`_txn.bootstrap_session(connection, env.namespace, env.database)`. In-function import (RULING 1).

**Sites 2 & 3 — `drop_database`'s `use()` and `_remove_database_with_retry`.** Both route through
**one** new harness-local helper, `_run_under_store_retry_seam` — a function the two call sites
call, not a pattern cloned at each. It does classify-and-signal in the exact shape
`bootstrap_session`'s inner closures use (`_txn.py:997-1019`) and delegates to
`retry_on_conflict`. It owns **no budget, no backoff, no marker**.

**Deleted:** `_RETRYABLE_CONFLICT_MARKER`, `_MAX_DROP_DATABASE_ATTEMPTS`,
`_DROP_DATABASE_BACKOFF_SECONDS`, the private retry loop, and their three justifying comment
blocks.

**Prose corrected** (all four sites you named): the harness module docstring (import-isolation
restated accurately + why `_txn` is lazy), the three deleted comments, `test_surreal_harness.py`'s
docstring (which called the hand-rolled loop "THE FIX"), and `test_retry_seam.py`'s 7e block —
replaced by a short block recording **the operator's 2026-07-20 overturn explicitly**, that the
copy is gone, and that sharing is now proven by mutation rather than by an equality assertion.
`TestTheTestHarnessCannotDriftFromTheSeamsMarker` is deleted, exactly as its own failure message
instructed.

---

## 2. Removed-behaviour inventory, adjudicated item by item

Written before editing, from the deleted code — not from the brief's list. Your four are B1–B4;
B5–B10 are mine.

| # | Behaviour of the deleted code | Verdict |
|---|---|---|
| **B1** | Teardown bounded at **5 attempts** (`_MAX_DROP_DATABASE_ATTEMPTS`) | **preserved-with-pin, widened deliberately.** Now floor 5 / ceiling 64 / 2.0s deadline. The floor (`_MAX_TXN_CONFLICT_ATTEMPTS = 5`) is *exactly* the old budget, so the non-regression guarantee is byte-for-byte: teardown still gets ≥5 attempts regardless of wall clock (`_txn.py:895-897`, audit-102 B1). Pinned: `test_exhausting_the_seams_budget_raises_the_seams_exhaustion_type`, `test_both_paths_follow_the_seams_wall_clock_deadline`. |
| **B2** | **Linear 10ms backoff**, explicitly justified as needing no jitter ("teardown has ONE waiter") | **dropped-deliberately.** The justification was **false under the standing runner**: `-n auto` on a 64-core box means teardown has *many* waiters, all reaping databases on one shared server. Full jitter is strictly better here, and the comment asserting otherwise was itself a prose defect. (`CLAUDE.md` #102: a fixed delay puts every racer to sleep for the same duration and they re-collide in lockstep.) |
| **B3** | Exhaustion raised the engine's own **`QueryError`** | **preserved-with-pin, type CHANGED to `TxnContentionExhaustedError`.** Caller-visible. Justified: `TxnContentionExhaustedError` is a type a private copy *cannot* raise, which is what makes the sharing observable at all. **Verified no consumer breaks:** grepped every `_surreal_harness` importer (21 files) — the only code that caught the old type was `test_exhausting_all_attempts_on_sustained_conflict_raises`, which you directed me to rewrite. Every other consumer calls `drop_database` in a fixture `finally` with no `except`. Consumer sweep receipt: §3.5 (identical fail/error counts vs baseline). **→ decisions-needed #1.** |
| **B4** | The engine's original message rode **on the raised exception** (the old loop re-raised the caught `QueryError` itself) | **dropped — and it IS a regression.** `retry_on_conflict` raises `TxnContentionExhaustedError` **without `from`** (`_txn.py:920`); the engine text goes to the log record's `extra["engine_error"]` instead — and only when a `label` is passed, which neither of my two call sites nor `bootstrap_session` do (`_txn.py:909`). So on a sustained teardown conflict the operator now sees *"gave up after N attempts over Xs"* and **no engine text at all**. Judged acceptable: sustained teardown contention past 64 attempts has never been observed (the live rate is one conflict, retried once), and the alternative — passing `label=`/`url=` — is a `_txn.py` change I am not authorised to make and would only half-fix it. **I did not change `_txn.py`. → decisions-needed #2.** |
| **B5** | Caught **`SurrealError` only** | **preserved-with-pin, widened deliberately.** Now `_CONNECTION_ERRORS = (OSError, SurrealError, WebSocketException)` — the seam's own set, per your instruction to copy the `_txn.py:997-1019` shape. Widening only affects an `OSError`/`WebSocketException` that *also* carries the conflict marker; the classifier gates it either way, so a transport fault still propagates unretried. |
| **B6** | Retry covered the `REMOVE DATABASE` **only** — `use()` was outside it | **this was the bug; fixed.** Pinned: `test_a_conflict_on_teardowns_use_call_is_retried_then_succeeds`. |
| **B7** | `connect_admin` had **no retry and no budget at all** — a conflict propagated raw | **fixed; same type-change note as B3.** `connect_admin` can now raise `TxnContentionExhaustedError`. Pinned: `test_sustained_conflict_raises_the_seams_own_exhaustion_type`. |
| **B8** | Bootstrap **statement order**: `DEFINE NAMESPACE` → `use()` → `DEFINE DATABASE` | **preserved-with-pin.** `bootstrap_session` (`_txn.py:1021-1023`) issues the identical order. Pinned by an exact-sequence assertion on `_FakeConnection.operations`, because a fake that only counts calls would wave through a build that put `use()` first — which works against a fake and fails against the engine. |
| **B9** | Each teardown attempt got a **fresh** budget per call (the loop was per-`drop_database`) | **preserved.** `retry_on_conflict` is called per operation; `bootstrap_session` additionally *composes* one budget across its three statements — a tightening, deliberate upstream (`_txn.py:965-973`), not something I introduced. |
| **B10** | The drift pin guaranteed *"harness marker == seam marker"* | **preserved by construction, pin retired.** There is no second copy left to drift. Replaced by two strictly stronger mutation pins (`test_detection_follows_the_seams_one_conflict_marker`, `test_the_bootstrap_paths_detection_follows_the_seams_marker`) — an equality assertion between two literals is something a private copy satisfies *by definition*; a mutation is not. |

**Nothing was spec-silent; no item needed a ruling I could not make.** The two items I flag
(B3/B4) I adjudicated and am surfacing, not deferring.

---

## 3. Gates — every command with its passed-COUNT tail

### 3.1 Scoped suites
```
$ cd loremaster && uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q
420 passed, 1 warning in 11.31s
```
Baseline before my work (same command at `8c96451`): `407 passed, 1 warning in 11.12s`.
Delta `+13` = 17 new tests − 3 replaced − 1 retired drift pin. The 1 warning is pre-existing
(`test_retry_seam.py:3140`, an un-awaited coroutine in an unrelated scout pin).

### 3.2 RED receipt (before the fix, commit `6be78d6`)
```
$ uv run pytest tests/test_surreal_harness.py -q
13 failed, 4 passed in 0.57s
```
The 4 green were the three teardown pins that already held + the RULING-1 AST pin (which guards a
property the harness already had and had to keep).

### 3.3 Live store — the real engine, not the fake
```
$ uv run pytest tests/test_surreal_store.py tests/test_findings.py tests/test_txn_contention.py -q -n auto
353 passed in 13.80s
```
These drive `surreal_env` / `admin_db`, i.e. **`connect_admin` against the live engine**, hundreds
of times under `-n auto`. Target was spike-surreal (`systemctl --user is-active
spike-surreal.service` → `active`, ws://127.0.0.1:**18000**). Production :18500 was never touched.
Earlier isolated run: `tests/test_txn_contention.py -q -n auto` → `22 passed in 6.62s`.

### 3.4 mypy
```
$ ./scripts/typecheck.sh
Found 55 errors in 5 files (checked 146 source files)
```
**Zero of them are in my files** (`./scripts/typecheck.sh | grep -E "_surreal_harness|test_retry_seam"` → no output).
**Baseline established, not assumed:** I checked my three files out at `8c96451`, re-ran, and got
`Found 55 errors in 5 files` — identical. **Delta = 0.** The 55 are packet 03's committed RED
contract (`loremaster.messages` missing: `_message_fakes.py`, `test_comms_tool.py`,
`test_comms_promise_registry.py`, `test_message_ledger.py`, plus
`test_surreal_schema.py:425 generate_message_ddl`). I did not chase them.

Two mypy errors *were* mine mid-flight (`comparison-overlap` / `unreachable` on
`assert connection is fake` — `connect_admin`'s declared return is the SDK union, which
`_FakeConnection` is not). Fixed by dropping the redundant identity assert; the exact-sequence
`operations` assertion already proves the fake was driven.

### 3.5 Consumer sweep — the 21 files that import the harness
Because I changed a module 21 test files depend on, I ran all of them, **with a baseline**:

| tree | result |
|---|---|
| `8c96451` (before) | `61 failed, 1274 passed, 166 errors in 51.38s` |
| HEAD (`0734d78`)   | `61 failed, 1288 passed, 166 errors in 50.55s` |

**Identical failed and error counts; `+14 passed` = exactly my net new tests.** Zero regressions
across every harness consumer. The 61/166 are the known packet-03 RED floor
(`ModuleNotFoundError: loremaster.messages`) — not mine, not chased.

### 3.6 ruff + no production drift
```
$ uv run ruff check .
All checks passed!

$ git status --short
?? scratchpad/

$ git diff --stat HEAD
(empty)
```

---

## 4. Mutation-proof transcript

**Method (per your protocol):** work committed green FIRST (`6be78d6`, `0734d78`), then mutations
applied to the **real tree** — safe because it is committed and clean, so `git checkout --` restores
byte-exactly. **No `cp -a` scratch copy of the repo was made** (repo law #140), so there is no
`loremaster.__file__` provenance receipt to print — the mutations ran in the real checkout, which is
the always-sound alternative the law names. For the one harness mutation I additionally took a
`cp -a` **content** backup and proved byte-exact restoration by `diff`.

Seam file MD5 before any mutation and after every restore: `e67978f0dc474af17079ed9ee0c5cb1a`
(printed at the head of each mutation step — all three matched).

### M1 — move the shared conflict MARKER
`_txn.py:409` `_RETRYABLE_CONFLICT_MARKER = "can be retried"` → `"MUTANT: no engine says this"`
```
$ uv run pytest tests/test_surreal_harness.py -q
11 failed, 6 passed in 0.43s
```
RED: every retry pin on **both** paths — `connect_admin`'s three, all three teardown pins, and all
five sharing pins. The harness's notion of "conflict" moved with the seam's, which is only possible
if it has no copy.

### M2 — make the seam stop reading its own attempt CEILING
`retry_on_conflict`: `if attempts >= _TXN_CONFLICT_ATTEMPT_CEILING or (` → `if attempts >= 5 or (`
```
$ uv run pytest tests/test_surreal_harness.py -q
5 failed, 12 passed in 0.23s
FAILED ...::test_sustained_conflict_raises_the_seams_own_exhaustion_type
FAILED ...::test_exhausting_the_seams_budget_raises_the_seams_exhaustion_type
FAILED ...::test_the_bootstrap_path_follows_the_seams_attempt_ceiling
FAILED ...::test_the_teardown_path_follows_the_seams_attempt_ceiling
FAILED ...::test_both_paths_follow_the_seams_wall_clock_deadline
```
RED: exactly the five bound-following pins, and **only** those — the detection pins correctly stayed
green (detection was untouched). A mutation that reddens everything proves less than one that
reddens the right things.

### M3 — move the shared JITTER
`_txn_conflict_backoff_seconds` made to `raise RuntimeError('MUTANT: the seam's jitter was executed')`
on entry.
```
$ uv run pytest tests/test_surreal_harness.py -q
11 failed, 6 passed in 0.39s
```
RED: every pin whose path takes at least one retry. **Honest scope of this one:** it proves the
harness's retries *traverse the seam's backoff function* (reach), not that they honour its
*duration* — my sustained pins deliberately zero the backoff constants for speed
(`_silence_backoff`), so a duration mutation would be masked by that patch. Stated rather than
glossed. → §5 R1.

### W1 — the wrong build the pins exist to catch (ROUTING IS NOT SHARING)
Not a seam mutation: I mutated the **harness** into the precise #102-receipted wrong build — it
still calls `retry_on_conflict`, but hand-rolls its own literal match underneath:
```python
-            if is_retryable_conflict_error(error):
+            if "Resource busy" in str(error):
```
```
$ uv run pytest tests/test_surreal_harness.py -q
1 failed, 16 passed in 0.21s
FAILED ...::test_detection_follows_the_seams_one_conflict_marker
```
This is the build that scored *"839 passed / 0 failed — indistinguishable from correct"* in the
#102 measurement. **Here it is distinguishable.** Note the bootstrap-path marker pin did *not*
fire, correctly: `connect_admin` goes through `bootstrap_session`, which uses the seam's classifier
directly, so the harness helper is not in that path at all.

**W2 — a fully private retry loop** needs no separate run: that build is precisely HEAD before my
fix, and its receipt is §3.2 (`13 failed`).

### Restore + re-green
```
$ git checkout -- loremaster/loremaster/store/_txn.py     # after each of M1/M2/M3
$ md5sum loremaster/loremaster/store/_txn.py
e67978f0dc474af17079ed9ee0c5cb1a                          # matched, every time

$ git checkout -- loremaster/tests/_surreal_harness.py    # after W1
$ diff /tmp/_surreal_harness.py.backup loremaster/tests/_surreal_harness.py
IDENTICAL

$ git status --short
?? scratchpad/
$ git diff --stat HEAD
(empty)

$ uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q
420 passed, 1 warning in 11.31s
$ uv run pytest tests/test_surreal_store.py tests/test_findings.py tests/test_txn_contention.py -q -n auto
353 passed in 13.80s
$ uv run ruff check .
All checks passed!
```

### Per-pin mutation proof
Every pin in `TestTheHarnessRetryPolicyIsTheSeamsPolicy` **is** a mutation proof — it mutates a seam
constant and asserts the harness's observed attempt count moves, **each with a positive-control leg**
running the identical assertion at the unmutated value, so a pin that had stopped discriminating
cannot hide behind a green mutated leg. The remaining pins were proven by the RED phase (§3.2) plus
M1/M2/M3 above; the mapping mutation → pins-reddened is the FAILED lists in each step.

**Fixture interrogation — "what wrong build would this still pass?"** Three answers changed the
fixtures: (a) a build that reorders `use()` before `DEFINE NAMESPACE` passes any call-counting fake
→ added the exact-sequence `operations` assertion; (b) a build with a private 7-attempt budget would
match a mutated ceiling of 5 or 64 by coincidence → `_MUTATED_ATTEMPT_CEILING = 7`, which is neither
the seam's ceiling, nor its floor, nor the deleted copy's budget; (c) a build agreeing with the seam
on one constant by luck → the deadline pin drives a *second, independent* axis (the attempt FLOOR),
and asserts `ceiling != floor` first so it cannot pass on a degenerate coincidence. I also checked
every assertion against its own failure message for the false-gate defect this repo has shipped; the
messages claim only what the assertions check.

---

## 5. ESCALATIONS and out-of-scope observations

**E1 — `signin()` is unretried at both sites (in-file, not in your three).**
`_surreal_harness.py:239` and `:301` both `await connection.signin(credentials)` bare. Not
conflict-class (auth, not a write-write race), so the seam's classifier would decline it anyway and
wrapping it would be routing-without-purpose. But it is a bare `await` in the same two functions I
just hardened, and a transport flake there fails the fixture exactly as the bootstrap flake did.
**Raising, not deciding.** The `_txn` seam has no signin helper, so closing this would be a `_txn.py`
change — outside my writable set.

**E2 — a receipts doc still describes the deleted constants as live.**
`docs/plans/v2/receipts/2026-07-19-packet03/REPORT-recon-pkt03.md:414` states teardown *"retries up
to `_MAX_DROP_DATABASE_ATTEMPTS = 5` (`:106`) … linear backoff `0.01s * attempt` (`:112`),
unjittered (one waiter)"*. All four claims are now false. It is a **dated historical receipt** of a
past recon, so my read is that it should stand as written — but this repo's law is that prose
contradicting code is a defect class, and it is outside my writable set either way. **Your call.**

**E3 — `probe_sequence_txn_concurrency.py` cites the deleted harness constant.**
`scratchpad/102-recovery/probe_sequence_txn_concurrency.py:4` names
`_surreal_harness._RETRYABLE_CONFLICT_MARKER` in a docstring. Scratchpad, untracked, not executed by
any gate. Noting for completeness only.

**R1 — residual: no pin asserts backoff DURATION.**
My sustained-conflict pins zero the seam's backoff constants for speed, so they pin the *give-up
bound* and the *classifier*, but not that the harness sleeps for the seam's jittered interval. M3
proves the harness *reaches* the seam's jitter function; nothing proves it honours its magnitude. I
judged a timing assertion not worth the flakiness it would buy in a suite that runs `-n auto` on 64
cores. Flagging it as a known, deliberate bound rather than leaving it implicit.

**R2 — the harness now takes a 0.3s import cost on first `connect_admin`/`drop_database` call.**
Measured by you, restated: importing `_txn` pulls `loremaster`, `loremaster.store` (empty
`__init__`), `loremaster.store._txn` — no path to `loremaster.messages`, which is why the packet-03
RED floor does not spread into the harness (confirmed empirically: identical error counts in §3.5).
Paid once per process, in-function.

**Ledger:** I did **not** resolve finding #150 (yours after the audit), did not deploy, did not
touch the 180-test RED floor, and did not touch any file outside the writable set.

**Tool honesty:** I loaded lore's tools but answered every structural question in this task by
direct `Read` and `grep` — the consumer sweeps here are rename/deletion **exhaustiveness** questions
(one missed site compiles-but-breaks) and non-symbol textual seams (a marker literal, prose in
docstrings), which are two of the three cases the project CLAUDE.md names as honest grep fallbacks.
Saying so out loud per §4 of the base protocol. No lore friction to file.
