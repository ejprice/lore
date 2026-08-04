# REPORT-builder-cycle-fix-04b3-1

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK
- state: **done** — `CURRENCY: PASS`, zero RED_ORPHANED (gate tail in §Verification)
- mission: make `scripts/pending_contract_gate.py --currency` render **CURRENCY: PASS** (zero RED_ORPHANED) by resolving packet 04b-3's 3 own pytest orphans (GROUP A) + 04b-2's 12 inherited ruff/typecheck orphans (GROUP B). `tasks.py` and the CYCLE contract tests were NOT touched (FROZEN/GO).
- deviations:
  - GROUP A routed the FULL connection scaffolding (topology + `connect_admin` + `unique_database` + teardown) through `_surreal_harness`, not just the topology block — the brief's "get the connection from the harness" + DRY law + the `forgery_door_sweep.py` reference all point at using the harness's own helpers, so the scripts no longer carry a private copy of `connect_admin`/`unique_database`/teardown.
  - `scripts/coldaudit_cycle_04b3_fork_a_refute.py` is **UNTRACKED** (`??`) — it needs `git add` by the lead; the disk-based AST pins already govern it (they read files, not the index), so it was RED and is now GREEN.
- Packages considered: none — no new mechanism specified. GROUP A reuses the EXISTING in-house shared seam (`loremaster/tests/_surreal_harness.py`); no library was hand-rolled or replaced. GROUP B is behaviour-preserving lint.
- Graded: build against `fff6e8f` · HEAD-at-report: `fff6e8f` · SAME. (No verdict on another agent's artifact is rendered here; the one measurement asserted — the harness importer count = 48 — is DERIVED live by the pin, receipt below.)
- decisions-needed: none.
- receipt pointers: RED baseline §Baseline; GROUP A fix §A; GROUP B fix §B; per-probe exit-0 runs §A.run; gate §Verification.

## Baseline (RED at fff6e8f, before this wave)
All three GROUP A pins RED; both secret pins name all three scripts (the disk-scan sees the untracked one):
```
FAILED tests/test_secret_typing.py::...::test_secretstr_is_minted_only_where_a_credential_ORIGINATES
  assert not ['scripts/coldaudit_cycle_04b3_fork_a_refute.py:55',
              'scripts/cycle_coexisting_legacy_soundness_probe.py:50',
              'scripts/esc1_write_path_cycle_closure.py:57']
FAILED tests/test_secret_resolution_seam.py::...::test_every_environment_read_is_the_entry_point_or_allowlisted
  assert not ['scripts/coldaudit_cycle_04b3_fork_a_refute.py::<module>',
              'scripts/cycle_coexisting_legacy_soundness_probe.py::<module>',
              'scripts/esc1_write_path_cycle_closure.py::<module>']
FAILED tests/test_surreal_harness.py::...::test_the_harnesss_docstring_counts_are_the_DERIVED_counts
  AssertionError: the harness docstring says 47 test files import it; 48 actually do.
3 failed in 3.10s
```

## Root cause (GROUP A)
Two packet-42 structural pins govern the whole workspace (`scripts/` included, test files excluded):
- `test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_secretstr_is_minted_only_where_a_credential_ORIGINATES` — every `SecretStr(...)` construction must sit in `loremaster/config.py` or `scripts/survey_txn_contention_102.py` (allowlist). The three probes minted `SecretStr(os.environ.get(...))` at module level.
- `test_secret_resolution_seam.py::TestSecretResolutionHasExactlyOneEntryPoint::test_every_environment_read_is_the_entry_point_or_allowlisted` — every `os.environ`/`os.getenv` read must be in `loremaster/config.py` or `ENV_READ_ALLOWLIST`. The three probes read `os.environ` at module level.

The pins scan `production_sources()` / `_python_sources()`, which EXCLUDE `loremaster/tests/` (`"tests" not in path.parts`). So the fix is not an allowlist entry (a new allowlist entry is a DESIGN decision the invariant itself defers) — it is to move the env read and the `SecretStr` mint into `_surreal_harness` (a test module the scans do not see) by routing each script's connection through that shared seam, exactly as `scripts/forgery_door_sweep.py::_harness` and `scripts/survey_txn_contention_102.py` already do.

## §A — GROUP A fix (3 probe scripts → `_surreal_harness` seam)
For each of `scripts/{coldaudit_cycle_04b3_fork_a_refute,esc1_write_path_cycle_closure,cycle_coexisting_legacy_soundness_probe}.py`:
- Deleted the hand-rolled `URL/USER/PASSWORD = …os.environ… SecretStr(…)` + `NAMESPACE` block, the local `unique_database()` (used `os.getpid`), the local `connect_admin()` (and esc1's local `teardown()`).
- Added `_repository_root()` + `_harness()` (the `forgery_door_sweep.py::_harness` pattern: put `loremaster/tests` on `sys.path`, `import _surreal_harness`).
- Module-level topology is now `_SURREAL_URL = _HARNESS.surreal_url()` and the **production-refusing assertions are kept verbatim** on it (`"18500" not in`, `"127.0.0.1:18000" in`).
- Connections come from the harness: `_fresh_env()` → `_HARNESS.make_env(database=_HARNESS.unique_database(), dim=_HARNESS.PRODUCTION_DIM)`; `await _HARNESS.connect_admin(env)`; teardown `await _HARNESS.drop_database(env)`. `TaskLedger(...)` is built from `env.{url,namespace,database,user,password}` (`env.password` is the harness's `SecretStr`).
- Removed now-unused imports (`os`, `pydantic.SecretStr`, `AsyncSurreal`, `signin_credentials`, `bootstrap_session`; kept `execute_transaction` in esc1); added `pathlib.Path`.

Harness importer count: the DERIVED count is **48** (04b-3 added `test_cycle_write_path_04b3.py`, which imports the harness but does NOT call `connect_admin`, so the `connect_admin`-caller count stays 30). Updated the `_surreal_harness.py` docstring literal `47 → 48`; ran the pin to confirm (it re-derives both counts live).

### §A.run — all three probes STILL RUN, exit 0 (spike `:18000`, real tree)
```
coldaudit_cycle_04b3_fork_a_refute.py: loremaster.__file__ = .../loremaster/loremaster/__init__.py
  [PASS] A: edges present -> REFUSE + far reached
  [PASS] B raw: refusal tracks reach exactly
  [PASS] B+backfill: edge restored -> REFUSE + far reached      EXIT=0

cycle_coexisting_legacy_soundness_probe.py:
  VERDICT: guard REFUSED the cyclic create — SOUND (HEAD / variant D).   EXIT=0

esc1_write_path_cycle_closure.py:
  VERDICT INPUT: every check PASSED; residue limited to the named phantom
  and the named batch-local siblings.                                    EXIT=0
```

### §A GREEN receipt
```
tests/test_secret_typing.py::...::test_secretstr_is_minted_only_where_a_credential_ORIGINATES
tests/test_secret_resolution_seam.py::...::test_every_environment_read_is_the_entry_point_or_allowlisted
tests/test_surreal_harness.py::...::test_the_harnesss_docstring_counts_are_the_DERIVED_counts
3 passed in 2.96s
```

## §B — GROUP B fix (04b-2's 12 inherited orphans, behaviour-preserving)
ruff (6):
- `scripts/c3_wrongbuild_driver.py` — 2× PLW1510: added explicit `check=False` to the two `subprocess.run` calls (`_collect`, `_run`); `check=False` is already the implicit default → no behaviour change. 3× E501: the long lines are byte-exact anchor/replacement DATA for the mutation driver, so they were wrapped via **implicit string concatenation** (the parser folds adjacent literals into ONE constant). Proven byte-exact: the sorted set of every `str` constant in the file is IDENTICAL to `HEAD:scripts/c3_wrongbuild_driver.py` (`string constants identical: True`).
- `scripts/audit_probes/coldaudit_wavec_r2_probe2.py:230` — PLC0206: `for name in GRAPHS` → `for name, graph in GRAPHS.items()` (and `GRAPHS[name]` → `graph`).

typecheck (6):
- `scripts/audit_probes/coldaudit_wavec_r2_probe4.py` — `_Malformed.subject` property gains `-> str`; the `create_many(bad_batch, …)` call gains `# type: ignore[arg-type]` (the batch DELIBERATELY carries a protocol-violating `_Malformed`; feeding a non-`TaskSpecLike` item IS the atomicity probe — `_Malformed.blocked_by = None` cannot satisfy `TaskSpecLike.blocked_by: list[str]`, so a `cast` would lie; `type: ignore` is the honest suppression).
- `scripts/audit_probes/coldaudit_wavec_r2_probe3.py:88` — `_set_blocked_by(db, …)` → `db: Any` (added `from typing import Any`).
- `scripts/c3_harness_repair.py` — 3× attr-defined: `FakeAgentRegistry`/`FakeAgentDatabase` were imported through `test_comms_tool` (which re-imports them without `__all__`). Repointed both imports to their REAL defining module `_comms_fakes` (which `test_comms_tool` itself imports them from; `_comms_fakes` has no `__all__`, so its direct class defs are exported). Same class objects → behaviour identical.

### §B GREEN receipt
```
ruff (c3_wrongbuild_driver.py, coldaudit_wavec_r2_probe2.py): All checks passed!
mypy (probe4, probe3, c3_harness_repair): Success: no issues found in 3 source files
```

## Verification
- 3 previously-failing GROUP A tests → GREEN (`3 passed`, counts above).
- 3 GROUP A probes run exit 0 against spike `:18000` (§A.run); `loremaster.__file__` printed from the real checkout.
- ruff on all 8 touched scripts + `c3_wrongbuild_driver` byte-exactness → clean.
- mypy on all touched scripts → clean.
- Tests hit spike-surreal `:18000` ONLY (topology derives from `_HARNESS.surreal_url()`, defaulting to `:18000`; both scripts keep the `18500`-refusing assertions).
- `scripts/pending_contract_gate.py --currency` → **CURRENCY: PASS**, zero RED_ORPHANED:
```
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 191 residual(s), owned by: packet-39-pending-build (trigger: operator decision #296, or packet 39's build start)
  ruff         GREEN
  pytest       RED_ADJUDICATED — 444 residual(s), owned by: packet-39-pending-build (trigger: operator decision #296, or packet 39's build start)
CURRENCY   : PASS — every claimed gate is GREEN or OWNED
```
The remaining reds are packet 39's ADJUDICATED bound (owned, with a trigger) — NOT orphaned, and NOT touched by this wave. My 15 targets (3 pytest orphans + 12 ruff/typecheck orphans) all flipped GREEN, so the orphan set is empty.

## Friction (could NOT file in lore — store transiently down)
- At close-out, `lore_comms action=send` (×2) AND `lore_findings action=report` all failed with
  `SurrealDB … query/transaction failed against 'ws://127.0.0.1:18500/rpc': no close frame received or sent`.
  The same session's earlier `register`/`drain` succeeded, so this is a TRANSIENT WebSocket drop on
  the production lore-surreal store, not a mis-call. Recording it HERE (the working channel) since I
  could not file it via `lore_findings`. **Please file it (area=lore_comms, category=capability_gap)
  when the store recovers**, or re-run my send. Non-fatal to this wave: proof-of-receipt is this
  report artifact, not the send return.

## Handoff notes for the lead
- `scripts/coldaudit_cycle_04b3_fork_a_refute.py` is untracked — `git add` it in the commit (the pins already govern it on disk).
- No git operations performed (COMMIT-ONLY brief; the lead commits). No deploy. `tasks.py` and the CYCLE contract tests untouched.
- The 102 auth/posture mypy errors are packet 39's ADJUDICATED bound — LEFT untouched; none of my edits are in that set.
