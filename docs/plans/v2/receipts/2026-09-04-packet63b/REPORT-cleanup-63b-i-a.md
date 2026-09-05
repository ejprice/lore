# REPORT-cleanup-63b-i-a

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **receipt:** brief-base v14 read · brief project v7 read
- **state:** **done**
- **deviations:**
  1. First full-suite run was CONTAMINATED by MY concurrent currency-gate pytest (two full suites at
     once) → `3 failed, 9 errors` all in `test_migration_wire.py`/`test_ingest_entity_seam.py`
     (`uvicorn did not report started within 15s` / store-txn rejection = resource starvation). PROVEN
     load-induced: isolated re-run **59 passed**; SOLO full suite **11077 passed / 0 failed / 0 errors**.
     None in the edited file or any governed/F5 module.
  2. The currency-gate background job was killed by the bg-job reaper twice (+ its watcher once) before
     emitting output — a job-lifecycle stop, not a gate failure. Ran it in the FOREGROUND → completed.
- **Packages considered:** none — no mechanism specified (mechanical dead-code + prose cleanup).
- **Reuse ledger:** none — deletions + one docstring only; no new symbols introduced.
- **Graded:** n/a — this is a cleanup/build report, renders no verdict on another artifact. Built on
  `81250d8`; HEAD-at-report `81250d8` (unmoved, edit uncommitted — lead commits).
- **decisions-needed (lead):** none blocking. FYI: cold-audit residuals **(c)** `_defined_test_names`
  DRY dedup and **(e)** latent double-arm `__wrapped__` pin remain DEFERRED (explicitly out of my
  scope, per brief). No cascade: `declared_workspace_members`/`derive_member_source_roots` stay live.
- **pointers:** deleted-fn 0/0 re-confirm table → §"Investigation"; edits → §"Edits made";
  gate tails → §"Gate results" + §"CLEAN receipts"; contamination analysis → §"First full-suite run
  CONTAMINATED"; dead-code non-regression → §"lore_dead_code regression → NONE".

### VERIFY — all green (SOLO, at working tree over 81250d8)
| gate | result |
|---|---|
| F5 pins `test_memory_enforcement_63b_ia.py` (`-n0`) | **33 passed** (1 benign coroutine-close warning) |
| Migrated `_63a_v`+`_63a_iv`+`_bounds_63a_iv` (`-n0`) | **27 passed** |
| FULL suite `-n auto` SOLO | **11077 passed, 51 skipped, 3 xfailed, 0 failed, 0 errors** (311s) = baseline |
| `uv run ruff check .` | All checks passed! |
| `./scripts/typecheck.sh` | 0 errors (all members) |
| `scripts/pending_contract_gate.py --currency` | **PASS — typecheck/ruff/pytest all GREEN, 0 RED_ORPHANED** |
| `lore_dead_code` regression | NONE (233 candidates, none in edited file, 4 deleted fns absent) |

## MISSION
Mechanical dead-code + prose-currency cleanup specified by the F5 cold-audit
(REPORT-cold-audit-63b-i-a.md §RESIDUALS a/b/d). Packet 63b wave i-a. Branch
feat/surreal-unification, HEAD 81250d8. F5 build is GO; this is post-GO cleanup.

### Scope (exact)
1. Delete 4 DEAD functions from `loremaster/tests/_governed_contract.py`
   (re-confirm 0/0 via lore_impact before each delete):
   - `_mutation_verb_for_table` (residual a)
   - `seam_modules_for_tree_allowlist` (residual d)
   - `_module_for_repo_relative_file` (residual d)
   - `_originating_prod_site` (residual d)
   + remove any orphaned imports/module-level names.
2. Trim ONE docstring (residual b): `observe_governed_table_writes` — rewrite the
   stale "★CONTRACT SHAPE★ … at HEAD the body is the retired verb-observer" framing
   to describe the BUILT mechanism; keep the reach-evidence citation by name.

### NOT in scope
- (c) `_defined_test_names` DRY dedup, (e) latent-double-arm pin — DEFERRED.
- No production code (governed.py/principals.py/local.py), no frozen contract pins,
  no F5 allowlist DATA. No git state mutation (lead commits).

## WORK LOG

### Investigation (all in `loremaster/tests/_governed_contract.py`, tier `lore`, HEAD 81250d8)
Re-confirmed each target DEAD via `lore_impact` (index fresh at 81250d8):
| function | lore_impact verdict | source span (at 81250d8) |
|---|---|---|
| `_mutation_verb_for_table` | dead — 0 prod / 0 test refs | 1125–1149 |
| `_originating_prod_site` | dead — 0 prod / 0 test refs | 1541–1565 |
| `_module_for_repo_relative_file` | dead — 0 prod / 0 test refs | 1767–1777 |
| `seam_modules_for_tree_allowlist` | dead — 0 prod / 0 test refs | 1780–1795 |

**Cascade check (the load-bearing finding — VERIFY "no NEW dead helper"):** the two deleted
callers `_module_for_repo_relative_file` / `_originating_prod_site` are the SECOND consumers of
two helpers I did NOT delete. `lore_impact` reported each helper "0 prod / 1 test ref", which I
initially mis-read as "only the dead caller references it" — but READING the source (not trusting
the undercounted heuristic) showed the single ref is a LIVE consumer:
- `derive_member_source_roots` — called by `governed_table_raw_mutation_sites_in_tree`
  (`_governed_contract.py` line 1490 at 81250d8, the LIVE whole-tree L1 scanner, 2 test refs) AND
  by the deleted `_originating_prod_site`. → STAYS LIVE.
- `declared_workspace_members` — called by `derive_member_source_roots` (line 1442, live) AND by
  the deleted `_module_for_repo_relative_file`. → STAYS LIVE.
