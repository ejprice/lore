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

## ROUND 2b (lead brief: D-r2-1 ruling, D-r2-2, F3, F4). Measured 2026-10-04 on the #486 working tree over HEAD `bf33631`.

### Round 2b summary
- **State:** done-with-deviations.
  - **D-r2-1:** the reaper test is re-keyed into an inner session. It passes on the current implementation AND under the throwaway F2-fix reference.
  - **D-r2-2:** done.
  - **F3:** the new pin fails on 6 of its 7 shapes for the right reason, and its control passes.
  - **F4:** the comment now tells the truth.
- **Deviation 1:** F3's `databases-none` shape PASSES on the current implementation. `set(None)` raises `TypeError`, which already satisfies "raise, never report clean". I kept the case because it is part of the property's domain.
- **Deviation 2:** `_InnerSession` gains a `record_path` field, which is additive. The re-keyed reaper test needs it to read what the inner reaper RETURNED.
- **Deviation 3:** F4 took the "make the comment true" branch. **There is no existing harness name to import:** `_surreal_harness.unique_database` inlines `f"test_{os.getpid()}_{uuid.uuid4().hex}"`. An awk over `_surreal_harness.py` for `"test_` finds only that one f-string, and the module has no prefix constant.
- **Decision needed (D-r2b-1, satisfiability, MEDIUM):** the reference build kept its leak ledger as a new harness module-level name. That made `TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_module_level_names_are_exactly_the_allowed_set` fail; this is an ALLOWLIST pin, and the implementer may not edit it. Any fix that adds module state to `_surreal_harness` hits the same pin. Options:
  - (a) the fix keeps the removal ledger outside the harness module (for example in `conftest.py`), and the allowlist is untouched;
  - (b) the contract owner pre-authorises one name in `_ALLOWED_MODULE_LEVEL_NAMES` once the implementer names it.
  - I recommend (a) as the default, because the contract then stays mechanism-free, and (b) if the implementer argues the chokepoint must sit inside the reaper.
- **Packages considered:** none — no mechanism specified (tests only).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 0 new reusable symbols. The additions are test-local constants and inner sources (`_INNER_REAPER_DIRECT_TEST`, `_WELL_FORMED_EMPTY_NAMESPACE_ANSWER`, `_answer_info_for_ns_with`), plus one field on the existing `_InnerSession`.
- **Hashes:** pre-round sha256 copies are kept as `…r2a` in the session scratchpad. Post-round sha256:
  - `test_surreal_harness.py` `f884dc9c…70b7`;
  - `test_harness_database_lifecycle_486.py` `d277c099…19ff`.

### Counts (same targeted set and command as round 2)
| run | result | red set |
|---|---|---|
| BEFORE (round-2 AFTER) | `2 failed, 774 passed` | the F2 pins `[n0]`, `[xdist-n1]` |
| AFTER on the current implementation | `8 failed, 776 passed, 1 warning in 33.50s`, rc=1 | the F2 pins `[n0]`, `[xdist-n1]` + F3 `[not-a-dict-none]`, `[not-a-dict-list]`, `[not-a-dict-string]`, `[databases-key-missing]`, `[databases-a-list]`, `[databases-a-string]` |
| UNDER the throwaway F2-fix reference | `7 failed, 777 passed`, rc=1 | the 6 F3 reds (the reference does not touch the shape read) + the allowlist pin (D-r2b-1). **The F2 pins and the re-keyed reaper test PASS. The outer session printed 0 `LEAKED` lines**, so no outer test leaks on purpose any more. |

- **Arithmetic, current implementation:** collected tests went 776 → 784, which is +7 F3 params and +1 F3 control. Passes went 774 → 776: +1 for `databases-none` and +1 for the F3 control. The re-keyed reaper test stayed a pass.
- **Post-restore confirmation:** an explicit `-rA` run on the restored tree gave `31 passed in 3.69s`. It covers:
  - `TestTheReaperRemovesExactlyWhatThisProcessLeaked` (both tests);
  - the F3 control and F3 `[databases-none]`;
  - `TestTheHarnessDeclaresNoRetryPolicyOfItsOwn`, where the allowlist pin passes again after the restore;
  - `TestTheHarnessRetryPolicyIsTheSeamsPolicy`, including all three renamed `…_kind` pins.

### D-r2-1 — the reaper test, re-keyed (`TestTheReaperRemovesExactlyWhatThisProcessLeaked::test_the_reaper_removes_a_leaked_database_and_spares_a_dropped_one`)
- **Inner session** (`_INNER_REAPER_DIRECT_TEST`, inner test `test_the_reaper_removes_the_leaked_one_and_spares_the_dropped_one`):
  - it mints and dials two databases, then drops one;
  - it calls `reap_minted_databases()`;
  - it writes the RETURN to `<record>.reaped.json`.
