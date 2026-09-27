brief-base v17 read
- **State:** done-with-deviations (1 minor deviation, below). Stubs written against HEAD `f66a190`, not committed (per brief).
- **Deviation:** `MIGRATION_WIRE_STARTUP_TIMEOUT_S` is set to `DEFAULT_STARTUP_TIMEOUT_S` (15.0, imported from `loopback`) instead of a bare `15.0` literal. Same value, ≠ 60.0, so the house no-hardcoded-values rule holds. The name is not wired into `serve_asgi`.
- **Packages considered:** none — no mechanism specified (stubs only).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** the 7 production symbols are exactly the contract's §Stub expectations list. There is 1 extra private stub-only constant (`_pytest_sessions._STUB_WORKERS_PLACEHOLDER`), and the builder deletes it when the ruled values land.
- **Graded:** n/a — this is a stub report, not a verdict on someone else's artifact.
- **Gate (3 files, `-n 12` because another lore pytest was live, pid 4008221):** **30 failed, 62 passed in 20.58s.** All 30 failures are BEHAVIORAL. There were 0 ImportError / ModuleNotFoundError / NameError / AttributeError / SyntaxError / TypeError. ruff: `All checks passed!` on the 3 touched files.
- **Decisions needed:**
  - **D1:** no pin checks the literal `WORKERS_PLACEHOLDER == "{workers}"`, and I stubbed it as `"{workers_stub}"` (see §D1).
  - **D2:** `test_forwarded_pytest_args_keep_the_policy_count[alone]` goes GREEN on this unfixed stub build. Its paired `[another-lore-session-live]` row does discriminate (see §D2).
- **Receipts:** §Stubs · §Gate tail · §Classification · §Count reconciliation vs the contract's RED receipt.

## Stubs (writable set = the contract's §Stub expectations list, nothing else)
1. `loremaster/tests/test_migration_wire.py`
   - Adds the module constant `MIGRATION_WIRE_STARTUP_TIMEOUT_S: float = DEFAULT_STARTUP_TIMEOUT_S`, placed after `_SURREAL_TEST_NAMESPACE`.
   - The import line gains `DEFAULT_STARTUP_TIMEOUT_S`.
   - The constant is NOT passed to `serve_asgi`, per the brief. The builder wires it.
2. `scripts/_pytest_sessions.py` (new):
   - `PROC_ROOT = Path("/proc")`.
   - `FLEET_CAPPED_PYTEST_WORKERS: str` and `SOLO_PYTEST_WORKERS: str`, both set to the placeholder `"<not-yet-implemented>"`.
   - `other_pytest_sessions(*, proc_root: Path = PROC_ROOT, own_pids: set[int]) -> list[tuple[int, str]]`.
   - `pytest_worker_count(*, proc_root: Path = PROC_ROOT, own_pids: set[int]) -> str`.
   - Both function bodies raise `NotImplementedError("Not yet implemented")`. Their docstrings state the contract, including "consults `other_pytest_sessions` through the module global, exactly once".
   - The real detector was NOT moved. `concurrent_wire_acceptance.other_pytest_sessions` keeps its own definition, so the one-definition and re-export pins are red, as expected.
3. `scripts/pending_contract_gate.py`: `WORKERS_PLACEHOLDER = "{workers_stub}"`, a value ≠ `"{workers}"`, placed after `JUNIT_PLACEHOLDER`. No pin needs the exact value in order to import (see D1). It is NOT substituted in `GateRunner.run`.

Untouched: the three contract test files, and every other pre-existing working-tree modification (`test_comms_footer.py`, `test_fixwave_a28_63c_i_a.py`, `test_mcp_server.py`, `pending_contracts.yaml`, and the R4 edit in `test_loopback_serving.py`). Those were already dirty at spawn and are not mine.

## Gate tail (measured 2026-09-26 at HEAD `f66a190` + the stubs)
Command: `uv run pytest -q -p no:cacheprovider --tb=line -n 12 loremaster/tests/test_loopback_serving.py loremaster/tests/test_migration_wire_budget_503.py scripts/test_pytest_workers_503.py`
```
30 failed, 62 passed, 24 warnings in 20.58s
```
Scan of the full log for `ImportError|ModuleNotFoundError|NameError|AttributeError|SyntaxError|TypeError`: **0 hits.**

