brief-base v17 read

# REPORT-impl-503-d1: tdd-light Phase 4 (GREEN) delta for lore #503 (the currency gate's worker count)

## SUMMARY BLOCK
- **State:** done-with-deviations. Nothing committed. Measured 2026-09-26 at HEAD `f66a190` plus the working tree.
- **Deviations:**
  - (1) I did not register on `lore_comms` (brief-base §5). The spawn brief named no ledger row, and `scripts/` is outside lore's graph (#507). Declared in §Capability check.
  - (2) The declared mutation prediction was a strict SUBSET of the observed reds. The extra reds are explained in §Mutation proof.
  - (3) One edit outside the brief's literal item-5 list, still inside the writable set: the `--wave` argparse help in `wave_gate.py` now states the refusal.
- **Packages considered:** worker-flag parsing → pytest's own `Parser` with `xdist.plugin` registered. Verdict `keep_with_trigger`, per lead ruling 3.
  - Read: the installed `_pytest.config.argparsing.Parser.__init__` signature (`*, _ispytest: bool = False`). `pytest.Parser` is exported as a type only.
  - Probed live on pytest 9.0.3 / xdist 3.8.0 via `config._parser`: `-qn3`→3, `-n 2 -n 3`→3, `--numproc 5`→None, `-n auto`→auto.
  - Triggers are recorded in the `_hardcoded_worker_counts` docstring.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 5 new symbols, all dispositioned (§DRY ledger).
- **Decisions needed:** none. D1-F1 = Reading B, D1-F2 = refuse before any spawn, and D1-F3 = a typed error were all ruled by the lead and implemented as ruled.
- **GATE:** 8-file gate **276 passed / 0 failed** · skills **120 passed** · `ruff check` clean on the 3 touched .py files · typecheck **54 errors total, 0 in the touched files** · `--verify-registry` exit 0 · `wave_gate.py --help` exit 0.
- **Receipts:** §Files changed · §Gate tails · §Live CLI receipts · §Mutation proof · §Noticed.

## Capability check (brief-base §4)
- **Demanded vs had:**
  - lore-first for structure questions: not used. `scripts/` is not in lore's graph (#507, already filed), so I searched with **awk** (grep/rg are hook-blocked, #473). This fallback is said out loud here.
  - `lore_comms` register: skipped. No ledger row was named, and the deliverable is this file.
- Everything else was satisfiable. I ran no full suite and never touched :18500. I killed nothing: no process was started that needed killing.

## Files changed
**`scripts/pending_contract_gate.py`**
- `ForwardedWorkerCountError(ValueError)`, new, after `ManifestError`: the typed refusal (D1-F3). Both CLIs print `REFUSED ARGUMENT:` and exit 2. It is not `ManifestError`, so no "MANIFEST ERROR" is printed for a CLI argument.
- `_WorkerFlag` (NamedTuple) + `_worker_flags(command)`, new: **the ONE recogniser of worker-flag spellings**. Each flag comes back as a (start, stop, value) span. The recognition logic is byte-for-byte the former body of `_hardcoded_worker_counts`, so F8 (`-qn3`) is still missed, as ruled.
- `_hardcoded_worker_counts`: body reduced to one line over `_worker_flags` (behaviour identical). The docstring now carries:
  - the F8 KNOWN BOUND;
  - the `keep_with_trigger` verdict and both triggers (ruling 3);
  - the CORRECTED rationale: pytest+xdist IS the full option table, but it is private. The claim "argparse would need xdist's full option table" is marked wrong.
- `_with_policy_workers_last(command)`, new: drops every worker flag whose value is `{workers}` and appends `-n {workers}` LAST. A command without that flag is returned unchanged.
- `GateSpec.resolved_command`: when `workers` is given, it first applies `_with_policy_workers_last`, then substitutes as before. `GateRunner.run` is still its only caller, and it is unchanged apart from its docstring. The resolver keeps `own_pids={getpid(), getppid()}` (ruling 4 is unchanged).
- `_run_selected_gates`: calls the new `_refuse_forwarded_worker_counts(pytest_args)` at ENTRY, before the leg loop, so no gate spawns (D1-F2). The docstring states the append-then-policy-last order and the refusal.
- `_refuse_forwarded_worker_counts(pytest_args)`, new: calls `_hardcoded_worker_counts` through the module global at call time (the mutation-by-stub pin depends on that). The message names `_pytest_sessions.pytest_worker_count`, and the name is derived from the function object's `__module__`/`__name__`, not a string literal.
- `main`: catches `ForwardedWorkerCountError` and exits 2. The docstring notes that a refused argument is exit 2 with no gate spawned.
- The `pytest_args` argparse help now states the policy and the refusal.
- `from typing import NamedTuple` import.

