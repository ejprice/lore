brief-base v18 read · brief project v7 read

# REPORT — implement-486-r4 (GREEN, #486 follow-up: R2 · #538 · #537, 2026-10-04)

## SUMMARY BLOCK
- **State:** done. Edited only `loremaster/tests/conftest.py`, `pyproject.toml` and `uv.lock`; `_surreal_harness.py` is byte-identical. Nothing committed. Base HEAD `3714837`.
- **Targeted after-run:** `873 passed, 2 skipped` in 175 s. Before: `2 failed, 871 passed, 2 skipped` (the reds were #537/F1 and #538). Same 875 collected, every contract cell GREEN, 0 GREEN→RED (§2).
- **R2:** `anyio.fail_after` bounds the reap and the daemon thread is gone. **Mutation A** (`fail_after(None)`) → exactly `[wedged-n0]` + `[wedged-xdist-n2]` RED, both "did not END within 180s" → `PROOF HELD` (§3).
- **#538:** a default-deny per-worker report-gap map on the controller. **Mutation B** (the gap set forced empty) → exactly the #538 pin RED, CONTROL green → `PROOF HELD`. An offline probe covers the doors the contract does not construct: crash, missing key, corrupt JSON, wrong shape, `None` value, and a node-down that never fired. Each is a gap; both reporting workers (one clean, one that crashed after reporting) are accounted (§3, §A).
- **#537:** `pytest-timeout` 2.4.0 is now a dev dependency. F1 is GREEN under plain `uv run pytest`, under `--with pytest-timeout -n 8` and under `-n 0`. `--with` now resolves to `.venv`, with no overlay (§4).
- **Deviations:** none.
- **Packages considered:**
  - session-end bound: `anyio` 4.13.0, verdict `replace` (applied). Read: the installed `fail_after` source (`create_cancel_scope(deadline=…)`, which raises `TimeoutError` iff `cancelled_caught` and the deadline has passed) and coldaudit-486-2 §4 probe §A.1.
  - report validation: `pydantic.TypeAdapter.validate_json`, verdict `replace` (over hand `isinstance` checks). Read: live probe, where None/int/non-JSON/wrong-shape each → `ValidationError`.
  - #537: `pytest-timeout` 2.4.0, added.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 6 new conftest symbols, all dispositioned (§5); 0 in `_surreal_harness.py`.
- **Graded:** n/a (implementer).
- **Decisions needed:** none. Flags for the lead, in §6: (F-a) a KNOWN BOUND of R2, a non-cancellable block in the reap path; (F-b) pytest-timeout now ships in the image venv.
- **Receipts:** §2 runs · §3 mutation proofs · §4 F1 · §5 DRY · §6 flags · §7 removed-behavior inventory · §8 gates/md5/diff · §A probe instrument (verbatim).

## Capability check (brief-base §4)
- grep/rg are hook-blocked on the main checkout (live-indexed); textual scans use awk. Said here per dogfood protocol.
- `lore_impact` on the conftest hooks (`_reap_within_budget`, `pytest_testnodedown`) returns covering tests = conftest itself only:
  pytest hook dispatch is framework-mediated and invisible to the graph. Covering tests were derived by hand (awk over test trees for the
  conftest/harness seam names) — §Scope.
- Idle-gate contract: `/tmp/claude-idle-gate-lore/unknown-implement-486-r4.contract` (session id not visible to me).
- Deadline: 90 min from spawn (spawn ≈23:35Z → 01:05Z).

## Scope (targeted set derivation)
- Contract files: `test_harness_database_lifecycle_486.py`, `test_no_raw_listener_in_test_trees.py`.
- Briefed: `test_surreal_harness.py`.
- Hand-derived covering tests (awk for `_reap_within_budget|_SESSION_END_REAP_BUDGET|_UNREAPED_REPORT_WORKEROUTPUT|_LEAK_REPORT_WORKEROUTPUT|pytest_testnodedown|conftest.py|_surreal_harness.py` over every test tree):
  `test_retry_seam.py` (scans `_surreal_harness.py`), `test_caplog_isolation.py` (conftest), `test_store_seam_one_derivation.py`.
  Rejected hits: `scripts/test_gated_ground.py` (synthetic `conftest.py` fixtures, not ours), `test_findings_signatures_64b.py` (writes its own tmp conftest), `_governed_contract.py` (helper, not a test).
- Runner: scratch `run_targeted.sh` (MemAvailable ≥ 20 GiB wait; no other lore pytest; `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300`).

## §1 What changed (measured 2026-10-04 on base `3714837`, uncommitted)
- **R2 — `loremaster/tests/conftest.py::_reap_within_budget`.** The daemon thread + `reaper.join(budget_seconds)` is gone. The reap
  now runs on the calling thread via `anyio.run(_bounded_reap)`, and `_bounded_reap` awaits `reap_minted_databases()` inside
  `anyio.fail_after(budget_seconds)`. Same budget constant (`_SESSION_END_REAP_BUDGET_SECONDS = 30.0`, untouched). On expiry it returns the
  same `TimeoutError("no answer within the 30s session-end reap budget")`, so `_reap_failure_outcome` still classifies it `unreachable`
  and `_unreaped_line` prints the same loud could-not-verify line. The scope's `cancelled_caught` separates the budget's own expiry
  from a `TimeoutError` the reap raised itself (which is returned as is, exactly as the thread version returned it). Imports: `asyncio` and
  `threading` dropped (no other use in the file), `anyio` added. The `pytest_sessionfinish` comment about an abandoned thread still marking
  entries is rewritten, since no thread exists any more.
- **#538 — the controller chokepoint, `conftest.py`.**
  - New controller state `_SESSION_END_REPORT_GAP_BY_WORKER: dict[str, str | None]`, **default-deny**. `pytest_testnodeready` (new,
    `optionalhook`) enters each worker with the gap `"it never went down"`. `pytest_testnodedown` is the ONE place a worker's report is read.
    It clears the gap (`None`) only when BOTH keys are present and parse to their shapes. Otherwise it records why: a missing key, with
    "(the worker went down with an error)" when `error` is set, or an unreadable value (pydantic shape errors). A corrupt value can no longer
    crash the controller's hook (the old `json.loads` would have raised).
  - The failing is done in the existing controller branch of `pytest_sessionfinish`: `_workers_without_session_end_report()` joins
    `_REAPED_LEAKS` / `_UNREAPED_AT_SESSION_END` in the one `exitstatus` check. `pytest_terminal_summary` writes one line per worker:
    `xdist worker gw<n> finished WITHOUT its session-end report (<gap>) — …`. The line never carries the worker's error text. ⚠ CORRECTED in §9 (coldaudit-486-3 F-2): the next claim, "xdist already prints that", is FALSE for the raised-hook case (error is None, xdist prints nothing). xdist
    already prints that, and in the contract's construction the error text IS the injected raise, which the pin filters out.
  - Shapes are `pydantic.TypeAdapter` (`_LEAK_REPORT_SHAPE`, `_UNREAPED_REPORT_SHAPE`), not hand-written isinstance checks.
  - Worker id is `node.gateway.id`, as xdist names it in its own lines (`_worker_id`).
- **#537 — `pyproject.toml` + `uv.lock`:** `uv add --dev pytest-timeout` → `pytest-timeout>=2.4.0` (2.4.0 resolved), with a comment in the
  idiom of the group. Measured after: `uv run --with pytest-timeout python -c 'sys.prefix'` → `/home/…/lore/.venv` (uv no longer builds
  an overlay env once the requirement is satisfied by the project env). That is the mechanism coldaudit-486-2 §3 named for F1.
- `_surreal_harness.py`: **untouched**. That keeps D-r2b-1 (no new module-level name) trivially, and the shared seams (`_run_under_store_retry_seam`,
  `governed.map_of`, `_MINTED_DATABASES`) are reached exactly as before, through `reap_minted_databases`.

## §2 Targeted runs (6 files, §Scope; `-n 8 --timeout=300`, 16G cgroup, MemAvailable ≥ 20 GiB + no other lore pytest confirmed before each)
| run | tree | tail |
|---|---|---|
| BEFORE (≈23:45Z) | HEAD `3714837` + contract files (md5s as briefed) | `2 failed, 871 passed, 2 skipped, 1 warning in 174.72s` — F1 #537 + `TestEveryXdistWorkerReportsItsSessionEnd::test_a_worker_that_never_shipped…` |
| AFTER (≈23:58Z) | this change | `873 passed, 2 skipped, 1 warning in 175.17s` · rc=0 |
- The 1 warning (`test_retry_seam.py:3263` "coroutine '_empty_subscription' was never awaited") appears in both runs: it predates this change and is not attributable to it. Flagged, not touched.
- The F1 runs and mutation proofs were each preceded by a MemAvailable read (27.7 / 28.1 GiB) and a `pgrep` (0 other lore pytest), not by the looping wait script. Stated for honesty.

## §3 Mutation proofs (`scripts/mutation_proof.py`; declared ids from `--collect-only`; predictions written to scratch before each run)
- **A — R2's bound is load-bearing.** Anchor `with anyio.fail_after(budget_seconds) as deadline:` → `with anyio.fail_after(None) as deadline:`, over the whole 486 file.
  Result: `2 failed, 57 passed in 188.07s`, `tree restored byte-exact (… md5 94f821754d8e37d0e613ef2f16f77dcc)`, `PROOF HELD`, rc 0.
  Both REDs read `Failed: the inner session against ws://127.0.0.1:<port>/rpc did not END within 180s — a session-end step is waiting on a TEST store that will never answer…`.
  This is the right reason: with the anyio deadline gone, nothing a dependency owns ends the wedged reap, so `fail_after` is the bound.
- **B — #538's chokepoint is load-bearing.** Anchor: the body of `_workers_without_session_end_report`, replaced with `return {}`. Scope: the `TestEveryXdistWorkerReportsItsSessionEnd` class.
  Result: `1 failed, 1 passed in 4.16s`, restored byte-exact (same md5), `PROOF HELD`, rc 0. The CONTROL stayed GREEN.

## §4 #537 / F1 under every runner form (≈00:05Z, single node id)
| runner | tail |
|---|---|
| `uv run pytest` (plain) | `1 passed in 0.10s` |
| `uv run --with pytest-timeout pytest -n 8 --timeout=300` | `1 passed in 1.45s` |
| `uv run --with pytest-timeout pytest -n 0 --timeout=300` | `1 passed in 0.10s` |
- Mechanism check: `uv run python -c "import sys; print(sys.prefix)"` and the same under `--with pytest-timeout` both print `/home/ejprice/PycharmProjects/lore/.venv`, with an identical `purelib`. With the requirement satisfied by the project env, uv builds no overlay, so `_is_installed_third_party` sees the project plugins again. That is coldaudit-486-2 §3's mechanism, now confirmed by measurement rather than reading.

## §5 DRY ledger (brief-base §6)
| new symbol (conftest) | lore query run | returned | disposition |
|---|---|---|---|
| `_SESSION_END_REPORT_GAP_BY_WORKER`, `_workers_without_session_end_report`, `pytest_testnodeready`, `_worker_id` | `lore_search "xdist controller reads worker workeroutput report and validates it; worker id of a node"` | an adversary report's bash screen (unrelated); no xdist-node helper anywhere | HAND-ROLLED: test-local controller state; the only existing reader is this file's own `pytest_testnodedown`, which was EXTENDED in place, not forked |
| `_LEAK_REPORT_SHAPE`, `_UNREAPED_REPORT_SHAPE` | same query + package question | — | REUSED the package (`pydantic.TypeAdapter`); the shapes mirror the worker side's `json.dumps(report)` / `json.dumps(unreaped)` types in `pytest_sessionfinish` |
| `_bounded_reap` (nested in `_reap_within_budget`) | package question (anyio) | `anyio.fail_after` | REUSED the package; replaces the bespoke thread bound |
- `_reap_failure_outcome`, `_unreaped_line`, `_SESSION_END_REAP_BUDGET_SECONDS` and the transport classifier (`loremaster.store._txn._SDK_AWAIT_BOUNDARY_ERRORS` / `is_connection_error`) are REUSED unchanged. The budget expiry still returns a `TimeoutError` (an `OSError`), so it routes through the ONE classifier to `unreachable`. No classification was cloned.

## §6 Flags (everything noticed; the operator owns scope)
- **F-a — KNOWN BOUND of R2 (the trade the thread made in the other direction):** anyio can cancel only what yields to the loop. A **non-cancellable block** in the reap path would now hang `pytest_sessionfinish` on the main thread, where the daemon thread used to abandon it: a synchronous blocking call, a `CancelScope(shield=True)`, or an executor thread joined at `anyio.run`'s runner shutdown.
  - What I read: `reap_minted_databases` (every engine call is an awaited SDK call through `_run_under_store_retry_seam`, and its `finally` is two awaits); `lore_search "anyio CancelScope shield=True"` (its one hit is the server's trace middleware, not the reap path).
  - What I measured: all four lost states (refused / silent / muted / wedged) end within the 120 s end-bound leg, and wedged is proven bound by `fail_after` (mutation A).
  - So `fail_after` CAN bound the reap as constructed, and the brief's STOP condition is not met.
  - Bound: this is pinned only for the states the contract constructs.
  - **Re-open trigger:** any sync blocking call, shielded scope or `to_thread` added to the reap path (`reap_minted_databases` → `connect_admin` / `run` / `_remove_database_with_retry` / `drop_database`).
  - Not pinned by a dedicated test (a test-tree change, outside my writable set). Lead's call whether the contract should add one.
- **F-b — the image venv now carries pytest-timeout.** The `Containerfile` runs `uv sync --all-packages`, which bakes the dev group into `/app/.venv` (see the `coverage` comment in `pyproject.toml`). The change is additive, and nothing shipped imports it. Stated so nobody reads a new package in the image as drift.
- **F-c — `git diff --stat` lists the two contract test files.** They are the uncommitted contract (md5s exactly as briefed). They are NOT my edits.
- **F-d — pre-existing warning:** `test_retry_seam.py::TestEverySdkCallSiteActuallyRetries::test_scouts_live_subscription_is_retried` emits `RuntimeWarning: coroutine '_empty_subscription' was never awaited`, in both the BEFORE and the AFTER run. It is not mine. Want it examined?
- **F-e — `lore_impact` cannot see pytest hook dispatch:** the covering tests for the conftest hooks came back as conftest itself only. That is a known framework-mediated limit (its caveat says so). Covering tests were derived by awk instead (§Scope). Not filed as new friction: the tool's own caveat names the class.

## §7 Removed-behavior inventory (the deleted daemon-thread bound, and the reshaped `pytest_testnodedown`)
| # | old behavior | fate |
|---|---|---|
| 1 | Session-end reap bounded at `_SESSION_END_REAP_BUDGET_SECONDS` (30 s) wall-clock | **preserved-with-pin**: the wedged × {n0, xdist} cells + the 120 s end-bound leg over all 4 lost states. Mutation A proves `fail_after` is the bound |
| 2 | On expiry: `TimeoutError("no answer within the 30s session-end reap budget")` → `unreachable` → loud could-not-verify line naming the DBs | **preserved-with-pin**: same f-string. The lost-store cells assert the `unreachable` line naming the DB, rc ≠ 0, `1 passed` |
| 3 | A hung reap was ABANDONED in a daemon thread, so the process could exit past it | **dropped-deliberately**: brief R2 (coldaudit-486-2 §4). anyio cancels level-triggered, in-loop, so there is nothing to abandon. The residual (a non-cancellable block) is F-a, a known bound with a trigger |
| 4 | The reap's own exception (any `BaseException`) returned to the caller for classification | **preserved for `Exception`** (unpinned beyond R5's `failed` cells, which pin a `SurrealStoreError`). `KeyboardInterrupt`/`SystemExit` now propagate. Old: a Ctrl-C landed in the main thread's `join` and propagated anyway, so this is equivalent for Ctrl-C. A `SystemExit` raised BY the reap would now end the session (none exists). Spec-silent: noted, not pinned |
| 5 | A `TimeoutError` the reap raised itself (not the budget) returned as is | **preserved**, via the scope's `cancelled_caught`. Spec-silent: no construction raises one before the budget, so unpinned |
| 6 | The reap's own event loop (`asyncio.run`, in the thread) | **replaced** by `anyio.run` (asyncio backend, same `asyncio.Runner` teardown) on the calling thread |
| 7 | Thread name `lore-session-end-reap`; the "abandoned thread may still be marking entries" snapshot hazard | **dropped**: no observer of the name. The hazard no longer exists; the snapshot stays and its comment was rewritten |
| 8 | `pytest_testnodedown`: an empty or absent key was skipped silently (`if serialized:`) | **dropped-deliberately**: that silence IS #538. An absent key is now a gap that fails the session (pinned: the #538 cell + mutation B) |
| 9 | `pytest_testnodedown`: a corrupt value raised `json.loads` errors inside the controller hook | **dropped-deliberately**: it is now a named gap (offline probe §A; no pytest pin constructs it, per contract §3 "SIBLINGS NOT TRIED") |
| 10 | `pytest_testnodedown`: one key present and valid, the other missing → the present one was still merged | **changed**: neither is merged and the worker is a gap. A half report is not an accounted worker, and the session fails either way. Unpinned (probe gw2 covers it) |

## §8 Gates, md5s, diff (≈00:12Z)
- `uv run ruff check loremaster/tests/conftest.py` → `All checks passed!`; `ruff format --check` → formatted; single-file `mypy` → `Success: no issues found`.
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` → typecheck `RED_ADJUDICATED — 83 residual(s)`, owned by packet-58-contract and packet-64b-i-contract. That is the same count contract-486-r4 §9(c) recorded, so this change added none. ruff `GREEN`. **RED_ORPHANED 0 among the legs run.** pytest `NOT_RUN` by design (no full suite; the leg prints its #312 orphan notice, which is the expected rendering of a deliberately-unrun leg).
- Contract md5s (unchanged): `6440b108c12a7fc37dc72f9f8fed5c46  test_harness_database_lifecycle_486.py` · `f6f6f73f529a05bc940a0499239e2380  test_no_raw_listener_in_test_trees.py`.
- `_surreal_harness.py` `fd443e2a2a998b2511d1ba6866ed6747`: `cmp` against my pre-edit backup shows it identical. Final conftest md5 `94f821754d8e37d0e613ef2f16f77dcc`.
- `git diff --stat`:
```
 loremaster/tests/conftest.py                       | 124 ++++++--
 .../tests/test_harness_database_lifecycle_486.py   | 349 ++++++++++++++++++++-
 .../tests/test_no_raw_listener_in_test_trees.py    |  68 +++-
 pyproject.toml                                     |   5 +
 uv.lock                                            |  14 +
 5 files changed, 516 insertions(+), 44 deletions(-)
```

## §A Instrument — the #538 door probe (verbatim; run `uv run python <file>` from the repo root; output in §SUMMARY)
```python
"""Drive conftest's #538 chokepoint through every door with fake xdist nodes (no store, no pytest run)."""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

TESTS = Path("/home/ejprice/PycharmProjects/lore/loremaster/tests")
sys.path.insert(0, str(TESTS))
spec = importlib.util.spec_from_file_location("lore_conftest_probe", TESTS / "conftest.py")
conftest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conftest)