- **Outer assertions, all kept from round 1 plus the outcome:**
  - the leaked name is in the reaper's return, and the dropped name is not;
  - neither database is in the store census afterwards;
  - the inner test PASSED;
  - **no output line names the DROPPED database**, so a fix's report may not name a clean test.
- **Not asserted here:** the inner session's rc. Under the ruling, the session must fail and report its leak, but that is the F2 leg's property, and asserting it here would turn this pin RED on the current implementation. The docstring says so.
- **The outer session no longer leaks on purpose.** Verified under the reference build: 0 `LEAKED` lines in the outer run's terminal summary.

### Throwaway F2-fix reference (pasted verbatim per brief-base §1; applied, run, restored)
- Backups: `cp -a` content copies of `_surreal_harness.py` and `conftest.py` (sha256 `e3561445…2fbe` and `e9941c5e…89ba`).
- Restore: `cp -a` back, then `cmp` (silent) and `sha256sum -c` → `_surreal_harness.py: OK`, `conftest.py: OK`. awk for `_REAPER_REMOVALS` over both files → 0 lines.
- It was never shipped. It is a satisfiability receipt (a correct build), not a wrong build.
```python
"""THROWAWAY reference edit (contract-486-r2 round 2b) — the obvious F2 fix: the reaper records
every removal into a process-wide list, and session end reports from that list. Never shipped."""
from pathlib import Path

harness = Path("_surreal_harness.py"); h = harness.read_text()
for old, new in [
    ("_MINTED_DATABASES: dict[str, str] = {}\n",
     "_MINTED_DATABASES: dict[str, str] = {}\n_REAPER_REMOVALS: list[str] = []\n"),
    ("            await _remove_database_with_retry(connection, database, url=reader_env.url)\n",
     "            await _remove_database_with_retry(connection, database, url=reader_env.url)\n            _REAPER_REMOVALS.append(database)\n"),
]:
    assert h.count(old) == 1, old; h = h.replace(old, new)
harness.write_text(h)

conftest = Path("conftest.py"); c = conftest.read_text()
old = "    leaked = tuple(asyncio.run(reap_minted_databases())) if minted_by else ()\n"
new = ("    from _surreal_harness import _REAPER_REMOVALS\n\n"
       "    if minted_by:\n        asyncio.run(reap_minted_databases())\n"
       "    leaked = tuple(dict.fromkeys(_REAPER_REMOVALS))\n")
assert c.count(old) == 1; conftest.write_text(c.replace(old, new))
```
(run from `loremaster/tests/`)

### D-r2-2 — sibling renames (`test_surreal_harness.py`, assertions unchanged)
- `test_detection_follows_the_seams_one_conflict_marker` → **`test_detection_follows_the_seams_one_conflict_kind`**. Its docstring, control comment and failure message now say "kind" / "conflict signal".
- `test_the_bootstrap_paths_detection_follows_the_seams_marker` → **`test_the_bootstrap_paths_detection_follows_the_seams_kind`**. Its failure message now says "SHARED kind" / "conflict signal".
- **Remaining "marker" mentions in that class:** one, the docstring's reference to the RETIRED class `TestTheTestHarnessCannotDriftFromTheSeamsMarker`. That is a historical name; I kept it.
- **References to the old names:** a round-2 sweep over `*.py`, `*.yaml` and `*.md` (excluding the receipts archive) found them only in this file and in the uncommitted `REPORT-*` files. No `pending_contracts.yaml` row names them.