**`scripts/wave_gate.py`**
- Imports `ForwardedWorkerCountError`. The try around `_run_selected_gates` catches it: `REFUSED ARGUMENT:`, exit 2.
- The forwarding comment now states that the policy flag is rendered after the selector, and that a worker-count selector is refused.
- The `--wave` help gains one sentence on the refusal (deviation 3).

**`scripts/gates.yaml`**
- The FIELDS `command` entry says `{workers}`'s `-n` is rendered LAST, after the manifest's tokens and any forwarded args, and that forwarded counts are REFUSED.
- The `pytest` description says the same in one sentence.

**`scripts/_pytest_sessions.py`**: unchanged. Nothing in the delta needed it.

No test file was modified.

## Gate tails (2026-09-26, HEAD `f66a190` + working tree)
```
$ uv run pytest -q -p no:cacheprovider --tb=short -n 12 loremaster/tests/test_loopback_serving.py loremaster/tests/test_migration_wire_budget_503.py loremaster/tests/test_migration_wire.py scripts/test_pytest_workers_503.py scripts/test_concurrent_wire_acceptance.py scripts/test_gate_currency.py scripts/test_pending_contract_gate.py scripts/test_wave_gate.py
276 passed, 22 warnings in 30.55s
$ cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests
120 passed in 18.07s
$ uv run ruff check scripts/pending_contract_gate.py scripts/wave_gate.py scripts/_pytest_sessions.py
All checks passed!
$ ./scripts/typecheck.sh            (exit 1)
Found 53 errors in 23 files (checked 297 source files)   typecheck: loremaster FAILED
Found 1 error in 1 file (checked 63 source files)        typecheck: scripts FAILED
  → 54 total; 0 in pending_contract_gate.py / wave_gate.py / _pytest_sessions.py
$ uv run python scripts/pending_contract_gate.py --verify-registry   → exit 0
$ uv run python scripts/wave_gate.py --help                          → exit 0
```
- **Typecheck errors.** The 54 errors are all in other packets' test files. By count: `loremaster/tests/`: `test_supersede_reanchor_58` 7, `test_governed_substrate_64b` 6, `test_mcp_server` 6, `test_reanchor_58_r2_rulings` 5, `test_findings_identity_64b` 4, and 18 more files with 1–3 each. `scripts/`: `test_forgery_door_sweep.py` 1, `loremaster.tasks` has no `SupersedeResult`.
- **`ruff format --check`** flags `pending_contract_gate.py` and `wave_gate.py`. This drift was already there before my edits: the format-diff line counts are the same before and after (129 and 14), and HEAD's `pending_contract_gate.py` alone has 132. `ruff format` is not a manifested gate.

## Live CLI receipts (no gate spawned; the refusal precedes every leg)
```
$ uv run python scripts/pending_contract_gate.py -- -n auto loremaster/tests/test_migration_wire.py
REFUSED ARGUMENT: the forwarded pytest args ['-n', 'auto', 'loremaster/tests/test_migration_wire.py'] carry an xdist worker count ['auto'] — the gate's worker count is decided by the fleet policy (_pytest_sessions.pytest_worker_count), rendered as the LAST worker flag. Drop the -n / --numprocesses argument (lore #503).
exit=2
$ uv run python scripts/wave_gate.py --wave=-n12
REFUSED ARGUMENT: the forwarded pytest args ['-n12'] carry an xdist worker count ['12'] — … (lore #503).
exit=2
# rendered argv, pytest gate + forwarded ['-qn3','x.py'], workers='12':
['uv','run','pytest','-q','-o','junit_family=xunit1','--junit-xml={junit_xml}','-qn3','x.py','-n','12']
```