GOOD = {conftest._LEAK_REPORT_WORKEROUTPUT_KEY: "[]", conftest._UNREAPED_REPORT_WORKEROUTPUT_KEY: "[]"}


def node(worker, workeroutput=None):
    fake = SimpleNamespace(gateway=SimpleNamespace(id=worker))
    if workeroutput is not None:
        fake.workeroutput = workeroutput
    return fake


doors = {
    "gw0 clean report": ([node("gw0", GOOD)], None),
    "gw1 crashed, no workeroutput": ([node("gw1")], "Traceback ... worker died"),
    "gw2 leak key missing": ([node("gw2", {conftest._UNREAPED_REPORT_WORKEROUTPUT_KEY: "[]"})], None),
    "gw3 corrupt (non-json)": ([node("gw3", {**GOOD, conftest._LEAK_REPORT_WORKEROUTPUT_KEY: "{oops"})], None),
    "gw4 wrong shape": ([node("gw4", {**GOOD, conftest._UNREAPED_REPORT_WORKEROUTPUT_KEY: json.dumps([["x"]])})], None),
    "gw5 None value": ([node("gw5", {**GOOD, conftest._LEAK_REPORT_WORKEROUTPUT_KEY: None})], None),
    "gw7 crashed AFTER a readable report": ([node("gw7", GOOD)], "worker died after finishing"),
}
for _label, (nodes, error) in doors.items():
    for each in nodes:
        conftest.pytest_testnodeready(each)
        conftest.pytest_testnodedown(each, error)
