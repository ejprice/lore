brief-base v18 read

# REPORT — contract-486-r2 (tdd-light CONTRACT, round-2 amendment, lore finding #486)

## SUMMARY BLOCK
- **State:** done-with-deviations. Measured 2026-10-04 on the #486 working tree over HEAD `bf33631`.
  - **F1:** the pin is re-keyed and GREEN; both its control leg and its mutated leg hold.
  - **F2:** the new pin is RED for the right reason on both params (rc 0, no report line: the false clear). Its control is GREEN.
  - Everything else in the targeted set is unchanged.
- **Deviation 1:** the F2 fixture goes beyond the brief's "test_a leaks, test_b reaps". It has two leakers and two reaper calls (a leak, a reap, a leak, a reap), because a single leaker plus a single reap cannot tell three wrong fixes apart (§F2 "Why four tests").
- **Deviation 2:** the F2 pin asserts that ONE output line names both the leaked database and its leaking test. It does not key on the word `LEAKED`. The brief's sentence admits two readings (§Forks, fork 1).
- **Deviation 3:** F2 also runs under `-n 1` (one xdist worker, so all inner tests stay on one process), in addition to `-n 0`.
- **Packages considered:** none — no mechanism specified. These are tests only; they reuse the file's own `_run_inner_session`, census and cleanup helpers.
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** 3 new test-local helpers, all dispositioned (§Reuse ledger).
- **Graded:** n/a — this is authorship, not a verdict. HEAD-at-report `bf33631`.
- **Decisions needed:**
  - **D-r2-1 (blocks a clean GREEN; reasoned, not constructed):** the contract's own `TestTheReaperRemovesExactlyWhatThisProcessLeaked::test_the_reaper_removes_a_leaked_database_and_spares_a_dropped_one` deliberately leaks a database in the OUTER session and reaps it itself. Under the obvious F2 fix (report every reaper removal), the outer suite session would report that leak and fail. This needs a ruling (§Forks, fork 2).
  - **D-r2-2 (low):** the two sibling pins still have "marker" in their names and prose. Their mutation already uses KIND. I did not rename them (§F1 sweep).
- **Receipts:** §Counts · §F1 · §F1 sweep table · §F2 (RED tail verbatim) · §Forks · §Gates

