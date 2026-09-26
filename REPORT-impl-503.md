brief-base v17 read · brief project v7 read (lore_comms register, session `297217bd`, agent `impl-503`)

# REPORT-impl-503 — tdd-light GREEN: #503 heavy wire budget · R4 teardown never masks the body · currency gate workers

## SUMMARY BLOCK
- **State:** done. Measured 2026-09-26 on a working tree based at HEAD `f66a190`, with nothing committed (per brief).
- **Deviations:** none that change behaviour. Three notes: (1) the gates.yaml pytest description points at the policy instead of restating "12"/"auto", so the prose cannot drift from `_pytest_sessions`. (2) The loader also ACCEPTS the placeholder in joined and long forms (`-n{workers}`, `--numprocesses={workers}`) and refuses every other value. (3) `pending_contract_gate.py` and `test_migration_wire.py` fail `ruff format --check` at HEAD `f66a190` too, so I left the old hunks alone; none of the formatter's hunks touch my lines (§Gates).
- **Packages considered:** process detection → psutil `keep_with_trigger` (the contract's verdict, which I did not re-derive; psutil is not a scripts dependency). I **moved** the stdlib `/proc` reader rather than replacing it. Trigger: the day the detector needs more than argv. Teardown note → stdlib PEP 678 `BaseException.add_note`. Placeholder substitution → extends the existing `{junit_xml}` idiom in `GateSpec.resolved_command`.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 6 new symbols, all dispositioned (§DRY ledger). The detector was MOVED (one definition), not copied.
- **Graded:** n/a — this is a build report, not a verdict on someone else's artifact.
- **Decisions needed:** none new. Contract forks F1/F2/F3 stand as the contract escalated them; I built A / A / F3-as-pinned. §Flags has one new item: forwarded `pytest_args` can carry a second `-n` that the loader never sees.
- **Receipts:** §Gates (226/0, skills 120/0, ruff, typecheck 0-in-touched) · §Mutation proof (sharing) · §Smoke.

## Capability check (brief-base §4)
- **Demanded:** lore tools as first choice. **Have:** them loaded. **Did:** I read the seams with awk/sed (grep is hook-blocked, #473) because I already knew the files and symbols from the contract and Phase 0 docs. The consumer sweep for `resolved_command` / `_run_selected_gates` / `pending_contract_gate` imports also ran through awk over `scripts/`, `skills/lore-deploy/scripts/` and `loremaster/tests/`. That was a textual seam (imports plus the YAML argv), which is case (b)/(c) of the dogfood protocol. No lore weakness was involved, so I filed no friction.
- Everything else the brief demanded was satisfiable. No full suite was run, :18500 was never touched, and the TEI embedder was never called.

## Files changed
| file | change |
|---|---|
| `scripts/_pytest_sessions.py` | Stub replaced. `PROC_ROOT` + `other_pytest_sessions` MOVED here verbatim from the driver; the only change is that the `"pytest"` literal became `PYTEST_ARGV_MARKER`. Added `FLEET_CAPPED_PYTEST_WORKERS = "12"`, `SOLO_PYTEST_WORKERS = "auto"`, and `pytest_worker_count`, which calls the module-global detector once. `_STUB_WORKERS_PLACEHOLDER` deleted. The module docstring names the #506 bound. |
| `scripts/concurrent_wire_acceptance.py` | Its `other_pytest_sessions` def and `PROC_ROOT` are deleted. It now has `from _pytest_sessions import other_pytest_sessions as other_pytest_sessions  # noqa: E402, PLC0414`, the PEP 484 explicit re-export, which mypy strict needs because it has no implicit re-export. `main` still calls the driver-module name. |
| `scripts/pending_contract_gate.py` | Adds `import os` and `import _pytest_sessions`. `WORKERS_PLACEHOLDER = "{workers}"`, plus `XDIST_WORKERS_SHORT_FLAG` / `XDIST_WORKERS_LONG_FLAG`. `GateSpec.wants_worker_count`. `GateSpec.resolved_command(junit_xml, workers=None)` with a `_substitute` helper. New module function `_hardcoded_worker_counts(command)`. `GateManifest._must_be_neither_empty_nor_ambiguous` refuses a junit gate with a hardcoded count. `GateRunner.run` resolves `pytest_worker_count(own_pids={getpid, getppid})` per run, and only when the command carries the placeholder. `_run_selected_gates` needed no change: it copies the spec and then calls `runner.run`, so both render paths substitute there. |
| `scripts/gates.yaml` | The pytest gate uses `"-n", "{workers}"`. Its description now describes the fleet policy by pointer and no longer says `-n auto`. The FIELDS header documents `{workers}` and the loader refusal. |
| `loremaster/loremaster/testing/loopback.py` | R4: in `_loud_teardown`'s failing-body branch, `stop` is wrapped in `try/except Exception`. A raise becomes a note `server at host:port teardown raised <Type>: <text>`, the `else` keeps the overrun note, and a bare `raise` re-raises the body's exception. An interrupt (BaseException that is not an Exception) escapes the inner `except` unchanged, with the body on its `__context__`. The clean-body path is unchanged. Prose updated: `_loud_teardown` docstring (plus a Raises `Exception:` line), the `serve_asgi` / `serve_http` Raises paragraphs, and `ServerShutdownTimeout`'s docstring. |
| `loremaster/tests/test_migration_wire.py` | Wiring only: `MIGRATION_WIRE_STARTUP_TIMEOUT_S: float = 60.0`, with a comment carrying the derivation (6 × max 10.04 s, n=551, commit 388c604) and the re-open trigger. `_serve_migration_wire` calls `serve_asgi(app, startup_timeout_s=MIGRATION_WIRE_STARTUP_TIMEOUT_S)`. The stub's now-unused `DEFAULT_STARTUP_TIMEOUT_S` import was removed. `loopback.DEFAULT_STARTUP_TIMEOUT_S` is still 15.0 (untouched). |

I did not touch any contract test file, and I did not touch the other agents' working-tree files (`test_comms_footer.py`, `test_fixwave_a28_63c_i_a.py`, `test_mcp_server.py`, `test_loopback_serving.py`'s contract edit, `pending_contracts.yaml`, the 64b files).

## Gates (measured 2026-09-26, tree based at `f66a190`)
Contract gate, exactly as briefed (`-n 12`):
```
uv run pytest -q -p no:cacheprovider --tb=short -n 12 loremaster/tests/test_loopback_serving.py loremaster/tests/test_migration_wire_budget_503.py loremaster/tests/test_migration_wire.py scripts/test_pytest_workers_503.py scripts/test_concurrent_wire_acceptance.py scripts/test_gate_currency.py scripts/test_pending_contract_gate.py scripts/test_wave_gate.py
226 passed, 22 warnings in 29.06s          (exit 0; the lead's RED baseline was 30 failed / 196 passed)
```
Skill tests (`cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests`):
```
120 passed in 17.22s                        (exit 0)
```
ruff over the 5 touched Python files: `All checks passed!`
`ruff format --check`: `loopback.py`, `_pytest_sessions.py` and `concurrent_wire_acceptance.py` are formatted. `pending_contract_gate.py` and `test_migration_wire.py` would be reformatted, **and so would both at HEAD `f66a190`**. I checked this with `git show HEAD:<f> | ruff format --check --stdin-filename <f> -`, which exits 1 for both. HEAD vs now has 29 → 28 hunks and 10 → 10 hunks respectively, and **none of the formatter's hunks touch a line I wrote** (an awk scan of `--diff` for my symbols came back empty). I did not reformat the pre-existing hunks because that would be unrelated diff noise. **Flag for the lead:** the red is pre-existing, not mine.
`./scripts/typecheck.sh`: exit 1, **60 errors (loremaster leg 59 in 23 files, scripts leg 1), 0 in any touched or contract file**. The skills, docs/eval and shellcheck legs are OK. The errors are all in other packets' files (58 / 63c / 64b families, plus `test_comms_footer.py`, `test_mcp_server.py`, `scripts/test_forgery_door_sweep.py`, `test_retry_seam.py`, `test_blocks_edge.py`, `test_task_read_surface.py`); the per-file tally is in my scratch log.

## Mutation proof — the detector is SHARED, not routed (brief-base §6)
I mutated the REAL tree after taking a `cp -a` content backup: `_pytest_sessions.PYTEST_ARGV_MARKER = "pytest"` → `"mutated-marker"`. I expected BOTH callers' detection pins to go red: the driver's preflight tests that expect a session to be found, and the policy rows that expect "12". Observed:
```
FAILED scripts/test_concurrent_wire_acceptance.py::TestTheOtherSessionPreflight::test_a_process_that_vanishes_mid_scan_is_skipped
FAILED scripts/test_concurrent_wire_acceptance.py::TestTheOtherSessionPreflight::test_a_live_pytest_session_is_reported
FAILED scripts/test_pytest_workers_503.py::TestTheWorkerPolicy::test_the_policy_over_the_real_detector[one-scratch-session]
FAILED scripts/test_pytest_workers_503.py::TestTheWorkerPolicy::test_the_policy_over_the_real_detector[one-repo-session]
FAILED scripts/test_pytest_workers_503.py::TestTheWorkerPolicy::test_the_policy_over_the_real_detector[three-sessions-still-12]
5 failed, 50 passed in 7.13s
```
Restored from the backup; `cmp` confirms the file is byte-exact. Honesty note: my expected set was stated as a CLASS ("the driver's detection pins + the '12' policy rows") and not as node ids from `--collect-only`. I did not name `test_a_process_that_vanishes_mid_scan_is_skipped` in advance; it asserts a surviving session is still reported, so it is in the class. Both populations reddened, and the pins that should stay green did: the "auto" rows, the gate tests (which stub the detector) and the non-detection preflight rows. The contract's own stub-the-detector pins cover the other direction, where the policy and gate must follow a replaced detector.

## Smoke (script entry points, no gates run)
- `uv run python scripts/pending_contract_gate.py --verify-registry` → exit 0. This proves `import _pytest_sessions` resolves when the file runs as a script, and that the shipped manifest loads under the new refusal.
- `uv run python scripts/wave_gate.py --help` → exit 0 (it imports `pending_contract_gate`).
- Live policy on this box (another pytest session was live): `pytest_worker_count(...)` → `12`, and the rendered gate argv is `[... '-n', '12', ...]`.

## DRY ledger
| new symbol | lore query run / search | what it returned | disposition |
|---|---|---|---|
| `_pytest_sessions.other_pytest_sessions` / `PROC_ROOT` | contract §Stub + awk over `scripts/*.py` for `other_pytest_sessions` | one definition, in `concurrent_wire_acceptance.py` | **REUSED (moved)**. There is one definition, which the AST pin and my mutation both prove |
| `_pytest_sessions.PYTEST_ARGV_MARKER` | awk over `scripts/` for an existing marker constant | the literal `"pytest"` inline in the moved body | **EXTENDED**: the moved literal is now named, and nothing else changed |
| `FLEET_CAPPED_PYTEST_WORKERS` / `SOLO_PYTEST_WORKERS` / `pytest_worker_count` | awk over `scripts/` and `skills/` for a worker-count policy | none (only hardcoded `-n` values in drivers) | **HAND-ROLLED**. This is the ruled new policy; it calls the shared detector |
| `WORKERS_PLACEHOLDER`, `XDIST_WORKERS_SHORT_FLAG`, `XDIST_WORKERS_LONG_FLAG` | read `pending_contract_gate` (`JUNIT_PLACEHOLDER` idiom) | `JUNIT_PLACEHOLDER` + `resolved_command` | **EXTENDED** `GateSpec.resolved_command` (a second placeholder, the same substitution seam) |
| `GateSpec.wants_worker_count`, `GateSpec._substitute` | same | `resolved_command`'s inline comprehension | **EXTENDED**: the comprehension is now a substitution map, so both placeholders go through one routine |
| `_hardcoded_worker_counts` | awk over `scripts/` for an argv flag parser | none (the loader had only a `{junit_xml}` presence check) | **HAND-ROLLED**, 15 lines. `argparse` does not fit: it would need xdist's full option table to parse a foreign argv |

## Flags (surfaced, not acted on)
1. **Forwarded `pytest_args` bypass the loader refusal.** `_run_selected_gates` appends caller-supplied args (the `--wave` selector, or `--pytest-args`) after the manifest command. A caller who forwards `-n 4` produces an argv with two `-n` values (xdist's argparse takes the last), and nothing refuses it because the check runs at manifest load. No test covers this, and the brief did not ask for it, so I left it alone. The lead should decide whether to rule it (refuse `-n` in forwarded args, or leave it as a deliberate operator override).
2. **CLAUDE.md commentary** (the lead edits it, not me). The "Run pytest with `-n auto`" bullet is still true for a lone session. The contract's recommended one-liner (REPORT-contract-503 §Anything-noticed 4) still applies: *the currency gate resolves `-n {workers}` via `scripts/_pytest_sessions.py::pytest_worker_count` — `FLEET_CAPPED_PYTEST_WORKERS` when another pytest session is live, else `SOLO_PYTEST_WORKERS` (operator 2026-09-26, #503)*. Naming the constants, not the numbers, keeps the prose derived.
3. **#506 (detector matches any argv mentioning pytest):** the behaviour is unchanged, as the brief ordered, and the bound is now named in `_pytest_sessions`' module docstring. For the worker policy a false positive only caps at 12, which is the safe direction.
4. **Gate currency:** once this lands, the contract's RED pins are green, so no `pending_contracts.yaml` entries are needed for them. That file is someone else's and I did not touch it.
5. **Pre-existing `ruff format` red** on `pending_contract_gate.py` and `test_migration_wire.py` at HEAD `f66a190` (§Gates). If the manifest's `ruff` gate ever grows a format leg, these two files will fail it.
