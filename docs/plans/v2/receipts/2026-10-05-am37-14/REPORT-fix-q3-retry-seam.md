brief-base v18 read · brief project v7 read

# REPORT — fix-q3-retry-seam (am-37 §14 Q3, test-only fix)

## SUMMARY BLOCK
- **State:** done-with-deviations (two, both below; neither touches production)
- **Deviation 1 (brief step 4 as worded would be a FALSE GATE):** `filterwarnings("error::RuntimeWarning")` ALONE does not redden a never-awaited coroutine (measured; the test PASSES). Applied BOTH `error::RuntimeWarning` + `error::pytest.PytestUnraisableExceptionWarning`. That is the "or equivalent" the brief allowed. §B.
- **Deviation 2 (spec §14 "exhausted iterator" fork):** an EMPTY iterator leaves the `async for` body (`_drain_pending`) unexecuted, so the brief's required mutation could never go red. The fake now yields ONE notification, and a 2nd assertion pins `query` calls == 4. §C.
- **Packages considered:** none — no mechanism specified (test fixture shape + pytest's own `filterwarnings` marker).
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** 1 renamed test-private fixture (`_empty_subscription` → `_one_notification_subscription`), no new reusable symbol. §F.
- **Graded:** n/a (builder). Built on HEAD `7fc90a9` · HEAD-at-report `7fc90a9` · SAME
- **Decisions-needed:** none blocking. 1 flag for #539 (§E): with this fix, NO test in `test_retry_seam.py` reaches `_consume_live`'s non-awaitable branch.
- **Receipts:** SDK shape §A · filter probe §B · before/after §D · mutation proofs §D2/§D3 · sibling sites §E · gates §G · final md5 `c70986938466c6161cba7410e30e3c29`

Capability check: everything demanded was available. Fallbacks: the PreToolUse hook blocks `grep`/`rg` in the main checkout. I used lore (`lore_get_symbol`, `lore_search`), Python `inspect`, and a Python line-scan for the textual site sweep. The sweep was a non-symbol textual seam (`suppress(`, `subscribe_live`), which is grep-honest case (b). Said here per the dogfood protocol; no friction filed, since the lore tools answered the symbol questions.

## A. The SDK's real shape (step 1). Read from the installed BODY, not production's comment
Installed `surrealdb` **2.0.0** (`.venv/lib/python3.14/site-packages/surrealdb/connections/async_ws.py`, `AsyncWsSurrealConnection.subscribe_live`, source line 482 at measurement 2026-10-04):
```python
    async def subscribe_live(
        self, query_uuid: str | UUID
    ) -> AsyncGenerator[dict[str, Value], None]:
        result_queue: Queue[dict[str, Any]] = Queue()
        suid = str(query_uuid)
        if suid not in self.live_queues:
            self.live_queues[suid] = []
        self.live_queues[suid].append(result_queue)

        async def _iter() -> AsyncGenerator[dict[str, Any], None]:
            while True:
                ret = await result_queue.get()
                yield ret["result"]

        return _iter()
```
`inspect.iscoroutinefunction` → True, `isasyncgenfunction` → False. **A coroutine that RETURNS an async generator, one level.** This matches §14's reading, which §14 rated MEDIUM because it was taken from production's comment; it is now re-derived from the body. All three async classes the SDK exports agree:
- `AsyncWsSurrealConnection` uses the body above.
- `AsyncEmbeddedSurrealConnection` inherits that same `async_ws.py:482` method.
- `AsyncHttpSurrealConnection` inherits `AsyncTemplate.subscribe_live` (`async_template.py:380`), which is a coroutine that raises `NotImplementedError`.

So no async SDK class returns a bare generator. Brief condition "if the SDK shape differs, STOP" → it does not differ; proceeded.

## B. The warning filter. `error::RuntimeWarning` alone is a FALSE GATE (measured)
Probe (scratch `probe/`, lore venv, pytest 9.0.3, CPython 3.14.7, `asyncio_mode=auto`), pasted verbatim per §1:
```python
import pytest
async def _coro(): return 1
@pytest.mark.filterwarnings("error::RuntimeWarning")
async def test_dropped_coroutine_with_filter():        # → PASSED (!)
    c = _coro(); del c
@pytest.mark.filterwarnings("error::RuntimeWarning")
@pytest.mark.filterwarnings("error::pytest.PytestUnraisableExceptionWarning")
async def test_dropped_coroutine_both_filters_MUST_FAIL():   # → FAILED  ✔
    c = _coro(); del c
@pytest.mark.filterwarnings("error::RuntimeWarning")
@pytest.mark.filterwarnings("error::pytest.PytestUnraisableExceptionWarning")
async def test_awaited_coroutine_both_filters_control_MUST_PASS():  # → PASSED ✔ (control)
    assert await _coro() == 1
@pytest.mark.filterwarnings("error::pytest.PytestUnraisableExceptionWarning")
async def test_dropped_coroutine_unraisable_only():    # → PASSED (!)
    c = _coro(); del c
```
Results: run 1 gave `2 passed` for the RuntimeWarning-only test and the no-filter test. Run 2 gave `1 failed, 2 passed`, where the failure is the both-filters case. Mechanism: the "never awaited" warning is raised inside the coroutine FINALIZER. Turned into an error there, it becomes an *unraisable* exception, and pytest re-issues it as `PytestUnraisableExceptionWarning` (non-fatal by default). **So the spec's and the brief's literal step 4 would have shipped a pin that cannot fire.** I applied both markers, with a comment above the test stating why. Recorded as lore memory `6583a4ff-…` (kind gotcha).

## C. The fork in §14 (two readings, written down per brief-base §2)
§14's fix text says `_empty_subscription` "becomes a plain function returning `_iterator()`" (still EMPTY), and then says *"`_drain_pending` then meets the fake's `query`, which conflicts 3× and answers `[]`"*.
- **Reading 1 (literal):** keep the iterator empty. Then the `async for` body NEVER runs, and `_drain_pending` is never called. The parenthetical is false, and the success leg stays dead, apart from the `async for` protocol itself. The brief's required mutation ("make the `async for` body raise, or skip `_drain_pending`") would stay GREEN, so the proof could not be produced.
- **Reading 2 (chosen, matches the spec's stated intent and the brief's receipt):** the iterator yields ONE notification and then ends. The body runs once, so `_drain_pending`'s SELECT meets the fake (3 conflicts + 1 success = 4). A second assertion pins `query == 4`.

Same shape as the SDK (coroutine → async generator). Ending after one item is a termination bound; the SDK's generator is `while True`. Notification content is `{}`, because production binds it to `_notification` and never reads it. I did not invent an SDK notification schema.

## D. Before / after / mutation receipts
All runs went through the waiting gate (MemAvailable ≥ 20 GiB AND no other lore pytest; script in §H). Each was cgroup-capped: `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300`. Each run used no store beyond whatever the file's own live-store tests use (`:18000` via the harness, never `:18500`).

**D1. Before / after (whole file `loremaster/tests/test_retry_seam.py`):**
- BEFORE (HEAD `7fc90a9`, file md5 `003d8583fecbb656dff4d3d15329574a`): `678 passed, 1 warning in 12.42s`. The warning was:
  `test_retry_seam.py::TestEverySdkCallSiteActuallyRetries::test_scouts_live_subscription_is_retried — test_retry_seam.py:3263: RuntimeWarning: coroutine '_empty_subscription' was never awaited`
- AFTER (md5 `c70986938466c6161cba7410e30e3c29`): `678 passed in 13.95s`. **No warning line.**

**D2. Mutation proof that the success leg is live (FIXED test, real tree, `scripts/mutation_proof.py`).**
- Declared id, taken from `pytest --collect-only -q` BEFORE any mutated run: `loremaster/tests/test_retry_seam.py::TestEverySdkCallSiteActuallyRetries::test_scouts_live_subscription_is_retried`
- Anchor (exactly once in `scout.py`; the bare `await self._drain_pending(connection)` occurs 3×, so the anchor includes the preceding comment line): `double-dispatch.\n                await self._drain_pending(connection)\n`

| mutation | replacement | result | restored |
|---|---|---|---|
| M1 skip drain | `pass  # MUTATION M1` | `1 failed, 677 passed` — `AssertionError: the drain SELECT was attempted 0 time(s) after the subscription was obtained…` — `PROOF HELD — the declared RED set fired EXACTLY` | `scout.py` md5 `def55d2f2e8be6c810aa8a3281b145aa` (= HEAD) |
| M2 body raises | `raise RuntimeError("MUTATION M2: success leg broken")` | `1 failed, 677 passed` — `RuntimeError: MUTATION M2: success leg broken` — `PROOF HELD` | `def55d2f…` (= HEAD) |

The tool exited 0 for both runs. `scout.py` md5 before and after both runs is `def55d2f2e8be6c810aa8a3281b145aa`.

**D3. The OLD test (HEAD's version) stays GREEN under the same mutations. This is the defect, demonstrated.**
This leg ran in a `./scripts/scratch_copy.sh` tree, because `mutation_proof.py` requires a non-empty `--expect-red`. Provenance receipt: `loremaster.scout.__file__ = …/scratchpad/tree/loremaster/loremaster/scout.py` (inside the scratch). HEAD's test file was copied in (md5 `003d8583…` asserted). Each mutation was applied with an exact-once anchor assert and restored by content with an md5 check. The instrument, pasted verbatim:
```bash
#!/usr/bin/env bash
set -u
S=<scratchpad>; T=$S/tree
ID='loremaster/tests/test_retry_seam.py::TestEverySdkCallSiteActuallyRetries::test_scouts_live_subscription_is_retried'
cd "$T" || exit 2
cp "$S/test_retry_seam.py.HEAD" loremaster/tests/test_retry_seam.py
echo "test file md5 (must be HEAD's 003d8583…): $(md5sum loremaster/tests/test_retry_seam.py | cut -d' ' -f1)"
echo "provenance: $(uv run python -c 'import loremaster.scout as s; print(s.__file__)')"
cp -a loremaster/loremaster/scout.py "$S/scout.py.scratch-orig"
ORIG_MD5=$(md5sum loremaster/loremaster/scout.py | cut -d' ' -f1)
for M in none m1_skip m2_raise; do
  if [ "$M" != none ]; then
    uv run python - "$S/anchor.txt" "$S/repl_$M.txt" <<'EOF' || { echo "MUTATION $M DID NOT LAND"; exit 3; }
import sys
anchor = open(sys.argv[1]).read(); repl = open(sys.argv[2]).read()
path = "loremaster/loremaster/scout.py"; src = open(path).read()
assert src.count(anchor) == 1, f"anchor matched {src.count(anchor)} times"
open(path, "w").write(src.replace(anchor, repl))
assert repl in open(path).read()
EOF
  fi
  "$S/gate.sh" > /dev/null || { echo "GATE FAILED"; exit 4; }
  systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -q -p no:cacheprovider --timeout=300 "$ID" > "$S/old_leg_$M.log" 2>&1
  rc=$?
  cp "$S/scout.py.scratch-orig" loremaster/loremaster/scout.py
  [ "$(md5sum loremaster/loremaster/scout.py | cut -d' ' -f1)" = "$ORIG_MD5" ] || { echo "RESTORE FAILED"; exit 5; }
  echo "mutation=$M pytest_exit=$rc :: $(tail -1 "$S/old_leg_$M.log")"
done
```
Output:
```
test file md5 (must be HEAD's 003d8583…): 003d8583fecbb656dff4d3d15329574a
provenance: …/scratchpad/tree/loremaster/loremaster/scout.py
mutation=none pytest_exit=0 :: 1 passed, 1 warning in 4.39s
mutation=m1_skip pytest_exit=0 :: 1 passed, 1 warning in 2.00s
mutation=m2_raise pytest_exit=0 :: 1 passed, 1 warning in 1.99s
```
At HEAD, a build that obtains the subscription and then never drains (M1), or crashes while draining (M2), passes the pin.

## E. Same fake shape / suppress pattern elsewhere in this file (each site, verdict)
Located by a Python line-scan of `suppress|_empty_subscription|subscribe_live|filterwarnings|RuntimeWarning` (line numbers at HEAD `7fc90a9`). Symbols are given for durability.

| site (HEAD line) | what | verdict |
|---|---|---|
| 2611 `contextlib.suppress(Exception)` around `subscriber._consume_live(connection, live_uuid)` in the live-store SDK-guard reach pin (the test that drives every `_all_sdk_call_sites()` and checks `report.observed`) | REAL SDK connection; the real subscription never ends, so the 1.0 s `wait_for` must time out | **Not this class.** There is no fake, so no shape mismatch. The pin's claim is "the guard OBSERVED the call site", which a swallowed exception cannot fake, because observation is recorded at the call. ⚠ Residual: `suppress(Exception)` is broader than the `TimeoutError` it needs, so it would also hide an unbounded-retry or TypeError regression in that path. It could narrow to `suppress(TimeoutError)`. **Not changed** (different class, outside the brief's "same defect" rule). Flag for lead. |
| 2635 same pattern around `awaiter._consume_live(...)` (InboxAwaiter) | same as 2611 | Same verdict and same residual. |
| 2874 `_ScoutFakeConnection.subscribe_live` | raises `ConnectionResetError` (the failure shape, deliberately) | Fine: there is no success shape to mismatch. |
| 2917 / 2920 `suppress(Exception)` / `suppress(CancelledError, Exception)` in `_run_subscriber_until_recovered` teardown (`stop()`, `await task`) | teardown | Not this class. The assertion is on `dispatched`, outside the suppress. |
| 6539 another fake `subscribe_live` | raises `ConnectionResetError` | Fine. |
| 6606 / 6609 teardown suppresses (same idiom as 2917/2920) | teardown | Not this class. |
| 9687 `_ForeverConflictingSubscription.subscribe_live` | always conflicts; never succeeds | Fine (exhaustion pin, no success shape). |
| 3154/3163/3263 (the target) | — | **Fixed.** |

**Flag for #539 (production, not touched):** `scout._consume_live`'s comment says the test fake is "an async-generator FUNCTION", and §A shows no async SDK class returns a bare generator. With this fix, the only success-shaped fake in this file is also awaitable. So `_consume_live`'s non-awaitable path (`inspect.isawaitable(...)` False) is now reached by no test in `test_retry_seam.py`. I did not sweep other test files for it. This is input for #539's "is the branch dead" re-derivation; the comment is now false about the test fake as well.

## F. Reuse ledger
| symbol | lore query | returned | disposition |
|---|---|---|---|
| `_one_notification_subscription` (test-private fixture, replaces `_empty_subscription`, 1 caller) | `lore_search "_AllMethodsConflictConnection subscribe_live _empty_subscription fake"` path=test_retry_seam.py, plus a line-scan for `_empty_subscription` | the single fixture + its single call site | EXTENDED in place (same fixture, corrected shape and renamed, because "empty" would now be a false name). No new policy symbol. |

## G. Gates (2026-10-04, HEAD `7fc90a9` + this diff)
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` gave:
  - `typecheck RED_ADJUDICATED — 83 residual(s)`, owned by packet-58-contract and packet-64b-i-contract;
  - `ruff GREEN`;
  - `pytest NOT_RUN`, because pytest was deliberately excluded by `--legs` per CLAUDE.md. The tool prints it as an ORPHAN line and exits 1 because of that NOT_RUN.
  - **RED_ORPHANED: 0.**
- `scripts/typecheck.sh`: loremaster `82 errors in 31 files` + scripts `1 error`, = 83, matching the adjudicated count. **0 lines name `test_retry_seam.py`.**
- `ruff check loremaster/tests/test_retry_seam.py`: All checks passed.
- `ruff format --check` would reformat the file, but this was **already true at HEAD** (verified on HEAD's copy). The only formatter hunk inside my edit range is the unchanged `test_scouts_live_subscription_is_retried(` signature wrap, which is identical to its siblings. `ruff format` is not a manifested gate. Flagged, not changed.
- `git diff --stat`: `loremaster/tests/test_retry_seam.py | 54 +++++++++++++++++-------  1 file changed, 42 insertions(+), 12 deletions(-)`. `scout.py` is unchanged (md5 `def55d2f…` = HEAD).
- Final md5 of `loremaster/tests/test_retry_seam.py`: **`c70986938466c6161cba7410e30e3c29`**
- No commits, no stash, no worktree. Content backups of both files are in the session scratchpad (`*.HEAD`).

## H. Waiting-gate script (instrument, pasted)
```bash
#!/usr/bin/env bash
for i in $(seq 1 120); do
  avail_kb=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
  others=$(pgrep -fa '[p]ython.*-m pytest|[b]in/pytest' | awk -v me="$$" '$1 != me' || true)
  if [ "$avail_kb" -ge $((20*1024*1024)) ] && [ -z "$others" ]; then
    echo "GATE CLEAR: MemAvailable=$((avail_kb/1024/1024))GiB, no other pytest"; exit 0
  fi
  echo "GATE WAIT ($i): MemAvailable=$((avail_kb/1024/1024))GiB others=[$others]"; sleep 15
done
echo "GATE TIMEOUT"; exit 1
```
Every run cleared it on the first poll (MemAvailable 28–29 GiB).

## Not tried
- An in-situ positive control showing that the fixed test reddens with the OLD fake shape restored. With that shape, the `TypeError` would fire before the warning filter matters, so the control would test the suppress removal and not the filter. The filter itself is proven in §B.

## I. Fold-in (lead-ruled, 2026-10-04): narrow the §E residual suppresses to `TimeoutError`
**Summary:** done-with-deviation. Both sites are narrowed to `contextlib.suppress(TimeoutError)`. The positive control is GREEN on the live TEST store, and the whole file gives **678 passed**. The discriminating negative proof HELD at both sites, and the pre-narrowing control stayed GREEN. **Final md5 `5e417a8162071e5a240ee6bb21e25bd5`** (`test_retry_seam.py`; this supersedes the md5 in the summary block above). `scout.py` `def55d2f…` and `inbox_awaiter.py` `8e34c21f…` are unchanged from HEAD.

**I.1 "The two tests" is ONE test with two sites.** Both suppresses (HEAD lines 2611, 2635) are inside `TestNoSdkCallEscapesTheDriverAtRuntime::test_every_production_sdk_call_site_was_OBSERVED_by_the_guard`. Site 1 drives `CommandSubscriber._consume_live` (`scout.py`). Site 2 drives `InboxAwaiter._consume_live`, which is in **`inbox_awaiter.py`, not `scout.py`**. A `scout.py` mutation therefore proves only site 1, so I mutated each file separately, restoring byte-exact via `mutation_proof.py`. Only the test file was edited.

**I.2 The edit.** Site 1: `suppress(Exception)` → `suppress(TimeoutError)`, plus a 4-line comment citing the Q3 class. Site 2: the same narrowing, plus a one-line comment. On a healthy store, neither site needed a broader class: the positive control passed. So the STOP condition did not trigger.

**I.3 Positive control (live TEST store `:18000` via the harness; gate CLEAR; capped `-n 8`):** `-rA` shows `PASSED …::test_every_production_sdk_call_site_was_OBSERVED_by_the_guard`, not skipped; `678 passed in 13.04s`.

**I.4 DEVIATION: the suggested negative mutation ("raise RuntimeError on entry") does NOT discriminate. Measured, and replaced.**
- First attempt: the brief's example, a `raise RuntimeError` inserted before `_consume_live`'s `try`, in each file.
  - Fixed file: PROOF HELD for both (`1 failed`, restored byte-exact).
  - **Control** (pre-narrowing `suppress(Exception)` file, in the scratch tree): **also `1 failed` for both.**
  - The reason is the guard test's own reach assertion: `the runtime guard never EXECUTED 1 of 12 production SDK call sites … scout.py:566 (_attempt:subscribe_live)` (and `inbox_awaiter.py:256` for the awaiter). A raise on entry means `subscribe_live` is never called, so the reach leg reddens whatever the suppress catches.
  - **Those first two "PROOF HELD" receipts say nothing about the narrowing. They are discarded as evidence.**
- Discriminating mutation (I2): insert `raise RuntimeError("MUTATION I2-<n>: non-timeout raise AFTER subscribe_live")` immediately after `subscription = await retry_on_conflict(_attempt, label=…)`. The site is OBSERVED, and then a non-timeout exception escapes. `RuntimeError` is not in `_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION`, so production does not catch it. Each anchor matches exactly once.
  - Declared id, from `--collect-only` before the runs: `loremaster/tests/test_retry_seam.py::TestNoSdkCallEscapesTheDriverAtRuntime::test_every_production_sdk_call_site_was_OBSERVED_by_the_guard`.
  - The command is scoped to that node, because raising in `_consume_live` would also redden the Q3 test and the three `_scout_seam_exhaustion_record` label tests, which are other `_consume_live` callers.

| mutation | narrowed file (real tree, `mutation_proof.py`) | pre-narrowing file (scratch, control) |
|---|---|---|
| I2-scout (`scout.py`) | `RuntimeError: MUTATION I2-scout…` · `1 failed` · **PROOF HELD** · restored md5 `def55d2f…` | `1 passed` |
| I2-awaiter (`inbox_awaiter.py`) | `RuntimeError: MUTATION I2-awaiter…` · `1 failed` · **PROOF HELD** · restored md5 `8e34c21f…` | `1 passed` |

The scratch control asserted provenance with `scratch_copy.sh --verify-only`: both modules resolve inside `…/scratchpad/tree/…`. It ran on the pre-narrowing test file (md5 `c7098693…`, i.e. the post-Q3 file), and each mutation was restored by content with an md5 check. The instrument is §D3's `old_test_leg.sh`, re-parametrised: the HEAD copy became the pre-narrowing copy, and the loop runs over {scout.py, inbox_awaiter.py} with the I2 anchor/replacement files.

**I.5 Gates (2026-10-04, HEAD `7fc90a9` + this diff):**
- Whole file through the waiting gate: **`678 passed in 13.00s`**, no warnings.
- `ruff check`: All checks passed.
- `--currency --legs typecheck,ruff`: typecheck RED_ADJUDICATED (83, packet-58/64b-i owners), ruff GREEN, pytest NOT_RUN (excluded by `--legs`). **RED_ORPHANED 0.**
- `typecheck.sh`: 82+1 errors, **0 naming `test_retry_seam.py`**.
- `git diff --stat`: `loremaster/tests/test_retry_seam.py | 62 ++++++++++++-----  1 file changed, 48 insertions(+), 14 deletions(-)`.
- No commits, stash, or worktree. Backups are in the session scratchpad (`test_retry_seam.py.preI`, `inbox_awaiter.py.HEAD`).

**I.6 Lift (CLASS):** *a pin never suppresses the exception class it exists to notice; and a negative mutation must leave the pin's OTHER legs satisfied, or it proves the wrong leg.* The second clause is the measured lesson from I.4. A mutation that trips a sibling assertion reddens the test for a reason unrelated to the change under proof. Only the control leg exposed this.