## Classification: every failure (30), each BEHAVIORAL
| # | Test | Raised | Class |
|---|---|---|---|
| 1–4 | `test_loopback_serving.py::TestAFailingBodyIsNeverReplacedByItsTeardown::test_the_body_exception_survives_and_the_teardown_failure_rides_as_a_note[{serve_asgi,serve_http}-body-raises-{Exception,BaseException}-raise]` | AssertionError: "teardown REPLACED the body's own …" | BEHAVIORAL (no stub needed; red on the unfixed code, as briefed) |
| 5 | `test_migration_wire_budget_503.py::…::test_the_heavy_budget_constant_has_the_ruled_value` | AssertionError `assert 15.0 == 60.0` | BEHAVIORAL |
| 6 | `…::test_every_serve_asgi_call_in_the_fixture_home_passes_the_budget_by_name` | AssertionError: "test_migration_wire.py:386 starts the heavy composition with NO startup_timeout_s" | BEHAVIORAL |
| 7 | `…::test_the_fixture_actually_hands_the_heavy_budget_to_the_server_start` | AssertionError: "handed serve_asgi startup_timeout_s=15.0" | BEHAVIORAL |
| 8 | `…::test_a_heavy_start_slower_than_the_default_budget_is_served` | `pytest.fail` after `ServerStartupTimeout` (15.0s budget) | BEHAVIORAL (the #503 failure itself) |
| 9 | `test_pytest_workers_503.py::TestTheWorkerPolicy::test_the_policy_constants_carry_the_ruled_values` | AssertionError `'<not-yet-implemented>' == '12'` | BEHAVIORAL |
| 10–15 | `…::test_the_policy_over_the_real_detector[empty-proc, one-scratch-session, one-repo-session, three-sessions-still-12, only-own-pid, worker-and-non-test-process]` | NotImplementedError (`pytest_worker_count`) | BEHAVIORAL |
| 16–17 | `…::test_the_policy_asks_the_shared_detector_at_call_time[another-lore-session-live, alone]` | NotImplementedError | BEHAVIORAL |
| 18 | `TestThereIsOneDetector::test_exactly_one_definition_across_the_non_test_scripts` | AssertionError: defined at `_pytest_sessions.py:29` and `concurrent_wire_acceptance.py:227` | BEHAVIORAL |
| 19 | `TestThereIsOneDetector::test_the_acceptance_driver_re_exports_the_shared_detector` | AssertionError: "not the shared object" | BEHAVIORAL |
| 20 | `TestTheGateRendersTheResolvedCount::test_every_pytest_gate_runs_with_the_policy_count[another-lore-session-live]` | AssertionError: would spawn `-n auto` | BEHAVIORAL |
| 21 | `…::test_every_pytest_gate_runs_with_the_policy_count[alone]` | AssertionError `assert 0 == 1` (the detector was never consulted) | BEHAVIORAL |
| 22 | `…::test_forwarded_pytest_args_keep_the_policy_count[another-lore-session-live]` | AssertionError `'auto' == '12'` | BEHAVIORAL |
| 23 | `…::test_the_count_is_resolved_when_the_gate_runs_not_when_it_loads` | AssertionError `['auto', 'auto']` | BEHAVIORAL |
| 24 | `TestTheManifestExpressesThePolicy::test_every_shipped_pytest_gate_takes_its_count_from_the_placeholder` | AssertionError: "hardcodes -n 'auto'" | BEHAVIORAL |
| 25 | `…::test_no_shipped_gate_description_teaches_the_retired_count` | AssertionError: description still says `-n auto` | BEHAVIORAL |
| 26–30 | `…::test_the_loader_refuses_a_hardcoded_worker_count[the-retired-literal, a-literal-count, joined-short-form, long-form, long-form-joined]` | `Failed: DID NOT RAISE ManifestError` | BEHAVIORAL |

STRUCTURAL: **0.**

## Count reconciliation vs the contract's RED receipt (REPORT-contract-503 §RED receipt, HEAD `884ca63`)
- **R4:** 4F/11P, which matches the contract.
- **Budget:** 4F/1P, which matches. The contract's 1-needs-stub (the constant) is now behavioral.
- **Workers:** **22F/4P**, where the contract measured 24F/2P. Passing tests, from the `-rp` listing:
  - `test_the_shipped_manifest_has_a_gate_the_policy_governs`: green at HEAD, non-vacuity.
  - `test_control_the_loader_accepts_the_placeholder_and_a_serial_gate[no-worker-flag-runs-serial]`: green at HEAD, control.
  - `test_control_…[the-placeholder]`: was AttributeError at HEAD and is now legitimately green. It is a control: the loader accepts the placeholder.
  - `test_forwarded_pytest_args_keep_the_policy_count[alone]`: was ModuleNotFoundError at HEAD and is now **green on a build that fixes nothing** (§D2).

## D1: the placeholder's ruled literal is unpinned
The contract's §Stub item 3 specifies `WORKERS_PLACEHOLDER = "{workers}"`, but every test READS the constant from production. None of them compares it to `"{workers}"`. So a builder who leaves my `"{workers_stub}"` in place and spells the manifest `-n {workers_stub}` passes the whole contract.
- Consequence: a cosmetic divergence from the ruling, not a behavioral defect.
- **Recommendation:** the builder brief states the ruled value explicitly, or the contract adds a one-line value pin (as it already does for `FLEET_CAPPED`/`SOLO`).
- The alternative stub choice (the exact `"{workers}"`) would have turned no additional test red or green. I chose ≠ per the brief's primary option.

## D2: one row of a parametrized pair is non-discriminating on its own
`test_forwarded_pytest_args_keep_the_policy_count[alone]` passes on the unfixed code, for these reasons:
- The shipped manifest still hardcodes `-n auto`, which happens to equal the "alone" expectation.
- This test does not assert that the detector was consulted. Its sibling `test_every_pytest_gate_runs_with_the_policy_count` does assert that.

The pair still discriminates: a build that ignores the policy on the forwarded path fails `[another-lore-session-live]`. So this is not a hole. It is flagged because the contract's RED receipt counted this row as "needs stub → red" and it is in fact green-by-coincidence. **Optional tightening:** assert `len(detector_calls) == 1` per spec in this test too, as the direct-render test does.

## Environment note
At gate time the box had non-lore pytest sessions live (mobile-pricepaper-smoke scratch worktrees, pids 3935899 / 3953478 / 4009011) as well as the lore scratch session (pid 4008221). This is relevant to contract fork F2: HEAD's detector would count all of them. I note it only as a fact. The contract has already escalated F2.