conftest.pytest_testnodeready(node("gw6"))  # came up, node-down never fired
gaps = conftest._workers_without_session_end_report()
for worker in sorted(conftest._SESSION_END_REPORT_GAP_BY_WORKER):
    print(f"{worker}: {'ACCOUNTED' if worker not in gaps else 'GAP — ' + gaps[worker]}")
expected_gaps = {"gw1", "gw2", "gw3", "gw4", "gw5", "gw6"}
assert set(gaps) == expected_gaps, set(gaps) ^ expected_gaps
print("PROBE OK: every non-reporting door is a gap; both reporting workers are accounted for")
```
Output (≈23:57Z):
```
gw0: ACCOUNTED
gw1: GAP — no 'lore_486_leaked_test_databases' value arrived (the worker went down with an error)
gw2: GAP — no 'lore_486_leaked_test_databases' value arrived
gw3: GAP — its report could not be read (1 shape error(s))
gw4: GAP — its report could not be read (2 shape error(s))
gw5: GAP — its report could not be read (1 shape error(s))
gw6: GAP — it never went down
gw7: ACCOUNTED
PROBE OK: every non-reporting door is a gap; both reporting workers are accounted for
```

## §9 Round 2 (lead brief 2026-10-05 ~00:33Z: P1 hard outer bound · P3 gap wording · R-2 · R-6)
**State: done (00:45Z).** Writable set: `loremaster/tests/conftest.py` only. Pre-edit backup: scratch `r2/conftest.before-r2.py` (md5 `94f821754d8e37d0e613ef2f16f77dcc`).
- Pre-flight: no test pins the old wording of items 3–4. I ran an awk over every `*.py` outside `.venv` for `test-namespace wipe|WITHOUT its session-end|could not verify that`, and the only hit is a docstring in the 486 file (`TestTheGapLineNeverContradictsItsCause`), which is not a pin.

### §9.1 What changed (`loremaster/tests/conftest.py` only; `94f82175…` → `2de2b7ee0de9a69a5a91aa7244b371e4`)
- **P1 — the hard outer bound (am-37 §14 Q2).** In `_reap_within_budget`, `anyio.run(_bounded_reap)` now sits inside
  `faulthandler.dump_traceback_later(_SESSION_END_HARD_BOUND_IN_BUDGETS * budget_seconds, exit=True, file=real_stderr)`, and
  `faulthandler.cancel_dump_traceback_later()` runs in a `finally`. The four §10 seams are KEPT:
  - the budget is the argument `pytest_sessionfinish` reads from the module attribute `_SESSION_END_REAP_BUDGET_SECONDS` at call time, and the hard bound is derived from it;
  - `reap_minted_databases` is imported from `_surreal_harness` inside the function, at call time;
  - the frame is named `_reap_within_budget`;
  - `real_stderr = sys.__stderr__`, falling back to `sys.stderr` only if `__stderr__` is `None`, which keeps the types honest.

  New module constant `_SESSION_END_HARD_BOUND_IN_BUDGETS = 2`. Lead ruling on §10's fork applied: the cooperative control stays rc ≠ 0 with the existing loud line (unchanged code path).
- **P3 — the gap's wording is derived from the gap.** A gap is now `_SessionEndReportGap(went_down: bool, cause: str)` (a `NamedTuple` with a `line(worker)` method). `went_down` is set by WHICH hook recorded it: `pytest_testnodeready` → `False`, `pytest_testnodedown` → `True`. The lifecycle clause comes from `_GAP_LIFECYCLE_BY_WENT_DOWN[went_down]`:
  - `"went down WITHOUT its session-end report"`;
  - `"never went down and sent no session-end report"`.

  No string is special-cased. ⚠ **The audit's example wording would fail the contract's own pin.** "did not report its session-end before the session **ended**" contains `ended`, which `TestTheGapLineNeverContradictsItsCause._ENDED_CLAIM` forbids for the never-went-down door. So I did not use it. The never-went-down cause text also avoids every `_ENDED_CLAIM` verb: `no node-down arrived before the controller's session-finish`.