So there is **NO cascade** — the 4 named functions are the only deletions; no helper is orphaned.
(This is why brief-base §4/CLAUDE.md demand re-derivation: `lore_impact`'s "1 test ref" undercounted
the true 2 call sites; source reading corrected the count.)

### Edits made (`loremaster/tests/_governed_contract.py`)
1. **Removed 3 orphaned imports** (each used ONLY inside a deleted function — programmatic scan
   confirmed no other code use; prose mentions at lines 52/964 remain and are fine):
   `import importlib` · `import sys` · `from types import ModuleType`.
2. **Deleted 4 dead functions** (spans above), collapsing blank lines to PEP8 2-blank separation.
3. **Rewrote the `observe_governed_table_writes` docstring** (residual b): replaced the stale
   pre-build "★CONTRACT SHAPE★ … at HEAD the body is the retired verb-observer" framing with a
   description DERIVED from the BUILT mechanism — the per-block `_F5_REGISTRY` + the ONE persistent
   `_f5_dispatcher` appended once at import; `query_raw`-door-only observation; reads via the
   UNWRAPPED `query_raw` (`_f5_unwrapped_query_raw` → `__wrapped__`); per-call `ObservedEffect`
   state-diff; per-loop lock. Kept the reach-evidence citation to
   `test_the_UNCOUNTABLE_door_set_is_DERIVED_from_the_SDK_and_DENIES_BY_DEFAULT` by name. This edit
   also removed the only surviving prose reference to the deleted `seam_modules_for_tree_allowlist`.

Post-edit static verification (`python3 ast.parse` + scan): file PARSES; all 4 deleted defs absent;
kept defs (`declared_workspace_members`, `derive_member_source_roots`,
`governed_table_raw_mutation_sites_in_tree`, `observe_governed_table_writes`) present; `ModuleType`
0 hits, `importlib`/`sys` prose-only; zero dangling references to any deleted name. 1913 → 1817 lines.

### Gate results (at working tree over 81250d8)
- `uv run ruff check .` → **All checks passed!**
- `./scripts/typecheck.sh` → all members OK, **0 errors** (lorerunes 13 / lorescribe 27 /
  loresigil 35 / loremaster 259 / skills 12 / docs/eval 2 / scripts 53; shellcheck OK).
- F5 pins serial `-n0` (`test_memory_enforcement_63b_ia.py`) → **33 passed** (1 benign
  coroutine-close warning in the intentional raising-hook test — same as cold-audit baseline).
- Migrated 63a (`_63a_v` + `_63a_iv` + `_bounds_63a_iv`) `-n0` → **27 passed**.
- `lore_dead_code` regression → **NONE.** Reconciled index (last_sweep 0.9s, git_ref=81250d8=HEAD,
  0 failures). 233 dead candidates repo-wide; the 4 deleted fns ABSENT; **zero** dead nodes in
  `_governed_contract.py` (test-tree, excluded from the scan). Post-reconcile `lore_impact`:
  `declared_workspace_members` and `derive_member_source_roots` each STILL 0 prod / 1 test ref —
  both retain their live consumer, so no helper was orphaned.

### ⚠ First full-suite run was CONTAMINATED by my own concurrent currency-gate run (MY error, disclosed)
I launched `scripts/pending_contract_gate.py --currency` (which runs its OWN full pytest) while the
`-n auto` full suite was already running — TWO full pytest suites hammering the `:18000` store +
spinning uvicorn simultaneously. Result of that contaminated run:
`3 failed, 11065 passed, 51 skipped, 3 xfailed, 9 errors in 522.36s` (vs the cold-audit's SOLO 315s).
- **Every** non-pass was in `test_migration_wire.py` (9 errors + 2 failures, all
  `RuntimeError: uvicorn did not report started within 15s (heavy build failed?)`) + one
  `test_ingest_entity_seam.py` store-transaction rejection — resource-starvation signatures, NOT
  `ImportError`/`NameError` (which is the only way my substrate edit could break another module).
- **None** is in the file I edited or any governed/F5 module. `11065 + 3 + 9 = 11077` = exact baseline.
- The concurrent currency gate ALSO RED-orphaned the SAME `test_migration_wire.py` tests — two
  independent pytest runs failing on the identical uvicorn tests = corroborated contention.
- **Isolated re-run** `uv run python -m pytest -n auto loremaster/tests/test_migration_wire.py
  loremaster/tests/test_ingest_entity_seam.py` → **59 passed in 17.01s.** Every contaminated test
  passes alone → the failures were load-induced transients, not a regression. (Not "flaky" — a named
  resource-contention mode: uvicorn's 15s startup timeout under CPU starvation.)

### CLEAN receipts (solo runs, nothing concurrent)
- **FULL suite `-n auto` SOLO** → `11077 passed, 51 skipped, 3 xfailed, 7 warnings in 311.00s` —
  **0 failed, 0 errors, FULL_SUITE_EXIT=0.** EXACTLY the cold-audit baseline (11077 passed / 0 failed).
- **Currency gate** (`scripts/pending_contract_gate.py --currency`, foreground, `CURRENCY_EXIT=0`) →
  ```
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    GREEN
  ruff         GREEN
  pytest       GREEN
  CURRENCY   : PASS — every claimed gate is GREEN or OWNED
  ```
  **0 RED_ORPHANED.** The RED_ORPHANED it reported during the contaminated concurrent run (all
  `test_migration_wire.py`) is gone once run solo. (Two SOLO background attempts were killed by the
  bg-job reaper before emitting output — a job-lifecycle stop, not a gate failure; the foreground run
  completed cleanly.)