### F3 — `TestTheReaperFailsLoudOnANamespaceAnswerItCannotRead`
- **PROPERTY:** for any `INFO FOR NS` answer from which the present set cannot be read, the reaper RAISES. It never returns "nothing leaked".
- **The domain is grounded in a live probe** (below): the well-formed answer is a `dict` with keys `accesses`, `databases` and `users`, where `databases` is a `dict`. So a missing `databases` key is also a wrong shape, and I pinned it. The brief named two classes; the missing key is the third member of the same "cannot read the present set" property.
- **Injection:** I monkeypatch `_surreal_harness.run` for the statement `INFO FOR NS` only; every other statement passes through to the real TEST store.
- **A real leaked database is minted and dialled**, so each wrong-shaped answer hides an actual leak. It is dropped in `finally`.
- **The outer test removes nothing.** No answer lists the leak, so this outer test cannot trigger the F2 swallow door.
- **Exception type:** the pin accepts ANY exception, because the property is "loud". It does not name a class, which keeps the mechanism free.
- **Control:** `test_CONTROL_a_well_formed_answer_is_read_without_raising`. A well-formed EMPTY `databases` map returns `()`, and the real leaked database is still present afterwards (read from the real census once the patch is undone). This proves the injection reaches the reaper's read and that the RED is about the SHAPE.
- **RED tails** (verbatim, the first 230 characters of each `Failed:` line):
```
E           Failed: `INFO FOR NS` answered None — a shape the present set cannot be read from — and the reaper RETURNED () instead of raising. With `test_1805343_588f479f614940c0a57e4f7238b9c2cf` actually leaked, that is a false '
E           Failed: `INFO FOR NS` answered [] — a shape the present set cannot be read from — and the reaper RETURNED () instead of raising. With `test_1805343_38503711f9464dbf88a1c34f2600ec1b` actually leaked, that is a false 'no
E           Failed: `INFO FOR NS` answered 'INFO FOR NS' — a shape the present set cannot be read from — and the reaper RETURNED () instead of raising. With `test_1805343_c6f07e7171e74b91978c5d50db073041` actually leaked, that is 
E           Failed: `INFO FOR NS` answered {'accesses': {}, 'users': {}} — a shape the present set cannot be read from — and the reaper RETURNED () instead of raising. With `test_1805343_1dc107b4a9734372b7bb6b81cdff3b72` actually 
E           Failed: `INFO FOR NS` answered {'accesses': {}, 'databases': [], 'users': {}} — a shape the present set cannot be read from — and the reaper RETURNED () instead of raising. With `test_1805343_0ee91b289122471f9ccc2d17c3
E           Failed: `INFO FOR NS` answered {'accesses': {}, 'databases': 'test_x', 'users': {}} — a shape the present set cannot be read from — and the reaper RETURNED () instead of raising. With `test_1805343_6d3855c13e1c49f39e59
```
- **Sibling, not pinned, flagged:** the contract's own census helper `_databases_in_the_test_namespace` has the same fail-open coercion (`… if isinstance(info, dict) else {}`).
  - It is an ORACLE, so a wrong shape there would make the leak legs' "absent from the store" assertions pass vacuously.
  - I did not change it. Hardening it, by raising on a wrong shape, is a one-line contract edit; I can do it if the lead wants (no ruling needed).

**Probe for the live shape** (pasted verbatim). Run from `loremaster/tests` with `PYTHONPATH=.` → `dict ['accesses', 'databases', 'users']` / `databases type: dict n= 76`:
```python
"""Probe (contract-486-r2 round 2b): the live shape of INFO FOR NS on the TEST store."""
import asyncio
from _surreal_harness import PRODUCTION_DIM, connect_admin, drop_database, make_env, run, surreal_url, unique_database

async def main() -> None:
    assert ":18500" not in surreal_url()
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    connection = await connect_admin(env)
    try:
        info = await run(connection, "INFO FOR NS")
        print(type(info).__name__, sorted(info) if isinstance(info, dict) else info)
        print("databases type:", type(info.get("databases")).__name__, "n=", len(info.get("databases", {})))
    finally:
        await connection.close()
        await drop_database(env)

asyncio.run(main())
```

### F4 — the `_RECIPE_PREFIX` comment
The old comment said "the lint reads it rather than restating a different one", which was false. It now reads:
> RESTATED here, not read: the harness keeps no prefix constant (`unique_database` inlines `f"test_{os.getpid()}_…"`). The restatement cannot drift silently: if the mint stops starting with it, the lint stops finding the mint and `test_the_lint_sees_the_one_mint` goes RED.

The drift claim matches what the lint does: `_naming_recipe_sites` keeps only sites whose leading literal starts with `_RECIPE_PREFIX`, and the non-vacuity pin asserts that the mint is among them.

### Gates (round 2b)
- `uv run ruff check .` → `All checks passed!`.
- I ran `ruff format` on `test_harness_database_lifecycle_486.py` only. It was format-clean before this round, and I diffed it to confirm the formatter removed only my own lines. I did not format `test_surreal_harness.py`, whose drift predates this work (round 2 §Gates).
- `pending_contract_gate.py --currency --legs typecheck,ruff`:
  - `typecheck RED_ADJUDICATED`, 83 residuals, unchanged;
  - `ruff GREEN`;
  - `scripts/typecheck.sh` printed 0 lines naming either edited file;
  - **RED_ORPHANED 0** for typecheck and ruff.

## ROUND 2c (lead brief: harden the census oracle so it fails closed). Measured 2026-10-04 on the #486 working tree over HEAD `bf33631`.

### Round 2c summary
- **State:** done.
  - The census oracle `_databases_in_the_test_namespace` now reads `INFO FOR NS` through production's `loremaster.governed.map_of(info, noun=_CENSUS_NOUN, required=("databases",))` (ONE IMPLEMENTATION).
  - A wrong-shaped answer raises `SurrealStoreError`. It no longer reads as an empty namespace.
