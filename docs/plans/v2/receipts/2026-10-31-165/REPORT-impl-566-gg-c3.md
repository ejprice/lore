brief-base v25 read

# REPORT-impl-566-gg-c3 — #566 C3 + #569, GREEN (tdd-light Phase 4), 2026-10-31

## SUMMARY
- **State:** done. Every gate is green on the final content (`scripts/gated_ground.py` md5 `f1accbcbec335a5f9c6ef4417bb526d1`). Gate 1: 351 passed / 0 failed (was 4 failed / 347 passed at HEAD). Gate 2: 85 passed. mypy and ruff are clean. Currency: RED_ORPHANED 0.
- **Deviations:** none to scope (writable set: `scripts/gated_ground.py` only). The brief named `scripts/test_secret_resolution_seam.py`, which does not exist; I ran `loremaster/tests/test_secret_resolution_seam.py` instead.
- **Packages considered:** `_pytest.main` for the `norecursedirs` default. I read the installed pytest 9.0.3 source. The default is an inline `default=[...]` literal in `pytest_addoption`, reachable only through the private parser (`get_config([])._parser._inidict`), and the module is stdlib-only by its own docstring. Verdict: `keep_with_trigger` for a copied constant. Trigger: a contract pin that re-derives it, which is MISSING (decision D1). Matching reuses the existing in-repo `fnmatch_ex` port, `_matches_collection_pattern`.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 5 new symbols, all dispositioned (§DRY ledger).
- **Graded:** n/a (builder report; no verdict on another's artifact). Built on HEAD `699b058`.
- **The ONE function:** `gated_ground._pytest_loads_conftest(path, *, testpaths, norecursedirs, repo_root)`.
  - Call site 1: `_execution_fate`, the LEG B verdict for a tracked conftest.
  - Call site 2: `_collector_input_paths`, the memo key, which filters every enumerated conftest address through it.
- **Sharing mutation:** run in a scratch copy. The pruning check in the shared function was replaced with `and True`. Declared 4 RED (2 verdict pins + 2 agreement pins, from `--collect-only`); observed exactly those 4: `PROOF HELD`, restored byte-exact. In both agreement pins the failure tuple was `(True, True)`, meaning the KEY moved and the verdict covered the conftest. So both callers observed the mutation, not just the verdict. Receipt: §Mutation proof.
- **Memo-key change:** exactly one population changed. An UNTRACKED `conftest.py` under a testpath inside a `norecursedirs`-pruned subtree now leaves the key. That is #569's class. `build/` and `.hidden/` are pinned; the other patterns are not pinned per pattern (F2). No other placement moved (§Memo-key inventory).
- **Decisions needed:** D1 (no contract pin re-derives `PYTEST_DEFAULT_NORECURSEDIRS`; that is a test-author item). F1 (venv/`__pycache__` pruning is not modelled). Both are below.
- **Pointers:** §What changed · §Memo-key inventory · §Mutation proof · §Gate receipts · §Flags.

## Capability check
- Demanded vs held: all held (Bash, Edit, Agent→haiku-runner, lore MCP, systemd-run). No DENIED tool call.
- Brief named `scripts/test_secret_resolution_seam.py`; that path does not exist. The file is
  `loremaster/tests/test_secret_resolution_seam.py` (it pins a per-function env-read allowlist keyed on
  `scripts/gated_ground.py::_collector_input_fingerprint`); I ran that one.
- Echo: `brief project v7 read` (lore_comms register, session fix-165-2026-10-31).

## Routing table (written at start, before the first sweep)
| step | tier | who | reason |
|---|---|---|---|
| read contract pins + gated_ground.py + r2b §2/§7 | 3 | self | design of the one shared function; an error here seals itself (looks right, every caller agrees with it) |
| consumer sweep (`git grep -ln gated_ground`) | 1 | self, single inline call | one grep, 10 hits, on the critical path (decides gate 2 scope); output read in full |
| gate 1 contract run | 1 | haiku-runner | test run |
| gate 2 consumer runs | 1 | haiku-runner | test run |
| gate 3 mypy / ruff / currency | 1 | haiku-runner | lint/type gate |
| mutation proof run (scratch) | 1 run · 3 verdict | haiku-runner ran it; I judged | mutation verdicts are never Haiku |
Fan-out: haiku 4 · sonnet 0 · peak 4. Test runs: delegated, none inline.

Consumer sweep coverage: `git grep -ln gated_ground -- scripts tests '*.py' '*.sh' '*.yaml' '*.toml'` → 10 files.
Verdicts: `scripts/gated_ground.py` (self) · `scripts/test_gated_ground.py` (gate 1) · `scripts/test_wrong_builds.py` +
`scripts/wrong_builds.py` (gate 2; anchors checked, none overlap my edits) · `scripts/test_trailing_newline_matrix.py` +
`scripts/_newline_matrix.py` (gate 2) · `scripts/test_harness_guards.py` (gate 2; prose mention only) ·
`loremaster/tests/test_secret_resolution_seam.py` (gate 2; source scan) · `loremaster/tests/test_findings_cas_seam_64b.py`
(prose mention only in a docstring, no import; NOT run) · `scripts/typecheck.sh` (gate 3 currency typecheck leg).
lore_impact not used: it cannot see `scripts/` (#507) — grep fallback, said out loud.

## What changed (`scripts/gated_ground.py` only; symbols, not lines)
1. **`_pytest_loads_conftest(path, *, testpaths, norecursedirs, repo_root)` — THE ONE function.** Loaded iff the
   conftest's directory is a path-component ancestor of some testpath, OR it is under a testpath and
   `_recursion_is_pruned(...)` is false. Keyword-only so the two new inputs cannot be transposed.
   - Call site 1 (verdict): `_execution_fate` → `scopes.testpaths / scopes.norecursedirs / scopes.repo_root`.
   - Call site 2 (memo key): `_collector_input_paths` filters every candidate conftest address through it.
2. **`_recursion_is_pruned(directory, *, testpath, norecursedirs, repo_root)`** — every component from just below the
   testpath down to the conftest's directory (inclusive) is tested; the testpath itself is not (explicit targets
   are not pruned, measured in the contract's own comment). Matching reuses `_matches_collection_pattern` (the
   existing `fnmatch_ex` port) on the ABSOLUTE path, as `_pytest.main.pytest_ignore_collect` does
   (`fnmatch_ex(pat, collection_path)`, read in the installed pytest 9.0.3).
3. **`pytest_norecursedirs(repo_root)`** — ini value REPLACES the default, never a union; absent key → default;
   `[]` returned as-is (pytest prunes nothing; honest, not vacuous). Called from `_derive` (new `_Scopes.norecursedirs`
   field) AND from `_collector_input_paths` (whose signature is pinned by the contract, so it reads the manifest itself).
4. **`PYTEST_DEFAULT_NORECURSEDIRS`** constant — see Packages line / Decisions D1.
5. **`_pytest_ini_list` / `_pytest_ini_described_as`** — extracted from `pytest_test_file_patterns` so the two
   ini-list readers share one parse + one refusal spelling (no behaviour change to `pytest_test_file_patterns`: same
   default, same `python-files-empty` door, same message text).
6. **`_collector_input_paths`**: conftest addresses are now ENUMERATED (the root → testpath chain, plus every
   `conftest.py` the `os.walk` meets under a testpath) and then FILTERED by the shared predicate. Non-conftest `.py`
   under a testpath stay in the key unconditionally, pruned directory or not (r2b §7 item 4: a collected test can
   import them). The root `conftest.py` moved from the fixed-file set into the chain (still in the key; the
   predicate's ancestor leg covers `.` for any non-empty testpaths, and `pytest_testpaths` refuses empty).
7. Docstrings updated: the `collector-memoisation` bound and `_collector_input_paths`' populations now name the
   shared predicate instead of "the chain".

## Memo-key change inventory (removed-behaviour inventory for `_collector_input_paths`)
| population | before | after | adjudication |
|---|---|---|---|
| manifest + shadowing config files | in key | in key | preserved |
| root `conftest.py` | in key (fixed set) | in key (chain → predicate ancestor leg) | preserved; pinned by the agreement pin's `conftest.py` row |
| chain conftests (ancestors of a testpath) | in key | in key (predicate ancestor leg) | preserved; agreement pin rows |
| every tracked `.py` | in key | in key | preserved (tracked conftests in pruned dirs stay in the key via this population) |
| untracked non-conftest `.py` under a testpath | in key | in key, even in a pruned dir | preserved (deliberate, r2b §7.4) |
| untracked `conftest.py` under a testpath, NOT in a pruned subtree | in key | in key | preserved; nested agreement rows |
| **untracked `conftest.py` under a testpath IN a pruned subtree** | in key | **OUT of key** | **the one change**; it is #569's class. Pinned rows: `build/` and `.hidden/`. NOT individually pinned: the other default patterns (`*.egg`, `_darcs`, `CVS`, `dist`, `node_modules`, `venv`, `{arch}`), a configured `norecursedirs`, and two-level pruning (`store/lease` under `["store"]`) — same predicate, same code path, but no row. Flagged F2, not a STOP: it is the change the ruling asks for, applied by the one predicate, not a different placement class. |

## DRY ledger (new symbols; brief-base §6)
| symbol | where I looked | disposition |
|---|---|---|
| `_pytest_loads_conftest` (reshaped, not new) | the brief named it; both encodings were read in full | the ONE owner; the second encoding (the inline chain loop in `_collector_input_paths`) is now an address ENUMERATION whose membership this function decides |
| `_recursion_is_pruned` | `gated_ground.py` (the `is_under`, `_matches_collection_pattern` and `_widens_to_whole_tree` helpers); `git grep -n norecursedirs -- '*.py'` found only the contract file and the pytest `ini` fixtures; no other pruning model exists in the repo | new; reuses `_matches_collection_pattern` for the match itself |
| `pytest_norecursedirs` | `pytest_test_file_patterns` (the same shape) | new reader; shares `_pytest_ini_list` with that sibling |
| `_pytest_ini_list`, `_pytest_ini_described_as` | extracted out of `pytest_test_file_patterns` | extracted so the two ini-list readers cannot drift (no behaviour change) |
| `PYTEST_DEFAULT_NORECURSEDIRS` | installed `_pytest/main.py::pytest_addoption` (pytest 9.0.3) | copied constant; no public pytest constant exists (D1) |
lore was not used for the reuse search: `scripts/` is invisible to lore_impact (#507). The fallback to grep plus reading is stated here.

## Decisions (both readings written down, per brief-base §2)
- **D1: where the `norecursedirs` default comes from.**
  - Reading A: import `_pytest.main` at runtime and read the default from the private parser (`get_config([])._parser._inidict["norecursedirs"][2]`). This is the contract's own idiom for `python_files`.
  - Reading B: carry a constant, with its source and version cited.
  - I chose **B**. The module's stated design is "imports the standard library and nothing else". Every sibling default (`PYTEST_DEFAULT_TEST_FILE_PATTERNS`, `SHADOWING_CONFIGURATION_FILENAMES`) uses B, and the contract re-derives it.
  - ⚠ **The re-derivation pin for this constant does not exist.** `scripts/test_gated_ground.py` has none, and I may not write one (role boundary). Until a test author adds the pin (same shape as `_pytest_declared_default_patterns`, key `norecursedirs`), the constant is an inherited copy. The constant's own comment says so. **A test-author item for the lead.**
- **D2: an empty configured `norecursedirs = []`.** I return it as-is (pytest prunes nothing), not as a blind refusal. Unlike an empty `python_files`, it does not make the leg vacuous. Not pinned either way.
- **D3: ancestors of a testpath are never pruned.** The brief says the components BETWEEN the testpath and the conftest are checked, so the ancestor leg ignores `norecursedirs`. Whether pytest loads `loremaster/conftest.py` under `norecursedirs = ["loremaster"]` was NOT measured (no row, no oracle). Flagged as F3.

## Flags (everything noticed; scope is the operator's)
- **F1. Other directory skips are not modelled.** `_pytest.main.pytest_ignore_collect` (read, 9.0.3) also skips `__pycache__` and virtualenv directories (`_in_venv`, unless `--collect-in-virtualenv`). A conftest planted in either would read as covered by the verdict and stay in the key. No pin asks for it, and r2b §7.3 calls it a planted-data edge. Not built (do not add untested behaviour). Re-open trigger: a pin for either shape.
- **F2. The key change is broader than its two pinned rows.** It covers every `norecursedirs` pattern and a configured ini value. Same predicate, same code path, but only `build/` and `.hidden/` have rows. The oracle pin re-measures only those two.
- **F3. Pruning of a testpath ANCESTOR is unmeasured** (D3).
- **F4. A conftest dropped from the key could, pathologically, be imported by a collected test.** Example: an untracked `build/conftest.py` imported as a module. Its content would then move the answer while the key stays still. Non-conftest helpers in pruned directories stay in the key for exactly this reason. Conftests are filtered because the agreement pin's converse leg requires it (r2b §7.4, F1 ruling).
- **F5. `pending_contracts.yaml` has no entry for the 4 r2b reds (r2b §7 "Adjudication needed").** They are GREEN on this build, so the entry is moot if this lands. If it does not land, they are orphaned reds.
- **F6. The currency `--legs typecheck,ruff` run prints `pytest NOT_RUN … ORPHAN` and `CURRENCY: FAIL`.** That comes from the leg selection the brief mandates, not from a red. The verdicts that matter are per leg: typecheck RED_ADJUDICATED (83 residuals, owners packet-58-contract / packet-64b-i-contract) and ruff. See the gate table. The tool reports leg selection as FAIL; filing a finding is worth considering (lead's call).
- **F7. The intermediate receipts' TREE= drifted (`3229…` → `10298…` → `d0492…`).** The cause was my own edits: the docstring rewrap after ruff's E501 on my line, plus heartbeat edits to this report (an untracked file inside the hash). Only the final-run receipts below count. Each final log also carries `md5sum scripts/gated_ground.py`, so its content can be matched against the commit even though this report file changed after the run.
- **F8. A ruff E501 on my own docstring line was caught by gate 3's first run** (`gate3b-ruff.log`, `gate3c-currency.log`: RED_ORPHANED 1). Fixed and rerun.

## Mutation proof (rider)
- Scratch: `./scripts/scratch_copy.sh /var/tmp/claude-1000/gg566c3-scratch` → EXIT=0, provenance asserted.
- `loremaster.__file__= /var/tmp/claude-1000/gg566c3-scratch/loremaster/loremaster/__init__.py`. `LORE_PYTHON` was exported to the scratch venv.
- Mutant: anchor `/var/tmp/claude-1000/gg566c3-logs/mut-anchor.txt` (the `and not _recursion_is_pruned(...)` clause of `_pytest_loads_conftest`), replaced by `and True`. One edit, inside the ONE function only.
- Declared RED (from `--collect-only`, written to `/var/tmp/claude-1000/gg566c3-logs/declared-red.txt` BEFORE the run): the 2 `test_a_conftest_pytest_never_loads_stays_execution_ungated[...]` verdict pins and the 2 `test_the_memo_key_and_the_verdict_give_one_answer_per_placement[...]` agreement pins, for `loremaster/tests/build/conftest.py` and `loremaster/tests/.hidden/conftest.py`. The ids are in `scripts/test_gated_ground.py::…` form, matching the scratch root as cwd (#560).
- Run 1 (`mutation.log`, gated_ground md5 `f62ef57a…` = pre-rewrap content; docstring-only difference from the final): `4 failed, 347 passed`, `PROOF HELD — the declared RED set fired EXACTLY`, `tree restored byte-exact`, EXIT=0. The agreement pins failed with `assert (True, True) == (False, False)`: key moved = True and verdict covered = True. **Both callers changed with the shared function.**
- Run 2 (`mutation-final.log`, on the FINAL content, md5 `f1accbcb…` before and after): `4 failed, 347 passed`, LANDED, `PROOF HELD`, restored byte-exact, EXIT=0, both agreement tuples `(True, True)`. Scratch `TREE=e4d0e06a…` (differs from the main tree only by its untracked/scratch contents).
- Why this shows sharing and not just a red: had the key kept a private copy, the agreement tuple would have read `(False, True)`, not `(True, True)`.

## Gate receipts (final; all on gated_ground.py md5 `f1accbcbec335a5f9c6ef4417bb526d1`, main-tree TREE=`75dfca42d392bb4aa944b80cbc784e93d8ca95231dde70fc5d2c8ac288621149`, HEAD `699b058`, DIRTY_FILES=30)
Each command is wrapped as `{ tree_id.sh <wt>; md5sum scripts/gated_ground.py; <cmd>; echo EXIT=$?; } > <log> 2>&1`.
| gate | command | log | EXIT= | count / verdict line |
|---|---|---|---|---|
| 1 contract | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q scripts/test_gated_ground.py -n 8 --timeout=300 -p no:cacheprovider -rfE` | /var/tmp/claude-1000/gg566c3-logs/gate1-final.log | 0 | `351 passed in 51.30s` |
| 2 consumers | same wrapper; `pytest -q scripts/test_wrong_builds.py scripts/test_trailing_newline_matrix.py scripts/test_harness_guards.py loremaster/tests/test_secret_resolution_seam.py -n 8 --timeout=300 -p no:cacheprovider -rfE` | /var/tmp/claude-1000/gg566c3-logs/gate2-final.log | 0 | `85 passed in 3.54s` (counts are per run; not split per file) |
| 3a mypy | `MYPYPATH=scripts uv run mypy scripts/gated_ground.py` | /var/tmp/claude-1000/gg566c3-logs/gate3a-mypy-final.log | 0 | `Success: no issues found in 1 source file` |
| 3b ruff | `uv run ruff check scripts/gated_ground.py` | /var/tmp/claude-1000/gg566c3-logs/gate3b-ruff-final.log | 0 | `All checks passed!` |
| 3c currency | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` (no `-n`) | /var/tmp/claude-1000/gg566c3-logs/gate3c-currency-final.log | 1 | typecheck RED_ADJUDICATED (83, owners packet-58-contract · packet-64b-i-contract) · ruff GREEN · **RED_ORPHANED 0** · pytest NOT_RUN (excluded by `--legs`; F6) |
| rider | `mutation_proof.py` in scratch (§Mutation proof) | /var/tmp/claude-1000/gg566c3-logs/mutation-final.log | 0 | `4 failed, 347 passed` · PROOF HELD · restored byte-exact |
These logs are under `/var/tmp` (the brief's scratch convention), not tracked. The lead archives them if they are wanted.
After these runs, only this report file changed (it is untracked and inside TREE's hash), so recompute TREE without it or match by the md5 line. Superseded runs (`gate*.log` without `-final`, `*-r2.log`, `mutation.log`) are kept as history for F7/F8.
