brief-base v16 read · brief project v7 read

# REPORT-close-466 — #466 final closing pass (R1 teardown leak, serve_http budget parity, one process-group runner, T1–T4)

## SUMMARY BLOCK
- **state:** done-with-deviations
- **deviations:** (1) item 2's fix was ALREADY in `8d42c27` (lead-applied, contradicting the refactor report's "(A) applied") — no test-first RED possible; proven by revert-mutation m2 instead (§Item 2). (2) item 3's pin was the lead's uncommitted addition; its comment cited a non-existent `§Addition-2` — repointed here. (3) added a class-completeness AST pin beyond the brief (CLAUDE.md "Fix the CLASS" landed mid-run) — §CLASS lift. (4) T1's declared-RED set under mutation t1 was too small (the prompt-shutdown controls also caught a zero-wait build) — recorded, and a subtler t1b proves the new leg is the sole asgi discriminator.
- **Packages considered:** `run_as_process_group` — stdlib `subprocess.Popen(start_new_session=True)`+`os.killpg`; `subprocess.run` READ at `/usr/lib/python3.14/subprocess.py:559` (kills the direct child only → cannot `replace`); `psutil` `keep_with_trigger` (trigger: a descendant that `setsid`s out of the group). No other mechanism.
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** 6 new symbols, all dispositioned (§DRY ledger): 3 EXTENDED in place, 2 HAND-ROLLED with reason, 1 test class reusing 8 helpers.
- **Graded:** `8d42c27`/`ceabe73` (the d1 tree as handed over) · HEAD-at-report: `6417e8f` · DIFFERENT (13 ahead, all docs/58/63c/64 — none touches the 5 in-scope files: `git diff --stat ceabe73 6417e8f -- <5 files>` empty)
- **decisions-needed:** (a) ledger vs. build a generated interrupt-injection sweep over `loopback.py`'s blocking waits (rec: ledger; trigger = a 4th blocking wait or a 2nd kind of process-global state) — §CLASS lift. (b) typecheck is RED on OTHER packets' uncommitted files (`scripts/test_forgery_door_sweep.py:42` `SupersedeResult`; 44 more across 19 loremaster-leg files of packets 58/63c/64b — derived from the final `typecheck.sh` run: `Found 44 errors in 19 files` + `Found 1 error in 1 file`) — owner/adjudication is the lead's.
- **receipts:** R1 RED→GREEN §Item 1 · item 2 m2 §Item 2 · item 3 RED→GREEN + m3 §Item 3 · T1–T4 + t1/t1b/t3/t4 §Item 4 · class pin + m4 §CLASS lift · final verify §Final verification (`124 passed`; ×5 `46 passed`; skills `120 passed`; ruff clean) · acceptance **20/20 ACCEPTED** §Acceptance.

---

