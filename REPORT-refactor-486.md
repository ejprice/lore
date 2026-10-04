brief-base v18 read · brief project v7 read

# REPORT — refactor-486 (tdd-light Phase 5 REFACTOR + AUDIT, lore finding #486)

## SUMMARY BLOCK
- **State:** done-with-deviations. The targeted set is **NOT green**: 1 contract pin was RED both before and after my edits (F1). My edits caused 0 GREEN→RED.
- **Deviation 1:** to put a satisfiability receipt on the routing of F1, I transiently edited one contract test line, ran it, and restored it byte-exact (sha256 verified). The final diff contains no test edits. Details in §F1.
- **Deviation 2:** the brief named HEAD `a489e8e`. HEAD moved to `a75420d` during my run. That commit is docs-only (`REPORT-lead-63c.md`) and touches nothing graded here.
- **Packages considered:** none — no mechanism specified (refactor only; the GREEN's mechanisms, `_txn` seam + pytest/xdist hooks, were reviewed as REUSED/adapter and are correct as such)
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** none. No new symbols. My edits are annotations plus one import moved.
- **Graded:** working tree on `a489e8e` · HEAD-at-report `a75420d` · DIFFERENT (1 ahead; docs-only, `REPORT-lead-63c.md`; nothing graded moved)
- **Decisions needed:**
  - **F1 (BLOCKER for the commit):** contract pin `test_run_detection_follows_the_seams_one_conflict_marker` patches `_txn._RETRYABLE_CONFLICT_MARKER`, which `34d0b6b` deleted. It is RED with `AttributeError` and needs the same KIND retarget its two siblings got. The retarget is proven satisfiable. Route it to the contract owner.
  - **F2 (MEDIUM, constructed):** a mid-session `reap_minted_databases()` call silently swallows an earlier same-worker leak. The contract's own reaper test is such a caller. Route it as a contract/design item.
- **Receipts:** §Counts · §Gates · §F1 · §F2 (probe pasted verbatim) · §Test-smell table · §Removed-behaviour list

## Capability check (brief-base §4)
- grep/rg are hook-blocked (#473). Textual sweeps used `awk`. This is grep case (b), non-symbol textual seams: marker names, `use()` arg parsing, and scoped fixtures.
- lore was loaded and used: `lore_findings get 486`, `lore_comms register/heartbeat`, and one `lore_search` for an existing `use()`-argument extractor. That search returned only SurrealDB docs-tier hits because my query was unscoped, so I confirmed by awk that no other `event.method == "use"` site exists in `loremaster/tests`. This was my query's fault, not lore friction, so nothing was filed.
- Nothing the brief demanded was out of reach.

## The review (cold, before any edit)

### Reuse / ROUTING-IS-NOT-SHARING: PASS
- `_surreal_harness.run` hands one attempt body (`_statement`) to `_run_under_store_retry_seam(label=_RUN_STATEMENT_LABEL, …)`. It has no local classifier, budget, or backoff, so classification is the seam's: `_txn.retry_on_conflict` → the typed `_RETRYABLE_CONFLICT_KIND` since `34d0b6b`.
- ⚠ At HEAD the pin that PROVES this (the KIND/marker mutation at `run`) is the stale one (F1), so the sharing proof for `run` **does not currently execute**.
- My transient F1 probe is the only evidence at this tree that the sharing holds:
  - the control leg retried;
  - the mutated leg did not retry;
  - the result was 1 passed.
- Ceiling and deadline sharing are proven by the generated `[run:DELETE …]` mutation pins, which are GREEN in both runs.
- `reap_minted_databases` reuses `_remove_database_with_retry`, `connect_admin` and `drop_database`. Every engine call it makes rides the seam, and the reach pin `TestTheHarnessMakesNoEngineCallOutsideTheSeam` is GREEN.

### DRY: no in-harness duplication
- **Census duplication, kept on purpose.** `test_harness_database_lifecycle_486._databases_in_the_test_namespace` / `_remove_if_present` repeat the reaper's "minted reader → `INFO FOR NS` / `REMOVE DATABASE`" shape.
  - I left that as is, deliberately. Those helpers are the contract's ORACLE over the reaper.
  - Routing the oracle through the code it grades would make the leak legs grade the reaper with itself. Independence beats DRY here.
- `_sdk_guard` has no `use()`-argument extractor to reuse. `conftest._record_database_selection` is the only `event.method == "use"` site (awk over `loremaster/tests/*.py`).

### Efficiency: fine
- `run` evaluates `surreal_url()`, an env read, eagerly on each of ~812 call sites. The cost is negligible, and making it lazy would change behaviour for an empty `raw_url`. I left it.
- `_MINTED_DATABASES` grows by one entry per mint per process and is never pruned. The memory is negligible, and the reaper intersects it with what is present.

### Contract coverage: implementation covers it
- Every contract leg is GREEN except F1, which is stale.
- The 63c-i-a rebase onto HEAD is coherent. `_conflict_error()` already builds via `_engine_shapes.typed_conflict_error`. The `drop_database` siblings were retargeted to `_RETRYABLE_CONFLICT_KIND`. `test_mcp_server._slug` (HELD hunk 2) landed via 64b r2 (`cb220ee`) as `unique_database()`.
- ⚠ **Not covered by my targeted set:** test files that landed between `90d908f` and HEAD (63c-i-a / 64b / 58 contracts, ~30 files).
  - The recipe lint (GREEN) scans them statically.
  - The runtime provenance check (`_every_database_a_test_opens_was_minted_by_the_harness`) only fires when they run, so the cold audit's full suite is the first place a foreign `use()` in those files would show.

## Findings

| # | finding | class | disposition |
|---|---|---|---|
| F1 | `test_surreal_harness.py::TestTheHarnessRetryPolicyIsTheSeamsPolicy::test_run_detection_follows_the_seams_one_conflict_marker` does `monkeypatch.setattr(txn_module, "_RETRYABLE_CONFLICT_MARKER", …)`. `34d0b6b` (63c-i-a am-36) deleted that name, so the test is RED with `AttributeError` before and after my edits. Its docstring still argues in terms of the text marker. | A rebase certifying the OLD world: the a28c DUAL retarget reached the two `drop_database` siblings (`_RETRYABLE_CONFLICT_KIND`, `"AKindNoEngineEmits"`) but not the #486 pin written on a base before it. | **ROUTED** → contract owner (a test edit; not mine). Proven fix: the same one-line retarget as the siblings, plus the docstring ("marker" → "kind"). Satisfiability shown in §F1. |
| F2 | `reap_minted_databases()` removes **every** still-present mint of the process. Called mid-session, it silently reaps every earlier same-process leak, so `pytest_sessionfinish` finds nothing, and the session passes with no `LEAKED` line. The contract's `TestTheReaperRemovesExactlyWhatThisProcessLeaked::test_the_reaper_removes_a_leaked_database_and_spares_a_dropped_one` is such a caller: under `-n 8`, any leak earlier on the worker that runs it is swallowed. **Constructed, not reasoned** (§F2): control rc=1 with 1 `LEAKED` line; probe rc=0 with 0 lines. | CLASS: "every leak this process makes is REPORTED". The report lives in `pytest_sessionfinish`, but the removal lives in `reap_minted_databases`, which any caller can invoke. SIBLINGS TRIED: the contract's direct reaper test (probed). SIBLINGS NOT TRIED: no other caller exists today. Awk over `loremaster/tests/*.py` found two callers: `conftest.pytest_sessionfinish`, and that test (via `getattr(_surreal_harness, "reap_minted_databases")`). Its two other awk hits are docstring mentions. | **ROUTED** (behaviour + contract; not a refactor). Options at the STATE: (a) the reaper records what it removed into the session leak ledger, whoever calls it, so a removal is never unreported; or (b) the direct test reaps only its own two names, which needs a scoping parameter on the reaper, an interface change. (a) is the chokepoint fix. |
| F3 | `reap_minted_databases`: `present = set(info.get("databases", {})) if isinstance(info, dict) else set()`. An unexpected `INFO FOR NS` shape makes the reaper return `()`, a silent "no leaks". The census helper in the contract file has the same fallback. | False-clear on a degraded path (Leg 2 forgery: a wrong-shape store response serves the same bytes as "clean"). | **ROUTED** (raising would change behaviour). Low likelihood: the shape is stable on 3.2.4. |
| F4 | `test_harness_database_lifecycle_486._RECIPE_PREFIX = "test_"`. Its comment says the lint "reads it rather than restating a different one", but it is a restated literal. | Prose promising a derivation the code does not perform. Mitigated: `test_the_lint_sees_the_one_mint` goes RED if the mint's prefix drifts. | **ROUTED** (contract-file prose; low). |
| F5 | The recipe lint keys sites by `path.name` (basename). Two members with same-named test files would collide in `_DOCUMENTED_EXCEPTIONS` / `_THE_ONE_MINT`. | A reach keyed on a non-unique name. | **ROUTED** (latent; no collision today). |
| F6 | `conftest._record_database_selection(event: Any, …)` and `pytest_terminal_summary(terminalreporter: Any)` were untyped, although `_sdk_guard.CallEvent` / `pytest.TerminalReporter` exist. `import asyncio` was function-local, though stdlib with no ordering hazard. | quality | **FIXED** (§Edits) |
| F7 | `pytest_sessionfinish` connects to the store whenever ANY name was minted, including pure-unit sessions whose fixtures only mint slugs (e.g. `_auth_fixtures.slug()`). If the store is down, that is an INTERNALERROR at session end. | Already ruled: D-a (loud INTERNALERROR) was accepted. | No action. Listed so the cold audit does not re-raise it as new. |

I deliberately kept the lazy `from _surreal_harness import …` imports in `conftest.py`. They match the file's existing idiom (`from _sdk_guard import install` inside a fixture). They also read `_MINTED_DATABASES` at call time, which keeps them correct if a test ever patches the module attribute.

## Test-smell table (Phase 1 contract tests)
| smell | hit? | where / why |
|---|---|---|
| tautology | no | Expected values are read from the seam's live constants and the real store census, never from `run`/the reaper's own output. The reaper direct test checks the store state independently via `_databases_in_the_test_namespace`. |
| unrepresentative fixture | **yes (F2)** | The reaper direct test calls a session-end operation MID-session on a shared worker. That context differs from production's single `sessionfinish` caller, and it makes the test itself a leak-swallower. |
| no magnitude guard on a derived output | n/a | No numeric derived output. Attempt counts are pinned exactly to the seam's constant. |
| forward-run masquerading as validation | no | The e2e legs construct the leak/forgery and diff the store state. Positive and negative controls are present (`test_CONTROL_…`). |
| drift-prone hardcoded convention | **minor (F4, F5)** | `_RECIPE_PREFIX` is restated, not read (guarded by the non-vacuity pin). The lint is keyed on basenames. |
| stale pin vs. moved production (extra row) | **yes (F1)** | Pins a deleted name, RED for a reason unrelated to #486. |

## Edits made (file + symbol) — test-side only, all in #486's diff
`loremaster/tests/conftest.py`. Pre-edit backup: `cp -a` to scratchpad, sha256 recorded. Post-edit sha256 prefix: `e9941c5eafc65157`.
- module imports: `import asyncio` moved to the top-level stdlib block. It was removed from inside `pytest_sessionfinish`.
- `_record_database_selection`: `event: Any` → `event: _sdk_guard.CallEvent`. This is string-annotated under `from __future__ import annotations`, and `_sdk_guard` is imported at module level below.
- `pytest_terminal_summary`: `terminalreporter: Any` → `pytest.TerminalReporter` (exported by pytest 9.0.3, checked).

Nothing else was edited. No assertion was touched, and the contract files are byte-identical to before my run (`test_harness_database_lifecycle_486.py` sha256 prefix `c731fc98d7b28044`; `test_surreal_harness.py` `be5e6aee1beae055`, restored and verified with `sha256sum -c`).

## Counts (targeted; 2026-10-04, tree on `a489e8e`)
Scope: 27 test files. These are the brief's five named files (`test_harness_database_lifecycle_486`, `test_surreal_harness`, `test_memory_replay_fidelity_63b_ib`, `test_comms_wiring`, `test_retry_seam`) plus every `test_*.py` in `git diff HEAD --name-only`, deduplicated. Each run used `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q`. MemAvailable was 38.6 GiB, and no other lore pytest was alive.
- **BEFORE:** `1 failed, 1414 passed, 1 warning in 98.37s`, rc=1. The red was F1.
- **AFTER:** `1 failed, 1414 passed, 1 warning in 103.07s`, rc=1. The red was F1.
- Red-set diff (`comm -3` on the sorted FAILED/ERROR lines): **empty**, so 0 GREEN→RED and 0 RED→GREEN.
- Neither run printed a `LEAKED test database` line.
- The warning is pre-existing: `test_retry_seam.py::…test_scouts_live_subscription_is_retried`, `_empty_subscription` never awaited.

## Gates (2026-10-04)
- `uv run ruff check .` → `All checks passed!` (rc 0)
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`:
  - `typecheck RED_ADJUDICATED` (83 residuals, owned by packet-58-contract and packet-64b-i-contract; none names `conftest.py`, `_surreal_harness.py`, the lifecycle file or `test_comms_wiring.py`, checked with awk);
  - `ruff GREEN`;
  - `pytest NOT_RUN`, the known #533 line.
  - **RED_ORPHANED 0** for typecheck/ruff.

## §F1 — satisfiability of the proposed retarget (transient, restored)
1. Backup: `cp -a loremaster/tests/test_surreal_harness.py <scratchpad>/…orig`, with sha256 `be5e6aee…166b` recorded.
2. The single line in that test was changed:
   - from `monkeypatch.setattr(txn_module, "_RETRYABLE_CONFLICT_MARKER", "a marker no engine emits")`
   - to `monkeypatch.setattr(txn_module, "_RETRYABLE_CONFLICT_KIND", "AKindNoEngineEmits")`.
   These are the exact sibling values from `…TestTheHarnessRetryPolicyIsTheSeamsPolicy`'s two `drop_database` legs.
3. Running that one test gave `1 passed in 0.16s`. Both the control leg (`run` retried: 2 calls) and the mutated leg (1 call, raw `QueryError`) held.
4. Restored with `cp -a`, then `sha256sum -c` → `OK`.

I did not build wrong implementations against it. That is the grader's role (brief-base §2).

## §F2 — the constructed false clear (instrument pasted verbatim per brief-base §1)
Result, 2026-10-04, tree on `a489e8e`, TEST store `:18000`:
```
== control: rc=1 · LEAKED lines: 1 · 1 passed in 0.69s
== probe: rc=0 · LEAKED lines: 0 · 2 passed in 0.74s
```
- In the control leg, the leak is reported and the session fails, which is correct.
- In the probe leg, the same leak followed by a mid-session reaper call gives rc 0 and no report: a false clear.
- Residue census afterwards found no `test_<pid>_…` database for pids 1777290–1777500. The reader DB was minted and dropped.

```bash
#!/usr/bin/env bash
# Probe (refactor-486): does a MID-SESSION reap_minted_databases() call (as the contract's
# TestTheReaperRemovesExactlyWhatThisProcessLeaked does) silently swallow an EARLIER test's leak
# on the same worker, so the session-end leak report never fires?
#   Leg CONTROL: test_a leaks alone            -> expect rc!=0 and a LEAKED line naming test_a
#   Leg PROBE  : test_a leaks, test_b reaps    -> false clear iff rc==0 and no LEAKED line
# Runs the inner session exactly as test_harness_database_lifecycle_486._run_inner_session does
# (suite conftest loaded via -p conftest, repo ini kept out via -c /dev/null). TEST store only.
set -u
REPO=/home/ejprice/PycharmProjects/lore
OUT=${1:?scratch dir}
run_leg() {  # $1 leg name, $2 include reaper test (0/1)
  local dir="$OUT/$1"; rm -rf "$dir"; mkdir -p "$dir"
  {
    echo 'from _surreal_harness import PRODUCTION_DIM, connect_admin, make_env, unique_database, reap_minted_databases'
    echo 'async def test_a_leaks_its_database():'
    echo '    connection = await connect_admin(make_env(database=unique_database(), dim=PRODUCTION_DIM))'
    echo '    await connection.close()'
    if [ "$2" = 1 ]; then
      echo 'async def test_b_calls_the_reaper_mid_session():'
      echo '    await reap_minted_databases()'
    fi
  } > "$dir/test_inner_probe.py"
  (cd "$dir" && env -u PYTEST_XDIST_WORKER -u PYTEST_XDIST_WORKER_COUNT -u PYTEST_CURRENT_TEST \
     PYTHONPATH="$REPO/loremaster/tests" "$REPO/.venv/bin/python" -m pytest -p no:cacheprovider -q -rA \
     -c /dev/null --rootdir "$dir" -o asyncio_mode=auto -p conftest test_inner_probe.py > "$dir/out.log" 2>&1
   echo "rc=$?" >> "$dir/out.log")
  echo "== $1: $(tail -1 "$dir/out.log") · LEAKED lines: $(awk '/LEAKED test database/' "$dir/out.log" | wc -l) · $(awk '/passed|failed/' "$dir/out.log" | tail -1)"
}
run_leg control 0
run_leg probe 1
```
I ran it as `systemd-run --user --scope -p MemoryMax=4G -p MemorySwapMax=0 ./probe_reaper_midsession.sh <scratch-dir>`.
- **Litmus for the fix:** if a second mid-session caller appeared tomorrow, would the fix still report the leak? Option (a) does, because the removal itself records the report. Option (b) does not; it only fixes this one test.

## Removed-behaviour list (final diff vs HEAD, for the lead's deletion reconciliation)
**`_surreal_harness.py`**
- `run`: the bare `return await connection.query(statement, params)` is gone. `run` now:
  - retries a typed retryable conflict;
  - raises `TxnContentionExhaustedError` on exhaustion, with a `store.retry.exhausted` record labelled `harness.run.statement`, instead of a raw `QueryError`;
  - makes more than one wire call per `run` under conflict.
  These changes are **dropped-deliberately** (Phase 0 item 1).
- `run` still forwards `params=None` as `None`, and still returns the result object unlaundered and unchanged.
- `unique_database`: it gained a side effect (a registry write keyed by `PYTEST_CURRENT_TEST`). Its output shape `test_<pid>_<hex32>` is unchanged.
- Module docstring: deleted "Nothing leaks; a reused PID later harmlessly reaps any prior orphan" (false claim, retired) and replaced it with the session-end reap plus the D2 bound.
- Module docstring seam paragraph and `_run_under_store_retry_seam` docstring: "Both teardown operations … neither clones" became "every harness operation … none clones". The `operation` arg doc "true for both callers here" now names `run` and carries a multi-statement caveat.
- Import: `Iterable` was added (for the contract-fixed `reap_minted_databases() -> Iterable[str]` signature). Nothing was deleted.

**`conftest.py`** (all additions, no deletions):
- an import-time `_sdk_guard._CALL_HOOKS` append;
- the autouse provenance fixture, which fails tests that `use()` an unminted `lore_test` DB;
- `pytest_sessionfinish` reap with exitstatus escalation OK→TESTS_FAILED;
- the xdist `pytest_testnodedown` merge;
- the `pytest_terminal_summary` leak lines.
- **New behaviour:** a session that minted any name now dials the store at session end (F7 / D-a).

**Clone sites (24 in 23 files):**
- `f"test_{uuid.uuid4().hex}"` (and `test_bulk_{…}` in `test_indexer_bulk_sweep`, and `test_{uuid.getnode() % 100000}_{…}` in `test_startup_divergence_reconcile`) became `unique_database()`. **The database name shape changes** from `test_<hex32>` to `test_<pid>_<hex32>`, and the `test_bulk_` prefix is gone.
- `test_ingest_entity_seam`: the `probe_`/`entprobe_` + `tmp_path.name` slugs became `unique_database()`.
- `import uuid` was deleted in 21 files: 20 module-level deletions plus the one function-local import in `test_resilient_db::_build_realistic_config`.
  - Re-derived 2026-10-04 by awk over `git diff HEAD -U0`, one deletion per file.
  - ⚠ `REPORT-implement-486.md` says "19 module-level". That is off by one. It is an inherited number, now corrected.

**`test_comms_wiring._open_context`:**
- It no longer returns `build_app_context(...)` directly. A failed build now drops the DB and re-raises.
- On the returned context, `aclose` is SHADOWED by an instance attribute that closes and then drops the DB. Every borrower's `aclose` now has a DB-drop side effect, including the 2 in `test_mcp_server`.
- The module's `_pending_surreal_slugs` autouse reaper still runs too, so the drop is double. That is harmless because the removal is `REMOVE DATABASE IF EXISTS`.

**`test_startup_divergence_reconcile._slug`:** the docstring sentence "no separate `unique_database()` call is needed" was deleted, because it is now false.

**`test_surreal_harness.py` (contract edits):** `query_outcomes` was widened (`list[BaseException | None]` → `list[Any]`), and the operation-discovery set now also drives `run`.
