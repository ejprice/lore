brief-base v17 read

# REPORT — stub-486 (tdd-light Phase 2 STUB: #486 harness `run()` retry + the test-DB leak)

## SUMMARY BLOCK
- **State:** done
- **Deviations:** none to the writable set. Comms: I did not register on `lore_comms` and did not write the idle-gate `.contract` file, because the brief named no session and I cannot see my session id (§Capability check).
- **Packages considered:** none — no mechanism specified (a stub with three names; the behaviour is GREEN's).
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** 3 new symbols, all fixed by the contract's exact-set allowlist (§DRY ledger)
- **Graded:** n/a (stub author) · HEAD-at-report `86a55eb`
- **Result (measured 2026-09-26 at `86a55eb` + this stub):** before the stub, **15 failed / 80 passed**. After it, **14 failed / 81 passed**. **Structural = 0.** All 80 tests that were green at baseline are still green. The one newly green test is the allowlist exact-set pin, which is expected.
- **Gates:** `ruff check loremaster/tests/_surreal_harness.py` passes: "All checks passed!", rc 0. `scripts/typecheck.sh` fails with rc 1, but **none** of its 73 errors is in `_surreal_harness.py` or either contract file (§Typecheck).
- **Decisions needed:** none. One item is surfaced for the operator: typecheck is red at HEAD in 32 other files (§Surfaced).
- **Receipts:** §Diff · §Failure table · §Counts · §Typecheck · §Instrument (the junit classifier, pasted verbatim)

## Capability check (brief-base §4)
- **grep/rg:** hook-blocked. I used `awk` for textual reads of the harness and test sources. This is the sanctioned fallback for non-symbol textual seams: I was reading allowlist entries and name references by string. lore was loaded with `ToolSearch "+lore"`, but I did not need it: every structure question was a read of one named file.
- **Idle-gate contract file (brief-base §5):** this needs `<session-id>` in its path, and that id is not visible to me, so I did not write the file. The default `REPORT-stub-486.md` is what I owe, and it is present.
- **lore_comms register:** the brief named no orchestration session, so I did not register. My only outbound message is the §1 native micro-format line the brief requires.
- The brief demanded nothing else that I could not do.

## Stub scope
- Writable set honoured. Only `loremaster/tests/_surreal_harness.py` was edited. Both contract files hash identically before and after:
  - `test_surreal_harness.py` `6b150fbc2c7bac34`;
  - `test_harness_database_lifecycle_486.py` `c731fc98d7b28044`.

  These prefixes match those recorded in the contract report §Test paths. `conftest.py` was not touched.
- `run` and `unique_database` are unchanged, per the brief. `_MINTED_DATABASES` therefore stays empty (GREEN wires the recording), and `reap_minted_databases` raises `NotImplementedError`.
- The allowlist pin counts only module-level `Assign`/`AnnAssign`/`def`/`class` bindings (`_module_level_bound_names`); imports are not counted. So the added `Iterable` import is not a new module-level name under the exact-set pin. The pin went GREEN, which confirms it.
- A content backup of the pre-stub harness was taken before editing, in my session scratchpad. That is not a durable address; the pre-stub state is also just `git show HEAD:loremaster/tests/_surreal_harness.py`, since the harness had no diff at HEAD.

## Diff
```diff
@@ -61,7 +61,7 @@ import inspect
-from collections.abc import AsyncIterator, Awaitable, Callable
+from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
@@ -126,6 +126,9 @@ TIER_B = "community"
 _TEARDOWN_SELECT_DATABASE_LABEL = "harness.teardown.select_database"
 _TEARDOWN_REMOVE_DATABASE_LABEL = "harness.teardown.remove_database"
+# #486: the canonical event name ``run``'s own seam call site is attributed under — distinct
+# from both teardown labels, so an exhausted ``run`` is never blamed on teardown.
+_RUN_STATEMENT_LABEL = "harness.run.statement"
@@ -150,6 +153,12 @@ def surreal_password() -> SecretStr:
+# #486: every database name :func:`unique_database` minted in THIS process, mapped to the
+# node id of the test that minted it (``PYTEST_CURRENT_TEST`` at mint time). Mutated IN
+# PLACE, never rebound — a holder of this dict must see every later mint.
+_MINTED_DATABASES: dict[str, str] = {}
@@ -818,6 +827,26 @@ async def drop_database(env: SurrealEnv) -> None:
+async def reap_minted_databases() -> Iterable[str]:
+    """Remove every database this process minted that is still present, and name each one.
+
+    The session-end leg of #486's leak guard. It reads :data:`_MINTED_DATABASES` and removes
+    every recorded database that still exists in :data:`TEST_NAMESPACE`. It touches no other
+    database: another live session's mints, and databases this process never minted, are
+    left alone. Every engine call rides :func:`_run_under_store_retry_seam`, exactly as
+    :func:`drop_database`'s teardown does.
+
+    Returns:
+        The names of the databases it removed. Each one is a leak: its test minted it and
+        never dropped it. A database its test already dropped is never returned.
+
+    Raises:
+        TxnContentionExhaustedError: If the engine keeps reporting a retryable conflict on
+            one of the removals past the seam's budget.
+    """
+    raise NotImplementedError("Not yet implemented")
```

## Failure table (after stub; `uv run pytest -q -n 4 <both files> -p no:cacheprovider --junitxml=…`)
Exception types come from the junitxml traceback (§Instrument).

| node id | exception | class |
|---|---|---|
| test_surreal_harness.py::TestRunRidesTheStoreRetrySeam::test_a_once_conflicting_statement_is_retried_and_returns_the_success | `surrealdb.errors.QueryError` (injected conflict) | BEHAVIORAL |
| test_surreal_harness.py::TestRunRidesTheStoreRetrySeam::test_sustained_conflict_exhausts_with_the_seams_type_and_an_attributable_record | `surrealdb.errors.QueryError` (injected conflict) | BEHAVIORAL |
| test_surreal_harness.py::TestTheHarnessRetryPolicyIsTheSeamsPolicy::test_every_operation_follows_the_seams_attempt_ceiling[run:DELETE type::record('memory',] | `surrealdb.errors.QueryError` (injected conflict) | BEHAVIORAL |
| test_surreal_harness.py::TestTheHarnessRetryPolicyIsTheSeamsPolicy::test_every_operation_follows_the_seams_wall_clock_deadline[run:DELETE type::record('memory',] | `surrealdb.errors.QueryError` (injected conflict) | BEHAVIORAL |
| test_surreal_harness.py::TestTheHarnessRetryPolicyIsTheSeamsPolicy::test_run_detection_follows_the_seams_one_conflict_marker | `surrealdb.errors.QueryError` (injected conflict) | BEHAVIORAL |
| test_surreal_harness.py::TestTheHarnessMakesNoEngineCallOutsideTheSeam::test_every_engine_door_use_in_the_harness_is_an_attempt_body_of_the_seam | AssertionError (`['run:216 -> .query']`; `run` only, so the stub adds no door) | BEHAVIORAL |
| test_harness_database_lifecycle_486.py::TestTheTestDatabaseNamingRecipeExistsOnce::test_no_test_tree_builds_a_test_name_outside_unique_database | AssertionError (clone sites) | BEHAVIORAL |
| test_harness_database_lifecycle_486.py::TestAForeignDatabaseNameFailsTheSessionThatUsedIt::…[bare-hex-slug] | AssertionError | BEHAVIORAL |
| test_harness_database_lifecycle_486.py::TestAForeignDatabaseNameFailsTheSessionThatUsedIt::…[forged-harness-shape-same-pid] | AssertionError | BEHAVIORAL |
| test_harness_database_lifecycle_486.py::TestALeakedDatabaseIsReapedAndReported::…[n0] | AssertionError (minted DB outlived the session) | BEHAVIORAL |
| test_harness_database_lifecycle_486.py::TestALeakedDatabaseIsReapedAndReported::…[xdist-n2] | AssertionError (same) | BEHAVIORAL |
| test_harness_database_lifecycle_486.py::TestTheReaperRemovesExactlyWhatThisProcessLeaked::test_unique_database_records_the_name_and_the_minting_test | AssertionError (`database in registry`; the registry now exists but is empty) | BEHAVIORAL |
| test_harness_database_lifecycle_486.py::TestTheReaperRemovesExactlyWhatThisProcessLeaked::test_the_reaper_removes_a_leaked_database_and_spares_a_dropped_one | **NotImplementedError** (stub hit) | BEHAVIORAL |
| test_harness_database_lifecycle_486.py::TestTheHarnessDocstringClaimsNoReaperItLacks::test_the_harness_no_longer_claims_pid_reuse_reaps_orphans | AssertionError ("reused PID" still in the docstring) | BEHAVIORAL |

**Why the five `QueryError`s are BEHAVIORAL, not structural:** each one is the contract's own fake raising `Transaction conflict: Resource busy. This transaction can be retried`. That fault escapes because `run` does not yet ride `_run_under_store_retry_seam`. This is the exact behaviour GREEN changes; I extracted the message from each junit failure.

The five do not match any structural class in the brief: they are not ImportError, AttributeError, NameError, an arg-count TypeError or a SyntaxError. The label assertions in `…sustained_conflict…` sit AFTER the `pytest.raises` and read the label via `getattr(..., None)`, so no AttributeError is reachable now that the label exists.

**Leak note:** `…reaper_removes_a_leaked…` mints two DBs and hits the stub. Its `finally: drop_database(leaked_env)` removes the leaked one, and `dropped_env` was already dropped before the reaper call. I reasoned this from the test source and did not re-measure the namespace.

## Counts
| | failed | passed | structural |
|---|---|---|---|
| before stub (`86a55eb`, harness clean) | 15 | 80 | 0 (all AssertionError / injected QueryError) |
| after stub | 14 | 81 | **0** |

- Green→not-green: **none**. All 80 baseline-green tests are still green, derived by `comm` over the junit passed sets.
- Newly green (1): `test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_module_level_names_are_exactly_the_allowed_set`. This is expected: its only RED cause was the three undeclared names (§RED, "stub-level").
- The two other "stub-level" REDs in §RED stay RED behaviorally: `test_unique_database_records…` (empty registry) and `test_the_reaper_removes…` (NotImplementedError).
- Tails: before, `15 failed, 80 passed in 8.93s`; after, `14 failed, 81 passed in 9.20s`.

## Typecheck
`./scripts/typecheck.sh` gives rc 1:
- `loremaster`: 72 errors in 32 files, FAILED.
- `skills`: OK.
- `docs/eval`: OK.
- `scripts`: 1 error (`scripts/test_forgery_door_sweep.py:42`, `loremaster.tasks` has no `SupersedeResult`), FAILED.
- `shellcheck`: OK.

An awk filter over the full output for `_surreal_harness`, `test_surreal_harness`, `test_harness_database_lifecycle_486`, `_RUN_STATEMENT_LABEL`, `_MINTED_DATABASES` and `reap_minted_databases` gives **zero hits**. Every error is in 58/64b/63c in-flight files or their neighbours; none is attributed to the stub. Examples:
- `test_mcp_server.py:7776` `caller` kwarg on `FakeFindingLedger.resolve`;
- `test_retry_seam.py:200` `_txn.TxnUniqueViolationError`;
- the `test_findings_*_64b.py` / `test_reanchor_58_r*` files.

Bound: I attributed errors by file and message. I did not run a before-stub typecheck for a byte diff. A stub-induced error could only appear where these three names are used, and the filter shows none.

## §DRY ledger
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_RUN_STATEMENT_LABEL` | none (name and role fixed by contract §Stub expectations) | — | HAND-ROLLED per contract; it mirrors the sibling `_TEARDOWN_*_LABEL` identity convention |
| `_MINTED_DATABASES` | none (contract-fixed) | — | HAND-ROLLED per contract; the contract decides the name and type |
| `reap_minted_databases` | none (contract-fixed; stub body only) | — | HAND-ROLLED per contract. The GREEN body must REUSE `_run_under_store_retry_seam` / `_remove_database_with_retry`, as its docstring says |

I ran no search for these three because the exact-set allowlist makes the names a contract decision, not a reuse choice.

## Surfaced (the operator owns scope)
- **`scripts/typecheck.sh` is RED at HEAD `86a55eb`: 73 errors across 33 files**, all outside this change. That includes `test_mcp_server.py`, which is owned by another agent. Per CLAUDE.md, the currency gate (`pending_contract_gate.py --currency`) decides whether that red is RED_ADJUDICATED or RED_ORPHANED. I did not run it (it is outside the brief), so the lead should check it at close-out.
- There is no fork in the stub interface. §Stub expectations fixes `Iterable[str]` as the return type, and the stub follows it verbatim.

## Instrument (brief-base §1; pasted verbatim; used for every exception type and the before/after passed-set diff above)
```python
"""Classify pytest junitxml outcomes: node id -> outcome -> exception type.

Usage: python junit_classify.py <junit.xml>  (prints TSV: outcome, exc_type, nodeid)
Exception type is taken from the failure/error element's `message`/`type` attrs and
the LAST 'E   <Type>:' line of the traceback text, which is the raised type.
"""
import re
import sys
import xml.etree.ElementTree as ET

TB_TYPE = re.compile(r"^E\s+([A-Za-z_][\w.]*(?:Error|Exception|Exit|Failed|Interrupt))\b", re.M)

def main(path: str) -> None:
    root = ET.parse(path).getroot()
    for case in root.iter("testcase"):
        nodeid = f"{case.get('classname')}::{case.get('name')}"
        outcome, exc = "passed", ""
        for tag in ("failure", "error", "skipped"):
            el = case.find(tag)
            if el is not None:
                outcome = tag
                text = el.text or ""
                hits = TB_TYPE.findall(text)
                exc = hits[-1] if hits else (el.get("type") or el.get("message", "")[:60])
                break
        print(f"{outcome}\t{exc}\t{nodeid}")

main(sys.argv[1])
```
The passed-set diff was run as `comm -13 <(passed before) <(passed after)` for newly green, and as `comm -23` for tests that went from green to not green.
