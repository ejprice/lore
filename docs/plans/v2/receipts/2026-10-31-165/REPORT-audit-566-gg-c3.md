brief-base v25 read

# REPORT-audit-566-gg-c3: tdd-light Phase 5 REFACTOR+AUDIT of 169539d (#566 C3 + #569)

## SUMMARY
- **Verdict: GO.**
  - The merge into the one `_pytest_loads_conftest` rule is sound.
  - No third copy of the rule exists.
  - The memo key was NOT found blind to any conftest pytest loads. Probes `probe-nrd-a`/`-b` and pytest 9.0.3's `Dir.collect`/`pytest_ignore_collect` source were read.
  - The `norecursedirs` matching follows `fnmatch_ex` semantics on directories.
  - The commit is GO, but the contract carries a mutation-proven gap (F4) and LEG B carries a pre-existing false-COVERED class (F2). Both are routed below; neither blocks the commit.
- **Fixed in place (doc only, no behaviour change; diff `scripts/gated_ground.py` +15/−7, md5 `329f3be434caddf6229e99cb6ea46309`):**
  - F1: the `conftest-collection-hooks` elaboration. It now states the #569 condition and names the pruning it does NOT model. Its "every other mechanism is caught" claim is now scoped to test FILES. A matching sentence was added to the `_pytest_loads_conftest` docstring.
  - F3: the `PYTEST_DEFAULT_NORECURSEDIRS` comment now cites the drift pin `test_the_declared_norecursedirs_default_matches_what_pytest_puts_in_force`, which landed in `7356fdf`. This also discharges lead directive #18013, which is acked.
- **Routed:**
  - F2 → finding **#570**: a tracked conftest in a `collect_ignore`d or virtualenv dir under a testpath reads COVERED; pytest never loads it. This was measured, predates 169539d, and is a fork: close the venv leg, or keep it as a stated instance of the registration bound.
  - F4 → finding **#571**: the #569 pins are leaf-only and default-list-only. This is mutation-proven; three more wrong builds are reasoned to survive.
  - F5 and F6 are LOW residuals, listed below.
- **Mutation (W2, leaf-only pruning), run in scratch `/var/tmp/claude-1000/gg566c3-audit-scratch`:**
  - `loremaster.__file__` = `/var/tmp/claude-1000/gg566c3-audit-scratch/loremaster/loremaster/__init__.py`.
  - Declared from `--collect-only` before the run: the 4 #569 pins (`/var/tmp/claude-1000/gg566c3-declared4.txt`). My prediction was that it would SURVIVE.
  - Observed: 352 passed, 0 red. All 4 declared pins stayed GREEN, with 0 unexpected reds. `mutation_proof` EXIT=4. The file was restored byte-exact (md5 `f1accbcb…`).
  - **The mutant survives**, so the pins do not carry the subtree rule. Log: `/var/tmp/claude-1000/gg566c3-mutation.log`.
- **Gates** (log `/var/tmp/claude-1000/gg566c3-gates.log`; TREE=`4c02212a…d9a9` @ HEAD `7356fdf`, 32 dirty files in the shared tree):
  - pytest on the 4 named files, `-n 8 --timeout=300`, under a 16G cgroup: **373 passed**, PYTEST_EXIT=0. This includes the sibling's committed pin.
  - mypy: `Success: no issues found in 1 source file`, MYPY_EXIT=0.
  - ruff: `All checks passed!`, RUFF_EXIT=0.
- **Fan-out:** haiku 2 · sonnet 0 · peak 1. Both haiku runners' RAN lines were checked against my commands.
- **Builder report:** read only its "Memo-key change" line, after the cold review. It agrees with my independent read: one population left the key, and venv is flagged as unmodelled.
- **Denial:** one probe command containing `rm -rf` in the scratchpad was DENIED. It was re-run without `rm`.
- **Worktree/scratch:** I left `/var/tmp/claude-1000/gg566c3-audit-scratch` in place, with no `rm -rf` per the brief. The probe trees are in my session scratchpad. I did no git operations.

Liveness: started cold review of 169539d.

brief project v7 read