- **R-2.** When a key is missing, the cause now reads `no '<key>' value arrived; <why>`, where `<why>` is one of:
  - `error is not None` → `the worker went down with an error`;
  - `error is None` → `the worker reported no error, so a session-finish hook in it may have raised before the harness's`.

  The round-1 §1 claim "xdist already prints that" is corrected in place (it is false for `error is None`).
- **R-6.** One constant, `_UNVERIFIED_DATABASES_REMEDY = "the operator's periodic test-namespace wipe removes them"`, is served by BOTH `_unreaped_line` and `_SessionEndReportGap.line`. ONE implementation, not two copies of the phrase.

Served lines, captured through the conftest's own hooks (instrument `r2/probe_gap_lines.py`, pasted in §9.6):
```
xdist worker gw0 never went down and sent no session-end report (no node-down arrived before the controller's session-finish) — whatever test databases it opened were neither reaped-and-named nor reported unverified. They may still be on the TEST store; the operator's periodic test-namespace wipe removes them
xdist worker gw1 went down WITHOUT its session-end report (no 'lore_486_leaked_test_databases' value arrived; the worker reported no error, so a session-finish hook in it may have raised before the harness's) — …same tail…
xdist worker gw2 went down WITHOUT its session-end report (no 'lore_486_leaked_test_databases' value arrived; the worker went down with an error) — …same tail…
xdist worker gw3 went down WITHOUT its session-end report (its report could not be read (1 shape error(s))) — …same tail…
```

