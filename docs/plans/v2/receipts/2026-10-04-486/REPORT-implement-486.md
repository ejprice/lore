brief-base v17 read · brief project v7 read

# REPORT — implement-486 (tdd-light Phase 4 GREEN: #486 harness `run()` retry + the test-DB leak)

## SUMMARY BLOCK
- **State:** waiting:64b-r2, for the final full-suite run only. Lead rulings round 1 was applied at 2026-09-27; see §Rulings round 1.
  - D-a and D-b were accepted as built.
  - HELD hunk 2 was re-routed to contract-64b-r2, and I did not apply it.
  - HELD hunks 1+3 were rejected. The leak is now fixed at the PRODUCER, `test_comms_wiring._open_context`, which is verified leak-free.
  - **No HELD work remains with me.**
- **Deviation 1:** I converted a straggler that is **outside the M4 list**, `test_ingest_entity_seam.py` (two `probe_`/`entprobe_` slugs). The brief's VERIFY clause ("each one is a finding to fix (convert it) or report") is my authority. The file was clean in git before I edited it. Its conversion made 5 provenance errors go GREEN (45/45).
- **Deviation 2:** I corrected stale prose at one converted site (`test_startup_divergence_reconcile.py::_slug`'s docstring said "no separate `unique_database()` call is needed").
- **Deviation 3 (superseded by ruling):** the consumer-side drain I proposed in `test_mcp_server.py` was rejected. The producer-side fix replaces it (§Rulings round 1).
- **Packages considered:**
  - Worker→controller report: pytest 9.0.3 `pytest_sessionfinish` plus xdist 3.8.0 `workeroutput`/`pytest_testnodedown`. I read the hookspec and the contract's `-n 2` leg, and the verdict is `replace_with_adapter`.
  - Retry: `_txn` via `_run_under_store_retry_seam`, REUSED.
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** 5 new conftest symbols and 0 new harness names, all dispositioned (§DRY ledger)
- **Graded:** n/a (implementer) · HEAD-at-start `f61ebe6` · HEAD-at-report `90d908f` (9 docs-only commits in between, none touching a file of mine)
- **Decisions needed:** none open. D-a and D-b were ruled ACCEPTED, and the HELD patch was re-routed to 64b-r2.
- **Receipts:** §Rulings round 1 · §Contract-files · §Full suite (run 1 + adjudication) · §HELD (patch + out-of-tree verification) · §Typecheck/ruff · §Instruments

## Capability check (brief-base §4)
- grep/rg are hook-blocked (#473). My textual sweeps used `awk`, which is sanctioned grep case (b) for non-symbol textual seams. They covered: prose near converted sites, the retired claim, the conftest-source pins, the higher-scoped fixtures, and the ingest slug sites. Each fallback is named where it is used.
- lore was loaded, and `lore_comms` registered me (`implement-486` / `63c-20260924`, cadence ≤20m) with heartbeats per milestone. Every structure read was a file the brief named. No lore structure query was needed, because the reuse targets are enumerated in the brief's §REUSE and I read them directly.
- Idle-gate `.contract`: I could not see my own session id with certainty, so I wrote it under both candidate ids.
- Nothing the brief demanded was out of reach.

## What changed (per file; cited by symbol)
### `loremaster/tests/_surreal_harness.py` (on top of the stub)
- **`run`**: its `connection.query(statement, params)` is now the body of an inner `_statement()` handed to `_run_under_store_retry_seam(label=_RUN_STATEMENT_LABEL, url=…)`.
  - The URL is `connection.raw_url`, which every real SDK connection carries (read from `AsyncWsSurrealConnection.__init__`). When that is absent (a scripted fake), it falls back to `surreal_url()`. The fallback avoids a new module-level name, which the exact-set allowlist forbids.
  - The return value is the attempt's own object, not laundered, and `params=None` is forwarded as `None`.
- **`unique_database`**: records `name → os.environ.get("PYTEST_CURRENT_TEST", "")` into `_MINTED_DATABASES`, in place.
- **`reap_minted_databases`**:
  1. Snapshots the registry (its own reader mint lands in it mid-call).
  2. Mints a reader DB, `connect_admin`s it, and reads `INFO FOR NS` via `run` (so through the seam).
  3. Removes `snapshot ∩ present` via `_remove_database_with_retry` (seam, teardown label), naming each target.
  4. It never `use()`s a target, and it closes and drops the reader in `finally`.
  5. It returns a sorted tuple.
- **Docstrings**:
  - The module docstring drops "Nothing leaks; a reused PID later harmlessly reaps any prior orphan". It now states the session-end guarantee and the D2 bound, verbatim to the ruling: a killed session leaves strays, which periodic operator wipes remove.
  - The docstrings of the module seam paragraph and `_run_under_store_retry_seam` now include `run`, so their "every/single classify-and-signal site" claims are true again. I also added the multi-statement re-runnability caveat on `operation`.

### `loremaster/tests/conftest.py`
- **Observer** `_record_database_selection`: a `_sdk_guard` call hook, appended ONCE at import (GOTCHA-B idempotence guard). For each `use(TEST_NAMESPACE, db)`, it records `db` into `_DATABASES_OPENED_THIS_TEST`. It records and never raises, because a raise would surface inside production code that may wrap connection errors. The verdict comes at teardown.
- **Autouse** `_every_database_a_test_opens_was_minted_by_the_harness`: clears at setup. At teardown it `pytest.fail`s, naming every opened DB that is not in `_MINTED_DATABASES`.
  - Ordering (measured, not assumed): pytest 9.0.3 `parsefactories` iterates `dir()`, so autouse fixtures run alphabetically.
  - Requested fixtures that dial are set up after every autouse fixture and torn down before them, so their `use()` calls are observed.
  - The guard's monkeypatch lives on `monkeypatch`, which was set up by an earlier autouse fixture, so it stays armed through those teardowns.
- **`pytest_sessionfinish`**: reaps if the registry is non-empty.
  - On an xdist worker, it writes a JSON report to `workeroutput[_LEAK_REPORT_WORKEROUTPUT_KEY]`.
  - Otherwise, it records the leaks and escalates `session.exitstatus` OK → TESTS_FAILED. It never downgrades a worse code.
- **`pytest_testnodedown`** (`optionalhook`): the controller merges each worker's report.
- **`pytest_terminal_summary`**: writes `LEAKED test database <name> (minted by <nodeid>) — reaped…` per leak.

### The clone sites
- The 23 M4 files other than the HELD one, converted by the §Instruments I-A script:
  - `_auth_fixtures`, `test_build_store`, `test_cli`, `test_comms_send_scope_63b_ii_a`, `test_comms_wiring`, `test_eager_startup_survives_unparseable_file`, `test_extension` ×2, `test_graph_wiring`, `test_impact`, `test_indexer`, `test_indexer_bulk_sweep`, `test_indexer_chunker_fault_isolation`, `test_indexer_contextualized`, `test_map`, `test_memory_cutover`, `test_reconcile`, `test_resilient_db`, `test_schema_rebuild`, `test_search`, `test_startup_divergence_reconcile`, `test_static_snapshot_reacquire`, `test_watcher`, `test_workspace_status`.
  - That is 24 sites, each now `unique_database()`.
  - Orphaned `import uuid` deleted: 19 module-level, plus `test_resilient_db::_build_realistic_config`'s function-local one.
  - Imports were merged and sorted by `ruff --select I --fix`, restricted to those files.
- **`test_ingest_entity_seam.py`** (Deviation 1): `_build_probe_app_context` and `_build_entity_probe_app_context` built `probe_`/`entprobe_` + `tmp_path.name`. That is not unique across concurrent sessions (a cross-session collision hazard too), and the `test_`-prefix lint cannot see it (contract bound #17). The provenance leg caught it at runtime, as designed. Both slugs now come from `unique_database()`.
- **`test_startup_divergence_reconcile.py::_slug`**: docstring corrected (Deviation 2).
- Every file in the writable set was `git status`-clean before I edited it, except `test_mcp_server.py`, which I did not touch.
- The contract test files are unmodified: sha256 prefixes are `6b150fbc2c7bac34` / `c731fc98d7b28044`, as recorded in the contract.

## Reuse receipts
- Retry: `_surreal_harness._run_under_store_retry_seam`, which is the only classify-and-signal point. Its classifier is `_txn.is_retryable_conflict_error`, and its budget and backoff come from `_txn.retry_on_conflict`. `run` has no local marker and no local budget.
  - Sharing is proven by the contract's own generated mutation pins, all GREEN on this build: `test_every_operation_follows_the_seams_attempt_ceiling[run:DELETE …]`, `…wall_clock_deadline[run:…]` and `test_run_detection_follows_the_seams_one_conflict_marker`, which moves `_txn._RETRYABLE_CONFLICT_MARKER` and requires `run` to stop retrying.
  - I did not run a separate mutation of my own. The builder is not the grader, and the contract's pins are the instrument.
- Removal: `_remove_database_with_retry` (the teardown idiom). The reader lifecycle uses `make_env` + `connect_admin` + `drop_database`.
- Observer: `_sdk_guard._CALL_HOOKS` / `CallEvent`, appended once at import (`_governed_contract` GOTCHA-B).
- Reach: the contract's `TestTheHarnessMakesNoEngineCallOutsideTheSeam` is GREEN, so every door use in the harness is covered.

## Rulings round 1 (lead, 2026-09-27): applied
- **D-a:** accepted as built (loud INTERNALERROR). **D-b:** accepted (bounds stated in code and docstring). No change.
- **HELD hunk 2** (`test_mcp_server.py::_slug`, `f"test_{uuid.uuid4().hex}"` → `unique_database()`): **re-routed to contract-64b-r2** and NOT applied by me. `uuid` stays used elsewhere in that file, so there is no import change.
- **HELD hunks 1+3** (the consumer-side drain): **rejected**. They are replaced by a PRODUCER-side fix in `test_comms_wiring.py`, which is in my writable set.
- **The producer fix: `test_comms_wiring._open_context` now owns its database's lifetime.**
  - It builds `make_env(database=slug, dim=_DIM)`.
  - If `build_app_context` raises, it drops the database and re-raises (`except BaseException`).
  - On success, it shadows the instance's `aclose` with `_aclose_and_drop_database`, which awaits the original `aclose` and then, in a `finally`, calls `drop_surreal_database(database_env)`.
  - Every existing `await context.aclose()` therefore reaps the database with no call site changed: the 11 in-file uses plus the 2 in `test_mcp_server`.
  - `# type: ignore[method-assign]` is used on the shadowing assignment, and mypy reports it as used (0 errors in the file).
  - It is idempotent with `test_comms_wiring`'s own autouse reaper, which still drains `_pending_surreal_slugs`: `drop_database` is `REMOVE … IF EXISTS`.
- **The class this closes:** a borrowed helper whose database cleanup depended on the lending module's autouse fixture. The fix makes the cleanup travel with the helper.
  - Importers of `test_comms_wiring`, from an awk scan (the sanctioned textual fallback): only `test_mcp_server.py:139`, which imports `_backdate_heartbeat` and `_open_context`.
  - `test_comms_footer.py:4357` calls a `_slug()`, but it does not import it from `test_comms_wiring`, and run 1 showed no leak there.
  - Bound: a borrowed helper that mints and dials but is never `aclose`d still leaks. That leak is caught loudly by the session-end reap, not by this fix.
- **Receipts (2026-09-27, `90d908f` + WIP):**
  - `uv run pytest -q -n 8 -p no:cacheprovider -rfE loremaster/tests/test_comms_wiring.py` → **`28 passed in 31.11s`, rc=0, 0 LEAKED lines** (full log checked).
  - The scratch copy of `test_mcp_server.py` differs from the main tree by the one `_slug` line ONLY (`diff` output: `374c374`). It was run with the suite conftest (`PYTHONPATH=loremaster/tests … -p conftest -c /dev/null --rootdir <scratch>`) over `::TestCadenceWiredThroughTheDispatch`:
    - `-n 0` → **`2 passed`, rc=0, 0 LEAKED**.
    - `-n 2` → **`2 passed`, rc=0, 0 LEAKED**.
    - ⚠ The first `-n 2` attempt exited **rc=143 with an empty log** (external SIGTERM). Two other lore pytest suites were live at the time, and MemAvailable read 18.4 GB, which is plausibly another session's memory watchdog. The retry was clean. I report both runs, per the brief.
  - The RED control for the same two tests is the pre-fix producer: run 1 (in-tree) and the earlier scratch run both printed 2 `LEAKED … TestCadenceWiredThroughTheDispatch` lines.
  - `ruff check .` → `All checks passed!` · `scripts/typecheck.sh` → 0 errors in `test_comms_wiring.py`, harness, conftest, or `test_ingest_entity_seam.py`. The totals (86 loremaster + 1 scripts) sit entirely in other agents' in-flight files.
- **Remaining wait:** 64b-r2's commit (which carries hunk 2), and then the final full-suite run.

## Contract-files receipt (measured 2026-09-27 at `90d908f` + this build)
`uv run pytest -q -n 4 -p no:cacheprovider loremaster/tests/test_surreal_harness.py loremaster/tests/test_harness_database_lifecycle_486.py`
→ **`1 failed, 94 passed in 9.78s`**.
- The 1 is `test_no_test_tree_builds_a_test_name_outside_unique_database`, listing exactly one site: `test_mcp_server.py:374 in _slug()`, which is HELD. It goes GREEN when the HELD patch lands.
- RED→GREEN: the contract's baseline was 15 failed / 80 passed and the stub's 14 / 81. Everything the stub left red is now green except the HELD-bound lint.
- Before the clone conversion, the same run gave `1 failed, 94 passed` with 25 sites listed.

## Converted-file receipts
- The 23 files that directly mint (the `_auth_fixtures` helper is exercised by the full suite): `uv run pytest -q -n 8 … <22 test files>` → **`585 passed in 124.93s`**, rc 0, no `LEAKED` line.
- `test_ingest_entity_seam.py` after conversion: `-n 6` → **`45 passed in 19.66s`**.
- `ruff check .` → `All checks passed!` (repo-wide, after all edits).

## Full-suite receipt (run 1, 2026-09-27 00:08–00:18, `-n 12`, another lore `-n 12` suite live, 15 GB MemAvailable watchdog)
- Runner: §Instruments I-B. Every variable is assigned before the `&`, and the run is killed by process GROUP. The watchdog log shows no fire: `run rc=1 finished 00:18:23`. MemAvailable read 25.4 GB mid-run.
- Tail: **`596 failed, 11978 passed, 63 skipped, 3 xfailed, 9 warnings, 633 errors in 596.50s`**.
- Classified from the junit XML by §Instruments I-C.

**PROVENANCE bucket (the #486 check firing, by design): 633 errors.**
- 628 in `test_mcp_server.py`, naming 643 databases. **All 643 are shaped `test_<hex32>`**, which is the `_slug` recipe the HELD patch replaces.
- 5 in `test_ingest_entity_seam.py` (the `probe_`/`entprobe_` straggler). **Now fixed**: 45/45 after conversion.
- No other file fired. **None of M7's 39 fixed-literal `database=` values dialed a store** (0 provenance hits outside those two files).

**OTHER bucket: 596 failures.** Every file is registered in `scripts/pending_contracts.yaml`, with one exception: `test_harness_database_lifecycle_486.py` ×1, the HELD lint.
- The registration check is file-level substring presence (bound: I did not match node ids against the registry).
- Messages are uniformly 58/63c/64b in-flight shapes:
  - `cannot import name 'arm_finding_identity' from '_finding_fakes'`;
  - `FakeFindingLedger.report() … 'title'`;
  - `AppContext.findings() … 'capability'`;
  - `Module "loremaster.tasks" has no attribute "SupersedeResult"` and the re-anchor assertions;
  - `test_retry_seam`'s guarded-CAS door-set enumeration;
  - `scripts/test_forgery_door_sweep` (58 am-1 door count, and mypy outside the gate).
- Per-file counts are in §Instruments I-C output (pasted below).
- **0 new reds attributable to #486.** The lint red is the HELD site. The provenance reds are the designed straggler detector: one family fixed, one HELD. No red carries `can be retried` or `harness.run.statement`, so run 1 showed no #486 escape and no `run` exhaustion (0 hits in the junit bodies and the log).

**LEAKED lines in run 1: 2, both real and pre-existing, and loud as designed.**
- `test_mcp_server.py::TestCadenceWiredThroughTheDispatch::test_register_cadence_through_the_dispatch` and `::test_heartbeat_cadence_through_the_dispatch`.
- Cause: they borrow `test_comms_wiring._open_context`. That function queues the slug on `test_comms_wiring._pending_surreal_slugs`, and only `test_comms_wiring`'s own autouse fixture drains that list; it is not active in `test_mcp_server`. Before #486 these leaked silently as `test_<hex32>`.
- This also proves the xdist worker→controller report works in a real `-n 12` run: both lines printed on the controller with the minting node id.
- Fix: HELD hunk 1 + 3 below.

A second full run was not done. Everything changed after run 1 was covered by a scoped run: the `test_ingest_entity_seam.py` conversion (45/45) and a docstring-only edit.

## HELD — `loremaster/tests/test_mcp_server.py` (SUPERSEDED by §Rulings round 1: hunk 2 re-routed to 64b-r2; hunks 1+3 rejected in favour of the producer fix. Kept as the record of what was proposed.)
- `git apply --check -p1` against the working tree at `90d908f` + WIP → **APPLY-CHECK-OK**.
- `uuid` stays imported, because it is still used elsewhere in the file (AST-checked).
- **Out-of-tree verification.** I ran the patched copy under the suite's conftest with the contract's inner-session wiring (`PYTHONPATH=loremaster/tests … -p conftest -c /dev/null`):
  - Hunk 2 alone, `-n 12`: **`28 failed, 638 passed`**. PROVENANCE is **0**, and the 28 OTHER reds are exactly the 64b-WIP set seen in run 1. The 2 LEAKED lines still printed.
  - Hunks 1+2+3, `::TestCadenceWiredThroughTheDispatch`: **`2 passed in 8.56s`**, with no LEAKED line.
  - The copy passes ruff.
- **Sequence:** apply together with, or after, 64b-r2's commit. Until then `test_mcp_server.py` carries 628 provenance teardown errors in any run.
```diff
--- a/loremaster/tests/test_mcp_server.py
+++ b/loremaster/tests/test_mcp_server.py
@@ -137,6 +137,7 @@
     assert_render_injection_safe,
 )
 from test_comms_wiring import _backdate_heartbeat, _open_context
+from test_comms_wiring import _pending_surreal_slugs as _comms_wiring_pending_slugs
 
 # CORPSE-A / removed-behaviour-1 (packet 63a): the governed memory retrofit makes the
 # packet 63a-ii (design §10.7-Y, operator ruling A): the AppContext composition root
@@ -371,7 +372,7 @@
 
 def _slug() -> str:
     """A unique per-test project slug, ALSO the default SurrealDB database name."""
-    slug = f"test_{uuid.uuid4().hex}"
+    slug = unique_database()
     _pending_surreal_slugs.append(slug)
     return slug
 
@@ -393,9 +394,12 @@
     try:
         yield
     finally:
-        for slug in _pending_surreal_slugs:
+        # _open_context (borrowed from test_comms_wiring) queues its slug on THAT module's
+        # list, whose own reaper is not active here — drain both, or the database leaks (#486).
+        for slug in (*_pending_surreal_slugs, *_comms_wiring_pending_slugs):
             await drop_surreal_database(make_env(database=slug, dim=_DIM))
         _pending_surreal_slugs.clear()
+        _comms_wiring_pending_slugs.clear()
```
- Alternative reading of hunks 1+3: the fix could instead live in `test_comms_wiring._open_context` (make the borrowed helper self-reaping). I chose the consumer-side drain because it leaves `test_comms_wiring`'s contract unchanged. Either reading closes the leak, and the lead/owner picks.

## Typecheck / ruff
- `./scripts/typecheck.sh` gave rc 1.
  - loremaster: `Found 83 errors in 33 files`. scripts: 1 error. lorescribe, loresigil, skills, docs/eval and shellcheck: OK.
  - An awk filter over every file I touched (harness, conftest, the 24 converted and edited files, and both contract files) gives **0 errors**.
  - The per-file tally (§Instruments I-C sibling) is entirely 58/63c/64b in-flight files. The non-64b-named ones are `test_retry_seam:200` (`TxnUniqueViolationError`), `test_task_guarded_shell_58:59`, `test_blocks_edge:347`, `test_task_claimable_partition_58:54`, `test_task_read_surface:233` (`SupersedeResult`) and `test_comms_footer:4233` (`arm_finding_identity`). None is mine.
- `uv run ruff check .` → `All checks passed!`

## Decisions (surfaced; the operator/lead owns them)
- **D-a — session end now needs the store whenever a name was minted.** `pytest_sessionfinish` reaps if `_MINTED_DATABASES` is non-empty, and many offline tests mint names without dialing (for example `test_build_store`'s sentinel-URL slug). If the store is unreachable at session end, the reap raises out of the hook: pytest prints INTERNALERROR and the exit code is 3. Loud, never silent, but a store-free subset run with the store down now fails at the end.
  - Alternative 1: reap only names this process observed being dialed. That is narrower, and it misses a slug that a subprocess server dials.
  - Alternative 2: catch, print "could not verify N minted databases", and fail with rc 1.
  - I kept the minimal loud form. The in-image conformance run (packet 01a) needs the store reachable at session end, as its tests already do.
- **D-b — reaper bounds (stated in code comments and the harness docstring; not pinned by me):**
  - (i) The observer fires only while the per-test guard is armed, so a module- or session-scoped fixture's `use()` goes unobserved. The awk census found 3 higher-scoped fixtures in the test trees, none minting a DB.
  - (ii) Only `TEST_NAMESPACE` is observed (contract bound #19).
  - (iii) A mid-session call of `reap_minted_databases()` (the contract's direct pin) also reaps any EARLIER test's still-present leak in that worker. That removes the leak, but it drops the leak's report line.
  - (iv) A killed session: D2.
- **D-c — the `test_`-prefix lint's blind spot is real, not theoretical.** `test_ingest_entity_seam`'s `probe_` slugs are the measured instance, and only the runtime leg caught them. Any other non-`test_` slug recipe that has not dialed yet is invisible until it does.

## Surfaced
- The 2 pre-existing `TestCadenceWiredThroughTheDispatch` leaks (HELD fix above).
- `test_ingest_entity_seam`'s `tmp_path.name` slugs were also a cross-session name-collision hazard, now closed.
- Out of scope, left for the lead: the contract report's own surfaced items (38 `pytest.raises(Exception)` sites, the `_count` helpers) are unchanged by this build.

## §DRY ledger (new reusable symbols; all in `conftest.py`)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_record_database_selection` | none; brief §REUSE names `_sdk_guard._CALL_HOOKS` as the mechanism | — | **REUSED `_sdk_guard._CALL_HOOKS`/`CallEvent`**; the hook is the only new code |
| `_every_database_a_test_opens_was_minted_by_the_harness` | none (contract §Stub expectations fixes the mechanism's home) | — | **HAND-ROLLED**: no existing provenance check. It reads the harness's `_MINTED_DATABASES` |
| `pytest_sessionfinish` / `pytest_testnodedown` / `pytest_terminal_summary` | none (pytest/xdist hook API) | — | **REUSED pytest + xdist hooks**. The reap itself is `reap_minted_databases` |
| `_LEAK_REPORT_WORKEROUTPUT_KEY`, `_DATABASES_OPENED_THIS_TEST`, `_REAPED_LEAKS` | n/a (identity constant and state) | — | HAND-ROLLED state, no policy |
- There are no new `_surreal_harness` names beyond the three the stub declared (exact-set allowlist GREEN).

## §Instruments (pasted verbatim, brief-base §1)
### I-A clone conversion (adapted from the contract's I-10; HELD file excluded; orphaned `uuid` removal)
```python
"""Convert the #486 clone sites (contract §Builder worklist item 5) to unique_database().

Adapted from the contract's I-10 instrument: test_mcp_server.py is EXCLUDED (HELD, 64b-r2 in
flight), and an import of `uuid` left unused by the conversion is deleted (ruff F401).
Prints per-file replacement counts and whether an import was added / uuid removed.
"""
import ast
import re
import sys
from pathlib import Path

CLONES = {
    "_auth_fixtures.py", "test_build_store.py", "test_cli.py", "test_comms_send_scope_63b_ii_a.py",
    "test_comms_wiring.py", "test_eager_startup_survives_unparseable_file.py", "test_extension.py",
    "test_graph_wiring.py", "test_impact.py", "test_indexer.py", "test_indexer_bulk_sweep.py",
    "test_indexer_chunker_fault_isolation.py", "test_indexer_contextualized.py", "test_map.py",
    "test_memory_cutover.py", "test_reconcile.py", "test_resilient_db.py", "test_schema_rebuild.py",
    "test_search.py", "test_startup_divergence_reconcile.py", "test_static_snapshot_reacquire.py",
    "test_watcher.py", "test_workspace_status.py",
}
PATTERN = re.compile(r'f"test_(?:bulk_|\{uuid\.getnode\(\) % 100000\}_)?\{uuid\.uuid4\(\)\.hex\}"')
root = Path(sys.argv[1])
total = 0
for name in sorted(CLONES):
    path = root / name
    source = path.read_text()
    converted, count = PATTERN.subn("unique_database()", source)
    total += count
    tree = ast.parse(converted)
    notes = []
    has_import = any(
        isinstance(node, ast.ImportFrom) and node.module == "_surreal_harness"
        and any(alias.name == "unique_database" for alias in node.names)
        for node in tree.body
    )
    if not has_import:
        last = max(node.end_lineno for node in tree.body if isinstance(node, ast.Import | ast.ImportFrom))
        lines = converted.splitlines(keepends=True)
        lines.insert(last, "from _surreal_harness import unique_database\n")
        converted = "".join(lines)
        notes.append("import-added")
    tree = ast.parse(converted)
    uuid_used = any(isinstance(node, ast.Name) and node.id == "uuid" for node in ast.walk(tree))
    if not uuid_used:
        lines = converted.splitlines(keepends=True)
        kept = [line for line in lines if line != "import uuid\n"]
        if len(kept) != len(lines):
            converted = "".join(kept)
            notes.append("uuid-import-removed")
    path.write_text(converted)
    print(name, count, " ".join(notes))
print("total replaced:", total)
```
Output: `total replaced: 24` (test_extension 2, every other file 1). It was followed by `ruff check --select I --fix <those files>`, which reported `22 fixed`, plus the manual removal of `test_resilient_db`'s function-local `import uuid`.

### I-B full-suite runner with the MemAvailable watchdog
```bash
#!/usr/bin/env bash
# Full lore suite at -n 12 under a host-MemAvailable watchdog (kills the run's process GROUP).
# Every variable is assigned in its own statement BEFORE any backgrounding.
set -u
SCRATCH="$1"
LABEL="$2"
REPO=/home/ejprice/PycharmProjects/lore
LOG="$SCRATCH/full_$LABEL.log"
XML="$SCRATCH/full_$LABEL.xml"
WATCHDOG_LOG="$SCRATCH/watchdog_$LABEL.log"
THRESHOLD_KB=$((15 * 1024 * 1024))
cd "$REPO"
setsid uv run pytest -q -n 12 -p no:cacheprovider -rfE --junit-xml="$XML" -o junit_family=xunit1 > "$LOG" 2>&1 &
RUN_PID=$!
echo "run pid $RUN_PID started $(date -Is)" > "$WATCHDOG_LOG"
while kill -0 "$RUN_PID" 2>/dev/null; do
  AVAILABLE_KB=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
  if [ "$AVAILABLE_KB" -lt "$THRESHOLD_KB" ]; then
    echo "WATCHDOG FIRED $(date -Is): MemAvailable ${AVAILABLE_KB}kB < ${THRESHOLD_KB}kB; killing group $RUN_PID" >> "$WATCHDOG_LOG"
    kill -TERM -- "-$RUN_PID" 2>/dev/null
    sleep 5
    kill -KILL -- "-$RUN_PID" 2>/dev/null
    break
  fi
  sleep 2
done
wait "$RUN_PID"
RC=$?
echo "run rc=$RC finished $(date -Is)" >> "$WATCHDOG_LOG"
exit "$RC"
```

### I-C red classifier (junit xunit1 → PROVENANCE vs OTHER, per file)
```python
"""Classify every failed/errored testcase in a pytest junit xml (xunit1) for #486 adjudication.

Buckets: PROVENANCE (the #486 per-test check fired: a test opened an unminted database),
OTHER. Prints per-file counts per bucket, and writes the OTHER node ids + first message line
to <xml>.other.tsv, and the PROVENANCE node ids + named databases to <xml>.provenance.tsv.
Usage: python classify_reds.py <junit.xml>
"""
import collections
import sys
import xml.etree.ElementTree as ET

PROVENANCE_MARK = "NOT minted by `_surreal_harness.unique_database()`"
path = sys.argv[1]
counts: dict[tuple[str, str], int] = collections.Counter()
other_rows, provenance_rows = [], []
for case in ET.parse(path).getroot().iter("testcase"):
    for tag in ("failure", "error"):
        element = case.find(tag)
        if element is None:
            continue
        text = (element.get("message") or "") + "\n" + (element.text or "")
        node = f"{case.get('file') or case.get('classname')}::{case.get('name')}"
        file_name = (case.get("file") or case.get("classname") or "").split("/")[-1]
        bucket = "PROVENANCE" if PROVENANCE_MARK in text else "OTHER"
        counts[(file_name, f"{bucket}:{tag}")] += 1
        first = (element.get("message") or "").splitlines()[0][:160] if element.get("message") else ""
        (provenance_rows if bucket == "PROVENANCE" else other_rows).append(f"{node}\t{tag}\t{first}")
for (file_name, bucket), n in sorted(counts.items()):
    print(f"{n:5d} {bucket:20s} {file_name}")
open(path + ".other.tsv", "w").write("\n".join(other_rows) + "\n")
open(path + ".provenance.tsv", "w").write("\n".join(provenance_rows) + "\n")
print("OTHER total", len(other_rows), "PROVENANCE total", len(provenance_rows))
```
Run-1 output, per file (the OTHER failure count, unless marked otherwise):

| file | count |
|---|---|
| test_blocks_edge | 1 |
| test_comms_footer | 81 |
| test_findings_adversary_pins_64b | 13 |
| test_findings_classes_64b | 21 |
| test_findings_enforcement_64b | 4 |
| test_findings_governance_64b | 24 |
| test_findings_identity_64b | 22 |
| test_findings_migrate_64b | 28 |
| test_findings_schema_64b | 17 |
| test_findings_scope_domain_64b | 12 |
| test_findings_signatures_64b | 2 |
| test_findings_system_writer_64b | 9 |
| test_fixwave_a19a_63c_i_a | 2 |
| test_fixwave_a19b_63c_i_a | 2 |
| test_fixwave_a28_63c_i_a | 76 |
| test_fixwave_a28b_63c_i_a | 24 |
| test_forgery_door_sweep | 3 |
| test_governed_substrate_64b | 34 |
| test_harness_database_lifecycle_486 | 1 |
| test_ingest_entity_seam | **5 PROVENANCE:error** |
| test_mcp_server | 28, plus **628 PROVENANCE:error** |
| test_reanchor_58_r2_am2 | 3 |
| test_reanchor_58_r2_probes | 12 |
| test_reanchor_58_r2_rulings | 27 |
| test_reanchor_58_r2_scale | 2 |
| test_reanchor_58_r3_am6 | 8 |
| test_reanchor_58_r3_cas_seam | 7 |
| test_reanchor_58_r3_convergence | 42 |
| test_reanchor_58_r3_probes | 6 |
| test_reanchor_58_r3_relate | 2 |
| test_reanchor_58_r3_tiers | 16 |
| test_retry_seam | 2 |
| test_supersede_reanchor_58 | 44 |
| test_task_claimable_partition_58 | 5 |
| test_task_guarded_shell_58 | 15 |
| test_task_read_surface | 1 |

Totals: `OTHER total 596 PROVENANCE total 633`.

### I-D provenance name-shape tally (run inline over the same junit XML)
The script pulls each provenance error's named databases, maps each to a shape (`test_<hex32>` or digits/hex → `#`), and counts per file.
- Result: `643 test_mcp_server.py :: test_<hex32>`.
- Plus 5 single `test_ingest_entity_seam.py :: probe_…`/`entprobe_…`.