## Routing table (written before first sweep)
| step | tier | who | reason |
|---|---|---|---|
| cold review of gated_ground.py diff | 3 | self | audit verdict; error would self-seal |
| pytest-semantics probe (norecursedirs / initpath parents) | 3 | self | probe design + control is the judgment; output tiny |
| test-smell list on new pins | 3 | self | judging another agent's tests (never-Haiku) |
| collect-only for declared ids | 1 | self inline | one command on critical path, output read whole (<20 lines) |
| mutation run | 1 | haiku-runner | test run |
| gate pytest run (4 files) | 1 | haiku-runner | test run |
| mypy + ruff | 1 | haiku-runner (same spawn batch) | lint/type gate |

## Denials
- Bash probe command containing `rm -rf case1 case2` (scratchpad) DENIED; re-run without rm.

## Cold review findings (written BEFORE any edit; gated_ground.py md5 f1accbcbec335a5f9c6ef4417bb526d1 = 169539d + no local edits)

- **F1 (doc false, FIX in place):** module docstring `conftest-collection-hooks` elaboration still says a conftest is registered when "it lies under a testpath, or its directory is a path-component ancestor of one (#566)". False since #569: a conftest under a testpath in a `norecursedirs` directory is NOT registered. Its next sentence, "Every OTHER silencing mechanism is caught by construction, because LEG B measures collection", is true for test files only. A conftest's verdict comes from the predicate, not from measurement (see F2).
- **F2 (behaviour gap, pre-existing, ROUTE):** LEG B reads a TRACKED conftest as COVERED when it sits under a testpath in a directory pytest prunes by a mechanism other than `norecursedirs`. Measured on 2026-10-31 (pytest 9.0.3), probe tree `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/4429789a-9bb4-4f36-b28b-7683e2f3f362/scratchpad/probe-nrd-b`:
  - pytest loaded only `t/conftest.py` and `t/ok/conftest.py`.
  - The predicate said True for `t/venvdir/conftest.py` (the dir has `pyvenv.cfg`) and for `t/ign/conftest.py` (`collect_ignore = ["ign"]`). That is a false COVERED on LEG B, and over-inclusion in the memo key, which is benign.
  - It agreed with pytest on `.hid` and `build` (False).
  - Mechanisms seen in `_pytest.main.pytest_ignore_collect`: `__pycache__`, `collect_ignore`/`collect_ignore_glob`, `--ignore`/`--ignore-glob` (via addopts), and `_in_venv` (`pyvenv.cfg` / `conda-meta/history`).
  - 169539d narrowed the over-claim; it did not introduce it.
  - `collect_ignore*` is arbitrary conftest code, so no predicate can close it: it needs a stated bound. Venv detection is a stdlib file check and is closable.
  - Fork for lead/operator: close the venv leg, or state both as instances of the registration bound. I state them in the docstring (F1 fix) either way.
- **F3 (doc going false, FIX in place):** the `PYTEST_DEFAULT_NORECURSEDIRS` comment says "no contract pin re-derives it against the installed pytest yet". The sibling's pin `test_the_declared_norecursedirs_default_matches_what_pytest_puts_in_force` now exists in the working tree (uncommitted). Once that lands the comment is false. Edit it to cite the pin, and COMMIT IT TOGETHER with the sibling's test file, or the comment is false the other way.
- **F4 (contract gaps, ROUTE to contract author; W2 mutation-run below).** Wrong builds that pass all 351+1:
  - W2: test only the conftest's own directory, not every component between it and the testpath.
  - W3: union the ini value with the defaults.
  - W4: ignore the ini and always use the defaults.
  - W5: also prune the testpath's own components.

  §7 of the contract MEASURED subtree pruning and ini-REPLACES-default, and the builder's docstrings claim both. No pin carries them, because every #569 row is (a) a LEAF-level pruned dir and (b) under the DEFAULT list. That is the rider-drop pattern: measured, written down, never pinned. W3/W4/W5 survival is reasoned from the pin inventory, not run (MEDIUM).