## Capability check (brief-base §4)
- grep/rg are hook-blocked (#473), so every sweep used `awk`. This is the textual-seam case (b).
- I did not use lore for structure questions. Both edits were to files the brief named, and the sweep was a bare textual sweep, which the law says belongs to grep/awk. No friction to file.
- Backups were taken before any edit:
  - path: `<session scratchpad>/test_surreal_harness.py.orig` and `…/test_harness_database_lifecycle_486.py.orig`;
  - pre-edit sha256 `be5e6aee…166b` and `c731fc98…0c0c`, identical to refactor-486's recorded values;
  - post-edit sha256 `2e8dabf8…8599` and `b21e44e9…b06f`.
- Writable set respected: only the two named test files were edited (plus this report). I made no git mutation and did not commit.

## Counts (targeted; 2026-10-04)
- **Scope:** `test_surreal_harness.py`, `test_harness_database_lifecycle_486.py`, `test_retry_seam.py`.
- **Command:** `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q`.
- **Conditions:** MemAvailable was 29.6 / 30.7 GiB, and no other lore pytest was alive.

| run | result | red set |
|---|---|---|
| BEFORE (pre-edit) | `1 failed, 772 passed, 1 warning in 26.83s`, rc=1 | F1 only: `AttributeError: <module 'loremaster.store._txn' …> has no attribute '_RETRYABLE_CONFLICT_MARKER'` |
| AFTER | `2 failed, 774 passed, 1 warning in 32.15s`, rc=1 | the two F2 params only |

- **Red-set diff** (`diff before.red after.red`):
  - F1 left the red set (RED→GREEN, and renamed);
  - `[n0]` and `[xdist-n1]` of the new F2 pin entered it;
  - nothing else moved.
- **Arithmetic:** collected tests went 773 → 776, which is +2 F2 params and +1 F2 control. Passes went 772 → 774, which is +1 for F1 now green and +1 for the control.
- **Explicit `-rA` confirmation run:** `TestTheHarnessRetryPolicyIsTheSeamsPolicy` (all 16) plus the F2 control gave `17 passed in 1.93s`. That run includes `PASSED …::test_run_detection_follows_the_seams_one_conflict_kind` and `PASSED …::TestAMidSessionReapNeverSwallowsALeak::test_CONTROL_the_same_leaks_with_no_mid_session_reap_are_all_reported`.
- **The warning:** it is pre-existing (refactor-486 §Counts: `_empty_subscription` never awaited in `test_retry_seam.py`).

## §F1 — the stale pin, re-keyed (`test_surreal_harness.py`)
- **Test:** `TestTheHarnessRetryPolicyIsTheSeamsPolicy::test_run_detection_follows_the_seams_one_conflict_marker` was renamed to **`…::test_run_detection_follows_the_seams_one_conflict_kind`**.
- **The mutation:**
  - old: `monkeypatch.setattr(txn_module, "_RETRYABLE_CONFLICT_MARKER", "a marker no engine emits")`;
  - new: `monkeypatch.setattr(txn_module, "_RETRYABLE_CONFLICT_KIND", "AKindNoEngineEmits")`.
  This is the exact form of its two siblings in the same class.
- **Docstring:** it now explains ROUTING-IS-NOT-SHARING in terms of the typed kind. It also records that `34d0b6b` (63c-i-a amendment 36) deleted the text marker this pin first mutated. It keeps the round-1 "RED at HEAD" sentence, which is still true of committed HEAD, because #486 is uncommitted.
- **Prose updated:** the control comment ("real conflict kind"), the control's failure message ("whose classifier it reads") and the mutated leg's failure message ("an error whose kind the SHARED seam no longer recognises").
- **Module docstring:** the citation of the test name (in the `TestTheHarnessRetryPolicyIsTheSeamsPolicy.` bullet) was updated to the new name and now says "conflict KIND".
- **Both legs hold:**
  - the control asserts `control.query_calls == 2` (`run` retried);
  - the mutated leg asserts `pytest.raises(QueryError)` and `mutated.query_calls == 1` (no retry);
  - the test PASSED (above), which requires both assertions.

### F1 sweep table
- **Pattern:** a BARE, case-insensitive `toupper($0) ~ /CONFLICT_MARKER/`, plus `marker` near the edited class.
- **Scope:** `loremaster/tests/*.py`, plus `lorerunes/tests`, `lorescribe/tests` and `loresigil/tests`, which had 0 hits.
- Every hit gets a verdict:

| file:line (pre-edit) / symbol | hit | verdict |
|---|---|---|
| `test_surreal_harness.py:97` (module docstring) | cites `…one_conflict_marker` | **FIXED.** Now cites `…one_conflict_kind`. |
| `test_surreal_harness.py:133-134` (comment) | "was the text marker `_RETRYABLE_CONFLICT_MARKER`, deleted" | OK. Historical; it states the deletion. |
| `test_surreal_harness.py:1462` `test_detection_follows_the_seams_one_conflict_marker` | name, docstring ("Moving the seam's MARKER"), comment ("seam's real marker") and message ("SHARED marker") | **PROSE-STALE, NOT re-keyed.** Its mutation already targets `_RETRYABLE_CONFLICT_KIND`. Renaming it is cosmetic and outside the brief's one-test rename → D-r2-2. |
| `test_surreal_harness.py:1495` `test_the_bootstrap_paths_detection_follows_the_seams_marker` | name and messages say "marker" | **PROSE-STALE, NOT re-keyed.** Same verdict → D-r2-2. |
| `test_surreal_harness.py:1532/1560` (the F1 test) | patched the deleted name | **FIXED** (re-keyed and renamed). |
| `test_surreal_harness.py:1886` `test_the_retired_policy_constants_are_gone["_RETRYABLE_CONFLICT_MARKER"]` | asserts that the name is ABSENT from `_surreal_harness` | OK. A retired-name pin, which is meant to name the corpse. |
| `test_retry_seam.py:140, 296, 3672` | comments: "was … `_RETRYABLE_CONFLICT_MARKER`, deleted / retired" | OK. Historical. |
| `test_retry_seam.py:3673` `_MARKER_NAME = "_RETRYABLE_CONFLICT_KIND"` | the variable name says marker; the value is the KIND | OK. The value is current. |
| `test_retry_seam.py:3723` `test_no_production_module_holds_the_engines_conflict_marker` | a hygiene pin over engine text | OK. Live. |
| `test_retry_seam.py:3757/3766` `_GOVERNED_CONFLICT_MARKER` | a DIFFERENT name | OK. Live in production (`loremaster/store/_txn.py` defines `_GOVERNED_CONFLICT_MARKER = "governed_conflict:"`). |
| `test_surreal_store.py:2421, 2477` | comments: "the deleted `_RETRYABLE_CONFLICT_MARKER`" | OK. Historical. |
| `test_surreal_store.py:2639-2651` `_LIVE_CONFLICT_MARKER_INDEX`, `_MARKER_FIRST_CONFLICT_MARKER_INDEX` | statement-index constants | OK. Unrelated naming (positions in a response). |
| `test_surreal_store.py:4088` | `_RETRYABLE_CONFLICT_MARKER in str(f.raw_result)` | OK. It sits inside a synthetic SOURCE STRING (an AST-lint fixture, "matching-the-engines-RAW-marker-is-not-a-label") and is never executed. |
| `test_surreal_store.py:878` `test_the_classifier_maps_the_governed_conflict_marker_to_the_fixed_label` | the governed marker | OK. Live. |
| `test_surreal_store.py:134-137` | imports `_RETRYABLE_CONFLICT_KIND` | OK. Current. |
| `test_txn_contention.py:101` | comment: "used to interpolate `_txn._RETRYABLE_CONFLICT_MARKER`" | OK. Historical. |
| `test_floor_calibration_store.py:355`, `test_store_lease.py:1363` | `…conflict_marker…appears_nowhere` hygiene pins | OK. Live. |

Exactly one stale KEY exists (the F1 test), and it is fixed. No other test patches or reads the deleted name.

## §F2 — the new property and its pin (`test_harness_database_lifecycle_486.py`)
**PROPERTY:** for every database D leaked by a test, D is reported (named together with its leaking test) and the session fails. This holds regardless of whether, or how many times, `reap_minted_databases()` was called mid-session on the same worker.

**Symbols added** (new "LEG 3b" block between leg 3 and leg 4; the module docstring's leg list now names it):
- `TestAMidSessionReapNeverSwallowsALeak::test_leaks_before_and_between_mid_session_reaper_calls_are_all_reported[n0|xdist-n1]`. The inner session runs `test_a` (leaks), `test_b` (calls the reaper), `test_c` (leaks), then `test_d` (calls the reaper again).
- `TestAMidSessionReapNeverSwallowsALeak::test_CONTROL_the_same_leaks_with_no_mid_session_reap_are_all_reported`. The same two leakers, with no reaper call.
- Helpers:
  - `_inner_leaker(name)` and `_inner_reaper_caller(name)` build the inner test sources;
  - `_assert_every_leak_was_reaped_and_reported(session, present)` is shared by both legs, so the RED leg and the control differ ONLY in the reaper calls.
  - The helper asserts, ∀ leaker:
    - its database is absent from the store census;
    - the session's returncode is non-zero;
    - some single output line contains both that database id and that leaker's function name.

**Why four tests, not two (FIXTURES MUST DISCRIMINATE).** Each wrong fix below survives a single-leaker, single-reap fixture. Each one loses a leaker here:
- "remember only the LAST reap call's removals" loses `test_a`;
- "each reap call overwrites the ledger" ends with the empty `test_d` reap, so both leakers are lost;
- "report only what the session-end reap finds" finds nothing, because `test_d` already reaped `test_c`.

A fix that attributes a removal to the test that was RUNNING the reaper (`test_b` / `test_d`) instead of to the minter fails the per-line attribution check.

**What is deliberately NOT pinned (QUANTIFIER LAW / no mechanism):**
- who records the removal (the reaper, a hook, a scoped reaper);
- the report's wording, including the literal `LEAKED`;
- whether the reaper-calling test itself passes.

The pin constrains only the session's verdict, its output and the store.

**RED evidence.** Verbatim tail from the AFTER run, identical in shape for `[xdist-n1]` apart from the pid/ids, `bringing up nodes...` and `4 passed in 1.79s`:
```
FAILED loremaster/tests/test_harness_database_lifecycle_486.py::TestAMidSessionReapNeverSwallowsALeak::test_leaks_before_and_between_mid_session_reaper_calls_are_all_reported[n0]
E       AssertionError: the session PASSED although 2 of its tests leaked a database — a false clear: the leaks were removed, and nobody was told.
E         returncode=0 created=['test_1792555_d863169306bb4526947b4d8dca52dad1', 'test_1792555_c0186866065d46bfa6a53925fb379d67']
E         --- output tail ---
E         ....                                                                     [100%]
E         ==================================== PASSES ====================================
E         =========================== short test summary info ============================
E         PASSED test_inner_486.py::test_a_leaks_before_the_first_reaper_call
E         PASSED test_inner_486.py::test_b_calls_the_reaper_mid_session
E         PASSED test_inner_486.py::test_c_leaks_between_the_two_reaper_calls
E         PASSED test_inner_486.py::test_d_calls_the_reaper_again
E         4 passed in 0.82s
E       assert 0 != 0
```
- **The right reason:** both inner tests dialled (`created` has 2), and both databases are already GONE (the survivors assertion before it held). The session nevertheless returned rc 0 with no report line. That is refactor-486 §F2's false clear, reproduced at the pin and not as an error.
- **The control is GREEN on the same tree.** The identical assertion over the identical leakers passes when no mid-session reap happens. So the RED leg fails because of the reap, not because of the assertion or the wiring.
- **Cleanup:** every created database is removed in a `finally` by the outer test (`_remove_if_present`).

**Satisfiability:** shown only by the control, which proves the assertion can pass on these leakers. No reference build was made. Building implementations is the implementer's or grader's role (brief-base §2). See fork 2 for the satisfiability risk this pin creates ELSEWHERE in the contract.

## §Forks (brief-base §2: two readings → both written, one picked)
1. **"a LEAKED line naming test_a".**
   - (i) Assert the literal word `LEAKED` on a line naming test_a.
   - (ii) Assert that one output line names both the leaked database id and test_a.
   - **Picked (ii).** It pins attribution without pinning the current implementation's wording (`conftest.pytest_terminal_summary`'s `LEAKED test database …`), and round-1 leg 3 likewise keyed on names, not wording.
   - If the lead wants the literal pinned too, it is a one-line addition to `_assert_every_leak_was_reaped_and_reported`.
2. **D-r2-1. Is a test's reaper call on its OWN mint a teardown or a leak?** *Reasoned, not constructed* (constructing it needs a fix build, which is not my role).
   - (R1) Every database `reap_minted_databases()` removes is a reported leak, whoever minted it.
   - (R2) A removal of a database minted by the very test calling the reaper is that test's teardown, and is not a leak.
   - My F2 pin is **reading-agnostic**: its reaper callers mint nothing, so every removal is another test's leak under both readings.
   - The existing `TestTheReaperRemovesExactlyWhatThisProcessLeaked::test_the_reaper_removes_a_leaked_database_and_spares_a_dropped_one` is NOT reading-agnostic:
     - it mints `leaked_env`, dials it and never drops it;
     - then it calls the reaper itself in the OUTER suite session;
     - under R1 with the obvious chokepoint fix (refactor-486 option (a): the reaper records what it removes into the session leak ledger), every suite session that runs that test will end with a `LEAKED … (minted by …test_the_reaper_removes…)` line and exit status TESTS_FAILED.
   - **Recommendation:** R1, which is the simpler property (no "who is calling" carve-out, which would be a guarded invariant). Move that direct reaper test's leak into an inner session via `_run_inner_session`. Its in-process assertions on the reaper's return value would then become output/store assertions, or a small inner-session record file like `_record`.
   - This is a contract edit in my writable file. I did NOT make it, because it reshapes a round-1 leg, and the R1/R2 choice is a ruling.
   - If R2 is ruled instead, that test stands as is, and the implementer must carve out self-mints, which F2 neither requires nor forbids.

## §Reuse ledger (brief-base §6)
| new symbol | query run | returned | disposition |
|---|---|---|---|
| `_inner_leaker` | awk over the file for inner test-source builders | `_INNER_LEAKING_TEST` (fixed name `_LEAKING_TEST_NAME`, a single test) | HAND-ROLLED test-local helper. The existing constant cannot take a name, and F2 needs two distinctly named leakers. Its body mirrors `_INNER_LEAKING_TEST`. Reshaping that constant to call the helper would touch leg 3; I left it alone. |
| `_inner_reaper_caller` | same | none | HAND-ROLLED, test-local. |
| `_assert_every_leak_was_reaped_and_reported` | same, for leak assertions | leg 3's inline asserts (single leaker, whole-output name check) | HAND-ROLLED. Leg 3's whole-output check cannot attribute per leaker: with several inner tests, `-rA` prints every name. |

## §Gates (2026-10-04)
- `uv run ruff check .` → `All checks passed!` (rc 0).
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`:
  - `typecheck RED_ADJUDICATED`: 83 residuals, owned by packet-58-contract and packet-64b-i-contract. This is the same count refactor-486 recorded. A separate `scripts/typecheck.sh` run printed 0 lines naming either edited file.
  - `ruff GREEN`.
  - `pytest NOT_RUN`: the known scoped-legs line.
  - **RED_ORPHANED 0** for typecheck/ruff.
- Outside the brief, noticed: `uv run ruff format --check loremaster/tests/test_surreal_harness.py` reports "would reformat". The **pre-edit original fails the same check** (verified on the backup copy), so this predates my edits. `ruff format` is not a manifested gate. I did not touch it.

## Noticed outside this change
- Sibling prose-stale "marker" names: D-r2-2 above.
- refactor-486 F3–F5 are still open, as routed there. I did not re-grade them.
