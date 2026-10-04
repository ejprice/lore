brief-base v18 read

# REPORT — implement-486-r3 (tdd-light GREEN, lore #486 round 3/3b, finding #534; 2026-10-04)

## SUMMARY BLOCK
- **State:** done-with-deviations. Measured 2026-10-04, 18:42–19:02Z, on the uncommitted #486 working tree over HEAD `773520c`.
- **Result:** the round-3/3b contract reds are all GREEN: 12/12 cells of `TestTheSessionEndReapNeverCostsPytestItsVerdict`, controls included. 0 GREEN→RED. The outer run prints 0 `LEAKED` lines and 0 unreachable/failed-reap lines.
  - BEFORE: `9 failed, 870 passed`.
  - AFTER: `1 failed, 878 passed`.
  - The 1 red that remains is NOT this change. It was red in BEFORE too, and the runner causes it (§Counts, F1).
- **Deviations:**
  1. **Lifted to the class.** A non-transport reap failure (a wrong-shaped `INFO`, contention exhaustion) is ALSO caught, named in its own line, and propagated under xdist. The contract does not pin this (§Class).
  2. **A gate incident, no test impact.** My first post-edit probe stalled because its gate self-matched its own shell (the brief-base §5.5 class). I killed it by PID before pytest started, so that run never executed. Every run that did execute printed `GATE CLEAR` first (§Gate).
- **Packages considered:**
  - Bounded reap: `asyncio.timeout`/`wait_for` (stdlib) and `concurrent.futures.ThreadPoolExecutor`. I read the installed `concurrent/futures/thread.py`: `threading._register_atexit(_python_exit)` joins its workers at exit. Verdict: `bespoke` — ~15 lines, a daemon `threading.Thread` with `join(timeout)` (§Bound).
  - Transport classification: `replace` → REUSED `loremaster.store._txn._SDK_AWAIT_BOUNDARY_ERRORS` + `is_connection_error`.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 4 new conftest symbols, all dispositioned (§DRY). There are 0 new harness module-level names, and the D-r2b-1 allowlist pin passes.
- **Graded:** n/a — implementation, not a verdict. HEAD-at-report `773520c`.
- **Decisions needed:** (D-r3-1) see §Readings. "Reap only what was OPENED" has two readings. I took (A): the store is dialed only if a minted DB was opened, and the candidate set is unchanged. There is also one new bound consequence for the operator to accept.
- **Receipts:** §Changes · §Bound · §xdist path · §Counts · §Loud-line receipts · §Gates · §Gate · §Flags

