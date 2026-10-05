brief-base v18 read · brief project v7 read

# REPORT — coldaudit-486-4 (cold REFUTE delta audit, #486 follow-up round 2: P1 hard outer bound · P2 #538 door domain · P3/R-2/R-6 wording; 2026-10-05)

## SUMMARY BLOCK
- **State:** done. **Verdict: GO-with-residuals.** P1 (hard outer bound), P2 (#538 door domain), P3 (F-3 wording), R-2 and R-6 are all correct in the build and hold under re-measurement. 0 GREEN→RED. Residuals, all LOW, are listed in the table below:
  - four missing or loose regression pins (F-1, F-2, F-4);
  - one false docstring rationale (F-3);
  - one design note on what a `-n 0` hard-bound kill tells the reader (F-5);
  - one wording nit (F-6).

  No MEDIUM, no HIGH.
- **P1 mutations (mine, §2):**
  - M1 (delete `dump_traceback_later`): **PROOF HELD**, exactly the 4 blocking cells RED.
  - M5 (bound = 1× budget): the 4 cooperative cells RED, as declared.
  - **M2 (never cancel): SURVIVES** (F-1).
  - **M3b (3× bound): SURVIVES.** M3 (4×) reddens only the 2 xdist cells, at 9.9 s against a 9 s ceiling (F-2).
  - **M4 (`sys.stderr` in place of `sys.__stderr__`): SURVIVES.** It is equivalent at session finish, and the docstring's stated reason for `__stderr__` is false by probe (F-3).
- **P2 (§3):** the generator is derived from `vars()` and the conftest's own worker session-finish.
  - C1 and C3 re-run: **MATCH** (3 and 12 RED).
  - C6 (a new suffixed key shipped and never read): the domain grows by 8 cells, 9 go RED, completeness stays green.
  - C7 (a key shipped without a suffixed constant): only the completeness pin goes RED.
- **P3 / R-2 / R-6 (§4):** no served line is false. R-6 is ONE implementation, **proven by mutation**: both served lines change, and the phrase has one literal in tracked `.py`. W1 (a new lifecycle verb) and W2 (the R-2 causes swapped, which serves a false cause) both **SURVIVE** (F-4).
- **Census (§5), 7 files:**
  - before (r1 tree): `934 passed, 2 skipped` (936 collected);
  - after (working tree): `970 passed, 4 skipped` (974 = 936 + 38 new);
  - **0 GREEN→RED.** The 2 new skips are the P3 accounted doors, by design.
- **Gates (§6):** typecheck RED_ADJUDICATED (83, owned, 0 in the audited files) · ruff GREEN · **RED_ORPHANED 0**. The FAIL render is #540, as briefed.
- **Lead ruling (cooperative control stays rc ≠ 0):** no evidence against it.
- **Deviations:** none. The real tree was never edited; its md5s are identical at start and end (§0, §7).
- **Packages considered:** none — no mechanism specified (audit). I READ, to judge:
  - pytest 9.0.3 `_pytest/faulthandler.py`: the timer is armed and cancelled only in `pytest_runtest_protocol`, with extra cancels in `pytest_enter_pdb` and `pytest_exception_interact`;
  - xdist 3.8.0 `xdist/remote.py` `WorkerInteractor.pytest_sessionfinish`: an old-style hookwrapper, so `workerfinished` is sent after `yield`.
- **Odoo-20 portability:** n/a — no Odoo seam touched. **Reuse ledger:** none. No repo symbols were added; the instruments are in §A.
- **Graded:** working tree on `38d5e83` (patch md5 `abd59483…`, five files at the briefed md5s) · HEAD-at-report: `38d5e83` · SAME.
- **Decisions needed:**
  1. F-1, F-2, F-4: these are regression-pin additions for a contract author. Fold them in before commit, or ledger them? I recommend at least F-2's exact-timeout pin: about one line, and it removes all timing slack.
  2. F-5 is the operator's design trade.
  3. F-3 is a docstring fix for the implementer.
- **Receipts:** §0/§7 md5 · §0' trees · §1 P1 · §2 mutation table · §3 P2 · §4 wording · §5 census · §6 gates · §F findings · Residuals · §A instruments (verbatim).

## Capability check (brief-base §4)
- Bash `grep` is hook-blocked on the main checkout (it is live-indexed), so textual scans here use `awk`/`python3`. Stated per the dogfood protocol. The scans are non-symbol textual seams (prose literals, call sites of a test-only helper), which is grep-honest case (b).
- `lore_comms register` done (session 63c, cadence ≤20m). The idle-gate contract is at `/tmp/claude-idle-gate-lore/unknown-coldaudit-486-4.contract`. The session id is not visible to me; sibling contracts use the same `unknown-` prefix.
- Deadline: 75 min from spawn (≈00:43Z → ≈01:58Z, 2026-10-05). Report written ≈01:05Z.
- No capability gap.

## §0 md5 receipts — START (2026-10-05 00:43:39Z, HEAD `38d5e83`)
```
2de2b7ee0de9a69a5a91aa7244b371e4  loremaster/tests/conftest.py
3c981b3ea9936c46ec08cd47df25109b  loremaster/tests/test_harness_database_lifecycle_486.py
f6f6f73f529a05bc940a0499239e2380  loremaster/tests/test_no_raw_listener_in_test_trees.py
f8f43532ab3febc4a153c9798e40eca8  pyproject.toml
2d0892676d29f0af24586afbdb8bd307  uv.lock
abd59483ced662c813cd210b00596173  486-r4-BUILD2.patch (lead scratchpad)
7fd7e2ec78ddf38e52032ec9059b6e1b  486-r4-BUILD.patch (lead scratchpad; round 1)
6440b108c12a7fc37dc72f9f8fed5c46  test_harness_database_lifecycle_486.py.contract-final (lead scratchpad; round 1)
```
All match the brief. Every mutation ran in a `scratch_copy.sh` copy (`mut/`). The real tree got only read-only runs: the census-after and the gates.

## §0' Trees
- **r1 (round-1 state).** Built with `./scripts/scratch_copy.sh <scratchpad>/r1`, then in the copy `git checkout HEAD --` on the five files and `git apply 486-r4-BUILD.patch`.
  - md5s: conftest `94f821754d8e37d0e613ef2f16f77dcc`, 486 file `6440b108…`, guard `f6f6f73f…`, pyproject `f8f43532…`, uv.lock `2d089267…`. These are exactly the round-1 states the brief names.
  - Provenance, from the census run: `loremaster.__file__ = <scratchpad>/r1/loremaster/loremaster/__init__.py`.
- **mut (round-2 state).** `./scripts/scratch_copy.sh <scratchpad>/mut` of the working tree: conftest `2de2b7ee…`, 486 file `3c981b3e…`. Provenance (scratch_copy receipt): `loremaster -> <scratchpad>/mut/loremaster/loremaster/__init__.py`. Every mutation's restore was verified byte-exact by md5.
- **The delta.** Round 1 → round 2 changes only two files:
  - `conftest.py`: the faulthandler bound in `_reap_within_budget`, `_SESSION_END_HARD_BOUND_IN_BUDGETS`, `_SessionEndReportGap` + `_GAP_LIFECYCLE_BY_WENT_DOWN`, `_UNVERIFIED_DATABASES_REMEDY`, and the R-2 cause text;
  - the 486 file: +506 lines, three classes `TestEveryWorkerDoorIsAccounted`, `TestTheGapLineNeverContradictsItsCause`, `TestTheSessionEndReapHasAHardOuterBound`.

  The guard file, pyproject and uv.lock are byte-identical across the rounds.

## §1 P1 — the hard outer bound: does each cell construct what it claims?
| claim | verdict | evidence |
|---|---|---|
| **sync block** | CONSTRUCTED | The injected `async def reap(): time.sleep(10 × budget)` has no await point, so no cancel scope can end it. Under M1 (no hard bound), each blocking cell held about 20.3–20.8 s, which is the whole sleep. anyio could not interrupt it, which is exactly the state the bound exists for. |
| **cooperative hang** | CONSTRUCTED | `await asyncio.sleep(10 × budget)`. The 4 cooperative cells pass with the `no answer within the 2s session-end reap budget` line, `1 passed`, and no dump. M5 (bound = 1×) reddens all 4, so the "no dump" and "budget line" legs can fail. |
| **`faulthandler_timeout` coexistence** | CONSTRUCTED, but discriminates little on its own | `PYTEST_ADDOPTS=-o faulthandler_timeout=600` makes pytest arm and cancel the same process-global timer around every test (pytest 9.0.3 `pytest_runtest_protocol`). All 4 variant cells pass. Its distinct power is against a bound armed BEFORE pytest's last per-test cancel. I did not build that wrong build (SIBLINGS NOT TRIED). |
| **dump reaches the real stderr** | `-n 0`: PINNED. xdist: PRESENT but UNPINNED | `-n 0`: `_DUMP_FRAME_NAMING_THE_REAP` has no comma before `in`, so only faulthandler's frame format can satisfy it. xdist: my probe X (§2) printed the child output. The worker's dump (`Timeout (0:00:04)!` … `conftest.py", line 432 in _reap_within_budget`) does reach it, after the controller's `1 passed`. The xdist leg asserts only rc ≠ 0 plus the gap line. That is acceptable, because the `-n 0` leg pins the dump. |
| **construction guard** | sound | It requires one opened database, at least one reaping-process stamp, and the budget seam present. Otherwise it reports CONSTRUCTION, never a verdict. |

**"What wrong build passes this?"** These do (measured in §2):
- a bound that is never cancelled (M2);
- a bound of up to 3× budget (M3b), and 4× under `-n 0`;
- a dump to `sys.stderr` (M4, equivalent in practice).

The 1× bound (M5), the missing bound (M1) and a 10×-class bound (M1 measures the unbounded 20 s) are all caught.

**Timer-coexistence judgment: no live risk today.**
- pytest's timer is live only inside `pytest_runtest_protocol`, so nothing is armed at session finish when `_reap_within_budget` arms its own. The `-o faulthandler_timeout=600` cells confirm this empirically.
- **Exception paths.** The arm sits outside the inner `try`:
  - if `dump_traceback_later` itself raises, nothing is armed, and the error is returned as the reap failure. The session fails loudly with `session-end reap failed … <error>`, and the reap is skipped.
  - any exception out of `anyio.run`, `BaseException` included, runs the `finally: cancel_dump_traceback_later()`.
- **Caller set.** An awk over every tracked test file finds that the ONLY caller of `_reap_within_budget` is `pytest_sessionfinish`. So the bound can never replace and cancel pytest's per-test timer mid-test.
- ⚠ **Bound, stated:** that rests on the caller set. A future in-test caller would silently disarm pytest's `faulthandler_timeout` for the rest of that test. Re-open trigger: any new caller of `_reap_within_budget`.

## §2 Mutation table (all in `mut/`, every run through the WAITING gate §A.1, 16G cgroup, `-n 8 --timeout=300`, TEST store :18000)
Predictions were written to scratch `declared/PREDICTIONS.txt` BEFORE each run (first block 00:47:59Z). Declared sets came from `pytest --collect-only` (`ids.txt`). M1 used `scripts/mutation_proof.py`; the rest used §A.2, a both-ways diff, because `mutation_proof.py` takes one anchor and needs a non-empty declared set.

| id | mutation (conftest unless noted) | declared | observed | verdict |
|---|---|---|---|---|
| M1 | the 3-line `faulthandler.dump_traceback_later(…)` call → `pass` | 4 blocking cells | `4 failed, 4 passed in 24.45s` (held 20.3–20.8 s); `tree restored byte-exact` | **PROOF HELD** (gate 00:50:44) |
| M2 | `faulthandler.cancel_dump_traceback_later()` → `pass` (armed, never cancelled) | ∅ (predicted survivor) | `8 passed in 9.53s` | **SURVIVOR** → F-1 |
| M3 | `_SESSION_END_HARD_BOUND_IN_BUDGETS = 4` | ∅ ("survivor or flaky") | `2 failed, 6 passed`, twice. The REDs are only `blocking-xdist-n2-*`, `held 9.9s` vs 9 s. Both n0 blocking cells GREEN | survives at `-n 0`; caught under xdist by 0.9 s → F-2 |
| M3b | `_SESSION_END_HARD_BOUND_IN_BUDGETS = 3` | ∅ | `4 passed` (blocking cells) | **SURVIVOR** → F-2 |
| M5 | `_SESSION_END_HARD_BOUND_IN_BUDGETS = 1` | 4 cooperative cells | `4 failed in 7.53s` | MATCH |
| M4 | `real_stderr = sys.stderr` | ∅ (predicted: equivalent at session finish) | `8 passed in 9.53s` | **SURVIVOR**, equivalent mutant → F-3 |
| C1 | `workeroutput.get(_UNREAPED_REPORT_WORKEROUTPUT_KEY, "[]")` (half report accounted) | 3 | 3 (`3 failed, 25 passed, 2 skipped`) | MATCH |
| C3 | `_workers_without_session_end_report` returns gaps only when every worker is a gap | 12 | 12 | MATCH |
| C6 | a new constant `_AUDIT_EXTRA_REPORT_WORKEROUTPUT_KEY` shipped by the worker session-finish, never read by `pytest_testnodedown` (2 anchors) | 9 (4 new P2 doors + 4 new P3 doors + all-at-once) | 9 (`9 failed, 27 passed, 2 skipped`; 38 collected vs 30) | MATCH: the domain follows the source of truth |
| C7 | `workeroutput["lore_999_audit_extra"] = "[]"` (shipped, no suffixed constant) | 1 (completeness) | 1 | MATCH: the completeness assertion fires |
| W1 | `False: "stopped WITHOUT its session-end report"` | ∅ | `28 passed, 2 skipped` | **SURVIVOR** (the stated verb-list bound) → F-4 |
| W2 | R-2: `if error is not None` → `if error is None` (the causes swapped) | ∅ | `28 passed, 2 skipped` | **SURVIVOR**, which serves a false cause → F-4 |
| X / X2 | (486 file, PROBES, not mutations) print `session.output` in the xdist / n0 blocking branch | ∅ | pass; the outputs are quoted in §1 and §F F-5 | probe |

## §3 P2 — the #538 door domain
- **Derived, not listed.** The keys come from `_report_keys`, i.e. `vars(conftest)` names ending in `_REPORT_WORKEROUTPUT_KEY`. The "complete report" is what the conftest's OWN worker `pytest_sessionfinish` writes into a fake `workeroutput`. Only the four broken-value kinds and the five whole-report doors are hand-written. That is the shape domain: an allowlist of ways a value can be wrong, not of keys.
- **Completeness fires** when a key is shipped without a suffixed constant (C7). **The generator grows** when one is added with the suffix (C6: +8 cells, and the unread key's doors redden). That is the property: *every value a worker ships is checked by the controller*.
- **Isolation.** `_fresh_suite_conftest` re-executes the conftest. Its module-level side effects, by AST scan:
  - `sys.path.insert` (idempotent);
  - `set_hypothesis_home_dir(_HYPOTHESIS_HOME)` (same value, idempotent);
  - the `_sdk_guard._CALL_HOOKS` append (monkeypatched to a copy).

  `_surreal_harness._MINTED_DATABASES` is monkeypatched to `{}`, so nothing leaks into the running session. `_door_names_at_collection` runs at import, inside a `MonkeyPatch.context()`. Benign.
- **Not re-run by me:** c2 (the corrupt value accounted). I rely on the contract's §10 receipt (`13 failed`), and C6's `=corrupt`/`=wrong-shape`/`=none` doors exercise the same `ValidationError` branch.

## §4 P3 / R-2 / R-6 — is any served line false or over-claiming?
These are the served lines (implementer probe §9.6, re-read against the code):
- **never went down:** `xdist worker gw0 never went down and sent no session-end report (no node-down arrived before the controller's session-finish) — …`.
  - No contradiction: `_ENDED_CLAIM` finds nothing once `never went down` is removed, and `session-finish` does not match `\bfinished\b`.
  - The clause states the controller's observation as the worker's lifecycle. The parenthetical names the exact bound (no node-down before the controller's session-finish), so the line names its bound. Acceptable.
- **went down, key missing, `error is None`:** `…; the worker reported no error, so a session-finish hook in it may have raised before the harness's`. Checked against xdist 3.8.0 `remote.py`:
  - `workerfinished` is sent after the hookwrapper's `yield`, so a hook that raises AFTER the harness's still ships the keys and the worker is accounted;
  - a hook that raises BEFORE it aborts pluggy's remaining impls, so no keys are shipped.

  So "before the harness's" is accurate. "may" is a hedge, and it is the right one: one other cause gives the same signal, the harness's OWN session-finish raising before it writes (e.g. an import error in `_reap_failure_outcome`). Not a false cause.
- **went down with error:** `…; the worker went down with an error`. Observed live in probe X: `[gw0] node down: Not properly terminated` → `the worker went down with an error`. True.
- **corrupt / wrong shape / `None`:** `went down WITHOUT its session-end report (its report could not be read (1 shape error(s)))`. A value DID arrive, so "WITHOUT its report" is loose: it means "without a READABLE report". It was inherited unchanged from round 1. LOW nit, F-6.
- **R-6:** `_UNVERIFIED_DATABASES_REMEDY = "the operator's periodic test-namespace wipe removes them"`. **ONE implementation, proven by mutation** (§A.3): with the constant changed to `AUDIT-MUTATED-REMEDY`, BOTH `_unreaped_line(...)` and `_SessionEndReportGap.line(...)` served the new text; restored to md5 `2de2b7ee…`. An awk over every tracked `.py` finds exactly one literal, `conftest.py` (the constant). The wording matches D2 (operator wipes; `_surreal_harness.py` module docstring: "wipes of the test namespace (operator ruling D2…)").
- **`_ENDED_CLAIM` (a verb list).** The bound is stated in the class docstring, which keeps it honest, and W1 shows it is real: `stopped WITHOUT` passes.
  - A fully derived verb domain is not possible for English.
  - A stronger allowlist form does exist: require each line to POSITIVELY state its door's lifecycle (`never went down` present iff `went_down is False`; `went down` without `never` iff True), keeping the negative list as a second leg. That catches W1 and any future synonym. See F-4.

## §5 Census — targeted before vs after
**Set (7 files):** `test_harness_database_lifecycle_486.py`, `test_surreal_harness.py`, `test_no_raw_listener_in_test_trees.py`, and the covering set from implement §Scope: `test_retry_seam.py`, `test_caplog_isolation.py`, `test_store_seam_one_derivation.py`, plus `test_loopback_serving.py`.
- `test_loopback_serving.py` is coldaudit-486-3's derivation, kept for continuity.
- Derivation: the implementer's list plus the prior audit's addition. `lore_impact` cannot see pytest hook dispatch (implementer F-e), so the fallback is stated.

| side | tree | gate | tail |
|---|---|---|---|
| BEFORE | `r1/` (round-1 conftest `94f82175…` + 486 `6440b108…`); `loremaster.__file__ = <scratchpad>/r1/loremaster/loremaster/__init__.py` | `GATE CLEAR 00:47:21` | `934 passed, 2 skipped, 9 warnings in 187.45s`, RC=0 |
| AFTER | the real working tree (audited md5s); `loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` | `GATE CLEAR 00:55:18` | `970 passed, 4 skipped, 9 warnings in 183.74s`, RC=0 |

- 936 → 974 collected: +38, exactly the contract's P1 8 + P2 17 + P3 13. **0 GREEN→RED.** Every new cell passes except the 2 P3 accounted-door skips, which are by design.
- Warnings 9 → 9, the same three categories: `test_retry_seam.py:3263` `_empty_subscription` never awaited (pre-existing F-d), the uvicorn `websockets_impl` DeprecationWarning, and `websockets.legacy`.

## §6 Gates (real tree, ≈00:59Z; no `-n` forwarded)
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` gave rc 1:
  - `typecheck RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract …`;
  - `ruff GREEN`;
  - `pytest NOT_RUN`, which makes the render read `CURRENCY: FAIL — claimed but never run: pytest`. That FAIL is #540, as briefed.

  **RED_ORPHANED 0** among the legs that ran.
- `scripts/typecheck.sh`: `errors total 83, in audited files 0` (awk over its output).
- `ruff check` on the three test files → `All checks passed!`. `ruff format --check` → `3 files already formatted`.

## §F Findings (each lifted to a class)
### F-1 (LOW): "the hard bound is cancelled on every way out" is unpinned; a never-cancelled timer passes all 8 cells (M2)
- **CLASS:** *∀ way out of `_reap_within_budget` (completed, timed out gracefully, raised), the process-global faulthandler timer is disarmed before the process continues.* The docstring claims this ("It is cancelled on every way out"), and no cell can observe it. In the cooperative cell, the child exits about 2 s after the arm, before the 4 s timer would fire. So a leftover timer is invisible, a fixture-timing reason.
- **Consequence of a regression.** A process whose post-reap tail runs past `2 × budget − reap time` would be `_exit(1)`ed, with a dump naming whatever frame it was in. That tail covers the remaining session-finish impls, the terminal summary, unconfigure, atexit, and the xdist worker's `workerfinished`. At the real budget (30 s) that is 60 s. The result is a loud FALSE failure with a misleading stack: never a false clear, but a trust-costly wrong cause.
- **Code today:** correct (`finally:` around `anyio.run`).
- **SIBLINGS TRIED:** never cancel (M2).
- **SIBLINGS NOT TRIED:**
  - cancel skipped only on the exception path (`anyio.run` raising a non-Timeout);
  - cancel called BEFORE arming.
- **Recommendation (contract author):** add one subprocess cell. The reap completes, or times out cooperatively, and a `trylast` session-finish in the injection plugin then holds the process for about `2 × budget + 1 s`. Expect no faulthandler header (`Timeout (`) and the normal verdict. M2 must turn it RED.

### F-2 (LOW): the ruled multiple (2 × budget) is pinned only to "≤ ~4×"; a 3× bound passes every cell (M3b)
- **CLASS:** FIXTURES MUST DISCRIMINATE, axis 3 (arithmetic alignment). The timing slack ε = 5 s is 2.5 budgets wide (budget 2 s), which is wider than the step it is meant to discriminate.
  - `-n 0` admits up to 4× (8 s + overhead ≤ 9 s ceiling);
  - xdist admits 3× and catches 4× by only 0.9 s (`held 9.9s`).

  The safety property (the hang IS bounded) holds. The ruled constant does not.
- **SIBLINGS TRIED:** 1× (caught by the cooperative cells), 3× (survives), 4× (xdist-only), unbounded (M1, caught).
- **SIBLINGS NOT TRIED:** 2.5×; a bound derived from a different budget source.
- **Recommendation (contract author), zero slack.** faulthandler's dump header PRINTS the configured timeout: observed `Timeout (0:00:04)!` for 2 × 2 s. The `-n 0` blocking cell can assert `Timeout (0:00:0{2×budget:g})!` in the output. That pins the multiple exactly from the dependency's own output, with no wall-clock arithmetic. Keep the held-time ceiling as the outer leg.

### F-3 (LOW, comment accuracy): the stated reason for `file=sys.__stderr__` is false; the choice is equivalent to `sys.stderr` at session finish (M4)
- The docstring says the dump goes "to the REAL stderr (pytest's capture may still own fd 2)". Contract §10 seam 4 says the same. But `sys.__stderr__.fileno()` is 2. If pytest's FDCapture owned fd 2, the dump would land in the capture tmpfile all the same, and `_exit` would discard it.
- **Probe §A.4** (plain python, FDCapture-style `dup2` of a tmpfile onto fd 2, then `faulthandler.dump_traceback(file=sys.__stderr__)`) printed: `sys.__stderr__.fileno() = 2` · `dump landed in the CAPTURE tmpfile: True (184 bytes)`.
- In practice pytest's global capture is SUSPENDED at session finish, which restores `sys.stderr` to the original object. That is why M4 is an equivalent mutant and why the `-n 0` dump is visible.
- **CLASS:** *a comment stating a mechanism that does not hold under the condition it names.* Not a served line, but agents read code.
- **Recommendation (implementer):** reword to "fd 2 — pytest's global capture is suspended at session finish (measured: the `-n 0` cells see the dump)". If robustness under active capture is ever wanted, the escape is pytest's own dup'd stderr fd (the faulthandler plugin's `config.stash` key), not `__stderr__`. NOT TRIED: a session where capture is resumed during session finish.

### F-4 (LOW): two wording legs are unpinned; one regression would serve a FALSE CAUSE (W2), the other is the stated verb bound (W1)
- **W2, CLASS:** *if the code branches on a value, at least one pin must use a different value* (FIXTURES axis 2). The R-2 cause clause branches on `error`, and the door domain already HAS both values: the key-absent doors have `error=None`; `crashed, shipped nothing` has `error` set. Yet no pin reads the cause. Swapping the two strings serves "the worker went down with an error" for a worker that reported none, and all 28 cells stay green. Under TRUST that is a false cause, the worst class of served line. The current text is correct (§4).
- **W1:** the `_ENDED_CLAIM` verb list. The bound is stated, and `stopped WITHOUT …` passes.
- **SIBLINGS TRIED:** W1, W2.
- **SIBLINGS NOT TRIED:** the R-6 remedy dropped from one line (no pin reads it; sharing was proven by probe, not by a test).
- **Recommendation (contract author):** P3 gains two legs, both generated over the existing doors:
  - **cause:** error-set doors contain `went down with an error`; `error=None` key-absent doors contain `reported no error`;
  - **positive lifecycle:** the line contains `never went down` iff `not door.went_down`.

  Both legs read `_Door` fields that already exist.

### F-5 (LOW, design note for the operator): a `-n 0` hard-bound kill tells the reader nothing about which test databases are unverified
- Probe X2 captured the whole `-n 0` blocking output: `.` `[100%]Timeout (0:00:04)!` followed by the thread stacks, then rc 1.
  - There is no pytest summary.
  - There is no line naming the opened-but-unverified databases, and no line saying they may remain on the TEST store. The graceful path's `_unreaped_line` names both.
- Under xdist, the controller's gap line covers this ("whatever test databases it opened were neither reaped-and-named nor reported unverified…").
- This is inherent to the ruled mechanism. am-37 §14 Q2: "a non-cancellable block … is a dumped stack". faulthandler cannot print a custom line at expiry.
- Not a false clear (rc 1, loud, the stack names `_reap_within_budget`). It IS a degraded-path render that drops a bound the healthy path names.
- **Options (operator):**
  - accept it as named here;
  - print the opened-database list to the real stderr BEFORE arming (one line on every reaping session, which is noise);
  - replace faulthandler with a watchdog that writes the line, then `faulthandler.dump_traceback` + `os._exit`. That is hand-rolling around a package that does the job, so it is not recommended.

  My recommendation is to accept and record it as a KNOWN BOUND in `_reap_within_budget`'s docstring.

### F-6 (LOW, wording nit): "WITHOUT its session-end report" is loose for doors where a value arrived but could not be read
- Same class as coldaudit-486-3 F-3 (*fixed prose wrapped around a variable cause*), on the report-presence axis rather than the lifecycle axis. Inherited from round 1, not new.
- Suggested derivation: for the `ValidationError` gap, `went down with an UNREADABLE session-end report (…)`.
- SIBLINGS TRIED: every `_SessionEndReportGap` cause string read against `_GAP_LIFECYCLE_BY_WENT_DOWN`.

## Residuals
| id | item | severity | owner | trigger / when |
|---|---|---|---|---|
| R-1 | F-1: never-cancelled timer survives; "cancelled on every way out" unpinned | LOW | contract author (486 file) | before #486 closes, or ledger it |
| R-2 | F-2: the ruled 2× multiple pinned only to ≤~4×; exact-timeout header assertion recommended | LOW | contract author | same |
| R-3 | F-3: false docstring rationale for `sys.__stderr__` (and contract §10 seam 4 wording) | LOW | implementer (conftest docstring) | next conftest touch |
| R-4 | F-4: R-2 cause leg and positive-lifecycle leg unpinned (W2 would serve a false cause) | LOW | contract author | before #486 closes, or ledger it |
| R-5 | F-5: `-n 0` hard-bound kill names no unverified databases | LOW | operator (design trade) | accept + docstring KNOWN BOUND, or rule otherwise |
| R-6 | F-6: "WITHOUT its report" for an unreadable value | LOW | lead (wording) | optional |
| R-7 | §1 bound: `_reap_within_budget` must stay session-finish-only, or it disarms pytest's per-test `faulthandler_timeout` | LOW (informational) | whoever adds a caller | re-open trigger: any new caller |
| R-8 | `faulthandler_timeout` variant's distinct discriminating power (an early-armed bound) not built by me | LOW | — | NOT TRIED |

## §7 md5 receipts — END (2026-10-05 01:00:05Z, HEAD `38d5e83`)
```
2de2b7ee0de9a69a5a91aa7244b371e4  loremaster/tests/conftest.py
3c981b3ea9936c46ec08cd47df25109b  loremaster/tests/test_harness_database_lifecycle_486.py
f6f6f73f529a05bc940a0499239e2380  loremaster/tests/test_no_raw_listener_in_test_trees.py
f8f43532ab3febc4a153c9798e40eca8  pyproject.toml
2d0892676d29f0af24586afbdb8bd307  uv.lock
```
These are byte-identical to START. `git status` is unchanged apart from this report.

## §A Instruments (verbatim; deliverables per brief-base §1)
### A.1 WAITING gate (`gate.sh`)
```bash
#!/usr/bin/env bash
# WAITING gate (coldaudit-486-4): MemAvailable >= 20 GiB AND no other lore pytest live; then exec under a 16G cgroup.
set -euo pipefail
while true; do
  avail_kib=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
  others=$(pgrep -fa '[p]ython.*-m pytest|[b]in/pytest' || true)
  if [ "$avail_kib" -ge $((20*1024*1024)) ] && [ -z "$others" ]; then break; fi
  echo "waiting $(date -u +%T): MemAvailable ${avail_kib} KiB; others: ${others:-none}" >&2; sleep 10
done
echo "GATE CLEAR $(date -u +%T): MemAvailable $(awk '/MemAvailable/ {print $2}' /proc/meminfo) KiB, no other pytest" >&2
exec systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 "$@"
```
Each test command was `gate.sh uv run --with pytest-timeout pytest -n 8 --timeout=300 -p no:cacheprovider -q …`, except probes X/X2, which ran at `-n 0 -s`.

### A.2 Multi-anchor mutation with a both-ways declared-set diff (`audit_mutate.py`)
```python
#!/usr/bin/env python3
"""coldaudit-486-4 instrument: apply one or more EXACT-ONCE text mutations to ONE file, run a pytest
command, restore the file byte-exact, and diff the observed RED set BOTH WAYS against a set declared
before the run (an empty declared set = a predicted SURVIVOR). Exists because scripts/mutation_proof.py
takes one anchor and requires a non-empty declared set.

usage: audit_mutate.py FILE DECLARED_FILE ANCHOR1 REPL1 [ANCHOR2 REPL2 ...] -- <pytest command>
"""
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

argv = sys.argv[1:]
split = argv.index("--")
head, command = argv[:split], argv[split + 1 :]
target, declared_file, *pairs = head
path = Path(target)
original = path.read_bytes()
md5_before = hashlib.md5(original).hexdigest()
declared = {line.strip() for line in Path(declared_file).read_text().splitlines() if line.strip()}
text = original.decode()
for anchor_file, replacement_file in zip(pairs[::2], pairs[1::2]):
    anchor, replacement = Path(anchor_file).read_text(), Path(replacement_file).read_text()
    count = text.count(anchor)
    if count != 1:
        sys.exit(f"ANCHOR {anchor_file} matched {count} times (need exactly 1) — nothing run")
    text = text.replace(anchor, replacement)
try:
    path.write_text(text)
    md5_mutated = hashlib.md5(path.read_bytes()).hexdigest()
    print(f"LANDED: {target} md5 {md5_before} -> {md5_mutated} ({len(pairs) // 2} anchor(s))")
    if md5_mutated == md5_before:
        sys.exit("mutation did not change the file — nothing run")
    result = subprocess.run(command, capture_output=True, text=True)
finally:
    path.write_bytes(original)
md5_restored = hashlib.md5(path.read_bytes()).hexdigest()
output = result.stdout + result.stderr
if os.environ.get("AUDIT_OUT"):
    Path(os.environ["AUDIT_OUT"]).write_text(output)
summary = output.split("short test summary info", 1)[1] if "short test summary info" in output else ""
observed = {re.split(r" - ", line.split(" ", 1)[1], maxsplit=1)[0].strip()
            for line in summary.splitlines() if line.startswith(("FAILED ", "ERROR "))}
print("\n".join(output.strip().splitlines()[-3:]))
print(f"RESTORED: md5 {md5_restored} {'== original' if md5_restored == md5_before else '!= ORIGINAL — RESTORE FAILED'}")
print(f"declared RED ({len(declared)}), observed RED ({len(observed)})")
print(f"  unexpected reds: {sorted(observed - declared)}")
print(f"  declared but GREEN: {sorted(declared - observed)}")
verdict = "MATCH" if observed == declared else "MISMATCH"
print(f"VERDICT: {verdict}{' (SURVIVOR: no pin reddened)' if not observed else ''}")
sys.exit(0 if md5_restored == md5_before else 3)
```
**Anchors → replacements**, all exact-once, verified before each run:
- **M2:** `            faulthandler.cancel_dump_traceback_later()` → `            pass  # M2: never cancelled`.
- **M3/M3b/M5:** `_SESSION_END_HARD_BOUND_IN_BUDGETS = 2` → `= 4` / `= 3` / `= 1`.
- **M4:** `    real_stderr = sys.__stderr__ if sys.__stderr__ is not None else sys.stderr` → `    real_stderr = sys.stderr`.
- **C1:** `…validate_json(workeroutput[_UNREAPED_REPORT_WORKEROUTPUT_KEY])` → `…validate_json(workeroutput.get(_UNREAPED_REPORT_WORKEROUTPUT_KEY, "[]"))`.
- **C3:** the `_workers_without_session_end_report` return → `gaps = {…}; return gaps if len(gaps) == len(_SESSION_END_REPORT_GAP_BY_WORKER) else {}`.
- **C6:** two anchors:
  - append `_AUDIT_EXTRA_REPORT_WORKEROUTPUT_KEY = "lore_999_audit_extra"` after the `_UNREAPED_…_KEY` constant;
  - append `workeroutput[_AUDIT_EXTRA_REPORT_WORKEROUTPUT_KEY] = "[]"` after the worker's unreaped `json.dumps` line.
- **C7:** only the second C6 anchor, with the literal key.
- **W1:** `    False: "never went down and sent no session-end report",` → `    False: "stopped WITHOUT its session-end report",`.
- **W2:** `if error is not None` → `if error is None` inside the R-2 `why`.
- **M1** used `scripts/mutation_proof.py --anchor-file` on the whole 3-line `faulthandler.dump_traceback_later(...)` call.

### A.3 R-6 sharing probe (`probe_remedy.py`, run with `uv run python` from the `mut/` root; the constant was mutated with a `cp -a` backup and restored to md5 `2de2b7ee…`)
```python
"""coldaudit-486-4: print both served lines that carry the stray-database remedy (R-6), via the conftest's own code."""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

TESTS = Path.cwd() / "loremaster/tests"
sys.path.insert(0, str(TESTS))
spec = importlib.util.spec_from_file_location("conftest_remedy_probe", TESTS / "conftest.py")
conftest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conftest)
print("FILE", conftest.__file__)
print("UNREAPED:", conftest._unreaped_line("failed", [("failed", "ValueError: x", ["test_db_1"])]).split("; ")[-1][-80:])
conftest.pytest_testnodeready(SimpleNamespace(gateway=SimpleNamespace(id="gw7")))
for worker, gap in conftest._workers_without_session_end_report().items():
    print("GAP:     ", gap.line(worker)[-80:])
```
Output, unmutated then with the constant mutated:
```
UNREAPED: the operator's periodic test-namespace wipe removes them
GAP:      l be on the TEST store; the operator's periodic test-namespace wipe removes them
--- mutated constant
UNREAPED: AUDIT-MUTATED-REMEDY
GAP:      r reported unverified. They may still be on the TEST store; AUDIT-MUTATED-REMEDY
```

### A.4 fd-capture probe (`fdcapture_probe.py`, plain `python3`)
```python
"""coldaudit-486-4: does faulthandler(file=sys.__stderr__) escape an fd-level capture of fd 2 (what pytest's FDCapture does)?"""
import faulthandler, os, sys, tempfile
saved = os.dup(2)
capture = tempfile.TemporaryFile()
os.dup2(capture.fileno(), 2)               # FDCapture-style: fd 2 now points at the capture tmpfile
faulthandler.dump_traceback(file=sys.__stderr__, all_threads=False)
os.dup2(saved, 2)                          # restore the real fd 2
capture.seek(0); captured = capture.read().decode()
print("sys.__stderr__.fileno() =", sys.__stderr__.fileno())
print("dump landed in the CAPTURE tmpfile:", "Current thread" in captured or "Stack (most recent" in captured, f"({len(captured)} bytes)")
```
Output: `sys.__stderr__.fileno() = 2` · `dump landed in the CAPTURE tmpfile: True (184 bytes)`.