- **No deviations.** I edited only `test_harness_database_lifecycle_486.py`, and did not touch `_surreal_harness.py` or `conftest.py`.
- **Packages considered:** none — no mechanism specified. The mechanism is an existing in-repo reader, REUSED.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** `map_of` is **REUSED** (`loremaster/governed.py::map_of`, "THE one reader of an `INFO FOR …` answer, with the ONE fail-closed shape policy"). It was found by the lead's brief and read in full before use.
  - Its `required` parameter covers the missing-key case, and its sub-map check covers `databases` being a non-map.
  - New test-local names: `_CENSUS_NOUN`, plus `_UNREADABLE_NAMESPACE_ANSWERS` (the round-2b F3 shape list, hoisted so the reaper leg and the census leg share ONE domain).
- **Decisions needed:** none.
- **Post-round sha256 of the lifecycle file:** `b1a6b92b982fd99b…`. The pre-round copy is kept as `…r2b` in the session scratchpad.

### What changed
- `_databases_in_the_test_namespace`: `info.get("databases", {}) if isinstance(info, dict) else {}` → `map_of(info, noun=_CENSUS_NOUN, required=("databases",))["databases"]`. The docstring states the fail-closed reason.
- `TestTheReaperFailsLoudOnANamespaceAnswerItCannotRead`: its inline `parametrize` list is now `_UNREADABLE_NAMESPACE_ANSWERS`. The values and ids are identical, so the test ids are unchanged.
- **New class `TestTheCensusOracleFailsClosed`:**
  - `test_the_census_raises_on_an_unreadable_answer[<7 shapes>]` replaces this module's `run`, the one the census calls, for `INFO FOR NS` only. Each shape must give `pytest.raises(SurrealStoreError, match=_CENSUS_NOUN)`.
  - `test_CONTROL_the_census_returns_the_real_set_on_a_well_formed_answer` is unpatched and live. A database the test mints and dials is IN the returned set, and it is dropped in `finally`.
- **Dropped while writing:** a second control assertion that every census name starts with `test_`. It asserted store content I had not verified (the namespace may hold other names) and that the brief did not ask for.

### Targeted run (same set and command as rounds 2/2b)
- MemAvailable was 21.8 GiB.
- The `pgrep -f '[p]ytest'` count of 1 was my own shell: the wrapper command line contains the word, which is the self-match bound brief-base §5 item 5 warns about. No other pytest was alive.
- **Tree under test, hashed before and after the run** (the implementer was building concurrently): `_surreal_harness.py` `e3561445ab11f52f` and `conftest.py` `e9941c5eafc65157`, unchanged during the run. These are the same files as round 2b.

| run | result | red set |
|---|---|---|
| BEFORE (round-2b AFTER) | `8 failed, 776 passed` | — |
| AFTER | `8 failed, 784 passed, 1 warning in 32.60s`, rc=1 | **identical** to round 2b (`diff after2b.red after2c.red` → empty): the 2 F2 pins and the 6 F3 shapes |

- **Arithmetic:** +8 passes, which are the 7 census shapes and the census control. No other node moved.

### Mutation proof of sharing (in-process; no file mutated)
- **Method:** a `-p` plugin replaced the shared function's BODY (`loremaster.governed.map_of.__code__`) with a fail-OPEN reader.
- **Result:** `TestTheCensusOracleFailsClosed` gave `7 failed, 1 passed in 0.84s`. Every shape went RED and the control stayed GREEN.
- **What it shows:** the census routes through the shared reader and keeps no private copy. The unmutated baseline is the AFTER run above, where all 8 pass.
- **Instrument** (pasted verbatim):
```python
"""Mutation plugin (contract-486-r2 round 2c): replace the BODY of the shared
loremaster.governed.map_of with a fail-OPEN reader. If the census routes through the shared
function, its fail-closed cells must go RED; a private copy would stay GREEN."""
import loremaster.governed


def _fail_open(result, *, noun, required=()):
    if isinstance(result, dict) and isinstance(result.get("databases"), dict):
        return result
    return {"databases": {}}


def pytest_configure(config):
    loremaster.governed.map_of.__code__ = _fail_open.__code__
```
- **Command:**
  - with `PYTHONPATH=<dir holding the plugin>`, run `uv run --with pytest-timeout pytest --timeout=300 -q -p no:cacheprovider -p mutate_map_of_486r2 "loremaster/tests/test_harness_database_lifecycle_486.py::TestTheCensusOracleFailsClosed"`;
  - run it under the same `systemd-run` cap.

### Gates
- `uv run ruff check .` → `All checks passed!`.
  - One I001 (import order, from the two new imports) was fixed with `ruff check --fix` on this file only.
  - `ruff format` was applied to this file only.
- **Noticed for the implementer:** the reaper should reuse the same `map_of` call for its own F3 fail-loud read. That would make the reaper and the census one implementation. The contract does not prescribe it; F3 accepts any raise.