## Capability check (brief-base §4)
- grep/rg are hook-blocked (#473; `grep` inside a pipeline was blocked once more this run by the lore-checkout hook): every text scan used awk.
- I ran one `lore_search` for an existing bounded-coroutine helper. It found none (§DRY).
- I did NOT register on comms (`lore_comms`), to protect the 60-minute deadline. The lead gets the one micro-format line.
- **Backups:** `cp -a` of both writable files, made before any edit:
  - `conftest.py` md5 `f2024e35…`;
  - `_surreal_harness.py` md5 `aaf41b8f…`.

  These match coldaudit-486's recorded hashes.
- **Test files are unchanged** (md5 recorded before the edits):
  - `test_harness_database_lifecycle_486.py` `472d6ec8…`;
  - `test_surreal_harness.py` `2c04d7a4…`.
- No git mutation, no commit. TEST store `:18000` only.

## Changes (by symbol)
### `loremaster/tests/conftest.py`
- **`_DATABASES_OPENED_THIS_SESSION: set[str]`** (new). It is filled by the existing `_record_database_selection` `use()` observer next to the per-test list, so every opened `TEST_NAMESPACE` database is recorded for the whole session.
- **`pytest_sessionfinish`:**
  - The store is dialed only when `_DATABASES_OPENED_THIS_SESSION & _MINTED_DATABASES.keys()` is non-empty. A name-only session never touches the store (#534 cell a).
  - The reap runs through `_reap_within_budget(_SESSION_END_REAP_BUDGET_SECONDS)` and never raises out of the hook.
  - On a failure it records `(outcome, cause, databases)`. `databases` = the minted DBs this session opened that are not marked reaped, sorted.
  - It reads ONE registry snapshot (`dict(_MINTED_DATABASES)`), because an abandoned reap thread may still be writing to the registry.
  - Under xdist, the worker writes BOTH reports into `workeroutput`.
  - On the terminal owner, the session fails (`TESTS_FAILED`) when there are leaks OR failed reaps.
- **`_reap_within_budget`** (new): runs `reap_minted_databases()` on its own event loop in a daemon thread, joins with the budget, and returns `None`, the raised exception, or `TimeoutError("no answer within the 30s session-end reap budget")`.
- **`_reap_failure_outcome`** (new): returns `"unreachable"` iff `isinstance(error, _SDK_AWAIT_BOUNDARY_ERRORS) and (isinstance(error, KeyError) or is_connection_error(error))`; otherwise `"failed"`. Both pieces are `_txn`'s own. The budget's `TimeoutError` is an `OSError`, so the same classifier covers it.
- **`pytest_testnodedown`**: also merges `_UNREAPED_REPORT_WORKEROUTPUT_KEY`.
- **`_unreaped_line`** (new) + **`pytest_terminal_summary`**: ONE line per outcome kind, merged across workers:
  - `TEST store <url> unreachable at session end (<causes>) — could not verify that N test database(s) this session opened were removed: <names>. …`;
  - or `session-end reap failed against the TEST store <url> (<causes>) — …`.
- **New constants:**
  - `_UNREAPED_REPORT_WORKEROUTPUT_KEY`;
  - `_SESSION_END_REAP_BUDGET_SECONDS = 30.0`;
  - `_STORE_UNREACHABLE = "unreachable"`, `_REAP_FAILED = "failed"`;
  - `_UNREAPED_AT_SESSION_END`.
- **Prose (R4 items 2, 3):**
  - The block comment now states the raw-`DEFINE DATABASE` bound (no `use()`, so the observer never sees it; no live test does it). It also states the bound this change WIDENS (§Readings).
  - "2186" → "(2186 measured 2026-09-26, contract-486 M2)".
  - "the one door every test database passes through" → "the door every test database a test SELECTS passes through".
- Import: `threading`.

### `loremaster/tests/_surreal_harness.py` (docstrings only; module-level names unchanged)
- **`_run_under_store_retry_seam` (R4 item 1):** "…outside an attempt body handed here — except the one exempt forwarding instrument it names in `_REACH_EXEMPT_FUNCTIONS` (`measure_store_traffic`)". I verified that `test_surreal_harness._REACH_EXEMPT_FUNCTIONS = frozenset({"measure_store_traffic"})`.
- **Module docstring, "Lifetime (#486)":** the reap now runs only when a test opened a mint, and under a hard time budget. An unreachable store at session end fails the session and names the DBs. Without this edit, the docstring would have over-claimed an unconditional reap.

## Bound — the value and why
- **Value:** `_SESSION_END_REAP_BUDGET_SECONDS = 30.0`, one wall-clock budget for the whole session-end reap.
  - A healthy reap takes well under 1 s: connect, `INFO`, the reader's drop.
  - The store seam's per-operation conflict deadline is `_txn._TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS = 2.0`.
  - So 30 s covers bootstrap + INFO + the reader drop + about a dozen worst-case contended removals.
  - It sits below websockets' keepalive (~20 s + 20 s), so a muted store ends at OUR bound, not at a dependency default. Receipt: muted ended at 30.6 s with cause `no answer within the 30s session-end reap budget`.
- **Why a thread, and not `asyncio.timeout`:** cancelling the reap runs its `finally`, which does `connection.close()` and then `drop_database(reader_env)` (a fresh `connect_admin`). Those awaits hit the same silent store and are not cancelled a second time, so an in-loop timeout is not a bound.
- **Why not `ThreadPoolExecutor`:** its workers are joined at interpreter exit (installed source, see the SUMMARY), so a hung reap would hang the process after pytest's verdict.
- **Daemon-thread consequence:** the abandoned thread is frozen at interpreter exit. No traceback was seen in any of the 6 lost-store sessions (§Loud-line receipts).
- ⚠ **Bound, stated:** a HEALTHY but slow reap that takes more than 30 s (for example, many leaks under sustained contention) is reported as "unreachable … no answer within the 30s budget". The session still fails loudly and names the DBs, and the cause text says it was the budget. **Re-open trigger:** a budget-timeout line on a session whose store was demonstrably up.

## xdist propagation path
1. The worker's `pytest_sessionfinish` (inside the worker process) gets a failed reap.
2. It writes `workeroutput["lore_534_unreaped_test_databases"] = json.dumps([(outcome, cause, [db…])])` beside the existing leak key, and returns without raising. Raising was the swallowed path, i.e. the false clear.
3. execnet carries it to the controller.
4. The controller's `pytest_testnodedown(node, error)` merges it into `_UNREAPED_AT_SESSION_END`. testnodedown runs inside the controller's runtest loop, before its own `pytest_sessionfinish`.
5. The controller's `pytest_sessionfinish`: its own `_MINTED_DATABASES` is empty, so it dials nothing. It sees `_UNREAPED_AT_SESSION_END` non-empty and sets `TESTS_FAILED`.
6. `pytest_terminal_summary` prints the one line.

This is the same channel as round 1's leak report. Receipt: `refused/silent/muted × xdist-n2` all ended rc 1 with the line (§Loud-line receipts).

## Readings (brief-base §2: two readings, both written down)
- **"Reap only what was OPENED":**
  - **(A) TAKEN:** the store is dialed iff a minted DB was opened this session. When it is dialed, the reaper's candidate set is unchanged (every mint, intersected with `INFO`).
  - **(B):** restrict candidates to minted ∩ opened. That needs a harness signature change, and it reaches strictly less.
  - Both pass the contract.
- ⚠ **Consequence for the operator, under either reading:** a database opened by a higher-scoped (session/module) fixture is not observed: the guard is per-test, a pre-existing bound, and no such fixture mints today (coldaudit-486 §1i). Before #534 the unconditional reap would still have removed it. Now it goes unreaped in a session where no TEST opened a minted DB. This is stated in the conftest block comment. **Re-open trigger:** the first non-function-scoped fixture that mints a test database.
- **Which names the loud line carries:** opened ∩ minted, not marked reaped. An opened-AND-dropped DB (the D1 residual) is listed too, because with the store down it cannot be verified. That is why the line says "could not verify … were removed", not "leaked".

## Class (deviation 1)
- **Lifted property:** ∀ session-end reap failure, the session's verdict is non-zero, names the unverified DBs, and has no raw traceback, in both runner modes.
- Before this change, the `-n 0` path raised (traceback). Under xdist, a worker raise was swallowed (rc 0). That held for ANY reap exception, not only connect errors: for example `map_of`'s F3 `SurrealStoreError` and `TxnContentionExhaustedError`.
- These now get the `"failed"` line. They are deliberately NOT labelled "unreachable", because the store answered.
- **Unpinned:** the contract pins only the transport states. Recommendation: one contract cell with a fake `INFO` shape at session end, under `-n 0` and xdist.
- ⚠ `KeyError` is classified "unreachable" because it is the SDK boundary atom (a socket dropped under an in-flight request, store reference §3). A KeyError raised by a BUG in the reaper itself would be mislabelled as unreachable. It would still be loud and still fail the session.

## Counts (targeted; same tree; same command; BEFORE on the backup-identical tree, AFTER with the edits)
Command:
`systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider -rfE`

Files:
- `test_harness_database_lifecycle_486.py`;
- `test_surreal_harness.py`;
- `test_no_raw_listener_in_test_trees.py`;
- `test_retry_seam.py`;
- `test_memory_replay_fidelity_63b_ib.py`;
- `test_comms_wiring.py`.

| run | gate printed | result | red set |
|---|---|---|---|
| BEFORE | `GATE CLEAR 18:42:52Z MemAvailable=20GiB other_lore_pytest=0` | `9 failed, 870 passed, 1 warning in 152.79s`, RC=1 | the 8 declared round-3/3b cells (a)[refused-n0], (a)[silent-n0], (c)[refused/silent/muted × n0/xdist-n2], **+ F1** |
| AFTER | `GATE CLEAR 18:59:58Z MemAvailable=20GiB other_lore_pytest=0` | `1 failed, 878 passed, 1 warning in 111.44s`, RC=1 | **F1 only** |
| LEG-4b probe | `GATE CLEAR 18:54:36Z MemAvailable=22GiB` | `12 passed in 37.08s`, RC=0 | none |

- **Arithmetic:** 870 + 9 = 879 = 878 + 1. 8 RED→GREEN, 0 GREEN→RED. The 4 controls/xdist-name-only cells were GREEN in BEFORE and stay GREEN.
- **Outer loud lines:** `LEAKED` = 0 in both runs. Unreachable/failed-reap lines = 0 in both runs (awk count).
- **The 1 warning** is identical in both runs and pre-existing: `test_retry_seam.py:3263: RuntimeWarning: coroutine '_empty_subscription' was never awaited`.
- **F1:** `test_no_raw_listener_in_test_trees.py::TestPluginPortFixturesAreForbidden::test_the_running_session_registers_no_plugin_fixture_the_derivation_missed` fails with `AssertionError: no installed third-party fixture registered in this session — the live leg sees nothing`. It was red in BEFORE, before my edits.
  - **Inference (MEDIUM):** the worker interpreter is uv's ephemeral `--with` environment (`/home/ejprice/.cache/uv/builds-v0/.tmp…/bin/python`, from the log). Its plugins are then not classified as "installed third-party" by that file's `_is_installed_third_party`.
  - A confirming run without `--with pytest-timeout` is §F1-check below.

### F1-check
See the appended result at the end of this report.

## Loud-line receipts (scratch driver reusing the contract's own helpers; each DB removed after)
Measured 2026-10-04 at ~18:56Z (gate CLEAR 18:56:05Z, MemAvailable 20 GiB).

```
== refused workers=None rc=1 1.6s   TEST store ws://127.0.0.1:47657/rpc unreachable at session end (ConnectionRefusedError: [Errno 111] Connect call failed ('127.0.0.1', 47657)) — could not verify that 1 test database(s) this session opened were removed: test_1998824_…   | 1 passed in 0.65s
== refused workers=2    rc=1 2.6s   … unreachable at session end (ConnectionRefusedError …) …                                   | 1 passed in 1.65s
== silent  workers=None rc=1 11.6s  … unreachable at session end (TimeoutError: timed out during opening handshake) …           | 1 passed in 10.66s
== silent  workers=2    rc=1 12.6s  … (TimeoutError: timed out during opening handshake) …                                     | 1 passed in 11.73s
== muted   workers=None rc=1 31.6s  … (TimeoutError: no answer within the 30s session-end reap budget) …                      | 1 passed in 30.64s
== muted   workers=2    rc=1 32.6s  … (TimeoutError: no answer within the 30s session-end reap budget) …                      | 1 passed in 31.71s
```
- **Note:** silent ends at websockets' 10 s open timeout, which is shorter than our budget. Muted ends at OUR budget.

The driver is pasted verbatim (brief-base §1 instrument rule; not committed). Run it from the repo root as `uv run python show_loud_line.py <tmpdir>`:
```python
"""Print the inner session's loud line + rc + duration for each lost state x runner (receipt only)."""
import asyncio, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, "loremaster/tests")
import test_harness_database_lifecycle_486 as contract

async def main() -> None:
    for state in contract._LOST_STORE_STATES:
        for workers in (None, contract._XDIST_WORKERS):
            tmp = Path(tempfile.mkdtemp(dir=sys.argv[1]))
            kill, ack = tmp / "k", tmp / "a"
            started = time.monotonic()
            with contract._KillableStoreForwarder(kill, ack, lost_state=state) as forwarder:
                session = contract._run_inner_session(
                    tmp, contract._INNER_OPENS_THEN_LOSES_THE_STORE, workers=workers,
                    extra_environment={"LORE_TEST_SURREAL_URL": forwarder.url,
                                       contract._KILL_SWITCH_ENV: str(kill), contract._KILLED_ACK_ENV: str(ack)},
                    timeout_seconds=180)
            elapsed = time.monotonic() - started
            lines = [l for l in session.output.splitlines() if "unreachable" in l.lower() or " passed" in l]
            print(f"== {state} workers={workers} rc={session.returncode} {elapsed:.1f}s created={session.created}")
            for line in lines:
                print("   ", line[:400])
            await contract._remove_if_present(*session.created)

asyncio.run(main())
```

## Gates
- **`uv run ruff check .`** → `All checks passed!`.
- **`ruff format --check`:**
  - `conftest.py` is formatted.
  - `_surreal_harness.py` "would reformat", and so would the pre-edit backup, so the drift is pre-existing. The diff hunks are code lines I did not touch (`SurrealConnection = (…)`, a generator in the class registry). My edits are docstring-only, and I did not reformat (that would be an unrelated diff).
- **`uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`:**
  - typecheck `RED_ADJUDICATED — 83 residual(s)`, owned by packet-58-contract and packet-64b-i-contract (the same 83 coldaudit-486 measured);
  - ruff `GREEN`;
  - `pytest NOT_RUN` is the known #533 scoped-legs line.
  - **RED_ORPHANED 0** for typecheck and ruff.
- **`scripts/typecheck.sh`:** 0 `error:` lines name `conftest.py` or `_surreal_harness.py` (awk filter, empty output).
- **D-r2b-1 allowlist:** the harness diff is two docstring hunks, with no module-level binding added. The pin `test_the_harnesss_module_level_names_are_exactly_the_allowed_set` is inside AFTER's 878 passed.

## Gate (brief: "CONFIRM the gate printed clear")
- Every pytest run above printed `GATE CLEAR` before it started; the lines are quoted in §Counts.
- ⚠ **One incident.** My first post-edit probe (`$S/gate.sh && …pytest…`, issued inline) waited 8 minutes with MemAvailable at 23 GiB. The gate's `ps … awk '/[p]ytest/ && /lore/'` matched my OWN parent `bash -c` command line, which contained the word "pytest". That is brief-base §5 item 5 (lore #228).
  - I killed it by PID (1977491). It exited 143 and **pytest never started**. That log file does not exist.
  - The gate now matches only processes whose `comm` is `python*`/`pytest*`: `ps -eo pid,comm,args | awk '$2 ~ /^(python|pytest)/ && /pytest/ && /lore/'`.
  - The BEFORE run was unaffected: it launched via a script path, not an inline command line.
- The gate instrument, verbatim (scratch, not committed):
```bash
for i in $(seq 1 900); do
  avail_kib=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
  # Only real python/pytest processes (comm), never a shell whose command line merely CONTAINS the word.
  others=$(ps -eo pid,comm,args | awk '$2 ~ /^(python|pytest)/ && $0 ~ /pytest/ && $0 ~ /lore/' | wc -l)
  if [ "$avail_kib" -ge $((20*1024*1024)) ] && [ "$others" -eq 0 ]; then
    echo "GATE CLEAR $(date -u +%H:%M:%SZ) MemAvailable=$((avail_kib/1024/1024))GiB other_lore_pytest=0"; exit 0
  fi
  sleep 2
done
```

## DRY ledger
| new symbol | query run | returned | disposition |
|---|---|---|---|
| `_reap_within_budget` | lore_search "run a coroutine in a separate thread with a hard wall-clock timeout, abandoning it if it hangs" | `test_scout._run_briefly` (an in-loop task cancel — not a bound across a `finally`, for the reason in §Bound); SurrealDB docs noise | HAND-ROLLED (stdlib `threading`; see Packages considered) |
| `_reap_failure_outcome` | read `loremaster.store._txn` (`_CONNECTION_ERRORS`, `_SDK_AWAIT_BOUNDARY_ERRORS`, `is_connection_error`, `_raise_attempt_failure`) | the boundary atom + the transport classifier | **REUSED** both. ⚠ The composite `KeyError or is_connection_error` is `_raise_attempt_failure`'s fate-1 test **composed again here**: `_txn` has no named predicate for it, and `_txn.py` is outside my writable set. FLAG: extract `is_transport_fault(error)` in `_txn` and call it from both places. |
| `_unreaped_line` | — (a format routine local to the existing `pytest_terminal_summary`) | — | HAND-ROLLED, conftest-local |
| `_DATABASES_OPENED_THIS_SESSION` | — | — | **EXTENDED** the existing `_record_database_selection` observer (one added line); no second hook |

## Flags (everything noticed)
1. **F1** (above): runner-shaped red in `test_no_raw_listener_in_test_trees.py` under `uv run --with pytest-timeout`. If the F1-check confirms it, every brief that mandates `--with pytest-timeout` shows this red. Owner: the lead / that file's owner. Not attributable to #486.
2. **DRY:** a `_txn` predicate is owed (§DRY row 2).
3. **Unpinned class leg:** the non-transport session-end failure (§Class).
4. **Widened bound:** an unobserved higher-scoped fixture's DB (§Readings).
5. A worker that dies in `pytest_sessionfinish` BEFORE writing `workeroutput` (for example, a bug in this hook) would still be swallowed. `pytest_testnodedown`'s `error` argument is not inspected. Not pinned; not changed (no test). Recommendation: the controller treats `error is not None` from a node as a failed session.