## Capability check (brief-base §4)
- lore tools loaded (`ToolSearch "+lore"`); registered `lore_comms` as `close-466` (session `466`).
- grep/rg hook-blocked → awk/sed used for textual reads (said at each use).
- `lore_search` for the DRY check ran >120 s and was backgrounded (same shape as finding #500); it did return (see DRY ledger).
- Idle-gate contract written: `/tmp/claude-idle-gate-lore/unknown-close-466.contract` (no session id exposed to Bash).
- Base moved: brief said HEAD `8d42c27`; HEAD at start is `ceabe73` (docs-only, `REPORT-lead-63c.md`). No in-scope file differs between them.

## Pre-existing state found at start (2026-09-26, HEAD `ceabe73` + working tree)
- **Item 2's production change ALREADY landed in `8d42c27`**: `serve_http(..., shutdown_timeout_s=DEFAULT_SHUTDOWN_TIMEOUT_S)` threaded into `_loud_teardown`, and `TestServeHttpShutdownOverrunIsLoud` already uses `SHORT_SHUTDOWN_BUDGET_S` + a parity-default pin. This CONTRADICTS `REPORT-refactor-466-d1.md` §Pins-d ("Reading chosen … (A, applied) … no API change") — the lead applied reading (B) at commit time without a RED receipt. So for item 2 no test-first RED was possible; I prove the pins discriminate by REVERT-mutation instead (§Item 2).
- **Item 3's pin + seam were ALREADY in the working tree (uncommitted, lead addition)**: `ConcurrentPairDriver.collect_argv()` and `test_a_timed_out_collect_takes_its_whole_tree_with_it`. Its comment cited `REPORT-refactor-466-d1.md §Addition-2`, a section that does not exist in that report (dangling address) — repointed to this report (§Item 3).

## Item 3 — `expected_passed()` through the SAME process-group kill (ONE implementation)
- **Pin** (lead's, uncommitted at start): `scripts/test_concurrent_wire_acceptance.py::TestATimedOutSessionTakesItsWholeTreeWithIt::test_a_timed_out_collect_takes_its_whole_tree_with_it` — F12's depth-3 fake-child-tree fixture routed through `collect_argv`.
- **RED at `ceabe73`+tree, for the right reason** (tree built, return prompt, but orphans survive):
  ```
  E           AssertionError: 2 of 3 members of the timed-out --collect-only tree are still alive 5.0s later: [3218694, 3218695] — orphaned by expected_passed
  FAILED scripts/test_concurrent_wire_acceptance.py::TestATimedOutSessionTakesItsWholeTreeWithIt::test_a_timed_out_collect_takes_its_whole_tree_with_it
  1 failed, 2 passed in 11.61s
  ```
  (orphans reaped by the test's own `finally`; `ps -p 3218694,3218695` empty afterwards.)
- **Fix**: new `scripts/concurrent_wire_acceptance.py::run_as_process_group(argv, *, timeout_s)` — Popen with `start_new_session=True`; on `TimeoutExpired` kills the group (`_kill_process_group`), drains, re-raises with the partial output attached (same contract as `subprocess.run`); on any other `BaseException` kills the group and re-raises. `ConcurrentPairDriver._run_session` and `ConcurrentPairDriver.expected_passed` BOTH call it; the Popen block that lived in `_run_session` is gone (no copy #2). Tiny typed adaptor `_captured_text` (TimeoutExpired's `.stdout` is typed `str | bytes | None`).
- **GREEN**: `scripts/test_concurrent_wire_acceptance.py` → `23 passed in 6.59s`.
- **Sharing proven by MUTATION** (real tree, content backup `cp -a` → restore; md5 `5ffab4c7705dfec19ca2894491962ea7` before AND after): `_kill_process_group` body → `session.kill()` (direct child only). Declared RED before the run: the session F12 pin + the collect pin. Observed:
  ```
  FAILED ...::test_no_member_of_a_timed_out_session_tree_survives_the_round
  FAILED ...::test_a_timed_out_collect_takes_its_whole_tree_with_it
  2 failed, 21 passed in 240.95s (0:04:00)
  ```
  declared == observed — PROOF HELD, both directions (one shared function, both callers redden).
  (The mutated `_kill_process_group` leaves the grandchildren holding the pipes, so `communicate()` hangs until the fake tree's own ~120 s lifetime — hence 240 s; RED by the elapsed-bound leg, which is the "waited on the tree instead of killing it" assertion.)
- Lead's pin comment repointed from the non-existent `REPORT-refactor-466-d1.md §Addition-2` to this report's §Item 3; three of its message lines re-wrapped for ruff E501 (text unchanged).

## Item 1 — R1: `_UvicornServerThread.stop` detaches the capture even when the join is interrupted
- **Pin (new)**: `loremaster/tests/test_loopback_serving.py::TestAnInterruptedTeardownLeavesNothingBehind::test_the_interrupt_propagates_unchanged_and_nothing_is_left_behind` — parametrised `port_ownership ∈ {owned, passed}` × F1's `_UNEXPECTED_INTERRUPTS` (pytest-timeout-shaped `BaseException`, `KeyboardInterrupt`) = 4 cases. Same injection style as F1 (a `SIGALRM` handler raising in the MAIN thread); the shared helper was split so the interrupt can be AIMED: new `_main_thread_interrupt(make_error)` yields `(raised, arm)`, and F1's `_interrupt_main_thread_after` is now a 3-line wrapper over it (one implementation of the injection). The lifespan shutdown is held on a gate, the timer is armed as the body's LAST act, with `shutdown_timeout_s=GENEROUS_SHUTDOWN_BUDGET_S` (10 s ≫ `INTERRUPT_AFTER_S` 0.3 s, asserted).
  - Non-vacuity legs: fired exactly once; `excinfo.value is raised[0]` (propagates UNCHANGED); `0.9×0.3 s ≤ elapsed < 10 s` and `app.events == ["startup"]` (it landed IN the teardown wait, lifespan shutdown not complete).
  - Outcome legs: the process-wide logging-handler snapshot is unchanged; every thread the test started ends once the gate opens; the port (owned AND passed) refuses afterwards.
- **RED at `ceabe73`+tree, for the right reason** — every non-vacuity leg passed, the handler leg failed, and the leak ACCUMULATES across cases (`uvicorn.error` held 1, 2, 3, 4 `_ThreadErrorCapture`s):
  ```
  E   AssertionError: the interrupted teardown left a logging handler attached — ... after={... 'uvicorn.error': (<_ThreadErrorCapture (ERROR)>,)}
  FAILED ...TestAnInterruptedTeardownLeavesNothingBehind::test_the_interrupt_propagates_unchanged_and_nothing_is_left_behind[owned-pytest-timeout-shaped-BaseException]
  FAILED ...[owned-KeyboardInterrupt]
  FAILED ...[passed-pytest-timeout-shaped-BaseException]
  FAILED ...[passed-KeyboardInterrupt]
  ```
  (The port legs were never the defect: an owned socket is closed by `_held_port`, a passed one by uvicorn's own shutdown, which closes listeners before the lifespan hang. They are pinned so the fix cannot regress them.)
- **Fix** (`loremaster/loremaster/testing/loopback.py::_UvicornServerThread.stop`): `try: self._thread.join(...) finally: self._detach_capture()`; docstring gains the `Raises: BaseException … propagates UNCHANGED, after the capture handler is detached` clause.
- **GREEN**: R1 class + F1 class → `8 passed, 2 warnings in 3.50s` (warnings: third-party `websockets.legacy` deprecations, pre-existing).
- This pin IS the mutation proof of the fix: the pre-fix code is the wrong build, and it went RED on all 4 cases.

## Item 2 — `serve_http(shutdown_timeout_s=…)` parity (already landed in `8d42c27`; verified here)
- State found: parameter present, threaded into `_loud_teardown`; `TestServeHttpShutdownOverrunIsLoud`'s two overrun pins already pass `SHORT_SHUTDOWN_BUDGET_S` with windows `_STUCK_EXIT_WINDOW_LOW_S/HIGH_S` derived from it, and `test_both_helpers_default_to_the_same_shutdown_budget` pins the default parity. No test-first RED was possible (the fix predates this pass) — **deviation, disclosed**.
- **Proof the budget is THREADED, by revert-mutation** (content backup → restore, md5 `84265d6fce0fb3af4d2d166830c74498` before and after): `serve_http`'s `_loud_teardown(..., shutdown_timeout_s, stop)` → `DEFAULT_SHUTDOWN_TIMEOUT_S`. Declared RED: both stuck-handler overrun pins. Observed:
  ```
  FAILED ...TestServeHttpShutdownOverrunIsLoud::test_a_clean_exit_with_a_stuck_handler_raises_naming_the_address
  FAILED ...TestServeHttpShutdownOverrunIsLoud::test_a_failing_body_keeps_its_own_exception_and_carries_the_overrun_as_a_note
  2 failed, 2 passed in 11.12s
  ```
  declared == observed — PROOF HELD. The class now runs in ~2 s instead of spending the real 5 s twice.
- **DUAL comment** added above `_stuck_handler_class` (the pin-(d) section header): first authored at the 5 s default; since `8d42c27` passes the short budget; assertions unchanged, only the budget argument and its derived window moved; threading proven here. ⚠ Two readings of "DUAL-comment it": (a) a comment recording BOTH the old and new budget and that assertions were kept (applied); (b) a reference to the removed-behaviour DUAL law (the old 5 s behaviour inventoried). (a) chosen; (b) would add nothing — the 5 s default is still pinned by the parity test.

## Item 4 — T1–T4 contract smells (`REPORT-refactor-466-d1.md` §Step 2): all four were mechanical; none weakened or retargeted an assertion
| # | disposition | change | proof |
|---|---|---|---|
| T1 | **FIXED** | `TestAShutdownOverrunIsLoud::test_a_failing_body_keeps_its_own_exception_and_carries_the_overrun_as_a_note` gains the LOWER elapsed bound (`0.9×SHORT ≤ elapsed`, joined to the existing upper bound) and the failing-path lifecycle legs (handler snapshot unchanged, port refuses). | **t1** mutation `_loud_teardown` failing branch → `stop(0.0)`: declared {asgi, http failing-body}, observed those + both prompt-shutdown positive controls (`4 failed, 5 passed`) — the declared set was too small: a ZERO-wait failing path is also caught by the controls, so the refactor's T1 wrong build was already caught. **t1b** (the subtler build) `→ stop(shutdown_timeout_s / 10)`: asgi failing-body RED **only** via the new leg (`exit took 0.05s against a 0.5s budget`), asgi control green; http failing-body RED (already had both bounds) + http prompt control RED (`serve_forever` polls at 0.5 s, so 0.05 s is not enough for it) → `3 failed, 6 passed`. Declared {asgi, http failing-body}; the extra http-control red is recorded, not hidden. The new leg is the ONLY discriminator for serve_asgi under t1b. md5 restored `84265d6f…`. |
| T2 | **FIXED** | new `GENEROUS_SHUTDOWN_BUDGET_S = 10.0` (own constant, comment says why); `test_positive_control_a_slow_in_budget_shutdown_does_not_raise` uses it instead of `GENEROUS_STARTUP_BUDGET_S`. Same value, so the control's behaviour is unchanged; the R1 pin reuses it. | value-preserving rename of the budget source; class GREEN. |
| T3 | **FIXED** | `_server_capable_imported_distributions` now returns `_ServerReach(capable, unexamined)`: a RECORD-less distribution or an unreadable `.py` is RECORDED, never silently skipped; `test_the_derived_server_capable_set_equals_the_planted_map` asserts `unexamined == ()` first. Measured live before the change (2026-09-26, `ceabe73`+tree): 25 imported distributions, 0 RECORD-less, 0 unreadable files; derived `{anyio, uvicorn}` — so the new assertion is a strengthening, not a ruling. New positive control `test_positive_control_an_unlistable_distribution_is_reported_not_skipped` (uvicorn made RECORD-less by monkeypatch must MOVE from `capable` to `unexamined`). | **t3** mutation back to `for file in distribution.files or []` (silent skip): declared {the positive control} == observed, `1 failed, 6 passed`. md5 restored `bf326980…`. **Bound**: the per-file `OSError` leg has no positive control of its own (only the RECORD-less leg is forced); re-open trigger: the first live `unexamined` line of the unreadable-file shape. |
| T4 | **FIXED** | new pin `test_the_reach_oracle_covers_every_verb_the_detector_flags`: `_LISTENER_METHODS − _DEPENDENCY_LISTENER_VERBS == ∅`. The oracle stays an independent literal (the detector never reads it); it just may not be narrower. | **t4** mutation: a verb added to `_LISTENER_METHODS` only → declared {the new pin} == observed, `1 failed, 6 passed`. |

No T-item needed a behaviour ruling.

## Final verification (2026-09-26, HEAD `ceabe73` + this working tree)
- **Brief's set** — `uv run pytest -p no:xdist -q -p no:cacheprovider loremaster/tests/test_loopback_serving.py loremaster/tests/test_no_raw_listener_in_test_trees.py scripts/test_concurrent_wire_acceptance.py loremaster/tests/test_migration_wire.py`:
  ```
  118 passed, 2 warnings in 171.28s (0:02:51)
  EXIT 0
  ```
  (Delta derived: the refactor report's `110 passed` (its §Step 5) → 118 = +7 from this pass (R1 ×4 parametrised cases, T3 positive control, T4 oracle pin, the lead's collect-tree pin) +1 the lead added at commit `8d42c27` (`test_both_helpers_default_to_the_same_shutdown_budget` — §Pins-d listed 3 tests in that class; it now holds 4).)
- **`test_loopback_serving.py` ×5**: `46 passed` each — run1 11.68 s · run2 12.07 s · run3 12.05 s · run4 12.01 s · run5 11.56 s.
- **Skills**: `cd skills/lore-deploy/scripts && uv run python -m pytest -q -p no:cacheprovider . ../tests` → `120 passed in 19.74s`, EXIT 0.
- **ruff** (`check` + `format --check`) over the five touched files: `All checks passed!` / `5 files already formatted`.
- **`scripts/typecheck.sh`** (canonical): **0 errors in any file I touched.** It exits 1 on OTHER packets' uncommitted files — `scripts/test_forgery_door_sweep.py:42` (`loremaster.tasks` has no `SupersedeResult`) and 44 errors across 19 files of packets 58/63c/64b (`test_findings_*_64b.py`, `test_reanchor_58_r2_*.py`, `test_supersede_reanchor_58.py`, `test_fixwave_a19a/a19b/a28_63c_i_a.py`, `test_blocks_edge.py`, `test_task_*`). Not mine, not touched; surfaced for the lead. My own first typecheck run DID catch one error of mine (assigning `str` to `TimeoutExpired.stdout`, typeshed `bytes | None`) — fixed by re-raising a constructed `TimeoutExpired(..., output=, stderr=) from expired`; driver tests re-run after it: `23 passed in 6.58s`.
- Post-verify edits: only that re-raise (driver file) — re-verified by the driver test file above; `loopback.py` and the two loremaster test files are unchanged since the 118-pass run.

## DRY ledger (brief-base §6)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `scripts/concurrent_wire_acceptance.py::run_as_process_group` | `lore_search("run subprocess in its own process group start_new_session and killpg the whole tree on timeout")` (ran >120 s, backgrounded, returned) + awk fallback over every tracked `*.py` for `killpg` / `start_new_session=True` / `os.setsid` / `process_group=` | lore: one hit, a bash `setsid`+watchdog recipe inside `REPORT-contract-58-r2.md` (a report, not importable code); awk: the ONLY Python site was `_run_session` itself | **EXTENDED** `_run_session`'s Popen block — lifted into the function and `_run_session` now calls it (no second copy); `expected_passed` is the second caller. Sharing proven by mutation (§Item 3). |
| `scripts/concurrent_wire_acceptance.py::_captured_text` | covered by the query above (a 3-line typing adaptor) | — | HAND-ROLLED: narrows typeshed's `str \| bytes \| None` for `TimeoutExpired.stdout`; no existing adaptor. |
| `loremaster/tests/test_loopback_serving.py::_main_thread_interrupt` | read of the file's own helpers (F1's `_interrupt_main_thread_after`) | the F1 helper, which arms at block entry only | **EXTENDED** `_interrupt_main_thread_after`: the handler install/restore moved into `_main_thread_interrupt`, and the F1 helper is now a wrapper over it — one injection implementation, two aim points. |
| `…/test_loopback_serving.py::GENEROUS_SHUTDOWN_BUDGET_S` | file read | `GENEROUS_STARTUP_BUDGET_S` (wrong axis — that is T2's smell) | HAND-ROLLED constant (T2's fix). |
| `…/test_loopback_serving.py::TestAnInterruptedTeardownLeavesNothingBehind` | — (a test class) | — | REUSED `_UNEXPECTED_INTERRUPTS`, `_RecordingApp(shutdown_gate=)`, `_attached_logging_handlers`, `_threads_still_alive_after`, `_becomes_refused`, `_get`, `INTERRUPT_AFTER_S`, `THREAD_END_BOUND_S`. |
| `…/test_no_raw_listener_in_test_trees.py::_ServerReach` | file read | the existing bare-`set[str]` return | **EXTENDED** `_server_capable_imported_distributions` (return type widened to carry `unexamined`; its one caller updated). |

Grep/rg are hook-blocked (#473): every textual search above used `awk`, said here.

## Packages considered
`run_as_process_group` — stdlib `subprocess.Popen(start_new_session=True)` + `os.killpg`; `subprocess.run` was READ (CPython 3.14 `subprocess.run`: on `TimeoutExpired` it `process.kill()`s the direct child only, then re-raises with `exc.stdout/stderr` set) — that is exactly the orphaning the pin catches, so `replace` is impossible and the Popen-level wrapper is the minimal gap. `psutil` (tree walk + kill) would also do it but is not a dependency of `scripts/` and a process GROUP already names the whole xdist tree; verdict `keep_with_trigger` — trigger: a descendant that `setsid`s out of the group (the existing `_kill_process_group` docstring bound).

## CLASS lift (global CLAUDE.md "Fix the CLASS, not the instance", added to that file DURING this run, 2026-09-26)
**Item 3 — CLASS:** *every child process the acceptance driver spawns dies with its whole tree, on timeout or interrupt.* Domain source of truth: the driver module's AST (every `subprocess.<name>(…)` call + every `from subprocess import`). Enforced at the STATE: one spawning function (`run_as_process_group`), and a GENERATED completeness pin — `scripts/test_concurrent_wire_acceptance.py::TestEveryDriverChildGoesThroughTheProcessGroupRunner` (allowlist-the-safe: outside the runner only `subprocess.TimeoutExpired` / `subprocess.CompletedProcess` may be called; non-vacuity: the runner exists once and calls `Popen`; 3 planted positive controls incl. the `from subprocess import run` alias door; 1 honest-code control). **m4** mutation (a raw `subprocess.run` back in `expected_passed`): declared {the scan pin} == observed, `1 failed, 5 passed`, flagged `278: subprocess.run`; md5 restored `10c37db0…`. SIBLINGS TRIED: session runner, collect runner, a future `subprocess.*` call, the from-import alias. SIBLINGS NOT TRIED (named bound in the scanner's docstring, threat model = honest developer): `os.system`/`os.spawn*`/`os.exec*`/`asyncio` subprocesses — re-open trigger: the driver first imports `asyncio` or calls an `os` process API other than `killpg`.

**Item 1 — CLASS:** *every blocking wait inside `loopback.py` that a signal can interrupt leaves no PROCESS-GLOBAL state behind and propagates the interrupt unchanged.* Domain: the blocking waits in `loremaster/loremaster/testing/loopback.py` (enumerated by reading the module — 3 sites): `_UvicornServerThread._await_started`'s join (F1 — pinned), `_UvicornServerThread.stop`'s join (R1 — pinned here), `_stop_http_server`'s join. Process-global state owned by the module: exactly one kind, the `uvicorn.error` capture handler, attached in `start` and detached in `_abandon`/`stop` — both detach paths are now `finally`-shaped or in an `except BaseException`. SIBLING NOT TRIED: an interrupt in `_stop_http_server`'s join — it holds no process-global state (no capture handler; the shutdown request is already issued from its own daemon thread; an owned socket is closed by `_held_port`'s context exit), so the class property holds by construction there; no pin written. ⚠ This lift is by READING, not by a generated sweep: no AST pin enumerates "every blocking call in loopback.py". **Decision for the lead:** a generated sweep (AST-enumerate every `join`/`wait`/`sleep` in the module and require each to be exercised by an interrupt-injection case) is buildable but is ~an instrument, not a fix; my rec: ledger it, re-open trigger = the module gains a fourth blocking wait or a second kind of process-global state.

**T1–T4:** T3 and T4 ARE class fixes already (T3: the derivation reports its unexamined domain instead of shrinking silently; T4: a subset relation over two derived sets, not a hand-list). T1/T2 are instance-level fixture quality (a magnitude bound; a constant's axis) — genuine one-offs.

- **Final re-run after the class pin** (same brief command, HEAD `6417e8f` + tree): `124 passed, 2 warnings in 189.08s (0:03:09)`, EXIT 0 (118 + the 6 class-pin cases); driver file alone `29 passed in 6.33s`; ruff `All checks passed!`; typecheck re-run: still 0 errors in my 5 files.

## Acceptance — `scripts/concurrent_wire_acceptance.py`, 20 rounds (2026-09-26, `--allow-other-sessions`: observed at launch via `ps`: two `-n 12` lore suites from other sessions, a 63c fixwave `-n 8` run, and a mobile_pricepaper_smoke suite)
Driver run in its own process group under a 15 GB MemAvailable watchdog (never tripped; instrument pasted below). Driver code = this pass's final `run_as_process_group` version (started after the typing fix).
```
round 01/20: 14/14 passed, 0 failed/errored (exit 0) · 14/14 passed, 0 failed/errored (exit 0) — GREEN
round 02/20 … round 19/20: identical line, GREEN each (full log: every round 14/14 · 14/14, exit 0)
round 20/20: 14/14 passed, 0 failed/errored (exit 0) · 14/14 passed, 0 failed/errored (exit 0) — GREEN
#466 concurrent-pair acceptance: ACCEPTED — 20/20 rounds green in both sessions (20 run; expected 14 passed per session)
EXIT 0
```
Wrapper (verbatim, brief-base §1 instrument rule):
```bash
#!/usr/bin/env bash
# Runs the #466 acceptance driver in its OWN process group; a 5 s watchdog SIGKILLs that group below 15 GB MemAvailable.
S=<session scratchpad>
cd /home/ejprice/PycharmProjects/lore
setsid uv run python scripts/concurrent_wire_acceptance.py --allow-other-sessions > $S/acceptance.log 2>&1 &
pid=$!
while kill -0 $pid 2>/dev/null; do
  a=$(awk '/MemAvailable/ {print int($2/1048576)}' /proc/meminfo)
  if [ "$a" -lt 15 ]; then echo "WATCHDOG MemAvailable=${a}G — killing PGID $pid" >> $S/acceptance.log; kill -KILL -- -$pid; fi
  sleep 5
done
wait $pid; echo "EXIT $?" >> $S/acceptance.log
```

## Flags for the lead (surfaced, not acted on)
- `REPORT-refactor-466-d1.md` §Pins-d says reading (A) "applied … no API change"; the committed `8d42c27` carries reading (B). The archived report will read as current — it wants a one-line superseded note when archived.
- Refactor R4 (a raising `stop()` in `_loud_teardown`'s failing branch replaces the body's exception) and R6 (aiohttp deny-list leaves `SockSite`/`AppRunner`/… unflagged) remain open as the refactor report surfaced them; untouched by this pass (not in the brief's item list). R8 is CLOSED by item 3; R1 CLOSED by item 1; R2 was closed by `8d42c27`.
- Uncommitted working-tree files of OTHER packets are what make `scripts/typecheck.sh` red (see decisions (b)).
- Nothing committed or staged (brief). Git state untouched.