## Mutation proof (ONE IMPLEMENTATION: render and refusal share `_worker_flags`)
- **Method:** content backup (`cp -a` to my session scratchpad), then a mutation of `_worker_flags`: `if part in (XDIST_WORKERS_SHORT_FLAG, XDIST_WORKERS_LONG_FLAG):` → `if part in (XDIST_WORKERS_LONG_FLAG,):`. The mutation LANDED: the `# MUTATION` marker was printed at its line.
- **Declared before the run:** (a) the refusal rows for `short-separate-*` / `flag-without-value`, and (b) the forwarding ruling-1 matrix rows, go red.
- **Observed: 44 red in `scripts/test_pytest_workers_503.py`.** (a) and (b) are all red, so the prediction held.
- **The extra reds are a wider blast, not noise.** Once `-n` is no longer matched as a separate flag, the bare `-n` token falls into the joined-short branch with value `""`. That makes the MANIFEST LOADER (the helper's third caller) refuse the shipped `-n {workers}`, which in turn reddens the long-spelling refusal rows, the pass-through controls and the pre-existing sections 1–4.
  - This is a stronger sharing result than predicted: loader, refusal and render all moved together.
  - It also shows my declared set was not independent of the loader, so I read it as a subset prediction, not an exact one.
- **Restored** from the content backup (`cmp` byte-exact), then re-run: `76 passed in 2.00s`.
- ⚠ **This is a builder's self-check, not a grade.** The independent re-grade (adversary or cold audit) is still owed.

## DRY ledger (new symbols)
lore could not be queried for `scripts/` (#507). Every search below is awk over `scripts/*.py`, `skills/lore-deploy/scripts/*.py` and `lorerunes/lorerunes/*.py`, for `numprocesses | class .*Error( | def _.*worker | def _refuse`.

| new symbol | search | returned | disposition |
|---|---|---|---|
| `_worker_flags` / `_WorkerFlag` | awk (above) | only `_hardcoded_worker_counts` | **EXTENDED `_hardcoded_worker_counts`**: its recognition loop was lifted into `_worker_flags` so the render uses the same spelling set. The helper keeps its name, signature and behaviour (ruling 2's "no second parser") |
| `_with_policy_workers_last` | awk (above) | none | HAND-ROLLED over `_worker_flags` (6 lines). No existing argv re-orderer |
| `_refuse_forwarded_worker_counts` | awk (above) | `restore_prod_dump._refuse_foreign_endpoint` (httpx request guard, unrelated domain) | HAND-ROLLED. It is a caller of `_hardcoded_worker_counts`, not a second parser |
| `ForwardedWorkerCountError` | awk (above) | `ManifestError`, `RegistryError`, `BrokenInstrumentError`, `lorerunes.posture.PostureError` | HAND-ROLLED per lead ruling 2 (D1-F3): `ManifestError` would print "MANIFEST ERROR" for a CLI argument. `PostureError` is a different domain |

## Noticed (surfaced, not dropped)
1. **`--derive` and `--verify-registry` ignore `pytest_args`** without refusing them. `--derive -- -n 3` is silently accepted, because those modes never reach `_run_selected_gates`. No worker count is ever applied there, so this is harmless, but a forwarded arg is dropped without a word. It is not pinned, and I did not change it (no test). Your call whether it matters.
2. **CLAUDE.md commentary** (outside my writable set): I would add one line to the "Run pytest with `-n auto`" bullet, as recommended in REPORT-contract-503-d1.md §Builder notes: *"…for a lone manual run; never forward `-n` to `pending_contract_gate` / `wave_gate` — it is refused (lore #503)."*
3. The siblings contract-503-d1 §Noticed 3 lists as not tried (`--maxprocesses`, `-p no:xdist`, `-o addopts=`, `PYTEST_ADDOPTS`) are still open. Ruling 2 limits the refusal to the helper's spellings.
4. The 54 typecheck errors listed under §Gate tails are unrelated to this scope.

There are 54 failing typecheck errors unrelated to our present scope. Do you want to examine them more closely?