- **F5 (residual, contract-ruled):** an untracked conftest in a pruned dir is now outside the memo key, as the F1 converse leg requires. The builder's own comment keeps non-conftest `.py` in pruned dirs because "a collected test may still import the module", and that rationale applies equally to an importable `conftest.py`. LOW: importing a conftest as a module is unusual, and the ruling is the lead's.
- **F6 (pre-existing, unmeasured, LOW/GUESS):** `os.walk` does not follow symlinked directories, while pytest's `scandir` `is_dir()` does. So an untracked conftest behind a symlinked dir under a testpath is plausibly outside the key, both before and after 169539d. It is inside the stated COMPLEMENT bound. Not probed.

**Memo-key question:** is the key newly blind to a conftest pytest DOES load? None found.
- The candidates are the chain plus the walk, filtered by the shared predicate.
- The predicate's only new False answers are `norecursedirs`-pruned subtrees.
- Probe `probe-nrd-a` (testpaths `["t","t/build/inner"]`, which exercises pytest's `isinitpath(with_parents=True)` exemption) agreed with the predicate on all 5 conftests. `t/build/conftest.py` was loaded via the ancestor leg; `t/build/other/conftest.py` was not loaded and the predicate said False. My hypothesis that it would be loaded was REFUTED.
- The root conftest with empty testpaths is refused upstream (`declared-paths-empty`).
- The key newly tracks one thing it should not: venv- and collect_ignore-pruned conftests (F2). This direction is benign.

**norecursedirs semantics:** `pytest_ignore_collect` calls `fnmatch_ex(pat, collection_path)` on the ABSOLUTE directory path, and `_matches_collection_pattern` is the port of `fnmatch_ex`. Its basename-vs-whole-path decision applies to directories unchanged, so the reuse is correct.
- Residual: pytest hands the un-resolved `direntry.path`, while the guard uses `repo_root.resolve()`. These differ only for separator-bearing patterns under a symlinked checkout root. This is the existing `_is_test_shaped` idiom. Negligible.

**DRY:** no third copy. `_pytest_loads_conftest` is called only from `_execution_fate` and `_collector_input_paths`. No other script encodes the rule (grep over `scripts/*.py`, `loremaster/loremaster`, `lorerunes/lorerunes` for `conftest`/`norecursedirs`; grep used because this is a non-symbol textual seam).

## Test-smell list (report only; no test edits)
- S1 = F4: #569 rows are fixture monoculture on two axes. The pruned component is always the leaf, and `norecursedirs` is always the default.
- S2: the failure message of `test_the_conftest_bound_does_not_claim_a_mechanism_the_collector_catches` asserts "The collector catches every silencing mechanism". For conftests that is false (F2, measured), so the message teaches a closure that does not exist. The assertion itself (summary avoids "collect_ignore") is fine.
- S3: the live oracle `test_the_load_tables_are_what_pytest_itself_loads` plants only default-`norecursedirs` trees, so it cannot re-measure ini-replaces-default or deep-subtree pruning.

## Fix-in-place receipts
- The edits were F1 (module docstring `conftest-collection-hooks` elaboration and the `_pytest_loads_conftest` docstring) and F3 (the `PYTEST_DEFAULT_NORECURSEDIRS` comment).
- The `STATED_BOUNDS` summary text is untouched. It is pinned to appear verbatim in the docstring and to avoid "collect_ignore", so the new text sits in the elaboration only.
- Re-verified by the gate run above: 373 passed, and mypy and ruff are clean.

## Mutation receipt (W2)
- Anchor `/var/tmp/claude-1000/gg566c3-anchor.txt`; replacement `/var/tmp/claude-1000/gg566c3-replacement.txt`; runner script `/var/tmp/claude-1000/gg566c3-mutation.sh`.
- The tool's own TREE line printed `n/a`: `tree_id.sh` was called without an argument inside the scratch copy. Identity is carried instead by md5 parity: before the run, the scratch and original `gated_ground.py`/`test_gated_ground.py` were byte-identical (`f1accbcb…` / `bea13453…`), and the scratch provenance check (`scratch_copy.sh`) gave EXIT=0.
- The scratch test file is the pre-`7356fdf` 352-test version.