### §9.2 Targeted runs (6 files, the §Scope set; every run through scratch `r2/gate.sh`, which WAITS for MemAvailable ≥ 20 GiB AND no other lore pytest; 16G cgroup; `-n 8 --timeout=300`; :18000)
| run | gate | tail |
|---|---|---|
| BEFORE | `GATE CLEAR 00:34:11: MemAvailable 32293588 KiB, no other pytest` | `5 failed, 904 passed, 4 skipped, 1 warning in 179.99s`: exactly the 4 P1 blocking cells + P3 `[never went down]` (the contract's declared REDs) |
| AFTER | `GATE CLEAR 00:37:31: MemAvailable 33331004 KiB, no other pytest` | **`909 passed, 4 skipped, 1 warning in 179.63s`**, rc=0. The same 913 were collected, 0 GREEN→RED. The warning is the pre-existing `test_retry_seam.py:3263` one (§6 F-d) |

### §9.3 Mutation proof — the hard bound is load-bearing
- The anchor is the whole 3-line `faulthandler.dump_traceback_later(…)` call (`--anchor-file r2/mutP1.anchor`), replaced by a comment.
- The 4 declared ids came from `--collect-only`, filtered to `TestTheSessionEndReapHasAHardOuterBound` × `blocking` (`r2/mutP1.declared`). The prediction was written before the run (`r2/mutP1.prediction`).
- Scope: the whole 486 file. Gate: `GATE CLEAR 00:40:49`.
- **Result:** `4 failed, 91 passed, 2 skipped in 56.33s`, `tree restored byte-exact (loremaster/tests/conftest.py: md5 2de2b7ee0de9a69a5a91aa7244b371e4)`, **`PROOF HELD`**, rc 0.
- The RED reason: `AssertionError: a SYNC block in the session-end reap held the process 20.3s past the session-end step's start — over the 9s hard bound (2 × 2s budget + 5s)…`. That is the right reason: without faulthandler, nothing ends a sync block. Every COOPERATIVE cell stayed GREEN, so the anyio bound still carries those on its own.

### §9.4 Gates, md5s, diff (00:44Z)
- `ruff format` + `ruff check loremaster/tests/conftest.py` → clean. Single-file `mypy` → `Success`.
- `pending_contract_gate.py --currency --legs typecheck,ruff`: typecheck `RED_ADJUDICATED — 83 residual(s)` (unchanged count, all owned by packet-58 / packet-64b-i); ruff `GREEN`; **RED_ORPHANED 0** over the legs run. pytest `NOT_RUN` by design.
- md5s: 486 file `3c981b3ea9936c46ec08cd47df25109b` (= brief) · guard file `f6f6f73f529a05bc940a0499239e2380` (= brief) · `_surreal_harness.py` `fd443e2a2a998b2511d1ba6866ed6747` (untouched; D-r2b-1 holds) · conftest `2de2b7ee0de9a69a5a91aa7244b371e4`.
- `git diff --stat` (it includes the uncommitted contract files and the round-1 pyproject/uv.lock, none edited this round):
  ```
   REPORT-implement-486-r4.md                         |   4 +
   loremaster/tests/conftest.py                       | 186 ++++-
   .../tests/test_harness_database_lifecycle_486.py   | 857 ++++++++++++++++++++-
   .../tests/test_no_raw_listener_in_test_trees.py    |  68 +-
   pyproject.toml                                     |   5 +
   uv.lock                                            |  14 +
  ```

### §9.5 Removed-behavior rows (changed line text and changed mechanics)
| # | old | new | fate |
|---|---|---|---|
| R2-1 | gap line prefix `xdist worker gwN finished WITHOUT its session-end report (…)` for EVERY gap | the lifecycle clause comes from `went_down`: `went down WITHOUT …` / `never went down and sent no …` | **changed deliberately** (F-3); pinned by `TestTheGapLineNeverContradictsItsCause` (13 doors) |
| R2-2 | gap cause `it never went down` | `no node-down arrived before the controller's session-finish` (the lifecycle clause now carries "never went down") | changed; same pin |
| R2-3 | missing-key cause `no '<key>' value arrived` (+ ` (the worker went down with an error)` when `error` was set) | `no '<key>' value arrived; the worker went down with an error` / `…; the worker reported no error, so a session-finish hook in it may have raised before the harness's` | **changed per R-2 ruling**. The error-set wording is preserved in substance. No pin on the text (none existed; spec-silent beyond the ruling) |
| R2-4 | `_unreaped_line` tail `the periodic test-namespace wipe removes them` | `the operator's periodic test-namespace wipe removes them` | **changed per R-6 ruling** (D2 = operator wipes; no scheduled wipe exists). No existing pin on the phrase (pre-flight scan above) |
| R2-5 | the gap line's tail repeated the same phrase as a second literal | both lines serve `_UNVERIFIED_DATABASES_REMEDY` | ONE implementation; a future rewording reaches both |
| R2-6 | the reap could hang the process forever on a non-cooperative block (round-1 KNOWN BOUND F-a) | `faulthandler` exits the process at 2 × budget, dumping stacks to the real stderr | **F-a CLOSED** by the operator's Q2 ruling; pinned by the 4 blocking cells + §9.3 |
| R2-7 | `_reap_within_budget` left the process-global faulthandler timer untouched | it arms that timer and always cancels it on the way out | it is cancelled in `finally`, on every path. The `pytest-faulthandler-timeout` cell variants pin coexistence with pytest's own per-test timer |
| R2-8 | gaps were plain `str` values in `_SESSION_END_REPORT_GAP_BY_WORKER` | `_SessionEndReportGap` values; `_workers_without_session_end_report()` returns them | internal type change; the contract drives the hooks only, so no pin reads the type |

### §9.6 Instrument (verbatim; run from the repo root with `uv run python <file>`)
```python
"""Print the served #538 gap line for each lifecycle door, driven through the conftest's own hooks."""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

TESTS = Path("/home/ejprice/PycharmProjects/lore/loremaster/tests")
sys.path.insert(0, str(TESTS))
spec = importlib.util.spec_from_file_location("lore_conftest_probe", TESTS / "conftest.py")
conftest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conftest)
GOOD = {conftest._LEAK_REPORT_WORKEROUTPUT_KEY: "[]", conftest._UNREAPED_REPORT_WORKEROUTPUT_KEY: "[]"}


def node(worker, workeroutput=None):
    fake = SimpleNamespace(gateway=SimpleNamespace(id=worker))
    if workeroutput is not None:
        fake.workeroutput = workeroutput
    return fake


conftest.pytest_testnodeready(node("gw0"))  # never went down
conftest.pytest_testnodeready(node("gw1"))
conftest.pytest_testnodedown(node("gw1", {}), None)  # went down, no error, no report (the F-2 case)
conftest.pytest_testnodeready(node("gw2"))
conftest.pytest_testnodedown(node("gw2"), "worker crashed")  # went down with an error
conftest.pytest_testnodeready(node("gw3"))
conftest.pytest_testnodedown(node("gw3", {**GOOD, conftest._LEAK_REPORT_WORKEROUTPUT_KEY: "{oops"}), None)
for worker, gap in sorted(conftest._workers_without_session_end_report().items()):
    print(gap.line(worker))
```
- **Flags this round:** none new. ⚠ In the round-1 §SUMMARY, F-a (the non-cancellable-block bound) is now CLOSED by P1 (R2-6).
